# IPD: Item-dependencies syntax parser, pure graph evaluator, and phased check/lint rules

- Date: 2026-08-30
- Kind: child
- Concern: Cross-item prerequisite relationships currently rely on implicit Set/Order sequencing or prose rather than an explicit, machine-enforced graph, leaving circular dependencies, dangling references, and out-of-order execution uncaught.
- Scope: Implement the mandatory id6-grounded `Item-Dependencies` metadata grammar, `From-Spec` link metadata recognition, pure shared DAG evaluator, the 6 stable `check.ipd-dependency-*` rules in `check_engine.py`, `check.from-spec-dangling`, phased `ipd_lint.py` enforcement, `aw ipd dependencies set` CLI, and the opt-in `ipd-dependency-statement-gate` commit hook. Implements spec 25kzda Sections 2.7-2.11 and 4.3.
- Scope-Paths: agent_workflows/artifact_dependencies.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/config.py, tests/test_item_dependencies.py
- Item-Dependencies: none
- Status: reviewed
- Set: detrun
- Order: 1
- Highest E allocated: 09
- Author: antigravity
- Id: bmh754
- Blocks-Release: next

## Workflow history
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): PR-006 fix. Normalized this history block to NEWEST-FIRST, the order `ipd_lifecycle._plan_status_events` assumes (it reverses to derive oldest-first). As authored the block was oldest-first, so the derived event stream read `to-review -> draft` and `aw check plans` reported `check.lifecycle-transition-invalid` ("backwards transition") on all 6 detrun plans. Verified pre-existing at pre-review commit `d4d265b6` (6 findings) and 0 after this fix. Content of every entry is unchanged; only line order.
- 2026-08-30 reviewed (aw set): plan-review: REJECT - NEEDS REPLAN (most of Set already shipped; collides with 3 approved Sets)
- 2026-08-30 /plan-review (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN; PR-001. Verified at HEAD `d4d265b6` that E-01..E-09 are ALREADY SHIPPED: `ipd_schema.parse_item_dependencies`/`canonical_item_dependencies` (ipd_schema.py:634,690, executed live), `META_ITEM_DEPENDENCIES` in META_RECOGNIZED (:207), `check_engine.evaluate_ipd_dependencies` with cycle detection (check_engine.py:1750), all six `check.ipd-dependency-*` rules (:121-137), `config.dependency_cutover_date` (config.py:816), phased lint consumption (ipd_lint.py:1046), the `aw ipd dependencies set` verb, the `ipd-dependency-statement-gate` hook, and 626 lines of tests. All graduated from this SAME spec 25kzda by the executed `ipddeps` Set (r7xku3/g69y23/ovbnyq/mp88bl). Only residue: `From-Spec` recognition + `check.from-spec-dangling`. Gate closed. NO-GO.
- 2026-08-30 to-review (antigravity): deepened edge cases, From-Spec schema recognition, cycle detection, and grandfathering cutover helpers.
- 2026-08-30 to-review (antigravity): authored from approved spec 25kzda (20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md).
- 2026-08-30 draft (antigravity): created.

## Goal

**REPLAN - DO NOT EXECUTE (/plan-review 2026-08-30, PR-001 BLOCKER).** This plan's goal is already
SHIPPED. It would build a second copy of working machinery. Verified at HEAD `d4d265b6`:

| This plan's E-item | Already shipped as | Evidence |
| --- | --- | --- |
| E-01 grammar parser/serializer | `ipd_schema.parse_item_dependencies`, `canonical_item_dependencies` | `agent_workflows/ipd_schema.py:634,690` (ran it: parses all edge types, canonicalizes, rejects duplicates and `state:ipd:executed:`) |
| E-02 `Item-Dependencies` recognition | `META_ITEM_DEPENDENCIES` in `META_RECOGNIZED` | `agent_workflows/ipd_schema.py:168,207` |
| E-03 pure graph evaluator + cycle detection | `check_engine.evaluate_ipd_dependencies` | `agent_workflows/check_engine.py:1750`, cycles via `item_dependency_cycles` |
| E-04 six `check.ipd-dependency-*` rules | all six registered | `agent_workflows/check_engine.py:121-137` |
| E-05 cutover helper + phased lint | `config.dependency_cutover_date`; lint consumes shared evaluator | `agent_workflows/config.py:816`; `agent_workflows/ipd_lint.py:1046` |
| E-06 `aw ipd dependencies set` | shipped verb | `aw ipd dependencies --help` |
| E-07 opt-in commit hook | shipped | `agent_workflows/hooks/ipd_dependency_statement_gate.py`; `ipd-dependency-statement-gate` verb |
| E-08/E-09 tests | shipped | `tests/test_ipd_dependency_check.py` (373 lines), `tests/test_ipd_dependency_statement_gate.py` (253 lines) |

All of it was graduated from THIS SAME spec `25kzda` by the earlier `ipddeps` Set (`r7xku3`, `g69y23`,
`ovbnyq`, `mp88bl` - all verified `executed`), whose plans cite spec sections 2.7-2.11 by name. This
plan was authored at `453673b6` (2026-08-30 00:08) against a spec paragraph that wrongly called the
design net-new; the maintainer corrected that paragraph at `a59f2c53` (00:35), and the corrected spec
now says a graduating Set "must CONSUME, not rebuild" this machinery.

The ONLY genuinely unbuilt residue here is `From-Spec` recognition plus a `check.from-spec-dangling`
rule (`From-Spec` is absent from `META_RECOGNIZED`, and no `from-spec` rule exists in
`check_engine.py`). That is a small, self-contained change and does not need a plan of this size.

Original goal, retained for the record: provide a single, pure, canonical `Item-Dependencies` parser,
schema validator, and graph evaluator that enforces explicit prerequisite edges across IPDs, specs,
and backlog items.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Grammar parser and schema recognition

- [ ] E-01 Create `agent_workflows/artifact_dependencies.py` implementing the canonical `Item-Dependencies` grammar parser and serializer supporting `none`, `executed:<id6>`, `exists:<type>:<id6>`, and `state:<type>:<status>:<id6>` with strict canonical sort ordering.
  - Depends on: none
  - Expected outcome: Parser parses valid edges into typed `DependencyEdge` dataclasses, validates the id6 alphabet (6 lowercase chars), validates legal types (`ipd`, `spec`, `backlog`) and status tokens, rejects duplicate edges, rejects self-edges, rejects `state:ipd:executed:<id6>` (must be `executed:<id6>`), and round-trips cleanly through `format_dependency_statement()`.
  - Execution state: pending

- [ ] E-02 Add metadata recognition for `Item-Dependencies` and `From-Spec` in `agent_workflows/ipd_schema.py` and wire metadata validation to `artifact_dependencies.py`.
  - Depends on: E-01
  - Expected outcome: `ipd_schema.py` recognizes `Item-Dependencies` directly following `Scope-Paths` and recognizes `From-Spec` alongside `From-Backlog` in `META_RECOGNIZED` without `IPD-M103` unknown field errors.
  - Execution state: pending

### Task group 2: Pure shared graph evaluator and consistency rules

- [ ] E-03 Implement `evaluate_item_dependencies()` in `agent_workflows/artifact_dependencies.py`: a pure, shared graph evaluator that resolves references against a repository snapshot or staged overlay, constructs a directed graph, detects cycles using Tarjan's strongly connected components algorithm, and evaluates edge satisfaction.
  - Depends on: E-01
  - Expected outcome: Evaluator returns structured findings for missing, unresolved, malformed, dangling, ambiguous, and cyclic dependency statements.
  - Execution state: pending

- [ ] E-04 Register the 6 stable dependency rules in `agent_workflows/check_engine.py` (`check.ipd-missing-dependency-statement`, `check.ipd-dependency-unresolved`, `check.ipd-dependency-malformed`, `check.ipd-dependency-dangling`, `check.ipd-dependency-ambiguous`, `check.ipd-dependency-cycle`) plus `check.from-spec-dangling`, delegating directly to the shared evaluator.
  - Depends on: E-03
  - Expected outcome: `aw check plans` and `aw check all` evaluate repository-wide IPD dependencies and emit deterministic findings with exact recovery commands.
  - Execution state: pending

### Task group 3: Phased linting and grandfathering cutover

- [ ] E-05 Add `dependency_schema_cutover_commit()` in `agent_workflows/config.py` and integrate phased `Item-Dependencies` validation into `agent_workflows/ipd_lint.py` across author, review-readiness, pre-execution, and pre-transition phases.
  - Depends on: E-03
  - Expected outcome: `unresolved` is advisory at author phase but blocking at review-readiness/pre-execution; missing field on post-cutover plans is an error; pre-cutover terminal plans in `executed/` receive grandfathered advisory; frozen statement at execution must match reviewed statement.
  - Execution state: pending

### Task group 4: Tooling and pre-commit hook

- [ ] E-06 Add the `aw ipd dependencies set <selector> <edges...>` command in `agent_workflows/cli.py` and `agent_workflows/ipd_cli.py`.
  - Depends on: E-01, E-03
  - Expected outcome: Setter validates input, writes canonical metadata line, appends workflow history receipt, and runs shared evaluator before committing path-scoped changes.
  - Execution state: pending

- [ ] E-07 Add the opt-in `ipd-dependency-statement-gate` local pre-commit hook in `agent_workflows/engine.py` and wire `aw hooks install ipd-dependency-statement-gate`.
  - Depends on: E-03
  - Expected outcome: Pre-commit hook checks staged `.ipd.md` files against HEAD overlay, preventing invalid or cyclic dependency edits from being committed while allowing unrelated commits.
  - Execution state: pending

### Task group 5: Test suite coverage and edge cases

- [ ] E-08 Create `tests/test_item_dependencies.py` covering parser round-trips, canonical sorting, satisfaction semantics for all edge types, 2-node/3-node/4-node cycle detection, dangling links, phased linting, grandfathering, setter CLI, and pre-commit hook.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: Comprehensive test suite passes with 100% branch coverage on graph evaluation and satisfaction logic.
  - Execution state: pending

- [ ] E-09 Add adversarial edge case tests: duplicate edges, self-loops, mixed `none` + edge, malformed id6 characters, `state:ipd:executed:` rejection, non-existent status token, and cross-type identity collision.
  - Depends on: E-08
  - Expected outcome: All edge case tests assert exact stable finding codes and verify fail-closed error reporting.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `ipd_schema.META_RECOGNIZED` contains recognized front-matter fields; `Item-Dependencies` must be placed immediately following `Scope-Paths`.
- `From-Spec` is the canonical spec-to-plan linkage field, mirroring `From-Backlog`.
- `check_engine.py` registers rules via `RuleSpec` table with unique identifiers, severity levels, and descriptive messages; all 6 dependency rules plus `check.from-spec-dangling` must be added there.
- Grandfathering precedent: `Scope-Paths: grandfathered` or cutoff-commit checks allow existing terminal plans to pass lint while requiring active plans to conform.

## Findings

- Prerequisite execution between child plans currently depends on sequential Set/Order numbering; an out-of-order dependency or cross-set prerequisite cannot be explicitly stated.
- `ipd_lint.py` and `check_engine.py` have no mechanism to detect circular dependencies between plans or verify that prerequisite artifacts are executed before execution begins.
- `From-Spec` is needed to link generated IPDs back to approved specifications without triggering `IPD-M103` unknown field lint errors.

## Proposed changes (ordered, validatable)

1. Add pure parser/serializer in `agent_workflows/artifact_dependencies.py` (E-01).
2. Register `Item-Dependencies` and `From-Spec` in `ipd_schema.py` (E-02).
3. Implement pure DAG evaluator and cycle detector (E-03).
4. Register the 6 `check.ipd-dependency-*` rules and `check.from-spec-dangling` in `check_engine.py` (E-04).
5. Add phased validation and cutover helper in `ipd_lint.py` and `config.py` (E-05).
6. Implement `aw ipd dependencies set` CLI (E-06).
7. Implement opt-in pre-commit hook in `engine.py` (E-07).
8. Cover everything with comprehensive tests in `test_item_dependencies.py` (E-08, E-09).

## Deferred / out of scope (with reason)

- **Source-side dependencies on specs and backlog items**: Deferred per spec Section 2.8; specs and backlog items serve as targets in v1.
- **DAG queue scheduling and execution**: Deferred to child plan `detrun-03` (`kaygwo`).

## Scope check

- Over-scope: none. Strictly implements the `Item-Dependencies` data layer, rules, and linter gates.
- Under-scope: none. All 6 rules from spec Section 2.10 and `From-Spec` link recognition are implemented and tested.

## Required tests / validation

- `python3 -m pytest tests/test_item_dependencies.py` passing.
- `python3 -m agent_workflows.cli check plans` passing.
- `python3 -m agent_workflows.cli ipd lint --phase author <path>` passing.

## Spec / documentation sync

- Implements spec `25kzda` (`20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md`) Sections 2.7-2.11 and 4.3.
- Updates `.aw/records/plans/README.md` to document the `Item-Dependencies` and `From-Spec` metadata field syntax and rules.

## Open questions

### OQ-01: Should `executed:<id6>` accept an executed plan whose status text says executed but lacks valid finalization evidence?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.7
- Resolution or deferral rationale: RESOLVED - No. `executed:<id6>` requires both status `executed` in `executed/` AND valid finalization/terminal lint evidence. Mere status text without valid location/evidence fails satisfaction.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Python test showing parser accepting all 4 edge types, canonical sorting, and rejecting invalid tokens.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: Pytest showing `ipd_schema.py` recognizing `Item-Dependencies` and `From-Spec` without `IPD-M103` unknown field error.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: Test session demonstrating cycle detection (2-node, 3-node, and 4-node cycles) and satisfaction checking for `executed:`, `exists:`, and `state:`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: `aw check plans` output demonstrating all 6 `check.ipd-dependency-*` rules and `check.from-spec-dangling` firing appropriately on synthetic fixtures.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: `aw ipd lint` runs across author, review-readiness, pre-execution, and pre-transition showing expected error/advisory dispositions and grandfathering behavior.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: CLI session running `aw ipd dependencies set` on a test plan, verifying resulting file format and workflow history.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: Hook execution test showing `ipd-dependency-statement-gate` blocking a cyclic commit and permitting a valid commit.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: `pytest tests/test_item_dependencies.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: Pytest assertions verifying rejection of self-loops, malformed id6 tokens, and invalid edge syntax with stable finding codes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30).** Do NOT execute and do NOT approve.
Nearly every E-item here is already shipped (see the table under `## Goal` for per-item evidence). An
executor reaching this gate must STOP and report. Retire with the parent Set `detrun` (`r4mbcw`); do not
file under `executed/`. The surviving residue (`From-Spec` + `check.from-spec-dangling`) belongs in a
new, much smaller plan.
