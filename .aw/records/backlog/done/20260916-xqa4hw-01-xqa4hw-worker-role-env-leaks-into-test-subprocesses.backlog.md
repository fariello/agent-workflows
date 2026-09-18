- Id: xqa4hw
- Status: done
- Set: xqa4hw
- Priority: high
- Work-Kind: bug
- Summary: AW_EXECUTION_ROLE=worker leaks into pytest subprocesses, so 20 tests fail inside a lane turn and any baseline captured there is wrong

## Workflow history
- 2026-09-18 done (aw set): Same defect as 1uq1cu (found earlier: 20 failures at the then-smaller suite, 31 at HEAD 6ff7a7ba) and fixed by the same change: conftest.py scrubs AW_EXECUTION_ROLE at import time so the test session always runs in the coordinator role, which also cleans the environment every test subprocess inherits. Measured: the marked invocation went from 31 failed / 8080 passed to 8111 passed, 3 skipped, 2 xfailed, identical to an unmarked run. The guard was not relaxed
- 2026-09-16 created (aw backlog): AW_EXECUTION_ROLE=worker leaks into pytest subprocesses, so 20 tests fail inside a lane turn and any baseline captured there is wrong

FOUND while executing IPD metc8b (dirtygates-02). It is not a defect in that plan's code; it is a defect in how a lane turn's environment reaches the test suite, and it directly attacks the execution contract's 'paste the ACTUAL runner output' rule.

WHAT IS WRONG. A runner lane turn sets `AW_EXECUTION_ROLE=worker` in the agent's environment (correctly: the agent must not run driver-only lifecycle verbs). But `python3 -m pytest` inherits it, and so do the SUBPROCESSES the tests spawn, so tests whose own fixtures legitimately invoke `aw ipd begin`/`finalize` are refused with `AW-LIFECYCLE-ROLE-001` and FAIL.

MEASURED 2026-09-16 in lane `metc8b` at commit `dc88a99a`, with NO source edits:
  bare `python3 -m pytest`                        -> 20 failed, 7301 passed, 3 skipped, 2 xfailed
  `env -u AW_EXECUTION_ROLE python3 -m pytest`     -> 7321 passed, 3 skipped, 2 xfailed, 0 failed
Re-running the identical 20 selected node ids with the variable cleared gives `20 passed`. The 20 span
`test_oc_runipd.py`, `test_agy_runipd_cli.py`, `test_ipd_lifecycle_cli.py`, `test_worker_role_refusal.py`,
`test_novalnomerge_integration.py` and `test_runner_backlog_close.py`.

WHY IT MATTERS, and why it is worse than 20 red tests. Every IPD in this repository is validated by
comparing a post-edit failure set against a pre-edit BASELINE. Inside a lane turn that baseline is
poisoned, so an executing agent sees 20 pre-existing failures in exactly the runner/lifecycle area most
plans touch, and has two bad options: mistake them for its own regressions, or wave them off as
'pre-existing' and thereby normalize ignoring 20 red tests. Both corrupt the evidence a human reads. It
also silently invites the anti-pattern of an agent 'discovering' that a suite passes only under a
modified environment.

POSSIBLE FIX SHAPES (not decided here). Either the suite should neutralize the variable for itself (a
`conftest.py` fixture clearing `AW_EXECUTION_ROLE` for test subprocesses, which keeps the guard honest
in production while making tests hermetic), or the lane prompt should state the required invocation, or
the role should be passed by a channel that does not survive into arbitrary child processes. The first
looks strongest because it fixes the baseline for every future lane without asking each agent to
remember a flag.

WORKAROUND USED IN THE MEANTIME: `env -u AW_EXECUTION_ROLE python3 -m pytest`, with both counts and the
reason recorded in plan `metc8b`'s validation section rather than silently.
