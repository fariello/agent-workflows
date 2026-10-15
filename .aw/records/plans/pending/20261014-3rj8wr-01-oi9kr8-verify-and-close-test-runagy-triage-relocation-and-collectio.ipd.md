# IPD: Verify and close test_runagy triage, relocation, and collection guard handoff

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `3rj8wr` (filed 2026-10-12 while graduating `n8adhb` into plan `5s31xp`) asks to triage the 10 failing tests in uncollected `tools/ipdrunner/test_runagy.py`, fix or retire each, relocate the module into `tests/` so standard gates run it, and remove its exemption from `tests/test_uncollected_test_modules.py`. Sibling backlog `gte0pd` (filed 2026-09-30 for the same defect) was already graduated to plan `g0u7f9` (`20261011-gte0pd-01-g0u7f9-repair-and-collect-the-tools-ipdrunner-shim-tests.ipd.md`) and executed in commit `b417e9c2d`, which performed the entire triage, repair, relocation (`tools/ipdrunner/test_runagy.py` -> `tests/test_ipdrunner_runagy_shim.py`), and exemption removal, but left `3rj8wr` open because `g0u7f9` carried `- From-Backlog: gte0pd` rather than `3rj8wr`.
- Scope: Verify on the current tree with pasted runner output that `tools/ipdrunner/test_runagy.py` has been relocated to `tests/test_ipdrunner_runagy_shim.py`, that all 10 historical failures across its three failure shapes remain repaired and every collected test in `tests/test_ipdrunner_runagy_shim.py` passes, that no stale `tools/ipdrunner/test_runagy.py` exemption or code citation remains in `agent_workflows/`, `tests/`, or `tools/` (with `tests/test_uncollected_test_modules.py` passing), and conditionally repair `tests/test_ipdrunner_runagy_shim.py` or `tests/test_uncollected_test_modules.py` only if verification reveals test drift or a residual reference (a product regression is filed as a release-gating `bug` instead, never repaired by editing the test; see E-03), so `3rj8wr` can close with a verified carrier.
- Scope-Paths: tests/test_ipdrunner_runagy_shim.py, tests/test_uncollected_test_modules.py, .aw/records/plans/pending/20261014-3rj8wr-01-oi9kr8-verify-and-close-test-runagy-triage-relocation-and-collectio.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: medium
- From-Backlog: 3rj8wr
- Set: 3rj8wr
- Order: 1
- Highest E allocated: 03
- Author: antigravity
- Id: oi9kr8

## Workflow history
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-003
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003 fixed (review record 20261014-3rj8wr-01-oi9kr8)
- 2026-10-14 to-review (aw set): authored review-ready from backlog 3rj8wr; commit b417e9c2d (plan g0u7f9) already triaged, repaired, relocated, and collected tools/ipdrunner/test_runagy.py

- 2026-10-14 draft (antigravity): created.

## Goal

Graduate backlog `3rj8wr` by verifying with pasted runner output that the triage, repair, relocation (`tools/ipdrunner/test_runagy.py` -> `tests/test_ipdrunner_runagy_shim.py`), and uncollected-module guard exemption removal landed in commit `b417e9c2d` (plan `g0u7f9`, backlog `gte0pd`) remain intact and green on the current tree, repairing the module or guard only if a check fails.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Confirm relocation, reference cleanup, and collection guard

- [ ] E-01 Confirm on the tracked tree that `tools/ipdrunner/test_runagy.py` has been relocated to `tests/test_ipdrunner_runagy_shim.py`, that no tracked code or test file under `agent_workflows/`, `tests/`, or `tools/` still cites `tools/ipdrunner/test_runagy` (`git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools`, where exit code 1 means zero matches; historical markdown records under `.aw/records/` are immutable history and excluded), and that the uncollected-module guard `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` passes with `tests/test_ipdrunner_runagy_shim.py` collected by bare `pytest` (`python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_ipdrunner_runagy_shim.py::"` returning a nonzero count) and no `tools/ipdrunner/test_runagy.py` key in `tests.test_uncollected_test_modules.EXEMPT`.
  - Depends on: none
  - Expected outcome: `git ls-files --error-unmatch tests/test_ipdrunner_runagy_shim.py` succeeds while `git ls-files tools/ipdrunner/test_runagy.py` is empty; `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools` exits 1 with no output; `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` passes all collected tests (2 at authoring HEAD `73e295d27`); and `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_ipdrunner_runagy_shim.py::"` is nonzero (25 at authoring HEAD).
  - Execution state: pending

### Task group 2: Confirm all triaged tests in the relocated module pass

