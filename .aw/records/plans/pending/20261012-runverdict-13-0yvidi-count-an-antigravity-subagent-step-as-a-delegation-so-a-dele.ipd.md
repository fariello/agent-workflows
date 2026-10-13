# IPD: Count an Antigravity subagent step as a delegation so a delegating verifier turn reads indeterminate, not uncorroborated

- Date: 2026-10-12
- Kind: child
- Concern: `verifier_corroboration.tool_call_from_event` (the shared primitive `e08ssu` landed, consumed by BOTH `verifier_corroboration.extract_session_commands` and `run_dashboard._agy_line`) returns `None` for every Antigravity `step_update` whose `step_type` is not `"tool"`, so the dedicated `step_type == "subagent"` delegation shape that `agy_runipd.render_agy_event` already renders ("`if step_type == "subagent":`" reading `subagent_info.subagents`) is invisible to analytics. Measured at authoring HEAD `649280be1`: a log holding one non-test `run_command` (`ls -la`) plus one `step_type: "subagent"`, `state: "DONE"` step gives `extract_session_commands` -> `delegation_count=0`, `corroborate_verifier_turn(log, ["python3 -m pytest"])` -> `uncorroborated`/`uncorroborated`, and `run_dashboard.session_stats` -> `tool_calls=1`, `tools={'run_command': 1}`, `categories={'shell': 1}` (no `subagent`). That verdict is published on the attempt and item and rendered by `run_viewer` as `corroboration: <verdict> (reason: <reason>)`, so `aw runs` accuses a verifier that genuinely delegated its test run, contradicting the module's own fail-open contract (indeterminate reason `(d) "delegation-present"`).
- Scope: IN: add a `step_type == "subagent"` arm to `tool_call_from_event`'s Antigravity branch that returns a delegation `ToolCall` (`tool="subagent"`, `delegation=True`, no command, no path) for the SAME terminal-state tuple the `"tool"` arm accepts (the shared `verifier_corroboration.AGY_TERMINAL_STATES` / `AGY_ERROR_STATES` that sibling `u3enlv` defines, which this plan depends on); document it as a numbered DESIGN DECISION; refresh the module docstring's `delegation-present` description and its `iuhx9d` reference; add a `step_type == "subagent"` branch to `run_dashboard._agy_line` that records the call through the same primitive; bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` by one and rename its version test; add a committed fixture for the shape plus verdict-level and dashboard-level outcome tests; record a `DECISIONS.md` entry and a `CHANGELOG.md` Fixed line. OUT (reasons in Deferred): Antigravity tool-name precedence (`n8we3u` / backlog `1kebul`), any change to what a verdict DOES (D160), and any change to the live renderer.
- Scope-Paths: agent_workflows/verifier_corroboration.py, agent_workflows/run_dashboard.py, tests/test_verifier_corroboration.py, tests/test_run_dashboard.py, tests/fixtures/verifier_corroboration/agy_session_subagent_step.jsonl, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: executed:e08ssu, executed:n8we3u, executed:u3enlv
- Status: approved
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
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
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

- [ ] E-01 Re-drive the authoring measurement at the executing HEAD and record it verbatim. EDIT NO FILE IN THIS ITEM. (a) Build two temporary JSONL logs under a temp dir: MIXED (one `step_type: "tool"`, `tool_name: "run_command"`, `CommandLine: "ls -la"` step, then one `step_type: "subagent"`, `state: "DONE"`, `subagent_info: {"subagents": [{"name": "x"}]}` step) and SUB-ONLY (the subagent step alone). Paste `tool_call_from_event(<subagent event>)`, `extract_session_commands(MIXED).delegation_count`, `corroborate_verifier_turn(MIXED, ["python3 -m pytest"])` `verdict`/`reason_code`, the same for SUB-ONLY, and `run_dashboard.session_stats` `tool_calls`/`tools`/`categories` for both. (b) Paste the current value of `run_dashboard.DASHBOARD_SCHEMA_VERSION` (3 at authoring; the prerequisites `n8we3u` and `u3enlv` each bump it by one, so 5 is expected, but E-03 increments whatever value is live) and paste `verifier_corroboration.AGY_TERMINAL_STATES` and `AGY_ERROR_STATES` (defined by `u3enlv` E-02; if either is absent, STOP AND REPORT: the prerequisite has not landed). (c) Run the bare suite and record the failing NODE IDS. If (a) already shows `delegation_count >= 1` for MIXED, STOP AND REPORT: the shape has been handled elsewhere.
  - Depends on: none
  - Expected outcome: pasted transcripts reproducing F-01 (or the STOP report), the current schema version and both state constants, and the baseline failing node-id list.
  - Execution state: pending

### Task group 2: detect the shape in the shared reader and the dashboard

- [ ] E-02 In `agent_workflows/verifier_corroboration.py`, extend `tool_call_from_event`'s Antigravity branch: when `step_type == "subagent"` and `state in AGY_TERMINAL_STATES` (the SAME shared constant the `"tool"` arm gates on after `u3enlv`; do not write a literal tuple, so the two arms cannot drift), return `ToolCall(tool="subagent", host="agy", command=None, path=None, seconds=<duration_seconds via _to_float>, error=(state in AGY_ERROR_STATES), delegation=True, command_missing=False)`. Return exactly ONE record per step regardless of `len(subagent_info.subagents)` (OQ-02). Every other non-`"tool"` step type still returns `None`, and the `"tool"` arm and the OpenCode branch are byte-unchanged. Add a numbered DESIGN DECISION to the function docstring citing `agy_runipd.render_agy_event`'s `step_type == "subagent"` arm and `agy_runipd`'s header ("agy's stdout stream ALREADY carries `step_type == 'subagent'` events") as the evidence the shape is real, and correct DESIGN DECISION 3's sentence "'subagent' has no in-tree occurrence outside SUBAGENT_TOOLS and CATEGORY_ORDER" so it now names this arm. Update the module docstring: item `(d) "delegation-present"` names the Antigravity `step_type == "subagent"` step alongside `browser_subagent`, and the CONTRACT block's reason (3) says the `step_type == "subagent"` gap tracked as `iuhx9d` is now detected while the observational ruling stands unchanged (other measured false positives remain, e.g. `1kebul`).
  - Depends on: E-01
  - Expected outcome: `tool_call_from_event(<subagent DONE event>)` returns a `ToolCall` with `tool='subagent'`, `host='agy'`, `delegation=True`, `error=False`; a `FAILED` subagent step returns `delegation=True`, `error=True`; MIXED gives `delegation_count == 1` and verdict `indeterminate`/`delegation-present`; SUB-ONLY gives `indeterminate`/`delegation-present`.
  - Execution state: pending

- [ ] E-03 In `agent_workflows/run_dashboard.py`, add an `elif stype == "subagent":` branch to `_agy_line` that obtains its record from `tool_call_from_event(obj)` and passes it to `_record_tool` exactly as the `"tool"` branch does (no new parsing in the dashboard). Increment `DASHBOARD_SCHEMA_VERSION` by one from the value E-01(b) recorded, because `_StatsCache` keys entries by `(size, mtime_ns)` and gates the cache on `raw.get("schema") == DASHBOARD_SCHEMA_VERSION`, so an unchanged log containing a subagent step would otherwise be served its stale count (same rule `e08ssu` OQ-02 applied). In the same item rename the existing `tests/test_run_dashboard.py::test_dashboard_schema_version_is_<N>` to the new value (docstring citing `0yvidi`), because that test pins the constant and E-03 alone would otherwise leave the suite red until E-05. Change no other dashboard logic: in particular the new branch inherits the `_agy_line` state gate, which after `u3enlv` is `AGY_TERMINAL_STATES`.
  - Depends on: E-02
  - Expected outcome: `session_stats(MIXED)` reports `tool_calls == 2`, `tools == {'run_command': 1, 'subagent': 1}`, `categories` containing `'subagent': 1`, `commands` unchanged from E-01; the schema version is one higher than E-01(b); the renamed version test passes.
  - Execution state: pending

### Task group 3: pin the outcome with a fixture and tests

- [ ] E-04 Add the committed fixture `tests/fixtures/verifier_corroboration/agy_session_subagent_step.jsonl` in the style of `agy_session_three_categories.jsonl` (an `init` event with `"session_id":"ses_<redacted>"`, a `user_input` step, one `run_command` step with a non-test `CommandLine` such as `git status`, one `step_type: "subagent"` `DONE` step with `subagent_info.subagents` of length 1, and an `agent_response` step). In `tests/test_verifier_corroboration.py` ADD (do not edit existing cases): (1) `extract_session_commands(fixture)` gives `delegation_count == 1` and one observed command; (2) `corroborate_verifier_turn(fixture, ["python3 -m pytest"])` gives `verdict == "indeterminate"` and `reason_code == "delegation-present"`; (3) a CONTROL built at test time from the fixture's lines with the subagent step removed gives `uncorroborated`, proving the fixture would otherwise be an accusation; (4) `tool_call_from_event` returns `delegation=True` with `error=True` for a subagent step in `ERROR` and in `FAILED` state, and returns `None` for a subagent step in `ACTIVE` state, for an unknown `CANCELED` state, and for a `step_type: "agent_response"` step. The expected per-state outcome is a LITERAL table in the test, not derived from `AGY_TERMINAL_STATES`, so a wrong constant fails the test rather than redefining the oracle (same rule `u3enlv` E-08 applies).
  - Depends on: E-02
  - Expected outcome: the four new cases pass; every pre-existing case passes unedited.
  - Execution state: pending

- [ ] E-05 In `tests/test_run_dashboard.py` ADD two cases (the schema-version rename is E-03's). (1) `session_stats` on the E-04 fixture counts `tools['subagent'] == 1`, `categories['subagent'] == 1`, and `commands` holding only the non-test command's kind. (2) A stale-cache case driven through `collect_rows`: place the fixture content as an agy session under a run built with the file's existing `_write_run(..., host="agy")` helper, write a cache file whose `schema` is `DASHBOARD_SCHEMA_VERSION - 1` and whose entry for that session carries the CURRENT `[size, mtime_ns]` stamp but stale stats (e.g. `tool_calls: 99`), call `collect_rows([run], cache_path=<file>)`, and assert `cache_hits == 0`, `cache_misses >= 1`, and the session row's `t_subagent == 1` and `tool_calls == 2`. Measured at review with a stand-in subagent arm: previous-schema cache -> `hits 0, misses 1, tool_calls [1]` on the unpatched dashboard; same-schema cache -> `hits 1, misses 0, tool_calls [99]`, which is the stale serve the bump prevents.
  - Depends on: E-03, E-04
  - Expected outcome: both new cases pass; no pre-existing test is edited by this item.
  - Execution state: pending

### Task group 4: record and run the suite

- [ ] E-06 Add the next free `### D<n>` to `DECISIONS.md` (D163 is already taken at review HEAD by "Rename/regroup citation rewriting skips and reports in-flight plans", and `n8we3u` and `u3enlv` each add one first, so read the last heading and use the next free number) with Context (F-01's measured verdict), Decision (an agy `step_type == "subagent"` step is a delegation in the shared reader; one record per step; the same `AGY_TERMINAL_STATES` the `"tool"` arm uses), the rejected alternative (counting one delegation per entry in `subagent_info.subagents`) with its reason, a note that D160 reason (3)'s example is now fixed while D160's ruling is unchanged, and Applied (files). Add one `CHANGELOG.md` line in the pending release's Fixed list, without em or en dashes, e.g. "Fixed: an Antigravity verifier turn that hands work to a subagent is now reported as indeterminate in `aw runs` instead of uncorroborated, and the run dashboard counts that handoff in its subagent column."
  - Depends on: E-02, E-03
  - Expected outcome: one new DECISIONS entry and one CHANGELOG line.
  - Execution state: pending

