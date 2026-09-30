# IPD: Pin the identity-slot pass to the terminal-inclusive corpus with a direct regression row

- Date: 2026-09-30
- Kind: child
- Concern: Backlog `e2j5w4` reports that `check_engine.check_collisions` builds the record list feeding `_check_identity_slots` under the caller's liveness filter, so `aw check all` reported zero `check.id6-identity-slot` findings while three live D140 violations sat on disk. MEASURED IN THIS LANE AT HEAD `522598b6`, THE CODE HALF IS ALREADY FIXED and the item's predicted divergence no longer reproduces: the enumeration in `check_collisions` now passes `include_retired=True` unconditionally and `records.append` is unguarded, so only the setid pass consults `caller_visible`. `check_collisions(root)` and `check_collisions(root, include_retired=True)` both return `Counter()` on the live tree. That fix arrived through collpop `t0jyb2`, whose finding table names this very item ("Same defect as backlog `e2j5w4`"), and the three named walkthroughs were separately re-id'd by `nrqo90`. WHAT IS NOT FIXED IS THE DEFENCE. The fix is pinned by EXACTLY ONE assertion in the whole suite, and that assertion is a BY-PRODUCT of a test about something else. Re-introducing the exact regression the item describes (re-guarding `records.append` with `include_retired or not is_retired(p, record_type)`) reds `1 failed, 3245 passed` out of a 3246-test suite, and the single failure is `tests/test_collision_population_parity.py::test_collision_population_parity`, a test whose stated subject is check-versus-doctor PARITY. Worse, its three parity equality assertions ALL STILL PASS under the mutation, because the regression moves BOTH surfaces together; what fails is its incidental step-(3) `assertIn(slot_finding, check_default)`. So the guard is one line away from being silently retired by anyone legitimately editing a parity test, and `tests/test_check_engine.py::CollisionTests`, the table that owns this rule and holds eleven rows including two identity-slot rows, passes the mutation untouched because every fixture file it builds is LIVE.
- Scope: Close `e2j5w4` with the invariant defended where it belongs rather than by accident. IN: (a) add two rows to the `CollisionTests.COLLISIONS` table in `tests/test_check_engine.py` whose fixtures place the identity-slot violation's files under a TERMINAL directory, one per (a)/(b) rule half, so the table that owns this rule fails the regression directly; (b) record in `_check_identity_slots`'s docstring that its corpus is terminal-inclusive BY CONTRACT and name the rows that pin it, because that function is where a future reader looks and it currently says nothing about the corpus it is handed; (c) append a dated measurement correction to backlog item `e2j5w4` recording that `t0jyb2` shipped its suggested fix, without touching its requirements, `- Status:` or `- Blocks-Release:`. OUT: any change to `check_engine.check_collisions`' or `_check_identity_slots`' BEHAVIOR, which measures correct on all four axes probed at authoring; widening the setid pass, whose narrow corpus is deliberate and documented; renaming any walkthrough (`nrqo90` already did, and re-renaming would rewrite cited history); the `CollisionTests` census/anti-vacuity concerns and the DECISIONS D140 parenthetical correction, both owned by sibling plan `aisk5z` at Order 01 in this same Set.
- Scope-Paths: tests/test_check_engine.py, agent_workflows/check_engine.py, .aw/records/backlog/open/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: e2j5w4
- Blocks-Release: next
- Set: id6slotgate
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: dta75n

## Workflow history

- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `e2j5w4`, graduating it. Every claim below was measured in this lane at HEAD `522598b6` by mutation probe, not read off prose. THE ITEM'S CODE DEFECT IS ALREADY FIXED, which inverts the deliverable from a behavior change into a defence: `t0jyb2` gave the slot pass the terminal-inclusive corpus the item's SUGGESTED FIX asked for, so the plan must NOT re-perform it. What the mutation probe surfaced instead is that the shipped fix is pinned by one incidental assertion inside a parity test whose own equality assertions survive the regression, while the eleven-row table that owns this rule passes it untouched because all its fixtures are live. The deliverable is therefore two terminal-fixture regression rows in that table, a corpus contract in the docstring, and a record correction. The item's release gate is inherited unchanged because the invariant is one edit away from undefended until those rows exist.

