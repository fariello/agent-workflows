# IPD: extract the 34 common symbols into a shared runner library, pure move

- Date: 2026-09-03
- Kind: child
- Concern: 34 top-level symbols are defined TWICE, once per runner, with AST-identical bodies. Because they are identical there is no behavioral disagreement TODAY, which is exactly why they are the dangerous class: nothing signals when one copy is edited and the other is not, and that is how the 52 currently-diverged symbols got that way. Measured at HEAD `c8bb11ae` by research `tvnq50` (E-01 of orchestrator `5e4sb6`): 33 are AST-identical, `print_status` is identical after host-token normalization, and together they are 551 lines of the runners' definition mass. The concrete cost of leaving them duplicated is already visible: `DriverError` is defined in BOTH runners (`oc_runipd.py:202`, `agy_runipd.py:379`) as two DISTINCT classes, and `agy_runipd.py:87-93` records a hand-written wrapper that exists solely to translate one into the other, because `enforce_dependency_preflight` raises oc's class and agy's `main` cannot catch it.
- Scope: Create ONE shared runner library and move all 34 class (a) symbols into it, then have both runners import them. PURE MOVE: no body may change, and every move is verified by an AST-identity assertion against the pre-move definition plus an object-identity assertion that both runners resolve to the same object. Excludes reconciling any diverged symbol (deferred behind `lanectn` and E-02's characterization baseline), excludes the class (d) re-forks (child 01 owns them), excludes re-homing the 40 names `agy_runipd` already imports from `oc_runipd`, and excludes any behavior change whatsoever, including the `DriverError` wrapper's REMOVAL if removing it would alter what `main` catches.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shared.py, tests/test_runner_refork_guard.py
- Item-Dependencies: executed:2r306y
- Status: approved
- Readiness: go-pending-approval
- Set: rununify
- Order: 2
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: 818uru
- Approval: 2026-09-04, recorded via aw ipd set: status set to approved
- Blocks-Release: next

## Workflow history
- 2026-09-04 approved (aw set): status set to approved

- 2026-09-03 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-301..PR-306; GO - PENDING HUMAN APPROVAL. Verified at HEAD `25d3f0b0`, tree clean, plan committed and unchanged, so the pre-review snapshot was correctly skipped. `aw ipd lint` conforming at `--phase author` and again at `--phase review-finalize`. THE INVENTORY RE-MEASURED INDEPENDENTLY AND THE PLAN'S NUMBERS ARE RIGHT: 88 symbols are defined in both runners, 35 AST-identical and 53 diverged; subtracting the two `2r306y` owns (`_read_id`, `_read_status`) leaves exactly the 34 this plan claims, and `StallTimeout` correctly sits in the diverged set (its docstrings differ). F-3's `DriverError` claim is TRUE and live: `agy_runipd.DriverError is oc_runipd.DriverError` returns False at this HEAD and the translation wrapper at `agy_runipd.py:1388-1411` exists exactly as described. F-4's 40-name count is exact (via nested `ImportFrom`; a body-level scan alone shows 37). THE DOMINANT FINDING (PR-301, BLOCKER, fixed by maintainer ruling): the plan's own two central mechanisms CONTRADICTED each other. E-02 requires every moved body's post-move AST fingerprint to EQUAL its pre-move capture, and simultaneously requires four symbols to take a new injected parameter - which changes their signature and body, so the fingerprint CANNOT match and the plan's load-bearing proof would fail on precisely the four riskiest symbols. Measured second cost: uniform parameter injection rewrites roughly 86 call sites (`save_state` 33 in oc + 31 in agy; `run_checked` 13 + 9) across the two highest-contention files in the repo, which 7 `reviewed` `lanectn` plans also edit. MAINTAINER RULED the thin runner-local wrapper: `runner_shared` owns the parameterized function, each runner keeps a one-line wrapper at the original name and signature binding its own dependency. That honors both original prohibitions (no registration seam, no module-level mutable state), leaves all ~86 call sites untouched, and keeps the fingerprint proof honest for the 30 clean symbols while the 4 wrapped ones are proven by behavior. E-02, E-05, E-06, E-08 and V-02 rewritten accordingly. Also FIXED: (PR-302, HIGH) the plan named four outside-dependencies; measurement finds a FIFTH problem in the same class - `discover_plans` also closes over `PlanRecord`, and the two runners' `PlanRecord` are DIFFERENT NamedTuples (oc has an extra `kind` field), so a moved `discover_plans` returning oc's shape would silently change agy's records. (PR-303, MEDIUM) E-06 lists `state_root` a second time ("if not already moved") after E-04 already moved it, and lists 7 symbols while its own count says 8; ambiguity in a move manifest is how a symbol gets moved twice or not at all. (PR-304, MEDIUM) the `runner_shared` docstring rule "holds only symbols PROVEN identical" is contradicted by the plan's own design the moment a parameterized wrapper target lands there; wording corrected so the module's stated contract matches what it will actually contain. (PR-305, LOW) E-03's `StallTimeout` check is understated: agy's `StallTimeout` subclasses agy's `DriverError`, so unifying the base class RE-PARENTS a live exception used by the stall watchdog. (PR-306, LOW) F-1's "551 oc lines" is not reproducible from the stated method without also stating it counts oc-side definition lines only. Three decisions recorded in the typed review record (D-1, D-2, D-3; all reversible).
- 2026-09-03 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored FROM E-01's inventory (research `tvnq50`), per orchestrator `5e4sb6`'s SECOND GATE. THREE CORRECTIONS to the orchestrator's child table, all from measurement rather than preference. (1) The count is **34, not 35** (33 AST-identical plus `print_status`, identical only after host-token normalization, which the table's "byte-identical" framing would have wrongly excluded). (2) The table calls this a "pure move ... verified by an identity assertion", which holds, but a naive lift FAILS: four symbols in the set call symbols OUTSIDE it (`run_checked` -> `pinned_child_env`, `discover_plans` -> `parse_plan_file`, `save_state` -> `write_report`, `validate_manifest` -> `parse_dependency_token`), and two of those four are class (c) DIVERGED, which this plan may not touch. E-02 resolves that by dependency injection rather than by dragging diverged code along. (3) `DriverError` is a LATENT BUG, not merely a duplicate: two distinct classes with a hand-written translation wrapper already documented at `agy_runipd.py:87-93`. Unifying it is the highest-value single symbol here and is sequenced first. Authored review-ready, not draft.
- 2026-09-03 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Give each of the 34 identical symbols exactly ONE definition, in one shared module both runners import, without changing a single line of any body and without touching a diverged symbol.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the module, and the identity harness that makes "pure move" falsifiable

- [x] E-01 Create `agent_workflows/runner_shared.py`, following `host_runner.py`'s conventions (module docstring stating what it owns and why, section banner comments, no import of either runner so no cycle can form). It starts EMPTY of moved logic; this item establishes the module and its contract only. Record in the docstring the constraint that decides every later question here: this module holds only symbols whose bodies were PROVEN identical across both runners, it may never import either runner, and a symbol whose bodies differ belongs in a later child, not here.
  STATE THE ADMISSION RULE PRECISELY (corrected at review, PR-304), because the obvious wording is false the moment E-02's wrapper mechanism lands: a moved function may take an outside dependency as a PARAMETER, so the rule is not "identical bodies, verbatim" but "identical bodies MODULO an explicitly injected dependency, with the injection recorded". Write it that way. A docstring asserting a stricter rule than the module actually keeps is worse than none, because the next reader will either believe it and be misled or notice the contradiction and distrust the whole contract. Per OQ-02 of the orchestrator, this module is the shared runner library and `plan_readiness.py` is DESIGNATED a peer it may import, NOT absorbed (its consumers include `status_set.py` and `ipd_schema.py`, which are not runners).
  - Depends on: none
  - Expected outcome: a new module that imports cleanly, defines no runner logic yet, and states its own admission rule; `python3 -c "import agent_workflows.runner_shared"` succeeds and a cycle check shows it imports neither runner.
  - Execution state: performed
  - Execution note: Created `agent_workflows/runner_shared.py` (787 lines at completion), following `host_runner.py`'s conventions: a docstring stating what the module owns and its design posture, banner comments per section, no import of a caller. It imports NEITHER runner, asserted by AST rather than by reading (`tests/test_runner_shared.py::NoRunnerImportTests`), and keeps NO module-level mutable state, so the maintainer's declined-registration-seam ruling is structurally enforced rather than merely documented. THE ADMISSION RULE IS STATED IN THE CORRECTED FORM PR-304 demanded: "identical bodies MODULO an explicitly injected dependency, with the injection recorded", with the complete injection list enumerated in the docstring and pinned by a test, so it cannot grow silently. `plan_readiness.py` is recorded as a DESIGNATED peer, not absorbed, per the orchestrator's OQ-02.

