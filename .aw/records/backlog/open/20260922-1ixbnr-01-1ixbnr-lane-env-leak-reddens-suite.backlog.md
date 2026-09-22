- Id: 1ixbnr
- Status: open
- Blocks-Release: next
- Set: 1ixbnr
- Priority: medium
- Work-Kind: bug
- Summary: The lane denial policy env var leaks into the lane agent's own test run, so test_turn_bounds fails in every isolated lane and every lane executor sees a red suite that is green on main

## Workflow history
- 2026-09-22 created (aw backlog): Found while executing plan lc4unl (planprio Order 03).

## Detail

WHAT IS WRONG. A lane turn is launched with `OPENCODE_CONFIG_CONTENT`
(`lane_containment.OPENCODE_RUNTIME_CONFIG_ENV`, `agent_workflows/lane_containment.py:739`) set in the
agent's process environment, to arm the isolated turn's deny-external-directory posture. That variable
is INHERITED by everything the agent then runs, including its own `python3 -m pytest`, and
`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
asserts the variable is ABSENT from a non-isolated turn's computed env (`tests/test_turn_bounds.py:310`).
The test builds its expectation from the ambient environment, so a variable the runner legitimately set
for the LANE is read as a variable the code wrongly set for a NON-ISOLATED turn.

REPRODUCED, both directions, in this lane at HEAD `c49c9027`:

    $ python3 -m pytest
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    1 failed, 8129 passed, 3 skipped, 2 xfailed, 3 warnings in 137.29s

    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py
    76 passed in 11.16s

Unsetting the single variable is the whole difference, which is what makes this environmental rather
than a product defect in the bound itself.

WHY IT MATTERS RATHER THAN BEING A CURIOSITY. Every lane executor is required to run the bare suite
and paste its summary, and every one of them sees a failure that does not exist on main. Each then
spends a turn proving it environmental, and the real hazard is the other branch: an executor who
assumes it is environmental WITHOUT checking will wave through a genuine regression in that file, and
an executor who concludes the tree is broken may abandon good work. A permanently red baseline also
destroys the failure-SET comparison that the execution contract relies on to tell a caused failure
from an inherited one.

THE FIX BELONGS IN THE TEST, not in the runner, since the runner is setting the variable for exactly
the reason it exists. The test must isolate the environment it computes against (build the non-isolated
env from a controlled base, or `monkeypatch.delenv(OPENCODE_RUNTIME_CONFIG_ENV, raising=False)` before
driving), so its assertion is about what the CODE sets rather than about what the ambient shell
happens to carry. A test whose verdict depends on who launched it cannot distinguish the behavior it
is pinning from its own environment, and this file is precisely the one that must be trustworthy
inside a lane.
