# IPD: Spend the frozen retry budget on a retryable failure so the correction layer stops being dormant

- Date: 2026-09-08
- Kind: child
- Concern: Spec `25kzda` 2.1's correction budget is fully built, fully tested, range-validated, operator-settable and frozen into run state, and then never spent. `plan_retry` and `retry_budget_remaining` have ZERO production callers: they appear only in `run_recovery.py` (their definitions) and `tests/test_run_recovery_cli.py`, and neither host runner imports the module for anything but the range check. So a failed run item today gets zero automatic correction attempts, and an operator who passes `--retry-budget 5` gets a value that is validated, resolved, frozen into `state.json`, and read by nothing.
- Scope: Wire CONSUMPTION only. On a RETRYABLE failure class, spend the frozen budget through the shipped helpers: issue a correction attempt, invalidate stale evidence, and escalate on exhaustion. Non-retryable classes stay non-retryable at every budget, and the frozen budget must not change on resume. Adds no flag, no new budget semantics, and no repository-policy tier.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_retry_consumption.py
- Item-Dependencies: none
- Status: to-review
- Set: retrywire
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: xipfy1
- From-Backlog: trjfyy
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `trjfyy`, inheriting its `Blocks-Release: next` gate. THE ITEM'S SEQUENCING GATE IS NOW SATISFIED, which is the main change since it was filed: it says "Gate this behind `uyeko5`, which owns the flag and the frozen value; wiring consumption first would have nothing to read the operator's budget from." `uyeko5` is now EXECUTED (`.aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md`, `- Status: executed`), so the flag, its precedence and the frozen value all exist and this plan has something to read. Consequently `Item-Dependencies: none` is correct rather than an oversight. THE DORMANCY CLAIM STILL HOLDS, re-verified at HEAD `a2e0438a` by symbol search rather than by trusting the item's line numbers: `plan_retry` (`run_recovery.py:269`) and `retry_budget_remaining` (`:415`) appear ONLY in their own module and in `tests/test_run_recovery_cli.py`. ONE PART OF THE ITEM IS NOW STALE AND IS RECORDED SO NOBODY RE-DERIVES IT: the item says the three symbols including `validate_retry_budget` have zero production callers, but `validate_retry_budget` (`:136`) IS now called in production, by `runner_shared.resolve_retry_budget` (`:1764`), which `uyeko5` added. So the RANGE CHECK is wired and only the two SPENDING helpers remain dormant; that narrows this plan to consumption and is why the range bound is explicitly out of scope. Also verified the frozen value genuinely exists to be read: `freeze_run_policy_flags` resolves `--retry-budget` to its effective integer via `resolve_retry_budget` (`runner_shared.py:1836-1837`) precisely so no later reader has to re-resolve it, which is exactly the property a consumption loop needs on resume.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the correction budget do something. An operator who sets a budget should see a failed item get bounded, evidence-invalidating correction attempts, and see escalation when the budget runs out, instead of a single failure and a silently unused number in `state.json`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: decide what may be retried, before wiring anything

- [ ] E-01 Define the RETRYABLE failure classes explicitly, as a shared table in `runner_shared.py`, and derive nothing implicitly. The runners' disposition vocabulary is `executed|substantially-complete|partial|blocked|failed-safely` (`oc_runipd.py:4837`), and `failed-safely` is assigned both to a genuine driver error and, per the comment at `oc_runipd.py:5852-5853`, to cases the classifier can conflate with a DELIBERATE OPERATOR STOP. That conflation is the single most important hazard here: retrying an operator's deliberate stop would spend paid model turns fighting the operator. So the table must be an ALLOWLIST of retryable classes, never a denylist of non-retryable ones, and a class the classifier is known to conflate must be excluded until it can be told apart. State per class WHY it is or is not retryable.
  - Depends on: none
  - Expected outcome: one shared allowlist naming each retryable class with its justification; a deliberate operator stop is provably NOT in it.
  - Execution state: pending

