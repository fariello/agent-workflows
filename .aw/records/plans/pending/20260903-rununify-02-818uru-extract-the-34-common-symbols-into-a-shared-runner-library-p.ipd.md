# IPD: extract the 34 common symbols into a shared runner library, pure move

- Date: 2026-09-03
- Kind: child
- Concern: 34 top-level symbols are defined TWICE, once per runner, with AST-identical bodies. Because they are identical there is no behavioral disagreement TODAY, which is exactly why they are the dangerous class: nothing signals when one copy is edited and the other is not, and that is how the 52 currently-diverged symbols got that way. Measured at HEAD `c8bb11ae` by research `tvnq50` (E-01 of orchestrator `5e4sb6`): 33 are AST-identical, `print_status` is identical after host-token normalization, and together they are 551 lines of the runners' definition mass. The concrete cost of leaving them duplicated is already visible: `DriverError` is defined in BOTH runners (`oc_runipd.py:202`, `agy_runipd.py:379`) as two DISTINCT classes, and `agy_runipd.py:87-93` records a hand-written wrapper that exists solely to translate one into the other, because `enforce_dependency_preflight` raises oc's class and agy's `main` cannot catch it.
- Scope: Create ONE shared runner library and move all 34 class (a) symbols into it, then have both runners import them. PURE MOVE: no body may change, and every move is verified by an AST-identity assertion against the pre-move definition plus an object-identity assertion that both runners resolve to the same object. Excludes reconciling any diverged symbol (deferred behind `lanectn` and E-02's characterization baseline), excludes the class (d) re-forks (child 01 owns them), excludes re-homing the 40 names `agy_runipd` already imports from `oc_runipd`, and excludes any behavior change whatsoever, including the `DriverError` wrapper's REMOVAL if removing it would alter what `main` catches.
- Scope-Paths: agent_workflows/runner_common.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_common.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:2r306y
- Status: to-review
- Set: rununify
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 818uru
- Blocks-Release: next

## Workflow history

- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored FROM E-01's inventory (research `tvnq50`), per orchestrator `5e4sb6`'s SECOND GATE. THREE CORRECTIONS to the orchestrator's child table, all from measurement rather than preference. (1) The count is **34, not 35** (33 AST-identical plus `print_status`, identical only after host-token normalization, which the table's "byte-identical" framing would have wrongly excluded). (2) The table calls this a "pure move ... verified by an identity assertion", which holds, but a naive lift FAILS: four symbols in the set call symbols OUTSIDE it (`run_checked` -> `pinned_child_env`, `discover_plans` -> `parse_plan_file`, `save_state` -> `write_report`, `validate_manifest` -> `parse_dependency_token`), and two of those four are class (c) DIVERGED, which this plan may not touch. E-02 resolves that by dependency injection rather than by dragging diverged code along. (3) `DriverError` is a LATENT BUG, not merely a duplicate: two distinct classes with a hand-written translation wrapper already documented at `agy_runipd.py:87-93`. Unifying it is the highest-value single symbol here and is sequenced first. Authored review-ready, not draft.
- 2026-09-03 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give each of the 34 identical symbols exactly ONE definition, in one shared module both runners import, without changing a single line of any body and without touching a diverged symbol.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the module, and the identity harness that makes "pure move" falsifiable

- [ ] E-01 Create `agent_workflows/runner_common.py`, following `host_runner.py`'s conventions (module docstring stating what it owns and why, section banner comments, no import of either runner so no cycle can form). It starts EMPTY of moved logic; this item establishes the module and its contract only. Record in the docstring the constraint that decides every later question here: this module holds only symbols PROVEN identical across both runners, it may never import either runner, and a symbol whose bodies differ belongs in a later child, not here. Per OQ-02 of the orchestrator, this module is the shared runner library and `plan_readiness.py` is DESIGNATED a peer it may import, NOT absorbed (its consumers include `status_set.py` and `ipd_schema.py`, which are not runners).
  - Depends on: none
  - Expected outcome: a new module that imports cleanly, defines no runner logic yet, and states its own admission rule; `python3 -c "import agent_workflows.runner_common"` succeeds and a cycle check shows it imports neither runner.
  - Execution state: pending

