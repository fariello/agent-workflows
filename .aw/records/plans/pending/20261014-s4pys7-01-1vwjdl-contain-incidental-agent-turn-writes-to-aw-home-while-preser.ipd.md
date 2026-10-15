# IPD: Contain incidental agent-turn writes to AW_HOME while preserving home-backend records

- Date: 2026-10-14
- Kind: child
- Concern: Agent-turn `AW_HOME` containment and selective home-backend pass-through across `oc_runipd.py` and `agy_runipd.py`.
- Scope: Measure what execute turns write to `AW_HOME`. Fix the latent `project_registry.find_project` default so it honors `AW_HOME` when both `registry_data` and `aw_home` are omitted. Add a selective per-turn `AW_HOME` sandbox to `runner_shared.py` (`prepare_agent_aw_home`, `reconcile_agent_aw_home`, `report_discarded_aw_home`). The sandbox isolates `<AW_HOME>/config/registry.json` and incidental `<AW_HOME>/projects/<other_pid>/` writes, such as the run directories that scratch temp-dir probes mint. It symlinks each project directory the turn's repository (and its lane worktree) already resolves to under the real `AW_HOME`, so home-backend records keep their current location. Wire both runners (`oc_runipd.run_opencode`, `agy_runipd.run_agy_turn`, and both `run_queue` summaries), add regression tests, and update `CHANGELOG.md` and `docs/security.md`.
- Scope-Paths: agent_workflows/project_registry.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_agent_aw_home_containment.py, CHANGELOG.md, docs/security.md, .aw/records/plans/pending/20261014-s4pys7-01-1vwjdl-contain-incidental-agent-turn-writes-to-aw-home-while-preser.ipd.md
- Item-Dependencies: none
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: followup
- Priority: low
- From-Backlog: s4pys7
- Set: s4pys7 (Agent-turn AW_HOME containment)
- Order: 1
- Highest E allocated: 09
- Author: Antigravity
- Id: 1vwjdl
- Approval: 2026-10-15, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-011
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-011 fixed (review record 20261014-s4pys7-01-1vwjdl)
- 2026-10-14 to-review (aw set): Review-ready IPD for graduating backlog item s4pys7 (agent-turn AW_HOME containment).

- 2026-10-14 draft (Antigravity): created from backlog `s4pys7`.

## Goal

Stop execute and verify turns under `aw oc run` and `aw agy run` from mutating the operator's `<AW_HOME>/config/registry.json` or polluting `<AW_HOME>/projects/` with incidental scratch project directories. Every project directory the turn's repository already resolves to under `AW_HOME` (the `records_backend: home` or `delivery_mode: clean-delta` case) must keep transparent read/write pass-through at its CURRENT location. Non-goal: changing where any repository's records live.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Honor AW_HOME in project_registry.find_project

- [ ] E-01 In `project_registry.find_project` (`agent_workflows/project_registry.py:297`), replace the default registry lookup `reg_path = get_registry_path(aw_home or os.path.expanduser("~/.aw"))` (`agent_workflows/project_registry.py:312`) with `get_registry_path(aw_home or os.environ.get("AW_HOME") or os.path.expanduser("~/.aw"))`, so that when both `registry_data` and `aw_home` are omitted the lookup reads `<AW_HOME>/config/registry.json` instead of escaping to `~/.aw`. This is a latent fix: all three in-repo callers (`storage.validate_storage_boundaries` at `agent_workflows/storage.py:122`, `storage.validate_companion_preflight` at `agent_workflows/storage.py:475`, `cli._run_project_status` at `agent_workflows/cli.py:11714`) pass `registry_data` explicitly.
  - Depends on: none
  - Expected outcome: `project_registry.find_project(repo)` called with no `registry_data` and no `aw_home`, while `AW_HOME` names a temp directory whose `config/registry.json` registers `repo`, returns that entry (`match_kind` not `None`). With `AW_HOME` unset, behavior is unchanged.
  - Execution state: pending

### Task group 2: Selective per-turn AW_HOME sandbox in runner_shared.py

