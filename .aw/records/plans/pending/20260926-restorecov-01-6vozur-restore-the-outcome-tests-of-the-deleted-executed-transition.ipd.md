# IPD: Restore the outcome tests of the deleted executed-transition gate end-to-end suite

- Date: 2026-09-26
- Kind: child
- Concern: The suite trim `19313eed` deleted `tests/test_executed_transition_gate.py` (1267 lines, 3 classes, 6 test methods), the only end-to-end coverage of the pre-commit hook `agent_workflows/hooks/executed_transition_gate.py`: staged-situation verdicts and refusal reasons, the real `begin`+`finalize` commit through an installed hook, merge-aware in-tree evidence, git enforcing the gate at both `pre-commit` and `pre-merge-commit`, and the pre-commit config registration. Recovered at HEAD `61ef21d8` and placed under `tests/`, all 6 pass (`6 passed`). Approved plan `kecxnb` (fencegate-01) creates a NEW narrow file at that same path, so the restoration goes to `tests/test_executed_transition_gate_e2e.py`.
- Scope: IN: restore the recovered file as `tests/test_executed_transition_gate_e2e.py`, keeping only tests that assert outcomes; declare the execution role where the file drives `ipd_lifecycle.begin`/`finalize`; a module docstring stating its relation to kecxnb's file. OUT: any change to the hook; kecxnb's file.
- Scope-Paths: tests/test_executed_transition_gate_e2e.py
- Item-Dependencies: executed:kecxnb
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: ove09p
- Set: restorecov
- Order: 1
- Highest E allocated: 03
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6vozur

## Workflow history
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog ove09p: restore the 6-test executed-transition gate e2e suite from 19313eed^ as tests/test_executed_transition_gate_e2e.py; all six audited as outcome tests.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The executed-transition hook regains end-to-end coverage that proves, by outcome, that a raw executed transition is refused with an actionable reason, finalize's own commit and an evidenced lane merge are allowed, and git fires the gate at both hook stages.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore, audit, verify

- [ ] E-01 Write `git show 19313eed^:tests/test_executed_transition_gate.py` to `tests/test_executed_transition_gate_e2e.py`. Its path assumptions already hold at `tests/` (`Path(__file__).resolve().parents[1]` for the `PYTHONPATH` pin in `MergeAwareInTreeEvidenceTests._env` and for `.pre-commit-config.yaml` in `PreCommitConfigStageRegistrationTests.setUp`), so no path edit is needed. Replace the module docstring's first paragraph with: this is the RESTORED end-to-end suite deleted by `19313eed`; `tests/test_executed_transition_gate.py` (plan kecxnb) holds the narrow `_has_executed_status` unit cases; the two files are complementary. Keep the rest of the docstring (it explains the table design).
  - Depends on: none
  - Expected outcome: the file exists at the new path and imports cleanly.
  - Execution state: pending

- [ ] E-02 Apply the outcome audit (see Findings F-2): keep all six methods, and make `support.declare_execution_role(self)` the first statement of `PreCommitExecutedGateTests.setUp` and `MergeAwareInTreeEvidenceTests.setUp` (add `from tests import support`). The first is required: measured under a re-asserted `AW_EXECUTION_ROLE=worker`, `test_real_finalize_own_commit_passes_via_installed_hook` FAILS (`1 failed, 5 passed`) because it calls `LC.begin`/`LC.finalize` in-process. The second is declared for the same rule (its lanes build finalize commits). No other code change; if kecxnb has landed, the file's tests must still pass unchanged against kecxnb's hook.
  - Depends on: E-01
  - Expected outcome: 6 tests, all passing with and without a re-asserted worker marker.
  - Execution state: pending

- [ ] E-03 Verify: run `python3 -m pytest -o addopts="" tests/test_executed_transition_gate_e2e.py -v`; run it with the throwaway re-assert plugin (`/tmp/opencode/roleplug/reassert_worker.py`: `@pytest.hookimpl(trylast=True) def pytest_runtest_setup(item): os.environ["AW_EXECUTION_ROLE"] = "worker"`, invoked with `PYTHONPATH=/tmp/opencode/roleplug ... -p reassert_worker`); run it next to kecxnb's file (`tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py`) to show no name or fixture collision; run the bare suite.
  - Depends on: E-02
  - Expected outcome: 6 passed in each run; bare suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Maintainer decision 2026-09-26: restore IFF the restored tests check OUTCOMES only; drop any test pinning source text, docstrings, or "code has not changed"; keep the count small.
