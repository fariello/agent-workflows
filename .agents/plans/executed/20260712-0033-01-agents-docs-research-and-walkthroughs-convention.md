# IPD: `.agents/docs/` convention (research + walkthroughs), tracked with the canonical naming, installed everywhere

- Date: 2026-07-12
- Concern: durable knowledge / convention. Research and analysis an agent relies on (e.g. the GPT-5.6
  instruction-file-discovery survey) should be IMMORTALIZED to a tracked location with the standard
  `YYYYMMDD-HHMM-NN-<slug>.md` naming - both in THIS repo and in every repo the framework installs
  into - so decisions have durable, discoverable evidence (P4 durable-knowledge / cold-start). Today
  such artifacts land ad hoc (I put two under `docs/research/` with a non-canonical `date-slug` name).
- Scope: define `.agents/docs/` with two initial buckets, `research/` and `walkthroughs/`, each using
  the canonical local-time `YYYYMMDD-HHMM-NN-<slug>.md` convention (D48/D50/D55) and a Category-1
  generated README (D49, no-clobber); scaffold them via the installer/`setup-repo` so INSTALLED repos
  get the same home; migrate the two current research files into `.agents/docs/research/` with
  canonical names; add an AGENTS.md directive to immortalize relied-on research; docs + DECISIONS.
  ABSORBS Theme D's `.agents/docs/walkthroughs/` scaffold (Theme D then shrinks to just the brain-dir
  MUST-mirror RULES).
- Status: executed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised by the maintainer - research we
  use should be tracked with standard names, here and in installed repos. Fleshed out against the
  D49 dir-README machinery and the plan-naming convention. Complete proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-D (wire ensure_docs_readmes into the install flow at engine.py:2225), PR-E (README is the
  tracked placeholder), cross-plan note with 0030-01 (share ONE agents_pointer_block). Mechanism
  verified against source. No BLOCKER/HIGH. Status -> reviewed.
- 2026-07-12 executed (Antigravity/Gemini): implemented .agents/docs/ scaffolding, templates, wired engine logic, migrated research files, and updated normalizer and AGENTS.md.

## Project conventions discovered (Step 0, VERIFIED against source)

- Dir-README scaffolding (D49): `ensure_plans_readmes` (engine.py:2104) writes no-clobber READMEs
  from `_PLANS_README_TARGETS` (:2098) + per-bucket templates under
  `.agents/workflows/templates/plans-<bucket>-README.md`; `create_setup_artifacts` (:2142) mkdirs the
  dirs. Same pattern extends cleanly to `.agents/docs/`: add a `_DOCS_README_TARGETS` tuple + new
  templates (`agents-docs-README.md`, `agents-docs-research-README.md`,
  `agents-docs-walkthroughs-README.md`) and scaffold the dirs. No-clobber, staged, dry-run aware.
- Naming convention: `YYYYMMDD-HHMM-NN-<slug>.md`, LOCAL time (D55), `NN` per-minute two-digit (D48).
  The normalizer (`normalize_plan_names.py`) currently scans `.agents/plans` + `.agents/prompts` and
  supports `--area` / `--all`; confirm/extend so `.agents/docs/**` is normalizable too (at least via
  `--area docs` or `--all`), keeping ONE naming enforcement path (the `aw plan-names` verb, D56).
- Existing `.agents/` top level: only `plans/` and `workflows/`. `docs/specs/` (repo root, NOT under
  `.agents/`) already holds a research prompt precedent; this IPD standardizes on `.agents/docs/` as
  the tracked home so it travels with installs.
- Two files to migrate (currently `docs/research/`, committed bec5a16):
  `2026-07-12-agent-instruction-file-discovery-survey.md` and `...-prompt.md`.
- House rule: no em dashes in AUTHORED framework Markdown. External research artifacts are archived
  VERBATIM (their own punctuation is preserved; the rule applies to what WE author, not cited sources).

## Proposed changes (ordered, validatable)

1. **Define `.agents/docs/` + buckets.** `research/` (durable research/analysis an agent relied on)
   and `walkthroughs/` (narrative session/feature walkthroughs). Both use
   `YYYYMMDD-HHMM-NN-<slug>.md` (walkthroughs: `...-<slug>-walkthrough.md`). Add three Category-1
   templates: `agents-docs-README.md` (overview of the docs tree + naming), plus per-bucket READMEs.
2. **Scaffold + no-clobber READMEs.** Extend `create_setup_artifacts` (engine.py:2142, which already
   mkdirs the plan buckets via `PLAN_LIFECYCLE_SUBDIRS` :2158/2167) to mkdir `.agents/docs/research`
   and `.agents/docs/walkthroughs`, and add `ensure_docs_readmes` mirroring `ensure_plans_readmes`
   (:2104) with a `_DOCS_README_TARGETS` tuple. PR-D: WIRE the new function into the install flow at
   the same call site as `ensure_workflow_artifacts_readme` / `ensure_plans_readmes` (engine.py:2225),
   else it is dead code. PR-E: the generated README is the tracked placeholder that keeps each
   otherwise-empty bucket in git (git does not track empty dirs) - intended, not a workaround.
   No-clobber, staged, dry-run aware, exactly like the plans READMEs.
