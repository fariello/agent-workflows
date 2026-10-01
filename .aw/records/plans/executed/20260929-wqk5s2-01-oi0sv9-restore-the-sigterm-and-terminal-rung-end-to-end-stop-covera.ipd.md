# IPD: Restore the SIGTERM and terminal-rung end-to-end stop coverage wqk5s2 reported, with a fixture that survives the run preflight

- Date: 2026-09-29
- Kind: child
- Concern: The two end-to-end stop-trigger behaviors backlog `wqk5s2` reported failing have NO test at HEAD, because the file holding them was deleted; the production defect is fixed, so what is missing is the guard, not the fix.
- Scope: Restore the SIGTERM (spec `c4gd2h` R13/A3) and terminal-rung (`install_stop_signal_handlers`) end-to-end assertions as behavioral tests driven by real signals to a real spawned driver, on a fixture plan that clears today's run preflight. No production change.
- Scope-Paths: tests/test_runner_stop_triggers_e2e.py, .aw/records/plans/pending/20260929-wqk5s2-01-oi0sv9-restore-the-sigterm-and-terminal-rung-end-to-end-stop-covera.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- From-Spec: c4gd2h
- Work-Kind: bug
- Priority: medium
- From-Backlog: wqk5s2
- Blocks-Release: next
- Set: wqk5s2
- Order: 1
- Highest E allocated: 04
- Author: OpenCode Claude Opus
- Id: oi0sv9

## Workflow history
- 2026-10-01 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: oi0sv9 verified (set wqk5s2, attempt 1).
- 2026-09-30 approved (aw set): status set to approved
- 2026-09-30 same-status (aw set): status unchanged (to-review)

