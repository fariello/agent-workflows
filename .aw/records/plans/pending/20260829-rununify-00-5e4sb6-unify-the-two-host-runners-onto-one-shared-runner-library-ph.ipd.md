# IPD: unify the two host runners onto one shared runner library, phased behind a measured inventory

- Date: 2026-08-29
- Kind: orchestrator
- Concern: `oc_runipd.py` (3144 lines) and `agy_runipd.py` (3143 lines) are near-duplicate host runners that have DIVERGED. Measured at HEAD `c7f41b9`: 72 top-level symbols are shared, and only 35 of those are byte-identical while 37 have drifted; 2637 of `oc_runipd`'s 2843 top-level-definition lines sit in shared symbols, so roughly 93 percent of each runner is duplicated logic. Five features exist only in the opencode runner and seven only in the agy runner. Recent lifecycle work went into opencode alone, so agy silently lacks it. A generic `host_runner` and a host-abstraction layer already exist and BOTH runners import neither.
- Scope: ORCHESTRATOR - authors NO product code. Its own execution work is (E-01) the function-by-function inventory the backlog item demands as a deliverable, and (E-02) whole-Set verification. Children carry all extraction. This plan owns the child table, the sequencing decision against the 21 unexecuted plans that already declare these modules, the anti-regression contract every child inherits, and the Set completion criteria. Explicitly EXCLUDES changing runner BEHAVIOR: this Set is a de-duplication, and every divergence it reconciles must be reconciled to an existing behavior, never to a new one.
- Scope-Paths: .aw/records/plans/pending, .aw/records/research
- Item-Dependencies: none
- Status: to-review
- Set: rununify
- Order: 0
- Highest E allocated: 02
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 5e4sb6
- Blocks-Release: next
- From-Backlog: dhuape

## Workflow history

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.
- 2026-08-30 to-review (opencode (its_direct/pt3-claude-opus-5-1m-us)): graduated from backlog `dhuape` during the blocking-backlog graduation sweep. The item's divergence snapshot was RE-MEASURED rather than trusted, and it was materially understated: an AST comparison shows 37 of 72 shared symbols have drifted, not a handful, and the item's own "def-name comm" method could not see this because a drifted function still has the same name (F1). Two of the item's premises were corrected by measurement: the host-abstraction modules it nominates as the extraction home are a GENERATOR and an orchestration layer, not a process runner, while the actual generic worker runner it does not mention (`host_runner`) is the real precedent (F4). The dominant risk turned out not to be the refactor itself but SEQUENCING: 21 unexecuted plans already declare these two modules in Scope-Paths, and at least eight of them explicitly defer TO this item while landing duplicated code in both runners meanwhile (F5). That reframes this plan's central job and is why it is an orchestrator with an inventory-first gate rather than a single refactor child.

## Goal

Get to ONE implementation of everything that is not host-specific, without changing what either runner does and without colliding with the large body of approved work already queued against these files. The inventory comes first because the backlog item asks for it as a deliverable and because no honest child scope can be drawn until the common/specific/divergent partition is known.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

This orchestrator authors NO product code. Its execution work is the inventory deliverable and the whole-Set verification; the children carry every extraction.

### Task group 1: the inventory, then the Set

- [ ] E-01 Produce the function-by-function INVENTORY the backlog item names as its first required deliverable, as a durable research artifact under `.aw/records/research/` created with `aw research new` (do not hand-name it). Classify EVERY top-level symbol in both runners as (a) COMMON, identical or trivially unifiable; (b) HOST-SPECIFIC, genuinely tied to one CLI's invocation, event stream, or binary resolution; or (c) DIVERGED, present in both but drifted, which is the class the item calls a divergence bug and which measurement shows is the LARGEST class at 37 symbols. For each class (c) symbol, record which side is authoritative and WHY, with the evidence, since that judgment is the actual intellectual work of this Set and must not be improvised per-child later. Use a mechanical method, not reading: an AST comparison of per-symbol source, plus a host-token-normalized comparison to separate "differs only by host naming" from "differs substantively" (measurement showed only ONE symbol differs by naming alone, so this distinction matters). The inventory must state the measured totals and the HEAD they were taken at, because they will move.
  - Depends on: none
  - Expected outcome: a committed research artifact partitioning all symbols into the three classes with a per-symbol authoritative-side decision and evidence for class (c); the totals and their measurement HEAD are recorded; the method is reproducible by a reader.
  - Execution state: pending

