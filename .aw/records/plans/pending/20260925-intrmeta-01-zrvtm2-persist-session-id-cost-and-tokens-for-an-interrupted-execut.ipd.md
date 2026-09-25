# IPD: Persist session id, cost and tokens for an interrupted execute attempt

- Date: 2026-09-25
- Kind: child
- Concern: AN INTERRUPTED EXECUTE ATTEMPT LOSES ITS SESSION ID AND ITS SPEND, ON BOTH HOSTS. Backlog `hyit04` (`bug`, `medium`, `Blocks-Release: next`): `state.json` records `"session_id": null` on an interrupted item's attempt although the attempt's session log carries a real `ses_` id, so `render_continuation_hint` (keyed on `state["set_sessions"]`) omits the Set and the `--session <id>` resume hint is unavailable for exactly the item that did not finish. Backlog `pfh5qa` (`bug`, `medium`, `Blocks-Release: next`), SAME ROOT CAUSE: `render_stream.render_run_summary_table` sums `att.get("cost")` / `att.get("tokens")` and prints `$0.00` and `-` for that item, while `aw runs` (session-log derived) prints `$2.17` / `3.62M`. ROOT CAUSE, read from the writer: in `runner_shared.execute_item_core` every write of `attempt["session_id"]`, `state["set_sessions"][setid]`, `attempt["cost"]` and `attempt["tokens"]` (the `if session_id:` block and the `extract_log_metrics(log_path)` call) sits AFTER the executor-spawn `try`, and all three turn-ending handlers on that `try` (`except runner_stop.StopNowForce`, `except runner_stop.StopAtCheckpoint`, `except StallTimeout`) `return` before reaching it; a `KeyboardInterrupt` (handler re-added by `87jnym`) likewise never reaches it. Reproduced at HEAD `8e74dcac` (F-2).
- Scope: IN: (a) one shared helper in `runner_shared` that reads the attempt's own session log (`attempt["log"]`) with the existing readers `extract_session_id` and `run_viewer.extract_log_metrics`, and writes `attempt["session_id"]`, `attempt["cost"]`, `attempt["tokens"]` and (main-tree turns only, drift-safe) `state["set_sessions"][setid]` / `state["session_id"]`; (b) call it from the three existing interrupt handlers and from the `except KeyboardInterrupt` handler `87jnym` adds, before their `save_state`; (c) behavioral tests through both hosts' real `execute_item`, including the summary table. OUT: parsing session logs in the summary table (rejected by `pfh5qa`, P8 two-derivations hazard); the verifier-turn interrupt handlers; other success-only attempt fields (`exit_code`, `ending_head`, `ending_status`, `argv`); whether spend of a POPPED clean-no-changes attempt survives (OQ-02).
- Scope-Paths: agent_workflows/runner_shared.py, tests/test_interrupt_attempt_metadata.py
- Item-Dependencies: executed:87jnym
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: hyit04
- Blocks-Release: next
- Set: intrmeta
- Order: 1
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: zrvtm2
- Approval: 2026-09-25, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-09-25 approved (aw set): status set to approved
- 2026-09-25 reviewed (aw set): status set to reviewed

- 2026-09-25 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-101..PR-107 all FIXED, no deferrals, OQ-01 resolved and OQ-02 sharpened (non-blocking). Re-reproduced F-2 on all FOUR interrupt paths against the real `oc_runipd.execute_item`. Removed the proposed `session_turn_counts` bump (the counter is the session-rotation trigger and the cited precedent does not bump it); corrected E-04's `render_continuation_hint` call, which omitted the required positional `run_dir` and raises `TypeError` as authored; showed `StopAtCheckpoint` IS constructible without a live stream so all four raises are testable (6 tests -> 8); added E-05 pinning the exclusive-precedence no-double-count property the whole fix rests on; corrected the verifier Deferred reason (the success path DOES write `verify_cost`/`verify_tokens`) and recorded F-7, that the summary table reads the misnamed `verification_cost`; strengthened F-3 to state that the `KeyboardInterrupt` call site does not exist at all and `87jnym` is approved-but-unexecuted; rewrote the gate with a scope fence, honesty rule and two stop conditions. Split E-01 per the size advisory; E/V renumbered to E-01..E-07 / V-01..V-07.
- 2026-09-25 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog hyit04, pfh5qa; re-measured at HEAD 8e74dcac that a StallTimeout through oc `execute_item` leaves attempt session_id/cost/tokens None and set_sessions empty although the log carries all three, and that 87jnym's handler writes none of them.

