# IPD: aw runs non-empty --agent stream and refusals emit aw.agent/v1 records

- Date: 2026-10-14
- Kind: child
- Concern: `aw runs --agent` and `aw runs list --agent` emit unenveloped JSON dicts on non-empty streams (plus an invalid `{"kind": "excluded_runs"}` pseudo-record when runs are excluded by filters and zero bytes on `--issues --agent` with no issues), and emit unenveloped `{"error": ..., "exit_code": 2}` payloads on `--agent` and `--json` for the three `--summary-only` flag conflicts and invalid `--since` specs.
- Scope: Wrap all `run_viewer.run_viewer_cli` `--agent` stream branches (`default`, `--latest-only`, `--summary-only`, `--issues`) in validated `aw.agent/v1` `kind: "item"` records followed by a validated terminal `kind: "summary"` record carrying `excluded_runs`, `findings`, and `filters`, and convert the four usage/flag-conflict/`--since` refusal branches to emit validated `aw.agent/v1` `kind: "error"` records (`outcome: "cannot-run"`, `exit: 2`) under `--agent` and `--json`.
- Scope-Paths: agent_workflows/run_viewer.py, tests/test_run_viewer.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/plans/pending/20261014-4d3ynu-01-3jg79f-aw-runs-non-empty-agent-stream-and-refusals-emit-aw-agent-v1.ipd.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: 4d3ynu
- Blocks-Release: next
- Set: 4d3ynu
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: 3jg79f

## Workflow history

- 2026-10-14 to-review (Antigravity): created from backlog item 4d3ynu, ready for review.

## Goal

Ensure `aw runs --agent` and `aw runs list --agent` emit schema-valid `aw.agent/v1` JSONL records across all non-empty and `--issues` execution paths (`kind: "item"` records followed by a terminal `kind: "summary"` record carrying `total`, `emitted`, `omitted`, `findings`, `filters`, and optional `excluded_runs`), and ensure all four flag-conflict and `--since` refusal paths emit validated `aw.agent/v1` `kind: "error"` (`outcome: "cannot-run"`, `exit: 2`) records under `--agent` and `--json` while preserving the `--json` success payload shape and all exit codes.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Refusal error records and `--agent` item/summary stream in `agent_workflows/run_viewer.py`

