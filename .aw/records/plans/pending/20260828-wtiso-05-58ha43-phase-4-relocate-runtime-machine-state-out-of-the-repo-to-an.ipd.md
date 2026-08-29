# IPD: Phase 4: relocate runtime machine-state out of the repo to an XDG state dir keyed by checkout-id (aw migrate-runtime-state, fail-closed dual-root, remove receipt copies)

- Date: 2026-08-28
- Kind: child
- Concern: The runner still writes per-machine CONTROL state (receipts, run dirs, transaction journals, locks) INSIDE the repository working tree, cwd/worktree-relative. Concretely: `oc_runipd.state_root(repo)` returns `repo/.aw/records/runs` (oc_runipd.py:1089-1090) and `run_dir = state_root(repo)/run_id` (oc_runipd.py:1143, agy_runipd.py:1191/:1247); `ipd_lifecycle.receipt_dir` returns `<repo>/.aw/state/ipd-lifecycle/` (ipd_lifecycle.py:45,244-251) and the finalize journal/lock live under `<repo>/.aw/state/runtime/` (ipd_lifecycle.py:86-92). These roots are gitignored (`.gitignore:60 .aw/state/`, `:73 .aw/worktrees/`; `.aw/records/runs/` is ignored via engine.py:5124-5125), so a linked worktree checks them out EMPTY. That is the root of backlog dh0uno: an inner `aw` in a lane resolves state relative to the WORKTREE, forking a second receipt/run tree the driver cannot see, and teardown destroys it. The current mitigation is to COPY the begin receipt into each lane (`sync_receipt_into_worktree`, oc_runipd.py:462-476 called at :2098; agy_runipd.py:580-... called at :2187), which x03wgn Section 9 finding 2 names as forked authority. Phase 3 (7p9n2v) introduces the typed ExecutionContext/PathResolver keyed by the git-common-dir checkout-id; this Phase 4 relocates the machine state itself OUT of the repo to an AW-owned XDG state dir keyed by that checkout-id, adds a journaled `aw migrate-runtime-state --apply`, makes dual-live-roots FAIL CLOSED (never a heuristic merge), and REMOVES the receipt-copy path now that consumers resolve via the resolver. Research x03wgn Section 2 ("relocate machine state"), Section 3 ("Recommendation and runner-up"; "What current code implies"), and Section 8 "Phase 4" prescribe this; R6 (XDG Base Directory Specification) is the storage contract.
- Scope: Add a platform state-dir helper that stores AW runtime state under `$XDG_STATE_HOME/agent-workflows/checkouts/<checkout-id>/` (fallback `~/.local/state/agent-workflows/...`; platform-native application-state dir on macOS/Windows behind the same helper); route the resolver's control roots (receipts, run dirs, transaction journals, locks) at that out-of-repo location keyed by the Phase-3 checkout-id; implement `aw migrate-runtime-state [--apply]` with an exclusive migration lock, dry-run inventory, journal, per-file checksums, and rollback (REUSING `layout_migration.MigrationManager`, no new engine); make it FAIL CLOSED when BOTH the legacy in-repo root and the new out-of-repo root hold live state (never heuristically merge); implement ONE bounded compatibility window (readers use legacy state ONLY when the new root is empty; ALL writes go to the new root; no dual-write); REMOVE `sync_receipt_into_worktree` and its call sites in both drivers now that finalize resolves the receipt via the resolver. Does NOT re-author the resolver (Phase 3 owns it; this child DEPENDS on it), does NOT add candidate-merge integration/recovery (Phase 5), does NOT add the OS sandbox (Phase 6).
- Scope-Paths: agent_workflows/platform_state.py, agent_workflows/migrate_runtime_state.py, agent_workflows/ipd_lifecycle.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/cli.py, tests/test_platform_state.py, tests/test_migrate_runtime_state.py, tests/test_receipt_copy_removed.py
- Item-Dependencies: executed:7p9n2v
- From-Backlog: dh0uno
- Status: to-review
- Set: wtiso
- Order: 5
- Highest E allocated: 09
- Author: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Id: 58ha43

## Workflow history
- 2026-08-29 to-review (aw set): status set to to-review

