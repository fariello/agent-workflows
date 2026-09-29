- Id: 57dwkc
- Status: graduated
- Graduated-To: 57dwkc
- Blocks-Release: next
- Set: 57dwkc
- Priority: medium
- Work-Kind: bug
- Summary: aw uninstall --deep orphans .aw/system/layout.json, so the no-.aw-remains promise fails

## Workflow history
- 2026-09-28 set (aw backlog): graduated by run run-20260928T235632Z-1358353: g1w58u
- 2026-09-26 note (aw backlog): CI step 'Run slow-marked tests' (tests.yml, plan 4petcj) is advisory because of this item's slow-test failure; when the last of the owning items (57dwkc, 3ypquf, 4vfkl1, g0bdgg) closes, remove its continue-on-error so the slow set fails closed.
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): aw uninstall --deep orphans .aw/system/layout.json, so the no-.aw-remains promise fails

MEASURED 2026-09-18 while executing wfartifacts Order 01 (gzhd7t); PRE-EXISTING at HEAD 6ff7a7ba, reproduced with the plan's changes stashed, so it is NOT caused by that plan.

WHAT IS WRONG: `aw uninstall --deep` with records REMOVE leaves `.aw/system/` behind, holding `layout.json` and `layout.schema.json`. `_DEEP_CLEANUP_ROOTS` (engine.py) does not list `.aw/system`, but `emit_layout_artifacts` writes those two files into it on every install, so deep cleanup cannot reach them and the documented 'no .aw/ directory remains' guarantee is false.

EVIDENCE: two tests assert the guarantee and both FAIL at HEAD:
  tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
  tests/test_cli.py::InstallAtomicWizardTests::test_interactive_deep_cleanup_records_remove_fully_cleans_aw
Enumerating what remains after install -> uninstall_repo -> plan_deep_cleanup -> run_deep_cleanup(remove_records=True) prints exactly:
  .aw/system DIR
  .aw/system/layout.json FILE
  .aw/system/layout.schema.json FILE

LIKELY FIX: add `.aw/system` to `_DEEP_CLEANUP_ROOTS` classified as OTHER (not records), the same shape wfartifacts Order 01 used for `.aw/workflow-artifacts`. Worth confirming whether the VERSION file and any other `.aw/system` member should go with it, since `.aw/system/workflows` is already listed separately via the legacy tuple.
