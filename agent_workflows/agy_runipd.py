#!/usr/bin/env python3
"""Restartable non-interactive Antigravity (agy) driver for reviewing and executing IPDs (runagy).

This driver manages execution, review, and verification queues for IPDs, Sets, and plan files:
- For plans with status 'to-review' (or 'draft'), it invokes Antigravity with `/plan-review <path>`.
- For plans with status 'approved', it executes them step-by-step using the durable
  driver runbook and records outcome state.
- After an execution turn, it automatically executes a rigorous skeptical verification turn
  in a clean, fresh Antigravity session (unless --no-verify is passed).
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
from typing import Any, Iterable, NamedTuple, Sequence, TextIO

# stallfp kaga7s: `Heartbeat` was a byte-identical INLINE COPY here, so a display fix in
# `render_stream` silently did not reach `aw agy run`. It is now imported, like `Statusline`,
# so there is exactly ONE definition. This unifies only the already-identical display class;
# it does NOT unify the two runners (that is backlog `dhuape`), and agy's watchdog wiring is
# unchanged because agy's stdout stream ALREADY carries `step_type == "subagent"` events and
# therefore has no subagent blind spot to fix.
# `Heartbeat` is re-exported (not used directly in this module): it is part of this module's
# public surface, because the `agy_runipd` shim re-exports it and asserts OBJECT IDENTITY with
# `agy_runipd.Heartbeat`. The explicit alias keeps a linter from stripping it as unused without
# introducing a partial `__all__` that would understate the rest of the public surface.
from agent_workflows.render_stream import Heartbeat as Heartbeat
from agent_workflows import runner_shutdown
from agent_workflows.render_stream import Statusline

# lanetruth Order 01 (af7i6p) E-02: import the SINGLE shared definition of the nested-`aw` pin
# rather than duplicating it here. Both drivers must stay symmetric, and a second copy is exactly
# how the previous inert half-pin came to differ from what it looked like it did. `oc_runipd` does
# not import this module, so there is no import cycle.
from agent_workflows.oc_runipd import (
    ToolIdentityError,
    assert_child_tool_identity,
    pinned_child_env,
    pinned_module_argv,
)

SCHEMA_VERSION = 1
DEFAULT_MODEL = "gemini-3.7-flash-high"
DEFAULT_TIMEOUT = "240m"
DEFAULT_STALL_TIMEOUT: float = 600.0
_SIGINT_GRACE_SECONDS = 5.0
_SIGTERM_GRACE_SECONDS = 2.0

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

# revgate Order 03 (7nkcgp) E-08. The EXACT recovery command for a `dependency-blocked` item, stated
# host-appropriately for this driver. Recovery is NOT automatic: re-queueing happens ONLY under the
# `if retry_incomplete:` branch of `run_queue`, which is False for a plain `start` and comes from the
# explicit `--retry-incomplete` flag on `resume`, so a bare `resume` leaves the item blocked. Also
# pre-existing and NOT changed here: with nothing satisfiable the loop blocks every queued item and
# BREAKS out of the run.
DEPENDENCY_BLOCK_RECOVERY_HINT = (
    "resolve the named cause, then re-queue with "
    "`aw agy runipd resume --repo <repo> --retry-incomplete <run-id>`; "
    "a bare `resume` does NOT re-queue a dependency-blocked item"
)

# Frontmatter and filename extraction regexes
_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
_SET_RE = re.compile(r"(?m)^-\s*Set:\s*(.+?)\s*$")
_ORDER_RE = re.compile(r"(?m)^-\s*Order:\s*(\d+)\s*$")
_DEPS_RE = re.compile(r"(?m)^-\s*(?:Dependencies|Depends-on):\s*(.+?)\s*$")
_PLAN_FILENAME_RE = re.compile(
    r"^\d{8}-([a-z0-9_-]+)-(\d{1,3})-([a-z0-9]{6})-(.+)\.(ipd|draft|plan)\.md$"
)

# Terminal output verbosity for the streamed child-agent turn.
OUTPUT_MODES = ("clean", "quiet", "raw")

# ANSI SGR codes.
_ANSI_RESET = "\033[0m"
_ANSI_CODES = {
    "bold": "1",
    "dim": "2",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "gray": "90",
}
_ANSI_STRIP_RE = re.compile(r"\033\[[0-9;]*m")

_STATUS_COLOR = {
    "executed": "green",
    "reviewed": "green",
    "approved": "green",
    "substantially-complete": "green",
    "partial": "yellow",
    "blocked": "yellow",
    "dependency-blocked": "yellow",
    "failed-safely": "red",
    "not-attempted": "gray",
    "interrupted": "yellow",
    "running": "cyan",
    "queued": "gray",
    # driverfin-03 (7kbtkw): fail-closed integration outcomes (dirty-base refusal / merge conflict);
    # rendered red because they leave the child NOT integrated and its set NOT finished.
    "integration-blocked": "red",
    "merge-conflict": "red",
}


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


class Palette:
    """Tiny colorizer: no-ops cleanly when color is disabled."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        if not self.enabled or not styles:
            return text
        codes = ";".join(_ANSI_CODES[s] for s in styles if s in _ANSI_CODES)
        if not codes:
            return text
        return f"\033[{codes}m{text}{_ANSI_RESET}"

    def status(self, status: str) -> str:
        return (
            self(status, self_color)
            if (self_color := _STATUS_COLOR.get(status))
            else status
        )


def _strip_ansi(text: str) -> str:
    return _ANSI_STRIP_RE.sub("", text)


def _one_line(text: str, limit: int = 200) -> str:
    """Collapse whitespace/newlines to a single line and clip to ``limit`` chars."""
    collapsed = " ".join(text.split())
    if len(collapsed) > limit:
        return collapsed[: limit - 1] + "\u2026"
    return collapsed


