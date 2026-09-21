- Id: 19lmbe
- Status: open
- Blocks-Release: next
- Set: 19lmbe
- Priority: high
- Work-Kind: bug
- Summary: aw backlog set --status ignores --dry-run and mutates the tree, because the path-form handler reads a nonexistent 'apply' flag

## Workflow history
- 2026-09-21 created (aw backlog): Filed from /plan-review of yv4tb1 after the defect fired on me during review.

`aw backlog set <path> --status <s> --dry-run` IGNORES `--dry-run` AND PERFORMS THE TRANSITION. It
rewrites the item, moves the file into the new status directory, and appends a history record, while
printing only the success line `aw backlog set: <name> -> <status>`. It prints NO preview and gives no
indication that a write occurred rather than a simulation.

MEASURED, AND IT FIRED ON A REVIEWER RATHER THAN BEING FOUND BY READING. During `/plan-review` of plan
`yv4tb1` on 2026-09-21 I ran the command that plan instructs an executor to run, with `--dry-run`
added, to check whether the command was well-formed. It closed backlog item `6h7y2y` from `graduated`
to `done`: the tracked file at `.aw/records/backlog/graduated/20260906-graduate-01-6h7y2y-...` was
deleted and an untracked copy appeared under `done/` reading `- Status: done`. I reverted it (`rm` the
new copy plus `git restore` the original) and then REPRODUCED it deliberately to confirm determinism.
Nothing was committed. That the accident closed a RELEASE-RELEVANT LEDGER ENTRY with a bare
`status -> done` history line, in a shared checkout, is why this is filed `bug` and not `chore`: the
user-perceptible impact is a silent unintended mutation of committed records.

ROOT CAUSE, WHICH IS A ONE-LINE FLAG-NAME MISMATCH. `aw backlog set` has TWO handlers, chosen by
whether `--status` is present (`cli.py:12636`). With `--status` ABSENT the positional form routes to
`status_set.run_set_command`, which reads `getattr(args, "dry_run", False)` (`status_set.py:1667`) and
correctly previews. With `--status` PRESENT it routes to `backlog.run_set`, whose only write guard is
`if not getattr(args, "apply", True)` (`backlog.py:838`). `aw backlog set` DEFINES NO `--apply` FLAG
(only `--dry-run`; confirmed in `--help`), so the `getattr` default of `True` always wins and the
guard is unreachable. The sibling `aw backlog new` IS `--apply`-gated, which is where the wrong flag
name plausibly came from.

CONFIRMING CONTRAST, so the fix target is unambiguous:

    aw backlog set done 6h7y2y --dry-run            # honors it: prints `graduated -> done (dry-run)`, writes nothing
    aw backlog set <path> --status done --dry-run   # IGNORES it: performs the transition

SUGGESTED FIX. Make `backlog.run_set` read `dry_run` (the flag that actually exists) rather than
`apply`, so the two forms agree; or route both spellings through one handler. Prefer whichever keeps a
SINGLE write-guard predicate, since the divergence is the whole defect. A regression test should assert
that BOTH spellings leave the tree byte-unchanged under `--dry-run`, because a test covering only the
positional form is what let this ship.

RELATED BUT DISTINCT. `f5pttg` (open) is about `aw ipd set` writing WITHOUT a confirmation prompt; this
is about a dry-run flag that is accepted and then ignored, which is worse in kind because the operator
explicitly asked for no write. `3q6tcr` (open) concerns missing `--work-kind`/`--priority` setters on
this same verb and is unrelated to the guard.

GATE. Carries `- Blocks-Release: next` per the repository rule that a live `bug` gates the next
release.
