- Id: rfu7mk
- Status: open
- Blocks-Release: next
- Set: rfu7mk
- Priority: medium
- Work-Kind: bug
- Summary: turn-bounds isolation test reads ambient OPENCODE_CONFIG_CONTENT, so it fails inside an agent turn that exports it

## Workflow history
- 2026-09-20 created (aw backlog): Pre-existing red inside an agent turn; found while establishing a baseline for plan h5pyqa.

## What is wrong

```
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
AssertionError: a non-isolated turn must get NO denial policy ...
assert 'OPENCODE_CONFIG_CONTENT' not in {...}
```

The test asserts a NON-isolated turn's environment carries no `OPENCODE_CONFIG_CONTENT` denial policy. The
env builder does not add one; the variable is INHERITED from the ambient environment, because an OpenCode
agent turn exports it. PROVEN 2026-09-20: `env -u OPENCODE_CONFIG_CONTENT python3 -m pytest
tests/test_turn_bounds.py -k isolation_scoped` gives `1 passed`, while the same command with the variable
present gives `1 failed`.

So the test is environment-dependent: green in a plain shell and CI, red whenever it runs INSIDE an agent
turn, which is precisely where the driver runs its gating suite.

## Why this one matters more than it looks

It is not merely flaky, it is ADVERSE TO THE GATE. `run_suite_check` runs the suite from inside a driver turn,
so this test is red exactly when the integration gate consults it, refusing lanes for a reason that has
nothing to do with any lane's work. That is the `run-20260919T194413Z-2056285` failure mode (one unrelated red
test refused three correct lanes) with a permanent cause rather than an accidental one.

Likely fix: the test should clear the variable from the base environment it diffs against (the isolated half
already asserts the policy is ADDED, which is the real property), so it measures what the builder does rather
than what it inherited.
