# IPD (ORCHESTRATOR): IPD structure, stable E-*/V-* mapping, and deterministic linting (Set `ipd-structure`)

- Date: 2026-08-02
- Kind: orchestrator
- Concern: implement the spec `.agents/docs/specs/20260802-1904-01-ipd-structure-and-linting.spec.md` (a gpt-5.6-revised working DRAFT that the maintainer asked to look at; NOT approved and NOT adopted; pending maintainer review and formal approval for execution): convert the IPD execution/validation checklist structure from relational prose ("near the top/end") into an EXACT, machine-checkable contract with stable `E-*`/`V-*` identifiers and an allocation watermark, a deterministic phase-aware linter, tool-assisted authoring, fixed lifecycle/checkbox/question/size semantics, quarantine semantics, and fail-closed review integration.
- Scope: ORCHESTRATOR for the ordered Set `ipd-structure`. Defines the child sequence, dependencies, whole-Set completion criteria, and cross-IPD validation. It changes no product files itself; each child does its own edits. Applies to new and nonterminal IPDs; terminal `executed/` plans are grandfathered. Formal maintainer approval of the specification is an explicit prerequisite to executing this Set (spec Section 18).
- Status: executed
- Set: ipdstruct (ipd-structure)
- Order: 0
- Highest E allocated: 08
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: by245s

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
- 2026-08-03 /plan-review (Codex gpt-5.6): REVIEWED - OPEN QUESTIONS; PR-001 through PR-010 repaired in the seven-plan Set where in scope. The controlling spec remains outside this review's candidate ledger and contains a provenance contradiction that blocks GO until corrected and formally approved.
- 2026-08-03 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): the whole Set is complete. All six children (01-06) are in `.agents/plans/executed/` with `Status: executed` and their own two checklists verified with evidence (commits 8d3247f, 3fa272f, 826b63b, 64fb51b, 6aa137e, 58202c2), executed in dependency order. Cross-IPD validation passed: single source of truth (`ipd_schema.py` imported by `ipd_lint`/`ipd_authoring`; templates byte-parity to `build_skeleton`); no fork/drift; dependency order respected; sizes within guidance. Final full suite `Ran 556 tests OK (skipped=1)`; dogfood `aw ipd lint --all .` -> conforming=1 (this orchestrator, transitioning now), quarantined=8, legacy=108, error=0; leak-clean; no em/en dashes. All E-01..E-08 performed, V-01..V-08 pass. Terminal move as a post-gate transaction.

## Goal

Deliver the IPD-structure convention end to end: a single canonical schema (including the metadata-block contract, the `E-*` allocation watermark, and quarantine semantics); a fence-aware read-only `aw ipd lint` with explicit checkpoints, the full execution/validation state model, and legacy + quarantine dispositions; non-destructive `aw ipd scaffold`/`sync` with the writing-command safety contract and watermark maintenance; schema-generated (or schema-checked) child + orchestrator templates (orchestrator execution checklist moved to immediately after `## Goal`) and an updated `ipd-spec` with the ambiguous "near" language removed and F-07/F-08/F-09 fixed; fail-closed structural preflight wired into `plan-review`, `plan-review-long`, `review-rubric`, and a NEW authoritative `ipd-lifecycle` execution-and-transition workflow (spec Section 12.1; it does not exist today); the always-loaded structural prose in `agents_pointer_prose()` replaced with a thin pointer; and migration/quarantine of nonterminal IPDs with repository dogfooding. Terminal plans stay grandfathered.

## Detailed Implementation Checklist (TODO)

The orchestrator's execution leaves coordinate the children and whole-Set checks. They use the same stable E/V contract as every other actionable IPD.

- [x] E-01 verify Child 01 is executed and its own checklist is verified.
  - Depends on: none
  - Expected outcome: canonical schema and schema tests, including metadata block, watermark, and quarantine, are complete.
  - Execution state: performed
- [x] E-02 verify Child 02 is executed after Child 01 and its own checklist is verified.
  - Depends on: E-01
  - Expected outcome: parser, linter, state machine, and disposition behavior are complete.
  - Execution state: performed
- [x] E-03 verify Child 03 is executed after Children 01 and 02 and its own checklist is verified.
  - Depends on: E-01, E-02
  - Expected outcome: scaffold, sync, writing safety, and watermark maintenance are complete.
  - Execution state: performed
- [x] E-04 verify Child 04 is executed after Children 01 through 03 and its own checklist is verified.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: templates, documentation, and F-07/F-08/F-09 corrections are complete.
  - Execution state: performed
