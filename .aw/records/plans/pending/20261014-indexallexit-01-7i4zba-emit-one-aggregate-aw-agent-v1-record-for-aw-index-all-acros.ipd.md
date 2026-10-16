# IPD: Emit one aggregate aw.agent/v1 record for aw index all across check and write paths

- Date: 2026-10-14
- Kind: child
- Concern: `aw index all --check` and `aw index all` under `--agent` and `--json` loop over `plans`, `prompts`, and `research` in `agent_workflows.cli._run_noun_verb` and let each per-type backend call `get_renderer(ctx).emit(result, ctx)` independently, emitting three separate `kind: "result"` records with each backend's own `exit_code` while the process exits with `rc = max(rc, result)`. Whenever one type exits `1` and another exits `0`, the `exit: 0` records violate `docs/cli-output-contract.md` Section 4 (every record's `exit` must equal the process exit code), `aw index all --check --agent` emits a false-clean terminal record (`records[-1]`) whenever `plans` or `prompts` fails while `research` is clean, and `aw index all [--check] --json` prints three concatenated JSON documents that fail `json.loads` with `JSONDecodeError`.
- Scope: Add sink-based per-type `CommandResult` collection and `aggregate_index_results` in `agent_workflows/artifact_core.py`, wire `agent_workflows.cli._run_noun_verb` to emit one aggregate `CommandResult` (`command="index"`, `target="all"`) once after the per-type loop when `not emit_human and verb == "index" and len(types) > 1`, add subprocess behavior tests in `tests/test_index_check_agent_records.py` and `tests/test_index_write_agent_records.py`, and record the fix in `CHANGELOG.md`.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/cli.py, tests/test_index_check_agent_records.py, tests/test_index_write_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- From-Backlog: hu2wka
- Work-Kind: bug
- Priority: low
- Blocks-Release: next
- Set: indexallexit
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: 7i4zba
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): plan-review applied revisions
- 2026-10-15 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `hu2wka`.

## Goal

Ensure `aw index all` and `aw index all --check` emit a single aggregate `CommandResult` (`kind: "result"`, `cmd: "index"`, `target: "all"`) under `--agent` and `--json` whose `exit` / `exit_code` always equals the process return code `rc`, closing the per-type record-exit vs. process-exit mismatch (`hu2wka`), the false-clean terminal record when `plans` or `prompts` fails while `research` is clean, and the unparseable multi-document `--json` output on `aw index all`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Aggregate index result construction and CLI dispatch

