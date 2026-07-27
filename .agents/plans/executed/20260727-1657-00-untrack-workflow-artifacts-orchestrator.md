# IPD (ORCHESTRATOR): reverse the workflow-artifacts/ tracking policy (gitignore it; local-only)

- Date: 2026-07-27
- Concern: data-exposure safety / honest defaults - `workflow-artifacts/` is a high-risk, low-value working dir where agents demonstrably embed home paths, usernames, hostnames, and session ids; the toolkit currently tells users to COMMIT it, contradicting its own leak-sanitizer. Reverse the policy: gitignore it, keep it local-only, and ship a safe migration.
- Scope: ORCHESTRATOR for the ordered Set `untrack-workflow-artifacts`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It makes no file edits itself.
- Status: executed
- Set: untrack-workflow-artifacts
- Order: 0
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer prompt (`.agents/prompts/pending/20260727-0655-01-untrack-workflow-artifacts.prompt.md`) reversing the "commit workflow-artifacts/" policy, corroborated by an untracked inbox task (`ocman.agent`, `.agents/comms/shared/inbox/20260726-1616-01-...`) reporting ~8,472 leak-sanitizer FAILs concentrated in `workflow-artifacts/`, and by the not-executed IPD `20260719-2354-01` (F5) that flagged the contradiction. Shaped as a `00`-orchestrated Set because the policy is asserted across product code + the whole release-review runbook + assess/advise/verify + top-level docs + a migration tool + tests (well past the <=5-step single-IPD guidance, D114/D116). The existing `tools/untrack-workflow-artifacts.py` is ADOPTED/verified, not re-written.

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (02), PR-002 (01). Reviewed all four serially (single-file variant on a 4-plan batch, by invocation). Verified claims from files: engine `check_gitignore` `:1916-1932`; the release-review/assess/advise/verify old-policy assertions (00-run-protocol :284, MANIFEST :117, advise :74, verify :76, assess :138 + :184); the tool `tools/untrack-workflow-artifacts.py` already implements the required index-only contract. Cross-IPD consistency holds; prompt<->ocman reconciliation coherent (tool index-only; history-rewrite documented not built); migration-safety invariant preserved; each child <=5 steps; all four carry both checklists (D115 duty satisfied). No open questions blocking; no unfixed BLOCKER/HIGH. Readiness: GO - PENDING HUMAN APPROVAL.

- 2026-07-27 executed (Antigravity): Orchestrated and verified completion of Set `untrack-workflow-artifacts` (Children 01, 02, and 03 executed and committed). Code, top-level docs, workflow runbooks, setup-repo, and migration tool are aligned on local-only, gitignored `workflow-artifacts/`. Full test suite green, leak-clean.

## Goal

Coordinate the reversal so it lands coherently while each child stays small and independently verifiable: (01) flip the policy in PRODUCT CODE + top-level docs + the repo `.gitignore`; (02) flip it in every WORKFLOW runbook and have `setup-repo` write the gitignore line; (03) adopt + test + document the `tools/untrack-workflow-artifacts.py` migration utility and the already-committed remediation guidance. After all three, the toolkit's guidance, code, and tool agree: `workflow-artifacts/` is local-only, gitignored, never force-added, with a safe opt-in migration.

Why it matters: committing `workflow-artifacts/` publishes machine-identifying info to repo history that is hard to scrub, for scratch records whose durable value lives elsewhere (the IPD, CHANGELOG/DECISIONS, code+tests). The sanitizer already flags exactly this, so the framework contradicts its own tool. The migration must be SAFE (index-only, never delete local files, never silently commit).

## Reconciliation of the prompt and the ocman task

