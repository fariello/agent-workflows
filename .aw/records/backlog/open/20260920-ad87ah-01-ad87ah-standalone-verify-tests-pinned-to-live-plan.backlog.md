- Id: ad87ah
- Status: open
- Blocks-Release: next
- Set: ad87ah
- Priority: medium
- Work-Kind: bug
- Summary: two standalone-verify tests assert a plan is not executed, but that plan has since executed, so they are red on a clean tree

## Workflow history
- 2026-09-20 created (aw backlog): Pre-existing red on a clean tree; found while establishing a baseline for plan h5pyqa.

## What is wrong

These two are RED on an unmodified tree at `8b25d779`:

```
FAILED tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan::test_refusals_are_returned_and_never_raised
FAILED tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan::test_a_plan_that_has_not_executed_is_refused_rather_than_audited
```

Both assert that `runner_shared.plan_audit_target(REPO_ROOT, "mp289j")` refuses with
`AUDIT_PLAN_NOT_EXECUTED`. They get `refusal == ""`, because plan `mp289j` HAS since executed and now lives
at `.aw/records/plans/executed/20260908-reverify-01-mp289j-...ipd.md`. The production predicate is behaving
CORRECTLY; the tests pin a fact about the LIVE plan corpus that has since changed.

This is the defect class backlog `yw6759` ("approval-gate test pinned to live plan corpus") already names, so
the fix should follow whatever remedy that item settles on: assert against a committed fixture corpus rather
than against the repository's own moving plan tree.

## Why it blocks release

Not for its own severity (it is test rot, not a product defect) but because a permanently red suite is
exactly what the `h5pyqa` incident turned on: every lane's trust signal is the FULL SUITE, so two standing
failures refuse EVERY lane's integration until an agent answers the gate question. That makes stale tests a
release-blocking condition here in a way they would not be in another repository.
