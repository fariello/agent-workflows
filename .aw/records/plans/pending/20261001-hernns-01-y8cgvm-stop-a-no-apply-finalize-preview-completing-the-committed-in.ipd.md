# IPD: Stop a no-apply finalize preview completing the committed-incomplete transaction and spending the begin receipt

- Date: 2026-10-01
- Kind: child
- Concern: `aw ipd finalize <plan>` WITHOUT `--apply` is documented as a preview (`cli.py` registers `--apply` as "Perform the transition (default: preview the precheck)"), and on the ordinary path it is one. But when a prior attempt left the finalize transaction journal in `PHASE_COMMITTED_INCOMPLETE`, `ipd_lifecycle.finalize` runs `_early_recovery_result` BEFORE it ever reaches its `if not apply:` arm, that helper calls `_resume_post_commit`, and the resume COMPLETES the transaction: it clears the journal and CONSUMES the single-use begin receipt. The preview arm is never reached. Backlog `hernns`, measured; reproduced independently in this lane on 2026-10-01 and found to affect two MORE preview surfaces the item did not name, including `aw set executed --dry-run`, whose `--dry-run` contract is a stronger promise than `--apply`'s default.
- Scope: IN: thread an `apply` flag through `ipd_lifecycle._early_recovery_result` so that, when false, the `PHASE_COMMITTED_INCOMPLETE` arm REPORTS the recoverable state and the exact command that would complete it instead of performing it; forward the flag from BOTH call sites (`finalize` and `retire_orchestrator`), which share that helper by construction; mint a stable finding id for the new report so no caller branches on prose; surface that id as a diagnostic on `aw ipd finalize`'s EXIT_OK preview, which today drops it on all three output modes (and reaches human plus `--json` only, per F-13); behavioral regression tests covering `finalize`, the real CLI, both `--dry-run` spellings, and a control pinning the rollup path UNCHANGED (F-8 measures its `committed-incomplete` arm unreachable, so forwarding the flag there is drift defense, not a live fix); one CHANGELOG line. OUT: changing the `apply=True` resume in ANY way (it stays "RESUMED, never reverted"); changing `PHASE_UNKNOWN_OUTCOME`'s existing refusal, which already fails closed identically for both flag values; `finalize_precheck`, whose own blindness to a wedged journal is `bn58ha`/`hlv737`'s subject and is deliberately untouched here; adding any auto-clear or remedy for a wedged journal; and `runner_shared.driver_finalize`, measured passing `--apply` unconditionally so no driver path changes behavior.
- Scope-Paths: agent_workflows/ipd_lifecycle.py, tests/test_ipd_lifecycle_cli.py, tests/test_orchestrator_retirement.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: hernns
- Blocks-Release: next
- Set: hernns
- Order: 1
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: y8cgvm
- Approval: 2026-10-01, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-01 approved (aw set): status set to approved
- 2026-10-01 reviewed (opencode/its_direct-pt3-claude-opus-5-1m-us): /plan-review round 1: 5 findings (PR-001 HIGH .. PR-005 LOW), all FIXED in place

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

- [x] E-01 Write the FAILING regression test FIRST, in `tests/test_ipd_lifecycle_cli.py`, in `RollbackFailureSemanticsTests` (whose `_begin_and_work` / `_executed_path` / `_head` helpers and whose wedging technique this needs, see F-10). Wedge `PHASE_COMMITTED_INCOMPLETE` exactly as the shipped `test_postcommit_committed_incomplete_and_resume` does, by patching `ipd_lint.lint_file` to return a `DISPOSITION_ERROR` result for `checkpoint == "post-transition"` only. Assert as PRECONDITIONS that the journal phase really is `LC.PHASE_COMMITTED_INCOMPLETE` and that `LC.receipt_path_for(...)` EXISTS, so the test cannot pass vacuously if a future change stops producing that state. Then call `LC.finalize(..., apply=False)` on the `executed/` path and assert the preview changed NOTHING: the journal is still `committed-incomplete`, the receipt still exists, and `HEAD` is unmoved. Run it and paste the FAILURE. Do NOT edit `ipd_lifecycle.py` in this item.
  - Depends on: none
  - Expected outcome: one new test FAILING at unmodified HEAD, whose failure shows the preview having cleared the journal (`None`) and consumed the receipt. That failure is the evidence both that the defect is real and that the test bites; a test written after the fix proves neither.
  - Execution state: performed

- [x] E-02 Add the second FAILING test, in the same class, driving the REAL CLI rather than the function, because the contract being violated is stated in `cli.py`'s help text and an in-process call cannot prove the shipped command violates it. Wedge the same state, then call `cli.main(["ipd","finalize","abc123","--dir",str(root),"--actor",...,"--message",...])` with NO `--apply`, and assert exit 0 together with the journal and receipt BOTH surviving. Keep this separate from E-01 rather than folding it in: E-01 pins the library contract and E-02 pins the operator-facing one, and F-7 shows the two can diverge per surface, so one test cannot stand in for the other.
  - Depends on: none
  - Expected outcome: a second test FAILING at unmodified HEAD, whose pasted failure shows the real CLI printing `finalized abc123 -> executed at <sha>` and consuming the receipt with no `--apply` anywhere in its argv.
  - Execution state: performed

- [x] E-03 Add the THIRD failing test, in the same class, for the `--dry-run` surfaces F-7 measured, which the backlog item does not mention and which carry the stronger promise. Drive `cli.main(["set","executed","abc123","--dir",...,"--actor",...,"--message",...,"--dry-run"])` on the wedged state and assert the journal and receipt survive. Assert the SAME for the `["ipd","set","executed",...,"--dry-run"]` spelling, since `status_set._delegate_plan_executed_to_finalize` serves both and a test covering one leaves the other unpinned. This is its own item because it is a different entry point with a different flag contract (`--dry-run`, not a defaulted `--apply`), not a second assertion about the same one.
  - Depends on: none
  - Expected outcome: a third test FAILING at unmodified HEAD, with the pasted failure showing `--dry-run` reporting `aw set -> ipd finalize: finalized abc123 -> executed at <sha>` and consuming the receipt. This is the strongest single statement of the defect, because `--dry-run` means write nothing.
  - Execution state: performed

### Task group 2: close the defect in the one shared helper

