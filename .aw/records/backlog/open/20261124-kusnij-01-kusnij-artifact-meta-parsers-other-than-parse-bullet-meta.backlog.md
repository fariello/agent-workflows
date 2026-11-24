- Id: kusnij
- Status: open
- Set: kusnij
- Work-Kind: bug
- Priority: low
- Summary: artifact_meta parsers other than _parse_bullet_metadata_with_loose still split text with str.splitlines() (history block, YAML front matter, read_text prelude), which also breaks at U+0085/U+2028/bare CR and can truncate or forge a line in a crafted record
- Short-Description: artifact_meta parsers other than _parse_bullet_metadata_with_loose still split text with str.splitlines() (history block, YAML front matter, read_text prelude), which also breaks at U+0085/U+2028/bare CR and can truncate or forge a line in a crafted record
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): artifact_meta parsers other than _parse_bullet_metadata_with_loose still split text with str.splitlines() (history block, YAML front matter, read_text prelude), which also breaks at U+0085/U+2028/bare CR and can truncate or forge a line in a crafted record
