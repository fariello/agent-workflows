- Id: 3q0fcm
- Status: open
- Blocks-Release: next
- Set: turnenvleak
- Priority: medium
- Work-Kind: bug
- Summary: A runner turn exports OPENCODE_CONFIG_CONTENT, which makes test_turn_bounds fail inside the lane

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing IPD 76w6mq. Running the bare suite INSIDE an aw oc run lane fails one test: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped. The assertion requires OPENCODE_CONFIG_CONTENT to be ABSENT from a NON-isolated turn's computed environment, but the agent's own turn exports that variable and the test inherits it, so the computed env contains it. Proven environmental, not a code defect: with the variable stashed out of the environment the FULL suite is green (7329 passed, 3 skipped, 2 xfailed), and the failure reproduces with all of 76w6mq's changes stashed. Impact: every agent running the suite inside a lane sees a spurious failure it must spend a turn eliminating, and an agent that does not investigate may either report a false regression or learn to ignore a real one. Fix direction: the test should compute the env from an explicit base rather than inheriting os.environ, or the runner should not export the config into the agent turn. Repro inside a lane: python3 -m pytest tests/test_turn_bounds.py, then env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py.
