# IPD: flip the workflow-artifacts/ policy in the workflow runbooks + setup-repo

- Date: 2026-07-27
- Concern: honest guidance - every runbook that emits `workflow-artifacts/` must stop calling it a committed deliverable and stop telling agents to track/force-add it; run records are local-only
- Scope: the workflow runbooks that assert the old policy (release-review 00-run-protocol/README/MANIFEST/01-current-state, assess, advise, verify) + `setup-repo` (write the gitignore rule). Prose workflow edits + setup-repo prose; DECISIONS/CHANGELOG.
- Status: executed
- Set: untrack-workflow-artifacts
- Order: 2
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): child 02 of the `untrack-workflow-artifacts` Set (see the `-00-` orchestrator). Depends on child 01 (the new default + DECISIONS rationale). Flips the workflow prose that child 01's code flip must be consistent with.

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001. Verified the cited runbook anchors assert the old policy and that assess states it in MULTIPLE places (:138 AND :184); fixed R2/Step 2 to flip ALL assess mentions (not just :182-184). <=5 steps; both checklists present. Readiness: GO - PENDING HUMAN APPROVAL.

- 2026-07-27 executed (Antigravity): Flipped all workflow runbooks (`release-review`, `assess`, `advise`, `verify`, `benchmark`) and `setup-repo` to specify `workflow-artifacts/` is local-only, gitignored, and never force-added. Added DECISION D118 and CHANGELOG entry.


## Goal

Make every shipped runbook agree with the new default: run records under `workflow-artifacts/` are LOCAL-ONLY working material, gitignored, NOT committed deliverables, and never force-added. Update: the release-review run protocol (`00-run-protocol.md`) and its README/MANIFEST/01-current-state that repeatedly say "committed deliverables by default", "Do NOT add workflow-artifacts/ to .gitignore", and "remove a stale workflow-artifacts/ ignore line"; the assess run-record section; advise's "committed deliverable" line; verify's "committed deliverables (evidence)" line. Have `setup-repo` add the `workflow-artifacts/` gitignore rule when it establishes the lifecycle. Add explicit guidance NOT to `git add -f` / force-track the directory.

Why it matters: child 01 flips the code and default, but release-review in particular currently INSTRUCTS the agent to remove any `workflow-artifacts/` ignore line and commit the run tree - the exact behavior that leaks. Until the runbooks are flipped, the guidance contradicts the new default and the sanitizer.

## Project conventions discovered (Step 0)

