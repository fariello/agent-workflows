- Id: zgndje
- Status: open
- Blocks-Release: next
- Set: zgndje
- Priority: medium
- Work-Kind: bug
- Summary: test_turn_bounds isolation-scoped policy test fails when the suite inherits OPENCODE_CONFIG_CONTENT from a lane turn

## Workflow history
- 2026-09-20 created (aw backlog): test_turn_bounds isolation-scoped policy test fails when the suite inherits OPENCODE_CONFIG_CONTENT from a lane turn

MEASURED 2026-09-20 in lane n5qca5 at HEAD 340c9174.

`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped` asserts that a NON-isolated turn carries NO `OPENCODE_CONFIG_CONTENT` denial policy (lane_containment.OPENCODE_RUNTIME_CONFIG_ENV), because a turn working in the main checkout would be refused its ordinary work by an external-directory denial (R4.1).

The assertion reads the env the driver would build, which INHERITS os.environ. When the suite itself runs INSIDE a managed lane turn, the runner has already exported OPENCODE_CONFIG_CONTENT for that turn, so the variable is present in os.environ, flows into the non-isolated env under test, and the assertion fails.

PROOF, environment alone, no code change:

    $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    43 passed in 4.84s
    $ python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
    1 failed, 42 passed in 4.73s

WHY THIS IS USER-PERCEPTIBLE: every agent turn run by `aw oc run` that executes the bare suite sees a red run it did not cause, so each such turn spends time diagnosing a phantom regression and each must justify the failure in its report. It also weakens the empty-delta criterion the execution contract relies on, since a real regression in this file would be masked by an expected failure.

LIKELY FIX: the test should control the variable rather than inherit it, e.g. build the env under a `mock.patch.dict(os.environ, ..., clear=...)` that removes OPENCODE_RUNTIME_CONFIG_ENV before driving, so the assertion measures what the DRIVER adds rather than what the ambient session already had. Whether the PRODUCTION path should also strip an inherited policy for a non-isolated turn is a separate and more interesting question: if it does not, a non-isolated turn launched from inside a lane session would inherit a denial policy that R4.1 says it must not have, which would be a real defect rather than a test artifact. Investigate that before fixing only the test.
