# IPD: Classify and render ledger-only run directories in aw runs viewer

- Date: 2026-10-14
- Kind: child
- Concern: `run_viewer.discover_run_dirs` admits every `run-*` directory under `state_root(repo)`, and `run_viewer.load_run_summary` treats any directory lacking `state.json` and `execution-report.md` as an empty driver run (`steps=[]`, `counts={}`), causing `format_run_human` (`aw runs`) to render a ledger-only run directory created by `aw run init` (plan `v47z9u`, writing `state_root(repo)/<run-id>/ledger.jsonl`) as a driver run with `0 steps: 0 steps`. In addition, `run_cli._reconstruct_workflow_from_ledger` collects step IDs only from `step_attempt` records and ignores `step_started` records, `resolve_target_runs_detailed` rejects explicit directory or file paths to a ledger-only run, and `run_viewer_cli` filters (`--active`, `--status`, `--failed`) inspect only `summary.steps` (`StepSummary` rows). Backlog `nf84rt`.
- Scope: (1) In `agent_workflows/run_cli.py`, widen `_reconstruct_workflow_from_ledger` to recover step IDs from `kind in ("step_started", "step_attempt")` records so started-but-not-yet-attempted steps surface as `running` in `RunEngine.reconstruct_state()`. This helper is SHARED: `run_cli._build_engine` calls it for every ledger leaf invoked without `--workflow`, so the widening also changes those leaves (F-05), and those changes are named, intended, and pinned by tests here. (2) In `agent_workflows/run_viewer.py`, add `ledger: dict[str, Any] | None = None` to `RunSummary`, add `_load_ledger_run_summary(run_dir, ledger_file)` verifying and reconstructing `ledger.jsonl` via `RunLedgerStore.read_records(verify=True)` and `RunEngine.reconstruct_state()` (returning `None` on corrupt/invalid/empty ledgers so `run_viewer_cli` records `unreadable_state`; no driver PID inference, F-07), and branch `load_run_summary` to call `_load_ledger_run_summary` when neither `state.json` nor `execution-report.md` is present and `(run_dir / "ledger.jsonl").is_file()`. (3) In `agent_workflows/run_viewer.py`, extend `resolve_target_runs_detailed` to resolve explicit directory paths containing `ledger.jsonl` and explicit file paths named `ledger.jsonl`. (4) Update `run_viewer_cli` filter predicates (`active_only`, `status_filter`, `failed_only`) to evaluate `summary.ledger` and `summary.counts` on ledger runs. (5) Update `format_run_human` to render ledger-only runs with the ledger model (`[ledger]`, `ledger: state=..., records=..., workflow=...`, step tally and per-step lines or `ledger steps: 0 recorded`, and the signpost `inspect: aw runs status <run_id> | aw runs show <run_id>`) instead of `0 steps: 0 steps`. (6) In `tests/test_run_viewer.py`, add `LedgerRunViewerTests` covering header-only and progressed ledger runs across human, `--json`, and `--agent` outputs, explicit path resolution, filter flags, and fail-closed `unreadable_state` exclusion. (7) In `tests/test_run_recovery_cli.py`, pin the ledger-leaf behavior the shared-helper widening changes (F-05). (8) One CHANGELOG line. OUT: adding `aw run init` itself (`v47z9u`), amending spec `25kzda` (`9epp40`), adding ledger leaves to `LIVE_SAFE_LEAVES` (`g5s94t`), writing `requirement_set` on init or adding `aw run verify` (`um0twl`), persisting `workflow.json` beside the ledger (`sflov4` / `o34rb3`), and widening explicit-path resolution for `execution-report.md`-only driver directories (not traceable to `nf84rt`; bare-name resolution already matches them).
- Scope-Paths: agent_workflows/run_viewer.py, agent_workflows/run_cli.py, tests/test_run_viewer.py, tests/test_run_recovery_cli.py, CHANGELOG.md
- Item-Dependencies: executed:v47z9u
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: nf84rt
- From-Spec: 25kzda
- Set: runledger
- Order: 6
- Highest E allocated: 09
- Author: antigravity
- Id: 3a3hh9
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010
- 2026-10-14 to-review (aw set): authored review-ready IPD from backlog nf84rt

- 2026-10-14 draft (antigravity): created.

## Goal

Classify ledger-only run directories (`ledger.jsonl` present without `state.json` or `execution-report.md`, as created by `aw run init` in plan `v47z9u`) inside `agent_workflows/run_viewer.py` and reconstruct and render them using the ledger run model (`RunLedgerStore` + `RunEngine.reconstruct_state` + `aw runs status` / `aw runs show` signpost) so `aw runs` never misreports a ledger run as a driver run with `0 steps: 0 steps`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reconstruct and classify ledger-only run directories

