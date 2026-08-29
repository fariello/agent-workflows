# IPD: Phase 5: real candidate-merge integration + full crash recovery (integration lock, expected-target-tip recheck, driver publication projection, aw recover/doctor, cross-platform locks, process-tree kill)

- Date: 2026-08-28
- Kind: child
- Concern: The runner's integration path is GREENWASH-SHAPED: it validates a stitched diff STRING, not an actual merged git tree. `integrate_lane_branch` (oc_runipd.py:508-560; agy_runipd.py:646-...) builds a `LaneOutcome` from `git diff base..branch` (oc_runipd.py:494), then calls `orchestrate_isolation.execute_merge_and_revalidate_gate` (orchestrate_isolation.py:947), whose "full revalidation" (:1121-1123) invokes a `full_validation_runner(combined_diff, merged_files)` CALLBACK that the driver wires to `make_integration_validation_runner._runner` which literally `return True` (oc_runipd.py:587-588; agy_runipd.py:635-...). Only AFTER the gate "passes" does the driver run the REAL `git merge --ff-only` (oc_runipd.py:541), so validation ran on a diff, never on the exact tree that becomes main; there is NO checkout-level integration lock, NO journaled `expected_target_tip`, and NO recheck/rebuild if main advanced during validation. The lease table is pure IN-MEMORY (`worktree_lease.LeaseTable`, worktree_lease.py:144-192; `snapshot()` at :190 is never persisted), so a crash loses all lane allocation/scope/ownership. Locking is POSIX-only `fcntl.flock` (oc_runipd.py:17,671; agy_runipd.py:18,768; project_registry.py:277; run_ledger_store.py:267; agy_sessions.py:38) and the process-tree kill is POSIX-only `os.killpg`/`getpgid` (oc_runipd.py:1566-1570; agy_runipd.py:1663-1667) with no Windows Job Object. There is no `aw recover <run-id>` and no `aw doctor --lanes` (cli.py registers `doctor` at :777/:7773 but no `--lanes`; `run_recovery.py` has crash/resume primitives but no lane/candidate/lock reconciliation). This maps exactly to research x03wgn Section 9 finding 6 ("current single-lane integration validation is not an actual merged-tree validation ... callback can return true before the later Git merge"), findings 5 (fcntl not portable) and the Section 7 hazards "Validation occurs before actual merge", "Target advances during validation", "In-memory lease lost on crash", "POSIX-only locking", "Process child survives parent kill". This Phase 5 replaces the diff/callback gate with an ACTUAL candidate-integration worktree (lock -> journal expected tip -> candidate at that tip -> merge lane -> full validation on the EXACT candidate tree -> re-read real target tip and rebuild if it moved -> journaled target update, never auto-stash/overwrite dirty user main), adds a driver-owned durable publication projection merged+validated with the product, persists lane allocation/scope/cleanup events so leases reconstruct after crash, implements `aw recover <run-id>` + `aw doctor --lanes`, replaces `fcntl` with a cross-platform lock abstraction, and adds a Windows Job Object process-tree kill. It implements the x03wgn Section 7 "Required recovery invariants" (esp. 2, 6, 7, 8, 9). Research x03wgn Section 5 (integration algorithm, dependencies-between-lanes, stale-bases/conflicts), Section 7 (failure-mode audit + required recovery invariants + adversarial/crash-injection tests), and Section 8 "Phase 5" prescribe this; references R2 (git-worktree), R4 (git-clone), R5 (git-merge `--ff-only`), R12 (fcntl Unix-only).
- Scope: Replace the diff/callback integration with a real candidate-integration worktree in the shared integration module: (1) `orchestrate_isolation` gains a candidate-merge integrator that acquires the checkout-level integration lock, journals `expected_target_tip`, creates a candidate worktree/branch AT that tip (REUSING `worktree_lease.allocate_worktree`), merges the lane tip there (`git merge --ff-only` where topology permits, x03wgn R5), runs the FULL validation on the EXACT candidate tree (not a diff string, not a `return True` callback), re-reads the REAL target tip and REBUILDS the candidate if it moved, then updates the target through a journaled operation that PAUSES (never auto-stashes/overwrites) on a dirty user main; (2) both drivers (`oc_runipd.integrate_lane_branch`, `agy_runipd.integrate_lane_branch`) call the new candidate integrator and DELETE the `make_integration_validation_runner` `return True` stub as the integration authority. Add a driver-owned durable PUBLICATION projection (sanitized ledger -> tracked `.aw/records`) merged into the SAME candidate and validated with the product tree. Persist lane allocation/scope/cleanup EVENTS to the run ledger and add a lease-reconstruction path so `worktree_lease.LeaseTable` rebuilds from durable events + `git worktree list --porcelain -z` after a crash. Add a cross-platform lock abstraction (`platform_lock`) and route the run/integration/ledger/migration locks through it (replacing raw `fcntl`), and a Windows Job Object process-tree kill behind the same `terminate_process` seam. Add `aw recover <run-id>` (reconciles ledger, refs, `git worktree list`, locks, journals, candidates, submissions, harvested artifacts WITHOUT a model) and `aw doctor --lanes`. Does NOT re-author the Phase-3 resolver or the Phase-4 out-of-repo relocation (DEPENDS on executed:58ha43); does NOT add the OS-sandbox hard mode (Phase 6, 1o4eif).
- Scope-Paths: agent_workflows/platform_lock.py, agent_workflows/candidate_integration.py, agent_workflows/publication_projection.py, agent_workflows/lane_recovery.py, agent_workflows/orchestrate_isolation.py, agent_workflows/worktree_lease.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/doctor.py, agent_workflows/cli.py, tests/test_platform_lock.py, tests/test_candidate_integration.py, tests/test_publication_projection.py, tests/test_lane_recovery.py, tests/test_crash_injection_integration.py, tests/test_process_tree_kill.py
- Item-Dependencies: executed:58ha43
- Status: to-review
- Set: wtiso
- Order: 6
- Highest E allocated: 16
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 2c122z

