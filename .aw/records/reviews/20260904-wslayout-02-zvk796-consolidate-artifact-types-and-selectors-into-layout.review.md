# Review: Consolidate artifact_types.py and selectors.py into layout model

- Plan-Id: zvk796
- Reviewed-At: 2026-09-04
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 6

All claims verified at HEAD `16777ccc`, working tree clean, target plan committed and unchanged, so the
pre-review snapshot was correctly skipped per Step 1. `aw ipd lint --phase author` conforming before and
`--phase review-finalize` conforming after the revisions.

Round 6 exists because rounds 1-5 predate a change to the very module this plan consolidates: on
2026-09-04 `selectors.py` gained a THIRD directory set (`NON_PRIMARY_RECORD_DIRS`) and a derived union
(`_OTHER_SWEEP_SKIP_DIRS`) in commit `d802e917`. The plan's round-5 text already knew about the third
set, but not about the union, and the union is what the `other` complement actually reads.

RE-MEASURED LIVE rather than trusted:

- `ARTIFACT_TYPES` is the 10 types claimed and DOES contain `roadmaps`; `normalize_type('roadmap')`
  returns `roadmaps`. So PR-001's non-narrowing invariant is stated against the real vocabulary.
- `EXCLUDED_RECORD_DIRS` is exactly the 7 pinned entries, matching OQ-01's ruling.
- `KNOWN_PRIMARY_TYPES` is 9 (`ARTIFACT_TYPES` minus `other`), as the conventions note says.
- `NON_PRIMARY_RECORD_DIRS == frozenset({'reviews'})`.
- `aw check reviews` still errors with "unknown artifact type", so F-4's net-new-behavior claim is
  current rather than already delivered.
- `agent_workflows/layout.py` correctly does NOT exist yet; Order 01 (`wpu5zu`) creates it.

The decomposition is sound and the two E-items are genuinely one concern each.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-101 | HIGH | UNDER-SCOPE | A. Correctness / D. Anti-regression | `selectors.py:183` (`_OTHER_SWEEP_SKIP_DIRS = KNOWN_PRIMARY_TYPES \| NON_PRIMARY_RECORD_DIRS \| EXCLUDED_RECORD_DIRS`), consumed at `:215`; E-02 named only the three inputs; V-02 asserted only `EXCLUDED_RECORD_DIRS`; outage fixed in `d802e917`; `tests/test_selector_resolver_matrix.py::OtherCatchAllDoesNotClaimTypedTreesTests` | E-02 SOURCES THE THREE INPUT SETS BUT NEVER NAMES THE DERIVED SET THAT ACTUALLY GATES THE SWEEP. The `other` catch-all consults the UNION, not the three sets individually, so re-sourcing the inputs from `layout.py` silently redefines the union. The validation gap is what makes this HIGH rather than LOW: V-02 asserted only the 7 exclusions, so a derivation that dropped `reviews` from the union would have PASSED this plan's own validation while re-opening a MEASURED outage - with `reviews` in neither set, a bare id6 matched twice (the plan as `plans`/id6, its own review as `other`/substring) and `aw set approved <id6>` refused with "id6 collision ... not overridable by --force" for ALL 28 reviewed plans. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (keep the union derived rather than hardcoded; the assertions already exist in a shipped test file) | FIXED | E-02 now requires `_OTHER_SWEEP_SKIP_DIRS` stay computed from whatever the three sets become, never hardcoded and never bypassed by a fourth membership test, with the outage recorded as the reason. V-02 now demands four pieces of evidence: the union containing `reviews`, `resolve(...,'other','<id6>')` returning empty, `match_selector` returning exactly `['plans']`, and `tests/test_selector_resolver_matrix.py` passing. Added as F-7. |
| PR-102 | LOW | IN-SCOPE | A. Correctness (framing) | `record_producers.RecordClass` enumerated live: 9 members INCLUDING `REVIEWS`; `artifact_types.ARTIFACT_TYPES`: 10 members, no `reviews`; `aw check reviews` -> error | F-4 describes `reviews` becoming an accepted token as "net-new behavior", which is true of `artifact_types` but understates the situation: `reviews` is ALREADY a `RecordClass` member, so the two vocabularies disagree TODAY. The union ruling RECONCILES two live vocabularies rather than adding a token to one. Worth stating so an executor does not assume nothing consumes `reviews` yet and skip checking the consumers. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Recorded as F-8 with both live measurements. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | PR-101 could be fixed by asserting the union in V-02 only, or by also constraining E-02's implementation. Which? | BOTH: constrain E-02 (keep the union derived) AND assert it in V-02. | Assert-only. Rejected: a validation that catches a bad derivation after the fact still permits an executor to hardcode the union, which passes the assertion today and rots the moment a fourth set is added. Constrain-only. Rejected: the outage it prevents was invisible to the existing validation, so the assertion is the part that makes the constraint checkable. | `selectors.py:183`/`:215` showing the union is the consumed value; `d802e917`'s measured 28-plan outage; the shipped regression test that already pins the property | yes |
