# IPD: the mixed-type confirmation gate and the runner-facing selector policy over the shipped resolver

- Date: 2026-08-30
- Kind: child
- Concern: `aw oc run` / `aw agy run` accept a selector and start work without ever telling the operator that the selection spans MORE THAN ONE KIND of work item. A selector that sweeps up plans, specs, and prompts together dispatches a different action per type, so the operator can authorize far more than they intended from one ambiguous word. Spec `25kzda` 2.5 requires the runner to print a per-type count and action preview and refuse to proceed until the mixing is explicitly acknowledged. Verified wholly unbuilt at HEAD `d08c1a1f`: `RUN-MIXED-TYPES`, `--allow-mixed`, and `allow_mixed` all grep to ZERO hits across `agent_workflows/` and `tests/`.
- Scope: Add the mixed-type confirmation gate (the sorted count and action preview, the exact-phrase interactive confirmation, the unattended `--allow-mixed` acknowledgement, and the verbatim `RUN-MIXED-TYPES` refusal) plus the thin runner-facing selector POLICY that decides which types a selector may span, as a standalone module consumed by callers. Excludes forking the shipped resolver `selectors.py`, excludes the DAG scheduler, excludes runtime dependency satisfaction, excludes runner-side backlog closure, and excludes wiring the gate into either runner module (deferred, see OQ-01).
- Scope-Paths: agent_workflows/run_selection_policy.py, tests/test_run_selection_policy.py
- Item-Dependencies: none
- Status: approved
- Set: runmixed
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 6lu3rq
- Approval: 2026-08-31, human ("approved"): Maintainer approved 2026-08-31 in session, after plan-review round 1 (m73aet APPROVE 0 findings; 6lu3rq and wlxkoz APPROVE WITH REVISIONS APPLIED, all findings FIXED in place, zero unresolved, no open questions).
- Blocks-Release: next
- From-Spec: 25kzda

## Workflow history
- 2026-08-31 approved (aw set, --by-human): Maintainer approved 2026-08-31 in session, after plan-review round 1 (m73aet APPROVE 0 findings; 6lu3rq and wlxkoz APPROVE WITH REVISIONS APPLIED, all findings FIXED in place, zero unresolved, no open questions).
- 2026-08-31 reviewed (aw set): plan-review round 1 complete; revisions applied. See .aw/records/reviews/ for the typed findings and decisions.
- 2026-08-31 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): plan-review round 1: APPROVE WITH REVISIONS APPLIED; PR-001 (1 finding, fixed). Verified at HEAD 381dbd5c: the gate is genuinely unbuilt (RUN-MIXED-TYPES/--allow-mixed/allow_mixed all ZERO hits), the E-04 refusal string is character-identical to spec 25kzda 2.5's exact refusal block (spec:215), the run-mixed exact-phrase and narrowing rules are verbatim in spec:206-209, selectors.py really is authoritative (UNIQUE_KINDS :46), both claimed sibling collisions really are in executed/, and Scope-Paths collide with NO pending or approved plan. PR-001: the plan implemented THREE of spec 2.5's FOUR bullets and was silent on the fourth (record counts/preview/response/queue-digest in the run ledger); grep for 'ledger' returned zero. Fixed by splitting it: E-03 now RETURNS the four facts as structured data (in scope) and the ledger WRITE is deferred to the caller owning a live run, with the partial discharge recorded in Spec sync so a successor knows what remains. Two reversible decisions recorded (D-1, D-2). Review artifact: .aw/records/reviews/20260831-runmixed-01-6lu3rq-the-mixed-type-confirmation-gate.review.md
- 2026-08-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): SUPERSEDES `kaygwo` (detrun-03), inheriting ONLY the residue that plan's own second review left standing, and inheriting its `- Blocks-Release: next` gate so retiring `kaygwo` does not silently drop it. `kaygwo` was `REJECT - NEEDS REPLAN` twice: its E-01 selector work is byte-for-byte already shipped as `selectors.py`, its E-05/E-06 DAG and cascade work is shipped as `ipd_set_plan.py` plus the now-`executed` `lanetruth-03` (`8guhs0`), and half its E-04 belongs to the now-`executed` `bkclose-01` (`zhr6mc`). What survived that review is the mixed-type gate, which is genuinely unbuilt and is the most valuable single item in the retired Set.
- 2026-08-30 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make the runner refuse to start a selection that silently spans multiple work-item types until the operator has seen exactly what it would do and said so, using the spec's own words for the preview and the refusal.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: classify a selection without forking the resolver

