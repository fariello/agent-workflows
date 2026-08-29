# Spec: Runner lifecycle: graceful-quit protocol and stop-state reconciliation

- Date: 2026-08-29
- Status: approved
- Id: c4gd2h
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- From-Backlog: kjzlgw
- Blocks-Release: next
- Scope: Four stop levels for aw oc/agy run over one unconditional clean-shutdown invariant, their trigger UX, ledger interaction, and reuse of the active-work reconciliation routine.

## Workflow history

- 2026-08-29 approved (aw specs, --by-human): Approved by maintainer instruction 2026-08-29: 'graduate/implement/execute <backlog>' must write specs as approved without a separate stop-and-approve round trip; all blocking OQs resolved from repository evidence.
## 0. Concepts (kept distinct)

- **STOP LEVEL**: how much in-flight work is permitted to COMPLETE before shutdown begins. This is the ONLY axis on which the four levels differ.
- **CLEAN SHUTDOWN**: the unconditional post-condition every level ends with (children reaped, lock released, ledger coherent, tree uncontaminated). "Clean" is NOT a level and is never optional.
- **RECONCILIATION**: determining what actually happened to an interrupted item by OBSERVING git and process state, rather than trusting an agent's claim. Shared with crash recovery.
- **OUTCOME CERTAINTY**: whether the interrupted item's disposition is KNOWN (stopped at a defined checkpoint) or INDETERMINATE (`unknown_outcome`, needs reconciliation before resume). This is what separates level 3 from level 4, not cleanliness.
- **DELIBERATE stop vs CRASH**: a stop is requested and cooperative; a crash is unrequested. Both converge on the same reconciliation routine.

## 0.1 Users / actors and scenarios

- **Maintainer at the controlling terminal**: presses Ctrl-C once to wind down after the current agent turn; presses again when in a hurry. Must never have to reason about whether cleanup happened.
- **Maintainer in a SECOND terminal** (the run is occupying the first, or the run is detached): needs an out-of-band, scriptable way to request any level for a named run.
- **The driver process** (`aw oc run` / `aw agy run`): polls for a stop request at cooperative checkpoints and owns the shutdown transaction.
- **The in-flight agent turn** (a child `opencode`/Antigravity process): may be allowed to finish, asked to stop at its next safe point, or interrupted.
- **A LATER run resuming the queue**: must be able to tell, from the ledger alone, whether the previously interrupted item is safe to resume or requires reconciliation first.

Scenario that motivates this spec (observed 2026-08-27): SIGTERM to `aw oc run` printed `Terminated` and exited, but the child `opencode` was reparented to init and kept writing the tree, `driver.lock` was left holding a dead PID, and the working tree was left mid-edit. There was no way to say "wind down cleanly."

## 0.2 Constraints and dependencies

- Reuses the reconciliation routine and `unknown_outcome` ledger model from research `ud28vy` (`.aw/records/research/20260827-activework-00-ud28vy-active-work-lifecycle-and-toolset-redirect.findings.md`). This spec MUST NOT define a second, parallel reconciliation mechanism (GUIDING_PRINCIPLES P8, single source of truth).
- Depends on the driver committing through `aw commit`/`aw finish` (backlog `ctt412`, already `done`).
- Per-run worktree isolation (Set `wtiso`, 8 plans currently `reviewed` in `pending/`) makes level 3/4 cleanup materially simpler but is NOT a hard prerequisite; this spec MUST degrade correctly on a shared checkout. Where `wtiso` changes where machine state lives, this spec follows `wtiso` rather than restating it.
- Stdlib-only, cross-platform. Signal semantics differ on Windows (no `SIGTERM` delivery in the POSIX sense); the spec MUST state the portable subset and what degrades.
- No new runtime dependency, and no bypass of existing lifecycle gates.

## 1. Goals

1. Every stop, at every level, leaves the system COHERENT: all child agent processes reaped (no orphans reparented to init), `driver.lock` released, the run ledger in a coherent terminal-or-interrupted state, and partial worktree edits quarantined or restored.
2. Offer four stop levels that differ ONLY in how much in-flight work completes first: after-call, after-set, now (next safe checkpoint), now-force (immediate interrupt).
3. Make the trigger discoverable and escalating at the terminal (Ctrl-C), and scriptable out-of-band (`aw oc run stop <run-id> --<level>`).
4. Record the interrupted item's disposition HONESTLY: known-and-incomplete for level 3, `unknown_outcome` for level 4, never a fabricated success.
5. Guarantee a later resume can distinguish "safe to continue" from "must reconcile first" from the ledger alone.
6. Never leave the operator guessing whether cleanup ran. Cleanup is unconditional and reported.

## 2. Non-goals

- Not a crash-recovery redesign. Crash recovery is `ud28vy`'s; this spec consumes it.
- Not a pause/resume-mid-turn feature. A stopped turn is stopped, not suspended for later continuation.
- Not a change to what the agent is asked to do, nor to plan/spec lifecycle authority.
- Not a replacement for `SIGKILL`. An operator who sends `SIGKILL` bypasses this protocol by definition; the spec's obligation is that the NEXT run reconciles that state, not that `SIGKILL` be graceful.
- Not worktree isolation itself (Set `wtiso`).

