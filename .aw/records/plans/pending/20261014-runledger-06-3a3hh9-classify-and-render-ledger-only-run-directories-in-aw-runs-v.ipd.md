# IPD: Classify and render ledger-only run directories in aw runs viewer

- Date: 2026-10-14
- Kind: child
- Concern: `run_viewer.discover_run_dirs` admits every `run-*` directory under `state_root(repo)`, and `run_viewer.load_run_summary` treats any directory lacking `state.json` and `execution-report.md` as an empty driver run (`steps=[]`, `counts={}`), causing `format_run_human` (`aw runs`) to render a ledger-only run directory created by `aw run init` (plan `v47z9u`, writing `state_root(repo)/<run-id>/ledger.jsonl`) as a driver run with `0 steps: 0 steps`. In addition, `run_cli._reconstruct_workflow_from_ledger` collects step IDs only from `step_attempt` records and ignores `step_started` records, `resolve_target_runs_detailed` rejects explicit directory or file paths to a ledger-only run, and `run_viewer_cli` filters (`--active`, `--status`, `--failed`) inspect only `summary.steps` (`StepSummary` rows). Backlog `nf84rt`.
- Scope: (1) In `agent_workflows/run_cli.py`, widen `_reconstruct_workflow_from_ledger` to recover step IDs from `kind in ("step_started", "step_attempt")` records so started-but-not-yet-attempted steps surface as `running` in `RunEngine.reconstruct_state()`. (2) In `agent_workflows/run_viewer.py`, add `ledger: dict[str, Any] | None = None` to `RunSummary`, add `_load_ledger_run_summary(run_dir, ledger_file)` verifying and reconstructing `ledger.jsonl` via `RunLedgerStore.read_records(verify=True)` and `RunEngine.reconstruct_state()` (returning `None` on corrupt/invalid/empty ledgers so `run_viewer_cli` records `unreadable_state`), and branch `load_run_summary` to call `_load_ledger_run_summary` when neither `state.json` nor `execution-report.md` is present and `(run_dir / "ledger.jsonl").is_file()`. (3) In `agent_workflows/run_viewer.py`, extend `resolve_target_runs_detailed` to resolve explicit directory paths containing `ledger.jsonl` (or `execution-report.md`) and explicit file paths named `ledger.jsonl`, update `run_viewer_cli` filter predicates (`active_only`, `status_filter`, `failed_only`) to evaluate `summary.ledger` and `summary.counts` on ledger runs, and update `format_run_human` to render ledger-only runs with the ledger model (`[ledger]`, `ledger: state=..., records=..., workflow=...`, step tally and per-step lines or `ledger steps: 0 recorded`, and the signpost `inspect: aw runs status <run_id> | aw runs show <run_id>`) instead of `0 steps: 0 steps`. (4) In `tests/test_run_viewer.py`, add `LedgerRunViewerTests` covering header-only and progressed ledger runs across human, `--json`, and `--agent` outputs, explicit path resolution, filter flags, and fail-closed `unreadable_state` exclusion. OUT: adding `aw run init` itself (`v47z9u`), amending spec `25kzda` (`9epp40`), adding ledger leaves to `LIVE_SAFE_LEAVES` (`g5s94t`), writing `requirement_set` on init or adding `aw run verify` (`um0twl`), and persisting `wf.json` beside the ledger (`sflov4`).
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/run_cli.py, tests/test_run_viewer.py
- Item-Dependencies: executed:v47z9u
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: nf84rt
- Set: runledger
- Order: 6
- Highest E allocated: 05
- Author: antigravity
- Id: 3a3hh9

## Workflow history
- 2026-10-14 to-review (aw set): authored review-ready IPD from backlog nf84rt

- 2026-10-14 draft (antigravity): created.

## Goal

