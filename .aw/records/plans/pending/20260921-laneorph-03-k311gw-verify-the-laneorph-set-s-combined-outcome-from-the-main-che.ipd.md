# IPD: Verify the laneorph Set's combined outcome from the main checkout

- Date: 2026-09-21
- Kind: child
- Concern: The `laneorph` Set's acceptance check has no owner that can be trusted to perform it. It sits on the Order-0 orchestrator `tb63qv` as that plan's only `E-*` item, and the runner RETIRES an orchestrator once every child is `executed` while deliberately SKIPPING the pre-transition E/V checkpoint, on the premise that a parent's own items are performed by nobody. That premise is false here, so the Set's combined verification would be reported complete having never been performed or verified. MEASURED 2026-09-22 in run `run-20260922T003414Z-1020752`: the orchestrator coverage probe refused the whole 34-set launch naming `tb63qv` among five parents carrying work no child covers (`events.jsonl`, event `orchestrator-probe-gate`, `blocking: ["5e4sb6","wfjsp4","a5wdne","tb63qv","s0gnha"]`). This plan is the child that OWNS that verification, so the parent's checklist becomes a real obligation performed by a real agent turn.
- Scope: Perform the Set-level acceptance check `tb63qv` E-01 describes, from the MAIN CHECKOUT, and record its evidence. IN: the three combined-outcome measurements (`aw attention --check` stranded-lane state, `git worktree list`, and a driver run leaving no worktree behind), each naming the tree it was measured in; plus the two backlog closures the Set's completion criteria require, which no other child owns. OUT: any change to lane reclaim, teardown, or attention CODE (that is Order 01 `65cuw0`), any branch disposition or deletion (that is Order 02 `ut0vzr`), and any re-performance of either child's own validation - this plan READS their recorded evidence and measures the COMBINED result, it does not redo their work.
- Scope-Paths: .aw/records/plans/pending, .aw/records/backlog/open, .aw/records/backlog/done
- Item-Dependencies: executed:65cuw0, executed:ut0vzr
- Status: to-review
- Set: laneorph
- Order: 3
- Highest E allocated: 03
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: k311gw

## Workflow history

- 2026-09-21 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.
- 2026-09-21 to-review (opencode/its_direct-pt3-claude-opus-5-1m-us): Authored at the maintainer's direction after the orchestrator coverage gate refused run `run-20260922T003414Z-1020752`, naming `tb63qv` as carrying work no child covers. Content is LIFTED from the parent's own E-01 and completion criteria rather than invented, so the obligation is unchanged and only its OWNER moves; the parent's checklist stays in place, per the repository rule that deleting it breaks a hand-run `execute <setid>`.

## Goal

Give the `laneorph` Set's acceptance check an owner that actually runs. The parent states the check
correctly; what it cannot do is perform it, because a retiring orchestrator spends no agent turn. After
this plan executes, "the leak is closed and the backlog is drained" is a claim backed by pasted evidence
measured in a named tree, rather than an unticked box on a plan the runner marked complete.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance, measured where it is true

- [ ] E-01 MEASURE THE COMBINED OUTCOME FROM THE MAIN CHECKOUT, and name that tree in every figure. Three measurements, all three required: (a) `aw attention --check` reports no stranded lane, OR exactly the maintainer-deferred ESCALATE set that Order 02 recorded; (b) `git worktree list` shows only the main checkout plus any lane a LIVE run owns; (c) a subsequent driver run leaves no worktree behind for the item it integrated. THE MEASURING TREE IS LOAD-BEARING AND IS THE WHOLE REASON THIS CANNOT BE DONE FROM A LANE: `.aw/records/runs/` is gitignored and therefore ABSENT inside a lane worktree, so `stranded_lane_drift` returns `[]` for lack of run records and reports a FALSE clean. The parent's E-01 records this measurement (a lane sees 13 lane worktrees where the main checkout sees a different set). So if this plan is executed in an isolated lane, it MUST state that and refuse (a), rather than pasting a clean it cannot substantiate.
  - Depends on: none
  - Expected outcome: three pasted measurements, each prefixed with the tree it was taken in (`git rev-parse --show-toplevel`), and an explicit statement of which `attention` arm was satisfied (genuinely empty versus exactly the deferred ESCALATE set, enumerated).
  - Execution state: pending

