# IPD: Restore behavioral test coverage for migration_complex coordinators, Fix Bar, consent gates and setup state machine

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `x62jok` (Set `trimgap`, group 8 of the `b1mx2w` filing plan) records that all 40 production keys in `agent_workflows/migration_complex.py` (265 exclusive lines) are `unreached` by the routine (core-tier) test selection at baseline HEAD, final verdict `unguarded-unreached` in `b1mx2w` `## Rollup mutation results`. Their behavioral tests lived in `tests/test_migration_complex.py` (30 tests), deleted by the suite trim `19313eed`; `hpjj44` `## Derived properties` attributes the exclusive reach of every one of these keys to that file. The only surviving core test touching the module, `test_core_module_coverage.test_migration_complex_drift`, asserts `IssueLedger() is not None`, which no mutation of any key can turn red. The other surviving consumer, `tests/test_release_review_readiness.py`, is not core-marked (it is absent from the bare-run collection, F-05), so it does not guard the merge gate. So a mutation that, for example, made `fix_bar` return True for `high` risk, made `authorize_release` approve a headless run, made `SetupRepoStateMachine.rollback` keep applied keys, or made `VerifyExecutionCoordinator.mark_executed` admit an executor, would pass the routine suite.
- Scope: Restore ONE behavioral test module at its original path, `tests/test_migration_complex.py`, mined from `19313eed^:tests/test_migration_complex.py`, marked `core` so the routine gate reaches it; adapt the ONE recovered test broken by the later `kmmoca` change (`authorize_release` now requires a `readiness_report`, commit `a6c676874`); and extend it where the deleted file reached a key without asserting its result (`run_fix_bar`/`disposition_all` return value, `rollback` return value, `OperatorDatum.to_dict` via `build_artifact()["data"]`, and the `authorize_release` readiness refusal branches). It drives all 40 keys named in `x62jok`/`b1mx2w`: `fix_bar`, `IssueLedger.add`, `IssueLedger.disposition_all`, `IssueLedger.undispositioned`, `IssueLedger.personas_covered`, `ReleaseReviewCoordinator.__post_init__`, `ReleaseReviewCoordinator.enter_stage`, `ReleaseReviewCoordinator.stages_entered`, `ReleaseReviewCoordinator.run_fix_bar`, `ReleaseReviewCoordinator.integrate_fixes`, `ReleaseReviewCoordinator.authorize_release`, `ReleaseReviewCoordinator.can_finalize`, `detect_mode_drift`, `DiffInspection.out_of_scope_paths`, `DiffInspection.failed_checks`, `DiffInspection.is_clean`, `VerifyExecutionCoordinator.verify`, `VerifyExecutionCoordinator.can_mark_executed`, `VerifyExecutionCoordinator.mark_executed`, `AssessAllCoordinator.lanes`, `AssessAllCoordinator.eligibility`, `AssessAllCoordinator.assert_lanes_read_only`, `AssessAllCoordinator.claim_synthesis_writer`, `AssessAllCoordinator.synthesize`, `SetupRepoStateMachine.preflight`, `SetupRepoStateMachine.apply_change`, `SetupRepoStateMachine.rollback`, `OperatorDatum.__post_init__`, `OperatorDatum.is_labeled_unavailable`, `OperatorDatum.is_operator_owned`, `OperatorDatum.to_dict`, `RiskAwarePackage.add_datum`, `RiskAwarePackage.unavailable_data`, `RiskAwarePackage.consent_gate`, `RiskAwarePackage.assert_supportable_claim`, `RiskAwarePackage.build_artifact`, `build_incident_package`, `build_migrate_package`, `build_benchmark_package`, `assert_commands_in_manifest`. EXCLUDES any change to `agent_workflows/migration_complex.py` or any other production file; EXCLUDES asserting contracts of the non-`migration_complex` keys the same deleted file also reached (`run_gates.evaluate_gate`, `run_gates.GateDecision.is_approved`, `run_freeze.diff_requirements`, `run_state.is_legal_edge`, `orchestrate_isolation.analyze_concurrency_eligibility`, `verify_roles.check_role_action`, `verify_roles.check_self_verification`), which other `trimgap` items own; EXCLUDES core-marking or editing `tests/test_release_review_readiness.py`, which is a separate file with its own tier decision.
- Scope-Paths: tests/test_migration_complex.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: x62jok
- Set: trimgap
- Order: 8
- Highest E allocated: 05
- Author: opencode
- Id: pdemar
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored from backlog `x62jok`. Recovered the deleted module from `19313eed^`, ran it unchanged against HEAD `30f327577` (29 passed, 1 failed in 1.82s: the consent-gate table, because `authorize_release` now demands a readiness report), re-ran it with only that test's release surface given a minimal clean `ReleaseReadinessReport` (30 passed in 0.62s), and measured every added expected value below by direct call (Findings F-02 to F-04) before writing it.
- 2026-10-17 draft (opencode): created.

