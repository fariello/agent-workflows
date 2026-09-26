# IPD: Restore the outcome tests of the deleted executed-transition gate end-to-end suite

- Date: 2026-09-26
- Kind: child
- Concern: The suite trim `19313eed` deleted `tests/test_executed_transition_gate.py` (1267 lines, 3 classes, 6 test methods), the only end-to-end coverage of the pre-commit hook `agent_workflows/hooks/executed_transition_gate.py`: staged-situation verdicts and refusal reasons, the real `begin`+`finalize` commit through an installed hook, merge-aware in-tree evidence, git enforcing the gate at both `pre-commit` and `pre-merge-commit`, and the pre-commit config registration. Recovered at HEAD `61ef21d8` and placed under `tests/`, all 6 pass (`6 passed`). Approved plan `kecxnb` (fencegate-01) creates a NEW narrow file at that same path, so the restoration goes to `tests/test_executed_transition_gate_e2e.py`.
- Scope: IN: restore the recovered file as `tests/test_executed_transition_gate_e2e.py`, keeping only tests that assert outcomes; declare the execution role where the file drives `ipd_lifecycle.begin`/`finalize`; a module docstring stating its relation to kecxnb's file; PROVE COLLECTION by the bare suite (review PR-701: a filename pytest does not collect adds zero tests while the suite still reports green, so "the file exists and passes when named directly" is not evidence it runs); decide and record the `slow` marker per the project's documented convention (review PR-702). OUT: any change to the hook; kecxnb's file; restoring `tests/test_role_declaration_guard.py`, whose absence review found but which is a separate deleted file with its own restoration decision (review PR-704).
- Scope-Paths: tests/test_executed_transition_gate_e2e.py
- Item-Dependencies: executed:kecxnb
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: ove09p
- Set: restorecov
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 6vozur

## Workflow history
- 2026-09-26 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-701, PR-702, PR-703, PR-705 FIXED, PR-704 DEFERRED (over-scope). All four of the plan's own findings were REPRODUCED at HEAD `f375e650` and hold: the recovered file gives `6 passed` against the post-kecxnb hook, and `1 failed, 5 passed` under a worker-role re-assert, fixed to `6 passed` by the plan's exact E-02 remedy. The gaps were elsewhere. PR-701 (HIGH): the plan's success criteria cannot distinguish a real restoration from one that restores nothing - review restored the file under a non-conforming filename and the bare suite reported an unchanged, fully green `2436 passed` with all 6 tests uncollected, so E-04 now demands a test COUNT (+6 exactly). PR-702: the `slow` marker was declined on duration when `pyproject.toml` defines it by KIND, so E-03/OQ-02 now require a recorded decision with both sides' measurements. PR-703: the verification recipe hardcoded an out-of-workspace path, and its obvious simplification (`AW_EXECUTION_ROLE=worker`) reports `6 passed` against the UNFIXED file because `conftest.py` scrubs the marker. 3 items -> 5 with a 5:5 E/V bijection. Baseline recorded for the executor: `2436 passed, 1 skipped in 41.67s`. Review record: `.aw/records/reviews/20260926-restorecov-01-6vozur-restore-the-outcome-tests-of-the-deleted-executed-transition.review.md`.
- 2026-09-26 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED; PR-701..PR-705 (PR-704 DEFERRED as over-scope). All four of the plan's findings reproduced and hold; the gaps were a missing collection check and an unexamined slow-marker convention. 3 items -> 5.
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

