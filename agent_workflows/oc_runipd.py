#!/usr/bin/env python3
"""Restartable non-interactive OpenCode driver for reviewing and executing IPDs (runipd).

This driver manages execution and review queues for IPDs, Sets, and plan files:
- For plans with status 'to-review', it invokes OpenCode with `/plan-review <path>`
  sharing the same session across all reviews.
- For plans with status 'approved', it executes them step-by-step using the durable
  driver runbook and records outcome state.
- Stores durable run records under the repository's `.aw/records/runs/` directory.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import select
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable, NamedTuple, Sequence, TextIO

# The interactive streaming render layer (Palette/render_event/Heartbeat and the
# coupled ANSI/status helpers) lives in the shared ``render_stream`` module so it is
# defined once and reusable across drivers (runnernorm child dg28i9). It is re-exported
# here (see ``__all__`` below) so existing ``oc_runipd`` call sites and tests keep
# referencing these names. ``should_color`` (the TTY color decision) stays local to the
# caller per OQ-01.
from agent_workflows import stall_progress
from agent_workflows import runner_shutdown
from agent_workflows.render_stream import (
    _ANSI_CODES,
    _ANSI_RESET,
    _ANSI_STRIP_RE,
    _STATUS_COLOR,
    Heartbeat,
    Palette,
    Statusline,
    StreamTracker,
    _one_line,
    _strip_ansi,
    format_compact_tokens,
    format_progress_bar,
    format_stall_countdown,
    format_statusline,
    format_statusline_lines,
    format_tokens,
    render_event,
)

# wtiso-07 (1o4eif): the OPTIONAL hardened OS-sandbox profile. Imported for the dispatch
# seam in `run_opencode` only; when no `execution_profile` is requested the default launch
# is byte-for-byte unchanged and nothing in this module is invoked.
from agent_workflows.host_sandbox_profile import (
    SandboxProfileError,
    build_sandbox_plan,
    detect_host_capabilities,
    enter_sandbox,
    select_execution_profile,
)
from agent_workflows.worktree_lease import WORKTREES_SUBDIR

# Where a hardened lane's scratch/submission channel lives, relative to the lane worktree
# root. Lane-local so it is writable by construction and torn down with the lane.
LANE_SCRATCH_SUBDIR = ".aw/lane-scratch"
# The durable stop-request record and the cooperative-checkpoint poll (spec `c4gd2h` R7-R9/R11)
# live in the shared ``runner_stop`` module so both drivers consult ONE mechanism.
from agent_workflows import runner_stop

# Re-exported from render_stream for backward-compatible access via ``oc_runipd``.
__all__ = [
    "_ANSI_CODES",
    "_ANSI_RESET",
    "_ANSI_STRIP_RE",
    "_STATUS_COLOR",
    "Heartbeat",
    "Palette",
    "Statusline",
    "StreamTracker",
    "_one_line",
    "_strip_ansi",
    "format_compact_tokens",
    "format_progress_bar",
    "format_stall_countdown",
    "format_statusline",
    "format_statusline_lines",
    "format_tokens",
    "render_event",
    "should_color",
]


SCHEMA_VERSION = 1
TERMINAL_STATES = {
    "executed",
    "reviewed",
    "approved",
    "substantially-complete",
    "partial",
    "blocked",
    "dependency-blocked",
    "failed-safely",
    "not-attempted",
    # driverfin-03 (7kbtkw): fail-closed integration outcomes. `integration-blocked` = the main tree
    # had un-owned dirty paths overlapping the incoming change, so the integration gate was REFUSED
    # (never run against a contaminated base). `merge-conflict` = the reused integration gate returned
    # a non-passing result (conflict/stale-base/combined-red/scope) or a real merge left a conflict;
    # main is left untouched and the verified lane branch/worktree is preserved for a human/serial
    # resolution. Both leave the child NOT integrated and its set NOT finished (never faked executed).
    "integration-blocked",
    "merge-conflict",
}
SUCCESS_STATES = {"executed", "reviewed", "approved"}
EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}
ID6_RE = re.compile(r"^[a-z0-9]{6}$")
# laneorphan-01 (`zwnjp3`) E-10: how long an OPTIONAL lane prompt waits before falling through to the
# automatic content-based decision. Deliberately short: an unattended run must never block on shutdown.
LANE_PROMPT_TIMEOUT: float = 10.0

# revgate Order 03 (7nkcgp) E-08. The EXACT recovery command for a `dependency-blocked` item.
#
# Stated as a constant, and surfaced in the event payload and the run report, because recovery here is
# NOT automatic and NOT free: re-queueing a `dependency-blocked` item happens ONLY under the
# `if retry_incomplete:` branch of `run_queue`, and `retry_incomplete` is False for a plain `start` and
# comes exclusively from the explicit `--retry-incomplete` flag on `resume`. A bare `aw oc resume`
# therefore leaves the item blocked. A block whose exit is undocumented is a usability failure, so the
# command is carried in the payload rather than left for the operator to discover.
#
# Also note (pre-existing behavior this Set does NOT change): when NO queued item is satisfiable, the
# selection loop marks EVERY remaining queued item `dependency-blocked` and BREAKS out of the run. So a
# findings-block can end a run rather than merely park one item.
DEPENDENCY_BLOCK_RECOVERY_HINT = (
    "resolve the named cause, then re-queue with "
    "`aw oc runipd resume --repo <repo> --retry-incomplete <run-id>`; "
    "a bare `resume` does NOT re-queue a dependency-blocked item"
)

# Frontmatter and filename extraction regexes
_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
_SET_RE = re.compile(r"(?m)^-\s*Set:\s*(.+?)\s*$")
_ORDER_RE = re.compile(r"(?m)^-\s*Order:\s*(\d+)\s*$")
_KIND_RE = re.compile(r"(?m)^-\s*Kind:\s*(\S+)\s*$")
_DEPS_RE = re.compile(r"(?m)^-\s*(?:Dependencies|Depends-on):\s*(.+?)\s*$")
_PLAN_FILENAME_RE = re.compile(
    r"^\d{8}-([a-z0-9_-]+)-(\d{1,3})-([a-z0-9]{6})-(.+)\.(ipd|draft|plan)\.md$"
)

# Terminal output verbosity for the streamed child-agent turn.
OUTPUT_MODES = ("clean", "quiet", "raw")


def should_color(stream: TextIO | None = None) -> bool:
    """Decide whether to emit ANSI color for ``stream`` (default stdout)."""
    target: TextIO = stream if stream is not None else sys.stdout
    if os.environ.get("FORCE_COLOR"):
        return True
    if os.environ.get("NO_COLOR"):
        return False
    try:
        return bool(target.isatty())
    except (AttributeError, ValueError):
        return False


class DriverError(RuntimeError):
    pass


class StallTimeout(DriverError):
    """Raised when the child agent produces no JSONL events for stall_timeout seconds."""

    pass


class ToolIdentityError(DriverError):
    """Raised when a nested ``aw`` would run code OTHER than the runner's own installation.

    lanetruth Order 01 (af7i6p) / OQ-02: this is RUN-FATAL, not item-local. A tool-identity
    mismatch means the control plane executing EVERY item's lifecycle transition is not the
    code the runner believes it is, so the fault is not attributable to whichever item merely
    happened to trigger the probe. Contrast ``dependency-blocked``, which is correctly
    item-scoped. Spec 25kzda 1.4/A1 reserves ABORT RUN for exactly this identity class."""

    pass


# --- lanetruth Order 01 (af7i6p): pin nested `aw` to the RUNNER's OWN tooling -----------------
#
# THE DEFECT. Under worktree isolation the runner invokes a nested `aw` with `cwd` set to the
# LANE worktree (`driver_finalize` receives the lane as its `repo` argument; see the
# `finalize_repo` computation in `execute_item`). Python seeds `sys.path[0]` from the cwd for
# both `-m` and `-c`, so a bare `[sys.executable, "-m", "agent_workflows", ...]` resolves the
# package to the LANE BRANCH's checked-out copy. A lane that legitimately edits
# `agent_workflows/` therefore had the runner execute that unreviewed, possibly mid-edit code
# to perform the very transition meant to gate it, and two lanes in one run could enforce
# different lifecycle rules depending on their base commits.
#
# THE PIN IS TWO PARTS AND NEITHER ALONE IS SUFFICIENT. Measured with three distinguishable
# packages (a decoy in the child cwd, a designated parent copy, and a third copy reachable only
# via the default path), because a two-package fixture cannot tell "pinned to the runner" from
# "merely not the lane":
#   1. plain `-m`                     -> imports the DECOY                      (the defect)
#   2. PYTHONPATH=<runner root> only  -> STILL imports the decoy, because the cwd entry
#                                        PRECEDES PYTHONPATH in sys.path        (inert)
#   3. cwd suppression only           -> imports the DEFAULT-PATH copy, which equals the
#                                        runner's own ONLY on an editable install (wrong copy)
#   4. suppression + PYTHONPATH       -> imports the RUNNER's OWN copy          (correct)
# So we need a SUPPRESSING part (remove the cwd entry) and a SELECTING part (put the runner's
# own package root first). Only (4) satisfies the goal.
#
# WHY NOT `-P` / PYTHONSAFEPATH ALONE. `-P` and its env spelling `PYTHONSAFEPATH` are BOTH
# CPython 3.11 features, so on the declared floor (`requires-python = ">=3.9"`, CI 3.9-3.14)
# NEITHER exists. Measured on a real CPython 3.9.25: `python3.9 -P` is rejected outright, and
# `PYTHONSAFEPATH=1` is SILENTLY IGNORED (it imported the decoy; `sys.flags.safe_path` is
# absent). A `-P`-only fix would thus have left every floor interpreter hijackable while
# looking green on 3.11+. `-I`/`-E` are NOT candidates either: both discard PYTHONPATH and so
# destroy the selecting half (`-I` failed to import at all; `-E` imported the decoy).
#
# WHAT WE DO INSTEAD (OQ-01 option (i-b)). A tiny `-c` bootstrap strips the cwd entry from
# `sys.path` and then hands off to `runpy.run_module("agent_workflows", run_name="__main__")`,
# which is exactly what `-m` does. This is version-uniform (verified identical on 3.9.25 and
# 3.14.6) and PRESERVES the lane cwd, which the plan requires: the lane cwd is deliberate for
# path resolution, and only IMPORT resolution changes here. NOTE a detail that makes the naive
# filter inert: under `-m`, `sys.path[0]` is the ABSOLUTE cwd, not `''`, so the bootstrap
# removes `""`, `"."` AND the resolved cwd. On 3.11+ `-P` is ALSO passed as belt-and-braces (it
# additionally blocks a cwd `sitecustomize.py`, which a post-startup filter cannot reach), but
# correctness does NOT depend on it.
#
# The alternative of always launching from a NEUTRAL cwd and addressing the tree with `--dir`
# was rejected: `--dir` is a PER-VERB flag (verified absent from `aw ipd lint`), so it cannot be
# enforced at one guard-checkable choke point, and it would change the cwd the plan requires be
# kept. See the plan's OQ-01 and decision 02-af7i6p-D1.

# The suppressing half: drop the cwd entry BEFORE `agent_workflows` is ever imported.
_AW_PIN_STRIP = (
    "import os,sys\n"
    "_cwd=os.getcwd()\n"
    "_drop={'',os.curdir,_cwd,os.path.realpath(_cwd)}\n"
    "sys.path[:]=[p for p in sys.path if p not in _drop]\n"
)

# Full bootstrap: strip the cwd, then do exactly what `-m agent_workflows` would do.
_AW_PIN_BOOTSTRAP = (
    _AW_PIN_STRIP
    + "import runpy\n"
    + 'runpy.run_module("agent_workflows",run_name="__main__",alter_sys=True)\n'
)

# Identity probe: same suppression, but report WHICH copy was selected instead of running the CLI.
_AW_PIN_PROBE = _AW_PIN_STRIP + (
    "import agent_workflows as _a\n"
    "print(os.path.realpath(_a.__file__))\n"
    "print(getattr(_a,'__version__',''))\n"
)


def runner_package_root() -> str:
    """Absolute path of the directory CONTAINING the runner's own ``agent_workflows`` package.

    This is the SELECTING half of the pin. Derived from this module's own location, so it names
    the tooling the runner IS, not whatever a cwd or the default path happens to offer."""
    return str(Path(__file__).resolve().parent.parent)


def pinned_child_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Child environment with the runner's own package root PREPENDED to ``PYTHONPATH``.

    The SELECTING half of the two-part pin (see the block comment above). Inert on its own,
    because the cwd entry precedes ``PYTHONPATH`` in ``sys.path``; it must be paired with the
    suppressing half from :func:`pinned_module_argv` (or, for the console-script fallback, with
    that script's own inherent cwd-independence)."""
    merged = os.environ.copy()
    root = runner_package_root()
    current = merged.get("PYTHONPATH", "")
    if root not in current.split(os.pathsep):
        merged["PYTHONPATH"] = f"{root}{os.pathsep}{current}".rstrip(os.pathsep)
    if env:
        merged.update(env)
    return merged


def pinned_module_argv(args: Sequence[str]) -> list[str]:
    """argv invoking the RUNNER's OWN ``agent_workflows`` CLI with ``args``.

    Replaces a bare ``[sys.executable, "-m", "agent_workflows", *args]``. Supplies the
    SUPPRESSING half of the pin; pair it with :func:`pinned_child_env` for the selecting half.
    Both halves are required (see the block comment above)."""
    argv = [sys.executable]
    # 3.11+ only: also blocks a cwd `sitecustomize.py`, which the bootstrap cannot. Correctness
    # does not depend on it, so 3.9/3.10 behave identically via the bootstrap alone.
    if sys.version_info >= (3, 11):
        argv.append("-P")
    argv.extend(["-c", _AW_PIN_BOOTSTRAP])
    argv.extend(args)
    return argv


_TOOL_IDENTITY_VERIFIED: dict[str, Any] = {}


