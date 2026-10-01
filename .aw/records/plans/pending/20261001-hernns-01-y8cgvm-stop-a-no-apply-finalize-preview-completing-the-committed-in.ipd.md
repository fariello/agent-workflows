# IPD: Stop a no-apply finalize preview completing the committed-incomplete transaction and spending the begin receipt

- Date: 2026-10-01
- Kind: child
- Concern: `aw ipd finalize <plan>` WITHOUT `--apply` is documented as a preview (`cli.py` registers `--apply` as "Perform the transition (default: preview the precheck)"), and on the ordinary path it is one. But when a prior attempt left the finalize transaction journal in `PHASE_COMMITTED_INCOMPLETE`, `ipd_lifecycle.finalize` runs `_early_recovery_result` BEFORE it ever reaches its `if not apply:` arm, that helper calls `_resume_post_commit`, and the resume COMPLETES the transaction: it clears the journal and CONSUMES the single-use begin receipt. The preview arm is never reached. Backlog `hernns`, measured; reproduced independently in this lane on 2026-10-01 and found to affect two MORE preview surfaces the item did not name, including `aw set executed --dry-run`, whose `--dry-run` contract is a stronger promise than `--apply`'s default.
- Scope: IN: thread an `apply` flag through `ipd_lifecycle._early_recovery_result` so that, when false, the `PHASE_COMMITTED_INCOMPLETE` arm REPORTS the recoverable state and the exact command that would complete it instead of performing it; forward the flag from BOTH call sites (`finalize` and `retire_orchestrator`), which share that helper by construction; mint a stable finding id for the new report so no caller branches on prose; surface that id as a diagnostic on `aw ipd finalize`'s EXIT_OK preview, which today drops it on all three output modes; behavioral regression tests covering `finalize`, the real CLI, `aw set executed --dry-run` and the rollup preview; one CHANGELOG line. OUT: changing the `apply=True` resume in ANY way (it stays "RESUMED, never reverted"); changing `PHASE_UNKNOWN_OUTCOME`'s existing refusal, which already fails closed identically for both flag values; `finalize_precheck`, whose own blindness to a wedged journal is `bn58ha`/`hlv737`'s subject and is deliberately untouched here; adding any auto-clear or remedy for a wedged journal; and `runner_shared.driver_finalize`, measured passing `--apply` unconditionally so no driver path changes behavior.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: hernns
- Blocks-Release: next
- Set: hernns
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: y8cgvm

## Workflow history

- 2026-10-01 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored from backlog `hernns`. The item's measurement was INDEPENDENTLY REPRODUCED in this lane before authoring rather than transcribed (F-1): a scratch git fixture, `begin`, in-scope commit, then the `post-transition` lint forced to error to wedge the journal, then `finalize` called on the resulting `executed/` path with `apply=False`. Two no-apply trials and one apply trial produced byte-identical messages, journals cleared and receipts consumed; the real `cli.main(["ipd","finalize",...])` with NO `--apply` did the same. Measurement then went BEYOND the item in two ways that changed the plan's shape. FIRST, two further preview surfaces reach the resume: `aw set executed <plan> --dry-run` and `aw ipd set executed <plan> --dry-run` both map `--dry-run` to `apply=False` through `status_set._delegate_plan_executed_to_finalize` and both were measured completing the transaction and consuming the receipt (F-7). That matters because `--dry-run` promises more than a defaulted `--apply` does, so the item understated the defect. SECOND, `retire_orchestrator` shares the same helper and has the same ordering (F-8), so a one-sided fix in `finalize` would leave the rollup preview defective and put the two transition paths back on the drift surface that `ROLLUP_SHARED_GATES` exists to keep them off. The fix direction was PROTOTYPED and measured end to end (F-5, F-6): preview reports and preserves the receipt, a subsequent `--apply` still resumes successfully, and the BARE suite is unchanged at `3531 passed, 2 skipped` before and after, so no shipped test depends on a preview performing the resume. Prototyping also surfaced F-9, that the new finding id is DROPPED on all three output modes at EXIT_OK, which is why E-05 exists.

## Goal

Make a finalize invoked WITHOUT `--apply` keep the promise its own help text makes: observe, report,
change nothing. Specifically, a `committed-incomplete` journal must make a preview SAY that a prior
attempt's lifecycle commit already landed and name the command that would complete it, while leaving
the journal and the single-use begin receipt exactly as it found them.