- [ ] E-01 In `agent_workflows/run_viewer.py` (`run_viewer.run_viewer_cli`, lines 3575-3610), add a helper `_usage_refusal(err_msg: str, term: Term, *, is_agent: bool = False, is_json: bool = False) -> int` modeled on `run_viewer._unresolvable_target_refusal` (`agent_workflows/run_viewer.py`, lines 3392-3421) and route the four usage/flag-conflict/`--since` refusal branches (`if short and summary_only:`, `if latest_only and summary_only:`, `if issues_only and summary_only:`, and `except ValueError as exc:` under `if since_spec:`) through it so `--agent` emits a single-line `aw.agent/v1` `kind: "error"` record via `_agent_schema.render_jsonl_record`, `--json` emits the validated `kind: "error"` record with `json.dumps(..., indent=2, ensure_ascii=False)`, and human mode continues calling `term.line(err_msg)` at exit code 2.
  - Depends on: none
  - Expected outcome: Each of the four refusal paths (`--short -S`, `--latest-only -S`, `--issues -S`, and invalid `--since <spec>`) under `--agent` or `--json` prints a schema-valid `aw.agent/v1` `kind: "error"` record (`cmd: "runs"`, `outcome: "cannot-run"`, `exit: 2`, `verified: False`, `complete: False`, `error: _agent_schema.redact_home_paths(err_msg)`, `next: "aw runs --help"`) validated by `agent_schema.validate_agent_record` and returns `2`.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/run_viewer.py` (`run_viewer.run_viewer_cli`, lines 3762-3972), extract shared filter-dictionary construction and recursive string sanitization helpers (`_build_viewer_filters_dict` and `_sanitize_agent_payload`), normalize `actual_path` and `collisions` paths in `_issue_records` (`agent_workflows/run_viewer.py`, lines 3853-3874) via `_agent_schema.normalize_repo_path(..., repo_root)`, and rewrite the `if is_agent:` block (`agent_workflows/run_viewer.py`, lines 3921-3972) so all four branches (`issues_only`, `latest_only`, `summary_only`, and default per-run) emit validated `aw.agent/v1` `kind: "item"` records (`cmd: "runs"`) followed by a validated terminal `kind: "summary"` record (`cmd: "runs"`, `outcome: "clean"`, `exit: 0`, `total: len(items)`, `emitted: len(items)`, `omitted: 0`, `complete: True`, `verified: True`, `findings: len(issue_records)`, `filters: filters`, optional `excluded_runs: excluded_data`, and `next: "aw runs" if (not items and filters) else None`), removing the non-schema `{"kind": "excluded_runs"}` pseudo-record while leaving `if is_json:` (`agent_workflows/run_viewer.py`, lines 3876-3919) unchanged.
  - Depends on: E-01
  - Expected outcome: Every `--agent` invocation of `aw runs` and `aw runs list` across default, `--latest-only`, `--summary-only`, and `--issues` (both empty and non-empty, with or without `excluded_runs`) emits 0 or more schema-valid `kind: "item"` records followed by exactly 1 schema-valid `kind: "summary"` record on stdout and returns `0`, while `--json` success output remains unchanged.
  - Execution state: pending

### Task group 2: Unit and CLI tests in `tests/test_run_viewer.py`

- [ ] E-03 In `tests/test_run_viewer.py`, update the three existing tests that assert the pre-envelope `--agent` line count or `{"kind": "excluded_runs"}` pseudo-record (`RunViewerTests.test_run_viewer_cli_formats_and_filters` at lines 685-689, `FilterExclusionReportingTests.test_agent_partial_path_remains_line_oriented_jsonl` at lines 2926-2944, and `FilterExclusionReportingTests.test_mode_branches_latest_and_issues` at lines 3005-3021) and add dedicated tests covering: (a) non-empty `--agent` item + summary stream across default, `--latest-only`, `--summary-only`, and `--issues` (populated and empty) for both `aw runs` and `aw runs list`; (b) `excluded_runs` placement on the terminal `kind: "summary"` record across `--agent` branches; (c) all four flag-conflict and `--since` refusals under `--agent` and `--json` (including home-path redaction on an invalid `--since` spec); (d) `agent_schema.validate_agent_record` validation of every emitted JSONL line; and (e) `--json` non-regression across all four modes.
  - Depends on: E-02
  - Expected outcome: All tests in `tests/test_run_viewer.py` and `tests/test_runs_empty_agent_record.py` pass, exercising every non-empty and refusal branch under `--agent`, `--json`, and human modes for both `aw runs` and `aw runs list`.
  - Execution state: pending

### Task group 3: Documentation and changelog sync

- [ ] E-04 In `docs/cli-output-contract.md` (Section 3.1 `Output Mode Matrix`, line 186), update the `aw runs` note to remove the `tracked as backlog 4d3ynu` caveat and state that under `--agent`, `aw runs` / `aw runs list` emits `aw.agent/v1` `kind: "item"` records followed by a terminal `kind: "summary"` record (or a single `kind: "summary"` record when zero items match) and `kind: "error"` (`outcome: "cannot-run"`, `exit: 2`) records on target, flag-conflict, and `--since` refusals, while `--json` preserves the bare `{"runs": [...]}` success payload and emits the pretty-printed `kind: "error"` record on refusals.
  - Depends on: E-02
  - Expected outcome: `docs/cli-output-contract.md` Section 3.1 accurately documents the `aw runs` `--agent` and `--json` output shapes with no reference to open backlog item `4d3ynu` and no em or en dashes.
  - Execution state: pending

- [ ] E-05 In `CHANGELOG.md` (under `## 2.0.0 (pending)`, around line 30), add a `- Fixed:` entry describing that `aw runs --agent` and `aw runs list --agent` now wrap non-empty run, `--latest-only`, `--summary-only`, and `--issues` streams in `aw.agent/v1` `kind: "item"` records followed by a terminal `kind: "summary"` record (carrying any `excluded_runs`) and emit `aw.agent/v1` `kind: "error"` records under `--agent` and `--json` on flag-conflict and invalid `--since` refusals.
  - Depends on: E-02
  - Expected outcome: `CHANGELOG.md` contains the new `- Fixed:` bullet under `## 2.0.0 (pending)` with no em or en dashes.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Predecessor plan `t76qdk` (`.aw/records/plans/executed/20261012-l5dq92-01-t76qdk-aw-runs-empty-state-agent-emits-an-aw-agent-v1-summary-recor.ipd.md`, from backlog `l5dq92`) fixed only the empty-state `if not summaries and not issues_only:` branch in `run_viewer.run_viewer_cli` (`agent_workflows/run_viewer.py`, lines 3755-3806) to emit a validated `aw.agent/v1` `kind: "summary"` record via `_agent_schema.render_jsonl_record` while preserving `{"runs": []}` under `--json`.