- [ ] E-02 Build the MOVE HARNESS before moving anything, because "pure move" is a claim that must be mechanically checkable rather than eyeballed 34 times. Capture the pre-move AST fingerprint of all 34 symbols from BOTH runners (`ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)`, the same method E-01 of the orchestrator used), store it as a fixture, and assert after each move that the shared definition's fingerprint EQUALS the captured one. RESOLVE THE FOUR OUTSIDE-DEPENDENCIES here, which is the part a naive lift gets wrong (measured): `run_checked` calls `pinned_child_env` (oc-only, host-specific), `discover_plans` calls `parse_plan_file` (class (c) DIVERGED), `save_state` calls `write_report` (class (c) DIVERGED), `validate_manifest` calls `parse_dependency_token` (oc-only, host-specific). A moved symbol must NOT import a diverged symbol from a runner, because that both re-creates the coupling and drags undecided behavior into shared code. Use INJECTION: the moved function takes the dependency as a parameter (or the module exposes a small registration seam), and each runner passes its own. State the mechanism once and apply it uniformly.
  - Depends on: E-01
  - Expected outcome: a fixture of 34 pre-move fingerprints; a documented injection mechanism; a test that FAILS if any moved body's fingerprint differs from its pre-move capture. Paste the mechanism and one worked example.
  - Execution state: pending

### Task group 2: move by seam, smallest and safest first

Move order is deliberate: each seam is independently verifiable, and the two seams with outside-dependencies come last so the harness is already proven on clean cases.

- [ ] E-03 Move the `DriverError` unification FIRST, alone, because it is the one symbol here that is a latent BUG rather than only a duplicate. `oc_runipd.py:202` and `agy_runipd.py:379` define two DISTINCT classes; `agy_runipd.py:87-93` documents a hand-written `enforce_dependency_preflight` wrapper whose only purpose is translating oc's class into agy's so agy's `main` can catch it. Move the single definition to `runner_common`, have both runners import it, and then check whether that wrapper is still needed. DO NOT DELETE THE WRAPPER AS A MATTER OF COURSE: if removing it changes what `agy_runipd.main` catches or what message it prints, it stays and this plan records why. `StallTimeout` subclasses agy's `DriverError` (`agy_runipd.py:383`), so verify the subclass relationship still holds after the move.
  - Depends on: E-02
  - Expected outcome: exactly one `DriverError` in the package; `oc_runipd.DriverError is agy_runipd.DriverError` is True; `issubclass(agy_runipd.StallTimeout, runner_common.DriverError)` is True; agy's `main` still catches a preflight refusal and still prints its `runagy: ...` message, demonstrated rather than asserted; an explicit statement of whether the wrapper was kept or removed, with the reason.
  - Execution state: pending

- [ ] E-04 Move the RUN/MISC seam (5 remaining symbols, 37 lines): `utc_now`, `should_color`, `new_run_id`, `state_root`, `resolve_run_dir`. `print_status` is deliberately NOT in this item: it is the one host-naming-only symbol, so it needs the normalization decision E-06 makes.
  - Depends on: E-03
  - Expected outcome: five symbols defined once; both runners' attributes are the same objects by `assertIs`; fingerprints match the pre-move capture.
  - Execution state: pending

- [ ] E-05 Move the GIT seam (6 symbols, 53 lines): `_run_git`, `git_head`, `git_branch`, `git_status`, `git_common_dir`, `run_checked`. `run_checked` carries the `pinned_child_env` outside-dependency, so apply E-02's injection mechanism here and treat this as its first real exercise. Note `_run_git` is ALSO defined in `layout_inventory.py` and `layout_migration.py` but those are NAME COLLISIONS with different bodies, not re-forks (verified in E-01's sweep) - do not "unify" them.
  - Depends on: E-04
  - Expected outcome: six symbols defined once, `run_checked`'s dependency injected rather than imported from a runner, and the collision note verified rather than assumed.
  - Execution state: pending

- [ ] E-06 Move the JSON/STATE seam (7 symbols, 47 lines): `load_json`, `atomic_write_json`, `append_jsonl`, `sha256_file`, `load_state`, `save_state`, `state_root` if not already moved, plus `print_status`. TWO SPECIAL CASES: `save_state` calls `write_report`, a class (c) DIVERGED symbol, so it must be injected, never imported; and `print_status` differs between runners ONLY by host tokens, so moving it requires deciding how the host string is supplied (a parameter, almost certainly) and PROVING the rendered output is byte-identical to each runner's current output for both hosts.
  - Depends on: E-05
  - Expected outcome: eight symbols defined once; `write_report` injected; `print_status` renders byte-identically to today for BOTH hosts, shown side by side.
  - Execution state: pending

