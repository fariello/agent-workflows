# IPD: Verify and lock behavioral coverage for run_analytics_findings build, causal and results keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `6ntz8v` (Set `trimgap`, group 10 of the `wo21z5` `## Filing plan`) carries three production keys of `agent_workflows/run_analytics_findings.py` that the `wo21z5` budget probe classified `unguarded`: `assert_no_causal_language` (operator `raise`), `build_finding` (operator `return-none`) and `findings_from_results` (operator `return-none`). The probe ran at baseline HEAD `f3afece9` (2026-10-17 18:14), where the surviving selection did not kill those mutants and only the deleted control file `tests/test_run_analytics_findings.py` did. That control file was restored later the same evening by plan `ivap17` (commit `0f8ca64d7`, 2026-10-17 20:59, NOT an ancestor of `f3afece9`), so the probe's verdict predates the restore. Re-probing at authoring HEAD `390d90f0` (F-02) shows all three mutants are now KILLED, including under the routine `-m core` selection. The residual risk this plan closes is that the verdict is unrecorded: the backlog item still reads as an open gap.
- Scope: Re-run the three `wo21z5` mutation probes (plus the opposite-polarity `return-none` probe of `assert_no_causal_language`) against `tests/test_run_analytics_findings.py` under the routine `core` selection at execution HEAD, and record the verdicts in this plan. ONLY IF a probe SURVIVES at execution HEAD, add one behavioral test to `tests/test_run_analytics_findings.py` that calls the surviving function and asserts on its returned value or raised `FindingRefusal`. EXCLUDES any production-code change; EXCLUDES other `run_analytics_findings.py` keys (`format_findings_report`, `price_era_paradox_finding`, `detect_pooled_era_comparison` are owned by executed `ivap17`); EXCLUDES other test files.
- Scope-Paths: tests/test_run_analytics_findings.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 6ntz8v
- Set: trimgap
- Order: 24
- Highest E allocated: 03
- Author: opencode
- Id: 92tzo6

## Workflow history
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (commit-before-reprobe, baseline_failing and base sha, real class names, satisfiable budget bar, execution contract); four probes re-run killed at 2aa1e2fd3 (F-04)

- 2026-10-23 to-review (opencode): authored from backlog `6ntz8v`. Confirmed `ivap17` restored the control file after the `wo21z5` baseline (`git merge-base --is-ancestor 0f8ca64d7 f3afece925` false), then re-ran `tools/mutation_probe.py` for all three keys at HEAD `390d90f0`; every mutant was killed (F-02). The plan is therefore verification-first with a conditional restore step.
- 2026-10-23 draft (opencode): created.

## Goal

Prove, with recorded mutation-probe output at execution HEAD, that an early-return or raise mutation of each of the three `6ntz8v` keys turns a routine core-tier test red, and add a behavioral test only for any key where that is not true. Done means all three keys have a pasted `verdict: killed` under `-m core`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-probe at execution HEAD

- [ ] E-01 Run `python3 tools/mutation_probe.py --op <op> agent_workflows/run_analytics_findings.py::<key> -- -o addopts= -q -p no:randomly -m core tests/test_run_analytics_findings.py` for these four (key, op) pairs: (`assert_no_causal_language`, `raise`), (`assert_no_causal_language`, `return-none`), (`build_finding`, `return-none`), (`findings_from_results`, `return-none`). `tools/mutation_probe.py` mutates inside its own isolated worktree, so the checkout's production code is never modified; it probes committed `HEAD` only. Before the first probe, record `git rev-parse HEAD` as `<base>`. Record each `head:`, `verdict:`, `baseline_failing:` and `mutant_failing:` line in Findings. A probe with `baseline_failing` above 0 or `verdict:` other than `killed`/`survived` (for example `error` or `invalid`) is not a result: record it, fix the cause if it is in scope, and re-run.
  - Depends on: none
  - Expected outcome: four probe outputs recorded, each with `baseline_failing: 0` and a `killed` or `survived` verdict; at authoring and again at review all four were `verdict: killed` (F-02, F-04).
  - Execution state: pending

