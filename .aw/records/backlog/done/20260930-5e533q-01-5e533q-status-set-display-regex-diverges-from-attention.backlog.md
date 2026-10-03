- Id: 5e533q
- Status: done
- Graduated-To: brgate
- Blocks-Release: next
- Set: 5e533q
- Priority: low
- Work-Kind: bug
- Summary: The aw set display path labels a record [blocking] on an unanchored whole-text Blocks-Release scan, so it disagrees with attention and releases on the same file

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD b92m14 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261001-brgate-01-b92m14-bound-every-blocks-release-reader-and-writer-to-the-metadata.ipd.md); evidence .aw/records/plans/executed/20261001-brgate-01-b92m14-bound-every-blocks-release-reader-and-writer-to-the-metadata.ipd.md
- 2026-10-01 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: b92m14
- 2026-09-30 created (aw backlog): Split from plan 4gwgo3 finding F-08, measured in that lane: aw set printed '[blocking]' for a backlog item whose smuggled '- Blocks-Release: next' sat in the history body, while 'aw attention --format json' reported '"blocks_release": null' for the same file and releases.get_release_blockers returned []. Cause: the display path searches rec.raw_text with '(?m)^-\\s*Blocks-Release:\\s*(\\S+)' (no trailing anchor, whole text) while attention.py and releases.py use anchored front-matter-biased reads. Plan 4gwgo3 reduces reachability by guarding the five setter flags that could PRODUCE such a file, but a hand-edited one still displays wrongly, so the reader divergence is untouched. Filed as a bug because a human reading 'aw set' output is told a record gates a release when the release view says it does not. Deciding WHICH reader is correct is the real work here.
