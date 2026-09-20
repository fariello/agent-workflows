# IPD: Pin the approval-gate corpus test to named id6s so a legitimate plan-review REJECT cannot red the suite

- Date: 2026-09-08
- Kind: child
- Concern: A TEST ASSERTS SOMETHING THAT IS FALSE BY CONSTRUCTION WHENEVER THE GATE WORKS. `tests/test_plan_readiness.py:789-798`, `ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`, globs the LIVE pending tree (`PENDING_DIR`, `:30`) and asserts no plan there carries a negative review verdict: `refused = [p.name for p in pending if PR.newest_verdict(...)[0] == PR.NEGATIVE]` then `self.assertEqual(refused, [], "pending plans falsely refused on their verdict")`. A pending plan that was legitimately REJECTed by `/plan-review` and is awaiting a replan is exactly what the pending tree SHOULD contain, so the suite reds on correct behavior.
  THE TEST'S INTENT IS SOUND, WHICH IS WHY THIS IS A REPAIR AND NOT A DELETE. Its docstring says "A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard" and its class docstring (`:770`) says "a fixture-only suite can pass while the gate misjudges reality". Both are right. The defect is the PROXY: "any pending plan is refused" cannot distinguish a FALSE refusal from a TRUE one.
  THE CORRECT PATTERN ALREADY EXISTS TWICE IN THE SAME CLASS, so the fix needs no design. `test_the_three_item_13_successors_are_not_refused` (`:781-787`) pins THREE named id6s that must NOT be refused and resolves each by id6 across five dispositions via the `_find` helper (`:772-779`), which calls `skipTest` when a plan is absent. `test_the_incident_plans_are_refused` (`:800-818`) pins FIVE named id6s that MUST be refused, COUNTS how many it actually checked, and calls `skipTest` when none remain "so it says so rather than lying". Both encode one insight: assert on NAMED artifacts whose verdict polarity is known, never on a whole mutable tree.
  THE FAILURE IS CURRENTLY LATENT, NOT ACTIVE, AND THAT IS THE ONE THING THIS PLAN MUST NOT HIDE. Measured in this lane at HEAD `fac69fbd`: `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` reports `67 passed`. RE-MEASURED AT REVIEW (HEAD `72d1b018`): still `67 passed`, and independently confirmed that ZERO of the now-104 pending plans parse NEGATIVE, so the assertion is vacuously true today. The reason is that `32ij2j`, the plan whose legitimate REJECT reddened the suite when the item was filed, has MOVED from `pending/` to `superseded/` (commit `32e4b74f`, verified), and the test globs `pending/` only; its REJECT record is intact (`newest_verdict` still returns `negative` for it). So the bug did not get fixed; the corpus drifted out from under it, which is the same accidental self-healing the item warns about for its sibling instance.
  WHAT THE ASSERTION ACTUALLY COVERS TODAY, MEASURED AT REVIEW, because it decides whether this plan is a net gain: it reads all 104 pending plans and parses each one's newest review record. By polarity they are 70 positive, 15 neutral, 19 unparseable (`None`). So the test exercises `newest_verdict` against 104 REAL, varied, human-authored review records on every suite run, and that breadth is the class's stated reason for existing ("a fixture-only suite can pass while the gate misjudges reality"). THE PLAN'S FIX AS WRITTEN REDUCES THAT TO A HANDFUL OF PINNED IDS, and E-03 explicitly permits answering "no corpus property wanted". Taken together those two steps would REMOVE 104-plan coverage and replace it with N-plan coverage, which repairs the false-by-construction defect by deleting the value rather than by fixing the proxy. E-03 is therefore no longer optional in the direction the plan allowed: see F-14 and the corrected E-03.
  AND THE CORPUS PROPERTY THE PLAN PROPOSES IS UNFALSIFIABLE, which is the finding that most changes the work. The plan (and the backlog item) offer "no plan whose newest review record contains an APPROVING verdict token is refused" as the defensible replacement. Measured at review: `newest_verdict` DERIVES its polarity by calling `classify_verdict` on that same record and returning the result (`plan_readiness.py:414-416`), so asserting "if `classify_verdict` says positive then `newest_verdict` is not negative" compares one function to its own internal call. It cannot fail for any input, and it holds across all 608 corpus plans for that reason rather than as evidence. Shipping it would replace a test that is false whenever the gate works with a test that is true whenever anything at all happens, which is worse: the first at least fails loudly. A FALSIFIABLE REPLACEMENT WAS FOUND AND VERIFIED AT REVIEW; it is specified in E-03 and F-15.
- Scope: Replace the whole-tree assertion with the named-id6 pattern its two siblings already use, using the existing `_find` helper and an honest `skipTest`, and add a corpus-property assertion that survives a legitimate REJECT if one is genuinely wanted. EXCLUDES editing `32ij2j` or any plan's review record; EXCLUDES a general guard against the whole "test asserts on live repo corpus" class (recorded as a decision with evidence, and a follow-up filed if wanted); EXCLUDES `tests/test_run_viewer.py`'s live-tree coupling, which `utwr6y` owns.
- Scope-Paths: tests/test_plan_readiness.py
- Item-Dependencies: none
- Status: executed
- Set: gatepin
- Order: 1
- Highest E allocated: 05
- Readiness: go-pending-approval
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: h3bjue
- From-Backlog: yw6759
- Blocks-Release: next

