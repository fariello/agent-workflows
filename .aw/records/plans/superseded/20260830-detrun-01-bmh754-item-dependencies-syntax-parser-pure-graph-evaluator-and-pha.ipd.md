RETIRED 2026-08-30: residue LANDED, not abandoned; superseded by commit `8c437188` ("feat(schema,check): recognize From-Spec and flag dangling spec links", merged to main as `b0eb74e6` from lane `aw/lane/bmh754_attempt2`). This plan is retired because the ONE thing its own review left as real work is now shipped, and everything else it proposed was already shipped before it was authored. All four residue items verified present at HEAD `d08c1a1f`: (1) `From-Spec` recognition - `ipd_schema.META_FROM_SPEC` is in `META_RECOGNIZED` (verified live: `True`); (2) `check.from-spec-dangling` - present in `check_engine.RULE_REGISTRY` (verified live: `True`) with helper `check_from_spec_dangling`; (3) documentation - `AGENTS.md:140-146` documents `From-Spec` beside `From-Backlog` (the review asked for `.aw/records/plans/README.md`, but that file documents neither field, so `AGENTS.md` was the correct home and the doc residue is discharged there); (4) the 4-node cycle case - `tests/test_ipd_dependency_check.py:509` `test_cycle_four_node` exists and passes. Nothing is re-gated onto a successor because there IS no successor and no residue: the release gate `- Blocks-Release: next` is discharged by the landed commit, not dropped. Retired, not deleted; not filed under `executed/`, because THIS PLAN was never executed - its residue was landed by a narrower lane instead.

# IPD: Item-dependencies syntax parser, pure graph evaluator, and phased check/lint rules

- Date: 2026-08-30
- Kind: child
- Concern: FALSE AS WRITTEN (corrected /plan-review 2026-08-30 pass 2, PR-101). The premise below is obsolete: an explicit machine-enforced graph SHIPPED before this plan was authored, and circular dependencies and dangling references ARE caught today (verified live: `check.ipd-dependency-cycle` and `check.ipd-dependency-dangling` fire from `check_engine.evaluate_ipd_dependencies`). The one true residue in the original sentence is out-of-order EXECUTION, and that is owned by approved plan `lanetruth-03` (`8guhs0`), not by this plan. Original text, retained for the record: "Cross-item prerequisite relationships currently rely on implicit Set/Order sequencing or prose rather than an explicit, machine-enforced graph, leaving circular dependencies, dangling references, and out-of-order execution uncaught."
- Scope: OBSOLETE AS WRITTEN (corrected /plan-review 2026-08-30 pass 2, PR-101). Everything named below EXCEPT `From-Spec` recognition and `check.from-spec-dangling` is already shipped and must be CONSUMED, not rebuilt; spec 25kzda Sections 2.7-2.11 and 4.3 were implemented by the executed `ipddeps` Set. The true remaining scope is two small changes: add `From-Spec` to `ipd_schema.META_RECOGNIZED`, and add a `check.from-spec-dangling` rule mirroring the shipped `check.from-backlog-dangling`. Original text, retained for the record: "Implement the mandatory id6-grounded `Item-Dependencies` metadata grammar, `From-Spec` link metadata recognition, pure shared DAG evaluator, the 6 stable `check.ipd-dependency-*` rules in `check_engine.py`, `check.from-spec-dangling`, phased `ipd_lint.py` enforcement, `aw ipd dependencies set` CLI, and the opt-in `ipd-dependency-statement-gate` commit hook."
- Scope-Paths: agent_workflows/artifact_dependencies.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/check_engine.py, agent_workflows/engine.py, agent_workflows/cli.py, agent_workflows/config.py, tests/test_item_dependencies.py
- Item-Dependencies: none
- Status: superseded
- Set: detrun
- Order: 1
- Highest E allocated: 09
- Author: antigravity
- Id: bmh754
- Blocks-Release: next

