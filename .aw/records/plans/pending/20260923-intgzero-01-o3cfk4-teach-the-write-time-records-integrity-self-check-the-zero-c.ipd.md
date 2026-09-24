# IPD: Teach the write-time records integrity self-check the zero-claimant case it is blind to, and tell a run at startup when the board it is about to work from is already invalid

- Date: 2026-09-23
- Kind: child
- Concern: BACKLOG `4y7nzh` MAKES THREE RECOMMENDATIONS AND RECOMMENDS "(i) PLUS (iii)". MEASURED AT HEAD `22cf67d9`: (i) IS BUILT, (iii) IS NOT, AND (i) HAS A HOLE ITS AUTHOR DID NOT ANTICIPATE. The item asks the runner to "assert record integrity for the ids it touched immediately after its own commit". That shipped: `runner_shared.process_backlog_close` carries a "SCOPED INTEGRITY SELF-CHECK, IMMEDIATELY AFTER OUR OWN WRITE (2026-09-22)" block that calls `backlog_item_paths_for_id`, and on a violation writes the fact into the item's `backlog_close` record, the run's `events.jsonl`, and stderr. Its design is right and this plan does not relitigate it.
  THE HOLE IS THE PREDICATE: `if len(claimants) > 1`. It detects an item existing in TWO status directories and is STRUCTURALLY BLIND to an item existing in NONE. Verified live: `backlog_item_paths_for_id(repo, "zzzz99")` returns `[]`, length 0, which the guard passes silently. So the check catches the duplicate shape and misses the absent shape.
  REVIEW CORRECTION (2026-09-24), AND IT IS THE DECIDING FACT OF THIS PLAN: THE PREDICATE IS NOT THE ONLY HOLE, AND COUNTING CLAIMANTS DIFFERENTLY CANNOT CLOSE EITHER SHAPE. `backlog_item_paths_for_id` walks `backlog._iter_items`, which globs the FILESYSTEM, so it answers a question about the WORKING TREE. Both corruption shapes are properties of the COMMIT: a half-committed `git mv` leaves the working tree perfectly correct (exactly one file, in the right directory) while HEAD holds two copies or none. Measured on both shapes in a throwaway git fixture: addition-only commit -> working-tree claimants 1, committed claimants 2; deletion-only commit -> working-tree claimants 1, committed claimants 0. In BOTH, `len > 1` is False and `len == 0` is also False. So the shipped duplicate branch cannot fire on the 36-item corruption it was written for, and the zero branch this plan proposed could not fire on `ca8e22e4` either. See F-6 and F-7; E-02 is redesigned to ask the COMMITTED-tree question, which is the only version of the check that can observe either failure.
  THAT MISSED SHAPE IS NOT HYPOTHETICAL, AND IT HAPPENED IN THIS BRANCH WHILE GRADUATING THE ITEM NEXT DOOR. Commit `ca8e22e4` committed ten backlog status moves as ten `D open/...` lines with NO `A done/...` lines (destinations were left staged-but-uncommitted because directory arguments did not expand). At that commit ten items existed in NEITHER COMMITTED tree, which a fresh checkout of `ca8e22e4` proves (no `.aw/records/backlog` directory at all). Repaired by `65109c8c`; the commit-path cause is graduated as `hv9gar` (`movehalf`). This plan owns the DETECTION half.
  THE ASYMMETRY IS REAL BUT NARROWER THAN FIRST WRITTEN, corrected in review so the executor does not build a rule that already exists. The absent shape is NOT caught by "NOTHING at any layer": `check.from-backlog-dangling` (severity `error`) fires whenever a plan or spec carries `- From-Backlog: <id6>` that resolves to no item, which is exactly what a vanished item produces for any item that had been graduated. Verified on the real occurrence: the plan committed IN `ca8e22e4` carries `- From-Backlog: 8pcdoa`, and `8pcdoa` was one of the ten items that commit deleted, so that rule WOULD have fired on this very corruption. What is genuinely missing is narrower and still worth closing: an item with no surviving `From-Backlog` referrer (an `open` item never graduated, and any item at the moment the runner writes it) vanishes UNREPORTED, and no rule asks the direct question "is this id6 claimed at all". That is the gap E-02 closes.
  AND (iii) IS GENUINELY ABSENT, WHICH IS THE ITEM'S OTHER RECOMMENDED HALF. Grepping the runner for a startup consultation of the cross-tree view returns nothing; the only "board is NOT authoritative" string is inside the post-close self-check quoted above, i.e. it fires AFTER a close rather than BEFORE a run. The measured failure `4y7nzh` describes is precisely a run proceeding for two days on top of a board that was already invalid, so a startup report is the half that addresses the two-day blindness rather than the per-write moment.
- Scope: Close the detection gaps `4y7nzh` names, at the two layers it recommends. IN: (a) make the write-time self-check ask the COMMITTED-tree claimant question and report BOTH broken counts (0 and >1) from it, keeping its report-never-raise discipline (REVISED in review per F-6: the authored scope was "report the ZERO-claimant case as well as the many-claimant case" against the existing working-tree query, which cannot observe either corruption); (b) add the startup report of recommendation (iii), so a run tells the operator BEFORE spawning anything that the cross-tree view is currently invalid and names the offending rule ids; (c) tests for both, including the zero case that has no coverage anywhere. OUT: recommendation (ii)'s opt-in pre-commit hook, deferred per OQ-01 because the item itself calls it "defensible" while noting local hooks are uncloned and `--no-verify`-skippable; the commit-path CAUSE of the absent-record shape, which is `hv9gar`'s (`movehalf`) subject, so this plan must not also change `offer_commit`; and making the CI gate louder, which the item explicitly forbids ("DO NOT fix this by making the CI gate louder alone: the gate was already correct, already fail-closed, and already red").
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_runner_backlog_close.py, tests/test_oc_runipd.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Set: intgzero
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: o3cfk4
- Approval: 2026-09-24, recorded via aw ipd set: status set to approved
- From-Backlog: 4y7nzh
- Blocks-Release: next

## Workflow history
- 2026-09-24 approved (aw set): status set to approved
- 2026-09-24 reviewed (aw set): status set to reviewed

