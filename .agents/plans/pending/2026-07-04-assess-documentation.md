# IPD: Assess documentation - bring ARCHITECTURE.md and contributor docs current with D31-D37

- Date: 2026-07-04
- Concern: documentation
- Scope: whole repository documentation (root docs + the manifest/prose that documents
  usage). Emphasis fell on ARCHITECTURE.md, which drifted most.
- Status: PENDING (awaiting human approval; not executed)
- Author: assess/documentation harness

## Goal

Make the repository's documentation describe what the toolkit actually does TODAY. Seven
roadmap changes (DECISIONS D31-D37) and an installer hardening (D38) landed after
ARCHITECTURE.md was written, and the command surface changed shape (D31). README and
index.md were kept current during those builds, but ARCHITECTURE.md was not, so it now
teaches an outdated model and omits over half the workflows. Accuracy is the
highest-harm documentation failure (the lens's first rubric item): a newcomer reading
ARCHITECTURE.md would try commands that no longer exist and would not learn about the
verification, advise, lifecycle, discovery, and onboarding workflows at all.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` (present).
- Pending-plans location/format used: `.agents/plans/pending/`; terminal dir
  `.agents/plans/done/` (both exist; this repo uses `done/`).
- Contributor/spec-sync contract: `CONTRIBUTING.md` (has a "Doc-sync checklist" whose
  step 5 already requires keeping README and ARCHITECTURE accurate - the process control
  that was not followed).
- Stack / relevant context: a documentation-and-Python-tooling repo; product = the
  workflow instruction files + three stdlib tools + the installer. Ground truth verified:
  15 command shims/tool, 29 assess concern lenses, 7 advise personas, 3 tools
  (`scan_secrets.py`, `setup_tools.py`, `run_checks.py`), VERSION `20260704-01`.

## Findings

Severity is impact if left alone; Remediation Risk is the Fix-Bar gate. Persona = the
reviewer perspective that surfaced it.

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence (file:line) |
|----|----------|------------------|---------|------|---------|----------------------|
| D-01 | High | Low | software-engineer | accuracy | ARCHITECTURE describes the pre-D31 model ("many commands `/assess-performance`, `/assess-security` share the one harness body"); those are now one `/assess <concern>`. | ARCHITECTURE.md:197-203 |
| D-02 | High | Low | novice | accuracy | ARCHITECTURE's by-tool examples use `/assess-security`, a command that no longer exists. | ARCHITECTURE.md:259 |
| D-03 | High | Low | software-engineer | completeness | ARCHITECTURE omits nine workflows: verify, advise, assess-all, spec, incident, release-notes, migrate, list-workflows, getting-started. | ARCHITECTURE.md:190-253 |
| D-04 | High | Low | software-engineer | accuracy | ARCHITECTURE file tree omits the D33-D37 dirs, `VERSION`, `tests/`, and `run_checks.py`; shim-dir comments name only release-review/plan-review. | ARCHITECTURE.md:26-35 |
| D-05 | Medium | Low | software-engineer | accuracy | No mention of framework versioning (VERSION, `YYYYMMDD-NN`, stamping, `--version`, D32) or the self-tests (`tests/`, D36). | ARCHITECTURE.md (absent) |
| D-06 | Medium | Low | operator | accuracy | `run_checks.py` (the verify evidence engine, D33) is missing from the tools description. | ARCHITECTURE.md:209,242 |
| D-07 | Low | Low | software-engineer | completeness | CONTRIBUTING doc-sync step 3 covers `assess-*` lenses but not the parallel `advise-<persona>` catalog rows. | CONTRIBUTING.md:23-24 |
| D-08 | Low | Low | operator | consistency | Stray Windows `:Zone.Identifier` metadata file in `prompts/`. | prompts/modular-...md:Zone.Identifier |
| D-09 | Low | Low | novice | completeness | No user-facing CHANGELOG despite a versioned framework; DECISIONS is rationale, not a changelog. | repo root; VERSION=20260704-01 |
| D-10 | (positive) | - | software-engineer | accuracy | README/ARCHITECTURE pointer to index.md's "Running a workflow (by tool)" section is correct. | index.md:79 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | D-01, D-02 | Rewrite the assess description to the single parameterized `/assess <concern>` + `assess-<concern>` catalog model; replace all `/assess-<concern>` command examples with `/assess <concern>`. | ARCHITECTURE.md | Low | grep ARCHITECTURE for `assess-` command syntax returns none except catalog/dir references; wording matches README/index.md. |
| 2 | D-03 | Add concise sections for the missing workflows: verify (evidence layer), advise (+personas), assess-all (rollup), the lifecycle four (spec/incident/release-notes/migrate), list-workflows, getting-started. | ARCHITECTURE.md | Low | Every workflow in `index.md` appears in ARCHITECTURE; count reconciles (15 commands). |
| 3 | D-04 | Update the file tree to the current `.agents/workflows/` layout, plus `VERSION`, `tests/`, and the three `tools/*.py`. | ARCHITECTURE.md | Low | Tree entries exist on disk; `ls` cross-check. |
| 4 | D-05, D-06 | Add short subsections on versioning/stamping (D32) and self-tests (D36); add `run_checks.py` to the tools description. | ARCHITECTURE.md | Low | Mentions VERSION scheme, `--version`, `tests/`, and all three tools. |
| 5 | D-07 | Generalize CONTRIBUTING doc-sync step 3 to cover both `assess-<concern>` lenses and `advise-<persona>` personas. | CONTRIBUTING.md | Low | Step names both catalog families. |
| 6 | D-08 | Remove the stray `:Zone.Identifier` file; confirm `.gitignore` guards the pattern. | prompts/, .gitignore | Low | `find . -name '*Zone.Identifier'` (outside .git) returns nothing; pattern in .gitignore. |
| 7 | D-09 | Either add a `CHANGELOG.md` seeded from DECISIONS D31-D38, or add a README line stating DECISIONS.md is the change history and linking it. (Recommend the README pointer; lighter.) | README.md (or new CHANGELOG.md) | Low | README points a user to where to see what changed per version. |

## Deferred / out of scope (with reason)

None. All findings are Low Remediation Risk (documentation edits with no behavior change)
and are proposed for action. D-10 is a positive check requiring no change.

## Scope check

- Over-scope: do not rewrite README or index.md - they are already accurate; only correct
  what has drifted. Do not expand ARCHITECTURE into a tutorial (that is README's job) or
  restate DECISIONS. Keep additions concise (the lens's anti-bloat / Complexity guard).
- Under-scope: ARCHITECTURE must actually cover the current workflow set; a token mention
  is not enough - a maintainer relies on it (CONTRIBUTING points here for the design).

## Required tests / validation

- After editing: `grep -nE "/assess-[a-z]" ARCHITECTURE.md` shows only catalog/dir/prefix
  references, no command examples.
- Every command row in `.agents/workflows/index.md` is represented in ARCHITECTURE.
- File-tree entries all exist (`ls` each).
- Em-dash check: grepping for the em-dash character returns 0 on every edited file.
- No behavior/code change, so no functional tests; this is a docs-only plan.

## Spec / documentation sync

This plan IS documentation sync. No user-visible software behavior changes. After
execution, the doc set (README, ARCHITECTURE, index.md, CONTRIBUTING) should be mutually
consistent and match the shipped D31-D38 state.

## Open questions

1. D-09: add a real `CHANGELOG.md`, or just point to `DECISIONS.md` from the README?
   (Assumption: the README pointer is sufficient and lighter; confirm.)
2. Should the `/release-notes` workflow later own CHANGELOG generation for this repo
   (dogfooding), rather than hand-maintaining it? (Out of scope for this docs plan.)

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and
it is NOT auto-executed. Recommended next steps:

1. Review this IPD (optionally run the `plan-review` workflow to harden it).
2. On approval, execute the ordered changes, run the validation, and confirm doc
   consistency.
3. Only then move this IPD from `.agents/plans/pending/` to `.agents/plans/done/` per this
   repo's lifecycle convention.
