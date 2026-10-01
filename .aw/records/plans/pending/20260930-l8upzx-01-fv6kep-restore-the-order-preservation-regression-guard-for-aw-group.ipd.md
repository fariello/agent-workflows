# IPD: Restore the Order-preservation regression guard for aw group plans and aw rename plans

- Date: 2026-09-30
- Kind: child
- Concern: The Order-preservation regression guard for `aw group plans` and `aw rename plans` was deleted wholesale in 19313eed, so an Order regression in either verb now passes CI silently.
- Scope: Restore outcome coverage for Order preservation across both verbs and both `group` branches as a new test module; no production change expected.
- Scope-Paths: tests/test_plans_group_order_preservation.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: medium
- From-Backlog: l8upzx
- Set: l8upzx
- Order: 1
- Highest E allocated: 06
- Author: agent
- Id: fv6kep

## Workflow history

- 2026-09-30 draft (agent): created.
- 2026-09-30 to-review (agent): authored from backlog item `l8upzx`; baseline behavior and lint signals measured in-lane before writing.

## Goal

Restore the deleted regression coverage proving that a bare `aw group plans <id6> --set X [--rename]` and a bare `aw rename plans <id6> --slug X` PRESERVE each plan's existing Order rather than renumbering it from zero, while an EXPLICIT `--order` still renumbers sequentially. The production fix is intact; only its guard is gone, so this plan is coverage restoration and expects no behavior change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the guard as one new outcome-test module

- [ ] E-01 Create `tests/test_plans_group_order_preservation.py` with a pytest fixture that builds a repository-backend AW project in `tmp_path` (git init, `.aw/records/plans/pending/`, a scoped `AW_HOME`, `register_or_update_project`, and a `.aw/config/config.json` naming `DeliveryMode.TRACKED` / `RecordsBackend.REPOSITORY`), seeding four plans: an orchestrator `aaa000` at Order 0, children `bbb222` at Order 1 and `ccc333` at Order 2, and a child `ddd444` with NO `- Order:` line whose filename carries the `04` slot.
  - Depends on: none
  - Expected outcome: the module imports and its fixture yields a seeded repo whose four plan files are committed; no test logic yet beyond the fixture being exercised.
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

- [ ] E-06 Prove the restored guard is falsifiable: run the full fast suite bare (`python3 -m pytest`), then temporarily force `plans_refs._preserved_order` to return 0, confirm the new module FAILS, and revert that edit so the production file is byte-unchanged.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the full suite passes with the new module in place; the forced-regression run fails on at least the two bare-regroup cases; `git diff --stat agent_workflows/plans_refs.py` is empty afterward.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The production fix lives in `plans_refs._preserved_order` and is consumed by `plans_refs.plan_set_assign`, which resolves the Order ABOVE the `rename` split so both branches share it. Its docstring states the contract directly: `None` (flag omitted) "PRESERVES each plan's own Order", while an integer "renumbers the named plans SEQUENTIALLY from it (``start_order + i``)".
- `_preserved_order`'s tier order is front-matter `- Order:`, else the filename's `NN` via `_CLUSTERED_RE`, else 0, matching `plans_refs.run_mv`'s already-shipped fallback.
- `tests/test_group_verb_policy.py` is the only surviving test module for these verbs, and its docstring scopes it to "setid length policy enforcement" alone, confirming the backlog's claim that the Order invariant is uncovered. It already drives `cli.main` in-process with `redirect_stdout`/`redirect_stderr` and a `temp_git_repo` `tmp_path` fixture, which is the pattern E-02 adopts.
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
| F-06 | Overlap with pending plan `949enf` is bounded and non-conflicting. | `949enf` declares `- Scope-Paths: agent_workflows/plans_refs.py, tests/test_group_verb_policy.py`; this plan's only scope path is a NEW module, `tests/test_plans_group_order_preservation.py`, so the two share no file. |

## Proposed changes (ordered, validatable)

1. Add one new test module, `tests/test_plans_group_order_preservation.py`, holding a shared seeded-repo fixture (E-01) driven entirely in-process (E-02).
2. Restore the six `group` Order cases, covering the `--rename` branch, the metadata-only branch, and the three must-not-break guards (E-03).
3. Restore the single `rename` Order-and-Date case so both sibling verbs are guarded in one place (E-04).
4. Restore the end-to-end lint case asserting the absence of `IPD-M104: Order:` plus the presence of an unrelated finding (E-05).

