- Id: bs1iek
- Status: open
- Blocks-Release: next
- Set: bs1iek
- Priority: medium
- Work-Kind: bug
- Summary: aw_upgrade_test.py rehearses the MAIN checkout's code when run from a lane worktree, silently invalidating its own results

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing IPD i8u6hh (verstamp Order 01).

tools/aw_upgrade_test.py resolves its installer command to [sys.executable, '-m', 'agent_workflows'] (_installer_cmd). In a lane worktree that resolves through the EDITABLE install to the MAIN checkout's agent_workflows package, not the worktree the agent is testing, so the rehearsal exercises code that does not contain the change under test.

MEASURED 2026-09-23 while validating i8u6hh: the first rehearsal of ansurv reported [version-unchanged] and a 1.2.1 stamp with the fix present in the worktree; re-running with PYTHONPATH pinned to the worktree stamped 1.3.0rc2.dev3716+g0189db24.d20260923 and both version observations disappeared. The result flipped on the import path alone.

This matters because the tool's own docstring names exactly this as disqualifying: running the installed console script 'would silently rehearse a DIFFERENT (possibly older) version than the checkout under test, which is the one mistake that would invalidate every result this tool produces'. The guard it implements (prefer -m over a PATH aw when agent_workflows/cli.py exists beside the tool) does not cover the editable-install case, because -m still resolves by sys.path and not by the tool's own location.

USER-PERCEPTIBLE IMPACT (why bug, not chore): the failure is SILENT and produces a confident wrong answer. An agent or maintainer validating a fix from a worktree reads 'the defect is still present' and either abandons a correct fix or reports a false negative. It cost one wasted rehearsal cycle in this turn and was caught only because an in-process install had already proved the opposite.

LIKELY FIX: make _installer_cmd resolve the package from the tool's OWN location (pass the repo root on PYTHONPATH, or invoke with -S/an explicit sys.path entry rooted at Path(__file__).parent.parent), and have probe record WHICH agent_workflows module file the install subprocess actually imported so a mismatch is visible in the report rather than invisible.

WHERE: tools/aw_upgrade_test.py, _installer_cmd (the [sys.executable, '-m', 'agent_workflows'] return).