- [ ] E-03 DECIDE AND RECORD THE `slow` MARKER, rather than declining it on wall-clock alone (review PR-702). The project's documented criterion is KIND, not duration: the `slow` marker is defined in `pyproject.toml` as "heavy subprocess/integration tests (spawn the CLI, install into temp repos)", and all four shipped users carry it for that reason (`tests/test_cli.py`, `tests/test_installer.py`, `tests/test_leak_sanitizer.py` file-wide; `tests/test_completion.py` on its one CLI-spawning class, with a comment saying it is marked because it SPAWNS the CLI). This file matches that description on its face: 13 `subprocess.run` call sites, real `git init`/`merge`/`commit`, an installed `pre-commit` hook shelling `python3 -m agent_workflows ipd-executed-gate`. Weigh that against the measured cost: review measured the bare suite at 2436 passed in 38.12/40.64/44.54s WITHOUT the file and 2442 passed in 46.75/43.65/38.59s WITH it, i.e. a delta inside run-to-run noise, and the file alone at 3.71-5.21s. Note the ORIGINAL file carried NO marker before deletion (`git show 19313eed^:tests/test_executed_transition_gate.py | rg pytestmark` is empty), so leaving it unmarked RESTORES the prior state and is defensible. Pick one, write the reason into the module docstring, and state it in the Scope check. If marked `slow`, say plainly that the default suite no longer runs it and E-04's bare-suite count will NOT include these 6.
  - Depends on: E-02
  - Expected outcome: a recorded decision with its reason in the file, consistent with the Scope check; no silent omission of the question.
  - Execution state: pending

- [ ] E-04 PROVE THE FILE IS ACTUALLY COLLECTED BY THE BARE SUITE, by test COUNT and not by a green summary (review PR-701). Paste the bare `python3 -m pytest` total BEFORE the file exists and AFTER, and show the difference is exactly +6 (review measured 2436 -> 2442; re-derive both at the executing HEAD rather than reusing those numbers). This item exists because a green suite is NOT evidence of collection: review named the restored file `tests/_probe_e2e_restore.py` by accident, and the bare suite reported `2436 passed` - unchanged, fully green, with all 6 restored tests silently uncollected, because pytest's default `python_files` is `test_*.py` and `pyproject.toml` sets no override. A restoration whose whole purpose is regaining coverage can therefore "pass" while restoring nothing. If E-03 marked the file `slow`, the bare delta is instead +0 BY DESIGN: in that case paste `python3 -m pytest -m slow` (or `make test-all`) showing the 6 collected there, and say which case applies.
  - Depends on: E-03
  - Expected outcome: the bare-suite delta is exactly +6 (unmarked) or the 6 are demonstrably collected under `-m slow` (marked); either way a COUNT, never a bare "green".
  - Execution state: pending

