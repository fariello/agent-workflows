- Id: try1jq
- Status: parked
- Release-Exempt-Kind: artifact
- Release-Exempt-Ref: cxxmyv
- Set: metastore
- Work-Kind: bug
- Priority: medium
- Summary: fixture_codemod._parse_bullet_site relocates pre-history heading sections after ## Workflow history via body=
- Short-Description: fixture_codemod._parse_bullet_site relocates pre-history heading sections after ## Workflow history via body=

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 parked (aw set): Pre-cutover dev-tool helper only (tools/fixture_codemod.py); does not ship as user runtime and is unused once metastore cutover cxxmyv lands.
- 2026-11-22 created (aw backlog): fixture_codemod._parse_bullet_site relocates pre-history heading sections after ## Workflow history via body=

In tools/fixture_codemod.py::_parse_bullet_site, any ## section appearing between metadata bullets and ## Workflow history is collected into body_sections and passed to RecordBuilder.backlog(..., body=...), which appends body after ## Workflow history. Measured on tests/test_backlog.py::BacklogPreservationTests::test_header_prose_survives during 2fn0vd Step 3: pre-history ## What is wrong prose was relocated after ## Workflow history without failing equivalence. Refuse fixtures with pre-history sections before ## Workflow history as unsupported-shape.