- 2026-09-24 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009, all FIXED. Findings recorded in `.aw/records/reviews/20260923-intgzero-01-o3cfk4-...review.md` Round 1. Structural lint `conforming` at `author` before review and at `review-finalize` after.
  THE PLAN'S OWN FIX WAS FALSIFIED BY MEASUREMENT AND E-02 IS REDESIGNED (PR-001, now F-6). The plan was right that the shipped guard is `len(claimants) > 1` and blind to zero, but the defect is one layer deeper: `backlog_item_paths_for_id` globs the FILESYSTEM via `backlog._iter_items`, so it describes the WORKING TREE, while both corruption shapes are properties of the COMMIT. Measured in git fixtures: addition-only -> working-tree 1 / committed 2; deletion-only -> working-tree 1 / committed 0, with `len > 1` and the proposed `len == 0` BOTH False in BOTH. So the shipped duplicate branch has never been able to fire on the 36-item corruption it cites, and the authored zero branch could not have fired on `ca8e22e4`. E-02 now asks the COMMITTED-tree question and reports both broken counts.
  AND THE EXISTING TESTS WOULD HAVE HIDDEN THAT (PR-002, F-7): `BacklogCloseIntegritySelfCheck` uses no `git init` at all, so a new test in the same style would have gone green against a still-blind check. E-04 now requires real commits and a fail-first demonstration.
  THREE MEASURED FALSE-POSITIVE RISKS CLOSED BEFORE THEY SHIPPED: validity must come from `drift_exit_code`, not raw finding count, because `attention.lane-superseded` is `info` by design (PR-004, F-8; live: 8 findings, 4 `info`); the committed-tree check must skip silently when there is no commit sha, which is the DEFAULT isolated path (PR-005, F-9); and E-03's ~4.8s view computation must be measured rather than assumed (PR-007).
  ONE OF THE PLAN'S OWN FINDINGS WAS OVERSTATED AND IS CORRECTED RATHER THAN DELETED (PR-003): F-3 claimed nothing catches the absent shape, but `check.from-backlog-dangling` (`error`) would have fired on `ca8e22e4`, since the plan committed there carries `- From-Backlog: 8pcdoa` and `8pcdoa` was one of the ten deleted items. F-3 is downgraded to MEDIUM and re-scoped to the genuinely uncovered cases.
  OQ-01 LEFT OPEN DELIBERATELY: it is `- Blocking: no` and a maintainer policy call (whether to add a fifth opt-in local hook), so it does not gate readiness. Readiness is `go-pending-approval`: no unfixed BLOCKER or HIGH, no blocking open question, awaiting human sign-off only.
- 2026-09-23 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): Graduated from backlog `4y7nzh`, NARROWED by measuring which of its three recommendations already exist. (i) is BUILT (the 2026-09-22 scoped self-check in `process_backlog_close`); (iii) is ABSENT; (ii) is deferred to OQ-01 on the item's own hedge about local hooks. `- Blocks-Release: next` is INHERITED from `4y7nzh`.
  THE FINDING THAT JUSTIFIES A PLAN RATHER THAN A CLOSE is that the shipped (i) tests `len(claimants) > 1` and is therefore blind to `len == 0`. Verified live (`[]`, length 0, passes). I then hit that exact shape for real in this branch at `ca8e22e4`, ten items in neither tree, so the blind spot has a measured occurrence and not merely a theoretical one.
  I DELIBERATELY SPLIT CAUSE FROM DETECTION. `hv9gar` (`movehalf`, from `mx1b4v`) owns the commit-path cause that produced `ca8e22e4`; this plan owns detection only. Both are needed: fixing the gateway stops the known route, while the zero-claimant check catches any future route, and neither subsumes the other.

## Goal

Make the runner's post-close integrity check ask the COMMITTED tree whether the item it just wrote is claimed exactly once, so both a vanished record and a duplicated one are loud at the moment of creation, and tell a run at startup when the board it is about to work from is already invalid.

REVISED IN REVIEW. The pre-review goal was "make a zero-claimant write as loud as a two-claimant one". That framing accepted the shipped check's query as correct and treated only its predicate as broken. F-6 shows the query is the deeper defect: it reads the working tree, where NEITHER corruption is visible, so the check as shipped cannot fire on the 36-item incident and the authored fix could not have fired on `ca8e22e4`. Counting claimants correctly in the wrong tree closes nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

#### Task group 1: confirm which recommendations already exist

- [x] E-01 RE-MEASURE THE CHECK'S TWO INDEPENDENT DEFECTS BEFORE WRITING ANYTHING, because E-02's redesign rests on the SECOND one, which the pre-review plan did not know about.
  CONFIRM (i) EXISTS AND FIND ITS PREDICATE: locate the scoped integrity self-check in `runner_shared.process_backlog_close` and quote the guard. At review it is `if len(claimants) > 1`.
  PROVE DEFECT 1, THE PREDICATE: call `backlog_item_paths_for_id` with an id6 that exists nowhere and show it returns an empty list, so a `len > 1` guard cannot fire. Paste it.
  PROVE DEFECT 2, THE TREE, WHICH IS THE ONE THAT DECIDES THE DESIGN. Confirm `backlog_item_paths_for_id` reads the FILESYSTEM (it iterates `backlog._iter_items`, which globs status directories) and therefore answers about the WORKING TREE, not the commit. Then build a throwaway git fixture and measure BOTH corruption shapes: commit a `git mv` addition-only, and commit one deletion-only. For each, paste the working-tree claimant count beside the committed (`git ls-tree -r HEAD`) claimant count. The expected result, measured in review, is that the working tree reads exactly 1 in BOTH shapes while HEAD reads 2 and 0 respectively, so `len > 1` AND `len == 0` are both False in both. If your measurement disagrees, STOP and report: E-02's redesign is wrong and the plan needs re-review.
  CONFIRM (iii) IS STILL ABSENT: grep the runner for any startup consultation of the cross-tree attention view. At review, the only "board is NOT authoritative" text is inside the post-close check, not at startup.
  MEASURE WHAT ALREADY CATCHES THE ABSENT SHAPE, rather than assuming nothing does. Run `aw check backlog --agent` and `aw attention --check --agent`. Then confirm the specific partial detector review found: `check.from-backlog-dangling` is an `error` rule that fires when a plan or spec's `- From-Backlog:` resolves to no item, so it catches a vanished item that HAS a referrer. State plainly which absent-item cases remain uncovered (an item with no referrer, and the write-time moment), because those are the only ones E-02 may claim to close.
  - Depends on: none
  - Expected outcome: the shipped predicate quoted; the working-tree-versus-commit defect proved with a pasted two-shape measurement showing both guards False; (iii) confirmed absent; and an explicit statement of which absent-item cases `check.from-backlog-dangling` already covers and which remain. Any divergence from the review measurement reported as a STOP.
  - Execution state: performed

