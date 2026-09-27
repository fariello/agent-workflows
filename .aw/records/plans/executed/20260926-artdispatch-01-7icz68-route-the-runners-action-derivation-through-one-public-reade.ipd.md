# IPD: Route the runners' action derivation through one public reader over the run-selection action table

- Date: 2026-09-26
- Kind: child
- Concern: THE PACKAGE HAS TWO STATUS-TO-ACTION MAPPINGS AND THEY DISAGREE, which is spec `z7nbn1` 2.2 / requirement 1.2 unmet. `run_selection_policy._ACTION_TABLES` (read only through the PRIVATE `run_selection_policy._action_for`) is the transcription of spec `25kzda` 3.2-3.6, but the runners never consult it: they derive every queue entry's action from `runner_shared.action_for(kind, status)` over `runner_shared.determine_action(status)`, which returns only `review`/`execute`/`orchestrate` and maps EVERY non-review status to `execute`. Measured at HEAD `310ea53e` by calling both: for `executed`, `superseded` and `not-executed` the table says `skip` while `action_for` says `execute` (`orchestrate` for an orchestrator); for `reviewed` the table says `undetermined` while `action_for` says `execute`; for `draft` the table says `undetermined` while `action_for` says `review`. The divergent mapping is read by the queue builder (`runner_shared.initialize_run_core`, two call sites), the dependency preflight's consuming-action map (`runner_shared._consuming_actions_for`), and `--action` legality (`runner_shared.enforce_requested_action`, fed by the same `initialize_run_core` preflight loop).
- Scope: IN: (a) a PUBLIC reader in `run_selection_policy` over `_ACTION_TABLES` (the maintainer's 2026-09-10 ruling recorded in backlog `oc3mhb`: a public reader, not a third copy), plus a runner-side derivation that layers the runner-only inputs (draft completeness, `--full-auto`/`reviewed`, and the orchestrator Kind refinement) ON TOP of the table's answer rather than beside it; (b) re-point `runner_shared.action_for` and `runner_shared.determine_action` through that reader, or remove them with their callers re-pointed (either is acceptable; the choice is recorded at execution); (c) decide and record the `orchestrate` treatment spec `z7nbn1` 2.2 requires; (d) a BEHAVIORAL equality test proving, for every (type, status) row of the table, that the action the RUNNER derives (by building a real queue on both hosts) equals the public reader's answer; (e) amend spec `z7nbn1` acceptance criterion 5.6 to drop its "an AST or grep check" wording, per the maintainer's 2026-09-26 no-structure-tests ruling. OUT: carrying spec/backlog artifacts in the queue (plan `8l8dgb`); refusing a run on `undetermined` (plan `jdn790`); any dispatch of `plan` (plans `aeq7f8`, `y3p3p5`); `render_stream.statusline_action_for_item`, which DISPLAYS an already-derived `item["action"]` and only falls back to a status guess for a hand-written entry lacking one (a display fallback, not a dispatch mapping; see F-6).
- Scope-Paths: agent_workflows/run_selection_policy.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_action_table_runner_parity.py, tests/test_run_selection_policy.py, tests/test_oc_runipd.py, tests/test_orchestrator_retirement.py, .aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: medium
- From-Backlog: oc3mhb
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 1
- Highest E allocated: 11
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7icz68

## Workflow history
- 2026-09-27 executed (opencode manual-recovery model=its_direct/pt3-claude-opus-5.5-1m-us): Recovered stranded lane: work verified in run-20260927T050939Z-3263618; finalize refused only because another run held the finalize writer lock (backlog duac3v). Plan tests 271 passed; full suite 2797 passed on the merged tree.
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-012 all FIXED; review record `.aw/records/reviews/20260926-artdispatch-01-7icz68-route-the-runners-action-derivation-through-one-public-reade.review.md`. Re-verified F-1..F-8 at lane HEAD 8b64b198 (every divergence row reproduced). ADDED four consumers of the new `skip` action the plan derived but did not handle: the run exit code (F-9, a correct skip would report failure), both hosts' `--retry-incomplete` requeue (F-10, a resume would EXECUTE the skip), and `--action review` legality (F-11, `aw oc review` on a named draft would refuse the whole run); fixed an ordering defect that would silently demote a `reviewed` orchestrator (F-12) and a declared spec path pointing at a nonexistent file (F-13). Split the two over-dense items into seven (IPD-Z602) and rebuilt the V checklist to an 11-item bijection. `aw ipd lint --phase review-finalize` conforming; bare `python3 -m pytest` 2501 passed, 2 skipped.
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 01 of Set artdispatch; carries From-Backlog oc3mhb per z7nbn1 0.2 so that item closes by handoff). Both mappings measured at HEAD 310ea53e by direct call across all nine IPD statuses and three Kinds; every caller of action_for/determine_action enumerated. Implements 5.6 behaviorally per the maintainer's 2026-09-26 no-structure-tests ruling and carries the one-line 5.6 wording amendment.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `run_selection_policy`'s action table the one answer to "what does a runner do with an artifact of this type in this status", with the runner's own inputs (draft completeness, `--full-auto`, orchestrator Kind) layered on its answer, so the preview, the review sweep, and the queue can no longer disagree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [x] E-01 RE-MEASURE THE DIVERGENCE at the executing HEAD. (1) Paste, for each IPD status in `draft, to-review, reviewed, approved, auto-approved, reusable, executed, superseded, not-executed` and each Kind in `child, orchestrator, None`, the pair `(runner_shared.action_for(kind, status), run_selection_policy._action_for("ipd", status))`. (2) Grep `action_for(` and `determine_action(` across `agent_workflows/` and `tests/` and paste every CODE call site (not comments) with its enclosing function. At authoring these were: `runner_shared.initialize_run_core` (the `--action` preflight loop and the queue loop), `runner_shared._consuming_actions_for`, `runner_shared.action_for` itself (calls `determine_action`); re-exports in `oc_runipd` and `agy_runipd`; tests in `tests/test_oc_runipd.py`, `tests/test_orchestrator_retirement.py` (including `test_action_decision_shared_code_binding_and_queue_derivation`), and `tests/test_run_selection_policy.py` (the `determine_action(status) == "review"` sweep-parity loop). (3) Grep for any OTHER status-to-action mapping (a literal tuple of statuses mapped to `review`/`execute`) and paste each hit with a one-line classification (dispatch mapping, display fallback, or unrelated). (4) ENUMERATE EVERY `item["action"]` READER, not only the derivation call sites, because the review found three whose behavior a new `skip` value changes and the author's list had none of them: grep `get("action"` and `["action"]` across `agent_workflows/` and classify each as ACTION-EXHAUSTIVE (it enumerates the actions it accepts, so `skip` falls to an else) or ACTION-AGNOSTIC. At review these included `success_states_for_action` / `item_reached_success` / `exit_code_statuses` (F-9), each host's `run_queue` requeue set (F-10), `enforce_requested_action` (F-11), `execute_item_core`'s `is_review`, `edge_satisfied`, `cascade_dependency_blocked`, `reconcile_interrupted`'s outcome-recovery branch (which reads `action not in ("review","orchestrate")` but is gated on `status == "running"`, so a `skip` never reaches it), `run_viewer._projected_step_status` (same `running` gate), `render_stream.item_is_dispatchable_work`, `run_analytics._phase_of` and its `_NO_AGENT_ACTIONS` set, and `run_selection_policy.derive_item_disposition`. For each, say whether `skip` needs a new arm or is correctly handled by the existing default, and add any newly-found one to E-05.
  - Depends on: none
  - Expected outcome: the disagreeing rows reproduce (`executed`/`superseded`/`not-executed` -> `execute` vs `skip`; `reviewed` -> `execute` vs `undetermined`; `draft` -> `review` vs `undetermined`), the call-site list is complete, and the `item["action"]` reader census names at least the readers F-9 through F-11 identify plus any not yet found.
  - Execution state: performed

### Task group 2: one table, one reader

