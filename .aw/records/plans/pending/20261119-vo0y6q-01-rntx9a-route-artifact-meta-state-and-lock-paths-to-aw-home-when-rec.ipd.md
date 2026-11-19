# IPD: Route artifact_meta state and lock paths to AW_HOME when records_backend is home

- Date: 2026-11-19
- Kind: child
- Concern: In `tests/test_records_root_accessor.py::test_home_records_reproduction_backlog`, running `aw backlog new --apply --dir <target>` against a repository with `records_backend: "home"` in `.aw/config/project.json` creates `<target>/.aw/state/locks/meta-<id6>.lock` inside the target checkout. Because the fixture has no `.aw/.gitignore`, `git status --porcelain --ignored` reports `?? .aw/state/` and fails the clean-target assertion. Every phase-B metadata writer (`backlog`, `specs`, `prompts`, `research_cmd`, `artifact_adopt`, `set_records`, `status_set`, `releases`, `coverage_record`, `plan_readiness`, `artifact_rename`, `review_findings`, `ipd_authoring`, `plans_refs`) obtains its state root from `agent_workflows/artifact_meta.py::legacy_context`, and `agent_workflows/meta_cli.py::meta_context` reads `logical_roots["state"]` from `project_context.resolve_project_context`, which returns `<target>/.aw/state` whenever `delivery_mode` is `tracked` even when `records_backend` is stored `home`.
- Scope: Route the `artifact_meta` metadata state root (used for `locks/meta-<key>.lock`, `operation_journal/`, and `index.db`) to `<AW_HOME>/projects/<project_id>/state` when `records_backend` resolves to `home` via a stored records placement and no explicit `local.json` `state_root` override exists. Keep `project_context.resolve_project_context` unchanged for `spec 20260810-1447-01` Section 5 tracked `state_durable` and `state_runtime` placement, keep unconfigured repositories (`builtin_defaults`) and `repository` or `companion` backends unchanged, delegate `agent_workflows/meta_cli.py::meta_context` to `artifact_meta.legacy_context`, and expand `tests/test_records_root_accessor.py` to pin the lock placement and clean-target behavior.
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/meta_cli.py, tests/test_records_root_accessor.py, .aw/records/plans/pending/20261119-vo0y6q-01-rntx9a-route-artifact-meta-state-and-lock-paths-to-aw-home-when-rec.ipd.md
- Item-Dependencies: none
- Status: to-review
- Short-Description: Route artifact_meta state and meta locks under AW_HOME when records_backend resolves to home
- Work-Kind: bug
- Priority: medium
- From-Backlog: vo0y6q
- Blocks-Release: next
- Set: vo0y6q
- Order: 1
- Highest E allocated: 04
- Author: antigravity/gemini
- Id: rntx9a

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-19 to-review (aw set): authored review-ready plan from backlog vo0y6q
- 2026-11-19 draft (antigravity/gemini): created.

## Goal

Ensure `aw backlog new --apply` and every other `artifact_meta` metadata reader and writer place metadata locks (`locks/meta-*.lock`), operation journals, and `index.db` under the project's `AW_HOME` state directory when `records_backend` resolves to stored `home`, keeping the target repository working tree clean while preserving existing behavior for unconfigured, `repository`, `companion`, and explicit `state_root` repositories.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Metadata state-root routing and tests

