# IPD: plan stable `Id` in `ipd_schema` + linter + scaffold/sync (Set `plans-adopter`, Order 2)

- Date: 2026-08-08
- Kind: child
- Concern: give every plan a stable, greppable citation handle that survives renaming/regrouping, expressed as a single `- Id:` line in the EXISTING `ipd_schema` metadata block (NOT a research-style frontmatter block, avoiding collision with `Set:`/`Order:`/`Status:`/`Kind:`/watermark).
- Scope: add `Id` (6-char base36 from the Order-01 core) as a REQUIRED plan metadata field in `agent_workflows/ipd_schema.py`; have `aw ipd lint` validate it; have `aw ipd scaffold`/`sync` emit it. No manifest, no rename, no migration. Requires Order 01 (`artifact_core`).
- Status: approved
- Set: plans-adopter
- Order: 2
- Highest E allocated: 06
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Approval: 2026-08-08 human maintainer (via opencode its_direct/pt3-claude-opus-4.8-1m-us): "Approved all. Please read and execute the orchestrator."
- Id: 2bpoz6

## Workflow history

- 2026-08-08 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `plans-adopter`; the identity layer for plans. Authored from spec `20260808-0004-01` Section 4.2 + OQ2.
- 2026-08-08 reviewed (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001/C2-3 (HIGH): added E-06 to repair every in-repo conforming fixture lacking Id (conforming-orchestrator.md, _conforming_child ~22x, templates) in lockstep with making Id required, else ~28 conformance/exact-diagnostic tests would flip to error; corrected OQ-01 (no metadata field-order rule exists).
- 2026-08-08 /plan-review (Antigravity Agent): APPROVE; (none)

## Goal

Make `- Id: <id6>` a first-class, required, linter-checked field of the plan metadata block, sourced from the shared core's id6 grammar, so plans have a stable citation handle independent of their filename. Update `aw ipd scaffold` to emit a fresh collision-checked `Id`, and `aw ipd sync` to backfill a missing `Id`. This is the enabler for citation-safe regrouping (Order 04) and the migration (Order 06).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: schema + linter

- [ ] E-01 add `Id` to the `ipd_schema` recognized metadata fields, sourced from `artifact_core`'s id6 grammar; define its position in the metadata block (after `Author`, or a defined slot) and its validity rule (exactly a 6-char base36 token).
  - Depends on: none
  - Expected outcome: `ipd_schema` recognizes and can validate an `- Id:` line.
  - Execution state: pending
- [ ] E-02 make `Id` REQUIRED for all plans (OQ2): a missing or malformed `Id` is a lint error. Grandfather nothing at the schema level; the migration (Order 06) backfills existing plans, and until then the `--legacy` path (terminal grandfathered plans) is unaffected.
  - Depends on: E-01
  - Expected outcome: `aw ipd lint` on a conforming plan WITHOUT an `Id` reports a precise error; WITH a valid `Id` passes.
  - Execution state: pending

### Task group 2: authoring tools + tests + templates

- [ ] E-03 update `aw ipd scaffold` to generate a fresh collision-checked `Id` (using the core generator, checked against ids already present under `.agents/plans/**`) and emit the `- Id:` line in the skeleton.
  - Depends on: E-01
  - Expected outcome: a scaffolded plan carries a valid unique `- Id:`.
  - Execution state: pending
- [ ] E-04 update `aw ipd sync` to BACKFILL a missing `Id` (assign a fresh collision-checked id, dry-run default + `--apply`), without touching an existing one.
  - Depends on: E-01
  - Expected outcome: `sync` on a plan lacking `Id` proposes/writes one; on a plan with `Id` leaves it unchanged.
  - Execution state: pending
- [ ] E-05 regenerate the IPD templates (`assess/templates/ipd.md` + `orchestrator-ipd.md`) to include the `- Id:` line (byte-parity with `ipd_authoring.build_skeleton`); extend `tests/test_ipd_schema`/`test_ipd_lint`/`test_ipd_authoring`/`test_ipd_templates` for the new field; run the file(s) plus the full suite and paste both.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: templates carry `Id`; new/updated tests pass; full suite green.
  - Execution state: pending
- [ ] E-06 REPAIR every existing in-repo "conforming" fixture that lacks `- Id:` so making `Id` required does not flip conformance/exact-diagnostic assertions to error: backfill a valid `- Id:` into `tests/fixtures/conforming-orchestrator.md` and into the `_conforming_child()` builder in `tests/test_ipd_lint.py` (used ~22 times), and into any other in-code conforming IPD string (e.g. `_conforming_orchestrator` helpers). This MUST land in the same change as E-02 (making Id required) so the suite never goes red between steps.
  - Depends on: E-02
  - Expected outcome: `tests/fixtures/conforming-orchestrator.md` and `_conforming_child()` carry a valid `Id`; the ~22 `_conforming_child` assertions and the fixture-based `test_ipd_lint`/`test_ipd_schema` conformance/exact-diagnostic tests pass unchanged in intent (no stray `meta.missing` diagnostic).
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_schema.py` owns the plan metadata contract (`META_REQUIRED`, `META_RECOGNIZED`, the bullet `- Field: value` grammar, the `Approval`/`Set`/`Order`/watermark rules). `Id` is added there as the single source.
- The id6 grammar is imported from `artifact_core` (Order 01), not redefined.
- `aw ipd scaffold`/`sync` live in `ipd_authoring.py`; `build_skeleton` must stay byte-parity with the templates (there is a `test_ipd_templates` parity check).
- The linter has an author/review/pre-execution/pre-transition/post-transition checkpoint model; `Id` validity applies at all non-legacy checkpoints.
- Test runner: stdlib `unittest`, NOT pytest.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C2-1 | HIGH | Low | integrity | identity | Plans need a stable handle to survive regrouping/rename (spec 2/4.2); the timestamp stem cannot serve once files are reclustered. | spec 2, 8 |
| C2-2 | MEDIUM | Medium | consistency | no-collision | The handle must reuse the existing metadata block, not add a second frontmatter system. | spec 3, 4.2 |
| C2-3 | HIGH | Low | testing | fixture-repair | Making `Id` required flips every in-repo conforming fixture lacking it to `error`: `tests/fixtures/conforming-orchestrator.md` and `_conforming_child()` (used ~22x) + the two templates. E-06 repairs them in lockstep with E-02. | tests/fixtures/conforming-orchestrator.md, tests/test_ipd_lint.py:33 |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | 4.2 | Add `Id` (core id6) to `ipd_schema` recognized fields + validity rule + position | `agent_workflows/ipd_schema.py` | Low | E-01 |
| 2 | OQ2 | Make `Id` required (lint error if missing/malformed) | `agent_workflows/ipd_schema.py`, `agent_workflows/ipd_lint.py` | Medium | E-02 |
| 3 | 4.2 | `aw ipd scaffold` emits a fresh collision-checked `Id` | `agent_workflows/ipd_authoring.py` | Low | E-03 |
| 4 | 4.2 | `aw ipd sync` backfills a missing `Id` | `agent_workflows/ipd_authoring.py` | Low | E-04 |
| 5 | 4.2 | Templates + tests | `assess/templates/ipd.md`, `orchestrator-ipd.md`, `tests/test_ipd_*` | Low | E-05 |
| 6 | 4.2 | Backfill `Id` into existing conforming fixtures (`conforming-orchestrator.md`, `_conforming_child()`) in lockstep with making Id required | `tests/fixtures/conforming-orchestrator.md`, `tests/test_ipd_lint.py` | Low | E-06 |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Later step |
|------|------------------|------|--------|-----------|
| Backfilling `Id` into existing plans | n/a | scope | That is the one-time migration. | Order 06 |
| Manifest / regroup / shards using `Id` | n/a | scope | Later children consume `Id`. | Orders 03 to 05 |

## Scope check

- Over-scope: none - one metadata field + its linter/scaffold/sync support + templates/tests.
- Under-scope: MUST make `Id` a required, validated, tool-emitted field so later children and the migration can rely on it.

## Required tests / validation

Extend `tests/test_ipd_schema.py` (Id recognized + required + validity), `tests/test_ipd_lint.py` (missing/malformed Id fails; valid passes), `tests/test_ipd_authoring.py` (scaffold emits a unique Id; sync backfills), `tests/test_ipd_templates.py` (templates carry Id, byte-parity). Run the affected files then the full suite `python3 -m unittest discover -s tests -t .`; PASTE both. Leak-clean; no em/en dashes.

## Spec / documentation sync

The `ipd-spec` doc (`.agents/docs/specs/20260726-1340-01-ipd-spec.md`) is updated to document the new `- Id:` field (its grammar, that it is required, and that it is a stable citation handle). No change to `20260808-0004-01` (this executes it).

## Open questions

### OQ-01: metadata-block position of `Id`

- Blocking: no
- Status: resolved
- Owner: this child
- Resolution or deferral rationale: place `- Id:` immediately after `- Author:` (end of the identity block), grouped with the other stable identity fields. VERIFIED at review: the linter does NOT enforce metadata FIELD order (`validate_metadata` checks presence/duplicates/unknown-fields/pairing/values, not order; only H2 heading order is checked), so the slot is a readability choice and cannot break a lint check. `Id` is added to `META_REQUIRED` (order-independent) and `META_RECOGNIZED`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a test showing `ipd_schema` recognizes `- Id:` and validates a 6-char base36 token (rejects wrong length/charset), sourced from `artifact_core`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw ipd lint` output: a plan missing `Id` fails with a precise message; the same plan with a valid `Id` conforms; confirm `--legacy` terminal plans are unaffected.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste a scaffolded plan showing a valid unique `- Id:`; confirm two scaffolds produce different ids.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `aw ipd sync` proposing an `Id` for a plan lacking one and leaving an existing `Id` unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: confirm both templates carry `- Id:` with byte-parity to `build_skeleton`; paste the affected test files' results + the full-suite `Ran N tests ... OK` summary; leak-clean.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: confirm `tests/fixtures/conforming-orchestrator.md` and `_conforming_child()` (and any other in-code conforming IPD) carry a valid `- Id:`; paste `python3 -m unittest tests.test_ipd_lint tests.test_ipd_schema -v` showing the previously-conforming fixtures still conform (no stray `meta.missing`); confirm this landed together with E-02 (no red intermediate state).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval; not auto-executed. Requires Order 01 (`artifact_core`). Do NOT claim done or move to `executed/` until every `E-*` is performed+checked AND its matching `V-*` is pass+checked with concrete evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds scope (the `Id` field + its tooling only; no manifest/regroup/migration). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