Classify ledger-only run directories (`ledger.jsonl` present without `state.json` or `execution-report.md`, as created by `aw run init` in plan `v47z9u`) inside `agent_workflows/run_viewer.py` and reconstruct and render them using the ledger run model (`RunLedgerStore` + `RunEngine.reconstruct_state` + `aw runs status` / `aw runs show` signpost) so `aw runs` never misreports a ledger run as a driver run with `0 steps: 0 steps`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reconstruct and classify ledger-only run directories

- [ ] E-01 In `agent_workflows/run_cli.py`, update `_reconstruct_workflow_from_ledger` so the step-extraction branch matches `elif kind in ("step_started", "step_attempt"):` instead of only `elif kind == "step_attempt":`.
  - Depends on: none
  - Expected outcome: A ledger containing a `step_started` record (written by `aw run start` before any `step_attempt` record) includes that step ID in the reconstructed workflow skeleton, and `RunEngine.reconstruct_state()` reports the step with `state == "running"` and `run_state == "running"`.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/run_viewer.py`, add `ledger: dict[str, Any] | None = None` to `RunSummary`, implement `_load_ledger_run_summary(run_dir: Path, ledger_file: Path) -> RunSummary | None`, and branch `load_run_summary` to delegate to `_load_ledger_run_summary` when `not state_file.is_file() and not report_file.is_file() and (run_dir / "ledger.jsonl").is_file()`.
  - Depends on: E-01
  - Expected outcome: For a ledger-only run directory with a valid hash-chained `ledger.jsonl`, `load_run_summary` verifies the chain via `RunLedgerStore(ledger_file).read_records(verify=True)`, reconstructs `RunStateSnapshot` via `run_cli._reconstruct_workflow_from_ledger` and `run_engine.RunEngine.reconstruct_state`, and returns a `RunSummary` with `ledger` populated (`run_id`, `run_state`, `workflow_id`, `workflow_digest`, `requirement_digest`, `record_count`, `steps`, `approvals`, `verifier_decisions`, `cancellation_reason`), `created_at` and `updated_at` taken from the first and last record `timestamp` fields, `counts` tallied by ledger step state, and `steps=[]`; for an unreadable, wrong-format, corrupt, or empty `ledger.jsonl`, `_load_ledger_run_summary` returns `None` so `run_viewer_cli` records `"unreadable_state"` in `excluded`.
  - Execution state: pending

### Task group 2: Viewer target resolution, filtering, and human/machine rendering

- [ ] E-03 In `agent_workflows/run_viewer.py`, update `resolve_target_runs_detailed` to accept explicit directory targets containing `ledger.jsonl` (or `execution-report.md` in addition to `state.json`) and explicit file targets named `ledger.jsonl`, and update `run_viewer_cli`'s `active_only`, `status_filter`, and `failed_only` filter checks to evaluate `summary.ledger` and `summary.counts` when `summary.ledger is not None`.
  - Depends on: E-02
  - Expected outcome: Passing `<runs-root>/run-<hex>` or `<runs-root>/run-<hex>/ledger.jsonl` to `resolve_target_runs_detailed` resolves to `<runs-root>/run-<hex>` (while still rejecting paths under `analytics/`), `run_cli._classify_absent_target` remains unaffected because it requires `(run_dir / "state.json").is_file()`, and `aw runs` filter flags (`--active`, `--status`, `--failed`) match ledger-only runs against `summary.ledger["run_state"]` and `summary.counts`.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/run_viewer.py`, update `format_run_human` so that when `run.ledger is not None`, it renders the ledger model instead of the driver-run `0 steps: 0 steps` tally.
  - Depends on: E-02
  - Expected outcome: For a ledger-only `RunSummary`, `format_run_human` emits `<run_id>  [ledger]` on the header line, the timing line from the ledger timestamps, `  ledger: state=<styled_run_state>, records=<record_count>, workflow=<workflow_id>` (styling `<run_state>` with `_resolve_ledger_status`), either `  <N> ledger steps: <tally>` with indented `    <step_id>: <styled_state> (attempts=<attempts>)` lines or `  ledger steps: 0 recorded` when `run.ledger["steps"]` is empty, optional `  cancellation: <reason>` when cancelled, and `  inspect: aw runs status <run_id> | aw runs show <run_id>`, without emitting `0 steps: 0 steps`.
  - Execution state: pending

