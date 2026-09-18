- Id: os1b9j
- Status: open
- Set: os1b9j
- Priority: medium
- Work-Kind: bug
- Summary: aw install --source with a string path crashes: resolve_source_root calls .expanduser() on a str

## Workflow history
- 2026-09-18 created (aw backlog): aw install --source with a string path crashes: resolve_source_root calls .expanduser() on a str

MEASURED 2026-09-18 while executing wfartifacts Order 01 (gzhd7t); PRE-EXISTING at HEAD 6ff7a7ba, reproduced with that plan's changes stashed, so it is NOT caused by it.

WHAT IS WRONG: `aw install --source <path> <target>` crashes with an unhandled AttributeError before doing any work.

  AttributeError: 'str' object has no attribute 'expanduser'
  agent_workflows/engine.py resolve_source_root: candidate = provided.expanduser().resolve()

`resolve_source_root` assumes `provided` is a `pathlib.Path`, but the argparse `--source` dest `source_root` carries a plain `str` (no `type=Path`), so the CLI path passes a str straight through `build_install_plan`. Reached via cli.py `_run_install` -> `_diagnostics_ok` -> `engine.build_install_plan`.

WHY IT IS NOT CAUGHT: the installer tests drive `engine.install_into_repo` directly with a real `Path`, and `run_installer` in tests/support does not exercise `--source` through the CLI parser, so no test covers the str path.

LIKELY FIX: coerce at the boundary (`type=Path` on the `--source` argparse option, or `Path(provided)` inside `resolve_source_root`); the latter also hardens library callers. Add a CLI-level regression test that passes `--source` as a string.
