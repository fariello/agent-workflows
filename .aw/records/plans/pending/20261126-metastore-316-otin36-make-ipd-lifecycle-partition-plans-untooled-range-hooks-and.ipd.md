# IPD: Make ipd_lifecycle, partition, plans, untooled-range, hooks, and meta_repair log-aware in the cutover code patch

- Date: 2026-11-26
- Kind: child
- Concern: Backlog `ldfefd` (metastore cutover test conversion; recorded in batch C plan `x8id25` F-05 and OQ-01, recovered from `run-20261126T020242Z-3080634` parked branch `aw/parked/run-20261126T020242Z-3080634/x8id25` under Option 1): inside `.aw/system/cutover/metastore-code.cutover.patch`, writers already create post-cutover log-backed records whose `.md` file holds only the two-key YAML mirror (`id`, `status`) while all other fields and history live in `.aw/records/meta/<id6>.jsonl`. Five production areas were not updated to read or commit companion logs: (1) `agent_workflows/ipd_lifecycle.py` calls `_lint.parse` without log state at 10 sites (`_extract_plan_id`, `_requirements_from_plan`, `_frozen_scope_paths`, `_is_grandfathered_scope`, `begin`, `finalize_precheck`, `retire_orchestrator`, `finalize`) so log-format plans fail closed with missing `- Id:` or empty `Scope-Paths`, and `_finalize_transaction` sets `owned_paths = [tx_plan_rel, dest_rel]` without staging `.aw/records/meta/<plan_id>.jsonl`, dropping the appended `executed` log event on worktree teardown; (2) `agent_workflows/partition.py` (`_is_orchestrator_plan`, both `_selectors._read_setid` calls, and `classify_sets`'s `_read_item_dependencies` fallback) and `agent_workflows/plans.py` (`_status_from_state`, `read_set`, and `scan`) read legacy bullet fields (`legacy_raw_status`, `legacy_raw_set`, `read_text`) instead of log-backed `State`, returning `None`/`False`/`[]` on log-format plans; (3) `agent_workflows/check_engine.py` (`_read_plan_state_at_checked`, `_check_untooled_plan_transition`, `check_status_untooled`, and `check_status_untooled_range`) reads only replayed log state via `artifact_meta.read_at` and ignores hand-edited in-file YAML mirror `status:` flips; (4) `agent_workflows/hooks/executed_transition_gate.py::check` and `agent_workflows/hooks/backlog_blocking_close_gate.py::check` read metadata before calling `_migration_marker_accepts(root)`, raising `MetadataSchemaError` on unstamped legacy repositories before the `m0001` terminal-commit marker can short-circuit; and (5) `agent_workflows/meta_cli.py::meta_repair` calls `_meta.resolve` and `_meta.repair` without catching `MetadataSchemaError`, crashing with an uncaught exception on unmigrated legacy repositories instead of returning a structured exit-2 `CommandResult` naming `aw migrate metadata`. Together these five gaps block five batch C test modules (`x8id25`) and post-cutover lifecycle workflows.
- Scope: In an isolated scratch worktree `.aw/state/otin36/scratch` with both cutover patches applied (including prerequisite plans `hdwqex`, `89mtbl`, `nv3upa`, `fljn9b`, `cugg3w`, and `szykgd`), make `agent_workflows/ipd_lifecycle.py`, `agent_workflows/partition.py`, `agent_workflows/plans.py`, `agent_workflows/check_engine.py::check_status_untooled` and `check_status_untooled_range`, `agent_workflows/hooks/executed_transition_gate.py::check`, `agent_workflows/hooks/backlog_blocking_close_gate.py::check`, and `agent_workflows/meta_cli.py::meta_repair` log-aware while keeping legacy bullet-format parity intact. Add and pass core behavioral test module `tests/test_cutover_log_lifecycle_and_hooks.py` in the scratch worktree, and regenerate `.aw/system/cutover/metastore-code.cutover.patch`. Make no live code changes outside `- Scope-Paths:`.
- Scope-Paths: .aw/records/plans/pending/20261126-metastore-316-otin36-make-ipd-lifecycle-partition-plans-untooled-range-hooks-and.ipd.md, .aw/system/cutover/metastore-code.cutover.patch
- Item-Dependencies: executed:szykgd
- Status: approved
- Review-Depth: standard
- Readiness: go-pending-approval
- From-Spec: 4sd62s
- Work-Kind: bug
- Priority: high
- From-Backlog: ldfefd
- Blocks-Release: next
- Set: metastore
- Order: 316
- Highest E allocated: 05
- Author: antigravity/gemini
- Id: otin36
- Approval: 2026-11-27, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-27 approved (aw set): status set to approved
- 2026-11-26 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-006, PR-007, PR-008; review record .aw/records/reviews/20261126-metastore-316-otin36-make-ipd-lifecycle-partition-plans-untooled-range-hooks-and.review.md
- 2026-11-26 same-status (aw set): OQ-02 Option 1: re-chain production-fix plans otin36..3e0vfy ahead of test batches psm9ac..x3mig6
- 2026-11-26 to-review (aw set): demoted reviewed -> to-review: These were flagged as '[stale-review]'
- 2026-11-26 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED
- 2026-11-26 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005; review record .aw/records/reviews/20261126-metastore-316-otin36-make-ipd-lifecycle-partition-plans-untooled-range-hooks-and.review.md
- 2026-11-26 to-review (aw set): authored as Order 316 ahead of x8id25 per recovery of run-20261126T020242Z-3080634 parked x8id25 OQ-01 Option 1
- 2026-11-26 draft (antigravity/gemini): created.

## Goal

Make IPD lifecycle transactions, work partitioning and plan scanning, untooled-status commit and range checks, migration-marker pre-commit gates, and `aw meta repair` log-aware inside `.aw/system/cutover/metastore-code.cutover.patch`, unblocking batch C (`x8id25`) and downstream cutover execution while preserving legacy parity.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [ ] E-01 Create the scratch worktree following the SCRATCH PROCEDURE of executed plan `2k5t16` (Step 0): run `git worktree add --detach .aw/state/otin36/scratch HEAD`; inside `.aw/state/otin36/scratch`, run `git apply --index .aw/system/cutover/metastore-docs.cutover.patch`, record `BASE=$(git write-tree)` in F-01, and then run `git apply --index .aw/system/cutover/metastore-code.cutover.patch`. If either patch rejects, stop and report.
  - Depends on: none
  - Expected outcome: `.aw/state/otin36/scratch` holds HEAD plus both patches staged, and F-01 records the base tree id.
  - Execution state: pending

### Task group 2: log-aware lifecycle, partition/plans, untooled-range, hooks, and meta_repair (scratch worktree only)

- [ ] E-02 Make `agent_workflows/ipd_lifecycle.py` log-aware in `.aw/state/otin36/scratch` while keeping legacy bullet-format parity intact:
  1. Add a shared helper that resolves optional companion `artifact_meta.State` for a plan path (via `artifact_meta.read_mirror_id6(text)` and the records root inside `artifact_meta.ephemeral_if_uninitialized()`, letting `MetadataSchemaError` propagate and returning `None` for unlogged legacy text), and pass `state=` to `_lint.parse(...)` at all 10 bare `_lint.parse` sites in `agent_workflows/ipd_lifecycle.py` (`_extract_plan_id`, `_requirements_from_plan`, `_frozen_scope_paths`, `_is_grandfathered_scope`, `begin`, `finalize_precheck`, `retire_orchestrator` x2, `finalize`, and scope-reason loading). Because `_requirements_from_plan`, `_frozen_scope_paths`, and `_is_grandfathered_scope` currently accept only `text: str`, add an optional `state=None` (or `doc=None`) parameter to each and pass the resolved `State` from their callers (`begin`, `finalize_precheck`, `finalize`, `_check_scope_widening`) so log-format plans yield accurate `Id`, `Status`, `Kind`/`Order`, and `Scope-Paths`.
  2. Update `agent_workflows/ipd_lifecycle.py::_finalize_transaction` across all three `owned_paths` construction points (non-git / `companion-lane-staged`, initial journal preparation + `git_index_entries`, and coordinator-worktree staging before `git add`) so when a companion log `.aw/records/meta/<plan_id>.jsonl` (or `.agents/meta/<plan_id>.jsonl` or companion-repo `meta/<plan_id>.jsonl`) exists for the finalized plan, its repo-relative path `meta_rel` is included in `owned_paths` alongside `tx_plan_rel` and `dest_rel`. Ensure the appended `executed` log event is staged and committed in the atomic finalize transaction rather than dropped on worktree teardown; in the non-git / `companion-lane-staged` branch (which mutates `plan_root` directly rather than a detached coordinator worktree), snapshot `meta_rel` and its pre-mutation bytes into the finalize journal and atomically restore them in `_rollback_precommit` on pre-commit fault (never deleting a pre-existing `meta/<plan_id>.jsonl`); and update `_assert_rollup_touched_only_owned_paths` to also reject uncommitted changes to the orchestrator's companion `meta/<plan_id>.jsonl` before rollup retirement.
  - Depends on: E-01
  - Expected outcome: in a throwaway log-format repository on `.aw/state/otin36/scratch`, `aw ipd begin` and `aw ipd finalize` succeed, freeze and reconcile log-stored `Scope-Paths`, move the plan to `.aw/records/plans/executed/`, and commit both the moved plan file and `.aw/records/meta/<plan_id>.jsonl` with the `executed` event.
  - Execution state: pending

- [ ] E-03 Make `agent_workflows/partition.py`, `agent_workflows/plans.py`, `agent_workflows/check_engine.py`, `agent_workflows/hooks/executed_transition_gate.py`, `agent_workflows/hooks/backlog_blocking_close_gate.py`, and `agent_workflows/meta_cli.py` log-aware in `.aw/state/otin36/scratch`:
  1. In `agent_workflows/partition.py` (`_is_orchestrator_plan`, both `_selectors._read_setid` call sites, and `classify_sets`'s `runner_shared._read_item_dependencies` fallback for Set members not in `cand_by_id`) and `agent_workflows/plans.py` (`_status_from_state`, `read_set`, and `scan`):
     - Fix `plans._status_from_state` to read `getattr(st, "status", None)` before falling back to `getattr(st, "legacy_raw_status", None)` (which is `None` on log-format `State` rows).
     - Update `plans.scan` to read `set_id` and `order` from the cached `State` (`st.set_id`, `st.order_nn`) with fallback to `read_set(f)`, and make `plans.read_set` resolve companion `meta/<id6>.jsonl` inside `artifact_meta.ephemeral_if_uninitialized()` when called directly (falling back to `artifact_meta.read_text` for unlogged legacy text).
     - Update `partition.py` to read `plan_role`, `set`, and `item_dependencies` from companion `artifact_meta.State` inside `artifact_meta.scan_once()` and `artifact_meta.ephemeral_if_uninitialized()` when a log exists (falling back to text parsing for legacy files).
  2. In `agent_workflows/check_engine.py` (`_read_plan_state_at_checked`, `_check_untooled_plan_transition`, `check_status_untooled`, and `check_status_untooled_range`), pass the in-file YAML mirror status from `artifact_meta.resolve_mirror_at` for both old and new revisions into `_check_untooled_plan_transition`, and switch `check_status_untooled_range` to `_read_plan_state_at_checked` (emitting a `check.status-untooled` drift and continuing whenever `new_corrupt is not None`, matching `check_status_untooled`):
     - Check mirror-vs-log consistency BEFORE the `is_in_executed` early returns in `_check_untooled_plan_transition`: flag `check.status-untooled` whenever a plan's in-file mirror `status:` at the new revision (`new_mirror_status`) contradicts `new_state.status` (including hand-edited mirror flips to intermediate, retirement, or `executed` statuses, or flips on an already-`executed/` plan, without a matching log transition or finalize commit), while accepting tooled `artifact_meta.append` / `aw ipd set` / `aw ipd finalize` transitions (and legacy bullet-format plans) where log and mirror agree.
  3. In `agent_workflows/hooks/executed_transition_gate.py::check` and `agent_workflows/hooks/backlog_blocking_close_gate.py::check`, call `_migration_marker_accepts(root)` BEFORE reading artifact metadata or running release-gate metadata queries, so unstamped legacy repositories running an `m0001` terminal commit short-circuit cleanly instead of raising `MetadataSchemaError` under `CURRENT_METADATA_SCHEMA == 2`, while mismatched, wrong-id, or corrupt markers still fall through to standard fail-closed gate checks.
  4. In `agent_workflows/meta_cli.py::meta_repair`, catch `agent_workflows/migrations/chain.py::MetadataSchemaError` around `_meta.resolve(tok, project_context=ctx)` and `_meta.repair(...)` and return a structured `CommandResult(command="meta repair", status="cannot-run", exit_code=2, ..., next_actions=[NextAction(command="aw migrate metadata")])` whose summary names `aw migrate metadata` instead of raising an uncaught exception on unmigrated legacy repositories.
  5. Record the verified caller and behavior audit across all five areas in F-02.
  - Depends on: E-02
  - Expected outcome: `partition` and `plans.read_set`/`scan` return accurate `status`, `plan_role`, `set`, `order`, and member `item_dependencies` on log-format plans; `check_status_untooled` and `check_status_untooled_range` catch hand-edited YAML mirror status flips while accepting tooled transitions; both pre-commit hooks accept valid `m0001` migration markers on unstamped legacy repos and still refuse mismatched or corrupt markers; and `meta_cli.meta_repair` returns exit 2 naming `aw migrate metadata` on unmigrated legacy repos.
  - Execution state: pending

- [ ] E-04 Add and run core behavioral test module `tests/test_cutover_log_lifecycle_and_hooks.py` (`pytestmark = pytest.mark.core`) in `.aw/state/otin36/scratch` (asserting real outputs, exit codes, and side effects; no code-pinning tests):
  1. Cover `ipd_lifecycle.begin`, `finalize_precheck`, `finalize`, and `retire_orchestrator` on log-format plans, verifying `Scope-Paths` freezing/reconciliation, dirty companion-log refusal in rollup retirement, pre-commit fault rollback restoring pre-mutation `meta/<plan_id>.jsonl` bytes in the non-git / `companion-lane-staged` branch without deleting the log, and verifying the finalize commit includes both the moved plan file and `.aw/records/meta/<plan_id>.jsonl` with `status == "executed"`.
  2. Cover `partition._is_orchestrator_plan`, `partition.classify_sets` (including Set-id resolution and non-candidate member `item_dependencies`), `plans.read_set`, and `plans.scan` (`status`, `set_id`, `order`) on log-format orchestrator and child plans.
  3. Cover `check_engine.check_status_untooled` and `check_engine.check_status_untooled_range` catching a hand-edited YAML mirror `status:` flip (intermediate and `executed`) while accepting a tooled `artifact_meta.append` / `aw ipd set` transition that updates both log and mirror.
  4. Cover `executed_transition_gate.check` and `backlog_blocking_close_gate.check` accepting a valid `m0001` migration marker commit on an unstamped schema-1 legacy repo without raising `MetadataSchemaError`, while still refusing an unmarkered, mismatched-marker, or corrupt-marker violation on a schema-2 log-format repo.
  5. Cover `meta_cli.meta_repair` returning structured exit-2 `CommandResult` naming `aw migrate metadata` on an unmigrated legacy repo without raising an uncaught exception.
  6. Run `python3 -m pytest -o addopts="" -m '' -v tests/test_cutover_log_lifecycle_and_hooks.py` in `.aw/state/otin36/scratch` and confirm every test passes.
  - Depends on: E-03
  - Expected outcome: `tests/test_cutover_log_lifecycle_and_hooks.py` passes every test in `.aw/state/otin36/scratch`.
  - Execution state: pending

### Task group 3: package

- [ ] E-05 In `.aw/state/otin36/scratch`, run `git add -A` and write `git diff --cached --binary $BASE` over `.aw/system/cutover/metastore-code.cutover.patch` in the executing checkout; remove the scratch worktree (`git worktree remove --force .aw/state/otin36/scratch`); run `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout; verify `git status --short` shows only `- Scope-Paths:` modified; and commit through `aw commit otin36 -- .aw/records/plans/pending/20261126-metastore-316-otin36-make-ipd-lifecycle-partition-plans-untooled-range-hooks-and.ipd.md .aw/system/cutover/metastore-code.cutover.patch`; never push.
  - Depends on: E-04
  - Expected outcome: `.aw/system/cutover/metastore-code.cutover.patch` contains all prior code-patch hunks plus this plan's changes; `tests/test_metastore_cutover_code_patch.py` passes; scratch worktree is removed; one path-scoped commit is created.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The scratch procedure and cumulative code patch are defined in executed plan `2k5t16` (Step 0, OQ-01); executed sibling `g45vyv`, reviewed sibling `hdwqex`, Order 314 sibling `fljn9b`, and Order 315 sibling `szykgd` follow the same procedure.
- `agent_workflows/ipd_lint.py` (updated by `hdwqex`) accepts an optional `state` parameter on `parse(...)` so log-backed plans expose `Id`, `Status`, `Scope-Paths`, and other fields without inline metadata bullets.
- `agent_workflows/migrations/chain.py::MetadataSchemaError` subclasses `RuntimeError`, so catching it explicitly in `meta_cli.meta_repair` while letting it propagate through normal schema-2 readers keeps spec `4sd62s` AC-11 intact.
- Tests exercise real behavior and assert on observable outcomes (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no `inspect`, `ast`, regex, or substring code-pinning tests.
- Cite code by symbol (`path::Symbol`) or by a quoted content string, with a line number only appended as a hint and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | (written by E-01) | Base tree id after applying `.aw/system/cutover/metastore-docs.cutover.patch`. |
| F-02 | (written by E-03) | Caller and behavior audit across `ipd_lifecycle.py`, `partition.py`, `plans.py`, `check_engine.py`, `hooks/executed_transition_gate.py`, `hooks/backlog_blocking_close_gate.py`, and `meta_cli.py`. |
| F-03 | `x8id25` F-05 and static audit of `.aw/system/cutover/metastore-code.cutover.patch` and live modules: 10 bare `_lint.parse(...)` calls and `owned_paths` in `ipd_lifecycle.py::_finalize_transaction`; `partition.py::_is_orchestrator_plan` and `_selectors._read_setid` calls plus `plans.py::read_set`/`scan`; `check_engine.py::check_status_untooled_range`; `_migration_marker_accepts` placement in `hooks/executed_transition_gate.py::check` and `hooks/backlog_blocking_close_gate.py::check`; and uncaught `MetadataSchemaError` in `meta_cli.py::meta_repair`. | Five verified production cutover gaps in `.aw/system/cutover/metastore-code.cutover.patch` block `x8id25` (batch C) and downstream cutover execution. |
| F-04 | `agent_workflows/ipd_lifecycle.py` (`_requirements_from_plan`, `_frozen_scope_paths`, `_is_grandfathered_scope`, `_rollback_precommit`, `_assert_rollup_touched_only_owned_paths`, `_finalize_transaction` lines 6065/6123/6155/6317); `agent_workflows/plans.py::_status_from_state` and `read_set`; `agent_workflows/partition.py::classify_sets` (`_read_item_dependencies` fallback); `agent_workflows/check_engine.py::check_status_untooled`, `check_status_untooled_range`, and `_check_untooled_plan_transition`; `agent_workflows/artifact_meta.py::scan_once` and `ephemeral_if_uninitialized`; `agent_workflows/meta_cli.py::meta_repair`. | Additional co-located cutover hazards verified during review: (1) `_requirements_from_plan`, `_frozen_scope_paths`, and `_is_grandfathered_scope` accept only `text: str` and need optional `state=` threaded from callers, `_finalize_transaction` builds `owned_paths` at three sites and mutates `meta/<plan_id>.jsonl` in place on the non-git / `companion-lane-staged` branch (needing journal snapshot + `_rollback_precommit` restore on fault), and `_assert_rollup_touched_only_owned_paths` checks only `plan_rel`; (2) `plans._status_from_state` reads only `legacy_raw_status` (returning `None` for every log-format plan/prompt), `partition.classify_sets` reads member `item_dependencies` from `.md` text only, and read-only companion-log lookups need `ephemeral_if_uninitialized()` / `scan_once()`; (3) `check_status_untooled` shares the mirror-flip blind spot with `check_status_untooled_range`, mirror-vs-log checks must run before `is_in_executed` early returns, and `check_status_untooled_range` must emit `check.status-untooled` when `_read_plan_state_at_checked` reports corrupt metadata. |

## Proposed changes (ordered, validatable)

1. E-01: Create scratch worktree `.aw/state/otin36/scratch` with both cutover patches staged.
2. E-02: Make `agent_workflows/ipd_lifecycle.py` parse calls (including `state=` threading into `_requirements_from_plan`/`_frozen_scope_paths`/`_is_grandfathered_scope`), `_assert_rollup_touched_only_owned_paths`, `_rollback_precommit` companion-log restore, and all three `owned_paths` sites in `_finalize_transaction` log-aware while keeping legacy parity.
3. E-03: Make `partition.py`, `plans.py` (including `_status_from_state`), `check_engine.py::check_status_untooled` and `check_status_untooled_range`, `executed_transition_gate.py`/`backlog_blocking_close_gate.py` marker checks, and `meta_cli.py::meta_repair` log-aware; record F-02.
4. E-04: Add and pass core behavioral test module `tests/test_cutover_log_lifecycle_and_hooks.py` in `.aw/state/otin36/scratch`.
5. E-05: Regenerate `.aw/system/cutover/metastore-code.cutover.patch`, remove the scratch worktree, pass `tests/test_metastore_cutover_code_patch.py`, and commit path-scoped.

```mermaid
flowchart TD
    E01["E-01: Create scratch worktree with both patches"] --> P{"Patches apply cleanly?"}
    P -->|No| STOP["Stop and report"]
    P -->|Yes| E02["E-02: Make ipd_lifecycle.py parse and finalize log-aware"]
    E02 --> E03["E-03: Make partition, plans, untooled checks, hooks, and meta_repair log-aware"]
    E03 --> E04["E-04: Add and run tests/test_cutover_log_lifecycle_and_hooks.py"]
    E04 --> E05["E-05: Regenerate code patch, run guard test, commit"]
```

## Deferred / out of scope (with reason)

- Making `ipd_lint`, `ipd_schema`, and `ipd_authoring` log-aware: already owned by Order 305.
  - Carrier: hdwqex
- Making `backlog.py` and `specs.py`/`releases.py`/`check_engine.py` spec-link/`cli._run_search`/`ipd_dependency_statement_gate.py` log-aware: already owned by Orders 314 and 315.
  - Carrier: fljn9b, szykgd
- Remaining production log-awareness fixes (`p109wy` -> `q6fiws` -> `j1f454` -> `lec341` -> `3e0vfy`): chained immediately after this plan (`p109wy` depends on `executed:otin36`) and ahead of test batches B through F per `psm9ac` OQ-02 Option 1.
  - Carrier: p109wy
- Converting batch C's 18 test modules (`test_ipd_lifecycle_cli` through `test_prompts_set_surface`): runs after `psm9ac` once the remaining production log-awareness plans (`p109wy..3e0vfy`) land.
  - Carrier: x8id25
- Converting later test batches (batches D through F): later batch children.
  - Carrier: e0g2gt
- Applying the cutover patches on the real tree: attended cutover commit.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No live code or test files are modified outside `.aw/system/cutover/metastore-code.cutover.patch`.
- Under-scope: none. All five production cutover gaps recorded in `x8id25` F-05 plus the co-located hazards in F-04 map to E-02 through E-04.

## Required tests / validation

- Throwaway-repository smoke checks on `.aw/state/otin36/scratch` for `ipd_lifecycle` begin/finalize, `partition`/`plans`, `check_status_untooled`/`check_status_untooled_range`, both pre-commit migration-marker hooks, and `meta_cli.meta_repair` (V-02, V-03).
- Core behavioral test module `python3 -m pytest -o addopts="" -m '' -v tests/test_cutover_log_lifecycle_and_hooks.py` in `.aw/state/otin36/scratch` (V-04).
- Cumulative patch guard test `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout (V-05).

## Spec / documentation sync

No spec or documentation change is needed in this plan. Spec `4sd62s` Sections 4.1 through 4.6 and 5.2 already define the post-cutover log format, and `.aw/system/cutover/metastore-docs.cutover.patch` already updates the documentation. This plan brings these five production lifecycle, partitioning, untooled-check, pre-commit hook, and repair paths inside the cutover code patch into agreement with them.

## Open questions

None open.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition) - as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction - name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `git worktree add --detach .aw/state/otin36/scratch HEAD` command, both `git apply --index` commands (for `.aw/system/cutover/metastore-docs.cutover.patch` and `.aw/system/cutover/metastore-code.cutover.patch`) with exit status 0, and the base tree id recorded in F-01.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste a throwaway-repository run on `.aw/state/otin36/scratch` (code paths updated by E-02) showing `aw ipd begin` and `aw ipd finalize` succeeding on a log-format plan (with frozen log-stored `Scope-Paths`), moving it to `.aw/records/plans/executed/`, and `git show --name-only HEAD` listing both the moved plan file and `.aw/records/meta/<plan_id>.jsonl` with `status == "executed"`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste F-02 (audit across all five areas) and observed outputs on `.aw/state/otin36/scratch` (code paths updated by E-03) showing `partition._is_orchestrator_plan`, `partition.classify_sets`, `plans.read_set`, and `plans.scan` returning log-stored `status`, `plan_role`, `set`, `order`, and member `item_dependencies`, `check_engine.check_status_untooled` and `check_status_untooled_range` flagging a hand-edited YAML mirror `status:` flip while accepting a tooled transition, `executed_transition_gate.check` and `backlog_blocking_close_gate.check` returning exit 0 on a valid `m0001` migration marker commit in an unstamped schema-1 repo (and exit 1 on an unmarkered or mismatched-marker violation on a schema-2 repo), and `meta_cli.meta_repair` returning exit 2 naming `aw migrate metadata` on an unmigrated legacy repo.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the full `python3 -m pytest -o addopts="" -m '' -v tests/test_cutover_log_lifecycle_and_hooks.py` output in `.aw/state/otin36/scratch` showing every test PASSED across `ipd_lifecycle`, `partition`/`plans`, `check_status_untooled`/`check_status_untooled_range`, both migration-marker hooks, and `meta_cli.meta_repair`.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-code.cutover.patch`, the `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` run showing every guard test PASSED (docs + code patch apply cleanly, patch touches files, and a broken patch is refused), `git worktree list` showing `.aw/state/otin36/scratch` removed, `git status --short` confirming no live edits outside `- Scope-Paths:`, and the `aw commit otin36` output naming the commit hash.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` (`szykgd`) is executed; open questions: none open. Code and tests are edited ONLY inside `.aw/state/otin36/scratch` and packaged into `.aw/system/cutover/metastore-code.cutover.patch`. Scope fence: `- Scope-Paths:` is a declaration; any needed edit outside it must be justified at finalize (`--scope-reason`), and any declared path left unmodified must be acknowledged (`--scope-ack`). Safety stop conditions: stop and report rather than editing live production code outside the scratch worktree or weakening test assertions if a patch hunk rejects, an unexpected failure occurs on unmodified code, or an unresolvable concurrent-edit conflict occurs. Honesty rule: you MUST paste the ACTUAL runner output of every command named in V-01 through V-05; never claim a result you did not run. Commits: commit only through `aw commit otin36 -- <paths>`; never push. Lifecycle transition: after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence, in a managed runner lane stop after committing the updated plan and let the runner run `aw ipd finalize`; in a hand-run session run `aw ipd finalize` to move the plan to `.aw/records/plans/executed/` (never use a raw `git mv` to `executed/`).
