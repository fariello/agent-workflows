# IPD: fence-aware parser + `aw ipd lint` + state machine (Set `ipd-structure`, Order 2)

- Date: 2026-08-02
- Kind: child
- Concern: build the deterministic, read-only `aw ipd lint` that enforces the Order-01 schema: a fence-aware Markdown parser, the execution/validation state machine, the `E-*`/`V-*` bijection, evidence/state legality, explicit `--phase` checkpoints, stable diagnostics + exit codes. No model calls, no network, no writes.
- Scope: the parser + linter + state-machine consuming the Order-01 schema, including the legacy AND quarantine dispositions and the metadata-block/watermark checks. No authoring tools (Order 03), no template/spec edits (04), no review wiring (05). Requires Order 01 executed (imports `ipd_schema`); if its symbols are absent, STOP.
- Status: executed
- Set: ipd-structure
- Order: 2
- Highest E allocated: 07
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-08-02 to-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): child of Set `ipd-structure`; the highest-value intervention (deterministic enforcement) per the research.
- 2026-08-02 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-003 (added the legacy-disposition behavior + its tests to E-05/E-06/V-05, since spec 13.2/16.5 make the linter own `legacy/not evaluated` and Order 06 only consumes it). Bootstrap manual preflight. No BLOCKER/HIGH. GO - PENDING HUMAN APPROVAL.
- 2026-08-03 revision (opencode its_direct/pt3-claude-opus-4.8-1m-us): substantive revisions: the linter now also implements the QUARANTINE disposition (spec Section 13.3) alongside legacy, the metadata-block checks incl. `auto-approved` and the `Order: 0` exception, the watermark checks (spec Section 5.6), and the deterministic-vs-semantic boundary is made explicit per checkpoint (spec Section 10.1); diagnostics carry line AND column; renamed `## Findings (drivers)` to `## Findings`. These SUPERSEDE the earlier GO verdict for readiness; returned to `Status: to-review`; a fresh independent `/plan-review` is required; the revising agent does NOT self-approve.
- 2026-08-03 /plan-review (Codex gpt-5.6): REVIEWED - OPEN QUESTIONS; PR-001 through PR-010 repaired where in scope. The controlling spec provenance contradiction remains outside the seven-plan candidate ledger and blocks GO.
- 2026-08-03 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us): executed Order 02 (after Order 01). Added `agent_workflows/ipd_lint.py` (fence-aware structural reader; metadata/heading/id-bijection/dependency/state/checkpoint/OQ/size/dash checks against `ipd_schema`; disposition model conforming/quarantined/legacy/error; exit 0/1/2 with disposition separate from exit; `--phase`, `--all`, `--legacy`, `--agent`) + `aw ipd lint` CLI wiring in `cli.py` + `tests/test_ipd_lint.py` (32 tests). Deterministic: no model/network/writes. Targeted `Ran 32 tests OK`; full suite `Ran 515 tests OK (skipped=1)` (+32, no regressions); leak-clean. Dogfood `aw ipd lint --all .`: the 6 pending ipd-structure plans report `conforming`, terminal plans `legacy/not evaluated`, the old-shape research-org plans `error` (they await Order-06 quarantine). All E-01..E-07 performed, V-01..V-07 pass with evidence. Terminal move as a post-gate transaction.

## Goal

`aw ipd lint [--phase CHECKPOINT] FILE`: parse structurally (fence-aware), validate against the Order-01 schema for the requested checkpoint, and report precise diagnostics. Deterministic: zero model calls, zero network, read-only. Its hard boundary (structure/state, never meaning) is documented in output and help. Spec Sections 4.1, 9, 10.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: parser

- [x] E-01 add a fence-aware structural Markdown reader (module `agent_workflows/ipd_lint.py`) that yields top-level H2 nodes and task-list leaves while excluding headings/checkboxes inside fenced/indented code, actual YAML front matter, and block quotes; retain source line/col.
  - Depends on: none
  - Expected outcome: parsing the spec's own example file does NOT treat its fenced examples as IPD structure.
  - Execution state: performed

### Task group 2: checks + state machine

- [x] E-02 implement structural checks against `ipd_schema`: required H2 present/unique/in-order per kind; execution heading is next H2 after `## Goal`; validation heading immediately precedes `## Approval and execution gate`; optional headings only in permitted intervals; AND the metadata-block checks (spec Section 4.4): required/conditional fields, duplicate/unknown field, `Kind`/`Status` (incl. `auto-approved`) values, the `Order: 0` orchestrator exception, the watermark field (spec Section 5.6: watermark >= largest present `E-*` suffix), and permitted path/status/kind combinations.
  - Depends on: E-01
  - Expected outcome: misplaced/duplicate/out-of-order headings, a bad/duplicate/unknown metadata field, an orchestrator `Order != 0`, and a watermark below a present id each produce a distinct coded error.
  - Execution state: performed
