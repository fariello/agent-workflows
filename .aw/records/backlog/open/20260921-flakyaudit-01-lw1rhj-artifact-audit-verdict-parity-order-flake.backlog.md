- Id: lw1rhj
- Status: open
- Blocks-Release: next
- Set: flakyaudit
- Priority: low
- Work-Kind: bug
- Summary: test_artifact_audit VerdictParityTests::test_four_verdict_shapes failed once under random ordering and did not reproduce in four subsequent full runs

## Workflow history
- 2026-09-21 created (aw backlog): test_artifact_audit VerdictParityTests::test_four_verdict_shapes failed once under random ordering and did not reproduce in four subsequent full runs

OBSERVED ONCE 2026-09-21 during plan fqnj8k's validation, at HEAD ef640388 plus that plan's attention.py/cli.py/test_attention.py changes.

THE OBSERVATION, stated exactly. One bare `python3 -m pytest` run reported:
    FAILED tests/test_artifact_audit.py::VerdictParityTests::test_four_verdict_shapes
    FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped
    2 failed, 7889 passed
The second failure is a separate, reproducible environment artifact of running under an agent host (OPENCODE_CONFIG_CONTENT present in the parent env) and is not this item.

WHAT DID NOT REPRODUCE. The `test_four_verdict_shapes` failure did not recur in: the test alone (`-o addopts=""`, 1 passed); its whole file under the configured parallel flags (63 passed); and FOUR subsequent full bare suite runs (7890 passed each, only the turn_bounds environment failure). No failure text was captured before the next run overwrote the buffer, which is a gap in this report and the first thing a fix attempt should correct.

WHY IT IS STILL WORTH FILING. `pyproject.toml` addopts enables `-n auto --dist=worksteal` and pytest-randomly, so test ORDER and worker ASSIGNMENT vary per run. A test that fails on one ordering and passes on others is by definition order-dependent or worker-shared-state-dependent, which is precisely the bug class that randomization exists to surface. Discarding it as "a flake" throws away the signal.

WHAT THE TEST DOES, as a starting point: `test_four_verdict_shapes` builds a tmpdir repo with four plan files and asserts `artifact_audit.audit_artifact` returns clean / location-mismatch / status-mismatch / missing-entirely. It takes no repo-root argument from the ambient environment and uses `tempfile.TemporaryDirectory`, so a naive read suggests it is isolated; the failure says otherwise, so the isolation claim needs checking rather than assuming (candidates: a module-level cache in `artifact_audit` or its resolver, a shared id6 registry, or cwd leakage from a concurrently-running test).

HOW TO HUNT IT: run the suite with a FIXED seed sweep (`-p randomly --randomly-seed=<n>`) until it reproduces, then bisect with `-p no:randomly` plus an explicit test order. Capture the assertion text when it does.
