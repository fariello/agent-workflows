- Id: sjsoqq
- Status: graduated
- Set: setiduniq
- Priority: high
- Work-Kind: feature
- Summary: Enforce setid uniqueness across types (hard/prevented) + bidirectional graduation links (From-Backlog/From-Spec by id6, Graduated-To by setid); fix the agentadhere collision

## Workflow history
- 2026-09-08 graduated (aw set): Graduated to the setidhard Set: yku4ga (Order 0), drzbs9 (01 sweep), bwgyum (02 Graduated-To + dangling check), dw7i3m (03 fresh-setid mint + prevention). Set setid is setidhard NOT setiduniq, because scaffolding into setiduniq immediately collided with THIS item and was regrouped under the spec's own G1 rule: this item's defect demonstrated while graduating it. DELIVERABLE #3 IS DEAD (landed 9107790 with tests/test_status_set.py coverage); the orchestrator re-checks it as a regression only. DELIVERABLE #1 IS HALF DEAD and easy to misread: check.setid-collision is ALREADY severity error at check_engine.py:95, so what remains is the soft posture I2 names plus actionability. STALE MEASUREMENT CORRECTED: the item says aw check all reports 0 setid-collision findings; it reports 29 across 21 distinct setids, and ALL 29 are the benign backlog-shares-its-plan's-setid pattern. That re-sequenced the Set: the dependency chain is 02 then 03 then 01 while the Order digits read 01,02,03, because sweeping before the fresh-setid mint would be undone by the next graduation and neither can precede the typed forward link. TWO BLOCKING GATES on the orchestrator: spec 4w7d6s is draft with three open questions, and the maintainer must accept a naming-convention change affecting every future graduation (narrowing I1 is the alternative). Item carries no Blocks-Release, so no plan inherits one. Separately reported: aw group plans --rename --apply without --order reset all four plans to Order 00.
- 2026-08-27 created (aw backlog): Enforce setid uniqueness across types (hard/prevented) + bidirectional graduation links (From-Backlog/From-Spec by id6, Graduated-To by setid); fix the agentadhere collision

PARTIAL OBSOLESCENCE RECORDED 2026-09-08 AT GRADUATION. Graduated to the `setidhard` Set: `yku4ga`
(Order 0, orchestrator), `drzbs9` (01, the sweep), `bwgyum` (02, `Graduated-To` + its dangling check),
`dw7i3m` (03, fresh-setid mint + creation/move prevention). NOTE the Set setid is `setidhard`, NOT
`setiduniq`, deliberately: scaffolding into `setiduniq` immediately collided with THIS item and was
regrouped under the spec's own G1 rule before authoring continued. That is this item's own defect,
demonstrated in the act of graduating it.

DEAD: DELIVERABLE #3. Landed in `9107790` with coverage in `tests/test_status_set.py`, as the Progress
note below already records. Excluded from the Set; the orchestrator's E-03 re-checks it as a REGRESSION
only.

HALF DEAD, AND EASY TO MISREAD: DELIVERABLE #1. The severity is ALREADY `error`:
`check_engine.py:95` registers `check.setid-collision` as `RuleSpec("error", ASSURANCE_REPOSITORY,
DET_DETERMINISTIC, "I-09")`, beside `check.id6-collision`. So there is no severity flip left to make. What
remains is the soft/whitelistable POSTURE the spec's I2 names, and the rule's ACTIONABILITY (see below).

STALE MEASUREMENT CORRECTED: the Progress note below says "`aw check all` now reports 0 setid-collision
findings". It reports TWENTY-NINE, across TWENTY-ONE distinct setids (`durablecapture` 4, `runverdict` 4,
`runrecon` 2, `integearn` 2, then seventeen at 1 each). The note's accompanying claim that the collision
"PHYSICALLY persists" is TRUE and re-verified: the closed item `3gr7fk` still carries `- Set: agentadhere`,
shared with EIGHT executed plans.