- 2026-08-28 draft (opencode its_direct/pt3-claude-opus-4.8-1m-us): created.

## Goal

Relocate AW runtime CONTROL state (receipts, run dirs, transaction journals, locks) OUT of the gitignored in-repo `.aw/state` / `.aw/records/runs` roots to an AW-owned XDG state dir `$XDG_STATE_HOME/agent-workflows/checkouts/<checkout-id>/` keyed by the Phase-3 checkout-id, delivered by a journaled `aw migrate-runtime-state --apply` (exclusive lock, dry-run inventory, per-file checksums, rollback) that FAILS CLOSED when both legacy and new roots hold live state, honoring one bounded read-legacy-only-when-new-empty compatibility window with NO dual-write, and REMOVING the receipt-copy-into-lane code now that consumers resolve the receipt through the typed resolver. This closes backlog dh0uno: an inner `aw` in a worktree writes to the single out-of-repo location and never forks a second in-worktree state tree. Acceptance is pasted command output plus observed filesystem/git state (a `find`/`ls` proving the worktree holds NO `.aw/state` fork; a `grep` proving the copy path is gone), never an agent's prose claim.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: platform state helper (x03wgn Section 2 relocation, Section 3 "Recommendation and runner-up", R6)

- [ ] E-01 Add `agent_workflows/platform_state.py` with a pure function `state_home() -> Path` that returns `$XDG_STATE_HOME/agent-workflows` when `XDG_STATE_HOME` is a set, non-empty, absolute path, else `~/.local/state/agent-workflows` on Linux, and the platform-native application-state directory on macOS (`~/Library/Application Support/agent-workflows`) and Windows (`%LOCALAPPDATA%\agent-workflows`) selected by `sys.platform`; per R6 an empty/relative `XDG_STATE_HOME` MUST be treated as unset (fall back), never joined.
  - Depends on: none
  - Expected outcome: `state_home()` is a pure function of env + `sys.platform`; with `XDG_STATE_HOME=/x/state` it returns `/x/state/agent-workflows`; with `XDG_STATE_HOME` empty or `"relative/rel"` it returns the `~/.local/state/agent-workflows` fallback (Linux); it writes nothing when called.
  - Execution state: pending

- [ ] E-02 Add `checkout_state_root(checkout_id: str) -> Path` to `platform_state.py` returning `state_home() / "checkouts" / <checkout-id>`; the `<checkout-id>` argument is the Phase-3 (7p9n2v) machine-local identity bound to the canonical git-common-dir (never derived here from a worktree path). Reject an empty/`..`/separator-bearing `checkout_id` (fail closed) so a caller cannot escape the `checkouts/` namespace.
  - Depends on: E-01
  - Expected outcome: `checkout_state_root("abc123")` equals `state_home()/checkouts/abc123`; `checkout_state_root("")`, `checkout_state_root("..")`, and `checkout_state_root("a/b")` each raise `ValueError` and create no directory.
  - Execution state: pending

### Task group 2: route control roots at the out-of-repo location via the Phase-3 resolver (x03wgn Section 3 "What current code implies", Section 8 Phase 4 item 1)

- [ ] E-03 Route `ipd_lifecycle.receipt_dir` and the finalize journal/lock (`_runtime_dir`, ipd_lifecycle.py:86-92,244-251) through the Phase-3 resolver so the receipt/journal/lock paths resolve to `checkout_state_root(<checkout-id>)/ipd-lifecycle/` and `.../runtime/` (out of the repo), NOT `<repo>/.aw/state/...`. Keep the public function signatures stable; change only the resolved root. Do NOT introduce a second resolver (Phase 3 owns the one resolver; the AST guard added in 7p9n2v forbids new raw `.aw/state` construction).
  - Depends on: E-02
  - Expected outcome: for a repo whose checkout-id is `K`, `ipd_lifecycle.receipt_path_for(repo, "id6")` resolves under `platform_state.checkout_state_root("K")/ipd-lifecycle/id6.receipt.json` (asserted `.is_relative_to(checkout_state_root("K"))`), and no longer under `repo/.aw/state`.
  - Execution state: pending