## Goal

Make every one of the 40 `unguarded-unreached` `migration_complex` keys from backlog `x62jok` reached by the routine (bare, core-tier) test run, through behavioral tests that call the code and assert on its return values, state and raised errors. Done means a `return-none`, `return-false`, `negate-return` or `raise` mutation (the operators `b1mx2w` assigned these keys) of any of them turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restored behavioral test module

- [ ] E-01 Create `tests/test_migration_complex.py` from `git show 19313eed^:tests/test_migration_complex.py`, adding `import pytest` and module-level `pytestmark = pytest.mark.core`, and amending the module docstring to name backlog `x62jok`, findings `b1mx2w`, plan `pdemar`, and the source `19313eed^`. Keep the stdlib `unittest.TestCase` classes as recovered (pytest collects them and applies the module mark). No subprocess, no filesystem writes: the only tree read is `assert_commands_in_manifest(SOURCE_WORKFLOWS)` over the in-repo workflows. Disposition rule if a recovered test OTHER than the one E-02 adapts fails at execution HEAD (none did at authoring, F-02, nor at review, F-06): do not mark this item performed until it is dispositioned. Record it in Findings and decide whether the current behavior is an intended change or a regression. For an intended change, cite the commit `git log -S` finds and adjust only that expectation. For a regression, file a `bug` backlog item with `aw backlog new ... --blocks-release next` (outside Scope-Paths, justified at finalize with `--scope-reason`) and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it, then continue.
  - Depends on: none
  - Expected outcome: the file exists and is selected by a bare `python3 -m pytest` (it carries the `core` marker); every recovered test passes except the consent-gate table E-02 adapts (one failure at authoring and review, re-derived at execution).
  - Execution state: pending

- [ ] E-02 Adapt `TheHumanConsentGate.test_no_handler_clears_either_gate_except_an_explicit_approval` to the `kmmoca` signature: add `from agent_workflows import release_readiness as RR` and a module-level helper returning `RR.ReleaseReadinessReport(gates=(RR.GateResult(name="full_suite", passed=True, detail="ok"),))`, and pass it as `readiness_report=` on the `authorize_release` surface ONLY (the `consent_gate` surface takes no such argument and must keep its recovered kwargs). Do not relax any row: headless must still raise naming `needs_input`, reject naming `rejected`, abort naming `aborted`, and approve must return `status == "approved"` with `is_approved` True. Add one sentence to the class docstring saying the clean report isolates the HUMAN gate from the readiness gates, which E-03 covers.
  - Depends on: E-01
  - Expected outcome: all 30 recovered tests pass.
  - Execution state: pending

