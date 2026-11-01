- Id: c1f6rd
- Status: open
- Set: awfed
- Priority: high
- Work-Kind: feature
- Summary: Federate AW projects across sibling repositories: project-qualified Item-Dependencies, multi-project attention, and registry registration on install

## Workflow history
- 2026-11-01 created (aw backlog): Filed at the maintainer's request (AceLM multi-repo layout decision 2026-11-01)

## Problem

A product split across several git repositories cannot be planned as one body of work with AW today. Each repository is its own AW project, and nothing connects them:

1. A plan in one repository cannot depend on a plan in another. The edge grammar is `executed:<id6>`, `exists:<type>:<id6>`, `state:<type>:<status>:<id6>` with no project qualifier (`ipd_schema._parse_item_dependency_edge`). Targets resolve only against the local project (`check_engine.build_dependency_index(repo_root)` over `status_set.inventory_all_artifacts(repo_root)`). A cross-repository reference is reported as dangling: `dangling Item-Dependencies target: executed:mzi119: no ipd artifact has id6 mzi119. Refusing before making changes.` (probe, 2026-11-01).
2. `aw attention` and `aw oc run` see one project. An orchestrator plan cannot track a child plan in a sibling repository as a typed `CONFIRM <id6> REACHED <status>` row (lint IPD-S408 `child-unauthored`), so the dependency is written in prose and no tool checks it.
3. `aw install` does not register the project in the AW_HOME registry. Only the attach and move verbs call `project_registry.register_or_update_project` (`cli.py` attach and move handlers). A fresh install in a probe created no `registry.json`. Any federation that looks up sibling projects through the registry therefore finds nothing.

Observed in AceLM (maintainer decision 2026-11-01): the product is split into separate repositories (`acelm` design records, `acelm-website`, and planned `deck`, `dealer`, and client repositories) so that contractors who work on Deck or the clients never receive Dealer code or Dealer's confidential records. The Set `deckdealer` in `acelm` already has one child plan (`99mu2h`) in `acelm-website` whose dependencies on `acelm` plans `2wm4rk` and `d6eszo` exist only as prose.

## Alternatives considered and rejected (evidence from probes in a scratch directory, 2026-11-01)

- **Monorepo.** Every AW surface works, but every contributor receives all code and records. Rejected for AceLM by the maintainer because of contractor isolation.
- **Parent repository with git submodules, no `.aw/` in the submodules.** `aw commit <plan> -- deck/src/lib.rs` fails with `fatal: Pathspec 'deck/src/lib.rs' is in submodule 'deck'`; `aw commit -- deck` is refused by `git_commit_helper.offer_commit` as a directory argument; `aw ipd finalize` marked the plan executed while the submodule change stayed uncommitted ("Disregarded 1 path(s) not owned by this execution ... deck"), which loses work silently. `git worktree add` on the parent leaves submodule directories empty, and lane teardown needs `--force`, which destroys unpushed submodule commits. The superseded layout spec `20260809-2211-01` section 20.5 already rejected submodules as a default. Worktree-isolation research `x03wgn` open item 14 is still unresolved.
- **Parent repository with submodules, each with its own `.aw/`.** Behaves exactly like separate repositories; the parent adds nothing for AW.
- **One companion records repository serving several code repositories, with repository-aliased Scope-Paths.** Not supported and costly to add: `ipd begin` and `ipd finalize` refuse a plan outside the repository root (`ipd_lifecycle.run_begin` and `run_finalize` plan-path check); Scope-Paths reject `..` and absolute paths (`ipd_schema._scope_path_entry_error`, IPD-M106); `storage.validate_companion_preflight` raises `IdentityConflictError` for a second target; lanes lose the companion binding because `.aw/config/` is untracked. Kept as possible later work (see "Out of scope"), not this item.

Selected: **separate repositories, each its own AW project, federated.** This matches the physical layout spec `20260810-1447-01` section 14: "Cross-repository Git operations cannot be atomic. AW coordinates and reports independent transactions but never claims a global commit." Each repository keeps its own plans, Scope-Paths, lanes, and commits. Federation adds only cross-project reads.

## Required change

### R1. Portable project alias

The project ID (`project_context._derive_project_id`, `project_registry.generate_project_id`) is a slug plus a hash of the local absolute path, so it differs between machines (for example two development machines). A tracked dependency edge cannot use it.

