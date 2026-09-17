# IPD: Split run_queue into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `run_queue` is written twice (381 lines in `oc_runipd.py`, 336 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 12 differing code lines of which only 2 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses. CORRECTED AT REVIEW 2026-09-16: "12 differing lines" is TRUE and is NOT a measure of liftability, and this plan conflated the two exactly as sibling `i3d6ml` did. Measured with the CLOSURE test, `run_queue` closes over 41 module-level names of which only 14 resolve in `runner_shared` and 27 do NOT; 11 of those 27 are functions that are still DEFINED TWICE (`execute_item`, `retry_deferred_integrations`, `reconcile_interrupted`, `requeue_interrupted`, `reclaim_lanes_on_interrupt`, `_observe_between_turn_stop`, `_record_deliberate_stop`, `render_continuation_hint`, `write_report`, `driver_actor`, `disable_lane_prompt`) and one of them (`disable_lane_prompt`) is pinned PERMANENTLY unmovable. So the shared core cannot be a relocation: it must take a dozen injected dependencies, and every one it takes it also FAILS to de-duplicate. See F-8 through F-14 and OQ-03.
- Scope: Extract the host-neutral core of `run_queue` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: this plan may not execute as a split until the maintainer decides OQ-03, because the split cannot be performed at this point in the Set without either injecting a dozen dependencies (a shape the maintainer already ruled against at scale) or breaking three source-inspection pins that four other plans installed. E-05 is the deliverable this plan can honestly produce today.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_run_queue.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py, tests/test_lane_tool_identity.py, tests/test_runner_backlog_close.py, tests/test_runner_shared.py, tests/test_runner_stop.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:i3d6ml
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 8
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: ty3cj6
- Approval: 2026-09-17, human ("approved"): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- From-Backlog: alw22r

## Workflow history
- 2026-09-17 executed E-01..E-05 in lane `aw/lane/ty3cj6` from HEAD `24932638` (opencode/its_direct-pt3-claude-opus-5-1m-us): MEASURE-AND-REPAIR, NO SPLIT, per the plan's own scope gate and E-04. THREE FILES: agy gains E-03's two `register_signal_report` refreshes (3 -> 5 sites, matching oc site for site), plus `tests/test_rununify_run_queue_characterization.py` (35 tests, both hosts) and `tests/test_rununify_run_queue.py` (32 tests). Bare suite `32 failed, 7583 passed` against a pre-change baseline of `32 failed, 7516 passed` at the same HEAD, failure sets BYTE-IDENTICAL (the 32 are the `AW_EXECUTION_ROLE=worker` lifecycle-role guard; with the role unset, pre-change is `7548 passed, 0 failed`). FIVE THINGS A READER SHOULD NOT HAVE TO FIND IN THE DIFF. FIRST, A LIVE SAFETY-GATE DEFECT WAS FOUND AND IS NOT FIXED HERE: `run_queue`'s `except ToolIdentityError` clause swallows a documented RUN-FATAL error on BOTH hosts (its own comment says "Re-raise to abort the whole run"; there is no `raise`). It was authored WITH one at `b04c70ce` and lost in merge `04a613aa`, whose first parent had it and whose second lacked the clause. Because `execute_item` writes `item["status"] = "running"` BEFORE the identity check, a real mismatch dispatches EVERY remaining item under the same wrong control plane and strands each at a non-terminal status; `tests/test_lane_tool_identity.py` is green on it because its pin only checks clause ORDER in source text. Pinned as three tests whose docstrings order their own deletion when the `raise` returns, filed as backlog `mo3h5b` (high/bug), and left unfixed because restoring the `raise` changes control flow on both runners' run-fatal path, which is outside this plan's declared scope (decision `09-ty3cj6-D4`, escalated to the human). SECOND, EVERY NUMBER THE PLAN STATES REPRODUCED EXACTLY, the first child of this Set for which nothing moved: 41 closure names, 11 still double-defined, 12 differing code lines, 2 host-token. THIRD, ONE GUARD WAS VACUOUS IN ITS FIRST VERSION and the fix is the interesting part: comparing published item STATUSES cannot fail under a test stub (the stub mutates the very dict the loop holds), so the F-9 test passed on the defective host; OBJECT IDENTITY (`published() is state`) is the property that discriminates, measuring True on oc and False on agy (decision `09-ty3cj6-D2`). FOURTH, THE OBVIOUS PROPERTY-RULE WAS WRONG AND OC PROVED IT: "every `state = load_state` in the loop must refresh" reported four violations on the CORRECT host, all on paths that break out and reach the end-of-run refresh, so the rule is scoped to reloads after which the loop CONTINUES and the end-of-run refresh those paths depend on is pinned separately (decision `09-ty3cj6-D3`). FIFTH, E-04 FOUND THE ACTIONABLE PART THE PLAN MISSED: nine of the eleven forks survive the whole Set (only `tx6q0h` lifts any, and it lifts two while REFUSING `driver_actor` on measured grounds), but FOUR of the seven unclaimed forks are CLOSURE-CLEAN TODAY and liftable now without `run_queue` moving, one of them 69 code lines on both hosts differing by TWO; filed as backlog `5jsjnr`. Pin inventory re-measured at 10 sites across 9 files (plan says six), 8 breaking on a thin caller, and every pin file was already fenced. Non-vacuity shown BIDIRECTIONALLY plus a third suite-scale control (E-03 reverted with tests kept: 5 guards fire, everything else green). `aw ipd lint --phase pre-transition` conforms; no push. NOT SELF-FINALIZED: this ran in a managed worker lane (`AW_EXECUTION_ROLE=worker`), where `ipd_lifecycle` refuses driver-only lifecycle verbs, so the driver owns the terminal transition.
- 2026-09-17 approved (aw set, --by-human): Maintainer directive 2026-09-16: the objective is 100% de-duplication of the redundant code between the two runners; readiness attested by the maintainer (not by an agent, not by a review), with the two supporting rulings (source-reading guards are re-based deliberately, never weakened silently; coordinated de-duplication across symbols is permitted) recorded in each plan's OQ-03 and history
- 2026-09-16 reviewed (maintainer, --by-human attestation via askme): MAINTAINER ATTESTATION 2026-09-16: readiness set to `go-pending-approval` BY THE MAINTAINER, not by an agent and not by a review. The prior `no-go` was written by this plan's own 2026-09-16 review round while its blocking OQ-03 was genuinely open. The maintainer then answered that question directly in an interactive session on 2026-09-16 with a single Set-wide directive ('at the end of the SET, there should be one code base shared by the two runners that contains 100% of the otherwise redundant code that currently is duplicated between the two runners'), plus two supporting rulings that dissolved the premises the finding rested on: TESTS ARE NOT IMMOVABLE (a source-reading guard is re-based deliberately as part of the work, never weakened silently; the maintainer cited this repository's own precedent at `tests/test_nested_tty_noninteractive.py:190-203`, whose 41 related tests pass at this HEAD) and COORDINATED DE-DUPLICATION IS PERMITTED (many functions may be de-duplicated together before testing, so a still-double-defined dependency is an ordering matter rather than a blocker). Asked directly how the stale verdict should be cleared, the maintainer chose to attest it themselves rather than fund a further review round. THE ALTERNATIVE WAS PRICED AND REJECTED ON EVIDENCE: the 2026-09-16 round cost roughly 2.5 hours across nine items and produced 1,479 lines of review prose while clearing nothing, and the comparable 2026-09-13 round cost $106.07 and raised four NEW blocking questions, so a further round was not expected to yield a clean sheet. NO AGENT WROTE THIS VALUE ON ITS OWN AUTHORITY. HONEST LIMIT: no independent reviewer re-examined this plan's contents; that assurance lives in the 2026-09-16 round 1 record, not in this attestation. Recorded here because the auto-approve predicate reads this field FIRST (`plan_readiness.is_plan_review_approved`), so a stale `no-go` is a live refusal that would have silently skipped this plan when the Set executed.
- 2026-09-16 reviewed (aw set): Reviewed 2026-09-16 by /plan-review: REVIEWED - OPEN QUESTIONS, NO-GO. 11 findings (PR-001..PR-011), 9 FIXED, PR-001/PR-002 OPEN and escalated as blocking OQ-03. The plan's 12-differing-line measurement REPRODUCES exactly, but liftability was never measured: `run_queue` closes over 27 names absent from `runner_shared`, 11 of them still double-defined, so the "relocation with a parameter" it promises is a twelve-parameter injection.