### Task group 2: close the zero-claimant blind spot

- [x] E-02 MAKE THE WRITE-TIME SELF-CHECK ASK THE COMMITTED-TREE QUESTION, AND REPORT BOTH BROKEN COUNTS FROM IT. This supersedes the pre-review wording, which proposed only adding a `len == 0` branch to the existing working-tree query; E-01's second measurement shows that branch could not fire on the failure it cites, so adding it alone would ship a second check as blind as the first.
  THE CHANGE IN ONE SENTENCE: after the close commit, count the files claiming this id6 IN THE COMMIT the runner just made, and report when that count is not exactly 1 (both 0 and >1).
  ADD A CLAIMANT QUERY THAT READS A COMMIT, DO NOT REPURPOSE THE EXISTING ONE. `backlog_item_paths_for_id` is used elsewhere and its working-tree semantics are pinned by existing tests (`tests/test_runner_backlog_close.py`, `BacklogCloseIntegritySelfCheck`), and this plan's scope check forbids changing its query semantics. Add a sibling that enumerates the committed tree (e.g. `git ls-tree -r --name-only <sha>` filtered to the backlog status directories, parsing each blob's `- Id:`, reusing `backlog.parse_item` and the `BACKLOG_ROOTS`/`STATUS_DIRS` constants rather than a hand-written path list, so a layout change cannot desynchronize the two). Both hosts must resolve to ONE object, as `test_both_drivers_share_ONE_implementation` requires of its sibling.
  KEEP THE WORKING-TREE BRANCH TOO, AND SAY WHY IN THE CODE. The two queries catch different things: a working-tree duplicate is a dirty checkout an operator must clean, while a committed miscount is corruption that will propagate through a push. Report them as SEPARATE conditions rather than merging them, so neither masks the other.
  KEEP THE EXISTING DISCIPLINE EXACTLY. The shipped block's docstring is explicit that it REPORTS AND NEVER RAISES, because "the close is already committed by this point, so refusing would leave the tree in exactly the same state while additionally killing the run". That reasoning applies identically here. Keep the `contextlib.suppress(Exception)` wrapper and the three destinations (the item's `backlog_close` record, `events.jsonl`, stderr).
  HANDLE THE NO-COMMIT CASE EXPLICITLY AND SILENTLY. `commit_backlog_close` returns None when nothing was committed, and on an ISOLATED turn the move rides the lane's own finalize commit rather than a commit made here, so there is frequently no sha to inspect. With no sha, the committed-tree check MUST be skipped without reporting: a "0 claimants" report derived from having no commit to look at would be a false positive on the normal isolated path, which is the default. Record that reasoning in the code, since it is the single most likely way this check becomes noise and gets ignored.
  DO NOT REUSE `attention.duplicate-id` FOR THE NEW CONDITIONS. A record that exists nowhere is not a duplicate identity, and a committed miscount is not the same fact as a working-tree one. Choose distinct names and use each consistently across all three destinations, so a reader grepping run events can tell the three situations apart.
  SAY WHAT A READER SHOULD DO. Each message carries the item's id6, the count actually observed, the sha inspected when there is one, and the remedy: for 0, that the destination write was probably dropped from the commit; for >1, that a pre-move copy probably survived beside its destination.
  - Depends on: E-01
  - Expected outcome: after a close whose commit leaves the id6 claimed 0 or >1 times IN THAT COMMIT, the fact is reported in all three destinations under a rule name distinct from `attention.duplicate-id` and distinct per condition; a close with no commit sha reports nothing; a healthy close reports nothing; the existing working-tree duplicate branch and `backlog_item_paths_for_id`'s semantics are unchanged; the check still never raises and never fails the run; both hosts share one implementation.
  - Execution state: performed

### Task group 3: recommendation (iii), the startup report

