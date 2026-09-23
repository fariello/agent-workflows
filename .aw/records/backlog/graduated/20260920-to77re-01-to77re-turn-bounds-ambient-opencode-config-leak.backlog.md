- Id: to77re
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: to77re
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds R4.1 policy assertion fails when the agent's own ambient env already carries OPENCODE_CONFIG_CONTENT

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
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