THE FINDING THAT RE-SEQUENCED THE WHOLE SET: all 29 findings are the SAME benign shape, a backlog item
sharing its setid with the plan Set it graduated into. So deliverable #6 (the sweep) cannot run first,
because deliverable #5 (fresh-setid mint) is the root cause and the next graduation would recreate a
collision; and neither can precede #4 (`Graduated-To`), because removing the shared setid without the
typed forward link deletes the only readable source-to-plan pointer. The dependency chain is therefore
02 then 03 then 01, while the Order digits read 01, 02, 03. Enforcement stays last, per spec Section 5.

TWO GATES THE SET CARRIES, both blocking and both recorded on the orchestrator. FIRST, spec `4w7d6s` is
`- Status: draft` with OQ-01/02/03 all `open`, its header says "REVISABLE before implementation", and this
item says implement it "once the spec is reviewed"; two of those questions change what the children build.
SECOND, and larger: because all 29 findings are the repository's own working convention, the maintainer is
being asked to accept a naming-convention change affecting every future graduation. If the at-a-glance name
match matters more, the right outcome is to NARROW I1 (for example exempting a pair joined by a resolvable
`From-Backlog`) rather than to sweep 21 setids, and the Set would need re-authoring.

A TOOL DEFECT FOUND WHILE GRADUATING, reported separately and NOT folded into the Set: `aw group plans
<id> --set X --rename --apply` with no `--order` reset the Order to `00` on all four plans, including
three children, silently producing three Order-0 children in one Set.

Design source of truth: spec `4w7d6s` (`.aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`). Implement its invariant + graduation-link model as a follow-on IPD Set once the spec is reviewed.

Tooling deliverables (from the spec):
1. Promote `check.setid-collision` from SOFT (whitelistable, awcheck-02-xwxxo8 E-02) to HARD/fail-closed in `check_engine` + `aw doctor` (like `check.id6-collision`).
2. Prevent at creation/move: `aw ipd scaffold`, `aw research new`/`new-comparison`, `aw backlog new`, `aw group`, `aw rename` refuse to mint/move into a cross-type-duplicate setid.
3. Setter UX: `aw ipd set`/`aw set <type>` resolve a setid WITHIN the requested type (so `aw ipd set agentadhere` works); on a genuine collision emit the specific setid-collision message + `aw group ... --set` recovery, not the generic "type mismatch" (the bug that triggered this).
4. Add `Graduated-To: <setid>[,<setid>...]` (multi-valued) to backlog items + specs; graduation writes it alongside the child's `From-Backlog`/`From-Spec`; add `check.graduated-to-dangling`.
5. Graduation mints a FRESH child setid (never the source's); links are typed + bidirectional.
6. One-time migration sweep: resolve all pre-existing cross-type setid collisions (starting with `agentadhere` - regroup the closed `3gr7fk` backlog item to its own setid + set its `Graduated-To`) BEFORE enabling hard enforcement, so it does not mass-fail.

Origin: `aw ipd set approved agentadhere ...` failed with a confusing cross-type "type mismatch"; the setid collision (plan Set vs closed backlog item vs research reports) is flagged by `aw check` today but only softly and not consulted by the setters. Reuses From-Backlog (built) + From-Spec (designed) + the existing collision checker.

Progress (2026-08-27): deliverable #3 (setter UX - `aw ipd set`/`aw set` scope the selector to the requested record type) landed via commit 9107790, WITH test coverage in `tests/test_status_set.py`. This item stays OPEN; remaining: #1 promote `check.setid-collision` soft -> hard/fail-closed; #2 creation/move prevention; #4 `Graduated-To` field + `check.graduated-to-dangling`; #5 fresh-setid graduation; #6 migration sweep. NOTE: `aw check all` now reports 0 setid-collision findings, but the collision PHYSICALLY persists - the closed `3gr7fk` backlog item still carries `- Set: agentadhere` (verified); detection changed, the data did not. Do NOT close until spec 4w7d6s's invariant + graduation-link model is built.