- [x] E-03 TELL A RUN AT STARTUP THAT THE BOARD IS ALREADY INVALID, naming the rule ids. This is `4y7nzh`'s recommendation (iii) and the half that addresses the measured two-day blindness, as opposed to the per-write moment (i) covers.
  REPORT, DO NOT REFUSE. The item asks to "have `aw oc run`/`aw agy run` report at startup that the cross-tree view is currently INVALID and name the rule ids, so an operator or agent is told before spending a night's compute on top of a known-broken board", and explicitly prefers this over "adding a new refusal that could wedge a commit". A run must still start.
  PUT IT BEFORE DURABLE STATE EXISTS. The pre-flight region where the other gates run is the right seam, i.e. before the run directory is created, so the operator sees it with the other startup facts rather than buried mid-run.
  CONSUME THE EXISTING VIEW, DO NOT FORK A SECOND ONE. `aw attention --check` already computes this and CI already consumes it; call the same authority rather than writing a second integrity walk, or the two will disagree about what "invalid" means. Reuse the in-process functions and `artifact_core.drift_exit_code` (which is what defines validity, exempting exactly `info` severity) rather than shelling out to the CLI and parsing its text.
  RESPECT THE `info` EXEMPTION, OR THE REPORT IS WRONG ON ITS FIRST DAY. Validity is `drift_exit_code(drift) == 0`, NOT `len(drift) == 0`; `attention.lane-superseded` is graded `info` deliberately so it reports without failing the gate. Measured on this tree during review: 8 lane findings, of which 4 are `info`. A report that counted raw findings would announce an invalid board on a tree the gate calls valid.
  SITE IT BESIDE `report_untracked_dirt_at_run_start` in `initialize_run_core`, which is the established run-start reporting seam: it is already before the run directory exists, already once-per-run (not once per queue item), and already documented as never raising. Do not invent a second seam.
  DO NOT ADD A SECOND SUBPROCESS-HEAVY WALK WITHOUT KNOWING ITS COST. Measured in review, `aw attention --check --agent` takes roughly 4.8s wall on this repository. That is paid once per run and is defensible against a night's compute, but MEASURE the in-process cost you actually add and paste it; if it exceeds a few seconds, report it rather than silently making every run start slower, since a user-perceptible slowdown is itself a `bug` by this repository's policy.
  IT MUST NOT BE ABLE TO BREAK A RUN. Wrap it so a failure to COMPUTE the view degrades to a warning, on the same reasoning the existing self-check uses: a diagnostic that can kill a run is worse than the blindness it cures. A repository with no records trees must produce silence, not a spurious warning.
  SAY WHAT IS WRONG, NOT MERELY THAT SOMETHING IS. Name the outstanding rule ids and their count; an operator who is told only "the board is invalid" cannot act, and a message that fires often without being actionable is the "trains people to ignore the rule" failure `4y7nzh` itself warns about.
  LAND IT ON BOTH HOSTS THROUGH ONE IMPLEMENTATION, sited in `runner_shared`, never in `oc_runipd` for `agy_runipd` to import.
  - Depends on: E-01
  - Expected outcome: both hosts report at startup, before the run directory exists, that the cross-tree view is invalid and which rule ids are outstanding; validity is computed through `drift_exit_code` so an `info`-only tree stays SILENT; the run still starts; a failure to compute the view warns instead of raising; a records-free repository is silent; the added startup cost is measured and pasted; one shared implementation.
  - Execution state: performed

### Task group 4: cover both

- [x] E-04 TEST BOTH COMMITTED-TREE MISCOUNTS AND THE STARTUP REPORT, from REAL GIT FIXTURES. Neither committed-tree shape has coverage anywhere today, which is why the shipped check could not fire on the corruption it was written for.
  THE FIXTURES MUST BE REAL COMMITS, NOT JUST FILES ON DISK. This is the specific inadequacy of the existing `BacklogCloseIntegritySelfCheck` tests: they write files into a `tempfile` directory with no git repository at all, so they can only ever exercise the working-tree query and would pass unchanged against a check that is blind to every real corruption. Each new fixture must `git init`, commit an item, `git mv` it, and then commit ONE SIDE of that move.
  COVER BOTH BROKEN COUNTS: deletion-only (committed claimants 0) and addition-only (committed claimants 2). Assert the report appears in all three destinations and that the run did NOT fail. Assert each condition's rule name is distinct from the other and from `attention.duplicate-id`.
  ASSERT THE EXACTLY-ONE CASE STAYS SILENT, so the new branch cannot become a false positive on every healthy close. This is the cheap guard that keeps the check trustworthy.
  ASSERT THE NO-SHA CASE IS SILENT, which is the isolated-turn default path. A check that reports "0 claimants" merely because there was no commit to inspect would fire on almost every normal run.
  FOR E-03, ASSERT THREE THINGS: that the report is emitted BEFORE the run directory exists (a test that only checks the text appears somewhere would pass against a report printed too late to help); that an `info`-only drift set produces SILENCE (the false-positive guard for the `drift_exit_code` requirement); and that a view-computation failure warns rather than raising.
  - Depends on: E-02, E-03
  - Expected outcome: tests failing against pre-E-02/E-03 code and passing after, covering both committed-tree miscounts from real git fixtures, the healthy close staying silent, the no-sha close staying silent, the startup report's position before durable state, the `info`-only silence, and the compute-failure warning.
  - Execution state: performed

## Project conventions discovered (Step 0)

