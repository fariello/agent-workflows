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
from typing import Any, Callable, Iterable, Optional

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

# runnoop Order 02 (`m85gxh`): the pure PER-ARTIFACT DISPOSITION renderer, imported from its OWNING
# module and NOT from `oc_runipd`. This module already imports 48 names from that driver and zero flow
# back, so a shared renderer must not become the 49th: the symbol is owned by a third module both
# hosts read, and `tests/test_runner_refork_guard.py` pins that both see the SAME object. The
# `as <same-name>` form matches the idiom used for every other re-export here and keeps a linter from
# stripping the binding.
from agent_workflows.run_selection_policy import (
    render_queue_dispositions as render_queue_dispositions,
)

# runnoop Order 03 (`bsc457`) E-03: the END-OF-RUN DISPOSITION SUMMARY. Imported from the OWNING module
# directly, never from `oc_runipd`, on exactly the terms the note above states: the oc-to-agy import
# count must not deepen for a symbol a third module owns, and the refork guard pins both hosts to the
# SAME object.
from agent_workflows.run_selection_policy import (
    render_disposition_summary as render_disposition_summary,
)

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
#
# `_read_id`'s `# noqa: F401` IS LOAD-BEARING (rununify 06 `sy7uwh`); see the fuller note in
# `oc_runipd`. Once `parse_plan_file` moved to `runner_shared` this module stopped calling `_read_id`,
# so `ruff --fix` removed the import as unused and broke the re-export
# `tests/test_runner_refork_guard.py` requires of BOTH runners.
from agent_workflows.selectors import read_front_matter_id as _read_id  # noqa: F401 - a DELIBERATE re-export; tests/test_runner_refork_guard.py requires it
from agent_workflows.selectors import read_front_matter_status as _read_status

