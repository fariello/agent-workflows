# IPD: Consolidate record_producers.py and project_schema.py into layout model

- Date: 2026-09-01
- Kind: child
- Concern: `record_producers.py` and `project_schema.py` maintain separate `RecordClass`, `DurableStateClass`, `RuntimeStateClass`, and subpath maps. Aligning them with `layout.py` removes duplication.
- Scope: Refactor `agent_workflows/record_producers.py` and `agent_workflows/project_schema.py` to source definitions from `agent_workflows/layout.py` while preserving existing exception types, class enums, and legacy migration path adapters. Author unit tests in `tests/test_record_producers.py`.
- Scope-Paths: agent_workflows/record_producers.py, agent_workflows/project_schema.py, tests/test_record_producers.py
- Item-Dependencies: executed:wpu5zu
- Status: to-review
- Readiness: no-go
- Set: wslayout
- Order: 3
- Highest E allocated: 02
- Author: antigravity
- Id: rodj06
- From-Spec: kw5y2s

## Workflow history
- 2026-09-04 to-review (aw set): Applied deterministic plan-review repairs; controlling spec kw5y2s awaits renewed human approval.

- 2026-09-04 reviewed (antigravity): /aw plan-review-long: APPROVE WITH REVISIONS APPLIED; PR-019, PR-020, PR-022, PR-023 fixed (added test file to Scope-Paths, added ten-clause execution contract, structured findings evidence table, conventions, bare-suite validation with baseline re-measurement, and readiness).
- 2026-09-01 draft (antigravity): created child plan.
- 2026-09-01 to-review (antigravity): authored complete plan.
- 2026-09-01 /plan-review (opencode/its_direct/pt3-claude-opus-5-1m-us): REJECT - NEEDS REPLAN (Set-level); see orchestrator rh5tt6 OQ-1/OQ-2 and review record 20260901-wslayout-00-rh5tt6-...review.md
  - PR-001 (drops root-level `records` class), PR-002 (tests/test_record_producers.py does not exist), PR-006, PR-007.
- 2026-09-01 /plan-review revisions applied (opencode/its_direct/pt3-claude-opus-5-1m-us): verdict revised REJECT -> APPROVE WITH REVISIONS APPLIED after the maintainer challenged the REPLAN call; all findings FIXED in place (no rewrite needed). review-finalize lint conforming; bare suite 4004 passed. Execution still gated on maintainer approval of spec kw5y2s (ipd-lifecycle.md:16).
- 2026-09-01 to-review (aw set): plan-review PR-007: metadata now matches the orchestrator sequence table

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

- `agent_workflows/record_producers.py`: central record routing and write guard. Defines `RecordClass` (9 members + `records` root-level carve-out), `DurableStateClass` (5 members), `RuntimeStateClass` (6 members), `_RECORD_CLASS_SUBPATHS`, and `_LEGACY_RECORD_CLASS_SUBPATHS`.
- `agent_workflows/project_schema.py`: canonical project schema vocabulary. `LogicalRoot` (4 members: system, config, state, records) and `RootClass` (6 members: system, config_project, config_local, state_durable, state_runtime, records).
- Controlling spec `kw5y2s` is `to-review` after its maintainer-directed API terminology correction; do not execute until renewed human approval restores the gate. Its rule against collapsing `RootClass` (6) into `LogicalRoot` (4) remains unchanged.
- `_RECORD_CLASS_SUBPATHS['records'] == ""` is the mandatory empty-subpath carve-out for the records root itself; naive mapping would produce invalid `records/records/` paths.
- `_LEGACY_RECORD_CLASS_SUBPATHS` preserves `docs/specs`, `docs/research`, and `docs/walkthroughs` overrides for legacy `.agents/` migration reads.
- Python 3.9 is the floor (`pyproject.toml:12`).

## Findings

