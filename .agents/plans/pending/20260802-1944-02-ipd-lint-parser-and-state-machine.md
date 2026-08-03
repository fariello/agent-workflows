# IPD: fence-aware parser + `aw ipd lint` + state machine (Set `ipd-structure`, Order 2)

- Date: 2026-08-02
- Kind: child
- Concern: build the deterministic, read-only `aw ipd lint` that enforces the Order-01 schema: a fence-aware Markdown parser, the execution/validation state machine, the `E-*`/`V-*` bijection, evidence/state legality, explicit `--phase` checkpoints, stable diagnostics + exit codes. No model calls, no network, no writes.
- Scope: the parser + linter + state-machine consuming the Order-01 schema, including the legacy AND quarantine dispositions and the metadata-block/watermark checks. No authoring tools (Order 03), no template/spec edits (04), no review wiring (05). Requires Order 01 executed (imports `ipd_schema`); if its symbols are absent, STOP.
- Status: to-review
- Set: ipd-structure
- Order: 2
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; the highest-value intervention (deterministic enforcement) per the research.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003 (added the legacy-disposition behavior + its tests to E-05/E-06/V-05, since spec 13.2/16.5 make the linter own `legacy/not evaluated` and Order 06 only consumes it). Bootstrap manual preflight. No BLOCKER/HIGH. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: the linter now also implements the QUARANTINE disposition (spec Section 13.3) alongside legacy, the metadata-block checks incl. `auto-approved` and the `Order: 0` exception, the watermark checks (spec Section 5.6), and the deterministic-vs-semantic boundary is made explicit per checkpoint (spec Section 10.1); diagnostics carry line AND column; renamed `## Findings (drivers)` to `## Findings`. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required; the revising agent does NOT self-approve.

## Goal

`aw ipd lint [--phase CHECKPOINT] FILE`: parse structurally (fence-aware), validate against the Order-01 schema for the requested checkpoint, and report precise diagnostics. Deterministic: zero model calls, zero network, read-only. Its hard boundary (structure/state, never meaning) is documented in output and help. Spec Sections 4.1, 9, 10.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: parser

- [ ] E-01 add a fence-aware structural Markdown reader (module `agent_workflows/ipd_lint.py`) that yields top-level H2 nodes and task-list leaves while EXCLUDING headings/checkboxes inside fenced/indented code, front matter, and block quotes; retain source line/col.
  - Depends on: none
  - Expected outcome: parsing the spec's own example file does NOT treat its fenced examples as IPD structure.
  - Execution state: pending

### Task group 2: checks + state machine

- [ ] E-02 implement structural checks against `ipd_schema`: required H2 present/unique/in-order per kind; execution heading is next H2 after `## Goal`; validation heading immediately precedes `## Approval and execution gate`; optional headings only in permitted intervals; AND the metadata-block checks (spec Section 4.4): required/conditional fields, duplicate/unknown field, `Kind`/`Status` (incl. `auto-approved`) values, the `Order: 0` orchestrator exception, the watermark field (spec Section 5.6: watermark >= largest present `E-*` suffix), and permitted path/status/kind combinations.
  - Depends on: E-01
  - Expected outcome: misplaced/duplicate/out-of-order headings, a bad/duplicate/unknown metadata field, an orchestrator `Order != 0`, and a watermark below a present id each produce a distinct coded error.
  - Execution state: pending
- [ ] E-03 implement the id + bijection checks: id grammar (incl. more than 99 syntactically valid ids, e.g. `E-100`), uniqueness, every `E-*` has exactly one `V-*` targeting it and every `V-*` targets a real `E-*`; correct id family per section; dependency targets exist, no self-ref, no cycle.
  - Depends on: E-01
  - Expected outcome: orphan/duplicate/miswired ids and dependency cycles each flagged; a plan with more than 99 valid ids parses without an id-grammar error.
  - Execution state: pending
- [ ] E-04 implement the state machine: execution + validation checkbox/state/evidence legality and E/V cross-constraints from the Order-01 tables; checkpoint-specific requirements for `author|review-finalize|pre-execution|pre-transition|post-transition`; question-field + size-assessment consistency. Every checkpoint checks ONLY deterministic structure/state (presence, grammar, recognized placeholders, cross-state legality); it MUST NOT assert semantic properties (meaningful atomicity, genuine observability, evidence sufficiency, truthful nonblocking classification), which stay with the semantic reviewer (spec Section 10.1).
  - Depends on: E-01
  - Expected outcome: each illegal combination and each checkpoint violation flagged; `pre-transition` rejects any non-`performed` E, non-`pass` V, unchecked V, or empty observed evidence; the boundary text in `--help`/output claims no semantic certainty.
  - Execution state: pending

### Task group 3: CLI + boundary + tests

- [ ] E-05 wire `aw ipd lint` into the CLI: `--phase` (explicit; conservative default inference from the metadata block/path but never infers a transition gate), stable rule codes + `path:line:col` diagnostics, exit `0`/`1`/`2` (conform / lint-error / tool-failure, never conflated), the no-em/en-dash rule applied to authored prose only (code blocks, metadata values, and exempt constructs NOT flagged), AND both dispositions (spec Sections 13.2/13.3/16.5): a terminal/grandfathered file with no legacy flag reports `legacy/not evaluated`; `--legacy` runs the reduced legacy checks; a QUARANTINED nonterminal file (metadata `Quarantine:` trio) reports the explicit `quarantined` disposition (a non-passing informational outcome distinct from both `pass` and `legacy/not evaluated`, never a false pass).
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `aw ipd lint --help` states the structure-not-meaning boundary; exit codes behave per spec Section 10; a grandfathered file reports `legacy/not evaluated`; a quarantined file reports `quarantined`; neither is reported as passing.
  - Execution state: pending
