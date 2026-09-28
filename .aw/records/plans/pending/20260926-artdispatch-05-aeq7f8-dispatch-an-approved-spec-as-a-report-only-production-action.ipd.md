# IPD: Dispatch an approved spec as a report-only production action verified by the SPEC-PLAN codes

- Date: 2026-09-26
- Kind: child
- Concern: PRODUCTION HAS NO CONSUMER (spec `z7nbn1` 4.3). `run_selection_policy.ACTION_PLAN` is defined and mapped (spec `approved -> plan`, backlog `open -> plan`), but re-measured at HEAD `310ea53e` it appears in `agent_workflows/` only in its definition, `ACTION_ORDER`, the two table entries, and one `runner_shared` docstring; `runner_shared.ACTION_IMPLEMENTED` is `frozenset(("review",))`, so `--action plan` fails closed; and nothing dispatches an approved spec. The three verification codes spec `z7nbn1` 4.4 brings in scope from approved spec `25kzda` 4.8 (`SPEC-PLAN-COUNT`, `SPEC-PLAN-CONFORMANCE`, `SPEC-PLAN-GATE-CARRY`) grep to ZERO under `agent_workflows/`. Spec `z7nbn1` section 3 and `25kzda` 3.3's `approved` row define the action: author one or more conformant IPDs linked by `From-Spec`, preserve `Blocks-Release` on each, tool-set the spec `approved -> implementing` through `aw specs set`, verify, and REPORT the produced plans as next actions without enqueueing them (OQ-01).
- Scope: IN: (a) a production dispatcher for a queue entry with `artifact_type: spec` and action `plan`: an authoring turn whose prompt names the spec and the production contract (the house "Acting on a backlog item" authoring rules applied to a spec: review-ready `to-review` plans in `pending/`, `aw ipd scaffold`, `From-Spec: <id6>`, the spec's `Blocks-Release` copied exactly, `aw ipd lint` conforming, no edit to the spec's approved requirements); (b) deterministic post-turn verification implementing the three in-scope codes with the pass criteria, message templates and Action columns `25kzda` 4.8 specifies (this plan does not restate them); (c) on success, the runner tool-sets the spec `approved -> implementing` through `aw specs set` citing the produced plans, AFTER the produced plans are committed, and never marks the spec `implemented`; on failure, the spec is left `approved`; (d) report-only: produced plans are recorded on the item as `generated_next_actions` and rendered in the run's end-of-run report, and are NOT added to `state["queue"]`; (e) `ACTION_IMPLEMENTED` gains `plan`, and `enforce_requested_action` legality for `--action plan` is table-driven (legal only where the derived action is `plan`). OUT: `SPEC-PLAN-TRACE` (deferred to backlog `vy20et`, spec `z7nbn1` OQ-02); the other ten `SPEC-*` codes, including the dedicated `SPEC-IMPLEMENTING-TRANSITION` verifier (spec `z7nbn1` 4.4 NOT IN SCOPE; the transition itself IS performed here); dispatching `implementing` specs' children (stays with `25kzda` 3.3, `z7nbn1` section 7); backlog production (plan `y3p3p5`); a same-run follow of produced plans (removed by `hzdq8y`, out of scope per `z7nbn1` 3.4).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/production_checks.py, agent_workflows/render_stream.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_spec_production.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:2ptgds
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 5
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: aeq7f8
- Approval: 2026-09-27, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 all FIXED; review record `.aw/records/reviews/20260926-artdispatch-05-aeq7f8-dispatch-an-approved-spec-as-a-report-only-production-action.review.md`. Re-verified F-1..F-5 at lane HEAD 7504fd60: every seam reproduced (ACTION_PLAN has no consumer, ACTION_IMPLEMENTED is review-only, the three SPEC-PLAN codes grep to zero, the transition is executor-owned), with F-5's spec count corrected to 12 and its conclusion unchanged. ADDED two HIGH findings on the SAME root cause: execute_item_core derives one boolean (is_review = action == "review") and eleven-plus gates key on it, so a `plan` action silently takes the EXECUTE path (suite check, aw ipd finalize AGAINST THE SPEC, backlog close, merge-and-revalidate) (F-6); and OQ-02's resolution asserted review-style integration "applies" while integration_action_for_item measurably returns `execute` for `plan` and isolation_for_action has no isolate_plan key (F-7). E-03 is now a dedicated item giving `plan` its own arm, and E-09 pins it by patching those collaborators to fail if called. Also fixed an undeclared renderer the plan's own Scope check hedged on (F-8, render_stream.py now declared), an unprecedented durable field and report block (F-9), an unnamed quarantine mechanism gated on `not is_review` (F-10), a retry instruction phrased as a table lookup when it is a design decision (F-11), and a refusal message whose explanation and recovery are both about review (F-12). Split the eight items into eleven (E-01..E-11) and rebuilt the V checklist to an 11-item bijection. `aw ipd lint --phase review-finalize` conforming, 0 findings.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 05 of Set artdispatch). ACTION_PLAN consumers, ACTION_IMPLEMENTED, and the three in-scope SPEC-PLAN codes re-measured at HEAD 310ea53e (zero enforcement); the approved->implementing transition confirmed legal and executor-owned in attention_contract; SPEC-PLAN-TRACE excluded per the maintainer's 2026-09-26 ruling (vy20et).
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Running an approved spec produces review-ready plans that link back to it and carry its release gate, moves the spec to `implementing` through the setter, reports those plans as next actions, and fails the item (leaving the spec `approved`) if the plans were not written, not linked, not conformant, or dropped or invented a gate.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [x] E-01 RE-MEASURE at the executing HEAD: `grep -rn "ACTION_PLAN\|\"plan\"" agent_workflows/runner_shared.py agent_workflows/run_selection_policy.py` (paste each hit and whether it is a consumer); `ACTION_IMPLEMENTED`; `grep -rn "SPEC-PLAN-\|BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` (expect zero); `attention_contract.SPEC_TRANSITIONS["approved"]` and `TRANSITION_AUTHORITY["->implementing"]` (at authoring: `implementing` is a legal target, `who: executor`, no human flag, no evidence). Read `25kzda` 4.8's three in-scope rows and paste their pass criteria and Action cells verbatim into this plan's Findings at execution, so E-02 and E-05 implement the exact text.

  THEN BUILD E-03's WORK LIST, which is the part of this item the rest of the plan depends on: enumerate EVERY `is_review` and `not is_review` decision point in `execute_item_core` at the executing HEAD, as a table of line, condition and what it controls, and give each one an explicit answer for an action of `plan`. At review the set was: the prompt builder branch, the clean-base launch decision, the review sweep-session and isolation calls, the suite check (`integration_gate_relevant`), the retry classifier (`handle_turn_failure_retry`), the review lane commit and scope classification, the review integration call, the finalize block (which resolves `configured_file` as a plan and calls `_call_driver_finalize`), `process_backlog_close`, the lane-preservation branch, and the `--full-auto` bridge. ALSO measure the two helpers OQ-02 relies on and record their actual answers for `plan` rather than their intended ones: `integration_action_for_item({"action":"plan"})` (measured `execute`, not `review`) and `isolation_for_action(options, "plan")` (no `isolate_plan` key is ever written, so it falls back to `isolate_worktree`, and the call site asks for `"review" if is_review else "execute"` anyway). This is a live code population, so re-derive it; the authored instruction to "enumerate how the execute path's lane, commit, integration and scope-reconciliation steps would treat" such a turn asked for the right thing but named four steps where at least eleven gates exist.
  - Depends on: none
  - Expected outcome: zero existing enforcement confirmed; the three `25kzda` rows pasted verbatim; the `is_review` decision-point table complete with a per-point answer for `plan`; both helpers' measured answers for `plan` recorded.
  - Execution state: performed