- Command inventory (`command_surface.COMMAND_INVENTORY` in `agent_workflows/command_surface.py`, lines 435-445) declares `runs` (`aw runs` and `aw runs list`) with `supports_agent=True`, `supports_json=True`, `agent_record_kind="summary"`, and `exit_contract=(0, 2)`.
- `agent_schema.validate_agent_record` (`agent_workflows/agent_schema.py`, lines 348-516) enforces `RECORD_KINDS = ("result", "summary", "item", "error")`, requires `schema: "aw.agent/v1"`, `kind`, and `cmd` on `item` records (`agent_workflows/agent_schema.py`, lines 494-498), requires `outcome`, `exit`, `total`, `emitted`, `omitted`, `complete`, and `verified` on `summary` records (`agent_workflows/agent_schema.py`, lines 455-492), requires `outcome`, `exit`, `verified`, `complete`, and non-empty `error` on `error` records (`agent_workflows/agent_schema.py`, lines 500-513), and recursively rejects any string value matching `_ANSI_ESCAPE_RE` or `_HOME_PATH_RE` (`agent_workflows/agent_schema.py`, lines 381-394).
- `AgentRenderer.render_item` (`agent_workflows/renderers.py`, lines 302-308) constructs `item` records by merging the envelope keys flat into the item dictionary: `{"schema": SCHEMA_VERSION, "kind": "item", "cmd": cmd, **item_dict}`.
- `run_viewer._unresolvable_target_refusal` (`agent_workflows/run_viewer.py`, lines 3392-3421) is the existing refusal helper in `run_viewer.py`: under `is_agent or is_json`, it constructs a `kind: "error"`, `cmd: "runs"`, `outcome: "cannot-run"`, `exit: 2`, `verified: False`, `complete: False`, `error: _agent_schema.redact_home_paths(message)` record, validates it with `_agent_schema.assert_valid_agent_record(record)`, and prints it with `indent=2 if is_json else None`.
- User-facing prose in `docs/cli-output-contract.md` and `CHANGELOG.md` must contain no em or en dashes (`\u2014` or `\u2013`).

## Findings

