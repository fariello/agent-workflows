# Review findings: plan 52rpc1

- Subject-Id: 52rpc1
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `b302210d7` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-183-52rpc1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-2.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests for all 8 target test modules passed: `python3 -m pytest tests/test_specs_evidence_gate_parity.py tests/test_specs_from_backlog.py tests/test_specs_metadata_duplicate_bullet.py tests/test_specs_recursive_read.py tests/test_specs_releases_descriptive_safety.py tests/test_specs_releases_unsafe_field.py tests/test_specs_set_adapter.py tests/test_specs_set_gate_parity.py` printed `78 passed in 3.46s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: complex` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-005 | MD-15, Section 7.2 |
| `E-01` & batch rule step 1 | Assumed `.aw/state/59aiyh/` exists before saving batch files | Added explicit `mkdir -p .aw/state/59aiyh/` and baseline capture instruction into E-01 and batch rule step 1 | PR-003 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated to `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite builder/codemod symbols are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Converts test data across 8 test modules to use the shared record builder `tests/record_builder.py::RecordBuilder` via fixture codemod `tools/fixture_codemod.py` in preparation for phase B cutover (`cxxmyv`, `4sd62s` section 6).
2. No. Standalone test fixture conversion; touches test files only.
3. Yes. Touches 8 test modules across specs and spec-releases; sized at 3 E-items (2 conversion batches and 1 finish).
4. Yes. `- Scope-Paths:` explicitly lists all 8 test module paths plus the plan itself.
5. Yes. If test fixtures are converted incorrectly or test outcomes drift, specs lifecycle gates or validation rules could silently lose coverage or falsely pass/fail.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and section 7 step 6); parent plan `7qxey9` (Order 38); orchestrator `63ib9r` (row 183); predecessor builder `9rgn2w` and codemod `653ndz`; and the 8 test modules in `tests/`.
- Verified that all cited test modules exist and F-40 line counts match the Concern statement (29 in test_specs_evidence_gate_parity, 44 in test_specs_from_backlog, 33 in test_specs_metadata_duplicate_bullet, 8 in test_specs_recursive_read, 15 in test_specs_releases_descriptive_safety, 11 in test_specs_releases_unsafe_field, 11 in test_specs_set_adapter, 18 in test_specs_set_gate_parity; total 169 legacy lines).

### Step R2

- Checked: 1:1 bijection between E-01..E-03 and V-01..V-03; `- Scope-Paths:` completeness; `- Item-Dependencies:` resolution (`executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45`); and verification reachability.
- Verified that V-01..V-03 demand verifiable evidence (empty diffs between before/after outcome lists, codemod reports, hand-conversion count <= 25, helper censuses, union diff, and git show stat).

### Step R3

- Checked: Security and privacy lens. Test fixture conversion to shared builder does not touch trust boundaries, secrets, or sandboxes. Verified refusal count threshold guard (<= 25) prevents unvetted hand edits.

### Step R4

- Checked: Engineering rubric. Reuses canonical `RecordBuilder` patterns, supports `raw_fields=` for deliberate invalid-input tests, ensures zero regression via diff check on test outcome lists, and avoids code-pinning assertions.

### Step R5

- Checked: Eight personas evaluated. Automated test suites maintain verification capability; power users and developers retain identical CLI/test behavior.

### Step R6

- Checked: Right-sizing at 3 E-items (2 conversion batches with 4 modules each, 1 finish item) across 8 test Scope-Paths. Cleanly decoupled split from `7qxey9`. No further decomposition needed.

### Step R7

- Checked: Cross-plan consistency with orchestrator `63ib9r` row 183, parent `7qxey9`, sibling chunks 1 and 3 through 10, and downstream cutover `cxxmyv`.

### Step S5

- Checked: Pre-existing open questions and findings. OQ-01 was resolved; owner updated from `none` to `plan author`. Zero open questions remain. No human decisions required.

### Pass 2

- Verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- Verified all 5 findings (PR-001..PR-005) fixed in place.
- Verified structural preservation: headings, E/V ids, and execution states preserved.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261109-metastore-183-52rpc1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-2.ipd.md:173-185; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), omitted the scope fence declaration clarification, and lacked a narrow safety stop if prerequisite builder/codemod symbols from `9rgn2w` or `653ndz` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), scope fence declaration clarification, and narrow safety stop if prerequisite builder/codemod symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261109-metastore-183-52rpc1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-2.ipd.md:96-99; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the batch conversion of test data and final verification (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261109-metastore-183-52rpc1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-2.ipd.md:35, 46 | The checklist preamble instructed saving the batch file list to `.aw/state/59aiyh/<batch>-files.txt` before editing, but the directory `.aw/state/59aiyh/` does not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-01 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/59aiyh/` and baseline capture instruction into E-01 and batch rule step 1 (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261109-metastore-183-52rpc1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-2.ipd.md:131-137 | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-183-52rpc1-move-spec-plan-lifecycle-and-orchestration-test-data-chunk-2.ipd.md:8-10 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can Chunk 2 execute in any order relative to other chunk plans? | Yes. Module sets are disjoint, each chunk depends on builder and codemod, and none edits `tests/support.py` (which runs in `59aiyh` E-09). | Impose strict serial ordering across all chunk plans (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | How are private test helpers handled in target modules? | None were identified at split or review in this chunk's modules; if any uncalled helper is discovered at conversion time, delete it, or list surviving helper with justification. | Keep dead helper functions (rejected: leaves redundant untested code paths); delete without caller check (rejected: risk of breaking unmigrated tests). | `52rpc1` E-01, E-02, F-40 | yes |
| D-3 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `52rpc1` Batch rule step 4, research `nj8zdp` | yes |
| D-4 | How should test fixtures with deliberately invalid values be constructed? | Use `RecordBuilder` with `raw_fields=` to inject invalid metadata bullets while maintaining structured generation. | Use raw markdown string literals or heredocs (rejected: bypasses builder pattern established for phase B). | `52rpc1` Batch rule step 4, spec `4sd62s` section 6 | yes |
| D-5 | How is `.aw/state/59aiyh/` initialized across lane worktrees? | Create `.aw/state/59aiyh/` via `mkdir -p .aw/state/59aiyh/` at step 1 before recording test outcome lists in each lane worktree. | Rely on preexisting state directory (fails in isolated git worktrees where `.aw/state/` is gitignored and not shared). | `52rpc1` Batch rule step 1, isolated lane environment | yes |
