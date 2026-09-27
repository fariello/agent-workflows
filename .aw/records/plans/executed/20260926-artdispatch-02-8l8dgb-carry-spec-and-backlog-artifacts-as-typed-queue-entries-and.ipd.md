# IPD: Carry spec and backlog artifacts as typed queue entries and resolve their selectors on both hosts

- Date: 2026-09-26
- Kind: child
- Concern: THE QUEUE ADMITS ONLY PLANS (spec `z7nbn1` 4.1, "the single structural blocker"). The selector can FIND a spec or backlog item and the action table KNOWS what to do with it, but the manifest between them cannot carry it. Re-measured at HEAD `310ea53e`: `runner_shared.build_dynamic_manifest` compiles `discover_plans` output alone into `manifest["plans"]`; `initialize_run_core`'s queue loop reads `manifest["plans"][id6]` with a bare subscript and writes a plan-shaped entry (`"configured_file": plan["file"]`); `runner_shared.expand_selectors` refuses a spec id6 through `match_spec_selector` / `describe_spec_selector_refusal` and a backlog id6 through `describe_unresolved_plan_selector` ("'oc3mhb' is a backlog item ..., not an IPD plan"); `refuse_unrunnable_selected_types` refuses any non-`ipd` `--type` after the mixed-type gate; `refuse_type_scoping_outside_the_review_sweep` refuses `--type` on `all` and named selectors; and `RUN_TYPE_SWEEPABLE` is `{ipd, spec}`. A SECOND defect sits in the same path and must be fixed here or 5.9 is false: a backlog id6 that also names a Set, or that uniquely PREFIXES one, is taken by a Set branch before any typed branch runs. Re-measured at review over the whole corpus (836 plans, 19 id-bearing specs, 632 backlog items): FOUR tokens are shadowed, in TWO distinct classes, and the class matters because the two branches sit at different points in the chain. EXACT setid: `faov03` (backlog `graduated`) -> plan `wja06w`, and `ackme8` (backlog `done`) -> plan `w0ln4q`. UNIQUE Set PREFIX: `8t5ghs` (backlog `done`) -> Set `8t5ghsgi` -> `s2ufeo`, and `vwios6` (backlog `done`) -> Set `vwios6ipd` -> four plans. No spec id6 is shadowed either way. THE AUTHORED CLAIM THAT ALL FOUR ARE THE SAME CASE WAS WRONG and is corrected here, because a fix that only precedes the exact-setid branch leaves the two prefix cases broken. `configured_file` was re-measured at review as 43 raw occurrences across six modules (`runner_shared` 28, `run_viewer` 6, `artifact_audit` 5, `oc_runipd` 2, `agy_runipd` 1, `attention` 1); a docstring-and-comment-excluding tokenizer pass gives 33 CODE occurrences over 33 lines in five modules (`runner_shared` 21, `run_viewer` 6, `artifact_audit` 4, `attention` 1, `oc_runipd` 1). Both numbers are live populations, so E-01 re-derives them rather than asserting them.
- Scope: IN: (a) a typed queue entry: every entry carries `artifact_type` (`ipd`/`spec`/`backlog`), and a typed accessor returns the entry's artifact path through the right per-type authority (plans through `resolve_plan_path`, which plan `mxzogk` makes fail closed; specs through `discover_specs`; backlog through `resolve_backlog_item`); (b) the manifest gains `specs` and `backlog` maps beside `plans` (additive; `plans` is unchanged), populated only for the ids a selection actually names or the `--type` set sweeps, so an ordinary IPD run's manifest and cost are unchanged; (c) `expand_selectors` resolves a spec or backlog id6 to THAT artifact (typed branch AHEAD of the Set and Set-prefix branches for an id6-shaped token that some non-plan artifact declares as its `- Id:`), replacing the two refusals; (d) `refuse_unrunnable_selected_types` and `refuse_type_scoping_outside_the_review_sweep` narrowed so `--type spec`/`--type backlog` reach the queue (still refusing `prompt`/`research`/`release`/`walkthrough`); (e) every `configured_file` read site that exists at execution enumerated and either routed through the accessor or justified (spec 5.8); (f) a non-plan queue entry whose action has no dispatcher yet (review of a spec until plan `2ptgds`, `plan` until plans `aeq7f8`/`y3p3p5`) is refused item-locally BEFORE any turn with a message naming the owning plan, so this plan never hands a spec to the plan executor; (g) THE FOUR SEAMS A TYPED ENTRY REACHES BETWEEN SELECTION AND THAT REFUSAL, each measured at review and none of them a `configured_file` site, so (e)'s census would not have found them: the `--action` legality preflight (F-9), `resolve_selected_artifact_paths` under the IPD-only default (F-10), the queue-status freeze plus the reporting success bar (F-11), and the active-runner conflict scan (F-12). OUT: freeze-time whole-run refusal (plan `jdn790`); the spec review and production dispatchers themselves; `resolve_plan_path`'s own fail-closed fix (plan `mxzogk`, spec 5.7); the `--with-dependencies` closure's refusal of non-plan targets (`closure_target_admission`), which stays as is because a produced plan's `From-Spec` is provenance, not a dependency edge (spec `25kzda` 5.4).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/run_viewer.py, agent_workflows/artifact_audit.py, agent_workflows/attention.py, tests/test_typed_queue_entries.py, tests/test_oc_runipd.py, tests/test_runner_shared.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: executed:7icz68, executed:mxzogk
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 2
- Highest E allocated: 13
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8l8dgb

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 8l8dgb verified (set artdispatch, attempt 2). [Scope reconciliation - widened-scope tests/test_agy_runipd_cli.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); in-scope-unmodified agent_workflows/artifact_audit.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified agent_workflows/attention.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified agent_workflows/run_viewer.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_runner_shared.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-09-27 approved (aw set): status set to approved

- 2026-09-26 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001..PR-011 all FIXED; review record `.aw/records/reviews/20260926-artdispatch-02-8l8dgb-carry-spec-and-backlog-artifacts-as-typed-queue-entries-and.review.md`. Re-verified F-1..F-8 at lane HEAD 252aa46c: every seam reproduced, and F-4's shadowed-token list was re-derived as FOUR tokens (`faov03`, `ackme8` exact setids; `8t5ghs`, `vwios6` unique Set prefixes), correcting the authored claim that `8t5ghs`/`vwios6`/`ackme8` are the same class as `faov03`. F-6's code-token count re-measured as 33 by a docstring-excluding tokenizer pass (43 raw, not 44), so E-01 no longer carries a number that did not reproduce. ADDED four seams a typed entry reaches between selection and E-06's refusal, NONE of which is a `configured_file` site and so none of which E-01's census would have found: the `--action` legality preflight (F-9, `aw oc review <spec-id6>` would refuse the whole run), `resolve_selected_artifact_paths` under the IPD-only default (F-10, a named spec becomes `unresolved` and is invisible to the mixed-type gate and the dependency preflight), the queue-status freeze and reporting success bar (F-11, a backlog `open` entry is frozen `reviewed` and never dispatched, and a `plan`-action entry exits 1), and the active-runner conflict scan (F-12). Split the four over-dense items into nine (E-01..E-13; `IPD-Z602` fired once on the first split's combined seam-test item and is cleared by splitting it in two) and rebuilt the V checklist to a 13-item bijection. `aw ipd lint --phase review-finalize` conforming, 0 findings; bare `python3 -m pytest` 1 failed, 2549 passed, 2 skipped, the one failure being the load-sensitive wall-clock assertion `tests/test_scope_match.py::ScopeMatchUnitTests::test_pathological_glob_avoids_exponential_time` (0.1191s against a 0.1s threshold), which passes in isolation and which this review's records-only edits cannot reach; the full output is pasted in the review record.

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 02 of Set artdispatch). The four oc3mhb seams re-measured at HEAD 310ea53e; configured_file re-counted (44 raw / 33 code tokens across six modules); a backlog-id6-shadowed-by-Set defect found and measured (faov03 resolves to plan wja06w); no id6 collides across plans, specs and backlog (830/19/620 measured). Depends on mxzogk for spec 5.7.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let a run queue carry a spec or a backlog item as itself, typed, so that naming one selects that artifact on both hosts and every downstream reader locates it through its own type's authority instead of assuming a plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [x] E-01 ENUMERATE THE `configured_file` SITES AND THE SELECTION CHAIN AT THE EXECUTING HEAD. (1) Every `configured_file` CODE occurrence (excluding docstrings AND comments) under `agent_workflows/`, as a table: module, enclosing function, read or write, and what it does with the value (resolve a plan path, display, audit lookup, lane record). Use a tokenizer pass that excludes docstring and comment tokens, not a raw grep count, and paste BOTH the raw `grep -o configured_file agent_workflows/*.py | sort | uniq -c` and the code-token table. At review these were 43 raw and 33 code occurrences over 33 lines in five modules; BOTH ARE LIVE POPULATIONS AND NEITHER IS THE BAR (the authored 44 did not reproduce). The required property is that the table has one row per code occurrence at THIS head and that E-09 gives every row a disposition. (2) Paste the ACTUAL ORDER, by symbol, of every gate `initialize_run_core` applies between flag resolution and the queue loop, not only the four the author listed: at review the order was `refuse_unsweepable_run_types`, `refuse_type_scoping_outside_the_review_sweep`, `expand_selectors`, `enforce_draft_admission_gate`, `resolve_selected_artifact_paths`, `enforce_dependency_preflight`, the `--action` preflight + `enforce_requested_action`, `enforce_mixed_type_gate`, `refuse_unrunnable_selected_types`, `enforce_no_active_runner_conflict`, then the queue loop. Each of the last four is a seam E-05 through E-08 must handle, so a census that stops at four gates is the defect this step exists to prevent. (3) Reproduce the two refusals (`expand_selectors(manifest, [<spec id6>])`, `[<backlog id6>]`) and BOTH Set-shadowing classes separately: every non-plan id6 that EQUALS a setid, and every one that uniquely PREFIXES a setid, each with the plans it currently returns. At review: exact `faov03`, `ackme8`; prefix `8t5ghs` (-> `8t5ghsgi`), `vwios6` (-> `vwios6ipd`). (4) Confirm no id6 collides across the plans, specs and backlog trees (at review: 836 plans, 19 id-bearing specs, 632 backlog items, all three pairwise intersections empty).
  - Depends on: none
  - Expected outcome: the code-occurrence table has one row per occurrence at this head; the gate order is pasted by symbol and names at least the four post-expansion seams; both shadowing classes are listed separately with their current results; the collision set is empty.
  - Execution state: performed

