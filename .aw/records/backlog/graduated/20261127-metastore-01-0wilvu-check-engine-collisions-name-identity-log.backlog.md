- Id: 0wilvu
- Status: graduated
- Graduated-To: 639g02
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: check_collisions and check_name_identity ignore meta JSONL logs and suppress YAML-mirror ids on log-format records
- Short-Description: check_collisions and check_name_identity ignore meta JSONL logs and suppress YAML-mirror ids on log-format records
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 graduated (aw set): Graduated to Order 324 child plan 639g02 in Set metastore.
- 2026-11-27 created (aw backlog): check_collisions and check_name_identity ignore meta JSONL logs and suppress YAML-mirror ids on log-format records

In the metadata-store cutover code patch (.aw/system/cutover/metastore-code.cutover.patch), two identity checks in agent_workflows/check_engine.py fail on post-cutover log-format records: (1) check_collisions (around lines 2270-2320) reads only artifact_meta.read_text instead of meta/<id6>.jsonl and suppresses declared_id whenever a file starts with '---' and carries YAML 'id:' without a legacy '- Id:' bullet, so declared_id is None and set is empty on every log-format record; (2) check_name_identity (around lines 3339-3345) reads _identity_declared_values from inline Markdown text only, never reading set from meta/<id6>.jsonl, so check.identity-absent-from-name cannot detect filename setid drift. Discovered during IPD psm9ac; blocks CollisionTests, LifecyclePlacementTests, EntryPointTests, and NameIdentityDriftTests in tests/test_check_engine.py.
