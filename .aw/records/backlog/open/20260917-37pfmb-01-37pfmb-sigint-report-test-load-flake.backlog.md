- Id: 37pfmb
- Status: open
- Set: 37pfmb
- Priority: low
- Work-Kind: bug
- Summary: SIGINT shutdown-report test times out under parallel suite load

## Workflow history
- 2026-09-17 created (aw backlog): SIGINT shutdown-report test times out under parallel suite load

Measured 2026-09-17 while executing plan 63425h (rcptwiden-01).

WHAT IS WRONG. `tests/test_runner_backlog_close.py::ShutdownReportOnInterrupt::test_sigint_produces_the_report_and_exits_130` intermittently fails with `subprocess.TimeoutExpired ... timed out after 30 seconds` when the full suite runs in parallel (`-n auto`). The test spawns a real child, waits for it to print READY, sends SIGINT, and gives it 30 seconds to emit the shutdown report and exit 130. Under load the child does not finish in that window.

EVIDENCE. Failed on two consecutive full-suite runs (gw7 both times); passed five consecutive times run alone (0.62-0.64s each); its whole file passed under forced parallelism (47 passed in 2.96s); passed twice consecutively on later full-suite runs (7855 passed each). The failure is a wall-clock timeout, not an assertion, so the report path itself is not implicated.

WHY IT MATTERS. It is a false red on an unattended run, and it is in a file an executing agent is likely NOT to have declared, so hitting it costs a lane the cost of diagnosing someone else's flake. The sibling SIGTERM test shares the harness and presumably the same exposure.

NOT DIAGNOSED HERE, deliberately: whether the right fix is a longer or load-aware timeout, marking these two `slow`, or serializing them (`xdist_group`) is a judgement about the suite's flake policy and belongs with whoever owns it. The harness already carries a comment about an earlier flake at -2 under the loaded parallel suite, so this is the same class recurring rather than a new discovery.
