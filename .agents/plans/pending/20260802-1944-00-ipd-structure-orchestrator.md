# IPD (ORCHESTRATOR): IPD structure, stable E-*/V-* mapping, and deterministic linting (Set `ipd-structure`)

- Date: 2026-08-02
- Kind: orchestrator
- Concern: implement the spec `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` (a gpt-5.6-revised DRAFT pending maintainer review and approval; NOT approved, NOT adopted): convert the IPD execution/validation checklist structure from relational prose ("near the top/end") into an EXACT, machine-checkable contract with stable `E-*`/`V-*` identifiers and an allocation watermark, a deterministic phase-aware linter, tool-assisted authoring, fixed lifecycle/checkbox/question/size semantics, quarantine semantics, and fail-closed review integration.
- Scope: ORCHESTRATOR for the ordered Set `ipd-structure`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It changes no product files itself; each child does its own edits. Applies to new and nonterminal IPDs; terminal `executed/` plans are grandfathered. Formal maintainer approval of the specification is an explicit prerequisite to executing this Set (spec Section 18).
- Status: to-review
- Set: ipd-structure
- Order: 0
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

<!--
Bootstrap note: this Set DEFINES the new IPD shape, but its own tooling (`aw ipd scaffold/sync/lint`)
does not exist until Orders 02/03. Per spec Section 12, these plan files are hand-authored to the new
shape under a labeled bootstrap exception: "machine preflight unavailable: bootstrap". After Order 02
lands, remaining unexecuted children SHOULD be linted with the real tool.
-->

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from the gpt-5.6-revised spec. Split into a Set because the work spans a canonical schema, a parser+linter+state-machine, authoring tools, template/spec edits, review-workflow integration, and a migration, with strict dependency ordering and well beyond one IPD's size guidance.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (Order 04 dependency corrected 01,03 -> 01,02,03 in this table, since 04's validation runs `aw ipd lint` from Order 02), PR-004 (Orders 01/04 now explicitly capture the orchestrator heading order this file exemplifies). Bootstrap preflight applied manually ("machine preflight unavailable: bootstrap"). No BLOCKER/HIGH. Readiness: GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive post-review structural revisions applied to the whole Set (corrected false "approved/adopted" spec provenance to a draft pending approval; moved this orchestrator's execution checklist to immediately after `## Goal` per spec Section 4.2; renamed `## Findings (drivers)` to `## Findings` across the Set; added the allocation-watermark, quarantine, metadata-block, writing-safety, and NEW `ipd-lifecycle` enforcement-path scope to the children; expanded acceptance-case coverage). These revisions SUPERSEDE the earlier /plan-review GO verdict for readiness purposes. Returned to `Status: to-review`; a FRESH independent `/plan-review` is required (the revising agent does NOT self-approve). No `approved` status set; maintainer approval remains separate and is a prerequisite to execution.

## Goal

Deliver the IPD-structure convention end to end: a single canonical schema (including the metadata-block contract, the `E-*` allocation watermark, and quarantine semantics); a fence-aware read-only `aw ipd lint` with explicit checkpoints, the full execution/validation state model, and legacy + quarantine dispositions; non-destructive `aw ipd scaffold`/`sync` with the writing-command safety contract and watermark maintenance; schema-generated (or schema-checked) child + orchestrator templates (orchestrator execution checklist moved to immediately after `## Goal`) and an updated `ipd-spec` with the ambiguous "near" language removed and F-07/F-08/F-09 fixed; fail-closed structural preflight wired into `plan-review`, `plan-review-long`, `review-rubric`, and a NEW authoritative `ipd-lifecycle` execution-and-transition workflow (spec Section 12.1; it does not exist today); the always-loaded structural prose in `agents_pointer_prose()` replaced with a thin pointer; and migration/quarantine of nonterminal IPDs with repository dogfooding. Terminal plans stay grandfathered.

## Detailed Implementation Checklist (TODO)

The orchestrator's actions are gating the children and running the cross-IPD checks. These items are gate checkpoints, not code edits, so they carry no `E-*` ids (spec Section 4.2: the execution checklist is the next H2 after `## Goal`; for the orchestrator its entries are coordination checkpoints).

- [ ] Child 01 executed (canonical schema + schema tests, incl. metadata-block/watermark/quarantine) and its own checklists verified.
- [ ] Child 02 executed (parser + `aw ipd lint` + state machine + legacy/quarantine disposition, after 01) and verified.
- [ ] Child 03 executed (scaffold + sync + writing-safety + watermark maintenance, after 01/02) and verified.
- [ ] Child 04 executed (templates + spec + F-07/F-08/F-09 + orchestrator-checklist relocation, after 01/02/03) and verified.
- [ ] Child 05 executed (review preflight + NEW `ipd-lifecycle` fail-closed enforcement + parity, after 01/02/04) and verified.
- [ ] Child 06 executed (migrate/quarantine nonterminal + thin `agents_pointer_prose` pointer + dogfood + adopt, after 01 to 05) and verified.
- [ ] Cross-IPD validation run (single-source-of-truth / no-drift / dependency correctness / size).
- [ ] Suite green after the last child (paste actual output); leak-clean; no em/en dashes; `aw ipd lint` dogfood clean on nonterminal IPDs (conforming pass; quarantined/grandfathered report their dispositions).

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260802-1944-01-canonical-ipd-schema.md` | The single machine-readable IPD schema (kinds, headings+order incl. the enumerated orchestrator order, optional intervals, metadata-block fields incl. `auto-approved` and the `Order: 0` exception, id grammar + allocation watermark, E/V field grammar + state tables, checkpoints, thresholds, quarantine + legacy) + schema tests. The source of truth everything else derives from or is checked against. | none |
| 02 | `20260802-1944-02-ipd-lint-parser-and-state-machine.md` | Fence-aware Markdown parser + read-only `aw ipd lint` with explicit `--phase` checkpoints, the execution/validation state machine, the bijection + evidence/state checks, the legacy AND quarantine dispositions, diagnostics + exit codes. | 01 |
| 03 | `20260802-1944-03-ipd-scaffold-and-sync.md` | `aw ipd scaffold` (new conformant skeleton from the schema) and non-destructive `aw ipd sync` (assign ids to new leaves via the watermark, add pending V skeletons, never rewrite stable ids or reuse a deleted suffix, refuse destructive sync after execution), both under the writing-command safety contract (spec Section 6.2). | 01, 02 |
| 04 | `20260802-1944-04-templates-and-spec-and-defect-fixes.md` | Child + orchestrator templates generated-from/checked-against the schema (orchestrator execution checklist moved to immediately after `## Goal`); `ipd-spec` update removing "near" language; F-07 checkbox semantics, F-08 lifecycle-gate-as-post-transaction, F-09 blocking-question + size-assessment grammar. | 01, 02, 03 |
| 05 | `20260802-1944-05-review-preflight-and-enforcement.md` | Structural preflight + fail-closed enforcement wired into `plan-review`, `plan-review-long`, `review-rubric`, and a NEW authoritative `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` execution-and-transition workflow (spec Section 12.1); parity tests for embedded vs standalone rubric/report-template content. | 01, 02, 04 |
| 06 | `20260802-1944-06-migrate-nonterminal-and-adopt.md` | Migrate/quarantine nonterminal IPDs to the new schema (incl. the research-org Set's explicit bootstrap quarantine); replace the always-loaded structural prose in `agents_pointer_prose()` with a thin pointer; dogfood lint across the repo; docs + DECISIONS pointer + thin AGENTS.md pointer; grandfather terminal plans. | 01, 02, 03, 04, 05 |

## Completion criteria (the whole Set is done only when)

- Each child (01 to 06) is executed and its OWN two checklists are verified with concrete evidence.
- The cross-IPD validation below passes.
- The suite is green after each child and at the end; leak-clean; no em/en dashes in authored Markdown.
- `aw ipd lint` passes on every migrated nonterminal IPD in this repo (dogfood, Order 06); quarantined plans (incl. the research-org Set) report the explicit `quarantined` disposition; terminal plans are correctly reported as grandfathered rather than conforming.

## Cross-IPD validation

- Consistency: the schema (Order 01) is the ONE source of truth; the linter (02), tools (03), templates+spec (04), and review integration (05) all derive from or are checked against it, with no second independently-maintained structural definition. Read them together and confirm no fork.
- No duplication/drift: parity tests exist for any embedded-vs-standalone rubric/report-template copies (Order 05); the `E-*`/`V-*` grammar, state tables, checkpoints, and heading order are defined once (01) and referenced elsewhere.
- Dependency correctness: no child uses a later child's symbols; the linter (02) does not assume the tools (03); migration (06) runs only after schema+linter+tools+templates+review exist.
- Size check: each child stays within the size guidance (prefer <=5 task groups / <=18 E leaves); a child exceeding it carries a Size-assessment exception with a cohesion rationale or is split.

## Deferred / out of scope (with reason)

| Item | Axis | Reason | Later step |
|------|------|--------|-----------|
| The controlled layout experiment (execution-top vs alternatives) | complexity | The research deferred it; top/bottom stays an explicitly provisional default. Not required for the deterministic corrections. | A later evidence effort if layout optimization becomes valuable. |
| Retrofitting the ~120 terminal `executed/` IPDs | functionality | Already implemented, rarely re-read; rewriting churns history for little value. | Grandfathered (Order 06); a later migration only if justified. |
| A merged action/evidence ledger for tiny plans | usability | Unsupported by direct evidence; version 1 keeps two physical sections. | Experimental variant, separate plan kind/schema version later. |
| Pre-commit / CI hook wiring of `aw ipd lint` | usability | Version 1 relies on authoritative-workflow invocation; hooks are defense in depth. | Follow-up once the tool is proven. |
| Re-authoring the research-org Set (00-07) to the new shape | scope | Depends on this Set landing first (maintainer's IPD-system-first sequencing). During this bootstrap it is explicitly QUARANTINED (spec Section 13.3), not migrated in place, so the dogfood never calls it conforming. | Immediately after this Set; tracked as the quarantine follow-up. |

## Scope check

- Over-scope: none - the orchestrator only coordinates; children make the bounded edits.
- Under-scope: the Set MUST deliver, for IPDs: the canonical schema (incl. metadata block, allocation watermark, quarantine), the linter + state machine + legacy/quarantine dispositions, scaffold + sync under the writing-safety contract, schema-driven templates + spec update + the three defect fixes + the orchestrator-checklist relocation, fail-closed review integration + the NEW `ipd-lifecycle` workflow + parity tests + the thin `agents_pointer_prose` pointer, and nonterminal migration/quarantine + dogfood + adoption docs. Anything less leaves the convention unenforced.

## Required tests / validation

Per-child validation (each child names its own literal commands) plus the cross-IPD checks above. Run `python -m pytest -q` after each child and at the end; paste ACTUAL output; `aw check-local-leaks . --agent` clean; no em/en dashes. Final acceptance: `aw ipd lint` (real tool) passes on every migrated nonterminal IPD and reports terminal plans as grandfathered.

## Open questions

### OQ-01: canonical-schema repository path

- Blocking: no
- Status: deferred
- Owner: Order 01 (discovery step)
- Resolution or deferral rationale: the exact on-disk path for the canonical schema is an implementation detail chosen in Order 01 after confirming repo conventions (spec Section 3); it does not gate the Set's design.

### OQ-02: Markdown parsing library

- Blocking: no
- Status: deferred
- Owner: Order 02
- Resolution or deferral rationale: the specific CommonMark-compatible parser is chosen in Order 02; the requirement (fence-aware, structural, source positions retained) is fixed by the spec.

## Validation and cross-check (verify before reporting the Set complete)

Each item maps to a checklist item above; provide concrete evidence.

- [ ] Each child 01 to 06 is in `.agents/plans/executed/` with `Status: executed` and its own Validation checklist verified; cite each.
- [ ] Cross-IPD validation performed: quote the schema's id grammar + state tables + heading order from Order 01 and confirm the linter, tools, templates, and review integration match it; confirm execution order respected the dependency table.
- [ ] Paste the actual final `pytest` summary line; paste `aw ipd lint` dogfood output showing nonterminal IPDs pass, quarantined plans (incl. research-org) report `quarantined`, and terminal plans report grandfathered; confirm leak-clean and no em/en dashes.
- [ ] Report any child that is incomplete/blocked/unverified EXPLICITLY; do NOT mark the Set complete otherwise.

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Specification prerequisite: the underlying specification is a gpt-5.6-revised DRAFT that is NOT approved and NOT adopted. Formal maintainer approval of the specification is an explicit prerequisite to executing this Set (spec Section 18); do NOT execute any child until that approval is recorded.

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Bootstrap preflight: until Order 02 lands, these plan files are hand-authored to the new shape and reviewed with a manual structural preflight labeled "machine preflight unavailable: bootstrap" (spec Section 12). After Order 02, lint remaining unexecuted children with the real `aw ipd lint`.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload. Terminal lifecycle transition is a POST-gate transaction, never an execution/validation checklist item.
