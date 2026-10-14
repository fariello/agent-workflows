# IPD: Contain incidental agent-turn writes to AW_HOME while preserving home-backend records

- Date: 2026-10-14
- Kind: child
- Concern: Agent-turn `AW_HOME` containment and selective home-backend pass-through across `oc_runipd.py` and `agy_runipd.py`.
- Scope: Investigate and measure what execute turns write to `AW_HOME` (`~/.aw`), fix `project_registry.find_project` to honor `AW_HOME` when `aw_home` is omitted, introduce a selective per-turn `AW_HOME` sandbox (`prepare_agent_aw_home`, `reconcile_agent_aw_home`, `report_discarded_aw_home`) in `runner_shared.py` that isolates `<AW_HOME>/config/registry.json` and incidental `<AW_HOME>/projects/<other_pid>/` writes (including scratch `/tmp/...` run-analytics caches) while symlinking `<AW_HOME>/projects/<active_pid>/` through to the real `AW_HOME` when the active repository uses `records_backend: home` or `delivery_mode: clean-delta`, wire both runners (`oc_runipd.py`, `agy_runipd.py`), add regression tests, and update `CHANGELOG.md` and `docs/security.md`.
- Scope-Paths: agent_workflows/project_registry.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_agent_aw_home_containment.py, CHANGELOG.md, docs/security.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: followup
- Priority: low
- From-Backlog: s4pys7
- Set: s4pys7 (Agent-turn AW_HOME containment)
- Order: 1
- Highest E allocated: 07
- Author: Antigravity
- Id: 1vwjdl

## Workflow history
- 2026-10-14 to-review (aw set): Review-ready IPD for graduating backlog item s4pys7 (agent-turn AW_HOME containment).

- 2026-10-14 draft (Antigravity): created from backlog `s4pys7`.

## Goal

Prevent execute turns under `aw oc run` and `aw agy run` from mutating the operator's `~/.aw/config/registry.json` or polluting `~/.aw/projects/` with incidental scratch project directories and run-analytics caches, while preserving transparent read/write pass-through to `~/.aw/projects/<active_pid>/` when the active repository uses `records_backend: home` or `delivery_mode: clean-delta`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Honor AW_HOME in project_registry.find_project

- [ ] E-01 Update `project_registry.find_project` (`agent_workflows/project_registry.py:303`) so that when `aw_home` is `None`, it resolves `base_dir` via `os.environ.get("AW_HOME") or os.path.expanduser("~/.aw")` (matching `project_registry.get_registry_path` at `agent_workflows/project_registry.py:72`) before running the reverse scan over `projects/*/config/project.json`.
  - Depends on: none
  - Expected outcome: Calling `project_registry.find_project(project_id)` with `aw_home=None` while `AW_HOME` is set in `os.environ` inspects `<AW_HOME>/config/registry.json` and `<AW_HOME>/projects/*/config/project.json` inside the `AW_HOME` directory rather than escaping to `os.path.expanduser("~/.aw")`.
  - Execution state: pending

### Task group 2: Selective per-turn AW_HOME sandbox in runner_shared.py

- [ ] E-02 Add `AW_HOME_ENV`, `AgentAwHome`, `prepare_agent_aw_home`, `reconcile_agent_aw_home`, and `report_discarded_aw_home` to `agent_workflows/runner_shared.py` immediately after `runner_shared.report_discarded_user_config` (`agent_workflows/runner_shared.py:47349`), implementing a per-turn seeded `AW_HOME` sandbox under `<run_dir>/agent-aw-home/<NN>-<id6>-attempt-<N>[-<suffix>]/` that copies `<real_aw_home>/config/registry.json`, symlinks `<sandbox>/projects/<active_pid>` (and the worktree-derived project id when `agent_dir` differs) to `<real_aw_home>/projects/<active_pid>` when the active repository is configured to use `AW_HOME` (`ctx.records_backend == "home"` or `ctx.delivery_mode == "clean-delta"`), and at turn exit unlinks those symlinks, records any incidental changes to `config/registry.json` or non-linked `projects/<other_pid>/` directories as `agent-aw-home-discarded` events in `<run_dir>/events.jsonl` (without values), and removes the sandbox.
  - Depends on: E-01
  - Expected outcome: `runner_shared.prepare_agent_aw_home`, `runner_shared.reconcile_agent_aw_home`, and `runner_shared.report_discarded_aw_home` are importable and isolate `<AW_HOME>/config/registry.json` and non-linked `<AW_HOME>/projects/<other_pid>/` writes while passing through writes to `<AW_HOME>/projects/<active_pid>/` when the active repo uses `AW_HOME`.
  - Execution state: pending

