# IPD: Count an Antigravity subagent step as a delegation so a delegating verifier turn reads indeterminate, not uncorroborated

- Date: 2026-10-12
- Kind: child
- Concern: `verifier_corroboration.tool_call_from_event` (the shared primitive `e08ssu` landed, consumed by BOTH `verifier_corroboration.extract_session_commands` and `run_dashboard._agy_line`) returns `None` for every Antigravity `step_update` whose `step_type` is not `"tool"`, so the dedicated `step_type == "subagent"` delegation shape that `agy_runipd.render_agy_event` already renders ("`if step_type == "subagent":`" reading `subagent_info.subagents`) is invisible to analytics. Measured at authoring HEAD `649280be1`: a log holding one non-test `run_command` (`ls -la`) plus one `step_type: "subagent"`, `state: "DONE"` step gives `extract_session_commands` -> `delegation_count=0`, `corroborate_verifier_turn(log, ["python3 -m pytest"])` -> `uncorroborated`/`uncorroborated`, and `run_dashboard.session_stats` -> `tool_calls=1`, `tools={'run_command': 1}`, `categories={'shell': 1}` (no `subagent`). That verdict is published on the attempt and item and rendered by `run_viewer` as `corroboration: <verdict> (reason: <reason>)`, so `aw runs` accuses a verifier that genuinely delegated its test run, contradicting the module's own fail-open contract (indeterminate reason `(d) "delegation-present"`).
- Scope: IN: add a `step_type == "subagent"` arm to `tool_call_from_event`'s Antigravity branch that returns a delegation `ToolCall` (`tool="subagent"`, `delegation=True`, no command, no path) for the SAME terminal-state tuple the `"tool"` arm accepts (the shared `verifier_corroboration.AGY_TERMINAL_STATES` / `AGY_ERROR_STATES` that sibling `u3enlv` defines, which this plan depends on); document it as a numbered DESIGN DECISION; refresh the module docstring's `delegation-present` description and its `iuhx9d` reference; add a `step_type == "subagent"` branch to `run_dashboard._agy_line` that records the call through the same primitive; bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` by one and rename its version test; add a committed fixture for the shape plus verdict-level and dashboard-level outcome tests; record a `DECISIONS.md` entry and a `CHANGELOG.md` Fixed line. OUT (reasons in Deferred): Antigravity tool-name precedence (`n8we3u` / backlog `1kebul`), any change to what a verdict DOES (D160), and any change to the live renderer.
- Scope-Paths: agent_workflows/verifier_corroboration.py, agent_workflows/run_dashboard.py, tests/test_verifier_corroboration.py, tests/test_run_dashboard.py, tests/fixtures/verifier_corroboration/agy_session_subagent_step.jsonl, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: executed:e08ssu, executed:n8we3u, executed:u3enlv
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: iuhx9d
- Blocks-Release: next
- Set: runverdict
- Order: 13
- Highest E allocated: 07
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: 0yvidi

## Workflow history
- 2026-10-14 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 0yvidi verified (set runverdict, attempt 1).
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006. Re-measured at HEAD 3e328494b: F-01 reproduces (MIXED uncorroborated uncorroborated, SUB-ONLY indeterminate missing-command-text, dashboard 1 {'run_command': 1} {'shell': 1}). Added F-07 and edges executed:n8we3u, executed:u3enlv so the subagent arm consumes u3enlv's AGY_TERMINAL_STATES (OQ-01 re-resolved); Deferred rows carry Carrier/Carrier-Declined; version-test rename moved into E-03; stale-cache case specified and revert-proved.
- 2026-10-12 to-review (aw set): Graduated from backlog iuhx9d. Re-measured at HEAD 649280be1: mixed log (non-test run_command + step_type subagent DONE) gives delegation_count=0 and verdict uncorroborated; dashboard drops the step. Narrow baseline 63 passed.

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make the shared Antigravity session reader recognise a `step_type == "subagent"` step as a delegation, so a verifier turn that delegated through that shape resolves to `indeterminate` (`delegation-present`) instead of a published `uncorroborated`, and the dashboard counts it in its own `subagent` category.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-drive the authoring measurement at the executing HEAD and record it verbatim. EDIT NO FILE IN THIS ITEM. (a) Build two temporary JSONL logs under a temp dir: MIXED (one `step_type: "tool"`, `tool_name: "run_command"`, `CommandLine: "ls -la"` step, then one `step_type: "subagent"`, `state: "DONE"`, `subagent_info: {"subagents": [{"name": "x"}]}` step) and SUB-ONLY (the subagent step alone). Paste `tool_call_from_event(<subagent event>)`, `extract_session_commands(MIXED).delegation_count`, `corroborate_verifier_turn(MIXED, ["python3 -m pytest"])` `verdict`/`reason_code`, the same for SUB-ONLY, and `run_dashboard.session_stats` `tool_calls`/`tools`/`categories` for both. (b) Paste the current value of `run_dashboard.DASHBOARD_SCHEMA_VERSION` (3 at authoring; the prerequisites `n8we3u` and `u3enlv` each bump it by one, so 5 is expected, but E-03 increments whatever value is live) and paste `verifier_corroboration.AGY_TERMINAL_STATES` and `AGY_ERROR_STATES` (defined by `u3enlv` E-02; if either is absent, STOP AND REPORT: the prerequisite has not landed). (c) Run the bare suite and record the failing NODE IDS. If (a) already shows `delegation_count >= 1` for MIXED, STOP AND REPORT: the shape has been handled elsewhere.
  - Depends on: none
  - Expected outcome: pasted transcripts reproducing F-01 (or the STOP report), the current schema version and both state constants, and the baseline failing node-id list.
  - Execution state: performed

### Task group 2: detect the shape in the shared reader and the dashboard

- [x] E-02 In `agent_workflows/verifier_corroboration.py`, extend `tool_call_from_event`'s Antigravity branch: when `step_type == "subagent"` and `state in AGY_TERMINAL_STATES` (the SAME shared constant the `"tool"` arm gates on after `u3enlv`; do not write a literal tuple, so the two arms cannot drift), return `ToolCall(tool="subagent", host="agy", command=None, path=None, seconds=<duration_seconds via _to_float>, error=(state in AGY_ERROR_STATES), delegation=True, command_missing=False)`. Return exactly ONE record per step regardless of `len(subagent_info.subagents)` (OQ-02). Every other non-`"tool"` step type still returns `None`, and the `"tool"` arm and the OpenCode branch are byte-unchanged. Add a numbered DESIGN DECISION to the function docstring citing `agy_runipd.render_agy_event`'s `step_type == "subagent"` arm and `agy_runipd`'s header ("agy's stdout stream ALREADY carries `step_type == 'subagent'` events") as the evidence the shape is real, and correct DESIGN DECISION 3's sentence "'subagent' has no in-tree occurrence outside SUBAGENT_TOOLS and CATEGORY_ORDER" so it now names this arm. Update the module docstring: item `(d) "delegation-present"` names the Antigravity `step_type == "subagent"` step alongside `browser_subagent`, and the CONTRACT block's reason (3) says the `step_type == "subagent"` gap tracked as `iuhx9d` is now detected while the observational ruling stands unchanged (other measured false positives remain, e.g. `1kebul`).
  - Depends on: E-01
  - Expected outcome: `tool_call_from_event(<subagent DONE event>)` returns a `ToolCall` with `tool='subagent'`, `host='agy'`, `delegation=True`, `error=False`; a `FAILED` subagent step returns `delegation=True`, `error=True`; MIXED gives `delegation_count == 1` and verdict `indeterminate`/`delegation-present`; SUB-ONLY gives `indeterminate`/`delegation-present`.
  - Execution state: performed

- [x] E-03 In `agent_workflows/run_dashboard.py`, add an `elif stype == "subagent":` branch to `_agy_line` that obtains its record from `tool_call_from_event(obj)` and passes it to `_record_tool` exactly as the `"tool"` branch does (no new parsing in the dashboard). Increment `DASHBOARD_SCHEMA_VERSION` by one from the value E-01(b) recorded, because `_StatsCache` keys entries by `(size, mtime_ns)` and gates the cache on `raw.get("schema") == DASHBOARD_SCHEMA_VERSION`, so an unchanged log containing a subagent step would otherwise be served its stale count (same rule `e08ssu` OQ-02 applied). In the same item rename the existing `tests/test_run_dashboard.py::test_dashboard_schema_version_is_<N>` to the new value (docstring citing `0yvidi`), because that test pins the constant and E-03 alone would otherwise leave the suite red until E-05. Change no other dashboard logic: in particular the new branch inherits the `_agy_line` state gate, which after `u3enlv` is `AGY_TERMINAL_STATES`.
  - Depends on: E-02
  - Expected outcome: `session_stats(MIXED)` reports `tool_calls == 2`, `tools == {'run_command': 1, 'subagent': 1}`, `categories` containing `'subagent': 1`, `commands` unchanged from E-01; the schema version is one higher than E-01(b); the renamed version test passes.
  - Execution state: performed

### Task group 3: pin the outcome with a fixture and tests

- [x] E-04 Add the committed fixture `tests/fixtures/verifier_corroboration/agy_session_subagent_step.jsonl` in the style of `agy_session_three_categories.jsonl` (an `init` event with `"session_id":"ses_<redacted>"`, a `user_input` step, one `run_command` step with a non-test `CommandLine` such as `git status`, one `step_type: "subagent"` `DONE` step with `subagent_info.subagents` of length 1, and an `agent_response` step). In `tests/test_verifier_corroboration.py` ADD (do not edit existing cases): (1) `extract_session_commands(fixture)` gives `delegation_count == 1` and one observed command; (2) `corroborate_verifier_turn(fixture, ["python3 -m pytest"])` gives `verdict == "indeterminate"` and `reason_code == "delegation-present"`; (3) a CONTROL built at test time from the fixture's lines with the subagent step removed gives `uncorroborated`, proving the fixture would otherwise be an accusation; (4) `tool_call_from_event` returns `delegation=True` with `error=True` for a subagent step in `ERROR` and in `FAILED` state, and returns `None` for a subagent step in `ACTIVE` state, for an unknown `CANCELED` state, and for a `step_type: "agent_response"` step. The expected per-state outcome is a LITERAL table in the test, not derived from `AGY_TERMINAL_STATES`, so a wrong constant fails the test rather than redefining the oracle (same rule `u3enlv` E-08 applies).
  - Depends on: E-02
  - Expected outcome: the four new cases pass; every pre-existing case passes unedited.
  - Execution state: performed

- [x] E-05 In `tests/test_run_dashboard.py` ADD two cases (the schema-version rename is E-03's). (1) `session_stats` on the E-04 fixture counts `tools['subagent'] == 1`, `categories['subagent'] == 1`, and `commands` holding only the non-test command's kind. (2) A stale-cache case driven through `collect_rows`: place the fixture content as an agy session under a run built with the file's existing `_write_run(..., host="agy")` helper, write a cache file whose `schema` is `DASHBOARD_SCHEMA_VERSION - 1` and whose entry for that session carries the CURRENT `[size, mtime_ns]` stamp but stale stats (e.g. `tool_calls: 99`), call `collect_rows([run], cache_path=<file>)`, and assert `cache_hits == 0`, `cache_misses >= 1`, and the session row's `t_subagent == 1` and `tool_calls == 2`. Measured at review with a stand-in subagent arm: previous-schema cache -> `hits 0, misses 1, tool_calls [1]` on the unpatched dashboard; same-schema cache -> `hits 1, misses 0, tool_calls [99]`, which is the stale serve the bump prevents.
  - Depends on: E-03, E-04
  - Expected outcome: both new cases pass; no pre-existing test is edited by this item.
  - Execution state: performed

### Task group 4: record and run the suite

- [x] E-06 Add the next free `### D<n>` to `DECISIONS.md` (D163 is already taken at review HEAD by "Rename/regroup citation rewriting skips and reports in-flight plans", and `n8we3u` and `u3enlv` each add one first, so read the last heading and use the next free number) with Context (F-01's measured verdict), Decision (an agy `step_type == "subagent"` step is a delegation in the shared reader; one record per step; the same `AGY_TERMINAL_STATES` the `"tool"` arm uses), the rejected alternative (counting one delegation per entry in `subagent_info.subagents`) with its reason, a note that D160 reason (3)'s example is now fixed while D160's ruling is unchanged, and Applied (files). Add one `CHANGELOG.md` line in the pending release's Fixed list, without em or en dashes, e.g. "Fixed: an Antigravity verifier turn that hands work to a subagent is now reported as indeterminate in `aw runs` instead of uncorroborated, and the run dashboard counts that handoff in its subagent column."
  - Depends on: E-02, E-03
  - Expected outcome: one new DECISIONS entry and one CHANGELOG line.
  - Execution state: performed

