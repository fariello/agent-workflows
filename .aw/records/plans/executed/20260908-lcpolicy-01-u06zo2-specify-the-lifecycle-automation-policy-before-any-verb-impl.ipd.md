# IPD: Specify the lifecycle automation policy before any verb implements one

- Date: 2026-09-08
- Kind: child
- Concern: How far automation may advance an artifact along the pipeline `backlog -> backlog-review -> graduate -> to-review -> reviewed -> approved -> executed` is decided by hardcoding, differently in each verb, rather than by one configurable policy a maintainer can set and an argument can override. The maintainer recorded the requirement while resolving `97df1z` OQ-02 and filed it separately because it spans every lifecycle verb. The item carries FIVE open design questions (per-transition versus per-artifact-type, whether an override may tighten as well as loosen, what the default is, whether an automated advance must stay distinguishable afterwards, and whether retirement and reversal are governed too), so writing code first would hardcode a sixth answer alongside the existing ones.
- Scope: Produce the SPEC, not the engine. Enumerate the transitions and the conditions that actually gate them today, by reading each verb; answer the five open questions with the maintainer; and define one policy predicate every verb will consult, extending the shipped `auto-approved` attestation vocabulary rather than forking it. NO verb behavior changes in this plan, so nothing can regress while the design is settled.
- Scope-Paths: .aw/records/specs
- Item-Dependencies: none
- Status: executed
- Set: lcpolicy
- Order: 1
- Highest E allocated: 06
- Readiness: go-pending-approval
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: u06zo2
- From-Backlog: rxya25

## Workflow history
- 2026-09-20 executed (aw oc run model=uri/its_direct/pt3-claude-opus-5-1m-us variant=high profile=opus): aw oc run self-finalize: u06zo2 verified (set lcpolicy, attempt 1).
- 2026-09-13 approved (aw set): status set to approved

- 2026-09-10 readiness re-check (opencode its_direct/pt3-claude-opus-5-1m-us): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: `plan_readiness.has_unresolved_blocking_question` -> False; `review_findings.subject_gating_blocks` -> empty; `plan_readiness.newest_verdict` polarity -> neutral (not negative). Specifically, its two remaining open questions are BOTH `Blocking: no` (OQ-03, OQ-05), which under the maintainer ruling of 2026-09-10 is not a not-ready condition. Performed at HEAD `84111de2` at the maintainer's explicit instruction of 2026-09-10, who was shown that 10 of 15 `no-go` plans were held by stale bookkeeping and chose to have them hand-fixed with evidence recorded rather than re-reviewed. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-09-09 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review complete: REVIEWED - OPEN QUESTIONS; PR-001..PR-008; three of the item's five design questions raised as OQ-03/04/05, OQ-04 blocking (irreversible indistinguishability property); Readiness no-go pending that answer

- 2026-09-09 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-008. Reviewed at HEAD `d45bf884`; `aw ipd lint` conforming at `--phase author` before revisions. SELF-REVIEW (same agent/model authored the plan), so the method was to GO LOOKING for the automated advances the plan's inventory would have to cover, rather than re-reading its prose. That produced both blockers. (1) BLOCKER PR-001: THE INVENTORY IS INCOMPLETE, AND UNDER OQ-01's PERMISSIVE DEFAULT AN OMITTED TRANSITION IS A PERMITTED ONE, which inverts the usual cost of a missing row from "a gate is not applied" to "no gate exists". The item's five surfaces omit at least three real automated advances, all measured: `finalize_orchestrator` (`oc_runipd.py:836-859`) writes the TERMINAL `executed` state with no agent turn and no human, which is the item's own candidate condition "whether an automated actor may write a terminal state at all" already happening; the `--full-auto` clear fires at TWO sites PER DRIVER, not one (queue-build `oc_runipd.py:2934`/`agy_runipd.py:1972` and post-review `:6926`/`:3982`), the second also rewriting the queue item's `action` to `execute`, so the plan's "exactly ONE advance" claim in OQ-01 understates it; and `process_backlog_close` advances a backlog item to `done`. E-01/V-01 rewritten to require exhaustiveness plus the search that establishes it. (2) BLOCKER PR-002: THREE OF THE ITEM'S FIVE QUESTIONS HAD NO OQ BLOCK, so E-03 would have answered them on the plan's own authority - the very hardcoding this plan exists to end, merely relocated from code into a spec. Raised as OQ-03 (policy key shape), OQ-04 (indistinguishability) and OQ-05 (retirement/reversal), each with a recommendation. OQ-04 is `Blocking: yes` because it is unrepairable: once advances are recorded indistinguishably from human ones, no later edit re-attributes them, and E-05 was asserting that prohibition itself. THREE MORE: the GATE claimed "OQ-01 is BLOCKING for the spec's CONTENT" while OQ-01 reads `Blocking: no`/`resolved` with the ruling recorded, so it would have stalled an executor on a settled question (PR-004); the shared-predicate precedent the spec is told to follow is only HALF adopted, since `is_plan_review_approved` is shared but `set_plan_approved` is DUPLICATED per driver with the agy copy conceding it is "kept byte-for-byte equivalent" by convention, so E-04 must now say whether single-authority covers the transition call too (PR-005); and the suite baseline was wrong in count and named failure (actual `1 failed, 5919 passed, 3 skipped, 2 xfailed`, an ENVIRONMENTAL `test_reporting_contract.py` case, not the `test_orchestrator_retirement` failure named, which now passes 112) (PR-007). I VERIFIED THE TWO EXISTING RESOLUTIONS rather than trusting them, since a plan asserting its own maintainer decisions is the forgery shape this repo guards: commit `0f0eb2b4` is maintainer-authored and states both decisions independently of the plan body, so OQ-01 and OQ-02 stand. CONFIRMED SOUND, and the plan's spec-first judgement is right: F-1 (`97df1z` executed, so the first consumer is live), F-2 (nothing covers the item), F-3/F-4 (`auto-approved` in `READY_TO_EXECUTE` and the schema refusing `Approval` on it), F-5, F-6 (`TRANSITION_AUTHORITY` at `:416`), F-7, F-9, F-10 (the cited spec really is `implemented`), the `Scope-Paths: .aw/records/specs` grammar (a bounded directory entry is legal), and the code's own admission that `rxya25` is the owed policy (`oc_runipd.py:755-757`). Added F-11..F-17 and four Step 0 conventions; corrected three stale line numbers inherited from the item (`evaluate_blocking_close` `:1980`, `driver_begin` `:903`, the `Approval` enforcement `:399-405`). Readiness `no-go` on account of OQ-04 alone; the recommendation is YES-ALWAYS-NO-OVERRIDE and E-05 is already written that way, so an affirming answer unblocks with no further edits.
- 2026-09-08 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `rxya25`. GATE NOTE: this item carries NO `- Blocks-Release:`, so this plan inherits none, despite `Priority: high`. THIS PLAN DELIBERATELY PRODUCES A SPEC RATHER THAN CODE, and the reason is the item's own shape: it is a MAINTAINER REQUIREMENT with five unanswered design questions, one of which ("what is the default?") the item itself notes would "immediately break `--full-auto` unless it ships with a permissive default". A plan that implemented a policy engine would have to answer all five by fiat, which is exactly the hardcoding the item exists to end. `aw specs new` exists and mints a conforming spec, so spec-first is a supported route. NOTHING IN THIS ITEM IS OBSOLETE and no spec or pending plan covers it: grepping the specs tree and the pending plans for a lifecycle-automation policy returns nothing. THE FIRST CONSUMER HAS LANDED, WHICH SHARPENS THE ITEM RATHER THAN CLOSING IT: `97df1z` (fullauto-01) is now EXECUTED, so the `--full-auto` path that decides "may I advance this reviewed plan to ready-to-execute without a human?" is SHIPPED and is answering that question by hardcoding today. So the item's premise ("`97df1z` is the FIRST CONSUMER of a policy that does not exist") is now a live condition rather than an anticipated one. ALL THE REUSABLE MATERIAL THE ITEM CITES VERIFIES AT HEAD `a2e0438a`: the honest-attestation precedent is real and enforced (`auto-approved` is a sibling ready-to-execute tier at `ipd_schema.py:267` with `READY_TO_EXECUTE = frozenset(("approved", "auto-approved"))`, documented at `:265-266` as "an automated clear, NOT human approval", and `:398-402` enforces that only `approved` carries the human `Approval` field); the shared-predicate pattern is real (`check_engine.evaluate_blocking_close` at `:1951`); and the config home exists (`.aw/config/project.json` plus a resolved user config path). ONE ADDITIONAL PRECEDENT WORTH REUSING that the item does not name: spec `20260815-0151-01-honest-human-approval-attestation.spec.md` (`- Status: implemented`) is the closest prior art in both subject and shape, having reframed a human-only gate into an honest non-TTY attestation, and its `TRANSITION_AUTHORITY` table in `attention_contract.py` is a per-transition authority model that already exists and that a policy should extend rather than duplicate.
- 2026-09-08 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Replace six hardcoded answers with one written policy. The deliverable is a spec that enumerates every gated transition, states the condition set per transition, answers the five open questions, and defines the single predicate every verb will consult, so the first implementation has a contract to build against rather than a sixth opinion to add.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: inventory what is actually hardcoded today

- [x] E-01 Inventory the ACTUAL per-transition decisions each verb makes today, by reading the code, and record them as a table in the spec. The item names five surfaces to cover: `driver_begin` (`oc_runipd.py:903`, NOT `:894` as the item says), `aw ipd finalize`, the backlog close gate (`check_engine.evaluate_blocking_close`, `:1980`, not `:1951`), the spec status setter, and the `--full-auto` promotion path now shipped by executed plan `97df1z`. For EACH, record which transition it gates, what condition it checks, what it does on failure (refuse, warn, proceed), and whether an automated actor may perform it. THIS INVENTORY IS THE SPEC'S FOUNDATION and must be measured rather than assumed: the item's whole claim is that these answers differ per verb, and a spec that generalizes from two of five surfaces would encode the same inconsistency it exists to remove.
  THE ITEM'S FIVE SURFACES ARE NOT THE WHOLE SET, AND UNDER A PERMISSIVE DEFAULT AN OMITTED TRANSITION IS A PERMITTED ONE. This is the single most important consequence of OQ-01's answer, so the inventory MUST be exhaustive rather than confined to the item's list. Measured at review time, at least these automated advances exist and are NOT in the item's five:
    * `finalize_orchestrator` (`oc_runipd.py:836-859`) administratively transitions an orchestrator to `executed` via `aw ipd set executed` with actor `aw oc run (orchestrator rollup)` and NO agent turn and NO human. That is an automated write of a TERMINAL state, which is exactly the item's own candidate condition "whether an automated actor may write a terminal state at all", already happening today.
    * The `--full-auto` clear fires at TWO distinct sites per driver, not one: the QUEUE-BUILD path (`oc_runipd.py:2934`, `agy_runipd.py:1972`) and the POST-REVIEW path (`oc_runipd.py:6926`, `agy_runipd.py:3982`). The second additionally rewrites the queue item's `action` to `execute` and its `status` to `queued`, so it is not merely a status set.
    * Automated backlog closing (`process_backlog_close` -> `evaluate_backlog_close`, `oc_runipd.py:1426`, `:1122`, called at `:6863`) advances a backlog item to `done` after a run.
  FIND THE REST BY SEARCHING FOR THE ACTORS, NOT BY TRUSTING THIS LIST. Grep for the calls that write a lifecycle status from a driver (`aw set`, `aw ipd set`, `aw backlog set`, `aw specs set` invocations and their in-process equivalents) and for the automated actor strings (`FULL_AUTO_ACTOR`, `aw oc run (orchestrator rollup)`); an advance that no row covers is one the policy will silently permit.
  - Depends on: none
  - Expected outcome: a per-verb, per-transition table of today's real behavior, each row citing the file and symbol it was read from, covering the item's five surfaces AND the additional automated advances above AND any further ones the search finds; the table states explicitly that it is intended to be exhaustive and says how exhaustiveness was checked.
  - Execution state: performed

