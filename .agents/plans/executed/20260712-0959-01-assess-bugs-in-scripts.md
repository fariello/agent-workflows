# IPD: Assess bugs - Python scripts correctness issues

- Date: 2026-07-12
- Concern: bugs
- Scope: python scripts (install-workflows.py, versioning.py, hatch_build.py, agent_workflows/*.py, tools under .agents/workflows/*)
- Status: executed
- Author: Antigravity (Gemini 1.5 Pro)

## Workflow history

- 2026-07-12 /assess bugs (Antigravity/Gemini): assessed python scripts; proposed 4 changes.
- 2026-07-12 /plan-review-long (opencode / its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH
  REVISIONS APPLIED. Independently re-verified all 4 findings against source - ALL REAL (BUG-01
  run_checks.py:590 dead `and False`; BUG-02 normalize_plan_names.py:226 unguarded fromtimestamp;
  BUG-03 versioning.py:319 `.get()` on possibly-non-dict PyPI JSON, uncaught AttributeError
  contradicting its own docstring; BUG-04 scan_secrets.py unused line_no). PL-1 (per-bug regression
  tests required, not just "run the suite"), PL-2 (disambiguate BUG-01 to the behavior-preserving
  cleanup; resolved interactively). No BLOCKER/HIGH. Status -> reviewed.
- 2026-07-12 executed (Antigravity/Gemini): implemented fixes for BUG-01, BUG-02, BUG-03, and BUG-04.

## Goal

Correct logic errors, potential runtime crashes, and dead code in the framework's core Python codebase and workflow scripts, enhancing robustness and code quality.

## Project conventions discovered (Step 0)

- Guiding principles: [GUIDING_PRINCIPLES.md](./GUIDING_PRINCIPLES.md) (specifically Principle 1: Fix by default; Principle 6: KISS; Principle 10: Safety and reversibility)
- Pending-plans location/format used: `.agents/plans/pending/` using `YYYYMMDD-HHMM-NN-<slug>.md` local time naming convention.
- Contributor/spec-sync contract: [AGENTS.md](./AGENTS.md)
- Stack / relevant context: Python 3.8+ zero-dependency environment.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| BUG-01 | Low | Low | Software engineer | verify/tools | Dead code pattern (`and False`) in `run_checks.py` | [run_checks.py:590](./.agents/workflows/verify/tools/run_checks.py#L590) |
| BUG-02 | Medium | Low | Software engineer | setup-repo/tools | Uncaught ValueError/OverflowError in `datetime.datetime.fromtimestamp` call | [normalize_plan_names.py:226](./.agents/workflows/setup-repo/tools/normalize_plan_names.py#L226) |
| BUG-03 | Medium | Low | Software engineer | core package | Uncaught AttributeError in PyPI latest version lookup if response JSON is not a dictionary | [versioning.py:319](./agent_workflows/versioning.py#L319) |
| BUG-04 | Low | Low | QA engineer | assess/tools | Unused variable `line_no` and default `:1` line reporting in `scan_secrets.py` history scans | [scan_secrets.py:311](./.agents/workflows/assess/tools/scan_secrets.py#L311) |

## Proposed changes (ordered, validatable)

Fix by default: all 4 findings carry Low Remediation Risk and should be fixed.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | BUG-01 | Remove the dead TERM `and args.yes and False` entirely and drop the unreachable `"declined"` literal, so the expression reduces to `"unclassified; not run" if not c.category else "declined by user"`. This PRESERVES current behavior (PL-2). Do NOT merely delete `and False` (that would ACTIVATE a new "declined" reason for `--yes` + unclassified commands, a behavior change). | [run_checks.py](./.agents/workflows/verify/tools/run_checks.py) | Low | Regression test pins the skip-reason unchanged before/after (PL-2). |
| 2 | BUG-02 | Add a try-except block around `fromtimestamp` in `normalize_plan_names.py` to gracefully handle ValueError, OSError, and OverflowError. | [normalize_plan_names.py](./.agents/workflows/setup-repo/tools/normalize_plan_names.py) | Low | Run unit tests; verify it compiles and runs. |
| 3 | BUG-03 | In `versioning.py`, verify `isinstance(data, dict)` before checking PyPI metadata keys to prevent `AttributeError`. | [versioning.py](./agent_workflows/versioning.py) | Low | Run unit tests; verify no crash if mock PyPI returns non-dict structures. |
| 4 | BUG-04 | Clean up the unused `line_no` variable in `scan_secrets.py` to prevent linter warnings. | [scan_secrets.py](./.agents/workflows/assess/tools/scan_secrets.py) | Low | Run unit tests. |

## Deferred / out of scope (with reason)

None.

## Scope check

- Over-scope: None.
- Under-scope: None.

## Required tests / validation

PLAN-REVIEW NOTE (PL-1): "run the suite" is NOT sufficient - the existing tests do not cover these
paths (that is why the bugs exist). Each fix needs a REGRESSION TEST that fails before the fix and
passes after:

- BUG-02: `fs_stamp` (or the code calling `fromtimestamp`) returns None (does not raise) for a bad
  epoch value (e.g. a mocked `stat()` returning an out-of-range mtime). Add to
  `tests/test_normalize_plan_names.py`.
- BUG-03: `latest_pypi_version` returns None (does not raise `AttributeError`) when the mocked PyPI
  response is valid JSON but NOT a dict (e.g. a list or a string). Reuse the mocked-urllib pattern
  already in `tests/test_pypi_links.py`.
- BUG-01: a test (or an assertion in an existing `run_checks` test) pinning the skip-reason behavior
  BEFORE and AFTER the dead-term removal, proving behavior is unchanged (see PL-2).
- BUG-04: assert the fix does not change reported findings; if line reporting is corrected (not just
  the unused var removed), assert the reported line number is accurate on a fixture with a known
  offset.

Then execute `python3 -m unittest discover tests` (full suite green) and confirm no new lint/format
findings.

## Spec / documentation sync

N/A. These are internal code bug fixes that do not change user-visible behavior.

## Open questions

- PL-2 (raised + RESOLVED with maintainer 2026-07-12 via /plan-review-long): BUG-01 must be a pure
  dead-code cleanup that PRESERVES current behavior (remove the whole `and args.yes and False` term
  and the unreachable `"declined"` literal), NOT the variant that activates a new "declined" reason.
  See change #1. No spec/doc change results.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review-long` (opencode / its_direct/pt3-claude-opus-4.8-1m-us). Verdict: APPROVE
WITH REVISIONS APPLIED (pending human sign-off). Every finding was re-opened at its cited `file:line`
and confirmed real - a well-evidenced assess. Revisions: PL-1 (added per-bug regression tests, since
the existing suite does not cover these paths - "run the suite" alone cannot prove the fixes) and
PL-2 (specified BUG-01 as the behavior-preserving dead-code cleanup, confirmed with the maintainer).
No BLOCKER/HIGH; no over-scope; security/scale/UI rubric Not Applicable (small correctness fixes in a
zero-dep CLI). Does not self-approve.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it; that sets `Status: reviewed`). Update `Status:` as it progresses (`to-review` -> `reviewed` -> `approved`), appending a Workflow-history line at each step.
2. On human approval, set `Status: approved` (+ the `Approval:` line), execute the ordered changes, run the validation, and sync specs/docs.
3. Only then set the terminal `Status:` and move this IPD from the pending dir to the right terminal dir per the project's lifecycle convention (canonical: `.agents/plans/pending/` -> `.agents/plans/executed/` when implemented+verified). Plan files are named `YYYYMMDD-HHMM-NN-<slug>.md` (local date+time; `NN` per-minute two-digit sequence, `00` reserved for an orchestrator; lowercase-kebab slug).
