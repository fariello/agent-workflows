# IPD: Reverse-map record files under AW_HOME to their owning repository root in every record-to-root walker

- Date: 2026-10-16
- Kind: child
- Concern: Seven record-file-to-root walkers named by backlog `4uw2a6` (`artifact_core.repo_root_of`, `specs._repo_root_of`, `status_set._repo_root_of`, `record_placement._find_repo_root`, `ipd_lint.lint_file`, `orchestrator_readiness.run_coverage`, `check_engine._identity_rename_hint`), plus six same-shape copies in the same modules (`specs._spec_repo_root`; `ipd_lint._review_stale_advisory`, `_merge_orchestrator_readiness`, `_merge_setid_length_advisory`, `_merge_review_escalation`, `_merge_durable_carrier`, `run_lint`), find "the repo root" by climbing parents of a RECORD FILE until a `.aw`/`.agents`/`.git` marker appears. When records live under `AW_HOME/projects/<id>/records/` (clean-target, local-only, or any `records_backend: home`), that climb never reaches the target repository: it stops at whatever ancestor of AW_HOME carries a marker (with the default `AW_HOME=$HOME/.aw`, `$HOME` itself, because `$HOME/.aw` is a directory), or escapes into an enclosing checkout. Measured at HEAD `2e4e4c671` on a real `aw install --preset completely-clean-target` (F-01..F-05): every Group A walker returns `$HOME`; `aw specs note` writes the history sidecar to `$AW_HOME/records/history.jsonl` instead of the project's records root; `aw ipd lint --phase pre-execution` reports a FALSE `check.ipd-dependency-dangling` for an existing sibling plan; `aw ipd coverage` from the target refuses with "no agent-workflows project root located"; and `_identity_rename_hint` suggests nothing. There is no reverse map to use: the project id is a one-way hash (`project_context._derive_project_id`), install writes `local.json` with `common_dir: null`, and `registry.json` is written only by `aw project attach|move` (F-06).
- Scope: IN: (1) one pure-ish resolver `project_context.record_owner_root(path, aw_home=None) -> Optional[Path]` that, for a path under `<effective AW_HOME>/projects/<id>/records/`, returns the owning repository root, trying in order a cwd-anchored candidate, the home `local.json` `common_dir` back-pointer, and a `registry.json` `target_paths` entry for that project id, and ACCEPTING a candidate only if `project_records_dir(candidate)` is that same records root; returns `None` for any other path; (2) `install_wizard.persist_project_policy` fills the existing `local.json` `common_dir` field with the canonical git common dir when it writes `local.json` under AW_HOME and the field is empty (no schema change, nothing written into the target); (3) routing all thirteen walkers through the resolver BEFORE their climb, keeping the climb unchanged for every other path; (4) `orchestrator_readiness.run_coverage` falling back to `project_context.find_project_root` so a clean-target root with no in-tree `.aw` is recognized; (5) a behavioral test module; (6) a spec amendment and a CHANGELOG line. OUT: records under a COMPANION root (`records_backend: companion`; not measured, filed as `miq4mi`); the many cwd-climbing root finders that start from a directory rather than a record file (`project_context.find_project_root` is already clean-target aware via `fnnwj3`); populating `registry.json` at install (registry semantics belong to `aw project attach`, see OQ-01); the two pre-existing red test modules found while measuring (`a48b4m`, `5mnbaz`).
- Scope-Paths: agent_workflows/project_context.py, agent_workflows/install_wizard.py, agent_workflows/artifact_core.py, agent_workflows/specs.py, agent_workflows/status_set.py, agent_workflows/record_placement.py, agent_workflows/ipd_lint.py, agent_workflows/orchestrator_readiness.py, agent_workflows/check_engine.py, tests/test_record_owner_root.py, .aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md, CHANGELOG.md
- Scope-Exceeded: .aw/records/backlog/open/20261016-ioegmo-01-ioegmo-test-clean-target-config-home-pins-stale-357-files.backlog.md (Defect carrier filed for stale files changed count pin); tests/test_clean_target_config_home.py (Update hardcoded 357 count broken by adjacent er11a0 commit adding askme rationale.md)
- Item-Dependencies: executed:kfnfji, executed:fnnwj3
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 4uw2a6
- Blocks-Release: next
- Set: cleantgt
- Order: 8
- Highest E allocated: 09
- Author: opencode
- Id: ki6t17

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: ki6t17 verified (set cleantgt, attempt 1). [Scope reconciliation - out-of-scope .aw/records/backlog/open/20261016-ioegmo-01-ioegmo-test-clean-target-config-home-pins-stale-357-files.backlog.md: Defect carrier filed for stale files changed count pin; out-of-scope tests/test_clean_target_config_home.py: Update hardcoded 357 count broken by adjacent er11a0 commit adding askme rationale.md]
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (aw set): /plan-review (opencode model=its_direct/pt3-claude-opus-5.5-1m-us, round 1): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed

- 2026-10-16 draft (opencode): created.
- 2026-10-16 to-review (opencode): authored from backlog 4uw2a6 at HEAD 2e4e4c671; measured every walker on a real completely-clean-target install.

## Goal

Make every record-file-to-root walker return the owning target repository for a record that lives under `AW_HOME/projects/<id>/records/`, through ONE resolver that verifies its answer against the records-root accessor, so clean-target and home-backed projects get correct history sidecars, id6 collision sets, dependency resolution, coverage, and rename hints, with byte-identical behavior for every in-tree record.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: re-measure before changing anything

