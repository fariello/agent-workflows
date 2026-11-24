- Id: q2vkdv
- Status: open
- Set: q2vkdv
- Work-Kind: followup
- Priority: low
- Summary: aw check all --agent picks a different top-level next hint on back-to-back runs over an unchanged tree, so its stdout hash is not a stable baseline key (found by 786w7r attempt 2: ayfyie group hint vs z1zu8c rename hint)
- Short-Description: aw check all --agent picks a different top-level next hint on back-to-back runs over an unchanged tree, so its stdout hash is not a stable baseline key (found by 786w7r attempt 2: ayfyie group hint vs z1zu8c rename hint)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): aw check all --agent picks a different top-level next hint on back-to-back runs over an unchanged tree, so its stdout hash is not a stable baseline key (found by 786w7r attempt 2: ayfyie group hint vs z1zu8c rename hint)

Measured 2026-11-24 at 56e9d649f: two consecutive `aw check all --agent` runs on an unedited tree produced the same diagnostics and findings_by_severity but different top-level `next` strings, so sha256 of stdout differed (ee0ec355... in attempt 1, ee0e8613... and 23113cb7... in attempt 2). Baselines such as 786w7r F-30 must compare rule multisets instead. Fix: choose the `next` hint deterministically (for example by sorted diagnostic order).