- [ ] E-02 After the children execute, verify the whole Set: everything classified COMMON in E-01 has exactly ONE implementation (proven by an AST-level duplicate-symbol check across both modules, not by grep), each runner retains only its host-specific surface, every class (c) divergence was reconciled to the authoritative side recorded in E-01, and NO runner behavior changed. The behavior-preservation proof is the load-bearing one: the full driver test suites for both hosts must pass, and the Set must not have introduced a single new user-visible behavior. Also confirm the feature-parity gaps the item names were closed in the direction E-01 decided, not silently dropped.
  - Depends on: none
  - Expected outcome: one implementation per common symbol (AST-verified); both driver suites green; every E-01 class (c) decision honored; no behavior change claimed or found; the opencode-only lifecycle features are present for both hosts or their absence is explicitly justified per-symbol.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

The child breakdown is DELIBERATELY NOT FIXED HERE, and that is a decision rather than an omission. E-01's inventory determines the honest seams, and inventing child scopes before measuring which of the 37 drifted symbols are reconcilable would be exactly the guesswork this plan exists to avoid. What IS fixed is the shape and the constraints:

| Order | What it does | Depends on |
|---|---|---|
| 01 | Extract the class (a) COMMON symbols that are already byte-identical (measured: 35 of them) into the shared module. Pure move, zero reconciliation, so it is provably behavior-neutral and can be verified by an identity assertion. | E-01 inventory |
| 02+ | One child per COHESIVE GROUP of class (c) DIVERGED symbols, each reconciling to the authoritative side E-01 recorded. Grouped by seam (for example prompt construction, selector expansion, run initialization), NOT one child per symbol and NOT one giant child. | 01 |
| last | Close the named feature-parity gaps (the opencode-only lifecycle/self-finalize surface, and any agy-only helper E-01 classifies as common) in the direction E-01 decided. | 02+ |

Hard constraints every child inherits, stated once here:
- A child may NOT change behavior. Every reconciliation goes to an EXISTING behavior on one side, chosen and justified in E-01.
- A child must land in BOTH runners or in neither. A one-sided extraction recreates the divergence it is removing.
- No child may exceed one cohesive seam. `execute_item` alone is 572 lines and is the single largest shared symbol; it may need a child to itself, and if E-01 shows it must be split further, split it.
- Children are SEQUENTIAL, not parallel, because they all edit the same two files. Declaring them parallel would guarantee the merge conflicts this repo is already suffering from.

## Completion criteria (the whole Set is done only when)

- Every symbol E-01 classified COMMON has exactly ONE implementation, verified at the AST level rather than by grep (the `2c122z` plan-review found a `grep "return True"` proof that could never fail; do not repeat that class of unfalsifiable evidence).
- Each runner contains only its host-specific surface plus imports of the shared library.
- Every class (c) divergence was reconciled to the side E-01 named authoritative, with the reconciliation recorded.
- The opencode-only lifecycle features either exist for both hosts or carry a per-symbol justification for remaining host-specific.
- NO behavior changed. Both hosts' driver suites pass, and the Set claims no new capability.
- The shared library is imported by both runners, and a test asserts that neither runner defines a symbol the shared library owns (the anti-regression guard against silent re-forking).

## Cross-IPD validation

- CID-1: exactly one implementation per common symbol, AST-verified across both modules.
- CID-2: both drivers import the shared library; neither redefines a shared symbol.
- CID-3: every child landed symmetrically; no child left one host behind.
- CID-4: no behavior change; both driver suites green at every child boundary, not merely at the end.

## Project conventions discovered (Step 0)