- [ ] E-03 ADD a table-driven test class `ReleaseReadinessRefusals` covering the `authorize_release` readiness branches with `input_handler` returning `"approve"` and `interactive=True` on a fresh `ReleaseReviewCoordinator(mode=RELEASE_MODE_FULL)` per row, each row a list of `RR.GateResult` plus `waived_standing_gates`, and the expected outcome: no report (`readiness_report=None`) raises `ReleaseAuthorityError` containing `no Section 9 readiness report supplied`; waiving `full_suite` raises containing `cannot be waived`; a failing applicable `full_suite` raises containing `hard gate failure(s): full_suite`; a NOT-applicable `full_suite` raises containing `hard gate failure(s): full_suite`; `full_suite` passing plus a NOT-applicable `residual_risk` raises containing `hard gate failure(s): residual_risk` (both are `READINESS_INPUT_REQUIRED_GATES`, so absence of the attestation input is a hard failure, F-06); `full_suite` passing plus failing `residual_risk` raises containing `residual_risk gate is unsigned`; `full_suite` passing plus failing `ipd_lint` unwaived raises containing `unwaived standing gate failure(s): ipd_lint`; the same with `waived_standing_gates=("ipd_lint",)` returns a decision with `status == "approved"`; `full_suite` passing plus a NOT-applicable `leak_scan` returns `status == "approved"`. The approval rows are what make the refusal rows non-vacuous; say so in the failure message.
  - Depends on: E-02
  - Expected outcome: all rows pass.
  - Execution state: pending

- [ ] E-04 ADD result assertions where the recovered file reaches a key without checking its return value: in a new `ReturnedValuesAreTheState` class, (a) after adding two findings (`low`/not integrity and `high`/integrity) to a full-mode coordinator's ledger, `run_fix_bar()` returns a list equal to `c.ledger.findings` whose dispositions are the literal strings `"fix-now"` and `"escalate"` respectively (literals, as the recovered Fix Bar table already uses, so a rename of the emitted value fails); (b) after `preflight()` and approving changes `c1` then `c2`, `rollback()` returns `("c2", "c1")` and equals `tuple(sm.rolled_back)`; (c) a migrate package with `OperatorDatum(key="prod_schema", provenance=PROVENANCE_UNAVAILABLE)` builds an artifact whose `data` equals `[{"key": "prod_schema", "provenance": "operator-data-unavailable", "value": None}]` and whose `operator_data_unavailable` equals `["prod_schema"]`. Use the module's own constants (`MC.PROVENANCE_UNAVAILABLE`) for INPUTS and literal strings for every EMITTED value (dispositions, `provenance`), so a rename of an emitted value fails. Item (c) is the one that matters most: `OperatorDatum.to_dict` mutated to `return None` SURVIVES the recovered file (F-06), and (c) is what kills it.
  - Depends on: E-01
  - Expected outcome: all added assertions pass.
  - Execution state: pending

### Task group 2: proof that every key is guarded

