# IPD: Split run_queue into a shared core and a thin host hook

- Date: 2026-09-15
- Kind: child
- Concern: `run_queue` is written twice (381 lines in `oc_runipd.py`, 336 in `agy_runipd.py`) for the same job. Measured at HEAD it carries 12 differing code lines of which only 2 bear a host token, so most of the divergence is DRIFT in shared logic rather than genuine host specificity, and every fix to one copy is a fix the other silently misses. CORRECTED AT REVIEW 2026-09-16: "12 differing lines" is TRUE and is NOT a measure of liftability, and this plan conflated the two exactly as sibling `i3d6ml` did. Measured with the CLOSURE test, `run_queue` closes over 41 module-level names of which only 14 resolve in `runner_shared` and 27 do NOT; 11 of those 27 are functions that are still DEFINED TWICE (`execute_item`, `retry_deferred_integrations`, `reconcile_interrupted`, `requeue_interrupted`, `reclaim_lanes_on_interrupt`, `_observe_between_turn_stop`, `_record_deliberate_stop`, `render_continuation_hint`, `write_report`, `driver_actor`, `disable_lane_prompt`) and one of them (`disable_lane_prompt`) is pinned PERMANENTLY unmovable. So the shared core cannot be a relocation: it must take a dozen injected dependencies, and every one it takes it also FAILS to de-duplicate. See F-8 through F-14 and OQ-03.
- Scope: Extract the host-neutral core of `run_queue` into `runner_shared.py`, leaving each host a thin hook supplying only what is genuinely its own. Logic resolves to the `oc_runipd` version per the maintainer's 2026-09-14 ruling except where a difference is a real capability, which is called out per difference below. RE-SCOPED AT REVIEW: this plan may not execute as a split until the maintainer decides OQ-03, because the split cannot be performed at this point in the Set without either injecting a dozen dependencies (a shape the maintainer already ruled against at scale) or breaking three source-inspection pins that four other plans installed. E-05 is the deliverable this plan can honestly produce today.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_rununify_run_queue.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py, tests/test_lane_tool_identity.py, tests/test_runner_backlog_close.py, tests/test_runner_shared.py, tests/test_runner_stop.py, tests/test_orchestrator_retirement.py
- Item-Dependencies: executed:i3d6ml
- Status: reviewed
- Readiness: no-go
- Set: rununify
- Order: 8
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5
- Id: ty3cj6
- From-Backlog: alw22r

## Workflow history
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

- [ ] E-01 MEASURE THE CLOSURE at execution HEAD, and refuse to proceed to E-04 on a stale list. The method is the one that reversed sibling `i3d6ml`, and it is NOT the body-difference method this plan originally used: parse `oc_runipd.run_queue`, collect every free name that resolves at MODULE level, and classify each into the six classes of the Goal table (resolves in `runner_shared`; equal constant; host-divergent constant; already-one-object-via-import; still double-defined; pinned unmovable). Emit the table with its members and name any symbol whose class changed since 2026-09-16. This E-item writes NO runner logic.
  - Depends on: none
  - Expected outcome: a reproducible closure table in the execution report with all 41 names classified; the count of still-double-defined names stated; `disable_lane_prompt`'s permanent-injection status confirmed or refuted against `UnmovableSymbolTests`.
  - Execution state: pending

- [ ] E-02 PIN THE CURRENT BEHAVIOR OF BOTH HOSTS, per the parent's E-02 constraint that no child may reconcile a symbol the characterization baseline has not pinned. Write characterization tests for `run_queue` on BOTH hosts covering every branch the split would move, following the precedent of `tests/test_wtiso_characterization.py`. The parent's own measurement found the agy side is the less covered one, so prioritize agy branches with no existing coverage; F-9 names the two concrete agy branches that are BOTH uncovered and defective, so start there. This E-item writes TESTS ONLY and changes no runner logic.
  - Depends on: E-01
  - Expected outcome: a committed characterization suite that passes against UNMODIFIED code and would fail if either host's observable behavior moved; the agy branches previously uncovered are named.
  - Execution state: pending

### Task group 2: the one real defect the measurement exposed