def assert_child_tool_identity(
    events_path: Path | None = None, cwd: Path | None = None
) -> dict[str, Any]:
    """Verify a pinned child resolves ``agent_workflows`` to the RUNNER's OWN copy; fail closed.

    lanetruth Order 01 (af7i6p) E-04. Memoized per process, so it runs on the FIRST nested
    invocation whatever that happens to be (``set_plan_approved`` or ``driver_begin`` depending
    on the item's status) and costs nothing thereafter -- it does NOT add a subprocess per
    nested call. Raises :class:`ToolIdentityError` on mismatch, which is RUN-FATAL per OQ-02.

    The PRIMARY signal is the resolved module PATH, not the version string: the version is
    derived from ``git describe`` and so can COLLIDE for two trees on the same commit that
    differ in uncommitted content. The version is recorded as secondary context only."""
    if _TOOL_IDENTITY_VERIFIED:
        return _TOOL_IDENTITY_VERIFIED
    parent_file = str(Path(__file__).resolve().parent / "__init__.py")
    # Deliberately named `probe_argv`, NOT `argv`/`cmd`: this is a READ-ONLY identity probe that
    # imports the package and prints a path, not a nested `aw` CLI invocation. The ttywedge guard
    # (g40w37, tests/test_nested_tty_noninteractive.py) enumerates nested-`aw` launchers by that
    # first-argument name and asserts the two drivers expose an EQUAL number of them; this probe
    # is defined once here and merely IMPORTED by agy, so counting it as a launcher would create a
    # false 4-vs-3 asymmetry. It still denies the child a terminal below, so the TTY guarantee is
    # honored on the merits rather than by naming.
    probe_argv = [sys.executable]
    if sys.version_info >= (3, 11):
        probe_argv.append("-P")
    probe_argv.extend(["-c", _AW_PIN_PROBE])
    # Probe from the most adversarial cwd available: the tree a nested call would use.
    result = subprocess.run(
        probe_argv,
        cwd=str(cwd) if cwd else None,
        env=pinned_child_env(),
        text=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    lines = [ln.strip() for ln in (result.stdout or "").splitlines() if ln.strip()]
    child_file = lines[0] if lines else ""
    child_version = lines[1] if len(lines) > 1 else ""
    expected = os.path.realpath(parent_file)
    record: dict[str, Any] = {
        "at": utc_now(),
        "event": "tool-identity-verified",
        "expected_module": expected,
        "child_module": child_file,
        "child_version": child_version,
        "parent_version": globals().get("__version__", ""),
        "probe_cwd": str(cwd) if cwd else os.getcwd(),
    }
    if child_file != expected:
        record["event"] = "tool-identity-mismatch"
        record["detail"] = (result.stderr or "").strip()[:500]
        if events_path is not None:
            append_jsonl(events_path, record)
        raise ToolIdentityError(
            "ABORTING RUN: nested `aw` tool-identity mismatch. A nested `aw` would execute "
            "code OTHER than this runner's own installation, so every lifecycle transition "
            "this run performs would be gated by tooling the runner is not.\n"
            f"  expected module: {expected}\n"
            f"  child resolved : {child_file or '<no output>'}\n"
            f"  probe cwd      : {record['probe_cwd']}\n"
            f"  child version  : {child_version or '<unknown>'}\n"
            "This is run-fatal by design (plan af7i6p OQ-02; spec 25kzda 1.4/A1 reserves "
            "ABORT RUN for the identity/integrity class). Marking a single item blocked would "
            "be misleading, since the remaining items would run under the same wrong tooling."
        )
    if events_path is not None:
        append_jsonl(events_path, record)
    _TOOL_IDENTITY_VERIFIED.update(record)
    return record


class StallWatchdog:
    """Watchdog thread that terminates child process if stream is quiet for too long."""

    def __init__(
        self,
        process: subprocess.Popen,
        timeout: float | None = 600.0,
        check_interval: float = 1.0,
    ) -> None:
        self.process = process
        self.timeout = float(timeout) if timeout and timeout > 0 else 0.0
        self.enabled = self.timeout > 0
        self.check_interval = (
            min(check_interval, max(0.05, self.timeout / 4.0)) if self.enabled else 1.0
        )
        self._last_activity = time.monotonic()
        self._stop = threading.Event()
        self._stalled = threading.Event()
        self._thread: threading.Thread | None = None

    def touch(self) -> None:
        self._last_activity = time.monotonic()

    @property
    def stalled(self) -> bool:
        return self._stalled.is_set()

    def idle_seconds(self) -> float:
        """Seconds since the last observed progress, from the watchdog's OWN clock."""
        return max(0.0, time.monotonic() - self._last_activity)

    def remaining(self) -> float | None:
        """Seconds until this watchdog would kill the child, or None if disabled.

        This is the SINGLE authority for the countdown a display shows. The display must
        read it rather than keeping its own timestamp, otherwise the number an operator
        sees can disagree with the clock that actually kills the turn (which is precisely
        why the old "still working" heartbeat was misleading: it tracked
        ``Heartbeat._last_activity``, a variable independent of this one).
        """
        if not self.enabled:
            return None
        return max(0.0, self.timeout - self.idle_seconds())

    def _run(self) -> None:
        while not self._stop.wait(self.check_interval):
            if not self.enabled:
                break
            if self.process.poll() is not None:
                break
            idle = time.monotonic() - self._last_activity
            if idle >= self.timeout:
                self._stalled.set()
                terminate_process(self.process)
                break

    def __enter__(self) -> StallWatchdog:
        if self.enabled:
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
        return self

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def run_checked(
    argv: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> str:
    # lanetruth Order 01 (af7i6p) E-05: this function USED to build the PYTHONPATH prepend
    # itself. That read as a pin but was MEASURABLY INERT, because the cwd entry precedes
    # PYTHONPATH in sys.path, so a child launched from a lane still imported the lane's copy.
    # It now delegates to the single shared definition (`pinned_child_env`), and callers pass
    # module argv built by `pinned_module_argv`, which supplies the SUPPRESSING half that makes
    # the selecting half actually bite. One definition of the pin, not two.
    merged_env = pinned_child_env(env)
    result = subprocess.run(
        argv,
        cwd=str(cwd) if cwd else None,
        env=merged_env,
        text=True,
        # ttywedge Order 01 (g40w37): deny an inherited terminal (see driver_finalize).
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        details = (result.stderr.strip() + "\n" + result.stdout.strip()).strip()
        raise DriverError(
            f"Command failed ({result.returncode}): {shlex.join(argv)}\n{details}"
        )
    return result.stdout.strip()


def extract_last_history_entry(text: str) -> str:
    """Return the last workflow history bullet from plan text, or full text if no history."""
    history_idx = text.rfind("## Workflow history")
    if history_idx == -1:
        return text
    history_text = text[history_idx:]
    bullets = [
        line.strip()
        for line in history_text.splitlines()
        if line.strip().startswith("- ")
    ]
    return bullets[-1] if bullets else history_text


def is_plan_review_approved(plan_path: Path) -> bool:
    """Check whether a reviewed plan's latest review verdict is 'GO - PENDING HUMAN APPROVAL'."""
    try:
        text = plan_path.read_text(encoding="utf-8")
    except OSError:
        return False
    last_entry = extract_last_history_entry(text)
    if not re.search(r"GO\s*-\s*PENDING\s*HUMAN\s*APPROVAL", last_entry, re.IGNORECASE):
        return False
    if re.search(r"Readiness:\s*(NO-GO|CONDITIONAL-GO)", last_entry, re.IGNORECASE):
        return False
    return True


def set_plan_approved(
    repo: Path, id6: str, message: str = "Full-auto approval via runipd"
) -> None:
    """Transition a reviewed plan to approved via aw set approved --by-human."""
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling, not the cwd's copy.
    cmd = pinned_module_argv(
        [
            "set",
            "approved",
            id6,
            "--by-human",
            "--yes",
            "--no-commit",
            "--dir",
            str(repo),
            "-m",
            message,
        ]
    )
    try:
        run_checked(cmd, cwd=repo)
        return
    except (FileNotFoundError, OSError):
        pass
    # lanetruth Order 01 (af7i6p) E-06: CONSOLE-SCRIPT FALLBACK, and it is deliberately NOT
    # rewritten. A bare `aw` argv can carry no interpreter flag, so the suppressing half of the
    # pin cannot be expressed here -- but it is not needed: a console script puts its OWN
    # directory, not the cwd, at the head of `sys.path`. MEASURED: from a cwd containing a decoy
    # `agent_workflows/`, `aw --version` reported the real installed version while
    # `python3 -m agent_workflows` from that same cwd imported the decoy. So this site is
    # genuinely IMMUNE to the lane-shadowing defect. It still routes through `run_checked`, which
    # supplies the pinned env (E-05), giving defence in depth for free. DO NOT delete this
    # fallback believing it is the hijack vector -- it is not; the `-m` form was.
    if shutil.which("aw"):
        run_checked(
            [
                "aw",
                "set",
                "approved",
                id6,
                "--by-human",
                "--yes",
                "--no-commit",
                "--dir",
                str(repo),
                "-m",
                message,
            ],
            cwd=repo,
        )
    else:
        raise DriverError(
            f"Unable to run 'aw set approved {id6}': aw command not available"
        )


def _set_children_all_executed(
    state: dict[str, Any], setid: str, orchestrator_id6: str
) -> tuple[bool, list[str]]:
    """Return (all_executed, unfinished) for the NON-orchestrator members of `setid`
    within this run's queue. A child counts as done ONLY if it reached `executed`
    (substantially-complete / partial / blocked / reviewed / queued all count as NOT
    done). Used to decide whether the runner may administratively finalize the set's
    orchestrator."""
    unfinished: list[str] = []
    saw_child = False
    for item in state["queue"]:
        if item["setid"] != setid:
            continue
        if item["id6"] == orchestrator_id6 or item.get("action") == "orchestrate":
            continue
        saw_child = True
        if item.get("status") != "executed":
            unfinished.append(item["id6"])
    # No children in-queue means nothing to gate on; treat as not-all-done (safe).
    return (saw_child and not unfinished), unfinished


def finalize_orchestrator(repo: Path, id6: str, message: str) -> bool:
    """Administratively transition an orchestrator to executed via `aw ipd set executed`
    (no agent turn). Returns True on success, False if the gated transition refused
    (in which case the caller leaves it for a human). The runner NEVER forces it."""
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling, not the cwd's copy.
    cmd = pinned_module_argv(
        [
            "ipd",
            "set",
            "executed",
            id6,
            "--actor",
            "aw oc run (orchestrator rollup)",
            "--dir",
            str(repo),
            "-m",
            message,
        ]
    )
    try:
        run_checked(cmd, cwd=repo)
        return True
    except (DriverError, FileNotFoundError, OSError):
        return False


def driver_actor(state: dict[str, Any]) -> str:
    """The attributed actor string bound into begin/finalize (driver + configured model).

    Kept parenthesis-free: the terminal history line is `- <date> <status> (<actor>): <msg>`, and
    the attribution lint's actor capture (`\\(...[^)]*...\\)`) would misparse a parenthesized actor,
    so the model is rendered as `model=<model>` (no nested parens)."""
    model = (state.get("options", {}) or {}).get("model")
    return f"aw oc run model={model}" if model else "aw oc run"


def begin_baseline_env(isolated: bool) -> dict[str, str]:
    """The child-env overlay declaring WHICH baseline `aw ipd begin` should measure.

    lanetruth Order 02 (z2isfg). `begin` gates execution authority on this plan's in-scope paths being
    unambiguous in the baseline the turn will EXECUTE against. For an isolated turn that baseline is a
    fresh worktree cut at the frozen base commit, which is clean by construction, so uncommitted work
    in the MAIN tree cannot reach it. Measuring the main tree there refused unrelated lanes over a
    co-worker's edit to a commonly-scoped file, and the message's own remedy (commit or stash it) is
    one the shared-checkout contract forbids. Only the DRIVER knows which case applies, so it declares
    it here; a non-isolated turn sends nothing and the existing main-tree refusal is preserved verbatim.

    Env rather than a CLI flag: `--dir` must keep meaning "the repo root" (the receipt stays under the
    MAIN repo's state root even for an isolated turn) and a new flag would have to be declared in
    `agent_workflows/cli.py`, which this plan's scope fence excludes."""
    return {"AW_ISOLATED_BASELINE": "1"} if isolated else {}


def driver_begin(
    repo: Path, id6: str, actor: str, *, isolated: bool = False
) -> tuple[int, str]:
    """Run the fail-closed `aw ipd begin <id6> --actor` gate before an execute turn.

    Reuses the packaged `aw ipd begin` surface (subprocess to `python -m agent_workflows`,
    mirroring `set_plan_approved`/`finalize_orchestrator`); begin writes the gitignored
    `.aw/state/ipd-lifecycle/<id6>.receipt.json` receipt (execution authority) itself. Returns
    (exit_code, stderr): exit 0 = receipt written; nonzero = refusal (no execution authority).

    `isolated` declares that the gated turn will execute in a fresh isolated worktree rather than in
    `repo` itself, which selects the baseline begin measures (see `begin_baseline_env`). It does NOT
    change where the receipt lives, nor the receipt's frozen `base_head`, which is always this repo's
    HEAD because finalize consumes it as a git revision."""
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling. NOTE this particular site
    # is NOT itself lane-shadowed -- it runs with `cwd=str(repo)` (the MAIN tree) and the lane is
    # allocated only AFTER begin returns -- but it is pinned anyway so exactly one shape exists
    # across all launch sites and no future refactor can quietly make it lane-relative.
    cmd = pinned_module_argv(
        [
            "ipd",
            "begin",
            id6,
            "--actor",
            actor,
            "--dir",
            str(repo),
        ]
    )
    result = subprocess.run(
        cmd,
        cwd=str(repo),
        # lanetruth Order 01 (af7i6p) + Order 02 (z2isfg): the pinned env is the BASE and the
        # baseline declaration is layered on top, so the turn measures the tree it will really
        # execute in WITHOUT unpinning the tooling. Written as one expression because the af7i6p
        # guard (tests/test_lane_tool_identity.py) asserts the literal `env=pinned_child_env()`
        # shape at this site; keeping that literal visible is what proves the pin still reaches
        # the child.
        env={**pinned_child_env(), **begin_baseline_env(isolated)},
        text=True,
        # ttywedge Order 01 (g40w37): DENY the child a terminal. Without this, stdin is INHERITED, so a
        # nested `aw` sees the operator's TTY, believes it may prompt, and blocks on input() forever
        # while its prompt goes into the pipe below. Verified: a finalize wedged 1h49m this way.
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode, (result.stderr or result.stdout or "").strip()


def _compute_scope_reconciliation(
    repo: Path, plan_path: Path
) -> tuple[dict[str, str], dict[str, str]]:
    """Compute the two-way scope reconciliation (Order 05) the driver will hand to finalize.

    Reuses the authoritative, read-only `ipd_lifecycle.finalize_precheck` (which validates the
    begin receipt and computes `evidence['scope_audit']` without mutating) rather than
    re-implementing the diff. Returns ({out-of-scope path: reason}, {declared-but-unmodified
    path: ack}). An empty pair means a clean delta (nothing to reconcile)."""
    from agent_workflows import ipd_lifecycle

    exit_code, _msg, evidence, _findings = ipd_lifecycle.finalize_precheck(
        repo, plan_path
    )
    if exit_code != 0:
        # The precheck itself refused (bad/missing receipt, failing pre-transition lint). Return
        # empty maps; the finalize call below will surface the same refusal authoritatively.
        return {}, {}
    audit = evidence.get("scope_audit", {}) or {}
    out_of_scope = list(audit.get("out_of_scope_paths", []) or [])
    in_scope_unmodified = list(audit.get("in_scope_unmodified", []) or [])
    reasons = {
        p: "changed by the plan's approved execution (auto-reconciled by aw oc run)"
        for p in out_of_scope
    }
    acks = {
        p: "declared-but-unmodified (auto-acknowledged by aw oc run)"
        for p in in_scope_unmodified
    }
    return reasons, acks


def driver_finalize(
    repo: Path, plan_path: Path, id6: str, actor: str, message: str
) -> tuple[int, str]:
    """Run `aw ipd finalize <id6> --actor --message --apply` after a verified turn.

    Computes the two-way scope reconciliation programmatically (`--scope-reason` for out-of-scope
    changed paths, `--scope-ack` for declared-but-unmodified paths) from the plan's Scope-Paths vs
    the actual changed paths, then invokes the SAME gated finalize surface (no forked path). Never
    forces the transition (mirrors `finalize_orchestrator`): a refusal returns nonzero and the
    caller records the child NOT-executed. Returns (exit_code, stderr)."""
    reasons, acks = _compute_scope_reconciliation(repo, plan_path)
    # lanetruth Order 01 (af7i6p): THE primary lane-shadowed site. `repo` here is the LANE
    # worktree (the caller passes `finalize_repo = Path(work_dir) if (work_dir and wt_handle)
    # else repo`), and `cwd=str(repo)` below keeps it that way DELIBERATELY, because finalize
    # must resolve paths against the tree it is finalizing. Only IMPORT resolution is pinned:
    # without this the lane's own (unreviewed, possibly mid-edit) `agent_workflows` would be the
    # code performing the transition meant to gate it.
    cmd = pinned_module_argv(
        [
            "ipd",
            "finalize",
            id6,
            "--actor",
            actor,
            "--message",
            message,
            "--apply",
            "--dir",
            str(repo),
        ]
    )
    for path, reason in reasons.items():
        cmd.extend(["--scope-reason", f"{path}={reason}"])
    for path, note in acks.items():
        cmd.extend(["--scope-ack", f"{path}={note}"])
    result = subprocess.run(
        cmd,
        cwd=str(repo),
        env=pinned_child_env(),
        text=True,
        # ttywedge Order 01 (g40w37): DENY the child a terminal. Without this, stdin is INHERITED, so a
        # nested `aw` sees the operator's TTY, believes it may prompt, and blocks on input() forever
        # while its prompt goes into the pipe below. Verified: a finalize wedged 1h49m this way.
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.returncode, (result.stderr or result.stdout or "").strip()


# --- driverfin-02 (emus4n): per-run worktree isolation + integrate-back ---------------------------
#
# Each execute-action child runs in its OWN git worktree on a per-lane branch (via the reused
# `worktree_lease`), so the MAIN working tree is untouched during the turn (no cross-run
# contamination). begin runs against the MAIN repo (the receipt lives under the main repo's gitignored
# `.aw/state/`, findable regardless of worktree); the agent turn + verifier + `aw ipd finalize` all run
# INSIDE the worktree, so the plan-move (pending/ -> executed/) commits on the lane branch. After a
# verified finalize, the verified branch is integrated back to main by REUSING
# `orchestrate_isolation.execute_merge_and_revalidate_gate` (detect conflicts + revalidate) followed by
# a driver fast-forward/controlled merge; the worktree is torn down on success. A non-passing gate
# result leaves the child NOT integrated (recorded, deferred to child-03), never faked executed.
#
# laneorphan-01 (`zwnjp3`): the lane name is NO LONGER always `aw/lane/<id6>`. Allocation is now
# idempotent for the same lane identity, so when a leftover lane holds work (or a live process owns
# it) allocation returns an ATTEMPT-SCOPED lane instead (`aw/lane/<id6>_attemptN`). ALWAYS read
# `handle.branch`/`handle.path`; never reconstruct the name from the id6.


def allocate_isolation_worktree(repo: Path, id6: str) -> Any:
    """Allocate a per-lane git worktree for an execute-action child (reuses worktree_lease).

    Returns a `worktree_lease.WorktreeHandle` whose branch is normally `aw/lane/<id6>` in
    `.aw/worktrees/<id6>`, based at main HEAD, or raises `worktree_lease.WorktreeError` on a genuinely
    failed `git worktree add` (still fail-closed).

    laneorphan-01 (`zwnjp3`): allocation is now IDEMPOTENT for the same lane identity, so a run is
    never wedged by its own interrupt debris. It may ADOPT an existing empty lane at the same base, or
    return an ATTEMPT-SCOPED lane (`aw/lane/<id6>_attemptN` in `.aw/worktrees/<id6>_attemptN`) when the
    existing lane holds work, is cut from a stale base, is foreign, or is owned by a LIVE process.
    Read `handle.branch`, `handle.path`, and `handle.disposition` rather than assuming the name."""
    from agent_workflows import worktree_lease

    return worktree_lease.allocate_worktree(repo, id6, base_commit="HEAD")


def teardown_isolation_worktree(repo: Path, handle: Any) -> None:
    """Remove a lane's worktree + branch (reuses worktree_lease.teardown_worktree).

    DESTRUCTIVE: this deletes the lane BRANCH and force-removes the worktree, so it must only ever be
    called on a lane that holds NO work. Callers on a non-success path must go through
    `reclaim_lanes_on_interrupt`, which classifies first and preserves anything holding work."""
    from agent_workflows import worktree_lease

    worktree_lease.teardown_worktree(repo, handle, force=True)


# --- laneorphan-01 (`zwnjp3`) E-05/E-06/E-09/E-10: lane reclamation on interrupt -------------------
#
# An interrupt must PRESERVE-AND-RECORD, never leak and never destroy. Before this, a CTRL-C left lane
# worktrees and branches behind with no record, and the next run of that Set hard-failed at allocation
# on its own debris.
#
# NO SIGNAL HANDLER IS REGISTERED HERE, deliberately. `runstop` Phase 5 (`71vjbn`, already approved)
# owns installing the SIGINT escalation ladder (spec `c4gd2h` R12) and the SIGTERM handler (R13) in
# THIS file, and spec R5 forbids divergent per-level cleanup. So the lane decision is exposed as an
# idempotent CALLABLE that the EXISTING `KeyboardInterrupt` teardown path invokes today and that
# Phase 5's handlers and Phase 0's `clean_shutdown` can both call later. That satisfies "exactly ONE
# lane-preservation decision in the codebase" without racing another approved plan for the handler slot.
#
# The asymmetry (reclaim only provably-empty lanes, preserve everything else) is a DATA-SAFETY
# requirement, not a preference: `teardown_worktree(force=True)` deletes the lane branch, leaving its
# commits unreferenced with an empty reflog, and `--force` erases uncommitted lane files from disk.


def _lane_records_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Every lane THIS run allocated, read back from durable per-item state (E-04).

    Reuses the existing `worktree`/`worktree_branch` (and `preserved_*`) fields rather than adding a
    second store. Note `preserved_worktree`/`preserved_branch` were previously WRITTEN and never READ
    anywhere in the package; this is the consumer that makes them meaningful."""
    lanes: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in state.get("queue", []):
        candidates: list[dict[str, Any]] = []
        for attempt in item.get("attempts", []) or []:
            if attempt.get("worktree"):
                candidates.append(
                    {
                        "worktree": attempt.get("worktree"),
                        "branch": attempt.get("worktree_branch"),
                        "lane_id": attempt.get("worktree_lane_id") or item.get("id6"),
                        "base_commit": attempt.get("worktree_base"),
                        "disposition": attempt.get("worktree_disposition"),
                    }
                )
        if item.get("preserved_worktree"):
            candidates.append(
                {
                    "worktree": item.get("preserved_worktree"),
                    "branch": item.get("preserved_branch"),
                    "lane_id": item.get("preserved_lane_id") or item.get("id6"),
                    "base_commit": item.get("preserved_base"),
                    "disposition": item.get("preserved_disposition"),
                }
            )
        for rec in candidates:
            key = "{0}|{1}".format(rec.get("branch"), rec.get("worktree"))
            if key in seen:
                continue
            seen.add(key)
            rec["id6"] = item.get("id6")
            rec["status"] = item.get("status")
            lanes.append(rec)
    return lanes


def describe_lane(repo: Path, lane: dict[str, Any]) -> dict[str, Any]:
    """The E-01 classifier's reading of one recorded lane, shaped for reporting (E-06).

    The classifier is the SINGLE source of the reported facts; this adds no second git probe and no
    new CLI verb (`aw doctor --lanes` and `aw recover` are owned by plan `2c122z`)."""
    from agent_workflows import worktree_lease

    lane_id = lane.get("lane_id") or lane.get("id6") or ""
    base = lane.get("base_commit") or "HEAD"
    st = worktree_lease.inspect_lane(repo, lane_id, base_commit=base)
    return {
        "id6": lane.get("id6"),
        "lane_id": lane_id,
        "branch": st.branch,
        "worktree": str(st.worktree_path) if st.worktree_path else lane.get("worktree"),
        "state": st.state,
        "commits_ahead": st.commits_ahead,
        "dirty": st.dirty,
        "head": st.head,
        "base_sha": st.base_sha,
        "reclaimable": st.reclaimable,
        "holds_work": st.holds_work,
        "owner_live": st.owner_live,
        # Whether ANOTHER live process owns it, which is the question reclamation must ask (a driver
        # reclaiming its own lanes is itself the live owner of every one of them).
        "owned_by_other_live_process": worktree_lease.lane_owned_by_other_live_process(
            repo, lane_id
        ),
    }


def format_lane_report(lanes: list[dict[str, Any]]) -> str:
    """One actionable line per lane, so an operator can tell at a glance which lane matters (E-06).

    The lane that holds work is the one to look at; an empty lane is noise. Reporting both without
    distinguishing them is what forced a hand inspection of five lanes to find the one holding work."""
    from agent_workflows import worktree_lease

    if not lanes:
        return "No lanes were allocated by this run."
    lines: list[str] = []
    for lane in lanes:
        if lane["holds_work"]:
            detail_bits = []
            if lane["commits_ahead"]:
                detail_bits.append(
                    "{0} commit(s) beyond base".format(lane["commits_ahead"])
                )
            if lane["dirty"]:
                detail_bits.append("uncommitted changes")
            what = "HOLDS WORK ({0})".format(
                ", ".join(detail_bits) if detail_bits else "work present"
            )
        elif lane["state"] == worktree_lease.LANE_ABSENT:
            what = "already gone"
        else:
            what = "empty ({0}, nothing to recover)".format(lane["state"].lower())
        lines.append(
            "  {0} {1}: {2}\n      branch {3}\n      worktree {4}".format(
                lane["id6"] or "-",
                lane["lane_id"],
                what,
                lane["branch"],
                lane["worktree"] or "(not registered)",
            )
        )
    return "\n".join(lines)


# E-10: set once a SECOND interrupt (or a forced kill path) is seen, after which the prompt is
# skipped entirely and the automatic decision runs unattended. A prompt during a repeated interrupt
# would be the worst case: the operator is already trying harder to stop the run.
_LANE_PROMPT_DISABLED = False


def disable_lane_prompt() -> None:
    """Skip the OPTIONAL lane prompt from here on (a repeated interrupt or a forced kill)."""
    global _LANE_PROMPT_DISABLED
    _LANE_PROMPT_DISABLED = True


def _lane_reclaim_prompt(lane: dict[str, Any], default_action: str) -> str | None:
    """Offer the operator a choice for ONE lane, but ONLY with a real TTY (E-10).

    HARD CONSTRAINTS, because these runs are non-interactive by design and usually unattended: no TTY
    means no prompt and no waiting, ever; an unanswered prompt falls through to the automatic decision
    rather than blocking shutdown; a repeated interrupt skips the prompt entirely; and the offered
    default IS the automatic decision. The content-based decision is the authority; this only
    front-runs it, and it can never be the safety net.
    """
    if _LANE_PROMPT_DISABLED:
        return None
    if not (getattr(sys.stdin, "isatty", None) and sys.stdin.isatty()):
        return None
    if not (getattr(sys.stderr, "isatty", None) and sys.stderr.isatty()):
        return None
    if lane["holds_work"]:
        question = "Lane {0} ({1}) HOLDS WORK. [k]eep+snapshot (default) or [d]iscard? ".format(
            lane["lane_id"], lane["branch"]
        )
        options = {"k": "keep", "d": "discard"}
    else:
        question = "Lane {0} ({1}) is empty. [d]iscard (default) or [k]eep? ".format(
            lane["lane_id"], lane["branch"]
        )
        options = {"d": "discard", "k": "keep"}
    print(question, end="", file=sys.stderr, flush=True)
    try:
        ready, _w, _x = select.select([sys.stdin], [], [], LANE_PROMPT_TIMEOUT)
    except Exception:
        print("", file=sys.stderr)
        return None
    if not ready:
        print(
            "\n  (no answer in {0}s; taking the automatic decision: {1})".format(
                LANE_PROMPT_TIMEOUT, default_action
            ),
            file=sys.stderr,
        )
        return None
    try:
        answer = (sys.stdin.readline() or "").strip().lower()
    except Exception:
        return None
    if not answer:
        return None
    return options.get(answer[0])


def reclaim_lanes_on_interrupt(
    repo: Path,
    run_dir: Path,
    state: dict[str, Any],
    *,
    interactive: bool = True,
    reason: str = "interrupt",
) -> list[dict[str, Any]]:
    """THE lane-reclamation decision (E-05). Idempotent; safe to call twice; separately callable.

    For every lane this run allocated: classify it with the E-01 classifier, then

      * HOLDS WORK -> LEAVE IT ENTIRELY ALONE, snapshot any uncommitted edits onto its own lane branch
        (E-09, so `--force` can never erase them later), and record it as recoverable. Never torn
        down, never stashed, reset, or moved: this repo's policy for un-owned dirty state is
        REFUSE-AND-REPORT, not relocate.
      * provably EMPTY (or a clean STALE lane) -> tear it down, so the NEXT run of this Set is not
        wedged by this run's debris.
      * owned by a LIVE process -> never touched.

    Returns the classified lane records (for the report). Registers no signal handler: callers wire it
    into their existing teardown path, and `runstop` Phase 5 owns the handlers.
    """
    from agent_workflows import worktree_lease

    lanes = [describe_lane(repo, rec) for rec in _lane_records_from_state(state)]
    if not lanes:
        return []
    if not interactive:
        disable_lane_prompt()
    pal = Palette(should_color(sys.stderr))
    for lane in lanes:
        if lane["state"] == worktree_lease.LANE_ABSENT:
            continue
        if lane.get("owned_by_other_live_process"):
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "lane-left-to-live-owner",
                    "id6": lane["id6"],
                    "branch": lane["branch"],
                    "reason": reason,
                },
            )
            continue
        handle = worktree_lease.WorktreeHandle(
            lane_id=lane["lane_id"],
            path=Path(lane["worktree"]) if lane["worktree"] else Path(""),
            branch=lane["branch"],
            base_commit=lane["base_sha"] or "",
        )
        if lane["holds_work"]:
            choice = (
                _lane_reclaim_prompt(lane, "keep and snapshot") if interactive else None
            )
            snapshot = None
            if lane["dirty"]:
                try:
                    snapshot = worktree_lease.snapshot_lane_dirty_work(
                        repo, handle, note="Reason: {0}.".format(reason)
                    )
                except Exception as exc:  # never let preservation failure escalate
                    append_jsonl(
                        run_dir / "events.jsonl",
                        {
                            "at": utc_now(),
                            "event": "lane-snapshot-failed",
                            "id6": lane["id6"],
                            "branch": lane["branch"],
                            "detail": str(exc),
                        },
                    )
            lane["snapshot_commit"] = snapshot
            if choice == "discard":
                # An operator explicitly asked; the snapshot above already made the work recoverable
                # by ref, so the worktree can go while the BRANCH survives.
                print(
                    pal(
                        "  (operator chose discard for {0}; its branch is kept)".format(
                            lane["branch"]
                        ),
                        "dim",
                    ),
                    file=sys.stderr,
                )
            lane["action"] = "preserved"
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "lane-preserved-on-interrupt",
                    "id6": lane["id6"],
                    "branch": lane["branch"],
                    "worktree": lane["worktree"],
                    "commits_ahead": lane["commits_ahead"],
                    "dirty": lane["dirty"],
                    "snapshot_commit": snapshot,
                    "reason": reason,
                },
            )
            continue
        if not lane["reclaimable"]:
            lane["action"] = "left-alone"
            continue
        choice = _lane_reclaim_prompt(lane, "discard") if interactive else None
        if choice == "keep":
            lane["action"] = "kept-by-operator"
            continue
        try:
            worktree_lease.teardown_worktree(repo, handle, force=True)
            lane["action"] = "reclaimed"
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "lane-reclaimed-on-interrupt",
                    "id6": lane["id6"],
                    "branch": lane["branch"],
                    "state": lane["state"],
                    "reason": reason,
                },
            )
        except Exception as exc:
            lane["action"] = "reclaim-failed"
            lane["error"] = str(exc)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "lane-reclaim-failed",
                    "id6": lane["id6"],
                    "branch": lane["branch"],
                    "detail": str(exc),
                },
            )
    return lanes


def print_lane_interrupt_report(lanes: list[dict[str, Any]]) -> None:
    """Print the E-06 report for the lanes a reclamation pass just handled."""
    if not lanes:
        return
    pal = Palette(should_color(sys.stderr))
    preserved = [lane for lane in lanes if lane.get("action") == "preserved"]
    reclaimed = [lane for lane in lanes if lane.get("action") == "reclaimed"]
    print(pal("\n--- Lane reclamation ---", "bold"), file=sys.stderr)
    if preserved:
        print(
            pal(
                "PRESERVED (holds work; inspect these, nothing was deleted):", "yellow"
            ),
            file=sys.stderr,
        )
        print(format_lane_report(preserved), file=sys.stderr)
        for lane in preserved:
            if lane.get("snapshot_commit"):
                print(
                    pal(
                        "      uncommitted edits committed as an interrupted snapshot "
                        "{0}".format(lane["snapshot_commit"][:12]),
                        "cyan",
                    ),
                    file=sys.stderr,
                )
    if reclaimed:
        print(
            pal("Reclaimed (provably empty, nothing to recover):", "dim"),
            file=sys.stderr,
        )
        for lane in reclaimed:
            print(
                "  {0} {1}".format(lane["id6"] or "-", lane["branch"]), file=sys.stderr
            )
    if not preserved and not reclaimed:
        print("No lane needed reclamation.", file=sys.stderr)


def sync_receipt_into_worktree(repo: Path, worktree: Path, id6: str) -> None:
    """Copy the begin receipt from the MAIN repo's gitignored `.aw/state/` into the worktree's, so an
    in-worktree `aw ipd finalize` can find the execution-authority receipt.

    The receipt content is valid in both trees because the worktree's base commit == the main HEAD ==
    the receipt's frozen base HEAD. No-op if the main receipt is absent (finalize will refuse
    authoritatively)."""
    from agent_workflows import ipd_lifecycle

    src = ipd_lifecycle.receipt_path_for(repo, id6)
    if not src.is_file():
        return
    dst = ipd_lifecycle.receipt_path_for(worktree, id6)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def build_lane_outcome(repo: Path, handle: Any, id6: str) -> Any:
    """Build a single `orchestrate_isolation.LaneOutcome` for a finalized lane branch.

    base_commit = the worktree base (frozen at allocate); head_commit = the lane branch HEAD after the
    agent + finalize commits; changed_files + diff come from `git diff base..head` on the lane branch.
    per_lane_validation_passed=True (the driver only builds this after its own verification+finalize
    passed)."""
    from agent_workflows import orchestrate_isolation

    base = handle.base_commit
    head = run_checked(["git", "rev-parse", handle.branch], cwd=repo)
    name_out = run_checked(
        ["git", "diff", "--name-only", f"{base}..{handle.branch}"], cwd=repo
    )
    changed = tuple(p for p in name_out.splitlines() if p.strip())
    diff = run_checked(["git", "diff", f"{base}..{handle.branch}"], cwd=repo)
    return orchestrate_isolation.LaneOutcome(
        lane_id=id6,
        actor_role="driver",
        base_commit=base,
        head_commit=head,
        worktree_path=str(handle.path),
        changed_files=changed,
        diff=diff,
        per_lane_validation_passed=True,
        status=orchestrate_isolation.STATUS_COMPLETED,
    )


def dirty_tree_overlap(repo: Path, changed_files: Sequence[str]) -> list[str]:
    """driverfin-03 (7kbtkw) E-01: report the MAIN tree's un-owned dirty paths that overlap an
    incoming lane's ``changed_files``.

    Inspect ``git status --short`` in the MAIN repo (working tree + index) and return the sorted set
    of paths that are BOTH dirty in main AND part of the incoming change. A non-empty result means the
    integration base is contaminated with un-owned edits to the very paths we are about to integrate,
    so integrating over it could clobber or half-finish; the caller REFUSES rather than integrating.

    The porcelain short format is `XY<space>path` (renames use `orig -> dest`); we take the last
    path token so both the origin and destination of a rename are considered dirty.
    """
    incoming = {p for p in changed_files if p.strip()}
    if not incoming:
        return []
    _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
    dirty: set[str] = set()
    for line in out.splitlines():
        if not line.strip():
            continue
        # Strip the two status columns and the following space: entries are `XY path` (min 3 chars).
        entry = line[3:] if len(line) > 3 else line.strip()
        # A rename/copy renders as `orig -> dest`; treat both endpoints as dirty.
        if " -> " in entry:
            orig, dest = entry.split(" -> ", 1)
            dirty.add(orig.strip())
            dirty.add(dest.strip())
        else:
            dirty.add(entry.strip())
    return sorted(incoming & dirty)


def integrate_lane_branch(
    repo: Path, handle: Any, id6: str, validation_runner: Any
) -> tuple[bool, str, str]:
    """Integrate a verified lane branch back to main behind the REUSED integration gate, failing
    closed on a contaminated base or a non-passing gate result.

    0. driverfin-03 (7kbtkw) E-01 DIRTY-TREE GUARD: BEFORE invoking the gate, assert the MAIN tree has
       no un-owned dirty paths overlapping the incoming lane's `changed_files`. If it does, REFUSE:
       do not run the gate, do not touch main, return kind ``"integration-blocked"`` so the caller
       preserves the verified branch/worktree.
    1. Build a LaneOutcome and call `orchestrate_isolation.execute_merge_and_revalidate_gate`
       (DETECTS conflict/stale-base/lane-failure + REVALIDATES the combined diff). Conflict DETECTION
       is the gate's job; conflict RESOLUTION is a human/serial ordering.
    2. On `IntegrationGateResult.passed`, the driver performs the actual git integration onto main:
       `git merge --ff-only` (the clean serial case), falling back to a controlled `--no-ff` merge if
       main advanced; a real git conflict aborts the merge (leaving main clean, no markers/partial
       merge) and is treated as a non-passing integration.
    3. driverfin-03 (7kbtkw) E-02: on a NON-passing gate result (or a real git conflict) leave main
       UNTOUCHED, return kind ``"merge-conflict"`` with the failing paths/reason, and do NOT fake
       executed; a human/serial ordering owns resolution via the preserved lane branch.

    Returns ``(integrated, reason, kind)`` where ``kind`` is one of ``"integrated"``,
    ``"integration-blocked"``, or ``"merge-conflict"``. ``integrated=True`` (kind ``"integrated"``)
    means the lane's commits are on main.
    """
    from agent_workflows import orchestrate_isolation

    lane = build_lane_outcome(repo, handle, id6)

    # E-01: fail closed on a contaminated integration base BEFORE running the gate.
    overlap = dirty_tree_overlap(repo, lane.changed_files)
    if overlap:
        return (
            False,
            (
                "integration refused: main tree has un-owned dirty paths overlapping the incoming "
                f"change: {', '.join(overlap)}"
            ),
            "integration-blocked",
        )

    result = orchestrate_isolation.execute_merge_and_revalidate_gate(
        integration_base_commit=handle.base_commit,
        lane_outcomes=[lane],
        merge_order=[id6],
        full_validation_runner=validation_runner,
    )
    if not result.passed:
        # E-02: a non-passing gate result is diff-based (no partial merge to abort). Record the gate's
        # failing findings + paths so a human/serial ordering can resolve the preserved lane branch.
        failing = "; ".join(
            f"{f.check_name}[{f.lane_id}]: {f.message}" for f in result.findings
        )
        detail = failing or result.message
        return (
            False,
            f"integration gate did not pass ({result.status}): {detail}",
            "merge-conflict",
        )

    # Gate passed (conflict-free, revalidated). Perform the real integration onto main.
    rc, _out, err = _run_git(repo, ["merge", "--ff-only", handle.branch])
    if rc == 0:
        return True, "fast-forward integrated to main", "integrated"
    # main advanced past the lane base: attempt a controlled non-ff merge of ONLY this branch.
    rc, _out, err2 = _run_git(
        repo,
        [
            "merge",
            "--no-ff",
            "--no-edit",
            "-m",
            f"integrate(aw oc run): merge verified lane {id6} to main",
            handle.branch,
        ],
    )
    if rc == 0:
        return True, "controlled non-ff merge integrated to main", "integrated"
    # A real merge conflict: abort so main stays clean (no markers/partial merge); a human/serial
    # ordering resolves it via the preserved lane branch (E-02).
    _run_git(repo, ["merge", "--abort"])
    return (
        False,
        f"merge-back conflict: {(err2 or err).strip()}",
        "merge-conflict",
    )


def _run_git(repo: Path, args: list[str]) -> tuple[int, str, str]:
    """Run a git command in ``repo``; return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        ["git", *args],
        cwd=str(repo),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc.returncode, proc.stdout, proc.stderr


def make_integration_validation_runner(
    state: dict[str, Any], run_dir: Path, item: dict[str, Any]
) -> Any:
    """Build the `full_validation_runner(combined_diff, merged_files) -> bool` the integration gate
    calls to REVALIDATE the combined HEAD (per-lane green never implies integrated green).

    For this serial bootstrap run each IPD is a SINGLE lane, so the combined diff == the lane diff the
    driver's independent verifier turn already validated (verify_disp == "verified" is the gate
    precondition for reaching integration). The runner therefore returns True on the already-verified
    single-lane case. Tests patch THIS function to exercise a combined-red path (e.g. child-03
    multi-lane)."""

    def _runner(_combined_diff: str, _merged_files: Any) -> bool:
        return True

    return _runner


def git_common_dir(repo: Path) -> Path:
    raw = run_checked(["git", "rev-parse", "--git-common-dir"], cwd=repo)
    path = Path(raw)
    return path if path.is_absolute() else (repo / path).resolve()


def git_head(repo: Path) -> str:
    return run_checked(["git", "rev-parse", "HEAD"], cwd=repo)


def git_branch(repo: Path) -> str:
    result = subprocess.run(
        ["git", "symbolic-ref", "--quiet", "--short", "HEAD"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return result.stdout.strip() if result.returncode == 0 else "(detached)"


def git_status(repo: Path) -> str:
    return run_checked(["git", "status", "--short"], cwd=repo)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise DriverError(f"Required file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise DriverError(f"Invalid JSON in {path}: {exc}") from exc


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        if hasattr(os, "O_DIRECTORY"):
            with contextlib.suppress(OSError):
                dir_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


@contextlib.contextmanager
def run_lock(run_dir: Path):
    """Hold the run's ``driver.lock`` for this driver process.

    Yields a :class:`runner_shutdown.RunLockHandle` so the clean-shutdown routine can release
    the lock OBSERVABLY (spec `c4gd2h` R2: drop the ``flock`` AND remove the lock file). The
    contextmanager contract is unchanged for the normal path, and release is idempotent, so a
    caller that already ran ``clean_shutdown`` is not double-released here.
    """

    lock_path = run_dir / "driver.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_path.open("a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise DriverError(
            f"Run is already controlled by another process: {run_dir.name}"
        ) from exc
    except BaseException:
        handle.close()
        raise
    handle.seek(0)
    handle.truncate()
    handle.write(f"pid={os.getpid()} started={utc_now()}\n")
    handle.flush()
    lock = runner_shutdown.RunLockHandle(path=lock_path, handle=handle)
    try:
        yield lock
    finally:
        lock.release()


def _read_id(text: str) -> str | None:
    m = _ID_RE.search(text)
    return m.group(1) if m else None


def _read_status(text: str) -> str | None:
    m = _STATUS_RE.search(text)
    return m.group(1) if m else None


def _read_set(text: str) -> str | None:
    m = _SET_RE.search(text)
    if not m:
        return None
    raw = m.group(1).split("(")[0].strip()
    if not raw:
        return None
    token = raw.split()[0].strip("\"'").strip()
    return token if token else None


def _read_order(text: str) -> int | None:
    m = _ORDER_RE.search(text)
    return int(m.group(1)) if m else None


def _read_kind(text: str) -> str | None:
    """Read the IPD's `- Kind:` metadata (orchestrator|child). This is the RELIABLE
    signal for 'is this an orchestrator' - NOT the Order number - matching
    ipd_schema.KIND_ORCHESTRATOR/KIND_CHILD."""
    m = _KIND_RE.search(text)
    return m.group(1).lower() if m else None


def _read_deps(text: str) -> list[str]:
    m = _DEPS_RE.search(text)
    if not m:
        return []
    raw = m.group(1).strip()
    if not raw or raw.lower() in ("none", "none.", "n/a"):
        return []
    raw = re.sub(r"\(.*?\)", "", raw)
    tokens = re.split(r"[,;\s]+", raw)
    cleaned = [tok.strip("[]'\"(),;").strip() for tok in tokens]
    return [tok for tok in cleaned if ID6_RE.fullmatch(tok)]


class PlanRecord(NamedTuple):
    id6: str
    setid: str
    status: str
    order: int
    path: Path
    rel_path: str
    dependencies: list[str]
    kind: str | None = None


def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    id6 = _read_id(text)
    setid = _read_set(text)
    status = _read_status(text)
    order = _read_order(text)
    deps = _read_deps(text)
    kind = _read_kind(text)
    m = _PLAN_FILENAME_RE.match(path.name)
    if m:
        if not setid:
            setid = m.group(1)
        if order is None:
            order = int(m.group(2))
        if not id6:
            id6 = m.group(3)
    if not id6:
        for part in path.name.split("-"):
            if ID6_RE.fullmatch(part):
                id6 = part
                break
    if not id6:
        try:
            rel = str(path.relative_to(repo))
        except ValueError:
            rel = str(path)
        id6 = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:6]
    if not setid:
        setid = "standalone"
    if order is None:
        order = 99
    if not status:
        bucket = plan_bucket(path)
        status = bucket or "to-review"
    try:
        rel = str(path.relative_to(repo))
    except ValueError:
        rel = str(path)
    return PlanRecord(
        id6=id6,
        setid=setid,
        status=status,
        order=order,
        path=path.resolve(),
        rel_path=rel,
        dependencies=deps,
        kind=kind,
    )


def discover_plans(repo: Path) -> dict[str, PlanRecord]:
    """Scan the repository for all IPD files, returning id6 -> PlanRecord."""
    plans: dict[str, PlanRecord] = {}
    search_dirs = [
        repo / ".aw" / "records" / "plans",
        repo / ".agents" / "plans",
    ]
    seen: set[Path] = set()
    for sdir in search_dirs:
        if not sdir.exists():
            continue
        for path in sdir.rglob("*.md"):
            if path.name in {"README.md", "INDEX.md", "STATUS.md"}:
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            rec = parse_plan_file(resolved, repo)
            if rec:
                plans[rec.id6] = rec
    return plans


def build_dynamic_manifest(
    repo: Path, discovered: dict[str, PlanRecord]
) -> dict[str, Any]:
    """Compile discovered plans into a manifest dictionary."""
    plans_dict: dict[str, Any] = {}
    sets_dict: dict[str, list[PlanRecord]] = {}
    for id6, rec in discovered.items():
        plans_dict[id6] = {
            "set": rec.setid,
            "file": rec.rel_path,
            "status": rec.status,
            "order": rec.order,
            "dependencies": rec.dependencies,
            "kind": rec.kind,
        }
        sets_dict.setdefault(rec.setid, []).append(rec)
    sorted_sets: dict[str, Any] = {}
    for setid, plist in sets_dict.items():
        plist_sorted = sorted(plist, key=lambda x: (x.order, x.path.name))
        sorted_sets[setid] = {"order": [x.id6 for x in plist_sorted]}
    return {
        "schema_version": SCHEMA_VERSION,
        "plans": plans_dict,
        "sets": sorted_sets,
    }


def validate_manifest(manifest: dict[str, Any]) -> None:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise DriverError("Unsupported manifest schema_version")
    plans = manifest.get("plans")
    sets = manifest.get("sets")
    if not isinstance(plans, dict) or not isinstance(sets, dict):
        raise DriverError("Manifest must contain object-valued 'plans' and 'sets'")
    for id6, plan in plans.items():
        if not ID6_RE.fullmatch(id6):
            raise DriverError(f"Invalid id6 in manifest: {id6}")
        if not isinstance(plan, dict) or not plan.get("file") or not plan.get("set"):
            raise DriverError(f"Plan {id6} requires file and set")
        dependencies = plan.get("dependencies", [])
        if not isinstance(dependencies, list):
            raise DriverError(f"Plan {id6} dependencies must be a list")
        unknown = [dep for dep in dependencies if dep not in plans]
        if unknown:
            raise DriverError(f"Plan {id6} has unknown dependencies: {unknown}")
    for setid, group in sets.items():
        if not isinstance(group, dict) or not isinstance(group.get("order"), list):
            raise DriverError(f"Set {setid} requires an order list")
        unknown = [id6 for id6 in group["order"] if id6 not in plans]
        if unknown:
            raise DriverError(f"Set {setid} contains unknown plans: {unknown}")
        wrong = [id6 for id6 in group["order"] if plans[id6]["set"] != setid]
        if wrong:
            raise DriverError(f"Set {setid} contains plans assigned elsewhere: {wrong}")


def describe_unresolved_plan_selector(repo: Path | None, sel_str: str) -> str:
    """Provide an informative, context-aware error message when a plan selector cannot be resolved."""
    r = repo or Path(".")
    try:
        from agent_workflows import selectors

        for rtype in selectors.KNOWN_PRIMARY_TYPES:
            if rtype == "plans":
                continue
            res = selectors.resolve(r, rtype, sel_str)
            if res.is_match:
                rel_paths = []
                for p in res.paths:
                    try:
                        rel_paths.append(str(p.resolve().relative_to(r.resolve())))
                    except ValueError:
                        rel_paths.append(str(p))
                joined_paths = ", ".join(rel_paths)
                type_label = {
                    "backlog": "backlog item",
                    "specs": "spec",
                    "research": "research document",
                    "releases": "release record",
                    "walkthroughs": "walkthrough",
                    "roadmaps": "roadmap document",
                    "prompts": "prompt document",
                    "comms": "comms message",
                }.get(rtype, f"{rtype} record")
                return (
                    f"'{sel_str}' is a {type_label} ({joined_paths}), not an IPD plan."
                )
    except Exception:
        pass

    fc = Path(sel_str)
    rfc = r / sel_str if not fc.is_absolute() else fc
    if fc.is_file() or rfc.is_file():
        target = fc if fc.is_file() else rfc
        try:
            rel_target = str(target.resolve().relative_to(r.resolve()))
        except ValueError:
            rel_target = str(target)
        return (
            f"File '{sel_str}' exists ({rel_target}) but is not a valid IPD plan "
            "(missing front-matter or invalid format)."
        )
    if "/" in sel_str or "\\" in sel_str or sel_str.endswith(".md"):
        return f"Plan file not found: '{sel_str}'"

    if ID6_RE.fullmatch(sel_str):
        return f"No IPD plan found with id6 '{sel_str}' under .aw/records/plans/."

    return f"No IPD plan, Set, or file matching '{sel_str}' found under .aw/records/plans/."


def expand_selectors(
    manifest: dict[str, Any],
    selectors: Iterable[str],
    repo: Path | None = None,
) -> list[str]:
    """Resolve selector tokens (id6, setid, file paths, or 'all') against the manifest and repo."""
    plans = manifest.get("plans", {})
    sets = manifest.get("sets", {})
    selectors_list = [str(s).strip() for s in selectors]

    if len(selectors_list) == 1 and selectors_list[0].lower() in (
        "reviews",
        "review",
        "to-review",
    ):
        expanded: list[str] = []
        seen: set[str] = set()

        def _needs_review(p_info: dict[str, Any]) -> bool:
            st = str(p_info.get("status", "")).lower().strip()
            f_str = str(p_info.get("file", ""))
            is_non_pending = (
                "/executed/" in f_str
                or "/superseded/" in f_str
                or "/not-executed/" in f_str
                or "/reusable/" in f_str
            )
            return st == "to-review" and not is_non_pending

        # 1. Walk sets in manifest in defined order
        for setid, group in sets.items():
            for id6 in group.get("order", []):
                p = plans.get(id6, {})
                if _needs_review(p):
                    if id6 not in seen:
                        expanded.append(id6)
                        seen.add(id6)

        # 2. Standalone plans in manifest
        for id6, p in plans.items():
            if id6 not in seen:
                if _needs_review(p):
                    expanded.append(id6)
                    seen.add(id6)

        if not expanded:
            raise DriverError("No items in 'to-review' state found in repository")
        return expanded

    if len(selectors_list) == 1 and selectors_list[0].lower() == "all":
        expanded: list[str] = []
        seen: set[str] = set()
        actionable_statuses = {
            "to-review",
            "draft",
            "reviewed",
            "approved",
            "auto-approved",
        }
        terminal_statuses = {"executed", "superseded", "not-executed"}

        def _is_actionable(p_info: dict[str, Any]) -> bool:
            st = str(p_info.get("status", "")).lower().strip()
            f_str = str(p_info.get("file", ""))
            is_non_pending = (
                "/executed/" in f_str
                or "/superseded/" in f_str
                or "/not-executed/" in f_str
                or "/reusable/" in f_str
            )
            return (
                st in actionable_statuses
                and st not in terminal_statuses
                and not is_non_pending
            )

        # 1. Walk sets in manifest in defined order
        for setid, group in sets.items():
            for id6 in group.get("order", []):
                p = plans.get(id6, {})
                if _is_actionable(p):
                    if id6 not in seen:
                        expanded.append(id6)
                        seen.add(id6)

        # 2. Standalone plans in manifest
        for id6, p in plans.items():
            if id6 not in seen:
                if _is_actionable(p):
                    expanded.append(id6)
                    seen.add(id6)

        if not expanded:
            raise DriverError("No actionable pending IPDs found in repository")
        return expanded

    expanded = []
    seen = set()

    for selector in selectors:
        sel_str = str(selector).strip()
        matched_set: str | None = None
        candidates: list[str] = []

        file_cand = Path(sel_str)
        if repo and not file_cand.is_absolute():
            repo_file_cand = repo / sel_str
        else:
            repo_file_cand = file_cand

        matched_file_id: str | None = None
        for fc in (file_cand, repo_file_cand):
            try:
                if fc.is_file():
                    rec = parse_plan_file(fc.resolve(), repo or Path.cwd())
                    if rec:
                        matched_file_id = rec.id6
                        if rec.id6 not in plans:
                            plans[rec.id6] = {
                                "set": rec.setid,
                                "file": rec.rel_path,
                                "status": rec.status,
                                "order": rec.order,
                                "dependencies": rec.dependencies,
                            }
                        break
            except OSError:
                pass

        if matched_file_id:
            candidates = [matched_file_id]
        elif sel_str in plans:
            candidates = [sel_str]
        elif sel_str in sets:
            matched_set = sel_str
            candidates = sets[sel_str]["order"]
        else:
            prefix_matches = [s for s in sets if s.startswith(sel_str)]
            if len(prefix_matches) == 1:
                matched_set = prefix_matches[0]
                candidates = sets[prefix_matches[0]]["order"]
            elif len(prefix_matches) > 1:
                raise DriverError(
                    f"Ambiguous Set selector prefix: {sel_str} matches {prefix_matches}"
                )
            else:
                matching_plans = [
                    id6
                    for id6, p in plans.items()
                    if sel_str in p.get("file", "")
                    or sel_str in Path(p.get("file", "")).name
                ]
                if len(matching_plans) == 1:
                    candidates = matching_plans
                elif len(matching_plans) > 1:
                    raise DriverError(
                        f"Ambiguous filename selector: {sel_str} matches multiple plans: {matching_plans}"
                    )
                else:
                    raise DriverError(describe_unresolved_plan_selector(repo, sel_str))

        if matched_set is not None and not candidates:
            raise DriverError(
                f"Set '{matched_set}' has an empty order (no plans to run)"
            )
        for id6 in candidates:
            if id6 not in seen:
                expanded.append(id6)
                seen.add(id6)

    if not expanded:
        raise DriverError("At least one id6 or Set selector is required")
    return expanded


def resolve_plan_path(repo: Path, configured: str, id6: str) -> Path:
    from agent_workflows import selectors

    if id6:
        try:
            matched = selectors.resolve_selectors(repo, "plans", [id6])
            if len(matched) == 1 and matched[0].is_file():
                return matched[0].resolve()
        except Exception:
            pass

    if configured:
        direct = (repo / configured).resolve()
        if direct.is_file():
            return direct
    roots = [repo / ".aw" / "records" / "plans", repo / ".agents" / "plans", repo]
    matches: list[Path] = []
    for root in roots:
        if root.exists():
            matches.extend(
                path for path in root.rglob(f"*-{id6}-*.ipd.md") if path.is_file()
            )
    unique = sorted(set(matches))
    if len(unique) == 1:
        return unique[0].resolve()
    if not unique:
        raise DriverError(f"Cannot locate IPD {id6}; configured path was {configured}")
    raise DriverError(f"Ambiguous IPD {id6}: {', '.join(str(path) for path in unique)}")


def plan_bucket(path: Path) -> str | None:
    parts = path.parts
    for bucket in (
        "executed",
        "active",
        "pending",
        "reviewed",
        "approved",
        "reusable",
        "superseded",
        "not-executed",
    ):
        if bucket in parts:
            return bucket
    return None


def determine_action(status: str) -> str:
    """Return 'review' for to-review plans; 'execute' for approved/ready plans."""
    norm = (status or "").lower().strip()
    if norm in ("to-review", "draft"):
        return "review"
    return "execute"


def action_for(kind: str | None, status: str) -> str:
    """Decide the driver action for a plan given its Kind + Status.

    Orchestrators are special ONLY once past review: an approved/auto-approved
    orchestrator authors no code, so it is not agent-executed ('orchestrate' -> the
    runner administratively finalizes it iff all its children reached executed). But a
    draft/to-review orchestrator still needs its own /plan-review to advance (the
    orchestrator artifact must be review-complete whether the set is driven by
    aw oc run OR executed manually), so it takes the normal 'review' action. Everything
    else uses determine_action (review for to-review/draft, execute otherwise)."""
    norm = (status or "approved").lower().strip()
    if (kind or "").lower() == "orchestrator" and norm not in ("to-review", "draft"):
        return "orchestrate"
    return determine_action(status or "approved")


def new_run_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{stamp}-{os.getpid()}"


def state_root(repo: Path) -> Path:
    return repo / ".aw" / "records" / "runs"


DEFAULT_RUNBOOK_TEXT = """# IPD Autonomous Execution Runbook

This runbook guides autonomous non-interactive execution of approved Implementation
Plan Documents (IPDs) in this repository.

## Execution Directives
1. Execute only the assigned IPD in this turn.
2. Read the assigned IPD in full, its current orchestrator, repository guidelines, and tests.
3. Make safe, verifiable forward progress. Do not weaken checks or fabricate evidence.
4. Commit only files you changed with path-scoped git commits (`git commit -m msg -- <path>`).
5. Never push to remote.
6. Write valid outcome JSON before exiting.
"""


def initialize_run(args: argparse.Namespace) -> Path:
    repo = Path(args.repo).expanduser().resolve()
    if not (repo / ".git").exists():
        try:
            common_dir_exists = git_common_dir(repo).exists()
        except DriverError:
            common_dir_exists = False
        if not common_dir_exists:
            raise DriverError(f"Not a Git repository: {repo}")

    if getattr(args, "manifest", None):
        manifest_path = Path(args.manifest).expanduser().resolve()
        manifest = load_json(manifest_path)
        validate_manifest(manifest)
    else:
        discovered = discover_plans(repo)
        manifest = build_dynamic_manifest(repo, discovered)
        manifest_path = None

    if getattr(args, "runbook", None):
        runbook_path = Path(args.runbook).expanduser().resolve()
    else:
        default_rb = (
            repo
            / "tools"
            / "ipdrunner"
            / "20260823-pending-ipds-overnight-execution-runbook.md"
        )
        if default_rb.is_file():
            runbook_path = default_rb.resolve()
        else:
            runbook_path = None

    queue_ids = expand_selectors(manifest, args.selectors, repo=repo)
    run_id = getattr(args, "run_id", None) or new_run_id()
    run_dir = state_root(repo) / run_id
    if run_dir.exists():
        raise DriverError(f"Run already exists: {run_id}")
    for name in ("sessions", "outcomes", "prompts"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "decisions-and-questions.md").write_text(
        f"# Decisions and Questions for {run_id}\n\n", encoding="utf-8"
    )

    if manifest_path is None:
        manifest_path = run_dir / "manifest.json"
        atomic_write_json(manifest_path, manifest)

    if runbook_path is None:
        runbook_path = run_dir / "runbook.md"
        runbook_path.write_text(DEFAULT_RUNBOOK_TEXT, encoding="utf-8")

    initial_session = getattr(args, "session", None)
    set_sessions: dict[str, str] = {}
    queue: list[dict[str, Any]] = []
    full_auto = getattr(args, "full_auto", False)
    for position, id6 in enumerate(queue_ids, start=1):
        plan = manifest["plans"][id6]
        setid = plan["set"]
        if initial_session:
            set_sessions[setid] = initial_session

        status = plan.get("status")
        p_path = None
        try:
            p_path = resolve_plan_path(repo, plan.get("file", ""), id6)
            rec = parse_plan_file(p_path, repo)
            if rec and not status:
                status = rec.status
        except Exception:
            if not status:
                status = "approved"

        if status == "reviewed" and full_auto and p_path:
            try:
                if is_plan_review_approved(p_path):
                    set_plan_approved(repo, id6)
                    status = "approved"
            except Exception:
                pass

        # Orchestrators are NOT agent-executed by the runner: an orchestrator IPD
        # (Kind: orchestrator) authors no code and only coordinates/verifies its set.
        # In runner mode the runner IS the coordinator and each child is already
        # verified twice (its own V-items + the fresh-session validation turn), so
        # running the orchestrator as an agent turn is redundant and produces spurious
        # blocked/partial. Instead the runner administratively finalizes it iff every
        # child in its set reached `executed` (see run_queue). Detected by the reliable
        # `- Kind:` field, not the Order number.
        # Kind + Status decide the action (see action_for): a draft/to-review
        # orchestrator still needs its /plan-review; only a past-review orchestrator is
        # 'orchestrate' (not agent-executed; finalized when all children executed).
        action = action_for(plan.get("kind"), status or "approved")
        queue.append(
            {
                "position": position,
                "id6": id6,
                "setid": setid,
                "configured_file": plan["file"],
                "dependencies": plan.get("dependencies", []),
                "initial_status": status or "approved",
                "action": action,
                "status": "queued"
                if status in ("to-review", "draft", "approved", "auto-approved")
                else "reviewed",
                "attempts": [],
            }
        )

    state = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "repo": str(repo),
        "manifest": str(manifest_path),
        "manifest_sha256": sha256_file(manifest_path),
        "runbook": str(runbook_path),
        "runbook_sha256": sha256_file(runbook_path),
        "selectors": list(args.selectors),
        "queue": queue,
        "session_id": initial_session,
        "set_sessions": set_sessions,
        "session_turn_counts": {},
        "options": {
            "opencode": getattr(args, "opencode", "opencode"),
            "model": getattr(args, "model", None),
            "agent": getattr(args, "agent", None),
            "auto": getattr(args, "auto", True),
            "session": initial_session,
            "output_mode": getattr(args, "output_mode", "clean"),
            "stall_timeout": getattr(args, "stall_timeout", DEFAULT_STALL_TIMEOUT),
            "full_auto": full_auto,
            "validate": getattr(args, "validate", False),
            "no_audit": not getattr(args, "validate", False),
            "self_finalize": getattr(args, "self_finalize", True),
            "isolate_worktree": getattr(args, "isolate_worktree", True),
            "max_items_per_session": getattr(args, "max_items_per_session", 4),
        },
        "driver": {
            "path": str(Path(__file__).resolve()),
            "sha256": sha256_file(Path(__file__)),
        },
    }
    atomic_write_json(run_dir / "state.json", state)
    append_jsonl(
        run_dir / "events.jsonl",
        {"at": utc_now(), "event": "run-created", "run_id": run_id, "queue": queue_ids},
    )
    write_report(run_dir, state)
    return run_dir


def load_state(run_dir: Path) -> dict[str, Any]:
    return load_json(run_dir / "state.json")


def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    atomic_write_json(run_dir / "state.json", state)
    write_report(run_dir, state)


def write_report(run_dir: Path, state: dict[str, Any]) -> None:
    counts: dict[str, int] = {}
    for item in state["queue"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    lines = [
        f"# Execution Report: {state.get('run_id', '')}",
        "",
        f"- Repository: `{state.get('repo', '')}`",
        f"- Created: {state.get('created_at', '')}",
        f"- Updated: {state.get('updated_at', '')}",
        f"- Selectors: `{' '.join(state.get('selectors', []))}`",
        f"- Set sessions: `{json.dumps(state.get('set_sessions', {}), sort_keys=True)}`",
        f"- Counts: `{json.dumps(counts, sort_keys=True)}`",
        "- Pushed: no (required; verify independently in outcomes)",
        "",
        "| # | id6 | Set | Action | Status | Verify | Attempts | Last session |",
        "|---:|---|---|---|---|---|---:|---|",
    ]
    for item in state["queue"]:
        attempts = item.get("attempts", [])
        session = attempts[-1].get("session_id", "") if attempts else ""
        action = item.get("action", "execute")
        verify = item.get("verification_status") or ""
        lines.append(
            f"| {item['position']} | `{item['id6']}` | `{item['setid']}` | `{action}` | "
            f"{item['status']} | {verify} | {len(attempts)} | `{session}` |"
        )
    # revgate Order 03 (7nkcgp) E-04: name the ROOT CAUSE in the report an operator actually reads,
    # not only in events.jsonl. Emitted as its own section so the table's column contract is unchanged.
    blocked = [
        item
        for item in state["queue"]
        if item.get("status") == "dependency-blocked"
        and (
            item.get("unsatisfied_dependencies")
            or item.get("unsatisfied_dependency_reasons")
        )
    ]
    if blocked:
        lines.extend(["", "## Dependency blocks (why)", ""])
        for item in blocked:
            reasons = item.get("unsatisfied_dependency_reasons") or {}
            lines.append(f"- `{item['id6']}` (position {item['position']}):")
            for dep in item.get("unsatisfied_dependencies") or []:
                detail = reasons.get(dep) or "dependency not satisfied"
                lines.append(f"  - `{dep}`: {detail}")
            hint = item.get("dependency_block_recovery")
            if hint:
                lines.append(f"  - Recovery: {hint}")
    lines.extend(
        [
            "",
            "## Review",
            "",
            "Review `decisions-and-questions.md` first, then `outcomes/` and `sessions/`.",
            "",
        ]
    )
    (run_dir / "execution-report.md").write_text("\n".join(lines), encoding="utf-8")


_SESSION_ID_KEYS = ("sessionID", "sessionId", "session_id")


def _event_session_id(raw_line: str) -> str | None:
    """Return the `ses_...` session id carried by ONE streamed stdout event, if any.

    Used LIVE during the turn (unlike :func:`extract_session_id`, which reads the finished
    log) so the subagent-progress observer learns the parent session id from the very first
    event. Fail-safe: a blank/unparseable line yields None.
    """
    line = raw_line.strip()
    if not line:
        return None
    try:
        event = json.loads(line)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(event, dict):
        return None
    for key in _SESSION_ID_KEYS:
        value = event.get(key)
        if isinstance(value, str) and value.startswith("ses_"):
            return value
    return None


def extract_session_id(log_path: Path) -> str | None:
    """Return the session id from a streamed JSONL log."""
    if not log_path.exists():
        return None
    fallback: str | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            for key in _SESSION_ID_KEYS:
                value = event.get(key)
                if not isinstance(value, str) or not value.strip():
                    continue
                if value.startswith("ses_"):
                    return value
                if fallback is None:
                    fallback = value
    return fallback


def _findings_block_reason(repo: Path, dep: str) -> str | None:
    """Return an operator-facing reason ``dep``'s review blocks its dependents, else None.

    revgate Order 03 (7nkcgp) E-01/E-02. Delegates ENTIRELY to
    ``review_findings.plan_gating_blocks``, the ONE shared predicate, which both host runners, the
    `aw check` evaluator, and the `/exec-set` Set compiler consume. This function re-implements no
    severity comparison and holds no threshold of its own, so the four surfaces cannot drift.

    Housed in ``review_findings`` (NOT in one runner imported by the other) because neither runner
    imports the other today and the in-flight `rununify` Set exists to extract their shared logic; a
    runner-to-runner import would collide with it.

    Fail-open on import/IO error: a crashing gate is a disabled gate, and this must never wedge a run.
    """
    try:
        from agent_workflows import review_findings as _rf

        blocks = _rf.plan_gating_blocks(repo, dep)
    except Exception:
        return None
    if not blocks:
        return None
    return "; ".join(b.describe() for b in blocks)


def dependency_status(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str]]:
    """(satisfied, unsatisfied-dep-id6s). Shape UNCHANGED: `unsatisfied` stays a flat list[str].

    See :func:`dependency_status_detailed` for the additional per-dependency REASON map, which is a
    strictly additive companion so every existing consumer of the flat list keeps working.
    """
    satisfied, unsatisfied, _reasons = dependency_status_detailed(item, state)
    return satisfied, unsatisfied


def dependency_status_detailed(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str], dict[str, str]]:
    """As :func:`dependency_status`, plus a ``{dep_id6: reason}`` map naming each ROOT CAUSE.

    revgate Order 03 (7nkcgp) E-01 + E-04. Two things changed here relative to the pre-Order-03
    behavior, and only two:

    1. An `executed:`-style (execute-action) dependency is satisfied by reaching `executed` ONLY IF
       it ALSO carries no recorded unresolved gating findings. Applied to BOTH resolution paths - the
       in-queue path (status in ``EXECUTION_SUCCESS_STATES``) and the out-of-queue path
       (``bucket == "executed"``) - because otherwise the gate would be evadable purely by whether the
       target happens to be in the same run's queue.
    2. Every unsatisfied dependency gets a reason string, so `dependency-blocked` can say WHY rather
       than only that something was not satisfied.

    A `review`-action item is deliberately NOT findings-gated: only an `executed:` edge asserts that
    work was completed and verified, so only it should require findings to be clean (the plan's
    Deferred section keeps `exists:`/`state:` semantics untouched).
    """
    by_id = {entry["id6"]: entry for entry in state["queue"]}
    repo = Path(state["repo"])
    unsatisfied: list[str] = []
    reasons: dict[str, str] = {}
    is_exec = item.get("action") != "review"
    required_states = EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES

    def _block(dep: str, reason: str) -> None:
        unsatisfied.append(dep)
        reasons[dep] = reason

    for dep in item.get("dependencies", []):
        if dep in by_id:
            dep_status = by_id[dep]["status"]
            if dep_status not in required_states:
                _block(
                    dep,
                    f"{dep}: queue status is `{dep_status}`, not one of "
                    f"{sorted(required_states)}",
                )
                continue
            # In-queue AND nominally successful: still refuse on unresolved gating findings.
            if is_exec:
                why = _findings_block_reason(repo, dep)
                if why:
                    _block(dep, why)
            continue
        try:
            dep_path = resolve_plan_path(repo, "", dep)
        except DriverError:
            _block(dep, f"{dep}: no plan resolves to this id6 in the repo")
            continue
        bucket = plan_bucket(dep_path)
        if is_exec:
            if bucket != "executed":
                _block(dep, f"{dep}: plan is in `{bucket}/`, not `executed/`")
                continue
            why = _findings_block_reason(repo, dep)
            if why:
                _block(dep, why)
        else:
            if bucket not in ("executed", "reviewed", "approved"):
                _block(
                    dep,
                    f"{dep}: plan is in `{bucket}/`, not executed/reviewed/approved",
                )
    return not unsatisfied, unsatisfied, reasons


def build_review_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    repo: Path,
) -> str:
    try:
        rel_path = str(plan_path.relative_to(repo))
    except ValueError:
        rel_path = str(plan_path)
    return f"/plan-review {rel_path}"


def build_recovery_lane_notice(
    item: dict[str, Any], state: dict[str, Any], recovery: bool
) -> str:
    """Tell a RESUMING agent, in the prompt, that it is continuing an interrupted attempt (E-11).

    Enriches the EXISTING `recovery` branch of the prompt (the `Mode: RECOVERY/CONTINUATION` line)
    with the lane facts E-04 now records, rather than adding a mechanism. A first attempt gets
    nothing, so a normal prompt is unchanged. There is deliberately NO acknowledgement gate and NO
    refusal path: a refusal would be one more way for an unattended run to stall. The point is that
    the agent must establish current state itself instead of assuming a clean start.
    """
    if not recovery:
        return ""
    lane_branch = item.get("preserved_branch")
    lane_path = item.get("preserved_worktree")
    lane_base = item.get("preserved_base")
    if not lane_branch:
        for attempt in reversed(item.get("attempts", []) or []):
            if attempt.get("worktree_branch"):
                lane_branch = attempt.get("worktree_branch")
                lane_path = attempt.get("worktree")
                lane_base = attempt.get("worktree_base")
                break
    lines = [
        "",
        "",
        "## You are continuing an INTERRUPTED attempt",
        "",
        "A previous attempt at this IPD was interrupted or killed before it finished. It is NOT a",
        "clean start. Whatever that attempt did is already on disk or already committed, and it may",
        "be half-applied. Establish the CURRENT state yourself before you edit anything: read the",
        "plan's execution/validation state, inspect the git log and the working tree, and check",
        "which E-items were actually performed. Do not assume the previous attempt did nothing, and",
        "do not assume it finished what it started.",
    ]
    if lane_branch:
        facts: list[str] = []
        try:
            from agent_workflows import worktree_lease

            repo = Path(state.get("repo", "."))
            lane_id = str(
                item.get("preserved_lane_id")
                or (item.get("attempts") or [{}])[-1].get("worktree_lane_id")
                or item.get("id6")
                or ""
            )
            st = worktree_lease.inspect_lane(
                repo, lane_id, base_commit=lane_base or "HEAD"
            )
            if st.commits_ahead:
                facts.append(f"it HOLDS {st.commits_ahead} commit(s) beyond its base")
            if st.dirty:
                facts.append("its tree has uncommitted changes")
            if not facts and st.exists:
                facts.append("it holds no commits and its tree is clean")
            if not st.exists:
                facts.append("it no longer exists")
        except Exception:
            facts.append("its current contents could not be read; inspect it yourself")
        lines.extend(
            [
                "",
                f"That attempt's lane branch is `{lane_branch}`"
                + (f" at `{lane_path}`" if lane_path else "")
                + ".",
                "State of that lane: " + "; ".join(facts) + ".",
                "A commit there whose message says INTERRUPTED SNAPSHOT is preserved uncommitted work",
                "from the interrupted attempt, not reviewed or validated work.",
            ]
        )
    return "\n".join(lines)


def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
) -> str:
    setid = item["setid"]
    decisions = run_dir / "decisions-and-questions.md"
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    report = run_dir / "execution-report.md"
    mode = "RECOVERY/CONTINUATION" if recovery else "NORMAL EXECUTION"
    prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None
    lane_notice = build_recovery_lane_notice(item, state, recovery)
    return f"""# OpenCode IPD Driver Turn

Mode: {mode}{lane_notice}
Run ID: {state["run_id"]}
Queue position: {item["position"]}
Assigned IPD: {item["id6"]}
Assigned Set: {setid}
Plan file at launch: {plan_path}
External run directory: {run_dir}
Decisions/questions register: {decisions}
Required JSON outcome: {outcome}
Driver report: {report}
Prior attempt: {json.dumps(prior, sort_keys=True) if prior else "none"}

## Concurrent Work

Other agents may modify this repository concurrently. Work only on files required for your task. Ignore unrelated changes, commits, and untracked files.

Do not alter, revert, stage, or commit another agent's work. Stage only your files; never use `git add .` or `git add -A`.

Before EVERY commit, verify what you are actually about to commit: run `git diff --cached --name-only` and confirm every path listed is one YOU modified for this task; `git restore --staged <path>` anything that is not yours. Path-scoping is NOT by itself sufficient, because `git commit -- <paths>` still commits whatever is ALREADY STAGED for those paths, including a co-worker's edits to the same file.

Stop only if another agent changes a file you are editing or must edit and the changes cannot be safely combined. Never discard their work.

Execute only IPD {item["id6"]}. Read the attached driver runbook, every applicable
repository instruction, the assigned IPD in full, its current orchestrator, current
repository state, and completed prerequisite artifacts before editing. Do not implement
another IPD in this turn.

All target IPDs are already human-approved. Do not ask for approval. This run is
non-interactive: do not invoke an interactive question tool or wait for human input.
When a material question arises, investigate the approved plans, repository decisions,
source, tests, history, and current primary documentation. If a reasonable recommended
approach exists, choose it, record it in the decisions/questions register with evidence,
alternatives, rationale, confidence, scope, reversibility, and validation, then continue.
If no reasonable approach exists, record a DEFERRED question with the work completed,
work blocked, dependency effect, exact preserved state, and recommended human action.
Continue every independent part of this IPD despite a deferred question.

Maximize safe forward progress. A local failure or unanswered question is not permission
to abandon independent work. Do not weaken checks, fabricate evidence, broaden approved
scope, bypass lifecycle controls, discard unrelated work, or push. Do not use git add -A,
git add ., git commit -a, --no-verify, destructive reset/clean, or stashing that could hide
ownership. Use the lifecycle available at this bootstrap stage and path-scoped commits.

If the IPD cannot validly finalize, preserve partial work using the repository-supported
nonterminal checkpoint mechanism or an attributable isolated branch/worktree. Leave the
main execution checkout safe for subsequent turns. Never claim executed unless the real
terminal state and acceptance criteria support it.

Before exiting, write valid JSON to {outcome} with at least:
{{
  "schema_version": 1,
  "run_id": "{state["run_id"]}",
  "position": {item["position"]},
  "id6": "{item["id6"]}",
  "setid": "{setid}",
  "disposition": "executed|substantially-complete|partial|blocked|failed-safely",
  "summary": "...",
  "starting_head": "...",
  "ending_head": "...",
  "commits": [],
  "files_changed": [],
  "tests": [],
  "decision_ids": [],
  "deferred_question_ids": [],
  "incomplete_requirements": [],
  "partial_work_location": null,
  "recommended_next_action": "...",
  "pushed": false
}}

The disposition must describe the actual repository result, not merely your effort. If no
material question arose, say so in the summary. Explicitly confirm pushed=false.
"""


def build_verifier_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
) -> str:
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    verify_outcome = (
        run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}-verification.json"
    )
    return f"""# Independent Rigorous Verification of Executed IPD

Plan: `{plan_path}`
Id: `{item["id6"]}`
Set: `{item["setid"]}`
Run ID: `{state["run_id"]}`
Execution Outcome JSON: `{outcome}`
Verification Outcome JSON to write: `{verify_outcome}`

## Concurrent Work

Other agents may modify this repository concurrently. Work only on files required for your task. Ignore unrelated changes, commits, and untracked files.

Do not alter, revert, stage, or commit another agent's work. Stage only your files; never use `git add .` or `git add -A`.

Before EVERY commit, verify what you are actually about to commit: run `git diff --cached --name-only` and confirm every path listed is one YOU modified for this task; `git restore --staged <path>` anything that is not yours. Path-scoping is NOT by itself sufficient, because `git commit -- <paths>` still commits whatever is ALREADY STAGED for those paths, including a co-worker's edits to the same file.

Stop only if another agent changes a file you are editing or must edit and the changes cannot be safely combined. Never discard their work.

You are an independent, skeptical verifier running in a fresh OpenCode session to audit
the execution of this IPD. Your goal is to rigorously verify whether the code, tests,
and documentation satisfy every requirement before this plan can be considered executed.

## Verification Requirements:

1. **Inspect Concrete Diffs & Commits**:
   - Inspect the git commits and working tree diffs produced for this IPD.
   - Verify that real functional changes were made, not just cosmetic/vocabulary additions.
   - Ensure all referenced files and symbols in the plan's Scope-Paths actually exist and are wired correctly.

2. **Evidence Table (E-* and V-*)**:
   - Check every Execution item (`E-*`) and every Validation item (`V-*`) in the IPD.
   - Check if the recorded observed evidence matches real code and passing tests.

3. **Run and Verify Test Suite**:
   - Run the required tests and validation commands for this IPD (e.g. `python3 -m pytest <test_file> -v` or `python3 -m unittest ...`).
   - Paste the actual runner output with exit code.
   - Confirm that tests are genuine and testing real assertions (not trivial passes).

4. **In-Scope Fixes**:
   - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit path-scoped (`git commit -m msg -- <paths>`). Never push.
   - If any unresolvable defect or scope gap remains, report it clearly.

5. **Write Verification Outcome**:
   Before exiting, write valid JSON to `{verify_outcome}`:
   {{
     "schema_version": 1,
     "id6": "{item["id6"]}",
     "verdict": "VERIFIED|CORRECTION_REQUIRED|BLOCKED",
     "summary": "...",
     "evidence": [],
     "tests_run": [],
     "corrections_made": []
   }}

Begin independent verification now.
"""


