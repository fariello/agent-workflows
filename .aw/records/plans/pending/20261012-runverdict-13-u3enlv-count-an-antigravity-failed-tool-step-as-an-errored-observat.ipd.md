# IPD: Count an Antigravity FAILED tool step as an errored observation in both analytics readers

- Date: 2026-10-12
- Kind: child
- Concern: Three in-tree readers of an Antigravity `step_update` accept different terminal-state tuples. `agy_runipd.render_agy_event` accepts `("DONE", "ERROR", "FAILED")` in both its `step_type == "tool"` and `step_type == "subagent"` arms (and `agy_runipd._AGY_STATE_TO_STATUS` maps `FAILED` to `"error"`), while `run_dashboard._agy_line` gates on `state not in ("DONE", "ERROR")` and `verifier_corroboration.tool_call_from_event` gates on `(state != "DONE" and state != "ERROR") or stype != "tool"`. Measured at HEAD `3301efc96` (F-01): a `FAILED` `run_command` step carrying `CommandLine="python3 -m pytest"` is rendered to the operator (`bash:  python3 -m pytest`) but `tool_call_from_event` returns `None`, `extract_session_commands` reports `commands=[]`, `missing_command_count=0`, the corroboration verdict is `indeterminate`/`missing-command-text`, and `session_stats` reports `tool_calls=0`, `tool_errors=0`, `commands={}`.
- Scope: IN: decide once that an Antigravity `FAILED` step is a terminal, ERRORED observation (it ran and failed), equivalent to `ERROR`; define that decision as two shared constants in `verifier_corroboration` (`AGY_TERMINAL_STATES = ("DONE", "ERROR", "FAILED")`, `AGY_ERROR_STATES = ("ERROR", "FAILED")`); route `tool_call_from_event`'s Antigravity branch, `run_dashboard._agy_line`'s state gate, and both state gates in `agy_runipd.render_agy_event` onto them; bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` by one because cached per-file values change for unchanged logs; add outcome tests for the extractor, the verdict, the dashboard, and cross-reader parity; record the decision in `DECISIONS.md` and one `CHANGELOG.md` line. OUT, each with a reason in the Deferred section: the tool-name key precedence (plan `n8we3u`, backlog `1kebul`), the `step_type == "subagent"` delegation shape (backlog `iuhx9d`), what a corroboration verdict DOES (D160), how a matched-but-errored command is judged (existing `ERROR` behavior, unchanged), `runner_stop.is_agy_safe_checkpoint` (a `FAILED` step is correctly not a checkpoint), and `agy_run._progress_messages`' state word table.
- Scope-Paths: agent_workflows/verifier_corroboration.py, agent_workflows/run_dashboard.py, agent_workflows/agy_runipd.py, tests/test_verifier_corroboration.py, tests/test_run_dashboard.py, tests/test_agy_failed_state_parity.py, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: executed:e08ssu, executed:n8we3u
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 8fiybc
- Set: runverdict
- Order: 13
- Highest E allocated: 09
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: u3enlv
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008. Record: .aw/records/reviews/20261012-runverdict-13-u3enlv-count-an-antigravity-failed-tool-step-as-an-errored-observat.review.md

- 2026-10-12 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog 8fiybc. Re-measured at HEAD 3301efc96: the backlog's measured consequence reproduces (FAILED -> tool_call_from_event None, verdict indeterminate missing-command-text, dashboard tool_calls 0) while the renderer renders the step. Decision (OQ-01): FAILED is an errored observation, identical to ERROR, on the evidence that the renderer already maps FAILED to "error". Suite baseline: 39 failed (unrelated no-project/explicit-dir/trailer/finalize-sendback env tests), 7180 passed, 2 skipped.
- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every Antigravity session-log reader agree on which step states are terminal and which are errors, by defining the accepted tuples once in `verifier_corroboration` and routing the renderer and both analytics readers onto them, so a `FAILED` tool call the operator sees is also counted by the dashboard and observed (as errored) by the corroboration reader.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-drive the authoring measurements at the executing HEAD and record them verbatim. EDIT NO FILE IN THIS ITEM. (a) For each state in `DONE`, `ERROR`, `FAILED`, build one `step_update` (`step_type="tool"`, `tool_name="run_command"`, `tool_info={"name": "run_command", "parameters": {"CommandLine": "python3 -m pytest"}}`), write it to a temporary JSONL log, and paste `verifier_corroboration.tool_call_from_event(ev)`, `extract_session_commands(log)` (commands, `missing_command_count`), `corroborate_verifier_turn(log, ["python3 -m pytest"])` (`verdict`, `reason_code`, `observed_count`), `run_dashboard.session_stats(log)` (`tool_calls`, `tool_errors`, `commands`), and `agy_runipd.render_agy_event(json.dumps(ev), render_stream.Palette(False), verbosity=1, use_unicode=False)`. (b) For `ERROR` and `FAILED`, paste `session_stats` `steps`/`error_messages`/`input` for an `agent_response` step carrying `usage.input_tokens=5` and for an `error_message` step (F-03). (c) Run the bare suite and record the sorted failing NODE IDS. Also paste `run_dashboard.DASHBOARD_SCHEMA_VERSION` and the last `### D<n>` heading in `DECISIONS.md` (E-04 and E-09 build on them). If (a) shows `FAILED` is ALREADY counted by both analytics readers, STOP AND REPORT: the divergence was closed elsewhere (for example by `n8we3u` touching the same function).
  - Depends on: none
  - Expected outcome: pasted transcripts reproducing F-01 and F-03 (or the STOP report), and the baseline failing node-id list.
  - Execution state: performed

### Task group 2: one decision, defined once

- [x] E-02 Add `AGY_TERMINAL_STATES: tuple[str, ...] = ("DONE", "ERROR", "FAILED")` and `AGY_ERROR_STATES: tuple[str, ...] = ("ERROR", "FAILED")` to `agent_workflows/verifier_corroboration.py`, export both in `__all__`, and document the decision beside them: a `FAILED` step is a terminal errored observation, equivalent to `ERROR`, on OQ-01's grounds (the live renderer has always accepted it and `agy_runipd._AGY_STATE_TO_STATUS` already maps it to `"error"`; no live Antigravity log exists in this checkout to show the two differ). Keep the module stdlib-only and import nothing from `agent_workflows`.
  - Depends on: E-01
  - Expected outcome: both constants exist with the stated values and are importable from `verifier_corroboration`.
  - Execution state: performed

- [x] E-03 Route `verifier_corroboration.tool_call_from_event`'s Antigravity branch onto the constants: return `None` unless `state in AGY_TERMINAL_STATES` and `stype == "tool"`, and set `is_error = state in AGY_ERROR_STATES`. Add the decision to the function's DESIGN DECISIONS docstring as the next numbered decision. Change NOTHING else in the function (in particular not the tool-name key, which `n8we3u` owns, and not the OpenCode branch).
  - Depends on: E-02
  - Expected outcome: the `FAILED` shape yields `ToolCall(tool='run_command', host='agy', command='python3 -m pytest', error=True, delegation=False, command_missing=False)`; `DONE` and `ERROR` yield exactly the V-01 baseline values.
  - Execution state: performed