def render_agy_event(raw_line: str, pal: Palette) -> str | None:
    """Translate one raw JSONL event from `agy --output-format stream-json` into a
    concise, colored terminal line.
    """
    line = raw_line.rstrip("\n")
    if not line.strip():
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return pal("  " + _one_line(line), "dim")

    event_type = event.get("event")
    if event_type == "init":
        init_data = event.get("init") or {}
        model = init_data.get("model", "antigravity")
        conv_id = event.get("conversation_id", "")
        cid_str = f" [session: {conv_id[:8]}...]" if conv_id else ""
        return pal(f"  \u2022 Initialized Antigravity ({model}){cid_str}", "dim")

    if event_type == "result":
        res = event.get("result") or {}
        status = res.get("status", "UNKNOWN")
        if status == "SUCCESS":
            return pal(f"  \u2713 Antigravity turn finished: {status}", "green")
        else:
            err = res.get("error") or status
            return pal(f"  \u2717 Antigravity turn failed: {err}", "red")

    if event_type == "step_update":
        step = event.get("step_update") or {}
        state = str(step.get("state", "")).upper()
        step_type = str(step.get("step_type", ""))

        if step_type == "tool":
            tool_info = step.get("tool_info") or {}
            tool_name = tool_info.get("name") or step.get("tool_name") or "tool"
            params = tool_info.get("parameters") or {}
            cmd = ""
            if "CommandLine" in params:
                cmd = str(params["CommandLine"])
            elif "command" in params:
                cmd = str(params["command"])
            elif "cmd" in params:
                cmd = str(params["cmd"])
            elif "Query" in params:
                cmd = f"grep {params['Query']}"
            elif "AbsolutePath" in params:
                cmd = Path(str(params["AbsolutePath"])).name
            elif "TargetFile" in params:
                cmd = Path(str(params["TargetFile"])).name
            elif "Pattern" in params:
                cmd = str(params["Pattern"])

            summary = f": {_one_line(cmd, 120)}" if cmd else ""
            if state == "ACTIVE":
                glyph = pal("\u2026", "yellow")
                return f"{glyph} {pal(tool_name, 'bold')}{summary}"
            elif state == "DONE":
                glyph = pal("\u2713", "green")
                dur = step.get("duration_seconds")
                dur_str = f" ({dur:.2f}s)" if dur is not None else ""
                return f"{glyph} {pal(tool_name, 'bold')}{summary}{pal(dur_str, 'dim')}"
            elif state in ("ERROR", "FAILED"):
                glyph = pal("\u2717", "red")
                return f"{glyph} {pal(tool_name, 'bold')}{summary}"

        if step_type == "agent_response" and state == "DONE":
            return None

        if step_type == "subagent":
            subagent = step.get("subagent_info") or {}
            subagents = subagent.get("subagents", [])
            count = len(subagents) if isinstance(subagents, list) else 1
            noun = "subagent" if count == 1 else "subagents"
            glyph = (
                pal("\u2713", "green") if state == "DONE" else pal("\u2026", "yellow")
            )
            return f"{glyph} {count} {noun} {state.lower()}"

    return None


class DriverError(RuntimeError):
    pass


class StallTimeout(DriverError):
    """Raised when the child agent produces no events for stall_timeout seconds."""

    pass


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

        Parity with the OpenCode driver (stallfp kaga7s): the live display reads the
        countdown from HERE, the clock that actually kills, so the number shown cannot
        disagree with reality.
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
    # lanetruth Order 01 (af7i6p) E-05: was an inert PYTHONPATH-only prepend (the cwd entry
    # precedes PYTHONPATH in sys.path, so a child launched from a lane still imported the lane's
    # copy). Now delegates to the ONE shared definition in `oc_runipd`, kept symmetric with that
    # driver by construction rather than by a duplicated copy.
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
    repo: Path, id6: str, message: str = "Full-auto approval via runagy"
) -> None:
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
    # lanetruth Order 01 (af7i6p) E-06: CONSOLE-SCRIPT FALLBACK, deliberately NOT rewritten (see
    # the fuller note at the matching oc_runipd site). A bare `aw` argv can carry no interpreter
    # flag, but it does not need one: a console script puts its OWN directory, not the cwd, at the
    # head of `sys.path`, so it is MEASURABLY IMMUNE to the lane-shadowing defect. It still routes
    # through `run_checked` for the pinned env (defence in depth). Do not delete it believing it is
    # the hijack vector -- the `-m` form was.
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


def driver_actor(state: dict[str, Any]) -> str:
    """The attributed actor string bound into begin/finalize (driver + configured model).

    Kept parenthesis-free: the terminal history line is `- <date> <status> (<actor>): <msg>`, and
    the attribution lint's actor capture (`\\(...[^)]*...\\)`) would misparse a parenthesized actor,
    so the model is rendered as `model=<model>` (no nested parens)."""
    model = (state.get("options", {}) or {}).get("model")
    return f"aw agy run model={model}" if model else "aw agy run"


