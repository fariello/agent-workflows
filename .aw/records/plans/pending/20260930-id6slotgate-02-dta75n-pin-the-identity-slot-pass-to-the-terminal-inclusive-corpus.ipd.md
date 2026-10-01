# IPD: Pin the identity-slot pass to the terminal-inclusive corpus with a direct regression row

- Date: 2026-09-30
- Kind: child
- Concern: Backlog `e2j5w4` reports that `check_engine.check_collisions` builds the record list feeding `_check_identity_slots` under the caller's liveness filter, so `aw check all` reported zero `check.id6-identity-slot` findings while three live D140 violations sat on disk. MEASURED IN THIS LANE AT HEAD `522598b6`, THE CODE HALF IS ALREADY FIXED and the item's predicted divergence no longer reproduces: the enumeration in `check_collisions` now passes `include_retired=True` unconditionally and `records.append` is unguarded, so only the setid pass consults `caller_visible`. `check_collisions(root)` and `check_collisions(root, include_retired=True)` both return `Counter()` on the live tree. That fix arrived through collpop `t0jyb2`, whose finding table names this very item ("Same defect as backlog `e2j5w4`"), and the three named walkthroughs were separately re-id'd by `nrqo90`. WHAT IS NOT FIXED IS THE DEFENCE. The fix is pinned by EXACTLY ONE assertion in the whole suite, and that assertion is a BY-PRODUCT of a test about something else. Re-introducing the exact regression the item describes (re-guarding `records.append` with `include_retired or not is_retired(p, record_type)`) reds `1 failed, 3245 passed` out of a 3246-test suite, and the single failure is `tests/test_collision_population_parity.py::test_collision_population_parity`, a test whose stated subject is check-versus-doctor PARITY. Worse, its three parity equality assertions ALL STILL PASS under the mutation, because the regression moves BOTH surfaces together; what fails is its incidental step-(3) `assertIn(slot_finding, check_default)`. So the guard is one line away from being silently retired by anyone legitimately editing a parity test, and `tests/test_check_engine.py::CollisionTests`, the table that owns this rule and holds eleven rows including two identity-slot rows, passes the mutation untouched because every fixture file it builds is LIVE.
- Scope: Close `e2j5w4` with the invariant defended where it belongs rather than by accident. IN: (a) add two rows to the `CollisionTests.COLLISIONS` table in `tests/test_check_engine.py` whose fixtures place the identity-slot violation's files under a TERMINAL directory, one per (a)/(b) rule half, so the table that owns this rule fails the regression directly; (b) record in `_check_identity_slots`'s docstring that its corpus is terminal-inclusive BY CONTRACT and name the rows that pin it, because that function is where a future reader looks and it currently says nothing about the corpus it is handed; (c) append a dated measurement correction to backlog item `e2j5w4` recording that `t0jyb2` shipped its suggested fix, without touching its requirements, `- Status:` or `- Blocks-Release:`. OUT: any change to `check_engine.check_collisions`' or `_check_identity_slots`' BEHAVIOR, which measures correct on all four axes probed at authoring; widening the setid pass, whose narrow corpus is deliberate and documented; renaming any walkthrough (`nrqo90` already did, and re-renaming would rewrite cited history); the `CollisionTests` census/anti-vacuity concerns and the DECISIONS D140 parenthetical correction, both owned by sibling plan `aisk5z` at Order 01 in this same Set.
- Scope-Paths: tests/test_check_engine.py, agent_workflows/check_engine.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: e2j5w4
- Blocks-Release: next
- Set: id6slotgate
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: dta75n
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved

- 2026-09-30 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-D01 through PR-D08 all FIXED in place. Structural lint conformed at `author` and reports zero findings at `review-finalize`. INDEPENDENTLY RE-RAN ALL FIVE AUTHORING FACTS at HEAD `5b03be28c` and every MECHANISM reproduces (zero live collision findings; the four-axis probe at `default=1 widened=1`; the mutation redding the parity test; that test's two equality assertions True with the slot presence False), so the plan's premise is sound. What review found instead were three defects that would each have cost an execution pass: the authored STOP condition ("more than the single parity test") fires on a tree carrying one pre-existing unrelated failure and would have killed a correct run (F-8); the declared backlog `- Scope-Paths:` points at `open/` while the item is `graduated/`, which `aw check` reports at `error` and which would have made `aw commit` refuse E-04's own deliverable (F-10); and E-04 duplicates an append the already-approved sibling `aisk5z` E-05 owns and targets correctly (F-11). Scope narrowed from three paths to two, E-04 converted to a write-nothing verification, and every count bar restated as a delta (F-9). Added OQ-02 recording the decision. `ce.stale_record_scope_paths`, `ce.check_durable_carrier` and `aw check` are all now clean for this plan. Human approval is still required. (Review record: `.aw/records/reviews/20260930-id6slotgate-02-dta75n-pin-the-identity-slot-pass-to-the-terminal-inclusive-corpus.review.md`.)
- 2026-10-01 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): status transition applied by `aw ipd set reviewed dta75n`, kept beside the `/plan-review` line above as the attributed record of the transition itself. Its date is the setter's UTC stamp while the local date was 2026-09-30, which is the clock skew backlog `fnb8pl` owns; left exactly as the tool wrote it.
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `e2j5w4`, graduating it. Every claim below was measured in this lane at HEAD `522598b6` by mutation probe, not read off prose. THE ITEM'S CODE DEFECT IS ALREADY FIXED, which inverts the deliverable from a behavior change into a defence: `t0jyb2` gave the slot pass the terminal-inclusive corpus the item's SUGGESTED FIX asked for, so the plan must NOT re-perform it. What the mutation probe surfaced instead is that the shipped fix is pinned by one incidental assertion inside a parity test whose own equality assertions survive the regression, while the eleven-row table that owns this rule passes it untouched because all its fixtures are live. The deliverable is therefore two terminal-fixture regression rows in that table, a corpus contract in the docstring, and a record correction. The item's release gate is inherited unchanged because the invariant is one edit away from undefended until those rows exist.

## Goal

Leave the D140 identity-slot rule's TERMINAL-INCLUSIVE CORPUS defended by the test that owns the rule, so the
fix `t0jyb2` shipped cannot be silently undone, and leave `e2j5w4`'s record saying what is actually true.

This plan deliberately changes NO production behavior. Five facts were established at authoring by running
code, so the executor inherits measurement rather than this plan's description of it. ALL FIVE WERE
INDEPENDENTLY RE-RUN AT REVIEW and the mechanisms all reproduce; three absolute COUNTS inside fact 4 had
drifted and one of them was load-bearing for a stop condition, recorded as F-8 and F-9. Treat every number
below as context and re-derive it, per the live-count rule.

1. THE ITEM'S PREDICTED DIVERGENCE NO LONGER REPRODUCES. The item predicts 15 findings at the default scope
   with zero identity-slot findings, and those 15 plus 3 `check.id6-identity-slot` under `include_retired=True`.
   Measured on the live tree:

   ```text
   default: Counter()
   retired: Counter()
   ```

   Both the divergence and the findings are gone. The three walkthroughs the item names by path do not exist
   under those names; `nrqo90` renamed them and gave each its own `- Id:` with the documented plan demoted to
   `- Target-Id:`, which is the half sibling plan `aisk5z` measured independently.

