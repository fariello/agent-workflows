# IPD: bounds-check the retry budget at the spec's 0..10 on the shipped helper

- Date: 2026-09-03
- Kind: child
- Concern: Spec `25kzda` 2.1 fixes the retry budget's legal range at 0 through 10 inclusive, and NOTHING enforces it. `plan_retry` (`run_recovery.py:213`) and `retry_budget_remaining` (`:355`) both accept `limit: int = DEFAULT_RETRY_LIMIT` (`:62`, currently `2`) and neither validates the value: `plan_retry(limit=-1)` would make every step instantly budget-exhausted, and `limit=10_000` would license an unbounded correction loop, which is exactly what a bounded retry exists to prevent. This is the SMALLEST and most clearly-correct slice of the retired-bundle parent `wlxkoz`, and it was stranded there behind a 13-code verbatim transcription task it has nothing to do with (parent F10, review round 2 PR-004).
- Scope: Add ONLY the 0..10 inclusive RANGE validation, at the boundary where the value enters the two shipped helpers, plus tests at the boundaries. Excludes changing `DEFAULT_RETRY_LIMIT` (resolved to `2` by maintainer ruling 2026-08-31; do NOT re-litigate and do NOT "restore" 3), excludes the 13 `RUN-*` codes (Order 1, `wlxkoz`), excludes `--unverifiable-ok` (Order 2, `zub5f1`), excludes adding a CLI flag (none exists today), and excludes touching `run_evidence.py`.
- Scope-Paths: agent_workflows/run_recovery.py, tests/test_run_recovery_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: runcodes
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: sq61qd
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT OUT OF `wlxkoz` (Order 1) at the maintainer's direction, discharging that plan's F10 / review-round-2 PR-004, which found it bundled three independent concerns and must be split before execution. This child carries the parent's E-04 VERBATIM in intent: the 0..10 range check only. It is deliberately the smallest slice, and that is the point of the split - the parent's own finding was that "if an executor fumbles the 13 verbatim transcriptions, the whole plan strands on its lane and the trivially safe bounds check strands with it". MEASURED AT AUTHORING rather than inherited: `DEFAULT_RETRY_LIMIT: int = 2` is at `run_recovery.py:62` (already spec-aligned, so E-01 must not touch it); `plan_retry` at `:213` takes `limit: int = DEFAULT_RETRY_LIMIT` at `:219`; `retry_budget_remaining` at `:355-356` takes the same; NEITHER validates. Also verified there is NO `--retry-budget` CLI flag in `run_cli.py` or `cli.py`, so "at entry" means the helpers' parameter and this plan must NOT invent a flag. The parent's E-05 test-ownership question is settled for this child: it touches ONLY `tests/test_run_recovery_cli.py`, never `tests/test_run_evidence_completion.py`, so it cannot collide with its siblings over a shared test file.

## Goal

Make an out-of-range retry budget impossible to pass, so a bounded retry is actually bounded, without changing the default or any other behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: validate the range at the boundary where the value enters

- [ ] E-01 Add the spec's 0..10 inclusive range validation to the two shipped entry points in `agent_workflows/run_recovery.py`: `plan_retry` (`:213`, `limit` at `:219`) and `retry_budget_remaining` (`:355`). Reject below 0 and above 10 with a clear message naming the offending value and the legal range. RE-READ BOTH SIGNATURES BEFORE EDITING and locate them BY SYMBOL: the parent plan's citations for these same symbols had already drifted ~15 lines once (parent PR-003), so a line number here is orientation, not an address.
  FOLLOW THE MODULE'S OWN REFUSAL CONVENTION rather than inventing one: `run_recovery.py` already defines typed errors and raises them (`RetryLimitExceededError` at `:77` with its message composed at `:84`, and `NoRetryableStateError`). A `ValueError` would be inconsistent with a module whose every other refusal is a named domain error, so add a typed error (or reuse the closest existing one) and say which you chose and why.
  DO NOT CHANGE `DEFAULT_RETRY_LIMIT`. It is `2` at `:62`, deliberately aligned to spec 2.1 by maintainer ruling 2026-08-31, with the reasoning recorded in a comment beside it (`:49`). Do not "restore" 3. Note `0` is a LEGAL budget meaning no retries, so the validation must accept it rather than treating falsy as unset.
  ALSO, IF CHEAP: assert the spec's rule that the frozen value cannot change on resume, at the point the value is read. If it is not cheap, say so and leave it; do not build a freeze mechanism inside a range-check plan.
  - Depends on: none
  - Expected outcome: `-1` and `11` are refused at entry with a message naming the value and the 0..10 range; `0` and `10` are both accepted; `DEFAULT_RETRY_LIMIT` is still `2`; the refusal uses the module's typed-error convention with the choice stated.
  - Execution state: pending

