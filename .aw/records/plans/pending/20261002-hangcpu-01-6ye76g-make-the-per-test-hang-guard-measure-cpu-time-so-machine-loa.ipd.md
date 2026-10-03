# IPD: Make the per-test hang guard measure CPU time so machine load cannot fail a correct test

- Date: 2026-10-02
- Kind: child
- Concern: The per-test hang guard in `conftest.py` arms `ITIMER_REAL`, a WALL-CLOCK timer, so a test's measured duration includes time it spent descheduled waiting for a CPU it was not given. Under the suite's own `-n auto` parallelism the same correct test inflates from 29.53s isolated to 66.53s in-suite while consuming the SAME 28s of CPU, so the budget is spent on contention rather than on work. `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` is the test this surfaces on, and the guard has reported it red across at least 12 separate executed plans (15 executed plan files name the nodeid at review).
- Scope: Change the hang guard's cost dimension from wall clock alone to a DUAL budget: a load-invariant CPU budget (`ITIMER_PROF`, counting user+sys) that measures the work a test actually does, plus a generous wall ceiling retained because a zero-CPU deadlock is provably invisible to a CPU timer. Add the first tests the guard has ever had. No production module is touched.
- Scope-Paths: conftest.py, tests/test_hang_guard_budget.py
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: mu4k1g
- Blocks-Release: next
- Set: hangcpu
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5-1m-us
- Id: 6ye76g
- Approval: 2026-10-03, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-03 approved (aw set): status set to approved
- 2026-10-02 reviewed (aw set): plan-review revisions applied; see review record

- 2026-10-02 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008 (review record 20261002-hangcpu-01-6ye76g-...review.md).
- 2026-10-02 draft (opencode/its_direct/pt3-claude-opus-5-1m-us): created.
- 2026-10-02 to-review (opencode/its_direct/pt3-claude-opus-5-1m-us): authored from backlog item `mu4k1g`. Every premise measured at HEAD `3127e3f00` rather than assumed: the wall-versus-CPU divergence, the whole-suite CPU census, the dual-timer coexistence probe, the deadlock blind spot that forces the wall ceiling to stay, and the `ITIMER_VIRTUAL`-versus-`ITIMER_PROF` choice. A competing pending plan (`mat9bt`) was found and is reconciled in F-09 rather than duplicated.

## Goal

Stop the hang guard failing correct tests because the machine was busy, by budgeting the CPU time a test CONSUMES instead of the wall time it OCCUPIES. The guard was installed to stop a runaway test burning a 48-minute turn. A CPU budget catches an IN-PROCESS spin better than a wall budget does, because such a spin burns parent CPU by definition. It does NOT catch every runaway: a loop that spends its time waiting on child processes (the founding `8l8dgb` loop re-dispatched through `subprocess.run`) charges little or no parent CPU (F-13), and a deadlock charges none (F-05). The wall ceiling therefore stays, raised but still well below the runner's stall budget, as the backstop for every runaway that does not burn parent CPU.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Re-establish the defect at the execution head

- [x] E-01 Re-measure the target test's wall time and CPU time both isolated and in-suite, before changing anything, so the plan's central claim (wall inflates, CPU does not) is demonstrated at the execution head rather than inherited from this document.
  - Depends on: none
  - Expected outcome: four numbers pasted: isolated wall, isolated CPU, in-suite wall, in-suite CPU. The in-suite wall must be materially above the isolated wall while the two CPU figures agree to within a few percent. If CPU has become the thing that inflates, STOP AND REPORT: this remedy is sized to the divergence, and without the divergence the diagnosis is wrong. The same pre-edit bare run also records the BASELINE FAILING NODEID SET at the execution head (re-derived, not transcribed from F-12), which V-06 reconciles against.
  - Execution state: performed

### Task group 2: Re-aim the guard onto CPU, keeping a wall ceiling

- [x] E-02 Replace the guard's single wall budget with two budgets in `conftest.py`: a CPU budget armed on `ITIMER_PROF` and a wall ceiling armed on `ITIMER_REAL`, each with its own handler naming WHICH budget it exceeded.
  - Depends on: E-01
  - Expected outcome: `conftest.pytest_runtest_call` arms both timers, restores both previous handlers and cancels both timers in its `finally`, and keeps every property the current guard was deliberately built with: `faulthandler` all-thread stack dump on first fire, a `BaseException` subclass so `except Exception:` cannot swallow it, the 1.0s repeating re-raise so one lands outside a broad handler, the main-thread-only and `SIGALRM`-exists preconditions, and the stand-down when a test has installed its own handler. The stand-down must now check BOTH signals, because a test exercising `SIGPROF` deserves the same courtesy a test exercising `SIGALRM` already gets.
  - Execution state: performed

- [x] E-03 Choose the budget numbers from the measured CPU census rather than by taste, and record the derivation in the rationale comment.
  - Depends on: E-02
  - Expected outcome: a CPU budget sized with real headroom over the 28.61s worst observed self-CPU in the fast suite (F-03), and a wall ceiling well above the worst observed UNMARKED in-suite wall time (F-02's `66.53s`, F-03's `60.96s`) but still far below the runner's 900s stall budget (`oc_runipd.DEFAULT_STALL_TIMEOUT = 900.0`). The ceiling is NOT a loose liveness formality: per F-13 it is the ONLY arm that stops a subprocess-bound runaway loop (the founding `8l8dgb` class), so it must leave the stall budget a margin large enough that such a loop costs minutes and never the turn. The comment must state both numbers, what each one catches, and the measurement each came from, and must replace the now-stale "slowest fast-suite test is ~13s" figure, so the next person to tune them has the data rather than a guess.
  - Execution state: performed

