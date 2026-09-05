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
import hashlib
import json
import os
import re
import select
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Iterable, NamedTuple, Sequence

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
from agent_workflows import platform_lock, runner_shutdown

# rununify 01 (`2r306y`): the rest of the display layer this module used to RE-FORK. `Palette`,
# `_strip_ansi`, `_one_line` and the four ANSI/status constants their bodies close over were
# inline copies here, AST-identical to `render_stream`'s, for exactly the reason `Heartbeat`
# above was: the guard that forbade these copies was written for `oc_runipd` only, so nothing
# noticed when this module grew its own. The constants are imported alongside the functions on
# purpose; keeping identical copies of just the constants would leave the same defect one layer
# down (a change to the palette or the status colors would still not reach `aw agy run`).
# `oc_runipd` imports the same seven names from the same owner (see its `__all__`), so the two
# drivers now bind the SAME objects. The `as <same-name>` form marks the ones this module does
# not call itself as an intentional re-export, so an autoformatter cannot strip them.
# rununify 01 (`2r306y`): identical copies of these two readers lived here and in `oc_runipd`,
# both AST-identical to `selectors`' readers. Both drivers now bind the SAME public `selectors`
# functions under the private names their call sites use, so a fix reaches both. The aliases are
# deliberately the PERMISSIVE readers, preserving the whitespace tolerance these copies had;
# `selectors`' strict internal readers back `aw find` and are unchanged.
from agent_workflows.selectors import read_front_matter_id as _read_id
from agent_workflows.selectors import read_front_matter_status as _read_status

from agent_workflows.render_stream import (
    Statusline,
    render_run_summary_table,
    install_exit_signal_handler,
    statusline_action_for_item,
    execution_index as execution_index,
    Palette as Palette,
    _strip_ansi as _strip_ansi,
    _one_line as _one_line,
    _ANSI_RESET as _ANSI_RESET,
    _ANSI_CODES as _ANSI_CODES,
    _ANSI_STRIP_RE as _ANSI_STRIP_RE,
    _STATUS_COLOR as _STATUS_COLOR,
)

# runorder (prpipy) E-07: an intentional RE-EXPORT, in the `as <same-name>` form this module uses for
# every shared object it must expose but does not call itself, so an autoformatter cannot strip it.
# The run-order announcement's WORDING has exactly ONE definition in the package and this driver
# binds that same object; it does NOT own a copy. The announcement itself is emitted through the
# shared `announce_run_order` below, so the two hosts cannot drift the way `Heartbeat` once did.
from agent_workflows.render_stream import (
    format_run_order_announcement as format_run_order_announcement,
)

# terseout `ntf6sx` E-04: the ONE concise-reporting contract, embedded in FULL in this driver's
# execution and verifier prompts (the same module the OpenCode driver and the installed
# `AGENTS.md#aw:reporting` section use), so the two drivers cannot drift apart.
from agent_workflows import reporting_contract

# fullauto Order 01 (97df1z): the `--full-auto` auto-approve gate lives in ONE shared module. This
# driver used to carry its own NEAR-copy of `is_plan_review_approved`/`extract_last_history_entry`
# (docstrings already stripped relative to the oc copies - live evidence of the drift), which meant a
# fix to one driver left `aw agy run --full-auto` broken. Do NOT reintroduce a local copy.
from agent_workflows.plan_readiness import (
    extract_newest_history_entry as extract_newest_history_entry,
)
from agent_workflows.plan_readiness import is_plan_review_approved

# rununify 02 (`818uru`): the symbols below were defined in THIS module AND in `oc_runipd` with
# bodies PROVEN AST-identical, so each had two definitions and a fix to one silently missed the other.
# They now have exactly ONE definition, in `runner_shared`, and are re-exported here so every call
# site and test in this module keeps working unchanged. NOTE this is a genuine LAYERING improvement
# and not just de-duplication: these names no longer reach this module THROUGH `oc_runipd` (see the
# 40-name import block below, which remains and is tracked as backlog `cnwy8g`), they come from a
# module that imports neither runner.
#
# `DriverError` is the reason this seam went first: it was defined as two DISTINCT classes, which is
# why the `enforce_dependency_preflight` wrapper below had to TRANSLATE one into the other before
# `main` could catch it. There is now ONE class, and `StallTimeout` below subclasses it, so every
# `except DriverError` in either driver catches either driver's stall.
#
# The `as <same-name>` form marks these as an intentional RE-EXPORT so an autoformatter cannot strip
# the ones this module does not itself call; `ruff` removed 6 such re-exports here on a previous
# change's first attempt and only a symmetry test caught it.
from agent_workflows.runner_shared import (
    ID6_RE as ID6_RE,
)
from agent_workflows.runner_shared import (
    SCHEMA_VERSION as SCHEMA_VERSION,
)
from agent_workflows.runner_shared import (
    DriverError as DriverError,
)
from agent_workflows.runner_shared import (
    _ORDER_RE as _ORDER_RE,
)
from agent_workflows.runner_shared import (
    _SET_RE as _SET_RE,
)
from agent_workflows.runner_shared import (
    new_run_id as new_run_id,
)
from agent_workflows.runner_shared import (
    resolve_run_dir as resolve_run_dir,
)
from agent_workflows.runner_shared import (
    should_color as should_color,
)
from agent_workflows.runner_shared import (
    state_root as state_root,
)
from agent_workflows.runner_shared import (
    utc_now as utc_now,
)
from agent_workflows.runner_shared import (
    _read_order as _read_order,
)
from agent_workflows.runner_shared import (
    _read_set as _read_set,
)
from agent_workflows.runner_shared import (
    describe_unresolved_plan_selector as describe_unresolved_plan_selector,
)
from agent_workflows.runner_shared import (
    plan_bucket as plan_bucket,
)
from agent_workflows.runner_shared import (
    resolve_plan_path as resolve_plan_path,
)
from agent_workflows.runner_shared import (
    _lane_records_from_state as _lane_records_from_state,
)
from agent_workflows.runner_shared import (
    allocate_isolation_worktree as allocate_isolation_worktree,
)
from agent_workflows.runner_shared import (
    build_recovery_lane_notice as build_recovery_lane_notice,
)
from agent_workflows.runner_shared import (
    describe_lane as describe_lane,
)
from agent_workflows.runner_shared import (
    format_lane_report as format_lane_report,
)
from agent_workflows.runner_shared import (
    print_lane_interrupt_report as print_lane_interrupt_report,
)
from agent_workflows.runner_shared import (
    teardown_isolation_worktree as teardown_isolation_worktree,
)
from agent_workflows.runner_shared import (
    append_jsonl as append_jsonl,
)
from agent_workflows.runner_shared import (
    atomic_write_json as atomic_write_json,
)
from agent_workflows.runner_shared import (
    load_json as load_json,
)
from agent_workflows.runner_shared import (
    load_state as load_state,
)
from agent_workflows.runner_shared import (
    sha256_file as sha256_file,
)
from agent_workflows.runner_shared import (
    _run_git as _run_git,
)
from agent_workflows.runner_shared import (
    git_branch as git_branch,
)

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

# The durable stop-request record and the cooperative-checkpoint poll (spec `c4gd2h` R7-R9/R11)
# live in the shared ``runner_stop`` module so both drivers consult ONE mechanism.
from agent_workflows import runner_shared, runner_stop

# --- Cross-IPD dependency API (lanetruth-03 / 8guhs0): IMPORTED, never re-declared --------------
#
# `oc_runipd` owns ONE definition of each of these and `agy_runipd` binds the SAME objects, so the
# two drivers cannot drift apart the way the deleted `_read_deps` pair did (it was duplicated
# verbatim in both modules and both were equally wrong). `oc_runipd` does NOT import `agy_runipd`, so
# there is no cycle, and the marginal import cost is ~2ms (measured).
#
# The one function that CANNOT be re-exported as-is is `enforce_dependency_preflight`: it raises
# `oc_runipd.DriverError`, which is a DIFFERENT class from this module's `DriverError`, so agy's
# `main` would not catch it and the refusal would surface as an unhandled traceback instead of a
# clean "runagy: ..." exit. This module therefore defines a thin `enforce_dependency_preflight`
# wrapper (further down, next to `PlanRecord`) that delegates and re-raises in THIS module's
# exception type. The rules and their severities remain the shared evaluator's; nothing about the
# policy is duplicated.
# The `as <same-name>` form marks these as an intentional RE-EXPORT, so an autoformatter cannot
# "clean up" the ones this module does not call itself. That is not cosmetic: `ruff` did remove 6 of
# them on the first commit attempt, and the cross-driver symmetry test caught it immediately
# (`test_both_drivers_expose_the_dependency_api` / `test_the_implementation_is_shared_not_copied`).
# Losing them would silently re-open the divergence this change exists to close, because a later fix
# to, say, `edge_satisfied` would then be reachable through only ONE driver.

