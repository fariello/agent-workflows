# IPD: Carry spec and backlog artifacts as typed queue entries and resolve their selectors on both hosts

- Date: 2026-09-26
- Kind: child
- Concern: THE QUEUE ADMITS ONLY PLANS (spec `z7nbn1` 4.1, "the single structural blocker"). The selector can FIND a spec or backlog item and the action table KNOWS what to do with it, but the manifest between them cannot carry it. Re-measured at HEAD `310ea53e`: `runner_shared.build_dynamic_manifest` compiles `discover_plans` output alone into `manifest["plans"]`; `initialize_run_core`'s queue loop reads `manifest["plans"][id6]` with a bare subscript and writes a plan-shaped entry (`"configured_file": plan["file"]`); `runner_shared.expand_selectors` refuses a spec id6 through `match_spec_selector` / `describe_spec_selector_refusal` and a backlog id6 through `describe_unresolved_plan_selector` ("'oc3mhb' is a backlog item ..., not an IPD plan"); `refuse_unrunnable_selected_types` refuses any non-`ipd` `--type` after the mixed-type gate; `refuse_type_scoping_outside_the_review_sweep` refuses `--type` on `all` and named selectors; and `RUN_TYPE_SWEEPABLE` is `{ipd, spec}`. A SECOND defect sits in the same path and must be fixed here or 5.9 is false: a backlog id6 that also names a Set is taken by the Set branch before any typed branch runs. Measured: `expand_selectors(m, ["faov03"])` returns plan `wja06w` (Set `faov03`, `to-review`), and `8t5ghs` / `vwios6` / `ackme8` resolve to plans through the Set-prefix branch, while their backlog items exist. `configured_file` was measured at 44 raw occurrences across six modules (`runner_shared` 28, `run_viewer` 6, `artifact_audit` 5, `oc_runipd` 2, `agy_runipd` 1, `attention` 1), of which 33 are code tokens rather than prose.
- Scope: IN: (a) a typed queue entry: every entry carries `artifact_type` (`ipd`/`spec`/`backlog`), and a typed accessor returns the entry's artifact path through the right per-type authority (plans through `resolve_plan_path`, which plan `mxzogk` makes fail closed; specs through `discover_specs`; backlog through `resolve_backlog_item`); (b) the manifest gains `specs` and `backlog` maps beside `plans` (additive; `plans` is unchanged), populated only for the ids a selection actually names or the `--type` set sweeps, so an ordinary IPD run's manifest and cost are unchanged; (c) `expand_selectors` resolves a spec or backlog id6 to THAT artifact (typed branch AHEAD of the Set and Set-prefix branches for an id6-shaped token that some non-plan artifact declares as its `- Id:`), replacing the two refusals; (d) `refuse_unrunnable_selected_types` and `refuse_type_scoping_outside_the_review_sweep` narrowed so `--type spec`/`--type backlog` reach the queue (still refusing `prompt`/`research`/`release`/`walkthrough`); (e) every `configured_file` read site that exists at execution enumerated and either routed through the accessor or justified (spec 5.8); (f) a non-plan queue entry whose action has no dispatcher yet (review of a spec until plan `2ptgds`, `plan` until plans `aeq7f8`/`y3p3p5`) is refused item-locally BEFORE any turn with a message naming the owning plan, so this plan never hands a spec to the plan executor. OUT: freeze-time whole-run refusal (plan `jdn790`); the spec review and production dispatchers themselves; `resolve_plan_path`'s own fail-closed fix (plan `mxzogk`, spec 5.7); the `--with-dependencies` closure's refusal of non-plan targets (`closure_target_admission`), which stays as is because a produced plan's `From-Spec` is provenance, not a dependency edge (spec `25kzda` 5.4).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/run_viewer.py, agent_workflows/artifact_audit.py, agent_workflows/attention.py, tests/test_typed_queue_entries.py, tests/test_oc_runipd.py, tests/test_runner_shared.py
- Item-Dependencies: executed:7icz68, executed:mxzogk
- Status: to-review
- Work-Kind: feature
- Priority: high
- From-Spec: z7nbn1
- Blocks-Release: next
- Set: artdispatch
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 8l8dgb