- [ ] E-04 Route the driver run root (`oc_runipd.state_root`, oc_runipd.py:1089-1090; `agy_runipd.state_root`, agy_runipd.py:1169) through the Phase-3 resolver so `run_dir` (oc_runipd.py:1143, agy_runipd.py:1191/:1247) resolves under `checkout_state_root(<checkout-id>)/runs/<run-id>` out of the repo, symmetrically in both drivers.
  - Depends on: E-03
  - Expected outcome: `oc_runipd.state_root(repo)` and `agy_runipd.state_root(repo)` for checkout-id `K` both return a path equal to `platform_state.checkout_state_root("K")/runs` (asserted equal in a unit test), not `repo/.aw/records/runs`.
  - Execution state: pending

### Task group 3: journaled migration with exclusive lock, dry-run, checksums, rollback, fail-closed dual-root (x03wgn Section 8 Phase 4 items 2-3, Section 2 "runtime layout migration journal" retention class)

- [ ] E-05 Add `agent_workflows/migrate_runtime_state.py` implementing a migration that REUSES `layout_migration.MigrationManager` (its exclusive `_acquire_lock`/`lock_file`, journaled move-not-copy `execute_migration`, and `rollback_migration`; layout_migration.py:264,647-679,709) to move the legacy in-repo control roots (`<repo>/.aw/state/ipd-lifecycle`, `<repo>/.aw/state/runtime`, `<repo>/.aw/records/runs`) into `checkout_state_root(<checkout-id>)`, recording per-file sha256 checksums in the journal and a rollback/recovery instruction. Do NOT fork a new migration engine (compat_migration.py:33-35 documents MigrationManager as the canonical journaled engine).
  - Depends on: E-04
  - Expected outcome: `migrate_runtime_state.plan(repo)` builds a move plan whose every entry has a `source`, `dest` under `checkout_state_root`, and a non-empty `sha256`; applying it holds the exclusive migration lock (a second concurrent apply raises the lock error) and, on a mid-move injected fault, `rollback` restores the legacy files byte-identical (checksums match).
  - Execution state: pending

- [ ] E-06 Make the migration FAIL CLOSED when BOTH the legacy in-repo root AND the new out-of-repo root contain live state: `migrate_runtime_state.assess(repo)` classifies (legacy-only -> migrate; new-only -> already-migrated no-op; neither -> nothing-to-do; BOTH-live -> `DUAL_ROOT_CONFLICT` requiring explicit human reconciliation) and `--apply` REFUSES on `DUAL_ROOT_CONFLICT` with a precise message, moving/merging NOTHING. Never heuristically merge directories (x03wgn Section 8 Phase 4 item 3).
  - Depends on: E-05
  - Expected outcome: with a non-empty legacy `.aw/state/ipd-lifecycle` AND a non-empty `checkout_state_root(K)/ipd-lifecycle`, `assess(repo).status == "DUAL_ROOT_CONFLICT"` and `apply(repo)` raises/exits non-zero naming both roots, leaving BOTH untouched (byte-identical before/after); no merge occurs.
  - Execution state: pending

- [ ] E-07 Implement the ONE bounded compatibility window: a resolver read helper reads legacy in-repo state ONLY when the new out-of-repo root is empty; once the new root is non-empty, reads and ALL writes target the new root exclusively (no dual-write). Add `readable_root(repo) -> Path` used by the read paths so the rule is a single pure predicate, not scattered conditionals.
  - Depends on: E-06
  - Expected outcome: `readable_root(repo)` returns the legacy in-repo root iff the new root is empty, else the new root; a write always targets the new root; a unit test asserts that after a write the legacy root is never subsequently written (its mtime/contents are unchanged across a second write) - proving no dual-write.
  - Execution state: pending

- [ ] E-08 Register `aw migrate-runtime-state [--apply]` as a top-level subcommand in `cli.py` (the top-level `add_subparsers` at cli.py:609): default is a dry-run that prints the inventory (sources, dests, checksums, classification) and exits 0; `--apply` performs the journaled move (or refuses on `DUAL_ROOT_CONFLICT`). Wire it to `migrate_runtime_state`.
  - Depends on: E-07
  - Expected outcome: `python3 -m agent_workflows migrate-runtime-state` prints a dry-run inventory and makes NO filesystem change (a `--apply`-free run leaves both roots unchanged); `... migrate-runtime-state --apply` on a legacy-only repo performs the move and exits 0.
  - Execution state: pending

