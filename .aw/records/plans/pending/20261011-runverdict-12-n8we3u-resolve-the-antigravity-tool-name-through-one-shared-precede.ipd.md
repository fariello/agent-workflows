# IPD: Resolve the Antigravity tool name through one shared precedence so a delegation is never read as a shell command

- Date: 2026-10-11
- Kind: child
- Concern: FIVE in-tree readers answer "which key names this Antigravity tool call?" in FOUR different ways, so one `step_update` is a subagent delegation to the live renderer and a shell test invocation to the corroboration verdict. `agy_runipd.render_agy_event` reads `tool_info.get("name") or step.get("tool_name")`; `runner_stop.event_label` reads `info.get("name") or step.get("tool_name") or step.get("step_type")` (same precedence); `agy_view.format_record` reads `update.get("tool_name") or info.get("name")` (the OPPOSITE precedence); `verifier_corroboration.tool_call_from_event` (and therefore BOTH analytics consumers, `verifier_corroboration.extract_session_commands` and `run_dashboard._agy_line`, which `e08ssu` routed onto it) reads `su.get("tool_name")` ONLY; and `agy_run._progress_messages`, a fifth reader the backlog item does not name, reads `tool.get("name", "tool")` ONLY. Measured at HEAD `f6473cd68` (F-02): a step carrying `tool_name="run_command"` and `tool_info.name="browser_subagent"` with a pytest `CommandLine` yields `corroborate_verifier_turn(..., ["make test"])` = `uncorroborated`/`uncorroborated` and dashboard `commands={'test': 1}`, while `runner_stop.event_label` names it `browser_subagent`. The `uncorroborated` verdict is published on the attempt and rendered by `run_viewer` as `corroboration: <verdict> (reason: <reason>)`, so the wrong answer is user-visible in `aw runs` and accuses a verifier of not running the tests it claimed.
- Scope: IN: add ONE shared primitive `verifier_corroboration.agy_tool_name(step_update)` that resolves an Antigravity tool name with a single, documented precedence (`tool_info.name` first, then `tool_name`, both stripped, empty string when neither is a non-blank string); route `tool_call_from_event` onto it and make its delegation flag fail open on a conflicting step (delegation when EITHER raw name is in `SUBAGENT_TOOLS`); bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` because cached per-file values change for unchanged log files; route `agy_runipd.render_agy_event`, `agy_view.format_record`, `runner_stop.event_label` and `agy_run._progress_messages` onto the same primitive while keeping each reader's own default label; add one cross-reader parity test file plus verdict-level and dashboard-level outcome tests; record the decision in `DECISIONS.md` with a `CHANGELOG.md` line. OUT, each with a reason in the Deferred section: the agy `FAILED` tool state (backlog `8fiybc`), the `step_type == "subagent"` delegation shape (backlog `iuhx9d`), the OpenCode tool-name key (one key, no disagreement), `stall_progress`'s raw substring scan for `"schedule"`/`"invoke_subagent"`/`"manage_task"` (key-agnostic, so precedence cannot disagree there), and any change to what a corroboration verdict DOES (D160: observational only).
- Scope-Paths: agent_workflows/verifier_corroboration.py, agent_workflows/run_dashboard.py, agent_workflows/agy_runipd.py, agent_workflows/agy_view.py, agent_workflows/runner_stop.py, agent_workflows/agy_run.py, tests/test_verifier_corroboration.py, tests/test_run_dashboard.py, tests/test_agy_tool_name_precedence.py, DECISIONS.md, CHANGELOG.md
- Item-Dependencies: executed:e08ssu
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 1kebul
- Blocks-Release: next
- Set: runverdict
- Order: 12
- Highest E allocated: 12
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: n8we3u
- Approval: 2026-10-12, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-12 approved (aw set): status set to approved
- 2026-10-12 reviewed (opencode/its_direct/pt3-claude-opus-5.5-1m-us): plan-review: APPROVE WITH REVISIONS APPLIED
- 2026-10-12 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Re-measured at HEAD 220239939: F-02 (conflict -> uncorroborated, dashboard commands={'test': 1}) and F-03 (info-only -> indeterminate missing-command-text) reproduce; added F-08 (renderer hides the name behind a command payload; degenerate shapes raise or diverge today) and reconciled E-05/E-06/E-07/E-08/E-09 and V-02/V-05/V-06/V-07; Deferred rows now carry Carrier/Carrier-Declined (check.ipd-uncarried-obligation was ERROR).
- 2026-10-12 to-review (aw set): Graduated from backlog 1kebul. Re-measured at HEAD f6473cd68: the backlog's CONFLICT shape reproduces end to end (corroborate_verifier_turn -> uncorroborated; dashboard commands={'test': 1}); found a fifth reader the item omits (agy_run._progress_messages) and that the INFO-ONLY shape the shipped tests construct is invisible to analytics (indeterminate missing-command-text). Precedence chosen tool_info.name first on evidence (OQ-01), with fail-open delegation on conflicting names (OQ-02) because no live agy log exists to measure real precedence. Suite baseline: 38 failed (unrelated no-project/explicit-dir env tests), 7181 passed, 2 skipped.

- 2026-10-12 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every Antigravity session-log reader agree on which tool a `step_update` names, by routing all five through one shared resolver whose precedence is chosen on evidence and recorded, so a subagent delegation can no longer be counted as a shell test command and turn the fail-open `indeterminate` (`delegation-present`) corroboration verdict into a published `uncorroborated`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-drive the authoring measurements at the executing HEAD and record them verbatim, so the change is made against current fact. EDIT NO FILE IN THIS ITEM. (a) Feed the three shapes of F-02 (CONFLICT: `tool_name="run_command"`, `tool_info.name="browser_subagent"`, `CommandLine="python3 -m pytest tests/x.py"`; NAME-ONLY: `tool_name` only; INFO-ONLY: `tool_info.name="run_command"` only, with a `CommandLine`) to all five readers (`agy_runipd.render_agy_event` at `verbosity=1` with `render_stream.Palette(False)`, `agy_view.format_record`, `runner_stop.event_label`, `agy_run._progress_messages`, `verifier_corroboration.tool_call_from_event`) and paste each reader's output. (b) Write the CONFLICT and INFO-ONLY shapes to temporary JSONL logs and paste `extract_session_commands`, `corroborate_verifier_turn(log, ["make test"])` (CONFLICT) / `corroborate_verifier_turn(log, ["python3 -m pytest"])` (INFO-ONLY), and `run_dashboard.session_stats` (`tools`, `commands`) for each. (c) Run the bare suite and record the failing NODE IDS (F-01). If (a) shows the readers ALREADY agree, STOP AND REPORT: the defect has been fixed elsewhere and this plan would be re-doing it.
  - Depends on: none
  - Expected outcome: pasted transcripts reproducing F-02 and F-03 (or the STOP report), and the baseline failing node-id list.
  - Execution state: performed

### Task group 2: one resolver, and route the analytics readers onto it

- [x] E-02 Add `agy_tool_name(step_update)` to `agent_workflows/verifier_corroboration.py`, export it in `__all__`, and document the precedence decision in its docstring. Contract: given a `step_update` mapping (anything else returns `""`), return `str(tool_info["name"]).strip()` when `tool_info` is a Mapping whose `name` is a non-blank string, else `str(step_update["tool_name"]).strip()` when that is a non-blank string, else `""`. The function must never raise (non-Mapping `tool_info`, non-string names, `None` all degrade to the next candidate). The docstring states the THREE reasons for `tool_info.name` first (F-05): (1) Antigravity's own headless stream documentation, as summarised in the in-tree research report `20260810-gemini-actually-validate-playbook...research-report.md` ("Completed tool steps contain `tool_name` and `tool_info`, including canonical tool name"), names `tool_info` as the canonical record; (2) it is the precedence the two runtime-critical readers already use (`render_agy_event`, the live operator stream, and `runner_stop.event_label`, the interrupt ledger), so choosing it moves the fewest operator-visible surfaces; (3) it is the only name key the shipped tests and the executed host-capability probe (`dwbm7a`, `host_sandbox_profile._probe_structured_tool_events`'s Antigravity case) construct, so the analytics readers are the outliers. Keep the module stdlib-only and import nothing from `agent_workflows`.
  - Depends on: E-01
  - Expected outcome: `verifier_corroboration.agy_tool_name` exists, is exported, and returns the documented value for every shape in V-02's table.
  - Execution state: performed

- [x] E-03 Route `verifier_corroboration.tool_call_from_event`'s Antigravity branch onto `agy_tool_name` for `ToolCall.tool` and for the `run_command` command-extraction test, and make its delegation flag FAIL OPEN: `delegation=True` when the resolved name OR either raw candidate (`tool_info.name`, `tool_name`, each stripped) is in `SUBAGENT_TOOLS`. Record the fail-open rule in the function's DESIGN DECISIONS docstring as a fourth numbered decision, citing the module header's own rule that "every unknown, missing, unreadable, delegated, or unresolved case resolves to `indeterminate`, never to `uncorroborated`": a step whose two name keys disagree and one of them is a subagent is ambiguous, so it must land on the permissive side. Do NOT change the OpenCode branch, the accepted state tuple (`DONE`/`ERROR`, see `8fiybc`), or the `step_type == "tool"` gate (see `iuhx9d`).
  - Depends on: E-02
  - Expected outcome: the CONFLICT shape yields `ToolCall(tool='browser_subagent', ..., delegation=True)` and the reverse conflict (`tool_name="browser_subagent"`, `tool_info.name="run_command"`) also yields `delegation=True` (its `tool` is `run_command` and its `command` is still extracted; `extract_session_commands` checks `tc.delegation` before `tc.command`, so the verdict counts it as a delegation and not as an observed command, while the dashboard, which ignores `delegation`, still counts it under `run_command`; that dashboard reading is accepted as the resolved-name view); the INFO-ONLY shape yields `tool='run_command'` with its command extracted; the NAME-ONLY shape is byte-identical to today.
  - Execution state: performed

- [x] E-04 Bump `run_dashboard.DASHBOARD_SCHEMA_VERSION` from 3 to 4 and update the existing version assertion in `tests/test_run_dashboard.py` (`test_dashboard_schema_version_is_3`, renamed to `..._is_4`, docstring citing this plan). Reason (F-06, same rule `e08ssu` OQ-02 applied): `_StatsCache` keys entries by `(size, mtime_ns)` and gates the whole cache on `raw.get("schema") == DASHBOARD_SCHEMA_VERSION`, and E-03 changes the `tools`/`commands`/`categories` a CONFLICT or INFO-ONLY log produces WITHOUT changing the file, so a stale entry would otherwise be served as fresh. Change no other dashboard logic: `_agy_line` already obtains its tool record from `tool_call_from_event`, so routing is inherited.
  - Depends on: E-03
  - Expected outcome: `DASHBOARD_SCHEMA_VERSION == 4`; the renamed test passes.
  - Execution state: performed

### Task group 3: route the three renderers and the progress reader onto the resolver

- [x] E-05 Route `agy_runipd.render_agy_event`'s `step_type == "tool"` branch onto `verifier_corroboration.agy_tool_name(step) or "tool"`, replacing `tool_info.get("name") or step.get("tool_name") or "tool"`. Also normalize `tool_info` to `{}` when `step.get("tool_info")` is not a Mapping (F-08: today `tool_info="junk"` makes `tool_info.get("parameters")` raise `AttributeError` in the live renderer), then keep `params = tool_info.get("parameters") or {}` and every downstream use unchanged. Behavior changes, all intended (F-08): a padded name now renders stripped AND, because the stripped name is then found in `_AGY_TOOL_PREFIX_KIND`, a padded `" run_command "` renders with the `bash` prefix instead of `• tool:`; a non-string `tool_info.name` falls back to `tool_name` instead of rendering `str(5)`; a non-Mapping `tool_info` no longer raises. Note: the renderer DROPS the tool name by design whenever `agy_prefix_kind` resolves to `bash`/`edit`/`write`/`read`/`find` and a command payload exists (it prints the payload), so the F-02 CONFLICT shape WITH a `CommandLine` renders `❯ bash:  python3 -m pytest tests/x.py` both before and after; the name is only visible on a parameter-free step.
  - Depends on: E-02
  - Expected outcome: a parameter-free CONFLICT step (`tool_name="run_command"`, `tool_info={"name": "browser_subagent"}`) still renders `• tool:  browser_subagent` at `verbosity=1`; a non-Mapping `tool_info` returns a line instead of raising; an existing `tests/test_agy_runipd_cli.py` case is not edited and still passes.
  - Execution state: performed

- [x] E-06 Route `agy_view.format_record`'s `TOOL` branch onto `agy_tool_name(update) or "tool"`, replacing `update.get("tool_name") or info.get("name") or "tool"`. This FLIPS the viewer's precedence on a CONFLICT step (it now prints `browser_subagent` where it printed `run_command`), which is the point; keep `info` for the `parameters`/`output` parts, but normalize it to `{}` when `update.get("tool_info")` is not a Mapping (F-08: `tool_info="junk"` raises `AttributeError` in `format_record` today).
  - Depends on: E-02
  - Expected outcome: `aw agy view` names the CONFLICT step `browser_subagent`, matching the live renderer; a non-Mapping `tool_info` yields a line instead of raising.
  - Execution state: performed

- [x] E-07 Route `runner_stop.event_label`'s `step_update` branch onto `agy_tool_name(step) or step.get("step_type")`, preserving the `step_type` fallback and the "never raise" contract its docstring states. Import `verifier_corroboration` at module top (it is stdlib-only, so no cycle with `platform_lock`/`runner_shutdown`).
  - Depends on: E-02
  - Expected outcome: labels are unchanged for every shape except a padded name (now stripped) and a non-string `tool_info.name` (today `unknown`, because the non-string wins the `or` chain and fails the `isinstance(name, str)` check; now `unknown:<tool_name>`, F-08); `tests/test_runner_stop_triggers_e2e.py` passes unedited.
  - Execution state: performed

- [x] E-08 Route `agy_run._progress_messages`'s tool branch onto `agy_tool_name(step) or "tool"` (then `_compact(..., 60)`), replacing `tool.get("name", "tool")`. Keep the existing `isinstance(tool, dict)` gate so a step without `tool_info` still emits no tool message. Behavior change: a NAME-ONLY step with an empty `tool_info` now names the tool instead of printing `tool finished: tool` (F-04), and a non-string `tool_info.name` falls back to `tool_name` instead of printing `str(5)` (F-08). The message KEY (`step:<i>:<state>:tool:<name>`) changes with the name; that is intended.
  - Depends on: E-02
  - Expected outcome: the NAME-ONLY shape with `tool_info: {"parameters": {}}` yields `tool finished: <tool_name>`.
  - Execution state: performed

### Task group 4: make the next divergence fail a test

- [x] E-09 Add `tests/test_agy_tool_name_precedence.py`, a cross-reader PARITY test that drives all five real readers (no mocks) with one parametrized table of `step_update` shapes (CONFLICT, REVERSE-CONFLICT, NAME-ONLY, INFO-ONLY, PADDED, NON-STRING `tool_info.name`, NON-MAPPING `tool_info`, NEITHER) and asserts each reader's emitted tool name equals `agy_tool_name(step)` (or that reader's documented default when it is `""`): the renderer's rendered line at `verbosity=1`, `format_record`'s output, `event_label`'s suffix, `_progress_messages`' message, and `tool_call_from_event(...).tool`. Construct the parity rows WITHOUT command-bearing parameters (`tool_info` carries no `parameters`, or `{}`), because `render_agy_event` deliberately prints the command payload instead of the tool name when one exists (F-08), so a row with a `CommandLine` cannot show the renderer's name choice. Documented defaults when `agy_tool_name` is `""`: renderer and viewer `tool`; `event_label` the `step_type` (`tool`); `_progress_messages` `tool` when `tool_info` is a Mapping and NO message when it is not (its `isinstance(tool, dict)` gate, E-08); `tool_call_from_event` `''`. The NON-MAPPING `tool_info` row must also assert that no reader raises (F-08). Assert on rendered OUTPUT, never on source text.
  - Depends on: E-03, E-05, E-06, E-07, E-08
  - Expected outcome: the new file passes; reverting any one reader to its old precedence makes at least one row fail (demonstrated in V-09).
  - Execution state: performed

- [x] E-10 Add outcome tests for the published verdict and the dashboard. In `tests/test_verifier_corroboration.py` (ADD cases only; do not edit existing ones, which use `tool_name`-only shapes and must keep passing unmodified): a CONFLICT log and a REVERSE-CONFLICT log each give `corroborate_verifier_turn(...)` = `indeterminate` with reason `delegation-present` and `delegation_count == 1`; an INFO-ONLY log with a matching claim gives `corroborated`. In `tests/test_run_dashboard.py`: `session_stats` on a CONFLICT log counts `tools={'browser_subagent': 1}`, category `subagent`, and no `commands`; on an INFO-ONLY log counts `tools={'run_command': 1}` and `commands={'test': 1}`.
  - Depends on: E-03, E-04
  - Expected outcome: the new cases pass; every pre-existing case in both files passes unedited (other than E-04's version test).
  - Execution state: performed

### Task group 5: record the decision and run the suite

- [x] E-11 Record the decision as the next `### D<n>` in `DECISIONS.md` (D163 at authoring; use the next free number) with Context (the five readers and F-02's measured verdict), Decision (`tool_info.name` first, `tool_name` fallback, fail-open delegation on a conflicting step), the rejected alternative (`tool_name` first) with its reason, and Applied (the files). Add one `CHANGELOG.md` line under the pending release's Fixed list, written without em or en dashes (user-facing prose), e.g. "Fixed: Antigravity session readers now agree on a tool call's name, so a subagent delegation is no longer counted as a shell command and can no longer make a verifier turn read as uncorroborated."
  - Depends on: E-03
  - Expected outcome: one new DECISIONS entry and one CHANGELOG line.
  - Execution state: performed