| ID | Severity | Location | Finding |
| :--- | :--- | :--- | :--- |
| F-01 | medium | `run_viewer.run_viewer_cli` (`agent_workflows/run_viewer.py`, lines 3575-3610) | Four usage/flag-conflict refusals (`short and summary_only`, `latest_only and summary_only`, `issues_only and summary_only`, and `resolve_since_timestamp` `ValueError`) print `json.dumps({"error": err_msg, "exit_code": 2})` when `is_agent or is_json`. These lack `schema`, `kind`, `cmd`, `outcome`, `exit`, `verified`, `complete`, and `next`, and fail `agent_schema.validate_agent_record`. Furthermore, `parse_since_timestamp` (`agent_workflows/run_viewer.py`, lines 3229-3231) interpolates the raw `spec` into `ValueError(f"invalid date, timestamp, or timespec '{spec}'")`, so an invalid `--since` spec containing a home path is not redacted unless passed through `_agent_schema.redact_home_paths`. |
| F-02 | medium | `run_viewer.run_viewer_cli` (`agent_workflows/run_viewer.py`, lines 3921-3972) | When `summaries` is non-empty (or when `issues_only` is true, even on an empty repo because line 3755 checks `if not summaries and not issues_only:`), the `if is_agent:` block emits raw `asdict(...)` or `build_multi_run_summary_dict(...)` dicts with no `schema`, `kind`, or `cmd` fields, emits no terminating `kind: "summary"` record, and when `issues_only` has 0 issues emits 0 bytes on stdout at exit 0 (violating `docs/cli-output-contract.md` Section 11.1). |
| F-03 | medium | `run_viewer.run_viewer_cli` (`agent_workflows/run_viewer.py`, lines 3937-3944, 3949-3956, 3964-3971) | When `excluded_data` is non-empty on a non-empty `--agent` run, `run_viewer_cli` appends `{"kind": "excluded_runs", "excluded_runs": excluded_data}`. `"excluded_runs"` is not a valid `aw.agent/v1` record `kind` (`RECORD_KINDS = ("result", "summary", "item", "error")`) and lacks `schema` and `cmd`. On the empty-state `--agent` path (`t76qdk`, lines 3797-3798), `excluded_runs` is already carried as an extra field on the `kind: "summary"` record. |
| F-04 | low | `run_viewer.run_viewer_cli` (`_issue_records` in `agent_workflows/run_viewer.py`, lines 3853-3874) | `_issue_records()` converts `rec["actual_path"]` with `str(rec["actual_path"])` instead of `_agent_schema.normalize_repo_path(rec["actual_path"], repo_root)` and leaves `rec["collisions"]` as a `list[Path]` (from `StepArtifactAudit.collisions: List[Path]` in `agent_workflows/artifact_audit.py`, line 59). If `actual_path` is an absolute path under a home directory or `collisions` is non-empty, `json.dumps` / `validate_agent_record` either fails `TypeError: Object of type Path is not JSON serializable` or fails home-path validation. Step fields (`configured_file`, `summary`, `incomplete_requirements`, `refusal`, `tests_run`, `corrections_made`, `corroboration_reason`) can also carry raw home paths in persisted run state unless recursively redacted via `_agent_schema.redact_home_paths` before `render_jsonl_record`. |
| F-05 | low | `tests/test_run_viewer.py` (lines 685-689, 2926-2944, 3005-3021) and `tests/test_runs_subdir_root.py` (lines 75-78) | Three tests in `tests/test_run_viewer.py` assert pre-envelope `--agent` behavior (`len(lines) == 1` or `records[-1]["kind"] == "excluded_runs"`). Meanwhile `tests/test_runs_subdir_root.py` parses `splitlines()[0]` and reads `["run_dir"]`, which continues to work unchanged when `splitlines()[0]` is a flat `kind: "item"` record (`{"schema": "aw.agent/v1", "kind": "item", "cmd": "runs", **s_dict}`). Zero existing tests exercise the four flag-conflict / `--since` refusals under `--agent` or `--json`. |

## Proposed changes (ordered, validatable)

1. **Unify usage/flag-conflict/`--since` refusals onto `aw.agent/v1` `kind: "error"` records (`E-01`)**:
   - In `agent_workflows/run_viewer.py`, define a module-private helper `_usage_refusal(err_msg: str, term: Term, *, is_agent: bool = False, is_json: bool = False) -> int` next to `_unresolvable_target_refusal` (`agent_workflows/run_viewer.py`, lines 3392-3421):
     ```python
     def _usage_refusal(
         err_msg: str,
         term: Term,
         *,
         is_agent: bool = False,
         is_json: bool = False,
     ) -> int:
         if is_agent or is_json:
             record: dict[str, Any] = {
                 "schema": _agent_schema.SCHEMA_VERSION,
                 "kind": "error",
                 "cmd": "runs",
                 "outcome": "cannot-run",
                 "exit": 2,
                 "verified": False,
                 "complete": False,
                 "error": _agent_schema.redact_home_paths(err_msg),
                 "next": "aw runs --help",
             }
             if is_agent:
                 print(_agent_schema.render_jsonl_record(record), end="")
             else:
                 _agent_schema.assert_valid_agent_record(record)
                 print(json.dumps(record, indent=2, ensure_ascii=False))
             return 2
         term.line(err_msg)
         return 2
     ```
   - In `run_viewer.run_viewer_cli` (`agent_workflows/run_viewer.py`, lines 3575-3610), replace the four inline `if is_agent or is_json: print(json.dumps({"error": err_msg, "exit_code": 2}))` blocks (`short and summary_only`, `latest_only and summary_only`, `issues_only and summary_only`, and `since_spec` `ValueError`) with `return _usage_refusal(err_msg, term, is_agent=is_agent, is_json=is_json)`.

