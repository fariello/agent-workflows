# IPD: Generalize layout-migration dispositions and add a reusable post-install migration entrypoint

- Date: 2026-08-12
- Kind: child
- Concern: The awphysical layout-migration tooling resolves the clean record/system/state classes, but its disposition rules do NOT cover the infrastructure files that EVERY installed agent-workflows repo carries (the `.agents/README.md` layout doc, the tracked leak-sanitizer allowlist config, the per-repo self-install manifest, and gitignored adapter dependency trees like `.opencode/node_modules`). As a result the migration inventory fails closed with `unknown-owner` on real installs, and each repo would have to rediscover the same dispositions by hand. There is also no simple, documented one-off entrypoint an end user runs after install/update to migrate their own repo.
- Scope: Disposition rules in `tools/awphysical/aw_layout_inventory.py` (`_legacy_class`, `classify_item`, `build_migration_map`, `_walk` gitignore handling); canonical reader-path constants (`agent_workflows/manifest.py` `DEFAULT_MANIFEST_RELPATH`, `agent_workflows/leak_sanitizer.py` `REPO_ALLOWLIST_REL`); a reusable user-facing post-install/update migration entrypoint (a short workflow/prompt over the existing `aw migrate-layout` CLI); and focused tests. NOT the live migration of any specific repo (that is Order 11 for this repo, and the user-run entrypoint for others).
- Status: to-review
- Highest E allocated: 05
- Author: opencode Opus 4.8
- Id: bsxowq

## Workflow history

- 2026-08-12 draft (opencode Opus 4.8): created as a follow-up to awphysical Order 11 (self-migration). Order 11 Stage 1 surfaced that the migration disposition rules are incomplete for infrastructure files every install carries; this plan generalizes the rules + reader-path canonicalization + a reusable entrypoint so other repos do not rediscover the same dispositions. See the decision record `.agents/docs/walkthroughs/20260812-1200-01-order11-self-migration-decision-record-walkthrough.md`.

## Goal

Make the layout migration resolve, automatically and identically for every installed repo, the infrastructure files that awphysical Order 11 had to disposition by hand (layout README, tracked leak-allowlist config, per-repo self-install manifest, gitignored adapter dependency trees), and give end users a single documented "run this once after install/update" entrypoint to migrate their own repo, so no repo repeats the by-hand analysis.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Generalize disposition rules in the inventory/map tooling

- [ ] E-02 Make `aw_layout_inventory._walk` honor `.gitignore`: skip gitignored subtrees (at minimum `node_modules`) so the inventory never enumerates dependency/runtime noise under adapter roots. Preserve current behavior for tracked/untracked-but-not-ignored content.
  - Depends on: none
  - Expected outcome: inventorying a repo with `.opencode/node_modules` (gitignored) yields zero `host-adapter-candidate` items for that tree; a non-ignored file under the same root is still inventoried.
  - Execution state: pending

- [ ] E-03 Extend `_legacy_class`/`classify_item`/`build_migration_map` with explicit dispositions for the infrastructure classes every install carries, matching the awphysical Order 11 decisions: the layout README (`.agents/README.md` -> regenerate as `.aw/README.md`, doc class), the tracked leak-allowlist + example (`.agents/local-leaks-allowlist.toml`, `.agents/local-leaks-hints.json.example` -> `.aw/config/`, config class), and the per-repo self-install manifest (`.agents/agent-workflows/managed-sections.json` + its README -> `.aw/system/`, system class). No `unknown-owner` for these on a standard install.
  - Depends on: none
  - Expected outcome: an inventory over a synthetic standard-install fixture resolves to `valid: True` with each infrastructure file assigned its decided destination and class; a genuinely unknown stray file still fails closed as `unknown-owner`.
  - Execution state: pending

### Task group 2: Canonicalize the reader paths once for all repos

- [ ] E-04 Update the canonical reader-path constants so the new locations are the source of truth while retaining bounded legacy compatibility: `manifest.py` `DEFAULT_MANIFEST_RELPATH` resolves the manifest at the system root (`.aw/system/managed-sections.json`) with a legacy `.agents/agent-workflows/` fallback; `leak_sanitizer.py` `REPO_ALLOWLIST_REL` resolves `.aw/config/local-leaks-allowlist.toml` with a legacy `.agents/local-leaks-allowlist.toml` fallback. Update the user-facing message strings (`leak_sanitizer.py`, `cli.py`) to the new path. Do not break un-migrated repos (fallback reads).
  - Depends on: none
  - Expected outcome: on a migrated repo the manifest/allowlist resolve at the `.aw/` locations; on an un-migrated repo they still resolve at the legacy paths; the sanitizer and installer behave identically before and after migration.
  - Execution state: pending

### Task group 3: Reusable post-install/update migration entrypoint