### Task group 3: Unit and CLI integration tests

- [ ] E-05 In `tests/test_run_viewer.py`, add `LedgerRunViewerTests` exercising header-only and progressed ledger-only run directories across `load_run_summary`, `format_run_human`, `resolve_target_runs_detailed`, and `aw runs` CLI invocations (human, `--json`, `--agent`, filter flags, and corrupt-ledger `unreadable_state` exclusion).
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: `python3 -m pytest tests/test_run_viewer.py tests/test_run_recovery_cli.py` passes with `LedgerRunViewerTests` verifying all four scenarios and all existing viewer and recovery tests green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Two run models share `state_root(repo)` (`utb2qr`, `rdjka2`, `v47z9u`, `d91i3e`)**: Decision record `utb2qr` and executed plan `rdjka2` established that `aw oc run` / `aw agy run` write driver runs (`state.json`, `events.jsonl`, `execution-report.md`, `outcomes/*.json`) and do not write `ledger.jsonl`, while `aw run init` (plan `v47z9u`) initializes standalone hash-chained workflow ledgers at `state_root(repo)/<run-id>/ledger.jsonl`. Executed plan `d91i3e` added the driver-run signpost in `run_cli._classify_absent_target` (`TARGET_LEDGER_RUN`, `TARGET_DRIVER_RUN`, `TARGET_UNKNOWN`) when a ledger verb (`aw runs show|status|...`) is pointed at a driver run; this plan (`3a3hh9`, from backlog `nf84rt`) closes the mirror direction when the viewer (`aw runs`) encounters a ledger-only directory under `state_root(repo)`.
- **Read surfaces never mutate (`GUIDING_PRINCIPLES.md` P10, `fduoj4`)**: `run_viewer.load_run_summary` and `run_viewer.run_viewer_cli` are strictly read-only inspection paths and must never write to or lock `ledger.jsonl`; `RunLedgerStore(ledger_file).read_records(verify=True)` reads and verifies the hash chain without acquiring `writer_lock` or mutating disk state.
- **Artifact audit scope (`run_viewer.audit_step_artifact`, `6ltz1y`, `zexed1`)**: `run_viewer_cli` iterates `for s in summaries: for st in s.steps: audit_step_artifact(st, ...)` to check `.aw/records/` artifact locations and statuses by `id6`. Workflow steps inside `ledger.jsonl` carry workflow step IDs (`S-01`, `S-02` per `run_ledger_schema._STEP_ID_RE`), not repository artifact `id6`s. Keeping `RunSummary.steps = []` for ledger-only runs and storing the ledger's step map under `RunSummary.ledger["steps"]` prevents `audit_step_artifact` from falsely flagging workflow step IDs as `missing_entirely` (`CLASS_MISSING`) in `--issues`, `--json`, and the human discrepancy table.
- **Section 7.3 run-ledger status styling (`run_viewer._resolve_ledger_status`)**: `agent_workflows/run_viewer.py` already defines `_resolve_ledger_status(token)` (`return _LS.resolve_status(token, "run_ledger")`) at `_resolve_ledger_status` for styling run-ledger lifecycle states (`pending`, `runnable`, `running`, `performed`, `verified`, `complete`, `blocked`, `failed`, `cancelled`, `interrupted`, `abandoned`, `unknown_outcome`).
- **Live-runs test isolation (`tests/test_run_viewer.py` `_forbid_live_runs_reads`)**: `tests/test_run_viewer.py` installs a `sys.addaudithook` fixture forbidding any test from reading the repository's real `.aw/records/runs/` tree; all tests in `tests/test_run_viewer.py` must construct temporary roots via `tempfile.TemporaryDirectory()`.

## Findings

