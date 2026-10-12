# IPD: Repair and collect the tools/ipdrunner shim tests

- Date: 2026-10-11
- Kind: child
- Concern: `tools/ipdrunner/test_runagy.py` is collected by NO standard invocation (`pyproject.toml` `testpaths = ["tests"]`; `Makefile` `test`/`test-all` and both `.github/workflows/tests.yml` pytest steps pass `tests/` explicitly), so its 25 tests rot invisibly. Measured at HEAD `d74169f1b`: `10 failed, 15 passed`, and every one of the 10 is drift between the test and the shipped runner, not a runner defect. The file is the only in-tree live reader of the `agy_runipd._read_id` re-export that `agy_runipd.py` and `oc_runipd.py` comments cite as justification for keeping it.
- Scope: Move the module into `tests/` (so every existing gate collects it with zero gate-config change), repair the 10 drifted tests against the CURRENT shipped behavior without weakening any behavioral assertion, update the in-code comments that cite the old path, and prove the bare suite now collects and passes it. No runner behavior changes.
- Scope-Paths: tools/ipdrunner/test_runagy.py, tests/test_ipdrunner_runagy_shim.py, agent_workflows/agy_runipd.py, agent_workflows/oc_runipd.py, tests/test_uncollected_test_modules.py
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: gte0pd
- Set: gte0pd
- Order: 1
- Highest E allocated: 07
- Author: opencode
- Id: g0u7f9

## Workflow history
- 2026-10-12 /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 fixed (review record 20261011-gte0pd-01-g0u7f9). Coordination note: sibling `5s31xp` seeds an EXEMPT entry for `tools/ipdrunner/test_runagy.py`; this plan's E-07 removes it if present.
- 2026-10-12 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-009

- 2026-10-12 to-review (opencode): authored review-ready from backlog gte0pd; option (b)-by-relocation chosen and recorded as OQ-01.
- 2026-10-12 draft (opencode): created.

## Goal

Make the `runagy.py` shim tests run in every developer run and in CI, green, by relocating the module into `tests/` and repairing its 10 drifted assertions to match the runner as it ships today, so the coverage hole backlog `gte0pd` describes is closed rather than merely documented.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and relocation

- [ ] E-01 Record the baseline: run `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q` and `python3 -m pytest --collect-only -q | grep -c test_runagy` at the starting HEAD, and run a bare `python3 -m pytest`, recording its summary line, wall time, and the NAMES of any failing tests (the comparison baseline for E-06). Also record whether `tests/test_uncollected_test_modules.py` exists at HEAD (it is added by pending plan `5s31xp`, Set `n8adhb`, which exempts `tools/ipdrunner/test_runagy.py` by name), and whether pending plan `vzk1iw` (backlog `fh8x8k`) has already landed its rewrite of the `_read_id` comments in `agent_workflows/agy_runipd.py`; E-06 and E-07 depend on both answers.
  - Depends on: none
  - Expected outcome: `10 failed, 15 passed` (or a stated, explained deviation if HEAD moved; re-measured at review HEAD `66401aeb1`: `10 failed, 15 passed`), collect count `0`, a recorded bare-suite summary with failing-test names and wall time, and the two sibling-plan facts recorded.
  - Execution state: pending

