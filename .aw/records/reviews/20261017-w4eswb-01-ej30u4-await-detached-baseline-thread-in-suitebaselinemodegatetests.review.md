# Review findings: plan ej30u4

- Subject-Id: ej30u4
- Subject-Type: ipd
- Reviewed-At: 2026-10-18
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `08fa69666`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `SuiteBaselineRun.__init__` starts `self._drain = threading.Thread(target=self._pump, daemon=True)`
  (`agent_workflows/runner_shared.py:29439`); `collect` joins with `wait_seconds` and returns
  `suite_baseline_absent` when `self._drain.is_alive()` (`:29508-29510`); `execute_item_core` calls
  bare `start_suite_baseline(` (`:41337`) and `collect(wait_seconds=0.0)` (`:43260`). Plan F-01 correct.
- Current file: test reports `XPASS` on an idle machine (`2 passed, 1 xpassed`).
- Demonstration on gitignored scratch copies with the baseline child slowed to `time.sleep(1.5)`:
  fixed-sleep shape `FAILED ... AssertionError: 'absent' != 'completed'`; proposed drain-join shape
  `PASSED`. Unslowed, both shapes pass (`6 passed`).
- `ruff check` on the proposed shape reports `F401` for `time` and `pytest`.
- `tests/slow_allowlist.txt` is read only by `conftest.py` `pytest_terminal_summary`; default
  `addopts` collects all 3 tests of the file.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric A/G (mechanism underspecified) | plan E-01 step 2 "Wrap `runner_shared.start_suite_baseline` using `mock.patch.object` with a tracking side effect"; `agent_workflows/runner_shared.py:41337` `start_suite_baseline(` | A side effect that calls `runner_shared.start_suite_baseline` while the patch is live recurses into the mock; the plan did not say to capture the original first or why patching the module global intercepts the call. | all Low | FIXED | E-01 spells out `original_start` captured before patching, the `tracking_start` wrapper, `side_effect=`, and cites the bare-name call site. Demonstrated on a scratch copy. |
| PR-002 | MEDIUM | UNDER-SCOPE | Rubric G (commit will be rejected) | `tests/test_suite_baseline_mode_gate.py:24` `import time`, `:29` `import pytest`; `.pre-commit-config.yaml` `id: ruff` `args: [--fix]` | Removing the sleep and the xfail leaves both imports unused (ruff `F401`, measured), so the mutating ruff hook would rewrite the file and reject the commit. | all Low | FIXED | Added E-01 step 3 to remove both imports; V-01 demands a pasted clean `ruff check`. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric E (validation does not prove the fix) | plan E-02 / V-02 "showing `1 passed` (no xpass)" | The test already XPASSes on an idle machine at HEAD, so a pass after the change proves nothing about the race; the validation could not distinguish fixed from unfixed. | all Low | FIXED | E-02 step 2 adds a scratch-only slowed-child contrast probe (new shape passes, old shape fails `'absent' != 'completed'`), demonstrated at review; V-02 demands both results. |
| PR-004 | LOW | IN-SCOPE | Rubric E / Step 0 accuracy | plan Step 0 "pytest requires `-m \"slow or not slow\"`"; `pyproject.toml` `addopts`; `conftest.py` `pytest_terminal_summary` | `slow_allowlist.txt` only feeds the duration report and applies no marker; the override is unnecessary, and "full test suite with `-m \"slow or not slow\"`" was an unbounded thorough-tier run. | all Low | FIXED | Corrected Step 0; E-02/V-02 use the file under `-n 6` plus the bare routine gate. |
| PR-005 | LOW | IN-SCOPE | Live-artifact criteria convention | plan E-02 / V-02 "`3 passed`" | A collected test count was used as the bar. | all Low | FIXED | Bar rewritten to every test `PASSED` with no xfail/xpass/failed, re-derived at execution. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to prove the wait removes the race without a contended machine? | Scratch-only slowed-child contrast probe, not committed | Commit a second slowed test (adds ~1.5s and a new test surface out of the plan's scope); rely on pass alone (cannot distinguish, PR-003) | Review demonstration on scratch copies at HEAD `08fa69666` | yes |
| D-2 | Validate under `-m "slow or not slow"` full suite? | No; file under `-n 6` plus bare routine gate | Thorough tier `make test-all` | `pyproject.toml` `addopts`; AGENTS.md repo-local suite contract | yes |