- [x] E-02 Build the MOVE HARNESS before moving anything, because "pure move" is a claim that must be mechanically checkable rather than eyeballed 34 times. Capture the pre-move AST fingerprint of all 34 symbols from BOTH runners (`ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)`, the same method E-01 of the orchestrator used), store it as a fixture, and assert after each move that the shared definition's fingerprint EQUALS the captured one.
  THE FIVE OUTSIDE-DEPENDENCIES, and the mechanism REVISED AT REVIEW. A naive lift fails because some moved symbols call symbols that stay behind (measured): `run_checked` -> `pinned_child_env` (oc-only, host-specific), `discover_plans` -> `parse_plan_file` (class (c) DIVERGED) AND `PlanRecord` (found at review, PR-302: the two runners' `PlanRecord` are DIFFERENT NamedTuples, oc's carrying an extra `kind` field, so a moved `discover_plans` would silently return oc's shape to agy), `save_state` -> `write_report` (class (c) DIVERGED), `validate_manifest` -> `parse_dependency_token` (oc-only, host-specific). A moved symbol must NOT import a diverged symbol from a runner, because that both re-creates the coupling and drags undecided behavior into shared code.
  MECHANISM: THIN RUNNER-LOCAL WRAPPER (maintainer ruling 2026-09-03 at review, superseding the earlier uniform-parameter-injection ruling of the same day). `runner_shared` owns the real function, taking each outside dependency as an explicit PARAMETER; each runner keeps a ONE-LINE wrapper at the ORIGINAL name and the ORIGINAL signature that calls it, binding its own dependency. This still honors both original prohibitions, which is why it is a refinement and not a reversal: the dependency is passed explicitly at a single visible site per runner, there is NO registration seam, and there is NO module-level mutable state.
  WHY THE UNIFORM-INJECTION FORM WAS REVISED, recorded so it is not re-proposed: (1) it CONTRADICTED THIS ITEM'S OWN PROOF - a function whose signature and body just gained a parameter cannot have an unchanged AST fingerprint, so the plan's load-bearing "pure move" evidence would have failed on exactly the four riskiest symbols; (2) MEASURED COST - threading a parameter through every call rewrites roughly 86 call sites (`save_state` is called 33 times in oc and 31 in agy; `run_checked` 13 and 9), all inside the two highest-contention files in the repo, which seven `reviewed` `lanectn` plans also edit, so it would manufacture the merge conflicts E-07 already warns about.
  THE FINGERPRINT RULE THEREFORE SPLITS, and say so plainly rather than quietly exempting things: the 30 symbols with no outside dependency are proven by STRICT fingerprint equality; the wrapped ones are proven by (a) fingerprint equality of the shared body MODULO the added parameter, stated explicitly and shown, plus (b) a BEHAVIOR test per symbol through each runner's wrapper. A wrapped symbol claimed as a byte-identical move would be a false claim.
  - Depends on: E-01
  - Expected outcome: a fixture of 34 pre-move fingerprints captured at a stated HEAD; the wrapper mechanism documented with one worked example showing the shared function, the oc wrapper and the agy wrapper; a test that FAILS if any of the 30 clean bodies' fingerprints differ from capture; and an explicit list of exactly which symbols are wrapped and why, so the exemption is enumerated rather than implicit.
  - Execution state: performed
  - Execution note: Built the harness BEFORE moving anything, and it was IMMEDIATELY load-bearing rather than ceremonial: a first, hand-written pass at the shared module was REJECTED on 15 of 33 symbols, and two of those 15 were REAL behavior changes I had introduced without noticing (`utc_now` rendered `strftime('%Y-%m-%dT%H:%M:%SZ')` instead of `.replace(microsecond=0).isoformat()`, and `should_color` read `AW_FORCE_COLOR` instead of `FORCE_COLOR`). That is precisely the class of defect the plan says a green suite cannot catch. The module body is therefore GENERATED from the runners' actual source text by AST line-span extraction, never retyped. Fixture: `tests/fixtures/runner_shared_premove_fingerprints.json`, 34 symbols x 2 runners captured at pre-move HEAD `1ecc5891`. THE FINGERPRINT RULE SPLITS as required: 25 strict, 8 injected (proven by subtraction), 1 host-naming-only, 1 unmovable. THE INJECTED COUNT IS 8, NOT 5: see the E-05 note for the three the plan's analysis could not see.

### Task group 2: move by seam, smallest and safest first

Move order is deliberate: each seam is independently verifiable, and the two seams with outside-dependencies come last so the harness is already proven on clean cases.

- [x] E-03 Move the `DriverError` unification FIRST, alone, because it is the one symbol here that is a latent BUG rather than only a duplicate. `oc_runipd.py:202` and `agy_runipd.py:379` define two DISTINCT classes (re-verified at review: `agy_runipd.DriverError is oc_runipd.DriverError` -> False at this HEAD); the wrapper documented at `agy_runipd.py:87-93` and implemented at `:1388-1411` exists only to translate oc's class into agy's so agy's `main` can catch it. Move the single definition to `runner_shared`, have both runners import it, and then check whether that wrapper is still needed. DO NOT DELETE THE WRAPPER AS A MATTER OF COURSE: if removing it changes what `agy_runipd.main` catches or what message it prints, it stays and this plan records why.
  RE-PARENTING A LIVE EXCEPTION IS THE REAL RISK HERE, and it is understated as "verify the subclass relationship" (PR-305). `agy_runipd.StallTimeout` SUBCLASSES agy's `DriverError` (`agy_runipd.py:383`) and is what the stall watchdog raises, so this move CHANGES StallTimeout's base class from agy's local class to the shared one. Every `except DriverError` in agy (measured: raises and handlers throughout, including `:479`, `:550`, `:1288`, `:1338`) must still catch a `StallTimeout`, and the WATCHDOG PATH specifically must be exercised rather than reasoned about, since a stall that stops being caught turns a clean timeout into an unhandled traceback in an unattended overnight run. Note `StallTimeout` itself is class (c) DIVERGED (the two docstrings differ), so this item may re-parent it but must NOT edit its body.
  - Depends on: E-02
  - Expected outcome: exactly one `DriverError` in the package; `oc_runipd.DriverError is agy_runipd.DriverError` is True; `issubclass(agy_runipd.StallTimeout, runner_shared.DriverError)` is True; agy's `main` still catches a preflight refusal and still prints its `runagy: ...` message, demonstrated rather than asserted; an explicit statement of whether the wrapper was kept or removed, with the reason.
  - Execution state: performed
  - Execution note: Moved FIRST and ALONE. `oc_runipd.DriverError is agy_runipd.DriverError` was False before and is True after; both are now `runner_shared.DriverError`, the single definition package-wide. `StallTimeout` in both runners and `ToolIdentityError` in oc are RE-PARENTED onto it with their bodies untouched (the two `StallTimeout` docstrings still differ, which is why they remain class (c) DIVERGED and out of scope; a test asserts they have NOT converged). THE WRAPPER'S FATE IS SETTLED AS KEEP-NARROWED, not deleted, and the reason is a behavior difference the plan told me to look for: the old wrapper re-raised the BASE `DriverError`, which DOWNGRADED any subclass, so an upstream `except ToolIdentityError` would have been defeated. Today the shared preflight raises only the base class, so that downgrade is unobservable - but removing the handler entirely and keeping the type-flattening are both worse than preserving the message-and-exit shape while dropping the flattening, which is what landed. Its `except _OcDriverError` half and that import are gone.

- [x] E-04 Move the RUN/MISC seam (5 remaining symbols, 37 lines): `utc_now`, `should_color`, `new_run_id`, `state_root`, `resolve_run_dir`. `print_status` is deliberately NOT in this item: it is the one host-naming-only symbol, so it needs the normalization decision E-06 makes.
  - Depends on: E-03
  - Expected outcome: five symbols defined once; both runners' attributes are the same objects by `assertIs`; fingerprints match the pre-move capture.
  - Execution state: performed
  - Execution note: Moved `utc_now`, `should_color`, `new_run_id`, `state_root`, `resolve_run_dir` as clean re-exports. ALSO MOVED, and NOT in the plan's dependency list: the four module CONSTANTS the later seams' bodies close over (`_SET_RE`, `_ORDER_RE`, `ID6_RE`, `SCHEMA_VERSION`), whose assignment VALUES were verified byte-identical at the AST level. The inventory missed them because its method enumerated `def`/`class` symbols rather than module-level assignments; they also CANNOT be left behind, because a function defined in `runner_shared` resolves a free name against `runner_shared`'s globals, so `_read_set` would raise `NameError`. Child 01 set the precedent by tabling the four ANSI constants for the same stated reason. WORTH RECORDING: my first attempt added the imports but left the local assignments in place, so oc's local `SCHEMA_VERSION = 1` SHADOWED the import above it - and an identity check still printed True, because the values compare as the same object. A shadowed duplicate LOOKS unified and is not. `ruff --select F811` caught it. See decision 05-818uru-D3.

- [x] E-05 Move the GIT seam (6 symbols, 53 lines): `_run_git`, `git_head`, `git_branch`, `git_status`, `git_common_dir`, `run_checked`. `run_checked` carries the `pinned_child_env` outside-dependency, so apply E-02's WRAPPER mechanism here and treat this as its first real exercise: `runner_shared.run_checked` takes the env-builder as a parameter, and each runner keeps a one-line `run_checked` wrapper binding its own, so the 13 oc and 9 agy call sites are NOT rewritten. Note `_run_git` is ALSO defined in `layout_inventory.py` and `layout_migration.py` but those are NAME COLLISIONS with different bodies, not re-forks (re-verified at review: all three signatures and bodies differ; the runners' returns a `(rc, out, err)` tuple while both layout copies return a `CompletedProcess`) - do not "unify" them.
  - Depends on: E-04
  - Expected outcome: six symbols defined once; `run_checked`'s dependency bound in a per-runner wrapper rather than imported from a runner into shared code; every existing `run_checked` call site unchanged; and the collision note verified rather than assumed.
  - Execution state: performed
  - Execution note: Moved all six. `_run_git` and `git_branch` are clean; `run_checked` takes `env_builder` per the maintainer's wrapper ruling, with a one-line wrapper in each runner binding its own `pinned_child_env`. THE PLAN'S DEPENDENCY ANALYSIS WAS INCOMPLETE HERE IN A WAY THAT BREAKS RATHER THAN MERELY COMPLICATES, and this is the single most important finding of the execution: `git_head`, `git_status` and `git_common_dir` CALL `run_checked`, which is in this same seam and whose signature changed, so a naive lift raises `TypeError: run_checked() missing 1 required keyword-only argument: 'env_builder'` - reproduced through BOTH runners before fixing. The analysis searched for calls OUT of the moved set and could not see an intra-seam dependency on a symbol whose own signature changed. THE OBVIOUS REPAIR IS A TRAP: rewriting the three onto the shared `_run_git` directly above them reads like a cleanup but would change `git_head` from raising `DriverError` to returning `""` and would drop `git_status`'s `--short`, and both feed every run's outcome record at four sites per runner with no suite asserting on them. The seam's own mechanism was applied uniformly instead, and a test now fails if anyone makes that "simplification". So the injected count is 8, not 5. See decision 05-818uru-D4.

