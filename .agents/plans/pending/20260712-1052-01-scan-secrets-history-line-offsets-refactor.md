# IPD: Scan secrets history line offset tracking refactor

- Date: 2026-07-12
- Concern: feature/correctness
- Scope: `.agents/workflows/assess/tools/scan_secrets.py`
- Status: reviewed
- Author: Antigravity (Gemini 1.5 Pro)

## Workflow history

- 2026-07-12 to-review (Antigravity/Gemini): Proposed split plan for the scan_secrets.py history scan line-offset tracking refactor.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  Verified against source: `scan_text` (scan_secrets.py:340, currently `line_no = ... + 1`),
  `scan_history` (:476, `@@` handling at :513), and `test_detects_planted_secret_in_history`
  (test_scan_secrets.py:83) to extend. This restores - now properly reviewed - the accurate
  line-reporting feature that was over-scoped into an earlier unrelated execution and reverted
  (see 1041-01 SPLIT). Added acceptance criteria + scope/risk; no BLOCKER/HIGH. Small, mechanical,
  low risk. Status -> reviewed.

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

## Acceptance criteria (added by plan-review)

- A secret introduced in git history at a KNOWN line offset (not line 1) is reported at that exact
  `path:line` by `--history-only` scanning; the prior behavior reported `:1`.
- Working-tree scanning behavior is unchanged (regression: the existing tree/history tests still
  pass).
- No new dependency; stdlib only. `scan_text`'s `start_line` defaults to 1 so all existing callers
  are unaffected.

## Scope / risk (added by plan-review)

- IN-SCOPE, single file (`scan_secrets.py`) + one test. Remediation Risk: Low (bounded, well-tested,
  additive parameter with a safe default). No over-scope: this is exactly the feature split out of the
  earlier over-scoped execution, nothing more.

## Verification Plan

### Automated Tests
* Add `test_scan_history_reports_correct_offset` to `tests/test_scan_secrets.py`: plant a secret at a
  KNOWN offset in a committed-then-removed file and assert the reported line number matches exactly
  (not `:1`).
* Existing tree + history tests must still pass (no regression).
* Run `python3 -m unittest discover tests` and verify the full suite is green (currently 205 OK; this
  adds 1 test).

## Approval and execution gate

`reviewed`. Awaiting human approval to execute. Then: implement the `scan_history`/`scan_text`
offset tracking + the regression test, validate (full suite green), commit (never push), `git mv`
to executed/. Small mechanical change; does not self-approve.
