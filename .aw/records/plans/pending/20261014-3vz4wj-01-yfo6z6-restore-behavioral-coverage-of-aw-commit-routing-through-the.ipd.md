# IPD: Restore behavioral coverage of aw commit routing through the shared offer_commit helper

- Date: 2026-10-14
- Kind: child
- Concern: `aw commit` (`work_cmd.run_commit`) is required to commit ONLY through the shared `git_commit_helper.offer_commit` (snapshot-then-intersect, path-scoped staging, `on_unrelated_staged="scope"`), but the behavioral tests that proved this were deleted with `tests/test_work_primitives.py` in commit `19313eed`, so a forked `git commit` path in `run_commit` would now go undetected.
- Scope: Add one new behavioral test module that drives `aw commit` through `cli.main` against a throwaway git repo and asserts (a) the shared helper is invoked exactly once with only the requested paths and `on_unrelated_staged="scope"`, for both plan-governed and `--no-plan` modes, and (b) with the helper stubbed to commit nothing, no `git commit` subprocess is spawned and HEAD is unchanged; then remove the now-stale "no live guard currently asserts this" remark in `work_cmd.run_commit`.
- Scope-Paths: tests/test_work_commit_routes_through_shared_helper.py, agent_workflows/work_cmd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 3vz4wj
- Set: 3vz4wj
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: yfo6z6

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog 3vz4wj; review-ready.

## Goal

Restore, as behavioral tests only (P16), the guarantee that `aw commit` routes every commit through `git_commit_helper.offer_commit` and carries no forked `git commit` path of its own, which was lost when `tests/test_work_primitives.py` was deleted (`ev7t1w` site S-27, disposition RETIRE-UNGUARDED).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: delegation tests

- [ ] E-01 Create `tests/test_work_commit_routes_through_shared_helper.py` with a `unittest.TestCase` whose `setUp` calls `support.declare_execution_role(self)` and builds a throwaway git repo carrying an approved plan `wk0001` with `- Scope-Paths: src/, tests/` (same fixture shape as `tests/test_commit_default_message.py` `_PLAN` / `CommitDefaultMessageTest.setUp`). Add tests that wrap the real `git_commit_helper.offer_commit` in a recording spy via `mock.patch.object(gch, "offer_commit", spy)` and drive `cli.main(["commit", "wk0001", "--dir", <root>, "-m", "add feature", "--", "src/feature.py"])` and the plan-less form `cli.main(["commit", "--no-plan", "-m", "...", "--dir", <root>, "--", "src/feature.py"])`, asserting: exit code 0; the spy was called exactly once; the recorded repo root equals the fixture root; the recorded paths equal exactly `["src/feature.py"]`; the recorded `on_unrelated_staged` kwarg equals `"scope"`; and `git show --name-only HEAD` lists `src/feature.py` and no other path. Also add a co-worker case: a second, unrelated path is pre-staged before the plan-less commit, and the test asserts it is absent from the new HEAD commit and still staged afterward.
  - Depends on: none
  - Expected outcome: the new module exists and its delegation tests pass against the current `work_cmd.run_commit`.
  - Execution state: pending
- [ ] E-02 In the same module add a no-fork test: stub `gch.offer_commit` to return `gch.CommitOutcome(status=gch.STATUS_NOTHING_TO_COMMIT, message="stubbed", staged=[], commit=None)` and wrap `subprocess.Popen` with a recording wrapper that still calls the real `Popen` (the `_GitArgvRecorder` approach used by the deleted module at `19313eed^:tests/test_work_primitives.py`, re-implemented locally, recognizing the git subcommand after skipping `-C <dir>` / `-c <cfg>` globals). Drive both the plan-governed and `--no-plan` forms and assert: exit code 1; no recorded git subcommand equals `commit`; HEAD before equals HEAD after. Add a sanity sub-assertion that the recorder DOES observe a `commit` subcommand when the real helper is left unstubbed, so the absence assertion cannot pass vacuously.
  - Depends on: E-01
  - Expected outcome: the no-fork tests pass, and the sanity check proves the recorder sees real `git commit` invocations.
  - Execution state: pending

### Task group 2: stale remark

