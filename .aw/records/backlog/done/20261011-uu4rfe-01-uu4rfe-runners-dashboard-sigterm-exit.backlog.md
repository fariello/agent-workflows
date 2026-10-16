- Id: uu4rfe
- Status: done
- Graduated-To: uu4rfe
- Set: uu4rfe
- Priority: low
- Work-Kind: chore
- Summary: Decide whether the aw runners table dashboard should return 143 on SIGTERM like aw pwatch (runners_monitor.run_table_dashboard stop_cleanly raises SystemExit(0) for both signals)

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 9380pe executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-uu4rfe-01-9380pe-make-the-aw-runners-table-dashboard-return-143-on-sigterm-wh.ipd.md); evidence .aw/records/plans/executed/20261014-uu4rfe-01-9380pe-make-the-aw-runners-table-dashboard-return-143-on-sigterm-wh.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 9380pe
- 2026-10-12 created (aw backlog): Decide whether the aw runners table dashboard should return 143 on SIGTERM like aw pwatch (runners_monitor.run_table_dashboard stop_cleanly raises SystemExit(0) for both signals)

Surfaced 2026-10-11 while authoring plan ww744p (backlog x31lcm). runners_monitor.run_table_dashboard installs its own stop_cleanly for SIGINT and SIGTERM raising SystemExit(0) and catches (KeyboardInterrupt, SystemExit) returning 0, the same shape pwatch had. ww744p changes only pwatch; aw runners --tree delegates to pwatch.main and inherits that change, but the default table dashboard does not. Not filed as a bug: no supervisor of the dashboard is known; decide for consistency with ww744p's ruling.