The user-visible property: an operator or driver that previews in order to decide whether to apply has
not already applied. Today the decision and the act are the same invocation on this path, and the only
clue is that the message says `finalized` rather than `would finalize`.

The receipt is what makes this more than a wording defect. It is a SINGLE-USE token, and its being spent
twice is precisely what `finidem` (`ld8lb3`) had to work around when two actors contended for one. Here
a surface documented as read-only spends it, so the operator who previews and then lets the driver apply
has handed the driver a receipt that no longer exists.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: pin the defect before changing anything

- [ ] E-01 Write the FAILING regression test FIRST, in `tests/test_ipd_lifecycle_cli.py`, in `RollbackFailureSemanticsTests` (whose `_begin_and_work` / `_executed_path` / `_head` helpers and whose wedging technique this needs, see F-10). Wedge `PHASE_COMMITTED_INCOMPLETE` exactly as the shipped `test_postcommit_committed_incomplete_and_resume` does, by patching `ipd_lint.lint_file` to return a `DISPOSITION_ERROR` result for `checkpoint == "post-transition"` only. Assert as PRECONDITIONS that the journal phase really is `LC.PHASE_COMMITTED_INCOMPLETE` and that `LC.receipt_path_for(...)` EXISTS, so the test cannot pass vacuously if a future change stops producing that state. Then call `LC.finalize(..., apply=False)` on the `executed/` path and assert the preview changed NOTHING: the journal is still `committed-incomplete`, the receipt still exists, and `HEAD` is unmoved. Run it and paste the FAILURE. Do NOT edit `ipd_lifecycle.py` in this item.
  - Depends on: none
  - Expected outcome: one new test FAILING at unmodified HEAD, whose failure shows the preview having cleared the journal (`None`) and consumed the receipt. That failure is the evidence both that the defect is real and that the test bites; a test written after the fix proves neither.
  - Execution state: pending

- [ ] E-02 Add the second FAILING test, in the same class, driving the REAL CLI rather than the function, because the contract being violated is stated in `cli.py`'s help text and an in-process call cannot prove the shipped command violates it. Wedge the same state, then call `cli.main(["ipd","finalize","abc123","--dir",str(root),"--actor",...,"--message",...])` with NO `--apply`, and assert exit 0 together with the journal and receipt BOTH surviving. Keep this separate from E-01 rather than folding it in: E-01 pins the library contract and E-02 pins the operator-facing one, and F-7 shows the two can diverge per surface, so one test cannot stand in for the other.
  - Depends on: none
  - Expected outcome: a second test FAILING at unmodified HEAD, whose pasted failure shows the real CLI printing `finalized abc123 -> executed at <sha>` and consuming the receipt with no `--apply` anywhere in its argv.
  - Execution state: pending

- [ ] E-03 Add the THIRD failing test, in the same class, for the `--dry-run` surfaces F-7 measured, which the backlog item does not mention and which carry the stronger promise. Drive `cli.main(["set","executed","abc123","--dir",...,"--actor",...,"--message",...,"--dry-run"])` on the wedged state and assert the journal and receipt survive. Assert the SAME for the `["ipd","set","executed",...,"--dry-run"]` spelling, since `status_set._delegate_plan_executed_to_finalize` serves both and a test covering one leaves the other unpinned. This is its own item because it is a different entry point with a different flag contract (`--dry-run`, not a defaulted `--apply`), not a second assertion about the same one.
  - Depends on: none
  - Expected outcome: a third test FAILING at unmodified HEAD, with the pasted failure showing `--dry-run` reporting `aw set -> ipd finalize: finalized abc123 -> executed at <sha>` and consuming the receipt. This is the strongest single statement of the defect, because `--dry-run` means write nothing.
  - Execution state: pending

### Task group 2: close the defect in the one shared helper