## Workflow history
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Replace the runner's greenwash-shaped diff/callback integration gate - which validates a stitched diff STRING via a `return True` callback (oc_runipd.py:587-588) BEFORE the real `git merge --ff-only` (oc_runipd.py:541) - with an ACTUAL candidate-integration worktree that acquires a checkout-level integration lock, journals `expected_target_tip`, creates a candidate at that tip, merges the lane tip there (`--ff-only` where possible, x03wgn R5), runs FULL validation on the EXACT candidate tree, re-reads the real target tip and rebuilds if it moved, then updates the target through a journaled op that never auto-stashes/overwrites a dirty user main; adds a driver-owned durable publication projection (sanitized ledger -> tracked `.aw/records`) merged+validated with the product tree; persists lane allocation/scope/cleanup events so `worktree_lease.LeaseTable` reconstructs after a crash from durable events + `git worktree list`; implements `aw recover <run-id>` and `aw doctor --lanes` that reconcile ledger/refs/worktrees/locks/journals/candidates WITHOUT a model; and replaces POSIX-only `fcntl`/`os.killpg` with a cross-platform lock abstraction + Windows Job Object process-tree kill. It satisfies the x03wgn Section 7 "Required recovery invariants" (2, 6, 7, 8, 9) and the Section 7 adversarial/crash-injection acceptance tests. Acceptance is pasted command output plus observed git+filesystem state (a candidate tree whose tip is the exact validated tree; a target that advanced during validation FORCING a rebuild; a fabricated/moved tip that is DETECTED; a crash at each journal boundary that `aw recover` reconciles to one unambiguous state), never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: cross-platform lock abstraction (x03wgn Section 7 "POSIX-only locking" hazard, R12; Section 8 Phase 5 item 6)

- [ ] E-01 Add `agent_workflows/platform_lock.py` with an `exclusive_file_lock(path)` context manager that acquires a NON-BLOCKING exclusive lock on `path` and raises `LockHeldError` if already held, using `fcntl.flock` on POSIX and `msvcrt.locking` on Windows, selected by `sys.platform` (per R12, `fcntl` is Unix-only). The POSIX branch preserves the EXACT current semantics of `oc_runipd.run_lock` (oc_runipd.py:666-683): `LOCK_EX | LOCK_NB`, `BlockingIOError` -> raise, `LOCK_UN` on exit.
  - Depends on: none
  - Expected outcome: `platform_lock.exclusive_file_lock(p)` yields a held lock; a second concurrent `exclusive_file_lock(p)` in another process raises `LockHeldError`; on POSIX the underlying call is `fcntl.flock(..., LOCK_EX|LOCK_NB)` and it releases on context exit (no leaked lock).
  - Execution state: pending

- [ ] E-02 Add `platform_lock.held_by_diagnostics(path) -> dict` returning recovery diagnostics (`pid`, process `start_time`, `boot_id`/`session_id`, `host`) written into the lockfile body, so a stale lock is reclaimed by verifying process start + boot identity, NOT PID alone (x03wgn Section 7 "Stale PID lock" / "PID reuse" hazards). The lock body format stays a superset of the current `pid=<pid> started=<ts>` line (oc_runipd.py:678) so existing readers still parse it.
  - Depends on: E-01
  - Expected outcome: after acquiring a lock, `held_by_diagnostics(path)` returns a dict containing the current `pid`, a non-empty `start_time`, and a `boot_id`/`session_id`; a reclaim helper treats a lock whose recorded `start_time`+`boot_id` no longer match a live process as STALE and reclaimable, and a matching live process as HELD.
  - Execution state: pending

- [ ] E-03 Route the driver run lock through `platform_lock`: replace the raw `fcntl` body of `oc_runipd.run_lock` (oc_runipd.py:666-683) and `agy_runipd.run_lock` (agy_runipd.py:762-780) with `platform_lock.exclusive_file_lock`, keeping the `driver.lock` path and the `DriverError("Run is already controlled by another process")` message. Remove the now-unused `import fcntl` from both driver modules if no other reference remains.
  - Depends on: E-01
  - Expected outcome: `oc_runipd.run_lock(run_dir)` and `agy_runipd.run_lock(run_dir)` still raise `DriverError` on a second concurrent hold, now via `platform_lock`; `grep -n "import fcntl" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` returns no matches (both drivers no longer import fcntl directly).
  - Execution state: pending

### Task group 2: Windows Job Object process-tree kill behind the terminate_process seam (x03wgn Section 7 "Process child survives parent kill" hazard; Section 8 Phase 5 item 6)

- [ ] E-04 Add a `_kill_process_tree(process)` helper in `platform_lock.py` (or a sibling `platform_process.py` if cleaner - one module, chosen at implementation) that on POSIX preserves the EXACT `os.killpg(os.getpgid(pid), sig)` behavior currently inlined in `oc_runipd.terminate_process` (oc_runipd.py:1566-1570) and on Windows uses a Job Object (`CreateJobObject` + `AssignProcessToJobObject` + `TerminateJobObject`, or `taskkill /T /F` fallback) so the whole child tree dies. Selected by `sys.platform`; no behavior change on POSIX.
  - Depends on: none
  - Expected outcome: on POSIX, `_kill_process_tree` sends the signal to the process GROUP (`os.killpg` path exercised, verified by a spawned child in the same session being reaped); the Windows branch is present and selected by `sys.platform` (unit-testable by monkeypatching `sys.platform` + mocking the Job Object calls).
  - Execution state: pending

- [ ] E-05 Route both drivers' `terminate_process` (oc_runipd.py:1559-...; agy_runipd.py:...1663-1667) through `_kill_process_tree` so the POSIX group-kill and the new Windows Job Object path share ONE seam, and `start_new_session=True` at launch (oc_runipd.py:1687; agy_runipd.py:1763) is paired with the matching kill on each platform.
  - Depends on: E-04
  - Expected outcome: `oc_runipd.terminate_process` and `agy_runipd.terminate_process` both delegate the tree kill to `_kill_process_tree`; a POSIX test spawns a parent that forks a child into its session, calls `terminate_process`, and asserts BOTH pids are gone (no orphan survives the parent kill).
  - Execution state: pending

### Task group 3: persist lane allocation/scope/cleanup events + reconstruct leases after crash (x03wgn Section 7 "In-memory lease lost on crash" hazard + recovery invariants 2,7; Section 8 Phase 5 item 1)