2. **Wrap `--agent` streams in `kind: "item"` + terminal `kind: "summary"` records (`E-02`)**:
   - In `agent_workflows/run_viewer.py`, add a helper `_sanitize_agent_value(val: Any) -> Any` that recursively applies `_agent_schema.redact_home_paths` (and strips any ANSI escape sequences if present) to strings inside dicts/lists/tuples so that user-authored or runner-persisted step strings (`summary`, `refusal`, `incomplete_requirements`, `corrections_made`, etc.) cannot trip `validate_agent_record`.
   - In `_issue_records()` (`agent_workflows/run_viewer.py`, lines 3853-3874), normalize `rec["actual_path"]` with `_agent_schema.normalize_repo_path(rec["actual_path"], repo_root)` when truthy, and normalize `rec["collisions"]` with `[_agent_schema.normalize_repo_path(p, repo_root) for p in rec.get("collisions") or []]` so `Path` instances are always repo-relative strings on both `--json` and `--agent`.
   - Extract `_build_viewer_filters_dict(...) -> dict[str, Any]` inside `run_viewer_cli` (reused by both the empty-state `if not summaries and not issues_only:` branch at lines 3763-3781 and the non-empty `if is_agent:` block at lines 3921-3972) recording active filters (`set`, `ipd`, `status`, `failed`, `active`, `last`, `since`, `targets`, plus mode flags `issues`, `latest_only`, `summary_only` when set on the `--agent` stream). Wait: let's check whether `t76qdk` tests in `tests/test_runs_empty_agent_record.py` assert exact keys in `filters` on the empty-state path!
     - In `tests/test_runs_empty_agent_record.py`: `test_empty_repo_runs_agent_emits_valid_summary_record` asserts `rec["filters"] == {}` when no filters are passed, and `test_filter_exhaustion_runs_agent_emits_valid_summary_record_with_filters_and_exclusions` passes `--set`, `--status`, `--failed`, `--last`, `--since`, and target `probe`. None of those pass `--issues`, `--latest-only`, or `--summary-only`, so keeping `_build_viewer_filters_dict` with the exact keys from lines 3763-3781 (`set`, `ipd`, `status`, `failed`, `active`, `last`, `since`, `targets`) preserves 100% compatibility with `t76qdk`!
   - In `if is_agent:` (`agent_workflows/run_viewer.py`, lines 3921-3972):
     - Compute `disc = _issue_records()`.
     - Build `raw_items: list[dict[str, Any]]` according to the active mode:
       - If `issues_only`: `raw_items = disc`
       - Else if `latest_only`: deduplicate `latest_steps_dict` (same as lines 3930-3935) and set `raw_items = [asdict(st) for _, st in latest_steps_dict.values()]`
       - Else if `summary_only`: `raw_items = [build_multi_run_summary_dict(summaries)]`
       - Else (default per-run view): for each `s` in `summaries`, build `s_dict = asdict(s)` with `s_dict["run_dir"] = _agent_schema.normalize_repo_path(s_dict["run_dir"], repo_root)` and append to `raw_items`.
     - For each `item_payload` in `raw_items`, build:
       ```python
       item_record: dict[str, Any] = {
           "schema": _agent_schema.SCHEMA_VERSION,
           "kind": "item",
           "cmd": "runs",
           **_sanitize_agent_value(item_payload),
       }
       print(_agent_schema.render_jsonl_record(item_record), end="")
       ```
     - Emit the terminal `kind: "summary"` record:
       ```python
       summary_record: dict[str, Any] = {
           "schema": _agent_schema.SCHEMA_VERSION,
           "kind": "summary",
           "cmd": "runs",
           "outcome": "clean",
           "exit": 0,
           "total": len(raw_items),
           "emitted": len(raw_items),
           "omitted": 0,
           "complete": True,
           "verified": True,
           "findings": len(disc),
           "filters": filters,
       }
       if excluded_data:
           summary_record["excluded_runs"] = _sanitize_agent_value(excluded_data)
       summary_record["next"] = "aw runs" if (not raw_items and filters) else None
       print(_agent_schema.render_jsonl_record(summary_record), end="")
       return 0
       ```

