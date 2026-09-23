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
import json
import os
import re
import select
import subprocess
import sys
import threading
import time
from collections.abc import Iterable, Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import Any, Callable, NamedTuple

# The interactive streaming render layer (Palette/render_event/Heartbeat and the
# coupled ANSI/status helpers) lives in the shared ``render_stream`` module so it is
# defined once and reusable across drivers (runnernorm child dg28i9). It is re-exported
# here (see ``__all__`` below) so existing ``oc_runipd`` call sites and tests keep
# referencing these names. ``should_color`` (the TTY color decision) stays local to the
# caller per OQ-01.
from agent_workflows import (
    runner_shared,
    runner_shutdown,
    stall_progress,
)

# runnoop Order 02 (`m85gxh`): the pure PER-ARTIFACT DISPOSITION renderer, whose wording and reason
# vocabulary live in `run_selection_policy` and must never be forked into a driver.
#
# SAFE AT MODULE LEVEL, measured rather than assumed: an AST walk of MODULE-LEVEL imports reachable
# from `run_selection_policy` reaches 16 modules and NONE of them is `oc_runipd`, `agy_runipd`,
# `runner_shared` or `render_stream`, so this edge closes no cycle. (A walk that also follows
# function-local imports does reach all four, which is why the distinction is stated here: those are
# deferred imports and cannot participate in an import-time cycle.)
#
# THE `as <same-name>` FORM IS DELIBERATE, and it is this repository's documented idiom for a shared
# symbol a runner must expose: it keeps `ruff` from stripping the binding as unused (which it has done
# to six such re-exports before, caught only by a symmetry test) and it makes the attribute reachable
# for `tests/test_runner_refork_guard.py`'s object-identity half. BOTH hosts import this from the
# owning module DIRECTLY; neither imports it from the other.
from agent_workflows.run_selection_policy import (
    render_queue_dispositions as render_queue_dispositions,
)

# runnoop Order 03 (`bsc457`) E-03: the END-OF-RUN DISPOSITION SUMMARY, imported from the SAME owning
# module and on the same terms as the line renderer above. Not added to `oc_runipd` for the other host
# to import: both hosts read `run_selection_policy` directly, so the one-way oc-to-agy import count is
# unchanged.
from agent_workflows.run_selection_policy import (
    render_disposition_summary as render_disposition_summary,
)

# terseout `ntf6sx` E-04: the ONE concise-reporting contract, embedded in FULL in this driver's
# execution and verifier prompts. A fresh worker session must not depend only on ambient host
# instructions, which is why the drivers already embed their other critical safeguards.

# runprofile Order 01 (`f2mrsw`): the named-runner-profile schema, store, and RESOLVER. Imported as a
# module (not symbol-by-symbol) so this driver cannot fork profile parsing or precedence, which
# runprofile-03 (`3cm15q`) execution contract item 2 forbids: "Use their resolver; do not fork profile
# parsing/storage inside oc_runipd.py". Module-level import also lets a test monkeypatch
# `runner_profiles.store_path` and have this driver see it.
from agent_workflows import runner_profiles

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

# fullauto Order 01 (97df1z): the `--full-auto` auto-approve gate lives in ONE shared module, so the
# two drivers cannot drift (the previous per-driver copies already had, silently). Re-exported below
# for existing external callers. Do NOT reintroduce a local copy of either function.
from agent_workflows.plan_readiness import (
    extract_newest_history_entry,
    is_plan_review_approved,
)
from agent_workflows.render_stream import (
    activity_for_item,
    resolve_item_lifecycle,
    format_spec_impact_announcement,
    format_spec_impact_failure,
    format_spec_edit_report,
    _ANSI_CODES,
    _ANSI_RESET,
    _ANSI_STRIP_RE,
    Heartbeat,
    Palette,
    # orchprobe (r2i1b1) E-01/E-02: the ONE refusal record, carrying a reason AND a remedy, defined in
    # `render_stream` because that module imports no first-party module and `runner_shared` already
    # imports IT (so the reverse edge the renderer needs cannot exist). Record a refusal through
    # `record_refusal`, never by assigning the key, so the writer cannot drift from the reader.
    REFUSAL_KEY as REFUSAL_KEY,
    Refusal as Refusal,
    record_integration_refusal as record_integration_refusal,
    record_refusal as record_refusal,
    refusal_of_item as refusal_of_item,
    Statusline,
    StreamTracker,
    _one_line,
    _strip_ansi,
    execution_index,
    format_compact_tokens,
    format_progress_bar,
    format_run_order_announcement,
    format_stall_countdown,
    format_statusline,
    format_statusline_lines,
    format_tokens,
    render_event,
    render_run_summary_table,
    install_exit_signal_handler,
    statusline_action_for_item,
)
from agent_workflows.worktree_lease import WORKTREES_SUBDIR

# rununify 02 (`818uru`): the symbols below were defined in THIS module AND in `agy_runipd` with
# bodies PROVEN AST-identical, so each had two definitions and a fix to one silently missed the other.
# They now have exactly ONE definition, in `runner_shared`, and are re-exported here so every call
# site and test in this module keeps working unchanged. `runner_shared` imports NEITHER runner, so
# there is no cycle. Do NOT reintroduce a local copy of any of them; `tests/test_runner_shared.py`
# fails if you do, in both directions.
#
# `DriverError` is the reason this seam went first: it was defined as two DISTINCT classes, so an
# error raised here could NOT be caught by `except DriverError` in `agy_runipd`, which carried a
# hand-written wrapper whose only job was to translate one into the other. There is now ONE class,
# and `StallTimeout`/`ToolIdentityError` below still subclass it, so every `except DriverError` in
# either driver catches either driver's stall.
#
# The `as <same-name>` form marks these as an intentional RE-EXPORT so an autoformatter cannot strip
# the ones this module does not itself call. That is not cosmetic: `ruff` removed 6 such re-exports
# from `agy_runipd` on a previous change's first attempt and only a symmetry test caught it.
# orchretire-03 (`pgq326`) E-04 EXTENDS this seam with the ACTION DECISION and the ORCHESTRATOR
# DISPATCH OUTCOME. `determine_action`/`action_for` were defined HERE, and agy had its own
# `determine_action` and NO `action_for` at all, so measured at HEAD `844d195c`:
# `agy.determine_action('approved')` returned `'execute'` where
# `oc.action_for('orchestrator','approved')` returned `'orchestrate'` -- `aw agy run` would have spent
# an agent turn AUTHORING against an approved orchestrator whose coordination role the runner has
# already superseded. Spec `77tr3o` R-10 requires the decision be shared CODE, so both hosts now bind
# these SAME objects and `tests/test_orchestrator_retirement.py` asserts that by object identity.
# `decide_orchestrator_dispatch`/`dispatch_orchestrator_item` come with them, because deciding the
# action is not enough: a host that decides `orchestrate` and has no branch READING it spends the turn
# anyway (E-07).
from agent_workflows.runner_shared import (
    ORCH_DISPATCH_RECONSIDER as ORCH_DISPATCH_RECONSIDER,
)
from agent_workflows.runner_shared import (
    ORCH_DISPATCH_RETIRE as ORCH_DISPATCH_RETIRE,
)
from agent_workflows.runner_shared import (
    ORCH_DISPATCH_TERMINATE as ORCH_DISPATCH_TERMINATE,
)
from agent_workflows.runner_shared import (
    ORCH_REASON_FINALIZE_REFUSED as ORCH_REASON_FINALIZE_REFUSED,
)
from agent_workflows.runner_shared import (
    OrchestratorDispatch as OrchestratorDispatch,
)
from agent_workflows.runner_shared import (
    action_for as action_for,
)
from agent_workflows.runner_shared import (
    decide_orchestrator_dispatch as decide_orchestrator_dispatch,
)
from agent_workflows.runner_shared import (
    determine_action as determine_action,
)
from agent_workflows.runner_shared import (
    dispatch_orchestrator_item as dispatch_orchestrator_item,
)

# runverdict (`1bfppy`) E-01/E-02: the ONE fail-closed VERIFIER VERDICT MAPPING, bound here as a
# re-export so `tests/test_runner_refork_guard.py` can assert BOTH hosts see the SAME object. Imported
# from `runner_shared` and NEVER defined here: a verdict test written in a driver is precisely the
# re-fork that let `CORRECTION_REQUIRED` be recorded as `verified` in two byte-identical copies.
from agent_workflows.runner_shared import (
    map_verdict as map_verdict,
)
from agent_workflows.runner_shared import (
    normalize_verdict as normalize_verdict,
)
from agent_workflows.runner_shared import (
    verdict_refusal_text as verdict_refusal_text,
)
from agent_workflows.runner_shared import (
    VerdictMapping as VerdictMapping,
)
from agent_workflows.runner_shared import (
    VERDICT_REFUSAL_CODE_DECLINED as VERDICT_REFUSAL_CODE_DECLINED,
)
from agent_workflows.runner_shared import (
    VERDICT_REFUSAL_CODE_UNREADABLE as VERDICT_REFUSAL_CODE_UNREADABLE,
)

# runverdict-06 (`fzxfph`): WHY there was no verdict to map, which is a different question from what
# the verdict said. Bound from `runner_shared` and NEVER defined here, for the identical reason the
# verdict table above is: the three facts were previously collapsed into one `unverified` token in two
# byte-identical per-host copies, and a reason code spelled twice is the producer/reader drift this
# module has already paid for.
from agent_workflows.runner_shared import (
    verify_absence_text as verify_absence_text,
)
from agent_workflows.runner_shared import (
    VERIFY_ABSENCE_CODES as VERIFY_ABSENCE_CODES,
)
from agent_workflows.runner_shared import (
    VERIFY_ABSENCE_NO_OUTCOME_FILE as VERIFY_ABSENCE_NO_OUTCOME_FILE,
)
from agent_workflows.runner_shared import (
    VERIFY_ABSENCE_PLAN_UNRESOLVABLE as VERIFY_ABSENCE_PLAN_UNRESOLVABLE,
)
from agent_workflows.runner_shared import (
    VERIFY_ABSENCE_TURN_INTERRUPTED as VERIFY_ABSENCE_TURN_INTERRUPTED,
)
from agent_workflows.runner_shared import (
    VERIFY_ABSENCE_VERDICT_UNREADABLE as VERIFY_ABSENCE_VERDICT_UNREADABLE,
)

# depblock 01 (`akzy45`) E-04: the DRAIN-TIME classification, bound HERE rather than reached through
# `runner_shared.` at the call site, because the cross-driver symmetry guard
# (`tests/test_runner_item_dependencies.py::CrossDriverSymmetryTests`) requires each driver to CARRY
# the attribute and asserts it is the SAME OBJECT on both. That guard is what caught agy running its own
# copy of `dependency_status_detailed` for months, so a new shared dependency rule joins it by name.
from agent_workflows.runner_shared import (
    classify_drain_block as classify_drain_block,
)
from agent_workflows.runner_shared import (
    record_transient_dependency_wait as record_transient_dependency_wait,
)
from agent_workflows.runner_shared import (
    ID6_RE as ID6_RE,
)
from agent_workflows.runner_shared import (
    spec_impacts_for_queue as spec_impacts_for_queue,
)
from agent_workflows.runner_shared import (
    declared_spec_paths as declared_spec_paths,
)
from agent_workflows.runner_shared import (
    conflicted_paths as conflicted_paths,
)

# runnoop zz5yxq (E-02/E-04): the ACTION-AWARE SUCCESS BAR. ONE definition in `runner_shared`, bound
# here with the `as <same-name>` form and pinned by object identity in
# `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`, so a second copy in either host fails a test.
# The form is load-bearing, not cosmetic: `ruff` stripped 6 such re-exports on one commit attempt in
# this package and only a cross-driver symmetry test caught it.
from agent_workflows.runner_shared import (
    success_states_for_action as success_states_for_action,
)
from agent_workflows.runner_shared import (
    item_reached_success as item_reached_success,
)
from agent_workflows.runner_shared import (
    item_needs_approval as item_needs_approval,
)
from agent_workflows.runner_shared import (
    exit_code_statuses as exit_code_statuses,
)
from agent_workflows.runner_shared import (
    EXIT_SUCCESS_TOKEN as EXIT_SUCCESS_TOKEN,
)
from agent_workflows.runner_shared import (
    NEEDS_INPUT_TOKEN as NEEDS_INPUT_TOKEN,
)
from agent_workflows.runner_shared import (
    NEEDS_INPUT_KEY as NEEDS_INPUT_KEY,
)
from agent_workflows.runner_shared import (
    enforce_no_active_runner_conflict as enforce_no_active_runner_conflict,
)
from agent_workflows.runner_shared import (
    format_slated_artifacts_table as format_slated_artifacts_table,
)

# runconcur-01 (`vddpml`) E-01/E-02/E-05: the REPOSITORY-scoped concurrency layer. Bound in the
# `as <same-name>` re-export form, so these ARE the shared objects (object identity holds, and
# `tests/test_concurrent_driver_guard.py` asserts it) rather than per-host wrappers. A one-sided guard
# would leave `aw agy run` able to race `aw oc run`, which is precisely the failure being fixed.
from agent_workflows.runner_shared import (
    peer_drivers as peer_drivers,
)
from agent_workflows.runner_shared import (
    format_peer_driver_report as format_peer_driver_report,
)
from agent_workflows.runner_shared import (
    integration_lock as integration_lock,
)
from agent_workflows.runner_shared import (
    integration_lock_path as integration_lock_path,
)
from agent_workflows.runner_shared import (
    integrate_under_repository_lock as integrate_under_repository_lock,
)
from agent_workflows.runner_shared import (
    runs_repo_root as runs_repo_root,
)

# retrywire (`xipfy1`) E-07: the TURN-FAILURE CORRECTION layer, bound in the same `as <same-name>`
# form and pinned by OBJECT IDENTITY in `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`. Bound
# here rather than reached as `runner_shared.<name>` at the call site because that table's identity
# half asserts each driver CARRIES the attribute and that both carry the SAME object - the guard that
# caught agy running its own copy of `dependency_status_detailed` for months. The decision, the
# performer and the classification table are all registered: a host that re-forked only the TABLE
# would agree about the mechanism and disagree about which failures are retryable, which is the more
# dangerous half (it decides what the run spends paid model turns on).
from agent_workflows.runner_shared import (
    TURN_RETRYABLE_DISPOSITIONS as TURN_RETRYABLE_DISPOSITIONS,
)
from agent_workflows.runner_shared import (
    TURN_RETRY_CLASSIFICATION as TURN_RETRY_CLASSIFICATION,
)
from agent_workflows.runner_shared import (
    turn_failure_is_retryable as turn_failure_is_retryable,
)
from agent_workflows.runner_shared import (
    turn_retry_decision as turn_retry_decision,
)
from agent_workflows.runner_shared import (
    turn_retry_budget_remaining as turn_retry_budget_remaining,
)
from agent_workflows.runner_shared import (
    handle_turn_failure_retry as handle_turn_failure_retry,
)


# integpath-02 (`6sb3yu`): a PURE move, so it is bound by re-export rather than wrapped (unlike its
# two neighbours, which need this host's `run_checked`/`host_label`). The `as <same-name>` FORM is
# load-bearing and not cosmetic: `ruff` removed 6 such re-exports on a first commit attempt in this
# package and only a cross-driver symmetry test caught it, so an unmarked import of a symbol this
# module does not itself call is at risk of being "cleaned up".
from agent_workflows.runner_shared import (
    dirty_tree_overlap as dirty_tree_overlap,
)
from agent_workflows.runner_shared import (
    format_merge_conflict_reason as format_merge_conflict_reason,
)
from agent_workflows.runner_shared import (
    generated_manifest_paths as generated_manifest_paths,
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
    lane_executed_carrier_override as lane_executed_carrier_override,
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
    backlog_item_paths_for_id as backlog_item_paths_for_id,
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

# rununify 03 (`i3d6ml`) E-02: the two `DriverError` subclasses. Both runners defined these, with
# identical (empty) bodies and differently-worded docstrings, so there were TWO `StallTimeout` classes
# and TWO `EmptyStatusSelection` classes. Binding the shared ones here means a stall raised through
# either driver's code path is caught by `except StallTimeout` in either driver, which is the same
# defect class `DriverError` itself was moved to end.
from agent_workflows.runner_shared import (
    EmptyStatusSelection as EmptyStatusSelection,
)
from agent_workflows.runner_shared import (
    StallTimeout as StallTimeout,
)

# rununify 03 (`i3d6ml`) E-02: host-neutral helpers whose two definitions carried no behavioral
# disagreement. `_findings_block_reason` delegates entirely to `review_findings.subject_gating_blocks`
# and `make_integration_validation_runner` returns a constant-True validator, so neither had anything
# host-shaped to preserve.
from agent_workflows.runner_shared import (
    _findings_block_reason as _findings_block_reason,
)
from agent_workflows.runner_shared import (
    make_integration_validation_runner as make_integration_validation_runner,
)

# rununify 03 (`i3d6ml`) E-02/E-03: `build_review_prompt` (the `/plan-review` command plus the isolation
# statement) and the four symbols whose hosts' OBSERVABLE OUTPUT differed. See each shared definition's
# docstring for what changed on which host; `attempt_log_path` in particular now produces oc's filename
# shape on BOTH hosts, which is what `run_analytics_statistics._VERIFY_LOG_RE` matches.
from agent_workflows.runner_shared import (
    attempt_log_path as attempt_log_path,
)
from agent_workflows.runner_shared import (
    build_review_prompt as build_review_prompt,
)
from agent_workflows.runner_shared import (
    resolve_prior_lane as resolve_prior_lane,
)
from agent_workflows.runner_shared import (
    sync_receipt_into_worktree as sync_receipt_into_worktree,
)
from agent_workflows.runner_shared import (
    write_prompt as write_prompt,
)

# rununify 05 (`ct4w0a`) E-02/E-04: the two symbols whose host definitions genuinely DISAGREED about
# behavior. `extract_session_id` is the UNION of both readers (all four keys, flat AND nested), because
# `conversation_id` is agy's own wire format and adopting oc's reader outright left agy unable to find
# its own session id. `_SESSION_ID_KEYS` comes with it: it was defined TWICE with DIFFERENT contents
# (three keys here, four in agy), so a reader finding either copy first would re-fork the disagreement.
# `begin_baseline_env` moves as `driver_begin`'s dependency; `driver_begin` itself keeps a one-line
# wrapper below because its pin helpers are defined HERE and cannot move (see that wrapper's note).
from agent_workflows.runner_shared import (
    _SESSION_ID_KEYS as _SESSION_ID_KEYS,
)
from agent_workflows.runner_shared import (
    begin_baseline_env as begin_baseline_env,
)
from agent_workflows.runner_shared import (
    extract_session_id as extract_session_id,
)

# rununify 06 (`sy7uwh`) E-02/E-03: the ONE plan record, its ONE reader, and the readers/constants that
# reader closes over. All of these used to be DEFINED in this module (with `agy_runipd` importing three
# of them FROM here and carrying its own divergent record and parser); there is now one of each, so the
# two hosts cannot come to disagree about what a plan record IS. The full rationale sits at each removed
# definition's old site further down this file. `plan_kind_from_file`/`resolve_manifest_kind` are the
# legacy-manifest `kind` fallback this host previously LACKED (`sy7uwh` OQ-03).
from agent_workflows.runner_shared import (
    PlanRecord as PlanRecord,
    _KIND_RE as _KIND_RE,
    _PLAN_FILENAME_RE as _PLAN_FILENAME_RE,
    _read_from_backlog as _read_from_backlog,
    _read_item_dependencies as _read_item_dependencies,
    _read_kind as _read_kind,
    build_dynamic_manifest as build_dynamic_manifest,
    parse_plan_file as parse_plan_file,
    plan_kind_from_file as plan_kind_from_file,
    resolve_manifest_kind as resolve_manifest_kind,
)

# rununify 01 (`2r306y`): `_read_id`/`_read_status` were defined in THIS module AND in
# `agy_runipd`, both AST-identical to `selectors`' own readers, so one owner had three copies.
# They are now the public `selectors` readers, bound to this module's historical private names
# because that is what every call site here already uses. `selectors` imports no runner, so
# there is no cycle. NOTE the aliases are deliberately the PERMISSIVE readers: this module's
# copies tolerated any whitespace after the `-` while `selectors`' internal readers require
# exactly one space, and that strictness is a documented `aw find` matching contract.
#
# `_read_id`'s `# noqa: F401` IS LOAD-BEARING, not clutter (rununify 06 `sy7uwh`). Once
# `parse_plan_file` moved to `runner_shared`, this module stopped CALLING `_read_id` itself, so
# `ruff --fix` deleted the import as unused -- and that silently broke a contract, because
# `tests/test_runner_refork_guard.py` requires BOTH runners to keep exposing `_read_id` bound to
# `selectors.read_front_matter_id` (measured: two tests failed with `oc_runipd._read_id is MISSING`).
# The `as <same-name>` form alone was NOT enough (ruff removed it again on the next hook run), and this
# module's `__all__` does not list the private readers, so the suppression is the mechanism that keeps
# the re-export alive. `_read_status` is still called locally and so needs none.
from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - a DELIBERATE re-export; tests/test_runner_refork_guard.py requires it
from agent_workflows.selectors import read_front_matter_status as _read_status

# The durable stop-request record and the cooperative-checkpoint poll (spec `c4gd2h` R7-R9/R11)
# live in the shared ``runner_stop`` module so both drivers consult ONE mechanism.
from agent_workflows import runner_stop

# lanectn `cqx5v7` (spec `7ckptx` R2.6): the host-neutral home for lane containment rules. Both
# drivers call THESE functions; neither carries a second copy of the path projection, the collection,
# or the idempotency (CID-2).
from agent_workflows import lane_containment

# Where a hardened lane's scratch/submission channel lives, relative to the lane worktree
# root. Lane-local so it is writable by construction and torn down with the lane.
LANE_SCRATCH_SUBDIR = ".aw/lane-scratch"

# Re-exported from render_stream for backward-compatible access via ``oc_runipd``.
__all__ = [
    "_ANSI_CODES",
    "_ANSI_RESET",
    "_ANSI_STRIP_RE",
    "activity_for_item",
    "resolve_item_lifecycle",
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
    "statusline_action_for_item",
    # fullauto 97df1z: re-exported from `plan_readiness` so external callers that imported these
    # from the driver keep working after the local duplicates were deleted.
    "extract_newest_history_entry",
    "is_plan_review_approved",
]


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
    # The post-rename spellings (`l2mzxn`). BOTH are listed: a pre-rename run directory still
    # carries the old strings, and terminality must not depend on which vocabulary wrote the file.
    "merge-needs-human",
    "merge-refused",
}
# rununify 04 (`tx6q0h`): relocated to `runner_shared` (byte-identical in both hosts);
# re-exported so this module's other call sites are untouched.
SUCCESS_STATES = runner_shared.SUCCESS_STATES
EXECUTION_SUCCESS_STATES = {"executed", "substantially-complete"}
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
# NARROWED BY depblock 01 (`akzy45`) E-01/E-02. This note used to record, as a known limitation, that
# when NO queued item is satisfiable the selection loop marked EVERY remaining queued item
# `dependency-blocked` and BROKE out of the run, so a findings-block could end a run rather than park
# one item. THE ALL-OR-NOTHING PART IS GONE: the drain arm now CLASSIFIES each remaining item through
# the shared `runner_shared.classify_drain_block` and writes this terminal label only on one that is
# PERMANENTLY blocked (a terminal-non-success prerequisite, a cycle, a dangling or unsatisfiable
# external edge, or any cause it cannot prove transient). An item whose every unmet prerequisite is
# still NON-TERMINAL is left `queued` and reported through `render_transient_dependency_waits` instead.
# The loop still BREAKS - nothing in a run re-queues such a prerequisite, so waiting inside this
# invocation cannot pay off - but the item keeps the cheaper recovery route below.
#
# THE THREE WRITE SITES FOR THIS STATUS, classified by E-01 so the next reader need not re-derive them:
#   1. `cascade_dependency_blocked` - PERMANENT by construction. It fires only on a prerequisite that
#      is `in TERMINAL_STATES and st not in required` (action-aware), which is exactly the
#      can-never-be-ready case. CORRECT AS WRITTEN; deliberately unchanged by `akzy45`.
#   2. The drain-time `if runnable is None:` arm in `run_queue` (this host and `agy_runipd`). This was
#      the site that conflated the two facts, and it is the ONE site `akzy45` changed.
#   3. `runner_shared.dispatch_orchestrator_item`'s `terminal_status` DEFAULT PARAMETER, reached by its
#      TERMINATE outcome. ALREADY CORRECT and the worked example this fix generalizes: `pgq326` split
#      that path three ways, where RECONSIDER writes NO status (leaving the item `queued`, which is
#      precisely the transient handling) and TERMINATE writes the terminal status WITH a specific
#      reason. Left byte-unchanged.
DEPENDENCY_BLOCK_RECOVERY_HINT = (
    "resolve the named cause, then re-queue with "
    "`aw oc runipd resume --repo <repo> --retry-incomplete <run-id>`; "
    "a bare `resume` does NOT re-queue a dependency-blocked item"
)

# Frontmatter and filename extraction regexes
_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
# `_KIND_RE` and `_PLAN_FILENAME_RE` are IMPORTED from `runner_shared` (rununify 06 `sy7uwh` E-03), not
# defined here. They MOVED with `parse_plan_file`/`_read_kind`, which are the only things that close
# over them: `_PLAN_FILENAME_RE` was byte-identical in both runners and `_KIND_RE` was oc-only, so
# leaving a duplicate CONSTANT behind would reproduce the same defect one layer down - a fix to either
# pattern would still not reach the runner carrying its own copy, which is exactly how `render_stream`'s
# ANSI constants came to be re-forked. Both are re-exported below with the rest of the shared names.
#
# NOTE (lanetruth-03 / 8guhs0 E-01): there is deliberately NO dependency regex here. The runner
# used to carry a private `_DEPS_RE` matching a LEGACY `Dependencies:`/`Depends-on:` field that no
# plan in the tree uses, so the canonical `- Item-Dependencies:` statement was invisible and every
# queue item froze with `dependencies: []`. The canonical field NAME comes from
# `ipd_schema.META_ITEM_DEPENDENCIES` and its GRAMMAR from `ipd_schema.parse_item_dependencies`
# (see `_read_item_dependencies`). Spec 25kzda 2.10: "All surfaces call this evaluator; none
# reimplement the rules." Re-adding a dependency regex here is a regression guarded by
# tests/test_runner_item_dependencies.py.

# Terminal output verbosity for the streamed child-agent turn.
OUTPUT_MODES = ("clean", "quiet", "raw")


# `StallTimeout` and `EmptyStatusSelection` are IMPORTED from `runner_shared` (rununify 03 `i3d6ml`
# E-02), not defined here. They are bound at the top of this module with the rest of the shared
# re-exports, so every `except StallTimeout` / `except EmptyStatusSelection` below is unchanged and now
# names the SAME class the antigravity driver names. `main`'s handler ORDER still matters and is
# untouched: the `EmptyStatusSelection` clause must precede the generic `except DriverError`, or the
# generic one absorbs it and an empty status selection exits 2 instead of 0.


class ToolIdentityError(DriverError):
    """Raised when a nested ``aw`` would run code OTHER than the runner's own installation.

    lanetruth Order 01 (af7i6p) / OQ-02: this is RUN-FATAL, not item-local. A tool-identity
    mismatch means the control plane executing EVERY item's lifecycle transition is not the
    code the runner believes it is, so the fault is not attributable to whichever item merely
    happened to trigger the probe. Contrast ``dependency-blocked``, which is correctly
    item-scoped. Spec 25kzda 1.4/A1 reserves ABORT RUN for exactly this identity class."""


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
    # KEEP the runner's own root even when it IS the cwd. Without this exception the two halves of
    # the pin defeat each other: `pinned_child_env` PREPENDS the runner root to PYTHONPATH, and this
    # filter then removes that very entry whenever the runner is launched from its own checkout (the
    # normal case), so the child fell through to the site-packages copy and the identity probe
    # reported a MISMATCH that aborted every run. Measured: sys.path lost the runner's own checkout
    # root and `agent_workflows` resolved under site-packages as a
    # namespace package. The lane-shadowing defect this pin exists to close is a DIFFERENT cwd (a
    # lane worktree carrying its own unreviewed copy), which is still dropped.
    "_keep=os.environ.get('AW_PIN_KEEP_ROOT') or ''\n"
    "_drop-={_keep,os.path.realpath(_keep)} if _keep else set()\n"
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
    # Use __file__ when present, else fall back to __path__[0]. With the cwd stripped, an
    # installed agent_workflows can resolve as a NAMESPACE package whose __file__ is None
    # (measured: site-packages/agent_workflows with __file__ None and a valid __path__),
    # which made os.path.realpath() raise TypeError and the probe report a false MISMATCH,
    # aborting every run as tool-identity-mismatch.
    "_f=getattr(_a,'__file__',None) or (list(getattr(_a,'__path__',[]))+[None])[0]\n"
    "print(os.path.realpath(_f) if _f else 'UNRESOLVED')\n"
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
    # Tell the suppressing half which root is the RUNNER's, so it is never dropped as "the cwd".
    merged["AW_PIN_KEEP_ROOT"] = root
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