- [x] E-04 Thread the flag through `ipd_lifecycle._early_recovery_result` and forward it from BOTH call sites. Give the helper a keyword-only `apply: bool = True` parameter, and in its `PHASE_COMMITTED_INCOMPLETE` arm, when `apply` is false, return `EXIT_OK` with a message that (a) says the prior finalize is COMMITTED-INCOMPLETE, (b) names the already-landed `lifecycle_commit` from the journal, (c) states that nothing was changed and the begin receipt was NOT consumed, and (d) names the re-invocation with `--apply` that would complete it. Site the check BEFORE `acquire_finalize_lock`, so a preview takes no writer lock. Pass `apply=apply` from `finalize` AND from `retire_orchestrator`. READ F-8 BEFORE WRITING THE SECOND FORWARD AND DO NOT RESTATE THE ORIGINAL CLAIM: review measured the rollup's `committed-incomplete` arm UNREACHABLE (its status-legality gate refuses `already-terminal` first, for BOTH flag values), so forwarding there fixes no live bug and is required as DRIFT DEFENSE, because `ROLLUP_SHARED_GATES` names `early-crash-recovery` shared and a helper that behaved differently per caller would break exactly that property. Do not write a comment or a test asserting the rollup preview resumes today; it does not. Default the parameter to `True` so any caller not updated keeps today's behavior, which is the fail-safe direction (a missed caller still resumes rather than silently previewing a transition the operator asked for). Leave `PHASE_UNKNOWN_OUTCOME` and the `return None` fall-through untouched. Record in a comment WHY the apply test cannot simply be moved ahead of early recovery in `finalize`: that would also skip the `unknown-outcome` refusal, so a preview of an ambiguously-wedged plan would report the ordinary precheck result and tell the operator to proceed, which converts this bug into a worse fail-OPEN one.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: E-01, E-02 and E-03 all pass. `finalize(..., apply=False)` and both `--dry-run` spellings report the recoverable state and leave the journal and receipt intact; `finalize(..., apply=True)` is byte-identical to today. `retire_orchestrator` is UNCHANGED in observable behavior for both flag values, which is the correct outcome given F-8.
  - Execution state: performed

- [x] E-05 Mint the finding id and make it VISIBLE on the preview surface. Add a module-level constant beside the existing `FINDING_RECEIPT_NEVER_ISSUED` / `FINDING_RECEIPT_ALREADY_FINALIZED` family, in the short-token form those two take (not the sentence form `FINDING_RECEIPT_STALE` takes, which that constant's own comment explains is preserving an already-shipped string), and emit it in E-04's findings tuple. Then fix the surfacing F-9 measured: `ipd_lifecycle.run_finalize`'s `EXIT_OK` branch calls `_emit` with no `diags`, so the id is dropped in human, `--json` and `--agent` modes alike, and a caller told to branch on an id it cannot observe is told nothing. Pass the findings through as diagnostics on that branch, mirroring the shape the `EXIT_FINDINGS` branch already uses (`OutDiag(location=str(plan_path), rule="IPD-FINALIZE", detail=f, ...)`) but with a NON-ERROR severity, since an `EXIT_OK` observation is not a refusal. KNOW WHAT `--agent` CAN AND CANNOT CARRY BEFORE WRITING THE TEST, measured at review (F-13): compact `--agent` output renders each diagnostic as `{"location", "rule"}` ONLY and DROPS `detail`, `--verbose` is not registered on `aw ipd finalize`, so routing the id through `detail` makes it observable in human and `--json` output but NOT in `--agent`, where only the `findings` COUNT rises from 0 to 1. Accept that asymmetry and pin it honestly rather than defeating it: do NOT put the id in the `rule` field to smuggle it into `--agent` (that breaks the `IPD-FINALIZE` rule-name convention the refusal branch established and which `runner_shared`'s `IPD-` prefix finding parser relies on), and do NOT register `--verbose` on this subparser, which is a CLI surface change this plan has no scope for. Add no consumer of the id (no runner branch, no retry classification): minting and surfacing it is the deliverable, and a consumer is a separate decision with its own risk.
  - Depends on: E-04
  - Expected outcome: one new module-level constant; the preview's findings tuple carries it; the id's TEXT is observable in human and `--json` output and the `--agent` record's `findings` count rises to 1 with `rule` `IPD-FINALIZE`; and an ORDINARY clean preview (no journal) still emits no diagnostics, still reports `outcome` `clean` with `findings` 0, and still exits 0.
  - Execution state: performed

- [x] E-06 Add the CONTROL test, in the same class, proving the change is narrow in both directions. Assert that `apply=True` on a `committed-incomplete` journal STILL resumes: exit 0, journal cleared, receipt consumed, and `HEAD` unmoved (no second lifecycle commit). Assert that the RECOVERY REMAINS REACHABLE AFTER A PREVIEW by running `apply=False` and then `apply=True` on the SAME fixture and checking the second call succeeds; this is the item's central risk, since a preview that wedged the plan out of its own recovery would be worse than the defect. Assert that `PHASE_UNKNOWN_OUTCOME` still returns `EXIT_CANNOT_RUN` for BOTH flag values, pinning that this plan did not convert a fail-closed refusal into a permissive report. Assert that an ordinary preview with NO journal returns exactly what it returns today, with the new finding id ABSENT. Drive the unknown-outcome wedge with the shipped `_rollback_precommit` patch plus `fault_injection="after_move"` that `test_unrecoverable_failures_and_unknown_outcome` already uses. The ROLLUP control is deliberately NOT here: it needs a different test module and a different fixture, so it is E-08.
  - Depends on: E-04, E-05
  - Expected outcome: four control assertions passing in `tests/test_ipd_lifecycle_cli.py`, so a later widening of E-04's condition into "any journal previews" fails a test rather than silently breaking the resume and rollback paths the journal exists to serve.
  - Execution state: performed

- [x] E-08 Add the ROLLUP-UNCHANGED control, in `tests/test_orchestrator_retirement.py`, in `RollupTransitionCase` (which owns the Set fixture and the `make_set` / `retire` helpers this needs; `RollbackFailureSemanticsTests` has no Set and cannot express it). ADDED AT REVIEW, split out of E-06 because it is a different module, a different fixture and a different surface. Wedge an orchestrator into `committed-incomplete` by building an eligible Set with one executed child and patching `ipd_lint.lint_file` to error at `post-transition` during an `apply=True` retire. Then assert that `retire_orchestrator` on the resulting `executed/` path returns `EXIT_FINDINGS` carrying `ROLLUP_REFUSED_ALREADY_TERMINAL` for BOTH `apply=False` AND `apply=True`, with the journal still `committed-incomplete` after each. This pins F-8's reachability premise: the rollup's `committed-incomplete` early-recovery arm is unreachable because the status-legality gate refuses first, so this plan changes nothing observable there. If a later change reorders that gate behind early recovery, this test fails and names the premise that moved, instead of letting a rollup preview silently begin resuming. Do NOT weaken it into asserting the rollup preview reports a recoverable state; it does not and must not be made to.
  - Depends on: E-04
  - Expected outcome: one new test passing, showing the identical `already-terminal` refusal under both flag values with the journal preserved, so the rollup half of E-04's forward is pinned as a no-op rather than asserted to be one.
  - Execution state: performed

### Task group 3: record it and prove no regression