- R1.1 Add an optional, portable `alias` to `.aw/config/project.json` (tracked): lowercase kebab, unique within a federation, for example `acelm`, `acelm-website`, `deck`, `dealer`. Default when absent: the repository directory name, slugified the same way as `_derive_project_id` without the hash.
- R1.2 `aw install` and `aw config` can set it non-interactively (`--alias NAME`); the installer prompts for it only in interactive mode and shows the default.
- R1.3 Record the alias in the AW_HOME registry entry (`ProjectRegistryEntry`) beside `project_id` and `target_paths`.

### R2. Register the project on install

- R2.1 `engine.install_into_repo` (or the CLI install path that calls it) calls `project_registry.register_or_update_project` for every successful install and update, with the resolved `project_id`, `alias`, delivery mode, records backend, and enabled hosts. The call is idempotent.
- R2.2 Registration failure is a warning, never an install failure, and the warning names the remedy (`aw project attach` or the equivalent existing verb).
- R2.3 Add `aw federation list` (or extend an existing read-only verb) that prints every registered project with alias, project ID, target paths, and whether each path exists on this machine.

### R3. Federation membership

- R3.1 A project declares its federation peers in tracked `.aw/config/project.json` as `federation: {"peers": ["acelm", "acelm-website", "deck"]}` (aliases only, no paths). A peer list is per project, so a contractor's `deck` checkout can list `acelm` and omit `dealer`, and the `dealer` project can list everything.
- R3.2 Resolve an alias to a local checkout in this order: machine-local `config/local.json` `federation.paths.<alias>` (absolute path, never tracked); the AW_HOME registry entry with that alias whose target path exists; a sibling directory of the current repository named after the alias that holds `.aw/` with the same alias. Record which source resolved each alias (provenance, as `resolve_project_context` already does for other fields).
- R3.3 A peer that does not resolve is `unavailable`, which is a normal state (the contractor case), not an error.

### R4. Project-qualified Item-Dependencies

- R4.1 Extend the edge grammar with an optional project qualifier: `<alias>/executed:<id6>`, `<alias>/exists:<type>:<id6>`, `<alias>/state:<type>:<status>:<id6>`. An unqualified edge keeps today's meaning (the local project). Update `ipd_schema._parse_item_dependency_edge`, `parse_item_dependencies`, `ItemDependency` (add `project: Optional[str]`), and `canonical()` so the qualifier round-trips and canonical ordering stays deterministic.
- R4.2 Resolution: `check_engine.build_dependency_index` gains a federated variant that builds one index per resolved peer (lazily, only for aliases that appear in edges) by running `status_set.inventory_all_artifacts` against the peer root. `_resolve_edge` returns a new verdict `unavailable` when the alias is not a declared peer or does not resolve on this machine, in addition to `ok`, `dangling`, `ambiguous`.
- R4.3 `aw check`, `aw ipd lint`, and `aw ipd dependencies set` treat `unavailable` as a warning by default and as an error with `--require-peers`. A qualified edge to an alias that is not in `federation.peers` is an error (typo protection).
- R4.4 Runner: `runner_shared._read_item_dependencies`, `dependency_status_detailed`, `edge_satisfied`, and `enforce_dependency_preflight` (and the `agy_runipd` copy) accept qualified edges. A qualified `executed:` edge is satisfied only when the peer's plan file is in the peer's `plans/executed/` directory on disk at the peer's current checkout (the same single on-disk authority the 2026-09-19 maintainer ruling set for local edges, cited in the `edge_satisfied` docstring). An `unavailable` edge blocks the dependent item with reason `peer-unavailable:<alias>`; it never counts as satisfied.
- R4.5 `aw ipd dependencies set` accepts qualified edges and validates them with the federated resolver; `--allow-dangling` also permits `unavailable`.
- R4.6 A peer is read, never written. No federation code path stages, commits, merges, or moves a file in a peer repository.

### R5. Orchestrator child rows across projects

- R5.1 Allow an orchestrator's typed child-tracking row to name a qualified child: `- [ ] E-NN CONFIRM <alias>/<id6> REACHED <status>`, and allow the child table to carry the alias in the Id cell (for example `` `acelm-website/99mu2h` ``). Update lint rule IPD-S408 (`child-unauthored`, `orchestrator-row-nonconforming`) to resolve qualified children through the federated resolver and to report `unavailable` children as info, not as unauthored.
- R5.2 `aw ipd board` and `aw ipd execute-set` show qualified children with their peer status and never try to run them in the current repository.

### R6. Multi-project attention

- R6.1 `aw attention --federation` (and `--projects a,b,c`) scans the current project and every resolved peer, labels each item with its alias, computes dependency depth across projects using R4 edges, and lists unavailable peers in a header line.
- R6.2 JSON output adds `project` to each item and a top-level `peers` list with `{alias, status: resolved|unavailable, root_source}`; never emit absolute paths in tracked or `--public` output.
- R6.3 `--check` fails closed only on the current project's violations unless `--federation --check-peers` is given.

