# IPD: Restore the stranded-run and dispatchable-work tests of test_run_summary_table

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`) group 40 carries 34 test names present in `tests/test_run_summary_table.py` at `19313eed^` but missing from the recreated file at HEAD, all classified `gap` in `b1mx2w` `## Recreated missing names` (replay verdict `pass`, 34 passed). The recreated file now holds 9 different tests (landed-column and lane-worktree rendering); the 34 lost tests covered `render_stream.render_run_summary_table` box layout, stranded-run outcomes (`integration_was_refused`, `integration_refusal_detail`, `format_stranded_work_section`, `_interrupt_reason_of`), the recovered-run fixture, dispatchable-work counting, and the `oc_runipd`/`agy_runipd` SIGINT/SIGTERM exit paths (`runner_shared.emit_shutdown_report`), 10 exclusive lines per `b1mx2w` `## Recreated re-diff`. A mutation making `integration_was_refused` return False, or `format_stranded_work_section` return an empty string, passes the routine suite today.
- Scope: Append 33 of the 34 missing tests, unchanged in body, to `tests/test_run_summary_table.py` with their module-level helpers (`STRANDED_FIXTURE`, `_state`, `_item`, `_stranded_item`, `_outcome_line`, `_q`) and imports, each marked `@pytest.mark.core`. The 34th, `test_both_hosts_and_the_summary_share_ONE_definition`, is not restored: its whole body is two `assert ... is ...` object-identity checks between modules (F-03). EXCLUDES any production change; EXCLUDES changing the committed fixture `tests/fixtures/run_summary/stranded-run-state.json` and the 9 existing tests.
- Scope-Paths: tests/test_run_summary_table.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 23
- Highest E allocated: 02
- Author: opencode
- Id: ya63p5

## Workflow history

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Ran the `19313eed^` copy of the file at HEAD `f84c3af26` (34 passed in 0.72s), appended the proposed 33 tests to a scratch copy of the current file (42 passed serially and under `-n 4`, 32 core-selected), and ran reverted early-return mutations of `integration_was_refused` and `format_stranded_work_section` against the old copy.
- 2026-10-17 draft (opencode): created.

## Goal

Bring back the 33 behavioral run-summary tests that the trim dropped, so the routine bare core-tier run renders real run states (stranded, landed, refused, interrupted, recovered, pre-executed members) and the runner exit paths, and asserts on the rendered summary text and exit codes. Done means a mutation that hides a stranded run or a refusal turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

- [ ] E-01 Append to `tests/test_run_summary_table.py`, after the existing classes, a section headed by a comment naming backlog `q86fxm`, findings `b1mx2w`, source revision `19313eed^` and the one deliberately excluded test. The section adds: the imports the old file used that the current file lacks (`io`, `json`, `unittest.mock.patch`, `pytest`, and from `agent_workflows.render_stream` `Palette`, `StreamTracker`, `_strip_ansi`, `format_duration`, `render_run_summary_table`, plus `from agent_workflows import oc_runipd, agy_runipd`), moved to the top import block so ruff's import-order rule passes; the six module-level helpers `STRANDED_FIXTURE`, `_state`, `_item`, `_stranded_item`, `_outcome_line`, `_q` copied verbatim; and the 33 test functions from `git show 19313eed^:tests/test_run_summary_table.py` copied verbatim except for a `@pytest.mark.core` decorator on each. Do not restore `test_both_hosts_and_the_summary_share_ONE_definition`. If an appended test fails at execution HEAD, STOP on it: record it in Findings and either update only that expectation for an intended change (cite the commit `git log -S` finds) or file a `bug` backlog item with `--blocks-release next` for a regression.
  - Depends on: none
  - Expected outcome: the file passes 42 tests (9 existing + 33 appended) serially, under `-n 4` and under random order; the 33 appended tests are core-selected; `ruff check tests/test_run_summary_table.py` is clean.
  - Execution state: pending

- [ ] E-02 Bring the 9 existing tests into the core tier by adding a module-level `pytestmark = pytest.mark.core` (and then dropping the now-redundant per-test `@pytest.mark.core` decorators E-01 added, so there is one marking mechanism). At authoring `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -m core --collect-only -q` reported `no tests collected (9 deselected)`, so a bare run does not run them today; they share the file and cost 0.67s together.
  - Depends on: E-01
  - Expected outcome: `-m core --collect-only -q` on the file lists all 42 tests.
  - Execution state: pending

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
| F-04 | Reverted scratch mutations against the 19313eed^ copy | `integration_was_refused` -> `False`: 10 failed, 24 passed; `format_stranded_work_section` -> `""`: 6 failed, 28 passed. Against the current 9-test file, `integration_was_refused` -> `False` produced 9 passed, confirming the gap. |

## Proposed changes (ordered, validatable)

1. E-01 appends the 33 behavioral tests with helpers and imports, core-marked.
2. E-02 brings the 9 existing tests into the core tier with them.

## Deferred / out of scope (with reason)

- `test_both_hosts_and_the_summary_share_ONE_definition` is not restored.
  - Carrier-Declined: no work is owed for this item; it is a code-structure pin forbidden by `AGENTS.md`, and `test_the_rendered_progress_line_excludes_pre_executed_members` plus `test_the_maintainers_exact_scenario_counts_zero_of_six` assert the observable dispatchable-work count it was protecting.

## Scope check

- Over-scope: none. One test file; no production code and no fixture change.
- Under-scope: none for group 40 (33 of 34 names restored, the 34th declined with reason).

## Required tests / validation

- `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -v` passes 42 tests, per-test list pasted; repeat under `-n 4` and with `-p randomly`.
- `python3 -m pytest tests/test_run_summary_table.py -o addopts="" -m core --collect-only -q` lists 42.
- Reach: `--cov=agent_workflows.render_stream --cov=agent_workflows.runner_shared --cov-report=term-missing` showing `_interrupt_reason_of`, `format_stranded_work_section`, `integration_refusal_detail`, `integration_was_refused` and `emit_shutdown_report` executing.
- Mutation spot-checks (scratch, reverted): `integration_was_refused` return False, `format_stranded_work_section` return `""`, `integration_refusal_detail` return `""`, `_interrupt_reason_of` return None.
- `ruff check tests/test_run_summary_table.py`; bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

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

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff --stat HEAD` showing only `tests/test_run_summary_table.py`; paste the `-v` run listing all 33 appended names PASSED and confirm by `rg -c "def test_both_hosts_and_the_summary_share_ONE_definition" tests/test_run_summary_table.py` returning 0; paste the `-n 4` and random-order summaries; paste `ruff check` clean; paste the failures from scratch `integration_was_refused` return-False and `format_stranded_work_section` return-`""` mutations (reverted).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `-m core --collect-only -q` listing 42 items; paste the reach output from Required tests; paste the bare `python3 -m pytest` summary line; paste `aw sanitize --agent` with no `fail`; paste a final empty `git diff agent_workflows/`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only `tests/test_run_summary_table.py` through `aw commit ya63p5 -- tests/test_run_summary_table.py`; never push. Mutation spot-checks are scratch production edits that must be reverted and absent from the diff. Move the plan to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`.
