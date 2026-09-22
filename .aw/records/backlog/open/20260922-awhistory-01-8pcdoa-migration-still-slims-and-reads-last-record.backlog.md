- Id: 8pcdoa
- Status: open
- Blocks-Release: next
- Set: awhistory
- Priority: medium
- Work-Kind: bug
- Summary: record_history.migrate_inline_history still SLIMS inline history to one record and keys 'latest' on the LAST record in file order, contradicting the newest-first writers and the durability ruling plan vhbvwz implemented

## Workflow history
- 2026-09-22 created (aw backlog): FOUND while executing plan vhbvwz (E-04/E-08 adjacent code). record_history._slim_inline_history (record_history.py, docstring 'keep ONLY the latest (last-in-order) record line', keep = records[-1]) and its caller migrate_inline_history still implement the behavior the maintainer REVERSED on 2026-09-10: they fold inline history into the gitignored sidecar and then truncate the file to one record. TWO DEFECTS, both live. FIRST, the slimming itself now contradicts spec 20260818-1525-02 as amended by vhbvwz (R2/AC1: inline history is the DURABLE home for specs and backlog, because .aw/.gitignore ignores records/history.jsonl so the sidecar does not survive a clone). SECOND, and independent of the ruling, it keeps records[-1] as 'the latest', which is the LAST record in FILE order while every writer PREPENDS, so on a newest-first file it retains the OLDEST record and deletes the newest. That is the same defect class vhbvwz E-02 fixed in attention_contract.last_history_at. WHY IT DID NOT FIRE IN THIS RUN: migrate_inline_history has no CLI entry point (grepped: its only callers are tests/test_record_history_migrate.py), so it is reachable only by a direct call today. It was therefore left alone deliberately rather than changed outside plan vhbvwz's declared scope. RECOMMENDED: either retire the migration (its job is done and its premise is reversed) or rewrite it to preserve inline history and to consume attention_contract.newest_history_record; do not leave a helper in the tree whose one action is to destroy the provenance the amended spec now requires.