## 3. The four levels (DECIDED; the levels are the maintainer's design)

All four run the IDENTICAL cleanup routine at the end. None is "just die" (which is what today's SIGTERM does).

| Level | Name | In-flight work allowed to complete | Interrupted-item disposition |
|---|---|---|---|
| 1 | STOP-AFTER-CALL | The in-flight IPD's agent turn finishes (writes outcome JSON, checkpoints ledger). Next item is NOT dequeued. | none interrupted |
| 2 | STOP-AFTER-SET | The rest of THIS set's queue finishes. Stops before any next set. | none interrupted |
| 3 | STOP-NOW | Current agent turn stops at its next SAFE checkpoint (does not finish). | KNOWN: recorded stopped/incomplete |
| 4 | STOP-NOW-FORCE | Current agent turn is interrupted IMMEDIATELY, not at a checkpoint. | INDETERMINATE: recorded `unknown_outcome`, needs reconciliation before resume |

The only difference between 3 and 4 is outcome CERTAINTY, not cleanliness.

## 4. Requirements

### 4.1 The clean-shutdown invariant (unconditional)

- R1. On completion of ANY level, no descendant agent process of the driver remains alive or reparented to init. The driver MUST reap the whole process tree, not just its direct child.
- R2. On completion of ANY level, `driver.lock` is released. A lock holding a dead PID is a defect, not an acceptable outcome.
- R3. On completion of ANY level, the run ledger is in a coherent state: every item is terminal, or explicitly marked interrupted with its level and certainty.
- R4. On completion of ANY level, partial worktree edits are quarantined or restored per the reconciliation routine; the tree is never left silently contaminated.
- R5. The cleanup routine is ONE implementation shared by all four levels and by crash recovery. Divergent per-level cleanup is prohibited.
- R6. Cleanup runs even when the level's "allow to complete" phase fails or times out. A failure to wind down gracefully escalates the level; it never skips cleanup.

### 4.2 Levels and mechanism

- R7. The driver POLLS a stop-request flag at cooperative checkpoints: between agent turns for levels 1 and 2, and at the next safe point within a turn for level 3. Level 4 is interrupt-then-reconcile. Raw `kill` is NOT the mechanism for levels 1 to 3.
- R8. A stop request is durable and idempotent: recorded once, re-reading it does not re-trigger, and it survives the driver being between checkpoints.
- R9. Escalation is monotonic. A request may only raise the level (1 -> 3 -> 4), never lower it, so an operator "pressing harder" is always honored.
- R10. Level 3's "safe checkpoint" MUST be defined in terms of observable state (e.g. no in-flight write to a tracked file, no partially written ledger record), not elapsed time.
- R11. Each level has a bounded wind-down budget. Exceeding it escalates to the next level with that escalation RECORDED, so a hung turn cannot make a stop hang forever.

### 4.3 Trigger UX

- R12. First SIGINT (Ctrl-C) requests level 1. Repeated SIGINT escalates 1 -> 3 -> 4, with a printed hint that pressing again stops harder.
- R13. SIGTERM requests level 3.
- R14. `aw oc run stop <run-id> --after-call|--after-set|--now|--now-force` requests any level out-of-band, from a second terminal or a script. `aw agy run stop` behaves identically.
- R15. Flag names convey HOW FORCEFULLY the turn is interrupted, never WHETHER cleanup happens. No flag may imply that cleanup is optional.
- R16. On each request the driver prints the level accepted, what it is waiting for, and how to escalate. Silence during wind-down is a defect.
- R17. `stop` on an unknown, already-finished, or already-stopping run reports that state and exits nonzero for "no such live run", rather than appearing to succeed.

### 4.4 Ledger and resume

- R18. An interrupted item records: the level that interrupted it, the certainty (known vs `unknown_outcome`), the observed git state, and what a resume must do first.
- R19. A later run MUST refuse to blindly resume an `unknown_outcome` item; it reconciles (per `ud28vy`) or requires explicit operator action.
- R20. A level 1 or 2 stop produces NO `unknown_outcome` items, since nothing was interrupted mid-turn.
- R21. The ledger distinguishes DELIBERATE stop from CRASH, so the history shows the operator's intent rather than implying a failure.

### 4.5 Honesty

- R22. A stopped item is never recorded as executed, complete, or successful. Disposition reflects real repository state, per the anti-greenwash rule.
- R23. The driver never claims cleanup it did not perform; each invariant R1 to R4 is verified and reported, not assumed.

## 5. Testable acceptance criteria

- A1. With a run in flight, send SIGINT once. The in-flight turn completes, the next item is not started, the process exits 0, no descendant of the driver remains (verified via process table), `driver.lock` is gone, and `git status` shows no unexplained modifications.
- A2. Same as A1 but with SIGINT sent three times in quick succession: the run ends at level 4, the interrupted item is recorded `unknown_outcome`, and the escalation path 1 -> 3 -> 4 appears in the run record.
- A3. Send SIGTERM to a run in flight. The current turn stops at a safe checkpoint, the item is recorded stopped/incomplete with KNOWN certainty (not `unknown_outcome`), and all of R1 to R4 hold.
- A4. From a second terminal, `aw oc run stop <run-id> --after-set` on a multi-set run: the current set's remaining queue completes, the next set is never started, exit 0, invariants hold.
- A5. `aw oc run stop <bogus-run-id>` exits nonzero with a message naming the unknown run, and mutates nothing.
- A6. Force-stop a run mid-write (level 4), then start a new run over the same queue: the new run REFUSES to blindly resume the `unknown_outcome` item and reports the reconciliation requirement.
- A7. Simulate a wind-down that exceeds its budget at level 1 (a turn that will not finish): the driver escalates, records the escalation, and still satisfies R1 to R4.
- A8. Kill the driver with SIGKILL (bypassing the protocol): the next run's reconciliation detects the stale lock and orphaned state and reports it, demonstrating the shared routine covers both stop and crash.
- A9. Assert exactly ONE cleanup implementation exists (a structural/AST or import-graph check), satisfying R5 and preventing per-level drift.
- A10. On a platform without POSIX signal semantics, the documented portable subset still provides level 1 and the out-of-band `stop` command, and the unsupported triggers fail loudly rather than silently doing nothing.

## 6. Open questions

### OQ-01: Does level 3's "next safe checkpoint" require agent cooperation, or can the driver alone determine it?

- Blocking: yes (it determines whether level 3 is implementable without changing the agent prompt/protocol)
- Status: resolved
- Owner: human maintainer
- Resolution (2026-08-29, from repository evidence; NO agent cooperation required): the driver ALREADY consumes the child's structured event stream line-by-line, so it can observe turn-internal boundaries itself. `oc_runipd.py:1765-1786` spawns the child with `--format json` and iterates `for line in process.stdout`, dispatching each line to `render_event(...)`; the captured session JSONL for a live run contains discrete `{"type":"step_start",...}` and `{"type":"tool_use",...}` records (verified against `.aw/records/runs/run-20260829T053827Z-2084502/sessions/01-jolfpj-attempt-1.jsonl`). A SAFE CHECKPOINT is therefore DEFINED as the instant after a completed `tool_use`/step event and before the next one is dispatched, which the driver detects unilaterally. This satisfies R10 (observable state, not elapsed time) with no prompt/protocol change and no per-agent capability negotiation. Consequence: level 3 does NOT degrade to level 4 for a non-cooperating agent. The existing `StallWatchdog` (`oc_runipd.py:1769`) is the precedent that the driver may act on stream observation alone.

### OQ-02: Should `stop` be able to target ALL live runs at once (e.g. `--all`)?

- Blocking: no
- Status: open
- Owner: human maintainer
- Notes: Concurrent runs are normal in this repo (multiple drivers were live on 2026-08-29). A per-run-id `stop` may be tedious in that situation, but `--all` is a broad blast radius. Deferrable: ship per-run-id first.

### OQ-03: Where does the stop-request flag live?

- Blocking: yes (it interacts directly with `wtiso` Phase 4, which relocates machine state out of the repo)
- Status: resolved
- Owner: human maintainer
- Resolution (2026-08-29, follow `wtiso`, do not invent a third location): the stop-request flag is per-machine CONTROL state, exactly the category `wtiso` Phase 4 relocates, so it lives at `platform_state.checkout_state_root(<checkout-id>)/runs/<run-id>/stop-request.json`, out of the repo and keyed by the Phase-3 canonical git-common-dir checkout-id. Evidence: `wtiso-05` (`58ha43`) E-01/E-02 define `state_home()` and `checkout_state_root(checkout_id)` under `$XDG_STATE_HOME/agent-workflows/checkouts/<checkout-id>/`, and E-04 routes the driver run root so `run_dir` resolves to `checkout_state_root(<checkout-id>)/runs/<run-id>`; the flag simply rides inside that already-relocated run dir. This is why it must NOT go in `<repo>/.aw/state` (the root Phase 4 moves) and must NOT be resolved from a worktree-relative path (backlog `dh0uno`: an inner `aw` forks a second state tree the driver cannot see and teardown destroys). Sequencing consequence recorded in the plans: the out-of-repo path REQUIRES `wtiso` Phase 3+4 (`7p9n2v`, `58ha43`) to be executed first; until then the flag resolves through the same accessor so no second resolver is introduced (the `wtiso` Phase 3 AST guard forbids new raw `.aw/state` construction).

### OQ-04: Is `unknown_outcome` reconciliation automatic or operator-gated?

- Blocking: no
- Status: open
- Owner: human maintainer
- Notes: R19 requires refusing a blind resume, but not whether the tool may auto-reconcile when the observation is unambiguous. Leaning operator-gated for safety (P10), automatic only when git state is provably clean.
