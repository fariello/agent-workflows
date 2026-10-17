# IPD: Govern and regression-test the work begin plan_path relativization fix for clean-delta repos

- Date: 2026-10-16
- Kind: child
- Concern: `aw work begin` crashed with `ValueError` on clean-delta repos (`completely-clean-target`, `local-only`) because the plan lives under `<AW_HOME>/projects/<id>/records/` and `Path.relative_to(repo_root)` raises for an out-of-root path. A guard landed inline during `nwporz` (commit `3d80673c1`) as declared scope drift, with no governing plan and no dedicated regression test.
- Scope: Add a dedicated behavioral regression test module for the `run_work_begin` lease `plan_path` computation covering both the out-of-root (clean-delta) and in-root (tracked records) cases, prove it fails without the guard, normalize the out-of-root value to POSIX form, and record the fix in CHANGELOG.
- Scope-Paths: agent_workflows/work_cmd.py, tests/test_work_begin_plan_path_outside_root.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: 707qi4
- Blocks-Release: next
- Set: 707qi4
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: t1fri2
- Approval: 2026-10-16, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog 707qi4; review-ready.

## Goal

Make the `aw work begin` clean-delta fix a governed, regression-locked behavior: a dedicated test proves `aw work begin` succeeds and writes a well-formed lease when the plan lives outside `repo_root`, and still writes a repo-relative POSIX `plan_path` when the plan is in-tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Code hardening

- [x] E-01 In `work_cmd.run_work_begin`, change the `except ValueError:` fallback (`plan_rel = str(plan_path)`) to `plan_rel = plan_path.resolve().as_posix()` so the out-of-root lease value is an absolute POSIX path on every platform, matching the in-root branch's `.replace("\\", "/")` normalization. Leave the in-root branch and the `aw commit` fallback (`plan_rel = plan_path.name`, which feeds `_in_scope`/commit-message derivation, not a lease) unchanged.
  - Depends on: none
  - Expected outcome: `git diff agent_workflows/work_cmd.py` shows only the fallback line changed inside `run_work_begin`.
  - Execution state: performed

### Task group 2: Regression tests

- [x] E-02 Create `tests/test_work_begin_plan_path_outside_root.py` with a test that, in a temp git repo with temp `HOME`/`AW_HOME` and `AW_NO_REEXEC=1`, installs the preset, scaffolds a child plan (`aw ipd scaffold --kind child --title ... --set ... --order 1 --priority low --work-kind chore --apply`), runs `aw ipd dependencies set <id6> none`, runs `python -m agent_workflows.cli work begin <id6>` as a subprocess, and asserts: exit code 0; stdout+stderr contain no `ValueError`/`Traceback`; the lease at `<AW_HOME>/projects/<project_id>/state/work/<id6>/work-lease.json` (`project_id` from `resolve_project_context(...).project_id`, as the mirrored test does) exists and parses as JSON, its `plan_path` is absolute, contains no backslash, `Path(plan_path).resolve()` equals the scaffolded plan's resolved path under `<AW_HOME>/projects/<project_id>/records/plans/pending/`, and `plan_id` equals the id6. Run it for BOTH clean-delta presets the bug names, `completely-clean-target` and `local-only` (one test per preset, or `subTest`), since both route records to `AW_HOME` (`project_schema` preset placements). Mirror the setup of `tests/test_clean_target_zero_delta_e2e.py` (`TestCleanTargetZeroDeltaE2E.setUp`).
  - Depends on: E-01
  - Expected outcome: the new test passes against the fixed code.
  - Execution state: performed
- [x] E-03 In the same module add an in-root counterpart: a temp repo installed with no `--preset` (`install . -y --no-interactive`, the tracked-records default), plan scaffolded under `<repo>/.aw/records/plans/pending/`, `work begin <id6>` exits 0, and the lease at `<repo>/.aw/state/work/<id6>/work-lease.json` has `plan_path` equal to the repo-relative POSIX path `.aw/records/plans/pending/<file>` (not absolute), and no `work-lease.json` exists under `AW_HOME`. (Measured at review HEAD `01cee44b9` in a `/tmp` scratch: lease at that path, `"plan_path": ".aw/records/plans/pending/20261016-qset-01-5jlb52-p-two.ipd.md"`.)
  - Depends on: E-02
  - Expected outcome: the in-root test passes, proving the guard did not regress the relative form.
  - Execution state: performed
