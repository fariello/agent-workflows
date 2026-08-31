# IPD: the mixed-type confirmation gate and the runner-facing selector policy over the shipped resolver

- Date: 2026-08-30
- Kind: child
- Concern: `aw oc run` / `aw agy run` accept a selector and start work without ever telling the operator that the selection spans MORE THAN ONE KIND of work item. A selector that sweeps up plans, specs, and prompts together dispatches a different action per type, so the operator can authorize far more than they intended from one ambiguous word. Spec `25kzda` 2.5 requires the runner to print a per-type count and action preview and refuse to proceed until the mixing is explicitly acknowledged. Verified wholly unbuilt at HEAD `d08c1a1f`: `RUN-MIXED-TYPES`, `--allow-mixed`, and `allow_mixed` all grep to ZERO hits across `agent_workflows/` and `tests/`.
- Scope: Add the mixed-type confirmation gate (the sorted count and action preview, the exact-phrase interactive confirmation, the unattended `--allow-mixed` acknowledgement, and the verbatim `RUN-MIXED-TYPES` refusal) plus the thin runner-facing selector POLICY that decides which types a selector may span, as a standalone module consumed by callers. Excludes forking the shipped resolver `selectors.py`, excludes the DAG scheduler, excludes runtime dependency satisfaction, excludes runner-side backlog closure, and excludes wiring the gate into either runner module (deferred, see OQ-01).
- Scope-Paths: agent_workflows/run_selection_policy.py, tests/test_run_selection_policy.py
- Item-Dependencies: none
- Status: to-review
- Set: runmixed
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 6lu3rq
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `kaygwo` (detrun-03), inheriting ONLY the residue that plan's own second review left standing, and inheriting its `- Blocks-Release: next` gate so retiring `kaygwo` does not silently drop it. `kaygwo` was `REJECT - NEEDS REPLAN` twice: its E-01 selector work is byte-for-byte already shipped as `selectors.py`, its E-05/E-06 DAG and cascade work is shipped as `ipd_set_plan.py` plus the now-`executed` `lanetruth-03` (`8guhs0`), and half its E-04 belongs to the now-`executed` `bkclose-01` (`zhr6mc`). What survived that review is the mixed-type gate, which is genuinely unbuilt and is the most valuable single item in the retired Set.
- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the runner refuse to start a selection that silently spans multiple work-item types until the operator has seen exactly what it would do and said so, using the spec's own words for the preview and the refusal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify a selection without forking the resolver

- [ ] E-01 Create `agent_workflows/run_selection_policy.py` and implement the per-type CLASSIFICATION of an already-resolved selection: given resolved paths, group them by canonical type and return a stable per-type count. CONSUME the shipped resolver; do NOT re-derive typing. MEASURED starting points so the executor does not rediscover them: `selectors.resolve()` (`agent_workflows/selectors.py:347`) is documented as the one selector-to-file resolver for the package, its `_PRECEDENCE` tuple (`:48`) is `('path','id6','setid','status','stem','substring')`, which is byte-identical to the precedence spec 25kzda 2.3 step 3 requires; `UNIQUE_KINDS` (`:46`) plus `Resolution.is_ambiguous` already reject an ambiguous unique selector (spec 2.3 step 4); and `KNOWN_PRIMARY_TYPES` (`:93`) already spans `plans`, `specs`, `prompts`, `research`, `backlog`, `walkthroughs`, `roadmaps`, `comms`, `releases`. The spec's SEVEN runnable types (2.2) are a SUBSET of that frozenset under different names (`ipd` vs `plans`), so this module MUST map spec-type-name to resolver-type-name in ONE data table rather than inventing a second vocabulary; state the mapping explicitly, including that `comms` and `roadmaps` have no spec type.
  - Depends on: none
  - Expected outcome: a pure function takes resolved paths and returns a per-type count keyed by the spec's type names; it calls into `selectors.py` rather than reimplementing precedence or ambiguity; the spec-name-to-resolver-name mapping is a single visible data table; a selection of one type reports exactly one type.
  - Execution state: pending