- The runners bypass the host-abstraction layer entirely, exactly as the item says: `oc_runipd.py` and `agy_runipd.py` contain ZERO references to `host_adapters`, `host_launchers`, `host_capability_registry`, or `host_runner`.
- But the item's nominated extraction home is WRONG, which changes the design. `host_adapters` describes itself as "a PURE generator" that emits Agent Skills packages and adapter metadata, and `host_launchers` is "thin launchers over the generic `host_runner`" for the Set coordinator. Neither is a process runner for a driver's turn loop. Folding driver logic into them would put runtime behavior inside a generator.
- The RIGHT precedent exists and the item does not mention it: `agent_workflows/host_runner.py` is a 349-line "generic structured host worker runner" whose docstring states its purpose as "One evidence-gated worker interface the Set coordinator uses to start, monitor, time-out, cancel, and collect a VALIDATED terminal envelope from an isolated task, on any supported host, without duplicating semantics per host". That is the same problem statement as this item, solved once for a different caller. Study it before choosing the shared module's shape; a NEW module (the item's `runipd_core`/`host_runner` candidate) is likely correct, but it should follow this one's conventions.
- The repo has a NAMED precedent for taking a narrow slice instead of waiting for this refactor: plan `97df1z` extracts ONE predicate into a new `agent_workflows/plan_readiness.py` shared by both runners, and records in its own Deferred section that full unification is "tracked by backlog `dhuape`; this plan shares ONLY this predicate to fix the bug without taking that refactor". That module does not exist yet, so `97df1z` will CREATE the first shared-runner-helper module. This Set should extend that module or explicitly supersede its placement, not open a third home.
- The `terminate_process` copies are near-identical in both runners with escalating SIGINT/SIGTERM/SIGKILL over a process group, and `runstop` Phase 0 already records that they are byte-identical apart from a docstring line, which is why its single-implementation check must be repo-wide. Coordinate: that plan and this Set are both trying to de-duplicate the same function.
- Both runners are under ACTIVE concurrent edit. At authoring time a live `aw oc run wtiso` process owned five lane worktrees, and uncommitted changes to both runner modules and both runner test modules were present in the working tree from another session.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | both runner modules | THE ITEM UNDERSTATES THE DIVERGENCE, and its method is why. It reports "~954 changed lines" and a handful of present-in-one-not-the-other functions found by "def-name comm". But a name comparison cannot see a function that exists in both and has DRIFTED. An AST comparison of per-symbol source at `c7f41b9` shows 72 shared symbols of which only 35 are byte-identical and 37 have diverged. So the divergence class the item calls a bug is the LARGEST class, not an exception list of five. | AST per-symbol digest comparison: `shared symbols: 72 / BYTE-IDENTICAL: 35 / DIVERGED: 37`; raw line diff of the two committed files: 1229 differing lines |
| F2 | HIGH | both runner modules | THE DUPLICATION IS ~93 PERCENT, which sizes the work honestly. Of `oc_runipd`'s 2843 lines inside top-level definitions, 2637 sit in symbols that also exist in agy; only 206 lines are opencode-only and 294 are agy-only. So this is not a refactor with a large shared core, it is two copies of one program with small host-specific tips. | measured line sums per symbol class at `c7f41b9` |
| F3 | HIGH | shared symbols | THE WORK CONCENTRATES IN A FEW HUGE FUNCTIONS, so child sizing must follow the measurement rather than the symbol count. The largest shared symbols are `execute_item` at 572 lines, `build_parser` at 201, `expand_selectors` at 173, `initialize_run` at 149, and `run_queue` at 117 (opencode side), and `run_queue` differs by 38 lines between hosts while `integrate_lane_branch` differs by 20. A child per symbol would be absurd for the small ones and impossible for `execute_item`. | per-symbol line counts and deltas at `c7f41b9` |
| F4 | HIGH | `host_adapters.py`, `host_launchers.py`, `host_runner.py` | THE ITEM'S PROPOSED HOME IS THE WRONG LAYER, and the right precedent is a module the item never mentions. `host_adapters` is self-described as "a PURE generator" for skills/adapter metadata; `host_launchers` is orchestration over `host_runner`. Neither runs a driver turn. Meanwhile `host_runner.py` already solves "one worker interface on any supported host without duplicating semantics per host" for the Set coordinator, which is precisely this item's goal for a different caller. Folding driver logic into the generator would be a layering violation; ignoring `host_runner`'s conventions would duplicate a solved design. | the three modules' docstrings; zero imports of any of them in either runner |
| F5 | HIGH | `.aw/records/plans/pending/` | SEQUENCING IS THE DOMINANT RISK, not the refactor. TWENTY-ONE unexecuted plans declare `oc_runipd.py` or `agy_runipd.py` in `Scope-Paths` (17 approved, 2 reviewed, 2 to-review), including the six-child `runstop` Set, the six-child `wtiso` Set, the four-plan `lanetruth` Set, and several singletons. At least EIGHT of them explicitly defer to `dhuape` by name while landing duplicated code in both runners in the meantime, with phrases like "this child lands the same call in both, no de-duplication" and "Driver unification (backlog `dhuape`)". So every day this Set waits, the duplication GROWS by design, and every day it runs first, it invalidates 21 plans' line citations and scope fences. | measured: 21 plans matched on `Scope-Paths`; the deferral text quoted from `runstop-00`, `runstop-01`, `runstop-03`, `runstop-06`, `fullauto-01` among others |
| F6 | MED | plan `97df1z` | The FIRST shared-runner-helper module is already scoped but does not exist yet: `97df1z` will create `agent_workflows/plan_readiness.py` and share exactly one predicate between the drivers, recording that full unification belongs to this item. This Set must extend or supersede that placement rather than opening a third location, or the repo ends up with a shared-helper module per bug fix, which is the same drift at a different granularity. | `97df1z` Scope-Paths and Deferred section; `plan_readiness.py` absent at `c7f41b9` |
| F7 | MED | `runstop-01` (`2ouj70`) | An OVERLAP that must be resolved rather than raced: `runstop` Phase 0 also de-duplicates `terminate_process`, recording that both runners carry byte-identical copies and that its single-implementation check must therefore be repo-wide. Two plans independently de-duplicating the same function will conflict. | `runstop-01`'s conventions section |
| F8 | MED | the item's feature list | The item's specific gap list VERIFIED as still accurate for names: opencode-only are `action_for`, `finalize_orchestrator`, `_read_kind`, `_set_children_all_executed`, `run_opencode`; agy-only are `render_agy_event`, `resolve_agy`, `run_agy_turn`, `_one_line`, `_strip_ansi`, plus `Heartbeat` and `Palette` classes the item does not list. Note `run_opencode` and `run_agy_turn` are the genuinely host-specific turn drivers and are correctly NOT common; the item's framing of `run_opencode` as a missing feature is a category error. | symbol-set difference at `c7f41b9` |
| F9 | LOW | working tree at authoring time | Both runner modules AND both runner test modules had uncommitted changes from a concurrent session, and a live driver process owned five lane worktrees. Any executor must assume contention on exactly these files. | `git status` and `ps` at authoring time |

