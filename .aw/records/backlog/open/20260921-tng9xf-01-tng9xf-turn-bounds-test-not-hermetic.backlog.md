- Id: tng9xf
- Status: open
- Blocks-Release: next
- Set: tng9xf
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped policy test is not hermetic against its own runner's env

## Workflow history
- 2026-09-21 created (aw backlog): Found while executing plan qhy3i3 (rdyrecheck-01). tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped asserts OPENCODE_CONFIG_CONTENT is ABSENT from a non-isolated turn's env, but it reads the AMBIENT environment. When the suite is run from inside an aw oc run driver turn, the driver exports that variable, so the test fails for an environmental reason with no code defect. Proof: env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts='' -> 43 passed, while the same command with the variable present -> 1 failed. Impact is user-perceptible: every lane of every driver run reports a red suite, and integration_is_earned gates self-finalize on a passing suite, so an environmental failure can strand verified lanes. Fix: build the expected env from an explicit base rather than os.environ, or drop the variable in the non-isolated arm before asserting.
