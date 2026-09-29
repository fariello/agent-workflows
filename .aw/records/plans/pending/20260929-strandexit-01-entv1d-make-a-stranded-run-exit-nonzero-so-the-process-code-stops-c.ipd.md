# IPD: Make a stranded run exit nonzero so the process code stops contradicting spec 25kzda's exit-0 row

- Date: 2026-09-29
- Kind: child
- Concern: A run holding unintegrated ("stranded") work prints a red `STRANDED` headline and still exits `0`, which spec `25kzda` defines as "every actionable item is verified". Automation keying on the exit status therefore reads success for a run whose own record says integration was REFUSED.
- Scope: Deny the exit-code success token to a queue item whose own run record says its integration was refused, at the one shared projection seam both hosts already call, and amend spec `25kzda`'s exit-code table to state the rule. Reuses the SHIPPED exit `1` rather than minting a new code.
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/render_stream.py, tests/test_stranded_run_exit_code.py, .aw/records/specs/approved/20260826-25kzda-01-25kzda-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: high
- From-Backlog: qzxt1m
- Blocks-Release: next
- Set: strandexit
- Order: 1
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: entv1d

## Workflow history

- 2026-09-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-09-29 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): authored from backlog `qzxt1m`, graduating plan `ys1dor`'s OQ-01. The backlog item said the question NEEDS A MAINTAINER DECISION on two axes (whether to widen `1` or mint a new code, and the scope). Both were resolved FROM REPOSITORY EVIDENCE rather than deferred back, and the evidence is cited in the Findings table: `docs/cli-output-contract.md` Section 3 mandates a "uniform three-state exit classification across all verbs" (`0`/`1`/`2`), which REFUSES a new code and settles the first axis; the second is settled by the same document's Anti-Greenwashing Invariant. THE PREMISE WAS RE-MEASURED LIVE, not trusted from the backlog prose, and the measurement moved twice: (1) the backlog's `25kzda:1057` citation has ROTTED (the table is now at `:1406-1415`), so this plan cites by section and quoted string per `IPD-C801`; (2) the defect does NOT reproduce with `substantially-complete` as an outer reader might assume (that status is already outside the execute success bar and already exits `1`, which `render_stream.py`'s own comment states); it reproduces with a status INSIDE the bar, and all three members (`executed`, `approved`, `retired`) were measured stranded-at-exit-0.

## Goal

Make the process exit code agree with the run's own record: when a run's `state.json` says an item's integration was refused, the run must not exit `0`. The visible half of this lie was fixed by `ys1dor` (the headline reads red `STRANDED`); this plan fixes the machine-readable half that `ys1dor` deliberately left in place, and amends the spec table so the contract states the rule rather than leaving a reader to infer it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: re-measure the premise before changing anything

- [ ] E-01 Re-measure the defect at the executing HEAD and record the numbers in this plan's V-01 evidence, because every citation in this plan's Findings table is a point-in-time snapshot and one of the backlog's own citations has already rotted. For each of the three statuses in `runner_shared.EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES`, build a one-item queue dict carrying `action: "execute"` plus a refusing `integration_signal` (use `"suite-failed"`), then record: what `render_stream.integration_was_refused` returns, what `runner_shared.exit_code_statuses` projects, and what `runner_stop.deliberate_stop_exit_code` returns for that projection with `stopped=False`. ALSO record the CONTRAST case that proves the fix must not be written at the status bar: the same probe with `status: "substantially-complete"`, which must already return `1` BEFORE any change. If any stranded case already returns nonzero at HEAD, STOP and report: the defect has been fixed or altered by other work and this plan's premise needs re-authoring rather than execution.
  - Depends on: none
  - Expected outcome: A recorded table showing `rc=0` for all three success-bar statuses with a refusing signal, and `rc=1` for `substantially-complete`. This is the falsifiable baseline the whole plan rests on.
  - Execution state: pending

