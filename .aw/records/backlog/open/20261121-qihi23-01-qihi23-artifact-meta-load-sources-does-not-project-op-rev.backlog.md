- Id: qihi23
- Status: open
- Set: qihi23
- Work-Kind: bug
- Priority: high
- Summary: artifact_meta._load_sources does not project op=review events from meta/*.jsonl into the reviews table, so query(latest_gate_review_of=...) returns empty for log-only artifacts
- Short-Description: artifact_meta._load_sources does not project op=review events from meta/*.jsonl into the reviews table, so query(latest_gate_review_of=...) returns empty for log-only artifacts
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): artifact_meta._load_sources does not project op=review events from meta/*.jsonl into the reviews table, so query(latest_gate_review_of=...) returns empty for log-only artifacts

## Problem

In `agent_workflows/artifact_meta.py`, `_load_sources` inserts rows into the SQLite `reviews` table only in the legacy `role == "review"` branch (loading `.review.md` files). In the `role == "log"` branch (loading `.aw/records/meta/<id6>.jsonl`), `_load_sources` writes `op == "review"` events to the `events` table, and writes zero rows to the `reviews` table.

Because `artifact_meta.query(latest_gate_review_of=<id6>)` checks `EXISTS (SELECT 1 FROM reviews r WHERE r.subject_id6 = a.id6 AND r.subject_id6 = ? AND r.review_kind = 'gate')`, a log-only artifact whose gate review is recorded in `meta/<id6>.jsonl` returns an empty result from `artifact_meta.query(latest_gate_review_of=...)`.

## Observed reproduction

1. Create `.aw/records/meta/sp4002.jsonl` containing valid `create` (`seq: 1`, `type: "spec"`, `status: "draft"`), `transition` (`seq: 2`, `from: "draft"`, `to: "to-review"`), and `review` (`seq: 3`, `round: 1`, `review_kind: "gate"`, `verdict: "APPROVE"`) events, with no `.review.md` file on disk.
2. Call `artifact_meta.history("sp4002", project_context=ctx)`: returns all three events, including the `op == "review"` gate event.
3. Call `artifact_meta.query(latest_gate_review_of="sp4002", project_context=ctx)`: returns `[]`.

## Acceptance criteria

1. `artifact_meta._load_sources` projects `op == "review"` events from `meta/<id6>.jsonl` into the `reviews` table (clearing stale rows for `id6` on reload).
2. `artifact_meta.query(latest_gate_review_of=<id6>)` returns the subject artifact's `State` when `meta/<id6>.jsonl` contains a gate review event and no `.review.md` file exists.
3. `artifact_meta.query(latest_gate_review_of=<id6>)` continues to return `[]` when `meta/<id6>.jsonl` contains only `review_kind == "refinement"` events.
4. `review_findings.review_attestation_missing` returns `None` for a log-only spec carrying a gate review event in `meta/<id6>.jsonl`.