## Goal

Make every interrupted execute attempt carry the session id and spend its own session log already records, so the one `state.json` ledger feeds the continuity hint, the summary table and `aw runs` consistently.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: one writer for interrupted-attempt accounting

- [ ] E-01 ADD `record_interrupted_attempt_accounting(state, item, attempt, work_dir)` to `agent_workflows/runner_shared.py`, near `reconcile_interrupted`, writing the ATTEMPT-LOCAL fields only. Body: `raw = attempt.get("log")`; if falsy or the file is absent, return without writing. Otherwise (1) `sid = extract_session_id(Path(raw))` and, if `sid`, set `attempt["session_id"] = sid`; (2) `from agent_workflows.run_viewer import extract_log_metrics` (local import, as the success path does at `from agent_workflows.run_viewer import extract_log_metrics` inside `execute_item_core`, so module import order is unchanged); `cost, toks = extract_log_metrics(raw)`; set `attempt["cost"]` when `cost is not None` and `attempt["tokens"]` when `toks`, identical to the success-path conditions. Wrap the whole body in `try/except Exception` recording `attempt["accounting_error"] = f"{type(exc).__name__}: {exc}"`: bookkeeping must never replace the interrupt being handled. Docstring states the P8 reason (one ledger, read by the same two readers the success path uses) AND the measured precedence fact that makes this safe: `run_viewer.extract_step_usage` prefers a stored `attempt["cost"]`/`attempt["tokens"]` in an exclusive `if/else` and falls back to the log ONLY when both are absent, so writing the field cannot double-count.
  - Depends on: none
  - Expected outcome: a pure attempt mutator that writes `session_id`, `cost` and `tokens` exactly as the success path would, touches no `state` key, and never raises.
  - Execution state: pending

- [ ] E-02 EXTEND THE SAME HELPER WITH THE STATE-LEVEL SESSION WRITE, kept separate from E-01 because it is the only part that mutates shared run state and the only part with a drift rule. Only when `not work_dir and not turn_runs_in_review_sweep_lane(state, work_dir)` and a `sid` was observed, apply the drift-safe rule `reconcile_interrupted` already uses (`existing in (None, session_id)`): on agreement set `state.setdefault("set_sessions", {})[item["setid"]] = sid` and `state["session_id"] = sid`; on disagreement write `attempt["session_reconciliation_error"] = f"persisted={existing} observed={sid}"` and do NOT raise (the success path's `raise DriverError(... "changed session unexpectedly" ...)` must not fire from an interrupt handler, where it would mask the interrupt being handled). DO NOT bump `session_turn_counts`, which the authored plan proposed: `reconcile_interrupted`, the existing recovery-path precedent this helper copies, deliberately does NOT bump it, and the counter is READ as the session-rotation trigger (`session_turns >= max_items` in `execute_item_core` and again in `oc_runipd.run_opencode`), so incrementing it on an interrupt would make a killed turn consume a rotation slot and could rotate the session a resume is trying to reuse. If a later measurement shows a killed turn must consume a slot, that is a separate change with its own evidence.
  - Depends on: E-01
  - Expected outcome: `set_sessions` written for a main-tree turn, untouched for a lane turn, and a mismatch recorded rather than raised; `session_turn_counts` unchanged on every path.
  - Execution state: pending

- [ ] E-03 CALL THE HELPER FROM EVERY EXECUTOR-SPAWN INTERRUPT HANDLER in `runner_shared.execute_item_core` (the inner `try:` whose body is `exit_code, session_id, log_path, argv = spawn_executor(...)`): in `except runner_stop.StopNowForce as stop:`, `except runner_stop.StopAtCheckpoint as stop:` and `except StallTimeout:`, insert `record_interrupted_attempt_accounting(state, item, attempt, work_dir)` immediately before that handler's `save_state(run_dir, state)`; in the `except KeyboardInterrupt as exc:` handler `87jnym` adds, insert it BEFORE the `reconcile_item_on_interrupt(...)` call (that function persists state via `save_state_fn`, so the fields land in the same write). Change nothing else in any handler (their `return`/`raise` and status routing belong to `ccu3k7`). Do not touch the verifier `spawn_verifier(...)` handlers. VERIFY THE KeyboardInterrupt CALL SITE EXISTS FIRST: at the time of review there is NO `except KeyboardInterrupt` anywhere in `execute_item_core` (`grep -n "except KeyboardInterrupt" agent_workflows/runner_shared.py` returns only comment lines and `run_queue`'s own handler), and `reconcile_item_on_interrupt` has ZERO callers, which is exactly the defect `87jnym` fixes. If that handler is still absent when this plan runs, `87jnym` has not executed and the declared `executed:87jnym` dependency was not honored: stop and report rather than adding the handler here, which would duplicate `87jnym`'s own scope.
  - Depends on: E-02
  - Expected outcome: `grep -c "record_interrupted_attempt_accounting(" agent_workflows/runner_shared.py` is 5 (def plus four calls), all inside the executor-spawn `try`.
  - Execution state: pending