def run_checked(
    argv: list[str], cwd: Path | None = None, env: dict[str, str] | None = None
) -> str:
    """Run ``argv``, returning stdout, raising `DriverError` on a nonzero exit.

    rununify 02 (`818uru`) E-05: the IMPLEMENTATION is the single shared
    `runner_shared.run_checked`; this is a one-line wrapper that binds THIS host's
    `pinned_child_env`. It deliberately keeps the ORIGINAL name and signature, so all 13 call
    sites in this module are untouched.

    WHY A WRAPPER AND NOT A THREADED PARAMETER (maintainer ruling, `818uru` OQ-02): passing the
    env-builder at every call site would have rewritten ~86 call sites across the two
    highest-contention files in the repo, and would have broken the plan's own AST-fingerprint
    proof on exactly its riskiest symbols. A registration seam was declined separately, because
    process-global state makes behavior depend on import order. So the dependency is passed
    EXPLICITLY, at exactly one visible site per runner, with no mutable module state.
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


class StallWatchdog(runner_shared.StallWatchdog):
    """Watchdog thread that terminates the child process if its stream is quiet for too long.

    hostdedup Order 01 (`li44r9`) E-02: the LOGIC now has one definition, in `runner_shared`. This
    subclass exists to bind THIS host's `terminate_process`, which forwards this module's tunable
    `_SIGINT_GRACE_SECONDS` / `_SIGTERM_GRACE_SECONDS` at call time. A bare alias would have reaped with
    the shared defaults and silently made those constants inert.

    A SUBCLASS RATHER THAN A FACTORY FUNCTION, because the name is used as a TYPE as well as a
    constructor (`__enter__` returns it, and call sites annotate against it), so a function returning an
    instance would not be a drop-in replacement.
    """

    def __init__(
        self,
        process: subprocess.Popen,
        timeout: float | None = 600.0,
        check_interval: float = 1.0,
    ) -> None:
        super().__init__(
            process, timeout, check_interval, reaper=lambda p: terminate_process(p)
        )


# fullauto Order 01 (97df1z), OQ-02: the automated-actor provenance for a `--full-auto` clear. This
# is what replaces the machine self-asserting `--by-human`: the history record names the automation
# that cleared the plan, so the audit trail is honest about who advanced it.
#
# hostdedup Order 01 (`li44r9`) E-08: READ FROM THE DESCRIPTOR rather than re-spelled as a literal, so
# this name and `OC_HOST_LABELS.full_auto_actor` CANNOT DISAGREE. The value is unchanged
# (`"aw oc run --full-auto"`); what changes is that there is now one place it is written. That matters
# because it reaches a plan's PERMANENT `## Workflow history` as `--actor`, so two spellings drifting
# apart would be a durable-history defect that no test currently in the suite would catch: the shipped
# assertion (`tests/test_oc_runipd.py`) checks the argv against THIS name, so a literal here that drifted
# from the descriptor would keep passing while the runner wrote the other value.
FULL_AUTO_ACTOR = runner_shared.OC_HOST_LABELS.full_auto_actor
FULL_AUTO_APPROVAL_MESSAGE = (
    "auto-approved by --full-auto: review readiness cleared (not human approval)"
)


def set_plan_approved(
    repo: Path, id6: str, message: str = FULL_AUTO_APPROVAL_MESSAGE
) -> None:
    """Transition a reviewed plan to `auto-approved` via `aw set` - NOT to human `approved`.

    hostdedup Order 01 (`li44r9`) E-02/E-08: now a thin wrapper over the ONE definition in
    `runner_shared`, which holds the full rationale. THE ACTOR IS PASSED AS DATA, through
    `OC_HOST_LABELS.full_auto_actor`, and that is the whole reason this symbol needed a decision rather
    than a verbatim move: its two host bodies WERE byte-identical, yet each read a module-level
    `FULL_AUTO_ACTOR` resolving to a DIFFERENT string, and that string lands in a plan's permanent
    `## Workflow history` through `--actor`. This module's `FULL_AUTO_ACTOR` is retained below as the
    single source of that value and is still asserted by `tests/test_oc_runipd.py`.
    """
    return runner_shared.set_plan_approved(
        repo,
        id6,
        message,
        labels=runner_shared.OC_HOST_LABELS,
        argv_builder=pinned_module_argv,
        run_checked=run_checked,
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
    (in which case the caller leaves it for a human). The runner NEVER forces it.

    NOT ON THE LIVE ROLLUP PATH, and the actor below is why that matters. This function has ZERO
    callers (AST-verified: no call, no attribute reference, no name reference anywhere in the package,
    the tests, or `tools/`); the live rollup goes `runner_shared` -> `ipd_lifecycle.retire_orchestrator`
    with :func:`driver_actor`. Its actor used to read ``aw oc run (orchestrator rollup)``, which is the
    exact string the actor-parenthesis defect was first diagnosed from, and which the setter guard now
    REFUSES (plan fn2l1u E-07). It was FIXED rather than deleted, deliberately: the function is the one
    documented `oc`-only module-launch site that `tests/test_lane_tool_identity.py:585-609` asserts as
    an expected asymmetry against `agy`, so deleting it would quietly erase a discussed design point,
    while leaving the old string would leave a call site the guard refuses as a trap for whoever next
    wires it up. Do NOT add an `agy` twin; that same test forbids it.
    """
    # lanetruth Order 01 (af7i6p): pinned to the runner's OWN tooling, not the cwd's copy.
    cmd = pinned_module_argv(
        [
            "ipd",
            "set",
            "executed",
            id6,
            "--actor",
            # Parenthesis-free `key=value`, the shape every writer in the toolkit emits (see
            # `driver_actor` below and `attention_contract.actor_refusal`).
            "aw oc run step=orchestrator-rollup",
            # setterguard `4bc1nd` E-03: `--yes` matches the sibling `set_plan_approved` above and
            # STATES THE INTENT of a deliberate unattended transition. This site is a LATENT break,
            # not an observed one: `run_set_command` now refuses an unconfirmed mutation from every
            # caller, and this argv is saved TODAY only because a plan->`executed` request is
            # intercepted by the `aw ipd finalize` delegation which returns BEFORE the confirmation
            # check is reached. That ordering is incidental rather than a guarantee, so relying on it
            # would leave a trap for whoever next changes either path.
            "--yes",
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


# rununify 04 (`tx6q0h`): one-line wrapper over the shared definition. Measured before the lift, the
# shared body returns byte-identically to each host's own copy on every state that host produces.
def driver_actor(state: dict[str, Any]) -> str:
    return runner_shared.driver_actor(state, labels=runner_shared.OC_HOST_LABELS)


# rununify 05 (`ct4w0a`) E-04: `begin_baseline_env` and the `driver_begin` LAUNCHER BODY are now
# defined ONCE in `runner_shared` and this is the one-line wrapper that binds THIS host's pin
# helpers. It keeps the ORIGINAL name and signature, so both call sites in this module are untouched.
#
# WHY A WRAPPER AND NOT A PURE MOVE, since the plan that ordered this lift expected one: the shared
# module may never import a runner, and `pinned_child_env`/`pinned_module_argv` are DEFINED here in
# `oc_runipd` (agy imports them FROM here, which makes them the same object in both hosts but does
# not make them reachable from `runner_shared`). So they are INJECTED, which is the maintainer's
# ruled mechanism for exactly this case (`818uru` OQ-02) and is already how `run_checked` -- the
# OTHER nested-`aw` launcher, also living in `runner_shared` -- consumes this same dependency.
#
# WHAT AGY GAINS: agy's own `driver_begin` accepted no `isolated` and layered no baseline overlay, so
# an ISOLATED `aw agy run` turn asked `aw ipd begin` to gate on the MAIN tree while the turn would
# execute in a LANE. Both hosts now reach this one launcher, so that asymmetry cannot recur.
def driver_begin(
    repo: Path, id6: str, actor: str, *, isolated: bool = False
) -> tuple[int, str]:
    """Run the fail-closed `aw ipd begin <id6> --actor` gate before an execute turn.

    Delegates ENTIRELY to `runner_shared.driver_begin`, binding this host's `pinned_child_env` and
    `pinned_module_argv`. See that function for the contract and for what `isolated` declares."""
    return runner_shared.driver_begin(
        repo,
        id6,
        actor,
        isolated=isolated,
        env_builder=pinned_child_env,
        argv_builder=pinned_module_argv,
    )


# --- specvis (st5klo): declared-spec-edit VISIBILITY, at run start AND at run end -----------------
#
# A plan MAY amend a spec (maintainer ruling 2026-09-07), so the safeguard is not a gate but
# VISIBILITY: whenever a run will rewrite a `.spec.md`, the operator must be told, BEFORE the run
# spends anything and AGAIN when it ends. Nothing here refuses a run or gates an edit.
#
# Everything in this block is defined ONCE and IMPORTED by `agy_runipd` (the `as <same-name>`
# re-export form documented at `agy_runipd.py:84-88`), for the reason that module records: a second
# copy in the other driver is precisely how `Heartbeat` and `_read_deps` came to disagree.


def queue_plan_path(repo: Path, item: "Mapping[str, Any]") -> Path | None:
    """The plan FILE a runner queue entry refers to, or None when it cannot be located.

    WHY THIS EXISTS, because it is a defect fix and not a convenience. `spec_impacts_for_queue`
    documents its input as carrying `"path"` or `"plan_path"`, and that is what every test hand-built.
    But a REAL runner queue entry carries NEITHER: both drivers freeze the plan location under
    `"configured_file"` (`oc_runipd.py:2979`, `agy_runipd.py:2094`) and nothing ever assigns `"path"`.
    So the pre-run spec announcement read an empty path from every item, computed an empty impact set,
    and printed NOTHING - on BOTH hosts, for every real run, while a green suite asserted otherwise
    because its fixtures supplied the key production never writes. Measured 2026-09-14 by driving both
    entry points on a fixture repo whose approved plan declares a `.spec.md`: no `SPEC CHANGES:` line
    on either host, and the same queue rebuilt with a `"path"` key yields the impact.

    Resolution order, each rung there for a reason:
      1. `path` / `plan_path` - an explicit override, and the shape the shared helper documents.
      2. `last_plan_path` - written after a successful finalize MOVED the plan (pending/ -> executed/),
         so it is the only rung that is still correct at RUN END for an executed item.
      3. `configured_file` - the frozen location, correct for every item that has not moved.
      4. `resolve_plan_path` - the authoritative shared resolver, which finds a plan by id6 wherever it
         now lives. Last because it globs, and a cheap hit above is both faster and more specific.

    Returns None rather than raising: every caller is an ADVISORY reporting surface, and refusing a run
    because a report could not name a file would be a worse failure than the unnamed file.
    """
    for key in ("path", "plan_path", "last_plan_path", "configured_file"):
        raw = item.get(key)
        if not raw:
            continue
        candidate = Path(str(raw))
        if not candidate.is_absolute():
            candidate = repo / candidate
        if candidate.is_file():
            return candidate
    id6 = str(item.get("id6") or "").strip()
    if not id6:
        return None
    try:
        return resolve_plan_path(repo, str(item.get("configured_file") or ""), id6)
    except (DriverError, OSError):
        return None


def queue_with_plan_paths(
    repo: Path, queue: "Sequence[Mapping[str, Any]]"
) -> list[dict[str, Any]]:
    """``queue`` re-expressed in the shape `spec_impacts_for_queue` DOCUMENTS it consumes.

    Adapts at the CALL SITE rather than widening the shared helper's input contract, which keeps that
    helper's documented shape ("reads each item's plan file from disk at dispatch") intact and keeps
    this fix inside the plan's declared scope. An item whose plan cannot be located is DROPPED, which
    matches the helper's own posture: an unreadable plan is skipped rather than failing the run.
    """
    out: list[dict[str, Any]] = []
    for item in queue or ():
        resolved = queue_plan_path(repo, item)
        if resolved is None:
            continue
        out.append(
            {
                "id6": item.get("id6"),
                "setid": item.get("setid"),
                "path": str(resolved),
            }
        )
    return out


# The three states a per-item spec reconciliation can be in at run end. Named constants because the
# end-of-run renderer branches on them and a typo'd string literal would silently render an item as
# the wrong thing - and the WRONG thing here is specifically "clean", which is the one reading that
# must never be manufactured (F-9).
SPEC_RECONCILED = (
    "reconciled"  # finalize precheck PASSED; the delta below is authoritative.
)
SPEC_RECONCILE_REFUSED = "refused"  # precheck REFUSED, so its empty pair means nothing.
SPEC_NOT_FINALIZED = (
    "not-finalized"  # the item never reached finalize; there is no delta at all.
)


def spec_edit_record(
    plan_path: Path,
    reasons: "Mapping[str, str]",
    acks: "Mapping[str, str]",
    *,
    state: str,
) -> dict[str, Any]:
    """The durable, spec-FILTERED view of one item's two-way scope reconciliation (E-03).

    ``reasons`` are the out-of-scope CHANGED paths and ``acks`` the declared-but-UNMODIFIED ones, i.e.
    exactly what `_compute_scope_reconciliation` returns. This narrows both to `.spec.md` files and
    keeps the item's DECLARED spec set beside them, so the end report can name the two asymmetries
    that matter:

      * `modified_not_declared` - a spec this item changed WITHOUT declaring it. THE important case: an
        undeclared contract change is the thing declared-scope visibility exists to catch.
      * `declared_not_modified` - a spec the item promised to change and did not. Worth a line because
        it usually means the amendment half of a plan was skipped while its code half landed.

    ``state`` must be one of the three constants above and is stored verbatim, because the renderer's
    honesty depends on distinguishing "reconciled and clean" from "we could not tell".
    """
    try:
        declared = declared_spec_paths(plan_path.read_text(encoding="utf-8"))
    except OSError:
        declared = []
    modified_not_declared = sorted(p for p in (reasons or {}) if p.endswith(".spec.md"))
    declared_not_modified = sorted(p for p in (acks or {}) if p.endswith(".spec.md"))
    return {
        "state": state,
        "declared": list(declared),
        "modified_not_declared": modified_not_declared,
        "declared_not_modified": declared_not_modified,
    }


def record_item_spec_edits(
    repo: Path,
    plan_path: Path,
    item: "MutableMapping[str, Any]",
    *,
    reconcile: "Callable[[Path, Path], tuple[Mapping[str, str], Mapping[str, str]]]",
) -> dict[str, Any]:
    """Store one item's spec reconciliation on the queue entry, and return what was stored.

    Called from each driver's finalize CALL SITE, which is the one place where both the queue item and
    the LANE worktree the reconciliation must be resolved against are in hand. Recording it durably
    (rather than returning it up a call chain) is what makes the end-of-run report correct on a RESUMED
    run and on an ABORTED one: the report reads `state.json`, not process memory.

    ``reconcile`` IS AN INJECTED PARAMETER, AND DELIBERATELY SO. `_compute_scope_reconciliation` is
    FORKED into two near-identical per-driver definitions (`oc_runipd.py` and `agy_runipd.py`), which is
    real drift, but unifying it touches the finalize path this plan must not alter, so it stays out of
    scope. Taking it as an argument lets this ONE recorder serve both hosts while each passes its OWN
    copy: the fork is neither deepened (no third copy) nor silently unified (neither host's behavior
    changes). This is the same explicit-injection form `runner_shared` uses for exactly this situation.

    THE REFUSED CASE IS DETECTED HERE, NOT INFERRED FROM EMPTINESS. `_compute_scope_reconciliation`
    returns `({}, {})` both when the delta is genuinely clean and when `finalize_precheck` REFUSED (bad
    or missing begin receipt, failing pre-transition lint), so emptiness alone cannot tell a caller
    which happened. That is the same ambiguity E-01 removed from the start announcement, and printing a
    positive all-clear for an item whose scope was never actually checked would reintroduce it. So when
    the pair comes back empty this asks the precheck DIRECTLY for its exit code and records `refused`
    when it did not pass. The extra call is read-only and mutates nothing (`finalize_precheck` is
    documented "No mutation"), and it is made only in the empty case, so the common path pays nothing.
    """
    reasons: Mapping[str, str] = {}
    acks: Mapping[str, str] = {}
    refused = False
    try:
        reasons, acks = reconcile(repo, plan_path)
    except Exception:
        # A reconciliation that could not run is NOT a clean delta. Record it as refused, which is the
        # conservative reading: the report will say the item could not be reconciled rather than
        # claiming its specs were unchanged.
        refused = True
    if not refused and not reasons and not acks:
        try:
            from agent_workflows import ipd_lifecycle

            exit_code, _msg, _evidence, _findings = ipd_lifecycle.finalize_precheck(
                repo, plan_path
            )
            refused = exit_code != 0
        except Exception:
            refused = True
    record = spec_edit_record(
        plan_path,
        reasons,
        acks,
        state=SPEC_RECONCILE_REFUSED if refused else SPEC_RECONCILED,
    )
    item["spec_edits"] = record
    return record


def spec_edit_summary(repo: Path, state: "Mapping[str, Any]") -> dict[str, Any]:
    """Aggregate the per-ITEM spec records into the per-RUN view the end report renders (E-03).

    THE AGGREGATION IS THE POINT (F-9). The start announcement is per-QUEUE (it reads every plan's
    declared scope in one pass), while the reconciliation is per-ITEM and only exists for an item that
    reached finalize. So this must report BOTH sides and never let one stand in for the other:
    `declared` is what the whole queue said it would change, and `reconciled`/`refused`/`not_finalized`
    say how much of that the run could actually vouch for.

    Reads ONLY durable state, so it renders identically from `print_status` on a finished run
    directory, from a normal exit, and from a signal path mid-run. An older run directory carrying no
    `spec_edits` key degrades to `not_finalized`, which is the honest reading rather than a clean one.
    """
    declared: dict[str, list[str]] = {}
    reconciled: list[dict[str, Any]] = []
    refused: list[str] = []
    not_finalized: list[str] = []
    for item in state.get("queue", []) or ():
        id6 = str(item.get("id6") or "?")
        plan_path = queue_plan_path(repo, item)
        if plan_path is not None:
            try:
                specs = declared_spec_paths(plan_path.read_text(encoding="utf-8"))
            except OSError:
                specs = []
            if specs:
                declared[id6] = specs
        record = item.get("spec_edits") or None
        if not record:
            # Only an item that could have finalized is interesting here. A queued/never-dispatched
            # item is reported as not-finalized too, which is correct: nothing vouched for its scope.
            not_finalized.append(id6)
            continue
        rec_state = record.get("state")
        if rec_state == SPEC_RECONCILE_REFUSED:
            refused.append(id6)
            continue
        if rec_state == SPEC_NOT_FINALIZED:
            not_finalized.append(id6)
            continue
        reconciled.append(
            {
                "id6": id6,
                "setid": item.get("setid"),
                "declared": list(record.get("declared") or []),
                "modified_not_declared": list(
                    record.get("modified_not_declared") or []
                ),
                "declared_not_modified": list(
                    record.get("declared_not_modified") or []
                ),
            }
        )
    return {
        "declared": declared,
        "reconciled": reconciled,
        "refused": refused,
        "not_finalized": not_finalized,
    }


def report_run_spec_edits(
    state: "Mapping[str, Any]",
    *,
    stream: Any = None,
    partial: bool = False,
) -> list[str]:
    """Print the END-OF-RUN declared-spec-edit report; return the lines printed (E-03).

    THE PRIMARY DELIVERABLE of specvis st5klo. Before this, the ONLY spec-impact surface in the package
    was pre-dispatch, so on a long run the operator's one chance to notice a rewritten contract was the
    top of a scrollback the run had since buried. This re-states it where the run summary is read.

    ``partial`` is the label the maintainer required (OQ-01, 2026-09-08) for the non-primary summary
    sites - the interrupt/SIGTERM path and the DriverError path. Those fire when the run did NOT
    complete, which is exactly when an operator most needs to know a spec was rewritten, so they are
    wired; but their reconciliation is by definition half-computed, so they say so rather than
    presenting a partial contract change as authoritative.

    Advisory like its start-of-run twin, and for the same reason: this runs at EXIT, so an exception
    escaping here would replace a completed run's summary with a traceback. It reports its own failure
    instead of vanishing (the E-01 lesson applied to the new surface).
    """
    out = stream if stream is not None else sys.stdout
    pal = Palette(should_color(out))
    try:
        summary = spec_edit_summary(Path(state["repo"]), state)
        lines = format_spec_edit_report(summary, pal=pal, partial=partial)
    except Exception as exc:
        lines = format_spec_impact_failure(exc, pal=pal)
    for line in lines:
        print(line, file=out)
    return lines


# rununify 04 (`tx6q0h`): one-line wrapper over the shared definition, binding THIS host's labels.
# The two copies differed ONLY by the `aw oc run` / `aw agy run` string they write into a plan's
# PERMANENT finalize record, which is why the shared version takes no default for it.
def _compute_scope_reconciliation(
    repo: Path, plan_path: Path
) -> tuple[dict[str, str], dict[str, str]]:
    return runner_shared.compute_scope_reconciliation(
        repo, plan_path, labels=runner_shared.OC_HOST_LABELS
    )


def driver_finalize(
    repo: Path, plan_path: Path, id6: str, actor: str, message: str
) -> tuple[int, str]:
    """Run `aw ipd finalize <id6> --actor --message --apply` after a verified turn.

    hostdedup Order 01 (`li44r9`) E-02/E-08: a thin wrapper over the ONE definition in `runner_shared`,
    which holds the full rationale for computing the two-way scope reconciliation and for never forcing
    the transition. The labels are this host's own because the auto-reconciliation reason and ack
    strings name the driver inside a plan's PERMANENT finalize record.
    """
    return runner_shared.driver_finalize(
        repo,
        plan_path,
        id6,
        actor,
        message,
        labels=runner_shared.OC_HOST_LABELS,
        env_builder=pinned_child_env,
        argv_builder=pinned_module_argv,
    )


# --- bkclose (zhr6mc): close a backlog item when the run executes its last carrier ----------------
#
# `graduated` means "design handed off, code not yet written" and `done` means "written and
# validated", but until now NOTHING advanced an item across that boundary: no automation, no
# workflow instruction, no `aw check` rule, and the one warning that would nag inspects `open/`
# only. Measured at authoring: ZERO items in `done/` carry a graduation record, so the transition
# had never once occurred.
#
# The runner is the right owner because it is the only actor that knows the MOMENT the last carrier
# lands. Everything below is defined ONCE here and IMPORTED by `agy_runipd` (which does not
# re-declare it), for the same reason the dependency API is shared: a duplicated copy is exactly how
# the deleted `_read_deps` pair came to be identically wrong in both drivers.

# The carrier-kind partition. The closing rule turns on whether the item's requested output INCLUDES
# AN IPD, not on the carrier's type per se (zhr6mc OQ-01, resolved by the maintainer):
#   * carriers include >= 1 IPD -> the item promised CODE, so it closes only when every IPD carrier
#     is in a terminal `executed` state;
#   * carriers include NO IPD   -> the item asked for the ARTIFACT, so it is done as soon as that
#     artifact EXISTS. Spec status is deliberately NOT consulted: an unreviewed, unapproved spec
#     still satisfies "create a spec", and approval is the spec's own lifecycle (`aw specs`).
CARRIER_KIND_IPD = "ipd"
CARRIER_KIND_OTHER = "other"


def _carrier_kind(path: Path) -> str:
    """`ipd` for a plan IPD, `other` for any non-IPD carrier (spec, or a later artifact type)."""
    return CARRIER_KIND_IPD if path.name.endswith(".ipd.md") else CARRIER_KIND_OTHER


class BacklogCloseVerdict(NamedTuple):
    """The decision about ONE backlog item, and why.

    close:    may the run close this item `done` now?
    reason:   the human-readable justification, reported verbatim either as the close message or as
              the E-06 unclosed-item reason. Never a bare boolean, because "we did not close it" is
              useless to the operator without the cause.
    evidence: the repo-relative carrier path to cite as `--evidence` when closing, else None.
    rule:     `ipd` (every IPD carrier executed) | `other` (the artifact exists) | None (no close).
    """

    close: bool
    reason: str
    evidence: str | None
    rule: str | None


# rununify 06 (`sy7uwh`) E-03: `_read_from_backlog` is IMPORTED from `runner_shared`, not defined here.
# It is one of the six module-level readers `parse_plan_file` closes over, so it had to become resolvable
# in the shared module for that function to move at all; leaving a SECOND copy behind would reproduce
# exactly the defect this Set exists to end (a fix reaching one caller and not the other), one layer
# down from the record itself. `agy_runipd` already bound this by name FROM this module, and
# `tests/test_runner_backlog_close.py::SharedNotCopied` asserts object identity between the two hosts;
# a shared definition re-exported here under the same name satisfies that assertion, because both hosts
# now name the SAME object rather than one naming the other's.
# (The import itself is hoisted to the top-of-file shared-import block, per E402.)


def resolve_backlog_item(repo: Path, item_id6: str) -> Path | None:
    """The backlog item file whose `- Id:` is ``item_id6``, or None.

    Reuses `backlog._iter_items` + `backlog.parse_item` (the tree walker and metadata reader the
    backlog verbs themselves use) rather than globbing for the id6, so a renamed file or a
    filename/`Id:` mismatch cannot make the runner miss an item the setter would find."""
    from agent_workflows import backlog as _backlog

    for path in _backlog._iter_items(Path(repo)):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if _backlog.parse_item(text).id == item_id6:
            return path
    return None


def evaluate_backlog_close(
    repo: Path,
    item_id6: str,
    earned_paths: Iterable[str],
    *,
    executed_overrides: Mapping[str, str] | None = None,
) -> BacklogCloseVerdict:
    """Decide whether THIS run may now close backlog item ``item_id6``, and why not if it may not.

    ``earned_paths`` are the repo-relative paths this run actually produced (see
    `run_earned_paths`). It is the E-04 gate: a run may not close an item whose carriers it merely
    OBSERVED as already executed, because closing is a state change it did not earn.

    FAIL CLOSED (E-04). Every lookup below is wrapped: a missing item, an unreadable tree, or a
    raising helper yields `close=False` plus a recorded reason, never an escaping exception and never
    an optimistic close.

    ``executed_overrides`` (dirtygates-03 `9iq461` E-03) maps ONE carrier's path AS ``repo`` SEES IT
    to the path it ALREADY occupies in the caller's lane worktree, and asserts that this single
    carrier is terminal `executed` even though ``repo`` still shows it in `pending/`.

    WHY THIS NARROW ESCAPE HATCH EXISTS, and why it is not a hole. OQ-01 resolved that eligibility is
    evaluated in MAIN, because the question "have ALL carriers of this item proved the work?" is a
    claim about SEVERAL plans and carrier discovery scans the FILESYSTEM (F-6), so only main's view
    sees every sibling's true bucket. But the runner now performs the item's MOVE inside the lane,
    BEFORE the merge, and at that instant main legitimately still shows THIS run's own plan in
    `pending/` -- so a literal main-only evaluation would refuse EVERY close, forever, and would do so
    silently (the run summary would simply list the item as left open). Measured pre-fix, the close
    ran AFTER the merge, which is exactly how main came to show the plan executed; moving the write
    earlier means that one fact must now be supplied explicitly rather than read.
    A WORKER MAY ASSERT FACTS ABOUT ITS OWN ITEM, which is the same role rule `retire_orchestrator`
    enforces from the other side. So the override is deliberately limited to the caller's OWN
    just-finalized plan, and it is a MAPPING rather than a set so the verdict can cite the path the
    carrier REALLY occupies (its `executed/` path) instead of main's stale `pending/` one, which would
    be a false citation. SIBLING carriers are still read from ``repo`` with no override, so the
    multi-carrier protection F-5/F-12 measured (21 of 108 carried items have more than one carrier,
    the tail running 9, 6, 5) is untouched: an item whose sibling has not run still does not close.
    Defaults to None, so every caller that does not pass it behaves exactly as before.
    """
    from agent_workflows import check_engine as _ce

    overrides = dict(executed_overrides or {})
    earned = {p for p in earned_paths if p}

    try:
        item_path = resolve_backlog_item(repo, item_id6)
    except Exception as exc:  # fail closed: an unreadable backlog tree closes nothing
        return BacklogCloseVerdict(
            False, f"backlog item lookup failed: {exc}", None, None
        )
    if item_path is None:
        return BacklogCloseVerdict(
            False, f"no backlog item resolves to id6 {item_id6}", None, None
        )
    status = item_path.parent.name
    if status == "done":
        return BacklogCloseVerdict(False, "item is already done", None, None)

    # THE ONE SHARED LOOKUP (E-02). `find_from_backlog_artifacts` already returns every PLAN and
    # SPEC carrying the link, plans first. A second implementation here would be the same divergence
    # defect this repository keeps hitting, so there is deliberately no local scan.
    try:
        carriers = [
            Path(p) for p, _br in _ce.find_from_backlog_artifacts(repo, item_id6)
        ]
    except Exception as exc:  # fail closed
        return BacklogCloseVerdict(False, f"carrier lookup failed: {exc}", None, None)
    if not carriers:
        return BacklogCloseVerdict(
            False,
            f"no plan or spec carries From-Backlog: {item_id6}, so no carrier proves the work",
            None,
            None,
        )

    def _rel(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(Path(repo).resolve()))
        except ValueError:
            return str(path)

    def _cited(path: Path) -> str:
        """The path to CITE for a carrier: its overridden (real) location if one was supplied.

        The distinction matters because the citation becomes the `--evidence` argument, and
        `check_engine.resolve_evidence_artifact` must be able to RESOLVE it (F-11). Citing main's
        stale `pending/` path for a plan that actually sits in `executed/` would be a false citation
        of a file that does not exist where the claim says it does.
        """
        return overrides.get(_rel(path), _rel(path))

    ipds = [p for p in carriers if _carrier_kind(p) == CARRIER_KIND_IPD]
    others = [p for p in carriers if _carrier_kind(p) == CARRIER_KIND_OTHER]

    if ipds:
        # THE IPD RULE (E-02). The item promised code, so every IPD carrier must be terminal
        # `executed`; one unexecuted sibling is enough to hold the item open. This is why closing on
        # "my plan executed" is wrong: measured at authoring, `dh0uno` has TWO carriers, so that rule
        # would have closed it while half its work was unwritten.
        unexecuted: list[str] = []
        for plan in ipds:
            # dirtygates-03 (`9iq461`) E-03: the caller's OWN just-finalized plan is asserted
            # executed, because at this point in the run its move exists only on the lane branch and
            # `repo` still shows it in `pending/`. EVERY OTHER CARRIER IS READ FROM `repo` WITH NO
            # OVERRIDE, which is the whole point: main's view is the only one that sees a sibling's
            # true bucket, and a lane-side scan would see this plan executed and answer more
            # permissively than main would.
            if _rel(plan) in overrides:
                continue
            try:
                bucket = plan_bucket(plan)
            except Exception as exc:  # fail closed
                return BacklogCloseVerdict(
                    False,
                    f"terminal-state read failed for {_rel(plan)}: {exc}",
                    None,
                    None,
                )
            if bucket != "executed":
                unexecuted.append(_rel(plan))
        if unexecuted:
            return BacklogCloseVerdict(
                False,
                "IPD carrier(s) not executed: " + ", ".join(sorted(unexecuted)),
                None,
                None,
            )
        # E-04: the run must have EARNED it. The deciding carrier has to be one this run produced,
        # not one it found already finished. BOTH spellings of an overridden carrier's path count as
        # earned: `collect_earned_paths` derives its set from `git diff`, which reports the LANE's
        # post-move `executed/` path, while the carrier scan found the same plan at main's `pending/`
        # path. Testing only one spelling would refuse a close the run demonstrably earned.
        earned_ipds = [p for p in ipds if _rel(p) in earned or _cited(p) in earned]
        if not earned_ipds:
            return BacklogCloseVerdict(
                False,
                "this run executed none of its carriers, so the close was not earned "
                "(all carriers were already executed before this run)",
                None,
                None,
            )
        return BacklogCloseVerdict(
            True,
            "every IPD carrier is executed and this run executed "
            + ", ".join(sorted(_cited(p) for p in earned_ipds)),
            _cited(earned_ipds[0]),
            CARRIER_KIND_IPD,
        )

    # THE NON-IPD RULE (E-03). No IPD carrier means the item's requested output IS the artifact, so
    # existence is the whole test. Spec STATUS is not read here on purpose: a `draft`/`to-review`
    # spec still satisfies "create the spec", and its approval belongs to `aw specs`.
    existing = [p for p in others if p.is_file()]
    if not existing:
        return BacklogCloseVerdict(
            False, "no non-IPD carrier artifact exists on disk", None, None
        )
    earned_others = [p for p in existing if _rel(p) in earned]
    if not earned_others:
        return BacklogCloseVerdict(
            False,
            "this run created none of its carriers, so the close was not earned "
            "(all carrier artifacts existed before this run)",
            None,
            None,
        )
    return BacklogCloseVerdict(
        True,
        "the requested artifact(s) exist and this run created "
        + ", ".join(sorted(_rel(p) for p in earned_others))
        + " (no IPD carrier, so approval is not required)",
        _rel(earned_others[0]),
        CARRIER_KIND_OTHER,
    )


def run_earned_paths(state: dict[str, Any]) -> list[str]:
    """Every repo-relative path THIS run actually produced, across all attempts (E-04).

    Two sources, both derived from git or from the lifecycle rather than from a model claim:
    the per-attempt `changed_paths` (`git diff --name-only <starting_head>..<ending_head>`) and the
    executed plan's own post-finalize path. An older run directory carrying neither simply earns
    nothing, which fails closed."""
    earned: list[str] = []
    for item in state.get("queue", []) or []:
        for key in ("earned_paths",):
            for path in item.get(key) or []:
                if path and path not in earned:
                    earned.append(path)
    return earned


def collect_earned_paths(repo: Path, item: dict[str, Any]) -> list[str]:
    """The repo-relative paths one item's turn produced: its diff plus its finalized plan path.

    Best-effort by design (E-04 fails closed): a git failure yields fewer earned paths, which can
    only ever WITHHOLD a close, never manufacture one."""
    earned: list[str] = []
    attempts = item.get("attempts") or []
    for attempt in attempts:
        start = attempt.get("starting_head")
        end = attempt.get("ending_head")
        if not start or not end or start == end:
            continue
        try:
            out = run_checked(
                ["git", "diff", "--name-only", f"{start}..{end}"], cwd=repo
            )
        except (DriverError, OSError):
            continue
        for line in out.splitlines():
            path = line.strip()
            if path and path not in earned:
                earned.append(path)
    last_plan = item.get("last_plan_path")
    if last_plan:
        try:
            rel = str(Path(last_plan).resolve().relative_to(Path(repo).resolve()))
        except ValueError:
            rel = str(last_plan)
        if rel not in earned:
            earned.append(rel)
    return earned


def collect_lane_earned_paths(repo: Path, handle: Any) -> list[str]:
    """The repo-relative paths a LANE BRANCH produced (dirtygates-03 `9iq461` E-03).

    A one-line wrapper binding THIS host's `run_checked`, in the SAME shape as the other four
    injected-dependency wrappers in this module (`git_head`, `git_status`, `git_common_dir`,
    `build_lane_outcome`). The IMPLEMENTATION and the full rationale live in
    `runner_shared.collect_lane_earned_paths`; it is defined there, not here, so BOTH hosts reach it
    through `runner_shared` rather than one host importing it from the other (backlog `cnwy8g`).
    """
    return runner_shared.collect_lane_earned_paths(
        repo, handle, run_checked=run_checked
    )


def close_backlog_item(
    repo: Path, item_path: Path, item_id6: str, evidence: str, message: str
) -> tuple[int, str]:
    """Close a backlog item `done` through the LIFECYCLE-OWNED setter, never by editing the file.

    ``repo`` is the tree the setter operates on: it is where the item file MOVES and, inseparably,
    the ``repo_root`` the release-gate predicate evaluates against (see the warning below).

    THE `--status` SPELLING IS DELIBERATE AND LOAD-BEARING (zhr6mc D1). `aw backlog set <status>
    <selector>` (positional) dispatches to `status_set.run_set_command`, which does NOT run the
    shared release-gate close predicate and cannot even accept `--evidence`; `aw backlog set
    <selector> --status done` dispatches to `backlog.run_set`, which DOES call
    `check_engine.evaluate_blocking_close` and REFUSES an illegitimate blocking close. Verified live:
    a `graduated` item carrying `Blocks-Release: next` closed with NO evidence via the positional
    form (exit 0) and was REFUSED via this one. The runner must be gated, so it uses this form; do
    not "simplify" it back to the positional spelling.

    `--dir` IS NOT MERELY "WHERE THE FILE MOVES" (dirtygates-03 `9iq461` F-10/F-11). Because the
    gated route runs `check_engine.evaluate_blocking_close`, this ONE argument also chooses the tree
    that predicate scans for release-gate carriers (`check_engine.py`'s `done` branch calls
    `find_from_backlog_artifacts(repo_root, item_id6)`) and the tree its `--evidence` citation is
    resolved against (`resolve_evidence_artifact(repo_root, evidence)`). `backlog.run_set` derives
    both from the same `resolve_verb_repo_root(args.dir)`, so THE TWO CANNOT BE SPLIT FROM HERE: one
    `--dir` is one tree for the move AND the gate. That is why `process_backlog_close` performs the
    MOVE in the lane but takes the ELIGIBILITY decision against main BEFORE calling this, and why the
    evidence it cites is a path that resolves in the lane. Do not "simplify" this to a lane-only
    evaluation: in the lane this run's own plan already sits in `executed/`, so a lane-side carrier
    scan is MORE likely to find a satisfying carrier than main's, and the error direction is the
    permissive one -- a release-gated item could close `done` that main's view would refuse.
    """
    cmd = pinned_module_argv(
        [
            "backlog",
            "set",
            item_id6,
            "--status",
            "done",
            "--evidence",
            evidence,
            "--message",
            message,
            "--dir",
            str(repo),
            "--no-commit",
        ]
    )
    # Launched through the SHARED `run_checked` rather than a fresh `subprocess.run`: it already
    # carries the af7i6p tooling pin AND the ttywedge (g40w37) `stdin=DEVNULL` terminal denial, so this
    # close cannot become the one nested-`aw` site that wedges on a prompt nobody can answer. Its
    # nonzero contract is an exception, which is converted back to the (rc, message) pair the
    # fail-closed caller needs.
    try:
        return 0, run_checked(cmd, cwd=repo)
    except (DriverError, FileNotFoundError, OSError) as exc:
        return 1, str(exc).strip()


def commit_backlog_close(
    repo: Path,
    item_id6: str,
    message: str,
    *,
    run_id: str | None = None,
    plan_id6: str | None = None,
) -> str | None:
    """Path-scoped-commit the item file the setter just MOVED, via the shared tooled commit path.

    Returns the new commit sha, or None when nothing was committed.

    RUN OWNERSHIP TRAILERS (runtrailwire-01 `wao266` E-02/E-03). ``run_id`` is the live run's own id
    and ``plan_id6`` the queue item (plan) whose execution earned the close; both are threaded from
    the caller's `state`/`item` and formatted by the canonical `git_commit_helper.run_item_trailers`,
    never hand-built, so the `AW-Run`/`AW-Item` key spelling is single-sourced and cannot drift.
    KEYWORD-ONLY AND OPTIONAL BY DESIGN: `agy_runipd` imports this function BY NAME and both drivers
    must keep resolving the same object, so the existing three-positional call form stays valid.

    WITH NO RUN ID THE TRAILER IS OMITTED, NEVER SYNTHESIZED (E-03). `run_item_trailers` already
    skips an absent value and returns `[]` when both are absent, which `offer_commit` composes into a
    BYTE-IDENTICAL message, so the safe behavior is the default and needs no special case here. The
    tempting "improvement" is to synthesize an id from a timestamp or the plan id; do not. The whole
    value of an immutable trailer is that a later reader can TRUST it, so a trailer asserting run
    ownership it cannot substantiate is strictly worse than no trailer at all (the same discipline
    `h9cn0y` E-03 applies when it refuses to name a responsible sha it cannot substantiate).

    WHICH PATH STILL CALLS THIS (dirtygates-03 `9iq461` E-02): the NON-ISOLATED one only
    (`--no-isolate-worktree`), where the setter genuinely wrote into the shared checkout and leaving
    the move uncommitted would hand the next turn a dirty tree. AN ISOLATED TURN NO LONGER CALLS IT:
    its move happens in the lane and is swept up by the lane's own finalize commit, so it rides the
    merge and arrives on main as part of one ref update. Making a SECOND commit on main there would be
    the exact mid-run write to the shared checkout this plan removes. Kept, not deleted, because the
    non-isolated path is a supported escape hatch (orchestrator `8lfoum` OQ-01 resolved to keep it).

    WHY COMMIT AT ALL ON THAT PATH (zhr6mc D2): `aw backlog set` moves the file (graduated/ -> done/)
    and does not commit, so leaving it would hand the next turn a dirty main tree -- which the
    `z2isfg` begin-dirty gate and the `driverfin-03` dirty-overlap gate both consume, and which is
    precisely the contamination those gates exist to stop.

    WHY THIS HELPER: `git_commit_helper.offer_commit` snapshots the index BEFORE staging, stages only
    the explicit paths, commits only the intersection of those paths with what it itself staged, and
    on failure resets ONLY its own paths. That is the shared-checkout-safe path AGENTS.md prescribes;
    a raw `git add` here could sweep in a co-worker's staged work.

    The path set is filtered to entries whose BASENAME contains this item's id6, so a co-worker's
    concurrent edit to a DIFFERENT backlog item can never be swept into the runner's commit.
    """
    from agent_workflows import git_commit_helper as _gch

    # Only EXISTING backlog roots may be named. A pathspec that matches nothing makes `git status`
    # exit nonzero ("did not match any files"), which `run_checked` turns into a DriverError, which
    # this function suppresses -- so naming both layouts unconditionally made the commit silently
    # never happen in any repo with only one of them (i.e. every real repo). Measured live.
    roots = [
        rel
        for rel in (".aw/records/backlog", ".agents/backlog")
        if (Path(repo) / rel).exists()
    ]
    if not roots:
        return None
    try:
        # `-uall` is LOAD-BEARING. Git's default `--porcelain` collapses an untracked directory to the
        # DIRECTORY entry (`?? .aw/records/backlog/done/`), whose basename carries no id6, so the
        # id6 filter below silently matched nothing and the newly written item was never staged -- the
        # move committed as a bare deletion, or not at all. Measured live before this flag was added.
        # `-uall` lists the individual untracked FILE instead.
        porcelain = run_checked(
            ["git", "status", "--porcelain", "-uall", "--", *roots],
            cwd=repo,
        )
    except (DriverError, OSError):
        return None
    paths: list[str] = []
    for line in porcelain.splitlines():
        # PARSE THE STATUS FIELD, DO NOT SLICE A FIXED WIDTH. `run_checked` returns a `.strip()`ed
        # blob, so porcelain's leading space for an unstaged change is already gone: `" D <path>"`
        # arrives as `"D <path>"`, and a blind `line[3:]` then ate the path's own first character,
        # producing `aw/records/...` and a `git add` pathspec failure. Measured live. Splitting on the
        # first run of whitespace after the 1-2 char status code is width-independent.
        parts = line.strip().split(None, 1)
        if len(parts) != 2:
            continue
        raw = parts[1].strip()
        if not raw:
            continue
        # A rename/copy entry is `old -> new`; both sides belong to the same move.
        for candidate in raw.split(" -> "):
            candidate = candidate.strip().strip('"')
            if (
                candidate
                and item_id6 in Path(candidate).name
                and candidate not in paths
            ):
                paths.append(candidate)
    if not paths:
        return None
    # FAIL CLOSED on a partial view: the setter MOVES the file, so a legitimate close always yields
    # both sides (the deletion and the addition). Seeing only one means the porcelain view is not what
    # this function assumes, and committing half a move would leave the tree worse than not committing
    # at all. The item is already `done` on disk either way; the operator commits it.
    if len(paths) < 2:
        return None
    try:
        outcome = _gch.offer_commit(
            repo,
            paths,
            message=message,
            assume_yes=True,
            interactive=False,
            # RUN OWNERSHIP, MACHINE-READABLE AND IMMUTABLE (E-02/E-03). The canonical formatter, not
            # a hand-built string, so the key spelling lives in ONE place. Values come from the LIVE
            # run threaded in by the caller; when a caller has no run id (a hand-driven or test
            # invocation) this returns `[]` and the message composes BYTE-IDENTICALLY to today's.
            # NOTHING IS SYNTHESIZED to fill the gap: an absent trailer means UNKNOWN ownership, while
            # a fabricated one would be a false ownership claim in permanent history.
            trailers=_gch.run_item_trailers(run_id, plan_id6),
        )
    except Exception:
        return None
    return getattr(outcome, "commit", None)


def process_backlog_close(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    *,
    lane_repo: Path | None = None,
    lane_handle: Any = None,
) -> None:
    """After a plan reaches `executed`, close its backlog item if this run earned it (E-02/E-03/E-04).

    Records the verdict on the queue item either way, so E-06 can report every item left open WITH
    ITS REASON rather than merely noting that something did not happen.

    THE DECISION AND THE WRITE HAPPEN IN DIFFERENT TREES, DELIBERATELY (dirtygates-03 `9iq461`).
    ``lane_repo`` is the isolated turn's lane worktree, passed BEFORE the merge, and ``lane_handle``
    its `WorktreeHandle` (whose `base_commit..branch` range is where the turn's commits actually are).
    When both are None (a `--no-isolate-worktree` turn, or a post-merge caller) everything behaves
    exactly as it did before.

    WHY SPLIT THEM. The write must be in the LANE so the item's move rides the lane's finalize commit
    and reaches main through the SAME merge as the code: a merge is atomic, so the bookkeeping lands
    if and only if the work lands, and NOTHING is written to the shared checkout while the run is
    still going. That mid-run write is not a theoretical tidiness point -- measured 2026-09-13, one
    item's uncommitted close left main dirty and a whole-tree gate then refused 27 of 42, 23 of 41 and
    18 of 43 remaining queue items across three consecutive runs.
    The DECISION must be taken against MAIN (OQ-01, resolved) because it asks whether ALL carriers of
    the item prove the work. That is a claim about several plans, carrier discovery scans the
    FILESYSTEM (`find_from_backlog_artifacts`), and 21 of 108 carried items have more than one carrier
    (one has nine), so a lane-side evaluation could close an item whose sibling carrier never ran.
    The single fact the lane legitimately contributes -- "my own plan is executed" -- is passed
    explicitly as `executed_overrides`, which is a worker asserting a fact about its OWN item.
    """
    item_id6 = item.get("from_backlog")
    if not item_id6:
        return
    repo = Path(state["repo"])
    # THE TREE THE MOVE HAPPENS IN. `repo` for a non-isolated turn (unchanged behavior); the lane for
    # an isolated one, so the move is swept into the lane's commit and arrives via the merge.
    write_repo = Path(lane_repo) if lane_repo is not None else repo
    isolated = write_repo.resolve() != repo.resolve()
    # THE EARNED SET, AND THE TRAP IN IT (E-03; the plan's F-7, corrected by measurement).
    # `collect_earned_paths` diffs the ATTEMPT's `starting_head..ending_head`, and both of those are
    # MAIN's HEAD sampled around the turn. For an ISOLATED turn main's HEAD never moves, so that range
    # is `X..X` and yields NOTHING -- and because the earned gate can only ever WITHHOLD a close, the
    # visible symptom would not be an error but a close that silently never happens again. So the lane
    # branch's own range is added, which is where the work actually is. It is read with `cwd=repo`
    # deliberately: a linked worktree shares the object database and refs with its parent, so the range
    # resolves identically from either cwd (measured; the cwd was never the issue, the RANGE was).
    earned_paths = collect_earned_paths(repo, item)
    if isolated and lane_handle is not None:
        for path in collect_lane_earned_paths(repo, lane_handle):
            if path not in earned_paths:
                earned_paths.append(path)
    item["earned_paths"] = earned_paths
    overrides: dict[str, str] = {}
    if isolated:
        with contextlib.suppress(Exception):  # fail closed: no override = fewer closes
            overrides = lane_executed_carrier_override(repo, write_repo, item)
    try:
        # ELIGIBILITY AGAINST MAIN. `repo`, never `write_repo`.
        verdict = evaluate_backlog_close(
            repo,
            item_id6,
            run_earned_paths(state),
            executed_overrides=overrides,
        )
    except Exception as exc:  # fail closed: never let a close attempt break the run
        item["backlog_close"] = {
            "item": item_id6,
            "closed": False,
            "reason": f"close evaluation failed: {exc}",
        }
        return
    record: dict[str, Any] = {
        "item": item_id6,
        "closed": False,
        "reason": verdict.reason,
        "rule": verdict.rule,
        "evidence": verdict.evidence,
        # Recorded so an operator (and V-01) can tell from the run's own state WHICH tree performed
        # the write, rather than inferring it from the absence of a commit.
        "wrote_in": "lane" if isolated else "main",
    }
    if not verdict.close:
        item["backlog_close"] = record
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "backlog-item-left-open",
                "id6": item["id6"],
                "backlog_item": item_id6,
                "reason": verdict.reason,
            },
        )
        return
    # RESOLVE THE ITEM IN THE TREE THE MOVE WILL HAPPEN IN. A lane-side move driven by a main-side
    # path is exactly the half-state this plan removes.
    item_path = resolve_backlog_item(write_repo, item_id6)
    if item_path is None:  # fail closed (raced away between evaluation and close)
        record["reason"] = f"backlog item {item_id6} disappeared before the close"
        item["backlog_close"] = record
        return
    message = (
        f"closed by aw oc run: IPD {item['id6']} executed "
        f"({verdict.reason}); evidence {verdict.evidence}"
    )
    rc, out = close_backlog_item(
        write_repo, item_path, item_id6, verdict.evidence or "", message
    )
    if rc != 0:
        # E-04 fail-closed: a refused setter leaves the item ALONE and the refusal is the reason.
        record["reason"] = f"setter refused the close: {out or f'exit {rc}'}"
        item["backlog_close"] = record
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "backlog-close-refused",
                "id6": item["id6"],
                "backlog_item": item_id6,
                "detail": record["reason"],
            },
        )
        return
    record["closed"] = True
    # E-02: COMMIT IN THE TREE THE MOVE HAPPENED IN, WHICH IS THE WHOLE OF THE FIX.
    #
    # For an ISOLATED turn that is the LANE, so this commit lands on the lane BRANCH and reaches main
    # through the same merge as the code: no commit is made on main, which is what E-02 asked for. It
    # is a SEPARATE lane commit rather than part of the finalize commit, necessarily so -- the close
    # can only be evaluated once the plan IS `executed`, which is what finalize makes true, so it
    # cannot precede it. That costs nothing: both commits are on the lane branch, and a merge takes the
    # branch or nothing, so the maintainer's stated property holds exactly ("the move lands if and only
    # if the merge lands").
    #
    # AND THE COMMIT IS NOT OPTIONAL HERE. Leaving the move uncommitted in the lane would be worse than
    # the bug being fixed: `integrate_lane_branch` merges the BRANCH (`git diff base..branch`), so an
    # uncommitted change is not in the merge at all, and `teardown_lane_if_classified` then refuses to
    # tear down a lane holding a dirty tracked file -- so the close would be silently dropped AND the
    # lane stranded. For a NON-ISOLATED turn this is the pre-existing behavior, unchanged.
    #
    # AND IT CARRIES RUN OWNERSHIP (runtrailwire-01 `wao266` E-02). The ids come from the LIVE run's
    # own state and the queue item in hand -- `state["run_id"]` and `item["id6"]` -- never from a
    # global and never from a read of `.aw/records/runs/`, which is gitignored and absent from a lane
    # worktree. `state.get` rather than `state[...]` because a hand-built or legacy state may carry no
    # run id, and the correct answer there is an omitted trailer, not a KeyError mid-close.
    record["commit"] = commit_backlog_close(
        write_repo,
        item_id6,
        message,
        run_id=state.get("run_id"),
        plan_id6=item.get("id6"),
    )
    # SCOPED INTEGRITY SELF-CHECK, IMMEDIATELY AFTER OUR OWN WRITE (2026-09-22).
    #
    # WHY HERE AND NOT ONLY IN CI. A `_staged_paths` bug committed this very relocation as a bare
    # ADDITION, so the pre-move copy survived in HEAD beside its destination and the item held two
    # contradictory lifecycle states at once. 36 items were corrupted over two days. The CI gate that
    # catches it is correct and fired, but it speaks only after a push, and 143 commits landed on
    # `origin/main` while it was red. The runner KNOWS which id6 it just wrote, so checking that one
    # id6 costs one tree walk and reports at the moment of creation rather than two days later.
    #
    # IT REPORTS AND NEVER RAISES. The close is already committed by this point, so refusing would
    # leave the tree in exactly the same state while additionally killing the run; the useful act is to
    # make the corruption impossible to MISS. The fact lands in three places a later reader actually
    # consults: the item's own `backlog_close` record, the run's `events.jsonl`, and stderr.
    with contextlib.suppress(Exception):  # never let a self-check break a run
        claimants = backlog_item_paths_for_id(write_repo, item_id6)
        if len(claimants) > 1:
            record["integrity"] = {
                "rule": "attention.duplicate-id",
                "id6": item_id6,
                "paths": claimants,
                "detail": (
                    f"backlog item {item_id6} now exists at {len(claimants)} paths, so its lifecycle "
                    "state is contradictory; a relocation committed only half of its move"
                ),
            }
            append_jsonl(
                run_dir / "events.jsonl",
                {
                    "at": utc_now(),
                    "event": "backlog-close-integrity-violation",
                    "id6": item["id6"],
                    "backlog_item": item_id6,
                    "rule": "attention.duplicate-id",
                    "paths": claimants,
                },
            )
            sys.stderr.write(
                f"warning: backlog item {item_id6} exists at {len(claimants)} paths after its close "
                f"({', '.join(claimants)}); `aw attention` will report attention.duplicate-id and its "
                "board is NOT authoritative until this is repaired\n"
            )
    item["backlog_close"] = record
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "backlog-item-closed",
            "id6": item["id6"],
            "backlog_item": item_id6,
            "evidence": verdict.evidence,
            "rule": verdict.rule,
            "commit": record["commit"],
            "wrote_in": record["wrote_in"],
        },
    )
    print(
        Palette(should_color(sys.stdout))(
            f"  \u2713 backlog item {item_id6} closed done (evidence {verdict.evidence})",
            "green",
        )
    )


