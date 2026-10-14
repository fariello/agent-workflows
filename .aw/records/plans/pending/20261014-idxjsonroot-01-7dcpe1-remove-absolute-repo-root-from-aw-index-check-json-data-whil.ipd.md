# IPD: Remove absolute repo_root from aw index --check --json data while preserving diagnostic path relativization

- Date: 2026-10-14
- Kind: child
- Concern: aw index <type> --check --json machine-output leak posture and diagnostic path relativization
- Scope: Add an out-of-band repo_root attribute on CommandResult so Diagnostic.to_dict, Change.to_dict, Evidence.to_dict, and HumanRenderer resolve repo_root without requiring data["repo_root"]; remove "repo_root" and non-human "human_rendered" from emit_index_check_result and emit_index_write_result data while normalizing drift diagnostic locations against repo_root.
- Scope-Paths: agent_workflows/result_types.py, agent_workflows/renderers.py, agent_workflows/artifact_core.py, tests/test_index_check_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- From-Backlog: aavf6a
- Blocks-Release: next
- Work-Kind: bug
- Priority: low
- Set: idxjsonroot
- Order: 1
- Highest E allocated: 04
- Author: Antigravity Agent
- Id: 7dcpe1

## Workflow history
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity Agent): created.

## Goal

Eliminate the raw absolute `repo_root` path (and non-human `human_rendered` drift text containing raw absolute `dangling-citation` file paths) from `aw index <type> --check --json` (`data` payload in `artifact_core.emit_index_check_result` and `artifact_core.emit_index_write_result`), while preserving repo-relative diagnostic, change, and evidence path normalization in both `--json` and `--agent` modes via an out-of-band `CommandResult.repo_root` attribute.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Out-of-band repo_root on CommandResult and index check/write emission cleanup

- [ ] E-01 Add an optional out-of-band `repo_root: Optional[Union[str, Path]] = None` field to `result_types.CommandResult` and resolve `repo_root = self.repo_root if self.repo_root is not None else self.data.get("repo_root")` in `result_types.CommandResult.to_dict`, `result_types.CommandResult.to_agent_record`, and `renderers.HumanRenderer.render` without serializing `repo_root` as a top-level or `data` key in `CommandResult.to_dict`.
  - Depends on: none
  - Expected outcome: `CommandResult(command="index", repo_root=root, diagnostics=[...], data={"target": "plans"})` relativizes `Diagnostic`, `Change`, and `Evidence` paths against `root` in both `to_dict()` and `to_agent_record()`, while `to_dict()["data"]` contains only `{"target": "plans"}` and callers that still pass `data["repo_root"]` remain backward-compatible.
  - Execution state: pending

- [ ] E-02 Update `artifact_core.emit_index_check_result` and `artifact_core.emit_index_write_result` to pass `repo_root=repo_root` (and `target=target` on `emit_index_check_result`) on `CommandResult`, normalize each drift `Diagnostic.location` via `_schema.normalize_repo_path(d.location, repo_root)`, remove `"repo_root"` from `data`, and include `"human_rendered"` in `emit_index_check_result` `data` only when `ctx.is_human`.
  - Depends on: E-01
  - Expected outcome: `aw index <plans|prompts|research> --check --json` emits `data == {"target": "<type>"}` with no `"repo_root"` or `"human_rendered"` key and no absolute path anywhere in the JSON document, `aw index <type> --check --agent` and human mode preserve their existing contracts, and `emit_index_write_result` omits `"repo_root"` from `data` in `--json` mode.
  - Execution state: pending

### Task group 2: Regression tests and changelog

- [ ] E-03 Add unit and CLI regression tests in `tests/test_index_check_agent_records.py` covering `CommandResult.repo_root` out-of-band relativization, `--check --json` `data` shape and leak-free stdout across `plans`, `prompts`, and `research` (clean, missing, and stale), and `dangling-citation` findings in a root-level scan file (`DECISIONS.md`) outside `agent_schema.normalize_repo_path` `known_markers` under both `--json` and `--agent`.
  - Depends on: E-02
  - Expected outcome: `pytest tests/test_index_check_agent_records.py` passes with explicit assertions that `"repo_root" not in doc["data"]`, `"human_rendered" not in doc["data"]`, root-level `dangling-citation` diagnostics relativize to `"DECISIONS.md:1"` in both `--json` and `--agent`, and no temporary fixture path or home directory path appears in `stdout`.
  - Execution state: pending

