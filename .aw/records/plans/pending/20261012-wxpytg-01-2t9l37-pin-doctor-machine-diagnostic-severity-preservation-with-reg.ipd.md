# IPD: Pin doctor machine diagnostic severity preservation with regression coverage

- Date: 2026-10-12
- Kind: child
- Concern: `aw doctor` machine output (`--agent` / `--json`) must report each finding's REAL severity rather than a blanket `error`.
- Scope: Verify the severity-preserving `Diagnostic` construction in `doctor.inspect_repo` and add behavior regression tests that drive `inspect_repo` and the `aw doctor --agent` CLI, asserting the emitted diagnostic severities and the unchanged exit code.
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor_diagnostic_severity.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: wxpytg
- Blocks-Release: next
- Set: wxpytg
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 2t9l37

## Workflow history

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog wxpytg; source fix found already present, plan scoped to verification plus regression coverage.

## Goal

Close backlog `wxpytg` provably: confirm that `doctor.inspect_repo` builds each machine `Diagnostic` from the drift's own severity (falling back to the rule registry, then `error`), and pin that behavior with outcome tests so the blanket `severity="error"` regression the backlog item describes cannot silently return.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the source state

- [ ] E-01 Re-read the `for d in report.all_drift:` loop in `doctor.inspect_repo` and confirm the `Diagnostic(...)` call passes `severity=getattr(d, "severity", "") or check_engine.rule_spec(d.rule).severity or "error"`; if a hardcoded `severity="error"` is found instead (for example after a revert), replace it with exactly that expression in `agent_workflows/doctor.py`.
  - Depends on: none
  - Expected outcome: `grep -n 'severity="error"' agent_workflows/doctor.py` returns no match inside `inspect_repo`, and the fallback chain expression is present.
  - Execution state: pending

### Task group 2: Regression tests

- [ ] E-02 Create `tests/test_doctor_diagnostic_severity.py` with a test that monkeypatches `doctor.run_doctor` (the seam `inspect_repo` already honors via the `_RUN_DOCTOR_CODE` check) to return four drifts: one with explicit `severity="info"`, one with explicit `severity="warning"`, one with empty severity on the registered info rule `doctor.dangling-doc-reference`, and one with empty severity on an unregistered rule id; call `doctor.inspect_repo(repo)` on a `tests.support.init_repo` fixture under `tmp_path` and assert the resulting diagnostics' severities are `info`, `warning`, `info`, `error` respectively, matched by rule/location.
  - Depends on: E-01
  - Expected outcome: test passes against the current source and would fail if the construction hardcoded `error`.
  - Execution state: pending
