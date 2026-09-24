- Id: 8bif6g
- Status: done
- Blocks-Release: next
- Set: 8bif6g
- Priority: high
- Work-Kind: bug
- Summary: a lane running with a worker AW_EXECUTION_ROLE silently masks test failures, so a bare suite run cannot validate a plan

## Workflow history
- 2026-09-23 done (aw set): Already FIXED by the root conftest.py session scrub, which pops AW_EXECUTION_ROLE at import time before any test module is collected. VERIFIED at HEAD 22cf67d9 on the affected family: tests/test_ipd_lifecycle_cli.py gives '89 passed' BOTH with and without AW_EXECUTION_ROLE=worker in the ambient environment, so the marking no longer changes the result and a bare suite run means the same thing whether a human or a runner turn typed it. The conftest records why the fix is sited there rather than in the runners: the marking on the AGENT is deliberate and load-bearing (it is what makes AW-LIFECYCLE-ROLE-001 fire on a lane agent that tries to finalize its own plan, incident i452hf), so removing it there would restore a real defect to fix a reporting one. TWO HONEST LIMITS ARE CARRIED FORWARD RATHER THAN CLOSED HERE, both to IPD 8i0xa7 (rolevac): the scrub made the worker-role guard's own test VACUOUS (6z5yos), and because the fix lives in this repo's conftest rather than in the runner, a MANAGED TARGET REPO that does not ship it is still exposed to the same false-baseline harm. Closed via the SATISFIED path.
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): a lane running with a worker AW_EXECUTION_ROLE silently masks test failures, so a bare suite run cannot validate a plan

Found while executing plan fujm0y (mergedirty-01) inside an isolated lane worktree.

SYMPTOM: a bare 'python3 -m pytest' in the lane reported 31 failed both BEFORE and AFTER the change, so the AFTER-minus-BEFORE regression set (compared by node ID, as the execution contract requires) was EMPTY. It was not. Re-running the same suite with the runner role exposed TWO genuine regressions the change had introduced, in tests that the bare run had counted among its 31 'pre-existing' failures.

CAUSE: the lane runs with AW_EXECUTION_ROLE set to a worker. Any test that drives a lifecycle transition (e.g. via 'aw ipd begin') is refused with AW-LIFECYCLE-ROLE-001 ('the runner owns begin/finalize for managed lanes; a worker-role process must not run them') and aborts BEFORE reaching its assertions, typically as a KeyError on state the refused call never wrote. The refusal is correct policy; the problem is that it is indistinguishable from, and MASKS, a real assertion failure in the same test.

WHY THIS MATTERS: the standard validation protocol (measure a baseline, compare failure sets by node ID) is defeated, because a test that fails for an environmental reason in BOTH runs cancels out and can hide any real breakage inside itself. An agent following the contract exactly still reports 'regression set empty' while shipping broken tests. Measured: 31 masked node IDs in this lane, 2 of which were genuinely broken by the change under test.

AFFECTED (observed): tests/test_oc_runipd.py, tests/test_agy_runipd_cli.py, tests/test_ipd_lifecycle_cli.py, tests/test_runner_backlog_close_in_lane.py, tests/test_novalnomerge_integration.py.

POSSIBLE FIXES (not chosen here): (a) have such tests SKIP explicitly under a worker role, so they are visibly not-run rather than failed, which restores the node-ID comparison; (b) have the lane prompt tell the agent its role and instruct it to validate under the runner role; (c) have the affected tests set the runner role in their own fixture, since they are exercising runner-owned behavior.

NOT FIXED HERE: entirely outside fujm0y's scope (its Scope-Paths cover the pre-merge dirty check). Reported because a validation protocol that silently fails closed-eyed is a hazard to every plan executed in a lane, not just this one.