### R7. Run-start report

- R7.1 `aw oc run` and `aw agy run` print, at run start, each qualified dependency of the queued items with its peer status, so an operator sees why an item waits on another repository.

## Acceptance evidence

All evidence must be actual command output from real runs, pasted into the plans that implement this item. Source-text assertions do not count.

1. Scratch federation: create three git repositories `alpha`, `beta`, `gamma` in a temporary directory, install AW in each with aliases, and declare peers. Show `aw federation list` output with all three.
2. Write a plan in `beta` with `Item-Dependencies: alpha/executed:<id6>`. Show `aw ipd lint` and `aw check` outputs: before the alpha plan is executed (edge resolves, not satisfied), after it is finalized in `alpha` (satisfied), with `alpha` moved away (verdict `unavailable`, warning), and with `--require-peers` (error).
3. Show `aw ipd dependencies set` rejecting a qualified edge to an alias that is not a declared peer.
4. Show an orchestrator in `beta` with a `CONFIRM alpha/<id6> REACHED executed` row linting conforming, and IPD-S408 reporting `unavailable` as info when `alpha` is absent.
5. Show `aw attention --federation` text and JSON with items from all three projects, the `project` field, and the `peers` list, with no absolute path in `--public` output.
6. Show `aw oc run <beta-selector>` holding the dependent item with reason `peer-unavailable:alpha` when `alpha` is absent, and releasing it when `alpha`'s plan is executed. Show that no file in `alpha` changed (`git -C alpha status --porcelain` empty, `git -C alpha log` unchanged).
7. Show that a fresh `aw install` writes a registry entry with the alias, and that an install with an unwritable AW_HOME still succeeds with the named warning.
8. Cross-machine check: copy `beta` to a second path (simulating another machine) with no registry entry and a `config/local.json` `federation.paths` binding; show the edge resolves through the local binding and the provenance names that source.
9. Full test suite passes, run bare as `python3 -m pytest`, with the runner output pasted.

## Evidence (code locations, verified 2026-11-01)

- Edge grammar: `agent_workflows/ipd_schema.py` `_parse_item_dependency_edge`, `parse_item_dependencies`.
- Edge resolution: `agent_workflows/check_engine.py` `build_dependency_index`, `_resolve_edge`; `agent_workflows/status_set.py` `resolve_dependency_edge_targets` (docstring: one resolver shared by setter and checker, spec 25kzda section 2.10).
- Runner: `agent_workflows/runner_shared.py` `_read_item_dependencies`, `edge_satisfied` (on-disk authority ruling 2026-09-19), `dependency_status_detailed`, `enforce_dependency_preflight`; `agent_workflows/agy_runipd.py` `enforce_dependency_preflight`.
- Attention: `agent_workflows/attention.py` `scan(repo_root, ...)`, `dependency_depths`.
- Registry: `agent_workflows/project_registry.py` `register_or_update_project`, `find_project`, `get_registry_path` (`AW_HOME/config/registry.json`); callers only in the `cli.py` attach and move handlers.
- Project ID: `agent_workflows/project_context.py` `_derive_project_id` (path hash), project-ID precedence in `resolve_project_context` section 6.
- Layout spec: `.aw/records/specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` section 14 (independent transactions), section 4.1 (`config/local.json` is machine-local and never tracked).
- Rejected submodule default: `.aw/records/specs/superseded/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` section 20.5.
- Open isolation item: `.aw/records/research/20260828-wtiso-00-x03wgn-worktree-isolation-state-model.gpt56.research-report.md` open item 14.

## Scope limits and out of scope

- Out of scope: a single plan whose Scope-Paths span repositories; aliased Scope-Paths; one companion records repository serving several targets; submodule-aware commits and lanes. Each is possible later work and needs its own spec. Federation must not make them harder (keep the alias and resolver reusable).
- No write to any peer repository from any federation code path (R4.6).
- No change to the meaning of unqualified edges, existing plans, or existing lint results for single-project repositories. A repository with no `federation` block behaves exactly as today.
- Security: resolving a peer reads only that peer's `.aw/records/` and `.aw/config/project.json`. Never follow a peer path outside the resolved root; reuse `project_registry._check_registry_path_security` rules.
- Graduation needs a spec (grammar change plus new verdict and new config keys); the maintainer has stated the intent to graduate this item promptly.
