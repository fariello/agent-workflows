- Id: c1f6rd
- Status: open
- Set: awfed
- Priority: high
- Work-Kind: feature
- Summary: Federate AW projects across sibling repositories: project-qualified Item-Dependencies, multi-project attention, and registry registration on install

## Workflow history
- 2026-11-02 note (aw backlog): R4.1 and R4.4 changed to match AceLM PR-06/PR-08 (2026-11-01): qualifier on the target after the condition; qualified edges resolve against the fetched remote default branch
- 2026-11-02 note (aw backlog): D7 prerequisite confirmed by maintainer (for now); D8 amended: first version supports repository-backed peers only, others refused as federation-unsupported-backend, companion support gated on m1wdj8; acceptance step 16 added.
- 2026-11-01 note (aw backlog): Review findings 1-12 resolved as maintainer decisions D1-D12 (Decisions section); R-items amended to cite them; acceptance evidence 10-15 added. Open: D7 AceLM contractor visibility of acelm; D8 companion project.json location.
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

THE DECISIONS SECTION BELOW (D1-D12, maintainer 2026-11-01) IS AUTHORITATIVE. Where an R-item and a decision disagree, the decision wins; the R-items have been amended to point at the decision that refines them. Terminology: the term "alias" in the R-items means the FEDERATION NAME of D11.

### R1. Portable project alias (refined by D4, D11)

The project ID (`project_context._derive_project_id`, `project_registry.generate_project_id`) is a slug plus a hash of the local absolute path, so it differs between machines (for example two development machines). A tracked dependency edge cannot use it.

- R1.1 Add a portable federation name to `.aw/config/project.json` (tracked) as `federation.name` (D11): lowercase kebab, unique within a federation, for example `acelm`, `acelm-website`, `deck`, `dealer`. It is NEVER derived (D4): it is REQUIRED whenever a `federation` block exists, and a repository with no `federation` block has no name and cannot be referenced.
- R1.2 `aw install` and `aw config` can set it non-interactively (`--name NAME`); in interactive mode the installer may SUGGEST the directory name but always writes the value explicitly (D4).
- R1.3 Record the name in the AW_HOME registry entry (`ProjectRegistryEntry`) as `federation_name` beside `project_id` and `target_paths` (D11).

### R2. Register the project on install (refined by D5, D10)

- R2.1 `engine.install_into_repo` (or the CLI install path that calls it) calls `project_registry.register_or_update_project` for every successful install and update, with the resolved `project_id`, `alias`, delivery mode, records backend, and enabled hosts. The call is idempotent.
- R2.2 Registration failure is a warning, never an install failure, and the warning names the remedy (`aw project attach` or the equivalent existing verb).
- R2.3 Add `aw project list` (D10; no new `aw federation` noun) that prints every registered project with federation name, project ID, target paths, and whether each path exists on this machine; `--prune` removes entries whose path is gone (D5). Add `aw project peers` (D10) for this project's declared peers. `aw install --no-register` skips registration for scratch installs (D5).

### R3. Federation membership (refined by D4, D5, D8, D11)

- R3.1 A project declares its federation peers in tracked `.aw/config/project.json` as `federation: {"peers": ["acelm", "acelm-website", "deck"]}` (aliases only, no paths). A peer list is per project, so a contractor's `deck` checkout can list `acelm` and omit `dealer`, and the `dealer` project can list everything.
- R3.2 Resolve an alias to a local checkout in this order: machine-local `config/local.json` `federation.paths.<alias>` (absolute path, never tracked); the AW_HOME registry entry with that alias whose target path exists; a sibling directory of the current repository named after the alias that holds `.aw/` with the same alias. Record which source resolved each alias (provenance, as `resolve_project_context` already does for other fields).
- R3.3 A peer that does not resolve is `unavailable`, which is a normal state (the contractor case), not an error. Several distinct candidates for one name resolve to `ambiguous-peer` (D5). A candidate is accepted only when its own tracked `federation.name` matches (D4), and the records root is obtained through `resolve_project_context` (D8).

### R4. Project-qualified Item-Dependencies (refined by D1, D2, D6, D7, D9)

