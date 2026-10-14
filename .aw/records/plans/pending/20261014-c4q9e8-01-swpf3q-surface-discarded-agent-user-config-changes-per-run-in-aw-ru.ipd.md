# IPD: Surface discarded agent user-config changes per run in aw runs

- Date: 2026-10-14
- Kind: child
- Concern: Backlog `c4q9e8`: plan `9y27t2` (backlog `btw02e`) discards an agent turn's writes to the operator's user configuration and appends an `agent-user-config-discarded` event for each added, removed, or modified file to `<run_dir>/events.jsonl`, printing a turn-end warning and an end-of-run summary via `runner_shared.report_discarded_user_config`. However, `aw runs` (`agent_workflows/run_viewer.py`) never reads those events from `<run_dir>/events.jsonl`, so an operator inspecting a completed or historical run later in human or `--json` (or `--agent`) mode cannot see that an agent turn tried to modify their user configuration, how many changes were discarded, or which top-level config keys were targeted.
- Scope: IN: extract a shared reader, key-list extractor, and human summary line formatter in `agent_workflows/runner_shared.py` (`AGENT_USER_CONFIG_DISCARDED_EVENT`, `read_discarded_user_config_events`, `discarded_user_config_keys`, `format_discarded_user_config_line`) used by both `runner_shared.report_discarded_user_config` and `agent_workflows/run_viewer.py`; extend `run_viewer.StepSummary` and `run_viewer.RunSummary` with `discarded_user_config_count`, `discarded_user_config_keys`, and `discarded_user_config`; populate them in `run_viewer.load_run_summary` (both `state.json` and `execution-report.md` fallback paths); render the per-run summary line in `run_viewer.format_run_human`, per-step detail lines in `run_viewer.render_step_details`, and multi-run aggregates in `run_viewer.build_multi_run_summary_dict` and `run_viewer.format_multi_run_summary`; behavioral tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py`; and `CHANGELOG.md`. OUT: changing how user-config writes are sandboxed or reconciled during a turn (already shipped in `9y27t2`); `AW_HOME` containment (backlog `s4pys7`); `project_context` XDG config resolution (backlog `m9dobx`); flagging a discarded user-config write as a step artifact/refusal issue in `step_has_issue` (the write was contained and discarded by the runner, so the artifact and run completion remain valid; see OQ-02).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/run_viewer.py, tests/test_agent_user_config_containment.py, tests/test_run_viewer.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: c4q9e8
- Set: c4q9e8
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: swpf3q

## Workflow history

- 2026-10-14 to-review (Antigravity): authored from backlog `c4q9e8` to surface the count and keys of discarded agent user-config changes per run in `aw runs` (human, `--json`, and `--agent`).
- 2026-10-14 draft (Antigravity): created.

## Goal

When an operator inspects runs with `aw runs` (in human, `--json`, or `--agent` mode), each run (and step) surfaces the count, deduplicated top-level keys, and durable event records of any agent user-config changes that were discarded during the run, read through one shared `events.jsonl` reader used by both the end-of-run report and the run viewer.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: baseline and shared `events.jsonl` reader in `agent_workflows/runner_shared.py`

- [ ] E-01 CAPTURE THE BASELINE: run the bare suite `python3 -m pytest` BEFORE the first edit and record its summary line and any failing node ids. The post-change bar is that no node id fails that did not fail here.
  - Depends on: none
  - Expected outcome: a recorded baseline summary line and failing-node-id list.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/runner_shared.py` (user-config containment section around `runner_shared.reconcile_agent_user_config` at line 47214 and `runner_shared.report_discarded_user_config` at line 47333), define `AGENT_USER_CONFIG_DISCARDED_EVENT = "agent-user-config-discarded"` and extract three shared helpers:
  1. `read_discarded_user_config_events(run_dir: Any, *, raise_on_error: bool = False) -> list[dict[str, Any]]`: resolves `run_dir_path` (`Path(run_dir.get("run_dir") or run_dir.get("repo") or ".")` when `isinstance(run_dir, Mapping)` else `Path(run_dir)`), opens `<run_dir_path>/events.jsonl` when `is_file()`, and returns each JSON object line where `data.get("event") == AGENT_USER_CONFIG_DISCARDED_EVENT` (normalizing `keys` to `[str(k) for k in data["keys"]]` when `isinstance(data.get("keys"), list)`). Skips blank or malformed JSON lines; when `raise_on_error=False` (default, for read-only viewer callers), catches `OSError` and returns `[]`.
  2. `discarded_user_config_keys(events: Sequence[Mapping[str, Any]]) -> list[str]`: returns the deduplicated list of top-level key strings across `events` in order of first appearance (`list(dict.fromkeys(str(k) for ev in events if isinstance(ev, Mapping) and isinstance(ev.get("keys"), list) for k in ev["keys"]))`).
  3. `format_discarded_user_config_line(events: Sequence[Mapping[str, Any]]) -> str | None`: returns `None` when `events` is empty, and otherwise returns `"Agent user-config changes discarded: <count> (<id6>: <file> <keys>; ...)"` with the exact formatting `runner_shared.report_discarded_user_config` already emits.
  Update `runner_shared.reconcile_agent_user_config` to reference `AGENT_USER_CONFIG_DISCARDED_EVENT` and refactor `runner_shared.report_discarded_user_config` to call `read_discarded_user_config_events(run_dir, raise_on_error=True)` and `format_discarded_user_config_line(events)`.
  - Depends on: E-01
  - Expected outcome: one shared constant, reader, key extractor, and formatter in `agent_workflows/runner_shared.py`; `runner_shared.report_discarded_user_config` produces byte-identical output for both populated and clean run directories while sharing the reader with `run_viewer`.
  - Execution state: pending