### Task group 2: tests

- [ ] E-04 ADD UNIT TESTS FOR THE HELPER in new `tests/test_interrupt_attempt_metadata.py`, writing real JSONL logs under a temp dir (no mocking of `extract_session_id` / `extract_log_metrics`). Log fixture: one `{"type": "step_finish", "sessionID": "ses_probe1", "part": {"cost": 2.17, "tokens": {"input": 100, "output": 20, "cache": {"read": 5, "write": 0}}}}` line; BOTH readers were driven against exactly this line at review and returned `ses_probe1` and `(2.17, {'total': 125, 'input': 100, 'output': 20, 'cache': 5})`, so assert `tokens["total"] == 125` and do NOT assert a `reasoning` key, which this fixture does not produce. Cases: (1) `work_dir=None`, empty `set_sessions`: attempt gets `session_id == "ses_probe1"`, `cost == 2.17`, `tokens["total"] == 125`; `state["set_sessions"]["demo"] == "ses_probe1"`; and `state.get("session_turn_counts", {})` is UNCHANGED (assert this positively, since E-02 deliberately does not bump it). (2) `set_sessions == {"demo": "ses_other"}`: no exception, `attempt["session_reconciliation_error"] == "persisted=ses_other observed=ses_probe1"`, `set_sessions` unchanged, cost still written. (3) `work_dir="/some/lane"`: attempt fields written, `set_sessions` untouched. (4) `attempt["log"]` pointing at a missing file: no keys added, no exception. (5) `attempt` with no `"log"` key at all: same, no exception.
  - Depends on: E-02
  - Expected outcome: 5 passing tests.
  - Execution state: pending