- [ ] E-04 Thread the flag through `ipd_lifecycle._early_recovery_result` and forward it from BOTH call sites. Give the helper a keyword-only `apply: bool = True` parameter, and in its `PHASE_COMMITTED_INCOMPLETE` arm, when `apply` is false, return `EXIT_OK` with a message that (a) says the prior finalize is COMMITTED-INCOMPLETE, (b) names the already-landed `lifecycle_commit` from the journal, (c) states that nothing was changed and the begin receipt was NOT consumed, and (d) names the re-invocation with `--apply` that would complete it. Site the check BEFORE `acquire_finalize_lock`, so a preview takes no writer lock. Pass `apply=apply` from `finalize` AND from `retire_orchestrator`: both already call this helper and F-8 measures both having early recovery precede their own `if not apply:` arm, so fixing one would leave the other defective and would put a gate back on the drift surface `ROLLUP_SHARED_GATES` exists to keep it off. Default the parameter to `True` so any caller not updated keeps today's behavior, which is the fail-safe direction (a missed caller still resumes rather than silently previewing a transition the operator asked for). Leave `PHASE_UNKNOWN_OUTCOME` and the `return None` fall-through untouched. Record in a comment WHY the apply test cannot simply be moved ahead of early recovery in `finalize`: that would also skip the `unknown-outcome` refusal, so a preview of an ambiguously-wedged plan would report the ordinary precheck result and tell the operator to proceed, which converts this bug into a worse fail-OPEN one.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: E-01, E-02 and E-03 all pass. `finalize(..., apply=False)` and both `--dry-run` spellings report the recoverable state and leave the journal and receipt intact; `finalize(..., apply=True)` is byte-identical to today.
  - Execution state: pending