| # | Location | Observation | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/run_viewer.py` `discover_run_dirs` (`def discover_run_dirs`) and `load_run_summary` (`def load_run_summary`) | `discover_run_dirs` admits every `run-*` subdirectory under `state_root(repo_root)`. In `load_run_summary`, when `state_file.is_file()` (`state.json`) and `report_file.is_file()` (`execution-report.md`) are both `False`, the function falls through and returns `RunSummary(run_id=run_dir.name, run_dir=run_dir, steps=[], counts={}, ...)` without checking `(run_dir / "ledger.jsonl").is_file()`. | In `format_run_human` (`tally_str = ", ".join(tally_parts) if tally_parts else f"{len(run.steps)} steps"`), a ledger-only run directory created by `aw run init` renders as `run-abcdef1234` followed by `  0 steps: 0 steps`. |
| F-02 | `agent_workflows/run_cli.py` `_reconstruct_workflow_from_ledger` (`def _reconstruct_workflow_from_ledger`) | `_reconstruct_workflow_from_ledger` recovers step IDs only from `elif kind == "step_attempt":` records, ignoring `kind == "step_started"` records (`RECORD_KINDS_V2_ONLY`). Meanwhile, `RunEngine.reconstruct_state` (`def reconstruct_state` in `agent_workflows/run_engine.py`) only records a `step_started` transition (`step_states[sid] = run_state.STATE_RUNNING`) when `sid in self._workflow_steps`. | If a step has been started (`aw run start <target> --step S-01 --workflow wf.json`) and has not yet recorded a `step_attempt`, reconstructing state from the ledger alone omits `S-01` from `_workflow_steps` and therefore omits `S-01` from `snapshot.steps`. |
| F-03 | `agent_workflows/run_viewer.py` `resolve_target_runs_detailed` (`def resolve_target_runs_detailed`) | For explicit path targets, `resolve_target_runs_detailed` checks `if p.is_dir() and (p / "state.json").is_file():` and `elif p.is_file() and p.name in ("state.json", "events.jsonl", "execution-report.md"):`. Meanwhile, `run_cli._classify_absent_target` (`def _classify_absent_target`) calls `resolve_target_runs_detailed` and then checks `if (run_dir / "state.json").is_file(): return TARGET_DRIVER_RUN`. | Passing an explicit directory path `<runs>/run-abcdef1234` or file path `<runs>/run-abcdef1234/ledger.jsonl` to `aw runs` fails with `no run matched target` even though bare `aw runs run-abcdef1234` matches by directory name. Extending the explicit-path branch to accept `ledger.jsonl` (and `execution-report.md` on directory targets) fixes explicit path targeting without altering `_classify_absent_target`. |
| F-04 | `agent_workflows/run_viewer.py` `run_viewer_cli` (`def run_viewer_cli`) | In `run_viewer_cli`, the `active_only` (`--active`), `status_filter` (`--status`), and `failed_only` (`--failed`) filters inspect only `summary.steps` (`StepSummary` entries). | Because ledger-only runs keep `summary.steps = []` (to avoid running `audit_step_artifact` against workflow step IDs like `S-01`), `--active`, `--status`, and `--failed` would unconditionally exclude every ledger-only run unless those predicates also check `summary.ledger` and `summary.counts`. |

## Proposed changes (ordered, validatable)

### 1. Recover `step_started` steps in `run_cli._reconstruct_workflow_from_ledger` (`E-01`)

In `agent_workflows/run_cli.py` inside `_reconstruct_workflow_from_ledger` (`elif kind == "step_attempt":`), widen the condition to:

```python
        elif kind in ("step_started", "step_attempt"):
            sid = str(rec.get("step", ""))
            if sid and sid not in seen_steps:
                seen_steps.add(sid)
                step_ids.append(sid)
```

### 2. Classify and reconstruct ledger-only run directories in `run_viewer.py` (`E-02`)

1. In `agent_workflows/run_viewer.py` on `RunSummary` (`class RunSummary`), add:
   ```python
   ledger: dict[str, Any] | None = None
   ```
   after `runtime_str: str | None = None`.