### Task group 2: surface per-run and per-step discarded user-config changes in `agent_workflows/run_viewer.py`

- [ ] E-03 In `agent_workflows/run_viewer.py`:
  1. Import `discarded_user_config_keys`, `format_discarded_user_config_line`, and `read_discarded_user_config_events` from `agent_workflows.runner_shared` (at `from agent_workflows.runner_shared import`, lines 41-51).
  2. Add three defaulted fields to `run_viewer.StepSummary` (around line 215) and `run_viewer.RunSummary` (around line 244):
     - `discarded_user_config_count: int = 0`
     - `discarded_user_config_keys: list[str] = field(default_factory=list)`
     - `discarded_user_config: list[dict[str, Any]] = field(default_factory=list)`
  3. In `run_viewer.load_run_summary` (lines 944-1378), read `discarded_events = read_discarded_user_config_events(run_dir)` once, index events by `str(ev.get("id6") or "").strip()`, populate the three fields on each `StepSummary` in both the `state.json` loop (lines 1173-1215) and the `execution-report.md` fallback loop (lines 1295-1314), and populate `discarded_user_config_count=len(discarded_events)`, `discarded_user_config_keys=discarded_user_config_keys(discarded_events)`, and `discarded_user_config=discarded_events` on the returned `RunSummary` (lines 1357-1378).
  4. In `run_viewer.format_run_human` (right after the cost/tokens block at line 2610, before `if run.steps:`), format the run's discarded user-config summary line using `format_discarded_user_config_line(run.discarded_user_config)` (with a fallback to `f"Agent user-config changes discarded: {run.discarded_user_config_count} ({run.discarded_user_config_keys})"` or without parenthetical keys when `run.discarded_user_config` was not populated on a synthetic `RunSummary` instance with `discarded_user_config_count > 0`), indent by two spaces (`"  " + disc_line`), style with `term.color256(..., 214)` when `getattr(term, "color", False)` is True, and append to `lines`. Emit nothing when count is 0.
  5. In `run_viewer.render_step_details` (around line 2460, before `if details:`), for each event `ev` in `step.discarded_user_config`, append `"  ! user-config discarded: <file> <keys>"` (or `"  ! user-config discarded: <file> (<change>)"` when `keys` is absent/empty, or `"  ! user-config discarded: <file>"` when neither is present), styled with `term.color256(..., 214)` when color is enabled.
  6. In `run_viewer.build_multi_run_summary_dict` (lines 2681-2930) and `run_viewer.format_multi_run_summary` (lines 2933-3245), aggregate `discarded_user_config_count` (sum across `summaries`) and `discarded_user_config_keys` (deduplicated keys in order of appearance across `summaries`) into the returned summary dict, and when `discarded_user_config_count > 0` append `"Agent user-config changes discarded: <count> (<keys>)"` (styled with color `214` when color is enabled) in `format_multi_run_summary` right after the `Total Cost:` / `Total Tokens:` header lines.
  - Depends on: E-02
  - Expected outcome: `aw runs` human output (default, `--short`, `--detail`, `--summary-only`, and multi-run) and `aw runs --json` (and `--agent`) surface the count, keys, and event details of discarded user-config changes per run and per step when present, while clean runs with zero events have unchanged human output and `0` / `[]` fields in JSON.
  - Execution state: pending

