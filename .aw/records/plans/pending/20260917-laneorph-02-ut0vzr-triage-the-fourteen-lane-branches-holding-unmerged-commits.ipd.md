# IPD: Triage the fourteen lane branches holding unmerged commits

- Date: 2026-09-17
- Kind: child
- Concern: THIRTEEN `aw/lane/*` branches hold commits not reachable from `main` (76 commits total), and nobody can currently say which hold recoverable work. Measured 2026-09-17: `2c122z` 26, `58ha43` 22, `7p9n2v` 16, `rchpms` 10, `upgtest`/`qcqhj7`/`nna8yz`/`mm5p3v` 3 each, `ybkmzp`/`fn2l1u`/`03ie04` 2 each, `r2i1b1`/`d7qoxv` 1 each. Six still have a worktree on disk. THE COUNT IS NOT THE RISK, and treating it as one is the trap this plan exists to avoid: 74 of the 76 commits belong to plans that `main` itself records as SUPERSEDED or already EXECUTED, so the likely correct disposition for most is DELETE, not merge. But `nna8yz` proves the inverse case is also real: its lane holds a 753-line `feat(lane)` commit whose feature DID reach `main` by a different route (`lane_containment.py`), so a naive 'it is not in main, therefore merge it' reading would have re-landed a stale duplicate of shipped work.
- Scope: Decide, per branch, one of THREE dispositions with cited evidence: RECOVER (real work absent from `main`, needs merging or re-plandering), DELETE (superseded, or its substance provably landed elsewhere), or ESCALATE (cannot be decided from repository evidence; needs the maintainer). Then execute the DELETE and RECOVER decisions. This plan produces a decision RECORD first and acts second, because a branch deletion is irreversible in practice and 76 commits of history is not something to guess at.
- Scope-Paths: .aw/records/research, .aw/records/backlog
- Item-Dependencies: executed:65cuw0
- Status: draft
- From-Backlog: qliia1
- Set: laneorph
- Order: 2
- Highest E allocated: 08
- Author: opencode/its_direct-pt3-claude-opus-5-1m-us
- Id: ut0vzr

## Workflow history

- 2026-09-17 draft (opencode/its_direct-pt3-claude-opus-5-1m-us): created.

## Goal

Empty the stranded-lane backlog by DECIDING each branch rather than accumulating it, and leave a cited
record of why each was deleted or recovered. Order 01 makes the stranded report trustworthy; this plan
makes it EMPTY, which is the only state in which it functions as an alarm.

WHY EVIDENCE-FIRST AND NOT A BULK SWEEP. The four largest branches (74 of 76 commits) all belong to the
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

- [ ] E-01 Re-measure the branch inventory at execution HEAD and record it, since `main` moves and a stale list would authorize a wrong deletion. For every `refs/heads/aw/lane/*`: commits ahead of the integration target, whether a worktree exists, the last commit date, the owning plan id6 if any, and that plan's CURRENT status and directory in `main`.
  - Depends on: none
  - Expected outcome: a table of every lane branch with a non-zero ahead-count, with its owning plan's status; the 2026-09-17 reading was 13 branches / 76 commits, and a material difference from that must be noted rather than silently absorbed.
  - Execution state: pending

- [ ] E-02 Write the DISPOSITION RULE before applying it, so the decisions are reproducible rather than ad hoc. State the evidence that justifies each of DELETE / RECOVER / ESCALATE, and state explicitly that neither branch size nor Set membership is sufficient on its own, citing `nna8yz` (superseded-looking but holds a feature that landed elsewhere) and the `wtiso` four (large but already retired with reasons).
  - Depends on: E-01
  - Expected outcome: a written rule an independent reader could apply to the same table and reach the same dispositions.
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

- [ ] E-07 Execute the RECOVER decisions first, merging or re-planning each as its evidence requires, and only then delete the DELETE branches. Ordering matters: a deletion is effectively irreversible once the reflog expires, so nothing is deleted until every recovery has landed.
  - Depends on: E-06
  - Expected outcome: each RECOVER branch's work reachable from the integration target; each DELETE branch's ref removed with its recorded sha noted in the research record for a reflog-window rescue.
  - Execution state: pending