- [ ] E-05 Add a reusable, documented one-off entrypoint that an end user runs after install/update to migrate their own repo to the `.aw/` layout: a short workflow (e.g. `/migrate-layout`) and/or a canonical prompt that drives the existing `aw migrate-layout` CLI through inventory -> review the disposition map -> rehearsal -> apply -> verify, with the human-gated confirmation and no-writer-window guidance made explicit. It must reuse the generalized dispositions from Task groups 1-2 (no per-repo rediscovery).
  - Depends on: none
  - Expected outcome: a user can follow one documented entrypoint to migrate their repo end to end; the entrypoint references the generalized rules and the `aw migrate-layout` actions rather than restating repo-specific dispositions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Disposition rules live in code (`aw_layout_inventory.py` `_legacy_class`/`classify_item`/`build_migration_map`); `migration-scenarios.json` is the crosswalk/acceptance catalog, not the rule source.
- `aw migrate-layout {inventory,plan,apply,status,resume,rollback,cleanup}` is the execution surface; the `migrate` workflow is a PLANNING workflow (produces an IPD, does not execute) and is a different thing from a layout-migration entrypoint.
- The new-layout code already reads the manifest at `<system_root>/managed-sections.json` (`project_layout.py`), so canonicalizing `DEFAULT_MANIFEST_RELPATH` is an alignment, not a redesign.
- The leak-allowlist reader path is centralized in one constant (`leak_sanitizer.py` `REPO_ALLOWLIST_REL`, used at ~:210/:219/:340) plus message strings; CI/pre-commit call the sanitizer rather than hardcoding the path.

## Findings

- awphysical Order 11 Stage 1 inventory over this repo returned `valid: False` with six `unknown-owner` items: `.agents/README.md`, `.agents/local-leaks-allowlist.toml`, `.agents/local-leaks-hints.json.example`, `.agents/agent-workflows/` (dir), `.agents/agent-workflows/README.md`, `.agents/agent-workflows/managed-sections.json`. Every standard install has these, so the gap is general, not repo-specific.
- The inventory also swept `.opencode/node_modules/` (3926 gitignored files) as `host-adapter-candidate` because `_walk` does not honor `.gitignore`.
- The decided dispositions (maintainer-confirmed) are recorded in the Order 11 decision-record walkthrough and are the source for E-NEW in Task groups 1-2.

## Proposed changes (ordered, validatable)

1. `_walk` honors `.gitignore` (skip gitignored subtrees / node_modules).
2. Classifier/map gain explicit infrastructure-file dispositions (README->doc/.aw, allowlist->config/.aw/config, manifest->system/.aw/system).
3. Reader-path constants canonicalized to the `.aw/` locations with legacy fallbacks; message strings updated.
4. A reusable post-install/update migration entrypoint (workflow/prompt) over `aw migrate-layout`.

## Deferred / out of scope (with reason)

- The live migration of THIS repo: owned by awphysical Order 11 (uses these dispositions).
- The live migration of any OTHER specific repo: performed by the end user via the new entrypoint.
- The repo-local-but-untracked `.aw/records` backend variant: separate backlog item (its own IPD).

## Scope check

- Over-scope: none - this generalizes existing machinery and adds an entrypoint; it does not redesign the physical model or perform a migration.
- Under-scope: gitignore-aware inventory, infrastructure-file dispositions, reader-path canonicalization with legacy fallback, and the reusable entrypoint are all included.

## Required tests / validation

- New inventory/classifier tests over a synthetic standard-install fixture: infrastructure files resolve to their decided classes/destinations; a stray file still fails closed; a gitignored `node_modules` subtree is excluded.
- Reader-path tests: manifest/allowlist resolve at `.aw/` locations on a migrated fixture and at legacy paths on an un-migrated fixture.
- `python3 -m unittest discover -s tests -t .` (or `pytest -n auto`) green.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`.

## Spec / documentation sync

- Update the controlling physical spec / migration docs to reference the generalized dispositions and the user entrypoint, if the reviewer finds a gap. Keep the Order 11 decision-record walkthrough cross-linked.

## Open questions

### OQ-01: Entrypoint shape - workflow vs prompt vs both

- Blocking: no
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: Decide during review whether the reusable post-install migration entrypoint is a `/migrate-layout` workflow, a canonical upload-ready prompt, or both. All three drive the same `aw migrate-layout` CLI; the choice is about delivery ergonomics.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-02 validates E-02
  - Required evidence: run the new inventory test over a fixture containing a gitignored `node_modules` subtree; show it is excluded and a non-ignored sibling is included; show RED when the gitignore skip is disabled (mutation probe).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: run the classifier/map test over a synthetic standard-install fixture; show README/allowlist/manifest each resolve to the decided class+destination and inventory is `valid: True`; show a stray file still yields `unknown-owner` (RED-then-GREEN).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: resolve manifest + allowlist on a migrated fixture (`.aw/` locations) and on an un-migrated fixture (legacy paths); paste both; show a mutation that breaks the legacy fallback fails RED.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: exercise the reusable entrypoint against a throwaway repo (inventory -> plan -> rehearsal -> apply -> verify) and show it reaches a migrated, `valid` state using the generalized rules; paste the actual commands/output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one coherent unit - generalize the migration dispositions the machinery already needs, canonicalize the reader paths those dispositions imply, and expose one reusable entrypoint that uses them.

Execution requires a GO `/plan-review` and explicit human approval. Scope fence: the inventory/classifier/map disposition rules, the two reader-path constants + their message strings, and the reusable entrypoint + focused tests only. Do not perform any repo's live migration, do not change the physical model, do not redesign the CLI. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
