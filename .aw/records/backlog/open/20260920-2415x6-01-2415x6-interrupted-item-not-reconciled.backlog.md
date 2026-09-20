- Id: 2415x6
- Status: open
- Blocks-Release: next
- Set: 2415x6
- Priority: high
- Work-Kind: bug
- Summary: interrupted items are left running: execute_item_core dedup stopped calling reconcile_item_on_interrupt

## Workflow history
- 2026-09-20 created (aw backlog): interrupted items are left running: execute_item_core dedup stopped calling reconcile_item_on_interrupt

FOUND BY a test-quality pass, not by a failing test, and that is the point: the guard that
should have caught it was a source-text pin that stayed GREEN.

WHAT IS BROKEN. `runner_shared.reconcile_item_on_interrupt` marks an interrupted item
`interrupted` and appends an `ipd-interrupted` event. Nothing in `agent_workflows/` calls it.
Verified: `grep -c reconcile_item_on_interrupt` is 1 in
`70a2059f^:agent_workflows/oc_runipd.py` and 0 in both drivers at HEAD. The only callers now
are `tests/test_runner_stop_triggers.py` and `tests/test_interrupt_menu.py`.

WHEN. Commit `70a2059f` (2026-09-18) 'refactor(runner): deduplicate execute_item into
runner_shared.execute_item_core' moved the emitter into the shared module and stopped
invoking it.

OPERATOR CONSEQUENCE. An item interrupted by SIGINT/SIGTERM stays `running` in run state
with no `ipd-interrupted` event. A resume cannot distinguish 'was interrupted' from 'is
still going', and the run viewer's `interrupted` arm renders nothing, so the operator is
told less than the runner knows. `render_stream.py:1906` already documents that arm as
depending on these two emit sites.

WHY NO TEST CAUGHT IT. `test_the_item_level_bookkeeping_path_is_still_wired` asserted the
literal `"event": "ipd-interrupted"` appears in each driver's source. It still does, in
each driver's `install_stop_triggers` DOCSTRING (`oc_runipd.py:7481`,
`agy_runipd.py:4083`). A substring search cannot tell prose from code, which is the exact
failure mode this repository has now measured five times.

CURRENT TEST STATE. The test was split: the structural half passes, and the behavioral half
is `@pytest.mark.xfail(strict=True)` in `tests/test_runner_stop_triggers.py`, so fixing
this flips it to XPASS(strict) and FAILS the suite until the marker is removed. Do not
delete the marker without restoring the call.

SUGGESTED FIX. Re-invoke `reconcile_item_on_interrupt` from the shared
`execute_item_core` KeyboardInterrupt path so both hosts get it once, then remove the
xfail marker. A maintainer should confirm that is the intended home rather than
re-adding two per-host call sites.
