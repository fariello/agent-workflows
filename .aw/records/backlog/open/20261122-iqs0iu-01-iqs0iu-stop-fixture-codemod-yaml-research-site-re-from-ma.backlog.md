- Id: iqs0iu
- Status: open
- Set: iqs0iu
- Work-Kind: bug
- Priority: low
- Summary: Stop fixture_codemod._YAML_RESEARCH_SITE_RE from matching two-key log-format YAML mirrors as research records
- Short-Description: Stop fixture_codemod._YAML_RESEARCH_SITE_RE from matching two-key log-format YAML mirrors as research records
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Stop fixture_codemod._YAML_RESEARCH_SITE_RE from matching two-key log-format YAML mirrors as research records

## Context

In `tools/fixture_codemod.py`, `_YAML_RESEARCH_SITE_RE` matches any string literal starting with a YAML front-matter block containing `id:` or `status:`. That pattern matches post-cutover two-key log-format mirrors (`---\nid: ...\nstatus: ...\n---`) written for `aw meta repair` tests in `tests/test_meta_repair_cli.py` (such as `_build_stale_mirror_fixture`, `test_move_repair_completes_pending_move_without_new_event`, and `test_diverged_tail_requires_confirm_and_prints_field_changes`) and plans to rewrite them into `RecordBuilder().research(..., raw_fields={'status': ...})`. In the same file, `_LEGACY_SUBJECT_FUNC_MARKERS` does not include `legacy_record`, so `test_legacy_record_reports_nothing_to_repair` is planned for rewrite rather than refused as `legacy-format subject`.

## Acceptance

1. Narrow `tools/fixture_codemod.py::_YAML_RESEARCH_SITE_RE` (or add a two-key mirror guard) so two-key log-format mirrors (`id` + `status` only, without research keys such as `kind`, `outcome`, `topic`, `consumed-by`) are not classified as legacy research fixtures.
2. Add `"legacy_record"` to `_LEGACY_SUBJECT_FUNC_MARKERS` so tests whose subject is legacy-format detection stay `legacy-kept`.
3. Add behavioral tests in `tests/test_fixture_codemod.py` proving both cases under `--dry-run`.
