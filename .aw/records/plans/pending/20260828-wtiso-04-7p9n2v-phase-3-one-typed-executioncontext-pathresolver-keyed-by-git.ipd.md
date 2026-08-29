# IPD: Phase 3: one typed ExecutionContext + PathResolver keyed by git-common-dir checkout-id (consolidate project_context/project_registry, role-aware paths, AST guard against raw .aw/state paths)

- Date: 2026-08-28
- Kind: child
- Concern: Under worktree isolation the driver spawns the in-lane agent with cwd inside `.aw/worktrees/<id6>`. Because `aw` resolves its machine-state roots (`.aw/state`, `.aw/records/runs`) relative to cwd/the discovered worktree, an inner `aw` (e.g. `aw ipd begin/finalize`) writes a SECOND receipt/run tree at `.aw/worktrees/<id6>/.aw/state/...` that the driver (running from main) cannot see and that teardown destroys (backlog dh0uno). The research (x03wgn) diagnoses this as a path-authority problem: two path resolvers exist (`project_context.py` logical roots at project_context.py:681, and `project_registry.py` git-common-dir matching at project_registry.py:298), the registry already prioritizes exact common-dir match (project_registry.py:358-364) but the drivers bypass the abstraction and construct control paths directly (agy_runipd.py:1232-1233, oc_runipd.py:1162-1163, ipd_lifecycle.py:86-88 and :244-251), and receipts are physically COPIED into the lane (agy_runipd.py:592, oc_runipd.py:470). This is Phase 3 of the wtiso Set (x03wgn Section 8 "Phase 3").
- Scope: Consolidate `project_context.py` + `project_registry.py` into ONE typed `ExecutionContext` + `PathResolver` with role-aware named accessors (coordinator/worker/verifier); bind a machine-local `checkout_id` to the canonical `git rev-parse --git-common-dir` (never derive a fresh id from a linked-worktree path); implement the resolution order from x03wgn Section 3; pass opaque selectors (AW_CHECKOUT_ID/RUN_ID/LANE_ID, NOT the control-root path) to child processes; add a static/AST guard forbidding NEW direct construction of `.aw/state`/`.aw/records/runs` paths outside the resolver + bounded migration code. Convert the correctness-critical consumers named in x03wgn Section 8 Phase 3 item 4 (shared orchestrator used by `oc_runipd.py`/`agy_runipd.py`, `ipd_lifecycle.py`, run ledger/viewer/recovery). Does NOT relocate state out of repo (that is Phase 4 / wtiso-05).
- Scope-Paths: agent_workflows/execution_context.py, agent_workflows/path_resolver.py, agent_workflows/project_context.py, agent_workflows/project_registry.py, agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, tests/test_execution_context_resolver.py, tests/test_pathresolver_role_guard.py, tests/test_no_raw_state_paths_ast_guard.py, tests/test_checkout_id_common_dir_binding.py
- Item-Dependencies: executed:rchpms
- From-Backlog: dh0uno
- Blocks-Release: next
- Status: reviewed
- Set: wtiso
- Order: 4
- Highest E allocated: 08
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 7p9n2v

