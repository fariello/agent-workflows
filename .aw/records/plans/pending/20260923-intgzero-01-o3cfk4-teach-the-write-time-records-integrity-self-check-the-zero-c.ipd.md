# IPD: Teach the write-time records integrity self-check the zero-claimant case it is blind to, and tell a run at startup when the board it is about to work from is already invalid

- Date: 2026-09-23
- Kind: child
- Concern: BACKLOG `4y7nzh` MAKES THREE RECOMMENDATIONS AND RECOMMENDS "(i) PLUS (iii)". MEASURED AT HEAD `22cf67d9`: (i) IS BUILT, (iii) IS NOT, AND (i) HAS A HOLE ITS AUTHOR DID NOT ANTICIPATE. The item asks the runner to "assert record integrity for the ids it touched immediately after its own commit". That shipped: `runner_shared.process_backlog_close` carries a "SCOPED INTEGRITY SELF-CHECK, IMMEDIATELY AFTER OUR OWN WRITE (2026-09-22)" block that calls `backlog_item_paths_for_id`, and on a violation writes the fact into the item's `backlog_close` record, the run's `events.jsonl`, and stderr. Its design is right and this plan does not relitigate it.
  THE HOLE IS THE PREDICATE: `if len(claimants) > 1`. It detects an item existing in TWO status directories and is STRUCTURALLY BLIND to an item existing in NONE. Verified live: `backlog_item_paths_for_id(repo, "zzzz99")` returns `[]`, length 0, which the guard passes silently. So the check catches the duplicate shape and misses the absent shape.
  THAT MISSED SHAPE IS NOT HYPOTHETICAL, AND IT HAPPENED IN THIS BRANCH WHILE GRADUATING THE ITEM NEXT DOOR. Commit `ca8e22e4` committed ten backlog status moves as ten `D open/...` lines with NO `A done/...` lines (destinations were left staged-but-uncommitted because directory arguments did not expand). At that commit ten items existed in NEITHER tree. Repaired by `65109c8c`; the commit-path cause is graduated as `hv9gar` (`movehalf`). This plan owns the DETECTION half, and the asymmetry is the whole point: the duplicate shape is caught by `attention.duplicate-id` AND by the runner's self-check, while the absent shape is caught by NOTHING at any layer. `aw check backlog` on this tree reports `check.name-nonconformant` and `check.collisions-not-checked` and says nothing about a record that vanished, because every integrity rule in the family asks "is this id6 claimed more than once" and none asks "is it claimed at all".
  AND (iii) IS GENUINELY ABSENT, WHICH IS THE ITEM'S OTHER RECOMMENDED HALF. Grepping the runner for a startup consultation of the cross-tree view returns nothing; the only "board is NOT authoritative" string is inside the post-close self-check quoted above, i.e. it fires AFTER a close rather than BEFORE a run. The measured failure `4y7nzh` describes is precisely a run proceeding for two days on top of a board that was already invalid, so a startup report is the half that addresses the two-day blindness rather than the per-write moment.
- Scope: Close the detection gaps `4y7nzh` names, at the two layers it recommends. IN: (a) make the write-time self-check report the ZERO-claimant case as well as the many-claimant case, keeping its report-never-raise discipline; (b) add the startup report of recommendation (iii), so a run tells the operator BEFORE spawning anything that the cross-tree view is currently invalid and names the offending rule ids; (c) tests for both, including the zero case that has no coverage anywhere. OUT: recommendation (ii)'s opt-in pre-commit hook, deferred per OQ-01 because the item itself calls it "defensible" while noting local hooks are uncloned and `--no-verify`-skippable; the commit-path CAUSE of the absent-record shape, which is `hv9gar`'s (`movehalf`) subject, so this plan must not also change `offer_commit`; and making the CI gate louder, which the item explicitly forbids ("DO NOT fix this by making the CI gate louder alone: the gate was already correct, already fail-closed, and already red").
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_backlog_close.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: to-review
- Set: intgzero
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: o3cfk4
- From-Backlog: 4y7nzh
- Blocks-Release: next

## Workflow history

- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `4y7nzh`, NARROWED by measuring which of its three recommendations already exist. (i) is BUILT (the 2026-09-22 scoped self-check in `process_backlog_close`); (iii) is ABSENT; (ii) is deferred to OQ-01 on the item's own hedge about local hooks. `- Blocks-Release: next` is INHERITED from `4y7nzh`.
  THE FINDING THAT JUSTIFIES A PLAN RATHER THAN A CLOSE is that the shipped (i) tests `len(claimants) > 1` and is therefore blind to `len == 0`. Verified live (`[]`, length 0, passes). I then hit that exact shape for real in this branch at `ca8e22e4`, ten items in neither tree, so the blind spot has a measured occurrence and not merely a theoretical one.
  I DELIBERATELY SPLIT CAUSE FROM DETECTION. `hv9gar` (`movehalf`, from `mx1b4v`) owns the commit-path cause that produced `ca8e22e4`; this plan owns detection only. Both are needed: fixing the gateway stops the known route, while the zero-claimant check catches any future route, and neither subsumes the other.

## Goal

Make a records write that leaves an item in no status tree as loud as one that leaves it in two, and tell a run at startup when the board it is about to work from is already invalid.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: confirm which recommendations already exist

- [ ] E-01 RE-MEASURE ALL THREE RECOMMENDATIONS BEFORE WRITING ANYTHING, because this plan's shape rests on (i) being built and (iii) not being.
  CONFIRM (i) EXISTS AND FIND ITS PREDICATE: locate the scoped integrity self-check in `runner_shared.process_backlog_close` and quote the guard. At authoring it is `if len(claimants) > 1`.
  PROVE THE BLIND SPOT: call `backlog_item_paths_for_id` with an id6 that exists nowhere and show it returns an empty list, so the guard cannot fire. Paste it.
  CONFIRM (iii) IS STILL ABSENT: grep the runner for any startup consultation of the cross-tree attention view. At authoring, the only "board is NOT authoritative" text is inside the post-close check, not at startup.
  CONFIRM NO RULE CATCHES THE ZERO CASE ANYWHERE: run `aw check backlog --agent` and `aw attention --check --agent` and confirm neither reports a record that exists in no status tree. If one does, this plan shrinks and you must say so.
  - Depends on: none
  - Expected outcome: the shipped predicate quoted, the zero-claimant blind spot proved with pasted output, (iii) confirmed absent, and confirmation that no existing rule catches the absent-record shape; any divergence reported.
  - Execution state: pending

### Task group 2: close the zero-claimant blind spot

- [ ] E-02 MAKE THE WRITE-TIME SELF-CHECK REPORT THE ZERO CASE. The guard must distinguish three outcomes rather than two: exactly one claimant (correct), more than one (the existing `attention.duplicate-id` report), and NONE (new).
  KEEP THE EXISTING DISCIPLINE EXACTLY. The shipped block's docstring is explicit that it REPORTS AND NEVER RAISES, because "the close is already committed by this point, so refusing would leave the tree in exactly the same state while additionally killing the run". That reasoning applies identically to the zero case. Keep the `contextlib.suppress(Exception)` wrapper and the three destinations (the item's `backlog_close` record, `events.jsonl`, stderr).
  DO NOT REUSE `attention.duplicate-id` AS THE RULE NAME. A record that exists nowhere is not a duplicate identity, and mislabeling it would make the two situations indistinguishable to anyone grepping run events. Choose a name for the absent-record condition and use it consistently across all three destinations.
  SAY WHAT A READER SHOULD DO. The duplicate message tells the reader `aw attention` will report it and the board is not authoritative. The zero-case message should be equally actionable: the item's id6, the fact it is claimed by no status directory, and that the destination write was probably dropped from the commit.
  - Depends on: E-01
  - Expected outcome: a close that leaves its item in no status tree is reported in all three destinations under its own rule name, distinct from `attention.duplicate-id`; the check still never raises and never fails the run; the exactly-one case stays silent.
  - Execution state: pending

### Task group 3: recommendation (iii), the startup report