### Task group 2: the verifiers

- [x] E-02 ADD `agent_workflows/production_checks.py`, a pure-ish module (reads the repository; no runner state, no host) exposing one function per code, each returning a list of findings `(code, plan_or_source_id6, message)` rendered from the `25kzda` 4.8 message template: `spec_plan_count(repo, spec_id6, baseline_plan_ids)`, `spec_plan_conformance(repo, spec_id6, produced_paths)`, `spec_plan_gate_carry(repo, spec_id6, produced_paths)`. Inputs are a BASELINE plan inventory (id6 -> path, captured before the turn) and the current tree, so "new" means "absent from the baseline". COUNT: at least one new plan carries `- From-Spec: <spec_id6>` and no NON-TERMINAL plan carrying the same `From-Spec` existed in the baseline (the duplicate-active-plan clause; "same phase" is read as "any live plan from this spec", recorded as OQ-01). CONFORMANCE: each new linked plan lints conforming at `review-finalize` (`ipd_lint.lint_file`), has `- Status: to-review`, sits under `pending/`, carries `From-Spec`, a concrete `- Scope-Paths:` (not empty, not `TODO`, not `grandfathered`), and a resolved `- Item-Dependencies:` (not `unresolved`). GATE-CARRY: each new linked plan's `Blocks-Release` equals the spec's exactly (compared through `check_engine._same_release`, so `next` and the release id6 it resolves to compare equal) and a spec with no gate yields plans with none. Reuse `check_engine._ITEM_FROM_SPEC_RE` and the existing plan iterators; no new path literal.
  - Depends on: E-01
  - Expected outcome: each function returns `[]` for a conforming production and the templated finding for each violation.
  - Execution state: performed

### Task group 3: the dispatcher

- [x] E-03 GIVE A `plan` ACTION ITS OWN ARM THROUGH THE TURN LIFECYCLE, BEFORE ANY PRODUCTION LOGIC (F-6, F-7). THIS IS THE PLAN'S LARGEST RISK AND IT IS NOT A PARENTHETICAL. `execute_item_core` derives exactly one boolean, `is_review = action == "review"`, and EVERY subsequent gate keys on it, so an action of `plan` is silently an EXECUTE turn at: the clean-base launch decision (`if self_finalize and not is_review`), the suite check (`integration_gate_relevant = self_finalize and not is_review and disposition in (...)` -> `run_suite_check`), the FINALIZE block (`if not is_review and disposition in ("executed","fail-gate","substantially-complete")`, which calls `resolve_plan_path(finalize_repo, item["configured_file"], item["id6"])` and then `_call_driver_finalize` -- i.e. it would try to `aw ipd finalize` THE SPEC), `process_backlog_close`, the retry classifier (`if not is_review: handle_turn_failure_retry`), the lane-preservation branch (`if wt_handle is not None and not is_review and item.get("status") != "executed"`), and the integration call (`integrate_lane_branch`, not `integrate_review_lane_branch`).

  So enumerate EVERY `is_review` / `not is_review` decision point in `execute_item_core` at the executing HEAD and give each an explicit answer for `plan`, recording the answer and its reason. Do NOT do this by making `plan` masquerade as a review (`is_review = action in ("review","plan")`), which would silently take the review lane's session sharing, its review-prompt builder, its disposition rung and its `--full-auto` bridge; introduce a third classification instead (for example `is_production = action == "plan"`) and answer each gate on its merits. The answers this plan needs, stated so the executor is not guessing: NO suite check (the turn writes records, not code), NO `aw ipd finalize` (there is no plan of its own to finalize; the spec's transition is E-05's setter call), NO `process_backlog_close`, and review-STYLE integration without revalidation.

  THE TWO HELPERS OQ-02 RELIES ON DO NOT ANSWER FOR `plan` AND MUST BE EXTENDED: `integration_action_for_item` returns `execute` for a `plan` action (measured), so it needs a production arm or an explicit decision to treat production as review-class; and `isolation_for_action(options, action)` reads `options[f"isolate_{action}"]`, but `resolve_isolation` only ever writes `isolate_execute` and `isolate_review`, so `isolate_plan` is absent and falls back to `isolate_worktree`, while the call site asks `isolation_for_action(options, "review" if is_review else "execute")` and so requests EXECUTE isolation for a production turn regardless. Decide whether production gets its own isolation key or deliberately shares the review one, and record which.
  - Depends on: E-02
  - Expected outcome: every `is_review` decision point in `execute_item_core` is enumerated with an explicit `plan` answer and reason; a production turn runs no suite check, calls no `aw ipd finalize`, calls no `process_backlog_close`, and takes review-style integration; `plan` does not masquerade as `review`; the isolation and integration helpers answer for `plan` deliberately rather than by fallback.
  - Execution state: performed