- [ ] E-06 Add durable lane-lifecycle EVENTS to the run ledger: when a worktree is allocated (`worktree_lease.allocate_worktree`, worktree_lease.py:70-103), emit a `lane_allocated` event recording lane_id, branch, absolute worktree path, and base_commit sha; when the lease claims paths (`LeaseTable.claim`, worktree_lease.py:164-181), emit a `lane_scope_claimed` event recording the exact owned path set; when a lane is torn down (`teardown_worktree`, worktree_lease.py:106-122), emit a `lane_cleanup_authorized` event. Emit through the existing ledger append (the `os.fsync`'d append at oc_runipd.py:660-662 pattern / `run_ledger_store`), NOT a new store.
  - Depends on: none
  - Expected outcome: allocating a worktree, claiming a scope, and tearing it down each append exactly one durable ledger event (`lane_allocated`/`lane_scope_claimed`/`lane_cleanup_authorized`) carrying lane_id+branch+path+base (allocate), the owned path set (claim), and the cleanup authorization (teardown); the events survive process exit (re-read from disk).
  - Execution state: pending

- [ ] E-07 Add `agent_workflows/lane_recovery.py` with `reconstruct_leases(run_id) -> LeaseTable` that rebuilds the in-memory `worktree_lease.LeaseTable` PURELY from the durable `lane_allocated`/`lane_scope_claimed`/`lane_cleanup_authorized` events (no model), so ownership is recovered after a crash. A lane with an allocate+claim but NO cleanup event is reconstructed as still-owning its paths; a lane with a cleanup event releases them.
  - Depends on: E-06
  - Expected outcome: given a ledger with lane A allocated+claiming `["x.py"]` and NO cleanup, and lane B allocated+claiming `["y.py"]`+cleanup, `reconstruct_leases(run_id).owner_of("x.py") == "A"` and `owner_of("y.py") is None`; the reconstruction reads ONLY durable events (a test with no live process still reconstructs correctly).
  - Execution state: pending

- [ ] E-08 Add `lane_recovery.reconcile_worktrees(repo, run_id) -> dict` that cross-checks the reconstructed leases against `git worktree list --porcelain -z` (x03wgn R2) and classifies each lane as `live` (worktree present + branch present), `orphaned-metadata` (branch present, worktree path missing), or `missing` (neither), returning the classification map WITHOUT deleting anything (recovery invariant 8: fail closed on disagreement, never infer success from an absent directory).
  - Depends on: E-07
  - Expected outcome: for a repo with one real allocated worktree and one lane whose worktree directory was `rm`'d out from under it, `reconcile_worktrees` classifies the first `live` and the second `orphaned-metadata`, deletes NOTHING, and a lane recorded allocated but never created classifies `missing`.
  - Execution state: pending

### Task group 4: real candidate-merge integrator with lock + expected-tip journal + rebuild-on-move (x03wgn Section 5 "Integration algorithm" steps 1-10; Section 7 hazards "Validation occurs before actual merge"/"Target advances during validation"/"Two runs integrate simultaneously"; recovery invariants 7,9)

- [ ] E-09 Add `agent_workflows/candidate_integration.py` with `integrate_candidate(repo, lane_tip, expected_target_tip, target_ref, full_validation, *, publication_tree=None, dirty_main_policy="pause") -> IntegrationResult` that performs x03wgn Section 5 steps 1-2: acquire the checkout-level integration lock at `checkout_state_root(<checkout-id>)/integration/lock` via `platform_lock.exclusive_file_lock` (E-01), then journal `expected_target_tip` (+ target_ref, lane_tip, run/lane/attempt, phase) to a durable candidate-integration journal BEFORE any git mutation (recovery invariant 7). The `<checkout-id>` and `checkout_state_root` come from the Phase-4 (58ha43) out-of-repo location; do NOT construct `.aw/state` (the Phase-3 AST guard forbids it).
  - Depends on: E-01
  - Expected outcome: `integrate_candidate` holds the single checkout-level integration lock while running (a second concurrent call raises `LockHeldError`), and writes a durable journal entry recording `expected_target_tip`+`target_ref`+`lane_tip`+phase BEFORE it creates the candidate worktree (the journal file exists and names the tip if the process is killed immediately after step 2).
  - Execution state: pending

- [ ] E-10 Implement x03wgn Section 5 steps 3-6 in `integrate_candidate`: create a DISPOSABLE candidate worktree/branch AT `expected_target_tip` (REUSING `worktree_lease.allocate_worktree(repo, "<candidate-id>", base_commit=expected_target_tip)`, worktree_lease.py:70), `git merge --ff-only <lane_tip>` there (x03wgn R5 - `--ff-only` refuses rather than creating a merge when not a fast-forward), and on merge conflict ABORT the candidate merge, preserve the lane, record conflict paths+both tips, and return a `conflict` result (never resolve in the user's main worktree). Then run `full_validation(candidate_worktree_path)` on the EXACT candidate tree - a real callable receiving the CANDIDATE WORKTREE PATH, replacing the `full_validation_runner(combined_diff, merged_files)` diff-string signature (orchestrate_isolation.py:951,1123).
  - Depends on: E-09
  - Expected outcome: `integrate_candidate` runs `full_validation` against the candidate WORKTREE PATH (a test asserts the callback received a real directory whose `git rev-parse HEAD` equals the post-merge candidate tip, NOT a diff string); a lane whose merge conflicts returns `status="conflict"` with the conflict paths + both tips recorded and leaves `target_ref` and the user main untouched.
  - Execution state: pending

- [ ] E-11 Implement x03wgn Section 5 steps 7-8 in `integrate_candidate`: after validation passes, RE-READ the real `target_ref` tip; if it DIFFERS from the journaled `expected_target_tip`, discard/retain the candidate for diagnosis and REBUILD against the new tip (re-journal + recreate candidate at the new tip + re-merge + re-validate), looping until the tip is stable through validation; only then update `target_ref` through a journaled `git update-ref`/`--ff-only` op. If the user's main working tree is DIRTY, PAUSE per `dirty_main_policy` (never auto-stash/reset/overwrite - x03wgn Section 7 "Dirty user main worktree" hazard).
  - Depends on: E-10
  - Expected outcome: a test where `target_ref` ADVANCES between the journal write and the post-validation re-read asserts `integrate_candidate` REBUILDS (a second candidate created at the new tip, re-validated) rather than updating the target from the stale candidate; a test with a dirty main worktree asserts the target update PAUSES (returns `status="paused-dirty-main"`) and the dirty files are byte-identical/untouched afterward (no stash, no reset).
  - Execution state: pending

- [ ] E-12 Record the integrated commit, validation evidence, and cleanup authorization to the candidate-integration journal BEFORE removing the candidate/lane (x03wgn Section 5 step 10; recovery invariant 7), and tear down the disposable candidate worktree via `worktree_lease.teardown_worktree` only after that authorization event is durable. On any non-passing outcome, PRESERVE the lane branch (recovery invariant 2: branch not deleted until integration or explicit abandonment is durably recorded).
  - Depends on: E-11
  - Expected outcome: a successful integration writes an `integrated` journal event naming the target tip + validation evidence BEFORE the candidate teardown (verified by killing after the ref update but before teardown: `aw recover` finds the `integrated` event and completes cleanup idempotently); a failed integration leaves the lane branch present (`git rev-parse <lane-branch>` succeeds).
  - Execution state: pending

- [ ] E-13 Rewire BOTH drivers' `integrate_lane_branch` (oc_runipd.py:508-560; agy_runipd.py:646-...) to call `candidate_integration.integrate_candidate` with a REAL `full_validation` that runs the actual validation command in the candidate worktree, and DELETE `make_integration_validation_runner`'s `return True` stub as the integration authority (oc_runipd.py:575-590; agy_runipd.py:635-...). The diff-oriented `execute_merge_and_revalidate_gate` (orchestrate_isolation.py:947) is retained only for its pre-merge conflict/stale-base/scope DETECTION; the merged-TREE validation authority now lives in `integrate_candidate`.
  - Depends on: E-12
  - Expected outcome: `grep -n "return True" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` shows the `make_integration_validation_runner` `_runner` no longer returns an unconditional True as integration authority (the function is removed or its stub is replaced by a real candidate-tree validation call); a driver integration test asserts `integrate_lane_branch` validates the merged CANDIDATE tree and refuses to update main when candidate validation fails.
  - Execution state: pending

### Task group 5: driver-owned durable publication projection merged+validated with the product (x03wgn Section 5 "Output harvest and durable publication"; Section 8 Phase 5 item 3; Section 2 "Durable project report/decision publication" retention class)

- [ ] E-14 Add `agent_workflows/publication_projection.py` with `project_publication(run_id, candidate_worktree) -> tuple[Path, ...]` that renders a SANITIZED projection of completed control-ledger events (decisions, reports, walkthroughs, plan records) into tracked `.aw/records/...` paths INSIDE the candidate worktree, EXCLUDING live machine state (receipts, locks, session logs, raw prompts, recovery journals) so those never enter Git (x03wgn Section 2 "Durable project report/decision publication" + "live receipts, locks, sessions, and journals remain untracked machine state"). Wire `integrate_candidate` (E-10) to accept this projection as the `publication_tree` so the projection is committed into the SAME candidate and validated with the product tree.
  - Depends on: E-10
  - Expected outcome: `project_publication` writes sanitized `.aw/records/...` files into the candidate worktree and writes NO receipt/lock/session/journal path there (a test asserts the projected file set intersects `.aw/records/` but is disjoint from any receipt/lock/session/journal path); `integrate_candidate` validates the combined product+publication candidate tree as one unit (the validation callback sees both the product change and the projected records present in the candidate worktree).
  - Execution state: pending

### Task group 6: aw recover <run-id> + aw doctor --lanes reconcile without a model (x03wgn Section 7 recovery invariant 9; Section 8 Phase 5 item 4)

- [ ] E-15 Implement `lane_recovery.recover(repo, run_id) -> RecoveryReport` and register `aw recover <run-id>` as a top-level subcommand in `cli.py` (via the `add_subparsers` at cli.py:609, mirroring the Phase-4 `migrate-runtime-state` registration). `recover` reconciles the ledger, refs, `git worktree list --porcelain -z`, locks (via `platform_lock.held_by_diagnostics`, E-02), candidate-integration journals, submissions, and harvested artifacts into ONE unambiguous state map WITHOUT a model, and FAILS CLOSED on disagreement (recovery invariant 8-9). It REUSES `run_recovery.py` crash/resume primitives (run_recovery.py:366,390,424) for the run-step layer and adds the lane/candidate/lock layer.
  - Depends on: E-08, E-12
  - Expected outcome: `python3 -m agent_workflows recover <run-id>` prints a reconciliation report classifying every retained worktree/branch/lock/candidate/journal (with a non-zero exit + explicit disagreement message when the ledger and git refs disagree), and reconciles a crash-at-target-update run to the correct post-update state using ONLY the durable journal + refs (no model call).
  - Execution state: pending

- [ ] E-16 Add a `--lanes` flag to `aw doctor` (extend `doctor.run`, doctor.py:1434; the `doctor` command at cli.py:777/:7773) that reports every reconstructed lane's classification (`live`/`orphaned-metadata`/`missing` from E-08), each held lock's diagnostics (E-02), and any candidate-integration journal that is mid-transaction, so an operator sees "what needs attention" for lanes WITHOUT a model. Read-only (probes, never mutates), matching the existing doctor probe pattern (doctor.py:198-519).
  - Depends on: E-08, E-15
  - Expected outcome: `python3 -m agent_workflows doctor --lanes` on a repo with one live lane and one orphaned-metadata lane prints both with their classification and any held-lock diagnostics, mutates nothing (a `git status` before/after is identical), and exits 0 when all lanes are `live`/cleanly reconciled and non-zero when an `orphaned-metadata`/mid-transaction lane needs attention.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The two host drivers are deliberate near-parity twins and BOTH must change symmetrically: `integrate_lane_branch` (oc_runipd.py:508-560, agy_runipd.py:646-...), `make_integration_validation_runner` (`return True` stub: oc_runipd.py:575-590, agy_runipd.py:635-...), `run_lock` (fcntl: oc_runipd.py:666-683, agy_runipd.py:762-780), `terminate_process` (os.killpg: oc_runipd.py:1559-1585/:1566-1570, agy_runipd.py:...1663-1667), `start_new_session=True` (oc_runipd.py:1687, agy_runipd.py:1763). Any Phase-5 driver change lands in both to avoid drift.
- The integration authority TODAY is diff+callback, not tree: `orchestrate_isolation.execute_merge_and_revalidate_gate` (orchestrate_isolation.py:947) builds `combined_diff` from `outcome.diff` strings (:1043,1092-1096) and calls `full_validation_runner(combined_diff, merged_files)` (:951,1123); the driver wires that runner to `_runner` which `return True` (oc_runipd.py:587-588). The REAL `git merge --ff-only` runs AFTER the gate passes (oc_runipd.py:541). This is the exact greenwash gap x03wgn Section 9 finding 6 names.
- The lease table is pure in-memory: `worktree_lease.LeaseTable` uses `self._owner`/`self._held` dicts (worktree_lease.py:152-156); `snapshot()` (worktree_lease.py:190-192) is documented "for checkpointing/inspection" but nothing persists it - a crash loses all ownership (x03wgn Section 7 "In-memory lease lost on crash").
- Worktree allocation/teardown is already factored: `worktree_lease.allocate_worktree` (worktree_lease.py:70-103, branch `aw/lane/<lane>`, base_commit arg) and `teardown_worktree` (worktree_lease.py:106-122). The candidate integrator REUSES `allocate_worktree(..., base_commit=expected_target_tip)` for its disposable candidate.
- Locking is POSIX-only `fcntl.flock(LOCK_EX|LOCK_NB)`: oc_runipd.py:17/:671, agy_runipd.py:18/:768, project_registry.py:18/:277, run_ledger_store.py:18/:267, agy_sessions.py:12/:38 (x03wgn Section 9 finding 5, R12). This phase adds `platform_lock` and routes the RUN + INTEGRATION locks through it (the ledger/registry/session locks are out of this phase's Scope-Paths - noted as under-scope-with-reason).
- The process-tree kill is POSIX-only: `os.killpg(os.getpgid(pid), sig)` inside `terminate_process` (oc_runipd.py:1566-1570, agy_runipd.py:1663-1667), paired with `start_new_session=True` (oc_runipd.py:1687). No Windows Job Object exists (x03wgn Section 7 "Process child survives parent kill").
- Recovery/doctor scaffolding EXISTS to reuse, not fork: `run_recovery.py` has `resume` (:366), `reconcile_unknown_outcome` (:390), `recover_crash` (:424) for the run-step layer; `doctor.py` has a probe pattern (`probe_git`:198, `probe_environment`:291, `run`:1434); the `doctor` command is registered at cli.py:777 / dispatched at :7773. There is NO `recover` command and NO `--lanes` flag yet.
- The journaled/locked migration engine is `layout_migration.MigrationManager` (layout_migration.py:259, `_acquire_lock`:647, `lock_file`:283, `execute_migration`, `rollback_migration`); the candidate-integration journal MIRRORS its crash-safe write-temp+atomic-rename+phase-before-destructive pattern rather than inventing a new one.
- Top-level `aw` subcommands register via `parser.add_subparsers(dest="command", ...)` at cli.py:609 (the Phase-4 `migrate-runtime-state` and this phase's `recover` register there).
- The checkout-id + out-of-repo `checkout_state_root` come from Phases 3-4 (7p9n2v/58ha43): the integration lock + candidate journal live under `checkout_state_root(<checkout-id>)/integration/` (out of the repo). This child DEPENDS on executed:58ha43 and must not re-derive identity or construct raw `.aw/state` (the Phase-3 AST guard forbids it).
- Tests are `unittest`-style under `tests/`, launching drivers as `python3 -m agent_workflows.oc_runipd` with `PYTHONPATH` pinned to `REPO_ROOT`; new tests follow that convention and use throwaway git repos + injected faults.

## Findings

| # | Finding | Evidence (x03wgn section + real file:line + reference) |
|---|---|---|
| F1 | Integration validates a stitched DIFF STRING via a `return True` callback BEFORE the real git merge - it never validates the merged tree. | x03wgn Section 9 finding 6 ("current single-lane integration validation is not an actual merged-tree validation ... the inspected callback can return true before the later Git merge") + Section 7 "Validation occurs before actual merge"; `execute_merge_and_revalidate_gate` diff/callback (orchestrate_isolation.py:947,951,1043,1092-1096,1123); `_runner` `return True` (oc_runipd.py:587-588; agy_runipd.py:635-...); real merge AFTER pass (oc_runipd.py:541). |
| F2 | The correct algorithm: lock -> journal expected tip -> candidate at that tip -> merge lane (`--ff-only`) -> validate the EXACT candidate tree -> re-read target tip and rebuild if moved -> journaled target update; never resolve conflicts in / auto-stash the user's dirty main. | x03wgn Section 5 "Integration algorithm" steps 1-10; R5 (git-merge `--ff-only` refuses rather than creating a merge); Section 7 hazards "Target advances during validation", "Dirty user main worktree", "Merge conflict". |
| F3 | Exactly one checkout-level integration lock serializes candidate construction + target update across runs; two runs integrating simultaneously must let exactly one proceed and the other rebuild. | x03wgn Section 5 step 1 + Section 2 "Checkout integration lock" retention class ("serializes candidate construction and target ref update across runs ... distinct from a run driver lock"); Section 7 "Two runs integrate simultaneously". |
| F4 | The in-memory lease table loses all lane ownership on a crash; allocation/scope/cleanup must be durable events and leases must reconstruct from them + `git worktree list`. | x03wgn Section 7 "In-memory lease lost on crash" ("Persist allocation/scope events and lane registry snapshot; reconcile with `git worktree list --porcelain -z`") + recovery invariants 2,7; R2; in-memory `LeaseTable` (worktree_lease.py:144-192). |
| F5 | Durable publication is a SANITIZED ledger projection merged+validated WITH the product tree; live receipts/locks/sessions/journals never enter Git. | x03wgn Section 5 "Output harvest and durable publication" + Section 2 "Durable project report/decision publication" retention class + Section 8 Phase 5 item 3. |
| F6 | `aw recover <run-id>` must reconcile ledger/refs/worktrees/locks/journals/candidates/submissions/artifacts WITHOUT a model and fail closed on disagreement; `aw doctor --lanes` surfaces lane attention. | x03wgn Section 7 recovery invariants 8-9 + Section 8 Phase 5 item 4; reuse `run_recovery.py` (:366,390,424) + `doctor.py` (:1434). |
| F7 | Locking is POSIX-only `fcntl` and the process-tree kill is POSIX-only `os.killpg`; both need a cross-platform abstraction + Windows Job Object. | x03wgn Section 9 finding 5 + Section 7 "POSIX-only locking"/"Process child survives parent kill" + Section 8 Phase 5 item 6; R12 (fcntl Unix-only); fcntl (oc_runipd.py:17,671; agy_runipd.py:18,768); killpg (oc_runipd.py:1566-1570; agy_runipd.py:1663-1667). |
| F8 | Crash injection is required at EVERY irreversible boundary (input seal, receipt, launch, observation, checkpoint, harvest, candidate merge, publication, validation, target update, cleanup); recovery reconciles each to one unambiguous state. | x03wgn Section 7 "Crash injection at every journal boundary" + recovery invariant 9 + Section 8 Phase 5 item 5. |
| F9 | Both host drivers must change symmetrically (twin parity). | x03wgn Section 8 Phase 5 (runner-wide); oc_runipd.py + agy_runipd.py parity of `integrate_lane_branch`/`run_lock`/`terminate_process`. |

## Proposed changes (ordered, validatable)

1. E-01/E-02: `platform_lock.py` - cross-platform `exclusive_file_lock` (fcntl / msvcrt) + `held_by_diagnostics` with start-time/boot-id stale detection (replaces raw fcntl semantics of oc_runipd.py:666-683).
2. E-03: route both drivers' `run_lock` through `platform_lock`; drop `import fcntl` from the drivers.
3. E-04/E-05: `_kill_process_tree` (POSIX `os.killpg` preserved + Windows Job Object) behind both drivers' `terminate_process` seam.
4. E-06/E-07/E-08: durable `lane_allocated`/`lane_scope_claimed`/`lane_cleanup_authorized` ledger events; `lane_recovery.reconstruct_leases` (rebuild LeaseTable from events) + `reconcile_worktrees` (`git worktree list` cross-check, classify, delete nothing).
5. E-09..E-13: `candidate_integration.integrate_candidate` (lock -> journal expected tip -> candidate at tip -> `--ff-only` merge -> validate the EXACT candidate tree -> re-read + rebuild on move -> journaled target update, pause on dirty main -> journaled cleanup); rewire both drivers + delete the `return True` integration authority.
6. E-14: `publication_projection.project_publication` (sanitized ledger -> tracked `.aw/records` in the candidate, excluding live machine state), merged+validated with the product tree.
7. E-15/E-16: `aw recover <run-id>` (model-free reconciliation, reuse run_recovery primitives) + `aw doctor --lanes`.

## Deferred / out of scope (with reason)

- Authoring the typed ExecutionContext/PathResolver + checkout-id derivation + AST guard: Phase 3 (7p9n2v). Out-of-repo `checkout_state_root`/XDG relocation + `aw migrate-runtime-state`: Phase 4 (58ha43). This child DEPENDS on both (Item-Dependencies: executed:58ha43) and only routes the integration lock + candidate journal through the existing out-of-repo location.
- OS-sandbox hard mode, read-only git-common-dir, driver-owned git mutation, read-only discovery phase: Phase 6 (1o4eif).
- Routing the LEDGER/REGISTRY/SESSION locks (run_ledger_store.py:267, project_registry.py:277, agy_sessions.py:38) through `platform_lock`: out of this phase's Scope-Paths. Reason: this phase's release-relevant portability targets are the RUN lock and the new INTEGRATION lock (the ones on the crash-recovery/integration path); the ledger/registry/session lock modules are not in scope and are a mechanical follow-up that does not change the Phase-5 acceptance criteria. Named here so the omission is deliberate, not silent.
- Speculative cross-lane dependency chaining (branch B from A's unintegrated tip, x03wgn Section 5 "Dependencies between lanes" speculative row): the default staged-merge order (integrate A, then create B) is what the integrator implements; speculative chaining is an optimization deferred with reason - it couples fate and is not required for the release-gating correctness this phase delivers.
- Content-addressed dedup store for local-retained artifacts (x03wgn Section 5 "a content-addressed store can deduplicate ... later"): the simple per-run copy+verified-manifest harvest is Phase 2's surface; this phase only ensures cleanup is preceded by a durable authorization event (recovery invariant 7), it does not add the CAS.

## Scope check

- Over-scope: none. Every E-item is an x03wgn Section 5/Section 8-Phase-5 deliverable (candidate integrator with lock+expected-tip+rebuild, publication projection, durable lane events + lease reconstruction, `aw recover`/`aw doctor --lanes`, cross-platform lock + Windows Job Object). No Phase-3 resolver authoring, no Phase-4 relocation engine, no Phase-6 sandbox.
- Under-scope: none. All four mandatory adversarial/crash guards are covered: (a) validation runs on the MERGED candidate tree + a target that advances during validation FORCES a rebuild (E-10/E-11, V-10/V-11); (b) crash-injection at EVERY journal boundary reconciles to one unambiguous state via `aw recover` WITHOUT a model (E-12/E-15, V-12/V-15, `tests/test_crash_injection_integration.py`); (c) two runs integrating simultaneously - exactly one candidate proceeds, the second rebuilds (E-09/E-11, V-09/V-11); (d) killing the worker mid-edit preserves+classifies all work (E-05/E-08, V-05/V-08). Both drivers are changed (E-03/E-05/E-13).

## Required tests / validation

- New adversarial/crash tests (named exactly):
  - `tests/test_candidate_integration.py::test_validation_runs_on_merged_candidate_tree_not_diff` - ADVERSARIAL guard (a): the `full_validation` callback receives the candidate WORKTREE PATH whose `git rev-parse HEAD` == the post-merge candidate tip, never a diff string.
  - `tests/test_candidate_integration.py::test_target_advances_during_validation_forces_rebuild` - ADVERSARIAL guard (a): `target_ref` advances between journal write and post-validation re-read -> a second candidate is built at the new tip and re-validated, the stale candidate is NOT used to update main.
  - `tests/test_candidate_integration.py::test_two_concurrent_integrations_one_proceeds_other_rebuilds` - ADVERSARIAL guard (c): two `integrate_candidate` calls contend on the checkout integration lock; exactly one proceeds, the second (after the first moves the tip) rebuilds.
  - `tests/test_candidate_integration.py::test_dirty_main_pauses_never_stashes` - dirty user main -> `status="paused-dirty-main"`, dirty files byte-identical afterward.
  - `tests/test_candidate_integration.py::test_merge_conflict_aborts_preserves_lane_no_main_mutation` - conflict -> candidate aborted, lane branch preserved, main untouched.
  - `tests/test_crash_injection_integration.py::test_recover_reconciles_at_every_journal_boundary` - ADVERSARIAL guard (b): inject a crash after EACH boundary (receipt, launch, observation, checkpoint, harvest, candidate merge, publication, target update, cleanup) and assert `aw recover` reconciles each to ONE unambiguous state WITHOUT a model.
  - `tests/test_lane_recovery.py::test_reconstruct_leases_from_durable_events` + `::test_reconcile_worktrees_classifies_orphaned_metadata_deletes_nothing` - guard (d): ownership rebuilt from events; orphaned metadata classified, nothing deleted.
  - `tests/test_process_tree_kill.py::test_posix_group_kill_reaps_child` (guard (d) mid-edit kill preserves no orphan) + `::test_windows_job_object_branch_selected` (monkeypatched `sys.platform`).
  - `tests/test_platform_lock.py::test_exclusive_lock_blocks_second_holder` + `::test_stale_lock_detected_by_start_time_not_pid`.
  - `tests/test_publication_projection.py::test_projection_excludes_live_machine_state` (projected set intersects `.aw/records/` but is disjoint from receipt/lock/session/journal paths).
- Full-suite regression: `python3 -m pytest -p no:randomly -q` must stay green. Paste ACTUAL output.

## Spec / documentation sync

- N/A for a tracked spec file in this phase. The integration algorithm contract is x03wgn Section 5 (external research, cited by findings), and the behavior is captured by the new tests + the recovery invariants (x03wgn Section 7). No `.gitignore` edit is required: the integration lock + candidate journal live under the Phase-4 out-of-repo `checkout_state_root(<checkout-id>)/integration/`, and the publication projection writes only tracked `.aw/records/...` paths (already tracked). If a `candidate-integration` / `recovery-invariants` operator doc is later warranted, it is deferred to the orchestrator's whole-Set verification (bl9q3d E-01) with reason: the operator-facing surface (`aw recover`/`aw doctor --lanes`) stabilizes only once all children are executed and the Set acceptance criteria are demonstrated.

## Open questions

### OQ-01: Should the default target-update policy on a dirty user main be `pause`, or integrate through a designated integration branch?

- Blocking: no
- Status: open
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Non-blocking. x03wgn Section 5 step 8 permits both ("pause or use a designated integration branch according to explicit policy") and forbids only auto-stash/reset/overwrite. This phase implements `dirty_main_policy="pause"` as the safe default (E-11/V-11 pin PAUSE + byte-identical dirty files); a `designated-branch` policy is an additive `dirty_main_policy` value that does not change the pause acceptance test and can be added without reopening the integrator's contract. The hard invariant tested here is "never auto-stash/overwrite", which holds for either policy value.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_platform_lock.py::test_exclusive_lock_blocks_second_holder` exits 0 showing `1 passed`. The test acquires `platform_lock.exclusive_file_lock(p)`, spawns a second process (or thread with its own fd) attempting the same lock, asserts it raises `LockHeldError`, and asserts the lock is released (a third acquire after the context exits succeeds); on POSIX it asserts the underlying call path is `fcntl.flock(..., LOCK_EX|LOCK_NB)`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_platform_lock.py::test_stale_lock_detected_by_start_time_not_pid` exits 0 showing `1 passed`. The test writes a lock body with the current pid but a MISMATCHED `start_time`+`boot_id`, asserts the reclaim helper classifies it STALE (reclaimable) despite the live pid, and a lock body matching a live process's start_time+boot_id classifies HELD; `held_by_diagnostics(path)` returns a dict with `pid`/`start_time`/`boot_id`(or `session_id`)/`host`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: TWO pasted commands. (1) `grep -n "import fcntl" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` prints NOTHING and exits 1 (both drivers no longer import fcntl). (2) `python3 -m pytest -p no:randomly -q tests/test_platform_lock.py -k run_lock_via_platform_lock` exits 0 showing `passed`; the test asserts `oc_runipd.run_lock(run_dir)` and `agy_runipd.run_lock(run_dir)` each raise `DriverError` (message contains "already controlled by another process") on a second concurrent hold and route through `platform_lock`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_process_tree_kill.py::test_windows_job_object_branch_selected` exits 0 showing `1 passed`. With `sys.platform` monkeypatched to `"win32"` and the Job Object calls mocked, the test asserts `_kill_process_tree` invokes the Job Object termination path (`CreateJobObject`/`AssignProcessToJobObject`/`TerminateJobObject` or the `taskkill /T /F` fallback), and with `sys.platform="linux"` it asserts the `os.killpg` path is selected.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_process_tree_kill.py::test_posix_group_kill_reaps_child` exits 0 showing `1 passed`. ADVERSARIAL guard (d): the test spawns a parent process with `start_new_session=True` that forks a long-lived child into the same session, calls the driver `terminate_process` (both `oc_runipd` and `agy_runipd`), and asserts BOTH the parent and child pids are gone afterward (`os.kill(pid, 0)` raises `ProcessLookupError` for each - no orphan survives).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_recovery.py -k durable_lane_events` exits 0 showing `passed`. The test allocates a worktree, claims a scope, and tears it down, then re-reads the run ledger FROM DISK (fresh process/handle) and asserts exactly one `lane_allocated` (with lane_id+branch+worktree path+base sha), one `lane_scope_claimed` (with the exact owned path set), and one `lane_cleanup_authorized` event are present and durable.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_recovery.py::test_reconstruct_leases_from_durable_events` exits 0 showing `1 passed`. ADVERSARIAL guard (d): the test seeds a ledger with lane A (allocated + claiming `["x.py"]`, NO cleanup) and lane B (allocated + claiming `["y.py"]` + cleanup), then in a FRESH process calls `lane_recovery.reconstruct_leases(run_id)` and asserts `.owner_of("x.py") == "A"` and `.owner_of("y.py") is None` - ownership recovered purely from durable events, no live process.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_recovery.py::test_reconcile_worktrees_classifies_orphaned_metadata_deletes_nothing` exits 0 showing `1 passed`. ADVERSARIAL guard (d): the test creates one real allocated worktree (classified `live`), `rm`s a second lane's worktree directory out from under it (classified `orphaned-metadata`), records a lane allocated-but-never-created (classified `missing`), asserts `reconcile_worktrees(repo, run_id)` returns that exact classification map, and asserts `git worktree list` + the branches are UNCHANGED (nothing deleted).
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_candidate_integration.py::test_two_concurrent_integrations_one_proceeds_other_rebuilds` exits 0 showing `1 passed`. ADVERSARIAL guard (c): the test starts two `integrate_candidate` calls contending on the checkout integration lock (`checkout_state_root(K)/integration/lock`), asserts exactly ONE proceeds while the other raises `LockHeldError`/waits, and that the durable candidate-integration journal records `expected_target_tip`+`target_ref`+`lane_tip`+phase BEFORE any candidate worktree is created (assert the journal file exists and names the tip when the process is interrupted immediately after the journal write).
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_candidate_integration.py::test_validation_runs_on_merged_candidate_tree_not_diff tests/test_candidate_integration.py::test_merge_conflict_aborts_preserves_lane_no_main_mutation` exits 0 showing `2 passed`. ADVERSARIAL guard (a): the first test captures the argument passed to `full_validation` and asserts it is a real candidate WORKTREE PATH whose `git rev-parse HEAD` equals the post-`--ff-only`-merge candidate tip (NOT a diff string, NOT `merged_files`). The second test forces a merge conflict and asserts `integrate_candidate` returns `status="conflict"` with conflict paths + both tips recorded, the lane branch still exists (`git rev-parse <lane-branch>` succeeds), and the user main worktree is byte-identical/untouched.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_candidate_integration.py::test_target_advances_during_validation_forces_rebuild tests/test_candidate_integration.py::test_dirty_main_pauses_never_stashes` exits 0 showing `2 passed`. ADVERSARIAL guard (a)+(c): the first test advances `target_ref` (a new commit) between the journal write and the post-validation re-read and asserts `integrate_candidate` DETECTS the mismatch and REBUILDS (a second candidate created at the new tip + re-validated; the stale candidate's tip is NOT written to `target_ref`). The second test makes the main working tree dirty, asserts `integrate_candidate(..., dirty_main_policy="pause")` returns `status="paused-dirty-main"`, does NOT update `target_ref`, and the dirty files' contents/mtime are unchanged afterward (no stash, no reset, no overwrite).
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_crash_injection_integration.py -k crash_after_target_update_before_cleanup` exits 0 showing `passed`. The test drives a successful `integrate_candidate` but injects a crash AFTER the `git update-ref`/merge succeeds and the `integrated` journal event is written but BEFORE the candidate teardown; it asserts the `integrated` journal event names the target tip + validation evidence, then runs `aw recover <run-id>` and asserts it completes the cleanup idempotently (candidate torn down, no duplicate integration) and that a FAILED integration in a companion case leaves the lane branch present.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: TWO pasted commands. (1) `grep -n "return True" agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` shows NO `make_integration_validation_runner` `_runner` returning an unconditional `True` as integration authority (the stub is removed or replaced). (2) `python3 -m pytest -p no:randomly -q tests/test_candidate_integration.py -k drivers_use_candidate_tree` exits 0 showing `passed`; the test drives BOTH `oc_runipd.integrate_lane_branch` and `agy_runipd.integrate_lane_branch` and asserts each validates the merged CANDIDATE tree and REFUSES to update main when candidate validation fails (a failing candidate validation -> main tip unchanged, lane branch preserved).
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_publication_projection.py::test_projection_excludes_live_machine_state` exits 0 showing `1 passed`. The test seeds a completed run's control ledger, calls `publication_projection.project_publication(run_id, candidate_worktree)`, and asserts the projected file set (a) is non-empty and all under tracked `.aw/records/...`, and (b) is DISJOINT from any receipt/lock/session-log/raw-prompt/recovery-journal path (no live machine state entered Git); a companion assertion drives `integrate_candidate(..., publication_tree=<projection>)` and asserts the validation callback saw BOTH the product change and the projected records present in the same candidate worktree.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_crash_injection_integration.py::test_recover_reconciles_at_every_journal_boundary` exits 0 showing `1 passed`. ADVERSARIAL guard (b): the test injects a crash after EACH journal boundary (receipt, launch, observation, checkpoint, harvest, candidate merge, publication, validation, target update, cleanup) and asserts `python3 -m agent_workflows recover <run-id>` reconciles each to ONE unambiguous state map (ledger+refs+`git worktree list`+locks+candidate journal+submissions+artifacts) WITHOUT a model, FAILS CLOSED (non-zero + explicit disagreement message) on a planted ledger-vs-refs disagreement, and reuses the `run_recovery` primitives for the run-step layer. Paste the reconciliation report for at least the `target update` and `cleanup` boundaries.
  - Observed evidence:
  - Result: pending

- [ ] V-16 validates E-16
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_lane_recovery.py -k doctor_lanes` exits 0 showing `passed`, PLUS a pasted `python3 -m agent_workflows doctor --lanes` run on a repo with one `live` and one `orphaned-metadata` lane showing both classifications + held-lock diagnostics, exiting non-zero (attention needed). The test asserts a `git status --porcelain` snapshot is IDENTICAL before and after `doctor --lanes` (read-only, mutates nothing) and that `doctor --lanes` exits 0 when all lanes are `live`/cleanly reconciled. Plus paste the full-suite `python3 -m pytest -p no:randomly -q` result showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one integration-and-recovery cut - making integration validate the EXACT merged candidate tree under a serialized checkout lock with a journaled, rebuild-on-move, crash-recoverable target update - whose E-items are interdependent facets of that single transaction. The cross-platform lock (TG1) is required before the integration lock (TG4) can be held portably; the process-tree kill (TG2) and durable lane events + lease reconstruction (TG3) are the crash-preservation half that the candidate integrator (TG4) and recovery (TG6) depend on; the publication projection (TG5) is validated inside the SAME candidate tree the integrator builds. They are not independently shippable without leaving a half-built integrator that validates a diff in one path and a tree in another (a worse greenwash than today's single honest gap), so this is one cohesive exception rather than separable standard plans.

This child inherits the Set's shared anti-greenwash execution contract from orchestrator bl9q3d verbatim:

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.

Post-gate lifecycle move: after every V-item shows pasted passing evidence and the full suite is green, run `aw ipd lint --phase pre-transition` on this file, then `aw ipd finalize` it (honoring the contract note about xmqv5l until wtiso-03 lands). Commit ONLY the Scope-Paths files, path-scoped, never push. The four mandatory adversarial/crash guards - (a) validation on the MERGED candidate + target-advance-forces-rebuild (V-10/V-11), (b) crash-injection at every journal boundary reconciled by `aw recover` without a model (V-12/V-15), (c) two simultaneous integrations - one proceeds, one rebuilds (V-09/V-11), (d) mid-edit kill preserves+classifies all work (V-05/V-08) - must each show pasted passing output before this plan may move to executed/.