- 2026-09-16 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO; PR-001 through PR-011 (9 FIXED, PR-001 and PR-002 OPEN and escalated as the new blocking OQ-03). EVERY NUMBER THE PLAN STATES REPRODUCED and its reasoning about DIFFERENCES is sound: 381/336 lines, 229/227 code lines, exactly 12 differing code lines, exactly 2 bearing a host token, and all seven enumerated differences are real and correctly classified. F-2's hazard is real but its PREMISE IS FALSE IN THE DIRECTION THAT MATTERS: `register_signal_report` is NOT oc-only, `agy_runipd.py:343` imports it and `oc.register_signal_report is agy.register_signal_report` is True today, so the plan's headline hazard ("must become a capability the descriptor declares") describes work already done; the REAL asymmetry is the CALL COUNT (oc calls it 5 times inside `run_queue`, agy 3), which is a genuine agy defect the plan does not name: agy skips the refresh after both integration-ladder state reloads, so a signal arriving there reports from a pre-reload snapshot. THE BLOCKING DEFECT is the same class that reversed sibling `i3d6ml`: the plan measured BODY DIFFERENCE and inferred LIFTABILITY. Closure-measured at HEAD `34aa40c0`, `run_queue` closes over 41 module-level names; 14 resolve in `runner_shared`, 27 do not, and 11 of the 27 are functions still DEFINED TWICE (`execute_item`, `retry_deferred_integrations`, `reconcile_interrupted`, `requeue_interrupted`, `reclaim_lanes_on_interrupt`, `_observe_between_turn_stop`, `_record_deliberate_stop`, `render_continuation_hint`, `write_report`, `driver_actor`, `disable_lane_prompt`), one of which (`disable_lane_prompt`) is pinned PERMANENTLY unmovable by `UnmovableSymbolTests` and can therefore never resolve. Also found: THREE SOURCE-INSPECTION PINS read `inspect.getsource(module.run_queue)` and assert substrings that a thin caller would no longer contain (`tests/test_runner_backlog_close.py:1228`, `tests/test_oc_runipd_cli.py:233`, `tests/test_agy_runipd_cli.py:1465`), plus three more that parse its source or count its call sites (`tests/test_lane_tool_identity.py:666`, `tests/test_runner_stop.py:607`, `tests/test_runner_shared.py:3234`/`:3270`), and `tests/test_orchestrator_retirement.py:3483` requires an `orchestrate` branch to remain in agy's OWN `run_queue` AST; none of the seven files was fenced. And `test_no_call_site_was_rewritten` counts `save_state` call sites per runner (38 oc / 36 agy, verified passing), of which 13 per host are inside `run_queue`, so the split moves a third of the counted population and the wrapper-ruling measurement fails unless the plan accounts for it. REVISED IN PLACE: the false hazard corrected, the closure measurement added as a gating E-01, the seven test files fenced, the six pins enumerated for the executor, non-vacuity made bidirectional, and E-05 added as the deliverable this plan can honestly produce today. NOT DECIDED, deliberately: whether to inject twelve dependencies, to re-order this plan behind the eleven, or to reduce the scope to the two-line host-token parameterization, since each restructures a Set with nine pending children.

- 2026-09-15 to-review (aw set): Authored 2026-09-15 from a fresh measurement at HEAD; resolves part of the rununify parent's placeholder child rows per the maintainer's 2026-09-14 oc-preferred ruling.

- 2026-09-15 draft (opencode/its_direct-pt3-claude-opus-5): created.
- 2026-09-15 authored (opencode/its_direct-pt3-claude-opus-5): authored from a per-symbol diff measured at HEAD; the differing lines were counted and classified rather than estimated.

## Goal

Give `run_queue` ONE implementation of everything that is not host-specific, so a fix lands once and reaches
both hosts, without changing what either runner does.

RESTATED AT REVIEW 2026-09-16, because the original goal is not achievable at this point in the Set and
the reason is measurable rather than aesthetic. `run_queue` is a DISPATCH LOOP: its body is almost
entirely calls to other symbols, so its "12 differing code lines" measure how little the two LOOPS
disagree and say nothing about whether the loop can move. The closure test says it cannot yet:

| Closure class | Count | Consequence |
|---|---|---|
| Resolves in `runner_shared` today | 14 | moves for free |
| Constant, defined twice, values EQUAL | 3 (`SUCCESS_STATES`, `EXECUTION_SUCCESS_STATES`, `TERMINAL_STATES`) | can be lifted with the loop |
| Constant, defined twice, values DIFFER by host | 1 (`DEPENDENCY_BLOCK_RECOVERY_HINT`) | must become a hook input |
| Already ONE object, imported by agy from oc | 8 (`ToolIdentityError`, `queue_sort_key`, `update_execution_order`, `cascade_dependency_blocked`, `dependency_status`, `dependency_status_detailed`, `report_run_spec_edits`, `register_signal_report`, `emit_shutdown_report`, `StreamTracker`) | needs relocation to `runner_shared`, not de-duplication |
| STILL DEFINED TWICE | 11 | each is an injected parameter, and injecting it is the opposite of sharing it |
| PINNED UNMOVABLE, permanently | 1 (`disable_lane_prompt`) | can NEVER resolve in `runner_shared`; injection is the only route, forever |

14 + 3 + 1 + 8 + 11 = 37, plus `Path`/`sys`/`time`/`contextlib` already counted in the 14; the arithmetic
is reproducible by E-01's method and is what E-01 must re-derive rather than trust.

