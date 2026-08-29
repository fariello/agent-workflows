# IPD: Phase 5: trigger UX (escalating SIGINT, SIGTERM) and the aw oc/agy run stop command

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R12-R17 define the only surfaces a human actually touches: first SIGINT (Ctrl-C) requests level 1 and repeated SIGINT escalates 1 -> 3 -> 4 with a printed hint, SIGTERM requests level 3, and `aw oc/agy run stop <run-id> --after-call|--after-set|--now|--now-force` requests any level out-of-band from a second terminal or a script. Until this child lands, all four levels exist but are UNREACHABLE by a user (Phases 2-4 are exercised by writing the Phase-1 record directly). The driver currently installs NO signal handler at all, so today a Ctrl-C is Python's default KeyboardInterrupt and a SIGTERM just kills it. This child also enforces the cross-level escalation on a wind-down budget breach (spec R11, A7) that Phase 3 only records.
- Scope: Add the signal handlers (SIGINT with escalation, SIGTERM) in BOTH drivers, the `stop` subcommand on both runners, the per-request progress reporting (spec R16), the unknown/finished-run error path (R17), and the budget-breach escalation enforcement (R11, A7). Also document the portable subset for platforms without POSIX signal semantics (R14/A10). Does NOT change any level's behavior (Phases 2-4 own that) and does NOT add `stop --all` (spec OQ-02, deferred).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_triggers.py
- Item-Dependencies: executed:m0z0ti
- Status: approved
- Set: runstop
- Order: 6
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 71vjbn
- Approval: 2026-08-29, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-08-29 approved (aw set): status set to approved
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-601..PR-608. Verdict is NOT approve because orchestrator OQ-02 remains open and now explicitly blocks two items here. Three defects were found by exercising the real code. (1) BLOCKER: `main()`'s implicit-start shim rewrites `argv = ["start"] + argv` for any first token outside a HARDCODED set (`oc_runipd.py:2905-2914`; `agy_runipd.py:2921-2930`), and the shim lives in `main()` not `build_parser()`, so adding a `stop` subparser alone leaves `stop <run-id> --now` silently rewritten to `start stop <run-id> --now` - evaluated directly - turning an operator's stop request into a run LAUNCH with the literal selector `stop`. E-03 now owns updating that set, with a test in both drivers. (2) BLOCKER: registering a SIGINT handler is a MODIFICATION, not additive - it suppresses the default `KeyboardInterrupt` that `main`'s exit-130 path (:2972-2974) and `execute_item`'s item-level `interrupted`/`ipd-interrupted` bookkeeping (:2011-2019) both depend on, and Phases 3-4 rely on that item being recorded interrupted; E-01 must now preserve or deliberately replace both. (3) HIGH: R17's "already-finished" case had no defined probe, and the obvious `driver.lock`-exists check is provably not liveness (the `2ouj70` review measured a stale lock outliving its holder with the flock already free), so E-04 now mandates a non-blocking `flock` probe. Also SPLIT the A10 work: the original E-07 was unexecutable (both drivers `import fcntl` unconditionally, so with it masked the module raises `ModuleNotFoundError` and no portable subset exists) AND its test method could not detect that (patching `sys.platform` at test time cannot undo an import-time failure), so the DECISION is now blocked item E-08 and the platform CLAIM is blocked item E-07, which also cleared an `IPD-Z602` density advisory the linter raised on my first attempt. Additionally: E-01 must use `gq6m2u`'s handler-safe entry rather than the plain locked write (that review measured a handler deadlock and a ~50% lost-escalation race), recorded the verified favorable fact that the child is in its own process group (`start_new_session=True`) so terminal Ctrl-C reaches only the driver, reconciled the `fcntl` Deferred entry that contradicted A10, and switched full-suite evidence to `make test-all`.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): Authored review-ready from spec c4gd2h (graduation of backlog kjzlgw).

- 2026-08-29 draft (opencode (its_direct/pt3-claude-opus-5-1m-us)): created.

## Goal

