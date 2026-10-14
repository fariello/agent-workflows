# IPD: Restore behavioral coverage that lint_file and check_durable_carrier share the evaluate_durable_carrier predicate

- Date: 2026-10-14
- Kind: child
- Concern: `ipd_lint.lint_file` (pre-transition, via `ipd_lint._merge_durable_carrier`) and `check_engine.check_durable_carrier` (the `aw check` sweep) are required to share ONE predicate, `check_engine.evaluate_durable_carrier`, and the pure `ipd_lint.lint_text` / `ipd_lint.check_checkpoint` must never reach it; the behavioral tests proving this were deleted with `tests/test_durable_capture.py` in `19313eed`, so a second implementation on either surface would now go undetected.
- Scope: Add one new behavioral test module that (a) replaces `check_engine.evaluate_durable_carrier` with a sentinel and asserts the sentinel's detail surfaces on both `lint_file --phase pre-transition` and `check_durable_carrier`, and (b) spies the real evaluator and asserts `lint_file` reaches it exactly once while `lint_text`/`check_checkpoint` reach it zero times at every checkpoint; then update the stale "no live guard currently asserts this" remark in the `evaluate_durable_carrier` docstring.
- Scope-Paths: tests/test_durable_carrier_shared_predicate.py, agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 8owahv
- Set: 8owahv
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: 55kl2u

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog 8owahv; review-ready.

## Goal

Restore, as behavioral tests only (P16), the guarantee that `aw check` and `aw ipd lint --phase pre-transition` answer `check.ipd-uncarried-obligation` from the ONE shared evaluator `check_engine.evaluate_durable_carrier`, and that the documented-pure lint surfaces never reach it. This was lost when `tests/test_durable_capture.py` was deleted (`ev7t1w` site S-09, disposition RETIRE-UNGUARDED).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: shared-predicate tests

- [ ] E-01 Create `tests/test_durable_carrier_shared_predicate.py` with a `unittest.TestCase` whose `setUp` calls `support.declare_execution_role(self)` and builds an isolated tmp repo (plans lanes `pending`/`executed`, backlog `open`, under `tempfile.mkdtemp`, removed in `tearDown`) holding ONE pending subject plan dated on/after `check_engine.CARRIER_CUTOVER_DATE` whose `## Deferred / out of scope (with reason)` section carries an uncarried row (`- AN UNCARRIED DEFECT: nothing tracks this.`) and whose E/V rows are `performed`/`pass` so pre-transition isolates this rule (fixture shape as `19313eed7^:tests/test_durable_capture.py` `_plan`, re-implemented locally). Add `test_one_predicate_backs_both_surfaces`: patch `check_engine.evaluate_durable_carrier` with a sentinel returning `[artifact_core.Drift(str(plan_path), "check.ipd-uncarried-obligation", MARKER, severity="error")]`, then call `ipd_lint.lint_file(plan, checkpoint="pre-transition")` and `check_engine.check_durable_carrier(repo)`, asserting the lint diagnostics with that code have messages exactly `[MARKER]` and the sweep drifts with that rule have detail exactly `[MARKER]`. Add a non-vacuity sub-assertion that, UNPATCHED, both surfaces report the rule on the same fixture with a detail that is NOT the marker.
  - Depends on: none
  - Expected outcome: the module exists and the sentinel test passes against current code, proving both consumers emit the shared evaluator's own output.
  - Execution state: pending
- [ ] E-02 In the same module add `test_only_lint_file_reaches_the_evaluator`: wrap the real evaluator with `mock.patch.object(check_engine, "evaluate_durable_carrier", wraps=check_engine.evaluate_durable_carrier)` and assert `lint_file(plan, checkpoint="pre-transition")` calls it exactly once and reports the rule; then, for every checkpoint in `ipd_schema.CHECKPOINTS`, drive `ipd_lint.lint_text(text, checkpoint=cp, directory="pending")` and `ipd_lint.check_checkpoint(ipd_lint.parse(text), cp, "pending")` under a fresh spy and assert call count 0. Also assert `lint_file` at every checkpoint other than `pre-transition` calls it 0 times (the `_CARRIER_CHECKPOINTS` placement, observed by behavior).
  - Depends on: E-01
  - Expected outcome: the placement test passes against current code.
  - Execution state: pending

### Task group 2: stale remark

- [ ] E-03 In `agent_workflows/check_engine.py`, edit the `evaluate_durable_carrier` docstring sentence "was asserted directly by ``tests/test_durable_capture.py`` (deleted in ``19313eed``; no live guard currently asserts this)" so it names `tests/test_durable_carrier_shared_predicate.py` as the live guard. Docstring-only change; no behavior change.
  - Depends on: E-02
  - Expected outcome: the docstring names the new live test module and no longer claims the guard is absent.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): drive the code and assert outputs; never read source via `inspect`/`ast`/regex. Patching a collaborator with a sentinel or a `wraps=` spy is behavioral observation, and is exactly how the deleted module replaced its two `inspect.getsource` pins.
