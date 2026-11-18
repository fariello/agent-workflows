- Id: joe57m
- Status: open
- Set: joe57m
- Work-Kind: followup
- Priority: medium
- Summary: Align artifact_meta history parsing and read_text with attention_contract.history_block
- Short-Description: Align artifact_meta history parsing and read_text with attention_contract.history_block

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-18 created (aw backlog): Align artifact_meta history parsing and read_text with attention_contract.history_block

Discovered while executing metastore Order 31 (i3b5zu): artifact_meta._parse_bullet_metadata_with_loose parses Workflow history lines without stopping at prose or skipping indented sub-bullets (unlike attention_contract.history_block), and artifact_meta.read_text does not return parsed history events. Because tests/test_history_consumers_shared_reader.py calls check_engine._item_close_date(raw_markdown_text) without repo_root or item_id6, _item_close_date must keep an in-memory history_block/last_history_at fallback until read_text and history_lines match attention_contract.history_block.