- [x] E-12 Run the full suite BARE (`python3 -m pytest`) and compare failing NODE IDS against E-01's baseline.
  - Depends on: E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-11
  - Expected outcome: no failing node id that is not in the baseline; the new tests are among the passes.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `verifier_corroboration` is declared "Pure stdlib-only reader: never imports runner_shared, run_dashboard, or either host runner" in its module docstring; the new primitive keeps that, and the dependency direction this plan adds (renderers importing it) is the one `e08ssu` already established for `run_dashboard`.
- `tool_call_from_event` documents each resolved disagreement as a numbered DESIGN DECISION in its docstring (E-02/E-03/E-04 of `e08ssu`); this plan adds the fourth in the same place.
- Cached dashboard values that change for an unchanged log require a `DASHBOARD_SCHEMA_VERSION` bump (`e08ssu` OQ-02, `run_dashboard._StatsCache`).
- The corroboration verdict is observational and refuses nothing (D160, spec `25kzda` Section 5.1); this plan changes only which verdict is computed, not what consumes it.
- Tests assert outcomes by driving real functions (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); the parity test drives every reader rather than grepping their source.
- Run the suite bare: `python3 -m pytest` (`pyproject.toml` `addopts` supplies `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| # | Severity | Location | Finding | Evidence |
|---|---|---|---|---|
| F-01 | BASELINE | full suite | At authoring HEAD `f6473cd68` the bare suite reports `38 failed, 7181 passed, 2 skipped, 3 warnings in 381.50s`. Every failure is in an unrelated no-project / explicit-dir / trailer / finalize-sendback test (`test_no_project_exit_is_cannot_run.py` 12, `test_explicit_dir_non_project.py` 6, `test_validator_nonsurveyable_dir.py` 5, `test_nonsurveyable_root_refusal.py` 4, `test_read_class_callers_refuse.py` 3, `test_commit_run_trailers_env.py` 3, `test_explicit_dir_subdir_resolution.py` 2, `test_attention.py` 1, `test_agent_surface_conformance.py` 1, `test_finalize_sendback.py` 1), none touching a Scope-Path. They are environment-sensitive in a lane worktree; the executor compares by NODE ID, not total. | `python3 -m pytest` run in this lane; per-file counts from `grep -E "^FAILED" | sed 's/::.*//' | sort | uniq -c`. The four directly relevant files pass: `125 passed in 41.11s` for `test_verifier_corroboration.py test_run_dashboard.py test_runner_stop_triggers_e2e.py test_agy_runipd_cli.py`. |
| F-02 | HIGH | `verifier_corroboration.tool_call_from_event`, `run_dashboard.session_stats` | THE BACKLOG ITEM'S MEASURED CONSEQUENCE REPRODUCES end to end, including the published verdict. A one-step CONFLICT log (`tool_name="run_command"`, `tool_info.name="browser_subagent"`, `CommandLine="python3 -m pytest tests/x.py"`) gives `extract_session_commands` delegation 0 and one observed command, `corroborate_verifier_turn(log, ["make test"])` = `uncorroborated uncorroborated`, and `session_stats` `tools={'run_command': 1}`, `commands={'test': 1}`. | Python transcript at authoring: `conflict extract: 0 ['python3 -m pytest tests/x.py']`, `conflict verdict: uncorroborated uncorroborated`, `conflict dash tools: {'run_command': 1} commands: {'test': 1}`. |
| F-03 | MED | same | THE INFO-ONLY SHAPE (the one the shipped tests and the `dwbm7a` probe construct) IS INVISIBLE TO ANALYTICS. A step with `tool_info.name="run_command"` and no `tool_name` gives `ToolCall(tool='', command=None)`, so `corroborate_verifier_turn(log, ["python3 -m pytest"])` = `indeterminate missing-command-text` and the dashboard counts `tools={'?': 1}`, `commands={}`. | Transcript: `infoonly extract: 0 0 []`, `infoonly verdict: indeterminate missing-command-text`, `infoonly dash tools: {'?': 1} commands: {}`. Shape constructed by `tests/test_runner_stop_triggers_e2e.py` (`"tool_info": {"name": "run_command"}`), `tests/test_runfresh_end_to_end.py`, and `host_sandbox_profile`'s Antigravity probe event. |
| F-04 | MED | `agy_run._progress_messages` | A FIFTH READER the backlog item does not list. It reads `tool.get("name", "tool")` and never `tool_name`, so a NAME-ONLY step prints `tool finished: tool`. The parity test must cover it or the fix leaves a reader behind. | Transcript of the three-shape probe across readers: CONFLICT -> `[p] tool finished: alpha_tool`; NAME-ONLY -> `[p] tool finished: tool`; `render_agy_event` -> `alpha_tool`/`beta_tool`; `agy_view` -> `beta_tool`/`beta_tool`/`alpha_tool`; `event_label` -> `alpha_tool`/`beta_tool`/`alpha_tool`; `tool_call_from_event().tool` -> `beta_tool`/`beta_tool`/`''`. `rg -l "tool_info|tool_name" agent_workflows` finds no other Antigravity reader (`security_hardening` and `runners_monitor` use the identifier for unrelated values; `stall_progress` substring-scans raw lines). |
| F-05 | DECISION INPUT | precedence | `tool_info.name` IS THE BETTER-EVIDENCED KEY. The in-tree research report states completed tool steps carry "`tool_name` and `tool_info`, including canonical tool name"; the two runtime-critical readers (`render_agy_event`, `event_label`) already prefer it; and every shipped test and the executed probe that constructs an Antigravity name uses `tool_info.name` (only `tests/test_stall_progress_agy.py` sets both, to the same value). Choosing `tool_name`-first would flip the live stream and the interrupt ledger instead of the two outliers. | `.aw/records/research/reference/202608/20260810-gemini-actually-validate-playbook-00-6zf5av-...research-report.md` (the "Antigravity 1.1.11 supports `--output-format stream-json`" paragraph); `dwbm7a` F-05 ("the key is `tool_info.name`"); `rg -n '"tool_info": \{"name"' tests` hits only `test_runner_stop_triggers_e2e.py` and `test_runfresh_end_to_end.py`. No live Antigravity session log exists in this checkout to measure real precedence (`mm6wuz`: "zero `\"event\":\"step_update\"` lines in all 380 session logs"), which is why E-03 adds the fail-open delegation rule rather than trusting precedence alone. |
| F-06 | MED | `run_dashboard._StatsCache` | THE CACHE WOULD SERVE STALE COUNTS: entries are keyed by `(size, mtime_ns)` and gated on `raw.get("schema") == DASHBOARD_SCHEMA_VERSION` (currently 3, pinned by `test_dashboard_schema_version_is_3`). E-03 changes the counts for an unchanged CONFLICT/INFO-ONLY file, so the version must move. | `run_dashboard.DASHBOARD_SCHEMA_VERSION = 3`; `_StatsCache.__init__` reads `raw.get("schema") == DASHBOARD_SCHEMA_VERSION`; `e08ssu` OQ-02 applied the same rule. |
| F-07 | LOW | import cost | Importing `verifier_corroboration` from `runner_stop`, `agy_view` and `agy_run` adds about 5ms of module self time (`python3 -X importtime`: `5513 | 84811 | agent_workflows.verifier_corroboration`, the cumulative figure being dominated by the `agent_workflows` package import every caller already pays). Not user-perceptible. | `python3 -X importtime -c "import agent_workflows.verifier_corroboration"`. |
| F-08 | MED | `agy_runipd.render_agy_event`, `agy_view.format_record`, `runner_stop.event_label`, `agy_run._progress_messages` | ADDED AT REVIEW. (a) The renderer prints the COMMAND PAYLOAD, not the tool name, whenever `agy_prefix_kind` resolves to a command class and a payload exists, so the F-02 CONFLICT shape WITH a `CommandLine` renders `❯ bash:  python3 -m pytest tests/x.py`; a parity row with a command cannot observe the renderer's name choice. (b) The degenerate shapes E-09 lists diverge today in ways beyond precedence: `tool_info="junk"` RAISES `AttributeError` in `render_agy_event` and `format_record`; `tool_info={"name": 5}` renders `5` in the renderer and `_progress_messages` but makes `event_label` return bare `unknown`; a padded `" run_command "` renders `• tool:   run_command ` because the unstripped name misses `_AGY_TOOL_PREFIX_KIND`. Routing through `agy_tool_name` fixes all of these, and they are now named as intended changes rather than surprises. | Review probe at HEAD `220239939`: `CONFLICT render: '❯ bash:  python3 -m pytest tests/x.py'`; `CONFLICT-noparams render: '• tool:  browser_subagent'`; `NONMAP render RAISES AttributeError 'str' object has no attribute 'get'`; `NONMAP view RAISES AttributeError`; `NONSTR label 'unknown'`; `NONSTR progress '[p] tool finished: 5'`; `PADDED render '• tool:   run_command '`. |