def unclosed_backlog_items(state: dict[str, Any]) -> list[tuple[str, str]]:
    """Every backlog item this run TOUCHED but did not close, as (item_id6, reason) pairs (E-06).

    Scope is deliberately this run's own work, not the whole repository (zhr6mc OQ-02): a run
    reporting on every open item would duplicate `aw attention`, which owns the cross-tree view. An
    item whose plan never reached the close evaluation is reported with that as its reason, so a
    linked item is never silently absent from the report.
    """
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in state.get("queue", []) or []:
        item_id6 = item.get("from_backlog")
        if not item_id6 or item_id6 in seen:
            continue
        record = item.get("backlog_close") or {}
        if record.get("closed"):
            seen.add(item_id6)
            continue
        reason = record.get("reason") or (
            f"IPD {item.get('id6')} ended {item.get('status', 'unknown')}, so the close was "
            f"never evaluated"
        )
        seen.add(item_id6)
        out.append((item_id6, reason))
    return out


def render_unclosed_report(state: dict[str, Any]) -> str:
    """The human-readable E-06 section, or '' when nothing is outstanding (print nothing then)."""
    outstanding = unclosed_backlog_items(state)
    if not outstanding:
        return ""
    pal = Palette(should_color(sys.stdout))
    lines = ["", pal("--- Backlog items left open ---", "bold")]
    for item_id6, reason in outstanding:
        lines.append(f"  - {pal(item_id6, 'yellow')}: {reason}")
    lines.append(
        pal(
            "  (this run's own items only; `aw attention` owns the cross-tree view)",
            "dim",
        )
    )
    return "\n".join(lines)


def render_runs_pointer(state: dict[str, Any]) -> str:
    """The E-07 trailing pointer. `aw runs <run-id>` is the real verb; `aw oc runs` does not exist."""
    return f"Run `aw runs {state.get('run_id', 'run-...')}` for more info."


def record_unclosed_backlog_items(run_dir: Path, state: dict[str, Any]) -> None:
    """LEDGER FIRST (E-06): append the unclosed-item record BEFORE anything is printed.

    Ordering is the whole point. A print can be truncated, redirected, or lost to an uncatchable
    kill; the ledger append survives all three, so `aw runs <run-id>` can still answer "what did it
    leave open?" when the terminal output cannot. Best-effort and never raising: this runs on the
    shutdown path, where an exception would be worse than a missing line."""
    outstanding = unclosed_backlog_items(state)
    if not outstanding:
        return
    with contextlib.suppress(Exception):
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "backlog-items-left-open",
                "items": [
                    {"item": item_id6, "reason": reason}
                    for item_id6, reason in outstanding
                ],
            },
        )


# --- bkclose (zhr6mc) E-05/E-06: the handler-safe shutdown report ---------------------------------
#
# WHY THIS IS A CALLABLE AND NOT A REGISTERED HANDLER (zhr6mc DEFERRED Q1).
#
# E-05 as authored asked this plan to install `signal.signal` handlers for SIGINT and SIGTERM in both
# runner modules. It may not, and the reason is recorded rather than worked around: FOUR executed
# plans installed guards that explicitly FORBID registering a handler (a `signal` `.signal(...)`
# call) in these two files
# (`tests/test_lane_allocation_idempotent.py`, `tests/test_runner_stop.py`,
# `tests/test_runner_stop_level3.py`, `tests/test_runner_stop_level4.py`), reserving that
# registration for `runstop` Phase 5 (`71vjbn`). One of those guards states the division of labor
# verbatim: "`runstop` Phase 5 (`71vjbn`, approved) OWNS SIGINT/SIGTERM registration in these same
# two files ... whichever plan registered last would silently win. This plan supplies the callable
# those handlers will invoke, and installs none itself."
#
# The designs are also incompatible, not merely double-registered: `71vjbn` E-01/E-02 require SIGINT
# to ESCALATE level 1 -> 3 -> 4 through `runner_stop.request_stop_nowait` and SIGTERM to REQUEST
# LEVEL 3, whereas E-05 here wanted both to report and let the process die of the signal. Seizing the
# registration would have deleted measured anti-deadlock protections (a handler deadlock plus a ~50%
# lost-escalation race) and pre-empted the next plan in the very same run queue.
#
# So this plan supplies exactly the callable the guard describes, and reaches SIGINT through the
# funnel that ALREADY exists (`except KeyboardInterrupt`), which needs no registration at all. When
# `71vjbn` lands its handlers, each must call `emit_shutdown_report()` before recording its stop
# request; that is a one-line addition inside handlers it is already writing.
#
# This is a SEPARATE mechanism from the escalating child-process kill sequence (the
# `(signal.SIGINT, _SIGINT_GRACE_SECONDS)` / `(signal.SIGTERM, _SIGTERM_GRACE_SECONDS)` loop in the
# shared reaper). That path signals CHILDREN and works; nothing about it is changed here.
#
# HANDLER DISCIPLINE, honored so `71vjbn` can call this from a real handler unchanged. Handlers run at
# arbitrary points between bytecodes, so this routine does not acquire the run lock, does not call
# `save_state`, and performs no blocking I/O beyond one ledger append and one print. It reads only
# state already in memory, and it is idempotent so a repeated signal neither double-prints nor hangs.

_SIGNAL_REPORT_STATE: dict[str, Any] = {}
_SIGNAL_REPORT_DONE = threading.Event()


def register_signal_report(run_dir: Path, state: dict[str, Any]) -> None:
    """Publish the run's in-memory state for the signal handlers to report from."""
    _SIGNAL_REPORT_STATE["run_dir"] = run_dir
    _SIGNAL_REPORT_STATE["state"] = state


def emit_shutdown_report(*, to_stderr: bool = False) -> None:
    """Write the unclosed-item record, then print it and the `aw runs` pointer. IDEMPOTENT.

    Idempotence is what makes a SECOND signal arriving mid-report safe: it neither double-prints nor
    deadlocks, it simply returns. `threading.Event` is used rather than a lock precisely because a
    handler must never block."""
    if _SIGNAL_REPORT_DONE.is_set():
        return
    _SIGNAL_REPORT_DONE.set()
    state = _SIGNAL_REPORT_STATE.get("state")
    run_dir = _SIGNAL_REPORT_STATE.get("run_dir")
    if not isinstance(state, dict) or run_dir is None:
        return
    stream = sys.stderr if to_stderr else sys.stdout
    with contextlib.suppress(Exception):
        record_unclosed_backlog_items(Path(run_dir), state)
    with contextlib.suppress(Exception):
        report = render_unclosed_report(state)
        if report:
            print(report, file=stream)
        print(render_runs_pointer(state), file=stream)


def signal_report_callback() -> Callable[[], None]:
    """THE callable `runstop` Phase 5 (`71vjbn`) must invoke from its SIGINT/SIGTERM handlers.

    Returned rather than registered, for the ownership reason recorded above: this plan may not call
    `signal.signal` in these modules. The returned function is handler-safe (no lock, no
    `save_state`, one ledger append plus one print) and idempotent, so `71vjbn` can call it first
    thing in each handler and then proceed to record its stop request.

    Prints to stderr, because a handler fires mid-run when stdout may be carrying streamed child
    output."""

    def _report() -> None:
        emit_shutdown_report(to_stderr=True)

    return _report


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
        print(file=sys.stderr)
        return None
    if not ready:
        print(
            f"\n  (no answer in {LANE_PROMPT_TIMEOUT}s; taking the automatic decision: {default_action})",
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
    """THE lane-reclamation decision, ONE implementation in `runner_shared` (`gqo6if` E-03).

    A HOST SHELL, NOT A SECOND BODY. The two drivers carried 73 `ast.unparse` lines each at 0.998
    host-token-normalised similarity, differing in ONE statement and only in its SPELLING, so the logic
    is shared and this keeps the original name, signature and defaults: every call site in this module
    and every test that drives `<driver>.reclaim_lanes_on_interrupt` is untouched.

    WHAT THE SHELL EXISTS TO INJECT, which is why this is a wrapper and not a bare re-export. The two
    prompt symbols stay PER HOST because `disable_lane_prompt` writes a module-level
    `_LANE_PROMPT_DISABLED` through `global` and THIS module's `_lane_reclaim_prompt` reads THIS
    module's copy. Binding the shared module's pair instead would set a flag nobody reads, silently
    breaking prompt suppression on a repeated interrupt. See the shared implementation's docstring and
    `tests/test_runner_shared.py::UnmovableSymbolTests`.
    """
    return runner_shared.reclaim_lanes_on_interrupt(
        repo,
        run_dir,
        state,
        interactive=interactive,
        reason=reason,
        lane_prompt=_lane_reclaim_prompt,
        disable_prompt=disable_lane_prompt,
    )


# `sync_receipt_into_worktree` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# integpath-02 (`6sb3yu`): the THREE lane-integration symbols below were defined in BOTH runners and
# had already drifted, so each of this Set's behavior changes would have had to be written twice. The
# implementations are now the single shared ones in `runner_shared`; these are one-line wrappers that
# keep the ORIGINAL name and signature, so every call site in this module is untouched. That is the
# same form the maintainer ruled for `run_checked` and the three git helpers (`818uru` OQ-02).
#
# EACH WRAPPER BINDS THIS HOST'S OWN VALUES, and the two kinds of binding are different:
#   * `run_checked` is an INJECTED DEPENDENCY - it takes an opencode-only `env_builder`, so shared
#     code cannot resolve it. Same reason as `git_head`/`git_status`/`git_common_dir`.
#   * `host_label` is the ONE value the two runners' `integrate_lane_branch` bodies actually differed
#     by. It lands in a merge commit subject on MAIN, so it identifies WHICH driver integrated a lane.
#     The shared function gives it NO DEFAULT on purpose; binding it here is what keeps this host's
#     git history saying `aw oc run` and not the other driver's name.


def build_lane_outcome(repo: Path, handle: Any, id6: str) -> Any:
    """Build this host's `orchestrate_isolation.LaneOutcome` for a finalized lane branch.

    integpath-02 (`6sb3yu`): the IMPLEMENTATION is the single shared `runner_shared
    .build_lane_outcome`; this wrapper binds THIS host's `run_checked`. See the note above.
    """
    return runner_shared.build_lane_outcome(repo, handle, id6, run_checked=run_checked)


def evaluate_clean_base_for_launch(
    repo: Path, *, shared_tree: bool = False
) -> lane_containment.CleanBaseResult:
    """lanectn Order 02 (`nna8yz`) E-05, spec R5.4: is `repo` a complete base for an unattended turn?

    hostdedup Order 01 (`li44r9`): now a thin wrapper. ONE definition lives in `runner_shared`, which
    every host reaches, so no host can drift from the rule (CID-3). The previous docstring said the
    rule was shared because "the agy twin calls it with its own runner", which named one particular
    host and would read as false the moment a third host exists; the property that actually matters is
    that there is one body and every host reaches it.

    The shared definition supplies the git runner and the `--untracked-files=no` scope; the RULE is
    `lane_containment.evaluate_clean_base`. See that function for why untracked files are excluded and
    for how this differs from the integration-time `dirty_tree_overlap` above.

    `shared_tree` is PASSED THROUGH, never interpreted (dirtybase `3i0aaz` E-03). It selects which
    true refusal sentence the shared rule produces - a `--no-isolate-worktree` turn is not isolated
    and omits nothing, so the lane wording would be false for it - and it changes NOTHING about what
    counts as dirty. Deciding the message here would fork the rule (R6.1) and let the hosts drift on a
    containment guarantee (CID-3).
    """
    return runner_shared.evaluate_clean_base_for_launch(repo, shared_tree=shared_tree)


def integrate_lane_branch(
    repo: Path, handle: Any, id6: str, validation_runner: Any
) -> tuple[bool, str, str]:
    """Integrate a verified lane branch back to main behind the REUSED integration gate.

    integpath-02 (`6sb3yu`): the IMPLEMENTATION is the single shared `runner_shared
    .integrate_lane_branch` (which carries the full contract in its docstring: the dirty-tree refusal,
    the gate call, `--ff-only` then the controlled `--no-ff` fallback, the abort that leaves main
    clean, and the three returned `kind` values). This wrapper binds THIS host's `run_checked` and its
    OWN `host_label`, so the merge subject on main still reads `integrate(aw oc run): ...`.

    dirtygates Order 05 (`ajxr5d`) E-03: it now also binds `action_kind="execute"` as a LITERAL, exactly
    as it binds `host_label`. THE SIGNATURE IS DELIBERATELY UNCHANGED, and that is the point:
    `tests/test_runner_shared.py::LaneIntegrationExtractionTests
    ::test_each_wrapper_keeps_the_ORIGINAL_signature` asserts each wrapper's kwonly list is EMPTY with
    the docstring "no wrapper may expose the injected parameter", and adding `*, action_kind: str` here
    was MEASURED to fail it. The review path calls `integrate_review_lane_branch` below rather than
    reaching around either wrapper, so no existing call site changes.
    """
    return runner_shared.integrate_lane_branch(
        repo,
        handle,
        id6,
        validation_runner,
        host_label="aw oc run",
        run_checked=run_checked,
        action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
    )


def integrate_review_lane_branch(
    repo: Path, handle: Any, id6: str
) -> tuple[bool, str, str]:
    """Integrate a REVIEW lane back to main: one merge, no revalidation (`ajxr5d` E-03, OQ-01).

    THE SIBLING WRAPPER, not a second implementation. Steps 0 and 2-4 of the shared function (the
    dirty-overlap guard, the ff-only-then-no-ff merge sequence, the capture-conflicted-paths-BEFORE-abort
    ordering, the `host_label` merge subject) are the SAME code an execute integration runs; only the
    revalidation gate is skipped, and it is skipped by NOT RUNNING rather than by any fabricated verdict.

    `validation_runner` IS NOT A PARAMETER HERE, and its absence is the contract made structural. There
    is no runner to pass because there is nothing to validate: a review's whole output is the plan under
    review plus its review record. `None` is handed to the shared function, which for `action_kind
    ="review"` never touches it. A caller therefore CANNOT supply a synthetic validation result through
    this path even by mistake, which is what OQ-01's load-bearing line requires.
    """
    return runner_shared.integrate_lane_branch(
        repo,
        handle,
        id6,
        None,
        host_label="aw oc run",
        run_checked=run_checked,
        action_kind=runner_shared.INTEGRATION_ACTION_REVIEW,
    )


def retry_deferred_integrations(
    run_dir: Path,
    state: dict[str, Any],
    *,
    poll: bool = False,
    ask: bool = False,
) -> list[dict[str, Any]]:
    """integpath-03 (`51vw4y`) E-03/E-04/E-05: re-attempt this host's DEFERRED integrations.

    A thin adapter: the LADDER is the shared `runner_shared.reattempt_deferred_integrations`, and this
    binds the four things that are host-specific - this host's `integrate_lane_branch` wrapper (which
    carries its own `host_label`, so a re-attempt's merge commit still names the right driver), its
    validation runner, its lane-handle reconstruction, and what "finished" means here.

    THE LANE HANDLE IS REBUILT FROM DURABLE STATE, not held in memory. A re-attempt happens in a LATER
    dispatch-loop iteration than the turn that deferred it, so the `WorktreeHandle` from that turn is
    long out of scope; the `preserved_*` fields the shared preservation emitter already writes are what
    make the lane findable again, which is exactly what they exist for.

    `i4ak5n` E-04/E-06: IT NOW BINDS A SECOND, REVIEW-ACTION PAIR, because the ladder was ACTION-BLIND
    and the pair below is EXECUTE-specific in two ways that would corrupt a review. `_integrate` reaches
    this host's execute wrapper, which pins `action_kind=execute` and is therefore exactly what triggers
    the merge-and-revalidate gate a review must skip BY NOT RUNNING (`ajxr5d` OQ-01); and `_finish`
    writes `status = "executed"`, closes a backlog item and resolves a plan path, none of which is valid
    for a turn that executed no plan. The review pair is `integrate_review_lane_branch` (which takes NO
    validation runner at all, so a synthetic verdict is structurally impossible) plus the SHARED
    `runner_shared.finish_integrated_review_item`. Which pair an item gets is decided by the shared
    `integration_action_for_item`, so the two hosts cannot disagree about it.
    """

    from agent_workflows import worktree_lease

    repo = Path(state["repo"])

    def _handle_for(item: Any) -> Any:
        branch = item.get("preserved_branch")
        worktree = item.get("preserved_worktree")
        if not branch:
            return None
        rc, _out, _err = _run_git(repo, ["rev-parse", "--verify", str(branch)])
        if rc != 0:
            return None
        return worktree_lease.WorktreeHandle(
            lane_id=str(item.get("preserved_lane_id") or item.get("id6") or ""),
            path=Path(worktree) if worktree else Path(""),
            branch=str(branch),
            base_commit=str(item.get("preserved_base") or ""),
        )

    def _integrate(item: Any, handle: Any) -> tuple[bool, str, str]:
        # integearn-03 (`daexj1`) E-03: pass THIS host's `run_suite_check` so the gate's revalidation
        # step measures the merge result instead of returning a constant True.
        return integrate_lane_branch(
            repo,
            handle,
            str(item.get("id6") or ""),
            make_integration_validation_runner(
                state, run_dir, item, suite_check=run_suite_check
            ),
        )

    def _finish(item: Any, handle: Any, reason: str) -> None:
        """The success path for a lane that integrated on a RE-attempt.

        It mirrors the first-attempt success path deliberately: the plan is already in `executed/` on
        the lane branch (finalize ran during the original turn), so what remains is to record
        `executed`, tear the lane down through the SHARED containment gate (never
        `teardown_isolation_worktree` directly, which force-deletes branch and files), and close the
        backlog item, which is the one moment a run can know the last carrier landed.

        dirtygates-03 (`9iq461`): THE COMMON CASE NO LONGER CLOSES ANYTHING HERE. The original turn
        already attempted the close IN ITS LANE (right after finalize, before integration), so an
        eligible item's move is on the lane branch and arrives with THIS merge; the guard below then
        skips, and no write reaches the shared checkout. The call is kept for the one case it still
        answers -- an item that was NOT eligible during the original turn (e.g. a sibling carrier had
        not executed yet) and may be eligible now -- which is pre-existing behavior and is left intact
        rather than silently dropped. HONEST LIMIT, recorded rather than hidden: in that narrow case
        the close does still write to main mid-run, because the lane is torn down above and there is no
        lane left to write in. Removing that last case needs a coordinator-owned throwaway worktree,
        which is Order 04's mechanism and deliberately outside this plan's scope.
        """
        item["status"] = "executed"
        item["integrated"] = reason
        attempts = item.get("attempts") or []
        if attempts:
            attempts[-1]["disposition"] = "executed"
            attempts[-1]["integrated"] = reason
        decision = lane_containment.teardown_lane_if_classified(
            repo=repo, handle=handle, run_dir=run_dir, item=item
        )
        if not decision.torn_down:
            lane_containment.record_lane_preserved(
                run_dir=run_dir,
                item=item,
                handle=handle,
                reason=decision.reason,
                reason_codes=decision.reason_codes,
                detail=decision.inventory.as_dict(),
            )
        else:
            for key in (
                "preserved_worktree",
                "preserved_branch",
                "preserved_lane_id",
                "preserved_base",
                "preserved_reason",
                "preserved_retention_reasons",
            ):
                item.pop(key, None)
        with contextlib.suppress(DriverError):
            item["last_plan_path"] = str(
                resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])
            )
        save_state(run_dir, state)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "ipd-integrated-after-deferral",
                "id6": item.get("id6"),
                "setid": item.get("setid"),
                "integration": reason,
                "attempts_used": item.get("integration_attempts"),
            },
        )
        print(
            Palette(should_color(sys.stdout))(
                f"  \u2713 IPD {item.get('id6')} integrated to main on a deferred re-attempt "
                f"({reason})",
                "green",
            )
        )
        # Skip when the lane-side close already succeeded: re-evaluating would answer
        # `item is already done` (close=False) and OVERWRITE the success record with a refusal, so a
        # correct close would be reported to the operator as "left open".
        if not (item.get("backlog_close") or {}).get("closed"):
            process_backlog_close(run_dir, state, item)
        save_state(run_dir, state)

    def _integrate_review(item: Any, handle: Any) -> tuple[bool, str, str]:
        """THE REVIEW-ACTION MERGE: `action_kind=review`, and no validation runner exists to pass.

        The same wrapper the FIRST attempt uses, which is the whole point: the retry must not reach a
        different merge path than the attempt it is retrying. Its signature takes no `validation_runner`,
        so this cannot hand the gate a synthetic verdict even by mistake (`ajxr5d` OQ-01).
        """
        return integrate_review_lane_branch(repo, handle, str(item.get("id6") or ""))

    def _finish_review(item: Any, handle: Any, reason: str) -> None:
        """THE REVIEW SUCCESS PATH, delegated to the shared performer.

        NOT `_finish`: a review claims no `executed`, closes no backlog item, resolves no plan path, and
        above all NEVER tears the sweep lane down (OQ-02 option (a), maintainer 2026-09-18 - the lane is
        shared by every review in the run, so retirement stays coordinator-owned and once-per-run).
        Shared rather than written here so the agy twin cannot drift from it.
        """
        pal = Palette(should_color(sys.stdout))
        runner_shared.finish_integrated_review_item(
            run_dir=run_dir,
            state=state,
            item=item,
            handle=handle,
            reason=reason,
            save_state=save_state,
            append_jsonl=append_jsonl,
            report=lambda message: print(pal(message, "green")),
        )

    return runner_shared.reattempt_deferred_integrations(
        repo=repo,
        run_dir=run_dir,
        state=state,
        integrate=_integrate,
        finish_integrated=_finish,
        integrate_review=_integrate_review,
        finish_integrated_review=_finish_review,
        save_state=save_state,
        append_jsonl=append_jsonl,
        handle_for=_handle_for,
        # integearn-03 (`daexj1`) E-03: carry the host's suite checker here too, so a DEFERRED
        # integration re-attempt revalidates on the same terms a first attempt does.
        validation_runner_for=lambda item: make_integration_validation_runner(
            state, run_dir, dict(item), suite_check=run_suite_check
        ),
        poll=poll,
        interactive=runner_shared.is_interactive_run(
            argparse.Namespace(
                unattended=bool((state.get("options") or {}).get("unattended")),
                full_auto=bool((state.get("options") or {}).get("full_auto")),
            )
        ),
        ask=ask,
    )


def _integrate_stranded_lanes(
    run_dir: Path, state: dict[str, Any]
) -> list[dict[str, Any]]:
    """integpath-04 (`rl67b0`) E-03/E-04: this host's wiring for the resume-time integration pass.

    A thin adapter, exactly as `retry_deferred_integrations` above is: the DECISION (which items
    qualify, the refusals, the real validation runner, the gate call, the honest state write, the
    hold-back) is the shared `runner_shared.integrate_stranded_lanes`. This binds only the four
    host-specific things:

      * this host's `integrate_lane_branch` wrapper, so a recovered merge subject on MAIN still reads
        `integrate(aw oc run): ...` rather than the other driver's name;
      * this host's `run_suite_check`, which the shared module MAY NOT IMPORT (a shipped AST test
        forbids `runner_shared` importing either driver, at module level or lazily), so it is injected;
      * `process_backlog_close`, injected for the same reason;
      * where the operator-facing lines go.
    """

    repo = Path(state["repo"])
    pal = Palette(should_color(sys.stdout))
    return runner_shared.integrate_stranded_lanes(
        repo=repo,
        run_dir=run_dir,
        state=state,
        integrate=integrate_lane_branch,
        suite_check=run_suite_check,
        save_state=save_state,
        append_jsonl=append_jsonl,
        process_backlog_close=process_backlog_close,
        report=lambda message: print(pal(message, "cyan"), file=sys.stderr),
    )


# `make_integration_validation_runner` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# hostdedup Order 01 (`li44r9`) E-02/E-03: `run_lock` and `locked_run` now have ONE definition each in
# `runner_shared`, and each host keeps a thin wrapper at the original name and signature.
#
# BOTH ARE CONTEXT MANAGERS, so the wrapper shape needs one word of explanation. A wrapper that merely
# RETURNED the shared call would be a plain function returning a context manager, which behaves
# identically at every `with` site but is no longer a `@contextlib.contextmanager` generator; a wrapper
# that re-`yield`ed inside its own `@contextlib.contextmanager` would nest two context managers and
# double the teardown path. `contextlib.contextmanager` already returns a re-usable factory, so
# delegating with a bare `return` is both the thinnest and the most faithful form: the yielded handle,
# the `finally` release ORDERING (handle before platform lock) and exception propagation are the shared
# definition's, unchanged.


def run_lock(run_dir: Path):
    """Hold the run's ``driver.lock`` for this driver process.

    Thin wrapper over the ONE definition in `runner_shared`, which holds the full rationale for the
    `platform_lock` acquisition, the ``dup``ed-descriptor ``pid=`` write and the observable release
    (spec `c4gd2h` R2, IPD `y6mfgo`).
    """
    return runner_shared.run_lock(run_dir)


def locked_run(run_dir: Path):
    """Hold the run lock AND guarantee the shared clean shutdown when the scope ends.

    Thin wrapper over the ONE definition in `runner_shared`, which holds the full rationale for why
    this layer -- and not a per-turn launch handler -- is the only scope that can satisfy all four
    clean-shutdown invariants (spec `c4gd2h` R1-R4, R6, R23).
    """
    return runner_shared.locked_run(run_dir)


# rununify 06 (`sy7uwh`) E-02/E-03: `_read_kind`, `_read_item_dependencies`, `PlanRecord` and
# `parse_plan_file` are IMPORTED from `runner_shared`, not defined here. All four used to live in THIS
# module, with `agy_runipd` importing the two readers FROM here (three oc-to-agy imports removed by the
# move) and carrying its OWN divergent `PlanRecord`/`parse_plan_file`. There is now ONE of each, so the
# two hosts cannot come to disagree about what a plan record IS.
#
# WHY THE RECORD COULD BE UNIFIED AT ALL, since `818uru` deliberately pinned it as un-unifiable: the
# reason it gave (agy had no use for `kind`) has DISSOLVED. agy imports the shared `action_for`, which
# READS `kind` to detect an orchestrator, so the split had come to cost a redundant disk read per plan
# and buy nothing. Measured: oc's field set was a strict SUPERSET of agy's, differing in exactly `kind`,
# and the two `parse_plan_file` bodies differed in exactly the two lines that read and pass it.
#
# `_read_from_backlog` STAYS DEFINED HERE, deliberately and only for now: it is re-exported to agy by
# name and is pinned by `tests/test_runner_backlog_close.py::SharedNotCopied`, which asserts object
# identity between the hosts. Lifting it is a `cnwy8g` reduction for a later child, and the shared
# module carries its own copy for `parse_plan_file`'s use; this module keeps binding its OWN so that
# suite's identity assertion still names one object. See the note at the shared definition.
# (The import itself is hoisted to the top-of-file shared-import block, per E402.)


# rununify 02 (`818uru`) E-08: one-line wrapper over the shared `discover_plans`, binding
# `parse_plan_file`.
#
# THE INJECTION IS NOW VESTIGIAL, and saying so plainly matters because the comment this replaces
# asserted the opposite as a design principle. `818uru` wrote that "the two drivers' `PlanRecord` are
# DIFFERENT NamedTuples (oc's carries a `kind` field agy's lacks)" and that "injecting the PARSER keeps
# each driver's own record type". rununify 06 (`sy7uwh`) unified BOTH the record and the parser, so
# there is exactly one of each and this wrapper now injects the SHARED `parse_plan_file` - the same
# object the agy wrapper injects. Nothing is kept apart any more.
#
# WHY THE PARAMETER STAYS ANYWAY, so nobody "finishes" this and breaks a guard: `discover_plans`'s
# signature is fingerprint-pinned in `tests/fixtures/runner_shared_premove_fingerprints.json` and
# enumerated in `tests/test_runner_shared.py::INJECTED`, and the maintainer's wrapper ruling exists
# specifically to leave call sites untouched. Collapsing the seam is a later plan's work, not a
# side effect of unifying a record.
def discover_plans(repo: Path) -> dict[str, PlanRecord]:
    """Scan the repository for all IPD files, returning id6 -> PlanRecord."""
    return runner_shared.discover_plans(repo, parse_plan_file=parse_plan_file)


# rununify 02 (`818uru`) E-08: one-line wrapper over the shared `validate_manifest`, binding
# `parse_dependency_token` (opencode-owned; the token grammar has ONE definition by design).
def validate_manifest(manifest: dict[str, Any]) -> None:
    runner_shared.validate_manifest(
        manifest, parse_dependency_token=parse_dependency_token
    )


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


# rununify 06 (`sy7uwh`) E-03: `build_dynamic_manifest` is IMPORTED from `runner_shared` (see the
# import block beside `PlanRecord` above), not defined here. The two hosts' versions differed in
# exactly ONE expression - `'kind': rec.kind` here versus `'kind': _plan_kind(rec.path)` there - so
# unifying the record collapsed this symbol for free, with oc's form surviving because it was already
# the one in production on this host.


def expand_selectors(
    manifest: dict[str, Any],
    selectors: Iterable[str],
    repo: Path | None = None,
    types: Any = None,
) -> list[str]:
    """Resolve selector tokens (id6, setid, file paths, or 'all') against the manifest and repo.

    `types` (specsweep-01 `ui8b9b` E-02) is the operator's `--type` set, honored by the REVIEW sweep
    only. It is KEYWORD-OPTIONAL and defaults to `None`, which `resolve_run_types` reads as the
    normative IPD-only default, so every existing call site (including the shipped tests that call
    this with three positional arguments) keeps its exact behavior.
    """
    plans = manifest.get("plans", {})
    sets = manifest.get("sets", {})
    selectors_list = [str(s).strip() for s in selectors]

    if len(selectors_list) == 1 and selectors_list[0].lower() in (
        "reviews",
        "review",
        "to-review",
    ):
        # revsweep-02 (`6ypimw`) E-02: THE SHARED membership test, replacing a `_needs_review` closure
        # that was a VERBATIM duplicate of agy's and that tested `status == "to-review"` while
        # `determine_action` (below) routed `to-review` AND `draft` to `review`. Spec 25kzda 2.4a
        # property 2 requires membership to BE the Section 3 dispatch table, implemented ONCE, "so an
        # item the table routes to review and an item the sweep selects are the same set BY
        # CONSTRUCTION". The shared function derives the answer from `run_selection_policy`'s action
        # table and reads plan text only for `draft` candidates, failing safe to NOT-swept.
        #
        # specsweep-01 (`ui8b9b`) E-02: ROUTED THROUGH THE TYPE-SCOPED ENTRY POINT, which for `ipd`
        # delegates to `sweep_review_candidates` VERBATIM (same manifest walk, same Set ordering, same
        # memoized decision), so a bare invocation's selection is unchanged. The agy twin does the
        # same; membership stays the ONE shared predicate and gains no second copy here.
        expanded = runner_shared.sweep_review_candidates_for_types(
            repo, types, manifest=manifest
        )

        if not expanded:
            # revsweep 76gsmv E-04: spec 25kzda 2.4a property 3. The message stays the same string
            # it always was, so any log-scraper still matches; only the TYPE changed, which is what
            # lets `main` exit 0 for the status selectors WITHOUT relaxing `DriverError` generally.
            raise EmptyStatusSelection(
                "No items in 'to-review' state found in repository"
            )
        return expanded

    if len(selectors_list) == 1 and selectors_list[0].lower() == "all":
        expanded: list[str] = []
        seen: set[str] = set()
        # setidsel (`7ap6ku`): `all` keeps its OWN, STRICTER test, and the difference from the
        # selector admission test below is deliberate rather than an oversight. `all` means "sweep
        # everything actionable", so it must additionally exclude a plan that is finished
        # (`executed`) or standing (`reusable`) or status-less, none of which anyone asked for by
        # name. A NAMED selector cannot use this stricter rule: an `executed` plan is a legitimate
        # queue member when a dependent declares `executed:<id6>` on it, and a status-less entry is
        # normal in a hand-written manifest. So the shared predicate refuses only the DELIBERATELY
        # RETIRED, and this branch narrows further on its own behalf.
        _is_actionable = runner_shared.manifest_entry_is_sweepable

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
    # setidsel (`7ap6ku`): every candidate DROPPED as already-finished, so an empty result can say
    # WHICH plans it skipped and why instead of claiming no selector was given.
    filtered_out: list[str] = []

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
                                "kind": rec.kind,
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

        # setidsel (`7ap6ku`): EVERY branch above converges here, which is why the admission test
        # belongs at this one point rather than repeated per branch. Before this, only the `all`
        # branch filtered, so naming a Set (the ordinary way an operator names work) queued its
        # RETIRED plans with a live `execute` action - measured at 587 terminal plans across 271 Sets.
        #
        # THE TWO SHAPES ARE DELIBERATELY DIFFERENT, and the discriminator is whether the operator
        # named THIS PLAN or named a CONTAINER that happens to hold it:
        #
        #   * A SET MEMBER is dropped SILENTLY. A Set is a topic label spanning a plan's whole
        #     history, so a mature Set legitimately holds executed and superseded members forever;
        #     refusing the Set because it contains its own finished work would make `aw oc run <set>`
        #     unusable for exactly the Sets that have made progress. Dropping is also what `all`
        #     already does, so the two selectors now agree.
        #   * AN EXPLICITLY NAMED PLAN (bare id6, filename, or file path) REFUSES LOUDLY. The
        #     operator typed that identifier, so silently expanding it to nothing would report
        #     "At least one id6 or Set selector is required" and leave them re-reading their own
        #     command line for a typo that is not there. Say which plan, what state it is in, and
        #     that the state is why.
        explicit_plan = matched_set is None and len(candidates) == 1
        for id6 in candidates:
            if id6 in seen:
                continue
            if not runner_shared.manifest_entry_is_selectable(plans.get(id6, {})):
                if explicit_plan:
                    info = plans.get(id6, {}) or {}
                    raise DriverError(
                        f"Plan {id6} is {str(info.get('status', '') or 'unknown')!r} and was "
                        f"RETIRED, so it cannot be run: "
                        f"{info.get('file', '(unknown path)')}. A retired plan "
                        f"({sorted(runner_shared.RETIRED_PLAN_STATUSES)}) is one whose work was "
                        f"deliberately decided against, so re-running it would implement a decision "
                        f"that was reversed. If it should run again, transition it out of its "
                        f"retired disposition first."
                    )
                filtered_out.append(id6)
                continue
            expanded.append(id6)
            seen.add(id6)

    if not expanded:
        # setidsel (`7ap6ku`): DISTINGUISH "you named nothing" from "everything you named is
        # finished", because the fix above made the second case COMMON (263 Sets in this repository
        # hold only terminal plans) and the old single message asserted the first, sending an
        # operator to hunt a typo in a selector that resolved perfectly well. Naming the dropped
        # plans is the whole point: it says the Set was found, what was in it, and why none of it ran.
        if filtered_out:
            detail = ", ".join(
                f"{i} ({(plans.get(i) or {}).get('status', '') or 'unknown'})"
                for i in filtered_out
            )
            raise DriverError(
                f"Every plan the selector(s) matched was RETIRED, so there is nothing to run: "
                f"{detail}. A retired plan "
                f"({sorted(runner_shared.RETIRED_PLAN_STATUSES)}) is one whose work was "
                f"deliberately decided against. This is not a selector typo: the plans were found "
                f"and deliberately skipped."
            )
        raise DriverError("At least one id6 or Set selector is required")
    return expanded


