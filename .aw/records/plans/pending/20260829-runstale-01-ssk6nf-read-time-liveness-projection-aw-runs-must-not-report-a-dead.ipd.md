# IPD: Read-time liveness projection: aw runs must not report a dead run's item as running

- Date: 2026-08-29
- Kind: child
- From-Backlog: l670yn
- Concern: `aw runs <run-id>` reports a dead run's item as `running` forever. Observed 2026-08-29 on `run-20260829T152806Z-3134751` after the maintainer interrupted `aw oc run`: the board showed `1 running` for `wtiso-04 7p9n2v` while `driver.lock` held pid 3134751, which `ps` proved DEAD and whose `flock` was freely acquirable. The reconciler already exists and is correct (`reconcile_interrupted`, oc_runipd.py:2402, resolves the plan, promotes a genuinely-executed item, else marks `interrupted`) but it is called from EXACTLY ONE place, inside `run_queue` (oc_runipd.py:2474), i.e. only on a RESUME. Every read path therefore trusts the persisted value: `run_viewer.load_run_summary` does `item.get("status", "queued")` (run_viewer.py:225) with no liveness check. This is INDEPENDENT of the graceful-quit work: a SIGKILL, OOM kill, crash, or laptop suspend never lets any handler run, so `running` stays persisted no matter how good the stop protocol becomes, and only a read-time check can report honestly.
- Scope: Make the READ path honest: add a read-only liveness projection so a `running` item belonging to a run that no live driver holds is REPORTED as interrupted-looking, and surface that distinctly enough that an operator is not misled. Read commands MUST NOT mutate state (`reconcile_interrupted` calls `save_state`, so it cannot be reused verbatim on a read path); a separate opt-in repair verb performs the durable fix, including for the already-stale run dir on disk. Does NOT install signal handlers, release/unlink the lock, or implement any stop level: Bug B is owned by spec c4gd2h and plans `2ouj70` (E-02/E-04) and `71vjbn` (E-01/E-02), and MUST NOT be re-specified here (GUIDING_PRINCIPLES P8).
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/run_cli.py, tests/test_run_viewer_liveness.py
- Item-Dependencies: none
- Status: approved
- Set: runstale
- Order: 1
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5-1m-us
- Id: ssk6nf
- Approval: 2026-08-29, human ("approved"): Maintainer directed fixing Bug A this turn (standing graduate/implement/execute authorization).

## Workflow history
- 2026-08-29 approved (aw set, --by-human): Maintainer directed fixing Bug A this turn (standing graduate/implement/execute authorization).
- 2026-08-29 to-review (aw set): Authored review-ready from backlog l670yn (Bug A only; Bug B owned by c4gd2h/2ouj70/71vjbn).

- 2026-08-29 draft (opencode its_direct/pt3-claude-opus-5-1m-us): created.

## Goal

Stop `aw runs` from asserting that a dead run is still working: derive a `running` item's displayed state from whether a live driver actually holds the run (an acquirable `flock` proves none does), read-only, with an explicit repair verb for the durable fix. Independent of the graceful-quit Set, because a SIGKILL or crash can never write a terminal status.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the liveness predicate

- [x] E-01 Add a pure, read-only liveness helper (in `run_viewer.py`) answering "does a live driver hold this run?" by attempting `fcntl.flock(LOCK_EX|LOCK_NB)` on `<run_dir>/driver.lock` and immediately releasing it. Acquirable (or a missing lock file) means NO live holder. Prefer flock over the recorded `pid=` because the OS releases flock on death and a PID can be REUSED, so a PID check alone can report a live holder that is a different process. The helper MUST NOT write, MUST NOT unlink the lock, and MUST degrade to "unknown" (never crash, never claim dead) on a platform without `fcntl` or on any OSError.
  - Depends on: none
  - Expected outcome: returns not-held for the verified stale run `run-20260829T152806Z-3134751`, held for a run whose driver is alive, and unknown (not dead) when `fcntl` is unavailable; the lock file is unchanged and still present afterward.
  - Execution state: performed

### Task group 2: honest reporting

