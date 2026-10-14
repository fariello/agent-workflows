# IPD: Refuse aw index write path with cannot-run when records directory is missing

- Date: 2026-10-14
- Kind: child
- Concern: `aw index plans`, `aw index prompts`, `aw index research`, and `aw index all` crash on the write path (without `--check`) when the target records directory does not exist on disk yet: `scan_plans`, `scan_prompts`, and `_scan_docs` return `([], [])`, after which `json_path.write_text(new_json, encoding="utf-8")` in `plans_index.run_index`, `prompts_index.run_index`, and `research_index.run_index` raises an unhandled `FileNotFoundError` with exit `1`, a Python traceback on `stderr`, and `0` bytes on `stdout` under `--agent` and `--json`, violating `docs/cli-output-contract.md` Section 11.4.
- Scope: Add `emit_index_missing_dir_refusal` in `agent_workflows/artifact_core.py` to emit a structured `cannot-run` (`exit: 2`, `kind: "error"`, `outcome: "cannot-run"`, `applied: False`, `verified: False`, `complete: False`, `next: "aw install ."`) result across `--agent`, `--json`, human (`stderr`), and `quiet=True` callers; guard the write branch of `plans_index.run_index`, `prompts_index.run_index`, and `research_index.run_index` when `not <dir>.is_dir()`; add subprocess and in-process (`quiet=True`) behavior tests in `tests/test_index_write_agent_records.py`; and record the fix in `CHANGELOG.md`.
- Scope-Paths: agent_workflows/artifact_core.py, agent_workflows/plans_index.py, agent_workflows/prompts_index.py, agent_workflows/research_index.py, tests/test_index_write_agent_records.py, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: bug
- Priority: low
- From-Backlog: o6cbp7
- Blocks-Release: next
- Set: indexmissdir
- Order: 1
- Highest E allocated: 04
- Author: Antigravity
- Id: fbdxmh

## Workflow history
- 2026-10-14 to-review (aw set): status set to to-review

- 2026-10-14 draft (Antigravity): created from backlog item `o6cbp7`.

## Goal

Prevent `aw index plans`, `aw index prompts`, `aw index research`, and `aw index all` from crashing with an unhandled `FileNotFoundError` traceback when a target records directory does not exist on disk yet, refusing instead at exit code `2` (`cannot-run`) with a schema-valid `aw.agent/v1` `kind: "error"` record under `--agent`, a structured `cannot-run` `CommandResult` under `--json`, a clear diagnostic on `stderr` in human mode, and zero directory creation or home-directory pollution.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Shared missing-directory refusal helper and index write-path guards

