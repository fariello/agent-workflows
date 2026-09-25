# IPD: Persist session id, cost and tokens for an interrupted execute attempt

- Date: 2026-09-25
- Kind: child
- Concern: AN INTERRUPTED EXECUTE ATTEMPT LOSES ITS SESSION ID AND ITS SPEND, ON BOTH HOSTS. Backlog `hyit04` (`bug`, `medium`, `Blocks-Release: next`): `state.json` records `"session_id": null` on an interrupted item's attempt although the attempt's session log carries a real `ses_` id, so `render_continuation_hint` (keyed on `state["set_sessions"]`) omits the Set and the `--session <id>` resume hint is unavailable for exactly the item that did not finish. Backlog `pfh5qa` (`bug`, `medium`, `Blocks-Release: next`), SAME ROOT CAUSE: `render_stream.render_run_summary_table` sums `att.get("cost")` / `att.get("tokens")` and prints `$0.00` and `-` for that item, while `aw runs` (session-log derived) prints `$2.17` / `3.62M`. ROOT CAUSE, read from the writer: in `runner_shared.execute_item_core` every write of `attempt["session_id"]`, `state["set_sessions"][setid]`, `attempt["cost"]` and `attempt["tokens"]` (the `if session_id:` block and the `extract_log_metrics(log_path)` call) sits AFTER the executor-spawn `try`, and all three turn-ending handlers on that `try` (`except runner_stop.StopNowForce`, `except runner_stop.StopAtCheckpoint`, `except StallTimeout`) `return` before reaching it; a `KeyboardInterrupt` (handler re-added by `87jnym`) likewise never reaches it. Reproduced at HEAD `8e74dcac` (F-2).
- Scope: IN: (a) one shared helper in `runner_shared` that reads the attempt's own session log (`attempt["log"]`) with the existing readers `extract_session_id` and `run_viewer.extract_log_metrics`, and writes `attempt["session_id"]`, `attempt["cost"]`, `attempt["tokens"]` and (main-tree turns only, drift-safe) `state["set_sessions"][setid]` / `state["session_id"]`; (b) call it from the three existing interrupt handlers and from the `except KeyboardInterrupt` handler `87jnym` adds, before their `save_state`; (c) behavioral tests through both hosts' real `execute_item`, including the summary table. OUT: parsing session logs in the summary table (rejected by `pfh5qa`, P8 two-derivations hazard); the verifier-turn interrupt handlers; other success-only attempt fields (`exit_code`, `ending_head`, `ending_status`, `argv`); whether spend of a POPPED clean-no-changes attempt survives (OQ-02).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_interrupt_attempt_metadata.py
- Item-Dependencies: executed:87jnym
- Status: to-review
- Work-Kind: bug
- Priority: medium
- From-Backlog: hyit04
- Blocks-Release: next
- Set: intrmeta
- Order: 1
- Highest E allocated: 05
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: zrvtm2

## Workflow history

- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog hyit04, pfh5qa; re-measured at HEAD 8e74dcac that a StallTimeout through oc `execute_item` leaves attempt session_id/cost/tokens None and set_sessions empty although the log carries all three, and that 87jnym's handler writes none of them.

## Goal

Make every interrupted execute attempt carry the session id and spend its own session log already records, so the one `state.json` ledger feeds the continuity hint, the summary table and `aw runs` consistently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one writer for interrupted-attempt accounting

- [ ] E-01 ADD `record_interrupted_attempt_accounting(state, item, attempt, work_dir)` to `agent_workflows/runner_shared.py`, near `reconcile_interrupted`. Body: `raw = attempt.get("log")`; if falsy or the file is absent, return without writing. Otherwise (1) `sid = extract_session_id(Path(raw))`; if `sid`, set `attempt["session_id"] = sid`, and only when `not work_dir and not turn_runs_in_review_sweep_lane(state, work_dir)` apply the drift-safe rule already used by `reconcile_interrupted` ("`existing in (None, session_id)`"): on agreement set `state.setdefault("set_sessions", {})[item["setid"]] = sid`, `state["session_id"] = sid`, and bump `state.setdefault("session_turn_counts", {})[sid]` by 1 (the turn DID consume a slot, matching the success path's `counts[session_id] = counts.get(session_id, 0) + 1`); on disagreement write `attempt["session_reconciliation_error"] = f"persisted={existing} observed={sid}"` and do NOT raise (the success path's `raise DriverError(... "changed session unexpectedly" ...)` must not fire from an interrupt handler, it would mask the interrupt). (2) `from agent_workflows.run_viewer import extract_log_metrics` (local import, as the success path does, so module import order is unchanged); `cost, toks = extract_log_metrics(raw)`; set `attempt["cost"]` when `cost is not None` and `attempt["tokens"]` when `toks`, identical to the success-path conditions. Wrap the whole body in `try/except Exception` that records `attempt["accounting_error"] = f"{type(exc).__name__}: {exc}"`: bookkeeping must never replace the interrupt being handled. Docstring states the P8 reason: one ledger, written from the same two readers the success path uses.
  - Depends on: none
  - Expected outcome: a pure state mutator, callable with a log path, that writes the four fields exactly as the success path would and never raises.
  - Execution state: pending

