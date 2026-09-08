# IPD: Pin the approval-gate corpus test to named id6s so a legitimate plan-review REJECT cannot red the suite

- Date: 2026-09-08
- Kind: child
- Concern: A TEST ASSERTS SOMETHING THAT IS FALSE BY CONSTRUCTION WHENEVER THE GATE WORKS. `tests/test_plan_readiness.py:789-798`, `ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, globs the LIVE pending tree (`PENDING_DIR`, `:30`) and asserts no plan there carries a negative review verdict: `refused = [p.name for p in pending if PR.newest_verdict(...)[0] == PR.NEGATIVE]` then `self.assertEqual(refused, [], "pending plans falsely refused on their verdict")`. A pending plan that was legitimately REJECTed by `/plan-review` and is awaiting a replan is exactly what the pending tree SHOULD contain, so the suite reds on correct behavior.
  THE TEST'S INTENT IS SOUND, WHICH IS WHY THIS IS A REPAIR AND NOT A DELETE. Its docstring says "A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard" and its class docstring (`:770`) says "a fixture-only suite can pass while the gate misjudges reality". Both are right. The defect is the PROXY: "any pending plan is refused" cannot distinguish a FALSE refusal from a TRUE one.
  THE CORRECT PATTERN ALREADY EXISTS TWICE IN THE SAME CLASS, so the fix needs no design. `test_the_three_item_13_successors_are_not_refused` (`:781-787`) pins THREE named id6s that must NOT be refused and resolves each by id6 across five dispositions via the `_find` helper (`:772-779`), which calls `skipTest` when a plan is absent. `test_the_incident_plans_are_refused` (`:800-818`) pins FIVE named id6s that MUST be refused, COUNTS how many it actually checked, and calls `skipTest` when none remain "so it says so rather than lying". Both encode one insight: assert on NAMED artifacts whose verdict polarity is known, never on a whole mutable tree.
  THE FAILURE IS CURRENTLY LATENT, NOT ACTIVE, AND THAT IS THE ONE THING THIS PLAN MUST NOT HIDE. Measured in this lane at HEAD `fac69fbd`: `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` reports `67 passed`, and the bare suite reports `5859 passed, 3 skipped, 2 xfailed`. The reason is that `32ij2j`, the plan whose legitimate REJECT reddened the suite when the item was filed, has MOVED from `pending/` to `superseded/` (commit `32e4b74f`), and the test globs `pending/` only. So the bug did not get fixed; the corpus drifted out from under it, which is the same accidental self-healing the item warns about for its sibling instance.
- Scope: Replace the whole-tree assertion with the named-id6 pattern its two siblings already use, using the existing `_find` helper and an honest `skipTest`, and add a corpus-property assertion that survives a legitimate REJECT if one is genuinely wanted. EXCLUDES editing `32ij2j` or any plan's review record; EXCLUDES a general guard against the whole "test asserts on live repo corpus" class (recorded as a decision with evidence, and a follow-up filed if wanted); EXCLUDES `tests/test_run_viewer.py`'s live-tree coupling, which `utwr6y` owns.
- Scope-Paths: tests/test_plan_readiness.py
- Item-Dependencies: none
- Status: to-review
- Set: gatepin
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h3bjue
- From-Backlog: yw6759
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `yw6759`. NOTHING IS OBSOLETE: the false-by-construction assertion is byte-for-byte intact at `tests/test_plan_readiness.py:789-798`, still globbing the live `PENDING_DIR` (`:30`), and NO plan in any disposition fixes it (searched all five for `test_plan_readiness`, `ApprovalGateRealCorpusTests`, `newest_verdict`, `corpuspin`, `yw6759`; `corpuspin` and `yw6759` have ZERO hits anywhere, and every `ApprovalGateRealCorpusTests` hit is a BASELINE NOTE recording it as a known failure to ignore, in at least `9xycbh:111`, `6eq3oq:169`, `5f2h8i:152`, `lhccjf:158`, `m7gvuz:114`, `:138`). TWO plans explicitly DISCLAIM fixing it: `daexj1:127` ("AUTO-FIXING THE CURRENT RED TEST ... belongs to whoever owns plan `32ij2j`'s REPLAN verdict") and superseded `xtklpd:254` ("Do not fix either here"). THREE OF THE ITEM'S CLAIMS ARE NOW WRONG AND ALL THREE ARE RECORDED HERE RATHER THAN CARRIED FORWARD. FIRST, the stated repro does NOT reproduce: `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` reports `67 passed` and the bare suite `5859 passed, 3 skipped, 2 xfailed`, because `32ij2j` moved from `pending/` to `superseded/` in commit `32e4b74f` (its REJECT record survives one entry deeper, so the verdict is still negative; the tree it sits in changed). The bug is LATENT, and E-01 must therefore MANUFACTURE the condition on a fixture instead of quoting the item's repro. SECOND, the item says its sibling instance in `test_orchestrator_retirement.py` "self-healed by corpus drift rather than being fixed"; that is FALSE. The test was DELIBERATELY renamed and rewritten to `test_runprofile_is_not_refused_for_unauthored_rows` (`tests/test_orchestrator_retirement.py:890`) in commit `31169afd`, whose new docstring (`:891-901`) reasons that asserting the refusal "pinned a transient repository state rather than the behavior this test is named for". That is the SAME insight this plan applies, already applied once in-repo, so it is a second local PRECEDENT that strengthens the item rather than obsoleting it; the old node id no longer exists (`pytest` on it collects 0 items). THIRD, the graduation briefing's baseline of `1 failed, 5648 passed` naming `test_orchestrator_retirement` does not hold here: that module reports `112 passed` and the bare suite is green. ONE PLAN SHARES THE FILE: `8v5pwa` (`rdattest-02`) declares `tests/test_plan_readiness.py` in `Scope-Paths` and its E-04 adds a forged-`Readiness`-field test to the auto-approve predicate; it does not touch `ApprovalGateRealCorpusTests`, so this is merge ordering, not a dependency. `utwr6y` (`testiso-01`) is NOT a dependency: it builds a synthetic RUN tree fixture for `tests/test_run_viewer.py`, a different tree on a different axis, and this fix needs no fixture beyond the `_find` helper that already exists. Noted for the maintainer, outside my items: `utwr6y`'s E-01/E-02 appear largely satisfied already by commit `e167c9b3`, while its E-03 file `tests/test_run_viewer_isolation.py` does not exist, and it carries `Blocks-Release: next`.

## Goal

Make the approval gate's real-corpus test assert a property that stays true while the gate works, so a legitimate `/plan-review` REJECT stops reddening the suite and stops teaching every agent and human that a red suite is normal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: manufacture the latent failure before fixing it

- [ ] E-01 REPRODUCE THE DEFECT DELIBERATELY, since it no longer reproduces on its own, and this is the step a careless executor will skip. The item's stated repro is stale: `32ij2j` left `pending/` in commit `32e4b74f`, so the test now passes (`67 passed`) while the defect is untouched. Demonstrate the assertion is false-by-construction rather than asserting that it is.
  DO IT ON A FIXTURE, NEVER ON THE LIVE TREE. Two ways are acceptable and both must avoid mutating the repository: point the assertion's logic at a temporary directory containing one synthetic plan whose newest review record is a REJECT, or parameterize the predicate and feed it a synthetic file list. Do NOT create, move, or edit any real plan to trigger it: 92 plans are pending, 18 approved plans are executing in live runs, and three agents are graduating concurrently.
  PASTE THE FAILURE. The evidence required is the assertion failing with the synthetic REJECT present, naming it, exactly as it would have named `32ij2j`. A fix demonstrated only against the fixed code proves nothing about the defect.
  ALSO PASTE THE CURRENT GREEN, so the record is honest about the failure being LATENT. `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` at HEAD, with its summary line. Do not let a later reader believe this plan was written against a red suite.
  - Depends on: none
  - Expected outcome: the false-by-construction assertion shown FAILING against a synthetic REJECTed plan with output pasted, the current live-tree GREEN also pasted, and no real plan created, moved or edited.
  - Execution state: pending

### Task group 2: apply the pattern the siblings already use

- [ ] E-02 REPLACE THE WHOLE-TREE ASSERTION WITH THE NAMED-ID6 PATTERN, and copy the siblings rather than inventing a shape. `test_the_three_item_13_successors_are_not_refused` (`:781-787`) is the exact model: iterate a tuple of named id6s, resolve each with the existing `_find` helper (`:772-779`), and assert the polarity. `_find` already walks `pending`, `executed`, `superseded`, `not-executed`, `reusable` and already calls `skipTest` when a plan is absent, so no new helper is needed.
  CHOOSE THE PINNED IDS FOR A STATED REASON, not by convenience. The property the test exists to catch is a FALSE refusal: a plan whose newest review record is APPROVING that the parser nonetheless reads as negative. So pin plans whose verdict polarity is KNOWN and POSITIVE, and record for each id6 why its polarity is known. Do not pin a plan merely because it is currently pending; pending is the mutable fact that caused the bug.
  KEEP THE HONEST-SKIP BEHAVIOR AND THE CHECKED COUNT. `test_the_incident_plans_are_refused` (`:800-818`) counts what it checked and skips with a reason when nothing remains, explicitly "so it says so rather than lying". A test that silently passes because its subjects vanished is the same class of defect in a new dress; carry the counter over.
  PRESERVE THE DOCSTRING'S INTENT, REWORDED. "A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard" is still the point; it must now say that the check is against NAMED plans whose polarity is known, and say WHY the whole-tree version was wrong, so nobody restores it.
  - Depends on: E-01
  - Expected outcome: the whole-tree glob replaced by named id6s resolved through the existing `_find`, each pinned id6's known polarity recorded, the checked-count and honest-skip carried over, and the docstring stating why the tree-wide form was wrong.
  - Execution state: pending

- [ ] E-03 DECIDE WHETHER A WHOLE-CORPUS PROPERTY IS WANTED AT ALL, AND IF SO USE ONE THAT SURVIVES A LEGITIMATE REJECT. This is the item's suggestion 2 and it is a real design choice, not a formality.
  "NO PLAN IS REFUSED" IS NOT SUCH A PROPERTY, which is the whole defect. The item's defensible alternative is: no plan whose newest review record contains an APPROVING verdict token is refused. That catches the parser bug the test was written to catch without forbidding rejection, and it is stable under any legitimate corpus state.
  RECORDING "NO" IS AN ACCEPTABLE OUTCOME. E-02's named-id6 test may be sufficient, and a corpus-wide property that reads 92 files on every suite run has a cost. If you decide against it, write the reason down; if you decide for it, it must be phrased over the verdict TOKEN and not over the tree's membership.
  IF YOU BUILD IT, PROVE IT IS STABLE by running it against a corpus that CONTAINS a legitimately REJECTed pending plan (the E-01 fixture supplies exactly that) and showing it passes.
  - Depends on: E-02
  - Expected outcome: a recorded decision on the corpus-wide property with reasoning; if built, phrased over the approving-verdict token and shown passing against a corpus containing a legitimate REJECT.
  - Execution state: pending

### Task group 3: the class, and the proof

- [ ] E-04 RECORD A DECISION ON GUARDING THE WHOLE DEFECT CLASS, and check the two neighbours before designing anything, because the item explicitly warns they may collide.
  THE CLASS HAS NOW PRODUCED THREE KNOWN INSTANCES, which is the argument for a guard: this test; `test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` in `tests/test_orchestrator_retirement.py`, which asserted `{"kgpptv": "reviewed"}` against the live corpus, was red for days, and was DELIBERATELY rewritten to `test_runprofile_is_not_refused_for_unauthored_rows` (`:890`) with a docstring (`:891-901`) reasoning that it "pinned a transient repository state rather than the behavior this test is named for"; and `tests/test_run_viewer.py`'s dependence on the gitignored runs tree.
  CHECK `utwr6y` FIRST, AS THE ITEM INSTRUCTS. Its E-03 adds a regression guard in a new `tests/test_run_viewer_isolation.py` and explicitly forbids implementing it as a grep over test source, because that "would pass while an implicit `dir='.'` still reached the live tree". Its E-04 SWEEPS for the same class in other tests reading gitignored box-local state and is scoped to REPORT, NOT FIX (its own words, "REPORT, DO NOT SILENTLY WIDEN"). So `utwr6y` contributes an INVENTORY, not a guard, and a guard built here must not duplicate its file or its sweep.
  THE HONEST DEFAULT IS TO RECORD AND FILE, NOT TO BUILD. A general "this test reads live repo state" detector is a new cross-cutting mechanism with its own false-positive risk, and some live-corpus tests are DELIBERATE and valuable (this very class exists because "a fixture-only suite can pass while the gate misjudges reality"). A blunt guard would forbid the good case along with the bad. So the deliverable is a written decision plus, if a guard is wanted, a follow-up backlog item or plan; not an in-scope build.
  - Depends on: E-03
  - Expected outcome: a recorded decision on a class-wide guard citing all three instances and `utwr6y`'s inventory scope, with a follow-up filed if wanted, and no duplication of `utwr6y`'s file or sweep.
  - Execution state: pending

- [ ] E-05 PROVE THE GATE'S REAL BEHAVIOR IS UNCHANGED IN BOTH DIRECTIONS, because the two sibling tests pin exactly that and are the reason this fix is safe.
  BOTH SIBLINGS MUST STAY GREEN AND NON-VACUOUS. `test_the_three_item_13_successors_are_not_refused` resolves `6lu3rq`, `m73aet`, `wlxkoz`, all currently in `executed/`; `test_the_incident_plans_are_refused` resolves `bmh754`, `a54m79`, `kaygwo`, `k7o7el`, `7f7782`, all currently in `superseded/`, and counts what it checked. Show they PASS and show the counter is nonzero, so neither passed vacuously.
  DO NOT EDIT `32ij2j` OR ANY REVIEW RECORD. Its REJECT verdict is correct and its status is correct. Changing a plan's review record to make a test pass would forge review evidence, which is the one thing the approval-gate machinery exists to prevent. Paste negative proof: `git status --porcelain .aw/records/plans/` clean.
  RUN THE SUITE BARE and judge on the DELTA. Measured in this lane at HEAD `fac69fbd`: `5859 passed, 3 skipped, 2 xfailed`. The graduation briefing quotes a different baseline (`1 failed, 5648 passed`, naming `test_orchestrator_retirement`), and that failure does NOT reproduce here (`112 passed` in that module). State what YOU observe rather than quoting either figure, and report AFTER minus BEFORE as a set.
  - Depends on: E-04
  - Expected outcome: both sibling tests green with a nonzero checked-count, negative proof that no plan or review record was edited, and a bare-suite delta that is empty with the observed counts stated.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FIX PATTERN ALREADY EXISTS TWICE IN THE SAME CLASS. `_find` (`tests/test_plan_readiness.py:772-779`) resolves an id6 across five dispositions and skips honestly; `test_the_three_item_13_successors_are_not_refused` (`:781`) and `test_the_incident_plans_are_refused` (`:800`) both pin named id6s. Copy them; design nothing.
- AN HONEST SKIP AND A CHECKED COUNTER ARE THE LOCAL HABIT. `test_the_incident_plans_are_refused` counts and skips "so it says so rather than lying". A vacuous pass is treated as a defect here.
- THE SAME INSIGHT WAS ALREADY APPLIED ONCE, IN ANOTHER MODULE. `tests/test_orchestrator_retirement.py:890`'s docstring (`:891-901`) records that asserting a refusal "pinned a transient repository state rather than the behavior this test is named for". That is a precedent for the reasoning, not just for the mechanics.
- THE LIVE-CORPUS COUPLING IS DELIBERATE IN THIS CLASS. The class docstring (`:770`) says "a fixture-only suite can pass while the gate misjudges reality". So the answer is not "never read the corpus", it is "assert a property the corpus cannot legitimately violate".
- `PENDING_DIR` IS THE MUTABLE FACT. Defined at `:30` from `REPO_ROOT` (imported from `tests.support`, `:28`). Any assertion over its MEMBERSHIP inherits every legitimate lifecycle move.
- THE FAILURE IS LATENT TODAY. `32ij2j` moved to `superseded/` in commit `32e4b74f`; the test globs `pending/` only. Do not write the plan as if the suite were red.
- ONE PLAN SHARES THE FILE. `8v5pwa` (`rdattest-02`) declares `tests/test_plan_readiness.py` and its E-04 targets the auto-approve predicate, a different class. Merge ordering, not a dependency.
- `utwr6y` IS A NEIGHBOUR, NOT A DEPENDENCY. Different file, different tree (synthetic RUN tree), and its E-04 sweep is scoped to REPORT ONLY.
- Shared checkout: 92 pending plans, 18 approved plans executing in live runs, three concurrent graduations. Fixtures only; never mutate a plan to move a test.
- The suite runs BARE (`python3 -m pytest`); `-o addopts=""` is legitimate only for a narrowed per-module count, as the item's own verify-by-running instruction uses.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | false by construction | The assertion demands NO pending plan carry a negative verdict, so any legitimate `/plan-review` REJECT reds the suite. A rejected plan awaiting replan is exactly what `pending/` should hold. | `tests/test_plan_readiness.py:789-798` |
| F-2 | HIGH | the proxy cannot distinguish true from false refusal | "Any pending plan is refused" collapses a parser bug and a correct rejection into one signal, while the docstring's intent is only the former. | `:790`, `:797` |
| F-3 | HIGH | the correct pattern is already in the same class, twice | Named id6s resolved by `_find` across five dispositions, with an honest `skipTest` and a checked counter. | `:772-779`, `:781-787`, `:800-818` |
| F-4 | HIGH | **the item's repro no longer reproduces; the bug is LATENT** | `pytest tests/test_plan_readiness.py -o addopts=""` -> `67 passed`; bare suite `5859 passed, 3 skipped, 2 xfailed`. Cause: `32ij2j` moved `pending/` -> `superseded/` in commit `32e4b74f`. Its REJECT record survives; the tree changed. So E-01 must manufacture the condition. | measured at HEAD `fac69fbd` |
| F-5 | MEDIUM | **the item is wrong that the sibling instance self-healed** | It was DELIBERATELY fixed: renamed to `test_runprofile_is_not_refused_for_unauthored_rows` in commit `31169afd`, docstring reasoning that the old form "pinned a transient repository state rather than the behavior this test is named for". The old node id collects 0 items. This is a second precedent FOR the fix. | `tests/test_orchestrator_retirement.py:890`, `:891-901` |
| F-6 | MEDIUM | the briefing's baseline does not hold here | `test_orchestrator_retirement.py` reports `112 passed`; the bare suite is green. Report observed counts, not quoted ones. | measured at HEAD `fac69fbd` |
| F-7 | MEDIUM | no plan fixes it, and two disclaim it | `corpuspin`/`yw6759`: zero hits in any disposition. Twelve pending plans record the failure as a baseline to ignore; `daexj1:127` and superseded `xtklpd:254` explicitly decline to fix it. | plan-tree search |
| F-8 | MEDIUM | the class has three known instances | This test; the orchestrator-retirement test (fixed); `tests/test_run_viewer.py`'s runs-tree dependence (owned by `utwr6y`). | F-5; `utwr6y` E-01..E-04 |
| F-9 | MEDIUM | `utwr6y` supplies an inventory, not a guard | Its E-03 guard is specific to the run-viewer suite and forbids a source grep; its E-04 sweep is "REPORT, DO NOT SILENTLY WIDEN". So a class-wide guard is unowned. | `utwr6y` E-03, E-04 |
| F-10 | MEDIUM | the cost has been paid repeatedly in review prose | Review records spend paragraphs establishing a suite failure "is not this plan's", and one disclosed that THE REVIEWER CAUSED it by rejecting a sibling plan, i.e. the gate working as designed recorded as collateral damage. `executed/...29wvmj:142` calls this test a "CORPUS TRAP". | `29wvmj:142`; `eqzd0h:369`, `:379`; `03ie04:838`, `:845` |
| F-11 | LOW | one file-sharing plan, not a dependency | `8v5pwa` declares `tests/test_plan_readiness.py`; its E-04 targets the auto-approve predicate, not this class. | `8v5pwa` Scope-Paths, E-04 |
| F-12 | LOW | the fix needs no new fixture | `_find` already exists and already skips honestly; `utwr6y`'s synthetic run-tree fixture is the wrong axis. | `:772-779` |
| F-13 | LOW | noticed outside scope, reported not acted on | `utwr6y`'s E-01/E-02 look largely satisfied by commit `e167c9b3` (which added an in-file fixture and a hazard note at `tests/test_run_viewer.py:22-27`) while its E-03 file does not exist; it carries `Blocks-Release: next`. Not this plan's item. | `e167c9b3`; `tests/test_run_viewer.py:22-27` |

## Proposed changes (ordered, validatable)

1. Manufacture the latent failure on a fixture and paste it, plus the current live-tree green (E-01).
2. Replace the whole-tree glob with named id6s through the existing `_find`, keeping the honest skip and counter (E-02).
3. Decide whether a corpus-wide property is wanted, and if so phrase it over the approving-verdict token (E-03).
4. Record a decision on a class-wide guard, checking `utwr6y` first, and file a follow-up rather than building (E-04).
5. Prove both siblings green and non-vacuous, no plan edited, bare-suite delta empty (E-05).

## Deferred / out of scope (with reason)

- EDITING `32ij2j` OR ANY REVIEW RECORD. Its REJECT is correct and its status is correct. Changing a review record to make a test pass would forge review evidence, which is precisely what the approval-gate machinery exists to prevent. The item says this in capitals and it is repeated here because it is the one tempting wrong fix.
- DELETING THE TEST. Its intent is sound and stated in two docstrings; a fixture-only suite genuinely can pass while the gate misjudges reality. This plan repairs the proxy, not the purpose.
- A GENERAL GUARD AGAINST "TEST ASSERTS ON LIVE REPO CORPUS". E-04 records the decision and may file a follow-up. Building it here is refused for two reasons: it is a new cross-cutting mechanism with its own false-positive risk, and some live-corpus coupling in this very class is DELIBERATE and valuable, so a blunt detector would forbid the good case with the bad.
- `tests/test_run_viewer.py`'s LIVE-TREE COUPLING. `utwr6y` (`testiso-01`) owns it, on a different file with a different fixture axis. Its E-04 sweep may name further instances; that is an inventory for a future decision, not work for this plan.
- THE AUTO-APPROVE PREDICATE AND THE FORGED-`Readiness` CASE. `8v5pwa` (`rdattest-02`) owns them in the same file but a different class.
- CHANGING `plan_readiness.newest_verdict` OR ANY GATE CODE. The gate is working correctly; the item's whole finding is that the TEST is wrong. `Scope-Paths` is deliberately the test file alone, and an executor who finds themselves editing `agent_workflows/plan_readiness.py` has left this plan's scope and should stop and report.
- FIXING `utwr6y`'s APPARENT PARTIAL COMPLETION (F-13). Reported to the maintainer; it belongs to another item and another agent may hold it.

## Scope check

- Over-scope: none. One test method rewritten, one optional corpus property, one recorded decision, one test file.
- Scope-Paths justification: `tests/test_plan_readiness.py` holds the defective assertion (`:789-798`), the `PENDING_DIR` constant it globs (`:30`), the `_find` helper E-02 reuses (`:772-779`), the two sibling tests that supply the pattern and that E-05 must keep green and non-vacuous (`:781-787`, `:800-818`), and the class docstring (`:770`) whose intent E-02 must preserve while rewording. Nothing else is needed, and that is the point: the gate code is correct.
- Under-scope, stated rather than left as `none`: this plan edits no plan and no review record, changes no gate code, deletes no test, builds no class-wide guard (E-04 decides and may file), does not touch `tests/test_run_viewer.py` or `tests/test_orchestrator_retirement.py`, and writes no spec.

## Required tests / validation

- THE MANUFACTURED FAILURE (E-01) pasted: the assertion's logic failing against a synthetic REJECTed plan and NAMING it, exactly as it would have named `32ij2j`.
- THE CURRENT GREEN ALSO PASTED, so the record is honest that the failure is latent: `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` at HEAD with its summary line.
- THE REWRITTEN TEST PASSING, with the pinned id6 list quoted and each id6's known polarity stated with the disposition it resolved from.
- THE CHECKED-COUNTER SHOWN NONZERO, proving the new test did not pass vacuously, and the honest-skip path exercised at least once (for instance by pinning an id6 that is deliberately absent in a fixture run) so the skip is demonstrated rather than assumed.
- BOTH SIBLINGS GREEN AND NON-VACUOUS: `test_the_three_item_13_successors_are_not_refused` (resolving `6lu3rq`, `m73aet`, `wlxkoz`) and `test_the_incident_plans_are_refused` (resolving `bmh754`, `a54m79`, `kaygwo`, `k7o7el`, `7f7782`, with its counter nonzero). Paste the module's own summary line.
- IF E-03 BUILT A CORPUS PROPERTY: shown passing against a corpus that CONTAINS a legitimately REJECTed pending plan, using E-01's fixture.
- NEGATIVE PROOF THAT NOTHING ELSE MOVED: `git status --porcelain .aw/records/plans/` clean, and `git diff --stat` showing `tests/test_plan_readiness.py` as the only changed file.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set. Measured in this lane at HEAD `fac69fbd`: `5859 passed, 3 skipped, 2 xfailed`; the briefing's `1 failed, 5648 passed` does NOT reproduce here. State what you observe. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC CHANGE, and no `.spec.md` path is declared. This plan changes a TEST's assertion, not a contract: the approval gate's behavior is unchanged, `plan_readiness.newest_verdict` is unchanged, and no artifact's meaning moves. An executor who finds a spec constraining what this test must assert should STOP and report rather than editing either.

THE DOCSTRINGS ARE THE DOCUMENTATION HERE, and E-02 must treat them as deliverables rather than incidentals. Two things must be written down where the next reader will hit them: that the check is against NAMED plans whose verdict polarity is known, and WHY the whole-tree form was wrong (a legitimately REJECTed pending plan is a correct state, so "no pending plan is refused" is false whenever the gate works). Without the second sentence, someone restores the tree-wide assertion in good faith.

RECORD THE THIRD-INSTANCE ARGUMENT IN E-04's DECISION, not only in this plan. `tests/test_orchestrator_retirement.py:891-901` already carries the reasoning for its own instance; the class-level observation (three instances, one fixed, one here, one owned by `utwr6y`) is durable knowledge that belongs in whatever follow-up E-04 files, so it is not re-derived a fourth time.

## Open questions

### OQ-01: Should a whole-corpus property exist at all after this fix?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN AND ASSIGNED TO E-03, because it is a genuine cost/benefit judgement rather than a fact the repository can settle. The class exists on the stated premise that "a fixture-only suite can pass while the gate misjudges reality" (`:770`), which argues FOR keeping some live-corpus check. Against it: any corpus-wide assertion reads every pending plan on every suite run, and the defect being fixed here is precisely what happens when such an assertion picks a property the corpus may legitimately violate. The one defensible formulation the item offers is "no plan whose newest review record contains an APPROVING verdict token is refused", which is stable under any legitimate state and still catches the parser bug the test was written for. E-03 must decide and record; recording NO is acceptable, since E-02's named-id6 test covers the stated intent.

### OQ-02: Does the class deserve a general guard?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN AND ASSIGNED TO E-04 AS A RECORDED DECISION, NOT A BUILD. The argument for is that the class has produced three known instances, one of them red for days. The arguments against are specific rather than lazy: a detector for "test reads live repo state" would flag the DELIBERATE and valuable cases in this very class, `utwr6y` E-03 already establishes that the obvious implementation (a grep over test source) is unsound because "it would pass while an implicit `dir='.'` still reached the live tree", and `utwr6y` E-04 is already producing an inventory scoped explicitly to REPORT and NOT FIX. So the cheapest correct next step is to let that inventory land and then decide with data. E-04 therefore records the decision and files a follow-up if wanted; non-blocking because this plan's fix stands either way.

### OQ-03: Which plans should the rewritten test pin?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A RULE RATHER THAN A LIST, because a hardcoded list authored today would itself age. The rule: pin plans whose newest review record's polarity is KNOWN AND POSITIVE, resolved by id6 across all five dispositions through the existing `_find`, with the reason each polarity is known recorded beside the id6. That is exactly what the sibling `test_the_three_item_13_successors_are_not_refused` does with `6lu3rq`/`m73aet`/`wlxkoz`, two of which have already moved from `pending/` to `executed/` without breaking it, which is the proof the pattern survives corpus drift. Deliberately NOT pinned: any plan chosen because it is currently PENDING, since pending membership is the mutable fact that caused this bug. E-02 selects the concrete ids and records the justification; the rule, not the list, is what a reviewer should check.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the ACTUAL failing output against the synthetic REJECTed plan, showing the assertion naming it. Paste the current live-tree run (`python3 -m pytest tests/test_plan_readiness.py -o addopts=""`) with its summary line, so the record states plainly that the failure is latent. Paste `git status --porcelain .aw/records/plans/` proving no real plan was created, moved or edited to manufacture it.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rewritten test in full. Quote the pinned id6 tuple and, for each id6, state its known verdict polarity and the disposition directory it resolved from. Show it calls the existing `_find` rather than a new helper. Paste the reworded docstring and confirm it states WHY the whole-tree form was wrong, not merely what the new form does.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state the decision on the corpus-wide property with its reasoning. If NO, that is a complete answer and the reason is the evidence. If YES, paste the property's code showing it is phrased over the APPROVING verdict token rather than over tree membership, and paste it PASSING against a corpus containing E-01's legitimately REJECTed plan.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: state the recorded decision on a class-wide guard, citing all three known instances by test name and file. Confirm in one sentence that `utwr6y`'s E-03 file and E-04 sweep were checked and are not duplicated. If a follow-up was filed, paste its id and summary; if not, state why the inventory should land first.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `tests/test_plan_readiness.py`'s own summary line showing both siblings green, and paste evidence the incident-plans counter was NONZERO (so it did not pass vacuously). Paste the honest-skip path exercised at least once. Paste `git status --porcelain .aw/records/plans/` clean and `git diff --stat` showing only the test file changed. THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta as a set, with the counts you actually observed rather than any quoted baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-03 (which plans to pin) is resolved as a RULE rather than a list, and OQ-01 (corpus-wide property) and OQ-02 (class-wide guard) are both assigned to E-items that may legitimately answer "no, and here is why", so the fix lands either way.

IT CARRIES `Blocks-Release: next`, inherited from backlog `yw6759` under the all-bugs-block-release rule. A REVIEWER SHOULD WEIGH THAT DELIBERATELY, because the failure is currently LATENT (F-4): the suite is green today only because the rejected plan moved out of `pending/`. The case for keeping the gate is that the value is preventing recurrence and the fix is small; the case against is that a latent bug may not need to gate a release. That is the maintainer's call, and it is stated here rather than assumed.

THE ONE TEMPTING WRONG FIX IS NAMED EXPLICITLY. Do not edit `32ij2j`, and do not edit any review record, to make a test pass. That would forge review evidence, which is exactly what the approval-gate machinery exists to prevent.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Manufacture the failure on a FIXTURE: 92 plans are pending, 18 approved plans are executing in live runs, and three agents are graduating concurrently, so creating or moving a real plan to trigger a test would interfere with other runs. Re-locate every symbol by NAME. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the manufactured failure, the current-green disclosure, the per-id6 polarity justification, and the nonzero sibling counter.