- [x] E-04 Mutation proof (TEMPORARY, MUST NOT be committed): replace the try/except in `run_work_begin` with the pre-fix `plan_rel = str(plan_path.relative_to(repo_root))`, run the new module and capture the failure of the out-of-root tests (both presets) while the in-root test still passes, then restore the E-01 code with `git diff` confirming only E-01's change remains. Note honestly: on POSIX `str(plan_path)` already contains no backslash, so the no-backslash assertion cannot distinguish E-01 from the `3d80673c1` fallback on Linux; the mutation proof targets the guard itself, not E-01's normalization.
  - Depends on: E-03
  - Expected outcome: out-of-root tests fail on the reverted code with `ValueError` in the captured output; in-root test passes on it; all pass on the restored code; `git diff agent_workflows/work_cmd.py` again shows only E-01.
  - Execution state: performed
- [x] E-05 Add the CHANGELOG bullet and run the final regression gates.
  - Depends on: E-04
  - Expected outcome: `CHANGELOG.md` gains, under `## 2.0.0 (pending)`, the line "- Fixed: `aw work begin` no longer crashes on clean-delta installs (`completely-clean-target`, `local-only`) whose plans live outside the repository." (matching the file's `- Fixed:` style; no em or en dashes, user-facing prose). `python3 -m pytest -o addopts="" -q tests/test_work_begin_plan_path_outside_root.py tests/test_clean_target_zero_delta_e2e.py tests/test_work_gate_severity.py` passes, and bare `python3 -m pytest` shows zero failures that do not also fail at the execution base commit (compare by test name; re-derive at execution, not from a count recorded here). The new module is not in `pyproject.toml` `testpaths`, so the bare gate does not run it; the narrowed run above is what covers it.
  - Execution state: performed

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

Reproduced at review HEAD `01cee44b9` (scratch under `/tmp`, temp `HOME`/`AW_HOME`): `work begin` exited 0 for `completely-clean-target` and `local-only`, each lease at `<AW_HOME>/projects/<id>/state/work/<id6>/work-lease.json` carrying an absolute `plan_path` under `<AW_HOME>/projects/<id>/records/plans/pending/`; in-root default install wrote `<repo>/.aw/state/work/<id6>/work-lease.json` with the relative path. `Path('/a/...').relative_to(Path('/b/repo'))` raises `ValueError` (Python 3.14 message: `is not in the subpath of`).

Baseline observed during authoring: `python3 -m pytest -o addopts="" -q tests/test_clean_target_zero_delta_e2e.py -x` -> `2 passed in 19.65s`.

## Proposed changes (ordered, validatable)

1. E-01: POSIX-normalize the out-of-root fallback in `work_cmd.run_work_begin`.
2. E-02/E-03: new behavioral test module covering out-of-root and in-root lease `plan_path`.
3. E-04: temporary mutation proof.
4. E-05: CHANGELOG bullet and final regression gates.

## Deferred / out of scope (with reason)

None. (No outstanding obligation is deferred: `aw commit` already guards its own relativization with `plan_rel = plan_path.name` and is exercised end to end by `tests/test_clean_target_zero_delta_e2e.py`, and no consumer of the lease needs a schema change.)

## Scope check

- Over-scope: none.
- Under-scope: none; the crash path (both clean-delta presets), its fallback form, and both branches of the guard are each covered by an E-item.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_work_begin_plan_path_outside_root.py` passes (E-02, E-03).
- `python3 -m pytest -o addopts="" -q tests/test_clean_target_zero_delta_e2e.py` still passes.
- Mutation proof shows the out-of-root tests fail without the guard (E-04).
- `tests/test_work_gate_severity.py` (existing `work begin` lease tests) still passes; routine gate `python3 -m pytest` shows no new failures versus the execution base (E-05).

## Spec / documentation sync

CHANGELOG bullet (E-05). No spec change: no spec describes the lease `plan_path` field's form, and behavior visible to users (the verb succeeding) is already what the clean-target spec promises.

## Open questions

### OQ-01: Should the out-of-root lease plan_path be absolute or just the file name?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Absolute. The committed fix (`3d80673c1`) already chose `str(plan_path)` (absolute) for `work begin`; an absolute path uniquely locates the plan under `AW_HOME`, whereas a bare name does not. E-01 only normalizes separators.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted `git diff agent_workflows/work_cmd.py` showing only the `except ValueError:` fallback in `run_work_begin` changed to `plan_path.resolve().as_posix()`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/work_cmd.py b/agent_workflows/work_cmd.py
index 60258455e..5f46f5996 100644
--- a/agent_workflows/work_cmd.py
+++ b/agent_workflows/work_cmd.py
@@ -366,7 +366,7 @@ def run_work_begin(args: argparse.Namespace) -> int:
     try:
         plan_rel = str(plan_path.relative_to(repo_root)).replace("\\", "/")
     except ValueError:
-        plan_rel = str(plan_path)
+        plan_rel = plan_path.resolve().as_posix()

     lease = {
         "plan_id": plan_id,
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted actual pytest output of `python3 -m pytest -o addopts="" -v tests/test_work_begin_plan_path_outside_root.py` showing the out-of-root test PASSED for both `completely-clean-target` and `local-only`, plus the observed lease JSON `plan_path` value (produced by the `aw work begin` subprocess the test drives via `work_cmd.run_work_begin`).
  - Observed evidence:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <PYTHON>
cachedir: .pytest_cache
Using --randomly-seed=1825542077
rootdir: .
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 3 items

tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_local_only PASSED [ 33%]
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_completely_clean_target PASSED [ 66%]
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_in_root_tracked_records PASSED [100%]

============================== 3 passed in 17.47s ==============================
```
Observed lease JSON `plan_path` values:
- `completely-clean-target`: `<AW_HOME>/projects/repo-45a2a8/records/plans/pending/20261017-regset-01-ou6hli-regression-probe-plan-completely-clean-target.ipd.md` (absolute POSIX path, no backslashes, resolves to plan file)
- `local-only`: `<AW_HOME>/projects/repo-1f8a00/records/plans/pending/20261017-regset-01-l01bh0-regression-probe-plan-local-only.ipd.md` (absolute POSIX path, no backslashes, resolves to plan file)
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: same pytest output showing the in-root test PASSED, with the observed relative `plan_path` value pasted.
  - Observed evidence:
```
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_in_root_tracked_records PASSED [100%]
```
Observed lease JSON `plan_path` value:
- `tracked-records`: `.aw/records/plans/pending/20261017-inrootset-01-874jo9-in-root-probe-plan.ipd.md` (relative POSIX path matching `.aw/records/plans/pending/<file>`, no lease under AW_HOME)
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted pytest output from the reverted-code run showing the out-of-root test(s) FAILED with `ValueError` in the captured subprocess output and the in-root test PASSED, pasted passing output after restore, and `git diff agent_workflows/work_cmd.py` showing only E-01's change remains.
  - Observed evidence: Reverted code failed with ValueError on out-of-root presets while in-root passed; all passed on restored code.
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <PYTHON>
cachedir: .pytest_cache
Using --randomly-seed=3827819373
rootdir: .
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 3 items

tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_completely_clean_target FAILED [ 33%]
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_in_root_tracked_records PASSED [ 66%]
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_local_only FAILED [100%]

=================================== FAILURES ===================================
_ TestWorkBeginPlanPathOutsideRoot.test_plan_path_outside_root_completely_clean_target _
...
ValueError: '<AW_HOME>/projects/repo-b2bd84/records/plans/pending/20261017-regset-01-tu0ii3-regression-probe-plan-completely-clean-target.ipd.md' is not in the subpath of '<REPO>'
___ TestWorkBeginPlanPathOutsideRoot.test_plan_path_outside_root_local_only ____
...
ValueError: '<AW_HOME>/projects/repo-2a1c71/records/plans/pending/20261017-regset-01-6690sa-regression-probe-plan-local-only.ipd.md' is not in the subpath of '<REPO>'
=========================== short test summary info ============================
FAILED tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_completely_clean_target
FAILED tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_local_only
========================= 2 failed, 1 passed in 25.30s =========================
```
Restored-code passing output:
```
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_local_only PASSED [ 33%]
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_in_root_tracked_records PASSED [ 66%]
tests/test_work_begin_plan_path_outside_root.py::TestWorkBeginPlanPathOutsideRoot::test_plan_path_outside_root_completely_clean_target PASSED [100%]
============================== 3 passed in 28.05s ==============================
```
Restored git diff shows only E-01:
```diff
diff --git a/agent_workflows/work_cmd.py b/agent_workflows/work_cmd.py
index 60258455e..5f46f5996 100644
--- a/agent_workflows/work_cmd.py
+++ b/agent_workflows/work_cmd.py
@@ -366,7 +366,7 @@ def run_work_begin(args: argparse.Namespace) -> int:
     try:
         plan_rel = str(plan_path.relative_to(repo_root)).replace("\\", "/")
     except ValueError:
-        plan_rel = str(plan_path)
+        plan_rel = plan_path.resolve().as_posix()

     lease = {
         "plan_id": plan_id,
```
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: the `git diff CHANGELOG.md` hunk, a dash scan of the added line showing no U+2014/U+2013, the pasted summary line of the narrowed pytest run, and the bare `python3 -m pytest` summary line with any failing names compared against the same names at the execution base commit.
  - Observed evidence: CHANGELOG.md updated without em/en dashes; narrowed and bare pytest runs passed with 0 test failures.
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index 5b43b4da4..0faacce70 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: `aw work begin` no longer crashes on clean-delta installs (`completely-clean-target`, `local-only`) whose plans live outside the repository.
 - Fixed: Commands acting on a record stored in a companion records repository now find the owning repository, so plan dependency checks, spec history, id6 collision checks, and rename hints work there.
 - Fixed: `aw install` no longer leaves two project configs when switching between `private-target` and `completely-clean-target`/`local-only`. It refuses by default and `--relocate` (with `--dry-run` preview, `--relocate-resume`, `--relocate-rollback`) moves config, records and install history and retires the old files, and companion switches still refuse.
 - Fixed: `aw runs decisions` and `aw runs questions` now emit a JSON object under `--agent` and `--json`, and `aw runs evidence`, `aw runs verify-ledger` and `aw runs show` report the ledger as a repository-relative path.
```
```
Dash scan check on added line:
Has em dash (U+2014): False, Has en dash (U+2013): False

Narrowed pytest run summary line:
19 passed in 53.84s

Bare python3 -m pytest summary line:
748 passed in 87.20s (0:01:27) (zero failed tests; wall time budget advisory on core tier)
Failing test names: None (0 failing tests).
```
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Do not execute until `- Status: approved`. Execute in an isolated worktree (`aw work begin t1fri2`, or under `aw oc run`, which isolates by default), in order E-01..E-05. Mark an `E-*` performed only after doing it and a `V-*` pass only with concrete pasted evidence; paste the ACTUAL runner output. Every probe uses a temp git repo with temp `HOME`/`AW_HOME`; never install into this repository or touch the real home. The E-04 mutation is temporary and MUST NOT be committed. Commit through `aw commit t1fri2 -- <paths>`; never `git add -A`, never push, never `--no-verify`.

SCOPE FENCE. `- Scope-Paths:` is a declaration reconciled at finalize; an out-of-scope edit that proves necessary is made and justified with `--scope-reason`, and a declared path left unmodified is acknowledged with `--scope-ack`.

POST-GATE LIFECYCLE. Once every `E-*` is performed, every `V-*` is pass, and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize t1fri2`. This plan inherits `- Blocks-Release: next` from backlog `707qi4`.