- [ ] E-02 Add `AW_HOME_ENV = "AW_HOME"`, the frozen dataclass `AgentAwHome`, and `prepare_agent_aw_home` to `agent_workflows/runner_shared.py`, directly after `runner_shared.report_discarded_user_config` (`agent_workflows/runner_shared.py:47333`), following Proposed change 2a. It must resolve the real home with `project_context._resolve_effective_aw_home` (or `ctx.effective_aw_home`), never `config.get_aw_home`. It must seed `config/registry.json`, link each pass-through project directory to its own real directory, and fail open by returning `None` (with a stderr warning) whenever a needed link cannot be created.
  - Depends on: E-01
  - Expected outcome: `runner_shared.prepare_agent_aw_home(run_dir, item, attempt_no, ...)` returns an `AgentAwHome` whose `path` holds a copy of the real `config/registry.json` and an otherwise empty `projects/`. For a repository whose logical roots resolve under `<real>/projects/<pid>`, it also holds a `projects/<pid>` symlink to `<real>/projects/<pid>`. It returns `None` when such a link cannot be created.
  - Execution state: pending

- [ ] E-03 Add `reconcile_agent_aw_home` and `report_discarded_aw_home` to `agent_workflows/runner_shared.py`, directly after `prepare_agent_aw_home`, following Proposed changes 2b and 2c. Reconcile unlinks every symlink under `<sandbox>/projects/` BEFORE any walk or delete, then walks with `os.walk(..., followlinks=False)`, never `Path.rglob`. It appends `{"event": "agent-aw-home-discarded", ...}` records (key names only, never values) to `<run_dir>/events.jsonl` via `runner_shared.append_jsonl` with `runner_shared.utc_now()`, and removes the sandbox in `finally`. Report prints the run-end summary line.
  - Depends on: E-02
  - Expected outcome: After a simulated turn that mutates the sandbox registry, creates `projects/scratch-<hash>/records/runs/<run>/`, and writes under a linked `projects/<pid>/records/`, `reconcile_agent_aw_home` returns and logs exactly the registry and scratch changes. The real registry bytes are unchanged, the linked write survives under `<real>/projects/<pid>/records/`, no real file is deleted, and the sandbox directory is gone. `report_discarded_aw_home` prints `Agent AW_HOME changes discarded: <n> (...)`.
  - Execution state: pending

### Task group 3: Runner integration (oc_runipd.py and agy_runipd.py)

- [ ] E-04 Wire the sandbox into `oc_runipd.run_opencode` (`agent_workflows/oc_runipd.py:2612`). Call `prepare_agent_aw_home(run_dir, item, attempt_no, suffix=log_suffix, repo=Path(state["repo"]), agent_dir=Path(agent_dir))` directly after the `prepare_agent_user_config` block (`agent_workflows/oc_runipd.py:2961`). On a handle, set `child_env["AW_HOME"] = str(handle.path)`. On `None`, LEAVE `AW_HOME` exactly as `pinned_child_env()` inherited it (do NOT pop it). Reconcile in the existing outer `finally:` (`agent_workflows/oc_runipd.py:3441`, after `process.wait()`) beside `reconcile_agent_user_config`, printing `  ! IPD <id6>: agent changed AW_HOME <file> (<keys>); change DISCARDED, your AW_HOME is unchanged` to stderr. Call `report_discarded_aw_home(run_dir)` beside `report_discarded_user_config(run_dir)` in `oc_runipd.run_queue` (`agent_workflows/oc_runipd.py:4496`), and import it alongside the `report_discarded_user_config as report_discarded_user_config` import (`agent_workflows/oc_runipd.py:336`).
  - Depends on: E-03
  - Expected outcome: Every OpenCode turn launched through `oc_runipd.run_opencode`, executor and verifier alike, receives `AW_HOME` pointing at its per-turn sandbox, which is reconciled after `process.wait()` even when the turn raises. The run-end summary is printed by `oc_runipd.run_queue`.
  - Execution state: pending

- [ ] E-05 Mirror E-04 in `agy_runipd.run_agy_turn` (`agent_workflows/agy_runipd.py:2399`): prepare after the `prepare_agent_user_config` block (`agent_workflows/agy_runipd.py:2512`) and before `popen_kwargs["env"] = child_env`. Use the same no-pop-on-`None` rule. Reconcile in the outer `finally:` (`agent_workflows/agy_runipd.py:2972`, after `process.wait()`) with the same stderr warning. Call `report_discarded_aw_home(run_dir)` in `agy_runipd.run_queue` (`agent_workflows/agy_runipd.py:3717`), with the import beside `agent_workflows/agy_runipd.py:784`.
  - Depends on: E-03
  - Expected outcome: Every Antigravity turn launched through `agy_runipd.run_agy_turn` receives the per-turn `AW_HOME` sandbox, which is reconciled after `process.wait()` even when the turn raises. The run-end summary is printed by `agy_runipd.run_queue`.
  - Execution state: pending