- R4.1 Extend the edge grammar with an optional project qualifier on the target, after the condition: `executed:<alias>/<id6>`, `exists:<type>:<alias>/<id6>`, `state:<type>:<status>:<alias>/<id6>`. A Set target is `<alias>/set/<setid>`. (Changed 2026-11-01 to match AceLM PR-08 in `acelm/docs/acelm-projects-and-repositories.md`, so that a target reads the same in prose, edges, and child rows.) An unqualified edge keeps today's meaning (the local project). Update `ipd_schema._parse_item_dependency_edge`, `parse_item_dependencies`, `ItemDependency` (add `project: Optional[str]`), and `canonical()` so the qualifier round-trips and canonical ordering stays deterministic. Self-qualification is normalized (D9).
- R4.2 Resolution: `check_engine.build_dependency_index` gains a federated variant that builds one index per resolved peer (lazily, only for aliases that appear in edges) by running `status_set.inventory_all_artifacts` against the peer root. `_resolve_edge` gains the verdicts `undeclared-peer` (the qualifier is not in `federation.peers` or is not a valid name), `unavailable` (a declared peer that does not resolve on this machine), and `ambiguous-peer` (D5), in addition to `ok`, `dangling`, `ambiguous` (D1). The `undeclared-peer` check runs FIRST, from tracked config only, before any resolution (D1).
- R4.3 `aw check`, `aw ipd lint`, and `aw ipd dependencies set` treat `undeclared-peer` as an error ALWAYS (typo protection, identical on every machine and in CI), and `unavailable` as a warning by default and as an error with `--require-peers` (D1).
- R4.4 Runner: `runner_shared._read_item_dependencies`, `dependency_status_detailed`, `edge_satisfied`, and `enforce_dependency_preflight` (and the `agy_runipd` copy) accept qualified edges. A qualified `executed:` edge is satisfied only when the peer's plan file is in `plans/executed/` on the peer's fetched remote default branch (for example `git -C <peer> show origin/main:<path>`), not in the peer's working tree. Unpushed work in a peer checkout does not satisfy the edge, and the number of peer clones has no effect (AceLM PR-06 and PR-08, maintainer decision 2026-11-01). The 2026-09-19 on-disk ruling still governs unqualified, local edges. Reading a fetched ref is a read; R4.6 still forbids any write, and the resolver must not run `git fetch` unless the operator passes `--fetch-peers`. An `unavailable` edge blocks the dependent item with reason `peer-unavailable:<name>`; it never counts as satisfied, except under the recorded run-scoped override of D7.
- R4.5 `aw ipd dependencies set` accepts qualified edges and validates them with the federated resolver; `--allow-dangling` also permits `unavailable` (never `undeclared-peer`). A self-qualified edge is written in its unqualified form (D9).
- R4.6 A peer is read, never written. No federation code path stages, commits, merges, or moves a file in a peer repository.

### R5. Orchestrator child rows across projects (refined by D3)

- R5.1 Allow an orchestrator's typed child-tracking row to name a qualified child: `- [ ] E-NN CONFIRM <alias>/<id6> REACHED <status>` (unchanged: the target form `<alias>/<id6>` already matches R4.1), and allow the child table to carry the alias in the Id cell (for example `` `acelm-website/99mu2h` ``). Update lint rule IPD-S408 (`child-unauthored`, `orchestrator-row-nonconforming`) to resolve qualified children through the federated resolver and to report `unavailable` children as info, not as unauthored.
- R5.2 `aw ipd board` and `aw ipd execute-set` show qualified children with their peer status and never try to run them in the current repository.

### R6. Multi-project attention (refined by D2)

- R6.1 `aw attention --federation` (and `--projects a,b,c`) scans the current project and every resolved peer, labels each item with its federation name, computes dependency depth across projects using R4 edges keyed by `(project, id6)` (D2), and lists unavailable peers in a header line.
- R6.2 JSON output adds `project` to each item and a top-level `peers` list with `{alias, status: resolved|unavailable, root_source}`; never emit absolute paths in tracked or `--public` output.
- R6.3 `--check` fails closed only on the current project's violations unless `--federation --check-peers` is given.

### R7. Run-start report

- R7.1 `aw oc run` and `aw agy run` print, at run start, each qualified dependency of the queued items with its peer status and the ref and commit it was read at (D6), so an operator sees why an item waits on another repository.

## Decisions (maintainer, 2026-11-01)

Adopted from the review of this item. Each states the decision and the reason it beats the alternatives considered, so the spec can carry it without re-deriving it.

### D1. Two verdicts, not one: `undeclared-peer` and `unavailable`

Decision: a qualified edge whose qualifier is not in this project's `federation.peers` (or is not a valid name) is `undeclared-peer`, ALWAYS an error. A declared peer that does not resolve on this machine is `unavailable`: a warning by default, an error under `--require-peers`. The declared-peer check runs first and reads tracked config only.

Why: it removes the R4.2/R4.3 contradiction. The declared check is computable from tracked files, so every machine and CI agree. One combined verdict would make typo severity depend on whether the reader happens to have the peer cloned, so a typo would pass review on any machine that lacks the peer.

