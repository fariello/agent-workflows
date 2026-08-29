# IPD: Phase 0: the shared clean-shutdown routine (reap tree, release lock, coherent ledger, quarantine tree) plus characterization tests

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R1-R6 require that EVERY stop level end in one identical clean shutdown: all descendant agent processes reaped, `driver.lock` released, the run ledger coherent, and partial worktree edits quarantined. Today none of that is guaranteed on a stop: the driver installs no signal handler (the only signal use in `oc_runipd.py` is inside `terminate_process`, :1632-1670), `run_lock` (:738-756) releases `flock` only via a `finally` on the normal path and never unlinks the lock file, and there is no tree-quarantine step at all. Without ONE shared routine first, each of the four levels would grow its own divergent cleanup, which spec R5 forbids.
- Scope: Add ONE shared clean-shutdown routine in a new module and make the existing driver teardown call it, in BOTH drivers. Also add characterization tests that PIN today's broken behavior so the later phases prove a real change rather than a re-assertion. Does NOT add any stop level, flag, poll, signal handler, or CLI verb (Phases 1-5 own those); this child only establishes the always-clean endpoint and its proof harness.
- Scope-Paths: agent_workflows/runner_shutdown.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_runner_shutdown.py
- Item-Dependencies: none
- Status: to-review
- Set: runstop
- Order: 1
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 2ouj70

## Workflow history
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Establish the ONE unconditional clean-shutdown routine (spec R1-R6) that every later stop level and crash recovery will call, plus characterization tests pinning today's orphan/stale-lock/dirty-tree behavior so subsequent phases demonstrate real improvement.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: the shared routine

- [ ] E-01 Add `agent_workflows/runner_shutdown.py` with `clean_shutdown(process, lock, run_dir, repo) -> ShutdownReport` performing the four spec invariants BEST-EFFORT in order (reap descendants, release lock, make ledger coherent, quarantine tree), never aborting on the first failure, and returning a `ShutdownReport` naming each invariant and whether it was satisfied (spec R1-R4, R6, R23). Reuse `terminate_process`'s existing process-group escalation rather than writing a second reaper (spec R5); import it or move it into this module and re-export so exactly one implementation exists.
  - Depends on: none
  - Expected outcome: `clean_shutdown` is importable, performs all four steps even when an earlier one raises internally, and returns a report whose per-invariant booleans reflect reality; a unit test with an injected failure in step 1 still shows steps 2-4 attempted.
  - Execution state: pending
- [ ] E-02 Make lock release OBSERVABLE per spec R2: in the shutdown routine, release the `flock` AND unlink the lock file (guarding against unlinking a lock another process now holds), so a stale `driver.lock` holding a dead PID can no longer be the residue of a stop. Keep `run_lock`'s existing contextmanager contract intact for the normal path.
  - Depends on: E-01
  - Expected outcome: after `clean_shutdown`, a fresh process can acquire `flock(LOCK_EX|LOCK_NB)` on the run dir and no `driver.lock` file remains; the normal (non-stop) run path still releases correctly.
  - Execution state: pending
- [ ] E-03 Add tree quarantine per spec R4: capture `git status --porcelain` before/after and, when the stop leaves modifications the run did not intend to publish, quarantine them (stash-like or copied aside with a recorded location) rather than leaving them in place, recording WHERE they went in the report. Never discard a change.
  - Depends on: E-01
  - Expected outcome: given a fake child that dirties a tracked file then is stopped, the tree ends clean per `git status --porcelain` and the report names the quarantine location holding the change; no change is lost.
  - Execution state: pending

### Task group 2: wiring and characterization

- [ ] E-04 Route BOTH drivers' existing teardown through `clean_shutdown`: replace the bare `terminate_process(process)` call in the `except BaseException:` handler (`oc_runipd.py:1785-1799`) and its `agy_runipd.py` counterpart with the shared routine, preserving the current re-raise/`StallTimeout` semantics so no existing behavior regresses.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: both drivers call `clean_shutdown` on teardown; existing driver tests still pass; an AST/import check shows no remaining second cleanup path (orchestrator CID-1).
  - Execution state: pending
- [ ] E-05 Add `tests/test_runner_shutdown.py` characterization tests that PIN today's broken behavior as the baseline the later phases improve on: a fake child that outlives a bare terminate is observed as an orphan, and a bare abort leaves `driver.lock` present holding a dead PID. Assert against the process table and the filesystem, not against code structure.
  - Depends on: E-04
  - Expected outcome: characterization tests pass and each carries a comment naming the defect it pins (kjzlgw observation, spec section 0.1) so a later phase changing that behavior must consciously update the test.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `terminate_process` (`oc_runipd.py:1632-1670`) ALREADY reaps a process GROUP with escalation SIGINT -> SIGTERM -> SIGKILL via `os.killpg`/`getpgid`, with per-signal grace constants `_SIGINT_GRACE_SECONDS=5.0` / `_SIGTERM_GRACE_SECONDS=2.0` (:1627-1628) and a `_close_process_streams` helper (:1672). REUSE and extend this; do NOT write a second reaper (spec R5).