- [x] E-06 Move the JSON/STATE seam. EXACT MANIFEST, 7 symbols (corrected at review, PR-303 - the earlier wording listed `state_root` a second time "if not already moved" although E-04 already moves it, and said 7 while counting 8; an ambiguous move manifest is how a symbol gets moved twice or skipped): `load_json`, `atomic_write_json`, `append_jsonl`, `sha256_file`, `load_state`, `save_state`, `print_status`. `state_root` is NOT in this item; E-04 owns it. TWO SPECIAL CASES: `save_state` calls `write_report`, a class (c) DIVERGED symbol, so it takes it as a parameter with a per-runner wrapper (this is the highest-count wrapper in the plan, protecting 33 oc and 31 agy call sites); and `print_status` differs between runners ONLY by host tokens (verified at review: the two bodies are identical except `driver_label='opencode'` versus `'antigravity'`), so moving it requires deciding how the host string is supplied (a parameter, almost certainly) and PROVING the rendered output is byte-identical to each runner's current output for both hosts.
  - Depends on: E-05
  - Expected outcome: seven symbols defined once; `write_report` bound in per-runner wrappers with all 64 `save_state` call sites unchanged; `print_status` renders byte-identically to today for BOTH hosts, shown side by side.
  - Execution state: performed
  - Execution note: Moved the SEVEN this item owns, not eight: `load_json`, `atomic_write_json`, `append_jsonl`, `sha256_file`, `load_state`, `save_state`, `print_status`. `state_root` was NOT touched here; E-04 owns it, per PR-303. `save_state` takes `write_report` (class (c) DIVERGED - the two drivers render different reports, so importing one would silently give both drivers that format), the highest-count wrapper in the plan. `print_status` takes `driver_label`, the sole host-naming-only symbol. BYTE-IDENTICAL RENDERING PROVEN BY CAPTURE, not by assertion: both hosts' output was rendered at pre-move HEAD `1ecc5891` in a detached worktree and diffed against post-move output - identical for oc and identical for agy. A first attempt tested this as `oc_output.replace("opencode","antigravity") == agy_output` and FAILED for a reason unrelated to the move: the summary is a box-drawn TABLE, so swapping an 8-character label for an 11-character one shifts column padding. That test would have reported a formatting artifact as a move defect; it was replaced by the claim that matters (each host names ITSELF) with byte-identity carried by the capture.