### Task group 3: behavioral tests and changelog

- [ ] E-04 Add behavioral tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py`:
  1. In `tests/test_agent_user_config_containment.py`, add `test_read_and_format_discarded_user_config_helpers` testing `runner_shared.read_discarded_user_config_events`, `runner_shared.discarded_user_config_keys`, and `runner_shared.format_discarded_user_config_line` across: (i) multiple events across turns/files with overlapping and non-overlapping `keys` plus an `added` non-JSON file without `keys`; (ii) blank and malformed lines in `events.jsonl` ignored without raising; (iii) missing `events.jsonl` returning `[]` and `None`; and (iv) end-to-end integration where `reconcile_agent_user_config` writes to `events.jsonl` and `run_viewer.load_run_summary` + `run_viewer.format_run_human` + `cli.main(["runs", "--dir", ..., "--json", ...])` surface the exact count (`1`) and keys (`["color_depth"]`).
  2. In `tests/test_run_viewer.py`, add `test_discarded_user_config_surfaced_in_human_and_json` testing `run_viewer.load_run_summary`, `run_viewer.format_run_human` (default, `--short`, `--detail`, colored and uncolored), `run_viewer.build_multi_run_summary_dict`, `run_viewer.format_multi_run_summary`, ` execution-report.md` fallback loading with `events.jsonl`, and `run_viewer.run_viewer_cli` (`--json`, `--summary-only --json`, `--latest-only --json`, `--agent`, and human) across a run with discarded user-config events and a clean run without them.
  - Depends on: E-03
  - Expected outcome: all new and existing tests in `tests/test_agent_user_config_containment.py` and `tests/test_run_viewer.py` pass, and the new tests fail if the `E-03` wiring in `run_viewer.py` is reverted.
  - Execution state: pending

- [ ] E-05 In `CHANGELOG.md`, add one `- Added:` bullet at the top of the `## 2.0.0 (pending)` entry list (around line 27) stating that `aw runs` now surfaces the count, keys, and event details of discarded agent user-config changes per run in human, `--json`, and `--agent` output from the run's durable `events.jsonl` log. Write no em or en dashes (user-facing prose rule).
  - Depends on: E-03
  - Expected outcome: one new `- Added:` bullet in `CHANGELOG.md` with no em or en dashes and `aw sanitize --agent` clean.
  - Execution state: pending

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
- Under-scope: none. Both human (`format_run_human`, `render_step_details`, `format_multi_run_summary`) and `--json` / `--agent` (`RunSummary`, `StepSummary`, `build_multi_run_summary_dict`) surfaces of `aw runs` are covered.

## Required tests / validation

- Targeted behavioral tests: `python3 -m pytest tests/test_agent_user_config_containment.py tests/test_run_viewer.py`
- Full bare test suite: `python3 -m pytest` compared against the E-01 baseline
- Leak sanitizer: `aw sanitize --agent`

## Spec / documentation sync

- No spec amendment required: no specification in `.aw/records/specs/` defines the field list of `RunSummary` or `StepSummary` in `run_viewer.py`.
- `CHANGELOG.md` updated under `## 2.0.0 (pending)` (E-05).

## Open questions