## Proposed changes (ordered, validatable)

1. Re-measure (E-01).
2. Add `verifier_corroboration.agy_tool_name` with the documented `tool_info.name` -> `tool_name` precedence (E-02).
3. Route `tool_call_from_event` onto it with fail-open delegation, inheriting into `extract_session_commands` and `run_dashboard._agy_line` (E-03); bump `DASHBOARD_SCHEMA_VERSION` to 4 (E-04).
4. Route `render_agy_event`, `format_record`, `event_label`, `_progress_messages` onto it, keeping each reader's own default (E-05..E-08).
5. Add the cross-reader parity test and the verdict/dashboard outcome tests (E-09, E-10).
6. Record D-entry and CHANGELOG line (E-11); run the full suite (E-12).

## Deferred / out of scope (with reason)

- The agy `FAILED` tool state accepted by the renderer but not by analytics: backlog `8fiybc` owns it; it is a different key (state, not name) and changes different counts.
  - Carrier: 8fiybc
- The `step_type == "subagent"` delegation shape: backlog `iuhx9d` owns it; it is a step-type gate, not a name precedence, and has its own fixture needs.
  - Carrier: iuhx9d
- OpenCode tool names: a single key (`part.tool`), so there is nothing to disagree on.
  - Carrier-Declined: no defect exists; OpenCode has one name key, so there is no outstanding work to carry.