- [ ] E-01 In `agent_workflows/artifact_core.py`, add `emit_index_missing_dir_refusal(args: Any, repo_root: Path, *, target: str, default_rel_dir: str) -> int` after `emit_index_write_result` so that: (a) when `getattr(args, "quiet", False)` is truthy it returns `2` immediately without emitting output; (b) otherwise it constructs a `Diagnostic(location=default_rel_dir, rule="records-dir-missing", detail=f"{default_rel_dir} does not exist; run 'aw install .'", severity="error", fix="aw install .")` and a `CommandResult(command="index", target=target, status="cannot-run", exit_code=2, summary=f"refusing to write {target} index: {default_rel_dir} does not exist", applied=False, diagnostics=[diag], next_actions=[NextAction(command="aw install .", description="initialize repository records directories")], data={"target": target, "index_dir": default_rel_dir}, verified=False, complete=False)`; (c) in human mode (`ctx.is_human`) it writes `f"error: {default_rel_dir}: directory does not exist; run 'aw install .'\n"` to `ctx.stderr` and returns `2`; (d) in machine modes (`not ctx.is_human`), if `isinstance(getattr(args, "_index_result_sink", None), list)` is true it appends `result` to `args._index_result_sink` and returns `2`, and otherwise returns `get_renderer(ctx).emit(result, ctx)`; and (e) if `aggregate_index_results` is present in `agent_workflows/artifact_core.py` (from sibling plan `7i4zba`), ensure its `check=False` branch maps `exit_code == 2` to `status = "cannot-run"`, `verified = all(r.verified for r in results)`, and propagates deduplicated `next_actions` from `results`.
  - Depends on: none
  - Expected outcome: `artifact_core.emit_index_missing_dir_refusal` deterministically returns `2` across `--agent`, `--json`, human mode, and `quiet=True` without leaking any absolute or home-directory paths.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/plans_index.py` (`run_index`), `agent_workflows/prompts_index.py` (`run_index`), and `agent_workflows/research_index.py` (`run_index`), add a missing-directory guard immediately after the `if getattr(args, "check", False):` block on the write branch: in `plans_index.run_index`, `if not plans_dir.is_dir(): return _core.emit_index_missing_dir_refusal(args, repo_root, target="plans", default_rel_dir=".aw/records/plans")`; in `prompts_index.run_index`, `if not prompts_dir.is_dir(): return _core.emit_index_missing_dir_refusal(args, repo_root, target="prompts", default_rel_dir=".aw/records/prompts")`; and in `research_index.run_index`, `if not research_root.is_dir(): return _core.emit_index_missing_dir_refusal(args, repo_root, target="research", default_rel_dir=".aw/records/research")`.
  - Depends on: E-01
  - Expected outcome: Invoking `aw index plans`, `aw index prompts`, `aw index research`, or `aw index all` (without `--check`) when the target records directory does not exist on disk returns exit code `2` via `emit_index_missing_dir_refusal` before `json_path.write_text` is reached, while `--check` behavior remains completely unchanged.
  - Execution state: pending

### Task group 2: Subprocess and in-process behavior tests and changelog

- [ ] E-03 In `tests/test_index_write_agent_records.py`, add behavioral tests covering missing records directories across all three verbs (`plans`, `prompts`, `research`) and `all`: (a) subprocess `--agent` tests in a fresh `git init` repository (with isolated `HOME` in temp dir) verifying each `aw index <verb> --agent` exits `2` with empty `stderr` (zero traceback), emits a single line that passes `agent_schema.validate_agent_record(rec) == []` with `kind == "error"`, `cmd == "index"`, `target == <verb>`, `outcome == "cannot-run"`, `exit == 2`, `verified is False`, `complete is False`, `applied is False`, `next == "aw install ."`, a `records-dir-missing` diagnostic at `.aw/records/<verb>`, and creates no directories under either the repo or `HOME`; (b) subprocess `--agent` test for `aw index all --agent` in a repository where `.aw/records/plans` exists and `.aw/records/prompts` and `.aw/records/research` are missing (the exact `o6cbp7` reproduction scenario), verifying `returncode == 2`, empty `stderr`, valid `aw.agent/v1` record(s) on `stdout`, and a terminal record (`lines[-1]`) with `kind == "error"`, `outcome == "cannot-run"`, `exit == 2`, `verified is False`, `complete is False`; (c) subprocess `--json` and human-mode tests for each verb when the directory is missing (`returncode == 2`, valid JSON with `status == "cannot-run"` and `exit_code == 2` under `--json`, and `stderr` naming `.aw/records/<verb>` and `aw install .` with empty `stdout` in human mode); and (d) in-process `quiet=True` tests calling `plans_index.run_index`, `prompts_index.run_index`, and `research_index.run_index` with `quiet=True` on a missing directory and asserting return value `2` with `0` bytes on `stdout` and `stderr`.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest tests/test_index_write_agent_records.py` passes with all new missing-directory refusal tests green.
  - Execution state: pending

- [ ] E-04 Add a `CHANGELOG.md` entry under `## [Unreleased]` -> `### Fixed` describing the `cannot-run` (exit `2`) refusal when `aw index <plans|prompts|research|all>` is invoked on the write path without an existing records directory (using no em or en dashes), and run the verification suite (`python3 -m pytest tests/test_index_write_agent_records.py tests/test_nv_backend_args_climb.py`, `python3 -m pytest`, and `python3 -m agent_workflows check all`).
  - Depends on: E-03
  - Expected outcome: `CHANGELOG.md` documents the fix with zero em/en dashes and the test suite and `aw check all` pass with zero errors.
  - Execution state: pending

## Project conventions discovered (Step 0)

