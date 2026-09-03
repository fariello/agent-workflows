# IPD: extract the 34 common symbols into a shared runner library, pure move

- Date: 2026-09-03
- Kind: child
- Concern: 34 top-level symbols are defined TWICE, once per runner, with AST-identical bodies. Because they are identical there is no behavioral disagreement TODAY, which is exactly why they are the dangerous class: nothing signals when one copy is edited and the other is not, and that is how the 52 currently-diverged symbols got that way. Measured at HEAD `c8bb11ae` by research `tvnq50` (E-01 of orchestrator `5e4sb6`): 33 are AST-identical, `print_status` is identical after host-token normalization, and together they are 551 lines of the runners' definition mass. The concrete cost of leaving them duplicated is already visible: `DriverError` is defined in BOTH runners (`oc_runipd.py:202`, `agy_runipd.py:379`) as two DISTINCT classes, and `agy_runipd.py:87-93` records a hand-written wrapper that exists solely to translate one into the other, because `enforce_dependency_preflight` raises oc's class and agy's `main` cannot catch it.
- Scope: Create ONE shared runner library and move all 34 class (a) symbols into it, then have both runners import them. PURE MOVE: no body may change, and every move is verified by an AST-identity assertion against the pre-move definition plus an object-identity assertion that both runners resolve to the same object. Excludes reconciling any diverged symbol (deferred behind `lanectn` and E-02's characterization baseline), excludes the class (d) re-forks (child 01 owns them), excludes re-homing the 40 names `agy_runipd` already imports from `oc_runipd`, and excludes any behavior change whatsoever, including the `DriverError` wrapper's REMOVAL if removing it would alter what `main` catches.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:2r306y
- Status: reviewed
- Readiness: go-pending-approval
- Set: rununify
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 818uru
- Blocks-Release: next

## Workflow history

- 2026-09-03 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-301..PR-306; GO - PENDING HUMAN APPROVAL. Verified at HEAD `25d3f0b0`, tree clean, plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` and again at `--phase review-finalize`. THE INVENTORY RE-MEASURED INDEPENDENTLY AND THE PLAN'S NUMBERS ARE RIGHT: 88 symbols are defined in both runners, 35 AST-identical and 53 diverged; subtracting the two `2r306y` owns (`_read_id`, `_read_status`) leaves exactly the 34 this plan claims, and `StallTimeout` correctly sits in the diverged set (its docstrings differ). F-3's `DriverError` claim is TRUE and live: `agy_runipd.DriverError is oc_runipd.DriverError` returns False at this HEAD and the translation wrapper at `agy_runipd.py:1388-1411` exists exactly as described. F-4's 40-name count is exact (via nested `ImportFrom`; a body-level scan alone shows 37). THE DOMINANT FINDING (PR-301, BLOCKER, fixed by maintainer ruling): the plan's own two central mechanisms CONTRADICTED each other. E-02 requires every moved body's post-move AST fingerprint to EQUAL its pre-move capture, and simultaneously requires four symbols to take a new injected parameter - which changes their signature and body, so the fingerprint CANNOT match and the plan's load-bearing proof would fail on precisely the four riskiest symbols. Measured second cost: uniform parameter injection rewrites roughly 86 call sites (`save_state` 33 in oc + 31 in agy; `run_checked` 13 + 9) across the two highest-contention files in the repo, which 7 `reviewed` `lanectn` plans also edit. MAINTAINER RULED the thin runner-local wrapper: `runner_shared` owns the parameterized function, each runner keeps a one-line wrapper at the original name and signature binding its own dependency. That honors both original prohibitions (no registration seam, no module-level mutable state), leaves all ~86 call sites untouched, and keeps the fingerprint proof honest for the 30 clean symbols while the 4 wrapped ones are proven by behavior. E-02, E-05, E-06, E-08 and V-02 rewritten accordingly. Also FIXED: (PR-302, HIGH) the plan named four outside-dependencies; measurement finds a FIFTH problem in the same class - `discover_plans` also closes over `PlanRecord`, and the two runners' `PlanRecord` are DIFFERENT NamedTuples (oc has an extra `kind` field), so a moved `discover_plans` returning oc's shape would silently change agy's records. (PR-303, MEDIUM) E-06 lists `state_root` a second time ("if not already moved") after E-04 already moved it, and lists 7 symbols while its own count says 8; ambiguity in a move manifest is how a symbol gets moved twice or not at all. (PR-304, MEDIUM) the `runner_shared` docstring rule "holds only symbols PROVEN identical" is contradicted by the plan's own design the moment a parameterized wrapper target lands there; wording corrected so the module's stated contract matches what it will actually contain. (PR-305, LOW) E-03's `StallTimeout` check is understated: agy's `StallTimeout` subclasses agy's `DriverError`, so unifying the base class RE-PARENTS a live exception used by the stall watchdog. (PR-306, LOW) F-1's "551 oc lines" is not reproducible from the stated method without also stating it counts oc-side definition lines only. Three decisions recorded in the typed review record (D-1, D-2, D-3; all reversible).
- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored FROM E-01's inventory (research `tvnq50`), per orchestrator `5e4sb6`'s SECOND GATE. THREE CORRECTIONS to the orchestrator's child table, all from measurement rather than preference. (1) The count is **34, not 35** (33 AST-identical plus `print_status`, identical only after host-token normalization, which the table's "byte-identical" framing would have wrongly excluded). (2) The table calls this a "pure move ... verified by an identity assertion", which holds, but a naive lift FAILS: four symbols in the set call symbols OUTSIDE it (`run_checked` -> `pinned_child_env`, `discover_plans` -> `parse_plan_file`, `save_state` -> `write_report`, `validate_manifest` -> `parse_dependency_token`), and two of those four are class (c) DIVERGED, which this plan may not touch. E-02 resolves that by dependency injection rather than by dragging diverged code along. (3) `DriverError` is a LATENT BUG, not merely a duplicate: two distinct classes with a hand-written translation wrapper already documented at `agy_runipd.py:87-93`. Unifying it is the highest-value single symbol here and is sequenced first. Authored review-ready, not draft.
- 2026-09-03 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give each of the 34 identical symbols exactly ONE definition, in one shared module both runners import, without changing a single line of any body and without touching a diverged symbol.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the module, and the identity harness that makes "pure move" falsifiable

- [ ] E-01 Create `agent_workflows/runner_shared.py`, following `host_runner.py`'s conventions (module docstring stating what it owns and why, section banner comments, no import of either runner so no cycle can form). It starts EMPTY of moved logic; this item establishes the module and its contract only. Record in the docstring the constraint that decides every later question here: this module holds only symbols whose bodies were PROVEN identical across both runners, it may never import either runner, and a symbol whose bodies differ belongs in a later child, not here.
  STATE THE ADMISSION RULE PRECISELY (corrected at review, PR-304), because the obvious wording is false the moment E-02's wrapper mechanism lands: a moved function may take an outside dependency as a PARAMETER, so the rule is not "identical bodies, verbatim" but "identical bodies MODULO an explicitly injected dependency, with the injection recorded". Write it that way. A docstring asserting a stricter rule than the module actually keeps is worse than none, because the next reader will either believe it and be misled or notice the contradiction and distrust the whole contract. Per OQ-02 of the orchestrator, this module is the shared runner library and `plan_readiness.py` is DESIGNATED a peer it may import, NOT absorbed (its consumers include `status_set.py` and `ipd_schema.py`, which are not runners).
  - Depends on: none
  - Expected outcome: a new module that imports cleanly, defines no runner logic yet, and states its own admission rule; `python3 -c "import agent_workflows.runner_shared"` succeeds and a cycle check shows it imports neither runner.
  - Execution state: pending

- [ ] E-02 Build the MOVE HARNESS before moving anything, because "pure move" is a claim that must be mechanically checkable rather than eyeballed 34 times. Capture the pre-move AST fingerprint of all 34 symbols from BOTH runners (`ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)`, the same method E-01 of the orchestrator used), store it as a fixture, and assert after each move that the shared definition's fingerprint EQUALS the captured one.
  THE FIVE OUTSIDE-DEPENDENCIES, and the mechanism REVISED AT REVIEW. A naive lift fails because some moved symbols call symbols that stay behind (measured): `run_checked` -> `pinned_child_env` (oc-only, host-specific), `discover_plans` -> `parse_plan_file` (class (c) DIVERGED) AND `PlanRecord` (found at review, PR-302: the two runners' `PlanRecord` are DIFFERENT NamedTuples, oc's carrying an extra `kind` field, so a moved `discover_plans` would silently return oc's shape to agy), `save_state` -> `write_report` (class (c) DIVERGED), `validate_manifest` -> `parse_dependency_token` (oc-only, host-specific). A moved symbol must NOT import a diverged symbol from a runner, because that both re-creates the coupling and drags undecided behavior into shared code.
  MECHANISM: THIN RUNNER-LOCAL WRAPPER (maintainer ruling 2026-09-03 at review, superseding the earlier uniform-parameter-injection ruling of the same day). `runner_shared` owns the real function, taking each outside dependency as an explicit PARAMETER; each runner keeps a ONE-LINE wrapper at the ORIGINAL name and the ORIGINAL signature that calls it, binding its own dependency. This still honors both original prohibitions, which is why it is a refinement and not a reversal: the dependency is passed explicitly at a single visible site per runner, there is NO registration seam, and there is NO module-level mutable state.
  WHY THE UNIFORM-INJECTION FORM WAS REVISED, recorded so it is not re-proposed: (1) it CONTRADICTED THIS ITEM'S OWN PROOF - a function whose signature and body just gained a parameter cannot have an unchanged AST fingerprint, so the plan's load-bearing "pure move" evidence would have failed on exactly the four riskiest symbols; (2) MEASURED COST - threading a parameter through every call rewrites roughly 86 call sites (`save_state` is called 33 times in oc and 31 in agy; `run_checked` 13 and 9), all inside the two highest-contention files in the repo, which seven `reviewed` `lanectn` plans also edit, so it would manufacture the merge conflicts E-07 already warns about.
  THE FINGERPRINT RULE THEREFORE SPLITS, and say so plainly rather than quietly exempting things: the 30 symbols with no outside dependency are proven by STRICT fingerprint equality; the wrapped ones are proven by (a) fingerprint equality of the shared body MODULO the added parameter, stated explicitly and shown, plus (b) a BEHAVIOR test per symbol through each runner's wrapper. A wrapped symbol claimed as a byte-identical move would be a false claim.
  - Depends on: E-01
  - Expected outcome: a fixture of 34 pre-move fingerprints captured at a stated HEAD; the wrapper mechanism documented with one worked example showing the shared function, the oc wrapper and the agy wrapper; a test that FAILS if any of the 30 clean bodies' fingerprints differ from capture; and an explicit list of exactly which symbols are wrapped and why, so the exemption is enumerated rather than implicit.
  - Execution state: pending

### Task group 2: move by seam, smallest and safest first

Move order is deliberate: each seam is independently verifiable, and the two seams with outside-dependencies come last so the harness is already proven on clean cases.

- [ ] E-03 Move the `DriverError` unification FIRST, alone, because it is the one symbol here that is a latent BUG rather than only a duplicate. `oc_runipd.py:202` and `agy_runipd.py:379` define two DISTINCT classes (re-verified at review: `agy_runipd.DriverError is oc_runipd.DriverError` -> False at this HEAD); the wrapper documented at `agy_runipd.py:87-93` and implemented at `:1388-1411` exists only to translate oc's class into agy's so agy's `main` can catch it. Move the single definition to `runner_shared`, have both runners import it, and then check whether that wrapper is still needed. DO NOT DELETE THE WRAPPER AS A MATTER OF COURSE: if removing it changes what `agy_runipd.main` catches or what message it prints, it stays and this plan records why.
  RE-PARENTING A LIVE EXCEPTION IS THE REAL RISK HERE, and it is understated as "verify the subclass relationship" (PR-305). `agy_runipd.StallTimeout` SUBCLASSES agy's `DriverError` (`agy_runipd.py:383`) and is what the stall watchdog raises, so this move CHANGES StallTimeout's base class from agy's local class to the shared one. Every `except DriverError` in agy (measured: raises and handlers throughout, including `:479`, `:550`, `:1288`, `:1338`) must still catch a `StallTimeout`, and the WATCHDOG PATH specifically must be exercised rather than reasoned about, since a stall that stops being caught turns a clean timeout into an unhandled traceback in an unattended overnight run. Note `StallTimeout` itself is class (c) DIVERGED (the two docstrings differ), so this item may re-parent it but must NOT edit its body.
  - Depends on: E-02
  - Expected outcome: exactly one `DriverError` in the package; `oc_runipd.DriverError is agy_runipd.DriverError` is True; `issubclass(agy_runipd.StallTimeout, runner_shared.DriverError)` is True; agy's `main` still catches a preflight refusal and still prints its `runagy: ...` message, demonstrated rather than asserted; an explicit statement of whether the wrapper was kept or removed, with the reason.
  - Execution state: pending

- [ ] E-04 Move the RUN/MISC seam (5 remaining symbols, 37 lines): `utc_now`, `should_color`, `new_run_id`, `state_root`, `resolve_run_dir`. `print_status` is deliberately NOT in this item: it is the one host-naming-only symbol, so it needs the normalization decision E-06 makes.
  - Depends on: E-03
  - Expected outcome: five symbols defined once; both runners' attributes are the same objects by `assertIs`; fingerprints match the pre-move capture.
  - Execution state: pending

- [ ] E-05 Move the GIT seam (6 symbols, 53 lines): `_run_git`, `git_head`, `git_branch`, `git_status`, `git_common_dir`, `run_checked`. `run_checked` carries the `pinned_child_env` outside-dependency, so apply E-02's WRAPPER mechanism here and treat this as its first real exercise: `runner_shared.run_checked` takes the env-builder as a parameter, and each runner keeps a one-line `run_checked` wrapper binding its own, so the 13 oc and 9 agy call sites are NOT rewritten. Note `_run_git` is ALSO defined in `layout_inventory.py` and `layout_migration.py` but those are NAME COLLISIONS with different bodies, not re-forks (re-verified at review: all three signatures and bodies differ; the runners' returns a `(rc, out, err)` tuple while both layout copies return a `CompletedProcess`) - do not "unify" them.
  - Depends on: E-04
  - Expected outcome: six symbols defined once; `run_checked`'s dependency bound in a per-runner wrapper rather than imported from a runner into shared code; every existing `run_checked` call site unchanged; and the collision note verified rather than assumed.
  - Execution state: pending

- [ ] E-06 Move the JSON/STATE seam. EXACT MANIFEST, 7 symbols (corrected at review, PR-303 - the earlier wording listed `state_root` a second time "if not already moved" although E-04 already moves it, and said 7 while counting 8; an ambiguous move manifest is how a symbol gets moved twice or skipped): `load_json`, `atomic_write_json`, `append_jsonl`, `sha256_file`, `load_state`, `save_state`, `print_status`. `state_root` is NOT in this item; E-04 owns it. TWO SPECIAL CASES: `save_state` calls `write_report`, a class (c) DIVERGED symbol, so it takes it as a parameter with a per-runner wrapper (this is the highest-count wrapper in the plan, protecting 33 oc and 31 agy call sites); and `print_status` differs between runners ONLY by host tokens (verified at review: the two bodies are identical except `driver_label='opencode'` versus `'antigravity'`), so moving it requires deciding how the host string is supplied (a parameter, almost certainly) and PROVING the rendered output is byte-identical to each runner's current output for both hosts.
  - Depends on: E-05
  - Expected outcome: seven symbols defined once; `write_report` bound in per-runner wrappers with all 64 `save_state` call sites unchanged; `print_status` renders byte-identically to today for BOTH hosts, shown side by side.
  - Execution state: pending

- [ ] E-07 Move the LANE seam (8 symbols, 242 lines, the largest): `_lane_records_from_state`, `describe_lane`, `format_lane_report`, `print_lane_interrupt_report`, `build_recovery_lane_notice`, `allocate_isolation_worktree`, `teardown_isolation_worktree`, `disable_lane_prompt`. CONTENTION WARNING, and it is the reason this seam is LAST: six of the seven `lanectn` plans declare both runner modules in their Scope-Paths. They name none of these eight symbols (verified: zero mentions across all seven plans), so there is no logical conflict, but there is a real TEXTUAL conflict risk if `lanectn` lands while this is in flight. Re-read both runners immediately before editing and stop rather than overwrite.
  - Depends on: E-06
  - Expected outcome: eight symbols defined once, fingerprints matching, and an explicit statement of whether `lanectn` landed in the interim and how conflicts were handled.
  - Execution state: pending

- [ ] E-08 Move the PLAN/SELECTOR seam (7 symbols, 170 lines): `discover_plans`, `resolve_plan_path`, `plan_bucket`, `_read_set`, `_read_order`, `describe_unresolved_plan_selector`, `validate_manifest`. `discover_plans` depends on `parse_plan_file` (DIVERGED) and `validate_manifest` on `parse_dependency_token` (oc-only), so both take per-runner wrappers per E-02.
  `discover_plans` ALSO CLOSES OVER `PlanRecord`, AND THE TWO RUNNERS' `PlanRecord` ARE DIFFERENT TYPES (found at review, PR-302; the plan's four-dependency list missed it). Measured: oc's `PlanRecord` has fields `(id6, setid, status, order, path, rel_path, dependencies, kind, dependency_error, from_backlog)` while agy's LACKS `kind` (`oc_runipd.py` vs `agy_runipd.py:1414`). So a shared `discover_plans` that constructs oc's `PlanRecord` would silently hand agy records carrying a field its own code never expects, and one that constructs agy's would DROP `kind` - which oc's `action_for` (`oc_runipd.py:2749`) reads to decide whether a plan is an orchestrator. Either way the failure is silent and type-shaped, not a crash. Treat `PlanRecord` as a dependency of the same kind: the record CONSTRUCTOR is supplied per runner, exactly like `parse_plan_file`. Do NOT unify the two `PlanRecord` definitions here; that is a class (c) reconciliation this plan may not perform.
  Then extend child 01's symmetric re-fork guard to cover all 34 moved symbols, so a future re-fork of any of them fails a test in EITHER runner, and sabotage-verify that extension in both directions.
  - Depends on: E-07
  - Expected outcome: seven symbols defined once; `PlanRecord`'s constructor supplied per runner with proof that each runner still gets its OWN record type (an `is` check per runner, plus evidence oc's `kind` field survives); the guard's table now covers all 34 plus child 01's five; sabotage in each runner fails the guard.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `host_runner.py` is the precedent for a shared runner-adjacent module: a docstring stating what it owns and its security/design posture, banner comments per section, and no import of a caller. Copy the conventions, not the contents.
- `agy_runipd.py:69-146` already imports 40 names FROM `oc_runipd`, with a comment at `:84-96` explaining why there is no cycle and why the `as <same-name>` re-export form is load-bearing (ruff removed 6 of them on a first attempt and a symmetry test caught it). Any import this plan adds must survive the same autoformatter pressure.
- The runners' anti-re-fork guard is being made symmetric by child 01; this plan EXTENDS that table rather than writing a second guard.
- The orchestrator's hard constraints inherited here: a child may not change behavior, must land in BOTH runners or neither, and may not exceed one cohesive seam.

## Findings

| # | Finding | Evidence |
|---|---------|----------|
| F-1 | The count is **34**, not the orchestrator's 35: 33 AST-identical plus `print_status`, identical only after host-token normalization. 551 oc-side definition lines (the qualifier added at review, PR-306: the bare number is not reproducible without stating it counts oc's copies only, since the two runners' copies differ in length). RE-VERIFIED AT REVIEW: 88 symbols are defined in both runners, 35 AST-identical and 53 diverged; minus the two child 01 owns (`_read_id`, `_read_status`) that is exactly 34. | research `tvnq50`, measured at HEAD `769989ce`, re-confirmed at `c8bb11ae`, and re-measured independently at review at `25d3f0b0` |
| F-2 | A NAIVE LIFT FAILS. Moved symbols call symbols outside the set: `run_checked` -> `pinned_child_env` (oc-only), `discover_plans` -> `parse_plan_file` (DIVERGED) **and `PlanRecord` (see F-8)**, `save_state` -> `write_report` (DIVERGED), `validate_manifest` -> `parse_dependency_token` (oc-only). Importing a DIVERGED symbol into shared code would drag undecided behavior along and re-create the coupling. | AST call-graph over the 34 symbols against the runners' top-level name set, re-run at review over free variables rather than calls alone, which is what surfaced `PlanRecord` |
| F-3 | `DriverError` is a LATENT BUG, not just a duplicate: two DISTINCT classes, with a hand-written translation wrapper already documented in-tree. This is the strongest single argument for the whole Set. | `oc_runipd.py:202`, `agy_runipd.py:379`, and the comment at `agy_runipd.py:87-93` |
| F-4 | `agy_runipd` already imports 40 names from `oc_runipd`, so the runners are NOT peers today: agy depends on oc. A shared module is therefore a correction of layering, not merely de-duplication. | `ast` walk of `ImportFrom` with module `agent_workflows.oc_runipd`: 4+21+12+1+1+1 = 40 names |
| F-5 | The 34 symbols cluster into FIVE clean seams with no cross-seam call edges except into already-moved ones: git (6, 53L), json/state (7, 47L), lane (8, 242L), plan/selector (7, 170L), run/misc (6, 39L). This is what makes one child viable instead of five. | seam grouping over the inventory, every symbol assigned, none unassigned |
| F-6 | CONTENTION: six of seven `lanectn` plans declare both runner modules, and the lane seam is this plan's largest. They name NONE of the 34 symbols, so the conflict is textual, not logical. | `rg` per symbol across the 7 `lanectn` plans: zero mentions |
| F-7 | `_run_git` is also defined in `layout_inventory.py` and `layout_migration.py`, but with DIFFERENT bodies. Name collision, not a re-fork; unifying them is out of scope and would be a behavior change. RE-VERIFIED AT REVIEW: the runners' version returns a `(returncode, stdout, stderr)` tuple and runs with `cwd=repo`, while both layout versions return a `CompletedProcess` and use `git -C <repo>`. Genuinely three different functions. | E-01's class (d) sweep distinguishes match from same-name; `layout_inventory.py:50`, `layout_migration.py:180`, `oc_runipd.py`'s `_run_git` |
| F-8 | **FOUND AT REVIEW (PR-302). A FIFTH outside-dependency the plan's list missed, and the most dangerous kind because it fails SILENTLY and type-shaped rather than by crashing.** `discover_plans` closes over `PlanRecord`, and the two runners' `PlanRecord` are DIFFERENT NamedTuples: oc's carries a `kind` field that agy's lacks. A shared `discover_plans` therefore cannot construct "the" record type - build oc's and agy receives a field its code never expects; build agy's and oc LOSES `kind`, which `action_for` reads to detect an orchestrator. Handled by supplying the constructor per runner, exactly like the other wrapped dependencies. | oc `PlanRecord` fields `(id6, setid, status, order, path, rel_path, dependencies, kind, dependency_error, from_backlog)` vs agy `PlanRecord` at `agy_runipd.py:1414` with no `kind`; consumer `action_for` at `oc_runipd.py:2749` |
| F-9 | **FOUND AT REVIEW (PR-301). The plan's two central mechanisms contradicted each other, which is why the injection mechanism was re-ruled.** E-02 demanded post-move AST fingerprint EQUALITY with the pre-move capture, while simultaneously requiring four symbols to gain an injected parameter - which changes signature and body, so the fingerprint cannot match. The plan's load-bearing proof would have failed on precisely its four riskiest symbols. Second measured cost: uniform injection rewrites ~86 call sites in the two highest-contention files. Resolved by the thin-wrapper ruling, which preserves the proof for the 30 clean symbols and leaves every call site untouched. | `save_state` called 33x in oc and 31x in agy; `run_checked` 13x and 9x; E-02's own fingerprint requirement versus its own injection requirement |

## Proposed changes (ordered, validatable)

1. Create `runner_shared.py` with its admission rule stated precisely, including the injected-dependency case (E-01).
2. Build the fingerprint harness and implement the thin-wrapper mechanism for the five outside-dependencies (E-02).
3. Unify `DriverError` alone, and settle the translation wrapper's fate (E-03).
4. Move run/misc, git, json/state, lane, plan/selector, in that order (E-04 to E-08).
5. Extend child 01's symmetric guard to all 34 and sabotage-verify it (E-08).

## Deferred / out of scope (with reason)

- Every class (c) DIVERGED symbol (53 by review's independent re-measurement, 52 in the earlier count; the delta is a counting boundary, not a new divergence): gated behind `lanectn` landing AND the orchestrator's E-02 characterization baseline. This plan touches them only by BINDING them in a per-runner wrapper at a call boundary, never by moving or editing them. `StallTimeout` is in this class and is RE-PARENTED by E-03 without its body being edited; that is the one permitted contact and it is why V-03 demands the watchdog path be exercised.
- Unifying the two `PlanRecord` definitions (F-8). A real divergence, but it is a class (c) reconciliation with a live consumer (`kind` feeds orchestrator detection), so this plan supplies the constructor per runner and changes neither definition.
- The class (d) re-forks: child 01 owns them, and this plan depends on it (`Item-Dependencies: executed:2r306y`) so the guard exists before this plan extends it.
- Re-homing the 40 names agy imports from oc (F-4). A real layering defect, but a design question of its own. **FILED AS BACKLOG `cnwy8g` (`runnerlayer-01`) so it cannot leave the live tree when this plan reaches `executed/`.** That item carries the full 40-name list, the three observable consequences, the constraints any fix inherits (classify before moving; keep the `oc -> agy` direction at zero imports; preserve the `as <same-name>` re-export form), and its sequencing: AFTER this plan, because this plan creates the module the work moves into.
- Absorbing `plan_readiness.py`. The orchestrator's OQ-02 resolved this from evidence: DESIGNATE, do not absorb, because `status_set.py` and `ipd_schema.py` import it and they are not runners.
- Removing the `DriverError` translation wrapper IF removal changes what agy's `main` catches (E-03). Behavior preservation outranks tidiness.
- The 47 opencode-only and 3 antigravity-only host-specific symbols: correctly host-specific, nothing to share.

## Scope check

- Over-scope: none. Every edit moves a proven-identical definition or adds a test that proves the move was faithful.
- Under-scope: this removes ~551 duplicated lines but fixes only ONE behavioral defect (`DriverError`, F-3). The 52 diverged symbols, which are where the real behavioral divergence lives, are deliberately untouched. Anyone expecting this plan to make the runners agree should read the orchestrator's sequencing gate instead.

## Required tests / validation

- `tests/test_runner_shared.py`: for each of the 34, an `assertIs` proving both runners resolve to the same object, plus an AST-fingerprint match against the pre-move capture for the ~30 with no outside dependency. For the five WRAPPED symbols the fingerprint is asserted modulo the added parameter and is backed by a behavior test through each runner's wrapper; that exemption must be enumerated in the test file, never left implicit.
- For each wrapped symbol, a before/after CALL-SITE COUNT in both runners proving no call site was rewritten (the reason the wrapper form was chosen over uniform injection).
- The extended symmetric guard from child 01, sabotage-verified in BOTH runner directions.
- `DriverError` specifically: one definition package-wide, identity across both runners, `StallTimeout` subclassing intact, and agy's `main` still catching a preflight refusal with its existing message.
- `print_status` byte-identical output for both hosts, shown side by side.
- Both driver suites green: `tests/test_oc_runipd.py` (93 at authoring) and `tests/test_agy_runipd_cli.py` (20).
- Full suite bare (`python3 -m pytest`), compared against YOUR OWN pre-change measurement. Baseline at authoring HEAD `c8bb11ae`: `4092 passed, 3 skipped, 4 xfailed`. No `-n0`, no second `-q`, no `-p no:randomly`.
- A cycle check: `runner_shared` imports neither runner.

## Spec / documentation sync

- N/A for public contracts: every moved name stays reachable at its existing runner attribute path, so no documented interface changes. If `AGENTS.md` or a module map enumerates the package's modules, add `runner_shared.py` there.

## Open questions

### OQ-01: Is the module name `runner_shared.py` right, given `runner_shutdown.py` and `runner_stop.py` already exist?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03: use `runner_shared.py`. It reads as the module shared by the host runners, whereas `runner_common.py` can be misread as a common or canonical runner. `runner_shared_lib.py` was declined as redundant because a Python module is already a library. The name remains internal and introduces no public contract.

### OQ-02: Injection or a registration seam for the five outside-dependencies?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-03, then REFINED BY THE MAINTAINER 2026-09-03 at review. A registration seam was and stays DECLINED: its process-global state would create registration-order and test-isolation risks. Module-level mutable state stays FORBIDDEN. `runner_shared` must never import a DIVERGED symbol from a runner. What CHANGED is the shape of the injection: the first ruling said parameter injection applied uniformly at every call site; review measured that this (a) contradicts E-02's own fingerprint proof, since a body that gains a parameter cannot match its pre-move capture, and (b) rewrites roughly 86 call sites in the two highest-contention files in the repo, which seven `reviewed` `lanectn` plans also edit. The maintainer therefore ruled the THIN RUNNER-LOCAL WRAPPER: `runner_shared` owns the parameterized function, each runner keeps a one-line wrapper at the original name and signature binding its own dependency. The dependency is still passed EXPLICITLY (one visible site per runner), there is still no seam and no mutable state, the call sites are untouched, and the fingerprint proof survives for the 30 symbols that have no outside dependency. Review also found a FIFTH dependency the original list missed, `PlanRecord` (F-8), handled by the same mechanism.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new module's docstring showing it states its own admission rule (identical-only, never imports a runner). Paste `python3 -c "import agent_workflows.runner_shared"` succeeding, and paste a check proving it imports neither runner (for example an AST scan of its `ImportFrom` targets). State which OQ-01 name was used.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the fingerprint fixture (or its generation command and a sample), showing all 34 symbols captured with the HEAD they were captured at. Paste the WRAPPER mechanism with one worked example: the shared parameterized function, the oc wrapper, and the agy wrapper, showing each wrapper keeps the ORIGINAL name and signature. Paste the explicit list of which symbols are wrapped (expected: `run_checked`, `discover_plans`, `save_state`, `validate_manifest`, `print_status`) and confirm the other 29-30 are strict-fingerprint moves. Paste a call-site count for `save_state` and `run_checked` in BOTH runners before and after, showing they are UNCHANGED, which is the whole point of the wrapper ruling.
  THEN prove the harness is load-bearing, not decorative: deliberately alter one moved body, paste the resulting FAILURE, and revert. A harness that passes both before and after such an alteration is not a harness and this item FAILS.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste a package-wide check showing exactly ONE `DriverError` definition. Paste `oc_runipd.DriverError is agy_runipd.DriverError` -> True (it is False today; paste the before too) and `issubclass(agy_runipd.StallTimeout, runner_shared.DriverError)` -> True. Paste a DEMONSTRATION that agy's `main` still catches a dependency-preflight refusal and still prints its `runagy: ...` message (run it; do not reason about it). State plainly whether the translation wrapper (documented at `agy_runipd.py:87-93`, implemented at `:1388-1411`) was kept or removed, and if removed, paste the evidence that removal changed nothing about what `main` catches.
  ALSO REQUIRED (PR-305), because this item RE-PARENTS a live exception: paste a demonstration that a `StallTimeout` raised by the stall watchdog is still caught where it was caught before, exercised rather than reasoned about. A `issubclass` check alone does NOT satisfy this: subclass-ness proves the type lattice, not that every `except DriverError` site in agy is reached, and a stall that stops being caught converts a clean timeout into an unhandled traceback in an unattended overnight run. Confirm `StallTimeout`'s own body was NOT edited (it is class (c) DIVERGED and out of scope).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: for each of the five symbols, paste the fingerprint match and the `assertIs` result. Paste `rg -n "^def utc_now|^def should_color|^def new_run_id|^def state_root|^def resolve_run_dir" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning NOTHING for both runners.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: fingerprint match and `assertIs` per symbol for the five clean ones. For `run_checked`, paste the SHARED parameterized definition and BOTH runners' one-line wrappers, plus proof `runner_shared` does not import `pinned_child_env` from a runner, plus the before/after call-site counts (13 oc, 9 agy) showing they are unchanged. Paste the `_run_git` collision check showing `layout_inventory.py`/`layout_migration.py` were left alone and their bodies genuinely differ (their return TYPE differs from the runners', which is the clearest single proof).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: fingerprint match and `assertIs` for the SEVEN symbols this item owns (not eight; `state_root` belongs to E-04, per PR-303). Paste proof `write_report` is bound in per-runner wrappers rather than imported into shared code, and paste the `save_state` call-site counts (33 oc, 31 agy) before and after showing they are UNCHANGED. For `print_status`, paste the rendered output for BOTH hosts before and after, side by side, showing byte-identical results, and name the mechanism by which the host string is supplied.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: fingerprint match and `assertIs` for all eight lane symbols, and both runners showing no local definition. STATE whether `lanectn` landed while this was in flight; if it did, paste the conflict resolution and confirm no `lanectn` change was reverted or absorbed. Paste `git log --oneline` for both runner files covering the execution window, so a co-worker's commit is visible rather than assumed absent.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: fingerprint match and `assertIs` for all seven. FOR `discover_plans` SPECIFICALLY (PR-302): paste evidence each runner still receives its OWN `PlanRecord` type after the move (`type(...) is oc_runipd.PlanRecord` from oc and `is agy_runipd.PlanRecord` from agy), and paste a record obtained through the OC path showing its `kind` field is still populated, since a shared constructor that dropped `kind` would silently disable orchestrator detection in `action_for` with no error. Confirm the two `PlanRecord` definitions were NOT unified.
  Paste the extended guard table showing all 39 names (child 01's five plus these 34) and TWO sabotage failures, one per runner. Then the closing measurements: both driver suites with counts, the full bare suite compared against your own pre-change measurement, and a package-wide AST check that each of the 34 has exactly ONE definition.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 8 E-leaves across 2 task groups, one concern throughout (move the proven-identical symbols into one module without changing behavior). It is at the upper end deliberately: the seams are sequential edits to the SAME two files, so splitting them into separate plans would guarantee the merge conflicts the orchestrator warns about, while each E-item remains one seam with its own V-item. If a reviewer judges E-07 (the 242-line lane seam) too large, split THAT item, not the plan.

Open questions: none. OQ-01 and OQ-02 were resolved by the maintainer 2026-09-03: use `runner_shared.py`, and inject each outside dependency explicitly via a THIN PER-RUNNER WRAPPER (OQ-02's refinement at review, which keeps the no-seam and no-mutable-state prohibitions intact while preserving E-02's fingerprint proof and leaving ~86 call sites untouched). No blocking question remains, so this plan is executable once approved AND once child 01 (`2r306y`) has executed.

This plan is `to-review` and requires explicit human approval before execution. It also has a hard prerequisite: `Item-Dependencies: executed:2r306y`, because it EXTENDS the symmetric guard child 01 installs.

Scope fence: touch ONLY `agent_workflows/runner_shared.py` (new), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `tests/test_runner_shared.py` (new), and `tests/test_runner_refork_guard.py` (child 01's, extended). Do NOT edit any class (c) DIVERGED symbol's body, in either runner, for any reason: touching one is this plan's stop condition, not a judgment call. THE ONE PERMITTED EXCEPTION, stated so it is not mistaken for a violation: E-03 re-parents `agy_runipd.StallTimeout` onto the shared `DriverError`, which changes its BASE CLASS without editing its body. Nothing else in class (c) may be touched, including the two `PlanRecord` definitions, which stay as they are. Do NOT change `render_stream.py` or `selectors.py`. Do NOT re-home the 40 oc-to-agy imports. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or the orchestrator.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. A "pure move" claim rests on the fingerprint fixture and the identity assertions, NOT on a grep and NOT on the suites being green: the suites were green while `DriverError` was two different classes. If any body changed, say so and treat it as a finding, because a changed body means this was not a move. AND DO NOT CALL THE FIVE WRAPPED SYMBOLS BYTE-IDENTICAL MOVES: they gained a parameter by design, so their evidence is fingerprint-modulo-the-parameter plus a behavior test, and reporting them under the strict claim would misrepresent exactly the five symbols carrying the most risk.

Execution contract: RE-READ both runner modules immediately before each seam and locate every symbol BY NAME, never by the line numbers in this plan. These are the highest-contention files in the repo: 21 unexecuted plans declare them, another session committed `render_stream.py` in `a396cb1b` during authoring, and six `lanectn` plans will edit them. Commit per SEAM, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption. If a co-worker's in-flight change to a runner cannot be safely combined with a seam, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
