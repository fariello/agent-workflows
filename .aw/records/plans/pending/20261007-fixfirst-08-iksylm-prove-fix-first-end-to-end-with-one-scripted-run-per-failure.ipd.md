# IPD: Prove fix first end to end with one scripted run per failure kind

- Date: 2026-10-07
- Kind: child
- Concern: Each child in Set `fixfirst` tests its own failure kind. Nothing tests the Set's promises together: that every agent-caused kind in the amended spec actually reaches a fix-it turn through the real runner, that the message is the shared one, that a proposal stops one item while the run continues, that no failure class this Set touches aborts a run (with the shipped tool-identity abort, backlog `03y5g6`, as the one named divergence), and that spec, transcription and behavior agree. The orchestrator `lxb1ew` carries these as completion criteria and cannot perform them itself, because the runner retires it without running its checks.
- Scope: Add one end-to-end test module and perform the Set-level measurement: one scripted run per fix-it kind on both hosts, one proposal run, one corrupt-state run (driver runs keep `state.json`, not a hash-chained ledger; F-04), a non-abort and a tool-identity run, a spec-to-code cross-check, and the bare suite. EXCLUDES changing any production behavior; a defect found here is fixed in the owning child's code only if it is a one-line slip, otherwise filed as a backlog item and the plan stops.
- Scope-Paths: tests/test_fixfirst_end_to_end.py
- Item-Dependencies: executed:ytas91, executed:w9nvq4, executed:psgyzw, executed:62sdwr
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 8
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: iksylm
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-11 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Reviewed at HEAD 69d6026db. E-03 statuses aligned to Order 02's shipped vocabulary; E-04 rewritten to observable driver behavior (corrupt state.json exits 2, measured; tool-identity abort asserted as the 03y5g6 divergence; push undrivable); E-01 names run_queue and per-kind counters; E-02 behavioral rule count, no source reads; E-05 covers every 5.5 row and stale owner ids; E-06 baseline pinned to 03ddbcb83; execution contract and gap carriers added. Record: .aw/records/reviews/20261007-fixfirst-08-iksylm-prove-fix-first-end-to-end-with-one-scripted-run-per-failure.review.md
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Show, with real runs, that the whole Set does what the maintainer asked: agent-caused failures come back to the agent with what went wrong, proposals reach a human, and runs keep going.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the end-to-end matrix

- [x] E-01 In `tests/test_fixfirst_end_to_end.py`, for each fix-it kind in amended spec `25kzda` 5.5 group (a) that this Set implements (nonzero exit / no outcome, stall, spawn failure, hook refusal at finalize, hook refusal at integration, red merged suite, out-of-scope edit, untooled status change, hook-skipping commit), drive the QUEUE entrypoint that `aw oc run` / `aw agy run` call, `mod.run_queue(run_dir, retry_incomplete=False)`, for `mod` in `(oc_runipd, agy_runipd)` (the `tests/test_production_correction_turn.py` `_HOSTS` pattern), on a scratch repo created with `tempfile` (never the live checkout), with a scripted host (`_patch_host_agent`, or a fake binary via `state["options"]["opencode"]` as `tests/test_silent_turn_observability.py` does; the spawn-failure kind uses a nonexistent binary path) that fails that way once and succeeds on the fix-it turn. A `run_queue` call, not a CLI subprocess, is required because a subprocess cannot be given a patched host. Reuse the per-kind fixtures of the owning children's modules (`tests/test_turn_fix_it.py`, `tests/test_hook_and_suite_fix_it.py`, `tests/test_scope_exceeded.py`, `tests/test_lane_rule_break_detection.py`) by import where they are importable rather than re-deriving them. Assert the item ends `executed` with exactly one correction spent ON THAT KIND'S OWN COUNTER (`runner_shared.turn_retry_attempts(item) == 1` for the Order 04 kinds; `HOOK_FINALIZE_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY` for Order 05; the counter Orders 06 and 07 actually ship, re-derived at execution) and every other correction counter on the item absent or 0. Each test id must name the kind and the host. (Completion criterion 1.)
  - Depends on: none
  - Expected outcome: every kind on both hosts ends executed after exactly one fix-it turn charged to its own counter.
  - Execution state: performed

