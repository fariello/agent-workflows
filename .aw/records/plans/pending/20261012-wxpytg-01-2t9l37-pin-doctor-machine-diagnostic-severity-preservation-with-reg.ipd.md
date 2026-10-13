# IPD: Pin doctor machine diagnostic severity preservation with regression coverage

- Date: 2026-10-12
- Kind: child
- Concern: `aw doctor` machine output (`--agent` / `--json`) must report each finding's REAL severity rather than a blanket `error`.
- Scope: Verify the severity-preserving `Diagnostic` construction in `doctor.inspect_repo` and add behavior regression tests that drive `inspect_repo` and the `aw doctor --agent` CLI, asserting the emitted diagnostic severities and the unchanged exit code.
- Scope-Paths: agent_workflows/doctor.py, tests/test_doctor_diagnostic_severity.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: wxpytg
- Blocks-Release: next
- Set: wxpytg
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: 2t9l37
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004. Re-measured at HEAD 6aa8c3441: fallback chain present, seam probe info/warning/info/error, compact --agent omits severity.

- 2026-10-12 draft (opencode): created.
- 2026-10-12 to-review (opencode): authored from backlog wxpytg; source fix found already present, plan scoped to verification plus regression coverage.

## Goal

Close backlog `wxpytg` provably: confirm that `doctor.inspect_repo` builds each machine `Diagnostic` from the drift's own severity (falling back to the rule registry, then `error`), and pin that behavior with outcome tests so the blanket `severity="error"` regression the backlog item describes cannot silently return.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm the source state

- [x] E-01 Re-read the `for d in report.all_drift:` loop in `doctor.inspect_repo` and confirm the `Diagnostic(...)` call passes `severity=getattr(d, "severity", "") or check_engine.rule_spec(d.rule).severity or "error"`; if a hardcoded `severity="error"` is found instead (for example after a revert), replace it with exactly that expression in `agent_workflows/doctor.py`.
  - Depends on: none
  - Expected outcome: `grep -n 'severity="error"' agent_workflows/doctor.py` returns no match inside `inspect_repo`, and the fallback chain expression is present.
  - Execution state: performed

### Task group 2: Regression tests

- [x] E-02 Create `tests/test_doctor_diagnostic_severity.py` with a test that monkeypatches `doctor.run_doctor` (the seam `inspect_repo` already honors via the `_RUN_DOCTOR_CODE` check) to return four drifts: one with explicit `severity="info"`, one with explicit `severity="warning"`, one with empty severity on the registered info rule `doctor.dangling-doc-reference`, and one with empty severity on an unregistered rule id; call `doctor.inspect_repo(repo)` on a `tests.support.init_repo` fixture under `tmp_path` and assert the resulting diagnostics' severities are `info`, `warning`, `info`, `error` respectively, matched by rule/location.
  - Depends on: E-01
  - Expected outcome: test passes against the current source and would fail if the construction hardcoded `error`.
  - Execution state: performed