- [x] E-07 Add ONE `- Fixed:` line under `## 2.0.0 (pending)` in `CHANGELOG.md`, in the user-facing register with no em or en dashes, saying that previewing a finalize of a plan whose previous attempt was interrupted after its commit landed now reports what it would do instead of silently completing it and spending the plan's begin receipt. Then establish and compare the suite baseline: run `python3 -m pytest` BARE at the unmodified HEAD of this lane BEFORE any source edit, record the summary line and the full FAILED set, run it again after E-01 through E-06 and E-08, and account for every difference. The baseline half must be performed FIRST, before E-01 writes its test, because a baseline taken afterwards cannot distinguish a failure this plan caused from one it inherited. RE-DERIVE THE NUMBER; DO NOT INHERIT ANY FIGURE FROM THIS PLAN'S PROSE. The count has already drifted twice: authoring measured `3531 passed, 2 skipped, 3 warnings in 103.04s` (208 deselected), and review re-measured the SAME lane at `3822 passed, 2 skipped, 3 warnings in 143.59s` (208 deselected) with the tree clean, because other lanes integrated between the two runs. Both figures are context, NEVER the bar; the bar is that your own before-run and after-run FAILED sets are identical. Treat ANY failure in the after-run as this plan's until the before-run shows the same node id.
  - Depends on: E-06, E-08
  - Expected outcome: one CHANGELOG entry in user terms, and two pasted bare-suite summary lines with their FAILED sets plus an explicit statement of whether the sets are identical.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The finding-id family this extends is `FINDING_RECEIPT_NEVER_ISSUED` (`"receipt-never-issued"`) and `FINDING_RECEIPT_ALREADY_FINALIZED` (`"receipt-consumed-already-finalized"`), both short tokens. `FINDING_RECEIPT_STALE` is deliberately a sentence because it NAMES an already-shipped string, and its own comment says so, which is why E-05 takes the token form.
