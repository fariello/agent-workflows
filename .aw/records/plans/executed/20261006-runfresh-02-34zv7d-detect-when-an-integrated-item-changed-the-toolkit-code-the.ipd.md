# IPD: Detect when an integrated item changed the toolkit code the runner is running

- Date: 2026-10-06
- Kind: child
- Concern: Nothing records which toolkit code a driver loaded, so nothing can tell that the code on disk has moved past it. `initialize_run_core` writes a `driver` record with the driver module's own path and digest (`runner_shared.sha256_file(driver_path)`), which covers one file, not the package, and is never compared again. On run `run-20261006T134924Z-332833` eighteen `agent_workflows/*.py` files changed under the driver (`git diff --name-only 3f4763b56 f723865c6 -- agent_workflows` lists 18, including `ipd_lint.py` and `ipd_schema.py`) and the driver could not have known. Spec `25kzda` 5.3b points 1 and 6 (added by Order 01) require a loaded-code record at run start and a classification of whether a restart could pick up new code.
- Scope: IN: a new module `agent_workflows/loaded_code.py` with (a) `fingerprint(root)`: a sha256 over the sorted relative paths and contents of every `agent_workflows/**/*.py` under `root`; (b) `loaded_code_record()`: the package root the CURRENT process imported `agent_workflows` from (`runner_shared.runner_package_root()`), its fingerprint, the time, and whether that root is the checkout the run targets; (c) `code_changed(repo)`: compares the record of the CURRENT process (kept in process memory, set when the process first called `loaded_code_record` or `code_changed`) with the fingerprint of the same root on disk now, returning `changed`, the old and new fingerprints, and a `restartable` flag that is False when the imported root is not the run's repository; writing the start record into `state["driver"]["loaded_code"]` (a list, first entry at creation) in `initialize_run_core`; a test file. OUT: acting on a change (Order 03); recording lint findings (Order 04).
- Scope-Paths: agent_workflows/loaded_code.py, agent_workflows/runner_shared.py, tests/test_loaded_code.py, tests/test_oc_runipd.py
- Item-Dependencies: executed:0bjke0
- Status: executed
- Readiness: go-pending-approval
- From-Spec: none
- Work-Kind: bug
- Priority: high
- Blocks-Release: f33nrj
- Set: runfresh
- Order: 2
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 34zv7d

## Workflow history
- 2026-10-08 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 34zv7d verified (set runfresh, attempt 1). [Scope reconciliation - widened-scope tests/test_oc_runipd.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-10-07 approved (aw set): status set to approved
- 2026-10-07 reviewed (aw set): plan-review: APPROVE WITH REVISIONS APPLIED

- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-06 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): Authored as Order 02 of Set `runfresh`. Implements spec `25kzda` 5.3b points 1 and 6 and the A.2 driver-record sentence, as amended by Order 01. Detection only.

## Goal

Give the runner one reliable answer to "has the toolkit code I am running changed on disk since this process loaded it, and would a restart pick the change up?", and record the code each run started on.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the detector

- [x] E-01 Add `agent_workflows/loaded_code.py` with `fingerprint(root: Path) -> str` and a companion per-file digest map, hashing, in sorted order of their POSIX paths relative to `root`, each `agent_workflows/**/*.py` file (excluding `__pycache__`) as a sha256 of its bytes, then the fingerprint as a sha256 over the sorted `<relpath>\0<file digest>\n` lines, so path and content boundaries cannot collide. Add `loaded_code_record(repo: Path | None, *, package_root: Path | None = None) -> dict` returning `{"package_root", "fingerprint", "recorded_at", "is_target_checkout"}`, where `package_root` defaults to `runner_shared.runner_package_root()` (imported inside the function; the keyword exists so tests can point it at a fixture tree and never edit the real package). MEMOIZE ONLY WHAT THE PROCESS LOADED: the first call in a process stores `package_root`, `fingerprint`, the per-file map and `recorded_at` in a module-level variable keyed by `package_root`, and later calls reuse them unchanged; `is_target_checkout` (realpath of `package_root` equals realpath of `repo`) is computed on EVERY call from the `repo` passed, because one process (a test worker) may initialize runs for many repositories. Add `_reset_for_tests()` clearing the memo.
  - Depends on: none
  - Expected outcome: two calls in one process return the same fingerprint even if a file changes in between; two calls with different `repo` values return their own `is_target_checkout`; `fingerprint` changes when any `agent_workflows/**/*.py` byte changes (including a subpackage such as `agent_workflows/hooks/`) and does not change when a non-`.py` file or a `__pycache__` file changes.
  - Execution state: performed

