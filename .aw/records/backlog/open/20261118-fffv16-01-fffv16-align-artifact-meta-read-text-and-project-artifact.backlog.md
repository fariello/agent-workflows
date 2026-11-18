- Id: fffv16
- Status: open
- Set: fffv16
- Work-Kind: followup
- Priority: medium
- Summary: Align artifact_meta.read_text and project_artifact with multi-bullet lineage
- Short-Description: Align artifact_meta.read_text and project_artifact with multi-bullet lineage

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-18 created (aw backlog): Align artifact_meta.read_text and project_artifact with multi-bullet lineage

Discovered while moving check_engine.build_graduation_reverse_index onto artifact_meta in metastore Order 143 (dbq57g): artifact_meta._parse_bullet_metadata_with_loose uses bullets.setdefault so read_text retains only the first From-Backlog or From-Spec bullet, and project_artifact treats from_backlog and from_spec as scalar strings. Legacy cache loading (load_legacy_artifact, _store_legacy_artifact_projection) and artifact_meta.query_lineage were updated in dbq57g so build_graduation_reverse_index preserves multi-bullet From-Backlog records for tests/test_from_backlog_cardinality.py; read_text and event-log projection remain to align.
