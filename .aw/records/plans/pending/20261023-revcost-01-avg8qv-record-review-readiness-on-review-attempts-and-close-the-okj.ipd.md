# IPD: Record review Readiness on review attempts and close the okj4bg review-cost question set

- Date: 2026-10-23
- Kind: child
- Concern: Backlog `i2i81x` is done when every question in prompt `okj4bg` Section 3 is answerable with an `aw runs query` command, or its missing data is listed. Commit `131c9470d` ("runs analyze: per-attempt review-cost facts ...") already shipped the attempt grain (`attempts.jsonl`, views `attempts`/`tools`/`experiment`, `--label`/`--review-variant`, the run-start `git` block), which answers Q1 to Q7. Two gaps remain. Q8 asks for "the review outcome (verdict or readiness, if the run records it)", but the runners never record the plan's `- Readiness:` on the attempt, so `run_analytics_attempts.view_experiment` reports only the disposition and its docstring says "the plan's Readiness value is not recorded by the runners". Q9 (review steps) has no recorded data, and the docs do not list what recording it needs. In addition, prompt `okj4bg` Section 5 requires a report (answerable questions with commands, missing data, wrong Section 1 facts, added recording), and the prompt itself is still `pending`.
- Scope: Record the reviewed plan's normalized `- Readiness:` value on every review attempt (a small, isolated run-record addition that the prompt's Section 2 allows), carry it through the attempt facts, the `aw runs query` allowlists, the `experiment` view and the dashboard, document it plus the Q9 missing data in `docs/run-analytics.md`, file the Section 5 report as a research findings document, and transition prompt `okj4bg` to `executed`. EXCLUDES recording review steps (owned by spec `k3yx72` Section 15 Order 04, which builds the multi-prompt review); EXCLUDES any price table or cost estimate for Antigravity; EXCLUDES the run grain (`run_analytics.PRODUCER_METRIC_KEYS`), which the attempt-grain views do not read; EXCLUDES spec reviews (a spec has no `- Readiness:`).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_dashboard.py, agent_workflows/run_analytics_attempts.py, agent_workflows/run_dashboard_assets/dashboard.js, docs/run-analytics.md, CHANGELOG.md, tests/test_run_analytics_review_cost.py, .aw/records/prompts/**/*okj4bg-runs-analyze-review-cost.prompt.md, .aw/records/research/**/*-revcost-*.findings.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: feature
- Priority: high
- From-Backlog: i2i81x
- Set: revcost
- Order: 1
- Highest E allocated: 10
- Author: opencode
- Id: avg8qv