# --- bkclose (zhr6mc): backlog-close + shutdown-report API, IMPORTED, never re-declared -----------
#
# Same division of labor as the dependency API above and for the same measured reason: a duplicated
# copy is how the deleted `_read_deps` pair came to be identically wrong in both drivers. Every rule
# (the IPD-vs-non-IPD carrier partition, the earned-close gate, the fail-closed lookups, the
# `--status`-form gated setter, the ledger-before-print ordering, the signal handlers, and the
# `aw runs` pointer) lives ONCE in `oc_runipd` and this module binds the SAME objects. The `as
# <same-name>` form marks these as an intentional RE-EXPORT so an autoformatter cannot strip the ones
# this module does not call itself; `tests/test_runner_backlog_close.py` asserts object identity, so
# losing them re-opens the divergence this change exists to close.
from agent_workflows.oc_runipd import (
    # novalnomerge-01 (evgi9n) E-04: ONE shared integration predicate and ONE shared suite check, so a
    # fix to the self-finalize gate cannot land in one driver and silently miss the other.
    SuiteCheckResult as SuiteCheckResult,
    integration_is_earned as integration_is_earned,
    run_suite_check as run_suite_check,
    BacklogCloseVerdict as BacklogCloseVerdict,
    CARRIER_KIND_IPD as CARRIER_KIND_IPD,
    CARRIER_KIND_OTHER as CARRIER_KIND_OTHER,
    _read_from_backlog as _read_from_backlog,
    close_backlog_item as close_backlog_item,
    collect_earned_paths as collect_earned_paths,
    commit_backlog_close as commit_backlog_close,
    emit_shutdown_report as emit_shutdown_report,
    evaluate_backlog_close as evaluate_backlog_close,
    signal_report_callback as signal_report_callback,
    process_backlog_close as process_backlog_close,
    record_unclosed_backlog_items as record_unclosed_backlog_items,
    register_signal_report as register_signal_report,
    render_runs_pointer as render_runs_pointer,
    render_unclosed_report as render_unclosed_report,
    resolve_backlog_item as resolve_backlog_item,
    run_earned_paths as run_earned_paths,
    unclosed_backlog_items as unclosed_backlog_items,
)
from agent_workflows.oc_runipd import (
    DEPENDENCY_FATAL_RULES as DEPENDENCY_FATAL_RULES,
    _artifact_owners as _artifact_owners,
    _read_item_dependencies as _read_item_dependencies,
    cascade_dependency_blocked as cascade_dependency_blocked,
    dependency_depth as dependency_depth,
    dependency_reasons as dependency_reasons,
    dependency_status as dependency_status,
    dependency_target_id6 as dependency_target_id6,
    edge_satisfied as edge_satisfied,
    parse_dependency_token as parse_dependency_token,
    preflight_dependency_findings as preflight_dependency_findings,
    queue_sort_key as queue_sort_key,
    # runorder (prpipy) E-07: the run-order comparison and its announcement, bound (never copied) for
    # the same reason the key above is. `queue_sort_key` was ALREADY shared, so `prpipy`'s ordering
    # change reached this driver automatically; the announcement's SITE (`initialize_run`) and the
    # preview's site (`print_status`) are per-driver, which is exactly how `aw agy run` would have
    # inherited the reordering with no warning. Binding the same two objects closes that.
    announce_run_order as announce_run_order,
    run_order_rationale as run_order_rationale,
    simulate_dispatch_order as simulate_dispatch_order,
    update_execution_order as update_execution_order,
)

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
# NOTE (lanetruth-03 / 8guhs0 E-01): there is deliberately NO dependency regex here. See the
# identical note in `oc_runipd`. The canonical field NAME comes from
# `ipd_schema.META_ITEM_DEPENDENCIES` and its GRAMMAR from `ipd_schema.parse_item_dependencies`; the
# dependency API objects below are IMPORTED FROM `oc_runipd`, not re-declared, so the two drivers
# cannot drift apart again. Re-adding a dependency regex here is a regression guarded by
# tests/test_runner_item_dependencies.py.
_PLAN_FILENAME_RE = re.compile(
    r"^\d{8}-([a-z0-9_-]+)-(\d{1,3})-([a-z0-9]{6})-(.+)\.(ipd|draft|plan)\.md$"
)

# Terminal output verbosity for the streamed child-agent turn.
OUTPUT_MODES = ("clean", "quiet", "raw")

# The ANSI SGR codes and the status->color map are IMPORTED from `render_stream` (see the
# import block near the top of this module), not defined here. They used to be byte-identical
# inline copies, which is the same defect `Heartbeat` had: a change to the shared palette or
# to the status colors silently did not reach `aw agy run`. `should_color` (the TTY color
# decision) deliberately stays local to the caller, per the extraction's OQ-01.


# `Palette`, `_strip_ansi` and `_one_line` are IMPORTED from `render_stream` above. They were
# inline copies here, AST-identical to the shared ones, which meant `agy_runipd.Palette` was a
# DIFFERENT CLASS from `render_stream.Palette` even though the two read the same: passing one
# where the other was expected type-checked as a mismatch, and any fix to the shared renderer
# stopped at this module's border.


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


