# IPD: Drill-down run analytics dashboard for aw runs analyze

- Date: 2026-09-27
- Kind: child
- Concern: The HTML report `aw runs analyze` publishes is not useful for cost-benefit-risk questions (which model/host/action costs more tokens, time, tool calls; what retries and failures waste). Its row grain is one run plus four state.json phase sums, it carries no tool-call data, and it has no drill-down.
- Scope: Add a per-attempt fact extractor over run `state.json` plus the per-session JSONL logs (both hosts), cached per session file inside the analytics namespace, and a new self-contained offline drill-down dashboard rendered from it. Publish the dashboard as the bundle's `index.html`; keep the previous renderer's document in the same bundle as `report.html`.
- Scope-Paths: agent_workflows/run_dashboard.py, agent_workflows/run_dashboard_assets/dashboard.js, agent_workflows/run_dashboard_assets/dashboard.css, .aw/records/plans/pending/20260927-runsdash-01-97i0ao-drill-down-run-analytics-dashboard-for-aw-runs-analyze.ipd.md, agent_workflows/run_analytics_cli.py, tests/test_run_dashboard.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Work-Kind: feature
- Priority: medium
- Set: runsdash
- Order: 1
- Highest E allocated: 06
- Author: opencode
- Id: 97i0ao
- Approval: 2026-09-28, human ("approved"): Maintainer requested this dashboard directly in session (2026-09-27) and asked it be done in an isolated worktree.

## Workflow history
- 2026-09-28 approved (aw set, --by-human): Maintainer requested this dashboard directly in session (2026-09-27) and asked it be done in an isolated worktree.

- 2026-09-27 draft (opencode): created.
- 2026-09-27 to-review (opencode): authored in full from the maintainer's request to replace the `aw runs analyze` HTML with a drill-down dashboard.

## Goal

Give the maintainer a dashboard that answers cost-benefit-risk questions about driver runs: per model, host, action (review / execute / verify / gate-answer / defect-reask), outcome, Set and time, compare tokens, cost, wall time, LLM steps, tool calls by category (read / write / edit / shell / search / todo), shell command kinds, and tool errors, and drill down from any aggregate to the individual attempts behind it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: facts

- [x] E-01 Implement `run_dashboard.session_stats` parsing one session JSONL of either host (OpenCode `step_finish`/`tool_use`; Antigravity `step_update`/`result`) into steps, tokens (input/output/cache/reasoning), cost, per-tool counts, tool errors, tool seconds, shell command kinds, first/last timestamps.
  - Depends on: none
  - Expected outcome: a dict of numeric stats per session file; malformed lines skipped, never raised.
  - Execution state: performed
- [x] E-02 Implement `run_dashboard.collect_rows` walking every canonical run's `state.json` queue attempts, joining each attempt's `log` and `verify_log` plus the other session files of that item/attempt (`-gate-answer`, `-defect-reask`) to one row per session, carrying run/set/id6/action/attempt/recovery/disposition/verification/host/model/date; with a per-session-file stats cache keyed by (size, mtime_ns) stored under the analytics namespace.
  - Depends on: E-01
  - Expected outcome: rows for the real corpus; a second call re-parses no unchanged session file.
  - Execution state: performed

### Task group 2: dashboard

- [x] E-03 Write the offline dashboard assets (`dashboard.css`, `dashboard.js`) and `run_dashboard.render_dashboard` embedding columnar rows as JSON: global filter chips (host, model, action, outcome, Set, date range, text), KPI strip, Compare view (group-by x metric, median/IQR/mean/sum/n bars, click a bar to filter), Trend view (per day/week stacked by a dimension), Scatter view (x/y metrics, color by dimension, log toggle, click a point to open the attempt), Tools view (tool mix per group), Waste view (tokens/cost/time spent on attempts that did not succeed, and on retries), Attempts table (sortable, paginated, CSV export) and an attempt detail panel; state kept in the URL hash.
  - Depends on: E-02
  - Expected outcome: a single HTML file with no network references that opens from disk.
  - Execution state: performed
- [x] E-04 Wire the dashboard into `run_analytics_cli.run_analyze` and `_publish_snapshot` so the bundle's `index.html` is the dashboard and the previous document is published as `report.html`; a dashboard failure falls back to the previous document as `index.html` rather than failing the sweep.
  - Depends on: E-03
  - Expected outcome: `aw runs analyze` publishes `index.html` (dashboard) and `report.html` (classic).
  - Execution state: performed

### Task group 3: tests and docs

- [x] E-05 Add `tests/test_run_dashboard.py` covering both session formats, the attempt/verify/gate row join, cache reuse, the offline scan, HTML-in-data escaping, and the CLI publication of both files.
  - Depends on: E-04
  - Expected outcome: new tests pass; full suite passes.
  - Execution state: performed
- [x] E-06 Add a CHANGELOG entry (no em or en dashes) describing the new dashboard.
  - Depends on: E-04
  - Expected outcome: CHANGELOG Unreleased section names the dashboard and `report.html`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Publication goes through `run_analytics_report.publish_bundle`, which refuses targets outside the analytics namespace and orders unknown names before the manifest (`_order_key`), so adding `report.html` needs no change there.
- Offline is enforced by `run_analytics_spa.scan_for_network_references`; the dashboard reuses it.
- Embedded strings must survive `</script>`: reuse `run_analytics_spa.escape_json_for_script`.
- Packaged assets live beside the module (`run_analytics_spa.ASSETS_DIRNAME = "run_analytics_assets"`); the wheel packs the whole `agent_workflows` package (`[tool.hatch.build.targets.wheel] packages`), so a sibling asset dir ships.
- The run resolver is `run_analytics_cli._resolve_run_dirs` (delegates to `run_viewer.resolve_target_runs_detailed`), which excludes the analytics tree.
- Commit via `aw commit <plan> -- <paths>`; run the suite bare as `python3 -m pytest`.

