- Id: 0b3ynm
- Status: graduated
- Graduated-To: metastore
- Set: metastore
- Work-Kind: bug
- Priority: high
- Summary: Post-cutover CLI creators (ipd_authoring, specs, releases, prompts) omit title, set, or order in artifact_meta.create fields
- Short-Description: Post-cutover CLI creators (ipd_authoring, specs, releases, prompts) omit title, set, or order in artifact_meta.create fields
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 graduated (aw set): graduated to Order 322 (6cltab) in Set metastore
- 2026-11-27 created (aw backlog): Post-cutover CLI creators (ipd_authoring, specs, releases, prompts) omit title, set, or order in artifact_meta.create fields

In .aw/system/cutover/metastore-code.cutover.patch, four CLI creating commands omit registry fields that legacy format inferred from H1 or filenames: ipd_authoring.py::run_scaffold omits title; specs.py::run_new omits set and order; releases.py::_create_release_via_meta omits title, set, and order; prompts.py::run_new omits order. Because post-cutover artifact_meta.read reads only meta/<id6>.jsonl, these fields return None and break tests/test_record_builder_slow.py::RecordBuilderParityTests.
