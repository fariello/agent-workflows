- Id: m9dobx
- Status: done
- Graduated-To: m9dobx
- Blocks-Release: next
- Set: m9dobx
- Priority: medium
- Work-Kind: bug
- Summary: project_context reads user config from a hard-coded ~/.config/agent-workflows, ignoring XDG_CONFIG_HOME that config.config_dir honors

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD qi5ljl executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-m9dobx-01-qi5ljl-route-project-context-user-config-reads-through-config-confi.ipd.md); evidence .aw/records/plans/executed/20261014-m9dobx-01-qi5ljl-route-project-context-user-config-reads-through-config-confi.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: qi5ljl
- 2026-10-12 created (aw backlog): filed while graduating btw02e (plan 9y27t2)

## Context

`project_context.resolve_project_context` reads the user config from a HARD-CODED `os.path.expanduser("~/.config/agent-workflows")` at two sites (the `aw_home` fallback in the "2. AW_HOME Resolution" block, and `user_cfg_dir_effective` under "Read configuration layers"), unless a caller passes `user_config_dir=`. Every other user-config reader routes through `config.config_dir()`, which honors `XDG_CONFIG_HOME`. So for an operator who exports `XDG_CONFIG_HOME`, `aw config set aw_home ...` and the GLOBAL_DEFAULTS layer are written to one file and read from another. It also means the test suite's conftest sandbox (which points `XDG_CONFIG_HOME` at a temp dir) does not isolate this reader: tests read the developer's real `~/.config/agent-workflows/config.json`.

Found while graduating `btw02e` (plan `9y27t2`), which adds an `AW_CONFIG_DIR` override to `config.config_dir()`; this reader would ignore that too.

## Ask

Route both sites through `config.config_dir()` (lazily imported, failing open like `leak_sanitizer._config_dir`), and add a behavioral test that sets `XDG_CONFIG_HOME` to a temp dir holding `{"aw_home": ...}` and asserts the resolved `effective_aw_home` follows it.

## Provenance
- From-Plan: 9y27t2
- Related: btw02e
