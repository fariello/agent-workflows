# IPD: adopt/test/document the untrack-workflow-artifacts migration tool + remediation guidance

- Date: 2026-07-27
- Concern: safe migration - a repo that already tracks `workflow-artifacts/` needs a safe, opt-in way to stop tracking it (index-only, keep local files, no silent commit), plus guidance for the leak-remediation case
- Scope: verify/adopt `tools/untrack-workflow-artifacts.py`, add tests that exercise it in a temp git repo, document it + the already-committed remediation options, and make any installer migration opt-in/confirmed (detect + offer/document; never silently remove/stage/commit). Tests + docs; light installer wiring if any.
- Status: reviewed
- Set: untrack-workflow-artifacts
- Order: 3
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): child 03 of the `untrack-workflow-artifacts` Set (see the `-00-` orchestrator). Depends on child 01 (the gitignore rule + rationale). The tool `tools/untrack-workflow-artifacts.py` ALREADY EXISTS (5561 bytes) and already implements the required behavior; this IPD ADOPTS/verifies it (adds tests + docs), it does not re-write it.

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no defects. Verified tools/untrack-workflow-artifacts.py already implements the required contract (dry-run default, --apply index-only git rm --cached + stage .gitignore, separate --commit rejecting unrelated staged, refuses dirty .gitignore, idempotent) and has NO tests; this IPD adds tests + docs + opt-in installer. Depends on 01. <=5 steps; both checklists present. Readiness: GO - PENDING HUMAN APPROVAL.

## Goal

Make the migration safe, tested, and documented: (1) VERIFY `tools/untrack-workflow-artifacts.py` implements the required contract - dry-run default; `--apply` does index-only `git rm -r --cached -- workflow-artifacts` (retains local files) + appends the `.gitignore` rule + stages both; separate `--commit` (requires `--apply`) rejects unrelated staged paths; refuses to stage `.gitignore` when it has pre-existing edits; idempotent on already-ignored/untracked; and adjust it only if a verified gap exists; (2) ADD tests exercising it in a temporary git repo covering the prompt's verification cases; (3) DOCUMENT the tool and the already-committed remediation guidance (index-only stop-tracking vs a `filter-repo` history rewrite for repos where the exposure matters; run `aw sanitize` first to size it); (4) make any installer migration OPT-IN/CONFIRMED - the installer may DETECT the old tracked state and OFFER or document the migration, but MUST NOT silently remove tracked files, stage changes, or commit.

Why it matters: flipping the default (01/02) stops future tracking, but existing repos have `workflow-artifacts/` in their index (and history); they need a safe, reviewable path to stop tracking without losing local files or triggering an unexpected commit. The tool exists; it must be proven and documented.

## Project conventions discovered (Step 0)

