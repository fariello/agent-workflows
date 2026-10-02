# IPD: Make the per-test hang guard measure CPU time so machine load cannot fail a correct test

- Date: 2026-10-02
- Kind: child
- Concern: The per-test hang guard in `conftest.py` arms `ITIMER_REAL`, a WALL-CLOCK timer, so a test's measured duration includes time it spent descheduled waiting for a CPU it was not given. Under the suite's own `-n auto` parallelism the same correct test inflates from 29.53s isolated to 66.53s in-suite while consuming the SAME 28s of CPU, so the budget is spent on contention rather than on work. `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` is the test this surfaces on, and the guard has reported it red across at least 12 separate executed plans.
- Scope: Change the hang guard's cost dimension from wall clock alone to a DUAL budget: a load-invariant CPU budget (`ITIMER_PROF`, counting user+sys) that measures the work a test actually does, plus a generous wall ceiling retained because a zero-CPU deadlock is provably invisible to a CPU timer. Add the first tests the guard has ever had. No production module is touched.
- Scope-Paths: conftest.py, tests/test_hang_guard_budget.py
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: mu4k1g
- Blocks-Release: next
- Set: hangcpu
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 6ye76g

## Workflow history

- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `mu4k1g`. Every premise measured at HEAD `3127e3f00` rather than assumed: the wall-versus-CPU divergence, the whole-suite CPU census, the dual-timer coexistence probe, the deadlock blind spot that forces the wall ceiling to stay, and the `ITIMER_VIRTUAL`-versus-`ITIMER_PROF` choice. A competing pending plan (`mat9bt`) was found and is reconciled in F-09 rather than duplicated.

## Goal

Stop the hang guard failing correct tests because the machine was busy, by budgeting the CPU time a test CONSUMES instead of the wall time it OCCUPIES. The guard was installed to stop a runaway test burning a 48-minute turn, and a CPU budget catches that class strictly better than a wall budget does, because a spinning test burns CPU by definition. The wall ceiling stays, raised and re-aimed at the one class CPU cannot see: a deadlock that blocks forever consuming nothing.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-establish the defect at the execution head

- [ ] E-01 Re-measure the target test's wall time and CPU time both isolated and in-suite, before changing anything, so the plan's central claim (wall inflates, CPU does not) is demonstrated at the execution head rather than inherited from this document.
  - Depends on: none
  - Expected outcome: four numbers pasted: isolated wall, isolated CPU, in-suite wall, in-suite CPU. The in-suite wall must be materially above the isolated wall while the two CPU figures agree to within a few percent. If CPU has become the thing that inflates, STOP AND REPORT: this remedy is sized to the divergence, and without the divergence the diagnosis is wrong.
  - Execution state: pending

### Task group 2: Re-aim the guard onto CPU, keeping a wall ceiling

- [ ] E-02 Replace the guard's single wall budget with two budgets in `conftest.py`: a CPU budget armed on `ITIMER_PROF` and a wall ceiling armed on `ITIMER_REAL`, each with its own handler naming WHICH budget it exceeded.
  - Depends on: E-01
  - Expected outcome: `conftest.pytest_runtest_call` arms both timers, restores both previous handlers and cancels both timers in its `finally`, and keeps every property the current guard was deliberately built with: `faulthandler` all-thread stack dump on first fire, a `BaseException` subclass so `except Exception:` cannot swallow it, the 1.0s repeating re-raise so one lands outside a broad handler, the main-thread-only and `SIGALRM`-exists preconditions, and the stand-down when a test has installed its own handler. The stand-down must now check BOTH signals, because a test exercising `SIGPROF` deserves the same courtesy a test exercising `SIGALRM` already gets.
  - Execution state: pending

- [ ] E-03 Choose the budget numbers from the measured CPU census rather than by taste, and record the derivation in the rationale comment.
  - Depends on: E-02
  - Expected outcome: a CPU budget sized with real headroom over the 28.61s worst observed self-CPU in the fast suite (F-03), and a wall ceiling well above the worst observed wall time but still far below the runner's stall budget. The comment must state both numbers, what each one catches, and the measurement each came from, so the next person to tune them has the data rather than a guess.
  - Execution state: pending

