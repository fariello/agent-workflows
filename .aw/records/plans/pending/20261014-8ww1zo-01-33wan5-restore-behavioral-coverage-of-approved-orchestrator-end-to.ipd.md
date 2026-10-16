# IPD: Restore behavioral coverage of approved-orchestrator end-to-end derivation and legacy manifest kind fallback on both hosts

- Date: 2026-10-14
- Kind: child
- Concern: Commit `19313eed` deleted `tests/test_rununify_record.py`, and with it the only behavioral tests that (a) an APPROVED ORCHESTRATOR derives `orchestrate` end to end through `discover_plans` -> `build_dynamic_manifest` -> `action_for` on BOTH hosts, and (b) a LEGACY hand-written manifest that omits the `kind` key still derives `orchestrate` on both hosts via `runner_shared.resolve_manifest_kind` / `plan_kind_from_file`. Executed plans `yuhl6o` (S-04, S-05) and `9rthek` (S-11) recorded those sites as RETIRE-UNGUARDED. A regression here is silent: an approved orchestrator would be agent-executed (a paid turn on a plan that authors no code), the defect `pgq326` fixed.
- Scope: Add one new behavioral test module exercising the real functions and the real queue build on both hosts, and repoint the three source comments that currently say "no live guard currently asserts this" at the new module. No production behavior change.
- Scope-Paths: tests/test_orchestrator_kind_derivation.py, agent_workflows/runner_shared.py, agent_workflows/agy_runipd.py, .aw/records/plans/pending/20261014-8ww1zo-01-33wan5-restore-behavioral-coverage-of-approved-orchestrator-end-to.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 8ww1zo
- Set: 8ww1zo
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: 33wan5
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved

- 2026-10-15 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): plan-review complete; PR-001..PR-006 fixed
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed (E-04 control made non-vacuous via mock-patched queue build, E-05/V-05 made checkable, execution contract added, E-03 manifest fixture specified, V-* bars re-based on behavior); review record `.aw/records/reviews/20261014-8ww1zo-01-33wan5-restore-behavioral-coverage-of-approved-orchestrator-end-to.review.md`.
- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog `8ww1zo`; review-ready.

## Goal

Restore behavioral (never source-reading, P16) test coverage for the two properties lost with `tests/test_rununify_record.py`: approved-orchestrator `orchestrate` derivation end to end on both hosts, and the legacy-manifest `kind` fallback on both hosts, including through the real `initialize_run` queue build with a `--manifest` that omits `kind`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: end-to-end derivation from a real plan tree (yuhl6o S-04, S-05)

- [x] E-01 Create `tests/test_orchestrator_kind_derivation.py` with a fixture helper that writes synthetic plan files (one `- Kind: orchestrator` Order 0, one `- Kind: child` Order 1, both `- Status: approved`) under a temp `.aw/records/plans/pending/`, and a test class named `ApprovedOrchestratorDerivesOrchestrateEndToEnd` that, for each host module in (`oc_runipd`, `agy_runipd`), calls `discover_plans(root)` -> `build_dynamic_manifest(root, found)` -> `action_for(entry["kind"], entry["status"])` and asserts `orchestrate` for the orchestrator and `execute` for the child, plus asserts both hosts produce equal manifests for the same tree.
  - Depends on: none
  - Expected outcome: New module exists; the end-to-end class passes on both hosts via `subTest(host=...)`.
  - Execution state: performed

### Task group 2: legacy manifest kind fallback (9rthek S-11)

- [x] E-02 In the same module, add a test class for the legacy fallback that calls the real `resolve_manifest_kind` on each host with a manifest entry that OMITS `kind` (asserting the fixture omits it) pointing at the real orchestrator plan file, and asserts `action_for(kind, "approved") == "orchestrate"` (action first, then `kind == "orchestrator"`); a test that an entry WITH `kind: "child"` returns `child` given a nonexistent path (no file read needed); a test that a missing file yields `plan_kind_from_file(...) is None` and `action_for(resolve_manifest_kind({}, missing), "approved") == "execute"` (safe direction); and a test that both hosts resolve the orchestrator and child entries identically. Name the class `LegacyManifestKindFallback`.
  - Depends on: E-01
  - Expected outcome: Fallback class passes on both hosts.
  - Execution state: performed

