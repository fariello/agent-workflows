# IPD: actually rename local lanes to untracked on both layouts, retroactive + gitignored

- Date: 2026-08-19
- Kind: child
- Concern: awuntracked-01 shipped `migrate_local_lanes_to_untracked` but it never took effect. (1) It receives only the ACTIVE layout's `dirs` (`.aw/records/*`), so it structurally cannot rename the legacy `.agents/{prompts,comms}/local`. (2) It runs only during `aw install`/scaffold, so it is NOT retroactive - a repo not reinstalled keeps `local/` (this repo still has all four: `.aw/records/{prompts,comms}/local` + `.agents/{prompts,comms}/local`). (3) It does not rewrite the nested `.gitignore`'s `local/` line to `untracked/`, and the legacy `.agents/comms/` has NO nested `.gitignore` at all (its ephemeral acks are safe only by the accident that `.agents/` is entirely untracked). Verified: `.agents/` has 0 tracked files (stale post-migration litter; canonical tree is `.aw/records/`).
- Scope: `agent_workflows/engine.py` (`migrate_local_lanes_to_untracked`: both-layout coverage + recursive content merge + scaffold ordering + nested-gitignore rewrite) and a new `aw normalize-lanes` verb (`agent_workflows/cli.py`, NO `tools.` import); rename this repo's four lanes as evidence; tests incl. an installed-wheel check. Does NOT route through `aw migrate-layout` (PR-001: that verb is dead when pip-installed) and does NOT fix that broader packaging defect (PR-003/backlog) or decide the `.agents/` litter fate (backlog wxz7gg).
- Verified in an installed wheel (Step (a)): PR-001 - `aw migrate-layout` raises `ModuleNotFoundError: No module named 'tools'` (cli.py:4061 + layout_migration.py:30 import the unshipped `tools.awphysical`; wheel ships `agent_workflows` only). PR-002 - even `aw install .` on a repo with an existing `local/acks/x.json` leaves the ack STRANDED in `local/` (scaffold mkdir's empty `untracked/acks/` first, then the shallow merge skips the nested file). Fresh installs correctly create `untracked/` (awuntracked-01's scaffold rename works only when no `local/` pre-exists).
- Status: approved
- Set: awuntrackedfix
- Order: 1
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: njfyjt
- Approval: maintainer (human), 2026-08-19: approved this specific plan and said go.

## Workflow history

- 2026-08-19 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created - awuntracked-01's lane migration only touched the active layout, ran only on install, and left the nested gitignore unrewritten; this makes the rename cover BOTH layouts, be retroactive via `aw migrate-layout`, and keep the lane gitignored.
- 2026-08-19 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): reviewed + revised after an INSTALLED-WHEEL portability test. Proven: PR-001 (migrate-layout crashes when pip-installed - tools.awphysical unshipped) and PR-002 (reinstall strands nested local/acks/x.json). Revised E-02 (recursive merge + scaffold order), E-03 (dropped migrate-layout; added tools-free `aw normalize-lanes` + scaffold path), E-04 (added installed-wheel validation). Filed PR-003 to backlog revnjq (migrate-layout dead when installed, out of scope here). Verdict: GO - PENDING HUMAN APPROVAL. Awaiting explicit human approval.
- 2026-08-19 approved (maintainer, human): explicitly approved this plan and instructed go.

## Goal

Make `local/` -> `untracked/` actually happen: rename the quarantine lane in BOTH the canonical (`.aw/records/`) AND legacy (`.agents/`) layouts, retroactively (a repo need not be reinstalled), and ensure the surviving lane carries a nested `.gitignore` that ignores `untracked/` so ephemeral acks can never be staged. Leave the four lanes in THIS repo renamed as validation evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: make the migration cover both layouts + the gitignore

- [ ] E-01 In `agent_workflows/engine.py`, generalize `migrate_local_lanes_to_untracked(repo_root, dirs)` so it renames the lane in EVERY layout present, not just the passed `dirs`. Concretely: build the candidate base list from BOTH the canonical and legacy roots - `.aw/records/prompts`, `.aw/records/comms`, `.agents/prompts`, `.agents/comms` (dedup with any `dirs` values) - and for each existing `<base>/local`, rename to `<base>/untracked` (keep the existing clean-rename / content-merge / idempotent logic). Keep the signature back-compatible (`dirs` optional/ignored-superset) so the scaffold call still works. Return the list of renamed lanes.
  - Depends on: none
  - Expected outcome: calling it on a repo with `.aw/records/comms/local` AND `.agents/prompts/local` renames BOTH to `untracked/`; a second call is a no-op.
  - Execution state: pending

