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

---

## Required Validation

1. **Selective Commit Verification**:
   * Add a dirty untracked file to the target repo.
   * Run the installer, select `[Y]` to commit.
   * Assert the framework files are committed, but the dirty file is left unstaged.
2. **Diagnostic Menu Assertions**:
   * Simulate dry-run and exit flows for options 1, 2, and 3 under mock TTY stdin environments.

---

## Open Questions

1. **Should we attempt to stash and unstash dirty files during a pull?**
   * *Recommendation*: No. If the worktree is dirty and the user selects Option 1 (Pull), git pull might fail naturally if there are conflicting changes. We should let Git handle this and cleanly report the failure rather than attempting complex stashing logic which can risk data loss.
2. **What if the branch has no tracking remote?**
   * *Recommendation*: The diagnostics block should skip the remote sync check and show `Remote: No tracking remote branch configured` without warning.