- 2026-09-30 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 all FIXED, zero deferred, zero open. I VERIFIED THIS PLAN BY BUILDING IT at HEAD `c0b2300e`, not by reading it. Recovered the harness from `19313eed^`, applied the fixture repairs, and measured BOTH restored tests PASSING deterministically 3 of 3 at about 1.9s, printing exactly the evidence V-02/V-03 demand (`SIGTERM -> level 3 (now), certainty known, stopped after event 4`; `status='interrupted'`; `driver exit 130`). Every premise reproduces: `5efc78d2`'s diff is as described and is an ancestor of HEAD; `19313eed` deleted a 2922-line file holding 60 tests and PRECEDES the fix; no test at HEAD signals a real driver (the only `os.kill`/`killpg` hits are fake objects and a monkeypatch in `test_oc_runipd.py`); `drift`-free F-05 confirmed with `pe7g6r` `done` and `xvp5vx` `open`; and F-06's stale xfail reproduces as `[XPASS(strict)]`. PR-001 (HIGH): the fixture repair is THREE changes and F-03 named ONE. Substituting `_CONFORMING_PLAN` alone left both tests red with the same `rc=2`, and capturing the DRIVER's stderr showed the real cause is `Ambiguous filename selector: taa matches multiple plans`, not the IPD preflight: that template takes only `id6` and hardcodes `Set: demo`/`Order: 1`, so both fixture plans collide while their filenames say `taa`/`01`,`02`. Rewriting Set/Order fixed that and exposed a third blocker (rc=1 from `?? .aw/records/runs/`) which the `.gitignore` that `test_liftaudit_stop_halts_run.py` already uses clears. All three are now in E-01 and evidenced by V-01. PR-002 (HIGH): E-04's single mutation cannot falsify E-03. The two behaviors were fixed by DIFFERENT commits, `5efc78d2` (SIGTERM) and `891afabb`/`gvf2sq` (the terminal rung's `FORCED_INTERRUPT_SENTINEL`, `git log -S` confirming it as the sole introducing commit and a descendant of `5efc78d2`); measured, Mutation A reddens only the SIGTERM test while the terminal-rung test stays green, and a second mutation is needed for it. E-04 and V-04 now require both, with the measured failure texts. PR-003 (MEDIUM): the plan carried TWO `aw check` findings at its own path, one an `error` (`check.ipd-uncarried-obligation`: all four Deferred rows lacked a typed carrier, so the obligations would vanish when the plan classed `done`) plus `check.plan-spec-link-missing`; both fixed in place, `- From-Spec: c4gd2h` added through the setter, and `aw check plans` now reports CLEAN for this path. PR-004 (LOW): OQ-01 pointed at "V-05's evidence" and this plan has only V-01..V-04; corrected to V-03, and the decision's unstated consequence (two subprocess signal tests enter the default suite, about 3 percent of a 63s run) is now recorded. PR-005 (MEDIUM): the gate lacked the lifecycle transition, the approval summary and a scope fence; all added, with the note that E-04's mutations necessarily edit `runner_shared.py` in a throwaway copy only. Findings and decisions D-1..D-5 in `.aw/records/reviews/20260929-wqk5s2-01-oi0sv9-restore-the-sigterm-and-terminal-rung-end-to-end-stop-covera.review.md`.
- 2026-09-29 to-review (OpenCode Claude Opus): authored from backlog `wqk5s2`; diagnosis measured (production defect already fixed by `5efc78d2`, coverage deleted by `19313eed`), so the plan restores the guard rather than changing `agent_workflows/`.

## Goal

Backlog `wqk5s2` reported two `slow`-marked end-to-end stop tests failing at HEAD. Measured at authoring, BOTH halves of that report have changed: the production defect was fixed on 2026-09-25 by `5efc78d2`, and the file that asserted it was deleted on 2026-09-24 by `19313eed`. So the live risk is no longer a wrong `stopped`/`interrupted` record; it is that the two behaviors spec `c4gd2h` R13/A3 require now have NO test anywhere in `tests/`, and the same regression could return unnoticed. This plan restores exactly those two behaviors as signal-driven end-to-end tests, and pairs them with a fixture plan that clears the run preflight added after `wqk5s2` was filed, so the restored tests fail for real reasons only.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the two behaviors as end-to-end tests

- [x] E-01 Create `tests/test_runner_stop_triggers_e2e.py` holding the signal-driven harness the restored tests need: a `_make_repo` that writes its fixture plans from the ALREADY-SHARED `tests.test_oc_runipd._CONFORMING_PLAN`, a `_write_fake_child` fake agent that announces readiness through a marker file rather than a sleep, and a run handle that spawns the real driver with `start_new_session=True` and reads only DURABLE artifacts (`state.json`, `events.jsonl`, the stop request). Recover the harness from `git show 19313eed^:tests/test_runner_stop_triggers.py` rather than rewriting it, and carry over ONLY the plumbing the two restored tests use.
  THE FIXTURE REPAIR IS THREE CHANGES, NOT ONE, AND SUBSTITUTING `_CONFORMING_PLAN` ALONE LEAVES THE TESTS RED (review PR-001; the authored F-03 named only the substitution). Review built the file exactly as specified and measured `AssertionError: driver exited (rc=2) before the child was ready` still firing. Driving the spawn by hand to capture the driver's own stderr showed the real cause is NOT the run preflight: it is `runipd: Ambiguous filename selector: taa matches multiple plans: ['ta0001', 'ta0002']`. THE REASON is that `_CONFORMING_PLAN` is parameterised by `id6` ONLY and HARDCODES `- Set: demo` and `- Order: 1`, so both fixture plans claim the same Set and Order while their filenames say `taa` / `01`,`02`. SO DO ALL THREE: (a) write the plans from `_CONFORMING_PLAN`; (b) rewrite `- Set:` and `- Order:` in the produced text to match the FILENAME the fixture generates, which is what makes the setid selector resolve to a Set rather than to an ambiguous filename match; (c) add the `.gitignore` carrying `.aw/state/`, `.aw/worktrees/` and `.aw/records/runs/` that `tests/test_liftaudit_stop_halts_run.py` already uses, and stage it (`_git(repo, "add", "-A")` rather than `add README .aw`), or the run directory dirties the tree and the driver exits 1. With all three applied review measured BOTH restored tests PASSING, deterministically in 3 of 3 runs, 2 passed in about 1.9s.
  - Depends on: none
  - Expected outcome: the new file imports and collects, and `python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" --collect-only -q` lists the restored tests with no collection error. Review's own collect reported exactly the two node ids in 0.26s.
  - Execution state: performed
- [x] E-02 Restore the SIGTERM behavior (spec `c4gd2h` R13 and acceptance A3) as a test that sends a REAL `SIGTERM` to the spawned driver and then asserts on what the driver durably recorded: the stop request reached `runner_stop.LEVEL_NOW`, exactly one `deliberate-stop-at-checkpoint` event was appended, the in-flight item carries a `stopped` record whose `certainty` is `runner_stop.CERTAINTY_KNOWN` and whose `level` is `LEVEL_NOW`, that record contains no `unknown_outcome`, and the NEXT queued item was never started. This is the assertion whose `KeyError: 'stopped'` the backlog item reported.
  - Depends on: E-01
  - Expected outcome: the test passes at HEAD and drives the real code path; the `stopped` record it reads is the one written by `runner_shared._record_checkpoint_stop`.
  - Execution state: performed
- [x] E-03 Restore the terminal-rung behavior as a test that escalates real `SIGINT`s rung by rung (never a burst, because standard POSIX signals coalesce, which is why the recovered harness waits for each rung to be RECORDED before pressing again) until the terminal level, then asserts the in-flight item is recorded `interrupted`, is not in `oc_runipd.SUCCESS_STATES`, and that the driver exited nonzero. This is the `AssertionError: 'running' != 'interrupted'` half of the backlog report.
  - Depends on: E-01
  - Expected outcome: the test passes at HEAD, and the `interrupted` status it reads is produced by `runner_shared.reconcile_item_on_interrupt` reached from `execute_item_core`'s `except KeyboardInterrupt` arm.
  - Execution state: performed
- [x] E-04 Prove each restored test can still FAIL. THE TWO TESTS ARE GUARDED BY TWO DIFFERENT PRODUCTION CHANGES, and the authored single-mutation recipe falsifies only ONE of them (review PR-002). Perform BOTH mutations, separately, each in a throwaway copy outside the repository worktree, and do not commit either.
  MUTATION A, which falsifies the SIGTERM test (E-02): revert `5efc78d2`'s two lines in `runner_shared.execute_item_core`'s `StopAtCheckpoint` arm, putting `item["status"] = runner_stop.STOPPED_DISPOSITION` in place of the `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` call and `return` in place of the `raise`. Measured at review: the SIGTERM test goes RED with `AssertionError: 2 != 1 : SIGTERM must stop the turn at a safe checkpoint` (the `return` lets the run continue to the next item, so a SECOND `deliberate-stop-at-checkpoint` event is appended), while the terminal-rung test still PASSES.
  MUTATION B, which falsifies the TERMINAL-RUNG test (E-03): remove the `FORCED_INTERRUPT_SENTINEL` from the `KeyboardInterrupt` message raised by `_terminal` inside `runner_shared.install_stop_triggers`. That sentinel was added by `891afabb` (`work(gvf2sq)`, 2026-09-28), NOT by `5efc78d2`, which is why Mutation A cannot falsify this half. Measured at review: the terminal-rung test goes RED and the SIGTERM test still passes.
  WHY TWO MUTATIONS RATHER THAN ONE IS THE HONEST DESIGN: F-01's bisection found the FIRST commit at which the filing-time file passed, which is `5efc78d2`, but the terminal-rung half was fixed three days later by `891afabb` under sibling item `pe7g6r` (F-05 already records that a sibling closed that half through a different route; what it did not say is that this makes the mutation check two-part). A single-mutation E-04 would report "the guard bites" while leaving E-03 unfalsified, which is the vacuous-guard outcome this item exists to prevent.
  - Depends on: E-02, E-03
  - Expected outcome: Mutation A reddens the SIGTERM test only; Mutation B reddens the terminal-rung test only; with production intact both pass. Each test is therefore individually falsifiable, and neither guard is vacuous.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST TEST OUTCOMES, NOT CODE STRUCTURE. `AGENTS.md`'s execution contract forbids reading production source with `inspect`, `ast`, regex or substring search, and forbids restoring such tests; `GUIDING_PRINCIPLES` P16 is the cited source. This governs WHAT may be restored from the deleted file: the two behaviors in scope are signal-driven and read only durable artifacts, so they conform, but three classes in that same deleted file (`ImplicitStartShimTests`, `PlatformHonestyTests`, `ScopeFenceTests`) do read `agent_workflows/` source via `inspect.getsource`, `ast.parse` or `REPO_ROOT / "agent_workflows"`, and are therefore deliberately NOT restored here (see Deferred).
- THE SUITE IS RUN BARE. `pyproject.toml`'s `addopts` supplies `-m 'not slow'`, so a `slow`-marked test is invisible to the contract's prescribed `python3 -m pytest`. That is precisely why `wqk5s2` went unnoticed, and it is a decision this plan must make consciously rather than inherit (OQ-01).
- CITE BY SYMBOL, NOT BARE OFFSET. Code is cited here as `module.function` or by quoted content string, per spec `ipd-structure-and-linting` Section 10.2 (`IPD-C801`).
- A CONFORMING FIXTURE PLAN ALREADY EXISTS AND IS ALREADY SHARED. `tests.test_oc_runipd._CONFORMING_PLAN` is imported by `tests/test_liftaudit_stop_halts_run.py` for exactly this purpose, so the restored file reuses it instead of minting a fourth stub template.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The production defect `wqk5s2` describes IS FIXED. Bisecting the 1105 commits between the filing-day commit `ee20e831` (2026-09-21) and `b526dbaf` (2026-09-26), running the UNMODIFIED filing-time test file against each tree, the first passing commit is `5efc78d2` (2026-09-25, `liftaudit` / plan `afpmdu`). Its `runner_shared.py` diff is the fix: in `execute_item_core`'s `StopAtCheckpoint` and `StopNowForce` arms it replaced `item["status"] = runner_stop.STOPPED_DISPOSITION` with `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` and replaced `return` with `raise`. RE-VERIFIED AT REVIEW: the diff hunks are exactly as described, and `5efc78d2` is an ancestor of HEAD. CORRECTED AT REVIEW, and it changes E-04 (PR-002): `5efc78d2` fixes the SIGTERM half ONLY. The terminal-rung half was fixed separately by `891afabb` (`work(gvf2sq)`, 2026-09-28), which added the `FORCED_INTERRUPT_SENTINEL` to `_terminal`'s `KeyboardInterrupt` message, and `git log -S` confirms that is the single commit introducing it. So "the first commit at which the filing-time FILE passed" is not the same fact as "the commit that fixed each behavior", and reverting only `5efc78d2` leaves the terminal-rung test passing (measured). F-05 already notes a sibling fixed that half by another route; the consequence for the mutation check is now stated in E-04. | Bisection log in Validation V-01; `git show 5efc78d2 -- agent_workflows/runner_shared.py`; review: `git log -S"FORCED_INTERRUPT_SENTINEL})" -- agent_workflows/runner_shared.py` -> `891afabb` alone; `git merge-base --is-ancestor 5efc78d2 891afabb` -> true. |
| F-02 | The tests that reported it NO LONGER EXIST. `tests/test_runner_stop_triggers.py` was deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24). Both `19313eed` and `5efc78d2` are ancestors of HEAD, and the deletion PRECEDES the fix, so the fix shipped with its end-to-end guard already removed. No test at HEAD sends a real signal to a spawned driver: `send_signal`/`os.kill` appear in `tests/` only inside `tests/test_oc_runipd.py`, on fake process objects and a monkeypatched `os.killpg`, never on a real driver. | `git log --diff-filter=D -- tests/test_runner_stop_triggers.py`; `git merge-base --is-ancestor` both ways; repo-wide search for `send_signal`/`os.kill` under `tests/`. |
| F-03 | A NAIVE RESTORE IS RED FOR AN UNRELATED REASON, so the restore needs a fixture repair. Dropping the deleted file back in at HEAD fails with `driver exited (rc=2) before the child was ready`: the run refuses at freeze time with many `[RUN-STRUCTURE-PREFLIGHT] ... violates IPD-M101/H202/S404/M106/M110/M111` findings against the file's own 8-line `_PLAN_TEMPLATE`, ending `No work started, and nothing durable was created.` That preflight was added by `544ba188` on 2026-09-27, AFTER `wqk5s2` was filed, so it is fixture rot introduced later and not the reported defect. THE PRESCRIBED REPAIR IS INSUFFICIENT AND REVIEW MEASURED IT (PR-001). Writing the plans from `_CONFORMING_PLAN` alone leaves BOTH tests red with the SAME `rc=2` message, and capturing the driver's own stderr shows a DIFFERENT cause: `runipd: Ambiguous filename selector: taa matches multiple plans: ['ta0001', 'ta0002']`. `_CONFORMING_PLAN` takes only `id6` and HARDCODES `- Set: demo` / `- Order: 1`, so both fixture plans claim one Set and Order while their filenames encode `taa`/`01`,`02`, and the setid selector degrades to an ambiguous filename match. Rewriting `- Set:`/`- Order:` to match the generated filename fixes that and exposes a THIRD blocker, rc=1 from a dirty tree (`?? .aw/records/runs/`), which the `.gitignore` used by `tests/test_liftaudit_stop_halts_run.py` clears. With all three applied review measured both restored tests PASSING, deterministically 3 of 3, at 0.93s and 0.89s (about 1.9s for the pair including fixture setup). | Probe runs in Validation V-02 and V-03; `git log -S"RUN-STRUCTURE-PREFLIGHT"`; review: hand-driven spawn capturing the ambiguous-selector stderr, then `2 passed in 1.89s / 1.90s / 2.04s`. |
| F-04 | THE BACKLOG ITEM'S OWN OPEN QUESTION IS ANSWERED, and the answer is the one it flagged as the serious case. The item said "Whether the defect is in the PRODUCTION recording or in the tests' expectation is exactly what needs deciding, and this item does not presume". It was the production recording: at the filing-day commit the item is left `'running'` and carries no `stopped` key, exactly as reported, and `5efc78d2` changed production (not the assertions) to fix it. The assertions were right. | The filing-day reproduction in V-01, which matches the item's quoted `KeyError: 'stopped'` and `'running' != 'interrupted'` verbatim. |
| F-05 | A SIBLING ITEM ALREADY CLOSED THE TERMINAL-RUNG HALF THROUGH A DIFFERENT ROUTE, which is why this plan restores coverage rather than re-fixing. Backlog `pe7g6r` ("terminal rung leaves item running") is `done`, graduated to executed plan `gvf2sq`. It reported the same `'running' != 'interrupted'` failure against the same test name. This plan therefore does not duplicate that fix; it restores the end-to-end assertion that `19313eed` removed from under it. | `.aw/records/backlog/done/20260917-pe7g6r-01-pe7g6r-terminal-rung-leaves-item-running.backlog.md`; `.aw/records/plans/executed/20260928-pe7g6r-01-gvf2sq-record-the-in-flight-item-interrupted-at-the-terminal-sigint.ipd.md`. |
| F-06 | ONE MORE DELETED TEST IN THAT FILE IS A GENUINE, STILL-OPEN DEFECT REPORT, and it must not be restored blindly. `PreExistingInterruptContractTests::test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt` carries `@pytest.mark.xfail(strict=True)` for a regression its own reason text says was fixed later. With the fixture repaired it reports `XPASS(strict)`, i.e. FAILS, because the behavior now works and the stale marker forbids success. Restoring it verbatim would import a red test; restoring it without the marker is a THIRD behavior, outside what `wqk5s2` reported. REPRODUCED AT REVIEW on the repaired fixture: appending that test to the restored class yields `1 failed, 2 passed` with the failure rendering `[XPASS(strict)]` and quoting the stale reason text verbatim, so the finding is confirmed rather than inferred. | Probe run in V-04, which reports `1 failed, 59 passed` with the single failure being that `XPASS(strict)`; review's own 3-test probe reporting `1 failed, 2 passed` with the same `[XPASS(strict)]`. |
| F-07 | Added at review. THE PLAN CARRIES TWO LIVE `aw check` FINDINGS OF ITS OWN, both mechanically detected and both fixable in place. (a) `check.plan-spec-link-missing`: the plan cites spec `c4gd2h` in front matter (its Scope line) without carrying `- From-Spec:`, and the spec exists at `.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md` with `- Id: c4gd2h`, so the link resolves. (b) `check.ipd-uncarried-obligation`, an `error`-severity rule: all FOUR Deferred rows record an outstanding obligation with NO durable carrier, so "once this plan reaches `executed` it classes `done` in `aw attention` and this vanishes with no record". Three of the four DO name owning items in prose (`xvp5vx` twice, and a separate item for F-06) but not in the typed `- Carrier:`/`- Carrier-Declined:` field the checker reads. Both are fixed by this review. | `aw check plans --json` at review HEAD, the two diagnostics located at this plan's own path with the quoted details. |