- [ ] E-04 Add a `Fixed:` entry under `## 2.0.0 (pending)` in `CHANGELOG.md` (with no em or en dashes) and run `pytest` on the index and JSON leak posture test modules plus `aw sanitize --agent`.
  - Depends on: E-03
  - Expected outcome: `CHANGELOG.md` documents the fix without em/en dashes, all targeted and full test runs pass, and `aw sanitize --agent` reports `"outcome":"clean"`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Normative machine-output leak contract (`docs/cli-output-contract.md` Section 4, `"4. Path Sanitization and Leak Posture"`):
  - All `location` fields in `diagnostics[]`, `changes[]`, and `evidence[]` must be repo-relative POSIX paths (forward slashes, no leading `./` or `/`) via `agent_schema.normalize_repo_path`.
  - Under `"### `data` field exemption"`, `result.data` is passed through without path transformation in `JsonRenderer.render` and `AgentRenderer.render`; producers must NOT place absolute paths in `data` unless explicitly permitted by an approved spec (such as spec `kw5y2s` for `data.logical_roots` when an external backend is active).
- `result_types.CommandResult.to_dict` and `result_types.CommandResult.to_agent_record` (`agent_workflows/result_types.py`, symbols `CommandResult.to_dict` and `CommandResult.to_agent_record`):
  - Both methods currently resolve `repo_root = self.data.get("repo_root")` and forward `repo_root` to `Diagnostic.to_dict(repo_root)`, `Change.to_dict(repo_root)`, and `Evidence.to_dict(repo_root)`.
  - `CommandResult.to_dict` then emits `"data": dict(self.data)` verbatim (`"`"data": dict(self.data),`"`), which is what `renderers.JsonRenderer.render` serializes via `json.dumps(result.to_dict(), indent=2, default=str)`.
  - `CommandResult.to_agent_record` strips internal keys from `self.data` via `internal_keys = {"repo_root", "human_rendered", "target"}` (`agent_workflows/result_types.py`, symbol `CommandResult.to_agent_record`), which is why `--agent` did not leak `data["repo_root"]` or `data["human_rendered"]` while `--json` leaked both.
- Why `repo_root` must still reach `Diagnostic.to_dict` / `agent_schema.normalize_repo_path`:
  - In `plans_index.check_drift` (`Drift(f"{d.file}:{d.line}", "dangling-citation", ...)`), `research_index.check_drift` (`Drift(f"{d.file}:{d.line}", "dangling-citation", ...)`), and `prompts_index.check_drift` (when `scan_dangling=True`), `d.file` returned by `artifact_refs.find_dangling_citations` (`iter_scan_files(repo_root, scan_roots)`) is an absolute `Path` (`repo_root / rel`).
  - `artifact_refs.DEFAULT_SCAN_ROOTS` includes root-level files and directories outside `.aw/` (`"DECISIONS.md"`, `"README.md"`, `"CHANGELOG.md"`, `"TODO.md"`, `"AGENTS.md"`, `"CLAUDE.md"`, `"GEMINI.md"`, `"docs"`).
  - In `agent_schema.normalize_repo_path` (`agent_workflows/agent_schema.py`, symbol `normalize_repo_path`), when `repo_root` is `None`, fallback stripping only recognizes `known_markers = (".aw/records/", ".aw/system/", ".aw/context/", ".aw/templates/", ".aw/doc/", "records/", "system/", "context/", "templates/", "doc/", "agent_workflows/", "tests/", "scripts/")` and otherwise falls back to the last 2 path components (`"/".join(parts[-2:])`). Without `repo_root`, an absolute location on a root-level scan file such as `DECISIONS.md` (with a trailing `:line` suffix) normalizes to `<repo-dir-name>/DECISIONS.md` (with `:line`) instead of the repo-relative `DECISIONS.md` (with `:line`), and a path inside a worktree (`.aw/worktrees/<lane>/.aw/records/...`) retains `.aw/worktrees/<lane>/...` unless `repo_root` or `known_markers` strips the worktree prefix.