- [ ] E-05 Mint the finding id and make it VISIBLE on the preview surface. Add a module-level constant beside the existing `FINDING_RECEIPT_NEVER_ISSUED` / `FINDING_RECEIPT_ALREADY_FINALIZED` family, in the short-token form those two take (not the sentence form `FINDING_RECEIPT_STALE` takes, which that constant's own comment explains is preserving an already-shipped string), and emit it in E-04's findings tuple. Then fix the surfacing F-9 measured: `ipd_lifecycle.run_finalize`'s `EXIT_OK` branch calls `_emit` with no `diags`, so the id is dropped in human, `--json` and `--agent` modes alike, and a caller told to branch on an id it cannot observe is told nothing. Pass the findings through as diagnostics on that branch, choosing a severity that does NOT make a clean ordinary preview look refused. Add no consumer of the id (no runner branch, no retry classification): minting and surfacing it is the deliverable, and a consumer is a separate decision with its own risk.
  - Depends on: E-04
  - Expected outcome: one new module-level constant; the preview's findings tuple carries it; and the id is observable in all three output modes, while an ORDINARY clean preview (no journal) still emits no diagnostics and still reports clean.
  - Execution state: pending

- [ ] E-06 Add the CONTROL test, in the same class, proving the change is narrow in both directions. Assert that `apply=True` on a `committed-incomplete` journal STILL resumes: exit 0, journal cleared, receipt consumed, and `HEAD` unmoved (no second lifecycle commit). Assert that the RECOVERY REMAINS REACHABLE AFTER A PREVIEW by running `apply=False` and then `apply=True` on the SAME fixture and checking the second call succeeds; this is the item's central risk, since a preview that wedged the plan out of its own recovery would be worse than the defect. Assert that `PHASE_UNKNOWN_OUTCOME` still returns `EXIT_CANNOT_RUN` for BOTH flag values, pinning that this plan did not convert a fail-closed refusal into a permissive report. Assert that an ordinary preview with NO journal returns exactly what it returns today, with the new finding id ABSENT. Drive the unknown-outcome wedge with the shipped `_rollback_precommit` patch plus `fault_injection="after_move"` that `test_unrecoverable_failures_and_unknown_outcome` already uses.
  - Depends on: E-04, E-05
  - Expected outcome: four control assertions passing, so a later widening of E-04's condition into "any journal previews" fails a test rather than silently breaking the resume and rollback paths the journal exists to serve.
  - Execution state: pending

### Task group 3: record it and prove no regression

- [ ] E-07 Add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, in the user-facing register with no em or en dashes, saying that previewing a finalize of a plan whose previous attempt was interrupted after its commit landed now reports what it would do instead of silently completing it and spending the plan's begin receipt. Then establish and compare the suite baseline: run `python3 -m pytest` BARE at the unmodified HEAD of this lane BEFORE any source edit, record the summary line and the full FAILED set, run it again after E-01 through E-06, and account for every difference. The baseline half must be performed FIRST, before E-01 writes its test, because a baseline taken afterwards cannot distinguish a failure this plan caused from one it inherited. This lane's HEAD was measured GREEN at authoring (`3531 passed, 2 skipped, 3 warnings in 103.04s`, 208 deselected) and the prototype was measured green too (`3531 passed, 2 skipped`), so re-derive the number rather than inheriting it and treat ANY failure in the after-run as this plan's until the before-run shows the same node id.
  - Depends on: E-06
  - Expected outcome: one CHANGELOG entry in user terms, and two pasted bare-suite summary lines with their FAILED sets plus an explicit statement of whether the sets are identical.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The finding-id family this extends is `FINDING_RECEIPT_NEVER_ISSUED` (`"receipt-never-issued"`) and `FINDING_RECEIPT_ALREADY_FINALIZED` (`"receipt-consumed-already-finalized"`), both short tokens. `FINDING_RECEIPT_STALE` is deliberately a sentence because it NAMES an already-shipped string, and its own comment says so, which is why E-05 takes the token form.
- The journal phase vocabulary is a set of module constants: `PHASE_PREPARED`, `PHASE_MUTATING`, `PHASE_READY_TO_COMMIT`, `PHASE_COMMITTED_INCOMPLETE`, `PHASE_UNKNOWN_OUTCOME`, `PHASE_COMPLETE`, with `_PRE_COMMIT_PHASES` grouping the first three. Only `COMMITTED_INCOMPLETE` is touched here.
- Exit codes are `EXIT_OK = 0`, `EXIT_FINDINGS = 1`, `EXIT_CANNOT_RUN = 2`. The new preview report uses `EXIT_OK`, matching the existing preview arm's own `EXIT_OK`: a preview that successfully observed a recoverable state has not failed, and returning nonzero would make `runner_shared.compute_scope_reconciliation`'s `exit_code != 0` branch and `record_item_spec_edits`'s `rc != 0` branch treat an observation as a refusal.
- `_early_recovery_result` is SHARED BY CONSTRUCTION between `finalize` and `retire_orchestrator`, and `ROLLUP_SHARED_GATES` names `early-crash-recovery` explicitly so a test can fail when one path gains a gate the other lacks. That sharing is why E-04 changes one helper and forwards from two call sites rather than patching either path locally.
- A landed lifecycle commit is "RESUMED, never reverted" (the `finalize` docstring). This plan does not weaken that: it changes only WHICH INVOCATION is allowed to perform the resume, never whether a landed commit may be reverted.
- Test-authoring contract (`AGENTS.md`, GUIDING_PRINCIPLES P16): assert observable outcomes, never read production source with `inspect`/`ast`/regex, never assert on symbol censuses. Every test here drives real functions and the real CLI against real temporary git repositories and asserts on exit codes, messages, findings, journal phase, receipt existence and `HEAD`.
- Run the suite BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow'`. Do not add `-n0`, a second `-q` (which suppresses the summary line this plan must paste), or `-p no:randomly`.
- Lifecycle tests declare their execution role in `setUp` via `support.declare_execution_role(self)`; the lane exports `AW_EXECUTION_ROLE=worker`, which `AW-LIFECYCLE-ROLE-001` refuses, so a test (or a measurement harness) that does not declare the coordinator role cannot reach `begin`/`finalize` at all. This was hit while measuring F-1 and is why the fixtures in this plan follow the shipped classes.
- The journal lives under the GITIGNORED `.aw/state/runtime/transactions/` tree (`finalize_journal_path`), so nothing here touches a tracked path beyond the three in `- Scope-Paths:`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `ipd_lifecycle.finalize` vs its own `if not apply:` arm | THE DEFECT, REPRODUCED IN THIS LANE 2026-10-01 (not transcribed from the item). Scratch git repo, `begin`, in-scope commit, then `ipd_lint.lint_file` patched to return `DISPOSITION_ERROR` for `checkpoint == "post-transition"` only, which lands the journal in `committed-incomplete` with the lifecycle commit ALREADY made and the plan already moved to `executed/`. Precondition in every trial: journal `committed-incomplete`, receipt PRESENT, plan in `executed/`. Then `finalize(..., apply=False)` on the executed path returned `(0, 'finalized abc123 -> executed at c95ed99f7086 (actor opencode/test).')` and left journal `None` with the receipt GONE. Two independent no-apply trials were byte-identical to each other, and identical in exit code, message and receipt state to the `apply=True` trial, so the two invocations are indistinguishable from their output. `HEAD` was unmoved in all three, which is correct and is the narrowness F-4 records. |
| F-2 | `ipd_lifecycle.finalize` control flow | WHY IT HAPPENS. `finalize` calls `_early_recovery_result` BEFORE the precheck and therefore long before `if not apply:`. That helper's `PHASE_COMMITTED_INCOMPLETE` arm takes the finalize lock and calls `_resume_post_commit`, which calls `_complete_after_commit`, which clears the journal and consumes the receipt. Because the helper RETURNS a `FinalizeResult`, `finalize` returns it immediately and the preview arm is unreachable for this phase. The helper receives no `apply` argument at all today, which is exactly the missing input E-04 supplies. |
| F-3 | the real CLI | THE OPERATOR-FACING HALF, measured. `cli.main(["ipd","finalize","abc123","--dir",<root>,"--actor","opencode/test","--message","m2"])`, with NO `--apply` in the argv, printed `finalized abc123 -> executed at c95ed99f7086 (actor opencode/test).`, exited 0, and left journal `None` with the receipt consumed. So this is not a library-only nicety: the shipped command whose `--apply` help reads "Perform the transition (default: preview the precheck)" performs the transition without it. |
| F-4 | `_resume_post_commit` | WHY THIS IS NARROW, stated so nobody over-prioritizes it, and it survived re-measurement. The resume creates NO second commit: `HEAD` was identical before and after in every trial. It is reachable only when a PRIOR attempt already reached `committed-incomplete`, which means that attempt's lifecycle commit demonstrably landed. So the resume is not fabricating a transition, and HEAD is not lying about the outcome either, since it does report `finalized` and not `would finalize`. The defect is that a no-`--apply` invocation can reach that state at all, and that the receipt is spent by it. |
| F-5 | PROTOTYPE measurement of the fix | THE FIX DIRECTION WORKS AND RECOVERY SURVIVES IT. With `_early_recovery_result` given `apply` and returning a report for `committed-incomplete` when false, measured on the same fixture: `finalize(apply=False)` -> exit 0, findings `('finalize-journal-committed-incomplete',)`, journal STILL `committed-incomplete`, receipt PRESERVED, `HEAD` unmoved. Then `finalize(apply=True)` on that SAME fixture -> exit 0, `finalized abc123 -> executed at 5f59830e87f1`, journal cleared, receipt consumed, `HEAD` still unmoved. That second half is the measurement that matters most: a preview does NOT wedge the plan out of its own recovery, which is the one way this fix could have been worse than the defect. |
| F-6 | the bare suite, before and after the prototype | NO SHIPPED TEST DEPENDS ON THE DEFECT. `python3 -m pytest` BARE at unmodified lane HEAD: `3531 passed, 2 skipped, 3 warnings in 103.04s` (208 deselected). The SAME bare suite with the prototype applied to `agent_workflows/ipd_lifecycle.py` (helper parameter plus both call sites forwarding): `3531 passed, 2 skipped, 3 warnings in 114.56s`. Identical pass/skip counts, zero failures, so the blast radius is empty and the fix needs no test rewrites. The prototype was then REVERTED and `git status` confirmed clean before this plan was written. |
| F-7 | `status_set._delegate_plan_executed_to_finalize` | TWO MORE PREVIEW SURFACES THE ITEM DOES NOT NAME, and the one with the strongest promise. That function computes `apply = not getattr(args, "dry_run", False)` and passes it straight into `ipd_lifecycle.finalize`, so `--dry-run` reaches the same early-recovery path. Measured on the wedged fixture: `aw set executed abc123 ... --dry-run` printed `aw set -> ipd finalize: finalized abc123 -> executed at 2a752c04ce50 (actor opencode/test).`, exited 0, cleared the journal and CONSUMED the receipt; `aw ipd set executed ... --dry-run` did the identical thing. This is worse than the `--apply` case rather than merely equal to it, because `--dry-run` is an explicit promise to write nothing, where a defaulted `--apply` is only a documented default. It is also why E-03 is its own item and why the fix must live in the shared helper rather than in `run_finalize`. With the prototype applied, both spellings reported `WOULD RESUME: ...` and preserved journal and receipt. |
| F-8 | `ipd_lifecycle.retire_orchestrator` | THE SECOND CALL SITE, which has the SAME ordering defect. `retire_orchestrator` calls `_early_recovery_result` and only later tests `if not apply:` (measured by locating both within the function's own source: early recovery precedes the apply test). So the rollup preview can perform the resume too, and a fix applied only in `finalize` would leave the rollup path defective while making the two paths DISAGREE about what a preview does. `ROLLUP_SHARED_GATES` enumerates `early-crash-recovery` precisely so the shared gates stay shared; E-04 therefore changes the helper and forwards from both, which keeps that property instead of spending it. |
| F-9 | `ipd_lifecycle.run_finalize`'s `EXIT_OK` branch | THE NEW FINDING ID IS INVISIBLE UNLESS THIS IS FIXED, measured with the prototype in place. That branch calls `_emit(EXIT_OK, "clean", result.message, data={...})` with NO `diags`, so the findings tuple is discarded. Measured output of a no-apply preview on the wedged fixture: human mode printed the message alone; `--json` emitted `"diagnostics": []`; `--agent` emitted `"findings":0`. In all three the id `finalize-journal-committed-incomplete` was ABSENT. So minting an id for a caller to branch on, without E-05's surfacing half, would ship an id no CLI consumer can observe, which is the prose-coupling that `runner_shared`'s `RETRYABLE_FINALIZE_FINDING_TEXTS` comment records the repository as trying to retire. |
| F-10 | `tests/test_ipd_lifecycle_cli.py` | THE FIXTURES ALREADY EXIST, so these tests reuse proven ones rather than inventing any. `RollbackFailureSemanticsTests` provides `_begin_and_work`, `_executed_path` and `_head`; `test_postcommit_committed_incomplete_and_resume` already wedges `committed-incomplete` by patching `lint_file` for the `post-transition` checkpoint, and already asserts the receipt present at the wedge and consumed after an `apply=True` resume; `test_unrecoverable_failures_and_unknown_outcome` already wedges `unknown-outcome` via `_rollback_precommit` plus `fault_injection="after_move"`. The new tests are the missing half of the first: it pins the `apply=True` resume thoroughly and never asks what `apply=False` does. |
| F-11 | `runner_shared.driver_finalize` | WHY NO DRIVER PATH CHANGES, which bounds the risk. It builds `["ipd","finalize",...]` including `"--apply"` unconditionally, so every driver finalize already takes the apply branch and is unaffected by E-04. `runner_shared`'s rollup call site likewise passes `apply=True` explicitly. The exposure is therefore to HUMAN previews and to the `--dry-run` surfaces in F-7, not to the unattended runners; this is a correctness and trust defect on an operator-facing contract, not a live hazard to a run in flight. |
| F-12 | `ipd_lifecycle.finalize_precheck` | THE ADJACENT PLAN, named so a reviewer does not expect overlap. `bn58ha`/`hlv737` teaches the precheck to refuse a `PHASE_UNKNOWN_OUTCOME` journal, and its F-6 explicitly EXCLUDES `committed-incomplete` from both its refusing set and its control set, recording that pinning either verdict there would freeze a behavior "backlog `hernns` may change". This plan is that change. The two touch the same file and do not touch the same function: `hlv737` edits `finalize_precheck`, this edits `_early_recovery_result` plus `run_finalize`'s emit branch. No `- Item-Dependencies:` edge is declared because neither needs the other's code to be correct, and both are measured green independently; an executor taking them in either order should expect a textual merge in `ipd_lifecycle.py` and no semantic conflict. |

## Proposed changes (ordered, validatable)

1. E-01: add the failing `finalize(apply=False)` preservation test and paste its failure at unmodified HEAD.
2. E-02: add the failing real-CLI test for a no-`--apply` invocation and paste its failure.
3. E-03: add the failing `--dry-run` test for both `set executed` spellings and paste its failure.
4. E-04: give `_early_recovery_result` a keyword-only `apply` parameter defaulting to `True`, report instead of resuming when false, and forward `apply=apply` from both `finalize` and `retire_orchestrator`.
5. E-05: mint the token-form finding id beside the `FINDING_RECEIPT_*` family, emit it in the new report, and pass findings as diagnostics on `run_finalize`'s `EXIT_OK` branch so it is observable.
6. E-06: add the control test pinning the `apply=True` resume, recovery-after-preview, the unchanged `unknown-outcome` refusal for both flag values, and the unchanged ordinary preview.
7. E-07: add the CHANGELOG line and compare the bare-suite baseline taken before any source edit with the after-run.

## Deferred / out of scope (with reason)

- MOVING THE `apply` TEST AHEAD OF EARLY RECOVERY in `finalize`, which the backlog item lists as one candidate shape. Rejected on analysis, and the reason is recorded in E-04's comment because it is the obvious "simpler" refactor a later reader will reach for: early recovery also owns the `PHASE_UNKNOWN_OUTCOME` refusal, so skipping it for a preview would make a preview of an ambiguously-wedged plan fall through to the ordinary precheck and report that the transition may proceed. That trades a contract violation for a fail-OPEN one.
  - Carrier-Declined: A REJECTED ALTERNATIVE DESIGN, not deferred work. E-04 implements the chosen shape and records this rejection in a code comment, so nothing remains outstanding for a carrier to own.
- MAKING THE PREVIEW REFUSE (nonzero) rather than report. Rejected because a preview that successfully observed a recoverable state has not failed, and two shipping consumers key on the code: `runner_shared.compute_scope_reconciliation` (`exit_code != 0`) and `record_item_spec_edits` (`rc != 0`) would both reclassify an observation as a refusal, the latter durably in a run's per-item record.
  - Carrier-Declined: A REJECTED ALTERNATIVE DESIGN, decided here on measured consumer behavior. E-04 ships the `EXIT_OK` shape, so no work is outstanding.
- ANY AUTO-CLEAR OR REMEDY for a wedged journal. The remedy for `committed-incomplete` is the `--apply` resume this plan preserves; for `unknown-outcome` it is the manual clearing the existing refusal already names. Inventing a third is a separate design question.
  - Carrier-Declined: Both wedged phases already HAVE a working remedy (the `--apply` resume, and the manual clear the existing refusal names), so this is a declined enhancement rather than a gap this plan leaves behind.
- TEACHING `finalize_precheck` ABOUT THE JOURNAL. That is `bn58ha`/`hlv737`, already authored and approved (F-12). Doing it here would duplicate an approved plan's deliverable.
  - Carrier: hlv737
- ADDING A CONSUMER of the new finding id (a runner retry branch, a disposition rule). Minting and surfacing it is this plan's deliverable; deciding what a driver should DO on seeing it is a policy question with its own risk.
  - Carrier-Declined: No consumer is REQUIRED for this fix to be complete: the defect is that a preview mutates, and E-04 closes that. An id with no consumer is the deliberate end state (the same shape the `FINDING_RECEIPT_*` family shipped in), not an unfinished half.
- THE `run_begin` / receipt-minting side. Nothing here changes when a receipt is created, only which invocations may spend one.
  - Carrier-Declined: A STATEMENT OF WHAT IS UNTOUCHED, recorded to bound the diff for a reviewer. There is no obligation here to carry.

## Scope check

- Over-scope: none. The three `- Scope-Paths:` entries are the implementation file, its existing test module, and the changelog. `status_set.py` is NOT in scope even though F-7 measures its `--dry-run` surfaces as defective, because they are defective only by delegation: they pass `apply` through faithfully and are fixed by the helper change, measured. `runner_shared.py` is not in scope for the reason F-11 gives.
- Under-scope: the second call site, `retire_orchestrator`, lives in the same file already in scope, so no path is missing. If an executor finds that forwarding the flag requires a signature change in `runner_shared.py` or `status_set.py`, that is a scope surprise and must be reconciled at finalize rather than absorbed silently; measurement says it does not, since both already pass `apply` positionally or by keyword and neither calls the helper directly.

## Required tests / validation

All tests are behavioral and drive real functions and the real CLI against real temporary git repositories, asserting on exit codes, messages, findings, journal phase, receipt existence and `HEAD`. No test reads production source, counts symbols, or asserts on comment text.

- E-01, E-02 and E-03 must each be run and FAIL at unmodified HEAD, with the failure pasted. A fix-first-then-test order cannot demonstrate that the defect was real or that the test detects it.
- E-06's controls must pin the `apply=True` resume, the reachability of recovery AFTER a preview, the `unknown-outcome` refusal under BOTH flag values, and an ordinary journal-free preview.
- The bare suite (`python3 -m pytest`) must be run before any source edit and again at the end, with both summary lines and FAILED sets pasted and compared.

## Spec / documentation sync

No `.spec.md` amendment. The behavior being corrected is not specified in a spec record: the contract it violates is stated in `cli.py`'s own `--apply` help text ("Perform the transition (default: preview the precheck)") and in `ipd_lifecycle.finalize`'s docstring, and this plan makes the code match that already-published contract rather than changing it. Nothing is added to `- Scope-Paths:` for a spec file, and no declared-spec-edit announcement should appear for this plan. `CHANGELOG.md` carries the single user-facing record (E-07).

## Open questions

### OQ-01: Should the preview's diagnostic severity be `warning` or `info`?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED from repository evidence, not deferred to the human, because the repo answers it. `run_finalize`'s `EXIT_FINDINGS` branch constructs its diagnostics with `severity="error"`, which is correct there because that branch IS a refusal. Reusing `error` on an `EXIT_OK` preview would make a successful observation render as a failure, and `aw check`'s own severity vocabulary already distinguishes advisory findings from errors for exactly this reason. The executor should therefore use a non-error severity, and E-06's control asserting that an ordinary journal-free preview still reports clean with no diagnostics is what keeps the choice honest. The precise token is an implementation detail the executor picks to match the `Diagnostic` type's existing values; it is not a contract this plan fixes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted FAILING run of the new test at unmodified HEAD, showing the assertion that fired and that the observed state was journal `None` with the receipt absent; plus the pasted PASSING run after E-04, showing journal `committed-incomplete`, the receipt present, and `HEAD` unmoved. Both preconditions (phase and receipt presence at the wedge) must appear as asserted, not assumed.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the pasted FAILING run showing the real CLI, invoked with an argv containing no `--apply`, printing `finalized abc123 -> executed at <sha>` and consuming the receipt; and the pasted PASSING run after E-04 showing the preview message with journal and receipt intact. The argv actually used must be pasted, so a reader can confirm `--apply` is genuinely absent.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: the pasted FAILING run for BOTH `aw set executed ... --dry-run` and `aw ipd set executed ... --dry-run`, each showing the receipt consumed; and the pasted PASSING run after E-04 showing both preserving journal and receipt. Both spellings must appear, since one passing does not imply the other.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the diff of `_early_recovery_result` and its two call sites, showing the keyword-only `apply` defaulting to `True`, the report returned before `acquire_finalize_lock`, and `apply=apply` forwarded from BOTH `finalize` and `retire_orchestrator`. Plus pasted output of a `retire_orchestrator(..., apply=False)` call on a `committed-incomplete` orchestrator journal showing it reports rather than resumes, since F-8's claim about that path was established by reading and must be confirmed by execution. Plus the comment text explaining why the apply test was not simply moved ahead of early recovery.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the new constant's definition pasted beside the existing `FINDING_RECEIPT_NEVER_ISSUED` / `FINDING_RECEIPT_ALREADY_FINALIZED` lines showing the same token form; and the actual stdout of the no-apply preview in ALL THREE output modes (human, `--json`, `--agent`) showing the id present in each. F-9 measured it absent in all three before this item, so all three must be re-run and pasted, not predicted. Also paste an ordinary journal-free preview in `--agent` mode showing `"findings":0` still, which is what proves the surfacing change did not make every clean preview emit noise.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted passing output for each of the four controls, with the concrete observed values quoted: the `apply=True` resume's exit code, cleared journal, consumed receipt and unmoved `HEAD`; the preview-then-apply sequence's second exit code; the `unknown-outcome` exit code under BOTH `apply=False` and `apply=True`; and the journal-free preview's message and empty findings tuple.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the added `CHANGELOG.md` line quoted verbatim, confirmed to sit under `## 2.0.0 (pending)` and to contain no em or en dash; plus the two BARE `python3 -m pytest` summary lines (before any source edit, and after all items) with their FAILED sets and an explicit statement of whether the sets are identical. A summary line showing a suppressed count (from a doubled `-q`) does not satisfy this.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and must not be executed before it is reviewed and explicitly approved by the
maintainer. Execution follows the repository execution contract: commit only the paths named in
`- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; paste
ACTUAL runner output for every test claim rather than asserting success; and leave any file not named
here untouched, including a co-worker's uncommitted changes in this shared checkout.

The terminal lifecycle move is NOT performed by hand. In a managed lane the runner owns begin/finalize
and `AW-LIFECYCLE-ROLE-001` refuses them to a worker, so an executing agent writes the outcome file its
turn prompt names and stops; the driver transitions the plan. In an unmanaged or manual run the executor
performs the transition with `aw ipd finalize`, which is the only supported route to `executed`, and only
after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted
evidence.
