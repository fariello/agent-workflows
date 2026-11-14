# Review findings: plan vaqtii

- Subject-Id: vaqtii
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `127f19377` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-210-vaqtii-move-second-half-unmatched-test-data-chunk-1-of-3-onto-the-r.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_executed_transition_gate.py tests/test_ipd_dependency_statement_gate.py` printed `29 passed in 0.99s`, and all 8 target test modules passed: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_legacy_finalize.py tests/test_limit_reach_check_search.py tests/test_live_conformance_sweep.py tests/test_migrate_layout_cli.py tests/test_mutation_result_facts.py tests/test_notify_cli.py tests/test_notify_core.py tests/test_notify_groups.py` printed `224 passed, 8 warnings in 95.45s (0:01:35)`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

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
3. Yes. Touches 8 test modules across second-half unmatched test data (subset G7b); sized at 3 E-items (2 conversion batches and 1 finish).
4. Yes. `- Scope-Paths:` explicitly lists all 8 test module paths plus the plan itself.
5. Yes. If test fixtures are converted incorrectly or test outcomes drift, legacy finalize, limit reach check, live conformance sweep, migrate layout CLI, mutation facts, or notify tests could silently lose coverage or falsely pass/fail.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and section 7 step 6); parent plan `59aiyh` (Order 47); orchestrator `63ib9r` (row 210); predecessor builder `9rgn2w` and codemod `653ndz`; and the 8 test modules in `tests/`.
- Verified that all cited test modules exist and F-40 line counts match the Concern statement (26 in test_legacy_finalize, 5 in test_limit_reach_check_search, 1 in test_live_conformance_sweep, 6 in test_migrate_layout_cli, 7 in test_mutation_result_facts, 1 in test_notify_cli, 1 in test_notify_core, 1 in test_notify_groups; total 48 legacy lines).

### Step R2

- Checked: 1:1 bijection between E-01..E-03 and V-01..V-03; `- Scope-Paths:` matches all 8 test files plus the plan.
- Verified that each validation check requires pasted diff evidence, per-test outcome lists, and census details.

### Step R3

- Checked: batch rule step 1 directory initialization hardened with `mkdir -p .aw/state/59aiyh/`. Safety stop added for prerequisite builder/codemod symbols.

### Step R4

- Checked: Mermaid diagram added per Requirement 12b. No em or en dashes in user-facing prose.

### Step R5

- Checked: OQ-01 resolved and assigned to `- Owner: plan author`.

### Step R6

- Checked: gate requires `aw ipd finalize vaqtii` and pre-transition lint clean.

### Step R7

- Checked: verified pre-review lint, baseline test suite execution, and post-revision lint.

### Check S5

- Checked: OQ-01 has status, owner, rationale, and recommendation strength.

### Pass 2

All review checks pass.

AW-REVIEW: DONE

### Findings

| Id | Severity | Status | Category | Location | Summary | Risk (C/U/S/F) | Resolution | Action |
|---|---|---|---|---|---|---|---|---|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261109-metastore-210-vaqtii-move-second-half-unmatched-test-data-chunk-1-of-3-onto-the-r.ipd.md:173-181 | `Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), omitted the scope fence declaration clarification, and lacked a narrow safety stop if prerequisite builder/codemod symbols from `9rgn2w` or `653ndz` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), scope fence declaration clarification, and narrow safety stop if prerequisite builder/codemod symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261109-metastore-210-vaqtii-move-second-half-unmatched-test-data-chunk-1-of-3-onto-the-r.ipd.md:99-109 | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the batch conversion of test data and final verification (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261109-metastore-210-vaqtii-move-second-half-unmatched-test-data-chunk-1-of-3-onto-the-r.ipd.md:38-48 | The checklist preamble instructed saving the batch file list to `.aw/state/59aiyh/<batch>-files.txt` before editing, but the directory `.aw/state/59aiyh/` does not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-01 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/59aiyh/` and baseline capture instruction into E-01 and batch rule step 1 (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261109-metastore-210-vaqtii-move-second-half-unmatched-test-data-chunk-1-of-3-onto-the-r.ipd.md:142-148 | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-210-vaqtii-move-second-half-unmatched-test-data-chunk-1-of-3-onto-the-r.ipd.md:8-10 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can Chunk 1 of 3 execute in any order relative to other chunk plans? | Yes. Module sets are disjoint, each chunk depends on builder and codemod, and none edits `tests/support.py` (which runs in `59aiyh` E-09). | Impose strict serial ordering across all chunk plans (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | How are private test helpers handled in target modules? | `tests/test_legacy_finalize.py` has helper `write_plan` which is deleted if uncalled; for other modules, delete uncalled helper if discovered or justify if surviving. | Keep dead helper functions (rejected: leaves redundant untested code paths); delete without caller check (rejected: risk of breaking unmigrated tests). | `vaqtii` E-01, E-02 | yes |
| D-3 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `vaqtii` Batch rule step 4, research `nj8zdp` | yes |
| D-4 | How should test fixtures with deliberately invalid values be constructed? | Use `RecordBuilder` with `raw_fields=` to inject invalid metadata bullets while maintaining structured generation. | Use raw markdown string literals or heredocs (rejected: bypasses builder pattern established for phase B). | `vaqtii` Batch rule step 4, spec `4sd62s` section 6 | yes |
| D-5 | How is `.aw/state/59aiyh/` initialized across lane worktrees? | Create `.aw/state/59aiyh/` via `mkdir -p .aw/state/59aiyh` at step 1 before recording test outcome lists in each lane worktree. | Rely on preexisting state directory (fails in isolated git worktrees where `.aw/state/` is gitignored and not shared). | `vaqtii` Batch rule step 1, isolated lane environment | yes |