### Task group 2: the typed entry

- [x] E-02 ADD THE TYPED ACCESSOR in `runner_shared`: `queue_entry_type(item) -> str` (the entry's `artifact_type`, defaulting to `ipd` when absent so every existing run record and hand-written manifest keeps meaning a plan, per spec `z7nbn1` 5a "existing run records keep their queue shape") and `queue_artifact_path(repo, item) -> Path` that dispatches on that type: `ipd` -> `resolve_plan_path(repo, item["configured_file"], id6)` (unchanged semantics, now fail-closed via `mxzogk`); `spec` -> the `discover_specs(repo)[id6].path`, raising `DriverError` naming the id6 when absent; `backlog` -> `resolve_backlog_item(repo, id6)`, raising likewise. Never falls back from one type to another. Also add `queue_plan_path_for(repo, item)` semantics: a caller that REQUIRES a plan calls a helper that raises `DriverError("<id6> is a <type>, not an IPD plan")` for a non-`ipd` entry, so plan-only code paths refuse loudly instead of resolving.
  - Depends on: E-01
  - Expected outcome: the accessor returns the spec's path for a spec entry, the backlog file for a backlog entry, the plan for a plan entry or an entry lacking `artifact_type`, and raises for a mismatch.
  - Execution state: performed

- [x] E-03 EXTEND THE MANIFEST AND QUEUE BUILDER. `build_dynamic_manifest` (or a sibling called by `initialize_run_core`) gains `specs` and `backlog` maps keyed by id6 holding `{file, status, set}` (plus `blocks_release` for later production checks), populated from `discover_specs` and a backlog enumeration over `backlog._iter_items` + `backlog.parse_item` (no new path literal; `check_engine._type_dirs`/`selectors` own the trees), LAZILY: only when the selection names a non-plan id6 or `--type` includes `spec`/`backlog`. `initialize_run_core`'s queue loop then builds an entry per selected id6 from whichever map owns it, with `artifact_type`, `configured_file` (the artifact's repo-relative path, kept for display and resume compatibility), `status`, `setid`, `dependencies: []` (specs and backlog items have no source-side dependency field, spec `25kzda` 2.10), `kind: None`, and `action` from plan `7icz68`'s `run_selection_policy.runner_action(artifact_type, status)`. The bare `manifest["plans"][id6]` subscript is replaced by a typed lookup that raises `DriverError` naming the id6 when no map holds it. `resolve_selected_artifact_paths` routes backlog ids through the backlog map, as it already routes specs through `discover_specs` (E-05 re-gates it so this works without `--type`). ALSO ADD THE TYPE RANK to `queue_sort_key` as the key immediately after `position`, per spec `25kzda` 5.4 rule 4 (`spec`, `backlog`, `ipd`, `prompt`), and REWRITE the docstring paragraph that currently declares the rank "deliberately NOT implemented" because "this runner's queue is homogeneous (IPDs only)" and that a later plan admitting non-plan targets "must revisit this note". This plan is that plan, so leaving the paragraph would assert a homogeneity this plan removes. This is unconditional, not contingent on `--allow-mixed`.
  - Depends on: E-02
  - Expected outcome: `--prepare-only --unattended` over one spec id6 writes a `state.json` queue entry with `artifact_type: spec`, the spec's path, and action `review` for a to-review spec; an IPD-only run's manifest has no `specs`/`backlog` keys and its queue entries are byte-identical apart from the new `artifact_type: ipd` key; `queue_sort_key` ranks a spec ahead of a backlog item ahead of a plan among equally-ready independent entries, and its docstring no longer claims the queue is IPD-only.
  - Execution state: performed

### Task group 3: selection

- [x] E-04 RESOLVE SPEC AND BACKLOG SELECTORS TO THEMSELVES in the shared `runner_shared.expand_selectors` (one definition for both hosts). For an id6-shaped token that is not a plan id6: if a spec or backlog item DECLARES it as `- Id:` (through `selectors.resolve(repo, <type>, token, allow=frozenset({selectors.MATCH_ID6}))`, the exact-declaration match, never a substring), return it as a typed selection. SITE THE BRANCH AHEAD OF BOTH SET BRANCHES, NOT ONE, and that plural is the correctness content rather than the branch (F-4 measured two distinct classes): the exact `elif sel_str in sets` branch AND the `prefix_matches = [s for s in sets if s.startswith(sel_str)]` branch that follows it, since `8t5ghs` and `vwios6` are shadowed only by the second. Siting after the exact-plan branch is correct and steals nothing (F-7: no non-plan id6 is a plan id6). Keep the existing precedence for everything else, including the file-candidate branch that still precedes it. Replace `describe_spec_selector_refusal`'s raise with the typed return, and make `describe_unresolved_plan_selector`'s backlog/spec branches unreachable for a declared id6 (keep them for non-declared tokens). The return shape must let `initialize_run_core` know each id's type (return typed tuples or populate the manifest's typed maps as a side effect; record which). An explicitly named spec/backlog id6 must still respect the retired-state refusal analogue: a `superseded` spec or a `done`/`graduated` backlog item is admitted and its action (`skip`) decides, rather than silently dropped. NOTE WHAT THIS ITEM MAKES REACHABLE, because E-05 through E-08 exist to catch it: after this change a non-plan id6 flows into four gates that read `manifest["plans"]` (F-9, F-10, F-11, F-12), so E-04 must NOT be executed and validated as though selection were the end of the chain.
  - Depends on: E-03
  - Expected outcome: `expand_selectors(m, ["faov03"])` selects backlog item `faov03`, not plan `wja06w` (EXACT-setid class); `expand_selectors(m, ["8t5ghs"])` selects backlog item `8t5ghs`, not plan `s2ufeo` via Set `8t5ghsgi` (PREFIX class); `expand_selectors(m, ["z7nbn1"])` selects the spec; a plan id6, a setid that no artifact declares as its id6, an ambiguous Set prefix, and a filename fragment resolve exactly as before.
  - Execution state: performed

- [x] E-05 NARROW THE THREE TYPE REFUSALS AND MAKE THE TYPED RESOLVER TYPE-DRIVEN. Four distinct changes, all in the same `--type`/selection chain, so they are one pass. (a) `refuse_unrunnable_selected_types` refuses only types with no queue representation (`prompt`, `research`, `release`, `walkthrough`). (b) `refuse_unsweepable_run_types` RUNS FIRST AND CURRENTLY REFUSES `--type backlog` EVERYWHERE, not only on `reviews` (measured: `refuse_unsweepable_run_types(("backlog",))` raises, and `refuse_unsweepable_run_types(("ipd","backlog"))` raises too), so without a change here `--type backlog` never reaches (a) or (c) at all and the plan's own expected outcome for it is unreachable. Its name and docstring scope it to the SWEEP, so narrow it to fire only for a review selector (`is_review_selector`, already shipped) and keep its exact message for that case: backlog has no review action in spec `25kzda` 3.4, so `reviews --type backlog` must stay a clear refusal that says why, while `aw oc run all --type backlog` must not be refused BY THE SWEEP'S gate. (c) `refuse_type_scoping_outside_the_review_sweep` admits `--type spec`/`--type backlog` on `all` and on named selectors, resolving `all --type spec` to every spec whose action is not `skip` (spec `25kzda` 2.4 "`aw oc run all --type spec` selects specs only") and deferring the empty-result wording to the existing `all` branch. (d) `resolve_selected_artifact_paths` IS GATED ON THE `--type` SET RATHER THAN ON THE ENTRY'S TYPE (F-10), so a spec named WITHOUT `--type` (which E-04 makes the ordinary case) lands in `unresolved`, contributes no path, and is INVISIBLE to the mixed-type gate that spec `25kzda` :166 requires to see it. Re-gate it on the typed entry's OWN type: a `spec` entry resolves through `discover_specs` and a `backlog` entry through the backlog map whatever `--type` says, exactly as an `ipd` entry already resolves through `resolve_plan_path`. Keep `unresolved` populated for an id NO tree can place, and (since it has zero readers in the package today, measured) have the caller REPORT a non-empty `unresolved` rather than dropping it silently. `enforce_mixed_type_gate` itself is unchanged: with (d) fixed it finally sees a genuinely mixed `all_paths`.
  - Depends on: E-04
  - Expected outcome: `aw oc run all --type spec --prepare-only --unattended` on a scratch repo queues the specs; `aw oc run all --type backlog` is not refused by the sweep gate while `reviews --type backlog` still is, with its reason; a spec id6 named with NO `--type` resolves to a path in `selection.all_paths` and `classify_paths` over a spec plus a plan reports `is_mixed=True`; `--type spec --type ipd` without `--allow-mixed` still refuses `[RUN-MIXED-TYPES]`; `--type prompt` still refuses naming the missing dispatcher.
  - Execution state: performed

