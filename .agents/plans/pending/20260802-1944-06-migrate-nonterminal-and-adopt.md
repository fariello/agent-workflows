# IPD: migrate nonterminal IPDs, dogfood, and adopt (Set `ipd-structure`, Order 6)

- Date: 2026-08-02
- Kind: child
- Concern: complete adoption: migrate or quarantine this repo's nonterminal IPDs to the new schema, dogfood `aw ipd lint` across the repo (nonterminal pass; terminal grandfathered), and record the convention (docs + DECISIONS pointer + thin AGENTS.md pointer).
- Scope: migration of nonterminal plans + dogfood + adoption docs. No new tool/linter logic. Requires Orders 01 to 05 executed; if their tools/wiring are absent, STOP.
- Status: reviewed
- Set: ipd-structure
- Order: 6
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): final child of Set `ipd-structure`; proves the convention on the repo's own plans and records adoption.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no findings (deps 01-05 correct; migrate/quarantine + dogfood + grandfather + thin AGENTS pointer match spec Sections 12/13; relies on Order 02's legacy disposition, now explicitly owned there per PR-003). Bootstrap manual preflight. GO - PENDING HUMAN APPROVAL.

## Goal

Every nonterminal IPD in this repo conforms to the new schema (or is explicitly quarantined); `aw ipd lint` passes on them and reports terminal `executed/` plans as grandfathered (not conforming); the convention is documented with a DECISIONS pointer and a thin, token-economical AGENTS.md pointer. Spec Sections 12, 13.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: migrate nonterminal plans

- [ ] E-01 inventory nonterminal IPDs (`.agents/plans/pending/`, `approved`, `reusable` if any) and migrate each to the new schema via `aw ipd sync` (assign `E-*`/`V-*`, add state fields, structured `OQ-*`, size-assessment), or explicitly quarantine ones not being pursued.
  - Depends on: none
  - Expected outcome: every nonterminal IPD either conforms or is quarantined with a recorded reason; the research-org Set 00-07 is NOT re-authored here (it is the immediate post-Set follow-up).
  - Execution state: pending
- [ ] E-02 dogfood: run `aw ipd lint` across the repo; nonterminal IPDs pass; terminal `executed/` plans return the explicit `legacy/not evaluated` disposition, not a false pass.
  - Depends on: E-01
  - Expected outcome: paste dogfood output showing the nonterminal/terminal split.
  - Execution state: pending

### Task group 2: adoption docs

- [ ] E-03 add a DECISIONS pointer entry (pin number at execution) referencing the spec; note it revises the "near" placement wording, adds the E-*/V-* bijection + linter, and fixes F-07/F-08/F-09; grandfathers terminal plans.
  - Depends on: E-01
  - Expected outcome: DECISIONS entry present, short, points to the spec.
  - Execution state: pending
- [ ] E-04 add a thin AGENTS.md pointer (one line, F6 token economy) to the `aw ipd` verbs ("scaffold/sync/lint an IPD; do not hand-number ids or hand-place checklists"); regenerate AGENTS.md to an empty diff except the pointer; leave the AGENT-PLANS sibling byte-identical.
  - Depends on: none
  - Expected outcome: `git diff -- AGENTS.md` shows only the pointer line; AGENT-PLANS unchanged.
  - Execution state: pending
- [ ] E-05 run `python -m pytest -q` and `aw ipd lint` dogfood; paste both.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: suite green; dogfood clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Nonterminal plans live in `.agents/plans/pending/` (and `approved`/`reusable` if present); terminal in `executed/`/`superseded/`/`not-executed/`.
- The always-loaded block is `agents_pointer_prose()` in `agent_workflows/engine.py`, regenerated into AGENTS.md via the sectioned path; a refresh MUST be an empty diff and MUST NOT disturb the `AGENT-PLANS` sibling (established pattern).
- DECISIONS entries are short pointers to specs (e.g. D112 -> ipd-spec); keep depth in the spec.
- Grandfathering: terminal plans are not retrofitted (spec Section 13.2).
- No em/en dashes in authored Markdown.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C6-1 | HIGH | Medium | maintainer | dogfood | The convention is unproven until the repo's own nonterminal plans conform and lint clean. | spec Section 13 |
| C6-2 | MEDIUM | Low | weak-agent | discovery | Agents must discover the `aw ipd` verbs at near-zero permanent token cost (thin pointer). | spec Section 4.11 of the research/F6 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C6-1 | migrate/quarantine nonterminal IPDs | `.agents/plans/pending/**` | Medium | E-01, E-02 dogfood |
| 2 | C6-1 | DECISIONS pointer | `DECISIONS.md` | Low | E-03 |
| 3 | C6-2 | thin AGENTS.md pointer | `agent_workflows/engine.py`, `AGENTS.md` | Low | E-04 empty-diff |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | scope | Re-authoring the research-org Set (00-07) to the new shape is the immediate post-Set follow-up, not part of this child. | Right after this Set |
| n/a | n/a | functionality | Terminal `executed/` plans are grandfathered, not migrated. | Only if later justified |
| n/a | n/a | usability | Pre-commit/CI hook wiring deferred. | Follow-up |

## Scope check

- Over-scope: none - migrate nonterminal + dogfood + adoption docs.
- Under-scope: MUST leave every nonterminal IPD conforming-or-quarantined, dogfood lint clean, and record adoption (DECISIONS + AGENTS pointer).

## Required tests / validation

`aw ipd lint` dogfood (E-02, E-05) + suite. Run `python -m pytest -q`; paste. Confirm the AGENTS.md regen is an empty diff except the pointer and AGENT-PLANS byte-identical. Leak-clean; no em/en dashes.

## Spec / documentation sync

`DECISIONS.md` (pointer), `AGENTS.md` (thin pointer), and any research/README dir docs that reference the IPD shape. The spec is unchanged (this executes it).

## Open questions

### OQ-01: quarantine mechanism for nonterminal plans not being pursued

- Blocking: no
- Status: deferred
- Owner: this child
- Resolution or deferral rationale: whether a non-migrated nonterminal plan is quarantined by a front-matter marker vs a move is decided here; default: mark and leave in place with a recorded reason.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: list each nonterminal IPD and its disposition (migrated | quarantined + reason); confirm research-org 00-07 left for the post-Set follow-up.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd lint` repo dogfood output: nonterminal IPDs exit 0; terminal plans report `legacy/not evaluated` (not a pass).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: quote the DECISIONS pointer entry; confirm it points to the spec and lists the revisions + grandfathering.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `git diff -- AGENTS.md` showing ONLY the added `aw ipd` pointer line; confirm AGENT-PLANS byte-identical.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the full-suite summary AND the dogfood lint result; suite green, dogfood clean.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Requires Orders 01 to 05; if absent, STOP. This file SHOULD be linted with the real `aw ipd lint`. Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with nonempty observed evidence (incl. the empty AGENTS.md diff and byte-identical AGENT-PLANS); else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (nonterminal migration + dogfood + adoption docs; edit only the existing `agents_pointer_prose`; regenerate AGENTS.md, do not hand-edit; do NOT re-author the research-org Set here). Terminal transition is a POST-gate transaction. Never create or push a tag / Release / PyPI upload.
