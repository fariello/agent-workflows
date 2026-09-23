# IPD: Verify the laneorph Set's combined outcome from the main checkout

- Date: 2026-09-21
- Kind: child
- Concern: The `laneorph` Set's acceptance check has no owner that can be trusted to perform it. It sits on the Order-0 orchestrator `tb63qv` as that plan's only `E-*` item, and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint, on the premise that a parent's own items are performed by nobody. That premise is false here, so the Set's combined verification would be reported complete having never been performed or verified. MEASURED 2026-09-22 by the orchestrator coverage probe, which refused the whole 34-set launch naming `tb63qv` among five parents carrying work no child covers (event `orchestrator-probe-gate`, emitted at `runner_shared` symbol `run_orchestrator_probe_gate`). This plan is the child that OWNS that verification, so the parent's checklist becomes a real obligation performed by a real agent turn.
  THE FALSE-CLEAN PREMISE THIS PLAN INHERITED IS ITSELF FALSE, and correcting it is the most important change this plan's review made. The parent's E-01 asserts that `.aw/records/runs/` is "gitignored and ABSENT inside a lane, so `stranded_lane_drift` returns `[]`" and that an in-lane check therefore reports a FALSE clean; this plan lifted that verbatim and built its whole measuring-tree rule on it. MEASURED AT REVIEW HEAD `a1dbb05a`, FROM INSIDE AN ISOLATED LANE: `attention.stranded_lane_drift(Path('.'))` returns THIRTEEN `attention.lane-stranded` records, not `[]`, and `aw attention --check` exits 1. The cause is `attention._resolve_runs_repo_root`, which detects `.aw/worktrees` in the resolved path and walks up to the owning checkout (measured: resolved root is the main checkout, not the lane), so the run records ARE reachable from a lane. It was added 2026-09-08 in commit `699c1fc7`, TEN DAYS BEFORE the parent's 2026-09-18 review, so the claim was wrong when written rather than merely stale. Also wrong in passing: the directory is UNTRACKED, not gitignored (`git check-ignore` exits 1 on it), which is why it is absent from a fresh worktree but reachable through the shared parent.
  WHAT SURVIVES THE CORRECTION, because the conclusion is right for a different reason. An in-lane measurement is still not the SET-LEVEL measurement this plan owes: `_resolve_runs_repo_root` reaches the main checkout's run records, so arm (a) is answerable from a lane, but arms (b) and (c) are about the WORKTREE POPULATION and a live run's own teardown, and a lane is itself one of the worktrees being counted. So the measuring tree must still be NAMED in every figure, and this plan must still say where it stood. What changes is the failure mode: an in-lane arm (a) does NOT silently report empty, so the hazard is not a false clean, and an executor must NOT refuse arm (a) merely for being in a lane (see OQ-01, whose answer is reversed).
- Scope: Perform the Set-level acceptance check `tb63qv` E-01 describes, from the MAIN CHECKOUT, and record its evidence. IN: the three combined-outcome measurements (`aw attention --check` stranded-lane state, `git worktree list`, and a driver run leaving no worktree behind), each naming the tree it was measured in; plus the two backlog closures the Set's completion criteria require, which no other child owns. OUT: any change to lane reclaim, teardown, or attention CODE (that is Order 01 `65cuw0`), any branch disposition or deletion (that is Order 02 `ut0vzr`), and any re-performance of either child's own validation - this plan READS their recorded evidence and measures the COMBINED result, it does not redo their work.
- Scope-Paths: .aw/records/plans/pending, .aw/records/backlog/open, .aw/records/backlog/done
- Item-Dependencies: executed:65cuw0, executed:ut0vzr
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: a58s04
- Blocks-Release: next
- Set: laneorph
- Order: 3
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: k311gw
- Approval: 2026-09-23, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-23 approved (aw set): status set to approved
- 2026-09-22 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. THE PLAN SHOULD EXIST - the parent `tb63qv` genuinely carries its only E-item with no child owning it, re-verified in code rather than from the gitignored run log (`evaluate_set_retirement` -> `Set 'laneorph' has 2 child(ren) that are not 'executed'`). PR-001 (BLOCKER): THE FALSE-CLEAN PREMISE THIS PLAN IS BUILT ON IS FALSE, AND WAS FALSE WHEN WRITTEN. The plan lifted the parent's claim that `.aw/records/runs/` is gitignored and absent in a lane so `stranded_lane_drift` returns `[]` and an in-lane check reports a FALSE clean, and instructed any lane-side executor to REFUSE the measurement. Measured from inside an isolated lane at HEAD `a1dbb05a`: `stranded_lane_drift` returns THIRTEEN `attention.lane-stranded` records and `aw attention --check` exits 1, because `attention._resolve_runs_repo_root` detects `.aw/worktrees` in the resolved path and walks up to the owning checkout. That escape hatch landed 2026-09-08 in `699c1fc7`, TEN DAYS before the parent's 2026-09-18 review, so this is not staleness. Two further corrections: the directory is UNTRACKED not gitignored (`git check-ignore` exits 1), and `git worktree list` reads the shared `.git` so it does not differ by tree as the parent implies. The old instruction would have declined a working measurement and presented the refusal as diligence - a false NEGATIVE, the mirror image of the false clean it guarded against. E-01, OQ-01 (answer REVERSED, original retained), F-02, V-01 and the honesty rule all corrected; the tree still matters for arms (b) and (c) on a reason that survives measurement (a lane is itself one of the worktrees being counted; a worker cannot witness its own teardown). PR-002 (HIGH): E-02's spanning criterion 2 asked for a NECESSARY BUT NOT SUFFICIENT condition - `worktree_lease.LaneState.reclaimable`'s own docstring says exactly that and records that its 'safe to tear down' wording was WITHDRAWN, because `dirty` derives from a porcelain blind to IGNORED files; the sufficient gate is `lane_containment.teardown_lane_if_classified` (spec `7ckptx` R5.5), which the criterion never mentioned. PR-003 (MEDIUM): the receipt check would have misread decision `08-65cuw0-D3` as an upstream failure and blocked the Set on a divergence the maintainer already owns. PR-004 (HIGH): the plan is not runnable at review HEAD - `executed:65cuw0` is satisfied but `executed:ut0vzr` is not (`approved`, 8 empty evidence blocks), so E-02 can only take its failure path; stated with the run order and explicitly NOT treated as a plan defect. PR-005 (MEDIUM): the Set's release gate died at its verifying child (`a58s04` is a release-blocking bug, `65cuw0` carries its `From-Backlog` + gate, this plan carried neither) - set through the setter. PR-006 (MEDIUM): E-03 relied on a close-legitimacy refusal that does not come (`evaluate_blocking_close` returns legitimate via HANDOFF with no evidence), so exit 0 proves nothing about the closure message, which is the deliverable. PR-007 (LOW): four Deferred rows lacked a durable carrier and the workflow history was oldest-first, reading as a backwards `to-review` -> `draft` transition. PR-008 (LOW): this plan's completion criterion is a green tree, which makes it unusually sensitive to another party's breakage, so Required tests now names the two failures measured at review HEAD that are NOT from this work. `aw ipd lint --phase author` conforming before, `--phase review-finalize` conforming after.

- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `tb63qv` as carrying work no child covers. Content is LIFTED from the parent's own E-01 and completion criteria rather than invented, so the obligation is unchanged and only its OWNER moves; the parent's checklist stays in place, per the repository rule that deleting it breaks a hand-run `execute <setid>`.
- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Give the `laneorph` Set's acceptance check an owner that actually runs. The parent states the check
correctly; what it cannot do is perform it, because a retiring orchestrator spends no agent turn. After
this plan executes, "the leak is closed and the backlog is drained" is a claim backed by pasted evidence
measured in a named tree, rather than an unticked box on a plan the runner marked complete.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance, measured where it is true

- [ ] E-01 MEASURE THE COMBINED OUTCOME FROM THE MAIN CHECKOUT, and name that tree in every figure. Three measurements, all three required: (a) `aw attention --check` reports no stranded lane, OR exactly the maintainer-deferred ESCALATE set that Order 02 recorded; (b) `git worktree list` shows only the main checkout plus any lane a LIVE run owns; (c) a subsequent driver run leaves no worktree behind for the item it integrated.
  THE MEASURING TREE IS LOAD-BEARING, AND THE REASON IS NOT THE ONE THE PARENT GIVES. Corrected at review, measured from inside an isolated lane at HEAD `a1dbb05a`: `attention.stranded_lane_drift` returns THIRTEEN `attention.lane-stranded` records from a lane and `aw attention --check` exits 1, because `attention._resolve_runs_repo_root` detects `.aw/worktrees` in the path and walks up to the owning checkout to find the run records. So there is NO false clean, and the parent's stated mechanism ("gitignored and ABSENT inside a lane, so `stranded_lane_drift` returns `[]`") is false - doubly so, since the directory is UNTRACKED rather than gitignored. DO NOT REFUSE ARM (a) MERELY FOR BEING IN A LANE: that refusal was this plan's original instruction and it would now decline a measurement that works.
  WHY THE TREE STILL MATTERS, per arm. Arm (a) is answerable from EITHER tree, so name the tree and paste it. Arms (b) and (c) are NOT: (b) counts the worktree POPULATION, and a lane is itself one of the worktrees being counted, so a lane-side count includes the counter and cannot be compared against "only the main checkout plus any live lane"; (c) requires observing a driver run's own teardown, which a worker turn inside that very lane cannot witness. So if you are executing in a lane, arm (a) is REQUIRED and arms (b) and (c) must be REFUSED with the tree named, which is the opposite allocation to the one this item originally carried.
  - Depends on: none
  - Expected outcome: `git rev-parse --show-toplevel` pasted FIRST, then arm (a) performed in whichever tree you are in, plus arms (b) and (c) either performed from the main checkout or explicitly REFUSED with the reason (a lane cannot count itself; a worker cannot witness its own teardown). An explicit statement of which `attention` arm was satisfied (genuinely empty versus exactly the deferred ESCALATE set, ENUMERATED). Refusing arm (a) because the tree is a lane FAILS this item, since that measurement demonstrably works from a lane.
  - Execution state: pending