- [ ] E-02 READ BOTH CHILDREN'S RECORDED EVIDENCE AND CONFIRM THE SET'S OWN COMPLETION CRITERIA, without re-performing either child's work. This is a RECEIPT CHECK: open `65cuw0` and `ut0vzr`, confirm each is `executed` with its `V-*` items carrying observed evidence rather than empty blocks, and confirm the two criteria that span them both - that every one of the 13 unmerged branches has a recorded disposition with cited evidence immortalized under `.aw/records/research/` BEFORE any deletion, and that a merged-and-clean lane reports `reclaimable=True` while a merged lane with an UNTRACKED file does not (the `wfamig` hazard). If either child's evidence is absent or contradicts its checkmark, REPORT THAT and do not compensate by re-deriving the result: a receipt check that silently becomes a re-verification hides an upstream validation failure.
  - Depends on: E-01
  - Expected outcome: a per-child statement naming the `V-*` items read and quoting the evidence line that satisfies each spanning criterion, or a named upstream failure.
  - Execution state: pending

- [ ] E-03 CLOSE BACKLOG `a58s04` AND `qliia1` HONESTLY, which is the one substantive record change no child owns. `qliia1` is Order 02's to close by its own scope; confirm it and close it if it is still open. `a58s04` REQUIRES A CORRECTION RATHER THAN A CLAIM OF IMPLEMENTATION: its "Expected" and "Fix sketch" sections (steps 3 and 4) carry the SAME TWO REFUTED PREMISES as this Set's original Concern - that `aw attention` does not already exclude a merged lane, and that `reclaimable` governs the end-of-run leak - and the 2026-09-18 review measured both false (`aw attention` asks the merged question through `runner_shared.lane_work_has_landed` and omits `LANDED` from `LANE_ATTENTION_STATES`; `reclaimable`'s only readers sit inside `reclaim_lanes_on_interrupt`, while the successful-run teardown is the already-wired `lane_containment.teardown_lane_if_classified`). So close it with `aw backlog set done` and a message that RECORDS THE CORRECTION; do NOT write a closure implying the sketch was carried out.
  - Depends on: E-02
  - Expected outcome: both items `done` via `aw backlog set`, with `a58s04`'s closure message naming both refuted premises and the evidence that refuted them; pasted command output for each.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- AN ORCHESTRATOR HOLDS ORCHESTRATION, NOT WORK OF ITS OWN, and the remedy for a parent carrying uncovered work is to ADD A CHILD rather than to delete the parent's items. `AGENTS.md` states this directly and gives the reason: the parent's checklist is what makes a hand-run `execute <setid>` complete when no runner is involved, so deleting it causes the lost work it exists to prevent. This plan therefore ADDS coverage and changes nothing on `tb63qv` except its child table.
- THE ORCHESTRATOR COVERAGE GATE IS THE MECHANISM THAT FOUND THIS, and its verdict is cached on the parent's item text plus its child table, so adding this row re-probes automatically. Specified in `25kzda` 2.5b and `77tr3o` R-12.
- ONE DEFINITION OF "MERGED" EXISTS AND THIS PLAN MUST NOT ADD A SECOND: `runner_shared.lane_work_has_landed`, which is deliberately THREE-VALUED (`True`/`False`/`None` for unanswerable). A verification that collapses `None` into either boolean is asserting something the codebase refuses to assert.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Severity | Evidence | Finding |
|---|---|---|---|
| F-01 | HIGH | `run-20260922T003414Z-1020752/events.jsonl`, event `orchestrator-probe-gate` | The coverage probe refused a 34-set launch naming `tb63qv` among five uncovered parents. Without this child the Set's only acceptance check is performed by nobody and reported complete. |
| F-02 | HIGH | `tb63qv` E-01, quoted | The parent's own item states the verification MUST be measured from the main checkout, because `.aw/records/runs/` is gitignored and absent in a lane, making an in-lane `stranded_lane_drift` return `[]` and report a false clean. Any executor of this plan in an isolated lane must refuse that measurement rather than paste it. |
| F-03 | MEDIUM | `tb63qv` completion criteria, quoted | Closing `a58s04` requires recording a CORRECTION: two of its fix-sketch steps rest on premises the 2026-09-18 review measured false. A closure claiming implementation would write a false history. |
| F-04 | MEDIUM | `tb63qv` OQ-03, quoted | The Set's `attention --check` criterion is not achievable as literally written: deleting a DELETE branch converts its `attention.lane-stranded` row into an equally-failing `attention.lane-unknown` row. E-01 therefore accepts the maintainer-deferred ESCALATE set as the satisfying arm, and requires it to be ENUMERATED rather than waved at. |

## Proposed changes (ordered, validatable)

1. Measure the three combined-outcome facts from the main checkout, naming the tree (E-01).
2. Read both children's recorded evidence and confirm the two spanning criteria (E-02).
3. Close `qliia1` and `a58s04`, the latter with its correction recorded (E-03).

## Deferred / out of scope (with reason)

- ANY CODE CHANGE. Lane reclaim, teardown, and attention behavior belong to Order 01 `65cuw0`; branch
  disposition belongs to Order 02 `ut0vzr`. This plan measures their combined effect and touches no
  product code, which is why its `Scope-Paths` name only records.
- RE-PERFORMING EITHER CHILD'S VALIDATION. E-02 is a receipt check by design (see its own wording): a
  receipt check that quietly becomes a re-verification conceals an upstream validation failure instead of
  reporting it.
- THE PARENT'S CHECKLIST. `tb63qv` E-01 stays exactly as written; only its child table gains a row. See
  the conventions section for why deleting it would be the defect rather than the fix.

## Scope check

- Over-scope: none.
- Under-scope: none. The parent carries exactly one `E-*` item plus the Set completion criteria, and E-01
  through E-03 cover the verification, the receipt check, and the record closures respectively.

## Required tests / validation

No product code changes, so there is no new unit test. The validation IS the pasted measurement, plus a
bare `python3 -m pytest` to demonstrate the tree is green at the moment the Set is declared complete (a
completion claim made against a red tree is not a completion claim).

## Spec / documentation sync

N/A. This plan changes no contract: it performs a verification the parent already specified and closes two
backlog items the Set already required. The only structural edit is the child-table row on `tb63qv`, which
is what the coverage gate reads.

## Open questions

### OQ-01: If this plan is dispatched into an isolated lane, should it refuse E-01(a) or request a non-isolated run?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: REFUSE THE MEASUREMENT AND SAY SO, resolved from the parent's own evidence rather than deferred. `tb63qv` E-01 records that `.aw/records/runs/` is gitignored and therefore absent inside a lane, so `stranded_lane_drift` returns `[]` and an in-lane check reports a FALSE clean. A false clean is worse than a refusal, because it closes the Set on a measurement that could not have detected the failure. So an executor in a lane MUST state the tree, refuse E-01(a), and report that the item needs a main-checkout measurement; the runner's `--no-isolate-worktree` is the operator's remedy and is not this plan's to choose. E-01's expected outcome already requires the tree to be named, which is what makes the refusal detectable rather than silent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste `git rev-parse --show-toplevel` FIRST, then the output of `aw attention --check` (with its exit code), `git worktree list`, and the post-integration worktree check. State which `attention` arm was satisfied and, if it was the ESCALATE arm, enumerate those lanes. An execution that pastes a clean `attention` result without naming the tree FAILS this item, because that is precisely the false-clean shape F-02 records.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: for each of `65cuw0` and `ut0vzr`, name the `V-*` items read and quote one evidence line per spanning criterion (the 13 dispositions immortalized under `.aw/records/research/` before any deletion; `reclaimable=True` for merged-and-clean and NOT for merged-with-untracked). If an upstream evidence block was empty or contradicted its checkmark, the required evidence is the STATEMENT of that failure, which satisfies this item while failing the Set.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `aw backlog set done` output for both `qliia1` and `a58s04`, plus the `a58s04` message quoted in full showing it names BOTH refuted premises (that `aw attention` already excludes a merged lane via `lane_work_has_landed`, and that `reclaimable` governs only the interrupt path while the end-of-run teardown is `lane_containment.teardown_lane_if_classified`). A closure message that reads as "the fix sketch was implemented" FAILS this item even though the command succeeded.
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
measurement and not a clean copied from a different tree. F-02 exists because the false-clean shape has
already been measured once in this Set.

SCOPE FENCE. Touch ONLY the paths in `- Scope-Paths:`. Specifically: change NO product code, delete NO
branch, and do NOT edit `tb63qv` beyond the child-table row that already exists by the time this runs. If
the work genuinely requires a path outside the fence, make the edit and justify it, since `aw ipd finalize`
refuses to complete until every out-of-scope path carries a `--scope-reason` and every declared-but-
unmodified path carries a `--scope-ack`.

POST-GATE LIFECYCLE. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` item
must carry observed evidence before the plan moves to `.aw/records/plans/executed/`. The runner owns the
terminal transition; a worker-role process is refused by `AW-LIFECYCLE-ROLE-001`.
