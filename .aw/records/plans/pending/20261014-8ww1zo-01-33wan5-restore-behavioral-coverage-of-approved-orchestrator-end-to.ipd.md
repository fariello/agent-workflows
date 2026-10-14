# IPD: Restore behavioral coverage of approved-orchestrator end-to-end derivation and legacy manifest kind fallback on both hosts

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_rununify_record.py`, and with it the only behavioral tests that (a) an APPROVED ORCHESTRATOR derives `orchestrate` end to end through `discover_plans` -> `build_dynamic_manifest` -> `action_for` on BOTH hosts, and (b) a LEGACY hand-written manifest that omits the `kind` key still derives `orchestrate` on both hosts via `runner_shared.resolve_manifest_kind` / `plan_kind_from_file`. Executed plans `yuhl6o` (S-04, S-05) and `9rthek` (S-11) recorded those sites as RETIRE-UNGUARDED. A regression here is silent: an approved orchestrator would be agent-executed (a paid turn on a plan that authors no code), the defect `pgq326` fixed.
- Scope: Add one new behavioral test module exercising the real functions and the real queue build on both hosts, and repoint the three source comments that currently say "no live guard currently asserts this" at the new module. No production behavior change.
- Scope-Paths: tests/test_orchestrator_kind_derivation.py, agent_workflows/runner_shared.py, agent_workflows/agy_runipd.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: low
- From-Backlog: 8ww1zo
- Set: 8ww1zo
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 33wan5

## Workflow history

- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog `8ww1zo`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) test coverage for the two properties lost with `tests/test_rununify_record.py`: approved-orchestrator `orchestrate` derivation end to end on both hosts, and the legacy-manifest `kind` fallback on both hosts, including through the real `initialize_run` queue build with a `--manifest` that omits `kind`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: end-to-end derivation from a real plan tree (yuhl6o S-04, S-05)

- [ ] E-01 Create `tests/test_orchestrator_kind_derivation.py` with a fixture helper that writes synthetic plan files (one `- Kind: orchestrator` Order 0, one `- Kind: child` Order 1, both `- Status: approved`) under a temp `.aw/records/plans/pending/`, and a test class that, for each host module in (`oc_runipd`, `agy_runipd`), calls `discover_plans(root)` -> `build_dynamic_manifest(root, found)` -> `action_for(entry["kind"], entry["status"])` and asserts `orchestrate` for the orchestrator and `execute` for the child, plus asserts both hosts produce equal manifests for the same tree.
  - Depends on: none
  - Expected outcome: New module exists; the end-to-end class passes on both hosts via `subTest(host=...)`.
  - Execution state: pending

### Task group 2: legacy manifest kind fallback (9rthek S-11)

- [ ] E-02 In the same module, add a test class for the legacy fallback that calls the real `resolve_manifest_kind` on each host with a manifest entry that OMITS `kind` (asserting the fixture omits it) pointing at the real orchestrator plan file, and asserts `action_for(kind, "approved") == "orchestrate"` (action first, then `kind == "orchestrator"`); a test that an entry WITH `kind: "child"` returns `child` given a nonexistent path (no file read needed); a test that a missing file yields `plan_kind_from_file(...) is None` and `action_for(resolve_manifest_kind({}, missing), "approved") == "execute"` (safe direction); and a test that both hosts resolve the orchestrator and child entries identically.
  - Depends on: E-01
  - Expected outcome: Fallback class passes on both hosts.
  - Execution state: pending

- [ ] E-03 In the same module, add a queue-build test that, for each host, creates a temp git repo with an approved orchestrator plan (and its executed child, plus a coverage record via `coverage_record.write` as `tests/test_orchestrator_retirement.py` `TheActionDecisionIsSHAREDCode` does), writes a hand-written manifest JSON with `schema_version` 1 and plan entries carrying `set`, `file`, `dependencies` but NO `kind`, invokes the host's real `initialize_run` with `manifest=<that path>` and `prepare_only=True`, and asserts the orchestrator's `state.json` queue entry has `action == "orchestrate"` and `kind == "orchestrator"`.
  - Depends on: E-02
  - Expected outcome: Legacy-manifest queue build derives `orchestrate` on both hosts through `runner_shared.initialize_run_core`.
  - Execution state: pending

### Task group 3: non-vacuity and comment repointing

- [ ] E-04 Add a non-vacuity control in the module that, in-process and without editing shipped source, substitutes a pass-through resolver (`lambda entry, _p: entry.get("kind")`) for the legacy entry and asserts `runner_shared.action_for(None, "approved") == "execute"`, proving the E-02/E-03 assertions would fail if the fallback were removed. Do not read source files, use `ast`/`inspect`, or pin symbol identity/counts.
  - Depends on: E-02
  - Expected outcome: Control passes, showing the derivation flips without the fallback.
  - Execution state: pending

- [ ] E-05 Repoint the three comment sites that say the guard was deleted and "no live guard currently asserts" this (in `runner_shared.py` near the `PlanRecord` section banner "THE FAILURE MODE HERE IS SILENT AND TYPE-SHAPED", in the `PlanRecord` docstring "DO NOT DROP `kind`", and in `agy_runipd.py` after "`_plan_kind` HAD TWO CALLERS") so they name `tests/test_orchestrator_kind_derivation.py` as the live guard. Comment-only edits.
  - Depends on: E-03
  - Expected outcome: `rg -n "no live guard currently asserts" agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` returns no matches for these three sites; no code change.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Tests must exercise behavior (P16, AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): the deleted file's `ThereIsExactlyOneRecordAndOneReader` repo-wide AST scan, the `_top_level_definitions` helper, its identity assertions, and `control_C` are source-structure pins and are deliberately NOT restored.
- Both hosts must be covered in every assertion: existing pattern `_dispatch_hosts()` in `tests/test_orchestrator_retirement.py` and `HOSTS` in the deleted file.
- The fallback lives in `runner_shared.plan_kind_from_file` and `runner_shared.resolve_manifest_kind`, re-exported by `oc_runipd` and `agy_runipd`; it is consumed in `runner_shared.initialize_run_core` at the queue-build site (`kind = resolve_manifest_kind(plan, p_path)`) and in the legality preflight.
- `initialize_run_core` takes the manifest from `args.manifest` (`load_json` + `validate_manifest`) when supplied, otherwise builds it dynamically; so a `--manifest` without `kind` is a real, reachable path.
- The shipped `tools/ipdrunner/20260823-pending-ipds-driver-manifest.json` carries no `kind` keys, confirming the legacy shape is real.
- Suite is run bare: `python3 -m pytest`.

## Findings

| Site | Lost test (in `19313eed^:tests/test_rununify_record.py`) | Live coverage today |
|---|---|---|
| yuhl6o S-04/S-05 | `OrchestratorDetectionStillWorksEndToEnd.test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts` | Partial: `tests/test_orchestrator_retirement.py` `TheActionDecisionIsSHAREDCode` covers it on agy only via `discover_plans` and on both hosts only via dynamic-manifest `initialize_run`; `tests/test_runner_shared.py` checks `kind` for a child only. |
| 9rthek S-11 | `TheLegacyManifestFallbackWorksOnBothHosts.*` | None: `rg -n "resolve_manifest_kind\|plan_kind_from_file" tests/` returns no matches. |

## Proposed changes (ordered, validatable)

1. New `tests/test_orchestrator_kind_derivation.py` (E-01..E-04).
2. Comment repoint in `agent_workflows/runner_shared.py` and `agent_workflows/agy_runipd.py` (E-05).

## Deferred / out of scope (with reason)

- Restoring the AST/identity/single-definition pins from the deleted file: prohibited by P16.
- `test_the_shipped_hand_written_manifests_are_still_understood` (asserted the shipped manifest's shape): pins a data file rather than behavior; E-03 covers the real legacy path instead.

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; all three cited sites (S-04, S-05, S-11) get a behavioral guard.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_orchestrator_kind_derivation.py` passes.
- Non-vacuity: temporarily (in a scratch, uncommitted edit) make `runner_shared.resolve_manifest_kind` return `entry.get("kind")`; the E-02 and E-03 tests fail naming `execute` vs `orchestrate`; revert.
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus comment repointing; no spec describes these tests.