# orchretire-03 (`pgq326`) E-04: `determine_action` and `action_for` MOVED to `runner_shared` and are
# imported at the top of this module, so BOTH hosts bind the same objects. Do NOT reintroduce a local
# copy here; `tests/test_orchestrator_retirement.py::TheActionDecisionIsSHAREDCode` fails if you do.


# revsweep 76gsmv E-03: the `--action` vocabulary spec 25kzda 2.1 declares. `review` is IMPLEMENTED
# here; `plan` and `execute` are REGISTERED so the flag's grammar matches the spec, and then REFUSED
# honestly, because their legality tables (2.6: `plan` only for an approved spec or open backlog
# item, `execute` only for approved/auto-approved/reusable IPDs) need per-type dispatch this Set has
# not built. Accepting them silently would be the worse failure: the operator would believe an action
# was constrained when nothing constrained it.
# rununify 04 (`tx6q0h`): relocated to `runner_shared`; re-exported for existing call sites.
ACTION_CHOICES = runner_shared.ACTION_CHOICES
ACTION_IMPLEMENTED = runner_shared.ACTION_IMPLEMENTED


# rununify 04 (`tx6q0h`): one-line wrapper over the shared definition. The safety content (spec
# 25kzda 2.6's three refusals) now has ONE implementation; only the `aw oc review` hint is per-host.
def enforce_requested_action(
    requested: str | None,
    items: list[tuple[str, str, str]],
) -> None:
    runner_shared.enforce_requested_action(
        requested, items, labels=runner_shared.OC_HOST_LABELS
    )


# Dependency findings that ABORT the whole run rather than failing one component. Spec 25kzda 2.10
# maps `check.ipd-dependency-ambiguous` to the `fatal` identity/type-ambiguity class, and 5.4 rule 1
# says "identity/type ambiguity aborts the run"; every other dependency finding fails only the
# affected graph component.
DEPENDENCY_FATAL_RULES = frozenset(("check.ipd-dependency-ambiguous",))


def _consuming_actions_for(plans: list[tuple[Path, str]]) -> dict[str, str]:
    """Map each selected plan's path to the action THIS run would take on it (`runner_shared.action_for`).

    Spec 25kzda 2.9 makes `executed:` satisfaction ACTION-DEPENDENT, so the shared evaluator needs to
    know which turn consumes each edge. Derived from the SAME `action_for(kind, status)` the queue
    builder uses, rather than a second local rule, so preflight and dispatch cannot disagree about
    what a plan's next action is. A plan whose kind/status cannot be read is simply OMITTED, which
    leaves the evaluator on its strict (execute) default: unreadable must never mean permissive.
    """
    from agent_workflows import ipd_lint as _lint

    out: dict[str, str] = {}
    for path, text in plans:
        try:
            fields = _lint.parse(text).meta_fields
            kind = (fields.get("Kind") or "").strip()
            status = (fields.get("Status") or "").strip()
        except Exception:
            continue
        # FAIL CLOSED, EXPLICITLY. Only a plan whose `- Status:` we actually READ may claim the
        # relaxed `review` reading. `action_for` happens to return `execute` for an empty status
        # today, but relying on that would make the safety of this gate depend on an unrelated
        # function's default; omitting the entry instead leaves the evaluator on its own strict
        # default, which is the behavior the tests pin.
        if not status:
            continue
        try:
            action = runner_shared.action_for(kind, status)
        except Exception:
            continue
        if action:
            out[str(path)] = action
    return out


def preflight_dependency_findings(
    repo: Path, plan_paths: list[Path], *, phase: str = "pre-execution"
) -> list[tuple[str, str, str]]:
    """Run the SHARED dependency evaluator over the selected plans. Returns [(location, rule, msg)].

    E-02 DELEGATES ENTIRELY: this calls `check_engine.evaluate_ipd_dependencies` with a BLOCKING
    phase and surfaces whatever it returns, naming the shared `check.ipd-*dependency*` rules. There
    is deliberately NO runner-local dependency policy here, and in particular NO runner-local branch
    for the MISSING-statement case.

    IT DOES pass the per-plan CONSUMING ACTION (`_consuming_actions_for`), which is an INPUT to the
    shared rules rather than a local policy: spec 25kzda 2.9 makes `executed:` satisfaction
    action-dependent, and the runner is the only caller that knows which turn it is about to take.
    The judgement still belongs entirely to the evaluator.

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
    drift = _ce.evaluate_ipd_dependencies(
        repo, phase=phase, plans=plans, actions=_consuming_actions_for(plans)
    )
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
4. Commit only files you changed, limited to the paths you name, through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change).
5. Never push to remote.
6. Write valid outcome JSON before exiting.
"""


def resolve_launch_profile(args: argparse.Namespace) -> runner_profiles.ResolvedLaunch:
    """Resolve THIS run's OpenCode launch identity once, before any durable side effect (E-02).

    Delegates the whole precedence decision to the Order-01 resolver
    (:func:`agent_workflows.runner_profiles.resolve`, executed plan `f2mrsw`) rather than forking
    profile parsing here, which this plan's execution contract item 2 requires. Precedence, highest
    first, is that resolver's: `explicit --model/--variant/--agent > named profile > per-runner
    default profile > host default`, applied PER FIELD, so `--variant high` on top of a profile does
    not drop the profile's model (the "direct override replaces whole profile" failure mode).

    `runner="oc"` is passed rather than `generic=True`: this is the OpenCode host command, so the
    runner is already known and must never be re-guessed from `default_runner` (that is Order 04's
    host-neutral dispatch, explicitly out of scope here).

    Every failure raises :class:`DriverError`, and this function is called BEFORE the run directory
    is created, so an unknown/wrong-runner/malformed configuration leaves NO run id, directory,
    events, or partial state. An ABSENT store is NOT a failure: `load()` returns an empty config with
    `present=False`, which resolves to the host default and preserves current behavior exactly
    (DECISION 18-3cm15q-D3).
    """

    requested = getattr(args, "profile", None)
    try:
        cfg = runner_profiles.load()
        return runner_profiles.resolve(
            cfg,
            runner="oc",
            profile=requested,
            model=getattr(args, "model", None),
            variant=getattr(args, "variant", None),
            agent=getattr(args, "agent", None),
            verify_with=getattr(args, "verify_with", None),
        )
    except runner_profiles.RunnerProfileError as exc:
        # Typed at the boundary, so the operator gets the resolver's exact diagnostic (which names the
        # known profiles, or the offending field) with the driver's exit-2 contract.
        raise DriverError(f"runner profile: {exc}") from exc


def resolve_launch_pair(
    args: argparse.Namespace,
) -> tuple[runner_profiles.ResolvedLaunch, runner_profiles.ResolvedLaunch | None]:
    """Resolve the EXECUTOR launch and the VERIFIER launch from ONE store read (`kgpptv` E-02).

    Returns ``(executor, verifier_or_None)``. ``None`` for the verifier means "reuse the executor's
    launch", which is what every run did before this field existed and is what an absent
    `verify_with` resolves to at every level.

    ONE STORE READ, deliberately. Two independent `runner_profiles.load()` calls would leave a
    window in which the file is edited between them, so a run could freeze an executor from one
    document and a verifier from another while recording ONE `config_digest` for both. Loading once
    makes the two records provably describe the same configuration, which is asserted below.

    ONE HOP (DECISION 06-kgpptv-D1): `executor.verify_with` names a profile, and that profile is
    resolved as a launch in its own right. The verifier profile's own `verify_with` is carried but
    INERT, so there is no chain to walk and a cycle is unreachable rather than merely detected.

    Called as the FIRST statement of `initialize_run`, so a dangling `verify_with` refuses before any
    run directory, event, or `state.json` exists (`3cm15q` F-13's guarantee, extended to this field).
    """

    try:
        cfg = runner_profiles.load()
        executor = runner_profiles.resolve(
            cfg,
            runner="oc",
            profile=getattr(args, "profile", None),
            model=getattr(args, "model", None),
            variant=getattr(args, "variant", None),
            agent=getattr(args, "agent", None),
            # hostdefault-02 (`ybkmzp`) E-03: the operator's TRI-STATE verification flag, threaded
            # into the EXECUTOR resolution so tier 1 registers as `explicit` and the stored
            # per-model choice reaches the run when the operator said nothing. `None` here means
            # SILENCE and must fall through to the profile store; it must never collapse to `False`,
            # which is why `start`'s `--validate` now defaults `None` like `resume`'s always has.
            validate=getattr(args, "validate", None),
            verify_with=getattr(args, "verify_with", None),
        )
        if executor.verify_with is None:
            return executor, None
        # NO `validate=` HERE, DELIBERATELY. This second resolution answers WHICH profile verifies,
        # never WHETHER one does (`docs/runner-profiles.md`: "IT SAYS WHICH, NOT WHETHER"). Threading
        # the flag in would let a verifier profile's own `validate` field re-decide the gate, which
        # is a second switch for one behavior and exactly what the tri-state chain exists to prevent.
        verifier = runner_profiles.resolve(
            cfg, runner="oc", profile=executor.verify_with
        )
    except runner_profiles.RunnerProfileError as exc:
        raise DriverError(f"runner profile: {exc}") from exc
    # Both launches came from ONE in-memory config, so this cannot fail; it is asserted rather than
    # assumed because a future refactor that re-read the store would silently break the guarantee
    # the two frozen records make by sharing a digest.
    if verifier.config_digest != executor.config_digest:
        raise DriverError(
            "runner profile: the executor and verifier launches were resolved from different "
            "configurations; refusing rather than freezing an inconsistent pair"
        )
    return executor, verifier


def launch_profile_record(
    resolved: runner_profiles.ResolvedLaunch,
) -> dict[str, Any]:
    """The durable `options.launch_profile` provenance object (E-03).

    Records WHICH configuration produced this run's launch and WHERE each field came from, so an
    operator reading `state.json` months later can distinguish an explicit flag from a named profile,
    a per-runner default, and the host default. `config_digest` is what makes a later edit to
    `runner-profiles.json` detectable rather than invisible.

    Contains NO credentials: only the model/variant/agent identifiers, the profile names, and the
    store path. `runner_profiles` stores no secrets by construction (its schema admits only
    `runner`/`model`/`variant`/`agent`/`validate`/`verify_with`/`execution_profile`, the last two
    being NAMES from vocabularies that module owns).
    """

    record: dict[str, Any] = {
        "requested": resolved.requested_profile,
        "applied": resolved.applied_profile,
        "runner": resolved.runner,
        "config_source": resolved.config_source,
        "config_present": resolved.config_present,
        "config_digest": resolved.config_digest,
        "model": resolved.model,
        "variant": resolved.variant,
        "agent": resolved.agent,
        # hostdefault-02 (`ybkmzp`) E-05: the resolved verification DECISION, recorded beside the
        # tier that produced it so `state.json` says both what was decided and who decided it. ONE
        # key, not two: the `provenance` mapping copied below ALREADY carries `validate`'s tier
        # (`explicit` / `profile` / `default-profile` / `defaults` / `shipped-default`), so
        # duplicating the tier here would create a second place for it to drift.
        #
        # A RUN CREATED BEFORE THIS CHANGE HAS NO SUCH KEY, so every reader of this record must read
        # it defensively; the shipped test that renders an older record must keep passing.
        "validate": resolved.validate,
        "provenance": dict(resolved.provenance),
    }
    # hardreach Order 01 (`n5qca5`) E-03: the resolved SANDBOX REQUEST, recorded in the provenance
    # object beside the fields it travels with. CONDITIONAL, matching `kgpptv`'s `verify_*` treatment:
    # a run that requested nothing freezes the record it always froze, byte for byte, so no existing
    # reader of `options.launch_profile` sees a new key it must learn.
    #
    # THIS IS THE AUDIT COPY, NOT THE READ PATH. `_apply_execution_profile` reads
    # `options["execution_profile"]`, which `initialize_run` writes beside this record; the value here
    # exists so an operator reading `state.json` can see WHICH profile asked and via which tier.
    if resolved.execution_profile is not None:
        record["execution_profile"] = resolved.execution_profile
    return record


def initialize_run(args: argparse.Namespace) -> Path:
    """Initialize a run, freezing queue items (including "from_backlog") and options via runner_shared.initialize_run_core.

    Freezes queue items with "from_backlog" and runs report_untracked_dirt_at_run_start.
    Evaluates __file__ in the runner module so driver identity attributes to this host.
    """
    # runprofile-03 (`3cm15q`) E-02: FIRST statement in the function, deliberately. The launch
    # identity is decided before the repository is even validated, so no ordering change can later
    # slip a durable write ahead of a refusal.
    # runprofile-06 (`kgpptv`) E-02: BOTH launches are resolved here in this same position.
    resolved_launch, resolved_verify = resolve_launch_pair(args)

    host_options = {
        "opencode": getattr(args, "opencode", "opencode"),
        "model": resolved_launch.model,
        "variant": resolved_launch.variant,
        "agent": resolved_launch.agent,
        "launch_profile": launch_profile_record(resolved_launch),
        # runverdict Order 07 (`w33lrl`) E-01/E-02: WHICH model incurred this run's cost and at WHAT
        # PRICES. Before this, `options.model` was `null` on a run where no `--model` was passed and
        # `launch_profile.provenance.model` read `host-default` ("nothing supplied it; pass no
        # argument"), which HONESTLY named the gap rather than filling it: the record said it did not
        # know. This resolves the host's own default and freezes the rate card in effect at launch,
        # with the config's DIGEST so a later `aw oc update-models` cannot silently reprice history.
        #
        # A SEPARATE KEY FROM `launch_profile`, DELIBERATELY. That record's `config_digest` covers
        # `runner-profiles.json`; this one covers the OpenCode config. Two files need two digests,
        # and overloading the existing key would break the shipped invariants that the executor and
        # verifier SHARE one profile digest and that it survives a resume unchanged.
        runner_shared.COST_ATTRIBUTION_KEY: runner_shared.cost_attribution_record(
            host="oc",
            model=resolved_launch.model,
            model_source=(resolved_launch.provenance or {}).get("model", ""),
            agent=resolved_launch.agent,
        ),
        **(
            {
                "verify_model": resolved_verify.model,
                "verify_variant": resolved_verify.variant,
                "verify_agent": resolved_verify.agent,
                "verify_launch_profile": launch_profile_record(resolved_verify),
                # `w33lrl` OQ-01: the VERIFIER launch gets its OWN snapshot. The two-model case is
                # live today (`--verify-with` ships), and one run-level field that silently described
                # only the executor would misattribute the verifier's cost the first time it is used.
                # CONDITIONAL, like its three siblings, so a run with no verifier profile freezes the
                # state it always froze.
                "verify_"
                + runner_shared.COST_ATTRIBUTION_KEY: runner_shared.cost_attribution_record(
                    host="oc",
                    model=resolved_verify.model,
                    model_source=(resolved_verify.provenance or {}).get("model", ""),
                    agent=resolved_verify.agent,
                ),
            }
            if resolved_verify is not None
            else {}
        ),
        # hardreach Order 01 (`n5qca5`) E-03: THE WRITER for the key `_apply_execution_profile` has
        # always read. Before this, `options["execution_profile"]` was set by NOTHING in the package
        # (its single occurrence outside the reader was a COMMENT), so `select_execution_profile`
        # returned "default" on every real invocation and the whole hardened branch below it was
        # unreachable in production even on a host whose EXECUTED probe reports it CAN enforce.
        #
        # THE EXISTING KEY, NOT A PARALLEL ONE. The reader, the closed vocabulary, and the fail-closed
        # resolver all already existed and are tested; this plan adds only a writer, and deliberately
        # changes nothing about what the sandbox does once selected.
        #
        # RESOLVED AT THE EXISTING SEAM, which is what makes it safe. `resolve_launch_pair` ran as the
        # FIRST statement of this function, before the run directory exists, so a malformed config
        # leaves no run id and no partial state; and this dict is FROZEN ONCE into `state.json`, so a
        # later edit to `runner-profiles.json` cannot change an in-flight run's sandbox posture.
        #
        # CONDITIONAL, so a run that requested nothing freezes byte-identically to what it froze
        # before this field existed. A `None` here would be a THIRD state the resolver does not have
        # (it reads absent and "default" identically) and would change every existing run's shape.
        #
        # OPENCODE ONLY BY CONSTRUCTION. `agy_runipd` contains zero references to `execution_profile`,
        # `host_sandbox_profile`, `runner_profiles`, `resolve_launch_profile` or `launch_profile`
        # (measured at execution HEAD), so it has no seam to carry this and an agy run SILENTLY
        # IGNORES a stored request rather than refusing it. That is degradation-by-omission, the very
        # thing `select_execution_profile` refuses by raising, so it is stated here and in
        # `docs/runner-profiles.md` instead of being left for an operator to discover. Making agy
        # refuse is a change to that host and is deliberately not smuggled in here.
        **(
            {"execution_profile": resolved_launch.execution_profile}
            if resolved_launch.execution_profile is not None
            else {}
        ),
        "auto": getattr(args, "auto", True),
        "validate": resolved_launch.validate,
        "no_audit": not resolved_launch.validate,
    }

    return runner_shared.initialize_run_core(
        args,
        host="oc",
        driver_path=Path(__file__),
        host_options=host_options,
        expand_selectors_fn=expand_selectors,
        enforce_dependency_preflight_fn=enforce_dependency_preflight,
        # depclosure 01 (`dhycim`): the closure asks THIS host's satisfaction predicate
        # whether an edge is already met, so it never adds a target adding cannot help.
        # INJECTED because `runner_shared` must import neither runner (two shipped guards
        # enforce that), and because one shared definition is what keeps the closure's
        # judgement identical to the dispatch-time re-check's.
        edge_satisfied_fn=edge_satisfied,
        set_plan_approved_fn=set_plan_approved,
        announce_run_order_fn=announce_run_order,
        is_plan_review_approved_fn=is_plan_review_approved,
        run_order_rationale_fn=run_order_rationale,
        write_report_fn=write_report,
        git_common_dir_fn=git_common_dir,
        parse_dependency_token_fn=parse_dependency_token,
        default_runbook_text=DEFAULT_RUNBOOK_TEXT,
        default_stall_timeout=DEFAULT_STALL_TIMEOUT,
    )


def render_launch_identity(state: dict[str, Any]) -> str:
    """One human line naming the run's frozen launch identity and WHERE each field came from (E-03).

    Shared by `write_report` and `print_status` so the two can never describe the same run
    differently. Reads only frozen state, never the profile store, so it renders the same string
    before and after `runner-profiles.json` is edited.

    Renders the provenance in parentheses per field, which is what lets an operator distinguish the
    four cases the plan requires them to tell apart: `explicit` (a flag), `profile` (the profile named
    with `as`), `default-profile` (the per-runner default), and `host-default` (nothing was
    configured, so no argument is passed and OpenCode chooses).
    """

    options = state.get("options", {}) or {}
    lp = options.get("launch_profile") or {}
    provenance = lp.get("provenance") or {}

    def field(label: str, value: Any) -> str | None:
        if not value:
            # An absent model/variant/agent is a DELIBERATE "pass no argument"; say so rather than
            # printing an empty value that reads like missing data.
            return f"{label}=(host default)" if label == "model" else None
        src = provenance.get(label)
        return f"{label}={value}" + (f" ({src})" if src else "")

    parts = [
        p
        for p in (
            field("model", options.get("model")),
            field("variant", options.get("variant")),
            field("agent", options.get("agent")),
        )
        if p
    ]
    requested, applied = lp.get("requested"), lp.get("applied")
    if requested:
        parts.append(f"profile={requested} (requested)")
    elif applied:
        parts.append(f"profile={applied} (default)")
    # runprofile-06 (`kgpptv`) E-03: name the VERIFIER's launch when the run froze a separate one,
    # so "which model checked this work" needs no `state.json` archaeology either. Emitted ONLY when
    # a verifier profile was configured, so the line is unchanged for every other run.
    vlp = options.get("verify_launch_profile") or {}
    if vlp:
        verify_bits = [
            f"verify-model={options.get('verify_model') or '(host default)'}"
        ]
        if options.get("verify_variant"):
            verify_bits.append(f"verify-variant={options['verify_variant']}")
        if options.get("verify_agent"):
            verify_bits.append(f"verify-agent={options['verify_agent']}")
        vsrc = (provenance.get("verify_with") or "").strip()
        applied_v = vlp.get("applied")
        if applied_v:
            verify_bits.append(
                f"verify-profile={applied_v}" + (f" ({vsrc})" if vsrc else "")
            )
        parts.extend(verify_bits)
    if not lp:
        # A run created before this field existed, or by a path that froze no snapshot. Say that
        # plainly instead of implying the identity is unknown.
        parts.append("profile=(none recorded)")
    return "; ".join(parts) if parts else "(host defaults)"


