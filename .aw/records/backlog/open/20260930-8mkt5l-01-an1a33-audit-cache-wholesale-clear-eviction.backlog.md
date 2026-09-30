- Id: an1a33
- Status: open
- Set: 8mkt5l
- Priority: low
- Work-Kind: chore
- Summary: artifact_audit _INDEX_CACHE evicts by wholesale clear(), so crossing the cap discards every entry instead of one

## Workflow history
- 2026-09-30 created (aw backlog): artifact_audit _INDEX_CACHE evicts by wholesale clear(), so crossing the cap discards every entry instead of one

MEASURED 2026-09-30 at review of IPD dea7dr (F-09), re-measured independently by the reviewer in this lane.

THE BEHAVIOR. `artifact_audit.build_index` evicts with `if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX: _INDEX_CACHE.clear()`, so crossing the cap (`_INDEX_CACHE_MAX = 8`) discards ALL entries rather than evicting one. Measured by indexing 10 distinct temporary roots in sequence:

  MAX: 8 | cache size after 10 distinct roots: 2

So a multi-root caller rebuilds indexes it had cached moments earlier.

WHY IT IS NOT A STALENESS DEFECT. A cleared cache is SLOW, never WRONG, so this cannot produce the `missing_entirely` wrong answer that motivated dea7dr. It is filed separately for that reason and dea7dr left it deliberately alone.

WHAT IT WOULD COST TO FIX, which is why it needs a decision rather than a patch: it requires choosing an eviction policy (LRU, or simply raising the cap), which is a design choice with its own cost measurement.

PERCEPTIBILITY, unmeasured and deliberately not claimed. Whether any real caller crosses 8 roots in one process is NOT established. The single production consumer is `run_viewer` (`aw runs`), which operates on one repo root per invocation, so the multi-root pattern may have no live trigger at all. Measure that before promoting this to `bug`: per AGENTS.md an unmeasured hunch that something feels slow is not a bug. The cold-versus-warm gap is large (this lane measured a cold `build_index` at about 7.4s against a warm hit at about 80ms, roughly 92x), so IF a live multi-root caller exists the impact would be user-perceptible; the open question is whether one does.