- **Fatal failure and `cannot-run` contract (`docs/cli-output-contract.md` Section 11.4)**: "Handlers MUST NEVER catch and swallow unexpected exceptions or return exit code `0` on fatal failure." Under `aw.agent/v1`, a missing prerequisite state that prevents a command from running maps to exit code `2` with a `kind: "error"`, `outcome: "cannot-run"`, `verified: false`, `complete: false` record (implemented via `CommandResult.to_agent_record` in `agent_workflows/result_types.py` around `if is_error:`).
- **Write verbs must not silently create unrequested directories (Set `dirsilent`, IPDs `lmyeas` OQ-01 and `rlhmt9` F-05)**: In `lmyeas` (`.aw/records/plans/executed/20261011-dirsilent-02-lmyeas-remove-import-time-and-read-only-directory-creation-in-comms.ipd.md` around `OQ-01`), write verbs must fail loudly and locally when the target records tree has not been initialized rather than silently creating directories on demand.
- **`aw install` already creates all three records directories (`agent_workflows/engine.py`)**: `engine.install_into_repo` (`agent_workflows/engine.py` around `ensure_plans_readmes(target_root)` and `create_setup_artifacts(target_root)`) creates `.aw/records/plans/`, `.aw/records/prompts/`, and `.aw/records/research/` (with `README.md` and `.gitkeep` files) during repository installation. A missing records directory on `aw index <type>` indicates an uninitialized repository or an unconfigured `--dir <subdir>`.
- **Why `mkdir(parents=True)` in `run_index` would corrupt `$HOME/.aw/projects/` and shadow in-repo records (`agent_workflows/plans_index.py`, `agent_workflows/research_index.py`)**: In `plans_index._dirs` (`agent_workflows/plans_index.py` around `resolve_record_path("plans", target_repo=str(repo_root))`) and `research_index._roots` (`agent_workflows/research_index.py` around `resolve_record_path("research", target_repo=str(repo_root))`), when a repository has no `.aw/config/project.json` (or when `--dir` points at a non-root subdirectory), `resolve_project_context` defaults to `records_backend = "home"` and returns `<aw_home>/projects/<slug>-<hash>/records/<type>`. Both `_dirs` and `_roots` only fall back to `repo_root / ".aw" / "records" / <type>` when `not <dir>.is_dir()`. If `run_index` called `mkdir(parents=True)` on the resolved path, it would (1) create unrequested directories inside `$HOME/.aw/projects/` on an unconfigured repo, (2) permanently shadow any `.aw/records/<type>` created later in the repo because `<aw_home>/projects/.../records/<type>.is_dir()` would now be `True`, and (3) leak the absolute `$HOME/.aw/projects/...` path into `data["index_dir"]` under `--json` because `index_dir.relative_to(repo_root)` raises `ValueError` in `artifact_core.emit_index_write_result`.
- **Legacy write-sink static check (`agent_workflows/record_producers.py`)**: `discover_legacy_write_sinks` (`agent_workflows/record_producers.py` around `def discover_legacy_write_sinks`) scans `agent_workflows/*.py` for lines containing `.agents/` alongside write markers (`.write_text(`, `.mkdir(`, `open(`, etc.). No new code in `artifact_core.py`, `plans_index.py`, `prompts_index.py`, or `research_index.py` may place `.agents/` on a line with a write marker.
- **Internal `quiet=True` callers of `run_index`**: Nine internal call sites invoke `run_index(argparse.Namespace(..., quiet=True))` after mutating an existing artifact (`artifact_adopt.py`, `artifact_rename.py`, `ipd_lifecycle.py`, `plans_refs.py`, `research_refs.py`, `research_cmd.py`, `status_set.py`). In all nine callers the artifact's directory already exists on disk; when `quiet=True` is passed on a missing directory, returning `2` without printing preserves the `quiet=True` contract.

## Findings

| ID | Severity | Location | Finding |
| :--- | :--- | :--- | :--- |
| F-01 | high | `agent_workflows/prompts_index.py` (`run_index`), `agent_workflows/research_index.py` (`run_index`), `agent_workflows/plans_index.py` (`run_index`) | On the write branch (`not getattr(args, "check", False)`), all three `run_index` functions call `scan_plans` / `scan_prompts` / `_scan_docs` (which return `([], [])` when the directory does not exist) and then immediately execute `json_path.write_text(new_json, encoding="utf-8")` at `prompts_dir / INDEX_JSON`, `research_root / INDEX_JSON`, and `plans_dir / INDEX_JSON`. When the directory is absent, `write_text` raises an unhandled `FileNotFoundError`, exiting `1` with a Python traceback on `stderr` and `0` bytes on `stdout` under `--agent`, `--json`, and human mode. |
| F-02 | high | `agent_workflows/cli.py` (`_run_noun_verb`) | Because `_run_noun_verb` loops `for t in types:` across `("plans", "prompts", "research")` on `aw index all`, if any single records directory is missing (for example in a repository that has `.aw/records/plans` but not `.aw/records/prompts` or `.aw/records/research`, as measured when filing `o6cbp7`), `aw index all --agent` crashes mid-loop on the first missing directory with an unhandled `FileNotFoundError` traceback. |
| F-03 | medium | `agent_workflows/plans_index.py` (`_dirs`), `agent_workflows/research_index.py` (`_roots`), `agent_workflows/artifact_core.py` (`emit_index_write_result`) | In an unconfigured `git init` repository without `.aw/config/project.json`, `plans_index._dirs` and `research_index._roots` resolve `plans_dir` / `research_root` via `resolve_record_path` to `<aw_home>/projects/<slug>-<hash>/records/<type>` when neither `.agents/...` nor `.aw/records/...` exists on disk. Using a canonical repo-relative `default_rel_dir` (`.aw/records/<type>`) in `emit_index_missing_dir_refusal` avoids exposing the `<aw_home>/projects/...` fallback path in diagnostics or `--json` `data["index_dir"]`. |

