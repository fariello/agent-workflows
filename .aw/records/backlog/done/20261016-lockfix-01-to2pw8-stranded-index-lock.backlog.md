- Id: to2pw8
- Status: done
- Set: lockfix
- Priority: high
- Work-Kind: bug
- Summary: Read-only git probes (version describe on every import, status checks) took index.lock; a killed process stranded a 0-byte lock that refused the next commit

## Workflow history
- 2026-10-16 done (aw set): fixed and verified in b50bcb58d (lock-free describe and dirty probe, lockfree_git_argv in every git wrapper, 14 status call sites); regression test tests/test_versioning.py DescribeTakesNoIndexLockTests fails on the old code; full suite shows the same 14 failures as untouched main and no new ones; gate released because the bug is fixed
- 2026-10-16 created (aw backlog): Read-only git probes (version describe on every import, status checks) took index.lock; a killed process stranded a 0-byte lock that refused the next commit

Observed 2026-10-16: twice a 0-byte index.lock appeared in an agent's worktree while a full pytest run was in progress there, refusing the next aw commit. Root cause measured: versioning._git_describe ran 'git describe --dirty' on EVERY import of agent_workflows (__version__); describe --dirty refreshes the index under index.lock whenever a tracked file's stat is stale, and --no-optional-locks does not suppress it for describe (strace, git 2.43). A process killed in that window (test hang guard, timeouts, cancelled agents) leaves the lock. Also 14 read-only 'git status' call sites and 7 git wrappers ran status without --no-optional-locks. Fix: describe without --dirty plus a lock-free dirty probe (status --porcelain --untracked-files=no with --no-optional-locks, verified lock-free and stat-change-correct); git_commit_helper.lockfree_git_argv applied in every git wrapper; literal status calls given --no-optional-locks. Test: tests/test_versioning.py DescribeTakesNoIndexLockTests fails on the old code (index inode rewritten) and passes on the fix.
