# IPD: Assess documentation - accuracy and consistency of the ai-coding repo docs

- Date: 2026-06-30
- Concern: documentation (repository documentation lens)
- Scope: whole project. Documentation surface only: `README.md`, `ARCHITECTURE.md`,
  `DECISIONS.md`, `GUIDING_PRINCIPLES.md`, `AGENTS.md`, `.agents/workflows/index.md`,
  `.agents/workflows/release-review/README.md` + `MANIFEST.md`, `prompts/*.md`, and the
  root `release-review-final-checks.txt`. Per the framework's own scope-exclusion rule
  (`.agents/workflows/00-run-protocol.md`, referenced by assess.md Step 0.5), the
  workflow *instruction bodies* are the framework itself and are not assessed as
  "project code"; their role as user-facing documentation (READMEs, index, MANIFEST) is
  in scope.
- Status: EXECUTED (approved by maintainer 2026-06-30; all steps applied and validated)
- Author: OpenCode (its_direct/pt3-claude-opus-4.8-1m-us)

## Goal

Keep this repository's documentation matching what the software actually does today,
per Guiding Principle 2 ("Honest documentation over aspirational documentation") and
Principle 8 ("Single source of truth; no drift"). This project's docs are its product
surface: users adopt the framework by reading `README.md` and `index.md`, so a
doc inaccuracy is a product defect. The docs are already strong; this plan fixes a
small number of accuracy/consistency defects and removes one orphaned, stale artifact
before they mislead a new adopter or erode trust in a project whose entire value
proposition is disciplined, honest review.

## Project conventions discovered (Step 0)

- Project intent: a collection of AI-assisted-development resources; centerpiece is the
  reusable agent-workflow framework under `.agents/workflows/` (flagship
  `release-review`, plus `plan-review` and the `assess-*` family). Audience: engineers
  adopting the framework in *other* repos, and agents executing it.
- Guiding principles: `GUIDING_PRINCIPLES.md` (present; 10 principles). Directly
  relevant: P2 honest docs, P6 KISS/anti-bloat, P8 single source of truth.
- Pending-plans location/format used: none existed. Created `.agents/plans/pending/`
  (the `assess.md` default) and wrote this IPD there. Confirmed by the maintainer as the
  project's convention for assessment IPDs (Open Question 1, resolved).
- Contributor/spec-sync contract: `AGENTS.md` is a one-line pointer only; no
  `CONTRIBUTING.md`. No explicit doc-sync rule beyond the guiding principles. (This
  absence is itself Finding D6.)
- Stack / relevant context: Markdown documentation + one Python installer
  (`install-workflows.py`, argparse). No build/test tooling in-repo.
- Scope exclusions applied: did not assess `workflow-artifacts/` (none present) or
  treat workflow instruction bodies as project code.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate for whether to