## Workflow history
- 2026-09-20 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: h3bjue verified (set gatepin, attempt 1).
- 2026-09-20 validated (opencode its_direct/pt3-claude-opus-5-1m-us): E-01..E-05 performed and V-01..V-05 verified with pasted evidence; `aw ipd lint --phase pre-transition` conforms with ZERO diagnostics and `aw sanitize --agent` is clean. THE DEFECT WAS MITIGATED BETWEEN REVIEW AND EXECUTION AND THAT CHANGED THE WORK: commit `7b9f3ae2` (2026-09-19) marked the target assertion `@pytest.mark.livecorpus` and `pyproject.toml:170` deselects that marker by default, so the false-by-construction assertion was intact but no longer collected in a default run. It was therefore manufactured on a FIXTURE (symlinks to all 102 real pending plans plus one synthetic REJECTed plan, `PENDING_DIR` redirected, shipped test body called unmodified) and shown FAILING while naming the synthetic plan, with the current green also pasted; no real plan was created, moved or edited. E-02 replaced the whole-tree glob with four id6s pinned for NAMED parser hazards (`fn2l1u` a positive verdict whose prose contains REJECT, `8lfoum` an attestation narrating a cleared no-go and containing REJECT, `btot17` a positive verdict narrating a superseded no-go, `920qnm` a PARENTHESIZED actor, the fn2l1u fail-open shape), each polarity MEASURED positive, all four in `executed/`, resolved through the existing `_find`, with a checked counter and an honest skip both demonstrated. It asserts `assertEqual(polarity, POSITIVE)` rather than the sibling's `assertNotEqual(..., NEGATIVE)`, which passes trivially for `None`. E-03 built the property review specified and REJECTED the unfalsifiable token property in code comment, shown FAILING against a synthetic no-verdict-token plus negative-readiness record and PASSING over the real corpus (7 of 694 parse NEGATIVE, all 7 contain REJECT, including `32ij2j` itself). NET COVERAGE ROSE: 694 real review records parsed after versus 102 pending-only before, so F-14's coverage-loss hazard is closed rather than acknowledged. E-04 recorded the decision and filed backlog `jb0sc1`, resolving OQ-02: the `livecorpus` marker supplies the discriminator OQ-02 said did not exist, and a sweep found SIX unmarked live-corpus call sites in four modules. Bare `python3 -m pytest` BEFORE `1 failed, 7206 passed, 3 skipped, 2 xfailed` and AFTER `1 failed, 7207 passed, 3 skipped, 2 xfailed`; failure-set delta EMPTY, the single failure being the pre-existing `test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which asserts about a NON-isolated turn and fails because this lane is an isolated worktree. The plan's four recorded baselines are all stale; this is the fifth, measured here, and the named `test_reporting_contract.py` failure does not reproduce (no `opencode-recovery/` in this lane; nothing of another party's was deleted, moved or modified). ONE DEFECT FOUND AND REPORTED, NOT FIXED: the sibling `test_the_three_item_13_successors_are_not_refused` now passes VACUOUSLY, since all three pinned ids (`6lu3rq`, `m73aet`, `wlxkoz`) measure polarity `None` and `assertNotEqual(..., NEGATIVE)` passes for `None`; filed as backlog `nz5cl2` (`bug`, `Blocks-Release: next`) rather than repaired, because the cause is that their newest records state no verdict token, so no assertion tweak fixes it. Deviation stated plainly: the E-03 property carries `@pytest.mark.livecorpus`, which the plan could not have asked for, so it runs in `make test-all`/`-m ''` and not in a default bare run; the E-02 test is deliberately unmarked and does run by default. No gate code was touched.
- 2026-09-13 approved (aw set): status set to approved
- 2026-09-10 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-007 all FIXED; review record written; Readiness go-pending-approval

- 2026-09-10 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-007; Readiness go-pending-approval. Reviewed at HEAD `72d1b018`; `aw ipd lint` conformed at `--phase author` before and `--phase review-finalize` after. THE DIAGNOSIS IS EXACTLY RIGHT AND THE RESTRAINT IS EXEMPLARY, and I weakened neither: the assertion really is false by construction, the fix pattern really does exist twice in the same class, the refusal to delete the test or edit `32ij2j` is correct, and the plan corrected three of its own backlog item's claims including proving that the sibling instance was DELIBERATELY fixed rather than self-healed. Every one of those re-verified true: `67 passed`, `32ij2j` in `superseded/` via `32e4b74f` with its REJECT intact, the renamed orchestrator test at `:890` with the cited docstring reasoning, `112 passed` in that module, and all eight sibling id6s resolving from the dispositions the plan names. TWO FINDINGS CHANGE THE WORK, and both come from measuring what the plan proposed rather than what it diagnosed. PR-001 (BLOCKER): the corpus property the plan and the item both recommend, "no plan whose newest review record contains an APPROVING verdict token is refused", is UNFALSIFIABLE. `newest_verdict` derives its polarity by calling `classify_verdict` on that record and returning the result (`plan_readiness.py:414-416`), so the property compares a function to its own internal call; it holds over all 608 corpus plans because it must. Shipping it would trade a test that is false whenever the gate works for one that is true unconditionally, which is worse because the first at least fails loudly. A falsifiable replacement was found and verified in both directions: every `NEGATIVE`-parsing newest record must literally contain `REJECT`, which can fail via the no-verdict-token plus negative-readiness route (`:417-420`), survives a legitimate REJECT by construction, and whose failure mode IS the false-refusal class the test exists to catch. PR-002 (HIGH): E-02 alone is a net LOSS of coverage. The removed assertion parses 104 real review records every run (measured: 70 positive, 15 neutral, 19 unparseable); E-02 replaces that with a handful of pinned ids and E-03 was permitted to decline a replacement, so the pair as written could have repaired the defect by deleting the class's stated value. E-03 is now a BUILD and OQ-01 is resolved accordingly. PR-003 (MEDIUM): 19 of 104 pending plans parse to polarity `None`, and the sibling assertion passes trivially for `None`, so OQ-03's "known and positive" had to become MEASURED positive or a pinned id could assert nothing. PR-004, PR-005, PR-006, PR-007: the baseline has now been wrong three times and the current single failure walks another party's gitignored `opencode-recovery/` (deletion prohibited in three places); the pending count is 104 not 92; `utwr6y`'s E-03 file confirmed still absent; the `Blocks-Release` target confirmed to resolve to `f33nrj`. No product code was modified by this review.

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `yw6759`. NOTHING IS OBSOLETE: the false-by-construction assertion is byte-for-byte intact at `tests/test_plan_readiness.py:789-798`, still globbing the live `PENDING_DIR` (`:30`), and NO plan in any disposition fixes it (searched all five for `test_plan_readiness`, `ApprovalGateRealCorpusTests`, `newest_verdict`, `corpuspin`, `yw6759`; `corpuspin` and `yw6759` have ZERO hits anywhere, and every `ApprovalGateRealCorpusTests` hit is a BASELINE NOTE recording it as a known failure to ignore, in at least `9xycbh:111`, `6eq3oq:169`, `5f2h8i:152`, `lhccjf:158`, `m7gvuz:114`, `:138`). TWO plans explicitly DISCLAIM fixing it: `daexj1:127` ("AUTO-FIXING THE CURRENT RED TEST ... belongs to whoever owns plan `32ij2j`'s REPLAN verdict") and superseded `xtklpd:254` ("Do not fix either here"). THREE OF THE ITEM'S CLAIMS ARE NOW WRONG AND ALL THREE ARE RECORDED HERE RATHER THAN CARRIED FORWARD. FIRST, the stated repro does NOT reproduce: `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` reports `67 passed` and the bare suite `5859 passed, 3 skipped, 2 xfailed`, because `32ij2j` moved from `pending/` to `superseded/` in commit `32e4b74f` (its REJECT record survives one entry deeper, so the verdict is still negative; the tree it sits in changed). The bug is LATENT, and E-01 must therefore MANUFACTURE the condition on a fixture instead of quoting the item's repro. SECOND, the item says its sibling instance in `test_orchestrator_retirement.py` "self-healed by corpus drift rather than being fixed"; that is FALSE. The test was DELIBERATELY renamed and rewritten to `test_runprofile_is_not_refused_for_unauthored_rows` (`tests/test_orchestrator_retirement.py:890`) in commit `31169afd`, whose new docstring (`:891-901`) reasons that asserting the refusal "pinned a transient repository state rather than the behavior this test is named for". That is the SAME insight this plan applies, already applied once in-repo, so it is a second local PRECEDENT that strengthens the item rather than obsoleting it; the old node id no longer exists (`pytest` on it collects 0 items). THIRD, the graduation briefing's baseline of `1 failed, 5648 passed` naming `test_orchestrator_retirement` does not hold here: that module reports `112 passed` and the bare suite is green. ONE PLAN SHARES THE FILE: `8v5pwa` (`rdattest-02`) declares `tests/test_plan_readiness.py` in `Scope-Paths` and its E-04 adds a forged-`Readiness`-field test to the auto-approve predicate; it does not touch `ApprovalGateRealCorpusTests`, so this is merge ordering, not a dependency. `utwr6y` (`testiso-01`) is NOT a dependency: it builds a synthetic RUN tree fixture for `tests/test_run_viewer.py`, a different tree on a different axis, and this fix needs no fixture beyond the `_find` helper that already exists. Noted for the maintainer, outside my items: `utwr6y`'s E-01/E-02 appear largely satisfied already by commit `e167c9b3`, while its E-03 file `tests/test_run_viewer_isolation.py` does not exist, and it carries `Blocks-Release: next`.

## Goal

Make the approval gate's real-corpus test assert a property that stays true while the gate works, so a legitimate `/plan-review` REJECT stops reddening the suite and stops teaching every agent and human that a red suite is normal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: manufacture the latent failure before fixing it

- [x] E-01 REPRODUCE THE DEFECT DELIBERATELY, since it no longer reproduces on its own, and this is the step a careless executor will skip. The item's stated repro is stale: `32ij2j` left `pending/` in commit `32e4b74f`, so the test now passes (`67 passed`) while the defect is untouched. Demonstrate the assertion is false-by-construction rather than asserting that it is.
  DO IT ON A FIXTURE, NEVER ON THE LIVE TREE. Two ways are acceptable and both must avoid mutating the repository: point the assertion's logic at a temporary directory containing one synthetic plan whose newest review record is a REJECT, or parameterize the predicate and feed it a synthetic file list. Do NOT create, move, or edit any real plan to trigger it: 104 plans are pending (re-measured at review; the plan said 92), approved plans are executing in live runs, and other agents are graduating concurrently.
  A WORKED SYNTHETIC RECORD, verified at review to parse as `NEGATIVE`, so you need not discover the shape: a plan whose `## Workflow history` newest entry reads `- 2026-09-08 reviewed (opencode/m): /plan-review REJECT - NEEDS REPLAN; readiness NO-GO`. `newest_verdict` returns `negative` for that, which is what the assertion keys on. `classify_verdict` reads the FIRST verdict token in the record message, so keep the token near the front.
  PASTE THE FAILURE. The evidence required is the assertion failing with the synthetic REJECT present, naming it, exactly as it would have named `32ij2j`. A fix demonstrated only against the fixed code proves nothing about the defect.
  ALSO PASTE THE CURRENT GREEN, so the record is honest about the failure being LATENT. `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` at HEAD, with its summary line. Re-measured at review: `67 passed`, and ZERO of the 104 pending plans parse `NEGATIVE`, so the assertion is currently VACUOUSLY true. Paste both facts; do not let a later reader believe this plan was written against a red suite.
  - Depends on: none
  - Expected outcome: the false-by-construction assertion shown FAILING against a synthetic REJECTed plan with output pasted, the current live-tree GREEN also pasted along with the count of pending plans currently parsing `NEGATIVE`, and no real plan created, moved or edited.
  - Execution state: performed

### Task group 2: apply the pattern the siblings already use

- [x] E-02 REPLACE THE WHOLE-TREE ASSERTION WITH THE NAMED-ID6 PATTERN, and copy the siblings rather than inventing a shape. `test_the_three_item_13_successors_are_not_refused` (`:781-787`) is the exact model: iterate a tuple of named id6s, resolve each with the existing `_find` helper (`:772-779`), and assert the polarity. `_find` already walks `pending`, `executed`, `superseded`, `not-executed`, `reusable` and already calls `skipTest` when a plan is absent, so no new helper is needed.
  CHOOSE THE PINNED IDS FOR A STATED REASON, not by convenience. The property the test exists to catch is a FALSE refusal: a plan whose newest review record is APPROVING that the parser nonetheless reads as negative. So pin plans whose verdict polarity is KNOWN and POSITIVE, and record for each id6 why its polarity is known. Do not pin a plan merely because it is currently pending; pending is the mutable fact that caused the bug.
  KEEP THE HONEST-SKIP BEHAVIOR AND THE CHECKED COUNT. `test_the_incident_plans_are_refused` (`:800-818`) counts what it checked and skips with a reason when nothing remains, explicitly "so it says so rather than lying". A test that silently passes because its subjects vanished is the same class of defect in a new dress; carry the counter over.
  PRESERVE THE DOCSTRING'S INTENT, REWORDED. "A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard" is still the point; it must now say that the check is against NAMED plans whose polarity is known, and say WHY the whole-tree version was wrong, so nobody restores it. State the reason precisely: a legitimately REJECTed plan sitting in `pending/` awaiting replan is a CORRECT state, so "no pending plan is refused" is false exactly when the gate is working.
  DO NOT PIN AN ID6 WHOSE POLARITY IS `None`. Measured at review, 19 of the 104 pending plans parse to `None` (no readable verdict), and `assertNotEqual(polarity, NEGATIVE)` passes trivially for those, so pinning one would look like coverage while asserting nothing. Pin only ids whose polarity is affirmatively POSITIVE, and record the polarity you measured for each, not merely that it is "known".
  PREFER IDS IN TERMINAL DISPOSITIONS, and say so with the reason: the sibling this item copies resolves `6lu3rq`, `m73aet`, `wlxkoz`, all of which sit in `executed/` (verified at review), and its own docstring notes two of the three moved out of `pending/` without breaking it. That is the proof the pattern survives drift, and it is also the argument against pinning anything currently pending.
  THIS ITEM ALONE IS A COVERAGE REDUCTION, so it is not the whole fix. It trades 104 real review records for N. E-03 is what restores whole-corpus coverage with a property that can actually fail, and the two must land together; do not treat E-03 as optional (F-14).
  - Depends on: E-01
  - Expected outcome: the whole-tree glob replaced by named id6s resolved through the existing `_find`, each pinned id6's MEASURED polarity recorded as positive with its disposition, no `None`-polarity id pinned, the checked-count and honest-skip carried over, and the docstring stating why the tree-wide form was wrong.
  - Execution state: performed

