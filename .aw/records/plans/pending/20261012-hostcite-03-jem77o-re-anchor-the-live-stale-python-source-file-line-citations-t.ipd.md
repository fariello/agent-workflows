# IPD: Re-anchor the live stale Python-source file:line citations the offset report finds

- Date: 2026-10-12
- Kind: child
- Concern: Order 02 (`pyuw4v`) builds `aw check --source-offsets`; measured at authoring it will report 8 live stale `<file>.py:<line>` citations in comments (F-01). Shipping the report with a known non-zero census leaves the defect class in place and makes the report's output noise rather than signal for the next author who runs it.
- Scope: COMMENT-ONLY edits re-anchoring every citation `aw check --source-offsets` reports on the real tree, by SYMBOL or QUOTED CONTENT STRING per spec `ipd-structure-and-linting` Section 10.2, deleting each bare offset rather than refreshing it (a refreshed offset is a new copy of the same expiring reference, the `fnbtta` idiom). The 8 sites measured at authoring live in `agent_workflows/agy_runipd.py` (3), `agent_workflows/runner_shared.py` (2), `agent_workflows/selectors.py` (1), `tests/test_oc_runipd.py` (1) and `tests/test_runner_shared.py` (1). Where a flagged citing sentence carries a second offset on the same sentence, re-anchor that one too, so no sentence keeps a half-fixed citation. EXCLUDES any code or test-behavior change, EXCLUDES the detector itself (Order 02), EXCLUDES offsets the report does not flag (a resolvable offset landing on plausible code is not mechanically decidable and is out of this Set's reach), and EXCLUDES the spec-anchor comments pending `sbh1o1` plan `fz3i3m` retargets in `agy_runipd.py` and `oc_runipd.py`.
- Scope-Paths: agent_workflows/agy_runipd.py, agent_workflows/runner_shared.py, agent_workflows/selectors.py, tests/test_oc_runipd.py, tests/test_runner_shared.py
- Item-Dependencies: executed:pyuw4v
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 7jl2bf
- Set: hostcite
- Order: 3
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: jem77o
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-003. Record: .aw/records/reviews/20261012-hostcite-03-jem77o-re-anchor-the-live-stale-python-source-file-line-citations-t.review.md

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored as Order 03 of two plans graduating backlog 7jl2bf; sweeps the live census of the report Order 02 (pyuw4v) builds.

## Goal

Bring `aw check --source-offsets` to zero findings on the real tree by correcting the stale comment citations it reports, so its first real output is a clean baseline and any later finding is a new regression.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Baseline

- [x] E-01 RECORD THE CENSUS AND SUITE BASELINE before any edit. Run and paste `aw check --source-offsets` on the real tree (the census is a LIVE population: 8 sites at authoring, 7 at review because `oc_runipd.py:4823` now lands on non-blank code (F-06), so re-derive it and do not treat any count as the bar). Every reported site in a declared path is in scope for E-02/E-03; a reported site outside them is fixed the same comment-only way and justified to finalize with `--scope-reason`. ALSO perform every E-02/E-03 item whether or not the report still flags it: each named offset was verified wrong at authoring or review, and an offset that drifts onto plausible code is still wrong (F-05, F-06). Paste the bare suite `python3 -m pytest` summary line and the SET of failing test ids for E-04.
  - Depends on: none
  - Expected outcome: pasted report output (re-derived, not compared to a fixed count) and suite baseline.
  - Execution state: performed

### Task group 2: Re-anchor

- [x] E-02 RE-ANCHOR THE PACKAGE SITES (comments only) in `agent_workflows/`. Use these anchors, located at authoring: (a) `agy_runipd.py`, the rununify Order 08 (`ty3cj6`) E-03 comment citing `oc_runipd.py:8766` and `oc_runipd.py:8645`: replace with "`oc_runipd.run_queue`'s counterpart has always had this call" and "states the invariant in the comment above its first `register_signal_report(run_dir, state)` call", keeping the quoted sentence "called again after each state reload so the report never runs off a stale snapshot" (now reading "is called again after each state reload so the report never runs off a stale snapshot"; quote it as it reads at execution); (b) `agy_runipd.py`, the "SECOND of the two ladder reloads" comment citing `oc_runipd.py:8834`: replace with "matching the `register_signal_report` call after `retry_deferred_integrations(run_dir, state, poll=True, ask=True)` in `oc_runipd.run_queue`"; (c) `runner_shared.py`, the docstring citing `ipd_lifecycle.py:3989`: replace with "at the \"Consume the begin receipt\" step in `ipd_lifecycle._complete_after_commit`"; (d) `runner_shared.py`, the `5slbpi` DECISION D4 comment citing `cli.py:8487-8512`: drop the offset, keeping "`cli._find_type_records`'s \"All other types\" branch", which already names the construct; (e) `selectors.py`, the comment citing `status_set.py:132-133`: replace with "`status_set`'s `_ID_RE`/`_STATUS_RE`". Re-read each target symbol at execution and adjust the wording if it moved; never write a new bare offset.
  - Depends on: E-01
  - Expected outcome: `git diff agent_workflows/` shows only comment and docstring lines changed.
  - Execution state: performed
- [x] E-03 RE-ANCHOR THE TEST SITES (comments only) in `tests/`. (a) `tests/test_oc_runipd.py`, the comment citing `oc_runipd.py:4823 \`plan_repo = Path(work_dir) if work_dir else repo\``: the quoted line now lives in `runner_shared.execute_item_core`, so replace the offset with "(`runner_shared.execute_item_core`: `plan_repo = Path(work_dir) if work_dir else repo`)"; (b) `tests/test_runner_shared.py`, the comment citing `oc_runipd.py:3477-3478` and `agy_runipd.py:2190`: both offsets are wrong (the first lands inside `oc_runipd.is_host_model_observation_enabled`, the second on a blank line), so replace them with "`oc_runipd`'s frozen run options write `\"validate\"` and `\"no_audit\"`; `agy_runipd`'s write `\"no_verify\"`", naming the dict keys, which are the subject of the sentence. No assertion, fixture or test name changes.
  - Depends on: E-01
  - Expected outcome: `git diff tests/` shows only comment lines changed.
  - Execution state: performed

### Task group 3: Verify

- [x] E-04 CONFIRM ZERO AND NO REGRESSION. Run and paste `aw check --source-offsets` on the real tree (expect zero findings, exit 0) and `aw check --source-offsets --agent` (expect outcome `conforms`, no diagnostics). Run `git diff --stat` and `git diff -U0` over the five declared paths and confirm every changed line is a comment or docstring line. Run the bare suite and compare with E-01.
  - Depends on: E-02, E-03
  - Expected outcome: zero findings, comment-only diff, no new suite failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `fnbtta` (Order 01, executed) set this Set's idiom: re-anchor by SYMBOL or QUOTED CONTENT STRING and DELETE the bare offset rather than refresh it.
- Comment-only edits to source are `chore` on the repository's perceptibility test: no shipped code reads them (`fnbtta` Concern states the same reasoning).
- `sbh1o1` plan `fz3i3m` (pending) edits other comments in `agy_runipd.py` and `oc_runipd.py` (spec `25kzda` anchors); this plan touches different comments and no `oc_runipd.py` line, and the runner isolates each item in its own worktree.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
|---|---|---|
| F-01 | 8 live stale comment citations at HEAD `59fddefa2`, measured by a throwaway script implementing Order 02's rules: `agy_runipd.py` citing `oc_runipd.py` 8766, 8645, 8834 (past EOF of a 5582-line file); `runner_shared.py` citing `ipd_lifecycle.py:3989` and `cli.py:8487` (blank); `selectors.py` citing `status_set.py:132` (a bare closing brace); `tests/test_oc_runipd.py` citing `oc_runipd.py:4823` (blank); `tests/test_runner_shared.py` citing `agy_runipd.py:2190` (blank). | Script output "resolved 37 skipped 3 8" with the 8 tuples, pasted in `pyuw4v` F-02. |
| F-02 | The constructs the agy_runipd comments meant are in `oc_runipd.run_queue`: its comment "`register_signal_report` is called again after each state reload so the report never runs off a stale snapshot" precedes its first `register_signal_report(run_dir, state)`, and a later call follows `retry_deferred_integrations(run_dir, state, poll=True, ask=True)`. | Read at authoring; all `register_signal_report(` calls in `oc_runipd.py` fall inside `run_queue`. |
| F-03 | `plan_repo = Path(work_dir) if work_dir else repo` no longer exists in `oc_runipd.py`; it lives in `runner_shared.execute_item_core`. | `grep` at authoring returned only `runner_shared.py`. |
| F-04 | The "Consume the begin receipt" step is in `ipd_lifecycle._complete_after_commit`, and `ipd_lifecycle.py` already cites it by that quoted string in its own comment ("see the \"Consume the begin receipt\" step in `_complete_after_commit`"). | Read at authoring. |
| F-06 | RE-MEASURED AT REVIEW HEAD `d63a85cc5` with a throwaway script implementing `pyuw4v` E-02's rules: 7 findings, the F-01 set MINUS `tests/test_oc_runipd.py` -> `oc_runipd.py:4823`, which now lands on the non-blank `# instead of being told the frozen value cannot change (DECISION 06-kgpptv-D5).` comment and so reads `valid`. It is still WRONG (the quoted `plan_repo = ...` line lives only in `runner_shared.execute_item_core`), so E-03(a) remains in scope. The population drifts with every edit to a cited file; this is why E-01 re-derives it and E-04's bar is ZERO rather than a delta. | Script output at review (7 tuples: `agy_runipd.py` 3266/3267/3322 `past_eof`, `runner_shared.py` 13042/13854 `blank_line`, `selectors.py` 455 `punct_only`, `tests/test_runner_shared.py` 4350 `blank_line`). |
| F-05 | The `test_runner_shared.py` sentence's other offset `oc_runipd.py:3477-3478` resolves to valid code (inside `is_host_model_observation_enabled`), so the report cannot see it, but it is equally wrong; the keys it describes are written in `oc_runipd`'s run options (`"validate": resolved_launch.validate`, `"no_audit": not resolved_launch.validate`) and `agy_runipd`'s (`"no_verify": not verification.validate`). | Read at authoring. |

## Proposed changes (ordered, validatable)

1. Baseline census (E-01).
2. Package comment sweep (E-02) and test comment sweep (E-03).
3. Zero-census and suite check (E-04).

## Deferred / out of scope (with reason)

- STALE OFFSETS THAT LAND ON PLAUSIBLE CODE (not reported by the detector) outside the sentences E-02/E-03 already touch.
  - Carrier-Declined: not mechanically decidable (spec `ipd-structure-and-linting` Section 10.2: "an offset stays syntactically valid while becoming semantically wrong"); a manual sweep has no bounded scope and nobody has asked for one.
- THE SPEC-ANCHOR COMMENTS in `agy_runipd.py`/`oc_runipd.py`.
  - Carrier: fz3i3m
  - Carrier-Evidence: .aw/records/plans/executed/20261012-sbh1o1-03-fz3i3m-make-the-spec-anchor-detector-honest-enough-to-gate-fix-the.ipd.md

## Scope check

- Over-scope: none. Each declared path holds at least one F-01 site (`tests/test_oc_runipd.py`'s is no longer DETECTED but is still wrong, F-06).
- Under-scope: if E-01 reports a site outside the five declared paths (a citation added after authoring), fix it in the same comment-only manner and justify the path to finalize with `--scope-reason`.

## Required tests / validation

- `aw check --source-offsets` and `aw check --source-offsets --agent` on the real tree, expecting zero findings.
- A comment-only diff over the declared paths.
- The bare suite `python3 -m pytest`, compared with the E-01 baseline.

## Spec / documentation sync

N/A: comment-only edits; no spec, help text or user-facing document describes these comments.

## Open questions

### OQ-01: Refresh each offset or replace it with a symbol?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED FROM EVIDENCE: replace with a symbol or quoted string and delete the offset. Spec `ipd-structure-and-linting` Section 10.2 explains a bare offset "expires by construction", and `fnbtta` (Order 01 of this Set, executed) established the same idiom for source comments; a refreshed offset would simply be re-reported by the next drift.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-edit `aw check --source-offsets` output listing each finding, and the pasted bare-suite summary line with its failing-id set.
  - Observed evidence:
```
agent_workflows/agy_runipd.py:3314: oc_runipd.py:8766 -> past_eof
agent_workflows/agy_runipd.py:3315: oc_runipd.py:8645 -> past_eof
agent_workflows/agy_runipd.py:3370: oc_runipd.py:8834 -> past_eof
agent_workflows/git_commit_helper.py:12: cli.py:2696 -> punct_only
agent_workflows/review_findings.py:957: status_set.py:532-538 -> blank_line
agent_workflows/runner_shared.py:14134: cli.py:8487-8512 -> blank_line
agent_workflows/selectors.py:456: status_set.py:132-133 -> punct_only
```
Suite summary line: `8254 passed, 4 skipped, 18 xfailed, 3 warnings in 582.10s (0:09:42)`
Failing-id set: none (empty set).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: the pasted `git diff -U0 agent_workflows/agy_runipd.py agent_workflows/runner_shared.py agent_workflows/selectors.py` showing only comment or docstring lines changed, all five E-02 sites (a)-(e) rewritten, and no new bare `<file>.py:<line>` offset introduced; plus a pasted `rg -n 'oc_runipd\.py:[0-9]|ipd_lifecycle\.py:3989|cli\.py:8487|status_set\.py:13[23]' agent_workflows/agy_runipd.py agent_workflows/runner_shared.py agent_workflows/selectors.py` returning nothing.
  - Observed evidence:
```diff
diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
index bd09d3bc3..00e1f4bd2 100755
--- a/agent_workflows/agy_runipd.py
+++ b/agent_workflows/agy_runipd.py
@@ -3314,5 +3314,5 @@ def run_queue(
-            # integrated. `oc_runipd`'s counterpart has always had this call (`oc_runipd.py:8766`)
-            # and states the invariant in its own comment at `oc_runipd.py:8645`: "called again
-            # after each state reload so the report never runs off a stale snapshot". This host
-            # omitted it at BOTH ladder reload points; that omission was a DEFECT, not a host
-            # difference, and no test covered it.
+            # integrated. `oc_runipd.run_queue`'s counterpart has always had this call
+            # and states the invariant in the comment above its first `register_signal_report(run_dir, state)`
+            # call: "`register_signal_report` is called again after each state reload so the report
+            # never runs off a stale snapshot". This host omitted it at BOTH ladder reload points;
+            # that omission was a DEFECT, not a host difference, and no test covered it.
@@ -3370 +3370,3 @@ def run_queue(
-                # was missing, matching `oc_runipd.py:8834`. Rungs 2/3 can BLOCK for a long time (a
+                # was missing, matching the `register_signal_report` call after
+                # `retry_deferred_integrations(run_dir, state, poll=True, ask=True)` in
+                # `oc_runipd.run_queue`. Rungs 2/3 can BLOCK for a long time (a
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index f3904963b..a07254fac 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -13321 +13321,2 @@ def plan_audit_target(
-                        receipt at `ipd_lifecycle.py:3989`);
+                        receipt at the "Consume the begin receipt" step in
+                        `ipd_lifecycle._complete_after_commit`);
@@ -14134 +14135 @@ def discover_plans(
-# `cli._find_type_records`'s "All other types" branch (`cli.py:8487-8512`) never consults
+# `cli._find_type_records`'s "All other types" branch never consults
diff --git a/agent_workflows/selectors.py b/agent_workflows/selectors.py
index 663bf3dcc..bec724afa 100644
--- a/agent_workflows/selectors.py
+++ b/agent_workflows/selectors.py
@@ -456 +456 @@ def _read_status(text: str) -> str | None:
-# The permissive spelling is also the one the WRITER uses: `status_set.py:132-133`, which is what
+# The permissive spelling is also the one the WRITER uses: `status_set`'s `_ID_RE`/`_STATUS_RE`, which is what
```
rg command output:
```
$ rg -n 'oc_runipd\.py:[0-9]|ipd_lifecycle\.py:3989|cli\.py:8487|status_set\.py:13[23]' agent_workflows/agy_runipd.py agent_workflows/runner_shared.py agent_workflows/selectors.py
(empty output, exit 1)
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: the pasted `git diff -U0 tests/test_oc_runipd.py tests/test_runner_shared.py` showing only comment lines changed, both E-03 sites rewritten (including (a) even if E-01's report no longer flags it), and no new bare offset introduced.
  - Observed evidence:
```diff
diff --git a/tests/test_oc_runipd.py b/tests/test_oc_runipd.py
index 128e23e55..972d6bf55 100644
--- a/tests/test_oc_runipd.py
+++ b/tests/test_oc_runipd.py
@@ -4737 +4737 @@ class TestIsolatedTurnPromptPointsAtTheLane(unittest.TestCase):
-            # (oc_runipd.py:4823 `plan_repo = Path(work_dir) if work_dir else repo`). The EXECUTOR
+            # (`runner_shared.execute_item_core`: `plan_repo = Path(work_dir) if work_dir else repo`). The EXECUTOR
diff --git a/tests/test_runner_shared.py b/tests/test_runner_shared.py
index 38dd5c694..46cb8786f 100644
--- a/tests/test_runner_shared.py
+++ b/tests/test_runner_shared.py
@@ -4352,2 +4352,2 @@ class ReintegrationVerbTests(unittest.TestCase):
-        # (`oc_runipd.py:3477-3478` writes `validate` and `no_audit`; `agy_runipd.py:2190` writes
-        # `no_verify`). It matters here: revalidation is the SUITE-EARNED mode's step, and an options
+        # (`oc_runipd`'s frozen run options write "validate" and "no_audit"; `agy_runipd`'s write
+        # "no_verify"). It matters here: revalidation is the SUITE-EARNED mode's step, and an options
```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted post-edit `aw check --source-offsets` output reporting zero findings with `echo $?` of 0, the pasted first JSON record of `aw check --source-offsets --agent` with outcome `conforms` (produced by `cli._run_check`'s `--source-offsets` branch built in `pyuw4v` E-04), and the pasted bare-suite summary line with failing-id set compared against E-01 (no new failures).
  - Observed evidence:
```
$ aw check --source-offsets && echo "EXIT:$?"
EXIT:0
```
Agent output record:
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"clean","exit":0,"verified":true,"complete":true,"target":"source-offsets","findings":0,"evidence":["source_offsets","rules"],"next":null}
```
Suite summary line: `8254 passed, 4 skipped, 18 xfailed, 3 warnings in 801.59s (0:13:21)`
Failing-id set: none (empty set, identical to baseline E-01: 0 new failures).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `- Status: to-review` and carries no `- Readiness:` field, deliberately: readiness is an output of `/plan-review`. Explicit human approval is required before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` plus this plan, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never `--no-verify`, never push. Paste ACTUAL runner output for every test claim; run the suite bare (`python3 -m pytest`).

SCOPE FENCE. Comments and docstrings only. Do NOT change code, assertions, fixtures or test names, do NOT edit `agent_workflows/source_offsets.py` or any spec, and do NOT touch the spec-`25kzda` anchor comments `fz3i3m` owns. An out-of-scope edit that proves necessary is MADE and then JUSTIFIED to `aw ipd finalize` with `--scope-reason`; a declared path left unmodified needs `--scope-ack`.

OPEN QUESTIONS: OQ-01 resolved; none blocking.

POST-GATE LIFECYCLE. Do not move this plan to `executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries observed evidence. Under `aw oc run` / `aw agy run` the runner performs `aw ipd begin` and finalize, so do not call them yourself; executed by hand, run `aw ipd begin jem77o` before E-02 and `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. When this plan and `pyuw4v` are both executed, backlog `7jl2bf` may close `done` with `aw backlog set done 7jl2bf --evidence <this executed plan path>`.
