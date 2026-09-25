- Id: 3pmsgf
- Status: done
- Set: 3pmsgf
- Priority: medium
- Work-Kind: followup
- Summary: rununify child plans' test fences are computed against pre-OQ scope, so re-opening scope via an OQ answer silently leaves guards unfenced

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: every rununify child it names is executed
- 2026-09-17 created (aw backlog): Found during rununify child 04 (tx6q0h). That plan's F-14 correctly identified that its Scope-Paths omitted test files the change must edit, and fenced five. But F-14 computed that list against the RE-SCOPED plan, which had provisionally EXCLUDED build_prompt. When the maintainer's OQ-03 answer restored build_prompt to scope, three further source-reading guards came into range and failed (tests/test_shared_checkout_contract.py, tests/test_lane_retention.py, tests/test_defect_report.py); all three were re-based and added to Scope-Paths at execution. The remaining rununify children (ct4w0a, sy7uwh, yrqyxb, ty3cj6, orziju, s16omw, 3dki3o) each carry a blocking OQ-03 resolved by the same Set-wide directive, and each one's test fence was likewise computed against its narrower reviewed scope. So each is likely to hit the same gap. Consider re-deriving each child's fence from the POST-directive scope before it executes, or having the finalize scope gate treat a re-based guard as an expected class rather than a surprise.