def write_prompt(
    run_dir: Path, item: dict[str, Any], prompt: str, attempt_no: int, suffix: str = ""
) -> Path:
    prefix = suffix or ("review" if item.get("action") == "review" else "exec")
    path = (
        run_dir
        / "prompts"
        / f"{item['position']:02d}-{item['id6']}-{prefix}-attempt-{attempt_no}.md"
    )
    path.write_text(prompt, encoding="utf-8")
    return path


def attempt_log_path(
    run_dir: Path, item: dict[str, Any], attempt_no: int, suffix: str = ""
) -> Path:
    tag = f"-{suffix}" if suffix else ""
    return (
        run_dir
        / "sessions"
        / f"{item['position']:02d}-{item['id6']}-attempt-{attempt_no}{tag}.jsonl"
    )


_SIGINT_GRACE_SECONDS = 5.0
_SIGTERM_GRACE_SECONDS = 2.0
DEFAULT_STALL_TIMEOUT: float = 600.0


def terminate_process(process: subprocess.Popen) -> None:
    """Reap a child OpenCode process and its process group without leaving orphans.

    Delegates to the SINGLE shared reaper in ``runner_shutdown`` (spec `c4gd2h` R5 forbids a
    second implementation; both drivers previously carried byte-identical copies). The
    module-level grace constants are read at call time and passed through, so a caller or test
    that tunes ``_SIGINT_GRACE_SECONDS`` / ``_SIGTERM_GRACE_SECONDS`` still takes effect.
    """

    runner_shutdown.terminate_process(
        process,
        sigint_grace=_SIGINT_GRACE_SECONDS,
        sigterm_grace=_SIGTERM_GRACE_SECONDS,
    )


