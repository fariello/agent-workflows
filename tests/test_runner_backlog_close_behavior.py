"""Behavioral tests for runner backlog-close behavior and shutdown reporting.

Triage of all 58 tests from deleted `tests/test_runner_backlog_close.py` (commit `19313eed7^`):

| Deleted Test | Property | Verdict | Evidence |
|---|---|---|---|
| `ReadsTheFromBacklogLink::test_both_drivers_read_the_link_into_the_plan_record` | Drivers parse_plan_file reads - From-Backlog: <id6> into PlanRecord.from_backlog and returns None when absent | UNGUARDED-CANDIDATE | Symbol search confirmed no live test in tests/ calls parse_plan_file and asserts from_backlog |
| `ReadsTheFromBacklogLink::test_the_link_is_frozen_on_the_queue_entry` | build_dynamic_manifest preserves from_backlog for linked plans and None for unlinked plans | UNGUARDED-CANDIDATE | tests/test_typed_queue_entries.py calls build_dynamic_manifest but asserts only selection paths and conflicts, not from_backlog |
| `ReadsTheFromBacklogLink::test_the_link_is_frozen_into_run_state_by_a_REAL_run` | initialize_run with --prepare-only freezes from_backlog onto state.json queue entries | UNGUARDED-CANDIDATE | No live test runs initialize_run and verifies from_backlog in state.json queue |
| `ReadsTheFromBacklogLink::test_absent_and_placeholder_values_mean_no_linked_item` | Placeholder values (-, none, unresolved, empty) in From-Backlog parse as None | UNGUARDED-CANDIDATE | tests/test_check_engine_release_gate.py only tests sentinels in check_release_gates, empty string and driver re-export unguarded |
| `ReadsTheFromBacklogLink::test_no_new_regex_the_field_name_comes_from_the_schema` | _read_from_backlog uses ipd_schema.META_FROM_BACKLOG rather than a hardcoded string | PIN | Pins constant string self.assertEqual(ipd_schema.META_FROM_BACKLOG, "From-Backlog") and monkeypatches internal module constant |
| `ClosingRules::test_single_ipd_carrier_closes_when_its_plan_executes` | Single executed IPD carrier produces verdict.close True with rule CARRIER_KIND_IPD | COVERED | tests/test_outer_close_spec_carrier.py::TestOuterCloseSpecCarrier::test_case_3_ipd_only_executed_plan_allows line 103: self.assertTrue(verdict.close); self.assertEqual(verdict.rule, CARRIER_KIND_IPD) |
| `ClosingRules::test_two_carrier_item_does_not_close_when_only_one_executed` | Item with two carriers where only one executed refuses close (verdict.close False) | UNGUARDED-CANDIDATE | tests/test_outer_close_spec_carrier.py tests single-plan and mixed plan+spec, not two-IPD carriers in evaluate_backlog_close |
| `ClosingRules::test_two_carrier_item_closes_when_both_executed` | Item with two carriers where both executed allows close (verdict.close True) | UNGUARDED-CANDIDATE | No live test in tests/ passes two executed IPD carriers to evaluate_backlog_close |
| `ClosingRules::test_spec_only_item_closes_on_existence_even_while_unapproved` | Spec-only item closes on existence even while draft (rule CARRIER_KIND_OTHER) | COVERED | tests/test_outer_close_spec_carrier.py::TestOuterCloseSpecCarrier::test_case_4_spec_only_draft_spec_allows line 126: self.assertTrue(verdict.close); self.assertEqual(verdict.rule, CARRIER_KIND_OTHER) |
| `ClosingRules::test_spec_status_is_never_consulted` | All spec review statuses produce identical close verdicts for spec-only items | UNGUARDED-CANDIDATE | tests/test_outer_close_spec_carrier.py tests only draft spec for spec-only; review-arc status invariance is not asserted across all 5 statuses |
| `ClosingRules::test_mixed_spec_plus_ipd_does_not_close_until_the_ipd_executes` | Mixed spec plus pending IPD refuses close even when spec exists | COVERED | tests/test_outer_close_spec_carrier.py::TestOuterCloseSpecCarrier::test_case_5_mixed_unexecuted_plan_and_unimplemented_spec_refuses_both line 157: self.assertFalse(verdict.close) |
| `ClosingRules::test_item_with_no_carriers_is_not_closed` | Item with no carriers produces verdict.close False with reason mentioning no carrier | UNGUARDED-CANDIDATE | No live test in tests/ calls evaluate_backlog_close with zero carriers |
| `ClosingRules::test_an_already_done_item_is_left_alone` | Item already in done/ produces verdict.close False with reason already done | UNGUARDED-CANDIDATE | No live test in tests/ calls evaluate_backlog_close for an item already in done/ |
| `ClosingRules::test_the_shared_lookup_is_reused_not_reimplemented` | Carrier set is queried from check_engine.find_from_backlog_artifacts with no duplicate scan | PIN | Asserts internal mock caller count self.assertEqual(len(calls), 1) |
| `EarnedCloseGate::test_a_run_that_executed_no_carrier_closes_nothing` | Empty earned_paths refuses close with reason mentioning not earned / executed none of its carriers | COVERED | tests/test_outer_close_spec_carrier.py::TestOuterCloseSpecCarrier::test_case_6_mixed_all_terminal_empty_earned_paths_refuses line 184: self.assertFalse(verdict.close); self.assertIn("this run executed none of its carriers", verdict.reason) |
| `EarnedCloseGate::test_the_gate_applies_to_the_non_ipd_rule_too` | Spec-only item with empty earned_paths refuses close | UNGUARDED-CANDIDATE | tests/test_outer_close_spec_carrier.py Case 6 uses a mixed plan+spec fixture, not spec-only with empty earned_paths |
| `EarnedCloseGate::test_an_induced_lookup_failure_leaves_the_item_untouched` | Exception raised by find_from_backlog_artifacts fails closed with item file untouched | UNGUARDED-CANDIDATE | No live test in tests/ mocks carrier lookup failure in evaluate_backlog_close |
| `EarnedCloseGate::test_an_induced_terminal_state_read_failure_fails_closed` | Exception raised by plan_terminal_state fails closed | UNGUARDED-CANDIDATE | No live test in tests/ mocks plan_terminal_state failure in evaluate_backlog_close |
| `EarnedCloseGate::test_an_induced_setter_failure_leaves_the_item_untouched_with_a_reason` | Setter failure return code leaves item untouched and records reason in backlog_close | UNGUARDED-CANDIDATE | No live test in tests/ asserts process_backlog_close behavior when close_backlog_item returns nonzero |
| `UsesTheGatedSetter::test_the_close_uses_the_status_form_which_runs_the_release_gate_predicate` | close_backlog_item invokes the setter with --status done to run the release gate | COVERED | tests/test_backlog_set_adapter.py::BacklogSetAdapterTests::test_runner_shared_close_backlog_item_end_to_end lines 135-144 executes close_backlog_item against live backlog set CLI, asserting rc 0 and file moved to done/ |
| `UsesTheGatedSetter::test_the_item_file_is_never_edited_directly` | process_backlog_close does not edit or move item file directly when setter is a no-op | UNGUARDED-CANDIDATE | No live test stubs close_backlog_item and compares before/after item file bytes |
| `UsesTheGatedSetter::test_the_commit_is_path_scoped_to_this_item_only` | commit_backlog_close stages only paths carrying item id6 across done and graduated | UNGUARDED-CANDIDATE | No live test asserts path scoping arguments of commit_backlog_close in isolation |
| `ClosesEndToEnd::test_a_real_close_moves_the_item_to_done_with_evidence` | process_backlog_close moves item to done/ preserving Blocks-Release and records evidence | UNGUARDED-CANDIDATE | No live test drives process_backlog_close end-to-end with real file moves and checks file content |
| `ClosesEndToEnd::test_the_move_is_committed_path_scoped_and_leaves_the_tree_clean` | Backlog item move is committed path-scoped, leaving git status clean | UNGUARDED-CANDIDATE | No live test asserts git status --porcelain clean and git show --name-only after process_backlog_close |
| `ClosesEndToEnd::test_a_coworkers_other_backlog_item_is_never_swept_in` | Concurrent uncommitted edit to another backlog item is not committed or reverted | UNGUARDED-CANDIDATE | No live test tests concurrent uncommitted backlog edits during process_backlog_close |
| `ClosesEndToEnd::test_the_close_is_recorded_in_the_run_ledger` | process_backlog_close appends backlog-item-closed event to events.jsonl | UNGUARDED-CANDIDATE | No live test verifies events.jsonl contains backlog-item-closed |
| `UnclosedReport::test_each_open_item_is_listed_with_its_reason` | unclosed_backlog_items and render_unclosed_report list each open item with its reason | UNGUARDED-CANDIDATE | Symbol search confirmed no live test asserts on output of unclosed_backlog_items or render_unclosed_report |
| `UnclosedReport::test_a_run_with_nothing_outstanding_prints_no_section` | Run state with all items closed produces empty list and empty string from report renderers | UNGUARDED-CANDIDATE | No live test in tests/ asserts empty unclosed report output |
| `UnclosedReport::test_an_item_whose_plan_never_reached_the_close_is_still_reported` | Queue item without backlog_close records plan status as reason | UNGUARDED-CANDIDATE | No live test exercises unclosed_backlog_items on unclosed/partial queue entries |
| `UnclosedReport::test_a_plan_with_no_linked_item_contributes_nothing` | Queue item without from_backlog is omitted from unclosed report | UNGUARDED-CANDIDATE | No live test exercises unclosed_backlog_items on unlinked queue entries |
| `UnclosedReport::test_the_ledger_record_is_written_before_the_print` | backlog-items-left-open ledger record is written before terminal print | UNGUARDED-CANDIDATE | No live test asserts ledger write ordering relative to print |
| `UnclosedReport::test_the_ledger_record_survives_when_the_print_is_discarded` | Ledger record is written even when stdout/stderr printing raises an exception | UNGUARDED-CANDIDATE | No live test tests emit_shutdown_report under broken print streams |
| `UnclosedReport::test_the_report_is_idempotent_under_a_repeated_signal` | Repeated emit_shutdown_report calls emit output and ledger records only once | UNGUARDED-CANDIDATE | No live test exercises repeated emit_shutdown_report calls |
| `UnclosedReport::test_the_pointer_names_the_real_run_id_and_the_real_verb` | render_runs_pointer outputs command with real run ID and CLI verb | UNGUARDED-CANDIDATE | No live test asserts format of render_runs_pointer |
| `UnclosedReport::test_the_pointer_names_a_verb_the_CLI_really_has` | Pointer verb aw runs is an actual CLI command that exits 0 with --help | UNGUARDED-CANDIDATE | No live test verifies aw runs exists via CLI help invocation |
| `UnclosedReport::test_json_output_suppresses_the_pointer_and_stays_PARSEABLE` | Driver main with --json emits valid JSON stdout and suppresses runs pointer | UNGUARDED-CANDIDATE | No live test verifies driver main --json output suppression of pointer |
| `ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` | Subprocess receiving SIGINT exits 130 and emits shutdown report to stderr | UNGUARDED-CANDIDATE | tests/test_runner_stop_triggers_e2e.py tests stop level 3, not SIGINT exit 130 and shutdown report |
| `ShutdownReportOnInterrupt::test_sigterm_produces_the_report_and_exits_143` | Subprocess receiving SIGTERM exits 143 and emits shutdown report to stderr | UNGUARDED-CANDIDATE | No live test asserts exit 143 and shutdown report on SIGTERM |
| `ShutdownReportOnInterrupt::test_the_sigterm_funnel_is_wired_in_both_drivers_main` | Driver main installs a Python callable SIGTERM handler | UNGUARDED-CANDIDATE | No live test in tests/ asserts signal.getsignal(signal.SIGTERM) after main runs |
| `ShutdownReportOnInterrupt::test_both_drivers_report_from_their_keyboardinterrupt_funnel` | KeyboardInterrupt raised during run_queue funnels to stderr with exit 130 in both drivers | UNGUARDED-CANDIDATE | No live test asserts KeyboardInterrupt funnel behavior in driver main |
| `ShutdownReportOnInterrupt::test_the_callable_is_handler_safe` | signal_report_callback does not acquire run_lock, locked_run, or save_state | UNGUARDED-CANDIDATE | No live test in tests/ traps run_lock/locked_run/save_state during signal_report_callback |
| `ShutdownReportOnInterrupt::test_the_child_kill_escalation_path_is_unchanged` | terminate_process reads grace constants at call time and stays separate from shutdown report | UNGUARDED-CANDIDATE | tests/test_oc_runipd.py::ChildTerminationTests covers oc_runipd grace constants only, not agy_runipd and not shutdown report separation |
| `SharedNotCopied::test_both_drivers_expose_the_backlog_close_api` | Both driver modules expose the backlog close API attributes | DELEGATION-COVERED | tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation covers BACKLOG_CLOSE_WRAPPERS and ELEVEN_REEXPORTS |
| `SharedNotCopied::test_the_implementation_is_shared_not_copied` | Re-exported symbols are identical objects across drivers | DELEGATION-COVERED | tests/test_runner_delegation_and_host_independence.py::TestRunnerBacklogCloseDelegation::test_delegation_reexport_single_implementation_identity line 233: assert oc_sym is agy_sym is shared_sym |
| `SharedNotCopied::test_both_drivers_call_the_close_from_their_finalize_success_branch` | Both drivers call process_backlog_close from execute_item on finalize success | UNGUARDED-CANDIDATE | No live test in tests/ asserts execute_item calls process_backlog_close for both drivers |
| `SharedNotCopied::test_both_drivers_emit_the_shutdown_report_on_normal_exit` | Both drivers emit shutdown report on normal exit of run_queue | UNGUARDED-CANDIDATE | No live test in tests/ asserts run_queue emits shutdown report on normal exit |
| `SharedNotCopied::test_an_interrupt_BEFORE_the_first_turn_still_reports` | Interrupt before first turn in run_queue still publishes state and reports unclosed items | UNGUARDED-CANDIDATE | No live test in tests/ tests pre-first-turn interrupt reporting |
| `BacklogCloseIntegritySelfCheck::test_a_single_claimant_is_the_healthy_case` | backlog_item_paths_for_id returns single path when exactly one file claims ID | UNGUARDED-CANDIDATE | Symbol search confirmed backlog_item_paths_for_id has zero live test callers in tests/ |
| `BacklogCloseIntegritySelfCheck::test_two_claimants_are_detected_which_is_the_36_item_corruption` | backlog_item_paths_for_id returns both paths when item exists in graduated/ and done/ | UNGUARDED-CANDIDATE | No live test in tests/ calls backlog_item_paths_for_id |
| `BacklogCloseIntegritySelfCheck::test_an_absent_id_is_empty_not_an_error` | backlog_item_paths_for_id returns empty list for unclaimed ID | UNGUARDED-CANDIDATE | No live test in tests/ calls backlog_item_paths_for_id |
| `BacklogCloseIntegritySelfCheck::test_paths_are_repository_relative_so_no_home_path_can_leak` | backlog_item_paths_for_id returns repo-relative paths | UNGUARDED-CANDIDATE | No live test in tests/ calls backlog_item_paths_for_id |
| `BacklogCloseIntegritySelfCheck::test_both_drivers_share_ONE_implementation` | backlog_item_paths_for_id is identical object in both drivers | PIN | Asserts object identity self.assertIs(fn, first) between drivers as a structural proxy for code sharing |
| `CommittedTreeBacklogCloseIntegritySelfCheck::test_committed_tree_addition_only_duplicate_is_detected` | process_backlog_close detects committed addition-only duplicate (Shape A) and emits attention.committed-duplicate event | UNGUARDED-CANDIDATE | No live test in tests/ exercises committed tree duplicate detection or attention.committed-duplicate |
| `CommittedTreeBacklogCloseIntegritySelfCheck::test_committed_tree_deletion_only_vanished_is_detected` | process_backlog_close detects committed deletion-only vanish (Shape B) and emits attention.committed-absent event | UNGUARDED-CANDIDATE | No live test in tests/ exercises attention.committed-absent |
| `CommittedTreeBacklogCloseIntegritySelfCheck::test_committed_tree_exactly_one_claimant_is_silent` | Healthy committed close with 1 claimant reports no integrity violation | UNGUARDED-CANDIDATE | No live test in tests/ exercises committed tree integrity self-check |
| `CommittedTreeBacklogCloseIntegritySelfCheck::test_no_commit_sha_is_silent` | No-commit close skips committed tree check silently | UNGUARDED-CANDIDATE | No live test in tests/ exercises committed tree integrity self-check when commit sha is None |
| `CommittedTreeBacklogCloseIntegritySelfCheck::test_paths_for_commit_are_repository_relative` | backlog_item_paths_for_commit returns repo-relative paths starting with .aw/ | UNGUARDED-CANDIDATE | Symbol search confirmed backlog_item_paths_for_commit has zero live test callers in tests/ |
| `CommittedTreeBacklogCloseIntegritySelfCheck::test_absent_id_and_invalid_commit_are_empty` | Nonexistent ID or invalid commit sha returns empty list from backlog_item_paths_for_commit without exception | UNGUARDED-CANDIDATE | No live test in tests/ calls backlog_item_paths_for_commit |

Summary of triage:
- PIN: 3
- DELEGATION-COVERED: 2
- COVERED: 5
- UNGUARDED-CANDIDATE: 48
- Total: 58
"""