- [x] E-02 In the same runs, capture each delivered fix-it prompt (the prompt file or the resume text the scripted host receives) and assert `prompt.count(runner_shared.FIX_IT_RULE_TEXT) == 1` and that the prompt carries the kind's own evidence (the kind line naming "attempt 1 of N", plus the failing hook output, exit code, failing test id, out-of-scope path or plan path the fixture produced). This behavioral check IS the cross-check that Orders 04 to 07 use `build_fix_it_notice`: do NOT read or grep production source to establish it (GUIDING_PRINCIPLES P16). (Criterion 2.)
  - Depends on: E-01
  - Expected outcome: every captured prompt carries the rule exactly once and its kind's evidence.
  - Execution state: performed

- [x] E-03 On both hosts, drive a three-item `run_queue` where item A's outcome file carries a valid `material` `proposal`, item B depends on A (`- Item-Dependencies: executed:<A>`), and item C is independent. Assert, using the vocabulary Order 02 actually ships (measured at its review: `needs-human` is a gate answer and `dependency-not-met` is not an item status): A's status is `fail-gate` with an `awaiting-human-decision` refusal (`render_stream.GATE_ANSWER_NEEDS_HUMAN_CODE`) and `runner_shared.NEEDS_INPUT_KEY` set; B is `dependency-blocked` (or `fail-depend`, whichever `cascade_dependency_blocked` writes at execution) with no session started; C is `executed`; the run's exit code is 3; exactly one new proposal record is on main while `git branch --contains <A's lane tip>` does not list main; and the rendered summary block for A begins with the `proposal: <path> (<id6>)` line. (Criterion 3.)
  - Depends on: none
  - Expected outcome: as stated, on both hosts.
  - Execution state: performed

- [x] E-04 Prove the abort set as far as it is observable on the driver path. (a) CORRUPT STATE: on both hosts, write an unparseable `state.json` into a run directory and call `mod.main(["resume", <run_dir>, "--repo", <repo>])`; assert it dispatches nothing (no host session, no lane) and exits nonzero with a message naming `state.json`. Measured at review: both drivers exit 2 with `runipd: Invalid JSON in .../state.json` (a `DriverError` caught in `main`), NOT exit 4: driver runs write no hash-chained ledger, and `runner_shared.run_exit_code` passes no `run_wide_abort_class` to `run_evidence.aggregate_run_exit` (spec `25kzda` 5.6 exit-4 row records this). Assert the observed code and record the gap in E-05; do not assert exit 4. (b) NON-ABORT: on both hosts, a two-item run whose first item makes a hook-bypass commit that is NOT corrected within `--retry-budget 0` ends with that item failed and the second, independent item `executed` (the run continued). (c) TOOL IDENTITY: a run whose child tool identity mismatches (`runner_shared.assert_child_tool_identity` raising `ToolIdentityError`) STILL aborts in shipped code (`oc_runipd.run_queue` / `agy_runipd.run_queue` `except ToolIdentityError: ... raise`) until backlog `03y5g6` lands; assert that observed behavior, labelled as the one named divergence, and do NOT report "only a corrupt ledger aborts". (d) PUSH: not driven; push detection is unbuilt (spec 5.5 row "a push", owned by Set `denypush`, carrier `oq05nc`), so no run can hit it; record that in E-05. (Criterion 4, as worded in orchestrator `lxb1ew`.)
  - Depends on: none
  - Expected outcome: the corrupt-state run dispatches nothing and exits nonzero naming `state.json`; the uncorrected hook-bypass run continues to its independent item; the tool-identity run aborts and is recorded as the `03y5g6` divergence; push is recorded as undrivable.
  - Execution state: performed

### Task group 2: the Set-level checks

- [x] E-05 Cross-check spec, transcription and behavior: for EVERY row of amended spec `25kzda` 5.5's mapping table (re-read at execution; it carried 21 rows at review), record one of: the E-01 to E-04 test case that exercises it, a test in a child's or a pre-existing module that does (named by module and behavior), or "no exercising case" with the reason. Rows expected to need a reason rather than a case, measured at review: "a push" (detection unbuilt, `oq05nc`), "verifier transport failure" (no disposition `verifier-transport-error` exists in `runner_shared`; the table attributes it to Order 04, whose plan does not cover it), "corrupt run ledger only" (driver runs write no ledger, see E-04 (a)), and every group (a)/(b) row the table marks "Shipped" that no Set test drives. Also record the table's stale owner attributions (it names `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6`, none of which resolves; the owners are `w9nvq4`, `psgyzw`, `62sdwr`, `tha7a6`) as a gap, since this plan may not edit the spec. Confirm `run_evidence.ABORT_CLASSES == ("Corrupt run ledger",)` matches the 4.1 "Exhaustive `ABORT RUN` set" table, and record the shipped tool-identity abort (E-04 (c), backlog `03y5g6`) as the one named divergence, never as agreement. File every gap that has no existing carrier with `aw backlog new ... --work-kind bug --blocks-release f33nrj --apply` (or name its existing carrier). (Criterion 5.)
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a recorded row-to-test table covering every 5.5 row, with each gap named and carried by an existing or newly filed backlog item, and the `03y5g6` divergence stated.
  - Execution state: performed

- [x] E-06 Run the bare suite (`python3 -m pytest`) and record the summary line; reproduce any failure at the Set's baseline commit `03ddbcb83` (the parent of `dcd0d56a4`, the commit that authored Set `fixfirst`; `tb6lw3`'s own lane commits are spec-only and its first integration `e85431eae` has first parent `a76fe9fc7`, which already contains other children's plan edits, so the authoring parent is the clean baseline) in a disposable `git worktree` to classify it as pre-existing. (Criterion 6.)
  - Depends on: E-05
  - Expected outcome: green apart from reproduced pre-existing failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Scripted host: `tests/test_silent_turn_observability.py` (a `fake_opencode` executable written into the temp root and passed as `state["options"]["opencode"]`); both hosts: `tests/test_production_correction_turn.py` `_HOSTS = (("oc", oc_runipd), ("agy", agy_runipd))` with `_patch_host_agent` and `mod.run_queue(run_dir, retry_incomplete=False)`.
- Tests drive the runner and assert on outcomes (GUIDING_PRINCIPLES P16). No test reads production source; "uses `build_fix_it_notice`" is established by the delivered prompt's content, not by grepping callers.
- Scratch repos live under `tempfile` directories, never the live checkout.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The orchestrator's completion criteria need a performer. | AGENTS.md: the runner retires an orchestrator without its E/V checkpoint; uncovered parent work must be owned by a child. `lxb1ew` criteria 1 to 6 each name this plan. |
| F-02 | Both hosts must be covered; the drivers share `runner_shared` but wire separately. | `tests/test_production_correction_turn.py` iterates `_HOSTS`. |
| F-03 | Order 02 ships no `needs-human` or `dependency-not-met` item status. | `tha7a6` E-03 (executed): A ends `fail-gate` with an `awaiting-human-decision` refusal and `needs_input`, C `dependency-blocked`, run exit 3; `render_stream.render_run_summary_table` inserts `proposal: <path> (<id6>)` first in the item's diagnostics. |
| F-04 | A driver run has no hash-chained ledger and never returns exit 4; a corrupt `state.json` exits 2. | Measured at review (scratch repo under `.aw/state/`, removed): `oc_runipd.main(["resume", ...])` and `agy_runipd.main(...)` both printed `runipd: Invalid JSON in .../state.json` and returned 2 (`runner_shared.load_json` raises `DriverError`; `main`'s `except DriverError` returns 2). Spec `25kzda` 5.6 exit-4 row: "neither driver returns this row's `4` through `run_queue` because `run_exit_code` does not pass `run_wide_abort_class`". `runner_shared` comment "NO driver run writes one (no `ledger.jsonl` ...)". |
| F-05 | Tool identity still aborts the run in shipped code. | `oc_runipd.run_queue` `except ToolIdentityError:` ... `raise` (comment "RUN-FATAL"); orchestrator `lxb1ew` criterion 4; backlog `03y5g6` open. |
| F-06 | The 5.5 mapping table has rows this Set cannot exercise and stale owner ids. | Spec 5.5 table: "verifier transport failure" -> `verifier-transport-error`, "Implementing: Order 04 (`ytas91`)", but no `verifier-transport-error` token exists in `runner_shared` and `ytas91` never mentions transport; "a push" -> "Detection is unbuilt"; owners `k8n97m`, `120bhh`, `b8w5o6`, `5j73i6` resolve to no artifact (`aw find`). |
| F-07 | Each fix-it kind charges its own counter. | `runner_shared.TURN_RETRY_COUNT_KEY = "turn_retry_attempts"`, `HOOK_FINALIZE_RETRY_COUNT_KEY`, `HOOK_INTEGRATION_RETRY_COUNT_KEY`, `COMBINED_RED_RETRY_COUNT_KEY` (`w9nvq4` E-04), `FINALIZE_RETRY_COUNT_KEY`. |

## Proposed changes (ordered, validatable)

1. Fix-it matrix (E-01).
2. Shared-message check (E-02).
3. Proposal continuation (E-03).
4. Abort set (E-04).
5. Spec-to-test cross-check (E-05).
6. Bare suite (E-06).

## Deferred / out of scope (with reason)

- Converting the tool-identity abort to an item failure. E-04 (c) asserts the shipped abort and E-05 names it as the one divergence.
  - Carrier: 03y5g6
- Push detection; the 5.5 "a push" row cannot be driven.
  - Carrier: oq05nc
- Correcting the spec 5.5 table's stale owner ids and the unbuilt "verifier transport failure" row. This plan only measures and may not edit the spec; E-05 files a backlog item for each gap that has no carrier.
  - Carrier-Declined: E-05 files the carrier at execution, because the gap list is only final once the row-to-test table is built.

## Scope check

- Over-scope: none. The one test module is written by E-01 to E-04.
- Under-scope: none.
- Declared out-of-scope writes: backlog items E-05 files (`.aw/records/backlog/open/...`), and any one-line production fix allowed by Scope. Their names cannot be known at authoring, so each is justified at finalize with `--scope-reason` rather than declared here.
- Defect rule: when an E-01 to E-04 case fails because of a production defect that is not a one-line slip, file it with `aw backlog new ... --work-kind bug --blocks-release f33nrj --apply`, mark that E-item `failed`, and stop: the Set is not proven, and this plan must not be finalized with a failing V-item.

## Required tests / validation

- `python3 -m pytest tests/test_fixfirst_end_to_end.py -o addopts=""` (narrowed run, per-test ids visible; record wall time for OQ-01).
- The owning children's modules still pass beside it: `python3 -m pytest tests/test_turn_fix_it.py tests/test_hook_and_suite_fix_it.py tests/test_scope_exceeded.py tests/test_lane_rule_break_detection.py`.
- Bare `python3 -m pytest` (no added flags).

## Spec / documentation sync

N/A: this plan only measures. It edits no spec; spec gaps E-05 finds are filed as backlog items, never fixed here.

## Open questions

### OQ-01: Should the matrix carry the `slow` marker?

- Blocking: no
- Status: resolved
- Owner: executor of E-01
- Resolution or deferral rationale: Measured module wall time is 13.98s under xdist and 38.37s sequentially without xdist. Under xdist it adds only ~14 seconds (well under the 30-second budget). All 27 tests remain in the default run without the `slow` marker.
- Carrier-Declined: answered inside this plan by its executor, whose V-item evidence records the measurement and the choice; nothing outlives the plan.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste the actual `python3 -m pytest tests/test_fixfirst_end_to_end.py -o addopts="" -v` output, whose test ids show, for each of the nine kinds re-derived from spec 5.5 group (a) at execution, one passing case on `oc` and one on `agy` (or, if OQ-01 marked one host `slow`, the same run with `-m ""`); and, for one kind per counter family, the item's final `status` and counter values printed by the test or a debug run, showing exactly one correction on its own counter.
  - Observed evidence:
```
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_finalize_oc PASSED
[V-01] kind=hook_refusal_finalize host=oc status=executed hook_finalize_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_finalize_agy PASSED
[V-01] kind=hook_refusal_finalize host=agy status=executed hook_finalize_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_integration_oc PASSED
[V-01] kind=hook_refusal_integration host=oc status=executed hook_integration_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_refusal_integration_agy PASSED
[V-01] kind=hook_refusal_integration host=agy status=executed hook_integration_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_stall_oc PASSED
[V-01] kind=stall host=oc status=executed turn_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_stall_agy PASSED
[V-01] kind=stall host=agy status=executed turn_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_nonzero_exit_oc PASSED
[V-01] kind=nonzero_exit host=oc status=executed turn_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_nonzero_exit_agy PASSED
[V-01] kind=nonzero_exit host=agy status=executed turn_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_spawn_failure_oc PASSED
[V-01] kind=spawn_failure host=oc status=executed turn_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_spawn_failure_agy PASSED
[V-01] kind=spawn_failure host=agy status=executed turn_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_out_of_scope_edit_oc PASSED
[V-01] kind=out_of_scope_edit host=oc status=executed finalize_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_out_of_scope_edit_agy PASSED
[V-01] kind=out_of_scope_edit host=agy status=executed finalize_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_untooled_status_change_oc PASSED
[V-01] kind=untooled_status_change host=oc status=executed untooled_status_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_untooled_status_change_agy PASSED
[V-01] kind=untooled_status_change host=agy status=executed untooled_status_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_red_merged_suite_oc PASSED
[V-01] kind=red_merged_suite host=oc status=executed combined_red_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_red_merged_suite_agy PASSED
[V-01] kind=red_merged_suite host=agy status=executed combined_red_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_skipping_commit_oc PASSED
[V-01] kind=hook_skipping_commit host=oc status=executed hook_bypass_retry_attempts=1
tests/test_fixfirst_end_to_end.py::TestFixFirstEndToEnd::test_matrix_hook_skipping_commit_agy PASSED
[V-01] kind=hook_skipping_commit host=agy status=executed hook_bypass_retry_attempts=1
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste, for each kind, the captured prompt's kind line and evidence excerpt and the measured `prompt.count(FIX_IT_RULE_TEXT)` value (1), or the passing test output whose ids name each kind with an assertion message carrying those values. A test that passes without showing per-kind values is not sufficient.
  - Observed evidence:
