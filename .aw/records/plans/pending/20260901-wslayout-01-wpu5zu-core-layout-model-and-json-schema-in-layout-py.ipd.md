# IPD: Core Layout Model and JSON Schema in layout.py

- Date: 2026-09-01
- Kind: child
- Concern: Workspace layout definitions need a single source of truth in Python with strongly-typed dataclasses and deterministic JSON / JSON Schema generation per Spec kw5y2s.
- Scope: Create `agent_workflows/layout.py` with dataclasses (`RecordClassDefinition`, `LayoutModel`), canonical layout constants, `build_default_layout()`, `to_json()`, and `to_schema()`. Add unit tests in `tests/test_layout.py`.
- Scope-Paths: agent_workflows/layout.py, tests/test_layout.py
- Item-Dependencies: none
- Status: to-review
- Set: wslayout
- Order: 1
- Highest E allocated: 02
- Author: antigravity
- Id: wpu5zu
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - Survives nearly intact (PR-001 vocabulary pinning only); the additive layout.py + tests/test_layout.py shape is correct.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all eight findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).

## Goal

Provide a standalone, pure Python layout model module (`agent_workflows/layout.py`) that encapsulates all workspace logical roots, record classes, state classes, traversal exclusions, and JSON schema emission.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Layout Model Module

- [ ] E-01 Create `agent_workflows/layout.py` defining frozen dataclasses (`RecordClassDefinition`, `LayoutModel`), `build_default_layout()`, `to_dict()`, `to_json(framework_version)`, `to_schema()`, and helper lookup methods (`get_record_subpath()`, `is_known_type()`, `normalize_type()`).
  - Depends on: none
  - Expected outcome: `agent_workflows/layout.py` exists with complete typed layout definitions.
  - Execution state: pending
  - VOCABULARY IS THE UNION (maintainer ruling 2026-09-01, plan-review PR-001). The model MUST document
    reality, not redefine it. The draft spec's table is WRONG and MUST NOT be copied verbatim: it omits
    `roadmaps` and `records` and adds `reviews`/`backlog`/`other`. Measured truth at HEAD:
    `ARTIFACT_TYPES` = plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms,
    releases, other (`agent_workflows/artifact_types.py:12-23`); `RecordClass` = plans, specs, research,
    records, prompts, comms, walkthroughs, releases, reviews
    (`agent_workflows/record_producers.py:85-101`).
  - Therefore `record_classes` MUST contain the union of ELEVEN names: plans, specs, research, backlog,
    reviews, releases, prompts, walkthroughs, roadmaps, comms, other. `roadmaps` is NOT optional: it has
    5 artifacts on disk (incl. `.aw/records/roadmaps/`) and working verbs `run_rename_roadmaps` /
    `run_group_roadmaps` (`agent_workflows/artifact_rename.py:827-828,855-856`).
  - `records` CARVE-OUT: `RecordClass.RECORDS` maps to the EMPTY subpath (`record_producers.py:136`),
    i.e. the records root itself, not a child directory. It MUST NOT be modeled as an ordinary record
    class with `subpath: "records"`. Represent it explicitly (a separate constant or an
    `is_root_alias`-style flag) so nothing derives a `records/records/` path.
  - Aliases MUST reproduce `_ALIASES` (`artifact_types.py:26-39`) exactly, including `roadmap` ->
    `roadmaps`, `others`/`misc` -> `other`, and the identity entries.
  - `traversal_exclusions` MUST reproduce `selectors.EXCLUDED_RECORD_DIRS` exactly at this stage
    (`.git`, `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`). Do NOT add
    `node_modules`/`venv`/`.venv` here; that widening is a deliberate behavior change owned by `zvk796`
    E-02 with its own assertion.

### Task group 2: Unit Testing & Schema Conformance

- [ ] E-02 Author unit tests in `tests/test_layout.py` (NEW FILE; it does not exist today) verifying model defaults, JSON serialization determinism, type normalization, alias resolution, and JSON schema validation using `jsonschema` (or stdlib schema checker).
  - Depends on: E-01
  - Expected outcome: `pytest tests/test_layout.py` passes cleanly.
  - Execution state: pending
  - MUST include a vocabulary-parity test asserting the model's `record_classes` is a SUPERSET of both
    `artifact_types.ARTIFACT_TYPES` and `{r.value for r in record_producers.RecordClass}` (excluding the
    `records` root carve-out), so a future edit that silently drops `roadmaps` (or any other live type)
    fails the suite. This is the regression fence for PR-001.
  - MUST assert the model's `traversal_exclusions` equals `selectors.EXCLUDED_RECORD_DIRS` exactly, so
    `zvk796`'s later widening is a visible, deliberate test change rather than a silent drift.

## Project conventions discovered (Step 0)

- Spec `kw5y2s` Section 4 & 5 defines the exact JSON schema and Python dataclass structures.

## Findings

- Creating `layout.py` as a standalone module first introduces zero changes to existing code and allows full unit test validation before refactoring dependent modules.

## Proposed changes (ordered, validatable)

1. Create `agent_workflows/layout.py` (E-01).
2. Create `tests/test_layout.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring existing modules is deferred to Orders 02 & 03.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_layout.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 4 & 5.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `agent_workflows/layout.py` defines `LayoutModel`, `RecordClassDefinition`, `build_default_layout()`, `to_json()`, and `to_schema()`.
  - PLUS the union-vocabulary proof (PR-001), pasted, not asserted. Run and paste the output of a
    differential check that the model reproduces the live vocabulary with NOTHING dropped, e.g.:
    `python3 -c "from agent_workflows import layout, artifact_types as AT, record_producers as RP, selectors as S; m=layout.build_default_layout(); rc=set(m.record_classes); print('missing_from_model:', sorted((set(AT.ARTIFACT_TYPES)|{r.value for r in RP.RecordClass}) - rc - {'records'})); print('roadmaps_present:', 'roadmaps' in rc); print('excl_equal:', tuple(m.traversal_exclusions)==tuple(S.EXCLUDED_RECORD_DIRS))"`
    Required result: `missing_from_model: []`, `roadmaps_present: True`, `excl_equal: True`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `pytest tests/test_layout.py` passes cleanly, with the actual runner output pasted (never a claimed pass).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
