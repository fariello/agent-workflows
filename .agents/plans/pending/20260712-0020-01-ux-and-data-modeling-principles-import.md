# IPD: Import sharpened UX + data-modeling principles (new lens + ui-ux enrichment + P6/P7/P3)

- Date: 2026-07-12
- Concern: principle/lens coverage. A set of generic UX and object/data/schema design principles
  (drafted with GPT-5.6, `tmp/GENERIC_AGENTS.md` + `tmp/GENERIC_GUIDING_PRINCIPLES.md`) codify the
  maintainer's design philosophy. Most is already covered by existing lenses; a filtered subset of
  genuinely-missing, sharp principles is worth importing. The compliance/security/accessibility-heavy
  remainder of those generics is deliberately OUT of scope here.
- Scope: (1) a NEW `assess` lens `data-modeling.md` + its manifest row; (2) enrich the existing
  `ui-ux` lens rubric; (3) lightly sharpen THIS repo's `GUIDING_PRINCIPLES.md` (P6/P7/P3);
  (4) cross-link from `architecture`/`api-design` lenses; (5) regenerate shims + docs/DECISIONS.
  Single-source-of-truth: the LENSES are the canonical home for the installed-side principles (not a
  competing baseline doc).
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-12 to-review (its_direct/pt3-claude-opus-4.8-1m-us): filtered the two generic docs to just
  UX + data/schema; confirmed against existing ui-ux/architecture/api-design lenses what is genuinely
  new; maintainer chose lens-enrichment + a new data-modeling lens + light P6/P7 sharpening. Complete
  proposal; born to-review.
