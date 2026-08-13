# IPD: Generalize layout-migration dispositions and add a reusable post-install migration entrypoint

- Date: 2026-08-12
- Kind: child
- Concern: The awphysical layout-migration tooling resolves the clean record/system/state classes, but its disposition rules do NOT cover the infrastructure files that EVERY installed agent-workflows repo carries (the `.agents/README.md` layout doc, the tracked leak-sanitizer allowlist config, the per-repo self-install manifest, and gitignored adapter dependency trees like `.opencode/node_modules`). As a result the migration inventory fails closed with `unknown-owner` on real installs, and each repo would have to rediscover the same dispositions by hand. There is also no simple, documented one-off entrypoint an end user runs after install/update to migrate their own repo.
- Scope: Disposition rules in `tools/awphysical/aw_layout_inventory.py` (`_legacy_class`, `classify_item`, `build_migration_map`, and gitignore-aware item enumeration); canonical reader-path resolution for the manifest and the leak-allowlist, which spans MORE than the two constants: `agent_workflows/manifest.py` (`DEFAULT_MANIFEST_RELPATH` + every consumer) and its consumers in `agent_workflows/engine.py` (the three `manifest_mod.DEFAULT_MANIFEST_RELPATH` read sites at ~3314/3432/4100); `agent_workflows/leak_sanitizer.py` (`REPO_ALLOWLIST_REL` used at ~210/219/340 + message strings) and its re-export in `agent_workflows/local_leaks.py`; the message string in `agent_workflows/cli.py` (~2698). A reusable user-facing post-install/update migration entrypoint (a short workflow/prompt over the existing `aw migrate-layout` CLI); and focused tests. NOT the live migration of any specific repo (that is Order 11 for this repo, and the user-run entrypoint for others).
- Status: approved
- Highest E allocated: 05
- Author: opencode Opus 4.8
- Id: bsxowq
- Set: migdispo (generalize layout-migration dispositions + reusable entrypoint)
- Order: 1
- Approval: 2026-08-12 human maintainer (chat) - approved to execute after /plan-review (APPROVE WITH REVISIONS APPLIED); recorded by opencode Opus 4.8.

## Workflow history

- 2026-08-12 draft (opencode Opus 4.8): created as a follow-up to awphysical Order 11 (self-migration). Order 11 Stage 1 surfaced that the migration disposition rules are incomplete for infrastructure files every install carries; this plan generalizes the rules + reader-path canonicalization + a reusable entrypoint so other repos do not rediscover the same dispositions. See the decision record `.agents/docs/walkthroughs/20260812-1200-01-order11-self-migration-decision-record-walkthrough.md`.
- 2026-08-12 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Verified every material claim from repository evidence. Widened Scope + E-04 to include the three `engine.py` manifest consumers (~3314/3432/4100) and the `local_leaks.py` re-export the original omitted (PR-001), and required a resolver rather than a bare `repo_root / CONST` string since a plain constant cannot express legacy fallback (PR-002). Sharpened E-02 to reuse the existing `git_sets` `ignored` set and prune ignored dirs (no gitignore reimplementation in `_walk`; avoid hashing node_modules) (PR-003). Made E-05 explicitly a distinctly-named `migrate-layout` workflow that must not shadow the existing `migrate` planning workflow, named to fit the future `/aw` command family (PR-004); OQ-01 resolved with the human maintainer (workflow, no standalone prompt; the `/aw` command-family redesign backlogged in TODO.md as a separate follow-up). Extended V-04/V-05 + Required tests to cover the added call sites and the workflow's non-collision. Structural lint conforming (author + review-finalize). Status to-review -> reviewed. Readiness: GO - PENDING HUMAN APPROVAL.
- 2026-08-12 approved (human maintainer via chat, recorded by opencode Opus 4.8): cleared to execute. Status reviewed -> approved.

## Goal

