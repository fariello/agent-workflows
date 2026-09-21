- Id: 8mkt5l
- Status: open
- Blocks-Release: next
- Set: 8mkt5l
- Priority: medium
- Work-Kind: bug
- Summary: artifact_audit's index cache can return a STALE index, because its invalidation signature is directory mtime and two writes inside one mtime tick are invisible to it

## Workflow history
- 2026-09-21 created (aw backlog): artifact_audit's index cache can return a STALE index, because its invalidation signature is directory mtime and two writes inside one mtime tick are invisible to it

OBSERVED 2026-09-21 in lane 9lyg5h as a FLAKE, then reproduced DETERMINISTICALLY. During execution of plan 9lyg5h one bare-suite run reported `tests/test_artifact_audit.py::VerdictParityTests::test_four_verdict_shapes` failing with `AssertionError` on `assertTrue(loc.location_mismatch)`. It then passed in isolation and in eight consecutive repeats of its own module, and in five consecutive full bare-suite runs, so it is intermittent rather than a regression. It is NOT caused by that plan's changes: the failing test does not touch the runner, and a bare suite at the pristine base commit was also clean.

THE CAUSE IS IN PRODUCTION CODE, not in the test. `artifact_audit.build_index` memoizes its index in `_INDEX_CACHE` keyed on `(repo_root, record_types)` and invalidates on `_dir_signature`, which is the set of record-directory mtimes (`agent_workflows/artifact_audit.py:726-811`). Directory mtime has FINITE granularity, so if an artifact is created, the index is built, and a SECOND artifact is created within the same mtime tick, the signature is unchanged and the cache returns an index that does not contain the second artifact. The audit then reports it `missing_entirely`.

MEASURED, by pinning the directory mtime back to simulate one tick (the tick itself is what makes the natural case rare and timing-dependent):

    first lookup found it         : True
    second artifact EXISTS on disk: True
    audit sees it?                : False
    location_mismatch (test wants True): False   <-- reproduces the flake

That the granularity is real here was measured too: two successive file creations in one directory left `st_mtime_ns` BYTE-IDENTICAL (`1789985177747625071` twice).

WHY IT IS A BUG AND NOT A TEST DEFECT, since the easy fix would be to slow the test down. `audit_artifact` is consumed by the finalize/executed-plan audit surfaces, so a stale index makes a REAL artifact report as missing or as non-drifting. Any writer that moves or creates a record and then audits within the same tick can be told the wrong thing, and an agent runner does exactly that kind of write-then-check. The consequence is user-perceptible and wrong rather than merely slow.

WHY `Blocks-Release: next`: per this repository's rule that every live bug gates the next release. It also matters more than its rarity suggests, because the symptom is an INTERMITTENT red test in the whole-repository suite, and that suite IS the integration trust signal: `daexj1`/`h5pyqa` measured one unrelated red test costing a run three refused lanes, eight cascaded blocks, 2h 10m and 55.02 USD.

FIX SHAPE (not applied; outside lane 9lyg5h's Scope-Paths): make the signature able to see a same-tick change, for example by including a cheap directory-content fingerprint (entry count, or the sorted name set) alongside the mtimes, or by adding `st_ctime_ns`/size, or by giving the cache a short TTL. Do NOT fix it by sleeping in the test, which would hide a defect a production caller can hit.
