# IPD: Make the turn-retry allowlist key on what happened, not on which vocabulary generation wrote the disposition

- Date: 2026-10-02
- Kind: child
- Concern: The turn-retry allowlist admits exactly one token, `failed-safely`, which is a LEGACY alias whose canonical replacement `fail-gate` is non-retryable. Whether a host-failure turn earns its correction budget therefore depends on WHICH PRODUCER wrote the disposition rather than on WHAT HAPPENED, and one reachable producer (`reconcile_disposition`'s nonzero-exit fallback) already writes the non-retryable spelling for a class spec `25kzda` 5.5 names retryable.
- Scope: Give the retry predicate a PRODUCER-DERIVED signal so a host failure is retryable under either spelling while every gate refusal stays refused, and pin the canonicalization hazard with a test. EXCLUDES widening the retryable CLASS SET (no new spec 5.5 class becomes retryable), EXCLUDES changing `TERMINAL_STATES`/`KNOWN_ITEM_STATUSES` membership, and EXCLUDES touching `finalize_retry_decision`.
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_retry_class_mapping.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: superseded
- Readiness: no-go
- From-Spec: 25kzda
- Work-Kind: chore
- Priority: medium
- From-Backlog: vmrhj0
- Set: vmrhj0
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: p47qfu

## Workflow history
- 2026-10-09 superseded (aw set): superseded by ytas91 (fixfirst-04): marks failures where the run learns them
- 2026-10-07 reviewed (aw set): status transition for the /plan-review record below
- 2026-10-07 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REJECT - NEEDS REPLAN; PR-001 (BLOCKER, replan: the F-03 marker producers never reach `turn_failure_is_retryable`, see F-12), PR-002 (HIGH, open: rung-5 side-effect discrimination is a maintainer decision, OQ-02), PR-003 (LOW, fixed: V-02 cross-reference). Review record `.aw/records/reviews/20261002-vmrhj0-01-p47qfu-make-the-turn-retry-allowlist-key-on-what-happened-not-on-wh.review.md`.
- 2026-10-02 same-status (aw set): link the spec this plan amends (check.plan-spec-link-missing)

- 2026-10-02 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `vmrhj0`. Every claim in the Findings table was MEASURED in this lane at HEAD `eebcbef00` by importing the shipped module and driving the real predicates, not transcribed from the item. THE ITEM'S CENTRAL CLAIM REPRODUCED EXACTLY: `TURN_RETRYABLE_DISPOSITIONS == frozenset({'failed-safely'})`, that token aliases to `fail-gate`, it is NOT in `TERMINAL_STATES_CANONICAL`, and `turn_failure_is_retryable({}, 'fail-gate')` is False. The item's `chore` classification is RETAINED and the reasoning is recorded in F-07: the divergence fails CLOSED (a retryable turn is refused a correction, never a gate refusal retried), so no operator receives an unsafe verdict today and no user-perceptible defect exists. THE AUTHORING ALSO FOUND ONE HAZARD THE ITEM DID NOT RECORD, in F-05: `canonical_terminal_status('failed-safely')` already returns `fail-gate` today, so any future caller that canonicalizes a disposition before the retry predicate sees it silently empties the allowlist, which is the migration risk the item predicted arriving through a path the item did not name. The item's proposed remedy (admit `fail-gate`) is MEASURED UNSAFE in F-06 and REJECTED; E-02 adopts a producer-derived signal instead.

## Goal

Make "is this failure retryable?" a question about WHAT HAPPENED rather than about which vocabulary generation spelled the disposition. After this plan, a host failure is retryable whether it was recorded as `failed-safely` or as canonical `fail-gate`, every gate refusal remains non-retryable under both spellings, and a test pins the canonicalization hazard so a later statusvocab migration cannot silently empty the allowlist.

THE GOAL IS A CORRECT DISCRIMINATOR, NOT A WIDER RETRY POLICY. No spec 5.5 class changes its retryable verdict. The never-retry list stays never-retryable, the predicate keeps failing closed on an unclassified token, `finalize_retry_decision` is untouched, and the correction budget's arithmetic is unchanged. The only behavior difference is that a host failure whose disposition was canonicalized now earns the budget spec 5.5 already grants it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: give the predicate a producer-derived signal

- [ ] E-01 In `agent_workflows/runner_shared.py`, introduce a single module-level constant naming the item key that records a HOST FAILURE, and write it at the three producers the audit found (F-03). Add the constant beside the other `TURN_RETRY_*` keys so a reader meets the retry vocabulary in one place, and give it a docstring stating that it is a POSITIVE marker written only by a producer that observed the host itself fail, never by a gate.
  WHY A PRODUCER MARKER AND NOT A WIDER TOKEN SET, which is the whole decision this plan exists to make. The item proposed admitting `fail-gate`, and F-06 measures why that is unsafe: `fail-gate` is written by at least twelve distinct sites in `runner_shared` alone and the overwhelming majority are GATE REFUSALS (clean-base refusal, scope-target refusal, host-capability preflight, spec/backlog transition findings, finalize-unresolvable, integration refusal), a class spec 5.5 lists as never-retryable. A token-level widening cannot tell those from a host failure because they share the token. The PRODUCER can, because the three host-failure producers are a closed, enumerable set.
  THE THREE PRODUCERS, each verified by symbol (F-03): the dispatcher refusal in `runner_shared.refuse_undispatchable_typed_entry` (the arm writing `item["status"] = "failed-safely"` together with `item["driver_error"] = reason`); `oc_runipd`'s `except DriverError` arm (`runnable["status"] = "failed-safely"`, `runnable["driver_error"] = str(exc)`); and `agy_runipd`'s identical `except DriverError` arm. All three ALREADY write `driver_error`, and F-04 measures that `driver_error` is assigned at exactly those three sites and nowhere else, so the marker can be derived from existing evidence rather than invented. PREFER deriving from `driver_error` over adding a fourth write if the executor finds the derivation total; record which was chosen and why.
  DO NOT WRITE THE MARKER AT A GATE. Adding it to a `fail-gate` producer would re-create the exact conflation this plan removes.
  - Depends on: none
  - Expected outcome: a module-level constant exists naming the host-failure marker key; the three producers in F-03 carry it (or it is provably derivable from `driver_error`, which they already carry); no gate-refusal site writes it; `python3 -c "from agent_workflows import runner_shared"` imports clean.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/runner_shared.py`, make `turn_failure_is_retryable` admit a HOST FAILURE under EITHER spelling by consulting E-01's marker, while leaving the token allowlist as the only other admission route. Concretely: after the two existing refusals (deliberate operator stop, refused finalize) and BEFORE the `status not in TURN_RETRYABLE_DISPOSITIONS` branch, admit the item when the marker is present AND the disposition is one of the two spellings a host failure can carry (`failed-safely` or its canonical `fail-gate`). Return a reason string that names the marker as the evidence, so a reader can tell a producer-derived admission from a token-derived one.
  ORDER IS LOAD-BEARING AND MUST NOT BE CHANGED. The deliberate-operator-stop refusal MUST stay first. Its own docstring records that without it a stop reconciles as `failed-safely`, which IS inside the allowlist, and this plan ADDS a second admission route, so a marker check placed above it would newly retry an operator's stop. That is the single most important refusal in the function and this plan must not weaken it. The refused-finalize check must likewise stay above, or the same failure is charged to two counters.
  KEEP THE FAIL-CLOSED TAIL EXACTLY AS IT IS: an unclassified token must still be refused with the "no entry in `TURN_RETRY_CLASSIFICATION`" reason rather than admitted by the new route.
  - Depends on: E-01
  - Expected outcome: `turn_failure_is_retryable({marker: ...}, "fail-gate")` is `(True, <reason naming the marker>)`; `turn_failure_is_retryable({}, "fail-gate")` is still `False` with its existing gate-refusal reason; `turn_failure_is_retryable({marker: ..., "stopped": {"stopped_deliberately": True}}, "fail-gate")` is `False` on the STOP reason; `turn_failure_is_retryable({marker: ..., "finalize_refusal": "X"}, "fail-gate")` is `False` on the FINALIZE reason; and an unknown token is still refused fail-closed.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/runner_shared.py`, record the decision in the source next to `TURN_RETRY_CLASSIFICATION` and `TURN_RETRYABLE_DISPOSITIONS`, because the table's own comment currently tells a reader the set is the whole contract and after E-02 it is not. State three things a future editor needs: that admission now has TWO routes (the derived token allowlist AND E-01's producer marker); that the marker exists because `fail-gate` is written by both host failures and gate refusals so the token alone cannot discriminate (cite the measurement in F-06); and that the `failed-safely` row remains in the table as a LEGACY spelling rather than being retired, because `TURN_RETRY_EXHAUSTED_STATUS`, `FINALIZE_RETRY_EXHAUSTED_STATUS` and `lane_containment.BOUND_EXPIRY_DISPOSITION` all still write that exact token (F-08).
  PRESERVE THE EXISTING ALLOWLIST-NOT-DENYLIST PROSE. Those paragraphs are load-bearing and were deliberately carried onto the derivation by plan `4gx141` E-01; this item ADDS to them and must not replace them.
  - Depends on: E-02
  - Expected outcome: the comment block above the derivation documents both admission routes, the discriminator's reason, and why the legacy row stays; the pre-existing allowlist-not-denylist and `partial` rationales are still present in the file.
  - Execution state: pending

