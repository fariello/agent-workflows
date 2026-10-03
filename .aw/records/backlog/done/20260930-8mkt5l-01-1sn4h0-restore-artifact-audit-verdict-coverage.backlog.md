- Id: 1sn4h0
- Status: done
- Graduated-To: 8mkt5l
- Set: 8mkt5l
- Priority: medium
- Work-Kind: chore
- Summary: The suite trim deleted four artifact_audit verdict tests and no surviving test reaches the index cache stale path

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD auqoig executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-8mkt5l-02-auqoig-restore-the-artifact-audit-verdict-coverage-as-outcome-tests.ipd.md); evidence .aw/records/plans/executed/20261001-8mkt5l-02-auqoig-restore-the-artifact-audit-verdict-coverage-as-outcome-tests.ipd.md
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: auqoig
- 2026-09-30 created (aw backlog): The suite trim deleted four artifact_audit verdict tests and no surviving test reaches the index cache stale path

MEASURED 2026-09-30 at review of IPD dea7dr (F-05), with the deletion re-verified independently by the reviewer in this lane.

WHAT WAS DELETED. Commit `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests") removed the whole `VerdictParityTests` class from `tests/test_artifact_audit.py`, including `test_four_verdict_shapes`, the liveness-carry test, the disposition-mapping test and the multi-word-status test. Verified: `git show 19313eed^:tests/test_artifact_audit.py` contains `class VerdictParityTests` and `test_four_verdict_shapes`; the file at HEAD contains neither.

WHY IT MATTERS. `test_four_verdict_shapes` was the only surviving test that wrote two artifacts into one repo root and audited both, which is the shape that exercises the index cache's staleness path. dea7dr instrumented a full bare run and recorded `{"total_calls": 224, "total_hits": 187, "STALE_HITS": 0}`, so the suite currently cannot go red from that defect class at all.

WHAT THIS ITEM IS AND IS NOT. dea7dr adds `tests/test_artifact_audit_index_cache.py` covering the CACHE INVALIDATION routes, which is the coverage its own fix needs. This item is the separate, larger question of the deleted VERDICT coverage: four tests about what an audit CONCLUDES, not about whether a lookup finds a file.

THE TRIAGE THIS NEEDS, which is why it is not a mechanical restore: each deleted test must be classified before restoring, because GUIDING_PRINCIPLES P16 and AGENTS.md forbid code-pinning tests, and some deleted tests in that trim were removed precisely because they pinned structure rather than behavior. Restore only those asserting observable outcomes; re-author the rest as outcome tests or record why they should stay deleted.