- The journal phase vocabulary is a set of module constants: `PHASE_PREPARED`, `PHASE_MUTATING`, `PHASE_READY_TO_COMMIT`, `PHASE_COMMITTED_INCOMPLETE`, `PHASE_UNKNOWN_OUTCOME`, `PHASE_COMPLETE`, with `_PRE_COMMIT_PHASES` grouping the first three. Only `COMMITTED_INCOMPLETE` is touched here.
- Exit codes are `EXIT_OK = 0`, `EXIT_FINDINGS = 1`, `EXIT_CANNOT_RUN = 2`. The new preview report uses `EXIT_OK`, matching the existing preview arm's own `EXIT_OK`: a preview that successfully observed a recoverable state has not failed. CORRECTED AT REVIEW: the authored note justified this by `runner_shared.compute_scope_reconciliation` and `record_item_spec_edits`, which actually consume `finalize_precheck` and not `finalize`, so they are NOT affected either way. The real basis is the operator surfaces: `run_finalize`'s `_emit` prefixes exit 1 with `refused: ` and renders its diagnostics at `severity="error"`, and `status_set`'s delegation maps exit 1 to `refused: ` too, so a nonzero preview would print a refusal for a successful observation. See the matching entry under `## Deferred / out of scope`.
- `_early_recovery_result` is SHARED BY CONSTRUCTION between `finalize` and `retire_orchestrator`, and `ROLLUP_SHARED_GATES` names `early-crash-recovery` explicitly so a test can fail when one path gains a gate the other lacks. That sharing is why E-04 changes one helper and forwards from two call sites rather than patching either path locally. NOTE the reachability asymmetry review measured (F-8): the rollup reaches the helper's `unknown-outcome` arm but NOT its `committed-incomplete` arm, because its own status-legality gate refuses an already-terminal plan first. Sharing is still the right shape; the second forward is drift defense rather than a live fix.
- A landed lifecycle commit is "RESUMED, never reverted" (the `finalize` docstring). This plan does not weaken that: it changes only WHICH INVOCATION is allowed to perform the resume, never whether a landed commit may be reverted.
- Test-authoring contract (`AGENTS.md`, GUIDING_PRINCIPLES P16): assert observable outcomes, never read production source with `inspect`/`ast`/regex, never assert on symbol censuses. Every test here drives real functions and the real CLI against real temporary git repositories and asserts on exit codes, messages, findings, journal phase, receipt existence and `HEAD`.
- Run the suite BARE as `python3 -m pytest`; `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` (quoted exactly at review; the authored note dropped `and not livecorpus`, which matters because the deselected count depends on BOTH markers). Do not add `-n0`, a second `-q` (which suppresses the summary line this plan must paste), or `-p no:randomly`.
- Lifecycle tests declare their execution role in `setUp` via `support.declare_execution_role(self)`; the lane exports `AW_EXECUTION_ROLE=worker`, which `AW-LIFECYCLE-ROLE-001` refuses, so a test (or a measurement harness) that does not declare the coordinator role cannot reach `begin`/`finalize` at all. This was hit while measuring F-1 and is why the fixtures in this plan follow the shipped classes.
- The journal lives under the GITIGNORED `.aw/state/runtime/transactions/` tree (`finalize_journal_path`), so nothing here touches a tracked path beyond the four in `- Scope-Paths:`.
- Compact `--agent` output renders a diagnostic as `{"location", "rule"}` and drops `detail` unless `context.verbose`, and `--verbose` is NOT registered on `aw ipd finalize`. So a finding id routed through `detail` is observable in human and `--json` output and NOT in `--agent`, where only the `findings` count changes. Measured at review; see F-13, which is why E-05 and V-05 state that asymmetry instead of demanding the id in all three modes.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Where | Finding |
|---|---|---|
| F-1 | `ipd_lifecycle.finalize` vs its own `if not apply:` arm | THE DEFECT, REPRODUCED IN THIS LANE 2026-10-01 (not transcribed from the item). Scratch git repo, `begin`, in-scope commit, then `ipd_lint.lint_file` patched to return `DISPOSITION_ERROR` for `checkpoint == "post-transition"` only, which lands the journal in `committed-incomplete` with the lifecycle commit ALREADY made and the plan already moved to `executed/`. Precondition in every trial: journal `committed-incomplete`, receipt PRESENT, plan in `executed/`. Then `finalize(..., apply=False)` on the executed path returned `(0, 'finalized abc123 -> executed at c95ed99f7086 (actor opencode/test).')` and left journal `None` with the receipt GONE. Two independent no-apply trials were byte-identical to each other, and identical in exit code, message and receipt state to the `apply=True` trial, so the two invocations are indistinguishable from their output. `HEAD` was unmoved in all three, which is correct and is the narrowness F-4 records. |
| F-2 | `ipd_lifecycle.finalize` control flow | WHY IT HAPPENS. `finalize` calls `_early_recovery_result` BEFORE the precheck and therefore long before `if not apply:`. That helper's `PHASE_COMMITTED_INCOMPLETE` arm takes the finalize lock and calls `_resume_post_commit`, which calls `_complete_after_commit`, which clears the journal and consumes the receipt. Because the helper RETURNS a `FinalizeResult`, `finalize` returns it immediately and the preview arm is unreachable for this phase. The helper receives no `apply` argument at all today, which is exactly the missing input E-04 supplies. |
| F-3 | the real CLI | THE OPERATOR-FACING HALF, measured. `cli.main(["ipd","finalize","abc123","--dir",<root>,"--actor","opencode/test","--message","m2"])`, with NO `--apply` in the argv, printed `finalized abc123 -> executed at c95ed99f7086 (actor opencode/test).`, exited 0, and left journal `None` with the receipt consumed. So this is not a library-only nicety: the shipped command whose `--apply` help reads "Perform the transition (default: preview the precheck)" performs the transition without it. |
| F-4 | `_resume_post_commit` | WHY THIS IS NARROW, stated so nobody over-prioritizes it, and it survived re-measurement. The resume creates NO second commit: `HEAD` was identical before and after in every trial. It is reachable only when a PRIOR attempt already reached `committed-incomplete`, which means that attempt's lifecycle commit demonstrably landed. So the resume is not fabricating a transition, and HEAD is not lying about the outcome either, since it does report `finalized` and not `would finalize`. The defect is that a no-`--apply` invocation can reach that state at all, and that the receipt is spent by it. |
| F-5 | PROTOTYPE measurement of the fix | THE FIX DIRECTION WORKS AND RECOVERY SURVIVES IT. With `_early_recovery_result` given `apply` and returning a report for `committed-incomplete` when false, measured on the same fixture: `finalize(apply=False)` -> exit 0, findings `('finalize-journal-committed-incomplete',)`, journal STILL `committed-incomplete`, receipt PRESERVED, `HEAD` unmoved. Then `finalize(apply=True)` on that SAME fixture -> exit 0, `finalized abc123 -> executed at 5f59830e87f1`, journal cleared, receipt consumed, `HEAD` still unmoved. That second half is the measurement that matters most: a preview does NOT wedge the plan out of its own recovery, which is the one way this fix could have been worse than the defect. |
| F-6 | the bare suite, before and after the prototype | NO SHIPPED TEST DEPENDS ON THE DEFECT. `python3 -m pytest` BARE at unmodified lane HEAD at AUTHORING: `3531 passed, 2 skipped, 3 warnings in 103.04s` (208 deselected). The SAME bare suite with the prototype applied to `agent_workflows/ipd_lifecycle.py` (helper parameter plus both call sites forwarding): `3531 passed, 2 skipped, 3 warnings in 114.56s`. Identical pass/skip counts, zero failures, so the blast radius is empty and the fix needs no test rewrites. The prototype was then REVERTED and `git status` confirmed clean before this plan was written. RE-MEASURED AT REVIEW on the same lane with a clean tree: `3822 passed, 2 skipped, 3 warnings in 143.59s` (208 deselected). The CONCLUSION survives (still zero failures, so nothing depends on the defect) but the NUMBER did not, which is why E-07 forbids inheriting either figure. |
| F-7 | `status_set._delegate_plan_executed_to_finalize` | TWO MORE PREVIEW SURFACES THE ITEM DOES NOT NAME, and the one with the strongest promise. That function computes `apply = not getattr(args, "dry_run", False)` and passes it straight into `ipd_lifecycle.finalize`, so `--dry-run` reaches the same early-recovery path. Measured on the wedged fixture: `aw set executed abc123 ... --dry-run` printed `aw set -> ipd finalize: finalized abc123 -> executed at 2a752c04ce50 (actor opencode/test).`, exited 0, cleared the journal and CONSUMED the receipt; `aw ipd set executed ... --dry-run` did the identical thing. This is worse than the `--apply` case rather than merely equal to it, because `--dry-run` is an explicit promise to write nothing, where a defaulted `--apply` is only a documented default. It is also why E-03 is its own item and why the fix must live in the shared helper rather than in `run_finalize`. With the prototype applied, both spellings reported `WOULD RESUME: ...` and preserved journal and receipt. |
| F-8 | `ipd_lifecycle.retire_orchestrator` | THE SECOND CALL SITE. CORRECTED AT REVIEW 2026-10-01: the original row claimed the rollup preview "can perform the resume too", established by READING that early recovery precedes the apply test. EXECUTION CONTRADICTS THAT, and the correction matters because V-04 demanded evidence the original claim could never produce. The ordering reading is right but INCOMPLETE: `retire_orchestrator` runs a status-legality gate (`_schema.checkpoint_allows_status("pre-transition", status)`) BEFORE early recovery, and a `committed-incomplete` orchestrator has ALREADY been moved to `executed/` with `- Status: executed` written by the prior attempt. Measured on a real git fixture built from `tests/test_orchestrator_retirement.py::RollupTransitionCase` (wedged by patching `ipd_lint.lint_file` to error at `post-transition`, journal confirmed `committed-incomplete`): BOTH `apply=False` and `apply=True` returned `EXIT_FINDINGS` with `REFUSED: orc000 carries Status 'executed', which is already terminal; there is nothing to retire.` and findings `('already-terminal',)`, leaving the journal `committed-incomplete` untouched. So the rollup's `committed-incomplete` arm is UNREACHABLE and is not defective today. The `PHASE_UNKNOWN_OUTCOME` arm IS reachable (measured: wedged via `_rollback_precommit` patched to fail with `fault_injection="after_move"`, the plan stays in `pending/` at `- Status: approved`, and `apply=False` returned `EXIT_CANNOT_RUN` naming the unknown-outcome journal), and that arm is identical for both flag values by construction, so it is unaffected either way. CONSEQUENCE FOR THE PLAN: forwarding `apply` from `retire_orchestrator` is still CORRECT and is still required, but as DEFENSE AGAINST DRIFT rather than as a live bug fix. `ROLLUP_SHARED_GATES` names `early-crash-recovery` precisely so the two paths cannot diverge, and leaving one call site un-forwarded would make the shared helper behave differently per caller, which is the drift that enumeration exists to prevent. |
| F-9 | `ipd_lifecycle.run_finalize`'s `EXIT_OK` branch | THE NEW FINDING ID IS INVISIBLE UNLESS THIS IS FIXED, measured with the prototype in place. That branch calls `_emit(EXIT_OK, "clean", result.message, data={...})` with NO `diags`, so the findings tuple is discarded. Measured output of a no-apply preview on the wedged fixture: human mode printed the message alone; `--json` emitted `"diagnostics": []`; `--agent` emitted `"findings":0`. In all three the id `finalize-journal-committed-incomplete` was ABSENT. So minting an id for a caller to branch on, without E-05's surfacing half, would ship an id no CLI consumer can observe, which is the prose-coupling that `runner_shared`'s `RETRYABLE_FINALIZE_FINDING_TEXTS` comment records the repository as trying to retire. |
| F-10 | `tests/test_ipd_lifecycle_cli.py` | THE FIXTURES ALREADY EXIST, so these tests reuse proven ones rather than inventing any. `RollbackFailureSemanticsTests` provides `_begin_and_work`, `_executed_path` and `_head`; `test_postcommit_committed_incomplete_and_resume` already wedges `committed-incomplete` by patching `lint_file` for the `post-transition` checkpoint, and already asserts the receipt present at the wedge and consumed after an `apply=True` resume; `test_unrecoverable_failures_and_unknown_outcome` already wedges `unknown-outcome` via `_rollback_precommit` plus `fault_injection="after_move"`. The new tests are the missing half of the first: it pins the `apply=True` resume thoroughly and never asks what `apply=False` does. |
| F-11 | `runner_shared.driver_finalize` | WHY NO DRIVER PATH CHANGES, which bounds the risk. It builds `["ipd","finalize",...]` including `"--apply"` unconditionally, so every driver finalize already takes the apply branch and is unaffected by E-04. `runner_shared`'s rollup call site likewise passes `apply=True` explicitly. The exposure is therefore to HUMAN previews and to the `--dry-run` surfaces in F-7, not to the unattended runners; this is a correctness and trust defect on an operator-facing contract, not a live hazard to a run in flight. |
| F-13 | `result_types.CommandResult.to_agent_record` / `cli.py`'s `ipd finalize` subparser | WHAT `--agent` CAN ACTUALLY CARRY, added at review because E-05 and V-05 demanded an impossible observation. Compact agent output renders each diagnostic as `{"location", "rule"}` and DELIBERATELY DROPS `detail` unless `context.verbose`; `--verbose` is NOT registered on `aw ipd finalize` (its `--help` offers only `--no-color/--color`, `--no-interactive/--interactive`, `--agent`, `--json`, `--fields`, `--actor`, `--message`, `--apply`, `--scope-reason`, `--scope-ack`, `--dir`). MEASURED at review two ways. Through the real CLI on a wedged fixture with `--apply` (so the existing `EXIT_FINDINGS` branch fires): `--agent` printed `"findings":1,"diagnostics":[{"location":".aw/records/plans/executed/20260824-demo-01-abc123-demo.ipd.md","rule":"IPD-FINALIZE"}]` with NO finding text anywhere, while `--json` printed the same diagnostic WITH `"detail"`. Directly on the type: an `EXIT_OK` record carrying one `severity="warning"` diagnostic yields `"outcome":"clean","exit":0,"findings":1`, confirming the severity choice does not flip `outcome` (the `status in ("clean","ok","conforms")` arm only reclassifies to `findings` when `exit_code == 1`), and that `data={"findings_ids": [...]}` is NOT a workaround because an explicit `data` findings count is overridden whenever `diagnostics` is non-empty. So E-05's deliverable is real but its reach is narrower than authored: human and `--json` gain the id text, `--agent` gains a COUNT. Recorded because V-05 would otherwise block on evidence no implementation in scope can produce. |
| F-12 | `ipd_lifecycle.finalize_precheck` | THE ADJACENT PLAN, named so a reviewer does not expect overlap. `bn58ha`/`hlv737` teaches the precheck to refuse a `PHASE_UNKNOWN_OUTCOME` journal, and its F-6 explicitly EXCLUDES `committed-incomplete` from both its refusing set and its control set, recording that pinning either verdict there would freeze a behavior "backlog `hernns` may change". This plan is that change. The two touch the same file and do not touch the same function: `hlv737` edits `finalize_precheck`, this edits `_early_recovery_result` plus `run_finalize`'s emit branch. No `- Item-Dependencies:` edge is declared because neither needs the other's code to be correct, and both are measured green independently; an executor taking them in either order should expect a textual merge in `ipd_lifecycle.py` and no semantic conflict. |

