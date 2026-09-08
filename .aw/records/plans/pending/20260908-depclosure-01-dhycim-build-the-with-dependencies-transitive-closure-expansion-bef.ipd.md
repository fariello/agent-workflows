# IPD: Build the with-dependencies transitive closure expansion before the queue is frozen

- Date: 2026-09-08
- Kind: child
- Concern: `--with-dependencies` IS REGISTERED AND REFUSES, SO A SPEC-DECLARED BEHAVIOR IS UNOWNED. Spec `25kzda` (`- Status: approved`) declares it in the 2.1 grammar (`:137`) and defines it at `:160`: "expands the selection to the transitive declared dependency closure before the queue is frozen. Any newly introduced type is subject to the same mixed-type gate. Without the flag, dependencies outside the selection are checked against current repository state but are not silently enqueued." Section 5 repeats it (`:295`, `:398`, `:936`) and three error catalogue rows RECOMMEND it as the operator's remedy (`IPD-DEP-SATISFIED` `:667`, `IPD-DEP-CASCADE` `:668`, `IPD-EXEC-READY` `:708`, each ending "then run: aw <host> run <id6> --with-dependencies").
  SO THE TOOL TELLS AN OPERATOR TO RUN A FLAG THAT REFUSES. Measured at HEAD `fac69fbd`: the flag is a row in the shared table with `implemented=False` and `owner="backlog x8diyb (rundepflags-01)"` (`agent_workflows/runner_shared.py:1877-1888`), registered onto both hosts' parsers by `register_run_policy_flags` (`:1927`) and refused by `refuse_unimplemented_run_flags` (`:2011`) with "is not yet implemented: ... owns the behavior. The flag is registered so it fails HERE, loudly, rather than parsing and silently doing nothing" (`:2027-2031`). It has ZERO behavioral consumption sites; the only other references are two comments recording the absence (`oc_runipd.py:3385`, `:3870`).
  THE REFUSAL IS THE RIGHT INTERIM STATE AND MUST NOT BE MISREAD AS THE BUG. `refuse_unimplemented_run_flags`'s own docstring says why (`:2017-2022`): "an operator who passes `--with-dependencies` and gets no closure expansion has been told a falsehood about what the run enforced." A silent no-op here is a CORRECTNESS failure, not a UX gap. This plan replaces the refusal with the behavior, not with a shrug.
  THE INSERTION SEAM IS EXACT AND ALREADY HAS A PRECEDENT. `initialize_run` (`oc_runipd.py:2732`, twin `agy_runipd.py:1754`) runs flag refusal (`:2781`) -> `expand_selectors` (`:2785`) -> draft-admission gate, which REBINDS `queue_ids` rather than raising (`:2800`) -> dependency preflight (`:2844`) -> MIXED-TYPE GATE (`:2881`) -> run directory created (`:2891`) -> queue list built (`:2912-2983`) -> `state.json` written (`:3066`). Closure expansion belongs between `expand_selectors` and the mixed-type gate, rebinding `queue_ids` exactly as the draft gate already does, which also satisfies spec `:936` ("computes the transitive closure before mixed-type confirmation and freezing") for free.
  AND THE MIXED-TYPE RE-TRIGGER IS FREE BECAUSE THE GATE IS ALREADY POSITIONED AFTER SELECTION. `run_selection_policy.decide` (`:712`) is pure (its docstring says "no TTY, no host, no filesystem, no ledger"), `RUN_MIXED_TYPES` is at `:294`, and `runner_shared.enforce_mixed_type_gate` (`:2112`) is called at `oc_runipd.py:2881` / `agy_runipd.py:1871`. Expanding `queue_ids` before that call re-triggers the gate with no restructuring.
  THE ONE PIECE THAT DOES NOT EXIST YET IS THE CLOSURE ITSELF. `dependency_depth` (`oc_runipd.py:3803`) walks transitively but is restricted to targets ALREADY IN THE QUEUE (`:3820`, `edge.id6 not in by_id: continue`), so it cannot pull an outside target in; `check_engine.build_dependency_index` resolves identity and returns no closure. Parsing exists (`_read_item_dependencies` `oc_runipd.py:2062` -> `ipd_schema.parse_item_dependencies` `:722`), preflight exists (`enforce_dependency_preflight` `oc_runipd.py:2568`), dispatch re-check exists (`dependency_status` `:3482`, called at `:7306` / `agy_runipd.py:4261`). Only the expansion is new.
