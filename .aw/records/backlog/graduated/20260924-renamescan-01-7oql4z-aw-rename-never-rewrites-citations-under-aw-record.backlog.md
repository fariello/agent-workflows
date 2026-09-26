- Id: 7oql4z
- Status: graduated
- Graduated-To: renamescan
- Blocks-Release: next
- Set: renamescan
- Priority: medium
- Work-Kind: bug
- Summary: aw rename never rewrites citations under .aw/records/reviews/ or tests/, so renaming a cited artifact leaves tracked reviews and test fixtures pointing at a file that no longer exists

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into to-review plan Set renamescan (commit 2c7068ca).
- 2026-09-24 created (aw backlog): aw rename never rewrites citations under .aw/records/reviews/ or tests/, so renaming a cited artifact leaves tracked reviews and test fixtures pointing at a file that no longer exists

FOUND 2026-09-25 renaming specs 25kzda and 5tapom (d6b2fa00). artifact_core.SCAN_ROOTS lists plans, specs, research, walkthroughs, roadmaps, prompt-library, backlog and releases but NOT .aw/records/reviews/, so 9 tracked review records kept the old spec names and had to be fixed by hand. tests/ is not scanned either (no test cited these two specs, so no harm this time).

TWO FURTHER DEFECTS IN THE SAME REWRITE, both measured on that rename:
1. The legacy-prefix stem rewrite turns a SHORT handle (e.g. spec `20260826-0718-01`) into the full new stem (`20260826-25kzda-01-25kzda-aw-run-...-verify.spec`), which reads as a broken filename. Two occurrences (backlog cjefq5, plan 1bdxcp) were hand-restored. A short handle should map to the new short handle (`20260826-25kzda-01`).
2. A quoted command transcript ('--- would rename A -> B ---') inside an executed plan is rewritten like any citation, falsifying what the command printed. Two occurrences (plans ha55fi, 3i6rso) were hand-restored in d6b2fa00/084689ef.

Fix direction: add .aw/records/reviews to SCAN_ROOTS (check why it was omitted first); map legacy short handles to the new short handle; leave text inside fenced code blocks and quoted transcripts alone, as the permalink masking in artifact_refs already does for pinned links.
