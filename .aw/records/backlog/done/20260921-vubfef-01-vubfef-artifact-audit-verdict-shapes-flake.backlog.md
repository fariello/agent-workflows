- Id: vubfef
- Status: done
- Set: vubfef
- Priority: low
- Work-Kind: bug
- Summary: test_artifact_audit.py::VerdictParityTests::test_four_verdict_shapes failed once under the parallel suite and has not reproduced; suspected shared-state flake in artifact_audit's process-global _INDEX_CACHE

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: test deleted in 19313eed; cache concern tracked in 8mkt5l
- 2026-09-21 created (aw backlog): OBSERVED ONCE, 2026-09-21, in a bare 'python3 -m pytest' run (xdist -n auto, random order) in the working tree of the l2mzxn ladder fix: '2 failed, 7995 passed' where the other failure was an EXPECTED wording assertion I was mid-way through updating. HAS NOT REPRODUCED SINCE: five consecutive bare full-suite runs green (7993 -> 7997 passed as the new tests landed), the file alone green 3x, the file across 6 explicit --randomly-seed values green, the class alone under xdist 3x, and an 8x stress of the three interacting files green. Also green on a PRISTINE detached worktree at the same HEAD (full suite, 7993 passed), so it is not something my change introduced to that test.

WHY IT IS FILED RATHER THAN DISMISSED: I saw it fail and could not prove WHY, and an unexplained failure in a gate test is exactly the shape of defect this repo keeps measuring. The honest statement is 'observed once, cause unproven', not 'flake, ignore'.

THE SUSPECTED MECHANISM, stated as a HYPOTHESIS I did NOT confirm. artifact_audit carries a process-global traversal cache (_INDEX_CACHE at artifact_audit.py:726, bounded at _INDEX_CACHE_MAX=8) keyed on (resolved repo_root, record_types) and invalidated by _dir_signature (:730), which is a tuple of record-directory st_mtime_ns values. Two properties make a cross-test interaction conceivable: (1) the key is a PATH, and tempfile can hand out the same path to a later test after an earlier one is removed, so a stale entry can in principle answer for a different tree; (2) invalidation rests entirely on directory mtimes, so any tree whose mtime does not advance between two different contents reuses the old index. The cache CLEARS wholesale at 8 entries, which under xdist means the eviction point depends on which other tests shared the worker - a classic order-dependent shape. test_four_verdict_shapes calls audit_artifact four times against one temp root and asserts one clean, one location_mismatch, one status_mismatch and one missing_entirely, so a stale index would plausibly surface as exactly one of those four verdicts being wrong.

I TRIED AND FAILED TO CONFIRM IT: a directly constructed same-path collision (build tree A at a path, index it, rmtree, rebuild different contents at the SAME path, re-index) returned the CORRECT answer both times, so either the signature catches it or my reproduction missed a condition the suite supplies.

WHAT A FIX WOULD NEED TO DECIDE: whether a process-global cache keyed on a reusable filesystem path is sound in a test process at all, versus keying on (path, inode/device) or exposing an explicit invalidation hook a fixture can call. Note the cache is a deliberate performance measure with a recorded rationale (the docstring measures record_dirs at ~1.6ms/call, ~16ms per signature), so the fix is NOT 'delete the cache'. Do not close this without either reproducing the failure or demonstrating the interaction is impossible; if a reproduction proves it harmless in production and only reachable in-test, reclassify accordingly and say so.