from agent_workflows.render_stream import (
    Statusline,
    render_run_summary_table,
    install_exit_signal_handler,
    statusline_action_for_item,
    # orchprobe (r2i1b1) E-01/E-02: the ONE refusal record (reason AND remedy), imported from
    # `render_stream` and NEVER from `oc_runipd`, so this shared symbol does not deepen the
    # oc-to-agy coupling that backlog `cnwy8g` tracks. Same object in both hosts, asserted by
    # object identity in `tests/test_refusal_surfacing.py`.
    REFUSAL_KEY as REFUSAL_KEY,
    Refusal as Refusal,
    record_integration_refusal as record_integration_refusal,
    record_refusal as record_refusal,
    refusal_of_item as refusal_of_item,
    execution_index as execution_index,
    # `progdenom`: shared with the oc host and the summary bar, so all three agree.
    dispatchable_work_total as dispatchable_work_total,
    Palette as Palette,
    _strip_ansi as _strip_ansi,
    _one_line as _one_line,
    _ANSI_RESET as _ANSI_RESET,
    _ANSI_CODES as _ANSI_CODES,
    _ANSI_STRIP_RE as _ANSI_STRIP_RE,
    _STATUS_COLOR as _STATUS_COLOR,
    # streamfmt (mm6wuz) E-06: the SHARED aligned prefix grammar and status glyphs, so the two hosts
    # put their payloads in the same column and a prefix added to the shared table reaches both.
    # Imported, never re-declared, for the same reason `Palette` is (see the note above).
    StreamTracker as StreamTracker,
    format_event_prefix as format_event_prefix,
    _relativize_path as _relativize_path,
    _status_glyph_char as _status_glyph_char,
    strip_system_protocol_prefix as strip_system_protocol_prefix,
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

# lanectn `cqx5v7` (spec `7ckptx` R2.6): the host-neutral lane containment rules, shared with the
# OpenCode driver. This driver CALLS them and holds no second copy of the path projection, the
# collection, or the idempotency (CID-2). Do NOT import them from `oc_runipd`: that would make one
# host the de-facto shared library, which R2.6 forbids.
from agent_workflows import lane_containment

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
# orchretire-03 (`pgq326`) E-04/E-07 EXTENDS this seam with the ACTION DECISION and the ORCHESTRATOR
# DISPATCH OUTCOME. This module previously defined its OWN `determine_action` and had NO `action_for`
# at all, so measured at HEAD `844d195c`: `agy.determine_action('approved')` returned `'execute'` where
# `oc.action_for('orchestrator','approved')` returned `'orchestrate'`, and `aw agy run` would have
# AGENT-EXECUTED an approved orchestrator. Both hosts now bind these SAME objects (spec `77tr3o` R-10);
# `tests/test_orchestrator_retirement.py` asserts it by object identity, so a re-forked copy fails.
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

# runverdict (`1bfppy`) E-01/E-02: the ONE fail-closed VERIFIER VERDICT MAPPING, imported from
# `runner_shared` and NOT from `oc_runipd`, for the same layering reason the note below gives. THIS HOST
# IS THE MORE EXPOSED ONE: its verifier is gated on `not no_verify` (default ON) and it passes
# `validate=verifier_expected` into `integration_is_earned`, where oc gates on `--validate` (default
# OFF). So the verdict mapping decides integration on THIS host's shipped default.
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

# depblock 01 (`akzy45`) E-04: the DRAIN-TIME classification, imported from `runner_shared` and NOT from
# `oc_runipd`. This host already imports 53 names from that driver (AST-measured), and adding to that
# pile would deepen the layering defect backlog `cnwy8g` owns; `7nkcgp`'s F-11 caught a proposed shared
# predicate that would have created the first runner-to-runner import for exactly this reason. Bound by
# name because the cross-driver symmetry guard requires each driver to CARRY the attribute.
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
# `tests/test_runner_refork_guard.py`'s `REFORK_TABLE`. A SECOND COPY IN THIS FILE IS FORBIDDEN: the
# whole point is that a later fix to the bar reaches BOTH drivers, and a copy here is precisely how
# agy carried a broken `dependency_status_detailed` for months.
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

# integpath-02 (`6sb3yu`): a PURE move, bound by re-export rather than wrapped (its two neighbours
# need this host's `run_checked`/`host_label` and so keep wrappers). The `as <same-name>` form marks
# it as a deliberate re-export so `ruff` does not "clean up" a symbol this module never calls itself.
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

# rununify 03 (`i3d6ml`) E-02: the two `DriverError` subclasses, which were defined in BOTH runners with
# identical (empty) bodies and differently-worded docstrings. There is one of each now, so a stall or an
# empty status selection raised through EITHER driver's code path is caught by `except StallTimeout` /
# `except EmptyStatusSelection` in either driver rather than only by the broader `except DriverError`.
from agent_workflows.runner_shared import (
    EmptyStatusSelection as EmptyStatusSelection,
)
from agent_workflows.runner_shared import (
    StallTimeout as StallTimeout,
)

# rununify 03 (`i3d6ml`) E-02: host-neutral helpers this module used to define itself.
# `_findings_block_reason` is bound HERE ON PURPOSE and not merely reachable: the cross-driver
# API-symmetry contract asserted by `tests/test_review_findings_cascade.py::SharedPredicateTests`
# requires this module to CARRY the attribute, which the aliased import satisfies. That test's second
# half, which read this module's SOURCE for the name of the shared predicate
# (`review_findings.subject_gating_blocks`), was RE-BASED onto `runner_shared` in the same change,
# because that is where the wrapper now lives; it was not weakened, and it still refuses a runner that
# reimplements the severity comparison.
from agent_workflows.runner_shared import (
    _findings_block_reason as _findings_block_reason,
)
from agent_workflows.runner_shared import (
    make_integration_validation_runner as make_integration_validation_runner,
)

# rununify 03 (`i3d6ml`) E-02/E-03: `build_review_prompt` plus the four symbols whose OBSERVABLE output
# differed between the hosts. TWO OF THESE CHANGE THIS DRIVER'S FILENAMES, which is disclosed at each
# shared definition rather than buried here: `attempt_log_path` now emits oc's
# `-attempt-<n>-verify.jsonl` shape, which REPAIRS this driver's verifier logs being misclassified as
# execute logs by `run_analytics_statistics.verifier_phase_of_log`; and `write_prompt` now treats
# `suffix` as REPLACING the action prefix rather than adding to it, so a suffixed prompt is
# `<NN>-<id6>-verify-attempt-<n>.md` instead of `<NN>-<id6>-exec-verify-attempt-<n>.md`.
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
# behavior, now defined ONCE in `runner_shared`. `extract_session_id` is the UNION and KEEPS everything
# this host read (`conversation_id` plus the nested `result`/`init` lookup), because that is this host's
# own wire format; oc's reader could not see it, so "oc wins" would have disabled session resume here
# outright. `_SESSION_ID_KEYS` comes with it because it was defined TWICE with different contents.
# `begin_baseline_env` is the baseline declaration this host previously did not send at all.
from agent_workflows.runner_shared import (
    _SESSION_ID_KEYS as _SESSION_ID_KEYS,
)
from agent_workflows.runner_shared import (
    begin_baseline_env as begin_baseline_env,
)
from agent_workflows.runner_shared import (
    extract_session_id as extract_session_id,
)
from agent_workflows.runner_shared import (
    enforce_no_active_runner_conflict as enforce_no_active_runner_conflict,
)
from agent_workflows.runner_shared import (
    format_slated_artifacts_table as format_slated_artifacts_table,
)

# lanetruth Order 01 (af7i6p) E-02: import the SINGLE shared definition of the nested-`aw` pin
# rather than duplicating it here. Both drivers must stay symmetric, and a second copy is exactly
# how the previous inert half-pin came to differ from what it looked like it did. `oc_runipd` does
# not import this module, so there is no import cycle.
from agent_workflows.oc_runipd import (
    ToolIdentityError,
    assert_child_tool_identity as assert_child_tool_identity,  # noqa: F401
    pinned_child_env,
    pinned_module_argv,
)

# The durable stop-request record and the cooperative-checkpoint poll (spec `c4gd2h` R7-R9/R11)
# live in the shared ``runner_stop`` module so both drivers consult ONE mechanism.
from agent_workflows import runner_shared, runner_stop

# rununify 06 (`sy7uwh`) E-02/E-03: the ONE plan record, its ONE reader, and the readers/constants that
# reader closes over. This module used to define its own `PlanRecord` (identical to oc's except that it
# LACKED `kind`), its own `parse_plan_file`, its own `build_dynamic_manifest` and its own
# `_PLAN_FILENAME_RE`, and it imported the three readers FROM `oc_runipd`; there is now ONE of each and
# the three readers reach this host through `runner_shared`, which drops the oc-to-agy import coupling
# backlog `cnwy8g` tracks from 56 to 53. `plan_kind_from_file`/`resolve_manifest_kind` are this host's
# former private `_plan_kind` legacy-manifest fallback, now shared so oc has it too (`sy7uwh` OQ-03).
# The full rationale sits at each removed definition's old site further down this file.
from agent_workflows.runner_shared import (
    PlanRecord as PlanRecord,
    _PLAN_FILENAME_RE as _PLAN_FILENAME_RE,
    _read_from_backlog as _read_from_backlog,
    _read_item_dependencies as _read_item_dependencies,
    _read_kind as _read_kind,
    build_dynamic_manifest as build_dynamic_manifest,
    parse_plan_file as parse_plan_file,
    plan_kind_from_file as plan_kind_from_file,
    resolve_manifest_kind as resolve_manifest_kind,
)

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
    # integearn-05 (`9lyg5h`) E-03/E-06: the three names the shared concurrent pre-work BASELINE is
    # injected with. They are re-exported HERE, under the same `as <same-name>` discipline as the
    # suite check above, because `execute_item_core` resolves them off `driver_module` and a name
    # missing from one host would silently give that host NO baseline while the other had one - which
    # is exactly the single-host divergence this whole re-export block exists to prevent, and it
    # would make an audit's answer depend on which runner executed the plan.
    #
    # `extract_suite_failures` IS `daexj1`/`h5pyqa`'s FUNCTION AND IS NOT RE-IMPLEMENTED. Sharing the
    # one extractor is what makes the pre-work and post-work id sets comparable at all.
    SUITE_CHECK_ARGV as SUITE_CHECK_ARGV,
    extract_suite_failures as extract_suite_failures,
    parse_suite_summary as parse_suite_summary,
    BacklogCloseVerdict as BacklogCloseVerdict,
    CARRIER_KIND_IPD as CARRIER_KIND_IPD,
    CARRIER_KIND_OTHER as CARRIER_KIND_OTHER,
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
    cascade_dependency_blocked as cascade_dependency_blocked,
    dependency_depth as dependency_depth,
    dependency_reasons as dependency_reasons,
    dependency_status as dependency_status,
    # depreview 03ie04 E-03: `dependency_status_detailed` is RE-EXPORTED here, not defined. This
    # module used to carry its own copy, and that copy was the reason a dependency fix could reach
    # only ONE of this driver's two paths: the dispatch path called the re-exported
    # `dependency_status` (whose body resolves `dependency_status_detailed` in OC's globals) while
    # the DRAIN path called the local copy. Measured before the deletion:
    # `agy.dependency_status_detailed is oc.dependency_status_detailed` -> False. The copy was also
    # BROKEN in three ways that the shared implementation is not: it never called `edge_satisfied`;
    # it never called `parse_dependency_token`, so it used the raw token as an id6 and reported
    # "no plan resolves to this id6 in the repo" for a perfectly valid `executed:<id6>`; and it had
    # no `orchestrate` clause, so an orchestrator item bypassed `decide_orchestrator_dispatch` on
    # that path. `tests/test_runner_item_dependencies.py`'s `_SHARED_NAMES` now pins this name, so
    # the copy cannot come back silently.
    dependency_status_detailed as dependency_status_detailed,
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

# specvis st5klo (E-01/E-02/E-03): the declared-spec-edit visibility surfaces, BOUND rather than
# copied, exactly as `announce_run_order` above is. This driver already reached the START announcement
# through that shared object, so E-01's fix arrived here with NO edit to this module's call sites; what
# is added here is the END-OF-RUN report, whose call sites ARE per-driver (three summary sites each) and
# so must be wired in both. `report_run_spec_edits` and its helpers have ONE definition in `oc_runipd`;
# a second copy here is the specific failure the module docstring above records for `Heartbeat`.
from agent_workflows.oc_runipd import (
    SPEC_NOT_FINALIZED as SPEC_NOT_FINALIZED,
    SPEC_RECONCILED as SPEC_RECONCILED,
    SPEC_RECONCILE_REFUSED as SPEC_RECONCILE_REFUSED,
    queue_plan_path as queue_plan_path,
    queue_with_plan_paths as queue_with_plan_paths,
    record_item_spec_edits as record_item_spec_edits,
    report_run_spec_edits as report_run_spec_edits,
    spec_edit_record as spec_edit_record,
    spec_edit_summary as spec_edit_summary,
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

# revgate Order 03 (7nkcgp) E-08. The EXACT recovery command for a `dependency-blocked` item, stated
# host-appropriately for this driver. Recovery is NOT automatic: re-queueing happens ONLY under the
# `if retry_incomplete:` branch of `run_queue`, which is False for a plain `start` and comes from the
# explicit `--retry-incomplete` flag on `resume`, so a bare `resume` leaves the item blocked.
#
# NARROWED BY depblock 01 (`akzy45`) E-01/E-02, symmetrically with `oc_runipd`. This note used to record
# that with nothing satisfiable the loop blocked EVERY queued item and BROKE out of the run. THE
# ALL-OR-NOTHING PART IS GONE: the drain arm now classifies each remaining item through the shared
# `runner_shared.classify_drain_block` and writes this terminal label only on a PERMANENTLY blocked one;
# an item whose every unmet prerequisite is still NON-TERMINAL is left `queued` and reported. The loop
# still BREAKS, since nothing inside a run re-queues such a prerequisite. See `oc_runipd`'s counterpart
# comment for the three write sites and their classifications; the predicate is shared, so this host
# cannot drift from it.
DEPENDENCY_BLOCK_RECOVERY_HINT = (
    "resolve the named cause, then re-queue with "
    "`aw agy runipd resume --repo <repo> --retry-incomplete <run-id>`; "
    "a bare `resume` does NOT re-queue a dependency-blocked item"
)

# Frontmatter and filename extraction regexes
_ID_RE = re.compile(r"(?m)^-\s*Id:\s*([0-9a-z]{6})\s*$")
_STATUS_RE = re.compile(r"(?m)^-\s*Status:\s*(\S+)\s*$")
# `_PLAN_FILENAME_RE` is IMPORTED from `runner_shared` (rununify 06 `sy7uwh` E-03), not defined here.
# It was BYTE-IDENTICAL to oc's copy and is closed over only by `parse_plan_file`, which moved to the
# shared module, so it moved with it rather than being injected - the same rule `_SET_RE`/`_ORDER_RE`
# already follow. A duplicate CONSTANT left behind would reproduce the defect one layer down.
#
# NOTE (lanetruth-03 / 8guhs0 E-01): there is deliberately NO dependency regex here. See the
# identical note in `oc_runipd`. The canonical field NAME comes from
# `ipd_schema.META_ITEM_DEPENDENCIES` and its GRAMMAR from `ipd_schema.parse_item_dependencies`; the
# dependency API objects below are IMPORTED (never re-declared), so the two drivers cannot drift apart
# again. Re-adding a dependency regex here is a regression guarded by
# tests/test_runner_item_dependencies.py.

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


#: streamfmt (mm6wuz) E-06: agy's `ACTIVE`/`DONE`/`ERROR` step states mapped onto the status
#: vocabulary `render_stream._status_glyph_char` already understands, so ONE glyph table serves both
#: hosts. `FAILED` is included because `render_agy_event` has always accepted it beside `ERROR`.
_AGY_STATE_TO_STATUS: dict[str, str] = {
    "ACTIVE": "running",
    "DONE": "completed",
    "ERROR": "error",
    "FAILED": "error",
}

#: agy tool name (and, as a fallback, its PARAMETER NAMES) -> shared prefix kind.
#:
#: NAME-BASED AND THEREFORE A HEURISTIC, stated plainly because it cannot be measured: there is not
#: one agy event in this repository's session corpus (measured: zero `"event":"step_update"` lines
#: across all 380 logs; every log is OpenCode), so unlike the oc mapping this table is derived from
#: the tool names the driver's own prompt text and parameter handling reference, not from observed
#: traffic. A tool it does not recognize falls back to its parameter shape and then to its own name
#: as the label, so an unmapped tool still renders in grammar and in column.
_AGY_TOOL_PREFIX_KIND: dict[str, str] = {
    "run_command": "bash",
    "write_to_file": "write",
    "replace_file_content": "edit",
    "edit_file": "edit",
    "view_file": "read",
    "read_file": "read",
    "view_code_item": "read",
    "list_dir": "find",
    "grep_search": "find",
    "codebase_search": "find",
    "find_by_name": "find",
    "glob_file_search": "find",
}


def agy_prefix_kind(tool_name: str, params: dict[str, Any] | None = None) -> str:
    """Map an agy tool onto a shared prefix kind (E-06).

    Falls back to the PARAMETER SHAPE when the name is unknown (`CommandLine` implies a command,
    `Query`/`Pattern` imply a search), and finally to the tool's own name, which
    `format_event_prefix` renders as `• <name>:` in the same column.
    """
    kind = _AGY_TOOL_PREFIX_KIND.get(tool_name)
    if kind:
        return kind
    params = params or {}
    if "CommandLine" in params or "command" in params or "cmd" in params:
        return "bash"
    if "Query" in params or "Pattern" in params:
        return "find"
    return "tool"


def render_agy_event(
    raw_line: str,
    pal: Palette,
    *,
    verbosity: int = 0,
    use_unicode: bool = True,
    repo_root: str | Path | None = None,
    tracker: StreamTracker | None = None,
) -> str | None:
    """Translate one raw JSONL event from `agy --output-format stream-json` into a
    concise, colored terminal line.

    streamfmt (mm6wuz) E-06. Tool lines now use the SHARED aligned prefix grammar
    (`render_stream.format_event_prefix`), so `aw agy run` and `aw oc run` put their payloads in the
    same column and a prefix added to the shared table reaches both hosts.

    WHAT IS NOT REACHABLE HERE, stated rather than claimed away. The agy schema is NOT the OpenCode
    schema: its fields are `event`/`step_update.state`/`step_update.tool_info.parameters` with
    `ACTIVE`/`DONE`/`ERROR` states and parameter names `CommandLine`/`Query`/`AbsolutePath`/
    `TargetFile`/`Pattern`. There is NO `filediff` equivalent and no additions/deletions anywhere, so
    an agy edit line CANNOT carry `(+A, -D)` and does not pretend to; it carries the repo-relative
    path instead of the bare basename it used to show. There is likewise no `todowrite` event, so no
    todo transition is computed. `tracker` accumulates tokens and cost from `step_update.usage`
    events and notes file modifications from `write_to_file` and `replace_file_content`.
    `duration_seconds` IS agy-only and is preserved.

    The new parameters are KEYWORD-ONLY WITH DEFAULTS because `tools/ipdrunner/runagy.py` re-exports
    every module attribute, so an existing two-argument `render_agy_event(line, pal)` call through
    that shim must keep working unchanged.
    """
    line = raw_line.rstrip("\n")
    if not line.strip():
        return None
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        if not strip_system_protocol_prefix(line):
            return None
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

        usage = step.get("usage") or event.get("usage")
        if tracker is not None and isinstance(usage, dict) and state == "DONE":
            inp = int(
                usage.get("input_tokens")
                or usage.get("prompt_tokens")
                or usage.get("input")
                or 0
            )
            out = int(
                usage.get("output_tokens")
                or usage.get("completion_tokens")
                or usage.get("output")
                or 0
            )
            cache_raw = (
                usage.get("cache_read_tokens")
                if "cache_read_tokens" in usage
                else usage.get("cache") or 0
            )
            if isinstance(cache_raw, dict):
                cache_val = int(cache_raw.get("read") or 0) + int(
                    cache_raw.get("write") or 0
                )
            elif isinstance(cache_raw, (int, float)):
                cache_val = int(cache_raw)
            else:
                cache_val = 0
            cost = float(
                step.get("cost") or event.get("cost") or usage.get("cost") or 0.0
            )
            tracker.update(inp=inp, out=out, cache=cache_val, cost=cost)

        if step_type == "tool":
            # Active tool events are suppressed to prevent double output in live streams;
            # the line is rendered once when the tool reaches a terminal state (DONE/ERROR/FAILED).
            if state not in ("DONE", "ERROR", "FAILED"):
                return None
            tool_info = step.get("tool_info") or {}
            tool_name = tool_info.get("name") or step.get("tool_name") or "tool"
            params = tool_info.get("parameters") or {}
            kind = agy_prefix_kind(str(tool_name), params)
            if tracker is not None and state == "DONE":
                if tool_name in (
                    "write_to_file",
                    "replace_file_content",
                    "multi_replace_file_content",
                ):
                    p = params.get("TargetFile") or params.get("AbsolutePath")
                    if p:
                        tracker.note_modified_file(_relativize_path(str(p), repo_root))
            # streamfmt (mm6wuz) E-06: the same tier rule the oc renderer applies. A read or a
            # search does not change the repository, so it is suppressed at the default tier and
            # surfaced at `-v`.
            if kind in ("read", "find") and verbosity < 1:
                return None
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
                # Was `Path(...).name`, a BARE BASENAME, which told an operator `runner_shared.py`
                # was touched without saying which of several trees it lived in. Repo-relative is
                # both more informative and what the leak-sanitizer prefers over an absolute path.
                cmd = _relativize_path(str(params["AbsolutePath"]), repo_root)
            elif "TargetFile" in params:
                cmd = _relativize_path(str(params["TargetFile"]), repo_root)
            elif "Pattern" in params:
                cmd = str(params["Pattern"])

            # THE AGY TOOL NAME IS KEPT in the payload, unlike the oc renderer which drops `bash`
            # in favor of `❯ bash:`. The reason is that agy's tool names are host-specific and NOT
            # recoverable from the class prefix (`write_to_file` and `replace_file_content` are both
            # file-mutating, and `agy_prefix_kind` maps them to different kinds only by a name
            # heuristic), so discarding the name would lose information the oc stream never had.
            summary = f"{tool_name}: {_one_line(cmd, 120)}" if cmd else str(tool_name)
            status = _AGY_STATE_TO_STATUS.get(state, "")
            if status in ("error", "failed"):
                prefix_style = "red"
            elif status in ("running", "pending", "in_progress"):
                prefix_style = "yellow"
            else:
                prefix_style = "bold"
            head = (
                format_event_prefix(kind, pal, use_unicode, style=prefix_style)
                + summary
            )
            if state == "DONE":
                # `duration_seconds` is AGY-ONLY (the oc stream has no per-tool duration) and is
                # preserved deliberately.
                dur = step.get("duration_seconds")
                if dur is not None:
                    head += pal(f" ({dur:.2f}s)", "dim")
            if verbosity >= 2 and params:
                # The only extra detail the agy schema affords at `-vv`. There is NO `filediff`
                # equivalent and no diagnostics payload, so the oc renderer's diff hunks and
                # Pyright entries are simply NOT REACHABLE here; the raw parameters are.
                head += "\n" + pal(
                    "      "
                    + _one_line(json.dumps(params, sort_keys=True, default=str), 200),
                    "dim",
                )
            return head

        if step_type == "agent_response" and state == "DONE":
            return None

        if step_type == "subagent":
            if state not in ("DONE", "ERROR", "FAILED"):
                return None
            subagent = step.get("subagent_info") or {}
            subagents = subagent.get("subagents", [])
            count = len(subagents) if isinstance(subagents, list) else 1
            noun = "child" if count == 1 else "children"
            status = _AGY_STATE_TO_STATUS.get(state, "")
            if status in ("error", "failed"):
                prefix_style = "red"
            elif status in ("running", "pending", "in_progress"):
                prefix_style = "yellow"
            else:
                prefix_style = "bold"
            return (
                format_event_prefix("child", pal, use_unicode, style=prefix_style)
                + f"{count} {noun} {state.lower()}"
            )

    return None


# `StallTimeout` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# `EmptyStatusSelection` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


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


# rununify 04 (`tx6q0h`): one-line wrapper over the shared definition. Measured before the lift, the
# shared body returns byte-identically to this host's own copy on every state this host produces; the
# `variant`/`profile` branches it also carries are simply unreached here, because no profile subsystem
# on this host populates those keys.
def driver_actor(state: dict[str, Any]) -> str:
    return runner_shared.driver_actor(state, labels=runner_shared.AGY_HOST_LABELS)


# rununify 05 (`ct4w0a`) E-04: the `driver_begin` LAUNCHER BODY is now defined ONCE in
# `runner_shared` and this is the one-line wrapper that binds this host's pin helpers (which are
# defined in `oc_runipd` and so cannot move into the shared module; see the shared definition's note
# and the `818uru` OQ-02 ruling that prescribes injection for exactly this case).
#
# THIS HOST GAINS A CORRECTNESS FEATURE, which is the whole point of adopting oc's version rather than
# keeping this one. The body that used to live here accepted no `isolated` and layered no baseline
# declaration onto the child env, so an ISOLATED `aw agy run` turn asked `aw ipd begin` to gate on the
# MAIN tree's cleanliness while the turn would actually execute in a LANE. That refused unrelated lanes
# over a co-worker's uncommitted edit to a commonly-scoped file. The signature gains the same
# keyword-only `isolated` (default `False`), so the existing three-argument call shape is unaffected.
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


# rununify 04 (`tx6q0h`): one-line wrapper over the shared definition, binding THIS host's labels.
# The two copies differed ONLY by the `aw oc run` / `aw agy run` string they write into a plan's
# PERMANENT finalize record, which is why the shared version takes no default for it.
def _compute_scope_reconciliation(
    repo: Path, plan_path: Path
) -> tuple[dict[str, str], dict[str, str]]:
    return runner_shared.compute_scope_reconciliation(
        repo, plan_path, labels=runner_shared.AGY_HOST_LABELS
    )


def driver_finalize(
    repo: Path, plan_path: Path, id6: str, actor: str, message: str
) -> tuple[int, str]:
    """Run `aw ipd finalize <id6> --actor --message --apply` after a verified turn.

    Computes the two-way scope reconciliation programmatically (`--scope-reason` for out-of-scope
    changed paths, `--scope-ack` for declared-but-unmodified paths) from the plan's Scope-Paths vs
    the actual changed paths, then invokes the SAME gated finalize surface (no forked path). Never
    forces the transition: a refusal returns nonzero and the caller records the child NOT-executed.
    Returns (exit_code, stderr).

    IDEMPOTENT (finidem `ld8lb3` E-05), through the SAME `runner_shared.finalize_outcome` the oc twin
    uses: a plan whose terminal transition already succeeded is reported as success so the caller
    integrates, instead of being refused for the receipt that success consumed. This is TWO changed
    sites because `driver_finalize` is genuinely duplicated per host; the DECISION is shared, so the
    two hosts cannot drift into two answers."""
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
    # finidem `ld8lb3` E-05: identical to the oc twin's last step, and deliberately the SAME shared
    # decision function rather than a second copy of the rule.
    return runner_shared.finalize_outcome(
        repo,
        plan_path,
        id6,
        result.returncode,
        (result.stderr or result.stdout or "").strip(),
    )


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

    # dirtygates Order 05 (`ajxr5d`) E-11: read lanes through the SWEEP-AWARE composer, so an interrupt
    # BETWEEN reviews reclaims the review sweep lane too instead of leaking it with no owner. The
    # per-item reader is composed rather than edited (its body is fingerprint-pinned as a pure move); see
    # `runner_shared.lane_records_including_sweep`. The classification and preservation below are
    # UNCHANGED and apply to the sweep lane exactly as to a per-item lane: a lane holding work is left
    # entirely alone and snapshotted, which is what keeps a stranded review recoverable.
    lanes = [
        describe_lane(repo, rec)
        for rec in runner_shared.lane_records_including_sweep(state)
    ]
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
                            "worktree": lane["worktree"],
                            "snapshot_commit": snapshot,
                            "reason": reason,
                        },
                    )
                except Exception as exc:
                    lane["action"] = "preserved"
                    append_jsonl(
                        run_dir / "events.jsonl",
                        {
                            "at": utc_now(),
                            "event": "lane-teardown-failed",
                            "id6": lane["id6"],
                            "branch": lane["branch"],
                            "detail": str(exc),
                        },
                    )
                continue
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


