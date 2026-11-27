- Id: jchvu0
- Status: parked
- Release-Exempt-Kind: artifact
- Release-Exempt-Ref: cxxmyv
- Set: metastore
- Work-Kind: bug
- Priority: medium
- Summary: fixture_codemod._plan_site silently overwrites aliased duplicate metadata bullets (e.g. Kind + Work-Kind) instead of refusing
- Short-Description: fixture_codemod._plan_site silently overwrites aliased duplicate metadata bullets (e.g. Kind + Work-Kind) instead of refusing

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-27 parked (aw set): Pre-cutover dev-tool helper only (tools/fixture_codemod.py); does not ship as user runtime and is unused once metastore cutover cxxmyv lands.
- 2026-11-22 created (aw backlog): fixture_codemod._plan_site silently overwrites aliased duplicate metadata bullets (e.g. Kind + Work-Kind) instead of refusing

In tools/fixture_codemod.py::_plan_site, _parse_bullet_site checks duplicate raw labels (label.lower() in bullets) but _plan_site maps aliased labels (such as - Kind: and - Work-Kind: on backlog items) onto the same canonical reg_name and assigns kwargs_code[reg_name] = effective_code without checking for collision. Measured on tests/test_backlog.py::BacklogPreservationTests::test_duplicate_work_kind_deduped during 2fn0vd Step 3: - Kind: chore was silently dropped, leaving a vacuous deduplication test that still passed equivalence. Refuse aliased collisions as unsupported-shape (or route through raw_fields).
