- Id: xp6o3v
- Status: open
- Set: xp6o3v
- Priority: low
- Work-Kind: chore
- Summary: aw rename/group never rewrite a facet-less filename citation, so a rename silently leaves prose citing the old name

## Workflow history
- 2026-10-01 created (aw backlog): Found while authoring plan j7dsci (graduating tf4jz5): measured that the three citations tf4jz5 names as the propagated damage are all unreachable by the rewriter.

MEASURED WHILE AUTHORING PLAN j7dsci. This is the TOOLING gap that forces that plan to make three of its edits by hand; j7dsci works around it deliberately and carries this as its OQ-02.

THE FACTS. `artifact_refs.plan_reference_rewrites_with_warnings` builds exactly TWO match keys from an old/new name pair: the FULL filename (`<name>.ipd.md`) and the whole stem INCLUDING the type facet, via `artifact_refs._whole_stem` (`<name>.ipd`). A citation that names the record WITHOUT either suffix, ending at the slug, matches neither key, and `_boundaried` therefore finds nothing. Such a citation is silently left pointing at a filename that no longer exists.

IT IS NOT HYPOTHETICAL AND IT IS EXACTLY THE DAMAGE A SIBLING ITEM FILED. Driving the real planner on the `qrokie` rename (`20260101-instsafe-07-qrokie-...-design-spec.ipd.md` -> `20260723-...`), the preview names SEVEN citing files and NONE of them is `DECISIONS.md`, `.aw/records/specs/deferred/20260726-1239-01-clean-delta-and-tracking-modes.spec.md`, or `.aw/records/research/20260726-0054-aw-delivery-and-clean-delta-research/README.md`. Those three are precisely the propagated citations backlog item `tf4jz5` names as the harm, and all three cite the facet-less stem `20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec`. So a maintainer running `aw rename plans` to repair a record would see a preview that LOOKS complete and would be left with three dangling citations.

A SECOND, NARROWER BLIND SPOT MEASURED AT THE SAME TIME: `artifact_core._REFERENCE_TEXT_SUFFIXES` is `('.md', '.txt', '.py')`, so no `.json` is ever scanned. The tracked fixture `tests/fixtures/derive_plan_status_baseline.json` keys plans by PATH, so a rename drops one baseline entry with no rewrite and no report. Its guard still passes (731 against a floor of 700), which makes the loss silent. Whether that belongs in the rewriter or in the fixture's own keying (plan `rlcq7g` re-keys it by id6) is part of the question.

WHY THIS IS NOT A ONE-LINE WIDENING, and why it is filed rather than fixed. Adding a facet-less key changes what EVERY rename of EVERY artifact type rewrites across the whole corpus, and it cuts both ways: it would catch these three, and it would also match prose that names a SLUG rather than a file, where a rewrite is wrong. Deciding it needs a corpus measurement of how often a facet-less stem appears and how often it means the file. Note the existing `count_legacy_prefix_records` shared-prefix guard and `_mask_fenced_code` as the precedents for how this module already narrows a risky key rather than matching greedily.

PRIORITY IS LOW AND WORK-KIND IS chore DELIBERATELY: no current record is broken by it (the gap only bites DURING a rename, and the one live repair that hits it, j7dsci, handles it by hand with the occurrences enumerated), and the fix is a judgement about matcher breadth rather than a defect with one correct answer. It therefore carries no release gate.