- [x] E-04 Route `run_dashboard._agy_line`'s state gate onto `verifier_corroboration.AGY_TERMINAL_STATES` (replacing `("DONE", "ERROR")`), so a `FAILED` `tool`, `agent_response` or `error_message` step is counted exactly as its `ERROR` twin is (F-03). Then bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` by one from its value at the executing HEAD (4 once `n8we3u` has executed, which the `executed:n8we3u` edge guarantees, so 4 -> 5; read the live value rather than assuming it) and rename the existing version test in `tests/test_run_dashboard.py` (`test_dashboard_schema_version_is_<N>`) to the new value, docstring citing this plan. Reason (F-04): `_StatsCache` reuses entries keyed by `(size, mtime_ns)` while `raw.get("schema") == DASHBOARD_SCHEMA_VERSION`, and this change alters counts for an unchanged log.
  - Depends on: E-02
  - Expected outcome: `session_stats` on the `FAILED` tool log reports `tool_calls=1`, `tool_errors=1`, `commands={'test': 1}`; `DASHBOARD_SCHEMA_VERSION` is one higher; the renamed test passes.
  - Execution state: performed

- [x] E-05 Route both state gates in `agy_runipd.render_agy_event` (the `step_type == "tool"` and `step_type == "subagent"` arms) onto `verifier_corroboration.AGY_TERMINAL_STATES`, importing it at module top. This is a pure de-duplication: the accepted set is unchanged, so rendered output must be byte-identical for every state.
  - Depends on: E-02
  - Expected outcome: rendered lines for `ACTIVE`, `DONE`, `ERROR`, `FAILED` tool and subagent steps equal the V-01 baseline; `tests/test_agy_runipd_cli.py` passes unedited.
  - Execution state: performed

### Task group 3: make the next divergence fail a test

- [x] E-06 Add cases (ADD only; do not edit existing ones) to `tests/test_verifier_corroboration.py`: a `FAILED` `run_command` log yields one observed command with `error=True` and `missing_command_count == 0`; `corroborate_verifier_turn(log, ["python3 -m pytest"])` on it equals the `verdict` and `reason_code` the same log yields with `state="ERROR"` (both `uncorroborated` at authoring and at review, see OQ-02); a log with one `FAILED` then one `DONE` pytest call and a matching claim yields `corroborated` with `observed_count == 2` (the verdict alone is NOT a fix test: re-measured at review, that log is already `corroborated` pre-fix because the `FAILED` call is dropped and `observed_count == 1`; the count is what fails pre-fix).
  - Depends on: E-03
  - Expected outcome: the new cases pass; every pre-existing case passes unedited.
  - Execution state: performed

- [x] E-07 Add cases to `tests/test_run_dashboard.py`: `session_stats` on a `FAILED` tool log counts `tool_calls=1`, `tool_errors=1`, `tool_err={'run_command': 1}`, `commands={'test': 1}`; a `FAILED` `agent_response` with usage counts `steps=1` and its tokens; a `FAILED` `error_message` counts `error_messages=1`; and for each of those three shapes the `FAILED` stats equal the `ERROR` twin's stats.
  - Depends on: E-04
  - Expected outcome: the new cases pass; every pre-existing case passes unedited apart from E-04's rename.
  - Execution state: performed

- [x] E-08 Add `tests/test_agy_failed_state_parity.py`, a cross-reader PARITY test driving the real readers (no mocks) over states `ACTIVE`, `DONE`, `ERROR`, `FAILED`, plus an unknown `CANCELED`: for each state it asserts that `render_agy_event` renders a `tool` step (non-`None` at `verbosity=1`) EXACTLY when `tool_call_from_event` returns a record AND `session_stats` counts `tool_calls == 1`, and, for the states that yield a record, that `ToolCall.error` equals `session_stats` `tool_errors == 1`. The expected outcome per state is a LITERAL table written in the test (`ACTIVE`: not observed; `DONE`: observed, not errored; `ERROR`: observed, errored; `FAILED`: observed, errored; `CANCELED`: not observed), NOT derived from `AGY_TERMINAL_STATES`/`AGY_ERROR_STATES`, so a wrong constant fails the test instead of redefining the oracle. Assert on outputs, never on source text.
  - Depends on: E-03, E-04, E-05
  - Expected outcome: the new file passes; reverting either analytics gate to `("DONE", "ERROR")` makes the `FAILED` row fail (demonstrated in V-08).
  - Execution state: performed

### Task group 4: record the decision and run the suite