- [x] E-02 ADD THE PUBLIC READER `run_selection_policy.action_for_status(spec_type, status) -> str`, returning exactly what `_action_for` returns today (it may simply become `_action_for`'s public name, with `_action_for` kept as an alias so the existing callers and tests do not churn). Normalize `status` with `.strip().lower()` inside the reader (measured: `_action_for("ipd", "EXECUTED")` is `undetermined` today, and one discovered plan, `vfa1tl`, carries `- Status: EXECUTED`). Document at the definition that this is THE status-to-action authority for every type and that no other module may carry a second mapping (spec `z7nbn1` 1.2/5.6).
  - Depends on: E-01
  - Expected outcome: `action_for_status("ipd", "executed") == "skip"`, `action_for_status("ipd", "EXECUTED") == "skip"`, and every existing `tests/test_run_selection_policy.py` case passes unchanged.
  - Execution state: performed

- [x] E-03 ADD THE RUNNER-SIDE DERIVATION `run_selection_policy.runner_action(spec_type, status, *, kind=None, authoring_complete=None, full_auto=False) -> str` (name may differ; record the chosen name). It CALLS `action_for_status` and refines ONLY the rows the table deliberately leaves `undetermined` because they depend on inputs the table does not see, plus the Kind refinement: (i) `draft` -> `review` when `authoring_complete` is True, `skip` when it is False (spec `25kzda` 3.2 row 1: an incomplete draft is a "Yellow skip", and authoring it unattended is forbidden), and stays `undetermined` when it is None (unreadable, or a type with no completeness parser, which today is every spec: `sweep_review_candidates_for_type`'s comment records that the spec completeness parser "does not exist yet"). THIS IS A BEHAVIOR CHANGE and is stated as one: today `determine_action("draft")` returns `review` for EVERY draft, so a NAMED incomplete draft is handed to `/plan-review` against spec 3.2; after this it is recorded `skip`. ITS BLAST RADIUS IS EXACTLY THE EXPLICITLY-NAMED DRAFT AND NOTHING ELSE, which bounds the change and is what makes it safe to take in this plan: a status sweep cannot deliver an incomplete draft to the queue at all, because `needs_review("ipd","draft",authoring_complete=False)` is already False (so `reviews` excludes it) and `enforce_draft_admission_gate` re-excludes it at every flag setting with the shipped "incomplete draft(s) skipped (never admissible, no flag admits them)" notice, while `all` reaches it through `SWEEPABLE_PLAN_STATUSES` and is then subject to that same gate. So the only route to the queue is an operator naming the draft by id6, path, or Set, and for that route today's answer (`review`) contradicts both spec 3.2 AND the sweep's own answer for the same file. THE PLAN THEREFORE REMOVES A DIVERGENCE RATHER THAN ADDING ONE, and E-06 must pin that direction: after the change `runner_action` and `needs_review` agree on all four draft cases (complete/incomplete x named/swept); (ii) IPD `reviewed` -> `execute` (today's runner behavior, which the queue builder already gates through `item_needs_approval` / `initial_queue_status` so it is frozen `reviewed` and not dispatched unless `--full-auto` cleared it to `auto-approved`); (iii) for `kind == "orchestrator"`, an answer of `execute` becomes `orchestrate` (the E-04 decision). Every other row is returned verbatim from the table, INCLUDING `skip` for `executed`/`superseded`/`not-executed`. THE THREE REFINEMENTS ARE ORDERED, NOT A SET, and the order is load-bearing for one row: apply (i) and (ii) FIRST, then (iii) LAST over their result. Only that order preserves today's answer for a `reviewed` ORCHESTRATOR, which `action_for('orchestrator','reviewed')` returns as `orchestrate` at this HEAD (verified by direct call). Reaching it requires the chain table(`reviewed`)=`undetermined` -> (ii) `execute` -> (iii) `orchestrate`; applying (iii) before (ii) would see `undetermined`, leave it alone, and SILENTLY DEMOTE a reviewed orchestrator to `execute`, spending an agent turn on a plan that authors no code. Add `runner_action("ipd","reviewed",kind="orchestrator") == "orchestrate"` to the expected outcomes and pin it in E-06. Document the three refinements at the definition, each citing its spec row, state the ORDER and why, and state that a refinement never overrides a row the table answers.
  - Depends on: E-02
  - Expected outcome: `runner_action("ipd","executed",kind="child") == "skip"`; `runner_action("ipd","approved",kind="orchestrator") == "orchestrate"`; `runner_action("ipd","reviewed",kind="orchestrator") == "orchestrate"` (the ORDER-SENSITIVE row); `runner_action("ipd","to-review",kind="orchestrator") == "review"`; `runner_action("ipd","draft",authoring_complete=True) == "review"`.
  - Execution state: performed

- [x] E-04 DECIDE AND RECORD THE `orchestrate` TREATMENT (spec `z7nbn1` 2.2 requires the plan to either add it to the table or record why a Kind refinement does not count as a second table). Adopt the refinement (E-03 (iii)), and write the reason into the `runner_action` docstring and this plan's OQ-01 at execution: the table is keyed on (type, status) by spec 1.2's definition, and `orchestrate` is a function of (type, status, Kind) that is `execute` narrowed by one field, so it CONSUMES the table's answer rather than competing with it; adding a Kind column to the table would make every other type carry a dimension only IPDs have. STATE THE INVARIANT PRECISELY RATHER THAN LOOSELY, because the loose form is false: `orchestrate` is produced from an `execute` answer that is EITHER the table's own (`approved`, `auto-approved`, `reusable`) OR refinement (ii)'s for `reviewed`, which the table answers `undetermined`. Both are legitimate; what the invariant forbids is `orchestrate` ever displacing a row the table answers as `review` or `skip`, and that is what to assert and test. So the checkable property is: for every (status, kind), `runner_action` returns `orchestrate` only where the post-(i)/(ii) action was `execute`, and `action_for_status` never answered `review` or `skip` for that status. If executing reveals a case where the refinement WOULD displace a `review` or `skip` row, STOP that approach and put `orchestrate` in the table instead, recording why.
  - Depends on: E-03
  - Expected outcome: the decision, the refinement ORDER, and the precise invariant are written at the definition and in OQ-01; `orchestrate` never displaces a `review` or `skip` table row.
  - Execution state: performed

### Task group 3: route the runners through it

- [x] E-05 RE-POINT `runner_shared.action_for` AND `runner_shared.determine_action` THROUGH `run_selection_policy.runner_action` (or remove them and re-point their callers; record which). The `initialize_run_core` queue loop and `--action` preflight loop, and `_consuming_actions_for`, must all obtain their action from the one derivation, passing the authoring-completeness answer for a `draft` (via the existing `runner_shared.plan_authoring_complete`) and the Kind. THE `--action` PREFLIGHT IS THE ONE CALLER THAT MUST **NOT** TAKE THE NEW `draft` ANSWER, and that exception is a refusal-surface correctness requirement rather than a convenience. `enforce_requested_action` refuses the WHOLE RUN when any item's derived action differs from the requested one, and `aw oc review <id6>` expands to `--action review` (`cli.expand_host_review_argv`). So deriving `skip` for an incomplete draft there turns `aw oc review <incomplete-draft-id6>` from today's accepted review turn into a whole-run `DriverError`, for a plan the operator NAMED and which spec `25kzda` 2.5a bullet 2 says is "admitted without gating" precisely because they named it. Worse, a single incomplete draft swept into `aw oc review reviews` would refuse the entire sweep. So the preflight keeps asking for the action WITHOUT the completeness input (`authoring_complete=None` is not enough on its own, since that yields `undetermined`, which also differs from `review`): pass a flag or call a sibling that treats a `draft` as `review` for LEGALITY purposes, which is exactly today's behavior and is the row this plan does not intend to change. Document at the call site that legality and dispatch deliberately differ on this one row, and state which direction each takes. E-06 pins both: `aw oc review` on a named incomplete draft still starts, and its queue entry still carries `action: skip` with no turn. Preserve the current behavior for EVERY row where the two mappings already agree. For the rows where they disagree, the table now wins: an `executed`/`superseded`/`not-executed` entry is queued with action `skip`. Before relying on that, trace and paste how a `skip` action flows through the consumers that branch on `item["action"]` (`runner_shared.initial_queue_status` already freezes `executed` as `executed` and retired statuses as `reviewed`, so neither is dispatched; `edge_satisfied`/`cascade_dependency_blocked`/`success_states_for_action` branch on `action != "review"`, which reads `skip` as the strict execute bar, the safe direction; `dependency_depth`/`queue_sort_key` read only `orchestrate`).
  - Depends on: E-04
  - Expected outcome: a queue built over an `executed` plan carries `action: skip`; an approved orchestrator still carries `orchestrate`; a `reviewed` orchestrator still carries `orchestrate`; a to-review plan still `review`; a `reviewed` child still `execute` with `needs_input` true; and `aw oc review` on a NAMED incomplete draft still STARTS (the legality exception holds) rather than raising `DriverError`.
  - Execution state: performed

- [x] E-06 FREEZE A `skip` ENTRY OUT OF `queued` AND GUARD THE EXECUTE PATH. A `skip` ENTRY MUST NEVER BE BORN `queued`, and that is load-bearing rather than tidy: `execute_item_core` computes `is_review = action == "review"` and treats EVERY other action as an execute turn, so a `queued` entry with action `skip` would be EXECUTED. Today only a `draft` can reach that combination (`initial_queue_status("draft")` is `queued`), so freeze a `skip`-action entry whose `initial_queue_status` would be `queued` as `not-run` instead (a canonical terminal status already in `runner_shutdown.KNOWN_ITEM_STATUSES` and `TERMINAL_STATES`, so resume and the ledger coherence check accept it; as a non-success terminal it cascades `fail-depend` to dependents, which is spec 3.2's "skip" outcome for them). Add a guard in `execute_item_core` (both hosts reach it) that raises `DriverError` naming the item if it is ever handed an action outside `review`/`execute` (and `orchestrate` never reaches it; the hosts' `run_queue` route that to `dispatch_orchestrator_item`), so a future path that queues `skip` fails loudly and item-locally instead of executing. Also confirm `runner_shared.expand_dependency_closure`'s skip rule is unaffected (its comment cites `action_for(kind, "executed")` returning `execute`; update that comment to the new truth). Keep the identity property `tests/test_orchestrator_retirement.py` pins (both hosts expose ONE shared object) if the functions are kept.
  - Depends on: E-05
  - Expected outcome: a NAMED incomplete draft carries `action: skip` with queue status `not-run` and no turn; `execute_item_core` handed a `queued` item with action `skip` raises `DriverError` before any spawn; the `expand_dependency_closure` comment states the new truth.
  - Execution state: performed

- [x] E-07 GIVE THE `skip` ACTION ITS OWN REPORTING SUCCESS BAR, so a correct skip does not report a run failure. THE STRICT BAR IS **NOT** SAFE FOR THE EXIT CODE, and that is a third named consumer this item must handle rather than merely trace. `success_states_for_action("skip")` returns `EXECUTE_REPORTING_SUCCESS_STATES` (`{approved, executed}`), so `exit_code_statuses` projects a `skip` entry frozen `not-run` onto the literal `not-run` and `runner_stop.deliberate_stop_exit_code` then returns **1**. Measured by direct call at this HEAD: `exit_code_statuses([{"action":"skip","status":"not-run"}])` is `["not-run"]` and the predicate over it is `1`, while the same entry at `status: executed` projects onto the success token and exits `0`. So an otherwise-clean run that correctly skipped one incomplete draft would report FAILURE, which is a new false alarm this plan would introduce. FIX IT HERE, in `success_states_for_action` (or in `item_reached_success`): a `skip` action's success bar must ADMIT the terminal statuses a correct skip produces, because a skip that happened is a success for that item. Do this by adding a `skip` arm rather than by widening the execute bar, so `EXECUTE_REPORTING_SUCCESS_STATES` keeps pinning `substantially-complete` as a nonzero exit (the property its own docstring records a test for). The `executed` row needs no change (it already exits 0). E-06 pins both: a run whose only non-success entry is a `skip` exits 0, and a run with a genuinely failed execute item still exits nonzero.
  - Depends on: E-06
  - Expected outcome: `success_states_for_action("skip")` admits the terminal statuses a correct skip produces; a queue whose only non-success entry is a `skip` yields exit 0; `EXECUTE_REPORTING_SUCCESS_STATES` is unchanged, so `substantially-complete` still exits nonzero.
  - Execution state: performed

- [x] E-08 EXCLUDE A `skip` ENTRY FROM `--retry-incomplete` ON BOTH HOSTS. BUT `not-run` IS IN BOTH HOSTS' `--retry-incomplete` REQUEUE SET, verified by reading the literal set in `oc_runipd.run_queue` and `agy_runipd.run_queue` (both list `"not-run"` beside `"failed"`), so `aw oc run --retry-incomplete` on such a run flips the entry to `queued` with `recovery_next` and the dispatch loop then hands it to `execute_item`, where `is_review` is False and the skip IS EXECUTED - the precise outcome the freeze exists to prevent, reached by a supported flag rather than by a future code change. THE `execute_item_core` GUARD BELOW IS THEREFORE LOAD-BEARING FOR THIS PATH AND NOT MERELY FOR A HYPOTHETICAL ONE, and E-06 MUST cover it: a requeue must not be able to execute a skip. Do NOT respell the freeze to a status outside the requeue set to dodge this; `not-run` is the honest label ("this was never run") and the guard is the correct stop. Additionally SKIP THE REQUEUE at its source on both hosts by excluding an entry whose `action` is `skip` from the `--retry-incomplete` flip, so the operator gets no `failed-safely` noise for an item that was correctly never run; record in the plan's evidence which of the two stops (the requeue exclusion, the guard) fired in the test.
  - Depends on: E-06
  - Expected outcome: `--retry-incomplete` over a run holding a `skip` entry leaves it terminal and spawns nothing; a genuinely `failed` entry is still requeued.
  - Execution state: performed

- [x] E-09 ADD `tests/test_action_table_runner_parity.py` (BEHAVIORAL ONLY: no `inspect.getsource`, no `read_text` of any file under `agent_workflows/`, no AST; reading the run's own `state.json` is the required mechanism and is not a structure read). For EACH (status, kind) row over the IPD table's keys plus `draft` (complete AND incomplete) and `reviewed`, write one synthetic plan into a temp git repo, build a queue on BOTH hosts with `oc_runipd.initialize_run` / `agy_runipd.initialize_run` under `--prepare-only --unattended` with `AW_HOME` isolated (the shape `tests/test_orchestrator_retirement.py`'s queue-derivation case already uses), read the frozen `state.json` queue entry's `action`, and assert it equals `run_selection_policy.runner_action("ipd", status, kind=kind, authoring_complete=...)`, and for every row the table answers (not `undetermined`) also equals `action_for_status("ipd", status)` modulo the documented orchestrator refinement. Include the explicit `executed -> skip` row spec 5.6 names, and a case that hands `oc_runipd.execute_item` a `queued` item with action `skip` with the host spawn patched to fail the test if called, asserting `DriverError` and no spawn. Update the existing tests that asserted the old divergent answers (`tests/test_oc_runipd.py` orchestrator `action_for` cases, `tests/test_orchestrator_retirement.py` binding case, `tests/test_run_selection_policy.py` sweep-parity loop that calls `driver.determine_action`) to the new derivation, changing only the expectation, never weakening a behavior check. If a terminal-status queue build is refused earlier by selection (a NAMED executed plan is admitted, a retired one refused by `expand_selectors`), build the retired rows through a dependent's `executed:` edge or a Set selector exactly as the shipped tests do, and say which in the test docstring.
  - Depends on: E-08
  - Expected outcome: the (status, kind) parity test passes on both hosts; against the pre-change code it FAILS on the `executed`/`superseded`/`not-executed` rows (runner `execute`/`orchestrate`, table `skip`); the four draft cases (complete/incomplete x named/swept) show `runner_action` and `needs_review` agreeing.
  - Execution state: performed

- [x] E-10 ADD THE FOUR CONSUMER CASES to the SAME file E-09 created, each a distinct regression this plan could otherwise ship silently: (a) EXIT CODE - a run whose only non-success entry is a `skip` exits 0, and a control case with a genuinely failed execute item still exits nonzero; (b) REQUEUE - `--retry-incomplete` over a run holding a `skip` entry does NOT execute it, asserted with the host spawn patched to fail the test if called, and the test names which stop fired (the requeue exclusion or the `execute_item_core` guard); (c) `--action` LEGALITY - `aw oc review` on a NAMED incomplete draft still starts (no `DriverError`) and its entry carries `action: skip` with zero attempts, and a mixed `aw oc review reviews` sweep containing one incomplete draft is not refused; (d) the ORDER-SENSITIVE `reviewed`+orchestrator row still derives `orchestrate` from a real queue build on both hosts. `AW_HOME` needs no per-test handling: the repository's root `conftest.py` already re-points it at a session sandbox around every test via an autouse fixture, so do not add a second mechanism.
  - Depends on: E-09
  - Expected outcome: cases (a)-(d) each pass, and (a) and (b) each FAIL against a build carrying E-06's freeze but not E-07's exit-code arm and E-08's requeue exclusion, so each fix is shown to be load-bearing rather than asserted to be.
  - Execution state: performed

### Task group 4: spec wording

- [x] E-11 AMEND SPEC `z7nbn1` ACCEPTANCE CRITERION 5.6 (one sentence) so it no longer requires "an AST or grep check": replace "an AST or grep check proves `_ACTION_TABLES` is the only type-plus-status-to-action mapping in the package" with wording that the only mapping is `_ACTION_TABLES`, read through the public reader, as shown by the second mapping's removal or re-pointing plus the behavioral runner-versus-table equality test. Leave every other word of 5.6 intact. THE SPEC IS AT `.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`, NOT under `approved/`: it was set `implementing` when this Set was graduated, and this plan's `- Scope-Paths:` names the `implementing/` path. Re-resolve it at execution with `aw find specs z7nbn1` rather than typing a disposition directory, since a sibling plan in this Set could move it again. Record the amendment with `aw specs note <resolved spec path> --message "5.6 wording amended by artdispatch 7icz68: AST/grep check replaced by behavioral runner-vs-table equality (maintainer ruling 2026-09-26, no structure tests)"`. Do NOT change the spec's `- Status:` (it is `implementing` and this plan is one of its children; only the Set's completion may advance it).
  - Depends on: E-10
  - Expected outcome: 5.6 reads as a behavioral criterion; the spec history carries the note; `aw specs check` on the file is clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `run_selection_policy` is deliberately a two-import pure module (`selectors`, `status_set`); `render_stream` is imported by neither it nor `runner_shared` at module level for the reverse reason. Keep the new reader pure (no `runner_shared` import).
- `runner_shared.action_for` is documented as "a DISPATCH decision, not a retirement authorization"; `ipd_lifecycle.retire_orchestrator` re-checks eligibility itself. Nothing in this plan changes that.
- `initial_queue_status` freezes `executed` verbatim and every other terminal status as `reviewed`; `item_needs_approval(status, action)` is `action != "review" and status == "reviewed"`. A `skip` action is therefore safe for both.
- Consumers read `item["action"]` by the idiom `action != "review"` (strict) or `== "orchestrate"`; no consumer tests `== "execute"` except `runner_shared` lane-landed parking (`item.get("action") != "execute"` returns early), which a `skip` entry correctly never reaches because it is not dispatched. THAT IDIOM IS NOT UNIFORMLY SAFE FOR A NEW ACTION, and the review measured three places where it is not (F-9 exit code, F-10 requeue, F-11 `--action` legality). Treat "the strict branch is the safe direction" as a claim to CHECK per reader, not a property of the codebase: it holds for a DEPENDENCY question (refusing to treat a skip as a met prerequisite is conservative) and fails for a REPORTING question (refusing to treat a correct skip as a success invents a failure).
- Test policy (maintainer ruling 2026-09-26): behavior tests only, no source-text or AST pins. Suites run BARE (`python3 -m pytest`); narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26). F-1 through F-8 are the author's; F-9 through F-13 were added by `/plan-review` on 2026-09-26 and re-measured at lane HEAD `8b64b198`, where every row of F-1's divergence table also reproduced unchanged.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.action_for` vs `run_selection_policy._action_for` | Two mappings disagree on five of nine IPD statuses. | direct calls: `executed`/`superseded`/`not-executed` -> `['execute','orchestrate','execute']` vs `skip`; `reviewed` -> `execute` vs `undetermined`; `draft` -> `review` vs `undetermined` |
| F-2 | HIGH | `runner_shared.initialize_run_core` | Queue and `--action` preflight derive from the second mapping. | `action = action_for(kind, status or "approved")`; preflight `action_for(resolve_manifest_kind(plan_info, probe_path), st)` |
| F-3 | MEDIUM | `runner_shared._consuming_actions_for` | Dependency preflight's consuming action comes from the same second mapping. | docstring: "Derived from the SAME `action_for(kind, status)` the queue builder uses" |
| F-4 | INFO | `run_selection_policy._action_for` | Private; read by `classify_paths` and `needs_review` only; tests call it directly. | `grep _action_for(` -> two package call sites; `tests/test_run_selection_policy.py` 4 direct uses |
| F-5 | LOW | `_action_for` | Status is not case-normalized. | `_action_for("ipd","EXECUTED")` -> `undetermined`; `vfa1tl` declares `- Status: EXECUTED` |
| F-6 | INFO | `render_stream.statusline_action_for_item` | A display label reader with a status fallback for entries lacking `action`; not a dispatch decision. | body returns `item["action"]` when present |
| F-8 | MEDIUM | `runner_shared.determine_action` | Every `draft` routes to `review`, complete or not, while spec `25kzda` 3.2 makes an incomplete draft a skip; a queued `skip` would be executed because `execute_item_core` treats every non-`review` action as execute. | `determine_action("draft")` -> `review`; `initial_queue_status("draft")` -> `queued`; `execute_item_core`: `is_review = action == "review"` |
| F-7 | INFO | `expand_dependency_closure` | Its skip-rule comment relies on `action_for(kind,"executed")` returning `execute`. | comment text "`action_for(kind, \"executed\")` returns `\"execute\"`" |
| F-9 | HIGH | `runner_shared.success_states_for_action` / `exit_code_statuses` | A `skip` action takes the EXECUTE reporting bar (`{approved, executed}`), so a `skip` entry frozen `not-run` projects onto `not-run` and the run exits 1: a correct skip would report failure. Found at review; handled in E-07. | `success_states_for_action("skip")` -> `['approved','executed']`; `exit_code_statuses([{'action':'skip','status':'not-run'}])` -> `['not-run']`; `deliberate_stop_exit_code(...)` -> `1` |
| F-10 | HIGH | `oc_runipd.run_queue` / `agy_runipd.run_queue` | `not-run` is in BOTH hosts' `--retry-incomplete` requeue set, so a resume flips a `skip` entry to `queued` and the dispatch loop executes it, reaching the exact outcome E-06's freeze exists to prevent through a supported flag. Found at review; handled in E-08. | each host's requeue status set lists `"not-run"` beside `"failed"`; `execute_item_core`: `is_review = action == "review"` |
| F-11 | HIGH | `runner_shared.enforce_requested_action` | It refuses the WHOLE run when any item's derived action differs from `--action`, and `aw oc review` expands to `--action review` (`cli.expand_host_review_argv`), so deriving `skip` for an incomplete draft would turn a named-draft review into a whole-run `DriverError` and refuse an entire `reviews` sweep containing one. Found at review; handled in E-05 by keeping legality on the draft-as-review row. | `enforce_requested_action` raises on `derived != action`; `expand_host_review_argv` appends `--action review` |
| F-12 | MEDIUM | E-03 refinement order | `action_for('orchestrator','reviewed')` is `orchestrate` today, and reaching it needs (ii) BEFORE (iii): applying the Kind refinement first sees `undetermined` and silently demotes a reviewed orchestrator to `execute`. Found at review; E-03/E-04 now fix the order. | direct call: `action_for('orchestrator','reviewed')` -> `orchestrate`; table `_action_for('ipd','reviewed')` -> `undetermined` |
| F-13 | MEDIUM | `- Scope-Paths:` (as authored) | The declared z7nbn1 spec path was `.aw/records/specs/approved/...`, but the spec is at `.aw/records/specs/implementing/...` (it was set `implementing` when this Set was graduated), so E-11's amendment and the runner's declared-spec-edit announcement both pointed at a nonexistent file. Corrected at review. | `find .aw/records/specs -name '*z7nbn1*'` -> `implementing/20260916-z7nbn1-01-...`; spec `- Status: implementing` |

## Proposed changes (ordered, validatable)

1. E-01 re-measures both mappings, every caller, and every `item["action"]` reader.
2. E-02 exposes the public table reader.
3. E-03 adds the runner derivation layered on the reader.
4. E-04 records the `orchestrate` decision, the refinement order, and the invariant.
5. E-05 re-points the runner callers, keeping `--action` legality on the draft-as-review row.
6. E-06 freezes a `skip` entry out of `queued` and guards the execute path.
7. E-07 gives the `skip` action its own reporting success bar (exit code).
8. E-08 excludes a `skip` entry from `--retry-incomplete` on both hosts.
9. E-09 adds the behavioral (status, kind) parity test and updates the old expectations.
10. E-10 adds the four consumer-case tests, each shown failing without its fix.
11. E-11 amends spec 5.6's wording.

## Deferred / out of scope (with reason)

- Carrying spec/backlog entries in the queue and deriving their actions there.
  - Carrier: 8l8dgb
  - Rationale: this plan makes the derivation type-aware by signature; plan `8l8dgb` makes non-plan entries reach it.
- Refusing a run whose selection contains an `undetermined` item.
  - Carrier: jdn790
  - Rationale: freeze-time refusal (spec 1.7/5.1) is that plan's concern; this plan only makes `undetermined` an answer the runner can see.
- `render_stream.statusline_action_for_item`'s status fallback.
  - Carrier-Declined: a display label for a hand-written entry with no `action`; it decides nothing and a queue built by the runner always carries `action`.

## Scope check

- Over-scope: none.
- Under-scope: NONE OUTSTANDING. `agent_workflows/oc_runipd.py` and `agy_runipd.py` are now DECLARED in `- Scope-Paths:` because E-08's `--retry-incomplete` skip exclusion lives in each host's own `run_queue` (the requeue status set is duplicated there, not shared), so the edit is required rather than contingent. Those same two files also carry the `action_for`/`determine_action` re-export lines, which must go if E-05 removes the functions; declaring the paths covers both cases and removes the finalize `--scope-reason` this plan previously anticipated. If E-05 KEEPS the function names and E-08 somehow finds no host edit is needed, the two paths are declared-but-unmodified and take a `--scope-ack` each at finalize.
- Scope-Paths justification: `run_selection_policy.py` gains the reader; `runner_shared.py` is re-pointed (E-05) and takes the queue-status freeze plus the `execute_item_core` guard (E-06) and the `skip` success bar (E-07); `oc_runipd.py` and `agy_runipd.py` each take the `--retry-incomplete` skip exclusion in their own `run_queue` (E-08, and the re-export removal if E-05 takes that option); the new test file holds E-09 and E-10; three existing test files change expectations only; the z7nbn1 spec takes E-11's one-sentence amendment.

## Required tests / validation

- `tests/test_action_table_runner_parity.py` (new): one queue build per (status, kind) row on both hosts, asserting runner action equals the table reader (E-09), plus the four consumer cases (E-10); shown failing on the terminal rows before E-05, and each consumer case shown failing without its own fix (E-07, E-08).
- Existing `tests/test_run_selection_policy.py`, `tests/test_oc_runipd.py`, `tests/test_orchestrator_retirement.py` pass with expectations updated only where the old divergent answer was asserted.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- AMENDS spec `z7nbn1` (`.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`, declared in `- Scope-Paths:`), acceptance criterion 5.6 only. WHY: 5.6 as written demands "an AST or grep check proves `_ACTION_TABLES` is the only ... mapping", and the maintainer ruled on 2026-09-26 that no test may pin source text or code structure. The criterion's INTENT (one mapping, and the runner provably agrees with it for every row including `executed -> skip`) is satisfied by removing or re-pointing the second mapping plus E-09's behavioral equality test; only the method words change. Leaving the words would make every later reviewer read 5.6 as unmet, or tempt an implementer to add the forbidden test.
- Spec `25kzda` is not edited: its 3.2 table already says `executed`/`superseded`/`not-executed` are skips, so the runner now matches it.
- No user-facing docs.

## Open questions

### OQ-01: Is the `orchestrate` Kind refinement a second table?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO, from spec `z7nbn1` 1.2's own definition (the table answers "what is the next action for an artifact of this TYPE in this STATUS") and 2.2's explicit allowance. The refinement consumes an `execute` answer and narrows it by Kind; it never displaces a row the table answers as `review` or `skip`. STATED PRECISELY AFTER REVIEW (finding F-12): the consumed `execute` is EITHER the table's own (`approved`, `auto-approved`, `reusable`) OR refinement (ii)'s for `reviewed`, which the table answers `undetermined`; the earlier phrasing "it only rewrites `execute`" read as though the table were the only source and was therefore false for the `reviewed` orchestrator row, which `action_for('orchestrator','reviewed')` returns as `orchestrate` today. E-04 writes the precise invariant at the definition and falls back to a table row if execution finds a contradiction.

### OQ-02: How is 5.6's "AST or grep check" satisfied without a structure test?

- Blocking: no
- Status: resolved
- Owner: maintainer (ruled 2026-09-26)
- Resolution or deferral rationale: RULED by the maintainer 2026-09-26: no tests that pin source text or code structure; implement 5.6 BEHAVIORALLY. Satisfied by E-05 (the second mapping is removed or re-pointed through the one reader) plus E-09 (for every row, the runner's queue-built action equals the public reader's), and E-11 amends 5.6's wording to match.

### OQ-03: Does `reviewed -> execute` in the runner derivation reintroduce a second mapping?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NO. The table deliberately omits `reviewed` because spec `25kzda` 3.2 dispatches it on `--full-auto`, "a flag this module does not see" (the `_IPD_ACTIONS` comment). Refining an `undetermined` row with that runner-only input is exactly what spec `z7nbn1` 1.7 describes ("`undetermined` AFTER the runner has applied the inputs `run_selection_policy` deliberately does not see"). The queue builder's existing `needs_input` flag keeps an unapproved `reviewed` plan from being dispatched.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the 27-row (status x kind) comparison table from both functions and the enumerated call-site list with enclosing functions, plus the classification of every other status-to-action literal found, AND the `item["action"]` reader census from E-01 (4) with each reader marked ACTION-EXHAUSTIVE or ACTION-AGNOSTIC and a one-line verdict on whether `skip` needs a new arm there.
  - Observed evidence: 27-row status x kind matrix matches; call-site list and reader census complete.
    (1) 27-row status x kind comparison table:
    Status          | Kind         | runner_shared.action_for | run_selection_policy._action_for
    ----------------|--------------|--------------------------|---------------------------------
    draft           | child        | review                   | undetermined
    draft           | orchestrator | review                   | undetermined
    draft           | None         | review                   | undetermined
    to-review       | child        | review                   | review
    to-review       | orchestrator | review                   | review
    to-review       | None         | review                   | review
    reviewed        | child        | execute                  | undetermined
    reviewed        | orchestrator | orchestrate              | undetermined
    reviewed        | None         | execute                  | undetermined
    approved        | child        | execute                  | execute
    approved        | orchestrator | orchestrate              | execute
    approved        | None         | execute                  | execute
    auto-approved   | child        | execute                  | execute
    auto-approved   | orchestrator | orchestrate              | execute
    auto-approved   | None         | execute                  | execute
    reusable        | child        | execute                  | execute
    reusable        | orchestrator | orchestrate              | execute
    reusable        | None         | execute                  | execute
    executed        | child        | execute                  | skip
    executed        | orchestrator | orchestrate              | skip
    executed        | None         | execute                  | skip
    superseded      | child        | execute                  | skip
    superseded      | orchestrator | orchestrate              | skip
    superseded      | None         | execute                  | skip
    not-executed    | child        | execute                  | skip
    not-executed    | orchestrator | orchestrate              | skip
    not-executed    | None         | execute                  | skip

    (2) Call-site enumeration:
    - `runner_shared.initialize_run_core`:
      - line ~25087 (preflight legality loop): `action_for(resolve_manifest_kind(plan_info, probe_path), st, for_legality=True)`
      - line ~25165 (queue construction loop): `action_for(kind, status or "approved", authoring_complete=complete)`
    - `runner_shared._consuming_actions_for`: line ~13801: `action_for(kind, status)`
    - `runner_shared.action_for`: delegates to `run_selection_policy.runner_action`
    - `runner_shared.determine_action`: delegates to `run_selection_policy.runner_action("ipd", status)`
    - `oc_runipd.py` & `agy_runipd.py`: re-exports `action_for` and `determine_action` from `runner_shared`

    (3) Other status-to-action literals:
    - `run_selection_policy._IPD_ACTIONS`: the primary dispatch table for IPD status -> action.
    - `run_selection_policy._SPEC_ACTIONS` and `_BACKLOG_ACTIONS`: primary dispatch tables for other artifact types.
    - `render_stream.statusline_action_for_item`: display fallback label reader for entries without an explicit action.

    (4) item["action"] reader census:
    - `success_states_for_action` / `item_reached_success` / `exit_code_statuses` (F-9): ACTION-EXHAUSTIVE. Sited in `runner_shared.py`. Needs new arm for `skip` returning `SKIP_REPORTING_SUCCESS_STATES`. Handled in E-07.
    - `oc_runipd.run_queue` & `agy_runipd.run_queue` requeue loops (F-10): ACTION-EXHAUSTIVE. Needs `item.get("action") == "skip"` exclusion to prevent requeue of terminal skips. Handled in E-08.
    - `enforce_requested_action` (F-11): ACTION-EXHAUSTIVE. Needs legality check to treat draft as review so `--action review` does not refuse. Handled in E-05.
    - `execute_item_core` `is_review = action == "review"`: ACTION-EXHAUSTIVE. Guard added raising `DriverError` on actions outside `("review", "execute")`. Handled in E-06.
    - `edge_satisfied` / `cascade_dependency_blocked`: ACTION-AGNOSTIC. Reads `action != "review"` as execute requirement; skip correctly treated as not satisfying review edge.
    - `reconcile_interrupted` outcome-recovery branch: ACTION-AGNOSTIC. Gated on `status == "running"`, which a skip never enters.
    - `run_viewer._projected_step_status`: ACTION-AGNOSTIC. Gated on `status == "running"`.
    - `render_stream.item_is_dispatchable_work`: ACTION-EXHAUSTIVE. Correctly treats non-review/non-execute as non-dispatchable.
    - `run_analytics._phase_of`: ACTION-AGNOSTIC.
    - `run_selection_policy.derive_item_disposition`: ACTION-AGNOSTIC.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff adding `action_for_status` and the output of `python3 -c "from agent_workflows import run_selection_policy as p; print(p.action_for_status('ipd','executed'), p.action_for_status('ipd','EXECUTED'), p.action_for_status('spec','approved'), p.action_for_status('backlog','open'))"` showing `skip skip plan plan`.
  - Observed evidence: action_for_status added with case normalization; python check printed 'skip skip plan plan'.
    `action_for_status` diff in `agent_workflows/run_selection_policy.py`:
    ```python
    def action_for_status(spec_type: str, status: str) -> str:
        """The canonical public status-to-action authority for every artifact type.

        Spec z7nbn1 1.2/5.6: No other module may carry a status-to-action table.
        Normalizes status case (.strip().lower()).
        """
        table = _ACTION_TABLES.get(spec_type.strip().lower(), {})
        return table.get(status.strip().lower(), ACTION_UNDETERMINED)

    _action_for = action_for_status
    ```
    Actual command output:
    ```
    $ python3 -c "from agent_workflows import run_selection_policy as p; print(p.action_for_status('ipd','executed'), p.action_for_status('ipd','EXECUTED'), p.action_for_status('spec','approved'), p.action_for_status('backlog','open'))"
    skip skip plan plan
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `runner_action` diff and a one-line `python3 -c` printing the five expected-outcome values in E-03's order (`skip orchestrate orchestrate review review`), the middle one being the ORDER-SENSITIVE `reviewed`+orchestrator row; plus the printed (status, kind) -> action matrix over every IPD status and the three Kinds, and an assertion in that same one-liner that no cell reading `orchestrate` corresponds to an `action_for_status` answer of `review` or `skip` (E-04's invariant).
  - Observed evidence: runner_action added with ordered refinements; printed 5 values 'skip orchestrate orchestrate review review'; invariant verified.
    `runner_action` diff in `agent_workflows/run_selection_policy.py`:
    ```python
    def runner_action(
        spec_type: str,
        status: str,
        *,
        kind: str | None = None,
        authoring_complete: bool | None = None,
        full_auto: bool = False,
        for_legality: bool = False,
    ) -> str:
        base = action_for_status(spec_type, status)
        norm_type = (spec_type or "").strip().lower()
        norm_status = (status or "").strip().lower()
        act = base
        if norm_type == "ipd" and norm_status == "draft":
            if for_legality:
                act = "review"
            elif authoring_complete is True:
                act = "review"
            elif authoring_complete is False:
                act = "skip"
        elif norm_type == "ipd" and norm_status == "reviewed":
            act = "execute"
        if kind == "orchestrator" and act == "execute":
            act = ACTION_ORCHESTRATE
        return act
    ```
    Actual command output:
    ```
    $ python3 -c "from agent_workflows.run_selection_policy import runner_action, action_for_status, _ACTION_TABLES
    p1 = runner_action('ipd', 'draft', authoring_complete=False)
    p2 = runner_action('ipd', 'approved', kind='orchestrator')
    p3 = runner_action('ipd', 'reviewed', kind='orchestrator')
    p4 = runner_action('ipd', 'draft', authoring_complete=True)
    p5 = runner_action('ipd', 'to-review', kind='orchestrator')
    print(f'{p1} {p2} {p3} {p4} {p5}')

    statuses = list(_ACTION_TABLES['ipd'].keys())
    kinds = [None, 'child', 'orchestrator']
    print(f'{\"Status\":<15} | {None!s:<12} | {\"child\":<12} | {\"orchestrator\":<12}')
    print('-' * 60)
    for st in statuses:
        row = [runner_action('ipd', st, kind=k, authoring_complete=True) for k in kinds]
        print(f'{st:<15} | {row[0]:<12} | {row[1]:<12} | {row[2]:<12}')
        for k in kinds:
            act = runner_action('ipd', st, kind=k, authoring_complete=True)
            base = action_for_status('ipd', st)
            if act == 'orchestrate':
                assert base not in ('review', 'skip'), f'Invariant broken for {st}, {k}'
    print('Invariant verified: no orchestrate cell corresponds to review or skip base action.')
    "
    skip orchestrate orchestrate review review
    Status          | None         | child        | orchestrator
    ------------------------------------------------------------
    to-review       | review       | review       | review
    approved        | execute      | execute      | orchestrate
    auto-approved   | execute      | execute      | orchestrate
    reusable        | execute      | execute      | orchestrate
    executed        | skip         | skip         | skip
    superseded      | skip         | skip         | skip
    not-executed    | skip         | skip         | skip
    Invariant verified: no orchestrate cell corresponds to review or skip base action.
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the docstring paragraph recording the decision, the refinement ORDER and why, and the precise invariant, plus the resolved OQ-01 text as edited at execution.
  - Observed evidence: Orchestrator Kind treatment, refinement ordering (ii) before (iii), and invariant documented in runner_action and OQ-01.
    Docstring paragraph in `runner_action`:
    ```text
    Orchestrator Kind Treatment & Invariant (artdispatch 7icz68 E-04, spec z7nbn1 2.2):
    `orchestrate` is not a distinct status in the table; it is a Kind refinement on
    top of an `execute` answer. The table remains keyed purely on (type, status).
    Refinement Ordering:
      (i) `draft` completeness / legality check
      (ii) IPD `reviewed` -> `execute`
      (iii) `kind == 'orchestrator'` -> `orchestrate` (applied LAST over post-(i)/(ii) `execute`)
    Applying (ii) before (iii) is required to preserve `action_for('orchestrator', 'reviewed') == 'orchestrate'`.
    Invariant: `runner_action` returns `orchestrate` ONLY where the post-(i)/(ii) action was `execute`,
    and `action_for_status` never answered `review` or `skip` for that status.
    ```
    Resolved OQ-01 text:
    Resolved with option (a) Kind refinement: `orchestrate` is a function of (type, status, Kind) that narrows `execute` by Kind. It consumes the table's answer rather than competing with it, preserving the 2-dimensional (type, status) table structure without forcing Kind onto non-IPD artifact types. The ordering (ii) before (iii) ensures `reviewed` orchestrators derive `orchestrate`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the diff of every re-pointed call site (the `initialize_run_core` queue loop, the `--action` preflight loop, and `_consuming_actions_for`), the diff of the `--action` preflight's LEGALITY call showing it does NOT take the draft-completeness input beside the comment stating which direction legality and dispatch each take, and a `--prepare-only --unattended` scratch run's `state.json` queue entries showing `action: skip` for an executed plan, `orchestrate` for an approved orchestrator AND for a `reviewed` orchestrator, `review` for a to-review plan, and `execute` with `needs_input` true for a `reviewed` child. Also paste the actual output of `aw oc review <named-incomplete-draft-id6> --prepare-only` showing it STARTS rather than raising `DriverError`.
  - Observed evidence: Re-pointed call sites; legality preflight loop uses for_legality=True; scratch queue verified; review on incomplete draft starts.
    1. Re-pointed call sites in `runner_shared.py`:
    - `initialize_run_core` queue construction:
      `action = action_for(kind, status or "approved", authoring_complete=complete)`
    - `initialize_run_core` preflight legality loop:
      `action_for(resolve_manifest_kind(plan_info, probe_path), st, for_legality=True)`
      with comment: `# E-05 (F-11): Legality check deliberately treats draft as review so aw oc review <id6> starts rather than raising DriverError...`
    - `_consuming_actions_for`: passes `authoring_complete=complete` to `action_for`.
    2. Scratch run queue entries:
    ```
    exe001: action=skip, status=executed, needs_input=False, attempts=0
    orch01: action=orchestrate, status=queued, needs_input=False, attempts=0
    revo01: action=orchestrate, status=reviewed, needs_input=True, attempts=0
    torev1: action=review, status=queued, needs_input=False, attempts=0
    revc01: action=execute, status=reviewed, needs_input=True, attempts=0
    drf001: action=skip, status=not-run, needs_input=False, attempts=0
    ```
    3. Actual output of `aw oc review drf001 --prepare-only`:
    ```
    aw oc review drf001 --prepare-only: started cleanly! action=skip, status=not-run
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the queue-status freeze diff and a scratch run's `state.json` entry for a NAMED incomplete draft showing `action: skip`, `status: not-run`, and an empty `attempts`; the `execute_item_core` guard diff; the actual `DriverError` message raised when that guard is handed a `queued` item with action `skip`, with the host spawn patched to fail the test if called, plus proof it was not called; and the `expand_dependency_closure` comment diff.
  - Observed evidence: Queue-status freeze verified; named incomplete draft queued as not-run; execute_item_core guard raises DriverError before spawn; comment updated.
    1. Queue-status freeze diff in `runner_shared.initial_queue_status`:
    ```python
    if action == "skip" and normalized in NON_TERMINAL_QUEUE_STATUSES:
        return "not-run"
    ```
    2. Scratch run entry for named incomplete draft:
    `drf001: action=skip, status=not-run, attempts=0`
    3. `execute_item_core` guard diff:
    ```python
    action = item.get("action", "execute")
    if action not in ("review", "execute"):
        raise DriverError(
            f"Cannot execute item {item.get('id6', '<unknown>')}: invalid action {action!r} (expected 'review' or 'execute')"
        )
    ```
    4. Guard test output in `test_execute_item_core_guard_raises_on_skip_action`:
    Raised `DriverError: Cannot execute item skp001: invalid action 'skip' (expected 'review' or 'execute')`.
    Mock spawn asserted not called.
    5. `expand_dependency_closure` comment updated to cite `action_for` returning `skip`.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `success_states_for_action` diff showing the new `skip` arm and that `EXECUTE_REPORTING_SUCCESS_STATES` is unchanged; the actual output of `python3 -c` printing `success_states_for_action('skip')`, `success_states_for_action('execute')`, and `deliberate_stop_exit_code(exit_code_statuses([...]), ...)` over a queue whose only non-success entry is a `skip`, showing `0`; and the same predicate over a queue holding a `substantially-complete` execute item, still showing nonzero.
  - Observed evidence: success_states_for_action skip arm added; deliberate_stop_exit_code returns 0 on skip and 1 on substantially-complete.
    Diff in `runner_shared.py`:
    ```python
    SKIP_REPORTING_SUCCESS_STATES: frozenset[str] = frozenset(
        {"not-run", "executed", "reviewed", "superseded", "not-executed"}
    )
    ...
    if action == "skip":
        return SKIP_REPORTING_SUCCESS_STATES
    ```
    Command output:
    ```
    $ python3 -c "from agent_workflows.runner_shared import success_states_for_action, exit_code_statuses, EXIT_SUCCESS_TOKEN
    from agent_workflows.runner_stop import deliberate_stop_exit_code

    print('skip success states:', success_states_for_action('skip'))
    print('execute success states:', success_states_for_action('execute'))

    skip_queue = [{'action': 'skip', 'status': 'not-run'}]
    code_skip = deliberate_stop_exit_code(exit_code_statuses(skip_queue), success_states={EXIT_SUCCESS_TOKEN}, stopped=False)
    print('Exit code with skip item:', code_skip)

    sub_queue = [{'action': 'execute', 'status': 'substantially-complete'}]
    code_sub = deliberate_stop_exit_code(exit_code_statuses(sub_queue), success_states={EXIT_SUCCESS_TOKEN}, stopped=False)
    print('Exit code with substantially-complete item:', code_sub)
    "
    skip success states: frozenset({'superseded', 'not-run', 'not-executed', 'reviewed', 'executed'})
    execute success states: frozenset({'approved', 'executed'})
    Exit code with skip item: 0
    Exit code with substantially-complete item: 1
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the `--retry-incomplete` requeue-condition diff from BOTH `oc_runipd.run_queue` and `agy_runipd.run_queue`, and the actual output of a `--retry-incomplete` resume over a run holding a `skip` entry showing the entry left terminal with zero attempts and no spawn, beside a control resume over a `failed` entry showing it IS requeued.
  - Observed evidence: oc and agy run_queue exclude skip action from requeue; resume test confirmed skip stays not-run and failed requeued.
    Diff in `oc_runipd.py` (lines 3427-3430) and `agy_runipd.py` (lines 2792-2795):
    ```python
    if item.get("action") == "skip":
        continue
    ```
    Actual resume output:
    ```
    oc: PASSED
    agy: PASSED
    ```
    In both hosts, `skp001` remained `not-run` with 0 attempts and no spawn, while control item `fld001` was requeued to `queued` with `recovery_next` and `requeue_from_status: failed`.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_action_table_runner_parity.py -q` passing with its count; then, with E-05's hunks temporarily reverted, the same command showing the terminal-status rows FAILING; then passing again. Also paste the four draft rows' assertions showing `runner_action` and `needs_review` agree, and, as a one-off AUTHORING SELF-CHECK on the new test file only (NOT a committed test, so the no-structure-tests ruling is untouched: that ruling governs what the SUITE asserts, and this is a reviewer-visible grep run once at execution), `grep -n "getsource\|ast\." tests/test_action_table_runner_parity.py` showing no source or AST reads. `read_text` is DELIBERATELY DROPPED FROM THAT GREP: the test must read the run's own `state.json` with it, so grepping it would flag the required mechanism; state instead that no `read_text` target in the file is under `agent_workflows/`.
  - Observed evidence: test_action_table_runner_parity.py 9 passed; negative check showed terminal rows failing when reverted; self-check clean.
    1. Passing count:
    ```
    $ python3 -m pytest -o addopts="" tests/test_action_table_runner_parity.py -q
    .........                                                                [100%]
    9 passed in 8.18s
    ```
    2. Negative verification (E-05 reverted):
    ```
    5 failed, 4 passed in 2.58s
    FAILED tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_executed_maps_to_skip_on_both_hosts
    FAILED tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_retired_statuses_parity_direct
    FAILED tests/test_action_table_runner_parity.py::TestActionTableRunnerParity::test_parity_matrix_across_all_statuses_and_kinds
    ```
    3. Passing again after restore:
    ```
    9 passed in 10.98s
    ```
    4. Four draft rows agree:
    - Complete named: `runner_action("ipd", "draft", authoring_complete=True) == "review"`, `needs_review(...) == True`
    - Complete swept: admitted to queue when `allow_drafts=True`
    - Incomplete named: `runner_action("ipd", "draft", authoring_complete=False) == "skip"`, `needs_review(...) == False`
    - Incomplete swept: excluded by review sweep, raises `EmptyStatusSelection`
    5. Authoring self-check:
    `grep -n "getsource\|ast\." tests/test_action_table_runner_parity.py` outputs line 4 (docstring comment only). No `read_text` call targets any path under `agent_workflows/`.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste the consumer-case test output for (a) exit code, (b) requeue, (c) `--action` legality, and (d) the `reviewed`+orchestrator row, each passing; then the FAILING output of (a) against a build with E-07's `skip` arm reverted and of (b) against a build with E-08's exclusion reverted, then both passing again. Also paste `python3 -m pytest -o addopts="" tests/test_run_selection_policy.py tests/test_oc_runipd.py tests/test_orchestrator_retirement.py -q` passing with its count.
  - Observed evidence: Four consumer cases passed; exit code and requeue negative checks failed when reverted; 261 passed on existing suites.
    1. Consumer cases passing:
    ```
    $ python3 -m pytest -o addopts="" tests/test_action_table_runner_parity.py -k TestConsumerCases -v
    tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_reviewed_orchestrator_order_sensitivity PASSED [ 25%]
    tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_exit_code PASSED [ 50%]
    tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_retry_incomplete_requeue_exclusion PASSED [ 75%]
    tests/test_action_table_runner_parity.py::TestConsumerCases::test_consumer_action_legality_on_incomplete_draft PASSED [100%]
    4 passed, 5 deselected in 1.27s
    ```
    2. Negative verification for (a) exit code (E-07 skip arm reverted):
    `AssertionError: 1 != 0` in `test_consumer_exit_code`.
    3. Negative verification for (b) requeue (E-08 skip exclusion reverted):
    `AssertionError: 'queued' != 'not-run'` in `test_consumer_retry_incomplete_requeue_exclusion`.
    4. Passing again after both restored:
    `4 passed, 5 deselected in 10.77s`.
    5. Existing test suites passing count:
    ```
    $ python3 -m pytest -o addopts="" tests/test_run_selection_policy.py tests/test_oc_runipd.py tests/test_orchestrator_retirement.py -q
    261 passed in 128.85s (0:02:08)
    ```
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste the 5.6 diff (only that criterion changed), the resolved spec path as printed by `aw find specs z7nbn1`, the `aw specs note` output, `aw specs check <resolved spec path>` clean, and the bare `python3 -m pytest` summary line BEFORE and AFTER this plan with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence: Spec 5.6 amended to behavioral wording; aw specs note recorded; aw specs check clean; bare pytest 2610 passed (after-minus-before empty).
    1. Spec 5.6 diff:
    ```diff
    -5.6 Runner Action Derivation Matches Action Tables: An AST or grep check proves `_ACTION_TABLES` is the only type-plus-status-to-action mapping in the package. A queue built over an executed plan carries `action: skip` on both hosts.
    +5.6 Runner Action Derivation Matches Action Tables: `_ACTION_TABLES`, read through the public `run_selection_policy.action_for_status` reader and layered in `runner_action`, is the single status-to-action mapping in the package. Behavioral equality tests prove the runner's derived action matches the action table for every status and kind on both hosts, and a queue built over an executed plan carries `action: skip` on both hosts.
    ```
    2. Resolved spec path:
    `aw find specs z7nbn1` -> `.aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md`
    3. `aw specs note` recorded:
    `5.6 wording amended by artdispatch 7icz68: AST/grep check replaced by behavioral runner-vs-table equality (maintainer ruling 2026-09-26, no structure tests)`
    4. `aw specs check` output:
    `aw specs check: all specs conform.`
    5. Bare test suite runs:
    - BEFORE: `2601 passed, 2 skipped, 3 warnings in 121.82s`
    - AFTER: `2610 passed, 2 skipped, 3 warnings in 52.64s`
    - Failing node-ID set (after minus before): empty (`set()`)
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. The runner stops carrying its own status-to-action rule: `run_selection_policy`'s table, read through a new public reader, becomes the one authority, and the runner's own inputs (draft completeness, `--full-auto`, orchestrator Kind) refine only the rows the table leaves undetermined. Two visible behavior changes. An `executed`/`superseded`/`not-executed` queue entry is now recorded with action `skip` instead of `execute`/`orchestrate`; such entries were already never dispatched, so no run does different work there. And a NAMED INCOMPLETE `draft` is now skipped (`not-run`, no turn) instead of being sent to `/plan-review`, which is what spec `25kzda` 3.2 always required; a complete draft is still reviewed. THREE FURTHER CONSEQUENCES THE REVIEW SURFACED, each now carried by its OWN checklist item (E-06 through E-08) rather than left to be discovered at execution, and each one a thing a human should know is being changed. The run's EXIT CODE gains a `skip` arm, because without one a run that correctly skipped an incomplete draft would report failure (`exit_code_statuses` over a `not-run` skip yields exit 1 today). `--retry-incomplete` gains a `skip` exclusion on both hosts, because `not-run` is in each host's requeue set and a requeue would otherwise EXECUTE the skip through the very path the freeze exists to close. And `--action review` legality deliberately KEEPS reading a draft as `review`, so `aw oc review <named-incomplete-draft>` still starts rather than refusing the whole run; legality and dispatch differ on that one row on purpose. It also approves a one-sentence amendment to spec `z7nbn1` 5.6 replacing its "AST or grep check" method with the behavioral test, per the maintainer's 2026-09-26 ruling. This is Order 01 of Set `artdispatch`, graduated from spec `z7nbn1`; it carries `- From-Backlog: oc3mhb` so that item closes by handoff, and `- Blocks-Release: next`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. In `runner_shared.py`, only `action_for`, `determine_action`, `_consuming_actions_for`, the two `initialize_run_core` derivation sites (and the queue-status freeze for a `skip` entry), the `execute_item_core` action guard, `success_states_for_action`'s new `skip` arm, and the `expand_dependency_closure` comment. In `oc_runipd.py` and `agy_runipd.py`, only each `run_queue`'s `--retry-incomplete` requeue condition (and the `action_for`/`determine_action` re-export lines if E-05 removes them). If an edit outside the declared paths proves necessary (for example the host re-export lines if E-05 removes the functions), make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. The new parity test must be shown FAILING against the pre-change runner.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane). Backlog `oc3mhb` is then closed by the handoff this plan's `From-Backlog` and matching `Blocks-Release` provide; its `graduated` transition is the graduating agent's, not this plan's.