## Workflow history

- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from approved spec z7nbn1 (Order 02 of Set artdispatch). The four oc3mhb seams re-measured at HEAD 310ea53e; configured_file re-counted (44 raw / 33 code tokens across six modules); a backlog-id6-shadowed-by-Set defect found and measured (faov03 resolves to plan wja06w); no id6 collides across plans, specs and backlog (830/19/620 measured). Depends on mxzogk for spec 5.7.
- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Let a run queue carry a spec or a backlog item as itself, typed, so that naming one selects that artifact on both hosts and every downstream reader locates it through its own type's authority instead of assuming a plan.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: measure

- [ ] E-01 ENUMERATE AT THE EXECUTING HEAD. (1) Every `configured_file` CODE occurrence (not docstring or comment) under `agent_workflows/`, as a table: module, enclosing function, read or write, and what it does with the value (resolve a plan path, display, audit lookup, lane record). Use a tokenizer pass, not a raw grep count, and paste both the raw `grep -o configured_file agent_workflows/*.py | sort | uniq -c` and the code-token table (at authoring: 44 raw, 33 code tokens). (2) For each hosts' `initialize_run_core` path, paste the order of the refusals `refuse_unsweepable_run_types`, `refuse_type_scoping_outside_the_review_sweep`, `enforce_mixed_type_gate`, `refuse_unrunnable_selected_types`. (3) Reproduce: `expand_selectors(manifest, [<spec id6>])` and `[<backlog id6>]` refusals, and the Set-shadowing case (`faov03` -> `wja06w` at authoring; list every backlog or spec id6 that equals or prefixes a setid at execution). (4) Confirm no id6 collides across the plans, specs and backlog trees (at authoring: 830 plans, 19 id-bearing specs, 620 backlog items, zero collisions).
  - Depends on: none
  - Expected outcome: the enumeration table, the refusal order, and all reproductions are pasted; the collision set is empty.
  - Execution state: pending

### Task group 2: the typed entry

- [ ] E-02 ADD THE TYPED ACCESSOR in `runner_shared`: `queue_entry_type(item) -> str` (the entry's `artifact_type`, defaulting to `ipd` when absent so every existing run record and hand-written manifest keeps meaning a plan, per spec `z7nbn1` 5a "existing run records keep their queue shape") and `queue_artifact_path(repo, item) -> Path` that dispatches on that type: `ipd` -> `resolve_plan_path(repo, item["configured_file"], id6)` (unchanged semantics, now fail-closed via `mxzogk`); `spec` -> the `discover_specs(repo)[id6].path`, raising `DriverError` naming the id6 when absent; `backlog` -> `resolve_backlog_item(repo, id6)`, raising likewise. Never falls back from one type to another. Also add `queue_plan_path_for(repo, item)` semantics: a caller that REQUIRES a plan calls a helper that raises `DriverError("<id6> is a <type>, not an IPD plan")` for a non-`ipd` entry, so plan-only code paths refuse loudly instead of resolving.
  - Depends on: E-01
  - Expected outcome: the accessor returns the spec's path for a spec entry, the backlog file for a backlog entry, the plan for a plan entry or an entry lacking `artifact_type`, and raises for a mismatch.
  - Execution state: pending

- [ ] E-03 EXTEND THE MANIFEST AND QUEUE BUILDER. `build_dynamic_manifest` (or a sibling called by `initialize_run_core`) gains `specs` and `backlog` maps keyed by id6 holding `{file, status, set}` (plus `blocks_release` for later production checks), populated from `discover_specs` and a backlog enumeration over `backlog._iter_items` + `backlog.parse_item` (no new path literal; `check_engine._type_dirs`/`selectors` own the trees), LAZILY: only when the selection names a non-plan id6 or `--type` includes `spec`/`backlog`. `initialize_run_core`'s queue loop then builds an entry per selected id6 from whichever map owns it, with `artifact_type`, `configured_file` (the artifact's repo-relative path, kept for display and resume compatibility), `status`, `setid`, `dependencies: []` (specs and backlog items have no source-side dependency field, spec `25kzda` 2.10), `kind: None`, and `action` from plan `7icz68`'s `run_selection_policy.runner_action(artifact_type, status)`. The bare `manifest["plans"][id6]` subscript is replaced by a typed lookup that raises `DriverError` naming the id6 when no map holds it. `resolve_selected_artifact_paths` routes backlog ids through the backlog map, as it already routes specs through `discover_specs`.
  - Depends on: E-02
  - Expected outcome: `--prepare-only --unattended` over one spec id6 writes a `state.json` queue entry with `artifact_type: spec`, the spec's path, and action `review` for a to-review spec; an IPD-only run's manifest has no `specs`/`backlog` keys and its queue entries are byte-identical apart from the new `artifact_type: ipd` key.
  - Execution state: pending