- Scope: Build `--with-dependencies` for real: a transitive closure over declared `Item-Dependencies` computed after selection and before the mixed-type gate, rebinding the selection, admitting targets the manifest does not yet carry, re-triggering the mixed-type gate on any newly introduced type, and flipping the flag row to `implemented=True` with its help text. EXCLUDES `--follow-generated` ENTIRELY, which shares the source item but is a different and much larger problem with no detection mechanism in existence (see Deferred and OQ-01); EXCLUDES changing satisfaction semantics, which spec `:295` fixes as unchanged; EXCLUDES registering `--type` or making a live mixed selection reachable.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_flag_surface.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py
- Item-Dependencies: none
- Status: to-review
- Set: depclosure
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: dhycim
- From-Backlog: x8diyb
- Blocks-Release: next

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `x8diyb`, WHICH IS DELIBERATELY SPLIT: this plan takes `--with-dependencies` ONLY and `--follow-generated` is NOT graduated. THE REASON IS A MEASURED ABSENCE, not a scoping preference: THERE IS NO MECHANISM BY WHICH A RUN DETECTS THAT AN AGENT TURN GENERATED A NEW IPD. Searched for it; `recommended_next_action` and `files_changed` appear ONLY inside the prompt text the runner SENDS the agent (`oc_runipd.py:4898`, `:4904`; `agy_runipd.py:2395`, `:2401`) and are never parsed back for a new-IPD claim; `generated_manifest_paths` (`runner_shared.py:309`) is about `INDEX.json`/`INDEX.md` merge conflicts and is unrelated; the queue is appended to at exactly ONE place, build time (`oc_runipd.py:2954`, `agy_runipd.py:1944`), and nothing re-discovers plans mid-run. So `--follow-generated` requires inventing detection AND mutating a deliberately frozen queue, which is a different plan and arguably a different design decision; graduating it here would produce a plan whose first E-item is "invent the missing half". The surviving half is recorded on the item and OQ-01 states what a future plan must answer. NOTHING IN THE `--with-dependencies` HALF IS OBSOLETE, and no plan in any disposition builds it: searched all five for `with-dependencies`, `follow-generated`, `rundepflags`, `x8diyb`, "dependency closure", `RUN-MIXED-TYPES`. Hits are `uyeko5` (executed; registered the refusals), `8guhs0`/`ovbnyq`/`r7xku3` (executed; explicitly DEFERRED the closure), `6lu3rq` (executed; built the mixed-type gate), and `kaygwo` (SUPERSEDED, whose E-07 promised both flags and was rejected NEEDS REPLAN, so this ground has been attempted once and must not be re-attempted the same way). THE ITEM'S GATE IS SATISFIED AND TWO OF ITS CLAIMS ARE NOW STALE: `uyeko5` is executed, so "the flags do not exist until `uyeko5` E-05 lands" is obsolete (they exist and refuse), and "doing it first would mean two sessions in the same runner code" no longer holds because the flag surface moved to `runner_shared.py`, not the runners. `wenmg4` (`specfresh-01`) DOES NOT AFFECT THIS: its `Scope-Paths` is the spec file alone, its scope is `25kzda`'s INFRASTRUCTURE PARAGRAPH (`:21-33`) only, and it explicitly excludes "CHANGING ANY DESIGN TEXT IN `25kzda`. Factual-status only" (`:116`) and "BUILDING ANY OF THE FIVE ENUMERATED ITEMS" (`:115`); neither flag is among the five. So 2.1's declarations stand. ONE CONSTRAINT THE ITEM DID NOT KNOW, and it is the real hidden cost: `discover_plans` (`runner_shared.py:1147`) walks only the two plans trees, so a `spec` or `backlog` dependency target has NO manifest entry at all, which is both why the mixed-type re-trigger is currently untestable on a live invocation (`runner_shared.py:2134-2141` records this) and why E-03 has to decide manifest admission rather than assume it. ALSO: a shipped contract test pins the current state and MUST be updated in the same change: `tests/test_run_flag_surface.py:680-684` asserts there are EXACTLY TWO unimplemented flags and names them, and `:280-286` requires `NOT YET IMPLEMENTED` and `x8diyb` in an unimplemented row's help.

## Goal

Make `--with-dependencies` do what the spec says and what three error messages already tell operators to run, so a prerequisite outside the selection is actually enqueued instead of the flag refusing, without weakening the mixed-type gate or the satisfaction rules.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the refusal and the seam

- [ ] E-01 CHARACTERIZE THE REFUSAL AND THE SEAM BEFORE CHANGING EITHER, so the change is measured. Capture the current refusal for `--with-dependencies` on BOTH hosts with its exit code, and record that it happens before the run directory exists (`refuse_unimplemented_run_flags` is called at `oc_runipd.py:2781` and `agy_runipd.py:1790`, ahead of run-dir creation at `oc_runipd.py:2891`), because that no-durable-state property must survive.
  THEN PIN THE SEAM ORDER as a test or an asserted trace: `expand_selectors` -> draft gate rebinding `queue_ids` -> dependency preflight -> mixed-type gate -> run dir -> queue build -> `state.json`. Spec `:936` requires closure BEFORE mixed-type confirmation and freezing, so the order is a contract, not an implementation detail.
  ALSO CAPTURE THE THREE ERROR MESSAGES that recommend the flag (`IPD-DEP-SATISFIED`, `IPD-DEP-CASCADE`, `IPD-EXEC-READY`), because they are the operator-facing promise this plan makes true, and a reviewer should be able to see the before state.
  - Depends on: none
  - Expected outcome: both hosts' current refusal captured with exit codes and the no-durable-state property recorded, the seam order pinned, and the three recommending error messages captured.
  - Execution state: pending

### Task group 2: compute the closure

