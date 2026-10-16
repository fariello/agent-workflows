- Id: wbz75c
- Status: open
- Blocks-Release: next
- Set: cfgreloc
- Priority: medium
- Work-Kind: bug
- Summary: aw install --records-backend change on an installed repo repoints the records resolver without moving the existing records tree, orphaning it

## Workflow history
- 2026-10-16 created (aw backlog): aw install --records-backend change on an installed repo repoints the records resolver without moving the existing records tree, orphaning it

Found 2026-10-16 while graduating ui1aln. Probe (scratch AW_HOME, AW_NO_REEXEC=1): install a repo with --preset private-target, commit, add .aw/records/backlog/mine.md, then 'python3 -m agent_workflows install <repo> --records-backend home -y --no-interactive' exits 0 and project.json records 'preset: private-target, records_backend: home, delivery_mode: tracked'. resolve_project_context then returns records root <AW_HOME>/projects/<id>/records while mine.md stays in <repo>/.aw/records and is no longer seen by any reader. The config placement is unchanged, so the ui1aln cross-placement guard (install_wizard.resolve_policy_noninteractive) does not fire. Spec 20260810-1447-01 Section 8 says a placement change invokes migration planning rather than silently moving files; here nothing moves and the resolver silently switches. Distinct from ui1aln (config placement) but the cfgreloc placement-switch planner (plan pl3f6e) is the natural place to reuse.
