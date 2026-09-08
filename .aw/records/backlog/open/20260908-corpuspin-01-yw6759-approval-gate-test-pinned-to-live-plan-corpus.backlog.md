- Id: yw6759
- Status: open
- Blocks-Release: next
- Set: corpuspin
- Priority: medium
- Work-Kind: bug
- Summary: test_no_pending_plan_is_refused_on_a_verdict_today asserts no pending plan carries a negative verdict, so a legitimate plan-review REJECT reds the suite: pin named id6s the way its two sibling tests already do

## Workflow history
- 2026-09-08 created (aw backlog): Filed after the maintainer observed that a defect found during a graduation sweep was reported in chat but captured nowhere durable. The gate is correct and the TEST is wrong: 32ij2j legitimately carries a /plan-review REJECT. Second instance of this class in the suite; the first (test_orchestrator_retirement RealRepositorySets) self-healed by corpus drift rather than being fixed. Blocks-Release: next per the all-bugs-block-release rule.

FOUND 2026-09-08 by the maintainer, after a graduation sweep merged nine plans and the bare suite
reported `1 failed, 5661 passed`. The failure was correctly identified as not caused by that sweep,
reported in chat, and then NOT captured anywhere durable. This item is that capture. The maintainer's
rule is that every known issue gets a backlog item or a plan; a chat report is neither.

THE DEFECT. `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_no_pending_plan_is_refused_on_a_verdict_today`
asserts that NO plan in `.aw/records/plans/pending/` carries a negative review verdict:

    refused = [p.name for p in pending
               if PR.newest_verdict(p.read_text(encoding="utf-8"))[0] == PR.NEGATIVE]
    self.assertEqual(refused, [], "pending plans falsely refused on their verdict")

That assertion is FALSE BY CONSTRUCTION as soon as any pending plan is legitimately rejected by
`/plan-review`, which is a normal and desirable event. Measured at HEAD `b392330c`: plan `32ij2j`
(`.aw/records/plans/pending/20260906-integearn-01-32ij2j-...ipd.md`) reads `- Status: reviewed` and its
newest review record begins "/plan-review REJECT - NEEDS REPLAN; readiness NO-GO", so
`PR.newest_verdict` returns `negative`. THE GATE IS WORKING CORRECTLY AND THE TEST IS WRONG.

THE TEST'S OWN INTENT IS SOUND, WHICH IS WHY THIS IS NOT A DELETE. Its docstring says "A gate that
refuses live, legitimately-reviewed plans is a lockout, not a safeguard", and its class docstring says
"a fixture-only suite can pass while the gate misjudges reality". Both are right. The bug is that the
chosen PROXY for "falsely refused" is "any pending plan is refused", which cannot distinguish a FALSE
refusal from a TRUE one. A plan that was genuinely rejected and is awaiting a replan is exactly what
the pending tree should contain.

THE SIBLING TESTS SHOW THE CORRECT PATTERN ALREADY EXISTS IN THE SAME CLASS, so the fix has a local
model rather than needing a design:
  * `test_the_three_item_13_successors_are_not_refused` pins THREE NAMED id6s that must not be refused
    and resolves each by id6 across every disposition directory, with a `skipTest` when a plan is
    absent. It is immune to corpus growth.
  * `test_the_incident_plans_are_refused` pins FIVE NAMED id6s that MUST be refused, counts how many
    it actually checked, and calls `skipTest` when none remain so it "says so rather than lying".
Both encode the same insight: assert on NAMED artifacts whose verdict is known, never on a whole
mutable tree.

WHY THIS MATTERS BEYOND ONE RED TEST. This is the SECOND instance of the same defect class in this
suite, and the first one was live for weeks:
`tests/test_orchestrator_retirement.py::RealRepositorySets::test_runprofile_refuses_for_R2_and_NOT_for_unauthored_rows`
asserted `{"kgpptv": "reviewed"}` against the live plan corpus and failed for days as `kgpptv`
advanced to `approved`; it was the repository's long-standing known baseline failure. Measured
2026-09-08 it now PASSES (112 passed in that module), because the corpus drifted back into agreement by
accident, not because anything was fixed. So the class has produced two failures, one of which
self-healed and can recur at any time.

THE COST IS REAL AND ALREADY PAID SEVERAL TIMES. A test that fails for a legitimate repository state
trains every agent and human to treat a red suite as normal, which is precisely how a genuine
regression gets waved through. It has also polluted plan reviews: at least two review records in this
repository spend paragraphs establishing that a suite failure "is not this plan's", and one review
explicitly disclosed that THE REVIEWER CAUSED the failure by rejecting a sibling plan, which is the
gate working as designed being recorded as collateral damage.

WHAT TO FIX, not prescribed in detail.
  1. Replace the whole-tree assertion with the NAMED-id6 pattern its two siblings already use: a list
     of plans whose verdict polarity is known and asserted, resolved by id6 across dispositions, with
     an honest `skipTest` when a named plan is gone.
  2. If a whole-corpus property is genuinely wanted, it must be a property that survives a legitimate
     REJECT. "No plan is refused" is not such a property. A defensible one: no plan whose newest review
     record contains an APPROVING verdict token is refused, which catches the parser bug the test was
     written to catch without forbidding rejection.
  3. Consider whether the two known instances justify a guard against the class: a test that reads
     `.aw/records/plans/` or `.aw/records/runs/` and asserts on its CONTENT rather than on a fixture is
     the shape to detect. Note pending plan `utwr6y` (`testiso` Order 01) already exists to decouple
     `tests/test_run_viewer.py` from the gitignored runs tree, so a third instance of the same class is
     already being addressed separately; check it before designing a general guard so the two do not
     collide.

DO NOT FIX IT BY EDITING `32ij2j`. Its REJECT verdict is correct and its `- Status: reviewed` is
correct. Changing a plan's review record to make a test pass would forge review evidence, which is the
one thing the approval-gate machinery exists to prevent.

VERIFY BY RUNNING, NOT READING: `python3 -m pytest tests/test_plan_readiness.py -o addopts=""` at HEAD
`b392330c` reproduces the failure naming `32ij2j`, and the fix must keep
`test_the_incident_plans_are_refused` and `test_the_three_item_13_successors_are_not_refused` passing,
since those two pin the gate's real behavior in both directions.