## Workflow history
- 2026-10-23 reviewed (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 to PR-009 fixed (review record .aw/records/reviews/20261023-revcost-01-avg8qv-record-review-readiness-on-review-attempts-and-close-the-okj.review.md)
- 2026-10-23 to-review (aw set): authored from backlog i2i81x; Q1-Q7 already shipped in 131c9470d, this plan closes Q8 readiness, lists Q9 missing data, and files the okj4bg Section 5 report

- 2026-10-23 draft (opencode): created.

## Goal

Make prompt `okj4bg` Section 3 fully closed: Q8's review outcome includes the plan's Readiness, Q9's missing recording is listed, and the prompt's Section 5 report exists as a tracked findings document, so backlog `i2i81x` can be closed on evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: record Readiness on review attempts

- [ ] E-01 In `runner_shared.execute_item_core`, immediately after the call `disposition, outcome = reconcile_disposition(` (the one passing `plan_repo=Path(work_dir) if work_dir else None`) returns, when `is_review` is true and `queue_entry_type(item) == "ipd"`, read the plan through `queue_artifact_path(Path(work_dir) if work_dir else repo, item)` (the same tree `reconcile_disposition` reads, `plan_repo or repo`) and store `attempt["review_readiness"] = _schema.read_readiness(text)` (one of `go`, `go-pending-approval`, `no-go`, or `None`), importing locally as `from agent_workflows import ipd_schema as _schema` the way the module's other call sites do. Wrap the path resolution and `read_text` in `try/except (OSError, UnicodeDecodeError, DriverError)` that stores `None`, so an unreadable plan never changes the disposition. Do not write anything to the plan; this reads the field `/plan-review` wrote. The value is recorded whatever the disposition (a later `fail-gate`, for example from the silent-turn gate, keeps it); consumers read it beside `disposition`. Turns that return before `reconcile_disposition` (spawn failure, interruption, deliberate stop) do not reach this line and carry no key.
  - Depends on: none
  - Expected outcome: a plan-review attempt that reaches `reconcile_disposition` carries `review_readiness` in `state.json` on both hosts (the code is shared through `execute_item_core`); execute, plan and spec-review attempts do not carry the key.
  - Execution state: pending

- [ ] E-02 Add a test class `ReviewReadinessRecordingTests` to `tests/test_run_analytics_review_cost.py` that drives `oc_runipd.execute_item` for a review item with `run_opencode` patched (the harness of `tests/test_rereview_reviewed_plan.py::test_execute_item_core_rereview_demotes_and_turn_sees_to_review`: a git repo, a plan written at `- Status: to-review` with no Readiness line, `isolate_worktree: False`). The item must be a FRESH review, so it must NOT carry `"rereview": True`: a re-review with no Readiness line ends `fail-gate` by design (`reconcile_disposition`, refusal code `rereview-no-fresh-review`), which would break case two. Case one: the fake turn changes the plan to `- Status: reviewed` and adds `- Readiness: go-pending-approval`, and the test asserts `item["attempts"][-1]["review_readiness"] == "go-pending-approval"`. Case two: the fake turn changes the plan to `reviewed` with no Readiness line, and the test asserts the key is present and `None`. Both cases also assert `item["status"] == "reviewed"`, the status the same turn produces today (measured at review with exactly this harness: case one `reviewed`, case two `reviewed`, and the same case two with `rereview: True` `fail-gate`).
  - Depends on: E-01
  - Expected outcome: two passing behavioral tests that exercise the real `execute_item` path.
  - Execution state: pending

### Task group 2: carry Readiness through the analysis

- [ ] E-03 In `run_dashboard.collect_rows`, add a `"readiness"` entry to the attempt `base` row dict that keeps the three cases E-01 records apart: the attempt's `review_readiness` value when it is a non-empty string; the literal `"absent"` when the key is present but `None` (the review left no valid Readiness); and `""` when the key is missing (an attempt not recorded by this change: older runs and non-review actions). Also add `"readiness": ""` to the synthesized `base` dict for unclaimed session files. Add `"readiness"` to `COLUMNS` and `ATTEMPT_FACT_FIELDS`, and bump `ATTEMPT_FACTS_SCHEMA_VERSION` from 2 to 3. In `run_analytics_attempts`, add `"readiness"` to `ATTEMPT_FILTER_FIELDS` and `ATTEMPT_GROUP_FIELDS`. In `view_experiment`, take the last main attempt's readiness the way `disposition` is taken today (the `last = max(mains, ...)` row), add a `"readiness"` count map to each row using `_label` (so `""` reads `(not recorded)`), and replace the docstring sentence "the plan's Readiness value is not recorded by the runners, so it is not reported" with one saying `readiness` comes from the attempt's `review_readiness`, recorded from this plan's commit onward, with `absent` meaning the review wrote no valid value and `(not recorded)` meaning the run predates the recording.
  - Depends on: E-01
  - Expected outcome: `aw runs query experiment` rows carry a `readiness` count map, `aw runs query attempts --group-by readiness` is accepted, and `aw runs query schema` lists `readiness` among the attempt-grain filter and group-by fields.
  - Execution state: pending

- [ ] E-04 In `run_dashboard_assets/dashboard.js`, add `readiness` to the list of fields normalized to `(none)`, to `DIMS` (label `Readiness`, help text naming `go` / `go-pending-approval` / `no-go`, `absent` when the review wrote no valid value, recorded for plan reviews only), to `FACETS`, and to `GROUPABLE`.
  - Depends on: E-03
  - Expected outcome: the dashboard's sidebar and split-by selectors offer Readiness.
  - Execution state: pending

- [ ] E-05 Extend the fixture in `tests/test_run_analytics_review_cost.py`: `_review_run` gains a keyword `readiness` (default: a sentinel meaning "write no key") that its inner `att(...)` writes as `review_readiness` on the main attempt (a string, or `None` for the key-present-but-absent case). In `AttemptQueryTests.setUp`, give most of the 14 runs `readiness="go"`, give at least one run `readiness=None`, and leave at least one run without the key (an older run). Keep the existing 14-run, two-variant, two-model shape so every existing assertion (row counts, `n` values, medians) is unchanged. Add tests that (a) `query.run_query("experiment", repo=self.repo, filters=["label=exp1"])` rows carry the expected `readiness` count maps, including `go`, `absent`, and `(not recorded)`, with each map's counts summing to that row's `items`; (b) `query.run_query("attempts", repo=self.repo, group_by="readiness", metric="cost", stat="count")` returns one row per readiness label present in the fixture; (c) `query.run_query("attempts", repo=self.repo, filters=["readiness=go"], metric="cost", stat="count")` counts only the `go` main sessions; (d) the published `attempts.jsonl` header line reports `"schema": 3` and its row lines carry a `readiness` key; (e) `query.run_query("schema").payload["attempt_grain"]` lists `readiness` in both `filter_fields` and `group_by_fields`. Update `test_experiment_view` only where the new `readiness` key changes what it asserts. Assertions name the behavior (labels and counts derived from the fixture), not test-function names or collected counts.
  - Depends on: E-03
  - Expected outcome: behavioral tests that run the real `run_analyze` leaf and `run_query` and assert on their output; every pre-existing test in the file still passes.
  - Execution state: pending

### Task group 3: document, report, and file the prompt

- [ ] E-06 In `docs/run-analytics.md` section "Review cost: per-attempt analysis": change the existing row `| Experiment comparison | aw runs query experiment --filter label=<label> |` to say it includes the review outcome (disposition and Readiness) per plan, variant and model, and add the row `| Attempts by Readiness | aw runs query attempts --filter action=review --group-by readiness --metric cost,steps |` to the question table (backticks as the existing rows use them); replace the sentence ending "the plan's Readiness value is not recorded by the runners." in the **Experiment** bullet with the new behavior: the `readiness` count map, what `absent` and `(not recorded)` mean, and the from-commit caveat; and add a short subsection "What is not recorded yet" listing: review steps (Q9: needs the review step, meaning which prompt of a multi-prompt review, and the pass number recorded for each prompt, which spec `k3yx72` Section 9.3 specifies and its Section 15 Order 04 builds), Antigravity cost (tokens only, no price table is applied), and Readiness on runs started before this change. No em or en dashes (user-facing prose).
  - Depends on: E-03
  - Expected outcome: every `okj4bg` Section 3 question maps to a command or to a named missing field in the docs.
  - Execution state: pending

- [ ] E-07 Add one `CHANGELOG.md` entry beside the existing "per-attempt review-cost analysis" entry: review attempts record the plan's Readiness, which `aw runs query experiment` and `--group-by readiness` report. No em or en dashes.
  - Depends on: E-03
  - Expected outcome: one added CHANGELOG line.
  - Execution state: pending

- [ ] E-08 Create the prompt's Section 5 report with `aw research new --kind findings --set revcost --slug runs-analyze-review-cost-report --summary "okj4bg Section 5 report: review-cost questions, commands, missing data, corrected facts" --apply` (it mints the doc's own id6 and writes `.aw/records/research/<date>-revcost-<NN>-<id6>-runs-analyze-review-cost-report.findings.md`; a dry run at review previewed `20261023-revcost-01-<id6>-runs-analyze-review-cost-report.findings.md`), then fill it with five sections: (1) each Section 3 question Q1 to Q9 with its exact `aw runs query` command (from the docs table), Q9 answered as "not recorded" with a pointer to (2); (2) the missing data (Q9 review steps; Antigravity cost; Readiness before this commit); (3) the Section 1 facts found wrong when checked against code (at minimum F-03 and F-04 below: `state.json` now carries a `git` block and `options.label`/`options.review_variant`; `defect-report-recorded` is not itself a redo, the re-ask it may trigger is counted through `defect_reasked`), and, if `.aw/records/runs/` exists in the executing workspace, a re-measurement of the Section 1 table through `aw runs analyze` and the commands above, or the line "run data not present in this workspace; facts checked against code only"; (4) the recording added (`review_readiness`, from this plan's commit, on both hosts); (5) the test command and its actual summary line: run the E-10 named-file pytest command here, after E-02 to E-05 are in place, and paste its real summary line (E-10 re-runs it as the final gate). Then run `aw research set-outcome <findings-id6> --to adopted --consumed-by avg8qv --apply` so the report records that this plan used it, and `aw research index` (its `INDEX.json`/`INDEX.md` outputs are gitignored, so nothing from the index is committed).
  - Depends on: E-02, E-05, E-06
  - Expected outcome: a tracked `*-revcost-*-runs-analyze-review-cost-report.findings.md` under `.aw/records/research/`, matched by the `Scope-Paths` glob, whose front matter names `avg8qv` in `consumed-by`.
  - Execution state: pending

- [ ] E-09 Transition the prompt with `aw prompts set executed okj4bg --message "Section 5 report filed as research <findings-id6> (plan avg8qv)" --yes --no-commit` (`--no-commit` because E-10's single path-scoped commit carries the move; without `--commit` a non-interactive call commits nothing anyway, per `cli._add_commit_flags`). The move leaves two tracked records citing the old `prompts/pending/` path in prose (backlog `i2i81x` and spec `k3yx72`); leave them unedited, since both are outside this plan's fence and the id6 `okj4bg` still resolves; E-08's report names the new path.
  - Depends on: E-08
  - Expected outcome: the prompt file lives under `.aw/records/prompts/executed/` and is no longer under `pending/`.
  - Execution state: pending

- [ ] E-10 Run `python3 -m pytest -o addopts="" -n auto tests/test_run_analytics_review_cost.py tests/test_run_dashboard.py tests/test_rereview_reviewed_plan.py tests/test_defect_report.py` (no `-q`, so the `N passed` summary line prints), then the bare core gate `python3 -m pytest`, then `aw check`. `aw check` passes when it reports zero `error` findings and no `warning` this plan introduced; at review it exited 1 on two pre-existing warnings (`check.system-layout-missing` on `.aw/system/layout.json`, `check.identity-absent-from-name` on spec `k3yx72`), which are not this plan's to fix, so compare against that baseline re-derived at execution rather than against exit 0. Commit through `aw commit avg8qv -- <paths>`, naming each changed file explicitly: the six code, docs and test files, the new findings document, and BOTH sides of the prompt move (the removed `pending/` path and the added `executed/` path). Never push.
  - Depends on: E-02, E-04, E-05, E-06, E-07, E-08, E-09
  - Expected outcome: both pytest runs report no failures; `aw check` reports no error and no new warning; one path-scoped commit containing only declared paths.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The attempt grain lives in `run_dashboard.collect_rows` / `run_dashboard.ATTEMPT_FACT_FIELDS` and is queried through `run_analytics_attempts` (allowlists `ATTEMPT_FILTER_FIELDS`, `ATTEMPT_GROUP_FIELDS`); `run_analytics_query.run_query` branches to it for views `attempts`, `tools`, `experiment`. Adding a field means adding it to the allowlists, not a free-form expression (prompt `okj4bg` Section 2).
- `ATTEMPT_FACTS_SCHEMA_VERSION` is bumped when `ATTEMPT_FACT_FIELDS` changes; `attempts.jsonl` is regenerated on every analyze, so no cache migration is needed. The session-stats cache (`DASHBOARD_SCHEMA_VERSION`) keys `session_stats` output, which this plan does not change.
- `ipd_schema.read_readiness` is the existing pure reader that normalizes to `READINESS_VALUES` (`go`, `go-pending-approval`, `no-go`) or `None`.
- `reconcile_disposition` reads the lane tree (`plan_repo or repo`) because the review's edits are uncommitted there at that point; the new read follows the same rule.
- `aw runs analyze` writes only under `runner_shared.analytics_root` (gitignored). Unchanged here.
- Under-powered refusal (`run_analytics_statistics.MINIMUM_SAMPLE_SIZE = 12`, applied by `run_analytics_attempts.summarize_group`) is untouched.
- Tests exercise code and assert on outputs (AGENTS.md, no code-pinning). `tests/test_run_analytics_review_cost.py` carries no `core` marker, so it runs in the thorough tier and is named explicitly in E-10.
- Commit only through `aw commit avg8qv -- <paths>`; never push. Cite code by SYMBOL or quoted string (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `git show --stat 131c9470d`; `docs/run-analytics.md` section "Review cost: per-attempt analysis" | The attempt grain, the three views, the Review cost tab, `--label`, `--review-variant` and the run-start `git` block already exist; the docs table maps Q1 to Q8 to commands. |
| F-02 | `run_analytics_attempts.view_experiment` docstring: "the plan's Readiness value is not recorded by the runners, so it is not reported"; `grep -n review_readiness agent_workflows/` returns nothing | Q8's "verdict or readiness" half is the one Section 3 answer that is missing data a small record addition can supply. |
| F-03 | `runner_shared.run_start_git_record` and `runner_shared.add_run_label_flags`; `run_dashboard._run_context` | `okj4bg` Section 1 says `state.json` has "no git commit and no user label". That is no longer true for runs started after `131c9470d`: `state["git"]` holds `commit`, `dirty`, `aw_version`, and `options` holds `label` and `review_variant`. |
| F-04 | `runner_shared.execute_item_core` emits `"event": "defect-report-recorded"`; `run_dashboard._redo_events` does not read it | `defect-report-recorded` fires on every recorded defect report, not only on a redo; the re-ask it can trigger is already counted via `attempt["defect_reasked"]` and the `defect-reask` session row. So it should not be counted as a redo; the report says so. |
| F-05 | `.aw/records/specs/reviewed/20261017-k3yx72-01-k3yx72-plan-review-redesign.spec.md` Sections 9.3, 13.4, 15 | Q9's review-step recording ("the last completed prompt" per step) is designed in `k3yx72` and assigned to its Order 04. Recording it here would preempt that design, so this plan lists it as missing data. |
| F-06 | `run_analytics_pricing` module docstring: "THERE IS NO `cache_write` RATE COLUMN" | Cost share for cache writes cannot be computed from recorded cost splits; token share for `cache_write` is already reported by `summarize_group`'s `token_share`. No new price data is needed or invented. |
| F-07 | `ls .aw/records/runs` in this authoring lane: absent | Run data is not present in a lane worktree, so Section 1 numbers cannot be re-measured here; E-08 makes the re-measurement conditional and says so explicitly when it cannot run. |
| F-08 | `runner_shared.reconcile_disposition`, the `if item.get("rereview"):` branch refusing with code `rereview-no-fresh-review` when no `- Readiness:` line exists; review-time probe driving `oc_runipd.execute_item` with the `tests/test_rereview_reviewed_plan.py` harness | A FRESH review that writes `reviewed` with no Readiness ends `reviewed`; the same turn on a `rereview: True` item ends `fail-gate`. E-02 must therefore use a fresh review item, and `review_readiness: None` on a `reviewed` attempt is a reachable state worth reporting (`absent`). |
| F-09 | `cli._add_commit_flags` docstring: "non-interactively it is a NO-OP (never commits silently)"; `.aw/.gitignore` entries `records/research/INDEX.json`, `records/research/INDEX.md` | `aw prompts set` commits nothing in an unattended turn unless `--commit` is passed, and the research index is not tracked; E-09 uses `--no-commit` and E-10 commits both sides of the prompt move. |
| F-10 | `aw check --json` at review, base `623eb73cb`: 0 errors, 2 warnings (`check.system-layout-missing`, `check.identity-absent-from-name` on spec `k3yx72`) | `aw check` already exits 1 before this plan runs, so "passes" must mean "no error and no new warning", re-derived at execution. |

## Proposed changes (ordered, validatable)

1. E-01 records `review_readiness` on each plan-review attempt; E-02 proves it through `execute_item`.
2. E-03 carries the field into attempt facts, allowlists and the experiment view; E-04 exposes it on the dashboard; E-05 proves the query output.
3. E-06 and E-07 document the change and the missing data; E-08 files the Section 5 report; E-09 transitions the prompt.
4. E-10 runs the suites and `aw check`, then commits.

## Deferred / out of scope (with reason)

- Recording review steps (Q9).
  - Carrier-Declined: no work is owed here; spec `k3yx72` Section 15 Order 04 builds the multi-prompt review and its per-prompt recording, and this plan lists the needed field in the docs and report (F-05).
- Antigravity dollar estimates.
  - Carrier-Declined: no work is owed; prompt `okj4bg` Section 2 forbids invented prices, and tokens are already reported where cost is missing.
- Counting `defect-report-recorded` as a redo.
  - Carrier-Declined: no work is owed; the event is not a redo (F-04).

## Scope check

- Over-scope: none. Every declared path is touched by a named E-item.
- Under-scope: none. Q1 to Q7 are answered by existing code (F-01), Q8 by E-01 to E-05, Q9 by the missing-data listing in E-06 and E-08, and Section 5 by E-08.

## Required tests / validation

Invariants and the test that pins each:

- A review attempt's disposition is unchanged by the new recording: E-02 asserts `item["status"] == "reviewed"` in both cases.
- Readiness recorded on a plan-review attempt is the normalized field value, or `None` when absent: E-02 cases one and two.
- Older runs (no key) stay queryable and report `(not recorded)`, distinct from `absent`: E-05 (a).
- `aw runs query` stays allowlisted; `readiness` is accepted only because it is on the lists: E-05 (b), (c), (e), plus the existing `test_disallowed_fields_refused`.
- Existing attempt-grain numbers are unchanged: every pre-existing test in `tests/test_run_analytics_review_cost.py` and `tests/test_run_dashboard.py` still passes.

Commands:

- `python3 -m pytest -o addopts="" -n auto tests/test_run_analytics_review_cost.py tests/test_run_dashboard.py tests/test_rereview_reviewed_plan.py tests/test_defect_report.py`: all pass, summary line pasted (E-02, E-05, E-10).
- Bare `python3 -m pytest` summary line pasted (E-10).
- `aw check` result pasted, no error and no warning beyond the pre-existing baseline (E-10, F-10).

## Spec / documentation sync

`docs/run-analytics.md` is updated (E-06). No spec describes the attempt-grain field or view tables (the only spec naming this work, `k3yx72`, lists it as a prerequisite in prose, Section 13.2), so no `.spec.md` is declared in Scope-Paths. The plan cites `k3yx72` as evidence only and graduated from backlog `i2i81x`, not from that spec, so it deliberately carries no `- From-Spec:`; the advisory `check.plan-spec-link-missing` (info) it raises is expected. The runner records the new attempt key on both hosts through the shared `execute_item_core`; no runner spec (`25kzda`) enumerates attempt-record keys, so none is amended.

## Open questions

### OQ-01: Record Readiness on the attempt, or read it from the plan at analysis time?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: record it on the attempt. Analysis runs long after the plan has moved and been re-reviewed, so reading the current plan would attribute a later review's Readiness to an earlier attempt. The prompt allows "a small, isolated addition to the run records" (Section 2), and E-01 is one key written after the existing disposition read.

### OQ-02: Should the experiment view's outcome merge disposition and readiness into one field?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no, keep `outcome` (disposition counts) unchanged and add a separate `readiness` count map, so existing consumers of `outcome` and the existing `test_experiment_view` assertions keep their meaning.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git diff` hunk of `agent_workflows/runner_shared.py` showing the `review_readiness` write after the `reconcile_disposition(...plan_repo=...)` call in `execute_item_core`, guarded by `is_review` and `queue_entry_type(item) == "ipd"`, reading through `queue_artifact_path` on the `work_dir`-or-`repo` tree, with the `(OSError, UnicodeDecodeError, DriverError)` fallback to `None`, and no write to the plan file.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_run_analytics_review_cost.py -k ReviewReadinessRecording` output with every collected test PASSED and none skipped, and quote the asserting lines showing the two behaviors pinned: a `go-pending-approval` turn records `review_readiness == "go-pending-approval"`, a no-Readiness turn records the key present and `None`, and both end `item["status"] == "reviewed"` for an item with no `rereview` flag (the observation is produced by `oc_runipd.execute_item` through `runner_shared.execute_item_core`, reachable as demonstrated at review).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the `git diff` hunks adding `readiness` to both `base` dicts in `run_dashboard.collect_rows` (with the value / `absent` / `""` mapping), `run_dashboard.COLUMNS`, `run_dashboard.ATTEMPT_FACT_FIELDS`, `ATTEMPT_FACTS_SCHEMA_VERSION = 3`, `run_analytics_attempts.ATTEMPT_FILTER_FIELDS`, `ATTEMPT_GROUP_FIELDS`, and the `view_experiment` change including the replaced docstring sentence.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `git diff` of `agent_workflows/run_dashboard_assets/dashboard.js` showing `readiness` in the normalization list, `DIMS`, `FACETS` and `GROUPABLE`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_run_analytics_review_cost.py` output with every collected test PASSED (pre-existing ones included) and none failed or skipped, and quote the asserting lines that pin each of E-05's behaviors (a) to (e): experiment `readiness` maps with `go`, `absent` and `(not recorded)` summing to `items`; one group-by row per readiness label; the `readiness=go` filter count; the schema-3 header and `readiness` row key; and `readiness` in the schema view's attempt-grain fields.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `git diff` of `docs/run-analytics.md` showing the changed experiment row, the new "Attempts by Readiness" row, the replaced Readiness sentence (with `absent` and `(not recorded)` explained), and the "What is not recorded yet" subsection naming review steps, Antigravity cost and pre-change Readiness; paste `git diff -U0 docs/run-analytics.md | grep '^+' | grep -nP '[\x{2013}\x{2014}]'` returning nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `git diff` of `CHANGELOG.md` showing exactly one added line, with no em or en dash.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the path of the new findings document, its front matter (showing `kind: findings`, `set: revcost`, and `consumed-by` naming `avg8qv`), its five section headings, the Q1 to Q9 command lines (Q9 as not recorded), the corrected-facts list containing F-03 and F-04, either the re-measurement output or the "run data not present in this workspace" line, and the pasted pytest summary line; paste the `aw research index` output and then `aw research find --id <findings-id6>` showing the new document in the manifest.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the `aw prompts set executed okj4bg ...` output, `ls .aw/records/prompts/executed/ | grep okj4bg` showing the file, `ls .aw/records/prompts/pending/ | grep okj4bg` returning nothing, and the file's first line showing `Status: executed`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste the actual summary line of the named-file pytest run (no `failed`, no `error`), the bare `python3 -m pytest` summary line (and any budget block verbatim), the `aw check` severity counts with every `error` and `warning` diagnostic listed and each warning shown to be pre-existing (present on the base commit) rather than introduced, and `git show --stat HEAD` listing only paths declared in `- Scope-Paths:`, including both the deleted `prompts/pending/` and added `prompts/executed/` prompt paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). All open questions are resolved. Scope fence: the paths in `- Scope-Paths:`; do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. Commit only through `aw commit avg8qv -- <paths>`; never push. Paste actual test output. Move the plan to `.aw/records/plans/executed/` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