- [x] E-03 In the same file add a test that monkeypatches `doctor.run_doctor` to return only `info`-severity drifts and asserts `inspect_repo` still reports the info severities while the exit-code contract is honored (`artifact_core.drift_exit_code` on the drifts is 0 and the result's status is `clean`), proving severity preservation does not move the exit code.
  - Depends on: E-01
  - Expected outcome: test passes; info-only findings yield a clean exit with `info` diagnostics.
  - Execution state: performed
- [x] E-04 In the same file add an end-to-end CLI test. In an `init_repo` fixture under `tmp_path`, write an `AGENTS.md` whose `<!-- aw:block -->` ... `<!-- /aw:block -->` region backticks a missing path (e.g. `` `docs/missing-thing.md` ``), so `doctor.probe_installed_doc_references` yields a `doctor.dangling-doc-reference` drift with severity `info`. Also create one untracked file. Run `tests.support.run_cli("doctor", "--agent", "--verbose", cwd=repo)`, take the `aw.agent/v1` `result` record, and run `tests.support.run_cli("doctor", "--json", cwd=repo)` too. On BOTH surfaces assert: every diagnostic carries a severity in `{"error", "warning", "info"}`; the `doctor.dangling-doc-reference` diagnostic is `info`, which is the DISCRIMINATING assertion because a hardcoded `error` turns it red; and the `doctor.git-untracked` diagnostic equals `check_engine.rule_spec("doctor.git-untracked").severity`. `--verbose` is REQUIRED for the agent surface: compact `--agent` emits diagnostics as `{location, rule}` only (`result_types.CommandResult.to_agent_record`, the `else` arm of `if is_verbose:` under `# Diagnostics (omitted in compact if clean)`), so a bare `--agent` record has no severity to assert. Note that the registry fallback is not discriminating at the CLI: `doctor.git-untracked` is unregistered and resolves to the default `error`, which a hardcoded `error` would also produce. The seam test (E-02) is what pins the fallback chain.
  - Depends on: E-01
  - Expected outcome: test passes; both machine surfaces report `doctor.dangling-doc-reference` as `info` beside `error` diagnostics (measured at review on HEAD `6aa8c3441`: `[('doctor.version-not-installed', 'error'), ('doctor.dangling-doc-reference', 'info'), ('doctor.git-untracked', 'error')]` on `--agent --verbose` and on `--json`, exit 1).
  - Execution state: performed

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
| F-03 | The fix was incidental to an unrelated plan, so nothing would catch a revert. | `ka0g86` concerns AGENTS.md target neutrality, not severity; `git show 64ccf6758 -- agent_workflows/doctor.py` shows `-                severity="error",` replaced by the fallback chain. The backlog file was added at `ad7599ee1` (2026-10-08 04:33) and the fix landed at `64ccf6758` (06:24 the same day). |
| F-04 | Compact `--agent` output carries NO severity on diagnostics; only `--agent --verbose` and `--json` do. Of the drifts a fresh `init_repo` produces, the ones carrying `info` are `doctor.dangling-doc-reference` and `doctor.artifact-status-location-drift`, both set explicitly in their `core.Drift(...)` calls; `doctor.git-untracked` and `doctor.version-not-installed` are unregistered and resolve to `error`. | Review run at HEAD `6aa8c3441`: bare `--agent` diagnostics `[{"location":"<version>","rule":"doctor.version-not-installed"},{"location":"u.txt","rule":"doctor.git-untracked"}]`; `result_types.CommandResult.to_agent_record` compact branch; `check_engine.rule_spec('doctor.git-untracked').severity == 'error'`. |
| F-05 | The seam works as E-02/E-03 assume. Monkeypatching `doctor.run_doctor` to the four drifts yields `[('x.one','info'), ('x.two','warning'), ('doctor.dangling-doc-reference','info'), ('zz.unregistered','error')]`, status `findings`, exit 1; an info-only list yields status `clean`, exit 0, and `artifact_core.drift_exit_code == 0`. | Review probe calling `doctor.inspect_repo` on an `init_repo` fixture. |

## Proposed changes (ordered, validatable)

1. Confirm (or restore) the fallback-chain severity expression in `doctor.inspect_repo` (E-01).
2. Add `tests/test_doctor_diagnostic_severity.py` with the seam-level preservation test (E-02), the exit-code neutrality test (E-03), and the CLI end-to-end test (E-04).

## Deferred / out of scope (with reason)

- Registering explicit severities for doctor rules that are currently unregistered (for example `doctor.git-untracked`, whose text summary calls it informational): this changes exit-code behavior and is a policy decision outside the backlog item's requirement, which is only to preserve the real severity.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above
- Changes to `attention.py`: already fixed and tested by `nwcf8j`.
  - Carrier-Declined: deliberate non-goal or out of scope for this plan as described above

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
- Owner: plan author
- Resolution or deferral rationale: Repository evidence (F-01) shows the fix is present; E-01 is therefore a verification step that only edits source if the expression has regressed. The remaining value is regression coverage (F-02, F-03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `grep -n 'or check_engine.rule_spec(d.rule).severity' agent_workflows/doctor.py` showing the line inside `inspect_repo`, plus `git diff agent_workflows/doctor.py` (empty if no regression was found).
  - Observed evidence:
    ```
    $ grep -n 'or check_engine.rule_spec(d.rule).severity' agent_workflows/doctor.py
    2230:                or check_engine.rule_spec(d.rule).severity
    $ git diff agent_workflows/doctor.py
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted pytest output for the seam-level preservation test showing it passed, with the test asserting `info`, `warning`, `info`, `error` for the four drifts. Then a MUTATION run: temporarily replace the fallback-chain expression in `doctor.inspect_repo` with `severity="error"`, re-run the test file, and paste the FAILED output naming this test (and E-04's test); restore it, and paste an empty `git diff agent_workflows/doctor.py`.
  - Observed evidence:
    Pass run:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=4014160928
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 1 item

    tests/test_doctor_diagnostic_severity.py::test_doctor_inspect_repo_preserves_diagnostic_severity_seam PASSED [100%]

    ============================== 1 passed in 0.90s ===============================
    ```
    Mutation run (with `severity="error"` in `doctor.inspect_repo`):
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2897174303
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collecting 3 items                                                             collected 3 items

    tests/test_doctor_diagnostic_severity.py::test_doctor_inspect_repo_info_only_exit_code_and_status FAILED [ 33%]
    tests/test_doctor_diagnostic_severity.py::test_doctor_inspect_repo_preserves_diagnostic_severity_seam FAILED [ 66%]
    tests/test_doctor_diagnostic_severity.py::test_doctor_cli_preserves_diagnostic_severity_e2e FAILED [100%]

    =================================== FAILURES ===================================
    ...
    tests/test_doctor_diagnostic_severity.py:67: AssertionError: assert 'error' == 'info'
    ...
    tests/test_doctor_diagnostic_severity.py:148: AssertionError: agent: doctor.dangling-doc-reference diagnostic severity must be 'info', got 'error'
    =========================== short test summary info ============================
    FAILED tests/test_doctor_diagnostic_severity.py::test_doctor_inspect_repo_info_only_exit_code_and_status
    FAILED tests/test_doctor_diagnostic_severity.py::test_doctor_inspect_repo_preserves_diagnostic_severity_seam
    FAILED tests/test_doctor_diagnostic_severity.py::test_doctor_cli_preserves_diagnostic_severity_e2e
    ============================== 3 failed in 5.26s ===============================
    ```
    Restored and verified diff:
    ```
    $ git checkout agent_workflows/doctor.py && git diff agent_workflows/doctor.py
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted pytest output for the info-only exit-code test showing it passed.
  - Observed evidence:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2609233144
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 1 item                                                              collected 1 item

    tests/test_doctor_diagnostic_severity.py::test_doctor_inspect_repo_info_only_exit_code_and_status PASSED [100%]

    ============================== 1 passed in 1.15s ===============================
    ```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted pytest output for the CLI end-to-end test showing it passed (the observation is produced by `aw doctor --agent --verbose` and `aw doctor --json` via `doctor.inspect_repo`), the V-02 mutation run showing this test also went red, and the pasted summary line of a bare `python3 -m pytest` full-suite run with no new failures (any failure shown as pre-existing by re-running it at the base commit).
  - Observed evidence:
    CLI end-to-end test run:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=22809411
    rootdir: <repo-root>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 1 item                                                              collected 1 item

    tests/test_doctor_diagnostic_severity.py::test_doctor_cli_preserves_diagnostic_severity_e2e PASSED [100%]

    ============================== 1 passed in 4.09s ===============================
    ```
    Mutation run failure:
    Demonstrated in V-02 mutation run above where `tests/test_doctor_diagnostic_severity.py::test_doctor_cli_preserves_diagnostic_severity_e2e` failed with `AssertionError: agent: doctor.dangling-doc-reference diagnostic severity must be 'info', got 'error'`.
    Full suite summary line:
    ```
    7590 passed, 2 skipped, 3 warnings in 1092.96s (0:18:12)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). OQ-01 is resolved; none remain. `- Scope-Paths:` is a declaration that finalize reconciles: an out-of-scope edit that proves necessary is made and then justified with `--scope-reason`, and an unmodified declared path (expected for `agent_workflows/doctor.py` when E-01 finds no regression) gets a `--scope-ack`. Commit through `aw commit 2t9l37 -- <paths>` (never `git add -A`), and never push. Paste the ACTUAL runner output for every claim that a test passed; never claim a pass you did not run. After every `E-*` reads `performed`, every `V-*` reads `pass` with pasted evidence, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled lifecycle. Under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`. In a hand-driven execution the executor runs `aw ipd finalize 2t9l37 --actor <agent/model> --message <summary> --apply`. Backlog `wxpytg` (and its `Blocks-Release: next` gate, which this plan carries) is advanced by the runner's backlog-close step, never by hand.