- [ ] E-02 BUILD THE TRANSITIVE CLOSURE AS ONE HOST-NEUTRAL FUNCTION IN `runner_shared.py`, and do NOT extend `dependency_depth`. That function (`oc_runipd.py:3803`) deliberately skips targets not already in the queue (`:3820`, `edge.id6 not in by_id: continue`), which is correct for ORDERING and exactly wrong for EXPANSION; overloading it would break sorting for every run.
  PUT IT IN THE SHARED MODULE, NOT IN EITHER RUNNER. The flag row already lives in `runner_shared.RUN_POLICY_FLAGS` and both hosts call `register_run_policy_flags`; a closure implemented in `oc_runipd.py` and mirrored in `agy_runipd.py` would be the class-(d) re-fork the `rununify` Set exists to eliminate. One function, called from both `initialize_run`s.
  PARSE WITH THE EXISTING PARSER. `ipd_schema.parse_item_dependencies` (`:722`) via `_read_item_dependencies` (`oc_runipd.py:2062`) is the single definition of an edge. Do not re-parse `- Item-Dependencies:` by regex.
  HANDLE THE GRAPH HAZARDS EXPLICITLY, because a closure walk is where they bite: a CYCLE must terminate (visited set), a DIAMOND must not enqueue a target twice, a SELF-EDGE must not loop, and DEPTH must be bounded or at least explained. A closure that hangs or double-enqueues on a malformed graph is worse than a refusal.
  DECIDE WHAT AN UNRESOLVABLE TARGET DOES, and make it loud. An edge naming an id6 that resolves to nothing cannot be enqueued; refusing the run is defensible and so is proceeding with a stated warning, but SILENTLY DROPPING IT is not, because the operator passed a flag precisely to be sure prerequisites were queued. Record the decision. Note `f6idxs` (`depverb-01`) is separately making a dangling dependency target refuse pre-write, so the two must not contradict.
  - Depends on: E-01
  - Expected outcome: one host-neutral closure function in `runner_shared.py` using the existing edge parser, terminating on cycles, self-edges and diamonds without duplicate enqueue, with a recorded, loud decision for an unresolvable target consistent with `f6idxs`.
  - Execution state: pending

- [ ] E-03 ADMIT A CLOSURE TARGET THAT THE MANIFEST DOES NOT CARRY, which is the hidden cost the backlog item did not know about. `discover_plans` (`runner_shared.py:1147`) walks only the two plans trees, so a dependency target that is a `spec` or a `backlog` item has NO manifest entry, and a queue entry is built from manifest data (`oc_runipd.py:2912-2983`, entry fields at `:2954` onward including `configured_file`, `dependencies`, `order`).
  DECIDE AND RECORD WHAT HAPPENS FOR EACH TARGET TYPE. A plan target outside the selection is straightforward: it is in the manifest already. A non-plan target is not, and there are only a few honest options: extend discovery for the closure's benefit, construct a minimal entry, or REFUSE with a message naming the type. Choose one and write the reason; do not let a non-plan target silently vanish, since that recreates the falsehood the refusal exists to prevent.
  THIS IS ALSO WHY THE MIXED-TYPE RE-TRIGGER IS CURRENTLY UNTESTABLE ON A LIVE INVOCATION, a fact already recorded at `runner_shared.py:2134-2141`. Read that note before designing, and if this plan makes a live mixed selection REACHABLE for the first time, say so explicitly, because that is a meaningful change in what the gate can actually gate.
  DO NOT REGISTER `--type`. Spec 2.2/2.3 declares it and neither host registers it; that is another plan's scope and pulling it in would widen this one unreviewably.
  - Depends on: E-02
  - Expected outcome: a recorded per-type admission decision for closure targets absent from the manifest, with no silent drop, the `:2134-2141` untestability note consulted, and `--type` untouched.
  - Execution state: pending

### Task group 3: wire it at the seam and keep the gate honest

- [ ] E-04 REBIND THE SELECTION AT THE SEAM ON BOTH HOSTS, between `expand_selectors` (`oc_runipd.py:2785`, agy twin) and the mixed-type gate (`oc_runipd.py:2881`, `agy_runipd.py:1871`), following the draft-admission gate's existing precedent of rebinding `queue_ids` rather than raising (`oc_runipd.py:2800`).
  THE ORDER IS A SPEC CONTRACT, not a preference: `:936` requires the closure BEFORE mixed-type confirmation and freezing, and `:398` says "`--with-dependencies` may add the target and its transitive dependencies before freezing; without it, an unsatisfied external target cannot be met in this run."
  KEEP BOTH HOSTS' CALL SHAPE IDENTICAL, since these two `initialize_run`s are already a known divergence surface and several pending plans edit them.
  DO NOT TOUCH SATISFACTION SEMANTICS. Spec `:295` is explicit: "`--with-dependencies` changes selection, not satisfaction semantics. Every declared dependency is enforced whether or not its target was selected." So `enforce_dependency_preflight` (`oc_runipd.py:2568`) and `dependency_status` (`:3482`) keep their rules; only the SET being run changes. Also update or remove the now-false comment at `oc_runipd.py:3385` ("There is no `--with-dependencies` closure in this runner, so an unsatisfied external target simply cannot be met in this run"), because leaving it would misdirect the next reader.
  - Depends on: E-03
  - Expected outcome: the closure rebinds the selection before the mixed-type gate on both hosts with identical call shape, satisfaction semantics unchanged, and the stale `:3385` comment corrected.
  - Execution state: pending

- [ ] E-05 PROVE THE MIXED-TYPE GATE RE-TRIGGERS ON A NEWLY INTRODUCED TYPE, which spec `:160` and `:1103` both require ("any new type triggers mixed confirmation"; and on resume "Requires original `--with-dependencies` and `--allow-mixed` when expansion mixes types").
  THE GATE NEEDS NO RESTRUCTURING, which is the good news: `run_selection_policy.decide` (`:712`) is pure, `RUN_MIXED_TYPES` is `:294`, and `enforce_mixed_type_gate` (`runner_shared.py:2112`) already sits AFTER selection. Expanding before it is sufficient. Verify that claim rather than assuming it.
  TEST THE CONFIRMATION PATH, NOT ONLY THE CLASSIFICATION. The gate refuses non-interactively and confirms interactively; an expansion that mixes types must reach the same behavior an explicitly mixed selection would. Assert the refusal code and message identity.
  AND ASSERT THE NEGATIVE: an expansion that introduces NO new type must NOT trigger the gate. A gate that fires on correct behavior trains operators to pass `--allow-mixed` reflexively, which is the failure mode backlog `gjadwm` records.
  - Depends on: E-04
  - Expected outcome: an expansion introducing a new type reaching the same `RUN-MIXED-TYPES` behavior as an explicit mixed selection, and an expansion introducing no new type not triggering it, both asserted.
  - Execution state: pending

