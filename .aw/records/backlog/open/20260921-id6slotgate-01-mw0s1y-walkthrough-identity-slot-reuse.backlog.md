- Id: mw0s1y
- Status: open
- Blocks-Release: next
- Set: id6slotgate
- Priority: medium
- Work-Kind: bug
- Summary: Three walkthroughs reuse their source plan's id6 in their own filename identity slot, violating D140 and the walkthroughs README

## Workflow history
- 2026-09-21 created (aw backlog): Three walkthroughs reuse their source plan's id6 in their own filename identity slot, violating D140 and the walkthroughs README

MEASURED 2026-09-21 while executing IPD paw8so. This is the DATA half of the defect; the missing DETECTION is filed separately as `e2j5w4`.

THE VIOLATION. Three walkthroughs carry their source PLAN's id6 in their own `YYYYMMDD-<setid>-NN-<id6>-<slug>` filename identity slot while declaring no `- Id:` of their own:

  .aw/records/walkthroughs/20260906-lanectn-04-y5od1h-missing-input-report-and-refuse-walkthrough.md  (plan y5od1h)
  .aw/records/walkthroughs/20260917-lanectn-07-4fodkt-whole-set-verification-of-spec-7ckptx.walkthrough.md  (plan 4fodkt)
  .aw/records/walkthroughs/20260901-runstop-00-zpbx7o-graceful-quit-whole-set-verification.walkthrough.md  (plan zpbx7o)

THE RULE THEY BREAK, quoted from `.aw/records/walkthroughs/README.md`: 'The `<id6>` in the filename identity slot is the walkthrough's OWN unique identity (DECISIONS.md D140): a walkthrough MUST mint its own id6 there and MUST NOT reuse the id6 of the plan it documents. To link a walkthrough to the plan it documents, use the typed frontmatter field `Target-Id: <plan-id6>` (the canonical directional reference), never the identity slot.' D140 is the p7dqwz decision and names this exact shape.

THEY ARE NOT ALL EQUALLY BAD, WHICH MATTERS FOR THE REMEDY. `4fodkt` and `zpbx7o` DO carry a typed `- Target-Id:` bullet, so the relationship is machine-readable and only the identity slot is wrong; they need a fresh id6 minted into the slot (and into a new `- Id:`), with `Target-Id` left as-is. `y5od1h` carries NO typed reference field at all (it names its plan only as a prose `- Plan:` path), so it needs both the fresh identity AND a `Target-Id:` bullet.

MEASURED POPULATION CONTEXT. Of 24 walkthroughs: 8 are conformant (own `- Id:` equals the slot), 6 hold a slot id6 with no declared `- Id:`, and the remaining 10 are legacy names with no identity slot. Of the 6, exactly these 3 hold an id6 that is ANOTHER file's declared identity; the other 3 are legacy-slug false matches excluded by the real-id6 discriminator.

WHY IT GATES A RELEASE. `Work-Kind: bug`, and AGENTS.md's standing rule is that a live bug carries `Blocks-Release`. The user-perceptible effect: `aw find y5od1h` returns two artifacts for one identity, so an id6 no longer names exactly one file, which is the cross-tree handle every typed link depends on.

DO NOT RENAME THESE RECORDS WITHOUT A MAINTAINER DECISION. Renaming a record under `.aw/records/` rewrites tracked history that other artifacts cite by name; paw8so's execution contract explicitly forbade the executor from doing it and required reporting instead. `aw rename --to-id6` is ALSO a measured no-op on an already-clustered name, so no single existing verb performs this repair.