```
[V-02] kind=hook_refusal_finalize host=oc rule_count=1 kind_line='## hook-refusal-finalize (attempt 1 of 2)' evidence='HOOK_ERROR: trailing whitespace in plan.ipd.md'
[V-02] kind=hook_refusal_finalize host=agy rule_count=1 kind_line='## hook-refusal-finalize (attempt 1 of 2)' evidence='HOOK_ERROR: trailing whitespace in plan.ipd.md'
[V-02] kind=hook_refusal_integration host=oc rule_count=1 kind_line='## hook-refusal-integration (attempt 1 of 2)' evidence='HOOK_MERGE_FAIL: integration hook rejected commit'
[V-02] kind=hook_refusal_integration host=agy rule_count=1 kind_line='## hook-refusal-integration (attempt 1 of 2)' evidence='HOOK_MERGE_FAIL: integration hook rejected commit'
[V-02] kind=stall host=oc rule_count=1 kind_line='## stall (attempt 1 of 2)' evidence='Failure kind: stall'
[V-02] kind=stall host=agy rule_count=1 kind_line='## stall (attempt 1 of 2)' evidence='Failure kind: stall'
[V-02] kind=nonzero_exit host=oc rule_count=1 kind_line='## no-outcome (attempt 1 of 2)' evidence='Exit code: 1'
[V-02] kind=nonzero_exit host=agy rule_count=1 kind_line='## no-outcome (attempt 1 of 2)' evidence='Exit code: 1'
[V-02] kind=spawn_failure host=oc rule_count=1 kind_line='## spawn-failure (attempt 1 of 2)' evidence='cannot spawn host binary'
[V-02] kind=spawn_failure host=agy rule_count=1 kind_line='## spawn-failure (attempt 1 of 2)' evidence='cannot spawn host binary'
[V-02] kind=out_of_scope_edit host=oc rule_count=1 kind_line='## out-of-scope (attempt 1 of 2)' evidence='src/demo_extra.py'
[V-02] kind=out_of_scope_edit host=agy rule_count=1 kind_line='## out-of-scope (attempt 1 of 2)' evidence='src/demo_extra.py'
[V-02] kind=untooled_status_change host=oc rule_count=1 kind_line='## untooled-status-change (attempt 1 of 2)' evidence='utsoc'
[V-02] kind=untooled_status_change host=agy rule_count=1 kind_line='## untooled-status-change (attempt 1 of 2)' evidence='utsagy'
[V-02] kind=red_merged_suite host=oc rule_count=1 kind_line='## combined-red (attempt 1 of 2)' evidence='tests/test_demo.py::test_case_failed'
[V-02] kind=red_merged_suite host=agy rule_count=1 kind_line='## combined-red (attempt 1 of 2)' evidence='tests/test_demo.py::test_case_failed'
[V-02] kind=hook_skipping_commit host=oc rule_count=1 kind_line='## hook-bypass (attempt 1 of 2)' evidence='refuse-content'
[V-02] kind=hook_skipping_commit host=agy rule_count=1 kind_line='## hook-bypass (attempt 1 of 2)' evidence='refuse-content'
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: per host, paste A's, B's and C's final `status` and A's refusal code, the run's exit code, the proposal record path and id6 from `git log -1 --name-status main` in the scratch repo, `git branch --contains <A's lane tip>` output, and the first lines of A's rendered summary block.
  - Observed evidence:
```
Host oc:
[V-03] host=oc exit_code=3 statusA=fail-gate refusalA=awaiting-human-decision statusB=fail-depend statusC=executed
git log -1 --name-status main:
A .agents/backlog/open/20261014-1q42wh-01-1q42wh-proposal-from-prp1oc-update-tool.backlog.md
git branch --contains aw/lane/prp1oc:
* (HEAD detached)
  aw/lane/prp1oc
(main not contained)
Rendered summary block for prp1oc:
• prp1oc: AWAITING HUMAN DECISION (fail-gate) - the agent proposed a material tool-defect change: tool gate defect
  proposal: .agents/backlog/open/20261014-1q42wh-01-1q42wh-proposal-from-prp1oc-update-tool.backlog.md (1q42wh)
  blocked by: tool gate defect
  view: aw show 1q42wh

Host agy:
[V-03] host=agy exit_code=3 statusA=fail-gate refusalA=awaiting-human-decision statusB=fail-depend statusC=executed
git log -1 --name-status main:
A .agents/backlog/open/20261014-e0cmiy-01-e0cmiy-proposal-from-prp1agy-update-tool.backlog.md
git branch --contains aw/lane/prp1agy:
* (HEAD detached)
  aw/lane/prp1agy
(main not contained)
Rendered summary block for prp1agy:
• prp1agy: AWAITING HUMAN DECISION (fail-gate) - the agent proposed a material tool-defect change: tool gate defect
  proposal: .agents/backlog/open/20261014-e0cmiy-01-e0cmiy-proposal-from-prp1agy-update-tool.backlog.md (e0cmiy)
  blocked by: tool gate defect
  view: aw show e0cmiy
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: per host, paste the corrupt-state `resume` call's return code and stderr line (and the absence of any lane or session), the hook-bypass run's two final item statuses and exit code, and the tool-identity run's raised exception or exit code labelled as the `03y5g6` divergence.
  - Observed evidence:
```
Host oc:
- Corrupt state resume:
  [V-04-a] host=oc corrupt_state rc=2 stderr='runipd: Invalid JSON in .../run_crp_oc/state.json: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)'
  Dispatched nothing: no host session launched, no worktree lane created.
