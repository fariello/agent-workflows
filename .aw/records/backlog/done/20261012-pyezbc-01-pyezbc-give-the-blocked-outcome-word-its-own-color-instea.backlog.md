- Id: pyezbc
- Status: done
- Graduated-To: pyezbc
- Set: pyezbc
- Priority: low
- Work-Kind: followup
- Summary: Give the BLOCKED outcome word its own color instead of the cyan else-branch

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 5apgyn executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-pyezbc-01-5apgyn-give-the-blocked-outcome-word-its-own-orange-208-color-inste.ipd.md); evidence .aw/records/plans/executed/20261014-pyezbc-01-5apgyn-give-the-blocked-outcome-word-its-own-orange-208-color-inste.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: 5apgyn
- 2026-10-13 created (aw backlog): Give the BLOCKED outcome word its own color instead of the cyan else-branch

Measured in plan 064awu (Findings F-06): render_stream.render_run_summary_table colors the BLOCKED outcome word cyan, falling into the color-selection's else-branch because no branch names BLOCKED explicitly. The code's own ys1dor E-02 comment warns that an unhandled outcome word looks deliberate while being wrong. Spec uonrjg Section 7.2 assigns stage blocked orange 208 rather than cyan.