## Proposed changes (ordered, validatable)

1. **`agent_workflows/artifact_core.py` (`emit_index_missing_dir_refusal`)**:
   - Add `emit_index_missing_dir_refusal(args: Any, repo_root: Path, *, target: str, default_rel_dir: str) -> int` immediately after `emit_index_write_result`:
     ```python
     def emit_index_missing_dir_refusal(
         args: Any,
         repo_root: Path,
         *,
         target: str,
         default_rel_dir: str,
     ) -> int:
         """Refuse an index write invocation with exit code 2 (cannot-run) when the records directory does not exist."""
         if getattr(args, "quiet", False):
             return 2
         from agent_workflows.renderers import get_renderer
         from agent_workflows.result_types import (
             CommandResult,
             Diagnostic,
             NextAction,
             select_output,
         )

         ctx = select_output(args)
         detail = f"{default_rel_dir} does not exist; run 'aw install .'"
         if ctx.is_human:
             ctx.stderr.write(f"error: {default_rel_dir}: directory does not exist; run 'aw install .'\n")
             return 2

         diag = Diagnostic(
             location=default_rel_dir,
             rule="records-dir-missing",
             detail=detail,
             severity="error",
             fix="aw install .",
         )
         result = CommandResult(
             command="index",
             target=target,
             status="cannot-run",
             exit_code=2,
             summary=f"refusing to write {target} index: {default_rel_dir} does not exist",
             applied=False,
             diagnostics=[diag],
             next_actions=[
                 NextAction(
                     command="aw install .",
                     description="initialize repository records directories",
                 )
             ],
             data={
                 "target": target,
                 "index_dir": default_rel_dir,
             },
             verified=False,
             complete=False,
         )
         sink = getattr(args, "_index_result_sink", None)
         if isinstance(sink, list):
             sink.append(result)
             return result.exit_code
         return get_renderer(ctx).emit(result, ctx)
     ```
   - If `aggregate_index_results` is already present in `agent_workflows/artifact_core.py` (from sibling plan `7i4zba`), ensure its `check=False` branch sets `status = "cannot-run"` when `exit_code == 2` (or `any(r.status == "cannot-run" for r in results)`), `verified = all(r.verified for r in results)`, and propagates deduplicated `next_actions` from `results`.

2. **`agent_workflows/plans_index.py` (`run_index`), `agent_workflows/prompts_index.py` (`run_index`), and `agent_workflows/research_index.py` (`run_index`)**:
   - In `plans_index.run_index`, immediately after the `if getattr(args, "check", False):` block (before `entries, drift = scan_plans(plans_dir)`):
     ```python
     if not plans_dir.is_dir():
         return _core.emit_index_missing_dir_refusal(
             args,
             repo_root,
             target="plans",
             default_rel_dir=".aw/records/plans",
         )
     ```
   - In `prompts_index.run_index`, immediately after the `if getattr(args, "check", False):` block (before `entries, drift = scan_prompts(prompts_dir)`):
     ```python
     if not prompts_dir.is_dir():
         return _core.emit_index_missing_dir_refusal(
             args,
             repo_root,
             target="prompts",
             default_rel_dir=".aw/records/prompts",
         )
     ```
   - In `research_index.run_index`, immediately after the `if getattr(args, "check", False):` block (before `entries, drift = _scan_docs(research_root, repo_root=repo_root)`):
     ```python
     if not research_root.is_dir():
         return _core.emit_index_missing_dir_refusal(
             args,
             repo_root,
             target="research",
             default_rel_dir=".aw/records/research",
         )
     ```

3. **`tests/test_index_write_agent_records.py`**:
   - Add missing-directory refusal tests covering `--agent`, `--json`, human mode, `aw index all --agent`, and in-process `quiet=True` calls across `plans`, `prompts`, and `research`, verifying exit code `2`, `kind == "error"`, `outcome == "cannot-run"`, `applied is False`, `verified is False`, `complete is False`, `next == "aw install ."`, diagnostic rule `"records-dir-missing"`, zero traceback on `stderr`, and zero directory creation in the repo or `HOME`.