# `sync_receipt_into_worktree` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# integpath-02 (`6sb3yu`): `build_lane_outcome`, `dirty_tree_overlap` and `integrate_lane_branch` were
# defined HERE AND in `oc_runipd`, and had already drifted. The implementations are now the single
# shared ones in `runner_shared`; what remains is a wrapper at the ORIGINAL name and signature per
# symbol, so no call site in this module changed. See the fuller note at the oc twin.
#
# THE `host_label` BINDING BELOW IS THIS FILE'S WHOLE STAKE IN THE MOVE: the shared function gives it
# no default, and this wrapper is what keeps a merge commit on main reading `integrate(aw agy run)`
# rather than silently claiming the other driver did the integration.


def build_lane_outcome(repo: Path, handle: Any, id6: str) -> Any:
    """Build this host's `orchestrate_isolation.LaneOutcome` for a finalized lane branch.

    integpath-02 (`6sb3yu`): one-line wrapper over the single shared implementation, binding THIS
    host's `run_checked` (which itself binds `pinned_child_env`).
    """
    return runner_shared.build_lane_outcome(repo, handle, id6, run_checked=run_checked)


def collect_lane_earned_paths(repo: Path, handle: Any) -> list[str]:
    """The repo-relative paths a LANE BRANCH produced (dirtygates-03 `9iq461` E-03).

    The MIRROR of the oc twin and equally thin: it binds THIS host's `run_checked` and nothing else.
    The implementation and its rationale live once in `runner_shared.collect_lane_earned_paths`, so
    neither host imports it from the other (backlog `cnwy8g`).
    """
    return runner_shared.collect_lane_earned_paths(
        repo, handle, run_checked=run_checked
    )


# `make_integration_validation_runner` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


def evaluate_clean_base_for_launch(
    repo: Path, *, shared_tree: bool = False
) -> lane_containment.CleanBaseResult:
    """lanectn Order 02 (`nna8yz`) E-05, spec R5.4: is `repo` a complete base for an unattended turn?

    The MIRROR of the oc twin, and deliberately as thin as it: it supplies the git invocation and the
    `--untracked-files=no` scope, while the RULE lives once in `lane_containment.evaluate_clean_base`.
    Re-deciding here what counts as dirty would fork the rule (spec R6.1) and let the two hosts drift
    on a containment guarantee (CID-3).

    `shared_tree` is PASSED THROUGH, never interpreted (dirtybase `3i0aaz` E-03), for the same reason
    and in the same shape as the oc twin: it selects which true refusal sentence the shared rule
    produces and changes nothing about what counts as dirty.
    """
    _rc, out, _err = _run_git(repo, ["status", "--porcelain", "--untracked-files=no"])
    return lane_containment.evaluate_clean_base(out, shared_tree=shared_tree)


def integrate_lane_branch(
    repo: Path, handle: Any, id6: str, validation_runner: Any
) -> tuple[bool, str, str]:
    """Integrate a verified lane branch back to main behind the REUSED integration gate.

    integpath-02 (`6sb3yu`): the IMPLEMENTATION is the single shared `runner_shared
    .integrate_lane_branch`, whose docstring carries the full contract (the dirty-tree refusal, the
    gate call, `--ff-only` then the controlled `--no-ff` fallback, the abort that leaves main clean,
    and the three returned `kind` values). This wrapper binds THIS host's `run_checked` and its OWN
    `host_label`.

    dirtygates Order 05 (`ajxr5d`) E-03/E-06: it now also binds `action_kind="execute"` as a LITERAL,
    exactly as it binds `host_label`, so this wrapper's SIGNATURE is unchanged and the shipped contract
    test asserting each wrapper's kwonly list is EMPTY stays green. The review path uses the sibling
    `integrate_review_lane_branch` below.
    """
    return runner_shared.integrate_lane_branch(
        repo,
        handle,
        id6,
        validation_runner,
        host_label="aw agy run",
        run_checked=run_checked,
        action_kind=runner_shared.INTEGRATION_ACTION_EXECUTE,
    )


