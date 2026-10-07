# IPD: Wire the run state machine into the host runners

- Date: 2026-09-30
- Kind: orchestrator
- Concern: `run_state.py`, `verify_roles.py` and `run_recovery.py` define a closed state set, a complete legal transition table with per-edge AUTHORITY, and a role contract granting the verifier exactly the verification edges - and NEITHER host driver imports ANY of the three. RE-MEASURED at lane HEAD `cedab274` by grepping both driver modules for all three module names: ZERO matches in `agent_workflows/oc_runipd.py` and ZERO in `agent_workflows/agy_runipd.py`, so the backlog item's central claim holds unchanged eight days later.
  WHAT THE DRIVERS USE INSTEAD, measured rather than described. `runner_shared.TERMINAL_STATES_CANONICAL` holds FOURTEEN tokens and `run_state.ALL_STATES` holds ELEVEN, and their intersection is exactly ONE (`failed`); computed in-process. Widening the comparison to the driver's live-plus-terminal token set (16 values including `queued`, `running`, `partial`, `interrupted`) the intersection is still ONE (`running`). A THIRD vocabulary exists in the same area: `ipd_lifecycle.ROLE_WORKER` is `worker`, which is absent from `verify_roles.ROLE_CONTRACTS` (7 roles: coordinator, corrector, executor, human, investigator, runtime, verifier), so the shipped role guard `AW-LIFECYCLE-ROLE-001` and the shipped role CONTRACT share no token either.
  WHY THE OVERLAP IS SMALL, AND WHY THAT IS THE FINDING RATHER THAN A COUNTERARGUMENT. The two vocabularies are indexed on DIFFERENT AXES: `run_state`'s tokens name WHERE AN ITEM IS in a lifecycle (`pending`, `runnable`, `verifying`), while the driver's name WHICH AUTHORITY REFUSED (`fail-gate`, `fail-begin`, `fail-lane`, `fail-verify`, `fail-depend`, `fail-merge`, per the `statusvocab` comment above `TERMINAL_STATES_CANONICAL`: "Every non-`executed` label names the refusing authority"). So this Set is NOT a rename of one onto the other, and any child that tries to collapse them is wrong. The genuine defect is that the axes are UNRELATED: nothing records which lifecycle position a driver item occupies, so no legal-edge check and no authority check can run at all.
  THE COST IS PAID REPEATEDLY AND IS CITED IN-TREE, which is what makes this a defect rather than a taste preference. `runner_shared`'s own `retrywire` comment records that `run_recovery.plan_retry` "REMAIN[S] THE INTENDED LONG-TERM HOME" yet is "UNREACHABLE from a driver run", and that the driver therefore carries a SECOND implementation of retry semantics - "this repository normally refuses one". The `1bfppy` block comment records the same gap in the verdict path. Plan `fzxfph` had to mint FOUR reason codes after measuring that `run_state` has no token for any of them.
- Scope: Close the wiring gap in the two places it is CHECKABLE, and record what remains blocked on a substrate decision this Set is forbidden from taking. Order 01 introduces ONE shared translation from the driver's item status to a `run_state` position and uses it to CHECK each driver transition against the legal table (report-only, refusing nothing). Order 02 consumes `verify_roles` at the one shared verify site to enforce verifier session independence and verifier state authority, both of which are currently unenforced and one of which is measurably discarded (`_v_session` is captured and never read).
  EXCLUDES, AND THIS FENCE IS THE MOST IMPORTANT PART OF THIS PLAN. (1) NO LEDGER. Making a driver run write a hash-chained `ledger.jsonl` so `run_engine.RunEngine` and therefore `run_recovery` become reachable is EXPLICITLY OPEN and is NOT decided here; `runner_shared`'s own comment says "WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN ... Nobody may cite this section as a decision to abandon the ledger design", and approved spec `25kzda` concedes the ledger is built but unwired. `run_recovery` is therefore UNREACHABLE BY CONSTRUCTION from a driver run and this Set does not import it; see OQ-01. (2) NO REQUEUE. The `correction_required -> runnable` transition remains unimplemented (`1bfppy` OQ-01). (3) NO VOCABULARY REPLACEMENT. No driver status token is renamed, removed, or re-spelled, and `TERMINAL_STATES` keeps every member: a translation is ADDITIVE and a rename would break `run_viewer`, `runner_shutdown.KNOWN_ITEM_STATUSES`, `artifact_audit` and the attention mapping at once. (4) NO NEW REFUSAL from the transition check (Order 01 is report-only); Order 02 DOES refuse, and its fence says exactly where.