### Task group 4: remove receipt copying now that consumers use the resolver (x03wgn Section 8 Phase 4 item 5, Section 9 finding 2, depends on Phase 3)

- [ ] E-09 REMOVE `sync_receipt_into_worktree` (oc_runipd.py:462-476; agy_runipd.py:580-...) AND its call sites (oc_runipd.py:2098; agy_runipd.py:2187), so no begin receipt is copied into any lane worktree. In-worktree finalize now finds the receipt through the Phase-3 resolver at the single out-of-repo `checkout_state_root(<checkout-id>)/ipd-lifecycle/` location (identical for the main checkout and every linked worktree of the same checkout-id). Update the driverfin-02 comment blocks (oc_runipd.py:435-437,2093; agy_runipd.py:555,2184) that describe the copy.
  - Depends on: E-04
  - Expected outcome: `grep -rn "sync_receipt_into_worktree" agent_workflows/` returns NO matches (definition and both call sites gone); an isolated in-worktree finalize still locates the receipt (resolver-based) with no copy performed.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The two host drivers are deliberate near-parity twins (`oc_runipd.py`, `agy_runipd.py`): both define `state_root(repo) -> repo/.aw/records/runs` (oc_runipd.py:1089-1090, agy_runipd.py:1169), both define `sync_receipt_into_worktree` (oc_runipd.py:462, agy_runipd.py:580) called at the finalize block (oc_runipd.py:2098, agy_runipd.py:2187). Any Phase-4 change MUST land in both to avoid drift.
- The receipt is a LOCAL gitignored file: `ipd_lifecycle.receipt_dir(repo) = <repo>/.aw/state/ipd-lifecycle/` and `receipt_path_for(repo, id6) = .../ <id6>.receipt.json` (ipd_lifecycle.py:45,244-251). The finalize transaction journal + writer lock live under `<repo>/.aw/state/runtime/` (`_runtime_dir`, ipd_lifecycle.py:86-92; `finalize_lock_path`/`finalize_journal_path`, ipd_lifecycle.py:90-95). These are the control roots this phase relocates.
- These roots are gitignored, which is WHY a worktree checks them out empty and an in-worktree `aw` forks a second tree: `.gitignore:60` ignores `.aw/state/`, `.gitignore:73` ignores `.aw/worktrees/`, and `.aw/records/runs/` is ignored (engine.py:5124-5125 ensures the `records/runs/` line). `check_engine.py:1004-1007` treats `.aw/state/` and `.aw/worktrees/` as gitignored runtime scratch.
- The canonical journaled migration engine is `layout_migration.MigrationManager` (layout_migration.py:264; exclusive `_acquire_lock` + `lock_file` at :647-679; journaled move-not-copy `execute_migration` at :709; `rollback_migration`). `compat_migration.py:33-35` documents that this engine is REUSED, never forked. `ipd_lifecycle.py:48-73` is the repo's canonical crash-safe lock+journal pattern (phased journal, idempotent resume/rollback) to mirror.
- The worker-forbidden path predicate already exists: `worktree_lease.path_is_worker_forbidden` + `FORBIDDEN_WORKER_PATH_HINTS` (worktree_lease.py:199-211, which already lists `.aw/records/runs/`). Reuse it rather than duplicating rules (anti-greenwash contract point 4).
- Top-level `aw` subcommands are registered in `cli.py` via `parser.add_subparsers(dest="command", ...)` at cli.py:609; new commands are added there.
- The checkout-id identity comes from Phase 3 (7p9n2v): the typed ExecutionContext/PathResolver bound to the canonical git-common-dir (`git rev-parse --git-common-dir`, per x03wgn R7 / project_registry.py). This child DEPENDS on that resolver existing (Item-Dependencies: executed:7p9n2v) and must not re-derive identity from a worktree path.
- Tests are `unittest`-style under `tests/`, launching drivers as `python3 -m agent_workflows.oc_runipd` with `PYTHONPATH` pinned to `REPO_ROOT`. New tests follow that convention.