- [ ] E-05 ADD A NO-DOUBLE-COUNT TEST for the precedence claim the fix rests on, in the same file. Call `run_viewer.extract_step_usage` on one item twice: once with an attempt carrying ONLY `log` (today's interrupted shape) and once with the same attempt ALSO carrying `cost`/`tokens` (the post-fix shape), and assert the two results are EQUAL. Measured at review, both return `(2.17, {...'total': 125...}, 2.17, {...}, None, {})`, because `extract_step_usage` reads the stored fields in an exclusive `if/else` that falls back to the log only when both are absent. This is the one assertion that proves the fix cannot inflate `aw runs`, which the authored plan asserted in prose and never tested; it is also the test that would catch a future refactor turning that `if/else` into two additive branches.
  - Depends on: E-01
  - Expected outcome: 1 passing test showing byte-equal usage tuples before and after the stored fields exist.
  - Execution state: pending

- [ ] E-06 ADD BEHAVIORAL TESTS THROUGH EACH HOST'S REAL `execute_item` in `tests/test_interrupt_attempt_metadata.py`, parametrized over `oc_runipd` (fixtures `tests.test_oc_runipd._init_repo_with_conforming_plan` and the `SelfFinalizeWiringTests._state_and_item` / `_mk_run_dir` SHAPE, which must also create `sessions/` since those fixtures create only `outcomes/` and `prompts/`) and `agy_runipd` (`tests.test_agy_runipd_cli._init_repo_with_conforming_plan` plus its `AgySelfFinalizeTests` equivalents), both `isolate_worktree: False` and `self_finalize: False`, `no_audit: True`. Patch `driver_begin` to `(0, "ok")` and the host spawn (`oc_runipd.run_opencode` / `agy_runipd.run_agy_turn`) with a fake that writes the E-04 log line to `runner_shared.attempt_log_path(run_dir, item, attempt_no)` and then raises, parametrized over ALL FOUR: `runner_shared.StallTimeout("stall")`, `runner_stop.StopNowForce()`, `runner_stop.StopAtCheckpoint(runner_stop.CheckpointObserver(detector=lambda s: False, last_checkpoint_label="E-01"))`, and `KeyboardInterrupt("clean-up-and-terminate")` (for the last, the fake also writes an untracked file into the repo so `reconcile_item_on_interrupt` keeps the attempt; wrap in `pytest.raises(KeyboardInterrupt)`). Assert, for each: `item["attempts"][-1]` has `session_id == "ses_probe1"`, `cost == 2.17`, `tokens["total"] == 125`; the persisted `run_dir / "state.json"` agrees; `state["set_sessions"]["demo"] == "ses_probe1"`; `render_stream.render_run_summary_table(state, run_dir)` output contains `2.17` for the row. Call the hint as `runner_shared.render_continuation_hint(state, run_dir, labels=<host labels>)` and assert it contains `ses_probe1`: the signature is `(state, run_dir, driver_cmd=None, *, labels)`, `run_dir` is REQUIRED POSITIONALLY and `labels` is KEYWORD-ONLY, so the authored phrasing "called with the host's `labels`" omits a required argument and a literal reading raises `TypeError` (hit at review). Do NOT assert an exact item `status`: measured at review, the four raises end `interrupted`, `unknown_outcome`, `interrupted` and `running` respectively, so a single expected status would be wrong for three of them and status routing is `ccu3k7`'s, not this plan's.
  - Depends on: E-03, E-04
  - Expected outcome: 8 passing tests (2 hosts x 4 raises); each FAILS with E-03's calls removed (attempt `session_id` None, table `$0.00`), which is the measured HEAD behavior.
  - Execution state: pending

- [ ] E-07 RUN THE BARE SUITE `python3 -m pytest` (no extra flags; `addopts` already supplies `-q -n auto --dist=worksteal` and the marker deselection, so do NOT add `-n0`, a second `-q`, or `-p no:randomly`); in particular `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py` and `87jnym`'s `tests/test_interrupt_reconcile.py` must stay green.
  - Depends on: E-06, E-05
  - Expected outcome: the bare suite summary line shows 0 failed.
  - Execution state: pending

## Project conventions discovered (Step 0)

- ONE SHARED CORE: both hosts' `execute_item` delegate the executor spawn and its exception handlers to `runner_shared.execute_item_core`, so the fix lands once. Both hosts' spawns write the executor log at `attempt_log_path(run_dir, item, attempt_no, suffix="")`, which is exactly the `attempt["log"]` value `execute_item_core` records at attempt creation.
- ONE LEDGER (P8): `pfh5qa` forbids a second cost derivation in the table; `run_analytics_sources` already "prefer[s] a stored `attempt["cost"]`/`attempt["tokens"]`, fall back to `extract_log_metrics`", so writing the stored field makes every surface agree. VERIFIED AT REVIEW that the precedence is EXCLUSIVE, not additive: `run_viewer.extract_step_usage` reads `att.get("cost")`/`att.get("tokens")` in an `if ... else` whose else-branch reads the log, and driving it on one item with and without the stored fields returned IDENTICAL tuples. So the fix provably cannot inflate `aw runs` (E-05 pins this).
- DRIFT RULE ON RECOVERY PATHS RECORDS, NEVER RAISES: `reconcile_interrupted` writes `session_reconciliation_error` on a set-session mismatch; the helper copies that rule. It also does NOT bump `session_turn_counts`, and that omission is deliberate rather than incidental: the counter is READ as the session-rotation trigger (`session_turns >= max_items`, in both `execute_item_core` and `oc_runipd.run_opencode`), so a bump on an interrupt would let a killed turn consume a rotation slot.
- `attempt["log"]` IS AVAILABLE TO EVERY HANDLER, which is what makes this fix possible at all: it is written at attempt CREATION (`"log": str(attempt_log_path(run_dir, item, attempt_no))` in the attempt dict literal), not in the post-spawn `attempt.update({...})`. Both hosts' spawns write the executor log to that same path (`attempt_log_path(run_dir, item, attempt_no, suffix=log_suffix)` with an empty suffix for an executor turn).
- THE ATTEMPT RECORD'S NUMBER KEY IS `"number"`, NOT `"attempt"`. `reconcile_item_on_interrupt`'s no-changes arm pops on `attempts[-1].get("attempt") == attempt_no`, which is never true against a real attempt dict, so at review the pop does NOT fire; `87jnym` clause (c) fixes exactly that. This is why OQ-02 is a real question only AFTER `87jnym` lands.
- `runner_shared.render_continuation_hint(state, run_dir, driver_cmd=None, *, labels)` takes `run_dir` POSITIONALLY and `labels` KEYWORD-ONLY. `render_stream.render_run_summary_table(state, run_dir=None, ...)` takes the rest optional.
- `runner_stop.StopAtCheckpoint` requires an observer, and one is constructible without a live stream: `CheckpointObserver(detector=lambda s: False, last_checkpoint_label="E-01")`. So all four interrupt paths are testable behaviorally and none needs a grep-only substitute.
- Behavioral tests only, no source-text pins (the `87jnym` history shows a substring guard satisfied by a docstring).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `runner_shared.execute_item_core` | The only writers of `attempt["session_id"]`, `set_sessions`, `attempt["cost"]`, `attempt["tokens"]` for an execute turn follow the spawn `try`; all three handlers `return` first. Attempt is born `"session_id": None`. Re-verified at review by content, not offset. | Quoted writers, all AFTER the `exit_code, session_id, log_path, argv = spawn_executor(` call: `attempt["session_id"] = session_id`, `state["set_sessions"][item["setid"]] = session_id`, `attempt["cost"] = att_cost`, `attempt["tokens"] = att_toks`. The attempt dict literal carries `"session_id": None` and `"log": str(attempt_log_path(run_dir, item, attempt_no))`. Each of `except runner_stop.StopNowForce as stop:`, `except runner_stop.StopAtCheckpoint as stop:` and `except StallTimeout:` ends in `return` after its own `save_state(run_dir, state)` |
| F-2 | HIGH | both hosts | RE-REPRODUCED AT REVIEW on all FOUR paths, driving the real `oc_runipd.execute_item` with a spawn that writes a `ses_probe1`/`cost 2.17` log then raises. Every one ends `sid=None cost=None tok=None set_sessions={}` while the SAME log yields `ses_probe1` and `(2.17, total 125)`; the summary table printed `$0.00` and `-`. Statuses differ per path: `StallTimeout`->`interrupted`, `StopNowForce`->`unknown_outcome`, `StopAtCheckpoint`->`interrupted`, `KeyboardInterrupt`->`running` (raised out). | review probe output, four `[label] ... sid=None cost=None` lines plus the rendered table row |
| F-3 | HIGH | `87jnym`, and its call site does not exist yet | `reconcile_item_on_interrupt` writes status/events/`interrupt_reason` and never session or spend, so `87jnym` does not cover these items. STRONGER THAN THE PLAN STATED: at review `execute_item_core` has NO `except KeyboardInterrupt` at all and `reconcile_item_on_interrupt` has ZERO callers, so E-03's fourth call site is created by `87jnym` and this plan cannot run before it. `87jnym` is `- Status: approved` and still in `pending/`, i.e. NOT executed. | `grep -rn "reconcile_item_on_interrupt" agent_workflows/ tests/` -> one def, one comment, no call; `grep -n "except KeyboardInterrupt" agent_workflows/runner_shared.py` -> comments plus `run_queue` only; `87jnym` front matter |
| F-4 | MED | `render_stream.render_run_summary_table` | Reads `att.get("cost")` / `att.get("tokens")` only; correct once the ledger is written, so no renderer change is needed. Confirmed by the review probe printing `$0.00` with a populated log and by the exclusive-precedence measurement showing no double count. | `c = att.get("cost")`, `toks = att.get("tokens") or {}` |
| F-5 | MED | `runner_shared.render_continuation_hint` | Keyed on `state.get("set_sessions", {})`; the interrupted Set is absent because nothing wrote it. | `sessions = state.get("set_sessions", {})` |
| F-6 | INFO | `reconcile_interrupted` | A driver CRASH (item left `running`) already recovers `session_id` from the log on the next resume, but not cost/tokens, and an interrupt that sets `interrupted` is skipped by its `if item["status"] != "running": continue`. | `session_id = extract_session_id(Path(raw_log)) if raw_log else None` |
| F-7 | LOW | `render_stream.render_run_summary_table` verification keys | The table reads `att.get("verification_cost")` and `att.get("verification_tokens")`, but the verifier success path writes `attempt["verify_cost"]` / `attempt["verify_tokens"]`, and `verify_*` is the name every other consumer uses (`run_viewer.extract_step_usage`, `run_analytics*`). So those two table reads are DEAD and verifier spend never reaches the summary table on ANY path, interrupted or not. OUT OF SCOPE here (this plan's Scope-Paths exclude `render_stream.py` and the defect is independent of interrupts), but it is the reason the Deferred note on verifier interrupts must not say "no consumer exists": a consumer exists and is misnamed. | `grep -rn "verification_cost\|verification_tokens" agent_workflows/` -> only the two `render_stream` reads; `grep -rn "verify_cost"` -> the writer plus `run_viewer`/`run_analytics` readers |

## Proposed changes (ordered, validatable)

1. E-01: shared helper writing the ATTEMPT-local fields from the two existing readers, never raising.
2. E-02: the same helper's state-level session write, drift-safe, with no `session_turn_counts` bump.
3. E-03: call it in the four executor-spawn interrupt handlers before their state write.
4. E-04: helper unit tests against real logs.
5. E-05: the no-double-count test pinning the exclusive precedence the fix relies on.
6. E-06: host-parametrized `execute_item` tests over all four raises, incl. continuity hint and summary table.
7. E-07: bare suite.

## Deferred / out of scope (with reason)

- Verifier-turn interrupts (`spawn_verifier(...)` `except StallTimeout` / `StopNowForce` / `StopAtCheckpoint`). CORRECTED AT REVIEW, because the authored reason was factually wrong and would mislead whoever picks this up: the verifier SUCCESS path DOES write accounting, as `attempt["verify_cost"]` / `attempt["verify_tokens"]` from `extract_log_metrics(_v_log)`, so a success-path contract to mirror exists and a verifier interrupt genuinely loses that spend. The separate reason it is still deferred: the summary table reads the MISNAMED `verification_cost` / `verification_tokens` (F-7), so verifier spend reaches the table on NO path today, and fixing the interrupt half while the reader is misnamed would produce a correct ledger no table surfaces. That reader fix touches `render_stream.py`, which this plan does not declare.
  - Carrier-Declined: no measured symptom (both backlog items measured an execute-turn interrupt only), and the dependent reader defect F-7 must be resolved first for a verifier fix to be observable. Worth a backlog item; deliberately not filed by this review, since a review must not create the work it then cites.
- Other success-only attempt fields (`exit_code`, `ending_head`, `ending_branch`, `ending_status`, `argv`) that `hyit04` asked to check: confirmed also absent on the interrupt paths, but none feeds continuity or spend, and `exit_code` has no honest value for a killed child.
  - Carrier-Declined: checked per hyit04's request; no consumer shows a wrong value from their absence.
- Refreshing cost/tokens in `reconcile_interrupted` for a crashed (`running`) item.
  - Carrier-Declined: not the measured path; a crash leaves the item `running` and the success-path readers can be reused there later if a symptom is measured.

## Scope check

- Over-scope: none. One new helper and four one-line calls in `runner_shared.py`, one new test file.
- Under-scope: the `KeyboardInterrupt` call site does not exist until `87jnym` lands, hence `Item-Dependencies: executed:87jnym`. CONFIRMED AT REVIEW that this is a hard prerequisite and not a nicety: `execute_item_core` has no `except KeyboardInterrupt` at all and `reconcile_item_on_interrupt` has zero callers, so three of E-03's four call sites exist today and the fourth does not. `87jnym` is `approved` but still in `pending/`. E-03 therefore carries a stop condition rather than authorizing this plan to add the handler, which is `87jnym`'s declared scope (its clause (a)). If `ccu3k7` rewrites the sibling handlers first, re-read the `try` and place each call before that handler's state write.

## Required tests / validation

- `python3 -m pytest tests/test_interrupt_attempt_metadata.py -o addopts="" -v` pasted, all passing.
- Mutation: E-03's four calls removed -> E-06's eight tests FAIL on `session_id`/`2.17`; restored after. The mutation must be shown, not asserted: it is the only evidence distinguishing "the fix works" from "the test asserts something already true", and the HEAD behavior it should reproduce was measured at review on all four raises.
- The no-double-count equality from E-05, pasted as two tuples.
- `git diff --stat` limited to the two Scope-Paths.
- Bare `python3 -m pytest` summary line.

## Spec / documentation sync

- N/A: no `.spec.md` specifies the per-attempt `cost`/`tokens`/`session_id` keys on interrupt paths (`grep -rln "set_sessions" .aw/records/specs/` returns nothing, re-run at review). The helper's docstring carries the rationale, including the measured exclusive-precedence fact that makes writing the field safe. No `.spec.md` appears in `- Scope-Paths:`, so the runners will announce no declared spec edit for this plan, which is correct.

## Open questions

### OQ-01: Should a killed attempt's spend count in the run total (pfh5qa's question)?

- Blocking: no
- Status: resolved
- Owner: this plan's executor
- Resolution or deferral rationale: Resolved as COUNT IT. `pfh5qa` states printing `$0.00` "is the one option that is not" defensible, and counting is the only option achievable without a new "excluded" label on the table; the summary table already sums every attempt, so writing the field makes the total include it. A maintainer who prefers exclude-with-label can file that as a follow-up; nothing here blocks it.
- Carrier-Declined: resolved from the backlog's own ruling text.

### OQ-02: A clean-tree `KeyboardInterrupt` pops the attempt, taking its recorded spend with it. Preserve it?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Default: accept for this plan. The session id still reaches `set_sessions` (written on `state`, not the popped attempt), which fully fixes `hyit04`; only the spend of an attempt that changed nothing disappears, matching `reconcile_item_on_interrupt`'s "as if it never ran before" contract. If the maintainer wants that spend kept, the follow-up is to move the popped attempt's `cost`/`tokens` onto an item-level `discarded_attempts` list the table also sums.
- SHARPENED AT REVIEW, because the question is not yet live and the authored text implied it was. The pop is guarded by `attempts[-1].get("attempt") == attempt_no`, while the attempt record's key is `"number"`, so on current code the predicate is `None == 1` and the pop NEVER FIRES. `87jnym` clause (c) ("make the no-changes arm's attempt pop match the attempt record's real `"number"` key") is what makes it fire, so this question becomes real exactly when this plan's declared dependency lands. Two consequences for the executor: the E-06 `KeyboardInterrupt` cases must write an untracked file (as E-06 already specifies) so the attempt is PRESERVED and the assertions have an attempt to read; and if `87jnym` has landed and a clean-tree case is added later, its expected result is a popped attempt, not a missing field.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the diff adding `record_interrupted_attempt_accounting` showing the local `extract_log_metrics` import, the two success-path-identical write conditions (`cost is not None`, `if toks`), and the outer `except Exception` recording `accounting_error`; plus `python3 -c "from agent_workflows import runner_shared as r; print(callable(r.record_interrupted_attempt_accounting))"` printing `True`. Confirm in the diff that E-01's portion writes NO `state` key, so the attempt-local and state-level halves stay separable.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: the diff showing the `existing in (None, sid)` drift rule, the `session_reconciliation_error` write, and the `not work_dir and not turn_runs_in_review_sweep_lane(...)` guard; plus pasted `grep -n "session_turn_counts" agent_workflows/runner_shared.py` with the same line set as before the change, proving no bump was added. The absence of a bump is a REQUIRED property, not an omission: a bump would let a killed turn consume a session-rotation slot.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted `grep -n "record_interrupted_attempt_accounting(" agent_workflows/runner_shared.py` showing the def plus exactly four calls, each inside the executor-spawn handlers (`StopNowForce`, `StopAtCheckpoint`, `StallTimeout`, `KeyboardInterrupt`), and `git diff` showing no other line of those handlers changed. ALSO paste `grep -n "except KeyboardInterrupt" agent_workflows/runner_shared.py` showing the handler EXISTS inside `execute_item_core` before this plan's edit, which is the evidence that `87jnym` actually executed; at review it did not exist.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted `python3 -m pytest tests/test_interrupt_attempt_metadata.py -o addopts="" -v -k helper` (or the actual names) showing the five helper tests passing, and a test-source excerpt showing real JSONL files and no patching of the two readers. Case (1)'s assertion that `session_turn_counts` is unchanged must be visible in the pasted names or source.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: the two `extract_step_usage` tuples pasted side by side (attempt with `log` only, and the same attempt with `cost`/`tokens` added) showing them EQUAL, plus the passing test name. This is the evidence that the fix does not inflate `aw runs`; a claim without the two tuples is not acceptable.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: pasted `python3 -m pytest tests/test_interrupt_attempt_metadata.py -o addopts="" -v` listing the EIGHT host x raise tests passing (2 hosts x `StallTimeout`, `StopNowForce`, `StopAtCheckpoint`, `KeyboardInterrupt`); then the four E-03 calls temporarily removed and the same run pasted with those eight FAILING (session_id None / `2.17` absent), then restored. All four raises must be exercised BEHAVIORALLY: `StopAtCheckpoint` is constructible without a live stream (`CheckpointObserver(detector=lambda s: False, last_checkpoint_label="E-01")`, verified at review), so a grep-only substitute for it is NOT acceptable. Also paste the `render_continuation_hint(state, run_dir, labels=...)` output containing `ses_probe1`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: the pasted summary line of a bare `python3 -m pytest` run, showing 0 failed, plus the pre-change baseline count so a pre-existing failure is not read as caused by this change. State it as `<before> -> <after>`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. One new helper in `runner_shared.py`, four one-line calls in existing interrupt handlers, and one new test file. The behavior change is confined to what an INTERRUPTED execute attempt records; no success path moves, no renderer changes, and no spec is amended. The change is additive to a ledger whose readers already prefer the stored field, which was measured rather than assumed: `run_viewer.extract_step_usage` reads `attempt["cost"]`/`attempt["tokens"]` in an exclusive `if/else` and falls back to the log only when both are absent, so `aw runs` reports the same figure before and after and the summary table stops printing `$0.00`. Approval also covers one deliberate NON-change the authored plan proposed and this review removed: `session_turn_counts` is NOT bumped, because that counter is the session-rotation trigger.

IT MUST RUN AFTER `87jnym`, AND THAT IS A HARD PREREQUISITE, NOT A PREFERENCE. Three of the four call sites exist today; the fourth (`except KeyboardInterrupt` in `execute_item_core`) does not exist at all, and `reconcile_item_on_interrupt` has zero callers, which is the defect `87jnym` fixes. `87jnym` is `approved` and still in `pending/`. The declared `- Item-Dependencies: executed:87jnym` is what the runner enforces; V-03 additionally requires pasted evidence that the handler exists before this plan edits it.

Scope fence (a DECLARATION for reconciliation, not a stop directive): in `agent_workflows/runner_shared.py`, only the new `record_interrupted_attempt_accounting` function and one added call line inside each of the four executor-spawn interrupt handlers. `tests/test_interrupt_attempt_metadata.py` is new. `agent_workflows/render_stream.py`, `agent_workflows/run_viewer.py`, `agent_workflows/run_analytics*.py`, and both host drivers are expected to need NO edit (the renderers and readers already read the keys this writes). The verifier `spawn_verifier(...)` handlers are NOT touched. No `.spec.md`, backlog, or release record is edited. An edit outside that surface is MADE and then JUSTIFIED at finalize with `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path, which `aw ipd finalize` refuses to complete without.

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. Three claims here are specifically easy to fake and must not be. V-06's MUTATION run, because a passing test proves nothing about a fix unless the same test fails without it, and the HEAD behavior it must reproduce was measured at review on all four raises. V-05's two usage tuples, because "no double count" is otherwise an assertion about code the executor did not run. And V-02's `session_turn_counts` grep, because the absence of a bump is a required property that a diff summary will not show.

GENUINE STOP CONDITIONS (unsafe or unresolvable, not scope questions): if `except KeyboardInterrupt` is still absent from `execute_item_core`, stop and report, because `87jnym` has not executed and adding the handler here would duplicate its declared scope. If a call site requires changing a handler's `return`/`raise` or status routing, stop and report, because that behavior belongs to `ccu3k7` and to executed plan `13xo5k`.

Commit ONLY the Scope-Paths via `aw commit zrvtm2 -- agent_workflows/runner_shared.py tests/test_interrupt_attempt_metadata.py`, never `git add -A`, never push. Before the terminal transition `aw ipd lint --phase pre-transition` must conform and every `V-*` carry observed evidence; the RUNNER owns that transition when it executes this plan in a lane, otherwise the executor performs it with `aw ipd finalize`, never a raw `git mv`. On execution, close BOTH `hyit04` and `pfh5qa` with `--evidence` citing the executed plan: both carry `- Blocks-Release: next` and both are `graduated` to this Set, and this plan inherits that gate (note `- From-Backlog:` can name only one, so `pfh5qa`'s close relies on the `--evidence` route rather than the handoff route).
