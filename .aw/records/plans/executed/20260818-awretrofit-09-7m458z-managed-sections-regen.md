# IPD: Regenerate self-install managed-sections.json to .aw/system keys (via aw install)

- Date: 2026-08-18
- Kind: child
- Concern: Release-review 20260817-153418 finding S5-K01 (split out of Order 05, 2026-08-17): the self-install manifest `.aw/system/managed-sections.json` is keyed entirely on legacy `.agents/workflows/*` (150 keys, 0 `.aw/`) - it was `git mv`'d into `.aw/system/` in the Order-11 migration without rekeying. On the next `aw install`/update ON THIS repo, the installer may treat every `.agents/workflows/*` entry as a vanished managed file, disturbing prune/diff.
- Scope: Regenerate `.aw/system/managed-sections.json` so its keys are `.aw/system/workflows/...`, via the manifest machinery / a controlled `aw install .` self-update (NOT a hand-edit). Verify install/update prune/diff behaves + the rekeyed manifest stays sanitize-clean. This is a self-install-only concern (running `aw install` ON this framework repo), NOT a shipped-artifact defect. OUT: prose/dead-code (Order 05, done).
- Status: executed
- Set: awretrofit
- Order: 9
- Highest E allocated: 02
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 7m458z

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): split out of Order 05 (carries finding K01 + the sanitize-after-regen check PR-002). Ready for /plan-review.
- 2026-08-18 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE (no revisions). Structural preflight conforming. Verified: managed-sections.json still 150 legacy `.agents/workflows/*` keys, 0 `.aw/`; no standalone manifest-rebuild function exists, so the full `aw install .` regeneration path (with OQ-01's commit-only-managed-sections.json scoping) is correct. E-01/E-02 sound; OQ-01 resolved. No findings, no open questions. GO - PENDING HUMAN APPROVAL.
- 2026-08-18 BLOCKED (opencode Opus 4.8): approved + attempted, but `aw install .` FAILS before reaching the manifest - `ensure_workflow_artifacts_readme` (engine.py:4082) tries to `git add workflow-artifacts/README.md` which is gitignored ("paths are ignored... Use -f"). It also regenerates 42 stale `.claude/commands/*` (+ `.opencode/commands/*`) shims still pointing at `.agents/workflows/` and creates `.aw/config/project.json` - beyond this Order's manifest scope. Partial install reset cleanly (manifest still 150/0, nothing committed). This Order is BLOCKED on a new Order 10 (fix the install `git add` gitignore bug + regenerate the stale host shims); once `aw install .` runs cleanly, the manifest rekey follows. Reverted Status to `reviewed` (needs re-approval after Order 10).
- 2026-08-18 UNBLOCKED + FINDING (opencode Opus 4.8): Order 10 executed (commit 8ab840d) - `aw install .` now completes. BUT executing it revealed the E-01 assumption is WRONG: `aw install .` ACCUMULATES manifest keys - it ADDS the current `.aw/system/*` keys but does NOT PRUNE the stale `.agents/workflows/*` keys (observed 150 legacy + 150 aw = 346 after a full install). So a bare `aw install .` does NOT reach the "0 legacy keys" goal; E-01 needs a purge/rebuild step (drop keys whose path no longer exists in the tree, or rebuild the manifest fresh from the installed `.aw/system/` members), not just `aw install .`. This Order needs a re-plan-review of E-01 with that mechanism before re-approval.
- 2026-08-18 REWORKED (opencode Opus 4.8): rewrote E-01 to the FRESH-REBUILD mechanism (DELETE the manifest first, then `aw install .` rebuilds it empty->current-only, since the install records every member it writes). Traced the root cause to `install_into_repo` load+append with no stale-key prune (engine.py:4405); confirmed a fresh rebuild captures all three entry classes (file/shim/section). Added finding K01b + convention notes. Re-review next; Status remains `to-review` (needs a fresh /plan-review + human approval).
- 2026-08-18 /plan-review [re-review after rework] (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE (no further revisions). Verified the reworked mechanism against real code (empty-load, record-all). GO - PENDING HUMAN APPROVAL.
- 2026-08-18 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): human approved. E-01: deleted managed-sections.json + `aw install .` rebuilt it fresh -> 0 legacy `.agents/workflows/*` keys (196 entries: 150 .aw/system file + 44 shim + 2 section); committed 6115148 (ONLY managed-sections.json, path-scoped: soft-reset the installer's broad auto-commit, dropped the redundant backlog/roadmaps .gitkeep + project.json side-effects). E-02: sanitize clean, attention valid, full serial suite 1011 passed / 1 skipped; repeat installs byte-stable (no accumulation). V-01/V-02 verified. pre-transition lint conforming; moved pending -> executed/.

## Goal

Rekey the self-install manifest so a re-install/update ON this framework repo behaves correctly (no
spurious vanished-managed-file prune), by regenerating it through the manifest machinery rather than
hand-editing 150 stale keys.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: regenerate the manifest

- [x] E-01 Rebuild `.aw/system/managed-sections.json` FRESH so it contains ONLY current keys, not the 150 stale `.agents/workflows/*`. **REWORKED (Order-10 finding): a bare `aw install .` does NOT work - `install_into_repo` LOADS the existing manifest (engine.py:4405) and RECORDS what it writes but never PRUNES stale keys, so it ACCUMULATES (observed 150 legacy + 150 aw = 346).** The correct mechanism is a FRESH rebuild: DELETE `.aw/system/managed-sections.json` first, then run `aw install .` - `manifest_mod.load()` on an absent path returns an empty Manifest, and the install records every member it writes (files at engine.py:1585, sections at :1371), so the rebuilt manifest is complete and current-only. The rebuilt manifest holds all three entry classes (150 `file` bundle members + 44 `shim` .claude/.opencode + 2 `section` for `.gitignore#aw:untracked` and `AGENTS.md#aw:pointer`) keyed to `.aw/system/*` / the real host-adapter paths. Order 10 already fixed the install so it completes on this repo. Handle the install's other outputs (shims already regenerated by Order 10 = no-op; do NOT let it re-commit - reset any auto-commit and commit ONLY managed-sections.json path-scoped, verifying nothing else changed).
  - Depends on: none
  - Expected outcome: `grep -c '\.agents/workflows' .aw/system/managed-sections.json` -> 0; the manifest keys are the current `.aw/system/*` + shim + section set (~196 entries, no legacy `file` keys); a second `aw install .` is a clean no-op (no accumulation, no spurious prune).
  - Execution state: performed

### Task group 2: verify

- [x] E-02 Verify: the rekeyed manifest stays `aw sanitize --agent` clean (it holds this repo's file hashes; PR-002), `aw attention --check` valid, and the full serial suite unaffected (>= 1004 passed / 1 skipped).
  - Depends on: E-01
  - Expected outcome: sanitize + attention clean; suite unchanged.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- `managed-sections.json` is a GENERATED manifest (manifest.py; populated during `install_all` keyed by each file's install `relative_posix`), NOT hand-maintained; regenerate via the machinery.
- There is no standalone "rebuild from tree" function; regeneration is a full `aw install .`.
- CRITICAL (Order-10 finding): `install_into_repo` LOADS the existing manifest (engine.py:4405) and only RECORDS what it writes - it does NOT prune stale keys. So a bare `aw install .` ACCUMULATES (150 legacy + 150 aw). The fix is to DELETE the manifest FIRST so the install rebuilds it fresh (empty-load -> records only current members). `aw install` records `file`/`shim` (engine.py:1585) + `section` (:1371) entries, so a fresh rebuild is complete.
- Order 10 fixed the install to complete on this repo (it previously aborted on the gitignored workflow-artifacts README); the shims are already regenerated, so this Order's install run should be a no-op for them.

## Findings

| id | area | evidence | issue |
|---|---|---|---|
| K01 | managed-sections.json | 150 `.agents/workflows/*` keys, 0 `.aw/` (git mv'd in Order 11 without rekey) | self-install prune/diff churn on re-install |
| K01b | install accumulates | `install_into_repo` load+append (engine.py:4405), no stale-key prune | a bare `aw install .` yields 150+150=346, not a rekey; E-01 must DELETE the manifest first for a fresh rebuild |

## Proposed changes (ordered, validatable)

1. E-01 regenerate the manifest via `aw install .` (path-scoped commit of managed-sections.json). 2. E-02 verify sanitize/attention/suite.

## Deferred / out of scope (with reason)

- Prose/dead-code (Order 05, done). Any shipped-artifact change (the manifest is self-install-only).

## Scope check

- Over-scope: none - a single manifest regen; commit only managed-sections.json unless a full install legitimately updates other already-current files.
- Under-scope: none - K01 is the whole concern.

## Required tests / validation

- `grep -c '.agents/workflows' .aw/system/managed-sections.json` -> 0; a re-install/update dry-run is a clean no-op.
- `aw sanitize --agent` clean on the rekeyed manifest; `aw attention --check` valid; full serial suite >= 1004 passed / 1 skipped.

## Spec / documentation sync

- None; self-install manifest only. No spec status change.

## Open questions

### OQ-01: If `aw install .` touches files beyond managed-sections.json, commit them or keep it minimal?

- Blocking: no
- Status: resolved
- Owner: opencode Opus 4.8
- Resolution or deferral rationale: Commit ONLY `managed-sections.json` path-scoped. If the self-install
  legitimately updates other files (shims/AGENTS.md), verify each is a correct no-op/already-current and
  either leave it unstaged or handle it in a separate, clearly-labeled commit - never bundle an
  unexplained broad rewrite into this manifest-regen Order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: `grep -c '.agents/workflows' .aw/system/managed-sections.json` -> 0 (keys now `.aw/system/...`); a re-install/update dry-run reports no spurious vanished-managed-file prune. Paste.
  - Observed evidence: Deleted the manifest (was 196 entries: 150 legacy `.agents/workflows/*` file keys + 44 shim + 2 section, 0 aw), then `aw install .` rebuilt it fresh -> 196 entries: 150 `.aw/system/*` file + 44 `.claude/.opencode` shim + 2 section, **0 legacy** (`grep -c '"\.agents/workflows' -> 0`). Repeat installs are STABLE: the 2nd install re-emitted the same content (the one-time rekey diff), the 3rd committed nothing new (byte-identical) - no accumulation, no spurious prune. Committed ONLY managed-sections.json (soft-reset the installer's broad auto-commit; dropped the redundant backlog/roadmaps `.gitkeep` + `.aw/config/project.json` side-effects; shims already current from Order 10).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: `aw sanitize --agent` clean on the rekeyed manifest; `aw attention --check` valid; full serial suite >= 1004 passed / 1 skipped. Paste.
  - Observed evidence: `aw sanitize --agent` clean on the rekeyed manifest (PR-002: it holds this repo's file hashes only, no home-path/identifier leak). `aw attention --check: the view is valid.` Full serial suite: `1011 passed, 1 skipped` (unchanged - manifest is data, no behavioral impact).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The executor
regenerates the manifest via the machinery, pastes evidence (the 0-legacy-keys grep, the no-op
re-install dry-run, sanitize/attention/suite), commits ONLY `.aw/system/managed-sections.json`
path-scoped (per OQ-01), never pushes, runs `aw ipd lint --phase pre-transition` + the full suite, and
the orchestrator owns the move to `executed/`. LOW-MEDIUM risk (self-install path) - the manifest is
self-install-only and the regen is verified by a clean no-op re-install.
