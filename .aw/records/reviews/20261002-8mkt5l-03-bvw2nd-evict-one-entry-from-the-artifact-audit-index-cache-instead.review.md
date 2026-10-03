# Review: Evict one entry from the artifact-audit index cache instead of clearing all of it

- Subject-Id: bvw2nd
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Target plan was committed and unchanged (snapshot skipped). `aw ipd lint --phase author` was clean before the edits; `--phase review-finalize` was clean after the attested transition.

Re-verified at lane HEAD `cae85d5d5`:
- `build_index` evicts via `if len(_INDEX_CACHE) >= _INDEX_CACHE_MAX: _INDEX_CACHE.clear()`.
- The cache key is `(str(repo_root.resolve()), tuple(record_types))` with an `OSError` fallback, and the hit branch is gated on `cached[0] == sig`.
- `_INDEX_CACHE_MAX = 8`.
- The cliff reproduces: `8 [1, 2, 3, 4, 5, 6, 7, 8, 1, 2]`.
- Under the shipped `clear()`, a hot root interleaved with 9 fresh roots is not retained (`hot retained (clear): False`).
- `tests/test_artifact_audit_index_cache.py` indexes `_INDEX_CACHE[key][1]`.
- Sibling `0a7v0x` E-03 pops a key from the cache.
- The carriers `ieg7q6` and `0a7v0x` and the predecessor `dea7dr` resolve.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Correctness of record / spec sync | `agent_workflows/artifact_audit.py:1053` "RESIDUAL LIMIT 2 / OVER-INVALIDATION (carrier `an1a33`)"; dea7dr Deferred row "WHOLESALE `clear()` EVICTION ... Carrier: an1a33" | E-04 treated the paragraph as naming `an1a33` "for the wholesale clear". In fact the paragraph's body is only about over-invalidation, which `dea7dr` accepted as a trade, and the `an1a33` label is a mislabel. The rewrite instruction could therefore leave the over-invalidation text pointing at a carrier that this plan closes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-04 now states the mislabel and its source. It requires the over-invalidation text to stand as an accepted trade with no carrier, and eviction to be described separately as LRU. V-04 checks that `an1a33` is detached. |
| PR-002 | MEDIUM | IN-SCOPE | Testing (E) | plan E-05 hot-root test "enough fresh roots to cross the cap" | The fresh-root count was unspecified. With fewer than `_INDEX_CACHE_MAX` interleaved fresh roots, an insert-only queue never evicts the hot entry, so the mandated insert-only mutation could stay green. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | The test now requires at least `_INDEX_CACHE_MAX + 2` fresh roots, one between each re-query, with the cap read from the module. A review probe confirms the shipped code fails this check. |
| PR-003 | LOW | IN-SCOPE | Live-artifact criteria (G) | plan V-05 "all four tests passing by name", "the predecessor's 30 tests" | The bars were test counts and names. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced with a behaviour mapping, and a predecessor count that must be identical before and after. |
| PR-004 | LOW | IN-SCOPE | Validation coherence | plan Required tests "Performance must be re-measured after the change per E-02 and E-03" | No E or V item delivered this after-change re-measurement, and it adds nothing because E-04 does not change rebuild cost. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Reworded so that E-02 and E-03 are pre-change only and E-01's fixture is re-run after the change. |
| PR-005 | LOW | IN-SCOPE | Execution contract (G) | plan gate; OQ-01/OQ-02 `Owner: none` | The gate did not state who owns finalize, did not include the paste-actual-output rule, and gave no route for an out-of-scope justification. Two resolved OQs had no owner. Sibling `0a7v0x`'s `pop` on the cache was not mentioned. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added all three to the gate, set both owners to `plan author`, and added an E-05 note on composing with `0a7v0x` and on the container API. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What carrier should the surviving over-invalidation text name? | None (an accepted trade) | Keep `an1a33` (wrong subject, and closed by this plan); file a new carrier (dea7dr already accepted the trade, so nothing is owed) | dea7dr Deferred rows and E-07 "state whether the trade is still accepted"; `an1a33` Summary is about eviction only | yes |