- [x] E-03 BUILD A WHOLE-CORPUS PROPERTY THAT IS BOTH FALSIFIABLE AND STABLE UNDER A LEGITIMATE REJECT. This item was a "decide whether" and is now a "build it", for two measured reasons (F-14, F-15): without it this plan is a net LOSS of coverage, dropping from 104 real review records to a handful of pinned ids; and the property the plan and the item proposed cannot fail.
  DO NOT BUILD THE PROPOSED PROPERTY. "No plan whose newest review record contains an APPROVING verdict token is refused" is UNFALSIFIABLE. Measured at review: `newest_verdict` computes its polarity as `_, polarity = classify_verdict(message)` and returns that value (`agent_workflows/plan_readiness.py:414-416`), so the antecedent and the consequent are the same line of code. It holds over all 608 corpus plans because it must, not because the gate is healthy. A test that cannot fail is worse than the one being removed.
  BUILD THIS INSTEAD, verified falsifiable at review: FOR EVERY PLAN IN THE CORPUS WHOSE NEWEST REVIEW RECORD PARSES AS `NEGATIVE`, THAT RECORD MUST LITERALLY CONTAIN THE `REJECT` TOKEN. It is falsifiable because `newest_verdict` has a SECOND route to `NEGATIVE`: when the record states NO verdict token at all, a negative READINESS token decides (`plan_readiness.py:417-420`). A record reaching `NEGATIVE` by that route contains no `REJECT`, so the assertion genuinely fails. Verified at review with a synthetic record (`readiness NO-GO, no verdict token stated` -> `polarity=negative`, no `REJECT` present, property violated).
  AND THAT FAILURE MODE IS THE REAL FALSE-REFUSAL CLASS, which is why this property serves the test's stated intent where the tautology does not: a reviewer who records a readiness but forgets the verdict token has their plan silently refused by the gate. That is precisely "a gate that refuses live, legitimately-reviewed plans is a lockout", detected across the whole corpus rather than for N pinned ids.
  IT SURVIVES A LEGITIMATE REJECT BY CONSTRUCTION: a properly REJECTed plan parses `NEGATIVE` and DOES contain `REJECT`, so it satisfies the property instead of violating it. That is the difference from the assertion being removed, and it is the sentence to put in the docstring.
  MEASURED BASELINE TO REPRODUCE, NOT TO TRUST: across all 608 plans in the five dispositions, 7 parse `NEGATIVE` and all 7 contain `REJECT`, so the property passes at review HEAD. Re-measure; if your count differs, report it rather than adjusting the property.
  SCOPE IT LIKE THE SIBLINGS: count what it checked and skip honestly if the corpus yields nothing to check, so it cannot pass vacuously if the tree is ever empty or unreadable.
  - Depends on: E-02
  - Expected outcome: a corpus-wide property asserting that every `NEGATIVE`-parsing newest review record contains `REJECT`, shown FAILING against a synthetic no-token/negative-readiness record and PASSING against the real corpus including a legitimately REJECTed plan, with a checked-count and honest skip; and a written statement that the originally proposed token property was rejected as unfalsifiable.
  - Execution state: performed

### Task group 3: the class, and the proof

- [x] E-04 RECORD A DECISION ON GUARDING THE WHOLE DEFECT CLASS, and check the two neighbours before designing anything, because the item explicitly warns they may collide.
  THE CLASS HAS NOW PRODUCED THREE KNOWN INSTANCES, which is the argument for a guard: this test; `test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` in `tests/test_orchestrator_retirement.py`, which asserted `{"kgpptv": "reviewed"}` against the live corpus, was red for days, and was DELIBERATELY rewritten to `test_runprofile_is_not_refused_for_unauthored_rows` (`:890`) with a docstring (`:891-901`) reasoning that it "pinned a transient repository state rather than the behavior this test is named for"; and `tests/test_run_viewer.py`'s dependence on the gitignored runs tree.
  CHECK `utwr6y` FIRST, AS THE ITEM INSTRUCTS. Its E-03 adds a regression guard in a new `tests/test_run_viewer_isolation.py` and explicitly forbids implementing it as a grep over test source, because that "would pass while an implicit `dir='.'` still reached the live tree". Its E-04 SWEEPS for the same class in other tests reading gitignored box-local state and is scoped to REPORT, NOT FIX (its own words, "REPORT, DO NOT SILENTLY WIDEN"). So `utwr6y` contributes an INVENTORY, not a guard, and a guard built here must not duplicate its file or its sweep.
  THE HONEST DEFAULT IS TO RECORD AND FILE, NOT TO BUILD. A general "this test reads live repo state" detector is a new cross-cutting mechanism with its own false-positive risk, and some live-corpus tests are DELIBERATE and valuable (this very class exists because "a fixture-only suite can pass while the gate misjudges reality"). A blunt guard would forbid the good case along with the bad. So the deliverable is a written decision plus, if a guard is wanted, a follow-up backlog item or plan; not an in-scope build.
  - Depends on: E-03
  - Expected outcome: a recorded decision on a class-wide guard citing all three instances and `utwr6y`'s inventory scope, with a follow-up filed if wanted, and no duplication of `utwr6y`'s file or sweep.
  - Execution state: performed

- [x] E-05 PROVE THE GATE'S REAL BEHAVIOR IS UNCHANGED IN BOTH DIRECTIONS, because the two sibling tests pin exactly that and are the reason this fix is safe.
  BOTH SIBLINGS MUST STAY GREEN AND NON-VACUOUS. `test_the_three_item_13_successors_are_not_refused` resolves `6lu3rq`, `m73aet`, `wlxkoz`, all currently in `executed/`; `test_the_incident_plans_are_refused` resolves `bmh754`, `a54m79`, `kaygwo`, `k7o7el`, `7f7782`, all currently in `superseded/`, and counts what it checked. Show they PASS and show the counter is nonzero, so neither passed vacuously.
  DO NOT EDIT `32ij2j` OR ANY REVIEW RECORD. Its REJECT verdict is correct and its status is correct. Changing a plan's review record to make a test pass would forge review evidence, which is the one thing the approval-gate machinery exists to prevent. Paste negative proof: `git status --porcelain .aw/records/plans/` clean.
  RUN THE SUITE BARE and judge on the DELTA. THREE DIFFERENT BASELINES HAVE NOW BEEN RECORDED FOR THIS PLAN AND ALL THREE ARE STALE, which is the reason the instruction is "state what you observe": the graduation briefing said `1 failed, 5648 passed` naming `test_orchestrator_retirement`; this plan said `5859 passed, 3 skipped, 2 xfailed` in a lane at `fac69fbd`; and at review HEAD `72d1b018` a bare run measures `1 failed, 5958 passed, 3 skipped, 2 xfailed`. The single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks 189 files in a GITIGNORED `opencode-recovery/` directory (1746 files) belonging to ANOTHER PARTY. `test_orchestrator_retirement.py` reports `112 passed`, so the briefing's named failure still does not reproduce.
  DO NOT DELETE, MOVE, OR MODIFY `opencode-recovery/` TO GREEN THE SUITE. It is another party's uncommitted data in a shared checkout, and removing it is the un-owned-state destruction AGENTS.md forbids. That failure is pre-existing, is not yours, and must be reported as such. Report AFTER minus BEFORE as a set and do not add `-n0`, a second `-q`, or `-p no:randomly` to the bare run.
  - Depends on: E-04
  - Expected outcome: both sibling tests green with a nonzero checked-count, negative proof that no plan or review record was edited, and a bare-suite delta that is empty with the observed counts stated and the pre-existing failure identified as not this plan's.
  - Execution state: performed

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
| F-13 | LOW | noticed outside scope, reported not acted on | `utwr6y`'s E-01/E-02 look largely satisfied by commit `e167c9b3` (which added an in-file fixture and a hazard note at `tests/test_run_viewer.py:22-27`) while its E-03 file does not exist; it carries `Blocks-Release: next`. Not this plan's item. CONFIRMED at review: `tests/test_run_viewer_isolation.py` still does not exist, `utwr6y` is `to-review` and declares it. | `e167c9b3`; `tests/test_run_viewer.py:22-27`; `ls` on that path |
| F-14 | HIGH | **FOUND AT REVIEW: E-02 alone is a net LOSS of coverage, and E-03 was allowed to decline** | The assertion being removed reads all 104 pending plans and parses each one's newest review record (measured at review: 70 positive, 15 neutral, 19 `None`), exercising `newest_verdict` against 104 real human-authored records every suite run. E-02 replaces that with a handful of pinned ids, and E-03 as written explicitly permitted answering "no corpus property wanted". Those two together would repair the false-by-construction defect by DELETING the class's stated value ("a fixture-only suite can pass while the gate misjudges reality") rather than by fixing the proxy. E-03 is therefore now mandatory. | measured polarity census over `pending/`; class docstring `tests/test_plan_readiness.py:770` |
| F-15 | BLOCKER-FOR-E-03-AS-WRITTEN | **FOUND AT REVIEW: the proposed corpus property is UNFALSIFIABLE** | Both the plan and backlog `yw6759` offer "no plan whose newest review record contains an APPROVING verdict token is refused". `newest_verdict` computes polarity as `_, polarity = classify_verdict(message)` and returns it (`plan_readiness.py:414-416`), so the antecedent and consequent are the same line of code; the assertion cannot fail for any input. It holds across all 608 corpus plans because it must. Shipping it would trade a test that is false whenever the gate works for one that is true unconditionally, which is strictly worse because the first at least fails loudly. | read `plan_readiness.py:406-422`; verified the property over 608 plans yields 0 violations by construction |
| F-16 | HIGH | **FOUND AT REVIEW: a falsifiable replacement exists, was verified, and serves the test's actual intent** | Property: every plan whose newest review record parses `NEGATIVE` must have a record literally containing `REJECT`. Falsifiable because `newest_verdict` reaches `NEGATIVE` by a SECOND route, the no-verdict-token plus negative-READINESS branch (`plan_readiness.py:417-420`); a record taking that route has no `REJECT` and violates the property. Verified failing on a synthetic record (`readiness NO-GO, no verdict token stated` -> `negative`, no `REJECT`). And that failure mode IS the false-refusal class the test exists to catch: a reviewer who records a readiness but omits the verdict token gets silently refused. Passes on the real corpus (7 of 608 parse `NEGATIVE`, all 7 contain `REJECT`), and survives a legitimate REJECT by construction. | measured both directions at review |
| F-17 | MEDIUM | **FOUND AT REVIEW: pinning a `None`-polarity plan would assert nothing** | 19 of the 104 pending plans parse to `None` (no readable verdict). The sibling pattern asserts `assertNotEqual(polarity, NEGATIVE)`, which passes trivially for `None`, so an id6 chosen for convenience could look like coverage while testing nothing. OQ-03's rule said "known and positive" without warning that a large fraction of the corpus is neither. | polarity census; `tests/test_plan_readiness.py:786-787` |
| F-18 | MEDIUM | the baseline has now been wrong three times | Briefing: `1 failed, 5648 passed` naming `test_orchestrator_retirement`. Plan: `5859 passed, 3 skipped, 2 xfailed`. Review HEAD `72d1b018`: `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the failure being `test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks another party's gitignored `opencode-recovery/` (1746 files). The plan's instruction to state observed counts is correct and is retained; the new failure needed naming so nobody deletes a co-worker's data to green the suite. | bare `python3 -m pytest` at review; `112 passed` in the orchestrator module |
| F-19 | LOW | the pending count drifted | The plan says 92 pending plans; measured 104 at review. Minor, but the figure appears in the execution contract as the reason not to mutate the live tree, so it is corrected rather than left. | `ls` count over `pending/` |

