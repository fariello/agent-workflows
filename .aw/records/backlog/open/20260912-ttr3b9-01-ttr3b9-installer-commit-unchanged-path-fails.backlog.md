- Id: ttr3b9
- Status: open
- Blocks-Release: next
- Set: ttr3b9
- Priority: high
- Work-Kind: bug
- Summary: aw install ends 'Error: git commit failed' when the framework is already current: the manifest is offered for commit unchanged, and a back-filled .aw/.gitignore was missing from the commit set

## Workflow history
- 2026-09-12 created (aw backlog): aw install ends 'Error: git commit failed' when the framework is already current: the manifest is offered for commit unchanged, and a back-filled .aw/.gitignore was missing from the commit set

## Reported and FIXED 2026-09-12 (filed for the record, per the carrier rule)

The maintainer ran `aw install` in a target repo and it ended:

    Committing changes...
    On branch main
    Changes not staged for commit:
            modified:   .aw/.gitignore
    Untracked files:
            .aw/config/
    no changes added to commit (use "git add" and/or "git commit -a")
    Error: git commit failed.

Surfaced while verifying the `2812t3` fix, but only the FIRST defect below is related to it; the
second is older and is what actually produced the error.

## Two defects composed

FIRST, `.aw/.gitignore` WAS MISSING FROM THE COMMIT SET. It is TRACKED, and `_ensure_aw_gitignore`
appends to it, but it reached `prompt_and_run_commit`'s `files_to_commit` through NEITHER `installed`
(the manifest install reports it `[already current]`, because the manifest hash matches BEFORE the
append) NOR `agents_status`. So the back-fill was applied and then left uncommitted.

SECOND, AND THIS IS WHAT CAUSED THE ERROR: the install manifest is appended to `installed` as
`[overwrite]` on EVERY run even when its bytes are unchanged (`install_all`, the `manifest_rel`
append). `git commit -- <paths>` FAILS with "no changes added to commit" when NONE of the given paths
has a stageable change. In a repo whose framework was fully current, the set was exactly
`.aw/system/managed-sections.json`, that path had no diff, and the commit died. The user was left at a
red error with a dirty tree.

Note the failure was INVISIBLE on a repo with any other pending change, which is why it survived: any
real file change gave the commit something to do.

## The fix

TWO CHANGES IN `prompt_and_run_commit`, both in one place deliberately.

1. A `git status --porcelain -- <paths>` probe DROPS every path git sees no change in, so whatever a
   producer claims, only genuinely-changed paths are offered. This is the general guarantee; fixing
   the manifest producer alone would leave the next stale producer free to reintroduce it.
2. A dirty-check ADDS `.aw/.gitignore` when it has uncommitted changes. Implemented as a git query
   rather than a flag threaded from `_ensure_aw_gitignore`, because the append happens on several
   paths (`write_setup_marker`, the records-migration branch) and only some are reachable from any
   given entry point (`engine.run` for `aw install` vs `cli._install_one` for `aw setup`), so a flag
   would be correct for one and stale for the others.

Verified end to end on the reported scenario (framework current, `.aw/.gitignore` missing the two
`2812t3` patterns, six state/config files present): run 1 offers `[modified] .aw/.gitignore` and
reports `Changes committed successfully`, leaving only the intentionally-tracked
`.aw/config/project.json` untracked; run 2 offers nothing and exits clean. New
`InstallerCommitSetTests` covers both halves and both fail against the old code.

## Not fixed here, and deliberately

The manifest producer still claims `[overwrite]` on an unchanged file, so the installer's own REPORT
still says it touched a file it did not. That is cosmetic once the commit set is filtered, but it is a
separate honesty defect in `install_all` and wants its own change; the filter above means it can no
longer break a commit.