## Proposed changes (ordered, validatable)

1. E-01: add the failing `finalize(apply=False)` preservation test and paste its failure at unmodified HEAD.
2. E-02: add the failing real-CLI test for a no-`--apply` invocation and paste its failure.
3. E-03: add the failing `--dry-run` test for both `set executed` spellings and paste its failure.
4. E-04: give `_early_recovery_result` a keyword-only `apply` parameter defaulting to `True`, report instead of resuming when false, and forward `apply=apply` from both `finalize` and `retire_orchestrator` (the second forward is drift defense, not a live fix: see F-8).
5. E-05: mint the token-form finding id beside the `FINDING_RECEIPT_*` family, emit it in the new report, and pass findings as diagnostics on `run_finalize`'s `EXIT_OK` branch so it is observable in human and `--json` output, with `--agent` gaining the count (F-13).
6. E-06: add the control test pinning the `apply=True` resume, recovery-after-preview, the unchanged `unknown-outcome` refusal for both flag values, and the unchanged ordinary preview.
7. E-08: add the rollup-unchanged control in `tests/test_orchestrator_retirement.py`, pinning the identical `already-terminal` refusal under both flag values (split from E-06 at review: different module, different fixture).
8. E-07: add the CHANGELOG line and compare the bare-suite baseline taken before any source edit with the after-run.

## Deferred / out of scope (with reason)

- MOVING THE `apply` TEST AHEAD OF EARLY RECOVERY in `finalize`, which the backlog item lists as one candidate shape. Rejected on analysis, and the reason is recorded in E-04's comment because it is the obvious "simpler" refactor a later reader will reach for: early recovery also owns the `PHASE_UNKNOWN_OUTCOME` refusal, so skipping it for a preview would make a preview of an ambiguously-wedged plan fall through to the ordinary precheck and report that the transition may proceed. That trades a contract violation for a fail-OPEN one.
  - Carrier-Declined: A REJECTED ALTERNATIVE DESIGN, not deferred work. E-04 implements the chosen shape and records this rejection in a code comment, so nothing remains outstanding for a carrier to own.
- MAKING THE PREVIEW REFUSE (nonzero) rather than report. Rejected because a preview that successfully observed a recoverable state has not failed, and because `EXIT_OK` matches the sibling preview arm in the same function. REASONING CORRECTED AT REVIEW, conclusion unchanged: the authored version cited `runner_shared.compute_scope_reconciliation` (`exit_code != 0`) and `record_item_spec_edits` (`rc != 0`) as consumers that "would reclassify an observation as a refusal". Both of those branches call `ipd_lifecycle.finalize_precheck`, NOT `finalize`, and `finalize_precheck` is explicitly OUT of this plan's scope and is not reached by a `committed-incomplete` preview at all (early recovery returns before it). So those two are NOT consumers of the code this plan sets and they do not support the rejection. What DOES support it, verified at review: `EXIT_OK` is what the existing `if not apply:` arm in `finalize` already returns, `EXIT_FINDINGS` is reserved in `run_finalize`'s `_emit` for the `refused: ` prefix and the `severity="error"` diagnostics, and `status_set`'s delegation maps exit 1 to `refused: ` too, so a nonzero preview would print a refusal for a successful observation on both operator surfaces. Keeping the (correct but mis-cited) deferral honest matters because a later reader would otherwise inherit a false claim about who consumes this exit code.
  - Carrier-Declined: A REJECTED ALTERNATIVE DESIGN, decided here on repository evidence re-verified at review. E-04 ships the `EXIT_OK` shape, so no work is outstanding.
