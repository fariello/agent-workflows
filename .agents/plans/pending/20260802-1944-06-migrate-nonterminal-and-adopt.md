# IPD: migrate nonterminal IPDs, dogfood, and adopt (Set `ipd-structure`, Order 6)

- Date: 2026-08-02
- Kind: child
- Concern: complete adoption: migrate or explicitly quarantine this repo's nonterminal IPDs to the new schema (incl. the research-org Set's explicit bootstrap quarantine), replace the always-loaded structural prose in `agents_pointer_prose()` with a thin pointer, dogfood `aw ipd lint` across the repo (nonterminal pass; quarantined report `quarantined`; terminal grandfathered), and record the convention (docs + DECISIONS pointer + thin AGENTS.md pointer).
- Scope: migration/quarantine of nonterminal plans + the thin `agents_pointer_prose` pointer + dogfood + adoption docs. No new tool/linter logic. Requires Orders 01 to 05 executed; if their tools/wiring are absent, STOP.
- Status: to-review
- Set: ipd-structure
- Order: 6
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): final child of Set `ipd-structure`; proves the convention on the repo's own plans and records adoption.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE; no findings (deps 01-05 correct; migrate/quarantine + dogfood + grandfather + thin AGENTS pointer match spec Sections 12/13; relies on Order 02's legacy disposition, now explicitly owned there per PR-003). Bootstrap manual preflight. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: quarantine is now the DEFINED metadata mechanism (spec Section 13.3), the research-org Set gets an EXPLICIT bootstrap quarantine (reason/owner/follow-up), the always-loaded relational structural prose in `agent_workflows/engine.py` `agents_pointer_prose()` (the "near the top"/"near the end" language) is REPLACED with a thin pointer to the spec + `aw ipd` commands (not merely appended to), and the dogfood distinguishes conforming/quarantined/grandfathered/erroneous; renamed `## Findings (drivers)` to `## Findings`. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required; the revising agent does NOT self-approve.

## Goal

Every nonterminal IPD in this repo conforms to the new schema (or is explicitly quarantined); `aw ipd lint` passes on them and reports terminal `executed/` plans as grandfathered (not conforming); the convention is documented with a DECISIONS pointer and a thin, token-economical AGENTS.md pointer. Spec Sections 12, 13.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: migrate nonterminal plans

- [ ] E-01 inventory nonterminal IPDs (`.agents/plans/pending/`, `approved`, `reusable` if any) and migrate each to the new schema via `aw ipd sync` (assign `E-*`/`V-*`, add state fields + `Highest E allocated:`, structured `OQ-*`, size-assessment), or explicitly QUARANTINE ones not being pursued by adding the `- Quarantine:`/`- Quarantine owner:`/`- Quarantine follow-up:` metadata trio (spec Section 13.3) and leaving them in `pending/`. Apply the research-org Set's explicit bootstrap quarantine (reason "pending re-authoring to the new schema after the IPD-system Set", owner "the IPD-system Set follow-up", follow-up "re-author to the new schema").
  - Depends on: none
  - Expected outcome: every nonterminal IPD either conforms or carries the quarantine metadata trio with a recorded reason; the research-org Set 00-07 is quarantined (NOT re-authored here) with its follow-up recorded.
  - Execution state: pending
- [ ] E-02 dogfood: run `aw ipd lint` across the repo; conforming nonterminal IPDs pass; quarantined plans (incl. research-org) report the explicit `quarantined` disposition; terminal `executed/` plans return `legacy/not evaluated`; the four categories (conforming / quarantined / grandfathered / erroneous) are distinguished, and no skipped file is called conforming.
  - Depends on: E-01
  - Expected outcome: paste dogfood output showing the four-way split (conforming pass, quarantined, grandfathered, erroneous).
  - Execution state: pending

### Task group 2: adoption docs

- [ ] E-03 add a DECISIONS pointer entry (pin number at execution) referencing the spec; note it revises the "near" placement wording, adds the E-*/V-* bijection + linter, and fixes F-07/F-08/F-09; grandfathers terminal plans.
  - Depends on: E-01
  - Expected outcome: DECISIONS entry present, short, points to the spec.
  - Execution state: pending
