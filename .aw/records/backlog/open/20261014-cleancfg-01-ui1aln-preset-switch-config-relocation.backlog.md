- Id: ui1aln
- Status: open
- Blocks-Release: next
- Set: cleancfg
- Priority: medium
- Work-Kind: bug
- Summary: aw install --preset switch across config placements (target .aw/config <-> AW_HOME) leaves the old project.json authoritative; needs a relocation/migration path

## Workflow history
- 2026-10-15 created (aw backlog): aw install --preset switch across config placements (target .aw/config <-> AW_HOME) leaves the old project.json authoritative; needs a relocation/migration path

Found 2026-10-15 reviewing plan on0keo at 461fdf679. project_context.project_config_dir prefers <repo>/.aw/config/project.json whenever it exists, but persist_project_policy writes to the NEW preset's config_project placement. Probe: private-target install, then persist a local-only policy -> project.json written at <AW_HOME>/projects/<id>/config/ AND the stale private-target <repo>/.aw/config/project.json remains and is the one every reader resolves. Today aw install --preset local-only on a private-target repo instead produces an incoherent local-only/tracked/repository policy because resolve_policy_noninteractive keeps the old delivery/backend. Plan on0keo makes such a cross-placement switch refuse with a PolicyError; this item owns the real relocation (move config, policy keys and cutovers to the new placement, remove or retire the old one) which is a migration with tracked-file deletion and needs its own design.
