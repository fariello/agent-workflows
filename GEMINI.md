# Antigravity Rules for agent-workflows

## 1. NEVER WORK OR EDIT DIRECTLY IN MAIN (ISOLATION REQUIREMENT)
- The primary checkout on `main` MUST remain clean at all times.
- Live runner validation suites, baseline checks, and integration gates execute directly in the primary checkout. Uncommitted or in-progress edits on `main` corrupt concurrent runner validations and break CI/integration.
- ALWAYS create and work in an isolated git worktree under `.aw/worktrees/<name>` (or a dedicated feature branch in an isolated worktree):
  ```sh
  git worktree add -b <branch-name> .aw/worktrees/<worktree-name> main
  ```
- All editing, test runs, and commits MUST take place inside that isolated worktree.
- Integrate back cleanly through the integration gate under the repository integration lock (`aw integration-lock`).

## 2. Remote SSH Terminal & File Path Rules
- You are operating in a remote SSH terminal environment.
- NEVER use the `file://` URI scheme under any circumstances.
- NEVER output absolute file paths (such as `<home>/...` or `/path/to/...`).
- ALWAYS output file paths as plain text relative to the repository root (e.g. `path/to/file.py` or `.aw/records/...`), with no `file://` URI scheme and no markdown link wrappers.

## 3. Prose Style: No Em or En Dashes in User-Facing Prose
- Write NO em or en dashes in user-facing prose you author (READMEs, CHANGELOG, docs, or explanations meant for end users). Use plain hyphens (-) or colons/parentheses.
- Internal AI artifacts (IPDs, commit messages, code comments, research docs) are exempt.

## 4. Shared Checkout & Tooled Commits
- Other agents and humans work concurrently in this repo.
- Uncommitted changes or untracked files you did not create are not yours; never revert, stage, discard, reformat, or "clean up" another party's work.
- You MUST commit through `aw commit`:
  ```sh
  aw commit <plan> -- <paths>
  # Or when no plan governs the change:
  aw commit --no-plan -m "<msg>" -- <paths>
  ```
- Before touching `main`, always hold the repository integration lock:
  ```sh
  aw integration-lock -- git merge --ff-only <branch>
  ```

## 5. How to Run the Test Suite
- Run bare: `python3 -m pytest` (or `make test`).
- Do NOT pass `-n0` (disables xdist, making the suite 4x-6x slower).
- Do NOT pass an extra `-q` (compounds into `-qq` and hides the pass summary).
- Do NOT pass `-p no:randomly` (disables test-order randomization).

## 6. Test Outcomes, Not Code Structure (No Code-Pinning Tests)
- Tests must test observable behavior and outcomes.
- NEVER write tests that inspect source code using `inspect`, `ast`, regex, or line counting.
- Tests must execute the code and assert on real outputs, exit codes, and side effects.