### D2. Key by `(project, id6)` wherever more than one project is in view

Decision: a `QualifiedId(project, id6)` key is used by the federated dependency index, `attention.dependency_depths`, and cycle detection. Single-project code paths keep bare id6 keys and are unchanged. Every edge resolves RELATIVE TO THE DECLARING PLAN'S PROJECT: an unqualified edge inside a peer's plan points into that peer, which is what makes cross-repository depth chains correct. Acceptance includes two projects sharing an id6 on purpose and a chain that crosses repositories.

Why: id6s are minted per repository and cannot be made federation-unique (a contractor cannot see Dealer's records to check collisions). Prefixing only in the display still merges nodes in depth and cycle computation. Hashing the name into the id6 breaks every existing reference. The pair key is correct, cheap, and backward-compatible.

### D3. Sets are per repository; qualified orchestrator rows gate retirement

Decision: a Set lives in exactly one repository. A Set id appearing in two repositories names two unrelated Sets; the only cross-repository link is an explicit qualified row (`CONFIRM <name>/<id6> REACHED <status>`, or a qualified Id cell in the child table). The runner retires an orchestrator only when every local child is `executed` AND every qualified row's target is at the required status at the peer's integration ref (D6). Add typed refusal reasons beside the existing `RETIRE_REFUSED_*` (`runner_shared.py`): `peer-children-unfinished` and `peer-unavailable`, each naming the row. For the coverage gate, work a parent assigns to a qualified child in its own child table counts as covered, the same rule as for a local child. For AceLM, `99mu2h` in `acelm-website` keeps `deckdealer` in its filename only as a label; renaming its Set (for example `deckdealer-web`) is optional and recommended for clarity.

Why: not counting remote children would let a parent retire while its remote child is pending, the false completion the coverage gate exists to prevent (2026-09-08). A shared cross-repository Set namespace would make membership depend on which peers a machine can see, so the same orchestrator would retire on one machine and refuse on another, and two teams could merge Sets by picking the same name by accident. Explicit rows are deterministic, reviewable, and reuse the existing retirement machinery.

### D4. The federation name is never derived

Decision: `federation.name` is tracked and REQUIRED whenever a `federation` block exists (enforced by `aw check` and the config schema). Interactive install may suggest the directory name but writes the value explicitly; `--name` sets it non-interactively. A repository without a `federation` block has no name and cannot be referenced. Resolution always verifies that the candidate peer's own tracked `federation.name` matches the requested name.

Why: other repositories cite this name in tracked text, so it is an identity and must be tracked data. A directory-name default breaks on any clone into a different directory. The git remote URL breaks on forks, mirrors, and renamed hosts (contractors often work through mirrors). `project_id` embeds a local path hash (`_derive_project_id`).

### D5. Duplicate registry entries: verify, merge worktrees, then refuse as ambiguous

Decision: (a) drop candidates whose path is gone or whose tracked `federation.name` mismatches; (b) collapse candidates sharing a `common_dir` to their main worktree, which also stops runner lane worktrees (`.aw/worktrees/<id6>`) ever matching as peers; (c) if more than one distinct repository remains, return `ambiguous-peer` listing the candidates, remedied by a `config/local.json` `federation.paths.<name>` pin (already first in R3.2's order). Hygiene: `aw project list --prune` removes dead-path entries, explicitly invoked only (a path on an unmounted drive may be temporarily absent); `aw install --no-register` for scratch installs. Test isolation is already handled by the `AW_HOME` sandbox in `conftest.py`.

Why: "most recently seen wins" silently selects a scratch copy and reports wrong satisfaction with no visible signal. Failing on any duplicate punishes the normal case of several worktrees of one repository. Verify, collapse, then report ambiguity is correct and fails visibly.

### D6. Peer state is read at the peer's integration ref, never its working tree

Decision: read the peer's local `refs/heads/main` by default, overridable by tracked `federation.ref`. Read through git plumbing with no checkout: `git ls-tree -r <ref> -- <records>/plans/` gives bucket directory and id6 from filenames (enough for `executed:` and `exists:`); `git cat-file --batch` gives front-matter `Status:` for `state:` edges. Record the ref name and commit hash in resolution provenance. Static checks and the runner use the same reader. Never fetch: a fetch writes to the peer's `.git` and violates R4.6.

Why: the working tree varies with the checked-out branch and uncommitted moves, so one edge would answer differently with local editing. The remote-tracking ref needs a fetch to mean anything. A stale local `main` can only make an edge look unsatisfied, never falsely satisfied, because `executed` is effectively monotonic, so the error direction is safe. It matches the repository's model: lanes base on main HEAD and "executed" means finalized on main. Cost: a ref-tree reader beside `inventory_all_artifacts`, which is real but contained.

### D7. The contractor case is solved by routing, with a recorded run-scoped override

Decision: (a) routing rule: a plan may depend only on projects its executors can see. The `deck` peer list omits `dealer`, so D1's `undeclared-peer` error already stops a `deck` plan naming a Dealer plan. A cross-team dependency is expressed through a shared record in a repository both sides see, for example an interface spec in `acelm` the Dealer team moves to `implemented`, so the contractor plan depends on `acelm/state:spec:implemented:<id6>`. (b) escape hatch: a run-scoped `--allow-unavailable-peers '<why>'` that REQUIRES a justification and records it in `aw runs`, on the `--allow-uncovered-orchestrator-work` precedent. No persistent waiver field is written into the plan.

Why: a persistent waiver line in the plan is a hand-written attestation a gate would trust, the same forgery risk the `Readiness:` rule exists to stop. An exported status snapshot from `dealer` adds a sync mechanism that drifts and can leak confidential record names. Accepting a permanent block leaves the motivating case unsolved. Depending on a published contract rather than another team's internal plan is also the better engineering practice.

PREREQUISITE CONFIRMED (maintainer 2026-11-01, "for now"): AceLM contractors can see `acelm`, so `acelm` is the shared repository for the routing rule. If that changes, a different shared repository is needed.

### D8. Peer records root comes from `resolve_project_context`

Decision (amended by maintainer 2026-11-01 after verification):

- (a) Peer resolution is two steps: locate the checkout (local binding, registry, sibling directory), then call `resolve_project_context(peer_root)`. Never assume `<peer>/.aw/records`. The federation name is read from wherever the resolver places `config_project`, never from a hard-coded path. A context-resolution failure yields `unavailable` with that reason.
- (b) FIRST VERSION SUPPORTS `records_backend: repository` PEERS ONLY. For any other backend (`companion`, `home`, `repository-untracked`), `aw config`/`aw install` refuse to write a `federation` block and `aw check` reports an existing one as `federation-unsupported-backend:<backend>`; a peer reached with such a backend resolves `unavailable` with that reason. Lifting the restriction for companion-backed projects is gated on backlog `m1wdj8`.

Why (a): delegating to the project's own resolver inherits every placement mode instead of maintaining a second, partial copy of placement logic, so lifting (b) later needs no resolution change.

Why (b), verified 2026-11-01 by a code read and a scratch install with `--preset public-target-private-companion`: (1) `project.json` was written to `<target>/.aw/config/` and left UNTRACKED there, although the preset table and layout spec `20260810-1447-01` declare `config_project` `companion-tracked`, and `project_config_dir` resolves the target location; so a `federation.name` there would reach no other machine, breaking D4. (2) The companion directory was not a git repository, so D6's ref read has nothing to read. (3) No `companion_identity.json` was written. (4) The `home` and `local-only` layouts keep config and records untracked under `AW_HOME` by design, invisible to any other machine. Alternatives rejected: trusting the resolved location as-is works only on the installing machine and fails silently elsewhere, the machine-dependent behavior D1 and D4 exist to prevent; carrying the name in `companion_identity.json` builds on a file install does not write and still leaves no ref to read; fixing companion placement inside this item couples federation to an independent placement decision (filed separately as `m1wdj8`). Refusal is honest, deterministic, and cheap to verify. No impact for AceLM if each repository keeps `.aw/records/` in-repo (not verified here).

### D9. A self-qualified edge is normalized, not refused

Decision: an edge qualified with the declaring project's own name (for example `acelm/executed:x` inside `acelm`) means the unqualified edge. `aw ipd dependencies set` writes the unqualified form; lint WARNS that the spelling is non-canonical and offers the rewrite; it does not refuse.

Why: refusing punishes a harmless edge that arises naturally when edges are copied between repositories. Keeping both spellings gives one edge two canonical forms, which breaks de-duplication, canonical ordering, and cycle detection.

### D10. Verbs live under `aw project`, not a new `aw federation` noun

Decision: `aw project list` (the registry view, with `--prune`) and `aw project peers` (this project's declared peers with resolved/unavailable status, provenance, and ref hash; no absolute paths under `--public`).

Why: `aw project` already owns registry status, attach, and move, and the CLI surface is already large. Splitting the two views keeps distinct questions apart: what this machine has registered versus what this project can see.

### D11. The concept is the "federation name", nested in the `federation` block

Decision: tracked `federation: {"name": "deck", "peers": [...], "ref": "main"}`; machine-local `config/local.json` `federation.paths.<name>`; registry field `federation_name`. The grammar term for the `<name>/` prefix on an edge is "project qualifier".

Why: "alias" is already taken twice in this toolkit: `local_aliases` in `config/local.json` (path aliasing, `project_context.py`) and CLI command aliases. Nesting the name in the block also makes D4 structural, because a `federation` block with no name fails the schema, and keeps all federation config in one place.

### D12. Validation covers both test tiers and both runner hosts

Decision: implementing plans paste output from BOTH the bare `python3 -m pytest` core tier and `make test-all` (the thorough tier). The runner acceptance scenario (evidence step 6) runs on BOTH hosts, because dependency preflight exists twice (`runner_shared.enforce_dependency_preflight` and `agy_runipd.enforce_dependency_preflight`). The spec either collapses the two into one shared implementation or requires a test that drives the same scenario through both and asserts identical outcomes.

Why: a grammar change touches lint, check, the setter, attention, and both runners. The core tier is sized as a fast merge gate, not as coverage for a change across that many surfaces, and two copies of the check that are tested once will drift apart.

## Acceptance evidence

All evidence must be actual command output from real runs, pasted into the plans that implement this item. Source-text assertions do not count.

1. Scratch federation: create three git repositories `alpha`, `beta`, `gamma` in a temporary directory, install AW in each with aliases, and declare peers. Show `aw federation list` output with all three.
2. Write a plan in `beta` with `Item-Dependencies: executed:alpha/<id6>`. Show `aw ipd lint` and `aw check` outputs: before the alpha plan is executed (edge resolves, not satisfied), after it is finalized and pushed in `alpha` to a bare remote and fetched (satisfied), after it is finalized in `alpha` but not pushed (not satisfied), with `alpha` moved away (verdict `unavailable`, warning), and with `--require-peers` (error).
3. Show `aw ipd dependencies set` rejecting a qualified edge to an alias that is not a declared peer.
4. Show an orchestrator in `beta` with a `CONFIRM alpha/<id6> REACHED executed` row linting conforming, and IPD-S408 reporting `unavailable` as info when `alpha` is absent.
5. Show `aw attention --federation` text and JSON with items from all three projects, the `project` field, and the `peers` list, with no absolute path in `--public` output.
6. Show `aw oc run <beta-selector>` holding the dependent item with reason `peer-unavailable:alpha` when `alpha` is absent, and releasing it when `alpha`'s plan is executed. Show that no file in `alpha` changed (`git -C alpha status --porcelain` empty, `git -C alpha log` unchanged).
7. Show that a fresh `aw install` writes a registry entry with the alias, and that an install with an unwritable AW_HOME still succeeds with the named warning.
8. Cross-machine check: copy `beta` to a second path (simulating another machine) with no registry entry and a `config/local.json` `federation.paths` binding; show the edge resolves through the local binding and the provenance names that source.
9. Full test suite passes, run bare as `python3 -m pytest` AND as `make test-all`, with the runner output of both pasted (D12).
10. Id6 collision (D2): `alpha` and `beta` each hold an artifact with the same id6; `aw attention --federation` shows both as distinct items with correct depths, and a dependency chain `gamma -> beta -> alpha` orders correctly.
11. Orchestrator retirement (D3): an orchestrator in `beta` with a qualified row to an `alpha` child is refused retirement with `peer-children-unfinished` while the child is pending and `peer-unavailable` while `alpha` is absent, and retires once the child is executed at `alpha`'s `main`.
12. Ref authority (D6): moving the `alpha` plan into `executed/` in the working tree without committing leaves the edge unsatisfied; committing it on `alpha`'s `main` satisfies it; the provenance shows the ref and commit hash.
13. Verdicts (D1, D5, D9): an undeclared qualifier is an error with `alpha` present and absent alike; two distinct registered `alpha` repositories yield `ambiguous-peer`, and two worktrees of one `alpha` do not; a self-qualified edge is rewritten to its unqualified form with a lint warning.
14. Override (D7): `aw oc run --allow-unavailable-peers '<why>'` releases the held item, and the justification appears in `aw runs`; the same run without a justification is refused.
15. Both hosts (D12): the scenario of step 6 runs through `aw oc run` and `aw agy run` with identical outcomes.
16. Unsupported backend (D8): `aw config`/`aw install` refuse to add a `federation` block in a project installed with `--preset public-target-private-companion` and in one with `--records-backend home`; `aw check` reports a hand-written block there as `federation-unsupported-backend:<backend>`; a qualified edge to such a peer resolves `unavailable` with that reason.

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