3. **Update existing `--agent` tests and add full conformance coverage in `tests/test_run_viewer.py` (`E-03`)**:
   - Update `RunViewerTests.test_run_viewer_cli_formats_and_filters` (`tests/test_run_viewer.py`, lines 685-689) to assert `len(lines) == 2`, validate both lines with `agent_schema.validate_agent_record`, assert `lines[0]` is `kind == "item"` with `run_id == "run-20260827T212958Z-2367239"`, and assert `lines[1]` is `kind == "summary"` with `total == 1`, `emitted == 1`, `omitted == 0`, `outcome == "clean"`, `exit == 0`.
   - Update `FilterExclusionReportingTests.test_agent_partial_path_remains_line_oriented_jsonl` (`tests/test_run_viewer.py`, lines 2926-2944) and `FilterExclusionReportingTests.test_mode_branches_latest_and_issues` (`tests/test_run_viewer.py`, lines 3005-3021) to validate every line via `agent_schema.validate_agent_record`, assert leading records have `kind == "item"`, and assert the final record has `kind == "summary"` carrying `excluded_runs` (and that no record has `kind == "excluded_runs"`).
   - Add test methods in `tests/test_run_viewer.py` testing:
     - `aw runs --agent` and `aw runs list --agent` non-empty stream across default, `--latest-only`, `--summary-only`, and `--issues` (both when issues exist and when 0 issues exist, plus on an empty repo with `--issues --agent`);
     - all four refusal paths (`--short --summary-only`, `--latest-only --summary-only`, `--issues --summary-only`, and `--since invalid` including a `str(Path.home() / "bad-spec")` home path) under `--agent` and `--json`, asserting `exit == 2`, `kind == "error"`, `outcome == "cannot-run"`, `cmd == "runs"`, `verified is False`, `complete is False`, `next == "aw runs --help"`, and `validate_agent_record(...) == []`;
     - `--json` non-regression across default, `--latest-only`, `--summary-only`, and `--issues`.

4. **Sync `docs/cli-output-contract.md` and `CHANGELOG.md` (`E-04`, `E-05`)**:
   - Update `docs/cli-output-contract.md` line 186 and `CHANGELOG.md` under `## 2.0.0 (pending)`.

## Deferred / out of scope (with reason)

none

## Scope check

- Over-scope: none.
- Under-scope: none. Every non-empty and refusal `--agent` path in `run_viewer.run_viewer_cli` (and the four usage/flag-conflict/`--since` refusal paths under `--json`) identified in backlog item `4d3ynu` is covered.

## Required tests / validation

- Targeted unit and CLI test runs:
  - `python3 -m pytest tests/test_run_viewer.py tests/test_runs_empty_agent_record.py tests/test_runs_subdir_root.py tests/test_runs_flag_position_parity.py tests/test_runs_repo_alias.py tests/test_family_root_agent_conformance.py tests/test_agent_surface_conformance.py`
- Leak-sanitizer and prose checks:
  - `aw sanitize --agent`
- Full test suite:
  - `python3 -m pytest`

## Spec / documentation sync

- `docs/cli-output-contract.md`: update Section 3.1 (`Output Mode Matrix`, line 186) to remove the `tracked as backlog 4d3ynu` caveat and document the `aw.agent/v1` `item` + `summary` stream and `error` refusal records on `aw runs`.
- `CHANGELOG.md`: add a `- Fixed:` entry under `## 2.0.0 (pending)`.

## Open questions