2. Add helper `_load_ledger_run_summary(run_dir: Path, ledger_file: Path) -> RunSummary | None` immediately before `load_run_summary`:
   ```python
   def _load_ledger_run_summary(
       run_dir: Path, ledger_file: Path
   ) -> RunSummary | None:
       """Reconstruct a RunSummary for a ledger-only run directory (`nf84rt` / `3a3hh9` E-02).

       Reads and verifies `ledger.jsonl` via `RunLedgerStore.read_records(verify=True)` (read-only;
       acquires no lock and mutates nothing). Returns `None` when the file is not a valid ledger,
       fails hash-chain verification, or is empty, so `run_viewer_cli` classifies it under
       `excluded` (`unreadable_state`) rather than rendering a phantom 0-step driver run.
       """
       from agent_workflows import run_cli as _run_cli
       from agent_workflows import run_engine as _run_engine
       from agent_workflows import run_ledger_store as _ledger_store

       store_inst = _ledger_store.RunLedgerStore(ledger_file)
       try:
           records = store_inst.read_records(verify=True)
       except Exception:
           return None
       if not records:
           return None

       run_rec = records[0] if records[0].get("kind") == "run" else {}
       run_id = str(run_rec.get("run_id") or run_dir.name)
       created_at = str(run_rec.get("timestamp") or "") or None
       updated_at = str(records[-1].get("timestamp") or "") or None

       try:
           workflow = _run_cli._reconstruct_workflow_from_ledger(records)
           engine = _run_engine.RunEngine(workflow, store_inst, run_id=run_id)
           snapshot = engine.reconstruct_state()
       except Exception:
           return None

       ledger_payload = _run_cli._snapshot_payload(snapshot)
       ledger_payload["workflow_digest"] = str(run_rec.get("workflow_digest") or "")
       ledger_payload["requirement_digest"] = str(
           run_rec.get("requirement_digest") or ""
       )

       counts: dict[str, int] = defaultdict(int)
       for st in snapshot.steps.values():
           counts[st.state] += 1

       temp_summary = RunSummary(
           run_id=run_id,
           run_dir=run_dir,
           created_at=created_at,
           updated_at=updated_at,
       )
       ts_dt = temp_summary.timestamp_dt
       pid, pid_state, is_live, runtime_seconds, runtime_str = (
           inspect_run_pid_and_runtime(run_dir, created_at, updated_at, ts_dt)
       )
       return RunSummary(
           run_id=run_id,
           run_dir=run_dir,
           created_at=created_at,
           updated_at=updated_at,
           steps=[],
           counts=dict(counts),
           pid=pid,
           pid_state=pid_state,
           is_live=is_live,
           runtime_seconds=runtime_seconds,
           runtime_str=runtime_str,
           ledger=ledger_payload,
       )
   ```
3. At the top of `load_run_summary` (`def load_run_summary`), after defining `state_file = run_dir / "state.json"` and `report_file = run_dir / "execution-report.md"`, check:
   ```python
   ledger_file = run_dir / "ledger.jsonl"
   if (
       not state_file.is_file()
       and not report_file.is_file()
       and ledger_file.is_file()
   ):
       return _load_ledger_run_summary(run_dir, ledger_file)
   ```

### 3. Update `resolve_target_runs_detailed` and `run_viewer_cli` filter predicates (`E-03`)

1. In `agent_workflows/run_viewer.py` inside `resolve_target_runs_detailed` (`if p.is_dir() and (p / "state.json").is_file():`), widen the explicit directory and file checks to:
   ```python
            if p.is_dir() and (
                (p / "state.json").is_file()
                or (p / "execution-report.md").is_file()
                or (p / "ledger.jsonl").is_file()
            ):
                if p not in matched:
                    matched.append(p)
                target_matched = True
            elif p.is_file() and p.name in (
                "state.json",
                "events.jsonl",
                "execution-report.md",
                "ledger.jsonl",
            ):
   ```