- [ ] E-02 Implement the ACTION PREVIEW half of the count: for each type, how many items would take each action, so the preview reads `IPDs: 4 (2 review, 2 execute)` as spec 25kzda 2.5 shows. Derive the per-item action from the item's STATUS using the spec's own dispatch tables (3.2 for IPDs, 3.3 for specs, 3.4 for backlog, 3.5 for prompts), and where this module cannot determine an action, report it as such rather than guessing. DO NOT implement the dispatch itself; this item only COUNTS what dispatch would do. That distinction is the whole reason this plan is small: the retired `kaygwo` conflated the preview with a full dispatch table and grew a 3-module scope.
  - Depends on: E-01
  - Expected outcome: the preview names, per type, the count per action, using the spec's action vocabulary (`review`, `plan`, `execute`, and skip); an item whose action cannot be determined from status is reported as undetermined rather than silently bucketed; the output ordering is stable (sorted), so the preview is diffable and testable.
  - Execution state: pending

### Task group 2: gate the mixing, fail closed

- [ ] E-03 Implement the mixed-type DECISION as a pure predicate: given the classified selection, whether the session is interactive, and whether `--allow-mixed` was passed, return a definite verdict (proceed or refuse) plus the reason. Keep the policy DATA-driven and keep the decision pure, so it is testable without a TTY and without a host. The three cases spec 25kzda 2.5 fixes: a single-type selection proceeds with no gate at all; an interactive multi-type selection requires the operator to type the EXACT phrase `run mixed`, and `y`, an empty response, and any generic confirmation are REJECTED; an unattended multi-type selection is refused unless `--allow-mixed` was present on the original command. Also honor 2.5's narrowing rule: `--allow-mixed` acknowledges type mixing ONLY, and every status, approval, verifiability, scope, and safety gate still applies, so this predicate must never be a place where another gate can be waived.
  - Depends on: E-01
  - Expected outcome: the predicate refuses an unattended multi-type selection without the flag; accepts it with the flag; requires the literal `run mixed` interactively and rejects `y`, `yes`, an empty string, and any other phrase; never gates a single-type selection; and returns a reason string a caller can print. No TTY is required to test any branch.
  - Execution state: pending

- [ ] E-04 Add the `RUN-MIXED-TYPES` finding code with the spec's VERBATIM refusal text. Spec 25kzda 2.5 fixes the exact string, so do not compose your own:
  `[RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, then run: aw <host> run <selector> --type <type> ... --allow-mixed`
  Note what the wording COMMITS to and preserve all of it: the code prefix, the counts, the explicit `No work started.` claim, and a recovery command. The `No work started.` clause is a BEHAVIORAL guarantee, not decoration: this gate runs after resolution and before any lease or host session (spec 2.5, "After resolution and before leases or sessions"), so a refusal must be provably incapable of having started work. The finding code is a cross-artifact contract string; do not rename it.
  - Depends on: E-03
  - Expected outcome: a refusal emits the spec's verbatim message including the counts and the recovery command; the code string is exactly `RUN-MIXED-TYPES`; a test proves the refusal path performs no mutation and starts nothing (no session, no lease, no repository write).
  - Execution state: pending

- [ ] E-05 Add `tests/test_run_selection_policy.py` covering every branch above and the falsifiable pair for the gate. Tests MUST include: a single-type selection passing ungated; a multi-type selection REFUSED unattended without the flag AND PROCEEDING with it (both directions, since a one-sided test does not demonstrate a gate); the exact-phrase requirement including at least three rejected near-miss responses; the verbatim message asserted against the spec text rather than against a paraphrase; and a case proving the classification defers to `selectors.py` rather than duplicating it.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the module's every branch is covered; the gate is demonstrated in both directions; the message assertion would FAIL if someone reworded the refusal; the suite passes bare.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE RESOLVER ALREADY EXISTS AND IS AUTHORITATIVE. `selectors.py:347` `resolve()` is documented in-module as the ONE selector-to-file resolver for the whole package, and its precedence already matches what spec 25kzda 2.3 requires. The retired `kaygwo`'s own Step 0 called that precedence the house standard and then proposed to reimplement it in a new `run_selector.py`; that contradiction is exactly what its second review caught. Consume it.
- AMBIGUITY REJECTION IS ALSO SHIPPED. `UNIQUE_KINDS` (`selectors.py:46`) plus `Resolution.is_ambiguous` already implement spec 2.3 step 4 (an id6 or canonical stem matching more than one file is corruption, not a multi-item selection). Do not add a second ambiguity policy.
- THE TYPE VOCABULARIES DIFFER IN SPELLING. `selectors.KNOWN_PRIMARY_TYPES` uses records-tree directory names (`plans`, `specs`, `backlog`, ...); spec 2.2 uses singular type names (`ipd`, `spec`, `backlog`, ...). One mapping table, stated once (E-01). Two vocabularies for one concept is the drift this repo repeatedly pays for.
- THE CROSS-IPD SCHEDULER IS SHIPPED AND IS NOT THIS PLAN'S BUSINESS. `ipd_set_plan.py` compiles the cross-IPD Set graph with cycle detection and a `_propagate_blocked` fixpoint cascade (`:236`) whose docstring already states the property `kaygwo`'s E-06 proposed to build ("Independent approved siblings are never blocked"). Measured: `grep -c 'Item-Dependencies' agent_workflows/ipd_set_plan.py` returns 0, so the compiler derives edges from the orchestrator's child table rather than the declared field. That gap is real but it is NOT this plan's residue; see Deferred.
- RUNTIME DEPENDENCY SATISFACTION SHIPPED WHILE THE RETIRED PLAN WAITED. `lanetruth-03` (`8guhs0`) is now in `executed/`, and the runner consumes the shared predicate directly (`oc_runipd.py:2778` calls `check_engine.evaluate_ipd_dependencies`; `enforce_dependency_preflight` fails closed before any session). The retired `kaygwo`'s E-05/E-06 are therefore not merely duplicative, they are OBSOLETE.
- RUNNER-SIDE BACKLOG CLOSURE ALSO SHIPPED. `bkclose-01` (`zhr6mc`) is in `executed/` and the runner reads `- From-Backlog:` (`oc_runipd.py:851`, `:2243`). Half of `kaygwo`'s E-04 is gone for the same reason.
- THE RUNNER'S STATE WORD IS `dependency-blocked`. Measured at `oc_runipd.py:119`. The retired plan used `dependency_not_met` throughout, an invented spelling with zero hits in the package. If this plan ever needs to name that state, use the shipped one.

