# IPD: Split execute_item into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `execute_item` is written twice (1212 lines in `oc_runipd.py`, 1074 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 101 differing code lines of which only 8 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses. CORRECTED AT REVIEW 2026-09-16: the counts REPRODUCE (1212/1074 raw, 893/870 code, 101 differing under AST normalization, 7 host-token lines, similarity 0.851) and they measure the WRONG PROPERTY, exactly as siblings `i3d6ml` and `ty3cj6` did. Closure-measured, `execute_item` depends on 57 module-level names: 20 resolve in `runner_shared`, 37 do NOT, and EIGHTEEN of those 37 are functions still DEFINED TWICE, reached by 24 call sites in oc and 23 in agy. Sixteen of the eighteen are claimed by sibling child `i3d6ml`, which was itself re-scoped at review from 48 symbols to 9 and lifts only TWO of them. See F-6 through F-13 and OQ-03.
- Scope: Extract the host-neutral core of `execute_item` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: the split is GATED on OQ-03. It cannot be performed at this position in the Set without injecting eighteen dependencies and breaking fourteen source-inspection pins across ten test files, six of which assert ORDERING of the lane and integration gates and are therefore the very safety properties F-2 says must be proven still fail-closed.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_execute_item.py, tests/test_dirty_base_gate.py, tests/test_lane_clean_base.py, tests/test_lane_session_isolation.py, tests/test_lane_submission_collection.py, tests/test_defect_report.py, tests/test_lane_tool_identity.py, tests/test_run_flag_surface.py, tests/test_runner_backlog_close.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:ct4w0a
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 7
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: yrqyxb
- Approval: 2026-09-17, human ("approved"): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 13 findings (PR-001..PR-013), 11 FIXED, PR-001/PR-002 OPEN and escalated as blocking OQ-03. Every measurement REPRODUCES; liftability was never measured. 18 of the 37 unresolved closure names are still double-defined, and 14 source-inspection pins across 10 test files read this function's body, six of them asserting the ORDERING of the lane and integration gates.

- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-001 through PR-013 (11 FIXED, PR-001 and PR-002 OPEN and escalated as the new blocking OQ-03). THIS IS THE THIRD `rununify` CHILD IN A ROW WHOSE CENTRAL PREMISE INVERTED UNDER THE SAME TEST, and every number the plan states reproduced exactly: 1212 oc lines and 1074 agy; 893/870 code lines; 101 differing lines under AST normalization with docstrings stripped (SequenceMatcher similarity 0.851); 7 host-token lines, not 8, and the plan's "8" is off by one in its own favor. F-1's claim that `execute_item` is the largest symbol and the heart of the driver is CONFIRMED, and F-2's hazard is REAL and if anything understated: I counted SIXTEEN distinct safety gates inside it on each host (the clean-base guard and its shared decision, the tool-identity assertion, `driver_begin`/`driver_finalize`, worktree allocation, submission collection, defect-report validation, the suite check, `integration_is_earned`, `integrate_lane_branch`, `build_lane_outcome`, `record_integration_refusal`, `reconcile_disposition`, `sync_receipt_into_worktree`, `process_backlog_close`), all present identically on both hosts. THE BLOCKING DEFECT: body difference was measured, liftability inferred. `execute_item` closes over 57 module-level names; 20 resolve in `runner_shared`, 37 do not, and EIGHTEEN of the 37 are still DEFINED TWICE (`StallTimeout`, `_compute_scope_reconciliation`, `_record_checkpoint_stop`, `_record_forced_stop`, `attempt_log_path`, `build_prompt`, `build_review_prompt`, `build_verifier_prompt`, `driver_actor`, `driver_begin`, `driver_finalize`, `evaluate_clean_base_for_launch`, `make_integration_validation_runner`, `reconcile_disposition`, `route_recovery_turn`, `set_plan_approved`, `sync_receipt_into_worktree`, `write_prompt`), reached by 24 call sites in oc and 23 in agy. Two more (`extract_log_metrics`, `reask_prompt_path`) are not module-level at all: the first is a function-local import from `run_viewer`, the second a lambda parameter, so a naive closure list mistakes both. WORSE THAN THE SIBLINGS: FOURTEEN source-inspection pins across TEN test files read `execute_item`'s body (12 via `inspect.getsource`, 2 via an AST lookup by name, 2 via `source.split("def execute_item")`), and SIX assert the ORDERING of exactly the gates F-2 says must be proven still fail-closed, including `tests/test_lane_clean_base.py:172` and `tests/test_dirty_base_gate.py:781` which require `evaluate_clean_base_for_launch` to appear BEFORE the spawn and BEFORE `allocate_isolation_worktree`. A thin caller contains none of those strings, so all fourteen fail, and the honest repair is not mechanical: it decides whether an ordering guarantee this repository paid for twice becomes a behavioral assertion or is retired. I ran the ten files: 305 tests pass today. Also corrected: the plan's `Item-Dependencies: executed:ct4w0a` buys almost nothing (`ct4w0a` lifts `driver_begin` only, 1 of the 18), and the 16 symbols `i3d6ml` claims are mostly ones its own review already excluded, so the declared prerequisite chain does not actually clear this plan's path. One hazard I checked and CLEARED for the record: `execute_item` contains NO `subprocess` call site, so the nested-TTY stdin guard that blocks sibling `ct4w0a` does not apply here; the agent spawn lives in `run_opencode`/`run_agy_turn`. REVISED IN PLACE: closure table added to the Goal, gating E-01 added, the split converted to E-04 (a written analysis deliverable), E-05 added as a guard suite for what actually changed, all ten pin files fenced, F-6 through F-13 added, non-vacuity made bidirectional, and the `save_state` census (15 of 38 oc and 15 of 36 agy sites live inside this function) recorded. NOT DECIDED, deliberately: which of four routes the Set takes, since this is the largest symbol in the repository and every route restructures a Set with nine pending children.

- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a per-symbol diff measured at HEAD; the differing lines were counted and classified rather than estimated.

## Goal

Give `execute_item` ONE implementation of everything that is not host-specific, so a fix lands once and reaches
both hosts, without changing what either runner does.

RESTATED AT REVIEW 2026-09-16. The goal is right and the plan cannot reach it from this position. The
closure test, the same one that inverted siblings `i3d6ml` and `ty3cj6`, measured at HEAD `96db8545`:

| Closure class | Count | Consequence |
|---|---|---|
| Resolves in `runner_shared` today | 20 | moves for free |
| Constant, defined twice, values EQUAL | 2 (`DEFAULT_STALL_TIMEOUT`, `SUCCESS_STATES`) | can be lifted with the core |
| Already ONE object (agy imports it from oc, or both import a third module) | 11 (`StreamTracker`, `_STATUS_COLOR`, `execution_index`, `SuiteCheckResult`, `assert_child_tool_identity`, `integration_is_earned`, `run_suite_check`, `process_backlog_close`, `record_item_spec_edits`, `is_plan_review_approved`, plus the `functools`/`lane_containment`/`runner_stop`/`runner_shared` module handles) | needs relocation, not de-duplication |
| Genuinely host-specific, the intended hook | 1 (`run_opencode` / `run_agy_turn`) | this is F-3, and it is correct |
| NOT module-level at all (a false positive of a naive closure scan) | 2 (`extract_log_metrics`, a function-local import from `run_viewer`; `reask_prompt_path`, a lambda parameter) | must not be treated as a dependency |
| STILL DEFINED TWICE | 18 | each becomes an injected parameter, and injecting it is the opposite of sharing it |

The eighteen are `StallTimeout`, `_compute_scope_reconciliation`, `_record_checkpoint_stop`,
`_record_forced_stop`, `attempt_log_path`, `build_prompt`, `build_review_prompt`, `build_verifier_prompt`,
`driver_actor`, `driver_begin`, `driver_finalize`, `evaluate_clean_base_for_launch`,
`make_integration_validation_runner`, `reconcile_disposition`, `route_recovery_turn`, `set_plan_approved`,
`sync_receipt_into_worktree` and `write_prompt`, reached by 24 call sites in oc and 23 in agy.

So the honest goal for THIS plan, pending OQ-03, is: MEASURE the closure, PIN the behavior of the sixteen
safety gates this function owns, DELIVER the analysis the Set needs to sequence the split, and GUARD what
was measured, rather than perform a relocation whose shared core would take eighteen parameters and whose
landing would break fourteen pins including six that assert the ordering of those same gates.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

SCOPE GATE ADDED AT REVIEW 2026-09-16. E-01, E-02, E-03 and E-05 are authorized unconditionally: they
measure, they pin the gates, they enumerate the pins, and they guard what was measured. THE SPLIT ITSELF
IS GATED on OQ-03, which is `Blocking: yes`, so the lint gate refuses execution until the maintainer
answers; E-04 delivers the ANALYSIS that decision needs and performs no relocation.

### Task group 1: measure before touching

- [ ] E-01 MEASURE THE CLOSURE at execution HEAD, and refuse to proceed to E-04 on a stale list. The method is the one that inverted siblings `i3d6ml` and `ty3cj6`, and it is NOT the body-difference method this plan originally used: parse `oc_runipd.execute_item`, collect every free name that resolves at MODULE level, and classify each into the six classes of the Goal table. TWO TRAPS THE NAIVE SCAN FALLS INTO, both measured at review and both of which must be excluded rather than injected: `extract_log_metrics` is a FUNCTION-LOCAL import from `run_viewer` (`oc_runipd.py:7144`, `agy_runipd.py:3913`), and `reask_prompt_path` is a LAMBDA PARAMETER (`oc_runipd.py:7363`), so neither is a module-level dependency at all. Report the still-double-defined count and its call-site count per host. This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: a reproducible closure table with all 57 names classified, the two false positives excluded BY NAME, and the double-defined set stated with per-host call-site counts.
  - Execution state: pending