### Task group 2: deny the success token to a stranded item

- [ ] E-02 In `render_stream.py`, extract the stranded-item question into ONE exported predicate that answers it for BOTH stranded shapes, and have the two existing renderers call it rather than re-deriving. Today `render_stream.integration_was_refused` covers the EXECUTE shape and `render_stream.review_integration_was_refused` covers the REVIEW shape, and only the first reaches the outcome-word ladder (the review arm is consumed solely by `format_stranded_work_section`). Add a predicate that returns True when EITHER holds, site it in `render_stream.py` beside the two it composes, and give it a docstring stating that it is the one question the exit code and the headline must both ask so the two cannot drift. Do NOT change either existing predicate's behavior: they are separately tested and separately consumed. THE MODULE CHOICE IS FORCED, not preferred: `render_stream.py` imports zero in-package modules and is imported BY `runner_shared.py` at module level, so the predicate can only live here; defining it in `runner_shared.py` would put the import edge backwards.
  - Depends on: E-01
  - Expected outcome: A single exported predicate in `render_stream.py` answering "does this item's own record say its work did not land?" for both shapes, with the two existing predicates unchanged and still individually callable.
  - Execution state: pending

- [ ] E-03 In `runner_shared.exit_code_statuses`, deny `EXIT_SUCCESS_TOKEN` to an item E-02's predicate calls stranded, projecting it onto a new non-status token instead. Follow the EXACT pattern `EXIT_MALFORMED_ENTRY_TOKEN` already establishes in this same function: a module-level token constant that is deliberately not spellable as a real status (so it can never be confused with something a driver persists), a comment stating why, and a projection arm. Place the stranded arm AFTER the `queued` arm and BEFORE the `item_reached_success` arm. BOTH halves of that placement are load-bearing and must be stated in the comment: after `queued` because `deliberate_stop_exit_code` keys its entire graceful-stop concession off that literal (a queued item never ran, so it cannot have stranded work, and projecting it onto anything else breaks a correct wind-down's exit `0`); before the success arm because that arm is precisely what currently manufactures the wrong `0`. DO NOT implement this by editing `EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES` or any other success bar: those bars answer four other questions (dependency satisfaction, reporting, skip classification) enumerated in the doc block above them, three shipped tests pin their exact membership (`test_reaskscore_composed.py`, `test_terminal_status_vocabulary.py`, `test_runner_shared.py::CrossHostSuccessBarEqualityTests`), and a stranded item's STATUS is legitimately a success - it is the INTEGRATION that failed, which is a different fact about a different step.
  - Depends on: E-02
  - Expected outcome: `exit_code_statuses` projects a stranded item onto a token outside `{EXIT_SUCCESS_TOKEN}`, so the unchanged `deliberate_stop_exit_code` returns `1` for it. No success-bar constant is modified, and `item["status"]` is not rewritten (the function still returns a fresh list and touches no state).
  - Execution state: pending

- [ ] E-04 Verify the change reaches BOTH hosts through the shared seam and touches nothing else, then record the evidence. Confirm by reading the code that `oc_runipd.run_queue` and `agy_runipd.run_queue` each reach the new behavior via their existing `runner_shared.exit_code_statuses` + `runner_stop.deliberate_stop_exit_code` call pair, so NEITHER host file needs editing (which is why neither appears in `Scope-Paths`). ALSO confirm the change cannot alter a graceful stop's exit `0`: spec `c4gd2h` A1 and A4 both require a deliberate stop to exit `0`, so run the deliberate-stop path with a queue containing only `queued` items plus landed ones and confirm it still returns `0`. If either confirmation fails, do not proceed to E-06; report which one and stop.
  - Depends on: E-03
  - Expected outcome: A recorded reading showing one shared seam serving both hosts with zero host-file edits, plus a measured deliberate-stop case still exiting `0`.
  - Execution state: pending

### Task group 3: pin the behavior and amend the contract