So the honest goal for THIS plan, pending OQ-03, is: MEASURE the closure, FIX the one real defect the
measurement exposed (agy's two missing `register_signal_report` refreshes, F-9), and DELIVER the
sequencing analysis the Set needs, rather than perform a split whose shared core would carry twelve
parameters and still leave eleven symbols duplicated.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

SCOPE GATE ADDED AT REVIEW 2026-09-16. E-01, E-02, E-03 and E-05 are authorized unconditionally: they
measure, they pin current behavior, they repair a defect that exists independently of any split, and they
guard what changed. THE SPLIT ITSELF IS GATED on OQ-03, which is `Blocking: yes`, so the lint gate refuses
execution until the maintainer answers; E-04's deliverable is the ANALYSIS that decision needs, and it
performs no relocation.

### Task group 1: measure before touching

- [x] E-01 MEASURE THE CLOSURE at execution HEAD, and refuse to proceed to E-04 on a stale list. The method is the one that reversed sibling `i3d6ml`, and it is NOT the body-difference method this plan originally used: parse `oc_runipd.run_queue`, collect every free name that resolves at MODULE level, and classify each into the six classes of the Goal table (resolves in `runner_shared`; equal constant; host-divergent constant; already-one-object-via-import; still double-defined; pinned unmovable). Emit the table with its members and name any symbol whose class changed since 2026-09-16. This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: a reproducible closure table in the execution report with all 41 names classified; the count of still-double-defined names stated; `disable_lane_prompt`'s permanent-injection status confirmed or refuted against `UnmovableSymbolTests`.
  - Execution state: performed

- [x] E-02 PIN THE CURRENT BEHAVIOR OF BOTH HOSTS, per the parent's E-02 constraint that no child may reconcile a symbol the characterization baseline has not pinned. Write characterization tests for `run_queue` on BOTH hosts covering every branch the split would move, following the precedent of `tests/test_wtiso_characterization.py`. The parent's own measurement found the agy side is the less covered one, so prioritize agy branches with no existing coverage; F-9 names the two concrete agy branches that are BOTH uncovered and defective, so start there. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed characterization suite that passes against UNMODIFIED code and would fail if either host's observable behavior moved; the agy branches previously uncovered are named.
  - Execution state: performed

### Task group 2: the one real defect the measurement exposed

- [x] E-03 REPAIR agy's TWO MISSING `register_signal_report` REFRESHES (F-9), which is a defect in its own right and does not require the split. oc calls it FIVE times inside `run_queue`, agy THREE: agy omits the refresh after the rung-1 integration reload (`agy_runipd.py:4855` area, oc's `oc_runipd.py:8169`) and after the rung-2/3 reload (oc's `oc_runipd.py:8237`). Both sites REBIND `state` via `load_state`, so on agy a signal arriving after either reload reports from a PRE-RELOAD snapshot, which is exactly the staleness the `bkclose` comment at `oc_runipd.py:8048` says the repeated call exists to prevent. Add the two calls in agy only. Note this CHANGES A COUNT the wrapper-ruling suite watches indirectly: verify `test_no_call_site_was_rewritten` still passes (it counts `save_state`, not `register_signal_report`, so it should, and saying so is the point).
  - Depends on: E-02
  - Expected outcome: agy calls `register_signal_report` at all five sites oc does; a test proves a signal after an integration reload reports post-reload state on BOTH hosts; `test_both_drivers_emit_the_shutdown_report_on_normal_exit` still passes.
  - Execution state: performed

### Task group 3: the split, GATED

- [x] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01's table: (a) the twelve dependencies a shared core would have to take and which of them the maintainer's `818uru` OQ-02 wrapper ruling already governs; (b) that `disable_lane_prompt` can NEVER resolve in `runner_shared` while `UnmovableSymbolTests` stands, so its injection is permanent rather than transitional; (c) the SIX source-inspection pins F-10 enumerates, each with the substring or AST shape it requires and whether a thin caller can still satisfy it; and (d) whether re-ordering this plan AFTER children 07/09/10/11 would reduce the twelve injections, since `execute_item` (child 07), `render_continuation_hint`/`write_report`/`driver_actor` (child 04, already executed-pending) and the interrupt family are the bulk of them.
  - Depends on: E-01
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement; no runner logic changed by this item.
  - Execution state: performed

### Task group 4: proof

- [x] E-05 Add `tests/test_rununify_run_queue.py` asserting WHAT THIS PLAN ACTUALLY DID, driven by a named table rather than by the aspiration: the closure classification E-01 measured is asserted mechanically (so a symbol silently changing class fails), agy's five `register_signal_report` sites are asserted present, and `disable_lane_prompt` is asserted STILL defined in both runners (the inverse assertion, so a later agent cannot "complete" the split by moving a symbol the maintainer pinned). If OQ-03 authorizes the split, extend this file with the shared-core object identity and the repo-wide AST anti-re-fork scan (per the parent's F10, not a pairwise check); do NOT write those assertions while the split is ungated, because a test asserting a state the code is not in is a failing test, not a guard.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: a suite that fails if the closure regresses, if agy loses a refresh site again, or if the pinned symbol is moved; and that does NOT assert an unexecuted split.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `runner_shared.py` is the established home for host-neutral runner logic and imports no runner, so it
  can hold the core without a cycle. It already uses NAME/VALUE INJECTION for exactly this shape
  (`run_checked(..., env_builder=)`, `save_state(..., write_report=)`, `resume_via_launcher(launcher, ...)`),
  which is the pattern the hook should follow rather than a new mechanism.
- `tests/test_review_findings_cascade.py::test_no_runner_to_runner_import` forbids a runner-to-runner
  import, so the core must land in `runner_shared` and never be reached by importing the other host.
  CORRECTED AT REVIEW: that guard is a SUBSTRING check for `"import oc_runipd"` /
  `"import agy_runipd"` (`tests/test_review_findings_cascade.py:308-313`), and agy uses the
  `from agent_workflows.oc_runipd import (...)` form TEN times, which the substring does not match. So
  agy DOES import oc today, extensively, and eight of the names `run_queue` closes over reach agy that
  way. Do not cite this guard as evidence that the coupling is absent; cite `runner_shared`'s own
  no-runner-import rule (`tests/test_runner_shared.py:955`), which IS AST-based and does hold.
- `tests/test_runner_shared.py:1238` (`UnmovableSymbolTests`) pins `disable_lane_prompt` in BOTH
  runners and asserts `runner_shared` does NOT define it, with the reason asserted rather than
  described: it mutates `_LANE_PROMPT_DISABLED` through `global` while each host's diverged
  `_lane_reclaim_prompt` reads its own copy, so lifting it silently breaks prompt suppression on a
  repeated interrupt in an unattended run. `run_queue` calls it (`oc_runipd.py:8329`), so a shared core
  must take it as a parameter FOREVER, not until a later child moves it.
- `tests/test_runner_shared.py:1148` (`test_no_call_site_was_rewritten`) counts `save_state` CALL SITES
  per runner and currently expects 38 in oc and 36 in agy (verified passing at review). THIRTEEN of
  each are inside `run_queue`. Moving them into `runner_shared` drops both counts by 13, and the test's
  own documented rule is that a moved count must be explained as a RELOCATION, in the file, not
  absorbed into a new literal.
- The parent Set forbids a child changing what a runner DOES, and forbids reconciling a symbol the
  characterization baseline has not pinned. E-01 exists to satisfy the second constraint.
- The execution contract forbids `git add -A`; commit only the declared `Scope-Paths`, path-scoped.

## Findings