- [x] E-02 Enumerate the CONDITION VOCABULARY, taking the item's candidate list as the starting point and checking each against the code rather than adopting it wholesale. The candidates are: unresolved BLOCKING versus non-blocking open questions (the pre-execution gate already distinguishes these); an unfixed review finding at or above `review_findings_gate.block_at` (enforced today by `check.review-finding-unescalated`); a stale `aw ipd begin` receipt; out-of-scope changed paths needing `--scope-reason`; a `Blocks-Release` gate on the artifact; and whether an automated actor may write a terminal state at all. For each, state where it is enforced today and whether it is genuinely a POLICY question (a maintainer might reasonably set it either way) or an INVARIANT (never negotiable). Getting that split right is what stops the policy becoming a switch that can disable a correctness gate.
  - Depends on: E-01
  - Expected outcome: each condition classified as policy or invariant, with its current enforcement point cited; invariants explicitly excluded from the policy surface.
  - Execution state: performed

### Task group 2: answer the five open questions with the maintainer

- [x] E-03 Answer the item's five open questions IN THE SPEC, each with its reasoning, because every one changes the shape of the eventual engine. TWO ARE ALREADY DECIDED BY THE MAINTAINER AND MUST BE TRANSCRIBED, NOT REOPENED: question 3 (the default) is OQ-01, resolved to a PERMISSIVE default with fail-closed available per transition; question 2 (override direction) is OQ-02, resolved to BOTH DIRECTIONS with only the loosening ones recorded. Carry each answer's recorded reasoning into the spec verbatim in substance, including OQ-01's requirement that the inverted posture be stated as DELIBERATE and OQ-02's requirement that a POLICY-closed transition be distinguished from a CONTRACT-closed one.
  THE OTHER THREE ARE NOT THE PLAN'S TO DECIDE ALONE, and the plan previously implied they were. (1) per-TRANSITION versus per-ARTIFACT-TYPE versus both; (4) whether an automated advance must always remain DISTINGUISHABLE; (5) whether the policy governs retirement and reversal as well as forward transitions. Each is now carried as its own open question (OQ-03, OQ-04, OQ-05) with a recommendation, because the plan's own gate correctly says these answers are PROPOSALS until the maintainer attests them, and because two of the three have consequences no reviewer may settle: question 4 decides whether the audit trail can ever stop distinguishing machine from human, and question 5 decides whether automation may retire an artifact. WRITE THE SPEC'S ANSWERS FROM THOSE OQ BLOCKS, so the spec never carries an answer whose provenance is this item's prose.
  - Depends on: E-02
  - Expected outcome: all five answered in the spec with reasoning; questions 2 and 3 transcribed from OQ-01/OQ-02 with their recorded constraints intact; questions 1, 4 and 5 taken from OQ-03/OQ-04/OQ-05's resolutions; question 3's answer explicitly reconciled against the shipped `--full-auto` behavior as measured by E-01.
  - Execution state: performed

