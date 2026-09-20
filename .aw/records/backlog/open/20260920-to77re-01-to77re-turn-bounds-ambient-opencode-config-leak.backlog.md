- Id: to77re
- Status: open
- Blocks-Release: next
- Set: to77re
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds R4.1 policy assertion fails when the agent's own ambient env already carries OPENCODE_CONFIG_CONTENT

## Workflow history
- 2026-09-20 created (aw backlog): test_turn_bounds R4.1 policy assertion fails when the agent's own ambient env already carries OPENCODE_CONFIG_CONTENT

Measured 2026-09-20 while executing IPD i4c0c3 in an `aw oc run` lane worktree.

WHAT IS WRONG. `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts that a NON-isolated turn's child env carries no `OPENCODE_CONFIG_CONTENT` (`policy_key not in main_env`, tests/test_turn_bounds.py:310). The env the assertion inspects is built by merging `os.environ`, so when the process RUNNING pytest already exports `OPENCODE_CONFIG_CONTENT` the key is present for reasons that have nothing to do with the code under test, and the test fails.

That is exactly the situation inside a runner lane: the agent turn itself is launched with that variable set, so every bare `python3 -m pytest` an agent runs in a lane reports this failure. Measured both directions in the lane:
  * `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts='' -q` -> `43 passed`
  * the same run with the in-flight change fully REVERTED -> `1 failed, 42 passed`
so it is independent of the plan being executed and is a property of the environment plus the test.

WHY IT MATTERS RATHER THAN BEING COSMETIC. The repository contract obliges an agent to run the bare suite and paste the summary line, and to judge its work on the DELTA against a baseline. A failure that fires for every lane turn makes that baseline environment-dependent: each executing agent must independently re-derive that this one failure is ambient, and an agent that instead takes it at face value will either chase a non-bug or, worse, learn to discount suite failures generally.

WHAT TO SOLVE FOR. The test's intent is sound and should not be weakened: R4.1 says the denial policy is isolation-scoped, so a non-isolated turn must not be GIVEN one. The fix is to make the assertion measure what the code DECIDED rather than what the ambient environment happened to contain, for example by clearing the key from the base environment the fixture drives with (`mock.patch.dict(os.environ, {}, clear=...)` or popping just that key), or by asserting the env-building call did not ADD it. Whichever is chosen, keep the contrast the docstring claims: the isolated env must still carry a denying policy.

NOT IN SCOPE: changing whether the runner exports the variable to an agent turn.