- [ ] E-02 `git mv tools/ipdrunner/test_runagy.py tests/test_ipdrunner_runagy_shim.py` and replace its module-level `sys.path.insert(...)` + `import runagy as driver` with `driver = support.load_module("ipdrunner_runagy_shim_under_test", REPO_ROOT / "tools" / "ipdrunner" / "runagy.py")` (`tests/support.py` `load_module` and `REPO_ROOT`, imported as `from tests.support import ...` or the form the neighbouring modules use), so the module still drives the SHIM, not `agent_workflows.agy_runipd` directly, WITHOUT permanently prepending `tools/ipdrunner/` to `sys.path` for every other test sharing the xdist worker (which would make `import runipd`/`import runagy` resolve suite-wide once the file is collected). The shim inserts the repo root itself, so nothing else is needed. Rewrite the `AgyEventRenderTests` docstring paragraph that says the module is "OUTSIDE THE BARE SUITE" and "ALREADY RED", since both statements become false; replace it with one sentence saying the module drives the runner through the `tools/ipdrunner/runagy.py` shim on purpose.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest tests/test_ipdrunner_runagy_shim.py -o addopts="" -q` reproduces the SAME `10 failed, 15 passed` (relocation alone changes no outcome), and `driver.__file__` ends in `tools/ipdrunner/runagy.py`.
  - Execution state: pending

### Task group 2: repair the 10 drifted tests (fixtures and assertions follow the shipped runner; no runner edits)

- [ ] E-03 Repair the `AgyExecutionLifecycleTests` FIXTURES (fixes the `RUN-STRUCTURE-PREFLIGHT` / exit-2 failures and unblocks the rest). In `_create_mock_repo`: write the plan from `tests.test_oc_runipd._CONFORMING_PLAN.format(id6="a1b2c3")` (the same fixture `tests/test_agy_runipd_cli.py` already imports) instead of the hand-written stub that lacks Concern/Scope/Scope-Paths/Priority/Work-Kind/Approval/Readiness and every required H2; write a `.gitignore` of `.aw/state/`, `.aw/worktrees/`, `.aw/records/runs/` (as `tests/test_agy_runipd_cli.py::_init_repo_with_conforming_plan` does); and commit a trivially passing `test_ok.py` so the runner's primary-checkout suite check (`runner_shared.run_suite_check`, argv `SUITE_CHECK_ARGV` = `python -m pytest`) has a green suite to find. In `_write_fake_agy`, make the VERIFIED verifier outcome carry a non-empty `tests_run` list, since the runner now refuses a VERIFIED verdict without test evidence (`verifier-no-test-evidence`). Do NOT change the fake's control flow otherwise.
  - Depends on: E-02
  - Expected outcome: `test_explicit_run_id`, `test_default_start_subcommand_inference`, `test_stall_timeout_and_resume_recovery`, `test_runagy_status_and_report_commands` pass; Lifecycle class `4 failed, 7 passed`, the 4 remaining being the ones E-04 owns (re-measured at review on a scratch copy with exactly these fixture changes: the 4 failing are `two_turn`, `prepare_only`, `verification_blocked`, `concurrent_work`; the result was identical with `AW_EXECUTION_ROLE=worker` set and unset). NOTE: `test_runagy_no_verify_skips_turn2` PASSES after E-03 only VACUOUSLY, because it asserts the absence of the superseded log name; E-04 (a) is what makes it meaningful again.
  - Execution state: pending

- [ ] E-04 Repair the four lifecycle ASSERTIONS that pin superseded runner output, each against the current authority named here: (a) `test_runagy_two_turn_execution_with_clean_verification` and `test_runagy_no_verify_skips_turn2`: verifier session log is now `01-a1b2c3-attempt-1-verify.jsonl` (`runner_shared.attempt_log_path`, shared since rununify 03 `i3d6ml`, which adopted the oc shape); keep `assertTrue` / `assertFalse` on that path, so the no-verify test still proves turn 2 did not run. (b) `test_verification_blocked_sets_disposition_partial`: a BLOCKED verdict now maps to status `fail-verify` (`runner_shared._VERDICT_TABLE`, `VERDICT_BLOCKED`); assert `fail-verify` and keep the `verification_status == "blocked"` assertion; rename the test to `..._sets_status_fail_verify`. (c) `test_prepare_only_mode`: assert on the current prepare-only output (the `Run order (1 item(s)): 01 a1b2c3` line and the `Run ID:` line) plus a behavioral check that `state.json` exists with one `queued` item and that NO session log was written (no `*.jsonl` under the run's `sessions/` directory; the directory itself IS created by prepare-only, measured at review). (d) `test_concurrent_work_statement_in_prompts`: stop pinning a verbatim prose paragraph (it drifted in wording and apostrophe); instead assert both prompts contain `## Concurrent Work` and that the Concurrent Work BLOCK extracted from each prompt is IDENTICAL between the execute and verifier prompts, which is the parity behavior the test exists for. Bound the block from `## Concurrent Work` through the end of its last sentence `Never discard their work.` (the text `runner_shared` emits in all three of its `## Concurrent Work` templates), NOT up to the next `## ` heading: measured at review, the execute prompt continues with un-headed run instructions after the block while the verifier prompt continues with its own preamble, so a next-heading boundary makes the two sections differ (`False`) while the terminal-sentence boundary makes them equal (`True`, 844 chars). Pass a `tempfile` run directory, not `/tmp/run` (review `2kyw59` PR-002 measured that the prompt builder materializes `outcomes/` under any path it is handed).
  - Depends on: E-03
  - Expected outcome: all 11 `AgyExecutionLifecycleTests` pass; no assertion is deleted without a replacement asserting the same behavior.
  - Execution state: pending