- [ ] E-05 Add `tests/test_stranded_run_exit_code.py` pinning the behavior by OUTCOME, driving the real predicates and asserting on real returned exit codes (never by reading source text, counting callers, or asserting a comment survives). Cover, each as its own case: (a) each of the three success-bar statuses with a refusing `integration_signal` exits nonzero; (b) a REVIEW item with `review_integrated: False` exits nonzero, which is the shape the pre-change code missed entirely; (c) a landed item whose signal is one of the two EARNED values (`verifier`, `driver-run-suite`) still exits `0`, so the fix cannot turn a good run red; (d) an item with NO `integration_signal` key at all still exits `0`, which is every non-isolated run and is the regression that would be most expensive to ship; (e) an item released by the gate answer (`integration_released_by_answer` set) still exits `0`, because that refusal was explicitly lifted; (f) a mixed queue with one stranded and one landed item exits nonzero, matching the headline's resolved OQ-02 ruling that a PARTIAL strand is still a strand; and (g) a deliberate stop over `queued` plus landed items still exits `0`, pinning the `c4gd2h` A1/A4 requirement against this change. For case (a), assert the test FAILS against pre-change code by recording the measured pre-change value from E-01 in a comment, so a future reader can tell the test would have caught this.
  - Depends on: E-03
  - Expected outcome: A new test module whose seven cases pass after the change, and whose case (a) is documented as failing before it.
  - Execution state: pending

- [ ] E-06 Amend spec `25kzda`'s "Run exit codes" table so the contract states this rule instead of leaving it to be inferred, and say why in the Spec sync section. Make exit `1`'s row name the stranded class explicitly (its current clauses are "failed", "ended `dependency_not_met`", or "ended `ran`/`unavailable` without `--unverifiable-ok`", and a stranded item matches NONE of them, which is the gap the backlog item names). Add a dated note recording that the rule was derived from exit `0`'s own existing text ("every actionable item is verified") rather than invented, that the three-state classification in `docs/cli-output-contract.md` Section 3 is what refused a new code, and that the drivers now return `1` for this class. DO NOT touch the row-`4` UNRECONCILED CONFLICT note: it documents a live disagreement between this table and the shipped `aw runs` table from `4` upward, this plan deliberately stays at `1` where the two tables AGREE, and silently editing that note would erase a recorded open problem this plan does not solve. Do NOT restate the drivers' returned-code inventory as a fixed list anywhere in the amendment: that inventory is already measured stale (the note says "only `0`/`2`/`130`/`143`" while the shipped `integrate` and `audit` verbs return `1`), and repeating a number nothing enforces is how this table rotted before.
  - Depends on: E-05
  - Expected outcome: Spec `25kzda`'s exit-`1` row names the stranded class, carries a dated derivation note, and leaves the row-`4` conflict note intact.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`). THIS PLAN HAS A LIVE INSTANCE: the backlog item cites `25kzda:1057` and `:1061`, and both have rotted (the table now sits later in the file). Backlog `sbh1o1` is filed about exactly this class of rot in exactly this spec, and `25kzda`'s own preamble declares every dated paragraph a point-in-time snapshot that MUST be re-measured.
