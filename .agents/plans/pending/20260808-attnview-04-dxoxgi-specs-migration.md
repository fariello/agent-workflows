# IPD: specs status and history migration (Set attnview, Order 4)

- Date: 2026-08-08
- Kind: child
- Concern: bring the existing specs corpus into conformance with the new specs contract (bare-enum `- Status:` + `## Workflow history`) via the `aw specs` verbs, WITHOUT moving any file, so `aw attention --check` passes clean on the repo's specs and the specs blind spot the whole Set targets is actually closed.
- Scope: a one-time normalization of the existing specs under `.agents/docs/specs/` using `aw specs set`/`note` (Order 02): map each free-form prose status to a bare enum token, add a `## Workflow history` section where missing, and add typed gates to any `deferred` spec. Preserve every repository-relative path (specs stay flat). Does NOT change spec DESIGN content, does NOT touch other trees. Requires Orders 01, 02, 03 executed.
- Status: draft
- Set: attnview
- Order: 4
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: dxoxgi

## Workflow history

- 2026-08-08 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created. Child of Set `attnview`, authored from the approved spec F7/A9 and Section 7 normalization guidance; requires the Order 02 verbs and the Order 03 checker.

## Goal

Normalize the ~8 existing specs to the new contract using the owner verbs (not hand edits): each spec ends with exactly one bare-enum `- Status:` and a conformant `## Workflow history`; any `deferred` spec carries valid typed gates. No file is renamed or moved. After migration, `aw attention --check` (and `aw specs check`) pass clean on the specs tree.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: survey + dry run

- [ ] E-01 enumerate every spec under `.agents/docs/specs/` (excluding `README.md`) and record its current prose status and whether it has a `## Workflow history` section; produce the mapping to the target bare enum token (e.g. `canonical` -> `implemented` + `- Canonical: true`; `APPROVED ... Go` -> `approved`; `draft (evidence-gated)` -> `deferred` WITH a gate, or `draft`, per the spec's actual state).
  - Depends on: none
  - Expected outcome: a reviewed old->new status map for every spec; no writes yet.
  - Execution state: pending
- [ ] E-02 STOP-for-review gate: present the old->new mapping (including any spec that becomes `deferred` and the gate to attach) for human confirmation before any write.
  - Depends on: E-01
  - Expected outcome: the human has confirmed the per-spec target status + gates.
  - Execution state: pending

### Task group 2: apply via the owner verbs

- [ ] E-03 for each spec, run `aw specs set <path> --status <target> [--gate-* ...] --message "attnview migration: normalize status to the closed enum"` (and `--approved-by`/`--evidence` where the confirmed target is `approved`/`implemented`), so each write goes through the validating verb and records history; NO file is renamed or moved.
  - Depends on: E-02
  - Expected outcome: every spec carries a bare-enum `- Status:` + an appended history record; paths unchanged.
  - Execution state: pending
- [ ] E-04 for any spec lacking a `## Workflow history` section, ensure one is created by the verb (or via `aw specs note`) so the required section exists everywhere.
  - Depends on: E-03
  - Expected outcome: every spec has a conformant `## Workflow history`.
  - Execution state: pending

### Task group 3: verify clean

- [ ] E-05 run `aw specs check` and `aw attention --check` on the repo; confirm the specs tree is clean (no missing/unknown status, no malformed gate, no missing history); run the full suite; confirm paths are unchanged with `git status` (only content edits, no renames). Paste actual output.
  - Depends on: E-03, E-04
  - Expected outcome: specs tree passes `--check`; no path changed; full suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The migration MUST use the Order 02 verbs (not hand edits) so every change is validated and self-records history; this dogfoods `aw specs`.
- G8/A9: preserve every repository-relative path; specs stay flat (no disposition subdirs).
- This spec (`20260808-1945-01`) is itself already `approved`; the migration normalizes the OTHER specs and leaves this one consistent.

## Findings

The existing specs carry free-form prose statuses (`DRAFT`, `canonical`, `approved (2026-08-08, human)`, `APPROVED ... Go`, `draft (evidence-gated)`, hand-written `Implemented`); several lack a `## Workflow history`. Three specs describe deferred work (external-delivery, clean-delta, pip/PyPI) and are candidates for `deferred` + a gate, which is exactly the blind spot the Set closes.

## Proposed changes (ordered, validatable)

1. In-place content edits to each spec under `.agents/docs/specs/` (status normalization + history), applied via `aw specs set`/`note`. No renames.
2. No new source files (this is a data migration using Order 02 tooling).

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| Renaming/moving specs into disposition subdirs | functionality | Breaks citation paths (spec Non-goals); specs stay flat. | not planned |
| Editing spec DESIGN content | scope | Migration only normalizes status/history metadata. | n/a |
| Migrating other trees (plans/research already conform; prompts/comms excluded) | scope | Out of v1 (OQ3). | Phase 3 |

## Scope check

- Over-scope: none - metadata normalization only, via the owner verb, no renames, no design edits.
- Under-scope: MUST leave every spec conformant so `aw attention --check` passes on the specs tree; a partial migration leaves the checker red and the blind spot open.

## Required tests / validation

`aw specs check` and `aw attention --check` clean on `.agents/docs/specs/`; `git status` shows only content modifications (zero renames) to spec files; `python3 -m unittest discover -s tests -t .` green (paste `Ran N ... OK`); `aw sanitize --agent` clean; no em/en dashes.

## Spec / documentation sync

The migration itself is the spec-sync (it brings specs into contract conformance). Record the migration in each spec's `## Workflow history` (the verb does this). No separate doc change.

## Open questions

### OQ-01: which of the deferred specs get `deferred` vs `draft`/`parked`

- Blocking: yes
- Status: open
- Owner: human (resolved at the E-02 STOP-for-review gate)
- Resolution or deferral rationale: whether external-delivery / clean-delta / pip-PyPI become `deferred` (with a gate citing the TODO/decision) or another status is a human judgment about their true state; resolved interactively at E-02 before any write. Blocking because the target status determines the gate; it is resolved during execution at the gate, not deferred.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: the old->new status map lists every spec under `.agents/docs/specs/` with its current prose status and target enum token + any gate.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: the human confirmed the mapping at the STOP gate (recorded); no write occurred before confirmation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: each spec now has a single bare-enum `- Status:` and an appended migration history record; `git status` shows content edits only (no renames); `approved`/`implemented` targets carried the required token/evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: every spec has a conformant `## Workflow history` section.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `aw specs check` and `aw attention --check` output showing the specs tree clean; paste the `git status` proving zero renames; paste the `python3 -m unittest` summary.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This child MUST be reviewed and approved by a human before execution. It carries a BLOCKING open question (OQ-01) resolved at the in-run STOP-for-review gate (E-02) before any write. Do NOT mark it done or move it to `executed/` until every V-* item is verified with concrete evidence; if any item cannot be completed, STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload. The terminal lifecycle transition is a POST-gate transaction, never an E-*/V-* item. Requires Orders 01, 02, 03 executed first; if their symbols/verbs are absent, STOP.
