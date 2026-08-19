# IPD: actually rename local lanes to untracked on both layouts, retroactive + gitignored

- Date: 2026-08-19
- Kind: child
- Concern: awuntracked-01 shipped `migrate_local_lanes_to_untracked` but it never took effect. (1) It receives only the ACTIVE layout's `dirs` (`.aw/records/*`), so it structurally cannot rename the legacy `.agents/{prompts,comms}/local`. (2) It runs only during `aw install`/scaffold, so it is NOT retroactive - a repo not reinstalled keeps `local/` (this repo still has all four: `.aw/records/{prompts,comms}/local` + `.agents/{prompts,comms}/local`). (3) It does not rewrite the nested `.gitignore`'s `local/` line to `untracked/`, and the legacy `.agents/comms/` has NO nested `.gitignore` at all (its ephemeral acks are safe only by the accident that `.agents/` is entirely untracked). Verified: `.agents/` has 0 tracked files (stale post-migration litter; canonical tree is `.aw/records/`).
- Scope: `agent_workflows/engine.py` (`migrate_local_lanes_to_untracked` + the scaffold call ordering + nested-gitignore rewrite) and `agent_workflows/cli.py`/`layout_migration.py` (invoke the rename from the retroactive `aw migrate-layout` verb); rename this repo's four lanes as evidence; tests. Does NOT decide the fate of the `.agents/` litter tree (that is backlog wxz7gg) - it only ensures the lane is named `untracked/` + gitignored wherever it exists.
- Status: reviewed
- Set: awuntrackedfix
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: njfyjt

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - awuntracked-01's lane migration only touched the active layout, ran only on install, and left the nested gitignore unrewritten; this makes the rename cover BOTH layouts, be retroactive via `aw migrate-layout`, and keep the lane gitignored.
- 2026-08-19 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): reviewed - verified all four `local/` lanes exist, `.agents/` is untracked litter (0 tracked), migrate_local_lanes_to_untracked is active-layout+install-gated only, migrate-layout is the retroactive verb whose data-loss guard preserves `local/`. Anchors verified. Verdict: GO - PENDING HUMAN APPROVAL. Awaiting explicit human approval before execution.

## Goal

Make `local/` -> `untracked/` actually happen: rename the quarantine lane in BOTH the canonical (`.aw/records/`) AND legacy (`.agents/`) layouts, retroactively (a repo need not be reinstalled), and ensure the surviving lane carries a nested `.gitignore` that ignores `untracked/` so ephemeral acks can never be staged. Leave the four lanes in THIS repo renamed as validation evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: make the migration cover both layouts + the gitignore

- [ ] E-01 In `agent_workflows/engine.py`, generalize `migrate_local_lanes_to_untracked(repo_root, dirs)` so it renames the lane in EVERY layout present, not just the passed `dirs`. Concretely: build the candidate base list from BOTH the canonical and legacy roots - `.aw/records/prompts`, `.aw/records/comms`, `.agents/prompts`, `.agents/comms` (dedup with any `dirs` values) - and for each existing `<base>/local`, rename to `<base>/untracked` (keep the existing clean-rename / content-merge / idempotent logic). Keep the signature back-compatible (`dirs` optional/ignored-superset) so the scaffold call still works. Return the list of renamed lanes.
  - Depends on: none
  - Expected outcome: calling it on a repo with `.aw/records/comms/local` AND `.agents/prompts/local` renames BOTH to `untracked/`; a second call is a no-op.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/engine.py`, (a) ALSO ensure a nested `.gitignore` ignoring `untracked/` exists in each comms/prompts base that has the lane: after renaming, if `<base>/.gitignore` is absent, write the comms/prompts nested-gitignore template (already updated by awuntracked-01 to emit `untracked/`); if present but still contains a bare `local/` line, rewrite that line to `untracked/`. (b) Fix the scaffold ordering (engine.py:4340-4348): call `migrate_local_lanes_to_untracked` BEFORE the `mkdir(... "untracked" ...)` so an existing `local/` gets a CLEAN rename rather than a merge into a freshly-mkdir'd `untracked/`.
  - Depends on: E-01
  - Expected outcome: every comms/prompts base with an `untracked/` lane has a sibling `.gitignore` containing `untracked/` and no bare `local/`; a fresh scaffold on a repo with a populated `local/` performs a clean rename (no pre-created empty `untracked/`).
  - Execution state: pending

### Task group 2: make it retroactive via the migrate verb

- [ ] E-03 Wire the lane rename into the retroactive `aw migrate-layout` verb so a user can fix an existing repo WITHOUT reinstalling. In `_run_migrate_layout` (cli.py:4055) - or the `MigrationManager` it drives (`agent_workflows/layout_migration.py`) - after the layout move completes (and also when there is nothing to move), call `engine.migrate_local_lanes_to_untracked(repo_root, {})` and report the renamed lanes. Preserve the existing data-loss guard (the `/local/`-preserve predicate at layout_migration.py:439 must NOT delete the lane; renaming is a move, not a remove). This makes `aw migrate-layout` idempotently normalize lane names on any repo.
  - Depends on: E-01,E-02
  - Expected outcome: `aw migrate-layout` on this repo renames all four `local/` lanes to `untracked/` (reported), leaves contents intact, and is a no-op on a second run; the layout-move behavior and its data-loss guard are unchanged.
  - Execution state: pending

### Task group 3: apply to this repo + tests

- [ ] E-04 (a) Run the rename on THIS repo (via `aw migrate-layout` or a direct `engine.migrate_local_lanes_to_untracked(Path('.'), {})` call) so `find . -type d -iname 'local' -not -path '*/node_modules/*'` returns NOTHING under `.aw/records/` and `.agents/`, and each comms/prompts base carries a `.gitignore` with `untracked/`; the moved ack/inbox/sent contents are intact. These lanes are untracked, so this is a working-tree change, not a commit of lane contents. (b) Add `tests/test_untracked_lane_both_layouts.py` (`UntrackedBothLayoutsTests`): a tmp fixture with populated `local/` under `.aw/records/comms`, `.aw/records/prompts`, `.agents/comms`, `.agents/prompts` -> after the migration ALL four are `untracked/` with contents preserved, each base has a `.gitignore` ignoring `untracked/`, and a second run is a no-op. Run the FULL serial suite and paste the tail; update `tests/test_untracked_lane_migration.py` if the two-layout generalization changes its single-layout expectations (it should still pass - the old dirs-scoped call is a subset).
  - Depends on: E-01,E-02,E-03
  - Expected outcome: this repo has no `local/` lane left (node_modules excluded) and gitignored `untracked/` lanes; the new test passes; the old lane-migration test still passes; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.agents/` is fully untracked (0 tracked files) - stale post-migration litter; canonical is `.aw/records/`. Both trees currently hold a `local/` lane.