- Sibling plan coordination (`7i4zba`, `.aw/records/plans/pending/20261014-indexallexit-01-7i4zba-emit-one-aggregate-aw-agent-v1-record-for-aw-index-all-acros.ipd.md`):
  - Plan `7i4zba` (graduated from `hu2wka`) explicitly notes under `## Deferred / out of scope (with reason)`: `"Removing repo_root and human_rendered from single-type emit_index_check_result data in --json mode: tracked separately under open backlog item aavf6a (idxjsonroot); E-01 omits repo_root and human_rendered on the new aggregate emit_index_all_result helper from day one."`
  - Keeping `emit_index_check_result` and `emit_index_write_result` signatures unchanged while using `CommandResult.repo_root` and normalizing `Diagnostic.location` is cleanly composable with `7i4zba` in either merge order.
- Prose convention (`GEMINI.md` Rule 3 and `AGENTS.md`):
  - User-facing prose in `CHANGELOG.md` must contain zero em dashes or en dashes.

## Findings

| # | Location (symbol / anchor) | Observation | Impact |
|---|---|---|---|
| F-01 | `agent_workflows/artifact_core.py` (`emit_index_check_result`, `"repo_root": str(repo_root)`) | `emit_index_check_result` constructs `CommandResult` with `data={"target": target, "repo_root": str(repo_root), "human_rendered": human_rendered}` and does not set `target=target` on `CommandResult`. | Under `aw index <type> --check --json`, `JsonRenderer.render` serializes `result.to_dict()`, emitting the caller's raw absolute checkout path in `data["repo_root"]` in violation of `docs/cli-output-contract.md` Section 4. |
| F-02 | `agent_workflows/artifact_core.py` (`emit_index_check_result`, `"human_rendered": human_rendered`) | `emit_index_check_result` builds `human_rendered = "".join(f"{d.location}: {d.rule}: {d.detail}\n" for d in drift)` from raw `d.location` strings (before `normalize_repo_path`) and unconditionally places `"human_rendered"` in `data`. Measured on this checkout with `python3 -m agent_workflows index research --check --json`, `data["human_rendered"]` contains 315 lines starting with the absolute checkout path from `dangling-citation` findings. | Even if `"repo_root"` alone were removed from `data`, `--check --json` would still leak raw absolute paths inside `data["human_rendered"]` whenever `dangling-citation` drift exists. `human_rendered` is only consumed by `renderers.HumanRenderer.render` (`if "human_rendered" in result.data:`). |
| F-03 | `agent_workflows/artifact_core.py` (`emit_index_write_result`, `"repo_root": str(repo_root)`) | `emit_index_write_result` also populates `data: Dict[str, Any] = {"target": target, "repo_root": str(repo_root), "count": count}`. | Any `emit_index_write_result` invocation rendered through `JsonRenderer` leaks `data["repo_root"]`; switching it to out-of-band `CommandResult(repo_root=repo_root)` keeps both index helpers consistent. |
| F-04 | `agent_workflows/result_types.py` (`CommandResult.to_dict` and `CommandResult.to_agent_record`) and `agent_workflows/renderers.py` (`HumanRenderer.render`) | `CommandResult` has no dedicated `repo_root` dataclass field; `to_dict`, `to_agent_record`, and `HumanRenderer.render` read `self.data.get("repo_root")` (or `result.data.get("repo_root")`). | Adding `repo_root: Optional[Union[str, Path]] = None` on `CommandResult` and resolving `self.repo_root if self.repo_root is not None else self.data.get("repo_root")` supplies an out-of-band `repo_root` channel for path relativization without breaking legacy callers that still pass `data["repo_root"]`. |

## Proposed changes (ordered, validatable)

1. **Out-of-band `repo_root` on `CommandResult` (`agent_workflows/result_types.py` and `agent_workflows/renderers.py`) — `E-01`**:
   - In `result_types.CommandResult` (`class CommandResult`), add dataclass attribute `repo_root: Optional[Union[str, Path]] = None` after `complete: bool = True`.
   - In `result_types.CommandResult.to_dict`, resolve `repo_root = self.repo_root if self.repo_root is not None else self.data.get("repo_root")` before converting `self.diagnostics`, `self.changes`, and `self.evidence`. Do not add `"repo_root"` to the returned dictionary.
   - In `result_types.CommandResult.to_agent_record`, resolve `repo_root = self.repo_root if self.repo_root is not None else self.data.get("repo_root")`.
   - In `renderers.HumanRenderer.render` (`agent_workflows/renderers.py`, symbol `HumanRenderer.render`), resolve `repo_root = Path(result.repo_root or result.data.get("repo_root") or ".")`.

