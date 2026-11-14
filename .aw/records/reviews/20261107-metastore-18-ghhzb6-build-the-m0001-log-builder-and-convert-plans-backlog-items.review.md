# Review findings: plan ghhzb6

- Subject-Id: ghhzb6
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `8f28f04fe` in an isolated runner review-sweep lane worktree. Working tree was clean at turn start (`pre-review snapshot: skipped unchanged`). Pass 1 and Pass 2 verified the plan against governing spec `4sd62s` (5.2 step 4, 4.2a, AC-19, AC-32, AC-40), orchestrator `63ib9r` (row 18), origin plan `dcerjg` (Order 04, E-09/E-10/E-14 subset), prerequisite plans `tve77h` (Order 02), `vxevph` (Order 15), and `dky26u` (Order 17), and companion split plan `hpedmn` (Order 19).

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Line 20, front matter | Scaffold blockquote instruction; missing `Review-Depth:` and `Readiness:` | Removed scaffold line; added `- Review-Depth: complex` and `- Readiness: go-pending-approval` | PR-001. |
| Line 121, validation rule | Two unicode em dashes in validation-state rule header | Replaced with plain ASCII spaced hyphens to eliminate IPD-C802 warnings | PR-002. |
| `Proposed changes` | Numbered list without diagram | Added Requirement 12 `flowchart TD` Mermaid diagram | PR-003. |
| `Approval and execution gate` | Scope fence without standard stop condition | Added explicit stop-and-report clause for unexpected failures or unresolvable conflicts | PR-004. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. The plan builds `agent_workflows/migrations/m0001_convert.py` which defines the migration event sequence (seq 0 checkpoint, rename, legacy events), compact front matter rewrite, and explicit destinations for 30 legacy metadata fields across plans, backlog items, releases, specs, and staged prompts. Companion plan `hpedmn` and roundtrip plan `dcerjg` rely on these converters.
2. No. It changes no authorization gate, permission check, policy predicate, sandbox boundary, or lock protocol.
3. No. It has 3 `E-*` items in 2 task groups.
4. No. It declares 3 work Scope-Paths (`agent_workflows/migrations/m0001_convert.py`, `agent_workflows/migrations/m0001_metadata_v2.py`, `tests/test_m0001_conversion.py`) and the plan itself.
5. No. Conversion execution in this plan runs strictly against `tmp_path` fixture repositories; the safety clause forbids applying migration to repository records.

AW-TIER: complex

### Step R1

- Checked: Prerequisite `tve77h` (Order 02) is executed, providing the core event registry, append keys, and in-file mirror writer. Prerequisite `vxevph` (Order 15) defines the migration chain, schema stamp, and preflight. Prerequisite `dky26u` (Order 17) defines the legacy rename map.
- Checked: All 3 dependencies in `- Item-Dependencies:` (`tve77h`, `vxevph`, `dky26u`) resolve in `.aw/records/plans/` and match orchestrator `63ib9r` row 18.
- Checked: Spec `4sd62s` 5.2 step 4, 4.2a, and AC criteria (AC-19, AC-32, AC-40) are verified in `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md`.
- Checked: Companion plan `hpedmn` (Order 19) and roundtrip plan `dcerjg` (Order 04) resolve in `.aw/records/plans/pending/` and match their split roles.

### Step R2

- Checked: E/V bijection is 3/3 (`E-01..E-03` to `V-01..V-03`), and `- Highest E allocated: 03` matches.
- Reachability: `V-01` verifies event layout (seq 0..3), field mapping destinations, and `Scope-Exceeded` parsing on `tmp_path` fixtures; `V-02` verifies `---`/`id`/`status`/`---` mirror, prompt comment formatting, and byte-identical exclusions; `V-03` verifies test outcomes and durations under `python3 -m pytest tests/test_m0001_conversion.py`.

### Step R3

- Checked: Migration code executes strictly against `tmp_path` fixture repositories in tests. The gate contains an explicit safety clause: "this plan NEVER runs `aw migrate metadata --apply` (or bare `aw migrate --apply`) in this checkout... If an apply would touch this checkout's records, stop and report".
- Checked: Descriptive text safety uses `attention_contract.refuse_unsafe_descriptive` with length boundaries (SR-903).