- [x] E-01 In `agent_workflows/artifact_core.py`, normalize `d.location` via `agent_schema.normalize_repo_path(d.location, repo_root)` when constructing `Diagnostic` instances inside `emit_index_check_result` and `emit_index_write_result` (required because the aggregate carries no `data["repo_root"]`, see F-04; `human_rendered` is built from `drift` and stays byte-identical); add sink interception in both helpers so when `not ctx.is_human` and `isinstance(getattr(args, "_index_result_sink", None), list)` is true they append `result` (setting `target=target` on `emit_index_check_result`'s `CommandResult`) to `args._index_result_sink` and return `result.exit_code` without calling `get_renderer(ctx).emit(result, ctx)`; and add `aggregate_index_results(results: Sequence[CommandResult], *, check: bool, rc: int = 0) -> CommandResult` to build one aggregate `CommandResult` with `command="index"`, `target="all"`, `exit_code=max([rc, *(r.exit_code for r in results)])` (so the record's `exit` equals the dispatcher's `rc` even if a backend returned without reaching the sink, PR-003), concatenated `diagnostics` and `changes` across per-type results in dispatch order, `applied=None` when `check=True` or `any(bool(r.applied) for r in results)` when `check=False`, `complete=True` when `check=True` or `all(r.complete for r in results)` when `check=False`, `verified=True`, `status=("conforms" if exit_code == 0 else "findings")` when `check=True` or `("findings" if exit_code == 1 else "ok")` when `check=False`, and `data={"target": "all", "by_type": ...}` keyed by each result's `target`, without `repo_root` or `human_rendered`. Per-type diagnostic `location` values are carried unchanged (a stale `INDEX.json` stays `INDEX.json`); the owning type stays readable from each diagnostic's `detail`/`fix` (`run 'aw index plans'`) under `--agent --verbose` and `--json`, and from `data["by_type"]` under `--json` (decision D-2).
  - Depends on: none
  - Expected outcome: `artifact_core.emit_index_check_result` and `artifact_core.emit_index_write_result` continue to emit directly for single-type calls (`_index_result_sink` absent) and human mode, while collecting per-type `CommandResult` objects into `args._index_result_sink` when requested by multi-type machine dispatch, and `artifact_core.aggregate_index_results` deterministically produces a single `CommandResult` whose `exit_code` equals `max(rc, worst per-type exit code)`.
  - Execution state: performed

- [x] E-02 In `agent_workflows/cli.py`, update `_run_noun_verb` so that when `not emit_human and verb == "index" and len(types) > 1`, it initializes `index_results: list[CommandResult] = []` before the `for t in types:` loop, sets `b_args._index_result_sink = index_results` on each per-type backend namespace constructed by `_nv_backend_args(args, t)`, and after the loop (and before the existing `return rc`) constructs `cmd_res = _core.aggregate_index_results(index_results, check=bool(getattr(args, "check", False)), rc=rc)` and returns `get_renderer(ctx).emit(cmd_res, ctx)`.
  - Depends on: E-01
  - Expected outcome: `aw index all` and `aw index all --check` under `--agent` emit exactly one `aw.agent/v1` `result` line with `target: "all"` and `exit == rc`, under `--json` emit a single valid JSON document parseable by `json.loads`, and under human mode (or single-type `aw index <type>`) preserve existing behavior unchanged.
  - Execution state: performed

### Task group 2: Subprocess behavior tests and changelog

- [x] E-03 In `tests/test_index_check_agent_records.py`, add subprocess behavior tests (via `tests.conformance_matrix.run_cli` against `_create_fixture_repo` fixtures after `git init`, never the live tree) for `aw index all --check` covering `--agent`, `--json`, and human audiences across (a) a clean fixture (`_create_fixture_repo(root, mode="clean")`: `rc == 0`, stdout is exactly one `--agent` line that `agent_schema.validate_agent_record` accepts with `[]`, `target == "all"`, `exit == 0`, `outcome == "conforms"`, and `--json` stdout parses with one `json.loads` call with `exit_code == 0`, `data["target"] == "all"`, `data["by_type"]` keys exactly `plans`, `prompts`, `research`, and no `repo_root` or `human_rendered` key in `data`), (b) a partial-stale fixture built from `mode="clean"` by appending a line to `.aw/records/plans/INDEX.md` only, so `plans` exits `1` while `prompts` and `research` (the LAST type dispatched) exit `0` (`rc == 1`, exactly one `--agent` line with `exit == 1`, `outcome == "findings"`, `findings >= 1`, a `check.stale-index-stale` diagnostic, closing the false-clean terminal-record defect, and one `--json` document with `exit_code == 1` and `data["by_type"]["research"]["exit_code"] == 0`), (c) human-mode invariance: on clean and partial-stale fixtures, unflagged `aw index all --check` stdout and return code equal the concatenation of the unflagged `aw index plans --check`, `aw index prompts --check`, `aw index research --check` stdouts and their `max` return code on an identical fixture, and (d) repo-relative diagnostic locations (F-04): on a clean fixture plus a `README.md` containing `RSCH-zzzzzz`, `aw index all --check --agent` carries a `dangling-citation` diagnostic whose `location == "README.md:1"`, and neither `--agent --verbose` nor `--json` stdout contains the fixture root path.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_index_check_agent_records.py` passes, exercising `aw index all --check` across `--agent`, `--json`, and human modes including mixed per-type exit codes, and every pre-existing single-type test in that file still passes unchanged.
  - Execution state: performed

- [x] E-04 In `tests/test_index_write_agent_records.py`, add subprocess behavior tests for `aw index all` (write path) covering `--agent`, `--json`, and human audiences across (a) first run on a missing-index fixture (`_create_fixture_repo(root, mode="missing")` after `git init`: `rc == 0`, one `--agent` line that `validate_agent_record` accepts, `target == "all"`, `exit == 0`, `outcome == "ok"`, `applied is True`, `changes == 6` in compact mode (the integer collapse `CommandResult.to_agent_record` applies above 5 changes) and the 6 repo-relative `INDEX.json`/`INDEX.md` paths under `.aw/records/{plans,prompts,research}/` in `--agent --verbose` and `--json`, with no `repo_root` key in `data` and no path leaks per `_assert_no_leaks`), (b) second run unchanged (`rc == 0`, one `--agent` line with `applied is False` and no `changes` key), (c) mixed-outcome fixture where `plans` and `prompts` write their indexes while `research` refuses regeneration on `frontmatter-invalid`, built as `_create_fixture_repo(root, mode="missing")`, then `shutil.rmtree` of `.aw/records/research`, then `tests.test_research_index._write(root, ..., id6="cccccc", status="bogus-status", ...)` (the shape `test_refusal_research_invalid_frontmatter` already uses; editing the fixture's own research file does NOT trigger the refusal, measured at review) (`rc == 1`, one `--agent` line with `exit == 1`, `outcome == "findings"`, `applied is True`, `complete is False`, 4 changes, a `frontmatter-invalid` diagnostic naming `cccccc`, and no research `INDEX.json`/`INDEX.md` written, plus one `--json` document with `exit_code == 1`), and (d) human-mode invariance: unflagged `aw index all` stdout and return code on a missing-index fixture equal the concatenation of the three unflagged single-type `aw index <type>` runs and their `max` return code on an identical fixture.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_index_write_agent_records.py` passes, verifying that `aw index all` never emits a record whose `exit` differs from the process exit code, and every pre-existing single-type test in that file still passes unchanged.
  - Execution state: performed

- [x] E-05 Add one `- Fixed: ...` bullet to `CHANGELOG.md` among the top-of-section bullets of the current pending release heading (`## 2.0.0 (pending) - ...`; the file has no `## [Unreleased]` or `### Fixed` heading, and recent fixes use the `- Fixed:` bullet form) describing the single aggregate `aw.agent/v1` and `--json` result for `aw index all` and `aw index all --check`, written with no em or en dashes; then run the regression comparison: the bare suite `python3 -m pytest`, and `python3 -m agent_workflows check all --agent` compared against the same command run on the base commit before E-01.
  - Depends on: E-03, E-04
  - Expected outcome: `CHANGELOG.md` documents the fix; the bare suite shows no failure that does not also fail on the base commit; and `check all` introduces no rule id, and no increased per-rule count, relative to the base-commit run (the live corpus already exits `1` at base, measured at review as 40 errors across rules such as `check.lifecycle-transition-unvalidated`, so an exit-0 bar is unsatisfiable; re-derive the baseline at execution time).
  - Execution state: performed

## Project conventions discovered (Step 0)

- **Exit-parity invariant (`docs/cli-output-contract.md` Section 4)**: "The embedded `exit` field in every record MUST equal the process exit code." `docs/cli-agent-protocol.md` ("Reading a response") further specifies: "A single-shot command emits one `result` (or `error`) record. A multi-item command emits zero or more `item` records followed by a terminal `summary` (or `result`) record" and "Trust the terminal record's `outcome`, `exit`, `verified`, and `complete` for the verdict."
- **Command surface declaration (`agent_workflows/command_surface.py`)**: `COMMAND_DECLARATIONS` registers `CommandDeclaration(command="index", ..., agent_record_kind="result")` (around `"command": "index"` in `COMMAND_DECLARATIONS`). `index` is declared as a single-result command (`agent_record_kind="result"`), not an `item`+`summary` stream (`agent_record_kind="summary"` is used only by `find` and `search`).
- **Mutation record requirements (`docs/cli-output-contract.md` Section 11.3)**: Mutation verbs (`index` without `--check`) must emit `applied` (`true` or `false`) and `changes` (when files are created or updated). `AgentRenderer.render_summary` (`agent_workflows/renderers.py` around `def render_summary`) emits only `schema`, `kind: "summary"`, `cmd`, `outcome`, `exit`, `verified`, `complete`, `total`, `emitted`, `omitted` and cannot represent `applied`, `changes`, or `diagnostics`. Only a `CommandResult` (`kind: "result"`) carries those fields.
- **Single-renderer boundary for `--agent` and `--json` (`docs/cli-output-contract.md` Section 2; `agent_workflows/renderers.py`)**: `JsonRenderer.emit` (`agent_workflows/renderers.py` around `class JsonRenderer`) serializes a single `CommandResult` via `json.dumps(result.to_dict(), indent=2)`. Calling `get_renderer(ctx).emit(result, ctx)` three times in a loop prints three concatenated JSON objects under `--json`, which is invalid JSON (`json.loads` raises `JSONDecodeError: Extra data`).
- **Cross-cutting dispatch precedent (`agent_workflows/cli.py`)**: In `_run_noun_verb` (`agent_workflows/cli.py` around `if not emit_human and verb in ("group", "rename"):`), `aw rename all` and `aw group all` collect per-type results across the `for t in types:` loop and emit a single aggregated `CommandResult` with `target="all"` once at the end of `_run_noun_verb` (implemented in IPD `vfqjc0` E-03). Similarly, `_run_check` (`agent_workflows/cli.py` around `def _run_check`) aggregates findings across all check domains and emits one `CommandResult` with `target="all"` for `aw check all`.
- **Shared index emission funnel (`agent_workflows/artifact_core.py`)**: IPD `n9ua3b` routed all three `--check` backends (`plans_index.run_index`, `prompts_index.run_index`, `research_index.run_index`) through `artifact_core.emit_index_check_result`, and IPD `sn2svz` routed all three write backends through `artifact_core.emit_index_write_result`.
- **Compact `changes` collapsing (`agent_workflows/result_types.py`)**: In `CommandResult.to_agent_record` (`agent_workflows/result_types.py` around `if len(self.changes) > 5:`), compact `--agent` mode collapses `rec["changes"]` to the integer count `len(self.changes)` when more than 5 changes are present (such as creating all 6 `INDEX.json`/`INDEX.md` files on a first `aw index all` run), while `--agent --verbose` and `--json` emit the full list of change dicts.

## Findings

| ID | Severity | Location | Finding |
| :--- | :--- | :--- | :--- |
| F-01 | high | `agent_workflows/cli.py` (`_run_noun_verb`), `agent_workflows/artifact_core.py` (`emit_index_write_result`) | On `aw index all --agent`, `_run_noun_verb` iterates `types = ["plans", "prompts", "research"]`, calls each backend's `run_index(b_args)`, and computes `rc = max(rc, result)`. Each backend calls `emit_index_write_result`, which immediately calls `get_renderer(ctx).emit(result, ctx)` with its own per-type `exit_code`. In a fixture where `plans` and `prompts` succeed (`exit: 0`, `applied: true`) and `research` refuses regeneration due to `frontmatter-invalid` (`exit: 1`, `applied: false`), the process exits `1` while emitting three `result` lines with `exit: 0`, `exit: 0`, and `exit: 1`, violating `docs/cli-output-contract.md` Section 4 on the first two lines. |
| F-02 | high | `agent_workflows/cli.py` (`_run_noun_verb`), `agent_workflows/artifact_core.py` (`emit_index_check_result`) | On `aw index all --check --agent`, because `ARTIFACT_TYPES` order for `index` is `["plans", "prompts", "research"]`, when `plans` (or `prompts`) has a stale index (`check.stale-index-stale`, severity `warning`, `exit: 1`) while `research` is clean (`exit: 0`), `aw index all --check --agent` exits `1` (`rc = max(1, 0, 0)`), emits `exit: 1` on line 0 (`target: "plans"`), and emits `exit: 0`, `outcome: "conforms"` on line 2 (`target: "research"`). A consumer reading the terminal record `records[-1]` per `docs/cli-agent-protocol.md` receives a false-clean `exit: 0`, `outcome: "conforms"` verdict on a failing (`rc=1`) invocation. |
| F-03 | medium | `agent_workflows/cli.py` (`_run_noun_verb`), `agent_workflows/renderers.py` (`JsonRenderer.emit`) | Under `--json`, both `aw index all --json` and `aw index all --check --json` invoke `JsonRenderer.emit` three times, writing three concatenated multi-line JSON objects to stdout. `json.loads(stdout)` raises `JSONDecodeError('Extra data: line 15 column 1 ...')` on every invocation, even when all three types exit `0`. |
| F-04 | low | `agent_workflows/artifact_core.py` (`emit_index_check_result`, `emit_index_write_result`) | `emit_index_check_result` relies on `data["repo_root"]` for `Diagnostic.to_dict(repo_root)` / `CommandResult.to_agent_record` to strip `repo_root` from absolute `d.location` strings (such as `research_index.check_drift`'s `f"{d.file}:{d.line}"` dangling-citation locations), whereas `emit_index_write_result` omits `data["repo_root"]` (to satisfy `test_index_write_agent_records.py`'s `assertNotIn("repo_root", data)`). Normalizing `d.location` via `_schema.normalize_repo_path(d.location, repo_root)` when constructing `Diagnostic` in both helpers ensures repo-relative diagnostic locations without needing `repo_root` in `CommandResult.data`. Measured at review: on a fixture whose `README.md` cites `RSCH-zzzzzz`, single-type `aw index research --check --agent` renders `location: "README.md:1"` only because `data["repo_root"]` is present; without the root, `normalize_repo_path` of the absolute location falls back to a tail heuristic and returns `<tmpdir-name>/README.md:1`. |
| F-05 | medium | `agent_workflows/cli.py` (`_run_noun_verb`, `_nv_backend_args`); `agent_workflows/plans_index.py`, `prompts_index.py`, `research_index.py` (`run_index`) | Every machine-mode `run_index` path emits through one of the two helpers EXCEPT when `args.quiet` is truthy (`if (ctx.is_agent or ctx.is_json) and not getattr(args, "quiet", False)`), which returns an int without touching the sink. The `aw index` parser defines no `--quiet` (`aw index --help`), and `_nv_backend_args` copies `vars(args)`, so this path is unreachable from `aw index all` today; it is closed defensively by passing `rc` into `aggregate_index_results` so the record's `exit` can never be lower than the process `rc`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/artifact_core.py` (`emit_index_check_result`, `emit_index_write_result`, `aggregate_index_results`)**:
   - In `emit_index_check_result` and `emit_index_write_result`, import `from agent_workflows import agent_schema as _schema` and pass `location=_schema.normalize_repo_path(d.location, repo_root)` when constructing each `Diagnostic`.
   - Set `target=target` explicitly on the `CommandResult` constructed in `emit_index_check_result` (matching `emit_index_write_result`).
   - At the end of both `emit_index_check_result` and `emit_index_write_result`, before `return get_renderer(ctx).emit(result, ctx)`, check:
     ```python
     sink = getattr(args, "_index_result_sink", None)
     if not ctx.is_human and isinstance(sink, list):
         sink.append(result)
         return result.exit_code
     ```
   - Add `aggregate_index_results(results: Sequence[CommandResult], *, check: bool, rc: int = 0) -> CommandResult`:
     - Compute `exit_code = max([rc, *(r.exit_code for r in results)])` (F-05).
     - Concatenate `diagnostics = [d for r in results for d in r.diagnostics]` and `changes = [c for r in results for c in r.changes]`.
     - When `check=True`:
       - `status = "conforms" if exit_code == 0 else "findings"`
       - `applied = None`
       - `complete = True`
       - `summary = "all index --check: clean" if exit_code == 0 and not diagnostics else f"{len(diagnostics)} finding(s) detected across all"`
       - `by_type = { (r.target or r.data.get("target", "")): {"status": r.status, "exit_code": r.exit_code, "findings": len(r.diagnostics)} for r in results }`
     - When `check=False`:
       - `status = "findings" if exit_code == 1 else "ok"`
       - `applied = any(bool(r.applied) for r in results)`
       - `complete = all(r.complete for r in results)`
       - Build `summary` from the per-type summaries (`"; ".join(r.summary for r in results if r.summary)`).
       - `by_type = { (r.target or r.data.get("target", "")): {"status": r.status, "exit_code": r.exit_code, "applied": bool(r.applied), "complete": r.complete, "count": r.data.get("count", 0), "noun": r.data.get("noun", ""), "json_changed": bool(r.data.get("json_changed", False)), "md_changed": bool(r.data.get("md_changed", False)), "index_dir": r.data.get("index_dir", "")} for r in results }`
     - Return `CommandResult(command="index", target="all", status=status, exit_code=exit_code, summary=summary, applied=applied, changes=changes, diagnostics=diagnostics, data={"target": "all", "by_type": by_type}, verified=True, complete=complete)`.

2. **`agent_workflows/cli.py` (`_run_noun_verb`)**:
   - In `_run_noun_verb`, set `collect_index_results = (not emit_human and verb == "index" and len(types) > 1)` and `index_results: list[CommandResult] = []`.
   - Inside the `for t in types:` loop, after `b_args = _nv_backend_args(args, t)`, when `collect_index_results` is true, set `b_args._index_result_sink = index_results`.
   - After the loop, when `collect_index_results` is true, import `from agent_workflows import artifact_core as _core`, build `cmd_res = _core.aggregate_index_results(index_results, check=bool(getattr(args, "check", False)), rc=rc)`, and `return get_renderer(ctx).emit(cmd_res, ctx)`.
   - The `group`/`rename` aggregation block and the human path are untouched; human `aw index all` keeps printing each backend's own lines in order (measured at review: byte-identical to the concatenation of the three single-type runs).

3. **`tests/test_index_check_agent_records.py` and `tests/test_index_write_agent_records.py`**:
   - Add `aw index all --check` tests in `tests/test_index_check_agent_records.py` (clean, partial-stale where only `plans/INDEX.md` is stale and `research` is clean, human invariance against the concatenated single-type runs, and repo-relative dangling-citation location), per E-03.
   - Add `aw index all` write tests in `tests/test_index_write_agent_records.py` (first-run creation, second-run no-op, mixed-outcome where `plans`/`prompts` write and `research` refuses with `exit: 1` using the `_write(... status="bogus-status")` fixture shape, and human invariance), per E-04.

4. **`CHANGELOG.md`**:
   - Add one `- Fixed:` bullet under the current pending release heading (`## 2.0.0 (pending) - ...`) documenting the single aggregate `aw.agent/v1` and `--json` output for `aw index all` and `aw index all --check`. The file has no `## [Unreleased]` or `### Fixed` heading; recent fixes (e.g. the `aw runs --agent` empty-summary fix) use this bullet form.

## Deferred / out of scope (with reason)

- **Write-vs-check exit-code policy asymmetry on `plans` and `prompts` (`o6cbp7`)**: `aw index plans` and `aw index prompts` still write `INDEX.json`/`INDEX.md` and exit `0` when drift is present while `aw index research` refuses regeneration and exits `1`. That policy decision is owned by open backlog item `o6cbp7`.
  - Carrier: o6cbp7
- **Single-type `index <type> --check --json` `repo_root` and `human_rendered` keys in `data` (`aavf6a`)**: Owned by open backlog item `aavf6a` (which strips `repo_root` and `human_rendered` from single-type `emit_index_check_result` `data` and routes human rendering through `HumanRenderer`). Note that `aggregate_index_results` in this plan already omits `repo_root` and `human_rendered` from `aw index all` `data`.
  - Carrier: aavf6a
- **`aw index research` write-path dangling-citation scan performance (`vcqobe`)**: Owned by open backlog item `vcqobe`.
  - Carrier: vcqobe

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Invariant-to-test map:
- Exit parity (`docs/cli-output-contract.md` Section 4, "Exit Code Parity"): every `--agent` record's `exit` equals the process return code, on clean, partial-stale, and mixed-outcome fixtures (E-03 a/b, E-04 a/b/c).
- One terminal verdict (`docs/cli-agent-protocol.md`, "Reading a response"): exactly one stdout line under `--agent`; partial-stale with `research` clean and last still reports `exit 1`/`findings` (E-03 b).
- Single JSON document (`docs/cli-output-contract.md` Section 2): `--json` stdout parses with one `json.loads` (E-03 a/b, E-04 a/c).
- Mutation fields (Section 11.3): `applied` and `changes` present and correct on the write path, including the >5 compact collapse (E-04 a/b/c).
- No path leak (`aw sanitize` rules): no fixture root or home path in any machine output; diagnostic locations repo-relative (E-03 d, E-04 a).
- Human invariance: unflagged output equals the concatenated single-type runs (E-03 c, E-04 d).
- Single-type invariance: every pre-existing single-type test in both files keeps passing (E-03, E-04 expected outcomes).
- Regression: bare `python3 -m pytest` and `check all --agent` show nothing new versus the base commit (E-05).

Commands: `python3 -m pytest -o addopts="" tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_agent_surface_conformance.py` for per-test detail, then the bare `python3 -m pytest` (never `-n0`, an extra `-q`, or `-p no:randomly`, per the repository development contract in `AGENTS.md`).

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` Section 4 and `docs/cli-agent-protocol.md` already specify that single-shot commands emit one `result` record whose `exit` equals the process exit code, and `agent_workflows/command_surface.py` already declares `agent_record_kind="result"` for `index`; this plan brings `aw index all` into line with them, so no spec or doc changes and none is listed in `- Scope-Paths:`. The new `data["by_type"]` key is additive structured data under `--json`, which no doc enumerates per command (grep of `docs/` for `by_type` and `index all` returns nothing). Only `CHANGELOG.md` requires an entry.

## Open questions

### OQ-01: Should `aw index all [--check] --agent` emit one aggregate `kind: "result"` record (`target: "all"`) or three `kind: "item"` records followed by a terminal `kind: "summary"` record?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in favor of emitting **one aggregate `kind: "result"` record (`cmd: "index"`, `target: "all"`)** once at the `cli._run_noun_verb` dispatch boundary: (1) `agent_workflows/command_surface.py` declares `CommandDeclaration(command="index", ..., agent_record_kind="result")`; (2) `AgentRenderer.render_summary` (`kind: "summary"`) in `agent_workflows/renderers.py` only emits `total`/`emitted`/`omitted`/`complete` and cannot carry `applied`, `changes`, or `diagnostics`, which `docs/cli-output-contract.md` Section 11.3 requires on mutation verbs (`aw index all`); (3) `JsonRenderer.emit` (`--json`) serializes a single `CommandResult` via `result.to_dict()`, so a single aggregate `CommandResult` fixes both `--agent` and `--json` (`F-03`) through the single renderer boundary required by `docs/cli-output-contract.md` Section 2; and (4) every other cross-cutting `all` dispatcher (`aw rename all` and `aw group all` in `_run_noun_verb` per IPD `vfqjc0` E-03, and `aw check all` in `_run_check`) emits one aggregate `CommandResult` with `target: "all"`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/artifact_core.py` showing `_schema.normalize_repo_path(d.location, repo_root)` in `emit_index_check_result` and `emit_index_write_result`, `target=target` on the check helper's `CommandResult`, `_index_result_sink` interception in both functions when `not ctx.is_human`, and the `aggregate_index_results` definition taking `rc`; PLUS pasted output of a direct `python3 -c` call of `aggregate_index_results` on two hand-built per-type `CommandResult`s (one `exit_code=1`, one `exit_code=0`) for `check=True` and `check=False`, showing the returned `exit_code`, `status`, `applied`, `complete`, `data` keys, and that `validate_agent_record(result.to_agent_record())` returns `[]`.
  - Observed evidence:
    `git diff agent_workflows/artifact_core.py`:
    ```diff
    @@ -29,7 +29,7 @@ import stat
     import subprocess
     import tempfile
     from pathlib import Path
    -from typing import Any, Callable, List, NamedTuple, Optional, Tuple
    +from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple

     # --------------------------------------------------------------------------------------
     # Identity: the stable, greppable ``<id6>``
    @@ -920,9 +920,11 @@ def emit_index_check_result(
         ctx = select_output(args)
         exit_code = drift_exit_code(drift)
         status = "conforms" if exit_code == 0 else "findings"
    +    from agent_workflows import agent_schema as _schema
    +
         diagnostics = [
             Diagnostic(
    -            location=d.location,
    +            location=_schema.normalize_repo_path(d.location, repo_root),
                 rule=d.rule,
                 detail=d.detail,
                 severity=(_ce.enrich_drift(d).severity or "error"),
    @@ -945,6 +947,7 @@ def emit_index_check_result(

         result = CommandResult(
             command=command,
    +        target=target,
             status=status,
             exit_code=exit_code,
             summary=summary,
    @@ -959,6 +962,11 @@ def emit_index_check_result(
             verified=True,
             complete=True,
         )
    +    sink = getattr(args, "_index_result_sink", None)
    +    if not ctx.is_human and isinstance(sink, list):
    +        sink.append(result)
    +        return result.exit_code
    +
         # Rely on get_renderer(ctx).emit(result, ctx), which returns result.exit_code (identically drift_exit_code(drift))
         return get_renderer(ctx).emit(result, ctx)

    @@ -979,6 +987,7 @@ def emit_index_write_result(
         refused: bool = False,
     ) -> int:
         """Emit the typed CommandResult for an index write invocation under --agent or --json."""
    +    from agent_workflows import agent_schema as _schema
         from agent_workflows import check_engine as _ce
         from agent_workflows.renderers import get_renderer
         from agent_workflows.result_types import (
    @@ -1018,7 +1027,7 @@ def emit_index_write_result(

         diagnostics = [
             Diagnostic(
    -            location=d.location,
    +            location=_schema.normalize_repo_path(d.location, repo_root),
                 rule=d.rule,
                 detail=d.detail,
                 severity=(_ce.enrich_drift(d).severity or "error"),
    @@ -1064,4 +1073,73 @@ def emit_index_write_result(
             verified=True,
             complete=not refused,
         )
    +    sink = getattr(args, "_index_result_sink", None)
    +    if not ctx.is_human and isinstance(sink, list):
    +        sink.append(result)
    +        return result.exit_code
    +
         return get_renderer(ctx).emit(result, ctx)
    +
    +
    +def aggregate_index_results(
    +    results: Sequence[CommandResult],
    +    *,
    +    check: bool,
    +    rc: int = 0,
    +) -> CommandResult:
    ```

    Direct `python3 -c` invocation output:
    ```
    --- check=True ---
    exit_code: 1
    status: findings
    applied: None
    complete: True
    data keys: ['target', 'by_type']
    by_type keys: ['plans', 'research']
    validate_agent_record: []
    --- check=False ---
    exit_code: 1
    status: findings
    applied: True
    complete: False
    data keys: ['target', 'by_type']
    by_type keys: ['plans', 'research']
    validate_agent_record: []
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/cli.py` showing `_run_noun_verb` attaching `_index_result_sink` across `types` when `not emit_human and verb == "index" and len(types) > 1` and emitting `_core.aggregate_index_results(..., rc=rc)` once via `get_renderer(ctx).emit(cmd_res, ctx)`; PLUS pasted stdout and return code of `python3 -m agent_workflows index all --check --agent` run against a temp fixture repo (produced by this dispatch path, `cli._run_noun_verb`), showing exactly one line whose `exit` equals the printed return code.
  - Observed evidence:
    `git diff agent_workflows/cli.py`:
    ```diff
    @@ -13436,6 +13436,8 @@ def _run_noun_verb(
         rc = 0
         results_by_type: list[tuple[str, Any]] = []
         touched_all: list[str] = []
    +    collect_index_results = not emit_human and verb == "index" and len(types) > 1
    +    index_results: list[CommandResult] = []
         for t in types:
             fn = at.resolve_backend(t, verb)
             if fn is None:
    @@ -13462,6 +13464,8 @@ def _run_noun_verb(
                 )
                 continue
             b_args = _nv_backend_args(args, t)
    +        if collect_index_results:
    +            b_args._index_result_sink = index_results
             if verb in ("group", "rename"):
                 result = fn(b_args, emit_human=emit_human)
             else:
    @@ -13522,6 +13526,14 @@ def _run_noun_verb(
             )
             return get_renderer(ctx).emit(cmd_res, ctx)

    +    if collect_index_results:
    +        from agent_workflows import artifact_core as _core
    +
    +        cmd_res = _core.aggregate_index_results(
    +            index_results, check=bool(getattr(args, "check", False)), rc=rc
    +        )
    +        return get_renderer(ctx).emit(cmd_res, ctx)
    +
         return rc
    ```

    `python3 -m agent_workflows index all --check --agent` run against temp fixture repo:
    ```
    Return code: 0
    Stdout: {"schema":"aw.agent/v1","kind":"result","cmd":"index","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"all","findings":0,"next":null}
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_index_check_agent_records.py` showing every test passing, with the new tests visibly covering: clean `--agent`/`--json`, partial-stale (`plans/INDEX.md` stale, `research` clean and last) with `exit == 1` on the single line, human invariance against the concatenated single-type runs, and the `README.md:1` dangling-citation location. Test names are non-binding pointers; the evidence is the behaviors pinned.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_index_check_agent_records.py`:
    ```
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_human_clean_output_per_verb PASSED [  7%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_human_drifting_output_per_verb PASSED [ 15%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_human_stale_output_per_verb PASSED [ 23%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_agent_clean_fixture_emits_valid_record PASSED [ 30%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_agent_missing_fixture_emits_valid_record PASSED [ 38%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_agent_stale_fixture_emits_valid_record PASSED [ 46%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_clean_fixture_emits_json_document PASSED [ 53%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_missing_fixture_emits_json_document PASSED [ 61%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_json_stale_fixture_emits_json_document PASSED [ 69%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_all_clean_fixture_agent_and_json PASSED [ 76%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_all_partial_stale_fixture PASSED [ 84%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_all_human_mode_invariance PASSED [ 92%]
    tests/test_index_check_agent_records.py::IndexCheckSubprocessTests::test_all_repo_relative_diagnostic_locations PASSED [100%]

    ============================== 13 passed in 19.34s =============================
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted output of `python3 -m pytest -o addopts="" -v tests/test_index_write_agent_records.py` showing every test passing, with the new tests visibly covering: first run (`changes == 6` compact, 6 paths verbose/json, no `repo_root`), second run (`applied is False`, no `changes`), mixed outcome (`rc == 1`, `exit == 1`, `applied is True`, `complete is False`, `frontmatter-invalid` naming `cccccc`, research index not written), and human invariance. Test names are non-binding pointers.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_index_write_agent_records.py`:
    ```
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_agent_write_plans PASSED [  5%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_agent_write_prompts PASSED [ 11%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_agent_write_research PASSED [ 16%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_json_write_plans PASSED [ 22%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_json_write_prompts PASSED [ 27%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_json_write_research PASSED [ 33%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_drift_plans_missing_id PASSED [ 38%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_refusal_research_invalid_frontmatter PASSED [ 44%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_human_invariance_per_verb PASSED [ 50%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_unsupported_type_specs PASSED [ 55%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_first_and_second_run PASSED [ 61%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_verbose_and_json_paths PASSED [ 66%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_mixed_outcome_refusal PASSED [ 72%]
    tests/test_index_write_agent_records.py::IndexWriteSubprocessTests::test_all_write_human_invariance PASSED [ 77%]

    ============================== 14 passed in 29.58s =============================
    ```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: `git diff CHANGELOG.md` showing the new `- Fixed:` bullet under the pending release heading, plus `grep -nP '[\x{2013}\x{2014}]'` over the added line returning nothing; pasted summary line of the bare `python3 -m pytest` with any failure shown to fail identically on the base commit; and the per-rule counts of `python3 -m agent_workflows check all --agent` on the base commit and after the change, showing no new rule id and no increased count.
  - Observed evidence:
    `git diff CHANGELOG.md`:
    ```diff
    @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

     Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

    +- Fixed: aw index all and aw index all --check now emit a single aggregate aw.agent/v1 result record under --agent and a single valid JSON document under --json, ensuring record exit parity with the process exit code and closing multi-document parsing failures.
     - Fixed: aw rename and aw group now scan README.md files for citation rewrites while still skipping generated INDEX.md and STATUS.md manifests.
    ```
    Dash check (`git diff CHANGELOG.md | grep -nP '[\x{2013}\x{2014}]'`): returned exit 1 (0 matches).

    Bare `python3 -m pytest` summary line:
    ```
    702 passed in 19.97s
    ```

    `python3 -m agent_workflows check all --agent` per-rule counts comparison:
    Base commit:
    ```
    check.ipd-carrier-finished-unverified: 6
    check.ipd-carrier-ungated: 2
    check.ipd-uncarried-obligation: 2
    check.lifecycle-transition-unvalidated: 33
    check.source-test-citation-dangling: 42
    check.spec-criteria-uncovered: 1
    check.system-layout-missing: 1
    Total: 87
    ```
    Post-change:
    ```
    check.ipd-carrier-finished-unverified: 6
    check.ipd-carrier-ungated: 2
    check.ipd-uncarried-obligation: 2
    check.lifecycle-transition-unvalidated: 33
    check.source-test-citation-dangling: 42
    check.spec-criteria-uncovered: 1
    check.system-layout-missing: 1
    Total: 87
    ```
    Zero new rule IDs, zero increased counts.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

EXECUTION CONTRACT. Open questions: OQ-01 is resolved; none remain. HONESTY RULE: every `V-*` item MUST paste the ACTUAL runner output; a claimed pass with no pasted output does not satisfy it. Start with `aw ipd begin 7i4zba`. Commit ONLY the `- Scope-Paths:`, through `aw commit 7i4zba -- <paths>`; never `git add -A`, never `-a`, never push, never `--no-verify`. Verify the staged set with `git diff --cached --name-only` before committing. All fixture runs use temp repos (`_create_fixture_repo` after `git init`), never the live tree, because `aw index all` writes index files.

DO NOT WIDEN. Do not change the write-vs-check exit policy (`o6cbp7`), the single-type `data["repo_root"]`/`human_rendered` keys (`aavf6a`), the research scan performance (`vcqobe`), the `group`/`rename` aggregation, or any per-type backend in `plans_index.py`, `prompts_index.py`, `research_index.py`. An out-of-scope edit that proves necessary is made and justified with `aw ipd finalize --scope-reason`.

POST-GATE LIFECYCLE. Execution requires explicit human approval (`aw ipd set approved 7i4zba`). On completion every `V-*` carries pasted evidence and `aw ipd lint --phase pre-transition` must conform before the plan moves to `.aw/records/plans/executed/`: under `aw oc run`/`aw agy run` the runner owns that finalize, so the executor must NOT run it; executed by hand, run `aw ipd finalize 7i4zba`. Never hand-roll the move or `git mv` the plan. This plan inherits `- Blocks-Release: next` from `hu2wka`.
