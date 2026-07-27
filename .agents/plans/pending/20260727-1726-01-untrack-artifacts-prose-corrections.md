# IPD: correct residual prose defects from the untrack-workflow-artifacts Set execution

- Date: 2026-07-27
- Concern: honest guidance / correctness - the executed untrack-workflow-artifacts Set left five prose defects: two wrong DECISIONS cross-references (D114 instead of D117) and three un-flipped "committed deliverable" assertions (two of which make `00-run-protocol.md` self-contradictory)
- Scope: fix the five residual prose items in `agent_workflows/engine.py` (a docstring line), `ARCHITECTURE.md`, `.agents/workflows/release-review/00-run-protocol.md`, and `.agents/workflows/benchmark/benchmark.md`. Prose-only (one engine docstring, no code logic). Post-execution corrective; the executed Set plans are NOT edited.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-27 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer-requested verification of the executed `untrack-workflow-artifacts` Set (children `20260727-1657-01/02/03`, in `.agents/plans/executed/`). The verification found the code + migration tool correct but five prose defects in the runbook/doc flip (Child 02) and cross-references (Child 01). Per the execution contract, an executed plan is not re-opened; this new corrective IPD closes the gap (an in-place corrective, not an edit to the executed plans).

- 2026-07-27 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no defects, no revisions required. Re-verified all five defect claims at the cited lines (P1 00-run-protocol.md:248, P2 :260 both contradict the correct :285; P3 benchmark.md:167; P4 engine.py:36 and P5 ARCHITECTURE.md:177 cite D114 for the workflow-artifacts policy where D117 is meant) and the not-a-defect ARCHITECTURE.md:183 (legacy-migration history, correct). COMPLETENESS confirmed by grep: the only 'committed deliverable' occurrences in shipped workflows are the three P1-P3 targets plus the already-correct :285, and the only D114 refs are the two P4/P5 targets - so this corrective catches everything. Prose-only, <=5 steps, no code logic, no executed-plan edits, both dual checklists present (D115 duty satisfied). No open questions; no unfixed BLOCKER/HIGH. Readiness: GO - PENDING HUMAN APPROVAL.
## Goal