| # | Sev | Where | Finding |
|---|---|---|---|
| F-1 | HIGH | measured at HEAD | `run_queue` is the SMALLEST of the five by real difference despite being 381/336 lines: only TWELVE code lines differ, and TWO of those carry a host token. It is very close to already-shared code that nobody has lifted. |
| F-2 | HIGH | `run_queue`, both hosts | ~~THE HAZARD THIS SPLIT CARRIES: `register_signal_report` is oc-only.~~ **RETRACTED AT REVIEW 2026-09-16: THE PREMISE IS FALSE.** `agy_runipd.py:343` imports `register_signal_report as register_signal_report` from `oc_runipd`, and `oc.register_signal_report is agy.register_signal_report` evaluates True. `tests/test_runner_backlog_close.py:1175` lists it in `_SHARED` and `test_the_implementation_is_shared_not_copied` asserts that identity; `test_agy_does_not_redefine_any_of_the_shared_functions` forbids agy from re-declaring it. So it is ALREADY one object reached by both hosts, and "must become a capability the descriptor declares" describes work completed by `bkclose` (`zhr6mc`). Replaced by F-9, which states the asymmetry that IS real. |
| F-3 | MED | `run_queue` | DIFFERENCE, the signature default: oc requires `retry_incomplete`, agy defaults it to `False`. Take oc's explicit form; a caller that relied on the default is then a compile-time error rather than a silent `False`. |
| F-4 | MED | `run_queue` | ~~DIFFERENCE, `register_signal_report`: oc calls it (twice) and agy does not.~~ **CORRECTED AT REVIEW: the direction and both numbers are wrong.** Both hosts call it; oc calls it FIVE times (`oc_runipd.py:8050`, `:8147`, `:8169`, `:8237`, `:8402`) and agy THREE (`agy_runipd.py:4733`, `:4819`, `:5046`). No capability flag is needed or wanted: the correct treatment is F-9's repair. |
| F-5 | MED | `run_queue` | DIFFERENCE, a local `repo` binding: pure style: oc binds `repo = Path(state['repo'])` then passes it, agy inlines the expression. Take oc's. |
| F-6 | MED | `run_queue` | DIFFERENCE, `driver_label`: the ONE genuine host string: `'opencode'` versus `'antigravity'`, passed to `render_run_summary_table`. This is exactly what child 04's host descriptor supplies. |
| F-7 | MED | `run_queue` | DIFFERENCE, the continuation hint: pure style: agy binds `hint` then prints it. Take oc's inline form. VERIFIED AT REVIEW: exact, and it is one of only two non-comment stylistic differences. Note however that `render_continuation_hint` ITSELF is still double-defined and host-divergent (oc says "OpenCode Session Continuity", agy "Antigravity Session Continuity"), so this line is a hook input in substance even though the STYLE resolves to oc. |
| F-8 | BLOCKER | the plan's own method; measured at HEAD `34aa40c0` | **THE PLAN MEASURED BODY DIFFERENCE AND INFERRED LIFTABILITY, the identical error that reversed sibling `i3d6ml`.** "12 differing code lines" is TRUE (verified: 229 oc code lines, 227 agy, 12 differing, 2 host-token) and it is the WRONG PROPERTY. A definition can move to `runner_shared` only if every module-level free name it closes over resolves there. `run_queue` closes over 41 such names: 14 resolve today, 27 do NOT, and 11 of the 27 are functions STILL DEFINED TWICE (`execute_item`, `retry_deferred_integrations`, `reconcile_interrupted`, `requeue_interrupted`, `reclaim_lanes_on_interrupt`, `_observe_between_turn_stop`, `_record_deliberate_stop`, `render_continuation_hint`, `write_report`, `driver_actor`, `disable_lane_prompt`). `run_queue` is a DISPATCH LOOP, which is exactly why its own body barely differs and why nearly everything it does lives behind a name that has not been unified yet. The promised "relocation with a parameter" is a relocation with TWELVE parameters that de-duplicates none of the twelve. |
| F-9 | HIGH | `agy_runipd.py` `run_queue`, two sites | **THE REAL ASYMMETRY, AND IT IS AN AGY DEFECT THE PLAN MISSED WHILE ASSERTING A FALSE ONE.** oc calls `register_signal_report` after EVERY `state = load_state(...)` rebind inside the loop; agy omits it after two of them, both in the integration-deferral ladder (oc has it at `oc_runipd.py:8169` after rung 1's reload and `:8237` after rung 2/3's; agy has neither). `oc_runipd.py:8048` states the invariant verbatim: "`register_signal_report` is called again after each state reload so the report never runs off a stale snapshot", and `oc_runipd.py:8106` repeats that `state` is REBOUND on every reload "so the handler's published reference must be refreshed or it would report from a stale snapshot". So on `aw agy run`, a SIGINT arriving after an integration re-attempt reports the pre-reload item states. This is fixable in two lines TODAY, independent of any split, and no test covers it. E-03 owns it. |
| F-10 | HIGH | six test files | **SIX PINS READ `run_queue`'s SOURCE OR AST, AND A THIN CALLER SATISFIES NONE OF THREE OF THEM.** (1) `tests/test_runner_backlog_close.py:1228` asserts `inspect.getsource(mod.run_queue)` contains both `"emit_shutdown_report()"` and `"register_signal_report("`, for BOTH hosts. (2) `tests/test_oc_runipd_cli.py:233` and (3) `tests/test_agy_runipd_cli.py:1465` assert its source contains `"tracker = StreamTracker()"`, the exact string `"execute_item(run_dir, state, runnable, recovery=recovery, tracker=tracker)"`, `"render_run_summary_table("` and `"tracker=tracker"`. All three FAIL the moment the body moves. Three more constrain it without necessarily failing: (4) `tests/test_lane_tool_identity.py:666` requires `except ToolIdentityError` to appear BEFORE `except DriverError` in its source; (5) `tests/test_runner_stop.py:607` string-indexes from `"def run_queue("` and asserts the poll precedes item selection; (6) `tests/test_runner_shared.py:3234`/`:3270` require `'"integration-deferred"'`, `retry_deferred_integrations`, `deferred_integration_items`, `runnable is None` and `poll=True` in its source. And (7) `tests/test_orchestrator_retirement.py:3483` parses `agy_runipd`'s OWN `run_queue` AST and requires an `If` whose test mentions `orchestrate` with a `Continue` inside, its message stating the shared decider is not sufficient. NONE of these seven files was in `Scope-Paths`, so `aw ipd finalize` would refuse every one as an out-of-scope edit. Added to the fence. |
| F-11 | MED | `tests/test_runner_shared.py:1148` | **THE SPLIT MOVES A THIRD OF A PINNED CALL-SITE POPULATION.** `test_no_call_site_was_rewritten` expects exactly 38 `save_state` call sites in oc and 36 in agy (verified passing at review; the arithmetic is 32+1+1+4 and 30+1+1+4). THIRTEEN per host are inside `run_queue`. Moving them drops both counts by 13, and the test's own rule forbids fixing that by editing the literal: "If a count moves and you cannot name the new call site, the wrapper ruling has been undone". The correct treatment is a documented RELOCATION subtraction, exactly as `RELOCATED_RUN_CHECKED_CALLERS` does for the six `run_checked` callers that moved. The plan does not mention it. |
| F-12 | MED | `DEPENDENCY_BLOCK_RECOVERY_HINT` | A NINTH DIFFERENCE the plan's enumeration misses because it is not on a differing LINE: `run_queue` reads this constant twice (`oc_runipd.py:8258`, `:8268`), the two hosts' values are NOT equal (`aw oc runipd resume ...` versus `aw agy runipd resume ...`), and `tests/test_runner_telemetry_integration.py:597` records that it "differs per host by design". So it is a genuine hook input, and a split that lifted it to `runner_shared` unchanged would print the wrong recovery command on one host. The other three constants it closes over (`SUCCESS_STATES`, `EXECUTION_SUCCESS_STATES`, `TERMINAL_STATES`) ARE equal and can move with the loop. |
| F-13 | MED | E-02/E-03/E-04 right-sizing as authored | The original E-02 bundled the whole relocation of a 381-line dispatch loop, its twelve dependency decisions, its import rewiring in two files of 9,375 and 5,727 lines, and the repair of seven test files into ONE item, which the count-based lint cannot see. A failure midway leaves the package unimportable, exactly as `i3d6ml`'s F-14 found for its groups. The re-scoped items are one measurement, one test-only baseline, a two-line repair, one written analysis, and one guard suite: one focused pass each. |
| F-14 | LOW | `Item-Dependencies: executed:i3d6ml` | THE DECLARED EDGE IS SATISFIED BUT INSUFFICIENT, and the direction is worth stating. Child 03 (`i3d6ml`) was itself re-scoped at review from 48 symbols to 9, and NONE of the 9 is among the 27 names `run_queue` closes over. So executing `i3d6ml` as re-scoped does not reduce this plan's injection count at all. The children that WOULD are 04 (`driver_actor`, `write_report`, `render_continuation_hint`) and 07 (`execute_item`), and this plan is ordered BEFORE 07 while 11 (`main`) is ordered after this one. That ordering is part of OQ-03. |

## Proposed changes (ordered, validatable)

1. Measure the CLOSURE at execution HEAD and classify all 41 names (E-01).
2. Characterize both hosts' current behavior for every branch a split would move (E-02).
3. Repair agy's two missing `register_signal_report` refreshes (E-03), the one real defect the
   measurement exposed, independent of any split.
4. Record the split analysis as a DELIVERABLE for OQ-03 rather than performing it (E-04).
5. Add the guard suite for what actually changed, including the inverse assertion that
   `disable_lane_prompt` stayed (E-05).

## Deferred / out of scope (with reason)

- The other four large functions of this Set, each owned by its own sibling child, because each is a
  distinct seam and the parent forbids a child exceeding one cohesive seam.
- The 48 no-disagreement symbols (child 03), the 8 host-string symbols (child 04), the two behavior
  conflicts (child 05), and the record type (child 06). All are ordered BEFORE this plan so their
  results are available rather than re-derived. NOTE child 03 was re-scoped at review to 9 symbols,
  none of which this plan closes over (F-14), so its execution does not unblock this one.
- THE SPLIT ITSELF, deferred to OQ-03 rather than attempted. Reason stated plainly because a reader
  will otherwise assume it was forgotten: performing it today requires either twelve injected
  dependencies (one of them permanent) or the reversal of three source-inspection pins that four
  executed plans installed. Both are decisions above this plan's authority.
- Any behavior change, feature addition, or flag change, EXCEPT E-03's two-line repair, which is a
  DEFECT FIX and is declared as one rather than smuggled in as a relocation. It makes agy match an
  invariant oc's own comments state, adds no feature, and changes no flag.

## Scope check

- Over-scope: none. E-03 is the only product-code change and it is two lines in one host, justified by
  a stated invariant in the other host's comments. The seven added test paths are repairs the change
  forces, not new work (F-10).