3. **`setup-repo` awareness.** Update `setup-repo.md` to list `.agents/docs/{research,walkthroughs}/`
   among the scaffolded lifecycle dirs and describe the naming + immortalize-research contract.
4. **Migrate current artifacts.** `git mv` the two `docs/research/*` files into `.agents/docs/research/`
   renamed to canonical `YYYYMMDD-HHMM-NN-<slug>.md` (derive the time from git-first-commit via the
   normalizer's earliest-evidence rule; `NN=01`, `02`). Leave `docs/specs/` as-is (specs are a
   separate, established area).
5. **Normalizer + verb coverage.** Ensure `normalize_plan_names.py` / `aw plan-names` can check/apply
   canonical names under `.agents/docs/**` (via the default set or `--all`); add a test.
6. **AGENTS.md directive (this repo + installed block).** Add a short rule to the managed
   `AGENT-WORKFLOWS` block: "Immortalize research/analysis you rely on for a decision to
   `.agents/docs/research/` using `YYYYMMDD-HHMM-NN-<slug>.md`; save narrative walkthroughs to
   `.agents/docs/walkthroughs/` with `...-walkthrough.md`." (Same block ships to installed repos, and
   - per IPD 20260712-0030-01 - into existing CLAUDE.md/GEMINI.md.)
7. **Docs + DECISIONS + tests.** README/ARCHITECTURE note the `.agents/docs/` tree; DECISIONS entry
   (Dnn); tests for the new scaffold (dirs + no-clobber READMEs created; dry-run; idempotent) and the
   normalizer coverage. Suite green. Regenerate this repo's `.agents/docs/**` READMEs (dogfood).

## Deferred / out of scope

- The brain-dir MUST-mirror RULES themselves (Theme D `20260712-0014-04`) - this IPD provides the
  `walkthroughs/` HOME; Theme D provides the enforcement prose. Theme D shrinks accordingly.
- Additional `.agents/docs/` buckets (e.g. `decisions/`, `adr/`) - add later if a need appears; do not
  speculatively create empty buckets (P6).
- Migrating `docs/specs/` or `docs/research/` legacy content beyond the two named files.

## Open questions (v1 leans for review)

1. `.agents/docs/` vs `.agents/analysis/` vs `.agents/knowledge/` for the parent. (Lean: `.agents/docs/`
   - broadest, and Theme D already assumed `.agents/docs/walkthroughs/`.)
2. Do research files carry front-matter (a `## Source`/date/`Workflow history`) like plans, or stay
   free-form archives? (Lean: free-form archives + a one-line provenance header the agent adds when
   saving; NOT the full plan Status lifecycle - research is reference, not a lifecycle artifact,
   consistent with the D52 "prompts get history, not the enum" stance.)
3. Should `assess`/`release-review`/`advise` run-records (under `workflow-artifacts/`) also move here?
   (Lean: NO - `workflow-artifacts/` is the established run-record home; `.agents/docs/research/` is for
   curated, relied-on artifacts an agent chooses to immortalize, not every run.)
4. Confirm the normalizer default scan should include `.agents/docs` or only via `--all`/`--area docs`.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Evidence re-opened against source:
- Mechanism VERIFIED: `PLAN_LIFECYCLE_SUBDIRS` (engine.py:1979), `ensure_plans_readmes` (:2104) +
  its call site next to `ensure_workflow_artifacts_readme` (:2225), and `create_setup_artifacts`
  bucket mkdirs (:2158/2167) - the `.agents/docs/` extension is a faithful mirror. Test harnesses
  `test_setup_artifacts.py` + `test_dir_readmes.py` exist to extend.
- PR-D (gap fixed): must WIRE `ensure_docs_readmes` into the install flow at :2225, else dead code.
- PR-E (clarified): the generated README is the tracked git placeholder for each otherwise-empty
  bucket (git ignores empty dirs) - intended.
- Rubric G (KISS): OQ3 correctly keeps run-records in `workflow-artifacts/` (no migration) and OQ2
  keeps research free-form (no forced Status lifecycle) - avoids over-modeling reference material.
- Cross-plan (with 0030-01): both edit the AGENTS.md managed block; the shared block content must be
  reconciled so change #6's directive text and 0030-01's mirroring use ONE block definition
  (`agents_pointer_block`), not two - noted so execution order does not create drift.
No BLOCKER/HIGH findings; OQ1-4 leaned. This IPD does not self-approve.

## Approval and execution gate

`reviewed`. Next: human approve (confirm OQ1-4 leans), execute changes 1-7, validate (suite green +
dogfood scaffold), commit (never push), `git mv` to executed/. Not auto-executed. Sequence note:
independent of the native-file-mirroring IPD (20260712-0030-01) except that both touch the AGENTS.md
managed block (`agents_pointer_block`) - reconcile against whichever lands first (ONE block
definition).
