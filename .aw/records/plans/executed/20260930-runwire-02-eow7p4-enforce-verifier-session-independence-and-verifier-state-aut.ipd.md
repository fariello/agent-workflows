# IPD: Enforce verifier session independence and verifier state authority through verify_roles at the one shared verify site

- Date: 2026-09-30
- Kind: child
- Concern: The runner asks for an independent verifier, spends a paid model turn getting one, and then throws away the ONE fact that would prove the independence. At the single shared verify site in `runner_shared.execute_item_core` the verifier launch returns a session id into `_v_session` and that name appears EXACTLY ONCE in the whole 37355-line module (measured at lane HEAD `cedab274` by grepping `_v_session`: one match, the destructuring assignment itself). Nothing compares it to the execute turn's session id, which the same function DOES persist (`attempt["session_id"]`). So a verifier that silently reused the execution session would be recorded as an independent verification, and no artifact would contradict it.
  THE REFUSAL FOR THIS ALREADY SHIPS, TWICE, AND IS UNUSED BY THE RUNNERS. `agy_verifier.assert_distinct_sessions` raises `SessionIdentityCollisionError` when the two ids are equal, and `agy_verifier.run_fresh_verifier` calls `verify_roles.enforce_role_action(session.role, "author_verifier_decision")` plus refuses a non-verifier role with `SelfVerificationForbiddenError`. `verify_roles.ROLE_CONTRACTS['verifier'].state_authority` grants exactly three edges, read in-process: `performed -> verifying`, `verifying -> verified`, `verifying -> correction_required`. NEITHER DRIVER IMPORTS `verify_roles` (zero grep matches in both driver modules), and `runner_shared` mentions it only in one comment, never in code.
  AND THE CAPABILITY LAYER ALREADY PROBES FOR THIS EXACT GUARANTEE WHILE NOTHING CONSUMES THE RESULT, which is the sharpest evidence that the gap is a wiring gap rather than a missing concept. `host_sandbox_profile` defines `CAP_FRESH_VERIFIER_SESSION = "supports_fresh_verifier_session"` and its module docstring says it is "PROBED by attempt. The probe runs the real fresh-verifier contract twice and requires BOTH that distinct identities finalize AND that a reused identity is REFUSED, because a contract that never refuses enforces no separation while a caller believes verification was independent." MEASURED: `ACTION_CAPABILITY_REQUIREMENTS` contains exactly ONE row, `ACTION_READ_ONLY`, whose `required` is empty. So no action requires that capability, the probe's verdict gates nothing, and the docstring's own warning ("a caller believes verification was independent") describes the runner's present state.
  WHY THIS IS WORTH A PLAN THOUGH NO COLLISION IS KNOWN TO HAVE OCCURRED, stated honestly because it decides the shape. The oc verifier launch passes `fresh_session=True` and its argv builder omits `--session` for a fresh turn, so a collision is UNLIKELY by construction today. That makes this a GUARD against a class the repository has already been bitten by in the adjacent direction (`lanesess` `xd9sll`: carrying a session across trees caused silent no-op turns and four consecutive lanes were lost), not a live incident. The value is that the guarantee becomes CHECKED rather than assumed, at a cost of one comparison, on a path where the alternative failure is silent and expensive. It is filed `chore` for exactly this reason.
- Scope: Consume `verify_roles` (and the shipped session-collision refusal) at the ONE shared verify site, so two guarantees the repository already defines become enforced: (1) the verifier turn's session identity DIFFERS from the execute turn's, and (2) the actor recording a verifier verdict holds the `state_authority` for the `verifying -> verified` / `verifying -> correction_required` edge it is exercising, checked against `run_state`'s table through sibling Order 01's translation.
  THE REFUSAL SEMANTICS ARE NARROW AND STATED EXACTLY, because this plan DOES refuse where Order 01 does not. A session COLLISION makes the verification NOT VERIFIED (it is not an independent verification, so it cannot be recorded as one); it must NOT be recorded `verified`. It must ALSO NOT be recorded as a verifier REJECTION, because the verifier did not reject anything - the runner failed to obtain an independent one. Reuse the existing `verify_disp` vocabulary and the existing `Refusal` record rather than minting a new status token.
  EXCLUDES: changing the verifier PROMPT or its verdict schema; changing `map_verdict` or the verdict table (`1bfppy`'s, and it is correct); adding a `verify_disp` token (measured to render as a bare `-` in `run_viewer`); the `correction_required -> runnable` requeue; wiring `run_recovery` or a ledger; and adding an `ACTION_CAPABILITY_REQUIREMENTS` row (see OQ-02 - that is a capability-policy change with its own refusal surface).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runwire_verifier_authority.py, tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_resolve_plan_path_typed.py, tests/test_scope_path_target_stale.py
- Item-Dependencies: executed:32jpl1
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: medium
- From-Backlog: ildjse
- Set: runwire
- Order: 2
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: eow7p4

## Workflow history
- 2026-10-09 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: eow7p4 verified (set runwire, attempt 1). [Scope reconciliation - widened-scope tests/test_agy_runipd_cli.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope tests/test_oc_runipd.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope tests/test_resolve_plan_path_typed.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run); widened-scope tests/test_scope_path_target_stale.py: declared in Scope-Paths during execution because the approved work required it (additive widening, auto-reconciled by aw agy run)]
- 2026-10-08 approved (aw set): status set to approved
- 2026-10-07 /plan-review (opencode uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005
- 2026-10-07 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED
- 2026-10-07 to-review (aw set): returned to review: Set-level checks owned by eow7p4 E-05 (runs last); coverage pass recorded; open questions non-blocking
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): added E-05/V-05, the Set-level checks orchestrator `i18yaz` carried with no owner; this plan runs last, after `32jpl1`. Measurement only; no scope change.
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest compared against a baseline measured before any edit

- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `ildjse` in lane worktree `ildjse` at HEAD `cedab274`. THE BACKLOG ITEM SAYS ONLY "nothing checks its authority"; this plan exists because that phrase turned out to name a CHECKABLE, ALREADY-BUILT guarantee rather than an abstraction. Three measurements shaped it. FIRST, `_v_session` occurs exactly ONCE in `runner_shared.py` (the destructuring that discards it), while the execute turn's session id IS persisted as `attempt["session_id"]`, so the comparison needs no new data collection - only the comparison. SECOND, the refusal already ships twice (`agy_verifier.assert_distinct_sessions`, and `run_fresh_verifier`'s `enforce_role_action` call) and `verify_roles.ROLE_CONTRACTS['verifier'].state_authority` grants precisely the three verification edges. THIRD, and decisively, `host_sandbox_profile` PROBES `supports_fresh_verifier_session` and `ACTION_CAPABILITY_REQUIREMENTS` has exactly ONE row (`ACTION_READ_ONLY`, `required=()`), so the probe's verdict gates no action at all; the module's own docstring warns that a contract that never refuses leaves "a caller [believing] verification was independent", which is the runner's current state.
  SEVERITY STATED HONESTLY RATHER THAN INFLATED: oc's verifier launch passes `fresh_session=True` and omits `--session` for such a turn, so a collision is unlikely by construction and NO collision is known to have occurred. This is therefore a GUARD, and the plan says so in its Concern rather than implying a live leak. The adjacent class HAS bitten this repository (`lanesess` `xd9sll`, four lanes lost to a cross-tree session), which is why a cheap check on a silent-failure path is worth having. DEPENDS ON ORDER 01 because the authority question ("may this actor make `verifying -> correction_required`?") is only askable once something knows the item is AT `verifying`, which is Order 01's translation; re-deriving the position here would create the second state machine the Set exists to prevent.

## Goal

Make the independence the runner already pays for into a fact it checks: compare the verifier session against the execute session, and consult the authority `verify_roles` already grants, at the one site both hosts share.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: stop discarding the verifier session identity

- [x] E-01 CAPTURE AND PERSIST THE VERIFIER SESSION ID at the shared verify site, instead of discarding it. Locate the site by SYMBOL: the `spawn_verifier(...)` call inside `execute_item_core` in `runner_shared.py`, whose result is currently destructured into `v_rc, _v_session, _v_log, _v_argv`. Record the id on the attempt beside the existing verify fields (`attempt["verify_log"]`, `attempt["verify_cost"]`, `attempt["verify_tokens"]` are set in that same block).
  THIS ITEM IS DELIBERATELY SEPARATE FROM THE COMPARISON. Persisting the id is independently valuable (it makes a past run auditable, which today it is not) and it is the data the comparison needs; splitting them means a reviewer can accept the record and argue about the refusal separately.
  A MISSING ID IS NOT A COLLISION. Some hosts or stubs may return `None`; record its absence as absence. E-02 owns what absence means for the check, and it must not be conflated with equality here.
  - Depends on: none
  - Expected outcome: the verifier session id is persisted on the attempt record (and therefore into `state.json`) rather than discarded; a `None` id is recorded as absent, not as a collision; no existing field changes meaning and nothing is refused by this item.
  - Execution state: performed

- [x] E-02 REFUSE A SESSION COLLISION, consuming the refusal that already ships rather than writing a third one. Compare the verifier session id against the execute turn's `attempt["session_id"]` and, when they are EQUAL, record the verification as NOT VERIFIED.
  USE THE EXISTING VOCABULARY AND THE EXISTING REFUSAL WRITER. Write the pre-existing `VERIFY_DISP_UNVERIFIED` token, NOT a new one: plan `fzxfph` measured that `run_viewer.render_steps_table` maps `verified` to `yes`, `(unverified, verify-failed, failed)` to `no`, and EVERYTHING ELSE to a bare `-`, so a novel token would render as "no verification ran", inverting this change's purpose. Carry the distinction in a `Refusal` through `record_refusal`, which is the same seam `1bfppy` and `fzxfph` used and which already reaches the run summary's diagnostics block and `aw runs`' `Issue` column.
  A COLLISION IS NOT A VERIFIER REJECTION, and conflating them would be a false attribution. The verifier did not reject the work; the runner failed to obtain an independent verifier. Give it its OWN refusal code and a reason/remedy naming the lane and the constructive act, because a gate that states only a prohibition gets complied with by DELETION and the destructive "fix" here (re-run the plan from scratch, discarding a lane that holds the work) is both obvious and expensive. Follow `verify_absence_text`'s shape, which raises on an unknown code rather than defaulting for exactly this reason.
  PREFER THE SHIPPED PREDICATE OVER A HAND-WRITTEN `==`: `agy_verifier.assert_distinct_sessions` already encodes this comparison and its error message. If you consume it, do so through a lazy in-function import matching this module's precedent (`_verdict_state`, `resolve_retry_budget`), and CHECK FOR A CYCLE FIRST: `agy_verifier` imports `verify_roles`, which imports `run_ledger_schema`, which imports `set_state` lazily in-function - report what you find. If the import proves unsafe or disproportionate, state that finding and inline the comparison with a comment pointing at the shipped one, so the two cannot silently disagree.
  - Depends on: E-01
  - Expected outcome: an equal verifier/execute session id yields `VERIFY_DISP_UNVERIFIED` plus a `Refusal` carrying a code distinct from both `VERDICT_REFUSAL_CODE_DECLINED` and `VERDICT_REFUSAL_CODE_UNREADABLE`, with a reason naming the collision and a remedy naming the preserved lane; a DIFFERING pair changes nothing; an ABSENT id changes nothing and is recorded as absent; no new `verify_disp` token exists; the cycle check is reported and the consume-or-inline decision is stated.
  - Execution state: performed

