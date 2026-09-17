# IPD: Drain and prevent orphaned lane worktrees

- Date: 2026-09-17
- Kind: orchestrator
- Concern: `.aw/worktrees/` grows without bound and the stranded-lane alarm is drowned in false positives. Two distinct defects produce one symptom. (1) PREVENTION: a lane whose work is fully merged is never reclaimable, because `commits_ahead` is measured against the lane's own base rather than the integration target, so every successful run leaks its worktree (measured 2026-09-17: 38 worktrees / 4.7G, of which 28 were merged AND clean; a manual sweep recovered 3.6G). (2) DRAIN: 13 lane branches hold 76 commits unreachable from `main`, undecided, of which 74 commits belong to plans `main` already records as `superseded`. Fixing only (1) leaves the existing backlog; fixing only (2) means the next run refills it.
- Scope: Coordinate the two children. Order 01 fixes the reclaim predicate and tears a lane down when its work lands. Order 02 drains the 13 existing branches by evidence-cited disposition. This orchestrator holds NO work of its own beyond sequencing and the Set-level acceptance check.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: to-review
- Set: laneorph
- Order: 0
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: tb63qv

## Workflow history
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Reach a state where `.aw/worktrees/` holds only lanes a live run owns, and `aw attention --check` reports
no stranded lane, so the stranded-lane report becomes a real alarm instead of background noise.

ORDER MATTERS AND IS DECLARED AS A DEPENDENCY. Order 02 depends on Order 01 (`executed:65cuw0`) because
draining before the leak is fixed refills the queue on the very next run, and because Order 02's
acceptance check (an empty stranded report) is only meaningful once Order 01 has stopped merged lanes
from appearing in it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance

- [ ] E-01 After both children are `executed`, verify the Set's combined outcome and record it: `aw attention --check` reports no stranded lane, `git worktree list` shows only the main checkout plus any lane a live run owns, and a subsequent driver run leaves no worktree behind. This is the only item on this orchestrator, and it is a VERIFICATION of the children's combined effect rather than work of its own.
  - Depends on: none
  - Expected outcome: pasted evidence that the leak is closed AND the backlog is drained; a regression in either half means the Set is not done regardless of the children's individual states.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `.aw/records/plans/pending/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md` | PREVENT: add a merged-ness reading to `LaneState`, make `reclaimable` honor it, tear the lane down at the end of a successful integration, and stop `aw attention` calling a merged lane stranded | none |
| 02 | `.aw/records/plans/pending/20260917-laneorph-02-ut0vzr-triage-the-fourteen-lane-branches-holding-unmerged-commits.ipd.md` | DRAIN: disposition each of the 13 unmerged lane branches as DELETE / RECOVER / ESCALATE on cited evidence, record the reasoning to `.aw/records/research/`, execute the decisions, close `qliia1` | `executed:65cuw0` |

## Completion criteria (the whole Set is done only when)

- A merged, clean lane reports `reclaimable=True`, and a merged lane with an UNTRACKED file does NOT
  (the `wfamig` hazard stays closed).
- A driver run that integrates a lane leaves NO worktree for it, and its branch still exists.
- `aw attention --check` reports no stranded lane, or exactly the maintainer-deferred ESCALATE set.
- Every one of the 13 unmerged branches has a recorded disposition with cited evidence, immortalized in
  `.aw/records/research/` BEFORE any deletion.
- Backlog `a58s04` and `qliia1` are both closed `done` with evidence.
- `python3 -m pytest` bare and green, pasted.

## Cross-IPD validation

- ORDER 02 MUST NOT RUN BEFORE ORDER 01 IS `executed`. Declared as `executed:65cuw0` on Order 02 rather
  than left to Set/Order, since Set/Order is only a tiebreaker and would not enforce it.
- The two children must agree on ONE definition of "merged": Order 02's disposition rule consumes Order
  01's `merged_into_target` reading rather than re-deriving merged-ness with its own git commands. A
  second definition is how the two halves would drift.
- Neither child may delete a lane BRANCH for a merged lane. Order 01 removes worktrees only; Order 02
  deletes refs only for branches it has dispositioned DELETE with a citation.
- Order 01's `aw attention` change must not suppress a genuinely stranded lane, or Order 02's acceptance
  check becomes vacuous: an empty report would then prove nothing. Order 01's V-04 pins both directions.

## Deferred / out of scope (with reason)

- A general operator-facing `aw lane` verb (list / reclaim / recover) is a plausible follow-on. Deferred:
  not needed to stop the leak or drain the backlog, and adding a public surface inside a defect fix widens
  the blast radius.
- Backlog `5bmq5f` (a backlog item duplicated across status directories, which is what the `lqly9m` and
  `pr5b0t` worktrees hold staged deletions for) is a separate defect with its own item.
- `perf/att-set-speed` is the maintainer's own branch and is not an `aw/lane/*` lane; untouched.
- Relocating machine-state out of the repo (the old `wtiso` Phase 4 ambition) is NOT revived here; those
  plans are retired and this Set only disposes of their leftover branches.

## Scope check

- Over-scope: none. This orchestrator holds one verification item and the child table; all work is in the
  children.
- Under-scope: none known. The two children cover prevention and drain, which are the two halves of the
  symptom.

## Required tests / validation

The children own their own validation. This orchestrator's own check is E-01: the Set-level end state,
evidenced by pasted `aw attention --check`, pasted `git worktree list`, and a real driver run shown to
leave no worktree behind. Note this Set is NOT verifiable by unit tests alone: the defect it fixes passed
every unit test for weeks while leaking 4.7G.

## Open questions

### OQ-01: Should the drain (Order 02) run at all, given most branches will be deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES. The value is not the disk it frees (7 of the 13 have no worktree
  and cost nothing) but the ALARM it restores: while merged and retired lanes sit in the stranded report,
  a genuinely stranded lane is indistinguishable from noise, which is how `2c122z` sat at 26 unmerged
  commits for three weeks unnoticed. An alarm that is always on is not an alarm.

### OQ-02: Is `nna8yz`'s feature really already in `main`, or did the 2026-09-17 check mislead?

- Blocking: no
- Status: open
- Owner: Order 02 E-04
- Resolution or deferral rationale: The 2026-09-17 reading found `materialize_lane_inputs` / `lane-inputs`
  present in `lane_containment.py`, `oc_runipd.py` and `agy_runipd.py`, which is why `nna8yz` is EXPECTED
  to disposition DELETE. But that was a symbol-presence check, not a behavioral equivalence proof, so
  Order 02's E-04 must confirm or correct it with evidence rather than inherit it as settled. Recorded as
  open so the expectation cannot be mistaken for a finding.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw attention --check` showing no stranded lane (or only the deferred
    ESCALATE set); pasted `git worktree list`; and evidence from a real driver run that integrated a lane
    and left no worktree while keeping its branch. Plus both children shown `executed` and `a58s04` /
    `qliia1` shown `done`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This Set requires explicit human approval before execution. Order 02 deletes git branches and therefore
carries the higher bar stated in its own gate: no deletion before its research record is committed, and
every deleted sha recorded.

Execution contract for both children: work in an isolated worktree, commit only declared `Scope-Paths`,
path-scoped, never `git add -A`, never push. Paste ACTUAL command output for every V-item.

Post-gate lifecycle: this orchestrator is retired to `.aw/records/plans/executed/` by the runner once both
children are `executed` on disk, spending no agent turn. If it is executed by hand instead, E-01 above must
be genuinely performed rather than assumed from the children's states, since a Set can have two executed
children and still leave a non-empty stranded report.