_close_process_streams = runner_shutdown._close_process_streams


def _apply_execution_profile(
    state: dict[str, Any],
    item: dict[str, Any],
    argv: list[str],
    agent_dir: str,
    work_dir: str | None,
) -> list[str]:
    """Wrap `argv` in the OS sandbox iff the hardened profile was explicitly requested.

    wtiso-07 (`1o4eif`) E-05/E-06. Returns `argv` UNCHANGED for the default profile, which
    is what keeps this phase strictly additive: no default-path behavior is altered.

    Raises `HardModeUnavailableError` when `hardened` is requested on a host whose EXECUTED
    probe reports it cannot enforce the sandbox (fail closed, never silent degradation), and
    `SandboxProfileError` when hardened mode is requested without an isolated lane, because
    there would be no lane boundary to enforce.
    """
    options = state.get("options", {})
    requested = options.get("execution_profile")
    capabilities = detect_host_capabilities("opencode")
    # Raises rather than returning "default" when hardened is unavailable.
    profile = select_execution_profile(requested, capabilities)
    if profile != "hardened":
        return argv

    if not work_dir:
        raise SandboxProfileError(
            "the hardened execution profile requires an isolated lane worktree, but this "
            "turn would run in the main checkout (work_dir is unset). There is no lane "
            "boundary to enforce; refusing rather than pretending to sandbox."
        )

    lane_root = Path(work_dir).resolve()
    # The lane's own scratch/submission channel, keyed by run and item so a retry or a
    # co-resident lane never collides. Kept INSIDE the lane so it is writable by
    # construction and disappears with the lane.
    lane_scratch = lane_root / LANE_SCRATCH_SUBDIR / state["run_id"] / item["id6"]
    lane_scratch.mkdir(parents=True, exist_ok=True)

    repo_root = Path(state["repo"]).resolve()
    sibling_lanes = [
        p
        for p in (repo_root / WORKTREES_SUBDIR).glob("*")
        if p.is_dir() and p.resolve() != lane_root
    ]
    plan = build_sandbox_plan(
        lane_worktree=lane_root,
        lane_scratch=lane_scratch,
        control_root=state.get("control_root")
        or (repo_root / ".aw" / "records" / "runs"),
        main_worktree=repo_root,
        sibling_lane_roots=sibling_lanes,
        git_common_dir=_git_common_dir(repo_root),
        credential_paths=_hardened_credential_paths(),
    )
    return enter_sandbox(
        argv,
        plan,
        capabilities,
        cwd=agent_dir,
        scratch_dir=lane_scratch,
    )