### Task group 2: conditional restore

- [ ] E-02 For every (key, op) pair E-01 reports `survived`, add one test to `tests/test_run_analytics_findings.py` in the class that already covers that function (`ContractRefusalTests` for `build_finding`, `CausalLanguageTests` for `assert_no_causal_language`, `CannotDetermineFindingTests` for `findings_from_results`), which calls the function and asserts on its returned `Finding`/list contents or on the raised `FindingRefusal` message; mine the body from `git show 19313eed^:tests/test_run_analytics_findings.py` where an equivalent test exists. Commit the test file through `aw commit 92tzo6 -- tests/test_run_analytics_findings.py` BEFORE re-running the E-01 probe for that pair, because the probe sees only committed `HEAD`. If E-01 reported `killed` for all four pairs, make NO file change and record "no survivor; no edit" in Findings.
  - Depends on: E-01
  - Expected outcome: either no diff to `tests/test_run_analytics_findings.py`, or a diff adding only tests, after which the re-probe of each previously surviving pair reports `verdict: killed`.
  - Execution state: pending

- [ ] E-03 Run the routine bare gate `python3 -m pytest` and confirm it passes with `tests/test_run_analytics_findings.py` in the core selection. The conftest budget check (`conftest.pytest_sessionfinish`) sets exit 1 on a wall-time overrun only when enforced (12 or more CPUs, host not oversubscribed, `AW_CORE_BUDGET_ENFORCE` not `0`) and otherwise prints a warning; the tier was already over 30s on this host before this plan (sibling `3wkrng` F-06 measured 59.22s, not enforced). So paste any `CORE TIER BUDGET EXCEEDED` block verbatim and do not count it against this item unless E-02 added a test that is among the block's listed slowest tests.
  - Depends on: E-02
  - Expected outcome: the bare run exits 0 and its summary line shows `passed` with no `failed` or `error`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): any test E-02 adds calls the function and asserts on outputs or raised refusals; no source reading.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`). `tests/test_run_analytics_findings.py` carries a module-level `pytestmark = pytest.mark.core`, so every test in it is in the routine gate, and a new test added there inherits the marking.
- Probe tool: `tools/mutation_probe.py` (`--op {return-none,return-true,return-false,negate-return,raise}`, selection after `--`) is the same tool `wo21z5` used, so the re-probe is directly comparable to the original verdict.
- Sibling precedent: executed `ivap17` restored this file for keys `format_findings_report`, `price_era_paradox_finding`, `detect_pooled_era_comparison` and validated with reverted mutation spot-checks.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `wo21z5` `## Baseline` (`head: f3afece9...`), `## Budget probe results` rows for the three keys (`files`, 59 collected, survivor `survived`, control `killed`, `unguarded`); `git log -1 0f8ca64d7` (2026-10-17 20:59, `work(ivap17)`); `git merge-base --is-ancestor 0f8ca64d7 f3afece925` returns false | The probe's surviving selection excluded the control file because it did not exist at `f3afece9`; `ivap17` restored it afterwards. The `unguarded` verdict describes a tree that no longer exists. |
| F-02 | `tools/mutation_probe.py` at HEAD `390d90f0`, selection `-o addopts= -q -p no:randomly [-m core] tests/test_run_analytics_findings.py` | `assert_no_causal_language` `raise`: `verdict: killed`, `mutant_failing: 11` (without `-m core`; the file is wholly core-marked so the selection is identical). `assert_no_causal_language` `return-none` with `-m core`: `killed`, `mutant_failing: 2`. `build_finding` `return-none`: `killed`, `mutant_failing: 17`. `findings_from_results` `return-none` with `-m core`: `killed`, `mutant_failing: 1` (`CannotDetermineFindingTests::test_every_non_computed_result_becomes_exactly_one_finding`). |
| F-03 | Same as F-02 | `findings_from_results` is killed by exactly one test, so it is the thinnest of the three; E-02 is the remedy only if that single test is lost before execution. |
| F-04 | review re-probe at HEAD `2aa1e2fd3`, same four (key, op) pairs, selection `-o addopts= -q -p no:randomly -m core tests/test_run_analytics_findings.py` | All four `verdict: killed`, `baseline_failing: 0`: `assert_no_causal_language` `raise` 11, `assert_no_causal_language` `return-none` 2 (`CausalLanguageTests::test_every_human_readable_field_is_scanned_and_named_in_the_refusal`, `CausalLanguageTests::test_the_check_FIRES_on_a_planted_causal_claim`), `build_finding` `return-none` 17, `findings_from_results` `return-none` 1 (`CannotDetermineFindingTests::test_every_non_computed_result_becomes_exactly_one_finding`). F-02 reproduces. The file's classes are `ContractRefusalTests`, `CausalLanguageTests`, `CannotDetermineFindingTests`, `PriceEraParadoxTests`, `RankingStabilityTests`, `ReportTests`. |