### Task group 4: flip the flag honestly and prove it

- [ ] E-06 FLIP THE FLAG ROW AND ITS HELP TEXT IN THE SAME CHANGE, or a shipped contract test fails. `tests/test_run_flag_surface.py:280-286` requires `NOT YET IMPLEMENTED` and `x8diyb` to appear in the help of any row with `implemented=False`, and `:680-684` asserts there are EXACTLY TWO unimplemented flags and names them.
  SET `implemented=True` AND NAME THE REAL OWNER on the `--with-dependencies` row (`runner_shared.py:1877-1888`), replacing `owner="backlog x8diyb (rundepflags-01)"` with the symbol that now owns the behavior, matching how every implemented row names its owner (for example `--unverifiable-ok` names `run_evidence.aggregate_run_exit`).
  UPDATE THE EXACTLY-TWO ASSERTION TO EXACTLY ONE, and leave `--follow-generated` as the remaining unimplemented row with its `x8diyb` ownership intact, since that half is deliberately not built here. Do NOT flip `--follow-generated`.
  REWRITE THE HELP TEXT to describe what it now DOES, not what it would do. The current text is subjunctive ("Would expand the selection ..."), which is correct today and wrong after.
  - Depends on: E-05
  - Expected outcome: `--with-dependencies` marked implemented with a real owner symbol and indicative help text, the exactly-two assertion updated to exactly one, and `--follow-generated` untouched and still refusing with its `x8diyb` ownership.
  - Execution state: pending

