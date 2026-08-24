# IPD: Deferred Questions Autonomous Decisions and Skip Records

- Date: 2026-08-23
- Kind: child
- Concern: Prevent needless interruption without hiding decisions or skipped work.
- Scope: Versioned run events, exact stop/defer classifier, generated projections, durable summaries, and answer/resume linkage.
- Scope-Paths: grandfathered
- Status: executed
- Set: execset
- Order: 2
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 3m4e54

## Workflow history
- 2026-08-24 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us (ipdrunner run-20260824T150827Z-2301181)): execset Order 02: Set coordination records, no-stop classifier, and separate Set state machine
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-23 /plan-review focused (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (versioning discipline is net-new, made explicit), PR-002 (per-kind _KIND_FIELDS + value rules, not a frozenset edit), PR-003 (OQ-02 human-resolved: separate Set machine, set_-prefixed names + run_state mapping), PR-004 (OQ-03 human-resolved: reuse append-a-newer-record supersession, no new `supersedes` kind), PR-005 (resume command cannot ride on decision Gate-Ref; close-on-answer is net-new), PR-006 (reconciled dense-vs-standard sizing note), PR-007 (corrected STOP wording + flagged shared always-loaded surface).
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003 (right-sizing, human-resolved: keep exception-sized E-01, strengthen V-01 to per-event-kind + per-transition evidence; investigator-role divergence noted).
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created from stop-policy and record-taxonomy audit.

## Goal

Make autonomous decisions and deferrals explicit, durable, reviewable, and resumable while stopping the Set only when the user’s two conditions are both true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Versioned events

- [x] E-01 Extend the closed ledger compatibly with `question_raised`, `question_disposition`, `human_answer`, `autonomous_decision`, `scope_deferred`, `work_claim`, `lane_outcome`, `integration_result`, and `set_checkpoint`; reconcile the missing `investigator` role; define a SEPARATE closed Set state machine with `set_`-prefixed states `set_planned|set_running|set_waiting_input|set_partial|set_complete|set_failed|set_cancelled` (disambiguated from `run_state.py`'s per-run states per OQ-02), its legal transitions, resume semantics, coordinator-only authority, and completion refusal, and document how each Set state derives from children's run states (`set_complete` only when every required child reached verified terminal; `set_partial` when any required node is deferred).
  - Depends on: none
  - Note (verified - the "extend compatibly" is more than a frozenset edit): (1) VERSIONING: today the ledger validates by EXACT equality to `LEDGER_SCHEMA_VERSION=1` (`run_ledger_schema.py:193-205`); there are NO version-compatibility rules. "Extend compatibly ... under explicit version rules" (and V-01's old-and-new-validate requirement) is NET-NEW: E-01 must either bump to schema v2 and add an explicit acceptance/compat rule (v1 ledgers still validate; v2 adds the new kinds) or define an equivalent versioning discipline - do not silently widen the v1 frozenset. (2) PER-KIND SCHEMA: each of the 9 new kinds needs its own `_KIND_FIELDS` entry (`run_ledger_schema.py:127-163`) AND, where it carries enums (e.g. Set-state, disposition), a value-rule branch in the cascade (`:250-313`); these are not one-line frozenset additions. (3) INVESTIGATOR: add `investigator` to `run_ledger_schema.ROLES` (`:42-44`) and reconcile with `verify_roles.ROLE_INVESTIGATOR` (`verify_roles.py:42`). Hash-chaining is provided by the STORE (`run_ledger_store.py:326-327`) and needs no change - new kinds inherit it.
  - Expected outcome: every decision, skip, lane, and checkpoint is attributable and hash-chained.
  - Execution note: (versioning, D18-3m4e54-D1) bumped `LEDGER_SCHEMA_VERSION` 1->2 and added `SUPPORTED_SCHEMA_VERSIONS={1,2}`; split `RECORD_KINDS` into `RECORD_KINDS_V1` (valid at v1 and v2) and `RECORD_KINDS_V2_ONLY` (the 9 new kinds, version-gated by new finding `RL-E018` so a v1 record carrying a v2-only kind is rejected). v1 records still validate unchanged (RL-E012 now checks membership in SUPPORTED_SCHEMA_VERSIONS). Added `_KIND_FIELDS` entries + value-rule branches (RL-E050..E057) for the 9 kinds (disposition/lane-outcome/integration-result enums; human_answer=human-only; integration_result/set_checkpoint/autonomous_decision authority; set_checkpoint set_state validated against `set_state.ALL_SET_STATES`). Added `investigator` to `run_ledger_schema.ROLES`, reconciling the prior divergence with `verify_roles.ROLE_INVESTIGATOR`. Hash-chaining inherited from the store (no store change). Created `agent_workflows/set_state.py`: the SEPARATE closed Set state machine with `set_`-prefixed states, a full transition table (SetTransitionRule + validate_set_transition/check_set_transition mirroring run_state's API), coordinator-only authority (human authorizes cancel), completion refusal (`SS-COMPLETION-REFUSED` when `all_required_children_verified_terminal` is false), and `derive_set_state()` deriving the Set state from children's run states (set_complete only when all-verified and none deferred; set_partial when any deferred).
  - Execution state: performed

### Material change 2: Exact no-stop classifier

- [x] E-02 Implement a pure classifier: decide robustly and record, else defer subgraph, else defer IPD, else drain independent frontier and only then emit `hard_stop_needs_input`; route unresolved `unknown_outcome` through deterministic reconciliation and that same predicate; lexically contain legacy child `STOP` instructions.
  - Depends on: E-01
  - Expected outcome: no question terminates the Set unless input is materially required and neither subgraph nor IPD can be safely skipped.
  - Execution note: created `agent_workflows/set_stop_policy.py`. `hard_stop_predicate()` is the EXACT four-clause conjunction (`needs_human AND no_robust_decision AND cannot_defer_subgraph AND cannot_defer_ipd`). `classify(QuestionSituation)` applies the ordered ladder: robust decision -> ACTION_DECIDE; not-materially-needed -> ACTION_DECIDE (least-disruptive default); can defer subgraph -> ACTION_DEFER_SUBGRAPH; can defer IPD -> ACTION_DEFER_IPD; else drain the independent frontier first (ACTION_DRAIN_THEN_STOP) and only with no frontier emit ACTION_HARD_STOP. An `is_unknown_outcome` situation short-circuits to ACTION_RECONCILE_UNKNOWN (deterministic reconciliation, not a human stop). `contain_child_stop()` lexically detects the literal `STOP and report` and marks it child-scoped (return control to the Set coordinator), leaving single-IPD execution unchanged.
  - Execution state: performed

### Material change 3: Inspectable and durable records

- [x] E-03 Generate local `decisions.md`, `open-questions.md`, and `deferred-work.md`; write/update a tracked walkthrough at partial/terminal checkpoints and every integrated decision-bearing commit; promote unresolved questions to blocked backlog records with `Gate-Kind: decision`, resume command, and close-on-answer behavior; on recovery promote any local untracked decision/question checkpoint before new work.
  - Depends on: E-02
  - Note (verified - honor existing backlog validation; two net-new pieces): (1) `Gate-Kind: decision` blocked items already exist and surface in `aw attention` (`backlog.py:200-219`, `attention.py:333-366`), BUT the `decision` `Gate-Ref` is constrained to a `D<number>` id (`attention_contract.py:396,428-429`) - the RESUME COMMAND therefore CANNOT ride on the `decision` gate's `Gate-Ref`; put the resume trigger in the backlog item body (or a distinct field), not `Gate-Ref`, or the item fails validation. (2) There is NO close-on-answer / auto-resolve mechanism today (backlog status changes are manual `aw backlog set`); close-on-answer is NET-NEW work this plan owns. (3) There is NO programmatic walkthrough WRITER verb (only rename/group); the tracked walkthrough is written directly following the `.aw/records/walkthroughs/` grammar.
  - Expected outcome: the user can inspect every consultation-preferred decision and every unanswered question through normal AW records/attention.
  - Execution note: created `agent_workflows/set_records.py`. `write_local_projections()` writes `decisions.md`/`open-questions.md`/`deferred-work.md` into the untracked `.aw/workflow-artifacts/<workflow>/<run-id>/` dir (the local authoritative run convention, gitignored, deliberately NOT routed through resolve_record_path). Pure renderers mark superseded decisions (via `prev`) and drop answered/disposed questions. `write_walkthrough()` writes a TRACKED walkthrough to `.aw/records/walkthroughs/` using `artifact_naming.build_clustered_name(..., artifact_type="walkthrough")` + `resolve_record_path` + `atomic_write` (verified clustered-conformant). `promote_question_to_backlog()` creates a blocked `Gate-Kind: decision` item with `Gate-Ref=D<number>` and the RESUME COMMAND in the item BODY (never Gate-Ref); it fails closed via `attention_contract.validate_gate_ref` + `backlog.validate_item` BEFORE writing. `close_on_answer()` is the NET-NEW auto-resolve: it transitions the blocked item blocked->done, drops gate fields, appends a history line, and moves it to `done/`, staying validation-conformant. `promote_local_checkpoints()` writes a tracked partial walkthrough on recovery before new work (idempotent no-op when nothing to promote).
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Runtime questions must not be appended to approved IPDs' authoring-time Open Questions.
- `.aw/workflow-artifacts/<workflow>/<run-id>/` is the local authoritative run convention and is intentionally untracked.
- Blocked backlog items already support `Gate-Kind: decision` and surface in `aw attention`; walkthroughs are the durable narrative record.
- `run_gates.py` currently stops every headless human gate and therefore needs set-level containment/refinement, not removal of consent gates.

## Findings

The current ledger is closed and cannot truthfully store decisions/questions (verified: `run_ledger_schema.py:47-70` defines a closed `RECORD_KINDS` frozenset and fails closed on unknown kinds; `question_raised`/`work_claim` etc. do not exist yet). Existing `STOP and report` text is child-scoped in practice but not stated. A run with deferred work needs a first-class `partial` result and must leave affected IPDs pending.

Right-sizing note (/plan-review 2026-08-23, human-resolved with Order 03 OQ-02): E-01 is dense (it bundles the ledger-schema extension AND the Set state machine) but is intentionally kept as ONE `standard`-sized item because the two parts are cohesive; V-01 was strengthened to require independent per-event-kind and per-transition evidence rather than splitting the E-item. (Front-matter `Size assessment: standard` is retained deliberately; "dense" here means conceptually loaded, not over the count threshold.)

## Proposed changes (ordered, validatable)

```text
hard_stop = needs_human
            AND no_robust_decision
            AND cannot_defer_subgraph
            AND cannot_defer_ipd
```

Autonomous decision fields include scope, selected option, alternatives, basis/evidence, why no prompt, `consultation_preferred`, confidence, reversibility, blast radius, affected files, and validation. Question fields include context, why input is required, affected nodes/descendants, disposition, options, recommendation, backlog ref, and resume trigger. Record decisions before mutation; a reversal is represented by appending a NEWER `autonomous_decision`/`question_disposition` record carrying a `supersedes`/`prev` pointer to the record it overrides (reusing the ledger's existing append-a-newer-record supersession idiom - `correction`, `requirement_revision` prev->new digest, later-verifier-supersedes-earlier - NOT a new `supersedes` event kind, per OQ-03).

## Deferred / out of scope (with reason)

- Product-level ADR content is updated only when within approved scope; otherwise create backlog follow-up.
- Comms and record-history sidecars are not decision stores.

## Scope check

- Over-scope: none.
- Under-scope: unknown-outcome side effects must keep the existing explicit reconciliation requirement.

## Required tests / validation

Truth-table every classifier and Set-state transition; adversarially test trivial questions, missing tone, release approval, ambiguous target repo, all-children-deferred, unknown-outcome reconcile/defer, illegal actor/transition, completion refusal, ledger compatibility, decision checkpoint crash recovery, backlog promotion, answer/resume, and no false completion.

## Spec / documentation sync

Update lifecycle wording so a child's `STOP and report` returns control to the Set coordinator (the literal `STOP and report` text - not the plan-coined `STOP THIS IPD` - is what exists, and it lives on AUTHORITATIVE SHARED surfaces: `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:20`, the canonical spec `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md:35`, and the always-loaded AGENTS block generated from `engine.py:1148`). Because today this text is NOT stated as child- vs Set-scoped, adding the "return control to the Set coordinator" semantics is a real doc change on a shared/always-loaded surface, not a child-local edit - keep it additive and backward-compatible for single-IPD (non-Set) execution. Also define local versus durable records and partial status.

## Open questions

### OQ-01: Should every tactical choice reach DECISIONS.md?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. Keep tactical/reversible choices in the run decision projection and durable walkthrough; promote only material product decisions.

### OQ-02: How does the Set state machine relate to the existing `run_state` machine?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review): KEEP the Set-level state machine SEPARATE from `run_state.py` (different granularities: coordinator-of-runs vs one run/step; merging would overload `run_state`'s per-step transition table). E-01 MUST (a) disambiguate the Set state token names so they do not collide with `run_state`'s bare `running|complete|failed|cancelled` (prefix `set_`, i.e. `set_planned|set_running|set_waiting_input|set_partial|set_complete|set_failed|set_cancelled`), and (b) document how each Set state derives from children's run states - a Set is `set_complete` ONLY when every required child run reached verified terminal lifecycle, and `set_partial` when any required node is deferred.

### OQ-03: New `supersedes` event kind, or reuse the existing supersession idiom?

- Blocking: no
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human decision (2026-08-23, /plan-review): REUSE the existing append-a-newer-record supersession pattern; do NOT add a net-new `supersedes` kind. Represent a reversed decision as a NEWER `autonomous_decision`/`question_disposition` record carrying a `supersedes`/`prev` pointer to the record it overrides, consistent with the ledger's existing `correction`, `requirement_revision` (`prev_digest -> new_digest`, `run_freeze.Revision`), and later-verifier-decision-supersedes-earlier idioms. Keeps the kind set minimal and the reversal semantics consistent with the rest of the ledger.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence (E-01 is dense - it bundles a ledger-schema extension AND a Set state machine; prove BOTH independently): (a) LEDGER SCHEMA: old and new ledgers validate under explicit version rules; EACH of the nine new event kinds (`question_raised`, `question_disposition`, `human_answer`, `autonomous_decision`, `scope_deferred`, `work_claim`, `lane_outcome`, `integration_result`, `set_checkpoint`) has a positive AND a negative schema test; the added `investigator` actor role is accepted by the ledger `ROLES` set and reconciled with `verify_roles.ROLE_INVESTIGATOR` (verified divergence: today `run_ledger_schema.py:42-44` omits `investigator` while `verify_roles.py:42` defines it); (b) SET STATE MACHINE (disambiguated per OQ-02): transition-table tests cover every legal edge among `set_planned|set_running|set_waiting_input|set_partial|set_complete|set_failed|set_cancelled`, assert the Set-state names do NOT collide with `run_state` states, verify `set_complete` requires every required child at verified terminal lifecycle (and `set_partial` when any is deferred), and REJECT illegal actors, illegal edges, and completion with any unresolved required node; resume semantics and coordinator-only authority are each asserted by a test.
  - Observed evidence: `python3 -m pytest tests/test_set_coordination.py::LedgerVersioningV01 tests/test_set_coordination.py::NewKindsPosNegV01 tests/test_set_coordination.py::SetStateMachineV01` -> `23 passed`; `python3 -m pytest tests/test_run_ledger_schema.py` -> `10 passed` (updated round-trip covers all 21 kinds). (a) LedgerVersioningV01: v1 ledger still validates (test_v1_ledger_still_validates), SUPPORTED_SCHEMA_VERSIONS={1,2} + LEDGER_SCHEMA_VERSION==2 (test_supported_versions), v2-only kind rejected at v1 with RL-E018 (test_v2_only_kind_rejected_at_v1), 999 rejected RL-E012, `investigator` in ROLES and == verify_roles.ROLE_INVESTIGATOR (test_investigator_role_accepted_and_reconciled). NewKindsPosNegV01: every one of the 9 kinds has a positive test + a negative test (missing field or bad enum/authority), incl. RL-E050 (disposition), RL-E051 (human_answer human-only), RL-E052 (lane outcome), RL-E054 (integration authority), RL-E055 (set_checkpoint set_state token), RL-E057 (autonomous_decision authority). (b) SetStateMachineV01: test_no_collision_with_run_state (ALL_SET_STATES disjoint from run_state.ALL_STATES; all `set_`-prefixed), test_legal_edges (every legal edge), test_illegal_edge_rejected (SS-ILLEGAL-TRANSITION), test_illegal_actor_rejected (SS-UNAUTHORIZED-ACTOR), test_completion_refused_without_all_verified (SS-COMPLETION-REFUSED + SetCompletionRefusedError raised), test_completion_allowed_when_all_verified, test_terminal_state_immutable, test_human_can_cancel_coordinator_authority_default (human cancels; human cannot drive planned->running), test_derivation (set_complete only when all-verified & none deferred; set_partial when any deferred).
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: exhaustive truth-table and adversarial fixtures show robust choices are recorded, deferrable subgraphs/IPDs never stop the Set, independent work drains first, and only the exact four-clause predicate yields `hard_stop_needs_input`.
  - Observed evidence: `python3 -m pytest tests/test_set_coordination.py::ClassifierV02` -> `11 passed`. test_predicate_only_all_four exhaustively checks the 16-row 4-bit truth table (hard_stop true IFF all four clauses true). Adversarial cases: test_robust_decision_never_stops, test_trivial_question_no_human_proceeds, test_defer_subgraph_beats_stop, test_defer_ipd_beats_stop, test_drain_then_stop (drains the frontier first, drain_first populated), test_hard_stop_only_when_all_four_and_no_frontier, test_release_approval_cannot_be_synthesized (a release-approval question stops, NEVER auto-decides), test_unknown_outcome_routes_to_reconcile (ACTION_RECONCILE_UNKNOWN, not a human stop), test_stop_containment_child_scope (legacy `STOP and report` recognized as child-scoped), test_frontier_after_drain.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: a partial fixture generates consistent local projections, tracked walkthrough, attention-visible blocked backlog item, answer linkage, and successful resume while deferred E-items remain pending; crash recovery promotes a decision checkpoint before releasing another lane. SPECIFICALLY: (a) the promoted blocked backlog item passes `aw backlog check`/attention validation - its `Gate-Kind: decision` carries a valid `D<number>` `Gate-Ref` and the resume command is NOT stuffed into `Gate-Ref`; (b) the close-on-answer path is exercised: answering the question transitions the blocked item to resolved automatically (net-new behavior) and the resume proceeds.
  - Observed evidence: `python3 -m pytest tests/test_set_coordination.py::RecordsV03` -> `8 passed`. test_local_projections_written (decisions/open-questions/deferred-work.md written with D1/consultation_preferred/Q1/a:E-03 content), test_superseded_decision_marked (a `prev`-pointing newer decision marks D1 SUPERSEDED), test_answered_question_not_open (a human_answer removes Q1 from open-questions), test_walkthrough_conformant (tracked walkthrough passes artifact_naming.is_clustered_conformant(expected_type='walkthrough')). (a) test_backlog_promotion_valid_and_resume_not_in_gate_ref: promoted item Status=blocked, Gate-Kind=decision, Gate-Ref=D1, resume command present in BODY and NOT in Gate-Ref, and `backlog.validate_item` returns []. (b) test_close_on_answer_transitions_blocked_to_done: close_on_answer moves the item to done/, Status=done, gate fields dropped, still validation-clean, original blocked file removed. test_recovery_promotes_checkpoint + test_recovery_noop_when_nothing_to_promote: recovery writes a tracked partial walkthrough before new work, and is a no-op when there is nothing to promote.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes cover authoritative facts, stop semantics, and human inspection.

Requires explicit approval. Never synthesize consent, approval, release authority, credentials, or irreversible choices.