# rununify 04 (`tx6q0h`): one-line wrapper over the shared report renderer, binding THIS host's
# labels and its `render_launch_identity` (the `- Launch:` line stays OpenCode-only; on a host with no
# profile subsystem it would render `profile=(none recorded)` forever - plan `tx6q0h` OQ-01).
def write_report(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.write_report(
        run_dir,
        state,
        labels=runner_shared.OC_HOST_LABELS,
        render_launch_identity=render_launch_identity,
    )


# rununify 02 (`818uru`) E-06: one-line wrapper over the shared `save_state`, binding THIS driver's
# `write_report`. `write_report` is class (c) DIVERGED (the two drivers render different reports), so
# importing one into shared code would silently give BOTH drivers that one's format. Keeping the
# original name and signature is what leaves this module's 32 `save_state` call sites untouched.
def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.save_state(run_dir, state, write_report=write_report)


# `_SESSION_ID_KEYS` and `extract_session_id` are now defined ONCE in `runner_shared` and imported
# above (rununify 05 `ct4w0a`). `_event_session_id` stays HERE because it is oc-only, and it is the
# SECOND consumer of that shared tuple: it reads the same key list LIVE during the turn. The tuple
# widened from three keys to four when it was shared, which is INERT for this function because it
# hard-filters on a `ses_` prefix and a `conversation_id` value never carries one.


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


# `_findings_block_reason` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


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

    ``by_id`` IS DELIBERATELY UNREAD and is kept only so the two call sites and their tests need no
    edit. It used to carry the IN-RUN status shortcut for an `executed:` edge, which the maintainer
    removed on 2026-09-19 in favour of ONE authority: the plan's directory on disk. See the
    `edge.kind == "executed"` branch for the measured incident that shortcut caused. Do not
    reintroduce a read of it without that ruling being revisited.

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
        # spec 2.9: the target must be terminally executed with valid finalization evidence.
        #
        # THE DISK IS THE ONLY AUTHORITY, AND THE IN-RUN SHORTCUT THAT USED TO SIT HERE IS GONE
        # (maintainer ruling 2026-09-19: one check, not gates in depth). It read the dependency's
        # IN-MEMORY run status and accepted any member of `EXECUTION_SUCCESS_STATES`, which admits
        # `substantially-complete`. That status means finalize did NOT happen, so the plan is still in
        # `pending/` and - measured - its lane was never merged. The shortcut therefore reported an
        # edge SATISFIED at the same moment the runner recorded the dependency's work as unintegrated.
        #
        # MEASURED COST, run `run-20260919T194413Z-2056285`: `yaxr4i` finished
        # `substantially-complete` with its two commits living only on `aw/lane/yaxr4i`. `n4xq3l`
        # declares `executed:yaxr4i`, was told the edge was met, and was dispatched into a tree with
        # NONE of that work (`grep -c -- '--color' agent_workflows/cli.py` -> 0 in its lane). It
        # correctly refused and went `blocked`, cascading `dependency-blocked` to eight more items:
        # 2h 10m and $55.02 for nothing integrated.
        #
        # WHY DELETING IT LOSES NOTHING: the branch below already answers this question for every
        # target, in-queue or not, and its own reasoning is the one the ruling adopted - an execute
        # turn consumes its prerequisite's WORK, so the terminal directory is the right authority,
        # because `executed/` is exactly where `aw ipd finalize` puts a plan and a directory move is
        # harder to forge than a status field. An in-run dependency that genuinely finalized reaches
        # `executed/` on disk and satisfies the edge through that branch on the next dispatch check,
        # which the runner performs per item rather than once at queue build.
        #
        # THE REVIEW RELAXATION IS UNAFFECTED because it lives in the branch below, not here: a
        # review turn still accepts a `reviewed`/`approved` `- Status:` field, since reviewing plan B
        # against plan A needs A's TEXT and not A's code.
        #
        # Evaluated from frozen repository state, and that is UNCHANGED by the arrival of
        # `--with-dependencies` (depclosure 01, `dhycim`). The flag now ships
        # (`runner_shared.expand_dependency_closure`), but spec 25kzda :351 is explicit that it
        # "changes selection, not satisfaction semantics": it can put the target IN the queue before
        # freezing, which is a different run, and it grants no relaxation to the rule below. Without
        # the flag an unsatisfied external target still simply cannot be met in this run.
        try:
            dep_path = resolve_plan_path(repo, "", edge.id6)
        except DriverError as exc:
            return False, f"{tok}: {exc}"
        bucket = plan_bucket(dep_path)
        allowed = ("executed",) if is_exec else ("executed", "reviewed", "approved")
        # PRECEDENCE (depreview 03ie04 E-01, OQ-01): A TERMINAL DIRECTORY IS AUTHORITATIVE; for a
        # NON-TERMINAL directory the `- Status:` FIELD carries the readiness. The two signals answer
        # different halves of one question and only one of them carries information in each case.
        #
        # WHY THE DIRECTORY MUST WIN IN `executed/`, measured and not hypothetical: 24 of the 455
        # plans in `executed/` carry a `- Status:` that `read_front_matter_status` returns None for
        # (all 24 the MULTI-WORD `EXECUTED (approved ...)` form the reader documents as yielding
        # None). Every one of them satisfies an `executed:` edge today because the directory decides.
        # Making the field authoritative EVERYWHERE, or letting a None field override a terminal
        # directory, silently breaks all 24 at once. `aw ipd finalize` is what moves a plan into
        # `executed/`, so the move is the harder-to-forge signal, which is the same anti-fabrication
        # posture `reconcile_disposition` takes when it trusts the directory over an agent's outcome.
        # (The plan's review recorded "24 absent, 1 multi-word"; re-measured at execution the corpus
        # is 24 multi-word and 0 absent. The conclusion is unchanged, the census is not.)
        #
        # WHY THE FIELD MUST WIN IN `pending/`: readiness in this layout is a FIELD, not a directory.
        # A plan sits in `pending/` from `draft` through `to-review`, `reviewed` and `approved`, and
        # only a TERMINAL state moves it, so there are no `reviewed/` or `approved/` directories to
        # find. Reading the bucket alone therefore made the review-action relaxation above
        # UNREACHABLE: every non-terminal plan buckets as `pending`, which is in neither `allowed`
        # tuple, so a review turn refused exactly as an execute turn would (spec 25kzda 2.9's
        # review-action row, which requires no terminal execution evidence).
        #
        # `_read_status` is the reader the module ALREADY imports and ALREADY uses for this exact
        # comparison in `reconcile_disposition`'s review branch; do not substitute another. It
        # returns None for an ABSENT and for a MULTI-WORD status alike, and in a NON-TERMINAL
        # directory both must FAIL CLOSED, exactly as an unrecognized bucket does.
        #
        # THE ASYMMETRY BETWEEN THE TWO `allowed` TUPLES IS THE POINT AND MUST STAY VISIBLE. Only the
        # REVIEW tuple gains anything from reading the field, because only it accepts a non-terminal
        # state. An EXECUTE turn consumes its prerequisite's WORK, so a merely `reviewed` or
        # `approved` plan has produced nothing to consume and satisfying its edge would dispatch a
        # dependent against a base lacking the commits it depends on; for an execute edge the
        # terminal directory IS the right authority, since `executed/` is exactly where finalize puts
        # a plan, and the precedence rule above already yields that answer with no special case.
        # Spec 25kzda 2.9 makes this normative: the two rows "must stay distinguishable by the
        # consuming action and by nothing else: not by queue membership, not by which host is
        # running, and not by whether the target happens to be in the current run".
        #
        # The terminal-directory set is NOT re-listed here: it is the shared
        # `run_selection_policy.TERMINAL_DIRECTORY_SEGMENTS` predicate, so a layout change lands in
        # one place. Lazily imported for the same reason `ipd_schema` is below.
        from agent_workflows import run_selection_policy as _policy

        effective = bucket
        if bucket is not None and not _policy.is_in_terminal_directory(str(dep_path)):
            try:
                field = _read_status(dep_path.read_text(encoding="utf-8"))
            except Exception:
                field = None
            effective = field
        if effective not in allowed:
            return False, (
                f"{tok}: external target {edge.id6} is {effective!r} "
                f"(directory {bucket!r}), needs one of {list(allowed)} "
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
    """(satisfied, unsatisfied-dep-tokens). Shape UNCHANGED: `unsatisfied` stays a flat list[str].

    See :func:`dependency_status_detailed` for the additional per-dependency REASON map, which is a
    strictly additive companion so every existing consumer of the flat list keeps working.
    """
    satisfied, unsatisfied, _reasons = dependency_status_detailed(item, state)
    return satisfied, unsatisfied


def dependency_status_detailed(
    item: dict[str, Any], state: dict[str, Any]
) -> tuple[bool, list[str], dict[str, str]]:
    """As :func:`dependency_status`, plus a ``{dep_token: reason}`` map naming each ROOT CAUSE.

    COMBINES revgate Order 03 (7nkcgp) with 8guhs0 (lanetruth-03), which both rewrote this function.
    Resolved at merge time on the maintainer's decision to keep BOTH behaviors rather than pick a
    side: 8guhs0's typed-token parsing runs FIRST and its per-edge verdict is delegated to
    `edge_satisfied`, then revgate's findings gate and reason map are layered on the result.

    From 8guhs0: each dependency is a CANONICAL TYPED token, resolved through the shared grammar
    before use. This closes its finding F8 - the pre-8guhs0 code used each `dep` BOTH as a queue dict
    key and as a bare id6, so an unconverted `"executed:af7i6p"` matched neither and landed in
    `unsatisfied`, BLOCKING a dependent that was actually ready. Failure direction was over-blocking,
    not wrongly admitting.

    From revgate 7nkcgp: an `executed:`-style (execute-action) dependency is satisfied by reaching
    `executed` ONLY IF it also carries no recorded unresolved gating findings, applied to BOTH the
    in-queue and out-of-queue resolution paths so the gate is not evadable by queue membership; and
    every unsatisfied dependency gets a reason string so `dependency-blocked` can say WHY.

    A `review`-action item is deliberately NOT findings-gated: only an `executed:` edge asserts that
    work was completed and verified.
    """
    by_id = {entry["id6"]: entry for entry in state["queue"]}
    repo = Path(state["repo"])
    unsatisfied: list[str] = []
    reasons: dict[str, str] = {}
    is_exec = item.get("action") != "review"

    def _block(dep: str, reason: str) -> None:
        unsatisfied.append(dep)
        reasons[dep] = reason

    if item.get("action") == "orchestrate":
        # orchretire-03 (`pgq326`) E-01: THE SELECTION GATE IS PART OF THE WIRING, and missing it would
        # have left this Set's whole mechanism unreachable from the run shape it was built for.
        #
        # MEASURED, not reasoned: this clause used to call the queue-scoped `_set_children_all_executed`,
        # and `initialize_run` derives an already-`executed` child's RUN status as `reviewed` (only
        # to-review/draft/approved/auto-approved become `queued`). So for the PRIMARY case spec R-1
        # names -- `aw oc run <setid>` on a Set whose children executed in EARLIER runs -- the gate
        # reported `satisfied=False, missing=['executed:<child>']` while the on-disk verdict was
        # `eligible=True`. The orchestrator was never selected, so the dispatch branch was NEVER
        # REACHED, and wiring only the dispatch branch would have fixed nothing for that run.
        #
        # It now asks the SAME shared decision the dispatch branch acts on, so the gate and the dispatch
        # cannot disagree about one plan. That equivalence is the point: two predicates answering one
        # question is how this function and `cascade_dependency_blocked` once gave OPPOSITE verdicts
        # (runorder F-7).
        #
        # WHY BLOCK ONLY ON RECONSIDER. A gate exists to make an item WAIT. So:
        #   * RETIRE     -> admit it; the dispatch branch retires it.
        #   * RECONSIDER -> block, because this run WILL still act on the named children; the item is
        #                   re-tested on a later iteration, which IS the reconsideration R-7 requires.
        #   * TERMINATE  -> ADMIT it, deliberately, so it reaches the dispatch branch and receives its
        #                   SPECIFIC reason. Blocking instead would leave it to the drain path, which
        #                   labels it `dependency-blocked` with whatever this function reported -- and
        #                   for the no-children case that list is EMPTY, which is exactly the `5e4sb6`
        #                   record that claimed an unmet dependency while naming none.
        decision = decide_orchestrator_dispatch(
            repo,
            str(item.get("setid") or ""),
            str(item["id6"]),
            state.get("queue") or [],
            terminal_states=TERMINAL_STATES,
            success_states=EXECUTION_SUCCESS_STATES,
        )
        if decision.outcome == ORCH_DISPATCH_RECONSIDER:
            for child_id, child_status in decision.unfinished:
                _block(
                    f"executed:{child_id}",
                    f"orchestrator waits for child {child_id} of set "
                    f"'{item.get('setid')}' to execute (currently {child_status or 'unfinished'})",
                )

    for dep in item.get("dependencies", []):
        dep = str(dep)
        # 8guhs0: parse the typed token FIRST, so the id6 and the queue key both come from the
        # parsed edge and never from the raw string.
        edge = parse_dependency_token(dep)
        if edge is None:
            # Fail closed: an unparseable token is never "no dependency". Preflight refuses such a
            # run before any session starts; this is the belt-and-braces path for a hand-edited
            # state.json.
            _block(dep, f"{dep}: unparseable dependency token")
            continue
        ok, reason = edge_satisfied(edge, item, state, by_id)
        if not ok:
            # Report the token AS DECLARED, not its canonical rewrite: `unsatisfied_dependencies` is
            # written into durable run records.
            _block(dep, reason or f"{dep}: dependency not satisfied")
            continue
        # revgate: the edge is satisfied structurally; for an execute-action dependency ALSO refuse
        # on unresolved gating findings. Uses the parsed edge's target id6, not the raw token.
        if is_exec:
            target = dependency_target_id6(edge) or dep
            why = _findings_block_reason(repo, target)
            if why:
                _block(dep, why)
    return not unsatisfied, unsatisfied, reasons


#: novalnomerge-01 (evgi9n) E-01: the gating suite must never inherit `run_evidence.capture_command`'s
#: 60s default. MEASURED at review: the bare suite runs ~37s on the reference host, so the default
#: leaves ~23s of headroom, and because E-02 treats a timeout as a FAILURE an under-set timeout would
#: silently degrade to "never integrate" -- recreating the very bug this module's gate change fixes.
SUITE_CHECK_TIMEOUT_SECONDS: float = 900.0

#: The repository's own test command, run BARE. `pyproject.toml` `addopts` already supplies
#: `-q -n auto --dist=worksteal -m 'not slow'`, so adding `-n0` (4-6x slower), a second `-q`
#: (suppresses the summary line this check parses) or `-p no:randomly` is forbidden by the repo
#: contract and would also change what the gate measures.
SUITE_CHECK_ARGV: tuple[str, ...] = (sys.executable or "python3", "-m", "pytest")

_SUITE_SUMMARY_RE = re.compile(
    r"^(?:=+\s*)?(\d+ (?:passed|failed).*?)(?:\s*=+)?$", re.MULTILINE
)


def parse_suite_summary(text: str) -> str:
    """The suite's COUNT LINE out of its output, or `""` when none is present.

    integearn-05 (`9lyg5h`) E-03: a NAMED, injectable reader for the one pattern `run_suite_check`
    already applies inline, so the concurrent pre-work baseline in `runner_shared` can report the same
    count line the post-work check reports. It exists ONLY because `runner_shared` may not import a
    host driver (a shipped AST test enforces that), so every host specific must be handed over as a
    name; this is the `run_checked`/`host_label` injection precedent applied to one regex.

    IT IS THE SAME PATTERN, DELIBERATELY NOT A SECOND ONE. `run_suite_check` keeps its inline use, and
    both now resolve `_SUITE_SUMMARY_RE`, because a second spelling of a parser is how a producer and
    a reader drift apart (the render_stream F-4 defect class, measured twice in this package).
    """

    match = _SUITE_SUMMARY_RE.search(text or "")
    return match.group(1).strip() if match else ""


#: gatewire-01 (`h5pyqa`) E-02: the lines naming WHICH tests failed, which `_SUITE_SUMMARY_RE`
#: deliberately does not capture.
#:
#: WHY A SECOND PATTERN RATHER THAN WIDENING THE FIRST. `_SUITE_SUMMARY_RE` answers "did it pass and
#: by how much", and its single capture group feeds `SuiteCheckResult.summary`, which the integration
#: refusal reason embeds. Widening it to also span the failure list would change that one-line reason
#: into a paragraph on every refusal. These are two different questions with two different readers, so
#: they get two patterns.
#:
#: BOTH `FAILED` AND `ERROR` ARE MATCHED, and the second is not padding. MEASURED on 2026-09-20 with a
#: deliberately broken import under this repository's own `-n auto --dist=worksteal` addopts: a module
#: that cannot be collected yields `ERROR test_broken.py` and NO `FAILED` line at all, while the count
#: line reads `1 failed, 1 passed, 1 error`. Matching only `FAILED` would therefore show an agent
#: nothing for the whole collection-error class, which is exactly the class most likely to be somebody
#: else's fault and so most likely to be a true `not-mine`.
_SUITE_FAILURE_LINE_RE = re.compile(r"^(?:FAILED|ERROR)\s+\S.*$", re.MULTILINE)

#: How many failing-test lines are carried. A pathological run can redden hundreds of tests, and this
#: text goes into a PROMPT; the cap keeps one bad suite from crowding out the rest of the question.
#: Generous on purpose: attribution gets harder, not easier, as the list is truncated.
SUITE_FAILURE_LINE_LIMIT: int = 40


def extract_suite_failures(stdout: str, stderr: str = "") -> tuple[str, ...]:
    """The `FAILED`/`ERROR` lines from a suite run, deduplicated, in first-seen order.

    gatewire-01 (`h5pyqa`) E-02. SEPARATE FROM THE COUNT LINE BY DESIGN: a count ("1 failed") tells an
    agent nothing it can attribute to its own diff, and attribution is the entire judgement the
    integration-refusal answer turns on.

    Deduplicated because xdist can report the same node twice across the short summary and a rerun
    section, and a question that lists one failure three times reads as three failures.
    """

    seen: dict[str, None] = {}
    for haystack in (stdout or "", stderr or ""):
        for match in _SUITE_FAILURE_LINE_RE.finditer(haystack):
            line = match.group(0).strip()
            if line and line not in seen:
                seen[line] = None
            if len(seen) >= SUITE_FAILURE_LINE_LIMIT:
                return tuple(seen)
    return tuple(seen)


class SuiteCheckResult(NamedTuple):
    """What the DRIVER observed when it ran the suite itself.

    novalnomerge-01 (evgi9n) E-01/E-02. This is an OBSERVED FACT, not a claim: the executor's outcome
    JSON has a ``"tests"`` field, but nothing reads it, so it is the agent's own prose about work it
    says it did. `passing` is True only on an observed exit 0.

    `failures` ADDED BY gatewire-01 (`h5pyqa`) E-02, and it is DEFAULTED so that every existing
    construction site and every test double that builds this tuple positionally keeps working. It
    carries the `FAILED`/`ERROR` lines naming WHICH tests failed, because `summary` carries only the
    count line and a count cannot be attributed to a diff.
    """

    passing: bool
    exit_code: int
    summary: str
    reason: str
    cwd: str
    timeout_seconds: float
    elapsed_seconds: float
    failures: tuple[str, ...] = ()

    @property
    def failing_text(self) -> str:
        """The failing tests as the QUESTION should show them, or an honest statement of absence.

        NEVER RETURNS AN EMPTY STRING, because this lands in a prompt: an empty section reads as "no
        failures" and would invite a false `not-mine`. When the names could not be recovered the agent
        is told so, and given the count line instead, so it can answer from the evidence that exists
        rather than from a blank.
        """

        if self.failures:
            return "\n".join(self.failures)
        if self.summary:
            return (
                f"{self.summary}\n"
                "(the individual failing test names could not be recovered from this run's output; "
                "re-run the suite yourself if you need them to answer)"
            )
        return (
            "the suite did not pass and produced no parseable summary "
            f"(exit {self.exit_code}): {self.reason}"
        )


def run_suite_check(
    repo_dir: Path,
    run_id: str,
    *,
    timeout: float = SUITE_CHECK_TIMEOUT_SECONDS,
) -> SuiteCheckResult:
    """Run the repository's suite in the PRIMARY checkout and report what actually happened.

    novalnomerge-01 (evgi9n) E-01/E-02.

    WHY THE PRIMARY CHECKOUT AND NOT THE LANE (PR-001, found at review as a BLOCKER): a linked
    worktree resolves `.aw/state` relative to cwd (backlog `dh0uno`), so a lane sees a DIFFERENT state
    tree. MEASURED: `tests/test_run_viewer.py` gives `36 passed` in the primary checkout and
    `15 failed, 20 passed` in a lane, every failure being the `run_viewer`/state-resolution family. A
    lane-run suite is therefore permanently red for reasons unrelated to the executing plan, which
    would leave the integration gate closed forever -- the same symptom this change removes, with a new
    cause. Callers MUST pass the primary repo, never `work_dir`.

    HONEST LIMIT: this proves THE TREE is green, not that the lane's uncommitted state is. That is the
    right trade (a green primary tree is what integration endangers) but it is not lane validation.

    FAIL CLOSED (E-02): a suite that cannot be run is a FAILURE, never a pass.
    `run_evidence.capture_command` already converts a timeout into exit 124 and any other exception
    into exit 127 instead of raising, so this is an honest reading of a nonzero exit rather than new
    machinery. Neither code is special-cased into a pass.

    THE OUTPUT READ HERE ONLY STARTED WORKING AT gatewire-01 (`h5pyqa`), and the repair is in
    `run_evidence.capture_command` rather than here. This function read
    `tool_event["stdout_excerpt"]`, and `build_tool_event` NEVER WROTE THAT KEY: a `tool_event` is a
    LEDGER record carrying `stdout_sha256`/`stdout_len` and deliberately not the text. Measured
    2026-09-20 by calling `capture_command` directly - `sorted(tool_event)` contained no
    `stdout_excerpt` - so this read yielded `""`, `summary` was ALWAYS empty, and every refusal reason
    said `no summary line parsed`. The existing tests could not see it because every one of them mocks
    `capture_command` and fabricates the key production never produced. `capture_command` now returns
    the text on the mapping it hands back, so this read means what it always claimed to.
    """
    from agent_workflows import run_evidence

    started = time.monotonic()
    try:
        tool_event, _envelope = run_evidence.capture_command(
            run_id,
            list(SUITE_CHECK_ARGV),
            cwd=repo_dir,
            evidence_kind="tests",
            actor="driver",
            timeout=timeout,
            max_output_bytes=512_000,
        )
        exit_code = int(tool_event.get("exit_code", 127))
        stdout = str(tool_event.get("stdout_excerpt") or "")
        stderr = str(tool_event.get("stderr_excerpt") or "")
    except Exception as exc:  # noqa: BLE001  # pragma: no cover
        # DELIBERATE blind catch, and not redundant: `capture_command` guards its own subprocess call
        # (timeout -> 124, other -> 127) but the lines BEFORE it are unguarded -- `Path(cwd).resolve()`
        # and the `get_git_head`/`get_git_dirty_digest`/`get_worktree_path` probes all run first and can
        # raise on a vanished cwd or a broken git dir. A gate that crashes is a gate that is OFF, so an
        # unexpected exception here must still be a REFUSAL, never an escape from the gate.
        elapsed = time.monotonic() - started
        return SuiteCheckResult(
            passing=False,
            exit_code=127,
            summary="",
            reason=f"suite check could not run (fail-closed): {exc}",
            cwd=str(repo_dir),
            timeout_seconds=timeout,
            elapsed_seconds=elapsed,
        )

    elapsed = time.monotonic() - started
    summary = parse_suite_summary(stdout) or parse_suite_summary(stderr)
    # gatewire-01 (`h5pyqa`) E-02: capture WHICH tests failed, not merely how many. `stdout` is
    # discarded after this function returns, so a failure name not taken here is gone for good.
    failures = extract_suite_failures(stdout, stderr)
    if exit_code == 0:
        reason = f"suite passed in {repo_dir} ({summary or 'no summary line parsed'})"
    elif exit_code == 124:
        reason = (
            f"suite TIMED OUT after {timeout:.0f}s (ran {elapsed:.0f}s) in {repo_dir}; "
            "treated as a failure (fail-closed)"
        )
    elif exit_code == 127:
        reason = (
            f"suite could not be executed in {repo_dir} (exit 127); "
            "treated as a failure (fail-closed)"
        )
    else:
        reason = (
            f"suite FAILED with exit {exit_code} in {repo_dir} "
            f"({summary or 'no summary line parsed'})"
        )
    return SuiteCheckResult(
        passing=exit_code == 0,
        exit_code=exit_code,
        summary=summary,
        reason=reason,
        cwd=str(repo_dir),
        timeout_seconds=timeout,
        elapsed_seconds=elapsed,
        failures=failures,
    )


#: Why an item did NOT reach the integration gate, or how it did. novalnomerge-01 (evgi9n) E-05:
#: `verify_disp` alone conflates "no verifier ran" (None, because validation is off) with "the
#: verifier declined" ("unverified"), and both previously landed the item in `substantially-complete`
#: with no way to tell them apart. These name the actual signal.
#:
#: RE-EXPORTS SINCE gatewire-01 (`h5pyqa`): the five signal names are now DEFINED ONCE, in
#: `runner_shared`, and bound here under their original names so every existing reader
#: (`oc_runipd.INTEGRATION_REFUSED_SUITE_FAILED`, the agy re-export, and the tests that read them off
#: this module) is unchanged. THEY HAD TO MOVE, and the reason is mechanical rather than stylistic:
#: `gate_answer_is_warranted` must compare against `INTEGRATION_REFUSED_SUITE_FAILED` to ask about the
#: suite refusal AND NOTHING ELSE, it lives in `runner_shared`, and `runner_shared` cannot import
#: `oc_runipd` (that is the import direction, and reversing it is a cycle). The alternative was to
#: spell the literal `"suite-failed"` a second time in the shared layer, which is precisely the
#: producer/reader drift this package has already paid for twice (render_stream F-4: a renderer read
#: `driver_error` while the producer wrote `integration_deferral`).
INTEGRATION_EARNED_BY_VERIFIER = runner_shared.INTEGRATION_EARNED_BY_VERIFIER
INTEGRATION_EARNED_BY_SUITE = runner_shared.INTEGRATION_EARNED_BY_SUITE
INTEGRATION_REFUSED_VERIFIER_DECLINED = (
    runner_shared.INTEGRATION_REFUSED_VERIFIER_DECLINED
)
INTEGRATION_REFUSED_SUITE_FAILED = runner_shared.INTEGRATION_REFUSED_SUITE_FAILED
INTEGRATION_REFUSED_NO_SIGNAL = runner_shared.INTEGRATION_REFUSED_NO_SIGNAL


class IntegrationVerdict(NamedTuple):
    """Whether an item earned automatic integration, and WHICH signal earned or refused it."""

    earned: bool
    signal: str
    detail: str


def integration_is_earned(
    *,
    validate: bool,
    verify_disp: str | None,
    suite_result: SuiteCheckResult | None,
) -> IntegrationVerdict:
    """Decide whether a completed execute turn has earned automatic integration.

    novalnomerge-01 (evgi9n) E-03/E-04. ONE predicate, consumed by BOTH drivers, so a one-runner fix
    cannot leave the other silently broken.

    THE BUG THIS FIXES: the gate used to require `verify_disp == "verified"`, but `verify_disp` is only
    ever assigned inside the validate-guarded block. `--validate` defaults FALSE while
    `--no-self-finalize` defaults TRUE, so in the SHIPPED DEFAULT configuration self-finalize was
    switched on and could never fire: every item ended `substantially-complete` with its lane
    preserved and nothing integrated. Measured cost before the fix: ~$528 across five overnight runs,
    21 plans stranded in lanes, then a full session hand-merging 24 lanes.

    THE TWO MODES ARE ALTERNATIVES, NOT AN OR ACROSS BOTH SIGNALS:

    * validation ON  -> the verifier's verdict decides, exactly as before. A verifier that DECLINED is
      a stronger and more specific signal than a green suite, so a passing suite must NOT override it;
      otherwise `--validate` would be weaker than the default, which is absurd.
    * validation OFF -> the DRIVER-RUN SUITE decides. This is an observed fact, unlike the executor's
      unread ``"tests"`` self-report. `aw ipd finalize` still applies its own independent fail-closed
      gate afterwards (`ipd_lifecycle.finalize_precheck`: a current begin receipt, the
      before-marking-executed lint requiring every `E-*` performed and every `V-*` passing with
      non-empty `Observed evidence`, and a scope comparison), so this lowers the bar less than it
      appears. Honest limit: that gate proves completeness and scope, NOT correctness, which is why a
      real suite run supplies the correctness signal it lacks.
    """
    if validate:
        if verify_disp == "verified":
            return IntegrationVerdict(
                True, INTEGRATION_EARNED_BY_VERIFIER, "verifier reported verified"
            )
        return IntegrationVerdict(
            False,
            INTEGRATION_REFUSED_VERIFIER_DECLINED,
            f"validation is ON and the verifier did not verify (verification={verify_disp!r}); "
            "a green suite deliberately does NOT override an explicit verifier verdict",
        )
    if suite_result is None:
        return IntegrationVerdict(
            False,
            INTEGRATION_REFUSED_NO_SIGNAL,
            "validation is OFF and no driver-run suite result is available; refusing to integrate "
            "without any trust signal (fail-closed)",
        )
    if suite_result.passing:
        return IntegrationVerdict(
            True,
            INTEGRATION_EARNED_BY_SUITE,
            f"no verifier ran (validation off); driver-run suite PASSED: {suite_result.reason}",
        )
    return IntegrationVerdict(
        False,
        INTEGRATION_REFUSED_SUITE_FAILED,
        f"no verifier ran (validation off) and the driver-run suite did not pass: "
        f"{suite_result.reason}",
    )


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
        if entry.get("action") == "orchestrate":
            setid = entry.get("setid")
            for other_id, other in by_id.items():
                if (
                    other_id != node
                    and other.get("setid") == setid
                    and other.get("action") != "orchestrate"
                    and other_id not in seen
                ):
                    best = max(best, 1 + _depth(other_id, seen | {node}))
        return best

    return _depth(id6, frozenset())


def queue_sort_key(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> tuple:
    """Deterministic ordering key for READY nodes (spec 25kzda 5.4 rules 4-5).

    DECLARED EDGES WIN, and that is why `dependency_depth` stays FIRST: a depth-0 node always
    precedes a node that declares an in-queue prerequisite, whatever the request order or the Order
    numbers say. So Set/Order/request-order can never act as evidence that a dependency is satisfied
    (rule 3), which is what Set/Order silently did while `dependencies` was always `[]`.

    `position` IS A PRIORITY (runorder prpipy; maintainer ruling 2026-09-01), ranked immediately
    after dependency depth and therefore ABOVE Set, Order, and id6. It carries the order the
    operator REQUESTED, so among equally-ready independent nodes the run executes them in the order
    they were asked for. The previous key ranked `position` LAST, which recorded the request and then
    discarded it: measured in run `run-20260901T042331Z-118022`, `aw oc run m73aet 6lu3rq` froze
    `position 1 m73aet` / `position 2 6lu3rq` and then dispatched `6lu3rq` first, purely because
    `"runmixed" < "runtrail"`, with nothing announcing the inversion.

    HONEST LIMITS OF THIS KEY, both of which the pre-prpipy docstring got wrong:

    * The sort is NO LONGER a function of artifact content alone. `position` comes from the
      INVOCATION (`expand_selectors` -> `initialize_run`), so the same plans selected in a different
      order legitimately execute in a different order. That is the intended contract, not drift.
    * `position` is a priority AND STILL A FROZEN IDENTITY. Outcome/prompt/session filenames and this
      run's decision ids all key on it, so it is assigned exactly once at queue-build time and is
      never renumbered by sorting. Reading it here must not make it mutable.

    `position` only equals the operator's TYPED order when the selectors were literal id6 tokens. A
    setid, `all`, `reviews`, or a file-path selector expands to many positions whose order comes from
    the MANIFEST, so callers that report ordering to a human must say "requested order" rather than
    claim a typed one (see `run_order_rationale`).

    Spec 5.4 rule 4 also lists a TYPE RANK (`spec`, `backlog`, `ipd`, `prompt`) ahead of Set. It is
    deliberately NOT implemented: this runner's queue is homogeneous (IPDs only), so a rank over types
    that cannot appear would be untestable dead code. Recorded rather than silently skipped.

    THE HOMOGENEITY SURVIVED `--with-dependencies` SHIPPING (depclosure 01, `dhycim`), which is worth
    stating because this note previously rested on the closure not existing. The closure now exists,
    and it REFUSES a `spec` or `backlog` dependency target precisely because the manifest cannot carry
    one, so every id it can add is still an IPD. A later plan that admits non-plan targets is what
    would make this rank reachable, and it must revisit this note.
    """
    return (
        dependency_depth(item["id6"], by_id),
        item.get("position", 0),
        str(item.get("setid") or ""),
        item.get("order") if isinstance(item.get("order"), int) else 999,
        item["id6"],
    )


def simulate_dispatch_order(
    queue: list[dict[str, Any]], initial_completed: Iterable[str] | None = None
) -> list[str]:
    """Simulate the order in which items in `queue` will actually be dispatched by `run_queue`.

    Accounts for:
    - In-queue declared dependencies: a dependent waits until all its in-queue prerequisites have run.
    - Orchestrator deferral: an orchestrator plan (action == 'orchestrate') waits until all child
      plans in its Set have completed.
    - Tiebreaking: among ready items, ordered by `queue_sort_key`.
    """
    if not queue:
        return []

    by_id = {str(item.get("id6")): item for item in queue}

    set_children: dict[str, set[str]] = {}
    for item in queue:
        id6 = str(item.get("id6"))
        setid = str(item.get("setid") or "")
        if item.get("action") != "orchestrate":
            set_children.setdefault(setid, set()).add(id6)

    in_queue_deps: dict[str, set[str]] = {}
    for item in queue:
        id6 = str(item.get("id6"))
        deps: set[str] = set()
        for dep in item.get("dependencies", []) or []:
            edge = parse_dependency_token(str(dep))
            if edge is not None and getattr(edge, "target_type", None) == "ipd":
                target = dependency_target_id6(str(dep))
                if target and target in by_id and target != id6:
                    deps.add(target)
        in_queue_deps[id6] = deps

    remaining = list(queue)
    completed: set[str] = set(initial_completed or ())
    executed: list[str] = []

    while remaining:
        ready: list[dict[str, Any]] = []
        for item in remaining:
            id6 = str(item.get("id6"))
            if not in_queue_deps.get(id6, set()).issubset(completed):
                continue
            if item.get("action") == "orchestrate":
                setid = str(item.get("setid") or "")
                children = set_children.get(setid, set())
                if not children.issubset(completed):
                    continue
            ready.append(item)

        if ready:
            chosen = min(ready, key=lambda it: queue_sort_key(it, by_id))
        else:
            chosen = min(remaining, key=lambda it: queue_sort_key(it, by_id))

        chosen_id = str(chosen.get("id6"))
        remaining.remove(chosen)
        completed.add(chosen_id)
        executed.append(chosen_id)

    return executed


def update_execution_order(
    state: dict[str, Any], runnable: dict[str, Any]
) -> list[str]:
    """Dynamically update `state["run_order"]["executed"]` to reflect actual dispatch order.

    Ensures that:
    1. Items that have already run/been dispatched form the prefix in their dispatch order.
    2. The current `runnable` item is placed next at index `len(already_dispatched)`.
    3. Remaining items in the queue follow in their simulated dispatch order.
    """
    run_order = state.setdefault("run_order", {})
    prev_executed: list[str] = list(run_order.get("executed") or [])
    dispatched: list[str] = list(run_order.get("dispatched") or [])
    dispatched_set = set(dispatched)

    queue = state.get("queue") or []

    # If dispatched list wasn't tracked yet, reconstruct from queue terminal/attempted states:
    if not dispatched:
        terminal_dispositions = {
            "executed",
            "reviewed",
            "approved",
            "substantially-complete",
            "partial",
            "blocked",
            "failed-safely",
            "integration-blocked",
            "merge-conflict",
        }
        for id6 in prev_executed:
            for it in queue:
                if str(it.get("id6")) == id6 and (
                    it.get("status") in terminal_dispositions or it.get("attempts")
                ):
                    if id6 not in dispatched_set:
                        dispatched.append(id6)
                        dispatched_set.add(id6)
        for it in queue:
            id6 = str(it.get("id6"))
            if (
                it.get("status") in terminal_dispositions or it.get("attempts")
            ) and id6 not in dispatched_set:
                dispatched.append(id6)
                dispatched_set.add(id6)

    runnable_id6 = str(runnable.get("id6"))
    if runnable_id6 not in dispatched_set:
        dispatched.append(runnable_id6)
        dispatched_set.add(runnable_id6)

    run_order["dispatched"] = dispatched

    # Remaining items that have not been dispatched yet
    remaining = [it for it in queue if str(it.get("id6")) not in dispatched_set]
    predicted_remaining = simulate_dispatch_order(
        remaining, initial_completed=dispatched_set
    )

    new_executed = list(dispatched) + [
        id6 for id6 in predicted_remaining if id6 not in dispatched_set
    ]
    run_order["executed"] = new_executed
    if "requested" in run_order:
        run_order["reordered"] = run_order["requested"] != new_executed

    return new_executed


def run_order_rationale(
    queue: list[dict[str, Any]], selectors: Iterable[str] | None = None
) -> dict[str, Any]:
    """Compare the REQUESTED order with the order the run will EXECUTE in, and say why they differ.

    runorder (prpipy) E-04. Ordering used to be silent: `position` recorded the request, the sort
    discarded it, and the only way to discover an inversion was to diff `events.jsonl` timestamps
    against `state.json` positions after the fact. This computes the comparison once, at queue build,
    so the driver can print it and freeze it into durable run state.

    Returns a JSON-safe dict (it is written verbatim into `state.json` and `events.jsonl`):

    * ``requested``   - id6s in the order the queue was FROZEN in, i.e. `position` order.
    * ``executed``    - the same id6s re-sorted by :func:`queue_sort_key`, i.e. dispatch order.
    * ``reordered``   - True iff those two differ.
    * ``causes``      - ``{id6: reason}`` for each item whose index MOVED. A reason begins with
                        ``declared dependency:`` when a real `Item-Dependencies` edge forces the move
                        (correct and expected) or ``tiebreak:`` when nothing but the comparator's
                        lower-ranked fields decided it (the case that bit the maintainer). Telling
                        those two apart is the operator-facing point, so a bare "reordered" is not
                        enough.
    * ``request_kind``- ``typed`` only when the selectors were LITERAL id6 tokens naming exactly this
                        queue; otherwise ``expanded``, because a setid / `all` / `reviews` / path
                        selector expands to many positions ordered by the MANIFEST, not by the
                        operator's typing. Callers must not claim a typed order for an expansion.
    * ``selectors``   - the raw selector tokens, so the message can name the expansion.

    Pure: no I/O, no printing. The message TEXT lives in `render_stream`, not here.
    """
    sel_list = [str(s).strip() for s in (selectors or [])]
    requested = [str(item.get("id6")) for item in queue]
    by_id = {str(item.get("id6")): item for item in queue}
    executed = simulate_dispatch_order(queue)

    req_index = {id6: idx for idx, id6 in enumerate(requested)}
    exec_index = {id6: idx for idx, id6 in enumerate(executed)}

    def _in_queue_edges(id6: str) -> list[tuple[str, str]]:
        """(target_id6, declared token) for each edge of ``id6`` pointing at another QUEUE node."""
        out: list[tuple[str, str]] = []
        for dep in by_id.get(id6, {}).get("dependencies", []) or []:
            edge = parse_dependency_token(str(dep))
            if edge is None or getattr(edge, "target_type", None) != "ipd":
                continue
            # NOTE: `dependency_target_id6` takes the raw TOKEN, not the parsed edge (verified by
            # signature); passing the edge silently returns None and would erase every cause.
            target = dependency_target_id6(str(dep))
            if target and target in by_id and target != id6:
                out.append((target, str(dep)))
        return out

    causes: dict[str, str] = {}
    for id6 in requested:
        if req_index[id6] == exec_index[id6]:
            continue
        reason = ""
        # Moved EARLIER because something requested before it declares it as a prerequisite.
        for other in requested:
            if req_index[other] >= req_index[id6]:
                continue
            for target, token in _in_queue_edges(other):
                if target == id6:
                    reason = (
                        f"declared dependency: {other} declares `{token}`, "
                        f"so {id6} must run first"
                    )
                    break
            if reason:
                break
        # Moved LATER because it declares a prerequisite that was requested after it.
        if not reason:
            for target, token in _in_queue_edges(id6):
                if req_index.get(target, -1) > req_index[id6]:
                    reason = (
                        f"declared dependency: {id6} declares `{token}`, "
                        f"so it waits for {target}"
                    )
                    break
        # Moved because of orchestrator deferral
        if not reason:
            item = by_id.get(id6, {})
            if item.get("action") == "orchestrate":
                reason = (
                    f"orchestrator: waits for children of set '{item.get('setid')}' "
                    f"to execute first"
                )
            else:
                for other in requested:
                    if req_index[other] >= req_index[id6]:
                        continue
                    other_item = by_id.get(other, {})
                    if other_item.get("action") == "orchestrate" and other_item.get(
                        "setid"
                    ) == item.get("setid"):
                        reason = (
                            f"orchestrator child: {other} is the orchestrator for set "
                            f"'{other_item.get('setid')}', so {id6} executes first"
                        )
                        break
        # Moved because DEPENDENCY DEPTH differs from the item it swapped with. The two loops above
        # only see a DIRECT edge between the mover and something requested before/after it, which
        # misses the commonest real case: `dependency_depth` is the FIRST element of
        # `queue_sort_key`, so a depth-1 node yields to every depth-0 node in the queue even when
        # there is no edge between those two at all. Measured live in `aw oc run revsweep`: `6ypimw`
        # (depth 1, via `executed:76gsmv`) and `eyh1fu` (depth 0, no edges) swapped, and BOTH were
        # reported as `tiebreak: no declared dependency explains this move` while a declared
        # dependency was the entire explanation. Attributing an edge-driven move to the tiebreak is
        # the specific lie this branch exists to stop: the tiebreak label is the operator's signal
        # that the runner reordered them on lower-ranked fields, so it must never absorb a move the
        # dependency graph forced.
        if not reason:
            depth = dependency_depth(id6, by_id)
            moved_later = exec_index[id6] > req_index[id6]
            # The counterpart that displaced it: among the items that crossed this one, the one whose
            # depth differs in the direction that explains the move. Naming it keeps the message
            # actionable rather than a bare "depth differs".
            for other in requested:
                if other == id6:
                    continue
                crossed = (req_index[other] > req_index[id6]) != (
                    exec_index[other] > exec_index[id6]
                )
                if not crossed:
                    continue
                other_depth = dependency_depth(other, by_id)
                if moved_later and other_depth < depth:
                    reason = (
                        f"declared dependency: {id6} has {depth} declared prerequisite level(s) "
                        f"in this queue and {other} has {other_depth}, so {other} runs first"
                    )
                    break
                if not moved_later and other_depth > depth:
                    reason = (
                        f"declared dependency: {other} has {other_depth} declared prerequisite "
                        f"level(s) in this queue and {id6} has {depth}, so {id6} runs first"
                    )
                    break
        if not reason:
            item = by_id.get(id6, {})
            pos = item.get("position")
            pos_txt = "unset" if not isinstance(pos, int) else str(pos)
            order = item.get("order")
            order_txt = "unset" if not isinstance(order, int) else str(order)
            reason = (
                "tiebreak: no declared dependency explains this move; ranked by "
                f"requested position {pos_txt}, Set '{item.get('setid') or ''}', "
                f"Order {order_txt}, id6"
            )
        causes[id6] = reason

    literal = bool(sel_list) and all(ID6_RE.fullmatch(s.lower()) for s in sel_list)
    typed = literal and [s.lower() for s in sel_list] == requested
    return {
        "requested": requested,
        "executed": executed,
        "reordered": requested != executed,
        "causes": causes,
        "request_kind": "typed" if typed else "expanded",
        "selectors": sel_list,
    }


def announce_run_order(
    run_dir: Path,
    state: dict[str, Any],
    *,
    stream: Any = None,
) -> dict[str, Any]:
    """Print the execution order and append it to `events.jsonl`; return the rationale.

    runorder (prpipy) E-04/E-07. ONE function so both host drivers announce identically and record
    identically; the wording comes from the shared `render_stream` formatter, never from a driver.
    The announcement is UNCONDITIONAL (the order must be auditable in the log even when nothing was
    reordered) and the durable record is what makes it readable after the terminal scrollback is gone.
    """
    rationale = state.get("run_order") or run_order_rationale(
        state.get("queue", []), state.get("selectors", [])
    )
    out = stream if stream is not None else sys.stdout
    pal = Palette(should_color(out))
    for line in format_run_order_announcement(rationale, pal=pal):
        print(line, file=out)
    # specvis: surface DECLARED spec edits before the run starts. A spec is the contract other plans
    # are reviewed against, so a run that rewrites one is the highest-leverage thing it can do and was
    # previously invisible unless the operator opened every plan.
    #
    # specvis st5klo E-01: the announcement is made ONCE HERE, for the WHOLE QUEUE, BEFORE any item is
    # dispatched (maintainer requirement 2026-09-08). `spec_impacts_for_queue` reads `state["queue"]`
    # entire, and this function's sole callers are the two drivers' queue-freeze points, which run
    # before the first child session. Do NOT move this into per-item dispatch: that would turn the one
    # pre-spend warning into a line buried mid-run, which is the surface the operator scrolls past.
    try:
        _repo = Path(state["repo"])
        # specvis st5klo E-01/E-02: `queue_with_plan_paths` is REQUIRED, not decoration. A real runner
        # queue entry carries its plan location under `configured_file`, while `spec_impacts_for_queue`
        # reads `path`/`plan_path`, so passing the raw queue made this announcement compute an empty
        # impact set and print nothing on EVERY real run, on BOTH hosts. See `queue_plan_path`.
        _impacts = spec_impacts_for_queue(
            _repo, queue_with_plan_paths(_repo, state.get("queue", []))
        )
        for line in format_spec_impact_announcement(_impacts, pal=pal):
            print(line, file=out)
    except Exception as exc:
        # specvis st5klo E-01: STILL advisory (a broken announcement must never stop a run from
        # starting, which is why this catches everything and does not re-raise), but no longer SILENT.
        # The old `pass` made two very different states render identically: "this run declares no spec
        # edits" and "the spec-impact computation crashed" both printed nothing, so an operator could
        # not tell a clean run from a broken announcer. One named line resolves that ambiguity without
        # changing what the run is permitted to do. Emitted from the SHARED function, so both hosts get
        # it from this single edit (`agy_runipd` imports and calls this very object).
        for line in format_spec_impact_failure(exc, pal=pal):
            print(line, file=out)
    # runconcur-01 (`vddpml`) E-02: SURFACE A PEER DRIVER before anything is dispatched. Measured on
    # 2026-09-22: two unattended drivers ran in one checkout for hours and NOTHING in any command's
    # output revealed the second one, so deciding what was safe to merge required reading both runs'
    # `state.json` by hand. Reported from the shared function, so both hosts get it from one edit.
    #
    # UNKNOWN IS RENDERED DISTINCTLY FROM NONE (`format_peer_driver_report`): no peer prints nothing,
    # an unprobeable one prints a named line. It REFUSES NOTHING - policy B serializes the integration
    # step instead - so an advisory failure here must never stop a run, hence the catch.
    try:
        _peers = peer_drivers(Path(state["repo"]), exclude_run_dir=run_dir)
        _peer_lines = format_peer_driver_report(_peers)
        if _peer_lines:
            print(file=out)
            for line in _peer_lines:
                print(pal(line, "yellow"), file=out)
        append_jsonl(
            run_dir / "events.jsonl",
            {
                "at": utc_now(),
                "event": "peer-drivers",
                "run_id": state.get("run_id"),
                "peers": [
                    {
                        "run_id": p.run_id,
                        "state": p.state,
                        "pid": p.pid,
                        "selectors": list(p.selectors),
                    }
                    for p in _peers
                ],
            },
        )
    except Exception as exc:
        # Named rather than silent, for the reason the spec-impact announcer above records: "no peer"
        # and "the peer query crashed" must not render identically.
        print(
            pal(f"  ! the peer-driver query could not be computed: {exc}", "yellow"),
            file=out,
        )
    try:
        from agent_workflows import term as T

        _repo = Path(state["repo"])
        _term = T.Term(color=should_color(out))
        _slated_table = format_slated_artifacts_table(
            _repo, state.get("queue", []), term=_term
        )
        if _slated_table:
            print(file=out)
            print(_slated_table, file=out, end="")
    except Exception:
        pass
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "run-order",
            "run_id": state.get("run_id"),
            "requested": rationale["requested"],
            "executed": rationale["executed"],
            "reordered": rationale["reordered"],
            "causes": rationale["causes"],
            "request_kind": rationale["request_kind"],
        },
    )
    return rationale


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

    THE SUCCESS BAR IS ACTION-DEPENDENT, and it MUST match `edge_satisfied`'s (runorder F-7). A
    REVIEW pass does not require its prerequisite to have been EXECUTED: reviewing a child that
    imports a module the previous child creates needs only that the previous child was reviewed,
    because no code is written or imported during a review. `edge_satisfied` has always encoded this
    (`is_exec = item.get("action") != "review"`, then `EXECUTION_SUCCESS_STATES if is_exec else
    SUCCESS_STATES`), so this function reuses the SAME predicate rather than a second one.

    MEASURED FAILURE this fixes (run `run-20260904T042705Z-1025943`): a 6-item all-`review` run of
    the `wslayout` Set reviewed Orders 00 and 01, and the instant Order 01 reached `reviewed` this
    cascade declared it a dead prerequisite and killed Orders 02-05 with "prerequisite reached a
    non-success terminal state". It hardcoded `EXECUTION_SUCCESS_STATES`, and `reviewed` is in
    `TERMINAL_STATES` but not in that set. Meanwhile `dependency_status_detailed` returned
    `satisfied: True` for those same items, so TWO functions gave opposite answers to one question
    and the cascade won because it runs after each item completes. The Set was well-formed and its
    edges were correct; a review-mode Set run was simply impossible to complete.
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
                # SAME action-aware bar as `edge_satisfied`; do NOT hardcode
                # EXECUTION_SUCCESS_STATES here (that made a review-mode Set run impossible).
                required = (
                    EXECUTION_SUCCESS_STATES
                    if item.get("action") != "review"
                    else SUCCESS_STATES
                )
                if st in TERMINAL_STATES and st not in required:
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


# `build_review_prompt` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# ---- recovery routing: verify-and-continue vs fresh execution ------------------------------------
#
# resumedupe (`txc9l1`). A resumed turn used to be told, in prose, that it was continuing an
# interrupted attempt and that its predecessor's lane already held commits, and then decide for itself
# what to do. That was MEASURED INSUFFICIENT: after `build_recovery_lane_notice` shipped those exact
# facts, a resumed turn still re-implemented work a prior attempt had already committed. The
# reviewable proof is item `zhr6mc`, whose two sibling commits share the subject
# `feat(runner): close a backlog item when the run executes its last carrier` on INDEPENDENT parents
# (`42b38acf` on `bcbbfb07`, `8a9b8f32` on `144f3347`), 2118 vs 2260 insertions over the same four
# files; only the second was merged and the first was retired as provably superseded. Item `bmh754`
# repeats the shape. That is one full turn's work performed twice.
#
# So the judgment MOVES TO THE DRIVER, which already holds every fact required and needs no new
# observation machinery: `worktree_lease.inspect_lane` is non-mutating by contract and already reports
# `commits_ahead`, `dirty`, the lane's own base sha and one of five `LANE_STATES`, and the prior
# attempt's lane identity is already recorded durably. Informing an agent is necessary but not
# sufficient; reading the lane is decidable.
#
# WHICH LANE TO READ IS THE WHOLE CORRECTNESS QUESTION, and reading the obvious one ships a feature
# that changes nothing while its tests pass. ALLOCATION NEVER REUSES A LANE HOLDING WORK:
# `allocate_worktree` classifies such a lane `HOLDS-WORK` and ATTEMPT-SCOPES alongside it, leaving it
# byte-identical, so a resumed turn runs in a BRAND-NEW `aw/lane/<id6>_attemptN` at ZERO commits while
# the work sits on the lane it was displaced from. Measured: after one real commit on lane `ntf6sx`, a
# second `allocate_worktree(repo, 'ntf6sx')` returned `ntf6sx:attempt2` with
# `displaced_from=aw/lane/ntf6sx`, and `inspect_lane` reported the NEW lane `EMPTY commits_ahead=0`
# against the OLD one's `HOLDS-WORK commits_ahead=1`. A classifier keyed on the turn's OWN lane would
# therefore answer `fresh-execution` on EVERY resume. Hence this classifies the PRIOR attempt's lane,
# resolved from durable state, and `tests/test_resumedupe.py` asserts the inspected lane id is the
# prior one so that regression fails loudly instead of silently disabling the feature.

DISPOSITION_FRESH_EXECUTION = "fresh-execution"
DISPOSITION_VERIFY_AND_CONTINUE = "verify-and-continue"
DISPOSITION_UNDETERMINED = "undetermined"

RECOVERY_DISPOSITIONS: tuple[str, ...] = (
    DISPOSITION_FRESH_EXECUTION,
    DISPOSITION_VERIFY_AND_CONTINUE,
    DISPOSITION_UNDETERMINED,
)


class RecoveryDisposition(NamedTuple):
    """The driver's routing decision for one recovery turn, plus the facts it was decided from.

    Carries its INPUTS, not merely its verdict, because a wrong routing decision is invisible after
    the fact otherwise; that diagnosability gap is why the original duplication took three runs to
    notice. `inspected_lane_id` is the load-bearing field for a reader: it says WHICH lane the
    decision was based on, which is the one thing a silently-inert regression would get wrong.
    """

    disposition: str  # one of RECOVERY_DISPOSITIONS
    reason: str
    inspected_lane_id: str | None
    inspected_branch: str | None
    inspected_worktree: str | None
    lane_state: str | None
    commits_ahead: int
    dirty: bool
    snapshot_only: bool
    real_commits: tuple[
        tuple[str, str], ...
    ] = ()  # (sha, subject) of NON-snapshot commits

    @property
    def verify_and_continue(self) -> bool:
        return self.disposition == DISPOSITION_VERIFY_AND_CONTINUE


# `resolve_prior_lane` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


def _lane_commit_subjects(
    repo: Path, base_sha: str, head_sha: str
) -> list[tuple[str, str]]:
    """(sha, subject) for each commit on a lane beyond its base, newest first. Read-only."""
    rc, out, _err = _run_git(
        repo, ["log", "--format=%H%x1f%s", f"{base_sha}..{head_sha}"]
    )
    if rc != 0:
        return []
    commits: list[tuple[str, str]] = []
    for line in out.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        commits.append((sha.strip(), subject.strip()))
    return commits


def classify_recovery_disposition(
    repo: Path, item: dict[str, Any], state: dict[str, Any]
) -> RecoveryDisposition:
    """Route a recovery turn from FACTS, not from the agent's judgment (E-01).

    PURE with respect to the repository: it runs read-only git commands through `inspect_lane` and
    `git log` only. It does NOT mutate state, does NOT write git, and specifically does NOT ADOPT,
    check out, merge, or tidy the displaced lane, which may hold another attempt's preserved work that
    the shipped rules require be left byte-identical.

    `verify-and-continue` only when the PRIOR lane holds at least one commit that is NOT an interrupted
    snapshot. `fresh-execution` when no prior lane is recorded, or it is absent, empty, or holds only
    snapshots. `undetermined` when a recorded lane cannot be read at all.
    """
    from agent_workflows import worktree_lease

    lane_id, lane_base, _lane_branch = resolve_prior_lane(item)
    if not lane_id:
        return RecoveryDisposition(
            disposition=DISPOSITION_FRESH_EXECUTION,
            reason="no prior lane is recorded for this item; nothing to verify",
            inspected_lane_id=None,
            inspected_branch=None,
            inspected_worktree=None,
            lane_state=None,
            commits_ahead=0,
            dirty=False,
            snapshot_only=False,
        )

    try:
        st = worktree_lease.inspect_lane(repo, lane_id, base_commit=lane_base or "HEAD")
    # DELIBERATELY BROAD, and narrower would be a correctness bug here. This routing decision must
    # never itself break a run: `inspect_lane` shells out to git, so it can raise OSError, a
    # subprocess error, or anything a future probe introduces, and ANY such failure has exactly one
    # correct answer - `undetermined`, dispatched as a fresh execution (E-03). Enumerating types would
    # convert a new failure mode into a crashed run instead of a slightly wasteful one.
    except Exception as exc:  # noqa: BLE001
        # E-03: an unreadable lane is UNDETERMINED, and `_route_recovery` turns that into a FRESH
        # EXECUTION dispatch. See its comment for why this direction is deliberate.
        return RecoveryDisposition(
            disposition=DISPOSITION_UNDETERMINED,
            reason=f"recorded prior lane {lane_id!r} could not be read: {exc}",
            inspected_lane_id=lane_id,
            inspected_branch=None,
            inspected_worktree=None,
            lane_state=None,
            commits_ahead=0,
            dirty=False,
            snapshot_only=False,
        )

    common = {
        "inspected_lane_id": lane_id,
        "inspected_branch": st.branch,
        "inspected_worktree": str(st.worktree_path) if st.worktree_path else None,
        "lane_state": st.state,
        "commits_ahead": st.commits_ahead,
        "dirty": st.dirty,
    }

    if not st.exists:
        return RecoveryDisposition(
            disposition=DISPOSITION_FRESH_EXECUTION,
            reason=f"prior lane {lane_id!r} no longer exists ({st.state})",
            snapshot_only=False,
            **common,
        )
    if st.commits_ahead == 0:
        return RecoveryDisposition(
            disposition=DISPOSITION_FRESH_EXECUTION,
            reason=(
                f"prior lane {lane_id!r} holds no commits beyond its base ({st.state}); "
                "there is no committed work to verify"
            ),
            snapshot_only=False,
            **common,
        )

    if not st.head or not st.base_sha:
        return RecoveryDisposition(
            disposition=DISPOSITION_UNDETERMINED,
            reason=(
                f"prior lane {lane_id!r} reports {st.commits_ahead} commit(s) but its "
                "head/base could not be resolved, so its contents cannot be classified"
            ),
            snapshot_only=False,
            **common,
        )

    commits = _lane_commit_subjects(repo, st.base_sha, st.head)
    if not commits:
        return RecoveryDisposition(
            disposition=DISPOSITION_UNDETERMINED,
            reason=(
                f"prior lane {lane_id!r} reports {st.commits_ahead} commit(s) but none "
                "could be listed, so its contents cannot be classified"
            ),
            snapshot_only=False,
            **common,
        )
    # E-02's SUBJECT-ONLY rule: a snapshot means work was preserved mid-edit and redoing it is
    # correct, so only NON-snapshot commits count as finished work worth verifying. Matching the
    # phrase anywhere in the body would misread a real commit that quotes it.
    real = tuple(
        (sha, subject)
        for sha, subject in commits
        if not worktree_lease.commit_subject_is_interrupted_snapshot(subject)
    )
    if not real:
        return RecoveryDisposition(
            disposition=DISPOSITION_FRESH_EXECUTION,
            reason=(
                f"prior lane {lane_id!r} holds only {len(commits)} interrupted-snapshot "
                "commit(s), which are preserved mid-edit work and NOT finished work"
            ),
            snapshot_only=True,
            real_commits=(),
            **common,
        )
    return RecoveryDisposition(
        disposition=DISPOSITION_VERIFY_AND_CONTINUE,
        reason=(
            f"prior lane {lane_id!r} already holds {len(real)} non-snapshot commit(s); "
            "verify and complete that work instead of re-executing the plan"
        ),
        snapshot_only=False,
        real_commits=real,
        **common,
    )


def build_verify_and_continue_notice(repo: Path, decision: RecoveryDisposition) -> str:
    """The prompt block asking a resumed turn to VERIFY AND COMPLETE prior work (E-04).

    A VARIANT of the recovery branch, not a second prompt mechanism, and it keeps that branch's
    deliberate constraints: NO acknowledgement gate and NO refusal path, because a refusal is one more
    way for an unattended run to stall.

    IT MUST SAY THE WORK IS ON A DIFFERENT BRANCH THAN THE AGENT'S CWD, because it is: the turn runs
    in a fresh attempt-scoped lane while the prior work sits on the displaced branch. So the branch is
    named, reading it is invited, and committing onto it is forbidden - that lane may be another
    attempt's preserved work and the shipped rule is to leave it byte-identical.
    """
    if not decision.verify_and_continue:
        return ""
    branch = decision.inspected_branch or "(unknown)"
    lines = [
        "",
        "",
        "## A PRIOR ATTEMPT ALREADY COMMITTED WORK FOR THIS PLAN: verify and continue it",
        "",
        "Do NOT implement this plan from scratch. A previous attempt at this same IPD already",
        f"committed work, and the driver has READ that work: {decision.reason}.",
        "",
        f"THAT WORK IS ON A DIFFERENT BRANCH THAN YOUR WORKING DIRECTORY. It is on `{branch}`,",
        "which is NOT the lane you are running in. Your own lane is where you must produce your",
        "commits; that other branch is READ-ONLY for you.",
        "",
        f"Commits already on `{branch}` (newest first):",
    ]
    for sha, subject in decision.real_commits:
        lines.append(f"  - {sha} {subject}")
    if decision.dirty:
        lines.append("")
        lines.append(
            "That lane ALSO has uncommitted changes in its working tree; a commit there whose"
        )
        lines.append(
            "subject says INTERRUPTED SNAPSHOT is preserved mid-edit work, not finished work."
        )
    diffstat = ""
    base_ref = ""
    newest_sha = ""
    if decision.real_commits:
        # `real_commits` is newest-first, so the OLDEST real commit's parent is the base of this
        # work. Note this deliberately spans any snapshot commits interleaved with real ones, which
        # is what an agent needs to see: the whole delta the prior attempt produced.
        base_ref = f"{decision.real_commits[-1][0]}~1"
        newest_sha = decision.real_commits[0][0]
        rc, out, _err = _run_git(repo, ["diff", "--stat", base_ref, newest_sha])
        if rc == 0 and out.strip():
            diffstat = out.strip()
    if diffstat:
        diff_cmd = f"git diff --stat {base_ref} {newest_sha}"
        lines.extend(
            [
                "",
                f"Diffstat of that work against its base (`{diff_cmd}`):",
                "",
            ]
        )
        lines.extend("    " + line for line in diffstat.splitlines())
    lines.extend(
        [
            "",
            "WHAT TO DO, in this order:",
            "",
            f"1. READ that work first. `git log {branch}` and `git diff` against that ref show you",
            "   exactly what exists. Read it before you write anything.",
            "2. Judge it against the plan: which `E-*` items does it actually perform, which `V-*`",
            "   items does it evidence, and what is still missing or wrong.",
            "3. BRING FORWARD what is still correct INTO YOUR OWN LANE, then finish the remainder",
            "   there. Re-authoring work that is already correct produces a duplicate sibling commit",
            "   and is the exact waste this routing exists to prevent.",
            f"4. Do NOT `git checkout`, merge, cherry-pick onto, rebase, or commit to `{branch}`, and",
            "   do not amend or delete anything on it. It may hold another attempt's preserved work",
            "   and must be left byte-identical. Read it; never write it.",
            "5. If you conclude the work is ALREADY COMPLETE, you still may not simply assert that:",
            "   fill each `V-*` item's `Observed evidence:` with the prior work's ACTUAL output (run",
            "   the tests yourself and paste what they print). A finalize gate checks the checklists",
            "   and their evidence, not your conclusion.",
        ]
    )
    return "\n".join(lines)


def route_recovery_turn(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    recovery: bool,
) -> RecoveryDisposition | None:
    """Decide how a recovery turn is dispatched and RECORD the decision durably (E-03, E-05).

    Returns None for a first attempt, so first-attempt behavior is untouched.

    E-03, THE FAIL-TOWARD-DOING-THE-WORK CHOICE, AND IT IS DELIBERATELY THE OPPOSITE OF A LIFECYCLE
    GATE. An `undetermined` reading is dispatched as a FRESH EXECUTION, never as a skip. Do not "fix"
    this into a refusal: the lifecycle gates fail CLOSED because their failure mode is falsely claiming
    work is done, whereas the failure mode HERE is leaving a plan UNIMPLEMENTED while reporting a turn
    was spent, which is strictly worse than paying for a duplicate turn. Wasted spend is recoverable;
    a silently skipped implementation is what a human discovers much later.

    CALL THIS BEFORE THE TURN'S OWN LANE IS ALLOCATED. Allocation writes `worktree_lane_id` onto the
    CURRENT attempt, and `resolve_prior_lane` would then resolve that fresh, always-empty lane as the
    "prior" one and answer `fresh-execution` on every resume - the inert-feature regression. Classify
    once, early, and reuse the returned decision for any later prompt rebuild rather than recomputing.
    """
    if not recovery:
        return None
    repo = Path(state["repo"])
    decision = classify_recovery_disposition(repo, item, state)
    effective = (
        DISPOSITION_FRESH_EXECUTION
        if decision.disposition == DISPOSITION_UNDETERMINED
        else decision.disposition
    )
    # E-05: record the verdict AND its inputs, so an operator can see WHY a turn was routed as it was
    # without re-deriving it. `inspected_lane_id` is what tells a future reader which lane the decision
    # was based on, which is the one fact a silently-inert regression would get wrong.
    record = {
        "disposition": decision.disposition,
        "dispatched_as": effective,
        "reason": decision.reason,
        "inspected_lane_id": decision.inspected_lane_id,
        "inspected_branch": decision.inspected_branch,
        "inspected_worktree": decision.inspected_worktree,
        "lane_state": decision.lane_state,
        "commits_ahead": decision.commits_ahead,
        "dirty": decision.dirty,
        "snapshot_only": decision.snapshot_only,
        "real_commits": [
            {"sha": sha, "subject": subject} for sha, subject in decision.real_commits
        ],
        "at": utc_now(),
    }
    item["recovery_routing"] = record
    save_state(run_dir, state)
    append_jsonl(
        run_dir / "events.jsonl",
        {
            "at": utc_now(),
            "event": "recovery-routed",
            "id6": item.get("id6"),
            **{k: v for k, v in record.items() if k != "at"},
        },
    )
    pal = Palette(should_color(sys.stdout))
    if decision.verify_and_continue:
        print(
            pal(
                f"  \u21ba recovery routed VERIFY-AND-CONTINUE: {decision.reason}",
                "cyan",
            )
        )
    elif decision.disposition == DISPOSITION_UNDETERMINED:
        print(
            pal(
                f"  ! recovery routing undetermined; dispatching a FRESH EXECUTION "
                f"(never a skip): {decision.reason}",
                "yellow",
            ),
            file=sys.stderr,
        )
    return decision


def build_isolation_notice(lane_root: Path | None) -> str:
    """The WORK HERE block for an isolated turn, or "" for a main-checkout turn.

    lanectn `cqx5v7` E-02 (spec `7ckptx` R1.2, R1.4): the TEXT lives in the host-neutral
    `lane_containment.isolation_notice`, which both drivers reach, and the EXCEPTION CLAUSE that used
    to authorize absolute out-of-lane paths is DELETED rather than reworded. See that function's
    docstring for the measured defect this block closes, for why the deletion is safe (the paths are
    lane-relative now, so there is nothing left to except), and for the honest limit.

    hostdedup Order 01 (`li44r9`): now a thin wrapper. This symbol was a THREE-WAY fork -- a real body
    in BOTH runners while `runner_shared.build_isolation_notice` also existed and was reached by
    nobody -- so the fix was to point both hosts at the definition that was already there rather than
    to add a fourth copy.
    """
    return runner_shared.build_isolation_notice(lane_root)


# rununify 04 (`tx6q0h`): one-line wrappers over the shared prompt builders. The INSTRUCTION TEXT is
# now identical on both hosts by the maintainer's ruling (plan `tx6q0h` OQ-03); only the host product
# name and, for the verifier, the host's shell-tool name vary. The two notice builders are injected
# because they still live per host at this point in the Set.
def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
    lane_root: Path | None = None,
    routing: RecoveryDisposition | None = None,
) -> str:
    return runner_shared.build_prompt(
        item,
        state,
        run_dir,
        plan_path,
        recovery,
        lane_root,
        routing,
        labels=runner_shared.OC_HOST_LABELS,
        build_isolation_notice=build_isolation_notice,
        build_verify_and_continue_notice=build_verify_and_continue_notice,
    )