- `stall_progress`'s background-task detection: it substring-scans the raw line for the quoted tool names, so it matches whichever key carries the name and cannot disagree on precedence.
  - Carrier-Declined: no defect exists; the scan is key-agnostic, so precedence cannot diverge there.
- What the corroboration verdict does: D160 rules it observational; this plan changes which verdict is computed for two shapes and nothing that consumes it.
  - Carrier-Declined: settled decision D160; changing what the verdict does is not desired work.

## Scope check

- Over-scope: none. Every Scope-Path is either a reader of the Antigravity name key, the cache version that must move with E-03, a test that pins the outcome, or the decision record.
- Under-scope: none known. `agy_run._progress_messages` (F-04) is added beyond the backlog item's list precisely so no reader is left on its own precedence; F-04's search found no other reader.

## Required tests / validation

- `python3 -m pytest` BARE in the executing worktree; do not add `-n0`, another `-q`, or `-p no:randomly`. Compare failing NODE IDS with E-01's baseline (F-01), not totals.
- `tests/test_agy_tool_name_precedence.py` (new, E-09) drives all five readers over one shape table and must pass; a deliberate revert of one reader must make it fail (V-09).
- New cases in `tests/test_verifier_corroboration.py` and `tests/test_run_dashboard.py` (E-10) pin the published verdict and dashboard counts for the CONFLICT, REVERSE-CONFLICT and INFO-ONLY shapes.
- Every PRE-EXISTING case in `tests/test_verifier_corroboration.py`, `tests/test_run_dashboard.py` (except the renamed version test), `tests/test_agy_runipd_cli.py`, `tests/test_runner_stop_triggers_e2e.py` and `tests/test_stall_progress_agy.py` passes unedited: they use NAME-ONLY or INFO-ONLY-consistent shapes, so an edit to one would mean the change altered a shape this plan claims to preserve.
- `aw ipd lint --phase pre-transition` conforming before the terminal transition.