- [ ] E-02 PIN THE SIXTEEN SAFETY GATES, per the parent's constraint that no child may reconcile a symbol the characterization baseline has not pinned, and because F-2's hazard is the real one. Write characterization tests for `execute_item` on BOTH hosts covering every branch the split would move, following `tests/test_wtiso_characterization.py`. Measured at review, this function calls SIXTEEN distinct gates on each host: `evaluate_clean_base_for_launch`, `clean_base_launch_decision`, `assert_child_tool_identity`, `driver_begin`, `allocate_isolation_worktree`, `collect_lane_submissions`, `validate_defect_report`, `run_suite_check`, `integration_is_earned`, `build_lane_outcome`, `integrate_lane_branch`, `record_integration_refusal`, `reconcile_disposition`, `sync_receipt_into_worktree`, `driver_finalize`, `process_backlog_close`. Pin each as BEHAVIOR (does it still refuse when it should), not as source text, because source-text pins are what F-8 shows the split breaks. Prioritize agy branches with no existing coverage. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed characterization suite that passes against UNMODIFIED code, covers all sixteen gates on BOTH hosts, and would fail if any gate stopped refusing; the agy branches previously uncovered are named.
  - Execution state: pending

### Task group 2: the pin inventory

- [ ] E-03 ENUMERATE THE FOURTEEN SOURCE-INSPECTION PINS and state, per pin, whether a thin caller can satisfy it. F-8 lists them; the deliverable is the per-pin verdict plus, for each of the SIX that assert gate ORDERING, a statement of what behavioral assertion would preserve the same guarantee. This is not a rewrite: authority to rewrite a pin installed by an executed plan is part of OQ-03. Do NOT edit a test in this item. Run the ten files first and record the baseline (305 passed at review) so a later red is attributable.
  - Depends on: E-01
  - Expected outcome: a fourteen-row table (file:line, what it asserts, thin-caller verdict, and for the six ordering pins the behavioral equivalent that would replace it), plus the pasted green baseline of all ten files.
  - Execution state: pending

### Task group 3: the split, GATED

- [ ] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01 and E-03: (a) the eighteen dependencies a shared core would take, with each one's owning sibling child and whether that child actually lifts it (measured at review: `i3d6ml` names sixteen but its re-scoped groups A and B lift only `StallTimeout`, `build_review_prompt`, `make_integration_validation_runner`, `attempt_log_path`, `write_prompt` and `sync_receipt_into_worktree`; `ct4w0a` lifts `driver_begin`; so at best SEVEN of eighteen clear); (b) how many injections remain after the whole Set's other children execute, which decides whether this plan is merely EARLY or structurally infeasible; (c) the fourteen pins and the six ordering ones; and (d) a recommendation on route, with the reason. Change no runner logic in this item.
  - Depends on: E-01, E-03
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement, explicitly answering whether the remaining injection count after the Set completes is acceptable.
  - Execution state: pending

### Task group 4: proof