- [ ] E-02 Extend the SHIPPED `tests/test_run_recovery_cli.py` with boundary cases, additively. Required: `-1` refused, `11` refused, `0` accepted, `10` accepted - the BOUNDARIES, not a middle value, because a middle-value test passes against an off-by-one and an off-by-one is the only bug this plan can realistically ship. Cover BOTH entry points, since validating one and not the other leaves the hole this plan exists to close.
  DO NOT create a new test module, and do NOT weaken, remove, or alter any existing assertion. PRESERVE a property the shipped file already has: two of its tests were updated 2026-08-31 to DERIVE their expectations from `DEFAULT_RETRY_LIMIT` rather than hard-coding a number, so no new test may hard-code `2` either.
  - Depends on: E-01
  - Expected outcome: four boundary cases per entry point pass; no existing assertion changed; no test hard-codes the default.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Refusals in `run_recovery.py` are TYPED DOMAIN ERRORS that are raised, not returned: `RetryLimitExceededError` (`:77`) and `NoRetryableStateError`, each with a composed message naming the step. Follow that shape.
- `DEFAULT_RETRY_LIMIT` carries a comment (`:49`) recording that its value was decided by maintainer ruling while the helper was still DORMANT (zero production callers), precisely so the same edit would not later become a costly behavior change. That comment is the historical record of the decision and must not be deleted.
- The two shipped tests that pinned the retry default now DERIVE from the constant, so it cannot silently drift again. Keep that property.
- `plan_retry`'s documented contract is that "a retry cannot turn failure into success by mere repetition", which is the reasoning behind a small bounded budget and behind rejecting a huge one.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | NEITHER shipped entry point validates `limit`. Both accept any int, so `-1` (every step instantly exhausted) and `10_000` (an effectively unbounded correction loop) are both silently legal today. | `run_recovery.py:213-219` (`plan_retry`), `:355-356` (`retry_budget_remaining`); neither body contains a range check |
| F-2 | `DEFAULT_RETRY_LIMIT` is ALREADY spec-aligned at `2`, so this plan's job is the range only. The spec-versus-code discrepancy the parent recorded (spec 2.1 said 2, code said 3) was resolved and applied on 2026-08-31. | `run_recovery.py:62` (`DEFAULT_RETRY_LIMIT: int = 2`) with the ruling recorded at `:49` |
| F-3 | THERE IS NO `--retry-budget` CLI FLAG, so "validate at entry" cannot mean argument parsing. The helpers' `limit` parameter IS the entry point. Verified so the executor does not invent a flag to validate. | `rg 'retry.budget' agent_workflows/run_cli.py agent_workflows/cli.py` finds only an unrelated exit-code comment (`run_cli.py:40`) |
| F-4 | `0` IS A LEGAL VALUE (no retries), so the check must not treat falsy as unset. An `if not limit:` style guard would silently substitute the default and defeat the spec's lower bound. | spec `25kzda` 2.1's inclusive 0..10 range |
| F-5 | SPLIT PROVENANCE: this plan is the parent's E-04, which shared a Scope-Paths list with a 13-code transcription task but had `Depends on: none` and no logical relation to it. Splitting removes the all-or-nothing integration risk the parent's F10 identified. | parent `wlxkoz` F10 / review round 2 PR-004; both E-01 and E-04 in the parent declared `Depends on: none` |
| F-6 | NO TEST-FILE CONTENTION WITH SIBLINGS. This child touches only `tests/test_run_recovery_cli.py`; Order 1 owns `tests/test_run_evidence_completion.py`. That settles, for this child, the parent's open question about who owns the shared test edits. | this plan's Scope-Paths against `wlxkoz`'s and `zub5f1`'s |
| F-7 | CONTENTION TO CHECK, inherited from the parent: APPROVED `0soncw` also claims `tests/test_run_recovery_cli.py` and is rewriting the `aw run` command strings its assertions invoke. Additive-only is a mitigation, not immunity. | parent F8; `0soncw`'s Scope-Paths |

## Proposed changes (ordered, validatable)

1. Add 0..10 inclusive validation to `plan_retry` and `retry_budget_remaining`, using the module's typed-error convention (E-01).
2. Add boundary tests (-1, 0, 10, 11) for both entry points to the shipped test module (E-02).

## Deferred / out of scope (with reason)