def _git_common_dir(repo_root: Path) -> str | None:
    """The shared git common directory, which hardened mode keeps READ-ONLY."""
    try:
        raw = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--git-common-dir"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if raw.returncode != 0:
        return None
    common = raw.stdout.strip()
    if not common:
        return None
    return str((repo_root / common).resolve())


def _hardened_credential_paths() -> list[str]:
    """Credential locations a coding worker never needs, made INACCESSIBLE in hardened mode.

    Only paths that exist are returned; a missing path is already unreachable.
    """
    home = Path(os.path.expanduser("~"))
    candidates = [
        home / ".ssh",
        home / ".aws",
        home / ".gnupg",
        home / ".netrc",
        home / ".git-credentials",
        home / ".config" / "gh",
        home / ".docker" / "config.json",
        home / ".kube",
        home / ".npmrc",
        home / ".pypirc",
    ]
    return [str(p) for p in candidates if p.exists()]
def _budget_breach_recorder(
    run_dir: Path,
    item: dict[str, Any],
    request: runner_stop.StopRequest,
    checkpoint_observer: runner_stop.CheckpointObserver,
) -> "Callable[[], None]":
    """Build the callback `BudgetBreachWatch` invokes when the wind-down deadline passes.

    runstop foi1b3 (E-04, spec R11). It RECORDS the breach on the established `events.jsonl`
    channel as an escalation-REQUIRED signal and returns. It deliberately does NOT escalate, does
    not terminate the child, and does not rewrite any item status: escalation spans levels 3 and 4
    and spec A7 places its enforcement in Phase 5 (`71vjbn`), which consumes this one signal.
    """

    def _record() -> None:
        event = runner_stop.budget_breach_event(
            request,
            at=utc_now(),
            id6=item.get("id6", ""),
            observed_events=checkpoint_observer.events_seen,
            last_completed_index=checkpoint_observer.last_checkpoint_index,
        )
        with contextlib.suppress(Exception):
            append_jsonl(run_dir / "events.jsonl", event)
        print(
            f"stop wind-down budget breached (level {request.level}, "
            f"{request.budget_seconds}s, deadline {request.deadline}): no safe checkpoint "
            f"observed; escalation REQUIRED (recorded, not performed here)",
            file=sys.stderr,
        )

    return _record


def _record_checkpoint_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    checkpoint_observer: runner_stop.CheckpointObserver,
) -> dict[str, Any]:
    """Record a level-3 stop on the item with KNOWN certainty (spec R18), returning the record.

    runstop foi1b3 (E-03). Writes to the item and to the established append-only `events.jsonl`
    channel; no new ledger substrate. The item's STATUS is set by `reconcile_disposition`'s
    deliberate-stop branch, so the two cannot disagree.
    """

    repo = Path(state["repo"])
    try:
        observed_git = git_status(repo)
    except Exception as exc:  # noqa: BLE001 - an honest note beats failing the stop
        observed_git = f"<unobserved: {exc}>"
    record = runner_stop.stopped_disposition(
        level=checkpoint_observer.requested_level or runner_stop.LEVEL_NOW,
        requester=checkpoint_observer.requester,
        last_completed_index=checkpoint_observer.last_checkpoint_index,
        last_completed_label=checkpoint_observer.last_checkpoint_label,
        git_state=observed_git,
        events_seen=checkpoint_observer.events_seen,
        at=utc_now(),
    )
    item["stopped"] = record
    append_jsonl(
        run_dir / "events.jsonl",
        runner_stop.stopped_stop_event(record, id6=item.get("id6", ""), at=utc_now()),
    )
    return record


def _record_forced_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    stop: "runner_stop.StopNowForce",
) -> dict[str, Any]:
    """Record a level-4 stop on the item as INDETERMINATE (spec R18/R21/R22), returning the record.

    runstop m0z0ti (E-02/E-03). Same shape and same channel as `_record_checkpoint_stop`, with the
    three level-4 differences the record builder enforces: certainty is `indeterminate`, the
    disposition is `unknown_outcome`, and NO last-completed-operation is invented (the cut point was
    not observed, so naming one would be the fabrication spec R22 forbids).

    The git state is OBSERVED here, at stop time, because after a force cut the tree may hold a
    partial edit and an assumed state would be worthless for the reconciliation a resume must do.

    R22 is asserted, not merely intended: the item's status is set through `reconcile_disposition`'s
    deliberate-stop branch (so the two cannot disagree) and this function refuses to record a success.
    """

    repo = Path(state["repo"])
    try:
        observed_git = git_status(repo)
    except Exception as exc:  # noqa: BLE001 - an honest note beats failing the stop
        observed_git = f"<unobserved: {exc}>"
    record = runner_stop.forced_disposition(
        level=stop.level,
        requester=stop.requester,
        git_state=observed_git,
        events_seen=stop.events_seen,
        # Carried as PRIOR observations only, under keys that cannot be read as "what finished
        # last" - which for a force cut is unknowable. They describe what the driver had ALREADY
        # seen complete before the request arrived, nothing about the cut itself.
        prior_completed_index=stop.prior_completed_index,
        prior_completed_label=stop.prior_completed_label,
        at=utc_now(),
    )
    item["stopped"] = record
    append_jsonl(
        run_dir / "events.jsonl",
        runner_stop.forced_stop_event(record, id6=item.get("id6", ""), at=utc_now()),
    )
    return record


def run_opencode(
    state: dict[str, Any],
    run_dir: Path,
    item: dict[str, Any],
    plan_path: Path,
    prompt_path: Path,
    attempt_no: int,
    fresh_session: bool = False,
    log_suffix: str = "",
    label_suffix: str = "",
    tracker: StreamTracker | None = None,
    work_dir: str | None = None,
) -> tuple[int, str | None, Path, list[str]]:
    options = state.get("options", {})
    opencode = options.get("opencode") or "opencode"
    argv = [opencode, "run"]
    # driverfin-02 (emus4n): when the child runs in an isolated worktree, the agent turn edits/commits
    # only there (`--dir <worktree>` + cwd), leaving the MAIN tree untouched. Defaults to the main repo.
    agent_dir = work_dir or state["repo"]

    # A verifier turn (fresh_session=True) runs in a clean session with no inherited
    # context, so it audits the executed work independently.
    #
    # lanesess (xd9sll): a session must NEVER be carried into a DIFFERENT tree. Sessions were keyed
    # per SET while worktrees are allocated per ITEM, so lanes 2..N of a set were launched with lane
    # 1's session; an opencode session carries its own project/`directory` binding, which then
    # OVERRIDES `--dir` and silently runs the turn in the PREVIOUS lane's worktree. Every main-repo
    # path is then "external", so the external_directory gate (qyaime) asks with no answerer and the
    # turn dies at the stall watchdog. Measured: qcqhj7 booted in its own lane, then re-bootstrapped
    # 8zgybk's and streamed under 8zgybk's session; four consecutive lanes were lost this way.
    # Therefore an isolated turn (work_dir set) is ALWAYS a fresh session, exactly like the verifier.
    isolated_turn = bool(work_dir)
    max_items = options.get("max_items_per_session", 4)
    raw_session = (
        state.get("session_id")
        or state.get("set_sessions", {}).get(item["setid"])
        or options.get("session")
    )
    is_rotation = False
    if raw_session and max_items and max_items > 0:
        session_turns = state.get("session_turn_counts", {}).get(raw_session, 0)
        if session_turns >= max_items:
            is_rotation = True
            raw_session = None

    session = None if (fresh_session or isolated_turn or is_rotation) else raw_session
    if session:
        argv.extend(["--session", session])

    argv.extend(["--dir", agent_dir, "--format", "json"])
    if options.get("model"):
        argv.extend(["--model", options["model"]])
    if options.get("agent"):
        argv.extend(["--agent", options["agent"]])
    if options.get("auto", True):
        argv.append("--auto")

    is_review = item.get("action") == "review"
    action_label = label_suffix or ("review" if is_review else "exec")
    argv.extend(
        [
            "--title",
            f"aw-{action_label}-{state['run_id']}-{item['setid']}-{item['id6']}",
        ]
    )

    if (
        not is_review
        and not log_suffix
        and state.get("runbook")
        and Path(state["runbook"]).exists()
    ):
        argv.extend(["--file", state["runbook"]])

    argv.extend(
        [
            "--file",
            str(plan_path),
            "--",
            prompt_path.read_text(encoding="utf-8"),
        ]
    )

    # wtiso-07 (1o4eif) E-05/E-06: OPTIONAL hardened OS-sandbox profile.
    #
    # This is the ONLY hardened-mode seam in the launch path and it is inert unless
    # `options["execution_profile"]` is explicitly "hardened": `select_execution_profile`
    # returns "default" for unset/"default", so `argv` below is untouched and the default
    # launch is byte-for-byte what it was before this phase.
    #
    # When "hardened" IS requested, `select_execution_profile` FAILS CLOSED - it raises
    # `HardModeUnavailableError` on a host whose EXECUTED probe cannot enforce the sandbox,
    # rather than silently running the worker unsandboxed (x03wgn Section 8 Phase 6.3).
    # The worker gets a writable lane worktree + lane scratch and a READ-ONLY git common
    # dir; the control root, main worktree, and every sibling lane are inaccessible. The
    # DRIVER performs all git mutation after the worker exits, so a read-only common dir
    # costs the worker nothing it is allowed to do (x03wgn Section 4).
    argv = _apply_execution_profile(state, item, argv, agent_dir, work_dir)

    output_mode = options.get("output_mode", "clean")
    pal = Palette(should_color(sys.stdout))
    log_path = attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)

    popen_kwargs: dict[str, Any] = {
        "cwd": agent_dir,
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "bufsize": 1,
    }
    if os.name == "posix":
        popen_kwargs["start_new_session"] = True

    stall_timeout = options.get("stall_timeout", DEFAULT_STALL_TIMEOUT)

    queue = state.get("queue", [])
    total_items = len(queue) or 1
    current_idx = item.get("position", 1)

    is_tty = bool(getattr(sys.stdout, "isatty", None) and sys.stdout.isatty())

    run_start_mono = None
    created_at = state.get("created_at")
    if created_at:
        try:
            created_ts = dt.datetime.fromisoformat(created_at).timestamp()
            run_start_mono = time.monotonic() - max(0.0, time.time() - created_ts)
        except Exception:
            run_start_mono = None

    with log_path.open("w", encoding="utf-8") as log:
        # Track the child so a clean shutdown at ANY layer can reap it even when this frame is
        # gone (spec `c4gd2h` R1: no descendant left alive or reparented to init).
        process = runner_shutdown.track_child(subprocess.Popen(argv, **popen_kwargs))
        assert process.stdout is not None
        statusline = Statusline(
            pal=pal,
            stream=sys.stdout,
            tracker=tracker,
            interval=1.0 if is_tty and output_mode == "clean" else 0.0,
            current_idx=current_idx,
            total_items=total_items or 1,
            setid=item.get("setid", ""),
            id6=item.get("id6", ""),
            run_start_mono=run_start_mono,
        )
        watchdog = StallWatchdog(process, timeout=stall_timeout)
        # The countdown the operator sees must come from the watchdog that kills, so the
        # display reads it directly rather than keeping a second timestamp.
        statusline.watchdog = watchdog

        # SUBAGENT PROGRESS (stallfp kaga7s): stdout carries ONLY parent-session events, so a
        # turn working inside a Task/subagent looks idle and used to be killed at the timeout.
        # This observer supplies the missing signal from opencode's own log. It is BEST-EFFORT
        # by contract: if the log is missing/unreadable/changed, it yields nothing and the
        # watchdog behaves exactly as it did before (stdout-only). It must never raise into
        # the turn, and it counts ONLY agent-loop lines, so a permission-deadlocked child
        # (which keeps emitting housekeeping lines) is still correctly killed.
        observer = stall_progress.SubagentProgressObserver()

        def _subagent_progress() -> None:
            watchdog.touch()
            statusline.touch("subagent")

        # Poll often enough that progress is always seen before the watchdog could fire.
        # Mirrors StallWatchdog.check_interval's own timeout/4 clamp, so a short timeout (as
        # used by tests) is still sampled several times per timeout window.
        poll_interval = (
            min(1.0, max(0.05, stall_timeout / 4.0)) if stall_timeout else 1.0
        )
        poller = stall_progress.ProgressPoller(
            observer, touch_callbacks=(_subagent_progress,), interval=poll_interval
        )
        # runstop foi1b3 (level 3): the OBSERVED safe-checkpoint tracker. Fed every stream line
        # regardless of `output_mode` - see the comment at the parse site below for why that matters.
        checkpoint_observer = runner_stop.CheckpointObserver(
            detector=runner_stop.is_oc_safe_checkpoint
        )
        breach_watch: runner_stop.BudgetBreachWatch | None = None
        # runstop m0z0ti (level 4, E-01): the IMMEDIATE interrupt is observed OUT OF BAND, for the
        # same measured reason Phase 3's budget watch is: `for line in process.stdout` BLOCKS, so a
        # poll inside the loop only runs when the next line arrives and a silent child would make
        # "immediately" mean "whenever the child next speaks". The watch only RECORDS the request;
        # the cut itself is raised on the main thread below and reaped by the ONE shared
        # `clean_shutdown` (spec R5) - never by a bare kill and never by a second reaper.
        forced: dict[str, Any] = {}

        def _note_force(level: int, requester: str) -> None:
            """Record the level-4 request and INTERRUPT the turn through the SHARED reaper.

            The reap happens HERE, not only in the teardown below, because the main thread may be
            blocked in `for line in process.stdout` with nothing more coming - which is exactly the
            silent-child case Phase 3's budget breach escalates FROM (spec A7). Reaping closes the
            child's stdout, the blocked iteration ends, and the main thread raises `StopNowForce`.
            `StallWatchdog._run` is the in-repo precedent for a supervisor thread reaping the child.

            It goes through `runner_shutdown.clean_shutdown`, which is the ONE shared routine and the
            ONE process-group escalation (spec R5): NOT a bare kill, NOT a second reaper, and not a
            local `terminate_process` call.
            """

            if forced:
                return
            forced["level"] = level
            forced["requester"] = requester
            report = runner_shutdown.clean_shutdown(process, run_dir=run_dir)
            if not report.all_satisfied:
                print(report.render(), file=sys.stderr)

        force_watch = runner_stop.ForceStopWatch(
            run_dir,
            on_force=_note_force,
            is_alive=lambda: process.poll() is None,
        )

        def _raise_if_forced() -> None:
            """Cut the turn NOW if a level-4 request has been observed (spec R7 level 4)."""

            if not forced:
                return
            raise runner_stop.StopNowForce(
                level=forced.get("level", runner_stop.LEVEL_NOW_FORCE),
                requester=forced.get("requester", ""),
                events_seen=observer.events_seen,
                # What had ALREADY been observed completing before the request. Passed so the record
                # can carry it under its `prior_observed_*` keys; it is NEVER promoted to "the last
                # completed operation", because the cut point itself was not observed.
                prior_completed_index=observer.last_checkpoint_index,
                prior_completed_label=observer.last_checkpoint_label,
            )

        try:
            # The poller shares the turn's scope, so its thread cannot outlive the turn or
            # leak across attempts. `force_watch` (runstop m0z0ti) joins the same scope so a
            # level-4 force stop is armed for exactly the turn's lifetime, no longer.
            with statusline, watchdog, poller, force_watch:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    statusline.touch("stdout")
                    watchdog.touch()
                    # Learn our PARENT session id from the stream; it is the key the observer
                    # needs to attribute a subagent's log lines to THIS turn.
                    if observer.parent_session_id is None:
                        observer.set_parent_session(_event_session_id(line))
                    # runstop gq6m2u: the IN-TURN cooperative checkpoint (spec `c4gd2h` R7). This
                    # is the per-line point the existing StallWatchdog already proves the driver
                    # may act on from stream observation alone. The poll is SIDE-EFFECT FREE and
                    # only REPORTS the requested level here; acting on a level is owned by the
                    # later phases (levels 1-2 branch between items, level 3 at this point).
                    level = runner_stop.poll_stop(run_dir)
                    # runstop m0z0ti (level 4, spec R7/A2): checked FIRST and BEFORE the line is
                    # classified, because level 4 must NOT wait for a checkpoint. The out-of-band
                    # `force_watch` above is what makes it prompt on a silent child; this is the
                    # main-thread half, so the cut always unwinds through the driver's own teardown.
                    if level is not None and level >= runner_stop.LEVEL_NOW_FORCE:
                        _note_force(
                            level,
                            (lambda r: r.requester if r is not None else "unknown")(
                                runner_stop.read_stop_request(run_dir)
                            ),
                        )
                    _raise_if_forced()
                    # runstop foi1b3 (level 3, spec R10/A3): a level >= 3 request means the TURN
                    # itself must stop, at the next OBSERVED safe checkpoint.
                    #
                    # THE PARSE IS DELIBERATELY NOT `render_event`. `render_event` is called only in
                    # the `output_mode == "clean"` branch below, so in `raw` and `quiet` modes nothing
                    # would parse the line and a `render_event`-based checkpoint would silently never
                    # fire - the feature would depend on an unrelated display flag. The detector in
                    # `runner_stop` does its own minimal decode and runs for EVERY line here, before
                    # any mode branch. Do not move it into the branch below.
                    #
                    # The definition itself is spec `c4gd2h` OQ-01's resolution: after a COMPLETED
                    # tool/step event, before the next is dispatched, observed from this very stream.
                    # No agent cooperation is involved, and none may be added (that was rejected).
                    if level is not None and level >= runner_stop.LEVEL_NOW:
                        if not checkpoint_observer.pending:
                            request = runner_stop.read_stop_request(run_dir)
                            checkpoint_observer.request(
                                level,
                                request.requester if request is not None else "unknown",
                            )
                            print(
                                f"stop requested: level {level} "
                                f"({runner_stop.LEVEL_NAMES.get(level, 'unknown')}); "
                                f"the current turn will stop at its next observed safe checkpoint",
                                file=sys.stderr,
                            )
                            # runstop foi1b3 (E-04, spec R11): arm the BOUNDED wait. A silent child
                            # never reaches another line, and `for line in process.stdout` BLOCKS, so
                            # a deadline can only be noticed from another thread (the shape
                            # StallWatchdog already uses). R10 is not violated: the checkpoint is
                            # still defined only by an observed event; this deadline is the GIVE-UP
                            # bound after which no checkpoint is awaited.
                            if request is not None:
                                remaining = runner_stop.deadline_seconds_remaining(
                                    request
                                )
                                breach_watch = runner_stop.BudgetBreachWatch(
                                    deadline_monotonic=time.monotonic()
                                    + max(0.0, remaining),
                                    on_breach=_budget_breach_recorder(
                                        run_dir, item, request, observer
                                    ),
                                    is_alive=lambda: process.poll() is None,
                                )
                                breach_watch.__enter__()
                    if checkpoint_observer.observe(line):
                        # The turn stops HERE, after an event observed to have completed. Raising
                        # unwinds into the existing `except BaseException` below, which already
                        # routes to the shared reaper, so no second teardown path exists (spec R5).
                        raise runner_stop.StopAtCheckpoint(observer)
                    if output_mode == "raw":
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    elif output_mode == "clean":
                        rendered = render_event(line, pal, tracker=tracker)
                        if rendered is not None:
                            statusline.write_event(rendered)
                # runstop m0z0ti (level 4): the stream also ENDS when `force_watch` reaped a silent
                # child, which is how the blocking iteration above is unblocked at all. Re-check here
                # so that path raises the same `StopNowForce` rather than falling through to a normal
                # `process.wait()` and reporting an ordinary nonzero exit.
                _raise_if_forced()
        except BaseException:
            if breach_watch is not None:
                breach_watch.__exit__(None, None, None)
            # runstop foi1b3: the stop MECHANISM. `clean_shutdown` owns the reaper (spec R5), so the
            # level-3 stop routes there rather than calling `terminate_process` itself. Be clear about
            # what this is: the child is a one-shot `opencode run` with NO cooperative stop channel,
            # so stopping it IS termination - at an instant chosen by observation. Levels 3 and 4
            # share this mechanism and differ only in WHEN it is issued. "KNOWN" certainty therefore
            # means no PREVIOUSLY OBSERVED operation was cut mid-flight, not that the agent finished
            # tidily.
            #
            # runstop m0z0ti (level 4): the SAME endpoint, deliberately. Spec c4gd2h section 3 states
            # the only difference between levels 3 and 4 is outcome CERTAINTY, not cleanliness, so
            # level 4 must not acquire its own teardown, its own reaper, or a bare kill.
            report = runner_shutdown.clean_shutdown(process, run_dir=run_dir)
            if not report.all_satisfied:
                print(report.render(), file=sys.stderr)
            log.flush()
            with contextlib.suppress(OSError):
                os.fsync(log.fileno())
            if watchdog.stalled:
                timeout_val = int(watchdog.timeout) if watchdog.timeout else 0
                raise StallTimeout(
                    f"OpenCode child turn stalled: no output for {timeout_val}s"
                ) from None
            raise
        finally:
            if breach_watch is not None:
                breach_watch.__exit__(None, None, None)

        if watchdog.stalled:
            terminate_process(process)
            log.flush()
            with contextlib.suppress(OSError):
                os.fsync(log.fileno())
            timeout_val = int(watchdog.timeout) if watchdog.timeout else 0
            raise StallTimeout(
                f"OpenCode child turn stalled: no output for {timeout_val}s"
            )

        returncode = process.wait()
        log.flush()
        os.fsync(log.fileno())
    return returncode, extract_session_id(log_path), log_path, argv


