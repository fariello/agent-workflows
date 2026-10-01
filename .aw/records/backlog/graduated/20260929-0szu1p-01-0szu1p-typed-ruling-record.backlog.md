- Id: 0szu1p
- Status: graduated
- Graduated-To: rulingcarrier
- Set: 0szu1p
- Priority: medium
- Work-Kind: feature
- Summary: Decide whether a maintainer ruling about named artifacts should get its own typed enforceable record, since today a ruling's only homes are unparsed DECISIONS.md prose or another plan's prose

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: jge900
- 2026-09-29 created (aw backlog): Filed at authoring time by plan nllamb (Set iguvci) as the durable carrier for its OQ-01. Filed rather than deferred to the executor because check.ipd-uncarried-obligation is error-severity for a plan dated after the 2026-09-19 cutover and refuses a Carrier naming a non-resolving id6.

WHAT IS UNDECIDED. A maintainer ruling that names specific artifacts (for example the 2026-09-12 ruling that 13 named plans carry specific Priority/Work-Kind values) has no enforceable home. Measured: there is no `decision` artifact type in `artifact_types.TYPE_BACKENDS` and no `.aw/records/decisions/` tree, and `DECISIONS.md` is a repo-root append-only prose log whose only programmatic use is as a text corpus for id6 reference scanning (`artifact_core.SCAN_ROOTS`). Nothing parses its entries, no status is read from it, and it is invisible to `aw attention` for the same structural reason deprecated `TODO.md` is.

WHY IT MATTERS, with a measured instance. Backlog `iguvci` recorded the consequence: the 2026-09-12 ruling lived in three plans' PROSE, the plan that was to apply it did not execute until 2026-09-23, and by then all 15 named plans were terminal and unwritable. The ruling was recorded in three places and landed on one plan's fields. Nothing detected the decay because prose carries no status.

THE OPTIONS, none obviously right. (a) A new typed `decisions/` records tree with a lifecycle, a checker, a CLI surface and an `aw attention` mapping, which is the complete answer and also the most work. (b) A convention that a ruling MUST be written onto the governed artifact's fields immediately, which the shipped 2026-09-24 ruling already implies for Priority/Work-Kind (`backlog.run_new` and `ipd_authoring` both cite it as 'decided where the work is first recorded') and which needs no new type. (c) A backlog item per decided artifact, as `iguvci` suggested, reusing the shipped carrier mechanism instead of inventing one.

WHAT IS ALREADY DONE, so this is not re-derived. Plan `nllamb` (Set `iguvci`) delivers the DETECTION half, which is useful under all three answers: an `aw check` rule catching a pending plan whose checklist names id6 targets its own `Scope-Paths` cannot reach. That is the measured signal that would have caught the 2026-09-12 decay. It deliberately does NOT choose among (a), (b) and (c), because that is a decision about what the records model should contain rather than a fact about what it does.

NOT URGENT. The detection rule removes the silence, which was the actual defect. This item is the model question.