## Goal

Leave the D140 identity-slot rule's TERMINAL-INCLUSIVE CORPUS defended by the test that owns the rule, so the
fix `t0jyb2` shipped cannot be silently undone, and leave `e2j5w4`'s record saying what is actually true.

This plan deliberately changes NO production behavior. Five facts were established at authoring by running
code, so the executor inherits measurement rather than this plan's description of it.

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

   One failure out of 3246 tests. Run per-file under the same mutation, the four other files that name this
   rule are all GREEN: `tests/test_check_engine.py` 49 passed, `tests/test_doctor.py` 35 passed,
   `tests/test_walkthrough_id6.py` 4 passed, `tests/test_artifact_adopt.py` 40 passed. The three that call
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

- [ ] E-01 RE-VERIFY THE FIVE AUTHORING FACTS AT THE EXECUTION HEAD AND CAPTURE THE BASELINE, because this plan's entire shape rests on the claim that the behavior fix already shipped, and executing it against a tree where that is false would leave a real defect live behind two new green tests. Record, with output: `check_engine.check_collisions(root)` and `check_collisions(root, include_retired=True)` as rule counters on the live tree; the four-axis synthetic probe from Goal fact 3 (owner retired, offender retired, both retired, and a rule-(a) violator that is itself retired), each at both `include_retired` values; a bare `python3 -m pytest` summary line; and `aw check all` output. THEN RE-RUN THE MUTATION PROBE that establishes facts 4 and 5, because it is the measurement this plan's value depends on: guard the `records.append` call in `check_collisions` with `include_retired or not is_retired(p, record_type)`, run the bare suite, record which tests fail, evaluate the parity test's three equality assertions directly, and RESTORE the file with `git checkout --` verifying `git status --short` shows no modification to `agent_workflows/check_engine.py`. IF the collision calls return any `check.id6-identity-slot` finding on the live tree, or the mutation reds more than the single parity test, STOP and report: the tree is not the one this plan was authored against and the correct response is a fresh plan.
  - Depends on: none
  - Expected outcome: both collision calls return zero findings of every rule; all four probe axes report 1 finding at BOTH `include_retired` values; the bare suite is green with its summary line on record; the mutation reds exactly `tests/test_collision_population_parity.py::CollisionPopulationParityTests::test_collision_population_parity` and nothing else; the parity test's two equality assertions both evaluate True under that mutation while the slot-presence check evaluates False; and `agent_workflows/check_engine.py` is unmodified afterwards.
  - Execution state: pending

### Task group 2: defend the corpus in the table that owns the rule