- CHANGING `DEFAULT_RETRY_LIMIT`. Already `2` and spec-aligned by maintainer ruling (F-2). Explicitly forbidden here.
- THE 13 `RUN-*` CODES and their bindings: Order 1 (`wlxkoz`).
- `--unverifiable-ok` AGGREGATE NEUTRALITY: Order 2 (`zub5f1`).
- ADDING A `--retry-budget` CLI FLAG. None exists (F-3), and inventing one would be a new user-facing surface rather than a bounds check.
- A FREEZE MECHANISM for the resume-invariance rule. E-01 asserts it only if cheap at the read site; building one belongs in its own plan.

## Scope check

- Over-scope: none. One module gains a range check; one shipped test module gains boundary cases.
- Under-scope: this validates the HELPER parameter only. Until something wires a user-facing budget, no operator can pass an out-of-range value anyway, so the value here is preventing a future caller from doing so. Stated plainly rather than overclaimed.

## Required tests / validation

- Boundary cases -1, 0, 10, 11 for BOTH `plan_retry` and `retry_budget_remaining`. Middle values alone do NOT satisfy this: they pass against an off-by-one.
- Every PRE-EXISTING assertion in `tests/test_run_recovery_cli.py` passes unchanged, and no new test hard-codes `2`.
- `DEFAULT_RETRY_LIMIT` is still `2` after the change, shown.
- Full suite BARE (`python3 -m pytest`), compared against YOUR OWN pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree: `tests/test_run_viewer.py` fails ~15 tests in a detached worktree that pass in the primary tree (backlog `dh0uno`), which would read as phantom regressions.
- `aw check plans` NO-WORSENING against your own fresh baseline; do NOT claim it passes (it is red on pre-existing findings owned by other Sets).

## Spec / documentation sync

- Implements the 0..10 retry-budget range of spec `25kzda` 2.1. No spec text changes.
- If the typed error added by E-01 is part of the module's public surface, note it in the module docstring beside the existing error classes; otherwise state N/A with the paths checked.

## Open questions

### OQ-01: Should the resume-invariance assertion land here or in its own plan?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT BLOCKING, because the range check is complete and useful without it. Spec 2.1 also says the frozen budget cannot change on resume. E-01 asserts that only IF it is cheap at the point the value is read; if enforcing it needs a freeze/compare mechanism, that is a different concern with its own state and belongs in its own plan rather than being smuggled into a bounds check. This is exactly the bundling that got the parent split, so the default is to leave it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the two amended signatures/bodies showing the validation, and the refusal messages for `-1` and `11` naming the value and the legal range. Paste acceptance for `0` and `10`. Paste `DEFAULT_RETRY_LIMIT` still `2` AND the comment at `:49` still present. State which error type you raised and why it matches the module's convention (a `ValueError` in a module whose every other refusal is a typed domain error needs a justification). Confirm BOTH entry points were validated, not one.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the four boundary cases passing for BOTH entry points, with counts. Paste `git diff tests/test_run_recovery_cli.py` proving every pre-existing assertion is untouched. Paste evidence no new test hard-codes `2` (show the derivation from `DEFAULT_RETRY_LIMIT`). PROVE THE TESTS ARE NOT VACUOUS: widen the bound to 0..11 in the implementation, paste the `11` case FAILING, then revert. A boundary test never observed failing does not establish the boundary. Then paste the bare full-suite summary with the HEAD, compared against your own pre-change baseline, measured in the primary checkout.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 2 E-leaves, one task group, one concern: enforce the spec's retry-budget range. This is deliberately the smallest of the three children the parent split into.

Open questions: OQ-01 (resume-invariance) is non-blocking; the range check stands alone either way. No blocking question remains.

This plan is `to-review` and requires explicit human approval before execution.

Scope fence: touch ONLY `agent_workflows/run_recovery.py` and `tests/test_run_recovery_cli.py` (test file: additive cases only; no existing assertion weakened, removed, or altered). Do NOT change `DEFAULT_RETRY_LIMIT` or delete the ruling comment beside it. Do NOT touch `run_evidence.py` (Order 1 and Order 2 own it). Do NOT add a CLI flag. Do NOT create a new test module. COORDINATION, inherited from the parent (F-7): APPROVED `0soncw` also claims `tests/test_run_recovery_cli.py` and is rewriting the command strings its assertions invoke, so re-measure that file (`git log --oneline -- <file>` plus a read of the invoked commands) immediately before editing; if `0soncw` has landed changes there, report it rather than merging blind. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is the SABOTAGE in V-02: a boundary test that has only been observed passing does not prove the boundary. Do NOT claim `aw check plans` passes; the bar is no-worsening against your own fresh baseline.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify with `git restore --staged <path>`, and re-run that check after any failed commit attempt, since a hook failure invalidates it. Prefer `aw commit <plan> -- <paths>`.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