- `ipd_lint._merge_durable_carrier` imports `check_engine as _ce` inside the function and calls `_ce.evaluate_durable_carrier(...)` at call time; `check_engine.check_durable_carrier` calls the module-global name. Patching the attribute on the `check_engine` module is therefore observed by both.
- Suite runs bare as `python3 -m pytest` (`-n auto`); tests must be xdist-safe with their own tmp repo and `support.declare_execution_role(self)` (`tests/support.py` `declare_execution_role`).
- Fixtures must not read live repo records (the deleted module's docstring: "EVERY fixture is an ISOLATED tmp repo built under `tmp_path`").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- Executed plan `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`) row S-09: `check_engine.py` / `evaluate_durable_carrier` / `tests/test_durable_capture.py` / `19313eed` / RETIRE-UNGUARDED, "no live test asserts this call agreement".
- `19313eed7^:tests/test_durable_capture.py` held `test_one_predicate_backs_both_surfaces` and `test_the_merge_is_wired_into_lint_file_and_not_the_pure_path`, both behavioral (sentinel and spy); they are the model for E-01/E-02.
- Current tests calling the evaluator (`tests/test_carrier_detail_descriptive_bound.py`, `tests/test_check_engine.py` `test_case_6_evaluate_durable_carrier_end_to_end`, `tests/test_ipd_authoring.py`) exercise one surface each; none proves both consumers route through the one function, nor that the pure path stays pure.
- The `evaluate_durable_carrier` docstring currently says "no live guard currently asserts this", which becomes false after E-01/E-02.

## Proposed changes (ordered, validatable)

1. E-01: new module with the sentinel single-predicate test plus non-vacuity check.
2. E-02: spy-based placement test (lint_file once at pre-transition, zero elsewhere, pure surfaces zero everywhere).
3. E-03: docstring-only update in `check_engine.evaluate_durable_carrier`.

## Deferred / out of scope (with reason)

- Restoring the rest of the deleted `tests/test_durable_capture.py` (verdict tables, severity tiers, section walk): not part of backlog `8owahv`, which names only the shared-predicate property.
  - Carrier-Declined: outside this backlog item's single named property; no defect is known in those areas.
- Any behavior change to `evaluate_durable_carrier`, `check_durable_carrier`, or `_merge_durable_carrier`: this is coverage restoration.
  - Carrier-Declined: deliberate non-goal, not an outstanding obligation.

## Scope check

- Over-scope: none. The only production edit is a docstring sentence that would otherwise become false.
- Under-scope: none. Both halves (one predicate backs both; pure path never reaches it) are covered.

## Required tests / validation

- `python3 -m pytest tests/test_durable_carrier_shared_predicate.py` passes (V-01, V-02).
- Mutation check: temporarily make `check_durable_carrier` compute its drift without calling `evaluate_durable_carrier` (e.g. return `[]` or an inline copy) and confirm the sentinel test FAILS, then revert (V-01).
- Full bare suite `python3 -m pytest` with no new failures (V-03).

## Spec / documentation sync

N/A: no spec or user-facing documentation describes these tests; the only text change is the docstring in E-03.

## Open questions

### OQ-01: New module or append to an existing carrier test module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: a new purpose-named module `tests/test_durable_carrier_shared_predicate.py`. `tests/test_carrier_detail_descriptive_bound.py` is scoped by its docstring to the Section 8.8 descriptive bound, and a dedicated name is what the E-03 docstring cites, matching sibling restoration plan `yfo6z6`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_durable_carrier_shared_predicate.py` showing `test_one_predicate_backs_both_surfaces` PASSED; pasted output of a temporary mutation run (body of `check_engine.check_durable_carrier` no longer calling `evaluate_durable_carrier`) showing that test FAILED, followed by `git diff --stat agent_workflows/check_engine.py` proving the mutation was reverted; plus `grep -nE "inspect|import ast|read_text\(.*(check_engine|ipd_lint)" tests/test_durable_carrier_shared_predicate.py` returning no match.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `-v` pytest output showing `test_only_lint_file_reaches_the_evaluator` PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/check_engine.py` showing only docstring lines changed and naming `tests/test_durable_carrier_shared_predicate.py`; AND the pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the two Scope-Paths files through `aw commit 55kl2u -- <paths>`; never push. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry pasted observed evidence with `Result: pass`.