- [x] E-01 Create `agent_workflows/run_selection_policy.py` and implement the per-type CLASSIFICATION of an already-resolved selection: given resolved paths, group them by canonical type and return a stable per-type count. CONSUME the shipped resolver; do NOT re-derive typing. MEASURED starting points so the executor does not rediscover them: `selectors.resolve()` (`agent_workflows/selectors.py:347`) is documented as the one selector-to-file resolver for the package, its `_PRECEDENCE` tuple (`:48`) is `('path','id6','setid','status','stem','substring')`, which is byte-identical to the precedence spec 25kzda 2.3 step 3 requires; `UNIQUE_KINDS` (`:46`) plus `Resolution.is_ambiguous` already reject an ambiguous unique selector (spec 2.3 step 4); and `KNOWN_PRIMARY_TYPES` (`:93`) already spans `plans`, `specs`, `prompts`, `research`, `backlog`, `walkthroughs`, `roadmaps`, `comms`, `releases`. The spec's SEVEN runnable types (2.2) are a SUBSET of that frozenset under different names (`ipd` vs `plans`), so this module MUST map spec-type-name to resolver-type-name in ONE data table rather than inventing a second vocabulary; state the mapping explicitly, including that `comms` and `roadmaps` have no spec type.
  - Depends on: none
  - Expected outcome: a pure function takes resolved paths and returns a per-type count keyed by the spec's type names; it calls into `selectors.py` rather than reimplementing precedence or ambiguity; the spec-name-to-resolver-name mapping is a single visible data table; a selection of one type reports exactly one type.
  - Execution state: performed

- [x] E-02 Implement the ACTION PREVIEW half of the count: for each type, how many items would take each action, so the preview reads `IPDs: 4 (2 review, 2 execute)` as spec 25kzda 2.5 shows. Derive the per-item action from the item's STATUS using the spec's own dispatch tables (3.2 for IPDs, 3.3 for specs, 3.4 for backlog, 3.5 for prompts), and where this module cannot determine an action, report it as such rather than guessing. DO NOT implement the dispatch itself; this item only COUNTS what dispatch would do. That distinction is the whole reason this plan is small: the retired `kaygwo` conflated the preview with a full dispatch table and grew a 3-module scope.
  - Depends on: E-01
  - Expected outcome: the preview names, per type, the count per action, using the spec's action vocabulary (`review`, `plan`, `execute`, and skip); an item whose action cannot be determined from status is reported as undetermined rather than silently bucketed; the output ordering is stable (sorted), so the preview is diffable and testable.
  - Execution state: performed

### Task group 2: gate the mixing, fail closed

- [x] E-03 Implement the mixed-type DECISION as a pure predicate: given the classified selection, whether the session is interactive, and whether `--allow-mixed` was passed, return a definite verdict (proceed or refuse) plus the reason. Keep the policy DATA-driven and keep the decision pure, so it is testable without a TTY and without a host. The three cases spec 25kzda 2.5 fixes: a single-type selection proceeds with no gate at all; an interactive multi-type selection requires the operator to type the EXACT phrase `run mixed`, and `y`, an empty response, and any generic confirmation are REJECTED; an unattended multi-type selection is refused unless `--allow-mixed` was present on the original command. Also honor 2.5's narrowing rule: `--allow-mixed` acknowledges type mixing ONLY, and every status, approval, verifiability, scope, and safety gate still applies, so this predicate must never be a place where another gate can be waived.
  - Depends on: E-01
  ADDED AT REVIEW (PR-001, spec 2.5 bullet 4): the predicate MUST also RETURN, as structured data, the four facts spec 2.5 requires to be recorded in the run ledger: the confirmed type counts, the action preview, the user response or the flag that was used, and the queue digest. Returning them is in scope; WRITING them to the ledger is not (see Deferred), because the write needs a live run's context and `run_ledger_store.py` is outside Scope-Paths. Returning them is the seam that makes the wiring follow-up trivial and keeps this plan from touching a runner.
  - Expected outcome: the predicate refuses an unattended multi-type selection without the flag; accepts it with the flag; requires the literal `run mixed` interactively and rejects `y`, `yes`, an empty string, and any other phrase; never gates a single-type selection; and returns a reason string a caller can print. No TTY is required to test any branch. It ALSO returns a structured record carrying the type counts, the action preview, the response-or-flag actually used, and the queue digest, so a caller can satisfy spec 2.5 bullet 4 without this module writing to the ledger.
  - Execution state: performed