- [x] E-03 In the same module, add a queue-build test that, for each host, creates a temp git repo with an approved orchestrator plan (and its executed child, plus a coverage record via `coverage_record.write` as `tests/test_orchestrator_retirement.py` `TheActionDecisionIsSHAREDCode` does), writes a hand-written manifest JSON with `schema_version` equal to `runner_shared.SCHEMA_VERSION` and a plan entry carrying `set`, `file`, `dependencies` but NO `kind` (assert the written JSON omits the key), plus a `sets` entry ordering it, invokes the host's real `initialize_run` with an `argparse.Namespace` shaped like the one in `TheActionDecisionIsSHAREDCode` but `manifest=<that path>` and `prepare_only=True`, and asserts the orchestrator's `state.json` queue entry has `action == "orchestrate"` and `kind == "orchestrator"`. Factor the repo-plus-manifest fixture and the `initialize_run` call into a helper E-04 reuses.
  - Depends on: E-02
  - Expected outcome: Legacy-manifest queue build derives `orchestrate` on both hosts through `runner_shared.initialize_run_core`.
  - Execution state: performed

### Task group 3: non-vacuity and comment repointing

- [x] E-04 Add a non-vacuity control test that reruns the E-03 helper for each host under `unittest.mock.patch.object(runner_shared, "resolve_manifest_kind", lambda entry, _p: entry.get("kind"))` (in-process, no shipped-source edit) and asserts the orchestrator's queue entry then has `action == "execute"` and `kind is None`, proving the E-03 assertion depends on the fallback. Patching `runner_shared` reaches the queue build because `initialize_run_core` resolves the name from `runner_shared`'s globals. Do not read source files, use `ast`/`inspect`, or pin symbol identity/counts.
  - Depends on: E-03
  - Expected outcome: Control passes on both hosts (measured at review HEAD `eaafddbcb` with a one-off probe: unpatched `orchestrate`/`orchestrator`, patched `execute`/`None`, on both hosts).
  - Execution state: performed

- [x] E-05 Repoint the three comment sites that say the guard was deleted and "no live guard currently asserts" this (in `runner_shared.py` near the `PlanRecord` section banner "THE FAILURE MODE HERE IS SILENT AND TYPE-SHAPED", in the `PlanRecord` docstring "DO NOT DROP `kind`", and in `agy_runipd.py` after "`_plan_kind` HAD TWO CALLERS") so they name `tests/test_orchestrator_kind_derivation.py` as the live guard. Comment-only edits.
  - Depends on: E-03
  - Expected outcome: each of the three comments names `tests/test_orchestrator_kind_derivation.py` as the live guard and keeps the `19313eed` deletion history; other "no live guard" comments in these files (which describe unrelated deleted tests) are untouched; no code change. Note the `runner_shared.py` banner wraps the phrase across two lines ("no" / "live guard currently asserts this derivation"), so locate it by the banner text, not by a one-line grep.
  - Execution state: performed

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
  - Carrier-Declined: prohibited by P16 code-structure pinning rule