- [ ] E-05 Run the full 40-key mutation sweep against the finished module: for each key in `b1mx2w` `## Rollup mutation results` rows `agent_workflows/migration_complex.py::*`, apply that row's assigned operator (`return-none`, `return-false`, `negate-return`, `raise`) as a scratch edit to `agent_workflows/migration_complex.py` at the top of the key's body, run `python3 -m pytest tests/test_migration_complex.py -o addopts="" -q -p no:randomly`, record KILLED (nonzero exit) or SURVIVED with the summary line, and restore the file before the next key. Keep any sweep driver script outside Scope-Paths in a gitignored scratch location (for example `.aw/state/`) and do not commit it. Then run the reach command in Required tests. A survivor is a defect in this plan's deliverable: add the missing assertion to `tests/test_migration_complex.py` and re-sweep that key; do not mark this item performed with a survivor outstanding.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: every one of the 40 keys is KILLED by its assigned operator (at review, against the recovered file plus the E-02 adaptation, 39 were killed and `OperatorDatum.to_dict@return-none` survived, F-06; E-04(c) closes it); `git diff agent_workflows/` is empty afterwards.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` managed block "TEST OUTCOMES, NOT CODE STRUCTURE"; `GUIDING_PRINCIPLES` P16). The recovered file has no `inspect`, `ast`, regex over source, or `assertIs` symbol-identity pins (checked with `rg "assertIs\(|inspect|import ast|getsource"` over `19313eed^:tests/test_migration_complex.py`: no match). `test_the_status_vocabulary_is_the_shared_one` asserts the VALUES of the public `run_gates.GATE_STATUS_*` vocabulary that a recorded gate decision is read from, which is an observable contract, so it is kept.
- THE ROUTINE GATE IS THE CORE TIER: a bare `python3 -m pytest` selects only `core`-marked tests (`conftest.pytest_collection_modifyitems`, IPD `hguae9`; marker declared in `pyproject.toml` `markers`). A restored module must carry `pytestmark = pytest.mark.core` to be reached by the merge gate.
- Sibling plans `syzi9i` (Order 11) and `33f8tn` (Order 9) of Set `trimgap` are the established shape: one core-marked behavioral test file, no production change, scratch mutation spot-checks reverted before commit.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Rollup mutation results` rows `agent_workflows/migration_complex.py::*`; `b1mx2w` `## Filing plan` group 8; `hpjj44` `## Derived properties` rows for each key | Exactly 40 keys, all `unreached` / `unguarded-unreached`, operators `return-none` (most), `return-false` (`OperatorDatum.is_labeled_unavailable`, `is_operator_owned`), `negate-return` (`fix_bar`) and `raise` (`__post_init__` x2, `enter_stage`, `preflight`, `claim_synthesis_writer`, `IssueLedger.add`, `assert_supportable_claim`, `assert_lanes_read_only`, `add_datum`). Each key's exclusive reach is attributed to `tests/test_migration_complex.py` (30 removed funcs). |
| F-02 | `git show 19313eed^:tests/test_migration_complex.py` copied to a scratch test path and run with `-o addopts=""` at HEAD `30f327577`, then deleted | `1 failed, 29 passed in 1.82s`. The failure is `TheHumanConsentGate.test_no_handler_clears_either_gate_except_an_explicit_approval`: every `authorize_release` row raised `release refused: no Section 9 readiness report supplied`. `rg` dates the requirement to commit `a6c676874` (`work(kmmoca)`), after the trim. |
| F-03 | the same scratch copy with only the `authorize_release` kwargs given a one-gate clean `ReleaseReadinessReport`, run with `--cov=agent_workflows.migration_complex --cov-report=term-missing`, then deleted | `30 passed in 0.62s`, coverage 89%. Remaining misses are in non-key helpers (`ReadinessVerification.to_dict`, `PersonaFinding.to_dict`, `IssueLedger.to_dict`, `last_verification`, `verify_readiness`, `finish`, `SetupChange.to_dict`, `DiffInspection.to_dict`, `CorrectiveArtifact.to_dict`), unreachable defensive raises (`run_fix_bar`, `integrate_fixes`, `assert_lanes_read_only` error lines), and the `authorize_release` readiness branches E-03 adds. Every key body executes. |
| F-04 | direct calls at HEAD `30f327577` | With an approving handler: a clean report returns `approved`; headless, reject and abort raise `release refused: no explicit human release authority (needs_input|rejected|aborted)`; waiving `full_suite` raises `gate 'full_suite' cannot be waived; ...`; failing or not-applicable `full_suite` raises `release refused: hard gate failure(s): full_suite`; failing `residual_risk` raises `release refused: residual_risk gate is unsigned in readiness report`; unwaived failing `ipd_lint` raises `release refused: unwaived standing gate failure(s): ipd_lint`; waived `ipd_lint` and not-applicable `leak_scan` each return `approved`. `OperatorDatum.to_dict` returns `{"key", "provenance", "value"}`; `rollback` returns `tuple(reversed(applied_changes))`; `MC.PROVENANCE_UNAVAILABLE` is `operator-data-unavailable`; a `low`/non-integrity plus `high`/integrity ledger dispositions to `fix-now`, `escalate`. |
| F-06 | plan review, HEAD `beb36ea1e`: recovered file plus the E-02 adaptation as a scratch test, then a scratch sweep applying each `b1mx2w` row's assigned operator to `agent_workflows/migration_complex.py` (restored after each key; `git diff agent_workflows/` empty afterwards); plus direct calls | Recovered file unchanged: `1 failed, 29 passed`; with the E-02 adaptation: `30 passed in 1.40s`. Sweep: 39 of 40 KILLED; `SURVIVED OperatorDatum.to_dict@return-none \| 30 passed in 0.55s`. Direct calls: a NOT-applicable `residual_risk` with passing `full_suite` raises `release refused: hard gate failure(s): residual_risk`; an empty report and a report with only a NOT-applicable `leak_scan` each return `approved` (not asserted: an empty report is out of this item's key contract). The E-04 (a) to (c) expected values reproduce exactly (`True ['fix-now', 'escalate']`; `('c2', 'c1') ('c2', 'c1')`; `[{'key': 'prod_schema', 'provenance': 'operator-data-unavailable', 'value': None}] ['prod_schema']`). |
| F-05 | `python3 -m pytest --collect-only -q` (bare, core tier) piped to `rg -c test_release_review_readiness` | No match: the surviving readiness test file is not in the routine selection, so its `authorize_release` assertions do not guard the merge gate. |

