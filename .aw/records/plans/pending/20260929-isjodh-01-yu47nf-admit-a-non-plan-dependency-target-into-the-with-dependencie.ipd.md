# IPD: Admit a non-plan dependency target into the --with-dependencies closure, and credit an in-queue one at the freeze gate

- Date: 2026-09-29
- Kind: child
- Concern: Backlog `isjodh` reports that `--with-dependencies` REFUSES a `spec` or `backlog` dependency target, narrower than approved spec `25kzda` Section 2.1, which says "Any newly introduced type is subject to the same mixed-type gate" and so presupposes such a target can join the queue. Re-measured at HEAD `171c92af`, the refusal is live and reproduces on BOTH hosts, but ALL THREE obstacles the item says a fixing plan must clear have since been closed by other work, and a FOURTH obstacle the item does not name is the one that actually blocks the fix. The user-visible defect is twofold: (a) a plan declaring a non-plan edge that is ALREADY SATISFIED runs fine bare and REFUSES under `--with-dependencies`, so a flag documented to change selection only (spec 2.6) turns a working invocation into a failing one; and (b) a plan declaring an UNSATISFIED non-plan edge cannot be run by ANY route the runner advertises, because the freeze-time refusal's own recovery text names two remedies and both refuse.
- Scope: Make `--with-dependencies` handle a non-plan dependency target honestly on both hosts. THREE coordinated changes, because each alone leaves a worse state than the refusal: admit a non-plan target in `runner_shared.closure_target_admission` (skipping one whose edge is already met, and refusing one whose edge enqueuing provably CANNOT satisfy rather than enqueuing a no-op); credit an IN-QUEUE non-plan target in `enforce_freeze_time_refusal`'s `exists`/`state` branch, which today never sets `could_be_met` and so refuses even when the queue contains the very item that would satisfy the edge; and order an admitted non-plan target AHEAD of its dependent in `dependency_depth`, which today skips every `edge.target_type != "ipd"` edge and so returns depth 0 for the dependent, letting it dispatch first and consume a status its target has not reached. Restore the behavioral coverage of this flag, which commit `19313eed` deleted entirely. EXCLUDES extending `discover_plans` to walk the specs or backlog trees (unnecessary: `lookup_manifest_artifact` already resolves both lazily); EXCLUDES changing satisfaction semantics, which spec 2.6 fixes as unchanged; EXCLUDES `--follow-generated`; EXCLUDES making the closure transitive THROUGH a non-plan node (see Deferred).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_typed_queue_entries.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: medium
- From-Backlog: isjodh
- Set: isjodh
- Order: 1
- Highest E allocated: 07
- Author: opencode model=pt3-claude-opus-5-1m-us
- Id: yu47nf

## Workflow history

