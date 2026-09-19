- Id: e17a2e
- Status: open
- Blocks-Release: next
- Set: e17a2e
- Priority: high
- Work-Kind: bug
- Summary: runner_shared reclaim path calls .strip() on _run_git's 3-tuple, raising AttributeError whenever a lane has no worktree

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): runner_shared reclaim path calls .strip() on _run_git's 3-tuple, raising AttributeError whenever a lane has no worktree

FOUND while executing IPD metc8b (dirtygates-02), in code that plan does not touch.

WHAT IS WRONG. In `agent_workflows/runner_shared.py`, the lane-reclaim path does:

    status_out = _run_git(repo, ["status", "--porcelain"])
    holds_work = bool(status_out.strip())

but `_run_git` returns a 3-tuple `(rc, stdout, stderr)`, so `.strip()` raises
`AttributeError: 'tuple' object has no attribute 'strip'`. Every other caller in the module
unpacks the tuple (e.g. `_rc, out, _err = _run_git(...)`), so this one line is inconsistent with
the established convention and cannot ever have executed successfully.

WHY IT IS LATENT RATHER THAN CONSTANTLY FIRING. The line is in the `else` arm reached only when
`lane is None`, i.e. when the record carries no `work_dir`, so the common isolated-lane path takes
the `lane["holds_work"]` branch instead and never touches it. That is also why the suite is green:
no test exercises the no-worktree arm.

WHY IT MATTERS. The arm decides `holds_work`, which gates whether a lane is cleaned up completely
or preserved. An `AttributeError` there fires on an INTERRUPT/RECOVERY path, which is exactly when
the runner is trying not to lose work, and it would surface as an unhandled exception rather than a
classified refusal.

FIX SHAPE. Unpack like every neighbour (`_rc, status_out, _err = _run_git(...)`), and add a test
covering the `lane is None` arm, since its absence is what let this ship.

EVIDENCE: the repository's own type checker flags it (`Cannot access attribute "strip" for class
"tuple[int, str, str]"`); the same diagnostic is present at HEAD before any metc8b edit, confirmed
by reading `git show HEAD:agent_workflows/runner_shared.py`.