- [x] E-07 Run the full suite BARE (`python3 -m pytest`) and compare failing NODE IDS against E-01's baseline.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: no failing node id absent from the baseline; the new tests are among the passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `verifier_corroboration` is stdlib-only and imports nothing from `agent_workflows`; this plan adds no import.
- `tool_call_from_event` records each resolved disagreement as a numbered DESIGN DECISION in its docstring (`e08ssu` E-02..E-04); this plan adds one in the same place.
- A change to cached dashboard values for an unchanged log requires a `DASHBOARD_SCHEMA_VERSION` bump (`run_dashboard._StatsCache`, `e08ssu` OQ-02).
- Corroboration is observational and refuses nothing (D160, spec `25kzda` Section 5.1); this plan changes which verdict is computed for one shape, not what consumes it.
- Fixtures under `tests/fixtures/verifier_corroboration/` redact session ids as `ses_<redacted>`.
- Tests drive real functions and assert outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Run the suite bare: `python3 -m pytest`; narrowed runs use `python3 -m pytest -o addopts="" -q <files>`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Location | Finding | Evidence |
|---|---|---|---|---|
| F-01 | HIGH | `verifier_corroboration.tool_call_from_event`, `corroborate_verifier_turn` | THE BACKLOG ITEM'S CONSEQUENCE REPRODUCES AT THE VERDICT, not only the count. MIXED log (non-test `ls -la` + subagent step): `delegation_count=0`, verdict `uncorroborated uncorroborated`. SUB-ONLY log: `indeterminate missing-command-text` (correct class, wrong reason). | Transcript at `649280be1`: `tcfe: None`, `extract: 0 ['ls -la'] agy`, `mixed verdict: uncorroborated uncorroborated 0`, `sub-only verdict: indeterminate missing-command-text`. |
| F-02 | MED | `run_dashboard._agy_line` | The dashboard drops the step entirely: `_agy_line` dispatches only on `agent_response`, `tool`, `error_message`, so even a fixed `tool_call_from_event` would not reach it without a new branch. | Transcript: `dash: 1 {'run_command': 1} {'shell': 1}`; `dash2: 0 {} {}`. `_agy_line` source branches `if stype == "agent_response"` / `elif stype == "tool"` / `elif stype == "error_message"`. |
| F-03 | MED | `run_dashboard.DASHBOARD_SCHEMA_VERSION` | Value is 3 and pinned by `tests/test_run_dashboard.py::test_dashboard_schema_version_is_3`; approved siblings `n8we3u` E-04 and `u3enlv` E-04 each bump it by one. This plan now depends on both (`- Item-Dependencies:`), so it executes last and takes the next value, hence E-03's "increment from current" wording. | `DASHBOARD_SCHEMA_VERSION = 3`; `n8we3u` E-04 and `u3enlv` E-04 text. |
| F-07 | MED | `verifier_corroboration.tool_call_from_event` state gate; sibling `u3enlv` | Approved sibling `u3enlv` (backlog `8fiybc`) replaces the agy `(DONE, ERROR)` tuple with shared `AGY_TERMINAL_STATES = ("DONE", "ERROR", "FAILED")` / `AGY_ERROR_STATES` and routes `_agy_line`'s gate onto it. A subagent arm written with a literal `DONE`/`ERROR` tuple would become the very third, inconsistent tuple OQ-01 sought to avoid, and `8fiybc` would close without ever covering this arm. Hence the dependency on `u3enlv` and E-02's use of the shared constants. | `u3enlv` Scope and E-02..E-04 (Status `approved`, no edge to this plan). Added at review. |
| F-04 | LOW | fixtures | No committed fixture contains the shape: `rg 'step_type.*subagent' tests` matches only a `"step_type":"tool"` + `tool_name: browser_subagent` line in `agy_session_three_categories.jsonl`. | `grep -rn 'step_type.*subagent' tests` output at authoring. |
| F-05 | INFO | consumers | `tool_call_from_event` and `extract_session_commands` have no other in-package consumer than `run_dashboard` and `verifier_corroboration` itself, so the new arm reaches exactly the two analytics readers. | `grep -rn "tool_call_from_event\|extract_session_commands" agent_workflows` -> only `run_dashboard.py` lines importing/calling `tool_call_from_event`. |
| F-06 | INFO | baseline | Narrow baseline: `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py tests/test_run_dashboard.py` -> `63 passed in 19.89s`. Full-suite baseline is taken by E-01(c) at execution, compared by node id. | Run in this lane at authoring. |