- 2026-09-29 draft (opencode model=pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode model=pt3-claude-opus-5-1m-us): authored from backlog `isjodh`. Re-measured all three obstacles the item names and found each already closed by later work; located and measured a fourth (the freeze gate's `exists`/`state` branch) that is the real blocker, and a fifth (ordering) that admitting a target newly exposes. Restated the deliverable around those measurements rather than the item's now-stale premises.

## Goal

Leave the repository in a state where `--with-dependencies` treats a `spec` or `backlog` dependency target the way approved spec `25kzda` Section 2.1 says it should: enqueued when enqueuing can satisfy the edge, skipped when the edge is already met, and refused with a reason naming the specific status transition only when no dispatchable action on that target could ever satisfy it. Two operator-visible defects close as a result: adding `--with-dependencies` to a working invocation stops turning it into a refusal, and a plan whose non-plan edge is unsatisfied becomes runnable through the remedy the freeze-time refusal already advertises instead of being unrunnable by every advertised route.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin today's behavior before changing it

- [ ] E-01 Add a `unittest.TestCase` to `tests/test_typed_queue_entries.py` that pins the TWO measured defects as currently-failing-then-passing behavior, on BOTH hosts (`oc_runipd` and `agy_runipd`), driving the real `initialize_run` with `--prepare-only`. Case (a): a plan whose `Item-Dependencies` is `exists:spec:<id6>` against an EXISTING spec freezes successfully BARE, and must also freeze successfully WITH `--with-dependencies` (today the second raises `ClosureRefusal`). Case (b): a plan whose `Item-Dependencies` is `state:backlog:graduated:<id6>` against an `open` backlog item must, with `--with-dependencies --allow-mixed`, freeze a queue containing BOTH ids (today it raises `ClosureRefusal`). Assert on the frozen `state.json` queue contents, not on internal call counts.
  - Depends on: none
  - Expected outcome: A new test class exists whose assertions describe the intended behavior. Run it and paste the failure, so the defect is demonstrated by the suite before any production edit.
  - Execution state: pending

### Task group 2: the three coordinated production changes

- [ ] E-02 In `runner_shared.closure_target_admission`, replace the blanket `if edge.target_type != "ipd"` refusal with a three-way verdict that asks whether enqueuing the target could satisfy the edge. Order the checks so satisfaction is asked FIRST: an already-met non-plan edge returns `skip` (the same reason the plan path already gives), because today the refusal preempts even a satisfied edge. For an unmet edge, resolve the target through `lookup_manifest_artifact` and derive its action with `run_selection_policy.runner_action`; return `add` when that action is one the runner dispatches and which can move the target to the status the edge demands, and `refuse` otherwise, with a message naming the target's current status, the status the edge demands, and the reason the derived action cannot bridge them. An `exists:` edge against a MISSING target keeps refusing: enqueuing cannot create a record. Delete the now-false second bullet of the existing rationale comment (the unguarded-`manifest["plans"][id6]` claim) rather than leaving it to mislead.
  - Depends on: E-01
  - Expected outcome: `closure_target_admission` returns `skip` for a satisfied non-plan edge, `add` for an unmet one a dispatchable action can satisfy, and `refuse` with a status-naming message otherwise. `exists:spec:<absent>` still refuses.
  - Execution state: pending

- [ ] E-03 In `runner_shared.enforce_freeze_time_refusal`, give the `elif edge.kind in ("exists", "state")` branch the in-queue credit its `executed:` sibling already has. That branch reads the target's status and composes a `why` but never sets `could_be_met`, so an `exists`/`state` edge refuses the whole run even when the target is IN the queue with an action that will satisfy it. Set `could_be_met` when the target is in `queue_by_id`, is not frozen awaiting approval, and its frozen action can move it to the demanded status (the same predicate E-02 uses, called from one shared helper so the two cannot diverge). Leave the not-in-queue case refusing exactly as today.
  - Depends on: E-02
  - Expected outcome: A run whose queue contains both a dependent and the non-plan target that will satisfy its edge passes the freeze gate instead of refusing. A run whose target is absent from the queue still refuses with the same finding text.
  - Execution state: pending

- [ ] E-04 In `runner_shared.dependency_depth`, stop discarding a non-IPD edge whose target is IN THE QUEUE. The guard `edge.target_type != "ipd" or edge.id6 not in by_id` gives a dependent depth 0 when its only prerequisite is an in-queue spec or backlog item, so `queue_sort_key` ranks the two only by `position` and the dependent can dispatch FIRST. Count an edge whose target is present in `by_id` whatever its type, keeping the existing skip for an out-of-queue target (which is not a queue node and cannot order the queue). Update the docstring sentence that states the old rule as intentional.
  - Depends on: E-02
  - Expected outcome: For a queue holding a dependent and its in-queue non-plan target, `dependency_depth` returns 1 for the dependent and 0 for the target, and `simulate_dispatch_order` puts the target first regardless of requested position.
  - Execution state: pending

### Task group 3: coverage, contract, and the record

- [ ] E-05 Restore behavioral coverage for the closure, which commit `19313eed` deleted with `tests/test_run_flag_surface.py` (4,863 lines, including all eleven `DependencyClosureTests`). Add to `tests/test_typed_queue_entries.py` the cases that survive as behavior rather than as structure: the flag absent changes nothing; a transitive plan-only closure still enqueues; a cycle and a diamond each terminate and enqueue every target once; a terminal-disposition target is skipped; an unresolvable plan target refuses and leaves NO run directory. Each case must drive `initialize_run` and assert on frozen state or on the refusal, never on source text.
  - Depends on: E-04
  - Expected outcome: The closure has behavioral coverage again, including the no-durable-state property, and the refusal paths this plan preserves are pinned so a later change cannot silently widen them.
  - Execution state: pending

- [ ] E-06 Add the ordering and refusal cases this plan's own changes newly create, on BOTH hosts: a non-plan target whose edge no dispatchable action can satisfy (`state:spec:approved:<to-review id6>`, since approval requires a human attestation) refuses with a message naming both statuses and leaves no run directory; and the E-04 ordering property is asserted through `simulate_dispatch_order` on a frozen queue built by `initialize_run`, with the dependent requested FIRST so `position` alone would invert it.
  - Depends on: E-05
  - Expected outcome: The two behaviors introduced here are pinned by tests that fail if either regresses.
  - Execution state: pending

- [ ] E-07 Reconcile the record with what ships. Correct the stale `:166` offset in the three places that cite it for spec `25kzda`'s "any newly introduced type" sentence (which now sits in Section 2.1 at line 224): the refusal string in `closure_target_admission`, the `--with-dependencies` help text in `RUN_POLICY_FLAGS`, and the gap paragraph in `enforce_mixed_type_gate`'s docstring. Rewrite that help text and that docstring paragraph to describe the shipped behavior after E-02 through E-04 rather than the narrowing they currently record, citing symbols rather than offsets. Amend spec `25kzda` Section 5.4 rule 4 so its type-rank sentence does not read as licensing the pre-E-04 ordering, stating that a declared edge to an in-queue target outranks type rank whatever the target's type.
  - Depends on: E-06
  - Expected outcome: No shipped message, help string, or docstring still describes the plans-only narrowing or cites `:166`, and the spec's ordering rule agrees with the implemented sort key.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). This plan is itself a case study: the backlog item and three shipped strings cite spec `25kzda` `:166`, and the sentence they mean has since moved to line 224.
- `runner_shared` must import NEITHER runner. The satisfaction predicate is threaded in as `edge_satisfied_fn` rather than imported, enforced by `tests/test_runner_shared.py::NoRunnerImportTests::test_runner_shared_imports_neither_runner` and `tests/test_rununify_host_descriptor.py::TheSharedModuleStaysCleanTests`. E-02's new predicate must obey this.
- One shared core serves both hosts: `oc_runipd.initialize_run` and `agy_runipd.initialize_run` both delegate to `runner_shared.initialize_run_core`, and both bind the same `edge_satisfied` object. So each change here lands once, and every test asserts it on both hosts.
- `run_selection_policy.action_for_status` is the single status-to-action authority ("No other module may carry a second status-to-action mapping"), with `runner_action` layering runner-only refinements. E-02 and E-03 must consume it rather than writing a second table.
- Tests must assert observable behavior, never code structure (AGENTS.md; GUIDING_PRINCIPLES P16). The deleted `DependencyClosureTests` are restored in E-05 as behavior only.
- The suite runs BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The refusal is live and host-symmetric. A plan declaring `state:spec:reviewed:<id6>` refuses under `--with-dependencies` on both hosts with `ClosureRefusal`. | Drove `oc_runipd.initialize_run` and `agy_runipd.initialize_run` with `--prepare-only --unattended --with-dependencies`; both raised `ClosureRefusal: state:spec:reviewed:spctor: --with-dependencies cannot enqueue a spec target.` |
| F-02 | **The item's obstacle 1 is closed.** It says "`discover_plans` walks the two plans trees only, so the manifest cannot carry one." True of `discover_plans`, but `runner_shared.lookup_manifest_artifact` now resolves specs and backlog lazily via `populate_manifest_specs` / `populate_manifest_backlog`, and the queue builder's non-plan branch already builds a typed entry. So no discovery change and no second queue-entry shape is needed. | `lookup_manifest_artifact(manifest, repo, "spc001")` returned `('spec', {...})` on a manifest built from `discover_plans` alone. `aw oc run <spec-id6>` froze a queue of `[('spc001', 'spec', 'plan', 'queued')]` on both hosts. |
| F-03 | **The item's obstacle 2 is closed.** It says the mixed gate is fed `selected_plan_paths`, built in a loop that drops a manifest-absent id inside `except (DriverError, KeyError): continue`. `initialize_run_core` now passes `list(selection.all_paths)` from `resolve_selected_artifact_paths`, whose plans branch falls THROUGH to the specs and backlog branches, so a non-plan id resolves rather than being dropped. | `resolve_selected_artifact_paths(repo, manifest, ["pln001","spc001","bkl001"], ("ipd",))` returned all three paths in `all_paths` with `unresolved == ()`. A mixed selection raised `[RUN-MIXED-TYPES]`, proving the gate SEES the mix. |
| F-04 | **The item's obstacle 3 is closed.** It says the queue builder's per-item first statement is an unguarded `manifest["plans"][id6]` raising a bare `KeyError` after the run directory exists. That statement is now `lookup_manifest_artifact(manifest, repo, id6)`, which raises `DriverError`; and the queue build, both freeze gates, and the mixed gate all precede the `run_dir` mkdir. | Queue-build loop's first statement is `atype, item_info = lookup_manifest_artifact(manifest, repo, id6)`. `lookup_manifest_artifact({"plans": {}}, repo, "zzzzzz")` raised `DriverError: No manifest entry found for artifact 'zzzzzz'`. Pending plan `kqb9ok` E-04 owns correcting the three stale comments that still assert the subscript. |
| F-05 | **The real blocker, unnamed by the item.** `enforce_freeze_time_refusal`'s `elif edge.kind in ("exists", "state")` branch reads the target's status and composes a `why` but NEVER assigns `could_be_met`, unlike the `executed:` branch which credits an in-queue target. So admitting a non-plan target is insufficient on its own: the run still refuses. Measured by monkeypatching the admission to permit non-plan targets. | With admission patched permissive, `--with-dependencies --allow-mixed` on a plan needing `state:spec:reviewed:spctor` still raised `[RUN-DEPENDENCY-UNSATISFIABLE] pln001 requires state:spec:reviewed:spctor; spctor is to-review`, even though `spctor` WAS in the expanded selection. |
| F-06 | **Admitting a target newly exposes an ordering defect.** `dependency_depth` skips every edge whose `target_type != "ipd"`, so a dependent whose only prerequisite is an in-queue non-plan target gets depth 0, same as the target. `queue_sort_key` then ranks them by `position`, and type rank is only the THIRD key, so the dependent can dispatch first and consume a status its target has not reached. | For a queue of `pln001` (declaring `state:backlog:graduated:bklopn`, position 1) and `bklopn` (position 2), both depths were 0 and `simulate_dispatch_order` returned `['pln001','bklopn']`. The identical graph with an IPD target gave depths 1 and 0 and order `['pln002','pln001']`. |
| F-07 | **Defect (a): the flag turns a passing run into a failing one.** A plan whose non-plan edge is ALREADY SATISFIED freezes fine bare and refuses under `--with-dependencies`, because the type check precedes the satisfaction check. This contradicts spec 2.6: "`--with-dependencies` changes selection, not satisfaction semantics." It also fires for an edge on a plan the operator never named, when that plan is pulled in transitively. | `edge_satisfied(exists:spec:spcapp)` returned `True`; bare run froze `OK`, `--with-dependencies` raised `ClosureRefusal`, on both hosts. Selecting only `pln002` (which depends on `pln001`, which declares the spec edge) also refused. |
| F-08 | **Defect (b): an unsatisfied non-plan edge makes a plan unrunnable by every advertised route.** The freeze refusal's recovery text says "Add it to the selection or run with --with-dependencies". Both were tried and both refuse, so the operator must satisfy the edge by hand outside the runner. The same shape with an IPD target is fully recoverable. | Bare: `[RUN-DEPENDENCY-UNSATISFIABLE]`. Adding the spec to the selection: same finding (F-05's uncredited branch). `--with-dependencies`: `ClosureRefusal`, both hosts. With an IPD target instead, `--with-dependencies` froze `[('pln001','ipd','execute'), ('pln002','ipd','execute')]`. |
| F-09 | **Not every non-plan edge is satisfiable by enqueuing, so `add` cannot be unconditional.** An `exists:` edge is met by existence alone, so enqueuing a missing target cannot create it. `state:spec:approved:<id6>` cannot be reached by any runner action, because approval requires a human attestation. But `state:backlog:graduated:<open id6>` and `state:spec:reviewed:<to-review id6>` ARE reachable, via the `plan` and `review` actions. This is why E-02 derives the action instead of blanket-admitting. | `runner_action` returned `plan` for `backlog/open`, `review` for `spec/to-review`, `plan` for `spec/approved`, `skip` for `backlog/graduated`. `_SPEC_ACTIONS` has no row producing `approved`. |
| F-10 | **The closure has ZERO test coverage.** No test in `tests/` references `closure_target_admission`, `expand_dependency_closure`, `ClosureRefusal`, or `CLOSURE_TERMINAL_BUCKETS`. All eleven `DependencyClosureTests`, including the non-plan refusal and no-durable-state cases, were deleted with `tests/test_run_flag_surface.py`. The only live mention of the flag is a helper parameter. | `grep -rn` for each symbol across `tests/` returned no hits. `git show --stat 19313eed` shows `tests/test_run_flag_surface.py | 4863 -----`. Sole live mention: `tests/test_action_table_runner_parity.py:205,221`. |
| F-11 | **Zero blast radius in this repository today.** Across 935 discovered plans, all 199 typed edges are `executed:ipd`; not one non-plan edge is declared. So the change cannot alter any existing plan's run, and the defect is latent rather than currently biting. This bounds the risk and also argues against a larger redesign. | Parsed every `PlanRecord.dependencies` across `discover_plans`: `executed/ipd x199`, non-plan total `0`. |
| F-12 | The `:166` citation is stale in three shipped strings. Spec `25kzda`'s "Any newly introduced type is subject to the same mixed-type gate" now sits in Section 2.1 at line 224; line 166 is an unrelated sentence about the `prompt` verb. The offset is hardcoded in the refusal message, the flag's `--help`, and `enforce_mixed_type_gate`'s docstring, so the shipped error currently mis-cites the spec. | Read the spec file: line 224 carries the sentence; line 166 reads "The `prompt` verb may report transport success...". The literal `25kzda :166` appears in `closure_target_admission`'s refusal f-string and in the `RUN_POLICY_FLAGS` help text. |
| F-13 | The closure is not transitive THROUGH a non-plan node, and after E-02 it silently will not be. The walk pushes an admitted id onto the frontier and then calls `resolve_plan_path` on it, which raises for a non-plan id and `continue`s, so that node's own edges are never read. Harmless in practice (neither specs nor backlog items carry `Item-Dependencies`), but it must be stated rather than discovered later. | With admission patched permissive, the record showed `visited: ["pln001","spctor"]` and `added: [spctor]`, yet the spec's text was never parsed for edges: `_read_item_dependencies` on a spec returns `([], None)` and `resolve_plan_path(repo,"","spcapp")` raised `DriverError`. |
| F-14 | No file overlap with the one live sibling. Pending plan `kqb9ok` (Set `ghff0p`) touches `runner_shared.py`, `run_selection_policy.py`, and `tests/test_typed_queue_entries.py`, and its E-04 corrects `closure_target_admission`'s stale comment. Its scope section explicitly leaves the `isjodh` question out: "Out of scope and explicitly left to a plan that can review the discovery change on its own merits." Two plans touch the same comment, so whichever lands second must reconcile; the runner isolates lanes and revalidates on merge. | Read `kqb9ok`'s `- Scope-Paths:` and its Deferred section. Set `depclosure` has no sibling plans: `dhycim` is its only member, status `executed`. |

