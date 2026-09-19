- Id: 7pntcb
- Status: open
- Set: 7pntcb
- Priority: medium
- Work-Kind: chore
- Summary: Nothing cross-checks a spec's acceptance criteria against the coverage of the plan Set implementing it

## Workflow history
- 2026-09-19 created (aw backlog): Found while resolving lifeglyph 2xz59a OQ-02, where five of spec uonrjg's 21 criteria were claimed by the orchestrator's coverage map but demanded by no child; only a human review caught it.

## The gap

A plan Set that implements a spec claims coverage of that spec's acceptance criteria in prose, and
nothing verifies the claim. `aw ipd lint` checks the `E-*`/`V-*` bijection WITHIN one plan, and
`aw check plans` validates metadata, but no tool reads a spec's criteria list and asks whether the Set
implementing it demands each one somewhere.

MEASURED INSTANCE, 2026-09-19. Spec `uonrjg` has 21 criteria (A1 to A21). Its orchestrator `2xz59a`
carried a coverage map asserting all 21 were owned. Five were not: A1, A4, A6, A19 and A21 appeared in
NO child's validation section, verified by grepping each token across all eight child files. The Set
would have executed to completion and reported success with five release-gating criteria never verified,
because each child validates only the criteria it names and the parent validates only child completion.

Note the map was not merely incomplete, it was WRONG IN BOTH DIRECTIONS: the same review that found the
five missing also listed A12 as missing, and re-measurement showed A12 was already claimed twice. So a
hand-maintained coverage map produces both false negatives and false positives.

## Why a checker is plausible

The inputs are already structured. A spec's criteria are `- **A<n>**` bullets under
`## Acceptance criteria`; a plan's claims live in its `V-*` items; and `- From-Spec:` already links a
plan to its spec (validated by `check.from-spec-dangling`). So a rule could resolve each plan's
`From-Spec`, parse the spec's criteria ids, and report any criterion no plan in the Set mentions.

HONEST LIMITS, so the item is not oversold. A token grep proves a criterion is NAMED, not that it is
genuinely validated: a plan could mention A4 and demand nothing useful. That makes this a
NECESSARY-not-sufficient check, in the same family as the existing carrier-obligation rule, which also
verifies that a reference resolves rather than that the handoff is wise. It is still worth having,
because the failure it catches (a criterion named by nobody) is exactly the one that reached review here
and is mechanically detectable.

## Scope sketch

- A consistency rule reporting, for each spec with at least one `From-Spec` plan, the criteria no such
  plan names. Advisory severity to start, since the corpus has not been measured for how many existing
  Sets would fail.
- Measure the corpus BEFORE choosing a severity. The carrier rule's own history is the precedent: it
  shipped `info` for pre-cutover plans precisely because 664 offending rows across 106 plans would have
  turned every tree red and trained agents to bypass `aw check`.
