- Id: mbx0o4
- Status: open
- Blocks-Release: next
- Set: instbugs
- Priority: high
- Work-Kind: bug
- Summary: completely-clean-target install writes .aw/config and .aw/state into the target despite promising zero AW-owned target files

## Workflow history
- 2026-10-07 created (aw backlog): completely-clean-target install writes .aw/config and .aw/state into the target despite promising zero AW-owned target files

Found during /plan-review of gi1w75 (2026-10-07, lane HEAD 6d434f537). A scratch `aw install <repo> --preset completely-clean-target -y --no-interactive` (AW_NO_REEXEC=1, HOME pointed at a temp dir) left `.aw/config/local.json`, `.aw/config/project.json`, `.aw/state/durable/install.json` and `.aw/state/durable/history` INSIDE the target, while `install_wizard.render_pre_write_plan` prints 'Target Delta: ZERO AW-owned target files created (clean-target).' and `resolve_project_context` resolves those classes under `<aw_home>/projects/<id>/`. Cause: `install_wizard.persist_project_policy` hard-codes `p_repo / '.aw' / 'config'` and `p_repo / '.aw' / 'state' / 'durable'` regardless of delivery mode. Also observed: AW_HOME got `.aw/projects/state/install.json` (no project id segment). gi1w75 makes the consent plan print resolver paths, so after it the plan will print home paths that the install does not write for clean-delta presets; pfub72 owns the state writer, but neither plan owns the config writer under clean-delta.
