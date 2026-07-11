# Decisions and assumptions - assess documentation (20260711-173843)

## Concern / scope

Documentation accuracy/honesty (P2), whole project, forward-facing docs. Run at the maintainer's
request BEFORE a planned `/release-review`, because documentation is this project's core value and a
lot of forward-facing docs moved under D44-D50.

## Project conventions discovered

- Guiding principles: `GUIDING_PRINCIPLES.md`; P2 (honest docs) governs; P3 (self-documenting),
  P8 (single source of truth).
- Plan lifecycle: five states + `done/` alias; filenames `YYYYMMDD-HHMM-NN-<slug>.md`
  (D45/D47/D48). This run's IPD is named per that convention.
- Framework-is-subject: this repo IS the product; `.agents/workflows/` assessed as the product
  (explicit-subject exception), not excluded per the normal scope rule.

## Key decisions / assumptions

- Ran a single documentation lens over the whole project (maintainer's choice), not
  self-documentation, and not scoped only to recent changes - to catch pre-existing drift too.
- Verdict "adequate, needs work": no blocker/false-feature claims; core descriptions accurate; drift
  is concentrated and all Low Remediation Risk to fix.
- Step 1 (dogfood re-run) is proposed FIRST because "honest docs" for this project includes the repo
  self-conforming to its own shipped D47/D49; leaving `.agents/plans/` at three dirs and the stamp at
  `1.0.0` would be the very dishonesty the concern targets.

## Intentionally NOT proposed (and why)

- The `v1.0.1` version bump / release itself: a RELEASE action, not documentation. Step 1's stamp
  refresh is entangled with it and gated on Open Question 1. This is a sequencing choice, not a
  Remediation-Risk deferral; `/release-review` (next) owns release readiness.
- No rewrites of DECISIONS dated entries or `workflow-artifacts/` history (append-only, P4).
- The `engine.py` type issues are CODE, not docs - out of concern; routed onward to `/release-review`
  (recorded as X-1 in findings.csv and in report.md) rather than dropped.

## Open questions for the user

1. Release intent: cut `v1.0.1` now (tag + `make version-file` + release notes), or just refresh the
   `index.md`/`VERSION` stamp to the current dev value and defer the release to after
   `/release-review`? (Blocks the version-bake half of Step 1.)
2. Python floor: tighten `requires-python` to `>=3.9` (match CI + README), or keep `>=3.8` and soften
   the README to "3.9+ verified, 3.8 best-effort"?