- `run_lock` (`oc_runipd.py:738-756`) is a `contextlib.contextmanager` taking `fcntl.flock(LOCK_EX|LOCK_NB)`, writing `pid=<pid> started=<utc>`, and releasing with `LOCK_UN` in a `finally`. Two facts matter: it NEVER unlinks the lock file (so a leftover file with a dead PID is the observed symptom), and `fcntl` is POSIX-only (Windows needs a different primitive; spec A10 covers the portable subset).
- The driver spawns the child with `--format json` and iterates its stdout line-by-line (`oc_runipd.py:1765-1786`), with `StallWatchdog` (:1769) as the precedent for acting on stream observation alone.
- The existing teardown path is the `except BaseException:` block at `oc_runipd.py:1785-1799`, which calls `terminate_process` then re-raises: that is the natural single call site to route through the new routine.
- `agy_runipd.py` mirrors this structure (its own `state_root` at :1232-1233 and receipt sync at :592); land symmetrically per orchestrator CID-3.
- Repo test convention: `tests/test_*.py` using `unittest` classes, run under `pytest` with `xdist` + `randomly` (so tests must be order-independent and parallel-safe).

## Findings

The four invariants are independently observable, which is what makes them testable without trusting the agent:

| Invariant | Spec | Observable proof |
|---|---|---|
| No orphaned descendants | R1 | process table: no live PID whose ancestor was the driver; nothing reparented to PID 1 |
| Lock released | R2 | lock file absent, or `flock(LOCK_EX|LOCK_NB)` succeeds from a fresh process |
| Ledger coherent | R3 | every item parses and is terminal, or explicitly interrupted with level+certainty |
| Tree uncontaminated | R4 | `git status --porcelain` shows no unexplained modifications |

R6 (cleanup runs even when the wind-down phase fails or times out) is the reason the routine must be invoked from a `finally`-style path, not only on the success path: today's `except BaseException:` handler at `oc_runipd.py:1785` re-raises after `terminate_process`, so a failure during teardown can still skip later steps. The new routine must therefore perform all four invariants best-effort, collect per-invariant results, and report them (spec R23: never claim cleanup it did not perform) rather than aborting on the first failure.

## Proposed changes (ordered, validatable)

1. New `agent_workflows/runner_shutdown.py` exposing a single `clean_shutdown(...)` entry that performs the four invariants best-effort and returns a structured per-invariant result.
2. Route both drivers' existing teardown through it (one call site each), preserving current exception semantics.
3. New `tests/test_runner_shutdown.py` with characterization tests pinning today's behavior and unit tests for the routine.

## Deferred / out of scope (with reason)

- Any stop LEVEL, the stop-request flag, the checkpoint poll, signal handlers, and the `stop` CLI verb: Phases 1-5 (`gq6m2u`, `1qxuke`, `foi1b3`, `m0z0ti`, `71vjbn`).
- Replacing `fcntl` with a cross-platform lock: the routine must not REGRESS portability, but implementing a Windows lock primitive is deferred to Phase 5 where spec A10 (portable subset) is validated.
- Unifying the two drivers (backlog `dhuape`): this child lands the same call in both, no de-duplication.
- Changing what the agent is asked to do: explicit spec non-goal.

## Scope check

- Over-scope: none. No level or trigger is implemented here.
- Under-scope: none. The four invariants (R1-R4), the run-even-on-failure rule (R6), the single-implementation rule (R5), and the honest-reporting rule (R23) each have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_shutdown.py -q` passes.
- Characterization tests demonstrate TODAY's defect explicitly (orphan survives, lock file remains with a dead PID) so the later phases' improvement is provable rather than asserted.
- `python -m pytest -q` remains green (no regression in the existing driver tests).
- All child agent processes in tests are local fakes; no network, no real `opencode` invocation.

## Spec / documentation sync

- No user-facing doc change yet (no CLI surface changes in this child).
- Spec `c4gd2h` moves `approved` -> `implementing` when this child begins (it is the first child).
- Record in the module docstring which spec requirement ids (R1-R6, R23) the routine satisfies, so the mapping is discoverable from the code.

## Open questions

### OQ-01: Should `clean_shutdown` raise on a failed invariant, or return a per-invariant result the caller reports?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RETURN a structured per-invariant result and let the caller report it. Raising would violate spec R6 (cleanup must complete even when part of the wind-down fails) by aborting the remaining invariants, and would violate R23 (never claim cleanup it did not perform) by making a partial failure indistinguishable from a crash. Resolved from the spec, not deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output for the injected-failure test showing all four invariants attempted when step 1 raises, plus the returned `ShutdownReport` contents printed in the assertion failure message or captured output. Prose that the routine "handles errors" is insufficient.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output showing (a) a fresh process acquires `flock(LOCK_EX|LOCK_NB)` on the run dir after `clean_shutdown`, and (b) `driver.lock` does not exist; plus a test proving a lock held by ANOTHER live process is not unlinked.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `git status --porcelain` output (empty) after a stop whose fake child dirtied a tracked file, plus the quarantine path from the report and a pasted diff/listing proving the change is recoverable there. A test asserting only that a function was called fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `python -m pytest -q` output showing the full suite green after the rewire, plus pasted output of the AST/import check proving exactly one cleanup implementation exists (orchestrator CID-1), scoped to `agent_workflows/` so the guard test's own literal does not defeat it.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted pytest output for the characterization tests, including the process-table observation (the orphan PID and its reparented ancestor) and the stale-lock file contents showing a dead PID. These must be OBSERVATIONS, not assertions about source code.
  - Observed evidence:
  - Result: pending

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
