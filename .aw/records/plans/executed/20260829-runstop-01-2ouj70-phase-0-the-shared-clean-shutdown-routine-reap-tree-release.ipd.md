# IPD: Phase 0: the shared clean-shutdown routine (reap tree, release lock, coherent ledger, quarantine tree) plus characterization tests

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R1-R6 require that EVERY stop level end in one identical clean shutdown: all descendant agent processes reaped, `driver.lock` released, the run ledger coherent, and partial worktree edits quarantined. Today none of that is guaranteed on a stop: the driver installs no signal handler (the only signal use in `oc_runipd.py` is inside `terminate_process`, :1632-1670), `run_lock` (:738-756) releases `flock` only via a `finally` on the normal path and never unlinks the lock file, and there is no tree-quarantine step at all. Without ONE shared routine first, each of the four levels would grow its own divergent cleanup, which spec R5 forbids.
- Scope: Add ONE shared clean-shutdown routine in a new module and make the existing driver teardown call it, in BOTH drivers. Also add characterization tests that PIN today's broken behavior so the later phases prove a real change rather than a re-assertion. Does NOT add any stop level, flag, poll, signal handler, or CLI verb (Phases 1-5 own those); this child only establishes the always-clean endpoint and its proof harness.
- Scope-Paths: agent_workflows/runner_shutdown.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shutdown.py
- Item-Dependencies: none
- Status: executed
- Set: runstop
- Order: 1
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 2ouj70

