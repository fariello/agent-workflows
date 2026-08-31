# IPD: Phase 5: trigger UX (escalating SIGINT, SIGTERM) and the aw oc/agy run stop command

- Date: 2026-08-29
- Kind: child
- Blocks-Release: next
- From-Backlog: kjzlgw
- Concern: Spec c4gd2h R12-R17 define the only surfaces a human actually touches: first SIGINT (Ctrl-C) requests level 1 and repeated SIGINT escalates 1 -> 3 -> 4 with a printed hint, SIGTERM requests level 3, and `aw oc/agy run stop <run-id> --after-call|--after-set|--now|--now-force` requests any level out-of-band from a second terminal or a script. Until this child lands, all four levels exist but are UNREACHABLE by a user (Phases 2-4 are exercised by writing the Phase-1 record directly). The driver currently installs NO signal handler at all, so today a Ctrl-C is Python's default KeyboardInterrupt and a SIGTERM just kills it. This child also enforces the cross-level escalation on a wind-down budget breach (spec R11, A7) that Phase 3 only records.
- Scope: Add the signal handlers (SIGINT with escalation, SIGTERM) in BOTH drivers, the `stop` subcommand on both runners, the per-request progress reporting (spec R16), the unknown/finished-run error path (R17), and the budget-breach escalation enforcement (R11, A7). Also document the portable subset for platforms without POSIX signal semantics (R14/A10). Does NOT change any level's behavior (Phases 2-4 own that) and does NOT add `stop --all` (spec OQ-02, deferred).
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_stop.py, tests/test_runner_stop_triggers.py
- Item-Dependencies: executed:m0z0ti
- Status: executed
- Set: runstop
- Order: 6
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-5-1m-us)
- Id: 71vjbn

