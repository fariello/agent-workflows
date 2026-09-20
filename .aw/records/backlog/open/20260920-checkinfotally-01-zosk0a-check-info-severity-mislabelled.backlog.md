- Id: zosk0a
- Status: open
- Blocks-Release: next
- Set: checkinfotally
- Priority: medium
- Work-Kind: bug
- Summary: aw check reports every info-severity finding as an error in its Evidence tally: err_cnt counts by rule-name prefix (not d.rule.startswith('warn')) instead of by severity, so a clean per-type run renders 'errors 1' while correctly exiting 0

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing IPD sk7ggr E-06. cli._run_check computes err_cnt = sum(1 for d in drift if not d.rule.startswith('warn')) and warn_cnt by the same prefix test, so severity is never consulted. PRE-EXISTING and not introduced by sk7ggr: measured at HEAD 93b7aabb, 'aw check plans' already renders 'errors 428' over a tree whose findings include 75 info-severity check.ipd-uncarried-obligation, and 76 of those 428 are info. sk7ggr's new check.collisions-not-checked advisory makes it visible on a CLEAN run too ('CONFORMS' beside 'errors 1'), which is what surfaced it. The exit code is correct throughout (artifact_core.drift_exit_code does key on severity and ignores info), so this is a REPORTING defect, not a gating one. Fix: tally by the enriched severity (check_engine.enrich_drift / RULE_REGISTRY) rather than by a rule-name prefix, and render info findings in their own bucket. cli.py was deliberately OUT of sk7ggr's declared Scope-Paths, so it was reported rather than edited.