### Task group 2: pin the behavior and the hazard

- [ ] E-04 In `tests/test_retry_class_mapping.py`, add tests that drive the real predicate (no `inspect`, no source reading, no symbol census) covering: (a) a host failure carrying E-01's marker is retryable under BOTH `failed-safely` and `fail-gate`; (b) a bare `fail-gate` with no marker is still refused, asserting on the returned REASON so a future change that admits it wholesale fails here; (c) the stop and finalize refusals still outrank the marker; (d) THE CANONICALIZATION HAZARD from F-05, asserting that a host failure whose disposition has been passed through `canonical_terminal_status` is still retryable, which is the property that makes a later statusvocab migration safe and the one no existing test covers; and (e) the existing derivation, coverage and table-agreement invariants still hold.
  THE NEGATIVE HALF MUST BE DEMONSTRATED, NOT ASSERTED. A test that has never been seen to fail is not known to test anything, so V-04 requires the executor to run (d) against the UNMODIFIED predicate first and paste the failure before E-02 lands.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_retry_class_mapping.py -o addopts=""` passes with the new cases present; case (d) is demonstrated red against the pre-E-02 predicate and green after; no added test reads production source text.
  - Execution state: pending

- [ ] E-05 AMEND spec `25kzda` 5.5's mapping table so it states the discriminator rather than only the token. The table's two host-failure rows currently read `failed-safely` in their Disposition column, which is the legacy spelling this plan stops relying on; update those two rows to name BOTH spellings and the producer marker that discriminates them, and leave every never-retryable row's verdict untouched. Record the amendment with `aw specs note` on the same file.
  THE SPEC'S `- Status:` STAYS `approved`. This is an ADDRESSING change: it changes no class's membership in either list, no budget, no bound, and no requirement. It makes the existing mapping precise about which token its host-failure rows mean, which is the question plan `4gx141` E-04 deliberately surfaced and recorded as OQ-01 for this plan to answer.
  - Depends on: E-02
  - Expected outcome: 5.5's two host-failure rows name both spellings and the marker; every never-retryable row is byte-identical in verdict; the spec's `- Status:` is still `approved`; `aw specs check` conforms; the amendment is recorded in the spec's workflow history.
  - Execution state: pending

## Project conventions discovered (Step 0)

- A SPEC-GOVERNED CONTRACT. `agent_workflows/runner_shared.py` declares `TURN_RETRY_CLASSIFICATION` as the one data table backing the retry verdict, and its own comment says "it is data rather than prose so a test can assert on it". Changes belong in the table or in a documented second route, never in a scattered judgement at a call site.
- `TURN_RETRYABLE_DISPOSITIONS` IS DERIVED, NOT MAINTAINED. Plan `4gx141` E-01 replaced the literal with a comprehension over the table, and the shipped comment instructs: "Change the table row rather than editing this set." This plan honors that by adding a second ADMISSION ROUTE in the predicate rather than hand-editing the frozenset.
- CLOSED STATUS VOCABULARIES. `runner_shutdown.KNOWN_ITEM_STATUSES` is closed and `runner_shutdown.observe_ledger` declares a run INCOHERENT on any status outside it, which is why `TURN_RETRY_EXHAUSTED_STATUS` reuses an existing token rather than inventing one. This plan invents no status.
- TEST OUTCOMES, NOT CODE STRUCTURE. Per `GUIDING_PRINCIPLES` P16 and the repository agent contract, the added tests must drive the predicate and assert on returned verdicts and reasons, never read production source with `inspect`/`ast`/regex.
- RUN THE SUITE BARE. `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`; use `-o addopts=""` only when per-test counts are genuinely needed.

## Findings

Every row was measured in this lane at HEAD `eebcbef00` by importing the shipped module, not transcribed from the backlog item.

| Id | Finding | Evidence |
| :--- | :--- | :--- |
| F-01 | The allowlist has exactly ONE member and it is a LEGACY token. | `TURN_RETRYABLE_DISPOSITIONS == frozenset({'failed-safely'})`; `TERMINAL_STATUS_ALIASES['failed-safely'] == 'fail-gate'`; `'failed-safely' in TERMINAL_STATES_CANONICAL` is `False`. Reproduces the item exactly. |
| F-02 | Its canonical replacement is NON-retryable, so the verdict depends on the spelling. | `turn_failure_is_retryable({}, 'fail-gate')` returns `(False, "... lifecycle gate or clean-base gate refused; not a host failure to retry without human action")`, while `turn_failure_is_retryable({}, 'failed-safely')` returns `(True, "... in spec 5.5's retryable host-failure class")`. |
| F-03 | The host-failure producers are a CLOSED set of three, and all three write `driver_error`. | `runner_shared.refuse_undispatchable_typed_entry` (`item["status"] = "failed-safely"` with `item["driver_error"] = reason`); `oc_runipd`'s `except DriverError` arm (`runnable["status"] = "failed-safely"`); `agy_runipd`'s identical arm. A fourth writer of the token, `lane_containment.BOUND_EXPIRY_DISPOSITION`, is consumed only inside that module and reaches no queue item (its sole use is a `"disposition"` field in a local record). |
| F-04 | `driver_error` is assigned at EXACTLY those three sites and nowhere else, so the marker is derivable from shipped evidence. | A repo-wide search for assignment to `["driver_error"]` across `agent_workflows/` returns three hits: `runner_shared.py`, `oc_runipd.py`, `agy_runipd.py`, each the site named in F-03. |
| F-05 | THE HAZARD THE ITEM PREDICTED IS ALREADY REACHABLE TODAY, by a path the item did not name. | `canonical_terminal_status('failed-safely')` returns `'fail-gate'`, and feeding that result back gives `turn_failure_is_retryable({}, 'fail-gate') == (False, ...)`. Any caller that canonicalizes before classifying therefore empties the allowlist silently. No existing test covers this composition. |
| F-06 | ADMITTING `fail-gate` WHOLESALE (the item's own proposed fix) IS MEASURABLY UNSAFE. | `fail-gate` is written at twelve-plus distinct sites in `runner_shared.py` alone, and the audited ones are gate refusals: `clean_base_refused`, `scope_target_refused`, `host_capability_unavailable` preflight, spec-transition findings, `[BACKLOG-GRADUATE-LEGITIMACY]`, backlog setter failure, rollback containment, production-integration refusal, and `FINALIZE_PLAN_UNRESOLVABLE_CODE`. Spec 5.5 lists human approval gate, unauthorized status change, hook bypass and out-of-scope mutation as never-retryable, and all map to `fail-gate` in the spec's own table. |
| F-07 | The gap fails CLOSED, which is why `chore` is correct and no release gate is warranted. | In every divergence the retryable item is REFUSED a correction (`fail-gate` -> not retryable); the reverse (a gate refusal being retried) does not occur, because gate sites carry no host-failure marker. No wrong-but-plausible retry can be produced, and the user-perceptible-impact test in `AGENTS.md` is not met: nothing a user waits on is slower and no output is wrong. |
| F-08 | The legacy row cannot simply be RETIRED from the table, because three live constants still write that exact token. | `TURN_RETRY_EXHAUSTED_STATUS == 'failed-safely'`, `FINALIZE_RETRY_EXHAUSTED_STATUS == 'failed-safely'`, `lane_containment.BOUND_EXPIRY_DISPOSITION == 'failed-safely'`. The first is documented as a deliberate reuse because `KNOWN_ITEM_STATUSES` is closed. |
| F-09 | The retry machinery is LIVE-WIRED, so this is a real code path and not a dormant surface. | `handle_turn_failure_retry` is called from `runner_shared.execute_item_core` and re-exported by both hosts; `turn_retry_decision` -> `turn_failure_is_retryable` is reached from it; and the call site's comment states it is placed deliberately before the unconditional `item["status"] = disposition` line. |
| F-10 | `reconcile_disposition`'s nonzero-exit fallback is the reachable producer of the NON-retryable spelling for a host-failure class. | Its documented rung 5 ends `return ("fail-verify" if exit_code == 0 else "fail-gate")`, and the main execute path calls it (`disposition, outcome = reconcile_disposition(repo, item, run_dir, exit_code, plan_repo=...)`) with that disposition flowing into `handle_turn_failure_retry`. Spec 5.5 names "host nonzero exit that did not create an ambiguous side effect" retryable. |
| F-12 | (REVIEW, 2026-10-07, HEAD `0b09c3347`) NONE OF THE THREE F-03 PRODUCERS EVER REACHES `turn_failure_is_retryable`, so E-01/E-02's marker route is DEAD WIRING and the reachable case in the Concern (F-10) carries no marker. | The predicate's ONLY production caller chain is `execute_item_core` -> `handle_turn_failure_retry` -> `turn_retry_decision` -> `turn_failure_is_retryable` (the sole `handle_turn_failure_retry(` call is inside `execute_item_core`, after `reconcile_disposition`). (1) `refuse_undispatchable_typed_entry` runs in `oc_runipd.run_queue`/`agy_runipd.run_queue` BEFORE `execute_item` and the caller `continue`s on True, so the item is never executed. (2) Both hosts' `except DriverError as exc:` arms (`runnable["driver_error"] = str(exc)`) run AFTER `execute_item` has RAISED out of `execute_item_core`, i.e. after the retry site was skipped. (3) No disposition assignment inside `execute_item_core` writes `failed-safely`; the only one that reaches the predicate is `handle_finalize_refusal`'s `FINALIZE_RETRY_EXHAUSTED_STATUS`, which carries `finalize_refusal` and is refused by the predicate's second guard. Measured: `reconcile_disposition(repo, {id6, configured_file:'nope.ipd.md', action:'execute'}, run_dir, 1)` returns `fail-gate`, and `turn_failure_is_retryable` on that item returns `(False, "... lifecycle gate or clean-base gate refused ...")`; the item has no `driver_error`, so the post-E-02 predicate returns the same. |
| F-11 | Budget exhaustion writing a retryable token does NOT loop, so this plan need not change the arithmetic. | `turn_retry_decision` compares `turn_retry_attempts(item)` against `frozen_retry_budget(state)` and the performer increments the counter before saving state, so "total dispatches for one item can never exceed `budget + 1`" holds even though `TURN_RETRY_EXHAUSTED_STATUS` is itself in the allowlist. |

## Proposed changes (ordered, validatable)

1. Add a host-failure marker constant and ensure the three F-03 producers carry it, preferring derivation from the `driver_error` they already write (E-01).
2. Add a second admission route to `turn_failure_is_retryable` keyed on that marker, strictly BELOW the stop and finalize refusals (E-02).
3. Record the two-route contract, the discriminator's justification, and why the legacy row stays, beside the classification table (E-03).
4. Pin the new behavior and the canonicalization hazard with outcome-driving tests, demonstrating the hazard case red first (E-04).
5. Amend spec 5.5's two host-failure rows to name both spellings and the marker, leaving every never-retryable verdict untouched (E-05).

## Deferred / out of scope (with reason)

- RETIRING the `failed-safely` token from the codebase in favor of `fail-gate` everywhere. F-08 measures three live constants writing it and `KNOWN_ITEM_STATUSES` is a closed vocabulary whose membership `observe_ledger` enforces, so a token migration has blast radius far beyond retry and is a separate, larger change.
  - Carrier-Declined: NO DEFECT EXISTS HERE. The legacy token is correctly handled by the alias map and by this plan's discriminator; this row records a deliberate blast-radius fence, not a deferred repair.
- UNIFYING the two classification surfaces (`turn_failure_is_retryable` and `finalize_retry_decision`) onto one evidence shape. Plan `4gx141`'s Under-scope section already recorded why they differ by design: a finished TURN has a disposition and no findings, while a refused FINALIZE has findings and no distinct disposition. Unifying them is a design change beyond this plan's question.
  - Carrier-Declined: NO DEFECT EXISTS HERE. The seam is declared and intentional in the spec after `4gx141` E-04; this plan keeps it.
- WIDENING any never-retryable spec 5.5 class. Explicitly refused: F-06 measures that the never-retry classes map onto `fail-gate` and a token-level widening would retry them. This plan's whole purpose is to admit host failures WITHOUT admitting that class.
  - Carrier-Declined: NO DEFECT EXISTS HERE. The never-retry list is correct as specified; preserving it is a requirement of this plan, not a deferral.
- `lane_containment.BOUND_EXPIRY_DISPOSITION`'s token. F-03 measures it is consumed only within its own module and never reaches a queue item's status, so it cannot reach the retry predicate and needs no marker.
  - Carrier-Declined: NO DEFECT EXISTS HERE. The constant is correct for its local record; it is simply out of this predicate's path.

## Scope check

- Over-scope: none. Each E-item serves the one question "is this failure retryable, and does the answer depend on what happened rather than on who spelled it?". Three candidate paths were checked and need NO change: `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`, because both re-export the retry symbols by `from ... import X as X` and this plan changes no symbol's name, type or module position (if E-01 concludes a fourth explicit marker write is needed at their `DriverError` arms rather than deriving from `driver_error`, those two paths MUST be added to `- Scope-Paths:` with a recorded `--scope-reason` at finalize); and `agent_workflows/runner_shutdown.py`, because this plan adds no status to the closed vocabulary.
- Under-scope: the plan does NOT re-verify each never-retryable class's individual consumer, and does not audit every one of the twelve-plus `fail-gate` write sites exhaustively; F-06 audits enough of them to establish that gate refusals dominate the token, which is all the design decision turns on. It also does not change the correction budget's arithmetic (F-11 measures it is already bounded).

## Required tests / validation

- Bare `python3 -m pytest` (the repository contract; `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`, so do not add flags). RE-ESTABLISH THE BASELINE IN YOUR OWN LANE BEFORE ANY EDIT and paste it; do NOT compare against the figure below, which will have expired. Authoring measured `3 failed, 4624 passed, 2 skipped` at HEAD `eebcbef00` with a clean `git status`, i.e. BEFORE any edit. THE THREE FAILURES ARE PRE-EXISTING AND ARE NOT THIS PLAN'S: `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`, `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, and `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`. None references `turn_failure_is_retryable` or any `TURN_RETRY` symbol (verified by search). If any is still red at execution, record it as pre-existing by reproducing it at the baseline commit BEFORE any edit; do not fix them here and do not let them mask a real regression. NOTE the third asserts a whole-corpus property over `.aw/records/specs/` and E-05 EDITS a spec, so it must be re-checked after E-05 specifically.
- `python3 -m pytest tests/test_retry_class_mapping.py -o addopts=""` for the new file's per-test counts.
- The canonicalization hazard (E-04 case (d)) must be demonstrated RED against the unmodified predicate before E-02 lands, and GREEN after; paste both.
- `aw specs check` on the amended spec, and `aw check` for the release-gate and artifact rules.
- `aw ipd lint --phase pre-transition` must conform before any terminal transition.

## Spec / documentation sync

- THIS PLAN AMENDS AN APPROVED SPEC, DECLARED IN `- Scope-Paths:`: `.aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md`. WHY, since a spec edit changes the contract every other plan is reviewed against: 5.5's mapping table currently names `failed-safely` as the disposition for both of its host-failure rows, and that is precisely the legacy spelling whose reliability this plan removes. Leaving the table unamended would make the shipped code and the spec disagree the moment E-02 lands, and would leave the next reader to re-derive which token the host-failure rows mean, which is the defect plan `4gx141` created the table to end and recorded as OQ-01 for this plan to answer.
- The amendment is an ADDRESSING change: it makes two existing rows precise and adds the discriminator. It changes no requirement, no budget, no bound, and no class's membership in either the retryable or the never-retryable list. The spec's `- Status:` therefore stays `approved` and E-05 records the amendment with `aw specs note` into the same declared file.

## Open questions

### OQ-01: Should the host-failure marker be derived from the existing `driver_error` key or written as a new explicit key?

- Blocking: no
- Status: open
- Owner: executor
- Resolution or deferral rationale: NON-BLOCKING because both options satisfy every E-item and V-item; the choice is an implementation detail the executor settles from evidence, and E-01 instructs it to record which it chose and why. The evidence favors DERIVATION: F-04 measures that `driver_error` is assigned at exactly the three host-failure producers in F-03 and nowhere else, so the signal already exists and a fourth write would be redundant. The reason it is not simply decided here is that `driver_error` is also READ as a legacy diagnostics key for three specific statuses (noted in `handle_turn_failure_retry`'s comment about the diagnostics block), so an executor may find a semantic collision that argues for a dedicated key. Either way the predicate's contract in E-02 is identical, which is why this does not block review.
- REVIEW NOTE 2026-10-07: superseded in substance by OQ-02. F-12 measures that neither option reaches the predicate, so this choice is moot until OQ-02 is answered.

### OQ-02: Which turn outcomes should count as a retryable host failure, and where does the evidence for that come from?

- Blocking: yes
- Finding: PR-002
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: RAISED BY /plan-review 2026-10-07 (verdict REJECT - NEEDS REPLAN). F-12 measures that the plan's marker producers (`driver_error` writers) never meet `turn_failure_is_retryable`, so E-01/E-02 as written would pass their unit tests and change nothing in a real run, while the one reachable case the Concern names, `reconcile_disposition`'s rung-5 nonzero-exit fallback (`fail-gate` with no outcome file), stays non-retryable. A sound replan has to set a marker AT THE POINT THE RUN LEARNS THE HOST FAILED INSIDE `execute_item_core`, most plausibly rung 5 of `reconcile_disposition` when `exit_code != 0`, and possibly a spawn failure from `spawn_executor`. The decision that is the maintainer's: spec 5.5 limits the retryable class to a nonzero exit "that did not create an ambiguous side effect", and rung 5 cannot tell a clean crash from an agent that changed files or ran gates before it exited nonzero. Options: (a) retry rung-5 nonzero exits only when the lane worktree shows no commits and no dirty paths since the turn began; (b) retry every rung-5 nonzero exit, because the correction turn resumes the isolated lane anyway; (c) keep today's fail-closed behavior and narrow this plan to a spec-table and comment fix plus the canonicalization pin. (a) and (b) newly spend paid correction turns on failures that are refused today, which is a risk-appetite call. Answer this, then re-author E-01, E-02, V-01, V-02, F-03, F-04, F-07 and the Scope check to match, and re-review.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste a Python session importing `agent_workflows.runner_shared` that prints the new marker constant's name and value, plus the output of a search for assignments to the marker key across `agent_workflows/` showing hits ONLY at the three F-03 producers (or, if derivation was chosen, showing the three `driver_error` sites and the predicate's read of them). Paste the recorded decision text for OQ-01. The evidence must show NO gate-refusal site writing the marker.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste a Python session driving the real predicate and printing all five verdicts named in E-02's expected outcome: marker + `fail-gate` -> True with a reason naming the marker; bare `fail-gate` -> False with the gate reason; marker + deliberate stop -> False on the STOP reason; marker + `finalize_refusal` -> False on the FINALIZE reason; and an unknown token -> False on the fail-closed "no entry" reason.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the comment block as it stands after the edit, showing it documents both admission routes, cites F-06's reason for the discriminator, and explains why the legacy row stays. In the same paste, show the pre-existing allowlist-not-denylist and `partial` paragraphs are still present.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste (a) the FAILING run of the canonicalization-hazard case against the unmodified predicate, including the assertion message, and (b) the PASSING run of `python3 -m pytest tests/test_retry_class_mapping.py -o addopts=""` after E-02, with per-test counts. Also paste the full bare `python3 -m pytest` summary line and confirm the only failures are the three pre-existing ones recorded in Required tests (or that they are gone).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the diff of spec 5.5's mapping table showing the two host-failure rows amended and every never-retryable row's Retryable column unchanged; paste the spec's `- Status:` line showing `approved`; paste the `aw specs check` output; paste the new workflow-history line written by `aw specs note`; and paste a re-run of `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms` showing the spec edit did not change that test's pre-existing status.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and carries NO `- Readiness:` field, because that field is an output of `/plan-review` and writing it here would forge an attestation no review performed. It requires explicit human approval before execution.

EXECUTION CONTRACT. The executor commits only the paths named in `- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never `--no-verify`, and does not push. Tests are run bare per the repository contract and the ACTUAL output is pasted into each `V-*` Observed evidence block; no validation may be marked `pass` from the matching execution checkmark. E-01 and E-02 MUST land together or with E-02's predicate change last: E-01 alone is inert (it only writes a marker nobody reads), which is the safe intermediate, but no commit may leave E-02's second admission route present while the marker is unwritten.

POST-GATE LIFECYCLE. After every `V-*` is `pass` with concrete pasted evidence and `aw ipd lint --phase pre-transition` conforms, the plan moves to `.aw/records/plans/executed/` through the tooled transition. Backlog item `vmrhj0` is set `graduated` (never `done`) by the runner on verification; the executor does not hand-edit its status.
