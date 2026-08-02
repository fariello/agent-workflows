# IPD (ORCHESTRATOR): IPD structure, stable E-*/V-* mapping, and deterministic linting (Set `ipd-structure`)

- Date: 2026-08-02
- Kind: orchestrator
- Concern: implement the approved spec `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md`: convert the IPD execution/validation checklist structure from relational prose ("near the top/end") into an EXACT, machine-checkable contract with stable `E-*`/`V-*` identifiers, a deterministic phase-aware linter, tool-assisted authoring, fixed lifecycle/checkbox/question/size semantics, and fail-closed review integration.
- Scope: ORCHESTRATOR for the ordered Set `ipd-structure`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It changes no product files itself; each child does its own edits. Applies to new and nonterminal IPDs; terminal `executed/` plans are grandfathered.
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

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from the maintainer-adopted (gpt-5.6-revised) spec. Split into a Set because the work spans a canonical schema, a parser+linter+state-machine, authoring tools, template/spec edits, review-workflow integration, and a migration, with strict dependency ordering and well beyond one IPD's size guidance.

## Goal

Deliver the IPD-structure convention end to end: a single canonical schema; a fence-aware read-only `aw ipd lint` with explicit checkpoints and the full execution/validation state model; non-destructive `aw ipd scaffold`/`sync`; schema-generated (or schema-checked) child + orchestrator templates and an updated `ipd-spec` with the ambiguous "near" language removed and F-07/F-08/F-09 fixed; fail-closed structural preflight wired into the plan-review and lifecycle workflows; and migration/quarantine of nonterminal IPDs with repository dogfooding. Terminal plans stay grandfathered.

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260802-1944-01-canonical-ipd-schema.md` | The single machine-readable IPD schema (kinds, headings+order, optional intervals, front-matter fields, id grammar, E/V field grammar + state tables, checkpoints, thresholds, legacy) + schema tests. The source of truth everything else derives from or is checked against. | none |
| 02 | `20260802-1944-02-ipd-lint-parser-and-state-machine.md` | Fence-aware Markdown parser + read-only `aw ipd lint` with explicit `--phase` checkpoints, the execution/validation state machine, the bijection + evidence/state checks, diagnostics + exit codes. | 01 |
| 03 | `20260802-1944-03-ipd-scaffold-and-sync.md` | `aw ipd scaffold` (new conformant skeleton from the schema) and non-destructive `aw ipd sync` (assign ids to new leaves, add pending V skeletons, never rewrite stable ids, refuse destructive sync after execution). | 01, 02 |
| 04 | `20260802-1944-04-templates-and-spec-and-defect-fixes.md` | Child + orchestrator templates generated-from/checked-against the schema; `ipd-spec` update removing "near" language; F-07 checkbox semantics, F-08 lifecycle-gate-as-post-transaction, F-09 blocking-question + size-assessment grammar. | 01, 03 |
| 05 | `20260802-1944-05-review-preflight-and-enforcement.md` | Structural preflight + fail-closed enforcement wired into `plan-review`, `plan-review-long`, `review-rubric`, and execution/lifecycle workflows; parity tests for embedded vs standalone rubric/report-template content. | 01, 02, 04 |
| 06 | `20260802-1944-06-migrate-nonterminal-and-adopt.md` | Migrate/quarantine nonterminal IPDs to the new schema; dogfood lint across the repo; docs + DECISIONS pointer + thin AGENTS.md pointer; grandfather terminal plans. | 01, 02, 03, 04, 05 |

## Completion criteria (the whole Set is done only when)

- Each child (01 to 06) is executed and its OWN two checklists are verified with concrete evidence.
- The cross-IPD validation below passes.
- The suite is green after each child and at the end; leak-clean; no em/en dashes in authored Markdown.
- `aw ipd lint` passes on every migrated nonterminal IPD in this repo (dogfood, Order 06), and terminal plans are correctly reported as grandfathered rather than conforming.

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
| Re-authoring the research-org Set (00-07) to the new shape | scope | Depends on this Set landing first (maintainer's IPD-system-first sequencing). | Immediately after this Set; tracked. |

## Scope check

- Over-scope: none - the orchestrator only coordinates; children make the bounded edits.
- Under-scope: the Set MUST deliver, for IPDs: the canonical schema, the linter + state machine, scaffold + sync, schema-driven templates + spec update + the three defect fixes, fail-closed review integration + parity tests, and nonterminal migration + dogfood + adoption docs. Anything less leaves the convention unenforced.

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

## Detailed Implementation Checklist (TODO)

The orchestrator's actions are gating the children and running the cross-IPD checks. These items are gate checkpoints, not code edits, so they carry no `E-*` ids.

- [ ] Child 01 executed (canonical schema + schema tests) and its own checklists verified.
- [ ] Child 02 executed (parser + `aw ipd lint` + state machine, after 01) and verified.
- [ ] Child 03 executed (scaffold + sync, after 01/02) and verified.
- [ ] Child 04 executed (templates + spec + F-07/F-08/F-09, after 01/03) and verified.
- [ ] Child 05 executed (review preflight + enforcement + parity, after 01/02/04) and verified.
- [ ] Child 06 executed (migrate nonterminal + dogfood + adopt, after 01 to 05) and verified.
- [ ] Cross-IPD validation run (single-source-of-truth / no-drift / dependency correctness / size).
- [ ] Suite green after the last child (paste actual output); leak-clean; no em/en dashes; `aw ipd lint` dogfood clean on nonterminal IPDs.

## Validation and cross-check (verify before reporting the Set complete)

Each item maps to a checklist item above; provide concrete evidence.

- [ ] Each child 01 to 06 is in `.agents/plans/executed/` with `Status: executed` and its own Validation checklist verified; cite each.
- [ ] Cross-IPD validation performed: quote the schema's id grammar + state tables + heading order from Order 01 and confirm the linter, tools, templates, and review integration match it; confirm execution order respected the dependency table.
- [ ] Paste the actual final `pytest` summary line; paste `aw ipd lint` dogfood output showing nonterminal IPDs pass and terminal plans report grandfathered; confirm leak-clean and no em/en dashes.
- [ ] Report any child that is incomplete/blocked/unverified EXPLICITLY; do NOT mark the Set complete otherwise.

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Bootstrap preflight: until Order 02 lands, these plan files are hand-authored to the new shape and reviewed with a manual structural preflight labeled "machine preflight unavailable: bootstrap" (spec Section 12). After Order 02, lint remaining unexecuted children with the real `aw ipd lint`.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload. Terminal lifecycle transition is a POST-gate transaction, never an execution/validation checklist item.