Make all four stop levels reachable by a human: escalating SIGINT, SIGTERM, and an out-of-band `aw oc/agy run stop <run-id> --<level>` command, with progress reporting, an honest error path for an unknown run, and enforcement of the wind-down budget escalation (spec R12-R17, R11, A5, A7, A10).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: signal triggers

- [ ] E-01 Register a SIGINT handler in BOTH drivers implementing spec R12's escalation: 1st SIGINT requests level 1, 2nd requests level 3, 3rd requests level 4, each via Phase 1's SIGNAL-HANDLER-SAFE entry point (`gq6m2u` E-06, NOT the plain `request_stop`) so write-time monotonicity prevents a downgrade under rapid presses AND the handler cannot deadlock on the sidecar lock. `gq6m2u`'s review established both: a bare atomic write loses the higher level in ~50% of races, and a blocking lock acquire inside a handler hangs the process outright, so the handler must take the non-blocking-then-defer path. The handler MUST do only the minimal record-and-return (no cleanup inside the handler); the existing poll acts on it (spec R7). Registering a SIGINT handler also SUPPRESSES the default `KeyboardInterrupt`, which two existing handlers depend on: `main`'s `except KeyboardInterrupt` returns 130 with "Interrupted; durable run state was preserved." (`oc_runipd.py:2972-2974`; `agy_runipd.py:2997`), and `execute_item`'s marks the item `interrupted`, appends an `ipd-interrupted` event, and re-raises (`oc_runipd.py:2011-2019`; `agy_runipd.py:2096`). Decide and record explicitly what happens to both: the item-level bookkeeping at :2011 must still occur for a level-3/4 stop (Phases 3-4 rely on the item being recorded interrupted), so either keep raising `KeyboardInterrupt` from the poll at the chosen boundary or replicate that bookkeeping on the new path - do not silently strand it. Also note the child is spawned with `start_new_session=True` (`oc_runipd.py:1759-1760`), verified to put it in a DIFFERENT process group, so a terminal Ctrl-C reaches only the driver and not the agent: the driver alone owns the escalation, and the child is stopped only through `clean_shutdown`.
  - Depends on: none
  - Expected outcome: delivering SIGINT three times to a spawned driver yields recorded levels 1, then 3, then 4 with a 3-entry escalation history; the handler performs no teardown itself and never blocks; and the pre-existing exit-130 path and the `execute_item` interrupted-bookkeeping are either preserved or deliberately replaced, with a test covering whichever was chosen.
  - Execution state: pending
- [ ] E-02 Register a SIGTERM handler in BOTH drivers requesting level 3 (spec R13), replacing today's default-kill behavior in which the driver prints `Terminated` and exits while its child is orphaned.
  - Depends on: E-01
  - Expected outcome: SIGTERM to a spawned driver records level 3 (not an immediate exit), the turn stops at a safe checkpoint per Phase 3, and the Phase-0 invariants hold; the Phase-0 characterization test pinning the OLD orphan behavior is consciously updated with a note.
  - Execution state: pending

### Task group 2: the out-of-band command

- [ ] E-03 Add a `stop` subcommand to BOTH runners' own parsers (where `start` already lives, NOT `cli.py`'s `oc` group, since `aw oc run` forwards REMAINDER verbatim - confirmed at `cli.py:2642-2658`) accepting `<run-id>` and exactly one of `--after-call|--after-set|--now|--now-force`, mapping to levels 1-4 via `request_stop(...)`. Flag help MUST state that these control interruption FORCE only and that cleanup is unconditional (spec R15). MANDATORY and easily missed: also add `"stop"` to the IMPLICIT-START SHIM's `subcommands` set in `main()` (`oc_runipd.py:2905-2914`; `agy_runipd.py:2921-2930`). That shim rewrites `argv = ["start"] + argv` for any first token not in the set, so a `stop` verb absent from it turns `stop <run-id> --now` into `start stop <run-id> --now`, i.e. it tries to START a run with the literal selector `stop` (verified by evaluating the shim logic). That is a silent, destructive misfire - the operator asks to stop and instead launches work. Because the shim lives in `main()` and NOT in `build_parser()`, adding the subparser alone does not cover it.
  - Depends on: E-01
  - Expected outcome: `aw oc run stop <run-id> --after-set` records level 2 for that run from a second process; `--help` shows all four flags and the cleanup-is-unconditional wording; the same works for `aw agy run stop`; and a test asserts the bare form `stop <run-id> --now` is NOT rewritten into `start` in EITHER driver.
  - Execution state: pending