- `render_stream.py` imports NO first-party module and is imported BY `runner_shared.py` at module level. Its own comments record this as a FORCED direction, not a style choice, and `runner_shared.py`'s import block records that a guard pins its module-level first-party imports to exactly `render_stream` + `runner_profiles`. Any predicate both the renderer and the runner must call therefore belongs in `render_stream.py`.
- `runner_shared.exit_code_statuses` is a PROJECTION, not a second exit-code function, and its docstring states why: `deliberate_stop_exit_code` takes one `success_states` container for the whole queue and structurally cannot apply a per-item bar, so the per-item decision is made in the projection and handed over already reduced. It also states "THIS REWRITES NOTHING" and that an item can only LOSE a success it never earned, which is exactly the direction this plan moves.
- The success bars are deliberately plural and answer five different questions, enumerated in a doc block above them. Changing one to fix an exit code would change the other four answers.
- The repository's exit vocabulary is a THREE-STATE contract (`0` clean, `1` domain findings, `2` usage/cannot-run) documented in `docs/cli-output-contract.md` Section 3 as "uniform ... across all verbs". That document also carries an Anti-Greenwashing Invariant: a record "MUST NEVER report a positive outcome ... for work that was `skipped`, `partial`, `unverified`, or `cannot-run`".
- A DELIBERATE stop must exit `0` (spec `c4gd2h` A1 and A4), which is why `deliberate_stop_exit_code` exists and why the `queued` literal is preserved verbatim through the projection.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-01 | The defect is live and reproduces at HEAD. A one-item queue with an execute action, a status inside the execute success bar, and a refusing `integration_signal` projects onto `EXIT_SUCCESS_TOKEN` and exits `0`, while the summary headline for the same queue reads `STRANDED`. | Measured 2026-09-29 by calling `render_stream.integration_was_refused`, `runner_shared.exit_code_statuses`, and `runner_stop.deliberate_stop_exit_code` directly. All three members of `runner_shared.EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES` (`approved`, `executed`, `retired`) measured `stranded=True rc=0`. |
| F-02 | The backlog item's spec citations have ROTTED. It cites the exit-code table at `25kzda:1057` and the row-4 conflict note at `:1061`; the table now begins later in the file and the note sits in its row-`4` cell. The QUOTED STRINGS survive verbatim, so the premise is intact and only the offsets died. | `25kzda`'s "Run exit codes" table, exit-`0` row: "Every actionable item is verified; remaining items were benign skips". Row `4` still contains "UNRECONCILED CONFLICT, recorded 2026-09-05". Backlog `sbh1o1` documents this same rot class in this same spec. |
| F-03 | THE FIX MUST NOT BE WRITTEN AT THE STATUS BAR, and the naive reading of the backlog would put it there. `substantially-complete` - the status of the run that originally motivated `ys1dor` - is ALREADY outside the execute success bar and ALREADY exits `1`. `render_stream.py`'s own comment says so: "THE EXIT CODE IS NOT TOUCHED AND WAS NEVER WRONG ... the measured run exited 1. Only this SUMMARY lied, and changing the exit code here would be a real regression." The surviving defect is a status INSIDE the bar carrying a refusing signal. | Measured 2026-09-29: `substantially-complete` + `suite-failed` projects onto `substantially-complete` and returns `rc=1`, while `executed` + `suite-failed` returns `rc=0`. |
| F-04 | The exit-`1` row does not currently cover this class, so the amendment is REQUIRED and not cosmetic. Its three clauses are "failed", "ended `dependency_not_met`", and "ended `ran`/`unavailable` without `--unverifiable-ok`"; a stranded item matches none. The rule is nonetheless derivable from the exit-`0` row, which is why this is a defect rather than a feature request. | `25kzda` "Run exit codes" table, rows `0` and `1`. |
| F-05 | A NEW EXIT CODE IS REFUSED BY AN EXISTING CONTRACT, which settles the backlog's "widen 1 or mint a new code" question from evidence. `docs/cli-output-contract.md` Section 3 mandates a "uniform three-state exit classification across all verbs", enumerating only `0`, `1`, `2`, and its Exit Code Parity rule says the embedded `exit` field "MUST equal the process exit code (`0`, `1`, `2`)". Minting `3` or higher for this class would break that uniformity; reusing `1` satisfies both documents. | `docs/cli-output-contract.md` Section 3 and its Protocol Invariants. |
| F-06 | Reusing `1` also avoids the ALREADY-BROKEN region of the contract. The row-`4` note records that this spec's table and the shipped `aw runs` table agree on `0`-`3` and disagree from `4` upward, with `aw runs` assigning `4` to invalid evidence, `5` to ledger corruption, `6` to ownership conflict and `7` to not-a-ledger. Staying at `1` keeps this plan entirely inside the region where the two tables agree. | `25kzda` row `4`; `run_cli.py`'s exit-code table constants (`EXIT_OK`, `EXIT_INCOMPLETE`, `EXIT_BLOCKED`, `EXIT_INVALID_EVIDENCE`, `EXIT_CORRUPTED_LEDGER`, `EXIT_OPERATIONAL`, `EXIT_INVALID_INVOCATION`, `EXIT_NOT_A_LEDGER`). |
| F-07 | THERE ARE TWO STRANDED SHAPES AND ONLY ONE REACHES THE HEADLINE, so an exit-code fix wired to the execute predicate alone would still exit `0` for a stranded REVIEW. `render_stream.review_integration_was_refused` (added by plan `i4ak5n`) is consumed ONLY by `format_stranded_work_section`, not by the outcome-word ladder, so a stranded review already prints the recovery section beneath a `COMPLETED` headline. | Measured 2026-09-29: a review item with `review_integrated: False` returns `integration_was_refused=False` and `rc=0`. Call-site reading confirms `review_integration_was_refused` has exactly one consumer. |
| F-08 | The stranded-with-success-status case is PRODUCTION-REACHABLE and not merely synthetic, which is what makes this a bug rather than a hardening exercise. `runner_shared.reconcile_disposition` returns `RETIRED_STATUS` whenever the plan sits in a retired directory, checked BEFORE the agent's self-report; `retired` is a member of the execute success bar; and `integrate_retired_lane` - the only thing that lands such a lane - is gated on `integration.earned`. A turn that retires its plan in-lane and does NOT earn integration therefore reaches the unconditional `item["status"] = disposition` write with `status: "retired"` and a refusing signal already recorded. | `reconcile_disposition`'s `RETIRED_PLAN_BUCKETS` arm; `EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES` measured as `{'approved', 'executed', 'retired'}`; the `integrate_retired_lane` call site's `and integration.earned` conjunct; `execute_item_core`'s unconditional status write. |
| F-09 | The shared seam means NEITHER host driver needs editing. Both `oc_runipd.run_queue` and `agy_runipd.run_queue` end by calling `runner_stop.deliberate_stop_exit_code(runner_shared.exit_code_statuses(state["queue"]), success_states={runner_shared.EXIT_SUCCESS_TOKEN}, stopped=...)`. Backlog `cnwy8g` re-homed the queue-ordering and dependency helpers into `runner_shared` for this reason. | The terminal `return` in each host's `run_queue`. |
| F-10 | `--unverifiable-ok` is NOT a usable lever here, so the plan must not reach for it. It is parsed and validated by `runner_shared.evaluate_unverifiable_admission`, which is called once with an EMPTY item list (it validates the invocation only) and whose returned aggregation is DISCARDED. Its owner `run_evidence.aggregate_run_exit` has zero driver call sites. | `evaluate_unverifiable_admission`'s empty-list call and unassigned result; `run_evidence.py`'s own note that its contribution classes have "NO CONSUMER YET, STATED PLAINLY". |
| F-11 | Nothing currently asserts an exit code for a stranded run, so no shipped test contradicts this change and no shipped test would have caught the defect. The existing exit-code tests cover the malformed-entry projection, a `failed-safely` item, a `substantially-complete` execute item, a `not-run` skip item, and the deliberate-stop path. | `test_typed_queue_entries.py::test_birth_status_and_exit_code`, `test_action_table_runner_parity.py::test_consumer_exit_code`, `test_liftaudit_stop_halts_run.py`. |
| F-12 | Three shipped tests pin the success bars' exact membership, which is the concrete cost of implementing this at the bar instead of at the projection. | `test_reaskscore_composed.py` (pins `EXECUTION_SUCCESS_STATES`, `SUCCESS_STATES`, `EXECUTE_REPORTING_SUCCESS_STATES` and the derivation between them), `test_terminal_status_vocabulary.py`, `test_runner_shared.py::CrossHostSuccessBarEqualityTests`. |