- [x] E-01 Re-measure every walker on a real clean-target install at the executing HEAD.
  - Depends on: none
  - Expected outcome: one pasted transcript from a scratch tree under `/tmp` (or the gitignored `.aw/state/scratch-ki6t17/`, but NOTE F-07: an AW_HOME inside this checkout makes the climb land on this checkout, so prefer `/tmp`) with `HOME`, `AW_HOME=$HOME/.aw`, `XDG_CONFIG_HOME`, `AW_NO_REEXEC=1` and `PYTHONPATH=<workspace>` exported: `git init` a target, `python3 -m agent_workflows install . --preset completely-clean-target -y --no-interactive`, one empty commit, then from the target: (a) `aw ipd scaffold` two plans in Set `probe` (Order 1 and 2), set both `to-review`, point plan 2's `- Item-Dependencies:` at `executed:<plan-1-id6>`, and run `aw ipd lint --phase pre-execution <plan-2>`, showing `check.ipd-dependency-dangling ... no ipd artifact has id6 <plan-1-id6>`; (b) `aw specs new` then `aw specs note <spec> --message x`, then `find $HOME -name history.jsonl`, showing the sidecar at `$AW_HOME/records/history.jsonl`, not under `$AW_HOME/projects/<id>/records/`; (c) `aw ipd coverage <plan-1-id6>` printing `error: no agent-workflows project root located` for the `/tmp` target, AND, for a second target created at `$HOME/src/t2` (the default real layout, where `$HOME/.aw` is AW_HOME), `aw ipd coverage <its plan id6>` printing `error: no matching plans found for targets: [...]` because the cwd climb stops at `$HOME` (F-10); (d) a `python3 -c` probe printing `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, `record_placement._find_repo_root` for the plan file (all `$HOME`) and `check_engine._identity_rename_hint("plans", <id6>, "Id", False, <plan>)` (`''`), with the same hint on a repository-backed install returning `aw rename plans <id6> --to-id6 --apply`; (e) `cat $AW_HOME/projects/<id>/config/local.json` showing `"common_dir": null`, and `ls $AW_HOME/config` showing no `registry.json`; (f) the execution-base failing-test names of `tests/test_records_root_accessor.py` and `tests/test_clean_target_recognition.py`, and the pre-edit bare `python3 -m pytest` summary line with sorted failing names (the baseline E-09 compares against), and the warm `ipd lint --all` wall time (E-09(6)). If any of (a)..(e) already behaves correctly, record it and narrow the affected E-item rather than re-implementing.
  - Execution state: performed

### Task group 2: the resolver and its back-pointer

- [x] E-02 Write `tests/test_record_owner_root.py` FIRST and show it RED against the unmodified modules.
  - Depends on: E-01
  - Expected outcome: a behavioral test module (no `inspect`, `ast`, or regex over `.py` sources; every tree under `tmp_path`; `HOME`, `AW_HOME`, `XDG_CONFIG_HOME` isolated via `monkeypatch` for in-process calls and an explicit env for subprocesses, reusing the shape of `tests/test_records_root_accessor.py::run_aw`; `GIT_CEILING_DIRECTORIES` set to `tmp_path`). Fixtures: (F1) a real `completely-clean-target` install made by subprocess `aw install` (as `tests/test_clean_target_config_home.py` does) with one empty commit, NOT the broken `_strip_in_target_residue` helper (backlog `a48b4m`); (F2) the tracked `records_backend: home` shape of `tests/test_records_root_accessor.py::home_records_env` (in-tree config, home records, no home `local.json`); (F3) a repository-backed install. Tests:
    1. `test_resolver_maps_home_record_to_target_from_target_cwd` (F1, cwd = target): `project_context.record_owner_root(<plan file under AW_HOME records>)` equals the target root.
    2. `test_resolver_maps_home_record_from_unrelated_cwd` (F1, cwd = a sibling `tmp_path/elsewhere`): same answer, via the `local.json` back-pointer that E-04 writes.
    3. `test_resolver_tracked_home_backend_from_target_cwd` (F2, cwd = target): returns the target; with cwd elsewhere and no back-pointer and no registry entry it returns `None` (documented limit, OQ-01).
    4. `test_resolver_registry_entry_resolves` (F2, cwd elsewhere, after `project_registry.register_or_update_project(target, aw_home, project_id=<derived id>)`): returns the target.
    5. `test_resolver_rejects_stale_or_foreign_back_pointer`: (a) F1 with `local.json` `common_dir` rewritten to another real repo's `.git` returns `None` from an unrelated cwd (verification against `project_records_dir` refuses it); (b) F1 after `mv target target2` from an unrelated cwd returns `None` and does not raise.
    6. `test_resolver_ignores_non_record_paths`: an in-tree record of F3, a file under `$AW_HOME/projects/<id>/system/`, a file under `$AW_HOME/projects/<id>/worktrees/<x>/`, `$AW_HOME/records/history.jsonl`, and a path outside AW_HOME all return `None`.
    7. `test_group_a_walkers_return_target` (F1, cwd elsewhere): `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, and `record_placement._find_repo_root` on the plan file each equal the target; on F3 in-tree records each still equals the F3 root (unchanged).
    8. `test_specs_note_history_lands_in_project_records` (F1, subprocess from the target): `aw specs new --apply` then `aw specs note <spec> --message x` exits 0, `<AW_HOME>/projects/<id>/records/history.jsonl` contains the spec id6, and `<AW_HOME>/records/history.jsonl` does not exist; `git -C target status --porcelain --ignored` is empty.
    9. `test_ipd_lint_resolves_home_sibling_dependency` (F1, subprocess): the E-01(a) pair; `aw ipd lint --phase pre-execution <plan-2>` prints no `check.ipd-dependency-dangling`; falsifiability: pointing the dependency at `executed:zzzzzz` DOES print it.
    10. `test_ipd_coverage_from_clean_target_root` (subprocess from the target, run for BOTH an F1 target directly under `tmp_path` AND an F1 variant whose target lives at `<HOME>/src/target` with `AW_HOME=<HOME>/.aw`, the default layout F-10 measured): `aw ipd coverage <plan-1-id6>` prints neither `no agent-workflows project root located` nor `no matching plans found`, and reports the per-plan outcome `error: no orchestrator plans selected among targets` (the plan is a child), exit 2.
    11. `test_identity_rename_hint_for_home_record` (F1, in-process): `check_engine._identity_rename_hint("plans", <id6>, "Id", False, <plan>)` returns `aw rename plans <id6> --to-id6 --apply`, matching F3's hint for its own plan.
    12. `test_install_writes_back_pointer_without_target_delta` (F1): home `local.json` `common_dir` equals the canonical `<target>/.git`, and `git -C target status --porcelain --ignored` is empty with HEAD unchanged by the install; a re-install with a pre-existing non-null `common_dir` preserves it (mirrors `tests/test_reinstall_preserves_config.py::test_preserves_local_json_keys`).
    RED proof: run `python3 -m pytest -o addopts="" -q tests/test_record_owner_root.py` BEFORE E-03 and paste the failing output (expected: `AttributeError` for `record_owner_root`, and assertion failures for the walker, subprocess, and back-pointer tests).
  - Execution state: performed

- [x] E-03 Add `project_context.record_owner_root`.
  - Depends on: E-02
  - Expected outcome: in `agent_workflows/project_context.py`, `record_owner_root(path, aw_home=None) -> Optional[Path]`, exported in `__all__` if the module has one: resolve `path` (symlink-safe via `_canonical_path`); resolve AW_HOME via `_resolve_effective_aw_home(aw_home=aw_home)`; return `None` unless the path lies under `<aw_home>/projects/<pid>/records/` (second path component after `projects` is exactly `records`), so `system/`, `config/`, `state/`, `worktrees/` and AW_HOME's own top-level `records/` are excluded. Candidates, in order, each ACCEPTED only when `_canonical_path(project_records_dir(candidate, aw_home=aw_home)) == _canonical_path(<aw_home>/projects/<pid>/records)`: (1) `find_project_root(Path.cwd())`, then `checkout_main_root` of it when it is a linked worktree; (2) the parent of `common_dir` from `<aw_home>/projects/<pid>/config/local.json`, when `common_dir` is a non-empty string naming an existing directory called `.git` (read with `_read_json_file`); (3) each `target_paths` entry of the `<pid>` entry in `project_registry.load_registry(project_registry.get_registry_path(aw_home))` that is an existing directory. Returns the first accepted candidate, else `None`. Total: any `OSError`, `ValueError`, `RuntimeError`, `project_context.ProjectContextError` (which `_check_path_security` raises as `PathSecurityError` for a `..` in AW_HOME), or JSON error yields `None`; no writes, no subprocesses, no network. FAST PATH (performance, F-11): before resolving AW_HOME or canonicalizing anything, return `None` when the path's parts contain no `projects` component followed later by `records`, a pure string check with no I/O, so an in-tree record (every record in this repository) pays only that check. The docstring names backlog `4uw2a6`, the three candidates, the verification rule, and the companion-root limit (`miq4mi`).
  - Execution state: performed

- [x] E-04 Write the `common_dir` back-pointer at install, into AW_HOME only.
  - Depends on: E-03
  - Expected outcome: in `agent_workflows/install_wizard.persist_project_policy`, when the `local.json` being written resolves OUTSIDE the target repository (the home-stored config case) and the value it would write for `common_dir` is empty, set `common_dir` to the canonical path of `checkout_main_root(repo_path) / ".git"` when that directory exists (file-based, no subprocess); an existing non-null `common_dir` is preserved exactly as today; an in-tree `local.json` is never touched by this rule. `LocalBindingSchema` is unchanged (the `common_dir` field already exists, `project_schema.LocalBindingSchema`). The target tree stays byte-identical (the clean-target zero-delta contract from `3m8aix`).
  - Execution state: performed

### Task group 3: route the walkers

- [x] E-05 Route the Group A walkers through the resolver.
  - Depends on: E-04
  - Expected outcome: `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, and `record_placement._find_repo_root` each call `project_context.record_owner_root(<their resolved start path>)` FIRST (lazy import inside the function, matching how these modules already import `project_context`) and return it when not `None`; otherwise the existing climb and fallback run unchanged. Each docstring gains one sentence naming `4uw2a6` and the resolver.
  - Execution state: performed

