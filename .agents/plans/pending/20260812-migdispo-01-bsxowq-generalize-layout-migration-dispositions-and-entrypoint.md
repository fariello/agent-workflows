# IPD: Generalize layout-migration dispositions and add a reusable post-install migration entrypoint

- Date: 2026-08-12
- Kind: child
- Concern: The awphysical layout-migration tooling resolves the clean record/system/state classes, but its disposition rules do NOT cover the infrastructure files that EVERY installed agent-workflows repo carries (the `.agents/README.md` layout doc, the tracked leak-sanitizer allowlist config, the per-repo self-install manifest, and gitignored adapter dependency trees like `.opencode/node_modules`). As a result the migration inventory fails closed with `unknown-owner` on real installs, and each repo would have to rediscover the same dispositions by hand. (The user-facing "migrate my repo" ENTRYPOINT originally in scope here is now delivered elsewhere; see the rescope note below.)
- Scope: Disposition rules in `tools/awphysical/aw_layout_inventory.py` (`_legacy_class`, `classify_item`, `build_migration_map`, and gitignore-aware item enumeration); canonical reader-path resolution for the manifest and the leak-allowlist, which spans MORE than the two constants: `agent_workflows/manifest.py` (`DEFAULT_MANIFEST_RELPATH` + every consumer) and its consumers in `agent_workflows/engine.py` (the three `manifest_mod.DEFAULT_MANIFEST_RELPATH` read sites at ~3314/3432/4100); `agent_workflows/leak_sanitizer.py` (`REPO_ALLOWLIST_REL` used at ~210/219/340 + message strings) and its re-export in `agent_workflows/local_leaks.py`; the message string in `agent_workflows/cli.py` (~2698). and focused tests. NOT the live migration of any specific repo (that is Order 11 for this repo), and NOT the user-facing migration entrypoint (rescoped out; see below).
- Status: executed
- Highest E allocated: 04
- Author: opencode Opus 4.8
- Id: bsxowq
- Set: migdispo (generalize layout-migration dispositions + reusable entrypoint)
- Order: 1


## Workflow history

- 2026-08-12 draft (opencode Opus 4.8): created as a follow-up to awphysical Order 11 (self-migration). Order 11 Stage 1 surfaced that the migration disposition rules are incomplete for infrastructure files every install carries; this plan generalizes the rules + reader-path canonicalization + a reusable entrypoint so other repos do not rediscover the same dispositions. See the decision record `.agents/docs/walkthroughs/20260812-1200-01-order11-self-migration-decision-record-walkthrough.md`.
- 2026-08-12 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005. Verified every material claim from repository evidence. Widened Scope + E-04 to include the three `engine.py` manifest consumers (~3314/3432/4100) and the `local_leaks.py` re-export the original omitted (PR-001), and required a resolver rather than a bare `repo_root / CONST` string since a plain constant cannot express legacy fallback (PR-002). Sharpened E-02 to reuse the existing `git_sets` `ignored` set and prune ignored dirs (no gitignore reimplementation in `_walk`; avoid hashing node_modules) (PR-003). Made E-05 explicitly a distinctly-named `migrate-layout` workflow that must not shadow the existing `migrate` planning workflow, named to fit the future `/aw` command family (PR-004); OQ-01 resolved with the human maintainer (workflow, no standalone prompt; the `/aw` command-family redesign backlogged in TODO.md as a separate follow-up). Extended V-04/V-05 + Required tests to cover the added call sites and the workflow's non-collision. Structural lint conforming (author + review-finalize). Status to-review -> reviewed. Readiness: GO - PENDING HUMAN APPROVAL.
- 2026-08-12 approved (human maintainer via chat, recorded by opencode Opus 4.8): cleared to execute. Status reviewed -> approved.
- 2026-08-13 rescope during execution (opencode Opus 4.8, human maintainer): E-02 and E-03 executed and committed (f00e7eb: gitignore-aware inventory + infra-file dispositions, with tests). Then the `/aw` namespace research was adopted (research set `awnamespace`, deciding doc id 2bodwq): the future user-facing migration entrypoint is a single `/aw` dispatcher fed by one host-neutral verb registry, NOT a standalone `migrate-layout` workflow. Former E-05 (+ V-05) REMOVED as the wrong shape; the entrypoint is delivered as the `migrate` verb of the `/aw` dispatcher in the separate `/aw` work (TODO.md). Highest E allocated 05 -> 04. OQ-01 marked moot. Plan rescoped to the host-neutral migration TOOLING (E-02/E-03/E-04). E-04 remains to execute.
- 2026-08-13 executed (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): E-04 executed and committed (962f9d1: manifest + leak-allowlist path resolvers with legacy fallback, routed through manifest.py + engine.py's 3 consumers + leak_sanitizer.py's 2 loaders/1 write + local_leaks re-export; message strings updated; installer/cli tests updated for the new `.aw/system` manifest create-default). All V-02/V-03/V-04 verified with concrete output + a mutation-probe of the legacy fallback (RED->GREEN). Full parallel suite `pytest -n 12` exit 0; pre-transition ipd lint conforming. Status approved -> executed; Approval line removed; moved pending/ -> executed/.