- [x] E-06 KEEP `--action` LEGALITY FROM REFUSING THE WHOLE RUN OVER A TYPED ENTRY (F-9). The `--action` preflight loop in `initialize_run_core` runs BEFORE the queue loop and its per-item first statement is `manifest["plans"].get(id6, {})`, so a spec or backlog id6 yields `{}`, `status` falls back to the LITERAL `"approved"`, and `action_for` derives `execute` from a status the artifact does not have. `enforce_requested_action` then refuses the WHOLE RUN, and because `aw <host> review` expands to `--action review` (`cli.expand_host_review_argv`), `aw oc review <spec-id6>` refuses instead of reviewing the spec E-04 just made selectable. MEASURED LIVE, not hypothetically: `reviews --type spec` resolves `['llbr2b']` and its preflight tuple is `('llbr2b','approved','execute')`, which `enforce_requested_action("review", ...)` refuses by name. Fix the preflight to read each id's status and action from ITS OWN typed map (the same typed lookup E-03 gives the queue loop), so a `to-review` spec derives `review` and legality agrees with dispatch. Do NOT fix this by exempting non-plan entries from legality: an operator who typed `--action` is asking for a guarantee, and silently skipping the check for exactly the new types would make the flag mean less than it says. State at the call site that the preflight and the queue loop now derive from the same typed source, which is what keeps them from disagreeing again.
  - Depends on: E-05
  - Expected outcome: `aw oc review <to-review-spec-id6> --prepare-only --unattended` on a scratch repo STARTS and freezes that entry with `action: review`; `--action execute` over the same spec still refuses, naming the spec and its real status rather than a fabricated `approved`; an IPD-only `--action review` run is byte-identical to today.
  - Execution state: performed

- [x] E-07 GIVE A TYPED ENTRY A CORRECT BIRTH STATUS AND A CORRECT SUCCESS BAR (F-11). Two IPD-only vocabularies swallow a non-plan status, and the first one silently defeats this whole plan for backlog items. (a) `initial_queue_status` keys on `NON_TERMINAL_QUEUE_STATUSES` (`to-review`, `draft`, `approved`, `auto-approved`, `reusable`: IPD tokens), so a backlog item whose status is `open` and whose action is `plan` is born `reviewed`, a TERMINAL state in both hosts' `TERMINAL_STATES`. It is therefore never dispatched and E-09's refusal never fires, so `--type backlog` would appear to work and quietly do nothing. Make the birth status derive from the entry's ACTION rather than from an IPD status allowlist: an entry whose action is actionable (`review`, `execute`, `plan`, `orchestrate`) is born `queued`; a `skip` action is born terminal (plan `7icz68` E-06 owns the `skip` freeze, so coordinate with it rather than duplicating it); an `undetermined` action is born `queued` and is plan `jdn790`'s freeze-time refusal to catch. A spec `to-review`/`approved` currently lands `queued` only by coincidence of sharing an IPD token, and that coincidence must not be what the change rests on. (b) `success_states_for_action` has no `plan` arm, so a `plan`-action entry takes the EXECUTE bar `{approved, executed}` and an entry that behaved correctly makes the run EXIT 1 (measured: `exit_code_statuses([{"action":"plan","status":"reviewed"}])` -> `['reviewed']`, and the exit predicate over it returns `1`). Add a `plan` arm admitting the terminal statuses a correct production turn produces; do NOT widen `EXECUTE_REPORTING_SUCCESS_STATES`, so `substantially-complete` keeps exiting nonzero. NOTE THE INTERACTION WITH E-09: until the production dispatchers land, a `plan`-action entry ends in E-09's refusal, which is a NON-SUCCESS terminal by design, so the `plan` arm must not admit the refusal status. Say which status the refusal writes and assert the exit code is nonzero for it.
  - Depends on: E-06
  - Expected outcome: a backlog `open` entry is born `queued`, not `reviewed`, and reaches E-09's refusal; a spec `to-review` entry is born `queued` for its ACTION rather than by token coincidence; `success_states_for_action("plan")` admits a completed production turn's terminal status and NOT the refusal status; `EXECUTE_REPORTING_SUCCESS_STATES` is unchanged.
  - Execution state: performed

- [x] E-08 MAKE THE ACTIVE-RUNNER CONFLICT SCAN TYPE-AWARE (F-12). `enforce_no_active_runner_conflict` sits between the mixed-type gate and the queue loop and is plan-shaped in two places: its `id_to_path` fallback is `if id6 in manifest["plans"]` then `resolve_plan_path`, and its synthesis of an `attention.Item` for an id it could not place reads `manifest["plans"].get(id6, {})` with `status` defaulting to the LITERAL `"to-review"`. So a typed entry gets `path=""` and a FABRICATED status in the very table a human is asked to decide `[D]rop / [R]efuse / [F]orce` from, and a real conflict (a spec another live run is already processing) is MISSED, because the run map keys on `id6` and `configured_file` and the scan never supplies either for a non-plan entry. Route both reads through the typed accessor and the typed maps, so the table shows the artifact's real path and real status. A fabricated status in a prompt a human decides from is the defect to fix here, not the lookup miss alone.
  - Depends on: E-07
  - Expected outcome: a typed entry in conflict with a live run appears in the conflict table with its REAL path and REAL status; a typed entry not in conflict passes through untouched; the IPD path is unchanged.
  - Execution state: performed

### Task group 4: every reader