### Task group 4: Regression tests and documentation

- [ ] E-06 Create `tests/test_agent_aw_home_containment.py` with unit tests (outcome-based, no source inspection) for:
  - (a) `find_project` honoring `AW_HOME` (E-01).
  - (b) Registry seeding, plus discard of a modified, added, or removed `config/registry.json`, where the events carry key names and no path or timestamp values.
  - (c) Discard of an incidental scratch project, produced by calling `runner_shared.mint_run_dir(<scratch tmp dir>)` with `AW_HOME` set to the sandbox, leaving `<real>/projects/` without that pid.
  - (d) Pass-through for a configured `records_backend: home` repository, for a `delivery_mode: clean-delta` repository (config under `<real>/projects/<pid>/config/project.json`), and for a lane `agent_dir` resolving to its own pid. In each case writes land at the pid's CURRENT real location, while registry and other-pid writes are still discarded.
  - (e) Self-containing run dir: `run_dir` lives under `<real>/projects/<pid>/records/runs/` and so is reachable through the sandbox's own link. Reconcile terminates and deletes nothing under `<real>`.
  - (f) Fail-open: with `os.symlink` patched to raise `OSError`, a home-backend repository makes `prepare_agent_aw_home` return `None` and nothing is created under `<real>/projects/`.
  - (g) `report_discarded_aw_home` output and the silence when there are no events.

  Symlink-dependent cases skip with a reason when `os.symlink` is unavailable (Windows without Developer Mode, `.github/workflows/tests.yml:27`).
  - Depends on: E-03
  - Expected outcome: `python3 -m pytest tests/test_agent_aw_home_containment.py` passes with 0 failures and every case (a) through (g) present and passing on Linux.
  - Execution state: pending

- [ ] E-07 Add end-to-end runner tests to `tests/test_agent_aw_home_containment.py`, modeled on `tests/test_agent_user_config_containment.py::test_incident_end_to_end_per_host` (`tests/test_agent_user_config_containment.py:206`). Each test drives `oc_runipd.run_opencode` and `agy_runipd.run_agy_turn` with a fake agent executable that writes a new key into `$AW_HOME/config/registry.json` and creates `$AW_HOME/projects/scratch-x/f`. Assert that the real registry bytes are unchanged, `<real>/projects/scratch-x` is absent, an `agent-aw-home-discarded` event exists, stderr carries the `DISCARDED` line, and the sandbox is deleted. Add one more case per host in which `prepare_agent_aw_home` is patched to return `None`, and assert the child observed the driver's inherited `AW_HOME`, unchanged rather than unset.
  - Depends on: E-04, E-05, E-06
  - Expected outcome: `python3 -m pytest tests/test_agent_aw_home_containment.py tests/test_agent_user_config_containment.py` passes with 0 failures, including the per-host end-to-end and inherit-on-`None` cases.
  - Execution state: pending

- [ ] E-08 Update `docs/security.md` (item `8. Agent turns contain user-config writes.` at `docs/security.md:40`, add a sibling item 9) and `CHANGELOG.md` (a `- Fixed:` or `- Added:` bullet in the `## 2.0.0 (pending)` list, beside the user-config bullet at `CHANGELOG.md:56`; there is no `## [Unreleased]` heading). Document per-turn `AW_HOME` containment, pass-through for project directories the repository already uses under `AW_HOME`, discarded-write reporting, the fail-open behavior (no containment when a link cannot be created), and the honest limit (`AW_HOME` is an environment selector, not an OS-level boundary).
  - Depends on: E-04, E-05
  - Expected outcome: `docs/security.md` and `CHANGELOG.md` describe the sandbox, the pass-through, the fail-open case and the limit, and contain no em or en dashes in the added lines.
  - Execution state: pending