## Findings

| # | Sev | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F1 | HIGH | `agent_workflows/` (absence) | The mixed-type gate is WHOLLY unbuilt, which is why it is worth a plan at all. Nothing warns an operator that one selector spans several kinds of work. | `rg -n 'RUN-MIXED-TYPES\|allow-mixed\|allow_mixed' agent_workflows/ tests/ --include=*.py` returns ZERO hits at HEAD `d08c1a1f` |
| F2 | HIGH | `selectors.py:48` vs retired `kaygwo` E-01 | The retired plan's selector residue was not residue at all: its proposed precedence is byte-identical to the shipped `_PRECEDENCE` tuple. Its FIRST review called it "the least duplicated child, the most salvageable"; its second review corrected that. Inheriting the pass-1 framing would re-create the duplicate. | `_PRECEDENCE = ('path','id6','setid','status','stem','substring')` at `selectors.py:48`; `kaygwo`'s own pass-2 history entry records the self-correction |
| F3 | HIGH | `.aw/records/plans/executed/` | TWO of the three sibling collisions that made `kaygwo` unexecutable have since EXECUTED, so its overlap is now with shipped code rather than with pending plans: `lanetruth-03` (`8guhs0`) and `bkclose-01` (`zhr6mc`) are both in `executed/`. This makes retirement, not re-scoping, the correct disposition for those E-items. | both plan files present under `.aw/records/plans/executed/`; runner call sites at `oc_runipd.py:2778` and `:851` |
| F4 | MED | `ipd_set_plan.py` | The one seam `kaygwo`'s review left genuinely open (declared-graph scheduling: the shipped Set compiler greps ZERO for `Item-Dependencies`) is REAL but is a surgical change to a shipped compiler owned by the Set-planning surface, not part of a mixed-type gate. Bundling them is what made the retired plan unexecutable. Deferred explicitly rather than silently dropped. | `grep -c 'Item-Dependencies' agent_workflows/ipd_set_plan.py` = 0; `_propagate_blocked:236` docstring |
| F5 | MED | spec `25kzda` 2.5 | The refusal message and the confirmation phrase are SPECIFIED VERBATIM, including a recovery command and the literal phrase `run mixed` with `y` explicitly rejected. A paraphrase would break the contract and weaken the gate; the retired plan paraphrased both. | spec 2.5 exact refusal block and its three bullet rules |
| F6 | LOW | spec `25kzda` 2.5 | `--allow-mixed` acknowledges type mixing ONLY. It must not become a general override seam; the spec says every other gate still applies. Worth pinning in a test, since a flag named "allow" invites scope creep. | spec 2.5, third bullet |

## Proposed changes (ordered, validatable)

1. Classify a resolved selection per type by CONSUMING `selectors.py` (E-01).
2. Count per-action within each type to produce the spec's preview (E-02).
3. Decide the gate purely, with the exact-phrase and unattended-flag rules (E-03).
4. Refuse with the spec's verbatim `RUN-MIXED-TYPES` message (E-04).
5. Cover every branch, both gate directions, and the verbatim message (E-05).