### OQ-01: What field names and human format should `aw runs` use for discarded user-config changes?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED from the backlog item's ask ("Surface the count and keys of discarded user-config changes per run in `aw runs` (human and `--json`), reading the same durable events") and plan `9y27t2` E-05: on `RunSummary` (and `StepSummary`), expose `discarded_user_config_count: int`, `discarded_user_config_keys: list[str]`, and `discarded_user_config: list[dict[str, Any]]` so `--json` and `--agent` consumers have the explicit count, the deduplicated top-level key list, and the per-event records (`id6`, `file`, `change`, `attempt`, `keys`). In human mode, `format_run_human` renders `  Agent user-config changes discarded: <n> (<id6>: <file> <keys>; ...)` via the shared `format_discarded_user_config_line` helper when count > 0 and omits the line when count == 0, matching `report_discarded_user_config` word-for-word.

### OQ-02: Should a discarded user-config write flip the step's `Issue` column to `YES` in `aw runs`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED to NO. `run_viewer.step_issue_reasons` (`agent_workflows/run_viewer.py`, lines 563-601) flags two classes that require operator remediation: an artifact location/status discrepancy or a runner refusal/abandonment where the step's work did not land cleanly. A discarded user-config change was already neutralized automatically by `reconcile_agent_user_config` (`9y27t2`), so no operator remediation is needed and flagging `Issue: YES` would cause `aw runs --issues` to report healthy completed steps as broken. Surfacing the line in the run header, in `--detail` step lines, in `--summary-only`, and in `--json`/`--agent` fields gives full visibility without false-positive issue flags.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: the pasted pre-change `python3 -m pytest` summary line and the list of any failing node ids.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: pasted output of a Python one-liner driving `runner_shared.read_discarded_user_config_events`, `runner_shared.discarded_user_config_keys`, `runner_shared.format_discarded_user_config_line`, and `runner_shared.report_discarded_user_config` on a temp run dir with two `agent-user-config-discarded` events in `events.jsonl` and on an empty run dir, plus `git diff -- agent_workflows/runner_shared.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: pasted output of a Python one-liner driving `run_viewer.load_run_summary`, `run_viewer.format_run_human` (default and `detail=True`), `run_viewer.format_multi_run_summary`, and `cli.main(["runs", "--dir", <tmp>, "--json"])` on a temp repo containing one run with `agent-user-config-discarded` events (`keys: ["color_depth"]`) and one clean run, showing `Agent user-config changes discarded: 1 (9y27t2: config.json ['color_depth'])` and `! user-config discarded: config.json ['color_depth']` in human output and `discarded_user_config_count == 1`, `discarded_user_config_keys == ["color_depth"]` in `--json` output (and `0` / `[]` with no extra human line on the clean run).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: pasted runner output of `python3 -m pytest -o addopts="" tests/test_agent_user_config_containment.py tests/test_run_viewer.py` and the full bare suite `python3 -m pytest` showing all tests passing with no new failures vs the V-01 baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `git diff -- CHANGELOG.md`, a check confirming zero `\u2013` / `\u2014` characters in the diff, and pasted output of `aw sanitize --agent` showing `"outcome":"clean"`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Ready for `/plan-review`, then explicit human approval (`aw ipd set approved swpf3q --by-human --message ...`). Both open questions are resolved from repository evidence and the backlog item's own ask; no maintainer decision is outstanding.

Execution contract once approved:

- Resolved questions: OQ-01 and OQ-02 are resolved; nothing remains for the maintainer.
- Order: perform E-01..E-05 in dependency order.
- Scope declaration (not a stop directive): `- Scope-Paths:` declares the files this plan expects to touch. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and justify it in the two-way scope reconciliation at finalize (`--scope-reason <path>=<why>`), and acknowledge any declared-but-unmodified path with `--scope-ack`. Stop and report only for a genuinely unsafe condition (an unresolvable concurrent edit to a declared file, or a cited symbol absent at HEAD).
- Honesty: paste the ACTUAL runner output into every `V-*` `Observed evidence`; never record a pass you did not observe.
- Commits: commit only the declared paths through `aw commit swpf3q -- <paths>`; never `git add -A`, never push, never tag.
- Lifecycle transition: when run by `aw oc run` / `aw agy run` as an isolated worker, do NOT run `aw ipd begin`/`aw ipd finalize` in the lane (the role marker refuses them); the driver finalizes after integration. When executed by hand, finish with `aw ipd finalize swpf3q` (never a hand-rolled `git mv` to `executed/`), and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass`.