- [ ] E-01 In `agent_workflows/artifact_meta.py`, add one shared helper `_meta_state_root(ctx: Any) -> Path` (plus a small helper `_home_state_override(resolved_ctx: Any, repo_root: Path, current_state: Path) -> Path`) and update `legacy_context(repo_root)` and every `artifact_meta` reader and writer that reads `ctx.logical_roots["state"]` (`read`, `history`, `resolve`, `query`, `query_lineage`, `review_rows`, `read_at`, `write_legacy`, `append`, `create`, `repair`) to use `_meta_state_root(ctx)`. Apply this rule: (1) start from `state = Path(ctx.logical_roots["state"])`; (2) when the context represents a `ProjectContext` with `records_backend == project_context.RecordsBackend.HOME.value` via a stored records placement (`provenance["records_backend"]["source"]` in `("project_durable_config", "machine_local_binding")` or `delivery_mode == "clean-delta"`) and `state.resolve() == (Path(target_repo).resolve() / ".aw" / "state").resolve()`, return `Path(ctx.effective_aw_home) / "projects" / ctx.project_id / "state"`; (3) in `legacy_context(repo_root)`, when `Path(resolved.logical_roots["records"]).resolve() == records.resolve()`, apply the same override whenever `resolved.records_backend == project_context.RecordsBackend.HOME.value` and `state.resolve() == (root / ".aw" / "state").resolve()`; (4) in all other cases (unconfigured repositories where `records_backend` provenance is `builtin_defaults` and `project_records_dir` returns `<repo>/.aw/records`, explicit `local.json` `state_root` overrides, `clean-delta` which already resolves to `AW_HOME`, `repository`/`repository-untracked`, `companion`, and synthetic `Ctx` objects without `records_backend`), keep `state` unchanged. Do not modify `agent_workflows/project_context.py::resolve_project_context`.
  - Depends on: none
  - Expected outcome: `artifact_meta.legacy_context(target)` returns `<AW_HOME>/projects/<project_id>/state` for stored `records_backend: "home"` (whether configured in `<target>/.aw/config/project.json`, `<target>/.aw/config/local.json`, or `<AW_HOME>/projects/<project_id>/config/project.json`), returns `<target>/.aw/state` for unconfigured or `repository`-backed repositories, and honors any explicit `local.json` `state_root` binding; `backlog.run_new`, `backlog.run_note`, `specs.run_new`, `prompts.run_new`, `research_cmd`, `artifact_adopt`, `set_records`, and `status_set` create `locks/meta-*.lock` under `<AW_HOME>/projects/<project_id>/state/locks/` when `records_backend` resolves to stored `home`, with zero writes to `<target>/.aw/state/`.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/meta_cli.py`, update `meta_context(repo_root)` to delegate to `artifact_meta.legacy_context(repo_root)` (`ctx = _meta.legacy_context(repo_root); return MetaContext(logical_roots=dict(ctx.logical_roots), repo_root=ctx.repo_root)`) instead of duplicating `project_records_dir` and `resolve_project_context` state resolution.
  - Depends on: E-01
  - Expected outcome: `meta_cli.meta_context` and `artifact_meta.legacy_context` return identical `records` and `state` roots across every backend (`home`, `repository`, `repository-untracked`, `companion`, `clean-delta`, and unconfigured), and `aw show` plus `aw index rebuild` write `index.db` under `<AW_HOME>/projects/<project_id>/state/index.db` on a stored `records_backend: "home"` repository instead of creating `<target>/.aw/state/`.
  - Execution state: pending

- [ ] E-03 In `tests/test_records_root_accessor.py`, keep `test_home_records_reproduction_backlog` unmodified and add outcome tests covering: (1) `aw backlog new --apply --dir <target>` on `home_records_env` creates `meta-<id6>.lock` under `<AW_HOME>/projects/*/state/locks/` and does not create `<target>/.aw/state`; (2) `aw backlog note --dir <target>` on `home_records_env` leaves `git status --porcelain --ignored` free of `??` entries and places its lock under `<AW_HOME>/projects/*/state/locks/`; (3) `aw specs new --apply --dir <target>` and `aw show <id6> --dir <target>` on `home_records_env` leave `git status --porcelain --ignored` free of `??` entries and create no `<target>/.aw/state`; (4) `artifact_meta.legacy_context` and `meta_cli.meta_context` agree on `state` across stored `project.json` `records_backend: "home"` (`delivery_mode: "tracked"`), `local.json`-only `records_backend: "home"`, `AW_HOME`-stored `project.json` `records_backend: "home"`, explicit `local.json` `state_root` override (must keep the explicit override), `records_backend: "repository"` (must return `<target>/.aw/state`), and unconfigured repository (must return `<target>/.aw/state`). Run a mutation proof by temporarily disabling the `home` state override in `agent_workflows/artifact_meta.py`, confirming `test_home_records_reproduction_backlog` fails with `?? .aw/state/`, and restoring the fix.
  - Depends on: E-02
  - Expected outcome: `python3 -m pytest -o addopts="" tests/test_records_root_accessor.py` passes all tests including `test_home_records_reproduction_backlog`, and the mutation proof demonstrates falsifiability.
  - Execution state: pending

- [ ] E-04 Run the related test modules (`python3 -m pytest -o addopts="" tests/test_records_root_accessor.py tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_cache.py tests/test_index_rebuild.py tests/test_project_layout.py tests/test_m0001_layout_stage.py tests/test_backlog.py tests/test_writers_obligations.py`), run bare `python3 -m pytest`, and run `aw ipd lint --phase pre-transition rntx9a`.
  - Depends on: E-03
  - Expected outcome: All targeted test modules pass, bare `python3 -m pytest` passes with zero regressions, and `aw ipd lint --phase pre-transition rntx9a` reports conforming.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, never by a line number alone (advisory `IPD-C801`).
- `agent_workflows/project_context.py::resolve_project_context` sets `state_root` to `<repo>/.aw/state` whenever `delivery_mode` is `tracked` (even when `records_backend` is `home`), unless `local.json` binds `state_root`. That behavior is governed by `spec 20260810-1447-01` Section 5 (tracked `state_durable` and `state_runtime` stay in the repository; only `clean-delta` moves general project state to `AW_HOME`) and is pinned for unconfigured repositories by `tests/test_project_layout.py::PhysicalPolicyMatrixTests::test_e01` and for in-place switching by `tests/test_records_root_switch_execute.py`.
- `agent_workflows/project_context.py::project_records_dir` returns `<repo>/.aw/records` for unconfigured repositories (whose `resolve_project_context` provenance for `records_backend` is `builtin_defaults`) and returns `AW_HOME/projects/<project_id>/records` only when `has_stored_records_placement` is true (`project_durable_config`, `machine_local_binding`, or `delivery_mode == "clean-delta"`).
- `tests/test_artifact_meta_legacy_writer.py::_init_repo` initializes an unconfigured git repository with `.aw/records` and `.aw/state` (no `.aw/config/project.json`) and `test_phase_b_create_preview_apply_lock_and_source_digest_refusal` asserts `(root / ".aw" / "state" / "locks" / "meta-cr0001.lock").exists()`.
- Phase-B writers (`backlog.run_new`, `backlog.run_note`, `specs.run_new`, `prompts.run_new`, `research_cmd._research_legacy_context`, `artifact_adopt`, `set_records._records_legacy_context`, `status_set`) all obtain `logical_roots["state"]` from `artifact_meta.legacy_context(repo_root)`.
- Core test suite runs with bare `python3 -m pytest`; narrowed runs use `-o addopts=""`. Tests must assert observable behavior and outcomes, never inspect production source (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only changed paths through `aw commit rntx9a -- <paths>`; never run `git add -A` or `git push`.

## Findings

| # | Severity | Location | Finding |
| - | -------- | -------- | ------- |
| F-01 | High | `tests/test_records_root_accessor.py::test_home_records_reproduction_backlog` | Baseline run at planning HEAD fails (`1 failed, 18 passed in 6.58s` for `tests/test_records_root_accessor.py`): `aw backlog new --apply --dir <target>` exits 0 and writes the backlog file under `AW_HOME`, then `git status --porcelain --ignored` in `<target>` reports `?? .aw/state/` (`AssertionError: Target working tree not clean`). |
| F-02 | High | `agent_workflows/artifact_meta.py::legacy_context`, `agent_workflows/artifact_meta.py::write_legacy`, `agent_workflows/backlog.py::run_new` | `backlog.run_new` (moved onto `artifact_meta.create` in executed plan `jlwedt`) reads `base_ctx = _meta.legacy_context(repo_root)` and builds `create_ctx` with `state: base_ctx.logical_roots["state"]`. In `home_records_env` (`{"preset": "private-target", "delivery_mode": "tracked", "records_backend": "home"}`), `project_records_dir` and `resolve_project_context.logical_roots["records"]` match (`<AW_HOME>/projects/<id>/records`), so `legacy_context` sets `state = Path(resolved.logical_roots["state"])` (`<target>/.aw/state`). `write_legacy` then runs `lock_path = state_root / "locks" / f"meta-{ltarget.key}.lock"` and `lock_path.parent.mkdir(parents=True, exist_ok=True)`, creating `<target>/.aw/state/locks/meta-<id6>.lock`. |
| F-03 | High | `agent_workflows/specs.py::run_new`, `agent_workflows/prompts.py::run_new`, `agent_workflows/research_cmd.py::_research_legacy_context`, `agent_workflows/artifact_adopt.py`, `agent_workflows/set_records.py`, `agent_workflows/status_set.py` | Every other phase-B writer also derives `state` from `artifact_meta.legacy_context(repo_root)` (or passes no `project_context` so `write_legacy` calls `legacy_context(rroot)`). `test_home_records_reproduction_specs` passed only because it did not run `git status --porcelain --ignored` on `<target>`. |
| F-04 | Medium | `agent_workflows/meta_cli.py::meta_context`, `agent_workflows/artifact_meta.py` (`read`, `history`, `resolve`, `query`, `query_lineage`, `review_rows`, `read_at`, `append`, `create`, `repair`) | `meta_cli.meta_context` resolves `state` independently from `resolve_project_context(...).logical_roots["state"]` (creating `index.db` under `<target>/.aw/state` during `aw show` or `aw index rebuild`), and 11 `artifact_meta` entry points read `Path(ctx.logical_roots["state"])` directly when passed a `ProjectContext` from `resolve_project_context`. Routing both through one helper prevents write locks and `index.db` from splitting across `<target>/.aw/state` and `<AW_HOME>/projects/<id>/state`. |
| F-05 | Low | Baseline related modules | Baseline run of `python3 -m pytest -o addopts="" -q tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_cache.py tests/test_index_rebuild.py tests/test_project_layout.py tests/test_m0001_layout_stage.py` passes (`49 passed in 19.05s`). |

## Proposed changes (ordered, validatable)

1. In `agent_workflows/artifact_meta.py`, add `_meta_state_root(ctx)` and `_home_state_override(resolved_ctx, repo_root, current_state)` and route `legacy_context` plus all `read`/`history`/`resolve`/`query`/`query_lineage`/`review_rows`/`read_at`/`write_legacy`/`append`/`create`/`repair` `state_root` lookups through them (E-01).
2. In `agent_workflows/meta_cli.py`, delegate `meta_context(repo_root)` to `artifact_meta.legacy_context(repo_root)` so `aw show` and `aw index rebuild` share the same `records` and `state` roots (E-02).
3. Expand `tests/test_records_root_accessor.py` with lock-location, `aw backlog note`, `aw specs new`, `aw show`, and `legacy_context`/`meta_context` parity tests, plus a mutation proof (E-03).
4. Run the narrowed test suites, bare `python3 -m pytest`, and `aw ipd lint --phase pre-transition rntx9a` (E-04).

```mermaid
flowchart TD
    Start["Resolve metadata state root for repo_root / ctx"] --> CheckBackend{"Stored records_backend == 'home'?"}
    CheckBackend -->|No| Keep["Keep resolved logical_roots['state'] (or repo/.aw/state for unconfigured)"]
    CheckBackend -->|Yes| CheckOverride{"state == repo_root/.aw/state?"}
    CheckOverride -->|"No (clean-delta or explicit local.json state_root)"| Keep
    CheckOverride -->|"Yes (tracked mode default in-target state)"| HomeState["Return AW_HOME/projects/<project_id>/state"]
    HomeState --> Consumers["legacy_context, meta_context, artifact_meta._meta_state_root -> locks/, operation_journal/, index.db"]
    Keep --> Consumers
