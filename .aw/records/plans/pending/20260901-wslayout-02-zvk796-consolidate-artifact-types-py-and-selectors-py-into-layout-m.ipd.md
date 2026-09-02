# IPD: Consolidate artifact_types.py and selectors.py into layout model

- Date: 2026-09-01
- Kind: child
- Concern: `artifact_types.py` and `selectors.py` maintain separate hardcoded sets of artifact types, aliases, and excluded directories. Sourcing them from `layout.py` removes duplication while maintaining exact backward compatibility.
- Scope: Refactor `agent_workflows/artifact_types.py` and `agent_workflows/selectors.py` to import constants and helper logic from `agent_workflows/layout.py`.
- Scope-Paths: agent_workflows/artifact_types.py, agent_workflows/selectors.py
- Item-Dependencies: executed:wpu5zu
- Status: to-review
- Set: wslayout
- Order: 2
- Highest E allocated: 02
- Author: antigravity
- Id: zvk796
- From-Spec: kw5y2s

## Workflow history

- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-001 (would delete shipped `roadmaps` noun), PR-005 (silently widens EXCLUDED_RECORD_DIRS), PR-006 (no bare-suite V-item), PR-007 (Item-Dependencies: none contradicts orchestrator).
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

## Goal

Consolidate `artifact_types.py` and `selectors.py` to consume the single source of truth in `layout.py` without breaking any existing imports or tests.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an E-* item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Refactor artifact_types.py