## Workflow history
- 2026-08-30 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Landed the ONE shared clean-shutdown routine (runner_shutdown.clean_shutdown) satisfying spec c4gd2h R1-R6/R23, routed both drivers through it at the lock-holding layer, and added 27 tests incl. characterization tests pinning today's orphan/stale-lock behavior. make test-all: zero net-new failures vs base HEAD be49ac4 (19 pre-existing, proven identical). [Scope reconciliation - out-of-scope tests/test_wtiso_adversarial.py: OUT OF SCOPE, consciously updated and recorded as DECISION 02-2ouj70-D1: it text-grepped oc_runipd.py for killpg/getpgid, which moved into the single shared reaper as spec c4gd2h R5 requires; the guard now asserts the primitives in runner_shutdown AND that the driver still delegates, so it is strengthened, not weakened; in-scope-unmodified agent_workflows/agy_runipd.py: modified in commit 2256846, before the receipt refresh; E-04 symmetric rewire per orchestrator CID-3; in-scope-unmodified agent_workflows/oc_runipd.py: modified in commit 2256846, before the receipt refresh; E-04 rewire (locked_run, run_lock handle, reaper delegation); in-scope-unmodified agent_workflows/runner_shutdown.py: modified in commit 2256846, which the refreshed begin receipt froze as its own base; created by this execution (E-01/E-02/E-03); in-scope-unmodified tests/test_runner_shutdown.py: modified in commit 2256846, before the receipt refresh; created by E-05 (27 tests)]
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-108. Fixed a BLOCKER layering error in E-04: the named call site `oc_runipd.py:1785-1799` is inside `run_opencode` (def :1679), which holds no lock (`run_lock` is taken in `main` at :2926/:2958), runs PER TURN (called :2001, :2106), and has no queue authority, so three of the four spec invariants (R2 lock, R3 ledger, R4 tree) were unreachable from it; the full `clean_shutdown` now goes at the lock-holding `main` layer with a reap-only call left at the per-turn handlers, and all FIVE handler sites are enumerated (oc :1786, :1798; agy :1835, :1856, :1868) instead of "one counterpart" each. Rewrote E-03, which would have auto-stashed a user's uncommitted work at stop time: the house policy for un-owned dirty paths is REFUSE-AND-REPORT (`dirty_tree_overlap`, :516-545, :578-587) and `wtiso` Phase 5 requires "never auto-stash/reset/overwrite a dirty user main", so R4 is now observe-and-report with before/after proof that the tree was NOT modified (GUIDING_PRINCIPLES 10). Measured and corrected the plan's central R2 premise: a stale `driver.lock` is COSMETIC, not a liveness bug - verified by holding the lock, SIGKILLing the holder, and re-acquiring successfully (`re-acquire: SUCCEEDS (flock auto-released by OS)`), so E-05 is now forbidden from pinning the false "stale lock blocks the next run" defect and must assert file-presence AND lock-freeness. Corrected the validation command (a bare `pytest -q` deselects `slow` per `pyproject.toml:122`, exactly this child's subprocess tests) to `make test-all`. Corrected two false convention claims (no `pytest-randomly` in this repo; `run_lock` is at :739 and acquired in `main`, not in the turn path). Corrected the `fcntl` deferral: `platform_lock` is already owned by `wtiso` `2c122z`, not by Phase 5 of this Set. Bounded the under-scope R3 claim and recorded the verified spec-transition mechanic (`approved -> implemented` is refused; use `implementing`).
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Establish the ONE unconditional clean-shutdown routine (spec R1-R6) that every later stop level and crash recovery will call, plus characterization tests pinning today's orphan/stale-lock/dirty-tree behavior so subsequent phases demonstrate real improvement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared routine

- [x] E-01 Add `agent_workflows/runner_shutdown.py` with `clean_shutdown(process, lock, run_dir, repo) -> ShutdownReport` performing the four spec invariants BEST-EFFORT in order (reap descendants, release lock, make ledger coherent, quarantine tree), never aborting on the first failure, and returning a `ShutdownReport` naming each invariant and whether it was satisfied (spec R1-R4, R6, R23). Reuse `terminate_process`'s existing process-group escalation rather than writing a second reaper (spec R5); import it or move it into this module and re-export so exactly one implementation exists.
  - Depends on: none
  - Expected outcome: `clean_shutdown` is importable, performs all four steps even when an earlier one raises internally, and returns a report whose per-invariant booleans reflect reality; a unit test with an injected failure in step 1 still shows steps 2-4 attempted.
  - Execution state: performed
- [x] E-02 Make lock release OBSERVABLE per spec R2: in the shutdown routine, release the `flock` AND unlink the lock file (guarding against unlinking a lock another process now holds), so a stale `driver.lock` holding a dead PID can no longer be the residue of a stop. Keep `run_lock`'s existing contextmanager contract intact for the normal path. SCOPE-CORRECTION (measured, see Findings): the leftover file is a COSMETIC/diagnostic residue, NOT a liveness defect - the kernel drops `flock` when the holder dies, so a stale file never actually blocks a later run. Implement the unlink for diagnostic honesty, but do NOT claim it fixes a blocked-run bug, and do NOT let the unlink become a correctness dependency for any later phase.
  - Depends on: E-01
  - Expected outcome: after `clean_shutdown`, a fresh process can acquire `flock(LOCK_EX|LOCK_NB)` on the run dir and no `driver.lock` file remains; the normal (non-stop) run path still releases correctly; and a lock file currently held by ANOTHER LIVE process is never unlinked.
  - Execution state: performed
- [x] E-03 Implement spec R4 as OBSERVE-AND-REPORT, not auto-stash. Capture `git status --porcelain` at stop time, record the observed dirty paths in the `ShutdownReport`, and report them to the operator; do NOT move, stash, reset, or copy aside the user's working tree by default. Rationale (a house invariant, not a preference): the repo's established policy for un-owned dirty paths is REFUSE-AND-REPORT, not relocate - `dirty_tree_overlap` + its caller fail closed with "integration refused: main tree has un-owned dirty paths..." (`oc_runipd.py:516-545`, :578-587), and `wtiso` Phase 5 (`2c122z`) states "never auto-stash/reset/overwrite a dirty user main" four times as a required invariant. An automatic `git stash` at stop time would also silently capture edits the HUMAN made in their own checkout while a run happened to be in flight, which is exactly the destructive, hard-to-reverse action GUIDING_PRINCIPLES 10 (safety and reversibility) forbids. Any actual relocation must therefore be opt-in and operator-triggered, which this child does NOT implement.
  - Depends on: E-01
  - Expected outcome: given a fake child that dirties a tracked file then is stopped, the report ENUMERATES the dirty paths and the operator is told; the working tree is left byte-for-byte as the user/agent left it (proven by comparing `git status --porcelain` and file contents before and after `clean_shutdown`); nothing is stashed, reset, or moved.
  - Execution state: performed

### Task group 2: wiring and characterization

- [x] E-04 Route BOTH drivers' teardown through `clean_shutdown` at the CORRECT layer. The call site named in the original draft (`oc_runipd.py:1785-1799`) is INSIDE `run_opencode` (def at :1679), which is the wrong layer for three of the four invariants and cannot satisfy them: `run_opencode` holds no lock (`run_lock` is acquired two layers up in `main`, :2926/:2958, so R2 is unreachable there), it is called PER TURN from `execute_item` (:2001, :2106) so a per-turn tree quarantine would fire between retries of a still-running item (R4 wrong), and it has no `state`/queue authority to make the ledger coherent (R3). Instead: (a) keep a process-reap-only call at the existing `run_opencode` handlers (which is all `terminate_process` does today, preserving current re-raise/`StallTimeout` semantics exactly); and (b) invoke the FULL four-invariant `clean_shutdown` in `main` around the `with run_lock(run_dir):` blocks (`oc_runipd.py:2926-2927`, `:2958-2962`; `agy_runipd.py:2942`, `:2982`), which is the only scope holding the lock, the run `state`, and the repo path together. Note there are THREE such handler sites in `agy_runipd.py` (:1835, :1856, :1868) and TWO in `oc_runipd.py` (:1786, :1798), not one "counterpart" each; enumerate and handle all five.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the full `clean_shutdown` runs at the lock-holding `main` layer in both drivers (so R2/R3/R4 are actually reachable), the per-turn handlers still reap the child as today with unchanged exception semantics, all five enumerated handler sites are accounted for, existing driver tests still pass, and an AST/import check shows no second cleanup path (orchestrator CID-1).
  - Execution state: performed
- [x] E-05 Add `tests/test_runner_shutdown.py` characterization tests that PIN today's behavior as the baseline the later phases improve on: a fake child that outlives a bare terminate is observed as an orphan, and a hard abort leaves `driver.lock` present holding a DEAD PID **while the lock itself is already free** (assert BOTH halves: the file exists AND a fresh `flock(LOCK_EX|LOCK_NB)` succeeds - see the measured correction in Findings). Do NOT assert that a stale lock blocks a later run; that is false and would pin a nonexistent defect. Assert against the process table and the filesystem, not against code structure. Mark these tests `slow` if they spawn subprocesses, matching the repo convention.
  - Depends on: E-04
  - Expected outcome: characterization tests pass and each carries a comment naming the defect it pins (kjzlgw observation, spec section 0.1) so a later phase changing that behavior must consciously update the test; the stale-lock test asserts file-presence AND lock-freeness, so it cannot be read as a liveness bug.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `terminate_process` (`oc_runipd.py:1632-1670`) ALREADY reaps a process GROUP with escalation SIGINT -> SIGTERM -> SIGKILL via `os.killpg`/`getpgid`, with per-signal grace constants `_SIGINT_GRACE_SECONDS=5.0` / `_SIGTERM_GRACE_SECONDS=2.0` (:1627-1628) and a `_close_process_streams` helper (:1672). REUSE and extend this; do NOT write a second reaper (spec R5).
- `run_lock` (`oc_runipd.py:739-756`) is a `contextlib.contextmanager` taking `fcntl.flock(LOCK_EX|LOCK_NB)`, writing `pid=<pid> started=<utc>`, and releasing with `LOCK_UN` in a `finally`. It NEVER unlinks the lock file, so a leftover file with a dead PID is the observed symptom. `fcntl` is POSIX-only, and note it is imported UNCONDITIONALLY at module top level (`oc_runipd.py:17`, `agy_runipd.py:18`), so the driver cannot even be imported without it (see orchestrator OQ-02, which is BLOCKING for Phase 5 and reinterprets spec A10).
- `run_lock` is acquired in `main`, NOT in the turn-running code: `oc_runipd.py:2926` and `:2958` (`agy_runipd.py:2942`, `:2982`). This is the layering fact that dictates where `clean_shutdown` must be invoked (see E-04); `run_opencode` cannot release a lock it never took.
- The driver spawns the child with `--format json` and iterates its stdout line-by-line (`oc_runipd.py:1765-1786`), with `StallWatchdog` (:1769) as the precedent for acting on stream observation alone.
- The `except BaseException:` block at `oc_runipd.py:1785-1799` calls `terminate_process` then re-raises. It is INSIDE `run_opencode` (def at :1679), i.e. per-TURN and lock-less, so it is the right place for a process reap and the WRONG place for the lock/ledger/tree invariants. There are five such handler sites total (`oc_runipd.py:1786`, `:1798`; `agy_runipd.py:1835`, `:1856`, `:1868`), not one per driver.
- `agy_runipd.py` mirrors this structure (its own `state_root` at :1232 and receipt sync at :592); land symmetrically per orchestrator CID-3. Both drivers also carry BYTE-IDENTICAL `terminate_process` copies (`oc_runipd.py:1632-1670` vs `agy_runipd.py:1720-1757`, differing only in a docstring line), which is why CID-1's single-implementation check must be repo-wide rather than per-file.
- Repo test convention: `tests/test_*.py` using `unittest` classes, run under `pytest` with `xdist`. Correction: there is NO `pytest-randomly` in this repo (verified: no match in `pyproject.toml`, `Makefile`, or CI), so do not rely on random ordering as a given; tests must still be parallel-safe for `-n auto --dist=worksteal`.
- Validation-command trap: the default `addopts` (`pyproject.toml:122`) is `-q -n auto --dist=worksteal -m 'not slow'`, so a bare `python -m pytest -q` SILENTLY SKIPS `slow` subprocess tests. This child's characterization tests spawn real processes and belong in that class, so the full-suite evidence must come from `make test-all`.

## Findings

The four invariants are independently observable, which is what makes them testable without trusting the agent:

| Invariant | Spec | Observable proof |
|---|---|---|
| No orphaned descendants | R1 | process table: no live PID whose ancestor was the driver; nothing reparented to PID 1 |
| Lock released | R2 | lock file absent, AND `flock(LOCK_EX|LOCK_NB)` succeeds from a fresh process |
| Ledger coherent | R3 | every item parses and is terminal, or explicitly interrupted with level+certainty |
| Tree uncontaminated | R4 | `git status --porcelain` dirty paths are ENUMERATED in the report and unchanged by cleanup (not relocated) |

MEASURED CORRECTION to the stale-lock premise (run 2026-08-29, before approving this plan). The spec's scenario (section 0.1) and backlog kjzlgw describe `driver.lock` "left holding a dead PID". That is real but it is COSMETIC, not a liveness bug. Observed directly by holding `run_lock` in a child process, `SIGKILL`ing it, and re-testing:

- `driver.lock exists after hard kill: True`, contents `pid=<dead pid> started=...`
- `re-acquire: SUCCEEDS (flock auto-released by OS)`
- a fresh driver started over the stale file and printed `locked`

So the kernel releases `flock` on process death; the leftover FILE never blocks a subsequent run. A live second process IS correctly refused (verified: rc 1 raised from `oc_runipd.py:744`). Consequences for this child: (a) E-02's unlink is a diagnostic-honesty fix, and must not be sold as unblocking a stuck run; (b) E-05 MUST NOT write a characterization test asserting "a stale lock blocks the next run", because that assertion is false and would pin a defect that does not exist; the honest pinned observation is "the file survives with a dead PID while the lock itself is already free".

R6 (cleanup runs even when the wind-down phase fails or times out) is the reason the routine must be invoked from a `finally`-style path, not only on the success path: today's `except BaseException:` handler at `oc_runipd.py:1785` re-raises after `terminate_process`, so a failure during teardown can still skip later steps. The new routine must therefore perform all four invariants best-effort, collect per-invariant results, and report them (spec R23: never claim cleanup it did not perform) rather than aborting on the first failure.

## Proposed changes (ordered, validatable)

1. New `agent_workflows/runner_shutdown.py` exposing a single `clean_shutdown(...)` entry that performs the four invariants best-effort and returns a structured per-invariant result.
2. Route both drivers' existing teardown through it (one call site each), preserving current exception semantics.
3. New `tests/test_runner_shutdown.py` with characterization tests pinning today's behavior and unit tests for the routine.

## Deferred / out of scope (with reason)

- Any stop LEVEL, the stop-request flag, the checkpoint poll, signal handlers, and the `stop` CLI verb: Phases 1-5 (`gq6m2u`, `1qxuke`, `foi1b3`, `m0z0ti`, `71vjbn`).
- Replacing `fcntl` with a cross-platform lock: out of scope here, and NOT deferred to Phase 5 either. Correction: a cross-platform lock (`platform_lock`) plus a Windows Job Object process-tree kill is already OWNED by `wtiso` Phase 5 (`2c122z`), so neither this child nor `71vjbn` may build a second one (P8). How spec A10 is honestly satisfied is the orchestrator's BLOCKING OQ-02; this child simply must not regress POSIX behavior.
- Unifying the two drivers (backlog `dhuape`): this child lands the same call in both, no de-duplication.
- Changing what the agent is asked to do: explicit spec non-goal.

## Scope check

- Over-scope: E-03 as originally drafted was over-scope and destructive (auto-stashing the user's working tree). Narrowed to observe-and-report per the house REFUSE-AND-REPORT precedent and GUIDING_PRINCIPLES 10; any real relocation is deferred as opt-in, operator-triggered work.
- Under-scope: R3 (ledger coherence) is the weakest-covered invariant here and is now explicitly bounded. This child does NOT own making the ledger record a stop LEVEL or CERTAINTY (Phases 2-4 own those fields); it owns only that `clean_shutdown` leaves `state.json` parseable and every item in a defined state, and that it does not corrupt the ledger mid-write. Note also that the pre-existing crash-reconciliation routine `reconcile_interrupted` (`oc_runipd.py:2402`) is spec R5's "crash recovery" half: this child MUST NOT create a parallel routine beside it, and the orchestrator records this as pre-existing fact 1.

## Required tests / validation

- `python -m pytest tests/test_runner_shutdown.py -q -m ''` passes (pass `-m ''` so `slow`-marked subprocess tests in this file are not silently deselected).
- Characterization tests demonstrate TODAY's behavior explicitly (orphan survives; lock file remains with a dead PID WHILE the lock is already free) so the later phases' improvement is provable rather than asserted, and so no false defect is pinned.
- `make test-all` (`python -m pytest tests/ -m ''`) remains green: the FULL suite, since a bare `python -m pytest -q` deselects `-m 'not slow'` per `pyproject.toml:122` and would skip exactly this child's tests.
- The R4 evidence is a before/after comparison proving the tree was NOT modified by cleanup, not a "tree is clean" assertion.
- All child agent processes in tests are local fakes; no network, no real `opencode` invocation.

## Spec / documentation sync

- No user-facing doc change yet (no CLI surface changes in this child).
- Spec `c4gd2h` moves `approved` -> `implementing` when this child begins (it is the first child). Use `aw spec set implementing c4gd2h`. Do NOT attempt `implemented` from here: verified 2026-08-29 that `aw spec set implemented c4gd2h` fails with `Illegal spec transition approved -> implemented`, and `implemented` additionally requires a resolvable `--evidence` citation (`agent_workflows/specs.py:517-521`). The `implemented` move belongs to the orchestrator's whole-Set verification, not to this child.
- Record in the module docstring which spec requirement ids (R1-R6, R23) the routine satisfies, so the mapping is discoverable from the code.

## Open questions

### OQ-01: Should `clean_shutdown` raise on a failed invariant, or return a per-invariant result the caller reports?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RETURN a structured per-invariant result and let the caller report it. Raising would violate spec R6 (cleanup must complete even when part of the wind-down fails) by aborting the remaining invariants, and would violate R23 (never claim cleanup it did not perform) by making a partial failure indistinguishable from a crash. Resolved from the spec, not deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output for the injected-failure test showing all four invariants attempted when step 1 raises, plus the returned `ShutdownReport` contents printed in the assertion failure message or captured output. Prose that the routine "handles errors" is insufficient.
  - Observed evidence: `python3 -m pytest "tests/test_runner_shutdown.py::BestEffortTests" -m '' -n0 -q -s` (injected `RuntimeError` in step 1 via an `Exploding.poll()`):

    ```text
    .ShutdownReport:
    clean shutdown: children_reaped NOT satisfied
      children_reaped (R1): NOT SATISFIED - error: RuntimeError: injected reap failure
      lock_released (R2): ok - lock file removed; lock free=True
      ledger_coherent (R3): ok - 1 item(s), all in a defined state
      tree_observed (R4): ok - no dirty paths
    ShutdownReport dict: {"all_satisfied": false, "dirty_paths": [], "invariants": {"children_reaped": {"attempted": true, "detail": "", "error": "RuntimeError: injected reap failure", "requirement": "R1", "satisfied": false}, "ledger_coherent": {"attempted": true, "detail": "1 item(s), all in a defined state", "error": null, "requirement": "R3", "satisfied": true}, "lock_released": {"attempted": true, "detail": "lock file removed; lock free=True", "error": null, "requirement": "R2", "satisfied": true}, "tree_observed": {"attempted": true, "detail": "no dirty paths", "error": null, "requirement": "R4", "satisfied": true}}, "reaped_pids": []}
    ..
    ```

    Step 1 raised, and steps 2-4 are each `attempted: true` and `satisfied: true`, so the routine did not abort on the first failure (R6). The report names the unsatisfied invariant rather than claiming success (R23). `test_missing_context_is_reported_as_skipped_not_as_success` additionally proves an invariant with no inputs reports SKIPPED, never satisfied.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted pytest output showing (a) a fresh process acquires `flock(LOCK_EX|LOCK_NB)` on the run dir after `clean_shutdown`, and (b) `driver.lock` does not exist; plus a test proving a lock held by ANOTHER live process is not unlinked.
  - Observed evidence: `python3 -m pytest "tests/test_runner_shutdown.py::LockReleaseTests" -m '' -n0 -q -s` (5 tests):

    ```text
    .foreign lock: unlinked=False exists=True (never removed)
    .driver.lock exists after clean_shutdown: False
    lock_is_free after clean_shutdown: True
    lock_released (R2): ok - lock file removed; lock free=True
    fresh process flock(LOCK_EX|LOCK_NB): acquired
    ...
    ```

    (a) a genuinely separate `python3 -c` process acquired `flock(LOCK_EX|LOCK_NB)` on the run dir after `clean_shutdown` (`acquired`); (b) `driver.lock exists after clean_shutdown: False`. The exists/free values are printed BEFORE the acquire probe on purpose, because that probe legitimately re-creates the file by opening it `a+`; printing afterwards would have misreported the post-shutdown state. `test_a_lock_held_by_another_live_process_is_never_unlinked` proves the foreign-lock guard: with a live holder and the path replaced under our fd, `unlinked=False exists=True`. `test_run_lock_still_releases_on_the_normal_path_in_both_drivers` and `test_run_lock_still_refuses_a_second_live_holder_in_both_drivers` confirm the normal `run_lock` contract is intact in BOTH drivers.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `git status --porcelain` from BEFORE and AFTER `clean_shutdown` proving they are IDENTICAL (the dirty file still dirty, still in place, contents unchanged), plus the pasted `ShutdownReport` section enumerating those dirty paths. Evidence that the tree was stashed, reset, or moved FAILS this item, as does a test asserting only that a function was called.
  - Observed evidence: `python3 -m pytest "tests/test_runner_shutdown.py::TreeObservationTests" -m '' -n0 -q -s`:

    ```text
    .git status --porcelain BEFORE clean_shutdown:
     M tracked.txt
    ?? untracked.txt
    git status --porcelain AFTER clean_shutdown:
     M tracked.txt
    ?? untracked.txt
    identical: True
    file contents identical: True
    git stash list: ''
    ShutdownReport R4 section:
    clean shutdown: lock_released, ledger_coherent NOT satisfied
      children_reaped (R1): ok - no live child agent process among 0 tracked
      lock_released (R2): SKIPPED - no run lock held by this caller
      ledger_coherent (R3): SKIPPED - no run directory supplied
      tree_observed (R4): ok - 2 dirty path(s) left exactly as found (nothing stashed, reset, or moved)
      working tree left untouched; dirty paths preserved in place:
         M tracked.txt
        ?? untracked.txt
    ..
    ```

    BEFORE and AFTER `git status --porcelain` are byte-identical (`identical: True`), the dirty file's contents are unchanged (`file contents identical: True`), and `git stash list` is empty, so nothing was stashed, reset, or moved. The `ShutdownReport` enumerates both dirty paths. `LockedRunWiringTests::test_locked_run_does_not_modify_a_dirty_tree` proves the same through the real driver entry point in BOTH drivers.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: (a) pasted `make test-all` output showing the FULL suite green after the rewire - a bare `python -m pytest -q` is NOT acceptable because `addopts` deselects `slow` (`pyproject.toml:122`); (b) pasted output of the repo-wide AST/import check proving exactly one cleanup implementation exists (orchestrator CID-1), scoped across `agent_workflows/` rather than per-file, since the two drivers hold byte-identical `terminate_process` copies a per-file check would pass; (c) pasted evidence that the full `clean_shutdown` is invoked at the LOCK-HOLDING layer (a call-site listing showing it wrapping `run_lock` in `main`, not inside `run_opencode`), and that all five per-turn handler sites were enumerated.
  - Observed evidence: (a) FULL suite via `make test-all` (`python3 -m pytest tests/ -m ''`):

    ```text
    19 failed, 3266 passed, 3 skipped, 4 xfailed in 97.85s (0:01:37)
    ```

    Those 19 failures are PRE-EXISTING and unrelated to this child. Proven, not asserted: the same suite was run at the frozen base HEAD `be49ac4` in a separate clean worktree (`git worktree add --detach /tmp/opencode/base-git be49ac4`), and the failing-test sets are identical:

    ```text
    $ diff /tmp/opencode/before.txt /tmp/opencode/after2.txt && echo "IDENTICAL to base HEAD: zero net-new failures"
    IDENTICAL to base HEAD: zero net-new failures
    ```

    (19 lines each; the set is `tests/test_run_viewer.py` x15, `test_command_surface_declarations` x1, `test_cli_conformance_matrix` x2, `test_cli.py::SubcommandDescriptionTests` x1.) One net-new failure DID appear at first (`tests/test_wtiso_adversarial.py::NestedPermissionDeadlockTests::test_nested_permission_only_stall_watchdog_now`, which text-greps `oc_runipd.py` for `killpg`/`getpgid`); it was consciously updated to assert the capability where the shared reaper now lives plus that the driver still delegates, recorded as DECISION 02-2ouj70-D1, and declared at finalize with `--scope-reason`.

    (b) repo-wide AST check proving exactly ONE cleanup implementation (orchestrator CID-1), scoped across `agent_workflows/` and counting only MODULE-LEVEL functions whose body references `killpg`/`getpgid`:

    ```text
    CID-1 process-reaper implementations in agent_workflows/ (module-level, AST):
      agent_workflows/runner_shutdown.py:129:terminate_process
    count=1 (must be 1)
    CID-1 PASS: exactly one shared reaper implementation
    agent_workflows.oc_runipd.terminate_process -> runner_shutdown.terminate_process  OK
    agent_workflows.agy_runipd.terminate_process -> runner_shutdown.terminate_process  OK
    ```

    (c) the full `clean_shutdown` is invoked at the LOCK-HOLDING layer, not inside the per-turn function. AST call-site listing plus the `run_lock`/`locked_run` wiring:

    ```text
    === enclosing function of each clean_shutdown call ===
      agent_workflows/oc_runipd.py:2793 inside def locked_run()
      agent_workflows/agy_runipd.py:2803 inside def locked_run()
    === locked_run wraps run_lock (the lock-holding scope) ===
    agent_workflows/oc_runipd.py:2789:    with run_lock(run_dir) as lock:
    agent_workflows/agy_runipd.py:2799:    with run_lock(run_dir) as lock:
    === main() uses locked_run, not bare run_lock ===
    agent_workflows/oc_runipd.py:3165:            with locked_run(run_dir):
    agent_workflows/oc_runipd.py:3208:            with locked_run(run_dir):
    agent_workflows/agy_runipd.py:3141:            with locked_run(run_dir):
    agent_workflows/agy_runipd.py:3187:            with locked_run(run_dir):
    ```

    All FIVE per-turn handler sites are accounted for and left as reap-only, with unchanged re-raise/`StallTimeout` semantics (`oc_runipd.py:1940`, `:1952`; `agy_runipd.py:1945`, `:1976`, `:1988`), plus the two `StallWatchdog` sites (`oc_runipd.py:179`, `agy_runipd.py:342`) which also remain reap-only. `LockedRunWiringTests` proves behaviorally, in BOTH drivers, that `locked_run` reaps a tracked child and removes the lock file on the success path AND on the failure path (`KeyboardInterrupt` raised inside the block), which is spec R6.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted pytest output for the characterization tests, including the process-table observation (the orphan PID and its reparented ancestor) and, for the stale lock, BOTH the file contents showing a dead PID AND the successful fresh `flock` acquisition proving the lock was already free. A test claiming a stale lock blocks a later run FAILS this item as factually wrong. These must be OBSERVATIONS, not assertions about source code.
  - Observed evidence: `python3 -m pytest "tests/test_runner_shutdown.py::CharacterizationTests" -m '' -n0 -q -s`:

    ```text
    orphan observed on the process table: grandchild pid 1149057 is alive after its parent pid 1149056 was killed; its ppid is now 1
    .stale driver.lock contents: 'pid=1149083 started=test' (pid 1149083 is dead)
    fresh flock on the stale file: acquired-by-fresh-process
    ..
    ```

    The orphan is an OBSERVATION of the process table, not a claim about source: after the direct child is killed, the grandchild is still returned alive by `os.kill(pid, 0)` and `/proc/<pid>/stat` shows its ppid is now `1` (reparented to init), which is exactly the `kjzlgw` symptom. For the stale lock BOTH halves are asserted and printed: the file survives holding a DEAD pid (`pid=1149083`, confirmed dead via `os.kill`), AND a fresh separate process acquires `flock(LOCK_EX|LOCK_NB)` on it (`acquired-by-fresh-process`), proving the lock itself was already free. No test asserts that a stale lock blocks a later run, because that is false; this was re-verified independently before implementing (hold `run_lock`, `SIGKILL` the holder, re-acquire: `re-acquire: SUCCEEDS (flock auto-released by OS)`). Each characterization test carries a comment naming the defect it pins and a message telling a later phase to update it consciously.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking FOR THIS CHILD (spec OQ-01/OQ-03 are RESOLVED in c4gd2h). The orchestrator's OQ-02 (spec A10 / Windows) is BLOCKING for `71vjbn` only and does not gate this child, which must merely avoid regressing POSIX behavior and must not add a lock abstraction.
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan. Specifically: do NOT edit `reconcile_interrupted`/`requeue_interrupted` here (orchestrator pre-existing fact 1 assigns the R19 refusal to `m0z0ti`), and do NOT introduce `platform_lock` (owned by `wtiso` `2c122z`).
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