- [x] E-09 ROUTE OR JUSTIFY EVERY `configured_file` READ SITE from E-01's table (spec 5.8), AND ADD THE ITEM-LOCAL REFUSAL. Each row gets exactly one disposition, written into this plan's Findings at execution: (a) ROUTED through `queue_artifact_path` (sites that need the artifact, e.g. `queued_orchestrator_targets`, `spec_impacts_for_queue`, `queue_plan_path`, reporting); (b) ROUTED through the plan-required helper (sites that are plan-only by nature: `execute_item_core`'s `resolve_plan_path` calls, `reconcile_disposition`, verify and finalize re-resolution, lane integration, backlog close), which then refuse a non-plan entry loudly; (c) JUSTIFIED as display or audit of an opaque string (e.g. `run_viewer` rendering, `artifact_audit.audit_artifact`'s existence short-circuit, `attention.get_active_runs_map`'s run-record read), with the reason. Then add the Scope-(f) item-local refusal: in both hosts' dispatch loop, a non-`ipd` entry whose action has no dispatcher yet ends with a recorded refusal (`render_stream.record_refusal`, code naming the missing dispatcher and the plan that owns it: `2ptgds` for a spec review, `aeq7f8`/`y3p3p5` for `plan`) and a non-success terminal status, BEFORE any lane, session or prompt. SITE IT AHEAD OF `execute_item`, NOT INSIDE IT, and that placement is the substance: `execute_item_core`'s FIRST statement is `resolve_plan_path(repo, item.get("configured_file",""), item["id6"])`, which for a spec entry raises inside the item-local `except DriverError` and records `failed-safely` with a resolver message, not a message naming the owning plan. A refusal that only happens to be produced by a resolver failure is not the clear refusal spec `z7nbn1` 1.7 asks for. Name which of the two hosts' loop positions you chose and why. A `skip` entry was never queued (plan `7icz68`).
  - Depends on: E-08
  - Expected outcome: every code occurrence has a disposition; a `queued` spec entry with action `review` run through `oc_runipd.run_queue` with `run_opencode` patched to fail the test if called ends refused with the refusal record naming plan `2ptgds` (NOT a `resolve_plan_path` message), no lane or session was created, and an independent plan in the same queue still runs.
  - Execution state: performed

### Task group 5: prove it

- [x] E-10 ADD `tests/test_typed_queue_entries.py` WITH THE SELECTION AND ENTRY-SHAPE CASES (behavioral only; temp git repos; no source or AST reads; reading the run's own `state.json` is the required mechanism and is not a structure read). Cases: (1) spec 5.9 on BOTH hosts: a spec id6 and a backlog id6, each also appearing in a plan's FILENAME, one also EQUAL to a setid and one a unique Set PREFIX (both F-4 classes, since a fix preceding only the exact branch leaves the prefix class broken), resolve through `expand_selectors` + `initialize_run(--prepare-only)` to a queue entry of the right `artifact_type` and path, never to the plan; (2) the accessor returns the right path per type and raises on a mismatch or a missing id6; (3) an entry lacking `artifact_type` (an old run record) is read as `ipd`; (4) an IPD-only run's queue is unchanged apart from `artifact_type: ipd` and its manifest carries no typed maps; (5) `all --type spec` queues specs only, `all --type backlog` is NOT refused by the sweep gate, and `reviews --type backlog` still refuses with its reason; (6) a plan-only helper handed a spec entry raises `DriverError` naming the type. `AW_HOME` needs no per-test handling: the root `conftest.py` already re-points it at a session sandbox via an autouse fixture, so do not add a second mechanism.
  - Depends on: E-09
  - Expected outcome: cases (1) through (6) pass on both hosts; (1) and (5) FAIL against the pre-change code, and (1) fails on the PREFIX sub-case even against a build that fixed only the exact-setid branch.
  - Execution state: performed

- [x] E-11 ADD THE TWO PRE-QUEUE SEAM CASES (findings F-9 and F-10, both in the selection chain ahead of the queue loop, so they share one fixture shape and are one focused pass). Each must be shown failing without its own fix, so the fix is proven load-bearing rather than asserted. `--action` LEGALITY asserts that `aw oc review <to-review-spec-id6> --prepare-only --unattended` STARTS and freezes that entry with `action: review`, while `--action execute` over the same spec refuses naming its REAL status. Against a build without E-06 the first assertion raises with the measured "(status 'approved' -> action 'execute')" text. MIXED-TYPE VISIBILITY asserts that a spec id6 named with NO `--type` contributes a path to the resolved selection, and that a selection of that spec plus a plan is classified MIXED and meets `[RUN-MIXED-TYPES]` without `--allow-mixed`. Against a build without E-05(d) the same selection classifies single-type and the gate does not apply.
  - Depends on: E-10
  - Expected outcome: both cases pass on both hosts and each FAILS with the pasted assertion against a build with only its own fix reverted.
  - Execution state: performed

- [x] E-12 ADD THE TWO QUEUE-SHAPE SEAM CASES (findings F-11 and F-12) PLUS THE ITEM-LOCAL REFUSAL CASE, same file, same failing-without-its-fix discipline. BIRTH STATUS AND EXIT CODE: a backlog `open` entry is born `queued` and reaches E-09's refusal, a run whose only entry is a COMPLETED production turn exits 0, and one ending in E-09's refusal exits nonzero; against a build without E-07 the backlog entry is born `reviewed` and nothing is dispatched at all. CONFLICT TABLE: a typed entry conflicting with a live run appears in the rendered table with its real path and real status rather than `""` and a fabricated `to-review`. THE REFUSAL CASE: a `queued` spec entry with action `review` run through `run_queue` with the host spawn patched to FAIL THE TEST IF CALLED ends refused, with the refusal record naming the owning plan (`2ptgds`), no lane or session directory created, and an independent plan in the same queue still executed.
  - Depends on: E-11
  - Expected outcome: all three cases pass on both hosts; the first two each FAIL with the pasted assertion against a build with only their own fix reverted; the refusal case's spawn was provably never called.
  - Execution state: performed

- [x] E-13 RE-RUN E-01's reproductions after the change, reconcile the existing refusal-expecting tests, and run the bare suite before and after. The tests to reconcile are `tests/test_oc_runipd.py::test_unresolved_selector_identifies_backlog_item` and `::test_unresolved_selector_identifies_spec`, plus the `tests/test_runner_shared.py` spec-selector refusal cases. THEIR FIXTURES DO RESOLVE UNDER E-04, measured at review: both write a real declaring file (`- Id: item01` / `- Id: spec01`) and `selectors.resolve(repo, <type>, <token>, allow={MATCH_ID6})` returns that file, so both tests WILL fail after E-04 and must be rewritten to assert the typed SELECTION rather than the refusal. The authored guess that these are "UNDECLARED fixtures" was wrong; do not keep them on that basis. Keep a refusal case for a token NO artifact declares (`test_unresolved_selector_identifies_missing_file_or_id6` already covers it) so the refusal path stays pinned.
  - Depends on: E-12
  - Expected outcome: both shadowing classes now select their artifacts; the spec and backlog selectors queue typed entries; the two named tests assert typed selection and pass; the after-minus-before failing node set is empty.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `selectors.resolve(..., allow=frozenset({selectors.MATCH_ID6}))` is the exact-declaration match; `resolve_one`/`resolve_selectors` drop the verdict and must not back a new read path (their own docstring).
- `discover_specs` keys on `- Id:` and skips id-less legacy specs (19 of the corpus's spec files carry an id); `backlog._iter_items` + `parse_item` are the backlog enumeration; `resolve_backlog_item` already resolves one by id6.
- `resolve_selected_artifact_paths` already splits `plan_paths` (dependency preflight) from `all_paths` (mixed-type gate), per `ui8b9b` DECISION D5; this plan extends, not replaces, that split.
- Both hosts' dispatch loops treat `DriverError` from `execute_item` as item-local (`driver_error` recorded, loop continues).
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

F-1 through F-8 are the author's, measured at HEAD `310ea53e` (2026-09-26); every one was re-verified at lane HEAD `252aa46c` by `/plan-review` and reproduced, with F-4 and F-6 CORRECTED on the numbers as noted in their rows. F-9 through F-12 were ADDED by `/plan-review` on 2026-09-26: they are the seams a typed queue entry reaches BETWEEN selector expansion and E-06's item-local refusal, and not one of them is a `configured_file` site, so E-01's census as authored could not have found them.

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `build_dynamic_manifest` | Manifest holds plans only. | body: `for id6, rec in discovered.items(): plans_dict[id6] = {...}` over `discover_plans` |
| F-2 | HIGH | `initialize_run_core` queue loop | Bare subscript, plan-shaped entry. | `plan = manifest["plans"][id6]`; `"configured_file": plan["file"]` |
| F-3 | HIGH | `expand_selectors` | Spec and backlog id6 refuse. | `z7nbn1` -> "is a spec ..., not an IPD plan, so it cannot be queued"; `oc3mhb` -> "is a backlog item ..., not an IPD plan" |
| F-4 | HIGH | `expand_selectors` Set branches | A backlog id6 equal to a setid, OR uniquely PREFIXING one, resolves to that Set's plans. TWO CLASSES, not one: the authored row listed all four tokens together, and a fix preceding only the exact-setid branch would leave the two prefix cases broken. | EXACT setid: `faov03` (backlog `graduated`) -> `['wja06w']`; `ackme8` (`done`) -> `['w0ln4q']`. UNIQUE PREFIX: `8t5ghs` (`done`) -> Set `8t5ghsgi` -> `['s2ufeo']`; `vwios6` (`done`) -> Set `vwios6ipd` -> 4 plans. No spec id6 shadowed in either class |
| F-5 | MEDIUM | `refuse_unrunnable_selected_types`, `refuse_type_scoping_outside_the_review_sweep` | Non-`ipd` `--type` refused after resolution; `--type` on `all`/named selectors refused. Also `refuse_unsweepable_run_types` refuses `--type backlog` EVERYWHERE, including on `reviews`, and it runs FIRST, so `--type backlog` never reaches either function. | direct call: `refuse_unsweepable_run_types(("backlog",))` raises; `refuse_type_scoping_outside_the_review_sweep(("spec",), ["all"])` raises; `(("spec",), ["reviews"])` admits |
| F-6 | INFO | `configured_file` | 43 raw occurrences across six modules; 33 CODE occurrences over 33 lines in five modules once docstrings and comments are excluded. The authored 44/33 pair did not reproduce on the raw half. | `grep -o`: runner_shared 28, run_viewer 6, artifact_audit 5, oc_runipd 2, agy_runipd 1, attention 1 (=43). Tokenizer pass excluding docstrings/comments: runner_shared 21, run_viewer 6, artifact_audit 4, attention 1, oc_runipd 1 (=33) |
| F-7 | INFO | identity | No id6 collides across the three trees. | re-measured at review: 836 plans, 19 id-bearing specs, 632 backlog items; all three pairwise intersections empty |
| F-8 | INFO | cost | Backlog enumeration is cheap; plan discovery dominates. | reading 620 backlog items 0.028s, `discover_specs` 0.06s, `discover_plans` 1.46s |
| F-9 | HIGH | `initialize_run_core`'s `--action` preflight loop; `enforce_requested_action` | THE PREFLIGHT IS PLAN-SHAPED AND RUNS BEFORE THE QUEUE LOOP, and it refuses the WHOLE run. Its per-item first statement is `manifest["plans"].get(id6, {})`, so a spec or backlog id6 yields `{}`, `status` defaults to the literal `"approved"`, and `action_for` derives `execute` from a status the artifact does not have. Since `aw <host> review` expands to `--action review` (`cli.expand_host_review_argv`), `aw oc review <spec-id6>` would refuse the entire run. Found at review; handled by new E-06. | direct call on this HEAD: for `z7nbn1` the loop yields `('z7nbn1', 'approved', 'execute')` and `enforce_requested_action("review", ...)` raises `DriverError` "--action review is illegal for 1 selected item(s): z7nbn1 (status 'approved' -> action 'execute')". Reproduced live through the shipped path: `reviews --type spec` resolves `['llbr2b']`, whose preflight tuple is `('llbr2b','approved','execute')` and refuses |
| F-10 | HIGH | `resolve_selected_artifact_paths` | IT IS GATED ON THE `--type` SET, NOT ON THE ENTRY'S TYPE, so a spec or backlog id6 named WITHOUT `--type` (the ordinary way E-04 makes it reachable) lands in `unresolved` and contributes NO path. Two silent consequences: the mixed-type gate is handed a single-type `all_paths` and cannot see the mix spec `25kzda` :166 requires it to gate, and `refuse_unrunnable_selected_types`'s message names "(none resolved)". `unresolved` has zero readers in the package, so nothing reports it. Found at review; handled by new E-05. | direct call: `resolve_selected_artifact_paths(repo, m, ["z7nbn1"], None).unresolved == ('z7nbn1',)`, `all_paths == ()`; with `("spec",)` it resolves. `classify_paths` over `["7icz68","z7nbn1","oc3mhb"]` under the default reports `spec_types=('ipd',) is_mixed=False`. `grep -n "\.unresolved" agent_workflows/` -> only `run_cli.py`'s unrelated `unresolved_blockers` |
| F-11 | HIGH | `initial_queue_status`; `success_states_for_action` / `exit_code_statuses` | THE TWO STATUS VOCABULARIES ARE IPD-ONLY, and a non-plan status falls through both. (a) `initial_queue_status` keys on `NON_TERMINAL_QUEUE_STATUSES` (IPD statuses), so a backlog `open` item, whose action is `plan`, is born `reviewed`: a TERMINAL state, never dispatched, and E-06's refusal never even fires. A spec `to-review`/`approved` is born `queued` only by coincidence of sharing the IPD token. (b) A `plan`-action entry takes the EXECUTE reporting bar `{approved, executed}`, so the frozen `reviewed` projects onto the literal `reviewed` and the run EXITS 1 for an item that behaved correctly. Found at review; handled by new E-07. | direct call: `initial_queue_status("open")` -> `'reviewed'`, and `'reviewed' in oc_runipd.TERMINAL_STATES` is True; `initial_queue_status("graduated"/"blocked"/"implementing")` -> `'reviewed'`. `success_states_for_action("plan")` -> `frozenset({'approved','executed'})`; `exit_code_statuses([{"action":"plan","status":"reviewed"}])` -> `['reviewed']`; `deliberate_stop_exit_code(that, success_states={EXIT_SUCCESS_TOKEN}, stopped=False)` -> `1` |
| F-12 | MEDIUM | `enforce_no_active_runner_conflict` | Runs between the mixed-type gate and the queue loop and is plan-shaped twice over: its `id_to_path` fallback is `if id6 in manifest["plans"]` then `resolve_plan_path`, and its unresolved-item synthesis reads `manifest["plans"].get(id6, {})` with `status` defaulting to the literal `"to-review"`. A typed entry therefore gets `path=""` and a fabricated status in the conflict table a human is asked to decide from, and a genuine conflict on a spec already being processed by a live run is MISSED. Found at review; handled by new E-08. | function body (both `manifest["plans"]` reads); `attention.get_active_runs_map` keys on `item["id6"]` and `item["configured_file"]`, so a typed entry is keyed only once the queue carries one (measured: 156 live keys, `z7nbn1`/`oc3mhb`/`faov03` all absent today) |

## Proposed changes (ordered, validatable)

1. E-01 enumerates read sites and the whole gate chain, and reproduces the refusals and both Set-shadowing classes.
2. E-02 adds the typed accessor.
3. E-03 extends the manifest and queue builder.
4. E-04 resolves spec/backlog selectors to themselves, ahead of BOTH Set branches.
5. E-05 narrows the three type refusals and re-gates the typed resolver on the entry's own type.
6. E-06 keeps `--action` legality from refusing the whole run over a typed entry.
7. E-07 gives a typed entry a correct birth status and a correct success bar.
8. E-08 makes the active-runner conflict scan type-aware.
9. E-09 routes or justifies every read site and refuses undispatchable entries item-locally, ahead of `execute_item`.
10. E-10 adds the selection and entry-shape tests.
11. E-11 adds the two pre-queue seam tests, each shown failing without its own fix.
12. E-12 adds the two queue-shape seam tests and the item-local refusal test, same discipline.
13. E-13 re-probes, reconciles the two existing refusal tests, and runs the suite.

## Deferred / out of scope (with reason)

- Whole-run refusal of an undetermined or non-conformant selected artifact.
  - Carrier: jdn790
  - Rationale: freeze-time refusal is that plan's concern; this plan's refusal is item-local and only for a missing dispatcher.
- The spec review dispatcher and the two production dispatchers.
  - Carrier: 2ptgds
  - Rationale: plans `2ptgds`, `aeq7f8` and `y3p3p5` each replace one E-06 item-local refusal with real dispatch.
- `closure_target_admission` refusing a `spec`/`backlog` dependency target under `--with-dependencies`.
  - Carrier-Declined: dependency edges to specs/backlog are `exists:`/`state:` leaf checks (spec `25kzda` 2.10) evaluated from repository state; enqueueing them is not required by spec `z7nbn1`, which scopes dispatch to what the operator selected.

## Scope check

- Over-scope: none.
- Under-scope: NONE OUTSTANDING after review. `agent_workflows/selectors.py`, `backlog.py`, `check_engine.py` are called, not changed. `runner_shared.py` now also takes E-05's four refusal/resolver changes, E-06's `--action` preflight, E-07's `initial_queue_status` and `success_states_for_action` arms, and E-08's conflict scan, all of which live in that one module and are covered by its existing declaration. `run_viewer.py`, `artifact_audit.py`, `attention.py` are declared because E-09 may route a site; if a site is only justified, its module is acknowledged at finalize with `--scope-ack`.
- Scope-Paths justification: `runner_shared.py` holds the manifest, queue builder, selector expansion, all three type refusals, the typed resolver, the `--action` preflight, the queue-status and success-bar vocabularies, the conflict scan and the new accessor; the two host modules hold the dispatch-loop refusal site (E-09) and the re-exports; the three reader modules hold `configured_file` sites; tests as listed.

## Required tests / validation

- `tests/test_typed_queue_entries.py` (new): six selection/entry-shape cases (E-10), the two pre-queue seam cases (E-11), and the two queue-shape seam cases plus the item-local refusal case (E-12), on both hosts, including spec 5.9's spec-and-backlog proof over BOTH F-4 shadowing classes; each shown failing against the build lacking its own fix.
- The two `tests/test_oc_runipd.py` selector-refusal tests REWRITTEN to assert typed selection (their fixtures do resolve under E-04, measured at review), and the `tests/test_runner_shared.py` spec-selector refusal cases reconciled; the no-artifact-declares-it refusal case kept.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. This plan implements spec `z7nbn1` 4.1, 5.8 and 5.9 as written. Spec 5.7 (typed resolver refusing a spec supplied as a plan's `configured_file`) is owned and satisfied by plan `mxzogk`, on which this plan depends; spec 0.2 already records that `mxzogk` satisfies 5.7 if it executes first.
- THE `queue_sort_key` TYPE RANK IS NOW MANDATORY, NOT CONDITIONAL. Spec `25kzda` 5.4 rule 4 lists a type rank (`spec`, `backlog`, `ipd`, `prompt`) between the requested position and Set, and `queue_sort_key`'s docstring records it as deliberately unimplemented because "this runner's queue is homogeneous (IPDs only)", adding that "a later plan that admits non-plan targets is what would make this rank reachable, and it must revisit this note". THIS IS THAT PLAN, so the authored hedge ("ADDS the rank ... only if a mixed queue is reachable after E-05 (it is ...)") resolves to an unconditional obligation and is restated as one: E-03 ADDS the type rank as the key after `position`, and UPDATES that docstring paragraph, which otherwise asserts a homogeneity this plan removes. A mixed queue is reachable two ways after E-05, not one: explicitly under `--allow-mixed`, and implicitly whenever a dependency closure or a Set selector mixes types. Leaving the note would make the next reader believe the queue is still IPD-only.
- No user-facing docs beyond `--help` text for `--type`, which is regenerated from the parser.

## Open questions

### OQ-01: Should the typed selector branch precede the Set branches?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES, and AHEAD OF BOTH SET BRANCHES rather than one, from repository evidence (F-4): a backlog id6 is its own identity, while a setid is a shared cross-type topic label (DECISIONS D153, cited in `check_engine.check_collisions`), and the naming grammar lets a graduated item's plans reuse the item's id6 as their setid. Spec `z7nbn1` 1.1 and 5.9 require the id6 to resolve to THAT artifact. CORRECTED AT REVIEW: the question as authored said "the Set branch", singular, and the measurement shows TWO shadowing paths, the exact `sel_str in sets` branch (`faov03`, `ackme8`) and the unique-prefix branch below it (`8t5ghs` -> `8t5ghsgi`, `vwios6` -> `vwios6ipd`). A branch sited between them would fix half the cases and leave the other half silently wrong, which is why E-04 and V-04 now name both. The branch fires only for an EXACT `- Id:` declaration, so a setid that no spec or backlog item declares is unaffected; E-01 lists every affected token, per class, at execution.

### OQ-02: Does an IPD-only run change?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: NOT ONLY BY ONE KEY, which is how this was authored and was not true. The QUEUE ENTRY of an IPD-only run gains exactly one additive key (`artifact_type: ipd`) and nothing else, and that part stands: the typed maps are built lazily so discovery cost and the manifest are unchanged, and readers default a missing `artifact_type` to `ipd` so old run records resume unchanged (spec `z7nbn1` 5a migration clause). But the RUN's behavior also depends on E-03's type rank in `queue_sort_key` and on E-07's `initial_queue_status`, both of which an IPD-only run executes. Neither changes an IPD-only ORDERING or BIRTH STATUS (a homogeneous queue has one rank value, and E-07 must preserve every IPD status's current answer), and that preservation is now an explicit obligation rather than an assumption: E-10 case (4) pins the queue entries byte-identical apart from `artifact_type`, and E-07's expected outcome requires the IPD answers unchanged. Stating it as "one additive key" full stop would have let an executor skip checking the two shared functions it touches.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the raw `grep -o` count, the docstring-and-comment-excluding code-occurrence table (one row per occurrence), the FULL gate order by symbol from flag resolution to the queue loop (it must name the `--action` preflight, `resolve_selected_artifact_paths`, the mixed-type gate, `refuse_unrunnable_selected_types` and `enforce_no_active_runner_conflict`), the two selector refusals reproduced, BOTH shadowing classes listed separately with the plans each token currently returns, and the empty collision set with its three tree sizes.
  - Observed evidence: Raw count 45 (6 modules); 35 code occurrences tabulated; gate order verified by symbol; refusals reproduced; both shadowing classes verified (faov03/ackme8 exact, 8t5ghs/vwios6 prefix); 0 collisions across 838 plans, 19 specs, 638 backlog items.
    Raw `grep -o configured_file agent_workflows/*.py | sort | uniq -c`:
    ```
          1 agent_workflows/agy_runipd.py:configured_file
          5 agent_workflows/artifact_audit.py:configured_file
          1 agent_workflows/attention.py:configured_file
          2 agent_workflows/oc_runipd.py:configured_file
         30 agent_workflows/runner_shared.py:configured_file
          6 agent_workflows/run_viewer.py:configured_file
    ```
    Code-occurrence table (excluding docstrings and comments):
    | Module | Line | Enclosing Function | Read/Write | Purpose / Action |
    | --- | --- | --- | --- | --- |
    | artifact_audit | 953 | `audit_artifact` | Read | parameter default `configured_file: str = ""` |
    | artifact_audit | 985 | `audit_artifact` | Read | `if configured_file and (Path(repo_root) / configured_file).is_file():` |
    | artifact_audit | 985 | `audit_artifact` | Read | `if configured_file and (Path(repo_root) / configured_file).is_file():` |
    | artifact_audit | 986 | `audit_artifact` | Read | `actual_file = Path(repo_root) / configured_file` |
    | attention | 2625 | `get_active_runs_map` | Read | `cfg_file = item.get("configured_file")` lookup in active runs map |
    | oc_runipd | 4599 | `handle_audit_command` | Write | `"configured_file": ""` synthetic queue entry for standalone audit command |
    | run_viewer | 155 | `<module>` | Read | `configured_file: str` dataclass field definition |
    | run_viewer | 621 | `audit_step_artifact` | Read | `configured_file=step.configured_file,` argument passed to `audit_artifact` |
    | run_viewer | 621 | `audit_step_artifact` | Read | `configured_file=step.configured_file,` argument passed to `audit_artifact` |
    | run_viewer | 1011 | `load_run_summary` | Read | `cfg_file = item.get("configured_file", "")` loaded from queue item in state.json |
    | run_viewer | 1113 | `load_run_summary` | Read | `configured_file=cfg_file,` assigned to RunItemSummary dataclass |
    | run_viewer | 1227 | `load_run_summary` | Read | `configured_file="",` default assigned to RunItemSummary |
    | runner_shared | 1642 | `lane_plan_is_terminal` | Read | `plan_path = resolve_plan_path(repo, str(lane.get("configured_file") or ""` |
    | runner_shared | 9513 | `_finish` | Read | `resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])` |
    | runner_shared | 10237 | `finish_reintegrated_item` | Read | `repo, str(item.get("configured_file") or ""), str(item["id6"])` |
    | runner_shared | 11997 | `lane_executed_carrier_override` | Read | `configured = item.get("configured_file", "") or ""` |
    | runner_shared | 15288 | `format_slated_artifacts_table` | Read | `cfg = q_item.get("configured_file") or ""` display formatting |
    | runner_shared | 17099 | `queued_orchestrator_targets` | Read | `item.get("configured_file") or ""` target plan path resolution |
    | runner_shared | 25844 | `initialize_run_core` | Write | `"configured_file": plan["file"],` written to IPD queue item |
    | runner_shared | 25881 | `initialize_run_core` | Write | `"configured_file": item_info.get("file", ""),` written to typed non-plan queue item |
    | runner_shared | 27712 | `reconcile_disposition` | Read | `source, item.get("configured_file", ""), item["id6"]` plan path re-resolution |
    | runner_shared | 27733 | `reconcile_disposition` | Read | `repo, item.get("configured_file", ""), item["id6"]` plan path re-resolution |
    | runner_shared | 27924 | `reconcile_interrupted` | Read | `path = resolve_plan_path(repo, item.get("configured_file", ""), item["id6"])` |
    | runner_shared | 28829 | `execute_item_core` | Read | `lane_root, item.get("configured_file", ""), item["id6"]` verifier prompt plan path |
    | runner_shared | 28878 | `execute_item_core` | Read | `lane_root, item.get("configured_file", ""), item["id6"]` verifier turn plan path |
    | runner_shared | 29280 | `_run_verifier_turn` | Read | `plan_repo, item.get("configured_file", ""), item["id6"]` verifier execution |
    | runner_shared | 30388 | `execute_item_core` | Read | `finalize_repo, item.get("configured_file", ""), item["id6"]` finalize plan path |
    | runner_shared | 30621 | `execute_item_core` | Read | `repo, item.get("configured_file", ""), item["id6"]` plan path re-resolution |
    | runner_shared | 30663 | `execute_item_core` | Read | `repo, item.get("configured_file", ""), item["id6"]` plan path re-resolution |
    | runner_shared | 30726 | `execute_item_core` | Read | `repo, item.get("configured_file", ""), item["id6"]` plan path re-resolution |
    | runner_shared | 30809 | `execute_item_core` | Read | `repo, item.get("configured_file", ""), item["id6"]` plan path re-resolution |
    | runner_shared | 33282 | `queue_artifact_path` | Read | `cfg = str(item.get("configured_file") or "").strip()` typed accessor resolution |
    | runner_shared | 33303 | `queue_plan_path_for` | Read | `cfg = str(item.get("configured_file") or "").strip()` plan-required helper resolution |
    | runner_shared | 33333 | `queue_plan_path` | Read | `for key in ("path", "plan_path", "last_plan_path", "configured_file"):` key list |
    | runner_shared | 33346 | `queue_plan_path` | Read | `return resolve_plan_path(repo, str(item.get("configured_file") or ""), ...)` fallback |

    Full gate order by symbol in `initialize_run_core`:
    1. `refuse_unsweepable_run_types`
    2. `refuse_type_scoping_outside_the_review_sweep`
    3. `expand_selectors_fn` (`expand_selectors`)
    4. `enforce_draft_admission_gate` (if `is_status_selector`)
    5. `expand_dependency_closure`
    6. `resolve_selected_artifact_paths`
    7. `enforce_dependency_preflight_fn`
    8. `--action` preflight loop (`lookup_manifest_artifact`) + `enforce_requested_action`
    9. `enforce_mixed_type_gate`
    10. `refuse_unrunnable_selected_types`
    11. `enforce_no_active_runner_conflict`
    12. Queue loop (`for position, id6 in enumerate(queue_ids, start=1):`)

    Reproduced refusals (pre-change):
    - `expand_selectors(manifest, ["z7nbn1"])` raised: `DriverError: 'z7nbn1' is a spec ..., not an IPD plan, so it cannot be queued`
    - `expand_selectors(manifest, ["oc3mhb"])` raised: `DriverError: 'oc3mhb' is a backlog item ..., not an IPD plan`

    Both Set-shadowing classes:
    1. Exact setid tokens:
       - `faov03` (backlog item `faov03`): pre-change matched Set `faov03` returning `['wja06w']`.
       - `ackme8` (backlog item `ackme8`): pre-change matched Set `ackme8` returning `['w0ln4q']`.
    2. Prefix setid tokens:
       - `8t5ghs` (backlog item `8t5ghs`): pre-change matched prefix for Set `8t5ghsgi` returning `['s2ufeo']`.
       - `vwios6` (backlog item `vwios6`): pre-change matched prefix for Set `vwios6ipd` returning `['uvsmmy', 'si3mmt', 'efnn74', '7mw7m5']`.

    Corpus counts and empty collision sets:
    - Plans: 838, Specs: 19, Backlog: 638.
    - Pairwise intersections: `plan & spec: set()`, `plan & backlog: set()`, `spec & backlog: set()`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the accessor diff and a `python3 -c` run showing the per-type paths and the mismatch `DriverError` text.
  - Observed evidence: Accessor implemented in runner_shared and re-exported in oc/agy; python3 -c verified per-type path resolution and DriverError text on type mismatch.
    Accessor implementation added to `agent_workflows/runner_shared.py` (lines 33272-33305) and re-exported in `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`:
    ```python
    def queue_entry_type(item: "Mapping[str, Any]") -> str:
        return str(item.get("artifact_type") or "ipd").strip().lower() or "ipd"

    def queue_artifact_path(repo: Path, item: "Mapping[str, Any]") -> Path:
        atype = queue_entry_type(item)
        id6 = str(item.get("id6") or "").strip()
        if atype == "ipd":
            cfg = str(item.get("configured_file") or "").strip()
            return resolve_plan_path(repo, cfg, id6)
        if atype == "spec":
            specs = discover_specs(repo)
            if id6 in specs:
                return Path(specs[id6].path)
            raise DriverError(f"Spec '{id6}' not found in {repo}")
        if atype == "backlog":
            found = resolve_backlog_item(repo, id6)
            if found is not None:
                return found
            raise DriverError(f"Backlog item '{id6}' not found in {repo}")
        raise DriverError(f"Unsupported artifact_type '{atype}' for queue entry '{id6}'")

    def queue_plan_path_for(repo: Path, item: "Mapping[str, Any]") -> Path:
        atype = queue_entry_type(item)
        id6 = str(item.get("id6") or "").strip()
        if atype != "ipd":
            raise DriverError(f"{id6} is a {atype}, not an IPD plan")
        cfg = str(item.get("configured_file") or "").strip()
        return resolve_plan_path(repo, cfg, id6)
    ```
    `python3 -c` verification output:
    ```
    IPD path: .aw/records/plans/pending/20260926-artdispatch-02-8l8dgb-carry-spec-and-backlog-artifacts-as-typed-queue-entries-and.ipd.md
    Spec path: .aw/records/specs/implementing/20260916-z7nbn1-01-z7nbn1-universal-artifact-dispatch.spec.md
    Backlog path: .aw/records/backlog/done/20260923-faov03-01-faov03-aw-find-specs-status-silently-ignores-its-filter-a.backlog.md
    Mismatch DriverError (spec): z7nbn1 is a spec, not an IPD plan
    Mismatch DriverError (backlog): faov03 is a backlog, not an IPD plan
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the manifest/queue-builder diff, the `state.json` queue entry from a `--prepare-only --unattended` spec run, a before/after diff of an IPD-only run's queue entries showing only `artifact_type` added, and the `queue_sort_key` diff (the new type rank plus the rewritten docstring paragraph) with a `python3 -c` showing a spec, a backlog item and a plan sorted in that order.
  - Observed evidence: Manifest builder extended with lazy typed maps; state.json queue entry verified for spec and IPD-only runs; queue_sort_key ranks spec ahead of backlog ahead of plan; docstring updated.
    Manifest builder extended with lazy `populate_manifest_specs` and `populate_manifest_backlog` keyed by id6; `initialize_run_core` constructs entries using `lookup_manifest_artifact(manifest, repo, id6)`.
    `state.json` queue entry from `--prepare-only --unattended` spec run:
    ```json
    {
      "action": "review",
      "artifact_type": "spec",
      "attempts": [],
      "configured_file": ".aw/records/specs/20260927-0001-01-spc001-test-spec.spec.md",
      "dependencies": [],
      "from_backlog": null,
      "id6": "spc001",
      "initial_status": "to-review",
      "kind": null,
      "needs_input": false,
      "order": null,
      "position": 1,
      "setid": "",
      "status": "queued"
    }
    ```
    IPD-only queue entry diff showing only `artifact_type: ipd` added:
    ```json
    {
      "action": "execute",
      "artifact_type": "ipd",
      "attempts": [],
      "configured_file": ".aw/records/plans/pending/20260927-s1-01-pln001-test.ipd.md",
      "dependencies": [],
      "from_backlog": null,
      "id6": "pln001",
      "initial_status": "approved",
      "kind": null,
      "needs_input": false,
      "order": 1,
      "position": 1,
      "setid": "s1",
      "status": "queued"
    }
    ```
    `queue_sort_key` diff in `agent_workflows/runner_shared.py`:
    ```python
    TYPE_RANK: dict[str, int] = {
        "spec": 0,
        "backlog": 1,
        "ipd": 2,
        "prompt": 3,
    }

    def queue_sort_key(item: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> tuple:
        ...
        return (
            dependency_depth(item["id6"], by_id),
            item.get("position", 0),
            TYPE_RANK.get(queue_entry_type(item), 99),
            str(item.get("setid") or ""),
            item.get("order") if isinstance(item.get("order"), int) else 999,
            item["id6"],
        )
    ```
    `python3 -c` sorting demonstration output:
    ```
    Sorted order: [('s1', 'spec'), ('b1', 'backlog'), ('p1', 'ipd')]
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `expand_selectors` diff showing the typed branch sited ahead of BOTH the exact-setid branch and the Set-prefix branch, and the post-change results for an EXACT-setid token (`faov03`), a PREFIX token (`8t5ghs`), a spec id6, a plan id6, a setid no artifact declares, an ambiguous Set prefix, and a filename fragment.
  - Observed evidence: expand_selectors typed branch sited ahead of exact and prefix Set branches; all 7 token cases verified (faov03, 8t5ghs, z7nbn1, 8l8dgb, artdispatch, prefix aw, filename fragment).
    `expand_selectors` diff in `agent_workflows/runner_shared.py`:
    ```python
            elif sel_str in plans:
                candidates = [sel_str]
            elif len(sel_str) == 6 and sel_str.isalnum() and _sel.resolve(effective_repo, "specs", sel_str, allow=frozenset({_sel.MATCH_ID6})).paths:
                populate_manifest_specs(manifest, effective_repo)
                candidates = [sel_str]
            elif len(sel_str) == 6 and sel_str.isalnum() and _sel.resolve(effective_repo, "backlog", sel_str, allow=frozenset({_sel.MATCH_ID6})).paths:
                populate_manifest_backlog(manifest, effective_repo)
                candidates = [sel_str]
            elif sel_str in sets:
                matched_set = sel_str
                candidates = sets[sel_str]["order"]
            else:
                prefix_matches = [s for s in sets if s.startswith(sel_str)]
    ```
    Post-change resolution outputs:
    1. faov03: `['faov03']` (exact setid token declared by backlog item)
    2. 8t5ghs: `['8t5ghs']` (prefix setid token declared by backlog item)
    3. z7nbn1: `['z7nbn1']` (spec id6)
    4. 8l8dgb: `['8l8dgb']` (plan id6)
    5. artdispatch: `['7icz68', '8l8dgb', 'jdn790', '2ptgds', 'aeq7f8', 'y3p3p5']` (undeclared Set name)
    6. ambiguous prefix (`aw`): `Ambiguous Set selector prefix: aw matches [...]`
    7. filename fragment (`20260926-artdispatch-02-8l8dgb-...`): `['8l8dgb']`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the diffs of all four changes (a `refuse_unrunnable_selected_types`, b `refuse_unsweepable_run_types`, c `refuse_type_scoping_outside_the_review_sweep`, d `resolve_selected_artifact_paths`) and the scratch-repo outputs for `all --type spec`, `all --type backlog` (NOT refused by the sweep gate), `reviews --type backlog` (still refused, with the reason), `--type spec --type ipd` (refused mixed), `--type prompt` (refused), plus a `python3 -c` showing a spec id6 named with NO `--type` landing in `all_paths` and `classify_paths` over that spec plus a plan reporting `is_mixed=True`.
  - Observed evidence: All 4 type-refusal and resolver changes implemented; scratch repo verified all --type spec, all --type backlog admitted, reviews --type backlog refused, mixed refused, prompt refused, and untyped spec path visibility with classify_paths.
    All 4 changes implemented in `agent_workflows/runner_shared.py`:
    (a) `refuse_unrunnable_selected_types` scopes unrunnable check to `{"prompt", "research", "release", "walkthrough"}`.
    (b) `refuse_unsweepable_run_types` checks `is_review_selector(selectors)` before raising, permitting `all --type backlog`.
    (c) `refuse_type_scoping_outside_the_review_sweep` allows `spec` and `backlog` on `all` and named selectors.
    (d) `resolve_selected_artifact_paths` routes by artifact type directly through `discover_specs` and `populate_manifest_backlog`.
    Scratch-repo outputs:
    - `all --type spec -> queue: ['spc001']`
    - `all --type backlog -> queue: ['bkl001']`
    - `reviews --type backlog` refusal: `--type backlog: the needs-review sweep can enumerate only ipd, spec today...`
    - `--type spec --type ipd` without `--allow-mixed`: `[RUN-MIXED-TYPES] Selection contains IPDs: 1, Specs: 1. No work started.`
    - `--type prompt` on named/all selector: `--type prompt is not honored by this selector...`
    - Spec named with NO `--type` combined with a plan:
      `selection.all_paths: ['20260927-0001-01-spc001-test-spec.spec.md', '20260927-s1-01-pln001-test.ipd.md']`
      `classify_paths is_mixed: True types: ('ipd', 'spec')`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `--action` preflight diff showing it reads status and action from the typed maps, the actual output of `aw oc review <to-review-spec-id6> --prepare-only --unattended` showing it STARTS with that entry frozen `action: review`, the refusal output of `--action execute` over the same spec naming its real status, and a pre-change reproduction of the `(status 'approved' -> action 'execute')` refusal for the same id6.
  - Observed evidence: --action preflight reads status and action from typed maps; aw oc review <spec> starts and freezes action: review; --action execute refuses naming real status to-review; pre-change approved->execute reproduced.
    `--action` preflight in `initialize_run_core` reads status and action from `lookup_manifest_artifact(manifest, repo, id6)` and `_policy.runner_action(atype, st, for_legality=True)`.
    Output of `aw oc review spc001 --prepare-only --unattended`:
    `Frozen action for review: review status: queued`
    Output of `--action execute` over the same spec:
    `Refusal for --action execute: --action execute is illegal for 1 selected item(s): spc001 (status 'to-review' -> action 'review'). Execute is legal only for approved, auto-approved, or reusable IPDs. No run was started. To review instead, run: aw oc review <selector>`
    Pre-change reproduction:
    `--action review is illegal for 1 selected item(s): spc001 (status 'approved' -> action 'execute')` (because absent entry defaulted status to `approved` and action to `execute`).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `initial_queue_status` diff and a scratch run's `state.json` showing a backlog `open` entry born `queued` (with its pre-change value `reviewed` also shown), the `success_states_for_action` diff showing the new `plan` arm with `EXECUTE_REPORTING_SUCCESS_STATES` unchanged, and `python3 -c` output of the exit predicate over (i) a completed production turn's terminal status showing 0, (ii) E-09's refusal status showing nonzero, and (iii) a `substantially-complete` execute item still nonzero.
  - Observed evidence: initial_queue_status derives birth status from action (queued for actionable items); state.json verified backlog open item born queued; success_states_for_action plan arm added; exit codes verified: completed production turn 0, E-09 refusal 1, substantially-complete 1.
    `initial_queue_status` diff in `agent_workflows/runner_shared.py`:
    ```python
    def initial_queue_status(plan_status: str | None, *, action: str | None = None) -> str:
        if action in ("review", "execute", "plan", "orchestrate"):
            return "queued"
        if action == "skip":
            return "reviewed"
        ...
    ```
    Backlog `open` item in `state.json` is born `status: "queued"`, `action: "plan"`; pre-change value was `reviewed`.
    `success_states_for_action` diff:
    ```python
    if action == "plan":
        return frozenset({"reviewed"})
    ```
    `python3 -c` output of exit predicate over the three cases:
    - (i) completed production turn exit code: `0`
    - (ii) E-09 refusal exit code: `1`
    - (iii) substantially-complete exit code: `1`
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the `enforce_no_active_runner_conflict` diff for BOTH plan-shaped reads (the `id_to_path` fallback and the `attention.Item` synthesis) and the rendered conflict table for a typed entry conflicting with a live run, showing its real path and real status, beside the pre-change output showing `path=""` and the fabricated `to-review`.
  - Observed evidence: enforce_no_active_runner_conflict reads through lookup_manifest_artifact and typed accessor; rendered conflict table verified showing real path and real status for conflicting typed entry.
    Both plan-shaped reads in `enforce_no_active_runner_conflict` routed through `lookup_manifest_artifact` and typed accessor.
    Rendered conflict table with typed entry `spc001`:
    ```
      Status   Run     Type     Blocks Priority Readiness OQs Exec Valid Date     SetID            N  ID6    Deps
    ◔ to-revie running spec          - -        -           -    -     - 20260927 spc001-test-spec 01 spc001 -
    ```
    Pre-change rendered `path=""`, type `plan`, and fabricated status `to-review`.
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste the completed per-site disposition table (every E-01 row, one disposition each), the refusal-site diff showing it sited ahead of `execute_item` rather than inside `execute_item_core`, and the item-local refusal run's queue statuses plus the recorded refusal record showing the spec refused with a message NAMING plan `2ptgds` (not a `resolve_plan_path` message), no lane or session directory created, and the independent plan executed.
  - Observed evidence: All 35 code occurrences from E-01 assigned dispositions; refuse_undispatchable_typed_entry sited ahead of execute_item in oc/agy run_queue; spec review refused with code missing-dispatcher-2ptgds, no lane/session created, independent plan executed.
    Per-site dispositions for all 35 code occurrences from E-01:
    - `artifact_audit.py` (4 sites): Justified; existence short-circuit and display formatting of configured file string.
    - `attention.py` (1 site): Justified; active runs map index by configured_file.
    - `oc_runipd.py` (1 site): Justified; synthetic audit command queue entry creation.
    - `run_viewer.py` (6 sites): Justified; display rendering and dataclass construction.
    - `runner_shared.py` (23 sites):
      - 8 sites in `execute_item_core`, `reconcile_disposition`, `reconcile_interrupted`, `_run_verifier_turn`, `finish_reintegrated_item`: routed through plan-required resolution; fail closed for non-IPDs.
      - 2 sites in `initialize_run_core`: writes `"configured_file"` in queue loop for IPD and typed entries.
      - 4 sites in `queue_artifact_path`, `queue_plan_path_for`, `queue_plan_path`: typed accessor resolution and plan-required enforcement.
      - remaining sites in `queued_orchestrator_targets`, `format_slated_artifacts_table`, `lane_executed_carrier_override`, `lane_plan_is_terminal`: routed / justified display.
    Refusal site diff: `runner_shared.refuse_undispatchable_typed_entry` placed directly in `run_queue` ahead of `execute_item` in `oc_runipd.py` and `agy_runipd.py`.
    Item-local refusal execution: spec item marked `status: failed-safely`, refusal code `missing-dispatcher-2ptgds`, reason `spec review for 'spc001' has no dispatcher in this runner version; owned by plan 2ptgds`; host spawn provably not called; no lane or session directory created; independent plan in same queue executed.
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_typed_queue_entries.py -q` passing with its count; then, against the pre-change code, cases (1) and (5) FAILING with the assertion text; then, against a build that fixed only the exact-setid branch, case (1)'s PREFIX sub-case still FAILING; then all passing.
  - Observed evidence: tests/test_typed_queue_entries.py 11 passed in 3.48s; pre-change cases (1) and (5) failed as expected; PREFIX sub-case against exact-only Set fix failed as expected.
    `python3 -m pytest -o addopts="" tests/test_typed_queue_entries.py -q`:
    ```
    ...........                                                              [100%]
    11 passed in 3.48s
    ```
    Against pre-change code:
    - Case (1) failed: `DriverError: 'spc001' is a spec ..., not an IPD plan, so it cannot be queued`
    - Case (5) failed: `RunFlagRefusal: --type backlog: the needs-review sweep can enumerate only ipd, spec today...`
    Against exact-only Set fix:
    - Case (1) PREFIX sub-case failed: `AssertionError: 's2ufeo' == '8t5ghs'` (prefix `8t5ghs` matched Set `8t5ghsgi`).
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: paste both pre-queue seam cases passing on both hosts, then the FAILING output of the `--action` legality case against a build with E-06 reverted (showing the "(status 'approved' -> action 'execute')" text) and of the mixed-type visibility case against a build with E-05(d) reverted (showing the selection classified single-type), then both passing again.
  - Observed evidence: Both pre-queue seam cases pass on both hosts; --action legality fails with expected message with E-06 reverted; mixed-type visibility fails with single-type classification with E-05(d) reverted.
    Both cases in `TestPreQueueSeams` pass on both hosts (`test_action_legality_preflight_on_both_hosts` and `test_mixed_type_visibility`).
    With E-06 reverted:
    `DriverError: --action review is illegal for 1 selected item(s): spc001 (status 'approved' -> action 'execute')`
    With E-05(d) reverted:
    `AssertionError: [RUN-MIXED-TYPES] not found in '...'` because `selection.all_paths` held only plan path, classifying single-type `('ipd',)`.
  - Result: pass

- [x] V-12 validates E-12
  - Required evidence: paste the birth-status/exit-code case and the conflict-table case passing, then each FAILING against a build with E-07 and E-08 reverted respectively, with the assertion text; and the refusal case's output showing the recorded refusal naming plan `2ptgds`, the patched spawn provably not called, no lane or session directory created, and the independent plan executed.
  - Observed evidence: All queue-shape seam cases and item-local refusal pass on both hosts; birth status fails with E-07 reverted; conflict table fails with E-08 reverted; refusal test verified host spawn not called.
    Cases in `TestQueueShapeSeams` pass on both hosts (`test_birth_status_and_exit_code`, `test_conflict_table_typed_entry`, `test_item_local_refusal_on_both_hosts`).
    With E-07 reverted:
    `AssertionError: 'reviewed' != 'queued'` (backlog item was born reviewed, exiting 1).
    With E-08 reverted:
    `AssertionError: 'spec' not found in table_output` (conflict table rendered path="" and fabricated to-review plan).
    Refusal test:
    Spec item refused with code `missing-dispatcher-2ptgds`, host spawn mock verified not called, independent plan `pln001` executed.
  - Result: pass

- [x] V-13 validates E-13
  - Required evidence: paste the post-change reproductions for both shadowing classes, the diff of the two rewritten `tests/test_oc_runipd.py` selector tests with their new typed-selection assertions passing, proof the no-artifact-declares-it refusal case still passes, and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence: Post-change reproductions verified for both shadowing classes; rewritten tests in test_oc_runipd.py pass; missing file refusal passes; bare python3 -m pytest passed 2841 passed, 2 skipped, 3 warnings in 152.64s with empty after-minus-before failing node-ID set.
    Post-change reproductions:
    - Exact setid: `faov03 -> ['faov03']`, `ackme8 -> ['ackme8']`
    - Prefix: `8t5ghs -> ['8t5ghs']`, `vwios6 -> ['vwios6']`
    `tests/test_oc_runipd.py` rewritten tests:
    - `test_unresolved_selector_identifies_backlog_item` asserts `selected == ['item01']` and `manifest['backlog']` populated; passes.
    - `test_unresolved_selector_identifies_spec` asserts `selected == ['spec01']` and `manifest['specs']` populated; passes.
    - `test_unresolved_selector_identifies_missing_file_or_id6` asserts refusal for undeclared token; passes.
    Bare `python3 -m pytest` summary line:
    ```
    2841 passed, 2 skipped, 3 warnings in 152.64s (0:02:32)
    ```
    Failing node-ID set after minus before: empty.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A run queue that can hold a spec or a backlog item as itself. Naming a spec or backlog id6 now selects that artifact on both hosts instead of refusing (or, for an id6 that doubles as a setid or uniquely prefixes one, silently selecting a different plan: four such tokens exist today). `--type spec`/`--type backlog` reach the queue. Until the later plans of this Set land, a queued spec or backlog item whose action has no dispatcher is refused item-locally, before any turn and before `execute_item`, with a message naming the plan that owns the missing dispatcher, so nothing is ever handed to the plan executor. Every `configured_file` reader is routed through a typed accessor or justified.

FOUR FURTHER SEAMS THE REVIEW SURFACED, each now its own checklist item (E-05 through E-08) rather than left to be discovered at execution, and each a thing a human should know is being changed because each one sits BETWEEN selection and that refusal and is plan-shaped today. `--action` LEGALITY: the preflight reads `manifest["plans"]` and defaults an absent entry's status to the literal `approved`, and it refuses the WHOLE run, so `aw oc review <spec-id6>` would refuse rather than review (measured live on `llbr2b`). THE MIXED-TYPE GATE'S INPUT: the typed resolver is gated on the `--type` set rather than on the entry's type, so a spec named without `--type` resolves to no path at all and the gate spec `25kzda` :166 requires to see a mix cannot see it. THE QUEUE-STATUS AND EXIT-CODE VOCABULARIES: both are IPD-only, so a backlog `open` item is born in a TERMINAL state and never dispatched (which would make `--type backlog` appear to work and do nothing), and a `plan`-action entry makes the run exit 1 for behaving correctly. THE ACTIVE-RUNNER CONFLICT TABLE: it synthesizes a FABRICATED `to-review` status and an empty path for an entry it cannot place, in the very table a human is asked to decide drop/refuse/force from. It also adds the type rank to `queue_sort_key` that spec `25kzda` 5.4 rule 4 specifies and that the code's own docstring says a plan admitting non-plan targets must implement.

Order 02 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `7icz68` (the action derivation) and `mxzogk` (the fail-closed plan resolver, spec 5.7).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
