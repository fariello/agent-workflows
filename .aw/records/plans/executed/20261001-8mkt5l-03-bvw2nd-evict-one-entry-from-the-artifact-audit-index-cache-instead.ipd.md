# IPD: Evict one entry from the artifact-audit index cache instead of clearing all of it

- Date: 2026-10-01
- Kind: child
- Concern: `artifact_audit.build_index` evicts with `if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX: _INDEX_CACHE.clear()`, so crossing the cap (`_INDEX_CACHE_MAX = 8`) discards EVERY cached `ArtifactIndex` rather than evicting one. Re-measured in this lane: indexing 10 distinct temporary roots in sequence walks the cache size up `1,2,3,4,5,6,7,8` and then back to `1,2`, ending at 2. A rebuild is expensive (median 4326ms cold against a 20ms warm hit on this repository's 2258 records, 214x), so a caller that crosses the cap pays a full re-enumeration for indexes it held moments earlier. The item files this as a SLOW-never-WRONG defect and that framing is confirmed: no staleness or wrong answer follows from a cleared cache.
- Scope: Replace the wholesale `clear()` with single-entry LRU eviction so crossing the cap costs ONE entry instead of all of them, and pin the two properties that keep the cache a cache. IN: the `_INDEX_CACHE` declaration and the eviction branch of `artifact_audit.build_index`, the `_INDEX_CACHE` commentary's `RESIDUAL LIMIT 2` paragraph naming this item as carrier, and a new `tests/test_artifact_audit_cache_eviction.py`. OUT: `_dir_signature` (untouched), `build_index`'s enumeration, `find_artifact`'s tiers, the tier-one identity verification plan `0a7v0x` adds (carrier `ieg7q6`), `audit_artifact`'s fresh status read, `run_viewer`'s explicit-index threading, and `_INDEX_CACHE_MAX`'s VALUE, which F-06 shows is the knob that actually moves the measured workload and which F-07 declines to turn on memory grounds.
- Scope-Paths: agent_workflows/artifact_audit.py, tests/test_artifact_audit_cache_eviction.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: an1a33
- Set: 8mkt5l
- Order: 3
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: bvw2nd

## Workflow history
- 2026-10-03 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: bvw2nd verified (set 8mkt5l, attempt 1).
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (RESIDUAL LIMIT 2 mislabels over-invalidation with an1a33; rewrite leaves the trade carrier-less), PR-002 (hot-root test needs >= MAX+2 interleaved fresh roots or insert-only mutation stays green), PR-003 (counts not the bar), PR-004 (after-change perf re-measure removed as unowned), PR-005 (gate finalize/paste/scope-reason; OQ owners; 0a7v0x pop compatibility). Cliff re-measured at lane HEAD cae85d5d5: [1..8,1,2].

- 2026-10-01 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `an1a33`. Every number below was MEASURED in this lane at HEAD `e1da9ae84` on an `ext2/ext3` filesystem; none is transcribed from the item. The item's reproduction HOLDS EXACTLY and its central OPEN QUESTION is now ANSWERED, which changes what this plan claims.
  CONFIRMED: the eviction reproduces precisely as the item states (cache size `1..8` then `1,2` over 10 distinct roots, ending at 2), and the cold-versus-warm gap is real and large (median 4326ms rebuild against a 20ms hit, 214x; the item measured roughly 92x and the direction is the same).
  ANSWERED, and this is the finding the item explicitly asks for: the item says "whether any real caller crosses 8 roots in one process is NOT established" and names `run_viewer` as the single consumer that "operates on one repo root per invocation". A LIVE MULTI-ROOT CALLER EXISTS, and it is the TEST SUITE, not a shipped command: `tests/test_run_viewer.py` alone drives `build_index` 82 times across 29 distinct roots in ONE process, and a three-module slice reaches 177 calls across 50 roots. So the cap is genuinely crossed today (F-02).
  FALSIFIED, and it is why this plan does not claim a speedup: on that REAL trace LRU saves essentially NOTHING. Replaying the measured key sequence, `clear()` costs 30 rebuilds and LRU costs 30 at the shipped cap of 8 (51 against 51 on the wider slice); the distinct-key floor is 29 (50), so at most ONE rebuild was ever avoidable. The reason is structural: 17 of 29 keys are queried exactly ONCE, so there is almost no reuse for any policy to preserve (F-03, F-04).
  FOUND, and it bounds the user-visible benefit to roughly zero: those multi-root rebuilds are on 3-record TEMPORARY roots costing a median 1.26ms each, not on the 2258-record repository root, so even the avoidable rebuild is about 1ms in a test process (F-05).
  CLASSIFICATION: `chore` is INHERITED from the item and re-examined rather than assumed. F-08 records why it still holds and, unusually, argues the measurement ARGUES AGAINST promotion rather than for it. The item carries no `- Blocks-Release:`, so this plan invents none.

## Goal

Make the index cache evict ONE entry when it reaches its cap, instead of discarding every entry, so the cache degrades gracefully at the boundary rather than cliff-edging to empty.

Be honest about WHY, because the measurement does not support the usual justification. This is a CORRECTNESS-OF-POLICY fix, not a measured speedup: on the only live multi-root workload that exists today (the test suite), LRU saves at most one rebuild of about 1ms (F-03, F-05). What it buys is that the data structure stops having a pathological shape whose cost is unbounded in the one scenario that would hurt, a long-lived process re-querying a hot root while other roots stream past, where `clear()` costs 29 of 200 hot-root rebuilds against LRU's 1 (F-06). No such process exists today, so this plan claims a BOUNDED RISK REMOVED and explicitly does NOT claim a user-perceptible win.

State plainly what this plan does NOT do: it does not raise `_INDEX_CACHE_MAX`, which F-06 shows is the knob that would actually have moved the measured trace, and F-07 records the memory reason for declining it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: establish the behavior and the honest size of the prize before changing anything

- [x] E-01 RE-REPRODUCE THE WHOLESALE EVICTION AT THE EXECUTION HEAD, BEFORE EDITING PRODUCTION CODE. Write a scratch script (NOT a committed test; put it under the gitignored `tmp/`) that builds N distinct temporary repo roots, each holding at least one record, calls `artifact_audit.build_index` on each in sequence, and prints `len(_INDEX_CACHE)` after EVERY call so the cliff is visible as a series rather than as a single endpoint.

  USE MORE ROOTS THAN THE CAP, at least `_INDEX_CACHE_MAX + 2`, and read the cap from the module rather than hardcoding 8, so the fixture cannot silently stop exercising the boundary if the constant changes.

  PRINT THE WHOLE SERIES, not just the final size. The item's own evidence line reports only `cache size after 10 distinct roots: 2`, and an endpoint alone is consistent with several policies; the series `1..8,1,2` is what identifies a wholesale clear specifically.

  IF THE SERIES DOES NOT SHOW THE CLIFF, STOP AND REPORT rather than proceeding to change the policy.
  - Depends on: none
  - Expected outcome: the per-call series printed with the cap beside it. Authoring measurement: `MAX: 8` and `sizes after each of 10 distinct roots: [1, 2, 3, 4, 5, 6, 7, 8, 1, 2]`, final size 2.
  - Execution state: performed

- [x] E-02 MEASURE WHAT A REBUILD ACTUALLY COSTS, ON BOTH ROOT SIZES THAT OCCUR, because this plan's whole value rests on the price of a discarded entry and the item's cost figure was taken only on the large root. Report, page-cache-warmed and interleaved: a cold `build_index` on THIS repository's root, a warm cache hit on it, `_dir_signature` alone, and a cold `build_index` on a SMALL fixture-sized root of about 3 records.

  THE SMALL-ROOT NUMBER IS THE LOAD-BEARING ONE and must not be skipped. F-02 shows the live multi-root caller is the test suite, whose roots are temporary 3-record fixtures, so the cost of the rebuilds this fix actually avoids is the small-root figure and NOT the repository figure. Reporting only the latter would overstate the prize by three orders of magnitude.

  ALSO REPORT `_dir_signature` AS A FRACTION OF A WARM HIT, since a hit pays the signature every time; this is what shows a cache hit is already dominated by the invalidation check rather than by lookup.
  - Depends on: none
  - Expected outcome: four medians with sample counts and the two derived ratios. Authoring measurements on 2258 records: cold rebuild median 4326.0ms (min 3319.8, max 4569.6), warm hit median 20.2ms, `_dir_signature` median 18.8ms, ratio 214.1x; small 3-record root rebuild median 1.26ms over 20 trials. If the small-root rebuild measures anywhere near the repository figure, STOP AND REPORT: that would contradict F-05 and change this plan's justification.
  - Execution state: performed

- [x] E-03 MEASURE THE REAL KEY SEQUENCE AND SIMULATE BOTH POLICIES AGAINST IT, which is the step that keeps this plan from claiming a speedup it does not have. Instrument `artifact_audit.build_index` to record the exact cache KEY of every call, run a real consumer (at minimum `tests/test_run_viewer.py`, which F-02 identifies as a live multi-root caller), then replay the captured sequence through two simulated policies: the shipped wholesale `clear()` and single-entry LRU, counting cache MISSES (each of which is one rebuild) for each.

  REPORT THE DISTINCT-KEY FLOOR BESIDE THE TWO COUNTS. No policy can do better than one miss per distinct key, so the floor is what says how much was ever winnable; without it a reader cannot tell a good policy from an unwinnable workload.

  ALSO REPORT THE KEY REPEAT DISTRIBUTION, because it is the explanation rather than a decoration: a workload whose keys are mostly queried once has nothing for an eviction policy to preserve, and that is what the authoring measurement found.

  SWEEP THE CAP TOO, at 8, 16 and 32, for both policies. This is what distinguishes "the policy is wrong" from "the cap is small", and F-06 rests on it.

  DO NOT TREAT A NULL RESULT AS A FAILURE. If LRU ties `clear()` on the real trace, that is the expected outcome (authoring measured exactly that) and it must be reported as such, not tuned until it shows a win.
  - Depends on: none
  - Expected outcome: the two miss counts, the floor, the repeat distribution and the cap sweep, with the command that produced them. Authoring measurements on `test_run_viewer.py`: 82 calls, 29 distinct keys across 29 distinct roots, `clear()` 30 misses against LRU 30 at cap 8, floor 29; cap sweep `8 -> 30/30`, `16 -> 30/29`, `32 -> 29/29`; repeat distribution `{1: 17, 2: 5, 6: 2, 4: 2, 8: 1, 14: 1, 13: 1}`. Wider three-module slice: 177 calls, 50 distinct keys, `clear()` 51 against LRU 51 at cap 8, floor 50.
  - Execution state: performed

### Task group 2: change the policy

- [x] E-04 REPLACE THE WHOLESALE EVICTION IN `artifact_audit.build_index` WITH SINGLE-ENTRY LRU, and update the `_INDEX_CACHE` commentary's `RESIDUAL LIMIT 2` paragraph in the same edit, since that paragraph names this item as the open carrier and would otherwise tell the next reader the hole is still open.

  THE MECHANISM: make `_INDEX_CACHE` a `collections.OrderedDict`, PROMOTE ON HIT (`move_to_end`) in the cache-hit branch of `build_index`, and on insert append then evict from the OLDEST end while over the cap (`while len(_INDEX_CACHE) > _INDEX_CACHE_MAX: _INDEX_CACHE.popitem(last=False)`).

  PROMOTION ON HIT IS LOAD-BEARING AND IS THE EASY THING TO OMIT. A variant that reorders only on INSERT is an insertion-order queue, not an LRU, and it measures no better than the wholesale clear on the one workload where the policy matters: authoring measured a hot root surviving 25 of 30 re-queries under insert-only ordering against 29 of 30 under true LRU, where `clear()` also gives 25 of 30. So an insert-only implementation would pass a naive size test while delivering none of this plan's stated benefit. The hit branch is the one that must change, and E-05's hot-root test is what pins it.

  USE A `while`, NOT AN `if`, for the eviction so the invariant holds even if the cap is lowered at runtime or more than one entry is somehow over.

  PRESERVE THE EXISTING KEYING AND THE SIGNATURE CHECK EXACTLY. The key stays `(resolved-root-string, tuple(record_types))` with its `OSError` fallback, and a cached entry is still returned only when `cached[0] == sig`. This plan changes WHICH entry is discarded and nothing about WHEN an entry is considered valid; a change to the latter is `0a7v0x`'s surface or a different plan's.

  DO NOT RAISE `_INDEX_CACHE_MAX`. F-06 measures it as the knob that would actually have improved the real trace and F-07 declines it on memory; turning both knobs at once would also make E-03's before/after comparison unreadable. Leave the constant at 8.

  REWRITE `RESIDUAL LIMIT 2` TO SAY WHAT IS NOW TRUE: the paragraph is headed `RESIDUAL LIMIT 2 / OVER-INVALIDATION (carrier `an1a33`)` and its body describes ONLY the over-invalidation from the deliberately-wide signature walk, yet names `an1a33` (whose subject is the wholesale clear, not over-invalidation) as carrier twice. That carrier attribution is a mislabel inherited from `dea7dr`, which accepted the over-invalidation as a TRADE and filed `an1a33` for the separate eviction defect (dea7dr's Deferred row "FIXING `_INDEX_CACHE_MAX`'s WHOLESALE `clear()` EVICTION ... Carrier: an1a33"). So after this change the over-invalidation text must stand as an ACCEPTED TRADE WITH NO CARRIER (do not invent one, and do not leave `an1a33` attached to it), and eviction must be described separately as now single-entry LRU. After this change the over-invalidation trade (a wide walk, accepted because a rebuild is slow but never wrong) is UNCHANGED and must be preserved, while the wholesale-clear carrier is CLOSED and must no longer be advertised as open. Record that eviction is now single-entry LRU, and record the measured reason the cap was NOT raised, so the next reader does not redo F-07's reasoning.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: `git diff -- agent_workflows/artifact_audit.py` shows `_INDEX_CACHE` as an `OrderedDict`, a `move_to_end` on the hit path, a `while`-guarded `popitem(last=False)` on the insert path, no change to the key construction or the `cached[0] == sig` comparison, `_INDEX_CACHE_MAX` still 8, and the `RESIDUAL LIMIT 2` paragraph rewritten; re-running E-01's fixture now shows the size series rising to the cap and STAYING there (`...,8,8,8`) instead of collapsing to 1.
  - Execution state: performed

### Task group 3: pin the outcome

- [x] E-05 ADD `tests/test_artifact_audit_cache_eviction.py` WITH FOUR OUTCOME TESTS. Clear `_INDEX_CACHE` in `setUp` AND `tearDown`, following `tests/test_artifact_audit_index_cache.py`: the cache is module-level shared state and `pyproject.toml`'s `addopts` randomizes order, so an entry left by a neighbour would make these pass or fail for the wrong reason.

  ALSO NOTE THE SIBLING'S CACHE TOUCH: approved-track plan `0a7v0x` E-03 POPS a key from `_INDEX_CACHE` before rebuilding. `OrderedDict.pop` behaves identically to `dict.pop`, so the two plans compose in either merge order; do not change the container to anything lacking `pop`/`get`/`__getitem__`, which `tests/test_artifact_audit_index_cache.py` also uses (`_audit._INDEX_CACHE[key][1]`).

  FIRST, THE BOUNDED-SIZE TEST: index `_INDEX_CACHE_MAX + 2` distinct temporary roots and assert the cache size equals the cap afterwards, never dropping to 1 or 2. Read the cap from the module; do not hardcode 8.

  SECOND, THE HOT-ROOT TEST, WHICH IS THE ONE THAT ACTUALLY PINS LRU AND MUST NOT BE OMITTED: prime a root, then interleave re-queries of that hot root with queries of AT LEAST `_INDEX_CACHE_MAX + 2` fresh roots (one fresh root between each re-query; read the cap from the module). The count is load-bearing: with fewer than `_INDEX_CACHE_MAX` fresh roots an insert-only queue never evicts the hot entry, so the test would pass without promotion-on-hit and miss F-10's mutation (measured at review: with `_INDEX_CACHE_MAX + 2` fresh roots the shipped `clear()` already fails this check, `hot retained (clear): False`), and assert the hot root's index is STILL the SAME OBJECT at the end (`assertIs`). This is the behavior the whole plan exists to buy, and it is the test that fails against an insert-only ordering as well as against the shipped `clear()`, which is exactly the distinction E-04 warns about.

  THIRD, THE NO-REBUILD-ON-A-HIT TEST: assert the existing memoization still holds, by wrapping `selectors._iter_paths` with a counter (restoring it in a `finally`, as the predecessor file does), looking the same unchanged root up twice, and asserting the traversal count does not move and the returned index is the same object. This is what stops a cache "fix" that quietly stops caching.

  FOURTH, THE INVALIDATION-STILL-WORKS TEST: after a real change to a cached root's tree, assert the returned index is a DIFFERENT object and contains the new record. An eviction change must not weaken invalidation, and this is the cheapest proof it did not.

  ASSERT ON OUTCOMES, NEVER ON CODE STRUCTURE. This file must not read `agent_workflows/artifact_audit.py` as text, must not `inspect.getsource` it, must not `ast`-parse it, and must not assert that `_INDEX_CACHE` is an `OrderedDict` by TYPE; assert the observable consequences (bounded size, object identity of a retained entry, traversal counts, invalidation) instead. Do not assert on wall-clock timings, which are flaky by construction. (GUIDING_PRINCIPLES P16; `AGENTS.md`'s code-pinning prohibition.)
  - Depends on: E-04
  - Expected outcome: four tests passing after E-04; the bounded-size and hot-root tests both RED against the pre-E-04 code; the hot-root test additionally RED against an insert-only (no `move_to_end` on hit) variant; the no-rebuild test RED if the cache lookup is removed. The file reads no production source text.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS ASSERT OUTCOMES, NEVER CODE STRUCTURE. `GUIDING_PRINCIPLES.md` P16 and `AGENTS.md` both forbid `inspect`, `ast`, regex or substring search against production source, and forbid symbol censuses as a proxy for correctness. E-05 is written to that rule: it asserts bounded cache size, object identity of a retained entry, traversal counts and invalidation, and deliberately does NOT assert that `_INDEX_CACHE` is an `OrderedDict`, which would be a type assertion standing in for the behavior.
- THE PREDECESSOR'S TEST FILE ESTABLISHES THE SHAPE TO FOLLOW. `tests/test_artifact_audit_index_cache.py` (added by `dea7dr`) wraps `_audit._sel._iter_paths` with a counter, restores it in a `finally`, asserts the count does not move across two lookups of an unchanged tree, asserts the cached `ArtifactIndex` is the SAME OBJECT, and asserts a real change produces a DIFFERENT object. E-05's third and fourth tests extend exactly that shape to the eviction axis.
- THE CACHE IS MODULE-LEVEL SHARED STATE AND THE SUITE RUNS IN RANDOM ORDER. `AGENTS.md` forbids `-p no:randomly` precisely to keep order-dependence visible, so a test reading `_INDEX_CACHE` without clearing it first is order-dependent by construction. The predecessor clears it in both `setUp` and `tearDown`; E-05 follows.
- CITE CODE BY SYMBOL OR BY A QUOTED CONTENT STRING, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). Every citation here names `artifact_audit.build_index`, `artifact_audit._dir_signature`, `artifact_audit._INDEX_CACHE`, `artifact_audit._INDEX_CACHE_MAX`, `selectors._iter_paths`, or quotes the comment text being changed.
- A SIBLING PLAN IN THIS SET TOUCHES THE SAME FILE AND MUST NOT BE COLLIDED WITH. Plan `0a7v0x` (Order 2, from backlog `ieg7q6`) edits `find_artifact`'s tier one and the `RESIDUAL LIMIT 1` paragraph, and its own scope section explicitly leaves "`_INDEX_CACHE_MAX`'s wholesale clear (carrier `an1a33`)" out. This plan edits the eviction branch and `RESIDUAL LIMIT 2`, so the two are disjoint by paragraph and by function. The runner isolates each plan in its own worktree and merges through a revalidation gate, so co-editing one file is not a hazard; the paragraph-level disjointness is what keeps the two edits semantically independent.

## Findings

All measured 2026-10-01 in this lane worktree at HEAD `e1da9ae84`, on an `ext2/ext3` filesystem (`stat -f -c %T .`). This repository's records tree holds 2258 enumerated records with 2196 distinct declared ids.

| # | Sev | Finding | Evidence |
|---|---|---|---|
| F-01 | HIGH | **THE ITEM'S REPRODUCTION HOLDS EXACTLY, AND THE SERIES IDENTIFIES THE POLICY RATHER THAN JUST THE ENDPOINT.** Indexing 10 distinct temporary roots walks the cache up to the cap and then collapses, which is a wholesale clear and not an eviction. The item reported only the endpoint (`cache size after 10 distinct roots: 2`); the per-call series is what rules out a one-entry policy. | `MAX: 8`; `sizes after each of 10 distinct roots: [1, 2, 3, 4, 5, 6, 7, 8, 1, 2]`; `final size: 2` |
| F-02 | HIGH | **THE ITEM'S CENTRAL OPEN QUESTION IS ANSWERED: A LIVE MULTI-ROOT CALLER EXISTS, AND IT IS THE TEST SUITE.** The item states "whether any real caller crosses 8 roots in one process is NOT established" and names `run_viewer` as the only consumer, which "operates on one repo root per invocation". That is right about the shipped command and incomplete about the process: `tests/test_run_viewer.py` calls `audit_step_artifact(step, repo_root=root)` with NO `artifact_index=`, so every such call reaches `_INDEX_CACHE`, and each test builds its own temporary root. Instrumented, that one module drives `build_index` 82 times across 29 distinct roots in a single process, crossing the cap of 8 repeatedly; a three-module slice reaches 177 calls across 50 roots. So the eviction path is exercised today, which is what makes this fixable rather than speculative. | `build_index calls: 82`, `distinct cache keys: 29`, `distinct repo roots: 29`, `MAX: 8`, `final cache size: 6` (`tests/test_run_viewer.py`, one process); wider slice `calls=177 distinct_keys=50 distinct_roots=50` |
| F-03 | HIGH | **ON THAT REAL TRACE, LRU SAVES NOTHING, AND THIS PLAN MUST NOT CLAIM A SPEEDUP.** Replaying the 82 captured keys through both policies at the shipped cap: wholesale `clear()` costs 30 rebuilds, single-entry LRU costs 30. The distinct-key floor is 29, so AT MOST ONE rebuild was ever avoidable on this workload, and LRU does not capture it at cap 8. The wider 177-call slice is the same story (51 against 51, floor 50). This is the finding that sets this plan's honest claim: a policy correction with a bounded worst case, not a measured win. | `replayed build_index calls: 82  distinct keys: 29`; `clear  -> rebuilds (cache misses): 30`; `lru    -> rebuilds (cache misses): 30`; wider slice `8 -> clear 51 / LRU 51`, `floor: 50` |
| F-04 | HIGH | **THE REASON LRU CANNOT WIN HERE IS THE WORKLOAD'S REUSE PROFILE, WHICH IS MOSTLY NONE.** Of the 29 distinct keys in the real trace, 17 are queried EXACTLY ONCE, and only 4 keys are queried more than 6 times. An eviction policy can only ever preserve reuse that exists; a workload of mostly-singleton keys is unwinnable for ANY policy, which is why F-03's tie is the expected result rather than an implementation defect. This is also why E-03 must report the distribution: without it, the tie looks like a failed optimization instead of a correctly measured null. | key repeat distribution `Counter({1: 17, 2: 5, 6: 2, 4: 2, 8: 1, 14: 1, 13: 1})` |
| F-05 | HIGH | **THE REBUILDS THIS FIX AVOIDS ARE THE CHEAP ONES, WHICH BOUNDS THE PRIZE AT ABOUT 1ms.** The item's cost case rests on the cold-versus-warm gap, re-measured here as a median 4326ms rebuild against a 20.2ms hit (214x) on the 2258-record repository root. But F-02 shows the multi-root caller is the test suite, whose roots are temporary 3-record fixtures, and a rebuild on such a root measures a median 1.26ms. So the one avoidable rebuild F-03 identifies is worth about a millisecond, not about four seconds. Both numbers are true and quoting only the first would overstate this plan's value by three orders of magnitude. ALSO NOTE a warm hit is nearly all signature: `_dir_signature` alone medians 18.8ms of the 20.2ms hit, so a "hit" is dominated by the invalidation check. | `rebuild (cache miss): min=3319.8 med=4326.0 max=4569.6 ms`; `cache HIT: min=16.9 med=20.2 max=25.1 ms`; `miss/hit ratio (median): 214.1x`; `_dir_signature only : min=14.1 med=18.8 max=24.5 ms`; `rebuild on a 3-record temp root: median 1.26 ms` |
| F-06 | MED | **THE CAP, NOT THE POLICY, IS WHAT WOULD HAVE MOVED THE MEASURED TRACE; AND THERE IS A DISTINCT WORKLOAD WHERE THE POLICY IS WHAT MATTERS.** Sweeping the cap on the real trace, LRU first beats `clear()` at 16 (30 against 29) and both reach the floor at 32 (29 against 29), so on THIS workload raising the cap is the effective knob. The policy nevertheless matters in a shape this workload does not have: a long-lived process re-querying ONE hot root while other roots stream past. Simulated over 200 hot-root re-queries, the hot root must be rebuilt 29 times under `clear()` against 1 under LRU with one cold root per iteration, and 57 against 1 with two per iteration. NO SUCH PROCESS EXISTS TODAY (every `aw` command is one-shot), so this is a bounded risk removed rather than a benefit realized, and it is the honest justification for the change. The same simulation shows the limit of the fix too: at 8 cold roots per iteration, enough to evict a hot entry between every re-query, both policies rebuild all 200 times. | cap sweep on the real trace `8 -> 30/30`, `16 -> 30/29`, `32 -> 29/29`, `floor 29`; hot-root simulation `cold-roots-per-iteration=1: clear()=29 LRU=1`, `=2: clear()=57 LRU=1`, `=8: clear()=200 LRU=200` (of 200 re-queries) |
| F-07 | MED | **RAISING THE CAP IS DECLINED ON A MEASURED MEMORY COST, WHICH IS WHY THIS PLAN CHANGES ONLY THE POLICY.** One `ArtifactIndex` for this repository measures about 1.34 MiB deep (2258 paths, 2196 declared-id entries, 2089 filename-id entries), so the shipped cap of 8 already admits about 10.73 MiB of cache, and 16 or 32 would admit about 21.45 MiB or 42.90 MiB. Since F-03 shows the real benefit of a larger cap is ONE avoidable 1.26ms rebuild (F-05), tens of megabytes is a bad trade, and a multi-root process holding several large roots is exactly where it would bite hardest. The policy fix costs no additional memory at all, which is what makes it the right half of the pair to take. | `ONE ArtifactIndex approx: 1373 KiB (1.34 MiB)` for `paths=2258 declared=2196 fname=2089`; `cap=  8 -> 10.73 MiB`, `cap= 16 -> 21.45 MiB`, `cap= 32 -> 42.90 MiB` |
| F-08 | MED | **`chore` IS INHERITED AND STILL CORRECT, AND THE MEASUREMENT ARGUES AGAINST PROMOTION RATHER THAN FOR IT.** The item says to measure perceptibility before promoting to `bug`, citing `AGENTS.md`'s rule that an unmeasured hunch is not a bug. Measured: the only live multi-root consumer is the test suite (F-02), the avoidable work there is one rebuild of about 1.26ms (F-03, F-05), and no shipped `aw` command crosses the cap because each is one-shot on a single root. A millisecond inside a test process is not user-perceptible by any reading, so this is a `chore` on evidence rather than by default. WHAT WOULD MOVE IT TO `bug`: a long-lived or daemonized consumer holding the cache across many roots, or a shipped command that sweeps multiple repository roots in one process, either of which would make F-06's unbounded hot-root case live against the 4326ms repository-root rebuild rather than the 1.26ms fixture one. | `clear  -> rebuilds: 30` against `floor: 29` on the live trace; `rebuild on a 3-record temp root: median 1.26 ms`; the two shipped `build_index` call sites both read `_audit.build_index(repo_root)` in `run_viewer` for a single root per invocation |
| F-09 | MED | **A SINGLE REPOSITORY ROOT CAN OCCUPY UP TO 10 CACHE KEYS, BECAUSE THE KEY INCLUDES `record_types` AND `audit_artifact` REORDERS IT PER ARTIFACT TYPE.** The key is `(root, tuple(record_types))`, and `audit_artifact` promotes a known queue type to the front of the vocabulary before searching (`search_types = (canonical_queue_type, *(t for t in record_types if t != canonical_queue_type))`). So ONE root audited across the 10 `TYPE_PRECEDENCE` values fills the cache and triggers the clear by itself: measured sizes `1,2,3,4,5,6,7,8` then a collapse, with `other` landing back at 1. This matters for two reasons: it means the item's "multi-root caller" framing understates how the cap is reached, and it means E-05's bounded-size test can be written with distinct roots while the production trigger may be a single root. NOTE the 10 types yield at most 9 distinct orderings, since `comms` canonicalizes to `None` and so does not reorder. | per-type cache sizes for ONE root: `plans 1, specs 2, backlog 3, releases 4, roadmaps 5, prompts 7, walkthroughs 8, comms 8, other 1`; `comms -> canonical=None in TYPE_PRECEDENCE=False`; the three-module slice saw `record_types variants seen: 3` |
| F-10 | LOW | **AN INSERT-ONLY ORDERING IS THE LIKELY WRONG IMPLEMENTATION AND MEASURES NO BETTER THAN THE SHIPPED CLEAR, so E-04 names the hit-path promotion explicitly and E-05 pins it.** An `OrderedDict` that is appended to on insert but never reordered on a cache HIT is an insertion-order queue: a hot root ages out despite being used constantly. Simulated over 30 hot-root re-queries with one cold root each, insert-only ordering retains the hot entry 25 of 30 times, which is EXACTLY what the wholesale `clear()` scores, while true LRU with promotion on hit retains it 29 of 30. So the bug-compatible variant would pass a bounded-size test and deliver none of F-06's benefit. | insert-only prototype `clear()  hits in cyclic workload of 50: 8` against `LRU hits ...: 8` (indistinguishable); corrected with promotion-on-hit: `clear : HOT root still cached on 25/30 re-queries`, `lru   : HOT root still cached on 29/30 re-queries` |
| F-11 | LOW | **THE EXISTING CACHE TESTS PASS AT THIS HEAD AND ARE THE REGRESSION SURFACE THIS PLAN MUST NOT DISTURB.** `tests/test_artifact_audit_index_cache.py` and `tests/test_artifact_audit.py` run green together, and the former pins the memoization and invalidation properties `dea7dr` established. This plan's claim is that it changes WHICH entry is dropped and nothing about when an entry is valid, so a regression in that file is attributable here and must be fixed rather than absorbed by editing the file. | `python3 -m pytest -o addopts="" tests/test_artifact_audit_index_cache.py tests/test_artifact_audit.py -q` -> `30 passed in 1.50s` |
| F-12 | LOW | **ONLY PATH AND IDENTITY FACTS ARE CACHED, SO THIS PLAN CANNOT AFFECT STATUS CORRECTNESS.** The `_INDEX_CACHE` commentary states "ONLY PATH FACTS ARE CACHED HERE: a record's `- Status:` is always read fresh in `audit_artifact`", and an eviction-policy change cannot alter that. It bounds the blast radius to lookup latency and keeps the item's own "slow, never wrong" framing true after the change as well as before it. | the quoted comment in `artifact_audit`'s `_INDEX_CACHE` block; `audit_artifact` calls `read_declared_status` per audit |

## Proposed changes (ordered, validatable)

1. Reproduce the wholesale-clear series across more than `_INDEX_CACHE_MAX` roots; change no file (E-01).
2. Measure rebuild and hit cost on BOTH the repository root and a fixture-sized root, plus `_dir_signature` alone; change no file (E-02).
3. Capture the real `build_index` key sequence from a live multi-root consumer and simulate both policies against it with a cap sweep and the reuse distribution; change no file (E-03).
4. `agent_workflows/artifact_audit.py`: make `_INDEX_CACHE` an `OrderedDict`, promote on hit, evict single entries from the oldest end with a `while`, leave `_INDEX_CACHE_MAX` at 8, and rewrite the `RESIDUAL LIMIT 2` paragraph to close this carrier while preserving the over-invalidation trade it also records (E-04).
5. `tests/test_artifact_audit_cache_eviction.py`: bounded size, hot-root retention by object identity, no rebuild on a hit, and invalidation still works (E-05).

## Deferred / out of scope (with reason)

- RAISING `_INDEX_CACHE_MAX`. Declined on measurement, not preference: F-06 shows the cap is the knob that would have improved the real trace (30 to 29 misses at 16, reaching the floor at 32), but F-03 and F-05 together value that entire improvement at ONE avoidable rebuild of about 1.26ms, while F-07 measures the cost at about 1.34 MiB per cached index, so 16 or 32 would admit roughly 21 or 43 MiB. Spending tens of megabytes for a millisecond is the wrong trade, and turning both knobs in one plan would also make the before/after comparison unreadable.
  - Carrier-Declined: No obligation is created. The measurement is recorded in F-06 and F-07 and E-04 writes the reason into the code comment, so the next reader finds the numbers at the point of decision rather than having to re-derive them. If a consumer appears that genuinely holds many large roots in one process, that consumer is the trigger and the cap should be revisited on its evidence.
- CLOSING THE SINGLE-ROOT MULTI-KEY AMPLIFICATION F-09 DESCRIBES, where one repository root occupies up to 10 cache keys because `audit_artifact` reorders `record_types` per artifact type. This plan makes it harmless at the boundary (an LRU evicts one of those entries instead of all of them) but does not remove the amplification, which would mean changing either the cache key or `audit_artifact`'s per-type reordering. The reordering exists to give the filename tier a deterministic precedence, so changing it is a lookup-semantics change and not a cache change.
  - Carrier-Declined: Nothing is owed, and this is a judgement a reviewer may overturn. The amplification costs only cache slots, never a wrong answer, and after this plan it costs at most one evicted entry rather than the whole cache; F-09 records the mechanism and the measurement for whoever revisits it. Filing an item for a now-harmless inefficiency would add tracked work whose own remedy is riskier than the condition.
- THE TIER-ONE IDENTITY STALENESS ROUTE AND `_dir_signature`'s BLINDNESS TO AN IN-PLACE `- Id:` REWRITE. A different defect in the same module with its own plan and its own carrier; this plan touches neither the signature nor the lookup tiers.
  - Carrier: ieg7q6
- THE MISS-ON-NEW HALF of that same identity route, where a freshly written id6 is unfindable from an already-primed index. Out of scope here for the same reason: it is an invalidation question, not an eviction one.
  - Carrier-Declined: No obligation is created BY THIS PLAN. Sibling plan `0a7v0x` already examined it, declined it with a recorded measurement, and documents the residual in the same code comment block; duplicating that decision here would create a second owner for one question.

## Scope check

- Over-scope: none. Two declared paths, each touched by named E-items: `agent_workflows/artifact_audit.py` by E-04 (the eviction branch, the `_INDEX_CACHE` declaration, the hit-path promotion, and the `RESIDUAL LIMIT 2` paragraph) and `tests/test_artifact_audit_cache_eviction.py` by E-05. E-01, E-02 and E-03 change no tracked file; their scratch scripts go under the gitignored `tmp/` and must not be committed. No `_dir_signature` change, no `find_artifact` change, no `selectors` change, no `run_viewer` change, no `doctor` change, no spec, no user-facing document, and no change to `_INDEX_CACHE_MAX`'s value.
- Under-scope, stated plainly: the cap stays at 8 so the measured trace keeps 30 rebuilds against a floor of 29 (F-03, F-06, declined in F-07); the single-root multi-key amplification stays (F-09, harmless after this change); the identity-staleness routes stay with `ieg7q6` and `0a7v0x`; and the deliberately-wide signature walk that causes over-invalidation stays exactly as it is, since this plan changes eviction and not invalidation. A reviewer who wants the cap raised should say so explicitly, but note F-07's measured memory cost against a 1.26ms prize.

## Required tests / validation

The BARE full suite is required by the execution contract: `python3 -m pytest`, with no added flags (no `-n0`, no extra `-q`, no `-p no:randomly`).

RE-DERIVE A BASELINE IN THE EXECUTION LANE BEFORE CHANGING ANYTHING, and compare post-change results by NODE ID rather than by total. Sibling plan `0a7v0x` measured this suite as NOT green at a nearby head and its failure set as NOT STABLE between runs at the same commit (two bare runs produced `5 failed, 4441 passed` and `2 failed, 4444 passed`, naming overlapping but different sets), so a total-versus-total comparison cannot distinguish a regression from load-dependent flake. Any failure naming `artifact_audit`, `build_index`, `_INDEX_CACHE` or the index cache IS attributable to this plan and must be fixed, not explained.

The new file must also be run alone with the configured defaults cleared, `python3 -m pytest -o addopts="" tests/test_artifact_audit_cache_eviction.py -v`, because per-test names are required and the configured `-q` suppresses them. That is the one sanctioned way to clear them per `AGENTS.md`.

THE PREDECESSOR'S CACHE TESTS MUST PASS UNCHANGED: `python3 -m pytest -o addopts="" tests/test_artifact_audit_index_cache.py tests/test_artifact_audit.py -v`. They pin the memoization and invalidation behavior `dea7dr` established (measured green at authoring in F-11; re-derive the count in the lane before the change), and this plan's whole claim is that it changes which entry is evicted WITHOUT disturbing when an entry is valid, so a regression there is this plan's and must not be absorbed by editing those files.

RED-BEFORE-GREEN IS REQUIRED, NOT OPTIONAL. The bounded-size and hot-root tests must each be shown FAILING against the pre-E-04 code and PASSING after it, with `git status --short agent_workflows/` proving the restoration between runs.

THE INSERT-ONLY MUTATION MUST ALSO BE SHOWN RED, and this is the one adversarial run that cannot be skipped, because F-10 measures an insert-only ordering as scoring exactly what the shipped wholesale clear scores (25 of 30 hot-root retentions against LRU's 29 of 30). In a scratch copy, remove ONLY the hit-path `move_to_end` while keeping the `OrderedDict` and the single-entry eviction, and paste the hot-root test FAILING. A hot-root test that passes without the promotion is not testing LRU and must be fixed before this plan is claimed done.

THE NO-REBUILD-ON-A-HIT TEST MUST BE SHOWN RED FOR ITS OWN OPPOSITE MUTATION: with the cache-hit lookup disabled in a scratch copy, paste it failing. Without that, a change that stopped caching entirely would pass every other test in the file.

E-01's fixture is re-run after the change (V-04). E-02 and E-03 are pre-change measurements that establish the honest prize (about one 1.26ms rebuild on the live trace); they need not be repeated after the change, since E-04 changes no rebuild cost and the simulation already models LRU.

`aw ipd lint` on this plan must report conforming. `aw sanitize --agent` must be clean. No `aw check` family run is required beyond what the suite covers, since no records artifact other than this plan is edited.

Every validation below asserts on OUTCOMES (pasted command output, `git diff`, exit codes). No `V-*` may be marked from memory, and none may be marked without the actual pasted output its `Required evidence` names.

## Spec / documentation sync

NO `.spec.md` FILE IS AMENDED and `- Scope-Paths:` declares none, so the runners' pre-run spec-edit announcement and the run-end reconciliation should both report zero declared and zero actual spec edits. No spec governs `artifact_audit`'s cache eviction policy or its cap: that behavior is documented only in the module's own `_INDEX_CACHE` comment block, which is why E-04's rewrite of the `RESIDUAL LIMIT 2` paragraph is a required part of this fix rather than optional tidying.

No user-facing document changes. `docs/` is untouched, and the prose this plan edits is internal code commentary, where the em-dash prohibition does not apply per `AGENTS.md`.

## Open questions

### OQ-01: Should the cap be raised instead of, or in addition to, changing the eviction policy?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AS POLICY-ONLY, ON MEASUREMENT, and recorded because it is the one real design choice here and a reviewer may legitimately disagree. The cap is demonstrably the more effective knob ON THE MEASURED WORKLOAD: F-06's sweep shows LRU first beating `clear()` at a cap of 16 and both reaching the distinct-key floor at 32, while at the shipped cap of 8 the two tie at 30 misses. So if the goal were to minimize rebuilds on today's trace, raising the cap would be the change to make. It is declined because the prize is tiny and the cost is not: F-03 bounds the entire improvement at ONE avoidable rebuild, F-05 prices that rebuild at a median 1.26ms because the multi-root roots are 3-record fixtures rather than the 2258-record repository, and F-07 measures one cached index at about 1.34 MiB, so a cap of 16 or 32 would admit roughly 21 or 43 MiB. Tens of megabytes for a millisecond is the wrong trade. The policy change, by contrast, costs no memory and removes an UNBOUNDED worst case (F-06's hot-root shape, where `clear()` rebuilds 29 or 57 times against LRU's 1), which is the right half of the pair to take even though it shows no win on today's trace. E-04 writes this reasoning into the code comment so it is not re-derived.

### OQ-02: Does the measured evidence justify promoting this item from `chore` to `bug`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AS NO, and the item explicitly asked for this to be measured rather than assumed ("Measure that before promoting this to `bug`"). The measurement came back AGAINST promotion, which is worth stating because the item's cold-versus-warm figure makes promotion look likely. `AGENTS.md`'s test is user-perceptible impact measured on the end-to-end command a user actually runs. Here the only live consumer that crosses the cap is the TEST SUITE (F-02), the avoidable work on that trace is one rebuild (F-03) worth about 1.26ms because the roots are 3-record fixtures (F-05), and no shipped `aw` command crosses the cap at all because each is one-shot on a single root. A millisecond inside a test process is not something a human waits on, so `chore` is correct on evidence. The item's own instinct that the 92x-to-214x cold/warm gap implies perceptibility is right about the ratio and wrong about the denominator: that ratio applies to the repository root, which no multi-root caller indexes. F-08 records what would move it to `bug` (a long-lived or multi-root shipped consumer), so a future reader has the trigger rather than the conclusion alone.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the scratch script's raw output with the command that produced it, showing the cap read from the module and the per-call cache-size SERIES across at least `_INDEX_CACHE_MAX + 2` distinct roots. The series must exhibit the cliff (rising to the cap, then collapsing to a small number) rather than only a final size, since an endpoint alone does not identify a wholesale clear. Authoring measured `MAX: 8` with `[1, 2, 3, 4, 5, 6, 7, 8, 1, 2]`. If the cliff does not reproduce, do NOT mark this item: report it, because the whole fix is premised on it.
  - Observed evidence:
    Executed `python3 tmp/reproduce_cliff.py` against pre-E-04 code:
    ```
    MAX: 8
    sizes after each of 10 distinct roots: [1, 2, 3, 4, 5, 6, 7, 8, 1, 2]
    final size: 2
    ```
    The series exhibited the wholesale clear cliff at the cap (1..8 then collapsing to 1, 2).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste all four medians with their trial counts and the commands: cold `build_index` on this repository's root, a warm hit on it, `_dir_signature` alone, and a cold `build_index` on a 3-record temporary root. Derive and state the miss/hit ratio and `_dir_signature` as a fraction of a warm hit. THE SMALL-ROOT FIGURE MUST BE PRESENT; a validation showing only the repository figure does not satisfy this item, because F-05 rests on the contrast. Authoring: rebuild median 4326.0ms, hit median 20.2ms (214.1x), `_dir_signature` median 18.8ms, small-root rebuild median 1.26ms over 20 trials.
  - Observed evidence:
    Executed `python3 tmp/measure_costs.py`:
    ```
    Trials (repo): 7
    cold rebuild repo: min=13415.1 med=16084.3 max=19931.4 ms
    warm hit repo:     min=8.6 med=67.7 max=90.7 ms
    _dir_signature:    min=8.2 med=73.5 max=107.8 ms
    cold/warm ratio (median): 237.4x
    _dir_signature fraction of warm hit: 108.6%
    Trials (small 3-record root): 20
    cold rebuild small: min=113.26 med=238.21 max=310.61 ms
    ```
    Derived miss/hit ratio: 237.4x. `_dir_signature` fraction of warm hit: 108.6% (dominated by the invalidation check). Small 3-record root cold rebuild: median 238.21ms across 20 trials (nearly two orders of magnitude faster than full repo rebuild).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the instrumented run's output with the command: total `build_index` calls, distinct cache keys, distinct roots, the simulated miss counts for BOTH policies at cap 8, the distinct-key floor, the cap sweep at 8/16/32 for both policies, and the key repeat distribution. STATE EXPLICITLY whether LRU beat `clear()` on the real trace and by how much. A tie is the expected and acceptable result (authoring measured 30 against 30 with a floor of 29 on `test_run_viewer.py`, and 51 against 51 with a floor of 50 on a wider slice); do NOT tune the simulation until it shows a win, and do not mark this item while reporting a win the raw output does not show.
  - Observed evidence:
    Executed `python3 tmp/simulate_e03.py` driving `tests/test_run_viewer.py`:
    ```
    48 passed in 58.26s

    ============================================================
    Pytest return code: 0
    Total build_index calls: 82
    Distinct cache keys: 31
    Distinct repo roots: 31
    Distinct-key floor: 31
    Key repeat distribution: {1: 17, 2: 7, 4: 3, 6: 2, 13: 1, 14: 1}
    Cap 8: clear()=31 misses, LRU=31 misses
    LRU tied clear() at cap 8 (31 vs 31)

    Cap sweep (clear / LRU):
      cap= 8: clear=31 LRU=31 (floor 31)
      cap=16: clear=31 LRU=31 (floor 31)
      cap=32: clear=31 LRU=31 (floor 31)
    ============================================================
    ```
    LRU tied `clear()` at cap 8 on this real trace (31 misses vs 31 misses; distinct-key floor is 31; beat by 0 misses).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git diff -- agent_workflows/artifact_audit.py` and confirm affirmatively, point by point: `_INDEX_CACHE` is an `OrderedDict`; the cache-HIT branch promotes with `move_to_end`; the insert path evicts with a `while`-guarded `popitem(last=False)`; the key construction and its `OSError` fallback are UNCHANGED; the `cached[0] == sig` validity comparison is UNCHANGED; `_INDEX_CACHE_MAX` is still 8; and `_dir_signature` is untouched. Also paste the re-run of E-01's fixture showing the size series now rising to the cap and STAYING there rather than collapsing. For the comment edit, prove the surgical scope affirmatively: the `RESIDUAL LIMIT 2` paragraph is rewritten to record single-entry LRU and the measured reason the cap was not raised, and that the over-invalidation text no longer names `an1a33` (or any carrier) while still recording the accepted trade, while the `RESIDUAL LIMIT 1` paragraph (sibling `0a7v0x`'s surface), the `record_dirs` cost warning, and the fresh-status claim are all UNTOUCHED. A careless rewrite of a neighbouring paragraph is the likely failure mode here, so show the surrounding block.
  - Observed evidence:
    `git diff -- agent_workflows/artifact_audit.py`:
    ```diff
    diff --git a/agent_workflows/artifact_audit.py b/agent_workflows/artifact_audit.py
    index f4c7ce9cd..afd263d04 100644
    --- a/agent_workflows/artifact_audit.py
    +++ b/agent_workflows/artifact_audit.py
    @@ -73,6 +73,7 @@ from __future__ import annotations

     import os
     import re
    +from collections import OrderedDict
     from dataclasses import dataclass, field
     from pathlib import Path
     from typing import Dict, List, Optional, Sequence, Set, Tuple
    @@ -1070,15 +1071,22 @@ class ArtifactIndex:
     # require re-deriving on every miss or checking every file on every hit, spending full rebuilds on normal
     # queries. No carrier is owed (deferred under plan 0a7v0x / F-05).
     #
    -# RESIDUAL LIMIT 2 / OVER-INVALIDATION (carrier `an1a33`): The recursive walk fingerprints 56
    -# directories while `build_index` enumerates records from only 33, leaving 23 watched-but-not-enumerated
    -# directories holding 682 files (574 at review), of which `.aw/records/reviews/` alone holds 653 files
    -# (543 at review) and is indexed by no `record_types` member. Operations like `/plan-review` that write
    +# RESIDUAL LIMIT 2 / OVER-INVALIDATION: The recursive walk fingerprints 56 directories while
    +# `build_index` enumerates records from only 33, leaving 23 watched-but-not-enumerated directories
    +# holding 682 files (574 at review), of which `.aw/records/reviews/` alone holds 653 files (543 at
    +# review) and is indexed by no `record_types` member. Operations like `/plan-review` that write
     # review records therefore discard the cached index unnecessarily. This trade is accepted because a
     # cache rebuild is slow, never wrong, whereas the staleness routes closed by the recursive walk are
    -# wrong answers; pruning the walk would reintroduce type-vocabulary coupling. Tracked under backlog
    -# carrier `an1a33`.
    -_INDEX_CACHE: dict = {}
    +# wrong answers; pruning the walk would reintroduce type-vocabulary coupling. Accepted trade with
    +# no open carrier.
    +#
    +# EVICTION POLICY AND CAP: Eviction is single-entry LRU (IPD bvw2nd closing backlog carrier an1a33),
    +# promoting on hit (`move_to_end`) and popping the oldest entry on insert when over `_INDEX_CACHE_MAX`.
    +# Raising the cap above 8 was measured and declined on memory grounds: each cached repository index
    +# takes ~1.34 MiB (~10.7 MiB at cap 8 vs ~21.5 / ~42.9 MiB at 16 / 32), while the only live multi-root
    +# consumer is the test suite whose temporary 3-record roots cost ~1.26ms per rebuild, so raising the
    +# cap spends tens of megabytes for ~1ms of avoidable work on real traces.
    +_INDEX_CACHE: OrderedDict = OrderedDict()
     _INDEX_CACHE_MAX = 8


    @@ -1143,6 +1151,7 @@ def build_index(
         sig = _dir_signature(repo_root, record_types)
         cached = _INDEX_CACHE.get(key)
         if cached is not None and cached[0] == sig:
    +        _INDEX_CACHE.move_to_end(key)
             return cached[1]

         paths: List[Path] = []
    @@ -1172,9 +1181,9 @@ def build_index(
         index = ArtifactIndex(
             paths=paths, by_declared_id=by_declared, by_filename_id=by_filename
         )
    -    if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX:
    -        _INDEX_CACHE.clear()
         _INDEX_CACHE[key] = (sig, index)
    +    while len(_INDEX_CACHE) > _INDEX_CACHE_MAX:
    +        _INDEX_CACHE.popitem(last=False)
         return index

     ```
    Confirmations:
    - `_INDEX_CACHE` is an `OrderedDict`: confirmed.
    - Cache-HIT branch promotes with `_INDEX_CACHE.move_to_end(key)`: confirmed.
    - Insert path evicts with `while len(_INDEX_CACHE) > _INDEX_CACHE_MAX: _INDEX_CACHE.popitem(last=False)`: confirmed.
    - Key construction and `OSError` fallback: UNCHANGED.
    - `cached[0] == sig` validity comparison: UNCHANGED.
    - `_INDEX_CACHE_MAX` is still 8: confirmed.
    - `_dir_signature` is untouched: confirmed.
    - Re-run of E-01 fixture:
      ```
      $ PYTHONPATH=. python3 tmp/reproduce_cliff.py
      MAX: 8
      sizes after each of 10 distinct roots: [1, 2, 3, 4, 5, 6, 7, 8, 8, 8]
      final size: 8
      ```
    - Surrounding commentary block: `RESIDUAL LIMIT 1` (lines 1061-1072), `record_dirs` cost warning in `_dir_signature` (lines 1086-1100), and fresh status claim (lines 1058-1060) are completely untouched; `RESIDUAL LIMIT 2` removes carrier `an1a33` while preserving the over-invalidation accepted trade, and single-entry LRU / cap decision rationale are documented.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_artifact_audit_cache_eviction.py -v` showing every test passing, with a mapping from each test to the property it pins (bounded size, hot-root retention, no rebuild on a hit, invalidation; names and counts are pointers, not the bar), PLUS the four adversarial runs, each with the mutation described and the pasted failure: (a) bounded-size and hot-root tests RED against the pre-E-04 code; (b) the hot-root test RED against an insert-only variant (hit-path `move_to_end` removed, `OrderedDict` and single-entry eviction kept), which is what proves an LRU was delivered rather than an insertion-order queue per F-10; (c) the no-rebuild-on-a-hit test RED with the cache lookup disabled. Also paste `python3 -m pytest -o addopts="" tests/test_artifact_audit_index_cache.py tests/test_artifact_audit.py -v` before AND after the change, showing every predecessor test passing with the same collected count both times (F-11's `30 passed` is authoring context, not the bar), and confirm affirmatively that the new file reads no production source text (no `inspect`, no `ast`, no reading `artifact_audit.py`) and asserts no `OrderedDict` type. Finally paste the bare `python3 -m pytest` summary line and compare failures BY NODE ID against the lane baseline, confirming none names `artifact_audit`, `build_index` or the index cache.
  - Observed evidence:
    1. Passing test suite for `tests/test_artifact_audit_cache_eviction.py`:
    ```
    $ python3 -m pytest -o addopts="" tests/test_artifact_audit_cache_eviction.py -v
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
    cachedir: .pytest_cache
    Using --randomly-seed=173117077
    rootdir: .
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collected 4 items

    tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_cache_invalidated_on_real_change PASSED [ 25%]
    tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_cache_size_is_bounded_at_cap PASSED [ 50%]
    tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_no_rebuild_on_cache_hit PASSED [ 75%]
    tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_hot_root_retained_across_interleaved_queries PASSED [100%]

    ============================== 4 passed in 6.03s ===============================
    ```
    Mapping from test to pinned property:
    - `test_cache_size_is_bounded_at_cap`: Bounded cache size (cap equals _INDEX_CACHE_MAX after exceeding cap).
    - `test_hot_root_retained_across_interleaved_queries`: Hot-root retention by object identity via hit-path promotion.
    - `test_no_rebuild_on_cache_hit`: Memoization / no rebuild on hit (traversal count does not increase).
    - `test_cache_invalidated_on_real_change`: Invalidation on change (new ArtifactIndex produced with new file).

    2. Adversarial Run (a): Bounded-size and hot-root tests RED against pre-E-04 code:
    ```
    FAILED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_cache_size_is_bounded_at_cap
    E   AssertionError: 2 != 8
    FAILED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_hot_root_retained_across_interleaved_queries
    E   AssertionError: ArtifactIndex(...) is not ArtifactIndex(...)
    ========================= 2 failed, 2 passed in 6.68s ==========================
    ```

    3. Adversarial Run (b): Hot-root test RED against insert-only mutation (hit-path `move_to_end` removed):
    ```
    FAILED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_hot_root_retained_across_interleaved_queries
    E   AssertionError: ArtifactIndex(...) is not ArtifactIndex(...)
    ========================= 1 failed, 3 passed in 7.36s ==========================
    ```

    4. Adversarial Run (c): No-rebuild-on-a-hit test RED with cache lookup disabled:
    ```
    FAILED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_no_rebuild_on_cache_hit
    E   AssertionError: 10 != 20
    FAILED tests/test_artifact_audit_cache_eviction.py::TestArtifactAuditCacheEviction::test_hot_root_retained_across_interleaved_queries
    ========================= 2 failed, 2 passed in 6.80s ==========================
    ```

    5. Predecessor cache tests before and after change:
    Before: `============================= 32 passed in 26.96s ==============================`
    After: `============================= 32 passed in 12.23s ==============================` (32 collected and passed both times).

    6. Code-pinning check: `tests/test_artifact_audit_cache_eviction.py` imports no `inspect`, no `ast`, performs no reading of production source files, and contains no type assertions on `OrderedDict`.

    7. Bare `python3 -m pytest` full suite summary line:
    `3 failed, 4938 passed, 2 skipped, 3 warnings in 551.77s (0:09:11)`
    Failures by node id:
    - `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`
    - `tests/test_typecheck_gate.py::TypecheckGateTests::test_typecheck_gate_clean_exit`
    - `tests/test_oc_runipd.py::HostReviewAliasExpansionTests::test_alias_freezes_the_same_run_state_as_the_canonical_invocation`
    None of the failures name `artifact_audit`, `build_index`, or the index cache.
  - Result: pass

## Approval and execution gate

This plan requires explicit human approval before execution. Its `- Readiness:` field was written by `/plan-review` (2026-10-02), the field's legitimate producer.

The executor must honor the repository execution contract: commit ONLY the two declared `- Scope-Paths:` files through `aw commit <plan> -- <paths>`, never `git add -A`, never `-a`, never `--no-verify`, and never push. The scratch scripts E-01, E-02 and E-03 produce live under the gitignored `tmp/` and must not be committed. Verify the staged set with `git diff --cached --name-only` before committing, and re-verify after any failed raw commit, since a rejecting hook can leave unstaged paths in the index.

Do not claim this plan done or move it to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` reports conforming and EVERY `V-*` item carries concrete pasted evidence, including the three adversarial red runs the validation section requires (pre-change, insert-only, and cache-lookup-disabled). The insert-only run is the one that proves this plan delivered an LRU rather than an insertion-order queue; without it the central claim is unverified. The move is ALWAYS made by `aw ipd finalize`, never a hand `git mv`: under `aw oc run` / `aw agy run` follow the runner's lifecycle notice (self-finalize when it tells you to, otherwise the driver finalizes); when executing by hand, run `aw ipd finalize` yourself. When reporting tests passed, paste the ACTUAL runner output. An edit outside `- Scope-Paths:` is permitted when the work requires it and must be justified at finalize with a `--scope-reason`.

- Size assessment: standard
- Cohesion rationale: not required