### Task group 3: selection

- [ ] E-04 RESOLVE SPEC AND BACKLOG SELECTORS TO THEMSELVES in the shared `runner_shared.expand_selectors` (one definition for both hosts). For an id6-shaped token that is not a plan id6: if a spec or backlog item DECLARES it as `- Id:` (through `selectors.resolve(repo, <type>, token, allow=frozenset({selectors.MATCH_ID6}))`, the exact-declaration match, never a substring), return it as a typed selection, AHEAD of the Set and Set-prefix branches. Keep the existing precedence for everything else. Replace `describe_spec_selector_refusal`'s raise with the typed return, and make `describe_unresolved_plan_selector`'s backlog/spec branches unreachable for a declared id6 (keep them for non-declared tokens). The return shape must let `initialize_run_core` know each id's type (return typed tuples or populate the manifest's typed maps as a side effect; record which). An explicitly named spec/backlog id6 must still respect the retired-state refusal analogue: a `superseded` spec or a `done`/`graduated` backlog item is admitted and its action (`skip`) decides, rather than silently dropped.
  - Depends on: E-03
  - Expected outcome: `expand_selectors(m, ["faov03"])` selects backlog item `faov03`, not plan `wja06w`; `expand_selectors(m, ["z7nbn1"])` selects the spec; a plan id6, a setid that is not an artifact's declared id6, and a filename fragment resolve exactly as before.
  - Execution state: pending

- [ ] E-05 NARROW THE TYPE REFUSALS. `refuse_unrunnable_selected_types` refuses only types with no queue representation (`prompt`, `research`, `release`, `walkthrough`); `RUN_TYPE_SWEEPABLE` gains `backlog` only if the review sweep has a meaning for it (it does not: backlog has no review action in spec `25kzda` 3.4, so `reviews --type backlog` must stay a clear refusal and say why); `refuse_type_scoping_outside_the_review_sweep` admits `--type spec`/`--type backlog` on `all` and on named selectors by resolving `all --type spec` to every spec whose action is not `skip` (spec `25kzda` 2.4 "`aw oc run all --type spec` selects specs only"), deferring the empty-result wording to the existing `all` branch. The mixed-type gate (`enforce_mixed_type_gate`) already sees `selection.all_paths` and is unchanged.
  - Depends on: E-04
  - Expected outcome: `aw oc run all --type spec --prepare-only --unattended` on a scratch repo queues the specs; `--type spec --type ipd` without `--allow-mixed` still refuses `[RUN-MIXED-TYPES]`; `--type prompt` still refuses naming the missing dispatcher.
  - Execution state: pending

### Task group 4: every reader