## Spec / documentation sync

- Specs: N/A with reason. No spec defines the Antigravity tool-name key; spec `25kzda` Section 5.1 mentions corroboration only to rule it observational and cites the extraction predicate's false positives generically (`iuhx9d`), which this plan does not contradict. `Scope-Paths` declares no `.spec.md`.
- `DECISIONS.md`: new entry recording the precedence and the fail-open delegation rule (E-11).
- `CHANGELOG.md`: one Fixed line, no em or en dashes (E-11).
- Module docstrings: `agy_tool_name` and `tool_call_from_event` carry the decision in code (E-02, E-03).

## Open questions

### OQ-01: Which key wins, `tool_info.name` or `tool_name`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, `tool_info.name` first with `tool_name` as fallback, on F-05's three grounds (the in-tree research report calls `tool_info` the canonical record; the two runtime-critical readers already use it; every shipped test and the executed `dwbm7a` probe constructs it). The rejected alternative, `tool_name` first, would flip the live operator stream and the interrupt ledger rather than the two analytics outliers, and would keep the INFO-ONLY shape (F-03) invisible to analytics unless the fallback were also added, at which point it differs only on a CONFLICT step, where the evidence favours `tool_info`.

### OQ-02: Precedence alone still chooses one name on a CONFLICT step; is that safe for the verdict?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED by E-03's fail-open delegation rule. No live Antigravity log exists here to show which key a real host fills (F-05), so a REVERSE-CONFLICT step (`tool_name="browser_subagent"`, `tool_info.name="run_command"`) under precedence alone would move from today's `indeterminate` to a possible `uncorroborated`, the exact accusation this bug is about. Treating the step as a delegation when EITHER name is a subagent keeps both conflict directions on `indeterminate`, which is the module header's stated rule for ambiguous cases. The cost is that a genuine shell command mislabelled with a subagent name is not compared, which can only make the verdict MORE permissive (spec `25kzda` Section 5.1 permits that direction).