## Workflow history
- 2026-08-29 /plan-review (OpenCode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006. Two findings would each have let Phase 3 "succeed" without fixing dh0uno. (1) WRONG FIX TARGET (PR-002): E-05 converted the four control-path CONSTRUCTORS, but `receipt_dir`/`receipt_path_for`/`state_root` all take `repo_root` as a PARAMETER, so the caller decides the tree. The fork actually enters at `ipd_lifecycle._repo_root` (`:237-241`), which delegates to `run_evidence.get_worktree_path` and returns the WORKTREE top-level, called as `_repo_root(Path(args.dir or "."))` from `run_begin` (`:1737`) and `run_finalize` (`:1898`). PROVEN LIVE with two real linked worktrees: `--dir <main>` yields `<main>/.aw/state/ipd-lifecycle/abc123.receipt.json` while `--dir <lane>` yields `<lane>/.aw/state/...` - two distinct control roots, which IS dh0uno. Converting only the four constructors would leave that untouched. E-05 now mandates routing `_repo_root`/`run_begin`/`run_finalize` through the resolver (keeping the product tree lane-local while the CONTROL root collapses to the checkout), and V-06 now requires END-TO-END evidence: run the real `aw ipd begin --dir <lane>` and show the receipt materializing under the MAIN control root with no `<lane>/.aw/state/` created, with the measured pre-fix baseline for comparison. (2) UNPASSABLE GUARD (PR-003): E-07's AST guard as written would fail immediately - a review-time scan found 45 modules under `agent_workflows/` constructing some `.aw` path, 19 touching a CONTROL path, ~14 in executable code, while E-05 converts only 4, and the allow-list was left unspecified. E-07 now carries the measured counts and four scoping requirements (match ONLY `.aw/state`/`.aw/records/runs`; skip docstrings/comments/help text, since many hits are prose; name the allow-list explicitly with a per-entry reason, with the expected ~14-module set enumerated from the measurement; and state that the guard's purpose is anti-regression on NEW forks). V-07 now requires pasting the allow-list verbatim with reasons and the entry count. Also: added the missing `Blocks-Release: next` (PR-001) that made this plan fire the exit-blocking `check.from-backlog-gate-mismatch` against its own `From-Backlog: dh0uno` (repo-wide drift 2 -> 1); removed the self-referential Scope-Paths entry (PR-004), matching every executed plan and the Set's other children, since `aw ipd finalize` owns the plan file and the declared `pending/` path ceases to exist on finalize; corrected the drifted driver citations and the stale layout-spec path, which was copied faithfully from a `project_context.py` docstring that itself predates the layout migration (PR-005, with a citation-basis note; NOTE the `project_registry.py`/`project_context.py`/`ipd_lifecycle.py` citations were ACCURATE, including the exact-common-dir priority branch at `:358-364`); and recorded E-06's transitive env dependency on `qcqhj7` E-04 (creates the child env dict) and `rchpms` E-06 (adds `AW_EXECUTION_ROLE`), so this item extends one dict rather than forking a second (PR-006). VERIFIED SOUND (no finding): the dh0uno diagnosis and the chosen fix key are correct - `get_git_common_dir` already returns a byte-identical value from the main checkout and from a linked worktree (measured), so binding `checkout_id` to it is the right invariant; and the AST-guard precedent at `tests/test_naming_authority_single_source.py:20-46` exists as cited.
- 2026-08-29 reviewed (aw set): status set to reviewed
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Establish exactly ONE typed path authority (`ExecutionContext` + `PathResolver`) keyed by a machine-local `checkout_id` bound to the canonical `git rev-parse --git-common-dir`, so an inner `aw` invoked from ANY cwd (including a linked lane worktree) resolves control state (`.aw/state`, `.aw/records/runs`) to the SINGLE checkout control root, fixing the dh0uno state fork; and add an AST guard that mechanically prevents any new module from re-forking a raw control path outside the resolver.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: typed context + resolver core

- [ ] E-01 Create `agent_workflows/execution_context.py` defining a frozen `ExecutionContext` dataclass with the exact fields from x03wgn Section 3 ("Why the recommendation is one resolver"): `project_id`, `checkout_id`, `run_id`, `lane_id`, `attempt_id`, `role` (enum `coordinator|worker|verifier`), `host_capabilities`. Add a constructor `ExecutionContext.resolve(...)` implementing the 5-step resolution order verbatim from x03wgn Section 3 "Resolution order" (1 in-process context; 2 pinned opaque IDs in child env resolved via local checkout registry; 3 exact canonical git-common-dir registry match; 4 exact canonical main-checkout path for a legacy unattached checkout; 5 origin URL as diagnostic hint only, ambiguity FAILS CLOSED). No filesystem writes.
  - Depends on: none
  - Expected outcome: `python3 -c "from agent_workflows.execution_context import ExecutionContext, Role"` imports; the module exposes `resolve` and a `Role` enum with `coordinator`/`worker`/`verifier`.
  - Execution state: pending

