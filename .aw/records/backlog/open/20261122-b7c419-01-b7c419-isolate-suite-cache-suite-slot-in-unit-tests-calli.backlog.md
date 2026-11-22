- Id: b7c419
- Status: open
- Set: b7c419
- Work-Kind: bug
- Priority: medium
- Summary: Isolate suite_cache.suite_slot in unit tests calling run_suite_check so external host suite runs cannot trigger TestHangTimeout
- Short-Description: Isolate suite_cache.suite_slot in unit tests calling run_suite_check so external host suite runs cannot trigger TestHangTimeout
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Isolate suite_cache.suite_slot in unit tests calling run_suite_check so external host suite runs cannot trigger TestHangTimeout

## Context

`tests/test_capture_command_contract.py::test_run_suite_check_records_are_schema_valid` and `tests/test_receipt_lane_record.py::TestReceiptLaneRecord::test_case_e_one_site_both_hosts` invoke `agent_workflows/runner_shared.py::run_suite_check` with a mocked fast command (for example `python3 -c "print('1 passed in 0.01s')"`). Inside `agent_workflows/suite_cache.py::run_full_suite`, `suite_slot` still acquires the host-global two-slot lock shared across all repositories on the machine. When two external test runs on the same host hold both slots for more than 240 seconds, both unit tests block in `suite_cache.suite_slot` and fail with `conftest.TestHangTimeout` even though the mocked command itself takes less than a second.

## Acceptance

1. Isolate `suite_cache.suite_slot` in unit tests that call `runner_shared.run_suite_check` with a mocked command (for example by directing the slot directory to a test-local temporary directory or bypassing host-global slot acquisition for mocked suite commands) so external suite runs on the same host cannot block those unit tests.
2. Add a behavioral test proving that `test_run_suite_check_records_are_schema_valid` and `test_case_e_one_site_both_hosts` complete promptly even when all host-global suite slots are held.
