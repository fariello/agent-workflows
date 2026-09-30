- Id: ieg7q6
- Status: open
- Set: 8mkt5l
- Priority: low
- Work-Kind: chore
- Summary: artifact_audit index cache cannot see an in-place record - Id: rewrite, so a stale id6 keeps resolving

## Workflow history
- 2026-09-30 created (aw backlog): artifact_audit index cache cannot see an in-place record - Id: rewrite, so a stale id6 keeps resolving

MEASURED 2026-09-30 at review of IPD dea7dr (F-06/OQ-01), and re-measured independently by the reviewer in this lane.

THE ROUTE. An IN-PLACE edit to a record's `- Id:` line changes no filename and no directory mtime, so a directory-content fingerprint (the signature dea7dr adopts) cannot see it. Reproduced under dea7dr's own candidate A with a 50ms sleep, so no race is involved:

  initial lookup aaaaaa: True
  route4 stale aaaaaa still found (should be False): True
  route4 new cccccc found (should be True): False

So the cached `by_declared_id` keeps resolving the OLD id6 and does not resolve the new one.

THE CANDIDATE THAT WOULD CLOSE IT, AND WHY IT WAS REFUSED. A per-file mtime-and-size signature (dea7dr's candidate B) does close this route unpinned, but is itself defeated by pinning the file's mtime and size, at which point the stale id6 resolves again. So it NARROWS rather than closes, at about 3x the chosen candidate's cost (dea7dr measured 10.70ms against 3.77ms). dea7dr OQ-01 refused it on that trade and named this item as the carrier.

WHY IT IS A chore AND NOT A bug. Rewriting a record's `- Id:` in place is a hand-edit shape no tooled path produces: every `aw` mutation verb that changes identity renames the file, which the adopted signature does see. No live consumer performs an in-place id6 rewrite followed by a re-audit. If one is ever found, reclassify and adopt candidate B, whose cost is already measured.

CONSUMER CONTEXT the reviewer added: the ONLY production consumer of this cache is `run_viewer` (`aw runs`). The doctor sweep calls `audit_tracked_artifact`, which touches neither `build_index` nor `find_artifact` (verified by source inspection and by instrumenting `build_index` across `doctor.probe_artifact_audit`, which recorded 0 calls).