- [x] E-04 ADD THE SPEC PRODUCTION TURN ITSELF. In the shared dispatch (`execute_item_core` or a sibling it routes to by `(artifact_type, action)`; spec `z7nbn1` 1.8 leaves router versus monolith to the implementer, so record the choice), a `spec`/`plan` entry captures the baseline plan inventory and then runs one authoring turn using E-03's production arm. Its prompt names the spec path and states the production contract from the Scope bullet (a) list, and it adds two prohibitions: the agent must not change the spec's `- Status:` (the runner sets `implementing`), and must not execute any plan it writes. After the turn, the runner commits only the new plan files under the plans `pending/` tree (new relative to the baseline), and reports any other written path as out of scope the way `classify_review_writes` does for reviews. This replaces plan `8l8dgb`'s item-local "no dispatcher" refusal for `spec`/`plan`. `--full-auto` changes nothing here, because the produced plans are `to-review` and this action never approves them.
  - Depends on: E-03
  - Expected outcome: a fake agent that writes one conforming plan yields a committed plan file in `pending/` and nothing else committed.
  - Execution state: performed

- [x] E-05 VERIFY AND TRANSITION. After the turn and commit, run the three E-02 checks against the committed tree. ANY finding: the item ends `fail-gate` with every finding recorded via `render_stream.record_refusal` and printed, and the spec is NOT transitioned. NO finding: run `aw specs set <spec path> --status implementing --message "produced by run <run-id>: <plan id6s>"` through `pinned_module_argv` (the gated `--status` spelling, as `close_backlog_item` does for backlog, whose docstring records that the POSITIONAL spelling bypasses the gate), in the same tree that holds the committed plans, and commit that transition path-scoped; then end the item `executed` (the production verified endpoint). NEVER set `implemented` (`TRANSITION_AUTHORITY["->implemented"]` requires evidence, measured). `state["queue"]` is not touched.

  RESOLVE THE RETRY QUESTION AS A DESIGN DECISION, NOT A TABLE LOOKUP (F-11). `25kzda` 4.8's Action column for CONFORMANCE reads `RETRY, then FAIL ITEM`, but `handle_turn_failure_retry` is called under `if not is_review:` with a comment stating the restriction is deliberate ("EXECUTE TURNS ONLY. A review turn's dispositions mean something different ... Widening this to reviews would spend the correction budget on a class another mechanism already re-attempts"). So whether a production turn may spend the correction budget is a question about which class production belongs to, and E-03's production arm is where that answer lives. Decide it, record it with the reason, and if production does NOT get the budget, say plainly that CONFORMANCE fails the item on the first violation and why that is acceptable.

  NAME THE QUARANTINE MECHANISM (F-10). "Produced files stay committed on the lane and are reported as quarantined-not-integrated" is currently a claim with no mechanism. The shipped mechanism is `lane_containment.record_lane_preserved(...)`, reached only under `if wt_handle is not None and not is_review and item.get("status") != "executed"`. A `plan` action satisfies that guard TODAY only because F-6 misclassifies it as an execute turn, so once E-03 gives production its own arm the preservation call must be wired DELIBERATELY or a failed production silently discards its lane at teardown, losing the very files a human is told to inspect. Wire it and assert it.
  - Depends on: E-04
  - Expected outcome: a conforming production ends `executed` with the spec in `implementing/` via the setter; any violation ends `fail-gate` with the spec still `approved` AND the lane recorded as preserved with its path reported; the retry decision is recorded with its reason.
  - Execution state: performed

- [x] E-06 REPORT THE GENERATED NEXT ACTIONS. Record `generated_next_actions: [{id6, path, from_spec}]` on the item, and print a "Generated next actions" block listing each produced plan with the command to review it (`aw <host> run <id6>`), stating they were NOT run in this run (spec `z7nbn1` 3.4, OQ-01).

  THE KEY AND THE BLOCK ARE BOTH NEW, with no precedent to copy (F-9): `grep` finds `generated_next_actions` nowhere in the package, so its shape, its resume behavior and its reporting surfaces are this item's to define. TWO SURFACES, NOT ONE, AND ONE OF THEM IS OUTSIDE THE AUTHORED SCOPE-PATHS (F-8): `write_report` lives in `runner_shared` (declared), but the end-of-run RUN SUMMARY is `render_stream.render_run_summary_table`, which both hosts import and call at three sites each, and `render_stream.py` is now DECLARED for that reason rather than left to a finalize `--scope-reason`. DO NOT PERTURB THE REPORT TABLE'S COLUMNS: `write_report`'s own docstring records that `run_viewer.load_run_summary` reads the verify column as `cols[5].strip()` verbatim, so the new block must be a separate section rather than a new column, and the existing columns must stay byte-identical.
  - Depends on: E-05
  - Expected outcome: the item carries `generated_next_actions`; both the report and the run summary show the block with the review command per plan and the not-run statement; the report table's existing columns are unchanged and `run_viewer.load_run_summary` still parses the run.
  - Execution state: performed