- [ ] E-02 Run the relocated shim test module with per-test output: `python3 -m pytest -o addopts="" -v tests/test_ipdrunner_runagy_shim.py`.
  - Depends on: none
  - Expected outcome: every collected test in `tests/test_ipdrunner_runagy_shim.py` passes with zero failures and zero errors (`25 passed` at authoring HEAD `73e295d27`, context rather than a hardcoded count bar), including all three failure shapes named in backlog `3rj8wr`: (a) the `AgyExecutionLifecycleTests` subprocess runs (`test_runagy_two_turn_execution_with_clean_verification`, `test_default_start_subcommand_inference`, `test_prepare_only_mode`, `test_explicit_run_id`, `test_runagy_no_verify_skips_turn2`, `test_verification_blocked_sets_status_fail_verify`, `test_stall_timeout_and_resume_recovery`, `test_runagy_status_and_report_commands`), (b) `AgyExecutionLifecycleTests.test_concurrent_work_statement_in_prompts`, and (c) `AgyParserAndDiscoveryTests.test_dependency_status_execution_vs_review`. These names are NON-BINDING POINTERS to the three behaviors (the runner lifecycle under a conforming fixture, the emitted `## Concurrent Work` prompt section, and disk-authoritative execute-edge satisfaction), not the bar: the bar is that every collected test passes, re-derived at execution. One historical name was renamed by `b417e9c2d`: `test_verification_blocked_sets_disposition_partial` (pre-move) is now `test_verification_blocked_sets_status_fail_verify`, so the absence of the old name is expected and not a lost test.
  - Execution state: pending

### Task group 3: Conditional repair and bare-suite verification

