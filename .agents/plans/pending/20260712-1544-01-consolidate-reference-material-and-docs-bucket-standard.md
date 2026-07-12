# IPD: Establish the .agents/docs/ bucket standard and consolidate root prompts/ + docs/specs/ under it

- Date: 2026-07-12
- Concern: repository conformance / durable-knowledge organization. Two root directories are misplaced
  relative to the now-mature `.agents/docs/` convention: `prompts/` (a historical reference prompt
  library, deliberately unmaintained/unversioned) and `docs/specs/` (one design spec + one research
  prompt). Their root placement wrongly implies first-class project status. Root cause of the ambiguity
  (verified): the `.agents/docs/` standard is UNDER-SPECIFIED - `agents-docs-README.md`, the template,
  and engine `DOCS_SUBDIRS` all name only `research` + `walkthroughs` as an apparently EXHAUSTIVE list,
  yet `roadmaps/` already exists on disk. The maintainer RECINDS the two prior decisions that kept these
  at root (see below).
- Scope: (a) establish the `.agents/docs/` bucket standard as a non-limiting standard (README/template/
  `DOCS_SUBDIRS`), adding `specs`, `prompts`, and `roadmaps`; (b) `git mv prompts/` -> `.agents/docs/
  prompts/`; (c) `git mv` the two `docs/specs/` files into `.agents/docs/` (the spec -> `.agents/docs/
  specs/`; the research prompt -> `.agents/docs/research/`), then retire the root `docs/` tree; (d)
  update every reference (README, ARCHITECTURE, CONTRIBUTING, the `spec` workflow, `prompts/README.md`,
  the reversed decisions), the packaging test, and DECISIONS. Touches `agent_workflows/engine.py`
  (`DOCS_SUBDIRS` + a new docs-bucket README template) and `tests/test_packaging.py`.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): raised when the maintainer flagged root
  `prompts/` as "that's wrong" and asked to move it (and `docs/specs/`) under `.agents/`. Investigation
  found the moves reverse two prior committed decisions AND that the `.agents/docs/` bucket standard is
  under-specified (the real root cause). Maintainer recinded the prior decisions, chose to MOVE (not
   delete) prompts/ preserving provenance, and asked to establish the docs-bucket standard. Complete
   proposal; born to-review.