4. **`CHANGELOG.md`**:
   - Add an entry under `## [Unreleased]` -> `### Fixed` documenting that `aw index plans`, `aw index prompts`, `aw index research`, and `aw index all` now refuse with exit code `2` (`cannot-run`) and a structured `aw.agent/v1` `error` record when the target records directory does not exist instead of crashing with `FileNotFoundError`.

## Deferred / out of scope (with reason)

- **Single aggregate `aw.agent/v1` and `--json` record for `aw index all` (`hu2wka` / `7i4zba`)**: Emitting one aggregate `CommandResult` with `target="all"` across the `for t in types:` loop in `cli._run_noun_verb` is owned by sibling plan `7i4zba` (graduating `hu2wka`). `emit_index_missing_dir_refusal` in this plan already supports `_index_result_sink` so both plans compose cleanly in either execution order.
  - Carrier: 7i4zba

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- Subprocess behavior tests in `tests/test_index_write_agent_records.py` driving `aw index plans`, `aw index prompts`, `aw index research`, and `aw index all` in repositories where the target records directories do not exist across `--agent`, `--json`, and human audiences, plus in-process `quiet=True` unit tests.
- Existing climb and non-project `--check` regression tests in `tests/test_nv_backend_args_climb.py`.
- Full test suite (`python3 -m pytest`) and repository conformance checks (`python3 -m agent_workflows check all`).

## Spec / documentation sync

- N/A with reason: `docs/cli-output-contract.md` Section 11.4 already specifies exit code `2` (`cannot-run`) with a `kind: "error"` record when a command cannot run due to missing prerequisites. Only `CHANGELOG.md` requires an `[Unreleased]` entry.

## Open questions

### OQ-01: When the target records directory does not exist on an `aw index <plans|prompts|research>` write invocation, should `run_index` create the directory (`mkdir`) and write an empty index, or refuse with exit code `2` (`cannot-run`)?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in favor of **refusing with exit code `2` (`cannot-run`) and a `kind: "error"` record under `--agent` (and a structured `cannot-run` `CommandResult` under `--json` and `stderr` message in human mode)**: (1) `engine.install_into_repo` (`agent_workflows/engine.py` around `ensure_plans_readmes` and `create_setup_artifacts`) already creates `.aw/records/plans/`, `.aw/records/prompts/`, and `.aw/records/research/` during `aw install` / `aw setup`, so a missing directory only occurs in an uninitialized repository, an unconfigured `--dir <subdir>`, or a partially constructed tree; (2) in an unconfigured `git init` repository (no `.aw/config/project.json`) or `--dir <subdir>`, `plans_index._dirs` and `research_index._roots` resolve via `resolve_record_path` (`records_backend = "home"` default in `project_context.py`) to `<aw_home>/projects/<slug>-<hash>/records/<type>`, so calling `mkdir(parents=True)` would silently pollute `$HOME/.aw/projects/`, permanently shadow any `.aw/records/<type>` created later in the repo (because `_dirs` and `_roots` gate their repo-local fallback on `if not <dir>.is_dir()`), and leak the absolute `$HOME/.aw/projects/...` path in `data["index_dir"]` under `--json`; and (3) refusing with `cannot-run` (exit `2`) and `next: "aw install ."` matches `docs/cli-output-contract.md` Section 11.4 and Set `dirsilent` (`lmyeas` OQ-01, `rlhmt9` F-05).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: `git diff agent_workflows/artifact_core.py` showing `emit_index_missing_dir_refusal` returning `2` when `quiet=True`, emitting an `error:` message to `ctx.stderr` in human mode, and constructing a `CommandResult` with `status="cannot-run"`, `exit_code=2`, `applied=False`, `verified=False`, `complete=False`, `Diagnostic(rule="records-dir-missing")`, and `NextAction(command="aw install .")` for `--agent` and `--json` (with `_index_result_sink` support).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `git diff agent_workflows/plans_index.py agent_workflows/prompts_index.py agent_workflows/research_index.py` showing the `if not <dir>.is_dir(): return _core.emit_index_missing_dir_refusal(...)` guard immediately after the `if getattr(args, "check", False):` block in all three `run_index` functions.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Pasted output of `python3 -m pytest tests/test_index_write_agent_records.py` showing all tests passing, including the new missing-directory refusal tests across `--agent`, `--json`, human mode, `aw index all --agent`, and `quiet=True`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `git diff CHANGELOG.md` showing the new `[Unreleased]` -> `### Fixed` entry (with zero em/en dashes) plus pasted output of `python3 -m pytest` and `python3 -m agent_workflows check all` exiting `0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored to `to-review` status from backlog item `o6cbp7` and awaits review and approval before execution. Upon execution and passing validation (`V-01` through `V-04`), finalize the plan via `aw ipd finalize fbdxmh`.