- [ ] E-02 In `execution_context.py`, implement `checkout_id` derivation that binds to the canonical `git rev-parse --git-common-dir` by delegating to the EXISTING `project_registry.get_git_common_dir` (project_registry.py:182) and hashing that common-dir path. Guarantee that when invoked from a LINKED worktree, the id is derived from the common dir (which is shared) and NOT from the linked-worktree path: add an explicit `_forbid_worktree_derived_id` check that asserts the input to the id hash is the common dir, never the passed cwd/worktree path. Never mint a fresh id from a linked-worktree `.git` file path.
  - Depends on: E-01
  - Expected outcome: `checkout_id` for the main worktree and for any linked worktree of the same repo are byte-identical; a helper raises if asked to derive an id from a non-common-dir path.
  - Execution state: pending

- [ ] E-03 Create `agent_workflows/path_resolver.py` defining `PathResolver(ctx: ExecutionContext)` with the role-aware named accessors from the x03wgn Section 3 sketch: `control_run_dir()`, `receipt_path(plan_id)`, `transaction_path()`, `integration_candidate()` (all coordinator-only), `lane_worktree()` (role-aware), `lane_input_dir()` (worker-readable), `lane_submission_dir()` (worker-writable). Coordinator-only accessors called with `role=worker` MUST raise the deterministic error `AW-LIFECYCLE-ROLE-001: runner owns begin/finalize for managed lanes` (x03wgn Section 3). All control paths are computed from the checkout control root keyed by `checkout_id`, NOT from cwd.
  - Depends on: E-01, E-02
  - Expected outcome: `PathResolver` importable; coordinator-role calls return control paths under the checkout control root; worker-role calls to coordinator-only accessors raise `AW-LIFECYCLE-ROLE-001`.
  - Execution state: pending

### Task group 2: route the two existing resolvers + correctness-critical consumers through the one authority

- [ ] E-04 Route `project_context.py` and `project_registry.py` through the consolidated authority: make `ExecutionContext.resolve` the single entry that composes the logical roots (currently project_context.py:681) and the git-common-dir matching (currently project_registry.py:298), so there is ONE path authority and no third resolver. Preserve the public `resolve_project_context`/`find_project` signatures (re-export or thin wrappers) so existing callers keep working; the consolidated code path must be the only place that computes control roots.
  - Depends on: E-03
  - Expected outcome: `resolve_project_context` and `find_project` still import and return equivalent results; `grep` shows control-root computation lives only in the new authority (no duplicated logical-root/common-dir logic remaining as an independent authority).
  - Execution state: pending

- [ ] E-05 Convert the correctness-critical control-path constructors named in x03wgn Section 8 Phase 3 item 4 to call the `PathResolver` instead of building `.aw/state`/`.aw/records/runs` directly: `ipd_lifecycle._runtime_dir`/`receipt_dir`/`receipt_path_for` (`ipd_lifecycle.py:86-88`, `:244-251`), and the driver run-root builders `agy_runipd.state_root` (`agy_runipd.py:1232-1233`) and `oc_runipd.state_root` (`oc_runipd.py:1162-1163`). Each now resolves via `PathResolver(ctx).control_run_dir()`/`receipt_path()` keyed by `checkout_id`, so an inner `aw` from a lane worktree resolves to the main checkout control root. MANDATORY ADDITIONAL TARGET - THE ACTUAL FORK ENTRY POINT (found at review; converting the four constructors ALONE does NOT fix dh0uno): `receipt_dir`/`receipt_path_for`/`state_root` all take `repo_root`/`repo` as a PARAMETER, so their CALLER decides which tree they land in. The fork is introduced by `ipd_lifecycle._repo_root(start)` (`ipd_lifecycle.py:237-241`), which delegates to `run_evidence.get_worktree_path(start)` and therefore returns the WORKTREE top-level, not the shared common dir; `run_begin` (`ipd_lifecycle.py:1737`) and `run_finalize` (`:1898`) both call it as `_repo_root(Path(args.dir or "."))`, i.e. cwd-derived. VERIFIED LIVE at review with two real linked worktrees: `receipt_path_for(_repo_root(main))` -> `<main>/.aw/state/ipd-lifecycle/abc123.receipt.json` while `receipt_path_for(_repo_root(lane))` -> `<lane>/.aw/state/...` - two distinct control roots, which IS dh0uno. Therefore `_repo_root` (or the two `run_begin`/`run_finalize` call sites) MUST also resolve the CONTROL root through `ExecutionContext`/`PathResolver` keyed by `checkout_id`, so `--dir <lane>` still yields the single shared control root. Keep the distinction explicit in code: the PRODUCT tree may legitimately remain the lane worktree (that is where the agent edits files); only the CONTROL root must collapse to the checkout.
  - Depends on: E-04
  - Expected outcome: the four named functions delegate to `PathResolver`; AND `_repo_root`/`run_begin`/`run_finalize` resolve the control root via the resolver, so an inner `aw ipd begin`/`finalize` run with cwd inside a linked worktree (or `--dir <lane>`) writes its receipt to the SAME control root as the main checkout (proved in V-06), while product-tree operations still target the lane.
  - Execution state: pending

