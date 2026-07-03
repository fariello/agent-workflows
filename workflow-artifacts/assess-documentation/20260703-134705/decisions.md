# Decisions and assumptions - assess-documentation 20260703-134705

## Concern and scope

- Concern: documentation (repository written docs).
- Scope: README, ARCHITECTURE, DECISIONS, CONTRIBUTING, AGENTS, `.agents/workflows/index.md`,
  and the release-review `README.md`/`MANIFEST.md`. NOT the workflow instruction bodies
  (those are the framework's product; covered by scope-exclusion / assessed as subject
  only when explicitly requested).

## Project conventions discovered

- Guiding principles present (`GUIDING_PRINCIPLES.md`): P2 honest docs, P8 single source.
- Plan/IPD lifecycle: `.agents/plans/pending/` + terminal `done/` (this repo predates the
  D26 `executed/` canonicalization and keeps `done/` as an accepted alias).
- Contributor contract: `AGENTS.md`, `CONTRIBUTING.md` (no em dashes, single-source).

## Key decisions

- **Re-verified before finalizing.** The IPD was drafted earlier the same day; per the
  workflow's discipline (verify claims against the current repo, do not trust the draft)
  every finding was re-checked. Result: D3, D4, D5 were already fixed by an intervening
  README rewrite (the on-ramp rewrite added the pipeline diagram, the DECISIONS-as-
  changelog line, and the newcomer primer). They are marked resolved-before-finalization
  rather than proposed.
- **D1 sharpened.** Re-check found the MANIFEST Files table is wrong in two directions:
  it lists `plan-review.md` (which lives in the sibling `plan-review/` dir, not
  `release-review/`) AND omits `MANIFEST.md` and `templates/`, which are present.
- **Verdict: adequate.** Docs are accurate and honest; only two low-risk MANIFEST edits
  remain.

## What was intentionally NOT proposed, and why

- A separate `CHANGELOG.md`: over-scope (Complexity axis) - `DECISIONS.md` serves that
  role and the README now points to it (D4).
- Any doc-style rewrite / reformatting: over-scope; the docs read well and are
  em-dash-free.

## Open questions

- Terminal-dir wording if the MANIFEST/README ever restate the lifecycle: use the D26
  canonical `executed/` with `done/` as an accepted alias (this repo uses `done/`).

## Note on repository rename

Between drafting and finalizing, the repo (and its local directory) were renamed
`ai-coding` -> `agent-workflows` (D27, D29). This assessment's scope and findings are
unaffected; the IPD title was updated to the new name.