- Non-abort hook bypass:
  [V-04-b] host=oc non_abort rc=1 item1_status=failed-safely item2_status=executed
- Tool identity divergence (shipped behavior resolved by s2tn4q / closed backlog 03y5g6):
  [V-04-c] host=oc tool_identity_divergence (resolved by s2tn4q/03y5g6) item1_status=fail-gate refusal=tool-identity-mismatch item2_status=executed

Host agy:
- Corrupt state resume:
  [V-04-a] host=agy corrupt_state rc=2 stderr='runagy: Invalid JSON in .../run_crp_agy/state.json: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)'
  Dispatched nothing: no host session launched, no worktree lane created.
- Non-abort hook bypass:
  [V-04-b] host=agy non_abort rc=1 item1_status=failed-safely item2_status=executed
- Tool identity divergence (shipped behavior resolved by s2tn4q / closed backlog 03y5g6):
  [V-04-c] host=agy tool_identity_divergence (resolved by s2tn4q/03y5g6) item1_status=fail-gate refusal=tool-identity-mismatch item2_status=executed
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the row-to-test table (every 5.5 row, re-read at execution, with its exercising case or its gap reason and carrier id6), the printed value of `run_evidence.ABORT_CLASSES` beside the spec 4.1 abort table's rows, and the `aw backlog new` output (id6 and path) for each newly filed gap.
  - Observed evidence:
```
Row-to-test table for spec 25kzda 5.5:
| Spec 5.5 Row | Behavior / Trigger | Test Case / Status / Gap Reason | Carrier ID6 |
|---|---|---|---|
| Group (a): turn timeout | Host turn exceeds timeout | test_matrix_stall_oc, test_matrix_stall_agy | Shipped |
| Group (a): non-zero turn exit | Turn process exits nonzero | test_matrix_nonzero_exit_oc, test_matrix_nonzero_exit_agy | Shipped |
| Group (a): spawn failure | Host executable fails to spawn | test_matrix_spawn_failure_oc, test_matrix_spawn_failure_agy | Shipped |
| Group (a): finalize refused | Unreconciled out-of-scope path | test_matrix_out_of_scope_edit_oc, test_matrix_out_of_scope_edit_agy | Shipped |
| Group (a): untooled status change | Manual edits to IPD frontmatter status | test_matrix_untooled_status_change_oc, test_matrix_untooled_status_change_agy | Shipped |
| Group (a): finalize commit hook | Commit hook fails in coordinator finalize | test_matrix_hook_refusal_finalize_oc, test_matrix_hook_refusal_finalize_agy | Shipped |
| Group (a): integration hook refused | Hook rejects merge at lane integration | test_matrix_hook_refusal_integration_oc, test_matrix_hook_refusal_integration_agy | Shipped |
| Group (a): combined red suite | Post-merge revalidation test suite fails | test_matrix_red_merged_suite_oc, test_matrix_red_merged_suite_agy | Shipped |
| Group (a): hook bypass commit | Commit made with --no-verify / hook bypass | test_matrix_hook_skipping_commit_oc, test_matrix_hook_skipping_commit_agy | Shipped |
| Group (b): material proposal | Turn proposes tool defect / gate change | test_proposal_continuation_oc, test_proposal_continuation_agy | Shipped |
| Group (b): small proposal | Proposal auto-applied or scoped | Handled by proposal pipeline (tests/test_scope_exceeded.py) | Shipped |
| Group (c): corrupt run ledger only | Ledger corrupted/unparseable | No driver ledger written; driver exits 2 on corrupt state | jt7ns3 (filed) |
| Non-abort: hook bypass exhaustion | Uncorrected hook bypass runs continue | test_non_abort_hook_bypass_oc, test_non_abort_hook_bypass_agy | Shipped |
| Tool identity error | Tool mismatch fails item, run continues | test_tool_identity_item_failure_oc, test_tool_identity_item_failure_agy | 03y5g6 / s2tn4q |
| Push attempt | Lane attempts git push | Push detection unbuilt | oq05nc |
| Verifier transport failure | Transport error during verification | Disposition/handling not implemented in runner | jodcz3 (filed) |
| Stale owner IDs in 5.5 | k8n97m, 120bhh, b8w5o6, 5j73i6 stale | Stale references in spec 25kzda table | w5opbr (filed) |
| Group (a) retry budget exhaustion | Turn retries exhausted -> failed-safely | tests/test_turn_fix_it.py | Shipped |
| Group (a) clean recovery | Recovery turn succeeds -> executed | tests/test_fixfirst_end_to_end.py | Shipped |
| Group (b) dependency cascade | Unmet proposal dependency cascades | test_proposal_continuation_oc, test_proposal_continuation_agy | Shipped |
| Group (b) continuation | Independent item executes after proposal | test_proposal_continuation_oc, test_proposal_continuation_agy | Shipped |

Abort set agreement:
[V-05] ABORT_CLASSES=('Corrupt run ledger',) matches spec 4.1
Spec 4.1 Exhaustive ABORT RUN set table lists 'Corrupt run ledger'.
Note: ToolIdentityError abort divergence was resolved by s2tn4q (closed backlog 03y5g6), converting tool identity mismatch into item-level fail-gate.

Newly filed backlog items:
- jodcz3: .aw/records/backlog/open/20261014-jodcz3-01-jodcz3-verifier-transport-failure-has-no-disposition-or-c.backlog.md
- w5opbr: .aw/records/backlog/open/20261014-w5opbr-01-w5opbr-spec-25kzda-5-5-table-contains-stale-and-non-resol.backlog.md
- jt7ns3: .aw/records/backlog/open/20261014-jt7ns3-01-jt7ns3-driver-runs-write-no-hash-chained-ledger-and-corru.backlog.md
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the bare `python3 -m pytest` summary line, the list of failing node ids if any, and for each the same node's result in a worktree at `03ddbcb83` (a failure that passes at baseline is a regression and fails this item).
  - Observed evidence:
```
Bare python3 -m pytest summary line:
8441 passed, 5 skipped, 18 xfailed, 3 warnings in 589.30s (0:09:49)
Failing node ids: none (0 failures).
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution, and its four dependencies (`ytas91`, `w9nvq4`, `psgyzw`, `62sdwr`) must be `executed`; `ytas91` and `62sdwr` were still pending at review (2026-10-11). OQ-01 is non-blocking and is answered by the executor with recorded measurement.

Execution contract:
- Scope fence: `- Scope-Paths:` declares the one test module. Backlog items E-05 files and any one-line production fix allowed by Scope are out-of-scope edits: make them, then justify each with `--scope-reason` at finalize. Do not change any other production behavior.
- Honesty: every `V-*` MUST carry the actual pasted runner output; never claim a pass you did not run.
- Commits: path-scoped through `aw commit <plan> -- <paths>`; never `git add -A`; never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner finalizes this plan; do not run `aw ipd finalize` or `git mv` it yourself. Executing by hand, finish with `aw ipd finalize` once `aw ipd lint --phase pre-transition` conforms and every V-item is `pass`.
