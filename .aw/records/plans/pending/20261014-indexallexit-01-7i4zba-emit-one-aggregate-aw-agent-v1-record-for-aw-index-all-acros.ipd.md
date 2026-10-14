# IPD: Emit one aggregate aw.agent/v1 record for aw index all across check and write paths

- Date: 2026-10-14
- Kind: child
- Concern: `aw index all --check` and `aw index all` under `--agent` and `--json` loop over `plans`, `prompts`, and `research` in `agent_workflows.cli._run_noun_verb` and let each per-type backend call `get_renderer(ctx).emit(result, ctx)` independently, emitting three separate `kind: "result"` records with each backend's own `exit_code` while the process exits with `rc = max(rc, result)`. Whenever one type exits `1` and another exits `0`, the `exit: 0` records violate `docs/cli-output-contract.md` Section 4 (every record's `exit` must equal the process exit code), `aw index all --check --agent` emits a false-clean terminal record (`records[-1]`) whenever `plans` or `prompts` fails while `research` is clean, and `aw index all [--check] --json` prints three concatenated JSON documents that fail `json.loads` with `JSONDecodeError`.
- Scope: Add sink-based per-type `CommandResult` collection and `aggregate_index_results` in `agent_workflows/artifact_core.py`, wire `agent_workflows.cli._run_noun_verb` to emit one aggregate `CommandResult` (`command="index"`, `target="all"`) once after the per-type loop when `not emit_human and verb == "index" and len(types) > 1`, add subprocess behavior tests in `tests/test_index_check_agent_records.py` and `tests/test_index_write_agent_records.py`, and record the fix in `CHANGELOG.md`.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/cli.py, tests/test_index_check_agent_records.py, tests/test_index_write_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- From-Backlog: hu2wka
- Work-Kind: bug
- Priority: low
- Blocks-Release: next
- Set: indexallexit
- Order: 1
- Highest E allocated: 05
- Author: Antigravity
- Id: 7i4zba

## Workflow history
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `hu2wka`.

## Goal

Ensure `aw index all` and `aw index all --check` emit a single aggregate `CommandResult` (`kind: "result"`, `cmd: "index"`, `target: "all"`) under `--agent` and `--json` whose `exit` / `exit_code` always equals the process return code `rc`, closing the per-type record-exit vs. process-exit mismatch (`hu2wka`), the false-clean terminal record when `plans` or `prompts` fails while `research` is clean, and the unparseable multi-document `--json` output on `aw index all`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Aggregate index result construction and CLI dispatch

