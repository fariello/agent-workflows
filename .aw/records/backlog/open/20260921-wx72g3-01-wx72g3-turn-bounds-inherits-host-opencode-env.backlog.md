- Id: wx72g3
- Status: open
- Blocks-Release: next
- Set: wx72g3
- Priority: high
- Work-Kind: bug
- Summary: test_turn_bounds permission-policy test fails whenever the suite runs inside OpenCode, because it asserts an env var is absent from an INHERITED environment

## Workflow history
- 2026-09-21 created (aw backlog): test_turn_bounds permission-policy test fails whenever the suite runs inside OpenCode, because it asserts an env var is absent from an INHERITED environment

MEASURED 2026-09-21 in lane 9lyg5h at HEAD 24aa8d41: a bare `python3 -m pytest` reports `1 failed, 7830 passed, 3 skipped, 2 xfailed`, the single failure being `tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`. It is present in BOTH the primary checkout and a fresh linked worktree, so it is not a worktree-resolution artifact.

THE CAUSE is that the test asserts a NEGATIVE over an environment it INHERITS. At tests/test_turn_bounds.py:310 it asserts `policy_key not in main_env` where `policy_key` is `lane_containment.OPENCODE_RUNTIME_CONFIG_ENV` (`OPENCODE_CONFIG_CONTENT`), on the premise that a NON-isolated turn must carry no denial policy. But the driver builds a non-isolated turn's env from the PARENT process env, and any suite run launched from inside an OpenCode session already has `OPENCODE_CONFIG_CONTENT` exported. So the assertion observes the HOST's variable rather than one the code under test added.

WHY IT MATTERS RATHER THAN BEING COSMETIC. Every agent executing a plan in this repository runs the suite from inside an agent host, so this test is red for every one of them, and the whole-repository suite IS the integration trust signal: a permanently red test is exactly the condition `daexj1`/`h5pyqa` measured costing a run 2h 10m and $55.02 for no integrated work. It also degrades this lane's own deliverable, since a pre-work baseline honestly reports a failure that is an artifact of where the suite ran.

THE FIX SHAPE (not applied here; outside this lane's Scope-Paths): the test should control the variable rather than assume its absence, for example by clearing `OPENCODE_CONFIG_CONTENT` from the environment it drives (monkeypatch.delenv with raising=False) so the assertion measures what the CODE added rather than what the host exported. The sibling ground is `utwr6y` (testiso-01), which exists to make tests own their inputs.