## Proposed changes (ordered, validatable)

1. Manufacture the latent failure on a fixture and paste it, plus the current live-tree green and the count of pending plans currently parsing `NEGATIVE` (E-01).
2. Replace the whole-tree glob with named id6s through the existing `_find`, keeping the honest skip and counter, pinning only measured-POSITIVE ids (E-02).
3. BUILD the corpus property that every `NEGATIVE`-parsing record contains `REJECT`, having rejected the unfalsifiable token property (E-03).
4. Record a decision on a class-wide guard, checking `utwr6y` first, and file a follow-up rather than building (E-04).
5. Prove both siblings green and non-vacuous, no plan edited, bare-suite delta empty (E-05).

NOTE THE SHAPE OF THE FIX AFTER REVIEW: E-02 narrows the assertion to named ids and E-03 restores whole-corpus coverage with a property that can actually fail. Neither alone is the repair. E-02 without E-03 trades 104 real records for a handful; E-03 without E-02 leaves the false-by-construction assertion in place.

## Deferred / out of scope (with reason)

- EDITING `32ij2j` OR ANY REVIEW RECORD. Its REJECT is correct and its status is correct. Changing a review record to make a test pass would forge review evidence, which is precisely what the approval-gate machinery exists to prevent. The item says this in capitals and it is repeated here because it is the one tempting wrong fix. HONORED AT EXECUTION: `git status --porcelain .aw/records/plans/` was empty throughout, `32ij2j` is untouched in `superseded/` with its REJECT intact, and the new E-03 property counts it as a PASSING row; no carrier needed.
  - Carrier-Declined: honored in full rather than deferred: `git status --porcelain .aw/records/plans/` was empty throughout, `32ij2j` is untouched in `superseded/` with its REJECT record intact, and the new E-03 property counts it as a PASSING row. Nothing outstanding remains to carry.
- DELETING THE TEST. Its intent is sound and stated in two docstrings; a fixture-only suite genuinely can pass while the gate misjudges reality. This plan repairs the proxy, not the purpose. HONORED AT EXECUTION: the intent was preserved and STRENGTHENED (102 records parsed before, 694 after), and both docstrings carry the reasoning forward; no carrier needed.
  - Carrier-Declined: honored in full rather than deferred: the test was repaired, not deleted, and its intent was strengthened from 102 parsed review records to 694. Nothing outstanding remains to carry.
- A GENERAL GUARD AGAINST "TEST ASSERTS ON LIVE REPO CORPUS". E-04 records the decision and may file a follow-up. Building it here is refused for two reasons: it is a new cross-cutting mechanism with its own false-positive risk, and some live-corpus coupling in this very class is DELIBERATE and valuable, so a blunt detector would forbid the good case with the bad. CARRIER AT EXECUTION: backlog `jb0sc1` (`livecorpusguard`, `open`, `low`, `chore`), which carries the four instances, the measured six unmarked call sites, and the guard shape the `livecorpus` marker now makes checkable.
  - Carrier: jb0sc1
- `tests/test_run_viewer.py`'s LIVE-TREE COUPLING. `utwr6y` (`testiso-01`) owns it, on a different file with a different fixture axis. Its E-04 sweep may name further instances; that is an inventory for a future decision, not work for this plan. CARRIER AT EXECUTION: `utwr6y` is now `superseded` (its live-tree cases were converted by `xbwq8n`), and the surviving guard gap is carried by backlog `rcmbnb` (`testisoguard`, `open`, `low`, `chore`); nothing here touches that file.
  - Carrier: rcmbnb
- THE AUTO-APPROVE PREDICATE AND THE FORGED-`Readiness` CASE. `8v5pwa` (`rdattest-02`) owns them in the same file but a different class. CARRIER AT EXECUTION: plan `8v5pwa`, verified still `approved` and still declaring `tests/test_plan_readiness.py`; its anchors were re-located by NAME here and this change touches no symbol it names.
  - Carrier: 8v5pwa
- CHANGING `plan_readiness.newest_verdict` OR ANY GATE CODE. The gate is working correctly; the item's whole finding is that the TEST is wrong. `Scope-Paths` is deliberately the test file alone, and an executor who finds themselves editing `agent_workflows/plan_readiness.py` has left this plan's scope and should stop and report. HONORED AT EXECUTION: `git diff --stat` shows `tests/test_plan_readiness.py` as the only source file changed; no gate code was touched, so this obligation needs no carrier.
  - Carrier-Declined: honored in full rather than deferred: `git diff --stat` shows `tests/test_plan_readiness.py` as the only source file changed and no gate code was touched, so there is no outstanding obligation to hand on.