- [ ] E-05 Verify the rest: run `python3 -m pytest -o addopts="" tests/test_executed_transition_gate_e2e.py -v` (6 named tests); run it under a worker-role re-assert plugin written INSIDE the repo tree or a workspace-local temp dir, NOT the hardcoded `/tmp/opencode/roleplug` the authoring session used (review PR-703: that path is machine-local and outside the executing workspace; an isolated lane may not be able to write it). Use the SHAPE the repository itself documents: `conftest.py` scrubs `AW_EXECUTION_ROLE` at import, so the marker must be re-asserted AFTER that scrub, which is why a plain `AW_EXECUTION_ROLE=worker python3 -m pytest` is NOT a substitute - review measured that spelling reporting `6 passed` even against the UNFIXED file, so it cannot prove the guard. The deleted `tests/test_role_declaration_guard.py` (recoverable at `19313eed^`) contains the canonical `_REASSERT_PLUGIN` using `pytest_configure`; reuse that shape. Then run it next to kecxnb's file (`tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py`) to show no name or fixture collision.
  - Depends on: E-04
  - Expected outcome: 6 passed direct; 6 passed under the re-assert plugin (it was `1 failed, 5 passed` before E-02); 12 passed combined with kecxnb's file.
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
| F-5 | HIGH | collection, not correctness (review PR-701) | A GREEN SUITE IS NOT EVIDENCE THE RESTORED TESTS RUN. pytest's default `python_files` is `test_*.py` and `pyproject.toml` sets no override, so a non-conforming filename contributes ZERO tests while the bare suite still reports fully green. Since this plan's entire deliverable is regained coverage, its success criterion must be a test COUNT, not a pass/fail. Hence E-04. | Review restored the file as `tests/_probe_e2e_restore.py` and the bare suite reported `2436 passed, 1 skipped ... in 40.16s` - identical to the baseline `2436 passed` - with all 6 tests silently uncollected. Renamed to `tests/test_executed_transition_gate_e2e.py`: `2442 passed, 1 skipped in 43.99s`, i.e. exactly +6. |
| F-6 | MED | the `slow` marker question (review PR-702) | THE PROJECT'S CRITERION IS KIND, NOT DURATION, so the plan's Scope-check dismissal ("the file ran 6 tests in under 5s") answers a question the convention does not ask. `pyproject.toml` defines `slow` as "heavy subprocess/integration tests (spawn the CLI, install into temp repos)", and this file is 13 `subprocess.run` sites, real `git init`/`merge`/`commit`, and an installed hook shelling `python3 -m agent_workflows`. The decision may still be NOT to mark (the original was unmarked, and the measured suite delta is inside noise), but it must be MADE against the stated criterion, not sidestepped. Hence E-03. | `pyproject.toml` marker definition; `tests/test_completion.py`'s marked class carries the comment "The only test here that SPAWNS the CLI, so it carries the `slow` marker"; `tests/test_cli.py`, `tests/test_installer.py`, `tests/test_leak_sanitizer.py` file-wide `pytestmark = pytest.mark.slow`. Bare suite: 38.12/40.64/44.54s without vs 46.75/43.65/38.59s with. Original file at `19313eed^`: no `pytestmark`. |
| F-7 | MED | E-03's verification recipe as authored (review PR-703) | THE RE-ASSERT RECIPE WAS NOT REPRODUCIBLE AS WRITTEN, on two counts. (a) It hardcodes `/tmp/opencode/roleplug`, a machine-local path outside the executing workspace that an isolated lane may not be able to write. (b) The obvious simplification does not work and the plan does not warn against it: `AW_EXECUTION_ROLE=worker python3 -m pytest` reports `6 passed` even against the UNFIXED file, because `conftest.py` pops the variable at import time, so an executor who "simplified" the recipe would conclude F-4 was wrong and skip E-02. | `conftest.py`: `os.environ.pop("AW_EXECUTION_ROLE", None)` with the rationale above it; measured `AW_EXECUTION_ROLE=worker python3 -m pytest -o addopts="" <unfixed file>` -> `6 passed in 3.71s`; measured via `pytest_runtest_setup` re-assert on the same unfixed file -> `1 failed, 5 passed in 3.44s`. |
| F-8 | LOW | `conftest.py`'s cross-reference is STALE (review PR-704) | `conftest.py` twice points a reader at `tests/test_role_declaration_guard.py` as the harness that proves role-independence, and the same trim `19313eed` DELETED that file (222 lines). So the shipped comment cites a file that does not exist, and the canonical `_REASSERT_PLUGIN` shape this plan's verification needs lives only in git history. Recorded, not fixed here: it is a different deleted file with its own restoration decision, and `conftest.py` is outside this plan's fence. | `19313eed --stat` lists `tests/test_role_declaration_guard.py` at 222 deleted lines; `ls tests/test_role_declaration_guard.py` -> No such file; `conftest.py` references it at its "CROSS-REFERENCE:" line and in its honest-limits paragraph. `git show 19313eed^:tests/test_role_declaration_guard.py` still recovers it, including `PROTECTED_FILES` and `_REASSERT_PLUGIN`. |

## Proposed changes (ordered, validatable)

1. E-01: restore at the new path with a corrected docstring head.
2. E-02: role declarations.
3. E-03: decide and record the `slow` marker against the kind-based criterion.
4. E-04: prove collection by test COUNT (the delta must be +6).
5. E-05: verify direct, under an in-workspace re-assert plugin, and beside kecxnb's file.

## Deferred / out of scope (with reason)

- Nothing is deferred: all six restored tests assert outcomes and are kept.
  - Carrier-Declined: no outstanding obligation.

## Scope check