### OQ-03: The INFO-ONLY shape can now reach `corroborated` or `uncorroborated` where it was `indeterminate`. Is that an acceptable verdict change?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED, yes. Today that shape is read as a nameless tool and reported `missing-command-text`, which is factually wrong (the command text is present). Reading it correctly is the bug fix, the verdict refuses nothing (D160), and E-10 pins the corroborated case so the change is validated rather than incidental, as the backlog item requires ("the change needs its own validation").

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: PASTE the full transcript of (a) all five readers over the three shapes, (b) `extract_session_commands` / `corroborate_verifier_turn` / `session_stats` for the CONFLICT and INFO-ONLY logs, showing `uncorroborated uncorroborated` and `indeterminate missing-command-text` respectively (or the STOP report if they now agree), and (c) the bare suite summary line plus the sorted failing node-id list. FAILS if any value is paraphrased rather than pasted.
  - Observed evidence:
    (a) All five readers over the three shapes:
    ```
    === PART (a): Five readers over three shapes ===

    --- Shape: CONFLICT ---
    render_agy_event: '❯ bash:  python3 -m pytest tests/x.py'
    agy_view.format_record: '0001     1 TOOL           DONE   run_command | {"CommandLine":"python3 -m pytest tests/x.py"}'
    runner_stop.event_label: 'unknown:browser_subagent'
    agy_run._progress_messages: [('step:1:DONE:tool:browser_subagent', '[test] tool finished: browser_subagent')]
    verifier_corroboration.tool_call_from_event: ToolCall(tool='run_command', host='agy', command='python3 -m pytest tests/x.py', path=None, seconds=0.0, error=False, delegation=False, command_missing=False)

    --- Shape: NAME-ONLY ---
    render_agy_event: '❯ bash:  run_command'
    agy_view.format_record: '0001     2 TOOL           DONE   run_command'
    runner_stop.event_label: 'unknown:run_command'
    agy_run._progress_messages: []
    verifier_corroboration.tool_call_from_event: ToolCall(tool='run_command', host='agy', command=None, path=None, seconds=0.0, error=False, delegation=False, command_missing=True)

    --- Shape: INFO-ONLY ---
    render_agy_event: '❯ bash:  python3 -m pytest tests/x.py'
    agy_view.format_record: '0001     3 TOOL           DONE   run_command | {"CommandLine":"python3 -m pytest tests/x.py"}'
    runner_stop.event_label: 'unknown:run_command'
    agy_run._progress_messages: [('step:3:DONE:tool:run_command', '[test] tool finished: run_command')]
    verifier_corroboration.tool_call_from_event: ToolCall(tool='', host='agy', command=None, path=None, seconds=0.0, error=False, delegation=False, command_missing=False)
    ```
    (b) CONFLICT and INFO-ONLY JSONL log analytics:
    ```
    [CONFLICT]
    extract_session_commands: SessionReadResult(commands=[ObservedCommand(command='python3 -m pytest tests/x.py', tool='run_command', host='agy', error=False)], delegation_count=0, missing_command_count=0, reason_code='', format='agy')
    corroborate_verifier_turn(["make test"]): uncorroborated uncorroborated
    session_stats: tools: {'run_command': 1} commands: {'test': 1}

    [INFO-ONLY]
    extract_session_commands: SessionReadResult(commands=[], delegation_count=0, missing_command_count=0, reason_code='', format='agy')
    corroborate_verifier_turn(["python3 -m pytest"]): indeterminate missing-command-text
    session_stats: tools: {'?': 1} commands: {}
    ```
    (c) Baseline bare suite run:
    ```
    8063 passed, 4 skipped, 18 xfailed, 3 warnings in 1134.23s (0:18:54)
    Failing node-id list: empty (0 failed).
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: PASTE the `git diff` of `agy_tool_name` and its docstring, and a transcript calling it on each shape: CONFLICT -> `'browser_subagent'`; REVERSE-CONFLICT -> `'run_command'`; NAME-ONLY -> the `tool_name`; INFO-ONLY -> `'run_command'`; PADDED (`" run_command "`) -> `'run_command'`; `tool_info={"name": 5}` with `tool_name="x"` -> `'x'`; `tool_info="junk"` with `tool_name="x"` -> `'x'`; neither -> `''`; a non-Mapping argument -> `''`. Also paste `"agy_tool_name" in verifier_corroboration.__all__` -> `True` and the import-purity delta (import `agent_workflows` first, snapshot `sys.modules`, then import `agent_workflows.verifier_corroboration` and paste the sorted new `agent_workflows.*` keys), which must be exactly `['agent_workflows.verifier_corroboration']` (measured at review; the `-X importtime` form cannot show this because the package `__init__` loads its own submodules first, `e08ssu` PR-005).
  - Observed evidence:
    `git diff` of `agy_tool_name`:
    ```python
    def agy_tool_name(step_update: Any) -> str:
        """Resolve the tool name of an Antigravity step update using canonical precedence.

        PRECEDENCE DECISION (D163):
        Given a step_update mapping (anything else returns ""), return
        str(tool_info["name"]).strip() when tool_info is a Mapping whose name is a non-blank
        string, else str(step_update["tool_name"]).strip() when that is a non-blank string,
        else "". Never raises (non-Mapping tool_info, non-string names, None all degrade to
        the next candidate).

        Three reasons establish tool_info.name as the primary key (F-05):
        (1) Antigravity's own headless stream documentation, as summarised in the in-tree
            research report 20260810-gemini-actually-validate-playbook-00-6zf5av-actually-validate-in-agy-research-report.md
            ("Completed tool steps contain tool_name and tool_info, including canonical tool name"),
            names tool_info as the canonical record.
        (2) It is the precedence the two runtime-critical readers already use (render_agy_event,
            the live operator stream, and runner_stop.event_label, the interrupt ledger), so
            choosing it moves the fewest operator-visible surfaces.
        (3) It is the only name key the shipped tests and the executed host-capability probe
            (dwbm7a, host_sandbox_profile._probe_structured_tool_events's Antigravity case)
            construct, so the analytics readers are the outliers.
        """
        if not isinstance(step_update, (dict, Mapping)):
            return ""
        tool_info = step_update.get("tool_info")
        if isinstance(tool_info, (dict, Mapping)):
            raw_name = tool_info.get("name")
            if isinstance(raw_name, str):
                s_name = raw_name.strip()
                if s_name:
                    return s_name
        raw_tool = step_update.get("tool_name")
        if isinstance(raw_tool, str):
            s_tool = raw_tool.strip()
            if s_tool:
                return s_tool
        return ""
    ```
    Transcript:
    ```
    import purity delta: ['agent_workflows.verifier_corroboration']
    in __all__: True
    CONFLICT: 'browser_subagent'
    REVERSE-CONFLICT: 'run_command'
    NAME-ONLY: 'run_command'
    INFO-ONLY: 'run_command'
    PADDED: 'run_command'
    NON-STR-NAME: 'x'
    NON-MAP-INFO: 'x'
    NEITHER: ''
    NON-MAP-ARG: ''
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: PASTE the `git diff` of `tool_call_from_event` (including the fourth DESIGN DECISION) and the `ToolCall` returned for CONFLICT (`tool='browser_subagent'`, `delegation=True`), REVERSE-CONFLICT (`delegation=True`), INFO-ONLY (`tool='run_command'`, `command` populated) and NAME-ONLY (identical to the V-01 baseline). Re-run V-01(b) and paste CONFLICT -> `indeterminate delegation-present` and INFO-ONLY -> `corroborated corroborated`. Paste `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py` output from BEFORE E-10 adds cases, showing every pre-existing case passes unmodified.
  - Observed evidence:
    `git diff` of `tool_call_from_event` and `ToolCall` outputs:
    ```
    CONFLICT: ToolCall(tool='browser_subagent', host='agy', command=None, path=None, seconds=0.0, error=False, delegation=True, command_missing=False)
    REVERSE-CONFLICT: ToolCall(tool='run_command', host='agy', command='python3 -m pytest tests/x.py', path=None, seconds=0.0, error=False, delegation=True, command_missing=False)
    NAME-ONLY: ToolCall(tool='run_command', host='agy', command=None, path=None, seconds=0.0, error=False, delegation=False, command_missing=True)
    INFO-ONLY: ToolCall(tool='run_command', host='agy', command='python3 -m pytest tests/x.py', path=None, seconds=0.0, error=False, delegation=False, command_missing=False)
    CONFLICT corroborate_verifier_turn: indeterminate delegation-present
    INFO-ONLY corroborate_verifier_turn: corroborated corroborated
    ```
    Pytest on pre-existing tests before E-10:
    ```
    46 passed in 8.26s
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: PASTE the diff showing `DASHBOARD_SCHEMA_VERSION = 4` and the renamed test, and a transcript in which a cache file written at schema 3 for an unchanged CONFLICT log is IGNORED (the `_StatsCache` reports a miss and `session_stats` returns the new `tools={'browser_subagent': 1}`), demonstrating the stale-entry hazard F-06 names is closed. Code path: `run_dashboard._StatsCache.__init__`.
  - Observed evidence:
    ```diff
    -DASHBOARD_SCHEMA_VERSION = 3
    +DASHBOARD_SCHEMA_VERSION = 4
    ```
    ```diff
    -    def test_dashboard_schema_version_is_3(self) -> None:
    -        """E-04 / OQ-02: DASHBOARD_SCHEMA_VERSION is 3."""
    -        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 3)
    +    def test_dashboard_schema_version_is_4(self) -> None:
    +        """E-04 (n8we3u): DASHBOARD_SCHEMA_VERSION is 4."""
    +        self.assertEqual(dash.DASHBOARD_SCHEMA_VERSION, 4)
    ```
    Transcript:
    ```
    cache.data after loading schema 3: {}
    cache.get(log_path) misses: 1 hits: 0
    entry tools: {'browser_subagent': 1} categories: {'subagent': 1} commands: {}
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: PASTE the diff of `render_agy_event`'s tool branch and the rendered line at `verbosity=1` for a PARAMETER-FREE CONFLICT step (contains `browser_subagent`), PADDED `tool_info={"name": " run_command "}` (contains `run_command` with no surrounding spaces), and `tool_info="junk"` with `tool_name="x"` (returns a line containing `x`, no exception); paste `python3 -m pytest -o addopts="" -q tests/test_agy_runipd_cli.py` passing with that file unedited (`git diff --stat tests/test_agy_runipd_cli.py` empty).
  - Observed evidence:
    ```diff
    -            tool_info = step.get("tool_info") or {}
    -            tool_name = tool_info.get("name") or step.get("tool_name") or "tool"
    +            raw_tool_info = step.get("tool_info")
    +            tool_info = raw_tool_info if isinstance(raw_tool_info, (dict, Mapping)) else {}
    +            tool_name = agy_tool_name(step) or "tool"
    ```
    Rendered line outputs:
    ```
    1. Parameter-free CONFLICT: '• tool:  browser_subagent'
    2. PADDED: '❯ bash:  run_command'
    3. JUNK tool_info: '• tool:  x'
    ```
    Pytest output:
    ```
    tests/test_agy_runipd_cli.py: 61 passed in 30.53s
    git diff --stat tests/test_agy_runipd_cli.py: empty
    ```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: PASTE the diff of `agy_view.format_record` and its output for CONFLICT, showing `browser_subagent` where V-01 showed `run_command`, for NAME-ONLY, unchanged from V-01, and for `tool_info="junk"` with `tool_name="x"` (a line naming `x`, no exception).
  - Observed evidence:
    ```diff
    -        info = update.get("tool_info") or {}
    -        name = update.get("tool_name") or info.get("name") or "tool"
    +        raw_info = update.get("tool_info")
    +        info = raw_info if isinstance(raw_info, (dict, Mapping)) else {}
    +        name = agy_tool_name(update) or "tool"
    ```
    Output for shapes:
    ```
    CONFLICT: 0001     1 TOOL           DONE   browser_subagent | {"CommandLine":"python3 -m pytest tests/x.py"}
    NAME-ONLY: 0001     2 TOOL           DONE   run_command
    JUNK-INFO: 0001     3 TOOL           DONE   x
    ```
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: PASTE the diff of `runner_stop.event_label` and its output for CONFLICT, NAME-ONLY, INFO-ONLY, `tool_info={"name": 5}` with `tool_name="x"` (now `<type>:x`), a step with no name keys (falls back to `step_type`), and a non-JSON line (`unknown`), and paste `python3 -m pytest -o addopts="" -q tests/test_runner_stop_triggers_e2e.py` passing with the file unedited.
  - Observed evidence:
    ```diff
    -        info = step.get("tool_info")
    -        name = None
    -        if isinstance(info, dict):
    -            name = info.get("name")
    -        name = name or step.get("tool_name") or step.get("step_type")
    +        name = verifier_corroboration.agy_tool_name(step) or step.get("step_type")
    ```
    Output for shapes:
    ```
    CONFLICT: 'unknown:browser_subagent'
    NAME-ONLY: 'unknown:run_command'
    INFO-ONLY: 'unknown:run_command'
    NON-STR-NAME: 'unknown:x'
    NO-NAME-KEYS: 'unknown:tool'
    NON-JSON: 'unknown'
    ```
    Pytest:
    ```
    tests/test_runner_stop_triggers_e2e.py: 2 passed in 3.45s
    ```
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: PASTE the diff of `agy_run._progress_messages` and its output for NAME-ONLY with `tool_info={"parameters": {}}` (now `tool finished: <tool_name>`), for CONFLICT (`browser_subagent`), and for a step with no `tool_info` (no tool message, unchanged).
  - Observed evidence:
    ```diff
    -        name = _compact(tool.get("name", "tool"), 60)
    +        name = _compact(agy_tool_name(step) or "tool", 60)
    ```
    Output for shapes:
    ```
    NAME-ONLY-WITH-INFO: [('step:1:DONE:tool:my_shell', '[phase] tool finished: my_shell')]
    CONFLICT: [('step:2:DONE:tool:browser_subagent', '[phase] tool finished: browser_subagent')]
    NO-TOOL-INFO: []
    ```
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: PASTE `python3 -m pytest -o addopts="" -q tests/test_agy_tool_name_precedence.py` passing with its per-test count. Then PROVE the test detects divergence: temporarily revert `agy_view.format_record` to `update.get("tool_name") or info.get("name") or "tool"`, re-run the file, PASTE the failing rows (CONFLICT must be among them), restore the change, re-run, and paste the pass. Paste `git diff --stat` after restoring to show no residue. FAILS if the test reads any production source text.
  - Observed evidence:
    Initial run:
    ```
    tests/test_agy_tool_name_precedence.py: 9 passed in 0.38s
    ```
    Revert failure:
    ```
    FAILED tests/test_agy_tool_name_precedence.py::test_cross_reader_tool_name_parity[padded-update_fields4-padded_tool]
    FAILED tests/test_agy_tool_name_precedence.py::test_cross_reader_tool_name_parity[reverse_conflict-update_fields1-cmd_tool]
    FAILED tests/test_agy_tool_name_precedence.py::test_cross_reader_tool_name_parity[conflict-update_fields0-sub_tool]
    3 failed, 6 passed in 0.34s
    ```
    Restored pass:
    ```
    tests/test_agy_tool_name_precedence.py: 9 passed in 0.39s
    git diff --stat agent_workflows/agy_view.py: 1 file changed, 6 insertions(+), 2 deletions(-)
    ```
  - Result: pass