- [ ] E-01 Update `agent_workflows/artifact_types.py` to derive `ARTIFACT_TYPES`, `_ALIASES`, `is_type_token()`, and `normalize_type()` directly from `agent_workflows/layout.py`, preserving all function signatures and exception types.
  - Depends on: none
  - Expected outcome: `artifact_types.py` re-exports the layout model definitions seamlessly.
  - Execution state: pending
  - Set-level prerequisite: `wpu5zu` must be executed first; see `- Item-Dependencies:` in the metadata.
  - NON-NEGOTIABLE (plan-review PR-001, maintainer ruling 2026-09-01): `roadmaps` MUST survive in
    `ARTIFACT_TYPES`, and `roadmap` MUST survive in `_ALIASES`. The draft spec's table omits them; the
    ruling is UNION, so derivation MUST NOT narrow this tuple. Deleting `roadmaps` would break
    `run_rename_roadmaps` / `run_group_roadmaps`
    (`agent_workflows/artifact_rename.py:827-828,855-856`) and orphan 5 on-disk artifacts.
  - `reviews` becomes an ACCEPTED type token by this derivation (it is in the layout model but not in
    today's `ARTIFACT_TYPES`), which is net-new behavior: `aw check reviews` currently fails with
    "unknown artifact type 'reviews'". That is intended per the union ruling and MUST be covered by
    V-01, not left as an accident.

### Task group 2: Refactor selectors.py

- [ ] E-02 Update `agent_workflows/selectors.py` to source `KNOWN_PRIMARY_TYPES` and `EXCLUDED_RECORD_DIRS` from `agent_workflows/layout.py`.
  - Depends on: E-01
  - Expected outcome: `selectors.py` uses the canonical layout exclusions and types.
  - Execution state: pending
  - TRAVERSAL EXCLUSIONS ARE A BEHAVIOR DECISION, NOT A PURE MOVE (plan-review PR-005). Today
    `EXCLUDED_RECORD_DIRS` = `.git`, `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`
    (7 entries). The draft spec additionally lists `node_modules`, `venv`, `.venv` (`kw5y2s:88-90`).
    `wpu5zu` deliberately pins the model to the CURRENT 7 so this consolidation is behavior-preserving.
  - Therefore: EITHER keep the 7 exactly (default; V-02 asserts equality), OR widen to 10 as an
    EXPLICIT, stated change and update the `wpu5zu` parity test in the same commit. Do NOT let the set
    change as a side effect of "sourcing from the model". Whichever is chosen, V-02 must paste the
    resulting set.

## Project conventions discovered (Step 0)

- `agent_workflows/artifact_types.py`: closed TYPE-noun vocabulary.
- `agent_workflows/selectors.py`: shared selector resolver.

## Findings

- `artifact_types.py` is imported across the CLI and test suite; re-exporting ensures zero downstream breakage.

## Proposed changes (ordered, validatable)

1. Refactor `agent_workflows/artifact_types.py` (E-01).
2. Refactor `agent_workflows/selectors.py` (E-02).

## Deferred / out of scope (with reason)

- Refactoring `record_producers.py` and `project_schema.py` is in Order 03 (rodj06).

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

- `pytest tests/test_awcmdsurf_vocab_and_parsers.py tests/test_selector_resolver_matrix.py` passing.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 5.1.

## Open questions

### OQ-01: Keep the seven current traversal exclusions, or widen to ten?

- Blocking: no
- Status: open
- Owner: executor of this Order, recorded in E-02 before implementing
- Finding: PR-005
- Resolution or deferral rationale: DELIBERATELY LEFT OPEN with a SAFE DEFAULT, so the decision is made
  once and visibly rather than as a side effect. Non-blocking because the default (keep seven) is
  behavior-preserving and needs no permission; only the widening is a change.
  THE FACTS: `selectors.EXCLUDED_RECORD_DIRS` currently holds SEVEN entries (`.git`,
  `.system_generated`, `__pycache__`, `runs`, `scratch`, `temp`, `tmp`). An earlier draft of spec
  `kw5y2s` additionally listed `node_modules`, `venv`, and `.venv`; those are NOT in the code, and the
  spec's Section 3.4 has been corrected to the real seven. `wpu5zu` pins the model to those seven so
  this consolidation is provably behavior-preserving.
  THE CHOICE: EITHER keep the seven exactly (DEFAULT; V-02 asserts equality and nothing else is needed),
  OR widen to ten as an EXPLICIT change, which additionally requires updating the `wpu5zu` parity test
  in the SAME commit and stating the reason here. Widening is plausibly desirable (a vendored
  `node_modules` under a records tree would be skipped), but it changes what record resolution walks, so
  it must not happen merely because the model became the source.
  REQUIRED: V-02 pastes the resulting set, and a set that changed WITHOUT a stated decision is a FAILED
  validation, not a pass.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a V-* item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: `python3 -m pytest tests/test_awcmdsurf_vocab_and_parsers.py` passes cleanly, with the ACTUAL runner output pasted (file verified to exist at review time).
  - PLUS the no-narrowing proof (PR-001), pasted:
    `python3 -c "from agent_workflows import artifact_types as AT; print(sorted(AT.ARTIFACT_TYPES)); print('roadmaps:', 'roadmaps' in AT.ARTIFACT_TYPES, '| roadmap alias:', AT.normalize_type('roadmap'))"`
    Required result: the printed tuple still contains all 10 pre-existing types INCLUDING `roadmaps`,
    and `normalize_type('roadmap')` returns `roadmaps`.
  - PLUS the intended net-new surface: `aw check reviews` no longer errors with "unknown artifact type",
    output pasted.
  - PLUS the BARE FULL SUITE (PR-006), because "100% backward compatibility" cannot be proven by two
    narrow files: run `python3 -m pytest` (bare; addopts already supply `-q -n auto --dist=worksteal -m 'not slow'`)
    and paste the `N passed` summary line, with zero regressions against the pre-change baseline.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: `python3 -m pytest tests/test_selector_resolver_matrix.py` passes cleanly, with the ACTUAL runner output pasted (file verified to exist at review time).
  - PLUS the exact exclusion set (PR-005), pasted:
    `python3 -c "from agent_workflows import selectors as S; print(tuple(S.EXCLUDED_RECORD_DIRS))"`
    Required result: either the unchanged 7-entry set, or the deliberately widened 10-entry set WITH the
    `wpu5zu` parity test updated in the same commit. A set that changed without a stated decision is a
    FAILED validation, not a pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required