## Proposed changes (ordered, validatable)

1. Re-measure the premise and record the baseline table, including the `substantially-complete` contrast that proves where the fix must NOT go (E-01).
2. Compose the two stranded predicates into one exported question in `render_stream.py`, the only module both the renderer and the runner can import (E-02).
3. Deny `EXIT_SUCCESS_TOKEN` to a stranded item inside `runner_shared.exit_code_statuses`, following the `EXIT_MALFORMED_ENTRY_TOKEN` precedent, leaving every success bar untouched (E-03).
4. Confirm both hosts inherit the change through the shared seam and that a deliberate stop still exits `0` (E-04).
5. Pin all seven cases by outcome in a new test module (E-05).
6. Amend spec `25kzda`'s exit-`1` row and record the derivation, leaving the row-`4` conflict note intact (E-06).

## Deferred / out of scope (with reason)

- WIRING THE DRIVERS TO `run_evidence.aggregate_run_exit`. That aggregator already owns a six-class taxonomy and the only integer table in the package, including exit `3` for `needs_input`, but neither driver calls it (zero call sites, recorded in `runner_shared.py` beside `NEEDS_INPUT_TOKEN` as plan `zz5yxq`'s deliberately-deferred OQ-02). Wiring it would change EVERY run's exit classification, not just the stranded class, and would immediately collide with the row-`4` conflict in F-06 and the three-state contract in F-05. That is a strictly larger change with a different risk profile and it needs its own plan.
- RECONCILING THE TWO EXIT-CODE TABLES from `4` upward. F-06 records the disagreement and this plan deliberately stays at `1`, inside the region where they agree. The row-`4` note already instructs whoever binds the abort classes to reconcile both tables explicitly; that is a separate mandate.
- PUTTING THE REVIEW STRANDED SHAPE INTO THE HEADLINE LADDER. F-07 measures that a stranded review prints `COMPLETED` with a stranded recovery section beneath it. This plan makes the review shape count for the EXIT CODE (E-02, E-05 case (b)) because that is the lie the backlog item carries, but it does not reorder the outcome-word ladder: that ladder's branch precedence is load-bearing and heavily commented (testing a signal before a status would relabel an existing outcome, which `ys1dor`'s review measured as "a regression dressed as the feature"), so changing it warrants its own plan and its own review. The headline half is FILED as backlog `aaa2xx` (Set `strandhead`); see OQ-01.
- CHANGING `aw attention --check`. It already gives automation a fail-closed signal, which is why the backlog item records that nothing is BLOCKED by the exit code being wrong. It is unaffected either way.