## Open questions

### OQ-01: Should the deleted structural pins also be restored?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The backlog item states "only behavioral outcomes may be restored, never a source-reading pin (P16)".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_orchestrator_kind_derivation.py -k EndToEnd` showing the orchestrator and child derivation tests passing with both `host=oc_runipd` and `host=agy_runipd` subtests (or per-host parametrized ids).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the legacy-fallback class tests passing; plus pasted output of the scratch non-vacuity run (resolver changed to `entry.get("kind")`) showing these tests FAIL with `execute` != `orchestrate`, then `git diff --stat agent_workflows/runner_shared.py` showing the scratch edit reverted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the legacy-manifest `initialize_run` test passing for both hosts; the observation is produced by `runner_shared.initialize_run_core` queue build (`resolve_manifest_kind(plan, p_path)`), created by E-03; and the same scratch non-vacuity run showing it FAIL.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Pasted pytest output showing the control test passing, and `rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_orchestrator_kind_derivation.py` returning no matches (no source reading).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted `git diff agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` showing only comment/docstring lines changed and naming `tests/test_orchestrator_kind_derivation.py`; pasted bare `python3 -m pytest` summary line showing the full suite passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). Commit only the Scope-Paths files through `aw commit <plan> -- <paths>`; never push. After every `V-*` item records pasted evidence with `Result: pass` and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through the tooled lifecycle (`aw ipd finalize`).
