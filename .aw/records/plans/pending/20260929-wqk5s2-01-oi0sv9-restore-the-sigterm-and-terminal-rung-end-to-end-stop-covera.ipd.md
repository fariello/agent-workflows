# IPD: Restore the SIGTERM and terminal-rung end-to-end stop coverage wqk5s2 reported, with a fixture that survives the run preflight

- Date: 2026-09-29
- Kind: child
- Concern: The two end-to-end stop-trigger behaviors backlog `wqk5s2` reported failing have NO test at HEAD, because the file holding them was deleted; the production defect is fixed, so what is missing is the guard, not the fix.
- Scope: Restore the SIGTERM (spec `c4gd2h` R13/A3) and terminal-rung (`install_stop_signal_handlers`) end-to-end assertions as behavioral tests driven by real signals to a real spawned driver, on a fixture plan that clears today's run preflight. No production change.
- Scope-Paths: tests/test_runner_stop_triggers_e2e.py, .aw/records/plans/pending/20260929-wqk5s2-01-oi0sv9-restore-the-sigterm-and-terminal-rung-end-to-end-stop-covera.ipd.md
- Item-Dependencies: none
- Status: to-review
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

- 2026-09-29 to-review (OpenCode Claude Opus): authored from backlog `wqk5s2`; diagnosis measured (production defect already fixed by `5efc78d2`, coverage deleted by `19313eed`), so the plan restores the guard rather than changing `agent_workflows/`.

## Goal

Backlog `wqk5s2` reported two `slow`-marked end-to-end stop tests failing at HEAD. Measured at authoring, BOTH halves of that report have changed: the production defect was fixed on 2026-09-25 by `5efc78d2`, and the file that asserted it was deleted on 2026-09-24 by `19313eed`. So the live risk is no longer a wrong `stopped`/`interrupted` record; it is that the two behaviors spec `c4gd2h` R13/A3 require now have NO test anywhere in `tests/`, and the same regression could return unnoticed. This plan restores exactly those two behaviors as signal-driven end-to-end tests, and pairs them with a fixture plan that clears the run preflight added after `wqk5s2` was filed, so the restored tests fail for real reasons only.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: restore the two behaviors as end-to-end tests

- [ ] E-01 Create `tests/test_runner_stop_triggers_e2e.py` holding the signal-driven harness the restored tests need: a `_make_repo` that writes its fixture plans from the ALREADY-SHARED `tests.test_oc_runipd._CONFORMING_PLAN` (verified conforming at `--phase pre-execution`, see Findings F-03), a `_write_fake_child` fake agent that announces readiness through a marker file rather than a sleep, and a run handle that spawns the real driver with `start_new_session=True` and reads only DURABLE artifacts (`state.json`, `events.jsonl`, the stop request). Recover the harness from `git show 19313eed^:tests/test_runner_stop_triggers.py` rather than rewriting it, and carry over ONLY the plumbing the two restored tests use.
  - Depends on: none
  - Expected outcome: the new file imports and collects, and `python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" --collect-only -q` lists the restored tests with no collection error.
  - Execution state: pending
- [ ] E-02 Restore the SIGTERM behavior (spec `c4gd2h` R13 and acceptance A3) as a test that sends a REAL `SIGTERM` to the spawned driver and then asserts on what the driver durably recorded: the stop request reached `runner_stop.LEVEL_NOW`, exactly one `deliberate-stop-at-checkpoint` event was appended, the in-flight item carries a `stopped` record whose `certainty` is `runner_stop.CERTAINTY_KNOWN` and whose `level` is `LEVEL_NOW`, that record contains no `unknown_outcome`, and the NEXT queued item was never started. This is the assertion whose `KeyError: 'stopped'` the backlog item reported.
  - Depends on: E-01
  - Expected outcome: the test passes at HEAD and drives the real code path; the `stopped` record it reads is the one written by `runner_shared._record_checkpoint_stop`.
  - Execution state: pending
- [ ] E-03 Restore the terminal-rung behavior as a test that escalates real `SIGINT`s rung by rung (never a burst, because standard POSIX signals coalesce, which is why the recovered harness waits for each rung to be RECORDED before pressing again) until the terminal level, then asserts the in-flight item is recorded `interrupted`, is not in `oc_runipd.SUCCESS_STATES`, and that the driver exited nonzero. This is the `AssertionError: 'running' != 'interrupted'` half of the backlog report.
  - Depends on: E-01
  - Expected outcome: the test passes at HEAD, and the `interrupted` status it reads is produced by `runner_shared.reconcile_item_on_interrupt` reached from `execute_item_core`'s `except KeyboardInterrupt` arm.
  - Execution state: pending