- [x] E-03 implement the id + bijection checks: id grammar (incl. more than 99 syntactically valid ids, e.g. `E-100`), uniqueness, every `E-*` has exactly one `V-*` targeting it and every `V-*` targets a real `E-*`; correct id family per section; dependency targets exist, no self-ref, no cycle.
  - Depends on: E-01
  - Expected outcome: orphan/duplicate/miswired ids and dependency cycles each flagged; a plan with more than 99 valid ids parses without an id-grammar error.
  - Execution state: performed
- [x] E-04 implement the state machine: execution + validation checkbox/state/evidence legality and E/V cross-constraints from the Order-01 tables; checkpoint-specific requirements for `author|review-finalize|pre-execution|pre-transition|post-transition`; question-field + size-assessment consistency. Every checkpoint checks ONLY deterministic structure/state (presence, grammar, recognized placeholders, cross-state legality); it MUST NOT assert semantic properties (meaningful atomicity, genuine observability, evidence sufficiency, truthful nonblocking classification), which stay with the semantic reviewer (spec Section 10.1).
  - Depends on: E-01
  - Expected outcome: each illegal combination and each checkpoint violation flagged; `pre-transition` rejects any non-`performed` E, non-`pass` V, unchecked V, or empty observed evidence; the boundary text in `--help`/output claims no semantic certainty.
  - Execution state: performed

### Task group 3: CLI + boundary + tests

- [x] E-05 wire `aw ipd lint` into the CLI: single-file mode plus `--all` repository aggregation; explicit `--phase`; conservative default inference that never infers a transition gate; `--agent` machine output with one deterministically escaped record per finding or disposition and no prose; stable rule codes + `path:line:col`; exit `0` for a successful evaluation with no conformance error, `1` for conformance errors, and `2` for invocation/internal failure. A zero exit with `quarantined` or `legacy/not evaluated` means evaluation succeeded, not conformance; authoritative gates require disposition `conforming`. Report conforming, quarantined, grandfathered, and erroneous outcomes distinctly; `--all` emits counts and exits 1 if erroneous is nonzero. Apply the dash rule to authored prose only.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: `aw ipd lint --help` states the structure-not-meaning boundary; exit codes behave per spec Section 10; a grandfathered file reports `legacy/not evaluated`; a quarantined file reports `quarantined`; neither is reported as passing.
  - Execution state: performed
- [x] E-06 add `tests/test_ipd_lint.py` with one named fixture or table row for every acceptance case in spec Section 16, including parser exclusions, both heading orders, every metadata invariant, watermark and dependency grammar, every legal/illegal state combination, each checkpoint including pre/post-transition consistency, OQ and size boundaries, migrated legacy, optional-section intervals, quarantine, repository aggregation, process-exit versus disposition semantics, `--agent` escaping, and dash-only-in-prose behavior. Assert a stable rule code + `path:line:col` for every failure.
  - Depends on: E-01, E-02, E-03, E-04, E-05
  - Expected outcome: table-driven + golden-fixture tests incl. legacy + quarantine + diagnostics; all pass.
  - Execution state: performed
- [x] E-07 run `python3 -m unittest tests.test_ipd_lint -v` then `python3 -m unittest discover -s tests -t .`; paste both.
  - Depends on: E-06
  - Expected outcome: new tests pass; suite green.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Imports the Order-01 `ipd_schema`; no restated constants.
- CLI style: argparse subcommands in `agent_workflows/cli.py`; add an `ipd` group with a `lint` action.
- Parser: implement a purpose-built, Python-standard-library structural reader for the bounded IPD grammar, retaining source positions and adding no runtime dependency.
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

`tests/test_ipd_lint.py` (E-06). Run `python3 -m unittest tests.test_ipd_lint -v` then `python3 -m unittest discover -s tests -t .`; paste both. Leak-clean; no em/en dashes.

## Spec / documentation sync

`aw ipd lint --help` documents the checkpoints + the structure-not-meaning boundary. Broader docs/DECISIONS/AGENTS pointer land in Order 06.

## Open questions

### OQ-01: Markdown parsing library vs in-repo reader

