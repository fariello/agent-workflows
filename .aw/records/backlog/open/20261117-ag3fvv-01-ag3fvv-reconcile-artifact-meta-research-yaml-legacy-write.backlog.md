- Id: ag3fvv
- Status: open
- Set: ag3fvv
- Work-Kind: bug
- Priority: high
- Summary: Reconcile artifact_meta research YAML legacy writer with 9gy5jk D-5 and D-6
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 created (aw backlog): Reconcile artifact_meta research YAML legacy writer with 9gy5jk D-5 and D-6

During IPD 9gy5jk execution, two direct conflicts were observed between already-executed metastore plans (7yr827, 2xwb9b) and 9gy5jk E-04/D-5/D-6: (1) tests/test_artifact_meta_legacy_writer.py::test_research_yaml_front_matter_field_edit (7yr827) requires op=='set' on research YAML to insert absent keys (priority, short-description), contradicting 9gy5jk E-04(c) and V-04(c); (2) tests/test_status_set_meta_writer.py::test_w04_research_without_status_gets_one_before_the_closing_fence (2xwb9b) requires aw set to insert a missing status: before closing ---, contradicting 9gy5jk E-04(d), V-04(d), and E-03(1) (insert after kind:, else before outcome:).