## Workflow history
- 2026-08-31 superseded (aw set): RETIRED: residue LANDED (not abandoned). The only genuinely-unbuilt item its own REJECT-NEEDS-REPLAN review identified - From-Spec recognition plus check.from-spec-dangling - shipped in 8c437188 (merged b0eb74e6 from lane aw/lane/bmh754_attempt2). All 4 residue items verified present at HEAD d08c1a1f: META_FROM_SPEC in META_RECOGNIZED (live True), check.from-spec-dangling in RULE_REGISTRY (live True), From-Spec documented at AGENTS.md:140-146, and test_cycle_four_node at tests/test_ipd_dependency_check.py:509 passing. Everything else the plan proposed was shipped by the executed ipddeps Set BEFORE this plan was authored. No successor and no re-gating needed: the Blocks-Release gate is DISCHARGED by the landed commit, not dropped. Not filed under executed/ because this PLAN never ran; a narrower lane landed its residue.
- 2026-08-31 to-review (aw set): REVERTING MY OWN ERRONEOUS APPROVAL. I set this approved on 2026-08-30 from the maintainer's blanket instruction 'I APPROVE all the reviewed IPDs', which swept up a plan whose OWN newest /plan-review verdict is REJECT - NEEDS REPLAN. The --by-human attestation was real but the maintainer plainly did not intend to approve a do-not-execute plan; approving on status alone without reading each verdict was my mistake. Flagged by a peer agent (comms fyi 20260831-0126-01) and independently verified: all FIVE detrun plans carry REJECT, not just bmh754. Returning to to-review so 'approved' does not license a rebuild of shipped machinery.
- 2026-08-30 approved (aw set, --by-human): Approved by the maintainer: 'I APPROVE all the reviewed IPDs' (2026-08-30 session, verbatim standing instruction before stepping away).
- 2026-08-30 /plan-review pass 2 (OpenCode its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN reaffirmed on independent re-verification; PR-101..PR-108. Pass 1 marked the Goal and gate but left the plan's OWN prose still asserting falsehoods, so a reader skipping the Goal banner would still be misled. Fixed in place: Concern, Scope, Findings, Project conventions, Scope check, Proposed changes, Required tests, and Spec sync now state what actually ships, with the original text retained struck-through. All 9 E-items now carry a per-item DO-NOT-BUILD verdict plus `Execution state: blocked` with an execution note, and all 9 V-items' evidence is marked NOT TO BE COLLECTED, so nothing here can be mechanically ticked. New findings this pass: (PR-102) two of the three original Findings were outright false, not merely stale - cross-set prerequisites ARE statable (13 pending plans do it) and cycle detection DOES exist with 2- and 3-node tests; (PR-108) OQ-01's answer was correct but assigned to the wrong layer - verified `_resolve_edge` (check_engine.py:1724-1742) checks existence and type only, and the evaluator at phase=pre-execution over sibling detrun-03 (declaring `executed:bmh754`, never executed) returns ZERO findings, so runtime satisfaction is genuinely unbuilt but is owned by approved `lanetruth-03` (8guhs0), whose review already pinned that split as its F7; (PR-106) `check plans` was an unachievable validation bar (222 pre-existing scope-drift findings from other Sets), replaced with no-worsening. Also verified self-edge rejection ships (check_engine.py:1870), the shipped cutover helper is DATE-based not commit-based, `aw hooks install` does not exist, and the shipped test module already covers 30 of the ~32 cases E-08/E-09 proposed. Residue narrowed to exactly 4 items with 5 explicit prohibitions, recorded in the gate. Lint conforming at author and review-finalize; 0 lifecycle and 0 dependency findings on this file. NO-GO.
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
  - Expected outcome: **DO NOT BUILD - SHIPPED as `ipd_schema.parse_item_dependencies`/`canonical_item_dependencies` (ipd_schema.py:634,690). Verified live: accepts all edge kinds, canonicalizes order, rejects bad id6 alphabet/length, bad type-status pairing, duplicates, `none`+edge mixing, E-ids, and `state:ipd:executed:`. Self-edge rejection ships in the evaluator (check_engine.py:1870-1880), where the owner id is known.** Original expected outcome: Parser parses valid edges into typed `DependencyEdge` dataclasses, validates the id6 alphabet (6 lowercase chars), validates legal types (`ipd`, `spec`, `backlog`) and status tokens, rejects duplicate edges, rejects self-edges, rejects `state:ipd:executed:<id6>` (must be `executed:<id6>`), and round-trips cleanly through `format_dependency_statement()`.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

- [ ] E-02 Add metadata recognition for `Item-Dependencies` and `From-Spec` in `agent_workflows/ipd_schema.py` and wire metadata validation to `artifact_dependencies.py`.
  - Depends on: E-01
  - Expected outcome: **PARTLY SHIPPED - `Item-Dependencies` recognition is DONE (ipd_schema.py:207). ONLY `From-Spec` is missing. This is the plan's one real residue.** Original expected outcome: `ipd_schema.py` recognizes `Item-Dependencies` directly following `Scope-Paths` and recognizes `From-Spec` alongside `From-Backlog` in `META_RECOGNIZED` without `IPD-M103` unknown field errors.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

### Task group 2: Pure shared graph evaluator and consistency rules

- [ ] E-03 Implement `evaluate_item_dependencies()` in `agent_workflows/artifact_dependencies.py`: a pure, shared graph evaluator that resolves references against a repository snapshot or staged overlay, constructs a directed graph, detects cycles using Tarjan's strongly connected components algorithm, and evaluates edge satisfaction.
  - Depends on: E-01
  - Expected outcome: **DO NOT BUILD - SHIPPED as `check_engine.evaluate_ipd_dependencies` (check_engine.py:1750) with cycle detection via `item_dependency_cycles` and a staged-overlay entry point. NOTE it is deliberately STATIC (`_resolve_edge`, :1724, checks existence+type only); runtime SATISFACTION is owned by approved plan `lanetruth-03` (`8guhs0`), not by a new module here.** Original expected outcome: Evaluator returns structured findings for missing, unresolved, malformed, dangling, ambiguous, and cyclic dependency statements.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

- [ ] E-04 Register the 6 stable dependency rules in `agent_workflows/check_engine.py` (`check.ipd-missing-dependency-statement`, `check.ipd-dependency-unresolved`, `check.ipd-dependency-malformed`, `check.ipd-dependency-dangling`, `check.ipd-dependency-ambiguous`, `check.ipd-dependency-cycle`) plus `check.from-spec-dangling`, delegating directly to the shared evaluator.
  - Depends on: E-03
  - Expected outcome: **DO NOT BUILD the six rules - ALL SIX are registered (check_engine.py:121-137). ONLY `check.from-spec-dangling` is missing; copy the shipped `check.from-backlog-dangling` pattern.** Original expected outcome: `aw check plans` and `aw check all` evaluate repository-wide IPD dependencies and emit deterministic findings with exact recovery commands.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

### Task group 3: Phased linting and grandfathering cutover

- [ ] E-05 Add `dependency_schema_cutover_commit()` in `agent_workflows/config.py` and integrate phased `Item-Dependencies` validation into `agent_workflows/ipd_lint.py` across author, review-readiness, pre-execution, and pre-transition phases.
  - Depends on: E-03
  - Expected outcome: **DO NOT BUILD - SHIPPED. `config.dependency_cutover_date` (config.py:816) plus the phase matrix in the shared evaluator; phased lint already consumes it (ipd_lint.py:1046). Also note the shipped helper is DATE-based; do NOT reintroduce the commit-based `dependency_schema_cutover_commit()` this item proposed.** Original expected outcome: `unresolved` is advisory at author phase but blocking at review-readiness/pre-execution; missing field on post-cutover plans is an error; pre-cutover terminal plans in `executed/` receive grandfathered advisory; frozen statement at execution must match reviewed statement.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

### Task group 4: Tooling and pre-commit hook

- [ ] E-06 Add the `aw ipd dependencies set <selector> <edges...>` command in `agent_workflows/cli.py` and `agent_workflows/ipd_cli.py`.
  - Depends on: E-01, E-03
  - Expected outcome: **DO NOT BUILD - SHIPPED. `aw ipd dependencies set` exists (verified via `aw ipd dependencies --help`), canonicalizes and validates before writing.** Original expected outcome: Setter validates input, writes canonical metadata line, appends workflow history receipt, and runs shared evaluator before committing path-scoped changes.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

- [ ] E-07 Add the opt-in `ipd-dependency-statement-gate` local pre-commit hook in `agent_workflows/engine.py` and wire `aw hooks install ipd-dependency-statement-gate`.
  - Depends on: E-03
  - Expected outcome: **DO NOT BUILD - SHIPPED as `agent_workflows/hooks/ipd_dependency_statement_gate.py`, exposed as the `ipd-dependency-statement-gate` verb. NOTE `aw hooks install` does NOT exist; the verb is top-level, so a replacement plan must not cite a nonexistent installer.** Original expected outcome: Pre-commit hook checks staged `.ipd.md` files against HEAD overlay, preventing invalid or cyclic dependency edits from being committed while allowing unrelated commits.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

### Task group 5: Test suite coverage and edge cases

- [ ] E-08 Create `tests/test_item_dependencies.py` covering parser round-trips, canonical sorting, satisfaction semantics for all edge types, 2-node/3-node/4-node cycle detection, dangling links, phased linting, grandfathering, setter CLI, and pre-commit hook.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07
  - Expected outcome: **DO NOT BUILD - SHIPPED. `tests/test_ipd_dependency_check.py` (373 lines, 32 tests) and `tests/test_ipd_dependency_statement_gate.py` (253 lines) already cover parser round-trips, satisfaction-layer resolution, 2-node and 3-node cycles, dangling, ambiguous, phased lint, and grandfathering.** Original expected outcome: Comprehensive test suite passes with 100% branch coverage on graph evaluation and satisfaction logic.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

- [ ] E-09 Add adversarial edge case tests: duplicate edges, self-loops, mixed `none` + edge, malformed id6 characters, `state:ipd:executed:` rejection, non-existent status token, and cross-type identity collision.
  - Depends on: E-08
  - Expected outcome: **MOSTLY SHIPPED - existing tests already cover self-dependency (:130), ambiguity/cross-type collision (:138,:156,:162), malformed (:120), and the no-auto-`none` rule (:361). A 4-node cycle case appears absent and would be a one-test addition, not a plan.** Original expected outcome: All edge case tests assert exact stable finding codes and verify fail-closed error reporting.
  - Execution state: blocked
  - Execution note: BLOCKED BY REVIEW (/plan-review 2026-08-30 pass 2). Not to be executed: this item is superseded by shipped code (or, for E-02/E-04/E-09, all but a small residue is). See the verdict in Expected outcome and the `## Goal` evidence table. Do not tick this box.

## Project conventions discovered (Step 0)

CORRECTED /plan-review 2026-08-30 pass 2 (PR-104): these were recorded as conventions to CONFORM TO
while building, but three of the four describe code that already exists, which is precisely the
inventory step the plan skipped.

- `ipd_schema.META_RECOGNIZED` contains recognized front-matter fields. `Item-Dependencies` is ALREADY
  there (`ipd_schema.py:207`, constant at `:168`) and the grammar is documented in-module at `:487-505`.
  Nothing to add.
- `From-Spec` is intended as the canonical spec-to-plan linkage field mirroring `From-Backlog`. It is
  NOT yet recognized; this is the plan's one real gap.
- `check_engine.py` registers rules via a `RuleSpec` table. All six `check.ipd-dependency-*` rules are
  ALREADY registered (`:121-137`) under catalog `I-08`. Only `check.from-spec-dangling` is missing, and
  the existing `check.from-backlog-dangling` is the pattern to copy.
- Grandfathering is ALREADY implemented and is DATE-based, not commit-based: `config.dependency_cutover_date`
  (`config.py:816`) plus the phase matrix in `evaluate_ipd_dependencies`. An absent marker grandfathers
  everything, so the historical corpus is never mass-failed. A replacement plan must NOT reintroduce the
  commit-based variant E-05 proposed.

## Findings

CORRECTED /plan-review 2026-08-30 pass 2 (PR-102). Two of the three original findings were factually
false at authoring time. Struck text is retained so the record shows what was claimed.

- ~~"Prerequisite execution between child plans currently depends on sequential Set/Order numbering; an
  out-of-order dependency or cross-set prerequisite cannot be explicitly stated."~~ FALSE: a cross-set
  prerequisite CAN be explicitly stated today, and 13 pending plans already do. This very plan's
  siblings declare `executed:bmh754` / `executed:a54m79`. The field, grammar, and setter all ship.
- ~~"`ipd_lint.py` and `check_engine.py` have no mechanism to detect circular dependencies between
  plans..."~~ FALSE: both consume `check_engine.evaluate_ipd_dependencies` (`ipd_lint.py:1046`), which
  builds one directed graph and emits `check.ipd-dependency-cycle`. Shipped tests cover 2-node and
  3-node cycles (`tests/test_ipd_dependency_check.py:145,150`).
- PARTLY TRUE, and the only surviving finding: "...or verify that prerequisite artifacts are executed
  before execution begins." The shipped evaluator is deliberately STATIC. Verified: `_resolve_edge`
  (`check_engine.py:1724-1742`) answers existence and type only, and running the evaluator at
  `phase="pre-execution"` over `detrun-03` (which declares `executed:bmh754`, a plan that has never
  been executed) returns ZERO findings. So SATISFACTION is genuinely unimplemented in the static layer
  by design. It is NOT this plan's residue: approved plan `lanetruth-03` (`8guhs0`) owns it, and its
  own review already pinned the static-vs-runtime split as finding F7, verifying that the shared
  evaluator "contains no notion of a run, a queue, an item outcome, or `verified`".
- TRUE and unbuilt: `From-Spec` is needed to link generated IPDs back to approved specs without an
  `IPD-M103` unknown-field error. Verified absent from `META_RECOGNIZED` and no `from-spec` rule exists
  in `check_engine.py` (the only `from_spec` greps are unrelated `importlib.module_from_spec` calls).

## Proposed changes (ordered, validatable)

SUPERSEDED /plan-review 2026-08-30 pass 2 (PR-105). Do not perform this sequence: steps 1, 3, 4, 5, 6,
7, and 8 all rebuild shipped code, and step 2 is done except for `From-Spec`.

The ONLY changes a replacement plan should make, both small:

1. Add `From-Spec` to `ipd_schema.META_RECOGNIZED` (constant beside `META_FROM_BACKLOG` at
   `ipd_schema.py:209`), so a spec-generated IPD can carry the link without an `IPD-M103` unknown-field
   error.
2. Add `check.from-spec-dangling` to the `check_engine.py` `RuleSpec` table, copying the shipped
   `check.from-backlog-dangling` rule and its resolution helper.

That is a single focused pass touching two files plus one test module. It does not need a 9-item plan,
and it must NOT create `agent_workflows/artifact_dependencies.py`.

Original sequence, retained for the record:

1. ~~Add pure parser/serializer in `agent_workflows/artifact_dependencies.py` (E-01).~~
2. Register `Item-Dependencies` and `From-Spec` in `ipd_schema.py` (E-02) - only the `From-Spec` half.
3. ~~Implement pure DAG evaluator and cycle detector (E-03).~~
4. ~~Register the 6 `check.ipd-dependency-*` rules~~ and `check.from-spec-dangling` in `check_engine.py` (E-04).
5. ~~Add phased validation and cutover helper in `ipd_lint.py` and `config.py` (E-05).~~
6. ~~Implement `aw ipd dependencies set` CLI (E-06).~~
7. ~~Implement opt-in pre-commit hook in `engine.py` (E-07).~~
8. ~~Cover everything with comprehensive tests in `test_item_dependencies.py` (E-08, E-09).~~

## Deferred / out of scope (with reason)

- **Source-side dependencies on specs and backlog items**: Deferred per spec Section 2.8; specs and backlog items serve as targets in v1.
- **DAG queue scheduling and execution**: Deferred to child plan `detrun-03` (`kaygwo`).

## Scope check

CORRECTED /plan-review 2026-08-30 pass 2 (PR-103). The original claim below was false in both
directions.

- Over-scope: SEVERE. 8 of 9 E-items rebuild shipped machinery (per-item evidence in the `## Goal`
  table). E-01/E-03 would create `agent_workflows/artifact_dependencies.py` duplicating
  `ipd_schema.parse_item_dependencies` and `check_engine.evaluate_ipd_dependencies`; E-04 would
  re-register six rules that are already registered; E-05 would add a cutover helper beside
  `config.dependency_cutover_date`; E-06/E-07 would re-add a shipped verb and a shipped hook; E-08/E-09
  would duplicate 626 lines of existing tests. Executing this plan makes the repo worse, not better:
  two parsers and two evaluators for one field is exactly the drift GUIDING_PRINCIPLES P8 forbids.
- Under-scope: the plan never inventoried the shipped implementation before proposing to build it,
  which is why every "no mechanism exists" finding was wrong. It also mis-attributes the ONE real gap
  it brushes against (runtime satisfaction) to itself rather than to approved plan `lanetruth-03`
  (`8guhs0`), and its `Scope-Paths` claims `agent_workflows/engine.py` and `cli.py`, files that
  `rununify`/other approved Sets are actively contending.
- Original text, retained for the record: "Over-scope: none. Strictly implements the
  `Item-Dependencies` data layer, rules, and linter gates. Under-scope: none. All 6 rules from spec
  Section 2.10 and `From-Spec` link recognition are implemented and tested."

## Required tests / validation

CORRECTED /plan-review 2026-08-30 pass 2 (PR-106). Two of these three were unachievable as written, so
an executor would have been blocked or tempted to fake a pass.

- ~~`python3 -m pytest tests/test_item_dependencies.py`~~ - that module does not exist and must not be
  created; it would duplicate `tests/test_ipd_dependency_check.py` (32 tests) and
  `tests/test_ipd_dependency_statement_gate.py`. Run those instead, and add at most one 4-node-cycle case.
- ~~`check plans` passing~~ - NOT achievable and never was: `aw check plans` is currently RED on 222
  pre-existing `check.scope-drift` findings across other Sets' plans, none owned by this plan. The
  honest bar is NO-WORSENING against a re-measured baseline, not "passing".
- `aw ipd lint --phase author <path>` conforming - achievable, and verified conforming for this file
  after the pass-2 edits.
- For the surviving residue, the real validation is: a fixture IPD carrying `From-Spec: <id6>` lints
  without `IPD-M103`, and `check.from-spec-dangling` fires on an unresolvable id6 and stays silent on a
  resolvable one.

## Spec / documentation sync

CORRECTED /plan-review 2026-08-30 pass 2 (PR-107).

- Sections 2.7-2.11 and 4.3 of spec `25kzda` were ALREADY IMPLEMENTED, by the `ipddeps` Set (`r7xku3`,
  `g69y23`, `ovbnyq`, `mp88bl`, all `executed`), whose plans cite those same section numbers. This plan
  claiming to implement them is the duplication, restated as traceability.
- The spec itself already records this: its corrected infrastructure-status paragraph names
  `Item-Dependencies`, `aw ipd dependencies`, and `aw runs` as shipped, and lists `From-Spec` among the
  STILL NET-NEW items. So the spec and this correction agree; only the plan was stale.
- Documentation residue that is still real: `.aw/records/plans/README.md` documents `Item-Dependencies`
  but not `From-Spec`, so a `From-Spec` plan should add it there beside the existing `From-Backlog`
  paragraph.
- Do NOT re-document the `Item-Dependencies` grammar; it is already documented in-module at
  `ipd_schema.py:487-505` and in `AGENTS.md`. Duplicating it would violate P8.

## Open questions

### OQ-01: Should `executed:<id6>` accept an executed plan whose status text says executed but lacks valid finalization evidence?

- Blocking: no
- Status: resolved
- Owner: resolved from spec 25kzda Section 2.7
- Resolution or deferral rationale: RESOLVED per the spec, but CORRECTED /plan-review 2026-08-30 pass 2
  (PR-108) because the answer described a layer this plan does not own, which would have misled an
  executor into building satisfaction logic here. Spec 2.9 does require status `executed` in `executed/`
  PLUS valid finalization evidence. However that is RUNTIME SATISFACTION, and it is NOT enforced by, and
  must not be added to, the shared static evaluator: verified `_resolve_edge` (`check_engine.py:1724-1742`)
  answers existence and type ONLY, and running the evaluator at `phase="pre-execution"` over sibling
  `detrun-03` (which declares `executed:bmh754`, never executed) returns ZERO findings. Satisfaction is
  owned by approved plan `lanetruth-03` (`8guhs0`), whose own review pinned this static-vs-runtime split
  as its finding F7. So: correct answer, wrong owner. A replacement plan must not implement it.

### OQ-02: Is a 4-node cycle case genuinely missing from the shipped cycle tests?

- Blocking: no
- Status: resolved
- Owner: resolved from repository evidence (/plan-review pass 2)
- Resolution or deferral rationale: RESOLVED - Yes, apparently missing, and it is trivial. Shipped tests
  cover `test_cycle_two_node` and `test_cycle_three_node` (`tests/test_ipd_dependency_check.py:145,150`)
  but no 4-node case. Since cycle detection uses a general strongly-connected-components routine
  (`item_dependency_cycles`) rather than length-specific logic, a 4-node case adds little assurance and
  is at most a one-test addition to the EXISTING module. It does not justify E-08/E-09, and it must not
  become the pretext for a new `tests/test_item_dependencies.py`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: Python test showing parser accepting all 4 edge types, canonical sorting, and rejecting invalid tokens.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: Pytest showing `ipd_schema.py` recognizing `Item-Dependencies` and `From-Spec` without `IPD-M103` unknown field error.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: Test session demonstrating cycle detection (2-node, 3-node, and 4-node cycles) and satisfaction checking for `executed:`, `exists:`, and `state:`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: `aw check plans` output demonstrating all 6 `check.ipd-dependency-*` rules and `check.from-spec-dangling` firing appropriately on synthetic fixtures.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: `aw ipd lint` runs across author, review-readiness, pre-execution, and pre-transition showing expected error/advisory dispositions and grandfathering behavior.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: CLI session running `aw ipd dependencies set` on a test plan, verifying resulting file format and workflow history.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: Hook execution test showing `ipd-dependency-statement-gate` blocking a cyclic commit and permitting a valid commit.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: `pytest tests/test_item_dependencies.py` passing with test counts pasted.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: **NOT TO BE COLLECTED (REPLAN, /plan-review pass 2): the matching E-item is superseded by shipped code; collecting this would mean proving a duplicate was built.** Original required evidence: Pytest assertions verifying rejection of self-loops, malformed id6 tokens, and invalid edge syntax with stable finding codes.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

**GATE: CLOSED. `REJECT - NEEDS REPLAN` (/plan-review 2026-08-30, reaffirmed pass 2).** Do NOT execute
and do NOT approve. 8 of 9 E-items are already shipped (per-item evidence in the `## Goal` table and in
each E-item's own verdict). Every E-item is marked `Execution state: blocked` with an execution note, and
every V-item's evidence is marked NOT TO BE COLLECTED, so there is nothing here to tick. An executor
reaching this gate must STOP and report.

Open questions: OQ-01 and OQ-02 are both resolved from repository evidence; neither needs you. Note
OQ-01's answer is correct but belongs to `lanetruth-03`, not here.

Retirement: retire with the parent Set `detrun` (`r4mbcw`). Prepend a `RETIRED 2026-08-30: <reason>;
superseded by <path/commit>` header and `git mv` to `.aw/records/plans/superseded/`. Do NOT file under
`executed/`; nothing was implemented. Do not silently delete.

Release gate: this plan carries `- Blocks-Release: next`. Retiring it drops that gate, so the residue
below must be re-gated onto its replacement (or the gate explicitly cleared by the maintainer).

THE ENTIRE SURVIVING RESIDUE, for whoever writes the replacement (one focused pass, two files plus one
test module):

1. Add `From-Spec` to `ipd_schema.META_RECOGNIZED`, beside `META_FROM_BACKLOG` (`ipd_schema.py:209`).
2. Add `check.from-spec-dangling` to the `check_engine.py` `RuleSpec` table, copying the shipped
   `check.from-backlog-dangling` rule and its resolution helper.
3. Document `From-Spec` in `.aw/records/plans/README.md` beside `From-Backlog`.
4. Optionally add a 4-node cycle case to the EXISTING `tests/test_ipd_dependency_check.py` (OQ-02).

Explicit prohibitions for that replacement: do NOT create `agent_workflows/artifact_dependencies.py`;
do NOT create `tests/test_item_dependencies.py`; do NOT add a commit-based cutover helper (the shipped
one is date-based); do NOT cite `aw hooks install` (no such verb; the gate is a top-level verb); and do
NOT implement runtime dependency satisfaction (owned by `lanetruth-03`, `8guhs0`).

Scope fence for that replacement: `agent_workflows/ipd_schema.py`, `agent_workflows/check_engine.py`,
`.aw/records/plans/README.md`, and `tests/test_ipd_dependency_check.py`. Both source files are actively
contended in this SHARED CHECKOUT, so verify `git diff --cached --name-only` before every commit and
unstage anything not yours. If it seems to need more, STOP and report.

Honesty rule (HARD MUST): when reporting tests or validation, paste the ACTUAL runner output with the
`git rev-parse HEAD` it was measured at. Specifically, do NOT claim `aw check plans` passes: it is
currently RED on 222 pre-existing `check.scope-drift` findings owned by other Sets. The bar is
no-worsening against a freshly measured baseline.

Execution contract: commit ONLY the files changed, path-scoped (`git commit -m msg -- <paths>`), never
`git add -A`, never push. Post-gate lifecycle is `aw ipd finalize`, never a hand-move. Do not create or
push a tag or release.