- [x] E-07 Move the LANE seam (8 symbols, 242 lines, the largest): `_lane_records_from_state`, `describe_lane`, `format_lane_report`, `print_lane_interrupt_report`, `build_recovery_lane_notice`, `allocate_isolation_worktree`, `teardown_isolation_worktree`, `disable_lane_prompt`. CONTENTION WARNING, and it is the reason this seam is LAST: six of the seven `lanectn` plans declare both runner modules in their Scope-Paths. They name none of these eight symbols (verified: zero mentions across all seven plans), so there is no logical conflict, but there is a real TEXTUAL conflict risk if `lanectn` lands while this is in flight. Re-read both runners immediately before editing and stop rather than overwrite.
  - Depends on: E-06
  - Expected outcome: eight symbols defined once, fingerprints matching, and an explicit statement of whether `lanectn` landed in the interim and how conflicts were handled.
  - Execution state: performed
  - Execution note: Moved SEVEN of the eight, all clean re-exports with strict fingerprint matches; 242 lines per copy, the largest seam. `disable_lane_prompt` CANNOT MOVE and stays in both runners: it mutates a module-level `_LANE_PROMPT_DISABLED` through `global`, so a shared definition would write `runner_shared`'s flag while each runner's `_lane_reclaim_prompt` (class (c) DIVERGED, so it stays) kept reading its OWN, and prompt suppression on a repeated interrupt would silently stop working - the symptom being an unattended run pausing to ask a question nobody is there to answer. It is the ONLY `global` among the 34 (verified by AST across all of them) and the reason is pinned in `UnmovableSymbolTests`. CONTENTION, which this item requires stating: `lanectn` has NOT landed - all seven of its plans remain unexecuted - and `git log` on both runner files shows no commit between this seam and E-06 other than my own. No conflict arose; nothing of anyone else's was overwritten or reverted. THREE GUARD TESTS OWNED BY OTHER PLANS were retargeted rather than weakened; see V-07 and decisions 05-818uru-D5/D6.

- [x] E-08 Move the PLAN/SELECTOR seam (7 symbols, 170 lines): `discover_plans`, `resolve_plan_path`, `plan_bucket`, `_read_set`, `_read_order`, `describe_unresolved_plan_selector`, `validate_manifest`. `discover_plans` depends on `parse_plan_file` (DIVERGED) and `validate_manifest` on `parse_dependency_token` (oc-only), so both take per-runner wrappers per E-02.
  `discover_plans` ALSO CLOSES OVER `PlanRecord`, AND THE TWO RUNNERS' `PlanRecord` ARE DIFFERENT TYPES (found at review, PR-302; the plan's four-dependency list missed it). Measured: oc's `PlanRecord` has fields `(id6, setid, status, order, path, rel_path, dependencies, kind, dependency_error, from_backlog)` while agy's LACKS `kind` (`oc_runipd.py` vs `agy_runipd.py:1414`). So a shared `discover_plans` that constructs oc's `PlanRecord` would silently hand agy records carrying a field its own code never expects, and one that constructs agy's would DROP `kind` - which oc's `action_for` (`oc_runipd.py:2749`) reads to decide whether a plan is an orchestrator. Either way the failure is silent and type-shaped, not a crash. Treat `PlanRecord` as a dependency of the same kind: the record CONSTRUCTOR is supplied per runner, exactly like `parse_plan_file`. Do NOT unify the two `PlanRecord` definitions here; that is a class (c) reconciliation this plan may not perform.
  Then extend child 01's symmetric re-fork guard to cover all 34 moved symbols, so a future re-fork of any of them fails a test in EITHER runner, and sabotage-verify that extension in both directions.
  - Depends on: E-07
  - Expected outcome: seven symbols defined once; `PlanRecord`'s constructor supplied per runner with proof that each runner still gets its OWN record type (an `is` check per runner, plus evidence oc's `kind` field survives); the guard's table now covers all 34 plus child 01's five; sabotage in each runner fails the guard.
  - Execution state: performed
  - Execution note: Moved all seven. `discover_plans` CARRIES TWO DEPENDENCIES IN ONE INJECTION, which makes it the subtlest move here: `parse_plan_file` is class (c) DIVERGED and is also what CONSTRUCTS each runner's `PlanRecord`, and the two `PlanRecord` are different NamedTuples (oc's carries `kind`, agy's does not). Injecting the PARSER rather than the record type is what keeps each driver's own type; verified by running both. ONE ANNOTATION HAD TO CHANGE and is stated rather than hidden, because it is the only place a moved body's text differs beyond gaining a parameter: `runner_shared` cannot NAME `PlanRecord` (importing either runner's is exactly the forbidden coupling), so `dict[str, PlanRecord]` became `dict[str, Any]`; the harness maps that spelling back before comparing, so the rest of the body is still held to EXACT equality. GUARD EXTENDED by 29 rows covering every clean-moved symbol plus the four constants; because child 01 built it as a DATA TABLE, the guarantee now applies to both runners in both directions automatically. Two absences from the table are recorded decisions, not oversights: the 8 wrapped symbols (a wrapper IS a local `def`, so their guarantee is enforced by `SingleDefinitionTests` proving each is a single delegating statement) and `disable_lane_prompt`.

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