- [ ] E-07 PROVE THE WHOLE PATH ON FIXTURES, INCLUDING THE CASES THAT MUST NOT CHANGE. Minimum cases: (a) a selection whose plan declares an out-of-selection plan dependency gains it, transitively, with the flag; (b) WITHOUT the flag the same selection is unchanged and the external target is still merely state-checked (spec `:160`, and the behavior at `oc_runipd.py:3384-3450`); (c) a cycle terminates; (d) a diamond enqueues each target once; (e) a new type triggers the gate, no new type does not (E-05's pair); (f) an unresolvable target behaves as E-02 decided, loudly; (g) BOTH HOSTS behave identically.
  CASE (b) IS THE REGRESSION GUARD. The flag's whole contract is that it CHANGES nothing when absent; an implementation that expands unconditionally would silently enqueue prerequisites for every run, which is the opposite falsehood.
  ASSERT HOST PARITY BY IDENTITY WHERE POSSIBLE, the way sibling plans do: if both hosts call the same shared function, assert the object identity rather than duplicating behavioral tests.
  FIXTURES ONLY, AND NEVER A LIVE RUN. Do not invoke a real `aw oc run` or `aw agy run` against this repository: 92 plans are pending, 18 approved plans are executing in live runs, and three agents are graduating concurrently, so a real dispatch could start work on another agent's plan. Build synthetic manifests and plan trees in throwaway repos, as `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` already do.
  - Depends on: E-06
  - Expected outcome: seven fixture cases passing with the flag-absent case asserted as an unchanged selection, host parity shown by identity where the code is shared, and no live run dispatched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE FLAG SURFACE IS A SHARED DATA TABLE, NOT PER-RUNNER CODE. `RUN_POLICY_FLAGS` rows at `runner_shared.py:1865-1903`, registered by `register_run_policy_flags` (`:1927`) from `oc_runipd.py:7856`/`:7927` and `agy_runipd.py:4718`/`:4762`, refused by `refuse_unimplemented_run_flags` (`:2011`), frozen by `freeze_run_policy_flags` (`:2058`). New behavior belongs in the shared module.
- THE REFUSAL IS PRINCIPLED AND ITS REASONING IS WRITTEN DOWN. `:2017-2022`: accepting these flags as silent no-ops would tell "a falsehood about what the run enforced". Replace the refusal with behavior, never with acceptance.
- THE SEAM IS FIXED BY SPEC. `:936` requires the closure before mixed-type confirmation and freezing; `initialize_run`'s existing order is `expand_selectors` (`oc_runipd.py:2785`) -> draft gate rebinding `queue_ids` (`:2800`) -> preflight (`:2844`) -> mixed gate (`:2881`) -> run dir (`:2891`) -> queue build (`:2912`) -> state (`:3066`).
- THE DRAFT GATE IS THE PRECEDENT FOR REBINDING. It "EXCLUDES, IT NEVER REFUSES" and rebinds `queue_ids` rather than raising; the closure is the same shape in the opposite direction.
- `dependency_depth` CANNOT BE REUSED. `oc_runipd.py:3803`, and `:3820` skips targets not in the queue. It is for ORDERING; expansion is a different question.
- THE PARSER AND THE CHECKS ALREADY EXIST. `_read_item_dependencies` (`oc_runipd.py:2062`) -> `ipd_schema.parse_item_dependencies` (`:722`); `enforce_dependency_preflight` (`:2568`); `dependency_status` (`:3482`) re-checked at dispatch (`:7306`, `agy_runipd.py:4261`). Only expansion is new.
- THE MIXED-TYPE GATE IS PURE AND ALREADY POSITIONED. `run_selection_policy.decide` (`:712`, "no TTY, no host, no filesystem, no ledger"), `RUN_MIXED_TYPES` (`:294`), `enforce_mixed_type_gate` (`runner_shared.py:2112`) at `oc_runipd.py:2881`/`agy_runipd.py:1871`.
- THE MANIFEST IS PLANS-ONLY. `discover_plans` (`runner_shared.py:1147`) walks the two plans trees, which is why a non-plan target has no entry and why the mixed re-trigger is currently untestable live (`:2134-2141`).
- TWO SHIPPED CONTRACT TESTS PIN THE PRESENT STATE. `tests/test_run_flag_surface.py:280-286` (help honesty) and `:680-684` (exactly two unimplemented flags, named). Both must change with the flip.
- THIS GROUND WAS ATTEMPTED ONCE AND REJECTED. Superseded `kaygwo` E-07 promised both flags and drew NEEDS REPLAN. Do not re-attempt it as a single combined item; that is why this plan takes one flag.
- SPEC `25kzda` IS `approved`, AND `wenmg4` DOES NOT TOUCH 2.1's DESIGN TEXT (its scope is the infrastructure paragraph `:21-33`; it excludes design changes `:116` and building the enumerated items `:115`).
- RUNNER FILE CONTENTION: `51vw4y`, `3i0aaz`, `m7gvuz`, `1bfppy`, `xipfy1` all declare one or both driver files. The runner isolates worktrees, so this is merge ordering, not a runtime hazard.
- Shared checkout, live runs in progress, suite runs BARE. Fixtures only; never dispatch a real run.

## Findings

| Id | Severity | Area | What | Evidence |
|---|---|---|---|---|
| F-1 | HIGH | a spec-declared behavior refuses | `implemented=False`, `owner="backlog x8diyb (rundepflags-01)"`, refused with "is not yet implemented". Zero behavioral consumption sites. | `runner_shared.py:1877-1888`, `:2011`, `:2027-2031` |
| F-2 | HIGH | **and three error messages tell operators to run it** | `IPD-DEP-SATISFIED`, `IPD-DEP-CASCADE`, `IPD-EXEC-READY` each end "then run: aw <host> run <id6> --with-dependencies". So the tool recommends a flag that refuses. | spec `25kzda:667`, `:668`, `:708` |
| F-3 | HIGH | the closure does not exist and cannot be borrowed | `dependency_depth` skips targets not already in the queue (`:3820`); `check_engine.build_dependency_index` returns no closure. New code. | `oc_runipd.py:3803`, `:3820` |
| F-4 | MEDIUM | the seam is exact and spec-fixed | Insert between `expand_selectors` (`:2785`) and the mixed gate (`:2881`), rebinding `queue_ids` as the draft gate does (`:2800`). Spec `:936` requires exactly that order. | `oc_runipd.py:2732-3066`; spec `:936` |
| F-5 | MEDIUM | the mixed re-trigger needs no restructuring | `decide` is pure (`:712`) and the gate already runs after selection (`runner_shared.py:2112` from `:2881`/`:1871`). | those symbols |
| F-6 | HIGH | **a non-plan target has no manifest entry, which the item did not know** | `discover_plans` walks only the two plans trees, so a `spec`/`backlog` dependency target cannot be enqueued from manifest data, and this is also why a live mixed selection is currently unreachable. | `runner_shared.py:1147`, `:2134-2141` |
| F-7 | MEDIUM | two shipped contract tests pin the present state | Exactly-two-unimplemented assertion naming both flags, and a help-honesty assertion requiring `NOT YET IMPLEMENTED` and `x8diyb`. | `tests/test_run_flag_surface.py:680-684`, `:280-286` |
| F-8 | HIGH | **`--follow-generated` has no detection mechanism at all** | `recommended_next_action`/`files_changed` exist only in the prompt SENT to the agent (`oc_runipd.py:4898`, `:4904`; `agy_runipd.py:2395`, `:2401`) and are never parsed back; `generated_manifest_paths` (`runner_shared.py:309`) is about INDEX merge conflicts; the queue is appended to only at build time (`oc_runipd.py:2954`, `agy_runipd.py:1944`). Hence the split. | those symbols |
| F-9 | MEDIUM | this ground was attempted and rejected once | Superseded `kaygwo` E-07 promised both flags; verdict NEEDS REPLAN. | `kaygwo:136` |
| F-10 | MEDIUM | the item's gating rationale is stale, twice | `uyeko5` is executed so the flags DO exist and refuse; and the flag surface now lives in `runner_shared.py`, so "two sessions in the same runner code" no longer applies. | `runner_shared.py:1865-1903`; `.aw/records/plans/executed/...uyeko5...` |
| F-11 | MEDIUM | `wenmg4` does not weaken the requirement | Its scope is `25kzda`'s infrastructure paragraph (`:21-33`); it excludes changing design text (`:116`) and building the enumerated items (`:115`), and neither flag is among the five. | `wenmg4` |
| F-12 | LOW | a stale comment will misdirect the next reader | `oc_runipd.py:3385` states there is no closure in this runner; it becomes false and must be corrected in the same change. | that line |
| F-13 | LOW | satisfaction semantics must not move | Spec `:295`: the flag "changes selection, not satisfaction semantics. Every declared dependency is enforced whether or not its target was selected." | spec `:295` |
| F-14 | LOW | a sibling plan is deciding dangling-target behavior | `f6idxs` (`depverb-01`) refuses a dangling dependency target pre-write; E-02's unresolvable-target decision must not contradict it. | `f6idxs` |

## Proposed changes (ordered, validatable)

1. Characterize the refusal, the seam order and the three recommending messages (E-01).
2. Build one host-neutral closure in `runner_shared.py`, cycle/diamond/self-edge safe, with a loud unresolvable-target decision (E-02).
3. Decide and record manifest admission per target type, with no silent drop (E-03).
4. Rebind the selection at the seam on both hosts, satisfaction semantics untouched, stale comment corrected (E-04).
5. Prove the mixed-type gate re-triggers on a new type and does not on no new type (E-05).
6. Flip the flag row and help text and update both shipped contract tests, leaving `--follow-generated` refusing (E-06).
7. Prove seven fixture cases including the flag-absent regression guard and host parity (E-07).

## Deferred / out of scope (with reason)

- `--follow-generated`, THE OTHER HALF OF THE SOURCE ITEM. NOT graduated, and this is the plan's most important exclusion. No mechanism exists by which a run detects that a turn generated a new IPD (F-8), so the work is not "wire a flag" but "invent detection, then mutate a deliberately frozen queue, then make the generated IPD resolve its own `Item-Dependencies` before review-readiness" (spec `:945`). That is a different design with a different risk profile, and the one previous attempt to carry both flags together was REJECTED (`kaygwo` E-07, NEEDS REPLAN). OQ-01 records what a future plan must answer first. The flag stays registered and refusing, with its `x8diyb` ownership intact, which is the honest state.
- CHANGING SATISFACTION SEMANTICS. Spec `:295` fixes them as unchanged; only the selected SET moves.
- REGISTERING `--type`. Spec 2.2/2.3 declares it, neither host registers it, and it is out of this plan's scope (as `oc_runipd.py:3870`'s comment already records for the related type-rank question).
- MAKING A LIVE MIXED SELECTION REACHABLE AS A GOAL. If E-03's admission decision happens to make it reachable, SAY SO as a finding, because it changes what the gate can gate. But extending discovery beyond what the closure needs is a separate decision.
- CONSOLIDATING OR RE-HOMING THE RUNNERS. `runnerlayer` (`lyo1tz`, `9kmbr0`, `1f7xno`) and `rununify` (`5e4sb6`) own that. This plan adds to `runner_shared.py`, which is the direction they are already going.
- THE RETRY-BUDGET MIDDLE TIER. The sibling half of `uyeko5`'s deferrals, owned by backlog `dh3us4` and graduated to `y4adch` (`retrytier-01`). Different flag, different precedence chain; do not touch `resolve_retry_budget`.
- DANGLING-TARGET REFUSAL AT WRITE TIME. `f6idxs` (`depverb-01`) owns it. E-02 only decides what the CLOSURE does with an unresolvable target at run time, and must stay consistent with it.
- ANY REAL RUN DISPATCH. 92 pending plans, 18 approved plans executing, three concurrent graduations. A live `aw oc run`/`aw agy run` from this plan's tests could start work on another agent's plan.