- [ ] E-04 Extend the per-test and per-run overrides to address both budgets, keeping the existing spellings working.
  - Depends on: E-02
  - Expected outcome: `@pytest.mark.timeout(<seconds>)` and `AW_TEST_TIMEOUT` continue to work and continue to mean a CPU budget's worth of cost, `0` still disables, and there is a way to address the wall ceiling separately. The four tests already carrying `@pytest.mark.timeout` (`tests/test_exit_contract_conformance.py` at 500, two in `tests/test_json_surface_leak_posture.py` at 300) must keep passing WITHOUT being edited: they are subprocess-heavy and spend almost no parent CPU, so a CPU-only reading of their marker would silently make their budget enormous. State explicitly which budget an existing marker now sets and why that is the safe reading.
  - Execution state: pending

### Task group 3: Give the guard the tests it has never had

- [ ] E-05 Add `tests/test_hang_guard_budget.py` proving the guard fires on the classes it must catch, by running real pytest subprocesses and asserting on their output and exit codes.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: outcome tests (P16: drive the code, assert real output and exit codes, never read production source with `inspect`/`ast`/regex) covering: a CPU-burning runaway IS caught and NAMED; a test that sleeps far past the CPU budget but inside the wall ceiling is NOT caught, which is the whole point of this plan; a zero-CPU deadlock IS caught by the wall ceiling; `0` disables; a marker lowers the budget; the failure names which budget was exceeded; and the guard behaves identically under `-n 2` as serially, since the suite always runs under xdist and a guard that only worked in the main process would be inert.
  - Execution state: pending

- [ ] E-06 Prove the suite-level outcome: the target test stops being load-dependent, and the guard still reports a genuine runaway.
  - Depends on: E-05
  - Expected outcome: a bare suite run in which the target nodeid is absent from the failure list, plus a demonstration that an injected runaway in a scratch test is still caught under that same configuration. The second half is required because a change that merely stops the guard firing is indistinguishable from a change that breaks the guard, and only the injection separates them.
  - Execution state: pending

### Task group 4: Record the limit honestly

