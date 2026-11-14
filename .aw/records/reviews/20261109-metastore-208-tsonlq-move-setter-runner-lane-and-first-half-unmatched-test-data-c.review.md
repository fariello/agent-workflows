# Review findings: plan tsonlq

- Subject-Id: tsonlq
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `e0b732062` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_executed_transition_gate.py tests/test_ipd_dependency_statement_gate.py` printed `29 passed in 1.14s`, and all 7 target test modules passed: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_authoring_coverage_guidance.py tests/test_awcmdsurf_mutation_verbs.py tests/test_awmigrename.py tests/test_awphysical_tools.py tests/test_collision_population_parity.py tests/test_companion_record_owner_root.py tests/test_completion.py` printed `105 passed in 80.89s (0:01:20)`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

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

1. Yes. Converts test data across 7 test modules to use the shared record builder `tests/record_builder.py::RecordBuilder` via fixture codemod `tools/fixture_codemod.py` in preparation for phase B cutover (`cxxmyv`, `4sd62s` section 6).
2. No. Standalone test fixture conversion; touches test files only.
3. Yes. Touches 7 test modules across setter, runner-lane, and unmatched tests; sized at 3 E-items (2 conversion batches and 1 finish).
4. Yes. `- Scope-Paths:` explicitly lists all 7 test module paths plus the plan itself.
5. Yes. If test fixtures are converted incorrectly or test outcomes drift, command surface, mutation verbs, or completion tests could silently lose coverage or falsely pass/fail.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and section 7 step 6); parent plan `1upea0` (Order 41); orchestrator `63ib9r` (row 208); predecessor builder `9rgn2w` and codemod `653ndz`; and the 7 test modules in `tests/`.
- Verified that all cited test modules exist and F-40 line counts match the Concern statement (2 in test_authoring_coverage_guidance, 3 in test_awcmdsurf_mutation_verbs, 2 in test_awmigrename, 1 in test_awphysical_tools, 2 in test_collision_population_parity, 7 in test_companion_record_owner_root, 7 in test_completion; total 24 legacy lines).

### Step R2

- Checked: 1:1 bijection between E-01..E-03 and V-01..V-03; `- Scope-Paths:` completeness; `- Item-Dependencies:` resolution (`executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45`); and verification reachability.
- Verified that V-01..V-03 demand verifiable evidence (empty diffs between before/after outcome lists, codemod reports, hand-conversion count <= 25, helper censuses, union diff, and git show stat).

### Step R3

- Checked: Security and privacy lens. Test fixture conversion to shared builder does not touch trust boundaries, secrets, or sandboxes. Verified refusal count threshold (at most 25 hand conversions before stop) and invalid-input testing via `raw_fields=`.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Sized cleanly (3 items, 2 task groups, 7 work paths). Batch rule ensures strict preservation of test coverage and behavior across all converted test modules.

### Step R5

- Checked: QA/QC (deterministic outcome list diffs before and after), Architect (shared record builder decoupling test data from storage layout changes in phase B), Testing/Regression (identical per-test outcomes, raw_fields for invalid metadata values), and Software Engineer (clean batch rules with bounded hand conversions).

### Step R6

- Checked: Decomposition and right-sizing. Plan is already a right-sized child chunk (chunk 6 of 7) split from `1upea0` following research `nj8zdp` guidance. It contains 3 E-items, 2 task groups, and 7 work Scope-Paths (well within the <= 5 E-items / <= 8 work paths limit). No further split needed.

### Step R7

- Checked: Cross-plan consistency within Set `metastore`. Aligns with orchestrator `63ib9r` row 208, parent `1upea0`, sibling chunks 1 through 5 and 7, and downstream cutover `cxxmyv`.

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
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:167-179; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), omitted the scope fence declaration clarification, and lacked a narrow safety stop if prerequisite builder/codemod symbols from `9rgn2w` or `653ndz` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), scope fence declaration clarification, and narrow safety stop if prerequisite builder/codemod symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:98-101; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the batch conversion of test data and final verification (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:35-39 | The checklist preamble instructed saving the batch file list to `.aw/state/59aiyh/<batch>-files.txt` before editing, but the directory `.aw/state/59aiyh/` does not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-01 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/59aiyh/` and baseline capture instruction into E-01 and batch rule step 1 (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:141-147 | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md:8-10 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can Chunk 6 execute in any order relative to other chunk plans? | Yes. Module sets are disjoint, each chunk depends on builder and codemod, and none edits `tests/support.py` (which runs in `59aiyh` E-09). | Impose strict serial ordering across all chunk plans (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | How are private test helpers handled in target modules? | None were identified at split or review in this chunk's modules; if any uncalled helper is discovered at conversion time, delete it, or list surviving helper with justification. | Keep dead helper functions (rejected: leaves redundant untested code paths); delete without caller check (rejected: risk of breaking unmigrated tests). | `tsonlq` E-01, E-02 | yes |
| D-3 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `tsonlq` Batch rule step 4, research `nj8zdp` | yes |
| D-4 | How should test fixtures with deliberately invalid values be constructed? | Use `RecordBuilder` with `raw_fields=` to inject invalid metadata bullets while maintaining structured generation. | Use raw markdown string literals or heredocs (rejected: bypasses builder pattern established for phase B). | `tsonlq` Batch rule step 4, spec `4sd62s` section 6 | yes |
| D-5 | How is `.aw/state/59aiyh/` initialized across lane worktrees? | Create `.aw/state/59aiyh/` via `mkdir -p .aw/state/59aiyh` at step 1 before recording test outcome lists in each lane worktree. | Rely on preexisting state directory (fails in isolated git worktrees where `.aw/state/` is gitignored and not shared). | `tsonlq` Batch rule step 1, isolated lane environment | yes |