### Task group 3: Runner integration (oc_runipd.py and agy_runipd.py)

- [ ] E-03 Wire `prepare_agent_aw_home`, `reconcile_agent_aw_home`, and `report_discarded_aw_home` into `agent_workflows/oc_runipd.py` inside `oc_runipd._execute_single_attempt` (`agent_workflows/oc_runipd.py:1399`) and `oc_runipd._run_batch` (`agent_workflows/oc_runipd.py:4463`), setting `child_env["AW_HOME"]` to the per-turn sandbox path (or popping `AW_HOME` if preparation returns `None`), reconciling in the outer `finally` block after `process.wait()` (`oc_runipd._execute_single_attempt` at `agent_workflows/oc_runipd.py:1873`) with stderr warnings (`  ! IPD <id6>: agent changed AW_HOME <file> (<keys>); change DISCARDED, your AW_HOME is unchanged`), and printing the summary line (`Agent AW_HOME changes discarded: <n> (...)`) at run end.
  - Depends on: E-02
  - Expected outcome: Every OpenCode agent turn launched via `oc_runipd._execute_single_attempt` receives `AW_HOME` pointing at its per-turn `agent-aw-home` directory, reconciles and discards incidental `AW_HOME` writes in the outer `finally` block after `process.wait()`, and reports discarded changes at the end of `_run_batch`.
  - Execution state: pending

- [ ] E-04 Wire `prepare_agent_aw_home`, `reconcile_agent_aw_home`, and `report_discarded_aw_home` into `agent_workflows/agy_runipd.py` inside `agy_runipd._execute_single_attempt` (`agent_workflows/agy_runipd.py:678`) and `agy_runipd._run_batch` (`agent_workflows/agy_runipd.py:2169`), setting `child_env["AW_HOME"]` to the per-turn sandbox path (or popping `AW_HOME` if preparation returns `None`), reconciling in the outer `finally` block after `process.wait()` (`agy_runipd._execute_single_attempt` at `agent_workflows/agy_runipd.py:1007`) with stderr warnings, and printing the summary line at run end.
  - Depends on: E-02
  - Expected outcome: Every Antigravity agent turn launched via `agy_runipd._execute_single_attempt` receives `AW_HOME` pointing at its per-turn `agent-aw-home` directory, reconciles and discards incidental `AW_HOME` writes in the outer `finally` block after `process.wait()`, and reports discarded changes at the end of `_run_batch`.
  - Execution state: pending

### Task group 4: Regression tests and documentation

- [ ] E-05 Create `tests/test_agent_aw_home_containment.py` testing: (1) seeding `<real_aw_home>/config/registry.json` into the sandbox and discarding mutations/additions/deletions to `config/registry.json` with `agent-aw-home-discarded` events containing key names only and never secret values; (2) discarding incidental `projects/<scratch_pid>/` directories (such as bare temp-dir `turn_telemetry` / `run_analytics_cache` writes or `aw install <tmp> --preset completely-clean-target`) without polluting `<real_aw_home>/projects/`; (3) preserving writes to `<real_aw_home>/projects/<active_pid>/` when the active repository uses `records_backend: home` or `delivery_mode: clean-delta` (both via the main checkout and via a lane worktree `agent_dir`) while still discarding `config/registry.json` and non-active `projects/<other_pid>/` mutations; (4) `project_registry.find_project` honoring `AW_HOME` from `os.environ` when `aw_home=None`; and (5) end-to-end `_execute_single_attempt` integration in both `oc_runipd` and `agy_runipd`.
  - Depends on: E-03, E-04
  - Expected outcome: `python3 -m pytest tests/test_agent_aw_home_containment.py tests/test_agent_user_config_containment.py` passes with 0 failures.
  - Execution state: pending