## Findings

| # | Finding | Evidence (x03wgn section + real file:line + spec) |
|---|---|---|
| F1 | Control state lives IN the repo working tree (gitignored), so linked worktrees check it out empty and an inner `aw` forks a second tree (backlog dh0uno). | x03wgn Section 3 "What current code implies" ("`oc_runipd.py`/`agy_runipd.py` still construct the run root relative to the repository...`ipd_lifecycle.py` still anchors receipts and journals under worktree-relative `.aw/state`"); oc_runipd.py:1089-1090/:1143, agy_runipd.py:1169/:1191, ipd_lifecycle.py:45,86-92,244-251; `.gitignore:60`/`:73`, engine.py:5124-5125. |
| F2 | The prescribed fix separates IDENTITY (git-common-dir checkout-id) from STORAGE (AW-owned XDG state dir), storing under `checkouts/<checkout-id>/`. | x03wgn Section 3 "Recommendation and runner-up" ("use Git's common directory to recognize a checkout, but put AW-owned runtime state in an AW-owned platform directory. On Linux use `$XDG_STATE_HOME/agent-workflows`, with `~/.local/state/agent-workflows` fallback ... platform-native ... on macOS and Windows"); x03wgn Section 8 Phase 4 item 1 ("store under `checkouts/<checkout-id>/`"). |
| F3 | The XDG spec (R6) defines `$XDG_STATE_HOME` for persistent, non-portable application state with `~/.local/state` fallback, and empty/relative values are treated as unset. | x03wgn R6 reference (freedesktop.org XDG Base Directory Specification: "Defines `$XDG_STATE_HOME` and the `~/.local/state` fallback for persistent, non-portable application state"); x03wgn Section 3 uses R6 as the storage contract. |
| F4 | The relocation must be a journaled, locked, checksummed, rollbackable migration - not a directory copy - and dual-live-roots must FAIL CLOSED (never heuristic merge). | x03wgn Section 8 Phase 4 items 2-3 ("`aw migrate-runtime-state --apply` with an exclusive migration lock, dry-run inventory, journal, checksums, and rollback/recovery"; "If both legacy and new roots contain live state, fail closed for explicit reconciliation. Never merge directories heuristically"); Section 2 "Runtime layout migration journal" retention class ("State relocation is an owned machine transaction, not a directory copy performed independently by lanes"); reuse target layout_migration.py:264,647-709. |
| F5 | Exactly one bounded compatibility window: read legacy only when the new root is empty; all writes to the new root; NO dual-write. | x03wgn Section 8 Phase 4 item 4 ("During one bounded compatibility window, readers may use legacy state only when the new root is empty. All new writes go to the new root. Do not dual-write"). |
| F6 | Receipt copying into lanes is forked authority and must be REMOVED once consumers resolve via the resolver (depends on Phase 3). | x03wgn Section 8 Phase 4 item 5 ("Remove receipt synchronization/copying after lifecycle consumers all use the resolver"); Section 9 finding 2 ("Both inspected host drivers synchronize the main receipt into the worktree before finalization"); oc_runipd.py:462-476/:2098, agy_runipd.py:580-.../:2187. |
| F7 | Both host drivers must change symmetrically (twin parity). | x03wgn Section 8 Phase 4 (runner-wide); oc_runipd.py + agy_runipd.py parity of `state_root`/`sync_receipt_into_worktree`; backlog dh0uno spans both drivers. |

## Proposed changes (ordered, validatable)

