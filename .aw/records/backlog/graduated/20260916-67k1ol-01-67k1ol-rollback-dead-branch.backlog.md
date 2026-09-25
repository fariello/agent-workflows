- Id: 67k1ol
- Status: graduated
- Graduated-To: rollbackdead
- Work-Kind: bug
- Blocks-Release: next
- Set: 67k1ol
- Priority: low
- Summary: _rollback_precommit step 3 issues an identical git restore --staged in both branches of an if/else on prior_index

## Workflow history
- 2026-09-25 graduated (aw set): graduated into rollbackdead plan zbh2yt; not just a dead branch: rollback resets a staged plan edit to HEAD
- 2026-09-16 created (aw backlog): _rollback_precommit step 3 issues an identical git restore --staged in both branches of an if/else on prior_index

Found 2026-09-16 while executing plan `4xt6u4` (reading `_rollback_precommit`, which that plan modifies). Step 3 of `agent_workflows/ipd_lifecycle.py::_rollback_precommit` reads:

    owned = journal.get("owned_paths", [])
    prior_index = journal.get("git_index_entries", {})
    for p in owned:
        # Reset the index entry for this owned path to its recorded state without staging others.
        if p in prior_index:
            _git(repo_root, ["restore", "--staged", "--", p])
        else:
            _git(repo_root, ["restore", "--staged", "--", p])

Both arms are BYTE-IDENTICAL, so the `if` is a no-op and `prior_index` (and therefore the journal's `git_index_entries` snapshot) is not actually consulted to decide anything. Two readings, and it matters which is true:

1. the branch is vestigial and should collapse to the unconditional call, in which case `git_index_entries` may be dead weight in the journal in the same way `index_json_before`/`index_md_before` once were; or
2. the two cases were MEANT to differ (a path that HAD a recorded index entry should be restored TO that entry, whereas one that had none should merely be unstaged), in which case this is a real bug and the recorded entries are silently ignored.

Reading (2) looks more likely given the comment says 'to its recorded state', which is a thing only the recorded entry can supply.

NOT CHANGED, deliberately: plan `4xt6u4` is scoped to step 4 and its sibling Order 04 (`u23gbn`) owns step 2, and the plan's own scope check explicitly asks that a wider audit of `_rollback_precommit` 'should be its own plan'. Filed as that follow-up. No behavior change was observed to depend on this either way; the suite passes 137/137 in `tests/test_orchestrator_retirement.py`.