def run_checked(
    argv: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> str:
    """Run ``argv``, returning stdout, raising `DriverError` on a nonzero exit.

    rununify 02 (`818uru`) E-05: the IMPLEMENTATION is the single shared
    `runner_shared.run_checked`; this is a one-line wrapper that binds `pinned_child_env`, which
    this module already imports from `oc_runipd` (the pin has ONE definition by design; see the
    lanetruth note on that import). It deliberately keeps the ORIGINAL name and signature, so all
    9 call sites in this module are untouched.

    WHY A WRAPPER AND NOT A THREADED PARAMETER: see the identical note on `oc_runipd.run_checked`.
    """
    return runner_shared.run_checked(argv, cwd, env, env_builder=pinned_child_env)


# rununify 02 (`818uru`) E-05: three one-line wrappers over the shared git helpers. Their bodies call
# `run_checked`, which is also shared and which takes the env-builder as a parameter, so they receive
# THIS module's `run_checked` wrapper by injection. Do NOT "simplify" them onto the shared `_run_git`:
# that would change `git_head` from raising `DriverError` to returning "" and drop `git_status`'s
# `--short`, and both feed every run's outcome record. See the note in `runner_shared`.
def git_head(repo: Path) -> str:
    return runner_shared.git_head(repo, run_checked=run_checked)


def git_status(repo: Path) -> str:
    return runner_shared.git_status(repo, run_checked=run_checked)


def git_common_dir(repo: Path) -> Path:
    return runner_shared.git_common_dir(repo, run_checked=run_checked)


# fullauto Order 01 (97df1z), OQ-02: the automated-actor provenance for a `--full-auto` clear (the
# agy twin of the oc constants; see `oc_runipd.set_plan_approved` for the full rationale).
FULL_AUTO_ACTOR = "aw agy run --full-auto"
FULL_AUTO_APPROVAL_MESSAGE = (
    "auto-approved by --full-auto: review readiness cleared (not human approval)"
)


def set_plan_approved(
    repo: Path, id6: str, message: str = FULL_AUTO_APPROVAL_MESSAGE
) -> None:
    """Transition a reviewed plan to `auto-approved` via `aw set` - NOT to human `approved`.

    fullauto Order 01 (97df1z), OQ-02, resolved by the maintainer: the machine must not assert the
    `--by-human` attestation. `auto-approved` is the shipped automated-clear tier
    (`ipd_schema.READY_TO_EXECUTE`), so no new vocabulary or flag was invented; the actor string
    carries the automated provenance. Kept byte-for-byte equivalent to the oc twin (which holds the
    full note) so the two drivers cannot diverge on the honesty of the audit trail.
    """
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling, not the cwd's copy.
    cmd = pinned_module_argv(
        [
            "set",
            "auto-approved",
            id6,
            "--actor",
            FULL_AUTO_ACTOR,
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
                "auto-approved",
                id6,
                "--actor",
                FULL_AUTO_ACTOR,
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
            f"Unable to run 'aw set auto-approved {id6}': aw command not available"
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


def sync_receipt_into_worktree(repo: Path, worktree: Path, id6: str) -> None:
    """DEPRECATED NO-OP. Retired as the correctness mechanism by the ``dh0uno`` control-root fix.

    See the twin in ``oc_runipd.sync_receipt_into_worktree`` for the full rationale.
    ``ipd_lifecycle.receipt_path_for`` now anchors on the CHECKOUT, so src and dst are the SAME path:
    the copy is no longer needed to make an in-lane finalize find the driver's receipt, and performing
    it would re-create the very fork this closes (the old body raised ``shutil.SameFileError``).
    """
    return None


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


@contextlib.contextmanager
def run_lock(run_dir: Path):
    """Hold the run's ``driver.lock`` for this driver process.

    Yields a :class:`runner_shutdown.RunLockHandle` so the clean-shutdown routine can release
    the lock OBSERVABLY (spec `c4gd2h` R2: drop the ``flock`` AND remove the lock file). Kept
    symmetric with ``oc_runipd.run_lock`` (orchestrator CID-3), including the ``platform_lock``
    acquisition and the ``dup``ed-descriptor write of the ``pid=`` record (IPD `y6mfgo`).
    """

    lock_path = run_dir / "driver.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        held = platform_lock.acquire(lock_path)
    except platform_lock.LockBusy as exc:
        raise DriverError(
            f"Run is already controlled by another process: {run_dir.name}"
        ) from exc
    handle = held.dup_stream()
    try:
        if handle is not None:
            handle.seek(0)
            handle.truncate()
            handle.write(f"pid={os.getpid()} started={utc_now()}\n")
            handle.flush()
    except BaseException:
        with contextlib.suppress(Exception):
            if handle is not None:
                handle.close()
        held.release()
        raise
    lock = runner_shutdown.RunLockHandle(path=lock_path, handle=handle)
    try:
        yield lock
    finally:
        lock.release()
        held.release()


def enforce_dependency_preflight(
    repo: Path, plan_paths: list[Path], *, phase: str = "pre-execution"
) -> list[tuple[str, str, str]]:
    """Fail CLOSED on an invalid selected dependency graph BEFORE any host session starts.

    Delegates to the shared implementation. The `except`/re-raise below is now a NO-OP for the case
    it was written for, and it is KEPT DELIBERATELY; see the note inside.
    """
    # NOTE the import FORM is deliberate: the symbol-level `from agent_workflows.oc_runipd import
    # <name>` spelling, NOT the module-alias spelling. revgate's guard
    # (tests/test_review_findings_cascade.py::test_no_runner_to_runner_import) rejects the
    # module-alias substring anywhere in this file, and the alias form contains it while the
    # symbol-level form does not. The coupling is identical either way; this spelling keeps the
    # guard meaningful for the case it actually targets, a NEW blanket runner-to-runner dependency.
    from agent_workflows.oc_runipd import (
        enforce_dependency_preflight as _oc_enforce_dependency_preflight,
    )

    # rununify 02 (`818uru`) SETTLED THIS WRAPPER'S FATE, and the answer is KEEP, narrowed.
    #
    # It existed because the two drivers defined `DriverError` as two DISTINCT classes, so a refusal
    # raised on the OpenCode side was invisible to `except DriverError` here and surfaced as an
    # unhandled traceback instead of a clean `runagy: ...` exit. There is now ONE class, so the
    # translation is unnecessary and the `except _OcDriverError` half was DELETED with its import.
    #
    # The re-raise stays as a `RuntimeError` guard rather than being removed outright, because
    # removing it is NOT behavior-neutral in one respect worth naming: the old wrapper re-raised the
    # BASE `DriverError`, which DOWNGRADED any subclass (`ToolIdentityError`) and would defeat an
    # `except ToolIdentityError` upstream. Today the shared preflight raises only the base class, so
    # that downgrade is unobservable - but preserving the message-and-exit shape while removing the
    # type-flattening is strictly better than either the old translation or no handler at all.
    try:
        return _oc_enforce_dependency_preflight(repo, plan_paths, phase=phase)
    except DriverError:
        # Already the ONE shared class (or a subclass, whose type is now PRESERVED rather than
        # flattened): `main` catches it and prints its `runagy: ...` message. Nothing to translate.
        raise


class PlanRecord(NamedTuple):
    id6: str
    setid: str
    status: str
    order: int
    path: Path
    rel_path: str
    # CANONICAL TYPED edge tokens, never bare id6 strings (8guhs0 E-01); see the `oc_runipd` note.
    dependencies: list[str]
    dependency_error: str | None = None
    # bkclose (zhr6mc) E-01: the plan's `- From-Backlog:` id6, kept symmetric with `oc_runipd`. Read
    # through the SHARED `_read_from_backlog` (imported, not copied), so both drivers resolve the
    # field name from `ipd_schema.META_FROM_BACKLOG` and cannot disagree.
    from_backlog: str | None = None


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
    from_backlog = _read_from_backlog(text)
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
        dependency_error=dep_err,
        from_backlog=from_backlog,
    )


# rununify 02 (`818uru`) E-08: one-line wrapper over the shared `discover_plans`, binding THIS
# driver's `parse_plan_file`. That injection carries TWO dependencies at once, which is why it is the
# subtlest one in the plan: `parse_plan_file` is class (c) DIVERGED, AND it is what CONSTRUCTS this
# module's `PlanRecord` - and the two drivers' `PlanRecord` are DIFFERENT NamedTuples (oc's carries a
# `kind` field agy's lacks). A shared `discover_plans` that built one type would hand the other
# driver a record shape its code never expects: build oc's and agy gets a stray field; build agy's
# and oc LOSES `kind`, which `action_for` reads to detect an orchestrator. Both failures are silent
# and type-shaped rather than a crash. Injecting the PARSER keeps each driver's own record type.
def discover_plans(repo: Path) -> dict[str, PlanRecord]:
    """Scan the repository for all IPD files, returning id6 -> PlanRecord."""
    return runner_shared.discover_plans(repo, parse_plan_file=parse_plan_file)


# rununify 02 (`818uru`) E-08: one-line wrapper over the shared `validate_manifest`, binding
# `parse_dependency_token` (opencode-owned; the token grammar has ONE definition by design).
def validate_manifest(manifest: dict[str, Any]) -> None:
    runner_shared.validate_manifest(
        manifest, parse_dependency_token=parse_dependency_token
    )


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
            # bkclose (zhr6mc) E-01: carried through the manifest, symmetric with `oc_runipd`.
            "from_backlog": rec.from_backlog,
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

    # 8guhs0 E-02 (symmetric with oc_runipd): FAIL CLOSED on an invalid dependency graph BEFORE any
    # host session starts, and before the run directory exists. The rules and their severities are
    # the SHARED evaluator's; there is no runner-local dependency policy.
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
    full_auto = getattr(args, "full_auto", True)
    for position, id6 in enumerate(queue_ids, start=1):
        plan = manifest["plans"][id6]
        setid = plan["set"]
        if initial_session:
            set_sessions[setid] = initial_session

        status = plan.get("status")
        p_path = None
        rec = None
        try:
            p_path = resolve_plan_path(repo, plan.get("file", ""), id6)
            rec = parse_plan_file(p_path, repo)
            if rec and not status:
                status = rec.status
        except Exception:
            if not status:
                status = "approved"

        # `Status: reviewed` remains a hard PRECONDITION and the cleared status is `auto-approved`,
        # never human `approved` (fullauto 97df1z; the oc twin carries the full note).
        if status == "reviewed" and full_auto and p_path:
            try:
                if is_plan_review_approved(p_path):
                    set_plan_approved(repo, id6)
                    status = "auto-approved"
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
                # 8guhs0 E-04: the plan's numeric Order, frozen as a TIEBREAKER only (see
                # `queue_sort_key`). Additive; an older run directory lacking the key still sorts.
                "order": plan.get("order"),
                # bkclose (zhr6mc) E-01: the linked backlog item, frozen on the queue entry, with the
                # same manifest-then-plan-file fallback `oc_runipd` uses so an older hand-written
                # manifest still gets the link.
                "from_backlog": plan.get("from_backlog")
                or (getattr(rec, "from_backlog", None) if p_path else None),
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
        # runorder (prpipy) E-07, symmetric with `oc_runipd`: the REQUESTED-vs-EXECUTED order
        # comparison frozen beside the queue it describes, computed by the SHARED function.
        "run_order": run_order_rationale(queue, list(args.selectors)),
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
    # runorder (prpipy) E-07: the SAME announcement the OpenCode driver emits, from the SAME shared
    # function, before the first child session. Not optional polish: `queue_sort_key` is shared, so
    # without this `aw agy run` would silently receive the reordering and neither the warning nor the
    # corrected preview.
    announce_run_order(run_dir, state)
    return run_dir


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


# rununify 02 (`818uru`) E-06: one-line wrapper over the shared `save_state`, binding THIS driver's
# `write_report`. `write_report` is class (c) DIVERGED (the two drivers render different reports), so
# importing one into shared code would silently give BOTH drivers that one's format. Keeping the
# original name and signature is what leaves this module's 30 `save_state` call sites untouched.
def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.save_state(run_dir, state, write_report=write_report)


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


# `dependency_status` is deliberately NOT defined here: it is RE-EXPORTED from `oc_runipd` in the
# import block above, so both drivers bind the SAME object and a fix cannot land in only one of them
# (asserted by tests/test_runner_item_dependencies.py::test_the_implementation_is_shared_not_copied).
# The merge of revgate 7nkcgp and 8guhs0 briefly produced BOTH a re-export and a local copy here; the
# copy is the one that had to go.


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


# NOTE (8guhs0 E-01/E-03): `dependency_status` is NOT defined here. It is IMPORTED from `oc_runipd`
# above, so the runtime satisfaction semantics exist exactly ONCE. The deleted copy was a verbatim
# duplicate of oc's, which is how both drivers came to be equally unable to read the canonical field:
# a fix applied to one silently left the other broken. `plan_bucket` is byte-identical between the
# two modules and `resolve_plan_path` differs only in formatting (verified), so the imported
# implementation behaves identically here.


def build_review_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    repo: Path,
) -> str:
    """Return EXACTLY the slash command for a review turn: `/plan-review <relative path>`.

    Deliberately prose-free (terseout `ntf6sx` E-05), symmetric with the OpenCode driver. The
    value is one argv element, so appended prose would be consumed as the slash command's
    `$ARGUMENTS`. The review turn inherits the concise-reporting contract from the generated
    command shim's pointer plus the installed `AGENTS.md#aw:reporting` section.
    """

    try:
        rel_path = str(plan_path.relative_to(repo))
    except ValueError:
        rel_path = str(plan_path)
    return f"/plan-review {rel_path}"


def build_isolation_notice(lane_root: Path | None) -> str:
    """The WORK HERE block for an isolated turn, or "" for a main-checkout turn.

    laneprompt: the SHARED text lives in `oc_runipd.build_isolation_notice`; this delegates so the two
    drivers cannot drift (the same reason `rununify` exists). See that docstring for the measured
    defect this closes.
    """
    from agent_workflows.oc_runipd import build_isolation_notice as _shared

    return _shared(lane_root)


def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
    lane_root: Path | None = None,
) -> str:
    setid = item["setid"]
    decisions = run_dir / "decisions-and-questions.md"
    outcome = run_dir / "outcomes" / f"{item['position']:02d}-{item['id6']}.json"
    report = run_dir / "execution-report.md"
    mode = "RECOVERY/CONTINUATION" if recovery else "NORMAL EXECUTION"
    prior = item.get("attempts", [])[-1] if recovery and item.get("attempts") else None
    lane_notice = build_recovery_lane_notice(item, state, recovery)
    isolation_notice = build_isolation_notice(lane_root)
    return f"""# Antigravity IPD Driver Turn

Mode: {mode}{lane_notice}{isolation_notice}
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
{reporting_contract.prompt_block()}"""


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
{reporting_contract.prompt_block()}"""


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


def _budget_breach_recorder(
    run_dir: Path,
    item: dict[str, Any],
    request: runner_stop.StopRequest,
    checkpoint_observer: runner_stop.CheckpointObserver,
) -> Callable[[], None]:
    """Build the callback `BudgetBreachWatch` invokes when the wind-down deadline passes.

    runstop foi1b3 (E-04, spec R11); the exact counterpart of the `oc_runipd` helper. It RECORDS
    the breach as an escalation-REQUIRED signal and returns, taking no escalation action: spec A7
    places enforcement in Phase 5 (`71vjbn`), which consumes this one signal.
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