- [ ] E-07 Document the blind spot this design accepts, in the rationale comment and in this plan's record.
  - Depends on: E-03
  - Expected outcome: a plainly worded note that a CPU budget cannot see a test blocked on I/O, a lock, or a child process, that this is why the wall ceiling is retained rather than removed, and that the ceiling is deliberately loose enough to be useless as a cost control. Anyone later tempted to delete the wall arm as redundant needs the measurement in F-05 showing a CPU-only guard let a 45s deadlock run to completion untouched.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- RUN THE SUITE BARE (`python3 -m pytest`). `pyproject.toml` `addopts` already supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`. Do not add `-n0` (several times slower here), a second `-q` (compounds to `-qq` and suppresses the `N passed` summary this plan requires pasted), or `-p no:randomly` (disables order randomization). To see per-test counts from a narrowed run, clear the defaults with `-o addopts=""`.
- P16 (GUIDING_PRINCIPLES) BANS CODE-PINNING TESTS, and this plan is unusually exposed to that trap because its subject is a pytest hook. E-05 must therefore drive the guard by running real pytest subprocesses and asserting on their stdout/stderr and exit codes. It must NOT assert that `conftest.py` contains certain text, must NOT count callers or `inspect` the hook, and must NOT pin the rationale comment's wording.
- THE GUARD'S DESIGN DECISIONS ARE MEASURED, NOT STYLISTIC, and each is documented in `conftest.py` with the incident that forced it. `TestHangTimeout` derives from `BaseException` because an `Exception`-based timeout was swallowed by `except Exception:` handlers for about 20s; the timer repeats at 1.0s because a one-shot alarm did NOT stop the hang it was built for, the first raise having landed under an `except Exception: return []`; `KeyboardInterrupt` is deliberately avoided because pytest treats it as a session abort. E-02 preserves all three rather than rediscovering them.
- THE REPOSITORY ALREADY SANCTIONS A PER-TEST BUDGET OVERRIDE and four tests use it: `tests/test_exit_contract_conformance.py` carries `@pytest.mark.timeout(500)` and documents in its own docstring that the marker is needed because the guard "ignores @pytest.mark.slow"; `tests/test_json_surface_leak_posture.py` carries two at 300. E-04 must keep all four green untouched.
- `AW_TEST_TIMEOUT` HAS NO EXTERNAL CONSUMERS, so changing its meaning breaks no caller. A repo-wide search finds it referenced only inside `conftest.py` itself (its rationale comment and `_test_timeout_seconds`), and in no workflow, `Makefile` target, or runner module.

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | **THE GUARD MEASURES WALL CLOCK, WHICH IS WHY LOAD FAILS A CORRECT TEST.** `conftest.pytest_runtest_call` arms `signal.setitimer(signal.ITIMER_REAL, budget, 1.0)`. `ITIMER_REAL` counts wall-clock time, so every second a test spends descheduled waiting for a core is charged to its budget exactly as if it had been working. This is the root cause, and it is a property of the timer selection rather than of any test. | `conftest.py` contains `_signal.setitimer(_signal.ITIMER_REAL, budget, 1.0)`. Direct probe: with a 1.0s budget and a 2.5s `time.sleep` consuming `0.000s` of CPU, `ITIMER_REAL -> fired=1` while `ITIMER_VIRTUAL -> fired=0`. |
| F-02 | **WALL TIME MORE THAN DOUBLES UNDER THE SUITE'S OWN PARALLELISM WHILE CPU TIME IS FLAT, so the budget is being consumed by contention and not by work.** This is the measurement the whole plan rests on: the test's COST did not change, only its OCCUPANCY did. On 12 cores the suite runs `-n auto`. | Isolated: `29.53s call` / `1 passed in 30.01s`. In-suite bare run with `--durations=12`: `66.53s call tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`, the slowest in the suite. Self-CPU across those two conditions: `28.29s` measured in a dedicated subprocess versus `28.61s` measured in-suite, a divergence of about 1 percent against a wall divergence of 2.25x. `nproc` = 12. |
| F-03 | **A CPU BUDGET IS COMFORTABLY SIZEABLE, because the worst self-CPU in the entire fast suite is 28.61s.** A whole-suite census with a profiling plugin and the guard disabled ranks every test above 1s by both dimensions. Nothing in the suite approaches a CPU figure that would make a generous CPU budget tight, so the budget can carry real headroom and still bind. | Whole-suite census (`AW_TEST_TIMEOUT=0`, profiling plugin, bare otherwise): `max self-cpu seen in whole fast suite: 28.61s`. Top rows by wall, as `wall / selfcpu`: `60.96 / 26.06` verbose-flag reach, `59.07 / 28.61` the target test, `33.67 / 0.00` `test_aw_check_plans_agent_no_crash`, `32.25 / 0.00` `test_cli_json_surface_envelope_clean`, `31.80 / 13.28` fields-flag reach, `30.24 / 0.00` `test_agent_surface_conformance[next]`, `23.46 / 0.02` the color-depth ladder. |
| F-04 | **THE WALL-HEAVY, CPU-FREE TESTS ARE THE COMMON CASE, AND THEY ARE THE ONES A WALL BUDGET PUNISHES MOST UNFAIRLY.** Four of the seven slowest tests by wall time consume effectively ZERO parent CPU (`0.00`, `0.00`, `0.00`, `0.02`), because they are subprocess-driven: the parent blocks in `wait()` while a child works. Under a wall budget their measured duration is almost entirely other processes' scheduling; under a CPU budget they are correctly cheap. | The `0.00` and `0.02` self-CPU rows in F-03's census. Corroborated per-test: `test_typecheck_gate_clean_exit` measured `wall=1.36s totalcpu=1.51s` when its child CPU is counted but `wall=0.67 PARENTcpu=0.00` when it is not, and it was itself reported as a load-dependent suite failure in two earlier plans while taking `0.31s`, `0.40s`, `0.36s` on three isolated runs. |
| F-05 | **A CPU-ONLY GUARD IS PROVABLY BLIND TO A DEADLOCK, WHICH IS WHY THE WALL CEILING MUST STAY.** A test blocking on an `Event` consumes no CPU, so a CPU timer never expires and the hang is invisible. With a 3s CPU budget and the wall arm disabled, such a test ran to its own 45s completion and the guard never fired. Removing the wall arm would therefore reintroduce the exact failure mode the guard exists to prevent. | Probe, CPU budget 3s and wall disabled, against `threading.Event().wait(45)`: `1 passed in 45.32s`, guard silent. The same dual-timer prototype with a 30s wall and 3s CPU budget against a spinning test: `zz_dual.Hang: CPU budget exceeded for tests/test_zz_hangclasses.py::test_spin_burns_cpu`, `1 failed, 2 passed in 26.41s`, with the sleeping and fast tests both correctly untouched. |
| F-06 | **BOTH TIMERS CAN BE ARMED SIMULTANEOUSLY AND FIRE INDEPENDENTLY ON DIFFERENT SIGNALS, so the dual-budget design is verified rather than hoped for.** `ITIMER_REAL` delivers `SIGALRM` and `ITIMER_PROF` delivers `SIGPROF`, which are distinct handlers, so one guard can distinguish "this test is expensive" from "this test is stuck". | Probe: with CPU budget 0.5s and wall budget 5s, a 1.5s CPU burn fired `['cpu']` only. With CPU budget 5s and wall budget 0.5s, a 1.5s sleep fired `['wall']` only. |
| F-07 | **`ITIMER_PROF` IS THE CORRECT CPU TIMER AND `ITIMER_VIRTUAL` IS NOT, because `VIRTUAL` counts user time only and would be blind to a syscall-bound spin.** A syscall-heavy loop splits its cost roughly evenly between user and system time, so a user-only timer under-charges it by about half. | A 40,000-iteration `os.stat` loop measured `user=0.086s sys=0.085s`. Probe with a 1.0s budget against a syscall-heavy burn: `ITIMER_PROF -> fired (correct: counts sys)`. `ITIMER_PROF` with a 1.0s budget against a 2.0s sleep: `did NOT fire (correct)`. |
| F-08 | **THE GUARD HAS NO TESTS AT ALL, which is why this plan adds them and why its own correctness claims must be demonstrated by injection rather than by a green suite.** No file under `tests/` references `TestHangTimeout`, `AW_TEST_TIMEOUT`, or the guard's message. A change to an untested mechanism that merely stops a failure is indistinguishable from one that disables the mechanism. The guard does, however, demonstrably work today inside xdist workers. | `grep -rln "TestHangTimeout\|AW_TEST_TIMEOUT\|HANG GUARD" tests/` returns nothing. Under `-n 2` with `AW_TEST_TIMEOUT=2`, an 8s spinning probe failed with `conftest.TestHangTimeout: TEST HANG GUARD: tests/test_zz_guardxdist.py::test_overruns_budget exceeded its 2s per-test budget` and the all-thread stack dump, `1 failed in 3.07s`. |
| F-09 | **A COMPETING PENDING PLAN ATTACKS THE SAME SYMPTOM FROM THE TEST SIDE, AND THE TWO ARE COMPLEMENTARY RATHER THAN DUPLICATES, BUT THEY DO CONFLICT IN ONE PLACE.** Plan `mat9bt` (Set `8sr0or`, `to-review`) cuts the swept sweep to a pairwise covering array, declaring `- Scope-Paths: tests/test_statusline_behavior.py`. It fixes ONE test's cost; this plan fixes the GUARD that mismeasures every test. Neither file overlaps. THE CONFLICT IS A PROSE INSTRUCTION, NOT A FILE: `mat9bt`'s execution contract says "Do not raise `_DEFAULT_TEST_TIMEOUT` in `conftest.py`", reasoning that raising the global budget would blind the guard. This plan does not raise the wall budget to fit a slow test; it changes the DIMENSION measured, which is the objection's actual substance. | `mat9bt` front matter: `- Status: to-review`, `- Scope-Paths: tests/test_statusline_behavior.py`, `- From-Backlog: 8sr0or`, `- Blocks-Release: next`. Its gate prose contains "Do not raise `_DEFAULT_TEST_TIMEOUT` in `conftest.py` to make the existing test fit". Its F-01 measures the same test at `68.16s`, consistent with this plan's `66.53s`. No pending plan declares `conftest.py` in `- Scope-Paths:` (`grep -rn "^- Scope-Paths:.*conftest" .aw/records/plans/pending/` is empty). |
| F-10 | **THREE BACKLOG ITEMS DESCRIBE THIS ONE FAILURE AND ONE IS ALREADY GRADUATED, so this plan must not quietly close records it was not handed.** `mu4k1g` (this plan's item, `open`) and `cqgr7f` (`open`) are both the same nodeid and the same load-dependent failure; `8sr0or` is already `graduated` to `mat9bt`. A fourth, `tf6x3a`, proposes marking the `fields`/`verbose` reach tests `livecorpus`, which F-03 shows is the neighbouring wall-heavy case. | `.aw/records/backlog/graduated/...8sr0or...` carries `- Status: graduated`, `- Graduated-To: 8sr0or`. `.aw/records/backlog/open/` holds `...cqgr7f...` (`- Status: open`, `- Work-Kind: bug`, `- Blocks-Release: next`) and `...tf6x3a...`. All three statusline items carry `- Blocks-Release: next`. |
| F-11 | **THE GUARD HAS REPORTED THIS ONE TEST RED ACROSS AT LEAST 12 EXECUTED PLANS, so the cost is recurring reviewer and agent time rather than a one-off annoyance.** Executed plan records repeatedly carry the nodeid with a note that it passed in isolation, each instance having cost an executing agent a triage round trip. The same pattern afflicts five other nodeids. | `grep -rhoiE` over `.aw/records/plans/` counts mentions per nodeid: `test_every_real_spec_in_this_repository_still_conforms` 66, `test_unreachable_binding_refusal_fires_under_perturbation` 62, `test_box_renderer_invariants_across_swept_inputs` 34, `test_verbose_flag_end_to_end_observable_difference` 26, `test_two_process_lock_wait_succeeds` 15, `test_typecheck_gate_clean_exit` 10. Sample annotations: "2 are timeouts under heavy parallel xdist load ... which pass in isolation (2 passed in 19.14s)"; "caused by timeout under 37-worker parallel execution, verified passing individually". |
| F-12 | **THE BASELINE AT THIS HEAD IS `3 failed, 4624 passed, 2 skipped`, AND ALL THREE FAILURES ARE PRE-FILED AND UNRELATED TO THE GUARD.** Recorded so the post-change run reconciles against a known set instead of being read as clean or as newly broken. Notably the target test PASSED in this run at `66.53s`, consistent with F-02: it is load-dependent, not deterministic, which is itself the argument for fixing the measurement rather than waiting for a reliable reproduction. | Bare `python3 -m pytest --durations=12` at HEAD `3127e3f00`: `3 failed, 4624 passed, 2 skipped, 3 warnings in 256.43s`, 232 deselected. The three: `tests/test_run_finding_reachability.py::TestRunFindingReachability::test_unreachable_binding_refusal_fires_under_perturbation`, `tests/test_spec_review_attestation.py::GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`, `tests/test_selector_type_containment.py::test_must_not_refuse_matrix`. |

## Proposed changes (ordered, validatable)

1. Re-measure wall and CPU, isolated and in-suite, before editing anything, and stop if the divergence has vanished (E-01).
2. Arm two timers in the guard, `ITIMER_PROF` for CPU cost and `ITIMER_REAL` for a wall ceiling, each naming its own budget on expiry, preserving every measured design decision the current guard carries (E-02).
3. Size both budgets from the whole-suite CPU census and record the derivation in the rationale comment (E-03).
4. Extend the marker and environment overrides to address both budgets, keeping the four existing `@pytest.mark.timeout` tests green untouched (E-04).
5. Add `tests/test_hang_guard_budget.py`, the guard's first tests, as outcome tests driving real pytest subprocesses, serially and under `-n 2` (E-05).
6. Demonstrate the suite-level outcome in both directions: the target test no longer load-dependent, and an injected runaway still caught (E-06).
7. Document the accepted blind spot and why the wall ceiling is retained (E-07).

## Deferred / out of scope (with reason)

- The swept-input sweep's own 7,776-row cost is NOT reduced here. `mat9bt` owns that, and F-09 establishes the two plans are complementary: that one lowers one test's cost, this one stops the guard mismeasuring every test's cost. Both are worth doing and neither subsumes the other.
  - Carrier: mat9bt
- Marking the `fields`/`verbose` end-to-end reach tests `livecorpus` is not done here. F-03 measures them at `60.96s` and `31.80s` wall against `26.06s` and `13.28s` CPU, so this plan's change substantially relieves them, but whether they belong in the default suite at all is a separate editorial call.
  - Carrier: tf6x3a
- The duplicate backlog item `cqgr7f` (F-10) describes the same failure as this plan's item and is not closed or retired here.
  - Carrier-Declined: Deliberately NOT carried. Deduplicating another record's lifecycle is a maintainer's call, not an executing agent's, and filing a carrier for "someone should tidy the backlog" would add a fifth record to a pile of four. RECOMMENDED ACTION FOR THE REVIEWER: once this plan executes, close `cqgr7f` as a duplicate of `mu4k1g` with this plan as the evidence, or re-point it here.
- The three pre-existing suite failures in F-12 are not fixed here; they are recorded only so the post-change run reconciles against a known set.
  - Carrier-Declined: No carrier is filed because all three are pre-existing and independently filed, and none touches the guard. Filing a fourth owner for work that already has one is the exact failure mode F-10 documents.
- No production module under `agent_workflows/` is touched. `- Scope-Paths:` names the test harness only.
  - Carrier-Declined: This is a SCOPE CONSTRAINT, not parked work. No production defect is known or suspected here; the defect is in how the harness MEASURES. If execution discovers a real product bug while instrumenting, it must stop and report rather than widening scope.

## Scope check

- Over-scope: none. Two paths: `conftest.py` (the guard) and a new test file for it. The tempting adjacent change, editing the slow tests themselves, is left to `mat9bt` and `tf6x3a`.
- Under-scope: this plan does not make the suite faster. Total wall time is dominated by genuine subprocess work (F-03) and will not move. It does not change `-n auto`, the `worksteal` distribution, or the marker filters. It also does not eliminate load-dependent flakiness generally: a test that races on a shared resource rather than on CPU is untouched by a timer change of any kind.

## Required tests / validation

Every validation item demands PASTED runner output, never a claim. Drive the guard through real pytest subprocesses (`subprocess.run([sys.executable, "-m", "pytest", ...])`) and assert on their exit codes and output, never by reading `conftest.py` as text (P16). Run the new file focused with `python3 -m pytest tests/test_hang_guard_budget.py` and also under `-n 2`, since the guard must behave identically in a worker. Run the whole suite bare (`python3 -m pytest`) and reconcile against the F-12 baseline of `3 failed, 4624 passed, 2 skipped` with the three nodeids named. Confirm the four pre-existing `@pytest.mark.timeout` tests pass unedited. Leave `git status --short` clean of scratch probe files.

## Spec / documentation sync

N/A with reason: no `.spec.md` governs the hang guard. A search for the guard's identifiers across `.aw/records/specs/` finds nothing, and `AW_TEST_TIMEOUT` has no consumer outside `conftest.py` itself (no workflow, `Makefile` target, or runner module references it), so no documented contract changes. The durable record of WHY the guard measures CPU, what each budget catches, and the deadlock blind spot that keeps the wall arm alive is the rationale comment E-03 and E-07 require in `conftest.py`, matching the existing convention there of documenting each design decision beside the incident that forced it. `CONTRIBUTING.md` and `AGENTS.md` describe how to RUN the suite, not how the guard measures, so neither needs an edit.

## Open questions

### OQ-01: Should the wall ceiling be retained at all, or should the guard become CPU-only?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT, retain it. F-05 ran the experiment: with the wall arm disabled and a 3s CPU budget, a test blocked on an `Event` consumed no CPU, never tripped the timer, and ran to its own 45s completion with the guard silent. A deadlock is precisely the shape of hang that costs a whole unattended turn, so a CPU-only guard would reintroduce the failure the guard was built for. The ceiling stays, raised and re-aimed: it is a liveness check, not a cost control.

### OQ-02: Should an existing `@pytest.mark.timeout(500)` now mean 500s of CPU or 500s of wall?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED, CPU, and the four existing users are safe either way. All four are subprocess-heavy tests whose parent spends almost no CPU (F-04 shows this class measuring `0.00` self-CPU), so reading their marker as a CPU budget makes it generous rather than tight: no existing marker becomes harder to satisfy, and none needs editing. The reading is also the intent-preserving one, since every marker in the tree was added to say "this test legitimately does a lot of work". E-04 keeps the wall ceiling separately addressable so a test that genuinely needs a longer LIVENESS allowance can still ask for one, and V-04 verifies all four pass unedited rather than assuming it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [ ] V-01 validates E-01
  - Required evidence: paste four measurements for `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` at the execution head: isolated wall, isolated CPU, in-suite wall (a `--durations` line from a bare run), and in-suite CPU. State the wall inflation ratio and the CPU agreement. The claim to confirm or refute is F-02's: wall roughly doubles while CPU moves by about 1 percent. If CPU is what inflates, STOP AND REPORT rather than proceeding, because the remedy would then be aimed at the wrong dimension.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the rewritten guard hook in full. Confirm by reading it that both timers are armed, that BOTH previous signal handlers are restored and BOTH timers cancelled on every exit path including exceptions, and that each handler's message names WHICH budget was exceeded. Confirm every preserved property explicitly, one line each: `faulthandler` all-thread dump on first fire; `TestHangTimeout` still deriving from `BaseException` (and say why: an `Exception` was swallowed for about 20s); the 1.0s repeating interval on both timers (and why: a one-shot alarm did not stop the original hang); no use of `KeyboardInterrupt`; main-thread-only and signal-availability preconditions; and a stand-down when a test has installed its own handler for EITHER signal. A missing restore is the specific defect to hunt here, because a leaked `SIGPROF` handler would corrupt every later test in the same worker.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the two budget constants and the rationale comment. State the CPU budget's headroom ratio against the 28.61s worst observed self-CPU (F-03) and the wall ceiling's ratio against the worst observed wall time (F-03's `60.96s`) and against the runner's stall budget. Re-derive the census at the execution head rather than transcribing F-03: paste the worst self-CPU figure you measured. If any test's self-CPU now exceeds the chosen budget, the budget is wrong and must be resized before proceeding.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: show by RUN, not by reading, that `AW_TEST_TIMEOUT=<n>` still lowers the budget, that `AW_TEST_TIMEOUT=0` still disables the guard entirely, and that `@pytest.mark.timeout(<n>)` still overrides per test. State which budget each spelling now addresses and how the wall ceiling is addressed separately. Then paste a green run of all four pre-existing marker users (`tests/test_exit_contract_conformance.py` and the two in `tests/test_json_surface_leak_posture.py`, the former requiring `-m slow` or `-m ''` since it is deselected by default) and confirm with `git diff --name-only` that neither file was edited. A marker user that needed editing to stay green means the override semantics changed incompatibly.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `tests/test_hang_guard_budget.py` and its green run, BOTH serially and under `-n 2`, with output for each. Confirm in writing that it contains no `inspect`, `ast`, regex, or substring read of `conftest.py` and asserts only on subprocess output and exit codes (P16). The suite must include and be shown to cover all six classes: CPU runaway CAUGHT and named; sleeping test well past the CPU budget but inside the wall ceiling NOT caught (the central new behavior); zero-CPU deadlock CAUGHT by the wall arm; `0` disables; marker lowers; message names the budget. THEN PROVE THE TESTS ARE MUTATION-SENSITIVE: break the guard (for example cancel the CPU timer immediately, or arm `ITIMER_VIRTUAL` instead of `ITIMER_PROF`) and paste the resulting failures, showing which cases fail and which still pass. Revert and re-paste green. A test suite for a guard that cannot detect a disabled guard is worthless, and this item is not satisfied by a passing run alone.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste a bare `python3 -m pytest` summary reconciled against F-12's `3 failed, 4624 passed, 2 skipped` with the three nodeids named, plus the `--durations` line for the target nodeid. The target must be ABSENT from the failure list, and the new test file's additions must account for the rise in the passed count. Any NEW failure is a stop-and-report condition, not something to explain away. Separately paste the injection half: a scratch runaway test caught by the guard under the SAME configuration as that suite run, with the guard's message. Both halves are required, because the suite half alone cannot distinguish a fixed guard from a disabled one. Delete the scratch test and paste `git status --short` proving the tree is clean of it.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: quote the comment text documenting the blind spot. Confirm it states plainly that a CPU budget cannot see a test blocked on I/O, a lock, or a child process; that this is why the wall ceiling is retained; and that the ceiling is deliberately too loose to serve as a cost control. Confirm it cites the measurement behind the claim (F-05's 45s deadlock running to completion under a CPU-only guard), so a future reader tempted to delete the wall arm as redundant finds the experiment rather than an assertion.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. The suite's per-test hang guard charges a test for WALL-CLOCK time, so when the suite's own `-n auto` parallelism saturates the machine, a correct test is failed for waiting on a CPU it was never given. Measured here: the statusline sweep takes 29.53s alone and 66.53s in-suite while consuming the SAME 28s of CPU, and that one test has been reported red across at least 12 executed plans, each costing an agent a triage round trip. This plan changes the guard's cost DIMENSION, not its budget: a load-invariant CPU budget on `ITIMER_PROF` measures the work a test does, and a generous wall ceiling is RETAINED and re-aimed at liveness. It touches `conftest.py` and adds the guard's first-ever tests; NO production code changes. The tradeoff is measured and stated rather than glossed: a CPU budget is provably blind to a zero-CPU deadlock, demonstrated by a 45s `Event` wait that a CPU-only guard let run to completion untouched, which is exactly why the wall arm survives. WHAT IS DELIBERATELY NOT HERE: the swept sweep's own 7,776-row cost (owned by pending plan `mat9bt`, complementary and non-overlapping, see F-09); any re-marking of the `fields`/`verbose` reach tests (carried by `tf6x3a`); any claim to make the suite faster, since its wall time is dominated by genuine subprocess work; and any closure of the duplicate backlog item `cqgr7f`, which is a maintainer's call. ONE THING A REVIEWER SHOULD WEIGH EXPLICITLY: `mat9bt`'s gate prose says not to raise `_DEFAULT_TEST_TIMEOUT` in `conftest.py`, on the reasoning that a bigger global budget blinds the guard. This plan does not raise the wall budget to accommodate a slow test; it changes what is measured, which addresses that objection's substance rather than evading it. If the reviewer disagrees, this plan is the one to reject, because `mat9bt` stands alone without it.

EXECUTION CONTRACT. Commit only `conftest.py` and `tests/test_hang_guard_budget.py` through `aw commit <plan> -- conftest.py tests/test_hang_guard_budget.py`; never `git add -A` and never push. Paste ACTUAL runner output for every `V-*` item; a claimed pass with no pasted output fails the gate. Do NOT edit any test to make it fit the new budgets, and in particular do not touch `tests/test_statusline_behavior.py` (that file belongs to `mat9bt`) or the four existing `@pytest.mark.timeout` users: if one of them needs editing to stay green, the override semantics changed incompatibly and that is a stop-and-report condition. Do not remove the wall ceiling as redundant (F-05 prices that at a real deadlock class). Do not weaken any preserved guard property: the `BaseException` base, the repeating re-raise, the `faulthandler` dump, the main-thread precondition, or the own-handler stand-down. Do not touch anything under `agent_workflows/`; if instrumenting appears to reveal a genuine product defect, STOP AND REPORT rather than widening scope. Delete every scratch probe file and prove the tree is clean.

POST-GATE LIFECYCLE. Run `aw ipd begin` before implementing and `aw ipd finalize` after every `V-*` reads `pass`, which performs the path-scoped commit and the move to `.aw/records/plans/executed/`. Do not hand-edit terminal state or move the file manually. Before finalizing, confirm `aw ipd lint --phase pre-transition` conforms and reconcile the bare-suite result against the F-12 baseline (`3 failed, 4624 passed, 2 skipped`, the three nodeids named there). Backlog item `mu4k1g` carries `- Blocks-Release: next` and this plan inherits it, so the gate travels with this plan and is discharged when it reaches `executed`.
