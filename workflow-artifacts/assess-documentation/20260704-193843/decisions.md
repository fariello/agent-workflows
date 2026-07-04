# Decisions and assumptions - assess documentation 20260704-193843

## Concern and scope

- Concern: documentation. Scope: whole-repository documentation.
- Scope interpretation: for this repo the "product" IS the workflow instruction files +
  tools + installer, and the "documentation" is the root docs (README, ARCHITECTURE,
  CONTRIBUTING, DECISIONS, GUIDING_PRINCIPLES, AGENTS) plus the user-facing usage prose in
  `.agents/workflows/index.md`. The standard assess exclusion ("do not assess
  `.agents/workflows/` as if it were the project") was applied to the workflow BODIES as
  instruction content, but `index.md`'s usage documentation was assessed because it is the
  manifest/doc a user reads to run things.

## Project conventions discovered

- Plans: `.agents/plans/pending/` (pending), `.agents/plans/done/` (terminal; this repo
  uses `done/`, an accepted alias for `executed/`).
- Guiding principles: `GUIDING_PRINCIPLES.md`.
- Contributor contract: `CONTRIBUTING.md`, including a "Doc-sync checklist" whose step 5
  already requires README and ARCHITECTURE to stay accurate - the control that lapsed.

## Key judgment

- The dominant issue is ACCURACY drift in `ARCHITECTURE.md` (the lens's top rubric item),
  caused by the D31-D37 work landing after it was written. README and index.md were kept
  current during those builds; ARCHITECTURE was not. Rated High severity because a
  maintainer is explicitly directed there, and because it teaches a command model
  (`/assess-<concern>`) that will fail if a reader tries it.
- All fixes are Low Remediation Risk: documentation edits, no behavior change, no code.
  Fix-by-default applies with nothing deferred.

## What was intentionally NOT proposed (and why)

- No changes to README or index.md content beyond the optional D-09 changelog pointer:
  they are already accurate; editing them would be churn (Complexity axis).
- Not expanding ARCHITECTURE into a tutorial or restating DECISIONS (anti-bloat).
- The self-referential caveat: I built D31-D38 and I am assessing the docs for that same
  work, so this is a rigorous self-check, not an independent review. A genuinely cold
  reader (different session/model) might catch drift I am blind to. The findings are
  grounded in verifiable file/line evidence to limit that bias.

## Assumptions (confirm)

- D-09: a README pointer to DECISIONS.md as the change history is sufficient (lighter than
  maintaining a separate CHANGELOG.md). Flagged as an open question in the IPD.

## Open questions for the user

1. CHANGELOG.md vs. a README pointer to DECISIONS.md (D-09).
2. Whether `/release-notes` should later own this repo's changelog (dogfooding) - out of
   scope here.