- [ ] E-02 In `agent_workflows/engine.py`, fix the CONTENT-STRANDING bug (PR-002, proven in an installed wheel): (a) make the merge branch of `migrate_local_lanes_to_untracked` RECURSIVE - when both `local/<x>` and `untracked/<x>` exist, merge their contents depth-first (move files, create missing dirs) instead of the current shallow top-level `if not dest.exists()` that leaves nested files (e.g. `local/acks/x.json`) stranded when `untracked/acks/` already exists; remove the emptied `local/` tree only after all files moved. (b) Fix the scaffold ordering (engine.py:4340-4348): call `migrate_local_lanes_to_untracked` BEFORE the `mkdir(... "untracked"/<sub> ...)` so an existing populated `local/` gets a CLEAN rename rather than a merge into freshly-mkdir'd empty `untracked/<sub>` dirs. (c) ensure a nested `.gitignore` ignoring `untracked/` exists in each comms/prompts base that has the lane: if `<base>/.gitignore` is absent, write the comms/prompts nested template (emits `untracked/`); if present but still containing a bare `local/` line, rewrite that line to `untracked/`.
  - Depends on: E-01
  - Expected outcome: reinstalling (or migrating) a repo whose `local/acks/x.json` exists moves that file to `untracked/acks/x.json` (NOT stranded); every migrated base has a sibling `.gitignore` containing `untracked/` and no bare `local/`.
  - Execution state: pending

### Task group 2: a retroactive path that works WHEN INSTALLED

- [ ] E-03 Provide a retroactive rename that runs in a PIP-INSTALLED repo. PR-001 (proven): `aw migrate-layout` is DEAD when installed - `_run_migrate_layout` (cli.py:4061) and `layout_migration.py:30` both `from tools.awphysical import ...`, and `tools/` is NOT in the wheel (`pyproject.toml:67` ships `agent_workflows` only), so `agent_workflows.layout_migration` raises `ModuleNotFoundError` on import. Do NOT route the lane rename through `migrate-layout`. Instead: (a) reach the rename via the ALREADY-SHIPPED install/update flow - the scaffolder already calls `migrate_local_lanes_to_untracked` (engine.py:4348), so with E-02's fixes `aw install .` on an existing repo now correctly renames+moves; AND (b) add a tiny dedicated verb `aw normalize-lanes` (cli.py, no `tools.` import) whose handler calls `engine.migrate_local_lanes_to_untracked(repo_root, {})` and reports the renamed lanes, so a user can fix a repo without a full reinstall. (This IPD does NOT fix the broader `migrate-layout`/`tools.`-not-shipped defect - that is recorded as PR-003/backlog and is out of scope here; it only ensures the LANE rename has a working installed entry point.)
  - Depends on: E-01,E-02
  - Expected outcome: in a clean pip-installed repo (built wheel), `aw normalize-lanes` renames a populated `local/` lane to `untracked/` with contents intact and is a no-op on re-run; `aw install .` on that repo does the same via the scaffold path; neither imports `tools`.
  - Execution state: pending

### Task group 3: apply to this repo + tests (incl. an INSTALLED-WHEEL test)

- [ ] E-04 (a) Run the rename on THIS repo via `aw normalize-lanes` (or `engine.migrate_local_lanes_to_untracked(Path('.'), {})`) so `find . -type d -iname 'local' -not -path '*/node_modules/*'` returns NOTHING under `.aw/records/` and `.agents/`, each comms/prompts base carries a `.gitignore` with `untracked/`, and moved ack/inbox/sent contents are intact (these lanes are untracked - a working-tree change, not a commit of lane contents). (b) Add `tests/test_untracked_lane_both_layouts.py` (`UntrackedBothLayoutsTests`): a tmp fixture with populated `local/` (incl. a NESTED `local/acks/x.json`) under `.aw/records/{comms,prompts}` and `.agents/{comms,prompts}` -> after the migration ALL four are `untracked/`, the nested file is at `untracked/acks/x.json` (PR-002 regression guard), each base has a `.gitignore` ignoring `untracked/`, and a second run is a no-op. (c) Add an INSTALLED-WHEEL validation (a subprocess test OR a documented manual V step with pasted output): build the wheel, `pip install` into a throwaway venv+repo, create a populated `local/acks/x.json`, run `aw normalize-lanes`, and assert the lane is renamed + content moved + no `tools` import error. Run the FULL serial suite and paste the tail; keep `tests/test_untracked_lane_migration.py` green (old dirs-scoped call is a subset).
  - Depends on: E-01,E-02,E-03
  - Expected outcome: this repo has no `local/` lane left; the new test (incl. the nested-file guard) passes; the installed-wheel path is demonstrated (pasted evidence); the old lane test still passes; full serial suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `.agents/` is fully untracked (0 tracked files) - stale post-migration litter; canonical is `.aw/records/`. Both trees currently hold a `local/` lane.