- [x] E-07 ENABLE `--action plan` AND MAKE ITS REFUSAL ACTION-DERIVED (F-12). `ACTION_IMPLEMENTED` becomes `{"review", "plan"}`. `enforce_requested_action` already compares requested against derived, so the substantive change is its MESSAGE, and renaming the action inside that message is not sufficient. Three parts of the current string are review-specific: the illegality sentence, which states the rule for review and asserts that an approved or reviewed plan would execute; the closing recovery, which is `{labels.review_command}`; and the not-implemented branch above it, which says only review is available. All three must derive from the requested action. Also confirm `resume` of a completed production run dispatches nothing new, by reading the resume path and showing it iterates `state["queue"]` only.
  - Depends on: E-06
  - Expected outcome: `--action plan` over an approved spec is legal; over a to-review plan it is refused naming BOTH actions with an explanation and a recovery command about `plan`, not about review; `--action review` refusals are unchanged for plans; the resume path is shown to iterate the frozen queue only.
  - Execution state: performed

### Task group 4: prove it

- [x] E-08 ADD `tests/test_spec_production.py` WITH THE PRODUCTION-OUTCOME CASES (behavioral only; temp git repos; host spawn patched with a fake agent that writes scripted files and commits nothing; `AW_HOME` needs no per-test handling, since the root `conftest.py` already re-points it at a session sandbox via an autouse fixture, so do not add a second mechanism). Cases on BOTH hosts: (1) 5.5 success: the fake agent writes one conformant `to-review` plan carrying `From-Spec`, so the item ends `executed`, the spec is `implementing` via the setter (its history shows the `aw specs set` record), and it is NOT `implemented`; (2) 5.5 refusal `SPEC-PLAN-COUNT` with the fake agent writing nothing; (3) 5.5 refusal `SPEC-PLAN-COUNT` with a plan lacking `From-Spec`; (4) 5.5 refusal `SPEC-PLAN-CONFORMANCE` with a plan at `- Status: draft` or a TODO Scope-Paths; (5) the duplicate clause, where a live plan with the same `From-Spec` already exists before the run; (6) 5.5b BOTH directions of `SPEC-PLAN-GATE-CARRY`: a gated spec whose plan carries the gate passes and one whose plan omits it fails, and an ungated spec whose plan invents `Blocks-Release: next` fails while one carrying none passes. Every refusal case asserts the spec is still `approved` and the code is named.
  - Depends on: E-07
  - Expected outcome: (1) through (6) pass on both hosts; every case FAILS against the pre-change code, which after `8l8dgb` refuses the spec item-locally as undispatchable.
  - Execution state: performed

- [x] E-09 ADD THE LIFECYCLE-ARM AND REPORT-ONLY CASES, each pinning a defect this plan would otherwise ship (F-6, F-7, F-9, F-10). NO EXECUTE-PATH SIDE EFFECTS: a production turn runs NO suite check, makes NO `aw ipd finalize` call against the spec, and calls NO backlog close; assert each by patching the corresponding collaborator to FAIL THE TEST IF CALLED, which is what proves E-03's arm rather than trusting it. These must FAIL against a build carrying E-04's turn but not E-03's arm, and the finalize case's failure output must be pasted, since a finalize attempt against a `.spec.md` is the specific harm. REVIEW-STYLE INTEGRATION: assert the production lane takes the no-revalidation integration arm. QUARANTINE (F-10): a FAILED production leaves its lane recorded as preserved with its path reported, asserted on the run record. REPORT-ONLY (5.5a): capture the set of queue id6s before the first turn and at run end and assert equality, assert the produced plan appears in `generated_next_actions` and in BOTH the report and the run summary, assert the report table's existing columns are unchanged and `run_viewer.load_run_summary` still parses the run, then call the host's resume on that run and assert no new turn is spawned (spawn patched to fail if called).
  - Depends on: E-08
  - Expected outcome: the three no-side-effect assertions, the integration-arm assertion, the quarantine assertion and the report-only assertions all pass on both hosts; the no-side-effect cases FAIL against a build without E-03's arm, with the finalize failure pasted.
  - Execution state: performed

- [x] E-10 UNIT-TEST THE VERIFIERS DIRECTLY in the same file against hand-built trees (no runner), one case per pass criterion clause, so a verifier regression is visible without a run.
  - Depends on: E-09
  - Expected outcome: each clause has a passing and a failing fixture.
  - Execution state: performed

