- Id: rmcqw8
- Status: open
- Set: rmcqw8
- Priority: medium
- Work-Kind: followup
- Summary: the orchestrator coverage probe cannot see hazard prose stated OUTSIDE a checklist item, because payload and cache key must stay identical

## Workflow history
- 2026-09-19 created (aw backlog): the orchestrator coverage probe cannot see hazard prose stated OUTSIDE a checklist item, because payload and cache key must stay identical

The coverage gate landed by orchprobe-03 (m7gvuz) sends the orchestrator's checklist item action text plus its child table's row cells, and NOTHING else, because its E-03 requires the payload be EXACTLY the inputs probe_cache_digest keys on. That identity is load-bearing: a payload the key does not cover means editing that thing serves a STALE verdict under apparent authority, which is the one way the cache can be actively wrong rather than merely useless.

THE RESIDUAL GAP, stated plainly rather than hidden. The plan's stated reason for using a MODEL rather than a pattern match is that the dangerous case is PROSE. Prose inside an ITEM'S action text IS sent (and that is the shape the live corpus actually contains, measured at execution: 5e4sb6 E-01/E-02/E-03, wfjsp4 E-02/E-03/E-04, a5wdne E-01 and tb63qv E-01 all state their parent-only work inside item action text). Prose in a section OUTSIDE the checklist - a Goal or Concern paragraph saying 'before any child runs, someone must migrate the database' - is NOT sent, so the probe cannot see it.

WHY IT WAS NOT WIDENED IN THAT PLAN. Widening the payload without widening the digest breaks the identity above; widening BOTH changes a shipped cache's key shape, which is 8tgg6g's artifact and outside m7gvuz's Scope-Paths. The narrow-but-honest behavior was chosen over a wider-but-stale-serving one. The limit is PINNED by tests/test_orchestrator_probe.py::TheExcerptHasAKnownLIMIT, which fails loudly if someone widens the payload alone, and that test names the required simultaneous change.

WHAT CLOSING THIS LOOKS LIKE: extend probe_cache_payload (and therefore probe_cache_digest) to include the prose sections a coverage question can turn on, keeping the payload and key identical by construction, and re-prove the five xmqv5l no-op invariants in tests/test_orchestrator_probe_cache.py (a checkbox tick, a filled Observed evidence, an appended history line, and a prose edit OUTSIDE the newly-included sections must all still leave the digest unchanged). Note the tension to resolve: including prose sections deliberately re-introduces prose sensitivity that frozen_region_digest excludes on purpose, so the widening must be scoped to the sections that can carry the hazard rather than to the whole file, and the choice must be recorded.
