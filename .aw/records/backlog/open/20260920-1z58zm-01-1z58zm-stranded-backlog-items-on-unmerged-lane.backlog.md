- Id: 1z58zm
- Status: open
- Set: 1z58zm
- Priority: medium
- Work-Kind: chore
- Summary: Two release-blocking backlog items (34q6ha, mepbmp) exist only on the unmerged lane aw/lane/udgilu_attempt2, so they are invisible to attention, find and every release-gate check

## Workflow history
- 2026-09-20 created (aw backlog): Found while verifying a session handoff's claim that a suite failure was unfiled: it WAS filed, as 34q6ha, but on a lane that never merged. git merge-base --is-ancestor d7950155 HEAD returns 1 and aw find backlog 34q6ha returns nothing. Verified each stranded item individually at HEAD: 34q6ha's test is fixed by f1983f30 (28 passed) but its second, smaller defect is still live (resolve_plan_path raises TypeError on a str repo, runner_shared.py:5587); mepbmp no longer reproduces (43 passed). Filed chore not bug because no user-visible behavior is wrong; the loss is in the record tree.

MEASURED AT HEAD 9d02743b. Commit `d7950155` ("backlog(34q6ha,mepbmp): file two pre-existing suite failures found verifying udgilu") created two backlog items, both `Status: open`, both `Work-Kind: bug`, both `Blocks-Release: next`. Neither file exists at HEAD:

    $ git merge-base --is-ancestor d7950155 HEAD ; echo $?
    1                                   # NOT an ancestor
    $ git branch -a --contains d7950155
    + aw/lane/udgilu_attempt2           # the ONLY ref containing it
    $ aw find backlog 34q6ha -p
                                        # no output
    $ aw find backlog mepbmp -p
                                        # no output

So two items that declare themselves release blockers are invisible to `aw attention`, `aw find` and every release-gate check, because they were committed inside a lane worktree whose branch never merged. `git diff --stat HEAD...aw/lane/udgilu_attempt2` shows exactly three files stranded: those two items and a pending IPD.

WHY THIS IS THE INTERESTING FAILURE AND NOT A BOOKKEEPING NIT. The release gate is only as good as the set of items it can SEE. An item filed as `Blocks-Release: next` on a lane that is later abandoned is strictly worse than never filing it, because the author believes the gate is armed and nothing reports otherwise. Nothing in `aw check` looks for records that exist on an unmerged lane, so this class of loss is silent by construction.

WHAT IS AND IS NOT STILL BROKEN, verified individually rather than assumed from the item text.

`34q6ha` (test_standalone_verify pinned live plan `mp289j` as a not-executed fixture): the TEST is FIXED on main by `f1983f30`, which replaced the real-repo lookup with a temp-repo fixture. Confirmed `python3 -m pytest tests/test_standalone_verify.py` -> `28 passed`. So the primary defect is resolved and its item should close, not re-open. But the item ALSO recorded a second, smaller defect that nobody has touched, and that one is still live at HEAD:

    $ python3 -c "from agent_workflows import runner_shared as rs; rs.resolve_plan_path('/tmp/x','','bbbbbb')"
    TypeError: unsupported operand type(s) for /: 'str' and 'str'

`runner_shared.resolve_plan_path` builds `repo / ".aw"` without coercing `repo` (runner_shared.py:5587), so a `str` argument raises instead of being accepted as path-like. Severity is LOW and stated honestly: every live caller in `oc_runipd.py` and `agy_runipd.py` passes a `Path`, so nothing is failing in production today; it is a latent trap in a function shared by both runners, and it is the only part of `34q6ha` that still needs a fix.

`mepbmp` (test_turn_bounds asserted a non-isolated turn carries no permission policy): does NOT reproduce at HEAD. `python3 -m pytest tests/test_turn_bounds.py` -> `43 passed`. Whatever changed on main since `5211f722` settled it, so this item is stale and should close as already-resolved rather than being carried forward.

THE ASK, which is a records decision and not a code fix. Decide whether to (a) re-file the still-live `resolve_plan_path` coercion as a fresh low-priority item at HEAD and let the two stranded items die with the lane, or (b) cherry-pick `d7950155` onto main and immediately close both items with the evidence above. (a) is less history-rewriting and loses the diagnosis prose; (b) preserves the record but lands two items only to close them. This item exists so the choice is made deliberately instead of by abandonment.

RELATED, same root cause, already filed: the ten backlog items duplicated across `graduated/` and `done/` (`fwq5nu`, `5bmq5f`) are the other half of "records written inside a lane do not reliably reach main". A fix that makes lane-committed records land or fail loudly would address both.

NOT FILED AS A BUG, deliberately. No user-visible behavior is wrong: a command that ran, ran correctly. The loss is in the record tree, so this is a `chore` under the perceptibility test in AGENTS.md, and it carries no `Blocks-Release` of its own even though the items it describes claim one.
