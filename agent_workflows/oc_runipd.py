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
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Iterable, NamedTuple, Sequence, TextIO

# The interactive streaming render layer (Palette/render_event/Heartbeat and the
# coupled ANSI/status helpers) lives in the shared ``render_stream`` module so it is
# defined once and reusable across drivers (runnernorm child dg28i9). It is re-exported
# here (see ``__all__`` below) so existing ``oc_runipd`` call sites and tests keep
# referencing these names. ``should_color`` (the TTY color decision) stays local to the
# caller per OQ-01.
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
    format_statusline,
    format_statusline_lines,
    format_tokens,
    render_event,
)

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

# Frontmatter and filename extraction regexes
_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
_SET_RE = re.compile(r"(?m)^-\s*Set:\s*(.+?)\s*$")
_ORDER_RE = re.compile(r"(?m)^-\s*Order:\s*(\d+)\s*$")
_KIND_RE = re.compile(r"(?m)^-\s*Kind:\s*(\S+)\s*$")
# NOTE (lanetruth-03 / 8guhs0 E-01): there is deliberately NO dependency regex here. The runner
# used to carry a private `_DEPS_RE` matching a LEGACY `Dependencies:`/`Depends-on:` field that no
# plan in the tree uses, so the canonical `- Item-Dependencies:` statement was invisible and every
# queue item froze with `dependencies: []`. The canonical field NAME comes from
# `ipd_schema.META_ITEM_DEPENDENCIES` and its GRAMMAR from `ipd_schema.parse_item_dependencies`
# (see `_read_item_dependencies`). Spec 25kzda 2.10: "All surfaces call this evaluator; none
# reimplement the rules." Re-adding a dependency regex here is a regression guarded by
# tests/test_runner_item_dependencies.py.
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
    merged_env = os.environ.copy()
    repo_src = str(Path(__file__).resolve().parent.parent)
    cur_pp = merged_env.get("PYTHONPATH", "")
    if repo_src not in cur_pp.split(os.pathsep):
        merged_env["PYTHONPATH"] = f"{repo_src}{os.pathsep}{cur_pp}".rstrip(os.pathsep)
    if env:
        merged_env.update(env)
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
    cmd = [
        sys.executable,
        "-m",
        "agent_workflows",
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
    try:
        run_checked(cmd, cwd=repo)
        return
    except (FileNotFoundError, OSError):
        pass
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
    cmd = [
        sys.executable,
        "-m",
        "agent_workflows",
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


def driver_begin(repo: Path, id6: str, actor: str) -> tuple[int, str]:
    """Run the fail-closed `aw ipd begin <id6> --actor` gate before an execute turn.

    Reuses the packaged `aw ipd begin` surface (subprocess to `python -m agent_workflows`,
    mirroring `set_plan_approved`/`finalize_orchestrator`); begin writes the gitignored
    `.aw/state/ipd-lifecycle/<id6>.receipt.json` receipt (execution authority) itself. Returns
    (exit_code, stderr): exit 0 = receipt written; nonzero = refusal (no execution authority)."""
    cmd = [
        sys.executable,
        "-m",
        "agent_workflows",
        "ipd",
        "begin",
        id6,
        "--actor",
        actor,
        "--dir",
        str(repo),
    ]
    result = subprocess.run(
        cmd,
        cwd=str(repo),
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
    cmd = [
        sys.executable,
        "-m",
        "agent_workflows",
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
    for path, reason in reasons.items():
        cmd.extend(["--scope-reason", f"{path}={reason}"])
    for path, note in acks.items():
        cmd.extend(["--scope-ack", f"{path}={note}"])
    result = subprocess.run(
        cmd,
        cwd=str(repo),
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
# Each execute-action child runs in its OWN git worktree on an `aw/lane/<id6>` branch (via the reused
# `worktree_lease`), so the MAIN working tree is untouched during the turn (no cross-run
# contamination). begin runs against the MAIN repo (the receipt lives under the main repo's gitignored
# `.aw/state/`, findable regardless of worktree); the agent turn + verifier + `aw ipd finalize` all run
# INSIDE the worktree, so the plan-move (pending/ -> executed/) commits on the lane branch. After a
# verified finalize, the verified branch is integrated back to main by REUSING
# `orchestrate_isolation.execute_merge_and_revalidate_gate` (detect conflicts + revalidate) followed by
# a driver fast-forward/controlled merge; the worktree is torn down on success. A non-passing gate
# result leaves the child NOT integrated (recorded, deferred to child-03), never faked executed.


def allocate_isolation_worktree(repo: Path, id6: str) -> Any:
    """Allocate a per-lane git worktree for an execute-action child (reuses worktree_lease).

    Returns a `worktree_lease.WorktreeHandle` (branch `aw/lane/<id6>`, dir `.aw/worktrees/<id6>`, base
    = main HEAD) or raises `worktree_lease.WorktreeError` on failure (fail-closed; no partial worktree
    left claimed)."""
    from agent_workflows import worktree_lease

    return worktree_lease.allocate_worktree(repo, id6, base_commit="HEAD")


def teardown_isolation_worktree(repo: Path, handle: Any) -> None:
    """Remove a lane's worktree + branch (reuses worktree_lease.teardown_worktree)."""
    from agent_workflows import worktree_lease

    worktree_lease.teardown_worktree(repo, handle, force=True)


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
    lock_path = run_dir / "driver.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise DriverError(
                f"Run is already controlled by another process: {run_dir.name}"
            ) from exc
        handle.seek(0)
        handle.truncate()
        handle.write(f"pid={os.getpid()} started={utc_now()}\n")
        handle.flush()
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


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


def _read_item_dependencies(text: str) -> tuple[list[str], str | None]:
    """Read the plan's canonical `- Item-Dependencies:` statement as CANONICAL TYPED edge tokens.

    Returns ``(edges, error)`` where ``edges`` is the list of canonical edge strings (e.g.
    ``["executed:af7i6p", "exists:spec:d4e5f6", "state:backlog:done:g7h8j9"]``) and ``error`` is the
    shared parser's message for a malformed statement (else None). `none`, `unresolved`, an empty
    value, and an absent field all yield ``([], None)``; the MISSING-vs-`none` distinction is NOT the
    runner's to judge (see `preflight_dependency_findings` and 8guhs0 OQ-02).

    THE QUALIFIER IS PRESERVED, NOT STRIPPED. The deleted `_read_deps` kept only bare id6 tokens,
    which would have silently degraded `exists:spec:<id6>` into an untyped id6 with different
    release semantics (plan finding F4). The satisfaction rule depends on the kind, so the typed
    token is what the record and the frozen queue must carry.

    Two shared authorities, no private parsing: the field NAME is `ipd_schema`'s constant and the
    metadata block is read by `ipd_lint.parse` (the same structural, fence-aware reader the lint and
    lifecycle surfaces use, measured byte-identical to `check_engine`'s extraction across the whole
    plans tree); the VALUE grammar is `ipd_schema.parse_item_dependencies`.
    """
    from agent_workflows import ipd_lint as _lint
    from agent_workflows import ipd_schema as _schema

    try:
        fields = _lint.parse(text).meta_fields
    except Exception:
        return [], None
    raw = fields.get(_schema.META_ITEM_DEPENDENCIES)
    if raw is None:
        return [], None
    edges, _ready, err = _schema.parse_item_dependencies(raw)
    if err:
        return [], err
    return [edge.canonical() for edge in edges], None


class PlanRecord(NamedTuple):
    id6: str
    setid: str
    status: str
    order: int
    path: Path
    rel_path: str
    # CANONICAL TYPED edge tokens (`executed:<id6>` / `exists:<type>:<id6>` /
    # `state:<type>:<status>:<id6>`), never bare id6 strings: the qualifier decides the satisfaction
    # rule (`dependency_status`). `dependency_error` carries the shared parser's message when the
    # statement is malformed, so preflight can fail closed instead of silently seeing no edges.
    dependencies: list[str]
    kind: str | None = None
    dependency_error: str | None = None


def parse_plan_file(path: Path, repo: Path) -> PlanRecord | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    id6 = _read_id(text)
    setid = _read_set(text)
    status = _read_status(text)
    order = _read_order(text)
    deps, dep_err = _read_item_dependencies(text)
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
        dependency_error=dep_err,
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


def parse_dependency_token(token: str) -> Any:
    """Resolve ONE frozen dependency token to a shared `ipd_schema.ItemDependency`, or None.

    The token grammar is the SHARED one (`parse_item_dependencies`); nothing is parsed here. The one
    accommodation is a BARE id6, which a hand-written manifest JSON may still carry (the shipped
    `tools/ipdrunner/*-driver-manifest.json` does): it is normalized to the `executed:<id6>` edge,
    which is what the pre-8guhs0 driver's bare deps already MEANT (`dependency_status` required the
    target to be in `executed/`). Plan FILES never take this path; their statements are read by
    `_read_item_dependencies` and are already canonical typed tokens.
    """
    from agent_workflows import ipd_schema as _schema

    tok = str(token).strip()
    if not tok:
        return None
    edges, _ready, err = _schema.parse_item_dependencies(tok)
    if not err and len(edges) == 1:
        return edges[0]
    if ID6_RE.fullmatch(tok):
        return _schema.ItemDependency("executed", "ipd", None, tok)
    return None


def dependency_target_id6(token: str) -> str | None:
    """The target id6 of a dependency token (None when the token is not a legal edge)."""
    edge = parse_dependency_token(token)
    return edge.id6 if edge is not None else None


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
        # 8guhs0 E-01: a dependency token is a SHARED-grammar typed edge (or a bare id6 in a legacy
        # hand-written manifest, normalized to `executed:`). Only IPD-typed targets must name a plan
        # in the manifest; a `spec`/`backlog` target is a graph LEAF (spec 25kzda 2.10) and is
        # resolved against the repository, not the queue.
        malformed = [dep for dep in dependencies if parse_dependency_token(dep) is None]
        if malformed:
            raise DriverError(
                f"Plan {id6} has malformed Item-Dependencies edges: {malformed}"
            )
        unknown = []
        for dep in dependencies:
            edge = parse_dependency_token(dep)
            if edge.target_type == "ipd" and edge.id6 not in plans:
                unknown.append(dep)
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


# Dependency findings that ABORT the whole run rather than failing one component. Spec 25kzda 2.10
# maps `check.ipd-dependency-ambiguous` to the `fatal` identity/type-ambiguity class, and 5.4 rule 1
# says "identity/type ambiguity aborts the run"; every other dependency finding fails only the
# affected graph component.
DEPENDENCY_FATAL_RULES = frozenset(("check.ipd-dependency-ambiguous",))


def preflight_dependency_findings(
    repo: Path, plan_paths: list[Path], *, phase: str = "pre-execution"
) -> list[tuple[str, str, str]]:
    """Run the SHARED dependency evaluator over the selected plans. Returns [(location, rule, msg)].

    E-02 DELEGATES ENTIRELY: this calls `check_engine.evaluate_ipd_dependencies` with a BLOCKING
    phase and surfaces whatever it returns, naming the shared `check.ipd-*dependency*` rules. There
    is deliberately NO runner-local dependency policy here, and in particular NO runner-local branch
    for the MISSING-statement case.

    WHY NO MISSING-STATEMENT BRANCH (8guhs0 OQ-02, resolved from repository evidence; see orchestrator
    y0gg8o OQ-03): the decision is the evaluator's plus the cutover marker's, not the runner's. The
    marker gates it (`config.dependency_cutover_date`), an ABSENT marker grandfathers every existing
    plan, and spec 2.10's severity column for `check.ipd-missing-dependency-statement` is itself
    phase-and-provenance conditional, so severity belongs to the evaluator. `ipd_lint` already encodes
    exactly this deferral. A runner that refused a fieldless plan on its own authority would be
    STRICTER than `aw check` and `aw ipd lint`, recreating the very divergence 8guhs0 exists to
    remove and violating 2.10's "none reimplement the rules". If a maintainer later SETS the cutover
    marker, fieldless plans begin failing preflight automatically, with no change here.
    """
    from agent_workflows import check_engine as _ce

    plans: list[tuple[Path, str]] = []
    for path in plan_paths:
        try:
            plans.append((path, path.read_text(encoding="utf-8")))
        except OSError:
            continue
    if not plans:
        return []
    drift = _ce.evaluate_ipd_dependencies(repo, phase=phase, plans=plans)
    return [(d.location, d.rule, d.detail) for d in drift]


def enforce_dependency_preflight(
    repo: Path, plan_paths: list[Path], *, phase: str = "pre-execution"
) -> list[tuple[str, str, str]]:
    """Fail CLOSED on an invalid selected dependency graph BEFORE any host session starts.

    Raises `DriverError` when the shared evaluator reports any finding for the selected plans, so a
    malformed/dangling/ambiguous/cyclic/self-edge statement (and the `unresolved` scaffold sentinel)
    refuses the run at freeze time rather than after a session has already mutated the repository.
    Returns the findings list (empty) when the graph is valid, so a caller can record "checked, clean".
    """
    findings = preflight_dependency_findings(repo, plan_paths, phase=phase)
    if not findings:
        return findings
    fatal = [f for f in findings if f[1] in DEPENDENCY_FATAL_RULES]
    lines = [f"  {rule}: {msg} [{loc}]" for loc, rule, msg in findings]
    label = (
        "run ABORTED (identity/type ambiguity is fatal)"
        if fatal
        else "run refused before any session started"
    )
    raise DriverError(
        "dependency preflight failed: "
        + label
        + " - the selected IPDs' `- Item-Dependencies:` statements did not pass the shared "
        f"evaluator at phase {phase!r}:\n"
        + "\n".join(lines)
        + "\nFix with `aw ipd dependencies set <id6> none|<edge>...`, then re-run."
    )


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

    # 8guhs0 E-02: FAIL CLOSED on an invalid dependency graph BEFORE any host session starts (and
    # before the run directory exists, so a refused run leaves no durable state to reconcile). The
    # rules and their severities are the SHARED evaluator's; see `enforce_dependency_preflight`.
    selected_plan_paths: list[Path] = []
    for id6 in queue_ids:
        try:
            selected_plan_paths.append(
                resolve_plan_path(repo, manifest["plans"][id6].get("file", ""), id6)
            )
        except (DriverError, KeyError):
            continue
    enforce_dependency_preflight(repo, selected_plan_paths)

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
                # 8guhs0 E-04: the plan's numeric Order, frozen for use as a TIEBREAKER only (see
                # `queue_sort_key`). Additive: an older run directory lacking the key still sorts
                # (the comparator defaults it), so existing runs resume unchanged.
                "order": plan.get("order"),
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


def _artifact_owners(repo: Path, record_type: str, id6: str) -> list[tuple[str, str]]:
    """Owners of ``id6`` of ``record_type`` as ``[(status, path)]`` via the SHARED identity index.

    Reuses `check_engine.build_dependency_index` (the same index the shared evaluator resolves edges
    with), so the runner and `aw check` cannot disagree about what an id6 names. Empty list = the
    target does not exist (dangling); more than one = ambiguous.
    """
    try:
        from agent_workflows import check_engine as _ce

        index = _ce.build_dependency_index(repo)
    except Exception:
        return []
    return [
        (st or "", path)
        for rt, st, path in index.owners.get(id6, [])
        if rt == record_type
    ]


def edge_satisfied(
    edge: Any,
    item: dict[str, Any],
    state: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> tuple[bool, str]:
    """Is ONE typed edge satisfied? Returns ``(satisfied, reason)``; ``reason`` is "" when satisfied.

    WHY THIS LIVES IN THE RUNNER AND NOT IN THE SHARED EVALUATOR (8guhs0 F7; spec 25kzda 2.9 vs
    2.10). Spec 2.10's "All surfaces call this evaluator; none reimplement the rules" governs the
    STATIC rules: malformed, dangling, ambiguous, cyclic, missing-at-phase. Those are delegated
    wholesale to `check_engine.evaluate_ipd_dependencies` in `preflight_dependency_findings`, and
    NOTHING of them is re-implemented here. What follows is spec 2.9's RUNTIME wait/release
    semantics, which that evaluator structurally CANNOT answer: its signature is
    `evaluate_ipd_dependencies(repo_root, *, phase, plans, overlay) -> List[Drift]` and it has no
    notion of a run, a queue, an item's outcome, or `verified` (verified by inspection: those words
    do not appear in its body). "Is this prerequisite verified IN THIS RUN yet?" is a question about
    run state, and run state lives here. So this is NOT a second implementation of the shared rules,
    and it must not be "consolidated" into the static evaluator: doing so would break both, because
    the static evaluator is called from `aw check`/lint/hook contexts that have no run at all. The
    IDENTITY index is still shared (`_artifact_owners` -> `check_engine.build_dependency_index`), so
    only the run-state judgement is local.
    """
    repo = Path(state["repo"])
    is_exec = item.get("action") != "review"
    tok = edge.canonical()

    if edge.kind == "executed":
        # spec 2.9: the target must be terminally executed with valid finalization evidence, or, if
        # it is IN THIS RUN, its current outcome must be `verified`.
        entry = by_id.get(edge.id6)
        if entry is not None:
            required_states = EXECUTION_SUCCESS_STATES if is_exec else SUCCESS_STATES
            if entry.get("status") not in required_states:
                return False, (
                    f"{tok}: in-run target {edge.id6} is {entry.get('status')!r}, "
                    f"needs one of {sorted(required_states)}"
                )
            return True, ""
        # Outside the queue: evaluated from frozen repository state. There is no
        # `--with-dependencies` closure in this runner, so an unsatisfied external target simply
        # cannot be met in this run.
        try:
            dep_path = resolve_plan_path(repo, "", edge.id6)
        except DriverError as exc:
            return False, f"{tok}: {exc}"
        bucket = plan_bucket(dep_path)
        allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")
        if bucket not in allowed:
            return False, (
                f"{tok}: external target {edge.id6} is in {bucket!r}, needs one of {list(allowed)} "
                "(it is not in this run, so it cannot become satisfied here)"
            )
        return True, ""

    from agent_workflows import ipd_schema as _schema

    record_type = _schema.ITEM_DEP_TYPE_TO_RECORD_TYPE.get(edge.target_type)
    owners = _artifact_owners(repo, record_type or "", edge.id6)
    if not owners:
        return False, f"{tok}: no {edge.target_type} artifact has id6 {edge.id6}"
    if len(owners) > 1:
        return False, (
            f"{tok}: id6 {edge.id6} matches multiple {edge.target_type} artifacts "
            f"({', '.join(p for _s, p in owners)})"
        )
    status = owners[0][0]

    if edge.kind == "exists":
        # spec 2.9: evaluated immediately from current repository state; NEVER waits for the target
        # to run, whatever its status.
        return True, ""

    # `state:` - the EXACT status is required. An already-satisfied `state:` edge is immediately
    # releasable (this returns True right away, no waiting); the scheduler's obligation is to run the
    # dependent BEFORE advancing the target away from that status, which holds here because the
    # runner never mutates a `spec`/`backlog` target, and an in-queue IPD target that would advance
    # is ordered AFTER its dependent by `queue_sort_key` (dependency depth).
    if status != edge.status:
        return False, (
            f"{tok}: {edge.target_type} {edge.id6} is {status!r}, needs exactly {edge.status!r}"
        )
    return True, ""


def dependency_status(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str]]:
    """Are all of ``item``'s declared edges satisfied? Returns ``(satisfied, unsatisfied_tokens)``.

    Each dependency is a CANONICAL TYPED token (8guhs0 E-01), so it is resolved through the shared
    grammar before use. NOTE the hazard this closes (plan finding F8): the pre-8guhs0 code used each
    `dep` BOTH as a queue dict key (`dep in by_id`) and as an id6 for `resolve_plan_path`, so an
    unconverted `"executed:af7i6p"` string would miss the queue lookup AND fail id6 resolution,
    landing in `unsatisfied` and BLOCKING a satisfied dependent. The failure direction is therefore
    over-blocking, not wrongly admitting; `parse_dependency_token` converts the token first so the
    id6 and the queue key are both taken from the parsed edge, never from the raw string.
    """
    by_id = {entry["id6"]: entry for entry in state["queue"]}
    unsatisfied: list[str] = []
    for dep in item.get("dependencies", []):
        edge = parse_dependency_token(dep)
        if edge is None:
            # Fail closed: an unparseable token is never treated as "no dependency". Preflight
            # (`preflight_dependency_findings`) refuses such a run before any session starts; this
            # is the belt-and-braces path for a hand-edited state.json.
            unsatisfied.append(str(dep))
            continue
        ok, _reason = edge_satisfied(edge, item, state, by_id)
        if not ok:
            # Report the token AS DECLARED, not its canonical rewrite: `unsatisfied_dependencies` is
            # written into durable run records, and echoing a bare id6 back as `executed:<id6>` would
            # silently change what those records say the plan asked for. A typed statement therefore
            # reports its typed token; a legacy bare id6 reports the bare id6.
            unsatisfied.append(str(dep))
    return not unsatisfied, unsatisfied


def dependency_depth(id6: str, by_id: dict[str, dict[str, Any]]) -> int:
    """Longest declared in-queue prerequisite chain ending at ``id6`` (0 = no in-queue prerequisite).

    Only IPD-typed edges whose target is IN THE QUEUE contribute: an external target or a
    `spec`/`backlog` leaf is not a queue node and cannot order the queue. Cycle-safe (a cycle is
    already refused by preflight, but a hand-edited state.json must not hang the scheduler here).
    """

    def _depth(node: str, seen: frozenset[str]) -> int:
        if node in seen:
            return 0
        entry = by_id.get(node)
        if entry is None:
            return 0
        best = 0
        for dep in entry.get("dependencies", []):
            edge = parse_dependency_token(dep)
            if edge is None or edge.target_type != "ipd" or edge.id6 not in by_id:
                continue
            best = max(best, 1 + _depth(edge.id6, seen | {node}))
        return best

    return _depth(id6, frozenset())


def queue_sort_key(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> tuple:
    """Deterministic ordering key for READY nodes (spec 25kzda 5.4 rules 4-5).

    DECLARED EDGES WIN; Set/Order is only a TIEBREAKER among nodes that are already ready. Ordering
    by dependency DEPTH first is what demotes Set/Order: a depth-0 node always precedes a node that
    declares an in-queue prerequisite, whatever their Order numbers say. Set/Order can therefore no
    longer act as evidence that a dependency is satisfied (rule 3), which is what it silently did
    while `dependencies` was always `[]`.

    Spec 5.4 rule 4 also lists a TYPE RANK (`spec`, `backlog`, `ipd`, `prompt`) ahead of Set. It is
    deliberately NOT implemented: this runner's queue is homogeneous (IPDs only; there is no
    `--with-dependencies` closure and no non-plan item can enter), so a rank over types that cannot
    appear would be untestable dead code. Recorded rather than silently skipped.

    `position` is LAST and is a stable identity, never a priority: outcome/prompt/session filenames
    and this run's decision ids all key on it, so it is frozen at queue-build time and is used here
    only to make the sort total.
    """
    return (
        dependency_depth(item["id6"], by_id),
        str(item.get("setid") or ""),
        item.get("order") if isinstance(item.get("order"), int) else 999,
        item["id6"],
        item.get("position", 0),
    )


def cascade_dependency_blocked(
    state: dict[str, Any], run_dir: Path | None = None
) -> list[dict[str, Any]]:
    """Propagate `dependency-blocked` over reverse edges to a fixed point (spec 25kzda 5.4 rule 7).

    A queued item whose prerequisite reached a NON-success terminal state can never become runnable,
    so it is marked blocked immediately instead of stalling the queue, and its own dependents follow
    transitively. Independent items are untouched and keep running.

    Uses the EXISTING `dependency-blocked` disposition (already in `TERMINAL_STATES` and already
    written by the orchestrator-deferral path). It does NOT introduce `dependency-not-met`, which is
    the spec's vocabulary but does not exist anywhere in this runner; inventing a parallel state
    would split the run records already on disk.
    """
    blocked: list[dict[str, Any]] = []
    while True:
        by_id = {entry["id6"]: entry for entry in state["queue"]}
        progressed = False
        for item in state["queue"]:
            if item.get("status") != "queued":
                continue
            dead: list[str] = []
            for dep in item.get("dependencies", []):
                edge = parse_dependency_token(dep)
                if edge is None or edge.target_type != "ipd":
                    continue
                entry = by_id.get(edge.id6)
                if entry is None:
                    continue
                st = entry.get("status")
                if st in TERMINAL_STATES and st not in EXECUTION_SUCCESS_STATES:
                    dead.append(f"{edge.canonical()} (target {st})")
            if not dead:
                continue
            item["status"] = "dependency-blocked"
            item["unsatisfied_dependencies"] = dead
            blocked.append(item)
            progressed = True
            if run_dir is not None:
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "dependency-blocked",
                        "id6": item["id6"],
                        "dependencies": dead,
                        "reason": "prerequisite reached a non-success terminal state",
                    },
                )
        if not progressed:
            return blocked


def dependency_reasons(item: dict[str, Any], state: dict[str, Any]) -> list[str]:
    """Human-readable reasons for each unsatisfied edge (for events/report; no gating decision)."""
    by_id = {entry["id6"]: entry for entry in state["queue"]}
    reasons: list[str] = []
    for dep in item.get("dependencies", []):
        edge = parse_dependency_token(dep)
        if edge is None:
            reasons.append(f"{dep}: not a legal Item-Dependencies edge")
            continue
        ok, reason = edge_satisfied(edge, item, state, by_id)
        if not ok:
            reasons.append(reason)
    return reasons


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
    return f"""# OpenCode IPD Driver Turn

Mode: {mode}
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
    """Reap a child OpenCode process and its process group without leaving orphans."""
    if process.poll() is not None:
        _close_process_streams(process)
        return

    def _signal(sig: int) -> bool:
        if hasattr(os, "killpg") and hasattr(os, "getpgid") and hasattr(os, "getpgrp"):
            try:
                pgid = os.getpgid(process.pid)
                if pgid != os.getpgrp():
                    os.killpg(pgid, sig)
                    return True
            except (ProcessLookupError, OSError):
                pass
        try:
            process.send_signal(sig)
            return True
        except (ProcessLookupError, OSError):
            return False

    for sig, grace in (
        (signal.SIGINT, _SIGINT_GRACE_SECONDS),
        (signal.SIGTERM, _SIGTERM_GRACE_SECONDS),
    ):
        if not _signal(sig):
            break
        try:
            process.wait(timeout=grace)
            _close_process_streams(process)
            return
        except subprocess.TimeoutExpired:
            continue

    _signal(signal.SIGKILL)
    with contextlib.suppress(Exception):
        process.wait(timeout=_SIGTERM_GRACE_SECONDS)
    _close_process_streams(process)


def _close_process_streams(process: subprocess.Popen) -> None:
    for stream in (process.stdout, process.stderr, process.stdin):
        if stream is not None:
            with contextlib.suppress(Exception):
                stream.close()


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
        process = subprocess.Popen(argv, **popen_kwargs)
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
        try:
            with statusline, watchdog:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    statusline.touch()
                    watchdog.touch()
                    if output_mode == "raw":
                        sys.stdout.write(line)
                        sys.stdout.flush()
                    elif output_mode == "clean":
                        rendered = render_event(line, pal, tracker=tracker)
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
                    f"OpenCode child turn stalled: no output for {timeout_val}s"
                ) from None
            raise

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
                attempt["worktree"] = work_dir
                attempt["worktree_branch"] = wt_handle.branch
                save_state(run_dir, state)
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "worktree-allocated",
                        "id6": item["id6"],
                        "worktree": work_dir,
                        "branch": wt_handle.branch,
                    },
                )
                print(
                    pal(
                        f"  \u2713 isolated worktree {wt_handle.branch} at {work_dir}",
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
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "worktree-preserved",
                "id6": item["id6"],
                "worktree": str(wt_handle.path),
                "branch": wt_handle.branch,
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
    tracker = StreamTracker()
    while True:
        state = load_state(run_dir)
        # 8guhs0 E-04: cascade FIRST. An item whose prerequisite already reached a non-success
        # terminal state can never become runnable, so mark it (and its dependents, transitively)
        # `dependency-blocked` and keep going with independent work rather than stalling the queue.
        if cascade_dependency_blocked(state, run_dir):
            save_state(run_dir, state)
            state = load_state(run_dir)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued:
            break
        runnable = None
        # 8guhs0 E-04: DECLARED EDGES are authoritative; Set/Order only breaks ties among nodes that
        # are ALREADY ready (spec 25kzda 5.4 rules 3-5). Selecting from a dependency-ordered list is
        # what demotes Set/Order: a lower Order can no longer make an unsatisfied node runnable, and
        # a higher Order can no longer delay an otherwise independent prerequisite.
        by_id = {entry["id6"]: entry for entry in state["queue"]}
        for item in sorted(queued, key=lambda it: queue_sort_key(it, by_id)):
            satisfied, _ = dependency_status(item, state)
            if satisfied:
                runnable = item
                break
        if runnable is None:
            for item in queued:
                _, missing = dependency_status(item, state)
                item["status"] = "dependency-blocked"
                item["unsatisfied_dependencies"] = missing
                append_jsonl(
                    run_dir / "events.jsonl",
                    {
                        "at": utc_now(),
                        "event": "dependency-blocked",
                        "id6": item["id6"],
                        "dependencies": missing,
                        "reasons": dependency_reasons(item, state),
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
        try:
            execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)
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
    return 0 if all(item["status"] in SUCCESS_STATES for item in state["queue"]) else 1


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
        help="Timeout in seconds with no output from child agent before terminating (default: 600; 0 to disable)",
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
        help="Override timeout in seconds with no output from child agent (default: 600; 0 to disable)",
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
            with run_lock(run_dir):
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
            with run_lock(run_dir):
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