- Under-scope: this plan does not perform the split it is named for. That is deliberate and gated
  (OQ-03), not an omission: E-04's deliverable is the analysis the maintainer needs to decide. It also
  does not attempt to shrink `run_queue` itself, which remains a legitimate later refactor.

## Required tests / validation

1. E-01's closure table, reproducible: a reader must be able to re-run the stated method and obtain the
   stated classification. State the HEAD it was taken at, because it will move.
2. The E-02 characterization suite, green against UNMODIFIED code and again after E-03. Both hosts'
   suites alone are NOT sufficient, because the parent measured them as asymmetric (95 oc tests versus
   21 agy at the time), so an agy-side regression can hide behind green.
3. `tests/test_rununify_run_queue.py` (new): the closure classification asserted mechanically; agy's
   five `register_signal_report` sites present; and `disable_lane_prompt` asserted STILL defined in both
   runners (the inverse assertion, so the pin cannot be "completed" away later).
4. NON-VACUITY, BIDIRECTIONAL. Two controls, both pasted. (a) Remove one of E-03's added
   `register_signal_report` calls and show the new suite FAILS, naming the site; restore. (b) Show the
   guard suite also fails in the OTHER direction, by moving `disable_lane_prompt` into `runner_shared`
   and observing both the new suite and `UnmovableSymbolTests` fail; restore. A guard that only fails
   one way does not pin a boundary.
5. THE SEVEN PINNED FILES, each green by name and each named in the report:
   `tests/test_runner_backlog_close.py`, `tests/test_oc_runipd_cli.py`, `tests/test_agy_runipd_cli.py`,
   `tests/test_lane_tool_identity.py`, `tests/test_runner_stop.py`, `tests/test_runner_shared.py`,
   `tests/test_orchestrator_retirement.py` (F-10). If E-03 alone leaves all seven untouched, SAY SO with
   the passing output rather than editing them speculatively.
6. `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` green, stated explicitly
   (F-11): it must still expect 38/36 because E-03 adds no `save_state` call site.
7. `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` green.
8. Bare `python3 -m pytest`, summary pasted, no new failure against the baseline at execution time. Take
   YOUR OWN baseline at YOUR HEAD before changing anything; sibling `i3d6ml`'s review measured a
   load-dependent timeout in the full suite that passes in isolation, so a single failure must be
   reproduced against the pre-change baseline before it is attributed to this plan.

## Spec / documentation sync

No `.spec.md` change expected: this is an internal refactor with no operator-visible contract change. IF
execution finds that a spec sentence describes the divergence being removed, amend it in the SAME change
and add the spec path to `Scope-Paths`, per the repository's spec-amendment rule.

REVIEWED 2026-09-16 AND STILL TRUE, with one thing worth stating rather than assuming. E-03's repair
makes agy's shutdown report read post-reload state, which is a change to what an OPERATOR SEES after a
signal, so check whether spec `25kzda` or `c4gd2h` pins the shutdown report's contents; if either does,
the repair brings agy INTO conformance rather than out of it, and that is worth one sentence in the
report either way. E-01, E-02, E-04 and E-05 touch no operator-visible contract.

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
  is that a child may not change behavior, and E-02's characterization suite is what makes a violation
  visible instead of silent. A partial split that leaves a smaller shared core is an acceptable outcome
  and is strictly better than a complete split that moves behavior; say which branches were left behind
  and why. CONFIRMED AT REVIEW 2026-09-16, and the condition this question anticipated HAS OCCURRED:
  the measurement in F-8 is the report, and OQ-03 is the stop. This resolution is what makes the
  re-scope obedient to the plan rather than a departure from it.