- [ ] E-03 In `agent_workflows/work_cmd.py` `run_commit`, rewrite the comment in the `if no_plan:` branch that reads "`tests/test_work_primitives.py` (deleted in `19313eed`; no live guard currently asserts this) proved this verb carries no forked commit path of its own" so it cites `tests/test_work_commit_routes_through_shared_helper.py` as the live guard. Comment-only change; no behavior change.
  - Depends on: E-02
  - Expected outcome: the comment names the new live test module and no longer claims the guard is absent.
  - Execution state: pending

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): tests must drive the code and assert on outputs, exit codes and side effects; never read source via `inspect`/`ast`/regex. Patching a collaborator (`mock.patch.object(gch, "offer_commit", ...)`) and recording spawned argv is behavioral observation, not a source pin.
- The suite runs bare as `python3 -m pytest` (pyproject `addopts` supplies `-q -n auto`); tests must be xdist-safe, so each test uses its own `tempfile.TemporaryDirectory` repo and `support.declare_execution_role(self)` per `tests/support.py` `declare_execution_role`.
- CLI-driving pattern: `cli.main(argv)` under `redirect_stdout`/`redirect_stderr`, catching `SystemExit`, as in `tests/test_commit_default_message.py` `CommitDefaultMessageTest._run`.
- `work_cmd` binds the helper as module alias `_gch` (`from agent_workflows import git_commit_helper as _gch`) and calls `_gch.offer_commit(...)` at call time, so patching the attribute on the `git_commit_helper` module is observed by `run_commit`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `work_cmd.run_commit` ends with `outcome = _gch.offer_commit(repo_root, paths, message=..., assume_yes=..., no_commit=..., on_unrelated_staged="scope", trailers=..., runner=...)` and has no other commit path; this is the property to guard.
- Executed plan `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`) row S-27: `work_cmd.py` / `run_commit` / `tests/test_work_primitives.py` / `19313eed` / RETIRE-UNGUARDED.
- The deleted module held `test_commit_delegates_to_the_one_shared_commit_helper` and `test_commit_holds_no_forked_git_commit_path_of_its_own` (visible via `git show 19313eed7^:tests/test_work_primitives.py`); both were behavioral and are the model for E-01/E-02.
- Current coverage check: `rg -l offer_commit tests/` lists helper-level and other-caller tests (`tests/test_git_commit_helper.py`, `tests/test_agent_commit_identity.py`, etc.), none of which drives `aw commit` with the helper observed or stubbed. `tests/test_commit_default_message.py` and `tests/test_commit_scope_reason.py` drive `aw commit` end to end but would still pass if `run_commit` forked its own `git commit`.
- The `--no-plan` branch comment in `run_commit` currently states "no live guard currently asserts this", which becomes false after E-01/E-02.

## Proposed changes (ordered, validatable)

1. E-01: new test module with spy-based delegation tests (plan and `--no-plan`) plus the co-worker-staged-path case.
2. E-02: no-fork tests with the helper stubbed and a `Popen` argv recorder, plus a non-vacuity sanity check.
3. E-03: comment-only update in `work_cmd.run_commit` pointing at the new guard.

## Deferred / out of scope (with reason)

- Restoring the other tests deleted with `tests/test_work_primitives.py` (`aw work begin`, `aw test`, `aw finish`): not part of backlog `3vz4wj`, which names only the `run_commit` routing property.
- Any change to `run_commit` or `git_commit_helper` behavior: this is a coverage-restoration chore.

## Scope check

- Over-scope: none. The only production edit is a comment that would otherwise become false.
- Under-scope: none. Both halves of the property (positive delegation and absence of a fork) are covered, in both commit modes.

## Required tests / validation

- `python3 -m pytest tests/test_work_commit_routes_through_shared_helper.py` passes (V-01, V-02).
- Mutation check: temporarily replace the `_gch.offer_commit(...)` call in `run_commit` with a direct `git commit` and confirm the new tests FAIL, then revert (V-02).
- Full bare suite `python3 -m pytest` passes with no new failures (V-03).

## Spec / documentation sync

N/A: no spec or user-facing documentation describes these tests; the only text change is the in-code comment in E-03.

## Open questions

### OQ-01: Should the restored tests live in a new module or be appended to an existing commit test module?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: a new, purpose-named module `tests/test_work_commit_routes_through_shared_helper.py`. Existing modules (`tests/test_commit_default_message.py`, `tests/test_commit_scope_reason.py`) are each scoped to one other behavior by their docstrings, and a dedicated module makes the guard discoverable by name, which is what the E-03 comment cites.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_work_commit_routes_through_shared_helper.py` showing each delegation test (plan mode, `--no-plan` mode, co-worker staged path) PASSED, plus a `grep -nE "inspect|ast\.|read_text\(.*work_cmd" tests/test_work_commit_routes_through_shared_helper.py` returning no source-reading match.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing the no-fork tests and the non-vacuity sanity check PASSED; AND pasted output of a temporary mutation run (the `_gch.offer_commit(...)` call in `run_commit` replaced with a direct `git commit` subprocess) showing at least one test in the new module FAILED, followed by `git diff --stat agent_workflows/work_cmd.py` proving the mutation was reverted (only the E-03 comment remains).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/work_cmd.py` showing only comment lines changed and naming `tests/test_work_commit_routes_through_shared_helper.py`; AND the pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the two Scope-Paths files through `aw commit yfo6z6 -- <paths>`; never push. Do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and V-01..V-03 carry pasted observed evidence with `Result: pass`.