- [x] V-01 validates E-01
  - Required evidence: paste the new module's docstring showing it states its own admission rule (identical-only, never imports a runner). Paste `python3 -c "import agent_workflows.runner_shared"` succeeding, and paste a check proving it imports neither runner (for example an AST scan of its `ImportFrom` targets). State which OQ-01 name was used.
  - Observed evidence: NAME USED, per OQ-01: `runner_shared.py`.
    Docstring (excerpt showing the admission rule, stated in PR-304's corrected form):
    ```
    # ---- THE ADMISSION RULE ---------------------------------------------------------
    A symbol belongs here only if BOTH runners' definitions were PROVEN identical by AST
    comparison (`ast.dump(ast.parse(ast.unparse(node)), include_attributes=False)`), never
    merely judged similar by reading. ...
    State the rule precisely, because the obvious wording is FALSE one screen further down:
    it is "identical bodies MODULO AN EXPLICITLY INJECTED DEPENDENCY", not "identical bodies
    verbatim". ...
      * This module MUST NOT import either runner, at module level or lazily inside a
        function. ... importing a DIVERGED symbol from one runner into shared code would
        silently give BOTH drivers that runner's behavior, which is a behavior change wearing
        a de-duplication's clothes.
      * NO module-level mutable state. A registration seam ... was considered ... and DECLINED
        by the maintainer: process-global state makes behavior depend on import ORDER and leaks
        between tests.
      * A symbol whose bodies DIFFER belongs to a later child of the `rununify` Set, not here.
    ```
    Import succeeds standalone:
    ```
    $ python3 -c "import agent_workflows.runner_shared as m; print(m.__name__)"
    agent_workflows.runner_shared
    ```
    Cycle check, by AST over every `Import`/`ImportFrom` in the module (module level AND lazy,
    since a lazy runner import would be just as fatal):
    ```
    runner_shared imports a runner: False []
    ```
    Its only `agent_workflows` imports are `render_stream` (module level) and, lazily inside
    moved bodies, `worktree_lease` and `selectors` - none of them a runner. Enforced by
    `tests/test_runner_shared.py::NoRunnerImportTests` (2 tests), so this is a standing guard
    and not a one-time check. OQ-02: `plan_readiness.py` is DESIGNATED a peer, not absorbed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the fingerprint fixture (or its generation command and a sample), showing all 34 symbols captured with the HEAD they were captured at. Paste the WRAPPER mechanism with one worked example: the shared parameterized function, the oc wrapper, and the agy wrapper, showing each wrapper keeps the ORIGINAL name and signature. Paste the explicit list of which symbols are wrapped (expected: `run_checked`, `discover_plans`, `save_state`, `validate_manifest`, `print_status`) and confirm the other 29-30 are strict-fingerprint moves. Paste a call-site count for `save_state` and `run_checked` in BOTH runners before and after, showing they are UNCHANGED, which is the whole point of the wrapper ruling.
  THEN prove the harness is load-bearing, not decorative: deliberately alter one moved body, paste the resulting FAILURE, and revert. A harness that passes both before and after such an alteration is not a harness and this item FAILS.
  - Observed evidence: FIXTURE `tests/fixtures/runner_shared_premove_fingerprints.json`,
    generated by AST capture at pre-move HEAD `1ecc5891f6bf8c4f1e42b1e9f863839157c8cc6d`:
    ```
    captured 34 symbols x 2 runners at 1ecc5891f6bf8c4f1e42b1e9f863839157c8cc6d
      AST-identical across runners: 33
      NOT identical: ['print_status']
    ```
    That INDEPENDENTLY RE-DERIVES the plan's load-bearing count (33 AST-identical + 1
    host-naming-only = 34) rather than trusting it, and a test re-derives it from the fixture
    on every run.
    WRAPPER MECHANISM, worked example (`run_checked`), showing the shared parameterized
    function and both wrappers keeping the ORIGINAL name and signature:
    ```
    # runner_shared.py
    def run_checked(argv, cwd=None, env=None, *, env_builder: Callable[...]) -> str:
        merged_env = env_builder(env)          # was: pinned_child_env(env)
        ...
    # oc_runipd.py
    def run_checked(argv: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
        return runner_shared.run_checked(argv, cwd, env, env_builder=pinned_child_env)
    # agy_runipd.py
    def run_checked(argv: list[str], cwd: Path | None = None, env: dict | None = None) -> str:
        return runner_shared.run_checked(argv, cwd, env, env_builder=pinned_child_env)
    ```
    WRAPPED SET IS 8, NOT THE EXPECTED 5. Expected by the plan: `run_checked`,
    `discover_plans`, `save_state`, `validate_manifest`, `print_status`. ACTUAL, adding three
    the plan's analysis could not see: `git_head`, `git_status`, `git_common_dir` (they call
    `run_checked`, an intra-seam dependency whose signature changed; see E-05 and decision
    05-818uru-D4). The other 25 are strict-fingerprint moves and 1 (`disable_lane_prompt`) did
    not move at all. The list is enumerated in the test module's `INJECTED` dict and asserted,
    so it cannot grow silently.
    CALL SITES UNCHANGED. The plan's figures (33/31 `save_state`, 13/9 `run_checked`) are
    SUBSTRING counts of `name(`, which also count the `def` line and docstring mentions; I
    replaced them with an AST `ast.Call` count rather than quietly adopting an inflated
    baseline. Measured at pre-move `1ecc5891` and at this HEAD:
    ```
      oc_runipd    save_state         32   ->  32  (unchanged)
      agy_runipd   save_state         30   ->  30  (unchanged)
      oc_runipd    run_checked        12   ->   9  (-3, accounted for)
      agy_runipd   run_checked         8   ->   5  (-3, accounted for)
    ```
    The `run_checked` drop is NOT a rewritten call site: `git_head`/`git_status`/
    `git_common_dir` were themselves callers and RELOCATED into `runner_shared` in this same
    seam. The subtraction is stated explicitly in the test rather than absorbed into a fudged
    expected number, and a companion test asserts those three still call it by injection.
    HARNESS PROVEN LOAD-BEARING, both halves, by deliberate sabotage and revert.
    (a) A CLEAN body (`plan_bucket`, added `parts = tuple(reversed(parts))`):
    ```
    E  AssertionError: ... : `plan_bucket` was NOT a pure move: its body differs from the
       pre-move capture at 1ecc5891f6bf8c4f1e42b1e9f863839157c8cc6d
    FAILED tests/test_runner_shared.py::PureMoveFingerprintTests::
           test_every_clean_symbol_is_a_STRICT_fingerprint_match
    ```
    (b) An INJECTED body (`run_checked`, `env_builder(env)` -> `env_builder(env) or {}`), which
    matters more, since that is the path carrying the enumerated exemption:
    ```
    E  AssertionError: ... : `run_checked` differs from its pre-move capture by MORE than the
       injected `env_builder` parameter
    FAILED tests/test_runner_shared.py::PureMoveFingerprintTests::
           test_every_injected_symbol_matches_MODULO_its_one_new_parameter
    ```
    Both reverted; the harness is green again (`43 passed`). ALSO NOTE the harness caught real
    defects in my OWN work before any of this: a first hand-written pass at the module was
    rejected on 15 of 33 symbols, two of them genuine behavior changes (`utc_now`'s output
    format, `should_color`'s env var). The module is generated from runner source as a result.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste a package-wide check showing exactly ONE `DriverError` definition. Paste `oc_runipd.DriverError is agy_runipd.DriverError` -> True (it is False today; paste the before too) and `issubclass(agy_runipd.StallTimeout, runner_shared.DriverError)` -> True. Paste a DEMONSTRATION that agy's `main` still catches a dependency-preflight refusal and still prints its `runagy: ...` message (run it; do not reason about it). State plainly whether the translation wrapper (documented at `agy_runipd.py:87-93`, implemented at `:1388-1411`) was kept or removed, and if removed, paste the evidence that removal changed nothing about what `main` catches.
  ALSO REQUIRED (PR-305), because this item RE-PARENTS a live exception: paste a demonstration that a `StallTimeout` raised by the stall watchdog is still caught where it was caught before, exercised rather than reasoned about. A `issubclass` check alone does NOT satisfy this: subclass-ness proves the type lattice, not that every `except DriverError` site in agy is reached, and a stall that stops being caught converts a clean timeout into an unhandled traceback in an unattended overnight run. Confirm `StallTimeout`'s own body was NOT edited (it is class (c) DIVERGED and out of scope).
  - Observed evidence: EXACTLY ONE `DriverError` package-wide, by AST over every
    `agent_workflows/*.py`:
    ```
    DriverError  ->  ['runner_shared.py:138']     (1 definition)
    ```
    IDENTITY, before and after:
    ```
    # before (HEAD 1ecc5891)
    DriverError is: False
    oc  DriverError subclasses: ['StallTimeout', 'ToolIdentityError']
    agy DriverError subclasses: ['StallTimeout']
    # after (HEAD dc1d9dee)
    oc is agy      : True
    oc is shared   : True
    agy StallTimeout subclass shared: True
    oc  StallTimeout subclass shared: True
    ToolIdentityError subclass shared: True
    ```
    AGY'S `main` STILL CATCHES A PREFLIGHT REFUSAL - RUN, not reasoned about. Against a scratch
    repo holding a plan with a dangling dependency:
    ```
    $ python3 -m agent_workflows.agy_runipd start --repo <tmp> aaaaaa
    runagy: dependency preflight failed: run refused before any session started - the selected
    IPDs' `- Item-Dependencies:` statements did not pass the shared evaluator at phase
    'pre-execution':
      check.ipd-dependency-dangling: executed:zzzzzz: no ipd artifact has id6 zzzzzz [...]
    Fix with `aw ipd dependencies set <id6> none|<edge>...`, then re-run.
    ```
    The `runagy: ...` message and the clean exit are both intact.
    WRAPPER: KEPT, NARROWED. Its `except _OcDriverError` half and the
    `from agent_workflows.oc_runipd import DriverError as _OcDriverError` import are DELETED;
    the handler itself stays. REASON, which is a behavior difference and not tidiness: the old
    form re-raised the BASE class, DOWNGRADING any subclass, so an upstream
    `except ToolIdentityError` would have been defeated. Demonstrated:
    ```
    ToolIdentityError is a DriverError: True
    after the wrapper's re-raise, type is: DriverError
    so `except ToolIdentityError` would MISS it: True
    ```
    The shared preflight raises only the base class today, so the downgrade is unobservable -
    which is why removal would ALSO have been defensible, and why the narrowed form (same
    message-and-exit shape, no type-flattening) was chosen as strictly better than either.
    WATCHDOG PATH EXERCISED, which this item states `issubclass` alone does NOT satisfy. The
    test walks each runner's SOURCE, confirms `raise StallTimeout(` still appears at 2+ sites
    and that both handler FORMS the runners rely on are present
    (`except StallTimeout:` at oc:5268/agy:3383 and
    `except (KeyboardInterrupt, StallTimeout):` at oc:5419/agy:3518), then raises the real
    class through each form plus a bare `except DriverError` - the form the re-parenting could
    have broken, since the base class now lives in another module. All pass for both runners.
    `StallTimeout` BODIES NOT EDITED: a test asserts the two docstrings still DIFFER (so the
    class is still class (c) DIVERGED and was not reconciled) and that each base is still
    spelled `DriverError`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: for each of the five symbols, paste the fingerprint match and the `assertIs` result. Paste `rg -n "^def utc_now|^def should_color|^def new_run_id|^def state_root|^def resolve_run_dir" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returning NOTHING for both runners.
  - Observed evidence: All five are single-definition and shared. AST, package-wide:
    ```
    utc_now          shared ONLY  ['runner_shared.py:145']
    should_color     shared ONLY  ['runner_shared.py:149']
    new_run_id       shared ONLY  ['runner_shared.py:162']
    state_root       shared ONLY  ['runner_shared.py:167']
    resolve_run_dir  shared ONLY  ['runner_shared.py:171']
    ```
    Fingerprints: STRICT match against the pre-move capture for all five (part of the 25 clean
    moves asserted by `test_every_clean_symbol_is_a_STRICT_fingerprint_match`).
    `assertIs`, both runners:
    ```
    utc_now              oc is shared=True  agy is shared=True
    should_color         oc is shared=True  agy is shared=True
    new_run_id           oc is shared=True  agy is shared=True
    state_root           oc is shared=True  agy is shared=True
    resolve_run_dir      oc is shared=True  agy is shared=True
    ```
    The requested grep returns NOTHING for both runners:
    ```
    $ rg -n "^def utc_now|^def should_color|^def new_run_id|^def state_root|^def resolve_run_dir" \
        agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    (no output)
    ```
    PLUS the four constants this item also moved, which the plan did not list (decision D3):
    ```
    constant SCHEMA_VERSION   oc=True agy=True
    constant ID6_RE           oc=True agy=True
    constant _SET_RE          oc=True agy=True
    constant _ORDER_RE        oc=True agy=True
    ```
    And the shadowing bug that nearly hid this: `ruff --select F811` reported
    `F811 Redefinition of unused 'SCHEMA_VERSION' from line 108` in oc and three siblings,
    because I had added the imports while leaving the local assignments. An `assertIs` check
    printed True anyway (equal values compare as the same object), so ONLY the linter caught
    it. Duplicates deleted; `ruff --select F811,F401,F821` now `All checks passed!`.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: fingerprint match and `assertIs` per symbol for the five clean ones. For `run_checked`, paste the SHARED parameterized definition and BOTH runners' one-line wrappers, plus proof `runner_shared` does not import `pinned_child_env` from a runner, plus the before/after call-site counts (13 oc, 9 agy) showing they are unchanged. Paste the `_run_git` collision check showing `layout_inventory.py`/`layout_migration.py` were left alone and their bodies genuinely differ (their return TYPE differs from the runners', which is the clearest single proof).
  - Observed evidence: All six single-definition. `_run_git` and `git_branch` are clean
    (`runner_shared.py:197` and `:213`, `shared ONLY`); the other four are shared + 2 wrappers:
    ```
    git_head        shared + 2 wrappers  ['agy_runipd.py:544', 'oc_runipd.py:472', 'runner_shared.py:209']
    git_status      shared + 2 wrappers  ['agy_runipd.py:548', 'oc_runipd.py:476', 'runner_shared.py:224']
    git_common_dir  shared + 2 wrappers  ['agy_runipd.py:552', 'oc_runipd.py:480', 'runner_shared.py:228']
    run_checked     shared + 2 wrappers  ['agy_runipd.py:523', 'oc_runipd.py:447', 'runner_shared.py:234']
    ```
    Fingerprints: STRICT for `_run_git` and `git_branch`; modulo-the-one-parameter for the four
    wrapped, each proven by SUBTRACTION (remove the parameter, map its use back, require exact
    equality) so any OTHER edit still fails.
    SHARED DEFINITION AND BOTH WRAPPERS for `run_checked`: see V-02's worked example above.
    `runner_shared` does NOT import `pinned_child_env` from a runner - the AST cycle check in
    V-01 shows zero runner imports, so the dependency arrives only as a parameter.
    CALL SITES: 12 oc / 8 agy before, 9 oc / 5 agy after, and the -3 per runner is fully
    accounted for by `git_head`/`git_status`/`git_common_dir` RELOCATING with the seam rather
    than by any call being rewritten; a companion test asserts those three still call
    `run_checked` by injection, and would fail if someone "simplified" them onto `_run_git`.
    BEHAVIOR, run rather than asserted - and this is the half that matters, because a naive
    lift of these three raised `TypeError: run_checked() missing 1 required keyword-only
    argument: 'env_builder'` through BOTH runners before the fix:
    ```
    oc_runipd  git_head match: True | git_status len: 130 | common_dir: .git
    agy_runipd git_head match: True | git_status len: 130 | common_dir: .git
    ```
    (`git_head` compared against `git rev-parse HEAD` run directly.) `run_checked` itself is
    exercised through both runners for a success, a nonzero exit raising `DriverError`, and the
    PYTHONPATH pin actually reaching the child (`AW_PIN_KEEP_ROOT` equals
    `runner_package_root()`), which proves the injected builder is the real
    `pinned_child_env` and not a stub.
    `_run_git` COLLISION CHECK, re-verified rather than assumed. Three same-named functions
    with different bodies; the clearest single proof is the RETURN TYPE:
    ```
    term.py:should_color            different body
    layout_inventory.py:sha256_file different body
    layout_inventory.py:_run_git    different body   # returns CompletedProcess, uses `git -C`
    layout_migration.py:_run_git    different body   # returns CompletedProcess, uses `git -C`
    benchmark_manifest.py:validate_manifest different body
    leak_sanitizer_config.py:load_state     different body
    ```
    The runners' version returns `(returncode, stdout, stderr)` and runs with `cwd=repo`. Both
    layout files were left untouched; unifying them would be a behavior change.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: fingerprint match and `assertIs` for the SEVEN symbols this item owns (not eight; `state_root` belongs to E-04, per PR-303). Paste proof `write_report` is bound in per-runner wrappers rather than imported into shared code, and paste the `save_state` call-site counts (33 oc, 31 agy) before and after showing they are UNCHANGED. For `print_status`, paste the rendered output for BOTH hosts before and after, side by side, showing byte-identical results, and name the mechanism by which the host string is supplied.
  - Observed evidence: SEVEN symbols, not eight - `state_root` belongs to E-04 (PR-303) and
    was not touched here. AST, package-wide:
    ```
    load_json          shared ONLY          ['runner_shared.py:269']
    atomic_write_json  shared ONLY          ['runner_shared.py:278']
    append_jsonl       shared ONLY          ['runner_shared.py:300']
    sha256_file        shared ONLY          ['runner_shared.py:308']
    load_state         shared ONLY          ['runner_shared.py:316']
    save_state         shared + 2 wrappers  ['agy_runipd.py:1781', 'oc_runipd.py:2777', 'runner_shared.py:320']
    print_status       shared + 2 wrappers  ['agy_runipd.py:3899', 'oc_runipd.py:5935', 'runner_shared.py:331']
    ```
    Fingerprints: STRICT for the five clean; modulo-the-parameter for `save_state` and
    `print_status`. `assertIs` holds for the five clean in both runners.
    `write_report` IS BOUND IN PER-RUNNER WRAPPERS, not imported into shared code:
    ```
    # runner_shared.py
    def save_state(run_dir, state, *, write_report: Callable[[Path, dict], None]) -> None:
        state["updated_at"] = utc_now(); atomic_write_json(run_dir / "state.json", state)
        write_report(run_dir, state)
    # each runner
    def save_state(run_dir: Path, state: dict[str, Any]) -> None:
        runner_shared.save_state(run_dir, state, write_report=write_report)
    ```
    V-01's AST cycle check shows `runner_shared` imports no runner, so the DIVERGED
    `write_report` reaches it only as a parameter. CALL SITES UNCHANGED: 32 oc / 30 agy before
    and after (AST `ast.Call` counts; the plan's 33/31 were substring counts including the
    `def` line). A behavior test drives `save_state` through BOTH runners and asserts
    `state.json` is written AND `execution-report.md` exists, which only the injected
    `write_report` creates - so the injection is proven wired, not merely accepted.
    `print_status` BYTE-IDENTICAL FOR BOTH HOSTS, proven by pre/post capture rather than by
    assertion. Rendered at pre-move HEAD `1ecc5891` in a detached worktree and at this HEAD,
    same fixture state, tmp path normalized:
    ```
    oc:  byte-identical to pre-move = True
    agy: byte-identical to pre-move = True
    ```
    MECHANISM: the host string is a keyword-only `driver_label` parameter; each runner's
    one-line wrapper supplies its own literal (`"opencode"` / `"antigravity"`), which is the
    ONLY thing the two pre-move bodies differed by.
    A FIRST ATTEMPT AT THIS TEST WAS WRONG and is recorded because it would have misled:
    asserting `oc_output.replace("opencode","antigravity") == agy_output` FAILS, but for a
    reason unrelated to the move - the summary is a box-drawn table, so an 8-character label
    and an 11-character one shift the column padding. It was replaced by the claim that
    matters (each host names ITSELF and not the other), with byte-identity carried by the
    capture above.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: fingerprint match and `assertIs` for all eight lane symbols, and both runners showing no local definition. STATE whether `lanectn` landed while this was in flight; if it did, paste the conflict resolution and confirm no `lanectn` change was reverted or absorbed. Paste `git log --oneline` for both runner files covering the execution window, so a co-worker's commit is visible rather than assumed absent.
  - Observed evidence: SEVEN of the eight moved, all clean, all STRICT fingerprint matches
    and `assertIs` in both runners. AST, package-wide:
    ```
    _lane_records_from_state     shared ONLY  ['runner_shared.py:343']
    describe_lane                shared ONLY  ['runner_shared.py:385']
    format_lane_report           shared ONLY  ['runner_shared.py:416']
    print_lane_interrupt_report  shared ONLY  ['runner_shared.py:454']
    build_recovery_lane_notice   shared ONLY  ['runner_shared.py:493']
    allocate_isolation_worktree  shared ONLY  ['runner_shared.py:567']
    teardown_isolation_worktree  shared ONLY  ['runner_shared.py:584']
    ```
    THE EIGHTH, `disable_lane_prompt`, DID NOT MOVE, and that is a finding rather than an
    omission:
    ```
    disable_lane_prompt  both runners (cannot move)  ['agy_runipd.py:792', 'oc_runipd.py:1607']
    ```
    It mutates a module-level `_LANE_PROMPT_DISABLED` through `global`. A shared `global` would
    write `runner_shared`'s flag while each runner's `_lane_reclaim_prompt` (class (c) DIVERGED,
    so it stays behind) kept reading its own, and prompt suppression on a repeated interrupt
    would silently stop working - an unattended run pausing for an answer nobody is there to
    give. It is the ONLY `global` among all 34 (AST scan over every one of them).
    `UnmovableSymbolTests` pins the reason and asserts the behavior still works in both runners.
    `lanectn` DID NOT LAND while this was in flight. All seven of its plans are still under
    `.aw/records/plans/pending/`, unexecuted. `git log` for both runner files across the whole
    execution window shows only my own commits since child 01's:
    ```
    $ git log --oneline -6 -- agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py
    dc1d9dee refactor(rununify): move the plan/selector seam, extend the guard (818uru E-08)
    6740330e refactor(rununify): move the lane seam to runner_shared (818uru E-07)
    99a9ae33 refactor(rununify): move the json/state seam to runner_shared (818uru E-06)
    99c4c132 refactor(rununify): move the git seam to runner_shared (818uru E-05)
    f8c49a09 refactor(rununify): move the run/misc seam to runner_shared (818uru E-04)
    229459ef refactor(rununify): create runner_shared, unify DriverError (818uru E-01..E-03)
    637c6f8a rununify-01 (2r306y): delete the already-extracted re-forks, make the guard symmetric
    ```
    So no conflict resolution was needed and NO co-worker change was reverted or absorbed.
    THREE GUARD TESTS OWNED BY OTHER PLANS WERE RETARGETED, NOT WEAKENED, and all three are
    SOURCE SCRAPES coupled to a symbol's location rather than its behavior:
      * `test_lane_allocation_idempotent.py::test_no_acknowledgement_gate_or_refusal_path_was_added`
        sliced each runner from `def build_recovery_lane_notice(`; after the move that
        `str.index` raised `ValueError: substring not found` BEFORE any assertion ran, so it
        was failing OPEN and could not have caught a real regression either. It now scrapes the
        single owner by AST and additionally asserts neither runner re-introduces a local copy.
      * `test_lane_tool_identity.py::test_stdin_devnull_is_not_regressed` and
        `test_nested_tty_noninteractive.py::test_symmetry_across_both_drivers` count
        `stdin=subprocess.DEVNULL` launch sites; both dropped 3 -> 2 because `run_checked`
        carried one of each driver's sites into `runner_shared` in E-05 (`grep -c` gives
        oc 4 -> 3, agy 3 -> 2, `runner_shared` 1, total preserved). Both now count across the
        owner set. THE THRESHOLDS ARE UNCHANGED AT 3: lowering them to 2 was the tempting
        one-character fix and would have silently accepted a future change that actually
        deleted a DEVNULL site, which is the exact `ttywedge` (g40w37) regression they exist to
        catch. `test_guard_fails_on_an_injected_regression` in the same file still passes.
    All three are outside this plan's Scope-Paths; justified in decisions 05-818uru-D5 and D6.
    This is one PATTERN seen three times and it will recur for every remaining `rununify` move.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: fingerprint match and `assertIs` for all seven. FOR `discover_plans` SPECIFICALLY (PR-302): paste evidence each runner still receives its OWN `PlanRecord` type after the move (`type(...) is oc_runipd.PlanRecord` from oc and `is agy_runipd.PlanRecord` from agy), and paste a record obtained through the OC path showing its `kind` field is still populated, since a shared constructor that dropped `kind` would silently disable orchestrator detection in `action_for` with no error. Confirm the two `PlanRecord` definitions were NOT unified.
  Paste the extended guard table showing all 39 names (child 01's five plus these 34) and TWO sabotage failures, one per runner. Then the closing measurements: both driver suites with counts, the full bare suite compared against your own pre-change measurement, and a package-wide AST check that each of the 34 has exactly ONE definition.
  - Observed evidence: All seven single-definition; STRICT fingerprints for the five clean and
    modulo-the-parameter for the two wrapped. AST, package-wide:
    ```
    _read_set                          shared ONLY          ['runner_shared.py:598']
    _read_order                        shared ONLY          ['runner_shared.py:609']
    resolve_plan_path                  shared ONLY          ['runner_shared.py:642']
    plan_bucket                        shared ONLY          ['runner_shared.py:672']
    describe_unresolved_plan_selector  shared ONLY          ['runner_shared.py:689']
    discover_plans                     shared + 2 wrappers  ['agy_runipd.py:1288', 'oc_runipd.py:2162', 'runner_shared.py:614']
    validate_manifest                  shared + 2 wrappers  ['agy_runipd.py:1295', 'oc_runipd.py:2169', 'runner_shared.py:744']
    ```
    `discover_plans` / `PlanRecord` (PR-302), the subtlest case, because the failure mode would
    be silent and type-shaped rather than a crash. The two definitions are UNCHANGED and still
    DISTINCT, and each runner still receives its OWN type:
    ```
    oc PlanRecord : ('id6','setid','status','order','path','rel_path','dependencies','kind','dependency_error','from_backlog')
    agy PlanRecord: ('id6','setid','status','order','path','rel_path','dependencies','dependency_error','from_backlog')
    distinct types: True

    oc_runipd    type is own PlanRecord=True  kind=child
    agy_runipd   type is own PlanRecord=True  kind=<absent>
    ```
    So oc's `kind` field IS still populated (`child`) - the field `action_for` reads to detect
    an orchestrator, which a shared constructor would have silently dropped. The mechanism is
    to inject the PARSER (`parse_plan_file`), not the record type, so the constructor is
    supplied per runner. The two `PlanRecord` were NOT unified; that is a class (c)
    reconciliation this plan may not perform.
    ONE ANNOTATION CHANGED, disclosed rather than hidden: `runner_shared` cannot NAME
    `PlanRecord` (importing either runner's is precisely the forbidden coupling), so
    `dict[str, PlanRecord]` became `dict[str, Any]` in `discover_plans`' signature and local.
    The harness maps that spelling back before comparing, so every other token in the body is
    still held to EXACT equality - if anything else had changed, the test would still fail.
    GUARD EXTENDED, and the table now covers 45 rows: child 01's 16 (`render_stream` x14 +
    `selectors` x2) plus 29 new `runner_shared` rows (25 clean-moved symbols + the 4 constants).
    Two absences are DECISIONS recorded in the table: the 8 WRAPPED symbols (a wrapper is a
    local `def` by construction, so it fails both halves by design; their equivalent guarantee
    is `SingleDefinitionTests`, which proves each wrapper is a single delegating statement and
    therefore a binding rather than a second body) and `disable_lane_prompt` (cannot move).
    SABOTAGE VERIFIED IN BOTH DIRECTIONS - a re-forked `plan_bucket` appended to each runner:
    ```
    ### SABOTAGE in oc_runipd:
    E  AssertionError: Lists differ: ['oc_runipd.py:6440 re-defines `plan_bucket`, which
       `runner_shared.py` already owns as `plan_bucket`'] != []
    E  ... IDENTITY MISMATCH. The runner does not see the owner's definition:
       'plan_bucket at 0x...> from agent_workflows.oc_runipd)'
    ### SABOTAGE in agy_runipd:
    E  AssertionError: Lists differ: ['agy_runipd.py:4369 re-defines `plan_bucket`, which
       `runner_shared.py` already owns as `plan_bucket`'] != []
    E  ... IDENTITY MISMATCH ... from agent_workflows.agy_runipd)
    ```
    Both halves fire in both directions; reverted, and `tests/test_runner_refork_guard.py` is
    `9 passed`.
    CLOSING MEASUREMENTS. Both driver suites at this HEAD:
    ```
    $ python3 -m pytest tests/test_oc_runipd.py tests/test_oc_runipd_cli.py tests/test_oc_runipd_shim.py
    7 failed, 98 passed in 10.03s
    $ python3 -m pytest tests/test_agy_runipd_cli.py tests/test_agy_runipd_shim.py
    6 failed, 18 passed in 2.61s
    ```
    The 13 failures are all in this lane's pre-existing baseline set (see below), not new.
    FULL SUITE, bare, at HEAD `dc1d9dee`:
    ```
    $ python3 -m pytest
    32 failed, 4265 passed, 3 skipped, 4 xfailed in 30.55s
    ```
    COMPARED AGAINST MY OWN PRE-CHANGE MEASUREMENT, not the plan's cited figure. This lane's
    baseline at HEAD `1ecc5891` was `32 failed, 4222 passed, 3 skipped, 4 xfailed`, and `comm`
    of the sorted FAILED sets returns EMPTY in the added direction: NOT ONE NEW FAILURE, and 43
    more tests pass. The plan cites `4092 passed` at HEAD `c8bb11ae`, which I could not
    reproduce and did not quote; all 32 baseline failures are environmental (17 caused by the
    driver's own `AW_EXECUTION_ROLE=worker`, which `tests/test_worker_role_refusal.py:225`
    explicitly asserts must NOT be set; 15 a pre-existing `test_run_viewer` isolation defect
    that discovers ambient `.aw/records/runs/` content). None touches a moved symbol. Fully
    diagnosed in decision 05-818uru-D1.
    `tests/test_runner_shared.py`: `43 passed`. `tests/test_runner_refork_guard.py`: `9 passed`.
    Sanitizer clean:
    ```
    {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean",
     "exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
    ```
    DUPLICATION REMOVED: `oc_runipd` 6874 -> 6437 lines (-437), `agy_runipd` 4801 -> 4366
    (-435), against a 787-line shared module that includes its own contract documentation.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: 8 E-leaves across 2 task groups, one concern throughout (move the proven-identical symbols into one module without changing behavior). It is at the upper end deliberately: the seams are sequential edits to the SAME two files, so splitting them into separate plans would guarantee the merge conflicts the orchestrator warns about, while each E-item remains one seam with its own V-item. If a reviewer judges E-07 (the 242-line lane seam) too large, split THAT item, not the plan.

Open questions: none. OQ-01 and OQ-02 were resolved by the maintainer 2026-09-03: use `runner_shared.py`, and inject each outside dependency explicitly via a THIN PER-RUNNER WRAPPER (OQ-02's refinement at review, which keeps the no-seam and no-mutable-state prohibitions intact while preserving E-02's fingerprint proof and leaving ~86 call sites untouched). No blocking question remains, so this plan is executable once approved AND once child 01 (`2r306y`) has executed.

This plan is `to-review` and requires explicit human approval before execution. It also has a hard prerequisite: `Item-Dependencies: executed:2r306y`, because it EXTENDS the symmetric guard child 01 installs.

Scope fence: touch ONLY `agent_workflows/runner_shared.py` (new), `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, `tests/test_runner_shared.py` (new), and `tests/test_runner_refork_guard.py` (child 01's, extended). Do NOT edit any class (c) DIVERGED symbol's body, in either runner, for any reason: touching one is this plan's stop condition, not a judgment call. THE ONE PERMITTED EXCEPTION, stated so it is not mistaken for a violation: E-03 re-parents `agy_runipd.StallTimeout` onto the shared `DriverError`, which changes its BASE CLASS without editing its body. Nothing else in class (c) may be touched, including the two `PlanRecord` definitions, which stay as they are. Do NOT change `render_stream.py` or `selectors.py`. Do NOT re-home the 40 oc-to-agy imports. Do not broaden CASUALLY; if the work GENUINELY requires a path outside the fence, MAKE THE EDIT AND JUSTIFY IT: `aw ipd finalize` refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-unmodified path carries a `--scope-ack`, so an unjustified widening is CAUGHT AT THE GATE rather than prevented by halting a run (maintainer ruling 2026-09-01; a scope fence DECLARES, it does not halt). Do NOT edit a sibling plan or the orchestrator.

Honesty rule (HARD MUST): paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. A "pure move" claim rests on the fingerprint fixture and the identity assertions, NOT on a grep and NOT on the suites being green: the suites were green while `DriverError` was two different classes. If any body changed, say so and treat it as a finding, because a changed body means this was not a move. AND DO NOT CALL THE FIVE WRAPPED SYMBOLS BYTE-IDENTICAL MOVES: they gained a parameter by design, so their evidence is fingerprint-modulo-the-parameter plus a behavior test, and reporting them under the strict claim would misrepresent exactly the five symbols carrying the most risk.

Execution contract: RE-READ both runner modules immediately before each seam and locate every symbol BY NAME, never by the line numbers in this plan. These are the highest-contention files in the repo: 21 unexecuted plans declare them, another session committed `render_stream.py` in `a396cb1b` during authoring, and six `lanectn` plans will edit them. Commit per SEAM, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Verify with `git diff --cached --name-only` before every commit and re-verify after any hook interruption. If a co-worker's in-flight change to a runner cannot be safely combined with a seam, STOP and report rather than overwriting.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
