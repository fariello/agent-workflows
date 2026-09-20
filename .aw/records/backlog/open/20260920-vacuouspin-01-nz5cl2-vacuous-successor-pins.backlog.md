- Id: nz5cl2
- Status: open
- Blocks-Release: next
- Set: vacuouspin
- Priority: medium
- Work-Kind: bug
- Summary: test_the_three_item_13_successors_are_not_refused passes vacuously: all three pinned plans now parse None polarity

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan h3bjue: all three pinned id6s (6lu3rq, m73aet, wlxkoz) measure polarity None at HEAD ad353b15, and assertNotEqual(polarity, NEGATIVE) passes trivially for None, so the test asserts nothing.

FOUND 2026-09-20 while executing plan `h3bjue` (`gatepin` Order 01), which repaired the SIBLING
test in the same class and was told to COPY this one's pattern. Reported rather than fixed: repairing
it is outside that plan's declared fence (its under-scope statement is explicit that only one method
is rewritten), and the repair is not a one-line assertion change; see below.

THE DEFECT. `tests/test_plan_readiness.py::ApprovalGateRealCorpusTests::test_the_three_item_13_successors_are_not_refused`
pins three named id6s and asserts each is not falsely refused:

    for id6 in ("6lu3rq", "m73aet", "wlxkoz"):
        path = self._find(id6)
        polarity, _ = PR.newest_verdict(path.read_text(encoding="utf-8"))
        self.assertNotEqual(polarity, PR.NEGATIVE, f"{id6} falsely refused")

`assertNotEqual(polarity, NEGATIVE)` passes for the `None` polarity, which means "no verdict could be
read at all". Measured at HEAD `ad353b15`, all three plans now parse `None`:

    6lu3rq: executed/ polarity=None
    m73aet: executed/ polarity=None
    wlxkoz: executed/ polarity=None

So the test resolves all three (it does NOT skip, and its author's honest-skip guard therefore never
fires) and asserts NOTHING about any of them. It is green, it names three real plans, and it exercises
no behavior. That is a vacuous pass, which this class explicitly treats as a defect: its neighbour
`test_the_incident_plans_are_refused` carries a checked-counter specifically "so it says so rather
than lying".

WHY IT WENT VACUOUS, which decides the fix. The polarity is `None` because each plan's NEWEST review
record states no verdict token:
  - `6lu3rq` and `m73aet`: `- 2026-08-31 reviewed (aw set): plan-review round 1 complete; revisions
    applied. See .aw/records/reviews/ for the typed findings and decisions.` A terse `aw set` record
    that delegates the verdict to the review file.
  - `wlxkoz`: `- 2026-09-04 reviewed (...): SPLIT PERFORMED at the maintainer's direction, ...` A
    split narration, again stating no verdict token.

This is drift, not breakage: the test was written when those records read differently (the plan's
docstring says their `REJECT` mention belonged to a RETIRED predecessor, which is the thing it was
built to prove is not refused). The records were legitimately superseded by newer ones.

WHY THE OBVIOUS FIX IS WRONG. Tightening the assertion to `assertEqual(polarity, PR.POSITIVE)` (which
is what `h3bjue` did for its own new test) would FAIL for all three, because the cause is not a parser
bug but that the newest records genuinely state no verdict. Options, offered as options and not a
decision:
  (a) Re-pin to three plans whose polarity MEASURES positive and whose records carry the same hazard
      shape the test was written for (a positive verdict whose prose contains `REJECT`); `h3bjue`'s
      new `KNOWN_POSITIVE` tuple already does this for four ids and is the local model.
  (b) Keep the ids and assert the STRONGER, still-true property: that a `REJECT` mention belonging to
      a RETIRED PREDECESSOR anywhere in the plan's history does not produce a refusal, which is the
      behavior the test is named for and which does not depend on the newest record's polarity.
  (c) Add a polarity precondition plus an honest skip, so drift makes it SKIP loudly rather than pass
      silently. Weakest option: it preserves the name without preserving the coverage.

WHY MEDIUM PRIORITY AND NOT LOW. Nothing is broken in shipped behavior, so no user is affected. But
the false assurance is load-bearing: this test is one of only two real-corpus checks that the approval
gate does not FALSELY refuse a legitimately reviewed plan, and a false refusal by that gate has NO
override. A green test that checks nothing there is worse than an absent one, because reviewers cite
it (plan `h3bjue`'s own review cites it as proof the named-id6 pattern survives corpus drift, which it
does; the point here is that surviving drift is not the same as still asserting something).
