- Id: qyevpr
- Status: graduated
- Graduated-To: cleancfg
- Blocks-Release: next
- Set: cleancfg
- Priority: high
- Work-Kind: bug
- Summary: re-running aw install overwrites .aw/config/project.json wholesale, discarding run policy, setids, release_gate_work_kinds and every hand-set or earlier-stamped cutover date

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: on0keo
- 2026-10-12 created (aw backlog): found while graduating mbx0o4 (plan p425hv)

Found 2026-10-12 while graduating backlog mbx0o4 at HEAD ffce69f34. Scratch private-target target (AW_NO_REEXEC=1, HOME and AW_HOME in a temp dir): after a first install, set `cutovers.spec_id6` to `2020-01-01` and add `run: {retry_budget: 2}` in `.aw/config/project.json`, then re-run `aw install <repo> --preset private-target -y --no-interactive`. Result: `cutovers.spec_id6` reads `2026-10-12` (today) and `run` is gone. Cause: `install_wizard.persist_project_policy` builds a fresh `ProjectPolicySchema` from the wizard policy and `os.replace`s the file without reading the existing one, so every key it does not model (`run`, `setids`, `release_gate_work_kinds`, `review_findings_gate`, `run_analytics_telemetry`) and the whole `cutovers` map are dropped; `config.sync_cutovers_on_install` then restamps every cutover at today's date, MOVING each grandfathering boundary forward on every reinstall, which retroactively turns previously grandfathered artifacts into violations. `config.sync_cutovers_on_install`'s docstring promises the opposite ('a subsequent install/update never alters previously established cutover boundaries'). Same clobber applies to `.aw/config/local.json` keys written by `run_analytics_wizard.write_settings`.