- Over-scope: none.
- Under-scope: closed by review. Two gaps were found and are now items rather than omissions. (1) The plan had no COLLECTION check, so its deliverable could be reported complete while restoring zero tests (F-5); E-04 adds a count-based criterion. (2) The `slow` marker was declined on DURATION ("the file ran 6 tests in under 5s"), but the project's criterion is KIND, and this file is exactly the subprocess/integration shape the marker names (F-6); E-03 makes it a recorded decision either way. A third gap is recorded and deliberately NOT fixed here: `conftest.py`'s cross-reference to the deleted `tests/test_role_declaration_guard.py` is stale (F-8), which is a different file's restoration decision and outside this fence.

## Required tests / validation

- The restored file under pytest (6 named tests), under an IN-WORKSPACE re-assert plugin (and shown `1 failed, 5 passed` without the E-02 declarations, so the declaration is proven load-bearing), and beside kecxnb's file (12 passed).
- The bare suite, judged by COUNT: the total must move by exactly +6, or the 6 must be shown collected under `-m slow` if E-03 marks the file. A green summary with an unchanged count is a FAILED restoration, not a pass (F-5).
- Test rule: outcomes only; F-2 records the audit and review independently confirmed it (no `inspect`, `getsource`, `__doc__` or source-text read anywhere in the file; the only `read_text` calls are on plan fixtures the tests themselves wrote).

## Spec / documentation sync

N/A: test-only restoration.

## Open questions

### OQ-01: Keep the configuration-registration test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Keep. It asserts the parsed values `pre-commit install` acts on, so it detects a real behavior loss (the merge-stage hook silently not installed) that no other in-repo test can observe without running `pre-commit install`; it pins no source text, formatting or wording. REVIEW CONFIRMED and adds the honest limit the answer should carry: this is the one test in the file that reads the LIVE repository's `.pre-commit-config.yaml` rather than a fixture it built, so it is the one test any change to that file can turn red. Verified it passes at the executing HEAD (all three rows match: `default_install_hook_types: [pre-commit, pre-merge-commit]`, `default_stages: [pre-commit]`, and `ipd-executed-transition-gate` the sole `pre-merge-commit` opt-in). That coupling is the POINT (a silently-disabled merge stage is invisible otherwise) and it is not the `livecorpus` case, which concerns the `.aw/records/` artifact tree that any agent can perturb; no `livecorpus`-marked test exists in the suite today.

### OQ-02: Mark the restored file `slow`?