- [ ] E-03 TELL A RUN AT STARTUP THAT THE BOARD IS ALREADY INVALID, naming the rule ids. This is `4y7nzh`'s recommendation (iii) and the half that addresses the measured two-day blindness, as opposed to the per-write moment (i) covers.
  REPORT, DO NOT REFUSE. The item asks to "have `aw oc run`/`aw agy run` report at startup that the cross-tree view is currently INVALID and name the rule ids, so an operator or agent is told before spending a night's compute on top of a known-broken board", and explicitly prefers this over "adding a new refusal that could wedge a commit". A run must still start.
  PUT IT BEFORE DURABLE STATE EXISTS. The pre-flight region where the other gates run is the right seam, i.e. before the run directory is created, so the operator sees it with the other startup facts rather than buried mid-run.
  CONSUME THE EXISTING VIEW, DO NOT FORK A SECOND ONE. `aw attention --check` already computes this and CI already consumes it; call the same authority rather than writing a second integrity walk, or the two will disagree about what "invalid" means.
  IT MUST NOT BE ABLE TO BREAK A RUN. Wrap it so a failure to COMPUTE the view degrades to a warning, on the same reasoning the existing self-check uses: a diagnostic that can kill a run is worse than the blindness it cures.
  LAND IT ON BOTH HOSTS THROUGH ONE IMPLEMENTATION, sited in `runner_shared`, never in `oc_runipd` for `agy_runipd` to import.
  - Depends on: E-01
  - Expected outcome: both hosts report at startup, before the run directory exists, that the cross-tree view is invalid and which rule ids are outstanding; the run still starts; a failure to compute the view warns instead of raising; one shared implementation.
  - Execution state: pending

### Task group 4: cover both

- [ ] E-04 TEST THE ZERO CASE AND THE STARTUP REPORT, from fixtures. The zero case has NO coverage anywhere today, which is why it shipped blind.
  THE ZERO-CASE FIXTURE MUST PRODUCE THE REAL SHAPE: a close whose destination write does not reach the commit, so the id6 is claimed by no status directory. Assert the report appears in all three destinations and that the run did NOT fail.
  ASSERT THE EXACTLY-ONE CASE STAYS SILENT, so the new branch cannot become a false positive on every healthy close. This is the cheap guard that keeps the check trustworthy.
  FOR E-03, ASSERT THE ORDER: the startup report must be emitted before the run directory exists. A test that only checks the text appears somewhere would pass against a report printed too late to help.
  - Depends on: E-02, E-03
  - Expected outcome: tests failing against pre-E-02/E-03 code and passing after, covering the zero-claimant close, the healthy close staying silent, and the startup report's position before durable state.
  - Execution state: pending

## Project conventions discovered (Step 0)

- THE WRITE-TIME SELF-CHECK REPORTS AND NEVER RAISES, and its own comment gives the reason: the close is already committed, so refusing changes nothing about the tree and only kills the run. Any new branch added to it inherits that contract.
- THE RUNNER ALREADY KNOWS WHICH id6 IT WROTE, which is why a SCOPED check (one id6, one tree walk) is the cheap remedy rather than a whole-tree validation on every write.
- `attention.duplicate-id` IS THE EXISTING RULE for one id6 in two status directories, consumed by `aw attention --check` and wired fail-closed in CI (`.github/workflows/tests.yml`, job `attention-check`). The absent-record condition has no rule name yet, which E-02 must supply rather than overloading this one.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `runner_shared.process_backlog_close` scoped self-check | The guard is `if len(claimants) > 1`, so it detects an item in TWO status directories and is structurally blind to an item in NONE. | `backlog_item_paths_for_id(repo, "zzzz99")` -> `[]`, length 0, guard passes silently |
| F-2 | HIGH | production, commit `ca8e22e4` | The blind shape occurred for real in this branch: ten status moves committed as ten `D` lines with no `A` lines, ten items in neither tree, repaired by `65109c8c`. | `git show --name-status ca8e22e4`: 10 `D`, 0 `A` |
| F-3 | HIGH | `check_engine` rule family, `aw attention` | NO layer catches the absent-record shape. Every integrity rule asks "is this id6 claimed more than once"; none asks "is it claimed at all". So the duplicate shape has two detectors and the absent shape has zero. | `aw check backlog --agent` on this tree reports only `check.name-nonconformant` x3 and `check.collisions-not-checked` |
| F-4 | HIGH (scope) | `runner_shared` | Recommendation (iii) is ABSENT: no startup consultation of the cross-tree view exists. The only "board is NOT authoritative" text is inside the post-close check, i.e. after a write rather than before a run. | grep of the runner for a startup attention/check consultation returns nothing |
| F-5 | MED (narrowing) | `runner_shared.process_backlog_close` | Recommendation (i) IS BUILT and well designed (three report destinations, never raises, scoped to the written id6). This plan extends it rather than building it, so an executor must not re-implement it. | the "SCOPED INTEGRITY SELF-CHECK, IMMEDIATELY AFTER OUR OWN WRITE (2026-09-22)" block |

## Proposed changes (ordered, validatable)