- ANY AUTO-CLEAR OR REMEDY for a wedged journal. The remedy for `committed-incomplete` is the `--apply` resume this plan preserves; for `unknown-outcome` it is the manual clearing the existing refusal already names. Inventing a third is a separate design question.
  - Carrier-Declined: Both wedged phases already HAVE a working remedy (the `--apply` resume, and the manual clear the existing refusal names), so this is a declined enhancement rather than a gap this plan leaves behind.
- TEACHING `finalize_precheck` ABOUT THE JOURNAL. That is `bn58ha`/`hlv737`, already authored and approved (F-12). Doing it here would duplicate an approved plan's deliverable.
  - Carrier: hlv737
  - Carrier-Evidence: .aw/records/plans/executed/20260929-bn58ha-01-hlv737-make-finalize-precheck-report-the-wedged-finalize-journal-it.ipd.md
- ADDING A CONSUMER of the new finding id (a runner retry branch, a disposition rule). Minting and surfacing it is this plan's deliverable; deciding what a driver should DO on seeing it is a policy question with its own risk.
  - Carrier-Declined: No consumer is REQUIRED for this fix to be complete: the defect is that a preview mutates, and E-04 closes that. An id with no consumer is the deliberate end state (the same shape the `FINDING_RECEIPT_*` family shipped in), not an unfinished half.
- THE `run_begin` / receipt-minting side. Nothing here changes when a receipt is created, only which invocations may spend one.
  - Carrier-Declined: A STATEMENT OF WHAT IS UNTOUCHED, recorded to bound the diff for a reviewer. There is no obligation here to carry.

## Scope check

- Over-scope: none. The four `- Scope-Paths:` entries are the implementation file, its existing test module, the orchestrator-retirement test module (ADDED at review for E-06's fifth control, which needs that file's Set fixture and cannot be written in `test_ipd_lifecycle_cli.py`), and the changelog. `status_set.py` is NOT in scope even though F-7 measures its `--dry-run` surfaces as defective, because they are defective only by delegation: they pass `apply` through faithfully and are fixed by the helper change, measured. `runner_shared.py` is not in scope for the reason F-11 gives.
- Under-scope: the second call site, `retire_orchestrator`, lives in the same file already in scope, so no path is missing. Review re-measured the in-tree caller set to confirm nothing else is: `finalize` has exactly TWO in-tree callers, `ipd_lifecycle.run_finalize` and `status_set._delegate_plan_executed_to_finalize`, and `_early_recovery_result` has exactly two, both inside `ipd_lifecycle.py`. If an executor finds that forwarding the flag requires a signature change in `runner_shared.py` or `status_set.py`, that is a scope surprise and must be reconciled at finalize rather than absorbed silently; measurement says it does not, since both already pass `apply` positionally or by keyword and neither calls the helper directly.

## Required tests / validation

All tests are behavioral and drive real functions and the real CLI against real temporary git repositories, asserting on exit codes, messages, findings, journal phase, receipt existence and `HEAD`. No test reads production source, counts symbols, or asserts on comment text.

- E-01, E-02 and E-03 must each be run and FAIL at unmodified HEAD, with the failure pasted. A fix-first-then-test order cannot demonstrate that the defect was real or that the test detects it.
- E-06's controls must pin the `apply=True` resume, the reachability of recovery AFTER a preview, the `unknown-outcome` refusal under BOTH flag values, an ordinary journal-free preview, and (added at review) the rollup path UNCHANGED for both flag values on a wedged `committed-incomplete` orchestrator.
- NO TEST MAY ASSERT THAT A ROLLUP PREVIEW RESUMES A `committed-incomplete` JOURNAL. F-8 measures that arm unreachable through `retire_orchestrator`; a test asserting otherwise would pass only against a fixture that bypassed the status gate, and would then pin a behavior the shipped code does not have.
- The bare suite (`python3 -m pytest`) must be run before any source edit and again at the end, with both summary lines and FAILED sets pasted and compared.

## Spec / documentation sync

No `.spec.md` amendment. The behavior being corrected is not specified in a spec record: the contract it violates is stated in `cli.py`'s own `--apply` help text ("Perform the transition (default: preview the precheck)") and in `ipd_lifecycle.finalize`'s docstring, and this plan makes the code match that already-published contract rather than changing it. Nothing is added to `- Scope-Paths:` for a spec file, and no declared-spec-edit announcement should appear for this plan. `CHANGELOG.md` carries the single user-facing record (E-07).

## Open questions

### OQ-01: Should the preview's diagnostic severity be `warning` or `info`?