2. In `run_viewer_cli` (`for r_dir in run_dirs:`), update `status_filter`, `failed_only`, and `active_only` so ledger-only runs (`summary.ledger is not None`) are evaluated against `summary.ledger["run_state"]` and `summary.counts`:
   ```python
        if status_filter:
            target_st = canonical_terminal_status(status_filter)
            if summary.ledger is not None:
                ledger_st = canonical_terminal_status(
                    str(summary.ledger.get("run_state") or "")
                )
                step_match = any(
                    canonical_terminal_status(st) == target_st
                    for st in summary.counts
                )
                if ledger_st != target_st and not step_match:
                    excluded.append((r_dir, "status_filter", summary))
                    continue
            elif not any(
                canonical_terminal_status(s.status) == target_st
                for s in summary.steps
            ):
                excluded.append((r_dir, "status_filter", summary))
                continue

        if failed_only:
            if summary.ledger is not None:
                run_st = str(summary.ledger.get("run_state") or "")
                if run_st not in _FAILED_FILTER_STATUSES and not any(
                    st in _FAILED_FILTER_STATUSES for st in summary.counts
                ):
                    excluded.append((r_dir, "failed_only", summary))
                    continue
            elif not any(
                (
                    canonical_terminal_status(s.status) in _FAILED_FILTER_STATUSES
                    or s.status in _FAILED_FILTER_STATUSES
                )
                for s in summary.steps
            ):
                excluded.append((r_dir, "failed_only", summary))
                continue

        if active_only:
            if summary.ledger is not None:
                if (
                    summary.ledger.get("run_state") != "running"
                    and "running" not in summary.counts
                ):
                    excluded.append((r_dir, "active_only", summary))
                    continue
            elif not any(s.status == "running" for s in summary.steps):
                excluded.append((r_dir, "active_only", summary))
                continue
   ```

### 4. Render ledger-only runs with the ledger model in `format_run_human` (`E-04`)

In `agent_workflows/run_viewer.py` inside `format_run_human` (`def format_run_human`):
1. When building `set_txt` for the header line (`if run.setids:`), if `run.ledger is not None` and `not set_txt`, set `set_txt = "  [ledger]"`.
2. Immediately before `# Line 3: Step count and status tally` (`tally_parts = []`), branch on `if run.ledger is not None:`:
   ```python
    if run.ledger is not None:
        run_state_raw = str(run.ledger.get("run_state") or "unknown")
        run_state_txt = term.style_lifecycle_text(
            run_state_raw, _resolve_ledger_status(run_state_raw)
        )
        rec_count = int(run.ledger.get("record_count") or 0)
        wf_id = str(run.ledger.get("workflow_id") or "-")
        lines.append(
            f"  ledger: state={run_state_txt}, records={rec_count}, workflow={wf_id}"
        )
        ledger_steps = run.ledger.get("steps") or {}
        if ledger_steps:
            tally_parts = [
                f"{cnt} {st}" for st, cnt in sorted(run.counts.items())
            ]
            tally_str = ", ".join(tally_parts)
            lines.append(f"  {len(ledger_steps)} ledger steps: {tally_str}")
            for sid, st_info in sorted(ledger_steps.items()):
                st_raw = str(st_info.get("state") or "pending")
                st_styled = term.style_lifecycle_text(
                    st_raw, _resolve_ledger_status(st_raw)
                )
                att_cnt = int(st_info.get("attempts") or 0)
                lines.append(f"    {sid}: {st_styled} (attempts={att_cnt})")
        else:
            lines.append("  ledger steps: 0 recorded")
        cancel_reason = run.ledger.get("cancellation_reason")
        if cancel_reason:
            lines.append(f"  cancellation: {cancel_reason}")
        lines.append(
            f"  inspect: aw runs status {run.run_id} | aw runs show {run.run_id}"
        )
        return "\n".join(lines)
   ```

### 5. Add `LedgerRunViewerTests` in `tests/test_run_viewer.py` (`E-05`)