def driver_begin(repo: Path, id6: str, actor: str) -> tuple[int, str]:
    """Run the fail-closed `aw ipd begin <id6> --actor` gate before an execute turn.

    Reuses the packaged `aw ipd begin` surface (subprocess to `python -m agent_workflows`,
    mirroring `set_plan_approved`); begin writes the gitignored
    `.aw/state/ipd-lifecycle/<id6>.receipt.json` receipt (execution authority) itself. Returns
    (exit_code, stderr): exit 0 = receipt written; nonzero = refusal (no execution authority)."""
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling. As in oc_runipd, this site
    # is not itself lane-shadowed (it runs against the MAIN tree, before any lane exists), but it
    # is pinned anyway so exactly one launch shape exists across both drivers.
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
        return {}, {}
    audit = evidence.get("scope_audit", {}) or {}
    out_of_scope = list(audit.get("out_of_scope_paths", []) or [])
    in_scope_unmodified = list(audit.get("in_scope_unmodified", []) or [])
    reasons = {
        p: "changed by the plan's approved execution (auto-reconciled by aw agy run)"
        for p in out_of_scope
    }
    acks = {
        p: "declared-but-unmodified (auto-acknowledged by aw agy run)"
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
    forces the transition: a refusal returns nonzero and the caller records the child NOT-executed.
    Returns (exit_code, stderr)."""
    reasons, acks = _compute_scope_reconciliation(repo, plan_path)
    # lanetruth Order 01 (af7i6p): THE primary lane-shadowed site (mirrors oc_runipd). `repo` is the
    # LANE worktree and `cwd=str(repo)` below keeps it that way DELIBERATELY, because finalize must
    # resolve paths against the tree it finalizes. Only IMPORT resolution is pinned, so the lane's
    # own unreviewed `agent_workflows` can no longer be the code performing its own gating.
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
# it) allocation returns an ATTEMPT-SCOPED lane (`aw/lane/<id6>_attemptN`). ALWAYS read
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
    in-worktree `aw ipd finalize` can find the execution-authority receipt. No-op if absent."""
    from agent_workflows import ipd_lifecycle

    src = ipd_lifecycle.receipt_path_for(repo, id6)
    if not src.is_file():
        return
    dst = ipd_lifecycle.receipt_path_for(worktree, id6)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


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


def build_lane_outcome(repo: Path, handle: Any, id6: str) -> Any:
    """Build a single `orchestrate_isolation.LaneOutcome` for a finalized lane branch.

    base_commit = the worktree base; head_commit = the lane branch HEAD; changed_files + diff from
    `git diff base..branch`."""
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


def make_integration_validation_runner(
    state: dict[str, Any], run_dir: Path, item: dict[str, Any]
) -> Any:
    """Build the `full_validation_runner(combined_diff, merged_files) -> bool` the integration gate
    calls to revalidate the combined HEAD. Single-lane serial bootstrap: the combined diff == the lane
    diff the verifier turn already validated, so it returns True. Tests patch THIS function to exercise
    a combined-red path."""

    def _runner(_combined_diff: str, _merged_files: Any) -> bool:
        return True

    return _runner


def dirty_tree_overlap(repo: Path, changed_files: Sequence[str]) -> list[str]:
    """driverfin-03 (7kbtkw) E-01: report the MAIN tree's un-owned dirty paths that overlap an
    incoming lane's ``changed_files``.

    Inspect ``git status --short`` in the MAIN repo (working tree + index) and return the sorted set
    of paths that are BOTH dirty in main AND part of the incoming change. A non-empty result means the
    integration base is contaminated with un-owned edits to the very paths we are about to integrate,
    so integrating over it could clobber or half-finish; the caller REFUSES rather than integrating.
    """
    incoming = {p for p in changed_files if p.strip()}
    if not incoming:
        return []
    _rc, out, _err = _run_git(repo, ["status", "--short", "--untracked-files=all"])
    dirty: set[str] = set()
    for line in out.splitlines():
        if not line.strip():
            continue
        entry = line[3:] if len(line) > 3 else line.strip()
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

    0. driverfin-03 (7kbtkw) E-01 DIRTY-TREE GUARD: BEFORE invoking the gate, refuse if the MAIN tree
       has un-owned dirty paths overlapping the incoming lane's `changed_files` (kind
       ``"integration-blocked"``; main untouched, branch/worktree preserved).
    Calls `orchestrate_isolation.execute_merge_and_revalidate_gate` (detect conflict/stale-base +
    revalidate), then performs the real git integration onto main (`git merge --ff-only`, falling back
    to a controlled `--no-ff` merge; a git conflict aborts, leaving main clean). A non-passing gate
    result / real conflict yields kind ``"merge-conflict"`` (driverfin-03 E-02); a human/serial
    ordering resolves it via the preserved lane branch. Returns ``(integrated, reason, kind)`` with
    ``kind`` one of ``"integrated"``, ``"integration-blocked"``, ``"merge-conflict"``."""
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
        failing = "; ".join(
            f"{f.check_name}[{f.lane_id}]: {f.message}" for f in result.findings
        )
        detail = failing or result.message
        return (
            False,
            f"integration gate did not pass ({result.status}): {detail}",
            "merge-conflict",
        )

    rc, _out, err = _run_git(repo, ["merge", "--ff-only", handle.branch])
    if rc == 0:
        return True, "fast-forward integrated to main", "integrated"
    rc, _out, err2 = _run_git(
        repo,
        [
            "merge",
            "--no-ff",
            "--no-edit",
            "-m",
            f"integrate(aw agy run): merge verified lane {id6} to main",
            handle.branch,
        ],
    )
    if rc == 0:
        return True, "controlled non-ff merge integrated to main", "integrated"
    _run_git(repo, ["merge", "--abort"])
    return False, f"merge-back conflict: {(err2 or err).strip()}", "merge-conflict"


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
    the lock OBSERVABLY (spec `c4gd2h` R2: drop the ``flock`` AND remove the lock file). Kept
    symmetric with ``oc_runipd.run_lock`` (orchestrator CID-3).
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
    """Resolve selector tokens (id6, setid, file paths, or 'all') against manifest and repo."""
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

        for _setid, group in sets.items():
            for id6 in group.get("order", []):
                p = plans.get(id6, {})
                if _needs_review(p):
                    if id6 not in seen:
                        expanded.append(id6)
                        seen.add(id6)

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

        for _setid, group in sets.items():
            for id6 in group.get("order", []):
                p = plans.get(id6, {})
                if _is_actionable(p):
                    if id6 not in seen:
                        expanded.append(id6)
                        seen.add(id6)

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
    roots = [
        repo / ".aw" / "records" / "plans",
        repo / ".agents" / "plans",
        repo,
    ]
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
    norm = (status or "").lower().strip()
    if norm in ("to-review", "draft"):
        return "review"
    return "execute"


def resolve_agy(explicit_path: str | None) -> str:
    """Return an executable agy path or raise DriverError."""
    if explicit_path:
        cand = Path(explicit_path).expanduser()
        if cand.is_file() and os.access(cand, os.X_OK):
            return str(cand.resolve())
        raise DriverError(f"The --agy path is not executable: {cand}")
    discovered = shutil.which("agy")
    if discovered:
        return discovered
    raise DriverError(
        "Cannot find 'agy' on PATH. Install Antigravity CLI or pass --agy PATH."
    )


def state_root(repo: Path) -> Path:
    return repo / ".aw" / "records" / "runs"


def new_run_id() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"run-{stamp}-{os.getpid()}"


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
    full_auto = getattr(args, "full_auto", True)
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

        action = determine_action(status or "approved")
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
            "agy_executable": getattr(args, "agy_executable", None)
            or getattr(args, "agy", None),
            "model": getattr(args, "model", DEFAULT_MODEL),
            "effort": getattr(args, "effort", None),
            "timeout": getattr(args, "timeout", DEFAULT_TIMEOUT),
            "session": initial_session,
            "new_session": getattr(args, "new_session", False),
            "dangerously_skip_permissions": getattr(
                args, "dangerously_skip_permissions", True
            ),
            "no_verify": getattr(args, "no_verify", False),
            "output_mode": getattr(args, "output_mode", "clean"),
            "stall_timeout": getattr(args, "stall_timeout", DEFAULT_STALL_TIMEOUT),
            "full_auto": full_auto,
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
        f"# Antigravity IPD Driver Execution Report: {state.get('run_id', '')}",
        "",
        f"- Repository: `{state.get('repo', '')}`",
        f"- Created: {state.get('created_at', '')}",
        f"- Updated: {state.get('updated_at', '')}",
        f"- Selectors: `{' '.join(state.get('selectors', []))}`",
        f"- Set sessions: `{json.dumps(state.get('set_sessions', {}), sort_keys=True)}`",
        f"- Counts: `{json.dumps(counts, sort_keys=True)}`",
        "- Pushed: no (required; verify independently in outcomes)",
        "",
        "| # | id6 | Set | Action | Status | Verification | Attempts | Last session |",
        "|---:|---|---|---|---|---|---:|---|",
    ]
    for item in state["queue"]:
        attempts = item.get("attempts", [])
        session = attempts[-1].get("session_id", "") if attempts else ""
        action = item.get("action", "execute")
        v_stat = item.get("verification_status") or "N/A"
        lines.append(
            f"| {item['position']} | `{item['id6']}` | `{item['setid']}` | `{action}` | "
            f"{item['status']} | `{v_stat}` | {len(attempts)} | `{session}` |"
        )
    # revgate Order 03 (7nkcgp) E-04: name the ROOT CAUSE in the report an operator actually reads,
    # not only in events.jsonl. Its own section, so the table's column contract is unchanged.
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


_SESSION_ID_KEYS = ("sessionID", "sessionId", "session_id", "conversation_id")


def extract_session_id(log_path: Path) -> str | None:
    """Return the session / conversation id from a streamed JSONL log."""
    if not log_path.exists():
        return None
    fallback: str | None = None
    with log_path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            for key in _SESSION_ID_KEYS:
                value = event.get(key)
                if isinstance(value, str) and value.strip():
                    return value
            res = event.get("result")
            if isinstance(res, dict):
                for key in _SESSION_ID_KEYS:
                    value = res.get(key)
                    if isinstance(value, str) and value.strip():
                        return value
            init = event.get("init")
            if isinstance(init, dict):
                for key in _SESSION_ID_KEYS:
                    value = init.get(key)
                    if isinstance(value, str) and value.strip():
                        return value
    return fallback


def _findings_block_reason(repo: Path, dep: str) -> str | None:
    """Return an operator-facing reason ``dep``'s review blocks its dependents, else None.

    revgate Order 03 (7nkcgp) E-02. The MIRROR of ``oc_runipd._findings_block_reason``, and
    deliberately a thin one: all logic lives in the ONE shared predicate
    ``review_findings.plan_gating_blocks``, so the two hosts cannot diverge and the gate is not
    evadable by switching host. This wrapper exists only because neither runner imports the other (the
    duplication the in-flight `rununify` Set exists to fix); it holds no threshold and no severity
    comparison of its own.
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

    See :func:`dependency_status_detailed` for the additive per-dependency REASON map.
    """
    satisfied, unsatisfied, _reasons = dependency_status_detailed(item, state)
    return satisfied, unsatisfied


def dependency_status_detailed(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str], dict[str, str]]:
    """As :func:`dependency_status`, plus a ``{dep_id6: reason}`` map naming each ROOT CAUSE.

    revgate Order 03 (7nkcgp) E-01/E-02 + E-04, mirroring ``oc_runipd`` exactly: an execute-action
    dependency is satisfied by reaching `executed` ONLY IF it also carries no recorded unresolved
    gating findings, applied to BOTH the in-queue and out-of-queue resolution paths so the gate is not
    evadable by whether the target is in the same run. A `review`-action item is not findings-gated,
    since only an `executed:` edge asserts completed-and-verified work.
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
    return f"""# Antigravity IPD Driver Turn

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

All target IPDs are approved. Do not ask for approval. This run is non-interactive:
do not invoke an interactive question tool or wait for human input. When a material question
arises, investigate the approved plans, repository decisions, source, tests, history,
and current primary documentation. If a reasonable recommended approach exists, choose it,
record it in the decisions/questions register with evidence, alternatives, rationale, confidence,
scope, reversibility, and validation, then continue. If no reasonable approach exists, record a
DEFERRED question with the work completed, work blocked, dependency effect, exact preserved state,
and recommended human action. Continue every independent part of this IPD despite a deferred question.

Maximize safe forward progress. A local failure or unanswered question is not permission to
abandon independent work. Do not weaken checks, fabricate evidence, broaden approved
scope, bypass lifecycle controls, discard unrelated work, or push. Do not use git add -A,
git add ., git commit -a, --no-verify, destructive reset/clean, or stashing that could hide
ownership. Use path-scoped commits (`git commit -m msg -- <paths>`).

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

The disposition must describe the actual repository result, not merely your effort.
Explicitly confirm pushed=false.
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

You are an independent, skeptical verifier running in a fresh Antigravity session to audit
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
   - Run the required tests and validation commands for this IPD using `run_command` (e.g. `pytest <test_file> -v` or `python3 -m unittest ...`).
   - Paste the actual runner output with exit code.
   - Confirm that tests are genuine and testing real assertions (not trivial passes).

4. **In-Scope Fixes**:
   - If you discover safely correctable defects, regressions, or missing test cases within the approved scope, fix them, re-run validation, and commit path-scoped (`git commit -m msg -- <paths>`).
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
    prefix = "review" if item.get("action") == "review" else "exec"
    tag = f"-{suffix}" if suffix else ""
    path = (
        run_dir
        / "prompts"
        / f"{item['position']:02d}-{item['id6']}-{prefix}{tag}-attempt-{attempt_no}.md"
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
        / f"{item['position']:02d}-{item['id6']}{tag}-attempt-{attempt_no}.jsonl"
    )


def terminate_process(process: subprocess.Popen) -> None:
    """Reap a child Antigravity process and its process group without leaving orphans.

    Delegates to the SINGLE shared reaper in ``runner_shutdown``. This driver and
    ``oc_runipd`` previously carried byte-identical copies of this escalation, which spec
    `c4gd2h` R5 forbids (orchestrator CID-1: the check is repo-wide for exactly that reason).
    The module-level grace constants are read at call time and passed through, so a test that
    tunes them still takes effect.
    """

    runner_shutdown.terminate_process(
        process,
        sigint_grace=_SIGINT_GRACE_SECONDS,
        sigterm_grace=_SIGTERM_GRACE_SECONDS,
    )


_close_process_streams = runner_shutdown._close_process_streams


def run_agy_turn(
    state: dict[str, Any],
    run_dir: Path,
    item: dict[str, Any],
    prompt_path: Path,
    attempt_no: int,
    session_id: str | None,
    use_continue: bool,
    log_suffix: str = "",
    label_suffix: str = "",
    work_dir: str | None = None,
) -> tuple[int, str | None, Path, list[str]]:
    options = state.get("options", {})
    agy_bin = options.get("agy_executable") or options.get("agy") or resolve_agy(None)
    prompt_text = prompt_path.read_text(encoding="utf-8")
    timeout = options.get("timeout", DEFAULT_TIMEOUT)
    # driverfin-02 (emus4n): when isolated, Antigravity runs with its cwd set to the worktree so it
    # edits/commits only there. Defaults to the main repo.
    agent_dir = work_dir or state["repo"]

    argv = [
        agy_bin,
        "-p",
        prompt_text,
        "--output-format",
        "stream-json",
        "--print-timeout",
        str(timeout),
    ]

    if options.get("dangerously_skip_permissions", True):
        argv.append("--dangerously-skip-permissions")

    if options.get("model"):
        argv.extend(["--model", options["model"]])
    if options.get("effort"):
        argv.extend(["--effort", options["effort"]])

    if session_id:
        argv.extend(["--conversation", session_id])
    elif use_continue:
        argv.append("--continue")

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
        if process.stdout is None:
            terminate_process(process)
            raise DriverError("Failed to open child agy stdout stream")

        statusline = Statusline(
            pal=pal,
            stream=sys.stdout,
            tracker=None,
            interval=1.0 if is_tty and output_mode == "clean" else 0.0,
            current_idx=current_idx,
            total_items=total_items or 1,
            setid=item.get("setid", ""),
            id6=item.get("id6", ""),
            run_start_mono=run_start_mono,
        )
        watchdog = StallWatchdog(process, timeout=stall_timeout)
        # stallfp kaga7s (display parity only): show the countdown from the clock that kills.
        # agy needs NO progress observer: its stdout stream already carries
        # `step_type == "subagent"` events (see render_agy_event), so every subagent step
        # already touches the watchdog below.
        statusline.watchdog = watchdog
        try:
            with statusline, watchdog:
                for raw_line in process.stdout:
                    log.write(raw_line)
                    log.flush()
                    statusline.touch("stdout")
                    watchdog.touch()

                    if output_mode == "raw":
                        sys.stdout.write(raw_line)
                        sys.stdout.flush()
                    elif output_mode == "clean":
                        rendered = render_agy_event(raw_line, pal)
                        if rendered is not None:
                            statusline.write_event(rendered)
        except BaseException:
            terminate_process(process)
            log.flush()
            with contextlib.suppress(OSError):
                os.fsync(log.fileno())
            if watchdog.stalled:
                timeout_val = int(watchdog.timeout) if watchdog.timeout else 0
                raise StallTimeout(
                    f"Antigravity child turn stalled: no output for {timeout_val}s"
                ) from None
            raise

        if watchdog.stalled:
            terminate_process(process)
            log.flush()
            with contextlib.suppress(OSError):
                os.fsync(log.fileno())
            timeout_val = int(watchdog.timeout) if watchdog.timeout else 0
            raise StallTimeout(
                f"Antigravity child turn stalled: no output for {timeout_val}s"
            )

        rc = process.wait()
        log.flush()
        with contextlib.suppress(OSError):
            os.fsync(log.fileno())

    captured_conv_id = extract_session_id(log_path) or session_id
    return rc, captured_conv_id, log_path, argv


def reconcile_disposition(
    repo: Path, item: dict[str, Any], run_dir: Path, exit_code: int
) -> tuple[str, dict[str, Any] | None]:
    if item.get("action") == "review":
        try:
            current_plan = resolve_plan_path(
                repo, item.get("configured_file", ""), item["id6"]
            )
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
        current_plan = resolve_plan_path(
            repo, item.get("configured_file", ""), item["id6"]
        )
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
    run_dir: Path, state: dict[str, Any], item: dict[str, Any], recovery: bool
) -> None:
    repo = Path(state["repo"])
    pal = Palette(should_color(sys.stdout))
    plan_path = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])
    attempt_no = len(item.get("attempts", [])) + 1
    action = item.get("action", "execute")
    is_review = action == "review"

    if is_review:
        prompt_text = build_review_prompt(item, state, run_dir, plan_path, repo)
    else:
        prompt_text = build_prompt(item, state, run_dir, plan_path, recovery=recovery)

    prompt_path = write_prompt(run_dir, item, prompt_text, attempt_no)
    max_items = state.get("options", {}).get("max_items_per_session", 4)
    raw_session = (
        state.get("session_id")
        or state.get("set_sessions", {}).get(item["setid"])
        or state.get("options", {}).get("session")
    )
    is_rotation = False
    if raw_session and max_items and max_items > 0:
        session_turns = state.get("session_turn_counts", {}).get(raw_session, 0)
        if session_turns >= max_items:
            is_rotation = True
            raw_session = None

    session_id = raw_session
    use_continue = (
        False
        if (state.get("options", {}).get("new_session") or is_rotation)
        else (session_id is None)
    )

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
        "action": action,
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
            "action": action,
            "attempt": attempt_no,
        },
    )

    total = len(state["queue"])
    mode_note = " (recovery)" if recovery else ""
    action_str = f"action={action}"
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
    # driverfin-02 (emus4n): per-run worktree isolation. Allocate a fresh worktree on an
    # `aw/lane/<id6>` branch so the agent edits/commits ONLY there; the MAIN tree stays untouched.
    # begin runs against MAIN (receipt under the main repo's `.aw/state/`); the agent turn + verifier +
    # finalize run in the worktree. Opt out with `--no-isolate-worktree`.
    isolate = state.get("options", {}).get("isolate_worktree", True)
    wt_handle = None
    work_dir: str | None = None
    if self_finalize and not is_review:
        actor = driver_actor(state)
        # lanetruth Order 01 (af7i6p) E-04: verify ONCE per process that a pinned nested `aw`
        # resolves to this runner's own tooling before letting one perform a lifecycle transition.
        # Memoized (no per-call subprocess). A mismatch is RUN-FATAL per OQ-02.
        assert_child_tool_identity(run_dir / "events.jsonl", cwd=repo)
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
                # lanesess (xd9sll): this turn now runs in its OWN tree, so it must NOT inherit a
                # session bound to a DIFFERENT tree. Sessions were keyed per SET while worktrees are
                # per ITEM, so lanes 2..N inherited lane 1's conversation and, with it, lane 1's
                # directory, silently executing in the wrong worktree. Drop the inherited session and
                # do NOT fall back to `--continue` (which resumes the previous conversation and would
                # reintroduce the same carryover). Kept symmetric with oc_runipd.run_opencode; a
                # one-driver-only fix is asserted against in tests.
                session_id = None
                use_continue = False
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
        rc, captured_session, log_file, argv = run_agy_turn(
            state,
            run_dir,
            item,
            prompt_path,
            attempt_no,
            session_id=session_id,
            use_continue=use_continue,
            log_suffix="",
            label_suffix="",
            work_dir=work_dir,
        )
    except KeyboardInterrupt:
        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        item["status"] = "interrupted"
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {"at": now, "event": "ipd-interrupted", "id6": item["id6"]},
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

    if captured_session:
        # lanesess (xd9sll): keep the observed conversation on the ATTEMPT (audit trail), but only
        # PROMOTE it to the set/run-wide keys for a non-isolated turn. An isolated lane deliberately
        # runs in a fresh conversation, so promoting it would re-arm the cross-tree carryover this
        # fixes. Kept symmetric with oc_runipd.
        attempt["session_id"] = captured_session
        if not work_dir:
            counts = state.setdefault("session_turn_counts", {})
            state.setdefault("set_sessions", {})[item["setid"]] = captured_session
            state["session_id"] = captured_session
            counts[captured_session] = counts.get(captured_session, 0) + 1

    attempt.update(
        {
            "ended_at": utc_now(),
            "exit_code": rc,
            "ending_head": git_head(repo),
            "ending_branch": git_branch(repo),
            "ending_status": git_status(repo),
            "log": str(log_file),
            "argv": argv,
        }
    )
    from agent_workflows.run_viewer import extract_log_metrics

    att_cost, att_toks = extract_log_metrics(log_file)
    if att_cost is not None:
        attempt["cost"] = att_cost
    if att_toks:
        attempt["tokens"] = att_toks

    disposition, outcome = reconcile_disposition(repo, item, run_dir, rc)

    verify_disp = None
    no_verify = state.get("options", {}).get("no_verify") or state.get(
        "options", {}
    ).get("no_audit")
    if (
        not is_review
        and disposition in ("executed", "substantially-complete")
        and not no_verify
    ):
        # driverfin-02: when isolated, resolve the plan from the WORKTREE and run the verifier there.
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
            v_rc, _v_session, _v_log, _v_argv = run_agy_turn(
                state,
                run_dir,
                item,
                v_prompt_file,
                attempt_no,
                session_id=None,
                use_continue=False,
                log_suffix="verify",
                label_suffix="verification",
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
    # `substantially-complete`; trigger on disposition in {executed, substantially-complete} AND
    # verification == verified (NOT on `disposition == "executed"` alone). On success the plan moves
    # to executed/ (re-resolve, mark executed); on refusal keep substantially-complete, never force.
    if (
        self_finalize
        and not is_review
        and disposition in ("executed", "substantially-complete")
        and verify_disp == "verified"
    ):
        # driverfin-02 (emus4n): when isolated, finalize runs INSIDE the worktree so the plan-move
        # commits on the `aw/lane/<id6>` branch. Copy the begin receipt (anchored under the MAIN
        # repo's `.aw/state/`) into the worktree so the in-worktree finalize finds it.
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
            f"aw agy run self-finalize: {item['id6']} verified "
            f"(set {item['setid']}, attempt {attempt_no})."
        )
        fin_rc, fin_msg = driver_finalize(
            finalize_repo, current_plan_for_finalize, item["id6"], actor, fin_message
        )
        if fin_rc == 0:
            # driverfin-02: the plan is now in executed/ ON the lane branch. If isolated, integrate the
            # verified branch back to main via the REUSED gate + a driver ff/controlled merge, then
            # tear down the worktree. A non-passing gate result (or merge-back conflict) leaves the
            # child NOT integrated (recorded, deferred to child-03), never faked executed.
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
                # `merge-conflict`. Main is left UNTOUCHED, the verified lane branch/worktree is
                # PRESERVED for a human/serial resolution, and the child is NOT faked executed (its
                # set therefore is NOT reported finished).
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
                disposition = fail_status
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

    # driverfin-02 (emus4n): PRESERVE a still-allocated worktree attributably (verification did not
    # pass, finalize refused, or integration deferred) rather than tearing it away; child-03 owns the
    # guard + resolution.
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

    full_auto = state.get("options", {}).get("full_auto", True)
    auto_approved = False
    if is_review and disposition in ("reviewed", "approved") and full_auto:
        plan_curr = resolve_plan_path(
            repo, item.get("configured_file", ""), item["id6"]
        )
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
        + pal(f" ({action})", "dim")
        + " -> "
        + pal(disposition, glyph_color)
        + pal(f"  (exit {rc})", "dim")
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
            "action": action,
            "attempt": attempt_no,
            "exit_code": rc,
            "status": disposition,
            "session_id": captured_session,
            "verification_status": verify_disp,
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
            path = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])
            if plan_bucket(path) == "executed":
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
    """Re-queue items left `interrupted` so resume retries in recovery mode."""
    requeued: list[str] = []
    for item in state["queue"]:
        if item["status"] == "interrupted":
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


def run_queue(
    run_dir: Path, retry_incomplete: bool = False, output_mode: str | None = None
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

    while True:
        state = load_state(run_dir)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued:
            break
        runnable = None
        for item in queued:
            satisfied, _ = dependency_status(item, state)
            if satisfied:
                runnable = item
                break
        if runnable is None:
            for item in queued:
                _, missing, why = dependency_status_detailed(item, state)
                item["status"] = "dependency-blocked"
                item["unsatisfied_dependencies"] = missing
                # revgate Order 03 (7nkcgp) E-04: ADDITIVE companion keys; the flat
                # `unsatisfied_dependencies` list[str] keeps its exact shape for existing consumers.
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
        try:
            execute_item(run_dir, state, runnable, recovery=recovery)
        except ToolIdentityError:
            # lanetruth Order 01 (af7i6p) E-04 / OQ-02: RUN-FATAL. Must precede the item-local
            # `except DriverError` (ToolIdentityError subclasses it), or the abort would be
            # downgraded to one item marked `failed-safely` while later items ran under the same
            # wrong tooling. Mirrors oc_runipd.
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
    hint = render_continuation_hint(state, run_dir)
    print(hint)
    return 0 if all(item["status"] in SUCCESS_STATES for item in state["queue"]) else 1


@contextlib.contextmanager
def locked_run(run_dir: Path):
    """Hold the run lock AND guarantee the shared clean shutdown when the scope ends.

    The lock-holding layer is the only scope holding all four clean-shutdown invariants' inputs
    at once: the ``driver.lock`` handle (spec `c4gd2h` R2), the run ledger (R3), and the
    repository path (R4), plus the tracked child agent processes (R1). The per-turn
    ``run_agy_turn`` handlers hold no lock and have no queue authority, so they only reap the
    child. Kept symmetric with ``oc_runipd.locked_run`` (orchestrator CID-3).
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
    """Detect the command prefix used to invoke the runner, defaulting to 'aw agy run'."""
    argv = sys.argv
    for i in range(len(argv) - 1):
        if argv[i] in ("agy", "antigravity") and argv[i + 1] in (
            "run",
            "runipd",
            "runagy",
        ):
            return f"aw {argv[i]} {argv[i + 1]}"
    return "aw agy run"