- `migrate_local_lanes_to_untracked` (engine.py) currently takes one `dirs` (active layout only) and does not touch the nested `.gitignore`.
- `aw migrate-layout` (cli.py:4055) is the retroactive verb; its data-loss guard (layout_migration.py:439) PRESERVES `local/` lanes (so a rename-move is safe; a remove would not be).
- The comms/prompts nested-gitignore templates already emit `untracked/` (awuntracked-01); the gap is rewriting an EXISTING `local/` gitignore line and creating the missing legacy one.
- node_modules `*/locales` dirs are unrelated (not `local/` lanes); the find filter must exclude `node_modules`.

## Findings

awuntracked-01 was correct in template + intent but inert in practice (active-layout-only + install-gated + gitignore not rewritten). This IPD makes the rename comprehensive (both layouts), retroactive (via migrate-layout), and gitignore-complete, then applies it here.

## Proposed changes (ordered, validatable)

1. Generalize the migration to both layouts.
2. Rewrite/create the nested `untracked/` gitignore; fix scaffold ordering.
3. Invoke it from `aw migrate-layout` (retroactive).
4. Apply to this repo + tests.

## Deferred / out of scope (with reason)

- Removing the stale `.agents/` litter tree entirely: deferred to backlog wxz7gg; this IPD only normalizes the lane name + gitignore wherever the tree exists.

## Scope check

- Over-scope: none.
- Under-scope: does not delete `.agents/` (wxz7gg owns that).

## Required tests / validation

`tests/test_untracked_lane_both_layouts.py` + existing `tests/test_untracked_lane_migration.py` green; live `find` shows no `local/` lane; full serial suite green.

## Spec / documentation sync

N/A: no spec governs the lane name; the gitignore + README (updated in awuntracked-01) already say `untracked/`.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The `.agents/` fate question is answered (litter; wxz7gg owns removal); this IPD is scoped to naming + gitignore only, so no open decision remains.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a fixture with `local/` under both `.aw/records/comms` and `.agents/prompts` -> after the call both are `untracked/`, contents preserved, second call returns []. Shown by the new test.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: each migrated base has a sibling `.gitignore` containing `untracked/` and no bare `local/` line; a scaffold on a populated `local/` produces a clean rename (assert no pre-created empty `untracked/` swallowed it). Shown by the new test.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw migrate-layout` on a fixture renames all present `local/` lanes to `untracked/`, reports them, is a no-op on re-run, and the layout-move + data-loss guard behavior is unchanged (existing layout-migration tests still pass).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `find . -type d -iname 'local' -not -path '*/node_modules/*'` prints nothing under `.aw/records/` and `.agents/` in THIS repo; `.aw/records/comms/.gitignore` (and the other three) contain `untracked/`; `python3 -m pytest tests/test_untracked_lane_both_layouts.py tests/test_untracked_lane_migration.py -p no:xdist -q` green; full serial suite tail pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. The four lane renames in this repo are working-tree moves of UNTRACKED content (not committed). Run the full serial suite and paste the actual runner output as V evidence. On completion, lint `--phase pre-transition` while still approved, then flip Status to executed, add an executed workflow-history line, `git mv` to `.aw/records/plans/executed/`, and lint `--phase post-transition`. Do not mark executed until every V item is verified with concrete evidence.
