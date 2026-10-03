# Review findings: plan 0a7v0x

- Subject-Id: 0a7v0x
- Subject-Type: ipd
- Reviewed-At: 2026-10-02
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

Reviewed at HEAD `c770942de` in an isolated review lane. The plan was committed and byte-identical to the lane
input (`diff` reported no difference), so no pre-review snapshot was needed. `aw ipd lint --phase author
--agent` reported clean (exit 0) before semantic review; `--phase review-finalize` reports clean after revision.

Verified from code: the `RESIDUAL LIMIT 1` comment text quoted by E-05 is verbatim at
`agent_workflows/artifact_audit.py:1049`; `find_artifact`'s tier order (declared id6, filename id6, stem) at
`artifact_audit.py:1192-1219` matches F-02; `build_index` returns the cached object on signature match at
`artifact_audit.py:1123-1126`; the three `_ID_LINE_RE` twins pin `[0-9a-z]{6}` (`check_engine.py:1638`,
`artifact_rename.py:250`, `ipd_authoring.py:338`); the insert-only guards F-08 quotes exist
(`artifact_rename.py:305`, `ipd_authoring.py:778`); `run_viewer.py` obtains its explicit index from
`_audit.build_index(repo_root)` (`run_viewer.py:2158`, `:3772`); the backlog item carries the OQ-02
falsification note; `ieg7q6`, `an1a33`, `1sn4h0` each resolve via `aw find` to one file.

Prototyped in the lane under gitignored `tmp/pr/` (no production code edited):
`demo.py`: `explicit index IS the cached object: True`; `build_index after in-place rewrite returns SAME stale
object: True`; after popping the key `fresh after pop-key: True None [...xxxxxx-x.ipd.md]`; `next call reuses
fresh (no rebuild): True`.
`demo2.py`: X declares `aaaaaa`, Y rewritten in place `bbbbbb`->`aaaaaa`: `cached: ...x.ipd.md collisions []`,
`verify-on-hit claim holds (so no re-derive): True`, `truth collisions: [x, y]`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | A. Correctness | `artifact_audit.py:1123-1126` (`build_index` cache hit on `cached[0] == sig`); `run_viewer.py:2158` (`artifact_index = _audit.build_index(repo_root)`); `tmp/pr/demo.py` output | E-03's explicit-index branch said "there is no cache entry to invalidate" and to "re-derive a FRESH index LOCALLY", and the gate said "do not clear `_INDEX_CACHE` there". But run_viewer's explicit index IS the cache entry, and because the signature is unchanged across the rewrite, calling `build_index` to re-derive returns the same stale object, so the re-derivation would silently re-answer from the wrong map on the dominant path. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03 now requires popping the root's cache key before rebuilding on BOTH paths, with the demonstration pasted; gate and V-03 reconciled. |
| PR-002 | MEDIUM | IN-SCOPE | C. Architecture (caching) | E-03 "clear `_INDEX_CACHE`, rebuild"; `artifact_audit.py:1155-1157` | Clearing the whole cache on one root's failed claim discards every other root's valid entry; an unconditional pop would also force a full traversal on every repeat lookup against a caller's still-stale explicit index. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03: pop only this root's key and only when the stored entry `is` the failed index; V-03 demands it. |
| PR-003 | MEDIUM | IN-SCOPE | A. Correctness | `artifact_audit.py:1203-1218` (tiers two and three) | E-03 said "answer from the fresh index" without saying through which tiers; a stale positive's correct answer may be a tier-two/three hit, so re-answering tier one only would return a wrong miss. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-03: inner pass runs all three tiers with verification disabled (the at-most-once bound). |
| PR-004 | MEDIUM | UNDER-SCOPE | E. Testing | F-06 (dominant path); V-03 fourth run; E-06 had five tests, none on `artifact_index=` | The dominant production path was demonstrated once in V-03 but pinned by no committed test, so a later edit could regress it unseen. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 adds a sixth test (truth-equality, caller object untouched, repeat call does not re-traverse) with RED mutations in V-06; Proposed changes and counts swept. |
| PR-005 | MEDIUM | UNDER-SCOPE | D. Domain invariants / honest docs | `tmp/pr/demo2.py` output | A collision CREATED in place is still reported as a clean single hit after the fix, because X's claim verifies and nothing reads Y. The plan claimed only the miss-on-new half stays open. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Documented as the same "fails to assert something TRUE" class: added to the Deferred miss-half row (same Carrier-Declined rationale) and to E-05's required comment text. |
| PR-006 | LOW | IN-SCOPE | G. Executability | Gate text "OQ-02 records that the item's own text should probably be corrected and leaves that decision to the maintainer" vs resolved OQ-02; gate "`aw ipd finalize` for the terminal transition" | Stale cross-reference to OQ-02's pre-resolution shape, and an unconditional finalize instruction (runner owns finalize under `aw oc run`). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Gate rewritten to match OQ-02's resolution; finalize ownership made conditional with `--scope-reason` for any out-of-scope edit. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | On the explicit-index path, re-derive by building an uncached private index, or by invalidating the cache key and rebuilding through `build_index`? | Pop the key only if it holds the stale object, then `build_index`, so the repaired index is re-cached | A private uncached `build_index` copy (duplicates the traversal path, and every repeat lookup would pay a full traversal); unconditional pop (same repeat cost) | `tmp/pr/demo.py`: `next call reuses fresh (no rebuild): True`; `artifact_audit.py:1123-1157` | yes |
| D-2 | Close the in-place-created collision in this plan? | No; defer with the miss half and document in code | Read every record's header on every hit (equals a rebuild per lookup) | Same asymmetry as OQ-01: an omission, not a false assertion; `tmp/pr/demo2.py` | yes |