## Proposed changes (ordered, validatable)

1. E-01 restores the core-marked module.
2. E-02 adapts the one test broken by the `kmmoca` signature change without weakening any row.
3. E-03 covers the `authorize_release` readiness refusal and approval branches.
4. E-04 asserts the returned values of `run_fix_bar`, `rollback` and `OperatorDatum.to_dict`.
5. E-05 proves the Goal by sweeping every key with its assigned mutation operator.

## Deferred / out of scope (with reason)

- Non-`migration_complex` keys reached by the same deleted file (`run_gates.evaluate_gate`, `run_gates.GateDecision.is_approved`, `run_freeze.diff_requirements`, `run_state.is_legal_edge`, `orchestrate_isolation.analyze_concurrency_eligibility`, `verify_roles.check_role_action`, `verify_roles.check_self_verification`) are not this item's keys; the restored tests will incidentally execute them, but asserting their contracts belongs to the `trimgap` items filed for those modules.
  - Carrier-Declined: no work is owed by this plan; `b1mx2w` `## Filed items` routes those modules to their own backlog items.
- Core-marking `tests/test_release_review_readiness.py` (F-05) is not done here: it is a different file whose tier is its own decision, and E-03 restores routine coverage of the `authorize_release` branches this item owns.
  - Carrier-Declined: no `migration_complex` key is left unguarded by declining it.
- Non-key `to_dict` helpers and `verify_readiness` (F-03 misses) are not in the 40 keys and are not tested here.
  - Carrier-Declined: outside the item's key set.

## Scope check

- Over-scope: none. One test file is the only path declared and the only path changed. No production code changes.
- Under-scope: none. All 40 keys from F-01 are driven by E-01 to E-04 (F-03 shows every key body executed by the recovered file; E-03 and E-04 add assertions on results the recovered file left unchecked), and E-05 demonstrates each is guarded (F-06).

## Required tests / validation

- `python3 -m pytest tests/test_migration_complex.py -o addopts="" -v` passes, with the per-test list pasted.
- Bare `python3 -m pytest` passes with the new module included, with the summary line pasted.
- Reach: `python3 -m pytest tests/test_migration_complex.py -o addopts="" --cov=agent_workflows.migration_complex --cov-report=term-missing` shows the bodies of all 40 keys executed; paste the output.
- Mutation spot-checks: scratch, uncommitted edits to `agent_workflows/migration_complex.py`, one per V-item as listed there, each run against the new module with the failure pasted, then reverted with `git diff agent_workflows/` shown empty.
- Mutation sweep (E-05): all 40 keys with their `b1mx2w` assigned operators, one KILLED/SURVIVED line per key pasted.

## Spec / documentation sync