- 2026-07-12 /plan-review (its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED;
  PR-A (assess-all areas are prose at assess-all.md:20, not a manifest group -> reframed OQ2; new
  assess- row auto-recognized as catalog). No BLOCKER/HIGH. Status -> reviewed.

## Project conventions discovered (Step 0, VERIFIED against source)

- Lenses live in `.agents/workflows/assess/lenses/*.md`; each is registered by a manifest row in
  `.agents/workflows/index.md` (`assess-<concern> | .agents/workflows/assess/assess.md |
  .agents/workflows/assess/lenses/<c>.md | <desc>`), and shims regenerate from the manifest. The
  `scaffold` workflow is the sanctioned way to author a new lens + wire the manifest.
- Existing coverage (so we do NOT duplicate): `ui-ux.md` already has flows/defaults/feedback/
  consistency/error-prevention/cognitive-load/power-user rubric; `architecture.md` has
  decomposition/coupling/abstraction/extensibility/config-over-hardcoding/single-source-of-truth;
  `api-design.md` covers the public-contract/canonical-interface angle. The genuinely-missing items
  are the object/data-modeling specifics + a few UX one-liners (below).
- This repo's `GUIDING_PRINCIPLES.md` is intentionally tight (10 principles). Import must SHARPEN
  existing principles, not bloat the file or add N/A (security/audit/accessibility/DB) material - this
  repo is a zero-dep CLI + markdown workflows.
- House rule: no em dashes in authored Markdown.

## Proposed changes (ordered, validatable)

1. **New lens `lenses/data-modeling.md`** (object/data/schema design). Rubric captures the items NOT
   already in `architecture`/`api-design`:
   - **Canonical models / "a new noun does not require a new model":** compare SEMANTICS not names;
     is this just a different label/state/role/config of an existing concept? Separate only on a real
     invariant/identity/lifecycle difference.
   - **Generality ladder (ordered):** (1) one model with variation as data/config -> (2) one shared
     core + a thin specialization -> (3) a bounded special case WITH written justification. Do not
     build for hypothetical needs; do not replace clear domain models with an unbounded metadata
     system.
   - **Configuration discipline:** config for expected variation (labels/roles/thresholds/routing/
     templates/effective-dates), and it must be typed/validated/versioned/auditable/testable; "do NOT
     turn configuration into a hidden programming language."
   - **Provenance & historical truth (generalized, project-agnostic):** preserve what was submitted/
     effective at each time; do not silently rewrite history; preserve provenance for imported/
     derived/user-entered data; version or effective-date rules when historical reconstruction
     matters. (Keep it general - not DB/regulatory-specific.)
   - Lead personas: architect (primary), software engineer, stakeholder. IPD emphasis: model changes
     are high Remediation Risk (migrations/blast radius); prefer the smallest evidenced change.
   - Register the manifest row `assess-data-modeling | .agents/workflows/assess/assess.md |
     .agents/workflows/assess/lenses/data-modeling.md | <desc>` in `index.md`; regenerate shims.
     PR-A (verified): the `assess-` prefix means `is_concern_catalog_row` recognizes it automatically
     (engine.py; tested in test_installer.py:38-44), and `test_parse_manifest_has_core_and_catalog`
     stays green - no test change needed for recognition. The concern's AREA (for `assess-all`
     grouping) is defined in PROSE at `assess-all.md:20` ("correctness, security/privacy, compliance,
     UX/docs, product/design, delivery/quality"), NOT a manifest field: add `data-modeling` to the
     "product/design" area there (this replaces the misframed OQ2 "add to a group").
2. **Enrich `ui-ux.md` rubric** with the missing sharp one-liners (do not duplicate existing bullets):
   - "Every unnecessary action is a defect" (friction is a defect, not a nicety).
   - "Do not require the user to select the only available option."
   - "Prefill known/likely values when safe; validate early; PRESERVE entered data after an error."
   - "Encourage automatic progression for safe intermediate steps, but never auto-commit a
     consequential final action." (refines the existing destructive-action-confirmation bullet.)
3. **Sharpen this repo's `GUIDING_PRINCIPLES.md`** (surgical, no bloat):
   - P6 (KISS): add the generality-ladder one-liner + "a new noun does not automatically require a new
     model/abstraction; compare semantics, not names."
   - P7 (general case): add "prefer variation as data/config before code."
   - P3 (self-documenting): add "minimize user effort; an unnecessary action is a defect."
4. **Cross-link** `architecture.md` and `api-design.md` lenses to the new `data-modeling` lens (a
   one-line "see also" so the canonical-model material has one home and the others reference it, per
   single-source-of-truth).
5. **Docs + DECISIONS + drift.** Update the assess lens catalog/README wherever lenses are listed;
   DECISIONS entry (Dnn) recording the import + what was deliberately EXCLUDED (compliance/security/
   accessibility/DB-history-heavy material) and why; run the suite (a lens is prose, but the manifest/
   catalog + any lens-count tests must stay green); regenerate shims.

## Deferred / out of scope

- The compliance/security/privacy/audit/accessibility bulk of the generic docs (already covered by
  dedicated lenses, or N/A to this repo; do not re-import).
- Any monolithic installed "GENERIC_GUIDING_PRINCIPLES" baseline doc (would compete with a target
  repo's own principles and create a second source of truth). The lenses are the delivery mechanism.
- The generic docs' plan-lifecycle section (it conflicts with D45-D55: it omits `NN`, the 5-dir
  lifecycle, local time, and the Status vocabulary; NOT imported).

## Open questions (v1 leans for review)

1. Lens name: `data-modeling` vs `schema-design` vs `object-modeling`. (Lean: `data-modeling` -
   broadest, covers objects+tables+schemas+config.)
2. assess-all grouping: RESOLVED (PR-A) - there is no manifest "group" field; areas are prose at
   `assess-all.md:20`. Add `data-modeling` to the "product/design" area there so rollups group it.
3. How much provenance/historical-truth to include without drifting into DB/regulatory territory.
   (Lean: keep to the general "don't rewrite history; preserve provenance; version when
   reconstruction matters" - 3-4 bullets, project-agnostic.)
4. Confirm the P6/P7/P3 edits SHARPEN rather than lengthen (keep GUIDING_PRINCIPLES tight).

## Plan-review record (2026-07-12)

Reviewed by `/plan-review` (its_direct/pt3-claude-opus-4.8-1m-us). Verdict: **APPROVE WITH REVISIONS
APPLIED** (pending human sign-off). Evidence re-opened against source:
- PR-A (accuracy): a new `assess-<concern>` row is auto-recognized as a catalog row
  (`is_concern_catalog_row`, test_installer.py:38-44) - no recognition test breaks; but assess-all
  AREAS are prose at `assess-all.md:20`, not a manifest group, so OQ2 was reframed (add to
  "product/design").
- Rubric G/H (KISS + principles): scope is well-disciplined - imports only the filtered subset,
  enriches existing lenses rather than duplicating (P8 single-source), keeps GUIDING_PRINCIPLES
  edits as SHARPENING not bloat (OQ4), and explicitly EXCLUDES the N/A compliance/security/DB bulk
  and the conflicting plan-lifecycle section (vs D45-D55). Good over-scope guarding.
- Rubric I (domain invariants): the new lens's "provenance/historical truth" bullet is kept
  general (OQ3), consistent with this repo's P4 (don't rewrite executed history) without importing
  DB/regulatory specifics.
- No BLOCKER/HIGH; a lens is prose (per the repo's "test mechanical parts, not instruction prose"
  policy) so validation is the manifest/shim regen staying green. OQ1/3/4 leaned. Does not
  self-approve.

## Approval and execution gate

`reviewed`. Next: human approve (confirm OQ1/3/4 leans + the lens name), execute changes 1-5,
validate (suite green + shims regenerated), commit (never push), `git mv` to executed/. Not
auto-executed.