1. E-01 re-measures all three recommendations and proves the zero-claimant blind spot at the executing HEAD.
2. E-02 adds the zero-claimant branch to the existing self-check, under its own rule name, preserving report-never-raise.
3. E-03 adds the startup invalid-board report on both hosts through one shared implementation, before durable state, non-fatal.
4. E-04 covers the zero case, the healthy-close silence, and the startup report's position.

## Deferred / out of scope (with reason)

- RECOMMENDATION (ii), THE OPT-IN PRE-COMMIT HOOK (OQ-01). The item calls it "defensible" and immediately states its limits: local hooks are not cloned by default and are `--no-verify`-skippable, so the portable authority stays the `aw check` rule plus CI. Deferred rather than refused.
- THE COMMIT-PATH CAUSE of the absent-record shape. That is `hv9gar`'s (`movehalf`) subject; this plan is detection only, and changing `offer_commit` here would collide with it.
- MAKING THE CI GATE LOUDER. The item explicitly forbids it: the gate "was already correct, already fail-closed, and already red". Nothing here touches CI.
- RE-IMPLEMENTING RECOMMENDATION (i). F-5: it is built; E-02 extends it.
- A GENERAL "EVERY RECORD TYPE MUST BE CLAIMED EXACTLY ONCE" CHECK RULE. That is the portable counterpart to F-3 and is a broader change than this plan's runner-scoped fix; it belongs with the `check_engine` rule family and should be carried by a SUCCESSOR PLAN rather than a backlog item, since F-3 already measures the gap (every integrity rule asks whether an id6 is claimed more than once; none asks whether it is claimed at all) and what is missing is the reviewed rule design.

## Scope check

- Over-scope: `runner_shared.py` is in scope ONLY for the zero-claimant branch (E-02) and the startup report (E-03). Do not alter the existing duplicate branch's behavior, its three destinations, or `backlog_item_paths_for_id`'s query semantics.
- Under-scope: if E-03's shared implementation cannot avoid touching the two host driver modules to reach the pre-flight seam, declare those files in `- Scope-Paths:` before editing them rather than widening scope at finalize.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_runner_backlog_close.py` and the host driver test module touched by E-03.
- E-04's zero-case test must be demonstrated FAILING against pre-E-02 code and passing after; given F-1 shipped uncovered, a test that never failed proves nothing.
- The healthy-close case must be shown still SILENT, so the new branch is not a false positive on every close.

## Spec / documentation sync

- The self-check block's comment explains why it exists and what it catches; E-02 must extend that prose to cover the zero case, since the current text implies the duplicate shape is the whole risk.
- If the startup report of E-03 constitutes a documented run behavior, check whether spec `25kzda` (the run contract) should record it, and declare that `.spec.md` in `- Scope-Paths:` before editing per the spec-amendment rule. No spec edit is anticipated for E-02.

## Open questions

### OQ-01: Should recommendation (ii), the opt-in staged-path duplicate hook, be built here?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: NOT blocking; this plan delivers (i)-extended and (iii), which is what `4y7nzh` actually recommends ("(i) plus (iii)"), so it terminates correctly without (ii). The case FOR is that it catches the hand-edit bypass, where someone stages a corrupt pair directly instead of going through a setter, which neither (i) nor (iii) sees because both are runner-scoped. The case AGAINST is stated by the item itself: a local hook is not cloned, is skippable with `--no-verify`, and would be the fifth opt-in hook nobody has installed, so it adds a maintenance surface with no portable authority. Escalated to the maintainer because four such hooks already exist and whether to add a fifth is a policy call about local-versus-CI enforcement, not an implementation detail.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the shipped guard quoted verbatim; pasted output showing `backlog_item_paths_for_id` returns an empty list for an absent id6; pasted `aw check backlog --agent` and `aw attention --check --agent` confirming neither reports the absent-record shape; a statement that (iii) is still absent.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: a fixture close whose destination never reaches the commit, with the resulting report pasted from all three destinations (item record, `events.jsonl`, stderr), under a rule name distinct from `attention.duplicate-id`, and proof the run did not fail.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted startup output from BOTH hosts on a repository whose view is invalid, naming the outstanding rule ids, shown to appear before the run directory exists; plus a case where computing the view fails, showing a warning rather than a raise.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: the new tests pasted FAILING against pre-E-02/E-03 code and PASSING after; the healthy-close case shown silent; the startup-report ordering assertion shown to fail if the report is moved after run-directory creation; plus the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