- 2026-07-12 /plan-review-long (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED.
  PB-2 (MEDIUM, completeness): a full `git grep` found `release-review/templates/final-response.md:70`
  references `prompts/` and was NOT enumerated; added it to change #5 + scope (conditional on it
  referring to this library), plus an explicit "LEAVE generic-example references alone" note
  (`assess.md:83`, `data-exfiltration.md:19`, `docs/rfcs/`). OQ1-4 resolved (maintainer): keep the rich
  prompts README; RENAME moved files to convention; document `roadmaps/` but do NOT ship it in
  DOCS_SUBDIRS (reconciled change #1 accordingly); next-free DECISIONS number. All cited path:line
  claims verified accurate. No BLOCKER/HIGH. Status -> reviewed.

## Plan-review record (2026-07-12)

Reviewed by `/plan-review-long` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH
REVISIONS APPLIED** (pending human sign-off).
- PB-2 (MEDIUM, rubric A/E, IN-SCOPE, FIXED): reference enumeration incomplete - a full `git grep`
  surfaced `final-response.md:70` (unenumerated) and the risk of over-reaching into generic-example
  references. Fixed: added the missing reference (conditionally) + an explicit leave-generic-examples
  instruction. Remediation Risk: Low.
- OQ1-4 (FIXED via maintainer decisions): keep rich prompts README (no-clobber); rename moved files to
  the `YYYYMMDD-HHMM-NN-<slug>` convention on move; document `roadmaps/` as a recognized bucket but do
  NOT add it to shipped `DOCS_SUBDIRS` (change #1 reconciled to add only `specs`+`prompts`); executor
  uses next-free DECISIONS number.
- Verified accurate (no finding): `DOCS_SUBDIRS` (engine.py:2212-2215), `FORBIDDEN_TOP`
  (test_packaging.py:25), `spec.md:24`, the prior "keep at root" statement (:73-74), `README.md:281-282`,
  `DECISIONS.md:65`, the wheel bundling model (test_packaging.py:79). Rubric E (packaging compatibility)
  is the load-bearing area and is handled (moves keep content out of the wheel; stale FORBIDDEN_TOP
  entries dropped; new assertion added). No BLOCKER/HIGH remains. Does not self-approve.

## Project conventions discovered (Step 0, VERIFIED against source)

- `.agents/docs/README.md` frames the tree as "two primary buckets" (`research/`, `walkthroughs/`) and
  reads as EXHAUSTIVE; it does NOT mention `roadmaps/` (which exists at `.agents/docs/roadmaps/` with a
  file) and has no room for a prompts bucket. The README is template-generated from
  `.agents/workflows/templates/agents-docs-README.md` (single source).
- Engine `DOCS_SUBDIRS = ("research", "walkthroughs")` (engine.py:2212-2215) is the canonical bucket
  list the installer scaffolds (README per bucket via `agents-docs-<bucket>-README.md` templates). It
  omits `roadmaps`. So the under-specification is consistent across README + template + code.
- Root `prompts/` (5 files): a historical reference library (`prompts/README.md`: "not stamped with the
  framework version ... not the current spec"). `fix-bar.md` is the ORIGIN of
  `release-review/fix-decision-policy.md`; the meta-prompt generated the `release-review/` runbook.
  Provenance value is real -> MOVE, not delete (P2/P4). Referenced by `README.md:281-282`,
  `ARCHITECTURE.md:25-27`, `DECISIONS.md:65` ("Sourced from `prompts/fix-bar.md`").
- `.agents/prompts/` is a DIFFERENT concept: operational STAGING for pending/queued prompts, scanned by
  `normalize_plan_names.py` (setup-repo) and tested at `test_normalize_plan_names.py:263`. So the moved
  library MUST go to `.agents/docs/prompts/` (a durable-docs content bucket), NOT `.agents/prompts/`.
- Root `docs/specs/` (2 files): `2026-07-06-pip-distribution-and-multi-repo-setup.md` (a real design
  spec) and `cli-name-collision-research-prompt.md` (a research prompt). The `spec` workflow names
  `docs/specs/` a valid home (`spec.md:24`).
- Reversed prior decisions (maintainer recinds both): (1) `docs/specs/2026-07-06-...:73-74` "Keeping
  `docs/specs/` and `prompts/` at the repo root is CORRECT"; (2) `spec.md:24` naming root `docs/specs/`
  as the specs home.
- Packaging (VERIFIED): the wheel ships `agent_workflows/` + the bundled tree remapped under
  `agent_workflows/_data/.agents/workflows/` (`test_packaging.py:79`). The SOURCE `.agents/` tree
  (plans, docs) is NOT shipped - only `.agents/workflows/` is bundled. So moving content under
  `.agents/docs/` keeps it out of the wheel naturally. `test_packaging.py:25`
  `FORBIDDEN_TOP = ("docs/", "prompts/", "tests/", "workflow-artifacts/")` asserts the wheel excludes
  those ROOT dirs; once root `docs/`+`prompts/` no longer exist, those two entries are stale.
  `CONTRIBUTING.md:113-116` documents the same exclusion list.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **Establish the `.agents/docs/` bucket standard (non-limiting).** Reword
   `.agents/workflows/templates/agents-docs-README.md` so it presents the buckets as a STANDARD that
   sets expectations WITHOUT limiting what may live under `.agents/docs/` (explicitly: "these are the
   standard buckets; other durable-doc content may exist"). Document buckets: `research/`,
   `walkthroughs/`, `specs/`, `prompts/`, and `roadmaps/`, each with a one-line purpose. Add ONLY
   `specs` and `prompts` to the shipped `DOCS_SUBDIRS` (engine.py:2212) with matching
   `agents-docs-<bucket>-README.md` templates; do NOT add `roadmaps` to `DOCS_SUBDIRS` (OQ3 RESOLVED:
   document it as a recognized bucket in the README standard, but do not scaffold it into downstream
   repos until the deferred post-release roadmaps-policy discussion). Regenerate `.agents/docs/README.md`
   + per-bucket READMEs (no-clobber; this repo's copies updated to match). The README's `roadmaps/`
   entry gets only a one-line "roadmap/consideration docs" purpose.
2. **Move `prompts/` -> `.agents/docs/prompts/`.** `git mv` all 5 files. Reframe `prompts/README.md` as
   the `.agents/docs/prompts/` bucket README (still "historical/reference, not maintained, superseded by
   the workflows"); reconcile it with the generated bucket README (keep the rich table as the bucket's
   own README content). NEVER to `.agents/prompts/` (staging-dir collision).
3. **Move `docs/specs/` into `.agents/docs/` and retire root `docs/`.** `git mv`
   `2026-07-06-pip-distribution-and-multi-repo-setup.md` -> `.agents/docs/specs/`; `git mv`
   `cli-name-collision-research-prompt.md` -> `.agents/docs/research/` (it is research, not a spec).
   Rename each to the `YYYYMMDD-HHMM-NN-<slug>.md` convention if `aw plan-names`/the docs convention
   requires it (the spec already leads with `2026-07-06`; confirm the normalizer is satisfied). Remove
   the now-empty root `docs/` tree.
4. **Update the `spec` workflow** (`.agents/workflows/spec/spec.md:24`): name `.agents/docs/specs/` as
   the specs home (retiring root `docs/specs/`); keep `docs/rfcs/` / `.agents/plans/` mentions as the
   workflow currently frames alternatives, but the canonical home is now under `.agents/docs/`.
5. **Update references + the reversed decisions.** `README.md:281-282` (prompts pointer ->
   `.agents/docs/prompts/`), `ARCHITECTURE.md:25-27` (tree diagram), `CONTRIBUTING.md:113-116`
   (packaging exclusion list: drop `docs/`+`prompts/` as ROOT dirs; the wheel already excludes the
   whole source `.agents/` tree). In `.agents/docs/specs/2026-07-06-...` (the moved spec) correct the
   now-false ":73-74" statement to record that root `docs/specs/`+`prompts/` were RETIRED into
   `.agents/docs/` by this IPD (append a corrective note; do not silently rewrite - it is a moved
   historical doc, so a dated correction line is honest). `DECISIONS.md:65` "Sourced from
   `prompts/fix-bar.md`" -> `.agents/docs/prompts/fix-bar.md`. COMPLETE reference set (added by
   /plan-review-long PB-2 after a full `git grep` for root `docs/`+`prompts/`):
   `release-review/templates/final-response.md:70` also names `prompts/` as a staging location - update
   it to `.agents/docs/prompts/` if it refers to this library, OR leave it if it refers to the generic
   pending-prompt staging concept (decide per the surrounding text; do not guess). LEAVE UNCHANGED
   (intentionally): `assess/assess.md:83` and `assess/lenses/data-exfiltration.md:19` and
   `spec.md`'s `docs/rfcs/` mention - these are GENERIC EXAMPLES of pending/spec dirs, not references to
   THIS repo's retired root `docs/`/`prompts/`; do not over-reach and edit generic examples.
6. **Packaging test.** In `tests/test_packaging.py`, drop the stale `"docs/"` and `"prompts/"` entries
   from `FORBIDDEN_TOP` (those root dirs no longer exist), and ADD an assertion that the wheel does not
   ship the source `.agents/docs/` or `.agents/prompts/` trees (only `agent_workflows/_data/.agents/
   workflows/` is bundled), so the ship-vs-dev boundary stays enforced after the move.
7. **Docs + DECISIONS + validation.** DECISIONS entry (Dnn = D72; note D72 is also claimed by IPD
   1449-01 if that lands first - the executor MUST use the next free number at execution time, not a
   hardcoded one) recording: the `.agents/docs/` bucket standard (non-limiting), the two moves, the two
   RECINDED prior decisions and why, and that provenance was preserved (moved not deleted). Validate:
   full suite green (esp. `test_packaging.py`, `test_normalize_plan_names.py`, `test_dir_readmes.py`,
   `test_setup_artifacts.py` which may assert `DOCS_SUBDIRS`); `aw plan-names` clean; regenerated docs
   READMEs match templates; `aw install . --dry-run` in sync. Paste the ACTUAL runner output.

## Deferred / out of scope

- Deeper `roadmaps/` policy / purpose (what belongs there, lifecycle): documented minimally here as a
  bucket; the substantive discussion is deferred to the maintainer post-release.
- The `.agents/prompts/` operational-staging concept: unchanged (it stays the pending/queued-prompt
  staging area; this IPD does not touch it).
- Shipping any of this reference material in the wheel: explicitly NOT wanted (stays dev/meta).

## Open questions (ALL RESOLVED with maintainer 2026-07-12 via /plan-review-long)

1. Bucket README for `.agents/docs/prompts/`: RESOLVED - keep the existing rich `prompts/README.md`
   table as the bucket's README (no-clobber; richer than a generated stub).
2. Naming of the moved spec/research files: RESOLVED - RENAME to the `YYYYMMDD-HHMM-NN-<slug>.md`
   convention on move (via `git mv`, preserving history), so they are conformant in the
   convention-governed tree. The spec (`2026-07-06-pip-distribution-...`) and the research prompt
   (currently undated) each get a conformant dated name.
3. `roadmaps/` in the shipped standard: RESOLVED - DOCUMENT `roadmaps/` as a recognized bucket in the
   `.agents/docs/` README standard, but do NOT add it to the shipped `DOCS_SUBDIRS` yet (the installer
   ships only `research`/`walkthroughs`/`specs`/`prompts`). Deeper roadmaps policy is a deferred
   post-release discussion, so we do not scaffold `roadmaps/` into downstream repos until then.
4. DECISIONS number collision with 1449-01 (both drafted "D72"): RESOLVED - the executor uses the next
   FREE number at execution time; whichever of {1449-01, 1544-01} lands second takes the higher number.

## Dependencies / sequencing

- Independent of IPD 1449-01 (pre-flight gate fix), except the shared DECISIONS-number caution (OQ4).
- Should land BEFORE the fresh `/release-review` re-run, so the review audits the conformant tree
  (otherwise the review would file findings about the very misplacement this IPD fixes). Maintainer
  sequence: fix workflow (1449-01) + this consolidation, then re-run release-review.

## Approval and execution gate

`to-review`. Execution contract (follow EXACTLY):

1. SCOPE FENCE. Touch ONLY: `agent_workflows/engine.py` (`DOCS_SUBDIRS` + docs-bucket README template
   wiring), `.agents/workflows/templates/agents-docs-README.md` + new `agents-docs-{specs,prompts,
   roadmaps}-README.md` templates, the regenerated `.agents/docs/**/README.md`, the moved files under
   `.agents/docs/`, the retired root `docs/` + `prompts/`, `.agents/workflows/spec/spec.md`,
   `.agents/workflows/release-review/templates/final-response.md` (the `:70` prompts-staging reference,
   per change #5, ONLY if it refers to this library), `README.md`, `ARCHITECTURE.md`, `CONTRIBUTING.md`,
   `tests/test_packaging.py`, `DECISIONS.md`. Do NOT refactor unrelated code, touch other workflows, or
   edit generic-example references (`assess/assess.md:83`, `data-exfiltration.md:19`, the `docs/rfcs/`
   mention). If a change seems to need more, STOP and report.
2. Use `git mv` for every relocation (preserve history); the source deletion + destination are both
   committed (path-scoped) so the move is complete.
3. Authoring style: NO em dashes or en dashes in any Markdown you write.
4. VALIDATE: run the FULL test suite; paste the ACTUAL runner output. Confirm `aw plan-names` clean,
   docs READMEs match templates, `aw install . --dry-run` in sync. Fix only what this IPD's changes
   break; if a test failure implies scope beyond the fence, STOP and report.
5. COMMIT only this IPD's touched files, PATH-SCOPED (`git commit -m msg -- <path> ...`); never
   `git add -A`/bare/`-a`; never push. Use the next free DECISIONS number (not a hardcoded D72).
6. When implemented and tests actually pass, `git mv` this file to `.agents/plans/executed/`, set
   `Status:` to `executed`, append a `## Workflow history` line, commit that move path-scoped.

HARD MUST: paste the real test output; use `git mv` (preserve provenance); stay inside the scope fence;
never push. Not auto-executed; requires human approval.