- [x] E-02 In `load_run_summary` (`run_viewer.py:178`), stop copying the persisted status verbatim for a `running` item (`:225`). When the run has no live holder per E-01, PROJECT that item's reported status to the interrupted-looking state and count it under that projection, so `counts` and the per-step lines agree. The projection is DISPLAY-ONLY: `state.json` is not modified by any read command. Preserve the persisted value alongside it so a caller can still see what was recorded.
  - Depends on: E-01
  - Expected outcome: `aw runs run-20260829T152806Z-3134751` reports 0 running and 1 interrupted-looking step; `state.json` is byte-identical before and after the command; a run with a live driver still reports `running`.
  - Execution state: performed
- [x] E-03 Make the projection VISIBLE rather than silently rewriting history: mark a projected step so an operator can tell "the driver is gone" from "the driver recorded this", e.g. a distinct status word or a suffix on the step line, and state the meaning in `aw runs --help`. Do not report a projected item as `executed` or `verified` under any circumstance.
  - Depends on: E-02
  - Expected outcome: the rendered line for a projected step is distinguishable from a genuinely-recorded `interrupted` step; help text explains that a projection means no live driver holds the run; a test asserts no projection path can yield `executed`/`verified`.
  - Execution state: performed

### Task group 3: durable repair

- [x] E-04 Add an opt-in repair path that performs the DURABLE fix by delegating to the existing `reconcile_interrupted` (oc_runipd.py:2402) rather than writing a second reconciler (P8), refusing when a live driver still holds the run. This is what fixes an already-stale run dir on disk, since a display projection does not correct `run-20260829T152806Z-3134751`.
  - Depends on: E-01
  - Expected outcome: the repair verb turns the stale run's persisted `running` into the reconciled state and is REFUSED (nonzero, nothing written) while a live driver holds the run; a second invocation is a no-op.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `reconcile_interrupted` (`oc_runipd.py:2402-2446`) is the CORRECT and only reconciler: it resolves the plan path, promotes an item whose plan actually reached `executed`, else sets `interrupted` and stamps `interrupted_at`/`ended_at`. It ends with `save_state`, so it MUTATES and therefore cannot be called from a read command. E-04 delegates to it; E-01/E-02 must not duplicate its logic.
- Its sole caller is `run_queue` (`oc_runipd.py:2467`, call at `:2474`), which is the resume path. That single call site is the whole defect.
- `run_viewer.load_run_summary` (`run_viewer.py:178`) builds `StepSummary`/`RunSummary` dataclasses (`:21-49`) and takes the status verbatim at `:225`, incrementing `counts` from it. `format_step_line` (`:469`) renders `step.status`, already special-casing `substantially-complete` -> `complete`, so a display-only projection has an established precedent.
- MEASURED CORRECTION carried from the `2ouj70` review (2026-08-29): a stale `driver.lock` holding a dead PID is COSMETIC, not a liveness bug, because the OS auto-releases `flock` on death (verified there by SIGKILLing a lock holder and re-acquiring successfully). This is exactly why E-01 uses flock-acquirability as the signal and treats the recorded PID as untrustworthy.
- `fcntl` is POSIX-only (`run_lock`, `oc_runipd.py:739`), so the helper must degrade to unknown rather than assuming dead on a platform without it.
- Bug B (the write side) is owned elsewhere: spec `c4gd2h` R1-R3/R12-R13 and plans `2ouj70` (E-02 lock release/unlink, E-04 teardown routing) and `71vjbn` (E-01/E-02 SIGINT/SIGTERM handlers). Verified those cover it and that NO runstop plan touches `run_viewer`/`aw runs`, so this child is disjoint from a Set currently under live review.

## Findings

Reproduction and ground truth captured 2026-08-29 on `run-20260829T152806Z-3134751`:

```
run-20260829T152806Z-3134751  [wtiso]  (8 steps: 3 blocked, 1 dependency-blocked, 3 queued, 1 running)
-    running  plan  20260828-wtiso-04-7p9n2v  [attempts: 1]

driver.lock                          -> pid=3134751 started=2026-08-29T15:28:10+00:00
ps -p 3134751                        -> PID 3134751 is DEAD
flock(LOCK_EX|LOCK_NB) on the lock   -> ACQUIRED (no live driver holds this run)
viewer-reported counts               -> {'dependency-blocked': 1, 'blocked': 3, 'running': 1, 'queued': 3}
```

The same probe run against a genuinely live review (`run-20260829T152815Z-3134929`) returned `flock BUSY -> live driver holds it`, so the predicate separates the two cases correctly and is not merely detecting "old run".

