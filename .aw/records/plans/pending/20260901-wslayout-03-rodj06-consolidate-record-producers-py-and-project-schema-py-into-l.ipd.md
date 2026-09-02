# IPD: Consolidate record_producers.py and project_schema.py into layout model

- Date: 2026-09-01
- Kind: child
- Concern: `record_producers.py` and `project_schema.py` maintain separate `RecordClass`, `DurableStateClass`, `RuntimeStateClass`, and subpath maps. Aligning them with `layout.py` removes duplication.
- Scope: Refactor `agent_workflows/record_producers.py` and `agent_workflows/project_schema.py` to source definitions from `agent_workflows/layout.py` while preserving existing exception types, class enums, and legacy migration path adapters.
- Scope-Paths: agent_workflows/record_producers.py, agent_workflows/project_schema.py
- Item-Dependencies: executed:wpu5zu
- Status: to-review
- Set: wslayout
- Order: 3
- Highest E allocated: 02
- Author: antigravity
- Id: rodj06
- From-Spec: kw5y2s

## Workflow history
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-001 (drops root-level `records` class), PR-002 (tests/test_record_producers.py does not exist), PR-006, PR-007.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).

## Goal

Consolidate `record_producers.py` and `project_schema.py` to consume `layout.py` without breaking existing record routing, write guards, or migration retention.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refactor record_producers.py

- [ ] E-01 Update `agent_workflows/record_producers.py` to align `RecordClass`, `DurableStateClass`, `RuntimeStateClass`, and `_RECORD_CLASS_SUBPATHS` with `layout.py` while preserving `_LEGACY_RECORD_CLASS_SUBPATHS` and existing write guard methods.
  - Depends on: none
  - Expected outcome: `record_producers.py` sources subpaths from the layout model.
  - Execution state: pending
  - Set-level prerequisite: `wpu5zu` must be executed first; see `- Item-Dependencies:` in the metadata.
  - THE `records` CARVE-OUT IS MANDATORY (plan-review PR-001). `RecordClass.RECORDS` maps to the EMPTY
    subpath (`agent_workflows/record_producers.py:136`), meaning the records ROOT itself. The draft spec
    omits it entirely. Sourcing `_RECORD_CLASS_SUBPATHS` from the model MUST preserve that empty-string
    mapping exactly; a naive derivation would either drop the member or give it `subpath: "records"`,
    producing a wrong `records/records/` path. Consume the explicit carve-out `wpu5zu` E-01 provides.
  - `backlog` and `other` are in the union model but NOT in today's `RecordClass`. Adding them is
    intended (union ruling), but each new member needs a subpath that matches where those artifacts
    ALREADY live (`.aw/records/backlog/`, `.aw/records/other/`); do not invent new directories.
  - `_LEGACY_RECORD_CLASS_SUBPATHS` (`:148`) and `resolve_record_read_paths` (`:608`, legacy lookup at
    `:631`) MUST keep working for `.agents/` migration reads. Any new member inherits the final subpath
    through the existing `**` spread, which is correct-by-absence; do not hand-add legacy entries for
    net-new classes.

### Task group 2: Refactor project_schema.py

- [ ] E-02 Align `LogicalRoot` and `RootClass` enums and constants in `agent_workflows/project_schema.py` with `layout.py`.
  - Depends on: E-01
  - Expected outcome: `project_schema.py` is in 100% sync with the canonical layout model.
  - Execution state: pending
  - ALSO create `tests/test_record_producers.py` if E-01 did not (plan-review PR-002): the file named by
    V-01 does not exist today, and no other plan in the Set creates it. It must cover the `records`
    empty-subpath carve-out, the preserved legacy read paths, and the write guard.
  - `LogicalRoot` has 4 members and `RootClass` has 6 (`agent_workflows/project_schema.py:45-51,54+`);
    the model's `logical_roots` has 4. Aligning MUST NOT collapse `RootClass` to 4 or drop a member: the
    two enums answer different questions (logical roots vs physical placement classes).

## Project conventions discovered (Step 0)

- `agent_workflows/record_producers.py`: central record routing and write guard.
- `agent_workflows/project_schema.py`: canonical project schema vocabulary.

## Findings

- `_LEGACY_RECORD_CLASS_SUBPATHS` must be retained in `record_producers.py` for legacy `.agents/` migration reads (`resolve_record_read_paths`).

## Proposed changes (ordered, validatable)

1. Refactor `agent_workflows/record_producers.py` (E-01).
2. Refactor `agent_workflows/project_schema.py` (E-02).

## Deferred / out of scope (with reason)

- Install-time emission is in Order 04 (hauwqh).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_record_producers.py tests/test_project_context.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 5.1.

## Open questions

- none.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - CORRECTED (plan-review PR-002): `tests/test_record_producers.py` DOES NOT EXIST at review time, so
    it cannot simply be run. E-01 must CREATE it (see the E-01 note); this V-item verifies the new file.
  - Required evidence: `python3 -m pytest tests/test_record_producers.py` passes cleanly, with the ACTUAL
    runner output pasted, and the file present in the commit.
  - PLUS the `records` carve-out proof (PR-001), pasted:
    `python3 -c "from agent_workflows import record_producers as RP; print(repr(RP._RECORD_CLASS_SUBPATHS.get('records'))); print(sorted(RP._RECORD_CLASS_SUBPATHS))"`
    Required result: `records` still maps to the EMPTY string `''`, and every pre-existing key is still
    present (nothing dropped).
  - PLUS the BARE FULL SUITE (PR-006), because "100% backward compatibility" cannot be proven by narrow
    files: run `python3 -m pytest` (bare) and paste the `N passed` summary line, zero regressions.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest tests/test_project_context.py` passes cleanly, with the ACTUAL runner output pasted (file verified to exist at review time).
  - PLUS proof that `LogicalRoot` and `RootClass` still expose every pre-existing member with unchanged
    values, pasted:
    `python3 -c "from agent_workflows.project_schema import LogicalRoot, RootClass; print([m.value for m in LogicalRoot]); print([m.value for m in RootClass])"`
    Required result: `LogicalRoot` still has exactly system/config/state/records, and `RootClass` still
    has all six members.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
