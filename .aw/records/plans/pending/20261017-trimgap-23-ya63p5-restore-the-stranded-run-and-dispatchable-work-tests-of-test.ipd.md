# IPD: Restore the stranded-run and dispatchable-work tests of test_run_summary_table

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`) group 40 carries 34 test names present in `tests/test_run_summary_table.py` at `19313eed^` but missing from the recreated file at HEAD, all classified `gap` in `b1mx2w` `## Recreated missing names` (replay verdict `pass`, 34 passed). The recreated file now holds 9 different tests (landed-column and lane-worktree rendering); the 34 lost tests covered `render_stream.render_run_summary_table` box layout, stranded-run outcomes (`integration_was_refused`, `integration_refusal_detail`, `format_stranded_work_section`, `_interrupt_reason_of`), the recovered-run fixture, dispatchable-work counting, and the `oc_runipd`/`agy_runipd` SIGINT/SIGTERM exit paths (`runner_shared.emit_shutdown_report`), 10 exclusive lines per `b1mx2w` `## Recreated re-diff`. A mutation making `integration_was_refused` return False, or `format_stranded_work_section` return an empty string, passes the routine suite today.
- Scope: Append 33 of the 34 missing tests, unchanged in body, to `tests/test_run_summary_table.py` with their module-level helpers (`STRANDED_FIXTURE`, `_state`, `_item`, `_stranded_item`, `_outcome_line`, `_q`) and imports, each marked `@pytest.mark.core`, plus one residual test (E-03) that asserts on `runner_shared.emit_shutdown_report` output, which the restored tests reach without asserting on (F-05). The 34th, `test_both_hosts_and_the_summary_share_ONE_definition`, is not restored: its whole body is two `assert ... is ...` object-identity checks between modules (F-03). EXCLUDES any production change; EXCLUDES changing the committed fixture `tests/fixtures/run_summary/stranded-run-state.json` and the 9 existing tests.
- Scope-Paths: tests/test_run_summary_table.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 23
- Highest E allocated: 03
- Author: opencode
- Id: ya63p5
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved

- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Ran the `19313eed^` copy of the file at HEAD `f84c3af26` (34 passed in 0.72s), appended the proposed 33 tests to a scratch copy of the current file (42 passed serially and under `-n 4`, 32 core-selected), and ran reverted early-return mutations of `integration_was_refused` and `format_stranded_work_section` against the old copy.
- 2026-10-17 draft (opencode): created.

## Goal

Bring back the 33 behavioral run-summary tests that the trim dropped, so the routine bare core-tier run renders real run states (stranded, landed, refused, interrupted, recovered, pre-executed members) and the runner exit paths, and asserts on the rendered summary text and exit codes. Done means a mutation that hides a stranded run or a refusal turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

- [x] E-01 Append to `tests/test_run_summary_table.py`, after the existing classes, a section headed by a comment naming backlog `q86fxm`, findings `b1mx2w`, source revision `19313eed^` and the one deliberately excluded test. The section adds: the imports the old file used that the current file lacks (`io`, `json`, `unittest.mock.patch`, `pytest`, and from `agent_workflows.render_stream` `Palette`, `StreamTracker`, `_strip_ansi`, `format_duration`, `render_run_summary_table`, plus `from agent_workflows import oc_runipd, agy_runipd`), moved to the top import block so ruff's import-order rule passes; the six module-level helpers `STRANDED_FIXTURE`, `_state`, `_item`, `_stranded_item`, `_outcome_line`, `_q` copied verbatim; and the 33 test functions from `git show 19313eed^:tests/test_run_summary_table.py` copied verbatim except for a `@pytest.mark.core` decorator on each. Do not restore `test_both_hosts_and_the_summary_share_ONE_definition`. Disposition rule if an appended test fails at execution HEAD (none did at authoring, F-02, nor at review, F-05): do not mark the item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: every test in the file passes, with zero failed, serially, under `-n 4` and under random order (42 at authoring and review: 9 existing + 33 appended; the count is context, not the bar); every one of the 33 appended names is present and core-selected; the repository's pinned hooks pass on the file: `pre-commit run ruff --files tests/test_run_summary_table.py` and `pre-commit run ruff-format --files tests/test_run_summary_table.py` (hook `ruff` v0.4.4 per `.pre-commit-config.yaml`; do NOT use a newer `ruff` from PATH, which already reports 2 pre-existing errors on the current file, F-05). `ruff-format` rewrites the file (at review it removed blank lines after docstrings); commit the rewritten file, since `aw commit` re-stages a hook-rewritten path once.
  - Execution state: performed

