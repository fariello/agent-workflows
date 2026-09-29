- Id: 7gr0vr
- Status: open
- Set: advisoryhdr
- Priority: low
- Work-Kind: chore
- Summary: aw commit/work begin advisory heading says '(warning)' for an error-registered rule

## Workflow history
- 2026-09-29 created (aw backlog): aw commit/work begin advisory heading says '(warning)' for an error-registered rule

FOUND BY: /plan-review of plan ygb3nk, 2026-09-29.

WHAT IS WRONG. `run_commit` and `run_work_begin` both print their non-blocking findings under the heading `note - N advisory (warning) finding(s) on <plan> (not blocking):`. The parenthetical `(warning)` is hardcoded and describes the SEVERITY the finding was assumed to have. Once a rule registered at another severity is routed to the advisory channel (which plan ygb3nk does for `check.scope-drift`, registered `error`), the heading announces an `error`-severity rule as a `warning`.

WHY IT MATTERS. It is cosmetic and human-facing only: no machine surface parses the heading, the rule id and detail are printed verbatim on the following line, and `aw check --agent` continues to report the finding at its registered severity. But it tells a human the wrong thing about a finding they are being asked to act on.

MEASURED. Plan ygb3nk's F-15 originally recorded this as unfixable because 'changing the heading text would break `test_commit_warning_drift_commits_with_advisory`, which asserts `advisory` in the output'. That reason is FALSE: the test asserts the SUBSTRING `advisory` (`assertIn("advisory", out)`, tests/test_work_gate_severity.py:192), which survives any edit to the `(warning)` parenthetical. Verified by substituting `note - 1 advisory (non-blocking) finding(s)` and confirming the substring is still present.

WHERE. `agent_workflows/work_cmd.py`, the advisory print block in `run_commit` and the matching one in `run_work_begin`.

WHAT A FIX LOOKS LIKE (not prescriptive). Either drop the severity parenthetical entirely (`N advisory finding(s)`) or derive it per finding from the enriched drift instead of hardcoding one word for the whole batch. Both verbs share the wording, so fix them together.

WORK-KIND. Filed `chore` rather than `bug`: the output is misleading but no user waits on it, nothing is computed from it, and the adjacent line carries the accurate rule id. Per the repository's perceptibility test an invisible-to-correctness wording slip is a chore, so it does NOT gate the next release.