### OQ-01: How should non-empty `--agent` modes (`default`, `--latest-only`, `--summary-only`, `--issues`) and `excluded_runs` be represented in `aw.agent/v1` JSONL?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Emit 0 or more flat `aw.agent/v1` `kind: "item"` records (`{"schema": "aw.agent/v1", "kind": "item", "cmd": "runs", ...}`, matching `AgentRenderer.render_item` in `agent_workflows/renderers.py`, lines 302-308) followed by a single terminal `kind: "summary"` record (`cmd: "runs"`, `outcome: "clean"`, `exit: 0`, `total: len(items)`, `emitted: len(items)`, `omitted: 0`, `complete: True`, `verified: True`, `findings: len(issue_records)`, `filters: filters`, `next: "aw runs" if (not items and filters) else None`). Carry `excluded_runs` on the terminal `kind: "summary"` record when non-empty (matching the empty-state `summary` record from `t76qdk` at `agent_workflows/run_viewer.py`, lines 3797-3798) instead of emitting the non-schema `{"kind": "excluded_runs"}` pseudo-record. This satisfies `command_surface.COMMAND_INVENTORY` (`agent_record_kind="summary"`) and `docs/cli-output-contract.md` Section 11.1 while preserving top-level item keys (`run_id`, `run_dir`, `steps`, etc.) on each `item` record.

### OQ-02: Should the four flag-conflict and `--since` refusals emit `aw.agent/v1` `kind: "error"` records on both `--agent` and `--json`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Yes. Sibling `_unresolvable_target_refusal` in the same module (`agent_workflows/run_viewer.py`, lines 3401-3418) already emits a validated `aw.agent/v1` `kind: "error"` record (`outcome: "cannot-run"`, `exit: 2`) on both `is_agent` and `is_json` (compact single-line JSONL on `--agent`, `indent=2` on `--json`). Routing the four usage/flag-conflict/`--since` refusals through `_usage_refusal` makes all refusal paths in `run_viewer_cli` consistent across `--agent` and `--json`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Run a one-liner invoking `run_viewer.run_viewer_cli` (loaded by `E-01`) across all four refusal branches (`--short -S`, `--latest-only -S`, `--issues -S`, and `--since` with `str(Path.home() / "not-a-date")`) under both `--agent` and `--json`, validating each parsed output with `agent_schema.validate_agent_record` and asserting `exit == 2`, `kind == "error"`, `outcome == "cannot-run"`, `cmd == "runs"`, and `<home>` redacted in output; paste the command and its `OK` output.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Run a one-liner invoking `cli.main` (loaded by `E-02`) for `aw runs` and `aw runs list` with `--agent` on a temporary fixture across default, `--latest-only`, `--summary-only`, and `--issues` (empty and non-empty, with and without `excluded_runs`), verifying every stdout line passes `agent_schema.validate_agent_record`, leading lines have `kind == "item"`, the final line has `kind == "summary"`, and `--json` still returns the bare dict shape; paste the command and its `OK` output.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Run `python3 -m pytest tests/test_run_viewer.py tests/test_runs_empty_agent_record.py tests/test_runs_subdir_root.py tests/test_runs_flag_position_parity.py tests/test_runs_repo_alias.py tests/test_family_root_agent_conformance.py tests/test_agent_surface_conformance.py` and `python3 -m pytest`, and paste the actual runner output showing 0 failures.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Inspect `git diff -- docs/cli-output-contract.md` and run a Python check confirming `4d3ynu` is no longer mentioned as an open caveat and zero `\u2013` / `\u2014` characters appear in the modified lines; paste the output.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Inspect `git diff -- CHANGELOG.md` and run a Python check confirming the new `- Fixed:` bullet is present under `## 2.0.0 (pending)` with zero `\u2013` / `\u2014` characters and `aw sanitize --agent` reports `"outcome":"clean"`; paste the output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored at `- Status: to-review` to graduate backlog item `4d3ynu`. Do not execute until reviewed and approved (`- Status: approved`). On execution completion, finalize via `aw ipd finalize 3jg79f` so the plan transitions to `.aw/records/plans/executed/`.