## Scope check

- Over-scope: none. One closure function, one call site per host, one gate re-trigger, one flag row, three test modules.
- Scope-Paths justification: `agent_workflows/runner_shared.py` holds the `--with-dependencies` row (`:1877-1888`), `register_run_policy_flags` (`:1927`), `refuse_unimplemented_run_flags` (`:2011`, message `:2027-2031`), `enforce_mixed_type_gate` (`:2112`) and its untestability note (`:2134-2141`), `discover_plans` (`:1147`), and is where E-02's closure belongs; `agent_workflows/oc_runipd.py` holds `initialize_run` (`:2732`) with the seam (`:2785`-`:2881`), the queue build (`:2912-2983`), `dependency_depth` (`:3803`) that must NOT be reused, `_read_item_dependencies` (`:2062`) that must be, and the stale comment (`:3385`); `agent_workflows/agy_runipd.py` holds the twin `initialize_run` (`:1754`) and mixed-gate call (`:1871`) so both hosts change identically; `tests/test_run_flag_surface.py` holds the two shipped contract assertions (`:280-286`, `:680-684`) that E-06 must update; `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` are where E-07's per-host fixture cases belong.
- Under-scope, stated rather than left as `none`: this plan does not build `--follow-generated`, does not register `--type`, does not change satisfaction semantics, does not extend discovery beyond the closure's need, does not re-home the runners, does not touch the retry budget, does not add a write-time dangling-target refusal, and amends no spec (see the sync section, which explains why the spec is already correct).

## Required tests / validation