- THE WRITE-TIME SELF-CHECK REPORTS AND NEVER RAISES, and its own comment gives the reason: the close is already committed, so refusing changes nothing about the tree and only kills the run. Any new branch added to it inherits that contract.
- THE RUNNER ALREADY KNOWS WHICH id6 IT WROTE, which is why a SCOPED check (one id6, one tree walk) is the cheap remedy rather than a whole-tree validation on every write.
- A RECORD'S LIFECYCLE STATE IS ITS DIRECTORY, so "claimed exactly once" is the integrity invariant, and the tree you ask that question OF is part of the invariant. The corruption class this family addresses is produced by COMMITS, so the committed tree is the authoritative one (F-6).
- VALIDITY IS `drift_exit_code(drift) == 0`, NOT `len(drift) == 0`. `info`-severity findings are advisory and deliberately do not fail the gate (`attention.lane-superseded`). Any new consumer of the cross-tree view must use the shared predicate, or it will disagree with CI about what "invalid" means (F-8).
- `attention.duplicate-id` IS THE EXISTING RULE for one id6 in two status directories, consumed by `aw attention --check` and wired fail-closed in CI (`.github/workflows/tests.yml`, job `attention-check`). The absent-record condition has no rule name yet, which E-02 must supply rather than overloading this one.
- `check.from-backlog-dangling` ALREADY PARTIALLY COVERS A VANISHED ITEM, via the referrer rather than the item, so E-02 must claim only the cases it genuinely adds (F-3).
- `report_untracked_dirt_at_run_start` IS THE ESTABLISHED RUN-START REPORTING SEAM in `initialize_run_core`: once per run, before the run directory exists, never raises. E-03 belongs beside it rather than in a new seam.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | BLOCKER | `runner_shared.process_backlog_close` scoped self-check | The guard is `if len(claimants) > 1`, so it detects an item in TWO status directories and is structurally blind to an item in NONE. | `backlog_item_paths_for_id(repo, "zzzz99")` -> `[]`, length 0, guard passes silently |
| F-2 | HIGH | production, commit `ca8e22e4` | The blind shape occurred for real in this branch: ten status moves committed as ten `D` lines with no `A` lines, ten items in neither COMMITTED tree, repaired by `65109c8c`. | `git show --name-status ca8e22e4`: 10 `D`, 0 `A`; a fresh checkout of that sha has no `.aw/records/backlog` directory |
| F-3 | MEDIUM (corrected in review; was HIGH) | `check_engine` rule family, `aw attention` | PARTIALLY WRONG AS AUTHORED. The absent shape is not undetected everywhere: `check.from-backlog-dangling` (`error`) fires on any plan/spec whose `- From-Backlog:` resolves to no item, which a vanished graduated item produces. It WOULD have fired on `ca8e22e4`. The real gap is narrower: an item with no referrer, and the write-time moment. | `check_engine.py` rule table, `check.from-backlog-dangling` severity `error`; the plan committed in `ca8e22e4` carries `- From-Backlog: 8pcdoa`, and `8pcdoa` is one of the ten items that commit deleted |
| F-4 | HIGH (scope) | `runner_shared` | Recommendation (iii) is ABSENT: no startup consultation of the cross-tree view exists. The only "board is NOT authoritative" text is inside the post-close check, i.e. after a write rather than before a run. | grep of the runner for a startup attention/check consultation returns nothing |
| F-5 | MED (narrowing) | `runner_shared.process_backlog_close` | Recommendation (i) IS BUILT (three report destinations, never raises, scoped to the written id6). Its REPORTING design is sound and is reused; its QUERY is not (F-6). An executor must not re-implement the reporting shape. | the "SCOPED INTEGRITY SELF-CHECK, IMMEDIATELY AFTER OUR OWN WRITE (2026-09-22)" block |
| F-6 | BLOCKER (found in review) | `runner_shared.backlog_item_paths_for_id`, consumed by the self-check | THE CHECK ASKS THE WRONG TREE, which is a deeper defect than its predicate and invalidates this plan's original E-02. The query globs the FILESYSTEM via `backlog._iter_items`, so it describes the WORKING TREE, while both corruption shapes are properties of the COMMIT. A half-committed `git mv` leaves the working tree correct. Measured both shapes: addition-only -> working-tree 1, committed 2; deletion-only -> working-tree 1, committed 0. `len > 1` is False in both, and the proposed `len == 0` is also False in both. So the shipped duplicate branch cannot fire on the 36-item corruption, and the authored zero branch could not have fired on `ca8e22e4`. | `backlog._iter_items` uses `d.glob("*.md")`; throwaway git fixture, both shapes, counts as stated |
| F-7 | HIGH (found in review) | `tests/test_runner_backlog_close.py`, `BacklogCloseIntegritySelfCheck` | THE EXISTING TESTS CANNOT DETECT F-6 AND MASK IT. Every case writes files into a `tempfile` directory with NO git repository, so they assert only the working-tree query. `test_two_claimants_are_detected_which_is_the_36_item_corruption` names the real corruption but constructs a shape that commit never produced, so it passes against a check blind to every real occurrence. E-04 must use real commits. | the class's `_repo` helper creates plain directories; no `git init` anywhere in the class |
| F-8 | HIGH (found in review) | E-03 as authored | A startup report computing validity as "any findings" would be WRONG IMMEDIATELY. `artifact_core.drift_exit_code` exempts `info` severity, and `attention.lane-superseded` is graded `info` on purpose. Measured on this tree: 8 lane findings, 4 of them `info`, so a raw-count report announces an invalid board on a tree the gate calls valid. | `attention.lane_drift_severity` docstring; `drift_exit_code` returns 1 only for non-`info`; live: 8 drift, 4 `info` |
| F-9 | HIGH (found in review) | E-02, isolated-turn path | A committed-tree check must SKIP when there is no commit sha. `commit_backlog_close` returns None when nothing was committed, and an ISOLATED turn (the DEFAULT) has its move swept into the lane's finalize commit instead, so a naive "0 committed claimants" report would fire on the normal path and train operators to ignore it. | `commit_backlog_close` docstring: "Returns the new commit sha, or None when nothing was committed"; "AN ISOLATED TURN NO LONGER CALLS IT" |

## Proposed changes (ordered, validatable)

1. E-01 re-measures the check's TWO defects at the executing HEAD: the predicate blind spot, and (decisively) the working-tree-versus-commit defect that determines E-02's design. It also measures what `check.from-backlog-dangling` already covers.
2. E-02 adds a committed-tree claimant query and reports both broken counts (0 and >1) from it, under distinct rule names, skipping silently when there is no commit sha, preserving report-never-raise and leaving the existing working-tree query's semantics untouched.
3. E-03 adds the startup invalid-board report on both hosts through one shared implementation, sited beside `report_untracked_dirt_at_run_start`, computing validity through `drift_exit_code` so `info` findings stay silent, before durable state, non-fatal.
4. E-04 covers both committed-tree miscounts from REAL git fixtures, the healthy-close and no-sha silences, the startup report's position, the `info`-only silence, and the compute-failure warning.

## Deferred / out of scope (with reason)

- RECOMMENDATION (ii), THE OPT-IN PRE-COMMIT HOOK (OQ-01). The item calls it "defensible" and immediately states its limits: local hooks are not cloned by default and are `--no-verify`-skippable, so the portable authority stays the `aw check` rule plus CI. Deferred rather than refused.
  - Carrier: 4y7nzh
- THE COMMIT-PATH CAUSE of the absent-record shape. That is `hv9gar`'s (`movehalf`) subject; this plan is detection only, and changing `offer_commit` here would collide with it.
  - Carrier: hv9gar
- MAKING THE CI GATE LOUDER. The item explicitly forbids it: the gate "was already correct, already fail-closed, and already red". Nothing here touches CI.
  - Carrier-Declined: a REFUSED alternative, not an outstanding obligation. The backlog item rules it out explicitly, so there is nothing for a future artifact to carry.
- RE-IMPLEMENTING RECOMMENDATION (i)'s REPORTING SHAPE. F-5: the three-destination, never-raises reporting design is built and is REUSED. Only its QUERY changes (F-6).
  - Carrier-Declined: already shipped and reused by E-02, so nothing remains outstanding.