- [ ] E-04 REPLACE the always-loaded relational structural prose in `agent_workflows/engine.py` `agents_pointer_prose()` (the "near the top"/"near the end" checklist language, around line 678) with a THIN pointer to the authoritative spec + `aw ipd` verbs ("scaffold/sync/lint an IPD; do not hand-number ids or hand-place checklists; the exact structure lives in the ipd-spec"); do NOT merely add a line while leaving the old independent contract in place. Regenerate AGENTS.md; the diff shows only the replaced pointer content; leave the AGENT-PLANS sibling byte-identical.
  - Depends on: none
  - Expected outcome: `agents_pointer_prose()` no longer contains "near the top"/"near the end"; `git diff -- AGENTS.md` shows only the replaced pointer content; AGENT-PLANS byte-identical.
  - Execution state: pending
- [ ] E-05 run `python -m pytest -q` and `aw ipd lint` dogfood; paste both.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: suite green; dogfood clean.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Nonterminal plans live in `.agents/plans/pending/` (and `approved`/`reusable` if present); terminal in `executed/`/`superseded/`/`not-executed/`.
- The always-loaded block is `agents_pointer_prose()` in `agent_workflows/engine.py` (verified 2026-08-02: it STILL contains the old relational "near the top"/"near the end" checklist language around line 678), regenerated into AGENTS.md via the sectioned path; the old contract is REPLACED with a thin pointer (not appended to), and the refresh MUST NOT disturb the `AGENT-PLANS` sibling (established pattern). The `.agents/plans/README.md` and `.agents/workflows/templates/plans-README.md` were checked and do NOT contain the "near the"/size language, so they are out of scope here.
- DECISIONS entries are short pointers to specs (e.g. D112 -> ipd-spec); keep depth in the spec.
- Grandfathering: terminal plans are not retrofitted (spec Section 13.2).
- No em/en dashes in authored Markdown.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C6-1 | HIGH | Medium | maintainer | dogfood | The convention is unproven until the repo's own nonterminal plans conform and lint clean. | spec Section 13 |
| C6-2 | MEDIUM | Low | weak-agent | discovery | Agents must discover the `aw ipd` verbs at near-zero permanent token cost (thin pointer). | spec Section 4.11 of the research/F6 |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C6-1 | migrate/quarantine nonterminal IPDs (incl. research-org bootstrap quarantine) | `.agents/plans/pending/**` | Medium | E-01, E-02 dogfood |
| 2 | C6-1 | DECISIONS pointer | `DECISIONS.md` | Low | E-03 |
| 3 | C6-2 | REPLACE the old relational prose in `agents_pointer_prose()` with a thin pointer | `agent_workflows/engine.py`, `AGENTS.md` | Low | E-04 |

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
- Status: resolved
- Owner: none
- Resolution or deferral rationale: RESOLVED by the specification (Section 13.3) and Order 01: a quarantined nonterminal plan carries the `- Quarantine:`/`- Quarantine owner:`/`- Quarantine follow-up:` metadata trio and REMAINS in `.agents/plans/pending/` (marked, not moved). This contract is owned by an earlier child (schema/linter), so it is not left open here.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: list each nonterminal IPD and its disposition (migrated | quarantined + reason/owner/follow-up); confirm the research-org Set 00-07 carries the quarantine metadata trio (not re-authored here).
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd lint` repo dogfood output showing the four-way split: conforming nonterminal IPDs exit 0; quarantined plans (incl. research-org) report `quarantined`; terminal plans report `legacy/not evaluated`; no skipped file called conforming.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: quote the DECISIONS pointer entry; confirm it points to the spec and lists the revisions + grandfathering.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste a grep of `agents_pointer_prose()` confirming NO "near the top"/"near the end" language remains and the thin pointer is present; paste `git diff -- AGENTS.md` showing only the replaced pointer content; confirm AGENT-PLANS byte-identical.
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
