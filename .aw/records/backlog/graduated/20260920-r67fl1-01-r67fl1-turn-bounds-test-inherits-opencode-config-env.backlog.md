- Id: r67fl1
- Status: graduated
- Graduated-To: envhermet
- Blocks-Release: next
- Set: r67fl1
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds permission-policy test is not hermetic: it inherits OPENCODE_CONFIG_CONTENT from the ambient environment and fails inside any OpenCode turn

## Workflow history
- 2026-09-23 graduated (aw set): Graduated to the envhermet Set (orchestrator uvwqvz, child 01 heglfv for the DEFECT, child 02 fwgq2u for the missing GUARD). This item is one of TWENTY-THREE open filings of a single non-hermetic assertion: tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped reads the AMBIENT OPENCODE_CONFIG_CONTENT, which run_opencode always sets for a turn. MEASURED at HEAD 22cf67d9: bare '144 passed', and with the variable set '1 failed, 143 passed' on 'assert OPENCODE_CONFIG_CONTENT not in {...}'. So the file is green for a human and red for every lane agent, which is why so many agents filed it independently. THE FIX MUST NOT RELAX THE ASSERTION: R4.1 genuinely requires a non-isolated turn to receive NO denial policy (it works in the main checkout where external-directory denial would refuse its ordinary work), so heglfv fixes the SEAM the test reads, not the guarantee. A session-wide conftest scrub is explicitly REJECTED, because that mechanism is what made rolevac 8i0xa7's role guard vacuous and repeating it would be a known self-inflicted defect. NOT CLOSED AS A DUPLICATE HERE: consolidating these twenty-three needs human judgement (uvwqvz OQ-01), since the filings are not identical and at least two attribute the failure to AW_EXECUTION_ROLE, a different and already-scrubbed cause.
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
