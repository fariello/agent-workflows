# IPD: Surface discarded agent user-config changes per run in aw runs

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `c4q9e8`: plan `9y27t2` (backlog `btw02e`) discards an agent turn's writes to the operator's user configuration and appends an `agent-user-config-discarded` event for each added, removed, or modified file to `<run_dir>/events.jsonl`, printing a turn-end warning and an end-of-run summary via `runner_shared.report_discarded_user_config`. However, `aw runs` (`agent_workflows/run_viewer.py`) never reads those events from `<run_dir>/events.jsonl`, so an operator inspecting a completed or historical run later in human or `--json` (or `--agent`) mode cannot see that an agent turn tried to modify their user configuration, how many changes were discarded, or which top-level config keys were targeted.
- Scope: IN: extract a shared reader, key-list extractor, and human summary line formatter in `agent_workflows/runner_shared.py` (`AGENT_USER_CONFIG_DISCARDED_EVENT`, `read_discarded_user_config_events`, `discarded_user_config_keys`, `format_discarded_user_config_line`) used by both `runner_shared.report_discarded_user_config` and `agent_workflows/run_viewer.py`; extend `run_viewer.StepSummary` and `run_viewer.RunSummary` with `discarded_user_config_count`, `discarded_user_config_keys`, and `discarded_user_config`; populate them in `run_viewer.load_run_summary` (both `state.json` and `execution-report.md` fallback paths); render the per-run summary line in `run_viewer.format_run_human`, per-step detail lines in `run_viewer.render_step_details`, and multi-run aggregates in `run_viewer.build_multi_run_summary_dict` and `run_viewer.format_multi_run_summary`; behavioral tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py`; and `CHANGELOG.md`. OUT: changing how user-config writes are sandboxed or reconciled during a turn (already shipped in `9y27t2`); `AW_HOME` containment (backlog `s4pys7`); `project_context` XDG config resolution (backlog `m9dobx`); flagging a discarded user-config write as a step artifact/refusal issue in `step_has_issue` (the write was contained and discarded by the runner, so the artifact and run completion remain valid; see OQ-02).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_viewer.py, tests/test_agent_user_config_containment.py, tests/test_run_viewer.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: c4q9e8
- Set: c4q9e8
- Order: 1
- Highest E allocated: 06
- Author: Antigravity
- Id: swpf3q
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008

- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008
- 2026-10-14 to-review (Antigravity): authored from backlog `c4q9e8` to surface the count and keys of discarded agent user-config changes per run in `aw runs` (human, `--json`, and `--agent`).
- 2026-10-14 draft (Antigravity): created.

## Goal

When an operator inspects runs with `aw runs` (in human, `--json`, or `--agent` mode), each run (and step) surfaces the count, deduplicated top-level keys, and durable event records of any agent user-config changes that were discarded during the run, read through one shared `events.jsonl` reader used by both the end-of-run report and the run viewer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and shared `events.jsonl` reader in `agent_workflows/runner_shared.py`

- [x] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` BEFORE the first edit and record its summary line and any failing node ids. The post-change bar is that no node id fails that did not fail here.
  - Depends on: none
  - Expected outcome: a recorded baseline summary line and failing-node-id list.
  - Execution state: performed