- [ ] E-02 Read the FROZEN budget, never the live `args`, so a resumed run cannot change its own budget mid-flight. `freeze_run_policy_flags` (`runner_shared.py`, the `retry_budget` branch at `:1836-1837`) resolves the flag to its effective integer at freeze time expressly so "the frozen state holds the value that will actually be used (never a bare `None` that a later reader has to re-resolve, and re-resolve differently)". Consume that frozen integer. Do NOT call `resolve_retry_budget` again in the loop: it reads `args`, and the docstring above it records that re-reading `args` on every resume "would silently change meaning between the first turn and the last". Note `0` IS A LEGAL BUDGET meaning no retries (`run_recovery.py:69-70` warns a falsy check must not treat it as unset), so the guard must be `is None`-shaped, not truthiness-shaped.
  - Depends on: E-01
  - Expected outcome: the loop reads the frozen integer; a `--retry-budget 0` run performs zero retries rather than falling back to the default 2; a resumed run uses the originally frozen value.
  - Execution state: pending

### Task group 2: spend it through the shipped helpers

- [ ] E-03 Spend budget through `plan_retry` (`run_recovery.py:269`) rather than counting attempts in the runner, so the ledger-backed semantics the helpers already implement and test are the ones that ship. `plan_retry` appends a retry record and does NOT delete the failed attempt (pinned by `tests/test_run_recovery_cli.py:124-131`), is idempotent on a repeated `idempotency_key` (`:133-143`), and raises `RetryLimitExceededError` (`run_recovery.py:87`) once the budget is exhausted (`tests/test_run_recovery_cli.py:145-160`). Use `retry_budget_remaining` (`:415`) to report what is left rather than recomputing it. DO NOT reimplement any of that in the runner: the whole reason this layer is dormant rather than missing is that the semantics already exist and only the call site is absent.
  - Depends on: E-02
  - Expected outcome: a retryable failure produces a retry record via `plan_retry`, the failed attempt is preserved, and remaining budget is reported from `retry_budget_remaining`.
  - Execution state: pending

- [ ] E-04 Issue a CORRECTION packet containing only the FAILED predicates, and invalidate stale evidence, per spec `25kzda` 5.5 / 4.2 / 5.2 as the item requires. A correction attempt is not a re-run of the whole item: re-sending the full task would both cost more and invite the model to redo work that passed. Equally, evidence captured by the FAILED attempt must not be allowed to satisfy the retried attempt, or a correction could inherit the very evidence that was wrong. Locate the evidence-invalidation seam by symbol in `run_recovery`/`run_evidence` rather than writing a second invalidation path, and if no such seam exists, say so and stop rather than inventing one silently.
  - Depends on: E-03
  - Expected outcome: the correction packet names only failed predicates; evidence from the failed attempt cannot satisfy the retry; both demonstrated on a fixture.
  - Execution state: pending

- [ ] E-05 ESCALATE on exhaustion instead of looping or silently giving up. When `plan_retry` raises `RetryLimitExceededError`, the item must reach a terminal disposition that says the budget was spent and how many attempts it bought, so an operator can tell "failed once" from "failed after two corrections". Record it where a read surface can find it: the run summary and `aw runs` both key off per-item state, and a reason that lives only in `events.jsonl` reaches no surface (measured on the adjacent orchestrator-deferral path, where exactly that happens). If reviewed plan `r2i1b1`'s shared refusal record has landed by execution time, USE IT rather than adding a parallel field; check first.
  - Depends on: E-03
  - Expected outcome: budget exhaustion yields a terminal disposition naming the attempts spent, visible on a read surface, with no unbounded loop.
  - Execution state: pending

### Task group 3: prove the boundaries, not just the happy path