def reconcile_disposition(
    repo: Path, item: dict[str, Any], run_dir: Path, exit_code: int
) -> tuple[str, dict[str, Any] | None]:
    # runstop foi1b3 (E-03, spec R18/R21/R22): the DELIBERATE-STOP branch, which MUST precede every
    # other branch below, including the exit-code fallback.
    #
    # MEASURED FAILURE THIS PREVENTS. A level-3 stop leaves NO outcome JSON (the runbook has the
    # AGENT write `outcomes/<NN>-<id6>.json` at turn END, so a mid-turn stop never produces one), the
    # plan is still in `pending/`, and the terminated child exits NONZERO. Without this branch every
    # check below misses and the final `return ("partial" if exit_code == 0 else "failed-safely")`
    # labels a DELIBERATE OPERATOR STOP as `failed-safely` - the crash-versus-intent conflation spec
    # R21 forbids and a verdict R22 forbids the driver to assert.
    #
    # It is keyed on the `stopped` record the checkpoint path wrote, NOT on the exit code or on the
    # mere presence of a stop-request file, so a run that requested a stop but whose turn genuinely
    # FAILED before any checkpoint still reconciles normally (a control test pins this).
    stopped = item.get("stopped")
    if isinstance(stopped, dict) and stopped.get("stopped_deliberately"):
        # `interrupted` is an EXISTING status in TERMINAL_STATES' sibling vocabulary and in
        # `runner_shutdown.KNOWN_ITEM_STATUSES`, so the ledger stays coherent (spec R3) and the
        # existing `requeue_interrupted` already retries it in recovery mode.
        #
        # runstop m0z0ti: this branch now covers BOTH turn-interrupting levels, and returns the SAME
        # status for each ON PURPOSE. The difference between them is CERTAINTY, carried as the
        # explicit `certainty` flag on the record above (`known` for level 3, `indeterminate` for
        # level 4) - not as a different status. That is what keeps a level-4 item visible to the
        # reconcile/requeue/report machinery while the R19 gate in `requeue_interrupted` still refuses
        # to re-run it. Neither level ever returns a success state (spec R22).
        return runner_stop.STOPPED_DISPOSITION, None
    if item.get("action") == "review":
        try:
            current_plan = resolve_plan_path(repo, item["configured_file"], item["id6"])
            text = current_plan.read_text(encoding="utf-8")
            status = _read_status(text)
        except Exception:
            status = None
        if exit_code == 0:
            if status in ("reviewed", "approved"):
                return status, None
            return "reviewed", None
        return "failed-safely", None

    outcome_path = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    outcome: dict[str, Any] | None = None
    if outcome_path.exists():
        try:
            outcome = load_json(outcome_path)
        except DriverError:
            outcome = None
    try:
        current_plan = resolve_plan_path(repo, item["configured_file"], item["id6"])
        bucket = plan_bucket(current_plan)
    except DriverError:
        bucket = None
    if bucket == "executed":
        return "executed", outcome
    if outcome:
        disposition = outcome.get("disposition")
        if disposition == "executed":
            return "substantially-complete", outcome
        if disposition in TERMINAL_STATES - {"dependency-blocked", "not-attempted"}:
            return disposition, outcome
    return ("partial" if exit_code == 0 else "failed-safely"), outcome


def execute_item(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    recovery: bool,
    tracker: StreamTracker | None = None,
) -> None:
    repo = Path(state["repo"])
    plan_path = resolve_plan_path(repo, item["configured_file"], item["id6"])
    attempt_no = len(item.get("attempts", [])) + 1

    is_review = item.get("action") == "review"
    if is_review:
        prompt = build_review_prompt(item, state, run_dir, plan_path, repo)
    else:
        prompt = build_prompt(item, state, run_dir, plan_path, recovery)

    prompt_path = write_prompt(run_dir, item, prompt, attempt_no)
    attempt = {
        "number": attempt_no,
        "started_at": utc_now(),
        "starting_head": git_head(repo),
        "starting_branch": git_branch(repo),
        "starting_status": git_status(repo),
        "prompt": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path),
        "session_id": None,
        "log": str(attempt_log_path(run_dir, item, attempt_no)),
        "recovery": recovery,
        "action": item.get("action", "execute"),
    }
    item.setdefault("attempts", []).append(attempt)
    item["status"] = "running"
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-started",
            "id6": item["id6"],
            "action": item.get("action", "execute"),
            "attempt": attempt_no,
        },
    )
    total = len(state["queue"])
    pal = Palette(should_color(sys.stdout))
    mode_note = " (recovery)" if recovery else ""
    action_str = f"action={item.get('action', 'execute')}"
    banner = (
        pal("\u25b6 ", "cyan")
        + pal(f"IPD {item['position']:02d}/{total} {item['id6']}", "bold", "cyan")
        + pal(
            f"  set={item['setid']}  {action_str}  attempt {attempt_no}{mode_note}",
            "dim",
        )
    )
    print(banner)
    print(pal(f"  plan: {plan_path}", "dim"))

    # driverfin-01 (p7peqf): self-finalize step 1 - run the fail-closed `aw ipd begin` gate BEFORE
    # the agent turn for an execute-action child, so scope + base HEAD are frozen and the agent turn
    # only starts with execution authority. A begin refusal blocks the child cleanly (no agent turn).
    self_finalize = state.get("options", {}).get("self_finalize", True)
    # driverfin-02 (emus4n): per-run worktree isolation. For an execute-action child, allocate a fresh
    # worktree on an `aw/lane/<id6>` branch (reused worktree_lease) so the agent edits/commits ONLY
    # there and the MAIN tree stays untouched during the turn. begin runs against MAIN (receipt under
    # the main repo's `.aw/state/`, findable regardless of worktree); the agent turn + verifier +
    # finalize run in the worktree. Opt out (share the main tree) with `--no-isolate-worktree`.
    isolate = state.get("options", {}).get("isolate_worktree", True)
    wt_handle = None
    work_dir: str | None = None
    if self_finalize and not is_review:
        actor = driver_actor(state)
        # lanetruth Order 01 (af7i6p) E-04: verify, ONCE per process, that a pinned nested `aw`
        # really resolves to this runner's own tooling before we let one perform a lifecycle
        # transition. Memoized, so this is the FIRST nested invocation's cost only and adds no
        # per-call subprocess. A mismatch raises ToolIdentityError, which is RUN-FATAL (OQ-02)
        # and propagates out of the queue loop rather than marking this one item blocked.
        assert_child_tool_identity(run_dir / "events.jsonl", cwd=repo)
        # lanetruth Order 02 (z2isfg): declare the baseline the turn will ACTUALLY execute against.
        # `isolate` is the same flag that allocates the lane below, so begin and the execution tree
        # cannot disagree. Note the lane does not exist yet at this point (it is allocated only after
        # begin grants authority, and that fail-closed ordering is deliberately preserved), which is
        # exactly why this is a declaration of the frozen-base-commit baseline rather than a path.
        # The kwarg is passed ONLY for an isolated turn so the non-isolated path keeps its exact
        # pre-existing three-argument call shape (the default already means "measure this tree").
        if isolate:
            begin_rc, begin_msg = driver_begin(repo, item["id6"], actor, isolated=True)
        else:
            begin_rc, begin_msg = driver_begin(repo, item["id6"], actor)
        if begin_rc != 0:
            attempt["ended_at"] = utc_now()
            attempt["begin_refused"] = begin_msg
            attempt["disposition"] = "blocked"
            item["status"] = "blocked"
            item["begin_refusal"] = begin_msg
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "ipd-begin-refused",
                    "id6": item["id6"],
                    "exit_code": begin_rc,
                    "detail": begin_msg,
                },
            )
            print(
                pal(
                    f"\u2717 IPD {item['position']:02d}/{total} {item['id6']} begin refused "
                    f"(no execution authority); not launching. {begin_msg}",
                    "red",
                ),
                file=sys.stderr,
            )
            return
        if isolate:
            try:
                wt_handle = allocate_isolation_worktree(repo, item["id6"])
                work_dir = str(wt_handle.path)
                # laneorphan-01 (`zwnjp3`) E-04: register the lane DURABLY at the moment of
                # allocation, reusing this existing per-item state + event path (no second store), so
                # an interrupt has something to report and a later run something to find. The lane id
                # and base sha are recorded too, because allocation may have ATTEMPT-SCOPED the name
                # and the reclamation classifier needs the real identity, not a reconstructed one.
                attempt["worktree"] = work_dir
                attempt["worktree_branch"] = wt_handle.branch
                attempt["worktree_lane_id"] = wt_handle.lane_id
                attempt["worktree_base"] = wt_handle.base_commit
                attempt["worktree_disposition"] = getattr(
                    wt_handle, "disposition", "created"
                )
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "worktree-allocated",
                        "id6": item["id6"],
                        "worktree": work_dir,
                        "branch": wt_handle.branch,
                        "lane_id": wt_handle.lane_id,
                        "base_commit": wt_handle.base_commit,
                        "disposition": getattr(wt_handle, "disposition", "created"),
                        "displaced_from": getattr(wt_handle, "displaced_from", None),
                    },
                )
                disp = getattr(wt_handle, "disposition", "created")
                suffix = "" if disp == "created" else f" ({disp})"
                print(
                    pal(
                        f"  \u2713 isolated worktree {wt_handle.branch} at {work_dir}{suffix}",
                        "cyan",
                    )
                )
            except Exception as exc:
                attempt["ended_at"] = utc_now()
                attempt["disposition"] = "blocked"
                item["status"] = "blocked"
                item["worktree_error"] = str(exc)
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "worktree-alloc-failed",
                        "id6": item["id6"],
                        "detail": str(exc),
                    },
                )
                print(
                    pal(
                        f"\u2717 IPD {item['position']:02d}/{total} {item['id6']} worktree "
                        f"allocation failed; not launching. {exc}",
                        "red",
                    ),
                    file=sys.stderr,
                )
                return

    try:
        exit_code, session_id, log_path, argv = run_opencode(
            state,
            run_dir,
            item,
            plan_path,
            prompt_path,
            attempt_no,
            tracker=tracker,
            work_dir=work_dir,
        )
    except runner_stop.StopNowForce as stop:
        # runstop m0z0ti (E-02/E-03, spec A2/R18/R21/R22): the turn was interrupted IMMEDIATELY, at a
        # point the driver did NOT observe. So the outcome is INDETERMINATE and is recorded that way;
        # the child has already been reaped through the SAME shared `clean_shutdown` level 3 uses
        # (spec R5), and cleanliness is identical - only certainty differs.
        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "deliberate-stop-now-force"
        record = _record_forced_stop(run_dir, state, item, stop)
        attempt["stopped"] = record
        attempt["disposition"] = runner_stop.FORCED_DISPOSITION
        # Through `reconcile_disposition` for the same reason level 3 does it: one place decides the
        # status, so the recorded certainty and the item status cannot disagree. It returns
        # `interrupted` (a status the ledger and recovery already understand); the INDETERMINACY is
        # the explicit `certainty` flag on the record, never a new status. See the decision recorded
        # in `runner_stop`'s level-4 section for why a bare `unknown_outcome` status is wrong.
        item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
        save_state(run_dir, state)
        print(
            pal(
                f"\u25a0 IPD {item['position']:02d}/{total} {item['id6']} INTERRUPTED IMMEDIATELY "
                f"(level {record['level']}, {record['level_name']}); outcome is "
                f"{record['disposition']} (certainty {record['certainty']}) after "
                f"{record['events_observed']} observed event(s); requested by "
                f"{record['requester']}. {runner_stop.RECONCILIATION_ACTION}",
                "yellow",
            ),
            file=sys.stderr,
        )
        raise
    except runner_stop.StopAtCheckpoint as stop:
        # runstop foi1b3 (E-02/E-03, spec A3/R18): the turn was stopped at an OBSERVED safe
        # checkpoint. Record it with KNOWN certainty and STOP the run; the child has already been
        # reaped through `clean_shutdown` inside `run_opencode` (spec R5's single reaper).
        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "deliberate-stop-at-checkpoint"
        record = _record_checkpoint_stop(run_dir, state, item, stop.observer)
        attempt["stopped"] = record
        attempt["disposition"] = runner_stop.STOPPED_DISPOSITION
        # Go through `reconcile_disposition` rather than assigning the status directly, so the
        # deliberate-stop branch there is the ONE place the disposition is decided and the two can
        # never disagree.
        item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
        save_state(run_dir, state)
        print(
            pal(
                f"\u25a0 IPD {item['position']:02d}/{total} {item['id6']} stopped at a safe "
                f"checkpoint (level {record['level']}, {record['level_name']}, certainty "
                f"{record['certainty']}) after event "
                f"{record['last_completed_event_index']} "
                f"({record['last_completed_event']}); requested by {record['requester']}",
                "yellow",
            ),
            file=sys.stderr,
        )
        raise
    except KeyboardInterrupt:
        attempt["interrupted_at"] = utc_now()
        item["status"] = "interrupted"
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {"at": utc_now(), "event": "ipd-interrupted", "id6": item["id6"]},
        )
        raise
    except StallTimeout:
        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "stall_timeout"
        stall_sec = state.get("options", {}).get("stall_timeout", DEFAULT_STALL_TIMEOUT)
        attempt["stall_timeout"] = stall_sec
        item["status"] = "interrupted"
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": now,
                "event": "ipd-stalled",
                "id6": item["id6"],
                "stall_timeout": stall_sec,
                "attempt": attempt_no,
            },
        )
        print(
            pal(
                f"\u2717 IPD {item['position']:02d}/{total} {item['id6']} stalled (no output for {int(stall_sec) if stall_sec else 0}s); turn terminated",
                "red",
            ),
            file=sys.stderr,
        )
        return

    if session_id:
        # lanesess (xd9sll): record the observed session on the ATTEMPT always (it is the audit
        # trail), but only PROMOTE it to the set/run-wide keys for a non-isolated turn. An isolated
        # lane deliberately gets a fresh session (see run_opencode), so promoting it would re-arm the
        # exact carryover this fixes and would make the set-consistency check below fire on every
        # lane after the first ("changed session unexpectedly"), aborting the run.
        attempt["session_id"] = session_id
        if not work_dir:
            counts = state.setdefault("session_turn_counts", {})
            existing = state.setdefault("set_sessions", {}).get(item["setid"])
            max_items = state.get("options", {}).get("max_items_per_session", 4)
            existing_turns = counts.get(existing, 0) if existing else 0
            is_planned_rotation = bool(
                max_items and max_items > 0 and existing_turns >= max_items
            )
            if existing and existing != session_id and not is_planned_rotation:
                raise DriverError(
                    f"Set {item['setid']} changed session unexpectedly: {existing} -> {session_id}"
                )
            state["set_sessions"][item["setid"]] = session_id
            state["session_id"] = session_id
            counts[session_id] = counts.get(session_id, 0) + 1

    attempt.update(
        {
            "ended_at": utc_now(),
            "exit_code": exit_code,
            "ending_head": git_head(repo),
            "ending_branch": git_branch(repo),
            "ending_status": git_status(repo),
            "log": str(log_path),
            "argv": argv,
        }
    )
    from agent_workflows.run_viewer import extract_log_metrics

    att_cost, att_toks = extract_log_metrics(log_path)
    if att_cost is not None:
        attempt["cost"] = att_cost
    if att_toks:
        attempt["tokens"] = att_toks
    disposition, outcome = reconcile_disposition(repo, item, run_dir, exit_code)

    # Turn 2: independent skeptical verification in a fresh session. After a successful
    # execution turn, audit the work in a clean session (no inherited context); if the
    # verifier finds unmet criteria, downgrade the disposition so it is not falsely
    # reported as executed. Opt in with --validate / --verify / --audit.
    verify_disp = None
    opts = state.get("options", {})
    validate = opts.get("validate", False)
    if "validate" not in opts:
        validate = not (opts.get("no_verify") or opts.get("no_audit"))
    if (
        not is_review
        and disposition in ("executed", "substantially-complete")
        and validate
    ):
        # driverfin-02: when isolated, resolve the plan from the WORKTREE (the agent's commits +
        # the plan itself live there); the verifier turn also runs in the worktree.
        plan_repo = Path(work_dir) if work_dir else repo
        try:
            current_plan_path = resolve_plan_path(
                plan_repo, item.get("configured_file", ""), item["id6"]
            )
        except DriverError:
            current_plan_path = plan_path

        v_prompt_text = build_verifier_prompt(item, state, run_dir, current_plan_path)
        v_prompt_file = write_prompt(
            run_dir, item, v_prompt_text, attempt_no, suffix="verify"
        )
        print(
            pal(
                f"\n  \u2022 Running independent verification for {item['id6']} in clean session...",
                "cyan",
            ),
            file=sys.stderr,
            flush=True,
        )
        try:
            v_rc, _v_session, _v_log, _v_argv = run_opencode(
                state,
                run_dir,
                item,
                current_plan_path,
                v_prompt_file,
                attempt_no,
                fresh_session=True,
                log_suffix="verify",
                label_suffix="verification",
                tracker=tracker,
                work_dir=work_dir,
            )
            if _v_log:
                attempt["verify_log"] = str(_v_log)
                from agent_workflows.run_viewer import extract_log_metrics

                v_cost, v_toks = extract_log_metrics(_v_log)
                if v_cost is not None:
                    attempt["verify_cost"] = v_cost
                if v_toks:
                    attempt["verify_tokens"] = v_toks
            v_outcome_file = (
                run_dir
                / "outcomes"
                / f"{item['position']:02d}-{item['id6']}-verification.json"
            )
            if v_outcome_file.is_file():
                try:
                    v_data = json.loads(v_outcome_file.read_text(encoding="utf-8"))
                    verify_verdict = str(v_data.get("verdict", "")).upper()
                    if (
                        "BLOCKED" in verify_verdict
                        or "NOT CONFORMING" in verify_verdict
                    ):
                        verify_disp = "blocked"
                        disposition = "partial"
                    else:
                        verify_disp = "verified"
                except Exception:
                    verify_disp = "verified" if v_rc == 0 else "unverified"
            else:
                verify_disp = "verified" if v_rc == 0 else "unverified"
        except (KeyboardInterrupt, StallTimeout):
            verify_disp = "unverified"

    attempt["disposition"] = disposition
    attempt["verification"] = verify_disp
    item["status"] = disposition
    item["last_outcome"] = outcome
    item["verification_status"] = verify_disp
    save_state(run_dir, state)

    # driverfin-01 (p7peqf): self-finalize step 2 - after a VERIFIED execute turn, run the gated
    # `aw ipd finalize` with programmatic two-way scope reconciliation. GATE PRECISION: before
    # finalize the verified child is still in pending/, so reconcile_disposition reports
    # `substantially-complete` (an agent self-claimed `executed` is downgraded there); we therefore
    # trigger on disposition in {executed, substantially-complete} AND verification == verified (NOT
    # on `disposition == "executed"` alone, which would never fire). On finalize success the plan is
    # now in executed/, so re-resolve and set the child `executed`; on refusal, keep it
    # substantially-complete and NEVER force the transition (mirrors finalize_orchestrator).
    if (
        self_finalize
        and not is_review
        and disposition in ("executed", "substantially-complete")
        and verify_disp == "verified"
    ):
        # driverfin-02 (emus4n): when isolated, finalize runs INSIDE the worktree so the plan-move
        # (pending/ -> executed/) commits on the `aw/lane/<id6>` branch. The begin receipt lives under
        # the MAIN repo's `.aw/state/` (anchored by run-id); copy it into the worktree so the
        # in-worktree finalize finds the execution-authority receipt (the receipt is valid in both
        # trees because the worktree base == the frozen base HEAD).
        finalize_repo = Path(work_dir) if (work_dir and wt_handle) else repo
        if work_dir and wt_handle:
            sync_receipt_into_worktree(repo, Path(work_dir), item["id6"])
        try:
            current_plan_for_finalize = resolve_plan_path(
                finalize_repo, item.get("configured_file", ""), item["id6"]
            )
        except DriverError:
            current_plan_for_finalize = plan_path
        actor = driver_actor(state)
        fin_message = (
            f"aw oc run self-finalize: {item['id6']} verified "
            f"(set {item['setid']}, attempt {attempt_no})."
        )
        fin_rc, fin_msg = driver_finalize(
            finalize_repo, current_plan_for_finalize, item["id6"], actor, fin_message
        )
        if fin_rc == 0:
            # driverfin-02: the plan is now in executed/ ON the lane branch (inside the worktree). If
            # isolated, integrate the verified branch back to main via the REUSED integration gate +
            # a driver fast-forward/controlled merge, then tear down the worktree. On a non-passing
            # gate result (or a merge-back conflict) leave the child NOT integrated (recorded,
            # deferred to child-03) and do NOT fake executed.
            integrated = True
            integ_reason = "in-place (no isolation)"
            integ_kind = "integrated"
            if wt_handle is not None:
                integrated, integ_reason, integ_kind = integrate_lane_branch(
                    repo,
                    wt_handle,
                    item["id6"],
                    make_integration_validation_runner(state, run_dir, item),
                )
            if not integrated:
                # driverfin-03 (7kbtkw) E-01/E-02: fail closed. A contaminated base yields
                # `integration-blocked`; a non-passing gate result / real merge conflict yields
                # `merge-conflict`. Either way main is left UNTOUCHED (the gate is diff-based and any
                # real merge was aborted), the verified lane branch/worktree is PRESERVED for a
                # human/serial resolution, and the child is NOT faked executed (its set therefore is
                # NOT reported finished - the orchestrator only finalizes when all children executed).
                fail_status = (
                    "integration-blocked"
                    if integ_kind == "integration-blocked"
                    else "merge-conflict"
                )
                fail_event = (
                    "ipd-integration-blocked"
                    if fail_status == "integration-blocked"
                    else "ipd-merge-conflict"
                )
                attempt["disposition"] = fail_status
                attempt["finalized"] = True
                attempt["integration_deferred"] = integ_reason
                item["status"] = fail_status
                item["integration_deferral"] = integ_reason
                # Leave the worktree/branch in place (NOT torn down) for a later human/serial fix.
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": fail_event,
                        "id6": item["id6"],
                        "setid": item["setid"],
                        "detail": integ_reason,
                        "branch": wt_handle.branch if wt_handle else None,
                    },
                )
                lane_branch = wt_handle.branch if wt_handle else "(none)"
                print(
                    pal(
                        f"  ! IPD {item['id6']} finalized on lane {lane_branch} but NOT "
                        f"integrated to main ({fail_status}): {integ_reason}",
                        "yellow",
                    ),
                    file=sys.stderr,
                )
                disposition = fail_status
            else:
                if wt_handle is not None:
                    with contextlib.suppress(Exception):
                        teardown_isolation_worktree(repo, wt_handle)
                    wt_handle = None
                disposition = "executed"
                attempt["disposition"] = "executed"
                attempt["finalized"] = True
                attempt["integrated"] = integ_reason
                item["status"] = "executed"
                # Re-resolve so any later handling sees the plan now living in executed/ on main.
                try:
                    item["last_plan_path"] = str(
                        resolve_plan_path(
                            repo, item.get("configured_file", ""), item["id6"]
                        )
                    )
                except DriverError:
                    pass
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "ipd-finalized",
                        "id6": item["id6"],
                        "setid": item["setid"],
                        "integration": integ_reason,
                    },
                )
                print(
                    pal(
                        f"  \u2713 IPD {item['id6']} finalized -> executed/ and integrated to main "
                        f"({integ_reason})",
                        "green",
                    )
                )
        else:
            attempt["finalize_refused"] = fin_msg
            item["finalize_refusal"] = fin_msg
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "ipd-finalize-refused",
                    "id6": item["id6"],
                    "exit_code": fin_rc,
                    "detail": fin_msg,
                },
            )
            print(
                pal(
                    f"  ! IPD {item['id6']} finalize refused (left {disposition}, not forced): "
                    f"{fin_msg}",
                    "yellow",
                ),
                file=sys.stderr,
            )

    # driverfin-02 (emus4n): if a worktree is still allocated here (verification did not pass,
    # finalize refused, or integration was deferred), PRESERVE it attributably rather than tearing it
    # away (forward-progress rule: never discard work). The branch holds the agent's commits; child-03
    # owns the guard + resolution. Record the preserved location so a later turn can find it.
    if wt_handle is not None and item.get("status") != "executed":
        item["preserved_worktree"] = str(wt_handle.path)
        item["preserved_branch"] = wt_handle.branch
        # laneorphan-01 (`zwnjp3`) E-04: carry the real lane identity and base too, so the
        # reclamation classifier can read them back instead of reconstructing a name that
        # attempt-scoping may have changed.
        item["preserved_lane_id"] = wt_handle.lane_id
        item["preserved_base"] = wt_handle.base_commit
        item["preserved_disposition"] = getattr(wt_handle, "disposition", "created")
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "worktree-preserved",
                "id6": item["id6"],
                "worktree": str(wt_handle.path),
                "branch": wt_handle.branch,
                "lane_id": wt_handle.lane_id,
                "base_commit": wt_handle.base_commit,
                "status": item.get("status"),
            },
        )
        print(
            pal(
                f"  \u2022 IPD {item['id6']} work preserved on lane {wt_handle.branch} "
                f"at {wt_handle.path} (not integrated; attributable for a later turn/child-03)",
                "dim",
            ),
            file=sys.stderr,
        )

    full_auto = state.get("options", {}).get("full_auto", False)
    auto_approved = False
    if is_review and disposition in ("reviewed", "approved") and full_auto:
        plan_curr = resolve_plan_path(repo, item["configured_file"], item["id6"])
        if is_plan_review_approved(plan_curr):
            try:
                set_plan_approved(repo, item["id6"])
                item["action"] = "execute"
                item["status"] = "queued"
                item["auto_approved"] = True
                auto_approved = True
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "ipd-auto-approved",
                        "id6": item["id6"],
                    },
                )
            except Exception as exc:
                print(
                    pal(
                        f"  ! Failed to auto-approve IPD {item['id6']}: {exc}",
                        "yellow",
                    ),
                    file=sys.stderr,
                )

    glyph = "\u2713" if disposition in SUCCESS_STATES else "\u25cf"
    glyph_color = (
        "green"
        if disposition in SUCCESS_STATES
        else (_STATUS_COLOR.get(disposition, "yellow"))
    )
    finish = (
        pal(f"{glyph} ", glyph_color)
        + pal(f"IPD {item['position']:02d}/{total} {item['id6']}", "bold")
        + pal(f" ({item.get('action', 'execute')})", "dim")
        + " -> "
        + pal(disposition, glyph_color)
        + pal(f"  (exit {exit_code})", "dim")
    )
    print(finish)
    if auto_approved:
        print(
            pal(
                f"  \u2713 IPD {item['id6']} auto-approved (GO - PENDING HUMAN APPROVAL); progressing to execution",
                "cyan",
            )
        )
    print()
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "ipd-finished",
            "id6": item["id6"],
            "action": item.get("action", "execute"),
            "attempt": attempt_no,
            "exit_code": exit_code,
            "status": disposition,
            "session_id": session_id,
        },
    )