## Proposed changes (ordered, validatable)

1. Pin both measured defects as failing tests on both hosts (E-01), so the change is demonstrated rather than asserted.
2. Extract one predicate answering "can a dispatchable action on this target move it to the status this edge demands?", derived from `run_selection_policy.runner_action`, and use it from BOTH `closure_target_admission` (E-02) and `enforce_freeze_time_refusal` (E-03). One definition, because a closure that admits a target the freeze gate then refuses is the exact failure F-05 measures.
3. Reorder `closure_target_admission` so satisfaction is asked before type, making an already-met non-plan edge a `skip` and closing defect (a) (E-02).
4. Credit an in-queue non-plan target in the freeze gate's `exists`/`state` branch, closing defect (b) (E-03).
5. Count an in-queue non-plan edge in `dependency_depth`, so an admitted target is ordered ahead of its dependent (E-04).
6. Restore the deleted closure coverage as behavioral tests, plus cases for the two behaviors this plan introduces (E-05, E-06).
7. Correct the stale `:166` citations and the narrowing prose, and amend spec 5.4 rule 4 so the ordering contract matches the implemented key (E-07).

## Deferred / out of scope (with reason)

- **Extending `discover_plans` to walk the specs and backlog trees.** Unnecessary and would be a real behavioral change to every run's manifest. `lookup_manifest_artifact` already resolves both types lazily (F-02), so the queue entry the item worried about already exists.
  - Carrier-Declined: This is not deferred work but a REJECTED design option. F-02 measures that the capability it would add already exists by another route, so there is no residual obligation for a carrier to own.
