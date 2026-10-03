- Id: ieg7q6
- Status: done
- Graduated-To: 8mkt5l
- Set: 8mkt5l
- Priority: low
- Work-Kind: chore
- Summary: artifact_audit index cache cannot see an in-place record - Id: rewrite, so a stale id6 keeps resolving

## Workflow history
- 2026-10-02 done (aw backlog): closed by aw agy run: IPD 0a7v0x executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-8mkt5l-02-0a7v0x-close-the-artifact-audit-cache-s-blindness-to-an-in-place-re.ipd.md); evidence .aw/records/plans/executed/20261001-8mkt5l-02-0a7v0x-close-the-artifact-audit-cache-s-blindness-to-an-in-place-re.ipd.md
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: 0a7v0x
- 2026-10-01 note (aw backlog): FALSIFICATION of this item's named remedy, measured 2026-10-01 at HEAD 8ca1d979c while authoring plan 0a7v0x. This item closes by instructing a future executor to 'adopt candidate B, whose cost is already measured'. Candidate B (per-file mtime+size) DOES NOT CLOSE THE ROUTE even unpinned: an id6 is a fixed-width 6-char token (check_engine._ID_LINE_RE pins [0-9a-z]{6}), so an in-place id6 rewrite is SIZE-PRESERVING and st_size can never discriminate, leaving only the file mtime and the same ~1ms tick the directory mtime had. Measured BLIND in 149/200 immediate-rewrite trials (0/200 after a 50ms sleep), at 4.10x the shipped signature's cost (71.18ms vs 17.34ms). Plan 0a7v0x therefore does NOT change _dir_signature; it verifies a tier-one identity claim in find_artifact instead (479us overhead, 1.3% of a lookup, 0.006% of the rebuild it avoids). Plan 0a7v0x also found two wrong answers beyond the stale positive recorded above (a WRONG PATH with no filename change anywhere, and a PHANTOM COLLISION where an in-place fix to a duplicate id6 still reports the collision), and found that the dominant production path bypasses this cache entirely (run_viewer threads one explicit artifact_index= through 9 call sites). See plan 0a7v0x F-03/F-04/F-06. No requirement of this item is changed by this note.
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
