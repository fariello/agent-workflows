# Walkthrough: Order 11 (agent-workflows self-migration) - decision record + execution plan

- Date: 2026-08-12
- Author: opencode Opus 4.8 (orchestrator), with the human maintainer
- Status: IN PROGRESS - Stage 1 (baseline + inventory) done; dispositions decided with the
  maintainer; rehearsal + real cutover NOT yet performed.
- Plan: `.agents/plans/pending/20260810-awphysical-11-g5zl1u-agent-workflows-source-repository-self-migration.md`
  (Status: approved, in pending/; the live migration is human-gated and supervised, staged with checkpoints).

## Locked preconditions (confirmed by the maintainer)
- Records backend for THIS repo: `repository` (TRACKED). `.agents/{plans,docs,specs,research,prompts,comms}`
  and `workflow-artifacts/` relocate to `.aw/records/*` and stay tracked in this repo.
- System: `.agents/workflows` -> `.aw/system` (canonical relocation).
- Config -> `.aw/config` (project.json tracked / local.json untracked). State -> `.aw/state` (durable/runtime).
- No-writer window: the maintainer keeps all other agents/sessions/workflows OUT during inventory -> cutover.
- External roots: NONE (all framework material is inside the repo; ~/.aw holds only registration/state, not migrated).
- Execution style: STAGED WITH CHECKPOINTS (map approval, rehearsal report, real cutover, commit confirmation).

## Reusable follow-up (the general problem)
- The Stage-1 findings below are GENERAL: every installed agent-workflows repo carries the same
  infrastructure files (layout README, tracked leak-allowlist config, per-repo self-install
  manifest, gitignored adapter dependency trees). Rather than rediscover these dispositions per
  repo, they are being generalized into the migration tooling + a reusable user entrypoint under a
  NEW follow-up IPD:
  `.agents/plans/pending/20260812-2216-01-generalize-layout-migration-dispositions-and-entrypoint.md`
  (id bsxowq, Status: to-review). Order 11 stays scoped to migrating THIS repo using the
  dispositions decided here; bsxowq makes them automatic for all repos and adds the
  post-install/update entrypoint over `aw migrate-layout`.

## Stage 1 findings (read-only; production `aw migrate-layout inventory --target-backend repository`)
- Baseline frozen at /tmp/opencode/order11-baseline: git clone --mirror repo.git, 762 commits,
  HEAD 3e07137, tracked-tree digest d91e0630..., 789 tracked files.
- Inventory returned valid:False (fail-closed) with two real issues, both resolved below.

### Issue A - node_modules noise (RESOLVED: exclude)
- The inventory swept in .opencode/node_modules/ (3926 gitignored dependency files) as
  `host-adapter-candidate`. Root cause: aw_layout_inventory._walk does NOT honor .gitignore
  (only skips .git), and _legacy_class blanket-labels anything under an `*-adapters` root as
  host-adapter-candidate. This is dependency noise, NOT framework material.
- Disposition: EXCLUDE node_modules from the migration (scope the inventory roots to skip it).
- TOOL GAP TO BACKLOG: make aw_layout_inventory._walk honor .gitignore (skip ignored subtrees,
  esp. node_modules) so the inventory does not enumerate dependency trees. Own follow-up.

### Issue B - 6 tracked .agents/ infrastructure files with no disposition (unknown-owner)
Decided dispositions (all IN-SCOPE for Order 11; maintainer confirmed, no deferrals):
1. `.agents/agent-workflows/managed-sections.json` (this repo's own install manifest) + its
   `README.md` -> `.aw/system/managed-sections.json`.
   - WHY: new-layout code ALREADY reads the manifest at <system_root>/managed-sections.json
     (project_layout.py:217/327/420). Legacy path manifest.py:41
     DEFAULT_MANIFEST_RELPATH = ".agents/agent-workflows/managed-sections.json" is exactly what
     this migration retires.
   - CODE CHANGE: update manifest.py:41 DEFAULT_MANIFEST_RELPATH to the .aw/system location
     (or make it resolve via the layout). Move/regenerate the explanatory README.
2. `.agents/local-leaks-allowlist.toml` (tracked, CI-read) + `.agents/local-leaks-hints.json.example`
   -> `.aw/config/`.
   - WHY: tracked, travels-with-repo, CI-deterministic project CONFIG = the .aw/config class.
   - CODE CHANGE (atomic with the move, or the sanitizer/CI break):
     leak_sanitizer.py:153 REPO_ALLOWLIST_REL -> .aw/config/local-leaks-allowlist.toml
     (functional uses at leak_sanitizer.py:210/219/340), plus message strings at
     leak_sanitizer.py:148/320/868 and cli.py:2698. No CI/pre-commit hardcodes the path (they
     call the sanitizer, which uses the constant) - confirmed by grep.
3. `.agents/README.md` (human doc describing the directory model) -> regenerate as `.aw/README.md`
   for the new system/config/state/records layout (E-05 "regenerate owner-managed docs").

## Remaining execution plan (staged, not yet done)
- Stage 1b: re-run inventory with node_modules excluded + the 3 dispositions encoded; confirm
  valid:True and present the final disposition map for approval (E-02 checkpoint).
- Stage 2: full rehearsal on a disposable clone - migrate, compare/postcheck/fresh-agent audit,
  exercise producing workflows, prove rollback + resume - BEFORE touching the real checkout.
- Stage 3: real cutover (hash-verify each phase; stop on drift), re-add the .aw/system pyproject
  lines commented out in commit c28cdd1 (wheel force-include + sdist include) and re-verify
  `python -m build` + full suite, regenerate indexes/adapters/manifests/version refs + the code
  reader updates above, strengthen the still-hollow test_e07 (git-separation) with real machinery.
- E-06: compare post-migration bytes/history/refs to the frozen baseline; postcheck + fresh-agent audit.
- E-07 checkpoint: show staged path-scoped diffs (relocation / derivatives / record movement kept
  separate) for the maintainer's commit confirmation; commit, NO push.
- Transition: fill E/V evidence with concrete output, pre-transition lint, Status executed,
  move to executed/, regen plans index. Orchestrator owns the terminal transition.
