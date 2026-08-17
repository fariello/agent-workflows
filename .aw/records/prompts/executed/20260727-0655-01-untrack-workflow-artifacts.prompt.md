# Reverse the `workflow-artifacts/` tracking policy

Implement a reversal of the prior policy requiring `workflow-artifacts/` to be committed and tracked.

## Decision

`workflow-artifacts/` is a high-risk, low-value working directory. Agents may place sensitive or publication-inappropriate material there, including local/system paths, private-repository references, private discussion or operational detail, and other information that does not belong in repository history. Across several thousand hours of use, its tracked history has provided no practical value.

Treat the directory as local, ignored working material. Do not require it to be committed, and do not encourage agents to force-add it.

## Implement

- Update the relevant workflow, installer, templates, documentation, and agent instructions to supersede the prior “track `workflow-artifacts/`” requirement.
- Add `workflow-artifacts/` to repository `.gitignore`, with a concise comment explaining that it may contain sensitive agent-generated working material and must not be committed.
- Ensure generated guidance tells agents not to use `git add -f` or otherwise force-track this directory.
- Add the accompanying `untrack-workflow-artifacts.py` migration utility in the appropriate project location, document it, and test it in a temporary Git repository.
- Make migration installer-supported but opt-in or explicitly confirmed. An installer must not silently remove tracked files, stage repository changes, or create a commit. It may detect the old state and clearly offer or document the migration.

## Migration behavior

The preferred migration is **not** backup → delete → restore. Use Git’s index-only removal instead:

```bash
git rm -r --cached -- workflow-artifacts
```

This removes tracked copies from Git while preserving the user’s working-directory files. The migration must then add and stage the `.gitignore` rule, so the next intentional commit both removes historical tracking and prevents accidental re-addition. It must not delete the local directory or its contents.

The utility should default to a read-only dry run; require an explicit `--apply` to modify the index or `.gitignore`; and never create a commit unless the user separately requests it. Refuse unsafe cases rather than staging unrelated `.gitignore` edits or unrelated changes in an automated commit.

## Verification

Before reporting success, verify that:

- a repository with tracked `workflow-artifacts/` ends with the directory still present locally but removed from Git’s index;
- `.gitignore` contains the documented ignore rule;
- the utility’s dry run performs no changes;
- an already-untracked directory is handled idempotently;
- an optional commit, if supported, cannot include unrelated staged files;
- installer behavior is opt-in/confirmed and never silently commits or removes local artifact files.