from __future__ import annotations

import contextlib
import io
import json
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path, PurePath
from typing import Any
from unittest import mock

import pytest

from agent_workflows import (
    agy_runipd,
    check_engine,
    oc_runipd,
    runner_shared,
    runner_shutdown,
)
from tests.support import REPO_ROOT

_DRIVERS = (("oc_runipd", oc_runipd), ("agy_runipd", agy_runipd))


def _plan_text(
    id6: str,
    *,
    from_backlog: str | None = None,
    setid: str = "demo",
    order: int = 1,
    status: str = "approved",
    bucket: str = "pending",
    **kw: Any,
) -> str:
    """A minimal conforming plan whose metadata block and structure the reader accepts."""
    bkl_line = f"- From-Backlog: {from_backlog}\n" if from_backlog is not None else ""
    return f"""# IPD: Test Plan {id6}

- Date: 2026-08-30
- Kind: child
- Concern: Test concern for plan {id6}.
- Scope: Test scope for plan {id6}.
- Scope-Paths: README.md
- Status: {status}
- Approval: 2026-08-30, test
- Readiness: go-pending-approval
{bkl_line}- Set: {setid}
- Order: {order}
- Highest E allocated: 01
- Author: test
- Priority: medium
- Work-Kind: feature
- Id: {id6}
- Item-Dependencies: none

## Workflow history
- 2026-08-30 /plan-review (test): APPROVE. Readiness: GO - PENDING HUMAN APPROVAL.
- 2026-08-30 {status} (test): created.

## Goal
Test goal for plan {id6}.

## Detailed Implementation Checklist (TODO)
### Task group 1: work
- [ ] E-01 Work item
  - Depends on: none
  - Expected outcome: done
  - Execution state: pending

## Project conventions discovered (Step 0)
None.

## Findings
None.

## Proposed changes (ordered, validatable)
1. E-01 do work.

## Deferred / out of scope (with reason)
- None.

## Scope check
- None.

## Required tests / validation
- None.

## Spec / documentation sync
- None.

## Open questions
- None.

## Validation and cross-check (verify before reporting done)
- [ ] V-01 validates E-01
  - Required evidence: check.
  - Observed evidence:
  - Result: pending

## Approval and execution gate
- Size assessment: standard
- Cohesion rationale: not required
"""