## Proposed changes (ordered, validatable)

1. `tests/test_runner_stop_triggers_e2e.py` (new): the signal-driven harness recovered from `git show 19313eed^:tests/test_runner_stop_triggers.py`, reduced to what the two restored tests need, with its fixture plans written from `tests.test_oc_runipd._CONFORMING_PLAN` so the run preflight (F-03) is satisfied. A NEW filename rather than the old one, because this file deliberately restores 2 of that file's 60 tests and must not claim to be it.
2. The same file: the restored SIGTERM test (E-02), asserting spec `c4gd2h` R13/A3 on the durable `stopped` record.
3. The same file: the restored terminal-rung test (E-03), asserting the in-flight item is recorded `interrupted` and the driver exits nonzero.
4. No change to `agent_workflows/`. The production behavior is already correct (F-01), and this plan's scope is the missing guard.

## Deferred / out of scope (with reason)

- THE OTHER 57 DELETED TESTS in `tests/test_runner_stop_triggers.py`. `wqk5s2` reported two, and this plan restores those two. The broader question of what the trim removed is ALREADY TRACKED as backlog `xvp5vx` ("audit what properties lost their only guard in the 19313eed suite trim"), so duplicating it here would fragment that audit. Re-verified at review: the deleted file held 60 `def test_` functions, so 58 are not restored here, and `xvp5vx` is `open` with `Work-Kind: chore`.
  - Carrier: xvp5vx
