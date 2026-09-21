- Id: 06ngnx
- Status: open
- Blocks-Release: next
- Set: 06ngnx
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds asserts OPENCODE_CONFIG_CONTENT is absent from a child env but inherits it from the parent turn, so the suite fails inside a lane run

## Workflow history
- 2026-09-21 created (aw backlog): test_turn_bounds asserts OPENCODE_CONFIG_CONTENT is absent from a child env but inherits it from the parent turn, so the suite fails inside a lane run

MEASURED 2026-09-21 while executing IPD rkn8ya in a managed lane. This is a TEST defect (a false failure), not a product defect; the assertion is right about the intent and wrong about the measurement.

FAILING TEST:
  tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

THE ASSERTION (tests/test_turn_bounds.py:310) requires `OPENCODE_CONFIG_CONTENT` to be ABSENT from the env handed to a NON-ISOLATED turn's child process, proving the permission posture is isolation-scoped.

THE DEFECT: the child env is built by copying `os.environ`, and when the suite itself runs INSIDE an `aw oc run` lane turn, the parent process already carries `OPENCODE_CONFIG_CONTENT` (the runner sets it for the worker). The variable is therefore present in the captured env by INHERITANCE, having nothing to do with the code under test, and the assertion fails.

PROVED INDEPENDENT OF ANY SOURCE CHANGE: the test fails identically with every rkn8ya edit stashed (`git stash push agent_workflows/... tests/...` then re-run), and `env | grep -c OPENCODE_CONFIG_CONTENT` reports 1 in the lane turn. Outside a lane (a normal developer shell) the variable is absent and the test passes, which is why CI and local runs have not seen it.

WHY IT MATTERS BEYOND ONE RED TEST: the bare suite is the evidence gate every plan's V-items cite, so a test that fails purely because the suite is running inside a runner turn makes every lane-executed plan report a failure it did not cause, and trains executors to explain away red.

SUGGESTED FIX: make the assertion measure what it means, by controlling the variable rather than trusting the ambient environment. Either (a) `monkeypatch.delenv("OPENCODE_CONFIG_CONTENT", raising=False)` before driving the two turns, so the only way it can appear is for the code under test to add it, or (b) assert on the DELTA (present on the isolated turn, absent on the non-isolated one, relative to a baseline env the test constructs) instead of on absolute absence. Option (a) is the smaller change and keeps the test's stated contrast intact.