- [ ] E-06 REPRODUCE at execution HEAD before any edit, in a scratch repo created under `tempfile.TemporaryDirectory()` that CONTAINS `.aw/records/` (without it `runner_shared.state_root` resolves to the home-scoped projects tree, F-06). Append a conformant `kind: "run"` header through `RunLedgerStore.append` at `state_root(root) / "run-abcdef1234" / "ledger.jsonl"` (no `aw run init` needed; that is `v47z9u`'s), then paste: (a) `aw runs --dir <root>` printing `run-abcdef1234` followed by `  0 steps: 0 steps`; (b) `resolve_target_runs_detailed([<dir>], root)` and `resolve_target_runs_detailed([<dir>/ledger.jsonl], root)` each returning the token as UNRESOLVED; (c) after appending `step_started` for `S-01`, `aw runs status <ledger path> --json` showing `"steps": {}` and `aw run record <ledger path> --step S-01 --state performed --json` exiting 2 with `unknown step 'S-01'`. If any of these has changed, stop and report the plan as overtaken with the contradicting output.
  - Depends on: none
  - Expected outcome: the pasted outputs above, each matching F-01, F-02, F-03 and F-05 as measured at review.
  - Execution state: pending

- [ ] E-01 In `agent_workflows/run_cli.py`, update `_reconstruct_workflow_from_ledger` so the step-extraction branch matches `elif kind in ("step_started", "step_attempt"):` instead of only `elif kind == "step_attempt":`, and update its docstring to say step ids are recovered from `step_started` and `step_attempt` records.
  - Depends on: E-06
  - Expected outcome: A ledger containing a `step_started` record (written by `aw run start` before any `step_attempt` record) includes that step ID in the reconstructed workflow skeleton, and `RunEngine.reconstruct_state()` reports the step with `state == "running"`, `attempts == 0` and `run_state == "running"`. Because `_build_engine` uses this helper for every ledger leaf invoked without `--workflow`, the following ledger-leaf changes are EXPECTED and are pinned by E-08 (measured at review by simulating the widening, F-05): `aw runs status` lists the started step as `running`; `aw runs resume` exits 3 (`EXIT_BLOCKED`, `condition: unknown_outcome`) instead of exit 0 with `unknown_outcome_steps: []`; `aw run record --step S-01 --state performed` exits 0 instead of exit 2 `unknown step`.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/run_viewer.py`, add `ledger: dict[str, Any] | None = None` to `RunSummary` (after `runtime_str`), implement `_load_ledger_run_summary(run_dir: Path, ledger_file: Path) -> RunSummary | None`, and branch `load_run_summary` to delegate to `_load_ledger_run_summary` when `not state_file.is_file() and not report_file.is_file() and (run_dir / "ledger.jsonl").is_file()`.
  - Depends on: E-01
  - Expected outcome: For a ledger-only run directory with a valid hash-chained `ledger.jsonl`, `load_run_summary` verifies the chain via `RunLedgerStore(ledger_file).read_records(verify=True)` (a pure read: it creates no `ledger.jsonl.lock` and writes nothing), reconstructs `RunStateSnapshot` via `run_cli._reconstruct_workflow_from_ledger` and `run_engine.RunEngine.reconstruct_state`, and returns a `RunSummary` with `ledger` populated (`run_id`, `run_state`, `workflow_id`, `workflow_digest`, `requirement_digest`, `record_count`, `steps`, `approvals`, `verifier_decisions`, `cancellation_reason`), `created_at` and `updated_at` taken from the first and last record `timestamp` fields, `runtime_seconds`/`runtime_str` computed from those two timestamps, `pid=None`, `pid_state=None`, `is_live=False` (a ledger run has no driver process; do NOT call `inspect_run_pid_and_runtime`, whose run-name PID fallback reads `run-12345678` as PID 12345678, F-07), `counts` tallied by ledger step state, and `steps=[]`. For a wrong-format (`NotALedgerError`), corrupt (`LedgerCorruption` subclasses, including `UnparseableLineError`), or empty (zero records) `ledger.jsonl`, `_load_ledger_run_summary` returns `None` so `run_viewer_cli` records `"unreadable_state"` in `excluded`. A driver directory holding `state.json` and also a `ledger.jsonl` is still loaded by the driver path, unchanged.
  - Execution state: pending

### Task group 2: Viewer target resolution, filtering, and human/machine rendering

- [ ] E-03 In `agent_workflows/run_viewer.py`, update `resolve_target_runs_detailed` to accept explicit directory targets containing `ledger.jsonl` (beside the existing `state.json` test) and explicit file targets named `ledger.jsonl` (beside `state.json`, `events.jsonl`, `execution-report.md`), keeping both `path_is_within_analytics` refusals.
  - Depends on: E-02
  - Expected outcome: Passing `<runs-root>/run-<hex>` or `<runs-root>/run-<hex>/ledger.jsonl` to `resolve_target_runs_detailed` resolves to `<runs-root>/run-<hex>`, a `ledger.jsonl` under the analytics tree is still unresolved, and `run_cli._classify_absent_target` is unaffected because it additionally requires `(run_dir / "state.json").is_file()` (OQ-02): `tests/test_run_recovery_cli.py` `TestLedgerResolutionAndWrongFormatVerdict` passes unchanged.
  - Execution state: pending

- [ ] E-07 In `agent_workflows/run_viewer.py` `run_viewer_cli`, update the `status_filter`, `failed_only`, and `active_only` checks to evaluate `summary.ledger["run_state"]` and `summary.counts` when `summary.ledger is not None`, leaving the driver-run branches byte-for-byte equivalent. The `active_only` `state.json` pre-filter is untouched (a ledger directory has no `state.json`, so it falls through to the full load).
  - Depends on: E-02
  - Expected outcome: `--active` includes a ledger run whose `run_state` is `running` or that has a `running` step and excludes a `pending` one; `--status running` includes the progressed run and `--status failed` excludes it; `--failed` includes a ledger run with a `failed` step or run state and excludes one without; every existing filter test in `tests/test_run_viewer.py` (including `FilterExclusionReportingTests`) still passes.
  - Execution state: pending

- [ ] E-04 In `agent_workflows/run_viewer.py`, update `format_run_human` so that when `run.ledger is not None`, it renders the ledger model instead of the driver-run `0 steps: 0 steps` tally.
  - Depends on: E-02
  - Expected outcome: For a ledger-only `RunSummary`, `format_run_human` emits `<run_id>  [ledger]` on the header line, the timing line from the ledger timestamps, `  ledger: state=<styled_run_state>, records=<record_count>, workflow=<workflow_id>` (styling `<run_state>` with `_resolve_ledger_status`), either `  <N> ledger steps: <tally>` with indented `    <step_id>: <styled_state> (attempts=<attempts>)` lines or `  ledger steps: 0 recorded` when `run.ledger["steps"]` is empty, optional `  cancellation: <reason>` when cancelled, and `  inspect: aw runs status <run_id> | aw runs show <run_id>`, without emitting `0 steps: 0 steps` and with no ANSI escape under `Term(color=False)`. Other human paths that iterate `summary.steps` (`format_multi_run_summary`, `--summary-only`, `--latest-only`, `--issues`) are left as they are: a ledger run contributes zero driver steps to them, which is true, and this plan does not redesign those aggregates.
  - Execution state: pending

### Task group 3: Unit and CLI integration tests

- [ ] E-05 In `tests/test_run_viewer.py`, add `LedgerRunViewerTests(TestCase)` driving `load_run_summary`, `format_run_human`, `resolve_target_runs_detailed`, and the real `aw runs` entry point (`_run_viewer`) over ledgers built with `RunLedgerStore.append` in a `tempfile.TemporaryDirectory()` root that contains `.aw/records/`, asserting on returned values, rendered output and exit codes, never on source text. Cases (names are non-binding pointers): (a) header-only run renders the ledger model in human mode, contains `[ledger]`, `ledger: state=pending, records=1`, `ledger steps: 0 recorded`, the `inspect:` signpost, and NOT `0 steps: 0 steps`, for both bare `aw runs` and `aw runs run-abcdef1234`; (b) progressed run (`run`, `step_started` S-01, `step_attempt` S-01 performed, `step_started` S-02) reconstructs S-01 `performed` attempts 1 and S-02 `running` attempts 0, `counts == {"performed": 1, "running": 1}`, `run_state == "running"`, and `--json` and `--agent` each carry the `ledger` dict and no `artifact_discrepancies`; (c) explicit directory and `ledger.jsonl` path resolution, and the `--active` / `--status running` / `--status failed` / `--failed` inclusion and exclusion from E-07; (d) a `run-*` directory whose `ledger.jsonl` is invalid JSON, non-ledger JSONL (`{"event": "not_a_ledger"}`), or empty returns `None` from `load_run_summary` and appears in `--json` `excluded_runs` with `reason == "unreadable_state"`, never as a `0 steps` row; (e) a ledger run directory named `run-12345678` reports `pid` as `None` (F-07); (f) loading a summary leaves the run directory listing unchanged (no `ledger.jsonl.lock` created). Show (a) and (d) failing on the pre-change code (the measured `0 steps: 0 steps` row and the non-`None` summary for an empty `ledger.jsonl`).
  - Depends on: E-01, E-02, E-03, E-07, E-04
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_run_viewer.py -k LedgerRunViewerTests` shows every case passing, and (a) and (d) are shown failing on the base commit.
  - Execution state: pending

- [ ] E-08 In `tests/test_run_recovery_cli.py`, add CLI-level coverage for the ledger-leaf behavior E-01 changes, driving `run_cli` over a ledger with a `run` header and one `step_started` record and NO `--workflow`: `aw runs status --json` lists the step as `running`; `aw runs resume --json` exits `EXIT_BLOCKED` (3) with `condition == "unknown_outcome"` and the step in `unknown_outcome_steps`; `aw run record --step S-01 --state performed --json` exits `EXIT_OK` (0). Place it in the existing class whose seeds it shares (`TestRunCliSubcommands` or `TestResumeCancelCrash`), not a new module.
  - Depends on: E-01
  - Expected outcome: the new test passes after E-01 and is shown failing on the base commit (`resume` exit 0, `record` exit 2), and `python3 -m pytest -o addopts="" tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py` passes.
  - Execution state: pending

- [ ] E-09 Add one CHANGELOG line under the top pending release describing that `aw runs` now shows a ledger-only run (from `aw run init`) with its ledger state and a pointer to `aw runs status`, and that ledger leaves run without `--workflow` now see a started-but-unrecorded step (no em or en dashes). Then run the bare suite.
  - Depends on: E-05, E-08
  - Expected outcome: the CHANGELOG diff, and a bare `python3 -m pytest` summary line with zero failures.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Two run models share `state_root(repo)` (`utb2qr`, `rdjka2`, `v47z9u`, `d91i3e`)**: Decision record `utb2qr` and executed plan `rdjka2` established that `aw oc run` / `aw agy run` write driver runs (`state.json`, `events.jsonl`, `execution-report.md`, `outcomes/*.json`) and do not write `ledger.jsonl`, while `aw run init` (plan `v47z9u`) initializes standalone hash-chained workflow ledgers at `state_root(repo)/<run-id>/ledger.jsonl`. Executed plan `d91i3e` added the driver-run signpost in `run_cli._classify_absent_target` (`TARGET_LEDGER_RUN`, `TARGET_DRIVER_RUN`, `TARGET_UNKNOWN`) when a ledger verb (`aw runs show|status|...`) is pointed at a driver run; this plan (`3a3hh9`, from backlog `nf84rt`) closes the mirror direction when the viewer (`aw runs`) encounters a ledger-only directory under `state_root(repo)`.
- **Read surfaces never mutate (`GUIDING_PRINCIPLES.md` P10, `fduoj4`)**: `run_viewer.load_run_summary` and `run_viewer.run_viewer_cli` are strictly read-only inspection paths and must never write to or lock `ledger.jsonl`; `RunLedgerStore(ledger_file).read_records(verify=True)` reads and verifies the hash chain without acquiring `writer_lock` or mutating disk state.
- **Artifact audit scope (`run_viewer.audit_step_artifact`, `6ltz1y`, `zexed1`)**: `run_viewer_cli` iterates `for s in summaries: for st in s.steps: audit_step_artifact(st, ...)` to check `.aw/records/` artifact locations and statuses by `id6`. Workflow steps inside `ledger.jsonl` carry workflow step IDs (`S-01`, `S-02` per `run_ledger_schema._STEP_ID_RE`), not repository artifact `id6`s. Keeping `RunSummary.steps = []` for ledger-only runs and storing the ledger's step map under `RunSummary.ledger["steps"]` prevents `audit_step_artifact` from falsely flagging workflow step IDs as `missing_entirely` (`CLASS_MISSING`) in `--issues`, `--json`, and the human discrepancy table.
- **Section 7.3 run-ledger status styling (`run_viewer._resolve_ledger_status`)**: `agent_workflows/run_viewer.py` already defines `_resolve_ledger_status(token)` (`return _LS.resolve_status(token, "run_ledger")`) at `_resolve_ledger_status` for styling run-ledger lifecycle states (`pending`, `runnable`, `running`, `performed`, `verified`, `complete`, `blocked`, `failed`, `cancelled`, `interrupted`, `abandoned`, `unknown_outcome`).
- **Live-runs test isolation (`tests/test_run_viewer.py` `_forbid_live_runs_reads`)**: `tests/test_run_viewer.py` installs a `sys.addaudithook` fixture forbidding any test from reading the repository's real `.aw/records/runs/` tree; all tests in `tests/test_run_viewer.py` must construct temporary roots via `tempfile.TemporaryDirectory()`, and each root must contain `.aw/records/` so `runner_shared.state_root` resolves inside it (F-06).
- **Suite and tests (repo-local AGENTS.md, `GUIDING_PRINCIPLES.md` P16)**: run the suite bare as `python3 -m pytest`; narrowed runs clear defaults with `-o addopts=""`. Tests drive behavior and never read production source.
- **Commit and lifecycle**: commit through `aw commit 3a3hh9 -- <paths>`, never push; CHANGELOG prose carries no em or en dashes.

## Findings

| # | Location | Observation | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/run_viewer.py` `discover_run_dirs` (`def discover_run_dirs`) and `load_run_summary` (`def load_run_summary`) | `discover_run_dirs` admits every `run-*` subdirectory under `state_root(repo_root)`. In `load_run_summary`, when `state_file.is_file()` (`state.json`) and `report_file.is_file()` (`execution-report.md`) are both `False`, the function falls through and returns `RunSummary(run_id=run_dir.name, run_dir=run_dir, steps=[], counts={}, ...)` without checking `(run_dir / "ledger.jsonl").is_file()`. | In `format_run_human` (`tally_str = ", ".join(tally_parts) if tally_parts else f"{len(run.steps)} steps"`), a ledger-only run directory created by `aw run init` renders as `run-abcdef1234` followed by `  0 steps: 0 steps`. |
| F-02 | `agent_workflows/run_cli.py` `_reconstruct_workflow_from_ledger` (`def _reconstruct_workflow_from_ledger`) | `_reconstruct_workflow_from_ledger` recovers step IDs only from `elif kind == "step_attempt":` records, ignoring `kind == "step_started"` records (`RECORD_KINDS_V2_ONLY`). Meanwhile, `RunEngine.reconstruct_state` (`def reconstruct_state` in `agent_workflows/run_engine.py`) only records a `step_started` transition (`step_states[sid] = run_state.STATE_RUNNING`) when `sid in self._workflow_steps`. | If a step has been started (`aw run start <target> --step S-01 --workflow wf.json`) and has not yet recorded a `step_attempt`, reconstructing state from the ledger alone omits `S-01` from `_workflow_steps` and therefore omits `S-01` from `snapshot.steps`. |
| F-03 | `agent_workflows/run_viewer.py` `resolve_target_runs_detailed` (`def resolve_target_runs_detailed`) | For explicit path targets, `resolve_target_runs_detailed` checks `if p.is_dir() and (p / "state.json").is_file():` and `elif p.is_file() and p.name in ("state.json", "events.jsonl", "execution-report.md"):`. Meanwhile, `run_cli._classify_absent_target` (`def _classify_absent_target`) calls `resolve_target_runs_detailed` and then checks `if (run_dir / "state.json").is_file(): return TARGET_DRIVER_RUN`. | Passing an explicit directory path `<runs>/run-abcdef1234` or file path `<runs>/run-abcdef1234/ledger.jsonl` to `aw runs` fails with `no run matched target` even though bare `aw runs run-abcdef1234` matches by directory name. Extending the explicit-path branch to accept `ledger.jsonl` fixes explicit path targeting without altering `_classify_absent_target` (review probe at HEAD `094f7a617`: both explicit tokens came back unresolved while the bare name resolved). |
| F-04 | `agent_workflows/run_viewer.py` `run_viewer_cli` (`def run_viewer_cli`) | In `run_viewer_cli`, the `active_only` (`--active`), `status_filter` (`--status`), and `failed_only` (`--failed`) filters inspect only `summary.steps` (`StepSummary` entries). | Because ledger-only runs keep `summary.steps = []` (to avoid running `audit_step_artifact` against workflow step IDs like `S-01`), `--active`, `--status`, and `--failed` would unconditionally exclude every ledger-only run unless those predicates also check `summary.ledger` and `summary.counts`. |
| F-05 | `agent_workflows/run_cli.py` `_build_engine` (`workflow = _reconstruct_workflow_from_ledger(records)`) | `_reconstruct_workflow_from_ledger` is not viewer-only: `_build_engine` calls it for EVERY ledger leaf invoked without `--workflow`. Review probe at HEAD `094f7a617`, ledger = `run` header + `step_started` S-01, no `--workflow`: `aw runs status --json` exit 1 with `"steps": {}`; `aw runs resume --json` exit 0 with `unknown_outcome_steps: []`; `aw run record --step S-01 --state performed --json` exit 2 `unknown step 'S-01'`. The same three with the widening simulated (monkeypatched helper): `status` lists `S-01: running`; `resume` exit 3 `condition: unknown_outcome`; `record` exit 0. With the widening simulated as a pytest plugin, `tests/test_run_recovery_cli.py`, `tests/test_run_cli_declarations.py` and `tests/test_run_viewer.py` still passed (106 passed), so nothing pins either behavior. | E-01 is a cross-surface behavior change. The new behavior is the correct one (a started step with no recorded outcome IS an unknown outcome, `run_recovery.detect_unknown_outcomes`; the old `resume` exit 0 silently hid it), so it is kept, but it must be declared and pinned (E-08), not left as an unmentioned side effect. |
| F-06 | `agent_workflows/runner_shared.py` `state_root` | `state_root` falls back to `<repo>/.aw/records/runs` only when `<repo>/.aw/records` exists; otherwise it resolves under the home-scoped projects tree. Review probe: a bare `tempfile.mkdtemp()` root resolved OUTSIDE the temp dir, under `$HOME`. | Tests that build a ledger at `state_root(root)` without first creating `<root>/.aw/records/` would write outside the temp root. E-05 and E-06 require `.aw/records/`. |
| F-07 | `agent_workflows/run_viewer.py` `inspect_run_pid_and_runtime` (`re.search(r"-(\d+)$", run_dir.name)`) | When no `driver.lock` exists, the PID falls back to the trailing digits of the run directory name. A ledger run id is `run-<hex>` (`run_ledger_schema._RUN_ID_RE`), which can be all digits. Review probe: `inspect_run_pid_and_runtime(Path(".../run-12345678"), ...)` returned `pid=12345678`. | The draft E-02 called this helper for ledger runs, which would print `pid: 12345678 [exited]` (or `live` if that PID happens to exist) for a run that has no process. E-02 now sets `pid`/`pid_state` to `None` and computes runtime from the ledger timestamps. |
| F-08 | `agent_workflows/run_ledger_store.py` `RunLedgerStore.read_records` | `read_records` returns `[]` for an empty file, raises `NotALedgerError` for non-ledger JSONL and `UnparseableLineError` (a `LedgerCorruption`) for invalid JSON, and acquires no lock. Review probe: a pure read created no `ledger.jsonl.lock`. Today an empty `ledger.jsonl` alone yields a non-`None` summary (`load_run_summary(...) is None` was `False`). | Confirms the fail-closed and read-only design of E-02 is reachable with the existing store, and gives E-05 (d) a pre-change failure to show. |

## Proposed changes (ordered, validatable)

### 0. Reproduce at execution HEAD (`E-06`)

Run the three probes in E-06 and paste their output before editing anything.

### 1. Recover `step_started` steps in `run_cli._reconstruct_workflow_from_ledger` (`E-01`)

In `agent_workflows/run_cli.py` inside `_reconstruct_workflow_from_ledger` (`elif kind == "step_attempt":`), widen the condition to:

```python
        elif kind in ("step_started", "step_attempt"):
            sid = str(rec.get("step", ""))
            if sid and sid not in seen_steps:
                seen_steps.add(sid)
                step_ids.append(sid)
```

This is the shared helper behind `_build_engine`, so the ledger-leaf changes listed in E-01's expected outcome follow; E-08 pins them.

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
       except (_ledger_store.NotALedgerError, _ledger_store.LedgerCorruption, OSError):
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
       except (_ledger_store.NotALedgerError, _ledger_store.LedgerCorruption, OSError):
           return None

       ledger_payload = _run_cli._snapshot_payload(snapshot)
       ledger_payload["workflow_digest"] = str(run_rec.get("workflow_digest") or "")
       ledger_payload["requirement_digest"] = str(
           run_rec.get("requirement_digest") or ""
       )

       counts: dict[str, int] = defaultdict(int)
       for st in snapshot.steps.values():
           counts[st.state] += 1

       # A ledger run has no driver process, so `inspect_run_pid_and_runtime` is deliberately NOT
       # called: its run-name fallback would read `run-12345678` as PID 12345678 (F-07). Runtime is
       # the span between the first and last ledger record.
       runtime_seconds: float | None = None
       runtime_str: str | None = None
       start_dt = RunSummary(run_id=run_id, run_dir=run_dir, created_at=created_at).timestamp_dt
       end_dt = RunSummary(run_id=run_id, run_dir=run_dir, created_at=updated_at).timestamp_dt
       if start_dt and end_dt:
           runtime_seconds = max(0.0, (end_dt - start_dt).total_seconds())
           runtime_str = format_duration(runtime_seconds)
       return RunSummary(
           run_id=run_id,
           run_dir=run_dir,
           created_at=created_at,
           updated_at=updated_at,
           steps=[],
           counts=dict(counts),
           pid=None,
           pid_state=None,
           is_live=False,
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

### 3. Update `resolve_target_runs_detailed` (`E-03`) and the `run_viewer_cli` filter predicates (`E-07`)

1. (`E-03`) In `agent_workflows/run_viewer.py` inside `resolve_target_runs_detailed` (`if p.is_dir() and (p / "state.json").is_file():`), widen ONLY the two membership tests and keep the existing bodies (the `path_is_within_analytics` refusal, the `seen`/`resolved` bookkeeping, and `continue`) unchanged. The draft's `matched`/`target_matched` names do not exist in this function:
   ```python
        if p.is_dir() and (
            (p / "state.json").is_file() or (p / "ledger.jsonl").is_file()
        ):
            ...  # existing body unchanged
        elif (
            p.is_file()
            and p.parent.is_dir()
            and p.name
            in ("state.json", "events.jsonl", "execution-report.md", "ledger.jsonl")
        ):
            ...  # existing body unchanged
   ```
2. (`E-07`) In `run_viewer_cli` (`for r_dir in run_dirs:`), update `status_filter`, `failed_only`, and `active_only` so ledger-only runs (`summary.ledger is not None`) are evaluated against `summary.ledger["run_state"]` and `summary.counts`:
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

In `tests/test_run_viewer.py`, add `LedgerRunViewerTests(TestCase)`. Every case builds its root with `tempfile.TemporaryDirectory()`, creates `<root>/.aw/records/` first (F-06), and writes ledgers through `RunLedgerStore.append`. Test names below are non-binding pointers; the binding bar is the behavior each asserts (E-05 (a) to (f)):
- header-only run: `load_run_summary` returns `ledger["run_state"] == "pending"`, `ledger["record_count"] == 1`, `ledger["steps"] == {}`, `pid is None`; `format_run_human` and CLI `_run_viewer(root, [])` / `_run_viewer(root, ["run-abcdef1234"])` exit 0, include `[ledger]`, `ledger: state=pending, records=1`, `ledger steps: 0 recorded`, and `inspect: aw runs status run-abcdef1234 | aw runs show run-abcdef1234`, and do not contain `0 steps: 0 steps`.
- progressed run: appends `kind="run"`, `step_started` (`S-01`), `step_attempt` (`S-01` -> `performed`), and `step_started` (`S-02`); `load_run_summary` reconstructs `S-01` (`performed`, `attempts=1`) and `S-02` (`running`, `attempts=0`) with `counts == {"performed": 1, "running": 1}` and `ledger["run_state"] == "running"`; `_run_viewer` in human, `--json`, and `--agent` modes surfaces the `ledger` dict with no `artifact_discrepancies`.
- explicit paths and filters: `resolve_target_runs_detailed` resolves both `<runs>/run-abcdef1234` and `<runs>/run-abcdef1234/ledger.jsonl` (and still refuses an analytics-tree path); `--active`, `--status running`, `--status failed`, and `--failed` include or exclude ledger runs as E-07 states (a header-only `pending` run is the negative case for `--active`, and a run with a `failed` `step_attempt` is the positive case for `--failed`).
- fail-closed: a `run-*` directory whose `ledger.jsonl` is invalid JSON, non-ledger JSONL (`{"event": "not_a_ledger"}`), or empty returns `None` from `load_run_summary` and is reported in `--json` `excluded_runs` with `reason == "unreadable_state"`, never as a `0 steps: 0 steps` row.
- no phantom PID: a ledger run directory named `run-12345678` loads with `pid is None` and its human output contains no `pid:` line.
- read-only: the run directory listing is identical before and after `load_run_summary` (no `ledger.jsonl.lock` is created).

### 6. Pin the ledger-leaf behavior the shared helper changes (`E-08`)

In `tests/test_run_recovery_cli.py`, in the existing class whose seeds fit (`TestRunCliSubcommands` or `TestResumeCancelCrash`), add one test over a ledger holding a `run` header and one `step_started` record for `S-01`, invoked WITHOUT `--workflow`: `runs status --json` shows `S-01` `running`; `runs resume --json` exits `run_cli.EXIT_BLOCKED` with `condition == "unknown_outcome"` and `"S-01"` in `unknown_outcome_steps`; `run record --step S-01 --state performed --json` exits `run_cli.EXIT_OK`. Show it failing on the base commit.

### 7. CHANGELOG and bare suite (`E-09`)

One line under the top pending release section of `CHANGELOG.md`, then `python3 -m pytest` bare.

## Deferred / out of scope (with reason)

- **`aw run init` CLI leaf**: Owned by sibling plan `v47z9u` (Order 03 in Set `runledger`, from backlog `hegwri`), which this plan declares in `- Item-Dependencies: executed:v47z9u`.
  - Carrier: v47z9u
- **Amending spec `25kzda` Section 1.2 Step 8 and Section 5.1**: Owned by sibling plan `9epp40` (Order 04 in Set `runledger`, from backlog `66ls4r`).
  - Carrier: 9epp40
  - Carrier-Evidence: .aw/records/plans/executed/20261014-runledger-04-9epp40-amend-spec-25kzda-1-2-step-8-and-5-1-to-scope-the-hash-chain.ipd.md
- **Adding `aw runs` ledger leaves to `LIVE_SAFE_LEAVES`**: Owned by sibling plan `g5s94t` (Order 05 in Set `runledger`, from backlog `a4tjxc`).
  - Carrier: g5s94t
- **Writing `requirement_set` on `aw run init` and adding `aw run verify`**: Owned by sibling plan `um0twl` (Order 05 in Set `runledger`, from backlog `8l1hgw`).
  - Carrier: um0twl
- **Persisting the workflow beside `ledger.jsonl` so subsequent `aw run` leaves need not repeat `--workflow`**: Owned by sibling plan `o34rb3` (Order 07 in Set `runledger`, from backlog `sflov4`, which is `graduated`, not open). `o34rb3` F-05 already assumes this plan classifies run directories by `state.json`, `execution-report.md` and `ledger.jsonl`, and a persisted `workflow.json` would not change that classification. When `o34rb3` lands, `_load_ledger_run_summary` could prefer the persisted workflow over the reconstructed skeleton; that is `o34rb3`'s to decide, not this plan's.
  - Carrier: o34rb3
- **Widening explicit DIRECTORY resolution to `execution-report.md`-only driver directories**: removed at review (PR-006). It is not traceable to `nf84rt`, it changes which DRIVER directories an explicit path reaches, and bare-name resolution already matches such directories by name.
  - Carrier-Declined: removed at review (PR-006)
- **Ledger rows in `format_multi_run_summary`, `--summary-only`, `--latest-only` and `--issues`**: those aggregates are defined over driver `StepSummary` rows. A ledger run contributes zero driver steps, which is true, so they stay unchanged (E-04). Redesigning them for a second run model is not what `nf84rt` asks for.
  - Carrier-Declined: defined over driver StepSummary rows; out of scope for nf84rt
- **Enveloping the non-empty `aw runs --agent` stream**: already tracked by backlog `4d3ynu` (`docs/cli-output-contract.md` Section 3.1); the new `ledger` key rides in the existing bare per-run object.
  - Carrier: 4d3ynu

## Scope check

- Over-scope: the draft's `execution-report.md` explicit-directory widening was removed (PR-006). Everything else serves classifying and rendering ledger-only run directories in `aw runs` (`nf84rt`).
- Under-scope: closed at review. The shared-helper side effect on the ledger leaves (F-05) is now declared in E-01 and pinned by E-08; a reproduce step (E-06), the PID guard (F-07), the scratch-root requirement (F-06), the CHANGELOG line and the bare suite (E-09) were added.

## Required tests / validation

- Reproduce at execution HEAD (E-06), pasted.
- New `LedgerRunViewerTests` in `tests/test_run_viewer.py` (E-05), with (a) and (d) shown failing on the base commit.
- New ledger-leaf test in `tests/test_run_recovery_cli.py` (E-08), shown failing on the base commit.
- Existing tests unchanged and passing: `tests/test_run_viewer.py` (all classes, including `FilterExclusionReportingTests` and `UnresolvableTargetRefusalTests`), `tests/test_run_recovery_cli.py` (including `TestLedgerResolutionAndWrongFormatVerdict`), `tests/test_run_cli_declarations.py`.
- Invariants and their tests: a ledger run never renders as `0 steps: 0 steps` (E-05 a); a damaged or foreign `ledger.jsonl` fails closed as `unreadable_state` (E-05 d); a ledger run never claims a driver PID (E-05 e); reading never writes (E-05 f); a started step with no recorded outcome is reported as unknown outcome by `resume` (E-08); driver-run filtering and rendering unchanged (existing suite).
- Bare suite `python3 -m pytest` (E-09).
- `aw ipd lint`, `aw sanitize --agent`.

## Spec / documentation sync

- Spec: none. No approved spec defines the `aw runs` viewer's per-run rendering or `RunSummary` fields; spec `25kzda` ledger-scope amendments are owned by sibling `9epp40`, and `25kzda` Section 6.2's ledger location is recorded by `v47z9u` E-06. No `.spec.md` is in Scope-Paths.
- Docs: `docs/cli-output-contract.md` Section 3.1 already describes the viewer's exits (`0`/`2`) and its bare `--json` / non-enveloped `--agent` shapes; this plan adds an optional `ledger` key (`null` for driver runs) inside that bare per-run object and changes no exit code of the viewer, so the contract text stays true. The ledger-leaf change (E-01/E-08) moves `aw runs resume` on a started-but-unrecorded step from `0` to `3`, which is already in the documented `resume` vocabulary (`3`: blocked, unknown outcome), so no doc edit is needed there either.
- CHANGELOG: one line (E-09).

## Open questions

### OQ-01: Should `aw runs` classify and render a ledger-only directory with the ledger model or skip it in `discover_run_dirs`?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Resolved in favor of classifying a ledger-only directory (`not state_file.is_file() and not report_file.is_file() and (run_dir / "ledger.jsonl").is_file()`) in `load_run_summary` and rendering it with the ledger model in `format_run_human` (including the `aw runs status <run_id> | aw runs show <run_id>` signpost). Skipping ledger directories in `discover_run_dirs` would make bare `aw runs` print `no matching runs found` (and `aw runs <run-id>` exit 2 with `no run matched target`) right after an operator runs `aw run init`, hiding the newly created run directory under `state_root(repo)`. Reconstructing the ledger state in `load_run_summary` while keeping `RunSummary.steps = []` displays accurate ledger metadata and step state in `aw runs` without triggering false `audit_step_artifact` (`missing_entirely`) findings on workflow step IDs (`S-01`). Re-checked at review: `discover_run_dirs` is also consumed by `attention` and `lanes_cli`, and both already skip directories without `state.json`, so classifying in `load_run_summary` (not in discovery) leaves them unaffected.

### OQ-02: Does accepting `ledger.jsonl` in `resolve_target_runs_detailed` affect `run_cli._classify_absent_target`'s `aw runs repair` signpost?

- Blocking: no
- Status: resolved
- Owner: antigravity
- Resolution or deferral rationale: Resolved from `agent_workflows/run_cli.py` (`def _classify_absent_target`): `_classify_absent_target` is invoked only when `resolve_ledger_path` returns `None` (no `ledger.jsonl` exists) and explicitly filters the directories returned by `resolve_target_runs_detailed` with `if (run_dir / "state.json").is_file(): return TARGET_DRIVER_RUN`. Accepting `ledger.jsonl` in `resolve_target_runs_detailed` therefore has zero effect on `_classify_absent_target` or `TestLedgerResolutionAndWrongFormatVerdict` in `tests/test_run_recovery_cli.py`. `run_analytics_cli._resolve_run_dirs` also delegates to this resolver; an explicit ledger path now reaches analytics ingestion, which reads driver artifacts (`state.json`, `events.jsonl`) and finds none in a ledger directory. V-03 requires the existing analytics-isolation tests (`AnalyticsIsolationTests`) to stay green.

### OQ-03: Is the ledger-leaf behavior change caused by E-01 (F-05) intended?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: Yes, keep it and pin it. A step with a `step_started` record and no terminal `step_attempt` is, by `run_recovery`'s own definition, an interrupted step whose outcome is unknown and "requires explicit reconciliation, not a silent rerun"; today `aw runs resume` without `--workflow` reports `unknown_outcome_steps: []` at exit 0 only because the skeleton drops the step, which hides exactly that condition. `aw run record` on such a step moving from exit 2 (`unknown step`) to exit 0 makes the follow-on of `aw run start` usable without `--workflow`, which is what sibling `o34rb3` is aiming at more fully. Demonstrated at review by monkeypatching the widening (F-05 probe output). Reversible: one condition in one helper, now pinned by E-08 so a revert is visible.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-06 validates E-06
  - Required evidence: the pasted pre-change outputs from E-06: (a) `aw runs --dir <root>` showing `run-abcdef1234` then `  0 steps: 0 steps`; (b) both explicit-path tokens reported unresolved by `resolve_target_runs_detailed`; (c) `aw runs status <ledger> --json` with `"steps": {}` and `aw run record <ledger> --step S-01 --state performed --json` exit 2 `unknown step 'S-01'`. Reachable today through `run_viewer.run_viewer_cli` and `run_cli._build_engine`.
  - Observed evidence:
  - Result: pending

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/run_cli.py` showing `_reconstruct_workflow_from_ledger` matching `kind in ("step_started", "step_attempt")` and the updated docstring, plus passing output of the E-05 progressed-run case showing a `step_started`-only step reconstructed with `state == "running"` and `attempts == 0`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing `ledger: dict[str, Any] | None = None` on `RunSummary`, `_load_ledger_run_summary` (catching `NotALedgerError`/`LedgerCorruption`/`OSError`, returning `None` on zero records, setting `pid=None`, not calling `inspect_run_pid_and_runtime`), and the `ledger_file.is_file()` branch in `load_run_summary`; plus passing output of the E-05 header-only, fail-closed, no-phantom-PID and read-only cases.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing only the two membership tests in `resolve_target_runs_detailed` widened to `ledger.jsonl` (no `execution-report.md` directory clause), plus passing output of `python3 -m pytest -o addopts="" tests/test_run_viewer.py tests/test_run_recovery_cli.py -k "LedgerRunViewerTests or TestLedgerResolutionAndWrongFormatVerdict or AnalyticsIsolationTests or UnresolvableTargetRefusalTests"`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing the `status_filter`, `failed_only` and `active_only` checks branching on `summary.ledger is not None` with the driver branches unchanged, plus passing output of the E-05 filter case (each of `--active`, `--status running`, `--status failed`, `--failed` with one included and one excluded ledger run) and of `python3 -m pytest -o addopts="" tests/test_run_viewer.py -k FilterExclusionReportingTests`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff agent_workflows/run_viewer.py` showing the `if run.ledger is not None:` block in `format_run_human`, plus the pasted human output of `aw runs --dir <root> --no-color` for a header-only and a progressed ledger run showing `[ledger]`, `ledger: state=...`, the step lines or `ledger steps: 0 recorded`, `inspect: aw runs status ... | aw runs show ...`, and no `0 steps: 0 steps` (the path E-02 and E-04 create: `run_viewer_cli` -> `load_run_summary` -> `_load_ledger_run_summary` -> `format_run_human`).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: pasted `python3 -m pytest -o addopts="" -v tests/test_run_viewer.py -k LedgerRunViewerTests` output with every case (a) to (f) passing, and pasted output of (a) and (d) failing on the base commit.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: the `tests/test_run_recovery_cli.py` diff, the new test's passing output, its pasted failing output on the base commit (`resume` exit 0 / `record` exit 2), and passing output of `python3 -m pytest -o addopts="" tests/test_run_recovery_cli.py tests/test_run_cli_declarations.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: the `CHANGELOG.md` diff (no em or en dashes), and the pasted bare `python3 -m pytest` summary line with zero failures (any failing node id must be shown to fail identically on the base commit to be excused), plus `aw sanitize --agent` output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval and once `v47z9u` is executed (`- Item-Dependencies: executed:v47z9u`). Open questions: all resolved. Scope fence: Scope-Paths is a declaration; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), and a declared path left untouched is acknowledged (`--scope-ack`). Commit only your own paths through `aw commit 3a3hh9 -- <paths>`; never push. Paste the actual runner output for every test claim; a claim without pasted output is not evidence. Lifecycle: when run by `aw oc run` / `aw agy run`, the runner finalizes; when executed by hand, finish with `aw ipd finalize 3a3hh9` only after `aw ipd lint --phase pre-transition` conforms and every `V-*` is `pass` with observed evidence.