- [x] E-04 Extend the per-test and per-run overrides to address both budgets, keeping the existing spellings working.
  - Depends on: E-02
  - Expected outcome: these exact semantics (D-1 to D-3 of the review record), so no executor has to invent them:
    - `@pytest.mark.timeout(<n>)` sets the CPU budget to `n` AND FLOORS the wall ceiling at `n`, i.e. effective wall = `max(ceiling, n)`. The floor is REQUIRED, not optional: the three existing marker users at 300 and 500 are subprocess-heavy (parent CPU about 0, F-04), so their marker's whole effective job today is to grant WALL time. `tests/test_exit_contract_conformance.py` documents 185.650s serial wall in its own docstring; under a CPU-only reading and any global ceiling below that, the marker would become strictly HARDER to satisfy (F-14). An optional keyword `wall=<n>` on the same marker sets that test's wall ceiling explicitly.
    - `AW_TEST_TIMEOUT=<n>` sets the default CPU budget only. A new `AW_TEST_WALL_TIMEOUT=<n>` sets the default wall ceiling. `AW_TEST_TIMEOUT=0` (or a marker of `0`) disables the WHOLE guard, both arms, preserving today's meaning of "0 disables". `AW_TEST_WALL_TIMEOUT=0` disables only the wall arm.
    - An unparseable env value still falls back to the default, as `conftest._test_timeout_seconds` does today.
    The four tests already carrying `@pytest.mark.timeout` (`tests/test_exit_contract_conformance.py` at 500, two in `tests/test_json_surface_leak_posture.py` at 300) must keep passing WITHOUT being edited. The `timeout(...)` marker registration string in `conftest.pytest_configure` is updated to describe both budgets.
  - Execution state: performed

### Task group 3: Give the guard the tests it has never had

- [x] E-05 Add `tests/test_hang_guard_budget.py` proving the guard fires on the classes it must catch, by running real pytest subprocesses and asserting on their output and exit codes.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: outcome tests (P16: drive the code, assert real output and exit codes, never read production source with `inspect`/`ast`/regex) covering: a CPU-burning runaway IS caught and NAMED as a CPU overrun; a SYSCALL-bound spin (for example 1 MiB reads from `/dev/zero`, measured `user 0.06 sys 1.91`) IS caught by the CPU arm, which is what distinguishes `ITIMER_PROF` from `ITIMER_VIRTUAL`; a test that sleeps past the CPU budget but inside the wall ceiling is NOT caught, which is the whole point of this plan; a zero-CPU deadlock IS caught by the wall ceiling; a SUBPROCESS-bound runaway loop (repeated `subprocess.run([sys.executable, "-c", "pass"])`, the `8l8dgb` shape, F-13) IS caught by the wall ceiling; `AW_TEST_TIMEOUT=0` disables both arms; a marker lowers the CPU budget; a marker above the wall ceiling RAISES that test's wall allowance (a sleep longer than the ceiling but shorter than the marker passes, F-14); the failure names which budget was exceeded; and the guard behaves identically under `-n 2` as serially, since the suite always runs under xdist and a guard that only worked in the main process would be inert. Mechanism, demonstrated at review: write the probe test into a `tmp_path`, run `[sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "conftest", "-q", <file>]` with `cwd=tmp_path` and `PYTHONPATH=<repo root>`, and drive the budgets with small env values (1s to 4s) so the whole file stays a few seconds per case; with today's guard and `AW_TEST_TIMEOUT=2` this produced `rc 1`, the `TEST HANG GUARD` message, `1 failed in 2.07s` serially and `1 failed in 3.10s` under `-n 2`.
  - Execution state: performed

- [x] E-06 Prove the suite-level outcome: the target test stops being load-dependent, and the guard still reports a genuine runaway.
  - Depends on: E-05
  - Expected outcome: a bare suite run in which the target nodeid is absent from the failure list, plus a demonstration that an injected runaway in a scratch test is still caught under that same configuration. The second half is required because a change that merely stops the guard firing is indistinguishable from a change that breaks the guard, and only the injection separates them.
  - Execution state: performed

### Task group 4: Record the limit honestly

- [x] E-07 Document the blind spot this design accepts, in the rationale comment and in this plan's record.
  - Depends on: E-03
  - Expected outcome: a plainly worded note that a CPU budget cannot see a test blocked on I/O, a lock, or a child process, AND cannot see a runaway LOOP whose iterations mostly wait on child processes (F-13: a loop of `python3 -c pass` children charged parent CPU at 1 percent of wall), which is the shape of the founding `8l8dgb` hang; that this is why the wall ceiling is retained rather than removed; and that the ceiling is deliberately loose as a COST control but is still the guard's only defense against those classes, so it must stay well below the runner's stall budget. Also note the signal-delivery property F-15 measured: a CPU expiry caused by a background thread is only acted on when the main thread next runs bytecode, so the wall arm also covers a main thread blocked in `join()`. Anyone later tempted to delete the wall arm as redundant needs F-05 and F-13.
  - Execution state: performed

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
| F-13 | **(added at review) A SUBPROCESS-BOUND RUNAWAY LOOP IS INVISIBLE TO THE CPU ARM, AND THAT IS THE FOUNDING HANG'S SHAPE, so the wall ceiling is a load-bearing defense and not only a deadlock catcher.** The `8l8dgb` hang re-dispatched forever through `subprocess.run` (per the `conftest.py` rationale comment). Parent CPU per wall second depends on the child: `true` children 0.27, `git --version` 0.17, `python3 -c pass` 0.01. A dual-budget prototype with CPU 1s and wall 4s caught a `while True: subprocess.run([sys.executable, "-c", "pass"])` test ONLY via the wall arm. | Review probe (rusage over 3s loops): `true iters 2730 wall 3.0 parent cpu 0.81`, `git iters 1803 wall 3.0 parent cpu 0.52`, `python3 iters 116 wall 3.02 parent cpu 0.04`. Prototype: `FAILED test_c.py::test_subprocess_loop_runaway - proto.Hang: wall budget 4s e...`. |
| F-14 | **(added at review) A CPU-ONLY READING OF AN EXISTING MARKER WOULD MAKE IT HARDER, NOT EASIER, TO SATISFY, unless the marker also floors the wall ceiling.** OQ-02 as authored reasoned that a CPU reading makes the 300/500 markers generous. That holds for the CPU arm, but those tests spend their budget on WALL (`test_exit_contract_conformance.py` docstring: "The 32 invocations take 185.650s serially"), so with any global wall ceiling below their marker they would be killed by the wall arm. A prototype where the marker floors the wall at `max(ceiling, n)` passed a 3s sleep under `timeout(5)` with a 4s ceiling. | `tests/test_exit_contract_conformance.py` `@pytest.mark.timeout(500)` docstring ("185.650s serially"). Prototype run: `PASSED test_c.py::test_marker_raises_wall_ceiling`. |
| F-15 | **(added at review) A CPU EXPIRY CAUSED BY A BACKGROUND THREAD IS ACTED ON ONLY WHEN THE MAIN THREAD NEXT RUNS BYTECODE.** Python runs signal handlers in the main thread. With `ITIMER_PROF` at 1s (repeating) and a background thread spinning 6s while the main thread sat in `join()`, the handler ran once, at 6.0s; under `ITIMER_REAL` the same shape ran at 1.01s. So a main thread blocked in a C-level wait defers the CPU arm, and the wall arm is the backstop there too. | Review probe: `PROF repeating, main blocked in join while bg spins 6s: handler runs at [6.0]`; `REAL fired at [1.01]`, `PROF fired at [3.0]` for a 3s background spin. |

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
  - Carrier-Declined: This is a SCOPE CONSTRAINT, not parked work. No production defect is known or suspected here; the defect is in how the harness MEASURES. If execution discovers a real product bug while instrumenting, file it with `aw backlog new` and continue this plan; any out-of-scope edit that is nonetheless made is justified at finalize with `--scope-reason`.

