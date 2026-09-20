- Id: r67fl1
- Status: open
- Blocks-Release: next
- Set: r67fl1
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds permission-policy test is not hermetic: it inherits OPENCODE_CONFIG_CONTENT from the ambient environment and fails inside any OpenCode turn

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing plan bn026f (Set lifeglyph).

## What is wrong

`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
asserts that a NON-isolated turn receives no denial policy, written as:

```python
assert policy_key not in main_env
```

where `policy_key` is `lane_containment.OPENCODE_RUNTIME_CONFIG_ENV`, i.e. the literal env var
name `OPENCODE_CONFIG_CONTENT` (`agent_workflows/lane_containment.py:739`). The env the test
inspects is the one `run_opencode` hands to `Popen`, which INHERITS the parent process
environment. So when the suite itself runs inside an OpenCode session, that variable is already
present in the ambient environment and the assertion fails on a correct implementation.

## Where

`tests/test_turn_bounds.py:310` (the assertion), against
`lane_containment.OPENCODE_RUNTIME_CONFIG_ENV` (`agent_workflows/lane_containment.py:739`).

## Measured, 2026-09-20, at HEAD e72eba8d

```text
$ python3 -m pytest
1 failed, 7544 passed, 3 skipped, 2 xfailed
FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
E  AssertionError: a non-isolated turn must get NO denial policy; ...
E  assert 'OPENCODE_CONFIG_CONTENT' not in {'AGENT': '1', 'AW_HOME': ..., ...}

$ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py
43 passed

$ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest
7545 passed, 3 skipped, 2 xfailed
```

## Why this is a defect and not merely an inconvenience

It is NOT caused by the change under test: it reproduces with the working tree reverted. The
user-perceptible cost is a FALSE FAILURE that every agent running the bare suite from inside an
OpenCode turn hits, on a repository whose execution contract requires pasting the actual suite
summary line. Each occurrence costs a diagnosis round trip and invites the worse outcome, an agent
concluding its own change broke an unrelated containment test.

## Candidate fix, not prescriptive

Make the test hermetic rather than weakening the assertion: delete the key from the inherited
environment in the test's own setup (or have the drive helper compare against a controlled baseline
env), so the assertion measures what `run_opencode` ADDED rather than what the process inherited.
Weakening the assertion would lose the R4.1 property it exists to pin.