- SEVEN FIXTURE CASES (E-07), each named with pasted output: transitive expansion with the flag; UNCHANGED selection without the flag; cycle terminates; diamond enqueues once; new type triggers the gate; no new type does not; unresolvable target behaves as decided.
- THE FLAG-ABSENT CASE QUOTED SEPARATELY, since an unconditional expansion would silently enqueue prerequisites for every run, the opposite falsehood to the one the refusal prevents.
- BOTH HOSTS PROVEN, with object identity asserted where the closure is shared rather than duplicating behavioral tests.
- THE MIXED-TYPE PAIR PASTED: an expansion introducing a new type reaching the same `RUN-MIXED-TYPES` refusal code and message as an explicit mixed selection, and an expansion introducing no new type NOT triggering it.
- THE FLAG SURFACE CONTRACT TESTS UPDATED AND GREEN: `tests/test_run_flag_surface.py` re-run with its own summary line, showing the exactly-one-unimplemented assertion and `--follow-generated` still carrying `NOT YET IMPLEMENTED` and `x8diyb` in its help.
- THE REFUSAL FOR `--follow-generated` STILL CAPTURED after the change, proving the other half was not accidentally enabled.
- THE NO-DURABLE-STATE PROPERTY PRESERVED: a refused or gated invocation leaves no run directory. Paste the directory listing.
- THE SEAM ORDER RE-ASSERTED after the change (closure before the mixed gate before freezing), since spec `:936` fixes it.
- THE STALE COMMENT'S REMOVAL SHOWN (`oc_runipd.py:3385`), so the file does not contradict its own behavior.
- `python3 -m pytest` BARE, before and after, both summary lines pasted and the failure-set DELTA stated as a set, with the counts you actually observed. Criterion: AFTER minus BEFORE is EMPTY, never an absolute count.
- MEASURE EXIT CODES UNPIPED (`cmd >/dev/null 2>&1; echo $?`).
- NEGATIVE PROOF THAT NO REAL RUN WAS DISPATCHED: no new directory under the run root, and `git status --porcelain` clean of unexpected paths.
- `aw ipd lint --phase pre-transition` conforming, pasted.
- `aw sanitize --agent` clean.

## Spec / documentation sync

NO SPEC AMENDMENT IS NEEDED, AND THAT IS THE POINT: spec `25kzda` already specifies this behavior correctly and completely (`:160`, `:295`, `:398`, `:936`, `:1103`), and the code is what lags. So no `.spec.md` path is declared in `Scope-Paths`. If the executor finds the implementation cannot honor the spec as written, STOP and report rather than editing the spec to match the code: `25kzda` is `approved`, and quietly relaxing an approved requirement to fit an implementation is the failure the declare-your-spec-edits rule exists to prevent.

ONE SPEC-ADJACENT DECISION MUST BE RECORDED SOMEWHERE DURABLE, from E-03: what the closure does with a non-plan dependency target, given that the manifest is plans-only. The spec says "any newly introduced TYPE is subject to the same mixed-type gate", which presupposes non-plan targets are enqueueable. If E-03 concludes they are not (yet), that is a GAP BETWEEN SPEC AND IMPLEMENTATION and it must be written down as such, in the plan record and in the code comment, rather than silently narrowing the flag to plans only. A reviewer should treat a silent plans-only narrowing as a finding.

TWO OPERATOR-FACING TEXTS CHANGE. The `--with-dependencies` help must become indicative rather than subjunctive (E-06). And the three error catalogue messages that recommend the flag become TRUE for the first time; verify their wording still reads correctly now that the remedy works, and if one implies something the implementation does not do, report it. Operator-facing text: write no em or en dashes.

`--follow-generated`'s help and ownership must remain UNCHANGED, still naming `x8diyb`, because that half is deliberately not built. A reader must not be able to conclude from the code that both halves shipped.

## Open questions

### OQ-01: What must a future `--follow-generated` plan answer first?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, AND RECORDED HERE SO THE OTHER HALF OF THE SOURCE ITEM IS NOT LOST. `--follow-generated` is not graduated because the mechanism it needs does not exist: nothing detects that an agent turn generated a new IPD (`recommended_next_action` and `files_changed` appear only in the prompt SENT to the agent and are never parsed back; the queue is appended to only at build time). Three questions must be answered before it can be planned honestly. (1) HOW IS A GENERATED IPD DETECTED: by parsing a field the outcome file already carries, by scanning the plans tree after a turn, or by a new explicit claim in the outcome contract? Each has a different trust model, and the outcome file is agent-authored, so an unverified claim would let a turn inject work into its own run. (2) WHAT DOES IT MEAN TO ADD TO A FROZEN QUEUE, given that freezing is deliberate and `--resume` refuses several flags precisely to keep a run reproducible? Spec `:1103-1104` already says a resume "requires original `--follow-generated`", which implies the frozen options must record it, but not what the queue's identity becomes. (3) HOW DOES A GENERATED IPD RESOLVE ITS OWN `Item-Dependencies` BEFORE REVIEW-READINESS, which spec `:945` requires and which is a review-lifecycle question, not a queue question. Until these are answered, the honest state is the current loud refusal. A maintainer should decide whether the behavior is wanted at all before anyone plans it.

### OQ-02: What happens when a closure target cannot be resolved?

- Blocking: no
- Status: open
- Owner: none
- Resolution or deferral rationale: OPEN AND ASSIGNED TO E-02, because both defensible answers are genuinely defensible and the choice interacts with a sibling plan. REFUSING the run is attractive: the operator passed the flag precisely to be certain prerequisites were queued, and a partially expanded closure is exactly the falsehood `refuse_unimplemented_run_flags` was written to avoid. PROCEEDING WITH A LOUD WARNING is attractive too: a single dangling edge in one plan would otherwise block a large legitimate selection, and the dependency preflight and dispatch-time re-check will still refuse the affected item on its own merits. What is NOT acceptable, and this much is decided, is silently dropping the target. The interaction to respect: `f6idxs` (`depverb-01`) is making a dangling dependency target refuse at WRITE time, which shrinks how often this arises and argues for the stricter run-time choice. E-02 must pick one, record the reason, and stay consistent with `f6idxs`.