- [ ] E-03 In the same file add a test that monkeypatches `doctor.run_doctor` to return only `info`-severity drifts and asserts `inspect_repo` still reports the info severities while the exit-code contract is honored (`artifact_core.drift_exit_code` on the drifts is 0 and the result's status is `clean`), proving severity preservation does not move the exit code.
  - Depends on: E-01
  - Expected outcome: test passes; info-only findings yield a clean exit with `info` diagnostics.
  - Execution state: pending
- [ ] E-04 In the same file add an end-to-end CLI test: in an `init_repo` fixture under `tmp_path` create one untracked file, run `tests.support.run_cli("doctor", "--agent", cwd=repo)`, parse the `aw.agent/v1` JSONL `result` record, and assert every diagnostic carries a severity in `{"error", "warning", "info"}` and that each diagnostic's severity equals `check_engine.rule_spec(rule).severity` for its rule (the untracked-file drift carries no explicit severity, so this asserts the registry fallback reaches the CLI surface).
  - Depends on: E-01
  - Expected outcome: test passes; CLI machine output reflects registry severities rather than a constant.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The suite runs bare as `python3 -m pytest` (AGENTS.md repo development contract); `pyproject.toml` `addopts` supplies `-q -n auto`.
- Tests must exercise behavior, never read source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the tests here call `inspect_repo` and the CLI and assert on output.
- Fixtures use `tests.support.init_repo` and `tests.support.run_cli` (see `tests/test_severity_truth_surfaces.py`, which tests the sibling attention fix from `nwcf8j`).
- `check_engine.rule_spec` returns `_DEFAULT_RULESPEC` (severity `error`) for an unregistered rule; `check_engine.RULE_REGISTRY` registers `"doctor.dangling-doc-reference"` at `info`.
- `artifact_core.drift_exit_code` fails on any severity other than `info`, so a legacy drift with empty severity still fails the gate.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The defect described by `wxpytg` (hardcoded `severity="error"` in doctor's machine `Diagnostic` construction) is no longer present in source. | `git blame` on the `severity=getattr(d, "severity", "")` lines in `doctor.inspect_repo` attributes them to commit `64ccf6758` (`work(ka0g86): Make the managed AGENTS.md block target-neutral ...`, 2026-10-08), which landed after the backlog item was filed from the `36sifo` review. |
| F-02 | No test pins the doctor-side behavior. | `tests/test_severity_truth_surfaces.py` tests only the doctor summary bucket count and the attention diagnostic severity (`test_attention_diagnostic_preserves_drift_severity_and_exit_code`); `tests/test_sanitizer_severity_vocabulary.py` covers only `doctor.leak-*` sanitizer translation. |
| F-03 | The fix was incidental to an unrelated plan, so nothing would catch a revert. | `ka0g86` concerns AGENTS.md target neutrality, not severity. |

## Proposed changes (ordered, validatable)

1. Confirm (or restore) the fallback-chain severity expression in `doctor.inspect_repo` (E-01).
2. Add `tests/test_doctor_diagnostic_severity.py` with the seam-level preservation test (E-02), the exit-code neutrality test (E-03), and the CLI end-to-end test (E-04).

## Deferred / out of scope (with reason)

- Registering explicit severities for doctor rules that are currently unregistered (for example `doctor.git-untracked`, whose text summary calls it informational): this changes exit-code behavior and is a policy decision outside the backlog item's requirement, which is only to preserve the real severity.
- Changes to `attention.py`: already fixed and tested by `nwcf8j`.

## Scope check

- Over-scope: none.
- Under-scope: none; the backlog item's only requirement (preserve real or registry severity instead of hardcoding `error`) is verified by E-01 and pinned by E-02 through E-04.

## Required tests / validation

- `python3 -m pytest tests/test_doctor_diagnostic_severity.py -o addopts=""` passes (performed by E-02, E-03, E-04).
- Full suite `python3 -m pytest` passes with no new failures.
- `aw ipd lint --phase pre-transition` conforms on this plan.

## Spec / documentation sync

N/A: no spec or user-facing doc describes doctor's per-diagnostic severity mapping beyond the rule registry, and this plan does not change behavior.

## Open questions

### OQ-01: Should the plan re-fix source if the defect is already gone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Repository evidence (F-01) shows the fix is present; E-01 is therefore a verification step that only edits source if the expression has regressed. The remaining value is regression coverage (F-02, F-03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `grep -n 'or check_engine.rule_spec(d.rule).severity' agent_workflows/doctor.py` showing the line inside `inspect_repo`, plus `git diff agent_workflows/doctor.py` (empty if no regression was found).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output for the seam-level preservation test showing it passed, with the test asserting `info`, `warning`, `info`, `error` for the four drifts.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted pytest output for the info-only exit-code test showing it passed.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted pytest output for the CLI end-to-end test showing it passed (the observation is produced by `aw doctor --agent` via `doctor.inspect_repo`), plus the pasted summary line of a bare `python3 -m pytest` full-suite run with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit through `aw commit <this plan> -- agent_workflows/doctor.py tests/test_doctor_diagnostic_severity.py <this plan>`; never push. After every `V-*` reads `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle transition.