- `test_the_shipped_hand_written_manifests_are_still_understood` (asserted the shipped manifest's shape): pins a data file rather than behavior; E-03 covers the real legacy path instead.
  - Carrier-Declined: pins data file shape rather than behavior; legacy path covered in E-03

## Scope check

- Over-scope: none; no production logic changes.
- Under-scope: none; all three cited sites (S-04, S-05, S-11) get a behavioral guard.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_orchestrator_kind_derivation.py` passes.
- Non-vacuity, permanent: the E-04 mock-patched control test (in the suite).
- Non-vacuity, one-off: temporarily (in a scratch, uncommitted edit) make `runner_shared.resolve_manifest_kind` return `entry.get("kind")`; the orchestrator-fallback tests in E-02 and the E-03 test fail naming `execute` vs `orchestrate`; revert. (The E-02 explicit-kind and missing-file tests are expected to keep passing.)
- Full suite `python3 -m pytest` passes.

## Spec / documentation sync

N/A: test-only addition plus comment repointing; no spec describes these tests.

## Open questions

### OQ-01: Should the deleted structural pins also be restored?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. The backlog item states "only behavioral outcomes may be restored, never a source-reading pin (P16)".

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_orchestrator_kind_derivation.py` showing the test(s) pinning "an approved orchestrator derives `orchestrate` and an approved child `execute` through `discover_plans` -> `build_dynamic_manifest` -> `action_for`, identically on both hosts" PASSED with zero failed (the class name is a pointer, not the bar; the per-host loop must cover both `oc_runipd` and `agy_runipd`).
  - Observed evidence:
```
tests/test_orchestrator_kind_derivation.py::ApprovedOrchestratorDerivesOrchestrateEndToEnd::test_an_approved_orchestrator_derives_orchestrate_and_child_derives_execute_on_both_hosts PASSED [ 25%]
tests/test_orchestrator_kind_derivation.py::ApprovedOrchestratorDerivesOrchestrateEndToEnd::test_both_hosts_produce_equal_manifests_for_the_same_tree PASSED [ 37%]
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted pytest output showing the legacy-fallback tests (kind-less entry -> `orchestrate`; explicit `child`; missing file -> `None`/`execute`; host agreement) PASSED; plus pasted output of the scratch non-vacuity run (resolver changed to `entry.get("kind")`) showing the kind-less-entry orchestrator test FAIL with `execute` != `orchestrate`, then pasted `git diff --stat agent_workflows/runner_shared.py` showing the scratch edit reverted (empty, or only the E-05 comment change).
  - Observed evidence:
```
tests/test_orchestrator_kind_derivation.py::LegacyManifestKindFallback::test_both_hosts_resolve_a_legacy_manifest_identically PASSED [ 62%]
tests/test_orchestrator_kind_derivation.py::LegacyManifestKindFallback::test_an_unreadable_plan_file_fails_to_the_safe_direction PASSED [ 75%]
tests/test_orchestrator_kind_derivation.py::LegacyManifestKindFallback::test_a_manifest_with_kind_is_trusted_and_no_file_is_read PASSED [ 87%]
tests/test_orchestrator_kind_derivation.py::LegacyManifestKindFallback::test_a_manifest_without_kind_still_derives_orchestrate_on_both_hosts PASSED [100%]

Scratch non-vacuity failure output:
FAILED tests/test_orchestrator_kind_derivation.py::LegacyManifestKindFallback::test_a_manifest_without_kind_still_derives_orchestrate_on_both_hosts - AssertionError: 'execute' != 'orchestrate'

Revert verification:
git diff --stat agent_workflows/runner_shared.py
(reverted to empty diff before E-05 comment edits)
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted pytest output showing the legacy-manifest `initialize_run` test passing for both hosts; the observation is produced by `runner_shared.initialize_run_core` queue build (`resolve_manifest_kind(plan, p_path)`), created by E-03; and the same scratch non-vacuity run showing it FAIL.
  - Observed evidence:
```
Passing test:
tests/test_orchestrator_kind_derivation.py::LegacyManifestQueueBuild::test_legacy_manifest_queue_build_derives_orchestrate_on_both_hosts PASSED [ 50%]

Scratch non-vacuity failure output:
FAILED tests/test_orchestrator_kind_derivation.py::LegacyManifestQueueBuild::test_legacy_manifest_queue_build_derives_orchestrate_on_both_hosts - AssertionError: 'execute' != 'orchestrate'
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted pytest output showing the mock-patched control test PASSED on both hosts (asserting `execute`/`None` under the pass-through resolver), and pasted `rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_orchestrator_kind_derivation.py` returning no matches (no source reading).
  - Observed evidence:
```
Control test passing:
tests/test_orchestrator_kind_derivation.py::LegacyManifestQueueBuildNonVacuityControl::test_queue_build_derivation_depends_on_fallback_on_both_hosts PASSED [ 12%]

No source-reading pins:
$ rg -n "import ast|import inspect|read_text\(.*\.py" tests/test_orchestrator_kind_derivation.py
(no matches, exit code 1)
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted `git diff agent_workflows/runner_shared.py agent_workflows/agy_runipd.py` showing only comment/docstring lines changed, exactly the three named sites (section banner, `PlanRecord` docstring, the `_plan_kind` HAD TWO CALLERS comment), each naming `tests/test_orchestrator_kind_derivation.py`; pasted bare `python3 -m pytest` summary line showing zero failures.
  - Observed evidence:
```diff
diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
index 1e0541fcb..8b4ef16e6 100755
--- a/agent_workflows/agy_runipd.py
+++ b/agent_workflows/agy_runipd.py
@@ -1952,7 +1952,7 @@ def validate_manifest(manifest: dict[str, Any]) -> None:
 # second was LIFTED to `runner_shared.plan_kind_from_file` / `resolve_manifest_kind` - given to BOTH
 # hosts rather than kept here, because oc lacked it entirely and the two hosts therefore DISAGREED
 # about a correctness gate in oc's disfavor (`sy7uwh` OQ-03, resolved by the maintainer 2026-09-16).
-# `tests/test_rununify_record.py` was deleted in `19313eed`; no live guard currently asserts this fallback.
+# `tests/test_rununify_record.py` was deleted in `19313eed`; live guard: `tests/test_orchestrator_kind_derivation.py`.


 def expand_selectors(
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index d6b9c9c4b..0c80baf62 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -14067,9 +14067,9 @@ def _read_order(text: str) -> int | None:
 #
 # THE FAILURE MODE HERE IS SILENT AND TYPE-SHAPED, and `818uru`'s own test says so: a shared
 # constructor that DROPPED `kind` "would silently disable orchestrator detection" rather than crash.
-# That is why the guard for this section (`tests/test_rununify_record.py`, deleted in `19313eed`; no
-# live guard currently asserts this derivation) asserted the orchestrator DERIVATION end to end on both
-# hosts rather than merely that a field exists.
+# That is why the guard for this section (`tests/test_rununify_record.py`, deleted in `19313eed`; live
+# guard: `tests/test_orchestrator_kind_derivation.py`) asserted the orchestrator DERIVATION end to end on
+# both hosts rather than merely that a field exists.
 #
 # BOTH PINS WERE INVERTED, NOT DELETED, following this repo's precedent for a pinned decision a later
 # phase deliberately reverses:
@@ -14163,8 +14163,8 @@ class PlanRecord(NamedTuple):
     DO NOT DROP `kind` to "simplify" this. It is what `action_for` reads to detect an orchestrator,
     and losing it disables orchestrator detection SILENTLY and type-shapedly rather than crashing -
     the failure mode `818uru`'s pinned test warned about and the reason
-    `tests/test_rununify_record.py` (deleted in `19313eed`; no live guard currently asserts this)
-    asserted the derivation end to end.
+    `tests/test_rununify_record.py` (deleted in `19313eed`; live guard:
+    `tests/test_orchestrator_kind_derivation.py`) asserted the derivation end to end.
     """

     id6: str
```
Full suite summary:
```
702 passed in 25.13s
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`. OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. The one-off scratch edit in V-02 must be reverted before any commit. Commit only those paths through `aw commit 33wan5 -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. Paste the ACTUAL runner output for every test claim; never claim a pass you did not run.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `8ww1zo` carries no `- Blocks-Release:` to inherit.
