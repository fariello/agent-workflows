- Id: ackme8
- Status: open
- Set: ackme8
- Priority: medium
- Kind: feature
- Summary: Add an 'aw releases' owner-verb to inspect/list release records

## Workflow history
- 2026-08-28 created (aw backlog): Add an 'aw releases' owner-verb to inspect/list release records

Releases are a first-class record class (.aw/records/releases/, releases.py, Blocks-Release gating across every tree) but the ONE records tree with no owner-verb: backlog/specs/plans/research all have 'aw <type>', releases has none. You cannot ask 'what is the planned release, its id6/version, and everything gating it?' on demand.

This session named the planned release in 'aw attention' and 'aw status' (commit c3a69ef, via releases.describe_planned_release). This item covers the remaining gap: a dedicated 'aw releases' / 'aw release show' verb for parity.

Design at plan time (candidates, not decided):
- 'aw releases' -> list release records (id6, version, status, summary), like 'aw backlog'.
- 'aw releases show <id6|next>' -> full record + the resolved blocker set (reuse attention.release_blockers).
- --json for machine use.
- Consider exposing create_release as 'aw releases new' (currently only a library fn).
- Consider naming it in 'aw doctor' too for parity with status.

Non-blocking for 2.0.0 (surfacing UX, not a ship gate).