def build_verifier_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    *,
    audit: bool = False,
    diff_basis: str = "",
) -> str:
    """This host's binding of the ONE shared verifier-prompt composer.

    ``audit`` / ``diff_basis`` are FORWARDED, not re-interpreted (reverify-01 `mp289j` E-06): the
    audit rendering is decided once, in `runner_shared.build_verifier_prompt`, so the standalone
    `audit` verb and the in-run turn 2 cannot drift. Both default to the in-run values, so every
    existing call site's output is byte-identical.
    """
    return runner_shared.build_verifier_prompt(
        item,
        state,
        run_dir,
        plan_path,
        labels=runner_shared.OC_HOST_LABELS,
        audit=audit,
        diff_basis=diff_basis,
    )


# `write_prompt` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# `attempt_log_path` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


_SIGINT_GRACE_SECONDS = 5.0
_SIGTERM_GRACE_SECONDS = 2.0
DEFAULT_STALL_TIMEOUT: float = 600.0


def terminate_process(process: subprocess.Popen) -> None:
    """Reap this host's child agent process and its process group without leaving orphans.

    hostdedup Order 01 (`li44r9`) E-03: now a thin wrapper over the ONE definition in
    ``runner_shared``, which in turn delegates to the SINGLE shared reaper in ``runner_shutdown``
    (spec `c4gd2h` R5 forbids a second implementation).

    THE MODULE-LEVEL GRACE CONSTANTS ARE STILL READ HERE, AT CALL TIME, AND PASSED THROUGH, so a
    caller or test that tunes ``_SIGINT_GRACE_SECONDS`` / ``_SIGTERM_GRACE_SECONDS`` on THIS module
    still takes effect. That is the reason the shared function takes them as no-default parameters
    rather than reading constants of its own: a shared read would have left this tuning seam silently
    inert (`tests/test_runner_shutdown.py` tunes exactly this and would have passed anyway).
    """

    runner_shared.terminate_process(
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

    WHO WRITES THE KEY THIS READS (`hardreach` Order 01, `n5qca5`): a per-profile
    `execution_profile` field in the operator's own `runner-profiles.json`, resolved by
    `resolve_launch_pair` and frozen into `state["options"]` by `initialize_run`. Until that
    plan there was NO writer at all, so both branches below were unreachable in production. There
    is deliberately no CLI flag: the enforcement is Linux/Landlock only, and a documented flag on a
    cross-platform tool reads as a cross-platform guarantee (that plan's OQ-01).
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
        control_root=state.get("control_root") or state_root(repo_root),
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
) -> Callable[[], None]:
    """Build the callback `BudgetBreachWatch` invokes when the wind-down deadline passes.

    hostdedup Order 01 (`li44r9`) E-02: a thin wrapper over the ONE definition in `runner_shared`, which
    holds the full rationale for why this RECORDS the breach and deliberately does not escalate
    (runstop foi1b3 E-04, spec R11/A7).
    """
    return runner_shared._budget_breach_recorder(
        run_dir, item, request, checkpoint_observer
    )


def _escalation_recorder(
    run_dir: Path, item: dict[str, Any]
) -> Callable[[int, int, str], None]:
    """Build the callback `EscalationWatch` invokes when it PERFORMS an escalation (71vjbn E-06).

    hostdedup Order 01 (`li44r9`) E-02/E-08: a thin wrapper over the ONE definition in `runner_shared`,
    which holds the full rationale (spec R11 records the escalation, R23 forbids claiming work not
    done). THE LABELS ARE PASSED AS DATA: the shared body reports the escalation to the operator with a
    driver command, and that command must name THIS host. Before the lift each host body called its own
    `_detect_driver_command`, which IS the labels binding, so a shared call would have named one host
    for all of them.
    """
    return runner_shared._escalation_recorder(
        run_dir, item, labels=runner_shared.OC_HOST_LABELS
    )


def _record_checkpoint_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    checkpoint_observer: runner_stop.CheckpointObserver,
    *,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Record a level-3 stop on the item with KNOWN certainty (spec R18), returning the record.

    hostdedup Order 01 (`li44r9`) E-02: a thin wrapper over the ONE definition in `runner_shared`, which
    holds the full rationale. THIS HOST'S `git_status` IS BOUND HERE because the shared `git_status`
    needs each host's own `run_checked`; see the shared definition for the defect that made this
    explicit rather than implicit.
    """

    return runner_shared._record_checkpoint_stop(
        run_dir,
        state,
        item,
        checkpoint_observer,
        work_dir=work_dir,
        git_status_fn=git_status,
    )


def _record_forced_stop(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    stop: runner_stop.StopNowForce,
    *,
    work_dir: str | Path | None = None,
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

    effective_dir = (
        work_dir
        or item.get("worktree")
        or (
            item.get("attempts", [{}])[-1].get("worktree")
            if item.get("attempts")
            else None
        )
    )
    repo = Path(effective_dir) if effective_dir else Path(state["repo"])
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


# lanectn Order 03 (`lhmrhx`) E-02, spec R4.2: the HOST-SPECIFIC half of policy observation.
#
# The DECISION is host-neutral (`lane_containment.evaluate_policy_observation`); only the I/O is here,
# because the probe command, its flag, and its output shape are opencode's, not a shared rule.
#
# `opencode debug config` prints the host's OWN RESOLVED configuration after every precedence layer
# has been merged, which is precisely what R4.2 asks be observed rather than assumed: it reflects a
# managed or higher-precedence source that overrode the runner's request. Measured on 1.18.27 at
# roughly 1.4s, so this is a bounded per-turn cost, not a per-call one.
_POLICY_PROBE_TIMEOUT_SECONDS = 30.0


def observe_opencode_policy(
    opencode: str,
    child_env: dict[str, str],
    requested: dict[str, str],
) -> lane_containment.PolicyObservation:
    """Ask the host what its EFFECTIVE permission policy is, under the SAME env the child will get.

    NEVER RAISES, and that is a requirement rather than defensiveness (spec R4.2, plan OQ-01): the
    observation is a DIAGNOSTIC, not a precondition. If the probe cannot run we return an
    `unverified` marker naming the reason and the turn continues, because the R4.4 bounds hold
    regardless of what the host decided. Letting a probe failure propagate would abort turns that
    were otherwise fine, which is strictly worse than the unknown it was trying to remove. What is
    NOT acceptable is recording nothing, because then a run silently believes it is protected.

    The probe runs with the CHILD's environment, so it observes the same precedence stack the child
    will, rather than the driver's.
    """

    version: str | None = None
    try:
        version_proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [opencode, "--version"],
            capture_output=True,
            text=True,
            timeout=_POLICY_PROBE_TIMEOUT_SECONDS,
            env=child_env,
        )
        if version_proc.returncode == 0:
            version = version_proc.stdout.strip().splitlines()[-1].strip() or None
    except Exception:
        version = None

    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [opencode, "debug", "config"],
            capture_output=True,
            text=True,
            timeout=_POLICY_PROBE_TIMEOUT_SECONDS,
            env=child_env,
        )
    except Exception as exc:
        return lane_containment.evaluate_policy_observation(
            None,
            requested,
            host_version=version,
            failure_reason=f"the policy probe could not run ({type(exc).__name__}: {exc})",
        )
    if proc.returncode != 0:
        return lane_containment.evaluate_policy_observation(
            None,
            requested,
            host_version=version,
            failure_reason=(
                f"`opencode debug config` exited {proc.returncode}: "
                f"{(proc.stderr or proc.stdout or '').strip()[:200]}"
            ),
        )
    return lane_containment.evaluate_policy_observation(
        proc.stdout, requested, host_version=version
    )


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
    use_verifier_launch: bool = False,
    # runanalytics Order 04 (`5f2h8i`) E-02/E-03: the invocation's PHASE, stated by the call site
    # and never inferred. Today an executor turn and a verifier turn are distinguishable only by the
    # `log_suffix="verify"` string this function hands to `attempt_log_path`, so phase is recoverable
    # from a FILENAME; deriving telemetry's phase that way would couple a data field to a
    # presentation detail and would break silently the day a log filename changes. Defaulted, so
    # every existing call site and every test that calls this function positionally is unchanged.
    telemetry_phase: str = runner_shared.TELEMETRY_PHASE_EXECUTE,
    # defreport 01 (`b7xarm`) E-05: an EXPLICIT session to resume, used only by the defect re-ask.
    # Keyword-only and defaulted, so no existing call site changes and no existing turn's argv moves.
    # See where it is consumed below for why resuming here is safe on an isolated lane.
    resume_session: str | None = None,
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
    # dirtygates Order 05 (`ajxr5d`) E-04: THE ONE ISOLATED TREE A SESSION MAY LEGITIMATELY PERSIST IN,
    # and it does NOT relax `xd9sll`'s rule - it states that rule precisely for the first time.
    #
    # The recorded cause of `xd9sll` is a CARDINALITY MISMATCH, not isolation as such: sessions were
    # keyed per SET while worktrees were allocated per ITEM, so lanes 2..N inherited lane 1's session and
    # the session's own directory binding overrode `--dir`. So the invariant is "never carry one session
    # into a DIFFERENT tree", and a per-item execute lane violates it on every turn (unchanged below,
    # still always fresh) while the REVIEW SWEEP LANE cannot violate it at all: it is ONE tree for every
    # review in the run, which is exactly why OQ-02 chose one lane for the sweep.
    #
    # THE SESSION READ HERE IS THE SWEEP'S OWN, not the set's. A review sweep is run-wide (`reviews`
    # selects across every Set), and the CLI promises continuity across the whole sweep, so a per-set key
    # would split it the first time a sweep spanned two Sets. `set_sessions` is deliberately left
    # untouched for the sweep: promoting a lane session into it is what would re-arm the carryover for a
    # LATER execute turn in the same set.
    sweep_lane_turn = runner_shared.turn_runs_in_review_sweep_lane(state, work_dir)
    max_items = options.get("max_items_per_session", 4)
    raw_session = (
        # THE OPERATOR'S EXPLICIT `--session` STILL SEEDS THE SWEEP, which is why the fallback is here
        # rather than the sweep key being read alone. `--session <id>` is documented as the session to
        # "attach/reuse across turns for multi-plan continuity", so honoring it for an execute turn and
        # ignoring it for a review would break the one surface whose whole purpose is continuity - and it
        # is SAFE, because the operator names one id for one run and the sweep is one tree.
        state.get(runner_shared.REVIEW_SWEEP_SESSION_KEY) or options.get("session")
        if sweep_lane_turn
        else (
            state.get("session_id")
            or state.get("set_sessions", {}).get(item["setid"])
            or options.get("session")
        )
    )
    is_rotation = False
    if raw_session and max_items and max_items > 0:
        session_turns = state.get("session_turn_counts", {}).get(raw_session, 0)
        if session_turns >= max_items:
            is_rotation = True
            raw_session = None

    session = (
        None
        if (fresh_session or (isolated_turn and not sweep_lane_turn) or is_rotation)
        else raw_session
    )
    # defreport 01 (`b7xarm`) E-05: the ONE caller that may resume a session an isolated turn would
    # otherwise refuse, and it is safe for the exact reason the isolated-turn refusal above exists.
    # That refusal prevents carrying ANOTHER lane's session into THIS tree (lanesess `xd9sll`: a
    # session's own project binding overrides `--dir`, and four consecutive lanes were lost to it).
    # The defect re-ask resumes THIS attempt's OWN session, observed from THIS turn in THIS lane, so
    # the binding it carries is the lane we want; a fresh session would instead have to re-derive the
    # agent's findings from the diff, which is both more expensive and less accurate.
    #
    # Passed ONLY by the re-ask call site and defaulted to None, so every other turn's argv is
    # byte-identical and `tests/test_lane_session_isolation.py` still sees no `--session` on a lane.
    if resume_session:
        session = resume_session
    if session:
        argv.extend(["--session", session])

    argv.extend(["--dir", agent_dir, "--format", "json"])
    # runprofile-06 (`kgpptv`) E-03: WHICH frozen launch this turn uses. ONE argv builder serves
    # every turn (a second builder for the verifier is how the two hosts' flag surfaces diverged),
    # so the ROLE is passed in explicitly by the caller and never inferred here.
    #
    # SELECTED BY THE CALL SITE, NOT BY `fresh_session`, and that distinction is the whole trap
    # (F-10). `fresh_session` is true for the verifier AND for every ISOLATED turn, and
    # `isolate_worktree` defaults True, so keying the verifier launch off `fresh_session` - or off
    # session-absence - would hand the VERIFIER's model to nearly every EXECUTE turn, which is the
    # DEFAULT configuration. Only the verifier call site passes `use_verifier_launch=True`.
    #
    # A REVIEW turn needs no branch at all: it IS the execute call site with
    # `item["action"] == "review"` (read below only to pick a `--title` label), so it keeps the
    # executor's launch automatically (F-11).
    #
    # `verify_launch` is falsy for every run created without a verifier profile (the keys are absent
    # from frozen state entirely), so the argv below is byte-identical to what it was before this
    # field existed.
    verify_launch = use_verifier_launch and bool(options.get("verify_launch_profile"))
    model_key, variant_key, agent_key = (
        ("verify_model", "verify_variant", "verify_agent")
        if verify_launch
        else ("model", "variant", "agent")
    )
    if options.get(model_key):
        argv.extend(["--model", options[model_key]])
    if options.get(variant_key):
        argv.extend(["--variant", options[variant_key]])
    if options.get(agent_key):
        argv.extend(["--agent", options[agent_key]])
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

    # lanectn Order 02 (`nna8yz`) E-04, spec R5.3: EVERY `--file` attachment for an isolated turn must
    # resolve inside the lane. Both values below are therefore localized against the manifest E-01
    # materialized, via the shared `localize_attachment` (the agy twin has no `--file` surface at all -
    # it passes its prompt inline - so there is nothing to mirror there; see that driver's launch path).
    #
    # dirtygates Order 05 (`ajxr5d`) E-01/E-02: THE LOCALIZATION IS NOW REACHED BY A REVIEW TOO, and it
    # needed no change to be so. `lane_root_for_attachments` is derived from `work_dir`, which is now set
    # for an isolated review, so a review's plan attachment resolves inside the sweep lane exactly as an
    # execute turn's does. This site was the SEVENTH `not is_review` guard, which the plan's original
    # six-site census omitted (finding F-8): the `not is_review` test remaining below governs only the
    # RUNBOOK attachment, and it is correct there for a reason of substance rather than of tree - a
    # review turn is not given the driver runbook at all, because its whole instruction is the
    # `/plan-review` slash command (see `build_review_prompt`, which is deliberately prose-free).
    #
    # CORRECTION TO THIS PLAN'S FINDING F-3, recorded because the plan asserted the opposite and an
    # executor trusting it would have fixed only half the defect. F-3 says "the plan path is ALREADY
    # lane-local (the driver passes the lane-resolved plan)" and that only the runbook needed changing.
    # MEASURED AT 44d4950d: FALSE for the argv. `execute_item` computes `lane_plan_path` and passes it
    # to `build_prompt`, so the PROMPT TEXT names the lane copy - which is what F-3 actually observed -
    # but the `run_opencode(...)` call a few lines later still passes the outer `plan_path`, which is
    # `resolve_plan_path(repo, ...)` against MAIN. So BOTH attachments named the main checkout and both
    # are localized here. The decisions register carries this as a DECISION with the evidence.
    lane_root_for_attachments = Path(work_dir) if work_dir else None

    if (
        not is_review
        and not log_suffix
        and state.get("runbook")
        and Path(state["runbook"]).exists()
    ):
        argv.extend(
            [
                "--file",
                lane_containment.localize_attachment(
                    lane_root=lane_root_for_attachments,
                    fallback=state["runbook"],
                    input_class=lane_containment.INPUT_CLASS_RUNBOOK,
                ),
            ]
        )

    argv.extend(
        [
            "--file",
            lane_containment.localize_attachment(
                lane_root=lane_root_for_attachments,
                fallback=plan_path,
                input_class=lane_containment.INPUT_CLASS_PLAN,
            ),
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
    # hardreach Order 01 (`n5qca5`): that key now HAS a writer, an `execution_profile` field in the
    # operator's own `runner-profiles.json` resolved and frozen at run creation. Until then nothing
    # in the package assigned it, so this seam could never fire in production. Reading it from the
    # FROZEN options (not from a store read here) is what makes a resume honor the posture the run
    # was created with.
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
    # streamfmt (mm6wuz) E-05: read from the FROZEN run options (not from `args`), which is the same
    # path `output_mode` takes, so a resume honors the tier the run was created or resumed with.
    verbosity = int(options.get("verbosity") or 0)
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

    # lanefinal (i452hf) / wtiso-03 (rchpms) E-06: mark an ISOLATED lane turn as the managed WORKER
    # role, so an in-lane `aw ipd begin`/`aw ipd finalize` hits the deterministic
    # AW-LIFECYCLE-ROLE-001 refusal instead of forking a SECOND receipt and a second lifecycle
    # transaction the driver cannot see. That fork is the measured cause of i452hf: the agent
    # correctly followed the repo contract, finalized in its lane, and the driver's own
    # self-finalize then refused against state it could not observe, stranding the work.
    #
    # Keyed on `work_dir` (the lane worktree), which is exactly "this turn runs in a managed lane".
    # A non-isolated turn is NOT marked, and the DRIVER's own process is never marked, so
    # `driver_begin`/`driver_finalize` keep full authority. Any inherited value is REMOVED when the
    # turn is not isolated, so a coordinator turn can never accidentally inherit a stale `worker`
    # marking from an outer process and refuse its own lifecycle verbs.
    #
    # The child previously INHERITED the environment implicitly (no `env` key at all). This builds it
    # explicitly via the SHARED `pinned_child_env` helper rather than a second construction, so the
    # runner's import pin is preserved and PATH/auth/toolchain vars still survive.
    #
    # HONEST LIMIT: this is an environment SELECTOR, not a hardened boundary. A same-user worker with
    # shell access can unset it. It stops an agent that is FOLLOWING the contract (the actual i452hf
    # case), not a determined one; hard enforcement is an OS sandbox / separate principal.
    from agent_workflows import ipd_lifecycle

    child_env = pinned_child_env()
    if work_dir:
        child_env[ipd_lifecycle.EXECUTION_ROLE_ENV] = ipd_lifecycle.ROLE_WORKER
    else:
        child_env.pop(ipd_lifecycle.EXECUTION_ROLE_ENV, None)

    # lanectn Order 03 (`lhmrhx`) E-01/E-02/E-03, spec R4.1/R4.2/R4.3/R4.6: ask THIS host for the
    # strongest permission posture it actually supports, then OBSERVE what took effect.
    #
    # Extends the ONE child-env construction above rather than forking a second one, which the plan
    # requires for the same reason the role selector does: two constructions drift.
    #
    # OPENCODE HAS A REAL DENIAL (unlike antigravity, R4.1a): `permission.external_directory=deny`
    # and `permission.question=deny` are supplied through the host's own runtime-config env var, so
    # the HOST refuses. Never by editing repository configuration (R4.1 forbids it): inline content
    # is owned by this process and vanishes with it, where a file would be a durable artifact
    # somebody could later mistake for project config.
    #
    # ORDERING IS SPEC-NORMATIVE, NOT STYLISTIC (R4.6). This denial MUST NOT precede the lane-relative
    # prompt work (child `cqx5v7`), because the host currently PERMITS out-of-lane writes (measured:
    # run `run-20260901T042331Z-118022` recorded zero permission events and both workers wrote all
    # five out-of-lane paths). Denying paths the prompt still NAMED would have converted a working
    # runner into a hard failure. `cqx5v7` is in `executed/`, so the prompt no longer names them.
    #
    # ISOLATED TURNS ONLY, deliberately narrower than the bounds below. R4.1 scopes the posture to an
    # unattended ISOLATED turn, and a non-isolated turn legitimately works in the main checkout, where
    # an external-directory denial would refuse its ordinary work.
    #
    # R4.3: an operator value is MERGED or LOUDLY OVERRIDDEN, never silently dropped. The risk is real
    # rather than hypothetical: `pinned_child_env` copies the process environment, so a blind
    # assignment here would discard whatever an operator had exported, with no warning.
    if work_dir:
        policy_request = lane_containment.build_permission_policy_env(
            child_env.get(lane_containment.OPENCODE_RUNTIME_CONFIG_ENV)
        )
        child_env[lane_containment.OPENCODE_RUNTIME_CONFIG_ENV] = (
            policy_request.env_value
        )
        posture = lane_containment.opencode_posture_record(policy_request)
        # R4.2: OBSERVE, do not assume the request won. Host configuration precedence can place a
        # managed source ABOVE the runner's, so a run that only SET the policy can believe it is
        # protected when it is not. OQ-01 resolved that an unobservable policy is recorded
        # `unverified` and the turn CONTINUES: the probe is a DIAGNOSTIC, and the R4.4 bounds below
        # hold regardless of what the host decided, so letting a probe failure propagate would abort
        # turns that were otherwise fine.
        observation = observe_opencode_policy(
            opencode, child_env, policy_request.policy
        )
        # The RECORDING is host-neutral (`lane_containment.record_host_posture`), so the record shape
        # is identical on both hosts and only the posture VALUE differs. See the agy twin for the
        # sanctioned asymmetry: that host passes no observation because it has no policy to observe.
        lane_containment.record_host_posture(
            run_dir, item, attempt_no, posture, observation
        )

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

    # streamfmt (mm6wuz) E-02: reset PER-TURN tracker state at the turn boundary. One
    # `StreamTracker` serves the whole invocation (`run_queue` constructs it once and passes it to
    # every item), so without this the first `todowrite` of queue item 2 would be diffed against
    # item 1's FINAL list and render a transition that never happened. Only the per-turn todo state
    # is cleared: token/cost totals and `modified_files` are run-scoped by design.
    if tracker is not None:
        tracker.begin_turn()

    # runanalytics Order 04 (`5f2h8i`) E-01/E-02/E-03: per-invocation telemetry, opened around THE
    # AGENT LAUNCH and nothing else.
    #
    # WHY EXACTLY HERE, AND NOWHERE ELSE IN THIS MODULE. This function holds the module's ONE
    # agent-launch `subprocess.Popen` (immediately below, already wrapped in
    # `runner_shutdown.track_child`), and it has exactly TWO callers: the executor in
    # `execute_item` and the verifier later in that same function. The module's other
    # `subprocess.run` calls are version probes, `git` helpers, and the lifecycle verbs; wrapping
    # those would emit telemetry for work nobody wants measured and would inflate the event volume
    # Order 03's overhead budget is sized against. So: wrap the agent turn.
    #
    # THE SEAM IS SHARED, NOT LOCAL. `runner_shared.turn_telemetry` is the ONE definition and the
    # agy driver reaches the SAME object; a copy here (or an import of a helper defined in this
    # module BY the agy driver) is precisely the re-fork `tests/test_runner_refork_guard.py` exists
    # to catch. It never raises, so no failure mode it has can change this turn's outcome, and the
    # `with` adds no branch to any code path below.
    telemetry_identity = runner_shared.telemetry_identity(
        run_id=str(state.get("run_id") or ""),
        item=item,
        attempt_no=attempt_no,
        phase=telemetry_phase,
        host="opencode",
    )
    with (
        runner_shared.turn_telemetry(
            run_dir,
            telemetry_identity,
            repo=state.get("repo"),
            # The launch identity this turn actually used, read from the SAME keys the argv above
            # was built from, so telemetry records the verifier's model on a verifier turn rather
            # than the executor's.
            extra_context={"model": options.get(model_key)},
        ),
        log_path.open("w", encoding="utf-8") as log,
    ):
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
            action=statusline_action_for_item(item),
            artifact_kind=item.get("kind", item.get("type", "ipd")),
            # lifeglyph (`qdd5jq`) E-03, spec Section 7.1: the live activity, derived from the
            # field that CARRIES it (`verification_status`, `integration_signal`, the retry state)
            # rather than from `action` alone, which only knows `review`/`execute`. `None` when the
            # entry signals nothing, which renders no activity cell rather than a guessed one.
            activity=activity_for_item(item),
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
        # runstop 71vjbn (E-06, spec R11/A7): ENFORCE the wind-down budget Phase 3 only RECORDED.
        #
        # It is armed for the WHOLE turn, not only after a stop is observed, and out-of-band for the
        # same measured reason every other watch here is: `for line in process.stdout` BLOCKS, so a
        # deadline on a silent child can only be noticed from another thread. Arming it
        # unconditionally also covers the level-1/2 case, whose wind-down deadline can expire while
        # this turn is still running and which the in-loop level-3 branch below never reaches.
        #
        # It only RAISES THE DURABLE LEVEL. The escalated level is then honored by the machinery that
        # already exists (the poll, `force_watch`, and the ONE shared `clean_shutdown`), so no second
        # reaper and no second teardown path is introduced (spec R5).
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
                # What had ALREADY been observed completing before the request. Passed so the record
                # can carry it under its `prior_observed_*` keys; it is NEVER promoted to "the last
                # completed operation", because the cut point itself was not observed.
                prior_completed_index=checkpoint_observer.last_checkpoint_index,
                prior_completed_label=checkpoint_observer.last_checkpoint_label,
            )

        # lanectn Order 03 (`lhmrhx`) E-04, spec R4.4/R4.4a/R4.4b/R4.4c/R4.4d: the two driver-side
        # bounds that do not trust the host. See `lane_containment.PERMISSION_TIMEOUT` /
        # `MAX_TURN_TIMEOUT` for each one's measured-from instant and reset semantics, which are the
        # two facts an identifier cannot carry, and for the one-turn (not one-run) scope.
        #
        # ARMED FOR EVERY UNATTENDED TURN, ISOLATED OR NOT (R4.4a): constructed here, outside any
        # `work_dir` branch, on purpose. R1.3 protects the non-isolated turn's PROMPT TEXT, which
        # stays byte-identical; this is driver-side SUPERVISION and changes no instruction an agent
        # reads. OpenCode has NO host-enforced per-turn ceiling (contrast antigravity's 240m
        # `--print-timeout`, R4.4d), so `None` is passed and the driver bound is genuinely new here.
        turn_bounds = lane_containment.TurnBoundWatch(
            reap=lane_containment.bound_expiry_reaper(process, run_dir, item),
            is_alive=lambda: process.poll() is None,
            max_turn_timeout=lane_containment.driver_bound_for_host(None),
        )

        # lanectn Order 04 (`y5od1h`) E-01/E-06, spec R3.1/R3.2/R3.5: the missing-input
        # REPORT-AND-REFUSE cycle. The observer is HOST-NEUTRAL (spec R2.6) and this is its whole
        # adapter here; the agy twin constructs the identical object (CID-3). Scoped to the turn, so
        # a refusal is attributed to the attempt that produced it.
        #
        # THE CHECKOUT IT CLASSIFIES AGAINST is the repo, NOT `agent_dir`. Classification is
        # COORDINATOR-SIDE (R3.3) and a report names a REPO-RELATIVE path, so resolving it against
        # the lane would make an in-lane request look absent whenever the lane legitimately lacks an
        # ignored file - the exact case a report is for.
        missing_input = lane_containment.MissingInputObserver(state["repo"])

        try:
            # The poller shares the turn's scope, so its thread cannot outlive the turn or
            # leak across attempts. `force_watch` (runstop m0z0ti) joins the same scope so a
            # level-4 force stop is armed for exactly the turn's lifetime, no longer, and
            # `escalation_watch` (runstop 71vjbn) joins it for the same reason. `turn_bounds`
            # (lanectn lhmrhx) joins it too: `__enter__` is what starts `MAX_TURN_TIMEOUT`'s clock,
            # so entering here means it measures from child start.
            with (
                statusline,
                watchdog,
                poller,
                force_watch,
                escalation_watch,
                turn_bounds,
            ):
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    statusline.touch("stdout")
                    watchdog.touch()
                    # lanectn lhmrhx E-04: progress DISARMS the permission bound (resettable);
                    # `MAX_TURN_TIMEOUT` is deliberately NOT reset. See `TurnBoundWatch`.
                    turn_bounds.note_progress()
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
                    # lanectn y5od1h E-01/E-05 (spec R3.1/R3.2/R3.5): classify a missing-input report
                    # and RECORD the refusal. Per-line and INDEPENDENT of `output_mode`, for the same
                    # reason the poll just above is: a report must not be missed because of an
                    # unrelated display flag. The worker is NOT blocked - it emitted the token and
                    # continued (R3.1) - and nothing here prompts (R3.2).
                    #
                    # PLACED AFTER THE POLL, not beside the stall-watchdog heartbeat above, on
                    # purpose: `test_runner_stop.py::PollWiringTests` bounds the CHARACTER DISTANCE
                    # from that heartbeat to this poll (to prove the poll sits at the per-line
                    # checkpoint), and inserting this block between them pushed the gap past its
                    # window. The ordering is behaviorally equivalent - both run for EVERY line,
                    # before any `output_mode` branch - so honoring the sibling bound costs nothing.
                    # Do not name that heartbeat symbol in this comment: the sibling test locates it
                    # with `rindex`, so a mention here would become the anchor it measures from.
                    missing_input.note_line(line, run_dir, item, attempt_no)
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
                    # THE PARSE IS DELIBERATELY NOT `render_event`. Even though `render_event` updates
                    # `tracker` across output modes below, the detector in `runner_stop` does its own
                    # minimal decode and runs for EVERY line here, before any mode branch. Do not move
                    # it into the branch below.
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
                                        run_dir, item, request, checkpoint_observer
                                    ),
                                    is_alive=lambda: process.poll() is None,
                                )
                                breach_watch.__enter__()
                    if checkpoint_observer.observe(line):
                        # The turn stops HERE, after an event observed to have completed. Raising
                        # unwinds into the existing `except BaseException` below, which already
                        # routes to the shared reaper, so no second teardown path exists (spec R5).
                        raise runner_stop.StopAtCheckpoint(checkpoint_observer)
                    if output_mode == "raw":
                        sys.stdout.write(line)
                        sys.stdout.flush()
                        if tracker is not None:
                            render_event(
                                line,
                                pal,
                                tracker=tracker,
                                verbosity=verbosity,
                                repo_root=agent_dir,
                            )
                    elif output_mode == "clean":
                        rendered = render_event(
                            line,
                            pal,
                            tracker=tracker,
                            verbosity=verbosity,
                            repo_root=agent_dir,
                        )
                        if rendered is not None:
                            statusline.write_event(rendered)
                    elif tracker is not None:
                        render_event(
                            line,
                            pal,
                            tracker=tracker,
                            verbosity=verbosity,
                            repo_root=agent_dir,
                        )
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
    repo: Path,
    item: dict[str, Any],
    run_dir: Path,
    exit_code: int,
    plan_repo: Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Score one finished turn. `plan_repo` (`ajxr5d` E-09) is the tree to READ THE PLAN FROM.

    DEFAULTED TO `repo`, so every existing call site and every existing behavior is unchanged; passed
    only by the main-turn call site, and only when the turn ran in a lane. See the review branch below
    for why an isolated review MUST read the lane, and why there is no "read it after the merge instead"
    alternative.
    """
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
        # dirtygates Order 05 (`ajxr5d`) E-09: READ THE PLAN FROM THE TREE THAT HOLDS THE REVISION.
        #
        # THE DEFECT, and it is a SCORING defect rather than a cosmetic one. This branch derives the
        # disposition from the plan's `- Status:` field. Once a review runs in a lane, the revised plan is
        # ON THE LANE and MAIN still reads `to-review` until the merge lands, so a `repo`-only read makes
        # the status comparison ALWAYS miss: a review that legitimately set `approved` would be recorded
        # merely `reviewed`, and the check would stop discriminating at all, so it could no longer help
        # tell a real review from a turn that did nothing.
        #
        # THE LANE READ IS THE ONLY REACHABLE ANSWER, not a preference (plan finding F-15). The
        # disposition is computed BEFORE the integration block in both hosts, and there is no call to
        # this function anywhere after it, so "compute it after the merge and read main" describes a
        # branch that does not exist. `plan_repo` therefore defaults to `repo`, which keeps the
        # non-isolated read byte-identical, and the main-turn call site passes the lane when there is one.
        #
        # THE PATTERN IS REUSED, NOT INVENTED: the verifier path already resolves its plan as
        # `plan_repo = Path(work_dir) if work_dir else repo` for exactly this reason.
        source = plan_repo or repo
        try:
            current_plan = resolve_plan_path(
                source, item["configured_file"], item["id6"]
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
    # integpath-03 (`51vw4y`) E-01: PASS THE NON-TERMINAL DEFERRAL THROUGH, EXPLICITLY.
    #
    # THIS IS THE SILENT-DOWNGRADE TRAP, and it is the single highest-risk line of this plan rather
    # than bookkeeping. `integration-deferred` is DELIBERATELY absent from `TERMINAL_STATES` (that
    # absence is what makes a re-attempt possible), so the set-difference branch above SKIPS it and
    # control reaches the fallback below, which would relabel a deferred item `partial`. `partial` IS
    # terminal, so the deferral would be destroyed, the item never re-attempted, and today's permanent
    # loss reproduced - while every ladder unit test still passed, because none of them route through
    # here. The status must therefore be named explicitly, on BOTH hosts.
    #
    # It is checked AFTER the outcome block on purpose: an agent's self-reported outcome never gets to
    # CLAIM a deferral (the driver decides that from the real integration attempt), so this reads the
    # status the driver already wrote onto the item.
    if item.get("status") == runner_shared.INTEGRATION_DEFERRED_STATUS:
        return runner_shared.INTEGRATION_DEFERRED_STATUS, outcome
    return ("partial" if exit_code == 0 else "failed-safely"), outcome


def execute_item(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    recovery: bool,
    tracker: StreamTracker | None = None,
) -> None:
    """Execute a single queue item via runner_shared.execute_item_core."""

    def _spawn_executor(
        prompt_path: Path,
        work_dir: Path | None,
        tracker: Any,
        plan_path: Path,
        attempt_no: int,
        session_id: str | None,
        use_continue: bool,
    ) -> tuple[int, str | None, Path, list[str]]:
        return run_opencode(
            state,
            run_dir,
            item,
            plan_path,
            prompt_path,
            attempt_no,
            tracker=tracker,
            work_dir=work_dir,
        )

    def _spawn_verifier(
        v_prompt_file: Path,
        current_plan_path: Path,
        work_dir: Path | None,
        tracker: Any,
        attempt_no: int,
    ) -> tuple[int, str | None, Path, list[str]]:
        return run_opencode(
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
            use_verifier_launch=True,
            telemetry_phase=runner_shared.TELEMETRY_PHASE_VALIDATE,
        )

    runner_shared.execute_item_core(
        run_dir,
        state,
        item,
        recovery,
        host_labels=runner_shared.OC_HOST_LABELS,
        spawn_executor=_spawn_executor,
        spawn_verifier=_spawn_verifier,
        raw_launcher=run_opencode,
        run_suite_check=run_suite_check,
        process_backlog_close=process_backlog_close,
        driver_module=sys.modules[__name__],
        tracker=tracker,
    )


# runrecon-02 (`fduoj4`) E-01: one-line wrapper over the shared `reconcile_interrupted`, binding THIS
# driver's `save_state`. The body was FORKED per host and the two copies had DIVERGED in one code line
# (oc indexed `item["configured_file"]`, agy used `.get(..., "")`, so oc raised `KeyError` past an
# `except DriverError` that does not catch it and aborted the whole loop before `save_state`); the
# shared version keeps agy's tolerant form. `save_state` is injected rather than imported because it
# needs `write_report`, which is class (c) DIVERGED: the maintainer's `818uru` OQ-02 wrapper ruling.
# Keeping the original name and signature is what leaves this module's call sites untouched.
def reconcile_interrupted(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.reconcile_interrupted(run_dir, state, save_state=save_state)


def requeue_interrupted(run_dir: Path, state: dict[str, Any]) -> list[str]:
    """Re-queue items left `interrupted` so resume retries in recovery mode.

    hostdedup Order 01 (`li44r9`) E-02: a thin wrapper over the ONE definition in `runner_shared`, which
    holds the full rationale, including why the INDETERMINATE refusal must live in the requeue itself
    rather than beside it (runstop m0z0ti E-04, spec R19, orchestrator CID-4).
    """
    return runner_shared.requeue_interrupted(run_dir, state)


def _observe_between_turn_stop(
    run_dir: Path,
    level: int | None,
    current_setid: str | None,
    existing: runner_stop.WindDown | None,
) -> runner_stop.WindDown | None:
    """Turn a polled stop LEVEL into a level-1/2 wind-down, capturing the set boundary ONCE.

    hostdedup Order 01 (`li44r9`) E-02: a thin wrapper over the ONE definition in `runner_shared`, which
    holds the full rationale for freezing the captured `setid` at first observation and for leaving
    levels 3 and 4 to later phases (runstop 1qxuke).
    """
    return runner_shared._observe_between_turn_stop(
        run_dir, level, current_setid, existing
    )


def _record_deliberate_stop(
    run_dir: Path, state: dict[str, Any], wind_down: runner_stop.WindDown
) -> None:
    """Append the DELIBERATE-stop ledger event (spec R21) and leave un-run items `queued`.

    hostdedup Order 01 (`li44r9`) E-02: a thin wrapper over the ONE definition in `runner_shared`, which
    holds the full rationale for using the established `events.jsonl` channel and for inventing no
    per-item status (runstop 1qxuke, spec R20/R21).
    """
    return runner_shared._record_deliberate_stop(run_dir, state, wind_down)


def run_queue(
    run_dir: Path,
    retry_incomplete: bool,
    output_mode: str | None = None,
    verbosity: int | None = None,
) -> int:
    state = load_state(run_dir)
    # bkclose (zhr6mc) E-06: publish the live ledger for the shutdown report BEFORE any turn starts,
    # so an interrupt at any point reports from real state. NO `signal.signal` registration here: it
    # is owned by `runstop` Phase 5 (`71vjbn`) and guarded by four executed plans (see the ownership
    # note on `signal_report_callback`). `register_signal_report` is called again after each state
    # reload so the report never runs off a stale snapshot.
    register_signal_report(run_dir, state)
    # streamfmt (mm6wuz) E-05: a resume may RE-CHOOSE the display tier, exactly as it may re-choose
    # `output_mode`. `None` means the operator did not pass the flag, so the frozen value is left
    # alone; `argparse` supplies `default=0` on `start`, so a bare `start` freezes 0.
    #
    # BOTH SETTINGS SHARE ONE `save_state` CALL deliberately. This used to be a bare
    # `if output_mode is not None: ...; save_state(...)` and adding a second such block would add a
    # second `save_state` CALL SITE, which `tests/test_runner_shared.py::WrapperTests::
    # test_no_call_site_was_rewritten` counts and pins per runner. Writing both display options in
    # one persist is also simply correct: they are set together on the same resume.
    display_options = {
        key: value
        for key, value in (
            ("output_mode", output_mode),
            ("verbosity", None if verbosity is None else int(verbosity)),
        )
        if value is not None
    }
    if display_options:
        state.setdefault("options", {}).update(display_options)
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
                # integpath-03 (`51vw4y`): a DEFERRED integration can outlive its run (an interrupt or
                # a crash between the deferral and the next loop iteration), and it is by definition
                # non-terminal, so a resume must be able to pick it up. Listed here rather than left to
                # the ladder alone because the ladder only runs inside a live dispatch loop.
                "integration-deferred",
                # `l2mzxn` renamed all four. BOTH vocabularies are listed because this set is matched
                # against a status read from a DURABLE run directory: the pre-rename spellings keep an
                # already-stranded item recoverable, and the canonical ones cover every new run.
                "merge-needs-human",
                "merge-refused",
                "merge-retry",
                "merge-unchecked",
            }:
                # integpath-04 (`rl67b0`) E-03/E-04: REMEMBER the status being overwritten. This flip
                # runs BEFORE the point where the integration pass may legally sit (the pass must
                # follow the indeterminate refusal below, which itself follows this block), so by then
                # `item["status"]` no longer says the item was `integration-blocked`. The integration
                # pass therefore selects on DURABLE LANE FACTS plus this recorded prior disposition,
                # and E-04's hold-back restores exactly this value rather than inventing one. Additive,
                # so nothing that reads `status` is affected.
                item["requeue_from_status"] = item["status"]
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
    # integpath-04 (`rl67b0`) E-03/E-04: MERGE ALREADY-VERIFIED LANES INSTEAD OF RE-DISPATCHING THEM.
    #
    # PLACEMENT IS THE SUBSTANCE OF THIS CHANGE, so it is stated exactly. It sits AFTER the
    # indeterminate refusal above, because that refusal `return 1`s before anything starts and main must
    # NOT be mutated during a resume the driver is about to decline; and BEFORE the dispatch loop below,
    # because once an item is dispatched the lane has already been attempt-scoped into a second branch
    # and the finished one abandoned. The `--retry-incomplete` requeue above only rewrites
    # `status`/`recovery_next` in memory-plus-state and dispatches nothing, so acting after it is still
    # strictly before any turn is launched; what it DOES mean is that the pass cannot select on
    # `status`, which is why it selects on durable lane facts and on `requeue_from_status`.
    #
    # NO SECOND LOCK: `run_queue` is only ever entered under `locked_run`, so the run lock is already
    # held here. NOT BEHIND A FLAG: the alternative default is silent re-dispatch of finished work,
    # which is the measured defect. It CANNOT ABORT THE RESUME: every failure inside is converted to a
    # recorded refusal, and the loop below still runs.
    #
    # NO STATE RELOAD AND NO `register_signal_report` REFRESH HERE, deliberately. The pass MUTATES the
    # very `state` dict this function holds and persists it through the injected `save_state`, so the
    # in-memory view is already current and the published reporter reference is still the same object; a
    # reload would rebind `state` to an equal dict for no gain, and would add a sixth
    # `register_signal_report` site to a function whose five sites are pinned as a measured invariant
    # (`tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned`). The loop below reloads
    # on its own first iteration regardless.
    _integrate_stranded_lanes(run_dir, state)
    tracker = StreamTracker()
    invocation_start_mono = time.monotonic()
    state["_invocation_start_mono"] = invocation_start_mono
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
        state["_invocation_start_mono"] = invocation_start_mono
        # bkclose (zhr6mc) E-06: `state` is REBOUND to a fresh dict on every reload, so the handler's
        # published reference must be refreshed or it would report from a stale snapshot taken before
        # the turns that actually linked the items.
        register_signal_report(run_dir, state)
        wind_down = _observe_between_turn_stop(run_dir, level, current_setid, wind_down)
        # 8guhs0 E-04: cascade FIRST. An item whose prerequisite already reached a non-success
        # terminal state can never become runnable, so mark it (and its dependents, transitively)
        # `dependency-blocked` and keep going with independent work rather than stalling the queue.
        if cascade_dependency_blocked(state, run_dir):
            save_state(run_dir, state)
            state = load_state(run_dir)
        # integpath-03 (`51vw4y`) E-03: RUNG 1. Re-attempt every DEFERRED integration here, at the top
        # of the loop, which is why it costs nothing: this loop already reloads state and already
        # cascades each iteration, so the previous item's completion IS the natural retry trigger. Zero
        # waiting, zero tokens, no agent turn. Every attempt routes through the full revalidate gate.
        #
        # ORDERED AFTER THE CASCADE DELIBERATELY: `integration-deferred` is NOT in `TERMINAL_STATES`,
        # so the cascade leaves a deferred item's dependents alone rather than killing them, and an
        # integration that succeeds HERE promotes the item to `executed` before the selection below
        # asks whether anything depends on it. That ordering is what converts the measured seven-of-34
        # cascade loss into no loss at all.
        if runner_shared.deferred_integration_items(state):
            retry_deferred_integrations(run_dir, state)
            save_state(run_dir, state)
            state = load_state(run_dir)
            register_signal_report(run_dir, state)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued and not runner_shared.deferred_integration_items(state):
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
            # integpath-03 (`51vw4y`) E-04/E-05: RUNGS 2 AND 3, and `runnable is None` IS the trigger.
            #
            # THE TRIGGER IS "is there anything else I could dispatch", not "is this the last item",
            # and that distinction is why this sits here rather than behind a queue-length test: this
            # one condition covers BOTH the last-item case and the case where five items remain and ALL
            # are deferred, which a last-item test would miss entirely.
            #
            # Rung 2 polls, bounded BOTH by count and by main's activity staleness; rung 3 then asks,
            # suppressed without a TTY and bounded by its own timeout. `ask=True` is passed
            # unconditionally because the SHARED ladder resolves the interactive predicate itself
            # (`is_interactive_run`, which also honors `--unattended`), so an unattended overnight run
            # can never stop on a question nobody will see.
            #
            # SPEC OQ-03: the run must NOT end leaving an item in a non-terminal state, so after these
            # rungs any still-deferred item is resolved to terminal `integration-blocked` with the lane
            # preserved, which is today's honest outcome reached LAST instead of FIRST.
            if runner_shared.deferred_integration_items(state):
                retry_deferred_integrations(run_dir, state, poll=True, ask=True)
                save_state(run_dir, state)
                state = load_state(run_dir)
                register_signal_report(run_dir, state)
                if runner_shared.deferred_integration_items(state):
                    runner_shared.resolve_exhausted_deferrals(
                        run_dir,
                        state,
                        save_state=save_state,
                        append_jsonl=append_jsonl,
                    )
                    save_state(run_dir, state)
                if [it for it in state["queue"] if it["status"] == "queued"]:
                    # An integration that landed during the rungs above can have unblocked a dependent,
                    # so go round again rather than declaring the queue drained.
                    continue
            # depblock 01 (`akzy45`) E-02: CLASSIFY BEFORE LABELLING. This loop used to write the
            # TERMINAL `dependency-blocked` on EVERY remaining queued item unconditionally, which
            # conflated "not ready yet" with "can never be ready" and made the first one unrecoverable
            # without `--retry-incomplete`. The shared predicate decides which of the two each item is;
            # a PERMANENT verdict takes the byte-identical path below, and a TRANSIENT one is left
            # `queued` and REPORTED instead. The classification is host-neutral and lives in
            # `runner_shared`, never here, so agy's copy of this arm cannot drift from it.
            for item in queued:
                _, missing, why = dependency_status_detailed(item, state)
                verdict = classify_drain_block(
                    item,
                    state,
                    missing,
                    why,
                    terminal_states=TERMINAL_STATES,
                    success_states=EXECUTION_SUCCESS_STATES,
                    review_success_states=SUCCESS_STATES,
                    parse_token=parse_dependency_token,
                )
                if verdict.transient:
                    # WRITE NO STATUS, exactly as `dispatch_orchestrator_item`'s RECONSIDER outcome
                    # does. The item stays `queued`, so the NEXT invocation re-tests it with no flag -
                    # a bare `resume` re-queues an `interrupted` prerequisite through
                    # `requeue_interrupted`. The record is still written: an unlabelled item with no
                    # event would be indistinguishable from one never reached.
                    record_transient_dependency_wait(
                        run_dir,
                        item,
                        verdict,
                        unsatisfied=missing,
                        reasons=why,
                        append_jsonl=append_jsonl,
                    )
                    continue
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
                        # depblock 01 (`akzy45`): the classification that JUSTIFIED the terminal label,
                        # so a reader of the stream can see it was decided rather than assumed.
                        "block_class": verdict.verdict,
                        "block_detail": verdict.detail,
                    },
                )
            save_state(run_dir, state)
            break
        recovery = bool(runnable.pop("recovery_next", False))
        update_execution_order(state, runnable)
        # Orchestrators are NOT agent-executed. orchretire-03 (`pgq326`) E-01/E-02: the outcome is the
        # SHARED three-way `dispatch_orchestrator_item`, replacing the single `else` that wrote a
        # TERMINAL `dependency-blocked` on ANY failure.
        #
        # WHY THE SINGLE WRITE WAS WRONG, both halves measured on real runs. `dependency-blocked` is in
        # `TERMINAL_STATES` and the selection filter admits only `queued`, so an orchestrator whose
        # children finished LATER IN THE SAME RUN was excluded forever, from an event literally named
        # `orchestrator-deferred`. But "just leave it queued" (backlog `kxkc04`) fixes only ONE of the
        # two failures that `else` covered: one run recorded both `not-all-children-executed` AND
        # `finalize-refused`, and leaving the second reconsiderable would retry a structural refusal
        # every iteration and SPIN. Hence three outcomes; `runner_shared` carries the full contract.
        if runnable.get("action") == "orchestrate":
            repo = Path(state["repo"])
            dispatch_orchestrator_item(
                repo,
                run_dir,
                state,
                runnable,
                actor=driver_actor(state),
                terminal_states=TERMINAL_STATES,
                success_states=EXECUTION_SUCCESS_STATES,
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
            raise
        except KeyboardInterrupt:
            # laneorphan-01 (`zwnjp3`) E-05: PRESERVE-AND-RECORD before the interrupt propagates,
            # so the run does not leak lanes (which wedged the next run at allocation) and does not
            # destroy any lane holding work. Wired into this EXISTING teardown path; NO signal handler
            # is registered here (`runstop` Phase 5 `71vjbn` owns SIGINT/SIGTERM registration).
            if "just-terminate-no-cleanup" in str(sys.exc_info()[1] or ""):
                save_state(run_dir, state)
            else:
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
        else:
            # reaskscore-03 (`dy9ymn`) E-04/E-06: A TURN THAT PROVABLY ATTEMPTED NOTHING GETS ONE MORE
            # ATTEMPT INSTEAD OF TAKING ITS WHOLE SET DOWN.
            #
            # PLACEMENT IS THE SUBSTANCE, so it is stated exactly. It is INSIDE the dispatch loop, on
            # the `else` of the `try` above, so it runs when and only when `execute_item` RETURNED
            # (never after a deliberate stop, an interrupt, or a `DriverError`, each of which breaks or
            # re-raises). The requeue SHAPE it copies lives in the pre-loop `--retry-incomplete` block,
            # and that is the WRONG PLACE for the call: that block runs BEFORE `while True:` and
            # inspects statuses left by a PREVIOUS invocation, so a check placed there would never
            # observe a zero-work turn that happened during THIS run.
            #
            # AND IT MUST PRECEDE THE CASCADE, which is why "inside the loop" is not enough on its own:
            # `cascade_dependency_blocked` runs at the TOP of the loop and first sees this turn's
            # terminal status on the NEXT iteration, by which point the siblings would already be
            # `dependency-blocked` and a retry would rescue nothing. The window between here and that
            # iteration is generous, but it is not optional.
            #
            # THE RULE ITSELF IS SHARED (spec `7ckptx` R2.6/R6.1) and this host contributes only the
            # seam and its own `save_state`/`append_jsonl`/labels bindings, so the two drivers cannot
            # drift on the predicate, the budget arithmetic, or the event.
            runner_shared.handle_zero_work_retry(
                repo=Path(state["repo"]),
                run_dir=run_dir,
                state=state,
                item=runnable,
                host_labels=runner_shared.OC_HOST_LABELS,
                save_state=save_state,
                append_jsonl=append_jsonl,
            )
    state = load_state(run_dir)
    # dirtygates Order 05 (`ajxr5d`) E-11: RETIRE THE REVIEW SWEEP LANE, once, HERE.
    #
    # WHY HERE AND NOT PER ITEM. The sweep lane is ONE tree serving every review in the run, so the only
    # correct owner of its teardown is the coordinator at the point where no further review can be
    # dispatched. A per-item teardown would delete the lane the next review needs. This also closes the
    # gap finding F-12 measured: `teardown_isolation_worktree` has exactly ONE call site per host and it
    # is gated on `driver_finalize`'s return code, which a review never produces, so a review lane had NO
    # reachable teardown at any nesting.
    #
    # IT CLASSIFIES BEFORE DESTROYING and therefore PRESERVES a lane that still holds work - a stranded
    # review whose merge conflicted, or an interrupt between reviews. That is the shared spec-R5.5 gate's
    # decision, not a second classifier: `teardown_isolation_worktree`'s own docstring forbids calling it
    # on a lane holding work, and force-removing a stranded review's lane would turn a recoverable
    # stranding into destroyed work.
    #
    # PLACED AFTER THE LOOP AND BEFORE THE REPORT so the report renders the retirement's outcome; and it
    # is IDEMPOTENT, so wiring it into a second exit path later cannot double-retire.
    with contextlib.suppress(Exception):
        runner_shared.retire_review_sweep_lane(
            Path(state["repo"]), run_dir, state, save_state=save_state
        )
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
            state,
            run_dir,
            tracker=tracker,
            pal=pal,
            exit_reason=exit_reason,
            driver_label="opencode",
        )
    )
    # runnoop Order 02 (`m85gxh`) E-03: THE PER-ARTIFACT DISPOSITION LINE, carrying the REASON.
    #
    # WHAT THIS ADDS THAT THE TABLE ABOVE DOES NOT, stated because the obvious reading is that it
    # duplicates it. The summary table already renders one ROW per matched artifact with its
    # disposition, INCLUDING an item with zero attempts; measured, a single `reviewed`/zero-attempt
    # item yields `01 | 01 | abc123 | wtiso | execute | reviewed` and the word `approval` appears
    # ZERO times in the whole render. So the missing thing was never the line, it was the REASON: a
    # reader saw `reviewed` and had to already know it meant "frozen, needing human approval, never
    # dispatched". This block supplies exactly that, for every matched artifact, from the facts the
    # runner already computed (`zz5yxq`'s durable needs-approval flag, the dependency reason strings,
    # `r2i1b1`'s refusal record).
    #
    # ONE CLOSING PASS OVER THE QUEUE, and that resolves the plan's OQ-01. The alternative (emit at
    # each item's termination) cannot cover this plan's whole point, because an artifact that is never
    # dispatched HAS no termination point, so that shape needs a closing pass anyway; and one pass
    # makes "exactly one line per matched artifact" STRUCTURAL rather than a discipline, since the
    # queue holds exactly one entry per matched artifact however many ATTEMPTS it accumulated. Live
    # per-item feedback already exists (the finish line in `runner_shared.execute_item_core`), so
    # nothing is lost by making this the retrospective surface.
    #
    # ONE CALL SITE PER HOST, deliberately, and NOT also on the interrupt/`DriverError` paths that
    # render their own summary: six call sites for one block is the duplication shape this repository
    # keeps paying for, and those paths are aborted runs whose dispositions are still mid-flight,
    # whereas the measured defect (a queue of `reviewed` plans, acted on by nothing) exits through
    # THIS path - the selection loop finds no `queued` item and breaks straight to here.
    #
    # The WORDING and the reason vocabulary live in the pure `run_selection_policy` module, never in a
    # driver, and both hosts import that module directly rather than one host importing from the
    # other. `refusal_of_item` is `r2i1b1`'s ONE reader, passed in so a recorded refusal reaches this
    # line through that plan's seam instead of a second read of the same key.
    for _disposition_line in render_queue_dispositions(
        state.get("queue", []), refusal_reader=refusal_of_item
    ):
        print(_disposition_line)
    # specvis st5klo E-03: the PRIMARY end-of-run site. Sited with the summary table rather than on a
    # new surface, because this is the block an operator already reads at exit; a spec rewrite reported
    # anywhere else would be as easy to miss as it was when the only report was pre-dispatch. NOT
    # `partial`: this path runs after the queue drained normally.
    report_run_spec_edits(state)
    # runnoop Order 03 (`bsc457`) E-03: THE CLOSING DISPOSITION SUMMARY, printed UNCONDITIONALLY,
    # INCLUDING for a run that acted on nothing - which is precisely the case that printed no answer
    # at all. Measured (backlog `em0z50`): `aw oc run wtiso` matched 8 plans, acted on none, and the
    # closing words an operator reacted to were `No OpenCode session was captured for this run.`
    # beneath a table reading `Outcome: COMPLETED` at 100%.
    #
    # UNCONDITIONAL FOLLOWS THE ESTABLISHED PRECEDENT rather than inventing a rule: `announce_run_order`
    # prints the run order whether or not anything was reordered, and its docstring gives the reason
    # ("the order must be auditable in the log even when nothing was reordered"). The argument is
    # stronger at exit, because the zero-action case is exactly the one a conditional print would skip.
    #
    # AT THE END AND SELF-CONTAINED (the plan's OQ-01, resolved from the maintainer's four-place ruling
    # recorded in `r2i1b1`'s OQ-01): the block repeats its own counts and remedies rather than referring
    # upward to the table, because readers pipe this output through `head` or `tail`. The START side is
    # already satisfied by `announce_run_order`, and a start-side print could not carry dispositions
    # that do not exist yet.
    #
    # BEFORE the continuation footer deliberately: the footer is session-continuity plumbing, so the
    # answer to "what did this run do?" must not sit beneath it. The wording and the remedy table live
    # in the pure `run_selection_policy` module, never in a driver, and `refusal_of_item` is
    # `r2i1b1`'s ONE reader, so a recorded refusal's own remedy is SOURCED rather than duplicated here.
    for _summary_line in render_disposition_summary(
        state.get("queue", []), refusal_reader=refusal_of_item
    ):
        print(_summary_line)
    print(render_continuation_hint(state, run_dir))
    state["_summary_table_printed"] = True
    # bkclose (zhr6mc) E-06/E-07: the NORMAL-exit half of the shutdown report. `emit_shutdown_report`
    # is the SAME idempotent routine the signal handlers use, so the normal and signal paths cannot
    # drift apart, and whichever fires first suppresses the other. Ledger BEFORE print, so an
    # uncatchable kill still leaves the answer on disk.
    register_signal_report(run_dir, state)
    emit_shutdown_report()
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
    #
    # runnoop zz5yxq (E-02), question (2) of the classification at `runner_shared.SUCCESS_STATES`:
    # "did the run succeed overall?". THE BAR IS NOW PER-ITEM AND ACTION-AWARE. It used to hand the
    # raw statuses against `SUCCESS_STATES`, which contains `reviewed` - correctly, for a REVIEW pass.
    # But `action_for` routes a `reviewed` plan to `execute` while the queue builder freezes it as
    # queue status `reviewed` rather than `queued`, so such an item is NEVER DISPATCHED and was then
    # counted a success: measured, `aw oc run wtiso` with 8 `reviewed` plans captured no session, ran
    # 0 attempts, and exited 0 (backlog `em0z50`). `exit_code_statuses` projects each entry onto the
    # bar its OWN action earns before the shared predicate judges it, so a `reviewed` EXECUTE item
    # exits 1 while a `reviewed` REVIEW item still exits 0. NO STATUS IS REWRITTEN (spec R22) and
    # `queued` is passed through verbatim so the deliberate-stop concession above still applies.
    return runner_stop.deliberate_stop_exit_code(
        runner_shared.exit_code_statuses(state["queue"]),
        success_states={runner_shared.EXIT_SUCCESS_TOKEN},
        stopped=wind_down is not None or stopped_at_checkpoint,
    )


