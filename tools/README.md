# Repository Tools

This directory contains standalone utility scripts for repository maintenance and migration.

## `untrack-workflow-artifacts.py`

`tools/untrack-workflow-artifacts.py` safely stops tracking a repository's `workflow-artifacts/` directory without deleting local files.

### Usage

1. **Dry run (default)**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py
   ```
   Inspects the repository state and prints what would be untracked. Makes no changes.

2. **Apply migration (index-only)**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py --apply
   ```
   Removes tracked `workflow-artifacts/` entries strictly from Git's index (`git rm -r --cached`), retains all local working-tree files, appends the `workflow-artifacts/` ignore rule to `.gitignore`, and stages both changes.

3. **Apply and commit**:
   ```bash
   python3 tools/untrack-workflow-artifacts.py --apply --commit
   ```
   Applies the migration and creates a dedicated commit (`chore: stop tracking workflow artifacts`). Rejects committing if unrelated files are staged.

### Remediation Guidance for Already-Committed Artifacts

If a repository has previously committed `workflow-artifacts/` run records to Git history:

1. **Size the Exposure First**:
   Run the local-leaks sanitizer to assess whether committed records contain sensitive local paths, usernames, or session IDs:
   ```bash
   aw sanitize . --agent
   ```

2. **Remediation Option A: Index-Only Stop Tracking (Recommended)**:
   Use `python3 tools/untrack-workflow-artifacts.py --apply` to stop tracking future changes and keep local files. This prevents future commits of run records without rewriting Git history.

3. **Remediation Option B: Git History Rewrite (Optional for Sensitive Exposure)**:
   If committed history contains sensitive credentials or private home paths that must be purged from Git history entirely, use `git-filter-repo` (or BFG Repo-Cleaner) to strip the directory from all commits:
   ```bash
   git filter-repo --path workflow-artifacts/ --invert-paths
   ```
   **WARNING (destructive; run ONLY with explicit human approval):** this REWRITES history, changes every subsequent commit SHA, and requires a coordinated force-push that invalidates all existing clones and open branches/PRs. It is NOT reversible by a normal pull. Do NOT run it automatically or as part of routine remediation; propose it, explain the blast radius, and wait for an explicit human decision before executing (consistent with the toolkit's never-rewrite-history-without-approval posture).