- `migrate_local_lanes_to_untracked` (engine.py) currently takes one `dirs` (active layout only), does not touch the nested `.gitignore`, and its shallow merge STRANDS nested files (PR-002).
- `aw migrate-layout` is NOT a usable retroactive path when installed (PR-001: `tools.awphysical` unshipped -> `ModuleNotFoundError`). The install/update scaffold flow and a new `tools`-free `aw normalize-lanes` verb are the working entry points.
- The comms/prompts nested-gitignore templates already emit `untracked/` (awuntracked-01); the gap is rewriting an EXISTING `local/` gitignore line and creating the missing legacy one.
- node_modules `*/locales` dirs are unrelated (not `local/` lanes); the find filter must exclude `node_modules`.

## Findings

awuntracked-01 was correct in template but inert/broken in practice. Proven in an installed wheel (Step a):

- PR-001 (HIGH, IN-SCOPE): `aw migrate-layout` crashes when pip-installed (`ModuleNotFoundError: No module named 'tools'`; cli.py:4061, layout_migration.py:30 import the unshipped `tools.awphysical`). Consequence: routing the retroactive rename through it (original E-03) would deliver it to a dead path in every downstream repo. Decision: FIXED for THIS scope by not using migrate-layout - added a `tools`-free `aw normalize-lanes` verb + rely on the install/scaffold path. The broader "migrate-layout is dead installed" defect is recorded as PR-003 (backlog, out of scope).
- PR-002 (HIGH, IN-SCOPE): the migration's shallow merge strands nested files - a reinstall left `local/acks/x.json` in place because empty `untracked/acks/` was mkdir'd first. Decision: FIXED - recursive merge + scaffold-order fix (E-02) + a nested-file regression guard (E-04).
- PR-003 (HIGH, OVER-SCOPE -> deferred to backlog): `agent_workflows.layout_migration` fails at import when installed (module-level `tools.` import), breaking `aw migrate-layout` and the install-time migration entirely. Not fixable within this lane-rename IPD without expanding scope to packaging; file a backlog item. Consequence if unresolved: `aw migrate-layout` remains unusable for downstream repos (but lane renaming no longer depends on it).

## Proposed changes (ordered, validatable)

1. Generalize the migration to both layouts.
2. Rewrite/create the nested `untracked/` gitignore; fix scaffold ordering.
3. Invoke it from `aw migrate-layout` (retroactive).
4. Apply to this repo + tests.

## Deferred / out of scope (with reason)

- Removing the stale `.agents/` litter tree entirely: deferred to backlog wxz7gg; this IPD only normalizes the lane name + gitignore wherever the tree exists.
- PR-003 (the broader `aw migrate-layout` / install-time migration being dead when pip-installed, because `agent_workflows.layout_migration` module-level-imports the unshipped `tools.awphysical`): OVER-SCOPE for a lane-rename IPD; requires a packaging/refactor decision (ship `tools.awphysical` inside the package, or inline the inventory it needs). Filed as backlog revnjq (awpackaging). This IPD deliberately avoids that path so the lane rename ships on a working entry point.

## Scope check

- Over-scope: PR-003 removed from scope (filed to backlog); this IPD does not touch migrate-layout's `tools.` dependency.
- Under-scope: does not delete `.agents/` (wxz7gg) and does not fix migrate-layout-when-installed (PR-003 backlog).

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
  - Required evidence: PR-002 regression - a fixture with a NESTED `local/acks/x.json` AND a pre-existing empty `untracked/acks/` -> after the migration the file is at `untracked/acks/x.json` (not stranded); each migrated base has a sibling `.gitignore` containing `untracked/` and no bare `local/`; scaffold ordering produces a clean rename. Shown by the new test.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: `aw normalize-lanes` (the new `tools`-free verb) on a fixture renames all present `local/` lanes to `untracked/`, reports them, is a no-op on re-run, and imports no `tools`; `aw install .` on the same repo does likewise via the scaffold path. NOT routed through `aw migrate-layout` (PR-001).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: (i) `find . -type d -iname 'local' -not -path '*/node_modules/*'` prints nothing under `.aw/records/` and `.agents/` in THIS repo + the four `.gitignore`s contain `untracked/`; (ii) `python3 -m pytest tests/test_untracked_lane_both_layouts.py tests/test_untracked_lane_migration.py -p no:xdist -q` green; (iii) INSTALLED-WHEEL proof - build wheel, pip install into a throwaway venv+repo, seed `local/acks/x.json`, run `aw normalize-lanes`, and paste output showing the lane renamed + `untracked/acks/x.json` present + no `ModuleNotFoundError`; (iv) full serial suite tail pasted.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution contract: commit only files changed by this plan, path-scoped, never push. The four lane renames in this repo are working-tree moves of UNTRACKED content (not committed). Run the full serial suite and paste the actual runner output as V evidence. On completion, lint `--phase pre-transition` while still approved, then flip Status to executed, add an executed workflow-history line, `git mv` to `.aw/records/plans/executed/`, and lint `--phase post-transition`. Do not mark executed until every V item is verified with concrete evidence.