- `support.declare_execution_role` is required for any test that drives `ipd_lifecycle.begin`/`finalize` in-process (see plan yx9xsa / backlog owi0no).
- `PyYAML` is in the `test` extra (`pyproject.toml` `[project.optional-dependencies] test`), so the config-registration test's `import yaml` is satisfied in CI.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `61ef21d8` on the file recovered from `19313eed^`.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | MED | hook coverage | The recovered suite still passes against today's hook. | copied under `tests/`, `python3 -m pytest <file> -o addopts="-q -p no:cacheprovider"` -> 6 passed (combined run with the lane-manifest file: `27 passed in 5.82s`) |
| F-2 | INFO | outcome audit, all 6 kept | (1) `test_each_staged_situation_gets_its_own_verdict_and_reason`: `GATE.check` exit code, refusal reason and plan id per staged situation, and that the gate mutated nothing: OUTCOME. (2) `test_real_finalize_own_commit_passes_via_installed_hook`: a real finalize commits through an installed hook and the plan lands in `executed/`: OUTCOME. (3) `test_the_merge_detector_reports_the_incoming_side_in_every_state`: `_merge_incoming_commits` returns the incoming shas for real merge states: OUTCOME of the evidence finder (computed from real git state, not source). (4) `test_merge_state_never_becomes_a_blanket_exemption`: `check` verdicts inside real merges: OUTCOME. (5) `test_git_itself_enforces_the_gate_at_both_merge_stages`: real `git merge`/`git commit` exit status with the hook installed at each stage: OUTCOME. (6) `test_both_git_stages_are_registered_with_only_the_gate_at_merge_time`: parses `.pre-commit-config.yaml` and asserts the three values `pre-commit` consumes to decide which hooks git installs; this is configuration that drives behavior (a misspelled key silently disables the merge stage), not source text or wording. | read of each method body |
| F-3 | INFO | dropped tests | None dropped: no method asserts source text, a docstring, or "code unchanged". The file's needles are refusal WORDING the operator sees (`gained '- Status: executed'` etc.), which is user-facing output, not source. | same |
| F-4 | MED | `test_real_finalize_own_commit_passes_via_installed_hook` | Fails under a re-asserted worker role; needs the role declaration. | with the re-assert plugin: `1 failed, 5 passed in 4.91s` |

## Proposed changes (ordered, validatable)

1. E-01: restore at the new path with a corrected docstring head.
2. E-02: role declarations.
3. E-03: verify.

## Deferred / out of scope (with reason)

- Nothing is deferred: all six restored tests assert outcomes and are kept.
  - Carrier-Declined: no outstanding obligation.

## Scope check

- Over-scope: none.
- Under-scope: none. The `slow` marker is not added: the file ran 6 tests in under 5s.

## Required tests / validation

- The restored file under pytest, under the re-assert plugin, and beside kecxnb's file; bare suite. Test rule: outcomes only; F-2 records the audit.

## Spec / documentation sync

N/A: test-only restoration.

## Open questions

### OQ-01: Keep the configuration-registration test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Keep. It asserts the parsed values `pre-commit install` acts on, so it detects a real behavior loss (the merge-stage hook silently not installed) that no other in-repo test can observe without running `pre-commit install`; it pins no source text, formatting or wording.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `diff <(git show 19313eed^:tests/test_executed_transition_gate.py) tests/test_executed_transition_gate_e2e.py` showing only the docstring head, the `support` import and the two declarations differ.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -n "declare_execution_role" tests/test_executed_transition_gate_e2e.py` showing two hits, and the re-assert-plugin run summary showing `6 passed` (it was `1 failed, 5 passed` without the declaration).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_executed_transition_gate_e2e.py -v` showing 6 passed with the six names; paste the combined run with `tests/test_executed_transition_gate.py` passing; paste the final summary line of a BARE `python3 -m pytest` showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One restored test file (6 tests, about 5s), audited as outcome-only with nothing dropped (F-2, F-3), plus two role declarations. Ordered after kecxnb because kecxnb creates the sibling file at the original path and changes the hook these tests exercise.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`.

GENUINE STOP CONDITION: if a restored test fails against the post-kecxnb hook, do not edit the test to pass; report it, since that would be a behavior regression in the hook.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `ove09p` `done` with `--evidence` citing the executed plan.