- `ImplicitStartShimTests`, `PlatformHonestyTests` and `ScopeFenceTests` specifically are NOT candidates for restoration in any plan: measured at authoring, they read production source through `inspect.getsource`, `ast.parse` and `REPO_ROOT / "agent_workflows"`, which `AGENTS.md` and `GUIDING_PRINCIPLES` P16 forbid restoring. Whatever properties they guarded need behavioral replacements, which is `xvp5vx`'s business.
  - Carrier: xvp5vx
- `test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt` (F-06). Its stale `strict=True` xfail is a real finding, reproduced at review as `[XPASS(strict)]`, but resolving it means deciding a third behavior's coverage and removing an attestation another plan wrote. Recorded here as a finding and left to the suite-trim audit rather than silently absorbed; it is one of the deleted tests that audit must dispose of, so it needs no separate item of its own.
  - Carrier: xvp5vx
- CHANGING THE `slow` MARKER POLICY REPO-WIDE. OQ-01 decides only what THIS file carries.
  - Carrier-Declined: nothing is owed. This row records a BOUNDARY on this plan, not a deferred defect: no finding here measures a fault in the repository-wide marker policy, and OQ-01 resolves the only question this plan needs answered (whether these two tests carry the marker). A repo-wide policy change would be a contract decision for the maintainer, not outstanding work an item should assert.