| Signal | Reliable? | Why |
|---|---|---|
| `flock` acquirable | YES | OS releases it on death; immune to PID reuse |
| recorded `pid=` alive | NO | PIDs are reused, so a live unrelated process reads as the driver |
| lock file present | NO | verified cosmetic; never unlinked even on a clean exit |
| `updated_at` age | NO | a long legitimate turn is indistinguishable from a dead one |

Why this cannot be folded into the graceful-quit Set: every level there depends on the driver still running long enough to act. `SIGKILL`, an OOM kill, a hard crash, and a suspend/resume all bypass that entirely, leaving `running` persisted with no handler having run. A read-time projection is the only mechanism that reports honestly in those cases, which is why it is a separate, permanently-needed fix rather than a duplicate.

## Proposed changes (ordered, validatable)

1. `run_viewer.py`: a pure flock-based liveness helper (no writes, degrades to unknown).
2. `run_viewer.py`: `load_run_summary` projects a `running` item to interrupted-looking when no live holder, display-only, counts consistent.
3. `run_viewer.py`/`run_cli.py`: the projection is visibly distinguishable and documented in `--help`.
4. `run_cli.py`: an opt-in repair verb delegating to `reconcile_interrupted` for the durable fix, refused while a driver is live.
5. `tests/test_run_viewer_liveness.py`: covers the predicate, the projection, read-only-ness, and the repair path.

## Deferred / out of scope (with reason)

- Signal handlers, lock release/unlink, and any stop level (Bug B): owned by spec `c4gd2h` and plans `2ouj70`/`71vjbn`, which are under live review right now. Re-specifying them here would duplicate an approved design and create the drift P8 forbids.
- Auto-repairing on read: deliberately rejected. A read command must not mutate (GUIDING_PRINCIPLES P10); the durable fix is the opt-in verb in E-04.
- Replacing `fcntl` with a cross-platform lock: `platform_lock` is owned by `wtiso` `2c122z` per the `2ouj70` review. This child degrades to unknown instead.
- Reconciling other runs' stale state in bulk: the repair verb is per-run; a sweep can follow if a real need appears.

## Scope check

- Over-scope: none. No signal handling, no lock mutation, no stop levels.
- Under-scope: none. The predicate (E-01), honest counts/lines (E-02), visible attribution (E-03), and the durable repair (E-04) each have a 1:1 validation item.

## Required tests / validation

- `make test-all` (a bare `pytest -q` deselects `slow` per `pyproject.toml:122`, which would skip subprocess-based tests).
- The liveness predicate is tested against a REAL lock held by a live subprocess and against a released one, not a mock, since the whole point is OS behavior.
- A read-only assertion compares `state.json` bytes before and after every read command.
- The already-stale `run-20260829T152806Z-3134751` is used as a real-world case for the projection, and the repair verb is exercised on a COPY so the live tree is not mutated by a test.
- No test may assert a projected item is `executed` or `verified`.

## Spec / documentation sync

- `aw runs --help` gains a sentence explaining that a projected status means no live driver holds the run (E-03) and naming the repair verb (E-04).
- No spec record needed: this is a read-path correctness fix, not a new protocol. Bug B's protocol lives in `c4gd2h`.
- Record in `run_viewer.py` that the projection is display-only and that `reconcile_interrupted` remains the single durable reconciler, so a future reader does not add a second one.

## Open questions