- [ ] E-03 Record the pre-execution bare-suite baseline (`python3 -m pytest`, recording the summary line and any failing test node IDs). If `E-01` found a stale `tools/ipdrunner/test_runagy` reference or exemption in `tests/test_uncollected_test_modules.py`, or if `E-02` reported any failure in `tests/test_ipdrunner_runagy_shim.py`, FIRST triage each failure as test drift or a product regression, exactly as `g0u7f9` F-3..F-9 did. Only TEST DRIFT (a fixture or assertion pinning superseded but intended runner behavior) may be repaired, with the minimal edit to the offending file in `Scope-Paths`, then re-run `E-01` and `E-02` until green. A PRODUCT REGRESSION (the runner now behaves wrongly) MUST NOT be "repaired" by editing or weakening the test: leave the test red, file it with `aw backlog new --summary "<what>" --priority high --work-kind bug --apply` and set its `- Blocks-Release: next` (AGENTS.md "Every live bug gates the next release"), mark this item `blocked` naming that backlog id6, and stop rather than finalize; otherwise record "no change required" citing the `V-01` and `V-02` evidence (since commit `b417e9c2d` already landed the repair, relocation, and exemption removal). Run the bare suite `python3 -m pytest` and confirm no new failing test node ID appears relative to the baseline.
  - Depends on: E-01, E-02
  - Expected outcome: either a per-failure drift-vs-regression triage plus a minimal test-drift diff to `tests/test_ipdrunner_runagy_shim.py` or `tests/test_uncollected_test_modules.py` followed by passing `E-01`/`E-02` re-runs; or, for a product regression, a filed `bug` backlog id6 with `Blocks-Release: next` and this item `blocked`; or an explicit "no change required" record (with unmodified `Scope-Paths` acknowledged at finalize via `--scope-ack`), plus a pasted bare `python3 -m pytest` summary line with no new failing test node IDs.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The test suite is run bare as `python3 -m pytest` (`AGENTS.md` repo-local development contract), where `pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Narrowed runs that need per-test `-v` or `--collect-only` output clear the configured defaults explicitly with `-o addopts=""`.
- Tests must exercise observable behavior and outcomes (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE", `GUIDING_PRINCIPLES` P16); the `git grep` in `E-01` is an executor verification step, not a committed code-pinning test.
- Commits go through `aw commit <plan> -- <paths>` (`AGENTS.md` execution contract).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at starting HEAD `73e295d27` in this lane.

| # | Finding | Evidence |
|---|---|---|
| F-01 | Backlog `3rj8wr` is a duplicate of backlog `gte0pd` (now `done`), which was graduated to plan `g0u7f9` and executed in commit `b417e9c2d`. | `.aw/records/plans/executed/20261011-gte0pd-01-g0u7f9-repair-and-collect-the-tools-ipdrunner-shim-tests.ipd.md` Finding F-12 explicitly notes: "Backlog `3rj8wr` (open, `followup`, filed 2026-10-12 while graduating `n8adhb`) asks for exactly this plan's work (triage the 10 failures, relocate into `tests/`, drop the guard exemption). It is a duplicate of `gte0pd` and nothing links it here." |
| F-02 | Triage result for all 10 historical failures in `tools/ipdrunner/test_runagy.py`: every failure was stale test drift against the shipped runner, not a product regression. | Proven in `g0u7f9` Findings F-3..F-9 and commit `b417e9c2d`: (1) the 6 subprocess runs failing in `RUN-STRUCTURE-PREFLIGHT` (`IPD-M101` missing `Concern` and other required metadata/H2s) plus 1 verifier failure (`verifier-no-test-evidence`) used a hand-written pre-gate stub in `AgyExecutionLifecycleTests._create_mock_repo` and a `VERIFIED` outcome lacking `tests_run` in `AgyExecutionLifecycleTests._write_fake_agy`, and three assertions pinned superseded output (`01-a1b2c3-verify-attempt-1.jsonl` instead of `runner_shared.attempt_log_path`'s `01-a1b2c3-attempt-1-verify.jsonl`, status `"partial"` instead of `runner_shared._VERDICT_TABLE[VERDICT_BLOCKED]`'s `"fail-verify"`, and old `--prepare-only` table text); (2) `AgyExecutionLifecycleTests.test_concurrent_work_statement_in_prompts` pinned an older verbatim paragraph before `runner_shared.py` added the pre-commit verification paragraph to `## Concurrent Work`; (3) `AgyParserAndDiscoveryTests.test_dependency_status_execution_vs_review` passed `state = {"repo": "/nonexistent", ...}`, which `runner_shared.edge_satisfied` rightly refuses because on-disk directory placement is authoritative for `executed` dependencies. |
| F-03 | `tools/ipdrunner/test_runagy.py` has already been relocated to `tests/test_ipdrunner_runagy_shim.py` and passes all 25 tests. | `git show --stat b417e9c2d` shows `tools/ipdrunner/test_runagy.py` moved to `tests/test_ipdrunner_runagy_shim.py`. Running `python3 -m pytest -o addopts="" -v tests/test_ipdrunner_runagy_shim.py` at HEAD `73e295d27` gives `25 passed in 31.99s`. |
| F-04 | The exemption in `tests/test_uncollected_test_modules.py` has already been removed and the guard passes. | `tests.test_uncollected_test_modules.EXEMPT` holds only `tools/awphysical/test_awphysical_tools.py`, `tools/aw_upgrade_test.py`, and `tests/test_lift_drift_scan.py`. Running `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` at HEAD `73e295d27` gives `2 passed in 12.81s`, and `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools` exits 1 with zero matches. |
| F-05 | Why `3rj8wr` remained `open`: `g0u7f9` carried `- From-Backlog: gte0pd`, so the runner's `process_backlog_close` closed `gte0pd` and did not touch `3rj8wr`. | `.aw/records/backlog/done/20260930-gte0pd-01-gte0pd-ipdrunner-tests-uncollected.backlog.md` workflow history records automatic closure by `aw agy run` on `g0u7f9`; `3rj8wr` has no prior `From-Backlog` carrier. Once this plan (`oi9kr8`, `- From-Backlog: 3rj8wr`) executes, `3rj8wr` closes cleanly via the runner's `process_backlog_close` (or `aw backlog set done 3rj8wr --evidence <executed-plan-path>` when run by hand). |
| F-06 | Plan review (2026-10-15) independently reproduced the 10 historical failures and the green relocated module. | Replaying `git show b417e9c2d^:tools/ipdrunner/test_runagy.py` from a temporary copy under `tools/ipdrunner/` (removed afterwards) with `python3 -m pytest -o addopts="" -q -p no:randomly` gave `10 failed, 15 passed`, naming the three shapes F-02 lists, with the pre-move name `test_verification_blocked_sets_disposition_partial`. The relocated module plus the guard gave `27 passed`, and `--collect-only` counted 25 shim tests. |

## Proposed changes (ordered, validatable)

1. `E-01` / `E-02`: verify on the execution tree that the relocation, citation/exemption cleanup, collection guard, and all 25 shim tests in `tests/test_ipdrunner_runagy_shim.py` remain green (no file edits expected).
2. `E-03`: conditional minimal repair to `tests/test_ipdrunner_runagy_shim.py` or `tests/test_uncollected_test_modules.py` only if `E-01` or `E-02` fails, followed by bare-suite verification.

## Deferred / out of scope (with reason)

- Repairing and relocating `tools/awphysical/test_awphysical_tools.py` (the remaining red uncollected test module in `tests.test_uncollected_test_modules.EXEMPT`): separate regression surface with its own backlog item (`byz9pj`), outside `3rj8wr`'s scope.
  - Carrier: byz9pj
- Rewriting `_read_id` re-export bindings in `agent_workflows/agy_runipd.py` to remove `# noqa: F401`: separate concern owned by sibling plan `vzk1iw` (backlog `fh8x8k`), outside `3rj8wr`'s scope.
  - Carrier: vzk1iw
  - Carrier-Evidence: .aw/records/plans/executed/20261011-fh8x8k-01-vzk1iw-justify-agy-runipd-re-exports-by-its-same-name-idiom-and-rec.ipd.md
