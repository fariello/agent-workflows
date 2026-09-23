- Id: tem4g9
- Status: open
- Blocks-Release: next
- Set: tem4g9
- Priority: medium
- Work-Kind: bug
- Summary: tests/test_turn_bounds.py isolation-scoped policy test fails when the developer's own env carries OPENCODE_CONFIG_CONTENT

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing w33lrl (baseline measurement). tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped asserts OPENCODE_CONFIG_CONTENT is absent from a non-isolated turn's env, but the assertion reads the AMBIENT process environment, so it fails for any developer or agent turn whose own environment already exports that variable (measured: present in this lane's env, and the failure reproduces identically before and after every source change in this plan). It is environmental rather than a product defect, but it makes a bare 'python3 -m pytest' red for a whole class of runs, which is exactly the signal a contract test must not blur. Fix: build the expected env from an explicit base rather than inheriting os.environ, or filter the key the test owns.