2. **Index check/write `CommandResult` construction (`agent_workflows/artifact_core.py`) — `E-02`**:
   - In `artifact_core.emit_index_check_result`:
     - Normalize each `Diagnostic.location` at construction using `_schema.normalize_repo_path(d.location, repo_root)` (and normalize `d.location` in `human_rendered` when `ctx.is_human` or keep `human_rendered` byte-identical for human mode while only attaching `"human_rendered"` to `data` when `ctx.is_human`). Note: to preserve existing human-mode behavior byte-for-byte on all tests, keep `human_rendered` construction unchanged and populate `data` as:
       ```python
       data: Dict[str, Any] = {"target": target}
       if ctx.is_human:
           data["human_rendered"] = human_rendered
       ```
     - Construct `CommandResult` with `target=target`, `repo_root=repo_root`, and `data=data` (no `"repo_root"` key in `data`).
   - In `artifact_core.emit_index_write_result`:
     - Populate `data: Dict[str, Any] = {"target": target, "count": count}` (no `"repo_root"` key in `data`) and pass `repo_root=repo_root` on `CommandResult`.

3. **Regression tests (`tests/test_index_check_agent_records.py`) — `E-03`**:
   - Add unit test `test_command_result_out_of_band_repo_root_relativizes_without_data_key(tmp_path)` exercising `CommandResult(command="index", target="plans", repo_root=tmp_path, diagnostics=[Diagnostic(location=f"{tmp_path / 'DECISIONS.md'}:1", rule="check.index-dangling-citation", detail="dangling")], data={"target": "plans"})` and asserting:
     - `"repo_root" not in res.to_dict()["data"]`
     - `"repo_root" not in res.to_dict()`
     - `res.to_dict()["diagnostics"][0]["location"] == "DECISIONS.md:1"`
     - `res.to_agent_record()["diagnostics"][0]["location"] == "DECISIONS.md:1"`
   - Add parametrized CLI test `test_index_check_json_omits_repo_root_and_human_rendered(index_fixture, verb, mode)` across `verb in ("plans", "prompts", "research")` and `mode in ("clean", "missing", "stale")` verifying:
     - `doc = json.loads(res.stdout)`
     - `"repo_root" not in doc["data"]`
     - `"human_rendered" not in doc["data"]`
     - `doc["data"]["target"] == verb`
     - `str(index_fixture) not in res.stdout` and `str(Path.home()) not in res.stdout`
   - Add parametrized CLI test `test_index_check_dangling_citation_relativizes_location_in_json_and_agent(index_fixture, verb)` for `verb in ("plans", "research")` that writes a dangling citation (`PLAN-999999` or `RSCH-999999`) to `index_fixture / "DECISIONS.md"` (a root-level scan file outside `agent_schema.normalize_repo_path` `known_markers`) and verifies:
     - Under `--check --json`: `res.returncode == 1`, `"repo_root" not in doc["data"]`, `"human_rendered" not in doc["data"]`, `str(index_fixture) not in res.stdout`, and the `check.index-dangling-citation` diagnostic has `location == "DECISIONS.md:1"`.
     - Under `--check --agent --verbose`: `res.returncode == 1`, `str(index_fixture) not in res.stdout`, and the `check.index-dangling-citation` diagnostic has `location == "DECISIONS.md:1"`.

4. **Changelog and verification (`CHANGELOG.md`) — `E-04`**:
   - Add a `Fixed:` bullet under `## 2.0.0 (pending)` in `CHANGELOG.md` describing the removal of the absolute `repo_root` path (and non-human `human_rendered` payload) from `aw index <type> --check --json` `data` and the out-of-band `CommandResult.repo_root` relativization channel, with zero em or en dashes.
   - Run `python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py` and `python3 -m agent_workflows check-local-leaks . --agent`.

## Deferred / out of scope (with reason)