- [ ] E-06 Pass opaque selectors, not the control-root path, to child processes: at the point the drivers spawn the in-lane agent, export ONLY `AW_CHECKOUT_ID`, `AW_RUN_ID`, `AW_LANE_ID`, `AW_ATTEMPT_ID`, `AW_EXECUTION_ROLE=worker`, `AW_LANE_ROOT=<absolute lane path>` (x03wgn Section 3 "The coordinator can export selectors"). Do NOT export the control-root path or coordinator capability. Delete the receipt-copy-into-lane behavior's reliance path so a worker never receives a control path: retire `sync_receipt_into_worktree` (agy_runipd.py:592, oc_runipd.py:470) as the mechanism (leave a thin no-op/deprecation shim if a caller remains, but the worker no longer needs a copied receipt because the resolver keys to the shared checkout).
  - Depends on: E-05
  - Expected outcome: the spawned child environment contains the six opaque selectors and NOT the control-root path; `sync_receipt_into_worktree` is no longer the correctness mechanism (grep shows it is deprecated/no-op or removed from the launch path).
  - Cross-plan note (added at review): `run_opencode`'s `popen_kwargs` has NO `env` key in the pre-Phase-1 tree, so the child env dict does not exist yet to add selectors to. It is CREATED by `executed:qcqhj7` (Phase 1, E-04: `os.environ.copy()` + `OPENCODE_CONFIG_CONTENT` passed as `popen_kwargs["env"]`) and gains `AW_EXECUTION_ROLE=worker` in `executed:rchpms` (Phase 2, E-06). This item is transitively downstream of both, so it EXTENDS that one env dict with the remaining opaque selectors (`AW_CHECKOUT_ID`, `AW_RUN_ID`, `AW_LANE_ID`, `AW_ATTEMPT_ID`, `AW_LANE_ROOT`); it must NOT create a second/competing env construction, and `AW_EXECUTION_ROLE` is already present rather than newly added here. Verify the shipped shape from those two children before editing.
  - Execution state: pending

### Task group 3: AST guard + adversarial proofs