- [ ] E-06 Update `docs/security.md` (`"8. Agent turns contain user-config writes."` at `docs/security.md:40`) and `CHANGELOG.md` (`## [Unreleased]`) to document per-turn `AW_HOME` containment (`prepare_agent_aw_home`, `reconcile_agent_aw_home`, `report_discarded_aw_home`), selective `<AW_HOME>/projects/<active_pid>/` pass-through for `records_backend: home` / `delivery_mode: clean-delta` repositories, and the honest threat-model limit (`AW_HOME` is an environment selector, not an OS-level boundary).
  - Depends on: E-03, E-04
  - Expected outcome: `docs/security.md` and `CHANGELOG.md` accurately describe the per-turn `AW_HOME` sandbox, selective home-backend pass-through, discarded-write reporting, and environment-selector limitation with no em or en dashes in user-facing prose.
  - Execution state: pending

- [ ] E-07 Run the full test suite (`python3 -m pytest`) and the leak sanitizer (`aw sanitize --agent`) to verify zero regressions and zero local leaks.
  - Depends on: E-05, E-06
  - Expected outcome: `python3 -m pytest` passes and `aw sanitize --agent` reports `"status": "pass"` with exit code 0.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Predecessor plan `9y27t2` (`.aw/records/plans/executed/20261012-btw02e-01-9y27t2-contain-agent-turn-writes-to-the-operator-s-user-config.ipd.md`) established the per-turn environment-sandbox pattern in `agent_workflows/runner_shared.py`: `runner_shared.prepare_agent_user_config` (`agent_workflows/runner_shared.py:47182`), `runner_shared.reconcile_agent_user_config` (`agent_workflows/runner_shared.py:47244`), and `runner_shared.report_discarded_user_config` (`agent_workflows/runner_shared.py:47349`), wired into `oc_runipd._execute_single_attempt` (`agent_workflows/oc_runipd.py:1399`) and `agy_runipd._execute_single_attempt` (`agent_workflows/agy_runipd.py:678`).
- Both runners reconcile per-turn sandboxes in the outer `finally` block AFTER `process.wait()` in `oc_runipd._execute_single_attempt` (`agent_workflows/oc_runipd.py:1866`) and `agy_runipd._execute_single_attempt` (`agent_workflows/agy_runipd.py:1001`) so a timed-out or interrupted child process cannot race `shutil.rmtree` or write after reconciliation.
- Discarded sandbox mutations are logged to `<run_dir>/events.jsonl` via `runner_shared._append_jsonl` (`agent_workflows/runner_shared.py:47337`) recording only relative file/subtree identifiers, change kind (`added` | `modified` | `removed`), and top-level key/section names (`keys`), never secret or path values.
- `conftest._restore_home_sandbox` (`conftest.py:228`) overrides `AW_HOME`, `AW_CONFIG_DIR`, `HOME`, and `XDG_CONFIG_HOME` during `pytest` runs; tests that exercise `prepare_agent_aw_home` directly pass an explicit `source_dir` or monkeypatch `AW_HOME` to a test-owned directory.
- User-facing prose in `CHANGELOG.md` and `docs/security.md` must contain no em or en dashes (`GEMINI.md` Rule 3).

## Findings

