# IPD: Triage the fourteen lane branches holding unmerged commits

- Date: 2026-09-17
- Kind: child
- Concern: THIRTEEN `aw/lane/*` branches hold commits not reachable from `main`, and nobody can currently say which hold recoverable work. Per-branch counts measured 2026-09-17 and RE-CONFIRMED at review HEAD `f741596e`: `2c122z` 26, `58ha43` 22, `7p9n2v` 16, `rchpms` 10, `upgtest`/`qcqhj7`/`nna8yz`/`mm5p3v` 3 each, `ybkmzp`/`fn2l1u`/`03ie04` 2 each, `r2i1b1`/`d7qoxv` 1 each. THE TOTAL IS 43 DISTINCT COMMITS, NOT 76: the per-branch counts SUM to 94, but the `wtiso` branches form one shared ancestry chain (`merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` returns 0), so summing double-counts. `git rev-list --count <all 13> --not main` = **43**; the whole `wtiso` group unions to **26**, the same as `2c122z` alone. The authored figure 76 was a third value matching neither sum nor union and is corrected here. Six branches still have a worktree on disk. THE COUNT IS NOT THE RISK, and treating it as one is the trap this plan exists to avoid: most of these commits belong to plans that `main` itself records as SUPERSEDED or already EXECUTED, so the likely correct disposition for most is DELETE, not merge. But `nna8yz` proves the inverse case is also real: its lane holds a 753-line `feat(lane)` commit whose feature DID reach `main` by a different route (`lane_containment.py`), so a naive 'it is not in main, therefore merge it' reading would have re-landed a stale duplicate of shipped work.
- Scope: Decide, per branch, one of THREE dispositions with cited evidence: RECOVER (real work absent from `main`, needs merging or re-plandering), DELETE (superseded, or its substance provably landed elsewhere), or ESCALATE (cannot be decided from repository evidence; needs the maintainer). Then execute the DELETE and RECOVER decisions. This plan produces a decision RECORD first and acts second, because a branch deletion is irreversible in practice and 76 commits of history is not something to guess at.
- Scope-Paths: .aw/records/research, .aw/records/backlog
- Item-Dependencies: executed:65cuw0
- Status: reviewed
- Readiness: no-go
- From-Backlog: qliia1
- Set: laneorph
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: ut0vzr

