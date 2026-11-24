- Id: t5t02b
- Status: open
- Set: readdecode
- Work-Kind: bug
- Priority: medium
- Summary: aw search and aw ipd board crash with UnicodeDecodeError on a non-UTF-8 record file
- Short-Description: aw search and aw ipd board crash with UnicodeDecodeError on a non-UTF-8 record file
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-24 created (aw backlog): aw search and aw ipd board crash with UnicodeDecodeError on a non-UTF-8 record file

## Problem

`agent_workflows/cli.py::_run_search` (`aw search`) and `agent_workflows/plans.py::scan` (used by `aw ipd board`) read a record with `read_text(encoding="utf-8")` inside `except OSError:`. `UnicodeDecodeError` is a `ValueError`, so a record file holding non-UTF-8 bytes crashes both commands with an unhandled traceback.

Measured 2026-11-24 during /plan-review of plan zeopzs: in the `tests/test_readers_cache_parity.py::_build_corpus_repo` corpus with the plan file overwritten by `b'\xff\xfe\x00\x00unparseable-record'`, `aw search clean --agent` and `aw ipd board` both raised `UnicodeDecodeError`.

## Expected behavior

Both commands report the unreadable record as a diagnostic and keep answering for the readable records, as plan zeopzs does for `aw find`.

## Discovery context

Split out of plan zeopzs (backlog wdarhj), whose scope is `aw find` only.
