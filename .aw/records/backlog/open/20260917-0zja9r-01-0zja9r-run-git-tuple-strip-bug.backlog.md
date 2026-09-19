- Id: 0zja9r
- Status: open
- Blocks-Release: next
- Set: 0zja9r
- Priority: medium
- Work-Kind: bug
- Summary: runner_shared._reset_item_for_retry treats _run_git's 3-tuple as a string, so the non-lane holds_work branch is always truthy

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): runner_shared._reset_item_for_retry treats _run_git's 3-tuple as a string, so the non-lane holds_work branch is always truthy

MEASURED at HEAD 1171f7b2, and PRE-EXISTING (not introduced by plan pr5b0t; the same code is at HEAD, line 2734 there).

WHERE: agent_workflows/runner_shared.py, in the retry-reset path, the branch taken when there is NO lane:

    status_out = _run_git(repo, ["status", "--porcelain"])
    holds_work = bool(status_out.strip())

WHAT IS WRONG: _run_git returns a 3-tuple (returncode, stdout, stderr), not a string. tuple has no .strip(), so this raises AttributeError the moment the non-lane branch is reached; a type checker flags it as 'Cannot access attribute strip for class tuple[int, str, str]'. The lane branch just above it (holds_work = bool(lane['holds_work'])) is the one normally taken, which is presumably why this has survived.

CORRECT SHAPE: unpack it, e.g. rc, out, _err = _run_git(repo, ['status', '--porcelain']) then holds_work = rc == 0 and bool(out.strip()).

WHY IT MATTERS: the branch decides whether an interrupted item is reset to queued as if it never ran, i.e. whether work is discarded. A crash there is safer than a wrong answer, but neither is acceptable on a work-preservation path.

FOUND BY: plan pr5b0t (lanestrand-01) while adding the stranded-lane predicate to the same module; reported rather than fixed, since it is outside that plan's Scope-Paths intent and its own contract forbids opportunistic scope.
