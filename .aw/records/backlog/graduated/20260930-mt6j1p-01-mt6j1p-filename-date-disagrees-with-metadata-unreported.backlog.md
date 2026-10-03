- Id: mt6j1p
- Status: graduated
- Graduated-To: mt6j1p
- Set: mt6j1p
- Priority: low
- Work-Kind: followup
- Summary: No checker reports a plan whose filename date disagrees with its own - Date: metadata, so a wrong filename date is silent even after the value itself is validated

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: wyk11f
- 2026-09-30 created (aw backlog): Filed while authoring plan fqcax0 (graduating 5h8u3z) as the carrier for its OQ-03: the wider gap the 5h8u3z backlog item raises in its last sentence and does not answer.

DEFERRED FROM PLAN fqcax0 OQ-03, which closes the ADJACENT defect (a present-but-unparseable - Date: value escaping aw ipd lint) and deliberately does not reach this one.

THE GAP. Nothing compares a plan's FILENAME date against the plan's own - Date: metadata, so the two can disagree indefinitely with no finding. Measured at authoring: a plan whose filename says 20260101 while nothing else does passes 'aw check plans' with rc 0 and no date finding. The corpus contains exactly one such file today, '.aw/records/plans/executed/20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md', whose real date is 20260723 (repairing that one record is tf4jz5; this item is about DETECTING the class).

WHY IT IS A SEPARATE RULE, not a widening of fqcax0's check. Its subject is a DISAGREEMENT between two sources that are each individually well-formed, whereas fqcax0's subject is a single value that cannot be parsed at all. They have different false-positive profiles, which is the whole difficulty.

THE DESIGN QUESTION A HUMAN MUST SETTLE FIRST, and the reason this is filed 'followup' rather than 'bug': a naive equality rule would MISFIRE on legitimate records. Spec 'agents-artifact-organization' Section 4.2 defines the leading YYYYMMDD as 'the SET's canonical date, shared by all members', so a regroup may legitimately give a member a different leading date from its own - Date:. Measured over the live corpus by plan 949enf: 31 of 589 clustered Sets already carry members with differing leading dates. So the rule needs a stated exemption for set-canonical dates (or must be scoped to a single-member Set, or must be advisory only), and whether it should exist at all is undecided.

WHAT WOULD MAKE IT A BUG: a measurement showing a disagreement that is NOT explained by set-canonical grouping and that a consumer acts on. fqcax0's F-03 enumerates the five date consumers; all read front matter, so a wrong FILENAME date is currently cosmetic plus self-perpetuating (949enf F-13) rather than load-bearing. That is why this is a followup and carries no release gate.
