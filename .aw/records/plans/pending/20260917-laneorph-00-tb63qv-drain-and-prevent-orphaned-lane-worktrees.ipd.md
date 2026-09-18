# IPD: Drain and prevent orphaned lane worktrees

- Date: 2026-09-17
- Kind: orchestrator
- Concern: `.aw/worktrees/` grows without bound. Two distinct pieces of work share that one symptom. (1) PREVENTION: successful lanes leak their worktrees (measured 2026-09-17: 38 worktrees / 4.7G, of which 28 were merged AND clean; a manual sweep recovered 3.6G). CORRECTED AT REVIEW 2026-09-18: the CAUSE named in the original Concern (`commits_ahead` measured against the lane's own base, so `reclaimable` is False forever) is REAL as a reading but is NOT the cause of the leak, because the end-of-run teardown path does not consult `reclaimable` at all. Order 01 is retargeted accordingly and now DEPENDS on `5w8g8j`; see its Concern for the measured evidence. (2) DRAIN: 13 lane branches hold commits unreachable from `main`, undecided, most of them belonging to plans `main` already records as `superseded`. Fixing only (1) leaves the existing backlog; fixing only (2) means the next run refills it.
- Scope: Coordinate the two children. Order 01 fixes the reclaim predicate and tears a lane down when its work lands. Order 02 drains the 13 existing branches by evidence-cited disposition. This orchestrator holds NO work of its own beyond sequencing and the Set-level acceptance check.
- Scope-Paths: .aw/records/plans/pending
- Item-Dependencies: none
- Status: reviewed
- Readiness: no-go
- Set: laneorph
- Order: 0
- Highest E allocated: 01
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: tb63qv

## Workflow history
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001..PR-009; readiness `no-go` on TWO blocking findings, plus a third BLOCKER fixed in place. Reviewed at HEAD `f741596e`; `aw ipd lint --phase author` conforming for all three plans before revision. BOTH MOTIVATING PREMISES ARE REFUTED, measured not reasoned. (1) `aw attention` ALREADY excludes a merged lane: `classify_lane_integration` asks the merged-ness question through `lane_work_has_landed` (`runner_shared.py:1077-1106`, the same `merge-base --is-ancestor` call Order 01's E-01 proposed to ADD), classifies it `LANDED`, and `LANE_ATTENTION_STATES` omits that state (`:1063-1068`); its section header at `:1015-1033` records the SAME measurement this Set presents as new. Measured: `aw attention --check` gave 19 rows over 12 DISTINCT lanes, `merge-base --is-ancestor <branch> main` said NOT-ancestor for ALL 12 (zero false positives), and the six lanes this Set names as merged appear ZERO times. (2) `reclaimable` HAS NOTHING TO DO WITH THE END-OF-RUN LEAK: its only two readers (`oc_runipd.py:2337`, `agy_runipd.py:1292`) are both inside `reclaim_lanes_on_interrupt`, while the successful-run teardown is a different, ALREADY-WIRED call, `lane_containment.teardown_lane_if_classified` (`oc_runipd.py:7881`, `agy_runipd.py:4430`, AST-confirmed inside `fin_rc == 0`), gated on the spec R5.5 INVENTORY. The real cause is an unaccounted gitignored file, i.e. plan `5w8g8j`, so `executed:5w8g8j` is now declared on Order 01 and the Set cannot deliver the 4.7G it leads with. WORST FINDING, PR-003, FIXED: the authored E-02 (`reclaimable` = merged AND not `dirty`) would have CAUSED DATA LOSS, because `dirty` comes from a plain `git status --porcelain` blind to IGNORED files (`worktree_lease.py:316-319` vs `lane_containment.py:2814-2819`), the predicate gates a `force=True` teardown that DELETES THE LANE BRANCH, and the plan's stated backstop does not fire: measured on git 2.43.0 with one ignored file, plain porcelain was empty and `git worktree remove` WITHOUT `--force` exited **0** and DELETED it (the same probe with an untracked file exited 128 and preserved it). E-02 now consumes `inventory_lane(...).classified` and E-03 routes the interrupt teardown through the shared R5.5 gate, removing a PRE-EXISTING force-delete hazard too. ALSO: the Set's acceptance criterion is UNREACHABLE, since deleting a branch converts its `attention.lane-stranded` row into an equally-failing `attention.lane-unknown` row (`runner_shared.py:1093-1096`, `:1170-1176`, `:1068`; `attention.py:1103-1111`); the "76 commits" total is neither the per-branch sum (94) nor the distinct union (43), the `wtiso` group being 26 distinct commits identical to `2c122z` alone; and every acceptance check needed a named non-lane measuring tree, because `.aw/records/runs/` is gitignored and `stranded_lane_drift` returns `[]` without run records, so an in-lane check reports a FALSE clean. Suite bare: `31 failed, 7866 passed, 3 skipped, 2 xfailed`, all 31 the documented worker-lane baseline (`770fkp`); no code changed. OQ-02 and OQ-03 raised `Blocking: yes` carrying PR-001 and PR-002.

- 2026-09-18 reviewed (aw set): plan-review complete: REVIEWED - OPEN QUESTIONS; 9 findings, 6 FIXED, PR-001 (both motivating premises refuted: aw attention already excludes a merged lane, and reclaimable governs only the interrupt path while the end-of-run teardown already exists) and PR-002 (deleting a branch converts its stranded row into an equally-failing lane-unknown row, so the Set's acceptance criterion is unreachable) left OPEN at BLOCKER and escalated as blocking OQ-02/OQ-03; PR-003 (the authored E-02 would have force-deleted lane branches holding ignored files) FIXED; readiness no-go
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Reach a state where `.aw/worktrees/` holds only lanes a live run owns, and `aw attention --check` reports
no stranded lane, so the stranded-lane report becomes a real alarm instead of background noise.

ORDER MATTERS AND IS DECLARED AS A DEPENDENCY. Order 02 depends on Order 01 (`executed:65cuw0`) because
draining before the leak is fixed refills the queue on the very next run.

TWO PREMISES OF THE ORIGINAL SET WERE REFUTED AT REVIEW (2026-09-18), and both are corrected here rather
than left for an executor to discover. They are recorded at Set level because each spans both children.

FIRST, `aw attention` DOES NOT REPORT A MERGED LANE AS STRANDED, so the "alarm drowned in false
positives" premise is false and the second half of Order 01's original scope was already-shipped work.
The predicate `classify_lane_integration` (`runner_shared.py:1110-1180`) already asks the merged-ness
question through `lane_work_has_landed` (`:1077-1106`, `git merge-base --is-ancestor <branch> <target>`)
and classifies a merged lane `LANDED`, which is deliberately silent. Its own section header
(`:1015-1033`) records the SAME measurement this Set's Concern presents as new. Measured at review HEAD
`f741596e`: `aw attention --check` emitted 19 rows over 12 DISTINCT lanes, `git merge-base --is-ancestor
<branch> main` returned NOT-ancestor for all 12, so there were ZERO false positives; and the six lanes
this Set names as merged (`3dki3o`, `51vw4y`, `orziju`, `s16omw`, `ty3cj6`, `yrqyxb`) appear in the
report ZERO times. So the report is already trustworthy, Order 02's acceptance check does not depend on
Order 01 for its meaning, and the dependency stands only on the refill argument above.

SECOND, THE LEAK IS ALREADY DIAGNOSED ELSEWHERE AND ITS CAUSE IS NOT `reclaimable`. Both drivers already
tear a lane down at the end of a successful integration, through `lane_containment.teardown_lane_if_classified`
(`oc_runipd.py:7881`, `agy_runipd.py:4430`, both inside the `fin_rc == 0` success branch), and that gate
consults the spec R5.5 INVENTORY, never `reclaimable`. `reclaimable` is read at exactly two call sites
(`oc_runipd.py:2337`, `agy_runipd.py:1292`), both inside `reclaim_lanes_on_interrupt`, i.e. the INTERRUPT
path only. What refuses teardown on a successful run is an unaccounted gitignored file, which is plan
`5w8g8j`'s subject (`laneign` Set, `Status: reviewed`, `Readiness: no-go` on two blocking questions).
Consequently Order 01 now depends on `5w8g8j` and is retargeted; without that fix its own V-03 cannot
pass, because the lane it expects to be torn down will be preserved by the inventory gate for a reason
Order 01 does not touch.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Set-level acceptance

- [ ] E-01 After both children are `executed`, verify the Set's combined outcome and record it, MEASURED FROM THE MAIN CHECKOUT and naming that tree: `aw attention --check` reports no stranded lane (or exactly the maintainer-deferred ESCALATE set, and see OQ-03 on why a deleted branch does NOT silence a row), `git worktree list` shows only the main checkout plus any lane a live run owns, and a subsequent driver run leaves no worktree behind. This is the only item on this orchestrator, and it is a VERIFICATION of the children's combined effect rather than work of its own. THE MEASURING TREE IS LOAD-BEARING: measured at review, a lane sees 13 lane worktrees where the main checkout sees a different set, and `.aw/records/runs/` is gitignored and ABSENT inside a lane, so `stranded_lane_drift` returns `[]` from a lane for lack of run records and would report a FALSE clean.
  - Depends on: none
  - Expected outcome: pasted evidence that the leak is closed AND the backlog is drained, each figure naming the tree it was measured in; a regression in either half means the Set is not done regardless of the children's individual states. An empty stranded report measured from inside a lane does NOT satisfy this item.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | `.aw/records/plans/pending/20260917-laneorph-01-65cuw0-fix-lane-reclaim-so-a-merged-lane-is-reclaimable-and-torn-do.ipd.md` | PREVENT: make the INTERRUPT-path `reclaimable` reading honor merged-ness, so an interrupted run's already-merged lane is reclaimed instead of left alone. RETARGETED at review: the `aw attention` half is already shipped and was removed, and the end-of-run teardown half belongs to `5w8g8j`. | `executed:5w8g8j` |
| 02 | `.aw/records/plans/pending/20260917-laneorph-02-ut0vzr-triage-the-fourteen-lane-branches-holding-unmerged-commits.ipd.md` | DRAIN: disposition each of the 13 unmerged lane branches as DELETE / RECOVER / ESCALATE on cited evidence, record the reasoning to `.aw/records/research/`, execute the decisions, close `qliia1` | `executed:65cuw0` |

## Completion criteria (the whole Set is done only when)

- A merged, clean lane reports `reclaimable=True`, and a merged lane with an UNTRACKED file does NOT
  (the `wfamig` hazard stays closed).
- A driver run that integrates a lane leaves NO worktree for it, and its branch still exists. NOTE this
  criterion is satisfied by `5w8g8j`, not by this Set: the end-of-run teardown gate is already wired and
  already refuses only on the inventory. Order 01's V-03 is scoped to the INTERRUPT path accordingly.
- `aw attention --check` reports no stranded lane, or exactly the maintainer-deferred ESCALATE set. THE
  BRANCH-DELETION INTERACTION MUST BE SETTLED FIRST (OQ-03): deleting a DELETE branch does not silence
  its row, it converts it to `attention.lane-unknown`, which carries the same `error` severity and fails
  `--check` identically. See OQ-03; this criterion is not achievable as written until that is resolved.
- Every one of the 13 unmerged branches has a recorded disposition with cited evidence, immortalized in
  `.aw/records/research/` BEFORE any deletion.
- Backlog `a58s04` and `qliia1` are both closed `done` with evidence. `a58s04`'s "Expected"/"Fix sketch"
  sections carry the same two refuted premises as this Set's original Concern (steps 3 and 4 of its
  sketch), so closing it MUST record the correction rather than claim its sketch was implemented.
- `python3 -m pytest` bare and green, pasted.

## Cross-IPD validation

- ORDER 02 MUST NOT RUN BEFORE ORDER 01 IS `executed`. Declared as `executed:65cuw0` on Order 02 rather
  than left to Set/Order, since Set/Order is only a tiebreaker and would not enforce it. The dependency
  now rests ONLY on the refill argument, since (per the Goal) the stranded report is already trustworthy.
- THE ONE DEFINITION OF "MERGED" ALREADY EXISTS AND NEITHER CHILD MAY ADD A SECOND. It is
  `runner_shared.lane_work_has_landed` (`:1077-1106`). Order 01 must REUSE it rather than introduce a
  parallel `merged_into_target` git call, and Order 02 must consume it rather than re-deriving merged-ness
  with its own commands. Note `lane_work_has_landed` is deliberately THREE-VALUED (`True`/`False`/`None`
  for unanswerable) while a `LaneState` boolean cannot express `None`, so Order 01 must not collapse the
  unanswerable case into `False`, and must never collapse it into `True`, which would authorize teardown
  on an unproven lane.
- Neither child may delete a lane BRANCH for a merged lane. Order 01 removes worktrees only; Order 02
  deletes refs only for branches it has dispositioned DELETE with a citation.
- NO CHILD MAY REACH `worktree_lease.teardown_worktree` DIRECTLY. It deletes the lane BRANCH and, with
  `force=True`, destroys uncommitted files unrecoverably (its own docstring records the measurement).
  Spec `7ckptx` R5.5 requires teardown to go through `lane_containment.teardown_lane_if_classified`. A
  child that adds a second teardown path violates R5.5 and R6.1 regardless of how safe its own guard is.

## Deferred / out of scope (with reason)

- A general operator-facing `aw lane` verb (list / reclaim / recover) is a plausible follow-on. Deferred:
  not needed to stop the leak or drain the backlog, and adding a public surface inside a defect fix widens
  the blast radius.
- Backlog `5bmq5f` (a backlog item duplicated across status directories, which is what the `lqly9m` and
  `pr5b0t` worktrees hold staged deletions for) is a separate defect with its own item.
- `perf/att-set-speed` is the maintainer's own branch and is not an `aw/lane/*` lane; untouched.
- Relocating machine-state out of the repo (the old `wtiso` Phase 4 ambition) is NOT revived here; those
  plans are retired and this Set only disposes of their leftover branches.
- MAKING THE END-OF-RUN TEARDOWN ACTUALLY FIRE is `5w8g8j`'s (`laneign` Set), not this Set's. Added at
  review once the teardown path was traced: the gate is already wired at `oc_runipd.py:7881` and
  `agy_runipd.py:4430` and refuses only on the R5.5 inventory, so the disk recovery this Set's Concern
  claims arrives with `5w8g8j` and not with Order 01. Declared as `executed:5w8g8j` on Order 01 rather
  than left as prose.
- AMENDING SPEC `7ckptx` R5.5 is out of scope for this Set and no `.spec.md` is declared in either child's
  `Scope-Paths`. That is deliberate: R5.5's teardown refusal is exactly the contract `5w8g8j` is blocked
  on, and a second plan narrowing it from a different Set is how one approved MUST gets weakened twice.

## Scope check

- Over-scope: none on this orchestrator, which holds one verification item and the child table. But the
  Set WAS over-scoped as authored, and it is corrected in Order 01 rather than here: its original E-04
  (stop `aw attention` calling a merged lane stranded) asked for behavior that already ships, and its
  original E-03 (tear the lane down at the end of a successful integration) asked for a call site that
  already exists and is gated by a rule Order 01 does not address.
- Under-scope: the Set does not, and after the retarget cannot, deliver the disk recovery its Concern
  leads with; that belongs to `5w8g8j` and is declared as a dependency. Whether the residue is worth
  executing as its own Set is OQ-02, which is blocking and the maintainer's.
- The Set's acceptance criterion is currently UNREACHABLE as written, per OQ-03: branch deletion converts
  a stranded row into an equally-failing unknown row. That is recorded as a blocking question rather than
  papered over, because every available fix changes either a fail-closed contract or this Set's own
  definition of done.

## Required tests / validation

The children own their own validation. This orchestrator's own check is E-01: the Set-level end state,
evidenced by pasted `aw attention --check`, pasted `git worktree list`, and a real driver run shown to
leave no worktree behind. Note this Set is NOT verifiable by unit tests alone: the defect it fixes passed
every unit test for weeks while leaking 4.7G.

MEASURE FROM THE MAIN CHECKOUT AND SAY SO. Two review-measured facts make an in-lane measurement
misleading rather than merely partial. `.aw/records/runs/` is gitignored and absent inside a lane, and
`stranded_lane_drift` returns `[]` when it finds no run records (`attention.py:1141-1145`), so an in-lane
`aw attention --check` reports a FALSE clean and would let this Set claim success having verified nothing.
And `git worktree list` reports a different set from a lane than from the main checkout. Any figure whose
tree is not named does not satisfy V-01.

DO NOT RUN THE SUITE WITH ADDED FLAGS. Run it bare (`python3 -m pytest`); `pyproject.toml` `addopts`
already supplies the quiet, parallel, fast-subset flags, and a second `-q` suppresses the summary line
this Set is required to paste. A managed worker lane also fails a set of lifecycle tests BY DESIGN
(backlog `770fkp`), so the gate is NO NEW failures against a baseline taken in the same tree, not an
absolute count.

## Open questions

### OQ-01: Should the drain (Order 02) run at all, given most branches will be deleted?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES. The value is not the disk it frees (7 of the 13 have no worktree
  and cost nothing) but the ALARM it restores: while merged and retired lanes sit in the stranded report,
  a genuinely stranded lane is indistinguishable from noise, which is how `2c122z` sat at 26 unmerged
  commits for three weeks unnoticed. An alarm that is always on is not an alarm.

### OQ-04: Is `nna8yz`'s feature really already in `main`, or did the 2026-09-17 check mislead?

- Blocking: no
- Status: open
- Owner: Order 02 E-04
- Resolution or deferral rationale: The 2026-09-17 reading found `materialize_lane_inputs` / `lane-inputs`
  present in `lane_containment.py`, `oc_runipd.py` and `agy_runipd.py`, which is why `nna8yz` is EXPECTED
  to disposition DELETE. But that was a symbol-presence check, not a behavioral equivalence proof, so
  Order 02's E-04 must confirm or correct it with evidence rather than inherit it as settled. Recorded as
  open so the expectation cannot be mistaken for a finding. CONFIRMED PRESENT at review HEAD `f741596e`:
  `materialize_lane_inputs` is defined at `lane_containment.py:2140` and called at `oc_runipd.py:6893`.
  That still does not settle behavioral equivalence, so this stays open and non-blocking, as it gates one
  branch's disposition rather than the Set.

### OQ-02: Should this Set proceed at all, now that its two motivating premises are refuted and the real leak belongs to `5w8g8j`?

- Blocking: yes
- Finding: PR-001
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED BY THE REVIEWER, because it is a scope and priority call.
  What review established (evidence in the Goal): the `aw attention` half of Order 01 is ALREADY SHIPPED
  and its removal is not optional; and the end-of-run teardown that actually leaks is gated by
  `teardown_lane_if_classified` on the spec R5.5 inventory, not by `reclaimable`, so it is `5w8g8j`'s
  subject and `5w8g8j` is itself `no-go` pending two maintainer answers. What REMAINS genuinely unfixed
  and is Order 01's alone: `reclaim_lanes_on_interrupt` leaves an already-merged lane alone on the
  INTERRUPT path, because `reclaimable` requires `commits_ahead == 0`. That is a real but much smaller
  defect than the Concern claims, and it does NOT recover the 4.7G. THE QUESTION: (a) proceed with Order
  01 retargeted to the interrupt path only, accepting that the disk recovery arrives with `5w8g8j`;
  (b) hold Order 01 until `5w8g8j` is decided, since its V-03 cannot pass without it; or (c) retire Order
  01 and fold the interrupt-path reading into `5w8g8j`'s Set. The Set-level dependency `executed:5w8g8j`
  has been declared on Order 01 either way, since (a) still cannot validate before it.

### OQ-03: Deleting a DELETE branch converts its stranded row into an `attention.lane-unknown` row, which also fails `--check`. How should Order 02 reach an empty report?

- Blocking: yes
- Finding: PR-002
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED BY THE REVIEWER, because every route changes a
  deliberately fail-closed contract or the Set's own acceptance criterion. MEASURED at review HEAD:
  `lane_work_has_landed` returns `None` when `git rev-parse --verify <branch>` fails
  (`runner_shared.py:1093-1096`), `classify_lane_integration` maps `None` to `LANE_UNKNOWN` (`:1170-1176`),
  `LANE_ATTENTION_STATES` contains `LANE_UNKNOWN` (`:1068`), and `lane_drift_severity` returns `error`
  for BOTH reportable states with the docstring "UNKNOWN fails too rather than warning: a landing question
  we cannot answer is not evidence the work landed" (`attention.py:1103-1111`). So Order 02's E-07 deletes
  the branches and E-08's acceptance check STILL FAILS, on a different rule id, for every branch it
  deleted. The Set cannot satisfy its own completion criterion as written. OPTIONS: (a) accept an
  `attention.lane-unknown` set as the terminal state and rewrite E-08 and the completion criteria to
  demand exactly that, naming each expected row; (b) also remove the RUN RECORDS that name those lanes,
  which makes the rows disappear at the source but edits run history and is out of the declared
  `Scope-Paths`; (c) teach the classifier a DISPOSITIONED state, which is new public behavior inside a
  cleanup plan and needs its own design; or (d) do not delete refs at all, keeping them as the cheap
  durable record Order 01's own OQ-02 already argues for, and closing `qliia1` on the research record
  alone. The reviewer's read is that (d) or (a) is the smallest correct answer, but the choice is the
  maintainer's because (b) and (c) both touch contracts beyond this Set.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted `aw attention --check` showing no stranded lane (or only the deferred
    ESCALATE set); pasted `git worktree list`; and evidence from a real driver run that integrated a lane
    and left no worktree while keeping its branch. Plus both children shown `executed` and `a58s04` /
    `qliia1` shown `done`. EVERY figure must NAME THE TREE it was measured in, and the stranded report
    must come from the MAIN CHECKOUT: an empty report from inside a lane is a known false clean (E-01)
    and does NOT satisfy this item. State the `attention.lane-unknown` row count separately from the
    `attention.lane-stranded` count, since branch deletion converts the first into the second and both
    fail `--check` (OQ-03).
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