### OQ-03: Can a non-plan dependency target actually be enqueued today?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN BECAUSE IT IS A SPEC-VERSUS-IMPLEMENTATION GAP, not an implementation detail, and it is the one place this plan might have to narrow an approved requirement. Spec `:160` says "any newly introduced TYPE is subject to the same mixed-type gate", which presupposes a non-plan target can join the queue. But `discover_plans` (`runner_shared.py:1147`) walks only the two plans trees, so a `spec` or `backlog` target has no manifest entry, and `runner_shared.py:2134-2141` already records that this is why a live mixed selection is currently unreachable. Three options: extend discovery for the closure's benefit (widest, and it makes the mixed gate live for the first time, which is a real behavioral change deserving its own review), construct a minimal queue entry for a non-plan target (narrow but invents a second entry shape), or REFUSE a non-plan closure target with a message naming the type (honest, and preserves the spec's intent for a later plan). E-03 must choose and record; if it chooses to refuse, that narrowing must be written down as a spec-implementation gap rather than passed over, because a silent plans-only `--with-dependencies` would satisfy neither the spec nor the operator.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste both hosts' current `--with-dependencies` refusal with UNPIPED exit codes, and paste a directory listing proving no run directory was created. Paste the pinned seam order (closure point, mixed gate, freeze) as a test or asserted trace. Paste the three error catalogue messages that recommend the flag, with their spec line numbers.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the closure function's signature, docstring and body. Show it uses `ipd_schema.parse_item_dependencies` (via `_read_item_dependencies`) rather than a new regex, and show it does NOT extend `dependency_depth`. Paste passing cases for a cycle, a self-edge and a diamond, proving termination and single enqueue. State the unresolvable-target decision with its reason and confirm consistency with `f6idxs`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: state the admission decision PER target type with its reason, and show no code path silently drops a target. Confirm you read `runner_shared.py:2134-2141` and state whether this change makes a live mixed selection reachable for the first time. If the decision narrows the flag to plan targets only, paste the written spec-implementation gap note, since spec `:160` presupposes otherwise.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the rebinding call from BOTH hosts and show the call shapes are identical. Paste evidence the closure runs BEFORE `enforce_mixed_type_gate` and before the run directory is created. Paste `git diff` over `enforce_dependency_preflight` and `dependency_status` proving satisfaction semantics are byte-unchanged. Paste the corrected `oc_runipd.py:3385` comment.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the ACTUAL output for an expansion that introduces a new type, showing the same `RUN-MIXED-TYPES` code and message an explicit mixed selection produces, with the interactive and non-interactive paths distinguished. Paste the NEGATIVE case: an expansion introducing no new type not triggering the gate. Quote both assertions.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the changed `--with-dependencies` row showing `implemented=True`, a real owner symbol, and indicative help text. Paste `tests/test_run_flag_surface.py`'s own summary line green, and quote the updated exactly-one-unimplemented assertion. Paste `--follow-generated`'s row UNCHANGED and its refusal still firing, proving the other half was not enabled.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the ACTUAL passing output of all seven cases, QUOTING the flag-absent case separately as the regression guard and stating why an unconditional expansion would be the opposite falsehood. Paste the host-parity proof (object identity where shared). Paste negative proof that no real run was dispatched (no new run directory, `git status --porcelain` clean). THEN paste the BARE `python3 -m pytest` summaries before and after with the failure-set delta as a set and the counts you observed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

THIS PLAN CARRIES NO BLOCKING QUESTION, but THREE open questions carry real decisions and two of them are the maintainer's. OQ-03 (can a non-plan target be enqueued today) is the one to read first, because the honest answer may narrow an approved spec requirement, and E-03 is required to write that gap down rather than pass over it. OQ-01 records what a future `--follow-generated` plan must answer, so the deliberately-dropped half is not lost.

IT DELIBERATELY GRADUATES HALF OF ITS SOURCE ITEM. `--follow-generated` is not built because no mechanism detects a generated IPD (F-8), and the one previous attempt to carry both flags in one item was REJECTED (`kaygwo` E-07, NEEDS REPLAN). The flag stays registered and refusing with its `x8diyb` ownership intact, which is the honest state, and backlog `x8diyb` records the surviving half.

IT CARRIES `Blocks-Release: next`, inherited from backlog `x8diyb`. The justification is stronger than "a flag is missing": three error catalogue messages already instruct operators to run `--with-dependencies` as the remedy for an unmet dependency, so the tool currently recommends a flag that refuses.

EXECUTION CONTRACT. Commit only files this plan changed, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`, never `git add .`, never push. NEVER DISPATCH A REAL RUN: 92 plans are pending, 18 approved plans are executing in live runs, and three agents are graduating concurrently, so a live `aw oc run`/`aw agy run` from a test could start work on another agent's plan. Fixtures and throwaway repos only. Re-locate every symbol by NAME: both driver files are under concurrent edit and their line numbers moved by roughly 70 and 95 lines in a single day. Do NOT flip `--follow-generated`. Verify the staged set with `git diff --cached --name-only` before every commit and re-verify after any failed hook.

POST-GATE LIFECYCLE MOVE. Do not claim done or move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted evidence, including the flag-absent regression guard, the mixed-type pair in both directions, and the proof that `--follow-generated` still refuses.