- [ ] E-06 add `tests/test_ipd_lint.py`: parser fixtures (fenced/indented/quoted/YAML-front-matter/metadata-block examples), heading-order cases, metadata-block cases (incl. `auto-approved`, `Order: 0`, watermark-below-present-id), id/bijection cases, every legal/illegal state combo, checkpoint cases, exit-code cases, legacy-disposition cases, quarantine-disposition cases, and the dash-only-in-prose cases, with diagnostics asserting a stable rule code + `path:line:col` (spec Section 16).
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: table-driven + golden-fixture tests incl. legacy + quarantine + diagnostics; all pass.
  - Execution state: pending
- [ ] E-07 run `python -m pytest tests/test_ipd_lint.py -q` then the full suite; paste both.
  - Depends on: E-06
  - Expected outcome: new tests pass; suite green.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Imports the Order-01 `ipd_schema`; no restated constants.
- CLI style: argparse subcommands in `agent_workflows/cli.py`; add an `ipd` group with a `lint` action.
- Parser: prefer a maintained CommonMark-compatible parser retaining source positions; if a new dependency is undesirable, a fence-aware structural reader is acceptable (decide in discovery, keep 3.9-safe).
- No em/en dashes in authored Markdown.

## Findings

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| C2-1 | HIGH | Medium | implementer | correctness | A naive regex checker would count the spec's/template's own Markdown examples as real structure. | spec Section 4.1, change-rationale Section 7 |
| C2-2 | HIGH | Low | automation | integrity | An internal/parse failure reported as passing lint would defeat fail-closed enforcement. | spec Section 10 (exit 2 distinct) |

## Proposed changes (ordered, validatable)

| Step | Source finding IDs | Change | Files | Remediation Risk | Validation |
|------|--------------------|--------|-------|------------------|------------|
| 1 | C2-1 | fence-aware parser | `agent_workflows/ipd_lint.py` | Medium | E-01 fixtures |
| 2 | C2-1 | structural + id + state checks | `agent_workflows/ipd_lint.py` | Medium | E-02..E-04 |
| 3 | C2-2 | CLI + exit codes + boundary | `agent_workflows/cli.py`, `agent_workflows/ipd_lint.py` | Low | E-05 |
| 4 | all | tests | `tests/test_ipd_lint.py` | Low | E-06, E-07 |

## Deferred / out of scope (with reason)

| Finding ID | Remediation Risk | Axis | Reason | Recommended later step |
|------------|------------------|------|--------|------------------------|
| n/a | n/a | scope | Scaffold/sync (write ops) are Order 03; lint is read-only. | Order 03 |
| n/a | n/a | scope | Wiring lint into review/lifecycle is Order 05. | Order 05 |

## Scope check

- Over-scope: none - parser + read-only checks + CLI + tests.
- Under-scope: MUST be fence-aware, cover all Order-01 state combinations + checkpoints, and never report a tool failure as a pass.

## Required tests / validation

`tests/test_ipd_lint.py` (E-06). Run `python -m pytest tests/test_ipd_lint.py -q` then `python -m pytest -q`; paste both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`aw ipd lint --help` documents the checkpoints + the structure-not-meaning boundary. Broader docs/DECISIONS/AGENTS pointer land in Order 06.

## Open questions

### OQ-01: Markdown parsing library vs in-repo reader

- Blocking: no
- Status: deferred
- Owner: this child's discovery step
- Resolution or deferral rationale: choose a maintained CommonMark parser vs a small fence-aware reader in discovery; the fence-awareness + source-position requirement is fixed. Prefer no new heavy dependency if a small reader suffices.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: paste a test showing the spec example file's fenced/quoted headings are NOT parsed as IPD H2/checkboxes.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste tests where a misplaced execution heading, a duplicate heading, an out-of-order heading, a bad/duplicate/unknown metadata field, an orchestrator `Order != 0`, and a watermark below a present id each yield the expected coded error; and a metadata block with `auto-approved` is accepted.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste tests for an orphan `V-*`, a duplicate `E-*`, a `V-*` with no matching `E-*`, and a dependency cycle, each flagged; and a plan with more than 99 valid ids (`E-100`) accepted by the id grammar.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the table test covering every legal/illegal execution+validation combo and a `pre-transition` rejection of a non-`pass` V.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `aw ipd lint --help` showing the structure-not-meaning boundary text; paste runs returning exit 0 (conform), 1 (lint error), and 2 (forced parse failure) distinctly; paste a grandfathered-file run reporting `legacy/not evaluated` (not a pass), a `--legacy` run doing the reduced checks, and a quarantined-file run reporting `quarantined` (not a pass); paste a dash-in-code case NOT flagged and a dash-in-prose case flagged.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the collected test count for `tests/test_ipd_lint.py` incl. parser/heading/id/state/checkpoint/exit-code fixtures.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste `pytest tests/test_ipd_lint.py -q` AND the full-suite summary (new tests pass, suite green).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Requires Order 01 (`ipd_schema`); if absent, STOP. Bootstrap: hand-authored to the new shape, reviewed with a manual preflight labeled "machine preflight unavailable: bootstrap"; after THIS child lands, later children can be linted by the real tool. Do NOT claim done or move to `executed/` until every `E-*` is `performed`+checked AND its matching `V-*` is `pass`+checked with nonempty observed evidence; else STOP and report.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (parser + read-only lint + CLI + tests; no write ops, no review wiring). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