- [x] E-02 Add `code_changed(repo: Path, *, package_root: Path | None = None) -> CodeChange` (when no record is memoized yet, as in a process started by `resume`, which never calls `initialize_run_core`, it first establishes one via `loaded_code_record`, so a resumed process compares against the code IT loaded and reports `changed=False` on its first call) returning a named result with `changed` (stored fingerprint differs from `fingerprint(package_root)` now), `old`, `new`, `restartable` (`is_target_checkout`), and `changed_files` (paths whose bytes differ, computed by keeping a per-file digest map alongside the fingerprint so the result can name what moved, capped at 50 names). It must be fast enough to call between every item: measure it on this repository and record the time (a review-time probe hashed the 188 `agent_workflows/**/*.py` files in about 0.1s cold; context only, re-measure).
  - Depends on: E-01
  - Expected outcome: after editing one `.py` file under the root, `code_changed` reports `changed=True` and names that file; with no edit, `changed=False`; with `repo` different from the package root, `restartable=False`; a first call with no memoized record returns `changed=False`; a warm call on this repository takes well under one second (measured and recorded).
  - Execution state: performed

### Task group 2: record it

- [x] E-03 In `runner_shared.initialize_run_core`, add `state["driver"]["loaded_code"] = [loaded_code_record(repo)]` beside the existing `id`/`path`/`sha256` fields (spec `25kzda` 5.3, A.2). Leave the existing driver fields unchanged. When `is_target_checkout` is False, append one `driver-restart-unavailable` event naming the imported root and the target repository, so the operator sees once that this run will not restart.
  - Depends on: E-02
  - Expected outcome: a new run's `state.json` carries `driver.loaded_code` with one entry; a run started from a non-target package also has one `driver-restart-unavailable` event.
  - Execution state: performed

### Task group 3: pin it

- [x] E-04 Add `tests/test_loaded_code.py` building a fixture package tree under `tempfile` and passing it as `package_root` (never editing the real package), calling `_reset_for_tests()` in `setUp`: fingerprint stability and sensitivity cases from E-01; `code_changed` cases from E-02 (one edited file named, no edit, non-target root, first call with no record); the first-call memoization case and the per-call `is_target_checkout` case; and an `initialize_run` case (the existing in-process pattern; the fixture repository is never the package root, so this run is the non-target case) asserting the `loaded_code` record and exactly one `driver-restart-unavailable` event. Prove the tests can fail by making `fingerprint` ignore file contents and pasting the failure.
  - Depends on: E-03
  - Expected outcome: the new file passes; the mutation fails it; no test reads production source.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `runner_shared` HAS A PINNED MODULE-LEVEL FIRST-PARTY IMPORT SET; the call into `loaded_code` from `initialize_run_core` must be a function-local import.
- EVERY EXISTING `initialize_run` TEST BECOMES A NON-TARGET RUN, because its fixture repository is never the package root, so each gains one `driver-restart-unavailable` event and one fingerprint computation (memoized per process). No current test asserts an exact `state["driver"]` key set or an exact event list from run creation (review-time grep), but the bare suite at E-04 is the check.
- `runner_shared.runner_package_root()` is the existing definition of "where this process's toolkit came from", used by `pinned_child_env`; reuse it rather than re-deriving.
- `checkout_pin.find_toolkit_checkout` already decides whether a directory is a toolkit checkout; `is_target_checkout` compares realpaths of the imported root and the run's repository instead, because the question here is "is the code I would reload the code the run is changing".
- Tests assert behavior, never code structure (`GUIDING_PRINCIPLES.md` P16).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The existing driver record covers one file. `initialize_run_core` writes `"driver": {"id", "path", "sha256": sha256_file(driver_path)}` and nothing reads it back to compare. | the `"driver": {` block in `initialize_run_core` |
| F-02 | Eighteen package files changed under the 2026-10-06 run, so a single-module digest would have missed most of them, including `ipd_lint.py` and `ipd_schema.py`, the two whose change caused the refusal. | `git diff --name-only 3f4763b56 f723865c6 -- agent_workflows` |
| F-03 | `runner_package_root()` is `Path(__file__).resolve().parent.parent` of `runner_shared`, so it names the directory the driver actually imported from, whether a checkout or an installed copy. | `runner_package_root` |