2. THE FIX IS IN THE ENUMERATION, EXACTLY WHERE THE ITEM SAID THE DEFECT WAS. `check_collisions` now calls
   `_iter_type_files` with a hardcoded `include_retired=True`, appends to `records` unconditionally, and
   consults `caller_visible = include_retired or not is_retired(p, record_type)` only for the setid pass,
   which sits AFTER the append. Its docstring states the contract in a shouted paragraph beginning "BOTH
   IDENTITY PASSES IGNORE THE LIVENESS FILTER; THE SETID PASS DOES NOT", citing IPD `sk7ggr` E-05 and collpop
   `t0jyb2`. This is the item's SUGGESTED FIX ("Give the identity-slot pass the same terminal-inclusive corpus
   the id6 pass already uses, and keep the setid pass on the caller's corpus"), already performed.

3. THE BEHAVIOR IS CORRECT ON ALL FOUR AXES, not merely on the shape the item happened to file. Probed with
   synthetic trees, counting only `check.id6-identity-slot`, at both `include_retired` values:

   ```text
   (i) owner executed / offender live walkthrough : default=1 widened=1
   (ii) owner pending / offender executed plan    : default=1 widened=1
   (iii) both executed                            : default=1 widened=1
   (iv) rule-(a) violator itself executed         : default=1 widened=1
   ```

   So neither the OWNER's retirement, the OFFENDER's retirement, nor both together hides a finding, and rule
   (a) (declared `- Id:` disagreeing with the file's own slot) is equally terminal-inclusive. This is why the
   plan changes no behavior: there is nothing left to fix.

4. THE WHOLE-SUITE PIN IS A SINGLE ASSERTION, AND IT IS INCIDENTAL. Re-introducing the item's exact regression
   by guarding the append with the caller's filter, then running the bare suite:

   ```text
   FAILED tests/test_collision_population_parity.py::CollisionPopulationParityTests::test_collision_population_parity
   1 failed, 3245 passed, 2 skipped, 3 warnings in 122.67s (0:02:02)
   ```

   ONE SLOT-RELATED FAILURE, and that property is what matters rather than the absolute figures, which have
   drifted. RE-MEASURED AT REVIEW on an unmutated tree the suite ALREADY carries one unrelated failure
   (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, backlog
   `fnb8pl`), so the mutated run reports `2 failed, 3426 passed, 2 skipped` and the regression's own
   contribution is the single parity test. E-01's stop condition is therefore a DELTA against the baseline,
   never a count (F-8). Run per-file under the same mutation, the four other files that name this rule are all
   GREEN, which is the load-bearing half of this fact: `tests/test_check_engine.py`, `tests/test_doctor.py`,
   `tests/test_walkthrough_id6.py` and `tests/test_artifact_adopt.py` each pass unmutated and mutated alike
   (re-measured at review: 50, 37, 4 and 40 respectively; the authored 49 and 35 were stale, F-9, so the
   executor must re-derive these rather than compare against any figure printed here). The three that call
   `check_collisions` at all pass `include_retired=True` explicitly, which is the value the regression does not
   affect.

5. THAT ONE TEST'S OWN SUBJECT SURVIVES THE REGRESSION, which is what makes the pin fragile rather than merely
   thin. Its docstring says it asserts "that aw check all and aw doctor report the identical set of collision
   findings". Evaluating its three equality assertions under the mutation:

   ```text
   PARITY assertion (1) default check==doctor : True
   PARITY assertion (2) widened check==doctor : True
   slot finding present in check_default      : False
   ```

   Both surfaces regress TOGETHER, so parity holds and the test's stated claim is untouched. The only thing
   that fails is its step-(3) `assertIn(slot_finding, check_default)`, a presence check the test carries as
   setup for the parity claim. A future author narrowing that test to its own subject would delete the
   repository's only guard against this defect and see a green suite. Meanwhile `CollisionTests` in
   `tests/test_check_engine.py`, whose docstring says all three collision rules "belong in one table", holds
   eleven rows of which two are identity-slot rows, and every fixture path in all eleven is LIVE (measured: no
   row writes under `executed/`, `done/`, `superseded/`, `not-executed/` or `graduated/`), so the table that
   owns the rule cannot see this regression at all.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-establish the baseline before changing anything

- [x] E-01 RE-VERIFY THE FIVE AUTHORING FACTS AT THE EXECUTION HEAD AND CAPTURE THE BASELINE, because this plan's entire shape rests on the claim that the behavior fix already shipped, and executing it against a tree where that is false would leave a real defect live behind two new green tests. Record, with output: `check_engine.check_collisions(root)` and `check_collisions(root, include_retired=True)` as rule counters on the live tree; the four-axis synthetic probe from Goal fact 3 (owner retired, offender retired, both retired, and a rule-(a) violator that is itself retired), each at both `include_retired` values; a bare `python3 -m pytest` summary line; and `aw check all` output. THEN RE-RUN THE MUTATION PROBE that establishes facts 4 and 5, because it is the measurement this plan's value depends on: guard the `records.append` call in `check_collisions` with `include_retired or not is_retired(p, record_type)`, run the bare suite, record which tests fail, evaluate the parity test's three equality assertions directly, and RESTORE the file with `git checkout --` verifying `git status --short` shows no modification to `agent_workflows/check_engine.py`.
  - THE STOP CONDITION IS A DELTA, NOT AN ABSOLUTE COUNT, and this is the correction F-8 and F-9 force. STOP and report (the tree is not the one this plan was authored against, and the correct response is a fresh plan) if EITHER the collision calls return any `check.id6-identity-slot` finding on the live tree, OR the mutation reds any test BEYOND the parity test and whatever was ALREADY failing on the unmutated tree. Do NOT stop merely because the suite shows more than one failure: measured at review, the baseline itself carries one pre-existing unrelated failure (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, owned by backlog `fnb8pl`, a local-versus-UTC history-clock defect), so the mutation reds TWO tests and the authored "more than the single parity test" trigger would have fired spuriously and killed a correct run. Compute the delta against the baseline run captured in this same item; never against a number quoted in this plan.
  - Depends on: none
  - Expected outcome: both collision calls return zero findings of every rule; all four probe axes report 1 finding at BOTH `include_retired` values; the baseline bare-suite summary line is on record WITH any pre-existing failure named; the mutation adds exactly `tests/test_collision_population_parity.py::CollisionPopulationParityTests::test_collision_population_parity` to that baseline failure set and nothing else; the parity test's two equality assertions both evaluate True under that mutation while the slot-presence check evaluates False; and `agent_workflows/check_engine.py` is unmodified afterwards.
  - Execution state: performed

### Task group 2: defend the corpus in the table that owns the rule

- [x] E-02 ADD TWO TERMINAL-FIXTURE ROWS TO `CollisionTests.COLLISIONS` IN `tests/test_check_engine.py`, one per half of the identity-slot rule, so the table that owns this rule fails the regression directly instead of delegating its only defence to a parity test.
  - ROW ONE covers rule (b) with a RETIRED OWNER: an executed plan declaring `- Id: aaa111` at `.aw/records/plans/executed/20260101-demo-01-aaa111-a.ipd.md` (built with `_plan_text("aaa111", status="executed")`) beside a live walkthrough at `.aw/records/walkthroughs/20260101-demo-01-aaa111-w.walkthrough.md` (built with `_walk_text()`, declaring no `- Id:`). This is the `p7dqwz` shape with the owner in terminal history, and it is the shape the item's three real violations had.
  - ROW TWO covers rule (a) with a RETIRED VIOLATOR: a single executed plan at `.aw/records/plans/executed/20260101-demo-01-slotaa-a.ipd.md` built with `_plan_text("fmbbb1", status="executed")`, whose slot `slotaa` disagrees with its own declared `fmbbb1`. This half is independent because rule (a) never consults another file, so a fix that widened only the ownership gather would still leave it blind.
  - EXPECTED RULE SET, measured at authoring and RE-MEASURED AT REVIEW: both rows expect EXACTLY `(IDENTITY_SLOT,)` from `check_collisions` AND from the full sweep, since the executed-directory fixtures trip no incidental content rule, unlike the live-fixture rows that carry `DRAFT_READY`. Review confirmed `Counter({'check.id6-identity-slot': 1})` for each shape at both `include_retired` values. Re-measure rather than trusting either figure.
  - ROW CONVENTIONS: give each row needles naming BOTH sides where two files are involved, per the table's stated convention that the detail is asserted and not only the rule id, and write the "why this row exists" column to say the fixture is TERMINAL ON PURPOSE and that the row exists because the corpus, not the rule logic, is what regressed.
  - PATH LITERALS, NOT CONSTANTS: write the paths as literals rather than through the `PLANS`/`WALK` constants, which point at `pending/` and the live walkthroughs directory, and add a brief comment saying so, since a later reader "tidying" them onto the constants would silently retire both rows.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_check_engine.py -o addopts=""` passes, `CollisionTests.COLLISIONS` holds exactly two rows MORE than the count re-derived in E-01 (13 at review, where the table holds 11, but re-derive rather than asserting 13 since another lane may add a row), and re-applying the E-01 mutation reds `tests/test_check_engine.py` where fact 4 measured it green.
  - Execution state: performed

- [x] E-03 RECORD THE CORPUS CONTRACT IN `_check_identity_slots`' DOCSTRING, because that function is where the next reader of this rule looks and it currently says nothing at all about the corpus it is handed, while the contract lives only in its CALLER's docstring. The function already carries three shouted paragraphs about what it deliberately does NOT detect and where that is detected instead, so a paragraph about its input is in keeping. State: that `records` is TERMINAL-INCLUSIVE BY CONTRACT and the function must never be given a liveness-filtered list; WHY, namely that an identity slot reusing an executed artifact's id6 collides with a permanently cited handle and breaks single-handle lookup, which is the same reasoning its `check.id6-collision` sibling already carries; that the caller enforces this by enumerating with `include_retired=True` unconditionally while only the setid pass consults `caller_visible`; and WHICH TESTS pin it, naming the two `CollisionTests` rows E-02 adds and `tests/test_collision_population_parity.py`, with the honest note that the latter's own parity assertions survive the regression so it is not the guard to rely on. Cite backlog `e2j5w4` and collpop `t0jyb2` as the history. Write no em or en dashes. Change no code in this item.
  - Depends on: E-02
  - Expected outcome: `git diff -- agent_workflows/check_engine.py` shows only added docstring lines inside `_check_identity_slots`, with no change to any statement, and the bare suite stays green.
  - Execution state: performed

### Task group 3: correct the record and gate

- [x] E-04 CONFIRM THE `e2j5w4` RECORD CORRECTION IS ALREADY OWNED BY THE SIBLING AND DO NOT RE-PERFORM IT. This item was authored as an append to backlog `e2j5w4`; review measured that sibling plan `aisk5z` (Order 01, same Set, already `- Status: approved`, `- Readiness: go-pending-approval`) carries the SAME append in its own E-05, which appends to BOTH `mw0s1y` and `e2j5w4`, names `aw backlog note` as the verb, declares the item at its correct `graduated/` path, and was corrected at review to select by id6. A second plan appending the same correction to the same record would either duplicate the paragraph or race it. So the action here is a VERIFICATION, not a write: read `.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md` and record whether `aisk5z`'s paragraph is present. If it IS present, this item is satisfied with no edit, and the record correction is attributed to `aisk5z`. If it is NOT present (because `aisk5z` has not executed yet), STILL DO NOT WRITE IT: that is `aisk5z`'s unexecuted obligation, not a gap, and the Deferred section carries `Carrier: aisk5z` for it. Write nothing to any backlog file in this plan. This plan's own `- Blocks-Release:` gate is discharged by its test coverage, not by the record edit.
  - Depends on: E-01
  - Expected outcome: no backlog file is modified by this plan (`git status --short` shows nothing under `.aw/records/backlog/`), and the evidence states whether `aisk5z`'s paragraph was found present or still pending, with the item's `- Status:` and `- Blocks-Release:` observed unchanged either way.
  - Execution state: performed

### Task group 4: regression gate

- [x] E-05 RUN THE FULL REGRESSION GATE AND COMPARE IT AGAINST THE E-01 BASELINE, so any failure is shown pre-existing rather than argued harmless. Run bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Then `aw ipd lint --phase pre-transition` on this plan, `aw check` compared against its E-01 baseline count, and `aw sanitize --agent`, which is not a formality here because the probe output this plan pastes contains temp-directory paths. FINALLY VERIFY THE WORKING TREE IS EXACTLY THE DECLARED SCOPE: E-01 and V-02 both temporarily modified `agent_workflows/check_engine.py`, so confirm with `git status --short` and with `git diff -- agent_workflows/check_engine.py` that the only surviving change to that file is E-03's docstring addition. Restore any residue by path name, never with `git stash`, a bare `git reset`, or `git checkout .`, since this checkout may be shared.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the suite summary line matches the E-01 baseline with no NEW failing test id (the pre-existing `fnb8pl` failure is expected in both and is not a regression) and an UNCHANGED test count (the two new rows are table rows inside one existing test); a conforming pre-transition lint; `aw check` no worse than baseline and with `check.scope-path-target-stale` absent for this plan; a clean sanitizer report; and a working tree holding exactly the TWO declared Scope-Paths with nothing under `.aw/records/backlog/`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NOT CODE STRUCTURE (AGENTS.md, GUIDING_PRINCIPLES P16). Both E-02 rows drive `check_engine.check_collisions` and `check_types` over a real fixture tree and assert on the returned findings and their details, which is the behavioral form. This plan deliberately does NOT add a test that greps `check_engine.py` for the unguarded `records.append`, even though that would pin the fix more directly, because that is precisely the code-pinning anti-pattern the contract forbids.
- THE COLLISION TABLE IS THE OWNER OF THIS RULE, and its own docstring says why: all three collision rules "are produced by a SINGLE pass of `check_collisions` over every supported type, which is why they belong in one table: the pass is where the interference between them lives". The corpus is a property of that pass, so the corpus rows belong in that table. It also warns that "the most dangerous mistake in this area is ADDING a rule that reports correct behavior", which is why E-02 adds no rule and only extends the fixture population.
- ROWS ASSERT AN EXACT RULE SET, INCLUDING INCIDENTAL RULES, and the table comment states the reason: the expected sets deliberately list rules "the fixture trips for reasons unrelated to collisions" because "trimming the assertion to 'the collision rules only' would let a content rule silently stop firing tree-wide". So E-02 must measure and record the full sweep's exact set for each new row rather than filtering to the slot rule.
- A RECORD UNDER `.aw/records/` IS APPENDED TO, NOT REWRITTEN. DECISIONS D140's `sk7ggr` bullet says so of itself ("deliberately left intact rather than rewritten"), and `nrqo90`'s E-07 applied the same rule to this very backlog item. E-04 appends.
- THE SETID PASS'S NARROW CORPUS IS DELIBERATE AND DOCUMENTED, not an oversight to fix alongside. `check_collisions`' docstring records that widening it would surface "within-type descriptive conflicts on retired records that are not active work", and the item's own SUGGESTED FIX says to keep it on the caller's corpus. This plan touches neither it nor `caller_visible`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-1 | The item's code defect is already fixed. `check_collisions` enumerates with a hardcoded `include_retired=True` and appends to `records` unconditionally; `caller_visible` gates only the setid pass, which follows the append. This is the item's SUGGESTED FIX verbatim, shipped by `t0jyb2`, whose finding table names `e2j5w4`. | Goal fact 2; the docstring paragraph "BOTH IDENTITY PASSES IGNORE THE LIVENESS FILTER; THE SETID PASS DOES NOT"; `t0jyb2` F-1 "Same defect as backlog `e2j5w4`". |
| F-2 | The item's predicted 0-versus-3 divergence does not reproduce: both collision calls return `Counter()` on the live tree. Its three named paths no longer exist, `nrqo90` having re-id'd them. | Goal fact 1 pasted counters; sibling plan `aisk5z` Goal fact 1 census naming commit `e83cb542`. |
| F-3 | The shipped behavior is correct on all four axes, not just the filed shape: a retired owner, a retired offender, both retired, and a retired rule-(a) violator each yield exactly 1 finding at BOTH `include_retired` values. Nothing remains to fix behaviorally. | Goal fact 3 four-axis probe. |
| F-4 | The fix's whole-suite pin is ONE assertion. Re-introducing the regression reds `1 failed, 3245 passed`; the four other test files naming this rule stay green because the three that call `check_collisions` all pass `include_retired=True` explicitly. | Goal fact 4 pasted suite summary and the four per-file summaries under mutation. |
| F-5 | That one test's OWN subject survives the regression: both surfaces regress together, so its two parity equality assertions evaluate True and only its incidental `assertIn(slot_finding, check_default)` fails. Narrowing the test to its stated claim would silently retire the repository's only guard. | Goal fact 5: `PARITY assertion (1) True`, `(2) True`, `slot finding present in check_default: False`. |
| F-6 | `CollisionTests`, the eleven-row table that owns this rule, cannot see the regression: every fixture path in all eleven rows is live (none under `executed/`, `done/`, `superseded/`, `not-executed/`, `graduated/`), so the corpus axis is untested where the rule is tested. | Goal fact 4 (`tests/test_check_engine.py` 49 passed under mutation); row-location sweep over `CollisionTests.COLLISIONS` printing `live` for all eleven. |
| F-7 | Rule (a) needs its own row rather than riding on rule (b). Rule (a) compares a file's slot against its OWN declared `- Id:` and consults no other file, so a partial fix that restored only the global ownership gather would leave it blind while the rule-(b) row passed. | `_check_identity_slots` rule (a) branch, which reads only `declared_id` and `slot_id6` of the file in hand; probe axis (iv) exercising it with the violator itself retired. RE-VERIFIED AT REVIEW: axis (iv) returns `default=1 widened=1` with the exact rule set `Counter({'check.id6-identity-slot': 1})`, confirming E-02's predicted `(IDENTITY_SLOT,)` for both new rows. |
| F-8 | ADDED AT REVIEW. THE AUTHORED STOP CONDITION MISFIRES AND WOULD HAVE KILLED A CORRECT RUN. E-01 told the executor to STOP if "the mutation reds more than the single parity test". Measured at review HEAD `5b03be28c`: the UNMUTATED suite already reports `1 failed, 3426 passed, 2 skipped` on `tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, a filed time-dependent local-versus-UTC history-clock defect owned by backlog `fnb8pl` (`open`, `bug`, `Blocks-Release: next`), unrelated to this mechanism. Under the mutation the suite reports `2 failed, 3426 passed`, so the authored trigger fires on a tree this plan IS correctly authored against, and the prescribed response ("a fresh plan") would discard a sound plan. | Baseline bare run and mutated bare run both captured at review; the mutated set is the baseline failure PLUS `tests/test_collision_population_parity.py::CollisionPopulationParityTests::test_collision_population_parity`. The stop condition is now a DELTA against a baseline captured in the same item. |
| F-9 | ADDED AT REVIEW. TWO PER-FILE COUNTS IN FACT 4 ARE STALE, so an executor comparing against them would read ordinary suite growth as a discrepancy. Re-measured at review, unmutated and mutated alike: `tests/test_check_engine.py` 50 (plan says 49), `tests/test_doctor.py` 37 (plan says 35), `tests/test_walkthrough_id6.py` 4, `tests/test_artifact_adopt.py` 40. The PROPERTY fact 4 rests on is unaffected and verified: all four files are GREEN under the mutation, so the slot guard really does live in only one test. The whole-suite figure `3245 passed` is stale for the same reason (`3426` at review). | Four per-file runs at review, before and after applying the mutation; the four green results are identical in both. |
| F-10 | ADDED AT REVIEW. THE DECLARED BACKLOG SCOPE-PATH DOES NOT EXIST, AND `aw commit` WOULD HAVE REFUSED E-04's OWN DELIVERABLE. The plan declared `.aw/records/backlog/open/20260921-id6slotgate-01-e2j5w4-...backlog.md`; the item sits in `graduated/` (the runner graduated it, recorded in its own history as "graduated by run run-20260930T053024Z-3198670: dta75n"). `ce.stale_record_scope_paths` returns `StaleScopePath(..., classification='moved', resolved=('.aw/records/backlog/graduated/...',))`, and `aw check` reports `check.scope-path-target-stale` against this plan at severity `error`. Mechanically: `ipd_lifecycle._scope_match` returns False for the real path against the declared pattern and `_is_implicitly_allowed` also returns False, so `aw commit <plan> -- <real path>` refuses as out-of-scope. | `ce.stale_record_scope_paths` output; `aw check` finding; direct evaluation of `_scope_match` / `_is_implicitly_allowed`; the item's own `- Status: graduated` front matter. |
| F-11 | ADDED AT REVIEW. E-04 DUPLICATES WORK THE ALREADY-APPROVED SIBLING OWNS. `aisk5z` (Order 01, same Set, `- Status: approved`, `- Readiness: go-pending-approval`) carries E-05: "CORRECT BOTH BACKLOG ITEMS' MEASUREMENTS", appending the dated paragraph to `mw0s1y` AND to `e2j5w4`, naming `aw backlog note` as the verb and instructing selection by id6 because "BOTH ITEMS ARE NOW UNDER `graduated/`". Its `- Scope-Paths:` declares the `graduated/` path for both. Its review record PR-001 retargeted exactly these paths and its D-4 decision row records why. So two plans in one Set were each told to append the same correction to one record, with the lower-Order one already approved and correctly targeted. | `aisk5z` front matter and E-05 text; `.aw/records/reviews/20260929-id6slotgate-01-aisk5z-...review.md` rows PR-001 and D-4. |

## Proposed changes (ordered, validatable)

1. Re-verify the five facts at the execution HEAD, capture the suite and `aw check` baselines, and re-run the
   mutation probe that establishes the pin's thinness, refusing to proceed if the tree differs (E-01 / V-01).
2. Add two `CollisionTests.COLLISIONS` rows whose identity-slot fixtures live under a terminal directory, one
   per rule half, so the owning table fails the regression directly (E-02 / V-02).
3. Record the terminal-inclusive corpus contract, its reason, and the tests that pin it in
   `_check_identity_slots`' docstring, changing no code (E-03 / V-03).
4. Verify the `e2j5w4` record correction is carried by sibling `aisk5z` E-05 and write nothing to any backlog
   file from this plan (E-04 / V-04).

## Deferred / out of scope (with reason)

- ANY BEHAVIOR CHANGE TO `check_collisions` OR `_check_identity_slots`. Measured correct on four axes (F-3).
  Re-performing the item's SUGGESTED FIX would be a no-op at best and a regression at worst.
  - Carrier-Declined: there is no outstanding work here to carry. The four-axis probe in Goal fact 3 measures the behavior as already correct at both `include_retired` values, so this row records a NON-task rather than a deferral, and naming a carrier for it would assert that someone still owes a behavior fix that nobody owes.
- WIDENING THE SETID PASS. Deliberate and documented; the item's own suggested fix says to keep it as is.
  - Carrier-Declined: not a deferral but a settled decision recorded twice already. `check_collisions`' docstring states the setid pass keeps the caller's corpus to avoid surfacing within-type descriptive drift on retired records, and backlog `e2j5w4`'s own SUGGESTED FIX asks for exactly this. Nothing is outstanding, so there is nothing for a carrier to own.
- RENAMING ANY WALKTHROUGH. `nrqo90` already did it; re-renaming would rewrite history other records cite.
  - Carrier-Evidence: .aw/records/plans/executed/20260926-wkthid6-01-nrqo90-mint-a-walkthrough-s-own-id6-in-write-walkthrough-add-the-wa.ipd.md
- THE `tests/test_walkthrough_id6.py` CENSUS GUARD, DECISIONS D140's stale parenthetical, backlog `mw0s1y`,
  AND THE `e2j5w4` RECORD CORRECTION ITSELF. All owned by sibling plan `aisk5z` (Order 01, this Set), whose
  E-05 appends the dated measurement correction to BOTH `mw0s1y` and `e2j5w4` through `aw backlog note`,
  selecting by id6. Measured at review: `aisk5z` is already `- Status: approved` with
  `- Readiness: go-pending-approval`, and its own review record (PR-001) retargeted its declared paths to
  `graduated/` for exactly this item. SO THIS PLAN NO LONGER OVERLAPS IT AT ALL: the backlog file is out of
  this plan's `- Scope-Paths:` and E-04 is a verification that writes nothing, which removes the ordering
  hazard the authored version tried to manage rather than merely sequencing it.
  - Carrier: aisk5z
  - Carrier-Evidence: .aw/records/plans/executed/20260929-id6slotgate-01-aisk5z-retire-the-walkthrough-identity-slot-defect-unpin-the-census.ipd.md
- NARROWING OR REWRITING `tests/test_collision_population_parity.py`. Its parity subject is legitimate and its
  incidental slot assertion is currently load-bearing. Once E-02 lands, the guard no longer depends on it, but
  removing the assertion is not this plan's business and would reduce coverage before a reviewer asked for it.
  - Carrier-Declined: deliberately nobody's task, and that is the point of the row. OQ-01 resolves from the repository that the assertion should be KEPT permanently, not merely deferred: it covers the `check_types` full-sweep seam the E-02 rows do not, and it is what stops the parity assertions being vacuously satisfiable by two surfaces that both report nothing. A carrier here would schedule a removal this plan argues against.
- A TEST THAT GREPS `check_engine.py` FOR THE UNGUARDED APPEND. Forbidden as a code-pinning test (P16).
  - Carrier-Declined: prohibited by contract rather than postponed. AGENTS.md forbids tests that read production source with `inspect`, `ast`, regex or substring search, and GUIDING_PRINCIPLES P16 says the same, so this must never be carried by anyone. The behavioral equivalent is E-02, which is in scope.

## Scope check

- Over-scope: none, AND THE SCOPE WAS NARROWED AT REVIEW FROM THREE PATHS TO TWO. The plan now adds two test
  rows (`tests/test_check_engine.py`) and a docstring paragraph (`agent_workflows/check_engine.py`), and
  touches no record. The third authored path, backlog `e2j5w4`, was REMOVED for two measured reasons: it was
  declared under `open/` while the item sits in `graduated/` (`ce.stale_record_scope_paths` classifies it
  `moved`, and `aw check` reports `check.scope-path-target-stale` at severity `error`, so `aw commit` would
  have refused the very file E-04 was told to edit), and the append is already owned by sibling `aisk5z` E-05,
  which declares the correct path. Both declared paths are modified by this plan, so no `--scope-ack` is owed.
- RE-DERIVE THE PATHS RATHER THAN TRUSTING THEM. Both remaining paths are source files that do not move, but
  if `aw check` reports `check.scope-path-target-stale` against this plan at execution, STOP and report rather
  than editing an undeclared path: the declaration is frozen by D141 precisely to preserve the said-versus-did
  signal.
- Under-scope: the plan does NOT make `aw check`'s CLI surface assert this rule end-to-end (no CLI-level test
  names `check.id6-identity-slot` today). Measured at authoring, the end-to-end path does work: on a synthetic
  repo holding an executed plan owning `aaa111` and a live walkthrough squatting it, `aw check all --agent`
  reports the finding with its D140 remediation in `next` and exits nonzero. A CLI-level regression row is a
  legitimate follow-up but the engine-level rows in E-02 are where the corpus regression is visible, and
  duplicating them at the CLI would pin the same fact twice.

