# IPD: Assess bugs - Python scripts correctness issues

- Date: 2026-07-12
- Concern: bugs
- Scope: python scripts (install-workflows.py, versioning.py, hatch_build.py, agent_workflows/*.py, tools under .agents/workflows/*)
- Status: to-review
- Author: Antigravity (Gemini 1.5 Pro)

## Workflow history

- 2026-07-12 /assess bugs (Antigravity/Gemini): assessed python scripts; proposed 4 changes.

## Goal

Correct logic errors, potential runtime crashes, and dead code in the framework's core Python codebase and workflow scripts, enhancing robustness and code quality.

## Project conventions discovered (Step 0)

- Guiding principles: [GUIDING_PRINCIPLES.md](file://<repo-root>/GUIDING_PRINCIPLES.md) (specifically Principle 1: Fix by default; Principle 6: KISS; Principle 10: Safety and reversibility)
- Pending-plans location/format used: `.agents/plans/pending/` using `YYYYMMDD-HHMM-NN-<slug>.md` local time naming convention.
- Contributor/spec-sync contract: [AGENTS.md](file://<repo-root>/AGENTS.md)
- Stack / relevant context: Python 3.8+ zero-dependency environment.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| BUG-01 | Low | Low | Software engineer | verify/tools | Dead code pattern (`and False`) in `run_checks.py` | [run_checks.py:590](file://<repo-root>/.agents/workflows/verify/tools/run_checks.py#L590) |
| BUG-02 | Medium | Low | Software engineer | setup-repo/tools | Uncaught ValueError/OverflowError in `datetime.datetime.fromtimestamp` call | [normalize_plan_names.py:226](file://<repo-root>/.agents/workflows/setup-repo/tools/normalize_plan_names.py#L226) |
| BUG-03 | Medium | Low | Software engineer | core package | Uncaught AttributeError in PyPI latest version lookup if response JSON is not a dictionary | [versioning.py:319](file://<repo-root>/agent_workflows/versioning.py#L319) |
| BUG-04 | Low | Low | QA engineer | assess/tools | Unused variable `line_no` and default `:1` line reporting in `scan_secrets.py` history scans | [scan_secrets.py:311](file://<repo-root>/.agents/workflows/assess/tools/scan_secrets.py#L311) |

## Proposed changes (ordered, validatable)

Fix by default: all 4 findings carry Low Remediation Risk and should be fixed.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | BUG-01 | Remove the dead code path `and False` and unused `"declined"` outcome in `run_checks.py`. | [run_checks.py](file://<repo-root>/.agents/workflows/verify/tools/run_checks.py) | Low | Run unit tests; verify code behaves identically without dead branch. |
| 2 | BUG-02 | Add a try-except block around `fromtimestamp` in `normalize_plan_names.py` to gracefully handle ValueError, OSError, and OverflowError. | [normalize_plan_names.py](file://<repo-root>/.agents/workflows/setup-repo/tools/normalize_plan_names.py) | Low | Run unit tests; verify it compiles and runs. |
| 3 | BUG-03 | In `versioning.py`, verify `isinstance(data, dict)` before checking PyPI metadata keys to prevent `AttributeError`. | [versioning.py](file://<repo-root>/agent_workflows/versioning.py) | Low | Run unit tests; verify no crash if mock PyPI returns non-dict structures. |
| 4 | BUG-04 | Clean up the unused `line_no` variable in `scan_secrets.py` to prevent linter warnings. | [scan_secrets.py](file://<repo-root>/.agents/workflows/assess/tools/scan_secrets.py) | Low | Run unit tests. |

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: None.
- Under-scope: None.

## Required tests / validation

- Execute `python3 -m unittest discover tests` and verify all tests pass.
- Verify through python compilation/linters that no syntax errors or unused variables are introduced.

## Spec / documentation sync

N/A. These are internal code bug fixes that do not change user-visible behavior.

## Open questions

None.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it; that sets `Status: reviewed`). Update `Status:` as it progresses (`to-review` -> `reviewed` -> `approved`), appending a Workflow-history line at each step.
2. On human approval, set `Status: approved` (+ the `Approval:` line), execute the ordered changes, run the validation, and sync specs/docs.
3. Only then set the terminal `Status:` and move this IPD from the pending dir to the right terminal dir per the project's lifecycle convention (canonical: `.agents/plans/pending/` -> `.agents/plans/executed/` when implemented+verified). Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md` (local date+time; `NN` per-minute two-digit sequence, `00` reserved for an orchestrator; lowercase-kebab slug).