### OQ-01: Should the projected state reuse the word `interrupted` or a distinct word?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: use a DISTINCT rendering (E-03), not a bare `interrupted`. A persisted `interrupted` is a fact the reconciler recorded after inspecting the plan; a projection is an inference from "no live driver" that has NOT inspected anything. Collapsing them would let the display assert a reconciliation that never happened, which is the same greenwashing this repo forbids elsewhere. `format_step_line` already remaps a status word for display (`substantially-complete` -> `complete`, `run_viewer.py:477-479`), so a distinct word is consistent with existing behavior.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output showing the predicate returns not-held for a lock whose holder was killed, held for a lock held by a LIVE subprocess (real flock, not a mock), and unknown when `fcntl` is unavailable (monkeypatched); plus proof the lock file still exists and is byte-unchanged after probing.
  - Observed evidence: `python3 -m unittest tests.test_run_viewer_liveness -v` (HolderStateTests, 6/6 ok). Liveness is tested against a REAL flock held by a live subprocess, not a mock:
    ```
    test_no_lock_file_means_no_holder ... ok
    test_released_lock_means_no_holder ... ok
    test_live_holder_is_detected ... ok
    test_lock_released_when_holder_dies ... ok
    Failing to prove a driver is alive is NOT proof it is dead. ... ok
    test_probe_does_not_modify_the_lock ... ok
    ```
    Live probe on the two real runs, which separates the cases correctly:
    ```
    run-20260829T152806Z-3134751  holder: none   (maintainer's interrupted run)
    run-20260829T152815Z-3134929  holder: live   (the runstop review, genuinely working)
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted `aw runs run-20260829T152806Z-3134751` output showing 0 running and the step reported as projected, plus a before/after checksum of that run's `state.json` proving the read command wrote nothing; plus a test showing a run with a live holder still reports `running`. Counts and per-step lines must agree.
  - Observed evidence: the reported defect is fixed. `aw runs run-20260829T152806Z-3134751`:
    ```
    run-20260829T152806Z-3134751  [wtiso]  2026-08-29 15:28:10  (8 steps: 1 abandoned?, 3 blocked, 1 dependency-blocked, 3 queued)
    -    abandoned?          plan      20260828-wtiso-04-7p9n2v  [attempts: 1]  [no live driver; recorded running]
    ```
    0 running, as required. Read-only proven by checksum over 3 read passes:
    ```
    3 read passes done
    state.json UNCHANGED
    driver.lock UNCHANGED (still present)
    ```
    A live run still reports `running` (`test_live_run_still_reports_running`), and counts agree with the per-step lines (`test_counts_and_steps_agree`), both ok.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted rendered lines for a PROJECTED step and a genuinely-persisted `interrupted` step side by side, showing they are distinguishable; pasted `aw runs --help` containing the explanation; and pasted test output asserting no projection path yields `executed` or `verified`.
  - Observed evidence: the projected line carries an explicit badge naming the persisted value, so an inference is never mistaken for a recorded fact:
    ```
    -    abandoned?  plan  20260828-wtiso-04-7p9n2v  [attempts: 1]  [no live driver; recorded running]
    ```
    A genuinely-persisted `interrupted` is NOT labelled (`A real reconciled interrupted must not be confused with an inference. ... ok`). `aw runs --help` explains the projection and names the repair verb:
    ```
    A step shown as `abandoned?` with `[no live driver; recorded running]` is a DISPLAY PROJECTION:
    state.json still records `running`, but no live driver holds that run (proven by an acquirable
    driver.lock flock), so the recorded status cannot be current. This happens whenever a run dies
    without a chance to write (SIGKILL, OOM, crash, suspend). Reconcile it durably with
    `aw runs repair <run-id>`.
    ```
    `test_projection_never_yields_executed_or_verified ... ok` pins the honesty rule.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted output of the repair verb on a COPY of the stale run dir showing the persisted status changed from `running` to the reconciled value (with the state diff), a second invocation reporting a no-op, and a refusal (nonzero, nothing written) when a live driver holds the run.
  - Observed evidence: exercised on a COPY of the stale run dir so the live tree was not mutated by a test:
    ```
    BEFORE: [('7p9n2v', 'running')]
    1st: (0, 'run-20260829T152806Z-3134751: reconciled 1 step(s): 7p9n2v running -> interrupted')
    2nd: (0, 'run-20260829T152806Z-3134751: nothing to repair (no running steps)')
    AFTER: [('7p9n2v', 'interrupted')]
    ```
    Refusal against the genuinely-live runstop review run, with a true exit code of 1 and nothing written:
    ```
    $ aw runs repair run-20260829T152815Z-3134929
    refusing to repair run-20260829T152815Z-3134929: a live driver still holds this run (stop it first, then repair)
    true exit on live-run refusal: 1
    ```
    Unit coverage: `test_repair_reconciles_and_is_idempotent`, `test_repair_refuses_while_a_driver_is_live` (asserts state bytes unchanged), `test_repair_rejects_a_non_run_directory`, all ok.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: none blocking (spec OQ-01/OQ-03 are RESOLVED in c4gd2h).
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