## Scope check

- Over-scope: none. The change is one projection arm, one composed predicate, one new test module, and one spec row. Neither host driver is edited (F-09), no success bar is edited (F-12), and no exit code outside `1` is introduced (F-05).
- Under-scope: This plan does not make the stranded-REVIEW case change the printed headline, only the exit code; the reason and the recommended follow-up are in Deferred. It also does not reconcile the two exit-code tables above `4`, and does not wire the unused `run_evidence` aggregator. A reader wanting "every dishonest run surface is now honest" will not get it from this plan alone; they will get the machine-readable half of one specific lie fixed.

## Required tests / validation

- `tests/test_stranded_run_exit_code.py`, the new module, all seven cases (E-05).
- The three existing exit-code surfaces, which must stay green and are the fence against a mis-sited fix: `tests/test_typed_queue_entries.py`, `tests/test_action_table_runner_parity.py`, `tests/test_liftaudit_stop_halts_run.py`.
- The three success-bar membership guards, which must stay green and would go red if the fix were wrongly implemented at a bar: `tests/test_reaskscore_composed.py`, `tests/test_terminal_status_vocabulary.py`, `tests/test_runner_shared.py`.
- The summary-rendering surfaces, since E-02 touches `render_stream.py`: `tests/test_zero_dispatch_outcome.py`, `tests/test_run_summary_table.py`.
- The full suite, run BARE as `python3 -m pytest`, with the actual `N passed` summary line pasted as evidence. Do not add `-n0`, a second `-q`, or `-p no:randomly`.
- `aw ipd lint --phase pre-transition` on this plan.
- `aw check release-gates`, because this plan carries `Blocks-Release: next`.
- `aw sanitize --agent`, because E-01 and V-01 capture measured output that could embed absolute paths.

