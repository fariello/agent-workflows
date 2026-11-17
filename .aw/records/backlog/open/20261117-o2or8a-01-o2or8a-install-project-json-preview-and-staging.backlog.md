- Id: o2or8a
- Status: open
- Set: o2or8a
- Work-Kind: bug
- Priority: medium
- Summary: aw install writes .aw/config/project.json via write_metadata_schema outside diff preview and leaves it unstaged on re-run when git_policies is absent
- Short-Description: aw install writes .aw/config/project.json via write_metadata_schema outside diff preview and leaves it unstaged on re-run when git_policies is absent
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 created (aw backlog): aw install writes .aw/config/project.json via write_metadata_schema outside diff preview and leaves it unstaged on re-run when git_policies is absent

## Problem

Observed on `main` (`8a1bdc631`) in two failing full-suite tests:

1. `tests/test_installer_scaffold_preview_parity.py::test_preview_proposed_set_is_superset_of_declarative_scaffolding_parity`: `agent_workflows/engine.py::install_into_repo` calls `chain.write_metadata_schema(plan.repo_root, _mig_chain.CURRENT_METADATA_SCHEMA)` when `not dry_run`, writing `.aw/config/project.json` outside `--diff` preview and outside `allowed_residual_fixed`.
2. `tests/test_installer.py::InstallerEndToEndTests::test_tool_scripts_are_executable_and_staged`: when `install_into_repo` writes a minimal `.aw/config/project.json` without `git_policies`, `agent_workflows/engine.py::stage_tracked_policy_files` skips staging `.aw/config/project.json`, leaving `M .aw/config/project.json` unstaged after re-running the installer.

## Acceptance criteria

- `install_into_repo` and `--diff` preview account consistently for `.aw/config/project.json`.
- Both failing installer tests above pass without weakening assertions.
