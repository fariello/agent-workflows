- Id: dh0uno
- Status: done
- Blocks-Release: next
- Set: statefork
- Priority: high
- Work-Kind: bug
- Summary: Worktree-relative aw state fork: an inner aw invoked with cwd inside a lane worktree resolves .aw/state and .aw/records/runs relative to the worktree, writing a SECOND receipt/run tree that the driver (running from main) cannot see and that teardown destroys

## Workflow history
- 2026-09-02 done (aw set): FIXED and landed in 6771e590. ipd_lifecycle.checkout_control_root is now the single authority for a checkout's .aw control root, keyed on git rev-parse --git-common-dir, and receipt_dir/_runtime_dir route through it, so a lane and the main tree resolve ONE receipt/lock/journal store. _repo_root still returns the PRODUCT tree, because finalize must commit into the tree the agent edited. sync_receipt_into_worktree is a documented no-op in both drivers (with one path, the copy had src == dst). Pinned by tests/test_statefork_dh0uno.py using a REAL git worktree: 8 of its 9 tests fail with the fix reverted. Bare suite 4013 passed, 3 skipped, 4 xfailed. NOTE the old acceptance claim that ~15 test_run_viewer failures ARE this bug was false: they are a gitignored-fixture artifact and pass with run records present and no fix applied. Deferred deliberately (see plan eulhzt): relocating control state out of the repo, which was wtiso Phase 4 and is a separate concern.
- 2026-08-29 graduated (aw set): status set to graduated
- 2026-08-28 created (aw backlog): Worktree-relative aw state fork: an inner aw invoked with cwd inside a lane worktree resolves .aw/state and .aw/records/runs relative to the worktree, writing a SECOND receipt/run tree that the driver (running from main) cannot see and that teardown destroys

ROOT CAUSE: aw resolves its machine-state roots (.aw/state, .aw/records/runs) relative to cwd. Under worktree isolation the driver-spawned agent runs with cwd inside .aw/worktrees/<id6>, so any inner aw (e.g. aw ipd begin/finalize) writes to .aw/worktrees/<id6>/.aw/state/... - a DIFFERENT file from the real one at the main repo root. The driver (from main) then cannot find the receipt/ledger the agent wrote; the fork is invisible to git status (gitignored) and the branch diff (never merged), and is destroyed on teardown_worktree.

RELATION: this is a THIRD facet of the same architecture problem as xmqv5l (stale receipt at finalize) and qyaime (external_directory permission deadlock). All three are addressed by research x03wgn (20260828-wtiso-00): a driver-owned control plane + out-of-repo machine state keyed by git rev-parse --git-common-dir + a typed ExecutionContext/PathResolver so an inner aw ALWAYS resolves control state to one location regardless of cwd, and worker-role lifecycle verbs refuse.

FIX (per x03wgn): typed resolver keyed by checkout-id (git common dir); do NOT copy receipts into lanes; do NOT derive a fresh checkout id from a linked worktree path; startup assertion that all linked worktrees resolve the same control identity; reject the cwd heuristic. See research x03wgn phases 3-4.

DISCOVERED: this session, diagnosing why finalizes/merge-backs fail under worktree isolation.