```

## Deferred / out of scope (with reason)

- Changing `project_context.resolve_project_context` `logical_roots["state"]` or `physical_classes["state_durable"]`/`["state_runtime"]` for `delivery_mode: tracked` with `records_backend: home`: governed by `spec 20260810-1447-01` Section 5 (`delivery_mode` controls `state_durable` and `state_runtime`, while `records_backend` controls `records`) and outside backlog `vo0y6q`.
  - Carrier-Declined: `spec 20260810-1447-01` Section 5 already defines the `tracked` vs `clean-delta` split for general project state; only `artifact_meta` locks, journals, and cache tied to `home`-backed records need `AW_HOME` routing here.
- Routing `aw specs new --apply` locks on a bare UNCONFIGURED repository (no stored `project.json`): `kfnfji` OQ-04 declined unifying unconfigured-repo divergence (`aw specs new` vs `aw backlog new`) as pre-existing behavior outside stored `records_backend: home`.
  - Carrier-Evidence: .aw/records/plans/executed/20261015-cleantgt-01-kfnfji-route-every-records-reader-and-writer-through-one-records-ro.ipd.md

## Scope check

- Over-scope: none. Every listed file directly owns `artifact_meta` state resolution (`agent_workflows/artifact_meta.py`), the CLI `MetaContext` wrapper (`agent_workflows/meta_cli.py`), or the home-records outcome suite (`tests/test_records_root_accessor.py`).
- Under-scope: none. `backlog.py`, `specs.py`, `prompts.py`, `research_cmd.py`, `artifact_adopt.py`, `set_records.py`, and `status_set.py` all obtain their state root from `artifact_meta.legacy_context`, so fixing `artifact_meta.py` covers every metadata writer and reader without touching each caller module.

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_records_root_accessor.py` (all tests pass, including `test_home_records_reproduction_backlog` and the new lock-path and parity cases).
- Mutation proof on `_home_state_override` in `agent_workflows/artifact_meta.py` demonstrating `test_home_records_reproduction_backlog` fails with `?? .aw/state/` when disabled and passes when restored.
- `python3 -m pytest -o addopts="" tests/test_records_root_accessor.py tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_cache.py tests/test_index_rebuild.py tests/test_project_layout.py tests/test_m0001_layout_stage.py tests/test_backlog.py tests/test_writers_obligations.py`.
- Bare `python3 -m pytest` (paste actual summary line).
- `aw ipd lint --phase pre-transition rntx9a` conforming.