- [ ] E-06 Test the matrix with FIXTURES, never against live run records: `.aw/records/runs/` is gitignored with zero tracked files, and `tests/test_run_viewer.py:1-30` documents that 23 tests reading it fail in a fresh checkout, so a test keyed to live runs is unrunnable in CI and in every lane worktree. Cover, as separate cases: a retryable failure at budget 2 gets exactly 2 correction attempts then escalates; the SAME failure at budget 0 gets none and escalates immediately; a NON-retryable class gets none at ANY budget including 10 (the item's explicit requirement); a deliberate operator stop is never retried; a resumed run keeps its originally frozen budget even if a different `--retry-budget` is passed to the resume; and `plan_retry`'s idempotency means a repeated attempt key does not double-spend. Assert the budget-2 case FAILS against HEAD `a2e0438a`, so the test proves the wiring rather than restating current behavior.
  - Depends on: E-04, E-05
  - Expected outcome: six fixture cases passing in a bare worktree; the budget-2 case fails before the change.
  - Execution state: pending

- [ ] E-07 Confirm both hosts share the wiring by OBJECT IDENTITY, not by grep, per the anti-re-fork discipline the `rununify` work established. Both runners must reach the same consumption function rather than each carrying a near-copy, which is the exact drift `run_recovery`'s own history warns about and which `plan_readiness` was created to end. Verify `agy_runipd` gained no new direct import from `oc_runipd` (the anti-divergence guard in `tests/test_runner_item_dependencies.py::AntiDivergenceGuardTests` polices this class of coupling), and that the shared symbol lives in `runner_shared.py`.
  - Depends on: E-06
  - Expected outcome: an identity assertion showing both hosts resolve to the same function object; no new cross-driver import.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The budget layer is DORMANT, not missing: `plan_retry` (`run_recovery.py:269`), `retry_budget_remaining` (`:415`), `RetryLimitExceededError` (`:87`) and `validate_retry_budget` (`:136`) all exist and are tested. Only the spending call site is absent.
- `validate_retry_budget` IS now wired in production, via `runner_shared.resolve_retry_budget` (`:1764`), which `uyeko5` added. The item's claim that all three symbols have zero callers is stale for this one; the range bound is therefore out of scope here.
- `DEFAULT_RETRY_LIMIT` is 2 and the reasoning is recorded at `run_recovery.py:53-64`: a retry is a CORRECTION attempt, "a retry cannot turn failure into success by mere repetition", so a corrector still failing after two passes usually faces a plan defect and a third attempt mostly buys another paid turn. That is the cost model this plan must respect.
- `0` is a LEGAL budget meaning no retries, and `run_recovery.py:69-70` explicitly warns that a falsy check must not treat it as unset.
- The MIDDLE precedence tier (repository policy) is deliberately NOT implemented and deliberately NOT faked: `resolve_retry_budget`'s docstring says so and points at backlog `dh3us4`. Do not add it here.
- The frozen value is resolved at freeze time on purpose (`runner_shared.py:1836-1837`), so a resumed run reads a stable integer. Re-reading `args` per turn is the documented mistake.
- `failed-safely` is used both for a real driver error and for cases the classifier can confuse with a deliberate operator stop (`oc_runipd.py:5852-5853`). That is why E-01 is an allowlist.
- Both hosts are expected to share such logic through `runner_shared.py`, and an anti-divergence guard tests for re-forking.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE SEQUENCING GATE IS SATISFIED: `uyeko5`, which the item names as the prerequisite owning the flag and the frozen value, has EXECUTED. | `.aw/records/plans/executed/20260903-runflags-01-uyeko5-...ipd.md`, `- Status: executed` |
| F-2 | The two spending helpers are still dormant at HEAD: `plan_retry` and `retry_budget_remaining` appear only in `run_recovery.py` and `tests/test_run_recovery_cli.py`. | symbol search at `a2e0438a` |
| F-3 | ONE CLAIM IN THE ITEM IS STALE, which narrows this plan: `validate_retry_budget` now HAS a production caller, `runner_shared.resolve_retry_budget`. | `run_recovery.py:136` called at `runner_shared.py:1764` |
| F-4 | The frozen budget exists to be read, resolved to an effective integer at freeze time specifically so no later reader re-resolves it. | `runner_shared.py:1836-1837` and the docstring above it |
| F-5 | `0` is a legal budget and must not be treated as unset by a truthiness check. | `run_recovery.py:69-70` |
| F-6 | The repository-policy tier is deliberately absent and tracked elsewhere, so this plan must not add it. | `resolve_retry_budget` docstring; backlog `dh3us4` (`blocked`) |
| F-7 | `failed-safely` conflates a driver error with a possible deliberate operator stop, so a denylist approach would retry an operator's stop. | `oc_runipd.py:5852-5853`, `:5883`, `:5905` |
| F-8 | The helpers' semantics are already pinned by tests, so the runner must call them rather than reimplement: retry preserves the failed attempt, is idempotent per key, and raises on exhaustion. | `tests/test_run_recovery_cli.py:124-131`, `:133-143`, `:145-160`, `:215-227` |
| F-9 | The cost model is explicit and argues for a small budget: a correction attempt is a paid model turn and repetition alone cannot fix a plan defect. | `run_recovery.py:53-64` |
| F-10 | The adjacent items are genuinely distinct and neither closes this: `dh3us4` covers only the policy tier and PRESUMES consumption exists, and `sq61qd` (executed) added only the range check and its own history says the helpers "remain DORMANT". | backlog `dh3us4`; `.aw/records/plans/executed/...sq61qd...ipd.md` |
| F-11 | A reason recorded only in `events.jsonl` reaches no read surface, which is why E-05 requires per-item state. | measured on the orchestrator-deferral path: no surface greps `orchestrator-deferred` |

## Proposed changes (ordered, validatable)

1. Define the retryable-class ALLOWLIST with per-class justification (E-01).
2. Read the frozen budget, treating 0 as legal (E-02).
3. Spend it through `plan_retry`/`retry_budget_remaining` (E-03).
4. Send a correction packet of only failed predicates and invalidate stale evidence (E-04).
5. Escalate on exhaustion to a terminal disposition visible on a read surface (E-05).
6. Test the six boundary cases with fixtures (E-06).
7. Assert both hosts share the wiring by object identity (E-07).

## Deferred / out of scope (with reason)

- THE REPOSITORY-POLICY PRECEDENCE TIER. Owned by backlog `dh3us4` (`blocked` on `uyeko5`), and `resolve_retry_budget` deliberately does not fake it. Adding it here would take over another item's scope.
- THE 0..10 RANGE BOUND. Already shipped by executed plan `sq61qd` and already reached at parse time through `resolve_retry_budget`. Re-checking it in the loop is the off-by-one the existing comment warns about.
- THE `--retry-budget` FLAG, ITS PRECEDENCE AND ITS FREEZING. Shipped by executed `uyeko5`. This plan consumes that value and adds no flag.
- ROUTING `CORRECTION_REQUIRED` BACK TO RUNNABLE. That is backlog `wyw936` (open, `Blocks-Release: next`), which the item calls "adjacent but distinct" and notes never mentions the budget helpers. The two should be SEQUENCED together (a correction route with no budget is unbounded; a budget with no correction route is dead), and OQ-01 carries that to the reviewer rather than absorbing another open item's scope.
- INTEGRATION-RETRY COUNTS. The item is emphatic and correct: re-attempting a MERGE costs a `git status` and a `git merge-tree` and repetition genuinely can succeed, so it is a different knob with a much larger default. Nothing here changes it.

## Scope check

- Over-scope: none. Two runner modules, the shared module they both use, and one new test module.
- Under-scope: the policy tier, the range bound, the flag surface, `wyw936`'s verdict routing, and integration retries are all left alone (see Deferred).

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m pytest tests/test_retry_consumption.py tests/test_run_recovery_cli.py` for the focused surface. The existing recovery tests must pass UNMODIFIED: they pin the helper semantics this plan consumes.
- The six boundary cases from E-06, each with its own pasted result.
- Exit codes measured UNPIPED (`cmd >/dev/null 2>&1; echo $?`).

## Spec / documentation sync

Spec `25kzda` (`aw run deterministic run and verify`, `- Status: approved`) sections 2.1, 4.1, 4.2, 5.2 and 5.5 already SPECIFY this behavior, so this plan IMPLEMENTS the spec rather than amending it and no `.spec.md` file is declared in `Scope-Paths`. Two obligations follow. FIRST, the executor must READ those sections and reconcile the implementation against them, reporting any place the spec demands something this plan does not do (a spec that describes dormant behavior is exactly how this item arose). SECOND, `--retry-budget`'s `--help` text currently discloses that the middle precedence tier is unimplemented; if wiring consumption changes what that flag observably does, the help text must be updated in the same change so the flag stops describing a dormant layer. If the executor concludes the spec itself is wrong about the correction protocol, declare the spec path in `Scope-Paths` and justify the amendment BEFORE editing, per the plan-may-amend-a-spec rule.

## Open questions

### OQ-01: Must `wyw936` land with or before this plan, since a correction route and a correction budget are only useful together?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: BLOCKING, and the item states the mutual dependency in its own words: "a correction route with no budget is unbounded and a budget with no correction route is dead." Verified `wyw936` is still `open` with no plan, and its fail-open is live (the verdict gate downgrades only on `BLOCKED`/`NOT CONFORMING`, so the schema's own `CORRECTION_REQUIRED` is recorded `verified` today). THE CONCRETE RISK if this lands alone: the budget becomes spendable on failures the runner already classifies as failures, while the verdict path that SHOULD trigger a correction still reports success, so the most valuable trigger stays disconnected. THREE OPTIONS. (a) Land `wyw936` first, then this: cleanest, but `wyw936` is not mine to graduate. (b) Land this alone, accepting that corrections fire only on failure classes, not on `CORRECTION_REQUIRED`: still a real improvement over zero retries, and safe, because the allowlist bounds what may be retried. (c) Merge the two: takes over another open item's scope, which the graduation contract forbids. RECOMMENDED: (b) if the maintainer wants the value sooner, (a) if they want the full loop at once. Either way the allowlist in E-01 keeps this safe on its own.

### OQ-02: Should a correction attempt be visible as a separate ATTEMPT in the run summary, or folded into the item's single row?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: RESOLVABLE FROM THE CODE, recorded so the answer is deliberate. The run summary and `execution-report.md` already render an `Attempts` count per item, and `plan_retry` deliberately PRESERVES the failed attempt rather than replacing it, so the data supports showing both. RECOMMENDATION: let the attempt count reflect corrections (it already would, since a retry appends a record) and put the ESCALATION reason in the per-item refusal surface from E-05, rather than adding a new column. Confirm by rendering a fixture run before choosing, since a column change is a contract change for anything parsing that table.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the allowlist source with the per-class justification comments, AND paste a table of every disposition value in the runners' vocabulary with its retryable verdict. Explicitly show that a deliberate operator stop is NOT retryable, naming the code path that distinguishes it (or, if it cannot be distinguished, showing that the conflated class is excluded).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a fixture run's `state.json` frozen `retry_budget` value and a trace or print showing the loop READ that value rather than calling `resolve_retry_budget`. Paste the `--retry-budget 0` case proving zero retries occur (not the default 2), which is what proves the `is None` guard rather than a truthiness check.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the retry records produced for one retryable failure showing the FAILED attempt still present alongside the retry, the value returned by `retry_budget_remaining` after each spend, and a grep proving the runner calls the helpers rather than counting attempts itself.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the correction packet actually sent, showing it names ONLY the failed predicates and not the passing ones, and paste a demonstration that evidence captured by the failed attempt does NOT satisfy the retried attempt (for example the invalidation call and the retried attempt re-collecting evidence). Name the invalidation seam by symbol.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the exhaustion case end to end: the `RetryLimitExceededError` being raised, the resulting terminal disposition, the recorded attempts-spent count, and that fact appearing on a READ surface (paste the run summary or `aw runs` output). State whether `r2i1b1` had landed and which record shape was used.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste all six cases with their results: budget 2 gives exactly 2 attempts then escalates; budget 0 gives none; a non-retryable class gives none at budget 10; a deliberate stop is never retried; a resume keeps the frozen budget despite a different flag value; a repeated idempotency key does not double-spend. ALSO paste the budget-2 case FAILING against pre-change code, and proof the tests are fixture-based (paste the fixture setup and a run with `.aw/records/runs/` absent).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste an object-identity assertion (`oc_mod.<symbol> is agy_mod.<symbol>` or equivalent through `runner_shared`) and its True result; paste a grep showing `agy_runipd` gained no new import from `oc_runipd`; paste the `tests/test_runner_item_dependencies.py` result. Paste the bare `python3 -m pytest` summary line and compare it to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened. OQ-01 is BLOCKING and is a sequencing decision about a sibling item (`wyw936`) that a reviewer must settle before execution.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line; do not claim a pass that was not run. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. NOTE THE CONTENTION AND THE COST: `oc_runipd.py` and `agy_runipd.py` are the most heavily edited files in the repository, so re-locate every citation BY SYMBOL at execution time and never by the line numbers above; and be aware this plan makes the runner spend PAID MODEL TURNS on corrections, so a wiring error is expensive rather than merely wrong, which is why E-01's allowlist and E-06's budget-0 case come before anything else. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