In `tests/test_run_viewer.py`, add `LedgerRunViewerTests(TestCase)` testing:
- `test_header_only_ledger_run_renders_ledger_model_not_zero_driver_steps`: creates `state_root(root)/run-abcdef1234/ledger.jsonl` with a valid `kind="run"` root record via `RunLedgerStore.append`, asserts `load_run_summary` returns `ledger["run_state"] == "pending"`, `ledger["record_count"] == 1`, `ledger["steps"] == {}`, and asserts both `format_run_human` and CLI `_run_viewer(root, [])` / `_run_viewer(root, ["run-abcdef1234"])` exit 0, include `[ledger]`, `ledger: state=pending, records=1`, `ledger steps: 0 recorded`, and `inspect: aw runs status run-abcdef1234 | aw runs show run-abcdef1234`, and do not contain `0 steps: 0 steps`.
- `test_progressed_ledger_run_reconstructs_started_and_attempted_steps_across_modes`: appends `kind="run"`, `step_started` (`S-01`), `step_attempt` (`S-01` -> `performed`), and `step_started` (`S-02`), verifies `load_run_summary` reconstructs `S-01` (`performed`, `attempts=1`) and `S-02` (`running`, `attempts=0`) with `counts == {"performed": 1, "running": 1}` and `ledger["run_state"] == "running"`, and verifies `_run_viewer` in human, `--json`, and `--agent` modes surfaces the `ledger` dict with zero `artifact_discrepancies`.
- `test_explicit_path_resolution_and_filters_for_ledger_runs`: verifies `resolve_target_runs_detailed` resolves both `<runs>/run-abcdef1234` and `<runs>/run-abcdef1234/ledger.jsonl` (while rejecting `analytics/` paths), and verifies `--active`, `--status running`, `--status failed`, and `--failed` filter inclusion/exclusion on ledger runs.
- `test_corrupt_or_non_ledger_file_fails_closed_as_unreadable_state`: verifies a `run-*` directory containing only invalid JSON or a non-ledger JSONL file (`{"event": "not_a_ledger"}`) in `ledger.jsonl` returns `None` from `load_run_summary` and is reported in `excluded_runs` with `reason == "unreadable_state"`, never as a `0 steps: 0 steps` driver run.

## Deferred / out of scope (with reason)

- **`aw run init` CLI leaf**: Owned by sibling plan `v47z9u` (Order 03 in Set `runledger`, from backlog `hegwri`), which this plan declares in `- Item-Dependencies: executed:v47z9u`.
- **Amending spec `25kzda` Section 1.2 Step 8 and Section 5.1**: Owned by sibling plan `9epp40` (Order 04 in Set `runledger`, from backlog `66ls4r`).
- **Adding `aw runs` ledger leaves to `LIVE_SAFE_LEAVES`**: Owned by sibling plan `g5s94t` (Order 05 in Set `runledger`, from backlog `a4tjxc`).
- **Writing `requirement_set` on `aw run init` and adding `aw run verify`**: Owned by sibling plan `um0twl` (Order 05 in Set `runledger`, from backlog `8l1hgw`).
- **Persisting `wf.json` beside `ledger.jsonl` so subsequent `aw run` leaves need not repeat `--workflow`**: Tracked by open backlog item `sflov4`.

## Scope check

- Over-scope: none. Every change serves classifying and rendering ledger-only run directories in `aw runs` (`nf84rt`).
- Under-scope: none. Both human and machine (`--json`, `--agent`) viewer outputs, explicit path resolution, filter flags (`--active`, `--status`, `--failed`), and `step_started` reconstruction in `_reconstruct_workflow_from_ledger` are covered.

## Required tests / validation