- [ ] E-07 Add the static/AST guard as a test module `tests/test_no_raw_state_paths_ast_guard.py` (following the existing AST-guard precedent `tests/test_naming_authority_single_source.py:20-46`, verified present): walk every `agent_workflows/*.py` with `ast`, and FAIL if any module OTHER than the resolver (`path_resolver.py`, `execution_context.py`) or an explicitly allow-listed bounded-migration module constructs a raw `.aw/state` or `.aw/records/runs` path (string literal segments `"state"`/`"runs"` joined to a `.aw` path, or the literals `".aw/state"`/`".aw/records/runs"`). The allow-list is a NAMED constant in the test, not a wildcard.
    MEASURED SCOPE (added at review - the naive form of this guard CANNOT pass, so it must be scoped deliberately): a scan of the current tree at review time found **45** modules under `agent_workflows/` that construct SOME `.aw` path, of which **19** touch a CONTROL path (`.aw/state` or `.aw/records/runs`) and roughly **14** do so in EXECUTABLE code rather than a docstring/comment. E-05 converts only FOUR of them. The guard MUST therefore be scoped so it is both PASSING and MEANINGFUL:
    (a) MATCH ONLY CONTROL PATHS - `.aw/state` and `.aw/records/runs`. Do NOT flag other `.aw` roots (`.aw/system`, `.aw/config`, `.aw/records/plans|specs|backlog|research`), which are legitimate product/record paths outside this phase's authority.
    (b) IGNORE NON-EXECUTABLE TEXT - skip module/function/class docstrings and `#` comments (many of the 19 hits are prose such as `oc_runipd.py:9` and `cli.py:1145`), and skip pure help/description strings; flag only real path CONSTRUCTION (`Path(...) / ".aw" / "state"`, `joinpath(".aw", "state", ...)`, or a `".aw/state..."`/`".aw/records/runs..."` literal used as a path).
    (c) NAME THE ALLOW-LIST EXPLICITLY, with a one-line reason per entry, drawn from the measured set. Expected entries at minimum: `project_context.py` (the consolidated authority's own root computation), `compat_migration.py`, `layout_migration.py`, `layout_inventory.py`, `storage.py`, `install_wizard.py`, `engine.py` (bounded install/migration code that must address the physical tree directly), `artifact_core.py` + `worktree_lease.py` + `check_engine.py` (path CLASSIFICATION constants, not control-root construction), `run_cli.py` + `run_viewer.py` + `completion.py` + `ipd_set_plan.py` (read-only run-tree discovery/back-compat probing), `work_cmd.py` (its own `.aw/state/work` subtree), and `lifecycle_fixtures.py` (test fixture). Any entry the executor does NOT convert MUST appear here with its reason; an unexplained entry is a scope violation.
    (d) The guard's PURPOSE is anti-regression on NEW forks: it must fail for a NEW module or a NEW construction site not on the allow-list, which is exactly what E-08's planted-violation test proves.
  - Depends on: E-06
  - Expected outcome: the guard test PASSES on the clean converted tree with an explicit, reasoned allow-list; running it on today's PRE-conversion tree would flag the unconverted control-path constructors (so the guard is demonstrably not vacuous), and the planted-violation test (E-08) fails it on a new violation.
  - Execution state: pending

- [ ] E-08 Write the three adversarial test modules with exact functions: (a) `tests/test_execution_context_resolver.py::test_two_linked_worktrees_share_control_root_distinct_lanes` — create TWO linked worktrees, assert every control path resolves to the IDENTICAL checkout control root, every lane path DIFFERS, and a worker-role resolver call for a control path RAISES `AW-LIFECYCLE-ROLE-001`; (b) `tests/test_pathresolver_role_guard.py::test_worker_role_refuses_control_path`; (c) `tests/test_checkout_id_common_dir_binding.py::test_checkout_id_not_derived_from_linked_worktree_path` — assert the id from a linked worktree equals the main-checkout id AND that the derivation helper refuses a linked-worktree path input. Also add, to the AST-guard module, `test_guard_fails_on_planted_violation` that copies the tree to a tmp dir, PLANTS a module doing `Path(repo)/".aw"/"state"/"x"`, and asserts the guard reports it (proves the guard actually fires).
  - Depends on: E-07
  - Expected outcome: all four adversarial tests pass (the guard-fails-on-planted-violation test proves the guard is not vacuous).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Two path resolvers exist today: `project_context.py` (logical system/config/state/records roots, `resolve_project_context` at project_context.py:320, root computation at project_context.py:681) and `project_registry.py` (git-common-dir probe `get_git_common_dir` at project_registry.py:182 and `find_project` matching order at project_registry.py:298, with the exact-common-dir branch at :358-364). The registry ALREADY prioritizes exact common-dir match over target-path and origin (project_registry.py:298+), matching x03wgn Section 3's resolution order, but the drivers bypass it (see below).
- Control-path construction is done directly (bypassing the abstraction) in: `ipd_lifecycle._runtime_dir` (`.aw/state/runtime`, ipd_lifecycle.py:86-87), `receipt_dir`/`receipt_path_for` (`.aw/state/ipd-lifecycle/`, ipd_lifecycle.py:244-251), `agy_runipd.state_root` (`.aw/records/runs`, agy_runipd.py:1232-1233), `oc_runipd.state_root` (`.aw/records/runs`, oc_runipd.py:1162-1163).
- Receipts are physically copied into the lane worktree by `sync_receipt_into_worktree` (agy_runipd.py:592; oc_runipd.py:470), which x03wgn Section 7 flags as the "receipt copied into lane -> two authorities diverge" hazard.
- The repo already has an AST/static single-source guard precedent (tests/test_naming_authority_single_source.py:20-46 uses `ast` to forbid duplicated authority across `agent_workflows/*.py`), which this plan's guard follows.
- Lint phases: `aw ipd lint --phase author` checks structure + ids present (confirmed via `aw ipd lint --help`).

## Findings

CITATION BASIS (added at review): every `file:line` reference was RE-VERIFIED against the current working tree on 2026-08-29. `project_registry.py` (`get_git_common_dir:182`, `find_project:298`, the exact-common-dir priority branch `:358-364`), `project_context.py` (`resolve_project_context:320`, state root `:681`), and `ipd_lifecycle.py` (`_runtime_dir:86`, `receipt_dir:244`, `receipt_path_for:249`) were ACCURATE. The DRIVER citations had drifted against the research's pinned snapshot `8d1bcd5` and were corrected (`oc state_root` 1089->1162, `agy state_root` 1169->1232, `sync_receipt_into_worktree` oc 462->470 / agy 580->592). The cited layout spec path was also corrected (it lives under `.aw/records/specs/`, not `.agents/docs/specs/`; the stale path was copied faithfully from the `project_context.py` docstring, which itself predates the layout migration). Anchor on SYMBOL NAMES and re-verify with `grep -n '<symbol>'`.

| # | Finding | Evidence (real file:line / research section) |
|---|---|---|
| F1 | dh0uno is a path-authority fork: inner `aw` resolves control state relative to worktree cwd, writing a second receipt/run tree the driver cannot see and teardown destroys. | backlog dh0uno ROOT CAUSE; x03wgn Section 7 row "Worktree-relative state fork" |
| F2 | The registry already prioritizes exact common-dir matching, but the active drivers/lifecycle bypass the abstraction and construct control paths directly. | x03wgn Section 3 "Never derive a fresh checkout ID..."; real: project_registry.py:358-364 (common-dir first) vs agy_runipd.py:1232-1233 / oc_runipd.py:1162-1163 / ipd_lifecycle.py:86-88,244-251 (direct construction) |
| F3 | The fix is ONE typed `ExecutionContext`/`PathResolver` (consolidate the two existing resolvers, do NOT add a third), with role-aware accessors and the `AW-LIFECYCLE-ROLE-001` refusal for worker-role control paths. | x03wgn Section 3 (the ExecutionContext/PathResolver sketch), Section 8 Phase 3 item 1 |
| F4 | `checkout_id` MUST bind to the canonical `git rev-parse --git-common-dir` and MUST NOT be derived fresh from a linked-worktree path; ambiguity fails closed. | x03wgn Section 1 (checkout-id definition), Section 3 "Resolution order" step 5 + "Never derive a fresh checkout ID from a linked worktree path" |
| F5 | Children must export OPAQUE selectors (AW_CHECKOUT_ID/RUN_ID/LANE_ID/ATTEMPT_ID/ROLE/LANE_ROOT), never the control-root path; and receipt-copy-into-lane must stop being the mechanism. | x03wgn Section 3 "The coordinator can export selectors"; Section 7 "Receipt copied into lane" |
| F6 | A static/AST guard must forbid NEW raw `.aw/state`/`.aw/records/runs` construction outside the resolver + bounded migration code. | x03wgn Section 8 Phase 3 item 5 |

## Proposed changes (ordered, validatable)

1. New `agent_workflows/execution_context.py`: `ExecutionContext` (frozen), `Role` enum, `resolve(...)` with the 5-step order, and common-dir-bound `checkout_id` with `_forbid_worktree_derived_id` (E-01, E-02).
2. New `agent_workflows/path_resolver.py`: `PathResolver` with role-aware accessors and `AW-LIFECYCLE-ROLE-001` refusal (E-03).
3. Consolidate: route `project_context.py`/`project_registry.py` control-root computation through the one authority; keep public signatures (E-04).
4. Convert consumers: `ipd_lifecycle._runtime_dir`/`receipt_dir`/`receipt_path_for`, `agy_runipd.state_root`, `oc_runipd.state_root` to the resolver (E-05).
5. Child launch: export opaque selectors only; retire `sync_receipt_into_worktree` as the mechanism (E-06).
6. AST guard test + four adversarial tests including the planted-violation proof (E-07, E-08).

## Deferred / out of scope (with reason)

- Relocating runtime state OUT of the repo to `$XDG_STATE_HOME` and `aw migrate-runtime-state`: owned by Phase 4 / wtiso-05 (x03wgn Section 8 Phase 4). This plan keeps state where it is but makes resolution single-authority and cwd-independent.
- Removing receipt synchronization entirely and the full teardown-preservation flow: Phase 4 item 5 completes receipt-copy removal; here it is retired as the CORRECTNESS mechanism only.
- Candidate-merge integration + `aw recover` (Phase 5 / wtiso-06) and OS-sandbox hard mode (Phase 6 / wtiso-07).

## Scope check

- Over-scope: none. State relocation, integration, and sandbox are explicitly deferred to later phases.
- Under-scope: none. The dh0uno fix requires all of: one typed authority (E-01..E-04), converting the bypassing consumers (E-05), opaque-selector child launch (E-06), and the AST guard + adversarial proofs (E-07, E-08). Green-path-only tests would be an under-scope finding per the shared contract; the adversarial set (E-08) covers the two-worktree identity/difference proof, the worker-role refusal, the no-linked-worktree-derived-id proof, and the planted-violation guard proof.

## Required tests / validation

- Unit + adversarial: `python3 -m pytest -p no:randomly -q tests/test_execution_context_resolver.py tests/test_pathresolver_role_guard.py tests/test_no_raw_state_paths_ast_guard.py tests/test_checkout_id_common_dir_binding.py` (paste ACTUAL output).
- Full suite regression: `python3 -m pytest -p no:randomly -q` (paste ACTUAL summary line).
- Structure: `aw ipd lint --phase author <this file>` reports conforming (paste line).

## Spec / documentation sync

- N/A for new spec creation in this child. The binding design is research x03wgn (cited per finding). If the layout spec `.aw/records/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` (the docstring at project_context.py:3-4 still cites the pre-migration `.agents/docs/specs/` path; verified at review that the file actually lives under `.aw/records/specs/`) needs a note that control-root computation is now single-authority, that is a doc follow-up owned by Phase 4's relocation work, not this child.

## Open questions

### OQ-01: Should `sync_receipt_into_worktree` be fully removed now or left as a deprecated no-op until Phase 4?

- Blocking: no
- Status: resolved
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Leave it as a deprecated no-op/shim in this child (E-06) so no caller breaks mid-migration; x03wgn Section 8 Phase 4 item 5 explicitly owns final removal of receipt synchronization after all lifecycle consumers use the resolver. The correctness fix here is that the worker resolves to the shared checkout control root regardless, so the copy is no longer load-bearing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -c "from agent_workflows.execution_context import ExecutionContext, Role; print(sorted(f.name for f in __import__('dataclasses').fields(ExecutionContext))); print([r.name for r in Role])"` — Observed stdout MUST list fields including `attempt_id, checkout_id, host_capabilities, lane_id, project_id, role, run_id` and Roles `['coordinator', 'worker', 'verifier']`, exit 0.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_checkout_id_common_dir_binding.py::test_checkout_id_not_derived_from_linked_worktree_path` — Observed stdout MUST show `1 passed` and exit 0; the test asserts the linked-worktree checkout_id EQUALS the main-checkout checkout_id and that `_forbid_worktree_derived_id` raises when given a non-common-dir path.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_pathresolver_role_guard.py::test_worker_role_refuses_control_path` — Observed stdout MUST show `1 passed`, exit 0; the assertion is that a worker-role `control_run_dir()`/`receipt_path()` call raises with the literal string `AW-LIFECYCLE-ROLE-001`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: TWO commands. (1) `python3 -c "import agent_workflows.project_context as c, agent_workflows.project_registry as r; print(hasattr(c,'resolve_project_context'), hasattr(r,'find_project'))"` -> `True True`, exit 0 (public signatures preserved). (2) `rg -n "\.aw['\"].*state|\.aw['\"].*records.*runs|\"state\", \"runtime\"" agent_workflows/project_context.py agent_workflows/project_registry.py` — Observed output MUST show control-root computation is no longer an independent authority in these two files (either routed through the new authority or removed); paste the actual rg output showing the remaining lines are the consolidated call sites only.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `rg -n "PathResolver|control_run_dir|receipt_path" agent_workflows/ipd_lifecycle.py agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py` — Observed output MUST show `ipd_lifecycle` receipt/runtime funcs and both drivers' `state_root` delegate to the resolver; AND `rg -n "\.aw. / .records. / .runs.|\.aw., .state.," agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py agent_workflows/ipd_lifecycle.py` shows no NEW raw construction in these functions. Paste actual rg output for both.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_execution_context_resolver.py::test_two_linked_worktrees_share_control_root_distinct_lanes` — Observed stdout MUST show `1 passed`, exit 0. The test creates two linked worktrees (`git worktree add`), constructs a coordinator `PathResolver` from each cwd, asserts `control_run_dir()`/`receipt_path()` are byte-identical across both AND equal the main checkout's, asserts `lane_worktree()` DIFFERS per lane, and asserts a worker-role control-path call raises `AW-LIFECYCLE-ROLE-001`. END-TO-END dh0uno CLOSURE (added at review; a resolver-only assertion is NOT sufficient because the fork enters via `_repo_root`, not via the resolver): the test MUST ALSO exercise the REAL entry point that forked - run `aw ipd begin <plan> --actor x --dir <lane-worktree>` (or call `ipd_lifecycle.run_begin` with `args.dir` pointed at the linked worktree) and assert the receipt file materializes under the MAIN checkout control root and that NO `<lane>/.aw/state/ipd-lifecycle/` directory is created. Paste the resolved receipt path from both the main-cwd and lane-cwd invocations showing they are the SAME absolute path. BASELINE FOR COMPARISON (measured at review on today's code, so the executor can show the delta): today `--dir <lane>` yields `<lane>/.aw/state/ipd-lifecycle/<id6>.receipt.json` while `--dir <main>` yields `<main>/.aw/state/...` - two distinct roots. Also paste `rg -n "AW_CHECKOUT_ID|AW_RUN_ID|AW_LANE_ID|AW_ATTEMPT_ID|AW_EXECUTION_ROLE|AW_LANE_ROOT" agent_workflows/agy_runipd.py agent_workflows/oc_runipd.py` showing the six opaque selectors are exported and NO control-root-path export exists at the launch site.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_no_raw_state_paths_ast_guard.py::test_clean_tree_has_no_raw_state_paths` — Observed stdout MUST show `1 passed`, exit 0 (the guard PASSES on the clean converted tree). ALSO paste the guard's ALLOW-LIST constant verbatim with its per-entry reasons, and state the count of allow-listed modules. Measured baseline at review for comparison: 45 modules construct some `.aw` path, 19 touch a control path, ~14 do so in executable code, and E-05 converts 4 - so an allow-list far smaller than ~10 entries means either more conversion happened (state it) or the matcher is too narrow (a finding). An allow-list containing a module with NO stated reason does not satisfy this V-item.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_no_raw_state_paths_ast_guard.py::test_guard_fails_on_planted_violation tests/test_execution_context_resolver.py tests/test_pathresolver_role_guard.py tests/test_checkout_id_common_dir_binding.py` — Observed stdout MUST show all adversarial tests `passed`, exit 0. The `test_guard_fails_on_planted_violation` case MUST demonstrate the guard reporting a PLANTED `.aw/state` construction (the test asserts the guard's finding list is non-empty for the planted module), proving the guard is not vacuous. Paste the actual output showing BOTH the clean-tree pass (V-07) and the planted-violation-detected pass so both sides of the guard are shown.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one indivisible path-authority consolidation. Splitting the typed context (E-01/E-02), the resolver (E-03), the consolidation of the two existing resolvers (E-04), the consumer conversion (E-05/E-06), and the AST guard + adversarial proofs (E-07/E-08) into separate plans would leave a half-migrated tree where two authorities briefly coexist — exactly the dh0uno fork this fixes. They must land as one atomic change so the "one path authority" invariant holds at the commit boundary and the AST guard can pass.

The shared anti-greenwash execution contract (inherited verbatim from the wtiso orchestrator bl9q3d; this child copies it and does not weaken it):

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.
