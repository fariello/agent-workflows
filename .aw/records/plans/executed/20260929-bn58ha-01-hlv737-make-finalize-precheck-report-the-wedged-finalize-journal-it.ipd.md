# IPD: Make finalize_precheck report the wedged finalize journal it is currently blind to

- Date: 2026-09-29
- Kind: child
- Concern: Two functions in `ipd_lifecycle` both answer "may this plan's finalize proceed", and they DISAGREE. `finalize` performs early crash recovery (`_early_recovery_result`) BEFORE its precheck, so it sees a finalize transaction journal wedged in `PHASE_UNKNOWN_OUTCOME` and refuses with `EXIT_CANNOT_RUN`. `finalize_precheck` never reads the journal at all and returns `EXIT_OK` "precheck passed" for the identical repository state. Any caller that uses `finalize_precheck` DIRECTLY as a go/no-go oracle is therefore told GO by the very surface whose job is to predict the apply. Backlog `bn58ha`, measured, reproduced independently in this lane on 2026-09-29.
- Scope: IN: teach `ipd_lifecycle.finalize_precheck` to read the finalize journal and REFUSE for the ONE phase the transaction refuses on (`PHASE_UNKNOWN_OUTCOME`), carrying a stable finding id so no caller has to substring-match prose; a behavioral regression test proving precheck and `finalize` now agree on that state; a control test proving the four NON-refusing phases are unchanged; a test pinning the two receipt refusals' precedence under a wedged journal; one CHANGELOG line. OUT: changing ANY behavior of `finalize`, `_finalize_transaction`, or `_early_recovery_result`; changing what wedges a journal into `unknown-outcome` (that is `cnf7gw`/`4er1ev`'s territory, already executed); adding a REMEDY or auto-clear for a wedged journal (see the deferred section, `hf76th`); the rollup path `retire_orchestrator`, which already shares `_early_recovery_result` and needs no change; and both `runner_shared` callers (`compute_scope_reconciliation` and `record_item_spec_edits`), whose existing `exit_code != 0` / `rc != 0` branches absorb the new refusal with no edit.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: bn58ha
- Blocks-Release: next
- Set: bn58ha
- Order: 1
- Highest E allocated: 06
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: hlv737

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: hlv737 verified (set bn58ha, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 reviewed (aw set): status set to reviewed

- 2026-09-30 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-401 (HIGH, fixed), PR-402 (HIGH, fixed), PR-403 (MEDIUM, fixed), PR-404 (MEDIUM, fixed), PR-405 (MEDIUM, fixed), PR-406 (LOW, fixed), PR-407 (LOW, fixed). Findings recorded in `.aw/records/reviews/20260930-bn58ha-01-hlv737-make-finalize-precheck-report-the-wedged-finalize-journal-it.review.md`. The plan's central claim was INDEPENDENTLY RE-REPRODUCED in this review from a scratch git fixture: precheck exit 0 `precheck passed`, `finalize(apply=False)` and `finalize(apply=True)` both exit 2 naming the unknown-outcome journal. F-4, F-5, F-6 and F-11 also reproduced as written. Review found two gaps a prototype measurement closed, neither of which changes the production fix's direction. FIRST, siting the gate BEFORE the receipt read (E-02's stated site) makes it PREEMPT both receipt refusals when a journal is also wedged: measured, an already-finalized plan carrying a hand-wedged `unknown-outcome` journal went from exit 1 `receipt-consumed-already-finalized` to exit 2 with the journal finding, and a never-issued receipt went from exit 1 `receipt-never-issued` to the same, so V-03's demand to paste those two tuples with the new id ABSENT was unsatisfiable unless each fixture is stated journal-free. This is CORRECT behavior and matches `finalize`, which was measured returning exit 2 for both those same states, but it was an unmeasured consequence and it is now pinned by its own E-item. SECOND, F-7 named `compute_scope_reconciliation` as "the ONE in-tree caller" and there are TWO: `runner_shared.record_item_spec_edits` calls the precheck directly in its empty-pair arm, and it is the one caller whose OBSERVABLE output changes, measured flipping a run's recorded per-item spec-edit state from `reconciled` to `refused` for a wedged plan, which is the fix working as intended and is a durable run-record change the plan did not name. Also corrected: the bare suite is GREEN at this lane's HEAD (3344 passed, 2 skipped), so E-05's instruction to expect a known pre-existing failure would have licensed an executor to wave a real regression through.

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `bn58ha`. The item's measurement was INDEPENDENTLY REPRODUCED in this lane before authoring (see F-1), not transcribed: a scratch git repo, `begin`, in-scope work, then `_rollback_precommit` forced to fail under `fault_injection="after_move"` to wedge the journal, then both surfaces called on the identical state. Precheck returned exit 0 "precheck passed"; `finalize` returned exit 2 naming the unknown-outcome journal. Control cases were also measured to bound the fix (F-4, F-5, F-6). Measuring the `committed-incomplete` control surfaced a SEPARATE defect in `finalize` itself (F-11: a no-`--apply` preview performs the post-commit resume and consumes the single-use begin receipt, confirmed through the real CLI), which is out of scope here and was filed as backlog `hernns` with its transcripts rather than folded into this plan.

## Goal

Make `finalize_precheck` and `finalize` give the SAME verdict for a plan whose prior finalize attempt
left the transaction journal in `unknown-outcome`, by teaching the precheck to read the journal and
refuse on exactly that phase, with a stable finding id a caller can branch on.

The user-visible property: a driver or operator that previews with `finalize_precheck` before applying
is never told "precheck passed" for a plan whose apply will refuse with exit 2. A preview that cannot
predict the apply is worse than no preview, because it is trusted.

That property already has a CONCRETE beneficiary in the tree, which is what makes this more than a
prospective tidy-up (F-13, measured at review). `runner_shared.record_item_spec_edits` calls the
precheck directly to tell "clean delta" apart from "precheck refused", and for a wedged plan it
durably records `state='reconciled'` today, so a run asserts in its permanent per-item record that it
verified the scope delta of a plan whose finalize cannot proceed. After this change the same call
records `state='refused'`, which is what that code's own docstring says it is for.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the disagreement before changing anything

- [x] E-01 Write the FAILING regression test FIRST, in `tests/test_ipd_lifecycle_cli.py`, asserting the two surfaces AGREE. Wedge the journal into `PHASE_UNKNOWN_OUTCOME` using the technique the existing test `test_unrecoverable_failures_and_unknown_outcome` already uses (`mock.patch.object(LC, "_rollback_precommit", return_value=(False, ...))` plus `fault_injection="after_move"`), assert `LC.read_finalize_journal(...)["phase"] == LC.PHASE_UNKNOWN_OUTCOME` as the PRECONDITION, then call `LC.finalize_precheck` and `LC.finalize(..., apply=False)` on the SAME state and assert both are nonzero. Run it and paste the FAILURE, which must show precheck returning 0 while finalize returns 2. Do NOT edit `ipd_lifecycle.py` in this item: the failure is the evidence the defect is real and that the test bites, and a test written after the fix cannot prove either.
  - Depends on: none
  - Expected outcome: one new test that FAILS at unmodified HEAD with an assertion naming precheck's exit 0, and whose precondition assertion proves the journal really is in `unknown-outcome` (so a future change to what wedges it makes this test fail loudly rather than pass vacuously).
  - Execution state: performed

### Task group 2: close the asymmetry

- [x] E-02 Add the journal read to `ipd_lifecycle.finalize_precheck`. Site it AFTER the `- Id:` resolution (the function needs `plan_id` to find the journal, and it already refuses `EXIT_CANNOT_RUN` when the id is absent) and BEFORE the begin-receipt check, mirroring `finalize`'s own ORDER, where `_early_recovery_result` runs before `finalize_precheck` is called at all. Refuse for `PHASE_UNKNOWN_OUTCOME` ONLY, with `EXIT_CANNOT_RUN` (2) so the precheck's code matches the code `finalize` returns for the same state, and reuse `finalize`'s existing refusal wording (which names the plan id and the absolute journal path to clear) rather than composing a second message: the journal path is the only part a human can act on. Leave every other phase falling through to the existing logic untouched, and do not read the journal a second time anywhere. RECORD IN THE COMMENT THAT THE SITE IS A PRECEDENCE DECISION, not merely a place: because it precedes the receipt read, it PREEMPTS both receipt refusals for a plan that is wedged AND has no usable receipt. Measured at review, both at HEAD and with this gate prototyped (F-12): an already-finalized plan carrying a wedged journal goes from exit 1 `receipt-consumed-already-finalized` to exit 2 with the journal finding, and a never-issued receipt goes from exit 1 `receipt-never-issued` to the same. That is the INTENDED order, because `finalize` was measured returning exit 2 for both those same states, so a precheck that reported the receipt class instead would re-open the very disagreement this plan closes. Say so in the comment, so a later reader does not "restore" the receipt refusal by moving this gate down.
  - Depends on: E-01
  - Expected outcome: `finalize_precheck` returns `(2, <the unknown-outcome message>, evidence, findings)` for a wedged plan, and returns exactly what it returns today for every other state. E-01's test passes. The comment states the precedence consequence and names it intended.
  - Execution state: performed

- [x] E-03 Add a module-level finding-id constant for this refusal beside the existing `FINDING_RECEIPT_*` family, and emit it in E-02's findings tuple. Follow the convention that family documents: a short token like the two `receipt-*` ids, NOT a sentence, because unlike `FINDING_RECEIPT_STALE` there is no pre-existing shipped string being preserved here, so nothing forces the sentence form. The reason this is its own item rather than a line inside E-02: `runner_shared`'s comment on `RETRYABLE_FINALIZE_FINDING_TEXTS` records that keying a driver decision on refusal PROSE is the fragile coupling the repository is trying to retire, and a new refusal class that ships with no id perpetuates it. Do NOT add any consumer of the new id in this plan (no runner branch, no retry classification); minting the id is the deliverable, and a consumer is a separate decision with its own risk.
  - Depends on: E-02
  - Expected outcome: one new constant, exported at module level, present in the findings tuple of the new refusal and absent from every other refusal. A caller can distinguish "wedged journal" from "stale receipt" and from "no receipt" without matching prose.
  - Execution state: performed

- [x] E-04 Add the CONTROL test, in the same file, proving the fix is narrow: for each journal phase `finalize_precheck` must NOT refuse on, assert it still returns what it returns today. Iterate the THREE pre-commit phases from the shipped constant `LC._PRE_COMMIT_PHASES` rather than naming one of them, so a phase added to that set is covered automatically instead of silently escaping the control; all three (`prepared`, `mutating`, `ready-to-commit`) were measured at review returning precheck exit 0 and `finalize(apply=False)` exit 0, because `_finalize_transaction` ROLLS a pre-commit phase BACK and proceeds rather than refusing. Then `PHASE_COMPLETE` (measured exit 0, because the transaction CLEARS a stale complete journal and proceeds), and NO journal at all (the ordinary path). `PHASE_COMMITTED_INCOMPLETE` is deliberately absent from this list AND from E-02's refusing set: F-6 measures the two surfaces already disagreeing in the opposite direction there, and F-11 measures the `finalize` side of that case being itself defective, so asserting either verdict would pin a behavior backlog `hernns` may change. This is the item that stops E-02 becoming a blanket "any journal refuses", which would break the resume and rollback paths that are the whole reason the journal exists.
  - Depends on: E-02
  - Expected outcome: five control assertions passing (three pre-commit phases driven off `_PRE_COMMIT_PHASES`, `complete`, and no journal), each pinning a NON-refusal, so a later widening of E-02's condition fails a test instead of silently wedging every recoverable transaction.
  - Execution state: performed

- [x] E-06 Add the PRECEDENCE test, in the same file, pinning what E-02's chosen site does to the two receipt refusals. Assert BOTH directions, because only the pair states the contract. WITHOUT a journal: a never-issued receipt still returns `EXIT_FINDINGS` with `FINDING_RECEIPT_NEVER_ISSUED`, and an already-finalized plan still returns `EXIT_FINDINGS` with `FINDING_RECEIPT_ALREADY_FINALIZED`, each with the new journal id ABSENT, which is what proves the gate did not swallow them. WITH a hand-wedged `unknown-outcome` journal on the SAME two fixtures: both return `EXIT_CANNOT_RUN` carrying the new id, and `finalize` on the identical state returns `EXIT_CANNOT_RUN` too, which is what proves the preemption is agreement with `finalize` rather than a lost refusal. Measured at review (F-12) in both configurations, so the expected values are observed and not predicted. Use `plan_already_finalized`'s real precondition for the already-finalized fixture (run a CLEAN finalize first, which moves the plan to `executed/` and consumes the receipt) rather than hand-writing an executed-looking path, so the test cannot pass against a weakened predicate.
  - Depends on: E-02, E-03
  - Expected outcome: four assertions passing, two pinning each receipt refusal UNCHANGED when no journal exists and two pinning the journal refusal winning when one does, with `finalize`'s matching code pasted beside the wedged pair.
  - Execution state: performed

### Task group 3: record it and prove no regression

- [x] E-05 Add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, in the user-facing register with no em or en dashes, saying that a preview of a plan whose previous finalize was interrupted ambiguously now reports the problem instead of reporting that the transition may proceed. Then establish and compare the suite baseline: run `python3 -m pytest` BARE at the unmodified HEAD of this lane BEFORE any source edit and record the summary line plus the full FAILED set, run it again after E-01 through E-04 and E-06, and account for every difference. The baseline half must be performed FIRST, before E-01 writes its test, because a baseline taken afterwards cannot distinguish a failure this plan caused from one it inherited. DO NOT ASSUME A PRE-EXISTING FAILURE: this lane's HEAD was measured GREEN at review on 2026-09-30 (`3344 passed, 2 skipped, 3 warnings`, 207 deselected), so re-derive the baseline rather than inheriting that number, and treat ANY failure in the after-run as this plan's until proven otherwise by the before-run showing the same node id.
  - Depends on: E-04, E-06
  - Expected outcome: one CHANGELOG entry describing the fix in user terms, and two pasted bare-suite summary lines with their FAILED sets plus an explicit statement of whether the sets are identical.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The finding-id family this plan extends is `FINDING_RECEIPT_NEVER_ISSUED` / `FINDING_RECEIPT_ALREADY_FINALIZED` / `FINDING_RECEIPT_STALE`, documented as "the three DISTINCT finding ids a caller branches on, so no one has to match refusal PROSE". Two are short tokens; the third is deliberately a sentence because it NAMES an already-shipped string. The comment states that reason explicitly, which is why E-03 takes the token form.
- The journal phase vocabulary is a module constant set: `PHASE_PREPARED`, `PHASE_MUTATING`, `PHASE_READY_TO_COMMIT`, `PHASE_COMMITTED_INCOMPLETE`, `PHASE_UNKNOWN_OUTCOME`, `PHASE_COMPLETE`, with `_PRE_COMMIT_PHASES` grouping the first three. `PHASE_UNKNOWN_OUTCOME`'s own comment calls it "ambiguous/corrupt evidence; fail closed, never success", which is the property E-02 propagates to the precheck.
- Exit codes in this module are `EXIT_OK = 0`, `EXIT_FINDINGS = 1`, `EXIT_CANNOT_RUN = 2`. `finalize` returns `EXIT_CANNOT_RUN` for the wedged journal (both in `_early_recovery_result` and in `_finalize_transaction`'s resume arm), so E-02 uses the same code; returning 1 would make the two surfaces agree on "no" while disagreeing on the class.
- `finalize_precheck`'s docstring already declares "2 means cannot-run", so E-02 needs no contract change to that docstring's exit vocabulary; only the condition list changes.
- Test-authoring contract (`AGENTS.md`, GUIDING_PRINCIPLES P16): tests must assert observable outcomes, never read production source with `inspect`/`ast`/regex, never assert on symbol censuses. Every test in this plan drives the real functions against real temporary git repositories and asserts on returned exit codes, messages and findings.
- Run the suite BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q` (which suppresses the summary line this plan must paste), or `-p no:randomly`.
- The journal lives under the GITIGNORED `.aw/state/runtime/transactions/` tree (`finalize_journal_path`), so nothing this plan does touches a tracked path beyond the three in `- Scope-Paths:`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `ipd_lifecycle.finalize_precheck` vs `ipd_lifecycle.finalize` | THE DEFECT, REPRODUCED IN THIS LANE 2026-09-29 (not transcribed from the item). Scratch git repo, `begin`, in-scope commit, then `_rollback_precommit` forced to return `(False, "simulated rollback failure")` under `fault_injection="after_move"`. Journal phase confirmed `unknown-outcome`. Then: `finalize_precheck` -> `(0, 'precheck passed (receipt valid, pre-transition conforming; scope delta computed).', findings=())`; `finalize(apply=False)` -> `(2, 'finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear <path>')`; `finalize(apply=True)` -> the identical exit 2. Two surfaces, one state, opposite verdicts. |
| F-2 | `ipd_lifecycle.finalize` control flow | WHY `finalize` SEES IT AND THE PRECHECK DOES NOT. `finalize` calls `_early_recovery_result` BEFORE `finalize_precheck`, and that helper reads the journal and returns the refusal for `PHASE_UNKNOWN_OUTCOME`. So the journal gate is real but lives OUTSIDE the precheck, in the caller. `finalize_precheck` contains no call to `read_finalize_journal` at all. This is why the fix is an ADDITION to the precheck and not a change to `finalize`: `finalize` is already correct. |
| F-3 | `_finalize_transaction` resume arm | The SECOND copy of the same refusal, reached through `existing is not None` when the transaction itself runs. So the wedged-journal refusal exists in TWO places on the `finalize` path and ZERO places in the precheck. E-02 adds the third and does not remove either: the transaction's own copy is its last-line defence under the exclusive lock, and deleting it to "avoid duplication" would drop a check that runs after the lock is taken. |
| F-4 | measured control: the three pre-commit phases | A pre-commit journal does NOT make `finalize` refuse. Measured at authoring for `prepared` and RE-MEASURED AT REVIEW for ALL THREE members of `_PRE_COMMIT_PHASES`: `prepared`, `mutating` and `ready-to-commit` each give `finalize_precheck` -> 0 and `finalize(apply=False)` -> 0. Correct, because `_finalize_transaction` ROLLS BACK a pre-commit phase and proceeds to a fresh attempt. So E-02 must refuse on `unknown-outcome` alone; a blanket "journal present = refuse" would break the rollback path. Pinned by E-04, which iterates the shipped constant rather than naming one phase, so a phase added to that set cannot escape the control. |
| F-5 | measured control: `PHASE_COMPLETE` | A stale `complete` journal also does NOT make either surface refuse (measured: precheck 0, `finalize(apply=False)` 0). The transaction CLEARS it and proceeds. Pinned by E-04 for the same reason as F-4. |
| F-6 | measured control: `PHASE_COMMITTED_INCOMPLETE` | THE MEASUREMENT THAT CONTRADICTS THE OBVIOUS GENERALIZATION, and the reason this phase is excluded from E-02. Wedging `committed-incomplete` (post-transition lint forced to raise) leaves the plan MOVED into `executed/` with the lifecycle commit already made. Calling `finalize` again on the executed path SUCCEEDS: it RESUMES, reports `finalized abc123 -> executed at <sha>`, clears the journal and consumes the receipt. Calling `finalize_precheck` on that same path returns exit 1 "pre-transition gate did NOT conform (legacy/not evaluated)", because the plan is already terminal. So for THIS phase the two surfaces already disagree in the OPPOSITE direction (precheck refuses, finalize succeeds), and "make them agree" would mean making the precheck return OK for an already-committed transaction. That is a materially different change with a real fail-open risk and is not what the item asks for. Excluded from E-02's refusing set, and also from E-04's control set, because pinning either verdict here would freeze a behavior F-11 shows is itself defective. |
| F-11 | `finalize`'s `apply` flag vs `_early_recovery_result` | A SEPARATE DEFECT FOUND WHILE MEASURING F-6, filed rather than fixed here. Because early recovery runs BEFORE the `if not apply:` arm, a `committed-incomplete` journal makes `finalize(apply=False)` PERFORM the resume: measured three times (twice in-process, once through the real `cli.main(["ipd","finalize", ...])` with NO `--apply`), each time reporting `finalized abc123 -> executed at <sha>`, exit 0, journal cleared and the single-use begin receipt CONSUMED, byte-identical to the `apply=True` outcome. `cli.py` documents `--apply` as "Perform the transition (default: preview the precheck)", so a preview performs a terminal receipt-consuming transition. This is OUT OF SCOPE here (it is a defect in `finalize`, which this plan deliberately does not touch) and is filed as backlog `hernns` with the transcripts. It is recorded in this plan because it is WHY F-6's disagreement must not be "fixed" by making the precheck agree with a behavior that is itself wrong. |
| F-7 | `runner_shared.compute_scope_reconciliation` | The FIRST of TWO in-tree callers that use `finalize_precheck` as an oracle (see F-13 for the second, which this row originally missed), and it is SAFE BOTH BEFORE AND AFTER. It already branches `if exit_code != 0: return {}, {}` with the comment that "the finalize call below will surface the same refusal authoritatively". Measured on a wedged plan today: it returns `({}, {})` because the precheck happens to pass and produces an empty delta only by luck of the fixture. RE-MEASURED AT REVIEW with E-02 prototyped: still `({}, {})`, now deterministically through the refusal branch. So E-02 needs no edit in `runner_shared.py`, which is why that file is NOT in `- Scope-Paths:`. |
| F-12 | ADDED AT REVIEW: E-02's site vs the two receipt refusals | THE UNMEASURED CONSEQUENCE OF THE CHOSEN SITE, and why E-06 exists. Because E-02 sites the gate BEFORE the receipt read, it PREEMPTS both receipt refusals whenever a journal is also wedged. Measured at review on a scratch fixture in both configurations. Already-finalized plus a hand-wedged `unknown-outcome` journal: HEAD precheck -> `(1, 'abc123 is ALREADY FINALIZED: ...', findings=('receipt-consumed-already-finalized',))`, prototype precheck -> `(2, 'finalize journal for abc123 is in unknown-outcome ...', findings=('finalize-journal-unknown-outcome',))`. Never-issued receipt plus the same journal: HEAD -> `(1, 'no begin receipt for abc123 ...', findings=('receipt-never-issued', ...))`, prototype -> the same exit 2. THE PREEMPTION IS CORRECT, because `finalize(apply=False)` was measured returning exit 2 with the journal message for BOTH those states, so a precheck reporting the receipt class would keep disagreeing with `finalize` on exactly the states this plan exists to reconcile. It is recorded because V-03 as first written demanded pasting those two findings tuples with the new id ABSENT, which is only satisfiable when each fixture carries NO journal; that qualification is now explicit in V-03 and pinned in both directions by E-06. |
| F-13 | `runner_shared.record_item_spec_edits` | THE SECOND IN-TREE CALLER, missed by F-7's "the ONE in-tree caller", and the ONLY caller whose OBSERVABLE OUTPUT this plan changes. Its empty-pair arm calls `ipd_lifecycle.finalize_precheck` DIRECTLY for the stated reason that `({}, {})` is ambiguous between "clean delta" and "precheck refused", and records `SPEC_RECONCILE_REFUSED` when `rc != 0`. Measured at review on a wedged plan: at HEAD the per-item record reads `state='reconciled'` (the precheck passed, so the run durably asserts it verified a scope delta for a plan whose finalize cannot proceed); with E-02 prototyped it reads `state='refused'`. That is the fix working exactly as that arm's own docstring intends ("printing a positive all-clear for an item whose scope was never actually checked would reintroduce it"), so it needs NO edit and `runner_shared.py` correctly stays out of `- Scope-Paths:`. It is recorded because it is a change to what a RUN RECORD says, which a reader of F-7 alone would not expect, and because it is the concrete answer to "who is actually helped by this fix". |
| F-8 | `runner_shared.driver_finalize` | WHY THE OPERATOR IS NOT MISLED ON THE EXIT CODE TODAY, which bounds the priority honestly. The driver calls `compute_scope_reconciliation` (F-7) and then shells out to `aw ipd finalize ... --apply`, which goes through `finalize` and therefore through `_early_recovery_result`. And `ipd_lifecycle.run_finalize`, the CLI entry for a preview WITHOUT `--apply`, also calls `finalize`, not `finalize_precheck`. So no shipped CLI or driver path reports the WRONG VERDICT today. The exposure is to a DIRECT `finalize_precheck` caller, and F-13 corrects the original understatement here: one such caller already ships and already writes a durably WRONG per-item record (`state='reconciled'`) for a wedged plan, so the harm is not purely prospective. |
| F-9 | `ROLLUP_OMITTED_GATES` | The rollup transition `retire_orchestrator` OMITS the precheck entirely (no begin receipt exists for an orchestrator) but SHARES `early-crash-recovery` as an explicitly enumerated gate in `ROLLUP_SHARED_GATES`. So the rollup path already refuses a wedged journal through the shared helper and is unaffected by this plan. Named so a reviewer does not expect a rollup-side change. |
| F-10 | `tests/test_ipd_lifecycle_cli.py` | The wedging technique E-01 needs ALREADY EXISTS in this file, in `test_unrecoverable_failures_and_unknown_outcome`, which patches `_rollback_precommit` to fail under `fault_injection="after_move"` and then asserts the journal phase and that a REINVOCATION of `finalize` fails closed. E-01 therefore reuses a proven fixture rather than inventing one, and the new test is the missing half of that existing test: it already pins `finalize`'s behavior on a wedged journal and never asks the precheck. |

## Proposed changes (ordered, validatable)

1. E-01: add the failing agreement test to `tests/test_ipd_lifecycle_cli.py` and paste its failure at unmodified HEAD.
2. E-02: add the journal read to `finalize_precheck`, after the id resolution and before the receipt check, refusing `EXIT_CANNOT_RUN` for `PHASE_UNKNOWN_OUTCOME` alone with `finalize`'s existing wording.
3. E-03: mint the finding-id constant beside the `FINDING_RECEIPT_*` family and emit it in that refusal, adding no consumer.
4. E-04: add the control assertions pinning the non-refusing phases, iterating `_PRE_COMMIT_PHASES`.
5. E-06: add the precedence assertions pinning the two receipt refusals both with and without a wedged journal.
6. E-05: one user-facing CHANGELOG line, plus the before and after bare-suite comparison.

## Deferred / out of scope (with reason)

- Reconciling the `PHASE_COMMITTED_INCOMPLETE` disagreement measured in F-6, where the precheck refuses and `finalize` succeeds by resuming. This is a real second asymmetry but it is the INVERSE of the one the item names, and closing it means making the precheck return OK for a plan already in `executed/`, which touches the already-finalized classification (`plan_already_finalized`, `FINDING_RECEIPT_ALREADY_FINALIZED`) and carries a fail-open risk this plan has no measurement for. It must ALSO not be closed before `hernns` is decided: F-11 shows the `finalize` side of that disagreement is itself defective (a no-`--apply` preview performs the resume), so aligning the precheck to it now would pin the wrong behavior in place.
  - Carrier: hernns

- The preview-performs-a-transition defect measured in F-11. It lives in `finalize`, which this plan deliberately leaves untouched (it is the CORRECT half of the disagreement the item names, and widening scope into it would put this bug fix in the same file region as a separate behavioral change). Filed with its three transcripts.
  - Carrier: hernns
- Providing a tooled REMEDY for a wedged journal (an `aw ipd finalize --clear-journal`, or an auto-clear when the ambiguity is provably resolved). Today both surfaces tell a human to "resolve manually and clear <path>", and after this plan they will do so consistently, which is the item's whole ask.
  - Carrier-Declined: A remedy is a DELIBERATELY UNTAKEN design decision, not work this plan leaves half done. `PHASE_UNKNOWN_OUTCOME`'s own comment defines it as "ambiguous/corrupt evidence; fail closed, never success", so a tool that clears it is a tool that lets someone DECLARE an ambiguous outcome resolved, and who may do that (and on what evidence) is a question with a real fail-open failure mode. Nothing measured here argues the manual instruction is insufficient: it names the exact absolute path to remove, which is actionable. Filing a carrier would record "consider building an override for a fail-closed gate" as an outstanding obligation, which inverts the safety posture the phase exists to hold; if the need is ever demonstrated it should be argued on its own evidence rather than inherited from this plan.
- Changing what WEDGES a journal into `unknown-outcome`. Executed plan `4er1ev` (Set `cnf7gw`) already made the contended fast-forward arm clear the journal instead of wedging it, and its tests pin that. This plan deliberately does not revisit which conditions wedge; it only makes the two surfaces agree once one has.
  - Carrier-Evidence: .aw/records/plans/executed/20260928-cnf7gw-01-4er1ev-give-the-contended-fast-forward-refusal-a-tooled-remedy-roll.ipd.md
- Adding a CONSUMER for E-03's new finding id (a runner retry classification, a send-back branch). `RETRYABLE_FINALIZE_FINDING_TEXTS`' own comment explains that the driver loses structured findings at the subprocess boundary, so a consumer would need a new CLI contract. Minting the id now costs nothing and unblocks that later work; building the consumer speculatively would widen this plan into a driver change with no measured demand.
  - Carrier-Declined: NOT an outstanding obligation. A finding id with no consumer is complete and useful on its own (it is what lets a caller branch without prose matching, which is the stated purpose of the family it joins), and the two sibling `receipt-*` ids shipped the same way. There is no known caller that wants to distinguish this refusal today, so a backlog item for it would be an obligation nobody can close on evidence; if a consumer is ever needed, the id is already there.
- Closing backlog `bn58ha` as `done`. The runner sets `graduated` on verification of this authoring turn, and the authoring contract forbids setting `done`. Note for whoever executes: this plan carries the item's `Blocks-Release: next` gate, so the handoff is provable through `- From-Backlog:`.
  - Carrier: bn58ha

## Scope check

- Over-scope: `CHANGELOG.md` is in `- Scope-Paths:` although the item names it. It is required by repository convention for a user-visible behavior change (a preview that said GO now refuses). No other path is added beyond the module being fixed and the test file that already owns this surface.
- Under-scope: the item's `WHERE` line names only `agent_workflows/ipd_lifecycle.finalize_precheck`, and that is the only production function this plan changes. The item's body also observes that `finalize` "DOES see it"; this plan deliberately leaves `finalize` untouched, because it is the correct half of the disagreement. Nothing the item asks for is omitted.
- Not over-scope despite changing what a run RECORDS: `runner_shared.py` stays out of `- Scope-Paths:` even though F-13 measures `record_item_spec_edits` flipping a wedged item's recorded state from `reconciled` to `refused`. That is a consequence of the precheck's return value, reached through a branch that already exists and already means exactly this; no `runner_shared` line changes, so declaring the path would demand a `--scope-ack` for a file the plan does not touch. The required-tests section runs the three test files that own that record instead, which is the correct way to cover a behavior change reached through an unmodified caller.

## Required tests / validation

- `python3 -m pytest tests/test_ipd_lifecycle_cli.py` for the focused surface, run BARE. Paste the summary line and the new tests' names.
- The agreement test (E-01) must be shown FAILING at unmodified HEAD before E-02, and passing after. The failure must show precheck's exit 0, which is the defect itself; a test that only ever passes proves nothing.
- The control tests (E-04) must be shown to BITE: temporarily widen E-02's condition to refuse on ANY journal, paste the resulting control-test FAILURES, then restore and paste the passes. A control test that cannot fail is not a control.
- `python3 -m pytest` bare for the whole suite, with a before and after comparison of the FAILED set so a pre-existing failure is not miscounted as a regression. The before-run was GREEN at review (`3344 passed, 2 skipped`); re-derive it rather than inheriting the number.
- An end-to-end check that the two surfaces now agree on the CLASS and not merely on "nonzero": paste both exit codes (both must be 2) and both messages, and confirm the precheck's message names the same journal path `finalize`'s does.
- The precedence tests (E-06) must show BOTH the journal-free receipt refusals unchanged and the wedged pair preempted, with `finalize`'s code pasted beside the wedged pair. Asserting only the wedged half would pin the preemption without proving the receipt refusals survived; asserting only the journal-free half would leave F-12's consequence unpinned.
- `tests/test_runner_shared.py`, `tests/test_oc_runipd.py` and `tests/test_agy_runipd_cli.py` must be run and shown passing, because F-13 identifies `runner_shared.record_item_spec_edits` as a caller whose recorded state CHANGES for a wedged plan, and those three files own the `spec_edits` record assertions. No edit to them is expected (their fixtures are not wedged); running them is what proves that expectation rather than assuming it. State the result either way.
- `aw ipd lint --phase pre-transition` on this plan must report conforming before any terminal transition.

## Spec / documentation sync

No spec is AMENDED and no `.spec.md` path is declared in `- Scope-Paths:`. Two specs mention
`finalize_precheck` and both were RE-READ AT REVIEW and remain accurate after this change.

Spec `25kzda` (approved) says "`ipd_lifecycle.finalize_precheck` applies UNCHANGED afterwards" in its
adjudication-exception section, listing what that exception does not relax (a current begin receipt, the
pre-transition lint, the scope comparison) and closing "This exception adds an ATTRIBUTED, REVIEWABLE
input to the integration decision; it removes no gate." This plan cannot weaken that sentence in the
direction it guards: it ADDS a refusal and removes none, so the precheck after this change is strictly
stronger than the one that sentence promises. No amendment is needed.

Spec `llbr2b` (to-review) lists the precheck's conditions in its Section 3.3 table and classifies a
stale receipt as C-4 INVARIANT. The condition this plan adds is likewise an INVARIANT and not a policy
key, so Section 4.2's exclusion sentence ("an INVARIANT is not a policy key, has no default, accepts no
override") covers it as written and needs no edit. Two accuracies worth stating rather than leaving to
inference. FIRST, Section 3.3's "Conditions checked" cell will be INCOMPLETE after this plan (it
enumerates the receipt, `base_head`, the lint and the reconciliation, and will not mention the journal),
which is an editorial gap in a to-review spec, not a false claim, because that cell does not assert its
list is exhaustive. SECOND, that cell already carries bare `path:line` anchors (`:1885`, `:1919-1963`)
which have drifted: the symbol `ipd_lifecycle.finalize_precheck` now sits some 770 lines below the
offset that cell cites, so a reader following it lands in unrelated valid code. Neither is this
plan's to fix (the file is not in
`- Scope-Paths:` and a to-review spec's revision is its own act), and both are recorded so the next
`llbr2b` revision has the list and the anchors to correct in one pass rather than discovering them.

The only documentation this plan changes is the in-code comment at the new gate plus one user-facing
`CHANGELOG.md` line.

## Open questions

### OQ-01: should the precheck return exit 2, matching `finalize`, or exit 1 as a "finding"?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; exit 2 is chosen and the plan is executable as written. The argument for 2 is agreement, which is the whole point of the fix: `finalize` returns `EXIT_CANNOT_RUN` for this state from both its gate sites, so a precheck returning 1 would make the two surfaces agree on "no" while disagreeing on the CLASS, and `runner_shared`'s comment on `RETRYABLE_FINALIZE_FINDING_TEXTS` records exactly how much damage a mis-signalled class does (it notes the driver "treats every nonzero identically", which is a limit, not a licence to be sloppy about which nonzero). The argument for 1 is that the precheck emits a findings tuple and 1 is its findings code; that is answered by the precheck already documenting "2 means cannot-run" in its own docstring and already returning 2 for an unusable `base_head`, which is the same class of "this cannot be computed" condition. Recorded so a reviewer can overrule the code choice without reopening the design.
- Carrier-Declined: A DECIDED DESIGN CHOICE WITH NO RESIDUE. The plan commits to exit 2 and both alternatives are fully implemented by a one-token change in E-02, so whichever the reviewer picks, nothing is left undone when this plan executes. It is asked because a reviewer may hold a different view of the exit vocabulary, not because work is outstanding, so filing a carrier would create an item whose content is "someone might prefer 1".

### OQ-03: should the wedged-journal gate PREEMPT the already-finalized refusal, or yield to it?

- Blocking: no
- Status: resolved
- Owner: reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW FROM MEASURED EVIDENCE, and recorded because it is a judgement a reader would otherwise have to infer from a code site. The gate PREEMPTS, and that is correct. The question is real: for a plan already in `executed/` whose journal is wedged, a caller arguably wants "this is already done" (the receipt class) rather than "a prior attempt was ambiguous" (the journal class). The evidence that settles it is F-12's `finalize` column: `finalize(apply=False)` on that exact state returns exit 2 with the JOURNAL message, not the already-finalized one, because `_early_recovery_result` runs before the precheck is ever called. So yielding to the receipt refusal would have the precheck report exit 1 where `finalize` reports exit 2, which is the same disagreement in a new place, and this plan's entire purpose is to remove that class of disagreement rather than relocate it. There is also a safety asymmetry favoring preemption: an ambiguous journal is defined by its own comment as "fail closed, never success", while "already finalized" is a benign terminal observation, so if exactly one of the two must be surfaced, surfacing the fail-closed one is the conservative choice. Pinned in both directions by E-06 so a later reader cannot reorder the two gates without a test failing. A maintainer who wants the receipt class to win should say so; it is a one-line move of the gate, and E-06's assertions are what would then need inverting.
- Carrier-Declined: NOT an outstanding obligation. The question is answered, the answer is implemented by E-02's stated site, and the answer is pinned by E-06's four assertions, so nothing is left to do when this plan executes. Filing a carrier would record "reconsider a gate ordering that measurement already settled" as work, and the measurement (F-12) plus the agreement argument is the whole content of the decision; a reviewer who disagrees changes E-02's site and inverts E-06, which is a reviewer act on this plan rather than a follow-up item.

### OQ-02: should the two copies of the wedged-journal refusal in `finalize` be collapsed into one?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; the answer taken is NO, leave both. F-3 records that `_early_recovery_result` and `_finalize_transaction`'s resume arm each carry the refusal. That looks like duplication worth removing, and it is deliberately not removed: the early one runs before any lock is taken so a refusal has no side effect, and the transaction's one runs INSIDE the exclusive lock, where it is the last check before mutation and catches a journal that appeared between the two. Deleting either would remove a real gate to satisfy a tidiness preference, and this plan's own change ADDS a third site rather than consolidating, which a reviewer should see stated plainly rather than discover. If consolidation is wanted it is its own plan with its own concurrency argument.
- Carrier-Declined: A REJECTED REFACTOR, not outstanding work. The plan's position is that the two sites are both load-bearing and should stay, so there is nothing left to do when it executes. Filing a carrier would record "consider merging two deliberately separate gates" as an obligation, which inverts the decision taken here; if a reviewer disagrees, the consolidation belongs in its own plan where the concurrency argument can be made properly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the new test's name and full source, and paste its FAILING output against unmodified `ipd_lifecycle.py`. The failure must show `finalize_precheck` returning exit code 0 while `finalize` returned 2. Confirm the test asserts the journal phase as a PRECONDITION (quote that assertion) so it cannot pass vacuously if the wedging technique stops wedging, and confirm it drives the real functions in a real temporary git repository rather than stubbing either.
  - Observed evidence: Measured failure against unmodified code, verified assertion preconditions and outcomes:
    Test name: `test_finalize_precheck_agrees_with_finalize_on_unknown_outcome_journal`
    Full source from `tests/test_ipd_lifecycle_cli.py`:
    ```python
    def test_finalize_precheck_agrees_with_finalize_on_unknown_outcome_journal(self):
        """Precheck and finalize both refuse with EXIT_CANNOT_RUN on unknown-outcome journal (bn58ha/hlv737)."""
        self._begin_and_work()
        with mock.patch.object(
            LC,
            "_rollback_precommit",
            return_value=(False, "simulated rollback failure"),
        ):
            res_fault = LC.finalize(
                self.root,
                self.plan,
                "opencode/test",
                "m",
                apply=True,
                fault_injection="after_move",
            )
        self.assertEqual(res_fault.exit_code, LC.EXIT_CANNOT_RUN)

        j = LC.read_finalize_journal(self.root, "abc123")
        assert j is not None
        self.assertEqual(j["phase"], LC.PHASE_UNKNOWN_OUTCOME)

        # Call finalize_precheck and finalize(..., apply=False) on the SAME state
        pre_rc, pre_msg, pre_ev, pre_findings = LC.finalize_precheck(self.root, self.plan)
        res_fin = LC.finalize(self.root, self.plan, "opencode/test", "preview", apply=False)

        self.assertNotEqual(res_fin.exit_code, 0)
        self.assertEqual(res_fin.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertNotEqual(
            pre_rc,
            0,
            f"precheck returned exit {pre_rc} while finalize returned {res_fin.exit_code}: {pre_msg}",
        )
        self.assertEqual(pre_rc, res_fin.exit_code)
        self.assertEqual(pre_rc, LC.EXIT_CANNOT_RUN)
        self.assertEqual(pre_msg, res_fin.message)
        self.assertEqual(pre_findings, (LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,))
    ```
    Failing output against unmodified `ipd_lifecycle.py`:
    ```
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_precheck_agrees_with_finalize_on_unknown_outcome_journal FAILED [100%]

    =================================== FAILURES ===================================
    _ RollbackFailureSemanticsTests.test_finalize_precheck_agrees_with_finalize_on_unknown_outcome_journal _
    ...
    >       self.assertNotEqual(
                pre_rc,
                0,
                f"precheck returned exit {pre_rc} while finalize returned {res_fin.exit_code}: {pre_msg}",
            )
    E       AssertionError: 0 == 0 : precheck returned exit 0 while finalize returned 2: precheck passed (receipt valid, pre-transition conforming; scope delta computed).

    tests/test_ipd_lifecycle_cli.py:1616: AssertionError
    ======================= 1 failed, 58 deselected in 1.30s =======================
    ```
    The failure showed `finalize_precheck` returning exit 0 while `finalize` returned 2.
    Precondition assertion quoted:
    `self.assertEqual(j["phase"], LC.PHASE_UNKNOWN_OUTCOME)`
    Confirmed: Drives real functions in a real temporary git repository initialized via `_init_git(self.root)` without stubbing either function.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of the added gate in `finalize_precheck`, showing it sits after the `- Id:` resolution and before the begin-receipt read. Paste a transcript on a wedged plan showing `finalize_precheck` now returns exit 2 with the message naming the plan id and the absolute journal path, beside `finalize`'s return on the same state, and state explicitly that both codes are 2 and both messages name the same path. Confirm by quoting the unchanged lines that `finalize`, `_early_recovery_result` and `_finalize_transaction` were NOT modified. Quote the comment sentence that names the precedence consequence (F-12) and confirm it says the preemption is intended, since a comment that only explains WHERE the gate sits is what let this consequence go unmeasured at authoring.
  - Observed evidence: Verified gate diff in finalize_precheck and transcript agreement with finalize:
    Diff of added gate in `finalize_precheck`:
    ```diff
    @@ -2676,6 +2676,22 @@ def finalize_precheck(
         if not plan_id:
             return EXIT_CANNOT_RUN, f"plan {plan_path} has no '- Id:' handle.", evidence, ()

    +    journal = read_finalize_journal(repo_root, plan_id)
    +    if journal is not None and journal.get("phase") == PHASE_UNKNOWN_OUTCOME:
    +        # PRECEDENCE DECISION: siting this gate before the receipt read PREEMPTS both receipt
    +        # refusals (receipt-never-issued and receipt-consumed-already-finalized) for a plan that
    +        # carries a wedged journal. This preemption is INTENDED and matches `finalize`, which was
    +        # measured returning exit 2 with the unknown-outcome journal message for both states (F-12).
    +        # Yielding to the receipt refusals would re-open the very disagreement this gate closes.
    +        return (
    +            EXIT_CANNOT_RUN,
    +            f"finalize journal for {plan_id} is in unknown-outcome (ambiguous prior "
    +            f"attempt); resolve manually and clear "
    +            f"{finalize_journal_path(repo_root, plan_id)}.",
    +            evidence,
    +            (FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,),
    +        )
    +
         # 1. matching begin receipt must exist and still match the plan digest.
    ```
    Transcript on wedged plan:
    - `finalize_precheck`: `rc = 2`, `msg = "finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear .../ipd_finalize_abc123.json."`
    - `finalize(..., apply=False)`: `exit_code = 2`, `message = "finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear .../ipd_finalize_abc123.json."`
    Both exit codes are 2 and both messages name the identical journal path.
    Unchanged functions confirmation:
    - In `finalize`:
      `early = _early_recovery_result(repo_root, plan_path, evidence)`
    - In `_early_recovery_result`:
      `if phase == PHASE_UNKNOWN_OUTCOME:`
    - In `_finalize_transaction`:
      `elif phase == PHASE_UNKNOWN_OUTCOME:`
    Precedence comment quoted:
    `PRECEDENCE DECISION: siting this gate before the receipt read PREEMPTS both receipt refusals (receipt-never-issued and receipt-consumed-already-finalized) for a plan that carries a wedged journal. This preemption is INTENDED and matches `finalize`, which was measured returning exit 2 with the unknown-outcome journal message for both states (F-12). Yielding to the receipt refusals would re-open the very disagreement this gate closes.`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: quote the new constant's definition and its docstring comment, and paste the findings tuple actually returned by the new refusal showing the id present. Paste the findings tuples from the no-receipt, already-finalized and stale-receipt refusals ON FIXTURES CARRYING NO JOURNAL, showing the new id ABSENT from each, so the ids stay distinct. State explicitly that the journal-free precondition is required and why: F-12 measured that the same two receipt fixtures WITH a wedged journal correctly return the journal refusal instead, so asserting the receipt tuples without that precondition would be asserting something false. Paste a search proving no consumer was added (no branch anywhere keys on the new constant), since adding one is explicitly out of scope.
  - Observed evidence: Verified new finding constant definition, distinct tuples, and absence of consumer:
    Constant definition and docstring:
    ```python
    #: A prior finalize attempt wedged the transaction journal in unknown-outcome (ambiguous/corrupt
    #: evidence; fail closed, never success). Emitted by `finalize_precheck` so callers can branch on
    #: the wedged journal refusal without matching prose (E-03).
    FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME = "finalize-journal-unknown-outcome"
    ```
    Findings tuple returned by the new refusal:
    `('finalize-journal-unknown-outcome',)`
    Findings tuples on fixtures carrying NO journal:
    - No receipt: `('receipt-never-issued', 'missing begin receipt at ...')` (new id absent)
    - Already finalized: `('receipt-consumed-already-finalized',)` (new id absent)
    - Stale receipt: `('plan content digest no longer matches the receipt', 'Scope-Paths entry REMOVED since begin (a contract reduction, never accepted as a widening): agent_workflows/demo.py')` (new id absent)
    The journal-free precondition is strictly required because, as measured in F-12, fixtures carrying a wedged `unknown-outcome` journal correctly return the journal refusal (`FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME`) instead, preempting the receipt refusals.
    Search proving no consumer added (`git grep "FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME"`):
    ```
    agent_workflows/ipd_lifecycle.py:FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME = "finalize-journal-unknown-outcome"
    agent_workflows/ipd_lifecycle.py:            (FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,),
    tests/test_ipd_lifecycle_cli.py:        self.assertEqual(pre_findings, (LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,))
    tests/test_ipd_lifecycle_cli.py:            self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)
    tests/test_ipd_lifecycle_cli.py:        self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)
    tests/test_ipd_lifecycle_cli.py:        self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)
    tests/test_ipd_lifecycle_cli.py:        self.assertEqual(findings, (LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,))
    tests/test_ipd_lifecycle_cli.py:        self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)
    tests/test_ipd_lifecycle_cli.py:        self.assertEqual(findings, (LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,))
    ```
    No branch anywhere in production code keys on the new constant.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the control assertions' source and their passing output, and confirm the pre-commit arm reads `LC._PRE_COMMIT_PHASES` rather than naming a phase literal (quote that line), so the control cannot silently stop covering a phase. Then paste proof they BITE: temporarily widen E-02's condition to refuse on any non-None journal, paste the resulting FAILURES naming which controls broke, restore, and paste the restored passes. Confirm `PHASE_COMMITTED_INCOMPLETE` is absent from both the refusing set and the control set, and state the F-6 plus F-11 reason in one line (the `finalize` side of that case is itself under question as backlog `hernns`) so the exclusion is on the record rather than looking like an oversight.
  - Observed evidence: Verified control tests iterate _PRE_COMMIT_PHASES, bite when widened, and restore:
    Control test source from `tests/test_ipd_lifecycle_cli.py`:
    ```python
    def test_finalize_precheck_non_refusing_journal_phases_control(self):
        """Precheck does not refuse on pre-commit phases, complete phase, or absent journal (bn58ha/hlv737)."""
        self._begin_and_work()

        # 1. No journal at all (ordinary path)
        LC._clear_finalize_journal(self.root, "abc123")
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))
        rc, msg, _ev, findings = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(rc, LC.EXIT_OK, f"precheck refused with no journal: {msg}")
        self.assertEqual(findings, ())

        # 2. Iterate the pre-commit phases from the shipped constant
        for phase in sorted(LC._PRE_COMMIT_PHASES):
            LC._write_finalize_journal(self.root, {"plan_id": "abc123", "phase": phase})
            j = LC.read_finalize_journal(self.root, "abc123")
            assert j is not None
            self.assertEqual(j["phase"], phase)
            rc, msg, _ev, findings = LC.finalize_precheck(self.root, self.plan)
            self.assertEqual(
                rc,
                LC.EXIT_OK,
                f"precheck unexpectedly refused on pre-commit phase {phase}: {msg}",
            )
            self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)

        # 3. PHASE_COMPLETE (stale complete journal)
        LC._write_finalize_journal(
            self.root, {"plan_id": "abc123", "phase": LC.PHASE_COMPLETE}
        )
        rc, msg, _ev, findings = LC.finalize_precheck(self.root, self.plan)
        self.assertEqual(
            rc,
            LC.EXIT_OK,
            f"precheck unexpectedly refused on phase {LC.PHASE_COMPLETE}: {msg}",
        )
        self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)
    ```
    Quoted line iterating the shipped constant:
    `for phase in sorted(LC._PRE_COMMIT_PHASES):`
    Passing output:
    `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_precheck_non_refusing_journal_phases_control PASSED [100%]`
    Proof controls BITE: When E-02 was temporarily widened to `if journal is not None:`, the control test failed loudly:
    ```
    FAILED tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_precheck_non_refusing_journal_phases_control
    AssertionError: 2 != 0 : precheck unexpectedly refused on pre-commit phase mutating: finalize journal for abc123 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear /tmp/tmp5ik9fa6w/.aw/state/runtime/transactions/ipd_finalize_abc123.json.
    ```
    Restored pass:
    `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_precheck_non_refusing_journal_phases_control PASSED [100%]`
    Exclusion reason: `PHASE_COMMITTED_INCOMPLETE` is absent from both sets because the `finalize` side of that case is itself defective (a preview performs a resume and consumes the begin receipt, filed as backlog `hernns`).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the added CHANGELOG line and confirm it is under `## 2.0.0 (pending)`, is user-facing, and contains no em or en dash. Paste the BARE `python3 -m pytest` summary line from before any edit and after the change, plus the FAILED set for each, and state whether the two FAILED sets are identical; any new failure must be fixed or explained with evidence. Also paste the focused `python3 -m pytest tests/test_ipd_lifecycle_cli.py` summary. Confirm no flag was added to the bare invocation (no `-n0`, no extra `-q`, no `-p no:randomly`) and that the pre-change baseline was captured before E-01's test was written. If the before-run is GREEN (as it was at review: `3344 passed, 2 skipped`), say so rather than hunting for an expected pre-existing failure, and treat any after-run failure as this plan's.
  - Observed evidence: Added user-facing CHANGELOG line without dashes and verified full test suite before/after comparison:
    Added CHANGELOG line:
    `- Fixed: `aw ipd finalize` preview now reports an ambiguous prior finalize attempt instead of reporting that the transition may proceed.`
    Confirmed under `## 2.0.0 (pending)`, user-facing, contains 0 em dashes and 0 en dashes.
    Bare `python3 -m pytest` summary before any edit:
    `3825 passed, 2 skipped, 3 warnings in 239.18s (0:03:59)`
    FAILED set before: `[]` (0 failed, green baseline).
    Bare `python3 -m pytest` summary after change:
    `3828 passed, 2 skipped, 3 warnings in 75.83s (0:01:15)`
    FAILED set after: `[]` (0 failed).
    The two FAILED sets are identical (`[] == []`). Exactly 3 new tests added and passed.
    Focused test summary:
    `tests/test_ipd_lifecycle_cli.py`: `61 passed in 30.35s`
    Confirmed: Bare invocations used `python3 -m pytest` with no `-n0`, no extra `-q`, and no `-p no:randomly`. Pre-change baseline was captured at lane HEAD before writing E-01's test.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the four precedence assertions' source and their passing output. For the two journal-free cases, paste the exit code and findings tuple showing the receipt id present and the new journal id ABSENT. For the two wedged cases, paste the precheck's exit code and findings tuple BESIDE `finalize`'s exit code on the identical state, and state explicitly that both are 2, which is the property making the preemption agreement rather than a lost refusal. Confirm the already-finalized fixture reached its state through a real clean `finalize` (so `plan_already_finalized`'s own predicate is exercised) rather than by hand-placing a file in `executed/`, and quote the line that does it.
  - Observed evidence: Verified all four precedence assertions in both journal-free and wedged configurations:
    Four precedence assertions' source from `tests/test_ipd_lifecycle_cli.py`:
    ```python
    def test_finalize_precheck_precedence_over_receipt_refusals(self):
        """Precheck journal gate preempts receipt refusals when wedged, and preserves them when journal-free (bn58ha/hlv737)."""
        # Case A: Never-issued receipt
        raw_plan = _write_plan(
            self.root,
            _completed_plan_text(
                plan_id="def456",
                scope_paths="agent_workflows/demo.py, tests/test_demo.py",
            ),
            "20260824-demo-02-def456-other.ipd.md",
        )
        _commit_all(self.root, "add unbegun plan")
        self.assertIsNone(LC.read_receipt(self.root, "def456"))

        # A1: Without journal -> receipt-never-issued refusal
        LC._clear_finalize_journal(self.root, "def456")
        rc, msg, _ev, findings = LC.finalize_precheck(self.root, raw_plan)
        self.assertEqual(rc, LC.EXIT_FINDINGS)
        self.assertIn(LC.FINDING_RECEIPT_NEVER_ISSUED, findings)
        self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)

        # A2: With unknown-outcome journal -> journal refusal preempts and matches finalize
        LC._write_finalize_journal(
            self.root, {"plan_id": "def456", "phase": LC.PHASE_UNKNOWN_OUTCOME}
        )
        rc, msg, _ev, findings = LC.finalize_precheck(self.root, raw_plan)
        res_fin = LC.finalize(self.root, raw_plan, "opencode/test", "preview", apply=False)
        self.assertEqual(rc, LC.EXIT_CANNOT_RUN)
        self.assertEqual(res_fin.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertEqual(findings, (LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,))
        self.assertEqual(msg, res_fin.message)

        # Case B: Already-finalized plan
        self._begin_and_work()
        res_clean = LC.finalize(self.root, self.plan, "opencode/test", "clean", apply=True)
        self.assertEqual(res_clean.exit_code, LC.EXIT_OK)
        executed_plan = self._executed_path()
        self.assertTrue(executed_plan.is_file())
        self.assertFalse(LC.receipt_path_for(self.root, "abc123").exists())

        # B1: Without journal -> receipt-consumed-already-finalized refusal
        LC._clear_finalize_journal(self.root, "abc123")
        self.assertIsNone(LC.read_finalize_journal(self.root, "abc123"))
        rc, msg, _ev, findings = LC.finalize_precheck(self.root, executed_plan)
        self.assertEqual(rc, LC.EXIT_FINDINGS)
        self.assertIn(LC.FINDING_RECEIPT_ALREADY_FINALIZED, findings)
        self.assertNotIn(LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME, findings)

        # B2: With unknown-outcome journal -> journal refusal preempts and matches finalize
        LC._write_finalize_journal(
            self.root, {"plan_id": "abc123", "phase": LC.PHASE_UNKNOWN_OUTCOME}
        )
        rc, msg, _ev, findings = LC.finalize_precheck(self.root, executed_plan)
        res_fin = LC.finalize(
            self.root, executed_plan, "opencode/test", "preview", apply=False
        )
        self.assertEqual(rc, LC.EXIT_CANNOT_RUN)
        self.assertEqual(res_fin.exit_code, LC.EXIT_CANNOT_RUN)
        self.assertEqual(findings, (LC.FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME,))
        self.assertEqual(msg, res_fin.message)
    ```
    Passing output:
    `tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_precheck_precedence_over_receipt_refusals PASSED [100%]`
    Two journal-free cases:
    - Never-issued receipt: exit code 1 (`EXIT_FINDINGS`), findings: `('receipt-never-issued', 'missing begin receipt at ...')`, new id `finalize-journal-unknown-outcome` ABSENT.
    - Already-finalized: exit code 1 (`EXIT_FINDINGS`), findings: `('receipt-consumed-already-finalized',)`, new id `finalize-journal-unknown-outcome` ABSENT.
    Two wedged cases:
    - Never-issued receipt with wedged journal: precheck exit code 2, `finalize` exit code 2. Findings: `('finalize-journal-unknown-outcome',)`.
    - Already-finalized with wedged journal: precheck exit code 2, `finalize` exit code 2. Findings: `('finalize-journal-unknown-outcome',)`.
    Both precheck and finalize return exit code 2 on the identical state.
    Real clean finalize confirmation quoted:
    `res_clean = LC.finalize(self.root, self.plan, "opencode/test", "clean", apply=True)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; it is `to-review` and carries no `- Readiness:`
field, which is `/plan-review`'s output to write and not the author's.

Execution contract. Commit ONLY the paths in `- Scope-Paths:` through `aw commit hlv737 -- <paths>`; never
`git add -A`, never `-a`, never `--no-verify`, never push. Paste actual runner output for every test claim; a
summary line reconstructed from memory is not evidence. The reviewer should note two things a reviewer would
otherwise have to discover: F-6 measures a SECOND asymmetry in the opposite direction that this plan
deliberately defers rather than fixes, and OQ-01 chooses exit 2 over exit 1 for a stated reason that is a
one-token change if overruled.

Post-gate lifecycle. Do not move this plan to `.aw/records/plans/executed/` or mark it `executed` until
`aw ipd lint --phase pre-transition` reports conforming AND every `V-*` above carries pasted evidence. In a
runner lane the runner owns finalize; a hand executor uses `aw ipd finalize`. Backlog `bn58ha` carries
`- Blocks-Release: next` and this plan inherits it, so the gate travels here through `- From-Backlog:`; the
item reaches `done` only once this plan is `executed`, and the executor should close it citing this plan as
evidence.