## Deferred / out of scope (with reason)

- WIRING THE GATE INTO `oc_runipd.py` / `agy_runipd.py`. Deferred so this plan touches neither runner, which removes the `rununify` (`5e4sb6`) sequencing conflict entirely rather than answering it. This is the same move that unblocked `hostcap-01` (`mjx7ne`). The honest consequence is stated in the Scope check: nothing consults this gate until a follow-up wires it.
- DECLARED-GRAPH SCHEDULING in `ipd_set_plan.py` (F4). Real, unbuilt, and a surgical change to a shipped compiler; it belongs to whoever owns Set planning, not to a mixed-type gate.
- THE FULL PER-TYPE DISPATCH TABLE of spec Section 3. This plan COUNTS what dispatch would do (E-02); it does not implement dispatch. Implementing it means editing both runners, which is deferred above.
- RUNTIME DEPENDENCY SATISFACTION. Shipped by `lanetruth-03` (`8guhs0`, executed).
- RUNNER-SIDE BACKLOG CLOSURE. Shipped by `bkclose-01` (`zhr6mc`, executed).
- A NEW `run_selector.py` OR `run_scheduler.py`. Explicitly rejected; those were the defects in the retired plan.

## Scope check

- Over-scope: none. One new module carries E-01 through E-04 and one new test module carries E-05. No shipped file is edited, which is deliberate in a contended checkout.
- Under-scope, DELIBERATE and stated plainly: the gate is not consulted by a live run when this plan completes. It lands tested and importable, and it prevents nothing until a follow-up wires the call sites. That is the price of not touching the two runner modules `rununify` is chartered to unify, and it is the right trade because the gate's VOCABULARY and its verbatim message are what any wiring needs first.
- Under-scope, ACKNOWLEDGED: E-02 can only preview actions it can derive from status. Where the spec's dispatch tables depend on flags this module does not see (`--full-auto`, `--action`), the preview reports undetermined rather than guessing. A preview that guessed would be worse than one that admits the limit.

## Required tests / validation