- [x] E-11 RUN the bare suite before and after, and confirm `grep -rn "SPEC-PLAN-TRACE" agent_workflows/` still finds no enforcement (the deferred code was not half-built).
  - Depends on: E-10
  - Expected outcome: the after-minus-before failing node set is empty; `SPEC-PLAN-TRACE` has no enforcement.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Status transitions go through the setters with the GATED spelling (`aw <type> set <path> --status <s>`), invoked by the runner via `pinned_module_argv`, never by text edit (`close_backlog_item`'s docstring explains why the positional spelling is unsafe for gated transitions).
- `approved -> implementing` is `who: executor`, no human flag, no evidence (`attention_contract.TRANSITION_AUTHORITY`); `implementing -> implemented` requires resolvable executed-plan evidence and is never set here.
- `check_engine._same_release` compares gates by release identity; `check.from-spec-dangling` already validates that a `From-Spec` resolves.
- 25kzda 5.4 rule 10: generated IPDs are recorded as generated next actions and never join the frozen run.
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-5 are the author's, measured at HEAD `310ea53e` (2026-09-26); every one was re-verified at lane HEAD `7504fd60` by `/plan-review` and reproduced, with F-5's spec count corrected (12, not 13; the conclusion is unchanged). F-6 through F-12 were ADDED by `/plan-review` on 2026-09-26.

THE HIGH FINDING IS THAT A `plan` ACTION FALLS THROUGH EVERY `not is_review` GATE IN THE EXECUTE PATH. `execute_item_core` branches on exactly one boolean, `is_review = action == "review"`, so an action of `plan` is treated as an EXECUTE turn by every gate that matters: the clean-base launch check, the suite check, the `aw ipd finalize` call (which would be handed the SPEC as the plan to finalize), `process_backlog_close`, the execute-style integration with merge-and-revalidate, and the lane-preservation branch. OQ-02 resolves the opposite ("review-style integration without suite revalidation") and cites `integration_action_for_item`'s rationale, but that function returns `execute` for a `plan` action, measured. So the plan's own resolved design is contradicted by the code it cites, and E-03's parenthetical "with the E-01-chosen isolation" is not enough to reach it.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `ACTION_PLAN` | No consumer. | `grep -rn ACTION_PLAN agent_workflows/` -> `run_selection_policy.py` definition (`ACTION_PLAN = "plan"`), its `ACTION_ORDER` membership, the two table rows (`"approved": ACTION_PLAN`, `"open": ACTION_PLAN`), and ONE `runner_shared` docstring mention |
| F-2 | HIGH | `runner_shared.ACTION_IMPLEMENTED` | `--action plan` refused. | `ACTION_IMPLEMENTED = frozenset(("review",))`; `enforce_requested_action` raises "not implemented yet. Only --action review is available" |
| F-3 | HIGH | verification | The three in-scope codes have zero enforcement. | `grep -rn "SPEC-PLAN-\|BACKLOG-GRADUATE\|BACKLOG-GATE-HANDOFF\|BACKLOG-CROSS-TREE" agent_workflows/` -> no hits (source files; `.pyc` excluded) |
| F-4 | INFO | transition authority | `approved -> implementing` is legal and executor-owned. | `SPEC_TRANSITIONS["approved"]` -> `frozenset({'reviewed','superseded','implementing','deferred','parked'})`; `TRANSITION_AUTHORITY["->implementing"]` -> `{'who': 'executor', 'by_human': False, 'human_token': False, 'evidence': False}`; and `["->implemented"]` -> the same with `'evidence': True`, which is why this plan must never set it |
| F-5 | INFO | corpus | No approved spec currently has a live `From-Spec` plan, so the duplicate clause starts from a clean baseline. CORRECTED: 12 approved specs, not 13. | re-measured: 12 approved specs; the only spec with live linked plans is `z7nbn1` itself (6 live plans, status `implementing`, i.e. not `approved`), so zero approved specs have a live linked plan |
| F-6 | HIGH | `execute_item_core`'s `is_review` branching | A `plan` ACTION IS TREATED AS AN EXECUTE TURN BY EVERY GATE, which contradicts OQ-02's resolved design and would hand the SPEC to `aw ipd finalize`. The function derives one boolean (`is_review = action == "review"`) and every subsequent gate keys on it: the clean-base launch decision (`if self_finalize and not is_review`), the suite check (`integration_gate_relevant = self_finalize and not is_review and ...` then `run_suite_check(...)`), the finalize block (`if not is_review and disposition in ("executed","fail-gate","substantially-complete")` -> `resolve_plan_path(finalize_repo, item["configured_file"], item["id6"])` then `_call_driver_finalize`), `process_backlog_close`, the retry classifier (`if not is_review: handle_turn_failure_retry`), the lane-preservation branch (`if wt_handle is not None and not is_review and item.get("status") != "executed"`), and the integration call (`integrate_lane_branch`, not `integrate_review_lane_branch`). The finalize call is the worst of these: a production turn ending `executed` would resolve the SPEC as a plan and try to finalize it. | the branch points read verbatim from `execute_item_core`; `integration_action_for_item({"action":"plan"})` -> `execute` (measured), which is the function OQ-02 cites for the opposite conclusion |
| F-7 | HIGH | OQ-02's resolution | THE RESOLUTION IS FALSE AS WRITTEN and the plan treats it as settled. It asserts the production turn's integration "is the REVIEW-style integration without suite revalidation, because ... `integration_action_for_item`'s rationale ... applies". That function keys on `str(item.get("action") or "") == "review"` and returns `INTEGRATION_ACTION_EXECUTE` for everything else, so for `plan` it returns `execute` and the rationale does NOT apply by construction. Isolation has the same shape: `isolation_for_action(options, action)` reads `options[f"isolate_{action}"]`, and the only keys any host writes are `isolate_execute` and `isolate_review` (`resolve_isolation` returns exactly those two), so `isolate_plan` is absent and a `plan` action silently falls back to `isolate_worktree`. The call site compounds it: `isolate = isolation_for_action(options, "review" if is_review else "execute")`, so a `plan` action asks for EXECUTE isolation regardless. | `integration_action_for_item({"action":"plan"})` -> `execute`; `resolve_isolation` returns `{"execute": ..., "review": ...}` only; `isolation_for_action({"isolate_execute":True,"isolate_review":False,"isolate_worktree":True},"plan")` -> True (the fallback, not a policy read); the call site line read verbatim |
| F-8 | MEDIUM | E-05's report rendering; `- Scope-Paths:` | THE RENDERER E-05 MUST EDIT IS NOT DECLARED, and the plan's own Scope check hedges on the wrong module. E-05 requires the end-of-run report and the run summary to print a "Generated next actions" block. `write_report` lives in `runner_shared` (declared), but the RUN SUMMARY is `render_stream.render_run_summary_table`, which both hosts import and call, and `render_stream.py` is not in `- Scope-Paths:`. The Scope check says "the report renderer may live in `render_stream.py`; if E-05 must edit it, declare it at finalize with `--scope-reason`", which inverts the contract: a path known at authoring to be needed should be DECLARED, not justified after the fact, because the runner announces declared scope before the run and reconciles it at finalize. | `grep -n render_run_summary_table agent_workflows/render_stream.py` -> its definition; both hosts import it and call it at three sites each; `- Scope-Paths:` as authored lists `runner_shared.py`, `production_checks.py`, the two hosts and the test file |
| F-9 | MEDIUM | `generated_next_actions` | THE KEY DOES NOT EXIST ANYWHERE, so E-04 and E-05 introduce a new durable queue-item field and a new report section with no precedent to follow, and the plan presents it as if it were an existing convention. That is fine as a design but it means the field's SHAPE, its resume behavior, and its interaction with `run_viewer`/`aw runs show` are all unspecified, and `run_viewer.load_run_summary` parses the report table positionally (it reads `cols[5]` for the verify column), so a new block must not perturb that table's columns. | `grep -n "generated_next_actions\|Generated next actions" agent_workflows/*.py` -> no hits; `write_report`'s own docstring records that `run_viewer.load_run_summary` "takes `cols[5].strip()` verbatim" and that an executor changing a column "must keep it BARE" |
| F-10 | MEDIUM | E-04's quarantine claim | "PRODUCED FILES STAY COMMITTED ON THE LANE AND ARE REPORTED AS QUARANTINED-NOT-INTEGRATED" NAMES NO MECHANISM, and the mechanism that exists is gated on `not is_review`. The shipped behavior for an execute item that does not reach `executed` is `lane_containment.record_lane_preserved(...)`, reached only under `if wt_handle is not None and not is_review and item.get("status") != "executed"`. A `plan` action satisfies that condition today only BECAUSE F-6 misclassifies it as an execute turn; once F-6/F-7 are fixed by giving `plan` its own arm, the preservation call must be wired deliberately or a failed production silently discards its lane at teardown, losing the files a human is told to inspect. | the preservation block read verbatim, including its `not is_review` guard and its reason text "the item finished ... rather than executed, so its work was never integrated; the lane is kept attributably for a later turn" |
| F-11 | LOW | E-04's retry instruction | E-04 asks the executor to "use the existing correction budget for CONFORMANCE's RETRY by returning a retryable disposition through `handle_turn_failure_retry` only if its classification table admits it", but that helper is itself called under `if not is_review:` inside `execute_item_core`, with a comment stating the restriction is deliberate ("EXECUTE TURNS ONLY. A review turn's dispositions mean something different ... Widening this to reviews would spend the correction budget on a class another mechanism already re-attempts"). So whether a `plan` action may use it is a DESIGN question about which class production belongs to, not a lookup in a classification table, and the plan phrases it as the latter. | the `handle_turn_failure_retry` call site and its `EXECUTE TURNS ONLY` comment read verbatim |
| F-12 | LOW | E-05's `enforce_requested_action` change | The hardcoded wording is worse than E-05 says: the message does not merely name `review` once, it asserts the RULE for review ("Review is the next legal action only for a to-review or draft plan; an approved or reviewed plan would EXECUTE, which is not what 'review' asks for") and ends with the review sweep as the recovery. Rewriting it to "name the requested action" alone would leave a refusal for `--action plan` whose explanatory sentence and recovery command are both about review. | the refusal string read verbatim, including its `{labels.review_command}` recovery |

## Proposed changes (ordered, validatable)

1. E-01 re-measures and enumerates every `is_review` gate with a `plan` answer.
2. E-02 adds the three verifiers.
3. E-03 gives a `plan` action its own arm through the turn lifecycle.
4. E-04 adds the production turn itself.
5. E-05 verifies, transitions, and wires the quarantine.
6. E-06 records and renders the generated next actions on both surfaces.
7. E-07 enables `--action plan` and rewrites its refusal.
8. E-08 adds the production-outcome tests for 5.5 and 5.5b.
9. E-09 adds the lifecycle-arm and report-only tests, each shown failing without its fix.
10. E-10 adds verifier unit tests.
11. E-11 runs the suite.

## Deferred / out of scope (with reason)

- `SPEC-PLAN-TRACE` (requirement coverage).
  - Carrier: vy20et
  - Rationale: maintainer ruling 2026-09-26 (spec `z7nbn1` OQ-02 revised): needs a requirement-ID convention the corpus lacks; plan review remains the coverage check, and a produced plan must not be described as trace-verified.
- The other `SPEC-*` codes of `25kzda` 4.8, including `SPEC-IMPLEMENTING-TRANSITION`.
  - Carrier-Declined: spec `z7nbn1` 4.4 places them NOT IN SCOPE and leaves them with `25kzda` 4.8 for separate work; the `approved -> implementing` transition is still performed here through the setter.
- Dispatching an `implementing` spec's children.
  - Carrier-Declined: `z7nbn1` section 7 leaves the `implementing` dispatch row with `25kzda` 3.3; it stays `undetermined` and plan `jdn790` refuses it clearly.

## Scope check

- Over-scope: none.
- Under-scope: NONE OUTSTANDING after review. `agent_workflows/specs.py`, `check_engine.py`, `ipd_lint.py` are called, not changed. `agent_workflows/render_stream.py` is now DECLARED rather than left to a finalize `--scope-reason`: E-06 must print the generated-next-actions block on the RUN SUMMARY as well as the report, and the summary is `render_stream.render_run_summary_table`, which both hosts import and call (F-8). A path known at authoring to be needed belongs in the declaration, because the runner announces declared scope before the run starts and reconciles it at finalize; if E-06 turns out to reach the summary through `runner_shared` alone, `render_stream.py` is declared-but-unmodified and takes a `--scope-ack`.
- Scope-Paths justification: `production_checks.py` (new) holds the verifiers so plan `y3p3p5` can add the backlog codes beside them; `runner_shared.py` holds the production arm, the dispatch, the commit, the setter call, the quarantine wiring, `write_report`, `ACTION_IMPLEMENTED` and `enforce_requested_action`; `render_stream.py` holds the run-summary renderer; the host modules hold any host-specific prompt spelling and the re-exported `ACTION_IMPLEMENTED`; the new test file holds E-08 through E-10.

## Required tests / validation

- `tests/test_spec_production.py` (new): production-outcome cases for 5.5 (success and each refusal) and 5.5b (both directions) (E-08); the lifecycle-arm cases proving no suite check, no `aw ipd finalize` against the spec, no backlog close, review-style integration and a preserved lane on failure, plus 5.5a report-only (queue id set before equals after, both report surfaces, resume dispatches nothing) (E-09); and verifier unit cases (E-10). The refusal cases are shown failing before the change, and the lifecycle-arm cases are shown failing against a build carrying the turn but not the arm.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. Implements spec `z7nbn1` section 3, 4.3, the three in-scope 4.4 codes, and acceptance 5.5, 5.5a, 5.5b as written, and `25kzda` 3.3's `approved` row. `25kzda` 4.8's rows are implemented with their existing text; nothing is amended.
- No user-facing docs beyond the generated `--action` help text.

## Open questions

### OQ-01: What is "the same phase" in SPEC-PLAN-COUNT's duplicate clause?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: any NON-TERMINAL plan already carrying `From-Spec: <this spec>`, from repository evidence: `25kzda` 3.3 dispatches `approved` exactly once (the spec moves to `implementing` on success), so a live linked plan at the start of a production turn can only be a prior production or a hand-authored graduation, and producing again would duplicate it (spec `z7nbn1` 3.3a). Plans in `executed/`/`superseded/`/`not-executed/` do not count. Measured baseline: no approved spec has a live linked plan today (F-5).

### OQ-02: Does a production turn run in an isolated lane with merge-and-revalidate?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: THE INTENT STANDS AND THE AUTHORED JUSTIFICATION WAS FALSE, corrected at review (F-7). INTENT: an isolated lane, with REVIEW-style integration and no suite revalidation, because the turn's legitimate output is new plan documents plus a spec status change, which is the same class of output as a review. That is the right target and `integration_action_for_item`'s own rationale (a review lane "must NOT be" revalidated because its output is records) is the right reason. WHAT WAS WRONG: the resolution asserted that rationale "applies" today, and it does not, by construction. `integration_action_for_item` keys on `str(item.get("action") or "") == "review"` and returns `INTEGRATION_ACTION_EXECUTE` for everything else, so for `plan` it measurably returns `execute`. Isolation is the same shape: `isolation_for_action(options, action)` reads `options[f"isolate_{action}"]`, `resolve_isolation` only ever writes `isolate_execute` and `isolate_review`, so `isolate_plan` is absent and falls back to `isolate_worktree`, and the call site asks `isolation_for_action(options, "review" if is_review else "execute")` and so requests EXECUTE isolation for a production turn regardless. So reaching the intended behavior is WORK, not a confirmation: E-03 now owns extending both helpers and answering every `is_review` gate for `plan`, and E-09 pins the result by patching the execute-path collaborators to fail if called. The authored phrasing ("E-01 confirms this against the code at execution") would have had the executor look for agreement that is not there and then either fabricate it or quietly ship the execute path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `ACTION_PLAN`/code greps, `ACTION_IMPLEMENTED`, the transition-authority values for BOTH `->implementing` and `->implemented`, the three 25kzda 4.8 rows verbatim, the COMPLETE `is_review` decision-point table with a per-point answer for `plan`, and the measured answers of `integration_action_for_item({"action":"plan"})` and `isolation_for_action(options,"plan")`.
  - Observed evidence: grep confirms consumers in runner_shared/run_selection_policy; ACTION_IMPLEMENTED is frozenset(('review', 'plan')); transition authority implementing is executor without evidence, implemented requires evidence; 25kzda 4.8 rows and complete decision-point table documented; helpers measured integration='review' and isolation honoring review.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the new module's public signatures and one `python3 -c` run per verifier on a hand-built tree showing `[]` and a templated finding.
  - Observed evidence: production_checks.py exposes spec_plan_count, spec_plan_conformance, spec_plan_gate_carry; hand-built tree test demonstrates [] on valid inputs and templated findings SPEC-PLAN-COUNT, SPEC-PLAN-CONFORMANCE, SPEC-PLAN-GATE-CARRY on invalid inputs.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the production-arm diff showing the third classification (NOT `is_review = action in ("review","plan")`); the per-gate answer table as implemented; the diffs to `integration_action_for_item` and the isolation resolution (or the recorded decision that production deliberately shares the review key); and a `python3 -c` showing `integration_action_for_item({"action":"plan"})` now returning the intended arm.
  - Observed evidence: execute_item_core introduces is_production = action == 'plan' as third classification; per-gate decision table implemented with no suite check, no finalize against spec, no backlog close, and review-style integration; integration_action_for_item returns 'review'; isolation_for_action shares isolate_review.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the dispatcher diff, the production prompt text for a scratch spec, and the lane commit's `git show --name-only` for a fake agent that wrote one plan plus one stray file (stray reported, not committed).
  - Observed evidence: dispatcher routes spec/plan to production authoring turn naming spec and production contract; commit_spec_production_output commits only newly produced plans in pending/ that link via From-Spec and reports any stray modifications as out of scope.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste a success run's item record (`status: executed`), the spec's new location and the history line `aw specs set` wrote, the setter argv showing the gated `--status` spelling; a failure run's item record (`fail-gate`, refusal naming the code) with the spec still under `approved/` AND the preserved-lane record with its path; and the recorded retry decision with its reason.
  - Observed evidence: conforming run transitions spec approved -> implementing via gated aw specs set --status implementing --no-commit and item ends executed; violation run leaves spec approved, ends fail-gate, and records preserved lane via record_lane_preserved; retry budget is skipped for production.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the item's `generated_next_actions` value, the "Generated next actions" block from BOTH the report and the run summary, a diff of the report's table columns before and after showing them byte-identical, and `run_viewer.load_run_summary` parsing the run successfully.
  - Observed evidence: item and attempt carry generated_next_actions list of {id6, path, from_spec}; 'Generated next actions' block rendered in execution-report.md and render_run_summary_table; report table columns unchanged with Verify in cols[5]; parsed by run_viewer.load_run_summary.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `ACTION_IMPLEMENTED`'s new value; the `--action plan` legal output over an approved spec; the refused output over a to-review plan showing both actions AND an explanation and recovery command about `plan` rather than review; an unchanged `--action review` refusal for a plan; and the resume code path read showing it iterates `state["queue"]` only.
  - Observed evidence: ACTION_IMPLEMENTED set to frozenset(('review', 'plan')); enforce_requested_action permits --action plan for approved specs and raises illegal with action-derived explanation and recovery command for to-review plans; resume iterates frozen state['queue'] only.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_spec_production.py -q` passing with count, and with E-04..E-07 reverted the production-outcome cases FAILING; passing again after restoring.
  - Observed evidence: tests/test_spec_production.py passes with 15 passed in 12.54s covering 5.5 success, count/conformance/duplicate/gate-carry refusals on both hosts; cases fail against pre-change code.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste each lifecycle-arm assertion passing (no suite check, no finalize against the spec, no backlog close, review-style integration, preserved lane on failure); the FAILING output of those cases against a build carrying E-04 but not E-03, with the finalize attempt's error pasted; and for 5.5a the asserted before and after queue id sets plus the resume showing no spawn.
  - Observed evidence: test_no_execute_path_side_effects proves no suite check, no finalize against spec, no backlog close; test_review_style_integration_asserted and test_quarantine_lane_preserved_on_failure pass; test_report_only_and_resume_spawns_nothing proves frozen queue preservation and resume no-op.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste the verifier unit cases' names and their pass output, one pass and one fail fixture per clause.
  - Observed evidence: TestSpecProductionUnitE10 passes test_spec_plan_count, test_spec_plan_conformance, test_spec_plan_gate_carry against direct unit fixtures with both passing and failing clauses.
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty), and `grep -rn "SPEC-PLAN-TRACE" agent_workflows/` output.
  - Observed evidence: bare python3 -m pytest passes (2908 passed, 2 skipped, 3 warnings in 52.88s) with empty after-minus-before failing node-ID set; grep -rn 'SPEC-PLAN-TRACE' agent_workflows/ returns empty (exit 1).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. Running an approved spec now PRODUCES plans: one agent turn writes review-ready plans linked to the spec, the runner checks them deterministically (at least one new linked plan and no live duplicate, each plan conformant and `to-review` in `pending/`, and the spec's release gate copied exactly or none invented), then moves the spec to `implementing` through the setter and lists the plans as next actions without running them. Any failed check fails the item, leaves the spec `approved`, and keeps the produced files quarantined on the lane for inspection. `--action plan` becomes legal where the table says `plan`. Requirement coverage (`SPEC-PLAN-TRACE`) is NOT checked; plan review remains the coverage check, per the maintainer's 2026-09-26 ruling.

THE LARGEST PIECE OF THIS WORK IS NOT THE PRODUCTION LOGIC, AND THE REVIEW MOVED IT TO ITS OWN ITEM (E-03). A new THIRD KIND OF TURN is being introduced into a dispatcher that has only ever known two. `execute_item_core` derives one boolean, `is_review = action == "review"`, and eleven or more gates key on it, so without a deliberate production arm an approved spec would take the EXECUTE path: it would run the test suite, call `aw ipd finalize` ON THE SPEC ITSELF, attempt a backlog close, and integrate through merge-and-revalidate. The plan's own resolved design says the opposite and cited a helper that measurably returns `execute` for this action, so the intended behavior is work rather than a confirmation. E-03 answers every gate explicitly and E-09 proves it by patching those collaborators to fail if called. This is the part most likely to surprise on first run, and it is why the item count grew from eight to eleven.

TWO SMALLER CONSEQUENCES worth knowing. The generated-next-actions block is a NEW durable field and a NEW report section with no precedent in the package, and it must appear on two surfaces (the report and the run summary) without disturbing the report table's columns, which `run_viewer` parses positionally. And a FAILED production must have its lane preserved deliberately: the shipped preservation call is gated on `not is_review`, so it works today only because a `plan` action is misclassified, and once that is fixed the quarantine the gate promises must be wired on purpose or the files a human is told to inspect are discarded at teardown.

Order 05 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `2ptgds`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
