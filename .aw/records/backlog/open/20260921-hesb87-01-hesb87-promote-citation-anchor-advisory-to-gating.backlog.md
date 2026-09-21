- Id: hesb87
- Status: open
- Set: hesb87
- Priority: low
- Work-Kind: followup
- Summary: Decide whether the IPD-C801 citation-anchor advisory should be promoted to a gating severity, using its measured false-positive rate on post-cutover plans

## Workflow history
- 2026-09-21 created (aw backlog): Carrier for the deferred promotion decision in plan mzc019 (citeanchor). The rule ships at info and must not gate until the false-positive rate on plans authored AFTER the cutover is measured, with the known line-granularity false positive (a multi-line E-item whose symbol is on line 1 and whose offset is on an indented continuation line) counted as such.
