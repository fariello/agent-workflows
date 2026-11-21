- Id: wdarhj
- Status: graduated
- Graduated-To: wdarhj
- Set: wdarhj
- Work-Kind: bug
- Priority: medium
- Summary: aw find plans: handle non-UTF-8 decode errors and surface incomplete cache records instead of crashing or silently falling back
- Short-Description: aw find plans: handle non-UTF-8 decode errors and surface incomplete cache records instead of crashing or silently falling back
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 graduated (aw backlog): graduated by run run-20261121T164611Z-3890369: zeopzs
- 2026-11-21 created (aw backlog): aw find plans: handle non-UTF-8 decode errors and surface incomplete cache records instead of crashing or silently falling back

## Problem

In `agent_workflows/cli.py::_find_type_records`, when a plan file is absent from the `artifact_meta.query` result because it failed to load (`QueryResult.incomplete`), the fallback calls `p.read_text(encoding="utf-8")` inside `except OSError: continue`:

1. If the plan file contains non-UTF-8 bytes, `p.read_text(encoding="utf-8")` raises `UnicodeDecodeError` (which is a `ValueError`, not an `OSError`), crashing `aw find plans` with an unhandled traceback instead of reporting the unreadable record cleanly.
2. If the plan file has a corrupt `meta/<id6>.jsonl` log, `artifact_meta.query` omits the plan from `rows` and records its `id6` in `incomplete`, but `_find_type_records` silently falls back to `_meta.read_text(p.read_text(encoding="utf-8"), record_type="ipd")` and prints the markdown fields without reporting that the log is corrupt or incomplete.

## Expected behavior

1. `aw find plans` must not crash with an unhandled `UnicodeDecodeError` when a plan file cannot be decoded as UTF-8.
2. When `artifact_meta.query` reports an `incomplete` record, `aw find` must surface or warn on the invalid record rather than silently serving fallback markdown text from a record whose metadata log failed to parse.

## Discovery context

Observed during execution of IPD `ffceq0` (E-12 cache-parity invalid-replacement testing).