- [x] E-09 Record the decision as the next free `### D<n>` in `DECISIONS.md` (D162 is the last at review; `n8we3u`, which executes first, takes the next, so expect D164, but use whatever is next free) with Context (the three tuples and F-01's measurement), Decision (`FAILED` is a terminal errored observation equal to `ERROR`, defined once in `verifier_corroboration`), the rejected alternative (treat `FAILED` as a non-event and drop it from the renderer) with its reason, and Applied (the files). Add one `CHANGELOG.md` line under the pending release, written without em or en dashes (user-facing prose), e.g. "Fixed: the run dashboard and verifier corroboration now count an Antigravity tool call that ended in the FAILED state, matching what the live stream shows." Then run the full suite BARE (`python3 -m pytest`) and compare failing NODE IDS against E-01's baseline.
  - Depends on: E-03, E-04, E-05, E-06, E-07, E-08
  - Expected outcome: one new DECISIONS entry, one CHANGELOG line, and no failing node id that is not in the baseline.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `verifier_corroboration` is declared a pure stdlib-only reader that never imports `runner_shared`, `run_dashboard`, or either host runner; the constants live there so the dependency direction stays the one `e08ssu` established (consumers import it, never the reverse).
- `tool_call_from_event` records each resolved reader disagreement as a numbered DESIGN DECISION in its docstring; this plan adds one in the same place.
- Cached dashboard values that change for an unchanged log require a `DASHBOARD_SCHEMA_VERSION` bump (`e08ssu` OQ-02, `run_dashboard._StatsCache`), with the version test renamed to match.
- The corroboration verdict is observational and refuses nothing (D160, spec `25kzda` Section 5.1); this plan changes which verdict is computed for one shape, not what consumes it.
- Tests assert outcomes by driving real functions (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Run the suite bare: `python3 -m pytest` (`pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Location | Finding | Evidence |
|---|---|---|---|---|
| F-01 | LOW | `verifier_corroboration.tool_call_from_event`, `run_dashboard._agy_line`, `agy_runipd.render_agy_event` | THE BACKLOG ITEM'S MEASURED CONSEQUENCE REPRODUCES. For a `run_command` step with `CommandLine="python3 -m pytest"`: `DONE` -> `ToolCall(..., error=False)`, verdict `corroborated corroborated`, dash `tool_calls 1, tool_errors 0, commands {'test': 1}`; `ERROR` -> `ToolCall(..., error=True)`, verdict `uncorroborated uncorroborated`, dash `tool_calls 1, tool_errors 1, commands {'test': 1}`; `FAILED` -> `tc= None`, `cmds= [] 0`, verdict `indeterminate missing-command-text`, dash `tool_calls 0, tool_errors 0, commands {}`. The renderer returns `'❯ bash:  python3 -m pytest'` for all three. | Python transcript at HEAD `3301efc96` driving the real functions. |
| F-02 | DECISION INPUT | `agy_runipd._AGY_STATE_TO_STATUS` | The renderer already treats `FAILED` as an error: `"FAILED": "error"`, with the comment "`FAILED` is included because `render_agy_event` has always accepted it beside `ERROR`". No live Antigravity log exists in this checkout to show `FAILED` and `ERROR` differ in meaning (`mm6wuz`: zero `step_update` lines across the session corpus, quoted in `agy_runipd`'s prefix-kind table comment). | `agy_runipd._AGY_STATE_TO_STATUS`; `runner_stop.is_agy_safe_checkpoint` docstring ("`ACTIVE`, `ERROR`, and `FAILED` are not checkpoints") also names `FAILED` as a real terminal non-success state. |
| F-03 | LOW | `run_dashboard._agy_line` | THE DASHBOARD GATE IS WIDER THAN TOOL STEPS: it is the first check in `_agy_line`, so a `FAILED` `agent_response` (tokens spent) and a `FAILED` `error_message` are also dropped. Measured: `ERROR agent_response` -> `steps 1, input 5.0`; `FAILED agent_response` -> `steps 0, input 0.0`; `ERROR error_message` -> `error_messages 1`; `FAILED error_message` -> `0`. The backlog names this exact tuple as one of the three to reconcile, so it is reconciled whole rather than special-cased to tool steps. | Python transcript at authoring driving `run_dashboard.session_stats`. |
| F-04 | LOW | `run_dashboard._StatsCache` | Cached entries keyed by `(size, mtime_ns)` and gated on `raw.get("schema") == DASHBOARD_SCHEMA_VERSION` (3 at authoring, pinned by `test_dashboard_schema_version_is_3`) would serve the old zero counts for an unchanged log, so the version must move. | `run_dashboard.DASHBOARD_SCHEMA_VERSION = 3`; `e08ssu` OQ-02 applied the same rule. |
| F-05 | BASELINE | full suite | At authoring HEAD `3301efc96` the bare suite reports `39 failed, 7180 passed, 2 skipped, 3 warnings in 217.77s`. Every failure is in an environment-sensitive no-project / explicit-dir / trailer / finalize-sendback / nv-backend test, none touching a Scope-Path; the three directly relevant files pass (`123 passed` for `test_verifier_corroboration.py test_run_dashboard.py test_agy_runipd_cli.py`). The executor compares by NODE ID, not total. | `python3 -m pytest` in this lane; `python3 -m pytest -o addopts="" -q -n auto tests/test_verifier_corroboration.py tests/test_run_dashboard.py tests/test_agy_runipd_cli.py` -> `123 passed in 11.39s`. |
| F-06 | INFO | plan `n8we3u` (Order 12, `approved` at review) | `n8we3u` edits the same function (`tool_call_from_event`, name key only), bumps the same `DASHBOARD_SCHEMA_VERSION` from 3 to 4, and takes D163; it explicitly defers this item (`8fiybc`, with `- Carrier: 8fiybc`). The two changes are orthogonal in LOGIC, but NOT in the cache key: if both execute from the same base (two lanes built before either lands), each writes `DASHBOARD_SCHEMA_VERSION = 4` and renames the test to `_is_4`, and git merges those IDENTICAL hunks cleanly, so the second change ships with no version bump of its own and a cache written by a build carrying only the first is served stale for unchanged logs. No textual conflict and no test catches that. Review therefore added the edge `executed:n8we3u` (review decision D-1): `n8we3u` is approved, so the edge costs nothing in practice, and it makes E-04 deterministically bump 4 -> 5 and E-09 take the next free D-number after `n8we3u`'s. | `n8we3u` Scope, E-03, E-04, E-11, Deferred section; `run_dashboard._StatsCache.__init__` gate `raw.get("schema") == DASHBOARD_SCHEMA_VERSION`. |

## Proposed changes (ordered, validatable)

1. Re-measure (E-01).
2. Define `AGY_TERMINAL_STATES` / `AGY_ERROR_STATES` once in `verifier_corroboration` (E-02).
3. Route `tool_call_from_event` (E-03), `run_dashboard._agy_line` plus the schema bump (E-04), and `render_agy_event` (E-05) onto them.
4. Add extractor/verdict, dashboard, and parity outcome tests (E-06, E-07, E-08).
5. Record the D-entry and CHANGELOG line and run the full suite (E-09).

## Deferred / out of scope (with reason)

- Tool-name key precedence (`tool_info.name` vs `tool_name`): owned by plan `n8we3u` / backlog `1kebul`; a different key with different counts.
  - Carrier: n8we3u
  - Carrier-Evidence: .aw/records/plans/executed/20261011-runverdict-12-n8we3u-resolve-the-antigravity-tool-name-through-one-shared-precede.ipd.md
- The `step_type == "subagent"` delegation shape in the analytics readers: owned by backlog `iuhx9d`.
  - Carrier: iuhx9d
- How a claim matched only to an ERRORED command is judged (`uncorroborated` today for `ERROR`): existing, deliberate behavior of `corroborate_verifier_turn` ("matched an observed non-errored command"); this plan makes `FAILED` follow it rather than re-deciding it. See OQ-02.
  - Carrier-Declined: no defect is recorded against the `ERROR` rule; it is deliberate shipped behavior, and E-06 pins FAILED-equals-ERROR so any later change carries `FAILED` with it.
- `runner_stop.is_agy_safe_checkpoint`: a `FAILED` step is correctly not a safe checkpoint; nothing to reconcile.
  - Carrier-Declined: nothing is owed; the checkpoint predicate already treats `FAILED` as a non-checkpoint, which is correct.
- `agy_run._progress_messages`' state-word table: it already prints `failed` for an unknown `FAILED` state via its lowercase fallback; cosmetic and not an accepted-state gate.
  - Carrier-Declined: re-verified at review, its table has no `FAILED` key and the lowercase fallback prints `failed`, so the output is already right.
- What the corroboration verdict does: D160 rules it observational.
  - Carrier-Declined: settled by D160; this plan changes no consumer.

## Scope check

- Over-scope: none. Every Scope-Path is a reader carrying one of the three tuples, the cache version that must move with E-04, a test that pins the outcome, or the decision record.
- Under-scope: none known. A search for `"DONE", "ERROR"` in `agent_workflows/` finds only `run_dashboard._agy_line` and the two `render_agy_event` gates; `tool_call_from_event` spells it `state != "DONE" and state != "ERROR"`. Review widened the search to every `step_update` reader (`agy_view.format_record`, `run_viewer`, `stall_progress`, `runner_shared`'s agy text collector, `agy_run._progress_messages`, `runner_stop`): none gates on a terminal-state tuple other than `runner_stop`'s DONE-only checkpoint (deferred above), and the renderer's `state == "DONE"` tracker/usage checks exclude `ERROR` and `FAILED` alike, so FAILED-equals-ERROR already holds there.

## Required tests / validation

- `python3 -m pytest` BARE in the executing worktree; do not add `-n0`, another `-q`, or `-p no:randomly`. Compare failing NODE IDS with E-01's baseline, not totals.
- `tests/test_agy_failed_state_parity.py` (new, E-08) must pass, and a deliberate revert of an analytics gate must make it fail (V-08).
- New cases in `tests/test_verifier_corroboration.py` (E-06) and `tests/test_run_dashboard.py` (E-07) pin the `FAILED` extractor, verdict and dashboard outcomes.
- Every PRE-EXISTING case in `tests/test_verifier_corroboration.py`, `tests/test_run_dashboard.py` (except the renamed version test) and `tests/test_agy_runipd_cli.py` passes unedited.
- `aw ipd lint --phase pre-transition` conforming before the terminal transition.

## Spec / documentation sync

- Specs: N/A with reason. No spec defines the Antigravity step-state vocabulary; spec `25kzda` Section 5.1 rules corroboration observational, which this plan does not contradict. `Scope-Paths` declares no `.spec.md`.
- `DECISIONS.md`: new entry recording that `FAILED` equals `ERROR` (E-09).
- `CHANGELOG.md`: one line, no em or en dashes (E-09).
- Module docstrings: the constants and `tool_call_from_event` carry the decision in code (E-02, E-03).

## Open questions

### OQ-01: Is a FAILED tool call an observation (it ran and failed) or a non-event?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, an observation, errored, identical to `ERROR`. Evidence (F-02): the live renderer has always accepted `FAILED` beside `ERROR` and `agy_runipd._AGY_STATE_TO_STATUS` maps it to `"error"`; `runner_stop.is_agy_safe_checkpoint` names it a terminal non-success state; the step carries the same `tool_info.parameters` an `ERROR` step does (the renderer prints its command). The rejected alternative, dropping `FAILED` from the renderer to match analytics, would hide a failed call from the operator, which is strictly worse for a human watching a run, and no evidence suggests the host emits `FAILED` for a call that never started.

### OQ-02: The FAILED-only shape moves from indeterminate to uncorroborated. Is that acceptable?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, yes, because it is exactly what the same log yields with `state="ERROR"` today (F-01: `uncorroborated uncorroborated`), the verdict refuses and downgrades nothing (D160), and today's `missing-command-text` reason is factually wrong (the command text is present). The backlog anticipated the opposite risk (a verdict moving TOWARD `indeterminate`); this plan removes that path. Whether a claim matched only to an errored command should be `uncorroborated` at all is a question about the existing `ERROR` rule, deferred above, and E-06 pins FAILED-equals-ERROR rather than a literal verdict so that a later decision on the `ERROR` rule carries `FAILED` with it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the full transcript of (a) the five readouts for `DONE`, `ERROR`, `FAILED` showing `FAILED` -> `None`, `indeterminate missing-command-text`, `tool_calls 0` (or the STOP report), (b) the `agent_response`/`error_message` stats for `ERROR` vs `FAILED`, and (c) the bare suite summary line plus the sorted failing node-id list. FAILS if any value is paraphrased rather than pasted.
  - Observed evidence: Re-driven at executing HEAD `21b8df8a981b409125f4edd78f15348de02e1875`:
    ```text
    === (a) tool step_update across DONE, ERROR, FAILED ===
    state=DONE:
      tool_call_from_event: ToolCall(tool='run_command', host='agy', command='python3 -m pytest', path=None, seconds=0.0, error=False, delegation=False, command_missing=False)
      extract_session_commands: commands=[ObservedCommand(command='python3 -m pytest', tool='run_command', host='agy', error=False)], missing_command_count=0
      corroborate_verifier_turn: verdict='corroborated', reason_code='corroborated', observed_count=1
      session_stats: tool_calls=1, tool_errors=0, commands={'test': 1}
      render_agy_event: '❯ bash:  python3 -m pytest'
    state=ERROR:
      tool_call_from_event: ToolCall(tool='run_command', host='agy', command='python3 -m pytest', path=None, seconds=0.0, error=True, delegation=False, command_missing=False)
      extract_session_commands: commands=[ObservedCommand(command='python3 -m pytest', tool='run_command', host='agy', error=True)], missing_command_count=0
      corroborate_verifier_turn: verdict='uncorroborated', reason_code='uncorroborated', observed_count=1
      session_stats: tool_calls=1, tool_errors=1, commands={'test': 1}
      render_agy_event: '❯ bash:  python3 -m pytest'
    state=FAILED:
      tool_call_from_event: None
      extract_session_commands: commands=[], missing_command_count=0
      corroborate_verifier_turn: verdict='indeterminate', reason_code='missing-command-text', observed_count=0
      session_stats: tool_calls=0, tool_errors=0, commands={}
      render_agy_event: '❯ bash:  python3 -m pytest'

    === (b) agent_response and error_message across ERROR, FAILED ===
    state=ERROR agent_response: steps=1, error_messages=0, input=5.0
    state=ERROR error_message: steps=0, error_messages=1, input=0.0
    state=FAILED agent_response: steps=0, error_messages=0, input=0.0
    state=FAILED error_message: steps=0, error_messages=0, input=0.0

    === (c-meta) DASHBOARD_SCHEMA_VERSION and last DECISIONS heading ===
    DASHBOARD_SCHEMA_VERSION = 4
    last DECISIONS heading: ### D165. Require an executed plan when a backlog close cites a plan as SATISFIED evidence
    ```
    Bare `python3 -m pytest` summary line and sorted failing node-id list at baseline HEAD `21b8df8a981b409125f4edd78f15348de02e1875`:
    ```text
    FAILED tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository
    1 failed, 8300 passed, 4 skipped, 18 xfailed, 3 warnings in 476.70s (0:07:56)
    NOTE: 292 tests were deselected by -m/-k and did not run.
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the `git diff` adding both constants and their comment, and a transcript printing `verifier_corroboration.AGY_TERMINAL_STATES`, `verifier_corroboration.AGY_ERROR_STATES`, and `"AGY_TERMINAL_STATES" in verifier_corroboration.__all__ and "AGY_ERROR_STATES" in verifier_corroboration.__all__` -> `True`.
  - Observed evidence: `git diff` of constants and `__all__` in `agent_workflows/verifier_corroboration.py` plus transcript:
    ```diff
    @@ -76,6 +76,8 @@ from pathlib import Path
     from typing import Any, NamedTuple

     __all__ = [
    +    "AGY_ERROR_STATES",
    +    "AGY_TERMINAL_STATES",
         "CORROBORATED",
         "INDETERMINATE_CLAIMS_EMPTY",
         "INDETERMINATE_DELEGATION",
    @@ -185,6 +187,17 @@ SUBAGENT_TOOLS: frozenset[str] = frozenset(
         }
     )

    +# Antigravity terminal and error step states (u3enlv, OQ-01, D166):
    +# A `FAILED` step is a terminal, errored observation (it ran and failed), equivalent to
    +# `ERROR`. The live renderer (`agy_runipd.render_agy_event`) has always accepted
    +# `("DONE", "ERROR", "FAILED")` and `agy_runipd._AGY_STATE_TO_STATUS` already maps
    +# `FAILED` to `"error"`; `runner_stop.is_agy_safe_checkpoint` names `FAILED` a terminal
    +# non-success state; and no live Antigravity log exists in this checkout to show `FAILED`
    +# and `ERROR` differ in meaning. Defined once here so the renderer, `tool_call_from_event`,
    +# and `run_dashboard._agy_line` share one state vocabulary.
    +AGY_TERMINAL_STATES: tuple[str, ...] = ("DONE", "ERROR", "FAILED")
    +AGY_ERROR_STATES: tuple[str, ...] = ("ERROR", "FAILED")
    ```
    ```text
    ('DONE', 'ERROR', 'FAILED')
    ('ERROR', 'FAILED')
    True
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the `git diff` of `tool_call_from_event` (including the new DESIGN DECISION) and the `ToolCall` returned for `DONE`, `ERROR`, `FAILED` (the `FAILED` one with `error=True`, `command='python3 -m pytest'`), plus `ACTIVE` -> `None`. Re-run V-01(a)'s extractor and verdict lines and paste `FAILED` -> one command, `missing_command_count 0`, and the same `verdict`/`reason_code` as `ERROR`. Paste `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` from BEFORE E-06 adds cases, all passing.
  - Observed evidence: `git diff` of `tool_call_from_event` in `agent_workflows/verifier_corroboration.py`, extractor/verdict transcript across `DONE`, `ERROR`, `FAILED`, `ACTIVE`, and pre-E-06 `tests/test_verifier_corroboration.py` run:
    ```diff
    @@ -395,6 +408,17 @@ def tool_call_from_event(obj: Any) -> ToolCall | None:
            (b) A step where tool_info.name and tool_name conflict and one of them is
                a subagent is ambiguous; failing open prevents accusing a verifier of
                failing to run claimed tests.
    +
    +    5. Antigravity FAILED State as Terminal Errored Observation (u3enlv, resolving 8fiybc):
    +       The Antigravity branch accepts `state in AGY_TERMINAL_STATES`
    +       (`("DONE", "ERROR", "FAILED")`) and sets `error = state in AGY_ERROR_STATES`
    +       (`("ERROR", "FAILED")`).
    +       Rationale:
    +       (a) `agy_runipd.render_agy_event` has always accepted `FAILED` alongside `DONE`
    +           and `ERROR` and `_AGY_STATE_TO_STATUS` maps `FAILED` to `"error"`.
    +       (b) Treating `FAILED` as a terminal errored observation reconciles `tool_call_from_event`,
    +           `run_dashboard._agy_line`, and `agy_runipd.render_agy_event` onto one shared
    +           vocabulary without hiding failed tool calls from the operator or analytics.
         """
         if not isinstance(obj, (dict, Mapping)):
             return None
    @@ -405,10 +429,10 @@ def tool_call_from_event(obj: Any) -> ToolCall | None:
                 return None
             state = su.get("state")
             stype = su.get("step_type")
    -        if (state != "DONE" and state != "ERROR") or stype != "tool":
    +        if state not in AGY_TERMINAL_STATES or stype != "tool":
                 return None
             tool_name = agy_tool_name(su)
    -        is_error = state == "ERROR"
    +        is_error = state in AGY_ERROR_STATES
             info = su.get("tool_info")
    ```
    ```text
    state=DONE:
      tool_call_from_event: ToolCall(tool='run_command', host='agy', command='python3 -m pytest', path=None, seconds=0.0, error=False, delegation=False, command_missing=False)
      extract_session_commands: commands=[ObservedCommand(command='python3 -m pytest', tool='run_command', host='agy', error=False)], missing_command_count=0
      corroborate_verifier_turn: verdict='corroborated', reason_code='corroborated', observed_count=1
    state=ERROR:
      tool_call_from_event: ToolCall(tool='run_command', host='agy', command='python3 -m pytest', path=None, seconds=0.0, error=True, delegation=False, command_missing=False)
      extract_session_commands: commands=[ObservedCommand(command='python3 -m pytest', tool='run_command', host='agy', error=True)], missing_command_count=0
      corroborate_verifier_turn: verdict='uncorroborated', reason_code='uncorroborated', observed_count=1
    state=FAILED:
      tool_call_from_event: ToolCall(tool='run_command', host='agy', command='python3 -m pytest', path=None, seconds=0.0, error=True, delegation=False, command_missing=False)
      extract_session_commands: commands=[ObservedCommand(command='python3 -m pytest', tool='run_command', host='agy', error=True)], missing_command_count=0
      corroborate_verifier_turn: verdict='uncorroborated', reason_code='uncorroborated', observed_count=1
    state=ACTIVE:
      tool_call_from_event: None
    ................................................                         [100%]
    48 passed in 6.92s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the diff of `_agy_line`'s gate, the version bump and the renamed test; `session_stats` for the `FAILED` tool log (`tool_calls 1`, `tool_errors 1`, `commands {'test': 1}`) and the `FAILED` `agent_response`/`error_message` logs equal to their `ERROR` twins; and a transcript in which a cache file written at the OLD schema for an unchanged `FAILED` log is ignored, so the new counts are returned (code path: `run_dashboard._StatsCache.__init__`).
  - Observed evidence: `git diff` of `agent_workflows/run_dashboard.py` and the renamed test in `tests/test_run_dashboard.py`, plus transcript of `session_stats` and `run_dashboard._StatsCache.__init__`:
    ```diff
    diff --git a/agent_workflows/run_dashboard.py b/agent_workflows/run_dashboard.py
    index 2f8ff199f..2924745bb 100644
    --- a/agent_workflows/run_dashboard.py
    +++ b/agent_workflows/run_dashboard.py
    @@ -38,7 +38,10 @@ from typing import Any, Callable, Iterable, Mapping, Sequence

     from agent_workflows.run_analytics_schema import resolve_attempt_model
     from agent_workflows.runner_shared import canonical_terminal_status
    -from agent_workflows.verifier_corroboration import tool_call_from_event
    +from agent_workflows.verifier_corroboration import (
    +    AGY_TERMINAL_STATES,
    +    tool_call_from_event,
    +)

     __all__ = [
         "DASHBOARD_SCHEMA_VERSION",
    @@ -52,7 +55,7 @@ __all__ = [
         "render_dashboard",
     ]

    -DASHBOARD_SCHEMA_VERSION = 4
    +DASHBOARD_SCHEMA_VERSION = 5
     ASSETS_DIRNAME = "run_dashboard_assets"
     STATS_CACHE_FILENAME = "dashboard-session-stats.json"
     UNRECORDED = "(unrecorded)"
    @@ -318,7 +321,7 @@ def _agy_line(
             return
         state = su.get("state")
         stype = su.get("step_type")
    -    if state not in ("DONE", "ERROR"):
    +    if state not in AGY_TERMINAL_STATES:
             return
         secs = _num(su.get("duration_seconds"))
         if stype == "agent_response":
    ```
    ```diff
    @@ -585,9 +585,9 @@ class TestUnifiedToolExtractionRouting(unittest.TestCase):
             for name in ("task", "browser_subagent", "subagent", "invoke_subagent"):
                 self.assertEqual(dash.tool_category(name), "subagent")

    -    def test_dashboard_schema_version_is_4(self) -> None:
    -        """E-04 (n8we3u): DASHBOARD_SCHEMA_VERSION is 4."""
    -        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 4)
    +    def test_dashboard_schema_version_is_5(self) -> None:
    +        """E-04 (u3enlv): DASHBOARD_SCHEMA_VERSION is 5."""
    +        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 5)
    ```
    ```text
    FAILED tool session_stats: tool_calls=1, tool_errors=1, commands={'test': 1}
    agent_response ERROR vs FAILED equal: True (steps=1, error_messages=0, input=5.0)
    error_message ERROR vs FAILED equal: True (steps=0, error_messages=1, input=0.0)
    _StatsCache.__init__ with schema=4: data_keys=0
    _StatsCache.get(log_tool): hits=0, misses=1, tool_calls=1, tool_errors=1, commands={'test': 1}
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the diff of both `render_agy_event` gates and the import; the rendered line for `ACTIVE`, `DONE`, `ERROR`, `FAILED` tool steps and `DONE`/`FAILED` subagent steps, identical to V-01's renderer output (`ACTIVE` -> `None`); and `python3 -m pytest -o addopts="" -q tests/test_agy_runipd_cli.py` passing with `git diff --stat tests/test_agy_runipd_cli.py` empty.
  - Observed evidence: `git diff agent_workflows/agy_runipd.py`, rendered lines for tool and subagent steps, and `tests/test_agy_runipd_cli.py` test run + empty diff:
    ```diff
    diff --git a/agent_workflows/agy_runipd.py b/agent_workflows/agy_runipd.py
    index 00e1f4bd2..c2756e926 100755
    --- a/agent_workflows/agy_runipd.py
    +++ b/agent_workflows/agy_runipd.py
    @@ -36,7 +36,10 @@ from typing import Any, Callable, Iterable, Optional
     # introducing a partial `__all__` that would understate the rest of the public surface.
     from agent_workflows.render_stream import Heartbeat as Heartbeat
     from agent_workflows import runner_shutdown, stall_progress
    -from agent_workflows.verifier_corroboration import agy_tool_name
    +from agent_workflows.verifier_corroboration import (
    +    AGY_TERMINAL_STATES,
    +    agy_tool_name,
    +)

     # runnoop Order 02 (`m85gxh`): the pure PER-ARTIFACT DISPOSITION renderer, imported from its OWNING
     # module and NOT from `oc_runipd`. This module already imports 48 names from that driver and zero flow
    @@ -1096,7 +1099,7 @@ def render_agy_event(
             if step_type == "tool":
                 # Active tool events are suppressed to prevent double output in live streams;
                 # the line is rendered once when the tool reaches a terminal state (DONE/ERROR/FAILED).
    -            if state not in ("DONE", "ERROR", "FAILED"):
    +            if state not in AGY_TERMINAL_STATES:
                     return None
                 raw_tool_info = step.get("tool_info")
                 tool_info = (
    @@ -1261,7 +1264,7 @@ def render_agy_event(
                 return None

             if step_type == "subagent":
    -            if state not in ("DONE", "ERROR", "FAILED"):
    +            if state not in AGY_TERMINAL_STATES:
                     return None
                 subagent = step.get("subagent_info") or {}
                 subagents = subagent.get("subagents", [])
    ```
    ```text
    state=ACTIVE: tool=None, subagent=None
    state=DONE: tool='❯ bash:  python3 -m pytest', subagent='↳ child: 1 child done'
    state=ERROR: tool='❯ bash:  python3 -m pytest', subagent='↳ child: 1 child error'
    state=FAILED: tool='❯ bash:  python3 -m pytest', subagent='↳ child: 1 child failed'
    .............................................................            [100%]
    61 passed in 21.90s
    ```
    `git diff --stat tests/test_agy_runipd_cli.py` output: (empty).
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the new test names, `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` output, and `git diff tests/test_verifier_corroboration.py` showing only ADDED lines.
  - Observed evidence: New test names: `TestSharedToolCallExtraction::test_agy_failed_run_command_extracted_and_matches_error_verdict` and `TestSharedToolCallExtraction::test_agy_failed_then_done_pytest_corroborated_with_observed_count_two`. Output of `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` and `git diff tests/test_verifier_corroboration.py`:
    ```text
    ..................................................                       [100%]
    50 passed in 27.61s
    diff --git a/tests/test_verifier_corroboration.py b/tests/test_verifier_corroboration.py
    index 0e472f208..e213752c7 100644
    --- a/tests/test_verifier_corroboration.py
    +++ b/tests/test_verifier_corroboration.py
    @@ -1257,3 +1257,101 @@ class TestSharedToolCallExtraction:
                 res = vc.corroborate_verifier_turn(f.name, ["python3 -m pytest tests/x.py"])
                 assert res.verdict == vc.CORROBORATED
                 assert res.reason_code == vc.CORROBORATED
    +
    +    def test_agy_failed_run_command_extracted_and_matches_error_verdict(self) -> None:
    +        """E-06 (u3enlv): FAILED run_command log yields one observed command with error=True and matches ERROR verdict."""
    +        failed_ev = {
    +            "event": "step_update",
    +            "step_update": {
    +                "step_index": 1,
    +                "step_type": "tool",
    +                "state": "FAILED",
    +                "tool_name": "run_command",
    +                "tool_info": {
    +                    "name": "run_command",
    +                    "parameters": {"CommandLine": "python3 -m pytest"},
    +                },
    +            },
    +        }
    +        error_ev = {
    +            "event": "step_update",
    +            "step_update": {
    +                "step_index": 1,
    +                "step_type": "tool",
    +                "state": "ERROR",
    +                "tool_name": "run_command",
    +                "tool_info": {
    +                    "name": "run_command",
    +                    "parameters": {"CommandLine": "python3 -m pytest"},
    +                },
    +            },
    +        }
    +        with (
    +            tempfile.NamedTemporaryFile("w+", suffix=".jsonl") as f_failed,
    +            tempfile.NamedTemporaryFile("w+", suffix=".jsonl") as f_error,
    +        ):
    +            f_failed.write(json.dumps(failed_ev) + "\n")
    +            f_failed.flush()
    +            f_error.write(json.dumps(error_ev) + "\n")
    +            f_error.flush()
    +
    +            ext = vc.extract_session_commands(f_failed.name)
    +            assert len(ext.commands) == 1
    +            assert ext.commands[0].command == "python3 -m pytest"
    +            assert ext.commands[0].error is True
    +            assert ext.missing_command_count == 0
    +
    +            corr_failed = vc.corroborate_verifier_turn(
    +                f_failed.name, ["python3 -m pytest"]
    +            )
    +            corr_error = vc.corroborate_verifier_turn(
    +                f_error.name, ["python3 -m pytest"]
    +            )
    +            assert corr_failed.verdict == corr_error.verdict
    +            assert corr_failed.reason_code == corr_error.reason_code
    +            assert corr_failed.observed_count == 1
    +
    +    def test_agy_failed_then_done_pytest_corroborated_with_observed_count_two(
    +        self,
    +    ) -> None:
    +        """E-06 (u3enlv): One FAILED then one DONE pytest call with matching claim yields corroborated with observed_count == 2."""
    +        failed_ev = {
    +            "event": "step_update",
    +            "step_update": {
    +                "step_index": 1,
    +                "step_type": "tool",
    +                "state": "FAILED",
    +                "tool_name": "run_command",
    +                "tool_info": {
    +                    "name": "run_command",
    +                    "parameters": {
    +                        "CommandLine": "python3 -m pytest tests/test_fail.py"
    +                    },
    +                },
    +            },
    +        }
    +        done_ev = {
    +            "event": "step_update",
    +            "step_update": {
    +                "step_index": 2,
    +                "step_type": "tool",
    +                "state": "DONE",
    +                "tool_name": "run_command",
    +                "tool_info": {
    +                    "name": "run_command",
    +                    "parameters": {
    +                        "CommandLine": "python3 -m pytest tests/test_pass.py"
    +                    },
    +                },
    +            },
    +        }
    +        with tempfile.NamedTemporaryFile("w+", suffix=".jsonl") as f:
    +            f.write(json.dumps(failed_ev) + "\n" + json.dumps(done_ev) + "\n")
    +            f.flush()
    +            res = vc.corroborate_verifier_turn(
    +                f.name, ["python3 -m pytest tests/test_pass.py"]
    +            )
    +            assert res.verdict == vc.CORROBORATED
    +            assert res.reason_code == vc.CORROBORATED
    +            assert res.observed_count == 2
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: PASTE the new test names, `python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py` output, and `git diff tests/test_run_dashboard.py` showing only additions plus the E-04 rename.
  - Observed evidence: New test names: `TestUnifiedToolExtractionRouting::test_dashboard_failed_tool_step_e07`, `TestUnifiedToolExtractionRouting::test_dashboard_failed_agent_response_step_e07`, and `TestUnifiedToolExtractionRouting::test_dashboard_failed_error_message_step_e07`. Output of `python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py` and `git diff tests/test_run_dashboard.py`:
    ```text
    .....................                                                    [100%]
    21 passed in 1.07s
    diff --git a/tests/test_run_dashboard.py b/tests/test_run_dashboard.py
    index f8d2c7443..d168941f5 100644
    --- a/tests/test_run_dashboard.py
    +++ b/tests/test_run_dashboard.py
    @@ -585,9 +585,9 @@ class TestUnifiedToolExtractionRouting(unittest.TestCase):
             for name in ("task", "browser_subagent", "subagent", "invoke_subagent"):
                 self.assertEqual(dash.tool_category(name), "subagent")

    -    def test_dashboard_schema_version_is_4(self) -> None:
    -        """E-04 (n8we3u): DASHBOARD_SCHEMA_VERSION is 4."""
    -        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 4)
    +    def test_dashboard_schema_version_is_5(self) -> None:
    +        """E-04 (u3enlv): DASHBOARD_SCHEMA_VERSION is 5."""
    +        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 5)

         def test_dashboard_conflict_and_info_only_shapes_e10(self) -> None:
             """E-10 (n8we3u): session_stats counts tools/categories/commands correctly for CONFLICT and INFO-ONLY."""
    @@ -632,6 +632,88 @@ class TestUnifiedToolExtractionRouting(unittest.TestCase):
                 self.assertEqual(stats_info["tools"], {"run_command": 1})
                 self.assertEqual(stats_info["commands"], {"test": 1})

    +    def test_dashboard_failed_tool_step_e07(self) -> None:
    +        """E-07 (u3enlv): session_stats on a FAILED tool log counts tool_calls=1, tool_errors=1, tool_err={'run_command': 1}, commands={'test': 1} and equals ERROR twin."""
    +        with tempfile.TemporaryDirectory() as td:
    +            by_state = {}
    +            for state in ("ERROR", "FAILED"):
    +                ev = {
    +                    "event": "step_update",
    +                    "step_update": {
    +                        "step_index": 1,
    +                        "step_type": "tool",
    +                        "state": state,
    +                        "tool_name": "run_command",
    +                        "tool_info": {
    +                            "name": "run_command",
    +                            "parameters": {"CommandLine": "python3 -m pytest"},
    +                        },
    +                    },
    +                }
    +                p = Path(td) / f"tool_{state}.jsonl"
    +                p.write_text(json.dumps(ev) + "\n", encoding="utf-8")
    +                by_state[state] = dash.session_stats(p)
    +
    +            st_failed = by_state["FAILED"]
    +            self.assertEqual(st_failed["tool_calls"], 1)
    +            self.assertEqual(st_failed["tool_errors"], 1)
    +            self.assertEqual(st_failed["tool_err"], {"run_command": 1})
    +            self.assertEqual(st_failed["commands"], {"test": 1})
    +            self.assertEqual(st_failed, by_state["ERROR"])
    +
    +    def test_dashboard_failed_agent_response_step_e07(self) -> None:
    +        """E-07 (u3enlv): session_stats on a FAILED agent_response with usage counts steps=1 and tokens, equal to ERROR twin."""
    +        with tempfile.TemporaryDirectory() as td:
    +            by_state = {}
    +            for state in ("ERROR", "FAILED"):
    +                ev = {
    +                    "event": "step_update",
    +                    "step_update": {
    +                        "step_index": 1,
    +                        "step_type": "agent_response",
    +                        "state": state,
    +                        "duration_seconds": 2.5,
    +                        "usage": {
    +                            "input_tokens": 5,
    +                            "output_tokens": 3,
    +                            "thinking_tokens": 2,
    +                            "cache_read_tokens": 1,
    +                        },
    +                    },
    +                }
    +                p = Path(td) / f"ar_{state}.jsonl"
    +                p.write_text(json.dumps(ev) + "\n", encoding="utf-8")
    +                by_state[state] = dash.session_stats(p)
    +
    +            st_failed = by_state["FAILED"]
    +            self.assertEqual(st_failed["steps"], 1)
    +            self.assertEqual(st_failed["input"], 5.0)
    +            self.assertEqual(st_failed["output"], 3.0)
    +            self.assertEqual(st_failed["reasoning"], 2.0)
    +            self.assertEqual(st_failed["cache_read"], 1.0)
    +            self.assertEqual(st_failed, by_state["ERROR"])
    +
    +    def test_dashboard_failed_error_message_step_e07(self) -> None:
    +        """E-07 (u3enlv): session_stats on a FAILED error_message counts error_messages=1 and equals ERROR twin."""
    +        with tempfile.TemporaryDirectory() as td:
    +            by_state = {}
    +            for state in ("ERROR", "FAILED"):
    +                ev = {
    +                    "event": "step_update",
    +                    "step_update": {
    +                        "step_index": 1,
    +                        "step_type": "error_message",
    +                        "state": state,
    +                    },
    +                }
    +                p = Path(td) / f"em_{state}.jsonl"
    +                p.write_text(json.dumps(ev) + "\n", encoding="utf-8")
    +                by_state[state] = dash.session_stats(p)
    +
    +            st_failed = by_state["FAILED"]
    +            self.assertEqual(st_failed["error_messages"], 1)
    +            self.assertEqual(st_failed, by_state["ERROR"])
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: PASTE `python3 -m pytest -o addopts="" -q tests/test_agy_failed_state_parity.py` passing with its count. Then PROVE it detects divergence: temporarily revert `run_dashboard._agy_line`'s gate to `("DONE", "ERROR")`, re-run, PASTE the failing `FAILED` row, restore; then do the same for `verifier_corroboration.tool_call_from_event`'s gate (revert to `state != "DONE" and state != "ERROR"`), PASTE the failing `FAILED` row, restore; re-run, paste the pass, and paste `git diff --stat agent_workflows/run_dashboard.py agent_workflows/verifier_corroboration.py` matching the intended change only. FAILS if the test reads any production source text.
  - Observed evidence: Initial pass, both revert failures on `FAILED`, restored pass, and `git diff --stat`:
    ```text
    .....                                                                    [100%]
    5 passed in 2.96s

    === (2) Revert run_dashboard._agy_line gate to ('DONE', 'ERROR') ===
    exit=1
    ...F.                                                                    [100%]
    =================================== FAILURES ===================================
    _______________ test_cross_reader_agy_tool_state_parity[FAILED] ________________

    state = 'FAILED', expected_observed = True, expected_errored = True
    ...
            assert rendered_observed is expected_observed
            assert extractor_observed is expected_observed
    >       assert dashboard_observed is expected_observed
    E       assert False is True

    tests/test_agy_failed_state_parity.py:75: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_agy_failed_state_parity.py::test_cross_reader_agy_tool_state_parity[FAILED]
    1 failed, 4 passed in 0.35s

    === (3) Revert verifier_corroboration.tool_call_from_event gate to != DONE and != ERROR ===
    exit=1
    ...F.                                                                    [100%]
    =================================== FAILURES ===================================
    _______________ test_cross_reader_agy_tool_state_parity[FAILED] ________________

    state = 'FAILED', expected_observed = True, expected_errored = True
    ...
            assert rendered_observed is expected_observed
    >       assert extractor_observed is expected_observed
    E       assert False is True

    tests/test_agy_failed_state_parity.py:74: AssertionError
    =========================== short test summary info ============================
    FAILED tests/test_agy_failed_state_parity.py::test_cross_reader_agy_tool_state_parity[FAILED]
    1 failed, 4 passed in 1.54s

    === (4) Re-run parity test after restore ===
    exit=0
    .....                                                                    [100%]
    5 passed in 1.13s

     agent_workflows/run_dashboard.py          |  9 ++++++---
     agent_workflows/verifier_corroboration.py | 28 ++++++++++++++++++++++++++--
     2 files changed, 32 insertions(+), 5 deletions(-)
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: PASTE the new `DECISIONS.md` entry and `CHANGELOG.md` line, a search of that CHANGELOG line for U+2014 and U+2013 returning no match, the bare `python3 -m pytest` summary line, the sorted failing node-id list, and the `comm -13` of baseline vs post-change failing node ids showing it is EMPTY. FAILS if any new failing node id appears.
  - Observed evidence: New `DECISIONS.md` entry (`D166`), `CHANGELOG.md` line, U+2014/U+2013 search, bare `python3 -m pytest` summary line, sorted failing node-id list (empty), and `comm -13` output (empty):
    ```diff
    diff --git a/CHANGELOG.md b/CHANGELOG.md
    index 32e48c456..97f055cb0 100644
    --- a/CHANGELOG.md
    +++ b/CHANGELOG.md
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: the run dashboard and verifier corroboration now count an Antigravity tool call that ended in the FAILED state, matching what the live stream shows.
     - Added: `aw checkup` command and periodic CI health checks with configurable interval (`ci_checkup_interval_commits`, default 100), workflow (`ci_checkup_workflow`, default `tests.yml`), and branch (`ci_checkup_branch`, default `main`) in `project.json`, showing checkup status in run start and run end banners, `aw attention`, and `aw doctor`.
    diff --git a/DECISIONS.md b/DECISIONS.md
    index 0d235a793..1627914cd 100644
    --- a/DECISIONS.md
    +++ b/DECISIONS.md
    @@ -2691,3 +2691,12 @@ both execute the (large) set well.
       1. *Forbidding plan citations outright:* Rejected because it would remove the legitimate "closed by this executed plan" route protected by backlog item `7lfe87`.
       2. *Reading the plan's `- Status:` field:* Rejected because a plan stays in `pending/` through `draft`, `to-review`, `reviewed`, and `approved`, and only the disposition directory reflects execution (`runner_shared.plan_bucket` docstring, `_carrier_is_executed`).
     - **Applied:** `agent_workflows/check_engine.py` (`_evidence_plan_unshipped`, `resolve_evidence_artifact`, `evaluate_blocking_close`); `tests/test_backlog_close_evidence_plan_disposition.py`; `AGENTS.md`; `.aw/records/backlog/README.md`; `CHANGELOG.md`; `DECISIONS.md` (this entry). Executed per IPD `ncmugb` (Set `evidpend`, Order 01, backlog `7lfe87`, follow-up `bkprhk`).
    +
    +### D166. Count an Antigravity FAILED step as a terminal errored observation equal to ERROR
    +
    +- **Context:** Three Antigravity `step_update` readers answered "is `state == 'FAILED'` a finished step?" differently: `agy_runipd.render_agy_event` accepted `("DONE", "ERROR", "FAILED")` for both `tool` and `subagent` steps and mapped `"FAILED": "error"` in `_AGY_STATE_TO_STATUS`, whereas `verifier_corroboration.tool_call_from_event` gated on `state != "DONE" and state != "ERROR"` and `run_dashboard._agy_line` gated on `state not in ("DONE", "ERROR")`. For a `run_command` step with `CommandLine="python3 -m pytest"`, `DONE` yielded `ToolCall(..., error=False)`, corroboration `corroborated corroborated`, and dashboard `tool_calls=1, tool_errors=0, commands={'test': 1}`; `ERROR` yielded `ToolCall(..., error=True)`, corroboration `uncorroborated uncorroborated`, and dashboard `tool_calls=1, tool_errors=1, commands={'test': 1}`; and `FAILED` yielded `tool_call_from_event -> None`, `extract_session_commands -> commands=[], missing_command_count=0`, corroboration `indeterminate missing-command-text`, and dashboard `tool_calls=0, tool_errors=0, commands={}`, while the live renderer printed `'❯ bash:  python3 -m pytest'` for all three. In addition, `run_dashboard._agy_line` dropped `FAILED` `agent_response` and `error_message` steps (counting `steps=0, input=0.0` and `error_messages=0` vs `ERROR`'s `steps=1, input=5.0` and `error_messages=1`).
    +- **Decision:** Treat an Antigravity `FAILED` step as a terminal errored observation equal to `ERROR`, defined once in `verifier_corroboration` via `AGY_TERMINAL_STATES: tuple[str, ...] = ("DONE", "ERROR", "FAILED")` and `AGY_ERROR_STATES: tuple[str, ...] = ("ERROR", "FAILED")` (both exported in `__all__`). Route `verifier_corroboration.tool_call_from_event`, `run_dashboard._agy_line`, and both `tool` and `subagent` gates in `agy_runipd.render_agy_event` onto these shared constants, and bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` from 4 to 5 so cached dashboard entries written before `FAILED` steps were counted are invalidated.
    +  Rejected alternative:
    +  1. *Treat `FAILED` as a non-event and drop it from `render_agy_event` to match analytics:* rejected because `render_agy_event` has always accepted `FAILED` alongside `ERROR`, `_AGY_STATE_TO_STATUS` maps `FAILED` to `"error"`, `runner_stop.is_agy_safe_checkpoint` names `FAILED` a terminal non-success state, and the step carries the same `tool_info.parameters` as an `ERROR` step; hiding a failed tool call from the live operator stream would conceal real failed execution from a human watching a run.
    +- **Applied:** `agent_workflows/verifier_corroboration.py` (`AGY_TERMINAL_STATES`, `AGY_ERROR_STATES`, `tool_call_from_event`); `agent_workflows/run_dashboard.py` (`_agy_line`, `DASHBOARD_SCHEMA_VERSION = 5`); `agent_workflows/agy_runipd.py` (`render_agy_event`); `tests/test_verifier_corroboration.py`; `tests/test_run_dashboard.py`; `tests/test_agy_failed_state_parity.py`; `DECISIONS.md` (this entry); `CHANGELOG.md`. Executed per IPD `u3enlv` (Set `runverdict`, Order 13, backlog `8fiybc`).
    ```
    ```text
    added CHANGELOG lines: ['- Fixed: the run dashboard and verifier corroboration now count an Antigravity tool call that ended in the FAILED state, matching what the live stream shows.']
    U+2014 or U+2013 matches: []
    NOTE: 292 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus'); run everything with: make test-all
    8311 passed, 4 skipped, 18 xfailed, 3 warnings in 458.52s (0:07:38)
    sorted post-change failing node-id list: (empty)
    comm -13 <(printf '%s\n' "tests/test_host_capability_extension.py::InspectionVerbTests::test_the_verbs_write_nothing_to_the_repository" | sort) <(printf '' | sort)
    comm -13 exit=0
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; do not self-approve.

Open questions: OQ-01 and OQ-02 are `resolved`, none is `Blocking: yes`. The decision a maintainer may wish to overrule is OQ-01 (`FAILED` equals `ERROR`); it is recorded with its evidence so it can be disputed on the evidence.

Prerequisites: `e08ssu` (which created `tool_call_from_event`) and `n8we3u` (which bumps the same cache version, see F-06) are executed; the runner enforces both edges at dispatch. If `verifier_corroboration.tool_call_from_event` is absent at the executing HEAD, STOP and report.

Execution contract: commit only the paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`; do not push; do not create a tag or release. Paste ACTUAL runner output for every validation item. Do not fold `n8we3u`/`1kebul` or `iuhx9d` into this change. An out-of-scope edit that proves necessary should be made and then justified through `aw ipd finalize --scope-reason <path>=<why>`, with `--scope-ack` for any declared path left unmodified.

Post-gate lifecycle: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, complete the terminal transition through the tooled path. Under `aw oc run` / `aw agy run` the runner owns both `aw ipd begin` and that transition, so do not call them yourself; a human-driven execution runs `aw ipd begin u3enlv` before E-01 and then uses `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Backlog `8fiybc` then closes through the handoff (this plan carries `- From-Backlog: 8fiybc`; the item has no `- Blocks-Release:` gate, so none is inherited).