## Spec / documentation sync

SPEC `25kzda` IS AMENDED BY THIS PLAN, and its path is declared in `Scope-Paths` so both runners announce the declared spec edit before the run starts and reconcile it at the end.

WHY THE AMENDMENT IS REQUIRED. The rule this plan implements is DERIVED from the exit-`0` row's existing text ("every actionable item is verified"), but the exit-`1` row enumerates three clauses and a stranded item matches none of them (F-04). Leaving the table unchanged would ship behavior that a reader of the contract cannot predict from the contract, which is the drift the repository's spec-amendment rule exists to prevent. The amendment is therefore the same change as the code, not a follow-up.

WHAT IS DELIBERATELY NOT TOUCHED. The row-`4` UNRECONCILED CONFLICT note stays exactly as it is (E-06): it records a live, dated disagreement between this table and the shipped `aw runs` table from `4` upward, and this plan stays at `1` where they agree. Editing or tidying that note would erase a recorded open problem this plan does not solve.

`docs/cli-output-contract.md` IS READ BUT NOT EDITED, and is therefore absent from `Scope-Paths`. Its three-state classification is what REFUSES a new exit code (F-05); reusing `1` for a "domain finding" is exactly what that document already says `1` means, so the change conforms to it as written and needs no edit. If the executor finds a document that ENUMERATES the run's exit codes and would become wrong, that file enters the fence and must be amended in the same change.

## Open questions

### OQ-01: Should the stranded-REVIEW shape also change the printed headline, not just the exit code?