- [ ] E-02 ADD TWO TERMINAL-FIXTURE ROWS TO `CollisionTests.COLLISIONS` IN `tests/test_check_engine.py`, one per half of the identity-slot rule, so the table that owns this rule fails the regression directly instead of delegating its only defence to a parity test. ROW ONE covers rule (b) with a RETIRED OWNER: an executed plan declaring `- Id: aaa111` at `.aw/records/plans/executed/20260101-demo-01-aaa111-a.ipd.md` (built with `_plan_text("aaa111", status="executed")`) beside a live walkthrough at `.aw/records/walkthroughs/20260101-demo-01-aaa111-w.walkthrough.md` (built with `_walk_text()`, declaring no `- Id:`), which is the `p7dqwz` shape with the owner in terminal history and is the shape the item's three real violations had. ROW TWO covers rule (a) with a RETIRED VIOLATOR: a single executed plan at `.aw/records/plans/executed/20260101-demo-01-slotaa-a.ipd.md` built with `_plan_text("fmbbb1", status="executed")`, whose slot `slotaa` disagrees with its own declared `fmbbb1`; this half is independent because rule (a) never consults another file, so a fix that widened only the ownership gather would still leave it blind. MEASURED AT AUTHORING, both rows expect EXACTLY `(IDENTITY_SLOT,)` from `check_collisions` AND from the full sweep (the executed-directory fixtures trip no incidental content rule, unlike the live-fixture rows that carry `DRAFT_READY`); re-measure rather than trusting that. Give each row needles naming BOTH sides where two files are involved, per the table's stated convention that the detail is asserted and not only the rule id, and write the "why this row exists" column to say the fixture is TERMINAL ON PURPOSE and that the row exists because the corpus, not the rule logic, is what regressed. Note the paths must be written as literals rather than through the `PLANS`/`WALK` constants, which point at `pending/` and the live walkthroughs directory; add a brief comment saying so, since a later reader "tidying" them onto the constants would silently retire both rows.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_check_engine.py -o addopts="" -q` passes with 49 tests, `CollisionTests.COLLISIONS` holds 13 rows, and re-applying the E-01 mutation reds `tests/test_check_engine.py` where fact 4 measured it green.
  - Execution state: pending

- [ ] E-03 RECORD THE CORPUS CONTRACT IN `_check_identity_slots`' DOCSTRING, because that function is where the next reader of this rule looks and it currently says nothing at all about the corpus it is handed, while the contract lives only in its CALLER's docstring. The function already carries three shouted paragraphs about what it deliberately does NOT detect and where that is detected instead, so a paragraph about its input is in keeping. State: that `records` is TERMINAL-INCLUSIVE BY CONTRACT and the function must never be given a liveness-filtered list; WHY, namely that an identity slot reusing an executed artifact's id6 collides with a permanently cited handle and breaks single-handle lookup, which is the same reasoning its `check.id6-collision` sibling already carries; that the caller enforces this by enumerating with `include_retired=True` unconditionally while only the setid pass consults `caller_visible`; and WHICH TESTS pin it, naming the two `CollisionTests` rows E-02 adds and `tests/test_collision_population_parity.py`, with the honest note that the latter's own parity assertions survive the regression so it is not the guard to rely on. Cite backlog `e2j5w4` and collpop `t0jyb2` as the history. Write no em or en dashes. Change no code in this item.
  - Depends on: E-02
  - Expected outcome: `git diff -- agent_workflows/check_engine.py` shows only added docstring lines inside `_check_identity_slots`, with no change to any statement, and the bare suite stays green.
  - Execution state: pending

### Task group 3: correct the record and gate

- [ ] E-04 APPEND A DATED MEASUREMENT CORRECTION TO BACKLOG ITEM `e2j5w4` WITHOUT TOUCHING ITS REQUIREMENTS, since it is `Blocks-Release: next` and presents a remediated defect as live, so a release reviewer reading it would believe a blocker is outstanding. The paragraph states that `t0jyb2` gave the identity-slot pass the terminal-inclusive corpus the item's SUGGESTED FIX asked for, that both collision calls now return zero findings of every rule, that the three named walkthroughs were separately re-id'd by `nrqo90` so the paths in the item's measured effect no longer exist, and that the residual work this plan performs is the regression coverage rather than a behavior change. DO NOT edit the item's existing measurement text: its whole value is as the record of what was true on 2026-09-21, and `nrqo90`'s E-07 deliberately preserved this item byte-identical for that reason. DO NOT change `- Status:`, which this plan's authoring contract reserves to the runner, and DO NOT change `- Blocks-Release:`. Prefer `aw backlog note` if that verb exists for appending history; otherwise append directly and say which you did and why. NOTE the sibling plan `aisk5z` at Order 01 in this Set also declares this file in its Scope-Paths and also appends to it: if `aisk5z` has already landed its paragraph, ADD YOURS BENEATH IT rather than replacing it, and say so in the evidence.
  - Depends on: E-01
  - Expected outcome: `git diff` of the backlog item shows only appended text, every pre-existing line including the three old walkthrough paths unchanged, and `- Status:` and `- Blocks-Release:` untouched.
  - Execution state: pending

### Task group 4: regression gate

- [ ] E-05 RUN THE FULL REGRESSION GATE AND COMPARE IT AGAINST THE E-01 BASELINE, so any failure is shown pre-existing rather than argued harmless. Run bare `python3 -m pytest` (no added flags: the configured `addopts` already supplies quiet, parallel and the fast subset, and a second `-q` would suppress the `N passed` line this plan requires). Then `aw ipd lint --phase pre-transition` on this plan, `aw check` compared against its E-01 baseline count, and `aw sanitize --agent`, which is not a formality here because the probe output this plan pastes contains temp-directory paths. FINALLY VERIFY THE WORKING TREE IS EXACTLY THE DECLARED SCOPE: E-01 and V-02 both temporarily modified `agent_workflows/check_engine.py`, so confirm with `git status --short` and with `git diff -- agent_workflows/check_engine.py` that the only surviving change to that file is E-03's docstring addition. Restore any residue by path name, never with `git stash`, a bare `git reset`, or `git checkout .`, since this checkout may be shared.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: the suite summary line matches the E-01 baseline with no new failure and an UNCHANGED test count (the two new rows are table rows inside one existing test); a conforming pre-transition lint; `aw check` no worse than baseline; a clean sanitizer report; and a working tree holding exactly the three declared Scope-Paths.
  - Execution state: pending

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
| F-7 | Rule (a) needs its own row rather than riding on rule (b). Rule (a) compares a file's slot against its OWN declared `- Id:` and consults no other file, so a partial fix that restored only the global ownership gather would leave it blind while the rule-(b) row passed. | `_check_identity_slots` rule (a) branch, which reads only `declared_id` and `slot_id6` of the file in hand; probe axis (iv) exercising it with the violator itself retired. |

## Proposed changes (ordered, validatable)

1. Re-verify the five facts at the execution HEAD, capture the suite and `aw check` baselines, and re-run the
   mutation probe that establishes the pin's thinness, refusing to proceed if the tree differs (E-01 / V-01).
2. Add two `CollisionTests.COLLISIONS` rows whose identity-slot fixtures live under a terminal directory, one
   per rule half, so the owning table fails the regression directly (E-02 / V-02).
3. Record the terminal-inclusive corpus contract, its reason, and the tests that pin it in
   `_check_identity_slots`' docstring, changing no code (E-03 / V-03).
4. Append a dated measurement correction to backlog `e2j5w4`, leaving its requirements, status, gate and
   original measurement text untouched (E-04 / V-04).

## Deferred / out of scope (with reason)

- ANY BEHAVIOR CHANGE TO `check_collisions` OR `_check_identity_slots`. Measured correct on four axes (F-3).
  Re-performing the item's SUGGESTED FIX would be a no-op at best and a regression at worst.
  - Carrier-Declined: there is no outstanding work here to carry. The four-axis probe in Goal fact 3 measures the behavior as already correct at both `include_retired` values, so this row records a NON-task rather than a deferral, and naming a carrier for it would assert that someone still owes a behavior fix that nobody owes.
- WIDENING THE SETID PASS. Deliberate and documented; the item's own suggested fix says to keep it as is.
  - Carrier-Declined: not a deferral but a settled decision recorded twice already. `check_collisions`' docstring states the setid pass keeps the caller's corpus to avoid surfacing within-type descriptive drift on retired records, and backlog `e2j5w4`'s own SUGGESTED FIX asks for exactly this. Nothing is outstanding, so there is nothing for a carrier to own.
- RENAMING ANY WALKTHROUGH. `nrqo90` already did it; re-renaming would rewrite history other records cite.
  - Carrier-Evidence: .aw/records/plans/executed/20260926-wkthid6-01-nrqo90-mint-a-walkthrough-s-own-id6-in-write-walkthrough-add-the-wa.ipd.md
- THE `tests/test_walkthrough_id6.py` CENSUS GUARD, DECISIONS D140's stale parenthetical, and backlog
  `mw0s1y`. All owned by sibling plan `aisk5z` (Order 01, this Set). This plan's only overlap with it is the
  `e2j5w4` backlog file, which both append to; E-04 names the ordering hazard and handles either order.
  - Carrier: aisk5z
- NARROWING OR REWRITING `tests/test_collision_population_parity.py`. Its parity subject is legitimate and its
  incidental slot assertion is currently load-bearing. Once E-02 lands, the guard no longer depends on it, but
  removing the assertion is not this plan's business and would reduce coverage before a reviewer asked for it.
  - Carrier-Declined: deliberately nobody's task, and that is the point of the row. OQ-01 resolves from the repository that the assertion should be KEPT permanently, not merely deferred: it covers the `check_types` full-sweep seam the E-02 rows do not, and it is what stops the parity assertions being vacuously satisfiable by two surfaces that both report nothing. A carrier here would schedule a removal this plan argues against.
- A TEST THAT GREPS `check_engine.py` FOR THE UNGUARDED APPEND. Forbidden as a code-pinning test (P16).
  - Carrier-Declined: prohibited by contract rather than postponed. AGENTS.md forbids tests that read production source with `inspect`, `ast`, regex or substring search, and GUIDING_PRINCIPLES P16 says the same, so this must never be carried by anyone. The behavioral equivalent is E-02, which is in scope.

## Scope check

- Over-scope: none. The plan adds two test rows, a docstring paragraph, and an appended record paragraph.
  Every declared Scope-Path is touched; no production statement changes.
- Under-scope: the plan does NOT make `aw check`'s CLI surface assert this rule end-to-end (no CLI-level test
  names `check.id6-identity-slot` today). Measured at authoring, the end-to-end path does work: on a synthetic
  repo holding an executed plan owning `aaa111` and a live walkthrough squatting it, `aw check all --agent`
  reports the finding with its D140 remediation in `next` and exits nonzero. A CLI-level regression row is a
  legitimate follow-up but the engine-level rows in E-02 are where the corpus regression is visible, and
  duplicating them at the CLI would pin the same fact twice.

## Required tests / validation

- `python3 -m pytest tests/test_check_engine.py -o addopts=""` green with the two new rows, and the 13-row
  table verified by count rather than by eye.
- THE MUTATION PROBE IS THE VALIDATION THAT MATTERS, because "the rows pass" and "the rows would have caught
  the regression" are independent claims and only the second is this plan's deliverable. With the item's exact
  regression re-applied, `tests/test_check_engine.py` MUST fail where fact 4 measured it green, and the
  failure message must name the terminal rows. The mutation must then be reverted with `git checkout --` and
  the revert verified with `git status --short`.
- Bare `python3 -m pytest` (no added flags; the configured `addopts` already supplies quiet, parallel and the
  fast subset, and a second `-q` would suppress the `N passed` line this plan must paste), compared against
  the E-01 baseline.
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
- Resolution or deferral rationale: RESOLVED AT AUTHORING FROM THE REPOSITORY, keep it, and the reasoning is measurement rather than preference. The assertion is currently the repository's ONLY guard against this regression (F-4), so removing it in the same change that adds a replacement would leave the invariant momentarily defended by untested new rows; and it is not redundant even afterwards, because it asserts the finding is present in `check_types(root, ["all"])` (the full-sweep seam a user reaches through `aw check all`) while the E-02 rows assert `check_collisions` and the sweep over a DIFFERENT fixture population. Its own test docstring gives the second reason to leave it: the parity claim needs a finding that EXISTS in order to compare two surfaces, so deleting the presence check would make the parity assertions satisfiable by two surfaces that both report nothing, which is exactly the vacuity the mutation probe exposed. What this plan does about it is in E-03: name the parity test as a pin while recording honestly that its parity assertions survive the regression, so a future author narrowing it knows what they would be removing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted rule counters for `check_collisions(root)` and `check_collisions(root, include_retired=True)` on the live tree, both empty of every rule. Pasted four-axis probe output showing `default=1 widened=1` on every axis, including the rule-(a) axis. The baseline bare `python3 -m pytest` summary line and the baseline `aw check` finding count, both recorded for E-05 comparison. Then the MUTATION evidence: the pasted bare-suite summary under mutation naming which tests failed, the four per-file summaries for `tests/test_check_engine.py`, `tests/test_doctor.py`, `tests/test_walkthrough_id6.py` and `tests/test_artifact_adopt.py`, the three-line parity-assertion evaluation showing both equality assertions True and the slot-presence check False, and a `git status --short` proving `agent_workflows/check_engine.py` was restored. State explicitly that the refusal condition (any live identity-slot finding, or more than the one parity test reddening) did NOT trigger. A run that pastes the baseline but not the mutation evidence does not satisfy this item, because the mutation is what establishes the plan's premise.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `git diff -- tests/test_check_engine.py` showing the two added rows with their terminal fixture paths, their measured expected rule sets, their needles, and their why-columns. Pasted `python3 -m pytest tests/test_check_engine.py -o addopts="" -q` summary. A pasted count proving `CollisionTests.COLLISIONS` holds 13 rows. THEN THE DECISIVE EVIDENCE: re-apply the E-01 mutation, run `python3 -m pytest tests/test_check_engine.py -o addopts="" -q`, and paste the FAILURE together with enough of the assertion message to show it names the two terminal rows by their case strings; then restore and paste a `git status --short` showing `agent_workflows/check_engine.py` unmodified. A passing row set without this mutation failure does NOT satisfy this item: it would show the rows run, not that they guard anything.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff -- agent_workflows/check_engine.py` showing only added docstring lines inside `_check_identity_slots`, with no statement changed. The diff must be readable as stating four things: that `records` is terminal-inclusive by contract, WHY (the permanently cited handle and single-handle lookup), HOW the caller enforces it (unconditional `include_retired=True`, with `caller_visible` gating only the setid pass), and WHICH tests pin it, naming both new `CollisionTests` rows and `tests/test_collision_population_parity.py` with the honest note that the latter's parity assertions survive the regression. Confirm no em or en dash was introduced. A diff adding only a one-line "corpus is terminal-inclusive" note does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `git diff` of `.aw/records/backlog/open/20260921-id6slotgate-01-e2j5w4-check-identity-slot-liveness-filter.backlog.md` showing ONLY added lines, with the `- Status:`, `- Blocks-Release:`, `- Work-Kind:` and `- Summary:` bullets and the three old walkthrough paths all unchanged. State which mechanism was used (`aw backlog note` or a direct append) and why. If sibling plan `aisk5z` has already appended its own paragraph, show that it is still present and that the new paragraph was added beneath it.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: bare `python3 -m pytest` summary line pasted BESIDE the E-01 baseline line, with no new failure and a test count higher by zero (the two new rows are table rows inside one existing test, so the count must be UNCHANGED; a changed count means something else moved and must be explained). A conforming `aw ipd lint --phase pre-transition` on this plan. `aw check` output compared against the E-01 baseline with both counts pasted. A clean `aw sanitize --agent`. A final `git status --short` showing exactly the three declared Scope-Paths modified and nothing else, in particular no residue under `.aw/records/walkthroughs/` and no modification to `agent_workflows/check_engine.py` beyond E-03's docstring.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution and must not be executed from `to-review`. The
executor commits only the three declared Scope-Paths, through `aw commit <plan> -- <paths>`, never
`git add -A` and never with a push. Test claims must be backed by pasted runner output; the mutation
evidence in V-01 and V-02 is not optional, because without it the plan's two new rows are unverified as
guards and the change is cosmetic.

One execution hazard is specific to this plan: E-01 and V-02 both MODIFY `agent_workflows/check_engine.py`
temporarily in order to prove the rows catch the regression. That file must be restored with
`git checkout -- agent_workflows/check_engine.py` and the restoration verified before any commit, so the only
change that reaches the commit is E-03's docstring addition. This checkout may be shared with other agents, so
do not use `git stash`, a bare `git reset`, or `git checkout .` to clean up: they would discard a co-worker's
uncommitted work. Restore the one path by name.

After validation passes, move this plan to `.aw/records/plans/executed/` through the tooled lifecycle
transition and let the runner set backlog item `e2j5w4` to `graduated`; the executor must not mark the item
`done` by hand, and must not clear its `- Blocks-Release:` gate, which is discharged by this plan's own
inherited gate once the plan is executed.