- [ ] E-02 READ BOTH CHILDREN'S RECORDED EVIDENCE AND CONFIRM THE SET'S OWN COMPLETION CRITERIA, without re-performing either child's work. This is a RECEIPT CHECK: open `65cuw0` and `ut0vzr`, confirm each is `executed` with its `V-*` items carrying observed evidence rather than empty blocks, and confirm the two criteria that span them both. If either child's evidence is absent or contradicts its checkmark, REPORT THAT and do not compensate by re-deriving the result: a receipt check that silently becomes a re-verification hides an upstream validation failure.
  SPANNING CRITERION 1, unchanged: every one of the 13 unmerged branches has a recorded disposition with cited evidence immortalized under `.aw/records/research/` BEFORE any deletion. Measured at review, no such artifact exists yet, which is consistent with `ut0vzr` being unexecuted and is what you should expect to find.
  SPANNING CRITERION 2, CORRECTED AND EXTENDED AT REVIEW, because as written it asked for a NECESSARY BUT NOT SUFFICIENT condition and would have passed a lane that is unsafe to delete. The original wording ("a merged-and-clean lane reports `reclaimable=True` while a merged lane with an UNTRACKED file does not") is TRUE and must still be confirmed - `worktree_lease.LaneState.reclaimable` is real, is the interrupt-path reading, and `65cuw0` E-02 is what taught it the merged case. But that property's own docstring opens "Provably EMPTY or provably RECOVERED. NECESSARY BUT NOT SUFFICIENT for teardown", and records that its previous "safe to tear down" wording was WITHDRAWN at review precisely because `dirty` comes from a plain `git status --porcelain` that is BLIND TO IGNORED FILES, with the measurement that `git worktree remove` without `--force` exits 0 and DELETES a lane holding only an ignored file. SO ALSO CONFIRM THE SUFFICIENT GATE: that the success-path teardown routes through `lane_containment.teardown_lane_if_classified` (the spec `7ckptx` R5.5 inventory gate), and that `65cuw0` recorded the two refusal shapes it pins - an uncollected submission preserved, and the `wfamig` untracked-file class preserved. A receipt check confirming only `reclaimable` would sign off the exact reading whose authorization claim was withdrawn.
  AND DO NOT FAIL `65cuw0` FOR A WORDING MISMATCH THE MAINTAINER ALREADY OWNS. That plan's E-02 evidence records a DELIBERATE divergence from its own item wording: the gitignored case is `reclaimed`, not preserved, and no `unknown-ignored-file` code is emitted, because spec `7ckptx` R5.5 was amended by `laneign` (`5w8g8j`) to make gitignored content DISPOSABLE on lane destruction. Honoring the literal wording would have FORKED R5.5 and red-ed `tests/test_lane_retention.py::test_a_lane_holding_ONLY_gitignored_files_IS_torn_down`. It is recorded as decision `08-65cuw0-D3` with human review requested. Read it as a recorded decision, not as evidence contradicting a checkmark.
  - Depends on: E-01
  - Expected outcome: a per-child statement naming the `V-*` items read and quoting the evidence line that satisfies each spanning criterion, INCLUDING both halves of criterion 2 (the `reclaimable` reading AND the R5.5 `teardown_lane_if_classified` gate with its two pasted refusal shapes), or a named upstream failure. Note whether `65cuw0`'s `08-65cuw0-D3` wording divergence has since been resolved by a human, and report it either way rather than treating it as a defect.
  - Execution state: pending

