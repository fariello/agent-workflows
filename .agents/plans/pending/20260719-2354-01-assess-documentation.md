# IPD: Assess documentation - reconcile user-facing docs with the current capability set

- Date: 2026-07-19
- Concern: documentation
- Scope: whole project's written documentation (README.md, ARCHITECTURE.md, and the top-level docs), assessed for ACCURACY against what the toolkit does today. Excludes the framework's own `.agents/workflows/` content and `workflow-artifacts/` run records (review-scope exclusion).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-19 /assess documentation (opencode its_direct/pt3-claude-opus-4.8-1m-us): assessed; proposed 6 changes.

## Goal

Keep the user-facing documentation accurate: it should describe what the toolkit does TODAY. This development cycle added capabilities and conventions (agent-comms D81, plan Sets D82, the `.agents/prompts/` staging convention D91, the `local-leaks` detector + `aw check-local-leaks` D92/D93, the full 3.9-3.14 CI matrix) but the hand-maintained user docs (README.md, ARCHITECTURE.md) were not all updated in lockstep. The documentation lens ranks ACCURACY highest (honest docs over impressive docs): a doc that omits or misstates a shipped capability misleads new users and contributors. This assessment finds the concrete drifts and proposes concise corrections.

## Project conventions discovered (Step 0)

- Project intent/stack: a portable AI-agent workflow framework + a pip/PyPI package (`agent_workflows`, CLI `aw`), Python 3.9+ stdlib-only, git-tag-driven versioning.
- Guiding principles: `GUIDING_PRINCIPLES.md`.
- Plan/IPD lifecycle: `.agents/plans/pending/` -> terminal dirs; files `YYYYMMDD-HHMM-NN-<slug>.md`; front-matter `Status:` readiness (D52). This IPD is born `to-review`.
- Contributor contract: `AGENTS.md`, `CONTRIBUTING.md`.
- Documentation source-of-truth model (verified): `.agents/workflows/index.md` is the authoritative capability manifest (installer + `/list-workflows` read it); README.md and ARCHITECTURE.md are HAND-MAINTAINED restatements and are the drift-prone copies. The manifest <-> lens-files <-> persona-files sets are currently CONSISTENT (31 lenses = 31 `assess-<concern>` rows; 7 personas = 7 `advise-<persona>` rows; `assess-all` is a standalone workflow, not a lens - verified, no drift there).
- Run-record convention conflict (see F5): the assess workflow says the `workflow-artifacts/` run record is a committed deliverable and must NOT be gitignored, but D92/D93 gitignored + untracked `workflow-artifacts/` because it leaked absolute paths. This run's record is therefore written under `workflow-artifacts/` but is LOCAL-ONLY (gitignored), not committed.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona = which reviewer perspective surfaced it. All are ACCURACY/completeness gaps in hand-maintained docs; doc fixes are Low Remediation Risk.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| F1 | MEDIUM | Low | novice / engineer | README accuracy | The Assessments concern table omits `local-leaks` (shipped D93). A user listing concerns from the README would not know it exists. | `README.md:158-163` (table has no `local-leaks`); `.agents/workflows/assess/lenses/local-leaks.md` exists; `.agents/workflows/index.md` `assess-local-leaks` row |
| F2 | MEDIUM | Low | operator | README accuracy (CLI) | The `aw` command list omits `aw check-local-leaks` (shipped D93), so the README's CLI surface is incomplete. | `README.md:31-42` (lists install/setup/list/plans/plan-names, not check-local-leaks); `agent_workflows/cli.py` subcommand |
| F3 | MEDIUM | Low | novice / engineer | README + ARCHITECTURE accuracy | Neither README nor ARCHITECTURE mentions the `.agents/prompts/` operational-staging convention (shipped D91), though both document the sibling `.agents/comms/` and `.agents/docs/` conventions. ARCHITECTURE's directory tree lists workflows/docs/comms but not prompts. | `README.md` (0 hits for `.agents/prompts`); `ARCHITECTURE.md:55,59` (tree lists docs/comms, not prompts) |
| F4 | LOW | Low | operator | README precision | The Python support statement says "3.9+ (CI-verified floor)" but does not name the actual CI matrix, which is now the full `3.9, 3.10, 3.11, 3.12, 3.13, 3.14` on Linux/macOS/Windows. Accurate in spirit; could be more precise/current. | `README.md:17,221`; `.github/workflows/tests.yml` `python-version: ["3.9".."3.14"]` |
| F5 | LOW | Low | contributor / maintainer | convention consistency | The assess workflow instructs that the `workflow-artifacts/` run record is a committed deliverable and "Do not git-ignore it," but D92/D93 gitignored + untracked `workflow-artifacts/`. The two conventions now contradict; a contributor running `/assess` will be told to commit something that is gitignored. | `.agents/workflows/assess/assess.md:182-184`; `.gitignore` (`workflow-artifacts/`); DECISIONS D92/D93 |
| F6 | LOW | Low | maintainer | doc drift prevention | The README/ARCHITECTURE capability restatements are hand-maintained with no guard, so they will keep drifting from `index.md` (F1-F3 are instances). There is no check that the README's concern list matches the lens set. | `README.md:158-163`; `.agents/workflows/index.md` manifest; no such test in `tests/` |