- [ ] E-07 Move the LANE seam (8 symbols, 242 lines, the largest): `_lane_records_from_state`, `describe_lane`, `format_lane_report`, `print_lane_interrupt_report`, `build_recovery_lane_notice`, `allocate_isolation_worktree`, `teardown_isolation_worktree`, `disable_lane_prompt`. CONTENTION WARNING, and it is the reason this seam is LAST: six of the seven `lanectn` plans declare both runner modules in their Scope-Paths. They name none of these eight symbols (verified: zero mentions across all seven plans), so there is no logical conflict, but there is a real TEXTUAL conflict risk if `lanectn` lands while this is in flight. Re-read both runners immediately before editing and stop rather than overwrite.
  - Depends on: E-06
  - Expected outcome: eight symbols defined once, fingerprints matching, and an explicit statement of whether `lanectn` landed in the interim and how conflicts were handled.
  - Execution state: pending

- [ ] E-08 Move the PLAN/SELECTOR seam (7 symbols, 170 lines): `discover_plans`, `resolve_plan_path`, `plan_bucket`, `_read_set`, `_read_order`, `describe_unresolved_plan_selector`, `validate_manifest`. `discover_plans` depends on `parse_plan_file` (DIVERGED) and `validate_manifest` on `parse_dependency_token` (oc-only), so both are injected. Then extend child 01's symmetric re-fork guard to cover all 34 moved symbols, so a future re-fork of any of them fails a test in EITHER runner, and sabotage-verify that extension in both directions.
  - Depends on: E-07
  - Expected outcome: seven symbols defined once; the guard's table now covers all 34 plus child 01's five; sabotage in each runner fails the guard.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `host_runner.py` is the precedent for a shared runner-adjacent module: a docstring stating what it owns and its security/design posture, banner comments per section, and no import of a caller. Copy the conventions, not the contents.
- `agy_runipd.py:69-146` already imports 40 names FROM `oc_runipd`, with a comment at `:84-96` explaining why there is no cycle and why the `as <same-name>` re-export form is load-bearing (ruff removed 6 of them on a first attempt and a symmetry test caught it). Any import this plan adds must survive the same autoformatter pressure.
- The runners' anti-re-fork guard is being made symmetric by child 01; this plan EXTENDS that table rather than writing a second guard.
- The orchestrator's hard constraints inherited here: a child may not change behavior, must land in BOTH runners or neither, and may not exceed one cohesive seam.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The count is **34**, not the orchestrator's 35: 33 AST-identical plus `print_status`, identical only after host-token normalization. 551 oc lines total. | research `tvnq50`, measured at HEAD `769989ce` and re-confirmed at `c8bb11ae` |
| F-2 | A NAIVE LIFT FAILS. Four moved symbols call symbols outside the set: `run_checked` -> `pinned_child_env` (oc-only), `discover_plans` -> `parse_plan_file` (DIVERGED), `save_state` -> `write_report` (DIVERGED), `validate_manifest` -> `parse_dependency_token` (oc-only). Importing a DIVERGED symbol into shared code would drag undecided behavior along and re-create the coupling. | AST call-graph over the 34 symbols against the runners' top-level name set |
| F-3 | `DriverError` is a LATENT BUG, not just a duplicate: two DISTINCT classes, with a hand-written translation wrapper already documented in-tree. This is the strongest single argument for the whole Set. | `oc_runipd.py:202`, `agy_runipd.py:379`, and the comment at `agy_runipd.py:87-93` |
| F-4 | `agy_runipd` already imports 40 names from `oc_runipd`, so the runners are NOT peers today: agy depends on oc. A shared module is therefore a correction of layering, not merely de-duplication. | `ast` walk of `ImportFrom` with module `agent_workflows.oc_runipd`: 4+21+12+1+1+1 = 40 names |
| F-5 | The 34 symbols cluster into FIVE clean seams with no cross-seam call edges except into already-moved ones: git (6, 53L), json/state (7, 47L), lane (8, 242L), plan/selector (7, 170L), run/misc (6, 39L). This is what makes one child viable instead of five. | seam grouping over the inventory, every symbol assigned, none unassigned |
| F-6 | CONTENTION: six of seven `lanectn` plans declare both runner modules, and the lane seam is this plan's largest. They name NONE of the 34 symbols, so the conflict is textual, not logical. | `rg` per symbol across the 7 `lanectn` plans: zero mentions |
| F-7 | `_run_git` is also defined in `layout_inventory.py` and `layout_migration.py`, but with DIFFERENT bodies. Name collision, not a re-fork; unifying them is out of scope and would be a behavior change. | E-01's class (d) sweep distinguishes match from same-name |

## Proposed changes (ordered, validatable)