- Modifying runner behavior in `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py`, or `agent_workflows/runner_shared.py`: all 10 failures in `test_runagy.py` were stale test fixtures/assertions, not runner defects (F-02).
  - Carrier-Declined: nothing defective was found in the runner; every failure was test drift already repaired in commit b417e9c2d.

## Scope check

- Over-scope: none.
- Under-scope: none; every requirement in backlog `3rj8wr` (triage each failure, fix or retire, relocate into `tests/`, and remove the exemption from `tests/test_uncollected_test_modules.py`) is accounted for in F-01..F-05 and verified by `E-01`..`E-03`.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py`: all collected tests pass (`V-01`).
- `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_ipdrunner_runagy_shim.py::"`: nonzero collected count (`V-01`).
- `python3 -m pytest -o addopts="" -v tests/test_ipdrunner_runagy_shim.py`: every collected test passes with zero errors and zero failures (`V-02`).
- Bare `python3 -m pytest`: summary line pasted and compared by failing test node ID against the pre-execution baseline (`V-03`).

## Spec / documentation sync

N/A: no specification or user-facing documentation references `tools/ipdrunner/test_runagy.py` or `tests/test_ipdrunner_runagy_shim.py` (`git grep` across `.aw/records/specs/` and `docs/` returns zero matches), and no user-visible behavior changes.

## Open questions

### OQ-01: Is any code change left given that plan `g0u7f9` (commit `b417e9c2d`) already triaged, repaired, relocated, and collected `tools/ipdrunner/test_runagy.py`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Repository evidence (F-01 through F-04) shows that commit `b417e9c2d` (executing plan `g0u7f9` for duplicate backlog `gte0pd`) already completed the code and test changes requested by `3rj8wr`. Following the precedent of executed plan `3or4ce` (backlog `u18kic`), this plan carries the verification and conditional repair so `3rj8wr` has a verified `From-Backlog` carrier and closes with pasted runner evidence.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste (1) the output and exit status of `git ls-files --error-unmatch tests/test_ipdrunner_runagy_shim.py` and `git ls-files tools/ipdrunner/test_runagy.py`; (2) the output and exit status of `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools` (showing exit status 1 and no matches, or listing any matches for `E-03`); (3) the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_uncollected_test_modules.py` showing all tests `PASSED`; and (4) the output of `python3 -m pytest --collect-only -q -o addopts="" | grep -c "^tests/test_ipdrunner_runagy_shim.py::"` showing a nonzero count.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the per-test `-v` output and summary line of `python3 -m pytest -o addopts="" -v tests/test_ipdrunner_runagy_shim.py`, showing every collected test `PASSED` with zero failures and zero errors.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste either `git diff -- tests/test_ipdrunner_runagy_shim.py tests/test_uncollected_test_modules.py` of the repair plus passing re-runs of `V-01`/`V-02`, or a "no change required" record citing `V-01`, `V-02`, and commit `b417e9c2d`; in both cases paste the pre-execution baseline and post-verification summary lines of a bare `python3 -m pytest` run with any failing test node IDs compared to show no new failure.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved oi9kr8 --by-human`). Open questions: OQ-01 is resolved; none remain. Start execution with `aw ipd begin oi9kr8`. `- Scope-Paths:` is a DECLARATION reconciled at finalize: if an out-of-scope edit proves necessary, make it and justify it with `--scope-reason <path>=<why>`, and when `tests/test_ipdrunner_runagy_shim.py` and `tests/test_uncollected_test_modules.py` require no edit (the expected no-change outcome because commit `b417e9c2d` already landed the work), acknowledge them at finalize with `--scope-ack` (or let `aw oc run` / `aw agy run` auto-acknowledge declared-but-unmodified paths). HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; never claim a pass you did not run. If a repair is needed, commit only the modified files in `Scope-Paths` through `aw commit oi9kr8 -- <paths>` (never `git add -A`, `-a`, or `--no-verify`), verify `git diff --cached --name-only` before committing, and never push. Lifecycle: under `aw oc run` / `aw agy run` the runner owns `finalize` after its merge-and-revalidate gate, so do NOT run `aw ipd finalize` inside the runner; when executed by hand, run `aw ipd finalize oi9kr8` once `aw ipd lint --phase pre-transition` conforms and `V-01`..`V-03` hold pasted evidence with `Result: pass`. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`. Once this plan is `executed`, backlog `3rj8wr` closes `done` via the runner's `process_backlog_close` (or `aw backlog set done 3rj8wr --evidence <executed-plan-path>` when executed by hand).