- **Making the closure transitive THROUGH a non-plan node (F-13).** No spec or backlog record carries `Item-Dependencies`, so there is nothing to traverse; building traversal for a case that cannot occur would add a code path no test could exercise honestly. Recorded in F-13 and noted in the walk so the next reader is not surprised.
  - Carrier-Declined: Unreachable by construction, not postponed. Neither the spec nor the backlog record contract admits an `Item-Dependencies` field, so no artifact can declare the edge this traversal would follow. If either contract ever gains one, that change is the trigger to revisit, and it would carry its own plan.
- **`--follow-generated`.** Shares the source backlog item `x8diyb` with the closure but is a different and much larger problem, excluded by `dhycim` before it and excluded here. `tests/test_runner_shared.py::FollowGeneratedRemovedTests` pins its removal.
  - Carrier-Declined: Already removed, not outstanding. `dhycim` excluded it and the removal is pinned by `tests/test_runner_shared.py::FollowGeneratedRemovedTests`, which asserts the flag is absent from the shared tables and rejected by both host parsers. Any future attempt to build it is new work needing its own backlog item, not an obligation this plan hands off.
- **Changing satisfaction semantics.** Spec 2.6 fixes them as unchanged: "Every declared dependency is enforced whether or not its target was selected." This plan changes which items are SELECTED, which items are CREDITED as in-queue, and the ORDER they run; it does not change what satisfies an edge.
  - Carrier-Declined: A boundary statement, not an obligation. The approved spec forbids this change, so there is nothing for a future carrier to pick up; a plan proposing it would have to amend spec 2.6 first.