- [ ] E-05 Repair `AgyParserAndDiscoveryTests::test_dependency_status_execution_vs_review`. It builds `state = {"repo": "/nonexistent", ...}` and expects an `executed` in-queue dependency to satisfy an execute edge; since the maintainer ruling of 2026-09-19 recorded in `runner_shared.edge_satisfied`, the plan's DIRECTORY on disk is the only authority (measured: `dependency_status_detailed` returns `'executed:dep003: Cannot locate IPD dep003'`). Give the test a `tempfile` repo containing `dep003` as a conforming plan under `.aw/records/plans/executed/` and `dep001` (status `reviewed`) under `pending/`, set `state["repo"]` to it, and keep all three original cases: execute-on-reviewed blocked, execute-on-executed satisfied, review-on-reviewed satisfied. Add one case that the old in-memory shortcut would have passed and the ruling refuses: an in-queue item whose run status is `executed` but whose file is still in `pending/` does NOT satisfy an execute edge.
  - Depends on: E-02
  - Expected outcome: the test passes and exercises the disk-authority rule in both directions.
  - Execution state: pending

### Task group 3: citations and gate proof

- [ ] E-06 Update the comments that cite the old path: the `_read_id` comment block and the trailing `# noqa: F401` text in `agent_workflows/agy_runipd.py` (the "one live reader" paragraph and its disclosure 1 "OUTSIDE the bare suite" and disclosure 2 "pre-existing suite failures", which become false) and the `_read_id` comment in `agent_workflows/oc_runipd.py` ("consumed in `tools/ipdrunner/test_runagy.py`"). Point them at `tests/test_ipdrunner_runagy_shim.py::AgyParserAndDiscoveryTests::test_read_deps_and_set` and drop the two now-false disclosures. Comment-only: `git diff` of both files must touch no non-comment line (the trailing text after `# noqa: F401 -` on the import line is a comment, so editing it is in bounds; the import itself is not). SIBLING PLAN: `vzk1iw` (backlog `fh8x8k`, pending) rewrites these same comment blocks and removes that `noqa`. Edit whatever text is present at execution HEAD by the PROPERTY (no comment cites `tools/ipdrunner/test_runagy.py` or calls the reader uncollected or red), not by quoted text; if `vzk1iw` has already landed, its comments will cite the old path too, and the same rule applies.
  - Depends on: E-02
  - Expected outcome: `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools` returns nothing (after E-07 if the guard exists); `ruff check --select F401 agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py` still passes.
  - Execution state: pending

