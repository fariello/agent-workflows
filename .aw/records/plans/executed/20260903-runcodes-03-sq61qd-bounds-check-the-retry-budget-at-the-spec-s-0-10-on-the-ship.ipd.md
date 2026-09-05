# IPD: bounds-check the retry budget at the spec's 0..10 on the shipped helper

- Date: 2026-09-03
- Kind: child
- Concern: Spec `25kzda` 2.1 fixes the retry budget's legal range at 0 through 10 inclusive, and NOTHING enforces it. `plan_retry` (`run_recovery.py:213`) and `retry_budget_remaining` (`:355`) both accept `limit: int = DEFAULT_RETRY_LIMIT` (`:62`, currently `2`) and neither validates the value: `plan_retry(limit=-1)` would make every step instantly budget-exhausted, and `limit=10_000` would license an unbounded correction loop, which is exactly what a bounded retry exists to prevent. This is the SMALLEST and most clearly-correct slice of the retired-bundle parent `wlxkoz`, and it was stranded there behind a 13-code verbatim transcription task it has nothing to do with (parent F10, review round 2 PR-004).
- Scope: Add ONLY the 0..10 inclusive RANGE validation, at the boundary where the value enters the two shipped helpers, plus tests at the boundaries. Excludes changing `DEFAULT_RETRY_LIMIT` (resolved to `2` by maintainer ruling 2026-08-31; do NOT re-litigate and do NOT "restore" 3), excludes the 13 `RUN-*` codes (Order 1, `wlxkoz`), excludes `--unverifiable-ok` (Order 2, `zub5f1`), excludes adding a CLI flag (none exists today), and excludes touching `run_evidence.py`.
- Scope-Paths: agent_workflows/run_recovery.py, tests/test_run_recovery_cli.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Set: runcodes
- Order: 3
- Highest E allocated: 02
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: sq61qd
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-09-05 executed (aw oc run): aw oc run self-finalize: sq61qd verified (set runcodes, attempt 1).
- 2026-09-05 executed (opencode its_direct/pt3-claude-opus-5-1m-us): E-01 and E-02 performed, V-01 and V-02 verified with pasted evidence. Started from HEAD `b2ad8358`; implementation commit `2a4ddef5`. Landed the 0..10 inclusive bound as ONE shared `validate_retry_budget(limit)` (`run_recovery.py:136-157`) taking JUST the value, called by both `plan_retry` (`:295`, before any ledger read) and `retry_budget_remaining` (`:425`) - the shape PR-001/F-8 required, since `uyeko5` E-04 must call this validation from a parse-time context where no `RunEngine` or `step_id` exists. The comparison exists in exactly ONE place (`grep` for `MIN_RETRY_LIMIT`/`MAX_RETRY_LIMIT` returns only the two constants at `:72-73`, the message at `:129`, and the single check at `:155`), so there is no second copy of the bound. Refusal is a NEW typed `InvalidRetryBudgetError(RecoveryError)` (`:113-131`), matching the module's convention that every refusal is a named domain error under one base, and deliberately NOT `RetryLimitExceededError`: proved distinguishable both by `issubclass(...) is False` and by a `try` whose first `except` is `RetryLimitExceededError` and calls `self.fail` if it ever catches. Bool excluded per F-9 using `run_ledger_schema._type_ok`'s precedent. `DEFAULT_RETRY_LIMIT` still `2` with its `:47-64` ruling comment intact - the ONLY edit to it is the permitted forward-reference update, which now names the validator instead of pointing at unwritten work; `retry_budget_remaining`'s `max(0, ...)` clamp untouched at `:427` and now documented as independent of the range check. Tests are a PURE INSERTION (`git diff --numstat` -> `198\t0`; zero deleted lines, no existing assertion weakened, no new module), 19 cases asserting the BOUNDARIES (-1, 0, 10, 11) at all THREE surfaces, with `limit=0` asserted BEHAVIORALLY (remaining 0, first retry refused, `count_retries` 0) so a default-substituting implementation would fail. BOTH mandatory sabotages were observed FAILING and reverted: widening the bound to 0..11 failed the `11` case at all three surfaces (3 failed, 16 passed), and removing the bool guard failed the `limit=True` case at all three (3 failed, 16 passed). No new test hard-codes `2` (the upper bound derives from `MAX_RETRY_LIMIT`, and the one literal is an arbitrary in-range `5` chosen NOT to be the default), preserving `8a99c7ca`'s derive-from-the-constant property. Suite bare at `b2ad8358`: `31 failed, 4462 passed` before, `31 failed, 4481 passed` after, with the sorted FAILED sets IDENTICAL by `diff` (+19 = exactly the tests added; all 31 pre-existing, none in this plan's file); re-confirmed `31 failed, 4481 passed` at the commit `2a4ddef5`. `aw check plans` unchanged at `errors 11 warnings 0` (no-worsening; it does NOT pass). `aw sanitize --agent` clean. `aw ipd lint --phase pre-transition` conforming. UNDER-SCOPE AS DESIGNED and not overclaimed: both helpers remain DORMANT (zero callers outside their own module), so no operator behavior changes and nothing in production can regress; the value is the seam `uyeko5` E-04 binds to. Two material decisions recorded (D-1: `0soncw` HAS since landed `f1baa33a` in the shared test file, re-measured as non-conflicting because my additions invoke zero CLI command strings and delete zero lines; D-2: `aw ipd begin`/`finalize` REFUSED to this worker role by `AW-LIFECYCLE-ROLE-001`, so the runner owns the lane transition). Not pushed.
- 2026-09-05 approved (aw set): status set to approved

- 2026-09-04 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 (5 findings, all FIXED in place, zero deferred, zero open). Verified at HEAD `42f72881`, working tree clean, target plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint --phase author` conforming before review and `--phase review-finalize` conforming after. THE PLAN'S MEASUREMENTS ALL HELD, and unusually for this Set every citation was exact: `DEFAULT_RETRY_LIMIT: int = 2` at `:62`, `plan_retry` at `:213` with `limit` at `:219`, `retry_budget_remaining` at `:355-356`, neither validating. F-1's two behavioral claims were EXECUTED rather than read: `plan_retry(limit=-1)` really does raise `RetryLimitExceededError` reporting "0 retries recorded meets/exceeds limit -1" on the first retry, and `limit=10_000` really is accepted by both helpers. ONE FINDING CHANGED THE DESIGN. PR-001 (HIGH): the plan told the executor to add the check to the two helper BODIES, but the consumer this validation exists for cannot reach it there - `runflags-01` (`uyeko5`) E-04 is written to CALL this validation and its fence forbids a duplicate bound, yet `--retry-budget` validates an operator value at parse time when no `RunEngine` or `step_id` exists, so a check inside `plan_retry(engine, step_id, ...)` is unreachable and that plan would be forced into the duplication it prohibits. E-01 now requires ONE shared validator taking just the value. FOUR MORE: PR-002, E-01 said "add a typed error (or reuse the closest existing one)" without excluding `RetryLimitExceededError`, whose reuse would make a CALLER error indistinguishable from normal budget escalation in every `except` clause; the plan now names `RecoveryError` (`:72`) as the base and forbids that reuse. PR-003/F-9, `bool` is an `int` in Python so `limit=True` silently means `1` and passes a naive range check; the package already has the exclusion precedent at `run_ledger_schema._type_ok:264-267`, and V-02 now requires a second sabotage since that guard is silent by construction. PR-004, F-4 declared `0` legal but every test only checked it was ACCEPTED, which an implementation substituting the default would also satisfy; E-02 now asserts `limit=0` means no retries BEHAVIORALLY. PR-005/F-11, F-7's inherited `0soncw` contention warning is stale (that plan has landed nothing in the test file; last three commits `8a99c7ca`, `99111c4c`, `caf658b4`), so it now reads as a pre-edit check rather than a live hazard. Also recorded F-10 (both helpers are still DORMANT - zero callers outside their module - which bounds the risk and forbids overclaiming operator impact), noted that `retry_budget_remaining`'s existing `max(0, ...)` clamp must not be "fixed", and found that `DEFAULT_RETRY_LIMIT`'s own comment already says the 0..10 bound "is enforced separately (see the runcodes Set)", i.e. the shipped code points at this plan - so the doc-sync section now requires updating that forward reference once satisfied. OQ-01 (resume invariance) RESOLVED from repository evidence rather than asked: `uyeko5` E-06 already owns "the frozen value cannot change on resume" for `--retry-budget`, so E-01's "assert it if cheap" clause was REMOVED rather than left dangling. Two reversible decisions recorded (D-1, D-2). Review artifact: `.aw/records/reviews/20260903-runcodes-03-sq61qd-bounds-check-the-retry-budget-at-the-spec-s-0-10-on-the-ship.review.md`

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): SPLIT OUT OF `wlxkoz` (Order 1) at the maintainer's direction, discharging that plan's F10 / review-round-2 PR-004, which found it bundled three independent concerns and must be split before execution. This child carries the parent's E-04 VERBATIM in intent: the 0..10 range check only. It is deliberately the smallest slice, and that is the point of the split - the parent's own finding was that "if an executor fumbles the 13 verbatim transcriptions, the whole plan strands on its lane and the trivially safe bounds check strands with it". MEASURED AT AUTHORING rather than inherited: `DEFAULT_RETRY_LIMIT: int = 2` is at `run_recovery.py:62` (already spec-aligned, so E-01 must not touch it); `plan_retry` at `:213` takes `limit: int = DEFAULT_RETRY_LIMIT` at `:219`; `retry_budget_remaining` at `:355-356` takes the same; NEITHER validates. Also verified there is NO `--retry-budget` CLI flag in `run_cli.py` or `cli.py`, so "at entry" means the helpers' parameter and this plan must NOT invent a flag. The parent's E-05 test-ownership question is settled for this child: it touches ONLY `tests/test_run_recovery_cli.py`, never `tests/test_run_evidence_completion.py`, so it cannot collide with its siblings over a shared test file.

## Goal

Make an out-of-range retry budget impossible to pass, so a bounded retry is actually bounded, without changing the default or any other behavior.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: validate the range at the boundary where the value enters

- [x] E-01 Add the spec's 0..10 inclusive range validation to the two shipped entry points in `agent_workflows/run_recovery.py`: `plan_retry` (`:213`, `limit` at `:219`) and `retry_budget_remaining` (`:355`). Reject below 0 and above 10 with a clear message naming the offending value and the legal range. RE-READ BOTH SIGNATURES BEFORE EDITING and locate them BY SYMBOL: the parent plan's citations for these same symbols had already drifted ~15 lines once (parent PR-003), so a line number here is orientation, not an address.
  PUT THE CHECK IN ONE SHARED, PUBLICLY CALLABLE VALIDATOR AND CALL IT FROM BOTH (added at review, PR-001). Do NOT inline the same comparison in two function bodies. Two reasons, both measured. (1) `runflags-01` (`uyeko5`) E-04 is written to CALL this plan's validation rather than re-check the range, and its `--retry-budget` flag validates a CLI value BEFORE any engine or step exists, so a check buried inside `plan_retry(engine, step_id, ...)` is unreachable from there and that plan would be forced into the duplicate bound its own fence forbids. (2) Two copies of one bound is how an off-by-one gets fixed in one place only. Give it a name and a signature that takes JUST the value (for example `validate_retry_budget(limit: int) -> int`), so the flag layer, the helpers, and the tests all exercise the same code.
  FOLLOW THE MODULE'S OWN REFUSAL CONVENTION rather than inventing one: `run_recovery.py` already defines typed errors and raises them, all descending from one base (`RecoveryError:72`, then `RetryLimitExceededError:76` with its message composed at `:84`, `UnknownOutcomeError:89`, `NoRetryableStateError:100`). A `ValueError` would be inconsistent with a module whose every other refusal is a named domain error, so add a typed error under `RecoveryError` (or reuse the closest existing one) and say which you chose and why. Do NOT reuse `RetryLimitExceededError`: it means "this step consumed its budget", a runtime condition, whereas an out-of-range `limit` is a CALLER error, and collapsing the two would make a programming mistake indistinguishable from normal escalation in every `except` clause.
  DO NOT CHANGE `DEFAULT_RETRY_LIMIT`. It is `2` at `:62`, deliberately aligned to spec 2.1 by maintainer ruling 2026-08-31, with the reasoning recorded in a comment at `:47-61`. Do not "restore" 3. Note `0` is a LEGAL budget meaning no retries, so the validation must accept it rather than treating falsy as unset.
  REJECT A NON-INTEGER AND A BOOL TOO (added at review, PR-003). `bool` is a subclass of `int` in Python, so `plan_retry(limit=True)` silently means `limit=1` and passes a naive `0 <= limit <= 10`. Use an `isinstance(limit, int) and not isinstance(limit, bool)` shaped guard, matching the precedent already in the package (`run_ledger_schema._type_ok:264-267` excludes `bool` from `int` for exactly this reason).
  DO NOT ALSO "FIX" `retry_budget_remaining`'s `max(0, ...)` CLAMP (`:360`). Measured: it already returns 0 rather than a negative number, which is correct and separately documented ("never negative"); the range check makes a negative `limit` unreachable, it does not replace the clamp.
  DO NOT IMPLEMENT THE RESUME-INVARIANCE RULE (revised at review; OQ-01 resolved). An earlier version said to assert it "if cheap". It is not this plan's: `runflags-01` (`uyeko5`) E-06 explicitly owns "the frozen value cannot change on resume" for `--retry-budget`, and enforcing it requires the run state and resume parser this module cannot reach. Leave it out entirely rather than half-asserting it here.
  - Depends on: none
  - Expected outcome: ONE shared validator, callable with just the value, called by both helpers; `-1` and `11` refused with a message naming the value and the 0..10 range; `0` and `10` accepted; a `bool` and a non-int refused; `DEFAULT_RETRY_LIMIT` still `2` and its comment intact; the refusal is a new typed error under `RecoveryError`, distinct from `RetryLimitExceededError`, with the choice stated; `retry_budget_remaining`'s existing clamp untouched.
  - Execution state: performed

- [x] E-02 Extend the SHIPPED `tests/test_run_recovery_cli.py` with boundary cases, additively. Required: `-1` refused, `11` refused, `0` accepted, `10` accepted - the BOUNDARIES, not a middle value, because a middle-value test passes against an off-by-one and an off-by-one is the only bug this plan can realistically ship. Cover BOTH entry points, since validating one and not the other leaves the hole this plan exists to close, plus the shared validator directly.
  ASSERT `0` MEANS NO RETRIES, NOT MERELY THAT IT PARSES (added at review, PR-004). F-4 says `0` is legal and the plan only ever checks that it is ACCEPTED, which a `limit=0` implementation that silently substituted the default would also satisfy. Assert the BEHAVIOR: with `limit=0`, `retry_budget_remaining` is `0` and `plan_retry` refuses with `RetryLimitExceededError` on the FIRST retry. That is what "0 retries" means, and it is the one accepted-boundary case with observable semantics.
  ASSERT THE TYPED-ERROR CHOICE, NOT JUST THAT SOMETHING RAISED. The out-of-range refusal must be caught as the NEW error type and must NOT be catchable as `RetryLimitExceededError`, since E-01 requires those be distinguishable; a bare `assertRaises(Exception)` would pass against the conflation E-01 forbids.
  DO NOT create a new test module, and do NOT weaken, remove, or alter any existing assertion. PRESERVE a property the shipped file already has: two of its tests DERIVE their expectations from `DEFAULT_RETRY_LIMIT` rather than hard-coding a number (`:151`, `:159-161`, `:221-227`, added 2026-08-31 in `8a99c7ca`), so no new test may hard-code `2` either.
  - Depends on: E-01
  - Expected outcome: the four boundary cases pass for both helpers and for the shared validator; `limit=0` is shown to mean no retries behaviorally; the refusal is asserted as the new typed error and shown NOT to be a `RetryLimitExceededError`; a bool/non-int is refused; no existing assertion changed; no test hard-codes the default.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Refusals in `run_recovery.py` are TYPED DOMAIN ERRORS that are raised, not returned, and they share ONE base class: `RecoveryError` (`:72`, "Base class for all recovery-layer errors (fail closed)"), with `RetryLimitExceededError` (`:76`), `UnknownOutcomeError` (`:89`), and `NoRetryableStateError` (`:100`) descending from it. A new refusal belongs under that base. Note this module's convention is the OPPOSITE of `run_evidence.py`'s (which has zero `raise` and reports as data); the two are different layers, so follow the local one.
- `DEFAULT_RETRY_LIMIT` carries a comment (`:47-61`) recording that its value was decided by maintainer ruling while the helper was still DORMANT (zero production callers), precisely so the same edit would not later become a costly behavior change. It ALSO states explicitly "NOT a range check: spec 2.1's 0..10 bound is enforced separately (see the runcodes Set)", i.e. the shipped code already points at THIS plan. That comment is the historical record of the decision and must not be deleted.
- STILL DORMANT, RE-MEASURED AT REVIEW: `plan_retry` and `retry_budget_remaining` have ZERO callers outside `run_recovery.py` itself, and `DEFAULT_RETRY_LIMIT`'s only external references are in `tests/test_run_recovery_cli.py`. So this change cannot regress production behavior, which is what makes it the safest of the three children - and it is also why the plan must not overclaim operator impact.
- The two shipped tests that pinned the retry default now DERIVE from the constant (`:151`, `:159-161`, `:221-227`), so it cannot silently drift again. Keep that property.
- `plan_retry`'s documented contract is that "a retry cannot turn failure into success by mere repetition", which is the reasoning behind a small bounded budget and behind rejecting a huge one.
- `retry_budget_remaining` already returns `max(0, limit - used)` (`:360`) and documents "never negative". That clamp is correct and independent of the range check; do not remove or duplicate it.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | NEITHER shipped entry point validates `limit`. Both accept any int, so `-1` (every step instantly exhausted) and `10_000` (an effectively unbounded correction loop) are both silently legal today. EXECUTED AT REVIEW rather than read: `plan_retry(limit=-1)` raises `RetryLimitExceededError` with "0 retries recorded meets/exceeds limit -1" on the very first retry, confirming the instant-exhaustion claim exactly; `plan_retry(limit=10_000)` returns a plan with `limit=10000`; `retry_budget_remaining(limit=10_000)` returns `10000`. | `run_recovery.py:213-219` (`plan_retry`), `:355-360` (`retry_budget_remaining`); neither body contains a range check; live results above |
| F-2 | `DEFAULT_RETRY_LIMIT` is ALREADY spec-aligned at `2`, so this plan's job is the range only. The spec-versus-code discrepancy the parent recorded (spec 2.1 said 2, code said 3) was resolved and applied on 2026-08-31. RE-MEASURED AT REVIEW and still `2`; the comment additionally says "NOT a range check: spec 2.1's 0..10 bound is enforced separately (see the runcodes Set)", so the shipped code already names this plan's work. | `run_recovery.py:62` (`DEFAULT_RETRY_LIMIT: int = 2`) with the ruling recorded at `:47-61` |
| F-3 | THERE IS NO `--retry-budget` CLI FLAG, so "validate at entry" cannot mean argument parsing. The helpers' `limit` parameter IS the entry point. Verified so the executor does not invent a flag to validate. | `rg 'retry.budget|retry_budget' agent_workflows/run_cli.py agent_workflows/cli.py` finds only an unrelated exit-code comment (`run_cli.py:40`) |
| F-8 | FOUND AT REVIEW; IT CHANGES E-01's SHAPE. The consumer this validation exists for CANNOT REACH IT if the check is inlined in the two helper bodies. `runflags-01` (`uyeko5`) E-04 explicitly says it "must call that validation rather than re-checking the range itself", and its fence forbids the duplicate; but `--retry-budget` validates an operator-supplied value at parse time, when no `RunEngine` or `step_id` exists, so a check inside `plan_retry(engine, step_id, ...)` is unreachable from the flag layer. E-01 therefore requires ONE shared validator taking just the value. | `uyeko5` E-04 and its scope fence; `plan_retry`'s signature (`run_recovery.py:213-221`) requiring `engine` and `step_id` |
| F-9 | FOUND AT REVIEW. `bool` IS AN `int` IN PYTHON, so `limit=True` silently means `1` and passes a naive `0 <= limit <= 10`. The package already has the precedent for excluding it. | `run_ledger_schema._type_ok` (`:264-267`): `if typ is int: return isinstance(val, int) and not isinstance(val, bool)` |
| F-10 | FOUND AT REVIEW. THE HELPERS ARE STILL DORMANT, which bounds this plan's risk and its claims: `plan_retry` and `retry_budget_remaining` have ZERO callers outside their own module, and `DEFAULT_RETRY_LIMIT`'s only external references are the shipped tests. Nothing in production can regress, and no operator gains anything until `uyeko5` lands the flag. | `rg 'plan_retry' agent_workflows/` and `rg 'retry_budget_remaining' agent_workflows/` outside `run_recovery.py` -> zero; `rg 'DEFAULT_RETRY_LIMIT'` outside the module -> only `tests/test_run_recovery_cli.py` |
| F-11 | FOUND AT REVIEW; F-7's inherited contention warning is STALE for this file. `tests/test_run_recovery_cli.py`'s last three commits are `8a99c7ca` (the retry-default alignment), `99111c4c`, and `caf658b4`; `0soncw` has landed NOTHING there. The coordination instruction is still worth keeping as a pre-edit check, but it should not read as an unresolved hazard. Note also that the sibling-serialization instruction has no machine enforcement (the same gap measured in `zub5f1` F-10), though here no sibling shares this plan's paths. | `git log --oneline -5 -- tests/test_run_recovery_cli.py`; this plan's Scope-Paths against `wlxkoz`'s and `zub5f1`'s |
| F-4 | `0` IS A LEGAL VALUE (no retries), so the check must not treat falsy as unset. An `if not limit:` style guard would silently substitute the default and defeat the spec's lower bound. | spec `25kzda` 2.1's inclusive 0..10 range |
| F-5 | SPLIT PROVENANCE: this plan is the parent's E-04, which shared a Scope-Paths list with a 13-code transcription task but had `Depends on: none` and no logical relation to it. Splitting removes the all-or-nothing integration risk the parent's F10 identified. | parent `wlxkoz` F10 / review round 2 PR-004; both E-01 and E-04 in the parent declared `Depends on: none` |
| F-6 | NO TEST-FILE CONTENTION WITH SIBLINGS. This child touches only `tests/test_run_recovery_cli.py`; Order 1 owns `tests/test_run_evidence_completion.py`. That settles, for this child, the parent's open question about who owns the shared test edits. | this plan's Scope-Paths against `wlxkoz`'s and `zub5f1`'s |
| F-7 | CONTENTION TO CHECK, inherited from the parent: APPROVED `0soncw` also claims `tests/test_run_recovery_cli.py` and is rewriting the `aw run` command strings its assertions invoke. Additive-only is a mitigation, not immunity. MEASURED AT REVIEW: it has landed nothing in that file yet (see F-11), so this is a pre-edit check, not a live conflict. | parent F8; `0soncw`'s Scope-Paths; `git log -5` on the file |

## Proposed changes (ordered, validatable)

1. Add ONE shared 0..10 inclusive validator (taking just the value, so the future `--retry-budget` flag can call it) plus a new typed error under `RecoveryError`, and call it from `plan_retry` and `retry_budget_remaining` (E-01).
2. Add boundary tests (-1, 0, 10, 11) for both entry points and the validator, plus the `limit=0` behavioral case and the typed-error assertion, to the shipped test module (E-02).

## Deferred / out of scope (with reason)

- CHANGING `DEFAULT_RETRY_LIMIT`. Already `2` and spec-aligned by maintainer ruling (F-2). Explicitly forbidden here.
- THE 13 `RUN-*` CODES and their bindings: Order 1 (`wlxkoz`).
- `--unverifiable-ok` AGGREGATE NEUTRALITY: Order 2 (`zub5f1`).
- ADDING A `--retry-budget` CLI FLAG. None exists (F-3), and inventing one would be a new user-facing surface rather than a bounds check. **NOW OWNED BY `runflags-01` (`uyeko5`), authored 2026-09-04**, which registers the flag on both runners with spec 2.1's CLI-over-policy-over-default precedence and CALLS this plan's range validation rather than duplicating it. So the gap is tracked, and this plan stays a bounds check.
- THE RESUME-INVARIANCE RULE ("the frozen value cannot change on resume"). **OWNED BY `runflags-01` (`uyeko5`) E-06**, which freezes every wired flag into run state and follows the shipped `default=None` resume-parser pattern. Removed from E-01 entirely at review (OQ-01 resolved): freezing needs the run state and resume parser this module cannot reach, so a partial assertion here would be a second, weaker enforcement point.

## Scope check

- Over-scope: none. One module gains a shared validator plus one typed error; one shipped test module gains boundary cases. The shared-validator shape is NOT scope creep: it is the same single check, given a callable name so the flag layer that must call it (`uyeko5` E-04) can (F-8).
- Under-scope, DELIBERATE and stated plainly: this validates the HELPER parameter only. Both helpers are DORMANT (zero callers outside their own module, F-10), so when this plan completes no operator behavior changes and nothing in production can regress. The value is preventing a future caller from passing an out-of-range budget, and supplying the seam `uyeko5` binds to. Not overclaimed.

## Required tests / validation

- Boundary cases -1, 0, 10, 11 for BOTH `plan_retry` and `retry_budget_remaining` AND for the shared validator directly. Middle values alone do NOT satisfy this: they pass against an off-by-one.
- `limit=0` proven to mean NO RETRIES behaviorally (`retry_budget_remaining` returns 0; `plan_retry` refuses on the first retry), not merely accepted.
- The out-of-range refusal asserted as the NEW typed error and shown NOT to be catchable as `RetryLimitExceededError`.
- A `bool` (`limit=True`) and a non-int refused (F-9).
- Every PRE-EXISTING assertion in `tests/test_run_recovery_cli.py` passes unchanged, and no new test hard-codes `2`.
- `DEFAULT_RETRY_LIMIT` is still `2` after the change, shown, with its `:47-61` comment intact.
- `retry_budget_remaining`'s `max(0, ...)` clamp still present and unmodified.
- Full suite BARE (`python3 -m pytest`), compared against YOUR OWN pre-change measurement at the HEAD you started from. No `-n0`, no second `-q`, no `-p no:randomly`.
- Measure in the PRIMARY checkout, not a scratch worktree: `tests/test_run_viewer.py` fails ~15 tests in a detached worktree that pass in the primary tree (backlog `dh0uno`), which would read as phantom regressions.
- `aw check plans` NO-WORSENING against your own fresh baseline; do NOT claim it passes (it is red on pre-existing findings owned by other Sets).

## Spec / documentation sync

- Implements the 0..10 retry-budget range of spec `25kzda` 2.1. No spec text changes.
- The typed error added by E-01 IS public surface (it descends from `RecoveryError`, which the module docstring already presents as the fail-closed error family), so note it and the shared validator in the module docstring beside the existing error classes. That docstring already documents the retry budget's escalation contract (`:14-17`), so the range bound belongs in the same paragraph rather than being discoverable only from the code.
- Record in the validator's docstring that it exists to be called by the future `--retry-budget` flag (`uyeko5` E-04) as well as by the two helpers, so a later reader does not "simplify" it back into two inlined comparisons and silently break that consumer.
- The `DEFAULT_RETRY_LIMIT` comment at `:47-61` currently says the 0..10 bound "is enforced separately (see the runcodes Set)". Once this plan lands, that forward reference is satisfiable: update it to name the validator, since a comment pointing at unwritten work is exactly the stale-pointer class this repo keeps correcting.

## Open questions

### OQ-01: Should the resume-invariance assertion land here or in its own plan?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-04 FROM REPOSITORY EVIDENCE, not deferred and not by asking: the resume-invariance rule is ALREADY OWNED by another plan. `runflags-01` (`uyeko5`) E-06 covers exactly this - "Freeze every wired flag into run state and honor the spec's RESUME rule ... and specifically 'the frozen value cannot change on resume' for `--retry-budget`" - and it follows the shipped `default=None` resume-parser pattern (its F-6, citing `oc_runipd.py:6373-6375` and `agy_runipd.py:4531-4533`). So the answer is NEITHER "here" nor "its own new plan": it belongs to `uyeko5` E-06, which is where the frozen value actually lives, since freezing requires the run state and the resume parser that this module has no access to. E-01's "assert it if cheap" clause is therefore DROPPED as a requirement rather than left dangling; this plan is the range check only. ORIGINAL RATIONALE RETAINED: not blocking, because the range check is complete and useful without it, and smuggling a freeze mechanism into a bounds check is exactly the bundling that got the parent split.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the shared validator's signature and body, and the two amended helper bodies showing they CALL it rather than repeating the comparison. Prove it is callable with the value ALONE (no engine, no step id), since that is what makes it reachable from `uyeko5`'s flag layer (F-8) - paste an invocation that passes only a number.
    Paste the refusal messages for `-1` and `11` naming the value and the legal range, and acceptance for `0` and `10`. Paste the `bool` refusal (`limit=True`) and a non-int refusal. Paste `DEFAULT_RETRY_LIMIT` still `2` AND its comment at `:47-61` still present. Paste `retry_budget_remaining`'s `max(0, ...)` clamp still present.
    State which error type you raised and why it matches the module's convention, and show it descends from `RecoveryError` and is NOT `RetryLimitExceededError` (a `ValueError`, or reusing the budget-exhausted error, in a module whose every refusal is a distinct typed domain error needs a justification). Confirm BOTH entry points route through the one validator, not one.
  - Observed evidence: VERIFIED at HEAD `b2ad8358872da2591af5bf0705be731bf0238a08`, primary lane checkout `aw/lane/sq61qd`.

    THE SHARED VALIDATOR (`agent_workflows/run_recovery.py:136-157`), taking ONLY the value, no engine and no step id:

    ```python
    def validate_retry_budget(limit: Any) -> int:
        """Return `limit` if it is a legal retry budget; otherwise raise `InvalidRetryBudgetError`.
        ... (docstring records: single definition of the bound; callable by the future --retry-budget
        flag (uyeko5 E-04) at parse time when no RunEngine or step exists; do NOT re-inline it;
        bool refused though bool is an int; 0 IS LEGAL and means "no retries") ...
        """
        if not isinstance(limit, int) or isinstance(limit, bool):
            raise InvalidRetryBudgetError(limit)
        if limit < MIN_RETRY_LIMIT or limit > MAX_RETRY_LIMIT:
            raise InvalidRetryBudgetError(limit)
        return limit
    ```

    THE BOUND EXISTS IN EXACTLY ONE PLACE, not two. `grep -n 'MIN_RETRY_LIMIT\|MAX_RETRY_LIMIT' agent_workflows/run_recovery.py`:

    ```text
    72:MIN_RETRY_LIMIT: int = 0
    73:MAX_RETRY_LIMIT: int = 10
    129:            f"{MIN_RETRY_LIMIT}..{MAX_RETRY_LIMIT} (spec 25kzda 2.1)"
    155:    if limit < MIN_RETRY_LIMIT or limit > MAX_RETRY_LIMIT:
    ```

    Line 155 is the ONLY comparison (72/73 are the constants, 129 is the message), so there is no second copy of the bound to drift.

    BOTH ENTRY POINTS CALL IT, neither repeats the comparison. `grep -n 'validate_retry_budget(limit)' agent_workflows/run_recovery.py` -> `295:` and `425:`, one in each helper:

    ```python
    # plan_retry, agent_workflows/run_recovery.py:295 (first statement, BEFORE any ledger read)
        validate_retry_budget(limit)
        snapshot = engine.reconstruct_state()

    # retry_budget_remaining, agent_workflows/run_recovery.py:425
        validate_retry_budget(limit)
        used = count_retries(engine, step_id)
        return max(0, limit - used)
    ```

    CALLABLE WITH THE VALUE ALONE, which is what makes it reachable from `uyeko5`'s flag layer (F-8). Live invocation passing only a number, no engine, no step id:

    ```text
    $ python3 -c "from agent_workflows import run_recovery as r; print(r.validate_retry_budget(5))"
    5
    ```

    REFUSALS AND ACCEPTANCES, live:

    ```text
    validator callable with the VALUE ALONE (no engine, no step_id):
      validate_retry_budget(5) -> 5
      validate_retry_budget(0) -> 0
      validate_retry_budget(10) -> 10
      refused -1 -> invalid retry budget -1: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
      refused 11 -> invalid retry budget 11: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
      refused 10000 -> invalid retry budget 10000: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
      refused True -> invalid retry budget True: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
      refused 2.5 -> invalid retry budget 2.5: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
      refused 'x' -> invalid retry budget 'x': must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
      refused None -> invalid retry budget None: must be an int in the inclusive range 0..10 (spec 25kzda 2.1)
    ```

    Each message names the offending value (`-1`, `11`, `True`) AND the legal range (`0..10`), as required. `0` and `10` are accepted (inclusive at both ends); the `bool` and non-int cases are refused (F-9).

    THE ERROR TYPE, and why. I added `InvalidRetryBudgetError(RecoveryError)` at `:113-131`. It matches the module's convention because every refusal in `run_recovery.py` is a named domain error descending from one base (`RecoveryError:72`, `RetryLimitExceededError:90`, `UnknownOutcomeError:103`, `NoRetryableStateError:110`); a `ValueError` would be the only stdlib refusal in the module. I did NOT reuse `RetryLimitExceededError`, and its docstring records why: that error means "this step consumed its budget", a normal runtime escalation, whereas an out-of-range `limit` is a CALLER error, and conflating them would make a programming mistake indistinguishable from ordinary escalation in every `except` clause. Live proof of the hierarchy:

    ```text
    InvalidRetryBudgetError.__mro__ = ['InvalidRetryBudgetError', 'RecoveryError', 'Exception', 'BaseException']
    descends from RecoveryError: True
    is NOT RetryLimitExceededError: True
    ```

    `DEFAULT_RETRY_LIMIT` STILL `2` AND ITS COMMENT INTACT (`:47-64`). Live: `DEFAULT_RETRY_LIMIT = 2 (unchanged, in range)`. The comment's spec quote, the 2026-08-31 ruling, the dormancy note, and the whole "WHY 2 IS THE RIGHT NUMBER" paragraph are all present and unedited; the ONLY change to it is the permitted forward-reference update, which now names the validator instead of pointing at unwritten work:

    ```text
    -# NOT a range check: spec 2.1's 0..10 bound is enforced separately (see the runcodes Set); this
    -# constant is only the DEFAULT when no budget is frozen by the CLI or repository policy.
    +# NOT a range check: spec 2.1's 0..10 bound is enforced separately by `validate_retry_budget()`
    +# below (runcodes Order 3, `sq61qd`); this constant is only the DEFAULT when no budget is frozen by
    +# the CLI or repository policy.
    ```

    `git diff -U0 agent_workflows/run_recovery.py | grep '^-[^-]'` returns exactly three deleted lines: the two comment lines above plus `retry_budget_remaining`'s one-line docstring (replaced by a longer one). No code line was deleted.

    THE CLAMP IS UNTOUCHED. `grep -n 'max(0, limit - used)'` -> `427:    return max(0, limit - used)`, still present, still the return expression, and `retry_budget_remaining`'s new docstring states the clamp is INDEPENDENT of the range check ("guarantees the RETURN is never negative once retries have been consumed, which the range check does not address") so a later reader does not delete it as redundant.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the boundary cases passing for BOTH entry points AND the validator, with counts. Paste the `limit=0` behavioral case: `retry_budget_remaining` returning 0 and `plan_retry` refusing on the first retry, since "accepted" alone would pass against an implementation that substituted the default. Paste the assertion that the out-of-range error is the new type and is NOT caught as `RetryLimitExceededError`.
    Paste `git diff tests/test_run_recovery_cli.py` proving every pre-existing assertion is untouched. Paste evidence no new test hard-codes `2` (show the derivation from `DEFAULT_RETRY_LIMIT`).
    PROVE THE TESTS ARE NOT VACUOUS, TWICE. (a) Widen the bound to 0..11 in the implementation, paste the `11` case FAILING, then revert: a boundary test never observed failing does not establish the boundary. (b) Remove the bool guard, paste the `limit=True` case FAILING, then revert: `bool` passing as `int` is silent by construction (F-9), so that guard needs its own falsification.
    Then paste the bare full-suite summary with the HEAD, compared against your own pre-change baseline, measured in the primary checkout.
  - Observed evidence: VERIFIED at HEAD `b2ad8358872da2591af5bf0705be731bf0238a08`, measured in this lane's checkout (`aw/lane/sq61qd`), which is a full non-detached checkout, so the `test_run_viewer.py` phantom-regression trap (backlog `dh0uno`) does not apply: those 15 failures are in my PRE-change baseline too and are byte-identical after.

    THE BOUNDARY CASES PASS FOR BOTH ENTRY POINTS AND THE VALIDATOR, with counts. `python3 -m pytest -o addopts="" -v tests/test_run_recovery_cli.py -k RetryBudgetRange`:

    ```text
    collected 74 items / 55 deselected / 19 selected

    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_plan_retry_rejects_above_upper_bound PASSED [  5%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_an_out_of_range_budget_appends_nothing PASSED [ 10%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_plan_retry_rejects_bool_budget PASSED [ 15%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_rejects_above_upper_bound PASSED [ 21%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_zero_budget_means_no_retries_not_the_default PASSED [ 26%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_clamp_still_never_negative PASSED [ 31%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_rejects_an_effectively_unbounded_budget PASSED [ 36%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_rejects_above_upper_bound PASSED [ 42%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_invalid_budget_error_is_not_a_retry_limit_exceeded_error PASSED [ 47%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_the_default_budget_is_itself_in_range PASSED [ 52%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_rejects_bool_budget PASSED [ 57%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_is_callable_with_the_value_alone PASSED [ 63%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_rejects_below_lower_bound PASSED [ 68%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_rejects_bool_and_non_int PASSED [ 73%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_plan_retry_rejects_below_lower_bound PASSED [ 78%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_rejects_below_lower_bound PASSED [ 84%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_accepts_upper_boundary PASSED [ 89%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_accepts_both_inclusive_boundaries PASSED [ 94%]
    tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_plan_retry_accepts_upper_boundary PASSED [100%]

    ====================== 19 passed, 55 deselected in 0.63s =======================
    ```

    All four boundaries are covered at all three surfaces: `-1` (`test_validator_rejects_below_lower_bound`, `test_plan_retry_rejects_below_lower_bound`, `test_retry_budget_remaining_rejects_below_lower_bound`), `11` (the three `..._above_upper_bound`), `0` (`test_validator_accepts_both_inclusive_boundaries` plus the behavioral case below), `10` (`test_validator_accepts_both_inclusive_boundaries`, `test_plan_retry_accepts_upper_boundary`, `test_retry_budget_remaining_accepts_upper_boundary`). Whole file: `74 passed` (55 shipped + 19 added).

    THE `limit=0` BEHAVIORAL CASE, not merely "accepted" (`test_zero_budget_means_no_retries_not_the_default`): it asserts `retry_budget_remaining(..., limit=0) == 0`, that `plan_retry(..., limit=0)` raises `RetryLimitExceededError` on the FIRST retry with `ctx.exception.limit == 0`, and that `count_retries(...) == 0` afterwards, so no retry was recorded. An implementation that treated the falsy `0` as unset and substituted `DEFAULT_RETRY_LIMIT` would fail all three, which is the point of asserting behavior rather than acceptance.

    THE TYPED-ERROR ASSERTION (`test_invalid_budget_error_is_not_a_retry_limit_exceeded_error`): asserts `issubclass(InvalidRetryBudgetError, RecoveryError)` is True, `issubclass(InvalidRetryBudgetError, RetryLimitExceededError)` is False, and additionally executes `validate_retry_budget(-1)` inside a `try` whose FIRST `except` is `RetryLimitExceededError` and calls `self.fail(...)` if it ever catches, so the conflation would be caught at runtime and not only by the subclass check. No `assertRaises(Exception)` anywhere.

    EVERY PRE-EXISTING ASSERTION UNTOUCHED. `git diff --numstat tests/test_run_recovery_cli.py`:

    ```text
    198	0	tests/test_run_recovery_cli.py
    ```

    Zero deleted lines: the change is a PURE INSERTION of one new test class between `TestBoundedRetry` and the E-02 section. Confirmed independently by `git diff -U0 tests/test_run_recovery_cli.py | grep -c '^-[^-]'` -> `0`. No existing assertion was weakened, removed, or altered, and no new test module was created.

    NO NEW TEST HARD-CODES `2`. `git diff -U0 ... | grep '^+' | grep -E '\b(limit|budget)\b.*[^_A-Za-z0-9]2\b'` returns nothing, while the same added block references the constants 18 times (`MIN_RETRY_LIMIT` / `MAX_RETRY_LIMIT` / `DEFAULT_RETRY_LIMIT`). The upper-bound tests DERIVE `11` as `run_recovery.MAX_RETRY_LIMIT + 1` rather than writing it, `test_the_default_budget_is_itself_in_range` passes `DEFAULT_RETRY_LIMIT` through the validator rather than asserting it equals a literal, and `test_validator_is_callable_with_the_value_alone` deliberately uses `5` (an arbitrary in-range value that is NOT the default) so it says nothing about the default's value. This preserves the property `8a99c7ca` established at `:151`, `:159-161`, `:221-227`.

    SABOTAGE (a): WIDEN THE BOUND TO 0..11, the `11` case must FAIL. Changed `:155` to `limit > MAX_RETRY_LIMIT + 1`:

    ```text
    === SABOTAGE (a): bound widened to 0..11 ===
    ___ TestRetryBudgetRangeValidation.test_validator_rejects_above_upper_bound ____
        def test_validator_rejects_above_upper_bound(self) -> None:
            """11 (one past the inclusive upper bound) is refused: the boundary, not a middle value."""
    >       with self.assertRaises(run_recovery.InvalidRetryBudgetError) as ctx:
    E       AssertionError: InvalidRetryBudgetError not raised

    _ TestRetryBudgetRangeValidation.test_retry_budget_remaining_rejects_above_upper_bound _
        def test_retry_budget_remaining_rejects_above_upper_bound(self) -> None:
    >       with self.assertRaises(run_recovery.InvalidRetryBudgetError):
    E       AssertionError: InvalidRetryBudgetError not raised

    =========================== short test summary info ============================
    FAILED tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_plan_retry_rejects_above_upper_bound
    FAILED tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_rejects_above_upper_bound
    FAILED tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_rejects_above_upper_bound
    3 failed, 16 passed, 55 deselected in 0.67s
    ```

    An off-by-one of exactly one is detected at ALL THREE surfaces, which is what a boundary test is for. REVERTED and re-verified: `19 passed, 55 deselected`.

    SABOTAGE (b): REMOVE THE BOOL GUARD, the `limit=True` case must FAIL. Changed `:153` to `if not isinstance(limit, int):`:

    ```text
    === SABOTAGE (b): bool guard removed ===
    ____ TestRetryBudgetRangeValidation.test_validator_rejects_bool_and_non_int ____
        def test_validator_rejects_bool_and_non_int(self) -> None:
            """`bool` is a subclass of `int`, so `True` must not silently mean a budget of 1."""
            for bad in (True, False, 2.0, "3", None):
                with self.subTest(bad=bad):
    >               with self.assertRaises(run_recovery.InvalidRetryBudgetError):
    E               AssertionError: InvalidRetryBudgetError not raised

    =========================== short test summary info ============================
    FAILED tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_retry_budget_remaining_rejects_bool_budget
    FAILED tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_plan_retry_rejects_bool_budget
    FAILED tests/test_run_recovery_cli.py::TestRetryBudgetRangeValidation::test_validator_rejects_bool_and_non_int
    3 failed, 16 passed, 55 deselected in 0.77s
    ```

    The guard has its own falsification at all three surfaces, as required, since `bool`-passing-as-`int` is silent by construction (F-9). REVERTED; `grep -n` confirms `:153` is back to `if not isinstance(limit, int) or isinstance(limit, bool):` and `:155` to `limit > MAX_RETRY_LIMIT`, and the file passes `74 passed`.

    BARE FULL SUITE, at HEAD `b2ad8358872da2591af5bf0705be731bf0238a08`, run as `python3 -m pytest` with no added flags (no `-n0`, no second `-q`, no `-p no:randomly`).

    PRE-CHANGE BASELINE, my own, same HEAD, before any edit:

    ```text
    31 failed, 4462 passed, 3 skipped, 4 xfailed in 33.54s
    ```

    AFTER:

    ```text
    31 failed, 4481 passed, 3 skipped, 4 xfailed in 34.47s
    ```

    Same 31 failures, `+19` passed = exactly the 19 tests this plan adds. Stronger than the counts, the failure SETS are identical: `diff` of the sorted `FAILED` lines before and after is EMPTY (`IDENTICAL FAILURE SET: zero regressions, zero new failures`). All 31 are pre-existing and untouched by this change (`test_run_viewer.py`, `test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_ipd_lifecycle_cli.py`, `test_novalnomerge_integration.py`, `test_worker_role_refusal.py`), none of which imports `run_recovery`'s budget surface.

    `aw check plans` NO-WORSENING against my own fresh baseline, as instructed (NOT a pass claim; it is red on pre-existing findings owned by other Sets, chiefly the `wslayout` plans): baseline `errors 11   warnings 0`, after `errors 11   warnings 0`. Unchanged.

    `aw sanitize --agent` clean: `{"outcome":"clean","exit":0,"findings":0}`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 2 E-leaves, one task group, one concern: enforce the spec's retry-budget range. This is deliberately the smallest of the three children the parent split into.

Open questions: OQ-01 (resume-invariance) is RESOLVED at review from repository evidence - it belongs to `runflags-01` (`uyeko5`) E-06, which already owns the frozen-value rule - and has been removed from E-01 rather than left as an optional clause. No blocking question remains.

This plan is `reviewed` and requires explicit human approval before execution.

Scope fence: touch ONLY `agent_workflows/run_recovery.py` and `tests/test_run_recovery_cli.py` (test file: additive cases only; no existing assertion weakened, removed, or altered). Do NOT change `DEFAULT_RETRY_LIMIT`'s VALUE or delete the ruling comment at `:47-61` (you MAY update that comment's forward reference to name the new validator, which is the one edit to it this plan permits). Do NOT touch `run_evidence.py` (Order 1 and Order 2 own it). Do NOT add a CLI flag: `--retry-budget` belongs to `runflags-01` (`uyeko5`) E-04, which is written to CALL this plan's validator. Do NOT modify `retry_budget_remaining`'s `max(0, ...)` clamp. Do NOT reuse `RetryLimitExceededError` for the range refusal. Do NOT create a new test module or a second copy of the bound. COORDINATION, inherited from the parent (F-7) and RE-MEASURED at review (F-11): APPROVED `0soncw` also claims `tests/test_run_recovery_cli.py` and is rewriting the command strings its assertions invoke, but it has landed NOTHING there yet (last three commits `8a99c7ca`, `99111c4c`, `caf658b4`). Re-measure that file (`git log --oneline -- <file>` plus a read of the invoked commands) immediately before editing; if `0soncw` has landed changes there by then, report it rather than merging blind. No SIBLING in this Set shares this plan's paths, so unlike `zub5f1` there is no same-file serialization requirement here. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at, from the PRIMARY checkout. The load-bearing evidence is the TWO SABOTAGES in V-02: a boundary test that has only been observed passing does not prove the boundary, and the bool guard is silent by construction so it needs its own falsification. Do NOT describe this change as fixing anything an operator can currently hit: both helpers are DORMANT (F-10), no CLI flag exists, and the Scope check says so. Do NOT claim `aw check plans` passes; the bar is no-worsening against your own fresh baseline.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify with `git restore --staged <path>`, and re-run that check after any failed commit attempt, since a hook failure invalidates it. Prefer `aw commit <plan> -- <paths>`.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
