- Id: owi0no
- Status: graduated
- Graduated-To: testhyg
- Blocks-Release: next
- Set: owi0no
- Priority: high
- Work-Kind: bug
- Summary: Declare execution role in remaining 10 test classes of test_ipd_lifecycle_cli.py

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set testhyg (commit 2c7068ca).
- 2026-09-24 created (aw backlog): Declare execution role in remaining 10 test classes of test_ipd_lifecycle_cli.py

When AW_EXECUTION_ROLE=worker is reasserted during test runs, 42 tests in tests/test_ipd_lifecycle_cli.py fail with AW-LIFECYCLE-ROLE-001 because only BeginCliTests declares its execution role. The remaining 10 test classes inherit the ambient role rather than declaring it.
