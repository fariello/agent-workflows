# IPD: Specify the lifecycle automation policy before any verb implements one

- Date: 2026-09-08
- Kind: child
- Concern: How far automation may advance an artifact along the pipeline `backlog -> backlog-review -> graduate -> to-review -> reviewed -> approved -> executed` is decided by hardcoding, differently in each verb, rather than by one configurable policy a maintainer can set and an argument can override. The maintainer recorded the requirement while resolving `97df1z` OQ-02 and filed it separately because it spans every lifecycle verb. The item carries FIVE open design questions (per-transition versus per-artifact-type, whether an override may tighten as well as loosen, what the default is, whether an automated advance must stay distinguishable afterwards, and whether retirement and reversal are governed too), so writing code first would hardcode a sixth answer alongside the existing ones.
- Scope: Produce the SPEC, not the engine. Enumerate the transitions and the conditions that actually gate them today, by reading each verb; answer the five open questions with the maintainer; and define one policy predicate every verb will consult, extending the shipped `auto-approved` attestation vocabulary rather than forking it. NO verb behavior changes in this plan, so nothing can regress while the design is settled.
- Scope-Paths: .aw/records/specs
- Item-Dependencies: none
- Status: to-review
- Set: lcpolicy
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: u06zo2
- From-Backlog: rxya25

## Workflow history

- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rxya25`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. THIS PLAN DELIBERATELY PRODUCES A SPEC RATHER THAN CODE, and the reason is the item's own shape: it is a MAINTAINER REQUIREMENT with five unanswered design questions, one of which ("what is the default?") the item itself notes would "immediately break `--full-auto` unless it ships with a permissive default". A plan that implemented a policy engine would have to answer all five by fiat, which is exactly the hardcoding the item exists to end. `aw specs new` exists and mints a conforming spec, so spec-first is a supported route. NOTHING IN THIS ITEM IS OBSOLETE and no spec or pending plan covers it: grepping the specs tree and the pending plans for a lifecycle-automation policy returns nothing. THE FIRST CONSUMER HAS LANDED, WHICH SHARPENS THE ITEM RATHER THAN CLOSING IT: `97df1z` (fullauto-01) is now EXECUTED, so the `--full-auto` path that decides "may I advance this reviewed plan to ready-to-execute without a human?" is SHIPPED and is answering that question by hardcoding today. So the item's premise ("`97df1z` is the FIRST CONSUMER of a policy that does not exist") is now a live condition rather than an anticipated one. ALL THE REUSABLE MATERIAL THE ITEM CITES VERIFIES AT HEAD `a2e0438a`: the honest-attestation precedent is real and enforced (`auto-approved` is a sibling ready-to-execute tier at `ipd_schema.py:267` with `READY_TO_EXECUTE = frozenset(("approved", "auto-approved"))`, documented at `:265-266` as "an automated clear, NOT human approval", and `:398-402` enforces that only `approved` carries the human `Approval` field); the shared-predicate pattern is real (`check_engine.evaluate_blocking_close` at `:1951`); and the config home exists (`.aw/config/project.json` plus a resolved user config path). ONE ADDITIONAL PRECEDENT WORTH REUSING that the item does not name: spec `20260815-0151-01-honest-human-approval-attestation.spec.md` (`- Status: implemented`) is the closest prior art in both subject and shape, having reframed a human-only gate into an honest non-TTY attestation, and its `TRANSITION_AUTHORITY` table in `attention_contract.py` is a per-transition authority model that already exists and that a policy should extend rather than duplicate.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Replace six hardcoded answers with one written policy. The deliverable is a spec that enumerates every gated transition, states the condition set per transition, answers the five open questions, and defines the single predicate every verb will consult, so the first implementation has a contract to build against rather than a sixth opinion to add.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: inventory what is actually hardcoded today

- [ ] E-01 Inventory the ACTUAL per-transition decisions each verb makes today, by reading the code, and record them as a table in the spec. The item names the surfaces to cover: `driver_begin` (`oc_runipd.py:894`), `aw ipd finalize`, the backlog close gate (`check_engine.evaluate_blocking_close`, `:1951`), the spec status setter, and the `--full-auto` promotion path now shipped by executed plan `97df1z`. For EACH, record which transition it gates, what condition it checks, what it does on failure (refuse, warn, proceed), and whether an automated actor may perform it. THIS INVENTORY IS THE SPEC'S FOUNDATION and must be measured rather than assumed: the item's whole claim is that these answers differ per verb, and a spec that generalizes from two of five surfaces would encode the same inconsistency it exists to remove.
  - Depends on: none
  - Expected outcome: a per-verb, per-transition table of today's real behavior, each row citing the file and symbol it was read from.
  - Execution state: pending

- [ ] E-02 Enumerate the CONDITION VOCABULARY, taking the item's candidate list as the starting point and checking each against the code rather than adopting it wholesale. The candidates are: unresolved BLOCKING versus non-blocking open questions (the pre-execution gate already distinguishes these); an unfixed review finding at or above `review_findings_gate.block_at` (enforced today by `check.review-finding-unescalated`); a stale `aw ipd begin` receipt; out-of-scope changed paths needing `--scope-reason`; a `Blocks-Release` gate on the artifact; and whether an automated actor may write a terminal state at all. For each, state where it is enforced today and whether it is genuinely a POLICY question (a maintainer might reasonably set it either way) or an INVARIANT (never negotiable). Getting that split right is what stops the policy becoming a switch that can disable a correctness gate.
  - Depends on: E-01
  - Expected outcome: each condition classified as policy or invariant, with its current enforcement point cited; invariants explicitly excluded from the policy surface.
  - Execution state: pending

### Task group 2: answer the five open questions with the maintainer

- [ ] E-03 Answer the item's five open questions IN THE SPEC, each with its reasoning, because every one changes the shape of the eventual engine. (1) Is the policy per-TRANSITION, per-ARTIFACT-TYPE, or both (a backlog item graduating is not the same risk as a plan finalizing)? (2) Does an argument override LOOSEN only, or may it also TIGHTEN (loosen-only is easier to reason about; tighten-also is more useful in CI)? (3) What is the DEFAULT (fail-closed matches this repository's posture, but the item warns it "would immediately break `--full-auto` unless it ships with a permissive default for the transitions it already performs")? (4) Must an automated advance always be DISTINGUISHABLE in the record afterwards? (5) Does the policy govern only FORWARD transitions, or also retirement (`superseded`/`not-executed`) and reversal (`approved -> to-review`)? Question 3 is the one with a live blast radius, since `97df1z` is now executed and its `--full-auto` path is shipped, so a fail-closed default with no grandfathering would break a working feature on day one.
  - Depends on: E-02
  - Expected outcome: all five answered in the spec with reasoning, and question 3's answer explicitly reconciled against the shipped `--full-auto` behavior.
  - Execution state: pending

- [ ] E-04 Define ONE policy predicate consulted by every verb, following the pattern the repository has already proved rather than inventing one. `check_engine.evaluate_blocking_close` (`:1951`) backs the backlog setter, the `aw check` rules AND the opt-in pre-commit hook, so those three provably cannot diverge; the spec must require the same for the lifecycle policy. Specify its inputs (artifact type, current status, target status, the artifact's own condition state, the resolved policy, any override) and its output (permit, refuse with a reason, or permit-with-attestation). ALSO SPECIFY THE IMPORT DISCIPLINE, because the predicate will be consumed by both host drivers: it must stay stdlib-cheap and driver-agnostic, the same constraint `plan_readiness` carries, and the anti-divergence guard in `tests/test_runner_item_dependencies.py` polices that class of coupling.
  - Depends on: E-03
  - Expected outcome: one predicate specified with typed inputs and outputs, a single-authority requirement, and the import discipline stated.
  - Execution state: pending

- [ ] E-05 EXTEND the shipped attestation vocabulary rather than forking it, which the item requires explicitly ("A policy engine should EXTEND this vocabulary, not fork it"). The precedent is real and enforced: `auto-approved` is a sibling ready-to-execute tier (`ipd_schema.py:267`), documented as "an automated clear, NOT human approval" (`:265-266`), and the schema enforces that only `approved` carries the human `Approval` field (`:398-402`); `.aw/records/plans/README.md` records D65's rule that it is "set only by an automated checker, never by an executor fast-tracking its own work". ALSO EXTEND, do not duplicate, the per-transition authority model that already exists: `attention_contract.TRANSITION_AUTHORITY`, introduced by the implemented spec `20260815-0151-01-honest-human-approval-attestation.spec.md`, is already a table of who may perform which transition. Specify how a policy-permitted automated advance is recorded so it stays DISTINGUISHABLE afterwards (question 4), and state that the policy may never be used to make an automated actor's advance indistinguishable from a human's.
  - Depends on: E-04
  - Expected outcome: the spec extends `auto-approved` and `TRANSITION_AUTHORITY` explicitly, names the recording mechanism for a policy-permitted advance, and forbids indistinguishability.
  - Execution state: pending

- [ ] E-06 Write the spec through `aw specs new` and take it to `to-review`, NOT to `approved`. Use the tool rather than hand-naming: `aw specs new --title ... --slug ... --apply` mints an id6 and writes the conforming `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` with an `- Id:`. Carry `- From-Backlog: rxya25` so the provenance is machine-readable. Set the status with `aw specs set`, never by hand-editing the field, and do NOT set `approved`: that requires the maintainer's attested sign-off (`--by-human`), and this plan's five answered questions are proposals until they have it. Also state in the spec that it authorizes NO code change by itself, so a later executor cannot read it as licence to start building.
  - Depends on: E-05
  - Expected outcome: a conforming spec at `- Status: to-review` carrying `- From-Backlog: rxya25`, created and transitioned by tool, authorizing no implementation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The item is a MAINTAINER REQUIREMENT with five open questions, filed separately from `97df1z` precisely because it "spans every lifecycle verb and is far larger than the plan that surfaced it". That is the shape of a spec, not of a code change.
- THE HONEST-ATTESTATION PRECEDENT IS REAL AND ENFORCED: `auto-approved` sits in `READY_TO_EXECUTE` alongside `approved` (`ipd_schema.py:267`) and is documented as an automated clear rather than human approval (`:265-266`), with the schema enforcing that only `approved` carries `Approval` (`:398-402`).
- THE SHARED-PREDICATE PATTERN IS PROVED: `evaluate_blocking_close` (`check_engine.py:1951`) backs three surfaces at once so they cannot diverge. That is the model E-04 requires.
- A PER-TRANSITION AUTHORITY TABLE ALREADY EXISTS: `attention_contract.TRANSITION_AUTHORITY`, from the implemented spec `20260815-0151-01-honest-human-approval-attestation.spec.md`. A policy must extend it rather than add a parallel table.
- Config has a home already (`.aw/config/project.json`, plus a resolved user config path), so the policy needs no new machinery to live somewhere.
- Spec status is OWNED by `aw specs` (`set`/`note`/`check`), a spec carries a bare-enum `- Status:` through `draft -> to-review -> reviewed -> approved -> ...`, and an agent may record human approval only with an explicit `--by-human` attestation. An agent may never set `implemented`.
- `aw specs new` mints the id6 and the conforming filename, so specs must not be hand-named.
- A spec may carry `- From-Backlog:`, and `aw check` flags a value resolving to no backlog item, so the provenance link is machine-checked.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | THE FIRST CONSUMER IS NOW SHIPPED, which makes the item live rather than anticipatory: `97df1z` is EXECUTED, so the `--full-auto` path that decides whether to advance a reviewed plan without a human is running and answering by hardcoding. | `.aw/records/plans/executed/20260829-fullauto-01-97df1z-...ipd.md` |
| F-2 | Nothing covers the item: no spec and no pending plan describes a lifecycle automation policy or a per-transition permission model. | grep over `.aw/records/specs/` and `.aw/records/plans/pending/` at `a2e0438a` |
| F-3 | The `auto-approved` tier exists, is in `READY_TO_EXECUTE`, and is documented as an automated clear rather than human approval. | `ipd_schema.py:265-267` |
| F-4 | The schema ENFORCES the distinction the item wants preserved: only `approved` requires the human `Approval` field, so `auto-approved` cannot masquerade as human sign-off. | `ipd_schema.py:396-402` |
| F-5 | The single-predicate pattern is proved in-tree and is the model to copy. | `check_engine.evaluate_blocking_close` at `:1951` |
| F-6 | A per-transition AUTHORITY table already exists and must be extended rather than duplicated. | `attention_contract.TRANSITION_AUTHORITY`, from spec `20260815-0151-01-honest-human-approval-attestation.spec.md` (`- Status: implemented`) |
| F-7 | The config home exists, so the policy has somewhere to live without new machinery. | `.aw/config/project.json`; `config.config_path()` resolves a user config |
| F-8 | QUESTION 3 HAS A LIVE BLAST RADIUS: a fail-closed default would break the shipped `--full-auto` unless the transitions it already performs are grandfathered, which the item itself warns about. | the item's own open-question list, read against F-1 |
| F-9 | `aw specs new` mints the id6 and the conforming name, so a spec-first graduation is a supported, tooled route rather than a hand-authored file. | `aw specs new --help` at `a2e0438a` |
| F-10 | The closest prior art in both subject and shape is an IMPLEMENTED spec that reframed a human-only gate into an honest attestation, so the design has a precedent to follow rather than inventing an attestation model. | `.aw/records/specs/20260815-0151-01-honest-human-approval-attestation.spec.md` |

## Proposed changes (ordered, validatable)

1. Inventory each verb's real per-transition decision, with citations (E-01).
2. Classify each candidate condition as policy or invariant (E-02).
3. Answer the five open questions in the spec, reconciling the default against shipped `--full-auto` (E-03).
4. Specify ONE predicate with typed inputs, outputs and import discipline (E-04).
5. Extend `auto-approved` and `TRANSITION_AUTHORITY`; forbid indistinguishability (E-05).
6. Create the spec by tool at `to-review` with `From-Backlog: rxya25` (E-06).

## Deferred / out of scope (with reason)

- IMPLEMENTING THE POLICY ENGINE. Deliberately not here: the item has five unanswered design questions and one of them (the default) can break a shipped feature. Code written before those answers would hardcode a sixth opinion beside the five this item exists to consolidate. Implementation is a follow-on Set graduated FROM the approved spec.
- CHANGING ANY VERB'S CURRENT BEHAVIOR, including `--full-auto`. Nothing regresses while the design is settled, which is the main safety property of a spec-first graduation here.
- MIGRATING THE EXISTING HARDCODED DECISIONS onto the policy. That is the implementation, and its sequencing is itself a design question (all verbs at once, or the `--full-auto` path first) that the spec should answer rather than a plan presume.
- THE `auto-approved` VOCABULARY ITSELF. Already shipped and enforced; the spec extends it and must not redefine it.
- RETIREMENT AND REVERSAL SEMANTICS beyond DECIDING whether they are in scope (question 5). If the answer is yes, specifying them fully may warrant its own spec section or its own spec; the plan does not presume the answer.
- CONFIG SCHEMA CHANGES. `.aw/config/project.json` is `config_version 2` and adding a policy block is an implementation concern; the spec names where the policy lives without editing the schema.

## Scope check

- Over-scope: none. `Scope-Paths` is the specs tree only, because the sole artifact this plan produces is a spec.
- Under-scope: deliberately large. No code, no tests of behavior, no verb change. A reviewer who wants implementation in the same pass should reject this shape rather than extend it, since the five open questions are the reason it is spec-first.

## Required tests / validation

- `python3 -m pytest` bare, per the repository contract, to prove this records-only change breaks nothing. Paste the ACTUAL summary line. Baseline on `main` is 1 failed, 5648 passed (the known `test_orchestrator_retirement` failure); judge on the DELTA, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
- `python3 -m agent_workflows specs check` (or `aw check specs`) must report the new spec conforming, with no new diagnostic.
- `python3 -m agent_workflows check` must not gain a diagnostic, in particular no `check.from-backlog-dangling` for the spec's `From-Backlog: rxya25`.
- NOTE there is no behavioral validation to run, by design: this plan changes no code. The verification is that the spec is conforming, complete against the item's five questions, and cites real code for every claim in its inventory.

## Spec / documentation sync

THIS PLAN'S ENTIRE DELIVERABLE IS A SPEC, so the sync is the work. The spec is created with `aw specs new` (never hand-named), transitioned with `aw specs set` (never by hand-editing `- Status:`), and carries `- From-Backlog: rxya25` so `aw check` can verify the provenance link. It is taken to `to-review` and NOT to `approved`: approval is the maintainer's attested act (`--by-human`), and this plan's answers to the five open questions are PROPOSALS until then. The spec must state explicitly that it authorizes no code change, so a later executor cannot mistake it for licence to build. TWO EXISTING SPECS ARE NEIGHBOURS and the new spec must position itself against both rather than silently overlapping: `20260815-0151-01-honest-human-approval-attestation.spec.md` (`implemented`) owns the human-attestation model and `TRANSITION_AUTHORITY`, and the IPD spec owns the plan lifecycle's own status vocabulary. If the design requires AMENDING either, that is a spec edit and the path must be declared in `Scope-Paths` with the reason given, per the plan-may-amend-a-spec rule; this plan declares only the specs tree because it expects to ADD, not amend.

## Open questions

### OQ-01: Should the policy's default be fail-closed, given that `--full-auto` is already shipped?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: OPTION (b), A PERMISSIVE DEFAULT MATCHING TODAY'S BEHAVIOR, with fail-closed available per transition. The recommendation at authoring was (a) (fail-closed plus an explicit grandfather list) and the maintainer chose otherwise, so the reasoning and the cost are recorded here rather than left implicit.
  WHAT THIS DECIDES, stated plainly because it is a change of character and not merely a default value: the spec's policy will be ALLOW-UNLESS-FORBIDDEN for lifecycle automation, which INVERTS this repository's posture everywhere else (refuse-unless-allowed). The spec MUST say so explicitly and MUST say it was a deliberate choice, or a later reader will read it as an oversight and "correct" it, breaking whatever automation has come to rely on it by then.
  WHY IT IS DEFENSIBLE, since the plan should not record a choice as arbitrary. FIRST, NOTHING CAN BREAK on the day the policy lands, which was the entire hazard the grandfather list existed to avoid; a list that must be maintained accurately is itself a failure mode, and this repository already carries one hand-maintained pattern list (the gitignore back-fill) whose non-genericity caused a separate defect this session. SECOND, the shipped automation is ALREADY CAREFUL in the way that matters: measured at HEAD, `--full-auto` performs exactly ONE advance, `reviewed` -> `auto-approved`, and it deliberately does NOT claim human `approved`, with the transition message reading "auto-approved by --full-auto: review readiness cleared (not human approval)" (`agy_runipd.py:830`, `:837-849`). So the distinction the policy most needs to protect is already preserved by the one thing the default permits. THIRD, a permissive default does not mean an unbounded one: fail-closed remains available PER TRANSITION, so the transitions that genuinely must never be automated (human `approved`, and `implemented` on a spec) can each be closed individually and explicitly, which is arguably clearer than a blanket refusal plus an exception list.
  WHAT THE SPEC MUST THEREFORE CARRY, as a direct consequence of this answer and not as separate work: (1) the inverted posture stated as deliberate, with this reasoning; (2) the per-transition fail-closed mechanism, since it is now the ONLY thing standing between automation and a transition that must stay human; (3) an explicit, named list of transitions that are fail-closed FROM THE START, because under a permissive default an unlisted transition is PERMITTED, so omission is now the dangerous direction rather than the safe one. That third point is the inverse of the grandfather list and carries the same maintenance burden, which a reviewer should weigh: the cost did not disappear, it moved.
  THE INVENTORY IS STILL REQUIRED. E-01 must still enumerate every transition automation performs today, because under a permissive default that inventory is what tells a maintainer what is already happening without being asked. It is no longer a grandfather list; it is the baseline the per-transition closures are chosen against.
### OQ-02: Should an argument override be able to TIGHTEN, or only LOOSEN?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-08: ALLOW BOTH DIRECTIONS, AND RECORD ONLY THE LOOSENING ONES. This upholds the recommendation, and it is materially more important than it looked at authoring because of the maintainer's answer to OQ-01.
  WHY THE ASYMMETRY IS THE POINT: OQ-01 resolved to a PERMISSIVE default (allow-unless-forbidden), so TIGHTENING is now the direction that ADDS safety and LOOSENING is the direction that REMOVES it. Under the fail-closed default originally recommended, the two directions would have had the opposite significance. So the recording rule follows the risk rather than the mechanism: a tightening override needs no justification because being stricter is never the hazardous choice, while a loosening override is written into the artifact so a relaxation is auditable rather than silent.
  THE CI CASE IS WHY BOTH DIRECTIONS ARE NEEDED, and it is concrete rather than hypothetical: a job may want to refuse ANY automated advance while building a release, which is stricter than the repository policy. If the policy could not be tightened, that job would have to reimplement the check, and a second copy of the rule is exactly the divergence E-04's single-predicate requirement exists to prevent. This is the same argument that makes `evaluate_blocking_close` a single shared predicate.
  FOLLOW THE EXISTING PRECEDENT FOR AUDITABILITY rather than inventing a mechanism: `--allow-open-questions` is already folded into the recorded actor string so the override is visible in the artifact's own history. A loosening override should be recorded the same way, which means a reader of the artifact sees it without consulting a run log (and note a run log would be the wrong home anyway, since `.aw/records/runs/` is gitignored and per-machine).
  ONE THING THE SPEC MUST NOT DO, as a consequence of both answers together: it must not let a LOOSENING override reach a transition that is fail-closed FOR SAFETY rather than by mere default. Under a permissive default the per-transition closures are the only real protection (see OQ-01), so if a loosening flag can open them, they are decorative. The spec must distinguish a transition that is closed by POLICY (a maintainer's choice, loosenable with a recorded override) from one that is closed by CONTRACT (human `approved`, and `implemented` on a spec, which no flag may open). That distinction is not optional and it did not exist in the question as authored.
## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the inventory table from the written spec, with at least the five named surfaces present, and for EACH row paste the file and symbol it was read from. A row without a citation does not satisfy this item, because the whole claim being tested is that these behaviors differ per verb and were measured rather than assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the condition table showing each of the item's six candidate conditions classified as POLICY or INVARIANT with its current enforcement point cited, and paste the spec sentence that excludes invariants from the policy surface.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: quote the spec's answer to each of the five questions, individually and in order. For question 3, paste the passage that reconciles the chosen default against the shipped `--full-auto` behavior, naming the transitions it currently performs.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the predicate's specified signature (inputs and the three-way output) and the spec sentence requiring every surface to call it and none to reimplement it. Paste the stated import discipline (stdlib-cheap, driver-agnostic) and the reason it exists.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the spec passages that EXTEND `auto-approved` and `TRANSITION_AUTHORITY` by name, the recording mechanism for a policy-permitted automated advance, and the sentence forbidding an automated advance from being indistinguishable from a human's. Paste the `ipd_schema.py` lines cited so the extension is anchored to real code.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `aw specs new ... --apply` invocation and its output showing the minted id6 and conforming filename; paste the spec's front matter showing `- Status: to-review` and `- From-Backlog: rxya25`; paste the `aw specs set` command used (proving the status was tool-set, not hand-edited); paste `aw check` showing no new diagnostic and no `check.from-backlog-dangling`; and paste the bare `python3 -m pytest` summary line compared to the stated baseline.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

OQ-01 is BLOCKING for the spec's CONTENT rather than for starting the work: E-01 and E-02 are pure inventory and can proceed, but E-03 cannot answer question 3 without the maintainer's ruling on the default, and that ruling determines whether a shipped feature breaks. A reviewer should also note the deliberate shape: this plan produces a SPEC and changes no code, because the item carries five unanswered design questions and implementing before they are answered would add a sixth hardcoded opinion to the five it exists to consolidate.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Create the spec with `aw specs new` and transition it with `aw specs set`; never hand-name a spec and never hand-edit its `- Status:`. Do NOT set the spec `approved` (that is the maintainer's attested act) and never set it `implemented` (an agent may not). Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line even though no code changes, so the records-only claim is evidenced. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