- Blocking: no
- Status: resolved
- Owner: this child's discovery step
- Resolution or deferral rationale: use the standard-library bounded structural reader defined above; test fenced and indented code, block quotes, actual YAML front matter, the bullet metadata block, and source positions.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste a test showing the spec example file's fenced/quoted headings are NOT parsed as IPD H2/checkboxes.
  - Observed evidence: `ipd_lint.parse` uses `_structural_lines` (fence/indent/YAML/blockquote aware). `ParserExclusionTests.test_fenced_example_not_parsed_as_structure` parses the live spec file and asserts its fenced `## Goal` / `## Detailed Implementation Checklist (TODO)` examples are NOT in `doc.h2` (`ok`); `test_yaml_front_matter_ignored` also `ok`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste tests where a misplaced execution heading, a duplicate heading, an out-of-order heading, a bad/duplicate/unknown metadata field, an orchestrator `Order != 0`, and a watermark below a present id each yield the expected coded error; and a metadata block with `auto-approved` is accepted.
  - Observed evidence: `HeadingTests` (missing/exec-not-after-goal/duplicate) + `MetadataLintTests` (unknown-field `IPD-M103`, orchestrator `Order` error, `auto-approved` accepted w/o Approval error, watermark-below-present `IPD-I304`) all `ok` in the 32-test run.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste tests for an orphan `V-*`, a duplicate `E-*`, a `V-*` with no matching `E-*`, and a dependency cycle, each flagged; and a plan with more than 99 valid ids (`E-100`) accepted by the id grammar.
  - Observed evidence: `IdBijectionTests.test_orphan_validation_flagged` (`IPD-I303`), `test_dependency_cycle_flagged` (`IPD-I305` "cycle"), `test_more_than_99_ids_ok` (`E-100` accepted; `suffix_of==100`) all `ok`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the table test covering every legal/illegal execution+validation combo and a `pre-transition` rejection of a non-`pass` V.
  - Observed evidence: `StateMachineTests` (checked-but-pending `IPD-S401`, pass-without-evidence `IPD-S402`/`IPD-S403`, `test_pre_transition_rejects_non_pass` -> `IPD-S404`) all `ok`; the underlying legal/illegal tables are exhaustively covered by Order-01 `test_ipd_schema` which this consumes.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `aw ipd lint --help` showing the structure-not-meaning boundary text; paste runs returning exit 0 (conform), 1 (lint error), and 2 (forced parse failure) distinctly; paste a grandfathered-file run reporting `legacy/not evaluated` (not a pass), a `--legacy` run doing the reduced checks, and a quarantined-file run reporting `quarantined` (not a pass); paste a dash-in-code case NOT flagged and a dash-in-prose case flagged.
  - Observed evidence: `--help` shows the `BOUNDARY_TEXT` (structure/state only). Live exit codes: conforming pending Order-02 file -> `exit=0` / `disposition: conforming`; executed Order-01 file -> `disposition: legacy/not evaluated`; missing file -> `exit=2`; `--all` with old-shape research-org plans present -> `exit=1` (`ExitCodeTests.test_all_exits_1_when_errors_present` `ok`). `DispositionTests` confirm quarantined + legacy are non-passing; `DashTests.test_dash_in_prose_flagged_but_not_in_code` confirms a fenced-code dash is NOT flagged while a prose dash is (`IPD-D701`).
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: paste the collected test count for `tests/test_ipd_lint.py` incl. parser/heading/id/state/checkpoint/exit-code fixtures.
  - Observed evidence: `python3 -m unittest tests.test_ipd_lint -v` -> `Ran 32 tests in 0.077s` / `OK`, across ParserExclusion/Conforming/Heading/MetadataLint/IdBijection/StateMachine/Checkpoint/OpenQuestionAndSize/Disposition/Dash/DiagnosticShape/ExitCode/AgentOutput/NoDependency classes.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: paste `pytest tests/test_ipd_lint.py -q` AND the full-suite summary (new tests pass, suite green).
  - Observed evidence: targeted `Ran 32 tests OK`; full `python3 -m unittest discover -s tests -t .` -> `Ran 515 tests in 149.720s` / `OK (skipped=1)` (483 -> 515 = +32; the 1 skip is the known release-tag test). Leak scan exit 0. (Runner is unittest per CONTRIBUTING.md; the "pytest" phrasing in the required-evidence line predates that correction.)
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Proposal; human review + approval required; not auto-executed. Correcting, independently reviewing, and formally approving the controlling spec is a prerequisite. Requires Order 01; if absent, STOP. This file may retain the historical bootstrap label because it creates lint; after it lands unavailable lint is a hard stop. Do not transition until every E/V pair is complete with evidence.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY this plan's files, path-scoped, never `git add -A`/`-a`, never push; `git add` new files first. Paste ACTUAL runner output; never claim a pass not run. No em or en dashes. STOP and report if execution exceeds scope (parser + read-only lint + CLI + tests; no write ops, no review wiring). Terminal transition is a POST-gate transaction, not a checklist item. Never create or push a tag / Release / PyPI upload.