## Proposed changes (ordered, validatable)

Fix inaccuracies first (lens guidance), keep edits concise (avoid bloat / Complexity axis).

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | F1 | Add `local-leaks` to the README Assessments table under Security & privacy, with a one-line focus consistent with the lens/manifest description. | `README.md` | Low | README lists `local-leaks`; matches `index.md` `assess-local-leaks` |
| 2 | F2 | Add `aw check-local-leaks` to the README CLI command list with a one-line description (working tree / `--history` / `--wheel`), consistent with `cli.py` and D93. | `README.md` | Low | README names the command; matches the CLI `--help` |
| 3 | F3 | Document the `.agents/prompts/` staging convention in README (the "what gets installed / conventions" section, next to `.agents/comms/`) and add it to the ARCHITECTURE directory tree + a short subsection, cross-referencing `.agents/prompts/README.md` and distinguishing it from the `.agents/docs/prompts/` library. | `README.md`, `ARCHITECTURE.md` | Low | both mention `.agents/prompts/`; the two prompt homes are distinguished |
| 4 | F4 | Update the README Python statement to name the current CI matrix (`3.9-3.14`, Linux/macOS/Windows) instead of only "3.9+ floor," keeping the "older 3.x expected but untested" caveat. | `README.md` | Low | wording matches `tests.yml` matrix |
| 5 | F5 | Reconcile the assess run-record convention with D92/D93: update `assess.md` (and, if present, the same wording in other workflows that emit `workflow-artifacts/`) to state that the run record is written under `workflow-artifacts/` and is LOCAL-ONLY (gitignored per D92/D93), no longer "a committed deliverable; do not git-ignore it." Record the reconciliation in DECISIONS (next free D-number, pin at execution). NOTE: this edits framework workflow files, so it is a convention change, not just user docs; keep it minimal and cite D92/D93. | `.agents/workflows/assess/assess.md`, other `workflow-artifacts/`-emitting workflows, `DECISIONS.md` | Low | no workflow tells the user to commit a gitignored dir; DECISIONS entry present |
| 6 | F6 | Add a lightweight drift guard: a `tests/` check asserting the README Assessments concern list matches the `assess-<concern>` manifest rows (and optionally the `advise-<persona>` list), so future capability additions cannot silently skip the README. Keep it advisory-simple (parse the README table region + `index.md`); do not over-engineer. | `tests/test_readme_catalog.py` (new), possibly a small parse helper | Low | the test FAILS if a lens/persona is missing from the README and PASSES on the reconciled README |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | n/a | No findings are deferred: all are Low Remediation Risk and proposed for action. | n/a |

Note on scope discipline (Complexity axis): F6's guard is deliberately scoped to the concern-list <-> manifest match only. A fully generated README (auto-rendered from the manifest) would be larger and is NOT proposed here; the guard catches drift without imposing a generator.

## Scope check

- Over-scope: none. Every step traces to an accuracy/consistency finding. F6 is bounded to a drift check, not a doc generator.
- Under-scope: Step 5 necessarily touches framework workflow files (not just user docs) because the inconsistency lives there; that is required to make the docs/conventions self-consistent. Confirm at review whether Step 5 should be split into its own IPD (it is a convention change) or kept here (OQ1).

## Required tests / validation

- Steps 1-4 (user docs): manual verification that each doc claim matches source (`index.md`, `cli.py --help`, `tests.yml`); link/anchor check; no em/en dashes; `aw check-local-leaks .` stays clean on the edited docs.
- Step 5: grep the workflow tree for the "do not git-ignore" run-record wording; confirm none remains that contradicts D92/D93.
- Step 6: `tests/test_readme_catalog.py` FAILS on a synthetic README missing a concern and PASSES on the real reconciled README; run on the CI matrix (stdlib only).
- Full suite: `python -m pytest -q` stays green; paste ACTUAL output (baseline 282 passed, 1 skipped; +1-ish from the new test).

## Spec / documentation sync

- This IPD IS a documentation-sync task. Steps update README.md and ARCHITECTURE.md (user docs) and `assess.md` + DECISIONS (Step 5 convention reconciliation). No product-behavior change except the new drift-guard test.

## Open questions

- OQ1 (Step 5 placement): the run-record/gitignore reconciliation edits framework workflow files and DECISIONS, which is a CONVENTION change rather than a pure user-doc fix. Keep it in this documentation IPD, or split it into its own small IPD? Lean: keep it here (it is small and is the direct cause of a documentation inconsistency), but flag for the human.
- OQ2 (F6 guard scope): assert only the assess-concern list, or also the advise-persona list and the core-command list, against the manifest? Lean: concerns + personas (both are catalog lists prone to the exact drift found); leave the core-command prose table advisory. Confirm.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review this IPD (optionally run `plan-review`; sets `Status: reviewed`). Resolve OQ1-OQ2. Pin the DECISIONS D-number for Step 5 at review.
2. On human approval, set `Status: approved` (+ `Approval:`), execute the ordered changes, run validation, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
