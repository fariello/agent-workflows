- Id: t49rmq
- Status: open
- Blocks-Release: next
- Set: t49rmq
- Priority: medium
- Work-Kind: bug
- Summary: The test suite is not hermetic against an inherited AW_EXECUTION_ROLE: 31 runner tests fail when it is set to worker

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-18 created (aw backlog): The test suite is not hermetic against an inherited AW_EXECUTION_ROLE: 31 runner tests fail when it is set to worker

MEASURED 2026-09-18 while executing wfartifacts Order 02 (plan vh14ku) inside an `aw oc run` managed lane, which exports `AW_EXECUTION_ROLE=worker` into the agent turn.

A BARE `python3 -m pytest` in that environment reports `31 failed, 7980 passed`. Clearing the single variable makes the same tests pass:

    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_oc_runipd.py tests/test_agy_runipd_cli.py tests/test_runner_backlog_close_in_lane.py -o addopts='' -q
    294 passed in 59.93s

    $ env -u AW_EXECUTION_ROLE python3 -m pytest
    8011 passed, 3 skipped, 2 xfailed

The failing tests live in `tests/test_oc_runipd.py` (WorktreeIsolationTests, FailClosedIntegrationGuardTests), `tests/test_agy_runipd_cli.py` (the Agy twins plus AgySelfFinalizeTests) and `tests/test_runner_backlog_close_in_lane.py`. Each drives the runner's own begin/finalize, and the refusal they hit is CORRECT product behavior: `wtiso_gate`/`ipd_lifecycle` refuse a driver-only lifecycle verb for a worker-role process with `AW-LIFECYCLE-ROLE-001`. The captured stderr of a failing test shows exactly that refusal, and the assertion then dies on a `KeyError` for an observation the refused turn never made.

SO THIS IS NOT A PRODUCT BUG AND NOT A REGRESSION: the same 31 fail at an untouched baseline worktree checked out at the same HEAD, so a failure-SET delta is empty either way. It is a TEST-HERMETICITY bug, and the harm is specific: an agent executing a plan inside a managed lane is required by the execution contract to run the suite and paste real output, and what it sees is 31 red tests it did not cause. That invites either a false regression report or, worse, a decision to 'fix' correct gate code.

SUGGESTED FIX: have the tests that exercise driver-role lifecycle verbs neutralize the inherited role explicitly (e.g. a fixture or `mock.patch.dict(os.environ)` clearing `AW_EXECUTION_ROLE`, or setting the driver role they actually mean to test), so the result does not depend on who launched the runner. Consider the same treatment for any other `AW_*` variable the runners export into a turn.