Make the layout migration resolve, automatically and identically for every installed repo, the infrastructure files that awphysical Order 11 had to disposition by hand (layout README, tracked leak-allowlist config, per-repo self-install manifest, gitignored adapter dependency trees), and give end users a single documented "run this once after install/update" entrypoint to migrate their own repo, so no repo repeats the by-hand analysis.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Generalize disposition rules in the inventory/map tooling

- [ ] E-02 Make the inventory skip gitignored subtrees (at minimum `node_modules`) so it never enumerates dependency/runtime noise under adapter roots. Note (verified): `git_sets()` (aw_layout_inventory.py:84) ALREADY computes the `ignored` set via `git ls-files --others --ignored --exclude-standard`, and the item loop already tags items `"ignored"` via `_git_state` (aw_layout_inventory.py:390/445). Do NOT reimplement gitignore inside the context-free `_walk` path-walker; instead thread the existing `ignored` set into enumeration (prune ignored directories so their subtrees are not descended, e.g. via `os.walk` `dirnames` pruning, so `node_modules`'s thousands of files are never `sha256`-hashed) and skip ignored items. Preserve current behavior for tracked and untracked-but-not-ignored content.
  - Depends on: none
  - Expected outcome: inventorying a repo with `.opencode/node_modules` (gitignored) yields zero items for that tree AND does not hash its files; a non-ignored file under the same root is still inventoried.
  - Execution state: pending

- [ ] E-03 Extend `_legacy_class`/`classify_item`/`build_migration_map` with explicit dispositions for the infrastructure classes every install carries, matching the awphysical Order 11 decisions: the layout README (`.agents/README.md` -> regenerate as `.aw/README.md`, doc class), the tracked leak-allowlist + example (`.agents/local-leaks-allowlist.toml`, `.agents/local-leaks-hints.json.example` -> `.aw/config/`, config class), and the per-repo self-install manifest (`.agents/agent-workflows/managed-sections.json` + its README -> `.aw/system/`, system class). No `unknown-owner` for these on a standard install.
  - Depends on: none
  - Expected outcome: an inventory over a synthetic standard-install fixture resolves to `valid: True` with each infrastructure file assigned its decided destination and class; a genuinely unknown stray file still fails closed as `unknown-owner`.
  - Execution state: pending

### Task group 2: Canonicalize the reader paths once for all repos

- [ ] E-04 Canonicalize manifest + leak-allowlist reader paths to the `.aw/` locations with bounded legacy fallback. IMPORTANT (verified): the current values are PLAIN relative-path strings joined at each call site as `repo_root / CONST`, which CANNOT express "prefer .aw, else legacy" on their own. So introduce a resolver (a function that returns the existing `.aw/` path if present, else the legacy path, else the `.aw/` path as the create-default) and route ALL read sites through it: for the manifest, `manifest.py` (define the resolver + keep `DEFAULT_MANIFEST_RELPATH` as the create-default) AND its three consumers in `engine.py` (~3314/3432/4100 currently do `repo_root / DEFAULT_MANIFEST_RELPATH`); for the allowlist, `leak_sanitizer.py` (`REPO_ALLOWLIST_REL` sites ~210/219/340) AND the `local_leaks.py` re-export. Writes/creates target the `.aw/` location; reads fall back to legacy so un-migrated repos keep working. Update the user-facing message strings (`leak_sanitizer.py` ~148/320/868, `cli.py` ~2698) to the new path.
  - Depends on: none
  - Expected outcome: on a migrated repo the manifest/allowlist resolve at the `.aw/` locations; on an un-migrated repo they still resolve at the legacy paths; the sanitizer, the installer, and every `engine.py` manifest consumer behave identically before and after migration; the `local_leaks.py` public re-export still resolves.
  - Execution state: pending

### Task group 3: Reusable post-install/update migration entrypoint

- [ ] E-05 Add a reusable, documented one-off entrypoint an end user runs after install/update to migrate their own repo to the `.aw/` layout: ONE workflow (per OQ-01 resolution; no standalone prompt required) that drives the existing `aw migrate-layout` CLI through inventory -> review the disposition map -> rehearsal -> apply -> verify, with the human-gated confirmation and no-writer-window guidance made explicit. It must reuse the generalized dispositions from Task groups 1-2 (no per-repo rediscovery). NAMING (verified + resolved): a `migrate` workflow ALREADY exists at `.agents/workflows/migrate/migrate.md` and is a PLANNING workflow; the new workflow MUST use the distinct id `migrate-layout` (matching the CLI verb) and must not shadow, rename, or repurpose the existing `migrate` workflow. Follow the workflow-dir + shim conventions so it installs via the normal installer (becoming `.aw/system` content). Name it so it can later slot into the planned `/aw <verb>` command family WITHOUT another rename; building that `/aw` namespace and renaming existing workflows is explicitly OUT OF SCOPE here (separate follow-up; see TODO.md).
  - Depends on: none
  - Expected outcome: a user can follow one workflow (id `migrate-layout`, distinct from the existing `migrate` workflow) to migrate their repo end to end; the workflow references the generalized rules and the `aw migrate-layout` actions rather than restating repo-specific dispositions.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Disposition rules live in code (`aw_layout_inventory.py` `_legacy_class`/`classify_item`/`build_migration_map`); `migration-scenarios.json` is the crosswalk/acceptance catalog, not the rule source.
- `aw migrate-layout {inventory,plan,apply,status,resume,rollback,cleanup}` is the execution surface; the `migrate` workflow is a PLANNING workflow (produces an IPD, does not execute) and is a different thing from a layout-migration entrypoint.
- The new-layout code already reads the manifest at `<system_root>/managed-sections.json` (`project_layout.py`), so canonicalizing `DEFAULT_MANIFEST_RELPATH` is an alignment, not a redesign.
- The leak-allowlist reader path is centralized in one constant (`leak_sanitizer.py` `REPO_ALLOWLIST_REL`, used at ~:210/:219/:340) plus message strings; CI/pre-commit call the sanitizer rather than hardcoding the path.

## Findings

- awphysical Order 11 Stage 1 inventory over this repo returned `valid: False` with six `unknown-owner` items: `.agents/README.md`, `.agents/local-leaks-allowlist.toml`, `.agents/local-leaks-hints.json.example`, `.agents/agent-workflows/` (dir), `.agents/agent-workflows/README.md`, `.agents/agent-workflows/managed-sections.json`. Every standard install has these, so the gap is general, not repo-specific.
- The inventory also swept `.opencode/node_modules/` (3926 gitignored files) as `host-adapter-candidate` because `_walk` does not honor `.gitignore`.
- The decided dispositions (maintainer-confirmed) are recorded in the Order 11 decision-record walkthrough and are the source for the E-items in Task groups 1-2.
- Review verification (2026-08-12 /plan-review): confirmed against evidence - `_walk`:370 skips only `.git` (E-02 premise holds); `git_sets`:84/94 already computes the `ignored` set and `_git_state`:355 already tags items, so E-02 reuses existing data (PR-003). `manifest.py:41 DEFAULT_MANIFEST_RELPATH` has THREE additional consumers in `engine.py` (~3314/3432/4100) that join it as `repo_root / CONST`, and `leak_sanitizer.py REPO_ALLOWLIST_REL` (210/219/340) is re-exported by `local_leaks.py:23/46`; the original Scope named neither, so E-04/Scope were widened to include them and to require a resolver (not a bare string), because `repo_root / CONST` cannot express legacy fallback (PR-001, PR-002). CI/pre-commit/Makefile hardcode NEITHER path (they call the sanitizer), confirming the reader-update is centralized. A `migrate` PLANNING workflow already exists at `.agents/workflows/migrate/migrate.md`, so E-05's entrypoint must be distinctly named (PR-004).

## Proposed changes (ordered, validatable)

1. `_walk` honors `.gitignore` (skip gitignored subtrees / node_modules).
2. Classifier/map gain explicit infrastructure-file dispositions (README->doc/.aw, allowlist->config/.aw/config, manifest->system/.aw/system).
3. Reader-path constants canonicalized to the `.aw/` locations with legacy fallbacks; message strings updated.
4. A reusable post-install/update migration entrypoint (workflow/prompt) over `aw migrate-layout`.

## Deferred / out of scope (with reason)

- The live migration of THIS repo: owned by awphysical Order 11 (uses these dispositions).
- The live migration of any OTHER specific repo: performed by the end user via the new entrypoint.
- The repo-local-but-untracked `.aw/records` backend variant: separate backlog item (its own IPD).
- The `/aw <verb>` command-family redesign (a single `/aw` namespace; move `/setup-repo` -> `/aw setup`, `/assess` -> `/aw assess`, etc., with per-host slash-grammar verification and back-compat aliases): a separate follow-up (backlogged in TODO.md by the 2026-08-12 review). E-05 only names its workflow to fit that future scheme; it does not build it.

## Scope check

- Over-scope: none - this generalizes existing machinery and adds an entrypoint; it does not redesign the physical model or perform a migration.
- Under-scope: gitignore-aware inventory, infrastructure-file dispositions, reader-path canonicalization with legacy fallback, and the reusable entrypoint are all included.

## Required tests / validation

- New inventory/classifier tests over a synthetic standard-install fixture: infrastructure files resolve to their decided classes/destinations; a stray file still fails closed; a gitignored `node_modules` subtree is excluded.
- Reader-path tests: manifest/allowlist resolve at `.aw/` locations on a migrated fixture and at legacy paths on an un-migrated fixture, INCLUDING through the `engine.py` manifest consumers and the `local_leaks.py` re-export (not just the leak_sanitizer entry).
- `python3 -m unittest discover -s tests -t .` (or `pytest -n auto`) green.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`.

## Spec / documentation sync

- Update the controlling physical spec / migration docs to reference the generalized dispositions and the user entrypoint, if the reviewer finds a gap. Keep the Order 11 decision-record walkthrough cross-linked.

## Open questions

### OQ-01: Entrypoint shape - workflow vs prompt vs both

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-12 (/plan-review, human maintainer): E-05 delivers ONE workflow for the layout migration (driving the `aw migrate-layout` CLI), named to slot into a FUTURE `/aw <verb>` command family (workflow id `migrate-layout`, distinct from the existing `migrate` PLANNING workflow). This plan does NOT build the `/aw` namespace or rename any existing workflow. The broader `/aw` command-family redesign (move `/setup-repo` -> `/aw setup`, `/assess` -> `/aw assess`, etc., with per-host slash-grammar verification and back-compat aliases) is a SEPARATE follow-up (see the backlog item recorded in `TODO.md`, filed by this review). A canonical standalone prompt is NOT required now.

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
  - Required evidence: resolve manifest + allowlist on a migrated fixture (`.aw/` locations) and on an un-migrated fixture (legacy paths) THROUGH the same resolver the code uses; paste both. Exercise at least one `engine.py` manifest consumer (e.g. the read at ~3314) and the `local_leaks.py` `REPO_ALLOWLIST_REL` re-export against both fixtures to prove all call sites route through the resolver. Show a mutation that breaks the legacy fallback fails RED.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm the new `migrate-layout` workflow exists with a distinct id (does NOT shadow/rename the existing `migrate` workflow) and installs via the normal installer (shim present); then follow it against a throwaway repo (inventory -> plan -> rehearsal -> apply -> verify) and show it reaches a migrated, `valid` state using the generalized rules; paste the actual commands/output.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one coherent unit - generalize the migration dispositions the machinery already needs, canonicalize the reader paths those dispositions imply, and expose one reusable entrypoint that uses them.

Execution requires a GO `/plan-review` and explicit human approval. Scope fence: the inventory/classifier/map disposition rules, the two reader-path constants + their message strings, and the reusable entrypoint + focused tests only. Do not perform any repo's live migration, do not change the physical model, do not redesign the CLI. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
