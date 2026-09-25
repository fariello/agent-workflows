- Id: hj4j0j
- Status: done
- Set: hj4j0j
- Priority: medium
- Work-Kind: bug
- Summary: test_standalone_verify's two refusal tests assume mp289j is still pending, and now fail because it executed

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by f1983f30; tests/test_standalone_verify.py later deleted in 19313eed
- 2026-09-20 created (aw backlog): test_standalone_verify's two refusal tests assume mp289j is still pending, and now fail because it executed

MEASURED at 283b3c92 while executing plan i1hlgx, which changed nothing in either file.

`tests/test_standalone_verify.py::TheAuditCannotTouchTheFinishedPlan` has two failing tests:

  * `test_a_plan_that_has_not_executed_is_refused_rather_than_audited`
  * `test_refusals_are_returned_and_never_raised`

WHY. Both call `runner_shared.plan_audit_target(REPO_ROOT, 'mp289j')` and assert a refusal, on the premise that `mp289j` is a PENDING plan and so must be refused by an audit verb whose contract is 'this is finished and immutable'. That plan is now EXECUTED (`.aw/records/plans/executed/20260908-reverify-01-mp289j-...`, finalized in 548b56b3), so `plan_audit_target` correctly returns NO refusal and the assertions fail. Observed: `AssertionError: '' is not true` at tests/test_standalone_verify.py:273.

THE DEFECT IS IN THE TEST, NOT THE PRODUCT. The verb behaves correctly for a plan in the state it is actually in. The test hardcodes a LIVE plan id6 as a fixture and so has a built-in expiry date: any pending plan it names becomes wrong the moment that plan executes. `test_an_unknown_id6_is_refused_with_its_own_code` in the same class is stable precisely because `zzzzzz` can never resolve.

SUGGESTED FIX. Stop using a live plan id as the not-executed fixture: seed a pending plan in a temp records tree, or assert against a plan whose bucket the test itself controls. Naming any real pending id6 reintroduces the same expiry.

FOUND BY: plan i1hlgx (unrelated change to run_cli.py's absent-ledger message). Present in the before-baseline as well as after, so not caused by that work.