- [x] E-04 Add the `RUN-MIXED-TYPES` finding code with the spec's VERBATIM refusal text. Spec 25kzda 2.5 fixes the exact string, so do not compose your own:
  `[RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, then run: aw <host> run <selector> --type <type> ... --allow-mixed`
  Note what the wording COMMITS to and preserve all of it: the code prefix, the counts, the explicit `No work started.` claim, and a recovery command. The `No work started.` clause is a BEHAVIORAL guarantee, not decoration: this gate runs after resolution and before any lease or host session (spec 2.5, "After resolution and before leases or sessions"), so a refusal must be provably incapable of having started work. The finding code is a cross-artifact contract string; do not rename it.
  - Depends on: E-03
  - Expected outcome: a refusal emits the spec's verbatim message including the counts and the recovery command; the code string is exactly `RUN-MIXED-TYPES`; a test proves the refusal path performs no mutation and starts nothing (no session, no lease, no repository write).
  - Execution state: performed

- [x] E-05 Add `tests/test_run_selection_policy.py` covering every branch above and the falsifiable pair for the gate. Tests MUST include: a single-type selection passing ungated; a multi-type selection REFUSED unattended without the flag AND PROCEEDING with it (both directions, since a one-sided test does not demonstrate a gate); the exact-phrase requirement including at least three rejected near-miss responses; the verbatim message asserted against the spec text rather than against a paraphrase; and a case proving the classification defers to `selectors.py` rather than duplicating it.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the module's every branch is covered; the gate is demonstrated in both directions; the message assertion would FAIL if someone reworded the refusal; the suite passes bare.
  - Execution state: performed

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
| F7 | MED | spec `25kzda` 2.5 bullet 4 | FOUND AT REVIEW (PR-001). This plan implements THREE of spec 2.5's four bullets and was silent on the fourth, which requires the confirmed type counts, action preview, user response or flag, and queue digest to be RECORDED IN THE RUN LEDGER. That record is the audit trail proving what the operator actually acknowledged, so without it a `--allow-mixed` run leaves no durable evidence of the counts that were waved through. Split at review: E-03 now RETURNS those four facts as structured data (in scope), while the ledger WRITE is deferred to the caller that owns a live run (out of scope, since it needs runner context). | spec 2.5 bullet 4 (`spec:210`); `grep -in 'ledger'` over this plan returned ZERO before the fix |

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
- WRITING THE SPEC 2.5 BULLET 4 LEDGER RECORD (added at review, F7). E-03 RETURNS the four facts the spec requires to be recorded (counts, preview, response-or-flag, queue digest), but this plan does not write them: the write needs a live run's context and `run_ledger_store.py` is outside Scope-Paths, so writing here would mean touching the runner surface this plan deliberately avoids. The honest consequence, stated so it is not lost: spec 2.5 bullet 4 is only PARTIALLY discharged by this plan, and the follow-up that wires the gate into a runner must complete it. Returning the facts is what makes that follow-up trivial rather than archaeological.

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
- PARTIAL DISCHARGE, recorded at review (F7/PR-001): spec 2.5 has FOUR bullets and this plan fully discharges three. Bullet 4 (record the counts, preview, response-or-flag and queue digest in the run ledger) is only HALF discharged: E-03 returns those facts, and the ledger WRITE is deferred to the runner-wiring follow-up. State this in the terminal history rather than claiming 2.5 is complete, so the successor knows what remains.
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