- [ ] E-01 In `agent_workflows/artifact_core.py`, normalize `d.location` via `agent_schema.normalize_repo_path(d.location, repo_root)` when constructing `Diagnostic` instances inside `emit_index_check_result` and `emit_index_write_result`; add sink interception in both helpers so when `not ctx.is_human` and `isinstance(getattr(args, "_index_result_sink", None), list)` is true they append `result` (setting `target=target` on `emit_index_check_result`'s `CommandResult`) to `args._index_result_sink` and return `result.exit_code` without calling `get_renderer(ctx).emit(result, ctx)`; and add `aggregate_index_results(results: Sequence[CommandResult], *, check: bool) -> CommandResult` to build one aggregate `CommandResult` with `command="index"`, `target="all"`, `exit_code=max((r.exit_code for r in results), default=0)`, concatenated `diagnostics` and `changes` across per-type results in `ARTIFACT_TYPES` order, `applied=None` when `check=True` or `any(bool(r.applied) for r in results)` when `check=False`, `complete=True` when `check=True` or `all(r.complete for r in results)` when `check=False`, `verified=True`, `status=("conforms" if exit_code == 0 else "findings")` when `check=True` or `("findings" if exit_code == 1 else "ok")` when `check=False`, and `data={"target": "all", "by_type": ...}` without `repo_root` or `human_rendered`.
  - Depends on: none
  - Expected outcome: `artifact_core.emit_index_check_result` and `artifact_core.emit_index_write_result` continue to emit directly for single-type calls (`_index_result_sink` absent) and human mode, while collecting per-type `CommandResult` objects into `args._index_result_sink` when requested by multi-type machine dispatch, and `artifact_core.aggregate_index_results` deterministically produces a single `CommandResult` whose `exit_code` matches the worst per-type exit code.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/cli.py`, update `_run_noun_verb` so that when `not emit_human and verb == "index" and len(types) > 1`, it initializes `index_results: list[CommandResult] = []` before the `for t in types:` loop, sets `b_args._index_result_sink = index_results` on each per-type backend namespace constructed by `_nv_backend_args(args, t)`, and after the loop constructs `cmd_res = _core.aggregate_index_results(index_results, check=bool(getattr(args, "check", False)))` and returns `get_renderer(ctx).emit(cmd_res, ctx)`.
  - Depends on: E-01
  - Expected outcome: `aw index all` and `aw index all --check` under `--agent` emit exactly one `aw.agent/v1` `result` line with `target: "all"` and `exit == rc`, under `--json` emit a single valid JSON document parseable by `json.loads`, and under human mode (or single-type `aw index <type>`) preserve existing behavior unchanged.
  - Execution state: pending

### Task group 2: Subprocess behavior tests and changelog

- [ ] E-03 In `tests/test_index_check_agent_records.py`, add subprocess behavior tests for `aw index all --check` covering `--agent`, `--json`, and human audiences across (a) a clean fixture (`rc == 0`, one `--agent` line with `target == "all"`, `exit == 0`, `outcome == "conforms"`, and one `--json` document with `data["target"] == "all"` and `data["by_type"]` keys `plans`, `prompts`, `research`), (b) a partial-stale fixture where `plans` is stale (`exit: 1`) while `prompts` and `research` are clean (`exit: 0`) (`rc == 1`, one `--agent` line with `exit == 1`, `outcome == "findings"`, `findings >= 1`, closing the false-clean terminal-record defect, and one `--json` document with `exit_code == 1`), and (c) human-mode `aw index all --check` invariance on clean and stale fixtures.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_index_check_agent_records.py` passes and exercises `aw index all --check` across `--agent`, `--json`, and human modes including mixed per-type exit codes.
  - Execution state: pending

- [ ] E-04 In `tests/test_index_write_agent_records.py`, add subprocess behavior tests for `aw index all` (write path) covering `--agent`, `--json`, and human audiences across (a) first run on a missing-index fixture (`rc == 0`, one `--agent` line with `target == "all"`, `exit == 0`, `outcome == "ok"`, `applied is True`, `changes == 6` in compact mode and 6 repo-relative paths in `--agent --verbose` and `--json`, with no `repo_root` key in `data` and no path leaks), (b) second run unchanged (`rc == 0`, one `--agent` line with `applied is False` and no `changes` key), (c) mixed-outcome fixture where `plans` and `prompts` write their indexes (`applied: True`) while `research` refuses regeneration on `frontmatter-invalid` (`rc == 1`, one `--agent` line with `exit == 1`, `outcome == "findings"`, `applied is True`, `complete is False`, and a `frontmatter-invalid` diagnostic, plus one `--json` document with `exit_code == 1`), and (d) human-mode `aw index all` invariance.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_index_write_agent_records.py` passes and verifies that `aw index all` never emits mismatched `exit: 0` records when any per-type backend exits `1`.
  - Execution state: pending

- [ ] E-05 Add a `CHANGELOG.md` entry under `## [Unreleased]` -> `### Fixed` describing the single aggregate `aw.agent/v1` and `--json` result for `aw index all` and `aw index all --check` (using no em or en dashes), and run the verification suite (`python3 -m pytest tests/test_index_check_agent_records.py tests/test_index_write_agent_records.py tests/test_agent_surface_conformance.py`, `python3 -m pytest`, and `python3 -m agent_workflows check all`).
  - Depends on: E-03, E-04
  - Expected outcome: `CHANGELOG.md` documents the fix cleanly and the full test suite and repository conformance checks pass with zero errors.
  - Execution state: pending

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
| F-04 | low | `agent_workflows/artifact_core.py` (`emit_index_check_result`, `emit_index_write_result`) | `emit_index_check_result` relies on `data["repo_root"]` for `Diagnostic.to_dict(repo_root)` / `CommandResult.to_agent_record` to strip `repo_root` from absolute `d.location` strings (such as `research_index.check_drift`'s `f"{d.file}:{d.line}"` dangling-citation locations), whereas `emit_index_write_result` omits `data["repo_root"]` (to satisfy `test_index_write_agent_records.py`'s `assertNotIn("repo_root", data)`). Normalizing `d.location` via `_schema.normalize_repo_path(d.location, repo_root)` when constructing `Diagnostic` in both helpers ensures repo-relative diagnostic locations without needing `repo_root` in `CommandResult.data`. |

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
   - Add `aggregate_index_results(results: Sequence[CommandResult], *, check: bool) -> CommandResult`:
     - Compute `exit_code = max((r.exit_code for r in results), default=0)`.
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
   - After the loop, when `collect_index_results` is true, import `from agent_workflows import artifact_core as _core`, build `cmd_res = _core.aggregate_index_results(index_results, check=bool(getattr(args, "check", False)))`, and `return get_renderer(ctx).emit(cmd_res, ctx)`.

3. **`tests/test_index_check_agent_records.py` and `tests/test_index_write_agent_records.py`**:
   - Add `aw index all --check` tests in `tests/test_index_check_agent_records.py` (clean, partial-stale where `plans` is stale and `research` is clean, and human invariance).
   - Add `aw index all` write tests in `tests/test_index_write_agent_records.py` (first-run creation, second-run no-op, mixed-outcome where `plans`/`prompts` write and `research` refuses with `exit: 1`, and human invariance).

4. **`CHANGELOG.md`**:
   - Add an entry under `## [Unreleased]` -> `### Fixed` documenting the single aggregate `aw.agent/v1` and `--json` output for `aw index all` and `aw index all --check`.

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

- Subprocess tests in `tests/test_index_check_agent_records.py` driving `aw index all --check` under `--agent`, `--json`, and human mode across clean and mixed/partial-stale fixtures.
- Subprocess tests in `tests/test_index_write_agent_records.py` driving `aw index all` under `--agent`, `--json`, and human mode across first-run, second-run unchanged, and mixed-outcome (`plans`/`prompts` succeed, `research` refuses with `exit: 1`) fixtures.
- Full conformance and unit test suite (`python3 -m pytest` and `python3 -m agent_workflows check all`).

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` Section 4 and `docs/cli-agent-protocol.md` already specify that single-shot commands emit one `result` record whose `exit` equals the process exit code, and `agent_workflows/command_surface.py` already declares `agent_record_kind="result"` for `index`. Only `CHANGELOG.md` requires an `[Unreleased]` entry.

## Open questions

### OQ-01: Should `aw index all [--check] --agent` emit one aggregate `kind: "result"` record (`target: "all"`) or three `kind: "item"` records followed by a terminal `kind: "summary"` record?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in favor of emitting **one aggregate `kind: "result"` record (`cmd: "index"`, `target: "all"`)** once at the `cli._run_noun_verb` dispatch boundary: (1) `agent_workflows/command_surface.py` declares `CommandDeclaration(command="index", ..., agent_record_kind="result")`; (2) `AgentRenderer.render_summary` (`kind: "summary"`) in `agent_workflows/renderers.py` only emits `total`/`emitted`/`omitted`/`complete` and cannot carry `applied`, `changes`, or `diagnostics`, which `docs/cli-output-contract.md` Section 11.3 requires on mutation verbs (`aw index all`); (3) `JsonRenderer.emit` (`--json`) serializes a single `CommandResult` via `result.to_dict()`, so a single aggregate `CommandResult` fixes both `--agent` and `--json` (`F-03`) through the single renderer boundary required by `docs/cli-output-contract.md` Section 2; and (4) every other cross-cutting `all` dispatcher (`aw rename all` and `aw group all` in `_run_noun_verb` per IPD `vfqjc0` E-03, and `aw check all` in `_run_check`) emits one aggregate `CommandResult` with `target: "all"`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/artifact_core.py` showing `_schema.normalize_repo_path(d.location, repo_root)` in `emit_index_check_result` and `emit_index_write_result`, `_index_result_sink` interception in both functions when `not ctx.is_human`, and the `aggregate_index_results` helper definition.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/cli.py` showing `_run_noun_verb` attaching `_index_result_sink` across `types` when `not emit_human and verb == "index" and len(types) > 1` and emitting `_core.aggregate_index_results(...)` once via `get_renderer(ctx).emit(cmd_res, ctx)`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Output of `python3 -m pytest tests/test_index_check_agent_records.py` showing all tests passing, including the new `aw index all --check` tests for `--agent`, `--json`, human mode, and partial-stale (`plans` stale, `prompts` and `research` clean) exit parity.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Output of `python3 -m pytest tests/test_index_write_agent_records.py` showing all tests passing, including the new `aw index all` write tests for `--agent`, `--json`, human mode, and mixed-outcome (`plans` and `prompts` succeed, `research` refuses with `exit: 1`) exit parity.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `git diff CHANGELOG.md` showing the new `[Unreleased]` -> `### Fixed` entry (with zero em/en dashes) plus pasted output of `python3 -m pytest` and `python3 -m agent_workflows check all` exiting `0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored to `to-review` status from backlog item `hu2wka` and awaits review and approval before execution. Upon execution and passing validation (`V-01` through `V-05`), finalize the plan via `aw ipd finalize 7i4zba`.