- **Correcting the two OTHER stale bare-subscript comments** (`match_spec_selector`, and `run_selection_policy`'s gate census). Owned by pending plan `kqb9ok` E-04/E-05 (F-14). This plan corrects only the one inside the function it rewrites, which it cannot avoid touching.
  - Carrier: kqb9ok
- **The mixed-type gate's own behavior.** After this change a non-plan target genuinely can enter a selection, making a live mixed expansion reachable for the first time; the gate already handles it (F-03, `[RUN-MIXED-TYPES]` observed) and needs no edit. Whether `--with-dependencies` should IMPLY `--allow-mixed` is a policy question for the maintainer, not a defect: spec 2.1 says `--full-auto` does not imply `--allow-mixed`, so the conservative reading is that the operator confirms the mix. Raised as OQ-02.
  - Carrier-Declined: No work is outstanding on the gate itself: F-03 measures it already refusing a mixed selection correctly, so this row records a verified non-need. The open policy question it raises is carried by OQ-02 below, which is where a maintainer ruling belongs; duplicating it as a second obligation here would double-count one decision.

## Scope check

- Over-scope: none. Every edit is inside the three declared paths and is required by a measured finding: E-02 by F-07/F-09, E-03 by F-05, E-04 by F-06, E-05 by F-10, E-01/E-06 as the coverage for those, E-07 by F-12.
- Under-scope: `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` are deliberately NOT in Scope-Paths. Both delegate to `runner_shared.initialize_run_core` and bind the same `edge_satisfied`, so the behavior lands once in the shared module; the tests assert it on both hosts. If execution finds a host-local edit is genuinely required, that is a scope change to declare and reconcile, not to absorb silently.

## Required tests / validation

- The new and restored cases in `tests/test_typed_queue_entries.py`, each driving the real `initialize_run` on BOTH hosts with `--prepare-only` and asserting on frozen `state.json` or on the refusal raised. No test may read production source text (AGENTS.md; P16).
- The full suite, run BARE as `python3 -m pytest`, with the actual summary line pasted.
- Targeted regression of the surfaces these functions feed: `tests/test_typed_queue_entries.py`, `tests/test_freeze_time_refusal.py`, `tests/test_dependency_block_reporting.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_run_selection_policy.py`, `tests/test_runner_shared.py`, `tests/test_action_table_runner_parity.py`, `tests/test_orchestrator_retirement.py`. The ordering change in E-04 touches `queue_sort_key`, which every run consumes, so `test_orchestrator_retirement.py` and `test_action_table_runner_parity.py` are load-bearing here rather than incidental.
- `aw check` and `aw ipd lint` on the amended spec and on this plan.

## Spec / documentation sync

- `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md` is declared in Scope-Paths and WILL be amended by E-07, at Section 5.4 rule 4. WHY, since a spec edit changes the contract every other plan is reviewed against: rule 4 lists type rank as an ordering key among "simultaneously ready independent nodes", and rule 5 already says "Explicit declared dependencies always win". E-04 makes a declared edge to an in-queue non-plan target actually win, which rule 5 mandates and which the pre-E-04 code did not do. Left unamended, rule 4's type-rank sentence reads as licensing the behavior F-06 measures, and the next reader cannot tell which rule governs. The amendment states the precedence explicitly rather than changing it.
- Section 2.1's `--with-dependencies` bullet needs NO amendment: this plan moves the implementation toward what it already says. The narrowing prose that must change is in the code (E-07), not the spec.
- No user-facing documentation change: `--with-dependencies` is documented through its generated `--help`, which E-07 rewrites.

## Open questions

### OQ-01: Should an unmet non-plan edge whose target cannot be advanced by any runner action refuse, or skip with a warning?

- Blocking: no
- Status: resolved
- Owner: opencode model=pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: REFUSE, following the precedent this function already sets for an unresolvable target: "an operator passes `--with-dependencies` to be CERTAIN the prerequisites are in the queue; a partially expanded closure delivers a selection that is neither the one they asked for nor the one they would have got without the flag." A skip-with-warning would expand the selection, leave the edge unmet, and then let the freeze gate refuse anyway, so the operator gets a less specific error later instead of a precise one now. Refusing at the seam also preserves the no-durable-state property. The refusal message must name the current status, the demanded status, and why no action bridges them, so it is actionable rather than merely a denial.

### OQ-02: Should `--with-dependencies` imply `--allow-mixed` once it can introduce a new type?

- Blocking: no
- Status: resolved
- Owner: opencode model=pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: NO, it must not imply it, and the approved spec settles this rather than leaving it to taste. Section 2.1's own `--with-dependencies` sentence says a newly introduced type "is subject to the same mixed-type gate", which requires the confirmation rather than waiving it, and the same section states that even `--full-auto` "does not imply `--allow-mixed`", so the strongest automation flag in the grammar does not buy this consent either. An implication would also be the one change here that silently WIDENS what an unattended run may execute: the closure can pull in a target the operator never named (F-07 measures a refusal firing for an edge on a transitively added plan), so the mix being confirmed is not always visible in the invocation. This plan therefore implements the conservative behavior, and the cost is one extra flag on a genuinely mixed expansion.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Paste the output of running ONLY the new test class before any production edit, showing it FAILING with `ClosureRefusal` for both the satisfied-edge case and the backlog-target case, on both hosts. A test that passes before E-02 would not be pinning the defect.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste a transcript showing, at execution HEAD, `closure_target_admission` returning `("skip", ...)` for an already-satisfied `exists:spec:<existing>` edge, `("add", "")` for `state:backlog:graduated:<open>`, and `("refuse", ...)` for both `exists:spec:<absent>` and `state:spec:approved:<to-review>`, with the refusal text quoted showing both statuses named. Also paste the diff hunk proving the false unguarded-subscript bullet was deleted.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the frozen queue from a run of a plan declaring `state:backlog:graduated:<open id6>` with `--with-dependencies --allow-mixed`, on BOTH hosts, showing both ids present and no `[RUN-DEPENDENCY-UNSATISFIABLE]`. Then paste the still-refusing case where the target is NOT in the queue, showing the finding text unchanged, proving the credit was narrowed to in-queue targets only.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: For a queue built by `initialize_run` holding a dependent at position 1 and its in-queue non-plan target at position 2, paste `dependency_depth` for both ids (expect 1 and 0) and `simulate_dispatch_order` (expect the target first). Paste the same measurements for an all-IPD queue to show that ordering did not move.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste the passing run of the restored closure cases, and for the unresolvable-target case paste an assertion result proving the runs root contains NO run directory after the refusal. Paste a `grep -rn` over `tests/` for `inspect`, `ast`, or source-reading in the new code showing none, evidencing the tests are behavioral.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the passing run of both new cases on both hosts, with the refusal message quoted for the unsatisfiable-status case showing it names the current and demanded statuses, and the dispatch order asserted for the inverted-position ordering case.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste `grep -rn '25kzda :166' agent_workflows/` returning no hits. Paste the new `--with-dependencies --help` output verbatim from BOTH `aw oc run start --help` and `aw agy run start --help`, showing the plans-only narrowing text is gone and the two remain byte-identical. Paste the spec diff for Section 5.4 rule 4 and the passing `aw check` / `aw ipd lint` output. FINALLY, as this is the last item, paste the ACTUAL bare `python3 -m pytest` summary line showing the full fast suite passing, plus the targeted regression run over the nine files named in Required tests. If any test fails, paste the failure and do not mark this item complete.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit ONLY the files in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`; never `git add -A`, never push, never `--no-verify`. The three production changes in Task group 2 are coordinated and must land together: each alone leaves a worse state than today's refusal (admitting without E-03 produces an expansion the freeze gate still refuses, which is F-05 measured; admitting without E-04 produces a dependent that dispatches before its prerequisite, which is F-06). Do not mark this plan executed, and do not move it to `.aw/records/plans/executed/`, until `aw ipd lint --phase pre-transition` reports conforming and EVERY `V-*` above carries pasted evidence from an actual run. E-07 amends an APPROVED spec, which is declared in Scope-Paths and will be announced by the runner before the run starts; the amendment is confined to Section 5.4 rule 4 and its rationale is recorded in Spec / documentation sync above.

Post-gate lifecycle move: on completion, transition with the tooled path (`aw ipd set executed <id6>`) so the move and the `## Workflow history` record are written together, and report the backlog item `isjodh` as satisfied by this plan's `- From-Backlog:` link rather than closing it by hand.
