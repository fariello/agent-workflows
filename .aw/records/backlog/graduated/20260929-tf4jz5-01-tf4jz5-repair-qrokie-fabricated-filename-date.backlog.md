- Id: tf4jz5
- Status: graduated
- Graduated-To: tf4jz5
- Set: tf4jz5
- Priority: low
- Work-Kind: chore
- Summary: The executed plan 20260101-instsafe-07-qrokie carries a fabricated filename date; its real 20260723 survives only in git and the wrong date propagated into DECISIONS.md and a spec

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053024Z-3198670: j7dsci
- 2026-09-29 created (aw backlog): Filed while authoring plan 949enf (graduating j84jg3): the already-materialized casualty of that defect, deferred to the maintainer as 949enf OQ-03.

MEASURED WHILE AUTHORING PLAN 949enf. This is the ALREADY-MATERIALIZED casualty of the date-fabrication defect 949enf fixes; the code fix prevents the NEXT occurrence and deliberately repairs nothing retroactively.

THE FACTS. `.aw/records/plans/executed/20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec.ipd.md` carries `- Date: 2026-07-23 (fleshed 2026-07-26 from research)`. `git log --diff-filter=R --name-status` shows it was renamed from `20260723-1100-07-clean-delta-and-tracking-modes-design-spec.md` in commit `05c4deb1`. So its real date `20260723` WAS present in the old filename, was discarded by the rename, and the `20260101` in its name today is the fabricated constant. Its front-matter `- Date:` is malformed (the trailing parenthetical defeats the anchored date regex), which is why the fabricator fired.

THE WRONG DATE PROPAGATED into prose citations of the plan BY NAME: `DECISIONS.md` cites "IPD 20260101-instsafe-07-qrokie-clean-delta-and-tracking-modes-design-spec", and `.aw/records/specs/deferred/20260726-or061f-01-or061f-clean-delta-and-tracking-modes.spec.md` records it as "produced by IPD `20260101-instsafe-07-qrokie-...`".

WHY THIS IS NOT A SIMPLE git mv, and why it is filed rather than fixed. It is an EXECUTED plan, so AGENTS.md forbids changing what it records and an `ipd-executed-gate` hook enforces that; and the two citations above would have to be rewritten in the same change or become dangling. So the decision is a maintainer call: RENAME with reference rewriting (`aw rename plans` updates name-based references, though note it has the sibling legacy-name bug 949enf fixes), or LEAVE it as recorded history and accept that one plan's name lies about its date.

PRIORITY IS LOW AND WORK-KIND IS chore DELIBERATELY: nothing is currently broken by it beyond one record's name being wrong, the real date is recoverable from git, and it is NOT filed as a bug because the live defect is the code path (949enf) rather than this artifact. It therefore carries no release gate.
