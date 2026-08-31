# IPD: Multi-type selector resolution, mixed-type gate, and DAG queue scheduler

- Date: 2026-08-30
- Kind: child
- Concern: `runipd` currently only resolves and executes single IPDs or IPD queues, without support for specs, backlog items, prompt files, or DAG dependency topological scheduling.
- Scope: Implement multi-type selector resolution across all 7 canonical artifact types, the mixed-type confirmation gate, the unified per-type dispatch table, and the pure DAG queue scheduler with dependency-not-met cascade. Implements spec 25kzda Sections 2.1-2.6, 3.1-3.6, and 5.4.
- Scope-Paths: agent_workflows/run_selector.py, agent_workflows/run_scheduler.py, agent_workflows/run_dispatch.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_run_selector_and_queue.py
- Item-Dependencies: executed:bmh754
- Status: to-review
- Set: detrun
- Order: 3
- Highest E allocated: 08
- Author: antigravity
- Id: kaygwo
- Blocks-Release: next

## Workflow history
- 2026-08-31 to-review (aw set): REVERTING MY OWN ERRONEOUS APPROVAL. I set this approved on 2026-08-30 from the maintainer's blanket instruction 'I APPROVE all the reviewed IPDs', which swept up a plan whose OWN newest /plan-review verdict is REJECT - NEEDS REPLAN. The --by-human attestation was real but the maintainer plainly did not intend to approve a do-not-execute plan; approving on status alone without reading each verdict was my mistake. Flagged by a peer agent (comms fyi 20260831-0126-01) and independently verified: all FIVE detrun plans carry REJECT, not just bmh754. Returning to to-review so 'approved' does not license a rebuild of shipped machinery.
- 2026-08-31 approved (aw set): set Item-Dependencies to executed:bmh754
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- 2026-08-30 /plan-review pass 2 (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN reaffirmed, residue HALVED; PR-301..PR-307. SELF-CORRECTION (PR-301): pass 1 called this 'the least duplicated child, the most salvageable' with E-01..E-04 as clean residue. Too generous. E-01 is SHIPPED: agent_workflows/selectors.py (512 lines) is documented as 'the ONE selector-to-file resolver for the whole package' and its _PRECEDENCE tuple ('path','id6','setid','status','stem','substring') is byte-identical to the precedence E-01 proposes, with UNIQUE_KINDS + Resolution.is_ambiguous already rejecting ambiguous unique selectors and KNOWN_PRIMARY_TYPES already spanning every artifact type. The plan's own Step 0 even calls that precedence the house standard, then proposes to reimplement it. Pass 1 also cited the WRONG module for the DAG overlap: run_engine.get_runnable_steps schedules steps WITHIN a run by depends_on step ids; the correct citation is ipd_set_plan.py (execset iy1a2g), the shipped cross-IPD Set graph compiler, which already does child->child edges, cycle detection, frozen manifests, parallel/serial eligibility, and - in _propagate_blocked - exactly E-06's cascade ('all its transitive descendants' blocked while 'independent approved siblings are NOT in here'). One real seam survives: the shipped compiler derives edges from the orchestrator ## Child IPDs table and greps ZERO for Item-Dependencies, so declared-graph scheduling is a SURGICAL change to it, not a new module (OQ-02, blocking). NEW COLLISION (PR-303/OQ-03): E-04's backlog-graduation half overlaps APPROVED bkclose-01 (zhr6mc), which owns runner-side From-Backlog reading and item closure; two plans must not split one lifecycle across both runners. Other new findings: E-04's spec handoff is BLOCKED because it emits From-Spec, still absent from META_RECOGNIZED (sibling bmh754), so its generated IPD would fail IPD-M103; E-07 silently promises --with-dependencies and --follow-generated, neither of which exists on aw oc run; the plan uses dependency_not_met throughout while the runner's real state is dependency-blocked (invented spelling has zero hits); and BOTH required validations were unachievable, one presupposing its own feature (--type does not exist). Residue narrowed from four items to two plus a thin wrapper: the mixed-type gate (verified ZERO hits for RUN-MIXED-TYPES/--allow-mixed/'run mixed', the cleanest win) and the Section 3 dispatch table with only the spec half of E-04. All 8 E-items blocked with notes, all 8 V-items NOT TO BE COLLECTED, 6 prohibitions and a scope fence recorded. Lint conforming at author and review-finalize. NO-GO pending maintainer answers to OQ-02 and OQ-03.
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001/PR-003. Least-duplicated child but still not executable: E-05/E-06 duplicate APPROVED `lanetruth-03` (`8guhs0`), which explicitly owns runner consumption of the shared dependency predicate and the 25kzda 2.9/5.4 runtime satisfaction semantics; a DAG release surface also ships (`run_engine.get_runnable_steps`, run_engine.py:273). E-07 collides with APPROVED `rununify` (`5e4sb6`). The three proposed `run_*` modules were authored without inventorying the ELEVEN shipped `run_*` modules. Salvageable residue: E-01..E-04 (multi-type selector, mixed-type gate, dispatch table). Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened selector precedence, mixed-type confirmation, dispatch handlers, tiebreaking rules, and DAG cascade algorithms.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE. Verdict unchanged; pass-1 reasoning SHARPENED and one pass-1 judgement
RETRACTED (/plan-review 2026-08-30 pass 2, PR-301).** Verified at HEAD `5d01b6db`.

RETRACTION OF A PASS-1 JUDGEMENT: pass 1 called this "the LEAST duplicated child and the most
salvageable" and named E-01..E-04 as clean residue. That was too generous. **E-01's core is SHIPPED.**
`agent_workflows/selectors.py` (512 lines) is documented as "the ONE selector-to-file resolver for the
whole package", and it already implements exactly what E-01 proposes:

| E-01 proposes | Shipped in `selectors.py` |
| --- | --- |
| precedence `path, id6, set, status, stem, substring` | `_PRECEDENCE = ('path','id6','setid','status','stem','substring')` - identical, in order |
| reject ambiguous unique selectors | `UNIQUE_KINDS = {'path','id6','stem'}` + `Resolution.is_ambiguous` |
| resolution across artifact types | `KNOWN_PRIMARY_TYPES` = plans, specs, backlog, prompts, research, releases, walkthroughs, roadmaps, comms |

E-01's own `## Project conventions discovered` even asserts this precedence "is the house standard
across all `aw find` and selector commands" - which is true, and is precisely why it must be CONSUMED,
not reimplemented in a new `run_selector.py`. So the pass-1 claim that E-01 was unbuilt was wrong.

ALSO RETRACTED, in the OPPOSITE direction: pass 1 cited `run_engine.get_runnable_steps` as the shipped
DAG overlap. That citation was WEAK - it schedules steps WITHIN one run by `depends_on` step ids, not
cross-artifact work items. The far stronger and correct citation is `agent_workflows/ipd_set_plan.py`,
the shipped IPD-Set graph compiler (execset Order `iy1a2g`), which ALREADY builds a cross-IPD DAG with
child->child edges, detects cycles, freezes a manifest, decides parallel-vs-serial eligibility, and
implements exactly the cascade E-06 proposes: `_propagate_blocked` marks a gated child plus "all its
transitive descendants" while "independent approved siblings are NOT in here". E-05/E-06 would be a
second cross-IPD scheduler and a second cascade.

ONE REAL DIFFERENCE, and it is the only defensible seam left in task group 3: the shipped Set compiler
derives cross-IPD edges from the orchestrator's `## Child IPDs` TABLE (`ipd_schema.H_CHILD_IPDS`), and
greps to ZERO hits for `Item-Dependencies`. So "schedule from the declared `Item-Dependencies` graph
instead of the orchestrator table" IS unbuilt - but that is a small, surgical change to the SHIPPED
compiler, and approved `lanetruth-03` (`8guhs0`) already owns the runner half of it.

UNCHANGED FROM PASS 1 (re-verified):
- E-05/E-06 collide with APPROVED `lanetruth-03` (`8guhs0`), which owns runner consumption of the
  shared `Item-Dependencies` predicate and the 25kzda 2.9/5.4 runtime satisfaction semantics. Its own
  review pinned the static-vs-runtime split as finding F7.
- E-07 edits BOTH `oc_runipd.py` and `agy_runipd.py`, fighting APPROVED `rununify` (`5e4sb6`) (OQ-03).

NEW COLLISION FOUND THIS PASS: E-04's backlog-handoff half overlaps APPROVED `bkclose-01` (`zhr6mc`),
whose scope is teaching both runners to read `From-Backlog:` and close a backlog item when the run
executes the last plan carrying it. Two approved plans must not both own runner-side backlog lifecycle.

WHAT IS GENUINELY UNBUILT AND WORTH KEEPING, narrowed from four items to two:
- E-02, the mixed-type confirmation gate: verified ZERO hits for `RUN-MIXED-TYPES`, `--allow-mixed`,
  and the `run mixed` phrase. Wholly unbuilt, self-contained, and genuinely valuable.
- E-03/E-04, the per-type/status dispatch table: no runner-side dispatch table exists, and this is the
  heart of spec Section 3. Keep it, but build it ON `selectors.py` for resolution, hand the backlog
  half to `bkclose-01`, and keep the spec-to-IPD handoff (which needs `From-Spec`, still unbuilt per
  sibling `bmh754`).

Original goal, retained for the record: provide the core selector resolution, dispatch, and DAG
scheduling layer for `aw <host> run`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Multi-type selector resolution and mixed-type gate

- [ ] E-01 Create `agent_workflows/run_selector.py` implementing pure multi-type selector resolution across all 7 canonical artifact types (`ipd`, `spec`, `backlog`, `prompt`, `research`, `release`, `walkthrough`).
  - Depends on: none
  - Expected outcome: **DO NOT BUILD (pass-2 retraction of pass-1's 'salvageable' call). SHIPPED as `agent_workflows/selectors.py` (512 lines), documented as 'the ONE selector-to-file resolver for the whole package'. Its `_PRECEDENCE` is byte-for-byte the precedence this item proposes, `UNIQUE_KINDS`+`Resolution.is_ambiguous` already reject ambiguous unique selectors, and `KNOWN_PRIMARY_TYPES` already spans plans/specs/backlog/prompts/research/releases/walkthroughs. Creating `run_selector.py` would fork the canonical resolver (P8). CONSUME it. The only genuine gap is the runner-facing policy on top: the `all`-defaults-to-IPDs-only rule and the exit-code mapping (2 for zero matches, 4 for ambiguity), which are thin wrappers, not a module.** Original expected outcome: Resolution applies canonical precedence (path, id6, set, status, stem, substring), enforces `all` default (IPDs only unless `--type` specified), rejects ambiguous unique selectors (exit 4), handles zero matches (exit 2), and deduplicates by `(type, stable_id, canonical_path)`.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

- [ ] E-02 Implement the mixed-type confirmation gate in `agent_workflows/run_selector.py` and wire into CLI runner entry points.
  - Depends on: E-01
  - Expected outcome: **KEEP - the single cleanest surviving item in this plan. Verified WHOLLY UNBUILT: `RUN-MIXED-TYPES`, `--allow-mixed`, and the exact `run mixed` phrase all grep to ZERO hits. Self-contained and valuable. Build it against `selectors.py` output rather than a new resolver, and note it needs no new module of its own.** Original expected outcome: Prints sorted item count and action breakdown preview; requires exact `run mixed` confirmation interactively and `--allow-mixed` in unattended mode, refusing work with `[RUN-MIXED-TYPES]` if unconfirmed.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

### Task group 2: Per-type and status dispatch table

- [ ] E-03 Create `agent_workflows/run_dispatch.py` implementing the complete per-type lifecycle dispatch table from spec Section 3 for IPDs, specs, backlog items, prompt files, and non-runnable records.
  - Depends on: E-01
  - Expected outcome: **KEEP THE SUBSTANCE, NOT THE MODULE. No runner-side per-type/status dispatch table exists, and this is the heart of spec Section 3, so the work is real. But it must consume `selectors.py` for typing/resolution and must be reconciled with the shipped `run_*` family before choosing a home; `run_dispatch.py` as a brand-new sibling to eleven existing `run_*` modules needs justification it does not give.** Original expected outcome: Evaluates item type and status to choose next legal action packet, handling IPD review/execute, spec review/authoring, backlog graduation, prompt contract verification, and non-runnable skips.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

- [ ] E-04 Implement spec IPD-authoring action (`approved` spec -> author `to-review` IPD with `From-Spec: <id6>` and `Blocks-Release`) and backlog graduation action (`open` backlog -> author spec/IPD with `From-Backlog: <id6>` -> `graduated`).
  - Depends on: E-03
  - Expected outcome: **SPLIT REQUIRED - NEW COLLISION FOUND (pass 2). The spec-to-IPD half is legitimate but BLOCKED: it emits `From-Spec: <id6>`, which sibling `bmh754` verified is still absent from `ipd_schema.META_RECOGNIZED`, so the generated IPD would fail lint with `IPD-M103`. The backlog-graduation half OVERLAPS APPROVED `bkclose-01` (`zhr6mc`), which owns runner-side `From-Backlog` reading and item closure. Hand the backlog half to that plan; keep the spec half sequenced after `From-Spec` lands.** Original expected outcome: Handoffs generate conformant artifacts, preserve release blocker gates, and perform atomic tool-authored status transitions.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

### Task group 3: Pure DAG queue scheduler and cascade engine

- [ ] E-05 Create `agent_workflows/run_scheduler.py` implementing the pure DAG queue scheduler driven by declared `Item-Dependencies`.
  - Depends on: E-01, E-03
  - Expected outcome: **DO NOT BUILD (REPLAN). A cross-IPD DAG scheduler ALREADY SHIPS: `ipd_set_plan.py` (execset Order `iy1a2g`) compiles an approved Set into a frozen, schedulable graph with child->child edges, cycle detection, and parallel/serial eligibility. Pass 1's citation of `run_engine.get_runnable_steps` was weak (that schedules steps within one run); this is the correct one. The ONE real gap is that the shipped compiler derives edges from the orchestrator `## Child IPDs` table and greps ZERO for `Item-Dependencies` - a surgical change to the SHIPPED compiler, not a new `run_scheduler.py`. Runner-side ownership belongs to approved `lanetruth-03` (`8guhs0`).** Original expected outcome: Constructs frozen queue DAG, evaluates runtime edge satisfaction, sorts ready items (dependency depth, type rank `spec`->`backlog`->`ipd`->`prompt`, Set, Order, id6), and yields actionable items sequentially.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

- [ ] E-06 Implement the deterministic dependency failure cascade in `agent_workflows/run_scheduler.py`.
  - Depends on: E-05
  - Expected outcome: **DO NOT BUILD (REPLAN). The cascade ALREADY SHIPS: `ipd_set_plan._propagate_blocked` marks a gated child plus 'all its transitive descendants' while 'independent approved siblings are NOT in here' - exactly this item's stated outcome. Also note the reason-code trap sibling `lanetruth-03` already documented: the runner's real state is `dependency-blocked`, and `dependency_not_met` (this item's wording) has ZERO hits in the runners, so following this text literally would invent a parallel state.** Original expected outcome: When a prerequisite item fails, is capability-refused, or stops for input, direct and transitive dependents are marked `skipped` / `dependency_not_met` recording full root cause chains (`root_causes`, `blocking_dependency`, `chain`), while independent items continue.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

### Task group 4: Runner integration and flags

- [ ] E-07 Integrate selector resolution, dispatching, and DAG scheduling into `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, supporting `--full-auto`, `--unattended`, `--with-dependencies`, and `--follow-generated`.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: **DO NOT BUILD AS WRITTEN (REPLAN). Edits BOTH runners, fighting approved `rununify` (`5e4sb6`), whose purpose is to collapse their ~93 percent duplication. Sequence after `rununify` so the wiring lands once (OQ-03). Note also that two of the four flags it promises (`--with-dependencies`, `--follow-generated`) do not exist on `aw oc run` today, so this item silently includes new public CLI surface.** Original expected outcome: Runners execute multi-item queues with full flag parity across interactive and unattended modes.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

### Task group 5: Test suite coverage and edge cases

- [ ] E-08 Create `tests/test_run_selector_and_queue.py` covering resolution precedence, mixed-type confirmation, dispatch actions, spec/backlog handoffs, DAG topological scheduling, tiebreaking rules, and cascade propagation.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: **CANNOT BE WRITTEN AS SPECIFIED. It tests six items that should not be built, and its target module name presumes E-01/E-05's modules exist. 'Comprehensive coverage' is also unfalsifiable as stated. Retarget onto the surviving residue (mixed-type gate, dispatch table) and extend existing test modules where one already covers the surface.** Original expected outcome: Full pytest suite passes with comprehensive coverage across all selector and queue scheduling paths.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: see the verdict in Expected outcome. Blockers are duplication of shipped code (selectors.py, ipd_set_plan.py) and/or collision with approved plans lanetruth-03, rununify, bkclose-01. Do not tick this box.

## Project conventions discovered (Step 0)

CORRECTED /plan-review 2026-08-30 pass 2 (PR-302). The first bullet is the plan's own self-refutation:
it correctly identifies the precedence as an existing house standard, then E-01 proposes to reimplement
it in a new module.

- Precedence `path -> id6 -> set -> status -> stem -> substring` IS the house standard - and it is
  IMPLEMENTED, in `agent_workflows/selectors.py` as `_PRECEDENCE`, in exactly that order, in the module
  documented as "the ONE selector-to-file resolver for the whole package" routed through by `rename`,
  `group`, `set`, `show`, `find`, and `archive`. Therefore E-01 must CONSUME `selectors.resolve()`, not
  fork it.
- Type rankings `spec, backlog, ipd, prompt`: this matches spec 5.4's tiebreaker ranking, but it is NOT
  a discovered repository convention - it appears nowhere in the codebase. Label it as spec-derived, not
  discovered, so a reader does not go looking for existing code.
- `--with-dependencies`: NOT an existing convention either. Verified it does NOT exist on `aw oc run`
  today (sibling plan `lanetruth-03`'s review recorded the same). Describing an unimplemented flag as a
  discovered convention is how E-07 came to promise flags that do not exist.
- NOT DISCOVERED but decisive: `agent_workflows/selectors.py` (canonical resolver) and
  `agent_workflows/ipd_set_plan.py` (shipped cross-IPD DAG compiler with transitive-descendant
  blocking). Missing these two is the root cause of E-01/E-05/E-06.

## Findings

CORRECTED /plan-review 2026-08-30 pass 2 (PR-303). Both findings are TRUE; the omission is that neither
was checked against shipped code or the three approved plans already in this territory.

- TRUE: the runners assume all queue items are IPDs. Independently corroborated by approved
  `lanetruth-03`, which measured every queue item frozen with `dependencies: []` and ordering falling
  back to Set/Order. That plan owns the fix.
- TRUE and important: closing a backlog item `done` when its plans merely exist drops the release gate,
  which is why `aw backlog set done` fails closed on a release-blocking item. But the correct terminal
  state is `graduated`, and runner-side backlog closure is owned by APPROVED `bkclose-01` (`zhr6mc`) -
  not by this plan's scheduler.
- MISSING FROM THE SURVEY: the mixed-type gate (E-02) is the one item here with no shipped counterpart
  and no approved-plan owner. That, not the scheduler, is this plan's real contribution.

## Proposed changes (ordered, validatable)

SUPERSEDED /plan-review 2026-08-30 pass 2 (PR-304). Steps 1, 5, and 6 duplicate shipped modules; step 7
fights approved `rununify`; half of step 4 belongs to approved `bkclose-01`.

The replacement shape (small, and mostly NOT new modules):

1. Add the runner-facing selector POLICY on top of `selectors.resolve()`: the `all`-means-IPDs-only
   default, `--type` union, and the exit-code mapping (2 zero matches, 4 ambiguity). A thin wrapper, not
   `run_selector.py`.
2. Implement the mixed-type confirmation gate (the exact `run mixed` phrase, `--allow-mixed` for
   unattended, `[RUN-MIXED-TYPES]` refusal). Wholly unbuilt; the cleanest win here.
3. Implement the per-type/status dispatch table from spec Section 3, consuming `selectors.py` for typing.
4. Keep ONLY the spec-to-IPD authoring handoff, and sequence it after `From-Spec` recognition lands
   (sibling `bmh754`'s residue), since the generated IPD would otherwise fail lint with `IPD-M103`.
5. If `Item-Dependencies`-driven scheduling is wanted, make it a SURGICAL change to the shipped
   `ipd_set_plan.py` (which today reads the orchestrator `## Child IPDs` table) and coordinate with
   `lanetruth-03` for the runner half. Do not write a new scheduler or a new cascade.
6. Defer all runner wiring until after `rununify`.

Original sequence, retained for the record:

1. ~~Implement multi-type selector resolution in `run_selector.py` (E-01).~~ Consume `selectors.py`.
2. Implement mixed-type gate and preview (E-02) - KEEP, genuinely unbuilt.
3. Implement dispatch table in `run_dispatch.py` (E-03) - keep the substance, justify the module.
4. Implement spec-to-IPD and backlog graduation dispatch handlers (E-04) - SPLIT; backlog half to `bkclose-01`.
5. ~~Implement DAG queue scheduler in `run_scheduler.py` (E-05).~~ Shipped as `ipd_set_plan.py`.
6. ~~Implement dependency failure cascade (E-06).~~ Shipped as `_propagate_blocked`.
7. ~~Wire scheduler into runner entry points (E-07).~~ Defer behind `rununify`.
8. ~~Cover with comprehensive tests in `test_run_selector_and_queue.py` (E-08).~~ Retarget to the residue.

## Deferred / out of scope (with reason)

- **Isolated worktree management**: Deferred to child plan `detrun-04` (`k7o7el`).
- **Deterministic verification checker**: Deferred to child plan `detrun-05` (`7f7782`).

## Scope check

CORRECTED /plan-review 2026-08-30 pass 2 (PR-305).

- Over-scope: three new modules where the repo already has canonical homes. `run_selector.py` forks
  `selectors.py`; `run_scheduler.py` forks `ipd_set_plan.py`'s cross-IPD graph and its
  `_propagate_blocked` cascade; `run_dispatch.py` is a twelfth `run_*` module added without reconciling
  the eleven that exist. E-07 also quietly adds two nonexistent public flags (`--with-dependencies`,
  `--follow-generated`).
- Under-scope: no reconciliation with THREE approved plans in the same territory (`lanetruth-03` owns
  runner dependency consumption, `rununify` owns the runner de-duplication, `bkclose-01` owns runner-side
  backlog closure), and no recognition that E-04's spec handoff is blocked on `From-Spec`, which does not
  yet exist. Also missing: the runner's real blocked-state name is `dependency-blocked`, not the
  `dependency_not_met` this plan uses throughout.
- Original text, retained for the record: "Over-scope: none. Strictly implements selector resolution,
  dispatch routing, and DAG queue scheduling. Under-scope: none. All 7 artifact types and dispatch rules
  from spec Section 3 are covered."

## Required tests / validation

CORRECTED /plan-review 2026-08-30 pass 2 (PR-306). Both items were unachievable as written.

- ~~`python3 -m pytest tests/test_run_selector_and_queue.py`~~ - the module does not exist, and it should
  not be created for surfaces that are already covered elsewhere.
- ~~`aw oc run all --type ipd --type spec` displaying a mixed-type preview~~ - NOT achievable: `--type`
  does not exist on `aw oc run`, and the mixed-type preview is exactly what E-02 would build. This
  validation presupposes its own feature, so it could only "pass" after the fact.
- The honest bar for the replacement: the full suite at no-worsening against a freshly measured
  baseline (do NOT claim `aw check plans` passes; it is RED on 222 pre-existing findings owned by other
  Sets), plus a test proving the mixed-type gate REFUSES on the wrong phrase and on a bare `y`, and a
  test proving `selectors.resolve()` is called rather than reimplemented.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 2.1-2.6, 3.1-3.6, and 5.4.
- Updates CLI help text for `aw oc run` and `aw agy run`.

## Open questions

### OQ-01: Does `--with-dependencies` add dependencies of already satisfied external prerequisites?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.1
- Resolution or deferral rationale: RESOLVED per spec 2.1/2.6, and the answer is accurate. CAVEAT ADDED
  /plan-review 2026-08-30 pass 2 (PR-307): the flag it describes DOES NOT EXIST on `aw oc run` today
  (verified; approved `lanetruth-03`'s review recorded the same and explicitly excluded closure expansion
  from its own scope). So this is a design answer about future behavior, not a description of the current
  CLI, and any replacement plan must implement the flag before relying on it.

### OQ-02: Should `Item-Dependencies`-driven scheduling extend the shipped Set compiler or live in the runner?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN (/plan-review pass 2). Three candidate homes now exist and only
  one should own each half. (1) `ipd_set_plan.py` ALREADY compiles a cross-IPD DAG with cycle detection
  and transitive-descendant blocking, but derives edges from the orchestrator `## Child IPDs` table and
  greps ZERO for `Item-Dependencies`; teaching it the declared graph is a surgical change. (2) Approved
  `lanetruth-03` (`8guhs0`) owns the RUNNER-side runtime satisfaction semantics. (3) This plan proposed a
  third module. Recommendation: extend `ipd_set_plan.py` for the static graph, leave runtime satisfaction
  to `lanetruth-03`, and delete `run_scheduler.py` from the design entirely. The maintainer should confirm,
  because it decides whether the Set compiler or the runner is the scheduling authority.

### OQ-03: Who owns the runner-side backlog handoff, this plan or `bkclose-01`?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN (/plan-review pass 2, NEW). E-04's second half graduates an
  `open` backlog item and sets `graduated`; APPROVED `bkclose-01` (`zhr6mc`) teaches both runners to read
  `From-Backlog:` and close the item when the last carrying plan executes. These are two halves of one
  lifecycle and must not be split across two plans that each edit both runners. Recommendation: give ALL
  runner-side backlog lifecycle to `bkclose-01` and keep only the spec-to-IPD handoff here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: Python test verifying selector resolution matching exact paths, id6, set, status, and rejecting ambiguous IDs.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: Test verifying interactive `run mixed` requirement and unattended `--allow-mixed` refusal.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: Dispatch table unit tests verifying correct action packet emitted for each type/status combination.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: Test showing spec authoring an IPD carrying `From-Spec` and backlog graduation setting `graduated`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: Test showing DAG queue scheduler executing independent nodes in correct topological priority order with tiebreaking rules.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: Test showing a failed parent node cascading `dependency_not_met` to descendants while independent branches finish.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: End-to-end runner test executing a 3-item multi-type queue under `--full-auto`.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: **NOT TO BE COLLECTED (REPLAN): the matching E-item is superseded by shipped code or blocked on an approved-plan collision; collecting this would mean proving a duplicate was built.** Original required evidence: `pytest tests/test_run_selector_and_queue.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30, reaffirmed pass 2 with a narrower
residue).** Do NOT execute and do NOT approve. All 8 E-items are `Execution state: blocked` with an
execution note, and all 8 V-items' evidence is NOT TO BE COLLECTED, so nothing here can be ticked. An
executor reaching this gate must STOP and report.

PASS-2 CORRECTION TO MY OWN EARLIER CALL: pass 1 described this as "the least duplicated child, the most
salvageable" with E-01..E-04 as clean residue. The residue is HALF that. E-01 is shipped
(`selectors.py`, whose `_PRECEDENCE` is byte-identical to what E-01 proposes) and half of E-04 belongs to
approved `bkclose-01`. Do not rely on the pass-1 framing.

Open questions: THREE, two of them BLOCKING and needing YOU:
- OQ-02 (blocking): is the scheduling authority the shipped `ipd_set_plan.py` compiler or the runner?
  Recommendation: extend the compiler; leave runtime satisfaction to `lanetruth-03`.
- OQ-03 (blocking, new): does runner-side backlog lifecycle belong entirely to `bkclose-01`?
  Recommendation: yes.
- OQ-01: accurate, but describes a flag that does not exist yet.

Retirement: retire with the parent Set `detrun` (`r4mbcw`). Prepend a `RETIRED 2026-08-30: <reason>;
superseded by <path/commit>` header and `git mv` to `.aw/records/plans/superseded/`. Do NOT file under
`executed/`; nothing was implemented.

Release gate: carries `- Blocks-Release: next`. Re-gate the residue below onto its successor, or have the
maintainer clear the gate explicitly.

SURVIVING RESIDUE, now just TWO substantive items plus one thin wrapper:

1. The mixed-type confirmation gate (E-02). Verified wholly unbuilt: `RUN-MIXED-TYPES`, `--allow-mixed`,
   and the exact `run mixed` phrase all grep to ZERO hits. The cleanest, most valuable item in the plan.
2. The per-type/status dispatch table from spec Section 3 (E-03), plus ONLY the spec-to-IPD half of E-04,
   sequenced after `From-Spec` recognition lands (else the generated IPD fails lint with `IPD-M103`).
3. A thin runner-facing selector policy over `selectors.resolve()`: `all` means IPDs-only, `--type` union,
   exit 2 on zero matches, exit 4 on ambiguity.

Explicit prohibitions for the replacement: do NOT create `run_selector.py` (fork of `selectors.py`), do
NOT create `run_scheduler.py` (fork of `ipd_set_plan.py`'s graph and `_propagate_blocked` cascade), do NOT
implement runtime dependency satisfaction (approved `lanetruth-03`), do NOT implement runner-side backlog
closure (approved `bkclose-01`), do NOT edit `oc_runipd.py`/`agy_runipd.py` before `rununify` lands, and do
NOT use the reason code `dependency_not_met` (the runner's real state is `dependency-blocked`; the invented
spelling has zero hits and would fork the state vocabulary).

Scope fence for the replacement: the dispatch/gate module it justifies, plus its test module. Both runners
and `cli.py` are actively contended in this SHARED CHECKOUT: verify `git diff --cached --name-only` before
every commit and unstage anything not yours. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do
NOT claim `aw check plans` passes (RED on 222 pre-existing findings owned by other Sets); the bar is
no-worsening against a fresh baseline. Do not write a validation that presupposes its own feature, as the
original `aw oc run all --type ipd --type spec` item did.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never
`git add -A`, never push. Post-gate lifecycle is `aw ipd finalize`, never a hand-move. Do not create or
push a tag or release.