| Id | Finding | Evidence |
| --- | --- | --- |
| F-1 | **Consolidating `record_producers.py` and `project_schema.py` onto `layout.py` establishes a single source of truth for record and state classes.** Preserves exact backward compatibility. | `agent_workflows/record_producers.py:85-160`; `agent_workflows/project_schema.py:45-65`. |
| F-2 | **The `records` empty-subpath carve-out is mandatory.** `RecordClass.RECORDS` maps to `""` representing the root records directory itself (`_RECORD_CLASS_SUBPATHS['records'] == ''`). | `record_producers.py:136`; spec Section 3.2.1. |
| F-3 | **Legacy `.agents/` migration paths must be preserved.** `_LEGACY_RECORD_CLASS_SUBPATHS` maintains legacy `docs/` paths (`docs/specs`, `docs/research`, `docs/walkthroughs`) for `resolve_record_read_paths`. | `record_producers.py:148-154,608-631`. |
| F-4 | **`LogicalRoot` (4) and `RootClass` (6) answer distinct questions and must not be collapsed.** Spec Section 5.1 item 4 explicitly forbids collapsing physical placement classes to logical roots. | `project_schema.py:45-64`; spec Section 5.1 item 4. |
| F-5 | **`tests/test_record_producers.py` is newly created by this plan.** Covers the empty-subpath carve-out, preserved legacy read paths, and write guards. Scope-Paths updated to include it (PR-020). | V-01 / E-02 notes; file verified absent before execution. |

## Proposed changes (ordered, validatable)

1. Refactor `agent_workflows/record_producers.py` and create unit tests (E-01).
2. Refactor `agent_workflows/project_schema.py` and finalize `tests/test_record_producers.py` (E-02).

## Deferred / out of scope (with reason)

- Install-time emission is in Order 04 (hauwqh).

## Scope check

- Over-scope: none.
- Under-scope: none. `tests/test_record_producers.py` is newly created by this plan and is included in `Scope-Paths` (PR-020).

## Required tests / validation

- `python3 -m pytest tests/test_record_producers.py tests/test_project_context.py` passing, with actual output pasted.
- Bare full repository suite `python3 -m pytest` from the PRIMARY checkout, with baseline re-measured on unmodified HEAD at execution time.
- `aw check --agent` showing no new diagnostic class (expecting the six `tk1gqo` reports).
- `aw sanitize --agent` passing clean.

## Spec / documentation sync

- Implements Spec `kw5y2s` Section 5.1. Spec is `approved`; do NOT edit it.
- No user-facing documentation changes owned by this internal refactor.

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

THE EXTERNAL SPEC GATE IS REOPENED: controlling spec `kw5y2s` is `to-review` after the maintainer-directed API terminology correction. `ipd-lifecycle.md:16` blocks execution until renewed human approval is recorded.

Execution contract:

1. Human approval of this plan is required before execution. There are no unresolved blocking questions.
2. Serial prerequisite: `wpu5zu` (Order 01) MUST reach `executed` before starting this plan, as this plan imports `agent_workflows/layout.py`.
3. Carve-out invariant: `RecordClass.RECORDS` MUST map to the empty string `""` in `_RECORD_CLASS_SUBPATHS` (PR-001).
4. Legacy preservation: `_LEGACY_RECORD_CLASS_SUBPATHS` MUST retain the `docs/`-prefixed subpaths for `specs`, `research`, and `walkthroughs`.
5. Class separation: Aligning with `layout.py` MUST NOT collapse `RootClass` (6 members) to `LogicalRoot` (4 members).
6. Create new tests: `tests/test_record_producers.py` must be authored and committed with this plan.
7. Validation requires ACTUAL pasted runner output; never claim a pass without running the commands.
8. Shared checkout discipline: commit only files this plan changed, path-scoped. Verify the staged set with `git diff --cached --name-only` and unstage anything not yours with `git restore --staged`. Never `git add -A`, bare `git add`, `git commit -a`, `--no-verify`, or push.
9. Validate in the PRIMARY checkout, never a scratch worktree (`dh0uno`).
10. Scope fence: declared paths are `agent_workflows/record_producers.py`, `agent_workflows/project_schema.py`, and `tests/test_record_producers.py`. An out-of-scope edit requires `--scope-reason`, and an unmodified declared path requires `--scope-ack`. Do NOT stop over a scope question. DO stop and report if a concurrent-edit conflict cannot be safely combined.
11. Expect the `check.lifecycle-transition-invalid` diagnostic; it is a known tooling defect (backlog `tk1gqo`) and must not be "fixed" by reordering the history.
12. On completion, run `aw ipd lint --phase pre-transition`, then `aw ipd finalize <plan> --actor <AGENT/MODEL> --message <SUMMARY> --apply`, and move the plan to `.aw/records/plans/executed/` with `- Status: executed`. The lifecycle transition is a POST-gate step, never an E-item.