## Workflow history
- 2026-08-31 executed (opencode/its_direct/pt3-claude-opus-5-1m-us): Phase 5 complete: all four stop levels reachable, plus the honest A10 platform boundary. E-01..E-06 were executed in the earlier partial run (driver run-20260830T202016Z-3474491); E-07/E-08 are closed out now that orchestrator zpbx7o OQ-02 is resolved as option (A), narrow A10 to a documented POSIX-only limitation. OQ-02's blocking premise was factually obsolete rather than merely overruled: it existed because a top-level import fcntl made the drivers unloadable on Windows, and plan y6mfgo removed that barrier by routing all six affected modules through one platform_lock helper with a subprocess test proving each still imports with fcntl blocked. E-07 therefore required NO product change: y6mfgo had already written the three platform statements (STOP_PLATFORM_NOTE, the module docstring, render_trigger_support), verified here by INVOKING them rather than reading them. The claim does not overstate: triggers remain POSIX-only and the out-of-band stop command is the portable path. Whole suite RE-MEASURED rather than trusting the partial run's figure, since HEAD moved: make test-all -> 5 failed, 4261 passed, 3 skipped, 4 xfailed. ZERO REGRESSIONS, proved by reproducing all five failures in a pristine clone at d4febb8e, the commit before this close-out; failures fell 20 -> 5 and passes rose 4075 -> 4261 from intervening work. Four are the pre-existing undeclared-CLI-leaf family, the fifth a cross-set level-2 queueing assertion; none is owned by this plan. [Scope reconciliation - in-scope-unmodified agent_workflows/agy_runipd.py: modified by the earlier partial execution (E-01..E-06) and by y6mfgo; E-07/E-08 needed no further change here; in-scope-unmodified agent_workflows/oc_runipd.py: modified by the earlier partial execution (E-01..E-06) and by y6mfgo; E-07/E-08 needed no further change here; in-scope-unmodified agent_workflows/runner_stop.py: E-07's platform statements were already written by y6mfgo (STOP_PLATFORM_NOTE, module docstring, render_trigger_support); verified by invocation rather than re-edited; in-scope-unmodified tests/test_runner_stop_triggers.py: already carries the loud-failure test and y6mfgo migrated its premise tripwire; verified passing rather than re-edited]
- 2026-08-31 E-07/E-08 UNBLOCKED by plan `y6mfgo` (locksafe-01), now EXECUTED. The A10 platform question that blocked them has a FACTUAL answer, so E-07's platform claim no longer has to be guessed and E-08's decision no longer waits on orchestrator `zpbx7o` OQ-02's lock half. What `y6mfgo` changed: `oc_runipd`, `agy_runipd`, `runner_stop`, `agy_sessions`, `project_registry` and `run_ledger_store` NO LONGER `import fcntl` at top level; all locking goes through the one `platform_lock` helper (backed by `filelock`), and a test proves all six modules IMPORT with `fcntl` blocked. So A10's FIRST half is now reachable: there IS a host on which the driver loads without POSIX file locking, which is exactly what the previous `partial` execution recorded as impossible. WHAT THE HONEST CLAIM MUST STILL SAY, because `y6mfgo` scoped these OUT deliberately: the SIGINT/SIGTERM ladder needs POSIX signal semantics and the process-tree reap (`os.killpg`/`getpgid`) has no Windows equivalent, so the TRIGGERS remain POSIX-only and the out-of-band `stop` command is the portable path. Importing is not supporting; do not overstate it. `y6mfgo` already updated the three in-code platform statements (`runner_stop`'s module docstring, the `render_trigger_support` note, and `STOP_PLATFORM_NOTE`) to that narrower and now-accurate wording, and migrated `tests/test_runner_stop_triggers.py`'s premise tripwire, which formerly ASSERTED the top-level `import fcntl` was present. This plan's `Status` is UNCHANGED (`approved`, still in `pending/`): E-07/E-08 and V-07/V-08 are unblocked but NOT executed, so it still cannot finalize.
- 2026-08-31 PARTIAL EXECUTION (opencode (its_direct/pt3-claude-opus-5-1m-us), driver run-20260830T202016Z-3474491): E-01..E-06 EXECUTED and V-01..V-06 validated with pasted evidence; E-07/E-08 and V-07/V-08 remain BLOCKED on orchestrator `zpbx7o` OQ-02 (a human decision), which is the shape this plan's own execution contract predicted. The plan therefore STAYS `approved` in `pending/` and was NOT finalized: `aw ipd lint --phase pre-transition` correctly refuses with IPD-S404 on exactly those four items. Delivered: the SIGINT ladder (1 -> 3 -> 4) and SIGTERM -> level 3 in BOTH drivers via one shared handler-safe installer; the `stop` verb with all four flags in both runners, INCLUDING the implicit-start shim fix without which `stop <run-id> --now` became `start stop <run-id> --now`; the R17 error path with liveness probed by lock ACQUIRABILITY (a stale lock file is proven to read `finished`); the R16 three-part progress report; and the R11/A7 budget-breach ESCALATION Phase 3 only recorded. FOUR DECISIONS were recorded to the run's decisions register rather than resolved silently: (D1) three back-to-back SIGINTs cannot reach level 4 because standard POSIX signals are NOT QUEUED - measured three ways, including an alternative handler design that fails identically, so the ladder test waits per rung and the burst test asserts R9 monotonicity instead; (D2) one escalation does NOT satisfy R11 on a silent child, because level 3 is honored from the child's event stream while only level 4 is acted on out-of-band, so `EscalationWatch` walks the ladder and the honest bound is the SUM of the rungs' budgets; (D3) four sibling scope fences in Phases 1/3/4 and `laneorphan` began passing VACUOUSLY once the handler moved into the shared module, so each was consciously replaced with the invariant that was load-bearing underneath and annotated in-body; (D4) a Phase-3 test asserting "the level is still 3 after a breach" was the fence this phase redeems, and was narrowed rather than deleted. Whole-suite result: `make test-all` -> 20 failed, 4075 passed; a pristine baseline clone of the same commit fails 25, and the failure sets compare to ZERO regressions (my 20 are a strict subset). Out-of-scope paths touched: the four test files in D3/D4, declared for `--scope-reason` at finalize.
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

- [x] E-01 Register a SIGINT handler in BOTH drivers implementing spec R12's escalation: 1st SIGINT requests level 1, 2nd requests level 3, 3rd requests level 4, each via Phase 1's SIGNAL-HANDLER-SAFE entry point (`gq6m2u` E-06, NOT the plain `request_stop`) so write-time monotonicity prevents a downgrade under rapid presses AND the handler cannot deadlock on the sidecar lock. `gq6m2u`'s review established both: a bare atomic write loses the higher level in ~50% of races, and a blocking lock acquire inside a handler hangs the process outright, so the handler must take the non-blocking-then-defer path. The handler MUST do only the minimal record-and-return (no cleanup inside the handler); the existing poll acts on it (spec R7). Registering a SIGINT handler also SUPPRESSES the default `KeyboardInterrupt`, which two existing handlers depend on: `main`'s `except KeyboardInterrupt` returns 130 with "Interrupted; durable run state was preserved." (`oc_runipd.py:2972-2974`; `agy_runipd.py:2997`), and `execute_item`'s marks the item `interrupted`, appends an `ipd-interrupted` event, and re-raises (`oc_runipd.py:2011-2019`; `agy_runipd.py:2096`). Decide and record explicitly what happens to both: the item-level bookkeeping at :2011 must still occur for a level-3/4 stop (Phases 3-4 rely on the item being recorded interrupted), so either keep raising `KeyboardInterrupt` from the poll at the chosen boundary or replicate that bookkeeping on the new path - do not silently strand it. Also note the child is spawned with `start_new_session=True` (`oc_runipd.py:1759-1760`), verified to put it in a DIFFERENT process group, so a terminal Ctrl-C reaches only the driver and not the agent: the driver alone owns the escalation, and the child is stopped only through `clean_shutdown`.
  - Depends on: none
  - Expected outcome: delivering SIGINT three times to a spawned driver yields recorded levels 1, then 3, then 4 with a 3-entry escalation history; the handler performs no teardown itself and never blocks; and the pre-existing exit-130 path and the `execute_item` interrupted-bookkeeping are either preserved or deliberately replaced, with a test covering whichever was chosen.
  - Execution state: performed
- [x] E-02 Register a SIGTERM handler in BOTH drivers requesting level 3 (spec R13), replacing today's default-kill behavior in which the driver prints `Terminated` and exits while its child is orphaned.
  - Depends on: E-01
  - Expected outcome: SIGTERM to a spawned driver records level 3 (not an immediate exit), the turn stops at a safe checkpoint per Phase 3, and the Phase-0 invariants hold; the Phase-0 characterization test pinning the OLD orphan behavior is consciously updated with a note.
  - Execution state: performed

### Task group 2: the out-of-band command

- [x] E-03 Add a `stop` subcommand to BOTH runners' own parsers (where `start` already lives, NOT `cli.py`'s `oc` group, since `aw oc run` forwards REMAINDER verbatim - confirmed at `cli.py:2642-2658`) accepting `<run-id>` and exactly one of `--after-call|--after-set|--now|--now-force`, mapping to levels 1-4 via `request_stop(...)`. Flag help MUST state that these control interruption FORCE only and that cleanup is unconditional (spec R15). MANDATORY and easily missed: also add `"stop"` to the IMPLICIT-START SHIM's `subcommands` set in `main()` (`oc_runipd.py:2905-2914`; `agy_runipd.py:2921-2930`). That shim rewrites `argv = ["start"] + argv` for any first token not in the set, so a `stop` verb absent from it turns `stop <run-id> --now` into `start stop <run-id> --now`, i.e. it tries to START a run with the literal selector `stop` (verified by evaluating the shim logic). That is a silent, destructive misfire - the operator asks to stop and instead launches work. Because the shim lives in `main()` and NOT in `build_parser()`, adding the subparser alone does not cover it.
  - Depends on: E-01
  - Expected outcome: `aw oc run stop <run-id> --after-set` records level 2 for that run from a second process; `--help` shows all four flags and the cleanup-is-unconditional wording; the same works for `aw agy run stop`; and a test asserts the bare form `stop <run-id> --now` is NOT rewritten into `start` in EITHER driver.
  - Execution state: performed
- [x] E-04 Implement the honest error path (spec R17): `stop` on an unknown, already-finished, or already-stopping run reports that state and exits NONZERO for a nonexistent live run, mutating nothing. It must never appear to succeed. Each of the three states needs a DEFINED probe, and only two are free: (a) UNKNOWN - `resolve_run_dir` already raises `DriverError` for a missing run (`oc_runipd.py:2664-2683`); (b) ALREADY-STOPPING - `read_stop_request(run_dir)` is non-None (Phase 1); (c) LIVE vs FINISHED - there is NO run-complete marker in the ledger today, and the presence of `driver.lock` is NOT liveness: measured in this review that a stale `driver.lock` survives its holder's death while its `flock` is already free. So the liveness probe MUST be an attempted non-blocking `flock` on the run's lock (free => no live driver, therefore "no such live run" => nonzero), NOT a file-existence check. Do not invent a new liveness file; `2ouj70` E-02 already makes lock state the observable signal.
  - Depends on: E-03
  - Expected outcome: `stop <bogus-run-id>` exits nonzero naming the unknown run and creates no file; `stop` on a FINISHED run (lock free) exits nonzero saying there is no live run, and creates no stop-request file; `stop` on an already-stopping run reports the existing level and does not downgrade it; a test asserts the finished-run case is decided by lock acquirability rather than by `driver.lock` existing.
  - Execution state: performed

### Task group 3: reporting and escalation enforcement

- [x] E-05 Report progress on every accepted request (spec R16): print the level accepted, what the driver is waiting for, and how to escalate. Silence during wind-down is a defect.
  - Depends on: E-01, E-03
  - Expected outcome: each accepted request emits a line naming the level, the awaited boundary, and the escalation hint; captured output from a signalled run contains all three for each escalation step.
  - Execution state: performed
- [x] E-06 Enforce the wind-down budget escalation Phase 3 only recorded (spec R11, A7): on a breach marker or an elapsed deadline read from Phase 1's record, escalate to the next level with the escalation RECORDED, so a hung turn can never make a stop hang forever.
  - Depends on: E-05
  - Expected outcome: a level-1 request against a fake child that will not finish escalates before the recorded deadline plus a bounded margin, records the escalation, and still satisfies all four Phase-0 invariants.
  - Execution state: performed
- [x] E-07 State the platform support boundary honestly in the user-facing surfaces: say in the `stop` help text and the module docstring which triggers work on which platforms, and assert the unsupported-trigger path fails LOUDLY rather than silently no-opping (spec A10's second half).
  - Depends on: E-03, E-08
  - Expected outcome: the `stop` help and module docstring name the supported platform set and the loud-failure behavior; a test asserts an unsupported trigger raises or warns visibly rather than silently doing nothing. The exact wording follows E-08's resolution and MUST NOT claim a working Windows portable subset unless E-08 selected an option that actually delivers one.
  - Execution state: performed
  - Execution note: ALREADY DELIVERED IN CODE by `y6mfgo`, which updated the three platform statements in the same pass that removed the import barrier, so this item required no further edit: `runner_stop.STOP_PLATFORM_NOTE` (appended to the `stop` help), the module docstring, and `render_trigger_support`. Verified by invoking them rather than by reading them (see V-07). The wording conforms to option (A) and does NOT claim a working Windows trigger set: it states the triggers are POSIX-only and names the out-of-band `stop` command as the portable path.
  - Execution note: BLOCKED behind E-08 (orchestrator `zpbx7o` OQ-02), which decides what the honest wording IS. E-01..E-06 are unaffected and may execute.

- [x] E-08 Resolve how spec A10 is satisfied, then record the decision, BEFORE E-07 writes any platform claim. Verified in plan-review that A10 is unreachable as the spec words it: both drivers `import fcntl` unconditionally at module top (`oc_runipd.py:17`, `agy_runipd.py:18`) and with `fcntl` masked `import agent_workflows.oc_runipd` raises `ModuleNotFoundError`, so on a non-POSIX host NOTHING works - not level 1, not the out-of-band `stop`. The original E-07 test method also could not detect this, since `sys.platform` is patched at test time while the failing import happens at import time. The three candidate resolutions and their costs are recorded in orchestrator OQ-02; a cross-platform lock (`platform_lock`) plus a Windows Job Object kill is already owned by `wtiso` Phase 5 (`2c122z`), so this Set must not build a second one (P8).
  - Depends on: none
  - Expected outcome: OQ-02 carries a recorded resolution (narrow A10 to a documented POSIX-only limitation, depend on `wtiso` Phase 5, or implement a Windows primitive here), with its consequence for this plan's `Deferred` entry reconciled, so E-07 has an unambiguous, non-contradictory wording to implement.
  - Execution state: performed
  - Execution note: RESOLVED 2026-08-31 as option (A) in orchestrator `zpbx7o` OQ-02, which now reads `Status: resolved` / `Blocking: no`. The question's blocking PREMISE is factually obsolete: it existed because a top-level `import fcntl` made the drivers unloadable on Windows, and plan `y6mfgo` has since executed and removed that barrier. Options (B) and (C) are moot, since `y6mfgo` superseded `2c122z`'s `platform_lock` portion. The Deferred-entry contradiction is gone: a DIFFERENT plan replaced `fcntl`, so this plan's deferral stands and E-07 needed no lock work.
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

## Whole-suite re-measurement at close-out (2026-08-31)

The partial execution above recorded `make test-all` -> `20 failed, 4075 passed` and reconciled that
against a pristine baseline. Because E-07/E-08 were closed later, on a HEAD that has moved (`y6mfgo`
landed in between), the suite was RE-MEASURED rather than trusting that figure:

    make test-all   ->   5 failed, 4261 passed, 3 skipped, 4 xfailed in 163.40s

ZERO REGRESSIONS, proved by comparison rather than asserted. All five failures reproduce in a pristine
`--shared` clone checked out at `d4febb8e`, the commit BEFORE any of this close-out work:

    tests/test_command_surface_declarations.py::...::test_zero_undeclared_parser_leaves
    tests/test_cli.py::SubcommandDescriptionTests::test_every_subparser_has_fuller_description
    tests/test_cli_conformance_matrix.py::...::test_no_undeclared_parser_leaves
    tests/test_cli_conformance_matrix.py::...::test_every_declared_leaf_gets_a_full_scenario_row_set
    tests/test_runner_stop_levels12.py::Level2Tests::test_level_2_leaves_another_sets_runnable_item_queued_when_this_set_is_blocked

(baseline clone: `5 failed, 92 passed` over those four modules). The pass count rose 4075 -> 4261 and
the failure count fell 20 -> 5, both attributable to work that landed in between, not to this plan.

Four of the five are the pre-existing undeclared-CLI-leaf family; the fifth is a cross-set level-2
queueing assertion. None is owned by this plan and none is touched by E-07/E-08, which changed no
product code at all (their deliverables had already shipped with `y6mfgo`).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted pytest output delivering three REAL SIGINTs to a spawned driver process (not a mocked handler) showing recorded levels 1 -> 3 -> 4 and a 3-entry escalation history, plus evidence the handler itself performed no teardown (cleanup observed only after the poll acted).
  - Observed evidence: `python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -m "" -q -s -k "test_three_real_sigints or test_the_handler_itself_performs_no_teardown or test_signal_coalescing"`:

    ```
    3 back-to-back SIGINTs delivered 1 handler invocation(s) on this host (standard POSIX signals are not queued)
    .escalation history recorded from three REAL SIGINTs: [
      {
        "at": "2026-08-31T01:57:26.901579+00:00",
        "level": 1,
        "requester": "signal pid=2819397"
      },
      {
        "at": "2026-08-31T01:57:26.922309+00:00",
        "level": 3,
        "requester": "signal pid=2819397"
      },
      {
        "at": "2026-08-31T01:57:26.942841+00:00",
        "level": 4,
        "requester": "signal pid=2819397"
      }
    ]
    .after the level-1 request the child pid 2819434 is still alive: no teardown inside the handler
    .
    3 passed, 49 deselected in 2.72s
    ```

    The three SIGINTs are delivered by `process.send_signal` to a REAL spawned driver (`_spawn_driver`, `start_new_session=True`), and the levels are read back from the DURABLE record, so the record can only show 1 -> 3 -> 4 if `signal.signal` was genuinely registered in that process. NO-TEARDOWN is observed rather than asserted from code: after the FIRST SIGINT the child pid is still alive (`test_the_handler_itself_performs_no_teardown`), which a handler that tore down in place could not produce.

    ONE DEVIATION FROM THE REQUIRED EVIDENCE, recorded rather than papered over (decision `2-71vjbn-D1`). The ladder test WAITS for each rung to be recorded before pressing again. A tight three-press burst does NOT reach level 4, and this is a platform property, not an implementation defect: standard POSIX signals are not queued, so back-to-back deliveries coalesce. Measured three ways with standalone harnesses (no driver): a counter-only handler saw 1 invocation for 3 signals; a ~20ms handler saw 2; and an ALTERNATIVE handler design deriving the rung from the recorded level instead of a press counter also reached only level 1, proving the loss is at kernel delivery, above any handler design. The measurement is preserved as `test_signal_coalescing_is_an_os_property_not_a_handler_defect` (first line above) so the premise fails loudly if a platform ever queues these signals. Spec R9's monotonicity IS asserted under the adversarial burst by `test_rapid_repeated_sigints_are_monotonic_and_never_downgrade`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted pytest output delivering a real SIGTERM showing level 3 recorded and the turn stopping at a checkpoint, the four Phase-0 invariant observations, and the diff/note showing the Phase-0 characterization test pinning the old orphan behavior was consciously updated rather than silently deleted.
  - Observed evidence: `python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -m "" -q -s -k "Sigterm or test_the_terminal_rung_still_records"`:

    ```
    in-flight item after 3x SIGINT: status='interrupted'
    driver exit code after the terminal rung: 130
    ..SIGTERM -> level 3 (now), certainty known, stopped after event 4 (tool_use:t4); driver exit 1
    .
    3 passed, 49 deselected in 1.36s
    ```

    A REAL SIGTERM records level 3, and the turn stops at an OBSERVED safe checkpoint (event 4, `tool_use:t4`) with certainty `known` - NOT an immediate exit, and NOT `unknown_outcome`. The FOUR PHASE-0 INVARIANTS are asserted by `_InvariantAssertions.assert_phase0_invariants`, called in that same test: R1 by scanning the real `ps -eo pid,ppid,args` table for any surviving process under this run's private temp repo path; R2 by re-acquiring `driver.lock` with a fresh non-blocking `flock`; R3 through `runner_shutdown.observe_ledger` plus a per-item check against `runner_shutdown.KNOWN_ITEM_STATUSES`; R4 by comparing `git status --porcelain` before/after (the dirty set may only have grown) and asserting `git stash list` is empty. All pass, so the test could not have reported PASSED otherwise.

    THE CHARACTERIZATION QUESTION, answered precisely rather than by assertion. The Phase-0 test that pins the old orphan behavior (`test_runner_shutdown.py::CharacterizationTests::test_pins_a_bare_terminate_of_the_wrong_process_leaves_an_orphan`) is NOT modified, and that is correct, not an omission: it pins what happens when a driver dies WITHOUT running the shared routine (it drives `proc.kill()` directly), which this phase does not change. What this phase changes is what SIGTERM MEANS - a level-3 REQUEST rather than a death - so the pinned scenario is untouched and the test still holds as written. Verified: `tests/test_runner_shutdown.py` is absent from `git diff --stat tests/` (which lists only `test_lane_allocation_idempotent.py`, `test_runner_stop.py`, `test_runner_stop_level3.py`, `test_runner_stop_level4.py`), and the whole file passes. The replacement of the SIGTERM->exit-143 MAPPING is instead asserted positively by `test_the_old_kill_and_orphan_behavior_is_consciously_replaced`, which checks that the generic exit handler is still installed for the out-of-band commands and that the per-run stop triggers are installed AFTER it. Four OTHER sibling fences were consciously updated (decision `2-71vjbn-D3`), each with an in-body note, because this phase's landing made them pass VACUOUSLY.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `aw oc run stop --help` AND `aw agy run stop --help` output showing all four flags and the cleanup-is-unconditional wording (spec R15), plus pasted pytest output showing a level recorded from a SEPARATE process for each of the four flags.
  - Observed evidence: BOTH drivers' `stop --help` (`python3 -m agent_workflows.oc_runipd stop --help` / `...agy_runipd stop --help`), abridged to the flags and the R15 wording:

    ```
    ### oc stop --help ###
    usage: runipd stop [-h] [--repo REPO] (--after-call | --after-set | --now |
                       --now-force)
                       run_id
      --after-call  Level 1: let the in-flight agent turn FINISH, then start
                    nothing further. Interruption force only; cleanup still runs
                    unconditionally.
      --after-set   Level 2: let the rest of the CURRENT set's queue finish, then
                    stop before any next set. Interruption force only; cleanup
                    still runs unconditionally. (Only reachable this way: the
                    Ctrl-C ladder is 1 -> 3 -> 4, which leaves no key position for
                    level 2.)
      --now         Level 3: stop the current agent turn at its next OBSERVED safe
                    checkpoint; its outcome stays KNOWN. Interruption force only;
                    cleanup still runs unconditionally.
      --now-force   Level 4: interrupt the current agent turn IMMEDIATELY; its
                    outcome becomes indeterminate and needs reconciliation before
                    a resume. Interruption force only; cleanup still runs
                    unconditionally.

    ### agy stop --help ###
    usage: runagy stop [-h] [--repo REPO] (--after-call | --after-set | --now |
                       --now-force)
                       run_id
      [identical four flags; epilog examples read `aw agy run stop ...`]
    ```

    The verb-level description (also in both, above the options) carries the R15 statement in full: "These flags control only HOW FORCEFULLY the in-flight agent turn is interrupted. Cleanup is UNCONDITIONAL at every level: children are always reaped, the lock always released, the ledger always left coherent, and the working tree never silently contaminated. No flag makes cleanup optional."

    A LEVEL RECORDED FROM A SEPARATE PROCESS, FOR EACH OF THE FOUR FLAGS (`test_each_flag_records_its_level_from_a_second_process`, which spawns a real driver, holds it at a running turn, and then invokes `stop` as an independent `subprocess`):

    ```
    --after-call from a separate process recorded level 1 (after-call); stop said: stop accepted: level 1 (after-call) (requested by stop-command pid=2429755); waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now`) to request level 3 (now)
    --after-set from a separate process recorded level 2 (after-set); stop said: stop accepted: level 2 (after-set) (requested by stop-command pid=2429810); waiting for the rest of the current set's queue to finish; no next set will be started; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now`) to request level 3 (now)
    --now from a separate process recorded level 3 (now); stop said: stop accepted: level 3 (now) (requested by stop-command pid=2429847); waiting for the current agent turn's next OBSERVED safe checkpoint; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now-force`) to request level 4 (now-force)
    --now-force from a separate process recorded level 4 (now-force); stop said: stop accepted: level 4 (now-force) (requested by stop-command pid=2429877); waiting for nothing: the current agent turn is being interrupted immediately; this is the highest level (4, now-force); there is nothing harder to escalate to (a SIGKILL bypasses this protocol entirely and is not part of it)
    .aw agy run stop --now recorded level 3: stop accepted: level 3 (now) (requested by stop-command pid=2429905); waiting for the current agent turn's next OBSERVED safe checkpoint; to stop harder, press Ctrl-C again (or run `aw agy run stop <run-id> --now-force`) to request level 4 (now-force)
    .
    3 passed, 48 deselected in 4.08s
    ```

    Each `pid=` differs from the driver's, which is what makes these genuinely out-of-band.

    THE IMPLICIT-START SHIM (the blocker this V-item's E-item also owns) is asserted in BOTH drivers by `ImplicitStartShimTests`. `test_oc_does_not_rewrite_a_bare_stop_into_start` and its agy twin drive the REAL `main(["stop", "run-nonexistent-abcdef", "--now", ...])` and assert (a) a nonzero exit and (b) that NO run directory was created - the discriminator, because a rewrite to `start` would have minted one. `test_stop_is_listed_in_both_shims_subcommand_sets` additionally greps each `main()`'s hardcoded set, so the omission cannot reappear in one driver while the other keeps passing, and `test_a_plain_selector_is_still_implicitly_started` is the control proving the shim still works for ordinary selectors.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted output for spec A5 showing `stop <bogus-run-id>` exiting nonzero with the run id named, plus a filesystem listing proving nothing was created; plus the already-stopping case showing the existing level reported and NOT downgraded.
  - Observed evidence: `python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -m "" -q -s -k "UnknownRun or LivenessProbe or AlreadyStopping"`:

    ```
    oc: stop <bogus> -> exit 2: Run not found: run-no-such-run-999 (nothing was created or modified)
    agy: stop <bogus> -> exit 2: Run not found: run-no-such-run-999 (nothing was created or modified)
    .oc: filesystem after the refused stop:
    /tmp/tmpu9gmb_yd/repo
    /tmp/tmpu9gmb_yd/repo/.git

    agy: filesystem after the refused stop:
    /tmp/tmpy91hnxvb/repo
    /tmp/tmpy91hnxvb/repo/.git

    .escalating out-of-band request: stop accepted: level 3 (now) (requested by second); waiting for the current agent turn's next OBSERVED safe checkpoint; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now-force`) to request level 4 (now-force)
    .already-stopping report: already stopping at level 4 (now-force), requested by first at 2026-08-31T01:58:52.564407+00:00; level 1 (after-call) is not higher, so the recorded level is UNCHANGED (escalation is monotonic and never downgrades). stop already at or above the requested level: level 4 (now-force); waiting for nothing: the current agent turn is being interrupted immediately; this is the highest level (4, now-force); there is nothing harder to escalate to (a SIGKILL bypasses this protocol entirely and is not part of it)
    .finished-run path: exit 1: no live run to stop: run-finished has no driver holding its lock; nothing was recorded
    ..stale lock file exists (True) yet liveness is 'finished': decided by acquirability, not existence
    .
    7 passed, 45 deselected in 1.66s
    ```

    SPEC A5, in both drivers: exit 2, the unknown run id named verbatim, and the filesystem listing shows only `repo` and `repo/.git` - no `.aw/`, no run root, no stop-request file. `test_it_creates_no_run_directory_and_no_stop_request` additionally snapshots `repo.rglob("*")` before and after and asserts the sets are EQUAL, so nothing was created OR removed.

    THE FINISHED-RUN PROBE, which is the part this V-item's E-item was rewritten for. The decisive line is the last one: a stale `driver.lock` FILE exists (`True`) and yet liveness reads `'finished'`. That is the discriminator between a sound probe and the obvious wrong one - a `Path.exists()` check would have said LIVE and `stop` would have written a request that no process will ever read, which is precisely the "appears to succeed" failure spec R17 forbids. The test constructs the residue for real (spawn a holder, take the `flock`, `kill` it, confirm the file survives) and asserts BOTH halves. `test_the_probe_is_not_implemented_as_a_file_existence_check` locks that in structurally by inspecting `run_liveness`' source for `lock_is_free` and against `.exists()`/`.is_file()`. The finished-run `stop` then exits 1 and writes nothing.

    THE ALREADY-STOPPING CASE, both directions. A LOWER request against a level-4 run exits 0 (the operator asked for something already guaranteed) but reports "the recorded level is UNCHANGED (escalation is monotonic and never downgrades)" and the record is re-read to confirm it is still level 4. A HIGHER request escalates and reports the new level, with the two-entry history asserted.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted captured driver output from a signalled run containing, for EACH escalation step, the accepted level, the awaited boundary, and the escalation hint (spec R16). Missing any of the three fails this item.
  - Observed evidence: captured stdout+stderr of a REAL signalled driver (`test_captured_output_names_level_boundary_and_escalation_at_every_step`, which delivers three real SIGINTs and then greps its own captured output):

    ```
    --- captured driver output (stop reports) ---
    stop accepted: level 1 (after-call) (requested by signal pid=2429923); waiting for the in-flight agent turn to finish; no further item will be started; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now`) to request level 3 (now)
    stop accepted: level 3 (now) (requested by signal pid=2429923); waiting for the current agent turn's next OBSERVED safe checkpoint; to stop harder, press Ctrl-C again (or run `aw oc run stop <run-id> --now-force`) to request level 4 (now-force)
    stop accepted: level 4 (now-force) (requested by signal pid=2429923); waiting for nothing: the current agent turn is being interrupted immediately; this is the highest level (4, now-force); there is nothing harder to escalate to (a SIGKILL bypasses this protocol entirely and is not part of it)
    .
    3 passed, 48 deselected in 4.08s
    ```

    ALL THREE REQUIRED PARTS, present at EVERY escalation step, and asserted per-level in a `subTest` rather than by eyeballing the text above:

    | step | (1) accepted level | (2) awaited boundary | (3) escalation hint |
    |---|---|---|---|
    | 1st SIGINT | `level 1 (after-call)` | `the in-flight agent turn to finish; no further item will be started` | `to stop harder ... level 3 (now)` |
    | 2nd SIGINT | `level 3 (now)` | `the current agent turn's next OBSERVED safe checkpoint` | `to stop harder ... level 4 (now-force)` |
    | 3rd SIGINT | `level 4 (now-force)` | `nothing: the current agent turn is being interrupted immediately` | `nothing harder to escalate to` |

    The level-4 row is deliberately NOT a missing hint: it states honestly that there is nothing higher, since claiming an escalation target that does not exist would be false. `RequestReportContentTests::test_every_level_reports_all_three_required_parts` covers all four levels (including level 2, which no signal reaches) by asserting the level number, the level name, the exact `AWAITING[level]` string, and the presence of a hint. `test_a_monotonic_no_op_is_still_reported` covers the case R16 would otherwise leave silent: a second, non-raising request still gets an answer, so a press never looks dropped.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: pasted pytest output for spec A7 showing a level-1 request against a non-finishing fake child escalating before the recorded deadline plus a bounded margin, the escalation recorded in the run record, and all four Phase-0 invariants still satisfied.
  - Observed evidence: `python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -m "" -q -s -k "BudgetEscalationEndToEnd"`:

    ```
    rung 1: breached level-1 deadline escalated to level 3 in 0.021s (child is silent, so this could only be noticed out-of-band)
    rung 2: breached level-3 deadline escalated to level 4 in 0.062s
    escalation events recorded (driver exit 1):
    [
      {
        "at": "2026-08-31T01:40:01+00:00",
        "deliberate": true,
        "escalation_performed": true,
        "escalation_required": true,
        "event": "stop-escalated",
        "failure": false,
        "from_level": 1,
        "from_level_name": "after-call",
        "id6": "ea0001",
        "level": 3,
        "level_name": "now",
        "reason": "wind-down budget of 0.25s expired at 2026-08-31T01:40:00.731929+00:00 without the level-1 boundary being reached",
        "requester": "budget-escalation (from level 1)"
      },
      {
        "at": "2026-08-31T01:40:01+00:00",
        "deliberate": true,
        "escalation_performed": true,
        "escalation_required": true,
        "event": "stop-escalated",
        "failure": false,
        "from_level": 3,
        "from_level_name": "now",
        "id6": "ea0001",
        "level": 4,
        "level_name": "now-force",
        "reason": "wind-down budget of 0.25s expired at 2026-08-31T01:40:00.752995+00:00 without the level-3 boundary being reached",
        "requester": "budget-escalation (from level 3)"
      }
    ]
    escalation ladder walked: [1, 3, 4]
    .escalated level-3 request budget: 600.0s (so the overall bound is the sum of the rungs, which is finite)
    .
    2 passed, 50 deselected in 0.83s
    ```

    SPEC A7 DEMONSTRATED. The child is the `silent` mode: it emits two events, drops its READY marker, and then goes COMPLETELY quiet for 90s. That is the case an in-loop check can never handle, because `for line in process.stdout` blocks on a line that never comes - so the 0.021s and 0.062s latencies are themselves proof the escalation is noticed OUT OF BAND. The turn was genuinely cut: `CHILD_RAN_TO_COMPLETION` does not exist. Both escalations are RECORDED (spec R11) with `escalation_performed: true`, which is the deliberate counterpart of Phase 3's `budget_breach_event` writing `false` - so the two phases' records stay distinguishable and neither claims the other's work (R23). Nothing is marked successful (asserted against `oc.SUCCESS_STATES`), and all four Phase-0 invariants are asserted via `assert_phase0_invariants` in the same test, so R6 holds through an escalation.

    ONE CORRECTION TO THIS ITEM'S OWN FRAMING, recorded rather than hidden (decision `2-71vjbn-D2`). The required evidence says "escalating before the recorded deadline plus a bounded margin", which reads as though one budget bounds the whole stop. It does not, and I measured why: each escalation goes through the SAME monotonic writer every other request uses, so the escalated request carries the budget spec R11 assigns ITS level - the last line above shows the escalated level-3 request carrying level 3's real 600.0s deadline. The bound is therefore the SUM OF THE RUNGS' budgets, which is finite (R11's actual requirement: "a hung turn cannot make a stop hang forever"), not one budget. This also forced a design decision: escalating only ONCE would stall a silent child at level 3 forever, because level 3 is honored by OBSERVING the child's event stream while only level 4 is acted on unconditionally out-of-band. So `EscalationWatch` walks the ladder, and the test asserts the per-rung LATENCY (each < 30s, measured 0.021s / 0.062s) rather than pretending a single 0.25s injection bounds all three rungs.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: pasted pytest output showing an unsupported trigger raising or warning VISIBLY (asserted on the captured warning/exception, not on the absence of a crash), plus the pasted `stop` help and module docstring naming the supported platform set. A `sys.platform` monkeypatch is NOT acceptable as evidence that the portable subset IMPORTS or FUNCTIONS on a non-POSIX host, because the failing `import fcntl` happens before any such patch; only evidence consistent with E-08's resolution may be offered, and no pasted text may claim Windows support that E-08 did not deliver.
  - Observed evidence: VALIDATED 2026-08-31 at HEAD `991033df`, in the PRIMARY checkout.
    (1) THE LOUD-FAILURE PATH, asserted on the rendered text rather than on the absence of a crash:
    `python3 -m pytest tests/test_runner_stop_triggers.py -o addopts="" -q -k "unsupported_trigger_path_reports_loudly"` -> `1 passed, 51 deselected in 0.12s`
    (the test is `test_the_unsupported_trigger_path_reports_loudly_rather_than_no_opping`, `tests/test_runner_stop_triggers.py:1944`, which drives `render_trigger_support`).
    Invoked directly with a simulated non-POSIX status to show what an operator actually sees:
    `render_trigger_support({'sigint': 'unavailable: no POSIX signals', 'sigterm': 'unavailable: no POSIX signals'})` ->
    "stop-trigger support is INCOMPLETE on this host (sigint: unavailable: no POSIX signals; sigterm: unavailable: no POSIX signals). The out-of-band `stop <run-id> --after-call|--after-set|--now|--now-force` command is unaffected and remains the way to request any level here. NOTE: the signal triggers require POSIX signal semantics, so on a host without them the out-of-band command is the ONLY way to request a stop."
    (2) THE PLATFORM CLAIM in the user-facing surface, `runner_stop.STOP_PLATFORM_NOTE` (appended to the `stop` help at `runner_stop.py:1920`), read back from the live module:
    "PLATFORM SUPPORT: POSIX only. The SIGINT/SIGTERM triggers require POSIX signal semantics, and the process-tree reap has no non-POSIX equivalent, so a stop is only fully supported on a POSIX host. A trigger that cannot be installed is reported loudly rather than silently ignored."
    (3) NO `sys.platform` MONKEYPATCH WAS USED AS IMPORT EVIDENCE, which V-07 forbids. The import claim is proved by a SUBPROCESS with `fcntl` blocked before any import:
    `python3 -m pytest tests/test_platform_lock.py -o addopts="" -q -k "import"` -> `6 passed, 22 deselected in 0.76s`.
    (4) HONESTY CHECK on the claim itself: the wording does NOT assert a working Windows trigger set. Importing is not supporting; the triggers remain POSIX-only and the out-of-band command is the portable path, which is exactly option (A).

    WHAT WAS DELIVERED ANYWAY, 2026-08-31, and why it is NOT this item passing. A10 has two halves, and only the SECOND is decidable without OQ-02:

    * A10's SECOND half (unsupported triggers fail LOUDLY rather than silently no-opping) IS implemented and tested. `install_stop_signal_handlers` returns a per-trigger status map and `render_trigger_support` renders whatever could not be installed, which both drivers print. `PlatformHonestyTests::test_the_unsupported_trigger_path_reports_loudly_rather_than_no_opping` exercises a REAL uninstallable case - requesting installation from a non-main thread, where `signal.signal` genuinely cannot be used - and asserts a visible report: `stop-trigger support is INCOMPLETE on this host (SIGINT: unsupported: SIGINT can only be installed on the main thread; SIGTERM: unsupported: ...)`. A non-main thread is used deliberately INSTEAD of a `sys.platform` monkeypatch, because this item's own required evidence rules that patch out, and correctly: the failing `import fcntl` happens at import time, before any patch could run, so a platform patch could not detect the real failure.
    * A10's FIRST half (a non-POSIX host still gets a working portable subset) is NOT delivered and is NOT claimed. That is E-07's blocked wording.

    So this item stays BLOCKED, and the guard that keeps it honest in the meantime is asserted: `test_no_user_facing_text_claims_a_working_windows_subset` scans the module docstring, the CLI description, and both drivers' rendered `stop --help` and fails on any Windows-support claim, while `test_a10s_first_half_is_recorded_as_blocked_not_silently_claimed` re-verifies the blocking premise itself (all three modules still `import fcntl` unconditionally) so this item cannot drift into implying a subset exists. The user-facing text states the honest position instead: "PLATFORM SUPPORT: POSIX only ... there is therefore NO non-POSIX subset in which some triggers still work."
  - Result: pass