- [ ] E-06 ROUTE OR JUSTIFY EVERY `configured_file` READ SITE from E-01's table (spec 5.8). Each row gets exactly one disposition, written into this plan's Findings at execution: (a) ROUTED through `queue_artifact_path` (sites that need the artifact, e.g. `queued_orchestrator_targets`, `spec_impacts_for_queue`, `queue_plan_path`, reporting); (b) ROUTED through the plan-required helper (sites that are plan-only by nature: `execute_item_core`'s `resolve_plan_path` calls, `reconcile_disposition`, verify and finalize re-resolution, lane integration, backlog close), which then refuse a non-plan entry loudly; (c) JUSTIFIED as display or audit of an opaque string (e.g. `run_viewer` rendering, `artifact_audit.find_plan_file`'s short-circuit, `attention`'s run-record read), with the reason. Add the E-02-(f) item-local refusal: in both hosts' dispatch loop, a non-`ipd` entry whose action has no dispatcher yet ends with a recorded refusal (`render_stream.record_refusal`, code naming the missing dispatcher and the plan that owns it) and a non-success terminal status, before any lane, session or prompt; a `skip` entry was never queued (plan `7icz68`).
  - Depends on: E-05
  - Expected outcome: every code occurrence has a disposition; a `queued` spec entry with action `review` run through `oc_runipd.run_queue` with `run_opencode` patched to fail if called ends refused, naming plan `2ptgds`, and an independent plan in the same queue still runs.
  - Execution state: pending

### Task group 5: prove it

- [ ] E-07 ADD `tests/test_typed_queue_entries.py` (behavioral only; temp git repos; no source or AST reads). Cases: (1) spec 5.9 on BOTH hosts: a spec id6 and a backlog id6, each also appearing in a plan's FILENAME and one also equal to a setid, resolve through `expand_selectors` + `initialize_run(--prepare-only)` to a queue entry of the right `artifact_type` and path, never to the plan; (2) the accessor returns the right path per type and raises on a mismatch or a missing id6; (3) an entry lacking `artifact_type` (an old run record) is read as `ipd`; (4) an IPD-only run's queue is unchanged apart from `artifact_type: ipd` and its manifest carries no typed maps; (5) `all --type spec` queues specs only and `reviews --type backlog` refuses with its reason; (6) the E-06 item-local refusal (spawn patched to fail the test); (7) a plan-only helper handed a spec entry raises `DriverError` naming the type. Update the existing refusal-expecting tests (`tests/test_oc_runipd.py` `test_unresolved_selector_identifies_backlog_item`/`..._spec` use UNDECLARED fixtures written without a matching filename grammar; keep them if they still refuse, change them only if their fixture now resolves, and say which) and the `tests/test_runner_shared.py` spec-selector refusal cases.
  - Depends on: E-06
  - Expected outcome: all pass on both hosts; (1), (5), (6) FAIL against the pre-change code.
  - Execution state: pending

- [ ] E-08 RE-RUN E-01's reproductions after the change and run the bare suite before and after.
  - Depends on: E-07
  - Expected outcome: `faov03` selects the backlog item; the spec and backlog selectors queue typed entries; the after-minus-before failing node set is empty.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `selectors.resolve(..., allow=frozenset({selectors.MATCH_ID6}))` is the exact-declaration match; `resolve_one`/`resolve_selectors` drop the verdict and must not back a new read path (their own docstring).
- `discover_specs` keys on `- Id:` and skips id-less legacy specs (19 of the corpus's spec files carry an id); `backlog._iter_items` + `parse_item` are the backlog enumeration; `resolve_backlog_item` already resolves one by id6.
- `resolve_selected_artifact_paths` already splits `plan_paths` (dependency preflight) from `all_paths` (mixed-type gate), per `ui8b9b` DECISION D5; this plan extends, not replaces, that split.
- Both hosts' dispatch loops treat `DriverError` from `execute_item` as item-local (`driver_error` recorded, loop continues).
- Test policy (maintainer ruling 2026-09-26): behavior tests only. Suites run BARE; narrowed runs use `-o addopts=""`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured at HEAD `310ea53e` (2026-09-26).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `build_dynamic_manifest` | Manifest holds plans only. | body: `for id6, rec in discovered.items(): plans_dict[id6] = {...}` over `discover_plans` |
| F-2 | HIGH | `initialize_run_core` queue loop | Bare subscript, plan-shaped entry. | `plan = manifest["plans"][id6]`; `"configured_file": plan["file"]` |
| F-3 | HIGH | `expand_selectors` | Spec and backlog id6 refuse. | `z7nbn1` -> "is a spec ..., not an IPD plan, so it cannot be queued"; `oc3mhb` -> "is a backlog item ..., not an IPD plan" |
| F-4 | HIGH | `expand_selectors` Set branches | A backlog id6 equal to or prefixing a setid resolves to that Set's plans. | `faov03` -> `['wja06w']` (Set `faov03`, plan `to-review`); `8t5ghs` -> `['s2ufeo']` via Set `8t5ghsgi`; `vwios6` -> 4 plans via `vwios6ipd`; `ackme8` -> `['w0ln4q']` |
| F-5 | MEDIUM | `refuse_unrunnable_selected_types`, `refuse_type_scoping_outside_the_review_sweep` | Non-`ipd` `--type` refused after resolution; `--type` on `all`/named selectors refused. | function bodies; both raise `RunFlagRefusal` naming spec `z7nbn1` |
| F-6 | INFO | `configured_file` | 44 raw occurrences / 33 code tokens across six modules. | `grep -o`: runner_shared 28, run_viewer 6, artifact_audit 5, oc_runipd 2, agy_runipd 1, attention 1; tokenizer pass 33 |
| F-7 | INFO | identity | No id6 collides across the three trees. | 830 plans, 19 specs, 620 backlog items; intersections empty |
| F-8 | INFO | cost | Backlog enumeration is cheap; plan discovery dominates. | reading 620 backlog items 0.028s, `discover_specs` 0.06s, `discover_plans` 1.46s |

## Proposed changes (ordered, validatable)

1. E-01 enumerates read sites and reproduces the refusals and the Set shadowing.
2. E-02 adds the typed accessor.
3. E-03 extends the manifest and queue builder.
4. E-04 resolves spec/backlog selectors to themselves.
5. E-05 narrows the type refusals.
6. E-06 routes or justifies every read site and refuses undispatchable entries item-locally.
7. E-07 adds behavioral tests.
8. E-08 re-probes and runs the suite.

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
- Under-scope: `agent_workflows/selectors.py`, `backlog.py`, `check_engine.py` are called, not changed. `run_viewer.py`, `artifact_audit.py`, `attention.py` are declared because E-06 may route a site; if a site is only justified, its module is acknowledged at finalize with `--scope-ack`.
- Scope-Paths justification: `runner_shared.py` holds the manifest, queue builder, selector expansion, refusals and accessor; the two host modules hold dispatch-loop entries and re-exports; the three reader modules hold `configured_file` sites; tests as listed.

## Required tests / validation

- `tests/test_typed_queue_entries.py` (new): seven behavioral cases on both hosts, including spec 5.9's spec-and-backlog proof; shown failing before the change.
- Existing selector-refusal tests updated only where their fixture now legitimately resolves.
- Bare `python3 -m pytest` before and after.

## Spec / documentation sync

- N/A: no `.spec.md` in `- Scope-Paths:`. This plan implements spec `z7nbn1` 4.1, 5.8 and 5.9 as written. Spec 5.7 (typed resolver refusing a spec supplied as a plan's `configured_file`) is owned and satisfied by plan `mxzogk`, on which this plan depends; spec 0.2 already records that `mxzogk` satisfies 5.7 if it executes first. Spec `25kzda` 5.4 rule 4's type rank (`spec`, `backlog`, `ipd`) becomes reachable once a queue holds more than one type; `queue_sort_key`'s docstring says a later plan must revisit it. This plan ADDS the rank to `queue_sort_key` as the key after `position` only if a mixed queue is reachable after E-05 (it is, under `--allow-mixed`), and records that in E-03's execution notes.
- No user-facing docs beyond `--help` text for `--type`, which is regenerated from the parser.

## Open questions

### OQ-01: Should the typed selector branch precede the Set branch?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: YES, from repository evidence (F-4): a backlog id6 is its own identity, while a setid is a shared cross-type topic label (DECISIONS D153, cited in `check_engine.check_collisions`), and the naming grammar lets a graduated item's plans reuse the item's id6 as their setid. Spec `z7nbn1` 1.1 and 5.9 require the id6 to resolve to THAT artifact. The branch fires only for an EXACT `- Id:` declaration, so a setid that no spec or backlog item declares is unaffected; E-01 lists every affected token at execution.

### OQ-02: Does an IPD-only run change?

- Blocking: no
- Status: resolved
- Owner: this plan's author
- Resolution or deferral rationale: only by one additive key (`artifact_type: ipd`) per queue entry. The typed maps are built lazily, so discovery cost and the manifest are unchanged; readers default a missing `artifact_type` to `ipd`, so old run records resume unchanged (spec `z7nbn1` 5a migration clause). E-07 case (4) pins it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the raw count, the code-token enumeration table, the refusal order, the three reproductions, the full shadowed-token list, and the empty collision set.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the accessor diff and a `python3 -c` run showing the per-type paths and the mismatch `DriverError` text.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the manifest/queue-builder diff, the `state.json` queue entry from a `--prepare-only --unattended` spec run, and a before/after diff of an IPD-only run's queue entries showing only `artifact_type` added.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `expand_selectors` diff and the post-change results for `faov03`, a spec id6, a plan id6, a plain setid, and a filename fragment.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the refusal diffs and the scratch-repo outputs for `all --type spec`, `--type spec --type ipd` (refused mixed), `reviews --type backlog` (refused with reason), and `--type prompt` (refused).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the completed per-site disposition table (every E-01 row, one disposition each) and the item-local refusal run's queue statuses showing the spec refused naming `2ptgds` and the independent plan executed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" tests/test_typed_queue_entries.py -q` passing with count; with E-03..E-06 reverted, cases (1), (5), (6) FAILING; passing again after restoring; and the updated existing tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the post-change reproductions and the bare `python3 -m pytest` summary line BEFORE and AFTER with the after-minus-before failing node-ID set (must be empty).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN IS APPROVING. A run queue that can hold a spec or a backlog item as itself. Naming a spec or backlog id6 now selects that artifact on both hosts instead of refusing (or, for an id6 that doubles as a setid, silently selecting a different plan). `--type spec`/`--type backlog` reach the queue. Until the later plans of this Set land, a queued spec or backlog item whose action has no dispatcher is refused item-locally, before any turn, with a message naming the plan that owns the missing dispatcher, so nothing is ever handed to the plan executor. Every `configured_file` reader is routed through a typed accessor or justified. Order 02 of Set `artdispatch`, graduated from spec `z7nbn1`, `- Blocks-Release: next`. Depends on `7icz68` (the action derivation) and `mxzogk` (the fail-closed plan resolver, spec 5.7).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the paths in `- Scope-Paths:`. If an edit outside the declared paths proves necessary, make it and justify it at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. New tests must be shown FAILING against the pre-change code.

Commit ONLY paths in `- Scope-Paths:` through `aw commit <plan> -- <paths>` (never `git add -A`, never push). On completion `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence; the terminal transition is `aw ipd finalize` (the runner owns it in a lane).
