# IPD: Restore the Order-preservation regression guard for aw group plans and aw rename plans

- Date: 2026-09-30
- Kind: child
- Concern: The Order-preservation regression guard for `aw group plans` and `aw rename plans` was deleted wholesale in 19313eed, so an Order regression in either verb now passes CI silently.
- Scope: Restore outcome coverage for Order preservation across both verbs and both `group` branches as a new test module; no production change expected.
- Scope-Paths: tests/test_plans_group_order_preservation.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: l8upzx
- Set: l8upzx
- Order: 1
- Highest E allocated: 06
- Author: agent
- Id: fv6kep

## Workflow history

- 2026-10-01 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED via /plan-review; PR-001 through PR-004 all FIXED, nothing left open or deferred. Reviewed in an isolated review lane at HEAD `54d43a38b`; `aw ipd lint --phase author --agent` reported `conforming` (exit 0, zero findings) BEFORE any edit and `--phase review-finalize` reports `conforming` after revision; the plan was committed and the tree clean, so no pre-review snapshot was taken. This plan's own first `- Kind:` bullet reads `child`, so the `IPD-S407` orchestrator row check does not apply. THE PREMISE IS CORRECT AND THE PLAN IS HONEST ABOUT BEING COVERAGE DEBT RATHER THAN A DEFECT. Re-derived independently: F-01 holds (`rg "PreservesOrderAndDate|PlansGroupPreservesOrder"` returns nothing and the file is absent); F-02 holds exactly (the deleted module carried 1 `PlansMvPreservesOrderAndDateTests` case and 7 `PlansGroupPreservesOrderTests` cases, all eight named correctly); F-03 holds (I implemented E-03's cases against live code and all four preservation behaviors pass, so `_preserved_order` and `plan_set_assign` are intact and this really is coverage restoration); F-04 holds precisely (a `Kind: child` at `- Order: 0` emits `IPD-M104: Order:` and at `- Order: 1` does not, while `IPD-H202` is present in BOTH, so E-05's presence-plus-absence assertion pair is sound); E-04's rename case reproduces end to end (a bare `--slug` rename of `20260810-demo-03-zzz111-old-slug.md` produced `20260810-demo-03-zzz111-new-slug.ipd.md` retaining `- Order: 3` and `- Date: 20260810`); and the `aw ipd lint` no-`--dir` convention reproduces (passing one exits 2 with "unrecognized arguments"). The plans-ORDER gap is genuine: no test file references `_preserved_order`, and the six existing Order tests in `test_group_verb_policy.py` are RESEARCH records, not plans. PR-001 IS THE FINDING THAT MATTERED: V-06's single negative control cannot falsify three of E-03's six cases, and the gate's "if the negative control does NOT fail, STOP" would therefore have halted a CORRECT execution. Measured by forcing `_preserved_order` to return 0: the three bare-regroup cases failed (`assert '0' == '1'`) but the orchestrator case PASSED, because its expected Order is 0 and the forced value is also 0, making it a tautology; and both explicit-`--order` cases passed because `plan_set_assign` resolves an explicit order without consulting the helper. E-06, V-06, Required tests and the gate's stop condition now name the falsifiable subset, and a second return-9 control was added so the orchestrator case is a real guard. PR-002: E-01's heavy fixture is unnecessary; measured, all four behaviors reproduce against nothing but `git init -q` plus direct file writes, which is exactly the shipped `temp_git_repo` fixture, so the `AW_HOME`/`register_or_update_project`/`config.json`/commit machinery was dropped and the existing `_seed_plan_record`/`_run_group_plans`/`_run_rename_plans` helper shapes are reused. PR-003: both halves of OQ-01's basis were wrong (that module's docstring is NOT setid-length-only and already hosts restored `19313eed` date coverage for these two verbs; `949enf` is `executed`, not pending), so the basis was replaced while the new-module decision stands on discoverability grounds. PR-004 added the gate's missing scope fence, open-questions statement and conditional finalize ownership. ONE THING TO KNOW AT EXECUTION: a bare suite run is not currently all-green, because of an order-dependent flake in `tests/test_runner_shared.py` that passes in isolation on a clean tree (F-08); E-06 and V-06 now demand a re-derived baseline rather than an absolute green bar. Full findings and three decisions in `.aw/records/reviews/20260930-l8upzx-01-fv6kep-restore-the-order-preservation-regression-guard.review.md`.
- 2026-09-30 draft (agent): created.
- 2026-09-30 to-review (agent): authored from backlog item `l8upzx`; baseline behavior and lint signals measured in-lane before writing.

## Goal

Restore the deleted regression coverage proving that a bare `aw group plans <id6> --set X [--rename]` and a bare `aw rename plans <id6> --slug X` PRESERVE each plan's existing Order rather than renumbering it from zero, while an EXPLICIT `--order` still renumbers sequentially. The production fix is intact; only its guard is gone, so this plan is coverage restoration and expects no behavior change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the guard as one new outcome-test module

- [ ] E-01 Create `tests/test_plans_group_order_preservation.py` with a pytest fixture that builds a plans repo in `tmp_path` and a seeding helper, then seed four plans: an orchestrator `aaa000` at Order 0, children `bbb222` at Order 1 and `ccc333` at Order 2, and a child `ddd444` with NO `- Order:` line whose filename carries the `04` slot.
  START FROM THE SHIPPED MINIMAL FIXTURE, NOT FROM THE DELETED MODULE'S HEAVY ONE (corrected at review, PR-002). `tests/test_group_verb_policy.py` already proves what this needs: its `temp_git_repo` fixture is just `subprocess.run(["git", "init", "-q"], cwd=tmp_path)` returning `tmp_path`, and its `_seed_plan_record` writes a plan file directly under `.aw/records/plans/pending/` with no project registration at all. MEASURED AT REVIEW: all four Order behaviors (bare `--rename`, bare metadata-only, the filename-slot fallback, and the orchestrator-at-zero) reproduce correctly against that minimal fixture, so a scoped `AW_HOME`, a `register_or_update_project` call, a `.aw/config/config.json` naming `DeliveryMode.TRACKED`/`RecordsBackend.REPOSITORY`, and committing the seeded files are all UNNECESSARY (F-09). Prefer REUSING `test_group_verb_policy.py`'s `_seed_plan_record`, `_run_group_plans` and `_run_rename_plans` shapes (copy them, or import them, but do not invent a third spelling); they already accept the `order`, `rename`, `apply` and `--dir` parameters every case here needs. Only add fixture machinery a measured failure actually forces.
  - Depends on: none
  - Expected outcome: the module imports and its fixture yields a seeded repo whose four plan files exist on disk; no test logic yet beyond the fixture being exercised. The fixture contains no `register_or_update_project` call and no `AW_HOME` manipulation unless a pasted failure justifies one.
  - Execution state: pending

- [ ] E-02 Drive every CLI assertion through `cli.main([...])` IN-PROCESS with `redirect_stdout`/`redirect_stderr`, following `tests/test_group_verb_policy.py`'s existing pattern, and do NOT reintroduce the deleted module's `subprocess.run([sys.executable, "-m", "agent_workflows", ...])` `_run_cli` helper.
  - Depends on: E-01
  - Expected outcome: the module contains no `subprocess` call that re-enters the `agent_workflows` CLI; `git init`/`git commit` subprocesses for fixture setup are fine.
  - Execution state: pending

- [ ] E-03 Add the `group` verb Order cases: (a) a bare `--rename` regroup of `bbb222` preserves `- Order: 1` AND the filename `01` slot; (b) a bare metadata-only regroup of `bbb222` preserves `- Order: 1` and leaves the filename untouched, asserting the front matter AGREES with the filename `NN`; (c) an explicit `--order 1` over `bbb222 ccc333 --rename` still renumbers sequentially to 1 and 2; (d) a bare `--rename` regroup of `ddd444` (no `- Order:` line) falls back to its filename slot and writes `- Order: 4`; (e) a bare `--rename` regroup of the orchestrator `aaa000` keeps it at `- Order: 0`; (f) an explicit `--order 0` over `ccc333 --rename` still lands at 0.
  - Depends on: E-02
  - Expected outcome: six `group` tests exist and pass, covering both branches plus the three must-not-break guards.
  - Execution state: pending

- [ ] E-04 Add the `rename` verb case restoring `PlansMvPreservesOrderAndDateTests`: a bare `aw rename plans zzz111 --slug new-slug --apply` on a seeded `20260810-demo-03-zzz111-old-slug.md` preserves both `- Order: 3` and `- Date: 20260810` and emits the `.ipd.md` facet, asserting the new name still starts `20260810-demo-03-zzz111-`.
  - Depends on: E-02
  - Expected outcome: one `rename` test exists and passes, so both sibling verbs' guarantees sit in one module.
  - Execution state: pending

- [ ] E-05 Add the end-to-end lint case: assert `aw ipd lint` does NOT report `IPD-M104: Order:` on a child after a bare regroup, asserting the ABSENCE of that code rather than a clean exit, and assert an unrelated `IPD-H202` IS present to prove the linter actually ran rather than the assertion passing on empty output.
  - Depends on: E-03
  - Expected outcome: one lint test exists and passes, proving the preserved Order is lint-valid for a `Kind: child`.
  - Execution state: pending

- [ ] E-06 Prove the restored guard is falsifiable: run the full fast suite bare (`python3 -m pytest`), then temporarily force `plans_refs._preserved_order` to return 0, confirm the EXPECTED SUBSET of the new module FAILS, and revert that edit so the production file is byte-unchanged.
  NAME THE FALSIFIABLE SUBSET EXPLICITLY, BECAUSE THREE OF E-03's SIX CASES ARE STRUCTURALLY INERT UNDER THIS CONTROL AND MUST NOT BE EXPECTED TO FAIL (measured at review, F-07). The cases that MUST go red are the three that consult `_preserved_order`: E-03(a) bare `--rename` of `bbb222`, E-03(b) bare metadata-only of `bbb222`, and E-03(d) the `ddd444` filename-slot fallback. The cases that MUST STAY GREEN are E-03(c) and E-03(f), because an explicit `--order` bypasses `_preserved_order` entirely, and E-03(e), because an orchestrator's expected Order is 0 and the forced return value is also 0, so that assertion is a TAUTOLOGY under the control and proves nothing. Record the green ones as expected-green rather than treating them as a failed control.
  THE ORCHESTRATOR CASE THEREFORE NEEDS A SECOND, DIFFERENT CONTROL to be a real guard. Force `_preserved_order` to return a nonzero sentinel (for example 9) instead, and confirm E-03(e) then FAILS; that is what distinguishes "the orchestrator stayed at 0 because the code preserved it" from "0 happened to be whatever the helper returned". Run both controls and paste both.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the full suite shows no NEW failure attributable to this module; under the return-0 control exactly E-03(a), E-03(b) and E-03(d) fail while E-03(c), E-03(e) and E-03(f) pass; under the return-9 control E-03(e) also fails; `git diff --stat agent_workflows/plans_refs.py` is empty afterward.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The production fix lives in `plans_refs._preserved_order` and is consumed by `plans_refs.plan_set_assign`, which resolves the Order ABOVE the `rename` split so both branches share it. Its docstring states the contract directly: `None` (flag omitted) "PRESERVES each plan's own Order", while an integer "renumbers the named plans SEQUENTIALLY from it (``start_order + i``)".
- `_preserved_order`'s tier order is front-matter `- Order:`, else the filename's `NN` via `_CLUSTERED_RE`, else 0, matching `plans_refs.run_mv`'s already-shipped fallback.
- `tests/test_group_verb_policy.py` is the only surviving test module for these verbs. CORRECTED AT REVIEW (PR-003): its docstring is NOT scoped to "setid length policy enforcement" alone; it reads "Outcome tests for setid length policy enforcement and date preservation across aw group and rename" and it already hosts restored `19313eed` DATE coverage for `aw group plans` and `aw rename plans`, plus six research-specific ORDER tests (F-10). The backlog's claim still holds for the PLANS ORDER invariant specifically, which nothing in that module or anywhere else asserts (verified: no test file references `_preserved_order`, and its plans tests assert only the filename DATE prefix). It already drives `cli.main` in-process with `redirect_stdout`/`redirect_stderr` and a two-line `temp_git_repo` `tmp_path` fixture, and it already carries `_seed_plan_record`, `_run_group_plans` and `_run_rename_plans`; that is the pattern E-02 adopts and the helper set E-01 reuses.
- The canonical in-tree import path for the fixture symbols is `from agent_workflows.project_registry import register_or_update_project` and `from agent_workflows.project_schema import DeliveryMode, RecordsBackend`, as used by `tests/test_record_producers.py`. The deleted module's `agent_workflows.config` / `agent_workflows.projects` spellings no longer resolve.
- `aw ipd lint` accepts a plain path and takes NO `--dir` flag; passing one exits 2 with "unrecognized arguments". Measured in-lane.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Both regression classes are gone from the tree. | `rg "PreservesOrderAndDate\|PlansGroupPreservesOrder"` over the worktree returns nothing, and `tests/test_awnaming_grammar_and_producers.py` does not exist. |
| F-02 | The deleted file carried exactly 8 relevant cases: 1 in `PlansMvPreservesOrderAndDateTests` and 7 in `PlansGroupPreservesOrderTests`. | `git show 19313eed^:tests/test_awnaming_grammar_and_producers.py` lists `test_mv_preserves_order_date_and_adds_facet`, `test_bare_rename_regroup_preserves_a_child_order`, `test_bare_metadata_only_regroup_preserves_a_child_order`, `test_explicit_order_still_renumbers_sequentially`, `test_bare_regroup_falls_back_to_the_filename_slot`, `test_bare_regroup_keeps_an_orchestrator_at_zero`, `test_explicit_order_zero_is_still_reachable`, `test_lint_no_longer_reports_ipd_m104_after_a_bare_regroup`. |
| F-03 | The production code is still correct, so this is coverage debt and not a live defect. | Measured in-lane by driving `cli.main` against a seeded temp repo: a bare `--rename` regroup of `bbb222` produced `20260908-newset-01-bbb222-probe-child-one.ipd.md` with `- Order: 1`; a bare metadata-only regroup of `ccc333` kept `- Order: 2`; the orchestrator `aaa000` stayed at `- Order: 0` with the `00` slot; `ddd444` (no `- Order:` line, filename `NN=04`) gained `- Order: 4`. |
| F-04 | The `IPD-M104: Order:` signal E-05 asserts on still exists and still fires for a child at Order 0. | Measured in-lane: linting a seeded `Kind: child` plan carrying `- Order: 0` emitted `IPD-M104: Order: child Order must be an integer >= 1`; the same plan at `- Order: 1` emitted no `IPD-M104: Order:` line while still emitting `IPD-H202` findings. |
| F-05 | The deleted module's subprocess CLI shape is a real hazard in a lane, not a hypothetical one. | Measured in-lane: an unpinned `python3 -c "import agent_workflows..."` resolved `agent_workflows.config` to the MAIN checkout's copy (`<main-checkout>/agent_workflows/config.py`) rather than to this worktree's. This reproduces backlog `ccbe60` and is why E-02 forbids the subprocess re-entry rather than merely preferring in-process. |
| F-06 | Overlap with `949enf` is bounded and non-conflicting, and the NON-CONFLICT CONCLUSION HOLDS even though this row's premise about that plan's state does not (see F-10). | `949enf` declares `- Scope-Paths: agent_workflows/plans_refs.py, tests/test_group_verb_policy.py`; this plan's only scope path is a NEW module, `tests/test_plans_group_order_preservation.py`, so the two share no file. |
| F-07 | ADDED AT REVIEW (PR-001). **V-06's NEGATIVE CONTROL CANNOT FALSIFY THREE OF E-03's SIX CASES, AND THE GATE'S STOP DIRECTIVE WOULD THEREFORE HAVE HALTED A CORRECT EXECUTION.** Implemented E-03's cases against live code, then forced `_preserved_order` to `return 0` and re-ran. Result: `3 failed, 1 passed` on the bare-regroup set, where the three failures were the `--rename` case (`assert '0' == '1'`), the metadata-only case, and the `ddd444` filename-slot case, and the ORCHESTRATOR case PASSED. It passes because its expected Order is 0 and the forced return value is also 0, so the assertion is a TAUTOLOGY under that control. Separately, the two explicit-`--order` cases (E-03(c), E-03(f)) were run under the same forced regression and BOTH passed, because `plans_refs.plan_set_assign` resolves an explicit `--order` without consulting `_preserved_order` at all. So exactly three of six cases are falsifiable by this control, and the gate's "if the negative control does NOT fail, STOP" reads as all-six-must-fail. A SECOND CONTROL FIXES THE ORCHESTRATOR CASE: forcing a nonzero sentinel (9) makes E-03(e) meaningful. | A probe module implementing E-03's six cases; a return-0 edit to `_preserved_order` and the pasted `3 failed, 1 passed` plus the two explicit-`--order` cases passing; `git diff --stat agent_workflows/plans_refs.py` empty after restore from a pre-edit copy |
| F-08 | ADDED AT REVIEW (PR-001). **A BARE SUITE RUN IS NOT CURRENTLY ALL-GREEN, so E-06's "the full suite passes" bar would fail on a cause this plan does not own.** Measured on a CLEAN tree (`git status --porcelain` empty, no edits): `1 failed, 3648 passed, 2 skipped, 3 warnings in 146.10s`, the failure being `tests/test_runner_shared.py::DanglingCommitSearchTests::test_07_real_corpus_arm_conditional`. Re-run ALONE on the same clean tree it PASSES (`1 passed in 5.82s`), so it is an order-dependent flake in a module this plan does not touch, surfaced by the configured `-p randomly` ordering. E-06 and V-06 now require a re-derived baseline and per-node attribution rather than an absolute green bar. | bare `python3 -m pytest` on a clean tree at review HEAD `54d43a38b`; the named node re-run in isolation with `-o addopts=""` passing; `git status --porcelain` empty before and after |
| F-09 | ADDED AT REVIEW (PR-002). **E-01's HEAVY FIXTURE IS UNNECESSARY; THE SHIPPED MINIMAL ONE SUFFICES, which the plan could have measured and did not.** E-01 prescribes a scoped `AW_HOME`, a `register_or_update_project` call, a `.aw/config/config.json` naming `DeliveryMode.TRACKED`/`RecordsBackend.REPOSITORY`, and committing the seeded files. MEASURED: with nothing but `git init -q` in `tmp_path` and plan files written directly under `.aw/records/plans/pending/`, all four Order behaviors reproduce correctly through `cli.main` (bare `--rename` preserved `- Order: 1` and the `01` slot; bare metadata-only preserved `- Order: 1`; `ddd444` with no `- Order:` line gained `- Order: 4` from its filename slot; the orchestrator kept `- Order: 0` and the `00` slot), reported `4 passed in 2.23s`. That minimal shape is exactly `tests/test_group_verb_policy.py`'s shipped `temp_git_repo` fixture plus its `_seed_plan_record`, so the simpler form is both sufficient AND already conventional here. | a probe module using only `git init -q` plus direct file writes, running E-03's four preservation cases green; read of `test_group_verb_policy.temp_git_repo` (two lines) and `_seed_plan_record` (no registration, no commit) |
| F-10 | ADDED AT REVIEW (PR-003). **`949enf` IS `executed`, NOT PENDING, AND `tests/test_group_verb_policy.py` ALREADY HOSTS RESTORED `19313eed` COVERAGE FOR THESE TWO VERBS, so both halves of OQ-01's stated basis are wrong.** The file resolves to `.aw/records/plans/executed/20260929-j84jg3-01-949enf-...ipd.md` carrying `- Status: executed`, so it claims no file going forward and OQ-01's "keeps this plan's `Scope-Paths` disjoint from pending plan `949enf`" argument is void. And that module's docstring is NOT scoped to setid length alone: it reads "Outcome tests for setid length policy enforcement and date preservation across aw group and rename" and states it "Also covers date preservation for `aw group plans` and `aw rename plans` ... restoring date regression coverage deleted in `19313eed` (IPD 949enf)". It already contains `_seed_plan_record`, `_run_group_plans`, `_run_rename_plans` and five plans-specific date tests, plus six research Order tests. The new-module DECISION survives on different grounds (discoverability of a 1000-line grab-bag module is what lost the coverage in the first place), which OQ-01 now states. | `ls .aw/records/plans/*/*949enf*` resolving under `executed/` and its `- Status: executed`; the module docstring quoted; its `def test_`/helper census listing the plans date tests and the three helpers |

## Proposed changes (ordered, validatable)

1. Add one new test module, `tests/test_plans_group_order_preservation.py`, holding a shared seeded-repo fixture (E-01) driven entirely in-process (E-02).
2. Restore the six `group` Order cases, covering the `--rename` branch, the metadata-only branch, and the three must-not-break guards (E-03).
3. Restore the single `rename` Order-and-Date case so both sibling verbs are guarded in one place (E-04).
4. Restore the end-to-end lint case asserting the absence of `IPD-M104: Order:` plus the presence of an unrelated finding (E-05).

No production change is proposed. If one proves necessary during execution, that is a separate finding to file rather than to absorb here (per the backlog's SCOPE note).

## Deferred / out of scope (with reason)

- Any change to `agent_workflows/plans_refs.py`: out of scope, because the fix is intact (F-03). (The secondary reason originally given, that `949enf` claims the file, no longer applies: that plan is `executed`, F-10. The primary reason stands on its own.)
  - Carrier-Declined: NOTHING TO CARRY, because there is no defect here. F-03 measured all four Order paths behaving correctly against live code, so this row records the ABSENCE of a production change rather than deferred work. Filing a carrier would assert a `plans_refs.py` defect that does not exist and would invite a later agent to "fix" correct code. The backlog item's own SCOPE note sets the policy this follows: "No production change is expected; if one proves necessary, that is a separate finding."
- Restoring the other classes deleted from `tests/test_awnaming_grammar_and_producers.py` (`GrammarRegexTests`, `ClusteredNameTests`, `ProducerTests`, `SetidLengthAuthoringGuardTests`): out of scope. Only the Order invariant is this backlog item's subject.
  - Carrier-Declined: OUT OF THIS ITEM'S SUBJECT AND PARTLY ALREADY COVERED. `SetidLengthAuthoringGuardTests`' subject survives in `tests/test_group_verb_policy.py`, whose docstring scopes it to exactly that policy, so carrying it would duplicate live coverage. The remaining three classes guard the naming GRAMMAR and the record PRODUCERS, which are different invariants with no measured gap behind them; 19313eed deleted 318 files, so a carrier naming "the rest of that commit" would be an unbounded obligation rather than a durable owner. A specific gap found later should be filed on its own measurement.
- The DATE half of the `rename` guard as a standalone concern: `949enf` restores it for both verbs.
  - Carrier: 949enf
  - Carrier-Evidence: .aw/records/plans/executed/20260929-j84jg3-01-949enf-resolve-a-plan-filename-date-from-the-name-before-inventing.ipd.md

## Scope check

- Over-scope: none. The single scope path is a new test module.
- Under-scope: the 7 deleted `group`-class cases map onto E-03 (6) and E-05 (1), and the 1 deleted `rename` case maps onto E-04, so all 8 are accounted for. No production file is touched, which is intended per F-03.

## Required tests / validation

- `python3 -m pytest tests/test_plans_group_order_preservation.py` run bare, with the actual `N passed` summary pasted as evidence.
- The full suite, `python3 -m pytest`, run bare per the execution contract (no added flags), to prove no regression elsewhere. RE-DERIVE THE BASELINE ON A CLEAN TREE BEFORE EDITING and judge on the DELTA of failing node ids: a bare run at review was NOT all-green (`1 failed, 3648 passed, 2 skipped`) because of an order-dependent flake in `tests/test_runner_shared.py` that passes in isolation (F-08). Do not inherit that result either; measure, then attribute every failing node against a named E-item.
- TWO negative controls proving the restored guard can actually FAIL, because one control cannot falsify all six cases (F-07). Control A: force `plans_refs._preserved_order` to return 0, and confirm E-03(a), E-03(b) and E-03(d) fail while E-03(c), E-03(e) and E-03(f) correctly PASS (the explicit-`--order` cases never reach the helper, and the orchestrator's expected 0 equals the forced 0, making that assertion a tautology under this control). Control B: force it to return 9, and confirm E-03(e) then fails. Revert after each. A guard that cannot fail is not a guard, and naming WHICH cases each control falsifies is what keeps an executor from reading three correct passes as a broken control.

## Spec / documentation sync

N/A with reason: this plan restores test coverage for an already-specified behavior and changes no public contract, no CLI surface, and no `.spec.md` file. `_preserved_order`'s own docstring already records the contract being guarded.

## Open questions

### OQ-01: Should the restored cases live in a new module or be folded into tests/test_group_verb_policy.py?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED IN FAVOR OF A NEW MODULE, but the original basis was measurably wrong in both halves and is replaced here (corrected at review, PR-003). WHAT WAS WRONG. First, that module's docstring is NOT scoped to setid length alone; it reads "Outcome tests for setid length policy enforcement and date preservation across aw group and rename" and explicitly says it "Also covers date preservation for `aw group plans` and `aw rename plans` ... restoring date regression coverage deleted in `19313eed` (IPD 949enf)". So it is ALREADY a mixed-subject module that already hosts restored `19313eed` coverage for these exact two verbs, and it already contains `_seed_plan_record`, `_run_group_plans` and `_run_rename_plans`. Second, `949enf` is `- Status: executed`, not pending, so it claims nothing going forward and the disjoint-`Scope-Paths` argument does not apply (F-10). WHY A NEW MODULE IS STILL THE RIGHT ANSWER, on grounds that hold: that module additionally carries six research-specific Order tests and the dynamically parametrized backend sweep, so it is already large and multi-subject, and a plans-Order module is independently nameable and discoverable, which matters because the deleted coverage was lost precisely by being buried in a 1000-line grab-bag module. The honest cost, recorded rather than hidden: a reader looking for "aw group plans Order" now has two plausible homes, so E-01 reuses that module's helper shapes to keep the two consistent, and this plan does NOT move or duplicate its date tests.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest tests/test_plans_group_order_preservation.py --collect-only -q` output showing the module collects, plus the fixture and seeding-helper bodies showing git init, the `.aw/records/plans/pending/` tree, and the four seeded plans with their Orders (`aaa000`=0, `bbb222`=1, `ccc333`=2, `ddd444`=none with filename `NN=04`). State explicitly whether the fixture needed a scoped `AW_HOME` or a `register_or_update_project` call: measured at review it does NOT (F-09), so if either is present, paste the failure that forced it rather than carrying it over from the deleted module. Also state which helper shapes were reused from `tests/test_group_verb_policy.py` (PR-002).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the output of a search for CLI re-entry in the new module (for example `rg -n "subprocess|cli.main" tests/test_plans_group_order_preservation.py`), showing every CLI assertion goes through `cli.main` and that no `subprocess` invocation names `-m agent_workflows`. Any `subprocess` hits must be git fixture setup only, and the paste must make that visible.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest tests/test_plans_group_order_preservation.py -o addopts="" -v` output naming all six `group` tests as passed, and for each of the two branch cases quote the asserted values: the `--rename` case showing `- Order: 1` with the filename `01` slot and `newset`, and the metadata-only case showing `- Order: 1` with the filename unchanged. Also show the explicit-`--order` case asserting 1 and 2, the fallback case asserting `- Order: 4`, the orchestrator case asserting `- Order: 0` with the `00` slot, and the explicit `--order 0` case asserting 0.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `rename` test as passed from the same `-v` run, and quote its assertions showing the renamed file still starts `20260810-demo-03-zzz111-`, ends `.ipd.md`, and retains both `- Order: 3` and `- Date: 20260810`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the lint test as passed, and quote its two assertions: the absence of `IPD-M104: Order:` and the presence of `IPD-H202`. State explicitly that the test asserts on absence of that code rather than on exit status, since a probe plan legitimately emits unrelated structural findings and an exit-0 assertion could never pass.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste (a) the bare `python3 -m pytest` summary line, reconciled against a baseline YOU measured on a clean tree BEFORE editing, explaining any failing node id against a named E-item; note that at review a bare run reported `1 failed, 3648 passed, 2 skipped` where the single failure was `tests/test_runner_shared.py::DanglingCommitSearchTests::test_07_real_corpus_arm_conditional`, which PASSES in isolation on a clean tree and is an order-dependent flake in an unrelated module (F-08), so re-derive rather than inherit either that result or the plan's original "full suite passes" bar. Paste (b) the RETURN-0 control: the diff of forcing `plans_refs._preserved_order` to return 0, and pytest output showing EXACTLY E-03(a), E-03(b) and E-03(d) FAILING while E-03(c), E-03(e) and E-03(f) PASS; state explicitly that those three passing is the EXPECTED and correct result, not a broken control (F-07). Paste (c) the RETURN-9 control showing E-03(e) FAILING, which is the only control under which the orchestrator assertion is not a tautology. Paste (d) `git diff --stat agent_workflows/plans_refs.py` (expected empty) confirming both forced changes were reverted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Open questions: OQ-01 is `- Status: resolved` and `- Blocking: no`, so nothing here waits on a human decision. Its stated BASIS was corrected at review (both halves were factually wrong, F-10) while its DECISION, a new module, is unchanged and now rests on discoverability grounds.

This plan is `- Status: reviewed` with `- Readiness: go-pending-approval`, both written by `/plan-review` on 2026-10-01. `reviewed` records that the review happened; it is NOT approval, and execution requires explicit human sign-off recorded with `aw ipd set approved fv6kep --by-human`.

Scope fence (a DECLARATION so the runner can reconcile afterwards, not a stop directive): the executor creates and edits only `tests/test_plans_group_order_preservation.py`. `agent_workflows/plans_refs.py` is TEMPORARILY edited twice by V-06's two negative controls and MUST be restored byte-identical; it is not a scope path and must never enter a commit. `tests/test_group_verb_policy.py` is NOT edited: its helper shapes are reused by copying, not by modifying it. If the work genuinely requires an edit outside the declared set, MAKE it and JUSTIFY it: `aw ipd finalize` refuses to complete without a `--scope-reason` per out-of-scope path and a `--scope-ack` per declared-but-unmodified path. Do STOP and report only for a genuinely unsafe condition: a concurrent edit to a file you are changing that cannot be safely combined, or a prerequisite symbol (`plans_refs._preserved_order`, `plans_refs.plan_set_assign`, `cli.main`) that is absent or has changed shape.

Execution contract: commit ONLY `tests/test_plans_group_order_preservation.py` via `aw commit fv6kep -- tests/test_plans_group_order_preservation.py`, never `git add -A` and never `--no-verify`, and do not push. Verify the staged set with `git diff --cached --name-only` before committing, since this checkout is shared. Run the suite BARE (`python3 -m pytest`) and PASTE THE ACTUAL RUNNER OUTPUT; a claim of passing tests without pasted output is a contract violation, and so is marking a `V-*` complete from the matching `E-*` checkmark rather than from evidence inspected in a separate pass. Do not modify `agent_workflows/plans_refs.py` permanently: V-06's controls require temporary edits, which MUST be reverted (confirm with an empty `git diff --stat agent_workflows/plans_refs.py`) and must never enter a commit.

Post-gate lifecycle move: this plan is terminal only when `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence with `Result: verified`. The terminal transition to `.aw/records/plans/executed/` then happens through the tooled lifecycle and NEVER by hand: if a runner (`aw oc run` / `aw agy run`) is driving this plan the runner OWNS the finalize and the executor must not call it; if the plan is executed by hand, the executor runs `aw ipd finalize` itself.

STOP CONDITION, STATED PRECISELY SO IT CANNOT MISFIRE (corrected at review, PR-001): STOP if the V-06 control-A run does not fail E-03(a), E-03(b) and E-03(d), or if the control-B run does not fail E-03(e). Do NOT stop merely because E-03(c), E-03(e) or E-03(f) pass under control A; measured at review, those three CANNOT fail under that control and their passing is the correct result (F-07). The original wording ("if the negative control does NOT fail, STOP") read as all-six-must-fail and would have halted a correct execution.
