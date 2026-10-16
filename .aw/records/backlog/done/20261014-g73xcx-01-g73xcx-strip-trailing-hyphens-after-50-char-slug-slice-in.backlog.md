- Id: g73xcx
- Status: done
- Graduated-To: g73xcx
- Set: g73xcx
- Priority: low
- Work-Kind: chore
- Summary: Strip trailing hyphens after 50-char slug slice in backlog.cmd_new so aw backlog new never writes a check.name-nonconformant filename

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD 1i2kgq executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-g73xcx-01-1i2kgq-strip-trailing-hyphens-after-slug-slice-in-hand-formatted-ba.ipd.md); evidence .aw/records/plans/executed/20261014-g73xcx-01-1i2kgq-strip-trailing-hyphens-after-slug-slice-in-hand-formatted-ba.ipd.md
- 2026-10-15 graduated (aw backlog): graduated by run run-20261014T234552Z-3806024: 1i2kgq
- 2026-10-14 created (aw backlog): Strip trailing hyphens after 50-char slug slice in backlog.cmd_new so aw backlog new never writes a check.name-nonconformant filename

Found while executing ellenm (Set iosmvn): agent_workflows/backlog.py cmd_new slices core.kebab(...)[:50] without .strip('-') (unlike prompts.py:509 and artifact_naming.build_clustered_name) and hand-formats the filename, so any summary whose kebab form has a hyphen at index 49 writes a filename ending in -.backlog.md that immediately fails aw check backlog with check.name-nonconformant. Also check specs.py:1084, ipd_authoring.py:579, and set_records.py:349 for the same unstripped slice.
