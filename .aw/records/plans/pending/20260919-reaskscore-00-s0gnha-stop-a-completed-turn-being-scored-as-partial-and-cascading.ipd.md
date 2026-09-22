# IPD: Stop a completed turn being scored as partial and cascading dependency-blocked across its Set

- Date: 2026-09-19
- Kind: orchestrator
- Concern: FOUR RUNS IN ONE DAY ENDED `BLOCKED` WITH THEIR WORK FINISHED, COMMITTED, AND THROWN AWAY BY THE SCORING. Measured 2026-09-18 across `run-20260918T045802Z-2547360`, `run-20260918T190723Z-2697256`, `run-20260918T193638Z-2963696` and their repeats: in each case one item was recorded `partial`, every sibling cascaded to `dependency-blocked`, and the orchestrator was deferred. Three INDEPENDENT defects compose to produce it. (1) THE HOST truncates a turn it was asked to run in the foreground, terminating the agent's own command and then reporting `SUCCESS` with exit 0, so the driver accepts a killed turn as a clean one. (2) THE DRIVER, having scored that empty turn `partial`, then spends a defect re-ask that COMPLETES THE ENTIRE JOB and re-collects the finished outcome to the exact path the scorer reads - and never rescores it, so a fully successful turn is recorded `partial` with `last_outcome: null` beside a complete outcome file. (3) A TURN THAT PROVABLY DID NOTHING is treated as a terminal attempt indistinguishable from one that genuinely fell short, so a single such item is allowed to block a whole Set. The dependency cascade itself is CORRECT in every instance and must not be loosened; each defect is a wrong INPUT to a right rule.
- Scope: Orchestrate the FOUR child plans that close these defects, in dependency order, and confirm at the end that the composed behavior actually fixes the measured runs rather than each piece passing in isolation. This plan holds ORCHESTRATION ONLY: every deliverable belongs to a child (`skn8uk` the rescoring, `ty7w6o` the host-truncation signal, `dy9ymn` the zero-work retry, `svacmz` the composed proof and the predicate-unweakened pins), and this file contributes no code, no test, and no record of its own. EXCLUDES loosening any dependency, success-bar, or orchestrator-retirement predicate, in every child without exception.
- Scope-Paths: .aw/records/plans/pending/20260919-reaskscore-00-s0gnha-stop-a-completed-turn-being-scored-as-partial-and-cascading.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: reaskscore
- Order: 0
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- From-Backlog: yxfw4k
- Blocks-Release: next
- Work-Kind: bug
- Id: s0gnha
- Approval: 2026-09-19, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-19 approved (aw set): status set to approved

- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /askme: OQ-03 RESOLVED FROM THE REPOSITORY WITHOUT ASKING, because there was no live decision left to ask about, clearing this plan's only blocking question and with it its `no-go`. BOTH PREMISES HAD EXPIRED BETWEEN THE TWO REVIEWS, and the timestamps make that checkable rather than asserted: this parent was reviewed at `24a3c262` with its lane merged at 12:53, while `dy9ymn`'s own round 1 landed at `27d399ed` 13:35, 42 minutes LATER. Measured at both commits: at `24a3c262` `dy9ymn` E-04 read "Use the run's already-resolved value ... introduce NO second retry knob" with `grep -c integration_attempts` = 0, exactly the unbuildable instruction this question reports; at HEAD that wording is gone and the count is 7, E-04 now telling its executor to count on the item mirroring the shipped `integration_attempts` precedent, which needs no ledger and adds no knob. That IS shape (b), already taken. SECOND PREMISE ALSO FALSE, AND ALREADY FALSE WHEN THE QUESTION WAS WRITTEN: `xipfy1` OQ-03 reads `- Status: resolved` at HEAD AND at `24a3c262` itself, the maintainer having settled the substrate on 2026-09-10 in favor of the drivers' own `state.json`/`events.jsonl`, so shape (a)'s stated cost never applied and the two answers coincide. THE CODE FACT THE FINDING MEASURED REMAINS TRUE and is preserved rather than waved away: re-measured at HEAD, no read of the frozen `retry_budget` exists anywhere in `agent_workflows/`, `plan_retry`/`retry_budget_remaining` still have zero callers outside `run_recovery.py`, `run_engine`/`RunEngine` appear 0 times in both drivers, and 0 of 214 run directories contain a `ledger.jsonl`; only the inference that this leaves `dy9ymn` unexecutable was falsified. NO EDIT TO `dy9ymn` WAS MADE: it is `go-pending-approval` with no gating finding, and adding an `executed:xipfy1` edge would block a ready plan on a preference, the same reasoning by which `xipfy1`'s own OQ-01 declined a hard edge. PR-005 recorded FIXED; `aw ipd lint --phase review-finalize` now `conforming`; `subject_gating_blocks` `()`. Readiness `no-go` -> `go-pending-approval`; HUMAN APPROVAL IS STILL REQUIRED and no agent may write it.
- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): /plan-review round 1: REVIEWED - OPEN QUESTIONS; PR-001..PR-007, five FIXED, PR-004 and PR-005 left OPEN with PR-005 escalated as blocking OQ-03; Readiness `no-go` pending that answer. Reviewed at HEAD `24a3c262`; the plan was byte-identical to the sealed lane input and the tree was clean, so no pre-review snapshot. `aw ipd lint --phase author` reported `clean` before the revisions and `--phase review-finalize` reports only the expected `IPD-Q501` (OQ-03 blocking and open) after them. THE DIAGNOSIS AND THE SET SHAPE ARE RIGHT, and I verified the central mechanism against the runner rather than the prose: the scoring call, the re-ask block, the injected `recollect` and `integration_gate_relevant` sit in the order the children claim, `reconcile_disposition` is pure in all three copies, and `skn8uk`'s OQ-02 is correct that a rescued item falls to `integration_is_earned`'s driver-run-suite branch. WHAT WAS WRONG WAS RECONCILIATION WITH THE FOURTH CHILD, added two commits after this file and never folded back in. (1) The parent's E-02/E-03 still duplicated the work `svacmz` was authored to own, and the parent's copy is the one a runner retirement ticks WITHOUT performing, so E-02 is now a RECEIPT CHECK over `svacmz`'s evidence blocks and E-03 is the Set-level backlog transitions no child owns. (2) Five places still counted three children. (3) TWO SELF-CARRIERS would have refused this plan's OWN finalize: `- Carrier: s0gnha` resolves while pending and goes terminal at `executed`, and measured against the live carrier index 2 of 5 obligations flipped to failing at `error` severity (this plan's `- Date:` is the first day past `CARRIER_CUTOVER_DATE`), evaluated at the `pre-transition` checkpoint the gate itself requires; both are now `Carrier-Declined` and re-measured at 0 of 6. (4) E-01 offered parallel lanes neither runner has (each `run_queue` selects one item and breaks; no `--jobs` flag). ESCALATED RATHER THAN FIXED: `dy9ymn` E-04 bounds its retry by a frozen `--retry-budget` that is parsed, validated, frozen and READ BACK BY NOTHING, while `xipfy1` (`approved`, release-blocking, sharing 3 of 4 scope paths) owns that gap and carries its own unresolved BLOCKER; OQ-03 puts the three shapes to the maintainer. ALSO MEASURED AND RECORDED: 22 of 74 citations across the Set (30%, `skn8uk` 48%) already point at different code, none out of range. Full record: `.aw/records/reviews/20260919-reaskscore-00-s0gnha-stop-a-completed-turn-being-scored-as-partial-and-cascading.review.md`.
- 2026-09-19 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored with its three children from backlog `yxfw4k` (the rescoring defect, newly filed) and `x7wfyx` (the zero-work retry, already open). The Set exists rather than a single plan because the three defects are genuinely independent: each one alone is sufficient to lose a run, each is fixable alone, and each has its own review surface. Inherits `Blocks-Release: next`.
- 2026-09-19 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Make a run's recorded outcome match what actually happened, so that finished work is never discarded as
`partial` and a single wasted turn never blocks three siblings. The Set is done when the two measured
failure shapes cannot reproduce and the composed behavior is demonstrated end to end, not merely
unit-tested in three parts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: sequence the Set and prove it composed

- [ ] E-01 EXECUTE THE CHILDREN IN THE ORDER THE TABLE BELOW DECLARES, honoring `dy9ymn`'s `executed:ty7w6o` edge and `svacmz`'s three `executed:` edges, and confirm each child is `executed` before dispatching anything that depends on it. `skn8uk` and `ty7w6o` are INDEPENDENT of each other and may run in either order; `dy9ymn` requires `ty7w6o` because it consumes the `attempt["host_truncation"]` record that plan produces; `svacmz` requires all three because it verifies the MERGED result. NOTE FOR AN EXECUTOR WORKING BY HAND RATHER THAN THROUGH A RUNNER: neither runner can dispatch two items concurrently (each `run_queue` selects ONE runnable item per loop iteration and breaks, `oc_runipd.run_queue` at the `for item in sorted(queued, ...)` / `break` selection, mirrored in `agy_runipd`), and there is no `--jobs`/`--parallel` flag, so "in parallel lanes" is not an available mode and nothing here depends on one. This item is orchestration and performs no product change of its own.
  - Depends on: none
  - Expected outcome: all four children are `executed`, each dependency edge was satisfied at dispatch, and no child's deliverable was performed by this plan.
  - Execution state: pending

- [ ] E-02 CONFIRM `svacmz` ACTUALLY PERFORMED THE TWO VERIFICATIONS IT OWNS, by reading its `V-*` evidence rather than by re-performing its work. This item is a RECEIPT CHECK, not a second verification: `svacmz` owns the predicate-unweakened pins (its E-01/E-02) and both measured-shape reconstructions plus the collision case (its E-03/E-04), and duplicating them here would put the same assertions in two places with no second observer. What this item does is confirm, on `svacmz`'s executed plan file, that its `V-01` carries the five constants' ACTUAL VALUES (not a bare "unchanged"), that its `V-02` carries the pin output and the `git diff` for both pin files, and that its `V-03`/`V-04` carry the SHAPE A and SHAPE B reconstruction output and the collision case. An empty or hand-waved `Observed evidence` block on any of those four is a FAILURE of this item and the Set is not complete.
  - Depends on: E-01
  - Expected outcome: `svacmz`'s `V-01`..`V-04` each carry concrete pasted evidence, quoted here by reference, and none is satisfied by an assertion without output.
  - Execution state: pending

- [ ] E-03 TRANSITION THE TWO SOURCE BACKLOG ITEMS HONESTLY, which is the one substantive act that belongs on this plan because it is a Set-level record change no child owns. Set `yxfw4k` `done` only if its defect is fixed AND validated by `svacmz`'s evidence; it carries `Blocks-Release: next`, so the close-legitimacy gate requires the gate be provably preserved or released (a `From-Backlog` handoff, cited `--evidence`, or an explicit `--blocks-release -`), and `aw backlog set done` FAILS CLOSED otherwise. Set `x7wfyx` `graduated`, NOT `done`, because only its item B is implemented, and do NOT clear its `Blocks-Release`. Use `aw backlog set` so each history entry is tool-written.
  - Depends on: E-01, E-02
  - Expected outcome: `yxfw4k` and `x7wfyx` each carry a tool-written transition consistent with what was actually delivered, and `x7wfyx` retains its release gate.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
| --- | --- | --- | --- |
| 01 | `20260919-reaskscore-01-skn8uk-rescore-the-disposition-after-a-defect-re-ask-whose-recollec.ipd.md` | Rescores the disposition from the re-collected outcome after a defect re-ask, monotonically (improvements only), before the integration gate reads it. Fixes the measured `partial`-with-`executed`-outcome. | none |
| 02 | `20260919-reaskscore-02-ty7w6o-record-a-host-truncated-agy-turn-as-truncated-instead-of-acc.ipd.md` | Observes the agy host's own truncation lines on the stream the driver already reads, and records a truncated turn durably instead of accepting exit 0 as a clean finish. Produces the signal only. | none |
| 03 | `20260919-reaskscore-03-dy9ymn-retry-a-turn-that-provably-attempted-nothing-instead-of-bloc.ipd.md` | Adds a narrow, fail-closed "provably attempted nothing" predicate and re-queues such an item once within the existing retry budget instead of recording a terminal `partial`. Consumes `ty7w6o`'s signal. | `executed:ty7w6o` |
| 04 | `20260919-reaskscore-04-svacmz-prove-the-composed-reaskscore-fix-against-both-measured-shap.ipd.md` | OWNS THE VERIFICATION E-02 AND E-03 DESCRIBE, so it is performed and verified by an agent turn instead of being retired unperformed. Pins the five shared constants byte-identical and the cross-host/AST pins unweakened on the merged result; reconstructs SHAPE A and SHAPE B end to end; proves the truncated-and-rescued collision is rescored without being retried and that the predicate ordering guarantees it. Adds tests and evidence only, no product change. | `executed:skn8uk`, `executed:ty7w6o`, `executed:dy9ymn` |
| 05 | `20260921-reaskscore-05-p9j6c0-close-the-reaskscore-set-receipt-check-svacmz-and-transition.ipd.md` | ACCEPT: performs this orchestrator's E-02 and E-03 as a real agent turn. Receipt-checks `svacmz`'s `V-01`..`V-04` for ACTUAL pasted evidence, then transitions both source backlog items honestly: `yxfw4k` to `done` via a CITED-EVIDENCE route that preserves its `Blocks-Release: next` rather than clearing it, and `x7wfyx` to `graduated` (NOT `done`, only item B is implemented) with its gate intact. E-01 is deliberately NOT lifted: dispatch ordering is the runner's act by construction. Added 2026-09-22 after the coverage gate refused a run naming `s0gnha` as carrying work no child covers. | `executed:svacmz` |

## Completion criteria (the whole Set is done only when)

- All FOUR children are `executed`, each having satisfied its own `V-*` items with concrete pasted evidence.
- The two measured failure shapes are reconstructed and shown not to reproduce, and the collision case is proven ordered rather than accidental: OWNED BY `svacmz` (its E-03/E-04), confirmed here by E-02.
- No shared predicate was weakened: OWNED BY `svacmz` (its E-01/E-02), confirmed here by E-02.
- The bare `python3 -m pytest` suite passes on the merged result, with the actual summary line pasted.
- The two source backlog items are transitioned honestly (E-03): `yxfw4k` may close once its defect is fixed and validated; `x7wfyx` must be `graduated`, NOT `done`, because only its item B is implemented and it carries `Blocks-Release: next`.

## Cross-IPD validation

- NO CHILD LOOSENED A PREDICATE. This is the Set's central safety property: all four measured cascades were correct, so any widening of a success bar would trade a visible defect for an invisible one. OWNED BY `svacmz` E-01/E-02; this plan's E-02 confirms the evidence exists.
- THE TWO FIXES DO NOT COLLIDE. `skn8uk` rescues a turn whose work EXISTS; `dy9ymn` re-dispatches a turn whose work DOES NOT. Those conditions are mutually exclusive by construction (`dy9ymn`'s conjunction requires no outcome file, no commit, unchanged head, clean tree, all of which a rescued turn violates), but the Set must DEMONSTRATE the exclusivity rather than assume it, because the cost of getting it wrong is re-dispatching completed committed work. OWNED BY `svacmz` E-04.
- THE ORDERING WITHIN THE TURN IS CONSISTENT ACROSS CHILDREN. `skn8uk` inserts its rescore between the defect record and the integration gate; `dy9ymn` requeues before the cascade observes a terminal status; `ty7w6o` records at the stdout seam and changes no disposition. Confirm on the merged result that these three insertions did not reorder each other, and that the AST ordering pins in `tests/test_rununify_execute_item_gates.py` pass unweakened.
- NO CHILD EDITED A SPEC. Each child deliberately declares no `.spec.md` path and each records its candidate amendment as a non-blocking open question (`skn8uk` OQ-01 on `7ckptx` R2.1, `ty7w6o` OQ-02 on `7ckptx` R4, `dy9ymn` OQ-01 on `25kzda` 5.5). Confirm none was edited anyway, since an undeclared spec edit is reported by the runner's own scope reconciliation.

## Deferred / out of scope (with reason)

- THE ORCHESTRATOR RETIREMENT BAR IS NOT WIDENED. `runner_shared.SET_RETIREMENT_DONE_STATUS` is `executed` alone, and its own comment says in terms that it is "DELIBERATELY NOT `EXECUTION_SUCCESS_STATES`"; it is governed by spec `77tr3o`. So a rescued item that reaches `substantially-complete` unblocks its SIBLINGS but leaves the parent stranded rather than retired; retirement follows normally once the item reaches `executed` through the finalize path `skn8uk` re-opens. Changing that bar inside a defect-fix Set would be an unreviewed contract change.
  - Carrier-Declined: Nothing to carry: the retirement bar is spec `77tr3o`'s reasoned contract and is not defective. A rescued item that reaches `executed` through the re-opened finalize path retires its parent normally, so no future act is pending.
- TELLING THE AGENT ITS REMAINING TURN BUDGET (`x7wfyx` item A) is left undone, with the consequence stated: `x7wfyx` is therefore `graduated`, not closed. It is a prompt change with its own regression surface, and per `ty7w6o`'s finding F-1 the agent was not the one choosing to stop, so it no longer addresses the measured cause.
  - Carrier: x7wfyx
- PREVENTING THE HOST FROM BACKGROUNDING A FOREGROUND COMMAND is out of reach and is `ty7w6o` OQ-03. It is upstream behavior this repository does not control and cannot test; the retry in `dy9ymn` is the compensating control.
  - Carrier: dy9ymn
- NO SPEC IS AMENDED BY THIS SET. Three candidate amendments are recorded as non-blocking open questions on the children for a reviewer to authorize deliberately, rather than being taken silently inside a defect fix.
  - Carrier-Declined: EACH AMENDMENT IS ALREADY CARRIED BY THE CHILD THAT RAISED IT, as that plan's own recorded open question with the wording it would use (`skn8uk` OQ-01, `ty7w6o` OQ-02, `dy9ymn` OQ-01), so the obligation has a home and a self-carrier here would only duplicate it. A SELF-CARRIER WAS REMOVED HERE DELIBERATELY at review: `- Carrier: s0gnha` on this plan resolves while the plan is pending and goes TERMINAL the moment the plan reaches `executed`, at which point `check.ipd-uncarried-obligation` reports it as resolving "only to a terminal/hidden artifact; nothing revisits it". Since this plan is dated on or after the carrier cutover `20260919`, that finding is `error` severity and it is evaluated at the `pre-transition` checkpoint, so a self-carrier would refuse this plan's own finalize. Measured at review by substituting an `executed` status for `s0gnha` in the carrier index: 2 obligations flipped from legitimate to failing.

## Scope check

- Over-scope: none. This plan declares only its own file and contributes no product change; every deliverable is owned by a child.
- Under-scope: the orchestrator retirement bar, `x7wfyx` item A, the host's own backgrounding behavior, and the three spec amendments, each excluded above with a reason. A reviewer should confirm these exclusions rather than assume them.

## Required tests / validation

Each child carries its own `V-*` items and its own evidence obligations; this plan does not restate them.
At the Set level, the bare `python3 -m pytest` suite must pass on the MERGED result (not merely per lane),
with the actual summary line pasted. The two reconstructions and the collision case are OWNED BY `svacmz`
(its E-03/E-04) and are confirmed here by E-02 reading `svacmz`'s pasted evidence, never re-performed.
Reconstructions must be built in `tmp_path`: the measured runs live under `.aw/records/runs/`, which is
gitignored and absent in CI, so a test reading it would pass locally and fail everywhere else.

## Open questions

### OQ-01: Should the three spec amendments the children identified be made in a follow-on plan?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because all four children are conforming under the specs as they stand, and each raising child records its candidate amendment with the wording it would use (`skn8uk` OQ-01: generalize `7ckptx` R2.1 from "collect before scoring" to "score from the latest successful collection"; `ty7w6o` OQ-02: state in `7ckptx` R4 that the driver must record a host-initiated termination; `dy9ymn` OQ-01: name the zero-work class explicitly in `25kzda` 5.5's retryable list). Deliberately not bundled into this Set: amending an approved spec changes the contract every other plan is reviewed against, which is the highest-leverage change a run can make and should be authorized on its own merits rather than carried along by a defect fix. If the reviewer wants them, one follow-on plan declaring the two spec files is the cheapest route.
- Carrier-Declined: Each amendment is carried by the child that raised it, as that plan's own open question; this question merely ASKS whether the reviewer wants them bundled, and the answer costs a reviewer sentence rather than a future act. A self-carrier (`- Carrier: s0gnha`) was removed here for the same measured reason recorded on the spec row in Deferred: it resolves today and goes terminal at this plan's own finalize, where the post-cutover `error` tier would refuse the transition.

### OQ-02: Should E-03's two backlog transitions be a fifth child, given a runner retirement performs no parent item?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NON-BLOCKING because the act is small, the risk is bounded, and BOTH routes are safe once stated. The problem is structural rather than hypothetical: when `aw oc run` / `aw agy run` retires this orchestrator it skips the pre-transition E/V checkpoint by design (`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`), so E-03's checkbox is reported complete having been performed by nobody, and the two backlog items would silently keep their pre-Set statuses while the parent claims otherwise. That is the same class of loss the orchestrator coverage gate exists to catch, and the gate does not catch this one, because the work IS declared on the parent rather than merely unowned. Three shapes are available and the reviewer should pick one: (a) LEAVE IT HERE with the gate paragraph's explicit warning that an operator must perform E-03 by hand after a runner retirement, which is what this plan now does and which costs one manual step; (b) AUTHOR A FIFTH CHILD owning the two `aw backlog set` calls, which makes the act agent-performed and gated but spends a whole turn on two commands; (c) MOVE the transitions onto `svacmz`, which already runs last and already has a turn, at the cost of mixing record-keeping into a plan whose Scope says "tests and evidence only". The recommendation is (c) if the reviewer wants it gated and (a) otherwise; it is recorded rather than chosen because it trades ceremony against safety and that is a maintainer judgement.
- Carrier-Declined: The obligation is DISCHARGED BY THIS PLAN'S OWN GATE, which now states the manual step an operator must take after a runner retirement, so nothing is pending on a future artifact. Should the reviewer prefer shape (b) or (c), that is a new plan or an edit to `svacmz` made at that point, not an obligation this plan hands off.

### OQ-03: `dy9ymn` bounds its retry by a budget nothing consumes; does it gain `executed:xipfy1`, or count attempts itself?

- Blocking: yes
- Status: resolved
- Owner: maintainer
- Finding: PR-005
- Resolution or deferral rationale: RESOLVED 2026-09-19 FROM THE REPOSITORY, NOT BY ASKING: SHAPE (b) IS ALREADY CHOSEN, IMPLEMENTED IN THE PLAN TEXT, AND CORRECT, so there was nothing left for a maintainer to decide. BOTH PREMISES OF THIS QUESTION EXPIRED BETWEEN THE TWO REVIEWS, and the timestamps are what make that verifiable rather than asserted: this parent was reviewed at HEAD `24a3c262` and its lane merged at `249e6a8d` 12:53, while `dy9ymn`'s own round 1 landed at `27d399ed` 13:35, FORTY-TWO MINUTES LATER. So this question describes a version of `dy9ymn` that no longer exists.
  PREMISE 1, THAT `dy9ymn` E-04 HAS NO EXECUTABLE FORM: FALSE AT HEAD. Measured by reading E-04 at both commits. At `24a3c262` it said "Use the run's already-resolved value ... and introduce NO second retry knob", with `grep -c integration_attempts` = 0, which is exactly the unbuildable instruction this question reports. At HEAD that wording is GONE and `grep -c integration_attempts` = 7: E-04 now says "COUNT IT ON THE ITEM, MIRRORING THE SHIPPED PRECEDENT, and do NOT reach for `plan_retry`", names the per-item key, and explains that this needs no ledger and adds no knob. `dy9ymn`'s own review recorded the same correction as its item (3). THAT IS SHAPE (b), already taken.
  PREMISE 2, THAT `xipfy1`'s SUBSTRATE QUESTION IS STILL OPEN: FALSE, AND IT WAS ALREADY FALSE WHEN THIS QUESTION WAS WRITTEN. `xipfy1` OQ-03 reads `- Status: resolved` at HEAD AND at `24a3c262`, the parent's own review commit: the maintainer settled it on 2026-09-10 by choosing option (b), spend the budget in the drivers' own `state.json`/`events.jsonl` substrate, reusing the shipped helpers' SEMANTICS without calling the ledger-bound functions. So shape (a)'s stated cost (inheriting an open blocker) never applied, and the maintainer's 2026-09-10 ruling and `dy9ymn`'s 13:35 correction are THE SAME ANSWER reached independently: count in the drivers' own state, not in a ledger.
  THE UNDERLYING CODE FACT IS CONFIRMED UNCHANGED, because it is the one thing here that was true and must not be silently dropped. Re-measured at HEAD: `grep` for `options.*retry_budget`, `get("retry_budget")` and `["retry_budget"]` across `agent_workflows/` still returns NOTHING, `plan_retry`/`retry_budget_remaining` still have zero callers outside `run_recovery.py`, `run_engine`/`RunEngine` appear 0 times in both drivers, and 0 of 214 run directories contain a `ledger.jsonl`. So the budget genuinely has no spend counter, and `xipfy1` genuinely still owns wiring one generally. What is false is only the INFERENCE that this leaves `dy9ymn` unexecutable: the precedent it now copies is shipped and verified present (`runner_shared` reads `int(options.get("integration_retry_limit", DEFAULT_INTEGRATION_RETRY_LIMIT))`, computes `attempts_used = int(item.get("integration_attempts", 0)) + 1`, and writes it back onto the item), and a second per-item counter for a different failure class is what `integration_attempts` already is.
  NO EDIT TO `dy9ymn` IS NEEDED and none was made: it is `Readiness: go-pending-approval` with no gating finding, its OQ-04 already records the `xipfy1` relationship and the non-collision argument, and adding an `executed:xipfy1` edge now would block a ready plan on a PREFERENCE - the same reasoning by which `xipfy1`'s own OQ-01 deliberately declined a hard edge. THE ONE RESIDUAL, recorded so it is not lost: if `xipfy1` later routes all retries through `plan_retry`, the zero-work tally should be migrated or deliberately kept as the zero-work-specific counter; that is `dy9ymn` OQ-04's non-blocking residual question and needs no action now.
  ORIGINAL FINDING, PRESERVED BECAUSE IT WAS RIGHT WHEN WRITTEN: BLOCKING, because the answer decides whether a child of this Set is executable at all and the repository cannot supply it. RAISED AT REVIEW AS A CROSS-PLAN FINDING the parent must surface. MEASURED: `--retry-budget` is parsed, range-validated through `run_recovery.validate_retry_budget`, and frozen into run options, and the frozen value IS READ BACK BY NOTHING. Searching `agent_workflows/` for `options.*retry_budget`, `get("retry_budget")` and `["retry_budget"]` returns no match, and `run_recovery.plan_retry` / `retry_budget_remaining` have zero callers outside their own module. The contrast that proves the absence is real rather than a search artifact: the sibling knob IS read back, as `int(options.get("integration_retry_limit", ...))` in `runner_shared`. So `dy9ymn` E-04's instruction to re-queue "bounded by the existing retry budget", to "use the run's already-resolved value" and to "introduce NO second retry knob" has no executable form today: its executor finds nothing to spend and must either BUILD the consumption path or ADD the knob the item forbids. Building it is `xipfy1`'s declared scope (`approved`, `Blocks-Release: next`, sharing three of `dy9ymn`'s four `Scope-Paths`), and `xipfy1`'s own review escalated an unresolved BLOCKER that its helpers require a `RunEngine` over a `ledger.jsonl` no driver run writes, so the substrate question is open there too. Neither plan cites the other. NON-BLOCKING for THIS plan because the parent contributes no code and the defect is `dy9ymn`'s; it is recorded here because the parent sequences the Set and an executor reaching `dy9ymn` would otherwise discover it mid-turn. THE THREE SHAPES: (a) give `dy9ymn` an `executed:xipfy1` edge, honest but it inherits `xipfy1`'s open BLOCKER and may stall the Set; (b) let `dy9ymn` count zero-work attempts on the item itself, bounded by a re-read of the frozen value, which contradicts its own no-second-counter instruction and spec `25kzda` 5.5's precedence and so needs the maintainer's authorization; (c) narrow `dy9ymn` to the PREDICATE plus the event and leave the re-queue to `xipfy1`, which keeps both plans conforming at the cost of not closing the measured cascade until `xipfy1` lands. Not resolved by this review: `dy9ymn` and `xipfy1` are outside its ledger, and choosing between (a), (b) and (c) is a sequencing and risk decision the maintainer owns. THIS QUESTION HOLDS THE SET: it is `- Blocking: yes`, so `aw ipd lint` refuses this plan at every checkpoint until it is answered, which is the intended effect. Answering it costs one sentence naming (a), (b) or (c); executing `dy9ymn` without an answer costs a turn that discovers the gap mid-flight.
- Carrier: dy9ymn

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted evidence that all FOUR children are `executed` (their plan files' `- Status:` and their location under `.aw/records/plans/executed/`), that `dy9ymn` was dispatched only after `ty7w6o` reached `executed`, and that `svacmz` was dispatched only after all three siblings did (cite the run record or the lifecycle commits). Plus a statement that this plan performed none of the children's deliverables.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: QUOTE, from `svacmz`'s executed plan file, the actual `Observed evidence` blocks of its `V-01` (the five constants' real values beside their pre-Set values, with file and symbol for each), its `V-02` (pin output plus `git diff` for both pin files), its `V-03` (the SHAPE A reconstruction, both halves: disposition AND no sibling `dependency-blocked`), and its `V-04` (SHAPE B plus the collision case plus the four-condition general argument). State explicitly for each whether the block is non-empty and contains OUTPUT rather than an assertion. If any of the four is empty or is a claim without output, record this item FAILED and do not complete the Set; do NOT substitute a re-run performed here, because that would make this plan the observer of its own receipt check.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `git diff` (or `aw backlog check` plus the item files) showing `yxfw4k`'s and `x7wfyx`'s transitions, each with a tool-written history entry. Must show `x7wfyx` at `graduated` and NOT `done`, and must show its `- Blocks-Release:` still present and unchanged. If `yxfw4k` was closed `done`, paste the gate escape that made the close legitimate (the `From-Backlog` handoff, the cited `--evidence`, or the explicit `--blocks-release -`), since `aw backlog set done` fails closed on a release-blocking item without one. Plus the full bare `python3 -m pytest` summary line on the merged result.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This Set is release-blocking (`Blocks-Release: next`, inherited from backlog `yxfw4k` per the
every-live-bug-gates-the-release rule) and must not be executed before explicit human approval, which
`- Status:` records and which no agent may write on the maintainer's behalf.

THIS IS AN ORCHESTRATOR AND HOLDS NO PRODUCT WORK OF ITS OWN. Its three items are sequencing (E-01), a
receipt check over `svacmz`'s evidence (E-02), and the Set-level backlog transitions (E-03); every
product deliverable belongs to a child. If an executor finds itself needing to make a product change
here, that is a missing child and must be authored as one, not parked on this plan, because a runner
retiring this plan SKIPS the pre-transition E/V checkpoint
(`ipd_lifecycle.ROLLUP_OMITTED_GATES['pre-transition-ev-checkpoint']`) on the premise that a parent's
items are performed by nobody.

READ THAT CONSEQUENCE PRECISELY, because it bears on E-03 and was corrected at review. The coverage gate
refused this Set once already for exactly this reason and `svacmz` was authored in response. E-02 and
E-03 as they now stand are still items NO AGENT PERFORMS when a runner retires this plan: a rollup
retirement performs every gate in `ROLLUP_SHARED_GATES` and skips the E/V checkpoint, so their checkboxes
would be reported complete unperformed. E-02 is acceptable in that light because it is a pure receipt
check whose underlying work `svacmz` already performed and evidenced under its own gate, so nothing is
lost if the receipt check itself is skipped. E-03 IS NOT in that category: a backlog transition is a real
act with a real gate. SO AN OPERATOR RETIRING THIS PLAN THROUGH A RUNNER MUST PERFORM E-03 BY HAND (two
`aw backlog set` calls) OR CONFIRM IT WAS ALREADY DONE, and must not read a retired parent as evidence
that the two items were transitioned. That is recorded as OQ-02 for the reviewer to settle rather than
resolved here, because the alternative (a fifth child owning two `aw backlog set` calls) may be more
ceremony than the act deserves and that is the maintainer's call.

EXECUTION CONTRACT (applies to every child). Commit only the files the executing plan changed,
path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`/bare, and never push. Before every
commit run `git diff --cached --name-only` and `git restore --staged` anything not yours: this is a
SHARED CHECKOUT with concurrent workers, and a failed pre-commit hook can leave paths in the index you
never staged, so re-verify after any failed attempt. Prefer `aw commit <plan> -- <paths>`. When reporting
tests passed, paste the ACTUAL bare `python3 -m pytest` output; do not add `-n0`, a second `-q`, or
`-p no:randomly`.

POST-GATE LIFECYCLE MOVE. Do not report the Set complete or move this plan to
`.aw/records/plans/executed/` until every child is `executed`, `aw ipd lint --phase pre-transition`
reports conforming, and every `V-*` above carries concrete pasted evidence. On closing the source items:
`yxfw4k` may close once its defect is fixed and validated; `x7wfyx` must be set `graduated`, not `done`,
and its `Blocks-Release` must not be cleared.