- [ ] E-07 Reconcile the uncollected-module guard. IF `tests/test_uncollected_test_modules.py` exists at execution HEAD (pending plan `5s31xp` adds it, seeding `EXEMPT` with `tools/ipdrunner/test_runagy.py` under owner `3rj8wr`), remove that one `EXEMPT` entry in the same commit as the move: the guard's stale-exemption rule fails when an exempt path no longer exists, so leaving it turns the bare suite red. Change nothing else in that file. IF the file does not exist, make no edit and acknowledge the declared path at finalize with `--scope-ack tests/test_uncollected_test_modules.py`; plan `5s31xp` must then not seed that entry (recorded in this plan's workflow history at review; the runner re-checks dependencies at dispatch, but nothing here orders the two plans, so whichever lands second reconciles).
  - Depends on: E-02
  - Expected outcome: either the guard exists and passes with the moved module collected and no `tools/ipdrunner/test_runagy.py` exemption, or the guard is absent and the path is acknowledged.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Suite contract (`AGENTS.md` repo-local section): run bare `python3 -m pytest`; `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; narrowed runs clear defaults with `-o addopts=""`.
- Collection surfaces, all keyed on `tests/`: `pyproject.toml` `testpaths = ["tests"]`; `Makefile` targets `test` (`python3 -m pytest tests/`) and `test-all`; `.github/workflows/tests.yml` steps `python -m pytest tests/ -n auto -rfEs` and `python -m pytest tests/ -n auto -m slow`. A file placed in `tests/` is therefore collected by all four with no config change.
- Fixture precedent: `tests/test_agy_runipd_cli.py` imports `_CONFORMING_PLAN` from `tests.test_oc_runipd` and writes the same `.gitignore` in `_init_repo_with_conforming_plan`; `tests/__init__.py` exists so `from tests...` imports work.
- Execution-role hygiene: tests driving lifecycle verbs in-process call `support.declare_execution_role(self)`; the lifecycle tests here drive the runner in a SUBPROCESS, so the executor must check whether `AW_EXECUTION_ROLE` leaks into that subprocess when the suite itself runs inside a runner lane, and pass an explicit `env` without it if so (`tests/support.py` `execution_role` docstring names the subprocess pattern). Measured at review inside a runner lane (`AW_EXECUTION_ROLE=worker` present): the repaired lifecycle class gave the same outcomes with the variable set and unset, so no explicit `env` is required; the executor re-checks this once and pastes it in V-03.
- No code-pinning tests (`AGENTS.md`, GUIDING_PRINCIPLES P16): repairs assert on runner outputs, exit codes, state files and session logs, never on source text.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | No standard invocation collects the module. | `python3 -m pytest --collect-only -q \| grep -c test_runagy` -> `0` at `d74169f1b`. |
| F-2 | Live count is 10 failed, not the 11 the backlog item recorded: plan `h0zk2g` (commit `25953c7e5`) already repaired `test_read_deps_and_set`. | `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q` -> `10 failed, 15 passed in 8.98s`. |
| F-3 | 6 lifecycle tests die in `RUN-STRUCTURE-PREFLIGHT` (exit 2): the fixture plan predates the ready-to-execute gate (missing Concern, Scope, Scope-Paths, Priority, Work-Kind, Approval, Readiness and all required H2s; `IPD-M101/M104/M106/M110/M111/M113`, `IPD-H202`). | Captured `E` lines from the run above. |
| F-4 | With a conforming fixture, the runner refuses a VERIFIED verdict lacking `tests_run` (`verifier-no-test-evidence`) and refuses integration when the primary-checkout suite check finds no suite (`integration still REFUSED after asking`). | Authoring experiment on a scratch copy under the gitignored `.aw/state/`, removed afterwards. |
| F-5 | Verifier log name moved to `<NN>-<id6>-attempt-<n>-verify.jsonl`. | `runner_shared.attempt_log_path` docstring (rununify 03 `i3d6ml`). |
| F-6 | BLOCKED verdict now yields status `fail-verify`. | `runner_shared._VERDICT_TABLE` `VERDICT_BLOCKED: VerdictMapping(VERIFY_DISP_BLOCKED, True, "fail-verify", True)`; measured `AssertionError: 'fail-verify' != 'partial'`. |
| F-7 | Prepare-only output no longer prints `01 a1b2c3 demo`; it prints `Run order (1 item(s)): 01 a1b2c3` and a table. | Measured assertion failure text. |
| F-8 | The Concurrent Work section gained a pre-commit verification paragraph and uses an ASCII apostrophe; the test pins the old verbatim prose. | `runner_shared.py` `## Concurrent Work` blocks vs the test's `expected` string. |
| F-9 | Execute-edge satisfaction reads disk only; `state["repo"] = "/nonexistent"` can never satisfy it. | `runner_shared.edge_satisfied` (2026-09-19 ruling); `dependency_status_detailed(...)` -> `(False, ['dep003'], {'dep003': 'executed:dep003: Cannot locate IPD dep003; configured path was '})`. |
| F-10 | The module is the only live reader of the `agy_runipd._read_id` re-export, and the comments justifying that re-export cite the uncollected path and disclose it as red. | `agent_workflows/agy_runipd.py` `_read_id` comment block; `agent_workflows/oc_runipd.py` `_read_id` comment. |
| F-11 | Sibling item `n8adhb` (now `graduated` to pending plan `5s31xp`, `reviewed`) covers `tools/test_agy_run.py` and adds a recurrence guard `tests/test_uncollected_test_modules.py` whose `EXEMPT` seeds `tools/ipdrunner/test_runagy.py` (owner `3rj8wr`) and fails on a stale exemption; `tools/awphysical/test_awphysical_tools.py` is a third uncollected module (owner `byz9pj`). | `.aw/records/backlog/graduated/20261001-n8adhb-01-n8adhb-tools-test-agy-run-not-collected.backlog.md`; `.aw/records/plans/pending/20261011-n8adhb-01-5s31xp-*.ipd.md` E-02. |
| F-12 | Backlog `3rj8wr` (open, `followup`, filed 2026-10-12 while graduating `n8adhb`) asks for exactly this plan's work (triage the 10 failures, relocate into `tests/`, drop the guard exemption). It is a duplicate of `gte0pd` and nothing links it here. | `.aw/records/backlog/open/20261011-3rj8wr-01-3rj8wr-triage-uncollected-test-runagy-failures.backlog.md`. |
| F-13 | Pending plan `vzk1iw` (backlog `fh8x8k`) rewrites the same `_read_id` comment blocks in `agy_runipd.py`/`oc_runipd.py` and its own E-03/E-05 prose cites `tools/ipdrunner/test_runagy.py`. | `.aw/records/plans/pending/20261011-fh8x8k-01-vzk1iw-*.ipd.md` E-03, E-05. |

