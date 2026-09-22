# IPD: Stop a bulk front-matter backfill racing its own run by re-deriving the edit against the settled tree

- Date: 2026-09-22
- Kind: child
- Concern: A plan whose job is to edit front matter across the whole `pending/` population is, by construction, contending with every execute item in its own run, so the more successful the run the more conflicts that plan causes and the more likely it is to be stranded. MEASURED on item `8u6770` in run `run-20260922T024054Z-2245533`, which ended `merge-refused` with a real git conflict in 13 files, ALL of them `.aw/records/plans/*.ipd.md` and NONE of them code.
  THE SHAPE IS A PURE LIFECYCLE RACE, NOT A DISAGREEMENT. `8u6770` reads plans in `.aw/records/plans/pending/` and adds two adjacent front-matter lines (`- Work-Kind:` and `- Priority:`) plus one history line to each, inheriting each value from a backlog item the plan itself names. While it ran, THE SAME RUN executed 13 of those very plans, and executing a plan moves the file `pending/` -> `executed/` AND rewrites its `- Status:` line from `approved` to `executed` AND appends its own history line. Git therefore sees both sides touching adjacent lines of a renamed file and conflicts. Measured at resolution time: of the 45 plans the lane edits, 15 had already moved to `executed/` on `main`.
  THE TWO EDITS ARE NOT IN OPPOSITION, which is what makes this losslessly resolvable and therefore worth automating. The lane's own appended history line says in as many words "status unchanged (no lifecycle transition)", so it never intended to touch `- Status:` at all. Resolution is mechanical: keep `main`'s `- Status:`, keep the lane's two new fields, keep both history lines. That is exactly what a human did on 2026-09-22 for all 13 files, verified green.
  THERE IS A TRAP IN THE OBVIOUS RESOLUTION, and it is why this must not be left to ad-hoc judgement. The lane holds a ten-day-old snapshot in which those 13 plans still read `- Status: approved`. Taking the lane's side of the conflict, which is the natural thing to do for "the branch that owns this edit", would REVERT 13 real executions and assert that 13 plans sitting in `executed/` are merely approved. A clean, conflict-free-looking resolution can therefore silently undo a lifecycle transition.
  THIS IS AN ARCHETYPE RATHER THAN AN INCIDENT. The same Set contains `lc4unl` (Order 03), which hit the same class and also ended unintegrated, and `lkexaw` (Order 01), which is the same kind of population-wide records edit. So the pattern recurs for every plan of this shape, and the cost scales with how well the run performs.
