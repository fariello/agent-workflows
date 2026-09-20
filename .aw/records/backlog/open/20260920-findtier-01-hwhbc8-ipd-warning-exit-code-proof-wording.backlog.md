- Id: hwhbc8
- Status: open
- Set: findtier
- Priority: low
- Work-Kind: followup
- Summary: IPD spec V-item wording asks for a synthetic-tree exit-0 proof that no non-info rule can satisfy

## Workflow history
- 2026-09-20 created (aw backlog): Found while executing findtier Order 02 (3i6rso). Plan 3i6rso's V-04 requires proving an advisory rule harmless via 'a synthetic tree whose ONLY finding is the new code, on which aw check exits 0'. That is unsatisfiable for any severity other than info: artifact_core.drift_exit_code is 'return 1 if any(severity != "info") else 0', so a warning-only tree exits 1 by design. Three registered rules already document this in their own comments (check.review-decision-unescalated, check.stale-index-missing, check.system-layout-*), and tests/test_review_findings.py states an exit-code argument proves nothing for a warning. The risk is that a future plan author repeats the ask and an executor either fabricates the evidence or mis-registers a rule as info to satisfy it. Suggested fix: state the canonical no-error-added proof shape (a severity assertion plus a lifecycle-gate source census) once, in the ipd-spec or a review checklist, so plan authors stop asking for the exit-0 form. See DECISION 04-3i6rso-D1.