## Spec / documentation sync

- None. `spec 4sd62s` Section 4.5 already states that records, `meta/*.jsonl`, and the cache follow the resolved project placement without assuming `<repo>/.aw/`. No CLI flags or user-facing documentation change.

## Open questions

### OQ-01: Should `project_context.resolve_project_context` itself move `logical_roots["state"]` to `AW_HOME` when `records_backend` is stored `home` and `delivery_mode` is `tracked`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: No. Measured in `agent_workflows/project_context.py::resolve_project_context`, `agent_workflows/placement_switch.py`, `tests/test_project_layout.py::PhysicalPolicyMatrixTests::test_e01`, and `tests/test_records_root_switch_execute.py`: `delivery_mode` (`tracked` vs `clean-delta`) governs `state_durable` (`install.json`, `history/`) and `state_runtime` under `spec 20260810-1447-01` Section 5. Moving `artifact_meta`'s metadata state (`locks/meta-*.lock`, `operation_journal/`, `index.db`) in `artifact_meta.legacy_context`, `artifact_meta._meta_state_root`, and `meta_cli.meta_context` resolves `vo0y6q` without altering `install_history` or `placement_switch` contracts.

### OQ-02: Should `artifact_meta` keep an explicit `local.json` `state_root` override if one is present alongside `records_backend: "home"`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. In `agent_workflows/project_context.py::resolve_project_context`, `merged_local_binding.get("state_root")` takes precedence over `delivery_mode`. Checking `state.resolve() == (repo_root / ".aw" / "state").resolve()` before redirecting to `AW_HOME` ensures an explicit machine-local `state_root` binding is preserved while the default in-target `.aw/state` fallback is redirected to `AW_HOME`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `git diff agent_workflows/artifact_meta.py` showing `_home_state_override`, `_meta_state_root`, `legacy_context`, and all `artifact_meta` state lookups routed through `_meta_state_root` with `project_context.py` untouched (`git diff agent_workflows/project_context.py` empty), plus pasted Python output showing `artifact_meta.legacy_context(target)` returns `<AW_HOME>/projects/<id>/state` for stored `records_backend: "home"` and `<target>/.aw/state` for an unconfigured repo.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff agent_workflows/meta_cli.py` showing `meta_context` delegating to `artifact_meta.legacy_context`, plus pasted output showing `meta_cli.meta_context(target).state_root == Path(artifact_meta.legacy_context(target).logical_roots["state"])` for both a stored `records_backend: "home"` repo and a `repository`-backed repo.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_records_root_accessor.py` output showing all tests including `test_home_records_reproduction_backlog` and every added lock-location, `backlog note`, `specs new`, `aw show`, and parity test PASSED, plus the pasted failure output from the mutation proof (showing `?? .aw/state/`) and the subsequent restored pass output.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the actual summary line of `python3 -m pytest -o addopts="" tests/test_records_root_accessor.py tests/test_artifact_meta_legacy_writer.py tests/test_artifact_meta_cache.py tests/test_index_rebuild.py tests/test_project_layout.py tests/test_m0001_layout_stage.py tests/test_backlog.py tests/test_writers_obligations.py`, the actual summary line of bare `python3 -m pytest`, and the `aw ipd lint --phase pre-transition rntx9a` conforming output.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved rntx9a --by-human`). Execute in an isolated worktree via `aw work begin rntx9a` (or under `aw oc run` / `aw agy run`), then `aw ipd begin rntx9a`, and perform E-01..E-04 in order. Commit per task or once at completion through `aw commit rntx9a -- <paths>` after verifying `git diff --cached --name-only`; never `git add -A`, never push, never tag. Every `V-*` must paste actual observed output. Run `aw ipd lint --phase pre-transition rntx9a` before finalizing (`aw ipd finalize rntx9a` when executing by hand). Inherits `- Blocks-Release: next` and `- From-Backlog: vo0y6q` from backlog item `vo0y6q`.