- [x] E-04 Define ONE policy predicate consulted by every verb, following the pattern the repository has already proved rather than inventing one. `check_engine.evaluate_blocking_close` (`:1980`, not `:1951`) backs the backlog setter, the `aw check` rules AND the opt-in pre-commit hook, so those three provably cannot diverge; the spec must require the same for the lifecycle policy. Specify its inputs (artifact type, current status, target status, the artifact's own condition state, the resolved policy, any override) and its output (permit, refuse with a reason, or permit-with-attestation). ALSO SPECIFY THE IMPORT DISCIPLINE, because the predicate will be consumed by both host drivers: it must stay stdlib-cheap and driver-agnostic, the same constraint `plan_readiness` carries, and the anti-divergence guard in `tests/test_runner_item_dependencies.py` polices that class of coupling.
  THE PRECEDENT IS ONLY HALF-ADOPTED TODAY, AND THE SPEC SHOULD SAY WHICH HALF, because "follow the shared-predicate pattern" is otherwise ambiguous about a live inconsistency. MEASURED: the DECISION half is genuinely shared (`plan_readiness.is_plan_review_approved` has one definition and `agy_runipd.py:104-111` carries an explicit comment that its near-copy was removed because "a fix to one driver left `aw agy run --full-auto` broken"), but the ACTION half is NOT: `set_plan_approved` is defined TWICE, once per driver (`oc_runipd.py:735`, `agy_runipd.py:834`), with the agy copy's own docstring conceding it is "kept byte-for-byte equivalent to the oc twin" by convention rather than by construction. So the spec must state whether the single-authority requirement covers only the PERMIT decision or also the TRANSITION-PERFORMING call; if only the former, two copies of the actor string and message remain free to drift, which is the same class of defect the shared predicate was introduced to end.
  - Depends on: E-03
  - Expected outcome: one predicate specified with typed inputs and outputs, a single-authority requirement that states explicitly whether it covers the decision only or the transition call too, and the import discipline stated.
  - Execution state: performed

- [x] E-05 EXTEND the shipped attestation vocabulary rather than forking it, which the item requires explicitly ("A policy engine should EXTEND this vocabulary, not fork it"). The precedent is real and enforced: `auto-approved` is a sibling ready-to-execute tier (`ipd_schema.py:267`), documented as "an automated clear, NOT human approval" (`:265-266`), and the schema enforces that only `approved` carries the human `Approval` field (`:399-405`, not `:398-402`); `.aw/records/plans/README.md` records D65's rule that it is "set only by an automated checker, never by an executor fast-tracking its own work". ALSO EXTEND, do not duplicate, the per-transition authority model that already exists: `attention_contract.TRANSITION_AUTHORITY` (`:416`), introduced by the implemented spec `20260815-0151-01-honest-human-approval-attestation.spec.md`, is already a table of who may perform which transition. Specify how a policy-permitted automated advance is recorded so it stays DISTINGUISHABLE afterwards (question 4).
  THE INDISTINGUISHABILITY PROHIBITION IS OQ-04's ANSWER, NOT THIS ITEM'S TO ASSERT. The plan previously had this item "state that the policy may never be used to make an automated actor's advance indistinguishable from a human's" on its own authority. That is a permanent, unrepairable property (records written indistinguishably cannot be re-attributed later), so it is escalated as OQ-04 (`Blocking: yes`, owner maintainer) and this item WRITES the maintainer's answer rather than deciding it. The recommendation is YES-ALWAYS-NO-OVERRIDE, evidenced by `auto-approved` being a separate status, the schema refusing `Approval` on it, and both drivers recording an automated actor string; so if that is the answer, this item proceeds exactly as drafted.
  - Depends on: E-04
  - ALSO GATED ON OQ-04 BEING ANSWERED, which is not expressible in `Depends on` (that field takes only `E-*` ids), so it is stated here: do not write the indistinguishability sentence until the maintainer has ruled. The `Blocking: yes` on OQ-04 already refuses the whole plan at every lint checkpoint, so this cannot be reached prematurely.
  - Expected outcome: the spec extends `auto-approved` and `TRANSITION_AUTHORITY` explicitly, names the recording mechanism for a policy-permitted advance, and carries OQ-04's attested answer on indistinguishability rather than the plan's own assertion.
  - Execution state: performed

- [x] E-06 Write the spec through `aw specs new` and take it to `to-review`, NOT to `approved`. Use the tool rather than hand-naming: `aw specs new --title ... --slug ... --apply` mints an id6 and writes the conforming `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` with an `- Id:`. Carry `- From-Backlog: rxya25` so the provenance is machine-readable. Set the status with `aw specs set`, never by hand-editing the field, and do NOT set `approved`: that requires the maintainer's attested sign-off (`--by-human`), and this plan's five answered questions are proposals until they have it. Also state in the spec that it authorizes NO code change by itself, so a later executor cannot read it as licence to start building.
  - Depends on: E-05
  - Expected outcome: a conforming spec at `- Status: to-review` carrying `- From-Backlog: rxya25`, created and transitioned by tool, authorizing no implementation.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The item is a MAINTAINER REQUIREMENT with five open questions, filed separately from `97df1z` precisely because it "spans every lifecycle verb and is far larger than the plan that surfaced it". That is the shape of a spec, not of a code change.
- THE HONEST-ATTESTATION PRECEDENT IS REAL AND ENFORCED: `auto-approved` sits in `READY_TO_EXECUTE` alongside `approved` (`ipd_schema.py:267`) and is documented as an automated clear rather than human approval (`:265-266`), with the schema enforcing that only `approved` carries `Approval` (`:398-402`).
- THE SHARED-PREDICATE PATTERN IS PROVED: `evaluate_blocking_close` (`check_engine.py:1980`) backs three surfaces at once so they cannot diverge. That is the model E-04 requires. But it is only HALF-adopted for `--full-auto`: the decision (`plan_readiness.is_plan_review_approved`) is shared while the action (`set_plan_approved`) is duplicated per driver (F-15), so "follow the pattern" must say which half it covers.
- RE-LOCATE BY SYMBOL: three line numbers this plan inherited are stale (`evaluate_blocking_close` `:1980` not `:1951`; `driver_begin` `oc_runipd.py:903` not `:894`; the `Approval` enforcement `ipd_schema.py:399-405`). See F-16.
- AUTOMATION ALREADY WRITES A TERMINAL STATE WITHOUT A HUMAN: `finalize_orchestrator` (`oc_runipd.py:836-859`) sets an orchestrator `executed` with actor `aw oc run (orchestrator rollup)` and no agent turn. That makes the item's candidate condition "whether an automated actor may write a terminal state at all" a description of TODAY, not a hypothetical, and it is why OQ-05 recommends bringing retirement and terminal writes inside the policy.
- UNDER OQ-01's PERMISSIVE DEFAULT, AN OMITTED TRANSITION IS A PERMITTED ONE. This inverts the usual cost of an incomplete inventory: normally a missing row means a gate is not applied, here it means no gate exists. E-01's exhaustiveness is therefore a safety property, not a documentation nicety.
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
| F-10 | The closest prior art in both subject and shape is an IMPLEMENTED spec that reframed a human-only gate into an honest attestation, so the design has a precedent to follow rather than inventing an attestation model. | `.aw/records/specs/20260815-0151-01-honest-human-approval-attestation.spec.md` (`- Status: implemented`) |
| F-11 | THE ITEM'S FIVE SURFACES ARE NOT THE WHOLE SET, WHICH UNDER OQ-01's PERMISSIVE DEFAULT MEANS THE OMISSIONS WOULD BE SILENTLY PERMITTED. Measured, three automated advances sit outside the item's list: `finalize_orchestrator` writes the TERMINAL `executed` state with no agent turn and no human; the `--full-auto` clear fires at TWO sites per driver (queue-build and post-review), the second also rewriting the queue item's `action` to `execute`; and `process_backlog_close` advances a backlog item to `done` after a run. Addressed by E-01. | `oc_runipd.py:836-859`; `oc_runipd.py:2934` and `:6926`, `agy_runipd.py:1972` and `:3982`; `process_backlog_close` at `oc_runipd.py:1426`, called `:6863` |
| F-12 | THREE OF THE ITEM'S FIVE QUESTIONS HAD NO OQ BLOCK, so E-03 would have answered them on the plan's own authority - the exact hardcoding this plan exists to end, merely relocated from code into a spec. Questions 1, 4 and 5 are now OQ-03/OQ-04/OQ-05, and OQ-04 is BLOCKING because an indistinguishability decision cannot be walked back once records are written. | the plan's own E-03 versus its two OQ blocks |
| F-13 | THE GATE CONTRADICTED THE RESOLVED QUESTIONS: it said "OQ-01 is BLOCKING for the spec's CONTENT" and that E-03 could not proceed without the maintainer's ruling, while OQ-01 reads `Blocking: no`/`resolved` with that ruling recorded. Stale text that would stall an executor on a settled question. | the plan's OQ-01 block versus its gate paragraph |
| F-14 | BOTH OQ RESOLUTIONS ARE GENUINELY MAINTAINER-AUTHORED, verified rather than trusted because a plan asserting its own maintainer decisions is the forgery shape this repository guards: commit `0f0eb2b4` is authored by the maintainer and its message states both decisions independently of the plan text. | `git show 0f0eb2b4` |
| F-15 | THE SHARED-PREDICATE PRECEDENT IS ONLY HALF-ADOPTED, which the spec must not paper over: the DECISION is shared (`plan_readiness.is_plan_review_approved`, with `agy_runipd.py:104-111` recording that its near-copy caused a real one-driver breakage), but the ACTION is DUPLICATED (`set_plan_approved` defined per driver, the agy copy conceding it is "kept byte-for-byte equivalent" by convention). Addressed by E-04. | `oc_runipd.py:735`; `agy_runipd.py:834`, `:104-111` |
| F-16 | THREE CITED LINE NUMBERS ARE STALE, two of them inherited from the item: `evaluate_blocking_close` is `check_engine.py:1980` (cited `:1951`), `driver_begin` is `oc_runipd.py:903` (cited `:894`), and the `Approval`-field enforcement is `ipd_schema.py:399-405` (cited `:396-402`/`:398-402`). Re-locate by symbol. | read at HEAD `d45bf884` |
| F-17 | THE STATED SUITE BASELINE IS WRONG IN COUNT AND NAMED FAILURE, and it is a validation criterion: actual `1 failed, 5919 passed, 3 skipped, 2 xfailed` with an ENVIRONMENTAL `test_reporting_contract.py` gitignored-dump failure, not the `test_orchestrator_retirement` failure named (that file now reports `112 passed`). | measured at HEAD `d45bf884` |

## Proposed changes (ordered, validatable)

1. Inventory every verb's real per-transition decision EXHAUSTIVELY, with citations, including the terminal and backlog advances the item omits (E-01).
2. Classify each candidate condition as policy or invariant (E-02).
3. Answer the five open questions in the spec FROM their OQ blocks, reconciling the permissive default against shipped `--full-auto` (E-03).
4. Specify ONE predicate with typed inputs, outputs, import discipline, and whether single-authority covers the transition call too (E-04).
5. Extend `auto-approved` and `TRANSITION_AUTHORITY`; forbid indistinguishability (E-05, pending OQ-04).
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

- `python3 -m pytest` bare, per the repository contract, to prove this records-only change breaks nothing. Paste the ACTUAL summary line. THE AUTHORING-TIME BASELINE WAS WRONG IN BOTH COUNT AND NAMED FAILURE; re-measured at HEAD `d45bf884` it is `1 failed, 5919 passed, 3 skipped, 2 xfailed`, and the single failure is `tests/test_reporting_contract.py::ParityTests::test_only_expected_files_contain_the_full_contract_prose`, caused by a gitignored local dump and therefore ENVIRONMENTAL. `tests/test_orchestrator_retirement.py` (the failure the plan named) now reports `112 passed`, so do not expect a failure there. Judge on the DELTA by NODE ID, not count, and expect additional environmental failures inside a lane worktree from tests that read live repo state.
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
### OQ-03: Is the policy keyed per-TRANSITION, per-ARTIFACT-TYPE, or both?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED IN REVIEW because the plan listed this as one of the item's five questions and then had no OQ block for it, so E-03 would have answered it by fiat, which is the hardcoding this plan exists to end. NOT blocking, because it changes the policy's KEY SHAPE rather than whether any gate holds, and a wrong answer is fixable by editing an unapproved spec.
  RECOMMENDATION: BOTH, keyed on the (artifact-type, transition) PAIR. The item's own reasoning is that "a backlog item graduating is not the same risk as a plan finalizing", and the pair key is the only one that expresses that. Evidence that the repository already thinks in pairs: `attention_contract.TRANSITION_AUTHORITY` (`:416`) is keyed per transition, while `ipd_schema` and the backlog/spec setters carry separate per-TYPE vocabularies, so a single-axis policy would have to flatten one of the two axes that already exist.
  THE COST OF THE PAIR KEY IS COMBINATORIAL SURFACE, which matters more under OQ-01's permissive default: every unlisted pair is PERMITTED, so a sparse table is a broad allowance. Whatever the answer, the spec must say what an unlisted key means and must not leave it implicit.

### OQ-04: Must a policy-permitted automated advance ALWAYS remain distinguishable in the record?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED BY THE MAINTAINER 2026-09-10 (`/askme`): YES, ALWAYS. A machine's advance must remain distinguishable from a human's in EVERY transition, and no policy setting may relax it. E-05 may now write that requirement as the maintainer's ruling rather than on the plan's own authority.
  BUT THE PROSE MUST NOT BE WRITTEN AS AN ABSOLUTE, AND THAT INSTRUCTION IS BROADER THAN THIS PLAN. The maintainer chose the strongest option AND rejected how it was framed: "I would like you to stop speaking in absolutes. We enforce these things until such a time as we receive evidence that the rules need relaxing or changing. It is exceedingly rare that any declared 'absolute' rule remains that way for very long. We try to make a rule inflexible sometimes, and change if needed, but recording the inflexibility in prose seems counterproductive to me since you often get stuck on a prior declaration of inflexibility and it requires me to police more than I would like to have to police."
  SO E-05 WRITES A CURRENTLY-ENFORCED REQUIREMENT, NOT A PERMANENT LAW. Concretely: state that the distinguishability requirement holds for every transition and that no policy setting relaxes it, WITHOUT the words "never", "no override possible", "permanent", or "in perpetuity", and WITHOUT a clause forbidding a future maintainer from revisiting it. The enforcement strength is unchanged (a loosening request is still refused today, and the refusal is documented, which is what OQ-04 was asked for); what changes is that the text does not claim the rule can never change, because such a claim is what later gets cited back at the maintainer and forces them to police their own documentation. Note this is deliberately NOT the offered "allow a documented exception" option, which was declined: there is no exception mechanism, only an acknowledgement that evidence could change the rule.
  THE MECHANICAL BASIS WAS RE-VERIFIED AT HEAD `f50c1c74` BEFORE ASKING, so the ruling records existing behavior rather than new behavior: `READY_TO_EXECUTE` holds `approved` AND `auto-approved` as siblings with the comment "it records an automated clear, NOT human approval" (`ipd_schema.py:265-267`); the schema refuses the human `Approval` field unless status is exactly `approved` (`:398-408`); and each driver defines its own automated actor string (`FULL_AUTO_ACTOR = "aw oc run --full-auto"` at `oc_runipd.py:729`, `"aw agy run --full-auto"` at `agy_runipd.py:828`). Three independent mechanisms already implement the answer.
  SCOPE OF THE STYLE INSTRUCTION: it applies to prose this session and beyond, not only to E-05. Any artifact I author that states a rule should describe what is enforced now and why, and should not assert that the rule is unchangeable.
  ORIGINAL REVIEW REASONING RETAINED BELOW. RAISED IN REVIEW AND MARKED BLOCKING, because it is the one question whose wrong answer cannot be walked back: if the policy ever permits an automated advance to be recorded indistinguishably from a human's, then every audit of every earlier advance becomes unreliable, and no later edit repairs records already written. The plan asserts the answer in E-05 ("state that the policy may never be used to make an automated actor's advance indistinguishable from a human's") and the item calls it "the property that makes the audit trail trustworthy", but neither is a maintainer attestation, and E-05 currently writes that prohibition into a spec on the plan's own authority.
  RECOMMENDATION: YES, ALWAYS, WITH NO OVERRIDE. This is the strongest-evidenced answer in the plan and the repository already enforces it mechanically rather than by convention: `auto-approved` is a SEPARATE status from `approved` in `READY_TO_EXECUTE` (`ipd_schema.py:267`), the schema REFUSES the human `Approval` field on anything but `approved` (`:399-405`), and both drivers record an automated actor string rather than `--by-human` (`FULL_AUTO_ACTOR` at `oc_runipd.py:729`, `agy_runipd.py:828`, with the message "auto-approved by --full-auto: review readiness cleared (not human approval)"). The executed plan `97df1z` reached this same conclusion at its own OQ-02, where the maintainer ruled the machine must not assert `--by-human`.
  WHY IT IS STILL ASKED RATHER THAN TREATED AS SETTLED: `97df1z`'s ruling covered ONE transition on ONE path. Making it a universal, non-overridable property of every transition under the new policy is a broader commitment, and under OQ-02's both-directions answer someone will eventually ask whether a loosening override may relax it. The spec needs a maintainer-attested "never" so that request has a documented refusal.

### OQ-05: Does the policy govern retirement and reversal, or only forward transitions?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED IN REVIEW for the same reason as OQ-03 (listed as one of the five, carried by no OQ block). NOT blocking, because the plan's deferred section already permits the answer to be "yes, in scope, specified later or in its own spec", so a decision to include them does not require this plan to specify them.
  RECOMMENDATION: YES, IN SCOPE, and the evidence for it is stronger than the plan realized: automation ALREADY writes a terminal state without a human. Measured at review time, `finalize_orchestrator` (`oc_runipd.py:836-859`) transitions an orchestrator to `executed` through `aw ipd set executed` with no agent turn and no human sign-off. So the question is not hypothetical: under OQ-01's permissive default, leaving retirement and terminal writes OUTSIDE the policy means they are governed by nothing, which is strictly worse than today, where at least the transition gate refuses on its own terms.
  DISTINGUISH THE TWO HALVES WHEN ANSWERING, because they differ in risk: RETIREMENT (`superseded`/`not-executed`) and terminal `executed` writes are advances that end an artifact's life and are the ones already happening automatically; REVERSAL (`approved -> to-review`) moves an artifact BACKWARD and is generally safe, since it removes rather than grants permission. A single yes/no may be the wrong shape.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the inventory table from the written spec, with at least the five named surfaces present, and for EACH row paste the file and symbol it was read from. A row without a citation does not satisfy this item, because the whole claim being tested is that these behaviors differ per verb and were measured rather than assumed.
    EXHAUSTIVENESS IS PART OF THIS ITEM, not a bonus, because under OQ-01's permissive default an unlisted transition is a PERMITTED one (F-11). The table MUST additionally contain rows for the three automated advances measured in review: `finalize_orchestrator`'s TERMINAL `executed` write, BOTH `--full-auto` clear sites per driver (queue-build and post-review, the latter also setting `action: execute`), and `process_backlog_close`'s advance to `done`. Paste the search used to establish exhaustiveness (the grep over lifecycle-setting calls and automated actor strings) and state what it returned; a table containing only the item's five surfaces FAILS this item.
  - Observed evidence: |

    THE INVENTORY AS WRITTEN IN THE SPEC (`.aw/records/specs/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md`, Sections 3.1 through 3.7, quoted in full below). EVERY ROW CARRIES THE FILE AND SYMBOL IT WAS READ FROM, at HEAD `2c316ef0`. NINE surfaces are covered where the item named five: the item's `driver_begin` (3.2), `aw ipd finalize` (3.3), the backlog close gate (3.5), the spec status setter (3.7) and the `--full-auto` path (3.1), PLUS the three review-measured additions (BOTH `--full-auto` sites in 3.1, automated backlog closing in 3.4, orchestrator rollup terminal retirement in 3.6) and the spec setter's TWO forked surfaces counted once in 3.7.

    SPEC SECTION 3.1: The `--full-auto` clear, at TWO sites per host

    | Fact | Value |
    |---|---|
    | Transition | `ipd:reviewed->auto-approved` |
    | Read from | `runner_shared.initialize_run` (`runner_shared.py:13196-13202`) - the QUEUE-BUILD site; `runner_shared.execute_item` (`runner_shared.py:15235-15271`) - the POST-REVIEW site |
    | Performed by | `oc_runipd.set_plan_approved` (`oc_runipd.py:875`) / `agy_runipd.set_plan_approved` (`agy_runipd.py:972`), each shelling out to `aw set auto-approved <id6> --actor <FULL_AUTO_ACTOR>` |
    | Condition checked | `plan_readiness.is_plan_review_approved(plan_path)`, plus `options.full_auto` |
    | On failure | Queue-build site: `except Exception: pass`, leaving the status `reviewed` (the item then needs input). Post-review site: prints `! Failed to auto-approve IPD <id6>` and proceeds |
    | Automated actor may perform it | YES, and this is the ONLY transition `--full-auto` performs |

    TWO SITES, NOT ONE, and the second does more than set a status: it also rewrites the queue item's
    `action` to `execute` and its `status` to `queued` (`runner_shared.py:15243-15247`), which is what
    converts a review turn into an execution turn within one run. A policy that governed only the status
    write would leave that re-dispatch ungoverned.

    WHAT IT DELIBERATELY DOES NOT DO, which is the honest-attestation precedent this spec extends: it does
    NOT claim human `approved`. The target status is the sibling `auto-approved` tier, the actor is an
    automated string, and the message reads "auto-approved by --full-auto: review readiness cleared (not
    human approval)" (`oc_runipd.py:870-873`). `set_plan_approved`'s own docstring names backlog `rxya25`
    and says its behavior is "hardcoded-but-honest until that lands" (`oc_runipd.py:892-896`). This spec
    is that landing.

    SPEC SECTION 3.2: `aw ipd begin`: the pre-execution authority gate

    | Fact | Value |
    |---|---|
    | Transition | Not a status change. It writes the EXECUTION-AUTHORITY receipt that `finalize` later consumes, so it gates `ipd:*->executed` one step removed |
    | Read from | `ipd_lifecycle.begin` (`ipd_lifecycle.py:1220`); driver entry `runner_shared.driver_begin` (`runner_shared.py:11817`), wrapped per host at `oc_runipd.py:1036` and `agy_runipd.py:1053` |
    | Conditions checked, in order | (1) non-empty `--actor`; (2) plan exists and carries a valid `- Id:` id6; (3) `pre-execution` lint disposition is `conforming`; (4) base HEAD is versioned and unambiguous; (5) requirements + `Scope-Paths` freeze; (6) baseline clean WITHIN the frozen `Scope-Paths` |
    | On failure | REFUSE, writing no receipt ("fail-closed: no receipt = no execution authority"). The driver marks the item `blocked` (`runner_shared.py:14227-14232`) |
    | Automated actor may perform it | YES. The driver calls it with `driver_actor(state)` (`runner_shared.py:14221`), e.g. `aw oc run model=<model>` |

    NOTE the `isolated` parameter selects WHICH baseline condition (6) measures, and does not skip it
    (`ipd_lifecycle.py:1244-1257`). A worker-role process is refused outright at the CLI wrapper
    (`ipd_lifecycle.run_begin`), which Section 4.2 classifies as an invariant.

    SPEC SECTION 3.3: `aw ipd finalize`: the terminal transition

    | Fact | Value |
    |---|---|
    | Transition | `ipd:<pre-terminal>->executed` |
    | Read from | `ipd_lifecycle.finalize` (`ipd_lifecycle.py:3358`) and `ipd_lifecycle.finalize_precheck` (`:1885`); driver entry `oc_runipd.driver_finalize` (`oc_runipd.py:1346`), `agy_runipd.driver_finalize` (`agy_runipd.py:1081`) |
    | Conditions checked | a matching begin receipt EXISTS; the receipt is CURRENT against the plan digest, with exactly one accepted mismatch class (an ADDITIVE `Scope-Paths` widening whose every other frozen category is byte-identical, `:1919-1963`); a usable `base_head`; `pre-transition` lint conforming (every `E-*` performed, every `V-*` evidenced); two-way scope reconciliation (out-of-scope changed paths need `--scope-reason`, declared-but-unmodified paths need `--scope-ack`, `:3437-3460`) |
    | On failure | REFUSE, leaving the plan unmoved. The driver records the item NOT executed and preserves its lane (`runner_shared.py:15211-15230`) |
    | Automated actor may perform it | YES. The driver computes the reconciliation programmatically and passes the same gated surface (`oc_runipd.py:1355-1378`) |

    SPEC SECTION 3.4: Automated backlog closing

    | Fact | Value |
    |---|---|
    | Transition | `backlog:<open\|blocked\|graduated>->done` |
    | Read from | `oc_runipd.process_backlog_close` (`oc_runipd.py:1861`), called from `runner_shared.execute_item` (`:15208`) and `runner_shared.py:4360-4367`; decided by `oc_runipd.evaluate_backlog_close` (`oc_runipd.py:1471`); the RELEASE-GATE half by `check_engine.evaluate_blocking_close` (`check_engine.py:2539`) |
    | Conditions checked | the item resolves and is not already `done`; at least one artifact carries `From-Backlog: <id6>`; if any carrier is an IPD, EVERY IPD carrier is terminal `executed`; the run EARNED it (the deciding carrier is one this run produced, not one it found finished); and then the release-gate predicate's HANDOFF / SATISFIED / DE-GATED test |
    | On failure | Records `backlog-item-left-open` WITH THE REASON and proceeds. Every lookup is wrapped to fail closed: "a missing item, an unreadable tree, or a raising helper yields `close=False` plus a recorded reason" (`oc_runipd.py:1484-1487`) |
    | Automated actor may perform it | YES, via the GATED `aw backlog set <id6> --status done` spelling, chosen deliberately over the positional one, which "cannot even accept `--evidence`" (`oc_runipd.py:1718-1725`) |

    SPEC SECTION 3.5: The backlog release-gate close predicate

    | Fact | Value |
    |---|---|
    | Transition | `backlog:*->done` (gated), `backlog:*->parked` (warned), `backlog:*->graduated` (explicitly legitimate), priority demotion of a blocker (warned) |
    | Read from | `check_engine.evaluate_blocking_close` (`check_engine.py:2539`) |
    | Condition checked | for `->done` on an item carrying `- Blocks-Release:`, one of HANDOFF (a `From-Backlog` plan or spec carrying the SAME `Blocks-Release`), SATISFIED (a resolvable `--evidence` citation), or DE-GATED (the post-mutation item carries no gate) |
    | On failure | `->done`: REFUSE, severity `error`, naming the three fixes. `->parked` and a priority demotion: WARN and allow |
    | Automated actor may perform it | YES, and this is the SHARED-PREDICATE PRECEDENT this spec's Section 7 requires the policy to copy: one predicate backs the setter, the `aw check` rules and the opt-in pre-commit hook, so they provably cannot diverge |

    SPEC SECTION 3.6: Orchestrator rollup retirement: an automated TERMINAL write with no agent turn

    | Fact | Value |
    |---|---|
    | Transition | `ipd:<pre-terminal>->executed` on an Order-0 orchestrator |
    | Read from | LIVE PATH: `runner_shared.dispatch_orchestrator_item` (`:9800`) -> `ipd_lifecycle.retire_orchestrator` (`ipd_lifecycle.py:3107`), decided by `runner_shared.evaluate_set_retirement` (`:8037`). Called from `oc_runipd.py:6758` and `agy_runipd.py:3520` |
    | Conditions checked | `Kind: orchestrator` (a `Kind: child` plan is refused outright); the Set has an orchestrator on disk; the Set has >= 1 child; EVERY child's on-disk `Status:` is exactly `executed`; the child table parsed and declares no row resolving to nothing; then the 12 gates in `ipd_lifecycle.ROLLUP_SHARED_GATES` (`:2938`) |
    | Deliberately OMITTED | the `pre-transition` `E-*`/`V-*` checkpoint, per `ROLLUP_OMITTED_GATES` (`:2989`) and spec `77tr3o` R-5, on the premise that an orchestrator's own items are performed by nobody |
    | On failure | REFUSE. The dispatcher rewrites the outcome to TERMINATE with reason `finalize-refused` rather than RECONSIDER, because a structural refusal retried each iteration would spin (`runner_shared.py:9875-9886`) |
    | Automated actor may perform it | YES, with NO agent turn and NO human, using `driver_actor(state)` |

    THIS IS THE ITEM'S OWN CANDIDATE CONDITION HAPPENING TODAY. The item asks "whether an automated actor
    may write a terminal state at all"; this transition is an automated actor writing a terminal state,
    already, in production. It is the strongest single piece of evidence for Section 5.5's answer that
    retirement and terminal writes are IN SCOPE for the policy.

    NOTE A STALE SIBLING. `oc_runipd.finalize_orchestrator` (`oc_runipd.py:976`) is an `aw ipd set
    executed` route with the actor `aw oc run step=orchestrator-rollup`. Its own docstring records that it
    has ZERO callers (AST-verified) and is retained only because
    `tests/test_lane_tool_identity.py:585-609` asserts it as a documented `oc`-only asymmetry. The policy
    must govern it if it is ever wired up, so it is listed; it is not a live advance today. The plan that
    produced this spec cited it as live (`oc_runipd.py:836-859`) and that citation is now stale in both
    line number and liveness.

    SPEC SECTION 3.7: The spec status setter, on TWO forked surfaces

    | Fact | Value |
    |---|---|
    | Transition | Every pair in `attention_contract.SPEC_TRANSITIONS` (`:437`), i.e. `spec:draft->to-review`, `->reviewed`, `->approved`, `->implementing`, `->implemented`, plus `deferred`/`parked`/`superseded` |
    | Read from | TWO surfaces, reached by different CLI spellings: `specs.run_set` (`specs.py:498`) for `aw specs set <path> --status <enum>`, and `status_set.validate_transition_allowed` (`status_set.py:493`) for the positional `aw specs set <status> <selector>` |
    | Conditions checked | transition legality against `SPEC_TRANSITIONS`; the `TRANSITION_AUTHORITY` requirement kinds for the target - `by_human` (`->approved`), `evidence` resolvable (`->implemented`), `review_record` (`->reviewed`); and for `->approved` the shared `plan_readiness.approval_refusals` predicate |
    | On failure | REFUSE, exit 1, file unchanged |
    | Automated actor may perform it | PARTIALLY, and this is the sharpest per-transition split in the inventory. `->to-review`, `->implementing`, `->deferred`, `->parked` and `->superseded` are open to an automated actor. `->approved` REFUSES without `--by-human`. `->implemented` REFUSES without a resolvable evidence citation. `->reviewed` REFUSES without a conforming review record |

    WHY BOTH SURFACES ARE LISTED RATHER THAN ONE. They are a FORK, not a wrapper: the code at each site
    says so explicitly, because "a gate installed in only one of them is bypassed by choosing the other
    spelling" (`specs.py:563-568`, `status_set.py:541-547`). The mitigation already in place is that both
    call the SAME shared predicates rather than carrying two copies of the logic. That is the pattern
    Section 7.3 requires the policy to follow, and this row is the reason the requirement has to cover the
    transition-performing call and not only the decision.

    NOTE THIS SETTER IS ALSO WHERE THE `draft` -> `to-review` PROMOTION WOULD HAPPEN if the runner's draft
    admission gate ever performed one; Section 4.4 records that it currently does not.

    THE EXHAUSTIVENESS SEARCHES, RUN AND PASTED (spec Section 3.9 records them; reproduced here with what they returned).

    SEARCH 1, every nested lifecycle-setting CLI invocation in both drivers and the shared runner:

        $ grep -rn 'pinned_module_argv(\|"aw",$' agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py agent_workflows/runner_shared.py
        agent_workflows/oc_runipd.py:901:    cmd = pinned_module_argv(
        agent_workflows/oc_runipd.py:933:                "aw",
        agent_workflows/oc_runipd.py:993:    cmd = pinned_module_argv(
        agent_workflows/oc_runipd.py:1363:    cmd = pinned_module_argv(
        agent_workflows/oc_runipd.py:1740:    cmd = pinned_module_argv(
        agent_workflows/agy_runipd.py:984:    cmd = pinned_module_argv(
        agent_workflows/agy_runipd.py:1013:                "aw",
        agent_workflows/agy_runipd.py:1096:    cmd = pinned_module_argv(
        (plus the two definitions of the helper itself at oc_runipd.py:669 and runner_shared.py:13434, excluded)

    EVERY ONE IS INVENTORIED: `oc_runipd.py:901`/`:933` and `agy_runipd.py:984`/`:1013` are `aw set auto-approved` (3.1); `oc_runipd.py:993` is the CALLERLESS `aw ipd set executed` sibling (3.6's stale-sibling note); `oc_runipd.py:1363` and `agy_runipd.py:1096` are `aw ipd finalize` (3.3); `oc_runipd.py:1740` is `aw backlog set --status done` (3.4); and `runner_shared.py:11854` is `aw ipd begin` (3.2), reached through the shared `driver_begin` rather than a per-host `pinned_module_argv` call.

    SEARCH 2, every automated actor string:

        $ grep -rn "FULL_AUTO_ACTOR = \|def driver_actor\|step=orchestrator-rollup\|orchestrator rollup" agent_workflows/*.py
        agent_workflows/agy_runipd.py:966:FULL_AUTO_ACTOR = "aw agy run --full-auto"
        agent_workflows/agy_runipd.py:1038:def driver_actor(state: dict[str, Any]) -> str:
        agent_workflows/ipd_lifecycle.py:3067:        f"RETIRED as the orchestrator rollup step of a runner Set completion, not executed by an "
        agent_workflows/ipd_lifecycle.py:3181:            f"{LIFECYCLE_ROLE_ERROR} (refused: orchestrator rollup retirement). The runner "
        agent_workflows/ipd_lifecycle.py:3190:    # The empty-actor wording stays LOCAL because it names this transition ("orchestrator rollup
        agent_workflows/ipd_lifecycle.py:3201:            "orchestrator rollup retirement requires a non-empty --actor.",
        agent_workflows/oc_runipd.py:869:FULL_AUTO_ACTOR = "aw oc run --full-auto"
        agent_workflows/oc_runipd.py:1002:            "aw oc run step=orchestrator-rollup",
        agent_workflows/oc_runipd.py:1018:def driver_actor(state: dict[str, Any]) -> str:
        agent_workflows/runner_shared.py:12280:def driver_actor(state: dict[str, Any], *, labels: HostLabels) -> str:
        agent_workflows/runner_shared.py:13503:FULL_AUTO_ACTOR = "aw-driver/full-auto"

    THIS SEARCH IS WHAT FOUND THE DEFECT REPORTED AS D-2: a THIRD `FULL_AUTO_ACTOR` at `runner_shared.py:13503` whose value AND message differ from both host copies and which nothing reads. Filed as backlog `zf999x`.

    SEARCH 3, every caller of the single status-write primitive:

        $ grep -rn "apply_status_change" agent_workflows/*.py
        (exactly ONE non-comment call outside status_set itself: agent_workflows/ipd_lifecycle.py:3778, inside the rollup retirement's coordinator worktree, i.e. 3.6. Every other reference is a docstring/comment. Everything else reaches the primitive through the CLI, which SEARCH 1 covers.)

    A TABLE CONTAINING ONLY THE ITEM'S FIVE SURFACES WOULD HAVE FAILED THIS ITEM, and it does not: Sections 3.1 (second site), 3.4 and 3.6 are the three review-measured additions, all present with citations. The spec states the exhaustiveness intent and its THREE LIMITS explicitly in Section 3.9 (it covers this package only; it is a snapshot at one HEAD; it names status writes rather than every decision leading to one), and acceptance criterion 4 requires a test that fails when a new automated advance appears without a row, which is what converts the snapshot into a maintained invariant.

    ONE CORRECTION TO THE PLAN'S OWN CITATIONS, made by re-locating by symbol as F-16 directs: `finalize_orchestrator` is `oc_runipd.py:976`, not `:836-859`, AND IT IS NOT LIVE. Its own docstring records ZERO callers (AST-verified) and says it is retained only because `tests/test_lane_tool_identity.py:585-609` asserts it as a documented oc-only asymmetry. The live automated terminal write is `runner_shared.dispatch_orchestrator_item` -> `ipd_lifecycle.retire_orchestrator` (`ipd_lifecycle.py:3107`). The plan's CLAIM (automation writes a terminal state with no agent turn and no human) is therefore CONFIRMED, on a different code path than the one it cited. Likewise the `--full-auto` sites are now `runner_shared.py:13196` and `:15235` (the shared runner did not exist when the plan was authored), `evaluate_blocking_close` is `check_engine.py:2539` (not `:1980`), `TRANSITION_AUTHORITY` is `attention_contract.py:486` (not `:416`), and `process_backlog_close` is `oc_runipd.py:1861` (not `:1426`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the condition table showing each of the item's six candidate conditions classified as POLICY or INVARIANT with its current enforcement point cited, and paste the spec sentence that excludes invariants from the policy surface.
  - Observed evidence: |

    THE CONDITION TABLE AS WRITTEN IN THE SPEC (Section 4.1). The item's SIX candidates are C-1 through C-6; C-7 through C-10 are additions found while reading the code.

    SPEC SECTION 4.1: The classification

    | # | Condition | Enforced today at | Class | Why |
    |---|---|---|---|---|
    | C-1 | Unresolved BLOCKING open question | `plan_readiness.has_unresolved_blocking_question` via `approval_refusals` (`plan_readiness.py:592-596`); `ipd_lint` checkpoint code `IPD-Q501` (`ipd_lint.py:76`) | POLICY | It is ALREADY overridable, by `--allow-open-questions`, and the override is already recorded in the artifact's actor string (`status_set.py:672-676`). A condition the shipped code lets a human wave is a policy condition by demonstration. This is also the maintainer's worked example, so it MUST be settable |
    | C-2 | Unresolved NON-BLOCKING open question | Not a refusal anywhere; the maintainer ruled 2026-09-10 that it is not a not-ready condition | POLICY | Currently permissive everywhere. A maintainer might reasonably want a stricter posture for a release branch, which is precisely the CI tightening case of Section 6.2 |
    | C-3 | An unfixed review finding at or above `review_findings_gate.block_at` | `check.review-finding-unescalated` (`check_engine.py:208`, `:3795`); `review_findings.subject_gating_blocks` via `approval_refusals` (`plan_readiness.py:517-527`); threshold from `config.findings_gate_threshold` (`config.py:1130`) | POLICY, with an invariant floor | The THRESHOLD is already configurable and already has a fail-closed default of `high` (`config.py:1103`), so the policy inherits a decided shape rather than inventing one. THE FLOOR: `approval_refusals` gives this refusal NO override at all today (`plan_readiness.py:527-532`), and the policy must not add one. So the threshold is policy; "a finding at or above the effective threshold refuses" is invariant |
    | C-4 | A stale `aw ipd begin` receipt | `ipd_lifecycle.finalize_precheck` (`:1919-1963`) | INVARIANT | A stale receipt means the frozen contract the execution was authorized against is not the contract now written down, so the scope delta finalize computes is meaningless. This is not a risk appetite question; it is a correctness precondition for the computation. Note the ONE accepted mismatch class (an additive `Scope-Paths` widening with every other frozen category byte-identical) is already specified and is not an override |
    | C-5 | Out-of-scope changed paths needing `--scope-reason` | `ipd_lifecycle.finalize` (`:3437-3460`), `_compute_scope_reconciliation` on the driver side (`oc_runipd.py:1355`) | INVARIANT that the DEMAND is made; POLICY whether an automated actor may ANSWER it | The demand for a reason is not negotiable: a silent out-of-scope edit is the thing the gate exists to surface. But TODAY the driver answers it programmatically and unattended, which is a real automation decision presently hardcoded. That half belongs on the policy surface |
    | C-6 | A `Blocks-Release` gate on the artifact | `check_engine.evaluate_blocking_close` (`:2539`), three surfaces | INVARIANT for `->done`; POLICY for the warned transitions | The `->done` branch fails closed and offers three explicit fixes, one of which (`--blocks-release -`) already de-gates deliberately. An override that let automation close a gated item WITHOUT one of the three fixes would make the release-blocker set unreliable, which is the one property the field exists to provide. The `->parked` and priority-demotion branches already only WARN, and whether they should refuse is a genuine policy question |
    | C-7 | Whether an automated actor may write a TERMINAL state at all | Nowhere as a single question; answered per site (3.3, 3.4, 3.6) | POLICY | This is the item's sharpest question and it is a policy one: automation writes terminal states today (3.6), a maintainer might reasonably forbid it, and both postures are coherent. Section 6.4 keeps the two transitions that must never be automated out of reach regardless |
    | C-8 | The worker/coordinator ROLE of the process | `ipd_lifecycle.worker_role_active` in `run_begin`/`run_finalize` and in `retire_orchestrator` (`ipd_lifecycle.py:3180-3186`) | INVARIANT | A worker-role process must not create lifecycle authority. This is a containment property (spec `7ckptx`), not a lifecycle-advance judgement, and a policy that could relax it would let a lane grant itself authority its container denies |
    | C-9 | The ACTOR being non-empty and parenthesis-free | `attention_contract.actor_refusal`, backstopped in `status_set.apply_status_change` (`:658-662`) | INVARIANT | An unattributed record is not a record. Nothing is gained by making this settable |
    | C-10 | Nested tool identity | `assert_child_tool_identity` (`oc_runipd.py:725`), run-fatal | INVARIANT | If the tooling performing a transition is not the tooling that gated it, every gate in this document is void. Explicitly run-fatal today rather than item-local, and that is correct |

    C-7 through C-10 are ADDITIONS to the item's six, found while reading the code. C-1 through C-6 are the
    item's own list, each checked against the code rather than adopted wholesale.

    SPEC SECTION 4.2: The exclusion sentence

    THE POLICY SURFACE CONSISTS OF THE CONDITIONS CLASSIFIED POLICY IN SECTION 4.1 AND NOTHING ELSE. An
    INVARIANT is not a policy key, has no default, accepts no override, and MUST NOT be expressible in the
    configuration file or on the command line; an implementation that admits one has widened the policy
    beyond this spec and is nonconforming.

    That is stated as a prohibition on the SURFACE rather than on the values, deliberately: a key whose
    only legal value is "enforced" is still a key, and the next person to touch it will wonder why it
    cannot be set to anything else and may add the missing value.

    THE SENTENCE EXCLUDING INVARIANTS FROM THE POLICY SURFACE (spec Section 4.2, quoted verbatim):

        THE POLICY SURFACE CONSISTS OF THE CONDITIONS CLASSIFIED POLICY IN SECTION 4.1 AND NOTHING ELSE. An
        INVARIANT is not a policy key, has no default, accepts no override, and MUST NOT be expressible in the
        configuration file or on the command line; an implementation that admits one has widened the policy
        beyond this spec and is nonconforming.

    Section 4.2 also states WHY the prohibition is on the SURFACE rather than on the values: "a key whose only legal value is 'enforced' is still a key, and the next person to touch it will wonder why it cannot be set to anything else and may add the missing value." Acceptance criterion 5 makes it testable.

    NOTE TWO CONDITIONS ARE DELIBERATELY SPLIT rather than forced into one class, because the honest answer is split: C-3 is POLICY in its THRESHOLD (already configurable at `config.py:1097-1104`, fail-closed default `high`) with an INVARIANT FLOOR that a finding at or above the effective threshold refuses (today `plan_readiness.approval_refusals` gives that refusal no override at all, `plan_readiness.py:528-531`), and C-5 is INVARIANT in that the `--scope-reason` DEMAND is made but POLICY in whether an automated actor may ANSWER it, which is what the driver does programmatically today (`oc_runipd.py:1355`).
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: quote the spec's answer to each of the five questions, individually and in order, AND name the OQ each answer came from (question 2 -> OQ-02, question 3 -> OQ-01, question 1 -> OQ-03, question 4 -> OQ-04, question 5 -> OQ-05). An answer with no OQ provenance FAILS this item, because answering on the plan's own authority is the hardcoding this plan exists to end (F-12). For question 3, paste the passage that reconciles the permissive default against the shipped `--full-auto` behavior, naming the transitions it currently performs as measured by E-01, and paste the sentence stating the inverted posture is DELIBERATE (OQ-01's explicit requirement). For question 2, paste the passage distinguishing a POLICY-closed transition from a CONTRACT-closed one, which OQ-02 requires and which the question as authored did not contain.
  - Observed evidence: |

    ALL FIVE ANSWERS, IN THE ITEM'S ORDER, EACH NAMING ITS OQ. Quoted from the spec's Section 5.

    SPEC SECTION 5.1: Question 1: is the policy keyed per-TRANSITION, per-ARTIFACT-TYPE, or both?

    FROM OQ-03 (status `open`, owner maintainer; the recommendation, not an attested ruling).

    ANSWER: BOTH, keyed on the `(artifact-type, transition)` PAIR, written `<type>:<old>-><new>`.

    REASONING, from OQ-03. The item's own argument is that "a backlog item graduating is not the same risk
    as a plan finalizing", and the pair key is the only key shape that expresses it. The repository already
    thinks in both axes: `attention_contract.TRANSITION_AUTHORITY` (`:486`) is keyed per TRANSITION while
    `ipd_schema`, `backlog` and the spec setter carry separate per-TYPE vocabularies, so a single-axis
    policy would have to flatten one of two axes that already exist.

    THE COST IS COMBINATORIAL SURFACE, and it bites harder because of 5.2's permissive default: every
    unlisted pair is PERMITTED, so a sparse table is a broad allowance.

    WHAT AN UNLISTED KEY MEANS, stated explicitly because OQ-03 requires it not be left implicit: an
    unlisted `(type, transition)` pair is PERMITTED to automation, subject to every invariant in Section
    4.1 and to the contract-closed set in Section 6.4. It is not an error, and it is not refused.

    SPEC SECTION 5.2: Question 3: what is the default?

    FROM OQ-01, RESOLVED BY THE MAINTAINER 2026-09-08 (recorded in commit `0f0eb2b4`, verified in review
    as maintainer-authored). Transcribed, not re-decided.

    ANSWER: A PERMISSIVE DEFAULT MATCHING TODAY'S BEHAVIOR, with fail-closed available PER TRANSITION.

    THE POSTURE IS ALLOW-UNLESS-FORBIDDEN, AND THAT IS A DELIBERATE INVERSION OF THIS REPOSITORY'S POSTURE
    EVERYWHERE ELSE, which is refuse-unless-allowed. The maintainer chose it over the reviewed
    recommendation of fail-closed-plus-a-grandfather-list. It is recorded as deliberate here so that a
    later reader does not read it as an oversight and "correct" it, breaking whatever automation has come
    to rely on it by then.

    WHY IT IS DEFENSIBLE, transcribed from OQ-01 so the choice is not recorded as arbitrary:

    1. NOTHING CAN BREAK on the day the policy lands, which was the entire hazard the grandfather list
       existed to avoid. A list that must be maintained accurately is itself a failure mode.
    2. THE SHIPPED AUTOMATION IS ALREADY CAREFUL IN THE WAY THAT MATTERS. `--full-auto` performs exactly
       one advance, `reviewed -> auto-approved`, and deliberately does not claim human `approved`. So the
       distinction the policy most needs to protect is already preserved by the one thing the default
       permits.
    3. A PERMISSIVE DEFAULT IS NOT AN UNBOUNDED ONE. Fail-closed remains available per transition, so the
       transitions that must never be automated can each be closed individually and explicitly, which is
       arguably clearer than a blanket refusal plus an exception list.

    THE COST DID NOT DISAPPEAR, IT MOVED, and a reviewer should weigh it: Section 6.5's fail-closed-from-
    the-start list is the inverse of the grandfather list and carries the same maintenance burden.

    RECONCILED AGAINST THE SHIPPED `--full-auto`, as OQ-01 and V-03 require. Measured in Section 3.1, the
    transitions `--full-auto` performs today are: `ipd:reviewed->auto-approved` (at both the queue-build
    and post-review sites), plus the queue re-dispatch to `action: execute` that accompanies the second.
    Under this default all three remain permitted on the day the policy lands, so `--full-auto` is
    unchanged by the policy's arrival. That is the whole purpose of the default, and it is the one
    behavioral claim in this spec that an implementation must test directly (Section 8, criterion 2).

    SPEC SECTION 5.3: Question 2: may an argument override TIGHTEN, or only LOOSEN?

    FROM OQ-02, RESOLVED BY THE MAINTAINER 2026-09-08 (same commit `0f0eb2b4`). Transcribed.

    ANSWER: BOTH DIRECTIONS ARE ALLOWED, AND ONLY THE LOOSENING ONES ARE RECORDED.

    WHY THE ASYMMETRY IS THE POINT. Because 5.2 resolved to a permissive default, TIGHTENING is the
    direction that ADDS safety and LOOSENING is the direction that REMOVES it. The recording rule follows
    the RISK rather than the mechanism: a tightening override needs no justification because being stricter
    is never the hazardous choice, while a loosening override is written into the artifact so a relaxation
    is auditable rather than silent.

    THE CI CASE IS WHY BOTH DIRECTIONS ARE NEEDED, and it is concrete: a job may want to refuse ANY
    automated advance while building a release, which is stricter than the repository policy. Without
    tightening, that job would have to reimplement the check, and a second copy of the rule is exactly the
    divergence Section 7's single-predicate requirement exists to prevent.

    HOW A LOOSENING OVERRIDE IS RECORDED: by the existing mechanism, not a new one. `--allow-open-questions`
    is folded into the recorded ACTOR string (`status_set.py:672-676`), so the override is visible in the
    artifact's own history and is machine-greppable. A loosening policy override MUST be recorded the same
    way. Note a run log would be the wrong home: `.aw/records/runs/` is gitignored and per-machine, so a
    record there is not a record.

    SPEC SECTION 5.4: Question 4: must a policy-permitted automated advance always remain DISTINGUISHABLE?

    FROM OQ-04, RESOLVED BY THE MAINTAINER 2026-09-10 via `/askme`. This is the maintainer's ruling, not
    this spec's assertion.

    ANSWER: YES. A machine's advance remains distinguishable from a human's in EVERY transition, and no
    policy setting relaxes it. A loosening override does not reach this requirement.

    THIS IS A CURRENTLY-ENFORCED REQUIREMENT AND NOT A CLAIM ABOUT THE FUTURE. The maintainer chose the
    strongest option AND rejected absolutist framing: rules here are enforced until evidence shows they
    need changing, and recording inflexibility in prose is counterproductive because a prior declaration of
    inflexibility gets cited back and has to be policed. So this section states what is enforced and why,
    and does not assert that the rule can never change. There is deliberately NO exception mechanism; that
    option was offered and declined.

    THREE MECHANISMS ALREADY IMPLEMENT IT, so the ruling records existing behavior:

    1. `auto-approved` is a SEPARATE status from `approved`, a sibling in `READY_TO_EXECUTE`, documented as
       "an automated clear, NOT human approval" (`ipd_schema.py:265-267`).
    2. The schema REFUSES the human `Approval:` field unless the status is exactly `approved`, and REQUIRES
       it when it is (`ipd_schema.py:400-411`).
    3. Each host records an automated ACTOR string rather than `--by-human`: `FULL_AUTO_ACTOR` at
       `oc_runipd.py:869` and `agy_runipd.py:966`, and `driver_actor` at `runner_shared.py:12280` for the
       begin/finalize/rollup paths.

    SPEC SECTION 5.5: Question 5: does the policy govern retirement and reversal?

    FROM OQ-05 (status `open`, owner maintainer; the recommendation, not an attested ruling).

    ANSWER: YES, IN SCOPE, with the two halves distinguished because they differ in risk.

    * RETIREMENT and TERMINAL WRITES (`superseded`, `not-executed`, `parked`, `deferred`, and `executed` /
      `implemented` / `done`) END an artifact's life. These are IN SCOPE and are the ones ALREADY HAPPENING
      automatically: Section 3.6 is an automated terminal write with no agent turn, and Section 3.4 is an
      automated `->done`. Leaving them outside the policy under a permissive default would mean they are
      governed by NOTHING, which is strictly worse than today, where each site at least refuses on its own
      terms.
    * REVERSAL (`approved -> to-review`, `reviewed -> draft`, and their spec equivalents in
      `attention_contract.SPEC_TRANSITIONS`) moves an artifact BACKWARD. It is IN SCOPE but is generally
      SAFE, because it REMOVES rather than grants permission. The default for a reversal pair should be
      permissive, and the reason is worth stating: an automation that can undo its own premature advance is
      safer than one that cannot.

    SPECIFYING RETIREMENT SEMANTICS IN FULL IS NOT DONE HERE. This section decides SCOPE. If the
    implementing Set finds the retirement half needs detail beyond the policy key, that detail may warrant
    its own spec section or its own spec.

    THE PROVENANCE IS EXPLICIT AND AUDITED IN THE SPEC ITSELF (Section 5.6), which is what stops an answer resting on the plan's own authority (F-12):

    SPEC SECTION 5.6: Attestation status of these five answers

    | Question | Source | Attested by the maintainer? |
    |---|---|---|
    | 3 (default) | OQ-01, commit `0f0eb2b4` | YES, 2026-09-08 |
    | 2 (override direction) | OQ-02, commit `0f0eb2b4` | YES, 2026-09-08 |
    | 4 (distinguishability) | OQ-04, `/askme` | YES, 2026-09-10 |
    | 1 (key shape) | OQ-03, `open` | NO. This is the plan's reviewed recommendation |
    | 5 (retirement/reversal scope) | OQ-05, `open` | NO. This is the plan's reviewed recommendation |

    THIS TABLE IS WHY THE SPEC IS AT `to-review` AND NOT AT `approved`. Two of the five answers are
    proposals. Approving this spec is the act that attests them, and it is the maintainer's
    (`--by-human`); nothing in this document may be read as that attestation having happened.

    QUESTION 3's RECONCILIATION AGAINST THE SHIPPED `--full-auto`, naming the transitions E-01 measured (quoted from Section 5.2):

        RECONCILED AGAINST THE SHIPPED `--full-auto`, as OQ-01 and V-03 require. Measured in Section 3.1, the
        transitions `--full-auto` performs today are: `ipd:reviewed->auto-approved` (at both the queue-build
        and post-review sites), plus the queue re-dispatch to `action: execute` that accompanies the second.
        Under this default all three remain permitted on the day the policy lands, so `--full-auto` is
        unchanged by the policy's arrival.

    THE SENTENCE STATING THE INVERTED POSTURE IS DELIBERATE (OQ-01's explicit requirement; quoted from Section 5.2):

        THE POSTURE IS ALLOW-UNLESS-FORBIDDEN, AND THAT IS A DELIBERATE INVERSION OF THIS REPOSITORY'S POSTURE
        EVERYWHERE ELSE, which is refuse-unless-allowed. The maintainer chose it over the reviewed
        recommendation of fail-closed-plus-a-grandfather-list. It is recorded as deliberate here so that a
        later reader does not read it as an oversight and "correct" it, breaking whatever automation has come
        to rely on it by then.

    QUESTION 2's POLICY-CLOSED versus CONTRACT-CLOSED DISTINCTION, which OQ-02 requires and the question as authored did not contain (spec Section 6.3, with the closed enumeration in 6.4):

    SPEC SECTION 6.3: POLICY-closed versus CONTRACT-closed

    This distinction is OQ-02's explicit requirement and did not exist in the question as authored. Under a
    permissive default the per-transition closures are the only real protection, so if a loosening flag
    could open them they would be decorative.

    * A POLICY-CLOSED transition is closed by a maintainer's choice. A loosening override MAY open it, and
      the override is recorded.
    * A CONTRACT-CLOSED transition is closed because opening it would make a record assert something
      false. NO policy setting and NO override opens it. An implementation MUST refuse the attempt rather
      than warn.

    SPEC SECTION 6.4: The contract-closed set

    This is a CLOSED enumeration. Adding to it is an amendment to this spec.

    | Transition | Why no override may open it |
    |---|---|
    | `ipd:reviewed->approved` (human `approved`) | `approved` REQUIRES the human `Approval:` field (`ipd_schema.py:400-405`) and `->approved` carries `by_human: True` in `TRANSITION_AUTHORITY`. An automated actor writing it asserts a human approved something no human approved. The honest automated route already exists and is `auto-approved` |
    | `spec:reviewed->approved` | The anti-self-approval FLOOR. `aw specs set` refuses without `--by-human` on BOTH surfaces (`specs.py:525-540`, `status_set.py:523-540`), and the floor's own text says a plain set without it "stops and refuses" |
    | `spec:implementing->implemented` | An agent may not set `implemented`; it requires a resolvable evidence citation (`specs.py:543-549`), and the repository instructions state the prohibition directly |

    NOTE WHAT IS NOT IN THIS SET, because the omissions are deliberate and each is a judgement a reviewer
    may dispute. `ipd:*->executed` is NOT contract-closed: automation performs it today through the gated
    `finalize` (3.3) and through the rollup retirement (3.6), and both are attributed honestly. Neither is
    `backlog:*->done` (3.4). Those are POLICY questions (C-7), so a maintainer may close them and a
    recorded override may reopen them.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the predicate's specified signature (inputs and the three-way output) and the spec sentence requiring every surface to call it and none to reimplement it. Paste the stated import discipline (stdlib-cheap, driver-agnostic) and the reason it exists. Paste the sentence that states explicitly whether the single-authority requirement covers the PERMIT DECISION only or also the TRANSITION-PERFORMING call, since the precedent is currently half-adopted (`is_plan_review_approved` shared, `set_plan_approved` duplicated per driver) and an ambiguous requirement would leave that drift licensed (F-15).
  - Observed evidence: |

    THE PREDICATE'S SPECIFIED SIGNATURE AND THREE-WAY OUTPUT (spec Section 7.1):

    SPEC SECTION 7.1: Signature

    One predicate, consulted by every surface that performs a lifecycle transition.

    INPUTS:

    * `artifact_type` - the canonical type token (`ipd`, `spec`, `backlog`, ...), from
      `status_set.detect_artifact_type` / `run_selection_policy.SPEC_TYPE_BY_RESOLVER_TYPE`, never a new
      vocabulary.
    * `current_status` and `target_status` - the transition, together forming the 5.1 pair key.
    * `condition_state` - the artifact's own answers to the Section 4.1 POLICY conditions, supplied by the
      caller rather than read here, so the predicate stays pure and cheap (7.4).
    * `resolved_policy` - the policy as read from configuration, resolved to a value for this pair.
    * `override` - the loosening or tightening argument, or none.
    * `actor` - the automated actor string that would be recorded, because a PERMIT-WITH-ATTESTATION
      verdict has to name what the attestation will say.

    OUTPUT: exactly one of three verdicts.

    * PERMIT - the transition may proceed with its ordinary attribution.
    * REFUSE, WITH A REASON - and the reason must be specific enough to act on. A refusal that does not
      name its cause is the failure mode this whole area exists to remove, which is why
      `plan_readiness._blocking_question_ids` exists to quote the actual `OQ-NN` ids
      (`plan_readiness.py:602-618`). It must also say WHICH kind of closure refused: POLICY-closed (an
      override could open it, and which one) or CONTRACT-closed (nothing can).
    * PERMIT-WITH-ATTESTATION - permitted, and the record MUST carry the automated provenance: the
      `auto-approved`-style sibling status where one exists, the automated actor string, and the loosening
      override folded into the actor when one was used. This verdict is how Section 5.4's
      distinguishability requirement is delivered mechanically rather than by the caller remembering.

    THE SINGLE-AUTHORITY REQUIREMENT, AND ITS EXPLICIT ANSWER TO THE HALF-ADOPTION QUESTION (spec Section 7.3). THE ANSWER IS: IT COVERS BOTH THE DECISION AND THE TRANSITION-PERFORMING CALL, stated in those words so F-15's measured drift is not left licensed:

    SPEC SECTION 7.3: Single authority: it covers the DECISION *and* the TRANSITION CALL

    The precedent is `check_engine.evaluate_blocking_close` (`check_engine.py:2539`), which backs the
    backlog setter, the `aw check` rules AND the opt-in pre-commit hook, so those three provably cannot
    diverge.

    THE REQUIREMENT COVERS BOTH HALVES, AND THIS IS THE ANSWER TO AN AMBIGUITY THAT WOULD OTHERWISE LICENSE
    A MEASURED DRIFT. "Follow the shared-predicate pattern" is ambiguous about whether it means the PERMIT
    DECISION only or also the TRANSITION-PERFORMING call, and Section 3.8's D-1 shows the repository is
    currently half-adopted: the decision is shared, the action is duplicated per host, and D-2 shows that
    duplication has ALREADY produced a third divergent constant nobody reads.

    So: ONE definition of the permit decision, AND ONE definition of the call that performs a
    policy-governed transition, including the actor string and message it records. A second copy of the
    performer is a second copy of the attestation, and the attestation is what Section 5.4 requires to stay
    honest.

    SPEC SECTION 7.4: Import discipline

    The predicate must be STDLIB-CHEAP and DRIVER-AGNOSTIC: it must not import a runner. Both host drivers
    will consume it, and `runner_shared`'s own module contract already states that shared code may not
    import a runner and must take host-varying data as a PARAMETER (the `HostLabels` descriptor, and
    `driver_begin`'s injected `env_builder`/`argv_builder`, are the shipped shape). `plan_readiness`
    carries the same constraint, and the anti-divergence guard in `tests/test_runner_item_dependencies.py`
    polices that class of coupling.

    The practical consequence: `condition_state` is a PARAMETER (7.1) rather than something the predicate
    reads, so the predicate is a deterministic function of its inputs and every branch is testable without
    a TTY, a host, or a live run. `run_selection_policy` is the model here; its module docstring states
    exactly this property.

    THE IMPORT DISCIPLINE AND THE REASON IT EXISTS (spec Section 7.4):

    SPEC SECTION 7.4: Import discipline

    The predicate must be STDLIB-CHEAP and DRIVER-AGNOSTIC: it must not import a runner. Both host drivers
    will consume it, and `runner_shared`'s own module contract already states that shared code may not
    import a runner and must take host-varying data as a PARAMETER (the `HostLabels` descriptor, and
    `driver_begin`'s injected `env_builder`/`argv_builder`, are the shipped shape). `plan_readiness`
    carries the same constraint, and the anti-divergence guard in `tests/test_runner_item_dependencies.py`
    polices that class of coupling.

    The practical consequence: `condition_state` is a PARAMETER (7.1) rather than something the predicate
    reads, so the predicate is a deterministic function of its inputs and every branch is testable without
    a TTY, a host, or a live run. `run_selection_policy` is the model here; its module docstring states
    exactly this property.
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the spec passages that EXTEND `auto-approved` and `TRANSITION_AUTHORITY` by name, the recording mechanism for a policy-permitted automated advance, and the sentence governing whether an automated advance may ever be indistinguishable from a human's. That sentence must cite OQ-04's ANSWER as its authority; a sentence asserting the prohibition with no OQ-04 resolution behind it FAILS this item, because it would be the plan deciding an unrepairable property on its own authority (F-12). Paste the `ipd_schema.py` lines cited so the extension is anchored to real code, using the re-measured `:399-405` rather than the plan's original `:398-402` (F-16).
  - Observed evidence: |

    THE PASSAGES EXTENDING `auto-approved` AND `TRANSITION_AUTHORITY` BY NAME, AND THE RECORDING MECHANISM (spec Section 8):

    SPEC SECTION 8.1: `ipd_schema.READY_TO_EXECUTE` and the `auto-approved` tier

    `auto-approved` is a SHIPPED sibling ready-to-execute tier (`ipd_schema.py:267`:
    `READY_TO_EXECUTE: FrozenSet[str] = frozenset(("approved", "auto-approved"))`), documented at
    `:265-266` as recording "an automated clear, NOT human approval", with `APPROVAL_STATUSES` at `:264`
    holding `approved` alone so the human `Approval:` field cannot attach to the automated tier
    (`:400-411`). `.aw/records/plans/README.md` records D65's rule that it is set only by an automated
    checker, never by an executor fast-tracking its own work.

    THE POLICY MUST NOT REDEFINE THIS. It is the MODEL for how a policy-permitted advance is recorded: a
    distinct status token where the pipeline has one, so the distinction survives in the artifact rather
    than only in a log. Where a pipeline stage has NO automated sibling token, the automated actor string
    carries the distinction (Section 8.3).

    SPEC SECTION 8.2: `attention_contract.TRANSITION_AUTHORITY`

    `TRANSITION_AUTHORITY` (`attention_contract.py:486`) is ALREADY a per-transition table of who may
    perform which transition, introduced by the implemented spec
    `20260815-0151-01-honest-human-approval-attestation.spec.md`. It carries `who`, `by_human`,
    `human_token`, `evidence`, `review_record` and `requires_gate` per entry, and it is consumed by BOTH
    spec-setting surfaces (`specs.py:524`, `status_set.py:523`).

    THE POLICY EXTENDS THIS TABLE RATHER THAN ADDING A PARALLEL ONE. Two observations make that the right
    move rather than a preference:

    1. It is keyed on `->{status}` today, i.e. per TRANSITION with the type implied (specs). Section 5.1's
       pair key is a generalization of exactly this key, so the policy is the same table widened by one
       axis, not a new concept.
    2. It already distinguishes REQUIREMENT KINDS (`by_human`, `evidence`, `review_record`), which is the
       same shape a policy needs for "what must be true for this actor to perform this transition".

    A PARALLEL TABLE WOULD BE THE DIVERGENCE THIS SPEC EXISTS TO END. Two tables answering "who may perform
    this transition" is D-1 and D-2 again, one layer up.

    SPEC SECTION 8.3: How a policy-permitted automated advance is recorded

    Three mechanisms, all shipped, composed rather than replaced:

    1. THE TARGET STATUS, where an automated sibling exists (`auto-approved`). Preferred, because it is
       visible to every reader of the artifact's front matter without parsing history.
    2. THE ACTOR STRING in the workflow-history record, always. `FULL_AUTO_ACTOR` for a `--full-auto`
       clear; `driver_actor(state)` (e.g. `aw oc run model=<model>`) for begin, finalize and the rollup
       retirement. The actor is validated non-empty and parenthesis-free by
       `attention_contract.actor_refusal`, backstopped in `status_set.apply_status_change` (`:658-662`).
    3. THE LOOSENING OVERRIDE, folded into that same actor string, following `--allow-open-questions`
       (`status_set.py:672-676`).

    WHAT MUST NOT HAPPEN, as Section 5.4's ruling requires: no policy setting and no override may cause an
    automated advance to be recorded in a way indistinguishable from a human's. Concretely, an automated
    actor must not pass `--by-human`, must not write the `Approval:` field, and must not record a bare
    human-looking actor string.

    THE SENTENCE GOVERNING DISTINGUISHABILITY, AND ITS AUTHORITY. The spec's Section 5.4 heading names OQ-04 as its source in its FIRST LINE, so the requirement is the maintainer's ruling and not the plan's assertion:

        FROM OQ-04, RESOLVED BY THE MAINTAINER 2026-09-10 via `/askme`. This is the maintainer's ruling, not
        this spec's assertion.

        ANSWER: YES. A machine's advance remains distinguishable from a human's in EVERY transition, and no
        policy setting relaxes it. A loosening override does not reach this requirement.

    AND THE PROHIBITION AS WRITTEN IN E-05's OWN SECTION (spec Section 8.3, closing paragraph):

        WHAT MUST NOT HAPPEN, as Section 5.4's ruling requires: no policy setting and no override may cause an
        automated advance to be recorded in a way indistinguishable from a human's. Concretely, an automated
        actor must not pass `--by-human`, must not write the `Approval:` field, and must not record a bare
        human-looking actor string.

    OQ-04's STYLE INSTRUCTION WAS HONORED, which is part of its resolution and not separate from it. The maintainer accepted the strongest option AND rejected absolutist framing. Verified mechanically over the spec text: ZERO occurrences of "in perpetuity"; "never"/"no override"/"permanent" appear ONLY in senses the ruling permits (describing what the CODE refuses today, e.g. "no policy setting and no override may cause...", and naming the CONTRACT-CLOSED set), and NOWHERE as a claim that the rule itself cannot change. Section 5.4 says so in its own words: "THIS IS A CURRENTLY-ENFORCED REQUIREMENT AND NOT A CLAIM ABOUT THE FUTURE ... this section states what is enforced and why, and does not assert that the rule can never change. There is deliberately NO exception mechanism; that option was offered and declined."

    THE `ipd_schema.py` LINES CITED, PASTED FROM THE FILE so the extension is anchored to real code. F-16's re-measurement is CONFIRMED and then REFINED: the `Approval`-field enforcement is `:400-411`, not the plan's original `:398-402` nor F-16's `:399-405`.

        $ sed -n '263,268p' agent_workflows/ipd_schema.py
        # Statuses that require (and only they may carry) an Approval field.
        APPROVAL_STATUSES: FrozenSet[str] = frozenset(("approved",))
        # `auto-approved` is a sibling ready-to-execute tier (D65); it records an automated clear, NOT human
        # approval, so it does NOT require the human `Approval` field.
        READY_TO_EXECUTE: FrozenSet[str] = frozenset(("approved", "auto-approved"))

        $ sed -n '400,411p' agent_workflows/ipd_schema.py
            # Approval iff Status is approved (auto-approved does NOT carry human Approval).
            has_approval = META_APPROVAL in fields
            if status == "approved" and not has_approval:
                errors.append(
                    MetaError(META_APPROVAL, "Approval is required when Status is approved")
                )
            if status != "approved" and has_approval:
                errors.append(
                    MetaError(
                        META_APPROVAL, "Approval must be absent unless Status is approved"
                    )
                )

        $ sed -n '486,488p' agent_workflows/attention_contract.py
        TRANSITION_AUTHORITY: Dict[str, Dict[str, object]] = {
            "->reviewed": {
                "who": "reviewer",
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `aw specs new ... --apply` invocation and its output showing the minted id6 and conforming filename; paste the spec's front matter showing `- Status: to-review` and `- From-Backlog: rxya25`; paste the `aw specs set` command used (proving the status was tool-set, not hand-edited); paste `aw check` showing no new diagnostic and no `check.from-backlog-dangling`; and paste the bare `python3 -m pytest` summary line compared to the stated baseline.
  - Observed evidence: |

    THE `aw specs new ... --apply` INVOCATION AND ITS OUTPUT, showing the minted id6 and the conforming filename (the spec was NOT hand-named):

        $ aw specs new --title "Lifecycle automation policy: one configurable per-(type, transition) permission surface" \
            --slug lifecycle-automation-policy \
            --summary "One configurable, argument-overridable policy deciding how far automation may advance an artifact along the lifecycle, consulted by a single shared predicate. Specification only; authorizes no code change." \
            --apply
        aw specs new: wrote <lane-worktree>/.aw/records/specs/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md

    (the tool prints an ABSOLUTE path; the machine-local prefix is elided here as `<lane-worktree>` so this record carries no local path, per the leak-sanitizer rule.)

    The minted id6 is `llbr2b` and the filename is `YYYYMMDD-<id6>-01-<id6>-<slug>.spec.md` as the grammar requires.

    THE `aw specs set` COMMAND USED, PROVING THE STATUS WAS TOOL-SET RATHER THAN HAND-EDITED (and that it went to `to-review`, NOT `approved`):

        $ aw specs set to-review .aw/records/specs/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md --message "<the record quoted in the spec's own Workflow history>" --no-commit
        -    spec        20260920-llbr2b-01-llbr2b  [high]  draft to-review

    THE SPEC'S FRONT MATTER, showing `- Status: to-review` and `- From-Backlog: rxya25`:

        # Spec: Lifecycle automation policy: one configurable per-(type, transition) permission surface

        - Date: 2026-09-20
        - Status: to-review
        - Id: llbr2b
        - Author: opencode its_direct/pt3-claude-opus-5-1m-us
        - From-Backlog: rxya25
        - Priority: high
        - Work-Kind: feature
        - Scope: One configurable, argument-overridable policy deciding how far automation may advance an artifact along the lifecycle, consulted by a single shared predicate. Specification only; authorizes no code change.

    `aw specs check` REPORTS THE SPEC CONFORMING:

        $ aw specs check .aw/records/specs/20260920-llbr2b-01-llbr2b-lifecycle-automation-policy.spec.md
        aw specs check: all specs conform.

    `aw check` GAINS NO DIAGNOSTIC, measured as a BEFORE/AFTER DIFF rather than asserted. The spec file was moved aside inside the workspace, `aw check --agent` captured, the file restored, and the two diagnostic multisets compared by (rule, location):

        BEFORE (spec absent): 396  AFTER (spec present): 396
        NEW diagnostics introduced by the spec: NONE
        diagnostics removed: NONE

    NO `check.from-backlog-dangling` FOR THIS SPEC. The repository carries exactly ONE instance of that rule and it names a DIFFERENT, pre-existing artifact, present in both the before and after runs:

        check.from-backlog-dangling | .aw/records/plans/executed/20260830-hostcap-01-mjx7ne-extend-the-shipped-sandbox-capability-contract-with-the-runn.ipd.md

    So the spec's `- From-Backlog: rxya25` RESOLVES (the item is at `.aw/records/backlog/graduated/20260831-rxya25-01-rxya25-lifecycle-automation-policy.backlog.md`).

    THE BARE SUITE, ACTUAL SUMMARY LINE (`python3 -m pytest`, no added flags, per the repository contract):

        1 failed, 7229 passed, 3 skipped, 2 xfailed, 3 warnings in 179.92s (0:02:59)
        FAILED tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped

    JUDGED BY NODE ID AGAINST THE STATED BASELINE, as the plan's validation section directs (the plan's `1 failed, 5919 passed` at HEAD `d45bf884` is stale in count, and its named failure `tests/test_reporting_contract.py` no longer fails; the count moved because 1310 tests were added between that HEAD and `2c316ef0`). THE ONE FAILURE IS ENVIRONMENTAL, NOT A REGRESSION, AND THAT WAS PROVEN RATHER THAN ASSERTED: the test asserts a non-isolated turn carries no `OPENCODE_CONFIG_CONTENT`, and THIS TURN'S OWN AMBIENT ENVIRONMENT sets that variable, so the assertion reads the harness's env rather than the code's.

        $ echo "set: ${{OPENCODE_CONFIG_CONTENT+YES}} len=${{#OPENCODE_CONFIG_CONTENT}}"
        set: YES len=66

        $ env -u OPENCODE_CONFIG_CONTENT python3 -m pytest tests/test_turn_bounds.py -o addopts="" -q
        43 passed in 14.86s

    With the ambient variable removed the whole file passes, so the failure is caused by the lane's environment and not by this change. THIS PLAN CHANGES NO CODE: the only files it adds are one spec and one backlog item, so no test outcome could be attributable to it in any case.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review`. It must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`; no `- Readiness:` field is written here, because that field is `/plan-review`'s attested output and hand-writing it would forge a review that never happened.

OQ-01 AND OQ-02 ARE ANSWERED, so nothing waits on them: the maintainer resolved both on 2026-09-08 (recorded in commit `0f0eb2b4`, verified in review as maintainer-authored, its message stating both decisions independently of the plan body). The gate previously said "OQ-01 is BLOCKING for the spec's CONTENT" and that "E-03 cannot answer question 3 without the maintainer's ruling"; that ruling exists, so the sentence was stale and would have stalled an executor on a settled question. Do not re-ask OQ-01 or OQ-02.

WHAT DOES BLOCK: OQ-04 (`Blocking: yes`), raised in review, asking whether a policy-permitted automated advance must ALWAYS remain distinguishable from a human's. `aw ipd lint` refuses this plan with `IPD-Q501` while it stands, which is the intended fail-closed stop, because E-05 currently writes that prohibition into a spec on the plan's own authority and the answer is unrepairable once records are written the other way. The recommendation is YES-ALWAYS-NO-OVERRIDE and E-05 is already written that way, so an affirming answer unblocks with no further edits. OQ-03 and OQ-05 are also newly raised but are non-blocking.

A reviewer should also note the deliberate shape: this plan produces a SPEC and changes no code, because the item carries five design questions and implementing before they are answered would add a sixth hardcoded opinion to the five it exists to consolidate.

Execution contract for whoever runs it: commit ONLY the paths listed in `Scope-Paths`, path-scoped (`git commit -m msg -- <paths>`), never `git add -A`, never push. Create the spec with `aw specs new` and transition it with `aw specs set`; never hand-name a spec and never hand-edit its `- Status:`. Do NOT set the spec `approved` (that is the maintainer's attested act) and never set it `implemented` (an agent may not). Run the bare suite (`python3 -m pytest`) and paste the ACTUAL summary line even though no code changes, so the records-only claim is evidenced. Every `V-*` above demands pasted evidence, and a `V-*` may not be marked complete from the matching `E-*` checkmark. When all validations carry real observed evidence and `aw ipd lint --phase pre-transition` conforms, move the plan to `.aw/records/plans/executed/` through `aw ipd finalize`, never with a raw `git mv` plus a hand-edited `- Status:`.