- Scope: Make a population-wide records edit survive its own run, by RE-DERIVING the intended field values against the settled tree at integration time rather than merging a stale snapshot of them, and/or by ordering such a plan after the execute items it would contend with. EXCLUDES any change to what values are written or to the inheritance rule that picks them (that is `planprio`'s own subject matter), excludes editing any plan in a terminal directory, and excludes the post-merge revalidation defect (sibling plan `tgyfs2`).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_records_only_lane_rederive.py
- Item-Dependencies: none
- Status: to-review
- Set: laneraceplan
- Order: 1
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: kl18sz
- Work-Kind: bug
- Priority: medium
- Blocks-Release: next
- From-Backlog: 21fykf

## Workflow history

- 2026-09-22 to-review (opencode its_direct/pt3-claude-opus-5-1m-us): Authored from backlog item `21fykf`, inheriting its `Blocks-Release: next` gate. The conflict shape was measured across all 13 files during a hand-resolution on 2026-09-22 and was IDENTICAL in every one (main's `- Status: executed` versus the lane's `- Status: approved` plus two new keys, and two competing history lines), which is what justifies a mechanical fix rather than case-by-case judgement. The plan deliberately offers detection-and-refusal as the minimum viable outcome (E-01/E-02) so that even if the maintainer rejects automatic re-derivation, the silent-revert trap is closed.
- 2026-09-22 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop a records-only backfill being punished for its own run's success, and make it impossible for resolving such a conflict to silently revert a lifecycle transition.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: close the trap first

- [ ] E-01 Add a pure classifier that recognizes the RECORDS-ONLY FRONT-MATTER conflict shape: every conflicting path is under `.aw/records/`, and on each the incoming side changes only front-matter keys ORTHOGONAL to `- Status:` while the target side changed `- Status:` and/or the file's lifecycle directory. It must return a three-valued answer and report UNKNOWN for anything it cannot prove, never assuming the safe-looking case.
  - Depends on: none
  - Expected outcome: given `8u6770`'s 13 real conflicting files, classifies all 13 as this shape; given a conflict touching a code path or a `- Status:`-versus-`- Status:` disagreement, returns UNKNOWN or not-this-shape.
  - Execution state: pending
- [ ] E-02 Make the integration REFUSE with a shape-specific, actionable message when E-01 recognizes this case, naming the trap explicitly: state that the incoming branch holds a STALE lifecycle snapshot, that taking its `- Status:` would revert N real executions, and name the files. This is the minimum viable outcome and is worth landing even if OQ-01 rejects automatic re-derivation.
  - Depends on: E-01
  - Expected outcome: replaying `8u6770`'s conflict produces a refusal naming the 15 already-executed plans and the safe resolution, instead of today's generic conflict text.
  - Execution state: pending

### Task group 2: re-derive instead of merge

- [ ] E-03 Implement RE-DERIVATION for the recognized shape, gated on OQ-01's answer: instead of merging the lane's stale file content, re-apply the lane's ORTHOGONAL front-matter keys onto the CURRENT `main` version of each plan, wherever that plan now lives, leaving `- Status:` and the lifecycle directory untouched. The lane's history line is appended without disturbing the target's own history entries.
  - Depends on: E-01
  - Expected outcome: applying `8u6770`'s intended edit to current `main` yields each plan carrying both new keys AND its true current `- Status:`, with zero plans moved between directories by this step.
  - Execution state: pending
- [ ] E-04 Fail closed on any file E-01 did not positively classify: re-derivation applies ONLY to the proven shape, and anything else keeps today's conflict refusal. A partially re-derivable conflict set must NOT be half-applied; either every conflicting file is classified or the whole integration refuses.
  - Depends on: E-03
  - Expected outcome: a conflict set mixing one records-only file and one code file refuses entirely, with nothing written.
  - Execution state: pending

### Task group 3: prove it and prevent the silent revert

- [ ] E-05 Add the regression file with an explicit ANTI-REVERT control: a test that FAILS if any code path can produce a result where a plan present in a terminal directory on `main` ends carrying a non-terminal `- Status:` from an incoming branch. Plus coverage of the classifier's UNKNOWN arm and E-04's all-or-nothing rule.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the file is RED against pre-fix source and GREEN after; the anti-revert control fails if re-derivation is ever widened to `- Status:`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The runner ALREADY orders a queue by declared dependency depth first (`dependency_depth` is the first key in `queue_sort_key`, and "DECLARED EDGES WIN" is stated there), so ordering a bulk-records plan after its contenders is expressible today via `- Item-Dependencies:` without new scheduler work. That is why OQ-02 treats sequencing as an available alternative rather than a feature request.
- Never edit a plan in a terminal directory: this repository closes a post-execution gap with a new corrective IPD instead. E-03 must therefore write to `executed/` plans' front matter ONLY if the maintainer explicitly permits it in OQ-03; otherwise those plans keep their missing fields and the gap is reported.
- The existing conflict handling treats conflict DETECTION as the gate's job and conflict RESOLUTION as a human/serial-ordering concern. E-02 respects that split (it improves the refusal), while E-03 deliberately crosses it, which is precisely why OQ-01 is blocking.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Finding | Evidence |
|---|---|---|
| F-1 | The conflict is records-only, never code | 13 conflicting files, all `.aw/records/plans/*.ipd.md`; the lane changes 47 files and 0 outside `.aw/records/` |
| F-2 | The two sides are orthogonal | lane adds `- Work-Kind:`/`- Priority:`; main rewrote `- Status:` and moved the file |
| F-3 | The lane never intended to touch status | its own history line reads "status unchanged (no lifecycle transition)" |
| F-4 | Taking the lane's side reverts real executions | the lane's snapshot still says `approved` for 15 plans now in `executed/` on main |
| F-5 | The shape was uniform across all 13 files | a single mechanical rule resolved every one, verified green |
| F-6 | It is an archetype, not an incident | sibling `lc4unl` hit the same class in the same run; `lkexaw` is the same plan shape |

## Proposed changes (ordered, validatable)

1. A three-valued classifier for the records-only front-matter conflict shape (E-01).
2. A shape-specific refusal naming the stale-snapshot trap and the safe resolution (E-02).
3. Re-derivation of orthogonal keys onto the current tree, gated on OQ-01 (E-03).
4. All-or-nothing fail-closed behavior for unclassified files (E-04).
5. Regression coverage with an explicit anti-revert control (E-05).

## Deferred / out of scope (with reason)

- WHICH values a backfill writes and the inheritance rule that chooses them: that is `planprio`'s subject (`8u6770`, `lc4unl`, `lkexaw`). This plan is about surviving integration, not about the values.
- The post-merge revalidation baseline defect (sibling plan `tgyfs2`): a different cause of the same run's strandings. `8u6770` failed on a genuine git conflict, not on a suite verdict.
- Editing plans already in `executed/` to add their missing fields: deferred to OQ-03 because it collides with the standing rule against editing terminal-directory plans.
- A general-purpose semantic merge driver for records: far wider than the measured problem. This plan addresses ONE proven shape and fails closed on everything else.

## Scope check

- Over-scope: none. One source path plus one new test file.
- Under-scope: this plan does not re-run `8u6770` itself. That lane was discarded and the work re-derived by hand, because the lane's content is a mechanical lookup that is cheaper to recompute than to merge; the 15 already-executed plans consequently still lack the two fields, which OQ-03 covers.

## Required tests / validation

- `python3 -m pytest tests/test_records_only_lane_rederive.py` GREEN after, and RED before, the before-run produced by reverting only the source file while keeping the new tests.
- `python3 -m pytest` bare, count line pasted, no new failing node ids against a baseline taken in the same worktree before the change.
- A REPLAY against the real recorded conflict: reconstruct `8u6770`'s conflicting file set from git (the lane branch and the merge base are both still resolvable) and show the classifier recognizing all 13 and the refusal or re-derivation behaving as specified. A synthetic fixture alone is insufficient for F-5.
- The anti-revert control demonstrated FAILING when re-derivation is deliberately widened to include `- Status:`.

## Spec / documentation sync

No `.spec.md` amendment if the plan stops at E-02 (a better refusal message changes no contract). If OQ-01 approves E-03, the integration contract DOES change, because a conflicting merge would no longer be purely human-resolved, and the spec text that assigns conflict resolution to a human/serial ordering must be amended in the same change. The executor must then declare that `.spec.md` path in `Scope-Paths` BEFORE editing it and state the reason here, per the plan-amends-spec rule.

## Open questions

### OQ-01: May the integration RE-DERIVE a records-only front-matter edit, or must it only refuse more informatively?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT the executor's call, because it changes a stated division of responsibility: today conflict DETECTION is the gate's and RESOLUTION is a human's. Re-derivation is safe in the narrow proven shape and removes a recurring manual chore, but it means the runner rewrites records content during integration, and a bug there writes wrong metadata into permanent history. RECOMMENDATION: approve E-03 but ONLY behind E-01's positive classification and E-04's all-or-nothing rule, since the failure mode is then a refusal rather than a bad write. If the answer is no, this plan still lands E-01/E-02, which closes the silent-revert trap, and that is a genuine improvement on its own.

### OQ-02: Should a bulk-records plan instead be SEQUENCED after the execute items it contends with?

- Blocking: no
- Status: resolved
- Owner: executor
- Resolution or deferral rationale: RESOLVED as a complementary mitigation, not a substitute, and it needs no code here. The scheduler already honors declared edges first (`dependency_depth` is `queue_sort_key`'s first key), so a plan of this shape CAN be ordered last today by declaring `- Item-Dependencies:` on the items it would contend with. That is a per-plan authoring choice, so it belongs in the authoring guidance rather than in this code change; it is also insufficient alone, because a plan can contend with items in a DIFFERENT run (as happened here, where a second driver held ten of the same files), which no intra-queue edge can order.

### OQ-03: Should the 15 plans that reached `executed/` before the backfill ran have the two fields added retroactively?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: DEFERRED to the maintainer because it collides with a standing rule. `aw ipd set` will not write to a plan in `executed/`, and the repository forbids editing a terminal-directory plan in place, so adding the fields requires either an explicit exception or accepting that those plans stay unlabelled forever. The executor must NOT decide this and must NOT edit any `executed/` plan absent an explicit answer. Reported as a known gap rather than silently closed.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the classifier run over the RECONSTRUCTED real conflict set from `8u6770`, pasting its verdict for each of the 13 files, plus its verdict for two negative cases (a code-path conflict and a `- Status:`-versus-`- Status:` conflict) showing not-this-shape or UNKNOWN.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the actual refusal text pasted for the replayed conflict, showing it names the stale-snapshot trap, the count of already-executed plans, and the safe resolution; contrasted with the generic text produced before the change.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: for at least three real plans (one still `pending/`, one now `executed/`, one moved between directories), the resulting front matter pasted showing both new keys present AND the true current `- Status:` preserved, plus `git status` evidence that no plan changed directory as a result of this step.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: a mixed conflict set (one records-only file plus one code file) shown refusing ENTIRELY, with evidence that nothing was written (clean `git status` and unchanged file digests for both paths).
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: the new test file GREEN after and RED before, the bare suite count line, and the anti-revert control demonstrated FAILING when re-derivation is widened to `- Status:` (paste the failing assertion).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is human-approved before execution and is executed under the repository's standing agent execution contract: commit ONLY the declared `Scope-Paths` through `aw commit`, never `git add -A` and never push; paste ACTUAL runner output for every test claim; and do not move this plan to `.aw/records/plans/executed/` until `aw ipd lint --phase pre-transition` conforms and every `V-*` above carries concrete observed evidence. A worker-role lane may NOT perform the terminal transition (`AW-LIFECYCLE-ROLE-001`): the runner owns `aw ipd begin`/`aw ipd finalize`.

OQ-01 IS BLOCKING AND GATES E-03 ONLY. An executor without an answer must land E-01/E-02 (detection plus a better refusal, which changes no contract), record the stop, and NOT implement re-derivation on the maintainer's behalf. OQ-03 gates any edit to an `executed/` plan: absent an explicit answer, do not touch one. THE SPECIFIC HAZARD OF THIS PLAN is that it writes to permanent records during integration, so E-04's all-or-nothing rule and E-05's anti-revert control are not optional: a wrong write here corrupts history rather than merely failing a run.