- [ ] E-09 Run the full test suite bare (`python3 -m pytest`) and the leak sanitizer (`aw sanitize --agent`).
  - Depends on: E-07, E-08
  - Expected outcome: `python3 -m pytest` reports 0 failed, and `aw sanitize --agent` emits a result record with `"outcome":"clean"` and `"exit":0`.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Predecessor plan `9y27t2` (`.aw/records/plans/executed/20261012-btw02e-01-9y27t2-contain-agent-turn-writes-to-the-operator-s-user-config.ipd.md`) established the per-turn environment-sandbox pattern: `runner_shared.AgentUserConfig` (`agent_workflows/runner_shared.py:47140`), `runner_shared.prepare_agent_user_config` (`agent_workflows/runner_shared.py:47151`), `runner_shared.reconcile_agent_user_config` (`agent_workflows/runner_shared.py:47214`), and `runner_shared.report_discarded_user_config` (`agent_workflows/runner_shared.py:47333`). They are wired into `oc_runipd.run_opencode` (`agent_workflows/oc_runipd.py:2961`, `:3444`, `:4496`) and `agy_runipd.run_agy_turn` (`agent_workflows/agy_runipd.py:2512`, `:2975`, `:3717`). No function named `_execute_single_attempt` or `_run_batch` exists in either runner.
- Both runners reconcile per-turn sandboxes in the outer `finally:` AFTER `process.wait()` (`returncode = process.wait()` in `oc_runipd.run_opencode`, `agent_workflows/oc_runipd.py:3438`; `rc = process.wait()` in `agy_runipd.run_agy_turn`, `agent_workflows/agy_runipd.py:2968`), so a timed-out or interrupted child cannot race the delete.
- Discard events are appended with `runner_shared.append_jsonl` (`agent_workflows/runner_shared.py:1078`), are timestamped with `runner_shared.utc_now` (`agent_workflows/runner_shared.py:341`), and name their kind under the `"event"` key (`"event": "agent-user-config-discarded"`, `agent_workflows/runner_shared.py:47259`), which `runner_shared.report_discarded_user_config` filters on (`agent_workflows/runner_shared.py:47363`). They record only relative identifiers, a change kind, and key names.
- The child env is built by `runner_shared.pinned_child_env` (`agent_workflows/runner_shared.py:33516`), which copies `os.environ`, so an un-set variable is INHERITED from the driver.
- `conftest._restore_home_sandbox` (`conftest.py:239`) re-points `AW_HOME` and `XDG_CONFIG_HOME` at a session sandbox around every test. Tests of `prepare_agent_aw_home` pass an explicit `source_dir` or monkeypatch `AW_HOME` to a test-owned directory.
- CI runs `windows-latest` (`.github/workflows/tests.yml:27`), where `os.symlink` may need Developer Mode. `run_analytics_report` (`agent_workflows/run_analytics_report.py:13`) documents the same constraint and keeps a non-symlink fallback.
- `<run_dir>` lives under `records/runs/`, which `.aw/.gitignore:14` ignores, so the sandbox is never committed.
- User-facing prose in `CHANGELOG.md` and `docs/security.md` must contain no em or en dashes (the `GEMINI.md` rule "Write NO em or en dashes in user-facing prose" at `GEMINI.md:20`, and the AGENTS.md execution contract).

## Findings