## Workflow history
- 2026-09-18 /plan-review (opencode/its_direct-pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; reviewed as part of orchestrator `tb63qv`'s Set (findings PR-001..PR-009 recorded there and in `.aw/records/reviews/20260917-laneorph-00-tb63qv-...review.md`); readiness `no-go` on one blocking finding. THE PLAN'S OWN ACCEPTANCE CRITERION IS UNREACHABLE AS AUTHORED (PR-002, escalated as blocking OQ-04): deleting a DELETE branch does NOT silence its attention row, it converts it into an equally-failing one. `lane_work_has_landed` returns `None` for a missing branch (`runner_shared.py:1093-1096`) -> `LANE_UNKNOWN` (`:1170-1176`) -> which IS in `LANE_ATTENTION_STATES` (`:1068`) -> which `lane_drift_severity` rates `error` ON PURPOSE, its docstring stating "UNKNOWN fails too rather than warning: a landing question we cannot answer is not evidence the work landed" (`attention.py:1103-1111`). So E-07 would perform 13 IRREVERSIBLE deletions and E-08 would still fail, on `attention.lane-unknown` instead of `attention.lane-stranded`. The gate now FORBIDS the DELETE half until OQ-04 is answered while allowing RECOVER to proceed, and E-07 must predict each deleted branch's resulting rule id so E-08 compares against a predicted set rather than an assumed silence. ARITHMETIC CORRECTED (PR-005): the "76 commits" total matches neither the per-branch sum (94) nor the distinct union (43, `git rev-list --count <13> --not main`); the `wtiso` group is 26 distinct commits, IDENTICAL to `main..aw/lane/2c122z` alone, because those branches share one ancestry chain (`merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` -> 0), so "74 of the 76 belong to `wtiso`" was a double-count artifact. MEASUREMENT DISCIPLINE ADDED (PR-006): `aw attention` CANNOT be measured from inside a lane, since `stranded_lane_drift` returns `[]` when it finds no run records (`attention.py:1141-1145`) and `.aw/records/runs/` is gitignored hence absent there, so an in-lane check reports a FALSE clean; E-01, E-08, V-01 and V-08 now require a named non-lane tree and count the two lane rule ids separately. Also: the premise that Order 01 "makes the stranded report trustworthy" is false (it already is; 12/12 reported lanes verified not ancestors of `main`, zero false positives), so the dependency on Order 01 now rests only on not refilling the queue; and `6knsrx` has NO branch, so it needs no disposition. WHAT VERIFIED EXACTLY: every plan-status claim (five `superseded`, seven `executed`), the retirement headers quoted verbatim, all 13 per-branch counts, and `materialize_lane_inputs` present at `lane_containment.py:2140` and called at `oc_runipd.py:6893`. OQ-04 raised `Blocking: yes` carrying PR-002.

- 2026-09-18 reviewed (aw set): plan-review complete (reviewed as part of orchestrator tb63qv's Set): REVIEWED - OPEN QUESTIONS; PR-002 left OPEN at BLOCKER and escalated as blocking OQ-04, since deleting a DELETE branch converts its attention.lane-stranded row into an equally-failing attention.lane-unknown row and E-08 cannot pass; the gate now forbids the DELETE half until it is answered while allowing RECOVER; PR-005 FIXED, the 76-commit total was neither the per-branch sum (94) nor the distinct union (43); PR-006 FIXED, every acceptance check now names a non-lane measuring tree; readiness no-go
- 2026-09-17 to-review (aw set): Authored 2026-09-17 from a measured sweep of .aw/worktrees/ (38 worktrees/4.7G, 28 provably merged and clean) and of the 13 lane branches holding 76 unmerged commits; complete enough to critique

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Empty the stranded-lane backlog by DECIDING each branch rather than accumulating it, and leave a cited
record of why each was deleted or recovered.

TWO PREMISES CORRECTED AT REVIEW 2026-09-18, both affecting this plan's definition of done.

FIRST, the clause "Order 01 makes the stranded report trustworthy" was REMOVED because it is false. The
report already excludes a merged lane: `classify_lane_integration` classifies one `LANDED` via
`lane_work_has_landed` and `LANE_ATTENTION_STATES` omits that state (`runner_shared.py:1063-1068`,
`:1110-1180`). Measured at review HEAD, `aw attention --check` reported 12 distinct lanes and ALL 12 were
provably not ancestors of `main`, i.e. zero false positives. So this plan does not inherit a trust problem
from Order 01, and the dependency on Order 01 rests only on not refilling the queue.

SECOND, AND THIS ONE BLOCKS: DELETING A BRANCH DOES NOT SILENCE ITS ROW. `lane_work_has_landed` returns
`None` when `git rev-parse --verify <branch>` fails (`runner_shared.py:1093-1096`),
`classify_lane_integration` maps `None` to `LANE_UNKNOWN` (`:1170-1176`), `LANE_ATTENTION_STATES` INCLUDES
`LANE_UNKNOWN` (`:1068`), and `lane_drift_severity` returns `error` for both reportable states, its
docstring stating "UNKNOWN fails too rather than warning: a landing question we cannot answer is not
evidence the work landed" (`attention.py:1103-1111`). So E-07's deletions convert each
`attention.lane-stranded` row into an `attention.lane-unknown` row that fails `aw attention --check`
identically, and E-08's acceptance criterion is UNREACHABLE as authored. This is OQ-04, blocking, and the
maintainer's to resolve; do not execute E-07 before it is answered.

WHY EVIDENCE-FIRST AND NOT A BULK SWEEP. The four largest branches (26 of the 43 distinct commits, since
they share one ancestry chain) all belong to the
`wtiso` Set, and every one of those plans is filed `superseded` in `main` with an explicit retirement
reason already written (`qcqhj7`: "superseded by the `lanectn` Set"; `58ha43`: "retiring UNLANDED, with
no successor for its main deliverable"; `2c122z`: "retiring UNLANDED ... never reachable"). So the bulk
of the apparent risk is already-decided work whose branches were simply never cleaned up. Deleting them
is correct. But `nna8yz` is the counter-example that forbids doing this by branch size or by Set alone:
its lane holds `feat(lane): materialize lane inputs by copy with a sealed manifest` (753 insertions),
that feature IS present in `main` today, and it got there through `lane_containment.py` rather than
through this branch. Only a per-branch substance check distinguishes those two cases, and getting it
wrong in the RECOVER direction re-lands a stale duplicate of shipped code.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Establish the inventory and the decision rule

- [ ] E-01 Re-measure the branch inventory at execution HEAD and record it, since `main` moves and a stale list would authorize a wrong deletion. For every `refs/heads/aw/lane/*`: commits ahead of the integration target, whether a worktree exists, the last commit date, the owning plan id6 if any, and that plan's CURRENT status and directory in `main`. REPORT BOTH THE PER-BRANCH COUNTS AND THE DISTINCT UNION (`git rev-list --count <branches> --not <target>`), and state which is which: summing per-branch counts double-counts shared ancestry, which is how the authored figure of 76 arose against a real union of 43 (F-1). NAME THE TREE the measurement was taken in, and take it from the MAIN CHECKOUT: `git worktree list` differs inside a lane, and `aw attention` reports a false clean there for lack of run records (F-11).
  - Depends on: none
  - Expected outcome: a table of every lane branch with a non-zero ahead-count, with its owning plan's status, plus the distinct-union total stated separately from the sum. The review baseline is 13 branches / 43 distinct commits / 94 summed, and a material difference from that must be noted rather than silently absorbed. A branch listed in this plan whose ref no longer resolves (e.g. `6knsrx`, which has none) is recorded as needing no disposition rather than dropped silently.
  - Execution state: pending

- [ ] E-02 Write the DISPOSITION RULE before applying it, so the decisions are reproducible rather than ad hoc. State the evidence that justifies each of DELETE / RECOVER / ESCALATE, and state explicitly that neither branch size nor Set membership is sufficient on its own, citing `nna8yz` (superseded-looking but holds a feature that landed elsewhere) and the `wtiso` four (large but already retired with reasons). THE RULE MUST NAME THE ONE MERGED-NESS PREDICATE IT USES and must be `runner_shared.lane_work_has_landed` (`:1077-1106`), not a hand-rolled git call: a second definition of "merged" is how this plan and Order 01 would drift. THE RULE MUST ALSO FORBID A COMMIT-SUBJECT MATCH as landing evidence (see OQ-03's method correction) and require an ANCESTRY or CONTENT test.
  - Depends on: E-01
  - Expected outcome: a written rule an independent reader could apply to the same table and reach the same dispositions, naming the shared predicate it consumes and explicitly excluding subject-grep as evidence.
  - Execution state: pending

### Task group 2: Decide each branch on evidence

- [ ] E-03 For each branch whose owning plan is `superseded` in `main`, cite the retirement header already recorded there and mark it DELETE. Do not re-litigate a retirement decision the repository already made; the deliverable is the citation, not a fresh judgement.
  - Depends on: E-02
  - Expected outcome: a per-branch citation of the existing `RETIRED <date>:` reason. Expected to cover `qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z` (and `6knsrx` if a branch exists), i.e. the bulk of the 76 commits.
  - Execution state: pending

- [ ] E-04 For each branch whose owning plan is `executed` in `main`, determine per branch whether the lane's SUBSTANCE reached `main` by another route, and cite the landing site. A textual diff against `main` is NOT sufficient evidence, because `main` has evolved since; identify the feature and locate it. Mark DELETE where the substance landed, RECOVER where it did not.
  - Depends on: E-02
  - Expected outcome: a per-branch verdict with the landing site named for each DELETE. `nna8yz` is expected to resolve DELETE with `lane_containment.py` cited as the landing site; `03ie04`, `fn2l1u`, `r2i1b1`, `ybkmzp`, `mm5p3v`, `d7qoxv` each need their own check.
  - Execution state: pending

- [ ] E-05 For any branch with no owning plan, or where E-04 cannot reach a cited conclusion, mark ESCALATE and write the specific question the maintainer must answer. `upgtest` is expected here (it is not a plan lane). Do NOT guess a disposition to make the table look complete.
  - Depends on: E-04
  - Expected outcome: an explicit ESCALATE list, each with a one-line question; an empty list is an acceptable outcome if every branch resolved.
  - Execution state: pending

- [ ] E-06 Immortalize the decision table to `.aw/records/research/` with `aw research new`, so the reasoning survives the branch deletions that follow. This must happen BEFORE E-07, since after deletion the evidence for a DELETE is gone.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: a committed research record containing the full table, the rule from E-02, and the per-branch citations.
  - Execution state: pending

### Task group 3: Execute the decisions

- [ ] E-07 Execute the RECOVER decisions first, merging or re-planning each as its evidence requires, and only then delete the DELETE branches. Ordering matters: a deletion is effectively irreversible once the reflog expires, so nothing is deleted until every recovery has landed. DO NOT BEGIN THE DELETION HALF UNTIL OQ-04 IS ANSWERED: deleting a ref does not silence its attention row, it converts it into an equally-failing `attention.lane-unknown` row (F-9), so the deletions as authored cannot achieve E-08 and the maintainer must first choose the terminal state. The RECOVER half is unaffected and may proceed.
  - Depends on: E-06
  - Expected outcome: each RECOVER branch's work reachable from the integration target; each DELETE branch's ref removed with its recorded sha noted in the research record for a reflog-window rescue. Also record, per deleted branch, the attention rule id its row moves TO, so the E-08 check is compared against a predicted set rather than an assumed silence.
  - Execution state: pending

- [ ] E-08 Confirm the end state FROM THE MAIN CHECKOUT, naming the tree: `aw attention --check` reports the terminal lane set OQ-04 authorized (which is NOT necessarily an empty report, per F-9), and `git worktree list` contains only the main checkout plus any lane a live run owns. Report the `attention.lane-stranded` and `attention.lane-unknown` counts SEPARATELY. Close backlog `qliia1` with the research record as evidence.
  - Depends on: E-07
  - Expected outcome: a lane report matching the state OQ-04 authorized, with the two rule ids counted separately, measured in a named tree that is not a lane (an in-lane report is a false clean, F-11); and `qliia1` closed `done` with cited evidence.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- A retired plan carries its reason in a `RETIRED <date>: <reason>` header in
  `.aw/records/plans/superseded/`. That header is the authoritative record of an already-made decision;
  this plan CITES it rather than re-deciding.
- `aw attention --check` is the canonical stranded-lane reporter (repaired by plan `pr5b0t`), and it is
  the acceptance surface for E-08. Do not hand-roll a second scan.
- Durable analysis belongs in `.aw/records/research/` via `aw research new`, never hand-named (AGENTS.md).
  E-06 exists because the evidence for a DELETE ceases to exist once the branch is gone.
- A lane BRANCH is the durable record of a lane's work while a WORKTREE is disposable: the 2026-09-17
  sweep removed 28 worktrees and zero branches. This plan is the converse operation and must be held to
  a correspondingly higher evidentiary bar.
- The execution contract forbids `git add -A` and forbids pushing; commit only declared `Scope-Paths`,
  path-scoped.

## Findings

| id | finding | evidence |
|---|---|---|
| F-1 | 13 lane branches hold **43 DISTINCT** commits unreachable from `main` (per-branch counts sum to 94; the authored figure of 76 was neither) | re-measured at review HEAD `f741596e`: per-branch `2c122z` 26, `58ha43` 22, `7p9n2v` 16, `rchpms` 10, `upgtest`/`qcqhj7`/`nna8yz`/`mm5p3v` 3, `ybkmzp`/`fn2l1u`/`03ie04` 2, `r2i1b1`/`d7qoxv` 1 (sum 94); `git rev-list --count <all 13> --not main` = **43**. The gap is shared ancestry, proven by `merge-base --is-ancestor aw/lane/58ha43 aw/lane/2c122z` -> 0 |
| F-2 | The `wtiso` group is **26** distinct commits, not 74, and unions to exactly `2c122z` alone; every plan of that Set is `superseded` in `main` | `git rev-list --count aw/lane/{2c122z,58ha43,7p9n2v,rchpms,qcqhj7} --not main` = 26, identical to `main..aw/lane/2c122z`; `.aw/records/plans/superseded/` holds `qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z`, `6knsrx`, each with a `RETIRED 2026-09-02:` header (verified verbatim for `58ha43` and `2c122z`). NOTE `6knsrx` has NO BRANCH (`git rev-parse --verify aw/lane/6knsrx` fails), so it needs no disposition |
| F-3 | Those retirements are explicit and already reasoned, so the branches need citing not deciding | e.g. `58ha43`: "retiring UNLANDED, with no successor for its main deliverable"; `2c122z`: "retiring UNLANDED ... never reachable" |
| F-4 | Branch size and Set membership are NOT sufficient evidence, in the direction that causes real harm | `nna8yz` (3 commits, plan `executed`) holds `feat(lane) ... sealed manifest` at 753 insertions; that feature IS in `main` via `lane_containment.py`, so RECOVER would re-land shipped work |
| F-5 | A textual diff against `main` cannot answer "did this land", because `main` has moved | all four sampled branches report DIFFERS against `main` for their touched files, including `nna8yz` whose substance demonstrably landed |
| F-6 | Every branch with an owning plan has that plan already `executed` or `superseded` in `main`; none is mid-flight | checked per id6: `nna8yz`/`03ie04`/`d7qoxv`/`fn2l1u`/`mm5p3v`/`r2i1b1`/`ybkmzp` all `executed`; the `wtiso` six all `superseded` |
| F-7 | `upgtest` has no owning plan id6, so it cannot be dispositioned by plan status | it is not a `<id6>` lane name; expected to land in E-05's ESCALATE list |
| F-8 | Seven of the 13 have NO worktree, so they consume no disk and are purely a signal problem | the 2026-09-17 sweep left 6 lane worktrees; `2c122z`, `58ha43`, `7p9n2v`, `rchpms`, `qcqhj7`, `nna8yz`, `03ie04` are branch-only. RE-MEASURE FROM THE MAIN CHECKOUT: `git worktree list` reports a different set from inside a lane |
| F-9 | **DELETING A DELETE BRANCH DOES NOT REMOVE ITS ROW FROM `aw attention`; it converts it to an equally-failing `attention.lane-unknown` row** | `lane_work_has_landed` returns `None` for a missing branch (`runner_shared.py:1093-1096`) -> `LANE_UNKNOWN` (`:1170-1176`) -> in `LANE_ATTENTION_STATES` (`:1068`) -> `lane_drift_severity` = `error` (`attention.py:1103-1111`, whose docstring says UNKNOWN fails deliberately). E-08's criterion is unreachable as authored; see OQ-04 |
| F-10 | The stranded report is ALREADY free of merged-lane false positives, so this plan inherits no trust problem from Order 01 | measured at review: `aw attention --check` gave 19 rows over 12 DISTINCT lanes, all 12 NOT ancestors of `main`; the six merged lanes named in Order 01 appear zero times |
| F-11 | `aw attention` CANNOT BE MEASURED FROM INSIDE A LANE: it reports a false clean | `stranded_lane_drift` returns `[]` when it finds no run records (`attention.py:1141-1145`), and `.aw/records/runs/` is gitignored (`.aw/.gitignore: records/runs/`) hence absent in a lane. E-01 and E-08 must name the measuring tree |

## Proposed changes (ordered, validatable)

1. Re-measure the inventory at execution HEAD (E-01) and write the disposition rule (E-02).
2. Disposition each branch on cited evidence: retirement headers for the `superseded` group (E-03),
   substance-landed checks for the `executed` group (E-04), explicit escalation for the remainder (E-05).
3. Immortalize the decision table to `.aw/records/research/` BEFORE any deletion (E-06).
4. Land every RECOVER, then delete every DELETE, recording each deleted sha (E-07).
5. Verify an empty stranded-lane report and close `qliia1` (E-08).

This plan changes no product code. Its deliverables are a research record, a set of branch operations,
and a closed backlog item.

## Deferred / out of scope (with reason)

- PREVENTING future accumulation is Order 01 (`65cuw0`); this plan drains the existing backlog only.
  Running this plan without Order 01 would refill the queue on the next run, which is why the dependency
  is declared rather than merely noted.
- The 2 staged deletions in the `lqly9m` and `pr5b0t` worktrees are a DIFFERENT defect (backlog `5bmq5f`,
  a backlog item duplicated across status directories) and are not lane-work to triage.
- `perf/att-set-speed` is the maintainer's own branch, not an `aw/lane/*` lane, and is untouched.
- Deleting merged lane branches is out of scope here as in Order 01: those hold no unmerged work and are
  not what this plan is about.

## Scope check

- Over-scope: none. Every E-item is on the path from "13 undecided branches" to "an empty stranded
  report with the reasoning recorded".
- Under-scope: the ESCALATE bucket is deliberately left for the maintainer rather than guessed. If E-05
  is non-empty, this plan can still finalize: an escalation with a written question is a completed
  disposition, whereas a fabricated verdict is not.

## Required tests / validation

- `aw attention --check` output pasted FROM A NAMED NON-LANE TREE, with `attention.lane-stranded` and
  `attention.lane-unknown` counted separately, matching the terminal state OQ-04 authorized. An empty
  report is NOT the expected outcome unless OQ-04 resolves to option (d) (F-9, F-11).
- The committed research record path, with its decision table, cited per branch.
- For every DELETE: the recorded sha, plus the citation that justified it (a retirement header, or the
  landing site of its substance). Never a commit-SUBJECT match, which OQ-03 records as an unsound method
  that already produced a wrong classification once.
- For every RECOVER: evidence its work is now reachable from the integration target, established with
  `runner_shared.lane_work_has_landed` (the one shared predicate) rather than a hand-rolled check.
- `python3 -m pytest` bare and green, pasted, since E-07 may merge real code. RUN IT BARE: `addopts`
  already supplies the flags, and a second `-q` suppresses the summary line this item requires. Take a
  baseline in the SAME tree first and gate on NO NEW failures, since a managed worker lane fails a set of
  lifecycle tests by design (backlog `770fkp`).
- `qliia1` shown `done` with evidence.

## Spec / documentation sync

N/A: no spec governs lane-branch triage, and this plan changes no product behavior. No `.spec.md` is
declared in `Scope-Paths`.

## Open questions

### OQ-01: Is deleting a branch whose plan is already `superseded` a decision this plan may make alone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: YES, and citing rather than re-deciding is what keeps it in scope.
  The repository ALREADY made the substantive call: each of the six `wtiso` plans carries an explicit
  `RETIRED 2026-09-02:` header stating it was superseded or is unlanded-with-no-successor. Deleting the
  branch of an already-retired plan enacts a recorded decision; it does not make a new one. E-06 preserves
  the sha of every deleted branch so a reflog-window rescue stays possible if a citation turns out wrong.

### OQ-02: What if a RECOVER branch no longer merges cleanly onto a moved `main`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Then it is RE-PLANNED, not force-merged. These branches are between
  three days and three weeks old against a fast-moving `main`, so a conflicted merge is the expected
  case rather than the exception, and resolving a stale three-week-old conflict by hand is exactly how
  shipped behavior gets silently reverted. E-07 therefore permits recovery by authoring a fresh plan that
  re-implements the work against current HEAD, with the lane branch cited as the source. Recovering the
  INTENT is the requirement; replaying the commits is not.

### OQ-03: Should `upgtest` be deleted since it has no owning plan?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED 2026-09-17 by the maintainer: DO NOT DELETE. PRESERVE and
  assess for recovery. The premise that "nothing in the repository records... whether its work is still
  wanted" was tested and is FALSE: the branch carries 3,063 insertions across 14 files, and the
  repository records what they are.
  MEASURED at 2026-09-17 (re-derive at execution HEAD rather than trusting these figures):
  `tools/aw_upgrade_test.py` (1370 lines, an upgrade rehearsal harness), `tests/test_aw_upgrade_test.py`
  (763 lines), `tools/README.md` (+77), THREE plans that exist NOWHERE in `main` (`h90ij1`, `z1yefm`,
  `i8u6hh`) each with its own `.review.md`, and two backlog items. So this is the one branch in the
  fourteen whose content is genuinely unlanded rather than squash-merged or deliberately retired.
  WHY IT IS WANTED, from its own review record rather than inferred: the review of `z1yefm` records a
  HIGH finding that TWO split-brain detectors disagree, engine's being content-aware
  (`engine.py:119-142`) while doctor's tests a bare `.is_dir()` (`doctor.py:323-326`), and that because
  `.agents/skills` is the intended permanent skills location for BOTH layouts, doctor "misreports
  forever". The record states the plan as originally written "would have shipped, passed its own
  validation, and left the user still reading 'Dual layouts detected'". That is a live user-visible
  defect with a written analysis, which is the opposite of abandoned scratch.
  THE DISPOSITION IS THEREFORE `RECOVER`, NOT `DELETE`, and E-05 should record it as such rather than as
  an ESCALATE. NOTE what recovery still owes, because "preserve" is not "merge": the branch was last
  touched 2026-09-12 and `main` has moved substantially since, so E-07 must establish a baseline, merge,
  and re-run the suite rather than fast-forwarding on the strength of this answer. The three unlanded
  plans are `to-review`/`go-pending-approval` per their own review records and still need human
  approval before any of them EXECUTES; recovering the branch makes them visible, it does not approve
  them.
  A METHOD CORRECTION THIS QUESTION EXPOSED, recorded because it affects E-04 and could authorize a
  wrong deletion. An earlier triage in this repository classified `upgtest` as already-landed by
  matching its tip commit SUBJECT against `git log main --grep`. That method is UNSOUND: the grep
  matched the lane's own commit rather than a commit on `main`, and every one of the three commits
  returns `git merge-base --is-ancestor <sha> main` -> false. E-04 must use an ANCESTRY or CONTENT test,
  never a subject match, and E-02's disposition rule should say so explicitly.

### OQ-04: Deleting a DELETE branch converts its stranded row into an equally-failing `attention.lane-unknown` row. What is this plan's terminal state?

- Blocking: yes
- Finding: PR-002
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT DECIDED BY THE REVIEWER, because every available route either
  changes a deliberately fail-closed contract or changes this plan's definition of done, and both are the
  maintainer's call. THE MECHANISM, measured at review HEAD and cited in F-9: a deleted branch makes
  `lane_work_has_landed` return `None`, which becomes `LANE_UNKNOWN`, which is in `LANE_ATTENTION_STATES`,
  which `lane_drift_severity` rates `error` ON PURPOSE ("a landing question we cannot answer is not
  evidence the work landed"). So E-07 deletes 13 refs and E-08 still fails, on `attention.lane-unknown`
  instead of `attention.lane-stranded`, once per deleted branch. OPTIONS: (a) ACCEPT an unknown-row set as
  the terminal state, rewriting E-08 and the completion criteria to demand exactly that predicted set row
  by row; (b) ALSO PRUNE the run records that name those lanes, which removes the rows at the source but
  edits run history and lies outside the declared `Scope-Paths`; (c) TEACH the classifier a
  DISPOSITIONED state, which is new public behavior and needs its own plan and spec thought; or (d) DO NOT
  DELETE REFS AT ALL, keeping them as the cheap durable record Order 01's OQ-02 already argues for, and
  closing `qliia1` on the committed research record alone. The reviewer's read is that (d) is the smallest
  correct answer and (a) the next, since both leave the fail-closed contract intact; but (b) and (c) touch
  surfaces beyond this Set and the choice is not the reviewer's to make. Until answered, E-07's RECOVER
  half may proceed and its DELETE half may not.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted inventory table measured at execution HEAD, with the per-branch
    ahead-count, worktree presence, owning plan id6, and that plan's status/directory. BOTH the summed and
    the DISTINCT-UNION commit totals, labelled, with any divergence from the review baseline (13 branches
    / 43 distinct / 94 summed) stated explicitly. The measuring TREE named, and it must not be a lane.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the written disposition rule, quoted, showing it names the evidence required for
    each of DELETE / RECOVER / ESCALATE and states that size and Set membership alone are insufficient.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: for each `superseded`-plan branch, the quoted `RETIRED ...` header from the plan
    file in `main`. A verdict with no quoted header does not satisfy this item.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: per branch, the identified feature and either the landing site in `main` (for
    DELETE) or a demonstration of its absence (for RECOVER). The `nna8yz` row must name
    `lane_containment.py` or correct the 2026-09-17 finding with evidence. A bare `git diff` verdict is
    explicitly NOT acceptable evidence for this item (F-5).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the ESCALATE list with one written question per entry, or a statement that it is
    empty because every branch resolved with a citation.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: the committed research record path and its table, shown to exist BEFORE any
    branch deletion (cite the commit order).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: for every RECOVER, proof its work is reachable from the integration target; for
    every DELETE, the recorded sha. Plus `python3 -m pytest` bare and green if any code merged.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: pasted `aw attention --check` from a NAMED tree that is not a lane, with the
    `attention.lane-stranded` and `attention.lane-unknown` row counts stated SEPARATELY and compared
    against the terminal set OQ-04 authorized; pasted `git worktree list`; and `qliia1` shown `done` with
    evidence. An empty report measured inside a lane does NOT satisfy this item (F-11), and an unknown-row
    count that was not predicted in E-07 is a failure of this item rather than a footnote.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and it carries a HIGHER bar than most:
E-07 deletes git branches, which is effectively irreversible once the reflog expires. The executor MUST
NOT delete any branch before E-06's research record is committed, and MUST record each deleted sha.

AND MUST NOT DELETE ANY BRANCH BEFORE OQ-04 IS ANSWERED. Deleting a ref does not silence its attention row
(F-9), so the deletions as authored cannot achieve this plan's own acceptance criterion, and performing an
irreversible act to reach an unreachable end state is the specific mistake this gate now blocks. The
RECOVER half of E-07 is unaffected.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL command output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. A non-empty
ESCALATE list does NOT block finalization, provided each entry carries its written question.