## Proposed changes (ordered, validatable)

1. Re-measure (E-01).
2. Add the `step_type == "subagent"` delegation arm to `tool_call_from_event`, with docstring decisions (E-02).
3. Route the shape into `run_dashboard._agy_line`; bump the schema version (E-03).
4. Fixture plus verdict tests (E-04); dashboard and cache tests (E-05).
5. DECISIONS + CHANGELOG (E-06); full suite (E-07).

## Deferred / out of scope (with reason)

- Antigravity tool-name precedence (`tool_info.name` vs `tool_name`): backlog `1kebul` / plan `n8we3u`; a different gate (name, not step type). The two plans edit the same function's different arms; this plan is ordered after `n8we3u` by its `- Item-Dependencies:` edge so the schema bump and DESIGN DECISION numbering are sequential.
  - Carrier: n8we3u
  - Carrier-Evidence: .aw/records/plans/executed/20261011-runverdict-12-n8we3u-resolve-the-antigravity-tool-name-through-one-shared-precede.ipd.md
- What a verdict does: D160 rules it observational; untouched.
  - Carrier-Declined: settled by D160; changing what the verdict does is not desired work.
- `agy_runipd.render_agy_event`, `agy_view`, `runner_stop`: they already render or label the shape, and this bug is about analytics only.
  - Carrier-Declined: nothing is owed; the live readers already handle `step_type == "subagent"`.

