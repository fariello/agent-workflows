- Id: an1a33
- Status: graduated
- Graduated-To: 8mkt5l
- Set: 8mkt5l
- Priority: low
- Work-Kind: chore
- Summary: artifact_audit _INDEX_CACHE evicts by wholesale clear(), so crossing the cap discards every entry instead of one

## Workflow history
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: bvw2nd
- 2026-10-01 note (aw backlog): Graduated to plan bvw2nd (20261001-8mkt5l-03). No requirement of this item is changed; this record is additive. THE ITEM'S OPEN QUESTION IS ANSWERED, and the answer argues AGAINST promotion to bug. The item asked whether any real caller crosses 8 roots in one process. One does, but it is the TEST SUITE, not a shipped command: tests/test_run_viewer.py calls audit_step_artifact with no artifact_index=, so every call reaches _INDEX_CACHE, and each test builds its own temp root; instrumented, that one module drives build_index 82 times across 29 distinct roots in one process (a three-module slice reaches 177 calls across 50 roots). The item's note that run_viewer is one-root-per-invocation is correct for the shipped command. REPRODUCTION CONFIRMED exactly: cache size series 1,2,3,4,5,6,7,8 then 1,2 over 10 roots. THE PRIZE IS NEAR ZERO, which the item could not know: replaying that real 82-call trace, wholesale clear() costs 30 rebuilds and single-entry LRU also costs 30 at cap 8, against a distinct-key floor of 29, so at most ONE rebuild was ever avoidable; 17 of 29 keys are queried exactly once, so there is almost no reuse for any policy to preserve. The avoidable rebuild is on a 3-record temp root costing a median 1.26ms, NOT on the 2258-record repo root (median 4326ms cold against a 20.2ms warm hit, 214x), so the item's cold/warm ratio is right about the ratio and wrong about the denominator. ALSO FOUND: a single repo root can occupy up to 10 cache keys by itself, because the key includes record_types and audit_artifact reorders it per artifact type, so the cap is reached without any multi-root caller. CAP VERSUS POLICY: the cap, not the policy, is what would have moved the measured trace (LRU first beats clear() at 16, both reach the floor at 32), but one ArtifactIndex measures about 1.34 MiB so caps of 16/32 would admit about 21/43 MiB for a 1.26ms prize; the plan therefore changes the policy only and declines the cap on that measurement. The policy change still earns its place by removing an UNBOUNDED worst case: in a hot-root-plus-streaming workload, clear() rebuilds the hot root 29 of 200 times (57 with two cold roots per iteration) against LRU's 1. No such long-lived process exists today, which is why chore still holds.
- 2026-09-30 created (aw backlog): artifact_audit _INDEX_CACHE evicts by wholesale clear(), so crossing the cap discards every entry instead of one

MEASURED 2026-09-30 at review of IPD dea7dr (F-09), re-measured independently by the reviewer in this lane.

THE BEHAVIOR. `artifact_audit.build_index` evicts with `if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX: _INDEX_CACHE.clear()`, so crossing the cap (`_INDEX_CACHE_MAX = 8`) discards ALL entries rather than evicting one. Measured by indexing 10 distinct temporary roots in sequence:

  MAX: 8 | cache size after 10 distinct roots: 2

So a multi-root caller rebuilds indexes it had cached moments earlier.

WHY IT IS NOT A STALENESS DEFECT. A cleared cache is SLOW, never WRONG, so this cannot produce the `missing_entirely` wrong answer that motivated dea7dr. It is filed separately for that reason and dea7dr left it deliberately alone.

WHAT IT WOULD COST TO FIX, which is why it needs a decision rather than a patch: it requires choosing an eviction policy (LRU, or simply raising the cap), which is a design choice with its own cost measurement.

PERCEPTIBILITY, unmeasured and deliberately not claimed. Whether any real caller crosses 8 roots in one process is NOT established. The single production consumer is `run_viewer` (`aw runs`), which operates on one repo root per invocation, so the multi-root pattern may have no live trigger at all. Measure that before promoting this to `bug`: per AGENTS.md an unmeasured hunch that something feels slow is not a bug. The cold-versus-warm gap is large (this lane measured a cold `build_index` at about 7.4s against a warm hit at about 80ms, roughly 92x), so IF a live multi-root caller exists the impact would be user-perceptible; the open question is whether one does.