- [x] V-01 validates E-01
  - Required evidence: paste the classification of a mixed selection showing per-type counts. Paste the spec-name-to-resolver-name mapping table itself, showing it is ONE data table. Paste evidence the module CALLS `selectors.py` rather than reimplementing it (the actual import and call site, not an assertion that it does). Paste a single-type selection reporting exactly one type.
  - Observed evidence: MEASURED at HEAD `26973ca6`. Per-type classification of a mixed selection (spec 2.5's own example shape):
    ```
    ipd        total=4 by_action=(('review', 2), ('execute', 2))
    spec       total=2 by_action=(('review', 1), ('plan', 1))
    prompt     total=1 by_action=(('execute', 1),)
    ```
    THE MAPPING IS ONE DATA TABLE, `SPEC_TYPE_BY_RESOLVER_TYPE` (`run_selection_policy.py:53`), printed from the module itself:
    ```
    plans          -> ipd          research       -> research
    specs          -> spec         releases       -> release
    backlog        -> backlog      walkthroughs   -> walkthrough
    prompts        -> prompt       comms          -> None
                                   roadmaps       -> None
    ```
    `comms` and `roadmaps` map explicitly to `None` (no spec 2.2 type), as E-01 required stating. `test_type_mapping_is_one_data_table_covering_the_resolver_vocabulary` asserts `set(SPEC_TYPE_BY_RESOLVER_TYPE) == set(selectors.KNOWN_PRIMARY_TYPES)`, so a type added to the resolver cannot be silently mistyped here.
    IT CALLS THE SHIPPED RESOLVER rather than reimplementing it. Actual import and call sites:
    ```
    39:from agent_workflows import selectors as _sel
    40:from agent_workflows import status_set as _status_set
    358:        resolver_type = _status_set.detect_artifact_type(p, repo_root)
    366:            rec = _status_set.read_artifact_record(p, repo_root)
    ```
    plus `_sel.resolve(...)` inside `resolve_selection`, proven by a SPY test (`test_resolution_defers_to_selectors_resolve`) that records the delegations and asserts exactly `[('plans','mixdemo'), ('specs','mixdemo'), ('backlog','mixdemo')]`, i.e. one call per type with no matching logic of the policy's own. `test_unique_kind_collision_is_reported_using_the_shipped_policy` proves spec 2.3 step 4 is applied via `selectors.UNIQUE_KINDS`, not re-derived.
    SINGLE TYPE REPORTS EXACTLY ONE: `test_single_type_selection_reports_exactly_one_type` asserts `type_count == 1`, `spec_types == ('ipd',)`, `is_mixed is False`.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste a preview rendering in the spec's shape (`IPDs: 4 (2 review, 2 execute)`) beside spec 2.5's example, showing they agree. Paste an item whose action cannot be determined from status being reported as UNDETERMINED rather than bucketed into an action. Paste two runs over the same input showing byte-identical (stable, sorted) output.
  - Observed evidence: MEASURED at HEAD `26973ca6`. `render_action_preview` output BESIDE spec 2.5's example, which is BYTE-IDENTICAL including column alignment (asserted by `test_preview_matches_spec_2_5_example_exactly`):
    ```
    RENDERED                            SPEC 2.5 EXAMPLE
    Mixed work-item selection:          Mixed work-item selection:
      IPDs:    4 (2 review, 2 execute)    IPDs:    4 (2 review, 2 execute)
      Specs:   2 (1 review, 1 plan)       Specs:   2 (1 review, 1 plan)
      Prompts: 1 (1 execute)              Prompts: 1 (1 execute)
    ```
    UNDETERMINED IS REPORTED, NOT BUCKETED. Statuses whose action the spec derives from something other than status (a completeness check, `--full-auto`) return `undetermined`:
    ```
    ipd/draft: undetermined      (spec 3.2 splits draft on an authoring-completeness check)
    ipd/reviewed: undetermined   (spec 3.2 dispatches reviewed on --full-auto, a flag not seen here)
    ipd/banana: undetermined     (unknown status: spec 3.2 red-aborts; guessing is forbidden)
    ipd/None: undetermined
    ```
    `test_undetermined_appears_in_the_preview_rather_than_silently_counting_as_an_action` asserts the preview shows `2 undetermined` alongside `1 execute`; `test_reviewed_ipd_is_undetermined_end_to_end_through_classify_paths` proves it end-to-end from a real file on disk. 8 parametrized cases cover the undeterminable set.
    STABLE/SORTED: `test_preview_is_stable_across_runs_and_input_order` renders the same selection twice AND with its item order REVERSED, asserting byte-identical output both ways (type order is `SPEC_TYPE_ORDER`, action order is `ACTION_ORDER`), and asserts the queue digest is likewise order-independent.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste all three cases: single-type ungated, unattended multi-type REFUSED without the flag, and the same selection PROCEEDING with `--allow-mixed`. Paste the exact-phrase check rejecting at least `y`, `yes`, and the empty string, and accepting exactly `run mixed`. Paste evidence no branch needed a TTY to test. Paste evidence `--allow-mixed` does not waive any other gate (F6). ALSO paste the STRUCTURED RECORD the predicate returns (F7/PR-001), showing all four spec 2.5 bullet 4 facts present: the type counts, the action preview, the response-or-flag actually used, and the queue digest. A returned record missing any of the four does not satisfy this item.
  - Observed evidence: MEASURED at HEAD `26973ca6`. ALL THREE CASES, from the module itself:
    ```
    single-type                proceed=True  gate_applied=False code=None
    unattended no flag         proceed=False gate_applied=True  code=RUN-MIXED-TYPES
    unattended --allow-mixed   proceed=True  gate_applied=True  code=None
    interactive 'run mixed'    proceed=True  gate_applied=True  code=None
    interactive 'y'            proceed=False gate_applied=True  code=RUN-MIXED-TYPES
    ```
    Note `gate_applied=False` on the single-type row: it is UNGATED, not "passed". The refuse/proceed pair on rows 2 and 3 is the SAME selection differing ONLY in the flag (`test_unattended_mixed_is_refused_without_the_flag_and_proceeds_with_it`).
    EXACT PHRASE: 12 parametrized rejections in `test_interactive_rejects_near_misses_and_generic_confirmations`, including the three the spec names plus near misses: `y`, `''`, `None`, `yes`, `Y`, `YES`, `ok`, `Run Mixed` (case not folded), `run`, `run mixed types`, `runmixed`, `run  mixed` (internal whitespace not normalized). Accepted: exactly `run mixed` (and only surrounding whitespace stripped, since a terminal read includes the newline).
    NO TTY NEEDED: `test_no_branch_requires_a_tty` reaches all five branches as plain function calls, asserting `[True, False, True, True, False]`. `decide` takes `interactive` and `response` as ARGUMENTS; the caller performs the prompt, so no branch touches a terminal.
    F6, THE FLAG WAIVES ONLY TYPE MIXING: `test_allow_mixed_waives_only_type_mixing` asserts `Verdict.WAIVES == ('type-mixing',)`, introspects `decide`'s signature to assert its parameter set is exactly `{classification, interactive, allow_mixed, response, host, selector}` with NO `allow_unapproved`/`skip_gates`/`force`/`allow_unverifiable`/`no_verify` knob, and asserts the flag does not alter the previewed actions.
    BULLET 4 STRUCTURED RECORD, all four facts present:
    ```
    {"type_counts": {"ipd": 4, "spec": 2, "prompt": 1},
     "action_preview": "Mixed work-item selection:\n  IPDs:    4 (2 review, 2 execute)\n  Specs: ...",
     "response_or_flag": "--allow-mixed",
     "queue_digest": "5e85c71a85dd209dd927553f19abd37c59825fd643c626ac40f..."}
    ```
    `test_verdict_carries_all_four_spec_2_5_bullet_4_facts` asserts all four keys on the proceed, confirm, and refuse paths, and that `response_or_flag` DISTINGUISHES `--allow-mixed` from the typed `run mixed` from `None`.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the emitted refusal BESIDE spec 25kzda 2.5's verbatim block, proving character-level agreement including the counts and the `aw <host> run <selector> --type <type> ... --allow-mixed` recovery command. Paste a grep proving the code string is exactly `RUN-MIXED-TYPES`. Paste evidence the refusal path started nothing and wrote nothing (for example `git status --porcelain` unchanged across the refusal), which is the `No work started.` claim the message makes.
  - Observed evidence: MEASURED at HEAD `26973ca6`. EMITTED REFUSAL beside spec 25kzda 2.5's verbatim block:
    ```
    SPEC 2.5 (exact refusal):
    [RUN-MIXED-TYPES] Selection contains <counts>. No work started. Review the selection, then run: aw <host> run <selector> --type <type> ... --allow-mixed

    EMITTED (placeholders left literal):
    [RUN-MIXED-TYPES] Selection contains IPDs: 4, Specs: 2, Prompts: 1. No work started. Review the selection, then run: aw <host> run <selector> --type <type> ... --allow-mixed

    EMITTED (host=oc, selector=mixdemo):
    [RUN-MIXED-TYPES] Selection contains IPDs: 4, Specs: 2, Prompts: 1. No work started. Review the selection, then run: aw oc run mixdemo --type <type> ... --allow-mixed
    ```
    Character-level agreement is ASSERTED, not eyeballed: `test_refusal_template_is_character_identical_to_the_spec` compares `REFUSAL_TEMPLATE` to the spec string and then asserts the rendered form equals that same string with ONLY `<counts>` substituted. Proven non-vacuous by MUTANT 3 below (`Review` -> `Please review` fails it).
    CODE STRING IS EXACTLY `RUN-MIXED-TYPES`:
    ```
    $ rg -n 'RUN_MIXED_TYPES = |^RUN-MIXED-TYPES' agent_workflows/run_selection_policy.py
    306:RUN_MIXED_TYPES = "RUN-MIXED-TYPES"
    ```
    `test_finding_code_string_is_exactly_run_mixed_types` pins it.
    `No work started.` IS PROVEN, not asserted: `test_refusal_path_starts_nothing_and_writes_nothing` monkeypatches `subprocess.Popen`/`run`/`check_output` to raise (so any host session would fail the test), takes a byte-level snapshot of every file in the repo tree, runs resolution + refusal, and asserts the snapshot is UNCHANGED. Structurally, every function in the module is pure with no session, lease, or write path.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest tests/test_run_selection_policy.py` output with counts, and paste the BARE `python3 -m pytest` summary line with the `git rev-parse HEAD` it was measured at, plus your own before-baseline at that same HEAD. Paste proof the tests are NOT VACUOUS: with the module's gate logic reverted or stubbed, show the gate tests FAIL. Paste the no-worsening comparison for `aw check plans` (before and after counts, both measured, not remembered).
  - Observed evidence: MEASURED at HEAD `26973ca6` (`git rev-parse HEAD` = `26973ca6a8ce3a26a4fae0dfaa44c3594446274a`).
    TARGETED MODULE (with counts, via `-o addopts=""` to clear the configured `-q`):
    ```
    $ python3 -m pytest tests/test_run_selection_policy.py -o addopts=""
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    Using --randomly-seed=948463573
    collected 65 items
    tests/test_run_selection_policy.py ..................................... [ 56%]
    ............................                                             [100%]
    ============================== 65 passed in 0.26s ==============================
    ```
    BARE SUITE, before/after, BOTH measured at the same HEAD `26973ca6` (baseline taken by moving my two new files out of the tree, then restoring them):
    ```
    BEFORE (my files absent):  15 failed, 3872 passed, 3 skipped, 4 xfailed in 36.67s
    AFTER  (my files present): 15 failed, 3937 passed, 3 skipped, 4 xfailed in 32.31s
    ```
    +65 passed, exactly my 65 tests; failures UNCHANGED at 15. All 15 are pre-existing and belong to another session's in-flight work in `tests/test_run_viewer.py` (captured list, all 15 are `RunViewerTests::*`); NONE touches `run_selection_policy`. I did not modify that file.
    NOT VACUOUS, three mutants, each reverted after measuring:
    ```
    MUTANT 1 (gate disabled: `if not classification.is_mixed:` -> `if True:`)
      => 20 failed, 45 passed   (kills the refusal, near-miss, bullet-4 and no-mutation tests)
    MUTANT 2 (lax phrase: accept {'run mixed','y','yes',''} case-folded)
      => 8 failed, 57 passed    (kills y/''/Y/YES/'Run Mixed', the tty-branch and phrase-constant tests)
    MUTANT 3 (reword refusal: 'Review the selection' -> 'Please review the selection')
      => 1 failed, 64 passed    (kills test_refusal_template_is_character_identical_to_the_spec)
    RESTORED => 65 passed in 0.21s
    ```
    `aw check plans` NO-WORSENING, both measured at HEAD `26973ca6`:
    ```
    BEFORE: ✗ FINDINGS  5 finding(s) detected across 453 plans   (errors 5, warnings 0)
    AFTER:  ✗ FINDINGS  5 finding(s) detected across 453 plans   (errors 5, warnings 0)
    ```
    It is RED and I do NOT claim it passes. All 5 findings name OTHER Sets' plans, none mine: 3x `check.ipd-dependency-findings-blocked` (`runprofile-03` `3cm15q`, `runprofile-04` `ygzq71`, `runprofile-05` `p7xhhm`) and 2x `check.lifecycle-transition-invalid` (`runnamecollapse-01` `0soncw`, `runcodes-01` `wlxkoz`). CORRECTION TO THE PLAN'S OWN BASELINE: the plan recorded 901 findings at the older HEAD `7e5ba287`; the current tree measures 5, so other Sets evidently repaired the `scope-drift` bulk in between. The bar met is no-worsening against the FRESH measurement, as the plan required (a measurement, not a memory).
    `aw sanitize --agent`: `{"outcome":"clean","exit":0,"findings":0}`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required. 5 E-leaves across 2 task groups, under the thresholds. One concern throughout: refuse a multi-type selection until the operator has seen and acknowledged it.

Open questions: NEITHER is blocking, and neither needs a maintainer decision. OQ-01 is DISSOLVED by deferring the runner wiring (the `hostcap-01` precedent), which is what lets this plan run without waiting on `rununify`. OQ-02 is DEFERRED to whoever owns the Set compiler, with its measurement preserved here so it is not lost; a mixed-type gate neither reads nor schedules a dependency graph, so it does not gate this work.

Scope fence: touch ONLY `agent_workflows/run_selection_policy.py` and `tests/test_run_selection_policy.py`, both new. Do NOT create `run_selector.py` or `run_scheduler.py` (forks of `selectors.py` and `ipd_set_plan.py`; this was the retired plan's central defect). Do NOT edit `selectors.py`, `ipd_set_plan.py`, `cli.py`, `oc_runipd.py`, or `agy_runipd.py`. Do NOT implement runtime dependency satisfaction (shipped, `8guhs0`) or runner-side backlog closure (shipped, `zhr6mc`). Do NOT use the reason code `dependency_not_met`; the runner's real state is `dependency-blocked` (`oc_runipd.py:119`) and the invented spelling has zero hits. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): paste ACTUAL runner output with the `git rev-parse HEAD` it was measured at. Do NOT claim `aw check plans` passes; it is RED on 901 pre-existing findings owned by other Sets (measured at HEAD `7e5ba287`), and the bar is no-worsening against your own fresh baseline. Do NOT describe this plan as making runs safer: it lands the gate and its message, and nothing consults them until a follow-up wires the runners. Say so plainly in the terminal history.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never `-a`, and never push. Several sessions commit to this checkout CONCURRENTLY: run `git diff --cached --name-only` before every commit and unstage anything you did not modify, with `git restore --staged <path>`. A pre-commit hook failure INVALIDATES that check, so re-run it after any failed commit attempt before retrying. Prefer `aw commit <plan> -- <paths>`, which is immune to index pollution by construction.

Post-gate lifecycle: do not claim done or move this plan until every `V-*` item is verified with concrete pasted evidence and `aw ipd lint --phase pre-transition` reports conforming; the transition is performed by `aw ipd finalize`, never by hand.