- Migrating unrelated commands (`cli._run_check` in `agent_workflows/cli.py`, `releases.py`) from `data["repo_root"]` to `CommandResult.repo_root`: out of scope for backlog item `aavf6a`, which specifically scopes `artifact_core.emit_index_check_result` (`aw index <type> --check --json`) and its `CommandResult` relativization path. `CommandResult` retains backward compatibility with `self.data.get("repo_root")` so other commands continue to work unchanged.
- Emitting one aggregate `CommandResult` for `aw index all [--check]`: owned by sibling plan `7i4zba` (backlog `hu2wka`).

## Scope check

- Over-scope: none.
- Under-scope: none; both sources of absolute-path leakage in `emit_index_check_result` (`data["repo_root"]` and `data["human_rendered"]`) and `emit_index_write_result` (`data["repo_root"]`) are addressed along with out-of-band `CommandResult.repo_root` relativization for `Diagnostic`, `Change`, and `Evidence` locations.

## Required tests / validation

- Targeted pytest suite: `python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py`
- Direct CLI verification: `python3 -m agent_workflows index plans --check --json` and `python3 -m agent_workflows index research --check --json` confirming `data` keys are `["target"]` with zero occurrences of the checkout path in stdout.
- Leak-sanitizer check: `python3 -m agent_workflows check-local-leaks . --agent`

## Spec / documentation sync

- `CHANGELOG.md`: add a `Fixed:` entry under `## 2.0.0 (pending)`.
- `docs/cli-output-contract.md`: N/A with reason — Section 4 (`"4. Path Sanitization and Leak Posture"`) already specifies that producers must not put absolute paths in `data` unless permitted by an approved spec; this plan brings `emit_index_check_result` and `emit_index_write_result` into compliance with the existing contract.

## Open questions

### OQ-01: Should `human_rendered` also be omitted from `emit_index_check_result` `data` when `not ctx.is_human`?

- Blocking: no
- Status: resolved
- Owner: Antigravity Agent
- Resolution or deferral rationale: Resolved from repository evidence (`agent_workflows/artifact_core.py` symbol `emit_index_check_result`, `agent_workflows/renderers.py` symbol `HumanRenderer.render`, and sibling plan `7i4zba`). `human_rendered` is only read by `HumanRenderer.render` (`if "human_rendered" in result.data:`). When `dangling-citation` findings exist, `human_rendered` contains raw `d.location` strings with absolute filesystem paths, so leaving `"human_rendered"` in `data` under `--json` would continue to leak the absolute repo root in `--check --json` output. Including `"human_rendered"` only when `ctx.is_human` preserves human mode byte-for-byte while making `--check --json` completely free of absolute repo-root paths.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/result_types.py agent_workflows/renderers.py` showing `repo_root: Optional[Union[str, Path]] = None` on `CommandResult` and fallback resolution `self.repo_root if self.repo_root is not None else self.data.get("repo_root")` in `CommandResult.to_dict`, `CommandResult.to_agent_record`, and `HumanRenderer.render`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/artifact_core.py` and pasted output of `python3 -c 'import json, subprocess; p = subprocess.run(["python3", "-m", "agent_workflows", "index", "research", "--check", "--json"], capture_output=True, text=True); doc = json.loads(p.stdout); print(sorted(doc["data"].keys()), doc["diagnostics"][0]["location"][:30] if doc["diagnostics"] else "no-diag")'` (created/exercised by `E-02` via `artifact_core.emit_index_check_result`) showing `['target']` and a repo-relative diagnostic location with no absolute checkout path in stdout.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted runner output of `python3 -m pytest tests/test_index_check_agent_records.py` showing all tests (including `test_command_result_out_of_band_repo_root_relativizes_without_data_key`, `test_index_check_json_omits_repo_root_and_human_rendered`, and `test_index_check_dangling_citation_relativizes_location_in_json_and_agent`) passing.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` showing the new `Fixed:` entry with zero em/en dashes, plus pasted runner outputs of `python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_json_surface_leak_posture.py` and `python3 -m agent_workflows check-local-leaks . --agent` exiting 0.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is authored in `to-review` status for human review and runner execution. Upon execution, all `E-*` items must be marked `performed` and all `V-*` items marked `pass` with concrete pasted evidence before transitioning the plan to `executed` via `aw ipd set executed 7dcpe1`.
