- Id: okjz5y
- Status: open
- Set: specaudit
- Priority: low
- Work-Kind: followup
- Summary: Restore tests for spec i4gpto (standalone executed-plan audit) criteria 3, 4, 6, 7, 8

## Workflow history
- 2026-10-25 created (aw backlog): Filed 2026-10-25 from the spec audit (session report).

Commit 19313eed7 deleted tests/test_standalone_verify.py (28 tests). The audit verb works live at HEAD 5db4791c1 (aw oc run audit: audit-plan-not-found and audit-plan-not-executed refusals; agy redirects with rc 2), but criteria 3, 4, 6, 7, 8 have no test. Also fix: the spec's Implemented-by field points at plans/pending/ (plan mp289j is executed), and the audit prompt advertises a diff_basis value lifecycle-commit (runner_shared.py ~34961) that the spec never defines and the code never produces. The spec is still draft and needs the full walk (to-review, reviewed, approved, implementing, implemented).