- [ ] E-02 CALL THE HELPER FROM EVERY EXECUTOR-SPAWN INTERRUPT HANDLER in `runner_shared.execute_item_core` (the inner `try:` whose body is `exit_code, session_id, log_path, argv = spawn_executor(...)`): in `except runner_stop.StopNowForce as stop:`, `except runner_stop.StopAtCheckpoint as stop:` and `except StallTimeout:`, insert `record_interrupted_attempt_accounting(state, item, attempt, work_dir)` immediately before that handler's `save_state(run_dir, state)`; in the `except KeyboardInterrupt as exc:` handler added by `87jnym` E-03, insert it BEFORE the `reconcile_item_on_interrupt(...)` call (that function persists state via `save_state_fn`, so the fields land in the same write). Change nothing else in any handler (their `return`/`raise` and status routing belong to `ccu3k7`). Do not touch the verifier `spawn_verifier(...)` handlers.
  - Depends on: E-01
  - Expected outcome: `grep -c "record_interrupted_attempt_accounting(" agent_workflows/runner_shared.py` is 5 (def plus four calls), all inside the executor-spawn `try`.
  - Execution state: pending

### Task group 2: behavioral tests

- [ ] E-03 ADD UNIT TESTS FOR THE HELPER in new `tests/test_interrupt_attempt_metadata.py`, writing real JSONL logs under a temp dir (no mocking of `extract_session_id` / `extract_log_metrics`). Log fixture: one `{"type": "step_finish", "sessionID": "ses_probe1", "part": {"cost": 2.17, "tokens": {"input": 100, "output": 20, "cache": {"read": 5, "write": 0}}}}` line. Cases: (1) `work_dir=None`, empty `set_sessions`: attempt gets `session_id == "ses_probe1"`, `cost == 2.17`, `tokens["total"] == 125`; `state["set_sessions"]["demo"] == "ses_probe1"`; `session_turn_counts["ses_probe1"] == 1`. (2) `set_sessions == {"demo": "ses_other"}`: no exception, `attempt["session_reconciliation_error"] == "persisted=ses_other observed=ses_probe1"`, `set_sessions` unchanged, cost still written. (3) `work_dir="/some/lane"`: attempt fields written, `set_sessions` untouched. (4) `attempt["log"]` pointing at a missing file: no keys added, no exception.
  - Depends on: E-01
  - Expected outcome: 4 passing tests.
  - Execution state: pending

- [ ] E-04 ADD BEHAVIORAL TESTS THROUGH EACH HOST'S REAL `execute_item` in `tests/test_interrupt_attempt_metadata.py`, parametrized over `oc_runipd` (fixtures `tests.test_oc_runipd._init_repo_with_conforming_plan` and `SelfFinalizeWiringTests._state_and_item` / `_mk_run_dir` shape) and `agy_runipd` (`tests.test_agy_runipd_cli.AgySelfFinalizeTests` equivalents), both `isolate_worktree: False`. Patch `driver_begin` to `(0, "ok")` and the host spawn (`oc_runipd.run_opencode` / `agy_runipd.run_agy_turn`) with a fake that writes the E-03 log line to `runner_shared.attempt_log_path(run_dir, item, attempt_no)` and then raises, parametrized over: `runner_shared.StallTimeout("stall")`, `runner_stop.StopNowForce()`, and `KeyboardInterrupt("clean-up-and-terminate")` (the fake also writes an untracked file into the repo so `reconcile_item_on_interrupt` keeps the attempt; wrap in `pytest.raises(KeyboardInterrupt)`). Assert, for each: `item["attempts"][-1]` has `session_id == "ses_probe1"`, `cost == 2.17`, `tokens["total"] == 125`; the persisted `run_dir / "state.json"` agrees; `state["set_sessions"]["demo"] == "ses_probe1"`; `runner_shared.render_continuation_hint(...)` output (called with the host's `labels`) contains `ses_probe1`; and `render_stream.render_run_summary_table(state, run_dir)` output contains `2.17` for the row. `StopAtCheckpoint` is exercised only if a `CheckpointObserver` can be built without a live stream; otherwise it is covered by E-02's grep and stated so in V-04.
  - Depends on: E-02, E-03
  - Expected outcome: 6 passing tests (2 hosts x 3 raises); each FAILS with E-02's calls removed (attempt `session_id` None, table `$0.00`), which is the measured HEAD behavior.
  - Execution state: pending