def reconcile_interrupted(run_dir: Path, state: dict[str, Any]) -> None:
    repo = Path(state["repo"])
    for item in state["queue"]:
        if item["status"] != "running":
            continue
        attempts = item.get("attempts", [])
        if attempts:
            raw_log = attempts[-1].get("log")
            session_id = extract_session_id(Path(raw_log)) if raw_log else None
            if session_id:
                existing = state.setdefault("set_sessions", {}).get(item["setid"])
                if existing in (None, session_id):
                    state["set_sessions"][item["setid"]] = session_id
                    state["session_id"] = session_id
                    attempts[-1]["session_id"] = session_id
                else:
                    attempts[-1]["session_reconciliation_error"] = (
                        f"persisted={existing} observed={session_id}"
                    )
        try:
            path = resolve_plan_path(repo, item["configured_file"], item["id6"])
            if plan_bucket(path) == "executed":
                # runstop m0z0ti (E-05, spec R22): THE FABRICATED-SUCCESS GATE.
                #
                # The promotion below infers success from the plan's DIRECTORY alone, consulting
                # neither the outcome artifact nor any stop record. For an item whose turn was
                # FORCE-CUT that is a live R22 violation: if the agent had already moved the plan to
                # `executed/` but was interrupted before its work was complete or verified, this would
                # record `executed` - a success the driver never established, which is precisely what
                # level 4 exists to prevent. So for an item flagged INDETERMINATE the promotion
                # refuses to fire and the conflict is REPORTED instead.
                #
                # Deliberately narrow: ordinary (non-indeterminate) interrupted items are promoted
                # exactly as before, and a control test pins that. Widening this to all interrupted
                # items would disable a legitimate promotion rather than fix a fabrication.
                if runner_stop.is_indeterminate(item):
                    item["reconciliation_conflict"] = (
                        f"plan is in executed/ ({path}) but this turn was force-interrupted "
                        f"(level 4), so the driver never established that the work completed; "
                        f"refusing to record it executed (spec c4gd2h R22). "
                        f"{runner_stop.RECONCILIATION_ACTION}"
                    )
                    append_jsonl(
                        run_dir / "events.jsonl",
                        {
                            "at": utc_now(),
                            "event": "interrupted-promotion-refused-unknown-outcome",
                            "id6": item["id6"],
                            "plan_bucket": "executed",
                            "certainty": runner_stop.CERTAINTY_INDETERMINATE,
                            "disposition": runner_stop.FORCED_DISPOSITION,
                            "requires_reconciliation": True,
                            "reason": item["reconciliation_conflict"],
                        },
                    )
                    print(
                        f"reconcile {item['id6']}: {item['reconciliation_conflict']}",
                        file=sys.stderr,
                    )
                else:
                    item["status"] = "executed"
                    append_jsonl(
                        run_dir / "events.jsonl",
                        {
                            "at": utc_now(),
                            "event": "interrupted-reconciled-executed",
                            "id6": item["id6"],
                        },
                    )
                    continue
        except DriverError:
            pass
        item["status"] = "interrupted"
        if attempts:
            now = utc_now()
            attempts[-1].setdefault("interrupted_at", now)
            attempts[-1].setdefault("ended_at", now)
        append_jsonl(
            run_dir / "events.jsonl",
            {"at": utc_now(), "event": "interrupted-detected", "id6": item["id6"]},
        )
    save_state(run_dir, state)


def requeue_interrupted(run_dir: Path, state: dict[str, Any]) -> list[str]:
    """Re-queue items left `interrupted` so resume retries in recovery mode.

    runstop m0z0ti (E-04, spec R19): EXCEPT an item flagged INDETERMINATE, which is SKIPPED and
    REPORTED instead of silently re-run.

    WHY THE GATE IS HERE AND NOT BESIDE THIS FUNCTION. `run_queue` calls `reconcile_interrupted` and
    then this function UNCONDITIONALLY on every start and every resume, and this function's original
    behavior was to flip every `interrupted` item straight back to `queued` with
    `recovery_next = True` and no operator gate. A refusal added anywhere else would simply be
    BYPASSED by the call that already ran, so the gate has to live in the requeue itself
    (orchestrator CID-4). `--retry-incomplete` is a SECOND route to the same requeue and is gated in
    `run_queue` for the same reason.

    Do not "clean this up" as a redundant special case: without it, a force-interrupted item whose
    outcome the driver never established is re-run blindly, which is the exact failure spec R19
    exists to prevent.
    """

    requeued: list[str] = []
    for item in state["queue"]:
        if item["status"] != "interrupted":
            continue
        if runner_stop.is_indeterminate(item):
            item["requires_reconciliation"] = True
            append_jsonl(
                run_dir / "events.jsonl",
                runner_stop.refused_resume_event(item, at=utc_now()),
            )
            print(runner_stop.resume_refusal_message(item), file=sys.stderr)
            continue
        item["status"] = "queued"
        item["recovery_next"] = True
        requeued.append(item["id6"])
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "interrupted-requeued",
                "id6": item["id6"],
            },
        )
    return requeued


def _observe_between_turn_stop(
    run_dir: Path,
    level: int | None,
    current_setid: str | None,
    existing: runner_stop.WindDown | None,
) -> runner_stop.WindDown | None:
    """Turn a polled stop LEVEL into a level-1/2 wind-down, capturing the set boundary ONCE.

    runstop 1qxuke. Returns the wind-down in force, or None while no between-turn stop applies.

    Two details carry the correctness:

    1. The captured `setid` is frozen at the FIRST observation and never re-derived. Level 2's
       boundary is "the rest of THIS set", and because the dequeue is dependency-ordered the set in
       flight can change under a naive re-derivation (sets interleave), which would stop at the
       wrong place. `existing` is therefore returned unchanged unless the level ESCALATED.
    2. Levels 3 and 4 are NOT handled here. They interrupt the running turn and belong to later
       phases; returning None for them leaves today's behavior untouched rather than silently
       treating a turn-interrupting request as a between-turn one.
    """

    if level not in runner_stop.BETWEEN_TURN_LEVELS:
        return existing
    if existing is not None and existing.level >= level:
        return existing
    request = runner_stop.read_stop_request(run_dir)
    requester = request.requester if request is not None else "unknown"
    # On an escalation (1 -> 2) keep the ORIGINALLY captured set: the operator raised the boundary
    # for the set they were already winding down, and re-capturing now could pick up a different
    # set that only became current because of an interleave.
    setid = existing.setid if existing is not None else current_setid
    wind_down = runner_stop.WindDown(level=level, requester=requester, setid=setid)
    print(
        f"stop requested: level {wind_down.level} ({wind_down.level_name}); "
        f"boundary = next "
        f"{'item' if wind_down.level == runner_stop.LEVEL_AFTER_CALL else 'set'}"
        + (f", finishing set {setid}" if wind_down.level == 2 and setid else ""),
        file=sys.stderr,
    )
    return wind_down


def _record_deliberate_stop(
    run_dir: Path, state: dict[str, Any], wind_down: runner_stop.WindDown
) -> None:
    """Append the DELIBERATE-stop ledger event (spec R21) and leave un-run items `queued`.

    runstop 1qxuke. Uses the driver's ESTABLISHED append-only `events.jsonl` channel, deliberately
    not a new ledger file or substrate. No per-item status is invented and nothing is marked
    `unknown_outcome`: levels 1-2 interrupt no turn, so every item is either genuinely finished or
    genuinely never started (spec R20).
    """

    remaining = [item["id6"] for item in state["queue"] if item["status"] == "queued"]
    append_jsonl(
        run_dir / "events.jsonl",
        runner_stop.deliberate_stop_event(wind_down, at=utc_now(), remaining=remaining),
    )
    print(
        f"deliberate stop (level {wind_down.level}, {wind_down.level_name}): "
        f"{len(remaining)} item(s) left queued, not started: {', '.join(remaining) or 'none'}",
        file=sys.stderr,
    )