- [x] E-02 In `agent_workflows/runner_shared.py` (user-config containment section around `runner_shared.reconcile_agent_user_config` at line 47214 and `runner_shared.report_discarded_user_config` at line 47333), define `AGENT_USER_CONFIG_DISCARDED_EVENT = "agent-user-config-discarded"` and extract three shared helpers:
  1. `read_discarded_user_config_events(run_dir: Any, *, raise_on_error: bool = False) -> list[dict[str, Any]]`: resolves `run_dir_path` (`Path(run_dir.get("run_dir") or run_dir.get("repo") or ".")` when `isinstance(run_dir, Mapping)` else `Path(run_dir)`), opens `<run_dir_path>/events.jsonl` when `is_file()` (with `errors="replace"`, as `run_viewer.load_run_summary` already does for this file), and returns each JSON object line where `data.get("event") == AGENT_USER_CONFIG_DISCARDED_EVENT` (normalizing `keys` to `[str(k) for k in data["keys"]]` when `isinstance(data.get("keys"), list)`). A line that does not contain the substring `AGENT_USER_CONFIG_DISCARDED_EVENT` is skipped BEFORE `json.loads` (cheap prefilter: `aw runs` now reads every listed run's `events.jsonl`, which grows with heartbeat and lifecycle events; measured at review on a 200k-line, ~12 MB file, a full `json.loads` scan took 0.45s versus 0.035s with the substring prefilter, F-05). Skips blank or malformed JSON lines. Error contract: with `raise_on_error=False` (default, for read-only viewer callers) it catches `OSError` and returns `[]`; with `raise_on_error=True` it lets `OSError` propagate so `report_discarded_user_config` keeps its existing `error: failed to summarize discarded user-config changes: <exc>` line (its existing `except Exception` stays, so the report still never raises).
  2. `discarded_user_config_keys(events: Sequence[Mapping[str, Any]]) -> list[str]`: returns the deduplicated list of top-level key strings across `events` in order of first appearance (`list(dict.fromkeys(str(k) for ev in events if isinstance(ev, Mapping) and isinstance(ev.get("keys"), list) for k in ev["keys"]))`).
  3. `format_discarded_user_config_line(events: Sequence[Mapping[str, Any]]) -> str | None`: returns `None` when `events` is empty, and otherwise returns `"Agent user-config changes discarded: <count> (<id6>: <file> <keys>; ...)"` with the exact formatting `runner_shared.report_discarded_user_config` already emits (measured at review for a two-event run: `Agent user-config changes discarded: 2 (9y27t2: config.json ['color_depth']; 9y27t2: notes.txt)`; `keys` renders as the Python list repr and an event without keys renders `<id6>: <file>` with no change word).
  Update `runner_shared.reconcile_agent_user_config` to reference `AGENT_USER_CONFIG_DISCARDED_EVENT` and refactor `runner_shared.report_discarded_user_config` to call `read_discarded_user_config_events(run_dir, raise_on_error=True)` and `format_discarded_user_config_line(events)`.
  - Depends on: E-01
  - Expected outcome: one shared constant, reader, key extractor, and formatter in `agent_workflows/runner_shared.py`; `runner_shared.report_discarded_user_config` produces byte-identical output for both populated and clean run directories (the existing `tests/test_agent_user_config_containment.py` `test_report_discarded_user_config_output` still passes unmodified) while sharing the reader with `run_viewer`.
  - Execution state: performed

### Task group 2: surface per-run and per-step discarded user-config changes in `agent_workflows/run_viewer.py`

- [x] E-03 In `agent_workflows/run_viewer.py`:
  1. Import `discarded_user_config_keys`, `format_discarded_user_config_line`, and `read_discarded_user_config_events` from `agent_workflows.runner_shared` (at `from agent_workflows.runner_shared import`, lines 41-51).
  2. Add three defaulted fields to `run_viewer.StepSummary` (around line 215) and `run_viewer.RunSummary` (around line 244):
     - `discarded_user_config_count: int = 0`
     - `discarded_user_config_keys: list[str] = field(default_factory=list)`
     - `discarded_user_config: list[dict[str, Any]] = field(default_factory=list)`
  3. In `run_viewer.load_run_summary` (lines 944-1378), read `discarded_events = read_discarded_user_config_events(run_dir)` once, index events by `str(ev.get("id6") or "").strip()`, populate the three fields on each `StepSummary` in both the `state.json` loop (lines 1173-1215) and the `execution-report.md` fallback loop (lines 1295-1314), and populate `discarded_user_config_count=len(discarded_events)`, `discarded_user_config_keys=discarded_user_config_keys(discarded_events)`, and `discarded_user_config=discarded_events` on the returned `RunSummary` (lines 1357-1378).
     Indexing rule: events are keyed by `id6`, and a step receives every event whose `id6` equals the step's `id6` (an `id6` normally occupies one queue position; if the same `id6` appears at more than one position, each such step receives the same events, which is stated in a code comment rather than silently guessed). An event whose `id6` matches no step is still counted on the `RunSummary` (it is never dropped). Set each step's `discarded_user_config_count` to `len` of its event list.
  4. In `run_viewer.format_run_human` (right after the cost/tokens block, before `if run.steps:`), when `run.discarded_user_config` is non-empty, append `"  " + format_discarded_user_config_line(run.discarded_user_config)`, styled with `term.color256(..., 214)` when `getattr(term, "color", False)` is True. Emit nothing when the list is empty. The line is emitted in both default and `short=True` modes. No synthetic count-only fallback: the count is always `len(discarded_user_config)`, so there is one source of truth for the human line.
  5. In `run_viewer.render_step_details` (around line 2460, before `if details:`), for each event `ev` in `step.discarded_user_config`, append `"  ! user-config discarded: <file> <keys>"` (or `"  ! user-config discarded: <file> (<change>)"` when `keys` is absent/empty, or `"  ! user-config discarded: <file>"` when neither is present), styled with `term.color256(..., 214)` when color is enabled.
  - Depends on: E-02
  - Expected outcome: `aw runs` single-run human output (default, `--short`, `--detail`) and `aw runs --json` / `--agent` per-run records (and `--latest-only` step records) surface the count, keys, and event records of discarded user-config changes per run and per step when present, while clean runs with zero events have byte-identical human output and `0` / `[]` fields in JSON.
  - Execution state: performed

- [x] E-06 In `run_viewer.build_multi_run_summary_dict` and `run_viewer.format_multi_run_summary`, aggregate `discarded_user_config_count` (sum across `summaries`), `discarded_user_config_runs` (number of runs with a non-zero count), and `discarded_user_config_keys` (deduplicated keys in order of appearance across `summaries`) into the returned summary dict (keys always present, `0` / `[]` when none), and when `discarded_user_config_count > 0` append `"Agent user-config changes discarded: <count> across <runs> run(s) (<keys>)"` (styled with color `214` when color is enabled) in `format_multi_run_summary` immediately after the header title line, OUTSIDE the `if has_any_cost:` block (the `Total Cost:` / `Total Tokens:` lines are emitted only when some step has cost, so anchoring the new line there would hide it on runs without usage data, F-06).
  - Depends on: E-03
  - Expected outcome: `aw runs --summary-only` (human and `--json` / `--agent`) and the multi-run summary appended after several runs report the aggregate count, run count, and keys, including when no step carries cost data; with no events anywhere the human summary is unchanged and the dict carries `0` / `0` / `[]`.
  - Execution state: performed

### Task group 3: behavioral tests and changelog

- [x] E-04 Add behavioral tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py`:
  1. In `tests/test_agent_user_config_containment.py`, add `test_read_and_format_discarded_user_config_helpers` testing `runner_shared.read_discarded_user_config_events`, `runner_shared.discarded_user_config_keys`, and `runner_shared.format_discarded_user_config_line` across: (i) multiple events across turns/files with overlapping and non-overlapping `keys` plus an `added` non-JSON file without `keys`; (ii) blank and malformed lines in `events.jsonl` ignored without raising; (iii) missing `events.jsonl` returning `[]` and `None`; and (iv) end-to-end integration where `reconcile_agent_user_config` writes to `events.jsonl` and `run_viewer.load_run_summary` + `run_viewer.format_run_human` + `cli.main(["runs", "--dir", ..., "--json", ...])` surface the exact count (`1`) and keys (`["color_depth"]`).
  2. In `tests/test_run_viewer.py`, add the new tests inside a new `unittest.TestCase` subclass (the module's existing tests are `TestCase` classes, e.g. `RunViewerTests`, and the suite also runs under `python -m unittest discover`), building fixtures with the module's own `_build_viewer_fixture`/`_run_viewer` helpers or the same `state.json` shape under a temp `.aw/records/runs/run-<ts>-<pid>/`, testing `run_viewer.load_run_summary`, `run_viewer.format_run_human` (default, `--short`, `--detail`, colored and uncolored), `run_viewer.build_multi_run_summary_dict`, `run_viewer.format_multi_run_summary`, ` execution-report.md` fallback loading with `events.jsonl`, and `run_viewer.run_viewer_cli` (`--json`, `--summary-only --json`, `--latest-only --json`, `--agent`, and human) across a run with discarded user-config events and a clean run without them. Also cover: an event whose `id6` matches no step is still counted on the run; a multi-run summary with no cost data still prints the aggregate line (E-06); and the clean run's human output equals its output with the feature's fields at defaults (no extra line).
  3. Mutation proofs (temporary, reverted, confirmed by `git diff`): (a) make `load_run_summary` skip the `read_discarded_user_config_events` call and confirm the run-viewer tests fail; (b) in `read_discarded_user_config_events`, drop the `data.get("event") == AGENT_USER_CONFIG_DISCARDED_EVENT` comparison (keep the substring prefilter) and confirm the helper test fails on a fixture line that mentions the event name in another field (for example `{"event": "heartbeat", "note": "agent-user-config-discarded"}`), which the prefilter alone admits; the fixture must include such a line so the exact-match check is pinned.
  - Depends on: E-03, E-06
  - Expected outcome: all new and existing tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py` pass, and the new tests fail if the `E-03` wiring in `run_viewer.py` is reverted.
  - Execution state: performed

- [x] E-05 In `CHANGELOG.md`, add one `- Added:` bullet at the top of the `## 2.0.0 (pending)` entry list (around line 27) stating that `aw runs` now surfaces the count, keys, and event details of discarded agent user-config changes per run in human, `--json`, and `--agent` output from the run's durable `events.jsonl` log. Write no em or en dashes (user-facing prose rule).
  - Depends on: E-03, E-06
  - Expected outcome: one new `- Added:` bullet in `CHANGELOG.md` with no em or en dashes and `aw sanitize --agent` clean.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Shared reader rule (GUIDING_PRINCIPLES P8; `agent_workflows/run_viewer.py` comments at `REFUSAL_KEY` lines 34-40 and `_projected_step_status` lines 133-135): `run_viewer` never re-derives a storage key or event parser that `runner_shared` owns; both the runner's end-of-run report and `aw runs` call one shared reader in `runner_shared`.
- `reconcile_agent_user_config` (`agent_workflows/runner_shared.py`, lines 47214-47331) writes `{at, event: "agent-user-config-discarded", id6, attempt, file, change, keys?}` records to `<run_dir>/events.jsonl`, where `file` is sandbox-relative and `keys` lists changed top-level JSON keys (values are never recorded, keeping `events.jsonl` leak-safe).
- `report_discarded_user_config` (`agent_workflows/runner_shared.py`, lines 47333-47388) prints `Agent user-config changes discarded: <n> (<id6>: <file> <keys>; ...)` at run end when events exist and prints nothing when there are none ("silence means none").
- `run_viewer.run_viewer_cli` (`agent_workflows/run_viewer.py`, lines 3876-3972) builds `--json` and `--agent` payloads directly from `dataclasses.asdict(s)` on `RunSummary`, `dataclasses.asdict(st)` on `StepSummary`, and `build_multi_run_summary_dict(summaries)`, so defaulted dataclass fields added to `RunSummary` and `StepSummary` are automatically emitted in machine output without breaking existing positional/keyword `RunSummary(...)` or `StepSummary(...)` call sites in tests.
- Non-lifecycle warning lines in `run_viewer` (`render_step_details` at line 2381, `format_refusal_summary` at line 2138) use 256-color index `214` (amber), which is explicitly exempted from lifecycle stage remapping by `agent_workflows/run_viewer.py` lines 1596-1601 (spec `uonrjg` R10.3).
- Behavioral tests only (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE", GUIDING_PRINCIPLES P16). Run the test suite bare (`python3 -m pytest`).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| ID | Finding | Evidence |
| --- | --- | --- |
| F-01 | `reconcile_agent_user_config` already persists leak-safe `agent-user-config-discarded` events in `<run_dir>/events.jsonl`. | `runner_shared.reconcile_agent_user_config` (`agent_workflows/runner_shared.py`, lines 47255-47313) appends `{at, event: "agent-user-config-discarded", id6, attempt, file, change, keys}` to `run_dir_path / "events.jsonl"`. |
| F-02 | `report_discarded_user_config` parses `events.jsonl` inline rather than through a reusable reader. | `runner_shared.report_discarded_user_config` (`agent_workflows/runner_shared.py`, lines 47351-47382) opens `events.jsonl`, filters for `data.get("event") == "agent-user-config-discarded"`, and formats `Agent user-config changes discarded: {count} ({details_str})` inline. |
| F-03 | `run_viewer.load_run_summary` only reads `events.jsonl` as a last-resort fallback for `run_starting_head` and ignores `agent-user-config-discarded` events. | `run_viewer.load_run_summary` (`agent_workflows/run_viewer.py`, lines 1018-1040) opens `events.jsonl` only when `run_starting_head` is missing and stops at the first commit sha key; `RunSummary` (`agent_workflows/run_viewer.py`, lines 224-245) and `StepSummary` (`agent_workflows/run_viewer.py`, lines 169-221) have no fields for discarded user-config changes. |
| F-05 | Reading `events.jsonl` in `load_run_summary` adds a per-run file scan to every `aw runs` invocation (the viewer loads every listed run through `load_run_summary`, `run_viewer.run_viewer_cli` loop `summary = load_run_summary(r_dir, repo_root)`). Today `events.jsonl` is read only on the rare `run_starting_head` fallback. | Review measurement at `461fdf679`: a 200k-line (~12 MB) `events.jsonl` of heartbeat-shaped records scanned with `json.loads` per line (the current `report_discarded_user_config` loop) took 0.45s; a substring prefilter before `json.loads` took 0.035s. E-02 mandates the prefilter. |
| F-06 | `format_multi_run_summary` prints `Total Cost:` / `Total Tokens:` only inside `if has_any_cost:`, so a line anchored "after the Total Cost/Total Tokens lines" disappears when no step has usage data. | `run_viewer.format_multi_run_summary` (`if has_any_cost:` before `f"Total Cost:   {cost_val_str}"`). |
| F-07 | The per-turn sandbox key includes a suffix (`<NN>-<id6>-attempt-<N>[-<suffix>]`, `runner_shared.prepare_agent_user_config`), but the event record carries only `id6` and `attempt`, so a verify turn's discard and an execute turn's discard for the same item and attempt are indistinguishable in `events.jsonl`. Per-step attribution by `id6` is therefore the finest grain available; this plan does not add a field to the event (out of scope, the writer is shipped `9y27t2`). | `runner_shared.prepare_agent_user_config` `turn_key = f"{pos:02d}-{id6}-attempt-{attempt_no}{tag}"`; `reconcile_agent_user_config` record keys. |
| F-04 | `format_run_human` header order is pinned for lines 0..2 by `tests/test_run_viewer.py`. | `RunViewerTests.test_runtime_and_pid_inspection` (`tests/test_run_viewer.py`, lines 1003-1045) asserts `lines[0]` (run_id), `lines[1]` (pid), and `lines[2]` (start/end/duration) on a clean `RunSummary`. Emitting the discarded user-config line after the cost/tokens line and ONLY when `discarded_user_config_count > 0` preserves every existing clean-run line index while surfacing the warning in the run header when events exist. |

## Proposed changes (ordered, validatable)

1. Extract `AGENT_USER_CONFIG_DISCARDED_EVENT`, `read_discarded_user_config_events`, `discarded_user_config_keys`, and `format_discarded_user_config_line` in `agent_workflows/runner_shared.py` and route `report_discarded_user_config` through them (E-02).
2. Extend `StepSummary` and `RunSummary`, populate them from `read_discarded_user_config_events(run_dir)` in `load_run_summary`, and render them in `format_run_human`, `render_step_details`, `build_multi_run_summary_dict`, and `format_multi_run_summary` in `agent_workflows/run_viewer.py` (E-03).
3. Add behavioral tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py` (E-04) and update `CHANGELOG.md` (E-05).

## Deferred / out of scope (with reason)

- `AW_HOME` containment during agent turns: tracked separately in open backlog item `s4pys7`.
  - Carrier: s4pys7
- `project_context` hard-coded `~/.config/agent-workflows` path ignoring `XDG_CONFIG_HOME` and `AW_CONFIG_DIR`: tracked separately in open backlog item `m9dobx`.
  - Carrier: m9dobx
- Treating a discarded user-config write as a step issue in `run_viewer.step_has_issue`: declined because the write was contained and discarded by the runner before touching operator state, so the artifact's on-disk state and the step's execution outcome are unaffected (see OQ-02).
  - Carrier-Declined: deliberate non-goal; contained and discarded writes do not invalidate the artifact or step outcome

## Scope check

- Over-scope: none. Every path in `- Scope-Paths:` is modified by an E-item: `agent_workflows/runner_shared.py` (E-02), `agent_workflows/run_viewer.py` (E-03), `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py` (E-04), `CHANGELOG.md` (E-05).
- Under-scope: none. Both human (`format_run_human`, `render_step_details`, `format_multi_run_summary`) and `--json` / `--agent` (`RunSummary`, `StepSummary`, `build_multi_run_summary_dict`) surfaces of `aw runs` are covered. Distinguishing execute-turn from verify-turn discards would need a new event field (F-07); it is not required by backlog `c4q9e8` (count and keys per run) and is not added.

## Required tests / validation

- Targeted behavioral tests: `python3 -m pytest -o addopts="" tests/test_agent_user_config_containment.py tests/test_run_viewer.py tests/test_runs_subdir_root.py` (the last also drives `build_multi_run_summary_dict`).
- Mutation proofs (a) and (b) from E-04, each reverted and confirmed with `git diff`.
- Full bare test suite: `python3 -m pytest` compared against the E-01 baseline
- Leak sanitizer: `aw sanitize --agent`

## Spec / documentation sync

- No spec amendment required: no specification in `.aw/records/specs/` defines the field list of `RunSummary` or `StepSummary` in `run_viewer.py`.
- `CHANGELOG.md` updated under `## 2.0.0 (pending)` (E-05).

## Open questions

### OQ-01: What field names and human format should `aw runs` use for discarded user-config changes?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from the backlog item's ask ("Surface the count and keys of discarded user-config changes per run in `aw runs` (human and `--json`), reading the same durable events") and plan `9y27t2` E-05: on `RunSummary` (and `StepSummary`), expose `discarded_user_config_count: int`, `discarded_user_config_keys: list[str]`, and `discarded_user_config: list[dict[str, Any]]` so `--json` and `--agent` consumers have the explicit count, the deduplicated top-level key list, and the per-event records (`id6`, `file`, `change`, `attempt`, `keys`). In human mode, `format_run_human` renders `  Agent user-config changes discarded: <n> (<id6>: <file> <keys>; ...)` via the shared `format_discarded_user_config_line` helper when count > 0 and omits the line when count == 0, matching `report_discarded_user_config` word-for-word.

### OQ-02: Should a discarded user-config write flip the step's `Issue` column to `YES` in `aw runs`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED to NO. `run_viewer.step_issue_reasons` (`agent_workflows/run_viewer.py`, lines 563-601) flags two classes that require operator remediation: an artifact location/status discrepancy or a runner refusal/abandonment where the step's work did not land cleanly. A discarded user-config change was already neutralized automatically by `reconcile_agent_user_config` (`9y27t2`), so no operator remediation is needed and flagging `Issue: YES` would cause `aw runs --issues` to report healthy completed steps as broken. Surfacing the line in the run header, in `--detail` step lines, in `--summary-only`, and in `--json`/`--agent` fields gives full visibility without false-positive issue flags.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: the pasted pre-change `python3 -m pytest` summary line and the list of any failing node ids.
  - Observed evidence:
```
707 passed in 22.01s
Failing node ids: none
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: pasted output of a Python one-liner driving `runner_shared.read_discarded_user_config_events`, `runner_shared.discarded_user_config_keys`, `runner_shared.format_discarded_user_config_line`, and `runner_shared.report_discarded_user_config` on a temp run dir with two `agent-user-config-discarded` events in `events.jsonl` and on an empty run dir, plus `git diff -- agent_workflows/runner_shared.py`.
  - Observed evidence:
```
RUN1 events: 2
RUN1 keys: ['color_depth']
RUN1 line: Agent user-config changes discarded: 2 (9y27t2: config.json ['color_depth']; 9y27t2: notes.txt)
RUN1 report: "Agent user-config changes discarded: 2 (9y27t2: config.json ['color_depth']; 9y27t2: notes.txt)\n"
RUN2 events: 0
RUN2 keys: []
RUN2 line: None
RUN2 report: ''
```
Diff:
```diff
diff --git a/agent_workflows/runner_shared.py b/agent_workflows/runner_shared.py
index b08c8d366..8cf344dbd 100644
--- a/agent_workflows/runner_shared.py
+++ b/agent_workflows/runner_shared.py
@@ -47715,6 +47715,81 @@ def prepare_agent_user_config(
         return None


+AGENT_USER_CONFIG_DISCARDED_EVENT = "agent-user-config-discarded"
+
+
+def read_discarded_user_config_events(
+    run_dir: Any,
+    *,
+    raise_on_error: bool = False,
+) -> list[dict[str, Any]]:
+    """Read agent-user-config-discarded events from <run_dir>/events.jsonl."""
+    try:
+        if isinstance(run_dir, Mapping):
+            run_dir_path = Path(run_dir.get("run_dir") or run_dir.get("repo") or ".")
+        else:
+            run_dir_path = Path(run_dir)
+
+        events_path = run_dir_path / "events.jsonl"
+        events: list[dict[str, Any]] = []
+
+        if not events_path.is_file():
+            return []
+        with events_path.open("r", encoding="utf-8", errors="replace") as handle:
+            for line in handle:
+                line = line.strip()
+                if not line or AGENT_USER_CONFIG_DISCARDED_EVENT not in line:
+                    continue
+                try:
+                    data = json.loads(line)
+                    if (
+                        isinstance(data, dict)
+                        and data.get("event") == AGENT_USER_CONFIG_DISCARDED_EVENT
+                    ):
+                        if isinstance(data.get("keys"), list):
+                            data["keys"] = [str(k) for k in data["keys"]]
+                        events.append(data)
+                except Exception:
+                    continue
+        return events
+    except OSError:
+        if raise_on_error:
+            raise
+        return []
+
+
+def discarded_user_config_keys(events: Sequence[Mapping[str, Any]]) -> list[str]:
+    """Return deduplicated list of top-level key strings across events in order of first appearance."""
+    return list(
+        dict.fromkeys(
+            str(k)
+            for ev in events
+            if isinstance(ev, Mapping) and isinstance(ev.get("keys"), list)
+            for k in ev["keys"]
+        )
+    )
+
+
+def format_discarded_user_config_line(
+    events: Sequence[Mapping[str, Any]],
+) -> str | None:
+    """Format the human summary line for discarded user-config events."""
+    if not events:
+        return None
+    count = len(events)
+    details: list[str] = []
+    for ev in events:
+        id6 = ev.get("id6", "unknown")
+        f = ev.get("file", "unknown")
+        keys = ev.get("keys")
+        if keys:
+            details.append(f"{id6}: {f} {keys}")
+        else:
+            details.append(f"{id6}: {f}")
+    details_str = "; ".join(details)
+    return f"Agent user-config changes discarded: {count} ({details_str})"
+
+
 def reconcile_agent_user_config(
     handle: Optional[AgentUserConfig],
     run_dir: Path | str,
@@ -47760,7 +47835,7 @@ def reconcile_agent_user_config(
                 records.append(
                     {
                         "at": utc_now(),
-                        "event": "agent-user-config-discarded",
+                        "event": AGENT_USER_CONFIG_DISCARDED_EVENT,
                         "id6": id6,
                         "attempt": attempt_no,
                         "file": rel,
@@ -47772,7 +47847,7 @@ def reconcile_agent_user_config(
                 records.append(
                     {
                         "at": utc_now(),
-                        "event": "agent-user-config-discarded",
+                        "event": AGENT_USER_CONFIG_DISCARDED_EVENT,
                         "id6": id6,
                         "attempt": attempt_no,
                         "file": rel,
@@ -47786,7 +47861,7 @@ def reconcile_agent_user_config(
                 if current_sha != handle.seed_hashes[rel]:
                     rec: dict[str, Any] = {
                         "at": utc_now(),
-                        "event": "agent-user-config-discarded",
+                        "event": AGENT_USER_CONFIG_DISCARDED_EVENT,
                         "id6": id6,
                         "attempt": attempt_no,
                         "file": rel,
@@ -47848,42 +47923,10 @@ def report_discarded_user_config(
     out = stream if stream is not None else sys.stdout
     lines: list[str] = []
     try:
-        if isinstance(run_dir, dict):
-            run_dir_path = Path(run_dir.get("run_dir") or run_dir.get("repo") or ".")
-        else:
-            run_dir_path = Path(run_dir)
-        events_path = run_dir_path / "events.jsonl"
-        events: list[dict[str, Any]] = []
-        if events_path.is_file():
-            with events_path.open("r", encoding="utf-8") as handle:
-                for line in handle:
-                    line = line.strip()
-                    if not line:
-                        continue
-                    try:
-                        data = json.loads(line)
-                        if (
-                            isinstance(data, dict)
-                            and data.get("event") == "agent-user-config-discarded"
-                        ):
-                            events.append(data)
-                    except Exception:
-                        continue
-        if events:
-            count = len(events)
-            details = []
-            for ev in events:
-                id6 = ev.get("id6", "unknown")
-                f = ev.get("file", "unknown")
-                keys = ev.get("keys")
-                if keys:
-                    details.append(f"{id6}: {f} {keys}")
-                else:
-                    details.append(f"{id6}: {f}")
-            details_str = "; ".join(details)
-            lines.append(
-                f"Agent user-config changes discarded: {count} ({details_str})"
-            )
+        events = read_discarded_user_config_events(run_dir, raise_on_error=True)
+        line = format_discarded_user_config_line(events)
+        if line is not None:
+            lines.append(line)
     except Exception as exc:
         lines.append(f"error: failed to summarize discarded user-config changes: {exc}")
     for line in lines:
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: pasted output of a Python one-liner driving `run_viewer.load_run_summary`, `run_viewer.format_run_human` (default and `detail=True`), `run_viewer.format_multi_run_summary`, and `cli.main(["runs", "--dir", <tmp>, "--json"])` on a temp repo containing one run with `agent-user-config-discarded` events (`keys: ["color_depth"]`) and one clean run, showing `Agent user-config changes discarded: 1 (9y27t2: config.json ['color_depth'])` and `! user-config discarded: config.json ['color_depth']` in human output (default and `short=True` for the run line, `detail=True` for the step line) and `discarded_user_config_count == 1`, `discarded_user_config_keys == ["color_depth"]` on both the run record and the `9y27t2` step record in `--json` and `--agent` output (and `0` / `[]` with no extra human line on the clean run). Reachable via `run_viewer.load_run_summary`, `format_run_human`, and `render_step_details` changed in `E-03`.
  - Observed evidence:
```
=== RUN 1 HUMAN DEFAULT ===
run-20261014T100000Z-1111111  [c4q9e8]
  pid: 1111111 [exited]
  start: 2026-10-14 10:00:00, end: 2026-10-14 10:05:00, duration: 5m 00s
  1 steps: 1 executed
  Agent user-config changes discarded: 1 (9y27t2: config.json ['color_depth'])
Status   Landed Date SetID  N ID6    Action  Attempts Elapsed Cost Total Tok Verified Issue
executed yes    -    c4q9e8 - 9y27t2 execute        -       -    -         - -        no
=== RUN 1 HUMAN SHORT ===
run-20261014T100000Z-1111111  [c4q9e8]
  pid: 1111111 [exited]
  start: 2026-10-14 10:00:00, end: 2026-10-14 10:05:00, duration: 5m 00s
  1 steps: 1 executed
  Agent user-config changes discarded: 1 (9y27t2: config.json ['color_depth'])
Status   Landed Date SetID  N ID6    Action  Verified Issue
executed yes    -    c4q9e8 - 9y27t2 execute -        no
=== RUN 1 HUMAN DETAIL ===
run-20261014T100000Z-1111111  [c4q9e8]
  pid: 1111111 [exited]
  start: 2026-10-14 10:00:00, end: 2026-10-14 10:05:00, duration: 5m 00s
  1 steps: 1 executed
  Agent user-config changes discarded: 1 (9y27t2: config.json ['color_depth'])
Status   Landed Date SetID  N ID6    Action  Attempts Elapsed Cost Total Tok Verified Issue
executed yes    -    c4q9e8 - 9y27t2 execute        -       -    -         - -        no

Details for c4q9e8-9y27t2:
  ! user-config discarded: config.json ['color_depth']
=== RUN 2 HUMAN DEFAULT ===
run-20261014T110000Z-2222222  [c4q9e8]
  pid: 2222222 [exited]
  start: 2026-10-14 11:00:00, end: 2026-10-14 11:05:00, duration: 5m 00s
  1 steps: 1 executed
Status   Landed  Date SetID  N ID6    Action  Attempts Elapsed Cost Total Tok Verified Issue
executed unknown -    c4q9e8 - clean1 execute        -       -    -         - -        YES
=== MULTI RUN SUMMARY ===
--- Summary across 2 runs (2 steps) ---
Agent user-config changes discarded: 1 across 1 run(s) (['color_depth'])
No recorded cost/token data for the selected runs.
=== CLI RUNS --JSON ===
RUN run-20261014T100000Z-1111111: count=1, keys=['color_depth']
  STEP 9y27t2: count=1, keys=['color_depth']
RUN run-20261014T110000Z-2222222: count=0, keys=[]
  STEP clean1: count=0, keys=[]
=== CLI RUNS --AGENT ===
run-1 count: 1 keys: ['color_depth']
 step 9y27t2 count: 1 keys: ['color_depth']
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: pasted runner output of `python3 -m pytest -o addopts="" tests/test_agent_user_config_containment.py tests/test_run_viewer.py tests/test_runs_subdir_root.py` all passing; pasted failing output under mutation (a) and under mutation (b), each passing again after revert, with a pasted `git diff --stat -- agent_workflows/` after revert showing only `runner_shared.py` and `run_viewer.py` with the intended E-02/E-03/E-06 edits (no residual mutation); and the full bare suite `python3 -m pytest` summary line with no failing node id absent from the V-01 baseline.
  - Observed evidence: Targeted tests passing (75 passed in 17.39s), mutations (a) and (b) verified and cleanly reverted, git diff stat showing only intended files, full suite passing with 707 passed.
Targeted tests:
```
tests/test_runs_subdir_root.py ........                                  [ 10%]
tests/test_run_viewer.py ............................................... [ 73%]
...........                                                              [ 88%]
tests/test_agent_user_config_containment.py .........                    [100%]

============================= 75 passed in 17.39s ==============================
```
Mutation (a) failing output:
```
FAILED tests/test_run_viewer.py::DiscardedUserConfigRunViewerTests::test_multi_run_summary_aggregation_and_no_cost_runs
FAILED tests/test_run_viewer.py::DiscardedUserConfigRunViewerTests::test_run_viewer_cli_modes
FAILED tests/test_run_viewer.py::DiscardedUserConfigRunViewerTests::test_load_and_format_run_human_and_clean_run_equality
FAILED tests/test_run_viewer.py::DiscardedUserConfigRunViewerTests::test_execution_report_fallback_with_events
======================= 4 failed, 54 deselected in 0.96s =======================
```
Mutation (b) failing output:
```
FAILED tests/test_agent_user_config_containment.py::test_read_and_format_discarded_user_config_helpers
======================= 1 failed, 8 deselected in 3.19s ========================
```
`git diff --stat -- agent_workflows/` after revert:
```
 agent_workflows/run_viewer.py    |  82 ++++++++++++++++++++++++++
 agent_workflows/runner_shared.py | 121 ++++++++++++++++++++++++++-------------
 2 files changed, 164 insertions(+), 39 deletions(-)
```
Full bare suite summary:
```
707 passed in 22.03s
```
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: pasted `git diff -- agent_workflows/run_viewer.py` hunks for `build_multi_run_summary_dict` and `format_multi_run_summary`, and pasted output (reachable via `run_viewer.format_multi_run_summary` and `cli.main(["runs", "--dir", <tmp>, "--summary-only", "--json"])` changed in `E-06`) on a temp repo with two runs WITHOUT any cost data, one carrying a `color_depth` discard event, showing the human line `Agent user-config changes discarded: 1 across 1 run(s) (['color_depth'])` (exact rendering of the key list as implemented) and the JSON summary fields `discarded_user_config_count == 1`, `discarded_user_config_runs == 1`, `discarded_user_config_keys == ["color_depth"]`; plus the same commands on a clean repo showing no line and `0` / `0` / `[]`.
  - Observed evidence: Diff hunks for build_multi_run_summary_dict and format_multi_run_summary verified against temp repo with color_depth discard event and clean repo.
Diff hunks:
```diff
@@ -2974,6 +2974,16 @@ def build_multi_run_summary_dict(summaries: list[RunSummary]) -> dict[str, Any]:
             },
         }

+    discarded_count = sum(s.discarded_user_config_count for s in summaries)
+    discarded_runs = sum(1 for s in summaries if s.discarded_user_config_count > 0)
+    discarded_keys = list(
+        dict.fromkeys(
+            k
+            for s in summaries
+            for k in s.discarded_user_config_keys
+        )
+    )
+
     return {
         "runs_count": total_runs,
         "steps_count": total_steps,
@@ -2981,6 +2981,9 @@ def build_multi_run_summary_dict(summaries: list[RunSummary]) -> dict[str, Any]:
         "avg_cost_per_run": avg_cost_per_run,
         "total_tokens": dict(total_tokens) if total_tokens else {},
         "avg_tokens_per_run": avg_tokens_per_run,
+        "discarded_user_config_count": discarded_count,
+        "discarded_user_config_runs": discarded_runs,
+        "discarded_user_config_keys": discarded_keys,
         "by_status": status_summary,
         "by_action": action_summary,
         "by_phase": by_phase,
@@ -3006,6 +3006,17 @@ def format_multi_run_summary(summaries: list[RunSummary], term: Term) -> str:
         else header_title
     )

+    disc_count = summary_data["discarded_user_config_count"]
+    disc_runs = summary_data["discarded_user_config_runs"]
+    disc_keys = summary_data["discarded_user_config_keys"]
+    if disc_count > 0:
+        disc_line = f"Agent user-config changes discarded: {disc_count} across {disc_runs} run(s) ({disc_keys})"
+        lines.append(
+            term.color256(disc_line, 214)
+            if getattr(term, "color", False)
+            else disc_line
+        )
+
     if has_any_cost:
         cost_str = f"${total_cost:.2f}"
         cost_val_str = (
```
Output:
```
=== POPULATED REPO ===
HUMAN MULTI (with_event=True):
--- Summary across 2 runs (2 steps) ---
Agent user-config changes discarded: 1 across 1 run(s) (['color_depth'])
No recorded cost/token data for the selected runs.
JSON SUMMARY (with_event=True):
discarded_user_config_count == 1
discarded_user_config_runs == 1
discarded_user_config_keys == ['color_depth']
=== CLEAN REPO ===
HUMAN MULTI (with_event=False):
--- Summary across 2 runs (2 steps) ---
No recorded cost/token data for the selected runs.
JSON SUMMARY (with_event=False):
discarded_user_config_count == 0
discarded_user_config_runs == 0
discarded_user_config_keys == []
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: pasted `git diff -- CHANGELOG.md`, a check confirming zero `\u2013` / `\u2014` characters in the diff, and pasted output of `aw sanitize --agent` showing `"outcome":"clean"`.
  - Observed evidence: CHANGELOG.md diff pasted, dash verification confirmed zero en/em dashes, leak sanitizer clean.
`git diff -- CHANGELOG.md`:
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index c140645fa..c4f1706d9 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Added: aw runs now surfaces the count, keys, and event details of discarded agent user-config changes per run in human, --json, and --agent output from the run's durable events.jsonl log.
 - Added: aw run init command to initialize a new run ledger and write its header record from a workflow definition.
 - Fixed: aw install and install_wizard.persist_project_policy now preserve existing project.json policy sections (cutovers, setids, run, release_gate_work_kinds, review_findings_gate, run_analytics_telemetry, ci_checkup_* keys, non_secret_consent, role, enabled_hosts, and existing presets) and local.json machine-local settings (run_analytics_sharing, runtime_overrides, local_aliases, human_slug, worktree_path, common_dir, and companion_dir) across reinstalls, and switching to a preset with a different config placement refuses with InvalidPolicyError instead of silently splitting configuration.
 - Added: aw oc review and aw agy review now support re-reviewing a plan at reviewed, approved, or auto-approved behind an explicit confirmation (-y/--yes or typed phrase re-review), demoting to to-review at lane dispatch with approval withdrawn, and ending at reviewed awaiting fresh human approval.
```
Dash verification:
```
en-dashes: 0, em-dashes: 0
```
Sanitizer output:
```json
{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5241,"findings":0,"evidence":["leak-scan"],"next":null}
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Reviewed; awaiting explicit human approval (`aw ipd set approved swpf3q --by-human --message ...`). Both open questions are resolved from repository evidence and the backlog item's own ask; no maintainer decision is outstanding.

Execution contract once approved:

- Resolved questions: OQ-01 and OQ-02 are resolved; nothing remains for the maintainer.
- Order: perform E-01, E-02, E-03, E-06, E-04, E-05 in dependency order. Mutation proofs are temporary and MUST NOT be committed.
- Scope declaration (not a stop directive): `- Scope-Paths:` declares the files this plan expects to touch. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and justify it in the two-way scope reconciliation at finalize (`--scope-reason <path>=<why>`), and acknowledge any declared-but-unmodified path with `--scope-ack`. A stop is reserved for a genuinely unsafe condition (an unresolvable concurrent edit to a declared file, or a cited symbol absent at HEAD), never for a scope question.
- Honesty: paste the ACTUAL runner output into every `V-*` `Observed evidence`; never record a pass you did not observe.
- Commits: commit only the declared paths through `aw commit swpf3q -- <paths>`; never `git add -A`, never push, never tag.
- Lifecycle transition: when run by `aw oc run` / `aw agy run` as an isolated worker, do NOT run `aw ipd begin`/`aw ipd finalize` in the lane (the role marker refuses them); the driver finalizes after integration. When executed by hand, finish with `aw ipd finalize swpf3q` (never a hand-rolled `git mv` to `executed/`), and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