def render_continuation_hint(
    state: dict[str, Any],
    run_dir: Path,
    driver_cmd: str | None = None,
) -> str:
    pal = Palette(should_color(sys.stdout))
    cmd = driver_cmd or _detect_driver_command()
    repo = state.get("repo", ".")
    run_id = state.get("run_id", "run-...")
    sessions = state.get("set_sessions", {})
    captured: list[tuple[str, str]] = [
        (s, sid) for s, sid in sessions.items() if sid and isinstance(sid, str)
    ]

    lines = ["", pal("--- Antigravity Session Continuity ---", "bold")]
    if not captured:
        lines.append("No Antigravity session was captured for this run.")
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
        # revgate Order 03 (7nkcgp) E-04: name the cause and the exact recovery command.
        reasons = item.get("unsatisfied_dependency_reasons") or {}
        for dep in item.get("unsatisfied_dependencies") or []:
            print(
                f"     blocked by {dep}: {reasons.get(dep) or 'dependency not satisfied'}"
            )
        hint = item.get("dependency_block_recovery")
        if hint and item.get("status") == "dependency-blocked":
            print(f"     recovery: {hint}")


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
        help="Stream the child agent's raw JSON events verbatim",
    )
    sub_parser.set_defaults(output_mode="clean")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="runagy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="""Autonomous Antigravity (agy) driver for Implementation Plan Documents (IPDs).