## Proposed changes (ordered, validatable)

1. E-01 re-probes all three keys at execution HEAD under `-m core`.
2. E-02 adds a behavioral test only for a surviving key; otherwise no file change.
3. E-03 confirms the bare core gate passes.

## Deferred / out of scope (with reason)

- Adding redundant tests for `findings_from_results` beyond the single killing test.
  - Carrier-Declined: no work is owed; one killing test meets the item's remedy ("restore behavioral coverage") and the repository's trim direction disfavors redundant tests.

## Scope check

- Over-scope: none. Only `tests/test_run_analytics_findings.py` is declared, and it changes only if a probe survives.
- Under-scope: none. All three backlog keys are probed by E-01 and remedied by E-02 when needed.

## Required tests / validation

- The four `tools/mutation_probe.py` runs of E-01 (and any E-02 re-probes), full `head`/`target`/`operator`/`verdict`/`mutant_failing` output pasted.
- `python3 -m pytest -o addopts="" -v tests/test_run_analytics_findings.py` passes, per-test list pasted.
- Bare `python3 -m pytest` summary line and exit status pasted, plus any budget block verbatim.
- `git diff --stat <base>..HEAD -- agent_workflows/` and `git diff --stat -- agent_workflows/` both empty (no production change committed or left in the tree).

## Spec / documentation sync

N/A: tests only (at most); no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore tests from `19313eed^` even though the keys are already guarded?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. `ivap17` already restored `tests/test_run_analytics_findings.py` from `19313eed^` (F-01) and the re-probe kills every mutant (F-02); restoring again would duplicate tests. E-02 keeps a conditional remedy in case the tree changes before execution.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the full output of all four `tools/mutation_probe.py` runs (produced by `tools/mutation_probe.py` itself, E-01), each showing `head:`, `selection:` containing `-m core tests/test_run_analytics_findings.py`, `baseline_failing: 0`, its `verdict:` line and its `newly_failing` list; paste `<base>` and `git diff --stat <base>..HEAD -- agent_workflows/` plus `git diff --stat -- agent_workflows/`, both showing no change.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: either paste `git diff --stat tests/test_run_analytics_findings.py` showing no change together with the Findings line "no survivor; no edit", or paste the diff adding only test functions, the `aw commit` output for it, and the re-probe output with a `head:` at or after that commit showing `baseline_failing: 0` and `verdict: killed` for each previously surviving pair, with a `newly_failing` list naming the added test, and `python3 -m pytest -o addopts="" -v tests/test_run_analytics_findings.py` with every test PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the bare `python3 -m pytest` summary line showing `passed` and no `failed` or `error`, its exit status, and any `CORE TIER BUDGET EXCEEDED` block verbatim (including any "not enforced" reason).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit 92tzo6 -- tests/test_run_analytics_findings.py` (only if E-02 changed it; plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL probe and runner output into each `V-*`; never claim a mutant was killed or a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which is the expected case here when E-02 makes no edit). No production file under `agent_workflows/` may change. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize 92tzo6` itself.