- [x] V-10 validates E-10
  - Required evidence: PASTE the new test functions' names and `python3 -m pytest -o addopts="" -q tests/test_verifier_corroboration.py tests/test_run_dashboard.py` output; paste `git diff tests/test_verifier_corroboration.py` showing only ADDED lines (no `-` lines other than diff headers), and `git diff tests/test_run_dashboard.py` showing only additions plus the E-04 rename.
  - Observed evidence:
    New test functions:
    - `test_agy_conflict_and_reverse_conflict_delegation_verdict`
    - `test_agy_info_only_matching_claim_corroborated`
    - `test_dashboard_conflict_and_info_only_shapes_e10`
    Pytest:
    ```
    tests/test_verifier_corroboration.py tests/test_run_dashboard.py: 66 passed in 7.83s
    ```
    Diffs show only additions to `test_verifier_corroboration.py` and additions plus E-04 rename to `test_run_dashboard.py`.
  - Result: pass

- [x] V-11 validates E-11
  - Required evidence: PASTE the new `DECISIONS.md` entry and the `CHANGELOG.md` line, and the output of a search of that CHANGELOG line for the characters U+2014 and U+2013 returning no match.
  - Observed evidence:
    `DECISIONS.md`: `### D164. Antigravity tool-name resolution uses canonical precedence (tool_info.name first) with fail-open delegation`
    `CHANGELOG.md` line:
    `- Fixed: Antigravity session readers now agree on a tool call's name, so a subagent delegation is no longer counted as a shell command and can no longer make a verifier turn read as uncorroborated.`
    Dashes check:
    ```
    Contains U+2014 (em-dash): False
    Contains U+2013 (en-dash): False
    NO EM OR EN DASHES: OK
    ```
  - Result: pass

