# Review: Consolidate record_producers.py and project_schema.py into layout model

- Plan-Id: rodj06
- Reviewed-At: 2026-09-04
- Reviewer: opencode its_direct/pt3-claude-opus-5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 6

All claims verified at HEAD `16777ccc`, working tree clean, target plan committed and unchanged, so the
pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` before and
`--phase review-finalize` after.

RE-MEASURED LIVE:

- `_RECORD_CLASS_SUBPATHS['records'] == ''` - the mandatory empty-subpath carve-out HOLDS, so PR-001's
  invariant is stated against reality and the `records/records/` hazard is real.
- `_LEGACY_RECORD_CLASS_SUBPATHS` retains a key for every current class, so F-3's migration-read
  preservation is current.
- `LogicalRoot` is exactly 4 (`system`, `config`, `state`, `records`) and `RootClass` exactly 6, so
  F-4's do-not-collapse rule is measured, not assumed.
- `tests/test_record_producers.py` genuinely does NOT exist, so PR-002's create-not-edit correction
  stands. `tests/test_project_context.py` DOES exist, so V-02's run-it instruction is valid.

The plan's structure and its three invariants (carve-out, legacy paths, enum separation) are correct.
One counting error was found, and it is the kind that corrupts a derivation rather than merely reading
oddly.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-201 | MEDIUM | IN-SCOPE | A. Correctness / G. Plan executability | `RecordClass` enumerated live: `['comms','plans','prompts','records','releases','research','reviews','specs','walkthroughs']` = NINE with `records` among them; `len(_RECORD_CLASS_SUBPATHS) == 9`; `REVIEWS = "reviews"` present with its revgate `15zvu6` E-09 comment | THE MEMBER COUNT WAS WRONG IN BOTH E-01 AND THE STEP-0 NOTE, which said "9 members + `records` root-level carve-out" - i.e. TEN. Measured: NINE TOTAL, `records` INCLUDED; it is a carve-out in its SUBPATH VALUE (empty string), not an extra member. A derivation built to produce ten members would either invent one or mis-map `records`, which is precisely the `records/records/` defect PR-001 exists to prevent. SECOND ERROR in the same item: `reviews` is described as absent from today's `RecordClass` alongside `backlog` and `other`, but it is ALREADY a member, so the net-new union members are `backlog` and `other` ONLY. An executor following the old text could have attempted to add `reviews` and hit a duplicate, or hand-added a legacy `docs/` override for a tree that deliberately has none. | C:Low; U:Low; S:Low; F:Medium; Overall:Low (correcting a count and a membership claim; no scope or design change) | FIXED | E-01 now states the nine-total count with the enumeration, explains that `records` is a value carve-out rather than an extra member, and names `backlog`/`other` as the only net-new members while forbidding re-adding `reviews`. The Step-0 conventions note corrected. Added as F-6, with F-7 recording that `_LEGACY_RECORD_CLASS_SUBPATHS` already has a key per class so "correct-by-absence" applies to net-new classes only. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is PR-201 a LOW (a miscount in prose) or MEDIUM (an executable defect)? | MEDIUM. | LOW. Rejected because the count is not decorative: E-01 instructs the executor to DERIVE `_RECORD_CLASS_SUBPATHS` from the model, and a target cardinality of ten against a real nine forces either an invented member or a mis-mapped `records` - the exact `records/records/` path defect the plan's own PR-001 invariant exists to prevent. A wrong number inside a derivation instruction is a functional risk, not a typo. | `len(_RECORD_CLASS_SUBPATHS) == 9` measured; `_RECORD_CLASS_SUBPATHS['records'] == ''`; E-01's own derivation instruction and PR-001 carve-out text | yes |