(The agy `FAILED` state is no longer deferred: `u3enlv` defines the shared state constants and this plan's subagent arm consumes them, see F-07.)

## Scope check

- Over-scope: none. Each Scope-Path is the reader that misses the shape, the dashboard that consumes it plus its cache version, the tests and fixture pinning it, or the decision record.
- Under-scope: none known; F-05 shows no other analytics consumer.

## Required tests / validation

- `python3 -m pytest` BARE; compare failing NODE IDS with E-01's baseline.
- New cases in `tests/test_verifier_corroboration.py` pin `indeterminate`/`delegation-present` on the fixture and `uncorroborated` on the control (E-04).
- New cases in `tests/test_run_dashboard.py` pin the `subagent` category count and the stale-cache miss (E-05).
- Every pre-existing case in both files passes unedited except the schema-version test (renamed in E-03).
- Revert proofs: V-04 (the subagent arm) and V-05 (the cache bump) each show the new test failing without the change.
- `aw ipd lint --phase pre-transition` conforming before the terminal transition.

## Spec / documentation sync

- Specs: N/A with reason. Spec `25kzda` Section 5.1 cites "Antigravity subagent delegations, bug `iuhx9d`" only as an EXAMPLE of measured false positives justifying the observational rule; the rule stands independently (other false positives remain, `1kebul`), so the spec stays correct as a historical justification and no `.spec.md` is in `Scope-Paths`.
- `DECISIONS.md`: new entry (E-06); D160 itself is not rewritten.
- `CHANGELOG.md`: one Fixed line, no em or en dashes (E-06).
- Module docstring of `verifier_corroboration` refreshed (E-02).

## Open questions

### OQ-01: Should the subagent arm accept `FAILED` as the live renderer does?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED AT REVIEW (superseding the author's "no"), yes, by consuming the shared constants rather than choosing a tuple here. The author's principle stands (one tuple across every agy arm), but approved sibling `u3enlv` (from backlog `8fiybc`) now owns that tuple as `verifier_corroboration.AGY_TERMINAL_STATES` / `AGY_ERROR_STATES` and does NOT touch a subagent arm in the analytics readers (it defers `iuhx9d` to this plan). So the only way to keep one tuple is for this plan to depend on `u3enlv` and gate on `AGY_TERMINAL_STATES`; a literal `DONE`/`ERROR` here would become the third tuple once `u3enlv` lands. A `FAILED` subagent step is therefore a delegation with `error=True`, matching `u3enlv` OQ-01 (FAILED is an errored terminal observation, as `agy_runipd._AGY_STATE_TO_STATUS` maps it). Recorded as review decision D-1.

### OQ-02: One delegation per step, or one per entry in `subagent_info.subagents`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, one per step. The verdict needs only `delegation_count > 0`, so the count does not change any verdict; `tool_call_from_event` returns a single record per event by contract (`e08ssu` E-01); and the dashboard counts tool CALLS, where a subagent step is one call. `render_agy_event` uses the list length only for display text.

### OQ-03: Which tool name should the record carry?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, `"subagent"`. It is already in `SUBAGENT_TOOLS` and maps to category `subagent` in `run_dashboard.TOOL_CATEGORIES`, so no vocabulary changes and the dashboard's `subagent` column counts it.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the full transcript of E-01(a) showing `None`, `delegation_count` 0, `uncorroborated uncorroborated` for MIXED and `indeterminate missing-command-text` for SUB-ONLY, and the dashboard counts (or the STOP report); paste the schema version value and the two `AGY_*_STATES` constants; paste the bare-suite summary line and sorted failing node-id list. FAILS if any value is paraphrased.
  - Observed evidence:
```
tool_call_from_event(<subagent event>): None
extract_session_commands(MIXED).delegation_count: 0
corroborate_verifier_turn(MIXED): verdict= uncorroborated reason_code= uncorroborated
extract_session_commands(SUB-ONLY).delegation_count: 0
corroborate_verifier_turn(SUB-ONLY): verdict= indeterminate reason_code= missing-command-text
run_dashboard.session_stats(MIXED): tool_calls= 1 tools= {'run_command': 1} categories= {'shell': 1}
run_dashboard.session_stats(SUB-ONLY): tool_calls= 0 tools= {} categories= {}
DASHBOARD_SCHEMA_VERSION: 5
AGY_TERMINAL_STATES: ('DONE', 'ERROR', 'FAILED')
AGY_ERROR_STATES: ('ERROR', 'FAILED')

Bare-suite summary line:
8357 passed, 4 skipped, 18 xfailed, 3 warnings in 584.51s (0:09:44)
Sorted failing node-id list:
(empty)
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the `git diff agent_workflows/verifier_corroboration.py` (new arm, new DESIGN DECISION, corrected decision 3, module docstring edits) and a transcript re-running E-01(a) showing `ToolCall(tool='subagent', host='agy', ..., delegation=True, ...)`, a `FAILED` subagent step giving `delegation=True, error=True`, MIXED `delegation_count 1` and `indeterminate delegation-present`, SUB-ONLY `indeterminate delegation-present`. The diff must show the new arm gating on `AGY_TERMINAL_STATES`/`AGY_ERROR_STATES` and no literal state tuple. Paste `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` BEFORE E-04 adds cases, all passing unedited.
  - Observed evidence:
```
git diff agent_workflows/verifier_corroboration.py:
diff --git a/agent_workflows/verifier_corroboration.py b/agent_workflows/verifier_corroboration.py
index 5a7870f7d..eb85d8ef5 100644
--- a/agent_workflows/verifier_corroboration.py
+++ b/agent_workflows/verifier_corroboration.py
@@ -29,9 +29,9 @@ alter any item disposition, verification status, or integration decision (such a
     make an outcome MORE permissive and explicitly forbids using an observation to
     disbelieve the agent; a corroboration refusal is the forbidden sign.
 (3) The extraction predicate has known false positives that make it unsafe to strand a
-    lane on: specifically, the Antigravity `step_type == "subagent"` delegation shape
-    is unobserved by the reader, causing genuine test delegations to resolve to
-    `uncorroborated` (tracked as bug `iuhx9d`).
+    lane on: while the Antigravity `step_type == "subagent"` delegation gap tracked as
+    bug `iuhx9d` is now detected, the observational ruling stands unchanged (other
+    measured false positives remain, e.g. `1kebul`).
 IMPERATIVE: A future consumer may read this verdict and may make an outcome MORE
 permissive on it, but MUST NOT refuse, downgrade, or change a disposition on it. A
 reader who believes a refusal is warranted opens a new decision rather than wiring
@@ -50,9 +50,9 @@ The turn-level corroboration verdict is partitioned into a closed set of conditi
        or cannot be read due to filesystem/OS permissions.
    (b) "log-empty": The session log exists but contains zero valid JSON event lines.
    (c) "claims-empty": The list of claimed test commands is empty.
-   (d) "delegation-present": The turn delegated work to a subagent (`task` on OpenCode
-       or `browser_subagent` on Antigravity). Subagent tool calls do not appear in the
-       parent session log, making commands unobservable.
+   (d) "delegation-present": The turn delegated work to a subagent (`task` on OpenCode,
+       or `browser_subagent` or a `step_type == "subagent"` step on Antigravity). Subagent
+       tool calls do not appear in the parent session log, making commands unobservable.
    (e) "missing-command-text": Shell calls were executed, but every shell call lacked
        command text (or no shell command text was observable).
    (f) "indirection-unresolved": An observed command is an unresolved indirection
@@ -393,8 +393,9 @@ def tool_call_from_event(obj: Any) -> ToolCall | None:
        - 'invoke_subagent' is referenced in-tree as a real Antigravity tool name
          (stall_progress lists 'invoke_subagent' alongside 'schedule' and 'manage_task'
          as tool names that start background tasks, and its docstring cites it).
-       - 'subagent' has no in-tree occurrence outside SUBAGENT_TOOLS and CATEGORY_ORDER.
-       - Neither appears in committed fixtures, which use only 'task' and
+       - 'subagent' had no in-tree occurrence outside SUBAGENT_TOOLS and CATEGORY_ORDER
+         until 0yvidi added the Antigravity `step_type == "subagent"` delegation arm.
+       - Neither appears in committed fixtures prior to 0yvidi, which used only 'task' and
          'browser_subagent'. This is a consistency fix backed by one in-tree reference.

     4. Antigravity Tool Name and Fail-Open Delegation (n8we3u, resolving 1kebul):
@@ -419,6 +420,20 @@ def tool_call_from_event(obj: Any) -> ToolCall | None:
        (b) Treating `FAILED` as a terminal errored observation reconciles `tool_call_from_event`,
            `run_dashboard._agy_line`, and `agy_runipd.render_agy_event` onto one shared
            vocabulary without hiding failed tool calls from the operator or analytics.
+
+    6. Antigravity Subagent Delegation Step (0yvidi, resolving iuhx9d):
+       An Antigravity `step_update` with `step_type == "subagent"` and
+       `state in AGY_TERMINAL_STATES` returns a delegation `ToolCall`
+       (`tool="subagent"`, `host="agy"`, `command=None`, `path=None`,
+       `seconds=_to_float(su.get("duration_seconds"))`, `error=(state in AGY_ERROR_STATES)`,
+       `delegation=True`, `command_missing=False`). Exactly one record is returned
+       per step regardless of `len(subagent_info.subagents)` (OQ-02).
+       Evidence:
+       `agy_runipd.render_agy_event` already contains a `step_type == "subagent"` arm
+       reading `subagent_info.subagents`, and `agy_runipd`'s header explicitly notes that
+       "agy's stdout stream ALREADY carries `step_type == 'subagent'` events". The shape
+       is real and unobserved by the reader, causing genuine test delegations to resolve
+       to `uncorroborated`.
     """
     if not isinstance(obj, (dict, Mapping)):
         return None
@@ -429,7 +444,20 @@ def tool_call_from_event(obj: Any) -> ToolCall | None:
             return None
         state = su.get("state")
         stype = su.get("step_type")
-        if state not in AGY_TERMINAL_STATES or stype != "tool":
+        if state not in AGY_TERMINAL_STATES:
+            return None
+        if stype == "subagent":
+            return ToolCall(
+                tool="subagent",
+                host="agy",
+                command=None,
+                path=None,
+                seconds=_to_float(su.get("duration_seconds")),
+                error=(state in AGY_ERROR_STATES),
+                delegation=True,
+                command_missing=False,
+            )
+        if stype != "tool":
             return None
         tool_name = agy_tool_name(su)
         is_error = state in AGY_ERROR_STATES

Transcript:
tool_call_from_event(<subagent DONE event>): ToolCall(tool='subagent', host='agy', command=None, path=None, seconds=2.0, error=False, delegation=True, command_missing=False)
tool_call_from_event(<subagent FAILED event>): ToolCall(tool='subagent', host='agy', command=None, path=None, seconds=3.0, error=True, delegation=True, command_missing=False)
extract_session_commands(MIXED).delegation_count: 1
corroborate_verifier_turn(MIXED): verdict= indeterminate reason_code= delegation-present
extract_session_commands(SUB-ONLY).delegation_count: 1
corroborate_verifier_turn(SUB-ONLY): verdict= indeterminate reason_code= delegation-present

Pytest output before E-04 additions:
$ python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py
..................................................                       [100%]
50 passed in 7.19s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the `git diff agent_workflows/run_dashboard.py` showing only the new `_agy_line` branch and the schema increment, the `git diff tests/test_run_dashboard.py` showing only the version-test rename/value, `session_stats(MIXED)` output with `tool_calls 2`, `tools {'run_command': 1, 'subagent': 1}`, `categories` containing `'subagent': 1`, and `python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py` passing.
  - Observed evidence:
```
git diff agent_workflows/run_dashboard.py:
diff --git a/agent_workflows/run_dashboard.py b/agent_workflows/run_dashboard.py
index 2924745bb..a75daac89 100644
--- a/agent_workflows/run_dashboard.py
+++ b/agent_workflows/run_dashboard.py
@@ -55,7 +55,7 @@ __all__ = [
     "render_dashboard",
 ]

-DASHBOARD_SCHEMA_VERSION = 5
+DASHBOARD_SCHEMA_VERSION = 6
 ASSETS_DIRNAME = "run_dashboard_assets"
 STATS_CACHE_FILENAME = "dashboard-session-stats.json"
 UNRECORDED = "(unrecorded)"
@@ -349,6 +349,19 @@ def _agy_line(
                 read_paths=read_paths,
                 edit_paths=edit_paths,
             )
+    elif stype == "subagent":
+        tc = tool_call_from_event(obj)
+        if tc is not None:
+            _record_tool(
+                stats,
+                tc.tool,
+                error=tc.error,
+                seconds=tc.seconds,
+                command=tc.command,
+                path=tc.path,
+                read_paths=read_paths,
+                edit_paths=edit_paths,
+            )
     elif stype == "error_message":
         stats["error_messages"] += 1

git diff tests/test_run_dashboard.py (version test rename/value):
@@ -588,4 +588,4 @@
-    def test_dashboard_schema_version_is_5(self) -> None:
-        """E-04 (u3enlv): DASHBOARD_SCHEMA_VERSION is 5."""
-        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 5)
+    def test_dashboard_schema_version_is_6(self) -> None:
+        """E-03 (0yvidi): DASHBOARD_SCHEMA_VERSION is 6."""
+        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 6)

session_stats(MIXED) output:
tool_calls: 2
tools: {'run_command': 1, 'subagent': 1}
categories: {'shell': 1, 'subagent': 1}
commands: {'inspect': 1}

$ python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py
.....................                                                    [100%]
21 passed in 0.82s
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the fixture content, the new test function names, and `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` output; paste `git diff tests/test_verifier_corroboration.py` showing only added lines. Then temporarily revert the E-02 arm, re-run the file, PASTE the failing new cases (the verdict case must fail with `uncorroborated`), restore, re-run passing, and paste `git diff --stat` showing no residue.
  - Observed evidence:
```
Fixture content (tests/fixtures/verifier_corroboration/agy_session_subagent_step.jsonl):
{"event":"init","init":{"session_id":"ses_<redacted>","tools":[]}}
{"event":"step_update","step_update":{"step_index":0,"state":"DONE","step_type":"user_input"}}
{"event":"step_update","step_update":{"step_index":1,"state":"DONE","step_type":"tool","tool_name":"run_command","duration_seconds":0.5,"tool_info":{"parameters":{"CommandLine":"git status"}}}}
{"event":"step_update","step_update":{"step_index":2,"state":"DONE","step_type":"subagent","duration_seconds":2.0,"subagent_info":{"subagents":[{"name":"worker"}]}}}
{"event":"step_update","step_update":{"step_index":3,"state":"DONE","step_type":"agent_response","duration_seconds":1.0,"usage":{"input_tokens":100,"output_tokens":10,"thinking_tokens":0,"cache_read_tokens":50}}}

New test function names:
- test_extract_session_commands_agy_subagent_step_fixture
- test_corroborate_verifier_turn_agy_subagent_step_fixture
- test_control_without_subagent_step_resolves_uncorroborated
- test_tool_call_from_event_subagent_step_literal_state_table
- test_tool_call_from_event_agent_response_returns_none

$ python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py
...........................................................              [100%]
59 passed in 8.00s

git diff tests/test_verifier_corroboration.py:
84 insertions(+), 0 deletions(-)

Revert proof (temporarily disabling E-02 subagent arm):
FAILED tests/test_verifier_corroboration.py::TestSharedToolCallExtraction::test_tool_call_from_event_subagent_step_literal_state_table[DONE-expected_tc0]
FAILED tests/test_verifier_corroboration.py::TestSharedToolCallExtraction::test_tool_call_from_event_subagent_step_literal_state_table[FAILED-expected_tc2]
FAILED tests/test_verifier_corroboration.py::TestSharedToolCallExtraction::test_extract_session_commands_agy_subagent_step_fixture
FAILED tests/test_verifier_corroboration.py::TestSharedToolCallExtraction::test_corroborate_verifier_turn_agy_subagent_step_fixture
FAILED tests/test_verifier_corroboration.py::TestSharedToolCallExtraction::test_tool_call_from_event_subagent_step_literal_state_table[ERROR-expected_tc1]
5 failed, 54 passed in 7.35s

test_corroborate_verifier_turn_agy_subagent_step_fixture failure:
AssertionError: assert 'uncorroborated' == 'indeterminate'
  - indeterminate
  + uncorroborated

Restored and re-run:
59 passed in 8.01s

git diff --stat: no residue on agent_workflows/verifier_corroboration.py beyond E-02 change.
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the new test names (non-binding pointers) and `python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py` output; paste the E-05 portion of `git diff tests/test_run_dashboard.py` showing only added lines. The stale-cache case exercises `run_dashboard._StatsCache` through `collect_rows`; paste its assertion lines (`cache_hits == 0`, the row's `t_subagent == 1`). Then temporarily set the cache file's `schema` in the test to the CURRENT value, re-run, PASTE the failure (stale `tool_calls` served), restore, and paste `git diff --stat` showing no residue.
  - Observed evidence:
```
New test names:
- test_dashboard_subagent_step_fixture_counts
- test_dashboard_stale_cache_invalidated_by_schema_version_bump

$ python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py
.......................                                                  [100%]
23 passed in 0.69s

E-05 portion of git diff tests/test_run_dashboard.py:
+    def test_dashboard_subagent_step_fixture_counts(self) -> None:
+        """E-05 (0yvidi): session_stats on E-04 fixture counts subagent tool, category, and non-test command."""
...
+    def test_dashboard_stale_cache_invalidated_by_schema_version_bump(self) -> None:
+        """E-05 (0yvidi): StatsCache with schema DASHBOARD_SCHEMA_VERSION - 1 is invalidated, re-parsing session."""
...
+            rows, info = dash.collect_rows([run], cache_path=cache_file)
+            self.assertEqual(info["cache_hits"], 0)
+            self.assertGreaterEqual(info["cache_misses"], 1)
+            self.assertEqual(len(rows), 1)
+            row = rows[0]
+            self.assertEqual(row["t_subagent"], 1)
+            self.assertEqual(row["tool_calls"], 2)

Assertion lines:
self.assertEqual(info["cache_hits"], 0)
self.assertEqual(row["t_subagent"], 1)

Revert proof (setting schema to CURRENT in test cache):
FAILED tests/test_run_dashboard.py::TestUnifiedToolExtractionRouting::test_dashboard_stale_cache_invalidated_by_schema_version_bump
AssertionError: 1 != 0 (cache_hits == 1, serving stale tool_calls: 99)

Restored and re-run:
23 passed in 0.69s

git diff --stat: no residue on tests/test_run_dashboard.py beyond E-03 and E-05.
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the new `DECISIONS.md` entry and the `CHANGELOG.md` line, plus a search of that line for U+2014 and U+2013 returning no match.
  - Observed evidence:
```
DECISIONS.md entry:
### D167. Count an Antigravity subagent step as a delegation across analytics readers

- **Context:** The shared Antigravity session reader `verifier_corroboration.tool_call_from_event` returned `None` for every `step_update` whose `step_type` was not `"tool"`, ignoring `step_type == "subagent"` steps that `agy_runipd.render_agy_event` already rendered as child delegations. In a session log holding one non-test `run_command` (`ls -la`) and one `step_type: "subagent"`, `state: "DONE"` step, `extract_session_commands` reported `delegation_count=0`, resolving `corroborate_verifier_turn` against claimed test commands to `uncorroborated` (reason: `uncorroborated`) instead of `indeterminate` (reason: `delegation-present`), and `run_dashboard.session_stats` dropped the step entirely (`tool_calls=1`, `tools={'run_command': 1}`, `categories={'shell': 1}`). This produced a false accusation against verifiers that legitimately delegated test runs to subagents.
- **Decision:** Recognize an Antigravity `step_type == "subagent"` step in `tool_call_from_event` as a delegation `ToolCall` (`tool="subagent"`, `host="agy"`, `delegation=True`, `seconds=duration_seconds`, `error=(state in AGY_ERROR_STATES)`) using the same `AGY_TERMINAL_STATES` constant as the `"tool"` arm. Route the shape into `run_dashboard._agy_line` via the same primitive and bump `DASHBOARD_SCHEMA_VERSION` from 5 to 6 so unchanged logs containing subagent steps are invalidated. Return exactly one record per step. Note that D160 reason (3)'s cited example (the `step_type == "subagent"` gap tracked as `iuhx9d`) is now detected while D160's observational ruling stands unchanged (other measured false positives remain, e.g. `1kebul`).
  Rejected alternative:
  1. *Counting one delegation per entry in `subagent_info.subagents`:* rejected because the verdict predicate needs only `delegation_count > 0` to fail open, `tool_call_from_event` returns exactly one record per event by contract, and the dashboard counts tool calls, where one subagent step update is one invocation regardless of how many child workers it spins up.
- **Applied:** `agent_workflows/verifier_corroboration.py` (`tool_call_from_event`); `agent_workflows/run_dashboard.py` (`_agy_line`, `DASHBOARD_SCHEMA_VERSION = 6`); `tests/test_verifier_corroboration.py`; `tests/test_run_dashboard.py`; `tests/fixtures/verifier_corroboration/agy_session_subagent_step.jsonl`; `DECISIONS.md` (this entry); `CHANGELOG.md`. Executed per IPD `0yvidi` (Set `runverdict`, Order 13, backlog `iuhx9d`).

CHANGELOG.md line:
- Fixed: an Antigravity verifier turn that hands work to a subagent is now reported as indeterminate in `aw runs` instead of uncorroborated, and the run dashboard counts that handoff in its subagent column.

Dash search result:
Contains U+2014 or U+2013: False
```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: PASTE the bare `python3 -m pytest` summary line, the sorted failing node-id list, and the `comm -13` of baseline vs post-change failing ids showing it is EMPTY. FAILS if a new failing id appears.
  - Observed evidence:
```
Bare `python3 -m pytest` summary line:
8368 passed, 4 skipped, 18 xfailed, 3 warnings in 433.64s (0:07:13)

Sorted failing node-id list:
(empty)

comm -13 of baseline vs post-change failing ids:
(empty)
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; do not self-approve.

Open questions: OQ-01..OQ-03 are `resolved`, none is `Blocking: yes`.

Prerequisites: `e08ssu`, `n8we3u`, and `u3enlv` are executed (`- Item-Dependencies:`), so `verifier_corroboration.tool_call_from_event`, `AGY_TERMINAL_STATES`, and `AGY_ERROR_STATES` exist; if any is absent at the executing HEAD, STOP and report.

Execution contract: commit only the paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`; do not push; do not create a tag or release. Paste ACTUAL runner output for every validation item. Do not fold `n8we3u`/`1kebul` or `u3enlv`/`8fiybc` work into this change beyond consuming their landed constants. An out-of-scope edit that proves necessary should be made and then justified through `aw ipd finalize --scope-reason <path>=<why>`, with `--scope-ack` for any declared path left unmodified.

Post-gate lifecycle: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, complete the terminal transition through the tooled path. Under `aw oc run` / `aw agy run` the runner owns both `aw ipd begin` and that transition, so do not call them yourself; a human-driven execution runs `aw ipd begin 0yvidi` before E-01 and then uses `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Backlog `iuhx9d` then closes through the handoff (this plan carries `- From-Backlog: iuhx9d` and the same `- Blocks-Release: next`).