- `tools/untrack-workflow-artifacts.py` (verified read): dry-run default; `--apply` -> `git rm -r --cached --ignore-unmatch -- workflow-artifacts` + `append_ignore_rule` (comment + `workflow-artifacts/`) + `git add -- .gitignore`; `--commit` requires `--apply`, and `acceptable_commit_paths` rejects any staged path outside `.gitignore`/`workflow-artifacts`; `gitignore_is_clean` refuses to stage a `.gitignore` with pre-existing staged/unstaged edits; idempotent (skips if the rule is present / nothing tracked). This matches the prompt's migration behavior already.
- Test precedent: stdlib `unittest` + a temp git repo (see `tests/support.py` `init_repo`, and the many installer tests). A `tests/test_untrack_workflow_artifacts.py` fits.
- The tool's `IGNORE_COMMENT`/`IGNORE_RULE` should MATCH the comment child 01/02 use, for consistency.
- Installer: the existing posture is "do not silently edit a user's tracked `.gitignore`"; any migration offer must preserve that (detect + document/offer only).

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| T1 | HIGH | Low | maintainer | untested safety-critical tool | The migration tool does index-only removal + stages `.gitignore` + can commit; it is safety-critical (must never delete local files or commit unrelated changes) but has NO tests. | `tools/untrack-workflow-artifacts.py` (no matching test file) |
| T2 | MEDIUM | Low | adopter | remediation guidance | Repos that already committed `workflow-artifacts/` need documented options (index-only vs history rewrite) and a pointer to `aw sanitize` to size the exposure (ocman #3); none exists. | ocman task `:50-55` |
| T3 | MEDIUM | Low | adopter / security | installer must not silently mutate | Any installer migration must be opt-in/confirmed and never silently remove/stage/commit (prompt "Make migration installer-supported but opt-in"). | prompt "Implement" bullet 5 |
| T4 | LOW | Low | maintainer | comment/rule consistency | The tool's ignore comment/rule should match what child 01/02 write, so migrated and freshly-set-up repos look identical. | `untrack-workflow-artifacts.py:19-23` vs child 01/02 wording |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | T1,T4 | Verify the tool against the required contract; fix only a verified gap; align its `IGNORE_COMMENT`/`IGNORE_RULE` with child 01/02's wording if they differ. | `tools/untrack-workflow-artifacts.py` (only if a gap) | Low | tool matches the contract; comment/rule consistent with 01/02; any change minimal + justified |
| 2 | T1 | Add `tests/test_untrack_workflow_artifacts.py` (temp git repo) covering the prompt's verification cases: a repo with tracked `workflow-artifacts/` ends with the dir still present locally but removed from the index + `.gitignore` rule staged; dry run makes NO changes; already-untracked/ignored is idempotent; `--commit` refuses when unrelated files are staged; refuses to stage a dirty `.gitignore`. | `tests/test_untrack_workflow_artifacts.py` (new) | Low | tests cover all listed cases; full suite green; paste actual output |
| 3 | T2 | Document the tool + remediation guidance: how to run it (dry-run then `--apply`, optional `--commit`), and for already-committed repos the two options (index-only stop-tracking; `filter-repo` history rewrite where the exposure matters) with "run `aw sanitize` first to size it". Home: the tool's usage in a docs/README location + a note in the setup/migrate guidance. | a docs location (e.g. `tools/README` or `.agents/docs/`), cross-ref from setup-repo | Low | tool documented; both remediation options + `aw sanitize`-first present |
| 4 | T3 | Installer migration is opt-in/confirmed: if the installer detects a repo tracking `workflow-artifacts/` without the ignore rule, it may PRINT an advisory pointing at the tool/migration (detect + offer/document), but MUST NOT run the removal, stage, or commit automatically. (Light wiring; if the cleanest form is documentation-only for now, do that and note it.) | `agent_workflows/engine.py` or `cli.py` (advisory only) or docs | Low | installer never silently removes/stages/commits; at most an advisory pointer; a test/None-op confirms no silent mutation |
| 5 | all | DECISIONS entry (pin at execution) for the migration tool + remediation guidance + opt-in installer posture (child 03; depends on 01); CHANGELOG. | `DECISIONS.md`, `CHANGELOG.md` | Low | entry present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Building a history-rewrite (filter-repo) tool | complexity/safety | Destructive, repo-specific; document the option, do not build it (prompt bounds the tool to index-only). | Separate IPD only if needed. |
| Code/doc/runbook flips | scope | Children 01/02. | 01/02. |
| Remediating this repo's own committed history | scope | Separate operational task. | Operational, sanitizer-sized first. |

## Scope check

- Over-scope: none - verify/adopt the existing tool + tests + docs + an opt-in (or documented) installer advisory + DECISIONS/CHANGELOG. No history-rewrite tool; no re-writing the tool from scratch; no silent installer mutation.
- Under-scope: MUST test the tool's safety-critical behavior in a temp repo (index-only, local files retained, dry-run no-op, idempotent, `--commit` rejects unrelated, refuses dirty `.gitignore`) (T1); MUST document both remediation options + `aw sanitize`-first (T2); MUST keep any installer migration opt-in/confirmed with no silent removal/stage/commit (T3); MUST align the tool's comment/rule with 01/02 (T4).

## Required tests / validation

- `python -m pytest -q` including the new `tests/test_untrack_workflow_artifacts.py`; paste actual output. The tests demonstrate: tracked -> local-present + index-removed + rule staged; dry-run no-op; idempotent; `--commit` refuses unrelated staged; refuses dirty `.gitignore`. Confirm the installer never silently mutates (advisory/None-op test or documented-only). `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `tools/untrack-workflow-artifacts.py` (if adjusted), `tests/test_untrack_workflow_artifacts.py`, a tool/remediation doc, setup-repo cross-ref, DECISIONS, CHANGELOG.

## Open questions

- OQ1 (installer advisory vs documentation-only): lean a minimal detect-and-advise (no mutation); if wiring it cleanly is disproportionate, ship documentation-only and note it. Confirm at execution.
- OQ2 (tool/doc home): lean a `tools/`-level usage note + a pointer from setup-repo/migrate guidance. Confirm at execution.

## Detailed Implementation Checklist (TODO)

- [ ] **Task 1: Verify the tool** against the contract; align its ignore comment/rule with 01/02; fix only a verified gap.
- [ ] **Task 2: Add `tests/test_untrack_workflow_artifacts.py`** (temp repo) covering tracked->removed+local-kept, dry-run no-op, idempotent, `--commit` rejects unrelated, refuses dirty `.gitignore`.
- [ ] **Task 3: Document the tool + remediation** (dry-run/apply/commit; index-only vs history-rewrite; `aw sanitize` first).
- [ ] **Task 4: Installer opt-in/confirmed** advisory (or documented-only) - never silently remove/stage/commit; confirm with a test or note.
- [ ] **Task 5: DECISIONS (pin number) + CHANGELOG**; run `python -m pytest -q` and PASTE output; leak-clean; path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [ ] Run the new tests: PASTE the actual `pytest` output; CONFIRM tracked->index-removed-with-local-kept, dry-run no-op, idempotent, `--commit` rejects unrelated staged, refuses dirty `.gitignore`.
- [ ] CONFIRM the tool is dry-run default, `--apply` index-only, `--commit` separate + requires `--apply`; cite the relevant lines; confirm its comment/rule matches 01/02.
- [ ] CONFIRM the remediation doc covers index-only AND history-rewrite options + `aw sanitize`-first; cite the path.
- [ ] CONFIRM the installer never silently removes/stages/commits (advisory-only or documented-only); cite the code/None-op test or the doc.
- [ ] CONFIRM DECISIONS + CHANGELOG present; leak-clean; no em/en dashes.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.

## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution. Child 03 of the `untrack-workflow-artifacts` Set; DEPENDS ON child 01 (the gitignore rule/comment + rationale; if absent, STOP and report). Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (no history-rewrite tool; no silent installer mutation; do not delete local artifact files). Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Confirm child 01 executed first.
2. On human approval, execute, validate (both checklists + the tool's temp-repo tests), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