## Proposed changes (ordered, validatable)

1. `tools/ipdrunner/test_runagy.py` -> `tests/test_ipdrunner_runagy_shim.py` (git mv; sys.path points at the shim directory; docstring corrected). E-02.
2. In the moved module: conforming fixture plan, `.gitignore`, passing `test_ok.py`, `tests_run` in the fake verifier. E-03.
3. In the moved module: four lifecycle assertions re-aimed at current runner authorities, none weakened. E-04.
4. In the moved module: dependency test given a real on-disk repo, plus a disk-authority negative case. E-05.
5. `agent_workflows/agy_runipd.py`, `agent_workflows/oc_runipd.py`: comment-only path update. E-06.
6. `tests/test_uncollected_test_modules.py`: drop the now-stale exemption if the guard exists. E-07.

## Deferred / out of scope (with reason)

- `tools/test_agy_run.py` and `tools/awphysical/test_awphysical_tools.py` collection, and any guard that fails when a `test_*.py` sits outside `testpaths`.
  - Carrier: n8adhb
- Adding `tools/` to `testpaths`, `Makefile` or CI. Rejected (OQ-01): relocation reaches every gate with no shared-gate edit.
  - Carrier-Declined: a rejected alternative, not owed work.
- Any change to runner behavior. Every failure is test drift (F-3..F-9); the runner is the authority being tested.
  - Carrier-Declined: nothing defective was found in the runner.

## Scope check

- Over-scope: none. The two `agent_workflows/` edits are comment-only and exist because the moved file is their cited evidence. `tests/test_uncollected_test_modules.py` is touched only to drop one exemption, and only if it exists (E-07).
- Under-scope: none known. The `_read_id` re-export gains real collected coverage as a side effect of E-02; no new pin is added for it (the s4jctz review recorded the maintainer ruling against import pins).

## Required tests / validation

