- Id: sjsoqq
- Status: open
- Set: setiduniq
- Priority: high
- Kind: feature
- Summary: Enforce setid uniqueness across types (hard/prevented) + bidirectional graduation links (From-Backlog/From-Spec by id6, Graduated-To by setid); fix the agentadhere collision

## Workflow history
- 2026-08-27 created (aw backlog): Enforce setid uniqueness across types (hard/prevented) + bidirectional graduation links (From-Backlog/From-Spec by id6, Graduated-To by setid); fix the agentadhere collision

Design source of truth: spec `4w7d6s` (`.aw/records/specs/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md`). Implement its invariant + graduation-link model as a follow-on IPD Set once the spec is reviewed.

Tooling deliverables (from the spec):
1. Promote `check.setid-collision` from SOFT (whitelistable, awcheck-02-xwxxo8 E-02) to HARD/fail-closed in `check_engine` + `aw doctor` (like `check.id6-collision`).
2. Prevent at creation/move: `aw ipd scaffold`, `aw research new`/`new-comparison`, `aw backlog new`, `aw group`, `aw rename` refuse to mint/move into a cross-type-duplicate setid.
3. Setter UX: `aw ipd set`/`aw set <type>` resolve a setid WITHIN the requested type (so `aw ipd set agentadhere` works); on a genuine collision emit the specific setid-collision message + `aw group ... --set` recovery, not the generic "type mismatch" (the bug that triggered this).
4. Add `Graduated-To: <setid>[,<setid>...]` (multi-valued) to backlog items + specs; graduation writes it alongside the child's `From-Backlog`/`From-Spec`; add `check.graduated-to-dangling`.
5. Graduation mints a FRESH child setid (never the source's); links are typed + bidirectional.
6. One-time migration sweep: resolve all pre-existing cross-type setid collisions (starting with `agentadhere` - regroup the closed `3gr7fk` backlog item to its own setid + set its `Graduated-To`) BEFORE enabling hard enforcement, so it does not mass-fail.

Origin: `aw ipd set approved agentadhere ...` failed with a confusing cross-type "type mismatch"; the setid collision (plan Set vs closed backlog item vs research reports) is flagged by `aw check` today but only softly and not consulted by the setters. Reuses From-Backlog (built) + From-Spec (designed) + the existing collision checker.

Progress (2026-08-27): deliverable #3 (setter UX - `aw ipd set`/`aw set` scope the selector to the requested record type) landed via commit 9107790, WITH test coverage in `tests/test_status_set.py`. This item stays OPEN; remaining: #1 promote `check.setid-collision` soft -> hard/fail-closed; #2 creation/move prevention; #4 `Graduated-To` field + `check.graduated-to-dangling`; #5 fresh-setid graduation; #6 migration sweep. NOTE: `aw check all` now reports 0 setid-collision findings, but the collision PHYSICALLY persists - the closed `3gr7fk` backlog item still carries `- Set: agentadhere` (verified); detection changed, the data did not. Do NOT close until spec 4w7d6s's invariant + graduation-link model is built.
