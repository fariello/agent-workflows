# Assess bugs - evidence (what was inspected)

Read-only. No product files modified (the IPD + this run record are the workflow's own deliverables).

## Files inspected

- `agent_workflows/engine.py` (esp. `run()` ~2704-2836, `install_into_repo` ~2645-2717,
  `prompt_and_run_commit` :1877-, `create_setup_artifacts`, `save_created_files_record` ~1682-1703,
  `run_rollback`/`_remove_path`, `merge_pointer_block`/`update_agents_pointer`, `install_all`
  customization path ~758/805/924, `run_git_diagnostics`/`classify_git_state` ~1415-, `check_gitignore`,
  `ensure_backups_gitignored` ~1303-).
- `agent_workflows/cli.py` (`_run_install` ~328, `_install_all` ~434, `setup`/`_run_setup` ~730,
  `_diagnostics_ok` ~291, `_confirm`, `_preflight_warnings`).
- `agent_workflows/comms.py` (is_filename_safe, parse_not_before, parse_envelope_header, validate_ack,
  ACK_WRITER, ack enum) - security-critical, checked by live execution.
- `agent_workflows/plans.py` (read_set, is_set_id_valid, parse_order, _set_member_sort_key, set_warnings,
  render_status_index Sets section).
- `agent_workflows/versioning.py` (parse_describe, rc/dev parse + sort keys, next_version_ok,
  latest_pypi_version), `config.py` (_preserve_home atomic write), `discovery.py` (ignore-before-recurse),
  `pypi_links.py`, `term.py` (should_color).
- Tools: `normalize_plan_names.py`, `scan_secrets.py` (redact, csv emit), `run_checks.py` (classification,
  denylist, PHONY skip, csv emit), `bench_env.py` (csv emit, temp cleanup).

## Verification (coordinator re-check of the three Medium findings)

- F4: `grep`/`sed` of `run()` -> confirmed `returncode` set to 1 in two places but final line is
  `return 0`; the undo branch correctly returns `returncode`.
- F5: `sed` of the `newly_created` builder -> confirmed it filters `installed` for ` [install]` only;
  `artifacts` (the create_setup_artifacts return) is never added.
- F8: `sed` of `_install_all` -> `except (Exception` (BaseException/SystemExit not caught); `_run_install`
  -> explicit `except SystemExit`. Confirmed the asymmetry.
- Lane 2 ran live Python to verify is_filename_safe (all vectors rejected, no bypass), parse_not_before,
  the payload-blind parser (post-`---` Status not captured), ACK_WRITER totality/disjointness, Set/Order
  parsing/sort/warnings, and versioning ordering - all confirmed correct.

## Sampling notes

- engine.py is large (~2857 lines); lanes read the install/rollback/diagnostics/pointer paths in full
  rather than the entire file. All other modules read in full.
