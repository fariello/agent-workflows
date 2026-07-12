# IPD: Scan secrets history line offset tracking refactor

- Date: 2026-07-12
- Concern: feature/correctness
- Scope: `.agents/workflows/assess/tools/scan_secrets.py`
- Status: to-review
- Author: Antigravity (Gemini 1.5 Pro)

## Workflow history

- 2026-07-12 to-review (Antigravity/Gemini): Proposed split plan for the scan_secrets.py history scan line-offset tracking refactor.

## Goal

Refactor `.agents/workflows/assess/tools/scan_secrets.py` to parse diff hunk headers (`@@`) in order to report the exact line numbers of findings in history scans, instead of defaulting to line 1.

## Proposed Changes

### assess/tools

#### [MODIFY] [scan_secrets.py](file:///.agents/workflows/assess/tools/scan_secrets.py)
* Refactor `scan_history()` to parse the diff hunk headers (`@@` lines) using the pattern `r"^@@ -\d+(?:\,\d+)? \+(\d+)(?:\,\d+)? @@"`.
* Track the exact target file line number offset using the parsed start line.
* Pass `start_line` offset to `scan_text()`.
* Add `start_line` parameter to `scan_text()` (defaulting to 1).
* Inside `scan_text()`, calculate line number as `line_no = text.count("\n", 0, m.start()) + start_line`.

## Verification Plan

### Automated Tests
* Add `test_scan_history_reports_correct_offset` to `tests/test_scan_secrets.py` planting a secret at a known offset in history and asserting that the reported line number matches exactly.
* Run `python3 -m unittest discover tests` and verify all tests pass.