- [ ] E-03 CLOSE BACKLOG `a58s04` AND `qliia1` HONESTLY, which is the one substantive record change no child owns. `qliia1` is Order 02's to close by its own scope; confirm it and close it if it is still open (measured at review: still `open`, `Work-Kind: followup`, no release gate). `a58s04` REQUIRES A CORRECTION RATHER THAN A CLAIM OF IMPLEMENTATION: its "Expected" and "Fix sketch" sections (steps 3 and 4) carry the SAME TWO REFUTED PREMISES as this Set's original Concern - that `aw attention` does not already exclude a merged lane, and that `reclaimable` governs the end-of-run leak - and the 2026-09-18 review measured both false (`aw attention` asks the merged question through `runner_shared.lane_work_has_landed` and omits `LANDED` from `LANE_ATTENTION_STATES`; `reclaimable`'s only readers sit inside `reclaim_lanes_on_interrupt`, while the successful-run teardown is the already-wired `lane_containment.teardown_lane_if_classified`). So close it with `aw backlog set done` and a message that RECORDS THE CORRECTION; do NOT write a closure implying the sketch was carried out.
  `a58s04` IS A RELEASE-GATED BUG AND THE CLOSE GATE WILL NOT STOP YOU, measured at review HEAD `a1dbb05a`: it carries `Blocks-Release: next` and `Work-Kind: bug`, and `check_engine.evaluate_blocking_close(repo, a58s04, "done", evidence=None)` returns LEGITIMATE via route HANDOFF with NO evidence passed, because `65cuw0` carries `From-Backlog: a58s04` with the same gate and HANDOFF is checked before SATISFIED. HERE THAT IS HONEST rather than a loophole - unlike the general case, the single handoff carrier is genuinely `executed` - but it means exit 0 proves nothing about your closure MESSAGE, which is the actual deliverable. Pass `--evidence` citing `65cuw0`'s executed plan anyway, expect the route to report HANDOFF rather than SATISFIED, and do NOT clear the gate with `--blocks-release -`.
  - Depends on: E-02
  - Expected outcome: both items `done` via `aw backlog set`, with `a58s04`'s closure message naming both refuted premises and the evidence that refuted them; pasted command output for each, plus the route the close-legitimacy predicate reported (expected HANDOFF) and confirmation the gate was not cleared.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD rather than to delete the parent's items. `AGENTS.md` states this directly and gives the reason: the parent's checklist is what makes a hand-run `execute <setid>` complete when no runner is involved, so deleting it causes the lost work it exists to prevent. This plan therefore ADDS coverage and changes nothing on `tb63qv` except its child table.
- THE ORCHESTRATOR COVERAGE GATE IS THE MECHANISM THAT FOUND THIS, and its verdict is cached on the parent's item text plus its child table, so adding this row re-probes automatically. Specified in `25kzda` 2.5b and `77tr3o` R-12.
- ONE DEFINITION OF "MERGED" EXISTS AND THIS PLAN MUST NOT ADD A SECOND: `runner_shared.lane_work_has_landed`, which is deliberately THREE-VALUED (`True`/`False`/`None` for unanswerable). A verification that collapses `None` into either boolean is asserting something the codebase refuses to assert.
- `reclaimable` IS A READING, NOT AN AUTHORIZATION, and the distinction is written into the code. `worktree_lease.LaneState.reclaimable` opens "Provably EMPTY or provably RECOVERED. NECESSARY BUT NOT SUFFICIENT for teardown" and records that its earlier "safe to tear down" wording was WITHDRAWN at review, because `dirty` comes from a plain `git status --porcelain` that cannot see IGNORED files. The sufficient gate is `lane_containment.teardown_lane_if_classified` (spec `7ckptx` R5.5). Any verification of teardown safety must name BOTH (F-05).
- A LANE CAN READ THE MAIN CHECKOUT'S RUN RECORDS, which is the opposite of what this Set's parent assumed. `attention._resolve_runs_repo_root` detects `.aw/worktrees` in the resolved path and walks up to the owning root, so `stranded_lane_drift` and `aw attention --check` both work from inside a lane (measured: 13 records, exit 1). Added 2026-09-08 in `699c1fc7`. Do not write a new plan on the false-clean premise (F-02).
- A RELEASE GATE IS INHERITED, NOT RE-DECIDED PER CHILD (`AGENTS.md`), and EVERY LIVE BUG GATES THE NEXT RELEASE. `a58s04` is an `open` `Work-Kind: bug` carrying `Blocks-Release: next`, and this plan closes it, so this plan carries the gate and `From-Backlog` (F-08).
- THE CLOSE-LEGITIMACY GATE CHECKS HANDOFF BEFORE SATISFIED, so an item with an existing `From-Backlog` carrier is already legitimate before any `--evidence` is offered; measured for `a58s04`, legitimate with `evidence=None` via HANDOFF. Here the sole carrier (`65cuw0`) is genuinely `executed`, so the outcome is honest - but exit 0 still proves nothing about the closure MESSAGE, which is E-03's real deliverable.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `runner_shared` symbol `run_orchestrator_probe_gate`, event `orchestrator-probe-gate`; `runner_shared.evaluate_set_retirement` run at HEAD `a1dbb05a` | The coverage probe refused a 34-set launch naming `tb63qv` among five uncovered parents. Without this child the Set's only acceptance check is performed by nobody and reported complete. RE-VERIFIED IN CODE rather than from the gitignored run log: `evaluate_set_retirement(repo, 'laneorph')` returns `eligible=False`, `reason=unfinished-children`, `detail="Set 'laneorph' has 2 child(ren) that are not 'executed': ut0vzr (approved), k311gw (to-review)"`. |
| F-02 | BLOCKER | `attention.stranded_lane_drift(Path('.'))` run from INSIDE this lane at HEAD `a1dbb05a` -> 13 `attention.lane-stranded` records; `attention._resolve_runs_repo_root(Path('.'))` -> the main checkout, not the lane; `aw attention --check` from the lane -> exit 1; `git check-ignore .aw/records/runs` -> exit 1 (NOT ignored); `git log -S` -> the worktree-escape added 2026-09-08 in `699c1fc7` | THE FALSE-CLEAN PREMISE IS FALSE, AND IT WAS FALSE WHEN WRITTEN. This row formerly restated the parent's claim that `.aw/records/runs/` is "gitignored and absent in a lane, making an in-lane `stranded_lane_drift` return `[]` and report a false clean", and instructed any lane-side executor to REFUSE the measurement. Measured from inside a lane, `stranded_lane_drift` returns THIRTEEN records and `--check` exits 1, because `_resolve_runs_repo_root` detects `.aw/worktrees` in the resolved path and walks up to the owning checkout. That escape hatch landed 2026-09-08, TEN DAYS before the parent's 2026-09-18 review, so this is not staleness. Two further corrections: the directory is UNTRACKED, not gitignored; and `git worktree list` reads the shared `.git` (`git rev-parse --git-common-dir` -> the main checkout's), so it does not differ by tree in the way the parent's "a lane sees 13 where the main checkout sees a different set" implies. CONSEQUENCE: the original instruction would have made an executor decline a working measurement and report a refusal as the honest outcome, which is a false NEGATIVE - the mirror image of the false clean it was guarding against. The tree still matters for arms (b) and (c) for a DIFFERENT reason, now stated. |
| F-03 | MEDIUM | `tb63qv` completion criteria, quoted; `a58s04` front matter at HEAD `a1dbb05a` (`Status: open`, `Blocks-Release: next`, `Work-Kind: bug`) | Closing `a58s04` requires recording a CORRECTION: two of its fix-sketch steps rest on premises the 2026-09-18 review measured false. A closure claiming implementation would write a false history. |
| F-04 | MEDIUM | `tb63qv` OQ-03, quoted | The Set's `attention --check` criterion is not achievable as literally written: deleting a DELETE branch converts its `attention.lane-stranded` row into an equally-failing `attention.lane-unknown` row. E-01 therefore accepts the maintainer-deferred ESCALATE set as the satisfying arm, and requires it to be ENUMERATED rather than waved at. |
| F-05 | HIGH | `worktree_lease.LaneState.reclaimable` docstring: "Provably EMPTY or provably RECOVERED. NECESSARY BUT NOT SUFFICIENT for teardown ... the previous docstring's 'safe to tear down' was WITHDRAWN at review"; `65cuw0` E-02's pasted refusal shapes | E-02'S SPANNING CRITERION 2 ASKED FOR A NECESSARY-BUT-NOT-SUFFICIENT CONDITION and would have signed off a lane that is unsafe to delete. The `reclaimable` property is real and its merged case is exactly what `65cuw0` delivered, so the criterion is not wrong - but its own docstring records that the authorization claim was withdrawn, because `dirty` derives from a plain `git status --porcelain` blind to IGNORED files, measured with `git worktree remove` exiting 0 and DELETING a lane holding only an ignored file. The SUFFICIENT gate is `lane_containment.teardown_lane_if_classified` (spec `7ckptx` R5.5), which the criterion never mentioned. A receipt check confirming only `reclaimable` endorses the reading whose safety claim was explicitly retracted. |
| F-06 | MEDIUM | `65cuw0` E-02 evidence, decision `08-65cuw0-D3`; `tests/test_lane_retention.py::test_a_lane_holding_ONLY_gitignored_files_IS_torn_down` | THE RECEIPT CHECK WOULD HAVE MISREAD A RECORDED DECISION AS A FAILURE. `65cuw0`'s evidence documents a deliberate divergence from its own item wording (the gitignored case is `reclaimed`, not preserved, and emits no `unknown-ignored-file` code) because spec `7ckptx` R5.5 was amended by `laneign` (`5w8g8j`) to make gitignored content disposable; honoring the literal wording would have forked R5.5 and red-ed a named test. E-02 told its executor to REPORT any evidence that "contradicts its checkmark", so a diligent reader would have flagged this as an upstream failure and blocked the Set on a decision the maintainer already owns and has been asked to review. |
| F-07 | HIGH | `oc_runipd.dependency_status_detailed` on `['executed:65cuw0','executed:ut0vzr']` at HEAD `a1dbb05a` -> unsatisfied `executed:ut0vzr`, "external target ut0vzr is 'approved' (directory 'pending')"; `65cuw0` 0 empty evidence blocks / 5 `Result: pass`; `ut0vzr` 8 empty blocks / 8 `Result: pending` | THE PLAN IS NOT RUNNABLE AT REVIEW HEAD AND E-02 CAN ONLY TAKE ITS FAILURE PATH. One of its two dependencies is met (`65cuw0` is `executed` with real evidence) and the other is not (`ut0vzr` is `approved` with all eight `Observed evidence` blocks empty). No research artifact for the 13 branch dispositions exists yet either, consistent with that. NOT a plan defect - the runner re-checks edges at dispatch and marks the item `dependency-blocked` - but decision-relevant: executed today, E-02's honest output is a named upstream failure, and a reader must not mistake that for this plan malfunctioning. |
| F-08 | MEDIUM | This plan's front matter against `tb63qv`'s and `65cuw0`'s; `a58s04` (`Blocks-Release: next`); `AGENTS.md` release-gate inheritance | THE SET'S RELEASE GATE DIED AT ITS VERIFYING CHILD. `a58s04` is a release-blocking `bug`, `65cuw0` carries `From-Backlog: a58s04` with `Blocks-Release: next`, and this plan - the one that CLOSES that item - declared neither field, so it was invisible to `aw attention`'s release-blocker set. The plan whose E-03 decides whether the gate is honestly discharged was the one not declaring it. |

## Proposed changes (ordered, validatable)

1. Measure the three combined-outcome facts, naming the tree, performing arm (a) wherever you are and
   refusing arms (b)/(c) with reasons if you are in a lane (E-01).
2. Read both children's recorded evidence and confirm the two spanning criteria, including BOTH halves of
   criterion 2 (the `reclaimable` reading and the R5.5 teardown gate) (E-02).
3. Close `qliia1` and `a58s04`, the latter with its correction recorded and its gate intact (E-03).

## Deferred / out of scope (with reason)

- ANY CODE CHANGE. Lane reclaim, teardown, and attention behavior belong to Order 01 `65cuw0`; branch
  disposition belongs to Order 02 `ut0vzr`. This plan measures their combined effect and touches no
  product code, which is why its `Scope-Paths` name only records.
  - Carrier: ut0vzr
- RE-PERFORMING EITHER CHILD'S VALIDATION. E-02 is a receipt check by design (see its own wording): a
  receipt check that quietly becomes a re-verification conceals an upstream validation failure instead of
  reporting it.
  - Carrier: ut0vzr
- THE PARENT'S CHECKLIST. `tb63qv` E-01 stays exactly as written; only its child table gains a row. See
  the conventions section for why deleting it would be the defect rather than the fix.
  - Carrier-Declined: NOT AN OBLIGATION, BUT ITS OPPOSITE. This row records that something must be LEFT
    ALONE, so there is no outstanding work for any record to carry, and filing a carrier would create an
    item whose only correct resolution is to do nothing. The parent's item is covered by THIS plan's E-01
    through E-03, which is the whole reason this plan exists.
- CORRECTING THE PARENT'S FALSE-CLEAN CLAIM IN `tb63qv` ITSELF (F-02). This plan's own E-01, OQ-01 and F-02
  now carry the measured correction, so an executor of THIS plan cannot be misled. But `tb63qv` E-01 still
  states the refuted premise in its own text, and it is `approved`, so a hand-run `execute laneorph` reading
  the parent directly would still be told to refuse a working measurement. Not fixed here because the parent
  is outside this plan's fence and is an approved plan another agent may be acting on.
  - Carrier-Declined: NOTHING IS LOST BY LEAVING IT, which is what makes declining honest rather than
    convenient. The parent's item is performed BY THIS PLAN, and this plan carries the corrected
    instruction, so the refuted sentence misleads nobody who executes the obligation. Recording it as a
    live obligation would assert that the Set is incomplete until a prose fix lands in a plan that is
    about to retire. E-01 and F-02 are the durable record of the correction.

## Scope check

- Over-scope: none. All three declared paths are needed: this plan's own file under `plans/pending`, and
  both `backlog/open` and `backlog/done` because `aw backlog set done` MOVES an item between them. Verified
  at review that `a58s04` and `qliia1` are both currently in `open/`.
- Under-scope: none. The parent carries exactly one `E-*` item plus the Set completion criteria, and E-01
  through E-03 cover the verification, the receipt check, and the record closures respectively.

## Required tests / validation

No product code changes, so there is no new unit test and no behavior-affecting test should move. The
validation IS the pasted measurement, plus a bare `python3 -m pytest` to demonstrate the tree is green at
the moment the Set is declared complete (a completion claim made against a red tree is not a completion
claim). BARE MEANS BARE: `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not
slow'`, so do not add `-n0`, a second `-q`, or `-p no:randomly`.

BASELINE IS A MEASUREMENT, NOT A CONSTANT: take your own count at your own HEAD rather than comparing
against a number written in any plan. AND KNOW WHICH FAILURES ARE NOT YOURS BEFORE YOU CLAIM A RED TREE
BLOCKS THE SET, because this plan's completion criterion is a green tree and that makes it unusually
sensitive to somebody else's breakage. Measured at review HEAD `a1dbb05a`, two tests were failing and
NEITHER came from this work (both verified by stashing these changes and re-running):
`tests/test_turn_bounds.py::TestArmedForEveryUnattendedTurn::test_the_permission_policy_by_contrast_IS_isolation_scoped`
(pre-existing, environment-dependent, asserts on the inherited process environment) and
`tests/test_orchestrator_retirement.py::RealRepositorySets::test_every_live_set_reaches_its_measured_verdict_for_its_measured_reason`
(its `commitguard` row expects child `2s0iym` `reviewed` where reality is `approved`, changed by an
unrelated concurrent commit; the refusal REASON is unchanged, so that row needs re-measuring per its own
guidance). Re-check both against a clean HEAD, attribute them honestly, and do NOT let a foreign red
failure be reported as this Set's completion criterion failing - say which failures are yours.

## Spec / documentation sync

N/A. This plan changes no contract: it performs a verification the parent already specified and closes two
backlog items the Set already required. The only structural edit is the child-table row on `tb63qv`, which
is what the coverage gate reads.

## Open questions

### OQ-01: If this plan is dispatched into an isolated lane, should it refuse E-01(a) or request a non-isolated run?

- Blocking: no
- Status: resolved
- Owner: none
- Finding: F-02
- Resolution or deferral rationale: **THE ORIGINAL ANSWER WAS WRONG AND IS REVERSED HERE. PERFORM ARM (a) IN THE LANE; REFUSE ONLY ARMS (b) AND (c).** Read the correction before the retained text below it.
  THE ORIGINAL ANSWER, RETAINED FOR THE RECORD: "REFUSE THE MEASUREMENT AND SAY SO, resolved from the parent's own evidence rather than deferred. `tb63qv` E-01 records that `.aw/records/runs/` is gitignored and therefore absent inside a lane, so `stranded_lane_drift` returns `[]` and an in-lane check reports a FALSE clean. A false clean is worse than a refusal, because it closes the Set on a measurement that could not have detected the failure. So an executor in a lane MUST state the tree, refuse E-01(a), and report that the item needs a main-checkout measurement; the runner's `--no-isolate-worktree` is the operator's remedy and is not this plan's to choose."
  WHY IT IS WRONG, measured at review HEAD `a1dbb05a` from inside an isolated lane rather than reasoned from the parent's prose: `attention.stranded_lane_drift(Path('.'))` returns THIRTEEN `attention.lane-stranded` records and `aw attention --check` exits 1. There is no false clean to guard against. The cause is `attention._resolve_runs_repo_root`, which detects `.aw/worktrees` in the resolved path and walks up to the owning checkout (measured: it resolves to the main checkout, not the lane), so a lane reaches the run records through the shared parent. That escape hatch was added 2026-09-08 in commit `699c1fc7`, ten days BEFORE the parent's 2026-09-18 review recorded the false-clean claim, so the premise was never true in this Set's lifetime. Two supporting corrections: `.aw/records/runs/` is UNTRACKED rather than gitignored (`git check-ignore` exits 1), which explains its absence from a fresh worktree without implying unreachability; and `git worktree list` reads the shared `.git` (`git rev-parse --git-common-dir` returns the main checkout's), so it does not vary by tree in the way the parent's framing suggests.
  THE COST OF THE OLD ANSWER, which is why this is a correction and not a nicety: it instructed an executor to DECLINE a working measurement and to report that refusal as the honest outcome. That is a false NEGATIVE, and it is the mirror image of the false clean it was written to prevent - the Set would have stalled on an unmeasurable-looking criterion that is in fact measurable from either tree.
  WHAT IS STILL REFUSED IN A LANE, on a reason that survives measurement. Arm (b) counts the WORKTREE POPULATION against "only the main checkout plus any lane a live run owns", and a lane is itself one of the worktrees being counted, so a lane-side count includes the counter and cannot satisfy the criterion. Arm (c) requires witnessing a driver run's own post-integration teardown, which a worker turn executing inside that very lane cannot observe. Both refusals are about what the measurement MEANS, not about what is readable. So: name the tree, perform (a), and refuse (b)/(c) with those reasons if you are in a lane. The runner's `--no-isolate-worktree` remains the operator's remedy for (b)/(c) and is still not this plan's to choose.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git rev-parse --show-toplevel` FIRST, then arm (a) `aw attention --check` (with its exit code), and arms (b) `git worktree list` and (c) the post-integration worktree check either performed from the main checkout or explicitly REFUSED with their reasons. State which `attention` arm was satisfied and, if it was the ESCALATE arm, ENUMERATE those lanes. An execution that pastes a clean `attention` result without naming the tree FAILS this item.
    AND REFUSING ARM (a) BECAUSE THE TREE IS A LANE ALSO FAILS THIS ITEM, which reverses what this item formerly implied. F-02 measured `stranded_lane_drift` returning 13 records and `--check` exiting 1 from inside a lane, because `_resolve_runs_repo_root` walks up to the owning checkout, so a lane-side refusal of (a) declines a measurement that demonstrably works. The refusable arms are (b), because a lane is itself one of the worktrees being counted, and (c), because a worker cannot witness its own teardown; name whichever you refused and why.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of `65cuw0` and `ut0vzr`, name the `V-*` items read and quote one evidence line per spanning criterion: (1) the 13 dispositions immortalized under `.aw/records/research/` before any deletion; (2) BOTH halves of the teardown-safety criterion - `reclaimable=True` for merged-and-clean and NOT for merged-with-untracked, AND the R5.5 gate `lane_containment.teardown_lane_if_classified` with `65cuw0`'s two pasted refusal shapes (uncollected submission preserved; the `wfamig` untracked class preserved). QUOTING ONLY THE `reclaimable` HALF FAILS THIS ITEM: that property's own docstring says "NECESSARY BUT NOT SUFFICIENT for teardown" and records that its "safe to tear down" claim was withdrawn, so a receipt check resting on it alone endorses a retracted safety claim (F-05).
    IF AN UPSTREAM EVIDENCE BLOCK WAS EMPTY OR CONTRADICTED ITS CHECKMARK, the required evidence is the STATEMENT of that failure, which satisfies this item while failing the Set. At review HEAD that is the expected outcome for `ut0vzr` (8 empty blocks, 8 `Result: pending`, because it has not executed) and NOT for `65cuw0` (0 empty blocks, 5 `Result: pass`).
    ONE THING THAT IS NOT AN UPSTREAM FAILURE, and reporting it as one FAILS this item: `65cuw0`'s recorded divergence from its own item wording on the gitignored case (`reclaimed` rather than preserved, no `unknown-ignored-file` code), which is decision `08-65cuw0-D3`, taken because spec `7ckptx` R5.5 was amended by `laneign` (`5w8g8j`) and the literal wording would have red-ed `tests/test_lane_retention.py::test_a_lane_holding_ONLY_gitignored_files_IS_torn_down`. Report it as a recorded decision awaiting human review (F-06).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw backlog set done` output for both `qliia1` and `a58s04`, plus the `a58s04` message quoted in full showing it names BOTH refuted premises (that `aw attention` already excludes a merged lane via `lane_work_has_landed`, and that `reclaimable` governs only the interrupt path while the end-of-run teardown is `lane_containment.teardown_lane_if_classified`). A closure message that reads as "the fix sketch was implemented" FAILS this item even though the command succeeded.
    ALSO REQUIRED, because `a58s04` is a release-gated bug: the `--evidence` citation used, the ROUTE the close-legitimacy predicate reported, and confirmation the gate was NOT cleared. Expect HANDOFF rather than SATISFIED, since `65cuw0` carries `From-Backlog: a58s04` with the same gate and HANDOFF is checked first; an evidence block asserting SATISFIED FAILS as a misreading. A close reached by passing `--blocks-release -` FAILS even at exit 0, and note that exit 0 here is NOT evidence of legitimacy: the predicate returns legitimate with no evidence at all (F-08), so this item is satisfied by the MESSAGE, not by the command succeeding.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Commit ONLY files this plan changed, path-scoped; never `git add -A`; never push.
When reporting tests passed, paste the ACTUAL runner output. Do NOT mark an `E-*` item performed for work
not done, and do NOT fill a `V-*` `Observed evidence` block with anything but observed output.

THE HONESTY RULE THAT MATTERS MOST HERE, because this plan's whole product is a verification: this plan can
only be satisfied by MEASUREMENTS, so there is nothing to show except real output. If a measurement cannot
be taken in the tree this plan is executing in, the correct result is a named refusal, not a substitute
measurement and not a clean copied from a different tree.

AND THE RULE CUTS BOTH WAYS, which is the correction this review made and the reason F-02 is now a BLOCKER
rather than a restatement of the parent. A REFUSAL YOU DID NOT NEED IS ALSO A DISHONEST REPORT. This plan
was authored believing an in-lane `aw attention --check` reports a FALSE CLEAN and instructing its executor
to refuse it; measured from inside a lane at HEAD `a1dbb05a`, `stranded_lane_drift` returns THIRTEEN records
and `--check` exits 1, because `_resolve_runs_repo_root` walks up out of `.aw/worktrees` to the owning
checkout. So the old instruction would have declined a working measurement and presented that refusal as
diligence, which is a false NEGATIVE - the mirror image of the false clean it guarded against, and equally a
way for the Set to avoid being measured. Refuse ONLY what you actually cannot measure (arms (b) and (c) from
a lane), name the tree either way, and never inherit a premise about tooling without re-running it: the
parent's claim was already false when it was written, ten days after `699c1fc7` landed.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Specifically: change NO product code, delete NO
branch, and do NOT edit `tb63qv` beyond the child-table row that already exists by the time this runs. If
the work genuinely requires a path outside the fence, make the edit and justify it, since `aw ipd finalize`
refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-
unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.

RUN ORDER, so nobody hand-runs this plan too early. Measured at review HEAD `a1dbb05a`: of this plan's two
declared edges, `executed:65cuw0` is SATISFIED (that plan is `executed` with 0 empty evidence blocks and 5
`Result: pass`) and `executed:ut0vzr` is NOT (`ut0vzr` is `approved` in `pending/` with 8 empty blocks and 8
`Result: pending`), so `runner_shared.evaluate_set_retirement` reports two unfinished children. The runner
handles this by construction - dependency depth is its first sort key and edges are re-checked at dispatch,
so an early dispatch marks this item `dependency-blocked` and continues rather than failing the run - and
there is nothing for a plan author to fix. A HAND-RUN executor, who has no such protection, must confirm
`ut0vzr` reads `Status: executed` before starting E-02; otherwise E-02's honest output is a named upstream
failure and no backlog item may be closed (E-03 depends on E-02). Note also that no research artifact for the
13 branch dispositions exists yet, which is consistent with `ut0vzr` being unexecuted rather than a defect.
