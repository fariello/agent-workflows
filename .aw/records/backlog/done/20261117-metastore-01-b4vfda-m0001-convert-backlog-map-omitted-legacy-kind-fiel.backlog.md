- Id: b4vfda
- Status: done
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: m0001_convert.backlog_map omitted legacy Kind field alias for work_kind (fixed in bv4kkj)
- Short-Description: m0001_convert.backlog_map omitted legacy Kind field alias for work_kind (fixed in bv4kkj)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 created (aw backlog): m0001_convert.backlog_map omitted legacy Kind field alias for work_kind (fixed in bv4kkj)

Legacy backlog items (including tests/migration_corpus.py mixed_layout qa1z04) serialize work_kind as - Kind: <value>. m0001_convert.py mapped Kind only for specs/plans and omitted it from backlog_map, triggering unknown-field census refusal during mixed_layout migration. Added Kind -> work_kind to backlog_map under bv4kkj.