1. Create `runner_common.py` with its admission rule stated (E-01).
2. Build the fingerprint harness and decide the injection mechanism for the four outside-dependencies (E-02).
3. Unify `DriverError` alone, and settle the translation wrapper's fate (E-03).
4. Move run/misc, git, json/state, lane, plan/selector, in that order (E-04 to E-08).
5. Extend child 01's symmetric guard to all 34 and sabotage-verify it (E-08).

## Deferred / out of scope (with reason)

- Every class (c) DIVERGED symbol (52 of them): gated behind `lanectn` landing AND the orchestrator's E-02 characterization baseline. This plan touches them only by INJECTION at a call boundary, never by moving or editing them.
- The class (d) re-forks: child 01 owns them, and this plan depends on it (`Item-Dependencies: executed:2r306y`) so the guard exists before this plan extends it.
- Re-homing the 40 names agy imports from oc (F-4). A real layering defect, but a design question of its own. **FILED AS BACKLOG `cnwy8g` (`runnerlayer-01`) so it cannot leave the live tree when this plan reaches `executed/`.** That item carries the full 40-name list, the three observable consequences, the constraints any fix inherits (classify before moving; keep the `oc -> agy` direction at zero imports; preserve the `as <same-name>` re-export form), and its sequencing: AFTER this plan, because this plan creates the module the work moves into.
- Absorbing `plan_readiness.py`. The orchestrator's OQ-02 resolved this from evidence: DESIGNATE, do not absorb, because `status_set.py` and `ipd_schema.py` import it and they are not runners.
- Removing the `DriverError` translation wrapper IF removal changes what agy's `main` catches (E-03). Behavior preservation outranks tidiness.
- The 47 opencode-only and 3 antigravity-only host-specific symbols: correctly host-specific, nothing to share.

## Scope check

- Over-scope: none. Every edit moves a proven-identical definition or adds a test that proves the move was faithful.
- Under-scope: this removes ~551 duplicated lines but fixes only ONE behavioral defect (`DriverError`, F-3). The 52 diverged symbols, which are where the real behavioral divergence lives, are deliberately untouched. Anyone expecting this plan to make the runners agree should read the orchestrator's sequencing gate instead.

## Required tests / validation

- `tests/test_runner_common.py`: for each of the 34, an AST-fingerprint match against the pre-move capture AND an `assertIs` proving both runners resolve to the same object.
- The extended symmetric guard from child 01, sabotage-verified in BOTH runner directions.
- `DriverError` specifically: one definition package-wide, identity across both runners, `StallTimeout` subclassing intact, and agy's `main` still catching a preflight refusal with its existing message.
- `print_status` byte-identical output for both hosts, shown side by side.
- Both driver suites green: `tests/test_oc_runipd.py` (93 at authoring) and `tests/test_agy_runipd_cli.py` (20).
- Full suite bare (`python3 -m pytest`), compared against YOUR OWN pre-change measurement. Baseline at authoring HEAD `c8bb11ae`: `4092 passed, 3 skipped, 4 xfailed`. No `-n0`, no second `-q`, no `-p no:randomly`.
- A cycle check: `runner_common` imports neither runner.

## Spec / documentation sync

- N/A for public contracts: every moved name stays reachable at its existing runner attribute path, so no documented interface changes. If `AGENTS.md` or a module map enumerates the package's modules, add `runner_common.py` there.

## Open questions

### OQ-01: Is the module name `runner_common.py` right, given `runner_shutdown.py` and `runner_stop.py` already exist?

- Blocking: no
- Status: open
- Owner: maintainer (cosmetic; executor may proceed with the stated default)
- Resolution or deferral rationale: NOT BLOCKING because the name is a rename away and nothing external depends on it. Default `runner_common.py`, chosen for consistency with the existing `runner_*` prefix that `runner_shutdown.py` and `runner_stop.py` established. The orchestrator's OQ-02 said "a NEW dedicated module following `host_runner.py`'s conventions", which fixes the CONVENTIONS but not the name. If you prefer something more descriptive (for example `runner_shared.py` or `driver_common.py`), say so before E-01; after E-08 a rename touches both runners again.

### OQ-02: Injection or a registration seam for the four outside-dependencies?

