- Id: zvyo35
- Status: open
- Blocks-Release: next
- Set: awinstallfix
- Priority: high
- Work-Kind: bug
- Summary: aw install: report no-op cleanly and skip commit prompt when staging is empty

## Workflow history
- 2026-10-23 created (aw backlog): aw install: report no-op cleanly and skip commit prompt when staging is empty

### Problem Statement

When `aw install <dir>` (or `aw install .`) runs on a repository where all framework files are already fully up to date and identical to the upstream package:
1. Every file correctly reports `[no change]`.
2. At the conclusion of the installation flow, `agent_workflows/engine.py:5528-5535` always saves the ownership manifest (`.aw/system/managed-sections.json`) via `manifest_mod.save(manifest, manifest_path)`.
3. It unconditionally executes `_stage_installed_file(plan.repo_root, manifest_rel)` (running `git add -- .aw/system/managed-sections.json`) and appends `.aw/system/managed-sections.json [overwrite]` to the `installed` list (`engine.py:5533-5535`).
4. Because the manifest file content written to disk was byte-for-byte identical to the version already committed at HEAD, `git add` leaves the staging index empty.
5. In `agent_workflows/engine.py:3400-3430`, the commit prompt flow inspects `installed`. Seeing `.aw/system/managed-sections.json`, it reports:
   ```
   Ready to commit framework sync changes:
     [modified ] .aw/system/managed-sections.json

   Would you like the installer to commit these changes? [Y/n]
   ```
6. When the user confirms with `Y`, the installer executes:
   `git commit -m "agent-workflows: sync via installer" -- .aw/system/managed-sections.json`
7. Git finds no changes staged for `.aw/system/managed-sections.json` and outputs:
   `nothing to commit, working tree clean`
   exiting with returncode 1 (standard Git behavior on an empty commit).
8. The installer catches `res.returncode != 0` at `engine.py:3442` and emits:
   `Error: git commit failed.`

This creates a degraded user experience:
- An update operation where everything was already clean and up to date asks the user to commit non-existent changes.
- Selecting the default "Yes" results in a prominent error message indicating that installation failed, causing confusion and false concern that the repository or framework installation is broken.

### Proposed Solution and Scope

1. **Staged Change Verification before Marking Installed (`agent_workflows/engine.py`):**
   - In `_stage_installed_file` or before appending `managed-sections.json` to `installed`, verify whether the file actually produced a git diff relative to the index/HEAD (e.g. check `git diff --name-only --cached` or check content hash equality before staging).
   - If the newly serialized manifest has the identical hash to what was already committed, do not mark it as `[overwrite]` or `[modified]` in `installed`.

2. **Pre-Commit Staging Audit in Commit Prompt (`agent_workflows/engine.py:3396-3430`):**
   - Before printing `Ready to commit framework sync changes:`, verify that `files_to_commit` actually corresponds to staged modifications in Git.
   - If no staged changes exist (working tree and index are clean):
     - Print a clear, positive message: for example, `Framework is up to date; no changes to commit.`
     - Omit the `Would you like the installer to commit these changes?` prompt entirely.
     - Skip running `git commit`.

3. **Graceful Handling of Empty Commit Exit Code:**
   - As defense-in-depth, if `git commit` is executed and returns exit code 1 because the working tree is clean (`nothing to commit`), recognize that specific message instead of reporting `Error: git commit failed.`

4. **Testing (`tests/test_engine.py` / `tests/test_cli_install.py`):**
   - Add a test for re-running `aw install` on an already up-to-date repository:
     - Assert that no spurious commit prompt is presented (or that auto-commit cleanly recognizes zero changes).
     - Assert that `Error: git commit failed` is not printed.