- [ ] E-04 Implement the honest error path (spec R17): `stop` on an unknown, already-finished, or already-stopping run reports that state and exits NONZERO for a nonexistent live run, mutating nothing. It must never appear to succeed. Each of the three states needs a DEFINED probe, and only two are free: (a) UNKNOWN - `resolve_run_dir` already raises `DriverError` for a missing run (`oc_runipd.py:2664-2683`); (b) ALREADY-STOPPING - `read_stop_request(run_dir)` is non-None (Phase 1); (c) LIVE vs FINISHED - there is NO run-complete marker in the ledger today, and the presence of `driver.lock` is NOT liveness: measured in this review that a stale `driver.lock` survives its holder's death while its `flock` is already free. So the liveness probe MUST be an attempted non-blocking `flock` on the run's lock (free => no live driver, therefore "no such live run" => nonzero), NOT a file-existence check. Do not invent a new liveness file; `2ouj70` E-02 already makes lock state the observable signal.
  - Depends on: E-03
  - Expected outcome: `stop <bogus-run-id>` exits nonzero naming the unknown run and creates no file; `stop` on a FINISHED run (lock free) exits nonzero saying there is no live run, and creates no stop-request file; `stop` on an already-stopping run reports the existing level and does not downgrade it; a test asserts the finished-run case is decided by lock acquirability rather than by `driver.lock` existing.
  - Execution state: pending

### Task group 3: reporting and escalation enforcement

- [ ] E-05 Report progress on every accepted request (spec R16): print the level accepted, what the driver is waiting for, and how to escalate. Silence during wind-down is a defect.
  - Depends on: E-01, E-03
  - Expected outcome: each accepted request emits a line naming the level, the awaited boundary, and the escalation hint; captured output from a signalled run contains all three for each escalation step.
  - Execution state: pending
- [ ] E-06 Enforce the wind-down budget escalation Phase 3 only recorded (spec R11, A7): on a breach marker or an elapsed deadline read from Phase 1's record, escalate to the next level with the escalation RECORDED, so a hung turn can never make a stop hang forever.
  - Depends on: E-05
  - Expected outcome: a level-1 request against a fake child that will not finish escalates before the recorded deadline plus a bounded margin, records the escalation, and still satisfies all four Phase-0 invariants.
  - Execution state: pending