# `locked_run` is now defined ONCE in `runner_shared` and reached through the thin wrapper above
# (hostdedup Order 01, `li44r9`). A SECOND definition used to sit here and SHADOWED that wrapper,
# which is why the anti-re-fork guard asserts one definition per host rather than merely that a
# wrapper exists: the wrapper existed and was unreachable.


# rununify 04 (`tx6q0h`): one-line wrappers over the shared definitions. The argv tokens and the
# host product name are DATA in `runner_shared.OC_HOST_LABELS`, not a second copy of the logic.
def _detect_driver_command() -> str:
    return runner_shared.detect_driver_command(labels=runner_shared.OC_HOST_LABELS)


def render_continuation_hint(
    state: dict[str, Any],
    run_dir: Path,
    driver_cmd: str | None = None,
) -> str:
    return runner_shared.render_continuation_hint(
        state, run_dir, driver_cmd, labels=runner_shared.OC_HOST_LABELS
    )


def _add_output_mode_flags(
    sub_parser: argparse.ArgumentParser,
    verbosity_default: int | None = 0,
) -> None:
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
    # streamfmt (mm6wuz) E-05: verbosity TIERS within the default `clean` stream, which is why this
    # is NOT part of the mutually exclusive group above: `--raw`/`--quiet` choose WHICH renderer
    # runs, `-v` tunes how much the `clean` renderer shows. Deliberately NOT registered in
    # `runner_shared.RUN_POLICY_FLAGS`: that table is the closed flag list spec `25kzda` 2.1
    # declares and `tests/test_run_flag_surface.py` asserts against the spec file, so adding a
    # display flag there would fail `test_no_owned_flag_is_absent_from_the_spec`. This is a display
    # flag, exactly like the `--quiet`/`--raw` pair it sits beside.
    #
    # `verbosity_default` is `0` on `start` (a bare run freezes tier 0) and `None` on `resume`, so an
    # OMITTED flag on resume leaves the frozen value untouched rather than silently resetting it to
    # 0. That is the same `None`-means-absent convention `runner_shared.apply_run_policy_flags_on_resume`
    # uses for the policy flags.
    sub_parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=verbosity_default,
        help="Increase live stream detail: -v also shows reads and searches (with line ranges "
        "and hit counts), -vv also shows diff hunks and diagnostics. Ignored under --raw/--quiet.",
    )


# rununify 02 (`818uru`) E-06: one-line wrapper over the shared `print_status`, supplying THIS host's
# label. `print_status` is the ONE symbol of the 34 that was not AST-identical across the runners: the
# two bodies were identical EXCEPT for the literal `driver_label="opencode"`. So the host string is a
# parameter and each driver binds its own; the rendered output is byte-identical to before.
def print_status(run_dir: Path) -> None:
    runner_shared.print_status(run_dir, driver_label="opencode")


def print_launch_identity(run_dir: Path) -> None:
    """Print the run's frozen launch identity beneath the status table (E-03).

    A SEPARATE function rather than a line inside `print_status`, deliberately: `test_runner_shared`
    asserts that each host's `print_status` renders BYTE-IDENTICALLY to the shared definition it wraps
    (measured: adding the line there fails with "oc_runipd.print_status diverged from the shared
    definition"). That parity guard exists so the two runners' status output cannot drift, so the
    profile line is emitted by the CALL SITES that want it instead of by the wrapper.

    OpenCode-specific on purpose: `--variant` is an OpenCode flag and the Agy runner has no typed
    equivalent yet, which this plan explicitly defers. `--json` status is untouched, since it dumps
    `state.json` verbatim and already carries `options.launch_profile`.
    """

    try:
        print(f"Launch: {render_launch_identity(load_state(run_dir))}")
    except Exception:
        # Never let a status read fail over a cosmetic line; the table is the contract.
        pass


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
  - reviews:  Every IPD whose next legal action is review, swept in one shared session
              and one shared isolated worktree (so the sweep never writes to the shared
              checkout; each review lands as one merge).
              Spelled 'reviews', 'review', or 'to-review'. Selects IPDs only; specs and
              backlog items are not reachable by any selector yet. Matching nothing is a
              success and exits 0, because a repository with nothing awaiting review is
              the healthy state. 'aw oc review' is the spelled form of this sweep.
              A COMPLETE 'draft' is in this sweep only with --allow-drafts (the draft
              admission gate); an INCOMPLETE draft is never admitted, by any flag.
  - all:      Every actionable pending IPD in the repository

AUTOMATIC STATUS ROUTING:
  - to-review: Runs OpenCode with `/plan-review <plan_path>` to review and improve the plan.
               All reviews in a run share the same OpenCode session for continuity, and
               they run in ONE shared isolated worktree, so no review writes to the shared
               checkout. Each review's plan edit and review record reach the main checkout
               together, as one merge, after its turn.
  - approved:  Executes the plan step-by-step according to the execution runbook.

LAUNCH IDENTITY (model / variant / agent):
  Give it directly, or name a saved profile with the `as` clause:

    aw oc run SELECTOR --model google/gemini-3.7-flash --variant high
    aw oc run as gem SELECTOR

  The `as <profile>` clause is POSITIONAL: it must come first, immediately after
  `run` (or `start`), and the very next token is always the profile name. So a
  profile may safely be named `status` or `all` without shadowing a command, and a
  profile-like token WITHOUT `as` is still just a selector.
  Manage profiles with `aw oc profile`.

  Precedence is per field, highest first:
    explicit --model/--variant/--agent  >  the named profile  >  the configured
    default profile for this runner  >  OpenCode's own default (no argument passed)
  So `--variant high` on top of a profile overrides ONLY the variant and keeps the
  profile's model.

  The resolution is FROZEN when the run is created and recorded in state.json
  (`options.launch_profile`, with per-field provenance). Every turn of the run,
  including the independent verifier turn and every resumed turn, uses that frozen
  identity; editing or deleting the profile afterwards cannot change a run in flight.

  To use the LITERAL selector `as`, end the options first: `aw oc run -- as`.
""",
        epilog="""EXAMPLES:
  # Review EVERYTHING awaiting review, in one shared session (the review sweep).
  # Spelled 'reviews', 'review', or 'to-review'; 'aw oc review' is the same command:
  runipd reviews

  # Review a single pending plan:
  runipd 20260824-ipdrunner-01-pr2nd0-harden.ipd.md

  # Review all to-review plans in a set using an existing session:
  runipd ipdrunner --session <session_id>

  # Execute an approved plan:
  runipd 5ahblp

  # Execute using a saved launch profile (model + variant + agent):
  runipd as gem 5ahblp

  # Same launch, spelled out directly:
  runipd 5ahblp --model google/gemini-3.7-flash --variant high

  # Execute multiple sets and plans in sequence:
  runipd v6zie5 unifyfileio ipdgates execset

  # Resume an interrupted run:
  runipd resume run-20260824T150827Z-2301181

  # Check status of a run:
  runipd status run-20260824T150827Z-2301181
