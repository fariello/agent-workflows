- Id: 4znh53
- Status: done
- Set: 4znh53
- Priority: medium
- Work-Kind: bug
- Summary: Color-env tests race under xdist: NO_COLOR/FORCE_COLOR/TERM mutate process-global os.environ, so parallel workers cross-contaminate and a different color node fails per run

## Workflow history
- 2026-09-20 done (aw set): CAUSE CORRECTED and DEFECT FIXED on main by commit 94fd41cb. The bug is REAL and the measurement in this item was sound; only the diagnosed mechanism was wrong, so the correction is recorded rather than the item being silently closed.

WHAT THIS ITEM SAID: the color tests mutate NO_COLOR/FORCE_COLOR/TERM in process-global os.environ, so parallel xdist workers cross-contaminate. Proposed remedy: patch.dict(os.environ, ...) per assertion.

WHY THAT CANNOT BE IT: tests/test_term.py already saves all three variables in setUp and restores them via addCleanup (same pattern in two more classes). pytest-xdist workers are SEPARATE PROCESSES running one test at a time, so two tests in different workers share no environment and two in one worker do not overlap. There was nothing to cross-contaminate, and the proposed remedy would not have fixed it.

THE ACTUAL CAUSE, measured in a fresh interpreter: the leaked state is a MODULE GLOBAL, term._COLOR_OVERRIDE, not the environment. cli._dispatch sets it from the parsed flags part way through its body, but argparse --help and usage errors raise SystemExit BEFORE the reset line, so the value survives the call:
  baseline:                                       override=None  should_color(TTY)=True
  after cli.main(['--no-color','check','--help']): override=False should_color(TTY)=False
Fifteen test files pass --color/--no-color to a CLI entry point, so one poisons its worker and whichever color test pytest-randomly schedules next in that worker fails. That is precisely the moving target measured here, and it explains why every affected node passed in isolation. The override deliberately does NOT travel through os.environ (term.py documents that a flag must not be inherited by spawned subprocesses), which is why the env theory could not hold.

THE FIX (94fd41cb): cli.main records the override it INHERITED and restores it in a finally, covering the return, SystemExit and exception paths. It restores the inherited value rather than None, because the runners set an override around a block of work and then launch nested aw invocations. Regression test: tests/test_term.py::CliNeverLeaksTheColorOverrideTests, a five-row table over the early-exit paths, mutation-verified (deleting the finally fails it and names the leaking path).

EVIDENCE: 21 consecutive bare 'python3 -m pytest' runs clean, and re-checked on this merge candidate: the leaking path now leaves override=None and should_color(TTY)=True.

GATE CLEARED rather than handed to a plan, because the gating defect no longer exists on main.
- 2026-09-20 created (aw backlog): Filed by plan udgilu execution 2026-09-20. Measured on lane aw/lane/udgilu at base bb714fd8: two consecutive bare full-suite runs failed on DIFFERENT nodes with different working trees. Run 1 (with udgilu's new files present): 4 failed - test_term.py ShouldColorGridTests::test_every_term_value_matches_the_ruled_expectation, ::test_every_no_color_force_color_cell_matches_the_ruled_expectation, ::test_a_falsey_force_color_never_forces_and_never_suppresses, ColorPrecedenceTests::test_env_beats_detection_without_a_flag. Run 2 (udgilu's files REMOVED and its record edits stashed, i.e. a clean baseline tree): 1 failed - tests/test_runner_shared.py SharedColorDecisionTests::test_a_falsey_force_color_no_longer_forces_color_into_a_pipe. A third bare run on the restored tree passed entirely (7157 passed, 3 skipped, 2 xfailed). Every affected node passes in isolation (tests/test_term.py alone: 34 passed; test_term+test_runner_shared+test_pwatch together: 234 passed; the three failing classes selected directly: 20 passed). The cause is shared mutable state rather than any assertion being wrong: these tests set and pop NO_COLOR / FORCE_COLOR / TERM in os.environ, which is PROCESS-GLOBAL, and pyproject addopts runs -n auto --dist=worksteal so several such tests land in one worker process and observe each other's env. USER-PERCEPTIBLE IMPACT: a bare 'python3 -m pytest' is the contract every agent and CI run is judged by here, and it fails nondeterministically on work that did not touch color at all, which costs a human a false regression investigation per occurrence (it cost one in this run). REMEDY: make the env manipulation hermetic (unittest.mock.patch.dict(os.environ, clear=False) per assertion, or pass the value in rather than through the environment, which term.should_color already supports via its override= parameter for the flag layer).