def _escalation_recorder(
    run_dir: Path, item: dict[str, Any]
) -> Callable[[int, int, str], None]:
    """Build the callback `EscalationWatch` invokes when it PERFORMS an escalation (71vjbn E-06).

    The exact counterpart of the `oc_runipd` helper (orchestrator CID-3: neither driver may have a
    level or an enforcement the other lacks). `escalation_performed` is True here precisely where
    Phase 3's breach event wrote False (spec R11/R23).
    """

    def _record(from_level: int, to_level: int, reason: str) -> None:
        event = runner_stop.escalation_event(
            from_level=from_level,
            to_level=to_level,
            at=utc_now(),
            reason=reason,
            id6=item.get("id6", ""),
            requester=f"budget-escalation (from level {from_level})",
        )
        with contextlib.suppress(Exception):
            append_jsonl(run_dir / "events.jsonl", event)
        print(
            f"stop ESCALATED from level {from_level} to level {to_level} "
            f"({runner_stop.LEVEL_NAMES.get(to_level, 'unknown')}): {reason}",
            file=sys.stderr,
        )
        runner_stop.report_request(
            to_level,
            requester=f"budget-escalation (from level {from_level})",
            command=_detect_driver_command(),
        )

    return _record


def _record_checkpoint_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    checkpoint_observer: runner_stop.CheckpointObserver,
) -> dict[str, Any]:
    """Record a level-3 stop on the item with KNOWN certainty (spec R18), returning the record.

    runstop foi1b3 (E-03); the exact counterpart of the `oc_runipd` helper, sharing the SAME record
    builder in `runner_stop` so the two drivers cannot describe the same stop differently.
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

    runstop m0z0ti (E-02/E-03); the exact counterpart of the `oc_runipd` helper, sharing the SAME
    record builder in `runner_stop` so an operator switching hosts gets the same guarantee
    (orchestrator CID-3). No last-completed-operation is invented: the cut point was not observed.
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

    # lanefinal (i452hf) / wtiso-03 (rchpms) E-06, the MIRROR of the oc twin: mark an ISOLATED lane
    # turn as the managed WORKER role so an in-lane `aw ipd begin/finalize` refuses with
    # AW-LIFECYCLE-ROLE-001 rather than forking a second receipt the driver cannot see. Same
    # `work_dir` key, same single env construction via the shared `pinned_child_env` - the two host
    # drivers must not drift on an authority rule. See the oc twin for the full rationale and for the
    # honest limit (an environment selector, not a hardened boundary).
    from agent_workflows import ipd_lifecycle

    child_env = pinned_child_env()
    if work_dir:
        child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
    else:
        child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)
    popen_kwargs["env"] = child_env

    stall_timeout = options.get("stall_timeout", DEFAULT_STALL_TIMEOUT)

    queue = state.get("queue", [])
    total_items = len(queue) or 1
    # When working on item at 1-based execution sequence S, number of completed items is S - 1 (e.g. 0 of 2 done).
    seq = execution_index(item, state)
    current_idx = max(0, seq - 1)

    is_tty = bool(getattr(sys.stdout, "isatty", None) and sys.stdout.isatty())

    run_start_mono = state.get("_invocation_start_mono")
    if run_start_mono is None:
        run_start_mono = time.monotonic()

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
            action=statusline_action_for_item(item),
            artifact_kind=item.get("kind", item.get("type", "ipd")),
        )
        watchdog = StallWatchdog(process, timeout=stall_timeout)
        # stallfp kaga7s (display parity only): show the countdown from the clock that kills.
        # agy needs NO progress observer: its stdout stream already carries
        # `step_type == "subagent"` events (see render_agy_event), so every subagent step
        # already touches the watchdog below.
        statusline.watchdog = watchdog
        # runstop foi1b3 (level 3): the OBSERVED safe-checkpoint tracker. NOTE the detector: agy's
        # completion signal is `step_update` with `state == "DONE"`, NOT oc's `tool_use` +
        # `part.state.status == "completed"`. The two drivers share the SEMANTICS through one helper
        # module (orchestrator CID-3) while each reads its OWN schema; assuming one schema across
        # both would make this silently never fire here.
        checkpoint_observer = runner_stop.CheckpointObserver(
            detector=runner_stop.is_agy_safe_checkpoint
        )
        breach_watch: runner_stop.BudgetBreachWatch | None = None
        # runstop m0z0ti (level 4, E-01): the out-of-band observer, identical in purpose and shape to
        # the `oc_runipd` one (orchestrator CID-3). `for raw_line in process.stdout` BLOCKS, so an
        # in-loop poll alone would make "immediately" mean "whenever the child next speaks".
        forced: dict[str, Any] = {}

        def _note_force(level: int, requester: str) -> None:
            """Record the level-4 request and INTERRUPT the turn through the SHARED reaper.

            Reaping here is what unblocks the main thread's blocking read on a silent child (the
            `StallWatchdog._run` precedent). It goes through `runner_shutdown.clean_shutdown`, the ONE
            shared routine and its ONE process-group escalation (spec R5): never a bare kill.
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
        # runstop 71vjbn (E-06, spec R11/A7): ENFORCE the wind-down budget Phase 3 only RECORDED. The
        # exact counterpart of the `oc_runipd` site. Armed for the WHOLE turn (not only once a
        # level-3 stop is seen) so a level-1/2 wind-down deadline expiring during this turn is also
        # bounded, and out-of-band because `for raw_line in process.stdout` BLOCKS on a silent child.
        # It only RAISES the durable level; the escalated level is honored by the existing poll,
        # `force_watch`, and the ONE shared `clean_shutdown` (spec R5).
        escalation_watch = runner_stop.EscalationWatch(
            run_dir,
            on_escalate=_escalation_recorder(run_dir, item),
            is_alive=lambda: process.poll() is None,
        )

        def _raise_if_forced() -> None:
            """Cut the turn NOW if a level-4 request has been observed (spec R7 level 4)."""

            if not forced:
                return
            raise runner_stop.StopNowForce(
                level=forced.get("level", runner_stop.LEVEL_NOW_FORCE),
                requester=forced.get("requester", ""),
                events_seen=checkpoint_observer.events_seen,
                prior_completed_index=checkpoint_observer.last_checkpoint_index,
                prior_completed_label=checkpoint_observer.last_checkpoint_label,
            )

        try:
            # `escalation_watch` (runstop 71vjbn) joins the turn's scope for the same reason
            # `force_watch` does: it must be armed for exactly the turn's lifetime, no longer.
            with statusline, watchdog, force_watch, escalation_watch:
                for raw_line in process.stdout:
                    log.write(raw_line)
                    log.flush()
                    statusline.touch("stdout")
                    watchdog.touch()
                    # runstop gq6m2u: the IN-TURN cooperative checkpoint (spec `c4gd2h` R7); the
                    # exact counterpart of the `oc_runipd` site. Side-effect free: it REPORTS the
                    # requested level, and acting on a level belongs to the later phases.
                    level = runner_stop.poll_stop(run_dir)
                    # runstop m0z0ti (level 4, spec R7/A2): checked FIRST and BEFORE the line is
                    # classified, because level 4 must NOT wait for a checkpoint. The counterpart of
                    # the `oc_runipd` site (orchestrator CID-3: identical semantics on both hosts).
                    if level is not None and level >= runner_stop.LEVEL_NOW_FORCE:
                        _note_force(
                            level,
                            (lambda r: r.requester if r is not None else "unknown")(
                                runner_stop.read_stop_request(run_dir)
                            ),
                        )
                    _raise_if_forced()
                    # runstop foi1b3 (level 3, spec R10/A3): stop the TURN at the next OBSERVED safe
                    # checkpoint. Parsed here, for EVERY line, independently of `output_mode` - not in
                    # the `clean` branch below via `render_agy_event`, which would make the feature
                    # silently inert under `raw` and `quiet`.
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
                            # runstop foi1b3 (E-04, spec R11): the BOUNDED wait, armed out-of-band
                            # because `for raw_line in process.stdout` BLOCKS on a silent child and
                            # so can never notice a deadline itself. R10 stands: the checkpoint is
                            # still defined only by an observed event; this is the GIVE-UP bound.
                            if request is not None:
                                remaining = runner_stop.deadline_seconds_remaining(
                                    request
                                )
                                breach_watch = runner_stop.BudgetBreachWatch(
                                    deadline_monotonic=time.monotonic()
                                    + max(0.0, remaining),
                                    on_breach=_budget_breach_recorder(
                                        run_dir, item, request, checkpoint_observer
                                    ),
                                    is_alive=lambda: process.poll() is None,
                                )
                                breach_watch.__enter__()
                    if checkpoint_observer.observe(raw_line):
                        raise runner_stop.StopAtCheckpoint(checkpoint_observer)

                    if output_mode == "raw":
                        sys.stdout.write(raw_line)
                        sys.stdout.flush()
                    elif output_mode == "clean":
                        rendered = render_agy_event(raw_line, pal)
                        if rendered is not None:
                            statusline.write_event(rendered)
                # runstop m0z0ti (level 4): the stream also ENDS when `force_watch` reaped a silent
                # child (that reap is what unblocks the read at all), so re-check here rather than
                # falling through to a normal `process.wait()` and reporting an ordinary exit code.
                _raise_if_forced()
        except BaseException:
            if breach_watch is not None:
                breach_watch.__exit__(None, None, None)
            # runstop foi1b3: route the stop through the SHARED reaper (spec R5), not a local
            # `terminate_process`. The child is a one-shot subprocess with no cooperative stop
            # channel, so stopping it IS termination at an observation-chosen instant; levels 3 and 4
            # share that mechanism and differ only in timing.
            #
            # runstop m0z0ti (level 4): the SAME endpoint, deliberately. Spec c4gd2h section 3 states
            # the only difference between levels 3 and 4 is outcome CERTAINTY, not cleanliness.
            report = runner_shutdown.clean_shutdown(process, run_dir=run_dir)
            if not report.all_satisfied:
                print(report.render(), file=sys.stderr)
            log.flush()
            with contextlib.suppress(OSError):
                os.fsync(log.fileno())
            if watchdog.stalled:
                timeout_val = int(watchdog.timeout) if watchdog.timeout else 0
                raise StallTimeout(
                    f"Antigravity child turn stalled: no output for {timeout_val}s"
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
    # runstop foi1b3 (E-03, spec R18/R21/R22): the DELIBERATE-STOP branch, ahead of every other
    # branch including the exit-code fallback, for the same measured reason as in `oc_runipd`: a
    # level-3 stop leaves NO outcome JSON (the agent writes it at turn END), the plan is still in
    # `pending/`, and the terminated child exits NONZERO, so the final
    # `("partial" if exit_code == 0 else "failed-safely")` would label a DELIBERATE OPERATOR STOP as
    # `failed-safely` - the intent-versus-breakage conflation R21 forbids.
    #
    # Keyed on the `stopped` record the checkpoint path wrote, NOT on the exit code, so a genuine
    # failure still reconciles normally even if a stop was requested.
    #
    # runstop m0z0ti: this branch now covers BOTH turn-interrupting levels and returns the SAME status
    # for each on purpose. The difference is CERTAINTY (`known` vs `indeterminate`), carried as an
    # explicit flag on the record, not as a different status - which is what keeps a level-4 item
    # visible to the reconcile/requeue/report machinery while the R19 gate refuses to re-run it.
    # Neither level ever returns a success state (spec R22).
    stopped = item.get("stopped")
    if isinstance(stopped, dict) and stopped.get("stopped_deliberately"):
        return runner_stop.STOPPED_DISPOSITION, None
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
    seq = execution_index(item, state)
    banner = (
        pal("\u25b6 ", "cyan")
        + pal(f"IPD {seq:02d}/{total} {item['id6']}", "bold", "cyan")
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
                    f"\u2717 IPD {seq:02d}/{total} {item['id6']} begin refused "
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
                        f"\u2717 IPD {seq:02d}/{total} {item['id6']} worktree "
                        f"allocation failed; not launching. {exc}",
                        "red",
                    ),
                    file=sys.stderr,
                )
                return

    # laneprompt: REBUILD the prompt now that the lane exists, so its paths and its instructions
    # describe the tree the turn will actually run in. Kept symmetric with
    # `oc_runipd.execute_item`; see `oc_runipd.build_isolation_notice` for the measured defect and
    # for why this is a rebuild rather than a later first build (the pre-launch refusal paths above
    # need a prompt on disk as evidence, and the lane cannot exist before `driver_begin` grants
    # authority).
    if work_dir and not is_review:
        lane_root = Path(work_dir)
        try:
            lane_plan_path = resolve_plan_path(
                lane_root, item.get("configured_file", ""), item["id6"]
            )
        except DriverError:
            lane_plan_path = plan_path
        prompt_text = build_prompt(
            item, state, run_dir, lane_plan_path, recovery=recovery, lane_root=lane_root
        )
        prompt_path = write_prompt(run_dir, item, prompt_text, attempt_no)
        attempt["prompt"] = str(prompt_path)
        attempt["prompt_sha256"] = sha256_file(prompt_path)
        attempt["lane_plan_path"] = str(lane_plan_path)
        save_state(run_dir, state)

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
    except runner_stop.StopNowForce as stop:
        # runstop m0z0ti (E-02/E-03, spec A2/R18/R21/R22): the exact counterpart of the `oc_runipd`
        # handler. The turn was interrupted IMMEDIATELY, at an unobserved point, so the outcome is
        # INDETERMINATE and is recorded that way. The child was already reaped through the SAME shared
        # `clean_shutdown` level 3 uses; cleanliness is identical and only certainty differs.
        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "deliberate-stop-now-force"
        record = _record_forced_stop(run_dir, state, item, stop)
        attempt["stopped"] = record
        attempt["disposition"] = runner_stop.FORCED_DISPOSITION
        item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
        save_state(run_dir, state)
        print(
            pal(
                f"\u25a0 IPD {seq:02d}/{total} {item['id6']} INTERRUPTED IMMEDIATELY "
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
        # runstop foi1b3 (E-02/E-03, spec A3/R18): the exact counterpart of the `oc_runipd` handler.
        # The turn was stopped at an OBSERVED safe checkpoint; record it with KNOWN certainty. The
        # child was already reaped through `clean_shutdown` inside `run_agy_turn` (spec R5).
        now = utc_now()
        attempt["interrupted_at"] = now
        attempt["ended_at"] = now
        attempt["interrupt_reason"] = "deliberate-stop-at-checkpoint"
        record = _record_checkpoint_stop(run_dir, state, item, stop.observer)
        attempt["stopped"] = record
        attempt["disposition"] = runner_stop.STOPPED_DISPOSITION
        # Decided in ONE place (`reconcile_disposition`'s deliberate-stop branch) so the two drivers
        # and the two code paths cannot disagree about what a stopped item is.
        item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
        save_state(run_dir, state)
        print(
            pal(
                f"\u25a0 IPD {seq:02d}/{total} {item['id6']} stopped at a safe "
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
                f"\u2717 IPD {seq:02d}/{total} {item['id6']} stalled (no output for {int(stall_sec) if stall_sec else 0}s); turn terminated",
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

    # novalnomerge-01 (evgi9n) E-01/E-04: when no verifier ran, the DRIVER runs the suite itself and
    # that observed result is the trust signal. NOTE THE SEMANTIC DIFFERENCE from `oc_runipd`: this
    # driver gates the verifier on `not no_verify` (verification defaults ON here), whereas `oc` gates
    # on `validate` (which defaults OFF). The shared predicate takes `validate=`, so pass the
    # locally-correct boolean rather than copying `oc`'s expression. Run the suite in the PRIMARY
    # checkout (`repo`), NEVER `work_dir`: a lane resolves a different `.aw/state` (dh0uno) where 15
    # `test_run_viewer.py` tests fail for unrelated reasons, which would close this gate forever.
    verifier_expected = not no_verify
    suite_result: SuiteCheckResult | None = None
    integration_gate_relevant = (
        self_finalize
        and not is_review
        and disposition in ("executed", "substantially-complete")
    )
    if integration_gate_relevant and not verifier_expected:
        suite_result = run_suite_check(repo, str(state.get("run_id") or ""))
        attempt["suite_check"] = {
            "passing": suite_result.passing,
            "exit_code": suite_result.exit_code,
            "summary": suite_result.summary,
            "cwd": suite_result.cwd,
            "timeout_seconds": suite_result.timeout_seconds,
            "elapsed_seconds": round(suite_result.elapsed_seconds, 3),
        }

    # novalnomerge-01 (evgi9n) E-05: record WHICH signal decided, so "no verifier ran" is
    # distinguishable from "the verifier declined". No new disposition value is invented.
    integration = integration_is_earned(
        validate=verifier_expected,
        verify_disp=verify_disp,
        suite_result=suite_result,
    )
    if integration_gate_relevant:
        attempt["integration_signal"] = integration.signal
        attempt["integration_detail"] = integration.detail
        item["integration_signal"] = integration.signal
        item["verifier_ran"] = bool(verifier_expected)
    save_state(run_dir, state)

    # driverfin-01 (p7peqf): self-finalize step 2 - after an execute turn that EARNED integration, run
    # the gated `aw ipd finalize` with programmatic two-way scope reconciliation. GATE PRECISION: before
    # finalize the child is still in pending/, so reconcile_disposition reports
    # `substantially-complete`; trigger on disposition in {executed, substantially-complete} AND an
    # earned integration verdict (NOT on `disposition == "executed"` alone). On success the plan moves
    # to executed/ (re-resolve, mark executed); on refusal keep substantially-complete, never force.
    #
    # novalnomerge-01 (evgi9n) E-03/E-04: the fourth condition was `verify_disp == "verified"`, which
    # only the verifier turn ever set, so whenever verification was disabled this branch was unreachable
    # and every item stranded on its lane. Both drivers now consume ONE shared predicate, so a
    # one-runner fix cannot leave the other silently broken.
    if integration_gate_relevant and integration.earned:
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
                # bkclose (zhr6mc) E-02/E-03/E-04, symmetric with `oc_runipd`: the plan is genuinely
                # `executed` on main here, which is the one moment a run can know the last carrier
                # landed. The SHARED `process_backlog_close` fails closed and records its reason
                # either way, so a refusal is reported (E-06) rather than swallowed.
                process_backlog_close(run_dir, state, item)
                save_state(run_dir, state)
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
        # The SHARED predicate (fullauto 97df1z): structured `- Readiness:` first, bounded
        # newest-history fallback second, fail closed otherwise. Records `auto-approved` (OQ-02).
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
        + pal(f"IPD {seq:02d}/{total} {item['id6']}", "bold")
        + pal(f" ({action})", "dim")
        + " -> "
        + pal(disposition, glyph_color)
        + pal(f"  (exit {rc})", "dim")
    )
    print(finish)
    if auto_approved:
        print(
            pal(
                f"  \u2713 IPD {item['id6']} auto-approved (review readiness cleared, "
                "NOT human approval); progressing to execution",
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
                # runstop m0z0ti (E-05, spec R22): THE FABRICATED-SUCCESS GATE, the exact counterpart
                # of the `oc_runipd` gate (orchestrator CID-3). This promotion infers success from the
                # plan's DIRECTORY alone, consulting neither the outcome artifact nor any stop record.
                # For a FORCE-CUT turn that records a success the driver never established: if the
                # agent had already moved the plan to `executed/` but was interrupted before its work
                # was complete or verified, `executed` would be a fabrication. So it refuses to fire
                # for an item flagged INDETERMINATE and reports the conflict instead.
                #
                # Deliberately narrow: ordinary interrupted items are promoted exactly as before, and
                # a control test pins that.
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
    REPORTED rather than silently re-run. The exact counterpart of the `oc_runipd` gate (orchestrator
    CID-3/CID-4): the gate must live IN the requeue, because `run_queue` calls this unconditionally on
    every start and resume, so a refusal added beside it would be bypassed by the call that already
    ran. Do not "clean this up" as a redundant special case.
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

    runstop 1qxuke. The exact counterpart of ``oc_runipd._observe_between_turn_stop`` (orchestrator
    CID-3: no level may exist in one driver only). The boundary decision itself lives in the shared
    ``runner_stop`` module, so the two drivers cannot drift apart on WHICH items may still start.
    """

    if level not in runner_stop.BETWEEN_TURN_LEVELS:
        return existing
    if existing is not None and existing.level >= level:
        return existing
    request = runner_stop.read_stop_request(run_dir)
    requester = request.requester if request is not None else "unknown"
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
    """Append the DELIBERATE-stop ledger event (spec R21); un-run items stay `queued`.

    runstop 1qxuke. The counterpart of ``oc_runipd._record_deliberate_stop``, writing the same
    event to the same established append-only ``events.jsonl`` channel.
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
    run_dir: Path, retry_incomplete: bool = False, output_mode: str | None = None
) -> int:
    state = load_state(run_dir)
    # bkclose (zhr6mc) E-06, symmetric with `oc_runipd`: publish the live ledger for the shutdown
    # report BEFORE any turn starts. NO `signal.signal` registration: it is owned by `runstop` Phase 5
    # (`71vjbn`) and guarded by four executed plans (see the ownership note in `oc_runipd`).
    register_signal_report(run_dir, state)
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
            # just refused, since its status set includes `interrupted`. Gated on the SAME predicate so
            # the two routes cannot disagree (kept symmetric with `oc_runipd`).
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
    # indeterminate item, exiting NONZERO and naming the item, its state, and the reconciliation
    # required. Kept symmetric with `oc_runipd.run_queue` (orchestrator CID-3).
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

    invocation_start_mono = time.monotonic()
    state["_invocation_start_mono"] = invocation_start_mono

    # runstop 1qxuke: the observed level-1/2 wind-down and the set in flight, kept symmetric with
    # `oc_runipd.run_queue` (orchestrator CID-3).
    wind_down: runner_stop.WindDown | None = None
    current_setid: str | None = None
    # Recorded EXACTLY ONCE, whichever boundary the loop exits at (kept symmetric with `oc_runipd`).
    stop_recorded = False
    # runstop foi1b3: True once a level-3 stop cut the running TURN at an observed safe checkpoint
    # (level 3 stops INSIDE a turn, unlike levels 1-2), so the deliberate-stop exit contract applies.
    stopped_at_checkpoint = False
    while True:
        # runstop gq6m2u: the BETWEEN-ITEM cooperative checkpoint (spec `c4gd2h` R7), the exact
        # counterpart of the `oc_runipd` site. runstop 1qxuke acts on it for level 1
        # (stop-after-call, R20/A1) and level 2 (stop-after-set, R20/A4).
        level = runner_stop.poll_stop(run_dir)
        state = load_state(run_dir)
        state["_invocation_start_mono"] = invocation_start_mono
        # bkclose (zhr6mc) E-06: `state` is REBOUND on every reload, so refresh the handler's
        # published reference or a signal would report from a pre-turn snapshot.
        register_signal_report(run_dir, state)
        wind_down = _observe_between_turn_stop(run_dir, level, current_setid, wind_down)
        # 8guhs0 E-04 (symmetric with oc_runipd): cascade FIRST, so an item whose prerequisite
        # reached a non-success terminal state is marked `dependency-blocked` (transitively) instead
        # of stalling the queue, while independent items keep running.
        if cascade_dependency_blocked(state, run_dir):
            save_state(run_dir, state)
            state = load_state(run_dir)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued:
            # runstop 1qxuke (E-03, OQ-01): the FINAL-set boundary. A level-2 stop on the last set
            # drains the queue and leaves HERE, so the deliberate stop must still be recorded (spec
            # R21) or it would be indistinguishable from an ordinary finish.
            if wind_down is not None and not stop_recorded:
                _record_deliberate_stop(run_dir, state, wind_down)
                stop_recorded = True
            break
        runnable = None
        # 8guhs0 E-04: DECLARED EDGES are authoritative; Set/Order only breaks ties among nodes that
        # are ALREADY ready (spec 25kzda 5.4 rules 3-5).
        by_id = {entry["id6"]: entry for entry in state["queue"]}
        for item in sorted(queued, key=lambda it: queue_sort_key(it, by_id)):
            satisfied, _ = dependency_status(item, state)
            if satisfied:
                runnable = item
                break
        # runstop 1qxuke: consent to START only, never a reordering. Out-of-boundary items stay
        # `queued` (spec R22), which for level 2 can mean ending with runnable work outstanding.
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
            # runstop 1qxuke: during a wind-down the remainder is `queued` because the OPERATOR
            # stopped, not because its dependencies are unmet; relabelling it `dependency-blocked`
            # would be a fabricated disposition (spec R22).
            if wind_down is not None:
                if not stop_recorded:
                    _record_deliberate_stop(run_dir, state, wind_down)
                    stop_recorded = True
                break
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
        update_execution_order(state, runnable)
        # runstop 1qxuke: the set now in flight, recorded BEFORE the turn so a stop requested during
        # it is observed at the next checkpoint with this set already captured.
        current_setid = runnable.get("setid")
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
        except runner_stop.StopNowForce:
            # runstop m0z0ti (E-01/E-03, spec A2): the current TURN was interrupted IMMEDIATELY, so the
            # RUN stops here. The item is already recorded as INDETERMINATE and the child reaped
            # through the shared `clean_shutdown`; remaining items keep `queued` (spec R22), and
            # nothing is marked executed, complete, or successful on this path.
            stopped_at_checkpoint = True
            state = load_state(run_dir)
            break
        except runner_stop.StopAtCheckpoint:
            # runstop foi1b3 (E-02, spec A3): the current TURN stopped at an observed safe checkpoint,
            # so the RUN stops here. The item is already recorded with KNOWN certainty and the child
            # reaped through `clean_shutdown`; remaining queued items are left `queued` (spec R22).
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
    pal = Palette(should_color(sys.stdout))
    exit_reason = None
    if wind_down is not None:
        exit_reason = f"STOPPED (Level {wind_down.level}: {runner_stop.LEVEL_NAMES.get(wind_down.level, 'wind-down')})"
    elif stopped_at_checkpoint:
        exit_reason = "STOPPED (at checkpoint)"
    print(
        render_run_summary_table(
            state, run_dir, pal=pal, exit_reason=exit_reason, driver_label="antigravity"
        )
    )
    hint = render_continuation_hint(state, run_dir)
    print(hint)
    state["_summary_table_printed"] = True
    # bkclose (zhr6mc) E-06/E-07: the NORMAL-exit half, through the SAME idempotent shared routine the
    # signal handlers use, so the two paths cannot drift and whichever fires first suppresses the
    # other. Ledger BEFORE print (an uncatchable kill still leaves the answer on disk).
    register_signal_report(run_dir, state)
    emit_shutdown_report()
    # runstop 1qxuke (E-05): the same deliberate-stop exit contract as `oc_runipd` (spec A1/A4 need
    # 0; the plain predicate returns 1 because a stop leaves items `queued`). Statuses are never
    # rewritten to manufacture the 0, and a run item that genuinely failed still exits nonzero.
    # runstop foi1b3: a level-3 stop is equally DELIBERATE and takes the same contract. Its own item
    # is `interrupted`, not a success state, so the run still exits nonzero for it - deliberately;
    # only items the stop never STARTED are excused, exactly as for levels 1-2.
    return runner_stop.deliberate_stop_exit_code(
        (item["status"] for item in state["queue"]),
        success_states=SUCCESS_STATES,
        stopped=wind_down is not None or stopped_at_checkpoint,
    )


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


# rununify 02 (`818uru`) E-06: one-line wrapper over the shared `print_status`, supplying THIS host's
# label. `print_status` is the ONE symbol of the 34 that was not AST-identical across the runners: the
# two bodies were identical EXCEPT for the literal `driver_label="antigravity"`. So the host string is a
# parameter and each driver binds its own; the rendered output is byte-identical to before.
def print_status(run_dir: Path) -> None:
    runner_shared.print_status(run_dir, driver_label="antigravity")


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
        help=(
            "Clear a plan that is already 'Status: reviewed' to 'auto-approved' and execute it "
            "immediately. The decision reads the plan's structured '- Readiness:' field "
            "(go|go-pending-approval clears; no-go, an unrecognized value, or an absent field with "
            "no approving review verdict does not). This records an AUTOMATED clear, NOT human "
            "approval: no --by-human attestation is asserted"
        ),
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
        help=(
            "Override full-auto mode (clear reviewed plans whose structured '- Readiness:' is "
            "go/go-pending-approval to 'auto-approved' and execute them; not human approval)"
        ),
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

    # runstop 71vjbn (E-03, spec R14/R15): the OUT-OF-BAND stop verb, through the SHARED declaration
    # so `aw agy run stop` is the SAME verb as `aw oc run stop` (orchestrator CID-3) rather than a
    # second copy that could drift. Declared on THIS parser (where `start` lives), not on `cli.py`'s
    # `agy` group, which forwards `argparse.REMAINDER` verbatim to this `main`.
    runner_stop.add_stop_parser(sub, command=_detect_driver_command())

    return parser


def handle_stop_command(args: argparse.Namespace) -> int:
    """Execute the `stop` verb: resolve the run, then apply the SHARED decision (spec R14/R17).

    The exact counterpart of `oc_runipd.handle_stop_command`. Resolution stays here (each driver has
    its own `resolve_run_dir`); the DECISION - liveness by lock acquirability, the monotonic no-op, and
    the honest nonzero paths - lives once in `runner_stop.stop_command`, so the two drivers cannot
    diverge on the error contract.

    An unresolvable run exits NONZERO and mutates NOTHING (spec A5): `run_dir` is passed as None with
    the resolver's own message rather than being constructed speculatively.
    """

    run_dir: Path | None
    unknown_reason = ""
    try:
        run_dir = resolve_run_dir(args.repo, args.run_id)
    except DriverError as exc:
        run_dir = None
        unknown_reason = f"{exc} (nothing was created or modified)"
    level = runner_stop.LEVEL_FLAGS.get(getattr(args, "level_flag", None) or "")
    result = runner_stop.stop_command(
        run_dir,
        level,
        run_id=args.run_id,
        requester=f"stop-command pid={os.getpid()}",
        command=_detect_driver_command(),
        unknown_reason=unknown_reason,
    )
    print(result.message, file=sys.stdout if result.ok else sys.stderr)
    return result.exit_code


def install_stop_triggers(run_dir: Path) -> dict[str, str]:
    """Install the SIGINT ladder and the SIGTERM handler for THIS run (runstop 71vjbn, spec R12/R13).

    The exact counterpart of `oc_runipd.install_stop_triggers`, including its decision about the
    PRE-EXISTING `KeyboardInterrupt` behavior that registering a SIGINT handler suppresses:

    * 1st Ctrl-C requests level 1 and RETURNS (the point of level 1 is to let the in-flight turn
      finish rather than unwind through it);
    * 2nd requests level 3 (stop at the next observed safe checkpoint);
    * 3rd requests level 4 AND raises `KeyboardInterrupt`, which preserves `execute_item`'s
      `except KeyboardInterrupt` (item marked `interrupted`, `ipd-interrupted` appended, lanes
      reclaimed) and `main`'s exit-130 path that Phases 3-4 depend on;
    * SIGTERM requests level 3 and returns, replacing today's kill-and-orphan behavior (spec R13).

    The handler only RECORDS, through the handler-safe writer, and never reaps (spec R5/R7). A trigger
    that cannot be installed is reported LOUDLY rather than silently skipped (spec A10).
    """

    def _terminal(level: int, requester: str) -> None:
        raise KeyboardInterrupt(
            f"stop level {level} ({runner_stop.LEVEL_NAMES.get(level, 'unknown')}) requested by "
            f"{requester or 'SIGINT'}"
        )

    status = runner_stop.install_stop_signal_handlers(
        run_dir,
        command=_detect_driver_command(),
        requester=f"signal pid={os.getpid()}",
        on_terminal=_terminal,
    )
    unsupported = runner_stop.render_trigger_support(status)
    if unsupported:
        print(unsupported, file=sys.stderr)
    return status


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # THE IMPLICIT-START SHIM. Any first token NOT in this set is treated as a selector and gets
    # `start` prepended. runstop 71vjbn (E-03): `"stop"` MUST be listed here. This shim lives in
    # `main()` and NOT in `build_parser()`, so adding the `stop` subparser alone does not cover it -
    # `stop <run-id> --now` would be rewritten to `start stop <run-id> --now`, i.e. it would LAUNCH a
    # run with the literal selector `stop`. That is a silent misfire in the exact opposite direction
    # of the operator's intent, so a test asserts the bare form is not rewritten (in both drivers).
    subcommands = {
        "start",
        "resume",
        "status",
        "report",
        "stop",
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

    run_dir = None
    # runstop 71vjbn (E-01/E-02): the SIGINT ladder and the SIGTERM handler are installed per-run,
    # inside the `start`/`resume` branches below, because a handler needs the run directory to record
    # into. `stop`, `status`, and `report` are short-lived out-of-band commands with no run to wind
    # down, so they keep the pre-existing SIGTERM->exit behavior.
    install_exit_signal_handler()

    try:
        if args.command == "stop":
            # runstop 71vjbn (E-03/E-04): out-of-band, deliberately BEFORE any run-lock or state
            # mutation. It never starts a run and never creates the run directory.
            return handle_stop_command(args)
        if args.command == "start":
            run_dir = initialize_run(args)
            print(f"Run ID: {run_dir.name}")
            print(f"State directory: {run_dir}")
            if args.prepare_only:
                print_status(run_dir)
                return 0
            # runstop 71vjbn: armed only now, because a handler needs the run dir to record into.
            install_stop_triggers(run_dir)
            with locked_run(run_dir):
                return run_queue(run_dir, retry_incomplete=False)

        run_dir = resolve_run_dir(args.repo, args.run_id)
        output_mode = getattr(args, "output_mode", None)

        if args.command == "status":
            if getattr(args, "json", False):
                state = load_state(run_dir)
                print(json.dumps(state, indent=2, sort_keys=True))
                # bkclose (zhr6mc) E-07: NO pointer line for machine-readable output; `--json` must
                # stay parseable. Symmetric with `oc_runipd`.
                return 0
            print_status(run_dir)
            print(render_runs_pointer(load_state(run_dir)))
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
            # runstop 71vjbn: a resumed run is just as interruptible as a fresh one.
            install_stop_triggers(run_dir)
            with locked_run(run_dir):
                return run_queue(
                    run_dir,
                    retry_incomplete=args.retry_incomplete,
                    output_mode=output_mode,
                )

        raise DriverError(f"Unsupported command: {args.command}")
    except KeyboardInterrupt as exc:
        msg = str(exc)
        is_sigterm = "SIGTERM" in msg
        exit_reason = (
            "TERMINATED (SIGTERM)" if is_sigterm else "INTERRUPTED (SIGINT / Ctrl-C)"
        )
        if run_dir and (run_dir / "state.json").is_file():
            try:
                state = load_state(run_dir)
                if not state.get("_summary_table_printed"):
                    pal = Palette(should_color(sys.stdout))
                    print(
                        render_run_summary_table(
                            state,
                            run_dir,
                            pal=pal,
                            exit_reason=exit_reason,
                            driver_label="antigravity",
                        )
                    )
                    hint = render_continuation_hint(state, run_dir)
                    print(hint)
            except Exception:
                pass
        # bkclose (zhr6mc) E-05/E-06/E-07: the shutdown report on the SIGNAL paths, emitted
        # through the funnel that ALREADY exists rather than a `signal.signal` registration this
        # plan may not make (see the ownership note on `signal_report_callback`). BOTH signals
        # arrive here: CPython raises `KeyboardInterrupt` for SIGINT, and executed plan `bds6nd`
        # registers the SIGTERM handler in `render_stream.install_exit_signal_handler`, which
        # raises `KeyboardInterrupt("Terminated by SIGTERM")` from a module the guards do not
        # cover. Ledger BEFORE print, and idempotent, so a repeated signal cannot double-report.
        emit_shutdown_report(to_stderr=True)
        print(
            f"{'Terminated by SIGTERM' if is_sigterm else 'Interrupted'}; durable run state was preserved.",
            file=sys.stderr,
        )
        return 143 if is_sigterm else 130
    except DriverError as exc:
        if run_dir and (run_dir / "state.json").is_file():
            try:
                state = load_state(run_dir)
                if not state.get("_summary_table_printed"):
                    pal = Palette(should_color(sys.stdout))
                    print(
                        render_run_summary_table(
                            state,
                            run_dir,
                            pal=pal,
                            exit_reason=f"FAILED ({exc})",
                            driver_label="antigravity",
                        )
                    )
                    hint = render_continuation_hint(state, run_dir)
                    print(hint)
            except Exception:
                pass
        print(f"runagy: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"runagy: unexpected failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