act now. Persona = which reviewer perspective surfaced it. Lead personas for this lens:
the complete novice and the engineer/operator adopting from the docs.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D1 | Medium | Low | Novice / Operator | Stale orphan artifact | `release-review-final-checks.txt` is a tracked root file describing the deleted `release-review.zip` build (`Created /mnt/data/release-review.zip`, "Files included: 22") and the abandoned root `release-review/` layout. The project removed the zip (DECISIONS D12, reversed) and restructured to `.agents/workflows/` (D17). The file is referenced by nothing and directly contradicts current docs. A newcomer scanning the repo root meets an authoritative-looking checklist describing an architecture that no longer exists. | `release-review-final-checks.txt:1-65`; orphan confirmed (no `.md` references it) |
| D2 | Medium | Low | Engineer/adopter | Provenance overstated (canonical vs. origin) | `README.md:30-31` calls `prompts/fix-bar.md` "the source of the framework's Fix Bar **policy**." `fix-bar.md:3-5` is a RhodyPACT-scoped prompt, and `DECISIONS.md:62-64` (D4) records it as a genuine *source input* ("Sourced from `prompts/fix-bar.md`") - so it truly was a source, but it is NOT the current normative policy. The enforced/canonical policy is `.agents/workflows/release-review/fix-decision-policy.md`. The README wording conflates "origin note" with "canonical policy," lightly undercutting P8. Fix is to disambiguate README only; the DECISIONS sourcing statement is accurate history and must be preserved. | `README.md:30-31`; `DECISIONS.md:62-64`; `prompts/fix-bar.md:1-5`; canonical: `fix-decision-policy.md` |
| D3 | Low | Low | Engineer/adopter | Prompts dir role unclear + one internal drift note | `prompts/` is a *living, reusable prompt library* the maintainer uses across their AI-aided coding environments (and a home for generated/reusable prompts); it is intentionally **not** consumed by this repo's workflows/commands. Current docs (`README.md:30`, `ARCHITECTURE.md:23`) describe it only as "reusable prompts," which understates that independence and can lead a reader to expect the workflows to use it. Separately, some prompts here (e.g. `final-release-validation-executable.md`) reference the pre-restructure `repository-review/<RUN_ID>/` run-artifact layout that the shipped framework migrated away from to `workflow-artifacts/` (D19); this is fine *as a reusable prompt* but a one-line note preventing a reader from mistaking those paths for the current framework's convention is worth adding. This is a clarity/framing fix, not a "supersede" action. | `README.md:30`; `ARCHITECTURE.md:23`; `prompts/final-release-validation-executable.md:56,62,70,77,794` |
| D4 | Low | Low | Novice | Filename typo in a documented artifact | `prompts/older-gerneral-qaqc-prompt-library.md` misspells "general" as "gerneral" in a tracked filename. Minor, but it is a visible quality signal in a project selling documentation discipline, and it makes the file harder to find/reference. | `prompts/older-gerneral-qaqc-prompt-library.md` (filename) |
| D5 | Low | Low | Operator/adopter | Getting-started gap: installer prerequisites/behavior not stated in README | `README.md:38-42` shows `python3 .../install-workflows.py` but never states the Python version requirement, that it is git-aware (stages, never commits), or that the *first* thing to do after install is review staged changes. The behavior is well-documented in `ARCHITECTURE.md` and the `--help`, but a novice following the README's "Using the workflows" section alone lacks the zero-to-first-success prerequisites the lens requires (Python 3, git repo, "review and commit the staged changes"). | `README.md:36-55` vs `install-workflows.py:125-147` (flags), `ARCHITECTURE.md:124-140` |
| D6 | Low | Low | Stakeholder/maintainer | No CONTRIBUTING / doc-sync contract | There is no `CONTRIBUTING.md` and `AGENTS.md` is only a pointer, so the rule "update `index.md` + add a lens + keep README/ARCHITECTURE in sync when adding a workflow" lives only implicitly in `ARCHITECTURE.md` prose. New contributors (or the maintainer months later) have no single checklist for keeping docs from drifting - the exact failure mode this IPD is cleaning up. The *fix* (a short CONTRIBUTING.md with a doc-sync checklist) is additive, doc-only, and reversible = Low Remediation Risk. Maintainer approved authoring it (Open Question 5, resolved: yes). | `AGENTS.md:1-7`; absence of `CONTRIBUTING.md` |

## Proposed changes (ordered, validatable)

