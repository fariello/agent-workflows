- Id: ipfgl1
- Status: open
- Blocks-Release: next
- Set: ipfgl1
- Priority: high
- Work-Kind: bug
- Summary: 31 tests fail at HEAD in the runner-harness modules (KeyError 'main_status_during_turn' and empty-dict assertions)

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-16 created (aw backlog): 31 tests fail at HEAD in the runner-harness modules (KeyError 'main_status_during_turn' and empty-dict assertions)

Measured 2026-09-16 at HEAD `daa48f42` while executing plan `4xt6u4`, on a BARE `python3 -m pytest` with this plan's two files reverted to HEAD, so the failures are PRE-EXISTING and unrelated to that plan:

    31 failed, 7377 passed, 3 skipped, 2 xfailed in 83.03s

Distribution by module: 10 `tests/test_runner_backlog_close_in_lane.py`, 9 `tests/test_oc_runipd.py`, 8 `tests/test_agy_runipd_cli.py`, 2 `tests/test_ipd_lifecycle_cli.py`, 1 `tests/test_worker_role_refusal.py`, 1 `tests/test_novalnomerge_integration.py`.

Two sampled failure shapes, both looking like harness/fixture wiring rather than product logic:

* `tests/test_oc_runipd.py::WorktreeIsolationTests::test_main_tree_clean_during_turn_and_receipt_under_main` -> `KeyError: 'main_status_during_turn'` at `tests/test_oc_runipd.py:2917`, i.e. a key the fixture never recorded.
* `tests/test_runner_backlog_close_in_lane.py::EligibilityIsDecidedInMain::test_the_eligible_single_carrier_item_DOES_close_through_the_merge` -> `AssertionError: None is not true : {}` at `tests/test_runner_backlog_close_in_lane.py:507`, i.e. an empty result mapping.

WHY THIS MATTERS BEYOND TIDINESS: a 31-failure baseline makes the execution contract's 'paste the actual runner output' evidence much weaker for every subsequent plan, because an executor can only demonstrate 'the FAILED set did not change' rather than 'the suite passes'. That is what this plan's V-02 had to do. It also risks a real regression hiding inside the accepted baseline.

None of the failing modules reference `_rollback_precommit` (checked with `grep -l`), so they are disjoint from plan `4xt6u4`'s change; its own module passes 137/137 and the FAILED-set diff across the change is empty.

NOT INVESTIGATED FURTHER, deliberately: outside plan `4xt6u4`'s declared `Scope-Paths` (`agent_workflows/ipd_lifecycle.py`, `tests/test_orchestrator_retirement.py`). Reported rather than fixed.
