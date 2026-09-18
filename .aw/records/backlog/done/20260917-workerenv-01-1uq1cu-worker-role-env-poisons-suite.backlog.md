- Id: 1uq1cu
- Status: done
- Set: workerenv
- Priority: high
- Work-Kind: bug
- Summary: runner exports AW_EXECUTION_ROLE=worker into execution turns, making 31 suite tests fail for reasons unrelated to the plan under execution

## Workflow history
- 2026-09-18 done (aw set): Fixed in conftest.py: the test session scrubs AW_EXECUTION_ROLE at import time so the suite always runs in the coordinator role. Measured at HEAD 6ff7a7ba: with the marking present the suite was 31 failed / 8080 passed; after the fix the SAME marked invocation is 8111 passed, 3 skipped, 2 xfailed, identical to an unmarked run. The guard was NOT relaxed: tests/test_worker_role_refusal.py still passes 7/7 and worker_role_active still returns True for a marked env
- 2026-09-17 created (aw backlog): runner exports AW_EXECUTION_ROLE=worker into execution turns, making 31 suite tests fail for reasons unrelated to the plan under execution

MEASURED 2026-09-18 during execution of integpath child 05 (3v7wo6), run run-20260918T015435Z-84931, at HEAD 36129255.

An execution turn launched by the runner has AW_EXECUTION_ROLE=worker in its environment. A bare
python3 -m pytest inside that turn reports 32 failures; the SAME suite with that one variable unset
(env -u AW_EXECUTION_ROLE python3 -m pytest) reports 1 failed, 7906 passed, with no code change.
So 31 failures are caused by the runner's own environment, not by the tree.

The direct cause is visible in the test that fails first: tests/test_worker_role_refusal.py:225
asserts os.environ.get('AW_EXECUTION_ROLE') != 'worker', with the docstring 'The DRIVER's own
environment must never be worker-marked, or driver_begin would refuse'. Tests that spawn a driver
subprocess inherit the marked environment, so driver_begin refuses inside the fixture; the affected
classes are the begin/finalize, worktree-isolation, fail-closed-integration and backlog-close-in-lane
families across tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py,
tests/test_runner_backlog_close_in_lane.py, tests/test_ipd_lifecycle_cli.py and
tests/test_novalnomerge_integration.py.

WHY THIS MATTERS BEYOND ONE TURN: every plan's validation section tells its executor to run the bare
suite and judge the delta against a self-measured baseline. Both measurements inside a runner turn
carry the same 31 phantom failures, so the delta happens to cancel and the check still passes; but an
executor who measures the baseline differently, or who reads the 32 as real, is misled into either
excusing a genuine regression or reporting one that does not exist. The fix is either to not export
the worker marking into a turn that is expected to run the suite, or to have the affected fixtures
scrub it from the child environment they build.

Do NOT fix this by relaxing tests/test_worker_role_refusal.py: that test exists to catch a
worker-marked driver process and is correct as written.
