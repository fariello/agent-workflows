- Id: 98zlut
- Status: open
- Blocks-Release: next
- Set: 98zlut
- Priority: high
- Work-Kind: bug
- Summary: aw backlog set has no --work-kind-aware gate default, so an item reclassified to bug or graduated by hand stays ungated

## Workflow history
- 2026-09-18 created (aw backlog): aw backlog set has no --work-kind-aware gate default, so an item reclassified to bug or graduated by hand stays ungated

FOUND 2026-09-18 while executing nobugship rgaasb E-04, from the measurement that the backfill population TRIPLED rather than shrank after child di08i9 shipped the creation default.

THE MEASUREMENT. rgaasb's population of live gateless bugs, re-derived at HEAD 8087387e: 65 items (47 open, 18 graduated), against 22 measured at review on 2026-09-12 and 28 when the Set was authored. By filename date the gateless items cluster overwhelmingly in the last three days: 26 dated 20260917 and 13 dated 20260918, i.e. AFTER di08i9's creation default landed.

WHY THAT IS NOT NECESSARILY di08i9 FAILING, stated honestly because the plan's own commit measured its default working. di08i9 defaults the gate in backlog.run_new via the shared backlog.decide_gate_default, and that path DOES work: filing three items during this very execution produced 'evidence':['blocks-release-default:next'] on each. So new items filed through the CLI with --work-kind bug ARE gated now.

WHAT THE GAP APPEARS TO BE. decide_gate_default is consulted at CREATION and in the setter paths, but it only ever RETURNS a value to write; it cannot see an item whose bug-ness arrives LATER. Two routes produce exactly that:

  * RECLASSIFICATION. An item filed as chore/followup/feature and later corrected to bug. The gate is
    not revisited, so it stays ungated. This is a documented live route: cnwy8g's own history records
    'RECLASSIFIED followup -> bug AND GATED, maintainer ruling 2026-09-03. Work-Kind edited directly
    because aw backlog set has no --work-kind flag' - and AGENTS.md records the maintainer
    reclassifying 59t9x5 from chore to bug by hand.
  * HAND AUTHORING. An item written directly into the tree, which bypasses the setter entirely. This
    is the hole rgaasb's checker exists to catch, and it now does.

WHY IT MATTERS. rgaasb makes the violation VISIBLE, which is a real improvement, but a rule whose
population regrows by tens of items per week between backfills is one a human will learn to ignore.
The creation default covers the front door; nothing covers reclassification.

SUGGESTED FIX. When aw backlog set changes an item's --work-kind INTO a gating kind (or transitions it
into a live status) and the item carries no gate, consult the existing decide_gate_default and apply
it, announcing it exactly as run_new does. The predicate, the notice shape, and the announcement
surfaces all already exist; this is a new CALL SITE, not new policy. NOTE --work-kind DOES now exist
on aw backlog set (verified in --help), so the tooling gap cnwy8g's history complained about is closed
and this call site is implementable today.

RELATED: the above explains the regrowth but was not measured item-by-item to a cause. Whoever takes
this should first classify a sample of the 20260917/20260918 items by route (created via CLI as a
non-bug then reclassified, versus hand-authored) so the fix targets the dominant one.