- [ ] E-07 State the platform support boundary honestly in the user-facing surfaces: say in the `stop` help text and the module docstring which triggers work on which platforms, and assert the unsupported-trigger path fails LOUDLY rather than silently no-opping (spec A10's second half).
  - Depends on: E-03, E-08
  - Expected outcome: the `stop` help and module docstring name the supported platform set and the loud-failure behavior; a test asserts an unsupported trigger raises or warns visibly rather than silently doing nothing. The exact wording follows E-08's resolution and MUST NOT claim a working Windows portable subset unless E-08 selected an option that actually delivers one.
  - Execution state: blocked
  - Execution note: BLOCKED behind E-08 (orchestrator `zpbx7o` OQ-02), which decides what the honest wording IS. E-01..E-06 are unaffected and may execute.

- [ ] E-08 Resolve how spec A10 is satisfied, then record the decision, BEFORE E-07 writes any platform claim. Verified in plan-review that A10 is unreachable as the spec words it: both drivers `import fcntl` unconditionally at module top (`oc_runipd.py:17`, `agy_runipd.py:18`) and with `fcntl` masked `import agent_workflows.oc_runipd` raises `ModuleNotFoundError`, so on a non-POSIX host NOTHING works - not level 1, not the out-of-band `stop`. The original E-07 test method also could not detect this, since `sys.platform` is patched at test time while the failing import happens at import time. The three candidate resolutions and their costs are recorded in orchestrator OQ-02; a cross-platform lock (`platform_lock`) plus a Windows Job Object kill is already owned by `wtiso` Phase 5 (`2c122z`), so this Set must not build a second one (P8).
  - Depends on: none
  - Expected outcome: OQ-02 carries a recorded resolution (narrow A10 to a documented POSIX-only limitation, depend on `wtiso` Phase 5, or implement a Windows primitive here), with its consequence for this plan's `Deferred` entry reconciled, so E-07 has an unambiguous, non-contradictory wording to implement.
  - Execution state: blocked
  - Execution note: BLOCKED on a human decision (orchestrator `zpbx7o` OQ-02). This is a decision item, not code; it exists so the platform claim in E-07 cannot be written before the decision that governs it.

## Project conventions discovered (Step 0)

- The driver installs NO signal handler today: the only `signal` references in `oc_runipd.py` are the constants at :1627-1628 and the escalation inside `terminate_process` (:1654-1666), which signals the CHILD, not a handler for the driver itself. So `signal.signal(...)` registration is genuinely new code - but it is not free of interactions: it suppresses the default `KeyboardInterrupt` that TWO existing handlers rely on (`main` :2972-2974 returning 130; `execute_item` :2011-2019 marking the item `interrupted` and re-raising), plus the agy counterparts (:2997, :2096). See E-01.
- Phase 1 (`gq6m2u`, as reviewed) provides a SIGNAL-HANDLER-SAFE request entry (its E-06) in addition to `request_stop`. Use the handler-safe one from a signal handler: `gq6m2u`'s review measured that the plain locked write DEADLOCKS when a signal lands while the lock is held, and that a lockless atomic write loses ~50% of escalation races. The handler-safe path is non-blocking and defers the durable write to the poll.
- A signal handler must be async-signal-safe in practice: it should do the minimum (record via the Phase-1 handler-safe entry) and let the polling loop act, matching spec R7's "driver POLLS a stop-request flag" rather than acting inside the handler.
- The agent child runs in its OWN process group (`start_new_session=True`, `oc_runipd.py:1759-1760`; verified: parent and child pgids differ), so a terminal Ctrl-C is delivered to the driver only. The driver therefore owns escalation entirely, and the child is only ever stopped via `clean_shutdown`.
- The implicit-start shim in `main()` rewrites `argv = ["start"] + argv` for any first token outside a HARDCODED set (`oc_runipd.py:2905-2914`; `agy_runipd.py:2921-2930`). Adding a subparser does NOT update it, so `stop` must be added to that set or `stop <run-id> --now` silently becomes `start stop <run-id> --now`.
- There is no run-complete/finished marker in the ledger, so "is this run LIVE?" must be probed via lock acquirability, not `driver.lock` existence (a stale lock file outlives its holder while the `flock` is already free - measured in the `2ouj70` review). Relevant to R17.
- Validation-command trap: default `addopts` (`pyproject.toml:122`) is `-m 'not slow'`, so a bare `python -m pytest -q` deselects `slow` subprocess/signal tests - exactly this child's class. Use `make test-all`.
- Phase 1 recorded the per-level budget and deadline; Phase 3 recorded a breach marker. This child is where the breach ESCALATES (spec A7), so the escalation logic reads one authoritative deadline rather than inventing a timeout.
- CLI convention: subcommands are declared on the runner's own parser; `aw oc run` currently forwards `argparse.REMAINDER` verbatim to `oc_runipd.main` (`cli.py`, the `oc`/`opencode` forwarding), so `stop` is added to the RUNNER's parser (where `start` already lives), not to `cli.py`'s `oc` group.
- `fcntl`-based `run_lock` (`oc_runipd.py:738-756`) is POSIX-only, and Windows lacks POSIX SIGTERM delivery: spec A10 requires the portable subset (level 1 + the out-of-band `stop`) to work and unsupported triggers to fail LOUDLY rather than silently no-op.

## Findings

The trigger matrix (spec R12-R14):

| Trigger | Level requested | Notes |
|---|---|---|
| 1st SIGINT (Ctrl-C) | 1 | prints what it is waiting for + how to escalate |
| 2nd SIGINT | 3 | "press again to stop harder" |
| 3rd SIGINT | 4 | terminal escalation |
| SIGTERM | 3 | scriptable single-shot |
| `stop --after-call` | 1 | out-of-band |
| `stop --after-set` | 2 | out-of-band; NOT reachable by signal (deliberate: no natural key for it) |
| `stop --now` | 3 | out-of-band |
| `stop --now-force` | 4 | out-of-band |

Note level 2 is reachable ONLY out-of-band. That is a deliberate consequence of the spec's escalation ladder (1 -> 3 -> 4) and is worth stating so a reviewer does not read it as an omission.

Two honesty requirements drive V-items: spec R15 forbids any flag name implying cleanup is optional (the names describe interruption force only), and spec R16 forbids silence during wind-down (the driver must say which level it accepted and what it is waiting for). Spec R17 requires `stop` on an unknown/finished run to exit nonzero rather than appear to succeed, which is the failure mode most likely to be implemented as a silent success.

VERIFIED (2026-08-29), three facts that change what this child must do:

1. **The implicit-start shim would swallow the new verb.** `main()` rewrites `argv = ["start"] + argv` whenever the first token is not in a hardcoded set (`oc_runipd.py:2905-2914`; `agy_runipd.py:2921-2930`). Evaluated directly: `["stop","run-123","--now"]` becomes `["start","stop","run-123","--now"]`. So without adding `stop` to that set, the operator's stop request would try to START a run with the literal selector `stop` - a silent misfire in the exact opposite direction of the user's intent. The shim lives in `main()`, not `build_parser()`, so adding a subparser alone does not fix it. E-03 now owns this.
2. **Registering a SIGINT handler is a MODIFICATION, not purely additive.** It suppresses the default `KeyboardInterrupt` that two existing handlers depend on: `main`'s exit-130 path (`:2972-2974`) and `execute_item`'s item-level bookkeeping that marks the item `interrupted` and appends an `ipd-interrupted` event (`:2011-2019`). Phases 3 and 4 depend on that item being recorded interrupted, so E-01 must consciously preserve or replace it.
3. **R17's "already-finished" case has no existing signal.** There is no run-complete marker, and `driver.lock`'s existence is not liveness (the `2ouj70` review measured a stale lock outliving its holder with the `flock` already free). The only sound probe is attempting a non-blocking `flock`. E-04 now specifies that rather than leaving "already-finished" undefined.

Favorable fact, also verified: the agent child is spawned with `start_new_session=True` and lands in a DIFFERENT process group (measured), so a terminal Ctrl-C reaches only the driver. The escalation ladder cannot be corrupted by the child receiving its own SIGINTs.

## Proposed changes (ordered, validatable)

1. Signal handlers in both drivers: SIGINT with 1 -> 3 -> 4 escalation and a printed hint; SIGTERM -> level 3. Handler only records via the Phase-1 atomic write; the poll acts.
2. `stop` subcommand on both runners with the four level flags, writing the same record.
3. Progress reporting on each accepted request (spec R16) and the nonzero unknown-run path (R17).
4. Budget-breach escalation enforcement (spec R11, A7) reading Phase 1's deadline and Phase 3's breach marker.
5. New `tests/test_runner_stop_triggers.py` covering the matrix, escalation monotonicity under rapid signals, the error path, and the portable subset.

## Deferred / out of scope (with reason)

- Any level's BEHAVIOR: Phases 2-4 (`1qxuke`, `foi1b3`, `m0z0ti`). This child only requests levels.
- `stop --all` across concurrent runs: spec OQ-02, non-blocking, deliberately deferred (broad blast radius; ship per-run-id first).
- A unified top-level `aw run stop`: orchestrator OQ-01 defers it to the runner unification (backlog `dhuape`).
- Implementing a Windows lock primitive to replace `fcntl`: OWNED ELSEWHERE - `wtiso` Phase 5 (`2c122z`) already plans `platform_lock` plus a Windows Job Object process-tree kill, so this child must not build a second one (P8). NOTE the unresolved tension this creates with spec A10, which is exactly what E-08/OQ-02 must settle: because `fcntl` is imported unconditionally, deferring the lock means there is NO working portable subset to document, so "this child documents and tests the portable subset" cannot be true simultaneously with this deferral. Whichever option OQ-02 selects, this entry must be reconciled with E-07's wording rather than left contradicting it.

## Scope check

- Over-scope: none. No level behavior is changed; only request surfaces and the escalation enforcement Phase 3 explicitly deferred here.
- Under-scope: as originally written, YES, in four ways now fixed. (1) Nothing owned adding `stop` to the implicit-start shim's hardcoded subcommand set, so the verb would have been silently rewritten into `start` (E-03). (2) Nothing addressed the two existing `KeyboardInterrupt` handlers that a new SIGINT handler suppresses, including the item-level `interrupted` bookkeeping Phases 3-4 depend on (E-01). (3) R17's "already-finished" case had no defined probe, and the obvious one (`driver.lock` exists) is provably not liveness (E-04). (4) A10 was assigned to an item that cannot satisfy it and whose test method cannot detect the failure; the decision is now a separate blocked item (E-08) so the platform CLAIM in E-07 cannot be written before the decision that governs it. Signals (R12-R13), the CLI verb (R14), flag-name honesty (R15), progress reporting (R16), the unknown/finished/stopping paths (R17), budget escalation (R11/A7), the platform boundary (A10), and the A10 decision each now have an E-item and a 1:1 V-item.

## Required tests / validation

- `python -m pytest tests/test_runner_stop_triggers.py -q -m ''` passes (pass `-m ''` so `slow`-marked signal/subprocess tests in this file are not silently deselected).
- Spec acceptance A5 (unknown run id exits nonzero, mutates nothing) and A7 (budget breach escalates and still satisfies the invariants) are demonstrated. A10 is demonstrated only to the extent E-08's resolution allows, and its status is stated plainly rather than claimed.
- Rapid repeated SIGINT is tested for MONOTONIC escalation (never a downgrade), exercising Phase 1's handler-safe entry so the test also proves the handler neither deadlocks nor loses a race.
- Signal tests deliver real signals to a spawned driver process (not a mocked handler) so the handler registration itself is proven, and each test must fail on timeout rather than hang the suite.
- A test asserts `stop <run-id> --now` is NOT rewritten by the implicit-start shim, in BOTH drivers.
- A test asserts the pre-existing interrupt behaviors are preserved-or-deliberately-replaced: the exit-130 path and `execute_item`'s `interrupted`/`ipd-interrupted` bookkeeping.
- A test asserts the finished-run case is decided by lock acquirability, not by `driver.lock` existing.
- `make test-all` (`python -m pytest tests/ -m ''`) remains green: the FULL suite, since a bare `python -m pytest -q` deselects `-m 'not slow'` per `pyproject.toml:122`.

## Spec / documentation sync

- `aw oc run --help` and `aw agy run --help` gain the `stop` verb and its four flags; the help text MUST convey that the flags control interruption FORCE only and that cleanup is unconditional (spec R15).
- Document the portable subset (which triggers work without POSIX signals) in the `stop` help and the module docstring (spec A10).
- Spec `c4gd2h` becomes eligible for `implemented` only after the orchestrator's whole-Set verification (E-01 there), not here.

## Open questions

### OQ-01: Should level 2 (after-set) also be reachable by a signal?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: no. Spec R12's escalation ladder is explicitly 1 -> 3 -> 4, so there is no free key position for level 2, and overloading one would make the "press again to stop harder" model ambiguous. Level 2 stays out-of-band via `stop --after-set` (spec R14). Recorded here because a reviewer could otherwise read the gap as an omission rather than a decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted pytest output delivering three REAL SIGINTs to a spawned driver process (not a mocked handler) showing recorded levels 1 -> 3 -> 4 and a 3-entry escalation history, plus evidence the handler itself performed no teardown (cleanup observed only after the poll acted).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted pytest output delivering a real SIGTERM showing level 3 recorded and the turn stopping at a checkpoint, the four Phase-0 invariant observations, and the diff/note showing the Phase-0 characterization test pinning the old orphan behavior was consciously updated rather than silently deleted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted `aw oc run stop --help` AND `aw agy run stop --help` output showing all four flags and the cleanup-is-unconditional wording (spec R15), plus pasted pytest output showing a level recorded from a SEPARATE process for each of the four flags.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output for spec A5 showing `stop <bogus-run-id>` exiting nonzero with the run id named, plus a filesystem listing proving nothing was created; plus the already-stopping case showing the existing level reported and NOT downgraded.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted captured driver output from a signalled run containing, for EACH escalation step, the accepted level, the awaited boundary, and the escalation hint (spec R16). Missing any of the three fails this item.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted pytest output for spec A7 showing a level-1 request against a non-finishing fake child escalating before the recorded deadline plus a bounded margin, the escalation recorded in the run record, and all four Phase-0 invariants still satisfied.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted pytest output showing an unsupported trigger raising or warning VISIBLY (asserted on the captured warning/exception, not on the absence of a crash), plus the pasted `stop` help and module docstring naming the supported platform set. A `sys.platform` monkeypatch is NOT acceptable as evidence that the portable subset IMPORTS or FUNCTIONS on a non-POSIX host, because the failing `import fcntl` happens before any such patch; only evidence consistent with E-08's resolution may be offered, and no pasted text may claim Windows support that E-08 did not deliver.
  - Observed evidence: NOT YET VALIDATED - blocked behind E-08/OQ-02. Plan-review 2026-08-29 established the blocking fact rather than the acceptance: with `fcntl` masked, `import agent_workflows.oc_runipd` raises `ModuleNotFoundError: No module named 'fcntl'`, so no portable subset exists on a non-POSIX host today and there is no honest platform claim to validate until the human decision lands.
  - Result: blocked
- [ ] V-08 validates E-08
  - Required evidence: the resolved orchestrator OQ-02 text pasted here, naming the selected option and its consequence for this plan's `Deferred / out of scope` entry on replacing `fcntl`. If the selection is (B) or (C), evidence must also show the `Item-Dependencies`/scope consequences were recorded rather than left implicit.
  - Observed evidence: NOT YET VALIDATED - awaiting the human decision on orchestrator `zpbx7o` OQ-02, which is `Status: open` and `Blocking: yes` as of 2026-08-29. Nothing to paste until it is resolved; this item is deliberately left blocked rather than pre-answered by the reviewer, since the choice is the maintainer's (it trades spec fidelity against serializing this Set behind `wtiso`).
  - Result: blocked

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract (inherited from orchestrator `zpbx7o`):

- Open questions: **ONE BLOCKING** - orchestrator `zpbx7o` OQ-02 (how spec A10 is honestly satisfied) is `Status: open`. E-07 and E-08 are `blocked` on it and MUST NOT be executed until it is resolved. E-01..E-06 are unaffected and may be executed once this plan is approved; a partial execution that completes E-01..E-06 and leaves E-07/E-08 blocked is the expected shape, so this plan MUST NOT be finalized to `executed/` until OQ-02 lands and both items are satisfied. Spec OQ-01/OQ-03 are RESOLVED in c4gd2h; this plan's own OQ-01 is resolved.
- Scope fence: touch ONLY this plan's declared `Scope-Paths`. Widening requires a new plan. Specifically: do NOT build a lock abstraction or Windows process-kill primitive (owned by `wtiso` `2c122z`), do NOT change any level's BEHAVIOR (Phases 2-4 own it; this child only requests levels and enforces the budget escalation Phase 3 deferred), and do NOT write a durable stop record from inside a signal handler by any path other than Phase 1's handler-safe entry.
- Honesty rule (hard MUST): paste the ACTUAL runner output into each `V-*` Observed evidence. Never claim a test passed that was not run.
- Commits: path-scoped only; never `git add -A`/`-a`; never push; never tag or release.
- Lifecycle: `aw ipd begin <this> --actor <agent/model>` BEFORE executing (fail-closed), then `aw ipd finalize` after validation passes. Never hand-move to `executed/`.
- If any validation fails, STOP and report rather than marking the plan executed.