| ID | Category | Location / Symbol | Observation & Empirical Measurement |
|---|---|---|---|
| F-01 | Empirical baseline (normal execute turns) | `config.get_aw_home` (`agent_workflows/config.py:100`), `conftest._restore_home_sandbox` (`conftest.py:239`) | Running normal `aw` CLI commands (`aw status`, `aw doctor`, `aw attention`, `aw find plans`, `aw ipd lint`, `aw check release-gates`, `aw project status`, `aw context`) against a `records_backend: repository` repo with a fresh `AW_HOME` writes **zero files** (`[]`) under `AW_HOME`. Running `python3 -m pytest` inside an agent turn also writes **zero files** to the inherited `AW_HOME` because `conftest._restore_home_sandbox` (`conftest.py:228`) unconditionally overrides `os.environ["AW_HOME"] = _AW_TEST_SANDBOX` at import time and around every test. |
| F-02 | Complete census of `AW_HOME` layout | `project_registry.get_registry_path` (`agent_workflows/project_registry.py:63`), `project_context._resolve_home_dir` (`agent_workflows/project_context.py:259`), `storage.init_storage` (`agent_workflows/storage.py:265`), `run_analytics_cache.get_cache_dir` (`agent_workflows/run_analytics_cache.py:29`) | `AW_HOME` contains exactly two top-level subtrees: (1) `<AW_HOME>/config/registry.json` (plus `registry.json.lock` during atomic writes), which stores the operator's global machine-wide project registry (`projects` map of `project_id` to `target_paths`, `aw_home_path`, `delivery_mode`, `records_backend`, `timestamps`); and (2) `<AW_HOME>/projects/<project_id>/`, which holds per-project directories (`config/project.json`, `records/`, `state/`, `work/`, and `records/runs/analytics/cache/`). |
| F-03 | Incidental agent-turn writes to `<AW_HOME>/config/registry.json` | `project_registry.register_or_update_project` (`agent_workflows/project_registry.py:209`), `cli._run_project_attach` (`agent_workflows/cli.py:3455`), `cli._run_project_move` (`agent_workflows/cli.py:3625`) | An agent turn never legitimately needs to mutate the operator's global `<AW_HOME>/config/registry.json`. However, an agent running an ad-hoc shell probe or `V-*` verification command that invokes `aw project attach`, `aw project move`, `aw install <tmp> --preset completely-clean-target`, or `project_registry.register_or_update_project` without overriding `AW_HOME` writes scratch project entries or ephemeral `.aw/worktrees/<id6>` paths directly into the operator's real `~/.aw/config/registry.json`. |
| F-04 | Incidental agent-turn writes to `<AW_HOME>/projects/<other_pid>/` (including scratch run-analytics caches) | `project_context.resolve_project_context` (`agent_workflows/project_context.py:1171`), `runner_shared.turn_telemetry` (`agent_workflows/runner_shared.py:23813`), `run_analytics_cache.update_cache` (`agent_workflows/run_analytics_cache.py:420`), `runner_shared.mint_run_dir` (`agent_workflows/runner_shared.py:47435`) | `project_context.resolve_project_context` defaults any unconfigured directory (`not ctx.is_configured`, such as a bare `mktemp -d` or `tempfile.TemporaryDirectory()` used in an agent's shell one-liner or `python3 -m unittest` probe) to `records_backend = "home"` and `project_id = _derive_project_id(target_repo)` (`<basename>-<sha256[:6]>`). Consequently, calling `turn_telemetry`, `run_analytics_cache.update_cache`, `mint_run_dir`, or `storage.init_storage` against a scratch temp directory `scratch_repo` creates `projects/scratch_repo-<hash>/records/runs/analytics/cache/salt` (verified empirically: `['projects', 'projects/scratch_repo-b28b90', ..., 'projects/scratch_repo-b28b90/records/runs/analytics/cache/salt']`) inside the operator's real `~/.aw/projects/`. |
| F-05 | Legitimate agent-turn writes to `<AW_HOME>/projects/<active_pid>/` | `project_context.resolve_project_context` (`agent_workflows/project_context.py:926`), `storage.resolve_records_root` (`agent_workflows/storage.py:72`) | When the active repository being operated on by the runner is configured (`ctx.is_configured`) and uses `AW_HOME` (`ctx.records_backend == "home"` or `ctx.delivery_mode == "clean-delta"`, or any path in `ctx.logical_roots.values()` resides under `ctx.effective_aw_home`), the agent turn legitimately reads and writes plans, specs, research, backlog items, and state under `<real_aw_home>/projects/<ctx.project_id>/`. A blanket discard of `AW_HOME` would destroy legitimate record mutations in home-backend repositories. |
| F-06 | Selective per-turn `AW_HOME` sandbox preserves home-backend records while containing all incidental writes | `runner_shared.prepare_agent_user_config` (`agent_workflows/runner_shared.py:47182`), `project_context._derive_project_id` (`agent_workflows/project_context.py:141`) | Seeding a per-turn directory `<run_dir>/agent-aw-home/<NN>-<id6>-attempt-<N>[-<suffix>]/` with a copy of `<real_aw_home>/config/registry.json` and an empty `projects/` directory, and symlinking `<sandbox>/projects/<ctx.project_id> -> <real_aw_home>/projects/<ctx.project_id>` (plus `<sandbox>/projects/<_derive_project_id(agent_dir)> -> <real_aw_home>/projects/<ctx.project_id>` when `agent_dir` is an isolated worktree whose path differs from `repo`) ONLY when `repo` is configured to use `AW_HOME`, satisfies both requirements: (1) legitimate reads/writes to the active home-backend project traverse the symlink directly to `<real_aw_home>/projects/<ctx.project_id>/`, and (2) all mutations to `config/registry.json` and all incidental `projects/<other_pid>/` directories (including scratch `/tmp/...` run-analytics caches) stay inside `<sandbox>` and are logged and discarded at turn exit after unlinking any `projects/*` symlinks. |
| F-07 | `project_registry.find_project` bypasses `AW_HOME` when `aw_home=None` | `project_registry.find_project` (`agent_workflows/project_registry.py:312`) | In `project_registry.find_project` (`agent_workflows/project_registry.py:303`), step 1 calls `load_registry(aw_home)` which honors `os.environ.get("AW_HOME")`, but step 2 (`project_registry.find_project` at `agent_workflows/project_registry.py:312`) computes `base_dir = os.path.abspath(os.path.expanduser(aw_home or "~/.aw"))`, ignoring `os.environ.get("AW_HOME")` whenever `aw_home` is `None`. Fixing `base_dir` to consult `aw_home or os.environ.get("AW_HOME") or "~/.aw"` closes this escape. |

## Proposed changes (ordered, validatable)

1. **Fix `project_registry.find_project` (`agent_workflows/project_registry.py:303`)**:
   - Replace `base_dir = os.path.abspath(os.path.expanduser(aw_home or "~/.aw"))` in `project_registry.find_project` (`agent_workflows/project_registry.py:312`) with `raw_home = aw_home or os.environ.get("AW_HOME") or "~/.aw"` followed by `base_dir = os.path.abspath(os.path.expanduser(raw_home))` so reverse-scanning `projects/*/config/project.json` honors `AW_HOME`.

2. **Add selective per-turn `AW_HOME` sandbox helpers in `agent_workflows/runner_shared.py`**:
   - Define `AW_HOME_ENV = "AW_HOME"` and `@dataclass class AgentAwHome`:
     - `path: Path` (the per-turn sandbox directory `<run_dir>/agent-aw-home/<NN>-<id6>-attempt-<N>[-<suffix>]/`)
     - `real_aw_home: Path` (the operator's resolved `AW_HOME` directory prior to per-turn override)
     - `seed_hashes: dict[str, str]` (relative file path -> SHA-256 hex digest for seeded files outside `projects/`, specifically `config/registry.json` when present)
     - `seed_json: dict[str, dict[str, Any]]` (relative file path -> parsed top-level JSON mapping for key-level diffing)
     - `linked_projects: tuple[str, ...]` (directory names under `<sandbox>/projects/` that are symlinked to `<real_aw_home>/projects/<active_pid>`)
     - `attempt: int`
     - `id6: str`
     - `suffix: str = ""`
   - Implement `prepare_agent_aw_home(run_dir: Path, item: Any, attempt_no: int, *, suffix: str = "", source_dir: Optional[Path] = None, repo: Optional[Path] = None, agent_dir: Optional[Path] = None) -> Optional[AgentAwHome]`:
     - Resolve `real_dir = Path(source_dir) if source_dir is not None else config.get_aw_home()[0]`.
     - Construct `sandbox_dir = Path(run_dir) / "agent-aw-home" / label` (`label = f"{order:02d}-{id6}-attempt-{int(attempt_no)}{suffix_part}"`).
     - If `sandbox_dir` already exists, first unlink any symlinks inside `sandbox_dir / "projects"` so `shutil.rmtree(sandbox_dir)` never traverses or deletes a linked real project directory, then recreate `sandbox_dir` (`mode=0o700`), `sandbox_dir / "config"`, and `sandbox_dir / "projects"`.
     - If `real_dir / "config" / "registry.json"` exists as a regular file, copy it to `sandbox_dir / "config" / "registry.json"` and record its SHA-256 in `seed_hashes["config/registry.json"]` and parsed JSON dict in `seed_json["config/registry.json"]` (recording specifically both top-level keys and the set of project IDs under `"projects"` so additions/mutations to `"projects"` report project-key or top-level changes without values).
     - If `repo is not None`, inspect `project_context.resolve_project_context(Path(repo), aw_home=real_dir)` (wrapping in `try/except Exception` so an unresolvable repo never breaks sandbox setup). When `ctx.is_configured` and (`ctx.records_backend == "home"` or `ctx.delivery_mode == "clean-delta"` or any root in `ctx.logical_roots.values()` is inside `real_dir`):
       - Ensure `real_project_dir = real_dir / "projects" / ctx.project_id` exists (`mkdir(parents=True, exist_ok=True)`).
       - Create symlink `sandbox_dir / "projects" / ctx.project_id -> real_project_dir` and record `ctx.project_id` in `linked_projects`.
       - If `agent_dir is not None`, compute `worktree_pid = project_context._derive_project_id(Path(agent_dir).resolve())`; if `worktree_pid != ctx.project_id` and not already linked, create symlink `sandbox_dir / "projects" / worktree_pid -> real_project_dir` and record `worktree_pid` in `linked_projects` so commands executed inside the lane worktree that derive a project ID from `cwd` resolve to the active project's home directory.
   - Implement `reconcile_agent_aw_home(handle: Optional[AgentAwHome], run_dir: Path, item: Any) -> list[dict[str, Any]]`:
     - In a `try / finally` block:
       - First, iterate over `handle.path / "projects"` (if present) and `unlink()` every symlink entry (including all entries in `handle.linked_projects`). This guarantees that symlinked active home-backend project directories are never scanned as discarded changes and never touched by `shutil.rmtree(handle.path)`.
       - Next, scan non-`projects/` files under `handle.path` (ignoring `.lock` and `.tmp` files) and compare against `handle.seed_hashes` / `handle.seed_json`, producing `{"file": rel, "change": "added" | "modified" | "removed", "keys": keys}` records (for `config/registry.json`, `keys` lists changed top-level keys plus any added/modified/removed `projects.<pid>` keys if top-level `"projects"` changed, with no path or timestamp values).
       - Next, scan remaining directories directly under `handle.path / "projects"`: for each non-linked `<pid>` directory that contains any files or subdirectories, emit one summarized record `{"file": f"projects/{pid_dir.name}", "change": "added", "keys": sorted_top_level_subdirs_or_files}` (for example `["records"]` when an incidental scratch `records/runs/analytics/cache/salt` was created).
       - For each record, append an event to `Path(run_dir) / "events.jsonl"` with `"type": "agent-aw-home-discarded"`, `"id6": handle.id6`, `"attempt": handle.attempt`, `"file": rec["file"]`, `"change": rec["change"]`, `"keys": rec["keys"]`, and `"at": _iso_now()`.
     - In the `finally:` block, unlink any remaining symlinks under `handle.path / "projects"` and call `shutil.rmtree(handle.path, ignore_errors=True)`.
   - Implement `report_discarded_aw_home(run_dir: Path, *, stream: Any = None) -> list[str]`:
     - Read `<run_dir>/events.jsonl` for `"type": "agent-aw-home-discarded"` events and emit `Agent AW_HOME changes discarded: <n> (<id6> <file> [<change>: <keys>]; ...)` when any exist.

3. **Wire `oc_runipd.py` and `agy_runipd.py`**:
   - Import `prepare_agent_aw_home`, `reconcile_agent_aw_home`, and `report_discarded_aw_home` from `runner_shared` in both `agent_workflows/oc_runipd.py` and `agent_workflows/agy_runipd.py`.
   - In `oc_runipd._execute_single_attempt` (`agent_workflows/oc_runipd.py:1399`) and `agy_runipd._execute_single_attempt` (`agent_workflows/agy_runipd.py:678`), call `aw_home_handle = prepare_agent_aw_home(run_dir, item, attempt_no, suffix=attempt_env_suffix, repo=repo, agent_dir=agent_dir)` right alongside `prepare_agent_user_config`, set `child_env["AW_HOME"] = str(aw_home_handle.path)` (or `child_env.pop("AW_HOME", None)` on `None`), reconcile in the outer `finally` block after `process.wait()` in `oc_runipd._execute_single_attempt` (`agent_workflows/oc_runipd.py:1873`) and `agy_runipd._execute_single_attempt` (`agent_workflows/agy_runipd.py:1007`) printing `  ! IPD <id6>: agent changed AW_HOME <file> (<keys>); change DISCARDED, your AW_HOME is unchanged` to `sys.stderr`, and call `report_discarded_aw_home(run_dir)` alongside `report_discarded_user_config(run_dir)` at the end of `oc_runipd._run_batch` (`agent_workflows/oc_runipd.py:4463`) and `agy_runipd._run_batch` (`agent_workflows/agy_runipd.py:2169`).

4. **Add regression test suite `tests/test_agent_aw_home_containment.py` and update docs**:
   - Create `tests/test_agent_aw_home_containment.py` covering `prepare_agent_aw_home`, `reconcile_agent_aw_home`, `report_discarded_aw_home`, `project_registry.find_project`, and both runners' `_execute_single_attempt`.
   - Update `docs/security.md` and `CHANGELOG.md`.

## Deferred / out of scope (with reason)

- OS-level filesystem sandboxing (`bwrap` / `sandbox-exec` / container namespaces) to block an agent process that explicitly unsets `AW_HOME` and writes directly to `~/.aw`: out of scope for `s4pys7` for the same reason documented in `9y27t2` (`"AW_CONFIG_DIR is an environment selector, not a hardened security boundary"` at `docs/security.md:42`)—`AW_HOME` is an environment selector that contains all well-behaved `aw` CLI invocations, tests, and probes, while OS-level containment belongs to the hardened execution profile.

## Scope check

- Over-scope: none.
- Under-scope: none (all four deliverables of backlog item `s4pys7`—measuring what execute turns write to `AW_HOME`, distinguishing legitimate home-backend writes from incidental writes, implementing selective per-turn containment across both runners, and regression testing—are covered by `E-01` through `E-07`).

## Required tests / validation

- Focused regression suite: `python3 -m pytest tests/test_agent_aw_home_containment.py tests/test_agent_user_config_containment.py`
- Full repository test suite: `python3 -m pytest`
- Leak sanitizer check: `aw sanitize --agent`

## Spec / documentation sync

- Update `docs/security.md` (`"8. Agent turns contain user-config writes."` at `docs/security.md:40`) to document per-turn `AW_HOME` containment and selective home-backend pass-through alongside `AW_CONFIG_DIR`.
- Update `CHANGELOG.md` under `## [Unreleased]` to note per-turn `AW_HOME` containment for `aw oc run` and `aw agy run`.

## Open questions

### OQ-01: How should per-turn `AW_HOME` containment preserve legitimate record writes when the active repository uses `records_backend: home` or `delivery_mode: clean-delta`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved from repository evidence in `project_context.resolve_project_context` (`agent_workflows/project_context.py:926`) and `storage.resolve_records_root` (`agent_workflows/storage.py:72`). When the active repository `repo` is configured (`ctx.is_configured`) and uses `AW_HOME` (`ctx.records_backend == "home"` or `ctx.delivery_mode == "clean-delta"` or a path in `ctx.logical_roots.values()` lies under `real_aw_home`), `prepare_agent_aw_home` creates `<real_aw_home>/projects/<ctx.project_id>` if needed and symlinks `<sandbox>/projects/<ctx.project_id>` (plus `<sandbox>/projects/<_derive_project_id(agent_dir)>` when `agent_dir` differs) to `<real_aw_home>/projects/<ctx.project_id>`. At turn exit, `reconcile_agent_aw_home` unlinks all symlinks under `<sandbox>/projects/` before scanning for incidental writes and before `shutil.rmtree(sandbox)`.

### OQ-02: How should incidental `<AW_HOME>/projects/<other_pid>/` directories (such as scratch run-analytics caches) be reported in `<run_dir>/events.jsonl`?

- Blocking: no
- Status: resolved
- Owner: Antigravity
- Resolution or deferral rationale: Resolved by matching the event schema of `runner_shared.reconcile_agent_user_config` (`agent_workflows/runner_shared.py:47244`). Rather than emitting one event per deep cache file under `<sandbox>/projects/<other_pid>/records/runs/analytics/cache/...`, `reconcile_agent_aw_home` emits one summarized `"type": "agent-aw-home-discarded"` event per non-linked `<other_pid>` directory (`"file": "projects/<other_pid>"`, `"change": "added"`, `"keys": [<sorted top-level subdirectories/files under <other_pid>>]`), keeping run event logs concise and free of sensitive file contents.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Output of `git diff agent_workflows/project_registry.py` and a Python one-liner invoking `project_registry.find_project` with `aw_home=None` and `AW_HOME` set to a temporary directory in `os.environ`, confirming it resolves the project inside `AW_HOME` and does not inspect `~/.aw`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Output of a Python probe exercising `runner_shared.prepare_agent_aw_home`, `runner_shared.reconcile_agent_aw_home`, and `runner_shared.report_discarded_aw_home` (created in `E-02`) showing: (a) for a `records_backend: repository` repo, mutations to `config/registry.json` and incidental `projects/scratch-123456/` directories are discarded from `real_aw_home` and logged as `agent-aw-home-discarded` events; and (b) for a `records_backend: home` repo, writes under `projects/<active_pid>/records/` persist in `real_aw_home/projects/<active_pid>/records/` while `config/registry.json` mutations are still discarded.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Output of `git diff agent_workflows/oc_runipd.py` showing `prepare_agent_aw_home`, `child_env["AW_HOME"]`, `reconcile_agent_aw_home` in the outer `finally` block after `process.wait()`, and `report_discarded_aw_home` in `_run_batch`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Output of `git diff agent_workflows/agy_runipd.py` showing `prepare_agent_aw_home`, `child_env["AW_HOME"]`, `reconcile_agent_aw_home` in the outer `finally` block after `process.wait()`, and `report_discarded_aw_home` in `_run_batch`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste of `python3 -m pytest tests/test_agent_aw_home_containment.py tests/test_agent_user_config_containment.py` runner output showing all tests passing.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Output of `git diff docs/security.md CHANGELOG.md` confirming `AW_HOME` per-turn containment and selective home-backend pass-through are documented with zero em or en dashes.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste of `python3 -m pytest` summary output and `aw sanitize --agent` JSON output showing `"status": "pass"`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This IPD is authored to `to-review` status to graduate backlog item `s4pys7`. Do not execute until approved; upon execution, validate all `V-01..V-07` items with concrete pasted output, transition the plan to `executed`, and commit via `aw commit 1vwjdl -- <paths>`.