No production change is proposed. If one proves necessary during execution, that is a separate finding to file rather than to absorb here (per the backlog's SCOPE note).

## Deferred / out of scope (with reason)

- Any change to `agent_workflows/plans_refs.py`: out of scope, because the fix is intact (F-03) and the file is already claimed by pending plan `949enf` (F-06).
  - Carrier-Declined: NOTHING TO CARRY, because there is no defect here. F-03 measured all four Order paths behaving correctly against live code, so this row records the ABSENCE of a production change rather than deferred work. Filing a carrier would assert a `plans_refs.py` defect that does not exist and would invite a later agent to "fix" correct code. The backlog item's own SCOPE note sets the policy this follows: "No production change is expected; if one proves necessary, that is a separate finding."
- Restoring the other classes deleted from `tests/test_awnaming_grammar_and_producers.py` (`GrammarRegexTests`, `ClusteredNameTests`, `ProducerTests`, `SetidLengthAuthoringGuardTests`): out of scope. Only the Order invariant is this backlog item's subject.
  - Carrier-Declined: OUT OF THIS ITEM'S SUBJECT AND PARTLY ALREADY COVERED. `SetidLengthAuthoringGuardTests`' subject survives in `tests/test_group_verb_policy.py`, whose docstring scopes it to exactly that policy, so carrying it would duplicate live coverage. The remaining three classes guard the naming GRAMMAR and the record PRODUCERS, which are different invariants with no measured gap behind them; 19313eed deleted 318 files, so a carrier naming "the rest of that commit" would be an unbounded obligation rather than a durable owner. A specific gap found later should be filed on its own measurement.
- The DATE half of the `rename` guard as a standalone concern: `949enf` restores it for both verbs.
  - Carrier: 949enf

## Scope check

- Over-scope: none. The single scope path is a new test module.
- Under-scope: the 7 deleted `group`-class cases map onto E-03 (6) and E-05 (1), and the 1 deleted `rename` case maps onto E-04, so all 8 are accounted for. No production file is touched, which is intended per F-03.

## Required tests / validation

- `python3 -m pytest tests/test_plans_group_order_preservation.py` run bare, with the actual `N passed` summary pasted as evidence.
- The full suite, `python3 -m pytest`, run bare per the execution contract (no added flags), to prove no regression elsewhere.
- A negative control proving the restored guard can actually FAIL: temporarily force `plans_refs._preserved_order` to return 0, confirm the new module fails, then revert. A guard that cannot fail is not a guard, and this is the one check that distinguishes restored coverage from a test that merely passes.

## Spec / documentation sync

N/A with reason: this plan restores test coverage for an already-specified behavior and changes no public contract, no CLI surface, and no `.spec.md` file. `_preserved_order`'s own docstring already records the contract being guarded.

## Open questions

### OQ-01: Should the restored cases live in a new module or be folded into tests/test_group_verb_policy.py?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Resolved from repository evidence in favor of a NEW module. `tests/test_group_verb_policy.py`'s docstring scopes it to "setid length policy enforcement across all aw group backends" and it iterates the backend registry dynamically for every group-capable type; the Order invariant is plans-specific and would dilute that module's stated subject. A new module also keeps this plan's `Scope-Paths` disjoint from pending plan `949enf`, which already claims that file (F-06).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest tests/test_plans_group_order_preservation.py --collect-only -q` output showing the module collects, plus the fixture body showing git init, the `.aw/records/plans/pending/` tree, a scoped `AW_HOME`, the `register_or_update_project` call, and the four seeded plans with their Orders (`aaa000`=0, `bbb222`=1, `ccc333`=2, `ddd444`=none with filename `NN=04`).
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
  - Required evidence: paste (a) the bare `python3 -m pytest` summary line showing the full fast suite passing, and (b) the negative control: the diff or description of forcing `plans_refs._preserved_order` to return 0, the resulting FAILING pytest output for the new module naming at least the two bare-regroup cases, and confirmation via `git diff --stat agent_workflows/plans_refs.py` (expected empty) that the forced change was reverted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY `tests/test_plans_group_order_preservation.py` via `aw commit <this plan> -- tests/test_plans_group_order_preservation.py`, never `git add -A` and never `--no-verify`, and do not push. Verify the staged set with `git diff --cached --name-only` before committing, since this checkout is shared. Do not modify `agent_workflows/plans_refs.py`: the negative control in V-06 requires a temporary edit, which MUST be reverted and must never enter a commit.

Post-gate lifecycle move: this plan is terminal only when `aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence with `Result: verified`. Then move it to `.aw/records/plans/executed/` through the tooled transition (`aw ipd set executed <plan>`), never by hand. If the negative control in V-06 does NOT fail, STOP: the restored guard is inert and the plan must not be marked executed.
