- Id: xa7pqe
- Status: open
- Set: specaudit
- Priority: medium
- Work-Kind: followup
- Summary: Restore behavioral tests for spec c4gd2h A1, A2, A4, A7 deleted by the 2026-09-24 suite trim

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Commit 19313eed7 (2026-09-24) deleted test_runner_stop.py, _levels12, _level3, _level4, _triggers, test_runner_shutdown.py and test_run_viewer_liveness.py, which walkthrough 01ad6r used to verify c4gd2h A1-A10. At HEAD 5db4791c1: A1 (single SIGINT ends after current call) is covered only at unit level (test_interrupt_tty_wedge.py); A2 (three SIGINTs reach level 4 with the escalation path recorded and item unknown_outcome) is partly covered; A4 (stop --after-set) and A7 (overrun wind-down escalates; BudgetBreachWatch/EscalationWatch in runner_stop.py) have no test. Also: amend A9 (demands an AST/import-graph check, forbidden by the no-code-pinning rule P16) into a behavioral criterion; record A10 (non-POSIX) as a gated deferral; resolve or defer OQ-02 and OQ-04. Then c4gd2h can move to implemented. Duplicate parked item w07sbr cites a deleted test file and can close.
