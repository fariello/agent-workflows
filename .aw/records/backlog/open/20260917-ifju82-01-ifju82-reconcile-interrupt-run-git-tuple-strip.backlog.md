- Id: ifju82
- Status: open
- Set: ifju82
- Priority: medium
- Work-Kind: bug
- Summary: reconcile_item_on_interrupt calls .strip() on _run_git's tuple, raising AttributeError on the no-lane interrupt path

## Workflow history
- 2026-09-17 created (aw backlog): reconcile_item_on_interrupt calls .strip() on _run_git's tuple, raising AttributeError on the no-lane interrupt path

Found while executing plan fujm0y (mergedirty-01), outside its scope.

runner_shared.reconcile_item_on_interrupt (agent_workflows/runner_shared.py:3983) has, at :4046-4047:

    status_out = _run_git(repo, ["status", "--porcelain"])
    holds_work = bool(status_out.strip())

runner_shared._run_git (:407) returns a (returncode, stdout, stderr) TUPLE, not a string, so .strip() raises AttributeError: 'tuple' object has no attribute 'strip'. The static type checker flags it at HEAD independently of this plan's change (verified at HEAD 80077bb3 with the change stashed).

REACHABILITY: the else-branch is taken only when 'lane is None', i.e. an interrupted item with NO work_dir (the non-isolated path). On the isolated path 'lane' is not None and the bug is bypassed, which is why the suite is green. So this is a latent crash on interrupt reconciliation for a non-isolated item rather than an everyday failure.

CONSEQUENCE: the AttributeError would escape during interrupt reconciliation, i.e. exactly when the driver is trying to record an interrupted item's state, so the failure lands on the recovery path.

SUGGESTED FIX: unpack the tuple, e.g. '_rc, status_out, _err = _run_git(...)', matching every other caller in the module. Add a regression test driving reconcile_item_on_interrupt with no work_dir.

NOT FIXED HERE: fujm0y's Scope-Paths cover runner_shared.py, but this line is unrelated to the pre-merge dirty check and touching it would be opportunistic scope broadening.