## Proposed changes (ordered, validatable)

1. New `loaded_code` module: `fingerprint`, memoized `loaded_code_record` (E-01).
2. `code_changed` with named changed files and a measured cost (E-02).
3. Record at run start; announce once when restart is unavailable (E-03).
4. Tests and a mutation proof (E-04).

## Deferred / out of scope (with reason)

- RESTARTING. Order 03.
  - Carrier: re15ol
- WATCHING FILES IN THE BACKGROUND. A between-item comparison is sufficient because a restart only happens between items.
  - Carrier-Declined: no need measured; a between-item check is cheaper and simpler

## Scope check

- Over-scope: none. One new module, one wiring edit in `runner_shared`, one test file.
- Under-scope: none; acting on the result is Order 03.

## Required tests / validation

- Baseline bare `python3 -m pytest` before editing.
- `python3 -m pytest -o addopts="" tests/test_loaded_code.py tests/test_runner_shared.py tests/test_hostdedup_third_host.py -q` pasted.
- The E-02 timing on this repository pasted (cold and warm).
- Mutation run pasted.
- Bare `python3 -m pytest` after, reconciled; `aw ipd lint` conforming; `aw sanitize --agent` clean.

## Spec / documentation sync

Implements spec `25kzda` 5.3b points 1 and 6 and the 5.3 driver-record sentence (A.2), as amended by Order 01. No spec edited here.

## Open questions

### OQ-01: Should the fingerprint cover only `.py` files?