- Scope-Paths: .aw/records/plans/pending/20260930-runwire-00-i18yaz-wire-the-run-state-machine-into-the-host-runners.ipd.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Coverage: pass
- Coverage-Fingerprint: d3b882caa768fe31875e606991d066d528cd607133270b443758d8686292d710
- Coverage-Checked: 2026-10-07 by uri/its_direct/pt3-claude-opus-5.5-1m-us
- Work-Kind: chore
- Priority: medium
- From-Backlog: ildjse
- Set: runwire
- Order: 0
- Highest E allocated: 02
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: i18yaz

## Workflow history
- 2026-10-07 reviewed (aw set): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. E-01/E-02 reduced to confirm-child items reading 32jpl1 (executed) and eow7p4 V-05, which owns the Set-level checks; removed demands on deleted tests (test_runner_shutdown.py, test_runner_refork_guard.py); restated the shared runner_shared.py path as serialized, not colliding; recorded that ildjse reopened and needs re-graduation; fixed the addopts quote; completed the execution contract.
- 2026-10-07 coverage pass (aw oc run): fingerprint d3b882caa768, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 to-review (aw set): returned to review: Set-level checks owned by eow7p4 E-05 (runs last); coverage pass recorded; open questions non-blocking
- 2026-10-07 coverage pass (aw oc run): fingerprint 0ff0457383ab, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-10-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): each criterion and Set-level check now leads with its owner; the cross-child checks are owned by `eow7p4` E-05, which runs last.
- 2026-10-06 draft (aw set): demoted to-review -> draft: returned to authoring by gradcover 52opph: uncovered obligation: Bare pytest compared against a baseline measured before any edit

- 2026-10-06 coverage fail (aw oc run): fingerprint 086243502328, model uri/its_direct/pt3-claude-opus-5.5-1m-us
- 2026-09-30 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Authored from backlog `ildjse` in lane worktree `ildjse` at HEAD `cedab274`. EVERY claim in the item was re-measured rather than trusted, and the item held up on its central claim: both drivers still import none of the three modules (zero grep matches each). THREE THINGS THE ITEM DID NOT SAY that shaped this Set.
  FIRST, THE ITEM'S "THREE OVERLAPPING VOCABULARIES" IS TRUE BUT ITS IMPLIED REMEDY IS NOT. Measured, the driver and `run_state` vocabularies overlap in exactly ONE token out of 14 and 11, because they are indexed on different axes (lifecycle POSITION versus REFUSING AUTHORITY, the latter stated verbatim in the `statusvocab` comment). So "the runners still carry their own status vocabulary in parallel" cannot be fixed by adopting one vocabulary; the honest fix is a TRANSLATION plus a CHECK, which is what Order 01 does. A plan that read the item as a rename would have broken five readers.
  SECOND, ONE OF THE ITEM'S THREE MODULES IS UNREACHABLE AND THE ITEM DOES NOT SAY SO. `run_recovery`'s entire public API takes a `run_engine.RunEngine` first positional and calls `reconstruct_state()`; `RunEngine` requires a `RunLedgerStore` over a `ledger.jsonl`; no driver run writes one. `runner_shared`'s `retrywire` comment records this and explicitly forbids treating it as a decision to abandon the ledger. So "wire in all three" is not executable as stated, and this Set wires TWO and records the third as OQ-01 rather than silently dropping it or silently building a ledger.
  THIRD, THE ITEM'S "NOTHING CHECKS ITS AUTHORITY" UNDERSTATES A CONCRETE, ALREADY-PAID-FOR GAP. At the one shared verify site in `runner_shared.execute_item_core`, the verifier's session id is captured and DISCARDED (`v_rc, _v_session, _v_log, _v_argv = spawn_verifier(...)`, and `_v_session` appears exactly once in the whole 37k-line module), so nothing compares it to the execute session. `verify_roles` already ships `SelfVerificationForbiddenError` and `agy_verifier` already ships `SessionIdentityCollisionError` for precisely this, unused by the runners. That gave Order 02 a falsifiable subject instead of a vocabulary-tidying exercise.
  ALSO CORRECTED: the item's closing line says the requeue is deferred "because the drivers have no per-item retry loop at all for a requeue to consume". THAT PREMISE HAS EXPIRED. Plan `xipfy1` (`retrywire`) shipped `handle_turn_failure_retry`, `frozen_retry_budget`, `turn_retry_budget_remaining` and `TURN_RETRY_CLASSIFICATION`, and `execute_item_core` calls the handler on execute turns; a turn failure IS re-dispatched today within the frozen budget. The requeue stays out of scope for a DIFFERENT and stronger reason (it would spend correction budget on a verifier rejection, a class `TURN_RETRYABLE_DISPOSITIONS` deliberately excludes - see its comment "Retrying a turn whose VERIFIER rejected it would also spend correction budget on a class `1bfppy` is separately wiring"), which is recorded rather than the stale one.
  NO SPEC AMENDED. Spec `25kzda` is MOVED TOWARD, not changed: its Section 4.2 finding codes are specification rather than shipped behavior, and nothing here alters a contract another plan is reviewed against. No `.spec.md` is in any child's `- Scope-Paths:`.