- [ ] E-08 Confirm the end state: `aw attention --check` reports NO stranded lane, and `git worktree list` contains only the main checkout plus any lane a live run owns. Close backlog `qliia1` with the research record as evidence.
  - Depends on: E-07
  - Expected outcome: an empty stranded-lane report, and `qliia1` closed `done` with cited evidence.
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
| F-1 | 13 lane branches hold 76 commits unreachable from `main` | measured 2026-09-17: `2c122z` 26, `58ha43` 22, `7p9n2v` 16, `rchpms` 10, `upgtest`/`qcqhj7`/`nna8yz`/`mm5p3v` 3, `ybkmzp`/`fn2l1u`/`03ie04` 2, `r2i1b1`/`d7qoxv` 1 |
| F-2 | 74 of the 76 commits belong to the `wtiso` Set, every plan of which is `superseded` in `main` | `.aw/records/plans/superseded/` holds `qcqhj7`, `rchpms`, `7p9n2v`, `58ha43`, `2c122z`, `6knsrx`, each with a `RETIRED 2026-09-02:` header |
| F-3 | Those retirements are explicit and already reasoned, so the branches need citing not deciding | e.g. `58ha43`: "retiring UNLANDED, with no successor for its main deliverable"; `2c122z`: "retiring UNLANDED ... never reachable" |
| F-4 | Branch size and Set membership are NOT sufficient evidence, in the direction that causes real harm | `nna8yz` (3 commits, plan `executed`) holds `feat(lane) ... sealed manifest` at 753 insertions; that feature IS in `main` via `lane_containment.py`, so RECOVER would re-land shipped work |
| F-5 | A textual diff against `main` cannot answer "did this land", because `main` has moved | all four sampled branches report DIFFERS against `main` for their touched files, including `nna8yz` whose substance demonstrably landed |
| F-6 | Every branch with an owning plan has that plan already `executed` or `superseded` in `main`; none is mid-flight | checked per id6: `nna8yz`/`03ie04`/`d7qoxv`/`fn2l1u`/`mm5p3v`/`r2i1b1`/`ybkmzp` all `executed`; the `wtiso` six all `superseded` |
| F-7 | `upgtest` has no owning plan id6, so it cannot be dispositioned by plan status | it is not a `<id6>` lane name; expected to land in E-05's ESCALATE list |
| F-8 | Seven of the 13 have NO worktree, so they consume no disk and are purely a signal problem | the 2026-09-17 sweep left 6 lane worktrees; `2c122z`, `58ha43`, `7p9n2v`, `rchpms`, `qcqhj7`, `nna8yz`, `03ie04` are branch-only |

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

- `aw attention --check` output pasted, showing no stranded lane remains (or showing exactly the
  ESCALATE set, if the maintainer deferred some).
- The committed research record path, with its decision table, cited per branch.
- For every DELETE: the recorded sha, plus the citation that justified it (a retirement header, or the
  landing site of its substance).
- For every RECOVER: evidence its work is now reachable from the integration target.
- `python3 -m pytest` bare and green, pasted, since E-07 may merge real code.
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
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: OPEN, and deliberately not guessed. `upgtest` holds 3 commits, has a
  live worktree, is named for a purpose ("upgrade test") rather than a plan id6, and was last touched
  2026-09-12. Nothing in the repository records who created it or whether its work is still wanted, so
  the disposition is the maintainer's. E-05 carries it as an ESCALATE with this question.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the pasted inventory table measured at execution HEAD, with the per-branch
    ahead-count, worktree presence, owning plan id6, and that plan's status/directory. Any divergence
    from the 2026-09-17 baseline (13 branches / 76 commits) stated explicitly.
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
  - Required evidence: pasted `aw attention --check` showing no stranded lane (or only the ESCALATE set),
    pasted `git worktree list`, and `qliia1` shown `done` with evidence.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution, and it carries a HIGHER bar than most:
E-07 deletes git branches, which is effectively irreversible once the reflog expires. The executor MUST
NOT delete any branch before E-06's research record is committed, and MUST record each deleted sha.

Execution contract: work in an isolated worktree, commit only the declared `Scope-Paths`, path-scoped,
never `git add -A`, never push. Paste ACTUAL command output for every V-item.

Post-gate lifecycle: `aw ipd finalize` moves this plan to `.aw/records/plans/executed/` only after
`aw ipd lint --phase pre-transition` conforms and every `V-*` carries observed evidence. A non-empty
ESCALATE list does NOT block finalization, provided each entry carries its written question.