Fix by default; each item is safe, well-scoped, and verifiable. Doc-only changes; no
code behavior changes. All are Low Remediation Risk except where noted.

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D1 | Remove the orphaned `release-review-final-checks.txt` (stale zip/`release-review/` build log, referenced by nothing). Use `git rm`. | `release-review-final-checks.txt` | Low | `grep -r release-review-final-checks .` returns no references; repo root no longer advertises the deleted zip layout. |
| 2 | D2 | Narrow, do NOT overcorrect. The true relationship (recorded in `DECISIONS.md:62-64` "D4 ... Sourced from `prompts/fix-bar.md`") is that `fix-bar.md` genuinely *was* a source input to the Fix Bar; preserve that. The only defect is README's word "**the** source of the framework's Fix Bar **policy**", which implies `fix-bar.md` is the current *normative/canonical* statement. Fix in `README.md:30-31`: describe `fix-bar.md` as "an origin/source note for the Fix Bar (see DECISIONS D4); the canonical, enforced policy is `.agents/workflows/release-review/fix-decision-policy.md`." Do NOT edit `DECISIONS.md:64` - it is a dated historical log and its "Sourced from" statement is accurate as-of-decision (see the plan note under Anti-regression). Optionally add a one-line pointer in `fix-decision-policy.md` naming it canonical if not already clear. | `README.md`, (optional) `fix-decision-policy.md` | Low | README names `fix-decision-policy.md` as the canonical policy and frames `fix-bar.md` as an origin note, not the normative source; the true DECISIONS D4 sourcing history is left intact. Consistent with P8. |
| 3 | D3 | Reframe the `prompts/` bullet in `README.md:30` (and the `ARCHITECTURE.md:23` line) to state its actual role: "a reusable prompt library for the maintainer's AI-aided coding across environments, and a home for generated/reusable prompts - independent of this repo's workflows/commands, which do not consume it." Do NOT mark it historical or superseded. Then (required, per resolved Open Question 2) add a one-line note at the top of `prompts/final-release-validation-executable.md` that its `repository-review/<RUN_ID>/` paths are illustrative of that standalone prompt and not the shipped framework's convention (which is `workflow-artifacts/`, see D19). | `README.md`, `ARCHITECTURE.md`, `prompts/final-release-validation-executable.md` | Low | The `prompts/` role is stated as an independent reusable library; the one-line note is present so no reader mistakes that prompt's example paths for the current framework's `workflow-artifacts/` convention. |
| 4 | D4 | Rename `prompts/older-gerneral-qaqc-prompt-library.md` -> `prompts/older-general-qaqc-prompt-library.md` via `git mv`; update any references. | `prompts/older-gerneral-qaqc-prompt-library.md` | Low | `git mv` done; `grep -rn gerneral .` returns nothing; no dangling links. |
| 5 | D5 | Add a short "Prerequisites" note to the README install section: **Python 3.7 or newer** (verified floor - installer relies only on `from __future__ import annotations`; see Open Question 3), a git repo, and "the installer stages changes but never commits - review and commit them." One or two lines; do not duplicate `ARCHITECTURE.md`. | `README.md` | Low | A novice can go README-only from zero to a staged install and knows to commit; no new drift with ARCHITECTURE (cross-reference, don't copy). |
| 6 | D6 | **Approved (Open Question 5 resolved: yes).** Add a minimal `CONTRIBUTING.md` with a short "when you add/rename a workflow" doc-sync checklist. To respect P8 (single source of truth), the checklist must **link to** `ARCHITECTURE.md`'s "Capability layout" section for the authoritative rules rather than restating them; it enumerates only the steps ("add a subdir + `index.md` manifest row + lens file; run the installer to regenerate shims; confirm README/ARCHITECTURE still accurate") and points to the canonical prose for detail. Keep it tight (KISS) - a checklist, not a process manual. | `CONTRIBUTING.md` (new) | Low | A contributor has one checklist that would have prevented the drift D1-D3 represent; it cross-references `ARCHITECTURE.md` (verified: no normative layout rule is duplicated into `CONTRIBUTING.md`). |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| (none) | - | - | No finding is deferred on Remediation-Risk grounds. Every finding (D1-D6) is proposed as an ordered step; D6 was approved by the maintainer (Open Question 5). | - |

## Scope check

- Over-scope (untraceable to a need; propose removal/deferral): none proposed. Steps
  are confined to correcting inaccuracies and one orphan removal; explicitly avoided
  rewriting the (accurate, strong) architecture/installer docs, and avoided adding new
  doc structure not traceable to a finding.
- Under-scope (needed capability missing; propose adding): the README getting-started
  prerequisites (D5/Step 5) - a needed capability (zero-to-first-success) currently
  missing from the README-only path; proposed for addition. The doc-sync contributor
  checklist (D6/Step 6) is likewise a missing capability, approved by the maintainer and
  included in the plan.

## Required tests / validation

Doc-only plan; validation is verification, not automated tests:

1. Link/reference integrity: `grep -rn` for each removed/renamed target
   (`release-review-final-checks`, `gerneral`) returns no stale references.
2. Accuracy re-check: re-verify each corrected claim against the source of truth -
   `fix-decision-policy.md` is named canonical (D2); `prompts/` is described as an
   independent reusable library and no reader would mistake a prompt's example
   `repository-review/` paths for the shipped `workflow-artifacts/` convention (D3).
3. Novice walk-through: read `README.md` top-to-bottom as a first-time user and confirm
   the install section now states prerequisites and the commit step (D5).
4. `git diff --stat` shows only the intended documentation files changed; no code,
   installer, or workflow-body changes. Confirm `DECISIONS.md` is unchanged (the
   anti-regression rule above forbids editing the historical log).
5. Verify `CONTRIBUTING.md` (Step 6, approved) links to `ARCHITECTURE.md` for the layout
   rules and does not restate them (P8 duplication check).
6. Authoring-style compliance (em-dash convention confirmed in force, Open Question 4):
   verify every changed file introduces no em dashes (use hyphens / parenthetical
   dashes). Active check on all of Steps 1-6.

## Spec / documentation sync

This plan *is* the documentation sync. No user-visible software behavior changes, so no
code specs are affected. After Step 2, ensure `README.md`, `GUIDING_PRINCIPLES.md` P1's
enforcement note, and `fix-decision-policy.md` are mutually consistent, all pointing at
`fix-decision-policy.md` as the canonical/enforced policy.

### Anti-regression: what NOT to change (preserve true history)

`DECISIONS.md` is a **dated historical decision log**. Do not "correct" it to match the
current layout:

- **D4 line 64 ("Sourced from `prompts/fix-bar.md`")** is accurate history - the Fix Bar
  genuinely was sourced from that prompt. Step 2 must NOT delete or weaken this; the
  README is the only place to disambiguate canonical-vs-origin.
- **D5 line 82 and other decisions** describe the older `repository-review/<RUN_ID>/`
  run-artifact layout that predates the `workflow-artifacts/` migration (D19). Those are
  correct as-of-decision records and must be left intact. Only *current-state* docs
  (README, ARCHITECTURE, index, live prompts) get the D3 "illustrative, not current"
  clarification - never the decision log.

This preserves the repository's own durable-knowledge invariant (P4): the "why" history
stays truthful even as the "what" evolves.

## Open questions

1. **Pending-plans location:** **resolved.** Maintainer confirmed `.agents/plans/pending/`
   (the assess.md default) as the convention for assessment IPDs. No change needed.
2. **`prompts/` intent:** Confirmed by the maintainer - `prompts/` is a living,
   reusable prompt library used across AI-aided coding environments and a home for
   generated/reusable prompts; it is intentionally not consumed by this repo's
   workflows. Step 3 reframes the docs accordingly (not "historical"). Sub-question
   **resolved by maintainer: yes** - add the one-line "illustrative of this prompt, not
   the shipped `workflow-artifacts/` convention" note where a prompt uses the old
   `repository-review/` paths (Step 3 covers this).
3. **Python floor for D5/Step 5:** **resolved.** Maintainer confirmed a Python 3 floor
   should be stated. Verified against the installer: the only version-sensitive
   construct is `from __future__ import annotations`
   (`install-workflows.py:54`), which requires **Python 3.7+** and defers the
   `tuple[...]` / `X | None` annotations so they never evaluate at runtime. No
   `match/case`, walrus, runtime `X | Y` unions, `removeprefix/suffix`, or dict `|=`
   are used. State **"Python 3.7 or newer"** in the README prerequisites (Step 5).
4. **Em-dash convention:** **resolved: in force.** Maintainer confirmed the
   "no em dashes in authored markdown" convention still holds. All edits in Steps 1-6
   must use hyphens / parenthetical dashes, never em dashes; validation item 6 is
   active (not N/A) and checks this on every changed file.
5. **CONTRIBUTING.md (D6/Step 6):** **resolved: yes, author it.** Maintainer approved a
   minimal doc-sync checklist. Step 6 is now un-gated and executes as part of the plan
   (linking to ARCHITECTURE for layout rules per P8, not restating them).

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution,
and it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and sync docs.
3. Only then move this IPD out of `pending/` per the project's lifecycle convention.