## Goal

Make the shipped state machine actually observe the runs it was written for: translate the driver's item status onto a `run_state` position once, check every driver transition against the legal table, and enforce the verifier authority `verify_roles` already grants - without renaming a single driver token and without deciding the open ledger question.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: orchestration of the runwire Set

- [ ] E-01 CONFIRM 32jpl1 REACHED executed
  - Depends on: none
  Confirm child 01 (`32jpl1`, map the driver item status vocabulary onto run_state) is `executed`, with its own validation evidence present. At review (2026-10-07) it IS executed (`.aw/records/plans/executed/20260930-runwire-01-32jpl1-...ipd.md`, finalize commit `f4de9ea19`), so this item reads its record; it does not re-perform its checks. Also read back the two children's front matter: each carries `- From-Backlog: ildjse`, neither declares a `- Blocks-Release:` gate, and `eow7p4` declares `- Item-Dependencies: executed:32jpl1`. Both children declare `agent_workflows/runner_shared.py`; that shared path is EXPECTED (both wire the one shared module) and is serialized by the dependency edge, so it is not a collision.
  - Expected outcome: `32jpl1` reads `- Status: executed` under `executed/` with every `V-*` carrying pasted evidence and `Result: pass`; both child rows resolve to real files; the front-matter properties above are quoted; no product file is touched by this item.
  - Execution state: pending

- [ ] E-02 CONFIRM eow7p4 REACHED executed
  - Depends on: E-01
  Confirm child 02 (`eow7p4`, enforce verifier session independence and verifier state authority) is `executed`. The Set-wide checks (one translation, no private host copy, vocabulary unchanged, ledger fence, `run_recovery` residual, bare suite against baseline) are PERFORMED by `eow7p4` E-05/V-05, which runs last; this item only confirms that child's V-05 carries pasted evidence for each of (a) to (f) and does not re-run them.
  - Expected outcome: `eow7p4` reads `- Status: executed` under `executed/`; its V-05 shows pasted evidence for (a) to (f), including an EMPTY symmetric difference for each of the three vocabulary collections and the bare-suite line beside the baseline.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | File | What it does | Depends on |
|---|---|---|---|---|
| 01 | `32jpl1` | `20260930-runwire-01-32jpl1-map-the-driver-item-status-vocabulary-onto-run-state-through.ipd.md` | Adds ONE shared translation from a driver item status to a `run_state` position, and uses it to CHECK each driver status write against `run_state`'s legal transition table. Report-only: records the check result and refuses nothing. | none |
| 02 | `eow7p4` | `20260930-runwire-02-eow7p4-enforce-verifier-session-independence-and-verifier-state-aut.ipd.md` | Consumes `verify_roles` at the one shared verify site: asserts the verifier session identity differs from the execute session's (today `_v_session` is discarded), and checks the verifier's `state_authority` before its verdict is allowed to downgrade an item. | 01 |