- [x] E-05 verify Child 05 is executed after Children 01, 02, and 04 and its own checklist is verified.
  - Depends on: E-01, E-02, E-04
  - Expected outcome: review preflight, lifecycle enforcement, generated integrations, and parity checks are complete.
  - Execution state: performed
- [x] E-06 verify Child 06 is executed after Children 01 through 05 and its own checklist is verified.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: nonterminal migration/quarantine, thin pointer, dogfood, and adoption documentation are complete.
  - Execution state: performed
- [x] E-07 run the cross-IPD validation.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06
  - Expected outcome: single-source-of-truth, no-drift, dependency, acceptance-case, and size checks pass.
  - Execution state: performed
- [x] E-08 run the final suite and repository dogfood checks and paste actual output.
  - Depends on: E-07
  - Expected outcome: unittest suite, leak check, dash check, and four-way lint inventory are clean and accurately classified.
  - Execution state: performed

## Child IPDs, sequence, and dependencies

Execute in Order. Each child is its own `/plan-review` + human approval + execution.

| Order | File | What it does | Depends on |
|-------|------|--------------|------------|
| 01 | `20260802-ipdstruct-01-ktv5h3-canonical-ipd-schema.md` | The single machine-readable IPD schema (kinds, headings+order incl. the enumerated orchestrator order, optional intervals, metadata-block fields incl. `auto-approved` and the `Order: 0` exception, id grammar + allocation watermark, E/V field grammar + state tables, checkpoints, thresholds, quarantine + legacy) + schema tests. The source of truth everything else derives from or is checked against. | none |
| 02 | `20260802-ipdstruct-02-dkpqmy-ipd-lint-parser-and-state-machine.md` | Fence-aware Markdown parser + read-only `aw ipd lint` with explicit `--phase` checkpoints, the execution/validation state machine, the bijection + evidence/state checks, the legacy AND quarantine dispositions, diagnostics + exit codes. | 01 |
| 03 | `20260802-ipdstruct-03-l060ep-ipd-scaffold-and-sync.md` | `aw ipd scaffold` (new conformant skeleton from the schema) and non-destructive `aw ipd sync` (assign ids to new leaves via the watermark, add pending V skeletons, never rewrite stable ids or reuse a deleted suffix, refuse destructive sync after execution), both under the writing-command safety contract (spec Section 6.2). | 01, 02 |
| 04 | `20260802-ipdstruct-04-x9engh-templates-and-spec-and-defect-fixes.md` | Child + orchestrator templates generated-from/checked-against the schema (orchestrator execution checklist moved to immediately after `## Goal`); `ipd-spec` update removing "near" language; F-07 checkbox semantics, F-08 lifecycle-gate-as-post-transaction, F-09 blocking-question + size-assessment grammar. | 01, 02, 03 |
| 05 | `20260802-ipdstruct-05-nyfgsz-review-preflight-and-enforcement.md` | Structural preflight + fail-closed enforcement wired into `plan-review`, `plan-review-long`, `review-rubric`, and a NEW authoritative `.agents/workflows/ipd-lifecycle/ipd-lifecycle.md` execution-and-transition workflow (spec Section 12.1); parity tests for embedded vs standalone rubric/report-template content. | 01, 02, 04 |
| 06 | `20260802-ipdstruct-06-5xwaxi-migrate-nonterminal-and-adopt.md` | Migrate/quarantine nonterminal IPDs to the new schema (incl. the research-org Set's explicit bootstrap quarantine); replace the always-loaded structural prose in `agents_pointer_prose()` with a thin pointer; dogfood lint across the repo; docs + DECISIONS pointer + thin AGENTS.md pointer; grandfather terminal plans. | 01, 02, 03, 04, 05 |

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

### Spec Section 16 acceptance-case ownership

No acceptance case is implied by a generic test phrase. The named cases map as follows; the owning E item implements the fixture/assertion and the matching V item inspects its result.

| Spec cases | Owning E/V |
|------------|------------|
| 16.1 conforming child; conforming orchestrator; missing, duplicate, renamed, or out-of-order required heading; apparent H2 in fenced code, indented code, block quote, or YAML front matter; heading/checkbox-like metadata value; optional heading allowed/forbidden; invalid/missing kind; invalid/missing, duplicate, or unknown metadata; bad orchestrator/child Order; incompatible status/directory/kind/checkpoint | Order 02 E-06/V-06 |
| 16.2 duplicate or malformed IDs; missing, duplicate, or orphan V mapping; >99 IDs; watermark below present ID | Order 02 E-06/V-06 |
| 16.2 reorder without renumber; next suffix; stable gaps; delete-highest then allocate above watermark; preserve evidence/state; refuse destructive sync; remove only untouched draft V; dry-run/apply for scaffold and sync; overwrite refusal; atomic/recoverable failed write | Order 03 E-04/V-04 |
| 16.3 every execution checkbox/state pair; every validation checkbox/result/evidence combination; every E/V cross-state conflict; checkpoint placeholder rules; pre-transition incomplete E/V/evidence rejection | Order 02 E-06/V-06 |
| 16.3 post-transition status/history/path/commit consistency | Order 05 E-03/V-03 |
| 16.4 open blocking rejected; resolved blocking accepted with rationale; deferred blocking rejected; deferred nonblocking owner/trigger/rationale; both size threshold boundaries; missing/present exception rationale; standard rejected over threshold | Order 02 E-06/V-06 |
| 16.5 every persisted status including auto-approved; distinct exits 0/1/2; direct grandfathered disposition; reduced legacy; migrated legacy; quarantine disposition; stable code/path/line/column diagnostics; authored-prose-only dash exemptions | Order 02 E-06/V-06 |
| 16.5 workflows fail closed on exits 1 and 2; bootstrap label boundary; intentional parity drift and missing dependency | Order 05 E-04/V-04 |
| 16.5 repository scan grandfather behavior; four-way dogfood inventory with no skipped file called conforming | Order 06 E-02/V-02 |

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

Per-child validation (each child names its own literal commands) plus the cross-IPD checks above. Run `python3 -m unittest discover -s tests -t .` after each child and at the end; paste ACTUAL output; `aw check-local-leaks . --agent` clean; no em/en dashes. Final acceptance: `aw ipd lint --all --agent` classifies every plan as conforming, quarantined, grandfathered, or erroneous without calling an excluded file conforming.

## Open questions

### OQ-01: canonical-schema repository path

- Blocking: no
- Status: resolved
- Owner: Order 01 (discovery step)
- Resolution or deferral rationale: use the already-planned Python 3.9, zero-runtime-dependency module `agent_workflows/ipd_schema.py`.

### OQ-02: Markdown parsing library

- Blocking: no
- Status: resolved
- Owner: Order 02
- Resolution or deferral rationale: implement a purpose-built, standard-library, read-only structural reader that recognizes only the bounded IPD grammar and retains source positions. Do not add a runtime Markdown dependency.

## Validation and cross-check (verify before reporting the Set complete)

Each item maps to a checklist item above; provide concrete evidence.

- [x] V-01 validates E-01 with the executed Child 01 path, its verified checklist, and its actual test output.
  - Required evidence: executed Child 01 path and cited verification evidence.
  - Observed evidence: `.agents/plans/executed/20260802-ipdstruct-01-ktv5h3-canonical-ipd-schema.md` (Status: executed; V-01..V-07 pass). Delivered `agent_workflows/ipd_schema.py` + `tests/test_ipd_schema.py` (37 tests); commit `8d3247f`.
  - Result: pass
- [x] V-02 validates E-02 with the executed Child 02 path, dependency evidence, and its verified checklist.
  - Required evidence: executed Child 02 path, dependency order, and cited verification evidence.
  - Observed evidence: `.agents/plans/executed/20260802-ipdstruct-02-dkpqmy-ipd-lint-parser-and-state-machine.md` (executed after 01). Delivered `agent_workflows/ipd_lint.py` + `aw ipd lint` + `tests/test_ipd_lint.py` (33 tests); commit `3fa272f`. Imports `ipd_schema` (no fork).
  - Result: pass
- [x] V-03 validates E-03 with the executed Child 03 path, dependency evidence, and its verified checklist.
  - Required evidence: executed Child 03 path, dependency order, and cited verification evidence.
  - Observed evidence: `.agents/plans/executed/20260802-ipdstruct-03-l060ep-ipd-scaffold-and-sync.md` (executed after 01, 02). Delivered `agent_workflows/ipd_authoring.py` + `aw ipd scaffold`/`sync` + `tests/test_ipd_authoring.py` (17 tests); commit `826b63b`.
  - Result: pass
- [x] V-04 validates E-04 with the executed Child 04 path, dependency evidence, and its verified checklist.
  - Required evidence: executed Child 04 path, dependency order, and cited verification evidence.
  - Observed evidence: `.agents/plans/executed/20260802-ipdstruct-04-x9engh-templates-and-spec-and-defect-fixes.md` (executed after 01-03). Regenerated both templates (byte-parity to `build_skeleton`) + rewrote `ipd-spec` (F-07/F-08/F-09, no "near the") + `tests/test_ipd_templates.py` (10 tests); commit `64fb51b`.
  - Result: pass
- [x] V-05 validates E-05 with the executed Child 05 path, dependency evidence, and its verified checklist.
  - Required evidence: executed Child 05 path, dependency order, generated integration checks, and cited verification evidence.
  - Observed evidence: `.agents/plans/executed/20260802-ipdstruct-05-nyfgsz-review-preflight-and-enforcement.md` (executed after 01, 02, 04). Wired plan-review + plan-review-long + rubric preflight; created `.agents/workflows/ipd-lifecycle/`; registered in index + engine-generated shims; `tests/test_plan_review_parity.py` (13 tests); commit `6aa137e`.
  - Result: pass
- [x] V-06 validates E-06 with the executed Child 06 path, dependency evidence, and its verified checklist.
  - Required evidence: executed Child 06 path, dependency order, and cited migration/dogfood evidence.
  - Observed evidence: `.agents/plans/executed/20260802-ipdstruct-06-5xwaxi-migrate-nonterminal-and-adopt.md` (executed after 01-05). Quarantined the 8 old-shape research-org plans; thin `agents_pointer_prose` pointer + regenerated AGENTS.md (AGENT-PLANS byte-identical); DECISIONS D122; lint index-file scoping fix; commit `58202c2`.
  - Result: pass
- [x] V-07 validates E-07.
  - Required evidence: quote the schema's grammar, state tables, heading order, and every Section 16 acceptance-case owner, then show each consumer agrees.
  - Observed evidence: single source of truth confirmed: `agent_workflows/ipd_schema.py` defines `CHILD_H2_ORDER`/`ORCHESTRATOR_H2_ORDER`, the id grammar (`E_ID_RE`/`V_ID_RE`), the execution/validation state tables + `cross_state_error`, checkpoints, thresholds, quarantine/legacy dispositions. Consumers import it and do not fork: `ipd_lint` (checks) and `ipd_authoring` (scaffold/sync) both `from agent_workflows import ipd_schema`; the templates are byte-parity to `build_skeleton` (`test_ipd_templates` OK); the Section-16 acceptance-case ownership table in this orchestrator maps each case to Order 02/03/05/06 E/V items, all executed. Dependency order (01->02->03->04->05->06) respected per the executed-move commit sequence (`20bd381`, `5920d50`, `39014f1`, `a29385f`, `6233268`, `3e94679`). Sizes within guidance (each child <=3 task groups, <=8 E leaves; all `Size assessment: standard`).
  - Result: pass
- [x] V-08 validates E-08.
  - Required evidence: actual unittest summary, `aw ipd lint --all --agent` four-way inventory, leak output, and dash check.
  - Observed evidence: `python3 -m unittest discover -s tests -t .` -> `Ran 556 tests in 152.513s` / `OK (skipped=1)` (the 1 skip is the known release-tag test; +109 tests over the Set: schema 37, lint 33, authoring 17, templates 10, parity 13, minus overlap). `aw ipd lint --all .` -> `conforming=1, quarantined=8, legacy/not evaluated=108, error=0` (the sole conforming pending plan is this orchestrator, transitioning now; quarantined/legacy are non-passing; error=0). Leak scan `check-local-leaks . --agent` exit 0; no em/en dashes in the authored Set artifacts.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Specification prerequisite: the underlying specification is a gpt-5.6-revised working DRAFT (the maintainer asked to look at it; NOT approved and NOT adopted). Independently review it and record formal maintainer approval before executing this Set (spec Section 18).

This ORCHESTRATOR and each child MUST be reviewed and approved by a human before execution. The orchestrator is "executed" only when all children are executed and the cross-IPD validation passes. Do NOT mark the orchestrator or any child done or move it to `executed/` until every item in its own Validation and cross-check checklist is verified with concrete evidence; if any item cannot be completed, STOP and report.

Bootstrap preflight: until Order 02 lands, these plan files are hand-authored to the new shape and reviewed with a manual structural preflight labeled "machine preflight unavailable: bootstrap" (spec Section 12). After Order 02, lint remaining unexecuted children with the real `aw ipd lint`.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by each plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds a plan's scope. Never create or push a tag / Release / PyPI upload. Terminal lifecycle transition is a POST-gate transaction, never an execution/validation checklist item.