- A GENERAL "EVERY RECORD TYPE MUST BE CLAIMED EXACTLY ONCE" CHECK RULE, and the portable committed-tree version of it. This is the portable counterpart to F-3/F-6 and is a broader change than this plan's runner-scoped fix; it belongs with the `check_engine` rule family and should be carried by a SUCCESSOR PLAN rather than a backlog item, since the gap is already measured and what is missing is the reviewed rule design. Note the scope correction from review: the portable gap is NOT "nothing detects an absent record" (F-3, `check.from-backlog-dangling` covers the referrer case) but "no rule asks the claimed-exactly-once question directly, and no rule asks it of the committed tree".
  - Carrier: 4y7nzh
- RE-EXAMINING WHETHER `aw attention`'s OWN `duplicate-id` RULE READS THE RIGHT TREE. F-6 concerns the RUNNER's query. Whether the portable `check_engine`/`attention` rules share the same working-tree assumption was NOT measured in this review and is not in scope; it belongs to the successor plan above. Flagged rather than silently assumed either way, because if they do, the CI gate's own reach is narrower than believed, and that is a bigger finding than this plan.
  - Carrier: 4y7nzh

## Scope check

- Over-scope: `runner_shared.py` is in scope ONLY for the committed-tree claimant query and its reporting branches (E-02) and the startup report (E-03). Do not alter the existing working-tree duplicate branch's behavior, its three destinations, or `backlog_item_paths_for_id`'s query semantics: F-6 is fixed by ADDING a committed-tree query beside it, not by changing that function, whose working-tree contract is pinned by existing tests.
- Under-scope: if E-03's shared implementation cannot avoid touching the two host driver modules to reach the pre-flight seam, declare those files in `- Scope-Paths:` before editing them rather than widening scope at finalize. Siting E-03 beside `report_untracked_dirt_at_run_start` inside `initialize_run_core` should require NO host-module edit, since both hosts already delegate there; if you find otherwise, say so.
- Deliberately NOT widened: F-6 means the shipped `attention.duplicate-id` write-time branch has never been able to fire on its motivating incident. Fixing that is exactly what E-02's committed-tree query does, so no separate corrective plan is needed for it; but do NOT also rewrite the working-tree branch or the portable `check_engine` rule family here (see the deferral below).
- Test-file scope: `tests/test_runner_backlog_close.py` is in scope for ADDING real-git fixtures. Per F-7 its existing no-git cases are inadequate but not WRONG about the working-tree query, so leave them in place rather than deleting them; deleting a passing test to replace it is how coverage silently shrinks.

## Required tests / validation

- `python3 -m pytest` bare, per the execution contract, with the actual summary line pasted.
- Targeted: `tests/test_runner_backlog_close.py` and the host driver test module touched by E-03.
- E-04's committed-tree tests must be demonstrated FAILING against pre-E-02 code and passing after; given F-1 and F-6 both shipped uncovered, a test that never failed proves nothing. Per F-7 this specifically means the fixture must use real commits: a new test that passes against the CURRENT code has reproduced the existing blind spot rather than the defect.
- The healthy-close case must be shown still SILENT, so the new branch is not a false positive on every close. The NO-SHA case must also be shown silent (F-9), since that is the default isolated path and the likeliest source of noise.
- E-03 must be shown silent on a tree whose only findings are `info` severity (F-8), and warning (not raising) when the view cannot be computed.
- The pre-existing `BacklogCloseIntegritySelfCheck` cases must still pass unchanged, proving `backlog_item_paths_for_id`'s working-tree semantics were not altered.
- `aw sanitize --agent` must be run and pasted: this change adds new message strings carrying repository paths and a commit sha to stderr and the run ledger, which is exactly the surface the leak sanitizer scans.

## Spec / documentation sync

- The self-check block's comment explains why it exists and what it catches, and it is now MISLEADING: it claims to catch the 36-item `_staged_paths` corruption, which F-6 shows its working-tree query cannot observe. E-02 must correct that prose, not merely extend it. Record both the committed-tree reasoning and the no-sha skip (F-9), since the latter is the likeliest route to this check becoming noise.
- `backlog_item_paths_for_id`'s own docstring also overclaims, asserting it answers the integrity question that the duplicate incident posed. Correct it to state plainly that it describes the WORKING TREE and to point at the committed-tree sibling, so the next reader is not misled the same way.
- If the startup report of E-03 constitutes a documented run behavior, check whether spec `25kzda` (the run contract) should record it, and declare that `.spec.md` in `- Scope-Paths:` before editing per the spec-amendment rule. Note that `25kzda` already documents the sibling run-start report ("UNTRACKED content, which is reported once at run start and refuses on no path"), so a parallel sentence there is the likely shape. No spec edit is anticipated for E-02.

## Open questions

### OQ-01: Should recommendation (ii), the opt-in staged-path duplicate hook, be built here?