N/A: this plan adds tests only and changes no behavior, CLI surface, or contract described by a spec or user-facing document. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore at the original path, or a new `*_restored_behavior.py` name?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: original path, following `syzi9i` OQ-01. The file is restored nearly verbatim (F-02, F-03), so its original name keeps `git log --follow` and the `hpjj44` / `b1mx2w` citations pointing at a real file. The path is unoccupied at HEAD (`ls tests | rg migration` shows only `test_root_run_scratch_migration.py`).

### OQ-02: Adapt the broken consent-gate test, or drop its release surface?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: adapt (E-02). The test's value is that BOTH callers of the one gate scheme agree on every handler; dropping the release surface would lose exactly the cross-caller check its docstring argues for. Supplying a clean readiness report is the minimal change that keeps the human gate the only variable, and E-03 separately covers the readiness branches so nothing the new signature added goes untested.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git status --short` showing only `tests/test_migration_complex.py` added; paste the `tests/test_migration_complex.py: N` line from bare `python3 -m pytest --collect-only -q` (the core selection prints one `path: N` line per file, so `rg -c` would print 1, not N), with N matching the per-test list of the Required tests `-v` run; paste the bare `python3 -m pytest` summary line showing it passed. If the run prints `CORE TIER BUDGET EXCEEDED`, paste that too and the same run's line without the module, and report it rather than un-marking tests (a pre-existing overrun is tracked separately, backlog `o58dro`).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the `-v` output listing `test_no_handler_clears_either_gate_except_an_explicit_approval` and `test_the_status_vocabulary_is_the_shared_one` as PASSED; paste the failure produced by scratch-mutating `RiskAwarePackage.consent_gate` to `return None` and the failure produced by scratch-mutating `authorize_release`'s final `if not decision.is_approved:` to `if False:` (headless row must then fail), each reverted afterwards.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `-v` output listing every `ReleaseReadinessRefusals` test as PASSED; paste the failure produced by scratch-mutating `authorize_release` so the `if hard_failures:` refusal is skipped (`if False:`), each reverted afterwards.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `-v` output listing every `ReturnedValuesAreTheState` test as PASSED; paste the failures produced by scratch-mutating `SetupRepoStateMachine.rollback` to `return None`, `OperatorDatum.to_dict` to `return None` (its `b1mx2w` operator, which the recovered file alone does not kill) and to `return {}`, and `IssueLedger.disposition_all`'s emitted disposition literal (for example `DISPOSITION_ESCALATE` temporarily reassigned to `"escalated"`), each reverted afterwards, with a `ReturnedValuesAreTheState` test among the failures in each case.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the sweep output, one line per key naming the key, its operator, KILLED or SURVIVED, and the pytest summary line, covering all 40 `b1mx2w` keys with zero SURVIVED; paste the coverage `term-missing` output for `agent_workflows/migration_complex.py` from the Required tests reach command, with every listed miss outside the 40 key bodies; paste a final empty `git diff agent_workflows/` and `git status --short` showing no sweep script staged or tracked.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:

- Open questions: all resolved (OQ-01, OQ-02).
- Scope fence: `tests/test_migration_complex.py` is the only declared path. An out-of-scope edit (for example a gated `bug` backlog item filed under the E-01 disposition rule) is made and then justified at finalize (`--scope-reason`), not a reason to stop. Mutation spot-checks and the E-05 sweep are scratch edits to `agent_workflows/migration_complex.py` that must be reverted before commit and must be absent from the diff; any sweep script lives in a gitignored scratch location and is never committed.
- Honesty: you MUST paste the actual runner output for every test, coverage and mutation claim; never claim a result you did not run.
- Commit: commit only through `aw commit pdemar -- tests/test_migration_complex.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: the plan reaches `executed/` only after `aw ipd lint --phase pre-transition` conforms and every V-item carries pasted evidence with `Result: pass`. Under `aw oc run` / `aw agy run` the runner performs the finalize transition; a hand executor runs `aw ipd finalize pdemar` instead. Never hand-`git mv` the plan.