## Scope check

- Over-scope: none. No production file is touched; the two restored tests are the two the backlog item names.
- Under-scope: the 57 other deleted tests in the same file, and the stale xfail (F-06), both deliberately deferred above with their owning items named.

## Required tests / validation

1. `python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" -q` must report both restored tests passing, with the count pasted. `-o addopts=""` is required to reach them if they stay `slow`-marked (OQ-01) and is harmless if they do not.
2. A bare `python3 -m pytest` must stay green, pasted with its `N passed` summary line, per the execution contract's HOW TO RUN THE SUITE paragraph (bare: no `-n0`, no extra `-q`, no `-p no:randomly`). Compare against a baseline the executor MEASURES at its own base rather than any number in this plan; review's own was `3387 passed, 2 skipped`, which will have moved.
3. The mutation check in E-04, which is TWO mutations, not one: Mutation A (reverting `5efc78d2`'s two lines) must redden the SIGTERM test, and Mutation B (removing `891afabb`'s `FORCED_INTERRUPT_SENTINEL`) must redden the terminal-rung test. A restored guard that cannot fail is not a guard, and a single mutation leaves one of these two unfalsified (review PR-002).
4. Three consecutive runs of the restored file, to show the signal escalation is not flaky (the recovered harness waits for each rung to be recorded rather than bursting, which is the anti-flake measure). Review measured `2 passed` in 1.89s / 1.90s / 2.04s.
5. `aw check plans` must report NO finding located at this plan's own path. Review found two there (`check.ipd-uncarried-obligation`, an error, and `check.plan-spec-link-missing`) and fixed both in place (F-07); an executor should confirm they have not returned rather than assume it.

