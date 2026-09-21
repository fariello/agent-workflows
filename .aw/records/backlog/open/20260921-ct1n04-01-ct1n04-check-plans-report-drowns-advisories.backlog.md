- Id: ct1n04
- Status: open
- Set: ct1n04
- Priority: low
- Work-Kind: followup
- Summary: aw check plans reported 416 findings including 354 check.scope-drift, so the one info-severity advisory this sweep adds is invisible in a report already 400 lines long

## Workflow history
- 2026-09-21 created (aw backlog): Observed while executing lintreach k9awrq. Measured at HEAD cd2e6adb: aw check plans reports 402 to 416 findings, of which check.scope-drift alone is 340 to 354 (it moves with live begin receipts, including other agents' in-flight ones). k9awrq deliberately ships check.ipd-lint-diagnostic at info severity so it cannot fail a gate, which means its whole value is that a human or agent READS it. A single info line inside a 400-line report is not read. This is a REPORTING concern and NOT a request to change any rule's severity: the plan's OQ-04 owns whether the lint rule should ever block, and check.scope-drift's own volume is a separate question about receipt liveness. Candidate directions: group or collapse per-rule findings in the human renderer, summarize the dominant rule rather than enumerating every row (evaluate_durable_carrier already caps its enumeration at five for exactly this reason), or separate advisories from errors in the rendered output.