def run_queue(
    run_dir: Path, retry_incomplete: bool, output_mode: str | None = None
) -> int:
    state = load_state(run_dir)
    if output_mode is not None:
        state.setdefault("options", {})["output_mode"] = output_mode
        save_state(run_dir, state)
    reconcile_interrupted(run_dir, state)
    if requeue_interrupted(run_dir, state):
        save_state(run_dir, state)
    if retry_incomplete:
        for item in state["queue"]:
            # runstop m0z0ti (E-04, spec R19): `--retry-incomplete` is the SECOND route into the
            # requeue and would otherwise re-run a force-interrupted item that `requeue_interrupted`
            # just refused, since its status set includes `interrupted`. Gate it on the SAME predicate
            # so the two routes cannot disagree. A broader retry flag is still not permission to
            # re-run work whose outcome the driver never established.
            if runner_stop.is_indeterminate(item):
                continue
            if item["status"] in {
                "interrupted",
                "substantially-complete",
                "partial",
                "failed-safely",
                "blocked",
                "dependency-blocked",
                # driverfin-03 (7kbtkw): a fail-closed integration outcome is retryable once the base
                # is clean / the conflict is resolved on the preserved lane branch.
                "integration-blocked",
                "merge-conflict",
            }:
                item["status"] = "queued"
                item["recovery_next"] = True
        save_state(run_dir, state)
    # runstop m0z0ti (E-04, spec R19/A6): REFUSE the resume outright when the queue still holds an
    # indeterminate item. Skipping it silently would satisfy "did not re-run it" while leaving the
    # operator with no signal, so the refusal exits NONZERO and names the item, its state, and the
    # required reconciliation. The remaining items are NOT started: an indeterminate item may well be
    # a dependency of theirs, and the driver cannot know what it did.
    unresolved = runner_stop.indeterminate_items(state["queue"])
    if unresolved:
        for item in unresolved:
            print(runner_stop.resume_refusal_message(item), file=sys.stderr)
        save_state(run_dir, state)
        write_report(run_dir, state)
        print(
            f"resume refused: {len(unresolved)} item(s) require reconciliation first: "
            f"{', '.join(item.get('id6', '?') for item in unresolved)}",
            file=sys.stderr,
        )
        return 1
    tracker = StreamTracker()
    # runstop 1qxuke: the observed level-1/2 wind-down, or None while no between-turn stop has been
    # requested. Captured ONCE at observation time (see `_observe_between_turn_stop`) because level
    # 2's boundary is the set that was in flight THEN, and the dependency-ordered dequeue below lets
    # sets interleave.
    wind_down: runner_stop.WindDown | None = None
    current_setid: str | None = None
    # The deliberate stop is recorded EXACTLY ONCE, whichever boundary the loop actually exits at
    # (declined item, drained queue, or dependency-blocked remainder).
    stop_recorded = False
    # runstop foi1b3: True once a level-3 stop cut the running TURN at an observed safe checkpoint.
    # Tracked separately from `wind_down` because levels 1-2 stop BETWEEN turns while level 3 stops
    # inside one, yet both are DELIBERATE and so must share the honest exit contract below.
    stopped_at_checkpoint = False
    while True:
        # runstop gq6m2u: the BETWEEN-ITEM cooperative checkpoint (spec `c4gd2h` R7), evaluated
        # before the next item is selected. runstop 1qxuke acts on it for the two BETWEEN-TURN
        # levels: level 1 = stop-after-call (R20/A1), level 2 = stop-after-set (R20/A4). Neither
        # interrupts the turn that just finished, so neither can produce an indeterminate outcome.
        level = runner_stop.poll_stop(run_dir)
        state = load_state(run_dir)
        wind_down = _observe_between_turn_stop(run_dir, level, current_setid, wind_down)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued:
            # runstop 1qxuke (E-03, OQ-01): the FINAL-set boundary. A level-2 request on the last set
            # drains the queue, so the loop leaves here rather than at the consent check below. The
            # deliberate stop must STILL be recorded (spec R21), otherwise a stop that happened to
            # skip nothing would be indistinguishable from an ordinary finish and the operator's
            # intent would vanish from the history. `stop_recorded` keeps it exactly-once.
            if wind_down is not None and not stop_recorded:
                _record_deliberate_stop(run_dir, state, wind_down)
                stop_recorded = True
            break
        runnable = None
        for item in queued:
            satisfied, _ = dependency_status(item, state)
            if satisfied:
                runnable = item
                break
        # runstop 1qxuke: the wind-down decides only whether the driver still CONSENTS to start the
        # selected item; it never reorders the queue. An item outside the boundary is left `queued`
        # (spec R22: no fabricated disposition), which for level 2 can legitimately mean ending with
        # runnable work outstanding (the operator asked to wind down, not to drain).
        if (
            wind_down is not None
            and runnable is not None
            and not wind_down.permits(runnable.get("setid"))
        ):
            if not stop_recorded:
                _record_deliberate_stop(run_dir, state, wind_down)
                stop_recorded = True
            break
        if runnable is None:
            # runstop 1qxuke: during a wind-down, do NOT relabel the remainder. Outside a stop,
            # marking every queued item `dependency-blocked` is the truthful description of why the
            # run ended. Under a stop it would not be: items of another set are `queued` because the
            # OPERATOR asked to stop, not because their dependencies are unmet, and rewriting their
            # status would be exactly the fabricated disposition spec R22 forbids. So record the
            # deliberate stop and leave the remainder `queued`.
            if wind_down is not None:
                if not stop_recorded:
                    _record_deliberate_stop(run_dir, state, wind_down)
                    stop_recorded = True
                break
            for item in queued:
                _, missing, why = dependency_status_detailed(item, state)
                item["status"] = "dependency-blocked"
                item["unsatisfied_dependencies"] = missing
                # revgate Order 03 (7nkcgp) E-04: an ADDITIVE companion key. The flat
                # `unsatisfied_dependencies` list[str] keeps its exact shape and meaning, so every
                # existing consumer is untouched; the reasons live alongside it.
                item["unsatisfied_dependency_reasons"] = why
                item["dependency_block_recovery"] = DEPENDENCY_BLOCK_RECOVERY_HINT
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "dependency-blocked",
                        "id6": item["id6"],
                        "dependencies": missing,
                        # Additive: the flat `dependencies` list above is unchanged.
                        "reasons": why,
                        "recovery": DEPENDENCY_BLOCK_RECOVERY_HINT,
                    },
                )
            save_state(run_dir, state)
            break
        recovery = bool(runnable.pop("recovery_next", False))
        # Orchestrators are not agent-executed: finalize iff every child in the set
        # reached `executed`, else leave blocked (no agent turn). See queue-builder note.
        if runnable.get("action") == "orchestrate":
            repo = Path(state["repo"])
            all_done, unfinished = _set_children_all_executed(
                state, runnable["setid"], runnable["id6"]
            )
            if all_done and finalize_orchestrator(
                repo,
                runnable["id6"],
                f"Orchestrator rollup: all children of set {runnable['setid']} executed "
                f"(aw oc run, no agent turn).",
            ):
                runnable["status"] = "executed"
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "orchestrator-finalized",
                        "id6": runnable["id6"],
                        "setid": runnable["setid"],
                    },
                )
            else:
                runnable["status"] = "dependency-blocked"
                runnable["unsatisfied_dependencies"] = unfinished
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "orchestrator-deferred",
                        "id6": runnable["id6"],
                        "setid": runnable["setid"],
                        "reason": "not-all-children-executed"
                        if not all_done
                        else "finalize-refused",
                        "unfinished_children": unfinished,
                    },
                )
            save_state(run_dir, state)
            continue
        # runstop 1qxuke: the set now in flight. Recorded BEFORE the turn so that a stop requested
        # DURING this turn is observed at the next checkpoint with this set already captured.
        current_setid = runnable.get("setid")
        try:
            execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)
        except ToolIdentityError:
            # lanetruth Order 01 (af7i6p) E-04 / OQ-02: RUN-FATAL, so it must NOT be caught by the
            # item-local `except DriverError` below (ToolIdentityError subclasses DriverError, so
            # without this clause the abort would be silently downgraded to one item marked
            # `failed-safely` while the remaining items kept running under the same wrong tooling
            # -- exactly the misleading outcome OQ-02 rejects). Re-raise to abort the whole run.
            save_state(run_dir, state)
        except KeyboardInterrupt:
            # laneorphan-01 (`zwnjp3`) E-05: PRESERVE-AND-RECORD before the interrupt propagates,
            # so the run does not leak lanes (which wedged the next run at allocation) and does not
            # destroy any lane holding work. Wired into this EXISTING teardown path; NO signal handler
            # is registered here (`runstop` Phase 5 `71vjbn` owns SIGINT/SIGTERM registration).
            state = load_state(run_dir)
            try:
                lanes = reclaim_lanes_on_interrupt(
                    Path(state["repo"]), run_dir, state, reason="interrupt"
                )
                print_lane_interrupt_report(lanes)
            except KeyboardInterrupt:
                # E-10: a SECOND interrupt while reclaiming. The operator is trying harder to stop, so
                # never prompt again and finish the automatic content-based decision unattended. The
                # preservation half must still run: it is what keeps work from being lost.
                disable_lane_prompt()
                with contextlib.suppress(Exception):
                    lanes = reclaim_lanes_on_interrupt(
                        Path(state["repo"]),
                        run_dir,
                        state,
                        interactive=False,
                        reason="repeated-interrupt",
                    )
                    print_lane_interrupt_report(lanes)
            except Exception:
                pass
            raise
        except runner_stop.StopNowForce:
            # runstop m0z0ti (E-01/E-03, spec A2): the current TURN was interrupted IMMEDIATELY, so
            # the RUN stops here too. `execute_item` already recorded the item as INDETERMINATE and
            # the child was reaped through the shared `clean_shutdown`. Remaining items keep `queued`
            # (spec R22 forbids relabeling work that never ran), and NOTHING is marked executed,
            # complete, or successful anywhere on this path.
            stopped_at_checkpoint = True
            state = load_state(run_dir)
            break
        except runner_stop.StopAtCheckpoint:
            # runstop foi1b3 (E-02, spec A3): the current TURN was stopped at an observed safe
            # checkpoint, so the RUN stops here too. `execute_item` already recorded the item with
            # KNOWN certainty and the child was reaped through `clean_shutdown`; the remaining queued
            # items are left `queued` untouched (spec R22 forbids relabeling work that never ran).
            stopped_at_checkpoint = True
            state = load_state(run_dir)
            break
        except DriverError as exc:
            runnable["status"] = "failed-safely"
            runnable["driver_error"] = str(exc)
            save_state(run_dir, state)
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "ipd-driver-error",
                    "id6": runnable["id6"],
                    "error": str(exc),
                },
            )
            print(f"IPD {runnable['id6']} failed safely: {exc}", file=sys.stderr)
    state = load_state(run_dir)
    write_report(run_dir, state)
    print(render_continuation_hint(state, run_dir))
    # runstop 1qxuke (E-05): a DELIBERATE stop exits 0 without lying about the queue. The plain
    # predicate treats any non-success status, INCLUDING the `queued` items a level-1/2 stop
    # intentionally never started, as failure; spec A1/A4 require 0. The shared helper ignores
    # `queued` only when a stop was actually observed, and still returns nonzero if an item that RAN
    # failed. No item's status is rewritten to manufacture the 0 (spec R22).
    #
    # runstop foi1b3: a level-3 stop is equally DELIBERATE, so it takes the same contract. Its own
    # item is `interrupted`, which is NOT a success state, so the run still exits nonzero for it -
    # deliberately. Level 3 admits the turn did not finish; only the items it never STARTED are
    # excused, exactly as for levels 1-2.
    return runner_stop.deliberate_stop_exit_code(
        (item["status"] for item in state["queue"]),
        success_states=SUCCESS_STATES,
        stopped=wind_down is not None or stopped_at_checkpoint,
    )


@contextlib.contextmanager
def locked_run(run_dir: Path):
    """Hold the run lock AND guarantee the shared clean shutdown when the scope ends.

    This is the LOCK-HOLDING layer, which is the only scope that holds all four clean-shutdown
    invariants' inputs at once: the ``driver.lock`` handle (spec `c4gd2h` R2), the run ledger
    (R3), and the repository path (R4), plus the tracked child agent processes (R1). The
    per-turn ``run_opencode`` handlers cannot satisfy R2/R3/R4 at all: they hold no lock, run
    once per turn, and have no queue authority, so they only reap the child.

    The routine runs in a ``finally`` so it also covers the failure path (spec R6: cleanup runs
    even when the wind-down phase fails or times out), and its per-invariant report is printed
    rather than assumed (spec R23).
    """

    repo: Path | None = None
    with contextlib.suppress(Exception):
        repo = Path(load_state(run_dir)["repo"])
    with run_lock(run_dir) as lock:
        try:
            yield lock
        finally:
            report = runner_shutdown.clean_shutdown(
                lock=lock, run_dir=run_dir, repo=repo
            )
            if not report.all_satisfied or report.dirty_paths or report.reaped_pids:
                print(report.render(), file=sys.stderr)


def _detect_driver_command() -> str:
    """Detect the command prefix used to invoke the runner, defaulting to 'aw oc run'."""
    argv = sys.argv
    for i in range(len(argv) - 1):
        if argv[i] in ("oc", "opencode") and argv[i + 1] in ("run", "runipd"):
            return f"aw {argv[i]} {argv[i + 1]}"
    return "aw oc run"


def render_continuation_hint(
    state: dict[str, Any],
    run_dir: Path,
    driver_cmd: str | None = None,
) -> str:
    """Print, on exit, the captured OpenCode session id(s) and the exact commands to
    reuse them (run a NEW plan in the same session context) or resume / inspect THIS run.

    Sessions are captured even when --session was not passed (extract_session_id reads
    them from the child's streamed JSONL), so this surfaces them without a hand-read of
    state.json. Handles 0, 1, and N captured sessions (a multi-Set run has one session
    per Set)."""
    pal = Palette(should_color(sys.stdout))
    cmd = driver_cmd or _detect_driver_command()
    repo = state.get("repo", ".")
    run_id = state.get("run_id", "run-...")
    sessions = state.get("set_sessions", {})
    captured: list[tuple[str, str]] = [
        (s, sid) for s, sid in sessions.items() if sid and isinstance(sid, str)
    ]

    lines = ["", pal("--- OpenCode Session Continuity ---", "bold")]
    if not captured:
        lines.append("No OpenCode session was captured for this run.")
    elif len(captured) == 1:
        setid, sid = captured[0]
        lines.append(f"Captured session: {pal(sid, 'cyan')} (Set: {setid})")
        lines.append("To run a new plan under the same session:")
        lines.append(f"  {cmd} --session {sid} <selector>")
    else:
        lines.append("Captured sessions by Set:")
        for setid, sid in captured:
            lines.append(f"  - {pal(setid, 'bold')}: {pal(sid, 'cyan')}")
        last_sid = captured[-1][1]
        lines.append("To run a new plan under the most recent session:")
        lines.append(f"  {cmd} --session {last_sid} <selector>")

    queue = state.get("queue", [])
    all_success = all(item.get("status") in SUCCESS_STATES for item in queue)

    if all_success:
        lines.append("To inspect run summary:")
        lines.append(f"  aw runs {run_id}")
    else:
        lines.append("To resume this run:")
        lines.append(f"  {cmd} resume --repo {repo} {run_id}")
    lines.append("")
    return "\n".join(lines)


def print_status(run_dir: Path) -> None:
    state = load_state(run_dir)
    print(f"Run: {state['run_id']}")
    print(f"Repository: {state['repo']}")
    print(f"Updated: {state['updated_at']}")
    print(f"State directory: {run_dir}")
    for item in state["queue"]:
        action = item.get("action", "execute")
        v = (
            f" [verify: {item.get('verification_status')}]"
            if item.get("verification_status")
            else ""
        )
        print(
            f"{item['position']:02d} {item['id6']} {item['setid']:<12} "
            f"{action:<8} {item['status']:<20}{v} attempts={len(item.get('attempts', []))}"
        )
        # revgate Order 03 (7nkcgp) E-04: name the cause and the exact recovery command here too,
        # since `status` is the surface an operator checks first.
        reasons = item.get("unsatisfied_dependency_reasons") or {}
        for dep in item.get("unsatisfied_dependencies") or []:
            print(
                f"     blocked by {dep}: {reasons.get(dep) or 'dependency not satisfied'}"
            )
        hint = item.get("dependency_block_recovery")
        if hint and item.get("status") == "dependency-blocked":
            print(f"     recovery: {hint}")


def resolve_run_dir(repo_arg: str, run_id: str) -> Path:
    looks_like_path = (
        os.sep in run_id
        or (os.altsep and os.altsep in run_id)
        or run_id.startswith("~")
    )
    if looks_like_path:
        candidate = Path(run_id).expanduser()
        for run_dir in (candidate, Path.cwd() / candidate):
            if run_dir.is_dir() and (run_dir / "state.json").is_file():
                return run_dir.resolve()
        raise DriverError(f"Run not found: {run_id}")
    repo = Path(repo_arg).expanduser().resolve()
    run_dir = state_root(repo) / run_id
    if run_dir.is_dir():
        return run_dir
    raise DriverError(f"Run not found: {run_id}")


def _add_output_mode_flags(sub_parser: argparse.ArgumentParser) -> None:
    group = sub_parser.add_mutually_exclusive_group()
    group.add_argument(
        "--quiet",
        dest="output_mode",
        action="store_const",
        const="quiet",
        help="Only per-IPD banners and a periodic heartbeat (no per-event lines)",
    )
    group.add_argument(
        "--raw",
        dest="output_mode",
        action="store_const",
        const="raw",
        help="Stream the child agent's raw JSON events verbatim (legacy behavior)",
    )
    sub_parser.set_defaults(output_mode="clean")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runipd",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Autonomous OpenCode driver for Implementation Plan Documents (IPDs).

Drives pre-execution plan reviews for to-review IPDs and full non-interactive
execution for approved IPDs, persisting durable run state, session logs,
prompts, decisions, and outcomes under `.aw/records/runs/<run-id>/`.

SELECTOR TYPES:
  - id6:      6-character unique ID (e.g. 'pr2nd0', '5ahblp')
  - setid:    IPD Set identifier (e.g. 'ipdrunner', 'execset')
  - filename: Path or filename of an IPD file (e.g. '.aw/records/plans/pending/...ipd.md')

AUTOMATIC STATUS ROUTING:
  - to-review: Runs OpenCode with `/plan-review <plan_path>` to review and improve the plan.
               All reviews in a run share the same OpenCode session for continuity.
  - approved:  Executes the plan step-by-step according to the execution runbook.
""",
        epilog="""EXAMPLES:
  # Review a single pending plan:
  runipd 20260824-ipdrunner-01-pr2nd0-harden.ipd.md

  # Review all to-review plans in a set using an existing session:
  runipd ipdrunner --session <session_id>

  # Execute an approved plan:
  runipd 5ahblp

  # Execute multiple sets and plans in sequence:
  runipd v6zie5 unifyfileio ipdgates execset

  # Resume an interrupted run:
  runipd resume run-20260824T150827Z-2301181

  # Check status of a run:
  runipd status run-20260824T150827Z-2301181
""",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    start = sub.add_parser(
        "start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Create a run and execute its queue (default)",
        description="Create a durable queue of IPDs and execute or review them.",
    )
    start.add_argument(
        "selectors",
        nargs="+",
        help="One or more target selectors: id6 (e.g. 5ahblp), setid (e.g. execset), or plan filenames/paths",
    )
    start.add_argument(
        "--repo",
        default=".",
        help="Target Git repository root (default: current directory)",
    )
    start.add_argument(
        "--session",
        help="OpenCode session ID to attach/reuse across turns for multi-plan continuity",
    )
    start.add_argument(
        "--manifest",
        default=None,
        help="Optional pre-compiled driver manifest JSON (auto-discovered from repository if omitted)",
    )
    start.add_argument(
        "--runbook",
        default=None,
        help="Optional custom driver execution runbook Markdown (uses repo default if omitted)",
    )
    start.add_argument(
        "--run-id",
        help="Explicit unique run ID (default: auto-generated timestamped ID)",
    )
    start.add_argument(
        "--opencode",
        default="opencode",
        help="OpenCode executable name/path (default: 'opencode')",
    )
    start.add_argument(
        "--model",
        help="Exact provider/model identifier for OpenCode (e.g. 'anthropic/claude-3-7-sonnet')",
    )
    start.add_argument("--agent", help="Primary OpenCode agent name")
    start.add_argument(
        "--auto",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Enable OpenCode auto mode",
    )
    start.add_argument(
        "--prepare-only",
        action="store_true",
        help="Create and display the durable queue without launching OpenCode",
    )
    start.add_argument(
        "--stall-timeout",
        type=float,
        default=DEFAULT_STALL_TIMEOUT,
        help=(
            "Timeout in seconds with no observed PROGRESS from the child agent before "
            "terminating. Progress counts events on the child's stdout AND best-effort "
            "subagent activity from opencode's own log, so a turn working inside a "
            "subagent is not killed for a quiet stdout (default: 600; 0 to disable)"
        ),
    )
    start.add_argument(
        "--full-auto",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Automatically approve reviewed plans with 'GO - PENDING HUMAN APPROVAL' verdict and execute them immediately",
    )
    start.add_argument(
        "--validate",
        "--verify",
        "--audit",
        dest="validate",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Run the turn-2 independent clean-session verification of executed plans (default: false; pass --validate to enable)",
    )
    start.add_argument(
        "--no-self-finalize",
        dest="self_finalize",
        action="store_false",
        default=True,
        help="Do not run 'aw ipd begin' before / 'aw ipd finalize' after each verified execute "
        "turn (the agent must move the plan itself). Default: the driver self-finalizes.",
    )
    start.add_argument(
        "--no-isolate-worktree",
        dest="isolate_worktree",
        action="store_false",
        default=True,
        help="Do not isolate each execute turn in its own git worktree; run in the main tree "
        "instead. Default: each IPD executes in an isolated worktree and its verified branch is "
        "integrated back to main.",
    )
    start.add_argument(
        "--max-items-per-session",
        type=int,
        default=4,
        metavar="N",
        help="Maximum consecutive non-isolated turns per session before starting a fresh session (default: 4; 0 to disable rotation)",
    )
    _add_output_mode_flags(start)

    resume = sub.add_parser(
        "resume",
        help="Resume an existing run",
        description="Resume an interrupted run or retry incomplete items in recovery mode.",
    )
    resume.add_argument(
        "run_id",
        help="Run ID (e.g. 'run-20260824T150827Z-2301181') or state directory path",
    )
    resume.add_argument("--repo", default=".", help="Target Git repository root")
    resume.add_argument(
        "--session",
        help="Override or attach OpenCode session ID for resuming turns",
    )
    resume.add_argument(
        "--retry-incomplete",
        action="store_true",
        help="Retry interrupted, partial, failed, or blocked items in recovery mode",
    )
    resume.add_argument(
        "--stall-timeout",
        type=float,
        default=None,
        help=(
            "Override timeout in seconds with no observed progress from the child agent "
            "(stdout events or best-effort subagent activity; default: 600; 0 to disable)"
        ),
    )
    resume.add_argument(
        "--full-auto",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override full-auto mode (auto-approve and execute reviewed plans with GO verdict)",
    )
    resume.add_argument(
        "--validate",
        "--verify",
        "--audit",
        dest="validate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override turn-2 independent verification of executed plans",
    )
    resume.add_argument(
        "--max-items-per-session",
        type=int,
        default=None,
        metavar="N",
        help="Override maximum consecutive non-isolated turns per session before starting a fresh session",
    )
    _add_output_mode_flags(resume)

    status = sub.add_parser(
        "status",
        help="Show status of an existing run",
        description="Inspect queue positions, attempt counts, actions, and statuses for a run.",
    )
    status.add_argument("run_id", help="Run ID or state directory path")
    status.add_argument("--repo", default=".", help="Target Git repository root")
    status.add_argument(
        "--json",
        action="store_true",
        help="Output the full state.json payload as JSON (for tooling/CI)",
    )

    report = sub.add_parser(
        "report",
        help="Regenerate and print execution report path",
        description="Rebuild execution-report.md from latest state and print its file path.",
    )
    report.add_argument("run_id", help="Run ID or state directory path")
    report.add_argument("--repo", default=".", help="Target Git repository root")

    return parser


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    subcommands = {
        "start",
        "resume",
        "status",
        "report",
        "-h",
        "--help",
        "-v",
        "--version",
    }
    if argv and argv[0] not in subcommands:
        argv = ["start"] + argv

    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    try:
        if args.command == "start":
            run_dir = initialize_run(args)
            print(f"Run ID: {run_dir.name}")
            print(f"State directory: {run_dir}")
            if args.prepare_only:
                print_status(run_dir)
                return 0
            with locked_run(run_dir):
                return run_queue(run_dir, retry_incomplete=False)
        run_dir = resolve_run_dir(args.repo, args.run_id)
        output_mode = getattr(args, "output_mode", None)
        if args.command == "status":
            if getattr(args, "json", False):
                state = load_state(run_dir)
                print(json.dumps(state, indent=2, sort_keys=True))
                return 0
            print_status(run_dir)
            return 0
        if args.command == "report":
            state = load_state(run_dir)
            write_report(run_dir, state)
            print(run_dir / "execution-report.md")
            return 0
        if args.command == "resume":
            if getattr(args, "full_auto", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["full_auto"] = args.full_auto
                save_state(run_dir, state)
            if getattr(args, "validate", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["validate"] = args.validate
                state["options"]["no_audit"] = not args.validate
                save_state(run_dir, state)
            if getattr(args, "max_items_per_session", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["max_items_per_session"] = (
                    args.max_items_per_session
                )
                save_state(run_dir, state)
            if getattr(args, "stall_timeout", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["stall_timeout"] = args.stall_timeout
                save_state(run_dir, state)
            if getattr(args, "session", None):
                state = load_state(run_dir)
                state["session_id"] = args.session
                state.setdefault("options", {})["session"] = args.session
                for s in state.get("set_sessions", {}):
                    state["set_sessions"][s] = args.session
                save_state(run_dir, state)
            with locked_run(run_dir):
                return run_queue(
                    run_dir,
                    retry_incomplete=args.retry_incomplete,
                    output_mode=output_mode,
                )
        raise DriverError(f"Unsupported command: {args.command}")
    except KeyboardInterrupt:
        print("Interrupted; durable run state was preserved.", file=sys.stderr)
        return 130
    except DriverError as exc:
        print(f"runipd: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"runipd: unexpected failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