## Proposed changes (ordered, validatable)

1. Measure and publish the three-class inventory with per-symbol authoritative-side decisions (E-01).
2. Decide the sequencing against the 21 queued plans (OQ-01) before any child runs.
3. Extract the 35 byte-identical symbols as a provably behavior-neutral first child.
4. Reconcile the 37 diverged symbols in cohesive, sequential groups, each to a decided authoritative side.
5. Close the feature-parity gaps in the decided direction.
6. Verify one-implementation-per-common-symbol at the AST level and both suites green (E-02).

## Deferred / out of scope (with reason)

- CHANGING BEHAVIOR is out of scope for the entire Set. This is de-duplication; any behavior question a child uncovers becomes a separate backlog item rather than an opportunistic fix, because a refactor that also changes behavior cannot be verified by "both suites still pass".
- A unified top-level `aw run` or `aw run stop` facade is out of scope, even though `runstop`'s orchestrator defers that verb to this item. Unifying the LIBRARY does not require unifying the CLI surface, and merging the two user-facing commands is a separate, user-visible decision.
- The `wtiso` Phase 3 resolver consolidation, which also touches both runners, stays with that plan. This Set must not absorb it.
- `terminate_process` de-duplication overlaps with `runstop` Phase 0 (F7). Whichever executes second must find the function already shared; do not both extract it.

## Scope check

- Over-scope: none. This orchestrator writes only a research artifact and its own plan record; it declares no product path, which is correct for an orchestrator that authors no code.
- Under-scope: THE CHILD PLANS ARE NOT YET WRITTEN, deliberately. Their scopes depend on E-01's measurement, and pre-committing them would be guesswork. This is an explicit, recorded gate: the Set cannot proceed past E-01 until the children are authored from the inventory and reviewed. A reviewer should hold this plan to that, and should NOT approve any child that was written before the inventory existed.
- The children WILL declare `agent_workflows/oc_runipd.py`, `agent_workflows/agy_runipd.py`, the new shared module, and both runner test modules. That fence must be stated per child, not inherited vaguely.