- [ ] E-05 RUN THE BARE SUITE `python3 -m pytest` (no extra flags); in particular `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py` and `87jnym`'s `tests/test_interrupt_reconcile.py` must stay green.
  - Depends on: E-04
  - Expected outcome: the bare suite summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE SHARED CORE: both hosts' `execute_item` delegate the executor spawn and its exception handlers to `runner_shared.execute_item_core`, so the fix lands once. Both hosts' spawns write the executor log at `attempt_log_path(run_dir, item, attempt_no, suffix="")`, which is exactly the `attempt["log"]` value `execute_item_core` records at attempt creation.
- ONE LEDGER (P8): `pfh5qa` forbids a second cost derivation in the table; `run_analytics_sources` already "prefer[s] a stored `attempt["cost"]`/`attempt["tokens"]`, fall back to `extract_log_metrics`", so writing the stored field makes every surface agree.
- DRIFT RULE ON RECOVERY PATHS RECORDS, NEVER RAISES: `reconcile_interrupted` writes `session_reconciliation_error` on a set-session mismatch; the helper copies that rule.
- Behavioral tests only, no source-text pins (the `87jnym` history shows a substring guard satisfied by a docstring).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.execute_item_core` | The only writers of `attempt["session_id"]`, `set_sessions`, `attempt["cost"]`, `attempt["tokens"]` for an execute turn follow the spawn `try`; all three handlers `return` first. Attempt is born `"session_id": None`. | `grep -n` at HEAD `8e74dcac`: `attempt["session_id"] = session_id` near :26315, `state["set_sessions"][item["setid"]] = session_id` near :26344, `attempt["cost"] = att_cost` near :26363; handlers near :26222-26312 each end `return` |
| F-2 | HIGH | both hosts | Reproduced: oc `execute_item` with a spawn that writes a `ses_probe1`/`cost 2.17` log then raises `StallTimeout` ends `status interrupted session_id None cost None tokens None set_sessions {}`. | probe `/tmp/opencode/g3/probe-intrmeta/p.py` output |
| F-3 | HIGH | `87jnym` E-03 | Its new `except KeyboardInterrupt` handler calls only `reconcile_item_on_interrupt`, whose body writes status/events/`interrupt_reason`, never session or spend. So `87jnym` does NOT cover these items. | `87jnym` E-01..E-06 text; no `session_id`/`cost`/`tokens` write in `reconcile_item_on_interrupt` (`grep` of its body) |
| F-4 | MED | `render_stream.render_run_summary_table` | Reads `att.get("cost")` / `att.get("tokens")` only; correct once the ledger is written, so no renderer change is needed. | `c = att.get("cost")`, `toks = att.get("tokens") or {}` |
| F-5 | MED | `runner_shared.render_continuation_hint` | Keyed on `state.get("set_sessions", {})`; the interrupted Set is absent because nothing wrote it. | `sessions = state.get("set_sessions", {})` |
| F-6 | INFO | `reconcile_interrupted` | A driver CRASH (item left `running`) already recovers `session_id` from the log on the next resume, but not cost/tokens, and an interrupt that sets `interrupted` is skipped by its `if item["status"] != "running": continue`. | `session_id = extract_session_id(Path(raw_log)) if raw_log else None` |

## Proposed changes (ordered, validatable)

1. E-01: shared helper reading the attempt log with the two existing readers, drift-safe, never raising.
2. E-02: call it in the four executor-spawn interrupt handlers before their state write.
3. E-03: helper unit tests against real logs.
4. E-04: host-parametrized `execute_item` tests incl. continuity hint and summary table.
5. E-05: bare suite.

## Deferred / out of scope (with reason)

- Verifier-turn interrupts (`spawn_verifier(...)` `except StallTimeout` / `StopAtCheckpoint`): they would need `verification_cost` / `verification_tokens`, keys the success path itself does not write today (`grep` finds none in `runner_shared.py`), so there is no success-path contract to mirror.
  - Carrier-Declined: no measured symptom; the backlog items measured an execute-turn interrupt only.
- Other success-only attempt fields (`exit_code`, `ending_head`, `ending_branch`, `ending_status`, `argv`) that `hyit04` asked to check: confirmed also absent on the interrupt paths, but none feeds continuity or spend, and `exit_code` has no honest value for a killed child.
  - Carrier-Declined: checked per hyit04's request; no consumer shows a wrong value from their absence.
- Refreshing cost/tokens in `reconcile_interrupted` for a crashed (`running`) item.
  - Carrier-Declined: not the measured path; a crash leaves the item `running` and the success-path readers can be reused there later if a symptom is measured.

## Scope check

- Over-scope: none. One new helper and four one-line calls in `runner_shared.py`, one new test file.
- Under-scope: the `KeyboardInterrupt` call site does not exist until `87jnym` lands, hence `Item-Dependencies: executed:87jnym`. If `ccu3k7` rewrites the sibling handlers first, re-read the `try` and place each call before that handler's state write.

## Required tests / validation

- `python3 -m pytest tests/test_interrupt_attempt_metadata.py -o addopts="" -v` pasted, all passing.
- Mutation: E-02 calls removed -> E-04 tests FAIL on `session_id`/`2.17`; restored after.
- `git diff --stat` limited to the two Scope-Paths.
- Bare `python3 -m pytest` summary line.

## Spec / documentation sync

- N/A: no `.spec.md` specifies the per-attempt `cost`/`tokens`/`session_id` keys on interrupt paths (`grep -rln "set_sessions" .aw/records/specs/` returns none relevant). The helper's docstring carries the rationale.

## Open questions

### OQ-01: Should a killed attempt's spend count in the run total (pfh5qa's question)?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: Resolved as COUNT IT. `pfh5qa` states printing `$0.00` "is the one option that is not" defensible, and counting is the only option achievable without a new "excluded" label on the table; the summary table already sums every attempt, so writing the field makes the total include it. A maintainer who prefers exclude-with-label can file that as a follow-up; nothing here blocks it.
- Carrier-Declined: resolved from the backlog's own ruling text.

### OQ-02: A clean-tree `KeyboardInterrupt` pops the attempt (`87jnym` E-02), taking its recorded spend with it. Preserve it?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: accept for this plan. The session id still reaches `set_sessions` (written on `state`, not the popped attempt), which fully fixes `hyit04`; only the spend of an attempt that changed nothing disappears, matching `reconcile_item_on_interrupt`'s "as if it never ran before" contract. If the maintainer wants that spend kept, the follow-up is to move the popped attempt's `cost`/`tokens` onto an item-level `discarded_attempts` list the table also sums.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the diff adding `record_interrupted_attempt_accounting` showing the `existing in (None, sid)` drift rule, the `session_reconciliation_error` write, the local `extract_log_metrics` import, and the outer `except Exception` recording `accounting_error`; plus `python3 -c "from agent_workflows import runner_shared as r; print(callable(r.record_interrupted_attempt_accounting))"` printing `True`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted `grep -n "record_interrupted_attempt_accounting(" agent_workflows/runner_shared.py` showing the def plus exactly four calls, each inside the executor-spawn handlers (`StopNowForce`, `StopAtCheckpoint`, `StallTimeout`, `KeyboardInterrupt`), and `git diff` showing no other line of those handlers changed.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `python3 -m pytest tests/test_interrupt_attempt_metadata.py -o addopts="" -v -k helper` (or the actual names) showing the four helper tests passing, and a test-source excerpt showing real JSONL files and no patching of the two readers.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tests/test_interrupt_attempt_metadata.py -o addopts="" -v` listing the six host x raise tests passing; then the four E-02 calls temporarily removed and the same run pasted with those six FAILING (session_id None / `2.17` absent), then restored. State whether `StopAtCheckpoint` was exercised behaviorally or only by V-02.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the pasted summary line of a bare `python3 -m pytest` run, showing 0 failed.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution, and must run after `87jnym` is executed. The executor commits only the Scope-Paths via `aw commit <plan> -- agent_workflows/runner_shared.py tests/test_interrupt_attempt_metadata.py`, never pushes, and pastes actual runner output including the mutation run. STOP and report if a call site requires changing a handler's return/raise or status routing. Before the terminal transition `aw ipd lint --phase pre-transition` must conform and every `V-*` carry observed evidence; the runner owns that transition in a managed lane, otherwise `aw ipd finalize`. On execution, close `pfh5qa` alongside `hyit04` via this plan's handoff.