- [ ] E-05 Add `tests/test_rununify_execute_item.py` asserting WHAT THIS PLAN ACTUALLY DID, driven by a named table rather than by the aspiration: the closure classification E-01 measured is asserted mechanically (so a symbol silently changing class fails), the two false-positive names are asserted NOT to be module-level in either runner, and the eighteen double-defined symbols are asserted STILL double-defined (the inverse assertion, so a later agent cannot "complete" the split symbol by symbol without the OQ-03 decision). If OQ-03 authorizes the split, extend this file with the shared-core object identity, the repo-wide AST anti-re-fork scan (per the parent's F10, not a pairwise check), and a direct assertion of F-2's hazard; do NOT write those assertions while the split is ungated, because a test asserting a state the code is not in is a failing test, not a guard.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: a suite that fails if the closure regresses, if a false positive is mistaken for a dependency, or if a pinned double definition is unilaterally collapsed; and that does NOT assert an unexecuted split.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports no runner, so it
  can hold the core without a cycle. It already uses NAME/VALUE INJECTION for exactly this shape
  (`run_checked(..., env_builder=)`, `save_state(..., write_report=)`, `resume_via_launcher(launcher, ...)`),
  which is the pattern the hook should follow rather than a new mechanism.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner-to-runner
  import, so the core must land in `runner_shared` and never be reached by importing the other host.
  CORRECTED AT REVIEW: that guard is a SUBSTRING check for `"import oc_runipd"` /
  `"import agy_runipd"` (`tests/test_review_findings_cascade.py:308-313`), which agy's
  `from agent_workflows.oc_runipd import (...)` form does not match; agy uses that form TEN times, and
  ELEVEN of the names `execute_item` closes over are already single objects precisely BECAUSE agy imports
  them from oc. Do not cite this guard as evidence the coupling is absent. The rule that does hold is
  `runner_shared`'s own, asserted by AST at `tests/test_runner_shared.py:955`.
- FOURTEEN PINS READ THIS FUNCTION'S BODY, across ten test files, and six of them assert the ORDERING of
  the lane and integration gates. See F-8 for the enumeration. They pass today (305 tests across the ten
  files, measured at review), and a thin caller satisfies none of the fourteen.
- `tests/test_runner_shared.py:1148` (`test_no_call_site_was_rewritten`) counts `save_state` call sites
  per runner at 38 oc / 36 agy. FIFTEEN of each sit inside `execute_item`, so a split moves 39 percent of
  the counted population; the test's own rule requires a moved count be documented as a RELOCATION, as
  `RELOCATED_RUN_CHECKED_CALLERS` already does, never absorbed into a new literal.
- CLEARED FOR THE RECORD, so a later reader does not re-raise it: `execute_item` contains NO `subprocess`
  call site on either host, so the nested-`aw` stdin guard (`tests/test_nested_tty_noninteractive.py:172`,
  `:218`) that blocks sibling `ct4w0a` does NOT apply to this plan. The agent spawn is inside
  `run_opencode` (`oc_runipd.py:6219`) and `run_agy_turn` (`agy_runipd.py:3144`), which stay put.
- The parent Set forbids a child changing what a runner DOES, and forbids reconciling a symbol the
  characterization baseline has not pinned. E-01 exists to satisfy the second constraint.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | `execute_item` is the largest single symbol in either runner and the heart of the driver: it spawns the agent turn, watches the stream, collects submissions, runs the gates, and integrates the lane. It carries 101 changed code lines of which only EIGHT bear a host token, so the vast majority of its divergence is DRIFT in shared logic, not host specificity. VERIFIED AT REVIEW 2026-09-16 and it reproduces: 1212/1074 raw lines, 893/870 code lines, 101 differing lines under AST normalization with docstrings stripped, SequenceMatcher similarity 0.851. ONE CORRECTION: the host-token count is SEVEN, not eight (three `run_opencode`/`run_agy_turn` pairs plus one `aw agy run` message string), so the plan errs marginally in its own favor. The conclusion drawn from the number is nonetheless sound; what is unsound is inferring LIFTABILITY from it (F-6). |
| F-2 | HIGH | `execute_item`, both hosts | THE HAZARD THIS SPLIT CARRIES: This function performs the LANE TEARDOWN and the INTEGRATION. A defect here can destroy verified work or merge over a contaminated base, which is the failure this repo has already paid for twice. Every gate must be proven still fail-closed AFTER the split, not merely present. CONFIRMED AND UNDERSTATED AT REVIEW: I counted SIXTEEN distinct safety gates called inside this function, identically on both hosts: `evaluate_clean_base_for_launch`, `clean_base_launch_decision`, `assert_child_tool_identity`, `driver_begin`, `allocate_isolation_worktree`, `collect_lane_submissions`, `validate_defect_report`, `run_suite_check`, `integration_is_earned`, `build_lane_outcome`, `integrate_lane_branch`, `record_integration_refusal`, `reconcile_disposition`, `sync_receipt_into_worktree`, `driver_finalize`, `process_backlog_close`. E-02 now pins all sixteen as BEHAVIOR. The sharpest consequence is F-8's: six existing pins assert the ORDERING of these gates by reading this function's source text, so the split breaks the very guards that make this finding checkable. |
| F-3 | MED | `execute_item` | DIFFERENCE, the spawn: oc calls `run_opencode`, agy calls `run_agy_turn`. Genuinely host-specific and the natural hook boundary. |
| F-4 | MED | `execute_item` | DIFFERENCE, stream/event handling: each host parses its own event shape; host-specific. |
| F-5 | MED | `execute_item` | DIFFERENCE, everything else: worktree allocation, lane-input materialization, the clean-base gate, submission collection, the defect-report validation and re-ask, the suite check, the integration ladder, lifecycle begin/finalize. All shared logic that has drifted independently and is the real payoff of this split. VERIFIED AT REVIEW: correct as a description of the drift, and INCOMPLETE as a plan, because most of these are not inline logic but CALLS to the eighteen still-double-defined symbols of F-6. Unifying `execute_item`'s body does not unify them; it parameterizes them. |
| F-6 | BLOCKER | the plan's own method; closure measured at HEAD `96db8545` | **BODY DIFFERENCE WAS MEASURED, LIFTABILITY INFERRED,** the third `rununify` child in a row to make this exact error (`i3d6ml` F-7, `ty3cj6` F-8). A definition can move to `runner_shared` only if every module-level free name it closes over resolves there. `execute_item` closes over 57: 20 resolve, 37 do not, and EIGHTEEN of the 37 are functions STILL DEFINED TWICE, reached by 24 call sites in oc and 23 in agy. The promised "relocation with a parameter" is a relocation with EIGHTEEN parameters that de-duplicates none of the eighteen. |
| F-7 | HIGH | E-02's premise; the sibling children | **THE DECLARED PREREQUISITES DO NOT CLEAR THE PATH, and the plan assumes they do.** `Item-Dependencies: executed:ct4w0a` gains exactly ONE of the eighteen (`driver_begin`). Sibling `i3d6ml` NAMES sixteen of them, but it was re-scoped at its own review from 48 symbols to 9, and only SIX of the eighteen fall in its surviving groups A and B (`StallTimeout`, `build_review_prompt`, `make_integration_validation_runner`, `attempt_log_path`, `write_prompt`, `sync_receipt_into_worktree`). So even after every sibling executes as re-scoped, at least ELEVEN of the eighteen remain double-defined. That converts the question from "is this plan too early" to "is the Set's plan for this symbol achievable at all", which is why OQ-03 exists. |
| F-8 | BLOCKER | ten test files, fourteen pins | **FOURTEEN PINS READ `execute_item`'s BODY AND A THIN CALLER SATISFIES NONE, and SIX of them assert the ORDERING of F-2's safety gates.** Twelve read `inspect.getsource`, two do an AST lookup by function name, two use `source.split("def execute_item")`. THE SIX ORDERING PINS: `tests/test_lane_clean_base.py:172` and `tests/test_dirty_base_gate.py:781` both require `evaluate_clean_base_for_launch` to appear BEFORE the spawn call and BEFORE `allocate_isolation_worktree`; `tests/test_lane_tool_identity.py:695` requires `assert_child_tool_identity` before `driver_begin(`; `tests/test_lane_submission_collection.py:240` requires `collect_lane_submissions` before the `disposition` assignment; `tests/test_lane_session_isolation.py:125` requires the `set_sessions` promotion to sit under a `work_dir` guard (by AST); `tests/test_defect_report.py:809` requires the defect-report persistence block to contain no `raise`/status write/`driver_finalize`/`return`. THE OTHER EIGHT: `tests/test_dirty_base_gate.py:184` (must NOT contain `report_untracked_dirt_at_run_start`), `:357` and `:749` (`shared_tree=not isolate`), `:795` (`clean_base_launch_decision(` present, `CLEAN_BASE_REFUSE` absent), `tests/test_lane_clean_base.py:197` (`attempt["clean_base_dirty_paths"]`, `"event": "clean-base-refused"`), `tests/test_lane_session_isolation.py:167` (agy must clear `session_id` and `use_continue`), `tests/test_run_flag_surface.py:887` (`get("full_auto", False)` exactly), `tests/test_runner_backlog_close.py:1218` (`process_backlog_close(run_dir, state, item)` literal). ALSO `tests/test_lane_session_isolation.py:158` requires the literal string `xd9sll` in `agy.execute_item`'s source. All ten files pass today: 305 tests, measured at review. NONE was in `Scope-Paths`; all ten are now fenced. |
| F-9 | HIGH | E-02 as authored | **A NAIVE CLOSURE SCAN PRODUCES TWO FALSE DEPENDENCIES, and injecting either would be wrong.** `extract_log_metrics` appears to be a free name but is a FUNCTION-LOCAL import from `run_viewer` inside `execute_item` itself (`oc_runipd.py:7144`, `agy_runipd.py:3913`), deliberately local per `run_analytics_sources.py:646` ("it keeps module import order" unchanged). `reask_prompt_path` is a LAMBDA PARAMETER (`oc_runipd.py:7363`, `agy_runipd.py:4098`), not a module symbol at all. An executor mechanically injecting every unresolved name would add two parameters that must not exist and would move a deliberately-local import to module scope. E-01 now excludes both by name. |
| F-10 | MED | `tests/test_runner_shared.py:1148` | **THE SPLIT MOVES 39 PERCENT OF A PINNED CALL-SITE CENSUS.** `test_no_call_site_was_rewritten` expects 38 `save_state` sites in oc and 36 in agy (verified passing at review). FIFTEEN of each are inside `execute_item`. Its own documented rule forbids repairing a moved count by editing the literal; the correct treatment is a documented RELOCATION subtraction, as `RELOCATED_RUN_CHECKED_CALLERS` does for the six moved `run_checked` callers. The plan does not mention the test. |
| F-11 | MED | `DEFAULT_STALL_TIMEOUT`, `SUCCESS_STATES` | Two constants the function closes over are defined twice with EQUAL values (600.0, and the three-element status set). They are the easy half of the closure and can move with the core; stated so the executor does not treat all 37 unresolved names as equally hard. Contrast `ty3cj6`, where the analogous constant DIFFERED per host and had to become a hook input; here neither does. |
| F-12 | MED | E-02/E-03/E-04 right-sizing as authored | **ONE E-ITEM BUNDLED THE LARGEST RELOCATION IN THE REPOSITORY.** The original E-02 asked for a 1212-line function's core to be extracted, eighteen dependency decisions made, import rewiring done in files of 9,375 and 5,727 lines, and fourteen pins across ten files repaired, in one pass. `execute_item` also carries ELEVEN `try` blocks and four `return` statements per host, so its control flow does not decompose cleanly into a call with a parameter. A failure midway leaves the package unimportable. The count-based lint cannot see any of this. The re-scoped items are one measurement, one gate-pinning suite, one pin inventory, one written analysis, and one guard suite. |
| F-13 | LOW | `Size assessment: exception` | The exception is CORRECTLY claimed and its rationale is sound: this is the single largest symbol in either runner and the parent explicitly anticipates it needing a child to itself. Recorded because a reviewer should not flag it: the size exception is not the problem with this plan, the closure is. Note the re-scoped items are individually SMALL, so the exception now covers scope ambition rather than a single oversized pass. |

## Proposed changes (ordered, validatable)

1. Measure the CLOSURE at execution HEAD and classify all 57 names, excluding the two false
   positives by name (E-01).
2. Pin the sixteen safety gates as BEHAVIOR on both hosts (E-02).
3. Enumerate the fourteen source-inspection pins with a per-pin thin-caller verdict, and a behavioral
   equivalent for each of the six ordering pins (E-03).
4. Record the split analysis as a DELIVERABLE for OQ-03 rather than performing it (E-04).
5. Add the guard suite for what was measured, including the inverse assertions (E-05).

## Deferred / out of scope (with reason)

- The other four large functions of this Set, each owned by its own sibling child, because each is a
  distinct seam and the parent forbids a child exceeding one cohesive seam.
- The 48 no-disagreement symbols (child 03), the 8 host-string symbols (child 04), the two behavior
  conflicts (child 05), and the record type (child 06). All are ordered BEFORE this plan so their
  results are available rather than re-derived. CORRECTED AT REVIEW: child 03 was re-scoped to 9
  symbols, so those results are much thinner than this sentence assumes, and F-7 measures what actually
  clears.
- THE SPLIT ITSELF, deferred to OQ-03 rather than attempted. Stated plainly because a reader will
  otherwise assume it was forgotten: performing it today needs eighteen injected dependencies and breaks
  fourteen pins, six of which assert the ordering of the gates F-2 calls load-bearing. Both are decisions
  above this plan's authority.
- REWRITING ANY OF THE FOURTEEN PINS. E-03 produces the verdict and the behavioral equivalent; the
  authority to change a guard an executed plan installed belongs to the maintainer (OQ-03).
- Any behavior change, feature addition, or flag change. This plan as re-scoped changes NO product code
  at all: every item measures, pins, enumerates, analyses, or guards.

## Scope check

- Over-scope: none. As re-scoped this plan writes tests and analysis only; it modifies no product module.
  The ten added test paths are the pin files E-03 must READ and that a future split would have to edit,
  fenced now so the declaration is honest rather than discovered at finalize.
- Under-scope: this plan does not perform the split it is named for. That is deliberate and gated
  (OQ-03), not an omission: E-04's deliverable is the analysis the maintainer needs. It also does not
  attempt to shrink `execute_item`, which remains a legitimate later refactor and is arguably the
  PREREQUISITE for any split, since an 893-code-line function with eleven `try` blocks is hard to
  relocate whole.

## Required tests / validation

1. E-01's closure table, reproducible: a reader must be able to re-run the stated method and obtain the
   stated classification. State the HEAD. The two false positives (F-9) must appear as EXCLUSIONS with
   their `path:line`, not as dependencies.
2. The E-02 gate-pinning suite, green against UNMODIFIED code, covering all SIXTEEN gates on BOTH hosts.
   Both hosts' existing suites alone are NOT sufficient, because the parent measured them as asymmetric
   (95 oc tests versus 21 agy at the time), so an agy-side regression can hide behind green.
3. E-03's fourteen-row pin table, plus the pasted GREEN BASELINE of all ten pin files. Measured at review:
   `python3 -m pytest tests/test_dirty_base_gate.py tests/test_lane_clean_base.py
   tests/test_lane_session_isolation.py tests/test_lane_submission_collection.py tests/test_defect_report.py
   tests/test_lane_tool_identity.py tests/test_run_flag_surface.py tests/test_runner_backlog_close.py
   -o addopts=""` gave `305 passed`. Re-take it at execution HEAD; a divergence from 305 is information,
   not noise.
4. `tests/test_rununify_execute_item.py` (new): the closure classification asserted mechanically; the two
   false-positive names asserted NOT module-level in either runner; the eighteen double-defined symbols
   asserted STILL double-defined (the inverse assertion).
5. NON-VACUITY, BIDIRECTIONAL. Two controls, both pasted. (a) Reclassify one closure entry in the test's
   table to the wrong class and show the new suite FAILS, naming it; restore. (b) Move ONE of the eighteen
   double-defined symbols into `runner_shared` and show the inverse assertion FAILS; restore. A guard that
   only fails one way does not pin a boundary.
6. `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` green with its 38/36
   expectation unchanged (F-10), stated explicitly: this plan as re-scoped adds no `save_state` call site.
7. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
8. Bare `python3 -m pytest`, summary pasted, no new failure against a baseline taken at YOUR OWN HEAD
   before changing anything. Sibling `i3d6ml`'s review measured a load-dependent timeout that passes in
   isolation, so reproduce any single failure against the pre-change baseline before attributing it here.

## Spec / documentation sync

No `.spec.md` change expected: this is an internal refactor with no operator-visible contract change. IF
execution finds that a spec sentence describes the divergence being removed, amend it in the SAME change
and add the spec path to `Scope-Paths`, per the repository's spec-amendment rule.

REVIEWED 2026-09-16 AND CONFIRMED, strengthened in one respect. As re-scoped this plan changes NO product
code, so it cannot alter an operator-visible contract at all. But E-03's six ordering pins express
requirements that spec `c4gd2h` (the clean-base and lane-containment rules, cited as R5.4/R6.1 in
`tests/test_lane_clean_base.py`) and spec `7ckptx` state in prose. If OQ-03 later authorizes converting an
ordering pin to a behavioral assertion, THAT change touches a spec-governed guarantee and must carry the
spec amendment in the same change, with the spec path declared in `Scope-Paths`. Say so in E-04's analysis
so the maintainer sees the spec consequence before choosing a route.

## Open questions

### OQ-01: Where exactly does the hook boundary belong?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: At the points Findings names as genuinely host-specific, and nowhere
  else. The test is mechanical rather than aesthetic: if a candidate boundary would require the shared
  core to contain an `if host == ...` branch, the boundary is in the wrong place, because that branch is
  the duplication this Set exists to remove wearing a different shape.

### OQ-02: What if the split cannot be done without changing behavior?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5
- Resolution or deferral rationale: STOP AND REPORT rather than proceeding. The parent's hard constraint
  is that a child may not change behavior, and E-02's gate-pinning suite is what makes a violation
  visible instead of silent. A partial split that leaves a smaller shared core is an acceptable outcome
  and is strictly better than a complete split that moves behavior; say which branches were left behind
  and why. CONFIRMED AT REVIEW 2026-09-16, and THE CONDITION THIS QUESTION ANTICIPATED HAS OCCURRED. The
  measurements in F-6, F-7 and F-8 are the report; OQ-03 is the stop. So the re-scope below is this plan
  obeying its own instruction, not departing from it.

### OQ-03: The split needs eighteen injected dependencies and breaks fourteen pins, six of them gate-ordering. Which route does the Set take?

- Blocking: yes
- Finding: PR-001, PR-002
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-16, and the answer is ROUTE (A)
  AS THE OBJECTIVE, with the route's stated obstacles ruled to be work rather than blockers. The
  maintainer's directive, given directly: "at the end of the SET, there should be one code base shared
  by the two runners that contains 100% of the otherwise redundant code that currently is duplicated
  between the two runners." So DO THE SPLIT. Routes (C) and (D) are refused: both leave this function
  duplicated, which the directive forbids. Route (B)'s re-ordering is PERMITTED as a tactic (see below)
  but is not itself the answer, because it defers rather than achieves.
  THE TWO OBSTACLES THIS QUESTION RESTED ON WERE BOTH RULED ON DIRECTLY, and both dissolve:
  (1) TESTS ARE NOT IMMOVABLE. Asked whether the source-reading pins prevent this work, the maintainer's
  answer was that they do not, and this repository has ALREADY adapted such a guard for shared code:
  `tests/test_nested_tty_noninteractive.py:190-203` counts the shared file's launch sites toward BOTH
  runners, its docstring records why, and all 41 tests in that file plus `tests/test_lane_tool_identity.py`
  pass at this HEAD. A source-reading pin is therefore something to UPDATE DELIBERATELY as part of the
  work: re-base it on the code's new location, record what it now asserts, and prove it still catches the
  regression it was installed for (an injected-regression test, which several of these pins already have).
  WHAT REMAINS FORBIDDEN is WEAKENING a guard silently, i.e. lowering a threshold or deleting an assertion
  so a failure disappears. Re-basing is not weakening. Where a pin asserts the ORDER of safety gates, the
  ordering property must survive the move; assert it on the shared implementation, and if a behavioral
  assertion can replace a source-text one without losing coverage, prefer it and say so.
  (2) THE INJECTED-DEPENDENCY COUNT IS NOT A VETO, AND THE MECHANISM IS ALREADY RULED. This question
  treated N injected parameters as a reason to stop, and cited the maintainer's 2026-09-03 `818uru`
  OQ-02 ruling as being against it. That reads the ruling backwards. The ruling ESTABLISHED the
  mechanism to use: `runner_shared` owns the real function taking each outside dependency as an explicit
  PARAMETER, and each runner keeps a ONE-LINE wrapper at the ORIGINAL name and ORIGINAL signature that
  binds its own dependency (see the executed plan's E-02 note). What that ruling rejected was threading a
  parameter through ~86 CALL SITES, which the wrapper form specifically avoids. So a shared core with N
  parameters plus a thin per-host wrapper IS the sanctioned form, not a violation of it.
  (3) SIBLING COUPLING IS NOT A BLOCKER EITHER. The maintainer confirmed directly that many functions may
  be de-duplicated together before testing, so a dependency that is still double-defined because a SIBLING
  has not landed is to be handled by doing the work in dependency order within the Set, not by refusing.
  Where this plan's dependency count falls materially once a sibling lands, run in that order (route (B)'s
  tactic) and say so in the execution note; where it does not, inject and wrap per (2).
  HOW TO SEQUENCE, since every one of these five children asked the same question: the runner already
  sorts by dependency depth and re-checks dependencies at dispatch, so declared `Item-Dependencies` are
  sufficient to order the work. Do not re-order plans by hand.
  THE ORIGINAL REVIEWER'S MEASUREMENT BELOW IS PRESERVED and E-01 must reproduce it at execution HEAD;
  only its CONCLUSION (that a route decision was owed by the maintainer) is superseded.
  --- original analysis, superseded as to its conclusion ---
  NOT DECIDED, deliberately. This is the largest symbol in the
  repository and every route restructures a Set with nine pending children and an approved orchestrator,
  which is a scope-and-sequencing call the maintainer owns.
  THE MEASUREMENT, not an opinion. `execute_item` closes over 57 module-level names: 20 resolve in
  `runner_shared`, 18 are still DEFINED TWICE (24 call sites in oc, 23 in agy), and 2 are false positives
  a naive scan invents (F-9). After every sibling executes AS RE-SCOPED, at least ELEVEN of the eighteen
  remain double-defined (F-7), so this is not merely an ordering problem. Separately, FOURTEEN pins across
  ten files read this function's body and a thin caller satisfies none; SIX of them assert the ORDERING of
  the clean-base guard, the tool-identity check, submission collection and the defect-report block, which
  are the safety properties F-2 exists to protect. And the split moves 15 of 38 and 15 of 36 pinned
  `save_state` sites (F-10).
  FOUR ROUTES, with what each costs. (A) INJECT ALL EIGHTEEN now: one shared core, taking eighteen
  parameters, de-duplicating none of them, and requiring fourteen pin repairs including six ordering
  guards; contradicts the maintainer's `818uru` OQ-02 ruling, which chose thin wrappers over uniform
  injection at far smaller scale. (B) SHRINK FIRST, THEN SPLIT: extract cohesive blocks of `execute_item`
  (the clean-base preflight, the submission-and-disposition block, the integration block) into named
  shared helpers one at a time, each with its own pins converted to behavioral assertions, and let the
  residual `execute_item` become thin as a CONSEQUENCE rather than as a step. Slower, and each slice is
  independently verifiable, and it is the only route that does not require a single change to break
  fourteen guards at once. (C) RE-ORDER this plan LAST in the Set, after 08 through 11, so the maximum
  number of the eighteen have been lifted; costs a Set re-ordering and F-7 shows it still leaves eleven.
  (D) DO NOT SPLIT `execute_item`: accept that the largest and most safety-critical symbol stays
  duplicated, and spend the Set's remaining effort on the four smaller functions.
  RECOMMENDATION: (B). It is the only route whose steps are individually small, individually verifiable,
  and individually revertible, and it converts the pin problem from "fourteen at once" into "two or three
  per slice, each with a behavioral replacement written deliberately". (A) is not recommended. (C) helps
  marginally and does not resolve the structural issue. (D) is defensible and should be said out loud
  rather than reached by attrition, because a Set that unifies four of five large functions and RECORDS
  why the fifth stayed is a better outcome than one that forces the fifth through eighteen injections.
  THIS PLAN'S E-01 THROUGH E-05 ARE EXECUTABLE UNDER EVERY ROUTE, including (D), and E-04's analysis is
  exactly what the decision needs; only the split is gated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted closure table with all 57 names classified into the six classes, the command or script that produced it, and the HEAD. Must state the still-double-defined count with per-host call-site counts, and must list `extract_log_metrics` and `reask_prompt_path` as EXCLUSIONS with their `path:line` and the reason each is not a module-level dependency. A table that repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted green run of the gate-pinning suite against UNMODIFIED code, with all SIXTEEN gates covered on BOTH hosts and each gate named in the output or the report; plus the list of agy branches it newly covers; plus a sabotage of ONE gate showing the suite FAILS and names that gate (a characterization test that cannot fail pins nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the fourteen-row pin table (file:line, what it asserts, thin-caller verdict), with a behavioral equivalent stated for each of the SIX ordering pins; plus the pasted green baseline of all ten pin files with its count, compared against the 305 measured at review. Explicit confirmation that NO test file was edited by this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the written analysis, covering parts (a) through (d) E-04 enumerates, and specifically ANSWERING whether the residual injection count after the whole Set completes is acceptable, with the per-symbol accounting that supports the number. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_execute_item.py -o addopts=""` green, including the inverse eighteen-still-double-defined assertion. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 5, both directions shown failing and then restored. (c) `test_no_call_site_was_rewritten` green at 38/36 (F-10). (d) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, plus both hosts' suites and all ten pin files green by name.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one cohesive seam: the single largest symbol in either runner, split at its spawn boundary. The parent explicitly anticipates that this function "may need a child to itself". SUSTAINED AT REVIEW 2026-09-16 (F-13): the exception is correctly claimed. Note that as re-scoped the five items are individually small and test-only, so the exception now covers the ambition of the SEAM rather than the size of any one pass.

OPEN QUESTION GATE. OQ-03 is `Blocking: yes` and OPEN. `aw ipd lint` refuses this plan at every checkpoint
until the maintainer answers it, which is intended: THE SPLIT is not executable on this plan's own
authority. E-01 through E-05 are all authorized unconditionally, because E-04 delivers the ANALYSIS the
decision needs rather than performing the relocation.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`; do NOT add
`-n0`, a second `-q`, or `-p no:randomly`. The `Scope-Paths` fence is a DECLARATION so the runner can tell
afterwards whether an out-of-scope file was edited or an in-scope file was not: an out-of-scope edit is
made and then JUSTIFIED at finalize with a `--scope-reason`, and a declared-but-unmodified path needs a
`--scope-ack`. EXPECT TO ACK THE TEN PIN FILES: E-03 READS them and must not edit them, so they will be
declared-but-unmodified by design.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, REWRITTEN 2026-09-16 because the original pointed at an item that no
longer performs the split: F-6's closure measurement (the reason this plan is NO-GO), F-8's fourteen pins
and especially the SIX that assert gate ORDERING (these are the ones no characterization suite can rescue,
because they assert on source text rather than behavior), and F-7's finding that at least eleven of the
eighteen injections survive the whole Set, which is what makes this a design question rather than a
sequencing one.
