- Id: 8iy2dk
- Status: done
- Blocks-Release: next
- Set: 8iy2dk
- Priority: high
- Work-Kind: followup
- Summary: plan-review and IPD-authoring/assessing workflows must explicitly check whether an IPD is too large and should be split into smaller IPDs (context/attention/execution sizing)

## Workflow history
- 2026-08-23 done (aw set): Closed by highpbacklog0822 Set (all child IPDs executed): 8iy2dk
- 2026-08-21 set (aw backlog): gate the 2.0.0 release on the IPD right-sizing check

Add an explicit right-sizing check to /plan-review, /plan-review-long, the assess harness, and aw ipd scaffold/authoring guidance: for each IPD, judge not just the mechanical size lint (>18 E-leaves / >5 groups) but whether any single E-item or the whole plan bundles multiple independently-verifiable concerns that would degrade a real agent's context, attention, and execution quality, and recommend splitting into smaller child IPDs when so. Root cause (2026-08-21): the awoptimize Set passed aw ipd lint as conforming with Size assessment: standard, but Orders 02/03/04 each contained Order-sized E-items (e.g. append-only tamper-evident ledger, crash recovery, a 12-class evidence-validator suite); the maintainer had to ask twice before the plans were decomposed. A passing size lint measures count, not conceptual density per item. Deliverables: (a) a per-E-item 'one-concern / executable-in-one-focused-pass' rubric check added to plan-review + plan-review-long + the assess IPD-producing harness; (b) consider a mechanical lint heuristic flagging an E-item action that names multiple deliverables/test-surfaces; (c) authoring guidance (aw ipd scaffold) that pushes one-concern-per-E-item; (d) treat a maintainer's sizing question as a finding to investigate by decomposition, not a signal to dismiss via the linter.