- Blocking: no
- Status: resolved
- Owner: opencode/its_direct-pt3-claude-opus-5-1m-us
- Resolution or deferral rationale: RESOLVED from repository evidence, not deferred to the human, because the repo answers it. `run_finalize`'s `EXIT_FINDINGS` branch constructs its diagnostics with `severity="error"`, which is correct there because that branch IS a refusal. Reusing `error` on an `EXIT_OK` preview would make a successful observation render as a failure, and `aw check`'s own severity vocabulary already distinguishes advisory findings from errors for exactly this reason. The executor should therefore use a non-error severity, and E-06's control asserting that an ordinary journal-free preview still reports clean with no diagnostics is what keeps the choice honest. The precise token is an implementation detail the executor picks to match the `Diagnostic` type's existing values; it is not a contract this plan fixes.
  - DEMONSTRATED AT REVIEW rather than left as reasoning, because this is a HOW question (it chooses a mechanism) and a resolution that only argues is undemonstrated. `result_types.Diagnostic` declares `severity: str = "error"` with the comment naming the full vocabulary `"error", "warning", "info"`, so both candidate tokens are legal. Constructed directly: a `CommandResult(status="clean", exit_code=0)` carrying one `severity="warning"` diagnostic emits `{"outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1}`, so a non-error severity on an `EXIT_OK` record does NOT flip `outcome` to `findings` (that reclassification happens only when `exit_code == 1`). The same record with no diagnostics emits `"findings":0` and no `diagnostics` key at all, which is the clean-preview control E-06 pins. Either `warning` or `info` therefore satisfies the requirement; `warning` is the better default because a recoverable wedged transaction is something an operator should act on, not merely note.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the pasted FAILING run of the new test at unmodified HEAD, showing the assertion that fired and that the observed state was journal `None` with the receipt absent; plus the pasted PASSING run after E-04, showing journal `committed-incomplete`, the receipt present, and `HEAD` unmoved. Both preconditions (phase and receipt presence at the wedge) must appear as asserted, not assumed.
  - Observed evidence:
    Failing run at unmodified HEAD:
    ```
    FAILED tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_preview_on_committed_incomplete_preserves_journal_and_receipt
    AssertionError: unexpectedly None : journal was cleared by preview
    ```
    Passing run after E-04:
    ```
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_finalize_preview_on_committed_incomplete_preserves_journal_and_receipt PASSED [100%]
    ```
    Observed: preconditions verified (journal phase committed-incomplete, receipt present), and after finalize(apply=False) the journal remained committed-incomplete, receipt remained present, and HEAD was unmoved.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: the pasted FAILING run showing the real CLI, invoked with an argv containing no `--apply`, printing `finalized abc123 -> executed at <sha>` and consuming the receipt; and the pasted PASSING run after E-04 showing the preview message with journal and receipt intact. The argv actually used must be pasted, so a reader can confirm `--apply` is genuinely absent.
  - Observed evidence:
    Failing run at unmodified HEAD:
    ```
    FAILED tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_cli_finalize_preview_on_committed_incomplete_preserves_journal_and_receipt
    AssertionError: unexpectedly None : journal was cleared by real CLI preview (output: finalized abc123 -> executed at f75175cf9642 (actor opencode/test).)
    ```
    Passing run after E-04:
    ```
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_cli_finalize_preview_on_committed_incomplete_preserves_journal_and_receipt PASSED [100%]
    ```
    Argv used:
    `["ipd", "finalize", "abc123", "--dir", str(self.root), "--actor", "opencode/test", "--message", "preview message"]`
    (no `--apply`). Preview printed `WOULD RESUME: finalize for abc123 is in committed-incomplete ...`, exited 0, and preserved journal and receipt intact.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: the pasted FAILING run for BOTH `aw set executed ... --dry-run` and `aw ipd set executed ... --dry-run`, each showing the receipt consumed; and the pasted PASSING run after E-04 showing both preserving journal and receipt. Both spellings must appear, since one passing does not imply the other.
  - Observed evidence:
    Failing run at unmodified HEAD:
    ```
    FAILED tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_cli_set_executed_dry_run_on_committed_incomplete_preserves_journal_and_receipt
    AssertionError: unexpectedly None : journal was cleared by set executed --dry-run (output: aw set -> ipd finalize: finalized abc123 -> executed at b2b950bcdfa0 (actor opencode/test).)
    ```
    Passing run after E-04:
    ```
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_cli_set_executed_dry_run_on_committed_incomplete_preserves_journal_and_receipt PASSED [100%]
    ```
    Both `["set", "executed", ... "--dry-run"]` and `["ipd", "set", "executed", ... "--dry-run"]` exited 0, reported `WOULD RESUME: ...`, and preserved both journal and receipt intact.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the diff of `_early_recovery_result` and its two call sites, showing the keyword-only `apply` defaulting to `True`, the report returned before `acquire_finalize_lock`, and `apply=apply` forwarded from BOTH `finalize` and `retire_orchestrator`. Plus the comment text explaining why the apply test was not simply moved ahead of early recovery. REWRITTEN AT REVIEW: this item previously demanded pasted output of a `retire_orchestrator(..., apply=False)` call "showing it reports rather than resumes", which F-8's correction shows is UNOBTAINABLE (that arm is unreachable; the status gate refuses `already-terminal` first). Demand instead the pasted output of `retire_orchestrator(..., apply=False)` AND `(..., apply=True)` on a wedged `committed-incomplete` orchestrator showing BOTH return the `already-terminal` refusal with the journal left `committed-incomplete`, which is the honest confirmation that this plan did not change the rollup path, plus the `PHASE_UNKNOWN_OUTCOME` rollup preview returning `EXIT_CANNOT_RUN` unchanged. An executor who produces a "rollup preview reports instead of resuming" transcript has either patched the status gate (out of scope) or mis-built the fixture, and must stop and report rather than widen the diff.
  - Observed evidence:
    Diff of `_early_recovery_result`:
    ```python
    def _early_recovery_result(
        repo_root: Path,
        plan_path: Path,
        evidence: Dict[str, Any],
        *,
        apply: bool = True,
    ) -> Optional[FinalizeResult]:
        ...
        if phase == PHASE_COMMITTED_INCOMPLETE:
            # hernns y8cgvm E-04: when apply is False, report the recoverable committed-incomplete state
            # instead of performing the resume. The apply test cannot simply be moved ahead of early
            # recovery in finalize: that would also skip the PHASE_UNKNOWN_OUTCOME refusal, so a preview
            # of an ambiguously-wedged plan would report the ordinary precheck result and tell the operator
            # to proceed, which converts this bug into a worse fail-OPEN one.
            # Site this check before acquire_finalize_lock so a preview takes no writer lock.
            if not apply:
                lifecycle_commit = journal.get("lifecycle_commit") or "unknown"
                return FinalizeResult(
                    EXIT_OK,
                    None,
                    f"WOULD RESUME: finalize for {early_id} is in committed-incomplete "
                    f"(prior lifecycle commit {lifecycle_commit} already landed). "
                    f"Nothing changed and begin receipt was NOT consumed; "
                    f"re-invoke with --apply to complete post-commit steps.",
                    evidence,
                    (FINDING_FINALIZE_JOURNAL_COMMITTED_INCOMPLETE,),
                )
    ```
    Forwarded call sites:
    - In `retire_orchestrator`: `early = _early_recovery_result(repo_root, plan_path, evidence, apply=apply)`
    - In `finalize`: `early = _early_recovery_result(repo_root, plan_path, evidence, apply=apply)`
    Observed rollup output on wedged committed-incomplete orchestrator:
    - `apply=False`: `exit_code=1`, `message="REFUSED: orc000 carries Status 'executed', which is already terminal; there is nothing to retire."`, `findings=('already-terminal',)`, `journal_phase='committed-incomplete'`
    - `apply=True`: `exit_code=1`, `message="REFUSED: orc000 carries Status 'executed', which is already terminal; there is nothing to retire."`, `findings=('already-terminal',)`, `journal_phase='committed-incomplete'`
    - `PHASE_UNKNOWN_OUTCOME` rollup preview: `exit_code=2`, `message='finalize journal for orc000 is in unknown-outcome (ambiguous prior attempt); resolve manually and clear ...'`, `findings=('sim-unknown',)`
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: the new constant's definition pasted beside the existing `FINDING_RECEIPT_NEVER_ISSUED` / `FINDING_RECEIPT_ALREADY_FINALIZED` lines showing the same token form; and the actual stdout of the no-apply preview in ALL THREE output modes (human, `--json`, `--agent`), pasted and not predicted. CORRECTED AT REVIEW: this item previously demanded "the id present in each", which F-13 measures as unobtainable in compact `--agent` mode (it renders `{"location","rule"}` only and drops `detail`, and `--verbose` is unregistered on this subparser). The honest bar: the id's TEXT appears in the human line and in `--json`'s `diagnostics[].detail`, and the `--agent` record shows `"findings":1` with `"rule":"IPD-FINALIZE"`, exit 0. Also paste an ordinary journal-free preview in `--agent` mode showing `"findings":0` still, which is what proves the surfacing change did not make every clean preview emit noise. If an executor finds a way to carry the id text into compact `--agent` output WITHOUT changing the `rule` convention or registering a new flag, that is a scope surprise to reconcile at finalize, not to absorb silently.
  - Observed evidence:
    Constant definition in `agent_workflows/ipd_lifecycle.py`:
    ```python
    FINDING_RECEIPT_NEVER_ISSUED = "receipt-never-issued"
    FINDING_RECEIPT_ALREADY_FINALIZED = "receipt-consumed-already-finalized"
    FINDING_RECEIPT_STALE = "plan content digest no longer matches the receipt"
    FINDING_FINALIZE_JOURNAL_UNKNOWN_OUTCOME = "finalize-journal-unknown-outcome"
    FINDING_FINALIZE_JOURNAL_COMMITTED_INCOMPLETE = "finalize-journal-committed-incomplete"
    ```
    Actual stdout in all three modes on committed-incomplete:
    Human mode:
    ```
    WOULD RESUME: finalize for abc123 is in committed-incomplete (prior lifecycle commit 7ab882a5dc70c705b197005fafc00d4c8625c277 already landed). Nothing changed and begin receipt was NOT consumed; re-invoke with --apply to complete post-commit steps.
      IPD-FINALIZE finalize-journal-committed-incomplete
    ```
    JSON mode:
    ```json
    {
      "schema": "aw.agent/v1",
      "command": "ipd finalize",
      "status": "clean",
      "exit_code": 0,
      "summary": "WOULD RESUME: finalize for abc123 is in committed-incomplete (prior lifecycle commit 7ab882a5dc70c705b197005fafc00d4c8625c277 already landed). Nothing changed and begin receipt was NOT consumed; re-invoke with --apply to complete post-commit steps.",
      "verified": true,
      "complete": true,
      "diagnostics": [
        {
          "location": ".aw/records/plans/executed/20260824-demo-01-abc123-demo.ipd.md",
          "rule": "IPD-FINALIZE",
          "detail": "finalize-journal-committed-incomplete",
          "severity": "warning"
        }
      ],
      "changes": [],
      "evidence": [],
      "next_actions": [],
      "data": {
        "commit": null,
        "evidence": {}
      }
    }
    ```
    Agent mode:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd finalize","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":1,"diagnostics":[{"location":".aw/records/plans/executed/20260824-demo-01-abc123-demo.ipd.md","rule":"IPD-FINALIZE"}],"next":null}
    ```
    Clean ordinary preview (no journal) in agent mode:
    ```json
    {"schema":"aw.agent/v1","kind":"result","cmd":"ipd finalize","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"next":null}
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted passing output for each of the FOUR controls, with the concrete observed values quoted: the `apply=True` resume's exit code, cleared journal, consumed receipt and unmoved `HEAD`; the preview-then-apply sequence's second exit code; the `unknown-outcome` exit code under BOTH `apply=False` and `apply=True`; and the journal-free preview's message and empty findings tuple. The rollup control moved to V-08 at review.
  - Observed evidence:
    Passing test output:
    ```
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_controls_apply_true_resumes_and_recovery_reachable_after_preview PASSED [ 50%]
    tests/test_ipd_lifecycle_cli.py::RollbackFailureSemanticsTests::test_controls_unknown_outcome_and_ordinary_preview_unchanged PASSED [100%]
    ```
    Concrete observed values:
    - Control 1 (`apply=True` resume): `exit=0`, `journal=None`, `receipt_exists=False`, `head_unmoved=True`
    - Control 2 (preview-then-apply): `preview_exit=0`, `apply_exit=0`, `journal=None`, `receipt_exists=False`, `head_unmoved=True`
    - Control 3 (unknown-outcome): `fault_exit=2`, `preview_exit=2`, `apply_exit=2` (exit 2 for both flag values)
    - Control 4 (clean preview): `exit=0`, `message='precheck + reconciliation passed; re-run with --apply to perform the terminal transaction.'`, `findings=()`
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: the pasted passing run of the new rollup control, quoting the observed exit code, the finding tuple, and the journal phase read back AFTER each call, for BOTH `apply=False` and `apply=True`. The two flag values must show the SAME refusal, since that sameness is the whole claim. Also state explicitly that no assertion in the new test claims the rollup preview reports a recoverable state, since F-8 measures that arm unreachable and such an assertion could only pass against a fixture that bypassed the status gate.
  - Observed evidence:
    Passing test output:
    ```
    tests/test_orchestrator_retirement.py::TheSharedGatesActuallyFireOnTheRollupPath::test_committed_incomplete_rollup_remains_unreachable_control PASSED [100%]
    ```
    Concrete observed values:
    - `apply=False`: `exit_code=1`, `findings=('already-terminal',)`, `journal_phase='committed-incomplete'`
    - `apply=True`: `exit_code=1`, `findings=('already-terminal',)`, `journal_phase='committed-incomplete'`
    Both flag values produce the identical `already-terminal` refusal and preserve the journal. No assertion in the test claims the rollup preview reports a recoverable state (unreachable because status gate refuses first).
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: the added `CHANGELOG.md` line quoted verbatim, confirmed to sit under `## 2.0.0 (pending)` and to contain no em or en dash; plus the two BARE `python3 -m pytest` summary lines (before any source edit, and after all items) with their FAILED sets and an explicit statement of whether the sets are identical. A summary line showing a suppressed count (from a doubled `-q`) does not satisfy this.
  - Observed evidence:
    Verbatim `CHANGELOG.md` entry under `## 2.0.0 (pending)`:
    `- Fixed: `aw ipd finalize` and `aw set executed --dry-run` previews of a plan whose previous attempt was interrupted after its commit landed now report what they would do instead of silently completing the transition and spending the plan's begin receipt.`
    Confirmed no em or en dashes present.
    Bare suite baseline before any edits:
    `6637 passed, 2 skipped, 3 warnings in 934.42s (0:15:34)` (259 deselected)
    FAILED set: empty
    Bare suite after all edits:
    `6644 passed, 2 skipped, 3 warnings in 418.63s (0:06:58)` (259 deselected)
    FAILED set: empty
    Delta: exactly +7 passed tests corresponding to E-01, E-02, E-03, E-05, E-06 (x2), E-08.
    FAILED sets are identical (empty before and after).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `reviewed` (round 1 recorded in
`.aw/records/reviews/20261001-hernns-01-y8cgvm-stop-a-no-apply-finalize-preview-completing-the-committed-in.review.md`)
and must not be executed before the maintainer explicitly approves it; `- Readiness:
go-pending-approval` records that review cleared it and only sign-off is outstanding. Execution follows
the repository execution contract: commit only the paths named in
`- Scope-Paths:`, through `aw commit <plan> -- <paths>`, never `git add -A` and never pushing; paste
ACTUAL runner output for every test claim rather than asserting success; and leave any file not named
here untouched, including a co-worker's uncommitted changes in this shared checkout.

The terminal lifecycle move is NOT performed by hand. In a managed lane the runner owns begin/finalize
and `AW-LIFECYCLE-ROLE-001` refuses them to a worker, so an executing agent writes the outcome file its
turn prompt names and stops; the driver transitions the plan. In an unmanaged or manual run the executor
performs the transition with `aw ipd finalize`, which is the only supported route to `executed`, and only
after `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete pasted
evidence.