- Blocking: no
- Status: resolved
- Owner: the executor, at E-03
- Carrier: 6vozur
- Resolution or deferral rationale: RESOLVED 2026-09-26 by the maintainer: do NOT mark the restored file `slow`. Reason: the measured full-suite cost is within run-to-run noise, the original file carried no marker, and marking it would drop the regained coverage from the default suite every lane runs. E-03 therefore leaves it unmarked and E-04 proves collection in the DEFAULT suite. The pre-resolution analysis follows for the record: DELIBERATELY LEFT TO EXECUTION with the criterion and the measurements supplied, rather than decided here, because both answers are defensible on the evidence and the choice changes what E-04 must prove. FOR marking: `pyproject.toml` defines `slow` as "heavy subprocess/integration tests (spawn the CLI, install into temp repos)" and this file is 13 `subprocess.run` sites driving real `git init`/`merge`/`commit` plus an installed hook that shells `python3 -m agent_workflows`, which is that description almost verbatim; all four shipped users of the marker carry it for exactly this reason. AGAINST marking: the file measured 3.71-5.21s alone and the bare-suite delta (38.12/40.64/44.54s without vs 46.75/43.65/38.59s with) is inside run-to-run noise, the original file carried no marker before deletion so leaving it unmarked restores the prior state, and marking it removes these 6 tests from the default suite that every lane runs - which for a restoration whose purpose is regained coverage is a real cost. Non-blocking because either choice is safe once E-03 records the reason and E-04 proves collection in the matching surface.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `diff <(git show 19313eed^:tests/test_executed_transition_gate.py) tests/test_executed_transition_gate_e2e.py` showing only the docstring head, the `support` import and the two declarations differ.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `grep -n "declare_execution_role" tests/test_executed_transition_gate_e2e.py` showing two hits plus the `from tests import support` import, and the re-assert-plugin run summary showing `6 passed`. Then paste the SAME plugin run against the file WITHOUT the declarations, showing `1 failed, 5 passed` and the `AW-LIFECYCLE-ROLE-001` message, so the declaration is proven load-bearing rather than assumed (review re-measured both).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the module-docstring lines recording the `slow` decision and its reason; paste the Scope check sentence agreeing with it; paste the timing measurements the decision rests on (the file alone, and the bare suite with and without it). If the decision is NOT to mark, the evidence must show the kind-based criterion was considered and answered, not skipped: quote `pyproject.toml`'s marker definition and say why this file is treated differently from the four shipped users.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the bare `python3 -m pytest` SUMMARY LINE from before the file exists and from after, with the arithmetic shown, and state the delta explicitly. A green summary alone does NOT satisfy this item; the count must move by exactly 6 (or the `-m slow` run must show the 6, if E-03 marked it). Also paste `python3 -m pytest --collect-only -q tests/test_executed_transition_gate_e2e.py | tail -1` as a direct collection check.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_executed_transition_gate_e2e.py -v` showing 6 passed with the six names; paste the re-assert-plugin run showing `6 passed`, together with the plugin's source and its path (which must be inside the workspace); paste the combined run with `tests/test_executed_transition_gate.py` showing 12 passed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: five items, one concern (restore one deleted test file so the hook regains end-to-end coverage). E-03 and E-04 are separate from the restore because each answers a question the restore itself cannot: whether the file belongs in the default suite, and whether it is actually collected. Review measured that without E-04 the plan can report success having restored zero running tests.

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One restored test file (6 tests, about 4-5s), audited as outcome-only with nothing dropped (F-2, F-3, both independently re-verified at review), plus two role declarations. Ordered after kecxnb because kecxnb creates the sibling file at the original path and changes the hook these tests exercise; kecxnb is now `executed`, so the dependency is satisfied and review confirmed all 6 restored tests pass against the post-kecxnb hook with no collision against kecxnb's file (12 passed combined).

ONE OPEN CHOICE IS LEFT TO THE EXECUTOR, NAMED HERE SO IT IS NOT A SURPRISE: whether this file carries the `slow` marker (OQ-02, decided at E-03). Marked, it leaves the default suite every lane runs and lives only in `make test-all`; unmarked, it restores the pre-deletion state and stays in the fast suite at a measured cost inside run-to-run noise. The evidence for both sides is in OQ-02 and the criterion is in `pyproject.toml`. A human who wants the other answer should say so at approval.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the Scope-Paths above. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. TWO CLAIMS ARE SPECIFICALLY NOT ACCEPTED AS GREEN-MEANS-DONE, because review measured each producing a false pass. A bare-suite summary with an UNCHANGED total does not demonstrate the restoration (the count must move by exactly 6, or the 6 must appear under `-m slow`). And `AW_EXECUTION_ROLE=worker python3 -m pytest` does NOT demonstrate the role fix: `conftest.py` pops that variable at import, so that spelling reports `6 passed` even against the unfixed file, and only a post-scrub re-assert plugin can observe the condition.

GENUINE STOP CONDITIONS, each requiring a human rather than a local workaround:
- A restored test fails against the post-kecxnb hook: do NOT edit the test to pass; report it, since that would be a behavior regression in the hook.
- `test_both_git_stages_are_registered_with_only_the_gate_at_merge_time` fails: it reads the LIVE `.pre-commit-config.yaml`, so a failure means the repository's real merge-stage registration changed. Report it; do not relax the test to match the current config, which would discard the only detection of a silently-disabled merge-stage hook.
- The bare-suite delta is neither +6 nor explained by an E-03 `slow` decision: stop. Something is not being collected, and a green summary will hide it.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize` (the runner owns it in a lane). Then set backlog item `ove09p` `done` with `--evidence` citing the executed plan.