## Goal

Make the layout migration resolve, automatically and identically for every installed repo, the infrastructure files that awphysical Order 11 had to disposition by hand (layout README, tracked leak-allowlist config, per-repo self-install manifest, gitignored adapter dependency trees), so no repo repeats the by-hand analysis. (The user-facing migration entrypoint is delivered as the `migrate` verb of the future `/aw` dispatcher, per the adopted `/aw` namespace research; see the rescope note.)

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Generalize disposition rules in the inventory/map tooling

- [x] E-02 Make the inventory skip gitignored subtrees (at minimum `node_modules`) so it never enumerates dependency/runtime noise under adapter roots. Note (verified): `git_sets()` (aw_layout_inventory.py:84) ALREADY computes the `ignored` set via `git ls-files --others --ignored --exclude-standard`, and the item loop already tags items `"ignored"` via `_git_state` (aw_layout_inventory.py:390/445). Do NOT reimplement gitignore inside the context-free `_walk` path-walker; instead thread the existing `ignored` set into enumeration (prune ignored directories so their subtrees are not descended, e.g. via `os.walk` `dirnames` pruning, so `node_modules`'s thousands of files are never `sha256`-hashed) and skip ignored items. Preserve current behavior for tracked and untracked-but-not-ignored content.
  - Depends on: none
  - Expected outcome: inventorying a repo with `.opencode/node_modules` (gitignored) yields zero items for that tree AND does not hash its files; a non-ignored file under the same root is still inventoried.
  - Execution state: performed

- [x] E-03 Extend `_legacy_class`/`classify_item`/`build_migration_map` with explicit dispositions for the infrastructure classes every install carries, matching the awphysical Order 11 decisions: the layout README (`.agents/README.md` -> regenerate as `.aw/README.md`, doc class), the tracked leak-allowlist + example (`.agents/local-leaks-allowlist.toml`, `.agents/local-leaks-hints.json.example` -> `.aw/config/`, config class), and the per-repo self-install manifest (`.agents/agent-workflows/managed-sections.json` + its README -> `.aw/system/`, system class). No `unknown-owner` for these on a standard install.
  - Depends on: none
  - Expected outcome: an inventory over a synthetic standard-install fixture resolves to `valid: True` with each infrastructure file assigned its decided destination and class; a genuinely unknown stray file still fails closed as `unknown-owner`.
  - Execution state: performed

### Task group 2: Canonicalize the reader paths once for all repos

- [x] E-04 Canonicalize manifest + leak-allowlist reader paths to the `.aw/` locations with bounded legacy fallback. IMPORTANT (verified): the current values are PLAIN relative-path strings joined at each call site as `repo_root / CONST`, which CANNOT express "prefer .aw, else legacy" on their own. So introduce a resolver (a function that returns the existing `.aw/` path if present, else the legacy path, else the `.aw/` path as the create-default) and route ALL read sites through it: for the manifest, `manifest.py` (define the resolver + keep `DEFAULT_MANIFEST_RELPATH` as the create-default) AND its three consumers in `engine.py` (~3314/3432/4100 currently do `repo_root / DEFAULT_MANIFEST_RELPATH`); for the allowlist, `leak_sanitizer.py` (`REPO_ALLOWLIST_REL` sites ~210/219/340) AND the `local_leaks.py` re-export. Writes/creates target the `.aw/` location; reads fall back to legacy so un-migrated repos keep working. Update the user-facing message strings (`leak_sanitizer.py` ~148/320/868, `cli.py` ~2698) to the new path.
  - Depends on: none
  - Expected outcome: on a migrated repo the manifest/allowlist resolve at the `.aw/` locations; on an un-migrated repo they still resolve at the legacy paths; the sanitizer, the installer, and every `engine.py` manifest consumer behave identically before and after migration; the `local_leaks.py` public re-export still resolves.
  - Execution state: performed

### Task group 3: (superseded) user-facing migration entrypoint

The reusable user-facing "migrate my repo" entrypoint originally planned here (a standalone
`migrate-layout` workflow) is SUPERSEDED by the consolidated `/aw` namespace research
(`.agents/docs/research/aw-namespace-research/aw-namespace-consolidated-report.md`, 2026-08-13),
which decides the future entrypoint is a SINGLE `/aw` dispatcher fed by one host-neutral verb
registry (where `migrate` is one verb), NOT a standalone per-workflow shim. Building a standalone
`migrate-layout` workflow now would be the wrong shape and would have to be torn out and re-folded
into the dispatcher. The migration entrypoint is therefore delivered as the `migrate` verb of the
`/aw` dispatcher in the separate `/aw` command-family work (backlogged in TODO.md). This plan is
rescoped to the host-neutral migration TOOLING (E-02/E-03/E-04) only. See the Deferred section and
the 2026-08-13 workflow-history entry.

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
   (The reusable user-facing migration entrypoint originally listed here is rescoped out; see Deferred.)

## Deferred / out of scope (with reason)

- The live migration of THIS repo: owned by awphysical Order 11 (uses these dispositions).
- The live migration of any OTHER specific repo: performed by the end user via the future `/aw migrate` entrypoint.
- The repo-local-but-untracked `.aw/records` backend variant: separate backlog item (its own IPD).
- The user-facing migration ENTRYPOINT (former E-05): RESCOPED OUT 2026-08-13. The adopted `/aw` namespace research (`.agents/docs/research/20260813-awnamespace-04-2bodwq-...reconciliation-report.md`, id 2bodwq, outcome adopted) decides the future entrypoint is a SINGLE `/aw` dispatcher fed by one host-neutral verb registry (with `migrate` as one verb), NOT a standalone per-workflow shim. Building a standalone `migrate-layout` workflow now would be the wrong shape and would have to be re-folded into the dispatcher, so the migration entrypoint is delivered as the `migrate` verb of the `/aw` dispatcher in the separate `/aw` command-family work.
- The `/aw <verb>` command-family redesign itself (single `/aw` dispatcher + verb registry; move `/setup-repo`, `/assess`, etc. under it; per-host adapters per the awnamespace research; back-compat aliases): a separate follow-up (backlogged in TODO.md). This plan does not build it.

## Scope check

- Over-scope: none - this generalizes existing migration tooling; it does not redesign the physical model, build the `/aw` command family, or perform a migration.
- Under-scope: gitignore-aware inventory, infrastructure-file dispositions, and reader-path canonicalization with legacy fallback are all included. The user-facing entrypoint is intentionally delivered by the separate `/aw` work (see Deferred), not missing.

## Required tests / validation

- New inventory/classifier tests over a synthetic standard-install fixture: infrastructure files resolve to their decided classes/destinations; a stray file still fails closed; a gitignored `node_modules` subtree is excluded. (Done in E-02/E-03: `tools/awphysical/test_awphysical_tools.py::InventoryTests::test_e02*/test_e03*`.)
- Reader-path tests: manifest/allowlist resolve at `.aw/` locations on a migrated fixture and at legacy paths on an un-migrated fixture, INCLUDING through the `engine.py` manifest consumers and the `local_leaks.py` re-export (not just the leak_sanitizer entry).
- `python3 -m unittest discover -s tests -t .` (or `pytest -n auto`) green.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`.

## Spec / documentation sync

- Update the controlling physical spec / migration docs to reference the generalized dispositions, if the reviewer finds a gap. Keep the Order 11 decision-record walkthrough cross-linked. The user-facing entrypoint doc is owned by the separate `/aw` command-family work.

## Open questions

### OQ-01: Entrypoint shape - workflow vs prompt vs both

- Blocking: no
- Superseding note (2026-08-13): OQ-01 is now MOOT for this plan - the entrypoint (former E-05) was rescoped OUT after the `/aw` namespace research was adopted (deciding doc id 2bodwq). The entrypoint is delivered as the `migrate` verb of the future `/aw` dispatcher, not by this plan. The prior interactive resolution (a distinctly-named workflow) is retained below as historical record but no longer governs this plan's scope.
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-12 (/plan-review, human maintainer): E-05 delivers ONE workflow for the layout migration (driving the `aw migrate-layout` CLI), named to slot into a FUTURE `/aw <verb>` command family (workflow id `migrate-layout`, distinct from the existing `migrate` PLANNING workflow). This plan does NOT build the `/aw` namespace or rename any existing workflow. The broader `/aw` command-family redesign (move `/setup-repo` -> `/aw setup`, `/assess` -> `/aw assess`, etc., with per-host slash-grammar verification and back-compat aliases) is a SEPARATE follow-up (see the backlog item recorded in `TODO.md`, filed by this review). A canonical standalone prompt is NOT required now.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-02 validates E-02
  - Required evidence: run the new inventory test over a fixture containing a gitignored `node_modules` subtree; show it is excluded and a non-ignored sibling is included; show RED when the gitignore skip is disabled (mutation probe).
  - Observed evidence: `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e02_inventory_prunes_gitignored_dependency_subtree` -> `Ran 1 test ... OK`. The test builds a fixture with a gitignored `.opencode/node_modules/somepkg/*.js` subtree plus a non-ignored `.opencode/commands/assess.md`, asserts NO `node_modules` item appears and `commands/assess.md` IS inventoried. Real-repo cross-check: `aw migrate-layout inventory --target-backend repository` went from 4784 items (3926 node_modules) to node_modules=0, `valid: True`. Implementation adds `_ignored_dirs()` (git ls-files --ignored --directory) and prunes those dirs in `_walk` (commit f00e7eb).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: run the classifier/map test over a synthetic standard-install fixture; show README/allowlist/manifest each resolve to the decided class+destination and inventory is `valid: True`; show a stray file still yields `unknown-owner` (RED-then-GREEN).
  - Observed evidence: `python3 -m unittest tools.awphysical.test_awphysical_tools.InventoryTests.test_e03_infrastructure_files_get_explicit_dispositions` -> `Ran 1 test ... OK`. Asserts (via build_migration_map): `README.md -> (doc, README.md)`, `local-leaks-allowlist.toml -> (config, config/local-leaks-allowlist.toml)`, `agent-workflows/managed-sections.json -> (system, system/managed-sections.json)` and inventory `valid: True`; and the falsifiable negative `classify_item("agents","stray-thing.xyz",...)["disposition"] == "block-unknown"` (a genuinely stray file still fails closed). Real-repo cross-check: the Order-11 inventory of this repo went `valid: False` (6 unknown-owner) -> `valid: True` (commit f00e7eb).
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: resolve manifest + allowlist on a migrated fixture (`.aw/` locations) and on an un-migrated fixture (legacy paths) THROUGH the same resolver the code uses; paste both. Exercise at least one `engine.py` manifest consumer (e.g. the read at ~3314) and the `local_leaks.py` `REPO_ALLOWLIST_REL` re-export against both fixtures to prove all call sites route through the resolver. Show a mutation that breaks the legacy fallback fails RED.
  - Observed evidence: `python3 -m pytest tests/test_manifest.py::ManifestPathResolverTests tests/test_leak_sanitizer.py::ConfigReconciliationTests::test_e04_allowlist_resolver_prefers_aw_config_falls_back_to_legacy tests/test_leak_sanitizer.py::ConfigReconciliationTests::test_e04_local_leaks_reexports_resolver` -> `6 passed`. Manifest resolver: create-default `.aw/system/managed-sections.json`; migrated-fixture resolves `.aw/system`; un-migrated-fixture resolves the legacy `.agents/agent-workflows/...`; new wins when both present. Allowlist resolver: same three cases, and `load_repo_allowlist(repo)` actually reads the legacy file via the resolver; `local_leaks` re-exports `REPO_ALLOWLIST_REL`, `LEGACY_REPO_ALLOWLIST_REL`, and `resolve_allowlist_path` (identity-checked). Engine consumers routed through `resolve_manifest_path` (uninstall inspect/remove + install load/save), validated by the full installer suite passing after the manifest create-default moved to `.aw/system` (installer/cli tests updated to the new location). Mutation probe: disabling the legacy branch in `resolve_manifest_path` makes `test_unmigrated_repo_falls_back_to_legacy` fail RED; restored -> GREEN. Real-repo cross-check: `resolve_allowlist_path(.)` returns this repo's legacy `.agents/local-leaks-allowlist.toml` and `check-local-leaks .` exits 0 (commit 962f9d1).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one coherent unit - generalize the migration dispositions the machinery already needs, canonicalize the reader paths those dispositions imply, and expose one reusable entrypoint that uses them.

Execution requires a GO `/plan-review` and explicit human approval. Scope fence: the inventory/classifier/map disposition rules, the two reader-path constants + their message strings, and the reusable entrypoint + focused tests only. Do not perform any repo's live migration, do not change the physical model, do not redesign the CLI. Paste actual outputs, commit only path-scoped files, never broad-stage, never push. Complete E/V evidence and pre-transition lint before moving this plan to `executed/`.