- FIXING `utwr6y`'s APPARENT PARTIAL COMPLETION (F-13). Reported to the maintainer; it belongs to another item and another agent may hold it. CARRIER AT EXECUTION: closed as an obligation, because `utwr6y` reached `superseded` on 2026-09-10 and its one live piece was carried forward to backlog `rcmbnb`; there is nothing left here to hand on.
  - Carrier: rcmbnb

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
- THE E-03 CORPUS PROPERTY IN BOTH DIRECTIONS, since a one-directional demonstration is what let the unfalsifiable version look acceptable: pasted FAILING against a synthetic record that reaches `NEGATIVE` with no `REJECT` token (a no-verdict-token record carrying a negative readiness), and pasted PASSING against the real corpus including at least one legitimately REJECTed plan. A V-03 that shows only the passing direction has not distinguished the built property from the tautology that was rejected.
- THE EXPLICIT STATEMENT THAT THE TOKEN PROPERTY WAS REJECTED AS UNFALSIFIABLE, with the reason, so a later author does not reintroduce it from the backlog item, which still recommends it.
- NEGATIVE PROOF THAT NOTHING ELSE MOVED: `git status --porcelain .aw/records/plans/` clean, and `git diff --stat` showing `tests/test_plan_readiness.py` as the only changed file.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set. THREE BASELINES HAVE BEEN RECORDED FOR THIS PLAN AND ALL ARE STALE (briefing `1 failed, 5648 passed`; plan `5859 passed`; review HEAD `72d1b018` measures `1 failed, 5958 passed, 3 skipped, 2 xfailed`, the failure being `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, which walks another party's gitignored `opencode-recovery/`). State what YOU observe. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count. Do NOT delete, move, or modify `opencode-recovery/` to green the suite.
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC CHANGE, and no `.spec.md` path is declared. This plan changes a TEST's assertion, not a contract: the approval gate's behavior is unchanged, `plan_readiness.newest_verdict` is unchanged, and no artifact's meaning moves. An executor who finds a spec constraining what this test must assert should STOP and report rather than editing either.

THE DOCSTRINGS ARE THE DOCUMENTATION HERE, and E-02 must treat them as deliverables rather than incidentals. Two things must be written down where the next reader will hit them: that the check is against NAMED plans whose verdict polarity is known, and WHY the whole-tree form was wrong (a legitimately REJECTed pending plan is a correct state, so "no pending plan is refused" is false whenever the gate works). Without the second sentence, someone restores the tree-wide assertion in good faith.

RECORD THE THIRD-INSTANCE ARGUMENT IN E-04's DECISION, not only in this plan. `tests/test_orchestrator_retirement.py:891-901` already carries the reasoning for its own instance; the class-level observation (three instances, one fixed, one here, one owned by `utwr6y`) is durable knowledge that belongs in whatever follow-up E-04 files, so it is not re-derived a fourth time.

## Open questions

### OQ-01: Should a whole-corpus property exist at all after this fix?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AT REVIEW 2026-09-10 BY MEASUREMENT: YES, ONE MUST EXIST, and it is not the one the plan proposed. This was posed as a cost/benefit judgement for the maintainer, but two measurements settle it from repository evidence, so it is resolved rather than escalated.
  WHY YES. The assertion being removed reads all 104 pending plans and parses each one's newest review record. Answering "no" would leave E-02's handful of pinned ids as the only real-corpus coverage, which contradicts the class's own stated premise that "a fixture-only suite can pass while the gate misjudges reality" (`tests/test_plan_readiness.py:770`) and would make this plan a net loss (F-14). The cost objection is real but small and was overstated: reading 104 files of a few KB each is already what the current test does on every suite run, and the module completes in 0.24s.
  WHY NOT THE PROPOSED FORMULATION. "No plan whose newest review record contains an APPROVING verdict token is refused" is UNFALSIFIABLE (F-15): `newest_verdict` derives its polarity by calling `classify_verdict` on that record and returning the result, so the property compares a function to its own internal call and cannot fail for any input. Its clean pass over 608 plans is a consequence of its form, not evidence about the gate.
  WHAT TO BUILD INSTEAD, verified falsifiable at review (F-16): every plan whose newest review record parses `NEGATIVE` must have a record literally containing `REJECT`. It can fail, because `newest_verdict` reaches `NEGATIVE` by a second route (no verdict token plus a negative readiness token), and a record taking that route contains no `REJECT`. It survives a legitimate REJECT by construction, since a properly rejected plan contains the token. And its failure mode is the exact false-refusal class the test was written for: a reviewer who records a readiness but omits the verdict token is silently refused by the gate.
  E-03 IS THEREFORE A BUILD, NOT A DECISION. Recording "no" is no longer an acceptable outcome, and the plan's permission to do so is withdrawn.

### OQ-02: Does the class deserve a general guard?

- Blocking: no
- Status: resolved
- Owner: none
- Carrier: jb0sc1
- Resolution or deferral rationale: RESOLVED AT EXECUTION 2026-09-20: YES, IT DESERVES ONE, AND IT IS NOW BUILDABLE WHERE IT WAS NOT. This was left open on the judgement that a detector for "test reads live repo state" would forbid the DELIBERATE and valuable cases along with the bad, and that judgement was correct WHEN IT WAS MADE. It was overtaken by commit `7b9f3ae2` (2026-09-19), which added the `livecorpus` pytest marker; `pyproject.toml:170` deselects it by default and `:157` defines it as exactly this hazard. That supplies the discriminator the question lacked: a guard need not judge whether a live-corpus read is GOOD, only whether it is DECLARED, which is mechanically checkable. The deliberate cases declare themselves and pass; an undeclared one is flagged. THE ANSWER IS STILL NOT "BUILD IT HERE", for the plan's own reason (a cross-cutting mechanism is not this fence's work) and for one `utwr6y` established: a source-level grep is evadable through a helper, so the implementation choice (AST or import-time) is a real decision someone must make deliberately. FILED as backlog `jb0sc1` with the four known instances, the measured six unmarked call sites, the tractable guard shape, and that caveat. The prior rationale is preserved below because it records why the answer changed.
  PRIOR RATIONALE, SUPERSEDED: OPEN AND ASSIGNED TO E-04 AS A RECORDED DECISION, NOT A BUILD. The argument for is that the class has produced three known instances, one of them red for days. The arguments against are specific rather than lazy: a detector for "test reads live repo state" would flag the DELIBERATE and valuable cases in this very class, `utwr6y` E-03 already establishes that the obvious implementation (a grep over test source) is unsound because "it would pass while an implicit `dir='.'` still reached the live tree", and `utwr6y` E-04 is already producing an inventory scoped explicitly to REPORT and NOT FIX. So the cheapest correct next step is to let that inventory land and then decide with data. E-04 therefore records the decision and files a follow-up if wanted; non-blocking because this plan's fix stands either way.

### OQ-03: Which plans should the rewritten test pin?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED AS A RULE RATHER THAN A LIST, because a hardcoded list authored today would itself age. The rule: pin plans whose newest review record's polarity is KNOWN AND POSITIVE, resolved by id6 across all five dispositions through the existing `_find`, with the reason each polarity is known recorded beside the id6. That is exactly what the sibling `test_the_three_item_13_successors_are_not_refused` does with `6lu3rq`/`m73aet`/`wlxkoz`, all three verified in `executed/` at review, and its own docstring notes two of them moved out of `pending/` without breaking it, which is the proof the pattern survives corpus drift. Deliberately NOT pinned: any plan chosen because it is currently PENDING, since pending membership is the mutable fact that caused this bug. E-02 selects the concrete ids and records the justification; the rule, not the list, is what a reviewer should check.
  ONE NECESSARY ADDITION FROM REVIEW (F-17): "KNOWN AND POSITIVE" MUST MEAN MEASURED POSITIVE, NOT MERELY NOT-NEGATIVE. Measured at review, 19 of the 104 pending plans parse to polarity `None`, and the sibling's assertion is `assertNotEqual(polarity, NEGATIVE)`, which passes trivially for `None`. So an id6 picked without measuring could satisfy the test while asserting nothing at all, reproducing the vacuous-pass defect this class treats as a bug. E-02 must record the polarity it MEASURED for each pinned id, and must not pin a `None`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the ACTUAL failing output against the synthetic REJECTed plan, showing the assertion naming it. Paste the current live-tree run (`python3 -m pytest tests/test_plan_readiness.py -o addopts=""`) with its summary line, so the record states plainly that the failure is latent. Paste `git status --porcelain .aw/records/plans/` proving no real plan was created, moved or edited to manufacture it.
  - Observed evidence: PASS. The defect was manufactured on a fixture and shown FAILING, the current live-tree green is pasted, and no real plan was created, moved or edited.
    THE WORLD MOVED AGAIN BETWEEN REVIEW AND EXECUTION, AND THAT IS THE FIRST THING TO RECORD. The plan and its review both describe an UNMARKED whole-tree assertion. At execution HEAD `ad353b15` it carries `@pytest.mark.livecorpus` (added 2026-09-19 in commit `7b9f3ae2`, "test(livecorpus): stop a whole-corpus canary from blocking every lane's integration"), and `pyproject.toml:170` deselects that marker by default (`-m 'not slow and not livecorpus'`). So the defect was MITIGATED, not fixed: the false-by-construction assertion is byte-for-byte intact, it is simply no longer collected in a default run. The plan's fourth baseline (`1 failed, 5958 passed`, the failure being `test_reporting_contract.py` walking another party's `opencode-recovery/`) is therefore ALSO stale; see V-05 for the fifth, measured here. That mitigation is WHY the E-04 decision changed from "record and file" to "record, and file a follow-up naming the now-tractable guard shape": the marker is the discriminator the review's OQ-02 said did not exist.
    THE DEFECT MANUFACTURED ON A FIXTURE, exactly as E-01 requires. Method: a temp directory of SYMLINKS to all 102 real pending plans plus ONE synthetic plan whose newest review record is a legitimate `/plan-review REJECT - NEEDS REPLAN; readiness NO-GO`, with the test module's `PENDING_DIR` pointed at it and the SHIPPED test body called unmodified. Nothing under `.aw/records/plans/` was created, moved, or edited.

    ```
    FAIL: test_the_shipped_assertion_fails_on_one_legitimately_rejected_pending_plan
    ----------------------------------------------------------------------
    Traceback (most recent call last):
      File ".../e01_repro.py", line 53, in test_the_shipped_assertion_fails_on_one_legitimately_rejected_pending_plan
        case.test_no_pending_plan_is_refused_on_a_verdict_today()
      File ".../tests/test_plan_readiness.py", line 1703, in test_no_pending_plan_is_refused_on_a_verdict_today
        self.assertEqual(refused, [], "pending plans falsely refused on their verdict")
    AssertionError: Lists differ: ['20260907-replanme-01-zzz999-a-legitimately-rejected-plan.ipd.md'] != []

    First list contains 1 additional elements.
    First extra element 0:
    '20260907-replanme-01-zzz999-a-legitimately-rejected-plan.ipd.md'

    - ['20260907-replanme-01-zzz999-a-legitimately-rejected-plan.ipd.md']
    + [] : pending plans falsely refused on their verdict

    Ran 1 test in 0.047s

    FAILED (failures=1)
    ```

    It names the synthetic plan exactly as it would have named `32ij2j`. The defect is confirmed false-by-construction: the ONLY thing wrong with that plan is that it was legitimately rejected and is awaiting replan, which is a correct occupant of `pending/`.
    THE CURRENT GREEN, so the record is honest that the failure is LATENT, both with the default marker filter and with it cleared:

    ```
    $ python3 -m pytest tests/test_plan_readiness.py -o addopts=""
    32 passed in 0.61s

    $ python3 -m pytest tests/test_plan_readiness.py -o addopts="-m ''"
    32 passed in 0.46s
    ```

    THE MEASURED `NEGATIVE` CENSUS AT EXECUTION HEAD, which is why it is vacuous rather than merely passing: ZERO of the 102 pending plans parse `NEGATIVE` (`pending 102 {'neutral': 19, 'positive': 73, None: 10}`). Across all five dispositions, 694 plans, exactly 7 parse `NEGATIVE` and all 7 sit in `superseded/`, including `32ij2j` whose REJECT record is intact. Note the plan's counts also drifted: 102 pending not 104, and 10 `None`-polarity not 19.
    NEGATIVE PROOF THAT NO REAL PLAN WAS TOUCHED TO MANUFACTURE IT:

    ```
    $ git status --porcelain .aw/records/plans/
    $
    ```

    Empty at the time of manufacture and still empty until the lifecycle transition below.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the rewritten test in full. Quote the pinned id6 tuple and, for each id6, paste the polarity you MEASURED (not merely asserted to be known) together with the disposition directory it resolved from. Confirm NO pinned id has polarity `None`, since `assertNotEqual(polarity, NEGATIVE)` passes trivially for `None` and 19 of 104 pending plans parse that way (F-17). Show it calls the existing `_find` rather than a new helper. Paste the reworded docstring and confirm it states WHY the whole-tree form was wrong, not merely what the new form does.
  - Observed evidence: PASS. The whole-tree glob is gone, four terminal id6s are pinned with MEASURED positive polarity, `_find` is reused, and the docstring states why the old form was wrong.
    THE REWRITTEN TEST IN FULL, `tests/test_plan_readiness.py`, replacing `test_no_pending_plan_is_refused_on_a_verdict_today`:

    ```python
    KNOWN_POSITIVE = (
        ("fn2l1u", "executed", "an APPROVE whose prose contains `REJECT`"),
        ("8lfoum", "executed", "an attestation narrating a CLEARED `no-go` and containing `REJECT`"),
        ("btot17", "executed", "an APPROVE narrating a superseded `no-go`"),
        ("920qnm", "executed", "a PARENTHESIZED actor, the fn2l1u fail-open shape"),
    )

    def test_named_plans_whose_verdict_is_known_positive_are_not_refused(self):
        """A gate that refuses live, legitimately-reviewed plans is a lockout, not a safeguard.

        THE CHECK IS AGAINST NAMED PLANS WHOSE VERDICT POLARITY IS KNOWN, and the reason is that the
        form this replaced was FALSE BY CONSTRUCTION. It globbed the whole live `pending/` tree and
        asserted that NO plan there carried a negative verdict. But a plan that `/plan-review`
        legitimately REJECTED and that is awaiting its replan is a CORRECT thing for `pending/` to
        contain, so "no pending plan is refused" is false exactly when the gate is WORKING. It could
        not distinguish a FALSE refusal (the parser misreading an approval) from a TRUE one (a real
        rejection), which is the only thing this test is named for. Measured: it went red on `32ij2j`
        after that plan's own legitimate `REJECT - NEEDS REPLAN` verdict, and review records across
        the tree spend paragraphs re-establishing that the red is nobody's fault. DO NOT RESTORE IT.

        The ids and their measured polarities are in `KNOWN_POSITIVE` above, each with the hazard it
        pins. `_find` resolves them across all five dispositions, and the counter below refuses to
        pass vacuously if they are ever all deleted.
        """
        checked = 0
        for id6, disposition, why in self.KNOWN_POSITIVE:
            path = self._find(id6)
            polarity, entry = PR.newest_verdict(path.read_text(encoding="utf-8"))
            # assertEqual, NOT assertNotEqual(NEGATIVE): the looser form also passes for `None`
            # (no readable verdict), so it would report coverage it does not have.
            self.assertEqual(
                polarity,
                PR.POSITIVE,
                f"{id6} ({why}, measured positive in {disposition}/) now reads {polarity!r}; "
                f"record: {entry[:200]}",
            )
            checked += 1
        if checked == 0:
            self.skipTest("none of the pinned known-positive plans remain in any disposition")
        self.assertEqual(checked, len(self.KNOWN_POSITIVE))
    ```

    (The in-file comment block above `KNOWN_POSITIVE`, not repeated here, records the measured `None`-polarity population and the reason every pin sits in a terminal disposition.)
    THE PINNED TUPLE IS `("fn2l1u", "8lfoum", "btot17", "920qnm")`, AND EACH POLARITY WAS MEASURED ON 2026-09-20 BY CALLING `PR.newest_verdict` ON THE RESOLVED FILE, not assumed:

    ```
    pin fn2l1u: executed/ measured polarity=positive | an APPROVE whose prose contains `REJECT`
    pin 8lfoum: executed/ measured polarity=positive | an attestation narrating a CLEARED `no-go` and containing `REJECT`
    pin btot17: executed/ measured polarity=positive | an APPROVE narrating a superseded `no-go`
    pin 920qnm: executed/ measured polarity=positive | a PARENTHESIZED actor, the fn2l1u fail-open shape
    test_named_plans_whose_verdict_is_known_positive_are_not_refused checked counter = 4
    ```

    NO PINNED ID HAS POLARITY `None`: all four measure `positive`. The measured token content, which is what makes each a real hazard rather than a convenient pick: `fn2l1u` REJECT=True no-go=False; `8lfoum` REJECT=True no-go=True; `btot17` REJECT=False no-go=True; `920qnm` REJECT=False no-go=False with a parenthesized actor `trimmed scope) (opencode its_direct/pt3-claude-opus-4.8-1m-us`. Every one is a record that a naive negative-token scan would refuse and that the real parser correctly approves, which is precisely the FALSE-refusal direction.
    F-17'S TRAP IS CLOSED MORE STRONGLY THAN THE PLAN ASKED. The plan required "do not pin a `None`"; the assertion is `assertEqual(polarity, PR.POSITIVE)`, not the sibling's `assertNotEqual(polarity, NEGATIVE)`, so a pin drifting to `None` FAILS instead of passing quietly. That matters because the sibling `test_the_three_item_13_successors_are_not_refused` is measurably in that weakened state right now: all three of its ids (`6lu3rq`, `m73aet`, `wlxkoz`) measure polarity `None`, so it currently asserts nothing (reported in V-05 and as a defect-report finding, NOT fixed here since it is outside this plan's fence).
    IT CALLS THE EXISTING `_find`, adding no helper: `path = self._find(id6)`, resolving across `pending`/`executed`/`superseded`/`not-executed`/`reusable` and skipping honestly when absent.
    THE DOCSTRING STATES WHY THE OLD FORM WAS WRONG, not merely what the new one does: "a plan that `/plan-review` legitimately REJECTED and that is awaiting its replan is a CORRECT thing for `pending/` to contain, so 'no pending plan is refused' is false exactly when the gate is WORKING", plus the explicit "DO NOT RESTORE IT".
    THE HONEST-SKIP PATH IS DEMONSTRATED, not assumed, by resolving against an empty fixture tree: `[honest skip, E-02 pins] SkipTest: plan fn2l1u not present in any disposition`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the property's code, and paste it BOTH FAILING and PASSING. FAILING against a synthetic record that reaches `NEGATIVE` with no `REJECT` token (the no-verdict-token plus negative-readiness route, `plan_readiness.py:417-420`), which is what proves it is falsifiable at all. PASSING against the real corpus including at least one legitimately REJECTed plan, with the count of `NEGATIVE`-parsing plans you measured stated.
    STATE EXPLICITLY THAT THE ORIGINALLY PROPOSED TOKEN PROPERTY WAS REJECTED AND WHY, naming `plan_readiness.py:414-416` as the reason it cannot fail. A V-03 that pastes only a passing run, or that ships the token property, is a FAILED validation: the whole point of this item after review is that a green test is not evidence unless it could have been red.
    Confirm the property counts what it checked and skips honestly rather than passing vacuously on an empty or unreadable corpus.
  - Observed evidence: PASS. The falsifiable `NEGATIVE`-implies-`REJECT` property is shipped and shown FAILING then PASSING; the unfalsifiable token property was rejected and is recorded as such in the code.
    THE PROPERTY'S CODE, `tests/test_plan_readiness.py`, marked `livecorpus` for the reason that marker now exists:

    ```python
    @pytest.mark.livecorpus
    def test_every_negative_verdict_in_the_corpus_states_the_reject_token(self):
        """Plan h3bjue E-03: the whole-corpus property, chosen because it CAN FAIL.

        THE PROPERTY: every plan whose newest review record parses as `NEGATIVE` must have a record
        that literally contains `REJECT`.
        ...
        """
        plans_root = REPO_ROOT / ".aw" / "records" / "plans"
        checked = 0
        silent = []
        for name in ("pending", "executed", "superseded", "not-executed", "reusable"):
            directory = plans_root / name
            if not directory.is_dir():
                continue
            for path in sorted(directory.glob("*.ipd.md")):
                polarity, entry = PR.newest_verdict(path.read_text(encoding="utf-8"))
                if polarity != PR.NEGATIVE:
                    continue
                checked += 1
                if "REJECT" not in entry:
                    silent.append(f"{name}/{path.name}: {entry[:200]}")
        if checked == 0:
            self.skipTest("no plan in any disposition currently parses as NEGATIVE")
        self.assertEqual(
            silent,
            [],
            f"{len(silent)} of {checked} refused plans state NO `REJECT` token, so each was refused "
            "on its READINESS alone. That is a silent lockout: the gate's refusal has no override, "
            "and the review record its author wrote states no rejection at all. FIX: read the named "
            "records; either the reviewer omitted the verdict token they meant to state, or "
            "`negative_readiness_asserted` is matching a token inside a clause that CLEARS it, which "
            "is the 2026-09-19 incident returning.\n" + "\n".join(silent),
        )
    ```

    DIRECTION 1, FAILING, which is what proves it falsifiable at all. A synthetic record taking the no-verdict-token plus asserted-negative-readiness route, symlinked into a temp copy of the full corpus. Precondition measured first, so the route is confirmed rather than hoped for:

    ```
    [precondition] synthetic polarity='negative'  'REJECT' in record=False

    FAIL: test_a_negative_record_with_no_reject_token_fails_the_property
    ----------------------------------------------------------------------
      File ".../tests/test_plan_readiness.py", line 1787, in test_every_negative_verdict_in_the_corpus_states_the_reject_token
        self.assertEqual(
    AssertionError: Lists differ: ['pending/20260920-silent-01-yyy888-refuse[136 chars]ed.'] != []

    First extra element 0:
    'pending/20260920-silent-01-yyy888-refused-on-readiness-alone.ipd.md: - 2026-09-20 reviewed (opencode/m): round 1 complete; readiness no-go until the blocking question is answered.'
    : 1 of 8 refused plans state NO `REJECT` token, so each was refused on its READINESS alone. ...
    ```

    The synthetic record is `- 2026-09-20 reviewed (opencode/m): round 1 complete; readiness no-go until the blocking question is answered.` It states NO verdict token, so `classify_verdict` returns `None` and the asserted-readiness branch decides, returning `negative` with no `REJECT` present. Confirmed directly: `PR.newest_verdict(txt)` -> `('negative', '- 2026-09-20 reviewed (opencode/m): round 1 complete; readiness no-go ...')`, `REJECT in entry: False`.
    DIRECTION 2, PASSING against the real corpus, INCLUDING at least one legitimately REJECTed plan. 7 plans across the 694 in five dispositions parse `NEGATIVE`, all 7 in `superseded/`, and all 7 contain `REJECT`:

    ```
    superseded 20260823-ipdfidelity-01-39fz2x-...ipd.md REJECT-in-entry: True
    superseded 20260830-detrun-01-bmh754-...ipd.md      REJECT-in-entry: True
    superseded 20260830-detrun-02-a54m79-...ipd.md      REJECT-in-entry: True
    superseded 20260830-detrun-03-kaygwo-...ipd.md      REJECT-in-entry: True
    superseded 20260830-detrun-04-k7o7el-...ipd.md      REJECT-in-entry: True
    superseded 20260830-detrun-05-7f7782-...ipd.md      REJECT-in-entry: True
    superseded 20260906-integearn-01-32ij2j-...ipd.md   REJECT-in-entry: True
    total negative 7

    $ python3 -m pytest tests/test_plan_readiness.py::ApprovalGateRealCorpusTests -o addopts="-m ''" -v
    tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_named_plans_whose_verdict_is_known_positive_are_not_refused PASSED
    tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_every_negative_verdict_in_the_corpus_states_the_reject_token PASSED
    tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_the_incident_plans_are_refused PASSED
    tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_the_three_item_13_successors_are_not_refused PASSED
    4 passed in 0.33s
    ```

    THAT COUNT MATCHES THE REVIEW'S MEASUREMENT EXACTLY (7 of 608 then, 7 of 694 now), so the property's baseline was reproduced rather than trusted. The seventh row IS `32ij2j`, the plan whose legitimate REJECT reddened the removed assertion. It now SATISFIES this property instead of violating it, which is the whole point.
    THE ORIGINALLY PROPOSED TOKEN PROPERTY WAS REJECTED AS UNFALSIFIABLE AND WAS NOT SHIPPED. "No plan whose newest review record contains an APPROVING verdict token is refused" compares a function to its own internal call: `newest_verdict` computes `_, polarity = classify_verdict(message)` and returns that value (`agent_workflows/plan_readiness.py:482`, the `:414-416` of the review's HEAD), so the antecedent and the consequent are one line of code. It cannot fail for any input, and its clean pass over the corpus is a consequence of its FORM, not evidence about the gate. The rejection and its reason are recorded in the shipped docstring so nobody reintroduces it from backlog `yw6759`, which still recommends it.
    IT COUNTS WHAT IT CHECKED AND SKIPS HONESTLY, demonstrated rather than asserted, by running it against an empty fixture tree: `[honest skip, E-03 property] SkipTest: no plan in any disposition currently parses as NEGATIVE`. On the real corpus its counter is 7.
    ONE DEVIATION FROM THE PLAN'S LETTER, STATED PLAINLY: the property carries `@pytest.mark.livecorpus`, which the plan did not ask for because the marker did not exist when it was written. It is applied because the marker's own definition in `pyproject.toml:157` describes exactly this test ("asserts a property over EVERY artifact in this repository's own .aw/records/ tree, so ANY agent writing a plan can turn it red"), and omitting it would re-create the lane-blocking failure mode that commit `7b9f3ae2` was written to stop. Consequence, and the honest cost: the property runs in `make test-all`, in release-review, and under `-m ''`, NOT in a default bare run. The E-02 named-id6 test is deliberately UNMARKED and does run by default, since four pinned terminal plans cannot be reddened by a third party authoring a plan.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: state the recorded decision on a class-wide guard, citing all three known instances by test name and file. Confirm in one sentence that `utwr6y`'s E-03 file and E-04 sweep were checked and are not duplicated. If a follow-up was filed, paste its id and summary; if not, state why the inventory should land first.
  - Observed evidence: PASS. The decision is to file rather than build, and the follow-up `jb0sc1` is filed carrying all four instances and the now-tractable guard shape.
    THE DECISION: DO NOT BUILD A GUARD HERE; FILE IT, AND FILE IT WITH THE SHAPE THAT IS NOW TRACTABLE. The plan's own default was "record and file, not build", and that holds. What CHANGED between review and execution is the reason a guard is worth filing at all: OQ-02 argued a guard was intractable because a detector for "test reads live repo state" would forbid the DELIBERATE and valuable cases along with the bad. Commit `7b9f3ae2` (2026-09-19) then added the `livecorpus` pytest marker and `pyproject.toml:170` deselects it by default. That supplies the missing discriminator: a guard no longer has to judge whether a live-corpus read is GOOD, only whether it is DECLARED. So the follow-up asks for "every live-corpus read is either marked `livecorpus` or allowlisted", which is checkable, rather than "no test reads the live corpus", which is wrong.
    THE THREE KNOWN INSTANCES THE PLAN NAMED, all cited by test name and file, plus a fourth measured here:
    (1) `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today` - the false-by-construction whole-tree assertion, REPLACED by this plan's E-02/E-03 pair.
    (2) `tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows` - asserted `{"kgpptv": "reviewed"}` against the live corpus, red for days, DELIBERATELY rewritten to `test_runprofile_is_not_refused_for_unauthored_rows` in commit `31169afd`; verified still present at `tests/test_orchestrator_retirement.py` with the docstring reasoning the plan quotes ("pinned a transient repository state rather than the behavior this test is named for").
    (3) `tests/test_run_viewer.py`'s dependence on the GITIGNORED `.aw/records/runs/` tree - fixed by plan `xbwq8n`; its missing guard is already tracked as backlog `rcmbnb`.
    (4) FOUND HERE, by sweeping every `tests/test_*.py` for a `glob`/`rglob`/`iterdir` over the live records tree: SIX call sites in four modules read the live plan corpus and carry NO `livecorpus` marker - `tests/test_plan_readiness.py:350` `test_every_pending_plan_yields_a_real_history_record`, `tests/test_ipd_lint.py:730` `test_every_readiness_carrying_plan_in_the_tree_is_attested`, `tests/test_ipd_lint.py:1084` `test_real_executed_plan_at_post_transition`, `tests/test_ipd_schema.py:2978` `test_executed_conforming_corpus_low_overfire_rate`, `tests/test_cli_find.py:447` `test_a_setid_query_excludes_prefix_sharing_foreign_sets`, `tests/test_cli_find.py:474` `test_an_id6_query_returns_the_declaring_artifact_not_its_citers`. Each is legitimate and valuable; none is touched here.
    `utwr6y` WAS CHECKED AND IS NOT DUPLICATED, AND ITS STATUS HAS CHANGED SINCE THE PLAN WAS WRITTEN: it is now `superseded` (retired 2026-09-10 because `xbwq8n` converted the 14 live-tree cases on 2026-09-08), its E-03 file `tests/test_run_viewer_isolation.py` still does not exist, and its E-04 sweep was completed by hand inside the retirement note; the surviving guard gap was carried forward as backlog `rcmbnb` (`open`, `low`, `chore`), which the new item cites rather than reimplementing, and nothing here touches `tests/test_run_viewer.py`.
    THE FOLLOW-UP FILED: `jb0sc1` - "Six live-corpus tests carry no livecorpus marker, so a third party's artifact can still red a lane's suite" (`.aw/records/backlog/open/20260920-livecorpusguard-01-jb0sc1-livecorpus-marker-guard.backlog.md`, Set `livecorpusguard`, `open`, `low`, `chore`). It carries all four instances, the measured six-call-site sweep, the now-tractable guard shape, and `utwr6y` E-03's warning that a source-level grep is evadable via a helper, so the class-level knowledge is durable and is not re-derived a fifth time.
    F-13 IS UPDATED RATHER THAN LEFT STALE: it noted `utwr6y` as `to-review` and apparently partly satisfied. It is now `superseded`, so the item it was reported against is closed; no action was taken on it here, as the plan directs.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `tests/test_plan_readiness.py`'s own summary line showing both siblings green, and paste evidence the incident-plans counter was NONZERO (so it did not pass vacuously). Paste the honest-skip path exercised at least once. Paste `git status --porcelain .aw/records/plans/` clean and `git diff --stat` showing only the test file changed.
    THEN paste the BARE `python3 -m pytest` summaries before and after and state the failure-set delta as a set, with the counts you actually observed rather than any quoted baseline (three have been recorded for this plan and all are stale, F-18). If the pre-existing `tests/test_reporting_contract.py` failure appears, report it as pre-existing and CONFIRM you did not delete, move, or modify `opencode-recovery/`.
    ALSO STATE THE NET COVERAGE POSITION IN ONE SENTENCE: how many real review records the module parses after this change versus the 104 it parsed before. That is the number a reader needs to judge whether this plan repaired the proxy or removed the value (F-14), and it is the single clearest summary of whether E-02 and E-03 together did their job.
  - Observed evidence: PASS. Both siblings green with nonzero counters, honest skips demonstrated, no plan or review record edited, bare-suite failure delta EMPTY, and coverage rose from 102 records to 694.
    THE MODULE'S OWN SUMMARY LINE, BOTH SIBLINGS GREEN, with the marker filter cleared so the new `livecorpus` property is collected too:

    ```
    $ python3 -m pytest tests/test_plan_readiness.py -o addopts="-m ''"
    33 passed in 0.49s
    ```

    (32 before, 33 after: E-02 replaced one test in place and E-03 added one.)
    THE INCIDENT-PLANS COUNTER IS NONZERO, recomputed directly rather than inferred from a green dot, so the sibling is proven non-vacuous:

    ```
      incident bmh754: polarity=negative REJECT_in_entry=True
      incident a54m79: polarity=negative REJECT_in_entry=True
      incident kaygwo: polarity=negative REJECT_in_entry=True
      incident k7o7el: polarity=negative REJECT_in_entry=True
      incident 7f7782: polarity=negative REJECT_in_entry=True
    test_the_incident_plans_are_refused checked counter = 5
    ```

    All five still resolve from `superseded/`. The new tests' counters are likewise nonzero: E-02 `checked counter = 4` (all four pins resolved, no skip), E-03 `checked counter = 7`.
    THE OTHER SIBLING IS GREEN BUT IS MEASURABLY VACUOUS, AND I AM REPORTING IT RATHER THAN FIXING IT. `test_the_three_item_13_successors_are_not_refused` resolves all three ids, so it does not skip, but every one now parses `None`:

    ```
      successor 6lu3rq: executed/ polarity=None
      successor m73aet: executed/ polarity=None
      successor wlxkoz: executed/ polarity=None
    test_the_three_item_13_successors_are_not_refused resolved = 3
    ```

    Its assertion is `assertNotEqual(polarity, PR.NEGATIVE)`, which passes trivially for `None`, so it currently asserts nothing about three plans it names. That is F-17's exact defect in the test this plan was told to COPY. I did not change it: it is outside `Scope-Paths`' intent for this fence (the plan's under-scope statement is explicit that only the one method is rewritten) and tightening it to `assertEqual(POSITIVE)` would fail, since the cause is that all three records are `aw set`/split narrations stating no verdict token at all. It is filed as a defect-report finding and as backlog `nz5cl2` (`vacuouspin`, `bug`, `medium`, `Blocks-Release: next` under the all-bugs-block-release rule). The new E-02 test deliberately does NOT inherit the weakness: it asserts `assertEqual(polarity, PR.POSITIVE)`.
    THE HONEST-SKIP PATH EXERCISED, both new tests, against an empty fixture tree:

    ```
    [honest skip, E-02 pins] SkipTest: plan fn2l1u not present in any disposition
    [honest skip, E-03 property] SkipTest: no plan in any disposition currently parses as NEGATIVE
    ```

    NOTHING ELSE MOVED. `git status --porcelain .aw/records/plans/` was EMPTY throughout execution (checked before the baseline run, after the AFTER run, and before staging; it becomes non-empty only for THIS plan file at the lifecycle transition below), and no plan or review record was edited to make any test pass. `32ij2j` is untouched: it remains in `superseded/` with its `REJECT - NEEDS REPLAN` record intact, and the E-03 property now counts it as a PASSING row.

    ```
    $ git diff --stat
     tests/test_plan_readiness.py | 143 +++++++++++++++++++++++++++++++++++--------
     1 file changed, 118 insertions(+), 25 deletions(-)
    ```

    One source file changed, as declared. The only other new path is the E-04 follow-up backlog item `jb0sc1`, which E-04 required.
    THE BARE SUITE, BEFORE AND AFTER, MEASURED HERE. The plan records three baselines and its review a fourth; ALL FOUR ARE STALE, so the BEFORE was measured in this lane by restoring `tests/test_plan_readiness.py` to `git show HEAD:` and parking the new backlog item outside the records tree, then restoring both. Both runs are bare `python3 -m pytest`, no added flags:

    ```
    BEFORE (HEAD ad353b15, my changes reverted):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7206 passed, 3 skipped, 2 xfailed, 3 warnings in 186.68s (0:03:06)

    AFTER (my changes applied):
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 7207 passed, 3 skipped, 2 xfailed, 3 warnings in 169.40s (0:02:49)
    ```

    FAILURE-SET DELTA: AFTER minus BEFORE = {} (EMPTY). Both sets are the single node `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`, which is PRE-EXISTING and not this plan's: it asserts a non-isolated turn gets no denial policy, and this lane IS an isolated worktree carrying `AW_PIN_KEEP_ROOT`, so the environment the test asserts about is the lane itself. It touches no file this plan changed. Passed count rises by exactly 1, which is the E-03 test.
    THE PLAN'S NAMED PRE-EXISTING FAILURE DID NOT APPEAR: `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose` PASSES here, and there is no `opencode-recovery/` directory in this lane. I did NOT delete, move, or modify `opencode-recovery/` or any other party's data; nothing outside my two paths was touched. This is the FIFTH distinct baseline recorded for this plan, which is itself the argument for the plan's "state what you observe" instruction.
    THE `livecorpus` SUBSET WAS RUN SEPARATELY, since a default bare run deselects it and would otherwise never execute the new property: `python3 -m pytest -o addopts="-q -n auto --dist=worksteal -m 'livecorpus'"` -> `1 passed in 16.36s`.
    NET COVERAGE POSITION, IN ONE SENTENCE: the module now parses the newest review record of ALL 694 tracked plans across five dispositions (E-03) plus 4 named terminal plans asserted strictly positive (E-02), against the 102 pending-only records the removed assertion parsed, so coverage rose roughly 6.8x rather than falling to a handful, and F-14's coverage-loss hazard is closed rather than merely acknowledged.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION. OQ-03 (which plans to pin) is resolved as a RULE rather than a list, with a review addition that "known and positive" must mean MEASURED positive. OQ-01 (corpus-wide property) was RESOLVED AT REVIEW from repository evidence rather than left open: one must exist, and it must be the falsifiable `NEGATIVE`-implies-`REJECT` property rather than the unfalsifiable token property the plan and the backlog item proposed. OQ-02 (class-wide guard) remains assigned to E-04 and may legitimately answer "no, and here is why", so the fix lands either way.

THE ONE THING A REVIEWER OR EXECUTOR MUST NOT DO IS SHIP E-02 WITHOUT E-03. Measured at review, the assertion being removed parses 104 real review records on every suite run; E-02 alone replaces that with a handful of pinned ids. The repair is the PAIR: narrow the false assertion, then restore whole-corpus coverage with a property that can actually fail. Either half alone leaves the class worse than it found it (F-14).

A GREEN TEST IS NOT EVIDENCE UNLESS IT COULD HAVE BEEN RED, and this plan exists because that principle was violated once already. It nearly was again: the property both the plan and the backlog item recommend cannot fail for any input (F-15). So every new assertion this plan adds must be demonstrated FAILING before it is demonstrated passing. That is why E-01 manufactures the defect and why V-03 demands both directions.

IT CARRIES `Blocks-Release: next`, inherited from backlog `yw6759` under the all-bugs-block-release rule, resolving to release `f33nrj` (the single `planned` record, verified at review). A REVIEWER SHOULD WEIGH THAT DELIBERATELY, because the failure is currently LATENT (F-4): the suite is green today only because the rejected plan moved out of `pending/`, and re-measured at review ZERO of the 104 pending plans parse `NEGATIVE`, so the assertion is vacuously true rather than merely passing. The case for keeping the gate is that recurrence is a matter of when rather than whether (any future `/plan-review` REJECT on a pending plan reds the suite for everyone) and the fix is small; the case against is that a latent bug need not gate a release. That is the maintainer's call, it is stated rather than assumed, and review did not change it.

THE ONE TEMPTING WRONG FIX IS NAMED EXPLICITLY. Do not edit `32ij2j`, and do not edit any review record, to make a test pass. That would forge review evidence, which is exactly what the approval-gate machinery exists to prevent.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. Manufacture the failure on a FIXTURE: 104 plans are pending (re-measured at review; the plan said 92), approved plans are executing in live runs, and other agents are graduating concurrently, so creating or moving a real plan to trigger a test would interfere with other runs. Do NOT delete, move, or modify the gitignored `opencode-recovery/` directory, which belongs to another party and causes the one pre-existing suite failure. Re-locate every symbol by NAME; all the `tests/test_plan_readiness.py` anchors in this plan were verified correct at review HEAD `72d1b018`, but `8v5pwa` (`reviewed`) declares the same file and may move them. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook, since `pre-commit` can leave another agent's paths in the index.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the manufactured failure, the current-green disclosure, the per-id6 polarity justification, and the nonzero sibling counter.
