# IPD: flip the workflow-artifacts/ policy in product code + top-level docs + the repo .gitignore

- Date: 2026-07-27
- Concern: data-exposure safety - invert the "workflow-artifacts/ is a committed deliverable" default in the code that checks it and in the top-level docs, and add the ignore rule to this repo's own `.gitignore`
- Scope: `agent_workflows/engine.py` (`check_gitignore` + the two docstring mentions), the repo root `.gitignore`, `ARCHITECTURE.md`, `README.md`, DECISIONS + CHANGELOG. Product-code touch limited to `check_gitignore` + docstrings.
- Status: executed
- Set: untrack-workflow-artifacts
- Order: 1
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): child 01 of the `untrack-workflow-artifacts` Set (see the `-00-` orchestrator). Flips the code + top-level docs; runbooks are child 02, the migration tool is child 03.

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-002. Verified `check_gitignore` at engine.py:1916-1932 asserts the old policy, and that NO test pins its strings (only a stub `""` at tests/test_cli.py:113), so the flip is no-regression; recorded that in the validation. <=5 steps; both checklists present. Readiness: GO - PENDING HUMAN APPROVAL.

- 2026-07-27 executed (Antigravity): Inverted `check_gitignore` in `agent_workflows/engine.py`, updated docstring line 35, updated `.gitignore` comment, updated `ARCHITECTURE.md` and `README.md`, added DECISION D117 and CHANGELOG entry.


## Goal

Invert the framework's default for `workflow-artifacts/` in the places child 02/03 build on: (1) `check_gitignore` currently WARNS when `.gitignore` ignores `workflow-artifacts/` ("run artifacts are committed deliverables; remove that ignore line") and reports "not ignored (correct)"; flip it so ignoring `workflow-artifacts/` is the EXPECTED/correct state and the absence of the rule is what it notes (optionally as an install-time nudge), without the installer silently editing the user's `.gitignore`; (2) fix the two `engine.py` docstring mentions ("Does NOT git-ignore... committed deliverables"); (3) add `workflow-artifacts/` to THIS repo's root `.gitignore` with a concise sensitive-material comment; (4) update `ARCHITECTURE.md` + `README.md` prose that call run artifacts committed deliverables.

Why it matters: the code that checks `.gitignore` actively steers users to commit a directory the sanitizer flags as leaking home paths/usernames/session ids. Flipping the check + docs is the foundation the runbook flip (02) and the migration tool (03) reference.

## Project conventions discovered (Step 0)

