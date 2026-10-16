# IPD: Govern and regression-test the work begin plan_path relativization fix for clean-delta repos

- Date: 2026-10-16
- Kind: child
- Concern: `aw work begin` crashed with `ValueError` on clean-delta repos (`completely-clean-target`, `local-only`) because the plan lives under `<AW_HOME>/projects/<id>/records/` and `Path.relative_to(repo_root)` raises for an out-of-root path. A guard landed inline during `nwporz` (commit `3d80673c1`) as declared scope drift, with no governing plan and no dedicated regression test.
- Scope: Add a dedicated behavioral regression test module for the `run_work_begin` lease `plan_path` computation covering both the out-of-root (clean-delta) and in-root (tracked records) cases, prove it fails without the guard, normalize the out-of-root value to POSIX form, and record the fix in CHANGELOG.
- Scope-Paths: agent_workflows/work_cmd.py, tests/test_work_begin_plan_path_outside_root.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: 707qi4
- Blocks-Release: next
- Set: 707qi4
- Order: 1
- Highest E allocated: 04
- Author: opencode
- Id: t1fri2

## Workflow history

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog 707qi4; review-ready.

## Goal

Make the `aw work begin` clean-delta fix a governed, regression-locked behavior: a dedicated test proves `aw work begin` succeeds and writes a well-formed lease when the plan lives outside `repo_root`, and still writes a repo-relative POSIX `plan_path` when the plan is in-tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Code hardening

- [ ] E-01 In `work_cmd.run_work_begin`, change the `except ValueError:` fallback (`plan_rel = str(plan_path)`) to `plan_rel = plan_path.resolve().as_posix()` so the out-of-root lease value is an absolute POSIX path on every platform, matching the in-root branch's `.replace("\\", "/")` normalization. Leave the in-root branch and the `aw commit` fallback (`plan_rel = plan_path.name`, which feeds `_in_scope`/commit-message derivation, not a lease) unchanged.
  - Depends on: none
  - Expected outcome: `git diff agent_workflows/work_cmd.py` shows only the fallback line changed inside `run_work_begin`.
  - Execution state: pending

### Task group 2: Regression tests

- [ ] E-02 Create `tests/test_work_begin_plan_path_outside_root.py` with a test that, in a temp git repo with temp `HOME`/`AW_HOME` and `AW_NO_REEXEC=1`, installs the `completely-clean-target` preset, scaffolds a child plan, sets its dependencies to `none`, runs `python -m agent_workflows.cli work begin <id6>` as a subprocess, and asserts: exit code 0; stderr contains no `ValueError`/`Traceback`; the `work-lease.json` under `<AW_HOME>/projects/<project_id>/` (located by glob for `work-lease.json`) parses as JSON, its `plan_path` is absolute, contains no backslash, resolves to the scaffolded plan file, and `plan_id` equals the id6. Mirror the setup of `tests/test_clean_target_zero_delta_e2e.py` (`TestCleanTargetZeroDeltaE2E.setUp`).
  - Depends on: E-01
  - Expected outcome: the new test passes against the fixed code.
  - Execution state: pending
- [ ] E-03 In the same module add an in-root counterpart: a temp repo installed with the default (tracked-records) preset, plan scaffolded under `<repo>/.aw/records/plans/pending/`, `work begin <id6>` exits 0, and the lease `plan_path` equals the repo-relative POSIX path `.aw/records/plans/pending/<file>` (not absolute). If the default install places the lease somewhere other than under `AW_HOME`, locate it by globbing `work-lease.json` under both the repo `.aw/` and `AW_HOME`.
  - Depends on: E-02
  - Expected outcome: the in-root test passes, proving the guard did not regress the relative form.
  - Execution state: pending
- [ ] E-04 Mutation proof (TEMPORARY, MUST NOT be committed): replace the try/except in `run_work_begin` with the pre-fix `plan_rel = str(plan_path.relative_to(repo_root))`, run the new module and capture the failure of the out-of-root test, then restore the E-01 code with `git diff` confirming only E-01's change remains. Then add a CHANGELOG `2.0.0 (pending)` bullet: "`aw work begin` no longer crashes on clean-delta installs (`completely-clean-target`, `local-only`) whose plans live outside the repository."
  - Depends on: E-03
  - Expected outcome: out-of-root test fails on the reverted code, passes on the restored code; CHANGELOG carries the bullet.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Clean-delta records live under `AW_HOME`, routed by `project_context.resolve_project_context`; the work lease path comes from `work_cmd._work_dir` -> `ipd_lifecycle.control_state_dir` (IPD `qk0ew6` E-06).