Make the workflow-artifacts guidance fully consistent by fixing the five residual prose defects the Set execution left: (1-2) correct two DECISIONS cross-references that cite D114 (the dual-checklist decision) where they mean D117 (the workflow-artifacts inversion); (3-4) flip the two remaining `00-run-protocol.md` assertions that still call run artifacts "committed deliverables" and instruct committing them (they currently CONTRADICT the same file's `:285` local-only statement); (5) flip the one remaining `benchmark.md` "committed deliverable" line (which D118 claimed to have flipped but did not).

Why it matters: `00-run-protocol.md` currently tells the agent BOTH to commit run artifacts as deliverables (`:248`, `:260`) and to keep them local-only and not commit them (`:285`) - a shipped self-contradiction that will produce exactly the leaking behavior the Set set out to stop. The wrong D-references misdirect anyone chasing the rationale. All are prose; none change code logic.

## Project conventions discovered (Step 0)

- The workflow-artifacts inversion decisions are D117 (code/docs), D118 (runbooks/setup-repo), D119 (migration tool). D114 is the unrelated dual-checklist decision.
- Verified defect locations (post-execution): `agent_workflows/engine.py:36` and `ARCHITECTURE.md:177` cite "D114" for the local-only-artifacts rationale (should be D117); `00-run-protocol.md:248` ("committed deliverables by default") and `:260` ("commits (run artifacts are committed deliverables)") still assert the old policy while `:285` states the new one; `benchmark/benchmark.md:167` still says "a committed deliverable".
- Verified NOT a defect: `ARCHITECTURE.md:183` "committed history moves" correctly describes the legacy `repository-review/` -> `workflow-artifacts/` git-mv migration (preserving that dir's history), not the go-forward policy - leave it.
- No test pins any of these strings (the suite is green at 445 passed, 1 skipped); this is documentation/docstring prose.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| P1 | MEDIUM | Low | agent running release-review | self-contradiction | `00-run-protocol.md:248` still instructs committing per-phase reports "since run artifacts are committed deliverables by default", contradicting `:285` (local-only, do not commit). | `.agents/workflows/release-review/00-run-protocol.md:248,285` |
| P2 | MEDIUM | Low | agent running release-review | self-contradiction | `00-run-protocol.md:260` (planning-only mode) still says "commits (run artifacts are committed deliverables)", same contradiction. | `.agents/workflows/release-review/00-run-protocol.md:260,285` |
| P3 | LOW | Low | agent running benchmark | un-flipped assertion + false completion claim | `benchmark/benchmark.md:167` still calls the run record "a committed deliverable"; D118's Applied list claims benchmark was flipped but it was not. | `.agents/workflows/benchmark/benchmark.md:167`; DECISIONS D118 |
| P4 | LOW | Low | maintainer / reader | wrong cross-reference | `engine.py:36` cites "(D114)" for the local-only-artifacts policy; the correct decision is D117. | `agent_workflows/engine.py:36` |
| P5 | LOW | Low | maintainer / reader | wrong cross-reference | `ARCHITECTURE.md:177` cites "D114" for the same policy; should be D117. | `ARCHITECTURE.md:177` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | P1,P2 | `00-run-protocol.md`: flip `:248` and `:260` so run artifacts are LOCAL-ONLY working material (not committed deliverables); the section/checkpoint commits are for PRODUCT/tracked changes, not the run-record tree; do not commit or force-add `workflow-artifacts/`. Make the wording consistent with the already-correct `:285`. | `.agents/workflows/release-review/00-run-protocol.md` | Low | no `00-run-protocol.md` line instructs committing run artifacts as deliverables; `:248`/`:260`/`:285` agree |
| 2 | P3 | `benchmark/benchmark.md:167`: change "a committed deliverable" to local-only working material (gitignored; do not commit/force-add), consistent with the other runbooks. | `.agents/workflows/benchmark/benchmark.md` | Low | benchmark run record stated local-only; no "committed deliverable" remains |
| 3 | P4,P5 | Fix the cross-references: `engine.py:36` and `ARCHITECTURE.md:177` cite D117 (not D114) for the local-only-artifacts policy. | `agent_workflows/engine.py`, `ARCHITECTURE.md` | Low | both cite D117; no stray D114 reference for this policy remains |
| 4 | all | Docs/decision sync: a short DECISIONS entry (pin at execution) recording the corrective (residual prose from the Set execution; the five fixes), cross-referencing D117/D118 and the executed children; CHANGELOG only if a user-facing statement changed materially (the policy itself did not change - this is a consistency correction, so a CHANGELOG line is optional/omit if redundant). | `DECISIONS.md`, (CHANGELOG.md if warranted) | Low | DECISIONS entry present; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Editing the executed Set plans (01/02/03) | n/a | policy | Executed plans are not re-opened; this corrective IPD is the record of the gap-close. | n/a |
| Any code-logic change | n/a | scope | The defects are prose/docstring only; `check_gitignore` and the tool are correct. | n/a |

## Scope check

- Over-scope: none - five prose fixes across four files + a DECISIONS note. No code logic, no executed-plan edits.
- Under-scope: MUST flip `00-run-protocol.md:248` and `:260` to remove the self-contradiction (P1/P2); MUST flip `benchmark.md:167` (P3); MUST correct both D114->D117 references (P4/P5); MUST NOT touch `ARCHITECTURE.md:183` (correct as-is); MUST leave the code/tool unchanged.

## Required tests / validation

- Prose only (one engine docstring line, no logic); run `python -m pytest -q` to confirm no regression (expect 445 passed, 1 skipped) and paste actual output. Grep the runbooks for residual "committed deliverable" as INSTRUCTION and confirm only historical/executed-plan/workflow-artifacts-run-record files retain it. Confirm no "D114" reference remains for the workflow-artifacts policy. `aw check-local-leaks .` clean; no em/en dashes.

## Spec / documentation sync

- `.agents/workflows/release-review/00-run-protocol.md`, `.agents/workflows/benchmark/benchmark.md`, `agent_workflows/engine.py`, `ARCHITECTURE.md`, `DECISIONS.md`.

## Open questions

- OQ1 (CHANGELOG line): lean OMIT - the policy did not change (D117/D118 already shipped it); this is a consistency correction. Confirm at execution; add a one-liner only if it aids readers.

## Detailed Implementation Checklist (TODO)

- [ ] **Task 1: Flip `00-run-protocol.md:248` and `:260`** - run artifacts local-only; commits are for product/tracked changes, not the run-record tree; consistent with `:285`.
- [ ] **Task 2: Flip `benchmark/benchmark.md:167`** - run record local-only working material, not a committed deliverable.
- [ ] **Task 3: Fix the D114 -> D117 references** in `engine.py:36` and `ARCHITECTURE.md:177`.
- [ ] **Task 4: DECISIONS entry (pin number)** for the corrective; CHANGELOG only if warranted; no em/en dashes.
- [ ] **Task 5: Validate + commit** - `python -m pytest -q` (paste output), grep-confirm no residual old-policy instruction / no stray D114 ref, leak-clean; path-scoped commit; lifecycle move.

## Validation and cross-check (verify before reporting done)

- [ ] Grep `00-run-protocol.md`: CONFIRM no line instructs committing run artifacts as deliverables; `:248`/`:260`/`:285` are consistent; cite the flipped lines.
- [ ] Open `benchmark/benchmark.md:167`: CONFIRM it states local-only (no "committed deliverable"); cite.
- [ ] Grep for "D114" in `engine.py` + `ARCHITECTURE.md`: CONFIRM no D114 remains for the workflow-artifacts policy (both now D117); cite.
- [ ] CONFIRM `ARCHITECTURE.md:183` (legacy-migration "committed history moves") was left intact.
- [ ] CONFIRM DECISIONS entry present; PASTE the `pytest` summary (expect 445 passed, 1 skipped); leak-clean; no em/en dashes.
- [ ] Report any incomplete/blocked/unverified item EXPLICITLY; do not mark executed otherwise.

## Approval and execution gate

This IPD is a proposal; it MUST be reviewed and approved by a human before execution, and it is NOT auto-executed. It corrects residual prose from the executed `untrack-workflow-artifacts` Set; it does NOT re-open those executed plans and does NOT change code logic. Do NOT claim done or move to `executed/` until every execution item is `- [x]` AND its Validation cross-check item is verified; if any cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`).
2. On human approval, execute, validate (both checklists), sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