## Spec / documentation sync

No spec amendment. Spec `c4gd2h` ("runner-lifecycle-graceful-quit", `implementing`) already states the contract these tests assert, unchanged: R13 "SIGTERM requests level 3" and A3 "Send SIGTERM to a run in flight. The current turn stops at a safe checkpoint, the item is recorded stopped/incomplete with KNOWN certainty (not `unknown_outcome`)". This plan restores coverage OF that requirement and does not alter it, so no `.spec.md` file is in `Scope-Paths`.

THE LINK TO THAT SPEC IS NOW DECLARED, added at review (F-07). The plan cites `c4gd2h` throughout but carried no `- From-Spec:` field, which `aw check` reports as `check.plan-spec-link-missing` against this plan's own path; the field is now set (`aw ipd set ... --from-spec c4gd2h`), and the spec resolves to `.aw/records/specs/implementing/20260829-c4gd2h-01-c4gd2h-runner-lifecycle-graceful-quit.spec.md`. Declaring the link does not make the spec editable by this plan and no spec path enters `- Scope-Paths:`; it records that this work descends from that contract, which is exactly what a restored conformance guard does.

## Open questions

### OQ-01: Should the restored tests carry `@pytest.mark.slow`?

- Blocking: no
- Status: resolved
- Owner: OpenCode Claude Opus
- Resolution or deferral rationale: RESOLVED from repository evidence: do NOT mark them `slow`. The backlog item names the marker as the reason the defect "went unnoticed", because `pyproject.toml`'s `addopts` carries `-m 'not slow'` and the contract's prescribed run is bare. The measured cost of not marking them is about 1.7s for the pair (0.76s and 0.89s, from `--durations` output in V-03), which does not warrant exclusion from the default run. RE-MEASURED AT REVIEW on the repaired fixture: 0.93s and 0.89s by `--durations`, with the whole file reporting `2 passed in 1.89s`, so the authored figure holds and the decision stands. Leaving them `slow` would restore the coverage into the same blind spot that let this defect sit from 2026-09-21 to 2026-09-29, so the restore would be nominal. If the executor measures materially more than that on its host, it should say so in V-03's evidence (which already demands `--durations` for both tests) rather than silently marking them `slow`. NOTE, corrected at review: the authored text pointed at "V-05's evidence" and there is no V-05 in this plan; the durations demand lives in V-03.
  ONE CONSEQUENCE THE RESOLUTION DOES NOT STATE, added at review: an unmarked test lands in the DEFAULT suite, so `python3 -m pytest` gains two subprocess-spawning signal tests. Measured at review, the bare suite runs 3387 tests in about 63s, so roughly 1.9s is about a 3 percent addition, and these are the only tests in the default set that deliver real signals to a spawned driver. That is the intended cost of the decision, not a hidden one; V-02 asks the executor to confirm the bare suite stays green with them included.

### OQ-02: Restore into the old filename or a new one?

