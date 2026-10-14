- Id: g73xcx
- Status: open
- Set: g73xcx
- Priority: low
- Work-Kind: chore
- Summary: Strip trailing hyphens after 50-char slug slice in backlog.cmd_new so aw backlog new never writes a check.name-nonconformant filename

## Workflow history
- 2026-10-14 created (aw backlog): Strip trailing hyphens after 50-char slug slice in backlog.cmd_new so aw backlog new never writes a check.name-nonconformant filename

Found while executing ellenm (Set iosmvn): agent_workflows/backlog.py cmd_new slices core.kebab(...)[:50] without .strip('-') (unlike prompts.py:509 and artifact_naming.build_clustered_name) and hand-formats the filename, so any summary whose kebab form has a hyphen at index 49 writes a filename ending in -.backlog.md that immediately fails aw check backlog with check.name-nonconformant. Also check specs.py:1084, ipd_authoring.py:579, and set_records.py:349 for the same unstripped slice.