## Required tests / validation

- `python3 -m pytest tests/test_check_engine.py -o addopts=""` green with the two new rows, and the table's
  growth verified by a BEFORE and AFTER count (exactly +2) rather than by eye or against a fixed total.
- THE MUTATION PROBE IS THE VALIDATION THAT MATTERS, because "the rows pass" and "the rows would have caught
  the regression" are independent claims and only the second is this plan's deliverable. With the item's exact
  regression re-applied, `tests/test_check_engine.py` MUST fail where fact 4 measured it green, and the
  failure message must name the terminal rows. The mutation must then be reverted with `git checkout --` and
  the revert verified with `git status --short`.
- Bare `python3 -m pytest` (no added flags; the configured `addopts` already supplies quiet, parallel and the
  fast subset, and a second `-q` would suppress the `N passed` line this plan must paste), compared against
  the E-01 baseline AS A DELTA. The suite is NOT green here: one pre-existing unrelated failure
  (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`, owned by
  backlog `fnb8pl`) is expected in both runs, so the bar is that no NEW failure appears, and this plan must
  neither claim a green suite nor attempt to fix that defect.
- `aw ipd lint --phase pre-transition` on this plan, `aw check` compared against its E-01 baseline, and
  `aw sanitize --agent` (the pasted probe output contains temp-directory paths, so the sanitizer is not a
  formality here).

## Spec / documentation sync

- NO SPEC AMENDMENT IS REQUIRED, and the reason is that the contract this plan defends is ALREADY WRITTEN in
  the two places that govern it. `.aw/records/walkthroughs/README.md` states the D140 rule and names
  `check.id6-identity-slot` as its enforcement, and `check_collisions`' docstring states the corpus split the
  identity passes take. Spec `2lcqno` (approved, setid semantics) states at its acceptance criterion 4 that
  `aw check` and `aw doctor` must report the same population on both axes, which this plan preserves and does
  not alter. No `.spec.md` file is in Scope-Paths and none is touched.
- E-03's docstring paragraph IS the documentation sync: the corpus contract currently exists only in the
  caller, and this plan puts it where the function that depends on it can be read alone.
- DECISIONS D140's `sk7ggr` parenthetical is stale about this exact behavior (it still says the identity-slot
  pass deliberately honors the liveness filter). Correcting it is deliberately NOT here: sibling plan `aisk5z`
  E-04 already owns that append, and two plans appending to one D140 bullet would conflict.

## Open questions

### OQ-01: Should the incidental slot assertion in the parity test be kept once E-02 lands?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT AUTHORING FROM THE REPOSITORY, keep it, and the reasoning is measurement rather than preference. The assertion is currently the repository's ONLY guard against this regression (F-4), so removing it in the same change that adds a replacement would leave the invariant momentarily defended by untested new rows; and it is not redundant even afterwards, because it asserts the finding is present in `check_types(root, ["all"])` (the full-sweep seam a user reaches through `aw check all`) while the E-02 rows assert `check_collisions` and the sweep over a DIFFERENT fixture population. Its own test docstring gives the second reason to leave it: the parity claim needs a finding that EXISTS in order to compare two surfaces, so deleting the presence check would make the parity assertions satisfiable by two surfaces that both report nothing, which is exactly the vacuity the mutation probe exposed. What this plan does about it is in E-03: name the parity test as a pin while recording honestly that its parity assertions survive the regression, so a future author narrowing it knows what they would be removing. RE-VERIFIED AT REVIEW by direct evaluation: under the mutation the two parity equalities return True and the slot-presence check returns False, exactly as stated, so the vacuity argument is measured rather than asserted.

### OQ-02: Does this plan still owe the `e2j5w4` record correction, given sibling `aisk5z` also carries it?

- Blocking: no
- Status: resolved
- Owner: plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us)
- Resolution or deferral rationale: NO, and this was RESOLVED FROM THE REPOSITORY rather than left to the executor, because the authored instruction would have produced either a duplicated paragraph or a refused commit. Three measurements decide it. (1) `aisk5z` (Order 01, same Set) is ALREADY `- Status: approved` and its E-05 appends the dated correction to BOTH `mw0s1y` and `e2j5w4` by id6 through `aw backlog note`, declaring the `graduated/` path (F-11). (2) This plan declared the item under `open/`, which does not exist: `ce.stale_record_scope_paths` classifies it `moved`, `aw check` reports `check.scope-path-target-stale` at `error`, and `ipd_lifecycle._scope_match` returns False for the real path, so `aw commit <plan> -- <real path>` would have REFUSED E-04's own deliverable (F-10). (3) Removing the record from this plan's scope costs the gate nothing, because this plan is `e2j5w4`'s SOLE `- From-Backlog:` carrier (verified: `aisk5z` carries `mw0s1y`), so the gate is discharged by this plan reaching `executed` on the strength of its test coverage, not by the prose edit. THE ALTERNATIVE REJECTED was to retarget the path to `graduated/` and keep the append with an ordering rule, which the authored E-04 attempted: it leaves two approved plans writing the same correction to one record, and the lower-Order one is already correctly targeted, so the ordering rule manages a collision that simply need not exist.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted rule counters for `check_collisions(root)` and `check_collisions(root, include_retired=True)` on the live tree, both empty of every rule. Pasted four-axis probe output showing `default=1 widened=1` on every axis, including the rule-(a) axis. The baseline bare `python3 -m pytest` summary line WITH ANY PRE-EXISTING FAILING TEST ID NAMED, plus the baseline `aw check` finding count, both recorded for E-05 comparison; a baseline that reports only a count without naming its failures cannot support the delta comparison E-05 and V-05 require. Then the MUTATION evidence: the pasted bare-suite summary under mutation naming which tests failed, the four per-file summaries for `tests/test_check_engine.py`, `tests/test_doctor.py`, `tests/test_walkthrough_id6.py` and `tests/test_artifact_adopt.py` (re-derived counts, not compared against the figures in fact 4, which F-9 measures as stale), the three-line parity-assertion evaluation showing both equality assertions True and the slot-presence check False, and a `git status --short` proving `agent_workflows/check_engine.py` was restored. State explicitly that the refusal condition did NOT trigger, expressed as the DELTA it now is: no live identity-slot finding, and no mutated failure beyond the parity test and the baseline's own failures (F-8). A run that pastes the baseline but not the mutation evidence does not satisfy this item, because the mutation is what establishes the plan's premise.
  - Observed evidence: PASS.
    1. Live tree collision rule counters:
       ```
       default: Counter()
       retired: Counter()
       ```
    2. Four-axis synthetic probe output:
       ```
       (i) owner executed / offender live walkthrough : (1, 1)
       (ii) owner pending / offender executed plan    : (1, 1)
       (iii) both executed                            : (1, 1)
       (iv) rule-(a) violator itself executed         : (1, 1)
       ```
    3. Baseline bare `python3 -m pytest` summary line:
       ```
       FAILED tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs
       1 failed, 4231 passed, 2 skipped, 3 warnings in 249.54s (0:04:09)
       ```
       (Pre-existing hang guard timeout on `test_statusline_behavior.py` under parallel load; passes cleanly standalone in 29.17s).
    4. Baseline `aw check all` finding count:
       `errors  28   warnings  2   info  43` (total 73 findings, 0 `check.id6-identity-slot`, 0 `dta75n` findings).
    5. Mutation evidence:
       Bare suite summary under mutation:
       ```
       FAILED tests/test_collision_population_parity.py::CollisionPopulationParityTests::test_collision_population_parity
       1 failed, 4231 passed, 2 skipped, 3 warnings in 169.96s (0:02:49)
       ```
       Four per-file test summaries under mutation (all green):
       `tests/test_check_engine.py`: 50 passed
       `tests/test_doctor.py`: 37 passed
       `tests/test_walkthrough_id6.py`: 4 passed
       `tests/test_artifact_adopt.py`: 40 passed
       Combined: `131 passed in 10.40s`
       Parity-assertion evaluation under mutation:
       ```
       PARITY assertion (1) default check==doctor : True
       PARITY assertion (2) widened check==doctor : True
       slot finding present in check_default      : False
       ```
       Restoration: `git checkout -- agent_workflows/check_engine.py` executed; `git status --short` verified completely clean.
    Refusal / stop condition delta check: did NOT trigger. Zero live identity-slot findings, and the mutation added exactly `tests/test_collision_population_parity.py::CollisionPopulationParityTests::test_collision_population_parity` as the single slot-related failure with no unexpected test regressions.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted `git diff -- tests/test_check_engine.py` showing the two added rows with their terminal fixture paths, their measured expected rule sets, their needles, and their why-columns. Pasted `python3 -m pytest tests/test_check_engine.py -o addopts=""` summary (do NOT add `-q`, which compounds with the cleared-then-absent default into suppressing the count line this item needs). A pasted BEFORE and AFTER count of `CollisionTests.COLLISIONS` showing it grew by exactly two, rather than an assertion that it equals any fixed number. THEN THE DECISIVE EVIDENCE: re-apply the E-01 mutation, run `python3 -m pytest tests/test_check_engine.py -o addopts=""`, and paste the FAILURE together with enough of the assertion message to show it names the two terminal rows by their case strings; then restore and paste a `git status --short` showing `agent_workflows/check_engine.py` unmodified. A passing row set without this mutation failure does NOT satisfy this item: it would show the rows run, not that they guard anything.
  - Observed evidence: PASS.
    1. `git diff -- tests/test_check_engine.py`:
       ```diff
       +        # PATH LITERALS, NOT CONSTANTS: written as literals rather than through the
       +        # PLANS/WALK constants (which point at pending/ and the live walkthroughs dir)
       +        # because the fixtures are terminal on purpose. Tidying them onto constants
       +        # would silently retire both rows.
       +        (
       +            "a walkthrough with no declared Id whose slot is a RETIRED plan's identity",
       +            (
       +                (
       +                    ".aw/records/plans/executed/20260101-demo-01-aaa111-a.ipd.md",
       +                    _plan_text("aaa111", status="executed"),
       +                ),
       +                (
       +                    ".aw/records/walkthroughs/20260101-demo-01-aaa111-w.walkthrough.md",
       +                    _walk_text(),
       +                ),
       +            ),
       +            (IDENTITY_SLOT,),
       +            (
       +                "20260101-demo-01-aaa111-w.walkthrough.md",
       +                "aaa111",
       +                "20260101-demo-01-aaa111-a.ipd.md",
       +            ),
       +            (),
       +            "IDENTITY-SLOT RULE (b) WITH A RETIRED OWNER (backlog e2j5w4, collpop t0jyb2): the "
       +            "fixture is TERMINAL ON PURPOSE and this row exists because the corpus, not the rule logic, "
       +            "is what regressed. An executed plan's id6 is permanently cited, so a live walkthrough "
       +            "squatting it in its identity slot must be reported even when the owner is in terminal "
       +            "history. The finding must name the offender AND the owner",
       +        ),
       +        (
       +            "a RETIRED plan whose declared Id differs from its filename slot",
       +            (
       +                (
       +                    ".aw/records/plans/executed/20260101-demo-01-slotaa-a.ipd.md",
       +                    _plan_text("fmbbb1", status="executed"),
       +                ),
       +            ),
       +            (IDENTITY_SLOT,),
       +            ("slotaa", "fmbbb1"),
       +            (),
       +            "IDENTITY-SLOT RULE (a) WITH A RETIRED VIOLATOR (backlog e2j5w4, collpop t0jyb2): the "
       +            "fixture is TERMINAL ON PURPOSE and this row exists because the corpus, not the rule logic, "
       +            "is what regressed. Rule (a) never consults another file, so widening only the global "
       +            "ownership gather would leave a retired violator blind while rule (b) passed. The detail "
       +            "must cite both ids",
       +        ),
       ```
    2. Summary of `python3 -m pytest tests/test_check_engine.py -o addopts=""`:
       ```
       ============================== 50 passed in 8.28s ==============================
       ```
    3. `CollisionTests.COLLISIONS` table count before and after:
       `BEFORE count: 11`
       `AFTER count: 13`
       (Grew by exactly 2).
    4. Decisive mutation evidence:
       Re-applied E-01 mutation, executed `python3 -m pytest tests/test_check_engine.py -o addopts=""`:
       ```
       FAILED tests/test_check_engine.py::CollisionTests::test_one_pass_reports_exactly_the_collisions_present
       AssertionError: ... `check_collisions` was wrong for 2 of 13 trees. ...
         a walkthrough with no declared Id whose slot is a RETIRED plan's identity:
           - `check_collisions` expected ['check.id6-identity-slot'], got nothing
           - the full sweep over the same tree expected ['check.id6-identity-slot'], got nothing
           - the findings never mention ['20260101-demo-01-aaa111-w.walkthrough.md', 'aaa111', '20260101-demo-01-aaa111-a.ipd.md'], so a user cannot tell WHICH files are involved; they said ''
           this row exists because: IDENTITY-SLOT RULE (b) WITH A RETIRED OWNER (backlog e2j5w4, collpop t0jyb2): the fixture is TERMINAL ON PURPOSE and this row exists because the corpus, not the rule logic, is what regressed. An executed plan's id6 is permanently cited, so a live walkthrough squatting it in its identity slot must be reported even when the owner is in terminal history. The finding must name the offender AND the owner
         a RETIRED plan whose declared Id differs from its filename slot:
           - `check_collisions` expected ['check.id6-identity-slot'], got nothing
           - the full sweep over the same tree expected ['check.id6-identity-slot'], got nothing
           - the findings never mention ['slotaa', 'fmbbb1'], so a user cannot tell WHICH files are involved; they said ''
           this row exists because: IDENTITY-SLOT RULE (a) WITH A RETIRED VIOLATOR (backlog e2j5w4, collpop t0jyb2): the fixture is TERMINAL ON PURPOSE and this row exists because the corpus, not the rule logic, is what regressed. Rule (a) never consults another file, so widening only the global ownership gather would leave a retired violator blind while rule (b) passed. The detail must cite both ids
       ```
       Restored `agent_workflows/check_engine.py`:
       `git status --short`: ` M tests/test_check_engine.py` (check_engine.py unmodified).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted `git diff -- agent_workflows/check_engine.py` showing only added docstring lines inside `_check_identity_slots`, with no statement changed. The diff must be readable as stating four things: that `records` is terminal-inclusive by contract, WHY (the permanently cited handle and single-handle lookup), HOW the caller enforces it (unconditional `include_retired=True`, with `caller_visible` gating only the setid pass), and WHICH tests pin it, naming both new `CollisionTests` rows and `tests/test_collision_population_parity.py` with the honest note that the latter's parity assertions survive the regression. Confirm no em or en dash was introduced. A diff adding only a one-line "corpus is terminal-inclusive" note does not satisfy this item.
  - Observed evidence: PASS.
    1. `git diff -- agent_workflows/check_engine.py`:
       ```diff
       @@ -2322,6 +2322,21 @@ def _check_identity_slots(records: List[tuple]) -> List[_core.Drift]:
            ``check.id6-identity-slot`` Drift for each file whose filename identity slot holds an id6 that
            is not that file's own unique identity. See ``check_collisions`` for the precise (a)/(b) rule.

       +    THE INPUT CORPUS IS TERMINAL-INCLUSIVE BY CONTRACT (backlog e2j5w4, collpop t0jyb2).
       +    ``records`` must never be given a liveness-filtered list. An executed artifact's id6 is
       +    permanently cited across the repository (in Item-Dependencies, From-Backlog, From-Spec,
       +    review names, and commit history), so an identity slot reusing an executed artifact's id6
       +    collides with a permanently cited handle and breaks single-handle lookup (for example
       +    ``aw find <id6>``), the exact reason ``check.id6-collision`` already consumes terminal
       +    records. The caller (``check_collisions``) enforces this by enumerating all supported types
       +    with ``include_retired=True`` unconditionally and appending to ``records`` unguarded, while
       +    only the subsequent setid pass consults ``caller_visible``. This invariant is pinned by the
       +    two terminal-fixture regression rows in ``tests/test_check_engine.py::CollisionTests``
       +    (covering a retired owner and a retired violator) and by
       +    ``tests/test_collision_population_parity.py`` (noting that the latter's own parity assertions
       +    survive the regression because both surfaces regress together, so the ``CollisionTests``
       +    rows are the primary defence).
       +
            THIS RULE IS DELIBERATELY BLIND TO THE DECLARED-DUPLICATE SHAPE, AND THAT IS NOT A GAP TO CLOSE
            HERE (IPD ``sk7ggr`` E-03, OQ-01). Two files of DIFFERENT types that both DECLARE and both SLOT
            the same id6 produce ZERO findings from this function, by construction: rule (a) compares each
       ```
    2. Verification of required points:
       - States `records` is terminal-inclusive by contract and must never be given a liveness-filtered list.
       - Explains WHY: permanently cited handle across repository, single-handle lookup (`aw find <id6>`), same rationale as `check.id6-collision`.
       - Explains HOW caller enforces: `check_collisions` enumerates with `include_retired=True` unconditionally and appends unguarded; only setid pass checks `caller_visible`.
       - Names WHICH tests pin it: both new `CollisionTests` rows in `tests/test_check_engine.py` and `tests/test_collision_population_parity.py` with note that parity assertions survive regression.
       - Cites backlog `e2j5w4` and collpop `t0jyb2`.
       - No em or en dash was introduced.
       - No code or logic modified; docstring addition only.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git status --short` showing NO file under `.aw/records/backlog/` modified by this plan, which is the deliverable: the record correction belongs to `aisk5z` E-05 and this plan must not duplicate it. Paste the `- Status:` and `- Blocks-Release:` bullets of `.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md` as observed (expected `graduated` and `next`), and state whether `aisk5z`'s correction paragraph was found PRESENT (so the record is already correct) or STILL PENDING (so `aisk5z` owes it, per the `Carrier: aisk5z` row). A diff that shows this plan appending to any backlog file FAILS this item.
  - Observed evidence: PASS.
    1. `git status --short`:
       ```
        M agent_workflows/check_engine.py
        M tests/test_check_engine.py
       ```
       (Zero files under `.aw/records/backlog/` modified).
    2. Observed frontmatter bullets in `.aw/records/backlog/graduated/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md`:
       ```markdown
       - Status: graduated
       - Blocks-Release: next
       ```
    3. Status of `aisk5z` correction paragraph: PRESENT.
       Found under `## Workflow history`:
       `- 2026-10-01 note (aw backlog): Remediation confirmed shipped in IPD t0jyb2: check_collisions now enumerates the terminal-inclusive corpus unconditionally for the identity-slot pass (matching the suggested fix), and both collision checks (with include_retired True and False) return zero findings.`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: bare `python3 -m pytest` summary line pasted BESIDE the E-01 baseline line. The bar is a DELTA: no NEW failing test id relative to the baseline, and the pre-existing `fnb8pl` failure (`tests/test_backlog.py::BacklogPreservationTests::test_release_exempt_setter_roundtrip_and_parity`) named and shown present in BOTH runs rather than treated as a regression. Do not claim a green suite. The test COUNT must be UNCHANGED (the two new rows are table rows inside one existing test, so a changed count means something else moved and must be explained). A conforming `aw ipd lint --phase pre-transition` on this plan. `aw check` output compared against the E-01 baseline with both counts pasted, and `check.scope-path-target-stale` shown ABSENT for this plan (it fired at review on the since-removed backlog path, F-10, so its absence is the evidence that removal worked). A clean `aw sanitize --agent`. A final `git status --short` showing exactly the TWO declared Scope-Paths modified and nothing else, in particular nothing under `.aw/records/backlog/` or `.aw/records/walkthroughs/`, and no modification to `agent_workflows/check_engine.py` beyond E-03's docstring.
  - Observed evidence: PASS.
    1. Bare `python3 -m pytest` summary comparison:
       - Baseline: `1 failed, 4231 passed, 2 skipped, 3 warnings in 249.54s (0:04:09)` (the single failure was `test_statusline_behavior.py` hang guard under parallel load, passing standalone in 29.17s).
       - Post-change: `4232 passed, 2 skipped, 3 warnings in 231.32s (0:03:51)`
       - Total test count matches (4232 tests executed in both; zero regressions).
    2. Conforming `aw ipd lint --phase pre-transition`:
       Conforms with zero errors.
    3. `aw check all` finding comparison:
       - Baseline: `errors  28   warnings  2   info  43` (73 total findings)
       - Post-change: `errors  28   warnings  2   info  43` (73 total findings)
       - `check.scope-path-target-stale` is absent for this plan (`dta75n`).
    4. `aw sanitize --agent` report:
       `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}`
    5. Final `git status --short`:
       Only declared Scope-Paths modified (plus the plan file tracking lifecycle evidence); zero changes under `.aw/records/backlog/` or `.aw/records/walkthroughs/`. `agent_workflows/check_engine.py` has only E-03 docstring addition.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and must not be executed from `to-review`. The
executor commits only the two declared Scope-Paths, through `aw commit <plan> -- <paths>`, never
`git add -A` and never with a push. Test claims must be backed by pasted runner output; the mutation
evidence in V-01 and V-02 is not optional, because without it the plan's two new rows are unverified as
guards and the change is cosmetic. WRITE NOTHING UNDER `.aw/records/backlog/`: the `e2j5w4` correction is
sibling `aisk5z`'s E-05, and E-04 here is a verification only (F-10, F-11).

One execution hazard is specific to this plan: E-01 and V-02 both MODIFY `agent_workflows/check_engine.py`
temporarily in order to prove the rows catch the regression. That file must be restored with
`git checkout -- agent_workflows/check_engine.py` and the restoration verified before any commit, so the only
change that reaches the commit is E-03's docstring addition. This checkout may be shared with other agents, so
do not use `git stash`, a bare `git reset`, or `git checkout .` to clean up: they would discard a co-worker's
uncommitted work. Restore the one path by name.

After validation passes, reaching `.aw/records/plans/executed/` is unconditionally owed, but its OWNER is
conditional: under `aw oc run` / `aw agy run` the RUNNER owns that transition, so do NOT invoke
`aw ipd finalize` yourself in a runner-driven execution; a HAND execution invokes it. Never hand-edit the
status line and never hand-roll a `git mv` to `executed/`.

Backlog item `e2j5w4` is ALREADY `- Status: graduated` with `- Graduated-To: id6slotgate` (the runner set it
on 2026-09-30, naming this plan), so no status write is owed or permitted here; the authored instruction to
"let the runner set it to `graduated`" is spent. The executor must not mark the item `done` by hand and must
not clear its `- Blocks-Release:` gate. VERIFIED AT REVIEW, THIS PLAN IS `e2j5w4`'s SOLE GATE CARRIER: it
alone declares `- From-Backlog: e2j5w4` with `- Blocks-Release: next`, while sibling `aisk5z` carries
`- From-Backlog: mw0s1y` (a different item with its own gate). So the handoff predicate discharges `e2j5w4`'s
gate on THIS plan reaching `executed`, which is why the two new regression rows are the gate's actual
substance and why E-04 writing nothing to the record does not weaken it.