## Required tests / validation

- E-01's inventory is validated by REPRODUCIBILITY, not by assertion: a reader must be able to re-run the stated method and get the stated partition. Include the method (AST per-symbol comparison plus host-token normalization) and the measurement HEAD in the artifact.
- Each child must show both hosts' driver suites green BEFORE and AFTER its change, since behavior preservation is the whole contract. Locate the suites by name (`tests/test_oc_runipd.py` and the agy runner tests) and paste counts for both.
- CID-1's proof must be AST-based. A grep for a symbol name is not proof of single implementation, because a name can legitimately appear in an import, a call, or a docstring. This requirement exists because a sibling plan's review caught exactly this class of unfalsifiable grep evidence.
- The anti-re-forking guard must be a TEST, not a convention: assert that neither runner module defines a top-level symbol the shared library owns. Without it, the next bug fix re-forks a helper and nothing notices.
- INVOKE THE SUITE BARE: `python3 -m pytest` and `python3 -m pytest -m ""` (or `make test` / `make test-all`). Do NOT add `-n auto` or a second `-q`.
- BASELINE IS A MEASUREMENT, NOT A CONSTANT. Fast suite during this sweep at `df731f1`: `2880 passed, 3 skipped, 4 xfailed`. Both runner modules and both runner test modules were dirty from a concurrent session at authoring time, so expect your baseline to differ; take your own with its HEAD.
- `aw check-local-leaks . --agent` clean; `aw ipd lint --phase pre-transition` conforming for this plan and every child.

## Spec / documentation sync

- No existing spec pins the two-runner structure, so no spec text change is forced. However, spec `25kzda` (aw-run deterministic run and verify) governs runner behavior generally; the executor should record that this Set changed structure only and left that spec's requirements untouched.
- If the shared module lands as a new file, its module docstring must state the same single-implementation rule this orchestrator enforces, so a future contributor adding a runner helper knows where it goes. Follow `host_runner.py`'s docstring conventions (F4).
- The `dhuape` item's own framing that the host-abstraction layer is the natural home should be corrected in the record (F4), so a later reader does not re-derive the wrong plan from the closed item.

## Open questions

### OQ-01: Does this Set run BEFORE or AFTER the 21 queued plans that already declare these modules?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: THIS IS THE ONE DECISION THIS PLAN CANNOT MAKE FROM REPOSITORY EVIDENCE, because it is a priority and risk-appetite call, which is the maintainer's to make. The evidence is laid out so the decision is informed. Running this Set FIRST invalidates the line citations, scope fences, and in some cases the E-item structure of 21 unexecuted plans, including three multi-child Sets that are already approved and one that is mid-flight in a LIVE run; the cost is a large re-review burden and a real chance of silently breaking an approved plan's assumptions. Running it LAST means the duplication keeps GROWING by design, because at least eight of those plans explicitly land the same code in both runners and defer de-duplication to this item, so the 37-symbol divergence will be larger and the reconciliation decisions harder. A THIRD option exists and may be best: run it INTERLEAVED, taking only the 35 byte-identical symbols now (a provably behavior-neutral extraction that touches no logic any queued plan reasons about) and deferring the 37 diverged symbols until the `runstop`, `wtiso`, and `lanetruth` Sets have landed. RECOMMENDATION: the interleaved option, because it stops the bleeding on the easy 35 without invalidating a single approved plan's reasoning, and because the diverged 37 are exactly the symbols those Sets are actively editing. The maintainer should confirm or override; this plan does not proceed on a guess about their sequencing priorities.

### OQ-02: Where does the shared library live, and does it absorb `plan_readiness.py`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: A NEW dedicated module, following `host_runner.py`'s conventions, and it SUBSUMES the placement of `plan_readiness.py` rather than coexisting with it. Resolved from evidence. The item's candidates `host_adapters`/`host_launchers` are eliminated by F4: they are a generator and an orchestration layer, so driver runtime logic does not belong in them. `host_runner.py` is the right precedent but the wrong home, because it serves the Set coordinator's worker-envelope contract rather than a driver's turn loop; copy its conventions, do not extend it. And `plan_readiness.py` (created by plan `97df1z`, F6) is the first shared-runner-helper module, so the correct end state is ONE shared runner library that this Set either absorbs it into or explicitly designates as part of. Leaving both is how a repo acquires a shared-helper module per bug fix, which is the same drift at finer granularity. E-01 must state which of absorb-or-designate it chose.