- [ ] E-04 Prove each restored test can still FAIL, by temporarily reverting in a scratch checkout the two production lines `5efc78d2` changed (`item["status"] = runner_stop.STOPPED_DISPOSITION` in place of the `reconcile_disposition` call, and `return` in place of `raise`, in `runner_shared.execute_item_core`'s `StopAtCheckpoint` arm) and recording that the restored tests go red. Do the revert ONLY in a throwaway copy outside the repository worktree and do not commit it; the point is to demonstrate the guard bites, not to change production.
  - Depends on: E-02, E-03
  - Expected outcome: with the fix reverted in the scratch copy, the restored tests fail; with it intact, they pass. The guard is therefore not vacuous.
  - Execution state: pending

## Project conventions discovered (Step 0)

- TESTS MUST TEST OUTCOMES, NOT CODE STRUCTURE. `AGENTS.md`'s execution contract forbids reading production source with `inspect`, `ast`, regex or substring search, and forbids restoring such tests; `GUIDING_PRINCIPLES` P16 is the cited source. This governs WHAT may be restored from the deleted file: the two behaviors in scope are signal-driven and read only durable artifacts, so they conform, but three classes in that same deleted file (`ImplicitStartShimTests`, `PlatformHonestyTests`, `ScopeFenceTests`) do read `agent_workflows/` source via `inspect.getsource`, `ast.parse` or `REPO_ROOT / "agent_workflows"`, and are therefore deliberately NOT restored here (see Deferred).
- THE SUITE IS RUN BARE. `pyproject.toml`'s `addopts` supplies `-m 'not slow'`, so a `slow`-marked test is invisible to the contract's prescribed `python3 -m pytest`. That is precisely why `wqk5s2` went unnoticed, and it is a decision this plan must make consciously rather than inherit (OQ-01).
- CITE BY SYMBOL, NOT BARE OFFSET. Code is cited here as `module.function` or by quoted content string, per spec `ipd-structure-and-linting` Section 10.2 (`IPD-C801`).
- A CONFORMING FIXTURE PLAN ALREADY EXISTS AND IS ALREADY SHARED. `tests.test_oc_runipd._CONFORMING_PLAN` is imported by `tests/test_liftaudit_stop_halts_run.py` for exactly this purpose, so the restored file reuses it instead of minting a fourth stub template.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | The production defect `wqk5s2` describes IS FIXED. Bisecting the 1105 commits between the filing-day commit `ee20e831` (2026-09-21) and `b526dbaf` (2026-09-26), running the UNMODIFIED filing-time test file against each tree, the first passing commit is `5efc78d2` (2026-09-25, `liftaudit` / plan `afpmdu`). Its `runner_shared.py` diff is the fix: in `execute_item_core`'s `StopAtCheckpoint` and `StopNowForce` arms it replaced `item["status"] = runner_stop.STOPPED_DISPOSITION` with `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` and replaced `return` with `raise`. | Bisection log in Validation V-01; `git show 5efc78d2 -- agent_workflows/runner_shared.py`. |
| F-02 | The tests that reported it NO LONGER EXIST. `tests/test_runner_stop_triggers.py` was deleted by `19313eed` ("test: trim test suite from 9,136 to under 2,000 tests", 2026-09-24). Both `19313eed` and `5efc78d2` are ancestors of HEAD, and the deletion PRECEDES the fix, so the fix shipped with its end-to-end guard already removed. No test at HEAD sends a real signal to a spawned driver: `send_signal`/`os.kill` appear in `tests/` only inside `tests/test_oc_runipd.py`, on fake process objects and a monkeypatched `os.killpg`, never on a real driver. | `git log --diff-filter=D -- tests/test_runner_stop_triggers.py`; `git merge-base --is-ancestor` both ways; repo-wide search for `send_signal`/`os.kill` under `tests/`. |
| F-03 | A NAIVE RESTORE IS RED FOR AN UNRELATED REASON, so the restore needs a fixture repair. Dropping the deleted file back in at HEAD fails with `driver exited (rc=2) before the child was ready`: the run refuses at freeze time with many `[RUN-STRUCTURE-PREFLIGHT] ... violates IPD-M101/H202/S404/M106/M110/M111` findings against the file's own 8-line `_PLAN_TEMPLATE`, ending `No work started, and nothing durable was created.` That preflight was added by `544ba188` on 2026-09-27, AFTER `wqk5s2` was filed, so it is fixture rot introduced later and not the reported defect. Writing the fixture plans from `tests.test_oc_runipd._CONFORMING_PLAN` (which lints `conforming` at `--phase pre-execution`) clears it, after which both reported tests pass at HEAD, deterministically in 3 of 3 runs, in about 0.8s each. | Probe runs in Validation V-02 and V-03; `git log -S"RUN-STRUCTURE-PREFLIGHT"`. |
| F-04 | THE BACKLOG ITEM'S OWN OPEN QUESTION IS ANSWERED, and the answer is the one it flagged as the serious case. The item said "Whether the defect is in the PRODUCTION recording or in the tests' expectation is exactly what needs deciding, and this item does not presume". It was the production recording: at the filing-day commit the item is left `'running'` and carries no `stopped` key, exactly as reported, and `5efc78d2` changed production (not the assertions) to fix it. The assertions were right. | The filing-day reproduction in V-01, which matches the item's quoted `KeyError: 'stopped'` and `'running' != 'interrupted'` verbatim. |
| F-05 | A SIBLING ITEM ALREADY CLOSED THE TERMINAL-RUNG HALF THROUGH A DIFFERENT ROUTE, which is why this plan restores coverage rather than re-fixing. Backlog `pe7g6r` ("terminal rung leaves item running") is `done`, graduated to executed plan `gvf2sq`. It reported the same `'running' != 'interrupted'` failure against the same test name. This plan therefore does not duplicate that fix; it restores the end-to-end assertion that `19313eed` removed from under it. | `.aw/records/backlog/done/20260917-pe7g6r-01-pe7g6r-terminal-rung-leaves-item-running.backlog.md`; `.aw/records/plans/executed/20260928-pe7g6r-01-gvf2sq-record-the-in-flight-item-interrupted-at-the-terminal-sigint.ipd.md`. |
| F-06 | ONE MORE DELETED TEST IN THAT FILE IS A GENUINE, STILL-OPEN DEFECT REPORT, and it must not be restored blindly. `PreExistingInterruptContractTests::test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt` carries `@pytest.mark.xfail(strict=True)` for a regression its own reason text says was fixed later. With the fixture repaired it reports `XPASS(strict)`, i.e. FAILS, because the behavior now works and the stale marker forbids success. Restoring it verbatim would import a red test; restoring it without the marker is a THIRD behavior, outside what `wqk5s2` reported. | Probe run in V-04, which reports `1 failed, 59 passed` with the single failure being that `XPASS(strict)`. |

## Proposed changes (ordered, validatable)

1. `tests/test_runner_stop_triggers_e2e.py` (new): the signal-driven harness recovered from `git show 19313eed^:tests/test_runner_stop_triggers.py`, reduced to what the two restored tests need, with its fixture plans written from `tests.test_oc_runipd._CONFORMING_PLAN` so the run preflight (F-03) is satisfied. A NEW filename rather than the old one, because this file deliberately restores 2 of that file's 60 tests and must not claim to be it.
2. The same file: the restored SIGTERM test (E-02), asserting spec `c4gd2h` R13/A3 on the durable `stopped` record.
3. The same file: the restored terminal-rung test (E-03), asserting the in-flight item is recorded `interrupted` and the driver exits nonzero.
4. No change to `agent_workflows/`. The production behavior is already correct (F-01), and this plan's scope is the missing guard.

## Deferred / out of scope (with reason)

- THE OTHER 57 DELETED TESTS in `tests/test_runner_stop_triggers.py`. `wqk5s2` reported two, and this plan restores those two. The broader question of what the trim removed is ALREADY TRACKED as backlog `xvp5vx` ("audit what properties lost their only guard in the 19313eed suite trim"), so duplicating it here would fragment that audit.
- `ImplicitStartShimTests`, `PlatformHonestyTests` and `ScopeFenceTests` specifically are NOT candidates for restoration in any plan: measured at authoring, they read production source through `inspect.getsource`, `ast.parse` and `REPO_ROOT / "agent_workflows"`, which `AGENTS.md` and `GUIDING_PRINCIPLES` P16 forbid restoring. Whatever properties they guarded need behavioral replacements, which is `xvp5vx`'s business.
- `test_the_item_level_bookkeeping_is_reached_by_a_real_interrupt` (F-06). Its stale `strict=True` xfail is a real finding, but resolving it means deciding a third behavior's coverage and removing an attestation another plan wrote. Recorded here as a finding and left to a separate item rather than silently absorbed.
- CHANGING THE `slow` MARKER POLICY REPO-WIDE. OQ-01 decides only what THIS file carries.

## Scope check

- Over-scope: none. No production file is touched; the two restored tests are the two the backlog item names.
- Under-scope: the 57 other deleted tests in the same file, and the stale xfail (F-06), both deliberately deferred above with their owning items named.

## Required tests / validation

1. `python3 -m pytest tests/test_runner_stop_triggers_e2e.py -o addopts="" -q` must report both restored tests passing, with the count pasted. `-o addopts=""` is required to reach them if they stay `slow`-marked (OQ-01) and is harmless if they do not.
2. A bare `python3 -m pytest` must stay green, pasted with its `N passed` summary line, per the execution contract's HOW TO RUN THE SUITE paragraph (bare: no `-n0`, no extra `-q`, no `-p no:randomly`).
3. The mutation check in E-04: with `5efc78d2`'s two production lines reverted in a scratch copy outside the worktree, the restored tests must go RED. A restored guard that cannot fail is not a guard.
4. Three consecutive runs of the restored file, to show the signal escalation is not flaky (the recovered harness waits for each rung to be recorded rather than bursting, which is the anti-flake measure).

## Spec / documentation sync

No spec amendment. Spec `c4gd2h` ("runner-lifecycle-graceful-quit", `implementing`) already states the contract these tests assert, unchanged: R13 "SIGTERM requests level 3" and A3 "Send SIGTERM to a run in flight. The current turn stops at a safe checkpoint, the item is recorded stopped/incomplete with KNOWN certainty (not `unknown_outcome`)". This plan restores coverage OF that requirement and does not alter it, so no `.spec.md` file is in `Scope-Paths`.

## Open questions

### OQ-01: Should the restored tests carry `@pytest.mark.slow`?

- Blocking: no
- Status: resolved
- Owner: OpenCode Claude Opus
- Resolution or deferral rationale: RESOLVED from repository evidence: do NOT mark them `slow`. The backlog item names the marker as the reason the defect "went unnoticed", because `pyproject.toml`'s `addopts` carries `-m 'not slow'` and the contract's prescribed run is bare. The measured cost of not marking them is about 1.7s for the pair (0.76s and 0.89s, from `--durations` output in V-03), which does not warrant exclusion from the default run. Leaving them `slow` would restore the coverage into the same blind spot that let this defect sit from 2026-09-21 to 2026-09-29, so the restore would be nominal. If the executor measures materially more than the ~1.7s recorded here on its host, it should say so in V-05's evidence rather than silently marking them `slow`.

### OQ-02: Restore into the old filename or a new one?

- Blocking: no
- Status: resolved
- Owner: OpenCode Claude Opus
- Resolution or deferral rationale: RESOLVED: a new file, `tests/test_runner_stop_triggers_e2e.py`. Reusing `tests/test_runner_stop_triggers.py` would present 2 restored tests under the name of a 60-test file that `19313eed` deliberately deleted, which misrepresents coverage to the next reader and would make `xvp5vx`'s audit harder by appearing to have already restored that file. The `_e2e` suffix states what the file actually is.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste the `--collect-only -q` output for `tests/test_runner_stop_triggers_e2e.py` under `-o addopts=""`, showing the restored test node ids collected with no error, AND paste the `git show 5efc78d2 -- agent_workflows/runner_shared.py` hunk containing `item["status"], _ = reconcile_disposition(repo, item, run_dir, 1)` to confirm F-01's fix is the one the harness must be able to falsify. Confirm in one line that the fixture plans are written from `tests.test_oc_runipd._CONFORMING_PLAN` and not from a hand-rolled stub.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the actual passing run of the SIGTERM test node id under `-o addopts=""` with `-s`, including the test's own printed line reporting the recorded level, level name, certainty and the event index it stopped after (the harness prints it), so the evidence shows the record was READ from `state.json` rather than assumed. The pasted line must show level 3, `now`, and certainty `known`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste the actual passing run of the terminal-rung test node id under `-o addopts=""` with `-s`, including the harness's printed `in-flight item after 3x SIGINT: status=...` line showing `'interrupted'` and the printed nonzero driver exit code. Also paste `--durations` for both restored tests, which is the measurement OQ-01's decision rests on.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste BOTH halves of the mutation check: (a) the restored tests FAILING in the scratch copy with `5efc78d2`'s `StopAtCheckpoint` arm reverted to `item["status"] = runner_stop.STOPPED_DISPOSITION` plus `return`, showing the failure text, and (b) the restored tests PASSING against the unmodified worktree. Then paste `git status --short` for the repository worktree, which must show no `agent_workflows/` modification, proving the revert happened only in the throwaway copy. If only one half is pasted, this item is not verified.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only the paths named in `Scope-Paths`, through `aw commit <plan> -- <paths>`; never `git add -A`, never `-a`, never push, and never `--no-verify`. Paste ACTUAL runner output for every `V-*` item; a claimed pass with no pasted output does not satisfy this gate. No production file under `agent_workflows/` may be modified by this plan: if the executor concludes one must be, that is a scope change and it must stop and report rather than broadening. Before the terminal transition, `aw ipd lint --phase pre-transition` must report conforming and every `V-*` must carry observed evidence; only then move this plan to `.aw/records/plans/executed/`.
