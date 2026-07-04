# Decisions and assumptions - assess documentation (20260704-180630)

## Concern and scope

- Concern: `documentation` (exact lens match, `assess/lenses/documentation.md`).
- Scope: whole project. Because this repo IS the framework, the harness's "do not
  assess `.agents/workflows/` as if it were the project" exclusion is applied by treating
  the workflow *bodies* as product and the repo-level docs + the workflow *manifest/READMEs*
  + `prompts/` as the documentation under review. This mirrors prior assess-documentation
  runs on this repo (2026-06-30, 2026-07-03, 2026-07-04).

## Project conventions discovered

- Guiding principles: `GUIDING_PRINCIPLES.md` (P2 honest docs, P4 durable knowledge, P8
  single source of truth are the binding ones for this concern).
- Plan lifecycle: `.agents/plans/pending/` (new) and `.agents/plans/done/` (terminal; this
  repo uses the `done/` alias). Both dirs exist. IPD template: `assess/templates/ipd.md`.
- Contributor contract: `CONTRIBUTING.md` (doc-sync checklist, step 5 = keep README/
  ARCHITECTURE accurate); `AGENTS.md` is a pointer only.
- House rule: no em dashes in authored Markdown (`CONTRIBUTING.md`).

## Key decisions

- Applied the Fix Bar as "what to propose": both findings are Low Remediation Risk, so
  both are proposed for fixing (fix-by-default). Nothing deferred, nothing dropped.
- DOC-01 rated Medium severity (not Low) because it is in the *canonical per-tool run
  guide* a newcomer is pointed to, and it makes them type a command that does not exist -
  higher novice harm than a stray typo elsewhere. Remediation Risk is Low (a two-line edit).
- Deliberately did NOT propose editing the historical `prompts/*.md` bodies for "currency":
  they are origin/reference artifacts, and rewriting them to look current would falsify
  history (against P4, and the same append-only discipline the framework applies to
  DECISIONS). Only an orienting index is proposed. (Complexity/functionality axis avoided.)
- Deliberately did NOT propose adding the internal D39 pending-plans review gate to the
  user-facing README: it is a release-review-internal behavior already documented in the
  workflow bodies and DECISIONS; surfacing it in README would be bloat (Complexity axis).

## What was intentionally NOT proposed and why

- No VERSION bump: docs-only, consistent with prior doc-fix executions.
- No changes to README quick-start, command tables, install-details, ARCHITECTURE, or
  GUIDING_PRINCIPLES: verified accurate against the current tree, `install-workflows.py
  --help`/`--version` (`20260704-02`), the manifest, and D31-D39.

## Open questions for the user

1. `prompts/README.md`: label clear successors explicitly ("superseded by <workflow>") or
   keep neutral "reference material" notes? Execution assumption: label the clear
   successors, mark the two general QA/validation prompts as reference material.
2. Confirm terminal dir stays `.agents/plans/done/` (repo convention) vs. the canonical
   `executed/`. Assumption: keep `done/`.

## Self-review caveat

Same author built/last-edited these docs and is assessing them. Rigorous self-check tied
to file:line evidence, not an independent audit.
