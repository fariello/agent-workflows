- Id: kvwwt0
- Status: graduated
- Graduated-To: cleancfg
- Blocks-Release: next
- Set: cleancfg
- Priority: high
- Work-Kind: bug
- Summary: completely-clean-target install stages .aw/system, .aw/records, .aw/.gitignore and host adapters into the target despite records_backend home and the zero-target-delta promise

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: irjoga
- 2026-10-12 created (aw backlog): found while graduating mbx0o4 (plan p425hv)

Found 2026-10-12 while graduating backlog mbx0o4 at HEAD ffce69f34. Scratch `aw install <repo> --preset completely-clean-target -y --no-interactive` (AW_NO_REEXEC=1, HOME and AW_HOME pointed at a temp dir) leaves STAGED in the target: 161 paths under `.aw/system/`, 41 under `.aw/records/` (although the stored policy says `records_backend: home` and the resolver puts records at `<aw_home>/projects/<id>/records`), `.aw/.gitignore`, `.aw/inbox`, `.aw/workflow-artifacts`, `.gitignore`, `.gitleaksignore`, `.github/workflows`, plus the host adapters (AGENTS.md, .agents/skills, .claude/commands, .opencode/commands). AW_HOME receives no system or records. Plan p425hv fixes only the config and install-state writers (mbx0o4) and makes the consent plan's Target Delta line state what is actually written; the zero-target-write install itself is spec or061f Phase 3 (parked carrier m15n3k). Decision for the maintainer: build Phase 3, or refuse/relabel the preset until it exists.
