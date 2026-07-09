# IPD: Interactive Git Pre-flight checks and post-install commit workflow

- Date: 2026-07-09
- Concern: Usability, safety, and Git integration of the installer CLI.
- Scope: Enhance the installation workflow with target repo git health checks (dirty state, pull/sync state) and a post-install prompt to auto-commit the changes.
- Status: PENDING / PROPOSAL

## Goal

Provide a smooth, transparent Git integration for the installer:
1. **Consolidated Git Diagnostics (Pre-flight)**: Instead of multiple sequential prompts, run all diagnostics upfront, present a unified status summary, and offer a clear single-choice menu.
2. **Selective Auto-Commit (Post-install)**: Offer to commit the framework-only files in a TTY session, showing exactly what will be committed and providing the fallback command if they decline.

---

## Proposed Design

* **Execution Safety**: All Git commands (`git fetch`, `git status`, `git pull`, `git commit`) must be run via `subprocess.run(shell=False)` with arguments passed as a list of strings to avoid shell injection or argument escaping vulnerabilities.
* **KISS Diffing**: The `--diff` feature must use Python's standard-library `difflib` to ensure cross-platform availability and zero-dependency implementation.

### Phase 1: Consolidated Pre-flight Git Diagnostics

Before applying any changes, if the target repository is a Git repository, the installer runs:
1. `git status --porcelain` to check for local changes.
2. A fast `git fetch` (with a timeout of 3 seconds, degrading gracefully if offline/unauthorized).
3. `git status -sb` or equivalent `git rev-list` to check sync status with the tracking remote.

The installer then prints a clean **Git Diagnostic Block**:

```
Git Diagnostics:
  - Branch 'main' is behind 'origin/main' by 2 commits (needs pull).
  - Repository has 3 uncommitted local files (dirty).

What would you like to do?
  [1] Pull latest changes (git pull --rebase) and proceed
  [2] Proceed anyway (risk of merge/overwrite)
  [3] Abort installation
Select an option [1-3, default 1]: 
```

* If option **[1]** is selected: Run `git pull --rebase`. If it succeeds, proceed with the install. If it fails, abort with instructions.
* If option **[2]** is selected: Proceed with the install immediately.
* If option **[3]** is selected: Abort cleanly.

*Non-TTY / `--yes` / `--no-interactive` behavior*: Diagnostics are skipped, or warnings are printed to stderr but execution proceeds automatically.

---

## Phase 2: Post-Install Selective Commit

After printing the install summary, the installer determines the list of files it actually created or modified (paths in `installed` and `pruned` lists, plus modified framework pointers like `AGENTS.md` and `.gitignore`).

If running interactively:
1. Display the commit plan:
   ```
   Ready to commit framework sync changes:
     [added    ] .agents/workflows/...
     [modified ] .gitignore

   Would you like the installer to commit these changes? [Y/n]
   ```
2. If the user accepts:
   * Run `git commit -m "agent-workflows: sync via installer" -- <only modified paths>` (ensuring other unrelated dirty files in the workspace are left unstaged/uncommitted).
3. If the user declines:
   * Print a helpful manual command:
     `To commit these changes manually, run:`
     `  git commit -m "sync agent-workflows" -- <paths...>`

### Phase 3: Safety and Quality of Life Enhancements

1. **Customization Protection (Warnings on Edited Shims)**:
   * Before replacing or pruning any `.md` shim inside `.opencode/commands/` or `.claude/commands/`, check if its contents contain the standard signature line or are identical to a generated shim.
   * If a file has been manually edited/customized by the developer, prompt:
     `⚠️ Warning: .opencode/commands/<name>.md has manual modifications that will be overwritten. Proceed? [y/N]`
   * If they choose No, skip that shim or abort.

2. **Rollback / Undo Support (`--undo`)**:
   * Add a command-line flag `aw install --undo` (or `install-workflows.py --undo`).
   * When triggered, identify the most recent backup folder under `.agents/backups/`.
   * Restore all files from that backup directory to their original paths in the target repository, cleanly rolling back the installation.

3. **Backup Auto-Pruning (Clutter Control)**:
   * During installation (after creating a new backup), count the directories under `.agents/backups/`.
   * If there are more than 5 backup folders, delete the oldest ones to maintain a rolling window of the last 5 backups.

4. **Change Diffs (`--diff` / `-d`)**:
   * Support a `--diff` command-line option.
   * Instead of installing, show a line-by-line colored diff (similar to `git diff`) of the differences between the current installed files and the source files.

---

## Required Validation

1. **Selective Commit Verification**:
   * Add a dirty untracked file to the target repo.
   * Run the installer, select `[Y]` to commit.
   * Assert the framework files are committed, but the dirty file is left unstaged.
2. **Diagnostic Menu Assertions**:
   * Simulate dry-run and exit flows for options 1, 2, and 3 under mock TTY stdin environments.
3. **Undo / Rollback Verification**:
   * Install the framework, modify a file, then trigger `aw install --undo`.
   * Assert the modified file is successfully restored to its backup state.
4. **Backup Auto-Pruning**:
   * Simulate creating 7 sequential installations.
   * Assert that only the 5 most recent backup folders remain in `.agents/backups/`.
5. **Customization Protection**:
   * Manually edit a command shim file, run the installer, and verify it alerts the user before overwriting.

---

## Open Questions

1. **Should we attempt to stash and unstash dirty files during a pull?**
   * *Recommendation*: No. If the worktree is dirty and the user selects Option 1 (Pull), git pull might fail naturally if there are conflicting changes. We should let Git handle this and cleanly report the failure rather than attempting complex stashing logic which can risk data loss.
2. **What if the branch has no tracking remote?**
   * *Recommendation*: The diagnostics block should skip the remote sync check and show `Remote: No tracking remote branch configured` without warning.
3. **Should the rollback option (`--undo`) stage the restored files in Git?**
   * *Recommendation*: Yes, if Git is available, it should stage the restored/deleted files to mirror the state before the install.
