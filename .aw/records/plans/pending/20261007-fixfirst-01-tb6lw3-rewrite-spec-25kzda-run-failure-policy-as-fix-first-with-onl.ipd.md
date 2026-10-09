# IPD: Rewrite spec 25kzda run failure policy as fix first, with only a corrupt ledger aborting a run

- Date: 2026-10-07
- Kind: child
- Concern: Spec `25kzda` tells the runner to give up on exactly the failures an agent fixes best. Section 5.5 lists push, hook bypass, unauthorized status change and out-of-scope mutation as "must never retry"; Section 5.7 says a hook refusal fails the item, a host failure retries "only when no ambiguous side effect exists", and push and hook bypass abort the run; Section 4.1 enumerates six run-abort classes. The maintainer ruled on 2026-10-07 that this is backwards for an isolated-worktree runner: aborting cannot undo a push, a hook bypass or a hand status edit lives only in the lane and is caught again at merge, and "ambiguous side effect" is not testable. The code already disagrees with the spec in both directions (F-03).
- Scope: Amend spec `25kzda` Sections 4.1, 4.2 (action and message cells), 5.5 and 5.7 to a fix-first policy, reconcile every other sentence of the spec that names the old six-class abort set, and update the `run_evidence` finding-code transcription the spec pins (`run_evidence.ABORT_CLASSES`, every affected `RunFindingCode` `action`/`abort`/`abort_classes`/`message` field, and the validator wording that says "six") so the byte-equality tests stay green. EXCLUDES all runner behavior changes (Orders 02 to 07), and EXCLUDES changing the retry budget's bound, default or precedence.
- Scope-Paths: .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md, agent_workflows/run_evidence.py, tests/test_run_finding_abort_partition.py, tests/test_run_finding_spec_transcription.py, tests/test_host_capability_extension.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: coivul
- From-Spec: 25kzda
- Blocks-Release: f33nrj
- Set: fixfirst
- Order: 1
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tb6lw3
- Approval: 2026-10-09, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-09 approved (aw set): status set to approved
- 2026-10-09 readiness re-check (agent (aw ipd recheck-readiness)): `- Readiness:` CHANGED `no-go` -> `go-pending-approval`. THIS IS A RE-CHECK, NOT A REVIEW: no finding was re-derived and no plan content was re-critiqued. The three `no-go` conditions were RECOMPUTED with the shipped predicates and each was found clear: unresolved-blocking-question -> clear (no unresolved BLOCKING open question; `has_unresolved_blocking_question` -> False (a NON-blocking open question is deliberately not counted, per the maintainer's 2026-09-10 ruling on qhy3i3 OQ-01)); unresolved-gating-finding -> clear (no unresolved gating finding; `review_findings.subject_gating_blocks` -> empty (an ABSENT review artifact is silent by that predicate's documented contract)); negative-review-verdict -> clear (the newest review record's verdict is not negative; `newest_verdict` -> neutral). RE-CHECKED REVIEW: the review of 2026-10-08, findings OQ-02. Recomputed at HEAD `1a6164cce`. HUMAN APPROVAL IS STILL REQUIRED AND WAS NOT GIVEN: `go-pending-approval` means the plan awaits sign-off, and nothing here approves it or clears it to execute. Only a review may set `go`.
- 2026-10-08 reviewed (aw set): plan-review round 1: REVIEWED - OPEN QUESTIONS (OQ-02 blocking)
- 2026-10-08 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-010. Nine fixed in place: 4.2 action/message cells and `abort_classes` now covered (new E-06; without it the shipped table fails `validate_finding_table` RC-ABORT-CLASS), the rest of the spec swept for the six-class set (new E-07), group (b) completed (changed frozen requirements with the 5.5a carve-out, unknown commit outcome), 4.1 containment/reclassification rerouted, Scope-Paths corrected (+`tests/test_host_capability_extension.py`, -`tests/test_retry_class_mapping.py`), partition tests retargeted, V-items strengthened, execution contract added. PR-003 OPEN as blocking OQ-02: shipped code aborts a run on a nested-tool identity mismatch (`ToolIdentityError`), which the 'only a corrupt ledger aborts' ruling does not address. Review record `.aw/records/reviews/20261007-fixfirst-01-tb6lw3-rewrite-spec-25kzda-run-failure-policy-as-fix-first-with-onl.review.md`.
- 2026-10-07 to-review (aw set): authored review-ready from backlog coivul (maintainer rulings 2026-10-07)

- 2026-10-07 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

The spec says what the maintainer wants: when the agent caused the failure, tell it what went wrong and let it fix it; stop one item only when a human or the runner itself must act; abort a run only when the runner cannot trust its own ledger.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: amend the spec

- [ ] E-01 Rewrite Section 5.5's two retry lists as three groups, in this order and with these members:
  (a) FIX-IT (agent-caused; a bounded correction turn naming what failed): host spawn failure; nonzero exit or no outcome file; stall or turn-limit expiry; missing expected artifact or failed deterministic check; missing or stale validation evidence; verifier transport failure; a hook refusal of any commit; a red combined suite after merge; an out-of-scope change (revert or justify); an unauthorized status change or plan move (undo, use the setter); a hook-bypass commit (undo, recommit through the hooks); a push (recorded, the agent is told, the run continues; detection is unbuilt and owned by Set `denypush`, so say so in the same bullet).
  (b) STOP THIS ITEM, NO FIX-IT TURN (a human or the runner must act; independent items continue): missing human approval; an agent proposal that a gate, tool or approach must change (Order 02); ownership or lease conflict; unknown commit or transaction outcome; unknown or non-idempotent external outcome; identity or type ambiguity; changed frozen requirements, EXCEPT an additive scope widening as defined in Section 5.5a (keep that carve-out and its cross-reference unchanged); fix-it budget exhausted.
  (c) ABORT THE RUN: corrupt run ledger only.
  DELETE the phrase "that did not create an ambiguous side effect" and do not replace it with another untestable qualifier.
  STATE THE ONE RULE FOR (a): the fix-it message tells the agent to fix the cause and not the gate, and that a gate or tool change is acceptable only when it is small and clearly a bug, with the reason recorded; otherwise the agent proposes it (Order 02, Order 03).
  RECONCILE THE PROSE AROUND THE LISTS in the same edit: rewrite "An out-of-scope mutation therefore fails and contains the item on the first occurrence even if ten retries remain" to the revert-or-justify fix-it turn, and keep the Set-level production refusal paragraph pointing at a class name that still exists in group (a) (it quotes "failed deterministic check for which a bounded correction is safe"; either keep that wording in group (a) or update the quote, but the two must match).
  - Depends on: none
  - Expected outcome: Section 5.5 carries the three groups with exactly these members, no "ambiguous side effect" wording remains anywhere in the spec, the surrounding prose agrees with the groups, and the retry budget paragraph (bound 0 to 10, default 2, three-tier precedence) is byte-identical, so `tests/test_retry_budget_citation.py` still locates its anchor sentence in Section 5.5.
  - Execution state: pending

- [ ] E-02 Rewrite the Section 5.5 disposition mapping table so each fix-it class names the evidence the runner keys on (a disposition plus a marker, a finalize finding, an integration refusal kind) rather than the single token `failed-safely`, and so no row says a class is retryable through a path that cannot reach it (F-02). Mark each row with the Order in this Set that implements it, and mark a row whose evidence is not produced by any child (push) "unbuilt" with its carrier (`oq05nc`). Every group (b) and (c) member keeps a row.
  - Depends on: E-01
  - Expected outcome: every fix-it row names its evidence and its implementing Order (or "unbuilt" plus carrier); the never-retry rows for push, hook bypass, unauthorized status change and out-of-scope mutation are gone; the table has one row per member of groups (a) to (c).
  - Execution state: pending

- [ ] E-03 Rewrite Section 5.7's response column to match E-01: hook refusal, out-of-scope mutation, unauthorized status change, hook-bypass attempt and host/transport failure become "Fix-it turn naming what failed" (push attempt: "Record, tell the agent, continue"); concurrent overlap and unknown external outcome become "Stop item; continue independent items"; corrupt ledger stays "Abort run". Rewrite Section 4.1's "Exhaustive `ABORT RUN` set" to the single class "Corrupt run ledger" (plus whatever OQ-02 decides), rewrite the `ABORT RUN` failure-action definition above it (it says "one of the six explicitly enumerated ... classes"), and move the other classes' rationale into a "Stop this item" paragraph. Rewrite the "reclassified" sentence and the containment transaction's step 6 and closing paragraph so they reclassify to a STOP-ITEM class (ownership conflict, unknown outcome) rather than to a run abort.
  - Depends on: E-01
  - Expected outcome: Section 5.7 and 4.1 agree with 5.5 group (c): the abort set has one member (or the OQ-02 answer), and no 4.1 sentence still routes an item-local fault to a run abort.
  - Execution state: pending

- [ ] E-06 Rewrite the Section 4.2 `RUN-*` action cells, and the message cells that promise a contrary response, to the amended policy, using exactly the 4.1 action vocabulary and these targets: group (a) -> `RETRY ...`, group (b) -> `FAIL ITEM ...`, group (c) -> `ABORT RUN`. Concretely: `RUN-FROZEN-IDENTITY` and `RUN-COMMIT-CONTENTS` drop their `ABORT RUN only ...` segment (identity ambiguity and ownership conflict are group (b)); `RUN-BASELINE-OWNERSHIP`'s `ABORT RUN` becomes a FAIL ITEM that continues independent items; `RUN-CROSS-TREE` drops its `ABORT RUN only ...` segment; `RUN-COMMIT-GATEWAY` becomes a RETRY (undo and recommit through the hooks) then FAIL ITEM after containment; `RUN-HOST-ATTEMPT` moves timeout/stall from FAIL ITEM to RETRY, keeping cancellation and exhausted budget as FAIL ITEM; `RUN-SCOPE-DELTA` becomes a revert-or-justify RETRY then FAIL ITEM after containment, and its message stops saying the changes "were quarantined and restored to baseline" before any fix-it turn; `RUN-LEDGER-INTEGRITY` stays `ABORT RUN`. Keep every cell terse and keep each message beginning `[<CODE>]` and ending in an `aw` recovery command (validator rules `RC-MESSAGE`, `RC-RECOVERY`). Keep the table at twelve codes (`RC-COUNT`). Update the `RUN-NO-PUSH` retirement prose's sentence "Section 4.1's `Push attempt` abort class is left in place" to say the class was removed by this amendment.
  - Depends on: E-03
  - Expected outcome: after this edit `run_evidence.derive_abort_from_action` over each spec action cell returns `always` for `RUN-LEDGER-INTEGRITY` only and `never` for the other eleven.
  - Execution state: pending

- [ ] E-07 Sweep every OTHER sentence of the spec that names the old six-class set or routes a fault to a run abort, and reconcile each to the amended policy or delete it. At authoring these were: Section 1.4 row A1 ("restricted to six explicitly enumerated ... classes"; "An out-of-scope mutation fails and quarantines only that item"); Section 2.1 ("a hook-bypass attempt is one of the six `ABORT RUN` classes"); Section 2.10 ("`fatal` here maps to the allowed run-wide identity/type ambiguity class": restate as a REFUSE RUN before any session, per decision D-2); Section 5.2 guarantee row 1 ("no shipped finding code names Section 4.1's `Push attempt` abort class") and the paragraph after the table ("the enumerated ownership-conflict abort class"); Section 5.3 step 9 ("marks the appropriate enumerated abort class and stops"); Section 5.4 step 1 ("identity/type ambiguity aborts the run"); Section 5.6 exit row 4 ("One of the six enumerated run-wide classes: ..."). RE-DERIVE the list at execution rather than trusting this one: `grep -n -i "abort\|six\|enumerated" <spec>`, and dispose of every hit. Leave the dated history of earlier amendments untouched.
  - Depends on: E-03, E-06
  - Expected outcome: every remaining hit of that grep is either the single corrupt-ledger class, a REFUSE RUN before any session, the OQ-02 answer, an unrelated use of the word (merge abort, draft "never an abort", operator stop), or a dated historical line, and each is listed with its disposition in V-07.
  - Execution state: pending

- [ ] E-04 Record the amendment with `aw specs note` on the same file, naming the maintainer ruling of 2026-10-07, the OQ-02 answer, and this plan's id6. Do NOT run `aw specs set`; the spec stays `approved`.
  - Depends on: E-02, E-03, E-06, E-07
  - Expected outcome: one new dated workflow-history line; `- Status: approved` unchanged; `aw specs check` conforms.
  - Execution state: pending

### Task group 2: keep the pinned transcription true

- [ ] E-05 Update `agent_workflows/run_evidence.py` so the shipped table matches the amended spec and still validates: `ABORT_CLASSES` holds only "Corrupt run ledger" (plus the OQ-02 answer); every `RunFindingCode` row changed by E-06 carries the amended `action` and `message` byte for byte, a stored `abort` equal to `derive_abort_from_action(action)`, and `abort_classes=()` for every row that no longer aborts (required by `validate_finding_table`'s `RC-ABORT-CLASS` rules: a never-aborting row may name no class, and every named class must be in `ABORT_CLASSES`). Update the module's prose that states the old set or its size (the `ABORT_CLASSES` comment, the abort-semantics comment block, `validate_finding_table`'s "six" messages, `aggregate_run_exit`'s "not one of spec 4.1's six" reason, the `AGGREGATE_RUN_WIDE` comment). Do NOT change `aggregate_run_exit`'s exit mapping or `NON_MASKABLE_CLASSES` (the run-wide class stays non-maskable; only its membership shrinks). Update tests only where they assert the old set or old cells, keeping them behavior tests over the shipped table: `tests/test_run_finding_abort_partition.py` (its perturbation tests pick `RUN-FROZEN-IDENTITY` and `RUN-CROSS-TREE` BECAUSE they are conditional; after E-06 no row is conditional, so retarget each to a row and perturbation that still proves the same property, e.g. perturb `RUN-LEDGER-INTEGRITY` from always to never), `tests/test_run_finding_spec_transcription.py` (only if a message cell it pins changed), and `tests/test_host_capability_extension.py` `GuaranteeRowEnforcementStatusTests.test_row_1_push_denial_enforcement_status` (it asserts `"Push attempt"` IS in `ABORT_CLASSES`; invert to assert it is absent and that no row names it).
  - Depends on: E-06
  - Expected outcome: `run_evidence.validate_finding_table().ok` is True; the four named test modules pass; no runner behavior changed (`git diff --name-only` lists no file outside Scope-Paths, and no file under `agent_workflows/` other than `run_evidence.py`).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- Spec 5.5 declares itself "the single normative home" for the retry budget; this plan changes the CLASSES, not the budget.
- `tests/test_run_finding_spec_transcription.py` asserts byte equality between spec Section 4.2 cells and `run_evidence.RUN_FINDING_CODES`, so editing a cell is a code change and both must move together.
- A spec edit is declared in `- Scope-Paths:` so both runners announce it before the run (AGENTS.md).
- `tests/test_run_finding_abort_partition.py` asserts the Section 4.2 ACTION cells byte for byte against `RunFindingCode.action`, and that each row's stored `abort` equals `run_evidence.derive_abort_from_action` over the spec cell; `run_evidence.validate_finding_table` (`RC-ABORT-CLASS`) refuses a never-aborting row that names an abort class and an aborting row that names none. So changing an action cell moves `action`, `abort` and `abort_classes` together.
- `tests/test_retry_budget_citation.py` locates the Section 5.5 budget sentence by content and derives its `###` heading; the budget paragraph and the 5.5 heading must survive the rewrite.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Section 5.5 lists out-of-scope mutation, unauthorized status change, hook bypass and push on the never-retry list; Section 5.7 says push and hook bypass abort the run, hook refusal fails the item, and host failure retries only "when no ambiguous side effect exists". | Spec `25kzda` Section 5.5 "It must never retry these classes regardless of budget"; Section 5.7 rows `hook_refused`, `hook_bypass_attempt`, `push_attempt`, `host_failure`. |
| F-02 | The 5.5 mapping table says host spawn failure and host nonzero exit are retryable through `turn_failure_is_retryable` on `failed-safely`, but no production path delivers that token to the predicate. | `runner_shared.TURN_RETRY_CLASSIFICATION`; `reconcile_disposition` rung 5 returns `fail-gate`; `oc_runipd` `except DriverError` sets `failed-safely` after `execute_item_core` has already returned (plan `p47qfu` F-12). |
| F-03 | The code disagrees with the spec in both directions: none of the six abort classes aborts a run; push, hook bypass and untooled status changes are not detected; out-of-scope edits are auto-justified and integrated. | `run_evidence.ABORT_CLASSES` is read only to validate the finding table; `runner_shared.compute_scope_reconciliation` writes "changed by the plan's approved execution (auto-reconciled by ...)" for every out-of-scope path; `RUN-COMMIT-GATEWAY` is `UNBOUND_BY_DEPENDENCY`. |
| F-04 | Section 4.1 makes the six classes "exhaustive" for aborting the whole queue, and `run_evidence.ABORT_CLASSES` transcribes them verbatim. | Spec Section 4.1 "Exhaustive `ABORT RUN` set"; `run_evidence.ABORT_CLASSES` docstring "Spec 4.1's EXHAUSTIVE abort-class set, verbatim". |
| F-06 | (review PR-001) The abort set is also encoded in Section 4.2's action cells, and the plan only touched the abort-class names. Five of twelve `RUN-*` rows abort: `RUN-BASELINE-OWNERSHIP` (`ABORT RUN`, ownership), `RUN-LEDGER-INTEGRITY` (`ABORT RUN`, ledger), and `RUN-FROZEN-IDENTITY`, `RUN-COMMIT-CONTENTS`, `RUN-COMMIT-GATEWAY`, `RUN-CROSS-TREE` (conditional). Shrinking `ABORT_CLASSES` while leaving any of their `abort_classes` makes the shipped table fail `validate_finding_table` (`RC-ABORT-CLASS`), and leaving their action text contradicts the new 4.1. `RUN-SCOPE-DELTA` and `RUN-HOST-ATTEMPT` (timeout) still say FAIL ITEM for group (a) classes. | `run_evidence.RUN_FINDING_CODES` rows by `code=`; spec 4.2 table rows `RUN-BASELINE-OWNERSHIP` "ABORT RUN", `RUN-SCOPE-DELTA` "FAIL ITEM after containment; cascade dependents; continue independent items"; `run_evidence.validate_finding_table` "a never-aborting code names abort classes". |
| F-07 | (review PR-002) At least nine spec sentences outside 4.1/5.5/5.7 restate the six-class set or route a fault to a run abort, so amending only three sections leaves the spec self-contradictory. | Spec 1.4 A1 "restricted to six explicitly enumerated"; 2.1 "a hook-bypass attempt is one of the six `ABORT RUN` classes"; 2.10 "`fatal` here maps to the allowed run-wide identity/type ambiguity class"; 4.1 "**ABORT RUN**: stop all dispatch only for one of the six"; 4.1 containment step 6 "classify as ownership conflict or unknown outcome and abort"; 5.2 row 1 "Section 4.1's `Push attempt` abort class"; 5.3 step 9 "marks the appropriate enumerated abort class and stops"; 5.4 step 1 "identity/type ambiguity aborts the run"; 5.6 exit row 4 "One of the six enumerated run-wide classes". |
| F-08 | (review PR-003) Shipped code aborts a run for two reasons that are NOT a corrupt ledger. (1) A nested-`aw` tool-identity mismatch raises `ToolIdentityError`, which both drivers catch before the item-local `except DriverError` and re-raise to abort the whole run; plan `af7i6p` OQ-02 chose run-fatal by citing this spec's 1.4/A1 identity/integrity class. (2) The dependency preflight labels a `check.ipd-dependency-ambiguous` finding "run ABORTED (identity/type ambiguity is fatal)", but it raises before any session starts, so it is a refusal to start, not a mid-run abort. | `runner_shared.assert_child_tool_identity` "ABORTING RUN: nested `aw` tool-identity mismatch"; `oc_runipd.run_queue` `except ToolIdentityError: ... raise`; `runner_shared.DEPENDENCY_FATAL_RULES`; `runner_shared.enforce_dependency_preflight` "run ABORTED (identity/type ambiguity is fatal)", called from `initialize_run_core`. |
| F-09 | (review PR-004) `tests/test_host_capability_extension.py` asserts `"Push attempt"` IS in `run_evidence.ABORT_CLASSES`, so E-05 as written breaks it, and it was not in Scope-Paths. `tests/test_retry_class_mapping.py` was in Scope-Paths but asserts no spec text (it tests `TURN_RETRY_CLASSIFICATION` against `turn_failure_is_retryable`), and Order 04 `ytas91` owns that file. | `GuaranteeRowEnforcementStatusTests.test_row_1_push_denial_enforcement_status` "'Push attempt' is intentionally retained in ABORT_CLASSES"; `tests/test_retry_class_mapping.py` `test_predicate_agrees_with_table`; `ytas91` Scope-Paths. |
| F-05 | Maintainer ruling 2026-10-07: a push cannot be undone by aborting; a hook bypass or a hand status edit should be undone by the agent and redone with the proper tool; a hook refusal should go back to the agent; retrying only an unchanged worktree is the least useful case; "ambiguous side effect" is not reliably testable. | Session 2026-10-07; backlog `coivul`. |

## Proposed changes (ordered, validatable)

1. Three-group retry policy in 5.5 (E-01).
2. Evidence-keyed mapping table (E-02).
3. Matching 5.7 responses and a one-member 4.1 abort set (E-03).
4. Record the amendment (E-04).
5. Rewrite the Section 4.2 action and message cells to the amended policy (E-06).
6. Sweep the rest of the spec for the old set (E-07).
7. Keep `run_evidence` and its tests byte-true to the spec (E-05).

## Deferred / out of scope (with reason)

- Implementing any of it. Orders 02 to 07 implement the classes; this plan changes only the contract and its pinned transcription, so code children are reviewed against the new contract.
  - Carrier: lxb1ew

## Scope check

- Over-scope: none. Each path is written by one E-item: the spec by E-01 to E-04, E-06 and E-07; `run_evidence.py` and the three tests by E-05. `tests/test_retry_class_mapping.py` was removed from Scope-Paths at review (F-09): it pins no spec text and Order 04 owns it.
- Under-scope: none known. The 4.2 cells (E-06) and the rest of the spec (E-07) are now covered. Making the runner BEHAVE per the new cells is the implementing children's work (Orders 04 to 07); this plan changes contract text and the transcription of it only, and the code that aborts today (F-08) is either reconciled by OQ-02 or left to a child named in the OQ-02 answer.
- Scope fence: `- Scope-Paths:` is a declaration so the runner can reconcile afterwards. If execution genuinely needs another file, edit it and justify it at finalize (`--scope-reason`), and acknowledge any declared path left unmodified (`--scope-ack`).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_run_finding_abort_partition.py tests/test_run_finding_spec_transcription.py tests/test_host_capability_extension.py tests/test_retry_budget_citation.py` (measured at review, HEAD `383ebc1ee`, before any edit: the first three plus `tests/test_retry_class_mapping.py` gave `59 passed`; re-derive at execution).
- `python3 -c "from agent_workflows import run_evidence as e; print(e.validate_finding_table().ok); print(e.ABORT_CLASSES); [print(r.code, r.abort, r.abort_classes) for r in e.RUN_FINDING_CODES]"`.
- Bare `python3 -m pytest`, with the failing node IDs recorded in the lane BEFORE any edit and compared after; a failure present only after is attributed to this plan.
- `aw specs check` and `aw check` on the amended spec.

## Spec / documentation sync

THIS PLAN AMENDS AN APPROVED SPEC, declared in `- Scope-Paths:`. Why: the maintainer ruled the current never-retry and abort lists wrong for an isolated-worktree runner (F-05), and every other child in this Set implements the amended contract, so the contract must change first. The amendment widens what is retried and narrows what aborts; it does not change the budget.

## Open questions

### OQ-01: Should a push still stop the item rather than continue?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Resolved 2026-10-07: record it, tell the agent, continue. Aborting cannot recall a pushed commit, and detection is out of this Set (`denypush`).

### OQ-02: What happens to the two shipped run aborts that are not a corrupt ledger?

- Blocking: yes
- Finding: PR-003
- Status: resolved
- Owner: maintainer
- Context: the ruling says only a corrupt ledger aborts a run. The code aborts in one more case: a nested `aw` resolving to a different package than the runner's own (`ToolIdentityError`, run-fatal by plan `af7i6p` OQ-02, which cited this spec's identity/integrity class). That fault is run-wide by nature: every later item's lifecycle transitions would run under the same wrong tooling, so stopping one item and continuing is what `af7i6p` rejected as misleading. The second case, an ambiguous dependency id6, is refused before any session starts and is resolved by the reviewer as a REFUSE RUN, not an abort (decision D-2).
- Options: (A) the abort set is "Corrupt run ledger" plus "Runner tool-identity mismatch", both described as "the runner cannot trust its own state or tooling"; the code is unchanged. (B) the abort set is "Corrupt run ledger" only, and the tool-identity mismatch is filed as a stop-item class with a carrier (a backlog item to change `run_queue`), accepting that later items run under the wrong tooling until it lands. (C) treat a tool-identity mismatch as a form of corrupt ledger and say so in 4.1.
- Recommendation: (A). It keeps the ruling's reason (the runner cannot trust itself) and matches shipped behavior, so spec and code agree without a new child.
- Resolution or deferral rationale: Resolved by maintainer 2026-10-08: Option B chosen. The abort set is strictly "Corrupt run ledger" only. An item must not fail at all unless the specific item cannot complete, and if unable to complete, fail ONLY that one item. Aborting the entire run for a tool identity mismatch prevents modifying the tool codebase itself and disrupts unattended runs. Tool identity error is handled as an item failure (stopping the item and letting independent items continue); carrier backlog item `03y5g6` is filed to update `run_queue` accordingly.
- Carrier: 03y5g6

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste the amended Section 5.5 group lists; paste `grep -c "ambiguous side effect"` on the spec showing 0; paste `git diff` of the budget paragraph showing no change to it; paste the rewritten out-of-scope sentence and the Set-level production refusal paragraph showing the class name it quotes exists in group (a); paste `python3 -m pytest -o addopts="" tests/test_retry_budget_citation.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the amended mapping table, showing each fix-it row's evidence and implementing Order (or "unbuilt" plus carrier), and a one-to-one count of table rows against the members of groups (a) to (c).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the amended 5.7 rows for every changed class; the amended 4.1 `ABORT RUN` definition, abort set, "reclassified" sentence, containment step 6 and closing paragraph; and state which OQ-02 option they implement.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the new workflow-history line, the spec's `- Status:` line, and `aw specs check <spec> --agent` output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the passing run of the four named test modules with per-test counts; paste the `validate_finding_table` / `ABORT_CLASSES` / per-row `abort` and `abort_classes` one-liner from Required tests, showing `True`, only the OQ-02-approved classes, `always` for `RUN-LEDGER-INTEGRITY` and `never` for the rest; paste `git diff --name-only` showing no path outside Scope-Paths; paste the bare-suite summary line with the before and after failing node-ID lists.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the amended Section 4.2 action column for all twelve codes and every changed message cell, and paste the output of `derive_abort_from_action` over each spec action cell (parsed from the spec file, not from the module), showing which codes abort.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the full output of `grep -n -i "abort\|six\|enumerated"` on the amended spec, with a disposition for every hit (reconciled, deleted, unrelated use, or dated history).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution. OQ-02 resolved with maintainer ruling (Option B; carrier `03y5g6`).

Execution contract:
- Every open question is resolved before `aw ipd begin`.
- Scope fence: see Scope check. An out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Commit only through `aw commit <plan> -- <paths>`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming and then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