### Step R4

- A (State & atomicity): Transactional migration reuses `layout_migration.MigrationManager` (`_acquire_lock`, `_save_transaction`, `_load_transaction`).
- C (Architecture): No new lock or journal components are introduced (spec 5.1). Mirror writer is shared with `artifact_meta`.
- D & E (Regression & test safety): All tests run against isolated `tmp_path` git repositories created with real `git init`. Unmigrated comms, `.data/`, READMEs, and templates are explicitly verified byte-identical.
- Spec sync: Implements `4sd62s` Section 5.2 step 4 and Section 4.2a for the 5 core record types without changing live repository records.

### Step R5

- Checked through review personas:
  - Architect: Modular division between core types (`m0001_convert.py`) and secondary types (`hpedmn`) avoids monolithic migration logic while preserving exact field mappings.
  - QA / Regression: Comprehensive unit tests on `tmp_path` fixtures exercise layout, path history, field destinations, and AC cases.
  - Operator: Explicit refusal and safety gate prevent accidental in-place migration of live repository files during test runs.

### Step R6

- Checked: Right-sizing is appropriate (3 E-items, 2 task groups, 3 work Scope-Paths). Splitting the 99-key migration across `ghhzb6` and `hpedmn` per maintainer step-complexity rule was sound. No further decomposition is needed.

### Step R7

- Checked: `ghhzb6` integrates cleanly with predecessors `tve77h`, `vxevph`, `dky26u`, companion `hpedmn`, and orchestrator `63ib9r`.
- Dependencies in `63ib9r` row 18 match `- Item-Dependencies:` exactly.

### Step S5

- Checked: OQ-04 and OQ-05 are resolved and non-blocking, carried from `dcerjg`. All 4 findings (`PR-001..PR-004`) are technical and procedural refinements resolved directly from repository evidence and standards. No human decision is required (`questions: []`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | LOW | IN-SCOPE | Proofreading / P-Proofread | `ghhzb6.ipd.md:20` (`> Write and proofread this plan...`); lines 1-19 | Unremoved authoring template prompt blockquote and missing front-matter metadata (`- Review-Depth: complex`, `- Readiness: go-pending-approval`). | Low | FIXED | Removed template line, added `- Review-Depth: complex` and `- Readiness: go-pending-approval`. |
| PR-002 | LOW | IN-SCOPE | Technical Writing / IPD-C802 | `ghhzb6.ipd.md:121` | Two unicode em dashes in validation-state rule header emitted IPD-C802 warnings. | Low | FIXED | Replaced em dashes with plain ASCII spaced hyphens. |
| PR-003 | LOW | IN-SCOPE | Technical Writing Requirement 12 | `ghhzb6.ipd.md:73-77` (`Proposed changes`) | Proposed changes lacked a Mermaid diagram illustrating the execution sequence. | Low | FIXED | Added a `flowchart TD` Mermaid diagram showing `E01 -> E02 -> E03`. |
| PR-004 | LOW | IN-SCOPE | S7 Contract / Safety | `ghhzb6.ipd.md:141-146` (`Approval and execution gate`) | Approval gate lacked an explicit stop-and-report clause for unexpected test failures or unresolvable concurrent-edit conflicts. | Low | FIXED | Added standard stop-and-report safety clause to the approval gate. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-001 | How should the unicode em dashes in line 121 be resolved? | Replace with plain ASCII spaced hyphens (` - `) | Leave as unicode em dashes or rephrase with commas | Conforms to `IPD-C802` rule in `agent_workflows/ipd_lint.py` and repository dash rule in `AGENTS.md` | yes |
| D-002 | What review depth tier should be assigned to `ghhzb6`? | Assign `complex` tier | Assign `standard` tier | `ghhzb6` establishes the core data migration transformations, event model builders, and 30 field mappings for 5 record types under `4sd62s` 5.2 step 4, mirroring precursor migration plan `vxevph` | yes |
