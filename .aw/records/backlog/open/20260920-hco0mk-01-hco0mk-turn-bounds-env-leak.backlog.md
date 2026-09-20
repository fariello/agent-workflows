- Id: hco0mk
- Status: open
- Blocks-Release: next
- Set: hco0mk
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds permission-policy test is not hermetic: it fails whenever OPENCODE_CONFIG_CONTENT is in the ambient environment

## Workflow history
- 2026-09-20 created (aw backlog): Filed by plan y4adch execution (retrytier-01) as a defect finding in adjacent code.

tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped asserts that a NON-isolated turn's environment does NOT carry the permission-denial policy key, by checking `policy_key not in main_env`. The environment it inspects INHERITS the ambient process environment, so the assertion fails whenever OPENCODE_CONFIG_CONTENT is already exported by the surrounding session.

MEASURED 2026-09-20 at HEAD 58876f1b in an oc_runipd lane worktree: a bare `python3 -m pytest` reports `1 failed, 7246 passed, 3 skipped, 2 xfailed` with this as the sole failure, both BEFORE and AFTER an unrelated change, so it is reproducible and not caused by the plan that found it.

WHY bug rather than chore: the failure is a WRONG ANSWER a human reads. Any maintainer or agent who runs the suite from inside an opencode session (which is the normal way it is run in this repo) sees a red suite that reports nothing true about the code, and must then spend time establishing that the failure is spurious. That cost is user-perceptible and recurs on every run.

THE FIX IS IN THE TEST, NOT THE PRODUCTION CODE: the test should compute the DELTA the launcher contributes rather than asserting absence from an inherited environment, or should build the base environment hermetically (e.g. via mock.patch.dict(os.environ, ..., clear=True)) so an ambient export cannot satisfy or defeat the assertion. Do NOT 'fix' it by unsetting the variable in a conftest, which would hide the same class of leak for every other test in the file.

Location: tests/test_turn_bounds.py:310 (assertion), with the failing environment printed in the assertion message.
