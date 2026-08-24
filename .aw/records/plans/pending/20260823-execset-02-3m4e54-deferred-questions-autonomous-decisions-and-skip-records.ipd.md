# IPD: Deferred Questions Autonomous Decisions and Skip Records

- Date: 2026-08-23
- Kind: child
- Concern: Prevent needless interruption without hiding decisions or skipped work.
- Scope: Versioned run events, exact stop/defer classifier, generated projections, durable summaries, and answer/resume linkage.
- Scope-Paths: grandfathered
- Status: approved
- Set: execset
- Order: 2
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 3m4e54
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
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

- [ ] E-01 Extend the closed ledger compatibly with `question_raised`, `question_disposition`, `human_answer`, `autonomous_decision`, `scope_deferred`, `work_claim`, `lane_outcome`, `integration_result`, and `set_checkpoint`; reconcile the missing `investigator` role; define a SEPARATE closed Set state machine with `set_`-prefixed states `set_planned|set_running|set_waiting_input|set_partial|set_complete|set_failed|set_cancelled` (disambiguated from `run_state.py`'s per-run states per OQ-02), its legal transitions, resume semantics, coordinator-only authority, and completion refusal, and document how each Set state derives from children's run states (`set_complete` only when every required child reached verified terminal; `set_partial` when any required node is deferred).
  - Depends on: none
  - Note (verified - the "extend compatibly" is more than a frozenset edit): (1) VERSIONING: today the ledger validates by EXACT equality to `LEDGER_SCHEMA_VERSION=1` (`run_ledger_schema.py:193-205`); there are NO version-compatibility rules. "Extend compatibly ... under explicit version rules" (and V-01's old-and-new-validate requirement) is NET-NEW: E-01 must either bump to schema v2 and add an explicit acceptance/compat rule (v1 ledgers still validate; v2 adds the new kinds) or define an equivalent versioning discipline - do not silently widen the v1 frozenset. (2) PER-KIND SCHEMA: each of the 9 new kinds needs its own `_KIND_FIELDS` entry (`run_ledger_schema.py:127-163`) AND, where it carries enums (e.g. Set-state, disposition), a value-rule branch in the cascade (`:250-313`); these are not one-line frozenset additions. (3) INVESTIGATOR: add `investigator` to `run_ledger_schema.ROLES` (`:42-44`) and reconcile with `verify_roles.ROLE_INVESTIGATOR` (`verify_roles.py:42`). Hash-chaining is provided by the STORE (`run_ledger_store.py:326-327`) and needs no change - new kinds inherit it.
  - Expected outcome: every decision, skip, lane, and checkpoint is attributable and hash-chained.
  - Execution state: pending

### Material change 2: Exact no-stop classifier

- [ ] E-02 Implement a pure classifier: decide robustly and record, else defer subgraph, else defer IPD, else drain independent frontier and only then emit `hard_stop_needs_input`; route unresolved `unknown_outcome` through deterministic reconciliation and that same predicate; lexically contain legacy child `STOP` instructions.
  - Depends on: E-01
  - Expected outcome: no question terminates the Set unless input is materially required and neither subgraph nor IPD can be safely skipped.
  - Execution state: pending

### Material change 3: Inspectable and durable records

- [ ] E-03 Generate local `decisions.md`, `open-questions.md`, and `deferred-work.md`; write/update a tracked walkthrough at partial/terminal checkpoints and every integrated decision-bearing commit; promote unresolved questions to blocked backlog records with `Gate-Kind: decision`, resume command, and close-on-answer behavior; on recovery promote any local untracked decision/question checkpoint before new work.
  - Depends on: E-02
  - Note (verified - honor existing backlog validation; two net-new pieces): (1) `Gate-Kind: decision` blocked items already exist and surface in `aw attention` (`backlog.py:200-219`, `attention.py:333-366`), BUT the `decision` `Gate-Ref` is constrained to a `D<number>` id (`attention_contract.py:396,428-429`) - the RESUME COMMAND therefore CANNOT ride on the `decision` gate's `Gate-Ref`; put the resume trigger in the backlog item body (or a distinct field), not `Gate-Ref`, or the item fails validation. (2) There is NO close-on-answer / auto-resolve mechanism today (backlog status changes are manual `aw backlog set`); close-on-answer is NET-NEW work this plan owns. (3) There is NO programmatic walkthrough WRITER verb (only rename/group); the tracked walkthrough is written directly following the `.aw/records/walkthroughs/` grammar.
  - Expected outcome: the user can inspect every consultation-preferred decision and every unanswered question through normal AW records/attention.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence (E-01 is dense - it bundles a ledger-schema extension AND a Set state machine; prove BOTH independently): (a) LEDGER SCHEMA: old and new ledgers validate under explicit version rules; EACH of the nine new event kinds (`question_raised`, `question_disposition`, `human_answer`, `autonomous_decision`, `scope_deferred`, `work_claim`, `lane_outcome`, `integration_result`, `set_checkpoint`) has a positive AND a negative schema test; the added `investigator` actor role is accepted by the ledger `ROLES` set and reconciled with `verify_roles.ROLE_INVESTIGATOR` (verified divergence: today `run_ledger_schema.py:42-44` omits `investigator` while `verify_roles.py:42` defines it); (b) SET STATE MACHINE (disambiguated per OQ-02): transition-table tests cover every legal edge among `set_planned|set_running|set_waiting_input|set_partial|set_complete|set_failed|set_cancelled`, assert the Set-state names do NOT collide with `run_state` states, verify `set_complete` requires every required child at verified terminal lifecycle (and `set_partial` when any is deferred), and REJECT illegal actors, illegal edges, and completion with any unresolved required node; resume semantics and coordinator-only authority are each asserted by a test.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: exhaustive truth-table and adversarial fixtures show robust choices are recorded, deferrable subgraphs/IPDs never stop the Set, independent work drains first, and only the exact four-clause predicate yields `hard_stop_needs_input`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: a partial fixture generates consistent local projections, tracked walkthrough, attention-visible blocked backlog item, answer linkage, and successful resume while deferred E-items remain pending; crash recovery promotes a decision checkpoint before releasing another lane. SPECIFICALLY: (a) the promoted blocked backlog item passes `aw backlog check`/attention validation - its `Gate-Kind: decision` carries a valid `D<number>` `Gate-Ref` and the resume command is NOT stuffed into `Gate-Ref`; (b) the close-on-answer path is exercised: answering the question transitions the blocked item to resolved automatically (net-new behavior) and the resume proceeds.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes cover authoritative facts, stop semantics, and human inspection.

Requires explicit approval. Never synthesize consent, approval, release authority, credentials, or irreversible choices.