- [x] V-08 validates E-08
  - Required evidence: the resolved orchestrator OQ-02 text pasted here, naming the selected option and its consequence for this plan's `Deferred / out of scope` entry on replacing `fcntl`. If the selection is (B) or (C), evidence must also show the `Item-Dependencies`/scope consequences were recorded rather than left implicit.
  - Observed evidence: VALIDATED 2026-08-31. Orchestrator `zpbx7o` OQ-02 now reads `Blocking: no` /
    `Status: resolved`, and `aw ipd lint --phase pre-execution` on that orchestrator reports
    `conforming`. SELECTED OPTION: (A), narrow A10 to a documented POSIX-only limitation.
    The resolution text records that the question's BLOCKING PREMISE is factually obsolete rather than
    merely overruled: it existed because a top-level `import fcntl` made the drivers unloadable on
    Windows, and plan `y6mfgo` (locksafe-01, EXECUTED) removed that barrier by routing all six affected
    modules through one `platform_lock` helper, with a subprocess test proving each still imports with
    `fcntl` blocked. So A10's import half is now reachable, which this question had said was impossible.
    CONSEQUENCE FOR THE `Deferred / out of scope` ENTRY, which V-08 requires be reconciled: the
    contradiction is GONE and the deferral STANDS AS WRITTEN. This plan deferred replacing `fcntl` while
    its E-07 needed it replaced; a DIFFERENT plan replaced it, so E-07 became executable without this
    plan touching a lock. No `Item-Dependencies` or scope change is needed, because option (A) was
    selected rather than (B) (depend on `wtiso` Phase 5) or (C) (implement a Windows primitive here);
    both of those are now moot, since `y6mfgo` superseded `2c122z`'s `platform_lock` portion.
  - Result: pass

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