- [ ] E-07 Run the full suite BARE (`python3 -m pytest`) and compare failing NODE IDS against E-01's baseline.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: no failing node id absent from the baseline; the new tests are among the passes.
  - Execution state: pending

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

- [ ] V-01 validates E-01
  - Required evidence: PASTE the full transcript of E-01(a) showing `None`, `delegation_count` 0, `uncorroborated uncorroborated` for MIXED and `indeterminate missing-command-text` for SUB-ONLY, and the dashboard counts (or the STOP report); paste the schema version value and the two `AGY_*_STATES` constants; paste the bare-suite summary line and sorted failing node-id list. FAILS if any value is paraphrased.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: PASTE the `git diff agent_workflows/verifier_corroboration.py` (new arm, new DESIGN DECISION, corrected decision 3, module docstring edits) and a transcript re-running E-01(a) showing `ToolCall(tool='subagent', host='agy', ..., delegation=True, ...)`, a `FAILED` subagent step giving `delegation=True, error=True`, MIXED `delegation_count 1` and `indeterminate delegation-present`, SUB-ONLY `indeterminate delegation-present`. The diff must show the new arm gating on `AGY_TERMINAL_STATES`/`AGY_ERROR_STATES` and no literal state tuple. Paste `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` BEFORE E-04 adds cases, all passing unedited.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: PASTE the `git diff agent_workflows/run_dashboard.py` showing only the new `_agy_line` branch and the schema increment, the `git diff tests/test_run_dashboard.py` showing only the version-test rename/value, `session_stats(MIXED)` output with `tool_calls 2`, `tools {'run_command': 1, 'subagent': 1}`, `categories` containing `'subagent': 1`, and `python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: PASTE the fixture content, the new test function names, and `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` output; paste `git diff tests/test_verifier_corroboration.py` showing only added lines. Then temporarily revert the E-02 arm, re-run the file, PASTE the failing new cases (the verdict case must fail with `uncorroborated`), restore, re-run passing, and paste `git diff --stat` showing no residue.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: PASTE the new test names (non-binding pointers) and `python3 -m pytest -o addopts="" -q tests/test_run_dashboard.py` output; paste the E-05 portion of `git diff tests/test_run_dashboard.py` showing only added lines. The stale-cache case exercises `run_dashboard._StatsCache` through `collect_rows`; paste its assertion lines (`cache_hits == 0`, the row's `t_subagent == 1`). Then temporarily set the cache file's `schema` in the test to the CURRENT value, re-run, PASTE the failure (stale `tool_calls` served), restore, and paste `git diff --stat` showing no residue.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: PASTE the new `DECISIONS.md` entry and the `CHANGELOG.md` line, plus a search of that line for U+2014 and U+2013 returning no match.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: PASTE the bare `python3 -m pytest` summary line, the sorted failing node-id list, and the `comm -13` of baseline vs post-change failing ids showing it is EMPTY. FAILS if a new failing id appears.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; do not self-approve.

Open questions: OQ-01..OQ-03 are `resolved`, none is `Blocking: yes`.

Prerequisites: `e08ssu`, `n8we3u`, and `u3enlv` are executed (`- Item-Dependencies:`), so `verifier_corroboration.tool_call_from_event`, `AGY_TERMINAL_STATES`, and `AGY_ERROR_STATES` exist; if any is absent at the executing HEAD, STOP and report.

Execution contract: commit only the paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`; do not push; do not create a tag or release. Paste ACTUAL runner output for every validation item. Do not fold `n8we3u`/`1kebul` or `u3enlv`/`8fiybc` work into this change beyond consuming their landed constants. An out-of-scope edit that proves necessary should be made and then justified through `aw ipd finalize --scope-reason <path>=<why>`, with `--scope-ack` for any declared path left unmodified.

Post-gate lifecycle: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, complete the terminal transition through the tooled path. Under `aw oc run` / `aw agy run` the runner owns both `aw ipd begin` and that transition, so do not call them yourself; a human-driven execution runs `aw ipd begin 0yvidi` before E-01 and then uses `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Backlog `iuhx9d` then closes through the handoff (this plan carries `- From-Backlog: iuhx9d` and the same `- Blocks-Release: next`).
