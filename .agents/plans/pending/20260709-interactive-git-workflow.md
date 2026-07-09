# IPD: Interactive Git Pre-flight checks and post-install commit workflow

- Date: 2026-07-09
- Concern: Usability, safety, and Git integration of the installer CLI.
- Scope: Enhance the installation workflow with target repo git health checks (dirty state, pull/sync state) and a post-install prompt to auto-commit the changes.
- Status: PENDING / PROPOSAL

## Goal

Automate common Git housekeeping tasks during framework installation/update:
1. **Pre-flight checks**: Warn the user if the target repository has uncommitted changes (dirty state) or is out of sync with its remote tracking branch, offering to pull first.
2. **Post-install commit prompt**: Offer to automatically commit the staged changes (and *only* the changes staged by the installer) at the end of a successful installation, if running interactively.

---

## Proposed Design

The installer engine (`engine.py` / `cli.py`) will implement the following two interactive phases when running in a TTY (and not bypassed by `--yes` / `--no-interactive`):

### Phase 1: Pre-flight Git Checks (Pre-install)

Before beginning the migration or sync process, if the target directory is a Git repository, the installer will run a series of diagnostics:

1. **Dirty Worktree Check**:
   * Run `git status --porcelain`.
   * If there are uncommitted changes, warn the user:
     `⚠️ Target repository has uncommitted changes.`
   * Ask: `"Do you want to continue the installation anyway? [y/N]"` (default No to prevent mixing framework updates with active feature work).

2. **Remote Synchronization Check**:
   * Attempt a fast remote fetch with a short timeout: `git fetch --quiet --timeout=3` (degrades gracefully if offline or remote access fails).
   * Run `git status -sb` or inspect `git rev-parse` differences to check if local is ahead or behind the remote branch.
   * If local is behind the remote, warn the user.
   * Ask: `"Local repository is behind remote. Would you like to pull changes before continuing? [y/N]"`
   * If confirmed, execute `git pull` and verify it succeeds before proceeding.

### Phase 2: Post-install Commit Prompt (Post-install)

After the installation is complete and the summary of changes is printed, if `use_git` is active and we are in an interactive TTY:

1. **Ask for Commit**:
   * Prompt: `"Would you like to commit the framework changes? [Y/n]"` (default Yes).
2. **Commit Only Sync Files**:
   * To prevent committing unrelated changes that the user might have in their worktree, the commit command should target **only** the list of files staged or modified by the installer (the files listed under `installed` and `pruned` paths, plus the modified `.gitignore` / `AGENTS.md` pointer).
   * Run:
     `git commit -m "agent-workflows: sync via installer" -- <list of modified files>`

---

## Required Validation

1. **Non-TTY / Piped Mode**: Pre-flight prompts are skipped, and the installer behaves non-interactively (as it does today).
2. **Bypass Flag (`--yes`)**: All prompts (both pre-flight pulls and post-install commits) are skipped.
3. **Dirty Worktree Handling**:
   * Confirm that responding "no" aborts the installer cleanly with exit code 1.
   * Confirm that responding "yes" allows the sync to proceed.
4. **Selective Commit**:
   * Plant a dirty file in the target repository before running the installer.
   * Run the installer, answer "yes" to the commit prompt, and verify that the installer files are committed but the unrelated dirty file remains uncommitted/staged.

---

## Open Questions

1. **How should we handle a failed `git pull`?**
   * *Recommendation*: If the `git pull` fails (e.g. due to merge conflicts), abort the installation immediately with a clear error so the developer can resolve the conflict manually.
2. **Should this be part of the `engine` run or handled at the `cli` wrapper level?**
   * *Recommendation*: The user-interactive prompts (using stdin/stdout) are best placed in the CLI wrapper (`cli.py` / `install-workflows.py`) or driven via `term.py` callbacks, keeping the core installation logic (`engine.py`) programmatic and easily testable under unit tests.