| ID | Category | Location / Symbol | Observation & Empirical Measurement |
|---|---|---|---|
| F-01 | Empirical baseline (normal execute turns) | `conftest._restore_home_sandbox` (`conftest.py:239`) | With a fresh `AW_HOME`, `aw status`, `aw attention`, `aw find plans`, `aw check release-gates`, `aw context` and `aw project status` run against this `records_backend: repository` repo wrote **zero files** under `AW_HOME`. This was re-measured at review time. `python3 -m pytest` inside a turn also writes nothing to the inherited `AW_HOME`, because the conftest fixture overrides it. |
| F-02 | `AW_HOME` layout | `project_registry.get_registry_path` (`agent_workflows/project_registry.py:245`), `project_context.resolve_project_context` (`agent_workflows/project_context.py:1217` `project_aw_dir`) | `AW_HOME` holds two subtrees. (1) `<AW_HOME>/config/registry.json` (plus `registry.json.lock` while writing), the machine-wide project registry. (2) `<AW_HOME>/projects/<project_id>/`, holding per-project `system/`, `config/`, `state/` and `records/` for non-repository backends. |
| F-03 | Incidental writes to `<AW_HOME>/config/registry.json` | `project_registry.register_or_update_project` (`agent_workflows/project_registry.py:392`), callers `cli._run_project_attach` (`agent_workflows/cli.py:11790`, call at `:11813`) and `cli._run_project_move` (`agent_workflows/cli.py:11820`, call at `:11843`) | An agent turn never legitimately needs to change the operator's registry. A turn that runs `aw project attach` or `aw project move` (for example as an ad-hoc probe) without overriding `AW_HOME` writes into the operator's real registry. These two CLI verbs are the only callers of `register_or_update_project`, and `project_registry.save_registry` is called only from it (`agent_workflows/project_registry.py:440`). |
| F-04 | Incidental writes to `<AW_HOME>/projects/<other_pid>/` | `project_context.resolve_project_context` default backend (`agent_workflows/project_context.py:1170` `built-in default (home)`), `runner_shared.state_root` (`agent_workflows/runner_shared.py:386`), `runner_shared.mint_run_dir` (`agent_workflows/runner_shared.py:405`) | An unconfigured directory, such as a `mktemp -d` scratch repo, resolves to `records_backend = home` with `project_id = _derive_project_id(path)`. Measured at review: `runner_shared.mint_run_dir(<scratch>)` with `AW_HOME=<h>` created `<h>/projects/scratch-0b74fe/records/runs/run-.../`. Any helper that resolves a runs root through `state_root` against a scratch path pollutes the operator's `projects/` the same way. |
| F-05 | Legitimate writes to `<AW_HOME>/projects/<pid>/` | `project_context.resolve_project_context` roots (`agent_workflows/project_context.py:1217`-`1268`), `project_context.project_config_dir` (`agent_workflows/project_context.py:755`) | When the turn's repository resolves any logical root (`system`, `config`, `state`, `records`) under `<AW_HOME>/projects/<ctx.project_id>/` (home backend, or clean-delta delivery), the turn legitimately reads and writes there. A blanket discard would destroy those records. |
| F-06 | Selective sandbox via per-pid symlinks | `project_context._derive_project_id` (`agent_workflows/project_context.py:745`) | Measured at review: with sandbox `AW_HOME=<sb>` and `<sb>/projects/<pid> -> <real>/projects/<pid>`, `resolve_project_context` for a clean-delta repo still finds its config through the link (`is_configured=True`, `records_backend=home`). `mint_run_dir(repo)` then created the run under `<real>/projects/<pid>/records/runs/`. The scheme works. A lane worktree derives its OWN pid from its path (measured: `wt-7f0d73` vs `repo-5429fa`), so a lane resolves its home roots under a different pid than the main checkout, and each pid must be linked to its own real directory. |
| F-07 | `find_project` default bypasses `AW_HOME` (latent) | `project_registry.find_project` (`agent_workflows/project_registry.py:311`-`313`) | When `registry_data is None` and `aw_home is None`, `find_project` reads `get_registry_path(os.path.expanduser("~/.aw"))`, ignoring `AW_HOME`. It performs no `projects/*` scan. Every in-repo caller passes `registry_data` (`storage.validate_storage_boundaries` at `agent_workflows/storage.py:122`, `storage.validate_companion_preflight` at `agent_workflows/storage.py:475`, `cli._run_project_status` at `agent_workflows/cli.py:11714`), so this is latent, but it is a direct escape for any probe calling `find_project(path)`. |
| F-08 | Two AW_HOME resolvers disagree | `config.get_aw_home` (`agent_workflows/config.py:1032`, default `Path.home()/".aw"`), `project_context._resolve_effective_aw_home` (`agent_workflows/project_context.py:249`) via `get_default_aw_home` (`agent_workflows/project_context.py:223`, default `$XDG_CONFIG_HOME/agent-workflows` when `XDG_CONFIG_HOME` is set) | Measured at review: with `AW_HOME` unset and `XDG_CONFIG_HOME` set, `config.get_aw_home()` returns `<HOME>/.aw`, while `project_context._resolve_effective_aw_home()` returns `<XDG>/agent-workflows`. Records are resolved by the latter. A sandbox seeded and linked from `config.get_aw_home()` would therefore link the wrong real directory, and home-backend records written by the turn would land in the wrong place. |
| F-09 | Self-referential link | `runner_shared.state_root` (`agent_workflows/runner_shared.py:399`) | For a home-backend repository, `run_dir` itself lives under `<real>/projects/<pid>/records/runs/`, so the sandbox at `<run_dir>/agent-aw-home/<turn>/` is reachable through its own `projects/<pid>` link. Any walk that follows links (`Path.rglob` follows directory symlinks before Python 3.13; `requires-python = ">=3.9"`, `pyproject.toml:12`) can loop or double-count, and any delete that follows links could reach real records. |
| F-10 | Fail-open must not relocate | `runner_shared.pinned_child_env` (`agent_workflows/runner_shared.py:33516`) | If preparation fails and the runner POPS `AW_HOME`, a child of a driver launched with a custom `AW_HOME` silently falls back to the default home and writes home-backend records to the wrong directory. Fail-open must mean "inherit the driver's `AW_HOME` unchanged, uncontained". Likewise, a sandbox missing a needed pass-through link would divert legitimate records into a directory that is deleted at turn exit, so a link failure must abandon the sandbox (return `None`) rather than proceed without the link. |