- [x] E-02 Bring the 9 existing tests into the core tier by adding a module-level `pytestmark = pytest.mark.core` (and then dropping the now-redundant per-test `@pytest.mark.core` decorators E-01 added, so there is one marking mechanism). At authoring `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -m core --collect-only -q` reported `no tests collected (9 deselected)`, so a bare run does not run them today; they share the file and cost 0.67s together.
  - Depends on: E-01
  - Expected outcome: `-m core --collect-only -q` on the file lists every test in it, and deselects none.
  - Execution state: performed

### Task group 2: residual assertion

- [x] E-03 Append one test, `test_the_shutdown_report_prints_the_runs_pointer_exactly_once(tmp_path, capsys)`, to the same restored section. It saves `runner_shared._SIGNAL_REPORT_STATE` (a dict copy) and whether `runner_shared._SIGNAL_REPORT_DONE` is set. It clears the event, calls `runner_shared.register_signal_report(tmp_path, {"run_id": "run-shut01", "queue": []})`, then calls `runner_shared.emit_shutdown_report()` twice. It asserts that `capsys.readouterr().out` contains `Run \`aw runs run-shut01\` for more info.` exactly once and that `.err` is empty. In `finally` it restores both globals. This is the only routine-tier assertion on the shutdown report's output and on its idempotence. The restored SIGINT/SIGTERM tests execute `emit_shutdown_report` but never assert on it, and the tests that do assert on it (`tests/test_runner_backlog_close_behavior.py` `TestUnclosedReport`) are not core-marked (F-05). Re-measure the pointer string at execution HEAD (`runner_shared.render_runs_pointer`); apply the E-01 disposition rule if it changed.
  - Depends on: E-02
  - Expected outcome: the test passes serially and under random order, and fails under a scratch `emit_shutdown_report` early `return None` and under a scratch removal of its `_SIGNAL_REPORT_DONE.is_set()` guard (both reverted).
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): `test_both_hosts_and_the_summary_share_ONE_definition` asserts only `runner_shared.dispatchable_work_total is render_stream.dispatchable_work_total` and the same for `agy_runipd`, so it pins re-export structure and is excluded. `test_the_earned_signal_constants_match_the_runners_definitions` compares constant VALUES and calls `integration_was_refused` on each refused signal, which is behavior, so it is kept. `test_the_committed_fixture_is_tracked_and_not_gitignored` runs `git check-ignore` on a test fixture, guarding that the suite is portable to other checkouts rather than pinning production code, so it is kept.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget): the 33 tests ran in 0.72s together at authoring (slowest 0.17 to 0.48s), so all join the core tier.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Recreated missing names` and `## Recreated re-diff` row `tests/test_run_summary_table.py` | 34 names classified `gap`; exclusive reach 10 lines across `render_stream._interrupt_reason_of`, `format_stranded_work_section`, `integration_refusal_detail`, `integration_was_refused` and `runner_shared.emit_shutdown_report`. |
| F-02 | `git show 19313eed^:tests/test_run_summary_table.py` copied to a scratch test path at HEAD `f84c3af26` | `34 passed in 0.72s`. The committed fixture `tests/fixtures/run_summary/stranded-run-state.json` still exists. No top-level name collides with the current file (checked by AST). Appending 33 tests to a scratch copy of the current file: `42 passed in 8.77s` with coverage, `42 passed in 4.52s` under `-n 4`, `-m core` selected 32 at that time (E-02 marks the remaining). |
| F-03 | Reading the old file | `test_both_hosts_and_the_summary_share_ONE_definition` consists solely of two `is` identity assertions between modules. |
| F-05 | Plan review at HEAD `31623e157`. Scratch merged file `tests/test_zzscr_rst.py` built per E-01 and E-02, a scratch E-03 test, early-return mutations against both the current file and the merged one, and a coverage JSON. All scratch files and production edits were removed (`git diff agent_workflows/` empty, `git status` clean). | Merged file: `42 passed` serially, `-n 4` and random seeds 1 to 3; `-m core` collects 42. CURRENT file (9 tests): every one of the 10 key mutations below survives, apart from `render_run_summary_table -> ""`. MERGED: `integration_was_refused -> False` 10 failed and `-> True` 5 failed; `integration_refusal_detail -> None` and `-> ""` each 2 failed; `format_stranded_work_section -> ""` 6 failed; `_interrupt_reason_of -> None` 1 failed; `item_is_dispatchable_work -> True` and `-> False` each 4 failed; `dispatchable_work_total -> 0` 6 failed. But `runner_shared.emit_shutdown_report -> None` SURVIVES (`42 passed`): the restored SIGINT tests reach it without asserting on its output. The tests that do catch it (`tests/test_runner_backlog_close_behavior.py`, 9 failed) are outside the core tier (`no tests collected (51 deselected)` under `-m core`). The scratch E-03 test passes and is order-independent (`43 passed` at seeds 1 to 3); it fails under `emit_shutdown_report -> None` and under removal of the idempotence guard. All five keys in F-01 reach an executed body line. PATH `ruff` 0.16.3 reports 2 errors on the CURRENT file at HEAD (`I001`, `RUF059`) and 5 on the merged one; the pinned `pre-commit` hooks `ruff` and `ruff-format` (v0.4.4) pass, and `ruff-format` removes 39 blank lines. |
| F-04 | Reverted scratch mutations against the 19313eed^ copy | `integration_was_refused` -> `False`: 10 failed, 24 passed; `format_stranded_work_section` -> `""`: 6 failed, 28 passed. Against the current 9-test file, `integration_was_refused` -> `False` produced 9 passed, confirming the gap. |