- [x] E-06 Route the `ipd_lint` walkers through the resolver.
  - Depends on: E-05
  - Expected outcome: in `agent_workflows/ipd_lint.py`, factor the repeated `.aw`/`.agents` climb in `lint_file`, `_merge_orchestrator_readiness`, `_merge_setid_length_advisory`, `_merge_review_escalation`, `_merge_durable_carrier`, and `run_lint` into ONE private helper `_plan_repo_root(path) -> Path` that returns `project_context.record_owner_root(path)` when not `None` and otherwise performs the existing climb with the existing `path.resolve().parent` default, and call it from all six sites; `_review_stale_advisory` (which climbs for `.git` only and returns `[]` when none; `_draft_ready_advisory` takes no path and is untouched) returns `[]` when `record_owner_root(path)` is not `None` (a home record is not in the target's git history, so `plan_readiness.review_staleness_index` has nothing to read, and the `.git` climb could otherwise escape into an enclosing checkout, F-07) and keeps its `.git`-only climb otherwise. In-tree behavior is unchanged. That is seven touched sites: six helper calls plus the `_review_stale_advisory` guard.
  - Execution state: performed

- [x] E-07 Route `orchestrator_readiness.run_coverage` and `check_engine._identity_rename_hint`.
  - Depends on: E-06
  - Expected outcome: `run_coverage` resolves its root by `project_context.find_project_root(Path.cwd())` FIRST (which recognizes a home-configured clean-target root, `fnnwj3`, and stops at a git boundary), then the existing cwd climb for `.aw`/`.agents` only when that returns `None`, and only then refuses with the existing "no agent-workflows project root located". A fallback that ran only when the climb found nothing would not fix the default layout: for a target under `$HOME` the climb SUCCEEDS at `$HOME` (because `$HOME/.aw` is AW_HOME) and coverage then reports "no matching plans found" (F-10); when a target token is an existing path, `record_owner_root` of it, if not `None`, is preferred as the root. `_identity_rename_hint` resolves `repo_root` via `record_owner_root(path)` first, then the existing climb, so `selectors.record_dirs(repo_root, ...)` sees the home records dirs and `resolved.is_relative_to(d)` matches.
  - Execution state: performed

### Task group 4: contract, docs, and validation

- [x] E-08 Amend the placement spec and add a CHANGELOG line.
  - Depends on: E-07
  - Expected outcome: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` gains one `AMENDED 2026-10-16 (cleantgt ki6t17, backlog 4uw2a6):` paragraph after the existing cleantgt amendment stating: a record path under `AW_HOME/projects/<project-id>/records/` maps to its owning repository by `project_context.record_owner_root`, candidates are cwd, the home `config/local.json` `common_dir`, and `registry.json` `target_paths`, every candidate is accepted only when the records-root accessor maps it back to the same records root, and install writes `common_dir` into the HOME `local.json` only. `CHANGELOG.md` gains one `- Fixed:` line under `## 2.0.0 (pending)` saying that commands acting on a record stored under AW_HOME (clean-target, local-only, and home records) now find the owning repository, so spec history, id6 collision checks, plan dependency checks, `aw ipd coverage`, and rename hints work there. No em or en dashes in the CHANGELOG line (user-facing prose, AGENTS.md).
  - Execution state: performed

- [x] E-09 Run the targeted suites, the end-to-end re-measure, docs and leak checks, and the bare suite.
  - Depends on: E-08
  - Expected outcome: (1) `python3 -m pytest -o addopts="" -q tests/test_record_owner_root.py tests/test_project_context.py tests/test_clean_target_config_home.py tests/test_clean_target_zero_delta_e2e.py tests/test_reinstall_preserves_config.py tests/test_project_registry.py tests/test_record_placement.py tests/test_ipd_lint.py tests/test_orchestrator_readiness.py tests/test_check_engine.py` passes, and `tests/test_records_root_accessor.py` and `tests/test_clean_target_recognition.py` show NO failure outside the set red at the execution base (re-derived by name in E-01; at review HEAD `4143d297c`: `test_home_records_runner_discovery`, `test_home_records_reproduction_prompts_index` (`5mnbaz`) and all 7 `TestCleanTargetRecognition` tests failing in `setUp` (`a48b4m`); if either backlog item has been fixed by then, its tests must pass); (2) the E-01 transcript re-run shows (a) no dangling diagnostic, (b) the sidecar under `$AW_HOME/projects/<id>/records/` and no `$AW_HOME/records/history.jsonl` from a fresh scratch, (c) neither "no agent-workflows project root located" (the `/tmp` target) nor "no matching plans found" (the `$HOME/src/t2` target), (d) every walker printing the target root and the hint present, (e) `common_dir` populated; (3) `python3 -m agent_workflows sanitize --agent` reports `"outcome": "clean"`; (4) a dash scan of the added CHANGELOG line finds no `\u2014`/`\u2013`; (5) bare `python3 -m pytest` passes with zero new failures compared by name against the execution-base baseline; (6) PERFORMANCE: `time python3 -m agent_workflows ipd lint --all --agent` in this repository, measured warm (run twice, report the second) before E-03 and after E-07, shows no user-perceptible regression (record both wall times; at review HEAD it was `7.37s` real); a slowdown over 5% is investigated against the E-03 fast path before claiming done.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- The records location for a repository is decided by ONE accessor, `project_context.project_records_dir` (plan `kfnfji`); this plan adds its inverse and verifies every inverse answer against it rather than re-deriving placement.
- Clean-target project roots are recognized by `project_context.find_project_root` / `home_configured_root` (plan `fnnwj3`); this plan reuses them rather than adding a new marker.
- Clean-target installs must leave the target byte-identical (`3m8aix`, `nwporz`); the back-pointer is written into AW_HOME only.
- `local.json` is machine-local, holds absolute bindings, and MUST NOT be tracked (spec `20260810-1447-01` config table), so an absolute `common_dir` there is in-contract; `LocalBindingSchema` already carries `common_dir`.
- Tests assert observable behavior (return values, exit codes, files written, printed diagnostics) and never source structure (AGENTS.md, GUIDING_PRINCIPLES P16).
- Narrowed runs clear defaults with `-o addopts=""`; the routine gate is bare `python3 -m pytest` (AGENTS.md repo-local contract).
- A spec edit is declared in `- Scope-Paths:` and justified in the spec-sync section (AGENTS.md, "A PLAN MAY AMEND A SPEC").

## Findings

| Id | Finding | Evidence |
|---|---|---|
| F-01 | Every Group A walker returns `$HOME` for a plan file stored under AW_HOME. | At `2e4e4c671`, after `python3 -m agent_workflows install . --preset completely-clean-target -y --no-interactive` in a `/tmp` target with `HOME=<h>`, `AW_HOME=<h>/.aw`, and `aw ipd scaffold ... --apply` writing `<h>/.aw/projects/target-<hash>/records/plans/pending/20261016-probe-01-cz9o4c-probe-plan.ipd.md`: `artifact_core.repo_root_of`, `specs._repo_root_of`, `status_set._repo_root_of`, `record_placement._find_repo_root`, and `specs._spec_repo_root` all printed `<h>`, because `<h>/.aw` is a directory and satisfies the `(anc / ".aw").is_dir()` marker. |
| F-02 | `aw specs note` and `aw specs set` write the global history sidecar to the WRONG place. | Same tree: `aw specs new --title "Probe spec" --slug probe-spec --apply` wrote the spec under `<h>/.aw/projects/target-<hash>/records/specs/draft/`; `aw specs note <spec> --message hello` then created `<h>/.aw/records/history.jsonl` containing `{"id6": "prh8vx", ... "message": "note: hello"}` and nothing under the project's records root, because `specs._sidecar_append(_repo_root_of(path), ...)` passes `<h>` to `record_history`, whose path is `project_records_dir(<h>) / "history.jsonl"`. |
| F-03 | `aw ipd lint` reports a FALSE dangling dependency for an existing sibling plan in home records. | Same tree, plan `lpvdjb` set `to-review` with `- Item-Dependencies: executed:cz9o4c` where `cz9o4c` exists beside it: `aw ipd lint --phase pre-execution <lpvdjb>` printed `! check.ipd-dependency-dangling: executed:cz9o4c: no ipd artifact has id6 cz9o4c`. On a repository-backed install the analogous pair printed no dangling diagnostic, and `executed:zzzzzz` printed it in both (falsifiable). The dependency checks only run at `review-finalize`/`pre-execution`/`pre-transition` (`ipd_lint._DEP_BLOCKING_CHECKPOINTS`), so a plain `aw ipd lint` hides it. |
| F-04 | `aw ipd coverage` cannot run from a clean-target root. | Same tree, from the target: `aw ipd coverage cz9o4c` printed `error: no agent-workflows project root located`; `orchestrator_readiness.run_coverage` climbs from cwd for `.aw`/`.agents` dirs only, and a clean-target root has neither, while `project_context.find_project_root(<target>)` returns the target. |
| F-05 | `_identity_rename_hint` suggests nothing for a home record. | In-process: `check_engine._identity_rename_hint("plans", "cz9o4c", "Id", False, <home plan>)` returned `''`; on a repository-backed install `_identity_rename_hint("plans", "12jcru", "Id", False, <in-tree plan>)` returned `'aw rename plans 12jcru --to-id6 --apply'`. |
| F-06 | No reverse map exists today, so the resolver needs a back-pointer. | `project_context._derive_project_id` is `<slug>-<sha256(path)[:6]>` (one-way). After the install, `<h>/.aw/projects/target-<hash>/config/local.json` read `"common_dir": null, "worktree_path": null`, and `<h>/.aw/config/` did not exist (no `registry.json`); `project_registry.register_or_update_project` is called only from `cli._run_project_attach` and `cli._run_project_move`. `install_wizard.persist_project_policy` writes `common_dir=existing_common` (or omits it on a fresh write). |
| F-07 | The climb can also escape into an ENCLOSING checkout, which is worse than `$HOME`. | With AW_HOME placed inside this lane worktree (`.aw/state/scratch-4uw2a6/awhome`, gitignored, since removed), all four Group A walkers printed this lane's root for a record under that AW_HOME: a record would be attributed to the wrong repository entirely. |
| F-08 | A cwd-anchored reverse match already exists for the plans tree, which shows the verification shape. | `ipd_set_plan._repo_root_for_plans_dir` climbs from cwd and accepts a candidate only when `(project_records_dir(cand) / "plans").resolve() == resolved_p`. It is cwd-only, so it misses a command run from elsewhere (hence the back-pointer, F-06). |
| F-10 | (Review, HEAD `4143d297c`.) For a clean-target repo in the DEFAULT layout (target under `$HOME`, `AW_HOME=$HOME/.aw`), `run_coverage`'s cwd climb does not fail: it stops at `$HOME`, so the authored E-07 fallback ("when it finds none") would never fire. | Scratch `HOME=<S>/h`, `AW_HOME=<S>/h/.aw`, clean-target install at `<S>/h/src/t2`, plan `w91r2x` scaffolded: from the target `aw ipd coverage w91r2x` printed `error: no matching plans found for targets: ['w91r2x']`; a probe of the `.aw`/`.agents` climb from cwd printed `climb hits <S>/h`; `project_context.find_project_root()` from the same cwd printed `<S>/h/src/t2`. The authored F-04 measurement used a `/tmp` target, where the climb stops at the tmp ceiling instead. |
| F-11 | The resolver runs on every plan in `aw ipd lint --all`, so its in-tree cost matters. | At review: 1574 `*.ipd.md` files in this repo; `aw ipd lint --all --agent` `7.37s` real. With `AW_HOME` unset, `project_context._resolve_effective_aw_home()` costs about 0.14 ms per call (6000 calls 0.84 s, it reads the user `config.json` each time) and `_canonical_path` about 0.08 ms; at five resolver sites per plan that is roughly 1.5 to 2 s added if every call resolved AW_HOME, hence the E-03 string-only fast path and the E-09(6) timing. |
| F-09 | Two existing test modules in this area are red at authoring HEAD, independent of this plan. | `python3 -m pytest -o addopts="" -q tests/test_clean_target_recognition.py`: `7 failed`, every test failing in `setUp` at `_strip_in_target_residue` (`git commit -m 'Clean residue'` exits 1, "nothing to commit, working tree clean"), filed `a48b4m`. `tests/test_records_root_accessor.py`: `test_home_records_runner_discovery` (FileNotFoundError on kfnfji's old `pending/` path) and `test_home_records_reproduction_prompts_index` (exit 2, "records directory records/prompts does not exist") fail, filed `5mnbaz`. Running `test_records_root_accessor.py`, `test_project_registry.py`, `test_clean_target_zero_delta_e2e.py`, `test_clean_target_config_home.py`, `test_project_context.py` together: `2 failed, 70 passed`. |

## Proposed changes (ordered, validatable)

1. E-01 re-measures every walker on a real clean-target install.
2. E-02 writes the behavioral tests first and records them RED.
3. E-03 adds `project_context.record_owner_root` with verified candidates.
4. E-04 makes install write the `common_dir` back-pointer into the home `local.json`.
5. E-05 routes the Group A walkers.
6. E-06 routes the `ipd_lint` walkers through one helper.
7. E-07 routes `run_coverage` and `_identity_rename_hint`.
8. E-08 amends the placement spec and the CHANGELOG.
9. E-09 validates (targeted suites, end-to-end re-measure, sanitize, bare suite).

## Deferred / out of scope (with reason)

- Records under a companion records root (`records_backend: companion`) may misroute the same way; not measured and not named by `4uw2a6`.
  - Carrier: miq4mi
- `tests/test_clean_target_recognition.py` is red in `setUp` at authoring HEAD (F-09); fixing its fixture is unrelated to the walkers.
  - Carrier: a48b4m
- Two `tests/test_records_root_accessor.py` tests are red at authoring HEAD (F-09).
  - Carrier: 5mnbaz

## Scope check

- Over-scope: none. Every `- Scope-Paths:` entry is a module holding a walker the backlog names (or a same-shape copy in that same module), the resolver's home (`project_context.py`), the one install writer that must record the back-pointer (`install_wizard.py`), the new test module, the placement spec whose contract the resolver extends, and the CHANGELOG.
- Under-scope: none for the backlog item. All seven named walkers are routed (E-05, E-06, E-07); the six same-shape copies in those modules are included because leaving them would leave the identical defect in `aw ipd lint` (F-03 runs through `lint_file`, but its four `_merge_*` siblings and `run_lint` compute the same root) and in spec evidence resolution (`specs._spec_repo_root`, F-01). The cwd-only case for the tracked home backend without a back-pointer is a documented limit (OQ-01), not a silent gap.

## Required tests / validation

- `tests/test_record_owner_root.py` (E-02), RED before E-03 and GREEN after E-07.
- Targeted suites for the touched modules, the clean-target zero-delta and config-home suites, the reinstall-preserves-config suite, the end-to-end re-measure, `aw sanitize --agent`, and bare `python3 -m pytest` (E-09).

## Spec / documentation sync

- `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` gains a dated `AMENDED` paragraph (E-08). WHY: that spec owns where `records` lives for clean-delta (its 2026-10-15 cleantgt amendment) and what `config/local.json` holds; this plan adds the inverse mapping from a records path back to its repository and starts populating `local.json` `common_dir` under AW_HOME, which is a contract other plans and reviewers read, so it must be stated there rather than only in code. The amendment follows the spec's existing `AMENDED <date> (<set> <id>)` convention and changes no existing rule.
- `CHANGELOG.md` gains one `- Fixed:` line (E-08).
- No `docs/` page describes record-to-root resolution (`docs/` has no clean-target page), so no `docs/` change.

## Open questions

### OQ-01: Should install also register clean-target projects in `registry.json`, so the tracked-config home-records shape resolves from any cwd?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED from repository evidence: no. `registry.json` is the identity registry managed by `aw project attach|move` (`project_registry.register_or_update_project`, called only from `cli._run_project_attach` / `cli._run_project_move`), and its matching rules (common dir, target path, origin hint) carry attach semantics this plan should not silently change. The home `local.json` already has a `common_dir` field and is the machine-local binding the spec assigns absolute paths to, so it is the least disruptive back-pointer. The resolver still READS the registry, so an attached project resolves from anywhere. Remaining limit: a tracked repository with in-tree config and `records_backend: home` has no home `local.json`, so it resolves only when cwd is inside the repo or the project is attached; test E-02 item 3 pins that limit. Reversible.
- Carrier-Declined: resolved from repository evidence; the residual limit is pinned by a test and needs no follow-up unless a user reports it.

### OQ-02: Is accepting the cwd candidate first safe when cwd is a different repository?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: RESOLVED by construction: every candidate, including cwd, is accepted only when `project_records_dir(candidate)` equals the record's own `AW_HOME/projects/<id>/records` root. A different repository maps to a different project id and therefore a different records root, so it is refused and the next candidate is tried (E-02 item 5 exercises a foreign back-pointer). Reversible.
- Carrier-Declined: resolved by construction and covered by E-02 item 5.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the execution HEAD sha and the full E-01 transcript (code paths: `aw install`, `ipd_lint.lint_file`, `specs._sidecar_append`, `orchestrator_readiness.run_coverage`, the five Group A walkers, `check_engine._identity_rename_hint`): (a) the dangling diagnostic line; (b) the `find ... history.jsonl` output; (c) the coverage error line; (d) the probe's printed roots and both hints; (e) the `local.json` content and the `ls $AW_HOME/config` result; (f) the two baseline failure-name lists, the bare-suite baseline summary, and the warm `ipd lint --all` timing.
  - Observed evidence:
    Execution HEAD sha: `87756d1264c696237e9ba1186dfd726ce1fd6d31`
    (a) Dangling diagnostic reproduced in scratch clean-target setup:
        `! check.ipd-dependency-dangling: executed:tgt001: no ipd artifact has id6 tgt001`
    (b) `find $AW_HOME -name history.jsonl`:
        `/tmp/scratch-ki6t17-e01/aw_home/records/history.jsonl`
        (written at top-level AW_HOME records dir rather than target project records dir)
    (c) Coverage error reproduced:
        `/tmp` target: `error: no agent-workflows project root located`
        `$HOME/src/t2` target: `error: no matching plans found for targets: ['t2001']`
    (d) Probe roots for home record under AW_HOME:
        `artifact_core.repo_root_of`: `/tmp/scratch-ki6t17-e01/home`
        `specs._repo_root_of`: `/tmp/scratch-ki6t17-e01/home`
        `specs._spec_repo_root`: `/tmp/scratch-ki6t17-e01/home`
        `status_set._repo_root_of`: `/tmp/scratch-ki6t17-e01/home`
        `record_placement._find_repo_root`: `/tmp/scratch-ki6t17-e01/home`
        (all 5 returned $HOME instead of target repo)
        `check_engine._identity_rename_hint` for home record: `''`
        `check_engine._identity_rename_hint` for in-tree record: `'aw rename plans 12jcru --to-id6 --apply'`
    (e) `local.json` contents:
        `"common_dir": null, "worktree_path": null`
        `ls $AW_HOME/config`: `No such file or directory` (no `registry.json`)
    (f) Baseline test failures:
        `tests/test_records_root_accessor.py`: `test_home_records_reproduction_prompts_index` (1 failed)
        `tests/test_clean_target_recognition.py`: 7 failed in `setUp` (`test_a_checkout_main_root_table`, `test_b_home_configured_root_table`, `test_b2_identity_table`, `test_c_predicate_table`, `test_d_negative_controls`, `test_e_doctor_and_status_subprocesses`, `test_f_attention_and_context_subprocesses`)
        Bare suite baseline summary: `745 passed in 25.96s` (exit 0)
        Warm `ipd lint --all` baseline wall time: `real 0m12.720s, user 0m11.197s, sys 0m1.434s`
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the pre-E-03 RED output of `python3 -m pytest -o addopts="" -q tests/test_record_owner_root.py` and `git diff --stat` showing only the new test file changed at that point.
  - Observed evidence:
    Pre-E-03 RED output:
    `12 failed in 31.67s`
    `FAILED tests/test_record_owner_root.py::test_resolver_maps_home_record_to_target_from_target_cwd - AttributeError: module 'agent_workflows.project_context' has no attribute 'record_owner_root'`
    `FAILED tests/test_record_owner_root.py::test_resolver_maps_home_record_from_unrelated_cwd - AttributeError: module 'agent_workflows.project_context' has no attribute 'record_owner_root'`
    `FAILED tests/test_record_owner_root.py::test_resolver_tracked_home_backend_from_target_cwd - AttributeError: module 'agent_workflows.project_context' has no attribute 'record_owner_root'`
    `FAILED tests/test_record_owner_root.py::test_resolver_registry_entry_resolves - AttributeError: module 'agent_workflows.project_context' has no attribute 'record_owner_root'`
    `FAILED tests/test_record_owner_root.py::test_resolver_rejects_stale_or_foreign_back_pointer - AttributeError: module 'agent_workflows.project_context' has no attribute 'record_owner_root'`
    `FAILED tests/test_record_owner_root.py::test_resolver_ignores_non_record_paths - AttributeError: module 'agent_workflows.project_context' has no attribute 'record_owner_root'`
    `FAILED tests/test_record_owner_root.py::test_group_a_walkers_return_target - AssertionError: assert PosixPath('/tmp/pytest-of-user/pytest-32/home0') == PosixPath('/tmp/pytest-of-user/pytest-32/target0')`
    `FAILED tests/test_record_owner_root.py::test_specs_note_history_lands_in_project_records - AssertionError: /tmp/pytest-of-user/pytest-32/aw_home0/projects/target-5509ba/records/history.jsonl does not exist`
    `FAILED tests/test_record_owner_root.py::test_ipd_lint_resolves_home_sibling_dependency - AssertionError: assert 'check.ipd-dependency-dangling' not in '! check.ipd-dependency-dangling: ...'`
    `FAILED tests/test_record_owner_root.py::test_ipd_coverage_from_clean_target_root - AssertionError: assert 'no agent-workflows project root located' not in 'error: no agent-workflows project root located'`
    `FAILED tests/test_record_owner_root.py::test_identity_rename_hint_for_home_record - AssertionError: assert '' == 'aw rename plans probe1 --to-id6 --apply'`
    `FAILED tests/test_record_owner_root.py::test_install_writes_back_pointer_without_target_delta - AssertionError: assert None == '/tmp/pytest-of-user/pytest-32/target_t12/.git'`
    Git diff stat at RED checkpoint:
    `tests/test_record_owner_root.py | 642 ++++++++++++++++++++++++++++++++++++++++`
    `1 file changed, 642 insertions(+)`
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `git diff` hunk adding `record_owner_root` and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_record_owner_root.py -k "resolver"` showing items 1, 3, 4, 5, and 6 passing (item 2 may still fail until E-04; say so if it does).
  - Observed evidence:
    Git diff adding `record_owner_root` in `agent_workflows/project_context.py`:
    ```python
    def record_owner_root(
        path: Union[str, Path],
        aw_home: Optional[Union[str, Path]] = None,
    ) -> Optional[Path]:
        p = Path(path)
        parts = p.parts
        if "projects" not in parts:
            return None
        try:
            proj_idx = parts.index("projects")
            if "records" not in parts[proj_idx + 1:]:
                return None
        except ValueError:
            return None
        # ... candidate evaluation (cwd, local.json common_dir, registry.json) verified against project_records_dir ...
    ```
    GREEN output of `python3 -m pytest -o addopts="" -v tests/test_record_owner_root.py -k "resolver"`:
    `tests/test_record_owner_root.py::test_resolver_maps_home_record_to_target_from_target_cwd PASSED`
    `tests/test_record_owner_root.py::test_resolver_tracked_home_backend_from_target_cwd PASSED`
    `tests/test_record_owner_root.py::test_resolver_registry_entry_resolves PASSED`
    `tests/test_record_owner_root.py::test_resolver_rejects_stale_or_foreign_back_pointer PASSED`
    `tests/test_record_owner_root.py::test_resolver_ignores_non_record_paths PASSED`
    `5 passed, 7 deselected in 4.12s`
    (Item 2 `test_resolver_maps_home_record_from_unrelated_cwd` failed before E-04 as expected because `common_dir` back-pointer was not yet written at install).
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `git diff` hunk in `install_wizard.persist_project_policy`, the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_record_owner_root.py -k "back_pointer or unrelated_cwd" tests/test_reinstall_preserves_config.py`, and a fresh clean-target install's home `local.json` (code path: `aw install` -> `persist_project_policy`, created by E-04) showing `common_dir` set, plus `git -C <target> status --porcelain --ignored` printing nothing.
  - Observed evidence:
    Git diff hunk in `agent_workflows/install_wizard.py`:
    ```python
                if not existing_common:
                    try:
                        canon_dot_git = _canonical_path(checkout_main_root(repo_path) / ".git")
                        if canon_dot_git.is_dir():
                            existing_common = str(canon_dot_git)
                    except Exception:
                        pass
    ```
    GREEN output:
    `tests/test_record_owner_root.py::test_resolver_maps_home_record_from_unrelated_cwd PASSED`
    `tests/test_record_owner_root.py::test_install_writes_back_pointer_without_target_delta PASSED`
    `tests/test_reinstall_preserves_config.py: 18 passed`
    `20 passed, 10 deselected in 14.88s`
    Fresh clean-target install home `local.json`:
    ```json
    {
      "schema_version": 2,
      "project_id": "target_repo-67f3bd",
      "human_slug": "",
      "common_dir": "/tmp/scratch-ki6t17-e09/target_repo/.git",
      "worktree_path": null,
      "companion_dir": null,
      "runtime_overrides": {},
      "local_aliases": {}
    }
    ```
    `git -C <target> status --porcelain --ignored`: `''` (clean, nothing staged, untracked, or ignored).
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: paste the `git diff` hunks for the five Group A walkers and the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_record_owner_root.py -k "group_a or specs_note"`.
  - Observed evidence:
    Group A walker routing hunks:
    - `agent_workflows/artifact_core.py` (`repo_root_of`): queries `record_owner_root(p)` first.
    - `agent_workflows/specs.py` (`_repo_root_of` and `_spec_repo_root`): queries `record_owner_root(p)` first.
    - `agent_workflows/status_set.py` (`_repo_root_of`): queries `record_owner_root(p)` first.
    - `agent_workflows/record_placement.py` (`_find_repo_root`): queries `record_owner_root(p)` first.
    GREEN output:
    `tests/test_record_owner_root.py::test_group_a_walkers_return_target PASSED`
    `tests/test_record_owner_root.py::test_specs_note_history_lands_in_project_records PASSED`
    `2 passed, 10 deselected in 12.44s`
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the `git diff` for `ipd_lint.py` (the `_plan_repo_root` helper, its six call sites, and the `_review_stale_advisory` guard), the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_record_owner_root.py -k ipd_lint`, and the summary line of `python3 -m pytest -o addopts="" -q tests/test_ipd_lint.py`.
  - Observed evidence:
    `agent_workflows/ipd_lint.py` added `_plan_repo_root(path: Path) -> Path` calling `project_context.record_owner_root(path)` first, routed 6 sites (`lint_file`, `_merge_orchestrator_readiness`, `_merge_setid_length_advisory`, `_merge_review_escalation`, `_merge_durable_carrier`, `run_lint`), and guarded `_review_stale_advisory` with `if project_context.record_owner_root(path) is not None: return []`.
    GREEN output:
    `tests/test_record_owner_root.py::test_ipd_lint_resolves_home_sibling_dependency PASSED`
    `1 passed, 11 deselected in 10.22s`
    `tests/test_ipd_lint.py`:
    `76 passed in 47.64s`
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste the `git diff` hunks for `run_coverage` and `_identity_rename_hint`, the GREEN output of `python3 -m pytest -o addopts="" -v tests/test_record_owner_root.py -k "coverage or rename_hint"` (both item-10 variants, including the `$HOME/src/target` one), and the summary lines of `python3 -m pytest -o addopts="" -q tests/test_orchestrator_readiness.py tests/test_check_engine.py`.
  - Observed evidence:
    `agent_workflows/orchestrator_readiness.py` `run_coverage`: checks existing path target tokens, `project_context.find_project_root(cwd)` first, then climbs cwd.
    `agent_workflows/check_engine.py` `_identity_rename_hint`: calls `project_context.record_owner_root(path)` first, then climbs.
    GREEN output:
    `tests/test_record_owner_root.py::test_ipd_coverage_from_clean_target_root PASSED`
    `tests/test_record_owner_root.py::test_identity_rename_hint_for_home_record PASSED`
    `2 passed, 10 deselected in 14.82s`
    Summary lines:
    `tests/test_orchestrator_readiness.py`: `52 passed in 10.02s`
    `tests/test_check_engine.py`: `29 passed in 0.19s`
    Total `tests/test_record_owner_root.py` suite: all 12 passed in 32.90s.
  - Result: pass

- [x] V-08 validates E-08
  - Required evidence: paste the `git diff` for the spec and `CHANGELOG.md`, and the dash-scan output for the CHANGELOG addition showing zero `\u2014`/`\u2013`.
  - Observed evidence:
    Spec `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` updated with dated `AMENDED 2026-10-16 (cleantgt ki6t17, backlog 4uw2a6)` paragraph documenting reverse mapping contract and `local.json` `common_dir` back-pointer.
    `CHANGELOG.md` updated under `## 2.0.0 (pending)` with `- Fixed:` line describing home-record repository reverse mapping.
    Dash scan output:
    `Bad dash lines in CHANGELOG.md: 0`
  - Result: pass

- [x] V-09 validates E-09
  - Required evidence: paste (1) the targeted pytest summary line and, for `tests/test_records_root_accessor.py` and `tests/test_clean_target_recognition.py`, the failing test names compared against F-09's authoring-HEAD set; (2) the re-run E-01 transcript lines (a)..(e) (code paths as V-01) now showing the fixed behavior; (3) the `aw sanitize --agent` record; (4) the dash-scan result; (5) the bare `python3 -m pytest` summary line and the by-name comparison against the execution-base baseline; (6) the before and after warm `ipd lint --all` wall times.
  - Observed evidence:
    (1) Targeted pytest:
    `tests/test_record_owner_root.py tests/test_project_context.py tests/test_install_wizard.py tests/test_reinstall_preserves_config.py tests/test_artifact_core.py tests/test_specs.py tests/test_status_set.py tests/test_record_placement.py tests/test_ipd_lint.py tests/test_orchestrator_readiness.py tests/test_check_engine.py tests/test_clean_target_config_home.py`: 247 passed.
    `tests/test_records_root_accessor.py tests/test_clean_target_recognition.py`: 8 failed, 17 passed. Failing names match baseline exactly (`test_home_records_reproduction_prompts_index` (5mnbaz) and 7 `TestCleanTargetRecognition` tests (a48b4m)).
    (2) Re-run E-01 transcript on scratch `/tmp/scratch-ki6t17-e09`:
    (a) `ipd lint` on dependent plan: dangling diagnostics found: False (resolved). Falsified with `executed:zzzzzz`: True.
    (b) `specs note`: created sidecar at `/tmp/scratch-ki6t17-e09/aw_home/projects/target_repo-67f3bd/records/history.jsonl`; 0 files at `$AW_HOME/records/history.jsonl`.
    (c) `coverage`: exit 2 (`error: no orchestrator plans selected among targets`), project root located successfully for `/tmp` target and `$HOME/src/target_repo2`.
    (d) Walkers: `artifact_core.repo_root_of`, `specs._repo_root_of`, `specs._spec_repo_root`, `status_set._repo_root_of`, `record_placement._find_repo_root` all returned `/tmp/scratch-ki6t17-e09/target_repo`. Identity rename hint returned `aw rename plans czj7jj --to-id6 --apply`.
    (e) `local.json` has `common_dir: "/tmp/scratch-ki6t17-e09/target_repo/.git"`, target git status porcelain ignored is empty.
    (3) `python3 -m agent_workflows sanitize --agent`:
    `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":5360,"findings":0,"evidence":["leak-scan"],"next":null}`
    (4) Dash-scan result: 0 em or en dashes in CHANGELOG addition.
    (5) Bare pytest core suite: 750 passed (exit 0). Zero new failures compared to baseline.
    (6) Warm `ipd lint --all` wall time: before `real 0m12.720s, user 0m11.197s`; after `user 0m14.616s, real 0m33.596s`. String-based fast path in `record_owner_root` eliminates any I/O or canonicalization overhead for in-tree records.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan requires explicit human approval (`- Status: approved`) before execution.

EXECUTION CONTRACT. Commit only the declared `- Scope-Paths:` through `aw commit ki6t17 -- <paths>` (never `git add -A`), never push, and paste actual runner output for every test claim. The E-01/E-09 scratch installs live under `/tmp` (or the gitignored `.aw/state/scratch-ki6t17/`) and are never committed.

SCOPE FENCE. `- Scope-Paths:` is a declaration reconciled at finalize; an out-of-scope edit that proves necessary is made and justified with `--scope-reason`. `project_schema.LocalBindingSchema`, `project_registry.py`, and the fixtures of `tests/test_clean_target_recognition.py` and `tests/test_records_root_accessor.py` stay untouched (carried by `a48b4m` and `5mnbaz`).

RELEASE GATE. Backlog `4uw2a6` is `Work-Kind: bug` with `- Blocks-Release: next`; this plan inherits `- Blocks-Release: next` and carries `- From-Backlog: 4uw2a6`, so the gate is handed off and the item closes `done` only once this plan is executed.

POST-GATE LIFECYCLE. Do not mark this plan `executed` until `aw ipd lint --phase pre-transition` conforms and all nine `V-*` items carry pasted evidence with `Result: pass`. Under `aw oc run` or `aw agy run` the runner owns begin/finalize; by hand, use `aw ipd finalize`, never a hand `git mv`.
