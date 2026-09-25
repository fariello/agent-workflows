- Id: 34q6ha
- Status: done
- Set: 34q6ha
- Priority: high
- Work-Kind: bug
- Summary: test_standalone_verify pins plan mp289j as a NOT-executed fixture, but mp289j is now executed, so 2 nodes fail on a clean tree

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: tests/test_standalone_verify.py deleted in 19313eed (same mp289j pin as ad87ah)
- 2026-09-20 created (aw backlog): test_standalone_verify pins plan mp289j as a NOT-executed fixture, but mp289j is now executed, so 2 nodes fail on a clean tree

Two nodes in `tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan` fail on a CLEAN checkout at main (`5211f722`), with no working-tree changes at all:

    FAILED tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan::test_a_plan_that_has_not_executed_is_refused_rather_than_audited
    FAILED tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan::test_refusals_are_returned_and_never_raised

CAUSE, which is a stale fixture rather than a wrong assertion. Both tests use plan `mp289j` as their
example of a plan that has NOT executed, and assert `plan_audit_target(REPO_ROOT, "mp289j").refusal ==
AUDIT_PLAN_NOT_EXECUTED`. That premise expired IN THE SAME RUN that created the test: `807fdfd6` added
the test at ct 1789897199, and `548b56b3` finalized `mp289j` to `.aw/records/plans/executed/` at ct
1789897622, seven minutes later. `mp289j` is now in `executed/`, so the audit target resolves cleanly
and `refusal` is `''`:

    AssertionError: '' != 'audit-plan-not-executed'
    AssertionError: '' is not true

A test that hard-codes a live plan id6 as a lifecycle FIXTURE dates the moment that plan advances. The
fix is to build a pending plan in a tmp_path fixture rather than naming a real one, so the assertion
cannot expire; substituting a currently-pending id6 only moves the expiry date.

SECOND, SMALLER DEFECT found while diagnosing: `runner_shared.resolve_plan_path` does `repo / ".aw"`
without coercing `repo`, so passing a `str` raises `TypeError: unsupported operand type(s) for /: 'str'
and 'str'` instead of accepting a path-like argument as its siblings do (runner_shared.py:5586, reached
from plan_audit_target at runner_shared.py:4799).

Found while executing plan `udgilu`; unrelated to that plan's scope (lifecycle_style).