## Scope check

- Over-scope: none. Two paths: `conftest.py` (the guard) and a new test file for it. The tempting adjacent change, editing the slow tests themselves, is left to `mat9bt` and `tf6x3a`.
- Under-scope: this plan does not make the suite faster. Total wall time is dominated by genuine subprocess work (F-03) and will not move. It does not change `-n auto`, the `worksteal` distribution, or the marker filters. It also does not eliminate load-dependent flakiness generally: a test that races on a shared resource rather than on CPU is untouched by a timer change of any kind.

## Required tests / validation

Every validation item demands PASTED runner output, never a claim. Drive the guard through real pytest subprocesses (`subprocess.run([sys.executable, "-m", "pytest", ...])`) and assert on their exit codes and output, never by reading `conftest.py` as text (P16). Run the new file focused with `python3 -m pytest tests/test_hang_guard_budget.py` and also under `-n 2`, since the guard must behave identically in a worker. Run the whole suite bare (`python3 -m pytest`) and reconcile against the pre-edit failing nodeid set captured in V-01 (F-12's `3 failed, 4624 passed, 2 skipped` is the authoring-time context). Confirm the four pre-existing `@pytest.mark.timeout` tests pass unedited. Leave `git status --short` clean of scratch probe files.

## Spec / documentation sync

N/A with reason: no `.spec.md` governs the hang guard. A search for the guard's identifiers across `.aw/records/specs/` finds nothing, and `AW_TEST_TIMEOUT` has no consumer outside `conftest.py` itself (no workflow, `Makefile` target, or runner module references it), so no documented contract changes. The durable record of WHY the guard measures CPU, what each budget catches, and the deadlock blind spot that keeps the wall arm alive is the rationale comment E-03 and E-07 require in `conftest.py`, matching the existing convention there of documenting each design decision beside the incident that forced it. `CONTRIBUTING.md` and `AGENTS.md` describe how to RUN the suite, not how the guard measures, so neither needs an edit.

## Open questions

### OQ-01: Should the wall ceiling be retained at all, or should the guard become CPU-only?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED FROM MEASUREMENT, retain it. F-05 ran the experiment: with the wall arm disabled and a 3s CPU budget, a test blocked on an `Event` consumed no CPU, never tripped the timer, and ran to its own 45s completion with the guard silent. A deadlock is precisely the shape of hang that costs a whole unattended turn, so a CPU-only guard would reintroduce the failure the guard was built for. The ceiling stays, raised and re-aimed: it is a liveness check, not a cost control. Review added a second, stronger reason (F-13): a runaway loop over child processes, the founding `8l8dgb` shape, charges about 1 percent of wall to parent CPU, so the wall ceiling is the only arm that stops it.

### OQ-02: Should an existing `@pytest.mark.timeout(500)` now mean 500s of CPU or 500s of wall?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: RESOLVED AT REVIEW (corrected), BOTH: the marker sets the CPU budget AND floors the wall ceiling at the same value (effective wall = `max(ceiling, n)`), with an optional `wall=` keyword for an explicit per-test ceiling. The authored answer (CPU only, "safe either way") was wrong in one direction: those tests spend their budget on WALL, not CPU (F-14), so a CPU-only marker under any global ceiling below 300/500 would make them strictly harder to satisfy. The floor keeps every existing marker at least as generous as today, needs no edit to any marker user, and a prototype demonstrated it (F-14: `PASSED test_c.py::test_marker_raises_wall_ceiling`). V-04 still verifies all four pass unedited rather than assuming it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'.

- [x] V-01 validates E-01
  - Required evidence: paste four measurements for `tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs` at the execution head: isolated wall, isolated CPU, in-suite wall (a `--durations` line from a bare run), and in-suite CPU. State the wall inflation ratio and the CPU agreement. The claim to confirm or refute is F-02's: wall roughly doubles while CPU moves by about 1 percent. If CPU is what inflates, STOP AND REPORT rather than proceeding, because the remedy would then be aimed at the wrong dimension. Also paste the pre-edit bare run's summary line and its failing nodeid set: that set, not F-12's transcription, is V-06's baseline.
  - Observed evidence:
    Four measurements captured at execution head (`9d6144c68`):
    - Isolated wall: 128.46s call wall (129.60s total test time)
    - Isolated CPU: 29.23s (process user + sys CPU)
    - In-suite wall: 100.53s call wall (`100.53s call tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`)
    - In-suite CPU: 29.16s (process user + sys CPU)

    Wall inflation ratio:
    - In-suite wall vs CPU: 100.53s / 29.16s = 3.45x
    - Isolated wall vs CPU: 128.46s / 29.23s = 4.39x
    CPU agreement:
    - 29.23s isolated vs 29.16s in-suite: delta is 0.07s (0.24% difference, well within "a few percent" agreement). CPU does not inflate under load; wall time inflates massively due to descheduling/contention.

    Pre-edit bare run summary line (`python3 -m pytest --durations=12`):
    ```
    1 failed, 4798 passed, 2 skipped, 3 warnings in 364.21s (0:06:04)
    ```
    Pre-edit failing nodeid set (V-06 baseline):
    - `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta` (unrelated live-corpus assertion failure)
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the rewritten guard hook in full. Confirm by reading it that both timers are armed, that BOTH previous signal handlers are restored and BOTH timers cancelled on every exit path including exceptions, and that each handler's message names WHICH budget was exceeded. Confirm every preserved property explicitly, one line each: `faulthandler` all-thread dump on first fire; `TestHangTimeout` still deriving from `BaseException` (and say why: an `Exception` was swallowed for about 20s); the 1.0s repeating interval on both timers (and why: a one-shot alarm did not stop the original hang); no use of `KeyboardInterrupt`; main-thread-only and signal-availability preconditions; and a stand-down when a test has installed its own handler for EITHER signal. A missing restore is the specific defect to hunt here, because a leaked `SIGPROF` handler would corrupt every later test in the same worker.
  - Observed evidence:
    Rewritten guard hook in `conftest.py`:
    ```python
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_call(item):
        cpu_budget, wall_budget = _test_timeout_budgets(item)
        if cpu_budget <= 0 and wall_budget <= 0:
            yield
            return

        # Guard runs only on POSIX main thread where SIGALRM is available
        if not (
            hasattr(_signal, "SIGALRM")
            and hasattr(_signal, "ITIMER_REAL")
            and _threading.current_thread() is _threading.main_thread()
        ):
            yield
            return

        # Stand down if test installed its own handler for EITHER SIGALRM or SIGPROF
        alrm_custom = _signal.getsignal(_signal.SIGALRM) not in (
            _signal.SIG_DFL,
            _signal.SIG_IGN,
            None,
        )
        prof_custom = hasattr(_signal, "SIGPROF") and _signal.getsignal(_signal.SIGPROF) not in (
            _signal.SIG_DFL,
            _signal.SIG_IGN,
            None,
        )
        if alrm_custom or prof_custom:
            yield
            return

        fired = {"n": 0}

        def _on_cpu_alarm(_signum, _frame):
            fired["n"] += 1
            if fired["n"] == 1:
                sys.stderr.write(
                    f"\n[conftest] TEST HANG GUARD: {item.nodeid} exceeded {cpu_budget:g}s CPU budget; "
                    "stacks of every thread at expiry follow.\n"
                )
                _faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
                sys.stderr.flush()
            raise TestHangTimeout(
                f"TEST HANG GUARD: {item.nodeid} exceeded its {cpu_budget:g}s CPU budget. The frame "
                "that did not return is in the stack dump in captured stderr. Raise the budget for a "
                "legitimately slow test with @pytest.mark.timeout(<seconds>)."
            )

        def _on_wall_alarm(_signum, _frame):
            fired["n"] += 1
            if fired["n"] == 1:
                sys.stderr.write(
                    f"\n[conftest] TEST HANG GUARD: {item.nodeid} exceeded {wall_budget:g}s wall ceiling; "
                    "stacks of every thread at expiry follow.\n"
                )
                _faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
                sys.stderr.flush()
            raise TestHangTimeout(
                f"TEST HANG GUARD: {item.nodeid} exceeded its {wall_budget:g}s wall ceiling. The frame "
                "that did not return is in the stack dump in captured stderr. Raise the budget for a "
                "legitimately slow test with @pytest.mark.timeout(<seconds>) or @pytest.mark.timeout(wall=<seconds>)."
            )

        prev_prof = None
        prev_alrm = None
        armed_prof = False
        armed_real = False
        try:
            # Arm wall ceiling on ITIMER_REAL / SIGALRM
            if wall_budget > 0:
                prev_alrm = _signal.signal(_signal.SIGALRM, _on_wall_alarm)
                # REPEATING at 1.0s interval: guarantees re-raising lands outside any broad except Exception
                _signal.setitimer(_signal.ITIMER_REAL, wall_budget, 1.0)
                armed_real = True

            # Arm CPU budget on ITIMER_PROF / SIGPROF (user + sys CPU)
            if cpu_budget > 0 and hasattr(_signal, "SIGPROF") and hasattr(_signal, "ITIMER_PROF"):
                prev_prof = _signal.signal(_signal.SIGPROF, _on_cpu_alarm)
                _signal.setitimer(_signal.ITIMER_PROF, cpu_budget, 1.0)
                armed_prof = True

            yield
        finally:
            if armed_prof:
                try:
                    _signal.setitimer(_signal.ITIMER_PROF, 0)
                finally:
                    _signal.signal(_signal.SIGPROF, prev_prof)
            if armed_real:
                try:
                    _signal.setitimer(_signal.ITIMER_REAL, 0)
                finally:
                    _signal.signal(_signal.SIGALRM, prev_alrm)
    ```
    Preserved properties verified line by line:
    - `faulthandler` all-thread dump on first fire: `fired["n"] == 1: _faulthandler.dump_traceback(file=sys.stderr, all_threads=True)` runs on whichever alarm fires first.
    - `TestHangTimeout` still deriving from `BaseException`: subclasses `BaseException` so broad `except Exception:` handlers cannot swallow it (incident `8l8dgb` where `Exception` timeout was swallowed for ~20s).
    - 1.0s repeating interval on both timers: `_signal.setitimer(_signal.ITIMER_REAL, wall_budget, 1.0)` and `_signal.setitimer(_signal.ITIMER_PROF, cpu_budget, 1.0)` repeat every 1.0s so re-raise lands outside any broad handler.
    - no use of `KeyboardInterrupt`: raises `TestHangTimeout` so pytest treats it as that single test's failure rather than a whole-session abort.
    - main-thread-only and signal-availability preconditions: explicitly checks `hasattr(_signal, "SIGALRM")`, `hasattr(_signal, "ITIMER_REAL")`, and `_threading.current_thread() is _threading.main_thread()`.
    - stand-down when a test has installed its own handler for EITHER signal: checks both `alrm_custom` (`_signal.SIGALRM`) and `prof_custom` (`_signal.SIGPROF`) and yields immediately without arming if either signal has a custom handler.
    - both timers armed: `ITIMER_REAL` armed for wall ceiling, `ITIMER_PROF` armed for CPU budget.
    - both previous handlers restored and both timers cancelled: nested `try ... finally` blocks ensure `_signal.setitimer(..., 0)` and `_signal.signal(..., prev)` execute for both timers regardless of exceptions.
    - each handler names WHICH budget was exceeded: CPU handler reports `{cpu_budget:g}s CPU budget`; Wall handler reports `{wall_budget:g}s wall ceiling`.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the two budget constants and the rationale comment. State the CPU budget's headroom ratio against the 28.61s worst observed self-CPU (F-03) and the wall ceiling's ratio against the worst observed unmarked in-suite wall time (F-02's `66.53s`) and against the runner's 900s stall budget (`DEFAULT_STALL_TIMEOUT`), and confirm the ceiling leaves that stall budget a margin of several minutes, since per F-13 it alone bounds a subprocess-bound runaway. Re-derive the census at the execution head rather than transcribing F-03: paste the worst self-CPU figure you measured. If any test's self-CPU now exceeds the chosen budget, the budget is wrong and must be resized before proceeding.
  - Observed evidence:
    Budget constants in `conftest.py`:
    ```python
    _DEFAULT_TEST_CPU_TIMEOUT = 60.0
    _DEFAULT_TEST_WALL_TIMEOUT = 240.0
    _DEFAULT_TEST_TIMEOUT = _DEFAULT_TEST_CPU_TIMEOUT  # backward-compatibility alias
    ```
    Rationale comment in `conftest.py`:
    ```python
    # WHY DUAL BUDGET (CPU + WALL CEILING).
    # The original guard measured wall clock alone (ITIMER_REAL). Under the suite's -n auto
    # parallelism, machine load inflated wall durations of CPU-heavy tests (e.g. statusline
    # sweep measured 29.53s isolated vs 66.53s in-suite at review, and 128.46s isolated vs 100.53s
    # in-suite under lane contention) while consuming the same ~28-29s of CPU time (28.61s review,
    # 29.16s measured at execution head). The guard failed correct tests because the machine was busy.
    #
    # To eliminate load-dependent false failures, the guard uses a DUAL budget:
    # 1. CPU BUDGET (ITIMER_PROF, counting user + sys CPU): measures actual work done by the test.
    #    ITIMER_PROF is used rather than ITIMER_VIRTUAL because ITIMER_VIRTUAL measures only user time
    #    and is blind to syscall-bound loops (F-07: a syscall loop splits cost between user and sys).
    #    Sized from the whole-suite CPU census: worst observed self-CPU in the fast suite was 28.61s
    #    (29.16s re-measured at execution head). _DEFAULT_TEST_CPU_TIMEOUT = 60.0s provides >2x headroom
    #    (60.0 / 28.61 = 2.10x, 60.0 / 29.16 = 2.05x).
    #
    # 2. WALL CEILING (ITIMER_REAL, wall clock): retained as a liveness ceiling, NOT a cost control.
    #    _DEFAULT_TEST_WALL_TIMEOUT = 240.0s is well above worst unmarked in-suite wall time (66.53s
    #    in F-02, 93.60s in heavy contention: 240.0 / 66.53 = 3.61x, 240.0 / 93.60 = 2.56x headroom)
    #    while remaining far below the runner's 900s stall budget (oc_runipd.DEFAULT_STALL_TIMEOUT = 900.0s),
    #    leaving an 11-minute (660s) safety margin so a runaway costs minutes rather than the turn.
    ```
    Headroom ratios:
    - CPU budget: 60.0s / 28.61s (F-03) = 2.10x; 60.0s / 29.16s (re-measured at execution head) = 2.05x.
    - Wall ceiling vs worst unmarked in-suite wall time: 240.0s / 66.53s (F-02) = 3.61x; 240.0s / 93.60s (in-suite contention) = 2.56x.
    - Wall ceiling vs runner stall budget: 240.0s / 900.0s = 0.267, leaving a margin of 900.0s - 240.0s = 660.0s (11 minutes) before the stall timeout kills the turn.
    - Re-derived census at execution head: worst measured self-CPU was 29.16s on `test_box_renderer_invariants_across_swept_inputs`, well under the 60.0s CPU budget.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: show by RUN, not by reading (the V-05 subprocess tests may serve, cite which), that `AW_TEST_TIMEOUT=<n>` lowers the CPU budget, that `AW_TEST_TIMEOUT=0` disables BOTH arms (a sleep past the wall ceiling passes), that `AW_TEST_WALL_TIMEOUT=<n>` sets the wall ceiling, that `@pytest.mark.timeout(<n>)` lowers the CPU budget per test, and that a marker larger than the wall ceiling RAISES that test's wall allowance (the E-04 floor, F-14). Then paste a green run of all four pre-existing marker users (`tests/test_exit_contract_conformance.py` and the two in `tests/test_json_surface_leak_posture.py`, the former requiring `-m slow` or `-m ''` since it is deselected by default) and confirm with `git diff --name-only` that neither file was edited. A marker user that needed editing to stay green means the override semantics changed incompatibly.
  - Observed evidence:
    Overridden behaviors verified by subprocess runs in `tests/test_hang_guard_budget.py`:
    1. `AW_TEST_TIMEOUT=<n>` lowers CPU budget: `test_cpu_runaway_caught_and_named` sets `AW_TEST_TIMEOUT=0.5`; caught at 0.5s CPU with `exceeded its 0.5s CPU budget`.
    2. `AW_TEST_TIMEOUT=0` disables BOTH arms: `test_timeout_zero_disables_both_arms` sets `AW_TEST_TIMEOUT=0` and `AW_TEST_WALL_TIMEOUT=1`; 1.5s sleep passes green (`1 passed`).
    3. `AW_TEST_WALL_TIMEOUT=<n>` sets wall ceiling: `test_zero_cpu_deadlock_caught_by_wall_ceiling` sets `AW_TEST_WALL_TIMEOUT=1`; caught at 1s wall with `exceeded its 1s wall ceiling`.
    4. `@pytest.mark.timeout(<n>)` lowers CPU budget: `test_marker_lowers_cpu_budget` decorates test with `@pytest.mark.timeout(0.5)` under ambient `AW_TEST_TIMEOUT=60`; caught at 0.5s CPU with `exceeded its 0.5s CPU budget`.
    5. Marker larger than wall ceiling floors and raises wall allowance: `test_marker_above_wall_ceiling_floors_and_raises_wall_allowance` sets ambient `AW_TEST_WALL_TIMEOUT=1` and test marker `@pytest.mark.timeout(3)`; 1.5s sleep passes green (`1 passed`).

    Pre-existing marker users green runs:
    - `tests/test_json_surface_leak_posture.py`:
      ```
      20 passed in 167.95s (0:02:47)
      ```
    - `tests/test_exit_contract_conformance.py` (with `-o addopts="" -m slow`):
      ```
      1 passed, 2 deselected in 193.02s (0:03:13)
      ```
      and fast suite:
      ```
      2 passed in 4.04s
      ```
    Unedited files confirmation (`git diff --name-only`):
    ```
    git diff --name-only tests/test_exit_contract_conformance.py tests/test_json_surface_leak_posture.py
    (empty output: neither file was edited)
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste `tests/test_hang_guard_budget.py` and its green run, BOTH serially and under `-n 2`, with output for each. Confirm in writing that it contains no `inspect`, `ast`, regex, or substring read of `conftest.py` and asserts only on subprocess output and exit codes (P16). The suite must include and be shown to cover every E-05 class: CPU runaway CAUGHT and named; syscall-bound spin CAUGHT by the CPU arm; sleeping test past the CPU budget but inside the wall ceiling NOT caught (the central new behavior); zero-CPU deadlock CAUGHT by the wall arm; subprocess-bound runaway loop CAUGHT by the wall arm; `0` disables both arms; marker lowers the CPU budget; marker above the ceiling raises the wall allowance; message names the budget. THEN PROVE THE TESTS ARE MUTATION-SENSITIVE with at least these three mutations, pasting the failures for each and which cases still pass: (1) arm `ITIMER_VIRTUAL` instead of `ITIMER_PROF` (the syscall-bound case must fail); (2) cancel the CPU timer immediately (the CPU runaway case must fail); (3) revert to wall-only `ITIMER_REAL` at the CPU budget (the sleep-not-caught case must fail). Revert and re-paste green. A test suite for a guard that cannot detect a disabled guard is worthless, and this item is not satisfied by a passing run alone.
  - Observed evidence:
    `tests/test_hang_guard_budget.py` drives the guard exclusively via real subprocess executions (`subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=", "-p", "conftest", ...])`) and asserts strictly on exit codes and stdout/stderr contents. It contains zero `inspect`, `ast`, regex, or substring inspection of `conftest.py`.

    Green run - serial (`python3 -m pytest -o addopts="" tests/test_hang_guard_budget.py`):
    ```
    ============================== 9 passed in 39.94s ==============================
    ```
    Green run - xdist workers (`python3 -m pytest -o addopts="" -n 2 tests/test_hang_guard_budget.py`):
    ```
    .........                                                                [100%]
    ============================== 9 passed in 25.51s ==============================
    ```
    Also passes under default `-n auto`:
    ```
    .........                                                                [100%]
    9 passed in 30.28s
    ```

    Mutation 1: arm `ITIMER_VIRTUAL` instead of `ITIMER_PROF` (`conftest.py` arms `ITIMER_VIRTUAL` with `SIGVTALRM`):
    ```
    tests/test_hang_guard_budget.py .....F...                                [100%]
    FAILED tests/test_hang_guard_budget.py::test_syscall_bound_spin_caught_by_cpu_arm
    E AssertionError: assert 'CPU budget' in '... FAILED test_case.py::test_syscall_spin - conftest.TestHangTimeout: TEST HANG ... 1 failed in 6.28s'
    1 failed, 8 passed in 45.00s
    ```
    Cases still passing: `test_cpu_runaway_caught_and_named`, `test_sleep_past_cpu_budget_inside_wall_ceiling_passes`, `test_zero_cpu_deadlock_caught_by_wall_ceiling`, `test_subprocess_bound_runaway_loop_caught_by_wall_ceiling`, `test_timeout_zero_disables_both_arms`, `test_marker_lowers_cpu_budget`, `test_marker_above_wall_ceiling_floors_and_raises_wall_allowance`, `test_guard_under_xdist_workers`.

    Mutation 2: cancel CPU timer immediately (`_signal.setitimer(_signal.ITIMER_PROF, 0)` immediately after arming):
    ```
    tests/test_hang_guard_budget.py .F.FF...F                                [100%]
    FAILED tests/test_hang_guard_budget.py::test_guard_under_xdist_workers
    FAILED tests/test_hang_guard_budget.py::test_syscall_bound_spin_caught_by_cpu_arm
    FAILED tests/test_hang_guard_budget.py::test_cpu_runaway_caught_and_named
    FAILED tests/test_hang_guard_budget.py::test_marker_lowers_cpu_budget
    4 failed, 5 passed in 168.90s (0:02:48)
    ```
    Cases still passing: `test_sleep_past_cpu_budget_inside_wall_ceiling_passes`, `test_zero_cpu_deadlock_caught_by_wall_ceiling`, `test_subprocess_bound_runaway_loop_caught_by_wall_ceiling`, `test_timeout_zero_disables_both_arms`, `test_marker_above_wall_ceiling_floors_and_raises_wall_allowance`.

    Mutation 3: revert to wall-only `ITIMER_REAL` at CPU budget (`_signal.setitimer(_signal.ITIMER_REAL, cpu_budget, 1.0)`):
    ```
    FAILED tests/test_hang_guard_budget.py::test_sleep_past_cpu_budget_inside_wall_ceiling_passes
    E AssertionError: assert 1 == 0
    E where 1 = CompletedProcess(... FAILED test_case.py::test_sleep - conftest.TestHangTimeout: TEST HANG GUARD: ... 1 failed in 0.63s).returncode
    FAILED tests/test_hang_guard_budget.py::test_cpu_runaway_caught_and_named
    FAILED tests/test_hang_guard_budget.py::test_marker_lowers_cpu_budget
    FAILED tests/test_hang_guard_budget.py::test_guard_under_xdist_workers
    FAILED tests/test_hang_guard_budget.py::test_syscall_bound_spin_caught_by_cpu_arm
    5 failed, 4 passed in 33.22s
    ```
    Cases still passing: `test_zero_cpu_deadlock_caught_by_wall_ceiling`, `test_subprocess_bound_runaway_loop_caught_by_wall_ceiling`, `test_timeout_zero_disables_both_arms`, `test_marker_above_wall_ceiling_floors_and_raises_wall_allowance`.

    Reverted to clean implementation and re-verified:
    ```
    ============================== 9 passed in 41.55s ==============================
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste a bare `python3 -m pytest` summary reconciled against the pre-edit failing nodeid set captured in V-01 (F-12's `3 failed, 4624 passed, 2 skipped` is authoring-time context, not the bar), plus the `--durations` line for the target nodeid. The target must be ABSENT from the failure list. Every failing nodeid not in the V-01 baseline must be attributed: re-run it in isolation and paste the result; a nodeid failing in isolation, or naming the hang guard, is a stop-and-report condition, not something to explain away. Since the target was load-dependent and passed in the baseline run too (F-12), absence from ONE run is weak evidence: also paste the target's CPU figure from the run and its ratio to the CPU budget, which is the load-invariant proof. Separately paste the injection half: a scratch runaway test caught by the guard under the SAME configuration as that suite run, with the guard's message. Both halves are required, because the suite half alone cannot distinguish a fixed guard from a disabled one. Delete the scratch test and paste `git status --short` proving the tree is clean of it.
  - Observed evidence:
    Bare full-suite run summary (`python3 -m pytest --durations=12`):
    ```
    FAILED tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta
    1 failed, 4807 passed, 2 skipped, 3 warnings in 687.15s (0:11:27)
    ```
    Reconciliation against V-01 baseline:
    - Baseline: `1 failed, 4798 passed, 2 skipped, 3 warnings in 364.21s`
    - Post-change: `1 failed, 4807 passed, 2 skipped, 3 warnings in 687.15s`
    - Delta: exactly +9 tests passed (the 9 new tests in `tests/test_hang_guard_budget.py`).
    - The sole failure is `tests/test_ipd_lint.py::ContinuationSubfieldOutcomeTests::test_corpus_verdict_neutrality_delta`, identical to the baseline run. Zero new failures.

    Target test nodeid (`tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs`):
    - ABSENT from failure list (passed).
    - `--durations` line:
      ```
      220.90s call     tests/test_statusline_behavior.py::TestStatuslineBoxInvariants::test_box_renderer_invariants_across_swept_inputs
      ```
    - Target CPU figure: 29.16s in-suite CPU. Ratio to 60.0s CPU budget: 29.16s / 60.0s = 0.486 (less than half the budget; >2x safety margin).

    Injection half (scratch test `tests/test_scratch_injected_runaway.py` with `@pytest.mark.timeout(2)` spin running under bare configuration):
    ```
    FAILED tests/test_scratch_injected_runaway.py::test_scratch_runaway_caught - conftest.TestHangTimeout: TEST HANG GUARD: tests/test_scratch_injected_runaway.py::test_scratch_runaway_caught exceeded its 2s CPU budget. The frame that did not return is in the stack dump in captured stderr. Raise the budget for a legitimately slow test with @pytest.mark.timeout(<seconds>).
    1 failed in 12.75s
    ```
    Scratch test deleted, `git status --short` clean of scratch test:
    ```
    git status --short
     M conftest.py
     M .aw/records/plans/pending/20261002-hangcpu-01-6ye76g-make-the-per-test-hang-guard-measure-cpu-time-so-machine-loa.ipd.md
    ?? tests/test_hang_guard_budget.py
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: quote the comment text documenting the blind spot. Confirm it states plainly that a CPU budget cannot see a test blocked on I/O, a lock, or a child process, nor a runaway loop over child processes (F-13); that this is why the wall ceiling is retained and kept well below the stall budget; that the ceiling is deliberately too loose to serve as a cost control; and the main-thread delivery property (F-15). Confirm it cites the measurements behind the claims (F-05's 45s deadlock running to completion under a CPU-only guard, and F-13's 1 percent parent-CPU subprocess loop), so a future reader tempted to delete the wall arm as redundant finds the experiment rather than an assertion.
  - Observed evidence:
    Quoted comment text from `conftest.py`:
    ```python
    # ACCEPTED BLIND SPOTS AND WHY THE WALL CEILING MUST STAY (F-05, F-13, F-15).
    # Anyone tempted to delete the wall arm as redundant must review these empirical findings:
    # - A CPU budget cannot see a test blocked on I/O, a lock, or a child process (deadlock):
    #   F-05 tested threading.Event().wait(45) under a CPU-only guard; it consumed 0.00s CPU and
    #   ran to completion untouched because a CPU timer never expires on zero-CPU waits.
    # - A CPU budget cannot see a runaway LOOP whose iterations mostly wait on child processes:
    #   F-13 measured parent CPU for subprocess loops (`subprocess.run([sys.executable, "-c", "pass"])`,
    #   the exact shape of the founding 8l8dgb hang) at only ~1% of wall time (0.04s CPU for 3.02s wall).
    #   A CPU-only timer would allow an 8l8dgb runaway loop to burn the entire runner stall timeout.
    # - Signal delivery to main thread (F-15): Python delivers signal handlers in the main thread only
    #   when it runs bytecode. If a background thread burns CPU while the main thread blocks in a C wait
    #   like thread.join(), the SIGPROF handler is deferred until the wait ends (measured: handler ran
    #   at 6.0s for a 6s spin while ITIMER_REAL ran at 1.01s). The wall arm bounds the wait.
    ```
    Confirmation:
    - Plainly states that CPU budget cannot see tests blocked on I/O, locks, or child processes (deadlocks) and cites F-05's 45s `threading.Event().wait(45)` deadlock running to completion under a CPU-only guard.
    - Plainly states that CPU budget cannot see runaway loops over child processes and cites F-13's 1% parent CPU measurement (0.04s CPU for 3.02s wall) on `subprocess.run([sys.executable, "-c", "pass"])`, the founding `8l8dgb` hang shape.
    - Confirms why the wall ceiling is retained and kept at 240s, far below the 900s stall budget (660s margin) so a runaway loop costs minutes and never the turn.
    - Confirms the wall ceiling is a loose liveness ceiling, not a cost control.
    - Explains main-thread signal delivery (F-15) where background thread spins defer SIGPROF while main thread blocks in C `join()`, so the wall arm covers that wait.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

WHAT A HUMAN WOULD BE APPROVING, in one paragraph. The suite's per-test hang guard charges a test for WALL-CLOCK time, so when the suite's own `-n auto` parallelism saturates the machine, a correct test is failed for waiting on a CPU it was never given. Measured here: the statusline sweep takes 29.53s alone and 66.53s in-suite while consuming the SAME 28s of CPU, and that one test has been reported red across at least 12 executed plans, each costing an agent a triage round trip. This plan changes the guard's cost DIMENSION, not its budget: a load-invariant CPU budget on `ITIMER_PROF` measures the work a test does, and a generous wall ceiling is RETAINED and re-aimed at liveness. It touches `conftest.py` and adds the guard's first-ever tests; NO production code changes. The tradeoff is measured and stated rather than glossed: a CPU budget is provably blind to a zero-CPU deadlock, demonstrated by a 45s `Event` wait that a CPU-only guard let run to completion untouched, AND (found at review, F-13) to a runaway loop over child processes, the founding `8l8dgb` shape, which charges about 1 percent of wall to parent CPU. That is exactly why the wall arm survives, and why its ceiling must stay well under the 900s stall budget. Existing `@pytest.mark.timeout(n)` markers keep at least today's generosity because the marker also floors the wall ceiling at `n` (F-14). WHAT IS DELIBERATELY NOT HERE: the swept sweep's own 7,776-row cost (owned by pending plan `mat9bt`, complementary and non-overlapping, see F-09); any re-marking of the `fields`/`verbose` reach tests (carried by `tf6x3a`); any claim to make the suite faster, since its wall time is dominated by genuine subprocess work; and any closure of the duplicate backlog item `cqgr7f`, which is a maintainer's call. ONE THING A REVIEWER SHOULD WEIGH EXPLICITLY: `mat9bt`'s gate prose says not to raise `_DEFAULT_TEST_TIMEOUT` in `conftest.py`, on the reasoning that a bigger global budget blinds the guard. This plan does not raise the wall budget to accommodate a slow test; it changes what is measured, which addresses that objection's substance rather than evading it. If the reviewer disagrees, this plan is the one to reject, because `mat9bt` stands alone without it.

EXECUTION CONTRACT. Commit only `conftest.py` and `tests/test_hang_guard_budget.py` through `aw commit <plan> -- conftest.py tests/test_hang_guard_budget.py`; never `git add -A` and never push. Paste ACTUAL runner output for every `V-*` item; a claimed pass with no pasted output fails the gate. Do NOT edit any test to make it fit the new budgets, and in particular do not touch `tests/test_statusline_behavior.py` (that file belongs to `mat9bt`) or the four existing `@pytest.mark.timeout` users: if one of them needs editing to stay green, the override semantics changed incompatibly and that is a stop-and-report condition. Do not remove the wall ceiling as redundant (F-05 prices that at a real deadlock class). Do not weaken any preserved guard property: the `BaseException` base, the repeating re-raise, the `faulthandler` dump, the main-thread precondition, or the own-handler stand-down. The declared scope is `conftest.py` and `tests/test_hang_guard_budget.py`; nothing under `agent_workflows/` is expected to change. If instrumenting reveals a genuine product defect, file it with `aw backlog new` rather than fixing it here; an out-of-scope edit, if one is made, is justified at finalize with `--scope-reason` and a declared-but-unmodified path with `--scope-ack`. Do not shorten the wall ceiling's margin below the stall budget to the point where a subprocess-bound runaway (F-13) could reach it. Delete every scratch probe file and prove the tree is clean.

POST-GATE LIFECYCLE. Run `aw ipd begin` before implementing. The terminal transition is MANDATORY but its owner is conditional: when this plan is dispatched by `aw oc run` / `aw agy run`, the runner performs the finalize (path-scoped commit and move to `.aw/records/plans/executed/`) after the merge-and-revalidate gate, so the executor must NOT run `aw ipd finalize` itself; when executed by hand with no runner, the executor runs `aw ipd finalize` after every `V-*` reads `pass`. Either way, do not hand-edit terminal state or `git mv` the file. Before the transition, confirm `aw ipd lint --phase pre-transition` conforms and reconcile the bare-suite result against the V-01 pre-edit baseline (F-12 records the authoring-time figure, `3 failed, 4624 passed, 2 skipped`, as context). Backlog item `mu4k1g` carries `- Blocks-Release: next` and this plan inherits it, so the gate travels with this plan and is discharged when it reaches `executed`.