1. E-01/E-02: `platform_state.py` - `state_home()` (XDG + fallback + platform-native, empty/relative treated as unset) and `checkout_state_root(<checkout-id>)` (`checkouts/<checkout-id>/`, escape-rejecting).
2. E-03/E-04: route receipt/journal/lock (`ipd_lifecycle`) and run dirs (both drivers' `state_root`) at `checkout_state_root(<checkout-id>)` through the Phase-3 resolver.
3. E-05: journaled `migrate_runtime_state` REUSING `layout_migration.MigrationManager` (lock + move-not-copy + checksums + rollback).
4. E-06: fail-closed `DUAL_ROOT_CONFLICT` classification (never heuristic merge).
5. E-07: one bounded read-legacy-only-when-new-empty window via a single `readable_root` predicate; no dual-write.
6. E-08: `aw migrate-runtime-state [--apply]` top-level subcommand (dry-run default).
7. E-09: remove `sync_receipt_into_worktree` + both call sites; finalize resolves the receipt via the resolver.

## Deferred / out of scope (with reason)

- Authoring the typed ExecutionContext/PathResolver + checkout-id derivation + AST guard: owned by Phase 3 (7p9n2v); this child DEPENDS on it (Item-Dependencies: executed:7p9n2v) and only routes control roots through it.
- Real candidate-merge integration, full crash recovery, `aw recover`/`aw doctor`, cross-platform lock abstraction: Phase 5 (2c122z).
- OS-sandbox hard mode / read-only git-common-dir: Phase 6 (1o4eif).
- Retaining a narrowly named ignored lane-EXCHANGE directory (x03wgn Section 8 Phase 4 item 6): a lane mailbox is Phase 2's surface; this child only removes the CONTROL-state copy, it does not add or remove the lane-exchange directory.
- Retention/harvest of local-retained artifacts: Phase 2's five-way classifier, not here.

## Scope check

- Over-scope: none. Every E-item is an x03wgn Section 8 Phase 4 item (helper, route control roots, journaled migration with lock/dry-run/checksums/rollback, fail-closed dual-root, one bounded window no-dual-write, remove receipt copy). No Phase 3 resolver authoring, no Phase 5 integration/recovery, no Phase 6 sandbox.
- Under-scope: none. All three mandatory adversarial guards are covered: (a) post-migration inner-aw-in-worktree writes to the out-of-repo location with NO `.aw/state` fork in the worktree (V-04 + V-09 `find`/`ls` absence assertion); (b) both-roots-live FAILS CLOSED not a silent merge (V-06); (c) receipt copy path is gone (V-09 `grep` proof). Both drivers are changed (E-04/E-09).

## Required tests / validation

- New adversarial tests (named exactly):
  - `tests/test_migrate_runtime_state.py::test_both_roots_live_fails_closed_no_merge` - ADVERSARIAL guard (b): dual live roots -> `DUAL_ROOT_CONFLICT`, apply refuses, neither root mutated.
  - `tests/test_migrate_runtime_state.py::test_inner_aw_in_worktree_writes_out_of_repo_no_state_fork` - ADVERSARIAL guard (a): after migration, an inner `aw` invoked with cwd inside a linked worktree writes state under `checkout_state_root(<checkout-id>)`, and a `find`/`ls` of the worktree shows NO `.aw/state` (and no `.aw/records/runs`) fork.
  - `tests/test_migrate_runtime_state.py::test_rollback_restores_legacy_byte_identical` and `::test_no_dual_write_after_new_root_populated`.
  - `tests/test_receipt_copy_removed.py::test_sync_receipt_into_worktree_is_gone` - ADVERSARIAL guard (c): `grep`/AST assertion that `sync_receipt_into_worktree` has no definition and no call site in `agent_workflows/`.
  - `tests/test_platform_state.py::test_state_home_xdg_and_fallback` and `::test_checkout_state_root_rejects_escape`.
- Full-suite regression: `python3 -m pytest -p no:randomly -q` must stay green. Paste ACTUAL output.

## Spec / documentation sync

- N/A for a tracked spec file in this phase (the storage contract is R6/XDG, external, and the behavior is captured by the new tests + backlog dh0uno). The `.gitignore` may keep ignoring `.aw/state`/`.aw/records/runs` for the compatibility window; no `.gitignore` edit is required because the new root is outside the repo entirely. If a `runtime-state-location` doc is later warranted it is deferred to Phase 5 with reason: the location stabilizes only after recovery/`aw doctor` (Phase 5) can reconcile it.

## Open questions

### OQ-01: On macOS/Windows, should the checkout state root use the platform-native application-state dir unconditionally, or honor an explicitly set `XDG_STATE_HOME` even there?

- Blocking: no
- Status: open
- Owner: opencode its_direct/pt3-claude-opus-4.8-1m-us
- Resolution or deferral rationale: Non-blocking. x03wgn Section 3 says "Use platform-native application-state directories on macOS and Windows behind the same helper", so the default is platform-native; honoring an explicitly set `XDG_STATE_HOME` on those platforms is a compatibility nicety that does not change the Linux acceptance tests (E-01/V-01 pin Linux + fallback behavior). The helper's contract is validated on the CI platform (Linux); the macOS/Windows branch is selected by `sys.platform` and can be unit-tested by monkeypatching `sys.platform` without changing the default decision.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_platform_state.py::test_state_home_xdg_and_fallback` exits 0 showing `1 passed`. The test asserts (Linux) `state_home()` with `XDG_STATE_HOME=/x/state` equals `Path("/x/state/agent-workflows")`, and with `XDG_STATE_HOME=""` or `XDG_STATE_HOME="relative/rel"` equals `Path.home()/".local/state/agent-workflows"`, and that calling `state_home()` created no directory (a tmp HOME shows no new dirs).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_platform_state.py::test_checkout_state_root_rejects_escape` exits 0 showing `1 passed`. The test asserts `checkout_state_root("abc123") == state_home()/"checkouts"/"abc123"` and that `checkout_state_root("")`, `checkout_state_root("..")`, `checkout_state_root("a/b")` each raise `ValueError` and create no directory (tmp HOME unchanged).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_platform_state.py -k receipt_resolves_out_of_repo` exits 0 showing `passed`. For a repo with checkout-id `K`, the test asserts `ipd_lifecycle.receipt_path_for(repo, "abc123").resolve().is_relative_to(platform_state.checkout_state_root("K"))` is True AND `not str(ipd_lifecycle.receipt_path_for(repo, "abc123")).startswith(str(repo / ".aw" / "state"))`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_migrate_runtime_state.py -k run_root_out_of_repo` exits 0 showing `passed`. The test asserts `oc_runipd.state_root(repo) == platform_state.checkout_state_root("K")/"runs"` AND `agy_runipd.state_root(repo) == platform_state.checkout_state_root("K")/"runs"` for checkout-id `K`, and neither equals `repo/.aw/records/runs`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_migrate_runtime_state.py::test_rollback_restores_legacy_byte_identical` exits 0 showing `passed`. The test seeds legacy control files, records their sha256, runs `migrate_runtime_state.apply` with an injected mid-move fault, then `rollback`, and asserts every legacy file exists again with a byte-identical sha256; it also asserts a second concurrent `apply` while the migration lock is held raises the lock error (proving the exclusive lock via `layout_migration.MigrationManager`).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_migrate_runtime_state.py::test_both_roots_live_fails_closed_no_merge` exits 0 showing `passed`. The test creates a non-empty legacy `.aw/state/ipd-lifecycle` AND a non-empty `checkout_state_root(K)/ipd-lifecycle`, snapshots both trees' file lists + digests, asserts `assess(repo).status == "DUAL_ROOT_CONFLICT"`, asserts `apply(repo)` raises/exits non-zero with a message naming BOTH roots, and asserts both trees' file lists + digests are UNCHANGED afterward (no merge, no move). ADVERSARIAL guard (b): both-roots-live is refused, never heuristically merged.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_migrate_runtime_state.py::test_no_dual_write_after_new_root_populated` exits 0 showing `passed`. The test asserts `readable_root(repo)` returns the legacy root while the new root is empty and the new root once it is non-empty; then performs a write, records the legacy root's mtime/contents, performs a second write, and asserts the legacy root is byte-identical/mtime-unchanged across the second write (proving no dual-write; all writes hit the new root).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `python3 -m pytest -p no:randomly -q tests/test_migrate_runtime_state.py -k cli_dry_run_and_apply` exits 0 showing `passed`. The test runs `python3 -m agent_workflows migrate-runtime-state` (no `--apply`) via subprocess, asserts exit 0, that stdout contains the inventory (a `source`/`dest`/`sha256` line), and that both roots are unchanged (dry-run made no filesystem change); then runs `... migrate-runtime-state --apply` on a legacy-only repo and asserts exit 0 and the files now live under `checkout_state_root`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: TWO pasted commands. (1) `grep -rn "sync_receipt_into_worktree" agent_workflows/` prints NOTHING and exits 1 (no matches: definition + both call sites removed). (2) `python3 -m pytest -p no:randomly -q tests/test_receipt_copy_removed.py::test_sync_receipt_into_worktree_is_gone tests/test_migrate_runtime_state.py::test_inner_aw_in_worktree_writes_out_of_repo_no_state_fork` exits 0 showing `2 passed`; the second test performs a migration, invokes an inner `aw` with cwd inside a linked worktree, asserts the state write landed under `platform_state.checkout_state_root(<checkout-id>)`, and asserts a `find <worktree> -path '*/.aw/state*'` / `ls <worktree>/.aw` shows NO `.aw/state` and NO `.aw/records/runs` fork inside the worktree. ADVERSARIAL guards (a) worktree has no state fork + (c) receipt-copy code path is gone. Plus paste the full-suite `python3 -m pytest -p no:randomly -q` result showing no regressions.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: one relocation cut - moving AW control state out of the repo to the XDG state dir keyed by checkout-id - whose E-items are interdependent facets of that single migration (the helper is required before routing; routing is required before the migration can target the new root; the migration's fail-closed dual-root and no-dual-write window are the same transaction's safety rules; the receipt-copy removal is only safe once routing resolves the receipt out of repo). They are not independently shippable without leaving a half-relocated state tree (a forked authority hazard worse than the current one), so this is one cohesive exception rather than separable standard plans.

This child inherits the Set's shared anti-greenwash execution contract from orchestrator bl9q3d verbatim:

1. **Prose is never evidence.** No E-item is complete on an assertion. Each E-item names ONE observable action; each paired V-item names FALSIFIABLE evidence: an exact command to run plus the specific string/exit-code/file-state that must appear. "Tests pass", "done", "verified", "should work" are forbidden as evidence.
2. **Paste real output (HARD MUST).** Every V-item's Observed evidence MUST be the ACTUAL pasted stdout/stderr + exit code of the named command, run in this repo at execution time. Fabricated, summarized, remembered, or "expected" output is a validation failure and a GP2 honesty violation. A V-item whose command was not run stays `Result: pending`.
3. **Adversarial acceptance is mandatory.** Because this Set is ABOUT untrustworthy agents, each child MUST include at least one adversarial test proving the guard fires: a test that a wrong/forgetful/lying behavior is DETECTED and BLOCKED (e.g. a fabricated outcome.json does not mark success; a stale/forked receipt is refused; an unanswerable permission prompt is killed, not awaited). Green-path-only tests are insufficient and are an UNDER-SCOPE finding.
4. **Determinism over model judgment.** Where a check can be a pure function + unit test (path resolution, receipt validity, scope reconciliation, retention classification), it MUST be, and the hook/driver/verifier MUST call the SAME predicate library so rules cannot drift.
5. **Scope fence.** Touch ONLY the child's declared Scope-Paths. Do not edit sibling children, this orchestrator, or product code outside scope. If the work seems to need more, STOP and report - do not silently broaden.
6. **Path-scoped commits, never push.** `git commit -m msg -- <paths>`; never `git add -A`/bare/`-a`; never push; never `--no-verify`.
7. **Lifecycle move is a POST-gate step.** Verify every V-item with pasted output, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Do NOT mark executed or move the plan unless validation actually passed. (NOTE: until wtiso-03 lands, finalize may hit xmqv5l; if so, record substantially-complete honestly rather than forcing.)
8. **Cite the research.** Each child's Findings section MUST cite the exact x03wgn section(s) it implements (research doc 20260828-wtiso-00-x03wgn) so a reviewer can check fidelity to the approved design.

Post-gate lifecycle move: after every V-item shows pasted passing evidence and the full suite is green, run `aw ipd lint --phase pre-transition` on this file, then `aw ipd finalize` it (honoring the contract note about xmqv5l until wtiso-03 lands). Commit ONLY the Scope-Paths files, path-scoped, never push. The three mandatory adversarial guards - V-09 (inner-aw-in-worktree writes out-of-repo with NO `.aw/state` fork + receipt-copy code path gone), V-06 (both-roots-live fails closed, no merge), and the V-09 `grep` proof - must each show pasted passing output before this plan may move to executed/.
