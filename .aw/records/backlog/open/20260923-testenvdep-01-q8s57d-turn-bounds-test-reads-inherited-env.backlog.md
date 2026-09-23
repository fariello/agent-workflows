- Id: q8s57d
- Status: open
- Blocks-Release: next
- Set: testenvdep
- Priority: medium
- Work-Kind: bug
- Summary: A turn-bounds test asserts an ENVIRONMENT property, so it fails on any machine exporting OPENCODE_CONFIG_CONTENT

## Workflow history
- 2026-09-23 created (aw backlog): Found executing dy9ymn. tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped asserts that a NON-ISOLATED turn's child env carries NO OPENCODE_CONFIG_CONTENT (R4.1: the denial policy is isolation-scoped). But the driver passes the parent environment through, so a variable of that name INHERITED from the operator's shell is indistinguishable from one the driver set. This lane's shell exports it, so the test fails at HEAD both with and without dy9ymn's change, and every suite run in that turn had to use 'env -u OPENCODE_CONFIG_CONTENT'. THE ASSERTION'S INTENT IS CORRECT and must not be deleted: it is what proves the policy is isolation-scoped. The fix is to make it measure the DRIVER's contribution rather than the resulting env, e.g. assert the key is absent from the env DELTA the driver applies, or clear the key in the fixture before driving so the inherited value cannot satisfy or defeat it. Filed as a bug because a green suite is a release gate and this makes it environment-dependent.