WHY 02 DEPENDS ON 01 rather than being independent: 02's authority check asks "is this actor allowed to make the transition `verifying -> correction_required`?", and that question is only askable once something knows the item is AT `verifying`, which is exactly what 01's translation supplies. Ordered serially so 02 consumes 01's function instead of privately re-deriving the position, which would create the second state machine this Set exists to avoid.

## Completion criteria (the whole Set is done only when)

- [Owner: 32jpl1] ONE translation exists from a driver item status to a `run_state` position, in `runner_shared` (the module both hosts already share), and neither driver carries a private copy.
- [Owner: 32jpl1] Every driver item-status write is checked against `run_state`'s legal transition table, and an illegal transition is RECORDED with the edge it attempted.
- [Owner: eow7p4] The verifier turn's session identity is compared against the execute turn's, and a collision is refused rather than discarded.
- [Owner: eow7p4] The verifier's `state_authority` from `verify_roles.ROLE_CONTRACTS` is consulted before a verdict downgrades an item.
- [Owner: 32jpl1, rechecked by eow7p4 E-05] NO driver status token is renamed or removed; `TERMINAL_STATES_CANONICAL`, `TERMINAL_STATUS_ALIASES` and `runner_shutdown.KNOWN_ITEM_STATUSES` are member-identical before and after.
- [Owner: each child at its boundary; eow7p4 E-05 last] The full suite passes with actual pasted output, at or above the lane's pre-work baseline.
- [Owner: eow7p4 E-05] `run_recovery` remains unimported by both drivers and that residual is recorded, not hidden.

## Cross-IPD validation

- [Owner: eow7p4 E-05, which runs last] NO SECOND STATE MACHINE: after both children, exactly one module defines the driver-status-to-`run_state` translation. Proven by grepping for the translation symbol across `agent_workflows/` and asserting one definition site.
- [Owner: eow7p4 E-05, which runs last] NO PRIVATE HOST COPY: neither `oc_runipd.py` nor `agy_runipd.py` carries its own transition check or its own session-independence test; both reach the shared ones through `runner_shared`. (As authored this cited `tests/test_runner_refork_guard.py` as precedent; that file was deleted by test-trim commit `19313eed7` and no longer exists, so it is not a precedent to rely on.)
- [Owner: eow7p4 E-05, which runs last] VOCABULARY UNCHANGED: the before/after member comparison from E-02, run once for the Set.
- [Owner: eow7p4 E-05, which runs last] THE LEDGER FENCE HELD: neither child imports `run_engine` or `run_recovery`, and no child writes a `ledger.jsonl`. Proven by grep across both children's changed files.

## Deferred / out of scope (with reason)