def _spec_text(id6: str, *, from_backlog: str, status: str = "draft") -> str:
    return "\n".join(
        [
            f"# Spec: {id6}",
            "",
            "- Date: 2026-08-30",
            f"- Id: {id6}",
            f"- Status: {status}",
            f"- From-Backlog: {from_backlog}",
            "",
            "## Summary",
            "",
            "A spec.",
            "",
        ]
    )


def _item_text(id6: str, *, status: str = "graduated", blocks_release: str = "") -> str:
    lines = [
        f"- Id: {id6}",
        f"- Status: {status}",
        "- Set: demo",
        "- Priority: medium",
        "- Kind: feature",
        "- Summary: a demo item",
    ]
    if blocks_release:
        lines.append(f"- Blocks-Release: {blocks_release}")
    lines += ["", "## Workflow history", f"- 2026-08-30 {status} (test): created.", ""]
    return "\n".join(lines)


def _state_with_open_item(run_id: str = "run-test") -> dict[str, Any]:
    return {
        "repo": "/fake/repo",
        "run_id": run_id,
        "queue": [
            {
                "id6": "aaaaaa",
                "position": 1,
                "setid": "demo",
                "status": "executed",
                "from_backlog": "bbbbbb",
                "backlog_close": {
                    "item": "bbbbbb",
                    "closed": False,
                    "reason": "IPD carrier(s) not executed: x.ipd.md",
                },
            }
        ],
    }


class _Repo:
    """A throwaway git repo with a backlog tree, plans tree, and specs tree."""

    def __init__(self, root: Path) -> None:
        self.root = root
        for rel in (
            ".aw/records/backlog/graduated",
            ".aw/records/backlog/open",
            ".aw/records/backlog/done",
            ".aw/records/plans/pending",
            ".aw/records/plans/executed",
            ".aw/records/specs",
        ):
            (root / rel).mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)

    def add_item(self, id6: str, **kw) -> Path:
        status = kw.get("status", "graduated")
        path = (
            self.root
            / ".aw/records/backlog"
            / status
            / f"20260830-demo-01-{id6}-demo-item.backlog.md"
        )
        path.write_text(_item_text(id6, **kw), encoding="utf-8")
        return path

    def add_plan(self, id6: str, *, bucket: str = "pending", **kw) -> Path:
        path = (
            self.root
            / ".aw/records/plans"
            / bucket
            / f"20260830-demo-0{kw.get('order', 1)}-{id6}-a-plan.ipd.md"
        )
        path.write_text(_plan_text(id6, **kw), encoding="utf-8")
        return path

    def add_spec(self, id6: str, **kw) -> Path:
        path = (
            self.root / ".aw/records/specs" / f"20260830-{id6}-01-{id6}-a-spec.spec.md"
        )
        path.write_text(_spec_text(id6, **kw), encoding="utf-8")
        return path

    def rel(self, path: Path) -> str:
        return str(path.resolve().relative_to(self.root.resolve()))

    def item_status(self, id6: str) -> str | None:
        """The DIRECTORY status of the item (the authoritative disposition), or None."""
        for status in ("open", "graduated", "blocked", "parked", "done"):
            d = self.root / ".aw/records/backlog" / status
            if d.is_dir():
                for f in d.glob("*.md"):
                    if f"-{id6}-" in f.name:
                        return status
        return None

    def commit_all(self) -> None:
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "fixture"],
            cwd=self.root,
            check=True,
        )


class _RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        runner_shared._SIGNAL_REPORT_DONE.clear()
        runner_shared._SIGNAL_REPORT_STATE.clear()
        self.addCleanup(runner_shared._SIGNAL_REPORT_DONE.clear)
        self.addCleanup(runner_shared._SIGNAL_REPORT_STATE.clear)
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = _Repo(Path(self._tmp.name))


# ======================================================================================
# E-04: Close-decision and fail-closed group
# ======================================================================================


