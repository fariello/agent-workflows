- Id: ldfefd
- Status: done
- Set: metastore
- Work-Kind: followup
- Priority: high
- Summary: Metastore cutover code patch removes the legacy bullet API that tests/record_builder.py, tools/fixture_codemod.py and 31 test modules still call; no metastore child owns converting them
- Short-Description: Metastore cutover code patch removes the legacy bullet API that tests/record_builder.py, tools/fixture_codemod.py and 31 test modules still call; no metastore child owns converting them
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-28 done (aw backlog): closed by aw agy run: IPD x3mig6 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md, .aw/records/plans/executed/20261125-metastore-310-x8id25-convert-test-batch-c-ipd-lifecycle-cli-through-prompts-set-s.ipd.md, .aw/records/plans/executed/20261125-metastore-311-e0g2gt-convert-test-batch-d-prose-dash-advisory-through-readers-run.ipd.md, .aw/records/plans/executed/20261125-metastore-312-qi0kl6-convert-test-batch-e-readers-selectors-find-through-spec-id6.ipd.md, .aw/records/plans/executed/20261125-metastore-313-x3mig6-convert-test-batch-f-spec-review-gate-kind-through-writers-s.ipd.md); evidence .aw/records/plans/executed/20261125-metastore-309-psm9ac-convert-test-batch-b-backlog-handoff-close-through-ipd-depen.ipd.md
- 2026-11-26 graduated (aw backlog): Carried by metastore Orders 306-313 (89mtbl, nv3upa, cugg3w, psm9ac, x8id25, e0g2gt, qi0kl6, x3mig6) per maintainer answer to run-20261125T162650Z-1337442 question 06-x1mmdp-a1-Q-01
- 2026-11-26 created (aw backlog): Metastore cutover code patch removes the legacy bullet API that tests/record_builder.py, tools/fixture_codemod.py and 31 test modules still call; no metastore child owns converting them

Found by x1mmdp (run run-20261125T162650Z-1337442, attempt 1) in a scratch worktree holding HEAD c7eed9a50 plus both cutover patches (docs base tree f88e0ca4f).

Observed: on the switched tree every test import fails at tests/record_builder.py:103 (artifact_meta._LEGACY_BULLET_LABEL raises AttributeError, reached through tests/support.py:34). The code patch removes LegacyRender, LegacyTarget, render_legacy_text, set_legacy_bullet_line, _LEGACY_BULLET_LABEL, _format_legacy_value, _RESEARCH_YAML_KEY, _format_yaml_value and _PROMPT_COMMENT_KEY. They are still used by tests/record_builder.py, tools/fixture_codemod.py:1094 and 31 test modules (for example tests/test_artifact_meta_legacy_write.py with 23 uses).

Measured: with the builder kept on the legacy format via copies of the removed helpers, the switched tree gives 567 failed, 2348 passed, 1 skipped, 66 errors across 71 modules. The failures are 385 schema-1 refusals (the builder writes bullet records, so the fixture repo reads as unmigrated), about 131 assertion failures, 104 removed-API errors and 6 DriverError. Builder usage the log switch must handle: text_only=True 1692 calls in 311 files (about 700 written to disk by the caller afterwards, which a log-format reader cannot see without a meta/<id6>.jsonl), raw_fields= 442, history= 796.

Cause: x1mmdp was sized as five small steps on the premise that only the builder and a few exact-spelling rows change. The removed API and the text_only write-then-read pattern make the switch a suite-wide conversion. jycxw8 (build_skeleton still emits bullets and the history H2; ipd_lint is not log-aware) also blocks any log-format plan builder that must lint as conforming.

Fix: split the work into child plans of the metastore Set ordered before cxxmyv: fix jycxw8 first; then decide what text_only means in the log format (for example create through artifact_meta.create in a throwaway repo and return the mirror plus body, or route lint_text callers to a file form); then convert the builder, fixture_codemod and the 71 failing modules in batches, each batch adding its hunks to .aw/system/cutover/metastore-code.cutover.patch. Per-module failure counts are in the x1mmdp attempt-1 lane submission evidence/failing-modules.txt.