- Blocking: no
- Status: deferred
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED, NON-BLOCKING, with the fact that makes it decidable already measured. F-07 records that `render_stream.review_integration_was_refused` is consumed only by `format_stranded_work_section`, so a stranded review today prints a `COMPLETED` headline directly above a recovery section telling the operator their work did not land - a self-contradicting screen. This plan makes that shape count for the EXIT CODE, which is the half the backlog item is about, so the machine-readable lie is fixed for both shapes. The HEADLINE half is deferred because the outcome-word ladder's branch precedence is load-bearing and its comments record a measured near-miss: `ys1dor`'s review found that testing the integration signal BEFORE the status would have relabelled the existing `FAILED` outcome for an `integration-blocked` item, calling it "a regression dressed as the feature". Reordering that ladder needs its own fence and its own review rather than riding along here. NOT BLOCKING because the exit code is what automation reads and what this plan fixes; a human reading the screen already sees the stranded recovery section naming the branch, so no operator is left with no signal at all. FILED, so the deferral has a durable carrier rather than living only in this plan's prose: backlog `aaa2xx` (Set `strandhead`), which records the measurement, states what this plan does and does not fix, and names the likely fix and the ladder hazard it must avoid.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The pasted baseline table from E-01: for each of `approved`, `executed`, `retired` with a refusing `integration_signal`, the returned value of `integration_was_refused`, the projected token list, and the exit code, showing `rc=0`; plus the `substantially-complete` contrast row showing `rc=1` BEFORE any change. Paste the actual interpreter output, not a description of it. State the HEAD commit the measurement was taken at.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: The new predicate's source pasted, plus interpreter output showing it returns True for BOTH an execute-shaped stranded item (refusing `integration_signal`) and a review-shaped one (`review_integrated: False`), and False for an item with neither key. Additionally paste output showing `integration_was_refused` and `review_integration_was_refused` each still return what they returned in V-01's baseline for the same inputs, proving neither was altered.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: The diff of `exit_code_statuses` and the new token constant pasted. Interpreter output showing a stranded item now projects onto the new token and `deliberate_stop_exit_code` returns `1` for it. PLUS the negative evidence that the fix was sited correctly: `git diff` over `agent_workflows/runner_shared.py` filtered to the success-bar constant names, showing ZERO changes to `SUCCESS_STATES`, `EXECUTION_SUCCESS_STATES`, `EXECUTE_REPORTING_SUCCESS_STATES`, `EXECUTE_OR_RETIRED_REPORTING_SUCCESS_STATES`, `SKIP_REPORTING_SUCCESS_STATES`, or `PLAN_REPORTING_SUCCESS_STATES`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: The terminal `return` statement from each host's `run_queue` pasted, showing both call the shared pair, plus `git diff --stat` showing `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py` are UNCHANGED. Plus interpreter output for the deliberate-stop case (a queue of `queued` plus landed items, `stopped=True`) returning `0`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted output of `python3 -m pytest tests/test_stranded_run_exit_code.py` showing all seven cases passing, with the `N passed` line. Then pasted output of `python3 -m pytest` (BARE) showing the whole fast suite green with its `N passed` line. Then pasted output of `python3 -m pytest tests/test_typed_queue_entries.py tests/test_action_table_runner_parity.py tests/test_liftaudit_stop_halts_run.py tests/test_reaskscore_composed.py tests/test_terminal_status_vocabulary.py tests/test_runner_shared.py tests/test_zero_dispatch_outcome.py tests/test_run_summary_table.py` green, which is the F-12 fence. If any of those was already failing before this change, say so explicitly with the pre-change result rather than attributing it to this plan.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: The diff of the spec's exit-code table pasted, showing the exit-`1` row names the stranded class and the dated derivation note is present. PLUS evidence the row-`4` note is intact: paste the row-`4` cell and confirm the string "UNRECONCILED CONFLICT, recorded 2026-09-05" is still present verbatim. PLUS pasted output of `aw ipd lint --phase pre-transition` on this plan conforming, `aw check release-gates` passing, and `aw sanitize --agent` over this plan and the captured evidence with zero `fail` findings.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan must not be executed until a human sets it `approved` with `aw ipd set approved <plan>`. No `- Readiness:` field is written here: that field is `/plan-review`'s attested output, and writing one while authoring would forge a review that has not happened.

THE EXECUTION CONTRACT. Commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Paste ACTUAL runner output for every test claim; do not claim a pass that was not run. Run the suite BARE as `python3 -m pytest`.

THE STOP CONDITION IS EXPLICIT AND COMES FIRST. E-01 re-measures the premise. If a stranded item already exits nonzero at the executing HEAD, the defect has been fixed or altered by other work: STOP, report the measurement, and do not proceed to E-02. This plan's entire justification is a measured `rc=0`, and executing it against a tree where that is no longer true would be changing code for a reason that has expired.

POST-GATE LIFECYCLE. After every `E-*` is performed and every `V-*` carries pasted, non-empty observed evidence, run `aw ipd lint --phase pre-transition` and finalize through the tooled path so the plan moves to `.aw/records/plans/executed/` with a scope-reconciled, path-scoped commit. Do not hand-edit terminal state. Because this plan declares a `.spec.md` path in `Scope-Paths`, both runners announce the declared spec edit before the run and reconcile declared against actual spec edits at the end; a spec changed without being declared is reported, so keep the amendment inside the declared fence.

BACKLOG HANDOFF. This plan carries `- From-Backlog: qzxt1m` and inherits that item's `- Blocks-Release: next`, so the release gate is provably preserved across the handoff and item `qzxt1m` may close once this plan is `executed`.
