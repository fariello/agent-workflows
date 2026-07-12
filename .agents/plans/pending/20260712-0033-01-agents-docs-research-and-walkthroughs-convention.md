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
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised by the maintainer - research we
  use should be tracked with standard names, here and in installed repos. Fleshed out against the
  D49 dir-README machinery and the plan-naming convention. Complete proposal; born to-review.

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
2. **Scaffold + no-clobber READMEs.** Extend `create_setup_artifacts` to mkdir `.agents/docs/research`
   and `.agents/docs/walkthroughs`, and add a `_DOCS_README_TARGETS` path in an `ensure_docs_readmes`
   (mirroring `ensure_plans_readmes`) so installed repos get the tree + generated READMEs, no-clobber.
   Wire it into the install flow next to `ensure_plans_readmes`.
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

## Approval and execution gate

`to-review`. Next: `/plan-review` (two-commit per D52), resolve OQs, human approve, execute changes
1-7, validate (suite green + dogfood scaffold), commit (never push), `git mv` to executed/. Not
auto-executed. Sequence note: independent of the native-file-mirroring IPD (20260712-0030-01) except
that both touch the AGENTS.md managed block - reconcile against whichever lands first.