- Blocking: no
- Status: open
- Owner: executor (E-02), with a stated default
- Resolution or deferral rationale: NOT BLOCKING, but it MUST be decided once in E-02 and applied uniformly rather than per-symbol, or the shared module acquires four different coupling styles. Default: plain PARAMETER injection, because it is explicit at every call site, needs no module-level mutable state, and cannot produce an import-order bug. A registration seam is only preferable if parameter threading proves to change many call sites, in which case record the measurement that justified it. Whichever is chosen, the invariant is absolute: `runner_common` must never import a DIVERGED symbol from a runner.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new module's docstring showing it states its own admission rule (identical-only, never imports a runner). Paste `python3 -c "import agent_workflows.runner_common"` succeeding, and paste a check proving it imports neither runner (for example an AST scan of its `ImportFrom` targets). State which OQ-01 name was used.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the fingerprint fixture (or its generation command and a sample), showing all 34 symbols captured with the HEAD they were captured at. Paste the injection mechanism decision (OQ-02) with one worked example. THEN prove the harness is load-bearing, not decorative: deliberately alter one moved body, paste the resulting FAILURE, and revert. A harness that passes both before and after such an alteration is not a harness and this item FAILS.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a package-wide check showing exactly ONE `DriverError` definition. Paste `oc_runipd.DriverError is agy_runipd.DriverError` -> True and `issubclass(agy_runipd.StallTimeout, runner_common.DriverError)` -> True. Paste a DEMONSTRATION that agy's `main` still catches a dependency-preflight refusal and still prints its `runagy: ...` message (run it; do not reason about it). State plainly whether the translation wrapper at `agy_runipd.py:87-93` was kept or removed, and if removed, paste the evidence that removal changed nothing about what `main` catches.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for each of the five symbols, paste the fingerprint match and the `assertIs` result. Paste `rg -n "^def utc_now|^def should_color|^def new_run_id|^def state_root|^def resolve_run_dir" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning NOTHING for both runners.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: fingerprint match and `assertIs` per symbol for all six. Paste the `run_checked` call sites showing `pinned_child_env` is INJECTED, plus proof `runner_common` does not import it from a runner. Paste the `_run_git` collision check showing `layout_inventory.py`/`layout_migration.py` were left alone and their bodies genuinely differ.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: fingerprint match and `assertIs` for all eight. Paste proof `write_report` is injected into `save_state` rather than imported. For `print_status`, paste the rendered output for BOTH hosts before and after, side by side, showing byte-identical results, and name the mechanism by which the host string is supplied.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: fingerprint match and `assertIs` for all eight lane symbols, and both runners showing no local definition. STATE whether `lanectn` landed while this was in flight; if it did, paste the conflict resolution and confirm no `lanectn` change was reverted or absorbed. Paste `git log --oneline` for both runner files covering the execution window, so a co-worker's commit is visible rather than assumed absent.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: fingerprint match and `assertIs` for all seven. Paste the extended guard table showing all 39 names (child 01's five plus these 34) and TWO sabotage failures, one per runner. Then the closing measurements: both driver suites with counts, the full bare suite compared against your own pre-change measurement, and a package-wide AST check that each of the 34 has exactly ONE definition.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 8 E-leaves across 2 task groups, one concern throughout (move the proven-identical symbols into one module without changing behavior). It is at the upper end deliberately: the seams are sequential edits to the SAME two files, so splitting them into separate plans would guarantee the merge conflicts the orchestrator warns about, while each E-item remains one seam with its own V-item. If a reviewer judges E-07 (the 242-line lane seam) too large, split THAT item, not the plan.

Open questions: OQ-01 (module name) and OQ-02 (injection mechanism) are both non-blocking with stated defaults. No blocking question remains, so this plan is executable once approved AND once child 01 (`2r306y`) has executed.

This plan is `to-review` and requires explicit human approval before execution. It also has a hard prerequisite: `Item-Dependencies: executed:2r306y`, because it EXTENDS the symmetric guard child 01 installs.

Scope fence: touch ONLY `agent_workflows/runner_common.py` (new), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `tests/test_runner_common.py` (new), and `tests/test_runner_refork_guard.py` (child 01's, extended). Do NOT edit any class (c) DIVERGED symbol's body, in either runner, for any reason: touching one is this plan's stop condition, not a judgment call. Do NOT change `render_stream.py` or `selectors.py`. Do NOT re-home the 40 oc-to-agy imports. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or the orchestrator.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. A "pure move" claim rests on the fingerprint fixture and the identity assertions, NOT on a grep and NOT on the suites being green: the suites were green while `DriverError` was two different classes. If any body changed, say so and treat it as a finding, because a changed body means this was not a move.

Execution contract: RE-READ both runner modules immediately before each seam and locate every symbol BY NAME, never by the line numbers in this plan. These are the highest-contention files in the repo: 21 unexecuted plans declare them, another session committed `render_stream.py` in `a396cb1b` during authoring, and six `lanectn` plans will edit them. Commit per SEAM, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption. If a co-worker's in-flight change to a runner cannot be safely combined with a seam, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