- Blocking: no
- Status: resolved
- Owner: author
- Resolution or deferral rationale: RESOLVED: yes. Only Python modules are held in memory from import; workflow markdown, templates and JSON are read from disk when used, so they are never outdated in a running process. Including them would trigger restarts that change nothing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the new module's functions and the test output for: unchanged repeat call, a `.py` edit (top-level and in a subpackage) changing the fingerprint, a `.md` and a `__pycache__` edit not changing it, memoization across an edit, and per-call `is_target_checkout` for two different `repo` values.
  - Observed evidence:
    Functions in `agent_workflows/loaded_code.py`:
    - `file_digests(root: Path | str) -> dict[str, str]`
    - `fingerprint_from_digests(digests: dict[str, str]) -> str`
    - `fingerprint(root: Path | str) -> str`
    - `loaded_code_record(repo: Path | str | None, *, package_root: Path | str | None = None) -> dict[str, Any]`
    - `code_changed(repo: Path | str, *, package_root: Path | str | None = None) -> CodeChange`
    - `_reset_for_tests() -> None`

    Test output (`python3 -m pytest -o addopts="" tests/test_loaded_code.py -k "Fingerprint or LoadedCodeRecord" -v`):
    ```
    tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_insensitivity_pycache PASSED [ 14%]
    tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_sensitivity_subpackage_py_change PASSED [ 28%]
    tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_stability_unchanged_repeat_call PASSED [ 42%]
    tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_sensitivity_top_level_py_change PASSED [ 57%]
    tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_insensitivity_non_py_files PASSED [ 71%]
    tests/test_loaded_code.py::LoadedCodeRecordTests::test_per_call_is_target_checkout PASSED [ 85%]
    tests/test_loaded_code.py::LoadedCodeRecordTests::test_first_call_memoization_across_file_edit PASSED [100%]
    ======================= 7 passed, 5 deselected in 0.55s ========================
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the test output for the four `code_changed` cases (edited file named, no edit, non-target root `restartable=False`, first call with no record `changed=False`) and the measured cold and warm timings on this repository.
  - Observed evidence:
    Test output (`python3 -m pytest -o addopts="" tests/test_loaded_code.py -k "CodeChanged" -v`):
    ```
    tests/test_loaded_code.py::CodeChangedTests::test_code_changed_no_edit PASSED [ 25%]
    tests/test_loaded_code.py::CodeChangedTests::test_code_changed_first_call_when_no_memo PASSED [ 50%]
    tests/test_loaded_code.py::CodeChangedTests::test_code_changed_non_target_root_not_restartable PASSED [ 75%]
    tests/test_loaded_code.py::CodeChangedTests::test_code_changed_with_file_edit_names_changed_file PASSED [100%]
    ======================= 4 passed, 8 deselected in 0.54s ========================
    ```

    Repository timings measured on 189 `agent_workflows/**/*.py` files:
    Cold timing: 0.5205s
    Warm timing (avg of 10 runs): 0.1715s (min: 0.0796s, max: 0.2203s)
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `initialize_run_core` diff and, from the test, the `driver.loaded_code` record in `state.json` and the `driver-restart-unavailable` event for the non-target case.
  - Observed evidence:
    `initialize_run_core` diff:
    ```diff
    @@ -30140,6 +30140,10 @@ def initialize_run_core(
             caps = _hsp.HostSandboxCapabilities()
             caps.probe_notes["initialization_probe_error"] = f"{type(exc).__name__}: {exc}"

    +    from agent_workflows.loaded_code import loaded_code_record
    +
    +    loaded_code_rec = loaded_code_record(repo)
    +
         state = {
             "schema_version": SCHEMA_VERSION,
             "run_id": run_id,
    @@ -30209,6 +30213,7 @@ def initialize_run_core(
                     if (driver_path is not None and Path(driver_path).is_file())
                     else None
                 ),
    +            "loaded_code": [loaded_code_rec],
             },
         }
         atomic_write_json(run_dir / "state.json", state)
    @@ -30216,6 +30221,17 @@ def initialize_run_core(
             run_dir / "events.jsonl",
             {"at": utc_now(), "event": "run-created", "run_id": run_id, "queue": queue_ids},
         )
    +    if not loaded_code_rec.get("is_target_checkout", False):
    +        append_jsonl(
    +            run_dir / "events.jsonl",
    +            {
    +                "at": utc_now(),
    +                "event": "driver-restart-unavailable",
    +                "reason": "non-target-checkout",
    +                "package_root": str(loaded_code_rec.get("package_root", "")),
    +                "repo": str(repo),
    +            },
    +        )
    ```

    From test execution on non-target repo:
    `driver.loaded_code`:
    ```json
    [
      {
        "fingerprint": "13b311950f2eb8387da0181fb1b784af7407aa50768f870b47e4326d16a7ca7e",
        "is_target_checkout": false,
        "package_root": "<repo-root>",
        "recorded_at": "2026-10-08T07:17:09+00:00"
      }
    ]
    ```

    `driver-restart-unavailable` event in `events.jsonl`:
    ```json
    [
      {
        "at": "2026-10-08T07:17:09+00:00",
        "event": "driver-restart-unavailable",
        "package_root": "<repo-root>",
        "reason": "non-target-checkout",
        "repo": "/tmp/tmpsqyt6xj9"
      }
    ]
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the new test file passing with its count; the mutation failing and the revert passing; a grep for source-structure reads returning nothing. Paste the BARE `python3 -m pytest` summary reconciled against your baseline, `aw ipd lint` conforming, `aw sanitize --agent`, and `git diff --cached --name-only` listing only declared paths.
  - Observed evidence:
    1. New test file passing:
    ```
    $ python3 -m pytest -o addopts="" tests/test_loaded_code.py -q
    ............                                                             [100%]
    12 passed in 3.63s
    ```
    2. Targeted suite:
    ```
    $ python3 -m pytest -o addopts="" tests/test_loaded_code.py tests/test_runner_shared.py tests/test_hostdedup_third_host.py -q
    164 passed in 81.32s (0:01:21)
    ```
    3. Mutation test (hardcoding static digest in file_digests):
    ```
    FAILED tests/test_loaded_code.py::CodeChangedTests::test_code_changed_with_file_edit_names_changed_file
    FAILED tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_sensitivity_subpackage_py_change
    FAILED tests/test_loaded_code.py::FingerprintBehavioralTests::test_fingerprint_sensitivity_top_level_py_change
    ========================= 3 failed, 9 passed in 3.45s ==========================
    ```
    After revert:
    ```
    12 passed in 3.63s
    ```
    4. Grep for source-structure reads:
    `grep -En "inspect|ast" tests/test_loaded_code.py` -> exit 1, 0 matches.
    5. Bare `python3 -m pytest` full suite:
    Baseline: `6656 passed, 2 skipped, 3 warnings in 559.82s (0:09:19)`
    Reconciled: `6668 passed, 2 skipped, 3 warnings in 471.32s (0:07:51)`
    Delta: +12 passed, 0 failed, 0 regressions.
    6. `aw ipd lint`: conforming.
    7. `aw sanitize --agent`: clean.
    8. Staged paths: only declared Scope-Paths.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval. Commit only declared paths through `aw commit <plan> -- <paths>`; never push. Paste actual output. Under a runner, the runner owns begin/finalize; by hand, use `aw ipd finalize`.
