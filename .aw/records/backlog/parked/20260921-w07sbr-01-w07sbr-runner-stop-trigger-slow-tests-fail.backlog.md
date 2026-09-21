- Id: w07sbr
- Status: parked
- Set: w07sbr
- Priority: medium
- Work-Kind: bug
- Summary: Two slow-marked runner_stop trigger tests fail at HEAD: a stopped item is left 'running' with no stopped record

## Workflow history
- 2026-09-21 set (aw backlog): DUPLICATE of wqk5s2, parked rather than deleted so the independent confirmation survives. Filed by plan 2iye0e's execution turn before noticing that a concurrent lane had already filed the same two failing slow-marked stop-trigger tests as wqk5s2 (open, bug, Blocks-Release: next, same two node ids). The release gate is cleared here so the duplicate does not double-count wqk5s2's gate. WHAT THIS ITEM ADDS, and the reason it is parked rather than closed: an INDEPENDENT reproduction at a different HEAD (4baea3bc) in a pristine detached worktree both before and after unrelated comment-only edits, plus the measurement that the failures are NOT environmental (re-run with OPENCODE_CONFIG_CONTENT, AW_EXECUTION_ROLE, AW_PIN_KEEP_ROOT and AGENT all unset, and with -p no:randomly), plus the observation that @pytest.mark.slow plus the configured -m 'not slow' addopts is what hides this from the contracted bare run. Fold any of that into wqk5s2 if useful; otherwise this can be closed.

Measured at HEAD 4baea3bc in an isolated lane worktree, BEFORE and AFTER the 2iye0e comment-only edits, so it is pre-existing and unrelated to that plan.

REPRODUCE:

    python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -q -p no:randomly
    2 failed, 61 passed, 1 xfailed

FAILING NODE IDS:

- tests/test_runner_stop_triggers.py::SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint
  -> KeyError: 'stopped' at tests/test_runner_stop_triggers.py:1061. The queue item carries no 'stopped' record at all after a real SIGTERM.
- tests/test_runner_stop_triggers.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted
  -> AssertionError: 'running' != 'interrupted'. The item's status is left 'running' after the terminal SIGINT rung.

WHY IT WAS NOT CAUGHT BY THE CONTRACTED SUITE: both classes carry @pytest.mark.slow (tests/test_runner_stop_triggers.py:1020 and :788), and pyproject addopts scopes the bare run with -m 'not slow'. So a bare 'python3 -m pytest' is GREEN (measured 7648 passed) while these two fail. That means the gap is invisible to the standard contract run and only surfaces in a slow-inclusive run.

WHAT IS AT STAKE, which is why this is filed as a bug rather than a chore: these two assertions are the spec c4gd2h R13/R18-R19 contract that a stopped item is RECORDED with its level and certainty. If the recording genuinely does not happen, a resume after a real SIGTERM or a terminal Ctrl-C rung reads an item still marked 'running' with no stop record, which is exactly the indeterminate-state confusion that spec's reconciliation requirements exist to prevent. It is NOT established here whether the defect is in the product (runner_stop / the drivers) or in the two tests' harness expectations; that triage is the work this item carries.

NOT ENVIRONMENTAL: re-measured with OPENCODE_CONFIG_CONTENT, AW_EXECUTION_ROLE, AW_PIN_KEEP_ROOT and AGENT all unset, and with -p no:randomly, with identical results. Distinguish from the separate, genuinely environmental failure of tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped, which fails only because an ambient OPENCODE_CONFIG_CONTENT leaks into the child env and passes once it is unset.