def integrate_review_lane_branch(
    repo: Path, handle: Any, id6: str
) -> tuple[bool, str, str]:
    """Integrate a REVIEW lane back to main: one merge, no revalidation (`ajxr5d` E-03/E-06, OQ-01).

    The agy twin of `oc_runipd.integrate_review_lane_branch`, binding THIS host's `host_label` so a
    review's merge subject on main still reads `integrate(aw agy run): ...`. It takes NO
    `validation_runner`, which is what makes the revalidation skip structural: there is no runner to
    pass because a review produces nothing to revalidate, and a caller therefore cannot supply a
    synthetic validation result through this path even by mistake.
    """
    return runner_shared.integrate_lane_branch(
        repo,
        handle,
        id6,
        None,
        host_label="aw agy run",
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
    """integpath-03 (`51vw4y`) E-03/E-04/E-05: re-attempt THIS host's deferred integrations.

    The MIRROR of the oc twin and equally thin: the LADDER is the single shared
    `runner_shared.reattempt_deferred_integrations`, and this binds only what is host-specific - this
    host's `integrate_lane_branch` wrapper (so a re-attempt's merge commit still reads
    `integrate(aw agy run)`), its validation runner, its lane-handle reconstruction from the durable
    `preserved_*` fields, and what "finished" means here. A ladder written into each driver would be
    written twice and fixed once (CID-3), which is the failure integpath-02 collapsed these symbols to
    prevent.

    `i4ak5n` E-04/E-06: the REVIEW-ACTION pair is bound here too, symmetrically with the oc twin (which
    carries the full rationale). The execute pair pins `action_kind=execute` - exactly what triggers the
    revalidation gate a review must skip by NOT RUNNING - and its success path writes `executed` and
    closes a backlog item, neither valid for a review. The review pair is this host's
    `integrate_review_lane_branch` plus the SHARED `runner_shared.finish_integrated_review_item`, and the
    shared `integration_action_for_item` (never a local test) decides which pair an item gets.
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
        # step measures the merge result instead of returning a constant True. The name is the SAME
        # object oc binds (agy re-exports oc's definition), so the two hosts measure identically.
        return integrate_lane_branch(
            repo,
            handle,
            str(item.get("id6") or ""),
            make_integration_validation_runner(
                state, run_dir, dict(item), suite_check=run_suite_check
            ),
        )

    def _finish(item: Any, handle: Any, reason: str) -> None:
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
        # dirtygates-03 (`9iq461`), symmetric with `oc_runipd`: the original turn already attempted
        # the close IN ITS LANE, so an eligible item arrives with this merge and this call skips. Kept
        # for the one case it still answers (an item not eligible during the original turn but eligible
        # now). The guard prevents re-evaluating an already-closed item, which would answer
        # `item is already done` and overwrite the success record with a refusal.
        if not (item.get("backlog_close") or {}).get("closed"):
            process_backlog_close(run_dir, state, item)
        save_state(run_dir, state)

    def _integrate_review(item: Any, handle: Any) -> tuple[bool, str, str]:
        """THE REVIEW-ACTION MERGE, the agy twin: `action_kind=review`, no validation runner to pass."""
        return integrate_review_lane_branch(repo, handle, str(item.get("id6") or ""))

    def _finish_review(item: Any, handle: Any, reason: str) -> None:
        """THE REVIEW SUCCESS PATH, delegated to the SHARED performer (never a second copy).

        NOT `_finish`: no `executed`, no backlog close, no plan-path resolution, and NEVER a per-item
        teardown of the shared sweep lane (OQ-02 option (a)).
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

    The MIRROR of the oc twin and equally thin: the DECISION (which items qualify, the refusals, the
    real validation runner, the gate call, the honest state write, E-04's hold-back) is the shared
    `runner_shared.integrate_stranded_lanes`. This binds only the host-specific four: THIS host's
    `integrate_lane_branch` wrapper (so a recovered merge subject on MAIN reads
    `integrate(aw agy run): ...`), this host's bound `run_suite_check` and `process_backlog_close`
    (injected because `runner_shared` may not import either driver), and where the operator-facing
    lines go.
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


# rununify 06 (`sy7uwh`) E-02/E-03: `PlanRecord` and `parse_plan_file` are IMPORTED from
# `runner_shared`, not defined here.
#
# WHAT WAS HERE AND WHY IT IS GONE. This module used to define its OWN `PlanRecord` - identical to oc's
# except that it LACKED oc's `kind` field - and its own `parse_plan_file` to build it. `818uru` pinned
# that split deliberately and wrote a test forbidding unification, deferring it to "a later child".
# THIS WAS THAT CHILD, and the override is legitimate because the split's premise DISSOLVED: when it
# was pinned this driver had no use for `kind`, and it now imports the shared `action_for`, which READS
# `kind` to detect an orchestrator. So the missing field bought nothing and cost a redundant disk read
# per plan, through the private `_plan_kind` helper that is also gone from the record path.
#
# THE FIELD SET IS oc's, per the Set's standing "oc is preferred" ruling, and it was measured to be a
# strict SUPERSET of this module's, differing in exactly `kind` - so this host LOST NOTHING and GAINED
# the field it was re-reading from disk. The two pins that asserted the split were INVERTED rather than
# deleted (`tests/test_runner_shared.py::DiscoverPlansRecordTypeTests` and the single record-shape
# assertion in `tests/test_orchestrator_retirement.py`), each now citing `sy7uwh`.
# THE THREE READERS COME FROM `runner_shared` NOW, NOT FROM `oc_runipd`. They moved with
# `parse_plan_file`, which closes over them, and the redirection REDUCES the oc-to-agy import coupling
# backlog `cnwy8g` tracks by three (56 -> 53, re-measured in
# `tests/test_orchestrator_probe_cache.py`). `_read_kind`'s old import comment here said the reader had
# to stay in `oc_runipd` "because moving it means moving `_KIND_RE` and the whole front-matter reader
# family with it, which is `cnwy8g`'s job"; moving `parse_plan_file` required exactly that, so it was
# done, and `_KIND_RE`/`_PLAN_FILENAME_RE` moved too rather than being left as duplicate constants.
# (The import itself is hoisted to the top-of-file shared-import block, per E402.)


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


# rununify 06 (`sy7uwh`) E-03: `_plan_kind` and `build_dynamic_manifest` are GONE from this module, and
# the two removals are for DIFFERENT reasons, which matters because conflating them would have caused a
# regression.
#
# `build_dynamic_manifest` is now IMPORTED from `runner_shared` (see the import block below). The two
# hosts' versions differed in exactly ONE expression - `'kind': rec.kind` on oc versus
# `'kind': _plan_kind(rec.path)` here - so unifying the record collapsed the symbol for free.
#
# `_plan_kind` HAD TWO CALLERS AND ONLY ONE OF THEM WAS THE RECORD SPLIT. Its docstring described only
# that first one (the `build_dynamic_manifest` line above), and deleting the helper on the strength of
# that docstring would have destroyed the SECOND caller, a LEGACY-MANIFEST FALLBACK in
# `initialize_run` with an entirely independent reason: a hand-written manifest carrying no `kind` key
# made an APPROVED ORCHESTRATOR derive `execute` and be AGENT-EXECUTED, the exact defect
# orchretire-03 (`pgq326`) fixed, and no test covered it. So the first caller became `rec.kind` and the
# second was LIFTED to `runner_shared.plan_kind_from_file` / `resolve_manifest_kind` - given to BOTH
# hosts rather than kept here, because oc lacked it entirely and the two hosts therefore DISAGREED
# about a correctness gate in oc's disfavor (`sy7uwh` OQ-03, resolved by the maintainer 2026-09-16).
# `tests/test_rununify_record.py` covers that fallback on both hosts for the first time.


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
        # revsweep-02 (`6ypimw`) E-02, the SAME shared function the opencode host calls, which is the
        # entire point: the closure this replaces was a verbatim duplicate of oc's (they diffed to one
        # loop-variable hunk), so fixing one host's `status == "to-review"` test would have left THIS
        # one wrong. The oc twin carries the full note; spec 25kzda 2.4a property 2 is the rule.
        expanded = runner_shared.sweep_review_candidates(manifest, repo=repo)

        if not expanded:
            # revsweep 76gsmv E-04: spec 25kzda 2.4a property 3. The message string is unchanged;
            # only the TYPE changed, which is what lets `main` exit 0 for the status selectors
            # WITHOUT relaxing `DriverError` generally (a misspelled id6 still exits 2).
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
        # setidsel (`7ap6ku`): EVERY branch above converges here, so the admission test belongs at
        # this one point. Before this, only the `all` branch filtered, so naming a Set queued its
        # RETIRED plans with a live `execute` action. THE WORDING AND THE TWO SHAPES ARE THE OC
        # TWIN'S, deliberately: a Set member is dropped SILENTLY (a Set is a topic label that
        # legitimately holds its own finished work forever), while an EXPLICITLY NAMED plan REFUSES
        # LOUDLY (the operator typed that identifier, so a silent drop would send them hunting a
        # typo that is not there). `tests/test_runipd_selector_admission.py` pins both hosts to the
        # same answers; do not let this drift from the oc copy.
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


# orchretire-03 (`pgq326`) E-04: the local `determine_action` that lived here is DELETED, not kept as a
# wrapper. It was a re-fork of oc's, and the divergence that mattered was not in its body but in what sat
# NEXT to it: oc also had `action_for`, and this module did not, so the two hosts derived different
# actions for the same plan. Both names are now imported from `runner_shared` at the top of this module.


# revsweep 76gsmv E-03: the `--action` vocabulary spec 25kzda 2.1 declares, in PARITY with the oc
# runner (which carries the full rationale). `review` is implemented; `plan` and `execute` are
# registered for grammar parity and refused honestly, because their per-type legality tables (2.6)
# need dispatch this Set has not built. Accepting them silently would let an operator believe an
# action was constrained when nothing constrained it.
# rununify 04 (`tx6q0h`): relocated to `runner_shared`; re-exported for existing call sites.
ACTION_CHOICES = runner_shared.ACTION_CHOICES
ACTION_IMPLEMENTED = runner_shared.ACTION_IMPLEMENTED


# rununify 04 (`tx6q0h`): one-line wrapper over the shared definition. The safety content (spec
# 25kzda 2.6's three refusals) now has ONE implementation; only the `aw agy review` hint is per-host.
# The previous local docstring made two claims that were FALSE and are not carried forward: that
# `--full-auto` "DEFAULTS TO TRUE on this host" (it is False on both, measured) and that the derived
# action comes from `determine_action` (both hosts call `action_for`). See the shared docstring.
def enforce_requested_action(
    requested: str | None,
    items: list[tuple[str, str, str]],
) -> None:
    runner_shared.enforce_requested_action(
        requested, items, labels=runner_shared.AGY_HOST_LABELS
    )


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
4. Commit only files you changed, limited to the paths you name, through `aw commit <plan> -- <paths>` (or `aw commit --no-plan -m <msg> -- <paths>` when no plan governs the change).
5. Never push to remote.
6. Write valid outcome JSON before exiting.
"""


def assert_verification_flags_are_distinct(start_parser: Any) -> None:
    """Prove the two verification spellings did not COLLIDE at parser build (`ybkmzp` E-02, F-14).

    THE HAZARD THIS CLOSES, measured rather than imagined. `BooleanOptionalAction` auto-generates a
    `--no-X` for every option string it is given, so registering `--validate` with oc's alias list
    (`--verify`, `--audit`) would generate `--no-verify` and `--no-audit`, which this parser already
    declares. With the default `conflict_handler` that raises at build time and is impossible to
    miss. With `conflict_handler="resolve"` it does something far worse and SILENT: the new action
    STEALS `--no-verify`/`--no-audit`, and the shipped spelling stops meaning what every existing
    invocation and every piece of documentation says it means.

    CHECKED AT THE PARSER, not at a parsed namespace, deliberately. The collision is a property of
    HOW THE PARSER WAS BUILT, so this is the only place it is decidable; a namespace-level check
    cannot distinguish a stolen flag from a hand-constructed `Namespace` that simply omitted the
    attribute, and several shipped tests legitimately build exactly such namespaces.
    """

    by_option: dict[str, str] = {}
    for action in getattr(start_parser, "_actions", []):
        for option in action.option_strings:
            by_option[option] = action.dest
    for option, expected in (
        ("--validate", "validate"),
        ("--no-validate", "validate"),
        ("--no-verify", "no_verify"),
        ("--no-audit", "no_verify"),
    ):
        actual = by_option.get(option)
        if actual != expected:
            raise DriverError(
                f"internal: {option} resolves to dest {actual!r}, expected {expected!r}. The two "
                f"verification spellings have collided, which would silently change what "
                f"--no-verify means on the host whose shipped posture is verification ON"
            )


def verification_flag_tristate(args: argparse.Namespace) -> Optional[bool]:
    """This host's TWO spellings collapsed into ONE tri-state (`ybkmzp` E-02).

    `--validate` / `--no-validate` is the tri-state (`True` / `False` / `None`, where `None` means
    the operator said nothing and the runner-profile store decides). `--no-verify` (with its
    `--no-audit` alias) is the SHIPPED spelling every existing invocation and every piece of
    documentation uses, so it is RETAINED unchanged and means exactly `--no-validate`.

    A CONTRADICTORY PAIR IS REFUSED rather than resolved by precedence. Measured: argparse accepts
    `--no-verify --validate` happily, parsing to `validate=True, no_verify=True`, so this check is
    hand-written and not an argparse freebie. Letting either spelling silently win would make a
    verification decision the operator did not make, and BOTH directions of that error are bad: one
    skips a check that was asked for, the other pays for a check that was declined.

    AN ABSENT ATTRIBUTE READS AS "NOT PASSED", which is the safe direction and is not the F-14
    hazard. Absence here means a hand-built `Namespace` (several shipped tests construct partial ones
    on purpose), and treating it as "no flag" leaves the decision to the profile store, whose floor
    on this host is verification ON. The flag-collision hazard is a property of the PARSER and is
    refused there instead, by :func:`assert_verification_flags_are_distinct`.
    """

    validate = getattr(args, "validate", None)
    no_verify = getattr(args, "no_verify", False)
    if bool(no_verify) and validate is True:
        raise runner_shared.RunFlagRefusal(
            "--no-verify (or --no-audit) and --validate contradict each other: one asks to skip "
            "turn-2 verification and the other asks to run it. Pass exactly one; --no-verify is "
            "the same request as --no-validate"
        )
    if bool(no_verify):
        return False
    return validate


def resolve_verification_decision(
    args: argparse.Namespace,
) -> runner_shared.VerificationDecision:
    """Resolve WHETHER this run verifies, through the ONE shared helper (`ybkmzp` E-04).

    A one-line binding, deliberately: the precedence chain lives in
    `runner_shared.resolve_verification_decision` so both hosts consume the same resolution, and
    only the flag-reading and the polarity translation are per host. A second copy of the chain here
    is how the deleted `_read_deps` pair came to be identically wrong in both drivers.

    NO PROFILE NAME IS PASSED, because this host has none to pass: `start` declares no `--profile`
    and this driver has no `as <profile>` clause (that is oc-only). The tiers reachable here are
    therefore the explicit flag, the per-runner DEFAULT profile (`defaults.profiles["agy"]`, which
    resolves without being named), `defaults.validate`, and the `agy` registry row. Adding a
    `--profile` flag or an `as` clause is the deferred dispatch-adapter work, not this plan's.
    """

    return runner_shared.resolve_verification_decision(
        runner="agy", profile=None, validate=verification_flag_tristate(args)
    )


def initialize_run(args: argparse.Namespace) -> Path:
    """Initialize a run, freezing queue items (including "from_backlog") and options via runner_shared.initialize_run_core.

    Freezes queue items with "from_backlog" and runs report_untracked_dirt_at_run_start.
    Evaluates __file__ in the runner module so driver identity attributes to this host.
    """
    # hostdefault-02 (`ybkmzp`) E-04: resolve THIS run's verification decision here, at the same
    # pre-durable seam as the refusals and BEFORE the run directory is created below.
    verification = resolve_verification_decision(args)
    host_options = {
        "agy_executable": getattr(args, "agy_executable", None)
        or getattr(args, "agy", None),
        "model": getattr(args, "model", DEFAULT_MODEL),
        "effort": getattr(args, "effort", None),
        "timeout": getattr(args, "timeout", DEFAULT_TIMEOUT),
        "new_session": getattr(args, "new_session", False),
        "dangerously_skip_permissions": getattr(
            args, "dangerously_skip_permissions", True
        ),
        "no_verify": not verification.validate,
    }

    return runner_shared.initialize_run_core(
        args,
        host="agy",
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


# rununify 04 (`tx6q0h`): one-line wrapper over the shared report renderer. THREE OBSERVABLE CHANGES
# to this host's report land here and are deliberate: the verify column header becomes `Verify`, its
# cell is no longer BACKTICKED, and its empty placeholder is an empty cell rather than `N/A`. The
# backtick removal is a BUG FIX: `run_viewer.py:1008` does not strip backticks for that column and
# `:1370` compares it to the bare string `verified`, so this host never rendered the `[verified]`
# badge. No `render_launch_identity` is bound: this host has no profile subsystem, so the `- Launch:`
# line would read `profile=(none recorded)` forever (plan `tx6q0h` OQ-01).
def write_report(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.write_report(run_dir, state, labels=runner_shared.AGY_HOST_LABELS)


# rununify 02 (`818uru`) E-06: one-line wrapper over the shared `save_state`, binding THIS driver's
# `write_report`. `write_report` is class (c) DIVERGED (the two drivers render different reports), so
# importing one into shared code would silently give BOTH drivers that one's format. Keeping the
# original name and signature is what leaves this module's 30 `save_state` call sites untouched.
def save_state(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.save_state(run_dir, state, write_report=write_report)


# `_SESSION_ID_KEYS` and `extract_session_id` are now defined ONCE in `runner_shared` and imported
# above (rununify 05 `ct4w0a`). THE UNION KEPT EVERYTHING THIS HOST READ -- all four keys including
# `conversation_id`, plus the nested `result`/`init` lookup -- because that is this host's own wire
# format and oc's reader could not see it. WHAT CHANGED HERE is the return DISCIPLINE: this body
# returned the FIRST non-empty hit, and the shared reader adopts oc's whole-file scan with a
# `ses_`-prefix preference, so a log carrying a `conversation_id` EARLY and a `ses_` value LATER now
# resolves to the `ses_` value. That is decision `06-ct4w0a-D1`, it occurred in 0 of 627 real logs, and
# `tests/test_rununify_conflicts.py` pins it. The dead `fallback` local this body carried (initialized
# to None, returned at the end, unreachable because every assigning branch returned first) is gone.


# `_findings_block_reason` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# NEITHER `dependency_status` NOR `dependency_status_detailed` IS DEFINED HERE. Both are RE-EXPORTED
# from `oc_runipd` in the import block above, so both drivers bind the SAME objects and the runtime
# satisfaction semantics exist exactly ONCE (asserted by
# tests/test_runner_item_dependencies.py::test_the_implementation_is_shared_not_copied, whose
# `_SHARED_NAMES` list now names both).
#
# THE HISTORY IS WHY THIS COMMENT IS EMPHATIC, because the same defect recurred here twice. The merge
# of revgate 7nkcgp and 8guhs0 briefly produced BOTH a re-export and a local copy of
# `dependency_status`; that copy went. The `_detailed` sibling's copy SURVIVED that cleanup because
# `_SHARED_NAMES` never listed it, so the guard passed over a live divergence for months: this
# driver's DISPATCH path called the re-exported `dependency_status` (which resolves `_detailed` in
# OC's globals) while its DRAIN path called the local copy, and the copy could not even parse a typed
# `executed:<id6>` token. depreview 03ie04 E-03 deleted it and E-04 closed the guard hole. `plan_bucket`
# is byte-identical between the two modules and `resolve_plan_path` differs only in formatting
# (verified), so the imported implementations behave identically here.


# `build_review_prompt` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


def build_isolation_notice(lane_root: Path | None) -> str:
    """The WORK HERE block for an isolated turn, or "" for a main-checkout turn.

    lanectn `cqx5v7` E-05: this used to delegate to `oc_runipd.build_isolation_notice`, which made the
    OPENCODE driver the de-facto shared library for a host-neutral rule - exactly what spec `7ckptx`
    R2.6 forbids. It now calls the host-neutral `lane_containment.isolation_notice`, the same function
    the oc driver calls, so neither host owns the other's text.
    """
    return lane_containment.isolation_notice(lane_root)


# resumedupe (`txc9l1`) E-04: recovery ROUTING has ONE definition, in `oc_runipd`, and these delegate
# to it. Following the shipped `build_isolation_notice` pattern above rather than copying: the twin of
# `build_recovery_lane_notice` was for a while a VERBATIM copy here, which is exactly how a one-runner
# fix leaves the other driver duplicating work. `runner_shared` would be the tidier home, but it holds
# a strict AST fingerprint pin proving a PURE MOVE of the symbols it received, so adding new logic
# there is out of this plan's scope; delegation gets the same no-drift guarantee today.


def classify_recovery_disposition(
    repo: Path, item: dict[str, Any], state: dict[str, Any]
) -> Any:
    """Delegate to the ONE definition in `oc_runipd` (see its docstring)."""
    from agent_workflows.oc_runipd import classify_recovery_disposition as _shared

    return _shared(repo, item, state)


# `resolve_prior_lane` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


def build_verify_and_continue_notice(repo: Path, decision: Any) -> str:
    """Delegate to the ONE definition in `oc_runipd` (see its docstring)."""
    from agent_workflows.oc_runipd import build_verify_and_continue_notice as _shared

    return _shared(repo, decision)


def route_recovery_turn(
    run_dir: Path,
    state: dict[str, Any],
    item: dict[str, Any],
    recovery: bool,
) -> Any:
    """Delegate to the ONE definition in `oc_runipd` (see its docstring)."""
    from agent_workflows.oc_runipd import route_recovery_turn as _shared

    return _shared(run_dir, state, item, recovery)


# rununify 04 (`tx6q0h`): one-line wrappers over the shared prompt builders. THE INSTRUCTION TEXT
# THIS HOST'S AGENT RECEIVES CHANGED, deliberately and by the maintainer's ruling (plan `tx6q0h`
# OQ-03), and it is the most consequential thing in this commit. This host's agents are now told, as
# the OpenCode host's already were, to preserve partial work through a nonterminal checkpoint or an
# attributable isolated branch, to leave checkouts they do not own safe for later turns, and never to
# claim executed unless the real terminal state supports it. The verifier prompt also gains the
# "Never push" prohibition it previously LACKED ENTIRELY while instructing the agent to commit.
def build_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
    recovery: bool,
    lane_root: Path | None = None,
    routing: Any = None,
) -> str:
    return runner_shared.build_prompt(
        item,
        state,
        run_dir,
        plan_path,
        recovery,
        lane_root,
        routing,
        labels=runner_shared.AGY_HOST_LABELS,
        build_isolation_notice=build_isolation_notice,
        build_verify_and_continue_notice=build_verify_and_continue_notice,
    )


def build_verifier_prompt(
    item: dict[str, Any],
    state: dict[str, Any],
    run_dir: Path,
    plan_path: Path,
) -> str:
    return runner_shared.build_verifier_prompt(
        item, state, run_dir, plan_path, labels=runner_shared.AGY_HOST_LABELS
    )


# `write_prompt` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


# `attempt_log_path` is now defined ONCE in `runner_shared` and imported above (rununify 03 `i3d6ml`).


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
    *,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Record a level-3 stop on the item with KNOWN certainty (spec R18), returning the record.

    runstop foi1b3 (E-03); the exact counterpart of the `oc_runipd` helper, sharing the SAME record
    builder in `runner_stop` so the two drivers cannot describe the same stop differently.
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
    *,
    work_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Record a level-4 stop on the item as INDETERMINATE (spec R18/R21/R22), returning the record.

    runstop m0z0ti (E-02/E-03); the exact counterpart of the `oc_runipd` helper, sharing the SAME
    record builder in `runner_stop` so an operator switching hosts gets the same guarantee
    (orchestrator CID-3). No last-completed-operation is invented: the cut point was not observed.
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
    tracker: StreamTracker | None = None,
    # runanalytics Order 04 (`5f2h8i`) E-02/E-04: the invocation's PHASE, the exact mirror of the oc
    # twin's parameter. Stated by the call site, never inferred from `log_suffix` (a presentation
    # detail) - see `oc_runipd.run_opencode` for the full reason. Defaulted, so no existing call site
    # or test changes.
    telemetry_phase: str = runner_shared.TELEMETRY_PHASE_EXECUTE,
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
    # streamfmt (mm6wuz) E-06: read from the FROZEN run options, the same path `output_mode` takes.
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

    # lanectn Order 03 (`lhmrhx`) E-06, spec R4.1a/R4.1b/R4.1c: the SANCTIONED ASYMMETRY with the oc
    # twin, recorded rather than left to be inferred from an absence.
    #
    # NO PERMISSION POLICY DOCUMENT IS SUPPLIED HERE, AND THAT IS NOT AN OMISSION. This host has NO
    # DENIAL POSTURE, permanently and by design (R4.1): `--dangerously-skip-permissions` is appended
    # above and its option DEFAULTS TO TRUE, because the only alternative
    # (`--no-dangerously-skip-permissions`) requires INTERACTIVE permissions an unattended turn has no
    # answerer for, and running without it was measured to fail or deadlock repeatedly. That is a
    # DECIDED CONSTRAINT this spec adopts (R4.1c), not a defect it tolerates, and R4.1b puts closing
    # it out of scope. Do NOT "harden" it: `tests/test_lane_permission_posture.py` PINS the default
    # and will fail if it is flipped (E-05), a guard running in the OPPOSITE direction from every
    # other check in this Set.
    #
    # CONSEQUENCE, which is why R4.1a requires it be RECORDED and not glossed: on this host the host
    # layer contributes NOTHING to containment, so the guarantee rests ENTIRELY on R1 (the prompt
    # names nothing outside the lane) and R4.4 (the driver bounds below). Those are load-bearing here
    # rather than defence-in-depth. No artifact may describe this host as "denied"; the shared
    # constructor emits `no-denial-posture` and names the layers that DO apply, so a call site cannot
    # get the wording wrong.
    if work_dir:
        lane_containment.record_host_posture(
            run_dir,
            item,
            attempt_no,
            lane_containment.antigravity_posture_record(),
            # NO observation argument, and its absence is MEANINGFUL rather than an oversight: there
            # is no denial policy on this host to observe, so R4.2 has nothing to verify here. The
            # oc twin passes one because it does.
        )

    stall_timeout = options.get("stall_timeout", DEFAULT_STALL_TIMEOUT)

    queue = state.get("queue", [])
    # `progdenom`: DISPATCHABLE WORK, not queue length, so this host's live progress display matches
    # the oc twin and the summary bar. `len` counted Set members that arrived already `executed` and
    # entries frozen `reviewed` awaiting approval, neither of which a run can dispatch.
    total_items = dispatchable_work_total(queue) or 1
    # When working on item at 1-based execution sequence S, number of completed items is S - 1 (e.g. 0 of 2 done).
    seq = execution_index(item, state)
    current_idx = max(0, seq - 1)

    is_tty = bool(getattr(sys.stdout, "isatty", None) and sys.stdout.isatty())

    run_start_mono = state.get("_invocation_start_mono")
    if run_start_mono is None:
        run_start_mono = time.monotonic()

    if tracker is not None:
        tracker.begin_turn()

    # runanalytics Order 04 (`5f2h8i`) E-04: per-invocation telemetry, THE MIRROR of the oc twin.
    #
    # THE SHAPE IS IDENTICAL BECAUSE THE SEAM IS ONE OBJECT, not because two files were kept in
    # step by inspection. Both hosts call `runner_shared.turn_telemetry`, so the event fields and
    # the phase semantics cannot drift; the only difference is the `host` label, which is the ONE
    # value that legitimately differs (compare the sanctioned host-parameterized asymmetries already
    # recorded above). This driver's single agent-launch `Popen` is immediately below, inside
    # `run_agy_turn`, with two callers: the executor and the verifier.
    telemetry_identity = runner_shared.telemetry_identity(
        run_id=str(state.get("run_id") or ""),
        item=item,
        attempt_no=attempt_no,
        phase=telemetry_phase,
        host="agy",
    )
    with (
        runner_shared.turn_telemetry(
            run_dir,
            telemetry_identity,
            repo=state.get("repo"),
            extra_context={"model": options.get("model")},
        ),
        log_path.open("w", encoding="utf-8") as log,
    ):
        # Track the child so a clean shutdown at ANY layer can reap it even when this frame is
        # gone (spec `c4gd2h` R1: no descendant left alive or reparented to init).
        process = runner_shutdown.track_child(subprocess.Popen(argv, **popen_kwargs))
        if process.stdout is None:
            terminate_process(process)
            raise DriverError("Failed to open child agy stdout stream")

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

        # lanectn Order 03 (`lhmrhx`) E-04/E-06, spec R4.4/R4.4a/R4.4d: the SAME host-neutral bounds
        # the oc twin arms, wired here rather than reimplemented (spec R2.6 forbids a second copy).
        # Armed for EVERY unattended turn, isolated or not (R4.4a).
        #
        # R4.4d, THE OVERLAP THIS HOST HAS AND THE OC HOST DOES NOT. Antigravity ALREADY enforces a
        # per-turn ceiling: `DEFAULT_TIMEOUT` is "240m" and is passed to the child as
        # `--print-timeout`, so the HOST kills the turn at nominally 4 hours - numerically identical
        # to `MAX_TURN_TIMEOUT`'s default. Two timers with the same value and different owners is
        # precisely the duplication that leaves a post-mortem unable to say which one killed a turn.
        # RESOLUTION, spec option (ii): the DRIVER bound is deliberately OFFSET to fire FIRST (see
        # `lane_containment.driver_bound_for_host`), so a termination is attributable to the driver,
        # which RECORDS WHICH BOUND FIRED, rather than to an opaque host timeout. WHICH IS EXPECTED
        # TO WIN: the driver's. The host's `--print-timeout` remains the BACKSTOP for the case where
        # the driver's own supervision thread dies.
        turn_bounds = lane_containment.TurnBoundWatch(
            reap=lane_containment.bound_expiry_reaper(process, run_dir, item),
            is_alive=lambda: process.poll() is None,
            max_turn_timeout=lane_containment.driver_bound_for_host(
                # PARSED, not passed raw: `--print-timeout` is written `"240m"`, so reading it as bare
                # seconds would pull the driver ceiling to 4 MINUTES and kill every turn.
                lane_containment.parse_host_ceiling_seconds(timeout)
            ),
        )

        # lanectn Order 04 (`y5od1h`) E-06, spec R3.1/R3.2/R3.5: the missing-input
        # REPORT-AND-REFUSE cycle, WIRED rather than reimplemented (spec R2.6 forbids a second copy,
        # CID-3 makes a rule present in one driver only a DEFECT). The observer object, the reject
        # rules, and the record SHAPE are identical to the oc twin's because both construct the SAME
        # host-neutral class; only this construction line is per-host.
        #
        # NO SANCTIONED ASYMMETRY HERE, unlike R4.1's permission posture: a worker on this host
        # reports a missing input exactly as it does on the other, so the cycle is genuinely uniform.
        missing_input = lane_containment.MissingInputObserver(state["repo"])

        # reaskscore Order 02 (`ty7w6o`) E-02/E-03: the per-turn observer for THE HOST'S OWN
        # TRUNCATION ADMISSION, constructed here beside `MissingInputObserver` for the same reason and
        # fed at the same every-line seam below.
        #
        # THE ASYMMETRY IS DELIBERATE AND MUST NOT BE "FIXED" BY COPYING IT TO THE OC LAUNCHER. Only
        # the agy CLI emits these lines; opencode emits nothing resembling them, so an oc-side copy
        # could never fire. The CLASSIFIER is host-neutral and shared (spec R2.6,
        # `lane_containment.classify_host_turn_line`); only this construction and the feed are per-host.
        # See `ty7w6o` OQ-02/OQ-05, which record that judgement so a reviewer can challenge it.
        host_truncation = lane_containment.HostTruncationObserver()

        try:
            # `escalation_watch` (runstop 71vjbn) joins the turn's scope for the same reason
            # `force_watch` does: it must be armed for exactly the turn's lifetime, no longer.
            # `turn_bounds` (lanectn lhmrhx) joins it too: `__enter__` starts `MAX_TURN_TIMEOUT`'s
            # clock, so entering here means it measures from child start.
            with statusline, watchdog, force_watch, escalation_watch, turn_bounds:
                for raw_line in process.stdout:
                    log.write(raw_line)
                    log.flush()
                    statusline.touch("stdout")
                    watchdog.touch()
                    # lanectn lhmrhx E-04: progress DISARMS the permission bound (resettable);
                    # `MAX_TURN_TIMEOUT` is deliberately NOT reset. See `TurnBoundWatch`.
                    turn_bounds.note_progress()
                    # runstop gq6m2u: the IN-TURN cooperative checkpoint (spec `c4gd2h` R7); the
                    # exact counterpart of the `oc_runipd` site. Side-effect free: it REPORTS the
                    # requested level, and acting on a level belongs to the later phases.
                    level = runner_stop.poll_stop(run_dir)
                    # lanectn y5od1h E-06: the exact counterpart of the `oc_runipd` site, at the SAME
                    # relative point (immediately after the poll) and independent of `output_mode`, so
                    # the two hosts cannot drift on WHEN a report is noticed (CID-3).
                    missing_input.note_line(raw_line, run_dir, item, attempt_no)
                    # reaskscore ty7w6o E-03: the host's truncation admission, observed HERE for
                    # EVERY raw line and independently of `output_mode`. NOT inside the rendering
                    # branches below: a signal parsed inside one is silently inert under `raw` and
                    # `quiet`, which is a mistake this very loop already records having made and
                    # fixed (see the `y5od1h` note above and the `foi1b3` note below). Observing
                    # only: `note_line` never raises, blocks, or terminates.
                    host_truncation.note_line(raw_line)
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
                        if tracker is not None:
                            render_agy_event(
                                raw_line,
                                pal,
                                verbosity=verbosity,
                                repo_root=agent_dir,
                                tracker=tracker,
                            )
                    elif output_mode == "clean":
                        rendered = render_agy_event(
                            raw_line,
                            pal,
                            verbosity=verbosity,
                            repo_root=agent_dir,
                            tracker=tracker,
                        )
                        if rendered is not None:
                            statusline.write_event(rendered)
                    elif tracker is not None:
                        render_agy_event(
                            raw_line,
                            pal,
                            verbosity=verbosity,
                            repo_root=agent_dir,
                            tracker=tracker,
                        )
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
            # reaskscore ty7w6o E-04: RECORD the host's truncation durably, so a turn the host cut is
            # distinguishable afterwards from one that finished rather than only in scrollback.
            #
            # IN THE `finally` ON PURPOSE: the loop above leaves by five paths (normal exhaustion,
            # `StopNowForce`, `StopAtCheckpoint`, `StallTimeout`, `KeyboardInterrupt`), and a host that
            # truncated the work did so whichever one was taken.
            #
            # IT CHANGES NO FATE. `record_host_truncation` writes `attempt["host_truncation"]` and one
            # `host-truncated-turn` event and touches NEITHER `exit_code`, `disposition`, nor
            # `item["status"]`: this plan produces the SIGNAL and `dy9ymn` decides what to do with it.
            #
            # WHY IT WRITES THROUGH `item["attempts"][-1]` RATHER THAN RETURNING THE RECORD. This
            # launcher's return is a FIXED 4-tuple whose shape is TYPED in
            # `runner_shared.execute_item_core`'s `spawn_executor`/`spawn_verifier` parameters and
            # SHARED with the oc twin, so widening it would edit a cross-host contract. `item` is
            # already a parameter here, and `execute_item_core` appends this turn's attempt to
            # `item["attempts"]` BEFORE it spawns, so `[-1]` IS this attempt; the `save_state` calls
            # that follow the spawn's return persist the mutation with no new call site.
            #
            # THE ASYMMETRY IS REAL AND IS STATED RATHER THAN HIDDEN. `run_agy_turn` did NO state
            # writing at all before this (zero `save_state`, zero `append_jsonl`, zero `item[...]`
            # assignments), so this adds a responsibility to a launcher that had none, and the oc twin
            # will NOT have it. That is accepted because only the agy CLI emits these lines and an
            # oc-side copy could never fire - so do NOT "fix" the asymmetry by copying this write into
            # the oc launcher. The host-neutral alternative is to own the observer in
            # `execute_item_core`, which `ty7w6o` OQ-05 records for a plan that declares that file.
            if host_truncation.truncated:
                with contextlib.suppress(Exception):
                    lane_containment.record_host_truncation(
                        run_dir, item, attempt_no, host_truncation
                    )
                # ONE short warning, at the time, because a turn whose work was killed is something
                # the operator should see now rather than discover in a post-mortem.
                with contextlib.suppress(Exception):
                    print(
                        pal(
                            f"  ! IPD {item.get('id6', '')} turn TRUNCATED BY ITS HOST: "
                            f"{host_truncation.describe()}",
                            "yellow",
                        ),
                        file=sys.stderr,
                    )

        if watchdog.stalled:
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
    repo: Path,
    item: dict[str, Any],
    run_dir: Path,
    exit_code: int,
    plan_repo: Path | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Score one finished turn. `plan_repo` (`ajxr5d` E-09/E-06) is the tree to READ THE PLAN FROM.

    DEFAULTED TO `repo`, so every existing call site and every existing behavior is unchanged. Mirrors
    the oc twin; see the review branch below for why an isolated review MUST read the lane.
    """
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
        # dirtygates Order 05 (`ajxr5d`) E-09/E-06: READ THE TREE THAT HOLDS THE REVISION.
        #
        # This branch derives the disposition from the plan's `- Status:`. Once a review runs in a lane
        # the revised plan is ON THE LANE and MAIN still reads `to-review` until the merge lands, so a
        # `repo`-only read makes the comparison ALWAYS miss: a review that set `approved` would be
        # recorded merely `reviewed`, and the check would stop discriminating at all. The lane read is the
        # ONLY reachable answer (plan finding F-15): the disposition is computed BEFORE the integration
        # block and this function is never called after it, so "read main post-merge" is not a real
        # branch. Reuses the same `Path(work_dir) if work_dir else repo` pattern the verifier path below
        # already uses for this exact reason.
        source = plan_repo or repo
        try:
            current_plan = resolve_plan_path(
                source, item.get("configured_file", ""), item["id6"]
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
    # integpath-03 (`51vw4y`) E-01: the EXACT counterpart of the `oc_runipd` site, and it must be here
    # too or this host silently relabels a deferred item `partial` (which IS terminal), destroying the
    # deferral behind a green suite. `integration-deferred` is deliberately NOT in `TERMINAL_STATES`,
    # so the set-difference branch above skips it and control would otherwise reach the fallback below.
    # See the oc site for the full reasoning; a rule present in one driver only is a DEFECT (CID-3).
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
    """Execute a single queue item via runner_shared.execute_item_core.

    Verification is governed by state options and not no_verify.
    """

    def _spawn_executor(
        prompt_path: Path,
        work_dir: Path | None,
        tracker: Any,
        plan_path: Path,
        attempt_no: int,
        session_id: str | None,
        use_continue: bool,
    ) -> tuple[int, str | None, Path, list[str]]:
        return run_agy_turn(
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
            tracker=tracker,
        )

    def _spawn_verifier(
        v_prompt_file: Path,
        current_plan_path: Path,
        work_dir: Path | None,
        tracker: Any,
        attempt_no: int,
    ) -> tuple[int, str | None, Path, list[str]]:
        return run_agy_turn(
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
            tracker=tracker,
            telemetry_phase=runner_shared.TELEMETRY_PHASE_VALIDATE,
        )

    runner_shared.execute_item_core(
        run_dir,
        state,
        item,
        recovery,
        host_labels=runner_shared.AGY_HOST_LABELS,
        spawn_executor=_spawn_executor,
        spawn_verifier=_spawn_verifier,
        raw_launcher=run_agy_turn,
        run_suite_check=run_suite_check,
        process_backlog_close=process_backlog_close,
        driver_module=sys.modules[__name__],
        tracker=tracker,
    )


# runrecon-02 (`fduoj4`) E-01: one-line wrapper over the shared `reconcile_interrupted`, the exact
# counterpart of the `oc_runipd` wrapper, binding THIS driver's `save_state`. The shared body took THIS
# host's tolerant `item.get("configured_file", "")` form, because the oc form raised `KeyError` past an
# `except DriverError` that does not catch it and so abandoned a whole crashed queue on one malformed
# item. `save_state` is injected (class (c) DIVERGED `write_report`; `818uru` OQ-02 wrapper ruling).
def reconcile_interrupted(run_dir: Path, state: dict[str, Any]) -> None:
    runner_shared.reconcile_interrupted(run_dir, state, save_state=save_state)


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
    run_dir: Path,
    retry_incomplete: bool = False,
    output_mode: str | None = None,
    verbosity: int | None = None,
) -> int:
    state = load_state(run_dir)
    # bkclose (zhr6mc) E-06, symmetric with `oc_runipd`: publish the live ledger for the shutdown
    # report BEFORE any turn starts. NO `signal.signal` registration: it is owned by `runstop` Phase 5
    # (`71vjbn`) and guarded by four executed plans (see the ownership note in `oc_runipd`).
    register_signal_report(run_dir, state)
    # streamfmt (mm6wuz) E-06, the MIRROR of the oc twin: both display options are written through
    # ONE `save_state`, because that call site count is pinned per runner by
    # `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten`. `None` means the
    # operator did not pass the flag, so the frozen value stands.
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
                # integpath-04 (`rl67b0`) E-03/E-04, symmetric with `oc_runipd`: REMEMBER the status
                # being overwritten, because the integration pass must follow the indeterminate refusal
                # below and by then `item["status"]` no longer says the item was `integration-blocked`.
                # The pass selects on durable lane facts plus this recorded prior disposition, and
                # E-04's hold-back restores exactly this value rather than inventing one.
                item["requeue_from_status"] = item["status"]
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

    # integpath-04 (`rl67b0`) E-03/E-04, symmetric with `oc_runipd.run_queue` (CID-3): MERGE
    # ALREADY-VERIFIED LANES INSTEAD OF RE-DISPATCHING THEM.
    #
    # PLACEMENT, stated exactly because it is the substance: AFTER the indeterminate refusal above (that
    # refusal `return 1`s before anything starts, and main must not be mutated during a resume the
    # driver is about to decline) and BEFORE the dispatch loop below (once an item is dispatched its
    # lane has already been attempt-scoped into a second branch and the finished one abandoned). The
    # requeue above dispatches nothing, so this is still strictly before any turn; what it does mean is
    # that the pass selects on durable lane facts and `requeue_from_status`, not on `status`.
    #
    # No second lock (this is inside `locked_run` already), no flag, and it cannot abort the resume.
    #
    # NO STATE RELOAD AND NO `register_signal_report` REFRESH HERE, for the reason the oc twin records:
    # the pass mutates THIS `state` dict and persists it, so the in-memory view is already current and
    # the published reporter reference is the same object; a reload would also add a sixth
    # `register_signal_report` site to a function whose five are pinned as a measured invariant.
    _integrate_stranded_lanes(run_dir, state)

    tracker = StreamTracker()
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
        # integpath-03 (`51vw4y`) E-03: RUNG 1, the exact counterpart of the `oc_runipd` site. Re-attempt
        # every DEFERRED integration at the top of the loop, where it costs nothing: the loop already
        # reloads state and already cascades, so the previous item's completion IS the retry trigger.
        # Ordered AFTER the cascade for the same reason as on the oc host: `integration-deferred` is not
        # terminal, so the cascade spares a deferred item's dependents, and an integration landing here
        # promotes the item BEFORE selection asks what depends on it.
        if runner_shared.deferred_integration_items(state):
            retry_deferred_integrations(run_dir, state)
            save_state(run_dir, state)
            state = load_state(run_dir)
            # rununify Order 08 (`ty3cj6`) E-03: REFRESH the shutdown reporter's published
            # reference, because the line above REBOUND `state` to a fresh dict. Without this, a
            # SIGINT arriving after a deferred integration re-attempt reports the PRE-reload
            # snapshot: the item shows as still `integration-deferred` when it has in fact just
            # integrated. `oc_runipd`'s counterpart has always had this call (`oc_runipd.py:8766`)
            # and states the invariant in its own comment at `oc_runipd.py:8645`: "called again
            # after each state reload so the report never runs off a stale snapshot". This host
            # omitted it at BOTH ladder reload points; that omission was a DEFECT, not a host
            # difference, and no test covered it.
            register_signal_report(run_dir, state)
        queued = [item for item in state["queue"] if item["status"] == "queued"]
        if not queued and not runner_shared.deferred_integration_items(state):
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
            # integpath-03 (`51vw4y`) E-04/E-05: RUNGS 2 AND 3, the exact counterpart of the `oc_runipd`
            # site, with `runnable is None` as the trigger because that condition already means "there
            # is nothing else I could dispatch instead" - covering both the last-item case and the
            # all-deferred case a last-item test would miss. The bounded poll and the timeout-bounded,
            # TTY-suppressed ask are the SHARED ladder's; `ask=True` is safe unconditionally because it
            # resolves `is_interactive_run` itself. Per OQ-03 any item still deferred afterwards is
            # resolved to terminal with its lane preserved: a run must not end on a non-disposition.
            if runner_shared.deferred_integration_items(state):
                retry_deferred_integrations(run_dir, state, poll=True, ask=True)
                save_state(run_dir, state)
                state = load_state(run_dir)
                # rununify Order 08 (`ty3cj6`) E-03: the SECOND of the two ladder reloads this host
                # was missing, matching `oc_runipd.py:8834`. Rungs 2/3 can BLOCK for a long time (a
                # bounded poll plus a timeout-bounded ask), so this is precisely the window in which
                # an operator is most likely to interrupt, and reporting a pre-reload snapshot here
                # would describe the run as it was before the poll rather than as it is.
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
                    continue
            # depblock 01 (`akzy45`) E-02/E-04: CLASSIFY BEFORE LABELLING, through the SAME shared
            # predicate `oc_runipd`'s counterpart arm calls. This host owns its own `run_queue` and so
            # its own copy of this loop, which is exactly why the classification itself must live in
            # `runner_shared`: a fix to the rule reaches both hosts, and neither can quietly re-fork it.
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
                    # WRITE NO STATUS: the item stays `queued` for the next invocation, and the record
                    # plus event keep it from exiting the run silently statusless.
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
                        # depblock 01 (`akzy45`): the classification that justified the terminal label.
                        "block_class": verdict.verdict,
                        "block_detail": verdict.detail,
                    },
                )
            save_state(run_dir, state)
            break

        recovery = bool(runnable.pop("recovery_next", False))
        update_execution_order(state, runnable)
        # orchretire-03 (`pgq326`) E-07: THE DISPATCH BRANCH THAT ACTS ON `orchestrate`, which sharing the
        # DECIDER (E-04) does not accomplish on its own. Verified at HEAD `844d195c`: the token
        # `orchestrate` appeared nowhere in this module outside the unrelated `orchestrate_isolation`
        # import, `execute_item` derived only `is_review = action == "review"`, and this loop called
        # `execute_item` UNCONDITIONALLY. So without this branch `aw agy run` spends a full agent turn
        # AUTHORING against an approved orchestrator whose coordination role the runner has superseded --
        # and every object-identity parity test on the decider still PASSES, because the decider was never
        # the missing piece. Proven by sabotage: removing this branch fails the agy dispatch tests while
        # the decider-identity assertion keeps passing.
        #
        # The OUTCOME is the SAME shared function `oc_runipd` calls, never a second copy: `pgq326`'s gate
        # forbids forking the retire/reconsider/terminate logic into this module, and the anti-re-fork
        # discipline `2r306y`/`818uru` established is what makes a fix to it reach both hosts.
        if runnable.get("action") == "orchestrate":
            dispatch_orchestrator_item(
                Path(state["repo"]),
                run_dir,
                state,
                runnable,
                actor=driver_actor(state),
                terminal_states=TERMINAL_STATES,
                success_states=EXECUTION_SUCCESS_STATES,
            )
            save_state(run_dir, state)
            continue
        # runstop 1qxuke: the set now in flight, recorded BEFORE the turn so a stop requested during
        # it is observed at the next checkpoint with this set already captured.
        current_setid = runnable.get("setid")
        try:
            execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)
        except ToolIdentityError:
            # lanetruth Order 01 (af7i6p) E-04 / OQ-02: RUN-FATAL. Must precede the item-local
            # `except DriverError` (ToolIdentityError subclasses it), or the abort would be
            # downgraded to one item marked `failed-safely` while later items ran under the same
            # wrong tooling. Mirrors oc_runipd.
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
    # dirtygates Order 05 (`ajxr5d`) E-11/E-06: RETIRE THE REVIEW SWEEP LANE, once, HERE - the mirror of
    # the oc twin. Coordinator-owned because ONE tree serves every review of the run, so a per-item
    # teardown would destroy the lane the next review needs; and this also closes the gap finding F-12
    # measured, that `teardown_isolation_worktree`'s sole call site per host is gated on
    # `driver_finalize`'s return code, which a review never produces. It CLASSIFIES BEFORE DESTROYING
    # through the shared spec-R5.5 gate, so a stranded review's lane is PRESERVED with its work.
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
            driver_label="antigravity",
        )
    )
    # runnoop Order 02 (`m85gxh`) E-03: THE PER-ARTIFACT DISPOSITION LINE, the exact mirror of the oc
    # twin. The REASON is the deliverable, not the line: the summary table above already renders one
    # row per matched artifact with its disposition (including a zero-attempt item), and carries no
    # explanation of what that disposition MEANS. Emitted in ONE CLOSING PASS over the queue, which is
    # what makes "exactly one line per matched artifact" structural and what covers the artifact that
    # is never dispatched and therefore has no termination point. The wording and the reason vocabulary
    # come from the pure `run_selection_policy` module (imported DIRECTLY by this host, never through
    # `oc_runipd`), and `refusal_of_item` is `orchprobe` `r2i1b1`'s ONE reader. See the longer note at
    # the oc call site for the measurement and for why only this exit path carries the block.
    for _disposition_line in render_queue_dispositions(
        state.get("queue", []), refusal_reader=refusal_of_item
    ):
        print(_disposition_line)
    # specvis st5klo E-03: the PRIMARY end-of-run site for this host, from the SAME shared
    # `report_run_spec_edits` the OpenCode driver calls. The report's computation and wording are
    # defined once (in `oc_runipd`/`render_stream`); only the SITE is per-driver.
    report_run_spec_edits(state)
    # runnoop Order 03 (`bsc457`) E-03: THE CLOSING DISPOSITION SUMMARY, the exact mirror of the oc
    # twin and printed UNCONDITIONALLY, including for a run that acted on nothing - the case that
    # previously closed with a sentence reading as a failed launch beneath a table saying COMPLETED.
    # Unconditional follows `announce_run_order`'s established precedent; the block sits at the END and
    # is self-contained (this plan's OQ-01) because readers pipe runner output through `tail`. Placed
    # BEFORE the continuity footer, since that footer is session plumbing rather than the answer to
    # "what did this run do?". The wording and the remedy table come from the pure
    # `run_selection_policy` module, imported DIRECTLY by this host, and `refusal_of_item` is
    # `orchprobe` `r2i1b1`'s ONE reader, so a recorded refusal's own remedy is SOURCED, not copied.
    for _summary_line in render_disposition_summary(
        state.get("queue", []), refusal_reader=refusal_of_item
    ):
        print(_summary_line)
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
    #
    # runnoop zz5yxq (E-02): the SAME action-aware bar as `oc_runipd`, through the SAME shared
    # projection, so the two hosts cannot disagree about whether a run succeeded. See the longer note
    # at the OpenCode site and the call-site classification at `runner_shared.SUCCESS_STATES`: a
    # `reviewed`-but-unapproved EXECUTE item is never dispatched and must not exit 0, while a
    # `reviewed` REVIEW item still must. No status is rewritten and `queued` passes through verbatim.
    return runner_stop.deliberate_stop_exit_code(
        runner_shared.exit_code_statuses(state["queue"]),
        success_states={runner_shared.EXIT_SUCCESS_TOKEN},
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


# rununify 04 (`tx6q0h`): one-line wrappers over the shared definitions. This host's THREE argv
# subcommand spellings (`run`, `runipd`, `runagy`) are DATA in `AGY_HOST_LABELS`, so none is lost.
def _detect_driver_command() -> str:
    return runner_shared.detect_driver_command(labels=runner_shared.AGY_HOST_LABELS)


def render_continuation_hint(
    state: dict[str, Any],
    run_dir: Path,
    driver_cmd: str | None = None,
) -> str:
    return runner_shared.render_continuation_hint(
        state, run_dir, driver_cmd, labels=runner_shared.AGY_HOST_LABELS
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
        help="Stream the child agent's raw JSON events verbatim",
    )
    sub_parser.set_defaults(output_mode="clean")
    # streamfmt (mm6wuz) E-06: the MIRROR of the oc twin, so `aw agy run -v` and `aw oc run -v` parse
    # identically. Outside the mutually exclusive group for the same reason: `--raw`/`--quiet` choose
    # WHICH renderer runs, `-v` tunes how much the `clean` renderer shows. `verbosity_default` is `0`
    # on `start` and `None` on `resume`, so an omitted flag on resume leaves the frozen tier alone.
    sub_parser.add_argument(
        "-v",
        "--verbose",
        dest="verbosity",
        action="count",
        default=verbosity_default,
        help="Increase live stream detail: -v also shows reads and searches, -vv also shows raw "
        "tool parameters. Ignored under --raw/--quiet.",
    )


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
  - reviews:  Every IPD whose next legal action is review, swept in one shared session
              and one shared isolated worktree (so the sweep never writes to the shared
              checkout; each review lands as one merge).
              Spelled 'reviews', 'review', or 'to-review'. Selects IPDs only; specs and
              backlog items are not reachable by any selector yet. Matching nothing is a
              success and exits 0, because a repository with nothing awaiting review is
              the healthy state. 'aw agy review' is the spelled form of this sweep.
              A COMPLETE 'draft' is in this sweep only with --allow-drafts (the draft
              admission gate); an INCOMPLETE draft is never admitted, by any flag.
  - all:      All actionable pending IPDs in the repository

EXAMPLE, the review sweep (the most frequent invocation):
  runagy reviews

AUTOMATIC STATUS ROUTING:
  - to-review: Runs Antigravity with `/plan-review <plan_path>`.
  - approved:  Executes the plan step-by-step according to the execution runbook,
               followed by independent verification in a clean session.
""",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    # stopdisc (`wqq8ua`) E-04: the mirror of the oc twin, which carries the full note. The run-level
    # help named no way to stop a run; this POINTS AT the shared `stop` verb instead of restating its
    # per-level help (P8), and the text is `runner_stop`'s so both hosts say the same thing.
    _stopping_note = runner_stop.stop_run_help_note(_detect_driver_command())

    # start
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
        help="Target plan selectors: ID6, Set ID, IPD filename, 'reviews' (alias "
        "'review'/'to-review'; every IPD whose next legal action is review, IPDs only), "
        "or 'all'",
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
    # hostdefault-02 (`ybkmzp`) E-02: the TRI-STATE surface, so this host can express "let the
    # stored per-model choice decide" as well as "verify" / "do not verify". `default=None` is the
    # load-bearing part: it is what distinguishes SILENCE (fall through to the profile store) from
    # an explicit `--no-validate`, and it matches oc's `resume` parser, which already ships
    # `default=None` for exactly this reason.
    #
    # REGISTERED BARE, WITH NO ALIASES, DELIBERATELY. oc spells this flag
    # `("--validate", "--verify", "--audit")`, and `BooleanOptionalAction` auto-generates a `--no-X`
    # for EVERY option string, so copying that alias list here would also generate `--no-verify` and
    # `--no-audit`, which THIS parser already declares directly above. Measured: that raises
    # `argparse.ArgumentError: conflicting option strings: --no-verify, --no-audit` at
    # `build_parser()` time, killing every `aw agy` invocation. `conflict_handler="resolve"` is
    # worse, not a fix: the new action would silently STEAL `--no-verify`/`--no-audit`, after which
    # `args.no_verify` does not exist at all and the freeze site below reads `False`
    # unconditionally, i.e. verification silently OFF by default on the host whose whole posture is
    # verification ON.
    start.add_argument(
        "--validate",
        dest="validate",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Run (or skip) the turn-2 independent clean-session verification. Omit to use the "
        "runner-profile store's per-model choice, which on this host defaults to verifying. "
        "`--no-verify` remains an accepted alias for `--no-validate`",
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
    # revsweep 76gsmv E-03: the flag `aw agy review` expands to (spec 25kzda 2.1). It NARROWS, never
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
        "implemented. This is what 'aw agy review' expands to.",
    )
    start.add_argument(
        "--stall-timeout",
        type=float,
        default=DEFAULT_STALL_TIMEOUT,
        help=f"Timeout in seconds with no output from child agent before terminating (default: {DEFAULT_STALL_TIMEOUT}; 0 to disable)",
    )
    # runflags-01 (`uyeko5`) E-01..E-07: spec `25kzda` 2.1's EIGHT policy flags, from the SHARED table.
    # E-07 (maintainer ruling 2026-09-04) NORMALIZES `--full-auto` to default `False` here: this host
    # declared `default=True`, so `aw agy run <selector>` auto-cleared a `reviewed` plan with an
    # approving `- Readiness:` and executed it with NO flag passed, while the opencode host required
    # opting IN. Two hosts disagreeing about whether execution is opt-in or opt-out is the divergence
    # the `rununify` Set exists to remove, and this one defaulted to the LESS safe direction.
    runner_shared.register_run_policy_flags(start)
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
        # stopdisc (`wqq8ua`) E-04 / DECISION 03-wqq8ua-D3: `RawDescriptionHelpFormatter` ADDED here,
        # the mirror of the oc twin. `start` above always had it; `resume` did not, and argparse's
        # default formatter reflows a description, so the stopping paragraph would collapse onto one
        # line with its indented command inlined. Behavior-neutral for parsing.
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
    # runflags-01 (`uyeko5`) E-06: the same eight flags on `resume`, all `default=None` (the shipped
    # `--full-auto` pattern), so an OMITTED flag cannot clobber the frozen value. The opencode twin
    # carries the full note.
    runner_shared.register_run_policy_flags(resume, resume=True)
    resume.add_argument(
        "--max-items-per-session",
        type=int,
        default=None,
        metavar="N",
        help="Override maximum consecutive non-isolated turns per session before starting a fresh session",
    )
    _add_output_mode_flags(resume, verbosity_default=None)

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

    # integpath-04 (`rl67b0`) E-02: the OUT-OF-BAND `integrate` verb, through the SHARED declaration
    # so `aw agy run integrate` is the SAME verb as `aw oc run integrate` (orchestrator CID-3) rather
    # than a second copy that could drift. Declared on THIS parser (where `start` lives), not on
    # `cli.py`'s `agy` group, which forwards `argparse.REMAINDER` verbatim to this `main`.
    runner_shared.add_integrate_parser(sub, command=_detect_driver_command())

    # reverify-01 (`mp289j`) E-05: the OUT-OF-BAND `audit` verb, DECLARED here through the same shared
    # helper so the two hosts keep registering the same subparser set (pinned by
    # `tests/test_rununify_build_parser.py`), and so `aw agy run audit --help` documents the verb
    # rather than reporting it does not exist.
    #
    # DECLARED ON BOTH HOSTS, IMPLEMENTED ON ONE, DELIBERATELY. Plan `mp289j` excludes wiring a second
    # host launch path ("a second host surface doubles the review burden for a verb whose value is
    # conditional"), so THIS host's binding REFUSES with a message naming the OpenCode spelling. That
    # is the honest shape: the verb is visible and self-documenting on both hosts, and the one place it
    # is not implemented says so out loud instead of half-running.
    runner_shared.add_audit_parser(sub, command=_detect_driver_command())

    # hostdefault-02 (`ybkmzp`) E-02: prove the two verification spellings did not collide while this
    # parser was being built. Checked HERE because the hazard is a property of the registration
    # (a `--validate` alias list, or `conflict_handler="resolve"`, can silently steal `--no-verify`
    # and change what it means), and this is the only point at which that is decidable.
    assert_verification_flags_are_distinct(start)

    return parser


def handle_integrate_command(args: argparse.Namespace) -> int:
    """Execute the `integrate` verb: re-attempt integration for one verified lane, NO agent turn.

    integpath-04 (`rl67b0`) E-02, the exact counterpart of `oc_runipd.handle_integrate_command`. THIN
    by contract: the whole decision (lane resolution from durable state, every refusal, the real
    validation runner, the gate call) is `runner_shared.reintegrate_lane`. This binds only what is
    host-specific - THIS host's `integrate_lane_branch` wrapper, so a recovered merge subject reads
    `integrate(aw agy run): ...` rather than the other driver's name, and this host's bound
    `run_suite_check`, which the shared module may not import.

    EXIT CONTRACT: 0 integrated, 1 refused (nothing merged, main untouched, lane preserved), 2 on a
    driver error.
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
    """Refuse the `audit` verb on THIS host, naming the spelling that works. reverify-01 (`mp289j`).

    NOT A STUB TO BE FILLED IN CASUALLY, and not an oversight. Plan `mp289j` excludes wiring the
    Antigravity host unless the decision requires it, and it does not: the verb buys ONE independent
    opinion, so having it on one host is the whole product, while a second launch path doubles the
    review burden for a surface whose value the plan itself calls conditional. The drivers are also
    mid-unification (`rununify`/`5e4sb6`), so a host-local copy of the launch logic is exactly the fork
    that backlog is open to remove.

    IT REFUSES LOUDLY RATHER THAN HALF-RUNNING, and the alternative is worse than it looks: with no
    binding at all, the shared declaration would parse `audit <id6>` successfully and then fall through
    to the "Unknown command" path, telling the operator the verb does not exist while `--help`
    documents it. Naming the working spelling is the difference between a dead end and a redirect.

    EXIT CONTRACT: 2, which is this driver's code for "cannot run", not 1 ("refused after checking"):
    nothing about the request was evaluated, so claiming a considered refusal would be a lie.
    """

    id6 = str(getattr(args, "id6", "") or "<id6>")
    print(
        "audit is not implemented on the Antigravity host. The verb buys ONE independent opinion, so "
        "it is wired on one host deliberately (plan `mp289j`) rather than duplicated while the two "
        "drivers are still being unified.\n"
        f"Run it on the OpenCode host instead:\n  aw oc run audit {id6}",
        file=sys.stderr,
    )
    return 2


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
    #
    # streamfmt (mm6wuz) E-06 / OQ-02 (resolved): `"-v"` and `"--version"` USED TO BE LISTED HERE and
    # were REMOVED, in lockstep with the oc twin. `-v` now means `--verbose`, and while it sat in this
    # set a LEADING `-v` was treated as a subcommand and never prefixed with `start`. The removed
    # `--version` entry guarded a flag NEITHER driver registers. THE TWO DRIVERS' SETS MUST STAY
    # IDENTICAL: `tests/test_runner_stop_triggers.py` regexes `subcommands = \{(.*?)\}` out of BOTH
    # source files, so a one-sided edit here is exactly the divergence that guard exists to catch.
    # integpath-04 (`rl67b0`) E-02: `"integrate"` MUST be listed here for the SAME reason `stop` must -
    # an unregistered first token becomes `start <token>`, so `integrate <id6>` would LAUNCH A RUN with
    # `integrate` as a selector. Added in lockstep with the oc twin and with the inline copy in
    # `tests/test_runner_stop_triggers.py`, which pins all three equal.
    # reverify-01 (`mp289j`) E-05: `"audit"` MUST be listed here for the SAME measured reason `stop` and
    # `integrate` must, and it must match the oc copy token for token (a test pins the two sets against
    # each other). An unregistered first token is rewritten into `start <token>`, so `audit <id6>` would
    # LAUNCH A RUN with `audit` as a selector.
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
        if args.command == "integrate":
            # integpath-04 (`rl67b0`) E-02: out-of-band like `stop`, before any run-lock or state
            # mutation. No run directory, no agent turn; it refuses a lane a LIVE process owns exactly
            # because it holds no run lock.
            return handle_integrate_command(args)
        if args.command == "audit":
            # reverify-01 (`mp289j`) E-05: declared on both hosts, implemented on OpenCode only. This
            # binding refuses and names the working spelling; see `handle_audit_command`.
            return handle_audit_command(args)
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
        # streamfmt (mm6wuz) E-06: `None` on `resume` when the flag was omitted, so an omitted `-v`
        # does not clobber the frozen tier.
        verbosity = getattr(args, "verbosity", None)

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
            # runflags-01 (`uyeko5`) E-06, symmetric with `oc_runipd`: refuse the flag spec `:131`
            # freezes (`--retry-budget`) before any state is loaded, then apply the flags the operator
            # actually PASSED while leaving the omitted ones frozen. The shared helper SUBSUMES the
            # hand-written `--full-auto` block that was here, preserving its shipped
            # overwrite-when-passed behavior exactly.
            runner_shared.refuse_frozen_flags_on_resume(args)
            state = load_state(run_dir)
            if runner_shared.apply_run_policy_flags_on_resume(state, args):
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
                            driver_label="antigravity",
                        )
                    )
                    # specvis st5klo E-03: interrupt/SIGTERM path, wired and LABELLED
                    # possibly-incomplete (OQ-01), symmetric with `oc_runipd`.
                    report_run_spec_edits(state, partial=True)
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
        # stopdisc (`wqq8ua`) E-03: the exact counterpart of the oc twin, which carries the full note.
        # In brief: this is where an operator learns what just happened and it named no gentler option;
        # the sentence sits AFTER the branch because it is true on both exits and leaves each existing
        # message byte-identical; it is future-tense because this handler cannot know which R12 path or
        # ladder rung produced the exit; and it is NOT a prompt, because Ctrl-C is taken by an operator
        # who wants out. The text itself is `runner_stop`'s, so both hosts say the same thing.
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
        # `expand_selectors`, which runs before the run directory is made.
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
                            driver_label="antigravity",
                        )
                    )
                    # specvis st5klo E-03: the DriverError path, wired and labelled (OQ-01).
                    report_run_spec_edits(state, partial=True)
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