## Proposed changes (ordered, validatable)

1. **Fix `project_registry.find_project` (`agent_workflows/project_registry.py:312`)** (E-01):
   - `reg_path = get_registry_path(aw_home or os.environ.get("AW_HOME") or os.path.expanduser("~/.aw"))`. No other line changes.

2. **Selective per-turn `AW_HOME` sandbox in `agent_workflows/runner_shared.py`**, placed after `runner_shared.report_discarded_user_config` (`agent_workflows/runner_shared.py:47333`):

   2a. **`AW_HOME_ENV`, `AgentAwHome`, `prepare_agent_aw_home`** (E-02):
   - `AW_HOME_ENV = "AW_HOME"`.
   - `@dataclass(frozen=True) class AgentAwHome` with these fields:
     - `path: Path`
     - `real_aw_home: Path`
     - `seed_hashes: dict[str, str]` (only `"config/registry.json"` when seeded)
     - `seed_json: dict[str, dict[str, Any]]`
     - `linked_projects: tuple[str, ...]`
     - `attempt: int`
     - `id6: str`
     - `suffix: str = ""`
   - `prepare_agent_aw_home(run_dir, item, attempt_no, suffix="", source_dir=None, repo=None, agent_dir=None) -> Optional[AgentAwHome]`. It mirrors the `prepare_agent_user_config` signature and runs inside a single `try/except Exception` that prints `  ! Warning: failed to seed agent AW_HOME sandbox: <exc>` to stderr and returns `None`.
     - Real home: `real_dir = Path(source_dir)` when given, else `Path(project_context._resolve_effective_aw_home()[0])` (F-08). Never use `config.get_aw_home`.
     - Label: `f"{int(item.get('position', 1)):02d}-{id6}-attempt-{attempt_no}{'-' + suffix if suffix else ''}"`, which is the same key scheme as `prepare_agent_user_config` (`agent_workflows/runner_shared.py:47171`-`47175`). Use `sandbox_dir = Path(run_dir) / "agent-aw-home" / label`. If it already exists, remove it with `shutil.rmtree` (which unlinks contained symlinks without following them). Then create `sandbox_dir` (`mode=0o700`), `config/` and `projects/`.
     - Seed: if `real_dir / "config" / "registry.json"` is a regular file, copy it with `shutil.copy2` and record its SHA-256 (`runner_shared.sha256_file`) and parsed dict.
     - Pass-through links: for each `target` in `(repo, agent_dir)` that is not `None`, de-duplicated by canonical path, compute `ctx = project_context.resolve_project_context(target_repo=str(target), aw_home=str(real_dir))` inside its own `try/except` (an unresolvable target contributes no link). Let `proj = real_dir / "projects" / ctx.project_id`. Link when any value of `ctx.logical_roots` lies inside `proj` (`project_context._is_safe_subpath`) AND (`ctx.is_configured` or `proj.is_dir()`). Do NOT create `proj` for an unconfigured target. When linking, `proj.mkdir(parents=True, exist_ok=True)` and `os.symlink(proj, sandbox_dir / "projects" / ctx.project_id, target_is_directory=True)` unless that name is already linked. Each pid links to ITS OWN real directory, which preserves current record locations exactly (Decision D-2 in the review record).
     - Link failure: if any needed `os.symlink` raises, remove every link created so far, `shutil.rmtree(sandbox_dir)`, warn, and return `None` (F-10).

   2b. **`reconcile_agent_aw_home(handle, run_dir, item) -> list[dict]`** (E-03):
   - `None` handle returns `[]`.
   - In `try`:
     1. Unlink every entry under `handle.path / "projects"` for which `os.path.islink` is true. This happens BEFORE any walk (F-09).
     2. Walk `handle.path` with `os.walk(handle.path, followlinks=False)`, skipping any entry still a symlink and skipping `*.lock` / `*.tmp`.
     3. For `config/registry.json`, compare against the seed: `added`, `removed` or `modified`. On `modified`, `keys` lists the differing top-level keys. When `projects` differs, it is replaced by `projects.<pid>` entries for each added, removed or changed pid. No values, paths or timestamps are recorded.
     4. Any other file outside `projects/` is reported as `added` with no keys.
     5. For each remaining non-empty directory `projects/<pid>`, emit one record `{"file": f"projects/{pid}", "change": "added", "keys": sorted(top-level entry names)}`.
     6. Each record is `{"at": utc_now(), "event": "agent-aw-home-discarded", "id6": ..., "attempt": ..., "file": ..., "change": ..., "keys"?: [...]}`, appended to `Path(run_dir) / "events.jsonl"` with `append_jsonl`.
   - On exception: warn, and append `{"event": "agent-aw-home-reconcile-failed", "error": str(exc), ...}`.
   - In `finally`: unlink any remaining symlinks under `projects/`, then `shutil.rmtree(handle.path, ignore_errors=True)`.

   2c. **`report_discarded_aw_home(run_dir, *, stream=None) -> list[str]`** (E-03): this is the mirror of `report_discarded_user_config` (`agent_workflows/runner_shared.py:47333`). It filters `"event" == "agent-aw-home-discarded"` and prints `Agent AW_HOME changes discarded: <n> (<id6>: <file> <keys>; ...)`, or nothing. It never raises.