### OQ-03: The split needs twelve injected dependencies, one of them permanent. Which route does the Set take?

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
  NOT DECIDED, deliberately, because every route restructures a Set
  that has nine pending children and an approved orchestrator, and that is a scope-and-sequencing call
  the maintainer owns. THE MEASUREMENT, not an opinion: `run_queue` closes over 41 module-level names;
  14 resolve in `runner_shared`, 11 are still DEFINED TWICE, and `disable_lane_prompt` is pinned
  unmovable by `tests/test_runner_shared.py:1238` so its injection would be PERMANENT rather than
  transitional. Separately, three pins assert substrings of `inspect.getsource(run_queue)` that a thin
  caller cannot contain (F-10), and the wrapper-ruling call-site census loses 13 of 38 and 13 of 36
  entries (F-11).
  FOUR ROUTES, with what each costs. (A) INJECT ALL TWELVE now: gets one shared loop, but the shared
  core takes twelve parameters, de-duplicates none of the twelve, and permanently injects the pinned
  symbol; the maintainer already rejected uniform injection at smaller scale in `818uru` OQ-02, so this
  route contradicts a standing ruling. (B) RE-ORDER this plan AFTER children 07/09/10/11, so
  `execute_item`, `render_continuation_hint`, `write_report` and `driver_actor` are already shared and
  the injection count falls; costs a Set re-ordering and makes child 11 (`main`, which declares
  `executed:ty3cj6`) wait on the new position. (C) REDUCE THIS PLAN to what is genuinely liftable
  today, which is the two host-token lines plus the F-12 constant, and drop "split" from its title;
  honest and small, but leaves the loop duplicated. (D) DO NOT SPLIT `run_queue` AT ALL: at 12 differing
  code lines out of 229 it is the LEAST drifted of the five large functions, so the de-duplication
  payoff is the smallest in the Set while the pin breakage is the largest.
  RECOMMENDATION: (B), then (C) if (B) is refused. (B) is the only route that reaches the Set's stated
  goal without contradicting the `818uru` ruling, and the re-ordering is cheap because this plan and
  child 11 are the only two edges affected. (A) is not recommended. (D) is defensible and should be
  said out loud rather than left as a silent outcome, since a Set that unifies four of five large
  functions and documents why the fifth stayed is a better record than one that forces the fifth.
  THIS PLAN'S E-01 THROUGH E-05 ARE EXECUTABLE UNDER EVERY ROUTE and produce the analysis the decision
  needs; only E-04's split is gated.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted closure table with all 41 names classified into the six classes, the command or script that produced it, and the HEAD. Must explicitly state the count of names still DEFINED TWICE and confirm or refute `disable_lane_prompt`'s pinned status by citing `tests/test_runner_shared.py:1238`. A table that merely repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence: RE-DERIVED at execution HEAD `24932638` with `closure_scan.py` (a full-scope-tracking scanner committed as evidence and reproduced in the walkthrough's Appendix C), NOT copied from this plan. Command: `python3 closure_scan.py`. Output:

    ```
    # `run_queue` closure classification at HEAD 24932638

    oc free module-level names : 41
    agy free module-level names: 41
    UNION                      : 41

    | Class | Count | Members |
    |---|---|---|
    | resolves-in-runner-shared | 7 | `DriverError`, `append_jsonl`, `dispatch_orchestrator_item`, `load_state`, `print_lane_interrupt_report`, `should_color`, `utc_now` |
    | already-one-object | 18 | `Palette`, `Path`, `StreamTracker`, `ToolIdentityError`, `cascade_dependency_blocked`, `contextlib`, `dependency_status`, `dependency_status_detailed`, `emit_shutdown_report`, `queue_sort_key`, `register_signal_report`, `render_run_summary_table`, `report_run_spec_edits`, `runner_shared`, `runner_stop`, `sys`, `time`, `update_execution_order` |
    | thin-wrapper | 1 | `save_state` |
    | equal-constant | 3 | `EXECUTION_SUCCESS_STATES`, `SUCCESS_STATES`, `TERMINAL_STATES` |
    | divergent-constant | 1 | `DEPENDENCY_BLOCK_RECOVERY_HINT` |
    | still-double-defined | 11 | `_observe_between_turn_stop`, `_record_deliberate_stop`, `disable_lane_prompt`, `driver_actor`, `execute_item`, `reclaim_lanes_on_interrupt`, `reconcile_interrupted`, `render_continuation_hint`, `requeue_interrupted`, `retry_deferred_integrations`, `write_report` |
    ```

    STILL DEFINED TWICE: **11**, stated as this item requires. 7+18+1+3+1+11 = 41.

    NO SYMBOL CHANGED CLASS since 2026-09-16. This is the FIRST child of this Set whose numbers did not move (`i3d6ml` was cut 48 -> 9 at review; `yrqyxb`'s forks improved 18 -> 11 at execution). The body-difference figures also reproduced exactly: 234 oc code lines, 232 agy, **12 differing**, **2 bearing a host token**. Raw lengths grew (403/347 against the plan's 381/336) from comment growth only.

    CLASSIFICATION CONVENTION NOTE, so the table is not read as disagreeing with the plan's Goal table: the plan counts 14 "resolves in `runner_shared`" and 8 "already ONE object" where this scanner reports 7 and 18. Same 41 names, same 11 forks; the scanner reserves `resolves-in-runner-shared` for names imported specifically FROM `runner_shared` and puts every third-module import (`Path`, `sys`, `time`, `contextlib`, the `render_stream` names) into `already-one-object`. The plan's own arithmetic note acknowledges the overlap. Every symbol lands in a class with the same CONSEQUENCE under both conventions. One refinement: `save_state` is reported as `thin-wrapper`, not a fork, because each host's body is a single delegating `runner_shared.save_state(...)` call, the sanctioned `818uru` OQ-02 form; counting it as duplication would overstate the work (sibling `yrqyxb`'s contribution, adopted).

    `disable_lane_prompt` PINNED STATUS **CONFIRMED**, not refuted. `tests/test_runner_shared.py:1319` (`UnmovableSymbolTests`; the plan cites `:1238`, the line has since moved) pins it in BOTH runners, asserts `runner_shared` does not define it, and asserts the REASON: it writes `_LANE_PROMPT_DISABLED` through `global` while each host's diverged `_lane_reclaim_prompt` reads its own copy. `run_queue` CALLS it at `oc_runipd.py:8926`, so a shared core must take it as a parameter FOREVER. Verified green:

    ```
    $ python3 -m pytest tests/test_runner_shared.py::UnmovableSymbolTests -o addopts=""
    3 passed
    ```

    The classification is additionally asserted MECHANICALLY in `tests/test_rununify_run_queue.py::TheClosureClassificationIsPinned` (11 tests), so it is re-derived by the suite and cannot go stale unnoticed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted green run of the characterization suite against UNMODIFIED code, plus the list of agy branches it newly covers (naming the two F-9 sites specifically), plus a sabotage of one pinned branch showing the suite FAILS (a characterization test that cannot fail pins nothing).
  - Observed evidence: `tests/test_rununify_run_queue_characterization.py`, 35 tests, every one running against BOTH hosts through `subTest`. It drives each host's REAL `run_queue` over a synthetic queue with `execute_item` stubbed, following the `tests/test_orchestrator_retirement.py::DispatchRunCase` precedent.

    GREEN AGAINST UNMODIFIED CODE. Taken BEFORE E-03, with 33 of the 35 passing and the two F-9 tests correctly FAILING on the unrepaired agy host (that failure is the sabotage-equivalent this item asks for, and it is the real defect rather than an injected one):

    ```
    $ python3 -m pytest tests/test_rununify_run_queue_characterization.py -o addopts="" -p no:randomly
    FAILED tests/test_rununify_run_queue_characterization.py::TheIntegrationLadderIsReachedFromTheLoop::test_the_published_snapshot_matches_the_live_statuses_after_the_ladder
    FAILED tests/test_rununify_run_queue_characterization.py::TheIntegrationLadderIsReachedFromTheLoop::test_the_reporter_sees_post_ladder_state_at_both_reload_points
    2 failed, 33 passed in 3.90s
    ```

    E   AssertionError: False is not true : agy_runipd: after the integration ladder reloaded state, the object the shutdown reporter would read is NOT the object the loop is working with, so a signal arriving here reports a PRE-reload snapshot.

    AND GREEN AFTER E-03, all 35:

    ```
    $ python3 -m pytest tests/test_rununify_run_queue_characterization.py -o addopts="" -p no:randomly
    35 passed in 3.81s
    ```

    THE TWO F-9 AGY BRANCHES, named as required: the RUNG-1 ladder reload (`agy_runipd.py:5199` area, oc's counterpart `oc_runipd.py:8766`) and the RUNG-2/3 ladder reload (`agy_runipd.py:5258` area, oc's `oc_runipd.py:8834`). Neither had ANY coverage before this suite. They are covered by `TheIntegrationLadderIsReachedFromTheLoop` (4 tests) and `TheSignalReporterSeesPostReloadState` (3 tests).

    OTHER AGY BRANCHES NEWLY COVERED, all previously uncovered on that host: the dependency cascade and its host-divergent recovery hint (`AnUnsatisfiableDependencyBlocksRatherThanStalls`, 3 tests); every one of the nine states `--retry-incomplete` re-queues, plus the `recovery=True` dispatch flag, its inverse, and the `runstop m0z0ti` R19 indeterminate refusal (`TheRetryIncompleteFlagRequeuesTheStatesItDeclares`, 4 tests, 18 subtests); the display-option freeze (3); the orchestrate short-circuit and its two state-set bindings (2); the driver label and continuation hint as OUTPUT (2); the tool-identity clause (2 + 3 defect-pinning); the between-item stop checkpoint (1); tracker wiring and instance reuse (2); exit codes (3).

    A DELIBERATE SABOTAGE WAS ALSO RUN, on top of the natural failure above: removing E-03's rung-1 call made 2 characterization tests plus 3 E-05 guards fail, naming the site. Pasted in full under V-05(b).

    ONE FINDING WORTH RECORDING, because it is why this suite is trustworthy at all. The FIRST version of the F-9 test PASSED on the defective host, i.e. it was VACUOUS. Comparing published item STATUSES cannot fail under a test stub, because the stub mutates the very dict the loop holds, so the pre-reload snapshot and the live object ARE the same object. The property that actually discriminates is OBJECT IDENTITY: `published() is state` measured True on oc and False on agy at this HEAD. Recorded as decision `09-ty3cj6-D2`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: FOUR parts, all pasted. (a) The two added call sites shown in context, with agy's `register_signal_report` count going 3 -> 5 and matching oc's five site-for-site. (b) A test proving a signal after an integration reload reports POST-reload state on BOTH hosts, green. (c) `tests/test_runner_backlog_close.py` green, including `test_both_drivers_emit_the_shutdown_report_on_normal_exit`. (d) `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` green with its 38/36 expectation unchanged (F-11).
  - Observed evidence: all four parts below, measured and pasted.

    **(a) THE COUNT AND THE SITE-FOR-SITE MATCH.** Before, measured by AST inside `run_queue`:

    ```
    oc_runipd register_signal_report sites: 5 [8647, 8744, 8766, 8834, 9021] | save_state sites: 13
    agy_runipd register_signal_report sites: 3 [5096, 5182, 5420]            | save_state sites: 13
    ```

    After:

    ```
    oc_runipd register_signal_report sites: 5 [8647, 8744, 8766, 8834, 9021] | save_state sites: 13
    agy_runipd register_signal_report sites: 5 [5096, 5182, 5209, 5264, 5436] | save_state sites: 13
    ```

    3 -> 5. SITE FOR SITE, by what each call FOLLOWS (this is the correspondence, not just the total):

    ```
    == oc_runipd                                      == agy_runipd
       L8647  preceded by: state = load_state(run_dir)    L5096  preceded by: state = load_state(run_dir)
       L8744  preceded by: state["_invocation_start_mono"] = ...   L5182  preceded by: state["_invocation_start_mono"] = ...
       L8766  preceded by: state = load_state(run_dir)    L5209  preceded by: state = load_state(run_dir)
       L8834  preceded by: state = load_state(run_dir)    L5264  preceded by: state = load_state(run_dir)
       L9021  preceded by: state["_summary_table_printed"] = True  L5436  preceded by: state["_summary_table_printed"] = True
    ```

    Exact correspondence at all five. The two added sites, in context (agy only; oc untouched):

    ```python
            if runner_shared.deferred_integration_items(state):
                retry_deferred_integrations(run_dir, state)
                save_state(run_dir, state)
                state = load_state(run_dir)
                # rununify Order 08 (`ty3cj6`) E-03: REFRESH the shutdown reporter's published
                # reference, because the line above REBOUND `state` to a fresh dict. ...
                register_signal_report(run_dir, state)
    ```

    ```python
                    retry_deferred_integrations(run_dir, state, poll=True, ask=True)
                    save_state(run_dir, state)
                    state = load_state(run_dir)
                    # rununify Order 08 (`ty3cj6`) E-03: the SECOND of the two ladder reloads this host
                    # was missing, matching `oc_runipd.py:8834`. ...
                    register_signal_report(run_dir, state)
    ```

    **(b) THE BEHAVIORAL PROOF, both hosts, green.** `TheSignalReporterSeesPostReloadState` (3 tests) and `TheIntegrationLadderIsReachedFromTheLoop::test_the_reporter_sees_post_ladder_state_at_both_reload_points` / `::test_the_published_snapshot_matches_the_live_statuses_after_the_ladder`. The discriminating measurement, before and after:

    ```
    BEFORE E-03:  oc published-is-live-object at each turn: [True]
                  agy published-is-live-object at each turn: [False]
    AFTER  E-03:  35 passed in 3.81s   (both hosts True)
    ```

    **(c) `tests/test_runner_backlog_close.py` GREEN**, including the named test:

    ```
    $ python3 -m pytest tests/test_runner_backlog_close.py -o addopts=""
    47 passed in 2.71s
    ```

    That file's `test_both_drivers_emit_the_shutdown_report_on_normal_exit` is one of the ten source-reading pins (it requires `"emit_shutdown_report()"` and `"register_signal_report("` in BOTH hosts' `run_queue` source); E-03 ADDS occurrences of the second substring, so the pin is satisfied more strongly than before.

    **(d) THE WRAPPER CENSUS UNCHANGED**, which is the point F-11 asks to be stated rather than assumed:

    ```
    $ python3 -m pytest tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten -o addopts=""
    1 passed in 2.11s
    ```

    E-03 adds `register_signal_report` calls ONLY. `save_state` sites inside `run_queue` stayed at 13 on both hosts (measured above), so the per-runner totals the census pins are untouched and no expected literal needed editing. `tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_the_repair_added_no_save_state_call_site` asserts this independently.

    Also green: `tests/test_runner_shared.py` in full (part of the 428-test pinned-file run under V-05(c)).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the written analysis itself, covering all four parts (a) through (d) that E-04 enumerates, with the six pins of F-10 each stated alongside the substring or AST shape it requires and a verdict on whether a thin caller can satisfy it. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence: the analysis is **Appendix B** of `.aw/records/walkthroughs/20260917-rqclosure-01-k2vn8p-run-queue-closure-measured-and-a-swallowed-run-fatal-error.walkthrough.md`, written as a TRACKED artifact rather than under `.aw/state/` (which is gitignored, so an analysis filed there would not survive; this follows the correction sibling `yrqyxb` had to make). All four parts:

    **(a) THE DEPENDENCIES AND WHO LIFTS THEM.** Eleven, not the plan's "twelve" (the plan counted the divergent constant `DEPENDENCY_BLOCK_RECOVERY_HINT` alongside the ten callables; the constant IS a hook input but is not a callable dependency). Per-symbol table with owning sibling and verdict. Two clear through `tx6q0h` (`render_continuation_hint`, `write_report`). `driver_actor` is DELIBERATELY REFUSED by that same sibling's E-05 on measured grounds (oc reads a profile subsystem where `runner_profiles`/`resolve_launch_profile`/`launch_profile` all grep to ZERO in `agy_runipd.py`). Which of them the `818uru` OQ-02 wrapper ruling governs: the ruling supplies the MECHANISM for all of them (shared core plus thin per-host wrapper), and the analysis states plainly why the mechanism being sanctioned does not make nine injections the right act here.

    **(b) `disable_lane_prompt` CAN NEVER RESOLVE in `runner_shared`**, so its injection is PERMANENT rather than transitional. Confirmed against `UnmovableSymbolTests` (see V-01) and asserted in the INVERSE direction by `tests/test_rununify_run_queue.py::ThePinnedSymbolStayedPinned` (4 tests), one of which pins that `run_queue` still CALLS it, since the permanence argument depends on that.

    **(c) THE PINS: 10 SITES ACROSS 9 FILES, not six.** Measured with `pin_scan.py` (committed as evidence, reproduced in Appendix C), which finds all three ways a test reaches this function's source. Each pin is tabulated with the exact substring or AST shape it requires and a thin-caller verdict: **8 BREAK, 2 SURVIVE**. The two survivors are `tests/test_oc_runipd_shim.py:40` and `tests/test_agy_runipd_shim.py:37`, both NEGATIVE assertions that `"def run_queue"` is ABSENT from the shim, which a split satisfies more strongly rather than less. THREE assert ORDERING (`test_lane_tool_identity.py:733`, `test_runner_stop.py:607`, `test_orchestrator_retirement.py:3575`), and each has a behavioral equivalent ALREADY IMPLEMENTED AND PASSING in the E-02 net, so the re-basing route the maintainer's ruling authorizes is demonstrated rather than proposed. Unlike sibling `yrqyxb`, which found three undeclared files, every pin file here is already in `Scope-Paths` except the two shim files whose pins are negative.

    **(d) WOULD RE-ORDERING AFTER 07/09/10/11 REDUCE THE INJECTIONS?** Answered with a measurement: **barely, and not enough to matter.** Only `tx6q0h` (04) lifts anything this plan closes over, and it lifts TWO. Child 07 (`yrqyxb`) is EXECUTED and did NOT split `execute_item`. Children 09/10/11 own `initialize_run`/`build_parser`/`main` and lift none of the eleven. So **nine of eleven survive the entire Set** and re-ordering is not the lever the plan hoped.

    THE ANALYSIS ALSO FOUND SOMETHING THE PLAN DID NOT, and it is the actionable part: **FOUR of the seven unclaimed forks are CLOSURE-CLEAN TODAY** and liftable right now, individually, without `run_queue` moving at all (`reconcile_interrupted`, which is 69 code lines on both hosts differing by TWO; `_record_deliberate_stop`; `requeue_interrupted`; `_observe_between_turn_stop`). Each closes over nothing but stdlib, `runner_shared` names, and the sanctioned `save_state` wrapper. That is the cheapest real progress available to this Set and NO plan currently claims it. Filed as backlog `5jsjnr` with the per-symbol accounting. `reclaim_lanes_on_interrupt` is similarly near-identical (134/134, two differing lines) but is blocked by the same `_LANE_PROMPT_DISABLED` global sibling `i3d6ml` hit (its backlog `8hx3g3`).

    **NO SPLIT WAS PERFORMED**, stated explicitly. `run_queue` still has two definitions and there is no shared core; `tests/test_rununify_run_queue.py::TheSplitHasNotBeenPerformed` (3 tests) asserts that MECHANICALLY. On OQ-03's status: it is `resolved` on disk, so the DESTINATION is settled ("do the split") and this turn did not re-ask it. What was OWED and is delivered is the SEQUENCING analysis, which concludes that the split is the right destination and this position in the Set is the wrong place to jump to it in one act, with a five-step route to reach it. Recorded as decision `09-ty3cj6-D1`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_run_queue.py -o addopts=""` green, including the inverse `disable_lane_prompt` assertion. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 4, both directions shown failing and then restored. (c) All SEVEN pinned files of F-10 green by name. (d) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, plus both hosts' suites green by name.
  - Observed evidence: all four parts below, measured and pasted.

    **(a) THE GUARD SUITE GREEN**, 32 tests:

    ```
    $ python3 -m pytest tests/test_rununify_run_queue.py -o addopts="" -p no:randomly
    32 passed in 2.26s
    ```

    Includes `ThePinnedSymbolStayedPinned` (4 tests: `disable_lane_prompt` still defined in BOTH runners, `runner_shared` still does NOT define it, the two definitions are not the same object, and `run_queue` still CALLS it).

    **(b) BIDIRECTIONAL NON-VACUITY, both directions shown failing and restored.**

    DIRECTION 1, remove one of E-03's added calls (the rung-1 site):

    ```
    $ python3 -m pytest tests/test_rununify_run_queue.py tests/test_rununify_run_queue_characterization.py -o addopts="" -p no:randomly
    FAILED tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_both_hosts_refresh_at_five_sites
    FAILED tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_every_ladder_reload_is_followed_by_a_refresh_on_both_hosts
    FAILED tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_the_two_hosts_have_the_SAME_number_of_sites
    FAILED tests/test_rununify_run_queue_characterization.py::TheIntegrationLadderIsReachedFromTheLoop::test_the_published_snapshot_matches_the_live_statuses_after_the_ladder
    FAILED tests/test_rununify_run_queue_characterization.py::TheIntegrationLadderIsReachedFromTheLoop::test_the_reporter_sees_post_ladder_state_at_both_reload_points
    5 failed, 62 passed in 5.98s
    ```

    Five tests fire and NAME the site. Restored, then re-verified: `67 passed in 5.83s`.

    DIRECTION 2, move the pinned symbol INTO `runner_shared` (`disable_lane_prompt` lifted with its `_LANE_PROMPT_DISABLED` global):

    ```
    $ python3 -m pytest tests/test_rununify_run_queue.py tests/test_runner_shared.py::UnmovableSymbolTests -o addopts="" -p no:randomly
    FAILED tests/test_rununify_run_queue.py::ThePinnedSymbolStayedPinned::test_runner_shared_still_does_not_define_it
    FAILED tests/test_runner_shared.py::UnmovableSymbolTests::test_the_shared_module_does_not_define_it
    2 failed, 34 passed in 2.57s
    ```

    BOTH my guard AND the maintainer's own `UnmovableSymbolTests` fire, which is the point: the boundary is pinned from two independent directions. Restored with `git checkout -- agent_workflows/runner_shared.py`, then re-verified: `72 passed in 7.01s` across both new files plus `UnmovableSymbolTests` plus the wrapper census. `git diff --stat` afterwards showed ONLY the intended `agent_workflows/agy_runipd.py | 16 ++++` change, so the committed tree carries no experiment residue.

    A THIRD, UNPLANNED AND STRONGER CONTROL, at SUITE scale. Reverting E-03 (`git stash push -- agent_workflows/agy_runipd.py`) while keeping the tests, then running the WHOLE suite:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest        # E-03 reverted, tests kept
    FAILED tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_both_hosts_refresh_at_five_sites
    FAILED tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_every_ladder_reload_is_followed_by_a_refresh_on_both_hosts
    FAILED tests/test_rununify_run_queue.py::TheSignalReportRefreshSitesArePinned::test_the_two_hosts_have_the_SAME_number_of_sites
    FAILED tests/test_rununify_run_queue_characterization.py::TheIntegrationLadderIsReachedFromTheLoop::test_the_published_snapshot_matches_the_live_statuses_after_the_ladder
    FAILED tests/test_rununify_run_queue_characterization.py::TheIntegrationLadderIsReachedFromTheLoop::test_the_reporter_sees_post_ladder_state_at_both_reload_points
    FAILED tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130
    6 failed, 7609 passed, 3 skipped, 2 xfailed in 93.18s
    ```

    Five of mine fire in a full-suite run and everything else stays green. E-03 restored via `git stash pop`, count re-verified at 5 sites.

    **(c) THE PINNED FILES GREEN BY NAME.** The plan lists seven; the measured inventory is nine files (the two shim files carry negative pins the plan does not name). All nine, green:

    ```
    $ python3 -m pytest tests/test_runner_backlog_close.py tests/test_runner_shared.py \
        tests/test_lane_tool_identity.py tests/test_runner_stop.py \
        tests/test_orchestrator_retirement.py tests/test_oc_runipd_shim.py \
        tests/test_agy_runipd_shim.py tests/test_oc_runipd_cli.py -o addopts=""
    428 passed in 58.78s
    ```

    The ninth, `tests/test_agy_runipd_cli.py`, green with the worker-role guard unset (see (d) for why that is the honest way to run it here):

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_agy_runipd_cli.py -o addopts=""
    66 passed in 11.24s
    ```

    AS THE PLAN ASKS: **E-03 left all of them UNTOUCHED.** No pin file was edited, so all nine are declared-but-unmodified and require `--scope-ack`. This is stated with passing output rather than by editing them speculatively.

    **(d) THE BARE SUITE, against a baseline taken at THIS HEAD before changing anything.**

    ```
    $ python3 -m pytest        # PRE-change baseline, HEAD 24932638, worker role set
    32 failed, 7516 passed, 3 skipped, 2 xfailed in 96.38s

    $ python3 -m pytest        # POST-change, with all three of my files
    32 failed, 7583 passed, 3 skipped, 2 xfailed in 90.53s

    $ diff <(pre FAILED lines | sort) <(post FAILED lines | sort)
    IDENTICAL
    ```

    **Byte-identical failure sets before and after; +67 passing and NO new failure.**

    THE 32 ARE THE WORKER-ROLE ARTIFACT, not a repo defect and not mine: `AW_EXECUTION_ROLE=worker` is set in a runner-managed lane, which makes `ipd_lifecycle` refuse driver-only verbs by design (`AW-LIFECYCLE-ROLE-001`), and the affected tests call `driver_begin` and friends directly. With the role unset:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest    # PRE-change
    7548 passed, 3 skipped, 2 xfailed in 91.11s     # ZERO failures

    $ env -u AW_EXECUTION_ROLE python3 -m pytest    # POST-change
    1 failed, 7614 passed, 3 skipped, 2 xfailed     # the sigint test
    ```

    THAT ONE FAILURE IS A PRE-EXISTING LOAD-DEPENDENT FLAKE, established rather than asserted: `test_sigint_produces_the_report_and_exits_130` spawns a real driver subprocess and signals it. It **also fails with E-03 REVERTED** (see the suite-scale control in (b): `6 failed`, of which five are my guards and the sixth is this test), and it passes in isolation and in its own file:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130 -o addopts=""
    1 passed in 0.64s
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_runner_backlog_close.py -o addopts=""
    47 passed in 2.71s
    ```

    The plan's Required-tests item 8 anticipates exactly this and requires it be reproduced against the pre-change baseline before attribution. It was.

    **BOTH HOSTS' SUITES GREEN BY NAME:** `tests/test_oc_runipd_cli.py` (in the 428 above), `tests/test_agy_runipd_cli.py` (66 passed), and `tests/test_oc_runipd.py`:

    ```
    $ env -u AW_EXECUTION_ROLE python3 -m pytest tests/test_oc_runipd.py -o addopts=""
    185 passed in 29.17s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

OPEN QUESTION GATE. OQ-03 is `Blocking: yes` and OPEN. `aw ipd lint` refuses this plan at every
checkpoint until the maintainer answers it, which is intended: THE SPLIT is not executable on this plan's
own authority. E-01, E-02, E-03, E-04 and E-05 are all authorized unconditionally, because E-04 delivers
the ANALYSIS the decision needs rather than performing the relocation.

EXECUTION CONTRACT. Commit ONLY the declared `Scope-Paths`, path-scoped; never `git add -A` and never
push. Paste the ACTUAL runner output for every `V-*`. Run the suite BARE as `python3 -m pytest`. Do NOT
add `-n0`, a second `-q`, or `-p no:randomly`. The `Scope-Paths` fence is a DECLARATION: an out-of-scope
edit is made and then JUSTIFIED at finalize with a `--scope-reason`, and a declared-but-unmodified path
needs a `--scope-ack`, which is expected here since E-03 may well leave all seven test files untouched.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.

REVIEWER'S HIGHEST-VALUE TARGETS, REWRITTEN 2026-09-16 because the original pointed at a retracted
premise: F-8's closure measurement (the reason this plan is NO-GO), F-9's two-line agy defect (the one
thing here that is unambiguously worth doing today), and F-10's six source-inspection pins, since three
of them fail the instant `run_queue`'s body moves and no amount of characterization coverage would have
caught that, because they assert on SOURCE TEXT rather than on behavior.
