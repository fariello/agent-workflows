- Id: bh1cy5
- Status: done
- Graduated-To: rescomp
- Set: instbugs
- Priority: low
- Work-Kind: feature
- Summary: Give research documents a companion convention for non-Markdown files (CSV, zip) that index, mv, set-assign, promote and archive carry along

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD mtdxiu executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-rescomp-01-mtdxiu-give-research-documents-a-companion-directory-that-index-mv.ipd.md); evidence .aw/records/plans/executed/20261012-rescomp-01-mtdxiu-give-research-documents-a-companion-directory-that-index-mv.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005641Z-2321995: mtdxiu
- 2026-10-07 created (aw backlog): Give research documents a companion convention for non-Markdown files (CSV, zip) that index, mv, set-assign, promote and archive carry along

Observed 2026-10-06 during a fresh target install (research report l6cbbb, defect D13, second half): an externally produced report arrived with four CSV companions plus a zip. The research tree has no convention for non-Markdown companions. The workaround was a sibling directory named <report-stem>.data/, which aw research index silently ignores and which set-assign/mv would orphan by renaming the report without it. Wanted: a documented companion convention (for example a directory sharing the doc's id6), recognized by aw research index (listed, and --check flags orphans), and carried along by mv/set-assign/promote/archive. The other half of D13 (an adopt verb that preserves an external body byte-for-byte) is fixed at HEAD by aw adopt (plan lznpv6, Set awinbox); verified 2026-10-06 in a scratch target: the adopted body is a byte-exact suffix of the dropped file. Feature request, recorded rather than planned, per the report's own instruction.