3. **Runner wiring** (E-04, E-05): as stated in E-04 and E-05. The key points:
   - `suffix=log_suffix`, so verifier turns get their own sandbox.
   - `repo=state["repo"]` and `agent_dir=agent_dir`.
   - Set `AW_HOME` on a handle, and leave it inherited on `None`.
   - Reconcile in the existing outer `finally:` after `process.wait()`.
   - Print the summary in each `run_queue`.

4. **Tests and docs** (E-06, E-07, E-08).

## Deferred / out of scope (with reason)

- OS-level filesystem sandboxing (`bwrap` / `sandbox-exec` / namespaces) to stop an agent that unsets `AW_HOME` or writes `~/.aw` by absolute path. This is out of scope for the same reason recorded by `9y27t2` (the `docs/security.md` item 8 sentence "is an environment selector, not a hardened security boundary" at `docs/security.md:42`); OS-level containment belongs to the hardened execution profile.
- Moving lane-worktree home-backend records into the main checkout's project directory. Today a lane resolves its own pid (F-06), and this plan preserves that location. Whether lane home records should merge into the main pid is a separate behavior change.
- Reconciling `config.get_aw_home` with `project_context._resolve_effective_aw_home` (F-08). This plan only avoids depending on the divergent resolver.

## Scope check

- Over-scope: none. The `docs/security.md` and `CHANGELOG.md` edits are required by the security-boundary and user-visible-behavior changes.
- Under-scope: none after revision. Measuring (F-01, F-04, re-measured), classifying legitimate versus incidental writes (F-03 to F-05), containment on both hosts (E-02 to E-05), fail-open safety (F-10), and regression tests (E-06, E-07) are all covered.

## Required tests / validation

- Focused: `python3 -m pytest tests/test_agent_aw_home_containment.py tests/test_agent_user_config_containment.py`
- Full suite, bare: `python3 -m pytest`
- Leak sanitizer: `aw sanitize --agent`

## Spec / documentation sync

- No `.spec.md` governs runner env containment (`9y27t2` amended none), so there is no spec edit.
- `docs/security.md`: add item 9 beside item `8. Agent turns contain user-config writes.` (`docs/security.md:40`).
- `CHANGELOG.md`: add one bullet in the `## 2.0.0 (pending)` list beside `CHANGELOG.md:56`.

## Open questions

### OQ-01: How should per-turn `AW_HOME` containment preserve legitimate record writes when the active repository uses `records_backend: home` or `delivery_mode: clean-delta`?

- Blocking: no
- Status: resolved
- Owner: plan author (revised by reviewer)
- Resolution or deferral rationale: Use per-pid symlinks. The approach was demonstrated at review (F-06): with a sandbox `AW_HOME` holding `projects/<pid> -> <real>/projects/<pid>`, a clean-delta repository still resolves `is_configured=True` and `records_backend=home`, and `mint_run_dir` wrote under `<real>/projects/<pid>/records/runs/`. Each target (`repo`, `agent_dir`) links its own resolved pid to its own real directory (Proposed change 2a), so no record changes location. Reconcile unlinks every link before walking or deleting (F-09). A link that cannot be created abandons the sandbox (F-10).