- Targeted test suite: `python3 -m pytest tests/test_run_viewer.py tests/test_run_recovery_cli.py`
- Full test suite: `python3 -m pytest`
- Leak sanitizer and repository checks: `aw ipd lint`, `aw check`, `aw sanitize --agent`

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` documents `aw runs` as the run viewer and `RunSummary.ledger` is an additive optional field (`None` for all driver runs); spec `25kzda` ledger-scope amendments are owned by sibling plan `9epp40`.

## Open questions

### OQ-01: Should `aw runs` classify and render a ledger-only directory with the ledger model or skip it in `discover_run_dirs`?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Resolved in favor of classifying a ledger-only directory (`not state_file.is_file() and not report_file.is_file() and (run_dir / "ledger.jsonl").is_file()`) in `load_run_summary` and rendering it with the ledger model in `format_run_human` (including the `aw runs status <run_id> | aw runs show <run_id>` signpost). Skipping ledger directories in `discover_run_dirs` would make bare `aw runs` print `no matching runs found` (and `aw runs <run-id>` exit 2 with `no run matched target`) right after an operator runs `aw run init`, hiding the newly created run directory under `state_root(repo)`. Reconstructing the ledger state in `load_run_summary` while keeping `RunSummary.steps = []` displays accurate ledger metadata and step state in `aw runs` without triggering false `audit_step_artifact` (`missing_entirely`) findings on workflow step IDs (`S-01`).

### OQ-02: Does accepting `ledger.jsonl` in `resolve_target_runs_detailed` affect `run_cli._classify_absent_target`'s `aw runs repair` signpost?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Resolved from `agent_workflows/run_cli.py` (`def _classify_absent_target`): `_classify_absent_target` is invoked only when `resolve_ledger_path` returns `None` (no `ledger.jsonl` exists) and explicitly filters the directories returned by `resolve_target_runs_detailed` with `if (run_dir / "state.json").is_file(): return TARGET_DRIVER_RUN`. Accepting `ledger.jsonl` in `resolve_target_runs_detailed` therefore has zero effect on `_classify_absent_target` or `TestLedgerResolutionAndWrongFormatVerdict` in `tests/test_run_recovery_cli.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/run_cli.py` showing `_reconstruct_workflow_from_ledger` matching `kind in ("step_started", "step_attempt")`, plus `python3 -m pytest tests/test_run_viewer.py -k test_progressed_ledger_run_reconstructs_started_and_attempted_steps_across_modes` output showing a `step_started`-only step reconstructed with `state == "running"`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing `ledger: dict[str, Any] | None = None` on `RunSummary`, `_load_ledger_run_summary`, and the `ledger_file.is_file()` branch in `load_run_summary`, plus `python3 -m pytest tests/test_run_viewer.py -k "test_header_only_ledger_run_renders_ledger_model_not_zero_driver_steps or test_corrupt_or_non_ledger_file_fails_closed_as_unreadable_state"` output passing.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing `resolve_target_runs_detailed` accepting `ledger.jsonl` and `run_viewer_cli` filter predicates (`status_filter`, `failed_only`, `active_only`) branching on `summary.ledger is not None`, plus `python3 -m pytest tests/test_run_viewer.py tests/test_run_recovery_cli.py -k "test_explicit_path_resolution_and_filters_for_ledger_runs or TestLedgerResolutionAndWrongFormatVerdict"` output passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing the `if run.ledger is not None:` block in `format_run_human` rendering `[ledger]`, `ledger: state=...`, step lines or `ledger steps: 0 recorded`, and `inspect: aw runs status ... | aw runs show ...`, plus `python3 -m pytest tests/test_run_viewer.py -k LedgerRunViewerTests` output passing.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Pasted runner output of `python3 -m pytest tests/test_run_viewer.py tests/test_run_recovery_cli.py` and `python3 -m pytest` showing all tests in `LedgerRunViewerTests` and the full suite passing.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored at `- Status: to-review` from backlog item `nf84rt` with `- Item-Dependencies: executed:v47z9u`. Once reviewed and approved, execute `E-01` through `E-05`, record concrete observed evidence in `V-01` through `V-05`, verify `aw ipd lint` and `python3 -m pytest`, and finalize via `aw ipd finalize 3a3hh9` (or `aw finish 3a3hh9`).