- `check_gitignore` (`engine.py:1916-1932`): returns "will be tracked (correct)" / "not ignored (correct)" and WARNS if `workflow-artifacts/` (or the legacy `repository-review/`) is ignored. This is the code assertion of the old policy.
- Docstrings: `engine.py:35` ("Does NOT git-ignore... committed deliverables") and `:125` ("local scratch, not a committed deliverable" - already correct-ish for backups; verify context).
- The installer today does NOT modify a target repo's tracked `.gitignore` for artifacts (only `ensure_backups_gitignored` touches it, for the backups dir). Keep that no-silent-edit posture: flipping the check must not make the installer auto-write the artifacts rule into a user's tracked `.gitignore` (that is the migration tool's opt-in job, child 03; setup-repo writing it is child 02's scaffolding decision).
- `ARCHITECTURE.md:177,184` and `README.md:243` describe run artifacts as committed deliverables.
- Complements the `.untracked.` convention (D105) and the leak-sanitizer; does not conflict.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| W1 | HIGH | Low | adopter / security | leak default | `check_gitignore` steers users to COMMIT `workflow-artifacts/`, which the sanitizer flags (~8,472 FAILs reported by ocman); the check must be inverted so ignoring it is correct. | `engine.py:1916-1932`; ocman task `.agents/comms/shared/inbox/20260726-1616-01-...` |
| W2 | MEDIUM | Low | maintainer | code docstrings | The engine docstrings assert the old "committed deliverables / does not git-ignore" policy. | `engine.py:35`, `:125` |
| W3 | LOW | Low | maintainer | this repo's own state | This repo's `.gitignore` does not ignore `workflow-artifacts/`, so the repo itself carries the exposure the policy warns about elsewhere. | root `.gitignore` (no `workflow-artifacts/` rule) |
| W4 | LOW | Low | contributor | top-level docs | ARCHITECTURE.md + README.md still call run artifacts committed deliverables. | `ARCHITECTURE.md:177,184`; `README.md:243` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | W1 | Invert `check_gitignore`: ignoring `workflow-artifacts/` is the EXPECTED/correct state; if the rule is present, report it as correct (local-only, sensitive working material); if absent, note it as an advisory (the run records will be tracked - the OLD, risky behavior) WITHOUT the installer editing the user's `.gitignore`. Keep the legacy `repository-review/` handling consistent. Update the status strings accordingly. | `agent_workflows/engine.py` | Low | `check_gitignore` treats ignored as correct + advises when absent; no silent `.gitignore` edit; any test asserting the old strings updated consciously |
| 2 | W2 | Fix the `engine.py` docstrings that assert "committed deliverables / does not git-ignore" to state the new default (run artifacts are LOCAL-ONLY working material; the installer does not commit them). | `agent_workflows/engine.py` | Low | docstrings reflect the new default; no stale "committed deliverable" claim in engine prose |
| 3 | W3 | Add `workflow-artifacts/` to THIS repo's root `.gitignore` with a concise comment (agent-generated working material; may contain local paths / private references / sensitive detail; do not commit). Do NOT delete the local dir. (Remediating this repo's already-committed history is a separate operational task, deferred by the orchestrator.) | `.gitignore` | Low | root `.gitignore` ignores `workflow-artifacts/` with the comment; local dir untouched |
| 4 | W4 | Update `ARCHITECTURE.md` + `README.md` prose: run artifacts are local-only working material, not committed deliverables; cross-reference the DECISIONS entry. | `ARCHITECTURE.md`, `README.md` | Low | no top-level doc calls `workflow-artifacts/` a committed deliverable |
| 5 | W1 | DECISIONS entry (pin at execution) recording the reversal (why: leak exposure + sanitizer contradiction + low provenance value; the new default; installer does not silently edit `.gitignore`; migration is the tool's opt-in job) - SUPERSEDES the prior D92/D93-era "committed deliverable" stance; CHANGELOG. Note children 02 (runbooks/setup-repo) and 03 (tool). Cross-reference the ocman task + prompt. | `DECISIONS.md`, `CHANGELOG.md` | Low | entry present; supersedes the old stance; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Runbook flips (release-review/assess/advise/verify) + setup-repo | scope | Child 02. | 02. |
| The migration tool + remediation docs + installer opt-in | scope | Child 03. | 03. |
| Rewriting this repo's committed `workflow-artifacts/` history | safety | Destructive/operational; orchestrator deferral. | Separate operational task. |

## Scope check

- Over-scope: none - `check_gitignore` + docstrings + this repo's `.gitignore` + two top-level docs + DECISIONS/CHANGELOG. No runbook edits (02), no tool (03), no history rewrite, no silent installer `.gitignore` edit.
- Under-scope: MUST invert `check_gitignore` so ignored is correct and MUST NOT make the installer silently edit a user's `.gitignore` (W1); MUST fix the engine docstrings (W2); MUST add the rule to this repo's `.gitignore` without deleting the local dir (W3); MUST update the top-level docs (W4); MUST record a DECISIONS entry that supersedes the old stance.

## Required tests / validation

- Run `python -m pytest -q`; VERIFIED at review time that NO test currently pins `check_gitignore`'s strings/behavior (the only `gitignore_status` reference is a stub placeholder `""` at `tests/test_cli.py:113`), so the flip is expected to be no-regression; if that changes, update the pinned test CONSCIOUSLY and record it. Confirm `check_gitignore` reports ignored-as-correct and advises-when-absent with no silent edit; the repo `.gitignore` ignores `workflow-artifacts/` with the comment; ARCHITECTURE/README no longer call it a committed deliverable; DECISIONS/CHANGELOG present. `aw check-local-leaks .` clean; no em/en dashes; paste actual test output.

## Spec / documentation sync

- `agent_workflows/engine.py`, `.gitignore`, `ARCHITECTURE.md`, `README.md`, DECISIONS, CHANGELOG.

## Open questions

- OQ1 (installer nudge when the rule is absent): lean an advisory status only (never a silent edit); setup-repo may write the rule (child 02). Confirm wording at execution.

## Detailed Implementation Checklist (TODO)

- [x] **Task 1: Invert `check_gitignore`** (`engine.py`): ignored = correct; absent = advisory (old risky behavior), no silent `.gitignore` edit; legacy `repository-review/` consistent; status strings updated.
- [x] **Task 2: Fix engine docstrings** (`:35`, `:125` context) to the new local-only default.
- [x] **Task 3: Add `workflow-artifacts/` to this repo's `.gitignore`** with the sensitive-material comment; do not delete the local dir.
- [x] **Task 4: Update `ARCHITECTURE.md` + `README.md`** prose (local-only, not committed deliverables).
- [x] **Task 5: DECISIONS (pin number) + CHANGELOG**; supersede the old stance; run `python -m pytest -q` (update any pinned test consciously) and PASTE output; leak-clean; path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [x] Open `check_gitignore`: CONFIRM ignored-is-correct + absent-is-advisory + no silent `.gitignore` edit; cite lines; quote the new status strings.
- [x] CONFIRM the engine docstrings no longer claim "committed deliverables / does not git-ignore" for artifacts; cite lines.
- [x] CONFIRM the repo root `.gitignore` ignores `workflow-artifacts/` with the comment and the local dir still exists; show the diff + `ls`.
- [x] CONFIRM `ARCHITECTURE.md` + `README.md` no longer call run artifacts committed deliverables; cite lines.
- [x] CONFIRM DECISIONS supersedes the old stance + CHANGELOG present; PASTE the `pytest` summary (note any consciously-updated test); leak-clean; no em/en dashes.
- [x] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.


## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution. Child 01 of the `untrack-workflow-artifacts` Set; no dependency. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped, never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (no runbook edits, no tool, no history rewrite, no silent installer `.gitignore` edit). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`. Then children 02 and 03.