- [ ] E-03 REPAIR agy's TWO MISSING `register_signal_report` REFRESHES (F-9), which is a defect in its own right and does not require the split. oc calls it FIVE times inside `run_queue`, agy THREE: agy omits the refresh after the rung-1 integration reload (`agy_runipd.py:4855` area, oc's `oc_runipd.py:8169`) and after the rung-2/3 reload (oc's `oc_runipd.py:8237`). Both sites REBIND `state` via `load_state`, so on agy a signal arriving after either reload reports from a PRE-RELOAD snapshot, which is exactly the staleness the `bkclose` comment at `oc_runipd.py:8048` says the repeated call exists to prevent. Add the two calls in agy only. Note this CHANGES A COUNT the wrapper-ruling suite watches indirectly: verify `test_no_call_site_was_rewritten` still passes (it counts `save_state`, not `register_signal_report`, so it should, and saying so is the point).
  - Depends on: E-02
  - Expected outcome: agy calls `register_signal_report` at all five sites oc does; a test proves a signal after an integration reload reports post-reload state on BOTH hosts; `test_both_drivers_emit_the_shutdown_report_on_normal_exit` still passes.
  - Execution state: pending

### Task group 3: the split, GATED

- [ ] E-04 DO NOT PERFORM THE SPLIT UNTIL OQ-03 IS ANSWERED, and record the analysis rather than silently skipping it. The deliverable is the disclosure, so an executor cannot mistake the omission for an oversight and "finish" it later. State, from E-01's table: (a) the twelve dependencies a shared core would have to take and which of them the maintainer's `818uru` OQ-02 wrapper ruling already governs; (b) that `disable_lane_prompt` can NEVER resolve in `runner_shared` while `UnmovableSymbolTests` stands, so its injection is permanent rather than transitional; (c) the SIX source-inspection pins F-10 enumerates, each with the substring or AST shape it requires and whether a thin caller can still satisfy it; and (d) whether re-ordering this plan AFTER children 07/09/10/11 would reduce the twelve injections, since `execute_item` (child 07), `render_continuation_hint`/`write_report`/`driver_actor` (child 04, already executed-pending) and the interrupt family are the bulk of them.
  - Depends on: E-01
  - Expected outcome: a written analysis sufficient for the maintainer to answer OQ-03 without re-deriving the measurement; no runner logic changed by this item.
  - Execution state: pending

### Task group 4: proof

- [ ] E-05 Add `tests/test_rununify_run_queue.py` asserting WHAT THIS PLAN ACTUALLY DID, driven by a named table rather than by the aspiration: the closure classification E-01 measured is asserted mechanically (so a symbol silently changing class fails), agy's five `register_signal_report` sites are asserted present, and `disable_lane_prompt` is asserted STILL defined in both runners (the inverse assertion, so a later agent cannot "complete" the split by moving a symbol the maintainer pinned). If OQ-03 authorizes the split, extend this file with the shared-core object identity and the repo-wide AST anti-re-fork scan (per the parent's F10, not a pairwise check); do NOT write those assertions while the split is ungated, because a test asserting a state the code is not in is a failing test, not a guard.
  - Depends on: E-01, E-03, E-04
  - Expected outcome: a suite that fails if the closure regresses, if agy loses a refresh site again, or if the pinned symbol is moved; and that does NOT assert an unexecuted split.
  - Execution state: pending

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
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED, deliberately, because every route restructures a Set
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

- [ ] V-01 validates E-01
  - Required evidence: the pasted closure table with all 41 names classified into the six classes, the command or script that produced it, and the HEAD. Must explicitly state the count of names still DEFINED TWICE and confirm or refute `disable_lane_prompt`'s pinned status by citing `tests/test_runner_shared.py:1238`. A table that merely repeats this plan's numbers without re-deriving them at execution HEAD does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted green run of the characterization suite against UNMODIFIED code, plus the list of agy branches it newly covers (naming the two F-9 sites specifically), plus a sabotage of one pinned branch showing the suite FAILS (a characterization test that cannot fail pins nothing).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: FOUR parts, all pasted. (a) The two added call sites shown in context, with agy's `register_signal_report` count going 3 -> 5 and matching oc's five site-for-site. (b) A test proving a signal after an integration reload reports POST-reload state on BOTH hosts, green. (c) `tests/test_runner_backlog_close.py` green, including `test_both_drivers_emit_the_shutdown_report_on_normal_exit`. (d) `tests/test_runner_shared.py::WrapperTests::test_no_call_site_was_rewritten` green with its 38/36 expectation unchanged (F-11).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the written analysis itself, covering all four parts (a) through (d) that E-04 enumerates, with the six pins of F-10 each stated alongside the substring or AST shape it requires and a verdict on whether a thin caller can satisfy it. Plus an explicit statement that NO split was performed and that OQ-03 remains the maintainer's, so the omission cannot be read as an oversight.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: FOUR parts, all pasted. (a) `python3 -m pytest tests/test_rununify_run_queue.py -o addopts=""` green, including the inverse `disable_lane_prompt` assertion. (b) The BIDIRECTIONAL non-vacuity controls from Required tests item 4, both directions shown failing and then restored. (c) All SEVEN pinned files of F-10 green by name. (d) Bare `python3 -m pytest` with no new failure against the baseline taken at execution HEAD, summary pasted, plus both hosts' suites green by name.
  - Observed evidence:
  - Result: pending

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
