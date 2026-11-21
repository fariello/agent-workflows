- Id: 3z57rk
- Status: open
- Set: 3z57rk
- Work-Kind: bug
- Priority: high
- Summary: aw install --dry-run --no-interactive executes legacy .agents/ to .aw/ migration live on disk
- Short-Description: aw install --dry-run --no-interactive executes legacy .agents/ to .aw/ migration live on disk
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 created (aw backlog): aw install --dry-run --no-interactive executes legacy .agents/ to .aw/ migration live on disk

## Observed behavior

Running `aw install --dry-run --no-interactive` in a repository with a legacy 1.2.1 `.agents/` layout actually executes the full layout migration live on disk (`git mv` of `.agents/` and `workflow-artifacts/` into `.aw/`, deleting leftover `.agents/README.md` with a backup tarball), and then blocks waiting on an interactive prompt:

```text
AW Policy Update Checkpoint
Keep current policy and proceed? [Y/n/review]
```

## Root cause

1. `agent_workflows/cli.py` (lines 9117 and 9159) calls `mgr.execute_migration(target_backend='repository', leftover_disposition=...)` without passing `dry_run=getattr(args, 'dry_run', False)`, even though `MigrationManager.execute_migration()` in `agent_workflows/layout_migration.py` (line 1067) already accepts `dry_run: bool = False`.
2. After the unintended live migration, `agent_workflows/install_wizard.py` (line 1028) renders the `AW Policy Update Checkpoint` prompt without honoring `--no-interactive` / `--dry-run`.

## Expected behavior

`aw install --dry-run` must never modify the working tree, git index, or `.aw/` directories (forward `dry_run` to `execute_migration()` or preview only), and `--no-interactive` must never block waiting for stdin.