- WIRING `run_recovery` (the third module the backlog item names). UNREACHABLE BY CONSTRUCTION: its whole API takes a `run_engine.RunEngine` and calls `reconstruct_state()`, `RunEngine` requires a `RunLedgerStore` over `ledger.jsonl`, and no driver run writes one. Whether a driver run SHOULD write a ledger is explicitly open (`runner_shared`'s `retrywire` comment forbids reading it as settled; spec `25kzda` concedes the ledger is built but unwired). Recorded as OQ-01 for the maintainer, not silently dropped.
  - Carrier: ye28s6
- THE `correction_required -> runnable` REQUEUE. `1bfppy` OQ-01, still deferred. The reason is now that it would spend the frozen correction budget on a verifier rejection, which `TURN_RETRYABLE_DISPOSITIONS` deliberately excludes by allowlist; changing that allowlist is a scheduling decision, not a wiring one.
  - Carrier-Declined: This is not this Set's obligation to carry onward: it is an EXISTING deferral owned by executed plan `1bfppy`'s OQ-01, recorded there with its reason, and re-filing it here would create a second owner for one decision. Restating it in this section is disclosure of a fence, not the creation of a new debt. Acting on it is a SCHEDULING decision (it changes what the frozen correction budget is spent on, and `TURN_RETRYABLE_DISPOSITIONS` excludes the verifier-rejection class by deliberate allowlist with its reason written down), so it needs a maintainer's call on retry accounting rather than a carrier from a wiring Set.
- REPLACING the driver's status vocabulary with `run_state`'s. The two are indexed on different axes (position versus refusing authority) and five readers depend on the driver's tokens. A translation is additive; a replacement is a different, much larger plan.
  - Carrier-Declined: NOT A DEFECT AND THEREFORE NOT A DEBT, which is why no carrier is filed. The two vocabularies are indexed on different axes BY DESIGN (the `statusvocab` comment states "Every non-`executed` label names the refusing authority"), so the driver tokens are correct as they stand and there is nothing outstanding to fix. This row records a boundary a reader might otherwise assume this Set crossed; filing a backlog item to "consider replacing a correct vocabulary" would manufacture work nobody has asked for.
- HARMONIZING `ipd_lifecycle.ROLE_WORKER` with `verify_roles.ROLE_CONTRACTS`. Measured as a real third disjoint vocabulary, but `AW-LIFECYCLE-ROLE-001` guards a different thing (which PROCESS may run `aw ipd begin`/`finalize`) than `verify_roles` does (which ROLE may author which record). Merging them needs its own analysis and would touch the shipped lifecycle guard.
  - Carrier-Declined: The disjointness is MEASURED but is not established as a defect, so filing a carrier would assert a conclusion this Set did not reach. The two mechanisms answer different questions (which PROCESS may run a lifecycle verb, versus which ROLE may author which record) and each is internally coherent; a shared vocabulary might be an improvement or might conflate two guards, and nothing here measured which. Recorded as an observation for a future reader rather than handed off as work, because a carrier naming an unproven defect wastes the next reader's time triaging it.
- MAKING `run_state`'s table REFUSE a driver transition. Order 01 is deliberately report-only; a refusing gate on a vocabulary this newly translated would wedge live runs on a mapping defect. Promoting the check to a refusal is a follow-on once the report shows zero false positives across a real corpus.
  - Carrier-Declined: DELIBERATELY NOT FILED YET, because the precondition for the decision does not exist until this Set has run. Promoting the check to a refusal requires evidence that it produces no false positives on a real corpus, and no such corpus exists before Order 01 ships the report-only check. Filing a carrier now would create an item whose first action is "wait", and the plan's OQ-02 already records the decision and its owner. The honest sequence is: ship the report, read the corpus, then file the promotion if the evidence supports it.

## Scope check

- Over-scope: none. Each child touches the one shared module plus its tests; neither renames a token nor adds a refusal beyond the one Order 02 names explicitly.
- Under-scope: DELIBERATE AND STATED. This Set does not make the drivers use `run_state` as their PRIMARY state representation, and it does not wire `run_recovery` at all. It makes the shipped table OBSERVE the runs (check + authority) rather than GOVERN them. Governing them requires the ledger decision, which is the maintainer's.

## Required tests / validation

- [Owner: eow7p4 E-05/V-05, plus each child's own V-items] `python3 -m pytest` run BARE (the configured `addopts` already supply `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, `pyproject.toml` `addopts`), with the actual `N passed` summary line pasted, compared against a baseline measured in this same lane worktree BEFORE any edit.
- [Owner: eow7p4 E-05/V-05, plus each child's own V-items] Each child's own new tests, which must drive real functions and assert on real outputs (no `inspect`/`ast`/regex over production source, no caller-count or line-count assertions; GUIDING_PRINCIPLES P16).
- [Owner: eow7p4 E-05/V-05, plus each child's own V-items] The four cross-IPD checks above, each with pasted evidence.

## Open questions

### OQ-01: Should a driver run write a hash-chained `ledger.jsonl`, making `run_engine` and `run_recovery` reachable?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: ye28s6
- Resolution or deferral rationale: NOT THIS SET'S TO TAKE, and the repository says so in two places. `runner_shared`'s `retrywire` comment states "WHETHER A DRIVER RUN SHOULD WRITE A LEDGER IS STILL OPEN and is NOT decided here ... Nobody may cite this section as a decision to abandon the ledger design", and approved spec `25kzda`'s preamble concedes "the ledger is built but UNWIRED". Plans `i1hlgx` and executed `7wei1o` both name it as an out-of-scope design question. This Set proceeds WITHOUT it, which is why it wires two modules and not three; nothing here forecloses either answer. NON-BLOCKING because both children are executable and valuable with the answer unknown: a translation and an authority check need no ledger.

### OQ-02: Should the transition check ever REFUSE, rather than only record?

- Blocking: no
- Status: open
- Owner: executor of Order 01, then maintainer
- Carrier-Declined: The decision's PRECONDITION does not exist until this Set has run, so there is nothing for a carrier to act on yet. Promoting the check to a refusal requires evidence that it yields no false positives on a real corpus, and that corpus is produced BY Order 01's report-only check; an item filed now would have "wait for the report" as its first and only step. The decision is recorded here with its owner and its default, and the honest sequence is ship, measure, then file if the evidence supports promotion.
- Resolution or deferral rationale: DEFAULT IS REPORT-ONLY and the executor must not change it. A refusing gate keyed on a brand-new translation would wedge live runs on a mapping defect rather than on a real illegal transition, and the driver's status writes have never been checked, so the false-positive rate is unmeasured. The safe sequence is: record first, read the corpus, then decide. If Order 01's executor finds the check fires on a CORRECT driver transition, that is a mapping defect to fix in Order 01, and it is also the evidence that report-only was the right default.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: PASTE `grep -n '^- Status:' <32jpl1 path>` showing `- Status: executed` with the path under `.aw/records/plans/executed/`, and its `AW_NO_REEXEC=1 aw ipd lint --phase post-transition` output conforming. PASTE a directory listing resolving BOTH child paths, plus, for each child, the four `- From-Backlog:`, `- Blocks-Release:` (expected ABSENT), `- Scope-Paths:` and `- Item-Dependencies:` lines quoted verbatim. State explicitly whether Order 02 declares Order 01 as a dependency and whether it consumes Order 01's translation (`runner_shared.map_driver_status_to_run_state`), since the table requires those two to agree. PASTE `aw ipd lint` output for `eow7p4` showing conforming.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE `grep -n '^- Status:' <eow7p4 path>` showing `- Status: executed` under `.aw/records/plans/executed/`, and its post-transition lint output conforming. QUOTE from `eow7p4`'s V-05 the pasted evidence for each of (a) to (f): the single definition-site hit, the two empty host-module greps, the three EMPTY symmetric differences (the "before" taken from `32jpl1`'s base commit, not remembered), the ledger-fence greps, the `run_recovery` residual, and the bare-suite summary line beside the pre-work baseline. A V-05 whose evidence for any of (a) to (f) is empty or paraphrased FAILS this item, as does any non-empty symmetric difference, regardless of whether the suite passes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This orchestrator carries ORCHESTRATION ONLY. Its two E-items confirm the children exist and agree (E-01), and check the one Set-wide invariant that is cheaper to verify once than twice (E-02). None of them edits a product file, so none of them is work a child should own instead. Its `- Scope-Paths:` is its own file for that reason.

EXECUTION CONTRACT. Execute children in Order (01, already executed at review, then 02); 02 consumes 01's translation and must not re-derive it. Commit only files changed for the item being executed, through `aw commit <plan> -- <paths>`, never `git add -A` and never `git push`. Verify the staged set with `git diff --cached --name-only` before every commit: this is a shared checkout and uncommitted work you did not create is not yours. Run the suite BARE as `python3 -m pytest` and paste the actual summary line; never claim a pass you did not run. SCOPE FENCE: `- Scope-Paths:` is a declaration for finalize's reconciliation; an out-of-scope edit the work genuinely needs is made and justified with `--scope-reason`, never treated as a reason to stop.

POST-GATE LIFECYCLE. Each child moves to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` item carries concrete pasted evidence. This orchestrator is retired by the runner once both children are `executed` on disk; that retirement SKIPS the pre-transition E/V checkpoint, which is exactly why this plan's own items are orchestration and not work. A human or agent executing by hand verifies V-01 and V-02 and then runs `aw ipd finalize`, never a hand `git mv`. Backlog item `ildjse` was graduated on 2026-10-01 and RETURNED TO `open` on 2026-10-06 when this plan was demoted for an uncovered obligation; its own history says "re-run graduation to complete the handoff". So once this plan is back at `to-review` or later, the graduation must be re-run (`aw backlog set graduated ildjse`), NOT `done`; this Set does not close it.