- release-review asserts the old policy in many places: `00-run-protocol.md:247,259,284,425,429`; `README.md:39,142,157`; `MANIFEST.md:117`; `01-current-state.md:13,44`. It both commits run artifacts AND removes any ignore line - the strongest assertion to flip.
- assess: `assess/assess.md` run-record section ("committed deliverable ... Do not git-ignore it", per the not-executed IPD F5 at `:182-184`).
- advise: `advise/advise.md:74` ("durable, committed deliverable, consistent with assess").
- verify: `verify/verify.md:76` ("committed deliverables (evidence)").
- setup-repo establishes the lifecycle/scaffolding; adding the `workflow-artifacts/` gitignore rule there is the ocman task's suggestion 2.
- release-review WRITES its own run records under `workflow-artifacts/release-review/<RUN_ID>/`; flipping to local-only changes that workflow's commit behavior (it still creates the records; it just does not commit them by default). Handle its "local setup commit of the initialized run artifacts" language.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| R1 | HIGH | Low | adopter / security | release-review leaks | release-review instructs removing any `workflow-artifacts/` ignore line and committing the run tree - the exact leak-producing behavior; must flip to local-only. | `00-run-protocol.md:284,425,429`; `README.md:142,157`; `MANIFEST.md:117`; `01-current-state.md:13,44` |
| R2 | MEDIUM | Low | contributor | assess/advise/verify | assess/advise/verify call their run records committed deliverables; must state local-only. assess asserts it in MULTIPLE places (at least `:138` "committed deliverables by default" AND `:184` "committed deliverable ... Do not git-ignore it") - flip ALL of them, not just one. | `assess.md:138,184` (F5); `advise.md:74`; `verify.md:76` |
| R3 | MEDIUM | Low | adopter | setup-repo scaffolding | setup-repo should write the `workflow-artifacts/` gitignore rule so a freshly set-up repo is safe by default (ocman #2). | `setup-repo/setup-repo.md` / README |
| R4 | LOW | Low | agent | force-add | Guidance should explicitly say NOT to `git add -f` / force-track `workflow-artifacts/`. | prompt "Implement" bullet 3 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | R1 | release-review: flip all "committed deliverables / do NOT gitignore / remove the stale ignore line / commit the run tree" language to: run records are LOCAL-ONLY working material, `workflow-artifacts/` is gitignored, do NOT commit or force-add it, do NOT remove its ignore line. Reconcile the "local setup commit of initialized run artifacts" step (it no longer commits the run tree; a run may still make product/tracked commits). Cover 00-run-protocol, README, MANIFEST, 01-current-state. | `.agents/workflows/release-review/00-run-protocol.md`, `README.md`, `MANIFEST.md`, `01-current-state.md` | Low | no release-review file says commit/track `workflow-artifacts/` or remove its ignore line; run records stated local-only |
| 2 | R2 | assess/advise/verify: change the run-record wording from "committed deliverable" to LOCAL-ONLY (gitignored working material), consistent with child 01's DECISIONS entry. In assess, flip ALL mentions (verified: `:138` "committed deliverables by default" AND `:184` "committed deliverable ... Do not git-ignore it"), not just one. Resolve the F5 contradiction the not-executed IPD flagged. | `.agents/workflows/assess/assess.md`, `advise/advise.md`, `verify/verify.md` | Low | none of the three calls the run record a committed deliverable (grep the assess file for residual mentions); F5 reconciled |
| 3 | R3,R4 | setup-repo: add `workflow-artifacts/` (with the sensitive-material comment) to the `.gitignore` it establishes; add explicit "never `git add -f`/force-track `workflow-artifacts/`" guidance to the relevant runbook(s). | `.agents/workflows/setup-repo/setup-repo.md` (+ README if it lists gitignore entries) | Low | setup-repo writes the rule; a no-force-add statement is present |
| 4 | all | DECISIONS entry (pin at execution) for the runbook flip + setup-repo rule + no-force-add (child 02 of the Set; depends on 01's default); CHANGELOG. | `DECISIONS.md`, `CHANGELOG.md` | Low | entry present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Code flip + top-level docs | scope | Child 01. | 01. |
| Migration tool + remediation docs | scope | Child 03. | 03. |
| A tracked sanitized run-summary mechanism | functionality | Distinct feature (ocman #4). | Later IPD. |

## Scope check

- Over-scope: none - the runbooks that assert the policy + setup-repo + DECISIONS/CHANGELOG. No code (01), no tool (03).
- Under-scope: MUST flip release-review's commit/track/remove-ignore-line instructions to local-only (R1) and reconcile its setup-commit language; MUST flip assess/advise/verify (R2) and resolve F5; MUST have setup-repo write the rule + a no-force-add statement (R3/R4); MUST stay consistent with child 01's default.

## Required tests / validation

- Prose only; run `python -m pytest -q` (no regression; paste output). Grep the release-review tree + assess/advise/verify + setup-repo and CONFIRM no shipped guidance says commit/track `workflow-artifacts/` or remove its ignore line, that run records are local-only, that setup-repo writes the rule, and that a no-force-add statement exists. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- The release-review runbook files, assess/advise/verify, setup-repo, DECISIONS, CHANGELOG.

## Open questions

- OQ1 (release-review local setup commit): lean it still makes product/tracked commits but no longer commits the `workflow-artifacts/` run tree; confirm exact wording at execution.

## Detailed Implementation Checklist (TODO)

- [x] **Task 1: release-review flip** - 00-run-protocol + README + MANIFEST + 01-current-state: local-only, gitignored, no commit/track/remove-ignore-line; reconcile the setup-commit language.
- [x] **Task 2: assess/advise/verify flip** - run records local-only; resolve F5.
- [x] **Task 3: setup-repo writes the gitignore rule + no-force-add guidance.**
- [x] **Task 4: DECISIONS (pin number) + CHANGELOG**; depends-on-01 noted; no em/en dashes.
- [x] **Task 5: Validate + commit** - `python -m pytest -q` (paste output), grep-confirm no residual old wording, leak-clean, path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [x] Grep the release-review tree: CONFIRM no "committed deliverable" / "do NOT git-ignore" / "remove the stale ignore line" / "commit the run artifacts" remains as INSTRUCTION; cite the flipped lines.
- [x] Open assess/advise/verify: CONFIRM run records are stated local-only (not committed deliverables); F5 reconciled; cite lines.
- [x] Open setup-repo: CONFIRM it writes `workflow-artifacts/` into `.gitignore` and a no-`git add -f`/force-track statement is present; cite lines.
- [x] Consistency: quote the new default from a runbook and confirm it matches child 01's DECISIONS entry.
- [x] CONFIRM DECISIONS + CHANGELOG present; PASTE the `pytest` summary; leak-clean; no em/en dashes.
- [x] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.


## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution. Child 02 of the `untrack-workflow-artifacts` Set; DEPENDS ON child 01 (the new default + DECISIONS rationale; if absent, STOP and report). Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped, never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Confirm child 01 executed first.
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