- Blocking: no
- Status: open
- Owner: maintainer
- Carrier: 4y7nzh
- Resolution or deferral rationale: NOT blocking; this plan delivers (i)-extended and (iii), which is what `4y7nzh` actually recommends ("(i) plus (iii)"), so it terminates correctly without (ii). The case FOR is that it catches the hand-edit bypass, where someone stages a corrupt pair directly instead of going through a setter, which neither (i) nor (iii) sees because both are runner-scoped. The case AGAINST is stated by the item itself: a local hook is not cloned, is skippable with `--no-verify`, and would be the fifth opt-in hook nobody has installed, so it adds a maintenance surface with no portable authority. Escalated to the maintainer because four such hooks already exist and whether to add a fifth is a policy call about local-versus-CI enforcement, not an implementation detail.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: the shipped guard quoted verbatim; pasted output showing `backlog_item_paths_for_id` returns an empty list for an absent id6; THE TWO-SHAPE MEASUREMENT pasted, showing for both an addition-only and a deletion-only commit the working-tree claimant count beside the committed (`git ls-tree -r HEAD`) count, and stating explicitly that `len > 1` and `len == 0` are both False in both shapes; pasted `aw check backlog --agent` and `aw attention --check --agent`; an explicit statement of which absent-item cases `check.from-backlog-dangling` already covers and which remain uncovered; a statement that (iii) is still absent. If the two-shape measurement disagrees with F-6, this V-item FAILS and the plan returns to review.
  - Observed evidence: VERIFIED. Shipped guard quoted; predicate defect proven with empty list; two-shape measurement executed and pasted confirming working-tree query is blind to both commit corruption shapes; aw check backlog and aw attention --check executed; uncovered cases stated; absence of (iii) confirmed. Detail below:
    1. Shipped guard quoted verbatim (`runner_shared.py:28141`):
       ```python
       claimants = backlog_item_paths_for_id(write_repo, item_id6)
       if len(claimants) > 1:
       ```
    2. Predicate defect 1 (absent id6 returns empty list, len > 1 cannot fire):
       ```
       backlog_item_paths_for_id(repo, 'zzzz99') -> [], len = 0
       ```
    3. Defect 2: Two-shape measurement on throwaway git fixture:
       ```
       Shape A (addition-only commit):
         Working-tree claimants (1): ['.aw/records/backlog/done/20260101-demo-01-abc123-test.backlog.md']
         Committed (HEAD) claimants (2): ['.aw/records/backlog/done/20260101-demo-01-abc123-test.backlog.md', '.aw/records/backlog/graduated/20260101-demo-01-abc123-test.backlog.md']
         Working-tree: len > 1 is False, len == 0 is False
         Committed (HEAD): len > 1 is True, len == 0 is False

       Shape B (deletion-only commit):
         Working-tree claimants (1): ['.aw/records/backlog/done/20260101-demo-01-def456-test.backlog.md']
         Committed (HEAD) claimants (0): []
         Working-tree: len > 1 is False, len == 0 is False
         Committed (HEAD): len > 1 is False, len == 0 is True
       ```
       In both corruption shapes, working-tree claimant count is 1, so `len > 1` and `len == 0` are both False in both shapes. The working tree query answers about the filesystem on disk and cannot observe either commit-level corruption.
    4. Pasted `aw check backlog --agent`:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"findings","exit":1,"verified":true,"complete":true,"target":"backlog","findings":5,"evidence":["inventory","rules"],"diagnostics":[{"location":".aw/records/backlog/open/20260920-modelvocab-01-6b9zd9-research-model-vocabulary-closed-list-refuses-new-.backlog.md","rule":"check.name-nonconformant"},{"location":".aw/records/backlog/open/20260923-promptid6-01-6tjye0-legacy-specs-missing-id-are-invisible-to-discover-.backlog.md","rule":"check.name-nonconformant"},{"location":".aw/records/backlog/open/20260924-24e5zv-01-24e5zv-citationanchoradvisorytests-asserts-citations-500-.backlog.md","rule":"check.name-nonconformant"},{"location":".aw/records/backlog/graduated/20260922-j08jky-01-j08jky-turn-bounds-permission-policy-test-fails-when-the-.backlog.md","rule":"check.name-nonconformant"},{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"run 'aw rename backlog .aw/records/backlog/open/20260920-modelvocab-01-6b9zd9-research-model-vocabulary-closed-list-refuses-new-.backlog.md' or rename to match 'YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md'."}
       ```
    5. Pasted `aw attention --check --agent`:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"attention","outcome":"findings","exit":1,"verified":true,"complete":true,"findings":11,"evidence":["attention"],"diagnostics":[{"location":".aw/records/backlog/open/20260919-wtd5m2-01-wtd5m2-seven-pending-orchestrators-carry-uncovered-work.backlog.md","rule":"attention.duplicate-id"},{"location":"aw/lane/13xo5k","rule":"attention.lane-superseded"},{"location":"aw/lane/7p3tt8","rule":"attention.lane-stranded"},{"location":"aw/lane/7p3tt8_attempt2","rule":"attention.lane-stranded"},{"location":"aw/lane/bxx9af","rule":"attention.lane-superseded"},{"location":"aw/lane/lkexaw","rule":"attention.lane-stranded"},{"location":"aw/lane/lkexaw_attempt2","rule":"attention.lane-stranded"},{"location":"aw/lane/lkexaw_attempt3","rule":"attention.lane-stranded"},{"location":"aw/lane/lkexaw_attempt4","rule":"attention.lane-stranded"},{"location":"aw/lane/tgop8e","rule":"attention.lane-superseded"},{"location":"aw/lane/y4bdoz","rule":"attention.lane-superseded"}],"next":null}
       ```
    6. Specific cases `check.from-backlog-dangling` covers vs remaining uncovered:
       `check.from-backlog-dangling` covers an absent item only when an existing plan or spec carries `- From-Backlog: <id6>` referencing it. Uncovered cases are: (a) an absent item that has no referrer (e.g. an `open` item never graduated), and (b) write-time verification when the runner closes an item.
    7. Startup consultation (iii) confirmed absent:
       Grep across runner modules confirmed no startup attention/check call existed.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for BOTH broken counts (a commit leaving the id6 claimed 0 times, and one leaving it claimed 2 times IN THAT COMMIT), the resulting report pasted from all three destinations (item record, `events.jsonl`, stderr), each under its own rule name distinct from the other and from `attention.duplicate-id`, with proof the run did not fail; plus a close with no commit sha shown to report NOTHING; plus a healthy close shown to report nothing; plus the pre-existing `BacklogCloseIntegritySelfCheck` cases shown still passing, proving `backlog_item_paths_for_id` was not altered; plus evidence both hosts resolve the new query to ONE object.
  - Observed evidence: VERIFIED. Both 0 and 2 broken count conditions report in record, events.jsonl, and stderr under distinct rule names without failing the run; no-sha and healthy closes stay silent; pre-existing BacklogCloseIntegritySelfCheck tests pass; single shared implementation in runner_shared.py. Detail below:
    1. Broken count 0 (committed-absent):
       - Item `backlog_close` record:
         `"integrity": {"rule": "attention.committed-absent", "id6": "def456", "paths": [], "commit": "...", "count": 0, "detail": "backlog item def456 exists at 0 paths in commit ...; the destination write was probably dropped from the commit"}`
       - `events.jsonl`:
         `{"at": "...", "event": "backlog-close-integrity-violation", "id6": "plan02", "backlog_item": "def456", "rule": "attention.committed-absent", "paths": [], "commit": "...", "count": 0, "detail": "..."}`
       - stderr:
         `warning: backlog item def456 exists at 0 paths in commit ...; \`aw attention\` will report attention.committed-absent and its board is NOT authoritative until this is repaired (the destination write was probably dropped from the commit)`
       - Run not failed: `item["backlog_close"]["closed"] is True`.
    2. Broken count 2 (committed-duplicate):
       - Item `backlog_close` record:
         `"integrity": {"rule": "attention.committed-duplicate", "id6": "abc123", "paths": [".aw/records/backlog/done/...", ".aw/records/backlog/graduated/..."], "commit": "...", "count": 2, "detail": "backlog item abc123 exists at 2 paths in commit ... (...); a pre-move copy probably survived beside its destination"}`
       - `events.jsonl`:
         `{"at": "...", "event": "backlog-close-integrity-violation", "id6": "plan01", "backlog_item": "abc123", "rule": "attention.committed-duplicate", "paths": [...], "commit": "...", "count": 2, "detail": "..."}`
       - stderr:
         `warning: backlog item abc123 exists at 2 paths in commit ... (...); \`aw attention\` will report attention.committed-duplicate and its board is NOT authoritative until this is repaired (a pre-move copy probably survived beside its destination)`
       - Run not failed: `item["backlog_close"]["closed"] is True`.
    3. Close with no commit sha:
       `test_no_commit_sha_is_silent` confirms `"integrity"` is absent, 0 violation events in ledger, stderr clean.
    4. Healthy close with 1 claimant:
       `test_committed_tree_exactly_one_claimant_is_silent` confirms `"integrity"` is absent, 0 violation events, stderr clean.
    5. Pre-existing `BacklogCloseIntegritySelfCheck`:
       All 5 pre-existing tests (`test_a_single_claimant_is_the_healthy_case`, `test_two_claimants_are_detected_which_is_the_36_item_corruption`, `test_an_absent_id_is_empty_not_an_error`, `test_paths_are_repository_relative_so_no_home_path_can_leak`, `test_both_drivers_share_ONE_implementation`) pass unchanged.
    6. Both hosts resolve to one object:
       `runner_shared.backlog_item_paths_for_commit` is defined in `runner_shared.py` and called directly by the shared `process_backlog_close`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted startup output from BOTH hosts on a repository whose view is invalid, naming the outstanding rule ids, shown to appear before the run directory exists; a tree whose only findings are `info` severity shown to produce SILENCE; a case where computing the view fails, showing a warning rather than a raise; a records-free repository shown silent; and the measured added startup cost pasted.
  - Observed evidence: VERIFIED. Startup invalid-board report tested on both hosts before run-dir creation; info-only drift and records-free repositories produce silence; scan failure degrades to warning; in-process startup cost measured at ~4.0s. Detail below:
    1. Startup output on invalid repository (`test_invalid_board_is_reported_at_run_start`):
       ```
       warning: cross-tree attention view is INVALID (1 finding(s): attention.duplicate-id (1)); `aw attention` board is not authoritative until repaired
       ```
       `test_startup_report_ordering_is_before_run_directory_creation` asserts report occurs when `len(list(runs_dir.glob("run-*"))) == 0` before run directory creation.
    2. Tree with only `info` severity findings (`test_info_only_findings_are_silent_at_run_start`):
       Drift with `severity="info"` (`attention.lane-superseded`) produces exit code 0 from `drift_exit_code` and empty stderr output.
    3. View computation failure (`test_computation_failure_degrades_to_warning_and_does_not_raise`):
       Exception during scan produces warning `warning: could not compute cross-tree attention view at run start: disk read error` and does not raise.
    4. Records-free repository (`test_clean_repository_is_silent_at_run_start`):
       0 drift produces empty stderr output.
    5. Measured in-process startup cost:
       ```
       scan: 1.3621s (1481 items, 1 drift)
       stranded_lane_drift: 2.6442s (10 lanes)
       drift_exit_code: 0.000012s (exit_code=1)
       Total in-process time: 4.0063s
       ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: the new tests pasted FAILING against pre-E-02/E-03 code and PASSING after, with the fixtures shown to use REAL COMMITS (per F-7, a new test passing against current code proves it reproduced the blind spot, not the defect); the healthy-close and no-sha cases shown silent; the startup-report ordering assertion shown to fail if the report is moved after run-directory creation; the bare `python3 -m pytest` summary line; and the `aw sanitize --agent` output.
  - Observed evidence: VERIFIED. Real git fixtures used; tests demonstrated failing before fix and passing after; bare pytest suite 100% green; aw sanitize clean. Detail below:
    1. Pre-E-02 / Pre-E-03 failure against original code:
       ```
       FAILED tests/test_runner_backlog_close.py::CommittedTreeBacklogCloseIntegritySelfCheck::test_committed_tree_addition_only_duplicate_is_detected
       FAILED tests/test_runner_backlog_close.py::CommittedTreeBacklogCloseIntegritySelfCheck::test_committed_tree_deletion_only_vanished_is_detected
       FAILED tests/test_oc_runipd.py::StartupAttentionIntegrityReportTests::test_invalid_board_is_reported_at_run_start
       ```
    2. Post-E-02 / Post-E-03 pass:
       `tests/test_runner_backlog_close.py` and `tests/test_oc_runipd.py`: 336 passed in 15.47s.
    3. Healthy-close and no-sha silence:
       `test_committed_tree_exactly_one_claimant_is_silent` and `test_no_commit_sha_is_silent` both pass with 0 warnings.
    4. Startup report ordering before run directory:
       `test_startup_report_ordering_is_before_run_directory_creation` passes.
    5. Bare `python3 -m pytest` summary line:
       `8889 passed, 5 skipped, 2 xfailed, 6 warnings in 142.87s (0:02:22)`
    6. `aw sanitize --agent` output:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"findings":0,"evidence":["leak-scan"],"next":null}
       ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution. The executor commits only the paths named in `- Scope-Paths:` via `aw commit <plan> -- <paths>`, never `git add -A`, and never pushes. Test claims must paste actual runner output. On completion, `aw ipd lint --phase pre-transition` must conform and every `V-*` must carry observed evidence before the plan moves to `.aw/records/plans/executed/`.