""",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    # stopdisc (`wqq8ua`) E-04: the run-level help matched NOTHING for stop, interrupt or ctrl
    # (measured), so an operator reading the command that STARTS a run was never told that graceful
    # stopping exists. The note POINTS AT the `stop` verb rather than restating its per-level help,
    # which `STOP_VERB_DESCRIPTION` and `STOP_LEVEL_FLAG_HELP` already do well (P8); a second copy
    # would drift, and the drift is the cost. The text is `runner_stop`'s, so both hosts and both
    # verbs say the same thing. It contains newlines and an indented command, which is why BOTH
    # parsers below need `RawDescriptionHelpFormatter`.
    _stopping_note = runner_stop.stop_run_help_note(_detect_driver_command())

    start = sub.add_parser(
        "start",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Create a run and execute its queue (default)",
        description="Create a durable queue of IPDs and execute or review them.\n\n"
        + _stopping_note,
    )
    start.add_argument(
        "selectors",
        nargs="+",
        help="One or more target selectors: id6 (e.g. 5ahblp), setid (e.g. execset), plan "
        "filenames/paths, 'reviews' (alias 'review'/'to-review'; every IPD whose next legal "
        "action is review, IPDs only), or 'all'",
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
        help="Exact provider/model identifier for OpenCode (e.g. 'anthropic/claude-3-7-sonnet'). "
        "Overrides the model of a profile named with 'as', leaving its other fields intact",
    )
    start.add_argument(
        "--variant",
        help="Model variant / reasoning effort for OpenCode (e.g. 'high', 'medium', 'low', "
        "'minimal'). Overrides only the variant of a profile named with 'as'",
    )
    start.add_argument(
        "--agent",
        help="Primary OpenCode agent name. Overrides only the agent of a profile named with 'as'",
    )
    # runprofile-06 (`kgpptv`) E-02: WHICH profile verifies, never WHETHER verification happens
    # (that is `--validate`). Takes a profile NAME, not a model: a reference reuses a whole
    # validated profile (its variant and agent too), and an inline model would be the first field
    # to escape the schema's own validation.
    start.add_argument(
        "--verify-with",
        dest="verify_with",
        default=None,
        metavar="PROFILE",
        help="Name the runner profile the INDEPENDENT VERIFIER turn launches with, so a run can "
        "execute with one model and be verified by another. Overrides a profile's own "
        "'verify_with' and the store's 'defaults.verify_with'. Omitted (the default) means the "
        "verifier reuses the executor's launch, exactly as before. This says WHICH profile "
        "verifies, not WHETHER verification runs (that is --validate). OpenCode host only.",
    )
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
    # revsweep 76gsmv E-03: the flag `aw oc review` expands to (spec 25kzda 2.1). It NARROWS, never
    # widens: `--action review` refuses any selected item whose next legal action is not review,
    # BEFORE the queue is frozen, so the word "review" can never execute a plan. `plan`/`execute` are
    # registered for grammar parity and refuse honestly rather than being silently accepted.
    start.add_argument(
        "--action",
        choices=ACTION_CHOICES,
        default=None,
        help="Require a specific action for every selected item. Only 'review' is implemented: it "
        "refuses the run if any selected plan's next legal action is not review, so it can never "
        "execute a plan. 'plan' and 'execute' are accepted by the grammar and refused as not yet "
        "implemented. This is what 'aw oc review' expands to.",
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
    # runflags-01 (`uyeko5`) E-01..E-07: spec `25kzda` 2.1's EIGHT policy flags, registered from the
    # SHARED table so the two hosts cannot declare seven of them and then drift on the eighth - which
    # is exactly what happened to `--full-auto`, whose default was `False` here and `True` on agy
    # until E-07 normalized it. `--full-auto` is included in the table, so it is NO LONGER declared
    # by hand here; its help text and `BooleanOptionalAction` moved into `RUN_POLICY_FLAGS` unchanged.
    runner_shared.register_run_policy_flags(start)
    start.add_argument(
        "--validate",
        "--verify",
        "--audit",
        dest="validate",
        action=argparse.BooleanOptionalAction,
        # hostdefault-02 (`ybkmzp`) E-03: `None`, NOT `False`, matching this driver's `resume` parser
        # which has always shipped `default=None` for exactly this reason. The flag is a genuine
        # TRI-STATE now: `None` means the operator said nothing, which falls THROUGH to the
        # runner-profile store's per-model choice, while an explicit `--no-validate` is a decision
        # that wins over every stored tier. With `default=False` those two cases are
        # indistinguishable, so a stored `validate: true` could never take effect.
        #
        # THE EFFECTIVE DEFAULT IS UNCHANGED: with nothing configured, tier 4 is
        # `RUNNER_REGISTRY["oc"].validate_default`, which is `False`, so a bare invocation still does
        # NOT verify. Only the mechanism moved, from a parser default to the resolver's bottom tier.
        default=None,
        help="Run the turn-2 independent clean-session verification of executed plans (default: the "
        "runner-profile store's per-model choice, which on this host resolves to false when nothing "
        "is configured; pass --validate to enable for this run)",
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
        # stopdisc (`wqq8ua`) E-04 / DECISION 03-wqq8ua-D3: `RawDescriptionHelpFormatter` ADDED here.
        # `start` above has always had it; `resume` did not, and argparse's DEFAULT formatter REFLOWS a
        # description, so the stopping paragraph below would collapse onto one line with its indented
        # command inlined (reproduced with a minimal argparse case at execution time). The keyword is
        # behavior-neutral for PARSING - argparse consults `formatter_class` only when formatting
        # usage/help - and it makes `start` and `resume` render their help the same way, which is what
        # an operator comparing the two verbs expects.
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help="Resume an existing run",
        description="Resume an interrupted run or retry incomplete items in recovery mode.\n\n"
        + _stopping_note,
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
    # runflags-01 (`uyeko5`) E-06: the same eight flags on `resume`, every one with `default=None`.
    # That is the SHIPPED `--full-auto` pattern and it is what makes an OMITTED flag preserve the
    # frozen value: with `default=False`, resume could not tell "the operator passed `--no-X`" from
    # "the operator passed nothing" and would clobber frozen policy on every resume.
    # `--retry-budget` is registered here too although it is REFUSED (spec `:131` freezes it), because
    # refusing it needs argparse to accept it first; otherwise the operator is told the flag does not
    # exist instead of being told the frozen value cannot change.
    runner_shared.register_run_policy_flags(resume, resume=True)
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
    resume.add_argument(
        "--variant",
        help="Override model variant / reasoning effort for OpenCode",
    )
    # runprofile-06 (`kgpptv`) E-02: registered with `default=None` so an OMITTED flag can never
    # clobber the frozen verifier launch, which is the `--full-auto`/`--retry-budget` pattern. When
    # it IS passed, it is REFUSED (see the refusal below), for the same reason `as <profile>` is
    # refused on resume: honoring a profile NAME requires re-reading `runner-profiles.json`, and
    # `3cm15q` E-04 forbids a resume from re-resolving it. Registered anyway because refusing needs
    # argparse to accept the flag first; otherwise the operator is told the flag does not exist
    # instead of being told the frozen value cannot change (DECISION 06-kgpptv-D5).
    resume.add_argument(
        "--verify-with",
        dest="verify_with",
        default=None,
        metavar="PROFILE",
        help="Refused on resume: the verifier launch is frozen when the run is created, because "
        "honoring a profile name here would mean re-reading runner-profiles.json. Omit it and the "
        "frozen value is used; start a new run to verify with a different profile.",
    )
    _add_output_mode_flags(resume, verbosity_default=None)

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

    # runstop 71vjbn (E-03, spec R14/R15): the OUT-OF-BAND stop verb, declared through the SHARED
    # helper so both drivers expose the SAME verb rather than two that merely agree today
    # (orchestrator CID-3). It is declared on THIS parser, where `start` already lives, and NOT on
    # `cli.py`'s `oc` group, because `aw oc run` forwards `argparse.REMAINDER` verbatim to this
    # `main` - re-declaring the flags there would drift and would bypass the implicit-start shim that
    # lives in `main()` rather than here.
    runner_stop.add_stop_parser(sub, command=_detect_driver_command())

    # integpath-04 (`rl67b0`) E-02: the OUT-OF-BAND `integrate` verb, declared through the SHARED
    # helper for exactly the reason `stop` is (orchestrator CID-3: a verb must not exist on one host
    # only, and its help text must not drift between them). Declared on THIS parser, where `start`
    # already lives, because `aw oc run` forwards `argparse.REMAINDER` verbatim here; `cli.py` carries
    # a THIN host-noun alias (`aw oc integrate`) that rewrites argv into this same subcommand, and
    # nothing else.
    runner_shared.add_integrate_parser(sub, command=_detect_driver_command())

    # reverify-01 (`mp289j`) E-05: the OUT-OF-BAND `audit` verb, declared through the SHARED helper
    # for the same reason `stop` and `integrate` are (a verb must not exist on one host only, and its
    # help text must not drift between them), and on THIS parser because `aw oc run` forwards
    # `argparse.REMAINDER` verbatim to this `main`. Like those two it MUST also appear in the
    # implicit-start shim's subcommand set below, or `audit <id6>` launches a RUN with `audit` as a
    # selector.
    runner_shared.add_audit_parser(sub, command=_detect_driver_command())

    return parser


def handle_integrate_command(args: argparse.Namespace) -> int:
    """Execute the `integrate` verb: re-attempt integration for one verified lane, NO agent turn.

    integpath-04 (`rl67b0`) E-02. THIN, and thin is the contract rather than a style note: the WHOLE
    decision (lane resolution from durable state, the five refusals, the live-owner refusal, the real
    validation runner, the gate call) is `runner_shared.reintegrate_lane`, which the resume pass calls
    too. This binds only what is host-specific - this host's `integrate_lane_branch` wrapper, so a
    recovered merge subject still reads `integrate(aw oc run): ...`, and this host's `run_suite_check`,
    which the shared module may not import (`tests/test_runner_shared.py::NoRunnerImportTests`).

    EXIT CONTRACT: 0 integrated, 1 refused (nothing was merged, main untouched, the lane preserved),
    2 for a usage/driver error, which is the contract every other verb here has.
    """

    repo = Path(getattr(args, "repo", ".") or ".").resolve()
    id6 = str(getattr(args, "id6", "") or "")
    outcome = runner_shared.reintegrate_lane(
        repo,
        id6,
        integrate=integrate_lane_branch,
        suite_check=run_suite_check,
        run_id=getattr(args, "run_id", None),
    )
    message = runner_shared.render_reintegration_result(outcome, id6=id6)
    print(message, file=sys.stdout if outcome.integrated else sys.stderr)
    return 0 if outcome.integrated else 1


def handle_audit_command(args: argparse.Namespace) -> int:
    """Execute the `audit` verb: ONE fresh-session independent opinion on an already-executed plan.

    reverify-01 (`mp289j`) E-05. This is the host binding; the two DECISIONS that are not
    host-specific live in `runner_shared` and are shared by construction: which plan is auditable and
    what it can be diffed against (`plan_audit_target`), and the prompt itself
    (`build_verifier_prompt(..., audit=True)`).

    NO SECOND VERIFIER, which is backlog `7u9kbm`'s hard constraint and `wlxkoz`'s argument against a
    second completion checker. This function composes NO prompt text of its own: it calls the SAME
    `build_verifier_prompt` the in-run turn calls, with `audit=True`, and launches it through the SAME
    `run_opencode` with the SAME `use_verifier_launch=True` the in-run verifier uses, so the verifier's
    configured model/variant/agent profile applies here too without a second resolution path.

    WHAT IT DELIBERATELY DOES NOT DO, since each omission is a design decision rather than a gap:

      * It mints a run directory but builds NO QUEUE and takes NO run lock. There is exactly one turn
        and no ordering to own, so `initialize_run` (selector expansion, dependency preflight, the
        mixed-type gate, the orchestrator coverage gate) would be machinery with nothing to decide.
        `stop` and `integrate` are the precedent for an out-of-band verb that touches no queue.
      * It performs NO LIFECYCLE TRANSITION and calls neither `aw ipd begin` nor `aw ipd finalize`.
        The subject plan is already terminal; a transition is exactly what OQ-05 forbids.
      * It does NOT INTEGRATE the lane. An audit's job is to form an opinion, and any CODE fix it makes
        is a fix behind a finished plan, which must be reviewed on its own merits rather than
        auto-merged by the verb that asked for it. The lane and its commits are reported by path so an
        operator can inspect, then `aw oc run integrate <id6>` or merge by hand.

    EXIT CONTRACT, matching `integrate`: 0 when the audit turn ran and wrote a verdict, 1 when the
    request was refused (no plan, not executed) or the turn produced no verdict, 2 for a driver error.
    """

    repo = Path(getattr(args, "repo", ".") or ".").resolve()
    id6 = str(getattr(args, "id6", "") or "")
    pal = Palette(should_color(sys.stdout))

    target = runner_shared.plan_audit_target(
        repo, id6, base=getattr(args, "base", None)
    )
    if target.refusal:
        print(f"audit refused ({target.refusal}): {target.reason}", file=sys.stderr)
        return 1

    run_id, run_dir = _fresh_audit_run_dir(repo)
    # ALL THREE, and `sessions/` is not optional decoration: `run_opencode` opens the attempt log with
    # `log_path.open("w")` and does NOT create its parent, so omitting it raises FileNotFoundError at
    # the moment of launch, after the prompt has been written and (with isolation on) after a lane has
    # been allocated. Measured while wiring this verb end to end.
    for sub in ("outcomes", "prompts", "sessions"):
        (run_dir / sub).mkdir(parents=True, exist_ok=True)

    # A MINIMAL STATE, written for the same reason a queued run writes one: the verdict must be
    # readable afterwards by somebody who did not watch the terminal. `action` is `audit` so
    # `aw runs` and the analytics reader can tell this apart from an execute or review turn rather
    # than mis-attributing its cost to an execution.
    item: dict[str, Any] = {
        "position": 1,
        "id6": target.id6,
        "setid": target.setid or "audit",
        "file": str(target.plan_path.relative_to(repo))
        if target.plan_path.is_relative_to(repo)
        else str(target.plan_path),
        "configured_file": "",
        "action": "audit",
        "status": "pending",
        "attempts": [],
    }
    state: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "repo": str(repo),
        "created_at": runner_shared.utc_now(),
        "kind": "audit",
        "queue": [item],
        "options": {
            "opencode": getattr(args, "opencode", "opencode") or "opencode",
            "auto": True,
            # The audit reuses the VERIFIER launch profile when one is configured, which is the
            # point: the operator who configured a stronger checker for turn 2 wants it here too.
            **_audit_launch_options(args),
        },
        "audit": {
            "plan": item["file"],
            "diff_basis": target.basis,
            "diff_basis_detail": target.basis_detail,
        },
    }
    runner_shared.atomic_write_json(run_dir / "state.json", state)

    prompt = build_verifier_prompt(
        item,
        state,
        run_dir,
        target.plan_path,
        audit=True,
        diff_basis=target.basis_detail,
    )

    handle = None
    work_dir: str | None = None
    if getattr(args, "isolate_worktree", True):
        # THE SAME `worktree_lease` EVERY EXECUTE TURN USES, not a second isolation path. OQ-04 is
        # recorded resolved as "do NOT run it in the shared primary checkout", and isolation is
        # already the default for execute turns on both hosts, so a lane here is the consistent
        # choice rather than a novel one.
        try:
            handle = runner_shared.allocate_isolation_worktree(repo, f"audit-{id6}")
            work_dir = str(handle.path)
        except Exception as exc:
            print(
                f"audit: could not allocate an isolated worktree ({exc}); refusing rather than "
                f"running in the shared checkout, which other agents may be using. Pass "
                f"--no-isolate-worktree to override deliberately.",
                file=sys.stderr,
            )
            return 1

    prompt_path = runner_shared.write_prompt(run_dir, item, prompt, 1, suffix="audit")
    print(pal(f"Audit run: {run_id}", "cyan"))
    print(f"  plan:  {item['file']}")
    print(f"  basis: {target.basis}")
    print(
        f"  tree:  {work_dir or 'the shared primary checkout (--no-isolate-worktree)'}"
    )

    verdict_path = run_dir / "outcomes" / f"01-{target.id6}-verification.json"
    try:
        rc, _session, log_path, _argv = run_opencode(
            state,
            run_dir,
            item,
            target.plan_path,
            prompt_path,
            1,
            fresh_session=True,
            log_suffix="audit",
            label_suffix="audit",
            work_dir=work_dir,
            use_verifier_launch=True,
            telemetry_phase=runner_shared.TELEMETRY_PHASE_VALIDATE,
        )
    finally:
        # THE LANE IS NEVER TORN DOWN HERE, even on an exception, and that is deliberate:
        # `teardown_isolation_worktree` is documented as destructive and safe only on a lane holding
        # NO work, and an audit that fixed code in scope holds exactly that work. Preserving it is the
        # same choice `reclaim_lanes_on_interrupt` makes for an interrupted execute lane.
        if handle is not None:
            print(f"  lane preserved: {handle.branch} at {handle.path}")

    verdict: dict[str, Any] | None = None
    for candidate in (
        verdict_path,
        (Path(work_dir) / verdict_path.relative_to(repo))
        if work_dir and verdict_path.is_relative_to(repo)
        else None,
    ):
        if candidate is not None and candidate.is_file():
            try:
                verdict = json.loads(candidate.read_text(encoding="utf-8"))
                break
            except (OSError, json.JSONDecodeError):
                continue

    item["attempts"].append(
        {
            "attempt": 1,
            "exit_code": rc,
            "log": str(log_path),
            "verdict": (verdict or {}).get("verdict", ""),
        }
    )
    item["status"] = "audited" if verdict else "no-verdict"
    state["audit"]["verdict"] = verdict or {}
    state["audit"]["lane"] = (
        {"branch": handle.branch, "path": str(handle.path)} if handle else None
    )
    runner_shared.atomic_write_json(run_dir / "state.json", state)

    if not verdict:
        print(
            f"audit: the turn exited {rc} but wrote no verdict to {verdict_path}. The session log is "
            f"at {log_path}; nothing about the audited plan changed.",
            file=sys.stderr,
        )
        return 1

    print(pal(f"  verdict: {verdict.get('verdict', '?')}", "cyan"))
    print(f"  summary: {verdict.get('summary', '')}")
    filed = verdict.get("findings_filed") or []
    if filed:
        print(f"  findings filed: {', '.join(str(f) for f in filed)}")
    print(f"  full verdict: {verdict_path}")
    return 0


def _fresh_audit_run_dir(repo: Path) -> tuple[str, Path]:
    """A run directory that does NOT already exist, returned as ``(run_id, path)``.

    reverify-01 (`mp289j`) E-03. THIS EXISTS BECAUSE `new_run_id` ALONE IS NOT ENOUGH, which was
    measured while writing this verb's own tests rather than assumed: the id is
    `run-<UTC seconds>-<pid>`, so two invocations from ONE shell inside the SAME second produce the
    IDENTICAL id (`{new_run_id(), new_run_id()}` had length 1). For a queued run that is harmless,
    because a run is long-lived and one process owns it. For an on-demand audit it is not: the whole
    append-versus-overwrite answer in E-03 is that a second opinion cannot erase the first, and two
    verdicts sharing a directory would overwrite exactly that.

    SO THE GUARANTEE IS MADE STRUCTURAL rather than probabilistic: the base id is suffixed `-2`, `-3`
    ... until the path is free, using `mkdir` itself as the test via `exist_ok=False`, which is atomic
    against a concurrent audit rather than a check-then-create race.

    A DELIBERATELY NARROW FIX. `new_run_id` is shared by both drivers and every queued run, so changing
    ITS format here would alter run ids repository-wide for a hazard only this verb has; the collision
    in the shared helper is reported as a finding with its own backlog carrier instead.
    """

    root = runner_shared.state_root(repo)
    base = runner_shared.new_run_id()
    for suffix in range(1, 100):
        run_id = base if suffix == 1 else f"{base}-{suffix}"
        candidate = root / run_id
        try:
            candidate.mkdir(parents=True, exist_ok=False)
            return run_id, candidate
        except FileExistsError:
            continue
    raise runner_shared.DriverError(
        f"could not mint a free audit run directory under {root} after 99 attempts; something is "
        f"creating run directories faster than this verb can name them"
    )


def _audit_launch_options(args: argparse.Namespace) -> dict[str, Any]:
    """The launch identity for an audit turn, resolved from the runner-profile store.

    SEPARATE FROM `handle_audit_command` so the resolution is testable without launching anything.

    It asks for the VERIFIER launch (`resolve_launch_pair`'s second element) and falls back to the
    ordinary one, because an audit IS a verification turn: an operator who configured
    `--verify-with opus` did so precisely to have a stronger checker read finished work, and this verb
    is that same request made after the fact. When no verifier profile is configured the keys are
    absent entirely, which is the same shape a run created without one has, so `run_opencode`'s argv is
    byte-identical to an ordinary turn's.
    """

    try:
        resolved_launch, resolved_verify = resolve_launch_pair(args)
    except Exception:
        return {}
    options: dict[str, Any] = {
        "model": resolved_launch.model,
        "variant": resolved_launch.variant,
        "agent": resolved_launch.agent,
    }
    if resolved_verify is not None:
        options.update(
            {
                "verify_model": resolved_verify.model,
                "verify_variant": resolved_verify.variant,
                "verify_agent": resolved_verify.agent,
                "verify_launch_profile": launch_profile_record(resolved_verify),
            }
        )
    return options


def handle_stop_command(args: argparse.Namespace) -> int:
    """Execute the `stop` verb: resolve the run, then apply the SHARED decision (spec R14/R17).

    hostdedup Order 01 (`li44r9`) E-02/E-08: a thin wrapper over the ONE definition in `runner_shared`.
    This host supplies its OWN `resolve_run_dir` and its OWN labels; the labels matter because the stop
    record names the operator-facing driver command, and before the lift this body called
    `_detect_driver_command`, which IS the labels binding.
    """
    return runner_shared.handle_stop_command(
        args,
        labels=runner_shared.OC_HOST_LABELS,
        resolve_run_dir_fn=resolve_run_dir,
    )


def install_stop_triggers(run_dir: Path) -> dict[str, str]:
    """Install the SIGINT ladder and the SIGTERM handler for THIS run (runstop 71vjbn, spec R12/R13).

    hostdedup Order 01 (`li44r9`) E-02/E-08: a thin wrapper over the ONE definition in `runner_shared`,
    which holds the full contract for the three-step Ctrl-C ladder, the SIGTERM replacement, and why
    the handler only RECORDS and never reaps. The labels are this host's own because the stop request
    names the operator-facing driver command.
    """
    return runner_shared.install_stop_triggers(
        run_dir, labels=runner_shared.OC_HOST_LABELS
    )


class ProfileClauseError(DriverError):
    """The `as PROFILE` clause was malformed (missing, repeated, or misplaced).

    A DriverError subclass so `main`'s existing handler renders it on stderr and exits 2 without a
    run directory ever being created; runprofile-03 (`3cm15q`) E-01/E-02 require a malformed
    invocation to cost the operator nothing durable.
    """


def extract_profile_clause(argv: list[str]) -> tuple[list[str], str | None]:
    """Split a FIXED `as PROFILE` clause off the front of a start argv (E-01).

    Returns `(argv_without_the_clause, profile_or_None)`. This is the whole grammar, and it is
    DELIBERATELY POSITIONAL rather than a scan for the word `as`:

      - `as` is recognized ONLY in the one fixed position, the token immediately after an implicit
        start (`aw oc run as gem SELECTOR`) or an explicit `start` (`aw oc run start as gem SEL`).
      - The token immediately after that `as` is ALWAYS the profile name, and every later token is a
        selector or option. So a profile may be named `status` or `--help` without shadowing
        anything, which is exactly the "alias named status" failure mode the plan's findings table
        requires protection against: no configured name can ever become a command, because the
        command position is decided BEFORE any configuration is read.
      - A profile-like token WITHOUT `as` stays a selector, so existing invocations are untouched.
      - A LITERAL `as` selector is reachable via the conventional end-of-options marker,
        `aw oc run -- as` (DECISION 18-3cm15q-D2). `--` also terminates the clause scan, so nothing
        after it is ever read as grammar.

    Raises :class:`ProfileClauseError` for a missing profile (`run as`), or for a repeated or
    misplaced clause (`run as gem as gem`, `run SEL as gem`), naming the exact usage. A MISPLACED
    clause must fail rather than be silently treated as a selector: `aw oc run 3cm15q as gem` looks
    like it requests a profile, and running it under the host default instead would launch the wrong
    model with no diagnostic at all.
    """

    usage = (
        "usage: aw oc run as <profile> [SELECTOR ...]   (the 'as' clause comes FIRST, "
        "immediately after 'run'/'start'; use 'aw oc run -- as' for a literal 'as' selector)"
    )

    # Only an explicit leading `start` is stepped over; `main` has not yet prepended one.
    head: list[str] = []
    rest = list(argv)
    if rest and rest[0] == "start":
        head.append(rest.pop(0))

    profile: str | None = None
    if rest and rest[0] == "as":
        if len(rest) < 2:
            raise ProfileClauseError(f"'as' requires a profile name. {usage}")
        candidate = rest[1]
        if candidate == "--":
            raise ProfileClauseError(f"'as' requires a profile name. {usage}")
        profile = candidate
        rest = rest[2:]

    # A SECOND or MISPLACED `as` anywhere in the remaining tokens is an error, not a selector. The
    # scan stops at `--`, which makes everything after it literal.
    for token in rest:
        if token == "--":
            break
        if token == "as":
            detail = (
                "the 'as' clause may appear only once"
                if profile is not None
                else "the 'as' clause must come FIRST, before any selector"
            )
            raise ProfileClauseError(f"misplaced 'as': {detail}. {usage}")

    return head + rest, profile


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # THE IMPLICIT-START SHIM. Any first token NOT in this set is treated as a selector and gets
    # `start` prepended. runstop 71vjbn (E-03): `"stop"` MUST be listed here. This shim lives in
    # `main()` and NOT in `build_parser()`, so adding the `stop` subparser alone does not cover it -
    # `stop <run-id> --now` would be rewritten to `start stop <run-id> --now`, i.e. it would LAUNCH a
    # run with the literal selector `stop`. That is a silent misfire in the exact opposite direction
    # of the operator's intent, so a test asserts the bare form is not rewritten (in both drivers).
    # KEEP THIS AS AN INLINE SET LITERAL. `test_runner_stop_triggers` asserts structurally, by regexing
    # `subcommands = \{(.*?)\}` in BOTH drivers' sources, that `"stop"` is listed here; hoisting the set
    # into a module constant makes that guard silently unmatchable (measured: it fails with
    # "unexpectedly None"). The guard is worth more than the deduplication, because it is what stops
    # `stop <run-id>` from being rewritten into `start stop <run-id>` in one driver only.
    #
    # streamfmt (mm6wuz) E-05 / OQ-02 (resolved): `"-v"` and `"--version"` USED TO BE LISTED HERE and
    # were REMOVED. `-v` now means `--verbose` on `start` and `resume`, and while it sat in this set a
    # LEADING `-v` was treated as a subcommand and never prefixed with `start`, so `aw oc run -v SEL`
    # failed with `invalid choice: 'SEL'` while `aw oc run -vv SEL` (not in the set) failed
    # differently with `unrecognized arguments: -vv`. The reservation also guarded a `--version` flag
    # NEITHER driver registers (measured: `parse_args(["--version"])` exits 2 with
    # `unrecognized arguments`), so it protected nothing. If a real `--version` is ever added, add
    # BOTH tokens back to BOTH drivers together and give `--verbose` the long spelling only; the two
    # sets must stay IDENTICAL because the structural test regexes both source files.
    # integpath-04 (`rl67b0`) E-02: `"integrate"` MUST be listed here for the SAME measured reason
    # `stop` must: an unregistered first token is rewritten into `start <token>`, so
    # `integrate <id6>` would LAUNCH A RUN with `integrate` as a selector, which is the opposite of
    # the operator's intent and is silent. A test asserts the bare form is not rewritten, in both
    # drivers, and a third assertion pins this set against the agy copy AND against the inline copy in
    # `tests/test_runner_stop_triggers.py`; all three must change together.
    # reverify-01 (`mp289j`) E-05: `"audit"` MUST be listed here for the SAME measured reason `stop`
    # and `integrate` must. An unregistered first token is rewritten into `start <token>`, so
    # `audit <id6>` would LAUNCH A RUN with `audit` as a selector - which for this verb is worse than
    # for the other two, because an operator asking for a cheap second opinion on FINISHED work would
    # instead pay for a full execution attempt against an already-executed plan.
    subcommands = {
        "start",
        "resume",
        "status",
        "report",
        "stop",
        "integrate",
        "audit",
        "-h",
        "--help",
    }

    # runprofile-03 (`3cm15q`) E-01: strip the FIXED `as PROFILE` clause BEFORE the shim and before
    # argparse, because `as gem` is grammar rather than selectors and `start`'s `nargs="+"` would
    # otherwise swallow both tokens as selector names. Ordered FIRST so the clause is recognized in
    # the implicit form (`run as gem SEL`) as well as the explicit one (`run start as gem SEL`).
    # `resume`/`status`/`report`/`stop` never carry the clause: `extract_profile_clause` only
    # inspects the first token, which for those is the subcommand itself, so their routing is
    # untouched (asserted by test).
    # The clause is parsed OUTSIDE the big `try` below (that block needs `run_dir`, which does not
    # exist yet), so its refusal is rendered here: stderr + exit 2, the same contract every other
    # `DriverError` gets, rather than an uncaught traceback.
    profile_request: str | None = None
    if argv and (argv[0] not in subcommands or argv[0] == "start"):
        try:
            argv, profile_request = extract_profile_clause(argv)
        except ProfileClauseError as exc:
            print(f"runipd: {exc}", file=sys.stderr)
            return 2

    if argv and argv[0] not in subcommands:
        argv = ["start"] + argv
    elif not argv and profile_request is not None:
        # `run as gem` with no selector: argparse must see `start` so it reports the missing
        # selector in its own words rather than printing top-level help.
        argv = ["start"]

    parser = build_parser()
    args = parser.parse_args(argv)

    # runprofile-03 (`3cm15q`) E-01: carry the extracted clause on the namespace, so every downstream
    # consumer reads it from ONE place (`args.profile`) exactly as it reads `--model`/`--variant`.
    # Set unconditionally, including to None, so `getattr(args, "profile", None)` is never a silent
    # AttributeError-shaped default on the resume/status/report namespaces.
    # Only OVERWRITE when this invocation actually carried a clause. A namespace that already supplies
    # a profile (a future parser-declared `--profile`, or a caller building its own namespace) must not
    # be silently cleared to None, which would make the refusal below unreachable.
    if profile_request is not None or not getattr(args, "profile", None):
        setattr(args, "profile", profile_request)

    # E-04: a resumed run uses the identity FROZEN at creation, so naming a profile on resume cannot be
    # honored. Refuse LOUDLY rather than accept-and-ignore: the operator who typed `as gem` believes
    # the resumed turns will use `gem`, and silently continuing under the original model is exactly the
    # "alias edited before resume silently changes models" failure this plan exists to prevent. Not
    # reachable through the shipped shim (the clause is scanned for `start` only), so this is a
    # belt-and-braces guard that keeps a later shim change from creating that silent misfire.
    named_profile = getattr(args, "profile", None)
    if named_profile is not None and getattr(args, "command", None) != "start":
        print(
            f"runipd: a profile ('as {named_profile}') cannot be named on "
            f"'{args.command}': the launch identity is frozen when the run is created. "
            f"Resume uses the original profile; start a NEW run to launch with a different one.",
            file=sys.stderr,
        )
        return 2

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
            # runstop 71vjbn (E-03/E-04): out-of-band, and deliberately BEFORE any run-lock or state
            # mutation. It never starts a run and never creates the run directory.
            return handle_stop_command(args)
        if args.command == "integrate":
            # integpath-04 (`rl67b0`) E-02: out-of-band like `stop`, and likewise before any run-lock
            # or state mutation. It creates no run directory and spends no agent turn; it refuses a
            # lane a LIVE process owns precisely because it holds no run lock.
            return handle_integrate_command(args)
        if args.command == "audit":
            # reverify-01 (`mp289j`) E-05: out-of-band like `stop` and `integrate`, and dispatched here
            # BEFORE any queue is built or run lock taken. Unlike those two it DOES spend one agent
            # turn (that is the product), and unlike `start` it builds no queue, takes no lock, and
            # performs no lifecycle transition on the plan it audits.
            return handle_audit_command(args)
        if args.command == "start":
            run_dir = initialize_run(args)
            print(f"Run ID: {run_dir.name}")
            print(f"State directory: {run_dir}")
            if args.prepare_only:
                print_status(run_dir)
                # runprofile-03 (`3cm15q`) E-03: `--prepare-only` exists so an operator can inspect
                # what a run WILL do before it launches, so the model/variant it will launch with
                # belongs here more than anywhere else.
                print_launch_identity(run_dir)
                return 0
            # runstop 71vjbn: armed only now, because a handler needs the run dir to record into.
            install_stop_triggers(run_dir)
            with locked_run(run_dir):
                return run_queue(run_dir, retry_incomplete=False)
        run_dir = resolve_run_dir(args.repo, args.run_id)
        output_mode = getattr(args, "output_mode", None)
        # streamfmt (mm6wuz) E-05: `None` on `resume` when the flag was omitted (see
        # `_add_output_mode_flags`), so an omitted `-v` does not clobber the frozen tier.
        verbosity = getattr(args, "verbosity", None)
        if args.command == "status":
            if getattr(args, "json", False):
                state = load_state(run_dir)
                print(json.dumps(state, indent=2, sort_keys=True))
                # bkclose (zhr6mc) E-07: NO pointer line here. `--json` output must stay parseable,
                # so a trailing human sentence is suppressed for machine-readable modes; the same
                # holds for `--agent`, which this driver does not expose (it forwards to a child).
                return 0
            print_status(run_dir)
            print_launch_identity(run_dir)
            print(render_runs_pointer(load_state(run_dir)))
            return 0
        if args.command == "report":
            state = load_state(run_dir)
            write_report(run_dir, state)
            print(run_dir / "execution-report.md")
            return 0
        if args.command == "resume":
            # runflags-01 (`uyeko5`) E-06: REFUSE a flag spec 2.1 freezes, before any state is loaded
            # or written. Scoped to `--retry-budget`, the one flag spec `:131` explicitly freezes ("the
            # frozen value cannot change on resume"). The blanket `:129` reading is NOT implemented,
            # because the shipped `--full-auto` on resume OVERWRITES the frozen option rather than
            # refusing, so the spec's two sentences disagree and converting a shipped flag's behavior
            # is out of this plan's fence. The divergence is recorded, not papered over.
            runner_shared.refuse_frozen_flags_on_resume(args)
            # runprofile-06 (`kgpptv`) E-02: REFUSE `--verify-with` on resume, before any state is
            # loaded or written, for exactly the reason `as <profile>` is refused: the flag names a
            # PROFILE, honoring it would require re-reading `runner-profiles.json`, and `3cm15q`
            # E-04 makes a resume use the identity frozen at creation. Refusing LOUDLY rather than
            # accepting-and-ignoring, because an operator who typed `--verify-with opus` believes
            # the resumed verifier turns will use `opus`, and silently continuing under the
            # original one is the "silently verified with the wrong model" failure this plan exists
            # to prevent.
            if getattr(args, "verify_with", None) is not None:
                raise DriverError(
                    f"--verify-with {args.verify_with!r} cannot be changed on resume: the "
                    "verifier launch is frozen when the run is created, because honoring a "
                    "profile name here would mean re-reading runner-profiles.json. Resume "
                    "without it to use the frozen value, or start a NEW run."
                )
            # Apply the policy flags the operator actually PASSED; leave the omitted ones frozen. This
            # SUBSUMES the hand-written `--full-auto` block that was here: the shared helper applies
            # the same `None`-means-absent rule to all eight, so `--full-auto`'s shipped resume
            # behavior (it OVERWRITES the frozen option, it does not refuse) is preserved EXACTLY.
            state = load_state(run_dir)
            if runner_shared.apply_run_policy_flags_on_resume(state, args):
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
            # runprofile-03 (`3cm15q`) E-04: an EXPLICIT `--variant` on resume still overrides, which
            # is the shipped behavior of plan `429f30` and is preserved deliberately (DECISION
            # 18-3cm15q-D1). What must NEVER happen is resume RE-RESOLVING the profile: nothing here
            # calls `runner_profiles.load()`, so editing, deleting, or repointing the profile after run
            # creation cannot alter this run. The frozen `options.launch_profile` snapshot is left
            # untouched on purpose, so it keeps recording what CREATED the run; an operator override
            # is visible as a divergence between it and the live `options.variant`.
            if getattr(args, "variant", None) is not None:
                state = load_state(run_dir)
                state.setdefault("options", {})["variant"] = args.variant
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
                    verbosity=verbosity,
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
                            driver_label="opencode",
                        )
                    )
                    # specvis st5klo E-03: WIRED on the interrupt/SIGTERM path and LABELLED
                    # possibly-incomplete (maintainer resolution of OQ-01, 2026-09-08). An aborted run
                    # is exactly when an operator most needs to know a spec was rewritten, so
                    # suppressing this would hide the interesting case; but items that never reached
                    # finalize have no reconciliation, so it must not read as authoritative.
                    report_run_spec_edits(state, partial=True)
                    print(render_continuation_hint(state, run_dir))
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
        if "just-terminate-no-cleanup" in msg:
            print(
                "Terminated without clean up; worktree and lanes left in place.",
                file=sys.stderr,
            )
        else:
            print(
                f"{'Terminated by SIGTERM' if is_sigterm else 'Interrupted'}; durable run state was preserved.",
                file=sys.stderr,
            )
        # stopdisc (`wqq8ua`) E-03: this is the moment an operator learns what just happened, and it
        # said nothing about the gentler option that existed. Spec R16's report covers a LIVE request
        # (`render_request_accepted`); the message printed on the way OUT was the empty surface.
        #
        # AFTER THE BRANCH, NOT INSIDE EITHER, for two reasons. It is true on BOTH exits, and keeping
        # it out of the branch bodies leaves each existing sentence byte-identical and contiguous,
        # which is what `tests/test_interrupt_menu.py::RunnerMainOutputOnInterruptTests` asserts.
        #
        # PHRASED AS WHAT IS AVAILABLE NEXT TIME, because this handler cannot know which R12 path or
        # which ladder rung produced the exit, so naming a level would risk describing the wrong one.
        # The out-of-band verb is true either way and needs no terminal at all.
        #
        # NOT A PROMPT, AND MUST NOT BECOME ONE: Ctrl-C is taken by an operator who wants OUT, and
        # blocking it on a question risks the unbounded wait `runner_stop.interrupt_menu_is_safe`
        # documents. One sentence, then the pre-existing exit code, unchanged.
        print(
            runner_stop.stop_interrupt_hint(_detect_driver_command()),
            file=sys.stderr,
        )
        return 143 if is_sigterm else 130
    except EmptyStatusSelection:
        # revsweep 76gsmv E-04, spec 25kzda 2.4a property 3: an empty STATUS sweep is the HEALTHY
        # state, so it reports plainly on stdout and exits 0. Ordered BEFORE the generic
        # `except DriverError` because it is a subclass; a misspelled id6 raises the plain
        # `DriverError` below and still exits 2. Nothing was created: this raises out of
        # `expand_selectors`, which runs before the run directory is made, so there is no summary
        # table to render and no state to reconcile.
        print("Nothing awaiting review; no run started.")
        return 0
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
                            driver_label="opencode",
                        )
                    )
                    # specvis st5klo E-03: the DriverError path, likewise wired and labelled (OQ-01).
                    report_run_spec_edits(state, partial=True)
                    print(render_continuation_hint(state, run_dir))
            except Exception:
                pass
        print(f"runipd: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"runipd: unexpected failure: {exc}", file=sys.stderr)
        raise


if __name__ == "__main__":
    raise SystemExit(main())