- [x] V-12 validates E-12
  - Required evidence: PASTE the bare `python3 -m pytest` summary line and the sorted failing node-id list, and the `comm -13` (or equivalent) of baseline vs post-change failing node ids showing it is EMPTY. FAILS if any new failing node id appears.
  - Observed evidence:
    Bare pytest suite run output:
    ```
    8075 passed, 4 skipped, 18 xfailed, 3 warnings in 884.95s (0:14:44)
    Failing node-id list: empty (0 failed).
    Diff with baseline: empty (0 new failures, 12 new passing tests).
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval before execution; do not self-approve.

Open questions: OQ-01, OQ-02 and OQ-03 are `resolved`, none is `Blocking: yes`, and no question remains for a human before execution. The one decision a maintainer may wish to overrule is OQ-01's precedence; it is recorded with its evidence so it can be disputed on the evidence.

Prerequisite: `e08ssu` (which created `tool_call_from_event`) is executed. If `verifier_corroboration.tool_call_from_event` is absent at the executing HEAD, STOP and report.

Execution contract: commit only the paths in `- Scope-Paths:` via `aw commit <plan> -- <paths>`; never `git add -A`, `git add .`, `git commit -a`, or `--no-verify`; do not push; do not create a tag or release. Paste ACTUAL runner output for every validation item. Do not fold `8fiybc` or `iuhx9d` into this change. An out-of-scope edit that proves necessary should be made and then justified through `aw ipd finalize --scope-reason <path>=<why>`, with `--scope-ack` for any declared path left unmodified.

Post-gate lifecycle: after every `V-*` is verified with pasted evidence and `aw ipd lint --phase pre-transition` reports conforming, complete the terminal transition through the tooled path. Under `aw oc run` / `aw agy run` the runner owns that transition; a human-driven execution uses `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Backlog `1kebul` then closes through the handoff (this plan carries `- From-Backlog: 1kebul` and the same `- Blocks-Release: next`).