- `python3 -m pytest tests/test_ipdrunner_runagy_shim.py -o addopts="" -q` -> `25 passed` (count may be 26 if E-05's added case is a separate test; the executor states which).
- Bare `python3 -m pytest` -> no failing test name absent from the E-01 baseline, and `python3 -m pytest --collect-only -q | grep -c test_ipdrunner_runagy_shim` is nonzero.
- `ruff check` on both edited `agent_workflows/` files passes.
- `aw ipd lint` on this plan conforms at pre-transition.

## Spec / documentation sync

N/A: no spec governs test placement for this module, and no user-facing doc names `tools/ipdrunner/test_runagy.py` (`git grep` of `docs/`, `CONTRIBUTING.md`, `tools/README.md` returns nothing). Historical review and plan records that cite the old path are history and are not edited.

## Open questions

### OQ-01: Which of the backlog item's four options to take?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Option (b), fix first then collect, implemented by RELOCATION into `tests/` rather than by widening `testpaths`. Evidence: the item's own objection to (a)/(b) is that collecting would turn 10 failures red in every run; this plan fixes all 10 before the file becomes collected, in the same commit, so no red state ever lands. Widening `testpaths` would not even reach CI or `make test`, which pass `tests/` explicitly (Step 0), so it would need three shared-gate edits; relocation needs none. (c) deleting would leave the two shims and the `_read_id` re-export with no runtime coverage. (d) is the status quo the item exists to end. The maintainer's instruction to graduate the item delegates the choice; the human may still overrule at review.

### OQ-02: Should the subprocess-driven lifecycle tests be marked `slow`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. `slow` is deselected by default and its CI step is `continue-on-error: true`, so marking them would recreate the very invisibility this plan removes. Precedent: `tests/test_agy_runipd_cli.py` drives git subprocesses unmarked. Measured during authoring: each lifecycle test is about 1 to 3 seconds (re-measured at review: slowest 4.65s, `test_stall_timeout_and_resume_recovery`; whole module about 23s serially); under `-n auto` that is a small share of the bare run. E-01 and V-06 record before/after wall time so a reviewer can dispute the number.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted summary lines of the baseline module run, the collect-only count, and the bare-suite summary line with its wall time and failing-test names, all at the starting HEAD (named by short sha); plus pasted `ls tests/test_uncollected_test_modules.py` and `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests` showing the sibling-plan state.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git status --short` showing the rename (`R  tools/ipdrunner/test_runagy.py -> tests/test_ipdrunner_runagy_shim.py`); pasted summary of the relocated module run BEFORE E-03 showing the same failure count as V-01; pasted output of `python3 -c` (or a test-time print removed afterwards) showing `driver.__file__` resolves to `tools/ipdrunner/runagy.py`; and the diff hunk showing no module-level `sys.path.insert` of `tools/ipdrunner` remains.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `-k AgyExecutionLifecycle` summary after E-03 alone, naming which tests pass and which remain failing, and the diff hunk of `_create_mock_repo` and of the fake verifier's outcome write.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `-k AgyExecutionLifecycle` summary showing all lifecycle tests pass; for each of (a)-(d) the before/after assertion lines from the diff, and one sentence per item naming the runner authority it now follows; confirmation that `test_runagy_no_verify_skips_turn2` asserts ABSENCE of the CURRENT verify-log name `01-a1b2c3-attempt-1-verify.jsonl` (the same name `two_turn` asserts PRESENT), and for (d) the extraction boundary used.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the rewritten test body; pasted passing run of `-k test_dependency_status`; and a falsification: temporarily move `dep003` back to `pending/` in the test, show the execute case fails, revert, and paste both outcomes.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `git diff agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py` pasted, showing comment-only hunks; empty output of `git grep -n "tools/ipdrunner/test_runagy" -- agent_workflows tests tools`; passing `ruff check` output; full-module run `python3 -m pytest tests/test_ipdrunner_runagy_shim.py -o addopts="" -q` with `0 failed`; bare `python3 -m pytest` summary line with failing-test names showing none absent from the V-01 baseline, and its wall time compared against V-01; and nonzero `python3 -m pytest --collect-only -q | grep -c test_ipdrunner_runagy_shim`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: EITHER the pasted `git diff tests/test_uncollected_test_modules.py` removing only the `tools/ipdrunner/test_runagy.py` `EXEMPT` entry plus a passing `python3 -m pytest -o addopts="" tests/test_uncollected_test_modules.py` run, OR pasted `ls tests/test_uncollected_test_modules.py` showing it absent and the `--scope-ack` recorded at finalize.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`aw ipd set approved g0u7f9 --by-human`); OQ-01 and OQ-02 are resolved and no question is open. Begin with `aw ipd begin g0u7f9`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. If an edit outside it proves necessary, make it and justify it at finalize with `--scope-reason <path>=<why>`; acknowledge a declared-but-unmodified path (E-07's conditional file) with `--scope-ack`. Do not edit runner code to make a test pass: if a repair reveals a genuine runner DEFECT rather than drift, stop that one item, file a backlog item (`aw backlog new`, `Work-Kind: bug`, with `- Blocks-Release: next`), mark the item `blocked`, and continue every independent item.

Honesty: you MUST paste the ACTUAL runner output for every test or command claim in each `V-*`; never claim a result you did not run.

Commits: the relocation, the repairs, and the E-07 exemption removal MUST land in ONE commit, so no intermediate state in history adds a collected red module (or a stale exemption) to the shared suite. Commit only the Scope-Paths you changed through `aw commit g0u7f9 -- <paths>`; never `git add -A`; verify `git diff --cached --name-only` before any raw commit; never push, never tag.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, run `aw ipd finalize g0u7f9`. Backlog `gte0pd` (no `- Blocks-Release:`) then closes with `aw backlog set done gte0pd`. Its duplicate `3rj8wr` (F-12) is discharged by the same work and should be closed with `aw backlog set done 3rj8wr --evidence <this plan's executed path>` once this plan is executed.