class TestReadsTheFromBacklogLink(_RepoCase):
    """Behavioral tests for reading and freezing From-Backlog links across both drivers."""

    def test_both_drivers_read_the_link_into_the_plan_record(self):
        """A plan carrying `- From-Backlog: <id6>` records that id6; one without records nothing."""
        linked = self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        bare = self.repo.add_plan("cccccc", order=2)
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                self.assertEqual(
                    mod.parse_plan_file(linked, self.repo.root).from_backlog,
                    "bbbbbb",
                    f"{name} must read the From-Backlog link",
                )
                self.assertIsNone(
                    mod.parse_plan_file(bare, self.repo.root).from_backlog,
                    f"{name} must record nothing when the field is absent",
                )

    def test_the_link_is_frozen_on_the_queue_entry(self):
        """The manifest and the frozen queue entry both carry it, in both drivers."""
        self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        self.repo.add_plan("cccccc", order=2)
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                manifest = mod.build_dynamic_manifest(
                    self.repo.root, mod.discover_plans(self.repo.root)
                )
                self.assertEqual(manifest["plans"]["aaaaaa"]["from_backlog"], "bbbbbb")
                self.assertIsNone(manifest["plans"]["cccccc"]["from_backlog"])

    def test_the_link_is_frozen_into_run_state_by_a_REAL_run(self):
        """The freeze, observed in `state.json` after driving the real `initialize_run`."""
        self.repo.add_plan("aaaaaa", from_backlog="bbbbbb")
        self.repo.add_plan("cccccc", order=2)
        self.repo.commit_all()
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                args = mod.build_parser().parse_args(
                    ["start", "all", "--repo", str(self.repo.root)]
                )
                args.prepare_only = True
                args.run_id = f"run-frozen-link-{name}"
                sink = io.StringIO()
                with (
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    run_dir = mod.initialize_run(args)
                frozen = {
                    entry["id6"]: entry.get("from_backlog", "<MISSING KEY>")
                    for entry in json.loads(
                        (run_dir / "state.json").read_text(encoding="utf-8")
                    )["queue"]
                }
                self.assertEqual(
                    frozen.get("aaaaaa"),
                    "bbbbbb",
                    f"{name} must FREEZE the From-Backlog link onto the queue entry",
                )
                self.assertIsNone(
                    frozen.get("cccccc"),
                    f"{name} must freeze None for an UNLINKED plan",
                )

    def test_absent_and_placeholder_values_mean_no_linked_item(self):
        """Placeholder values and empty string mean no linked item in both drivers."""
        for raw in ("-", "none", "unresolved", ""):
            for name, mod in _DRIVERS:
                with self.subTest(driver=name, value=raw):
                    text = _plan_text("aaaaaa").replace(
                        "- Id: aaaaaa", f"- Id: aaaaaa\n- From-Backlog: {raw}"
                    )
                    self.assertIsNone(mod._read_from_backlog(text))


class TestClosingRules(_RepoCase):
    """Behavioral tests for backlog-close evaluation rules."""

    def test_two_carrier_item_does_not_close_when_only_one_executed(self):
        """Item with two carriers refuses close when only one has executed."""
        self.repo.add_item("bbbbbb")
        done = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        pending = self.repo.add_plan(
            "cccccc", bucket="pending", order=2, from_backlog="bbbbbb"
        )
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                verdict = mod.evaluate_backlog_close(
                    self.repo.root, "bbbbbb", [self.repo.rel(done)]
                )
                self.assertFalse(verdict.close)
                self.assertIn("not executed", verdict.reason)
                self.assertIn(self.repo.rel(pending), verdict.reason)

    def test_two_carrier_item_closes_when_both_executed(self):
        """Item with two carriers closes when both have executed and been earned."""
        self.repo.add_item("bbbbbb")
        one = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        two = self.repo.add_plan(
            "cccccc", bucket="executed", order=2, from_backlog="bbbbbb"
        )
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                verdict = mod.evaluate_backlog_close(
                    self.repo.root, "bbbbbb", [self.repo.rel(one), self.repo.rel(two)]
                )
                self.assertTrue(verdict.close, verdict.reason)

    def test_spec_status_is_never_consulted(self):
        """Every spec status produces the same close verdict for spec-only items: existence is the test."""
        verdicts: dict[str, tuple] = {}
        for status in ("draft", "to-review", "reviewed", "approved", "implemented"):
            with self.subTest(spec_status=status), tempfile.TemporaryDirectory() as tmp:
                repo = _Repo(Path(tmp))
                repo.add_item("bbbbbb")
                spec = repo.add_spec("dddddd", from_backlog="bbbbbb", status=status)
                verdict = oc_runipd.evaluate_backlog_close(
                    repo.root, "bbbbbb", [repo.rel(spec)]
                )
                self.assertTrue(verdict.close, f"{status}: {verdict.reason}")
                verdicts[status] = (verdict.close, verdict.rule, verdict.evidence)
        self.assertEqual(
            len(set(verdicts.values())),
            1,
            f"Every spec status must reach identical verdict tuple; saw {verdicts}",
        )

    def test_item_with_no_carriers_is_not_closed(self):
        """An item with no carriers is refused close with an explanatory reason."""
        self.repo.add_item("bbbbbb")
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                verdict = mod.evaluate_backlog_close(self.repo.root, "bbbbbb", [])
                self.assertFalse(verdict.close)
                self.assertIn("no plan or spec carries", verdict.reason)

    def test_an_already_done_item_is_left_alone(self):
        """An item already in done/ is left alone with an explanatory reason."""
        self.repo.add_item("bbbbbb", status="done")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                verdict = mod.evaluate_backlog_close(
                    self.repo.root, "bbbbbb", [self.repo.rel(plan)]
                )
                self.assertFalse(verdict.close)
                self.assertIn("already done", verdict.reason)


class TestEarnedCloseGate(_RepoCase):
    """Behavioral tests for the earned-close gate and induced failure handling."""

    def test_the_gate_applies_to_the_non_ipd_rule_too(self):
        """Spec-only item with empty earned_paths refuses close."""
        self.repo.add_item("bbbbbb")
        self.repo.add_spec("dddddd", from_backlog="bbbbbb")
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                verdict = mod.evaluate_backlog_close(self.repo.root, "bbbbbb", [])
                self.assertFalse(verdict.close)
                self.assertIn("not earned", verdict.reason)

    def test_an_induced_lookup_failure_leaves_the_item_untouched(self):
        """An induced carrier lookup failure fails closed without modifying the item file."""
        self.repo.add_item("bbbbbb")
        self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        item_path = next(
            (self.repo.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
        )
        before = item_path.read_bytes()
        with mock.patch.object(
            check_engine,
            "find_from_backlog_artifacts",
            side_effect=RuntimeError("lookup failure"),
        ):
            verdict = oc_runipd.evaluate_backlog_close(
                self.repo.root, "bbbbbb", ["some/path"]
            )
        self.assertFalse(verdict.close)
        self.assertIn("lookup failure", verdict.reason)
        self.assertEqual(item_path.read_bytes(), before)

    def test_an_induced_terminal_state_read_failure_fails_closed(self):
        """An induced terminal state read failure fails closed."""
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        original = runner_shared.plan_bucket

        def boom(*_a, **_k):
            raise RuntimeError("induced bucket read failure")

        runner_shared.plan_bucket = boom  # type: ignore[assignment]
        try:
            verdict = oc_runipd.evaluate_backlog_close(
                self.repo.root, "bbbbbb", [self.repo.rel(plan)]
            )
        finally:
            runner_shared.plan_bucket = original  # type: ignore[assignment]
        self.assertFalse(verdict.close)
        self.assertIn("terminal-state read failed", verdict.reason)

    def test_an_induced_setter_failure_leaves_the_item_untouched_with_a_reason(self):
        """An induced setter failure leaves item file untouched and records failure reason."""
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        item_path = next(
            (self.repo.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
        )
        before = item_path.read_bytes()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }

        def failing_setter(*_a, **_k):
            return 1, "refused by gate: blocking carrier missing"

        with mock.patch.object(oc_runipd, "close_backlog_item", failing_setter):
            oc_runipd.process_backlog_close(run_dir, state, state["queue"][0])
        record = state["queue"][0]["backlog_close"]
        self.assertFalse(record["closed"])
        self.assertIn("refused by gate", record["reason"])
        self.assertEqual(item_path.read_bytes(), before)


class TestUsesTheGatedSetter(_RepoCase):
    """Behavioral tests for setter delegation and commit path scoping."""

    def test_the_item_file_is_never_edited_directly(self):
        """process_backlog_close delegates to setter, never editing the file directly."""
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        item_path = next(
            (self.repo.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
        )
        before = item_path.read_bytes()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        with mock.patch.object(
            oc_runipd, "close_backlog_item", lambda *_a, **_k: (0, "ok")
        ):
            oc_runipd.process_backlog_close(run_dir, state, state["queue"][0])
        self.assertTrue(item_path.is_file())
        self.assertEqual(item_path.read_bytes(), before)

    def test_the_commit_is_path_scoped_to_this_item_only(self):
        """commit_backlog_close scopes staged paths strictly to this item id6."""
        self.repo.add_item("bbbbbb")
        coworker = self.repo.add_item("cccccc", status="open")
        self.repo.commit_all()
        done = self.repo.root / ".aw/records/backlog/done"
        mine = next(
            (self.repo.root / ".aw/records/backlog/graduated").glob("*bbbbbb*.md")
        )
        (done / mine.name).write_text(
            mine.read_text(encoding="utf-8"), encoding="utf-8"
        )
        mine.unlink()
        coworker.write_text(
            coworker.read_text(encoding="utf-8") + "\nsomeone else's edit\n",
            encoding="utf-8",
        )

        from agent_workflows import git_commit_helper

        captured: list[tuple[list[str], dict]] = []
        real = git_commit_helper.offer_commit

        def spy(repo, paths, **kwargs):
            captured.append((list(paths), kwargs))
            return real(repo, paths, **kwargs)

        with mock.patch.object(git_commit_helper, "offer_commit", spy):
            sha = oc_runipd.commit_backlog_close(self.repo.root, "bbbbbb", "msg")
        self.assertEqual(len(captured), 1)
        paths, kwargs = captured[0]
        unrelated = [p for p in paths if "bbbbbb" not in Path(p).name]
        self.assertEqual(unrelated, [])
        self.assertEqual(
            sorted(Path(p).parent.name for p in paths),
            ["done", "graduated"],
        )
        self.assertFalse(kwargs.get("interactive", True))
        self.assertIsNotNone(sha)
        self.assertIn("someone else's edit", coworker.read_text(encoding="utf-8"))


class TestSharedNotCopiedFinalizeCall(_RepoCase):
    """Behavioral test ensuring both drivers call process_backlog_close upon finalize success."""

    def test_both_drivers_call_the_close_from_their_finalize_success_branch(self):
        """A real execute_item turn invokes process_backlog_close exactly once per driver."""
        for name, mod in _DRIVERS:
            spawn = "run_opencode" if name == "oc_runipd" else "run_agy_turn"
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                repo = _Repo(Path(tmp))
                repo.add_item("bbbbbb")
                plan = repo.add_plan("dbg001", bucket="executed", from_backlog="bbbbbb")
                repo.commit_all()
                run_dir = repo.root / ".aw" / "records" / "runs" / "run-close"
                (run_dir / "outcomes").mkdir(parents=True)
                (run_dir / "prompts").mkdir(parents=True)
                item = {
                    "position": 1,
                    "id6": "dbg001",
                    "setid": "demo",
                    "status": "queued",
                    "action": "execute",
                    "from_backlog": "bbbbbb",
                    "configured_file": repo.rel(plan),
                }
                state = {
                    "run_id": "run-close",
                    "created_at": "2026-09-14T00:00:00+00:00",
                    "updated_at": "2026-09-14T00:00:00+00:00",
                    "selectors": ["demo"],
                    "repo": str(repo.root),
                    "queue": [item],
                    "set_sessions": {},
                    "session_id": None,
                    "options": {
                        "opencode": "/bin/true",
                        "agy": "/bin/true",
                        "model": "probe",
                        "self_finalize": True,
                        "no_audit": True,
                        "isolate_worktree": False,
                    },
                }
                closes: list[tuple] = []
                sink = io.StringIO()
                with (
                    mock.patch.object(
                        mod,
                        spawn,
                        lambda *_a, _log=str(run_dir / "log"), **_k: (
                            0,
                            "ses",
                            _log,
                            ["probe"],
                        ),
                    ),
                    mock.patch.object(mod, "driver_begin", lambda *a, **k: (0, "ok")),
                    mock.patch.object(
                        mod, "driver_finalize", lambda *a, **k: (0, "ok")
                    ),
                    mock.patch.object(
                        mod, "assert_child_tool_identity", lambda *a, **k: None
                    ),
                    mock.patch.object(
                        mod,
                        "process_backlog_close",
                        lambda *a, _into=closes, **k: _into.append(a),
                    ),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    mod.execute_item(run_dir, state, item, recovery=False)
                self.assertEqual(item["status"], "executed")
                self.assertEqual(len(closes), 1)
                self.assertEqual(closes[0][2]["from_backlog"], "bbbbbb")


# ======================================================================================
# E-05: End-to-end close group
# ======================================================================================


class TestClosesEndToEnd(_RepoCase):
    """Behavioral tests driving process_backlog_close end-to-end on real git repositories."""

    def test_a_real_close_moves_the_item_to_done_with_evidence(self):
        """The full path through the real setter moves graduated -> done with evidence cited."""
        self.repo.add_item("bbbbbb", blocks_release="next")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]
        oc_runipd.process_backlog_close(run_dir, state, item)
        record = item["backlog_close"]
        self.assertTrue(record["closed"], record["reason"])
        self.assertEqual(self.repo.item_status("bbbbbb"), "done")
        moved = next((self.repo.root / ".aw/records/backlog/done").glob("*bbbbbb*.md"))
        text = moved.read_text(encoding="utf-8")
        self.assertIn("- Status: done", text)
        self.assertIn("- Blocks-Release: next", text)
        self.assertEqual(record["evidence"], self.repo.rel(plan))

    def test_the_move_is_committed_path_scoped_and_leaves_the_tree_clean(self):
        """The backlog move is committed with path scoping and leaves the working tree clean."""
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]
        oc_runipd.process_backlog_close(run_dir, state, item)
        record = item["backlog_close"]
        self.assertTrue(record["closed"], record["reason"])
        self.assertIsNotNone(record["commit"])
        porcelain = subprocess.run(
            ["git", "status", "--porcelain", "-uall", "--", ".aw/records/backlog"],
            cwd=self.repo.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(porcelain, "")
        files = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.repo.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        self.assertEqual(len(files), 2, files)
        for path in files:
            self.assertIn("bbbbbb", Path(path).name)

    def test_a_coworkers_other_backlog_item_is_never_swept_in(self):
        """A co-worker's uncommitted edit to another backlog item is neither committed nor touched."""
        self.repo.add_item("bbbbbb")
        coworker = self.repo.add_item("cccccc", status="open")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        coworker.write_text(
            coworker.read_text(encoding="utf-8") + "\nsomeone else's edit\n",
            encoding="utf-8",
        )
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        oc_runipd.process_backlog_close(run_dir, state, state["queue"][0])
        files = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.repo.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.split()
        for path in files:
            self.assertNotIn("cccccc", path)
        self.assertIn("someone else's edit", coworker.read_text(encoding="utf-8"))

    def test_the_close_is_recorded_in_the_run_ledger(self):
        """process_backlog_close appends a backlog-item-closed event to events.jsonl."""
        self.repo.add_item("bbbbbb")
        plan = self.repo.add_plan("aaaaaa", bucket="executed", from_backlog="bbbbbb")
        self.repo.commit_all()
        run_dir = self.repo.root / "run"
        run_dir.mkdir()
        state = {
            "repo": str(self.repo.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "aaaaaa",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "bbbbbb",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        oc_runipd.process_backlog_close(run_dir, state, state["queue"][0])
        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        closed = [e for e in events if e.get("event") == "backlog-item-closed"]
        self.assertEqual(len(closed), 1)
        self.assertEqual(closed[0]["backlog_item"], "bbbbbb")


# ======================================================================================
# E-06: Unclosed-report group
# ======================================================================================


class TestUnclosedReport(unittest.TestCase):
    """Behavioral tests for unclosed-item reports and CLI runs pointers."""

    def setUp(self) -> None:
        runner_shared._SIGNAL_REPORT_DONE.clear()
        runner_shared._SIGNAL_REPORT_STATE.clear()
        self.addCleanup(runner_shared._SIGNAL_REPORT_DONE.clear)
        self.addCleanup(runner_shared._SIGNAL_REPORT_STATE.clear)

    def test_each_open_item_is_listed_with_its_reason(self):
        """unclosed_backlog_items and render_unclosed_report list each item with reason."""
        state = _state_with_open_item()
        pairs = oc_runipd.unclosed_backlog_items(state)
        self.assertEqual(pairs, [("bbbbbb", "IPD carrier(s) not executed: x.ipd.md")])
        report = oc_runipd.render_unclosed_report(state)
        self.assertIn("bbbbbb", report)
        self.assertIn("not executed", report)

    def test_a_run_with_nothing_outstanding_prints_no_section(self):
        """When all items are closed, unclosed report returns empty."""
        state = _state_with_open_item()
        state["queue"][0]["backlog_close"]["closed"] = True
        self.assertEqual(oc_runipd.unclosed_backlog_items(state), [])
        self.assertEqual(oc_runipd.render_unclosed_report(state), "")

    def test_an_item_whose_plan_never_reached_the_close_is_still_reported(self):
        """A linked item without backlog_close records plan status as reason."""
        state = _state_with_open_item()
        del state["queue"][0]["backlog_close"]
        state["queue"][0]["status"] = "partial"
        pairs = oc_runipd.unclosed_backlog_items(state)
        self.assertEqual(len(pairs), 1)
        self.assertIn("partial", pairs[0][1])

    def test_a_plan_with_no_linked_item_contributes_nothing(self):
        """An unlinked plan contributes nothing to unclosed backlog items."""
        state = _state_with_open_item()
        state["queue"][0].pop("from_backlog")
        self.assertEqual(oc_runipd.unclosed_backlog_items(state), [])

    def test_the_ledger_record_is_written_before_the_print(self):
        """Ledger append is attempted before anything is printed to terminal."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            ledger = run_dir / "events.jsonl"
            observed: list[tuple[str, bool]] = []
            oc_runipd.register_signal_report(run_dir, _state_with_open_item())
            real_record = runner_shared.record_unclosed_backlog_items

            def watched_record(*args, **kwargs):
                observed.append(("ledger", ledger.exists()))
                return real_record(*args, **kwargs)

            def watched_print(*args, **kwargs):
                observed.append(("print", ledger.exists()))

            with (
                mock.patch.object(
                    runner_shared, "record_unclosed_backlog_items", watched_record
                ),
                mock.patch.object(runner_shared, "print", watched_print, create=True),
            ):
                oc_runipd.emit_shutdown_report()
        self.assertEqual(
            [label for label, _existed in observed][:2],
            ["ledger", "print"],
        )
        self.assertEqual(observed[0], ("ledger", False))
        self.assertTrue(observed[1][1])

    def test_the_ledger_record_survives_when_the_print_is_discarded(self):
        """Ledger record survives when printing to stream raises an exception."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            oc_runipd.register_signal_report(run_dir, _state_with_open_item())
            with (
                mock.patch.object(
                    runner_shared,
                    "render_unclosed_report",
                    side_effect=OSError("broken pipe"),
                ),
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                oc_runipd.emit_shutdown_report()
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["event"], "backlog-items-left-open")

    def test_the_report_is_idempotent_under_a_repeated_signal(self):
        """Calling emit_shutdown_report repeatedly produces only one output and ledger record."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            oc_runipd.register_signal_report(run_dir, _state_with_open_item())
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
                oc_runipd.emit_shutdown_report()
                first = buf.getvalue()
                oc_runipd.emit_shutdown_report()
                second = buf.getvalue()
            self.assertEqual(first, second)
            events = [
                json.loads(line)
                for line in (run_dir / "events.jsonl")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            self.assertEqual(len(events), 1)

    def test_the_pointer_names_the_real_run_id_and_the_real_verb(self):
        """render_runs_pointer outputs command with run ID and aw runs verb."""
        state = {"run_id": "run-xyz-123"}
        pointer = runner_shared.render_runs_pointer(state)
        self.assertIn("aw runs run-xyz-123", pointer)

    def test_the_pointer_names_a_verb_the_CLI_really_has(self):
        """The pointer names a command verb that actually exists on the CLI."""
        res = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "runs", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0, f"aw runs --help failed: {res.stderr}")

    def test_json_output_suppresses_the_pointer_and_stays_PARSEABLE(self):
        """Driver main with --json emits parseable JSON without runs pointer."""
        for name, mod in _DRIVERS:
            with tempfile.TemporaryDirectory() as tmp:
                repo = _Repo(Path(tmp))
                repo.add_plan("aaa111", from_backlog="bbbbbb")
                repo.add_item("bbbbbb")
                repo.commit_all()
                sink = io.StringIO()
                with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
                    mod.main(
                        [
                            "start",
                            "all",
                            "--repo",
                            str(repo.root),
                            "--prepare-only",
                            "--run-id",
                            f"run-pointer-{name}",
                        ]
                    )
                # Test human status
                buf_human = io.StringIO()
                with (
                    contextlib.redirect_stdout(buf_human),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    mod.main(
                        ["status", "--repo", str(repo.root), f"run-pointer-{name}"]
                    )
                self.assertIn("aw runs", buf_human.getvalue())

                # Test machine JSON status
                buf_json = io.StringIO()
                with (
                    contextlib.redirect_stdout(buf_json),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    mod.main(
                        [
                            "status",
                            "--repo",
                            str(repo.root),
                            f"run-pointer-{name}",
                            "--json",
                        ]
                    )
                json_out = buf_json.getvalue()
                self.assertNotIn("aw runs", json_out)
                parsed = json.loads(json_out)
                self.assertIsInstance(parsed, dict)


# ======================================================================================
# E-07: Signal and shutdown group
# ======================================================================================


_SIGNAL_SCRIPT = """
import json, os, signal, sys, time
from pathlib import Path
sys.path.insert(0, {repo!r})
from agent_workflows import {driver} as d
from agent_workflows.render_stream import install_exit_signal_handler

run_dir = Path({run_dir!r})
state = {{
    "repo": {run_dir!r},
    "run_id": "run-signal-test",
    "queue": [
        {{
            "id6": "aaaaaa", "position": 1, "setid": "demo", "status": "executed",
            "from_backlog": "bbbbbb",
            "backlog_close": {{"item": "bbbbbb", "closed": False,
                              "reason": "IPD carrier(s) not executed: x.ipd.md"}},
        }}
    ],
}}
d.register_signal_report(run_dir, state)
install_exit_signal_handler()
try:
    print("READY", flush=True)
    while True:
        time.sleep(0.05)
except KeyboardInterrupt as exc:
    is_sigterm = "SIGTERM" in str(exc)
    d.emit_shutdown_report(to_stderr=True)
    print(
        ("Terminated by SIGTERM" if is_sigterm else "Interrupted")
        + "; durable run state was preserved.",
        file=sys.stderr,
    )
    sys.exit(143 if is_sigterm else 130)
"""


class TestShutdownReportOnInterrupt(unittest.TestCase):
    """Behavioral tests for signal handling, shutdown reports, and handler safety."""

    def setUp(self) -> None:
        runner_shared._SIGNAL_REPORT_DONE.clear()
        runner_shared._SIGNAL_REPORT_STATE.clear()
        self.addCleanup(runner_shared._SIGNAL_REPORT_DONE.clear)
        self.addCleanup(runner_shared._SIGNAL_REPORT_STATE.clear)

    def _run_and_signal(self, driver: str, sig: int) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            script = Path(tmp) / "child.py"
            run_dir = Path(tmp) / "run"
            run_dir.mkdir()
            script.write_text(
                _SIGNAL_SCRIPT.format(
                    repo=str(REPO_ROOT), driver=driver, run_dir=str(run_dir)
                ),
                encoding="utf-8",
            )
            proc = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            assert proc.stdout is not None
            self.assertEqual(proc.stdout.readline().strip(), "READY")
            proc.send_signal(sig)
            try:
                out, err = proc.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                proc.kill()
                out, err = proc.communicate()
                raise
            events_path = run_dir / "events.jsonl"
            ledger = (
                events_path.read_text(encoding="utf-8") if events_path.exists() else ""
            )
            return proc.returncode, out + err + "\n--LEDGER--\n" + ledger

    def _assert_reported(self, rc: int, expect: int, output: str) -> None:
        self.assertEqual(rc, expect, output)
        self.assertIn("bbbbbb", output)
        self.assertIn("not executed", output)
        self.assertIn("Run `aw runs run-signal-test` for more info.", output)
        self.assertIn("backlog-items-left-open", output)

    @pytest.mark.skipif(
        sys.platform == "win32", reason="SIGINT subprocess requires POSIX"
    )
    def test_sigint_produces_the_report_and_exits_130(self):
        """Real SIGINT to child process exits 130 and produces report to stderr and ledger."""
        for name, _mod in _DRIVERS:
            with self.subTest(driver=name):
                rc, output = self._run_and_signal(name, signal.SIGINT)
                self._assert_reported(rc, 130, output)

    @pytest.mark.skipif(
        sys.platform == "win32", reason="SIGTERM subprocess requires POSIX"
    )
    def test_sigterm_produces_the_report_and_exits_143(self):
        """Real SIGTERM to child process exits 143 and produces report to stderr and ledger."""
        for name, _mod in _DRIVERS:
            with self.subTest(driver=name):
                rc, output = self._run_and_signal(name, signal.SIGTERM)
                self._assert_reported(rc, 143, output)

    def test_the_sigterm_funnel_is_wired_in_both_drivers_main(self):
        """Both drivers main installs a callable Python handler for SIGTERM."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                signal.signal(signal.SIGTERM, signal.SIG_DFL)
                self.addCleanup(signal.signal, signal.SIGTERM, signal.SIG_DFL)
                before = signal.getsignal(signal.SIGTERM)
                sink = io.StringIO()
                with (
                    tempfile.TemporaryDirectory() as tmp,
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    mod.main(["status", "--repo", tmp, "run-nope"])
                after = signal.getsignal(signal.SIGTERM)
                self.assertIsNot(after, before)
                self.assertTrue(callable(after))

    def test_both_drivers_report_from_their_keyboardinterrupt_funnel(self):
        """KeyboardInterrupt during queue execution funnels report to stderr with exit 130."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                runner_shared._SIGNAL_REPORT_DONE.clear()
                runner_shared._SIGNAL_REPORT_STATE.clear()
                root = Path(tmp)
                subprocess.run(["git", "init", "-q", "."], cwd=root, check=True)
                run_dir = root / ".aw" / "records" / "runs" / "run-ki"
                run_dir.mkdir(parents=True)
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": "run-ki",
                            "repo": str(root),
                            "created_at": "2026-09-14T00:00:00+00:00",
                            "updated_at": "2026-09-14T00:00:00+00:00",
                            "selectors": ["demo"],
                            "options": {},
                            "set_sessions": {},
                            "queue": [
                                {
                                    "position": 1,
                                    "id6": "aaaaaa",
                                    "setid": "demo",
                                    "action": "execute",
                                    "kind": "child",
                                    "status": "executed",
                                    "dependencies": [],
                                    "attempts": [],
                                    "from_backlog": "bbbbbb",
                                    "backlog_close": {
                                        "item": "bbbbbb",
                                        "closed": False,
                                        "reason": "IPD carrier(s) not executed: x.ipd.md",
                                    },
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                emit_kwargs: list[dict] = []
                real_emit = mod.emit_shutdown_report

                def spy_emit(*args, _real=real_emit, _seen=emit_kwargs, **kwargs):
                    _seen.append(dict(kwargs))
                    return _real(*args, **kwargs)

                def interrupted(*_a, _mod=mod, _rd=run_dir, **_k):
                    _mod.register_signal_report(
                        _rd,
                        json.loads((_rd / "state.json").read_text(encoding="utf-8")),
                    )
                    raise KeyboardInterrupt("Interrupted")

                out, err = io.StringIO(), io.StringIO()
                with (
                    mock.patch.object(mod, "run_queue", interrupted),
                    mock.patch.object(mod, "emit_shutdown_report", spy_emit),
                    contextlib.redirect_stdout(out),
                    contextlib.redirect_stderr(err),
                ):
                    rc = mod.main(["resume", "--repo", str(root), "run-ki"])
                self.assertEqual(rc, 130)
                self.assertEqual(len(emit_kwargs), 1)
                self.assertTrue(emit_kwargs[0].get("to_stderr"))
                self.assertIn("bbbbbb", err.getvalue())
                self.assertIn("Run `aw runs run-ki` for more info.", err.getvalue())
                self.assertTrue((run_dir / "events.jsonl").is_file())

    def test_the_callable_is_handler_safe(self):
        """signal_report_callback does not acquire locks or persist state, and writes ledger."""
        report = oc_runipd.signal_report_callback()
        self.assertTrue(callable(report))
        forbidden = ("run_lock", "locked_run", "save_state", "platform_lock")
        for name in forbidden:
            owner = next(
                (m for m in (oc_runipd, runner_shared) if hasattr(m, name)), None
            )
            if owner is None:
                self.assertTrue(
                    hasattr(oc_runipd, "run_lock")
                    or hasattr(runner_shared, "run_lock"),
                )
                continue
            with (
                self.subTest(forbidden=name, owner=owner.__name__),
                tempfile.TemporaryDirectory() as tmp,
            ):
                run_dir = Path(tmp)
                runner_shared._SIGNAL_REPORT_DONE.clear()
                runner_shared._SIGNAL_REPORT_STATE.clear()
                oc_runipd.register_signal_report(run_dir, _state_with_open_item())
                hits: list[str] = []
                real = getattr(owner, name)

                def trap(*args, _name=name, _real=real, _hits=hits, **kwargs):
                    _hits.append(_name)
                    return _real(*args, **kwargs)

                sink = io.StringIO()
                with (
                    mock.patch.object(owner, name, trap),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                ):
                    oc_runipd.signal_report_callback()()
                self.assertEqual(hits, [])
                self.assertTrue((run_dir / "events.jsonl").is_file())

    def test_the_child_kill_escalation_path_is_unchanged(self):
        """terminate_process reads grace constants at call time and stays separate from shutdown report."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                received: dict = {}
                report_hits: list[str] = []

                def spy_reaper(_process, _into=received, **kwargs):
                    _into.update(kwargs)

                def trap(label, _hits=report_hits):
                    def _trap(*_a, _label=label, _into=_hits, **_k):
                        _into.append(_label)

                    return _trap

                with (
                    mock.patch.object(mod, "_SIGINT_GRACE_SECONDS", 11.5),
                    mock.patch.object(mod, "_SIGTERM_GRACE_SECONDS", 22.5),
                    mock.patch.object(runner_shutdown, "terminate_process", spy_reaper),
                    mock.patch.object(
                        runner_shared,
                        "emit_shutdown_report",
                        trap("emit_shutdown_report"),
                    ),
                    mock.patch.object(
                        runner_shared,
                        "register_signal_report",
                        trap("register_signal_report"),
                    ),
                ):
                    mod.terminate_process(object())
                self.assertEqual(
                    (received.get("sigint_grace"), received.get("sigterm_grace")),
                    (11.5, 22.5),
                )
                self.assertEqual(report_hits, [])

    def test_both_drivers_emit_the_shutdown_report_on_normal_exit(self):
        """run_queue publishes live state before first turn and emits report on normal exit."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                runner_shared._SIGNAL_REPORT_DONE.clear()
                runner_shared._SIGNAL_REPORT_STATE.clear()
                run_dir = Path(tmp) / "run-report"
                run_dir.mkdir(parents=True)
                item = {
                    "position": 1,
                    "id6": "aaaaaa",
                    "setid": "demo",
                    "action": "execute",
                    "kind": "child",
                    "status": "queued",
                    "dependencies": [],
                    "attempts": [],
                    "from_backlog": "bbbbbb",
                }
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": "run-report",
                            "repo": str(tmp),
                            "created_at": "2026-09-14T00:00:00+00:00",
                            "updated_at": "2026-09-14T00:00:00+00:00",
                            "selectors": ["demo"],
                            "options": {},
                            "set_sessions": {},
                            "queue": [item],
                        }
                    ),
                    encoding="utf-8",
                )
                seen: list[str] = []
                real_emit = mod.emit_shutdown_report
                real_register = mod.register_signal_report

                def spy_emit(*args, _real=real_emit, _seen=seen, **kwargs):
                    _seen.append("emit")
                    return _real(*args, **kwargs)

                def spy_register(*args, _real=real_register, _seen=seen, **kwargs):
                    _seen.append("register")
                    return _real(*args, **kwargs)

                published_at_first_turn: list[dict] = []

                def fake_execute(
                    rd, st, it, *a, _mod=mod, _seen=published_at_first_turn, **k
                ):
                    _seen.append(dict(runner_shared._SIGNAL_REPORT_STATE))
                    it["status"] = "executed"
                    _mod.save_state(rd, st)

                buffer = io.StringIO()
                with (
                    mock.patch.object(mod, "execute_item", side_effect=fake_execute),
                    mock.patch.object(mod, "emit_shutdown_report", spy_emit),
                    mock.patch.object(mod, "register_signal_report", spy_register),
                    contextlib.redirect_stdout(buffer),
                    contextlib.redirect_stderr(buffer),
                ):
                    mod.run_queue(run_dir, retry_incomplete=False)
                output = buffer.getvalue()
                self.assertIn("emit", seen)
                self.assertIn("register", seen)
                self.assertLess(seen.index("register"), seen.index("emit"))
                self.assertTrue(
                    published_at_first_turn
                    and published_at_first_turn[0].get("state") is not None,
                )
                self.assertEqual(
                    str(published_at_first_turn[0].get("run_dir")),
                    str(run_dir),
                )
                self.assertIn("bbbbbb", output)
                self.assertIn("Run `aw runs run-report` for more info.", output)

    def test_an_interrupt_BEFORE_the_first_turn_still_reports(self):
        """An interrupt arriving before the first turn still reports from published pre-loop state."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name), tempfile.TemporaryDirectory() as tmp:
                runner_shared._SIGNAL_REPORT_DONE.clear()
                runner_shared._SIGNAL_REPORT_STATE.clear()
                run_dir = Path(tmp) / "run-early"
                run_dir.mkdir(parents=True)
                (run_dir / "state.json").write_text(
                    json.dumps(
                        {
                            "schema_version": 1,
                            "run_id": "run-early",
                            "repo": str(tmp),
                            "created_at": "2026-09-14T00:00:00+00:00",
                            "updated_at": "2026-09-14T00:00:00+00:00",
                            "selectors": ["demo"],
                            "options": {},
                            "set_sessions": {},
                            "queue": [
                                {
                                    "position": 1,
                                    "id6": "aaaaaa",
                                    "setid": "demo",
                                    "action": "execute",
                                    "kind": "child",
                                    "status": "queued",
                                    "dependencies": [],
                                    "attempts": [],
                                    "from_backlog": "bbbbbb",
                                    "backlog_close": {
                                        "item": "bbbbbb",
                                        "closed": False,
                                        "reason": "IPD carrier(s) not executed: x.ipd.md",
                                    },
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

                def interrupt_early(*_a, **_k):
                    raise KeyboardInterrupt("Interrupted")

                sink = io.StringIO()
                with (
                    mock.patch.object(mod, "reconcile_interrupted", interrupt_early),
                    contextlib.redirect_stdout(sink),
                    contextlib.redirect_stderr(sink),
                    self.assertRaises(KeyboardInterrupt),
                ):
                    mod.run_queue(run_dir, retry_incomplete=False)
                report = io.StringIO()
                with (
                    contextlib.redirect_stdout(report),
                    contextlib.redirect_stderr(report),
                ):
                    mod.emit_shutdown_report()
                self.assertIn("bbbbbb", report.getvalue())
                self.assertTrue((run_dir / "events.jsonl").is_file())


# ======================================================================================
# E-08: Integrity self-check group
# ======================================================================================


class TestBacklogCloseIntegritySelfCheck(unittest.TestCase):
    """Behavioral tests for runner_shared.backlog_item_paths_for_id."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "."], cwd=self.root, check=True)
        for d in ("graduated", "open", "done"):
            (self.root / ".aw/records/backlog" / d).mkdir(parents=True, exist_ok=True)

    def _item(self, path: Path, id6: str, status: str) -> None:
        path.write_text(_item_text(id6, status=status), encoding="utf-8")

    def test_a_single_claimant_is_the_healthy_case(self):
        """Exactly one claimant returns a 1-element list."""
        self._item(
            self.root / ".aw/records/backlog/done/20260101-aa-01-abc123-x.backlog.md",
            "abc123",
            "done",
        )
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                found = mod.backlog_item_paths_for_id(self.root, "abc123")
                self.assertEqual(len(found), 1)

    def test_two_claimants_are_detected_which_is_the_36_item_corruption(self):
        """Two claimants (graduated and done) returns both paths."""
        self._item(
            self.root
            / ".aw/records/backlog/graduated/20260101-aa-01-abc123-x.backlog.md",
            "abc123",
            "graduated",
        )
        self._item(
            self.root / ".aw/records/backlog/done/20260101-aa-01-abc123-x.backlog.md",
            "abc123",
            "done",
        )
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                found = mod.backlog_item_paths_for_id(self.root, "abc123")
                self.assertEqual(len(found), 2)
                self.assertTrue(
                    any("graduated/" in p for p in found)
                    and any("done/" in p for p in found),
                )

    def test_an_absent_id_is_empty_not_an_error(self):
        """An absent ID returns an empty list without error."""
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                self.assertEqual(mod.backlog_item_paths_for_id(self.root, "zzzzzz"), [])

    def test_paths_are_repository_relative_so_no_home_path_can_leak(self):
        """Paths returned by backlog_item_paths_for_id are repo-relative."""
        self._item(
            self.root / ".aw/records/backlog/done/20260101-aa-01-abc123-x.backlog.md",
            "abc123",
            "done",
        )
        for name, mod in _DRIVERS:
            with self.subTest(driver=name):
                for rel in mod.backlog_item_paths_for_id(self.root, "abc123"):
                    self.assertFalse(PurePath(rel).is_absolute())
                    self.assertTrue(rel.startswith(".aw/"))


class TestCommittedTreeBacklogCloseIntegritySelfCheck(unittest.TestCase):
    """Behavioral tests for committed tree backlog close integrity self-check."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        subprocess.run(["git", "init", "-q", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@t"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "t"], cwd=self.root, check=True)
        for rel in (
            ".aw/records/backlog/graduated",
            ".aw/records/backlog/open",
            ".aw/records/backlog/done",
            ".aw/records/plans/pending",
            ".aw/records/plans/executed",
        ):
            (self.root / rel).mkdir(parents=True, exist_ok=True)

    def _item(self, path: Path, id6: str, status: str) -> None:
        path.write_text(_item_text(id6, status=status), encoding="utf-8")

    def _plan(self, path: Path, id6: str, from_backlog: str) -> None:
        path.write_text(
            _plan_text(id6, from_backlog=from_backlog, bucket="executed"),
            encoding="utf-8",
        )

    def test_committed_tree_addition_only_duplicate_is_detected(self):
        """Shape A: A commit leaves two copies in HEAD, working tree has one."""
        item_grad = (
            self.root
            / ".aw/records/backlog/graduated/20260101-demo-01-abc123-test.backlog.md"
        )
        self._item(item_grad, "abc123", "graduated")
        plan = (
            self.root / ".aw/records/plans/executed/20260101-demo-01-plan01-test.ipd.md"
        )
        self._plan(plan, "plan01", "abc123")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)

        item_done = (
            self.root
            / ".aw/records/backlog/done/20260101-demo-01-abc123-test.backlog.md"
        )

        def do_close(*_a, **_k):
            item_grad.rename(item_done)
            return 0, "ok"

        def do_commit(*_a, **_k):
            self._item(item_grad, "abc123", "graduated")
            subprocess.run(
                ["git", "add", str(item_done), str(item_grad)],
                cwd=self.root,
                check=True,
            )
            subprocess.run(
                ["git", "commit", "-qm", "addition-only duplicate commit"],
                cwd=self.root,
                check=True,
            )
            item_grad.unlink()
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

        run_dir = self.root / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "repo": str(self.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "plan01",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "abc123",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]

        stderr_buf = io.StringIO()
        with (
            mock.patch.object(oc_runipd, "close_backlog_item", do_close),
            mock.patch.object(oc_runipd, "commit_backlog_close", do_commit),
            contextlib.redirect_stderr(stderr_buf),
        ):
            oc_runipd.process_backlog_close(run_dir, state, item)

        record = item.get("backlog_close") or {}
        self.assertTrue(record.get("closed"))
        self.assertIn("integrity", record)
        self.assertEqual(record["integrity"]["rule"], "attention.committed-duplicate")
        self.assertEqual(record["integrity"]["count"], 2)
        self.assertIsNotNone(record["integrity"]["commit"])
        self.assertEqual(len(record["integrity"]["paths"]), 2)

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        violations = [
            e for e in events if e.get("event") == "backlog-close-integrity-violation"
        ]
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule"], "attention.committed-duplicate")

        err = stderr_buf.getvalue()
        self.assertIn("attention.committed-duplicate", err)
        self.assertIn("abc123", err)
        self.assertIn("survived beside its destination", err)

    def test_committed_tree_deletion_only_vanished_is_detected(self):
        """Shape B: A commit leaves zero copies in HEAD, working tree has one."""
        item_open = (
            self.root
            / ".aw/records/backlog/open/20260101-demo-01-def456-test.backlog.md"
        )
        self._item(item_open, "def456", "open")
        plan = (
            self.root / ".aw/records/plans/executed/20260101-demo-01-plan02-test.ipd.md"
        )
        self._plan(plan, "plan02", "def456")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)

        item_done = (
            self.root
            / ".aw/records/backlog/done/20260101-demo-01-def456-test.backlog.md"
        )

        def do_close(*_a, **_k):
            item_open.rename(item_done)
            return 0, "ok"

        def do_commit(*_a, **_k):
            subprocess.run(
                ["git", "rm", "-q", str(item_open)], cwd=self.root, check=True
            )
            subprocess.run(
                ["git", "commit", "-qm", "deletion-only vanished commit"],
                cwd=self.root,
                check=True,
            )
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

        run_dir = self.root / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "repo": str(self.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "plan02",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "def456",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]

        stderr_buf = io.StringIO()
        with (
            mock.patch.object(oc_runipd, "close_backlog_item", do_close),
            mock.patch.object(oc_runipd, "commit_backlog_close", do_commit),
            contextlib.redirect_stderr(stderr_buf),
        ):
            oc_runipd.process_backlog_close(run_dir, state, item)

        record = item.get("backlog_close") or {}
        self.assertTrue(record.get("closed"))
        self.assertIn("integrity", record)
        self.assertEqual(record["integrity"]["rule"], "attention.committed-absent")
        self.assertEqual(record["integrity"]["count"], 0)
        self.assertIsNotNone(record["integrity"]["commit"])
        self.assertEqual(record["integrity"]["paths"], [])

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        violations = [
            e for e in events if e.get("event") == "backlog-close-integrity-violation"
        ]
        self.assertEqual(len(violations), 1)
        self.assertEqual(violations[0]["rule"], "attention.committed-absent")

        err = stderr_buf.getvalue()
        self.assertIn("attention.committed-absent", err)
        self.assertIn("def456", err)
        self.assertIn("dropped from the commit", err)

    def test_committed_tree_exactly_one_claimant_is_silent(self):
        """Healthy close with exactly 1 claimant in commit reports no integrity violation."""
        item_grad = (
            self.root
            / ".aw/records/backlog/graduated/20260101-demo-01-ghi789-test.backlog.md"
        )
        self._item(item_grad, "ghi789", "graduated")
        plan = (
            self.root / ".aw/records/plans/executed/20260101-demo-01-plan03-test.ipd.md"
        )
        self._plan(plan, "plan03", "ghi789")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)

        item_done = (
            self.root
            / ".aw/records/backlog/done/20260101-demo-01-ghi789-test.backlog.md"
        )

        def do_close(*_a, **_k):
            item_grad.rename(item_done)
            return 0, "ok"

        def do_commit(*_a, **_k):
            subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
            subprocess.run(
                ["git", "commit", "-qm", "clean move commit"], cwd=self.root, check=True
            )
            return subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.root,
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()

        run_dir = self.root / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "repo": str(self.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "plan03",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "ghi789",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]

        stderr_buf = io.StringIO()
        with (
            mock.patch.object(oc_runipd, "close_backlog_item", do_close),
            mock.patch.object(oc_runipd, "commit_backlog_close", do_commit),
            contextlib.redirect_stderr(stderr_buf),
        ):
            oc_runipd.process_backlog_close(run_dir, state, item)

        record = item.get("backlog_close") or {}
        self.assertTrue(record.get("closed"))
        self.assertNotIn("integrity", record)

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        violations = [
            e for e in events if e.get("event") == "backlog-close-integrity-violation"
        ]
        self.assertEqual(len(violations), 0)
        self.assertEqual(stderr_buf.getvalue(), "")

    def test_no_commit_sha_is_silent(self):
        """When there is no commit sha (e.g. isolated turn), committed check is skipped silently."""
        item_grad = (
            self.root
            / ".aw/records/backlog/graduated/20260101-demo-01-jkl012-test.backlog.md"
        )
        self._item(item_grad, "jkl012", "graduated")
        plan = (
            self.root / ".aw/records/plans/executed/20260101-demo-01-plan04-test.ipd.md"
        )
        self._plan(plan, "plan04", "jkl012")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)

        run_dir = self.root / "run"
        run_dir.mkdir(parents=True, exist_ok=True)
        state = {
            "repo": str(self.root),
            "run_id": "run-test",
            "queue": [
                {
                    "id6": "plan04",
                    "position": 1,
                    "setid": "demo",
                    "from_backlog": "jkl012",
                    "status": "executed",
                    "attempts": [],
                    "last_plan_path": str(plan),
                }
            ],
        }
        item = state["queue"][0]

        stderr_buf = io.StringIO()
        with (
            mock.patch.object(
                oc_runipd, "close_backlog_item", lambda *_a, **_k: (0, "ok")
            ),
            mock.patch.object(
                oc_runipd, "commit_backlog_close", lambda *_a, **_k: None
            ),
            contextlib.redirect_stderr(stderr_buf),
        ):
            oc_runipd.process_backlog_close(run_dir, state, item)

        record = item.get("backlog_close") or {}
        self.assertNotIn("integrity", record)

        events = [
            json.loads(line)
            for line in (run_dir / "events.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        violations = [
            e for e in events if e.get("event") == "backlog-close-integrity-violation"
        ]
        self.assertEqual(len(violations), 0)
        self.assertEqual(stderr_buf.getvalue(), "")

    def test_paths_for_commit_are_repository_relative(self):
        """Paths returned by backlog_item_paths_for_commit are repo-relative."""
        item_grad = (
            self.root
            / ".aw/records/backlog/graduated/20260101-demo-01-abc123-test.backlog.md"
        )
        self._item(item_grad, "abc123", "graduated")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        paths = runner_shared.backlog_item_paths_for_commit(self.root, sha, "abc123")
        self.assertEqual(len(paths), 1)
        for rel in paths:
            self.assertFalse(PurePath(rel).is_absolute())
            self.assertTrue(rel.startswith(".aw/"))

    def test_absent_id_and_invalid_commit_are_empty(self):
        """Nonexistent ID or invalid sha returns empty list, never an exception."""
        item_grad = (
            self.root
            / ".aw/records/backlog/graduated/20260101-demo-01-abc123-test.backlog.md"
        )
        self._item(item_grad, "abc123", "graduated")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "initial"], cwd=self.root, check=True)
        sha = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        self.assertEqual(
            runner_shared.backlog_item_paths_for_commit(self.root, sha, "zzzz99"), []
        )
        self.assertEqual(
            runner_shared.backlog_item_paths_for_commit(
                self.root, "deadbeef" * 5, "abc123"
            ),
            [],
        )
