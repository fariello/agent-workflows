# IPD: Make finalize_precheck report the wedged finalize journal it is currently blind to

- Date: 2026-09-29
- Kind: child
- Concern: Two functions in `ipd_lifecycle` both answer "may this plan's finalize proceed", and they DISAGREE. `finalize` performs early crash recovery (`_early_recovery_result`) BEFORE its precheck, so it sees a finalize transaction journal wedged in `PHASE_UNKNOWN_OUTCOME` and refuses with `EXIT_CANNOT_RUN`. `finalize_precheck` never reads the journal at all and returns `EXIT_OK` "precheck passed" for the identical repository state. Any caller that uses `finalize_precheck` DIRECTLY as a go/no-go oracle is therefore told GO by the very surface whose job is to predict the apply. Backlog `bn58ha`, measured, reproduced independently in this lane on 2026-09-29.
- Scope: IN: teach `ipd_lifecycle.finalize_precheck` to read the finalize journal and REFUSE for the ONE phase the transaction refuses on (`PHASE_UNKNOWN_OUTCOME`), carrying a stable finding id so no caller has to substring-match prose; a behavioral regression test proving precheck and `finalize` now agree on that state; a control test proving the three NON-refusing phases are unchanged; one CHANGELOG line. OUT: changing ANY behavior of `finalize`, `_finalize_transaction`, or `_early_recovery_result`; changing what wedges a journal into `unknown-outcome` (that is `cnf7gw`/`4er1ev`'s territory, already executed); adding a REMEDY or auto-clear for a wedged journal (see the deferred section, `hf76th`); the rollup path `retire_orchestrator`, which already shares `_early_recovery_result` and needs no change; and `runner_shared.compute_scope_reconciliation`, whose existing `exit_code != 0` branch absorbs the new refusal with no edit.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: bn58ha
- Blocks-Release: next
- Set: bn58ha
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: hlv737

## Workflow history

- 2026-09-29 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `bn58ha`. The item's measurement was INDEPENDENTLY REPRODUCED in this lane before authoring (see F-1), not transcribed: a scratch git repo, `begin`, in-scope work, then `_rollback_precommit` forced to fail under `fault_injection="after_move"` to wedge the journal, then both surfaces called on the identical state. Precheck returned exit 0 "precheck passed"; `finalize` returned exit 2 naming the unknown-outcome journal. Control cases were also measured to bound the fix (F-4, F-5, F-6). Measuring the `committed-incomplete` control surfaced a SEPARATE defect in `finalize` itself (F-11: a no-`--apply` preview performs the post-commit resume and consumes the single-use begin receipt, confirmed through the real CLI), which is out of scope here and was filed as backlog `hernns` with its transcripts rather than folded into this plan.

## Goal

Make `finalize_precheck` and `finalize` give the SAME verdict for a plan whose prior finalize attempt
left the transaction journal in `unknown-outcome`, by teaching the precheck to read the journal and
refuse on exactly that phase, with a stable finding id a caller can branch on.

The user-visible property: a driver or operator that previews with `finalize_precheck` before applying
is never told "precheck passed" for a plan whose apply will refuse with exit 2. A preview that cannot
predict the apply is worse than no preview, because it is trusted.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the disagreement before changing anything

- [ ] E-01 Write the FAILING regression test FIRST, in `tests/test_ipd_lifecycle_cli.py`, asserting the two surfaces AGREE. Wedge the journal into `PHASE_UNKNOWN_OUTCOME` using the technique the existing test `test_unrecoverable_failures_and_unknown_outcome` already uses (`mock.patch.object(LC, "_rollback_precommit", return_value=(False, ...))` plus `fault_injection="after_move"`), assert `LC.read_finalize_journal(...)["phase"] == LC.PHASE_UNKNOWN_OUTCOME` as the PRECONDITION, then call `LC.finalize_precheck` and `LC.finalize(..., apply=False)` on the SAME state and assert both are nonzero. Run it and paste the FAILURE, which must show precheck returning 0 while finalize returns 2. Do NOT edit `ipd_lifecycle.py` in this item: the failure is the evidence the defect is real and that the test bites, and a test written after the fix cannot prove either.
  - Depends on: none
  - Expected outcome: one new test that FAILS at unmodified HEAD with an assertion naming precheck's exit 0, and whose precondition assertion proves the journal really is in `unknown-outcome` (so a future change to what wedges it makes this test fail loudly rather than pass vacuously).
  - Execution state: pending

### Task group 2: close the asymmetry

- [ ] E-02 Add the journal read to `ipd_lifecycle.finalize_precheck`. Site it AFTER the `- Id:` resolution (the function needs `plan_id` to find the journal, and it already refuses `EXIT_CANNOT_RUN` when the id is absent) and BEFORE the begin-receipt check, mirroring `finalize`'s own ORDER, where `_early_recovery_result` runs before `finalize_precheck` is called at all. Refuse for `PHASE_UNKNOWN_OUTCOME` ONLY, with `EXIT_CANNOT_RUN` (2) so the precheck's code matches the code `finalize` returns for the same state, and reuse `finalize`'s existing refusal wording (which names the plan id and the absolute journal path to clear) rather than composing a second message: the journal path is the only part a human can act on. Leave every other phase falling through to the existing logic untouched, and do not read the journal a second time anywhere.
  - Depends on: E-01
  - Expected outcome: `finalize_precheck` returns `(2, <the unknown-outcome message>, evidence, findings)` for a wedged plan, and returns exactly what it returns today for every other state. E-01's test passes.
  - Execution state: pending

- [ ] E-03 Add a module-level finding-id constant for this refusal beside the existing `FINDING_RECEIPT_*` family, and emit it in E-02's findings tuple. Follow the convention that family documents: a short token like the two `receipt-*` ids, NOT a sentence, because unlike `FINDING_RECEIPT_STALE` there is no pre-existing shipped string being preserved here, so nothing forces the sentence form. The reason this is its own item rather than a line inside E-02: `runner_shared`'s comment on `RETRYABLE_FINALIZE_FINDING_TEXTS` records that keying a driver decision on refusal PROSE is the fragile coupling the repository is trying to retire, and a new refusal class that ships with no id perpetuates it. Do NOT add any consumer of the new id in this plan (no runner branch, no retry classification); minting the id is the deliverable, and a consumer is a separate decision with its own risk.
  - Depends on: E-02
  - Expected outcome: one new constant, exported at module level, present in the findings tuple of the new refusal and absent from every other refusal. A caller can distinguish "wedged journal" from "stale receipt" and from "no receipt" without matching prose.
  - Execution state: pending

- [ ] E-04 Add the CONTROL test, in the same file, proving the fix is narrow: for each of the three journal phases `finalize_precheck` must NOT refuse on, assert it still returns what it returns today. The three, with the behavior each must keep: a PRE-COMMIT phase (`PHASE_PREPARED`, measured today as precheck exit 0, because `_finalize_transaction` ROLLS IT BACK and proceeds rather than refusing); `PHASE_COMPLETE` (measured exit 0, because the transaction CLEARS a stale complete journal and proceeds); and NO journal at all (the ordinary path). `PHASE_COMMITTED_INCOMPLETE` is deliberately absent from this list AND from E-02's refusing set: F-6 measures the two surfaces already disagreeing in the opposite direction there, and F-11 measures the `finalize` side of that case being itself defective, so asserting either verdict would pin a behavior backlog `hernns` may change. This is the item that stops E-02 becoming a blanket "any journal refuses", which would break the resume and rollback paths that are the whole reason the journal exists.
  - Depends on: E-02
  - Expected outcome: three control assertions passing, each pinning a NON-refusal, so a later widening of E-02's condition fails a test instead of silently wedging every recoverable transaction.
  - Execution state: pending

### Task group 3: record it and prove no regression

- [ ] E-05 Add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, in the user-facing register with no em or en dashes, saying that a preview of a plan whose previous finalize was interrupted ambiguously now reports the problem instead of reporting that the transition may proceed. Then establish and compare the suite baseline: run `python3 -m pytest` BARE at the unmodified HEAD of this lane BEFORE any source edit and record the summary line plus the full FAILED set, run it again after E-01 through E-04, and account for every difference. The baseline half must be performed FIRST, before E-01 writes its test, because a baseline taken afterwards cannot distinguish a failure this plan caused from one it inherited; the repository has at least one known pre-existing failure, so "the suite is green" is not the expected result and must not be asserted.
  - Depends on: E-04
  - Expected outcome: one CHANGELOG entry describing the fix in user terms, and two pasted bare-suite summary lines with their FAILED sets plus an explicit statement of whether the sets are identical.
  - Execution state: pending

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
| F-4 | measured control: `PHASE_PREPARED` | A pre-commit journal does NOT make `finalize` refuse. Measured: with a hand-written `prepared` journal, `finalize_precheck` -> 0 and `finalize(apply=False)` -> 0. Correct, because `_finalize_transaction` ROLLS BACK a pre-commit phase and proceeds to a fresh attempt. So E-02 must refuse on `unknown-outcome` alone; a blanket "journal present = refuse" would break the rollback path. Pinned by E-04. |
| F-5 | measured control: `PHASE_COMPLETE` | A stale `complete` journal also does NOT make either surface refuse (measured: precheck 0, `finalize(apply=False)` 0). The transaction CLEARS it and proceeds. Pinned by E-04 for the same reason as F-4. |
| F-6 | measured control: `PHASE_COMMITTED_INCOMPLETE` | THE MEASUREMENT THAT CONTRADICTS THE OBVIOUS GENERALIZATION, and the reason this phase is excluded from E-02. Wedging `committed-incomplete` (post-transition lint forced to raise) leaves the plan MOVED into `executed/` with the lifecycle commit already made. Calling `finalize` again on the executed path SUCCEEDS: it RESUMES, reports `finalized abc123 -> executed at <sha>`, clears the journal and consumes the receipt. Calling `finalize_precheck` on that same path returns exit 1 "pre-transition gate did NOT conform (legacy/not evaluated)", because the plan is already terminal. So for THIS phase the two surfaces already disagree in the OPPOSITE direction (precheck refuses, finalize succeeds), and "make them agree" would mean making the precheck return OK for an already-committed transaction. That is a materially different change with a real fail-open risk and is not what the item asks for. Excluded from E-02's refusing set, and also from E-04's control set, because pinning either verdict here would freeze a behavior F-11 shows is itself defective. |
| F-11 | `finalize`'s `apply` flag vs `_early_recovery_result` | A SEPARATE DEFECT FOUND WHILE MEASURING F-6, filed rather than fixed here. Because early recovery runs BEFORE the `if not apply:` arm, a `committed-incomplete` journal makes `finalize(apply=False)` PERFORM the resume: measured three times (twice in-process, once through the real `cli.main(["ipd","finalize", ...])` with NO `--apply`), each time reporting `finalized abc123 -> executed at <sha>`, exit 0, journal cleared and the single-use begin receipt CONSUMED, byte-identical to the `apply=True` outcome. `cli.py` documents `--apply` as "Perform the transition (default: preview the precheck)", so a preview performs a terminal receipt-consuming transition. This is OUT OF SCOPE here (it is a defect in `finalize`, which this plan deliberately does not touch) and is filed as backlog `hernns` with the transcripts. It is recorded in this plan because it is WHY F-6's disagreement must not be "fixed" by making the precheck agree with a behavior that is itself wrong. |
| F-7 | `runner_shared.compute_scope_reconciliation` | The ONE in-tree caller that uses `finalize_precheck` as an oracle, and it is SAFE BOTH BEFORE AND AFTER. It already branches `if exit_code != 0: return {}, {}` with the comment that "the finalize call below will surface the same refusal authoritatively". Measured on a wedged plan today: it returns `({}, {})` because the precheck happens to pass and produces an empty delta only by luck of the fixture. After E-02 it returns `({}, {})` deterministically through the refusal branch. So E-02 needs no edit in `runner_shared.py`, which is why that file is NOT in `- Scope-Paths:`. |
| F-8 | `runner_shared.driver_finalize` | WHY THE OPERATOR IS NOT MISLED TODAY, which bounds the priority honestly. The driver calls `compute_scope_reconciliation` (F-7) and then shells out to `aw ipd finalize ... --apply`, which goes through `finalize` and therefore through `_early_recovery_result`. And `ipd_lifecycle.run_finalize`, the CLI entry for a preview WITHOUT `--apply`, also calls `finalize`, not `finalize_precheck`. So no shipped CLI or driver path is currently fooled. The exposure is to a DIRECT `finalize_precheck` caller, which is exactly what `compute_scope_reconciliation` is and what any future preview surface would be. |
| F-9 | `ROLLUP_OMITTED_GATES` | The rollup transition `retire_orchestrator` OMITS the precheck entirely (no begin receipt exists for an orchestrator) but SHARES `early-crash-recovery` as an explicitly enumerated gate in `ROLLUP_SHARED_GATES`. So the rollup path already refuses a wedged journal through the shared helper and is unaffected by this plan. Named so a reviewer does not expect a rollup-side change. |
| F-10 | `tests/test_ipd_lifecycle_cli.py` | The wedging technique E-01 needs ALREADY EXISTS in this file, in `test_unrecoverable_failures_and_unknown_outcome`, which patches `_rollback_precommit` to fail under `fault_injection="after_move"` and then asserts the journal phase and that a REINVOCATION of `finalize` fails closed. E-01 therefore reuses a proven fixture rather than inventing one, and the new test is the missing half of that existing test: it already pins `finalize`'s behavior on a wedged journal and never asks the precheck. |

## Proposed changes (ordered, validatable)

1. E-01: add the failing agreement test to `tests/test_ipd_lifecycle_cli.py` and paste its failure at unmodified HEAD.
2. E-02: add the journal read to `finalize_precheck`, after the id resolution and before the receipt check, refusing `EXIT_CANNOT_RUN` for `PHASE_UNKNOWN_OUTCOME` alone with `finalize`'s existing wording.
3. E-03: mint the finding-id constant beside the `FINDING_RECEIPT_*` family and emit it in that refusal, adding no consumer.
4. E-04: add the three control assertions pinning the non-refusing phases.
5. E-05: one user-facing CHANGELOG line, plus the before and after bare-suite comparison.

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

## Required tests / validation

- `python3 -m pytest tests/test_ipd_lifecycle_cli.py` for the focused surface, run BARE. Paste the summary line and the new tests' names.
- The agreement test (E-01) must be shown FAILING at unmodified HEAD before E-02, and passing after. The failure must show precheck's exit 0, which is the defect itself; a test that only ever passes proves nothing.
- The control tests (E-04) must be shown to BITE: temporarily widen E-02's condition to refuse on ANY journal, paste the resulting control-test FAILURES, then restore and paste the passes. A control test that cannot fail is not a control.
- `python3 -m pytest` bare for the whole suite, with a before and after comparison of the FAILED set so a pre-existing failure is not miscounted as a regression.
- An end-to-end check that the two surfaces now agree on the CLASS and not merely on "nonzero": paste both exit codes (both must be 2) and both messages, and confirm the precheck's message names the same journal path `finalize`'s does.
- `aw ipd lint --phase pre-transition` on this plan must report conforming before any terminal transition.

## Spec / documentation sync

No spec is AMENDED and no `.spec.md` path is declared in `- Scope-Paths:`. Two specs mention
`finalize_precheck` and both remain accurate after this change. Spec `25kzda` says
"`ipd_lifecycle.finalize_precheck` applies UNCHANGED afterwards" in the context of what a lane does not
relax, which this plan does not weaken: it adds a refusal and removes none. Spec `llbr2b` (to-review)
lists the precheck's conditions in its Section 3.3 table and classifies a stale receipt as C-4
INVARIANT; the condition this plan adds is likewise an invariant, not a policy key, and adding it does
not change that spec's classification or its exclusion sentence. When `llbr2b` is next revised its
condition list may gain a row for the wedged journal; that is an editorial refresh of a to-review spec
and not a contract change this plan must make, so no spec edit is declared. The only documentation this
plan changes is the in-code comment at the new gate plus one user-facing `CHANGELOG.md` line.

## Open questions

### OQ-01: should the precheck return exit 2, matching `finalize`, or exit 1 as a "finding"?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; exit 2 is chosen and the plan is executable as written. The argument for 2 is agreement, which is the whole point of the fix: `finalize` returns `EXIT_CANNOT_RUN` for this state from both its gate sites, so a precheck returning 1 would make the two surfaces agree on "no" while disagreeing on the CLASS, and `runner_shared`'s comment on `RETRYABLE_FINALIZE_FINDING_TEXTS` records exactly how much damage a mis-signalled class does (it notes the driver "treats every nonzero identically", which is a limit, not a licence to be sloppy about which nonzero). The argument for 1 is that the precheck emits a findings tuple and 1 is its findings code; that is answered by the precheck already documenting "2 means cannot-run" in its own docstring and already returning 2 for an unusable `base_head`, which is the same class of "this cannot be computed" condition. Recorded so a reviewer can overrule the code choice without reopening the design.
- Carrier-Declined: A DECIDED DESIGN CHOICE WITH NO RESIDUE. The plan commits to exit 2 and both alternatives are fully implemented by a one-token change in E-02, so whichever the reviewer picks, nothing is left undone when this plan executes. It is asked because a reviewer may hold a different view of the exit vocabulary, not because work is outstanding, so filing a carrier would create an item whose content is "someone might prefer 1".

### OQ-02: should the two copies of the wedged-journal refusal in `finalize` be collapsed into one?

- Blocking: no
- Status: open
- Owner: reviewer
- Resolution or deferral rationale: NOT blocking; the answer taken is NO, leave both. F-3 records that `_early_recovery_result` and `_finalize_transaction`'s resume arm each carry the refusal. That looks like duplication worth removing, and it is deliberately not removed: the early one runs before any lock is taken so a refusal has no side effect, and the transaction's one runs INSIDE the exclusive lock, where it is the last check before mutation and catches a journal that appeared between the two. Deleting either would remove a real gate to satisfy a tidiness preference, and this plan's own change ADDS a third site rather than consolidating, which a reviewer should see stated plainly rather than discover. If consolidation is wanted it is its own plan with its own concurrency argument.
- Carrier-Declined: A REJECTED REFACTOR, not outstanding work. The plan's position is that the two sites are both load-bearing and should stay, so there is nothing left to do when it executes. Filing a carrier would record "consider merging two deliberately separate gates" as an obligation, which inverts the decision taken here; if a reviewer disagrees, the consolidation belongs in its own plan where the concurrency argument can be made properly.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the new test's name and full source, and paste its FAILING output against unmodified `ipd_lifecycle.py`. The failure must show `finalize_precheck` returning exit code 0 while `finalize` returned 2. Confirm the test asserts the journal phase as a PRECONDITION (quote that assertion) so it cannot pass vacuously if the wedging technique stops wedging, and confirm it drives the real functions in a real temporary git repository rather than stubbing either.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the diff of the added gate in `finalize_precheck`, showing it sits after the `- Id:` resolution and before the begin-receipt read. Paste a transcript on a wedged plan showing `finalize_precheck` now returns exit 2 with the message naming the plan id and the absolute journal path, beside `finalize`'s return on the same state, and state explicitly that both codes are 2 and both messages name the same path. Confirm by quoting the unchanged lines that `finalize`, `_early_recovery_result` and `_finalize_transaction` were NOT modified.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: quote the new constant's definition and its docstring comment, and paste the findings tuple actually returned by the new refusal showing the id present. Paste the findings tuples from the no-receipt, already-finalized and stale-receipt refusals showing the new id ABSENT from each, so the ids stay distinct. Paste a search proving no consumer was added (no branch anywhere keys on the new constant), since adding one is explicitly out of scope.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the three control assertions' source and their passing output. Then paste proof they BITE: temporarily widen E-02's condition to refuse on any non-None journal, paste the resulting FAILURES naming which controls broke, restore, and paste the restored passes. Confirm `PHASE_COMMITTED_INCOMPLETE` is absent from both the refusing set and the control set, and state the F-6 plus F-11 reason in one line (the `finalize` side of that case is itself under question as backlog `hernns`) so the exclusion is on the record rather than looking like an oversight.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the added CHANGELOG line and confirm it is under `## 2.0.0 (pending)`, is user-facing, and contains no em or en dash. Paste the BARE `python3 -m pytest` summary line from before any edit and after the change, plus the FAILED set for each, and state whether the two FAILED sets are identical; any new failure must be fixed or explained with evidence. Also paste the focused `python3 -m pytest tests/test_ipd_lifecycle_cli.py` summary. Confirm no flag was added to the bare invocation (no `-n0`, no extra `-q`, no `-p no:randomly`) and that the pre-change baseline was captured before E-01's test was written.
  - Observed evidence:
  - Result: pending

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