### OQ-02: How should incidental `<AW_HOME>/projects/<other_pid>/` directories be reported in `<run_dir>/events.jsonl`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Report one summarized `"event": "agent-aw-home-discarded"` record per non-linked pid directory (`"file": "projects/<pid>"`, `"change": "added"`, `"keys": [top-level entry names]`). The record uses the `"event"` key and the `append_jsonl`/`utc_now` helpers of `runner_shared.reconcile_agent_user_config` (`agent_workflows/runner_shared.py:47257`-`47312`), so `report_discarded_aw_home` filters it exactly as its user-config twin does. Pid names are local identifiers that appear only in the gitignored run dir (`.aw/.gitignore:14`) and on the operator's stderr.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: Paste `git diff agent_workflows/project_registry.py`, showing only the `find_project` default changed. Also paste the output of a Python one-liner that sets `AW_HOME` to a temp dir whose `config/registry.json` registers a temp repo, calls `project_registry.find_project(<repo>)` with no other arguments, and prints a non-`None` `match_kind`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Paste the output of a Python probe (code path `runner_shared.prepare_agent_aw_home`, created by E-02) that prints:
    - (a) for a `records_backend: repository` repo, the sandbox listing (`config/registry.json` present, `projects/` empty) and `linked_projects == ()`;
    - (b) for a configured `records_backend: home` repo, `os.readlink(<sandbox>/projects/<pid>)` equal to `<real>/projects/<pid>`;
    - (c) with `os.symlink` patched to raise, the return value `None` and the absence of the sandbox directory.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Paste the output of a Python probe (code paths `runner_shared.reconcile_agent_aw_home` and `runner_shared.report_discarded_aw_home`, created by E-03) that simulates a turn in a home-backend sandbox whose `run_dir` lies under `<real>/projects/<pid>/records/runs/`. The output must show:
    - the returned records;
    - the real registry SHA-256 before and after (equal);
    - the linked file present under `<real>/projects/<pid>/records/`;
    - `<real>/projects/scratch-*` absent;
    - the sandbox absent;
    - the printed `Agent AW_HOME changes discarded:` line.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: Paste `git diff agent_workflows/oc_runipd.py`, showing in `run_opencode` the `prepare_agent_aw_home` call, `child_env["AW_HOME"]` set only on a handle (with no `pop` of `AW_HOME`), and `reconcile_agent_aw_home` in the outer `finally:` after `process.wait()`, and showing `report_discarded_aw_home(run_dir)` in `run_queue`. Also paste the passing lines for the oc cases of E-07.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: Paste `git diff agent_workflows/agy_runipd.py`, showing the same four elements in `run_agy_turn` and `run_queue`. Also paste the passing lines for the agy cases of E-07.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: Paste the actual runner output of `python3 -m pytest -o addopts="" -v tests/test_agent_aw_home_containment.py`, showing a passing test for each behavior (a) through (g) in E-06, with test names as non-binding pointers, and 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Paste the actual runner output of `python3 -m pytest tests/test_agent_aw_home_containment.py tests/test_agent_user_config_containment.py`, showing 0 failed. Name the tests that assert, per host, the unchanged real registry, the absent scratch pid, the `DISCARDED` stderr line, and the inherited `AW_HOME` on a `None` handle.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: Paste `git diff docs/security.md CHANGELOG.md`, plus the output of a grep for U+2013 and U+2014 over the added lines, which must show no matches.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: Paste the summary line of a bare `python3 -m pytest` run, showing 0 failed, and the `aw sanitize --agent` result record, showing `"outcome":"clean"` and `"exit":0`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved 1vwjdl --by-human`). OQ-01 and OQ-02 are resolved, and no question blocks. Begin with `aw ipd begin 1vwjdl`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition. An edit outside it is made and then justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `oc_runipd.py`, `agy_runipd.py` or `runner_shared.py` that cannot be safely combined, or a cited anchor (`prepare_agent_user_config` call sites, the outer `finally:` after `process.wait()`) that no longer exists.

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`. Never claim a result you did not run. Run the suite bare (`python3 -m pytest`).

Commits: commit only the `Scope-Paths` files you changed, through `aw commit 1vwjdl -- <paths>`. Never use `git add -A`, never push, never tag. This is a shared checkout, so verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run`, the runner owns finalize. When executing by hand, run `aw ipd finalize 1vwjdl` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` and never hand-roll a `git mv` into `executed/`. Backlog `s4pys7` (Work-Kind `followup`, no release gate) is closed `done` only after this plan is executed.