## Findings

- Measured 2026-09-27 over the local corpus: 298 run dirs, 1,532 session JSONL files, 769 MB. OpenCode sessions carry per-step tokens and `cost` in `step_finish`, and ~94k `tool_use` parts with status and timings; Antigravity sessions carry ~33k `agent_response` steps with `usage` and ~32k tool steps with `duration_seconds`.
- The current cache facts (`entry.json` `metric_facts`) hold only run totals: no model, no tool data, no per-attempt grain. The current renderer (`_render_report_html`) re-reads `state.json` for four phase sums only.
- Model identity: recorded in `state.json` `options.model` or `options.cost_attribution.model` for about 100 of 298 runs; OpenCode session JSONL carries no model id. Rows without it are labeled `(unrecorded)` rather than guessed.

## Proposed changes (ordered, validatable)

1. New `agent_workflows/run_dashboard.py` (E-01, E-02, E-03 render function).
2. New assets under `agent_workflows/run_dashboard_assets/` (E-03).
3. `run_analytics_cli.run_analyze` and `_publish_snapshot` publish the dashboard as `index.html` and the classic document as `report.html` (E-04).
4. Tests and CHANGELOG (E-05, E-06).

## Deferred / out of scope (with reason)

- Recovering model identity for runs that never recorded it (for example from a host's private database outside the repo): reading tool-internal stores outside the run records is a privacy and portability change needing its own decision. Going forward the drivers should record it.
  - Carrier: 7yz545
- Changing the Order 05 cache schema or the `aw runs query` views: the dashboard keeps its own disposable stats cache so no existing contract moves.
  - Carrier-Declined: not an obligation; no existing contract needs to move for this feature.
- Removing the classic renderer: kept as `report.html` so nothing is lost.
  - Carrier-Declined: deliberate retention, nothing outstanding.

## Scope check

- Over-scope: none.
- Under-scope: none; the cost of verification turns is separated because each verify session is its own row.

## Required tests / validation

- `python3 -m pytest tests/test_run_dashboard.py -o addopts=""` passes.
- Full suite `python3 -m pytest` passes.
- Real-corpus render: `aw runs analyze` in the main checkout publishes `index.html` and `report.html`; row count and size reported; offline scan clean.

## Spec / documentation sync

N/A for specs: no spec governs the report document layout (the analytics SPA contract is plan `6eq3oq`'s module docstring, and the classic document is preserved unchanged as `report.html`). CHANGELOG updated (E-06).

## Open questions

### OQ-01: Should the classic report remain published?

- Blocking: no
- Status: resolved
- Owner: opencode
- Resolution or deferral rationale: yes, as `report.html`; it costs one render and loses nothing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: pasted test output for both host formats showing parsed steps, tokens, tool counts and errors.
  - Observed evidence: `tests/test_run_dashboard.py::SessionStatsTests` (OpenCode 3 steps: input 300, output 30, cache_read 3000, cost 0.6, 6 tool calls, 3 errors, categories {shell:3, read:3}, commands {test:3}; Antigravity: 1 step, input 200, output 20, reasoning 5, cache 50, 2 tool calls counted from DONE/ERROR only, 1 error, commands {git:1}). Run: `python3 -m pytest tests/test_run_dashboard.py -o addopts=""` -> `13 passed in 0.40s`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted test output for the row join and cache reuse, plus the real-corpus row count.
  - Observed evidence: `CollectRowsTests` pass (roles [(1,main),(1,verify),(2,gate-answer),(2,main)], log-over-state numbers, state fallback when the log is missing, per-host unrecorded model label, agy run, cache 0/4 -> 4/0 -> 3/1 after touching one file). Real corpus: `{'runs': 298, 'runs_without_state': 1, 'sessions': 1327, 'cache_hits': 0, 'cache_misses': 1327}` 1522 rows in 12.1s cold; warm `cache_hits: 1327, cache_misses: 0` in 0.25s.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted offline-scan and escaping test output, plus the real-corpus dashboard size.
  - Observed evidence: `RenderTests.test_offline_and_escaped` passes (scan_for_network_references == [], `</script>` in data does not terminate the island, JSON round-trips). Real corpus index.html 586133 bytes. Headless Chromium over all 7 views x 3 grains: `errors []`, no NaN/undefined/Infinity in any view; clicks: bar -> `768 sessions match Stage: execute`, trend bar -> `Dates: 2026-08-24 to 2026-08-30`, scatter point opens the drawer (`True`), facet checkbox filters.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: pasted `aw runs analyze` output and a listing of the published bundle showing `index.html` and `report.html`.
  - Observed evidence: `AW_NO_REEXEC=1 python3 -m agent_workflows runs analyze --dir <main>` -> `CONFORMS  analyzed 298 run(s): 199 cached, 99 rebuilt, 0 skipped`; `ls analytics/latest/`: `analysis.json 49842`, `index.html 586133`, `manifest.json 638`, `report.html 236484`. `AnalyzePublishesDashboardTests` pass (manifest lists index.html, report.html, analysis.json; dashboard failure falls back to the classic document).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: pasted full-suite summary line.
  - Observed evidence: Full suite, bare: `2899 passed, 2 skipped, 3 warnings in 44.36s`.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: pasted CHANGELOG diff hunk.
  - Observed evidence: CHANGELOG.md hunk: `- Added: \`aw runs analyze\` now publishes a drill-down dashboard as the report's \`index.html\`. ... The previous report is kept beside it as \`report.html\`.` (no em or en dashes).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only once `Status: approved`. Execute in an isolated worktree allocated by `aw work begin`, commit through `aw commit`, never push. Move to `executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` carries pasted evidence.