## Proposed changes (ordered, validatable)

1. E-01 appends the 33 behavioral tests with helpers and imports, core-marked.
2. E-02 brings the 9 existing tests into the core tier with them.
3. E-03 adds one residual assertion for `emit_shutdown_report` (F-05).

## Deferred / out of scope (with reason)

- `test_both_hosts_and_the_summary_share_ONE_definition` is not restored.
  - Carrier-Declined: no work is owed for this item; it is a code-structure pin forbidden by `AGENTS.md`, and `test_the_rendered_progress_line_excludes_pre_executed_members` plus `test_the_maintainers_exact_scenario_counts_zero_of_six` assert the observable dispatchable-work count it was protecting.

## Scope check

- Over-scope: none. One test file; no production code and no fixture change.
- Under-scope: none for group 40 (33 of 34 names restored, the 34th declined with reason). Review added E-03, because one of the five F-01 reach targets (`emit_shutdown_report`) was reached but not asserted on (F-05).

## Required tests / validation

- `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -v` passes with zero failed, per-test list pasted; repeat under `-n 4` and with `-p randomly`.
- `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -m core --collect-only -q` collects every test in the file and deselects none.
- Reach: run the `-v` command with `--cov=agent_workflows.render_stream --cov=agent_workflows.runner_shared --cov-report=json:<tmp>/cov.json`. For each of `_interrupt_reason_of`, `format_stranded_work_section`, `integration_refusal_detail`, `integration_was_refused` and `emit_shutdown_report`, report whether any line of its function body is in `executed_lines`, using a scratch script that locates each body by symbol and is not committed. `term-missing` alone does not attribute lines to functions.
- Mutation spot-checks (scratch, reverted): `integration_was_refused` return False, `format_stranded_work_section` return `""`, `integration_refusal_detail` return `""`, `_interrupt_reason_of` return None, `emit_shutdown_report` return None, and removal of the `emit_shutdown_report` idempotence guard. Each must fail at least one test in the file.
- `pre-commit run ruff --files tests/test_run_summary_table.py` and `pre-commit run ruff-format --files tests/test_run_summary_table.py` pass; bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`; delete any `.coverage` file and scratch script.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Append to the recreated file or restore a separate module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: append. `b1mx2w` names these as missing from `tests/test_run_summary_table.py` specifically, the names do not collide with the 9 current tests (F-02), and one file keeps the run-summary contract in one place.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git diff --stat HEAD` showing only `tests/test_run_summary_table.py`. Paste the `-v` run listing all 33 appended names PASSED with zero failed, and confirm `rg -c "def test_both_hosts_and_the_summary_share_ONE_definition" tests/test_run_summary_table.py` returns 0. Paste the `-n 4` and random-order summaries. Paste the two `pre-commit run` hook lines showing `Passed`. Paste the failures from scratch `integration_was_refused` return-False and `format_stranded_work_section` return-`""` mutations (reverted).
  - Observed evidence:
    `git diff --stat HEAD`:
    ```
     tests/test_run_summary_table.py | 1051 ++++++++++++++++++++++++++++++++++++++-
     1 file changed, 1039 insertions(+), 12 deletions(-)
    ```
    All 33 appended tests PASSED with zero failed in `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -v`:
    ```
    tests/test_run_summary_table.py::test_oc_runipd_main_sigterm_and_sigint_handling PASSED [ 23%]
    tests/test_run_summary_table.py::test_the_maintainers_exact_scenario_counts_zero_of_six PASSED [ 25%]
    tests/test_run_summary_table.py::test_the_rendered_progress_line_excludes_pre_executed_members PASSED [ 27%]
    tests/test_run_summary_table.py::test_an_explicitly_empty_signal_is_treated_as_absent_not_as_a_refusal PASSED [ 30%]
    tests/test_run_summary_table.py::test_resume_statusbar_starts_from_resume_time PASSED [ 32%]
    tests/test_run_summary_table.py::test_render_run_summary_table_diagnostics PASSED [ 34%]
    tests/test_run_summary_table.py::test_a_stranded_run_is_not_reported_completed PASSED [ 37%]
    tests/test_run_summary_table.py::test_the_committed_fixture_is_tracked_and_not_gitignored PASSED [ 39%]
    tests/test_run_summary_table.py::test_a_landed_run_still_reports_completed_in_green PASSED [ 41%]
    tests/test_run_summary_table.py::test_the_denominator_never_divides_by_zero PASSED [ 44%]
    tests/test_run_summary_table.py::test_a_partially_stranded_run_reports_stranded PASSED [ 46%]
    tests/test_run_summary_table.py::test_render_run_summary_table_borders_and_alignment PASSED [ 48%]
    tests/test_run_summary_table.py::test_the_recovery_section_prints_NO_absolute_path PASSED [ 51%]
    tests/test_run_summary_table.py::test_agy_runipd_main_sigterm_and_sigint_handling PASSED [ 53%]
    tests/test_run_summary_table.py::test_an_unknown_future_signal_reads_as_a_refusal_not_as_success PASSED [ 55%]
    tests/test_run_summary_table.py::test_the_recovery_section_names_the_branch_and_the_reason_and_the_next_step PASSED [ 58%]
    tests/test_run_summary_table.py::test_an_integration_blocked_status_still_reports_failed PASSED [ 60%]
    tests/test_run_summary_table.py::test_an_exit_reason_still_short_circuits_the_whole_outcome_block PASSED [ 62%]
    tests/test_run_summary_table.py::test_the_item_table_gains_NO_column PASSED [ 65%]
    tests/test_run_summary_table.py::test_a_frozen_reviewed_entry_is_not_dispatchable_work PASSED [ 67%]
    tests/test_run_summary_table.py::test_a_refusal_released_by_the_agents_answer_is_not_stranded PASSED [ 69%]
    tests/test_run_summary_table.py::test_render_run_summary_table_tracker_override PASSED [ 72%]
    tests/test_run_summary_table.py::test_a_review_only_run_with_no_integration_signal_key_reports_completed PASSED [ 74%]
    tests/test_run_summary_table.py::test_the_reason_detail_is_read_from_the_ATTEMPT_and_absence_is_tolerated PASSED [ 76%]
    tests/test_run_summary_table.py::test_the_stranded_word_is_the_same_one_the_cross_tree_view_uses PASSED [ 79%]
    tests/test_run_summary_table.py::test_oc_runipd_print_status_renders_table PASSED [ 83%]
    tests/test_run_summary_table.py::test_an_item_with_no_preserved_branch_still_gets_an_actionable_line PASSED [ 86%]
    tests/test_run_summary_table.py::test_an_already_executed_set_member_is_not_dispatchable_work PASSED [ 88%]
    tests/test_run_summary_table.py::test_format_duration PASSED             [ 90%]
    tests/test_run_summary_table.py::test_the_earned_signal_constants_match_the_runners_definitions PASSED [ 93%]
    tests/test_run_summary_table.py::test_render_run_summary_table_ascii_borders PASSED [ 95%]
    tests/test_run_summary_table.py::test_the_recovered_run_fixture_STILL_reports_stranded PASSED [ 97%]
    tests/test_run_summary_table.py::test_agy_runipd_print_status_renders_table PASSED [100%]
    ```
    Excluded test confirmation:
    `rg -c "def test_both_hosts_and_the_summary_share_ONE_definition" tests/test_run_summary_table.py` returns 0.
    `-n 4` summary:
    `43 passed in 2.23s`
    Random-order summary:
    `43 passed in 0.96s` (Using --randomly-seed=1659667456)
    Pre-commit hooks:
    ```
    ruff.....................................................................Passed
    ruff-format..............................................................Passed
    ```
    Mutation spot-checks (scratch, reverted):
    `integration_was_refused` return False:
    `10 failed, 33 passed in 1.75s` (FAILED tests: test_the_earned_signal_constants_match_the_runners_definitions, test_a_stranded_run_is_not_reported_completed, test_the_recovery_section_names_the_branch_and_the_reason_and_the_next_step, test_the_reason_detail_is_read_from_the_ATTEMPT_and_absence_is_tolerated, test_an_item_with_no_preserved_branch_still_gets_an_actionable_line, test_the_recovery_section_prints_NO_absolute_path, test_the_item_table_gains_NO_column, test_a_partially_stranded_run_reports_stranded, test_an_unknown_future_signal_reads_as_a_refusal_not_as_success, test_the_recovered_run_fixture_STILL_reports_stranded).
    `format_stranded_work_section` return `[]`:
    `6 failed, 37 passed in 1.13s` (FAILED tests: test_the_recovered_run_fixture_STILL_reports_stranded, test_the_recovery_section_names_the_branch_and_the_reason_and_the_next_step, test_an_item_with_no_preserved_branch_still_gets_an_actionable_line, test_the_item_table_gains_NO_column, test_the_recovery_section_prints_NO_absolute_path, test_the_reason_detail_is_read_from_the_ATTEMPT_and_absence_is_tolerated).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `-m core --collect-only -q` collecting every test in the file with none deselected; paste the bare `python3 -m pytest` summary line; paste `aw sanitize --agent` with no `fail`.
  - Observed evidence:
    `-m core --collect-only -q`:
    ```
    tests/test_run_summary_table.py::TestLaneWorktreePathsAndFailVerifyRefusal::test_stream_events_render_actual_lane_worktree_path_while_tracker_dedupes_logical_path
    tests/test_run_summary_table.py::TestLaneWorktreePathsAndFailVerifyRefusal::test_explain_fail_verify_outcome_handles_missing_and_partial_outcomes
    tests/test_run_summary_table.py::TestLaneWorktreePathsAndFailVerifyRefusal::test_fail_verify_missing_disposition_surfaces_reason_and_remedy_across_summaries
    tests/test_run_summary_table.py::test_a_review_only_run_with_no_integration_signal_key_reports_completed
    tests/test_run_summary_table.py::test_oc_runipd_main_sigterm_and_sigint_handling
    tests/test_run_summary_table.py::test_the_recovered_run_fixture_STILL_reports_stranded
    tests/test_run_summary_table.py::test_an_already_executed_set_member_is_not_dispatchable_work
    tests/test_run_summary_table.py::test_the_maintainers_exact_scenario_counts_zero_of_six
    tests/test_run_summary_table.py::test_render_run_summary_table_tracker_override
    tests/test_run_summary_table.py::test_format_duration
    tests/test_run_summary_table.py::test_the_shutdown_report_prints_the_runs_pointer_exactly_once
    tests/test_run_summary_table.py::test_an_unknown_future_signal_reads_as_a_refusal_not_as_success
    tests/test_run_summary_table.py::test_the_item_table_gains_NO_column
    tests/test_run_summary_table.py::test_agy_runipd_print_status_renders_table
    tests/test_run_summary_table.py::test_the_recovery_section_prints_NO_absolute_path
    tests/test_run_summary_table.py::test_a_landed_run_still_reports_completed_in_green
    tests/test_run_summary_table.py::test_an_exit_reason_still_short_circuits_the_whole_outcome_block
    tests/test_run_summary_table.py::test_the_committed_fixture_is_tracked_and_not_gitignored
    tests/test_run_summary_table.py::test_an_item_with_no_preserved_branch_still_gets_an_actionable_line
    tests/test_run_summary_table.py::test_a_refusal_released_by_the_agents_answer_is_not_stranded
    tests/test_run_summary_table.py::test_oc_runipd_print_status_renders_table
    tests/test_run_summary_table.py::test_the_reason_detail_is_read_from_the_ATTEMPT_and_absence_is_tolerated
    tests/test_run_summary_table.py::test_a_frozen_reviewed_entry_is_not_dispatchable_work
    tests/test_run_summary_table.py::test_render_run_summary_table_borders_and_alignment
    tests/test_run_summary_table.py::test_the_earned_signal_constants_match_the_runners_definitions
    tests/test_run_summary_table.py::test_render_run_summary_table_diagnostics
    tests/test_run_summary_table.py::test_the_denominator_never_divides_by_zero
    tests/test_run_summary_table.py::test_the_stranded_word_is_the_same_one_the_cross_tree_view_uses
    tests/test_run_summary_table.py::test_resume_statusbar_starts_from_resume_time
    tests/test_run_summary_table.py::test_an_integration_blocked_status_still_reports_failed
    tests/test_run_summary_table.py::test_an_explicitly_empty_signal_is_treated_as_absent_not_as_a_refusal
    tests/test_run_summary_table.py::test_render_run_summary_table_ascii_borders
    tests/test_run_summary_table.py::test_the_recovery_section_names_the_branch_and_the_reason_and_the_next_step
    tests/test_run_summary_table.py::test_a_stranded_run_is_not_reported_completed
    tests/test_run_summary_table.py::test_a_partially_stranded_run_reports_stranded
    tests/test_run_summary_table.py::test_the_rendered_progress_line_excludes_pre_executed_members
    tests/test_run_summary_table.py::test_agy_runipd_main_sigterm_and_sigint_handling
    tests/test_run_summary_table.py::RunSummaryTableRenderingTests::test_landed_column_values_no_color
    tests/test_run_summary_table.py::RunSummaryTableRenderingTests::test_render_steps_table_headers_and_variants
    tests/test_run_summary_table.py::RunSummaryTableRenderingTests::test_landed_column_values_with_color
    tests/test_run_summary_table.py::LandedVerdictPredicateTests::test_artifact_audit_input_and_status_independence
    tests/test_run_summary_table.py::LandedVerdictPredicateTests::test_pure_directory_name_mapping
    tests/test_run_summary_table.py::LandedVerdictPredicateTests::test_path_and_monthly_shard_climbing
    43 tests collected in 0.40s
    ```
    None deselected (all 43 tests collected).
    Bare `python3 -m pytest` summary line:
    `1578 passed, 3 warnings in 71.21s (0:01:11)`
    `aw sanitize --agent` result:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5933,"findings":0,"evidence":["leak-scan"],"next":null}`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `-v` line for `test_the_shutdown_report_prints_the_runs_pointer_exactly_once` PASSED, plus a random-order run of the file with zero failed. Paste the failures, each naming that test, from scratch `emit_shutdown_report` early-`return None` and from removal of its `_SIGNAL_REPORT_DONE.is_set()` guard (both reverted). Paste the per-function reach listing from Required tests showing all five functions REACHED. Paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
    `-v` line:
    `tests/test_run_summary_table.py::test_the_shutdown_report_prints_the_runs_pointer_exactly_once PASSED [ 81%]`
    Random-order run of the file:
    `43 passed in 0.96s` (seed 1659667456)
    Failures from scratch mutations:
    `emit_shutdown_report` early `return None`:
    ```
    FAILED tests/test_run_summary_table.py::test_the_shutdown_report_prints_the_runs_pointer_exactly_once
    1 failed, 42 passed in 2.67s
    E           AssertionError: assert 0 == 1
    ```
    Removal of `_SIGNAL_REPORT_DONE.is_set()` guard:
    ```
    FAILED tests/test_run_summary_table.py::test_the_shutdown_report_prints_the_runs_pointer_exactly_once
    1 failed, 42 passed in 2.57s
    E           AssertionError: assert 2 == 1
    ```
    Per-function reach listing:
    `_interrupt_reason_of`: lines 3647-3675, body hits: 9/28 -> REACHED: True
    `format_stranded_work_section`: lines 4025-4119, body hits: 19/94 -> REACHED: True
    `integration_refusal_detail`: lines 3950-3978, body hits: 11/28 -> REACHED: True
    `integration_was_refused`: lines 3851-3888, body hits: 11/37 -> REACHED: True
    `emit_shutdown_report`: lines 49550-49570, body hits: 14/20 -> REACHED: True
    Final `git diff agent_workflows/`:
    Empty.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; none block.
- Scope fence (a declaration, not a stop condition): `tests/test_run_summary_table.py` is the only intended change. Any other path you edit (for example a `bug` backlog item filed under the E-01 disposition rule) must be justified at finalize with `--scope-reason`. If the declared path is left unmodified, it needs `--scope-ack`.
- Honesty rule: every V-item MUST paste the ACTUAL runner output; never claim a pass, a kill, or a reach you did not run and observe.
- Mutation spot-checks are scratch production edits: revert each one immediately, and confirm `git diff agent_workflows/` is empty before committing. Delete any `.coverage` file and scratch script.
- Commit: only `tests/test_run_summary_table.py`, through `aw commit ya63p5 -- tests/test_run_summary_table.py`; run `git diff --cached --name-only` first and unstage anything not yours. Never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize ya63p5` instead. Never hand-`git mv` the plan.