- `tests/test_run_selection_policy.py` must pass with every case in E-05.
- FALSIFIABILITY (HARD): the gate must be demonstrated REFUSING and PROCEEDING on the same selection, differing only in the flag. A happy-path-only test does not demonstrate a gate. Likewise the verbatim-message test must be written so that rewording the message FAILS it.
- INVOKE THE SUITE BARE: `python3 -m pytest`. `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do NOT add `-n0`, a second `-q`, or `-p no:randomly`.
- BASELINE IS A MEASUREMENT, not a memory: take before/after counts yourself with the `git rev-parse HEAD` they were measured at. This repo's HEAD moves hourly and several sessions commit concurrently.
- `aw check plans` is RED on pre-existing findings owned by other Sets (measured 901 at HEAD `7e5ba287`: 892 `check.scope-drift`, 7 `check.lifecycle-transition-invalid`, 2 `stale-index`). Do NOT claim it passes. The bar is NO-WORSENING against a freshly measured baseline.
- `aw sanitize --agent` clean; `aw ipd lint --phase pre-transition` conforming.

## Spec / documentation sync

- This plan implements spec `25kzda` 2.5 (the mixed-type gate) and the counting half of 2.4. It does not change the spec text; the spec already specifies the behavior exactly.
- Record which of the spec's Section 4.2 `RUN-*` codes now exists, since `RUN-MIXED-TYPES` is one of the codes a successor of `7f7782` must map. Leaving that unrecorded is how two plans both come to believe a code is unbuilt.
- No user-facing documentation changes until the gate is actually wired into a runner. Documenting an unconsulted gate would misdescribe the tool.

## Open questions

### OQ-01: Must the runner wiring wait for `rununify`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: THE QUESTION IS DISSOLVED, not answered, which is what lets this plan proceed now. The retired `kaygwo` carried this as a BLOCKING maintainer question (its OQ-03) because its E-07 edited both runner modules, doubling the surface `rununify` (`5e4sb6`) must reconcile. This plan instead defers the wiring entirely and touches neither runner, so the conflict cannot arise. The precedent is `hostcap-01` (`mjx7ne`), which dissolved the identical question the identical way at the maintainer's direction. The honest cost is recorded in the Scope check rather than hidden: the gate is not consulted by a live run until a follow-up wires it.

### OQ-02: Who owns declared-graph scheduling in the shipped Set compiler?

- Blocking: no
- Status: deferred
- Owner: maintainer (to assign to whoever owns the Set-planning surface `ipd_set_plan.py`; NOT this plan)
- Resolution or deferral rationale: DEFERRED OUT OF THIS PLAN, not answered inside it, because it is a different concern with a different owner. The retired `kaygwo` carried this as blocking (its OQ-02: is the scheduling authority the shipped compiler or the runner?). The measurement stands and is recorded here so it is not lost: `ipd_set_plan.py` compiles the cross-IPD graph but greps ZERO for `Item-Dependencies`, so it derives edges from the orchestrator's child table only. Whoever picks this up should extend that compiler rather than fork it, and should leave runtime satisfaction to the now-executed `lanetruth-03` (`8guhs0`). It is not blocking HERE because a mixed-type gate neither reads nor schedules a dependency graph.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the classification of a mixed selection showing per-type counts. Paste the spec-name-to-resolver-name mapping table itself, showing it is ONE data table. Paste evidence the module CALLS `selectors.py` rather than reimplementing it (the actual import and call site, not an assertion that it does). Paste a single-type selection reporting exactly one type.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a preview rendering in the spec's shape (`IPDs: 4 (2 review, 2 execute)`) beside spec 2.5's example, showing they agree. Paste an item whose action cannot be determined from status being reported as UNDETERMINED rather than bucketed into an action. Paste two runs over the same input showing byte-identical (stable, sorted) output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste all three cases: single-type ungated, unattended multi-type REFUSED without the flag, and the same selection PROCEEDING with `--allow-mixed`. Paste the exact-phrase check rejecting at least `y`, `yes`, and the empty string, and accepting exactly `run mixed`. Paste evidence no branch needed a TTY to test. Paste evidence `--allow-mixed` does not waive any other gate (F6).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the emitted refusal BESIDE spec 25kzda 2.5's verbatim block, proving character-level agreement including the counts and the `aw <host> run <selector> --type <type> ... --allow-mixed` recovery command. Paste a grep proving the code string is exactly `RUN-MIXED-TYPES`. Paste evidence the refusal path started nothing and wrote nothing (for example `git status --porcelain` unchanged across the refusal), which is the `No work started.` claim the message makes.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_run_selection_policy.py` output with counts, and paste the BARE `python3 -m pytest` summary line with the `git rev-parse HEAD` it was measured at, plus your own before-baseline at that same HEAD. Paste proof the tests are NOT VACUOUS: with the module's gate logic reverted or stubbed, show the gate tests FAIL. Paste the no-worsening comparison for `aw check plans` (before and after counts, both measured, not remembered).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 5 E-leaves across 2 task groups, under the thresholds. One concern throughout: refuse a multi-type selection until the operator has seen and acknowledged it.

Open questions: NEITHER is blocking, and neither needs a maintainer decision. OQ-01 is DISSOLVED by deferring the runner wiring (the `hostcap-01` precedent), which is what lets this plan run without waiting on `rununify`. OQ-02 is DEFERRED to whoever owns the Set compiler, with its measurement preserved here so it is not lost; a mixed-type gate neither reads nor schedules a dependency graph, so it does not gate this work.

Scope fence: touch ONLY `agent_workflows/run_selection_policy.py` and `tests/test_run_selection_policy.py`, both new. Do NOT create `run_selector.py` or `run_scheduler.py` (forks of `selectors.py` and `ipd_set_plan.py`; this was the retired plan's central defect). Do NOT edit `selectors.py`, `ipd_set_plan.py`, `cli.py`, `oc_runipd.py`, or `agy_runipd.py`. Do NOT implement runtime dependency satisfaction (shipped, `8guhs0`) or runner-side backlog closure (shipped, `zhr6mc`). Do NOT use the reason code `dependency_not_met`; the runner's real state is `dependency-blocked` (`oc_runipd.py:119`) and the invented spelling has zero hits. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim `aw check plans` passes; it is RED on 901 pre-existing findings owned by other Sets (measured at HEAD `7e5ba287`), and the bar is no-worsening against your own fresh baseline. Do NOT describe this plan as making runs safer: it lands the gate and its message, and nothing consults them until a follow-up wires the runners. Say so plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify, with `git restore --staged <path>`. A pre-commit hook failure INVALIDATES that check, so re-run it after any failed commit attempt before retrying. Prefer `aw commit <plan> -- <paths>`, which is immune to index pollution by construction.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