- Blocking: no
- Status: resolved
- Owner: OpenCode Claude Opus
- Resolution or deferral rationale: RESOLVED: a new file, `tests/test_runner_stop_triggers_e2e.py`. Reusing `tests/test_runner_stop_triggers.py` would present 2 restored tests under the name of a 60-test file that `19313eed` deliberately deleted, which misrepresents coverage to the next reader and would make `xvp5vx`'s audit harder by appearing to have already restored that file. The `_e2e` suffix states what the file actually is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the `--collect-only -q` output for `tests/test_runner_stop_triggers_e2e.py` under `-o addopts=""`, showing the restored test node ids collected with no error, AND paste the `git show 5efc78d2 -- agent_workflows/runner_shared.py` hunk containing `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` to confirm F-01's fix is the one Mutation A must be able to falsify. Confirm in one line that the fixture plans are written from `tests.test_oc_runipd._CONFORMING_PLAN` and not from a hand-rolled stub.
  ALSO EVIDENCE ALL THREE FIXTURE REPAIRS, because the substitution alone leaves the tests red (F-03, as corrected): quote the lines that (a) format `_CONFORMING_PLAN`, (b) rewrite `- Set:` and `- Order:` to match the generated filename, and (c) write and stage the `.gitignore` covering `.aw/records/runs/`. If the executor's own first run reports `driver exited (rc=2) before the child was ready`, capture the DRIVER's stderr (not just the harness assertion) before concluding anything about the preflight: review measured the real cause there to be an ambiguous filename selector, not an IPD conformance refusal.
  - Observed evidence: PASS. Details:
    `python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" --collect-only -q` output:
    ```
    tests/test_runner_stop_triggers_e2e.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted
    tests/test_runner_stop_triggers_e2e.py::SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint

    2 tests collected in 0.41s
    ```
    `git show 5efc78d2 -- agent_workflows/runner_shared.py` hunk:
    ```diff
    @@ -26686,7 +26684,7 @@ def execute_item_core(
                 attempt["interrupt_reason"] = "deliberate-stop-at-checkpoint"
                 attempt["stopped"] = record
                 attempt["disposition"] = runner_stop.STOPPED_DISPOSITION
    -            item["status"] = runner_stop.STOPPED_DISPOSITION
    +            item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)
                 save_state(run_dir, state)
                 print(
                     pal(
    @@ -26696,7 +26694,7 @@ def execute_item_core(
                     ),
                     file=sys.stderr,
                 )
    -            return
    +            raise
    ```
    Confirmed: fixture plans in `tests/test_runner_stop_triggers_e2e.py` are written from `tests.test_oc_runipd._CONFORMING_PLAN` rather than any hand-rolled stub.
    Quoted fixture repairs in `_make_repo`:
    (a) Format `_CONFORMING_PLAN`:
    `plan_text = _CONFORMING_PLAN.format(id6=id6)`
    (b) Rewrite `- Set:` and `- Order:` to match generated filename:
    `plan_text = re.sub(r"^- Set:\s*.*$", f"- Set: {setid}", plan_text, flags=re.MULTILINE)`
    `plan_text = re.sub(r"^- Order:\s*.*$", f"- Order: {order}", plan_text, flags=re.MULTILINE)`
    (c) Write and stage `.gitignore` covering `.aw/records/runs/`:
    `(repo / ".gitignore").write_text(".aw/state/\n.aw/worktrees/\n.aw/records/runs/\n", encoding="utf-8")`
    `_git(repo, "add", "-A")`
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the actual passing run of the SIGTERM test node id under `-o addopts=""` with `-s`, including the test's own printed line reporting the recorded level, level name, certainty and the event index it stopped after (the harness prints it), so the evidence shows the record was READ from `state.json` rather than assumed. The pasted line must show level 3, `now`, and certainty `known`.
  - Observed evidence: PASS. Details:
    `python3 -m pytest tests/test_runner_stop_triggers_e2e.py::SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint -o addopts="" -s -v`:
    ```
    tests/test_runner_stop_triggers_e2e.py::SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint SIGTERM -> level 3 (now), certainty known, stopped after event 4 (tool_use:t4); driver exit 1
    PASSED

    ============================== 1 passed in 1.11s ===============================
    ```
    The test printed: `SIGTERM -> level 3 (now), certainty known, stopped after event 4 (tool_use:t4); driver exit 1`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste the actual passing run of the terminal-rung test node id under `-o addopts=""` with `-s`, including the harness's printed `in-flight item after 3x SIGINT: status=...` line showing `'interrupted'` and the printed nonzero driver exit code. Review's own run printed `status='interrupted'` and `driver exit code after the terminal rung: 130`, so that is the expected shape. Also paste `--durations` for both restored tests, which is the measurement OQ-01's decision rests on, and the three-consecutive-run evidence item 4 of Required tests asks for.
  - Observed evidence: PASS. Details:
    `python3 -m pytest tests/test_runner_stop_triggers_e2e.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted -o addopts="" -s -v`:
    ```
    tests/test_runner_stop_triggers_e2e.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted in-flight item after 3x SIGINT: status='interrupted'
    driver exit code after the terminal rung: 130
    PASSED

    ============================== 1 passed in 1.16s ===============================
    ```
    `--durations=0` for both restored tests (`python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" --durations=0`):
    ```
    ============================== slowest durations ===============================
    0.97s call     tests/test_runner_stop_triggers_e2e.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted
    0.87s call     tests/test_runner_stop_triggers_e2e.py::SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint

    (4 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 2 passed in 2.09s ===============================
    ```
    Three consecutive runs of the restored file (`python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" -q`):
    Run 1: `.. [100%] / 2 passed in 2.07s`
    Run 2: `.. [100%] / 2 passed in 1.98s`
    Run 3: `.. [100%] / 2 passed in 2.00s`
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste FOUR results, because there are TWO mutations and each must redden its OWN test (review PR-002). (a) Mutation A (`5efc78d2`'s `StopAtCheckpoint` arm reverted to `item["status"] = runner_stop.STOPPED_DISPOSITION` plus `return`): the SIGTERM test FAILING, with its failure text. Review measured `AssertionError: 2 != 1 : SIGTERM must stop the turn at a safe checkpoint`, because the `return` lets the run proceed to the next item and append a second stop event. (b) Under Mutation A, the terminal-rung test still PASSING, which is what proves the two are independently guarded. (c) Mutation B (`891afabb`'s `FORCED_INTERRUPT_SENTINEL` removed from `_terminal`'s `KeyboardInterrupt` message): the terminal-rung test FAILING. (d) Both tests PASSING against the unmodified worktree. Then paste `git status --short` for the repository worktree, which must show no `agent_workflows/` modification, proving each revert happened only in the throwaway copy. NAMING ONE MUTATION AND CALLING THE GUARD PROVEN IS A FAILED V-04: review measured that reverting `5efc78d2` alone leaves the terminal-rung test green, so a single-mutation run demonstrates nothing about E-03.
  - Observed evidence: PASS. Details:
    (a) Mutation A: SIGTERM test FAILING in throwaway copy:
    ```
    FAILED tests/test_runner_stop_triggers_e2e.py::SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint
    E   AssertionError: 2 != 1 : SIGTERM must stop the turn at a safe checkpoint, not kill the driver; events: [...]
    1 failed in 2.72s
    ```
    (b) Under Mutation A, terminal-rung test PASSING:
    ```
    .                                                                        [100%]
    1 passed in 1.88s
    ```
    (c) Mutation B: terminal-rung test FAILING in throwaway copy:
    ```
    FAILED tests/test_runner_stop_triggers_e2e.py::PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted
    E   AssertionError: 'queued' != 'interrupted'
    E   - queued
    E   + interrupted
    E    : the interrupted item must be recorded `interrupted`, got {'action': 'execute', ... 'status': 'queued'}
    1 failed in 3.48s
    ```
    Under Mutation B, SIGTERM test PASSING:
    ```
    .                                                                        [100%]
    1 passed in 2.27s
    ```
    (d) Both tests PASSING against unmodified worktree:
    ```
    ..                                                                       [100%]
    2 passed in 3.35s
    ```
    (e) `git status --short` in repository worktree:
    ```
    $ git status --short
    ?? tests/test_runner_stop_triggers_e2e.py
    ```
    Zero modification to `agent_workflows/`; both reverts executed strictly in throwaway copies.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

`/plan-review` has run (see `## Workflow history` and the typed review record), so the `- Readiness:` field it wrote is the review's attestation; explicit human approval is still required before execution. Both open questions are `- Blocking: no` and `- Status: resolved`, so nothing is outstanding for a human to answer.

WHAT A HUMAN IS APPROVING: one new test file holding two restored end-to-end tests, and no production change at all. The two behaviors are spec `c4gd2h` R13/A3 (a real SIGTERM stops the turn at a checkpoint and records the item `stopped` with KNOWN certainty) and the terminal SIGINT rung recording the in-flight item `interrupted`. Both have NO test anywhere at HEAD, because the file asserting them was deleted by the suite trim before the production fixes landed.

REVIEW BUILT THE WHOLE THING AND IT WORKS, so feasibility is measured rather than argued. Recovering the harness, applying the fixture repairs, and running both restored tests produced `2 passed` deterministically in 3 of 3 runs at about 1.9s, printing exactly the evidence V-02 and V-03 demand (`SIGTERM -> level 3 (now), certainty known`; `status='interrupted'`; `driver exit code after the terminal rung: 130`). Both mutations reddened their own test. Nothing from that probe is committed.

THREE REVIEW CORRECTIONS AN APPROVER SHOULD KNOW. FIRST, the fixture repair is THREE changes and the plan named one: substituting `_CONFORMING_PLAN` alone leaves both tests red, because that template hardcodes `Set: demo`/`Order: 1` and the run then refuses with an AMBIGUOUS FILENAME SELECTOR, not the IPD preflight F-03 blamed. SECOND, the two tests are guarded by two DIFFERENT production commits (`5efc78d2` for SIGTERM, `891afabb`/`gvf2sq` for the terminal rung), so the single mutation E-04 prescribed would have left E-03 unfalsified; measured, reverting `5efc78d2` alone leaves the terminal-rung test green. THIRD, the plan carried two `aw check` findings against its own path, one of them an `error` (all four Deferred rows lacked a typed carrier) plus a missing `- From-Spec: c4gd2h`; both are fixed here.

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit oi0sv9 -- <paths>`; never `git add -A`, never `-a`, never push, and never `--no-verify`. Paste ACTUAL runner output for every `V-*` item; a claimed pass with no pasted output does not satisfy this gate. No production file under `agent_workflows/` may be modified by this plan: if the executor concludes one must be, that is a scope change and it must stop and report rather than broadening. The mutation checks in E-04 REQUIRE editing `runner_shared.py`, and that is why both must happen in a throwaway copy OUTSIDE this worktree; V-04's `git status --short` paste is the proof they did.

Before the terminal transition, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` must carry observed evidence. The transition is then UNCONDITIONALLY owed with a CONDITIONAL owner: in a managed lane the RUNNER owns it (`aw ipd begin`/`finalize` refuse an agent there with `AW-LIFECYCLE-ROLE-001`), and only in an unmanaged or manual run does the executor run `aw ipd finalize oi0sv9 --actor <agent/model> --message <summary> --apply` itself. Never hand-roll the move with `git mv` and never hand-edit `- Status: executed`.

Scope fence (a DECLARATION for reconciliation, not a stop directive): the two paths in `- Scope-Paths:`. If the work genuinely requires a file outside it, make the edit and JUSTIFY it at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

This plan inherits `- Blocks-Release: next` from backlog `wqk5s2` and is its `From-Backlog` carrier, so the HANDOFF route legitimizes closing that item; AFTER EXECUTION, and not before, set it `done` citing this executed plan. The ORDER is load-bearing: while this plan sits in `pending/`, closing `wqk5s2` fails closed because the gate is handed to a carrier that has not shipped.