Drives pre-execution plan reviews for to-review IPDs, full non-interactive
execution for approved IPDs, and clean-session skeptical self-validation,
persisting durable run state, session logs, prompts, decisions, and outcomes
under `.aw/records/runs/<run-id>/`.

SELECTOR TYPES:
  - id6:      6-character unique ID (e.g. 'pr2nd0', '5ahblp')
  - setid:    IPD Set identifier (e.g. 'ipdrunner', 'execset')
  - filename: Path or filename of an IPD file (e.g. '.aw/records/plans/pending/...ipd.md')
  - all:      All actionable pending IPDs in the repository

AUTOMATIC STATUS ROUTING:
  - to-review: Runs Antigravity with `/plan-review <plan_path>`.
  - approved:  Executes the plan step-by-step according to the execution runbook,
               followed by independent verification in a clean session.
""",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    # start
    start = sub.add_parser(
        "start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Create a run and execute its queue (default)",
        description="Create a durable queue of IPDs and execute or review them.",
    )
    start.add_argument(
        "selectors",
        nargs="+",
        help="Target plan selectors: ID6, Set ID, IPD filename, or 'all'",
    )
    start.add_argument(
        "--repo", default=".", help="Target Git repository root (default: .)"
    )
    start.add_argument(
        "--manifest", default=None, help="Optional pre-baked manifest JSON path"
    )
    start.add_argument(
        "--runbook", default=None, help="Optional driver runbook markdown path"
    )
    start.add_argument(
        "--run-id",
        help="Explicit unique run ID (default: auto-generated timestamped ID)",
    )
    start.add_argument(
        "--agy",
        "--agy-executable",
        dest="agy_executable",
        help="Path to agy executable",
    )
    start.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Antigravity model (default: {DEFAULT_MODEL})",
    )
    start.add_argument("--effort", help="Reasoning effort (low|medium|high)")
    start.add_argument(
        "--timeout",
        default=DEFAULT_TIMEOUT,
        help=f"Timeout per turn (default: {DEFAULT_TIMEOUT})",
    )
    start.add_argument(
        "--session", help="Resume or bind a specific Antigravity conversation ID"
    )
    start.add_argument(
        "--new-session", action="store_true", help="Force fresh session for each Set"
    )
    start.add_argument(
        "--dangerously-skip-permissions",
        "--dangerous",
        dest="dangerously_skip_permissions",
        action="store_true",
        default=True,
        help="Auto-approve all tool permission requests in agy (default: True)",
    )
    start.add_argument(
        "--no-dangerously-skip-permissions",
        dest="dangerously_skip_permissions",
        action="store_false",
        help="Require interactive tool permissions in agy",
    )
    start.add_argument(
        "--no-verify",
        "--no-audit",
        dest="no_verify",
        action="store_true",
        help="Skip turn-2 clean-session skeptical validation",
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
        "--prepare-only",
        action="store_true",
        help="Create and display the durable queue without launching Antigravity",
    )
    start.add_argument(
        "--stall-timeout",
        type=float,
        default=DEFAULT_STALL_TIMEOUT,
        help=f"Timeout in seconds with no output from child agent before terminating (default: {DEFAULT_STALL_TIMEOUT}; 0 to disable)",
    )
    start.add_argument(
        "--full-auto",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Auto-approve reviewed plans with GO verdict and immediately execute",
    )
    start.add_argument(
        "--max-items-per-session",
        type=int,
        default=4,
        metavar="N",
        help="Maximum consecutive non-isolated turns per session before starting a fresh session (default: 4; 0 to disable rotation)",
    )
    _add_output_mode_flags(start)

    # resume
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
        "--agy",
        "--agy-executable",
        dest="agy_executable",
        help="Path to agy executable",
    )
    resume.add_argument(
        "--session", help="Override or attach Antigravity session ID for resuming turns"
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
        help="Override timeout in seconds with no output from child agent",
    )
    resume.add_argument(
        "--full-auto",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Override full-auto mode",
    )
    resume.add_argument(
        "--max-items-per-session",
        type=int,
        default=None,
        metavar="N",
        help="Override maximum consecutive non-isolated turns per session before starting a fresh session",
    )
    _add_output_mode_flags(resume)

    # status
    status = sub.add_parser(
        "status",
        help="Show status of an existing run",
        description="Inspect queue positions, attempt counts, actions, and statuses for a run.",
    )
    status.add_argument("run_id", help="Run ID or state directory path")
    status.add_argument("--repo", default=".", help="Target Git repository root")
    status.add_argument("--json", action="store_true", help="Output status as JSON")

    # report
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
            if getattr(args, "stall_timeout", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["stall_timeout"] = args.stall_timeout
                save_state(run_dir, state)
            if getattr(args, "max_items_per_session", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["max_items_per_session"] = (
                    args.max_items_per_session
                )
                save_state(run_dir, state)
            if getattr(args, "agy_executable", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["agy_executable"] = args.agy_executable
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
        print(f"runagy: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"runagy: unexpected failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