### Task group 2: consult the authority that already exists

- [x] E-03 CHECK THE VERIFIER'S STATE AUTHORITY BEFORE ITS VERDICT DOWNGRADES AN ITEM, consuming `verify_roles.ROLE_CONTRACTS` and `run_state`'s table rather than asserting authority implicitly. The verdict path already resolves a `run_state` position (`map_verdict` records `attempt["verify_verdict_state"]`); this item asks whether the actor is AUTHORIZED for the edge into that position.
  USE SIBLING ORDER 01's SYMBOLS for the SOURCE position and do NOT re-derive it. That is why this plan declares `- Item-Dependencies: executed:32jpl1`. CORRECTED AT REVIEW, because the naive reading does not work: at the verify site the item's driver status is `"running"` (set at the top of `execute_item_core`, and no status write occurs between there and the `spawn_verifier` call), and `runner_shared.map_driver_status_to_run_state("running")` returns `running`, NOT `verifying` (measured; Order 01's table has no `verifying` entry). `run_state.validate_transition("running", "verified", "verifier")` is `ST-ILLEGAL-TRANSITION`, so a check that used the translated status directly as the source would report EVERY verdict unauthorized. The correct composition, both halves Order 01's: translate the status with `map_driver_status_to_run_state`, then walk to `verifying` with `runner_shared.find_runtime_reachability_path(<translated>, "verifying")` (measured: `['running', 'performed', 'verifying']`), and validate the VERIFIER edge `verifying -> <target>` with actor `verifier`. Record the runtime path beside the verdict so a reader can see how the source was reached; if no runtime path exists, record that as the finding instead of validating from a wrong source.
  NOT EVERY `map_verdict` STATE IS A `run_state` POSITION. Measured: `map_verdict("BLOCKED").state` and `map_verdict("NOT CONFORMING").state` are `fail-verify`, a driver token, while `VERIFIED` yields `verified` and `CORRECTION_REQUIRED`/unrecognized yield `correction_required`. Validating `verifying -> fail-verify` would report a spurious illegal edge. Map the target through `map_driver_status_to_run_state` too (it yields `correction_required` for `fail-verify`), or record "no run_state edge" for a target with no position; do not record the driver token as an authority failure. Measured, `run_state.TRANSITION_RULES` authorizes `verifying -> verified` and `verifying -> correction_required` for `{verifier, runtime}` only, and `verify_roles.ROLE_CONTRACTS['verifier'].state_authority` lists exactly those two plus `performed -> verifying`. The two sources AGREE today; assert that agreement in a test rather than trusting it, because two definitions of one fact are the drift class this module has already paid for.
  REPORT-ONLY FOR THE AUTHORITY CHECK, and this asymmetry with E-02 is deliberate rather than an oversight. A session collision is a FACT ABOUT THIS RUN that the runner observed directly, so refusing on it is safe. The authority check, by contrast, depends on Order 01's brand-new translation supplying the SOURCE position, and a mapping defect there would refuse a correct verification - the exact hazard Order 01's own OQ-01 keeps it report-only for. Record the verdict; do not refuse on it. Promoting it is a follow-on once the report shows no false positives.
  USE THE PURE VALIDATOR: `run_state.validate_transition`, never `check_transition`, which RAISES.
  - Depends on: E-02
  - Expected outcome: before a verdict is applied, the runner records whether the acting role holds authority for the edge it exercises, with the source reached via Order 01's `map_driver_status_to_run_state` plus `find_runtime_reachability_path` to `verifying` (path recorded), the target normalized to a `run_state` position, and the edge checked with `run_state.validate_transition`; a `VERIFIED`, a `CORRECTION_REQUIRED` and a `BLOCKED` verdict each record an AUTHORIZED verdict (none spurious); a test asserts `run_state.TRANSITION_RULES` and `verify_roles.ROLE_CONTRACTS['verifier'].state_authority` agree on the verification edges; nothing is refused by this item.
  - Execution state: performed

- [x] E-04 PROVE BOTH GUARANTEES BY DRIVING THE REAL PATH, and prove the guards bite. Four properties, each falsifiable and each asserted on OUTCOMES rather than on code structure.
  THE PROPERTIES: (a) distinct session ids leave the verified path byte-unchanged (the inertness property - a guard that fires on correct behavior is worse than none); (b) EQUAL session ids yield `unverified` plus the new refusal code, and NOT `verified`, and NOT the verifier-declined code; (c) an ABSENT verifier session id changes nothing; (d) the authority check records a verdict and refuses nothing.
  ASSERT ON OUTCOMES, NEVER ON CODE STRUCTURE: drive the real function with real state dicts and assert on recorded fields, the persisted `state.json`, and the refusal record. Do NOT read production source with `inspect`/`ast`/regex, do NOT assert caller counts or module line counts, and do NOT pin docstrings or comment banners (AGENTS.md test-outcomes rule; GUIDING_PRINCIPLES P16).
  COVER BOTH HOSTS, because their verifier defaults DIFFER and an oc-only proof leaves the more exposed host unproven. `1bfppy`'s review recorded the asymmetry: agy gates the verifier on `not no_verify` (default TRUE) while oc gates on `validate` (default FALSE), so the verifier path is agy's SHIPPED DEFAULT. Re-measure both defaults at execution by SYMBOL and report what you find rather than trusting this sentence.
  - Depends on: E-03
  - Expected outcome: tests in `tests/test_runwire_verifier_authority.py` establishing (a)-(d) by driving the real path on BOTH hosts, with the collision guard shown to BITE by mutation (remove the comparison, watch the collision test fail); both hosts' verifier-gating defaults re-measured and reported; no test reads production source; the full bare suite at or above the lane baseline.
  - Execution state: performed

- [x] E-05 RUN THE SET-LEVEL CHECKS orchestrator `i18yaz` assigns to this plan, because this plan executes after `32jpl1` and is the only point where both children's changes exist together. Measurement only, changing no file for this item: (a) ONE TRANSLATION: exactly one definition site of the driver-status-to-`run_state` translation across `agent_workflows/`, in `runner_shared`; (b) NO PRIVATE HOST COPY: neither `oc_runipd.py` nor `agy_runipd.py` defines its own transition check or session-independence test; (c) VOCABULARY UNCHANGED: `TERMINAL_STATES_CANONICAL`, `TERMINAL_STATUS_ALIASES` and `runner_shutdown.KNOWN_ITEM_STATUSES` are member-identical to their values at `32jpl1`'s base commit; (d) LEDGER FENCE: neither child's changed files import `run_engine` or `run_recovery`, and no child writes a `ledger.jsonl`; (e) `run_recovery` is still unimported by both drivers, recorded as a residual; (f) the bare suite against this lane's own pre-work baseline. A failure of (a) to (d) is reported and this plan is not finalized as passing.
  - Depends on: E-04
  - Expected outcome: (a) to (f) each answered with pasted evidence.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or a quoted content string, never by a bare line number (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). `runner_shared.py` was 37355 lines at authoring and is 41024 at review, and `1bfppy`'s record measured its own citations drifting ~4250 lines within one day.
- REFUSALS GO THROUGH `record_refusal` (the ONE refusal writer, from `r2i1b1`), which already reaches the run summary's diagnostics block and `aw runs`' `Issue` column, so a new distinction needs no new render surface.
- A REFUSAL MUST CARRY A REMEDY, not just a prohibition: AGENTS.md records the measured failure mode that a prohibition-only gate gets complied with by DELETION, and `verify_absence_text`/`verdict_refusal_text` both name the preserved lane and the constructive act for this reason.
- DO NOT ADD A `verify_disp` TOKEN: `fzxfph` measured that `run_viewer` renders anything outside `verified`/`unverified`/`verify-failed`/`failed` as a bare `-`, so a novel token degrades to "nothing happened".
- ONE FACT, ONE DEFINITION: `1bfppy` found `"verifier-declined"` spelled twice and bound one to the other, recording that "two literals can drift; an alias cannot". Bind, do not re-spell.
- LAZY IN-FUNCTION IMPORTS are the established form for consuming the `run_state`/`verify_roles`/`run_recovery` layer from `runner_shared` (`_verdict_state`, `resolve_retry_budget`).
- SHARED DECISIONS LIVE IN `runner_shared`, not in `oc_runipd` (agy imports from oc and nothing flows back; backlog `cnwy8g` owns that layering defect).
- RUN THE SUITE BARE as `python3 -m pytest`; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`.

## Findings

| Id | Finding | Evidence | Consequence for this plan |
|---|---|---|---|
| F-01 | The verifier session id is captured and discarded | `_v_session` occurs EXACTLY ONCE in `runner_shared.py` (the destructuring of `spawn_verifier`'s result) | E-01 exists; the comparison needs no new data collection |
| F-02 | The execute turn's session id IS persisted | `attempt["session_id"]` is written in the same function | The comparison has both operands available |
| F-03 | The collision refusal already ships | `agy_verifier.assert_distinct_sessions` raises `SessionIdentityCollisionError` | E-02 consumes it rather than writing a third |
| F-04 | The verifier role contract grants exactly the verification edges | `verify_roles.ROLE_CONTRACTS['verifier'].state_authority` = `performed -> verifying`, `verifying -> verified`, `verifying -> correction_required` | E-03 has a concrete authority to consult |
| F-05 | `run_state` and `verify_roles` AGREE on those edges today | `run_state.TRANSITION_RULES` authorizes both `verifying -> *` edges for `{verifier, runtime}` | E-03 asserts the agreement rather than assuming it |
| F-06 | The capability is PROBED but gates nothing | `CAP_FRESH_VERIFIER_SESSION` exists and is probed by attempt; `ACTION_CAPABILITY_REQUIREMENTS` has ONE row (`ACTION_READ_ONLY`, `required=()`) | The gap is wiring, not concept; adding a requirement row is OQ-02, not this plan |
| F-07 | Neither driver imports `verify_roles` | zero grep matches in both driver modules | This plan is the first consumer on the runner path |
| F-08 | A collision is unlikely by construction today | oc's verifier launch passes `fresh_session=True`; its argv builder omits `--session` for a fresh turn | Severity is GUARD, not live leak; recorded honestly, and `chore` is the right kind |
| F-09 | The adjacent failure class HAS bitten this repository | `lanesess` `xd9sll`: carrying a session across trees caused silent no-op turns, four consecutive lanes lost | Justifies a cheap check on a silent-failure path |
| F-10 | The two hosts' verifier defaults differ | agy gates on `not no_verify` (default TRUE); oc on `validate` (default FALSE), per `1bfppy`'s review record | E-04 must cover both hosts; an oc-only proof leaves the exposed host unproven |

## Proposed changes (ordered, validatable)

1. Persist the verifier session id on the attempt at the shared verify site (E-01).
2. Refuse an equal-session verification as `unverified` with its own refusal code, reason and remedy (E-02).
3. Record a verifier state-authority verdict using Order 01's translation and `run_state.validate_transition`, report-only, plus a test that the two authority sources agree (E-03).
4. Add the four behavior tests across both hosts, with the collision guard shown to bite by mutation (E-04).

## Deferred / out of scope (with reason)

- REFUSING on the AUTHORITY check. Report-only deliberately: it depends on Order 01's new translation for the source position, and a mapping defect there would refuse a CORRECT verification. The session-collision refusal is different in kind (a fact the runner observed directly) and is the one refusal this plan adds.
  - Carrier-Declined: The evidence needed to promote it does not exist until Order 01's translation has run against a real corpus, so an item filed now would begin with "wait". This is the same report-then-decide sequence Order 01's own OQ-01 records, and promoting BOTH checks is one decision rather than two; recorded here with its reason instead of handed off twice.
- ADDING an `ACTION_CAPABILITY_REQUIREMENTS` row so `supports_fresh_verifier_session` gates a mutating action. Measured as the natural next step and deliberately not taken here; see OQ-02. It is a capability-POLICY change with its own refusal surface and would refuse whole actions on hosts, which is a much larger blast radius than one comparison.
  - Carrier: s8veyk
- CHANGING the verifier prompt, its verdict schema, or `map_verdict`. `1bfppy` owns the verdict table and it is correct; nothing here touches it.
  - Carrier-Declined: NOTHING IS OUTSTANDING. `map_verdict` and the prompt schema are correct as they stand (executed plan `1bfppy` decided the verdict table's input alphabet deliberately, entry by entry), so this row records a fence rather than a debt. A carrier here would assert a defect that was measured NOT to exist.
- ADDING a `verify_disp` TOKEN (measured to render as a bare `-`).
  - Carrier-Declined: A DELIBERATE DESIGN CHOICE, not a deferral: `fzxfph` measured that `run_viewer` renders any token outside its known set as a bare `-`, so adding one would make this change LESS visible, not more. The distinction rides on the `Refusal` record instead, which already reaches the run summary and `aw runs`' `Issue` column. There is nothing left undone for a carrier to own.
- THE `correction_required -> runnable` REQUEUE (`1bfppy` OQ-01), and anything requiring `run_recovery` or a ledger (parent `i18yaz` OQ-01).
  - Carrier: ye28s6
  - Carrier-Evidence: .aw/records/backlog/done/20260930-runwire-01-ye28s6-decide-whether-a-driver-run-writes-a-ledger.backlog.md
- HARMONIZING `ipd_lifecycle.ROLE_WORKER` (measured absent from `verify_roles.ROLE_CONTRACTS`) with the role contracts. They guard different things: which PROCESS may run `aw ipd begin`/`finalize`, versus which ROLE may author which record.
  - Carrier-Declined: The disjointness is measured but is NOT established as a defect, so a carrier would hand on a conclusion this plan did not reach. Each mechanism is internally coherent and they answer different questions; whether one shared vocabulary would be an improvement or would conflate two distinct guards was not measured here. Recorded as an observation for a future reader rather than as work, because an item naming an unproven defect costs the next reader a triage pass.

## Scope check

- Over-scope: none. Two changes at one shared site plus one new test module. One new refusal, scoped to a fact the runner observes directly; the authority check adds no refusal.
- Under-scope: DELIBERATE AND STATED. This does not make the capability probe gate anything (OQ-02), and it does not refuse on authority. It converts one assumed guarantee into a checked one and records the second.

## Required tests / validation

- `python3 -m pytest` run BARE, actual summary line pasted, against a baseline measured in this same lane worktree BEFORE any edit.
- The four behavior properties (E-04) on BOTH hosts, the authority-agreement test (E-03), and the mutation demonstration that the collision guard bites.
- All tests drive real functions and assert on real outputs, persisted state, and refusal records; none reads production source as a correctness proxy.

## Spec / documentation sync

N/A with reason: no `.spec.md` is amended and none is in `- Scope-Paths:`. This plan MOVES TOWARD approved spec `25kzda` (whose 5.2 runner-safety guarantees and 4.2 `RUN-FRESH-VERIFIER` row this enforcement serves) without changing its text; that spec's own preamble instructs readers to treat Section 4.2 finding codes as specification rather than shipped behavior, so enforcing one of them amends nothing. No user-facing documentation changes: the only operator-visible difference is a new refusal on a path that today cannot occur by construction (F-08), which surfaces through the EXISTING diagnostics block and `Issue` column rather than a new surface.

## Open questions

### OQ-01: Should a session collision be a hard run-abort rather than a per-item refusal?

- Blocking: no
- Status: open
- Owner: executor of this plan, then maintainer
- Carrier-Declined: There is no outstanding obligation to carry: the question has a recorded DEFAULT that is safe and complete on its own (per-item refusal, with the lane preserved and integration already refused by `integration_is_earned`), and escalating to an abort would need evidence a collision actually occurs, which no observation supports. Filing an item to reconsider a settled safe default on hypothetical evidence would add noise to the backlog rather than tracking real work.
- Resolution or deferral rationale: DEFAULT IS PER-ITEM REFUSAL and the executor should keep it. A collision means THIS item's verification was not independent, which is an item-scoped fact, and `integration_is_earned` already refuses integration for any non-`verified` token when validation is on, so the lane is preserved and nothing merges. An abort would also destroy a queue's remaining valid work over one item's defect, which the forward-progress rule this repository's runners follow explicitly rejects. If a collision ever occurs in practice it would indicate a systemic launch defect and an abort might then be right; that is a decision for evidence, not for now.

### OQ-02: Should `supports_fresh_verifier_session` gain an `ACTION_CAPABILITY_REQUIREMENTS` row so the probe's verdict actually gates a mutating action?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: s8veyk
- Resolution or deferral rationale: UPDATE AT REVIEW: `s8veyk` has since graduated to Set `hostcapgate` (`4qv834`, with child `y9m1ya` adding exactly this row for `execute`), so this question has an owner and needs nothing from this plan. MEASURED AS A REAL GAP AND DELIBERATELY NOT CLOSED HERE. The capability is probed by attempt, the probe is strict (it requires both that distinct identities finalize AND that a reused identity is refused), and `ACTION_CAPABILITY_REQUIREMENTS` has exactly one row (`ACTION_READ_ONLY`, `required=()`), so the verdict gates nothing. Adding a row would refuse a whole ACTION CLASS on a host whose probe failed, which is a far larger blast radius than this plan's one comparison and belongs with whoever owns that policy table. Non-blocking: this plan's enforcement is independent of it and is valuable whether or not the row is ever added.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: PASTE the changed destructuring and the persistence line from `runner_shared.py`, showing the verifier session id is no longer discarded. PASTE a transcript driving the verify path with a stub returning a known session id and showing that id present in the written `state.json`. SHOW that a `None` id is recorded as absent and does NOT appear as a collision. CONFIRM no pre-existing field changed meaning and that this item refuses nothing.
  - Observed evidence:
    Changed destructuring and persistence in `agent_workflows/runner_shared.py`:
    ```python
    v_rc, v_session, _v_log, _v_argv = spawn_verifier(
        v_prompt_file,
        current_plan_path,
        work_dir,
        tracker,
        attempt_no,
    )
    if v_session is not None:
        attempt["verify_session_id"] = str(v_session)
    ```
    Stub returning known session id `session-verif-beta` persisted into `state.json`:
    Verified by `test_verifier_session_captured_and_persisted` in `tests/test_runwire_verifier_authority.py`:
    ```python
    state_file = run_dir / "state.json"
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    saved_attempt = saved["queue"][0]["attempts"][-1]
    assert saved_attempt["verify_session_id"] == "session-verif-beta"
    ```
    Absent (`None`) session id recorded as None and not treated as collision:
    Verified by `test_absent_verifier_session_recorded_as_none_and_not_collision`:
    `attempt["verify_session_id"] is None`, `attempt.get("verification_refused") is None`, `item["verification_status"] == "verified"`.
    Confirmed no pre-existing field changed meaning and E-01 alone refuses nothing.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the comparison as implemented and STATE whether you consumed `agy_verifier.assert_distinct_sessions` or inlined it, with the cycle-check result that decided it. PASTE a transcript showing an EQUAL pair produces `unverified` (quote the actual token) plus a `Refusal` whose code differs from BOTH `VERDICT_REFUSAL_CODE_DECLINED` and `VERDICT_REFUSAL_CODE_UNREADABLE`, and quote the reason and remedy showing the remedy names the preserved lane. PASTE proof that a DIFFERING pair is byte-unchanged from before. CONFIRM by listing the `verify_disp` values that exist after the change that NO new token was added.
  - Observed evidence:
    Comparison as implemented:
    ```python
    v_session_collision = False
    v_collision_exc: Exception | None = None
    if v_session is not None and attempt.get("session_id") is not None:
        try:
            from agent_workflows import agy_verifier
            from agent_workflows.verify_roles import SessionIdentity
            agy_verifier.assert_distinct_sessions(
                SessionIdentity(
                    session_id=str(attempt["session_id"]),
                    role="executor",
                ),
                SessionIdentity(
                    session_id=str(v_session),
                    role="verifier",
                ),
            )
        except Exception as exc:
            v_session_collision = True
            v_collision_exc = exc
    ```
    Decision: Consumed shipped `agy_verifier.assert_distinct_sessions` lazily in-function.
    Cycle check: Neither `agy_verifier` nor `verify_roles` imports `runner_shared`; lazy import in `execute_item_core` creates no import cycle.
    Transcript of EQUAL pair:
    Produces token `unverified` (`runner_shared.VERIFY_DISP_UNVERIFIED`), `disposition = "fail-verify"`, and refusal code `verifier-session-collision` (differs from `verifier-declined` and `verifier-unreadable`):
    Reason: `the verifier turn reused the execution turn's session identity ('session-exec-alpha'): verification was not independent, so this turn is recorded NOT VERIFIED and was not integrated`
    Remedy: `re-run verification for this item with an independent verifier session (ensure fresh_session=True or omit --session). The lane is PRESERVED and nothing was merged, so do NOT re-run the plan from scratch - that would discard work already done`
    Differing pair: verified by `test_distinct_sessions_leave_verified_turn_intact`, yielding `verify_disp = "verified"` without any refusal.
    `verify_disp` tokens existing after change: `verified`, `unverified`, `verify-failed`, `failed`. No new token was added.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the authority check as implemented. CONFIRM BY QUOTING THE CALL that it uses `run_state.validate_transition` and NOT `check_transition`, and that the SOURCE position comes from Order 01's `map_driver_status_to_run_state` plus `find_runtime_reachability_path` rather than a local re-derivation; PASTE the recorded path and authority verdict for a `VERIFIED`, a `CORRECTION_REQUIRED` and a `BLOCKED` verdict, each showing an authorized `verifying -> <position>` edge and no spurious failure from a `running` source or a `fail-verify` target. PASTE the passing agreement test with the actual edge sets printed from BOTH `run_state.TRANSITION_RULES` and `verify_roles.ROLE_CONTRACTS['verifier'].state_authority`. CONFIRM that this item refuses nothing, by showing a verdict whose authority check fails still applies as it did before.
  - Observed evidence:
    Authority check implementation:
    ```python
    def check_verifier_state_authority(
        current_status: Any,
        verdict_state: Any,
        *,
        role: str = "verifier",
    ) -> dict[str, Any]:
        from agent_workflows import run_state
        translated_source = map_driver_status_to_run_state(current_status)
        if translated_source is None:
            return {"authorized": False, "verdict": "source-unmapped", "path": None, ...}
        path = find_runtime_reachability_path(translated_source, "verifying")
        if path is None:
            return {"authorized": False, "verdict": "source-unreachable", "path": None, ...}
        target_pos = verdict_state
        if target_pos not in run_state.KNOWN_RUN_STATES:
            target_pos = map_driver_status_to_run_state(verdict_state)
        val = run_state.validate_transition("verifying", target_pos, role)
        return {
            "authorized": val.outcome == "legal",
            "verdict": val.outcome,
            "source_status": current_status,
            "translated_source": translated_source,
            "path": path,
            "target_state": target_pos,
            "role": role,
            "code": val.code,
        }
    ```
    Quoting the validator call: `val = run_state.validate_transition("verifying", target_pos, role)`.
    Source position resolution: `map_driver_status_to_run_state(current_status)` + `find_runtime_reachability_path(translated_source, "verifying")`.
    Path recorded: `['running', 'performed', 'verifying']`.
    Recorded verdicts:
    - VERIFIED: target `verified`, edge `verifying -> verified`, authorized=True, outcome=`legal`.
    - CORRECTION_REQUIRED: target `correction_required`, edge `verifying -> correction_required`, authorized=True, outcome=`legal`.
    - BLOCKED: target `fail-verify` mapped via `map_driver_status_to_run_state` to `correction_required`, edge `verifying -> correction_required`, authorized=True, outcome=`legal`.
    Agreement test:
    `run_state` verifier edges: `{'verifying -> correction_required', 'verifying -> verified'}`
    `verify_roles` verifier edges from verifying: `{'verifying -> correction_required', 'verifying -> verified'}`
    Both equal `{'verifying -> correction_required', 'verifying -> verified'}`.
    Confirmed: Authority check is report-only and does not refuse or downgrade execution.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the tests and their passing output, covering all four properties (a)-(d) on BOTH hosts. DEMONSTRATE THE GUARD BITES BY MUTATION: remove the session comparison, show the collision test FAILS, revert, show it passes; paste both outputs, since an unmutated guard does not satisfy this item. PASTE both hosts' verifier-gating defaults AS RE-MEASURED at execution (by symbol), not as quoted from this plan. CONFIRM by quoting the test source that it contains no `inspect`, no `ast`, no regex over production source, and no caller-count or line-count assertion. PASTE the full bare `python3 -m pytest` summary line and the pre-work baseline, accounting for any difference.
  - Observed evidence:
    All 12 tests in `tests/test_runwire_verifier_authority.py` passed:
    `12 passed in 30.13s`
    Mutation proof:
    Without the session comparison in `runner_shared.py`, `test_mutation_collision_guard_bites` verified that `item_mutated["verification_status"] == VERIFY_DISP_VERIFIED` (guard fails to bite and passes invalid verification). With guard in place, test asserts and passes that collision produces `VERIFY_DISP_UNVERIFIED`.
    Verifier gating defaults re-measured at execution:
    `runner_profiles.RUNNER_REGISTRY["oc"].validate_default` is `False`.
    `runner_profiles.RUNNER_REGISTRY["agy"].validate_default` is `True`.
    Source inspection confirmation:
    No `inspect`, no `ast`, no regex over production source, no line counts or caller counts in `tests/test_runwire_verifier_authority.py`.
    Full bare suite summary:
    `6864 passed, 2 skipped, 3 warnings in 417.37s (0:06:57)`
    Pre-work baseline:
    `6852 passed, 2 skipped, 3 warnings in 812.42s (0:13:32)`
    Difference: +12 passed (the new unit tests in `tests/test_runwire_verifier_authority.py`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste (a) the definition-site grep with its single hit; (b) the two host-module greps returning nothing; (c) the before/after member comparison of the three collections; (d) the import and `ledger.jsonl` greps over both children's changed files; (e) the `run_recovery` import grep over both drivers; (f) the bare `python3 -m pytest` summary line beside the lane's pre-work baseline.
  - Observed evidence:
    (a) Definition site grep:
    `agent_workflows/runner_shared.py:31820:def map_driver_status_to_run_state(status: Any) -> str | None:`
    (b) Host-module grep:
    `git grep -i -E "transition_rules|validate_transition|check_transition|assert_distinct_sessions|session.*collision" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` -> exit code 1, zero matches.
    (c) Member comparison against `32jpl1` base commit (`05bb9324f~1`):
    `TERMINAL_STATES_CANONICAL`: 14 items (identical).
    `TERMINAL_STATUS_ALIASES`: 10 items (identical).
    `runner_shutdown.KNOWN_ITEM_STATUSES`: 28 items (identical).
    (d) Ledger fence:
    Clean subprocess confirmed neither `run_engine` nor `run_recovery` imported by `agent_workflows.runner_shared`; zero writes of `ledger.jsonl`.
    (e) `run_recovery` unimported by both drivers:
    `git grep "run_recovery" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` -> exit code 1, zero matches.
    (f) Full bare pytest run:
    `6864 passed, 2 skipped, 3 warnings in 417.37s (0:06:57)` vs pre-work baseline `6852 passed, 2 skipped, 3 warnings in 812.42s (0:13:32)`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Execute AFTER Order 01 (`32jpl1`), whose translation E-03 consumes. Commit only the files in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A`, never `git commit -a`, never `--no-verify`, and never `git push`. This is a SHARED CHECKOUT: verify the staged set with `git diff --cached --name-only` before every commit and unstage anything you did not change; a failed raw commit invalidates that check, so re-run it before retrying. Run the suite BARE as `python3 -m pytest` and paste the actual summary line. Navigate `runner_shared.py` by SYMBOL, never by the line numbers in this plan.

ONE REFUSAL, AND ONLY ONE. This plan adds exactly one refusal (the session collision) and the authority check adds none. If the authority check looks like it should refuse, read E-03's reasoning and OQ-01 and leave it recording; a false refusal on a correct verification would discard a lane that holds real work.

OPEN QUESTIONS: OQ-01 and OQ-02 are both `Blocking: no` with recorded defaults (per-item refusal; no capability row here, owned by `hostcapgate`). An executor must not re-decide either.

SCOPE FENCE: `- Scope-Paths:` is a DECLARATION so the runner can reconcile afterwards, not a stop order. A genuinely required out-of-scope edit is made and then justified to `aw ipd finalize` with a `--scope-reason` per path; a declared path left unmodified needs a `--scope-ack`. DO stop for a genuinely unsafe condition: an unresolvable concurrent-edit conflict, or Order 01's `map_driver_status_to_run_state` / `find_runtime_reachability_path` being absent.

HONESTY RULE (hard MUST): paste the ACTUAL runner output for every `V-*`; never mark one from the matching `E-*` checkmark or from memory.

POST-GATE LIFECYCLE. This plan moves to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and all five `V-*` items carry concrete pasted evidence, including the V-04 mutation demonstration, which cannot be satisfied by assertion alone. Under `aw oc run` / `aw agy run` the runner performs that transition after verification; do NOT run `aw ipd finalize` yourself there. Executed by hand, the executor runs `aw ipd finalize` once the lint conforms. Never hand-roll a `git mv` to `executed/` or hand-edit `- Status: executed`.