The prompt and the ocman task agree on the flip + a safe index-only migration. Where they differ: the ocman task frames already-committed `workflow-artifacts/` as a LEAK to remediate (possibly a history rewrite), while the prompt scopes the tool to index-only stop-tracking and "must not delete local files." Reconciled: the TOOL does index-only stop-tracking only (never deletes, never rewrites history); child 03 DOCUMENTS the fuller remediation options (index-only vs `filter-repo` history rewrite) and recommends running `aw sanitize` first to size the exposure, but building a history-rewrite tool is OUT OF SCOPE (deferred). This respects the prompt's safety bound while capturing ocman's leak-remediation concern as guidance.

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260727-1657-01-untrack-policy-code-and-docs.md` | Flip the policy in product code (`engine.py check_gitignore` + docstrings), the repo root `.gitignore` (add `workflow-artifacts/` with a sensitive-material comment), `ARCHITECTURE.md`, `README.md`; DECISIONS + CHANGELOG. | none |
| 02 | `20260727-1657-02-untrack-policy-runbooks.md` | Flip the policy in the workflow runbooks (release-review 00-run-protocol/README/MANIFEST/01-current-state, assess, advise, verify) so run records are local-only, not committed deliverables, and never force-added; have `setup-repo` write the `workflow-artifacts/` gitignore line. | 01 (the DECISIONS rationale + the new default) |
| 03 | `20260727-1657-03-migration-tool-and-remediation.md` | Adopt/verify `tools/untrack-workflow-artifacts.py` (index-only, dry-run default, opt-in `--apply`, separate `--commit`), add tests in a temp repo, document it + the already-committed remediation guidance (index-only vs history rewrite; run `aw sanitize` first); make installer migration opt-in/confirmed (detect + offer/document, never silently remove/stage/commit). | 01 (the gitignore rule + rationale) |

## Completion criteria (the whole Set is done only when)

- 01 executed: `check_gitignore` no longer warns that ignoring `workflow-artifacts/` is wrong (it expects/accepts it ignored); the repo `.gitignore` has the rule + comment; ARCHITECTURE/README updated; DECISIONS entry present.
- 02 executed: no runbook instructs committing `workflow-artifacts/` or removing its ignore line; run records are local-only; `setup-repo` writes the gitignore rule; no "force-add" encouragement.
- 03 executed: the migration tool is verified + tested (temp-repo tests pass) + documented; the already-committed remediation guidance + `aw sanitize`-first pointer exist; installer migration is opt-in/confirmed and never silently removes/stages/commits.
- Cross-IPD validation passes; suite green after each child and at the end; leak-clean; no em/en dashes.

## Cross-IPD validation

- Consistency: after all three, code (`check_gitignore`), the repo `.gitignore`, the runbooks, `setup-repo`, and the tool/docs all agree that `workflow-artifacts/` is local-only/gitignored (no residual "committed deliverable"/"do not git-ignore it" in shipped guidance). Grep for the old wording and confirm only historical/executed-plan/workflow-artifacts-run-record files retain it.
- No contradiction with the leak-sanitizer or the existing `.untracked.` convention (D105); this is a whole-class default, complementary.
- Migration safety invariant holds end to end: index-only, local files retained, never a silent commit; the tool's temp-repo tests demonstrate it.
- Size check: each child <=5 major steps.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| A history-rewrite (filter-repo) tool to purge already-committed artifacts | complexity/safety | Destructive, repo-specific; the prompt bounds the tool to index-only. Document the option; do not build it. | A separate IPD only if a real need arises. |
| Remediating THIS repo's own already-committed `workflow-artifacts/` history | scope | A separate operational decision (this Set changes the framework default + tool, not this repo's history). | A separate operational task, sanitizer-sized first. |
| A tracked, sanitized run-summary mechanism (ocman suggestion 4) | functionality | Distinct feature (write a sanitized summary to `.agents/docs/`); not required to flip the default. | Later IPD if wanted. |

## Scope check

- Over-scope: none - orchestrator coordinates; children make bounded edits; no history rewrite.
- Under-scope: the Set MUST flip the policy in code+docs (01), runbooks+setup-repo (02), and adopt/test/document the safe migration + remediation guidance (03), kept consistent, honoring the prompt's safety bounds and reconciling the ocman task.

## Required tests / validation

- Product code touch is limited to `engine.py check_gitignore` + docstrings (01) and the tool/tests (03); the rest is prose/config. Run `python -m pytest -q` after each child (paste actual output); the tool gets temp-repo tests (03). `aw check-local-leaks .` clean; no em/en dashes.

## Open questions

- OQ1 (Set vs one IPD): RESOLVED (maintainer) - a `00`-orchestrated Set (large multi-file policy reversal; dogfoods the new size/orchestrator convention).
- OQ2 (history remediation): RESOLVED (reconciliation above) - tool is index-only; history rewrite is documented guidance, not built.

## Detailed Implementation Checklist (TODO)

- [x] **Child 01 executed** (code + top-level docs + repo `.gitignore` + DECISIONS/CHANGELOG); its own checklists verified.
- [x] **Child 02 executed** (runbooks + setup-repo), after 01; its checklists verified.
- [x] **Child 03 executed** (migration tool + tests + remediation docs + opt-in installer), after 01; its checklists verified.
- [x] **Cross-IPD validation run** (consistency; no residual "committed deliverable" in shipped guidance; migration-safety invariant; size).
- [x] **Suite green** after the last child (`python -m pytest -q`, actual output pasted); leak-clean; no em/en dashes.

## Validation and cross-check (verify before reporting the Set complete)

- [x] 01 done: `check_gitignore` inverted + repo `.gitignore` rule present + ARCHITECTURE/README updated + DECISIONS entry; cite lines.
- [x] 02 done: grep the runbooks + setup-repo and CONFIRM no shipped guidance says commit/track `workflow-artifacts/` or remove its ignore line, and setup-repo writes the rule; cite.
- [x] 03 done: temp-repo tests for the tool pass (paste output); tool is dry-run default + `--apply` index-only + separate `--commit`; remediation + `aw sanitize`-first guidance present; installer migration opt-in/confirmed.
- [x] Consistency: quote the new default from code, a runbook, and the tool docs and confirm they agree; grep confirms only historical files retain the old wording.
- [x] Paste the final `pytest` summary line; leak-clean; no em/en dashes. Report any child incomplete/blocked/unverified EXPLICITLY; do not mark the Set complete otherwise.


## Approval and execution gate

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and cross-IPD validation passes. Do NOT mark done or move to `executed/` until every item in the relevant Validation and cross-check checklist is verified with concrete evidence; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds a plan's scope (in particular, do NOT rewrite git history or delete local artifact files). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review this orchestrator + the three children (optionally `/plan-review`).
2. On human approval, execute 01 -> (02 and 03, both depend only on 01) in order; commit path-scoped (no push).
3. Set each child's terminal `Status: executed` and `git mv` to `.agents/plans/executed/`; when all three pass + cross-IPD validation, complete this orchestrator.