### OQ-03: Which side wins for each of the 37 diverged symbols?

- Blocking: no
- Status: deferred
- Owner: E-01 of this plan (trigger: the inventory's per-symbol authoritative-side decisions)
- Resolution or deferral rationale: DELIBERATELY DEFERRED TO E-01, which is this plan's first execution item, rather than guessed here. This is not an evasion: a per-symbol authoritative-side decision requires reading 37 pairs of implementations, which is the inventory's whole purpose and is exactly what the backlog item asks for as its deliverable. What IS decided here is the RULE those decisions must follow: reconcile to an EXISTING behavior on one side, never to a new synthesis, and record the evidence per symbol. The default presumption, to be overridden only with a stated reason, is that the opencode side is authoritative for lifecycle and finalize logic (because the item establishes and measurement confirms that recent lifecycle work landed there and agy never received it) and that neither side is presumed authoritative for anything else.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the created research artifact's path, showing it was created by `aw research new` rather than hand-named. Paste the three-class partition with per-symbol entries and the measured totals with the HEAD they were taken at. Paste the reproducible method and a transcript of it running. For class (c), paste at least the authoritative-side decision and its one-line evidence for the five largest diverged symbols, and confirm all 37 carry a decision. State which of absorb-or-designate you chose for `plan_readiness.py` per OQ-02. An inventory that classifies symbols without deciding authority for class (c) does NOT satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the AST-level duplicate-symbol check output proving one implementation per common symbol, and explicitly confirm it is AST-based rather than grep-based. Paste both hosts' driver suite results with counts and their HEAD. Paste the anti-re-forking TEST passing, and show it FAILING when a shared symbol is deliberately redefined in one runner. Paste a per-symbol confirmation that every class (c) reconciliation matched E-01's recorded decision, and for any that did not, the recorded reason. Finally, state plainly that NO behavior changed and back it with the suites rather than assertion; if any behavior did change, this item FAILS and the change belongs in its own plan.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required for this orchestrator (2 E-leaves, 1 task group). Note for the reviewer: the SET is large, and its right-sizing is enforced through the child constraints in the child table rather than here, because the child boundaries are legitimately unknown until E-01 measures them.

BLOCKING GATE, and it is genuine rather than ceremonial: OQ-01 (sequencing against the 21 queued plans) is UNRESOLVED and is a maintainer decision. No child may be authored or executed until it is answered. This plan records a recommendation (the interleaved option: take the 35 byte-identical symbols now, defer the 37 diverged ones until the `runstop`, `wtiso`, and `lanetruth` Sets land) but will not proceed on a guess, because the wrong choice either invalidates approved multi-child Sets or lets the duplication keep growing.

SECOND GATE: the children do not exist and must be authored FROM E-01's inventory, not before it. A reviewer should refuse any child plan whose scope was written without the measurement behind it.

Open questions: OQ-02 is resolved from evidence (a new dedicated module following `host_runner.py`'s conventions, subsuming `plan_readiness.py`'s placement); OQ-03 is deliberately deferred to E-01 with the decision RULE fixed here; OQ-01 is the one open question and it is the maintainer's.

Scope fence for THIS plan: write only the E-01 research artifact and this plan's own record. Author NO product code, touch NEITHER runner, and do not create the shared module. If executing this orchestrator seems to require editing a runner, that work belongs to a child that does not exist yet, so STOP and report.

Honesty rule (HARD MUST): when you report tests or validation passed, paste the ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Never claim a pass you did not run. Specific to this Set: do NOT claim a de-duplication is complete on the basis of a grep, and do NOT describe a behavior change as a refactor.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, and never push. This Set is the highest-collision work in the repo: both runner modules and both runner test modules were dirty from another session at authoring time, a live driver owned five lane worktrees, and 21 unexecuted plans declare these files. Every child must re-read both modules immediately before editing, locate code by SYMBOL (line numbers in any citation will have moved), and STOP rather than overwrite a co-worker's in-flight change.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand. Do not create or push a git tag or release.