- `ipd_lifecycle._repo_relative` documents that a repo-relative plan path is an IDENTITY key only sound for in-root paths; the lease `plan_path` is informational and is not read back by any consumer (`rg '"plan_path"' agent_workflows` shows only the writer in `work_cmd.run_work_begin` and the unrelated `ipd_lifecycle` receipt writer plus `runner_shared` queue readers that do not read `work-lease.json`).
- Tests must exercise behavior (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); subprocess-driven CLI tests with temp `HOME`/`AW_HOME` are the established pattern (`tests/test_clean_target_zero_delta_e2e.py`).
- Commits through `aw commit t1fri2 -- <paths>`; never push.

## Findings

| ID | Severity | Finding |
|---|---|---|
| F-01 | High | Pre-fix `run_work_begin` computed `"plan_path": str(plan_path.relative_to(repo_root))`, which raises `ValueError` when the plan resolves under `AW_HOME` (clean-delta presets). |
| F-02 | Medium | Commit `3d80673c1` ("fix(work): catch ValueError when relativizing plan_path on clean-delta", AW-Item `nwporz`) added the guard as declared out-of-scope drift (`nwporz` `- Scope-Exceeded:`); no plan governs it. |
| F-03 | Medium | The only coverage is the incidental step `self._run_aw("work", "begin", id6, ...)` inside `test_clean_target_zero_delta_e2e`, which asserts exit 0 and zero target delta but not the lease `plan_path` contents, and has no in-root counterpart. |
| F-04 | Low | The fallback `str(plan_path)` is not POSIX-normalized, unlike the in-root branch. |

Baseline observed during authoring: `python3 -m pytest -o addopts="" -q tests/test_clean_target_zero_delta_e2e.py -x` -> `2 passed in 19.65s`.

## Proposed changes (ordered, validatable)

1. E-01: POSIX-normalize the out-of-root fallback in `work_cmd.run_work_begin`.
2. E-02/E-03: new behavioral test module covering out-of-root and in-root lease `plan_path`.
3. E-04: temporary mutation proof plus CHANGELOG bullet.

## Deferred / out of scope (with reason)

None. (No outstanding obligation is deferred: `aw commit` already guards its own relativization with `plan_rel = plan_path.name` and is exercised end to end by `tests/test_clean_target_zero_delta_e2e.py`, and no consumer of the lease needs a schema change.)

## Scope check

- Over-scope: none.
- Under-scope: none; the crash path, its fallback form, and both branches of the guard are each covered by an E-item.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_work_begin_plan_path_outside_root.py` passes (E-02, E-03).
- `python3 -m pytest -o addopts="" -q tests/test_clean_target_zero_delta_e2e.py` still passes.
- Mutation proof shows the out-of-root test fails without the guard (E-04).
- Routine gate `python3 -m pytest` passes.

## Spec / documentation sync

CHANGELOG bullet (E-04). No spec change: no spec describes the lease `plan_path` field's form, and behavior visible to users (the verb succeeding) is already what the clean-target spec promises.

## Open questions

### OQ-01: Should the out-of-root lease plan_path be absolute or just the file name?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Absolute. The committed fix (`3d80673c1`) already chose `str(plan_path)` (absolute) for `work begin`; an absolute path uniquely locates the plan under `AW_HOME`, whereas a bare name does not. E-01 only normalizes separators.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `git diff agent_workflows/work_cmd.py` showing only the `except ValueError:` fallback in `run_work_begin` changed to `plan_path.resolve().as_posix()`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted actual pytest output of `python3 -m pytest -o addopts="" -v tests/test_work_begin_plan_path_outside_root.py` showing the out-of-root test PASSED, plus the observed lease JSON `plan_path` value (produced by the `aw work begin` subprocess the test drives via `work_cmd.run_work_begin`).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: same pytest output showing the in-root test PASSED, with the observed relative `plan_path` value pasted.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted failing pytest output (showing `ValueError` or non-zero exit) from the reverted-code run, pasted passing output after restore, `git diff --stat` showing no reverted code remains, the CHANGELOG diff, and pasted routine gate `python3 -m pytest` summary line plus `tests/test_clean_target_zero_delta_e2e.py` passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Do not execute until `- Status: approved`. Execute in an isolated worktree (`aw work begin t1fri2`, or under `aw oc run`, which isolates by default), in order E-01..E-04. Mark an `E-*` performed only after doing it and a `V-*` pass only with concrete pasted evidence; paste the ACTUAL runner output. Every probe uses a temp git repo with temp `HOME`/`AW_HOME`; never install into this repository or touch the real home. The E-04 mutation is temporary and MUST NOT be committed. Commit through `aw commit t1fri2 -- <paths>`; never `git add -A`, never push, never `--no-verify`.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize t1fri2`. This plan inherits `- Blocks-Release: next` from backlog `707qi4`.
