# Review findings: plan nbfg7w

- Subject-Id: nbfg7w
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `d479fa74c` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned clean (0 findings). Baseline unit tests for all 8 target test modules passed: `python3 -m pytest tests/test_review_record_classifier.py tests/test_review_rereview.py tests/test_review_sequence.py tests/test_review_sequence_runner.py tests/test_review_staleness_advisory.py tests/test_reviews_type_noun_surface.py tests/test_review_tier.py tests/test_walkthrough_id6.py` printed `75 passed in 5.67s` (with 1 test deselected by default marker filters). After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned clean with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: complex` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-005 | MD-15, Section 7.2 |
| `E-04` & batch rule step 1 | Assumed `.aw/state/59aiyh/` exists before saving batch files | Added explicit `mkdir -p .aw/state/59aiyh/` and baseline capture instruction into E-04 and batch rule step 1 | PR-003 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated to `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite builder/codemod symbols are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Converts test data across 8 review/walkthrough test modules to use the shared record builder `tests/record_builder.py::RecordBuilder` via fixture codemod `tools/fixture_codemod.py` in preparation for phase B cutover (`cxxmyv`, `4sd62s` section 6), and performs the partition catch-up for subsets G5b, G6a, G6b, G6c.
2. No. Standalone test fixture conversion; touches test files only.
3. Yes. Touches 8 test modules across review, record classification, and walkthrough tests, plus late-partition modules; sized at 3 E-items (2 conversion batches and 1 finish).
4. Yes. `- Scope-Paths:` explicitly lists all 8 test module paths plus the plan itself.
5. Yes. If test fixtures are converted incorrectly or test outcomes drift, review system and walkthrough tests could silently lose coverage or falsely pass/fail.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and section 7 step 6); parent plan / orchestrator `63ib9r` row 40; sibling chunk plans in `- Item-Dependencies:` (`i29bd5`, `v1t2ai`, `hp6ydi`, `lf0fe4`, `jjvnhb`, `f8jntm`, `a1b70x`, `j5mwpk`, `abf6yk`, `qjxcgf`, `0punmn`); upstream builder `9rgn2w` and codemod `653ndz`; and the 8 target test modules in `tests/`.
- Verified that all cited test modules exist and F-40 line counts match the Concern statement (29 in test_review_record_classifier, 45 in test_review_rereview, 27 in test_review_sequence, 49 in test_review_sequence_runner, 32 in test_review_staleness_advisory, 2 in test_reviews_type_noun_surface, 13 in test_review_tier, 6 in test_walkthrough_id6; total 203 legacy lines for G6c kept).

### Step R2

- Checked: 1:1 bijection between E-04, E-07, E-06 and V-04, V-07, V-06; `- Scope-Paths:` completeness; `- Item-Dependencies:` resolution (`executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:i29bd5, executed:v1t2ai, executed:hp6ydi, executed:lf0fe4, executed:jjvnhb, executed:f8jntm, executed:a1b70x, executed:j5mwpk, executed:abf6yk, executed:qjxcgf, executed:0punmn`); and verification reachability.
- Verified that V-04, V-07, V-06 demand verifiable evidence (empty diffs between before/after outcome lists, codemod reports, hand-conversion count <= 25, helper censuses, union diff, and git show stat).

### Step R3

- Checked: Security and privacy lens. Test fixture conversion to shared builder does not touch trust boundaries, secrets, or sandboxes. Verified refusal count threshold guard (<= 25) prevents unvetted hand edits.

### Step R4

- Checked: Engineering rubric. Reuses canonical `RecordBuilder` and `fixture_codemod.py` mechanisms. Invariant preservation enforced through strict before/after per-test outcome equality check (`-p no:randomly -n 0 -rA`). Verified right-sizing (3 E-items, 8 work paths). Added Mermaid diagram for multi-step process.

### Step R5

- Checked: Eight personas (QA/QC, testing/regression, architect, software engineer, novice, power user, stakeholder). Zero-drift outcome check and bounded hand conversions protect testing integrity.

### Step R6

- Checked: Decomposition and splitting. Plan is the finishing part of the round-3 split of `59aiyh` / `nbfg7w` with 8 test modules and 3 E-items; right-sized per `IPD-Z603`. No further decomposition needed.

### Step R7

- Checked: Cross-plan consistency. Verified alignment with metastore orchestrator `63ib9r` row 40 and sibling chunk plans (`v1t2ai`, `j5mwpk`, etc.). Module assignments are mutually disjoint.

### Step S5

- Checked: Open questions. OQ-01 verified non-blocking and resolved from repository facts; owner set to plan author. No blocking questions remain.

### Step S6

- Checked: Re-review decision. Edits hardened the plan in place without modifying E/V bijection, scope, or dependencies. No second round needed.
AW-REVIEW: DONE

### Step S7

- Checked: Finalize state and commit. Updated status to `reviewed`, set `- Readiness: go-pending-approval` and `- Review-Depth: complex`, recorded workflow history entry.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Executability / Gate | .aw/records/plans/pending/20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md:205-215 | Execution contract in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), omitted the scope fence declaration clarification, and lacked a narrow safety stop if prerequisite builder/codemod symbols from `9rgn2w` or `653ndz` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), scope fence declaration clarification, and narrow safety stop if prerequisite builder/codemod symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md:119-123; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the batch conversion of test data and final verification (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md:39, 49 | The checklist preamble instructed saving the batch file list to `.aw/state/59aiyh/<batch>-files.txt` before editing, but directory `.aw/state/59aiyh/` does not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-04 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/59aiyh/` and baseline capture instruction into E-04 and batch rule step 1 (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md:175-181 | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261107-metastore-40-nbfg7w-move-runner-family-reader-record-surface-review-and-unmatche.ipd.md:8-10 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: complex`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: complex` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Can the subsets of this part run in any order? | Yes. The kept items and the chunk plans (F-41) are disjoint module lists, each needs only the builder (`9rgn2w`) and the codemod (`653ndz`), and none edits `tests/support.py` (that is `59aiyh` E-09). This plan depends on its chunk plans only so that E-06's late-module catch-up sees their conversions. | Impose strict serial ordering across all chunk plans (rejected: unnecessary serialization of independent test files). | OQ-01, research `nj8zdp` | yes |
| D-2 | How are private test helpers handled in target modules? | Delete private record-building helpers (`tests/test_review_record_classifier.py`: `_make_plan_text`; `tests/test_review_sequence_runner.py`: `_write_plan`, `_write_review_record`; `tests/test_review_staleness_advisory.py`: `_make_plan_text`) when all internal callers move to the record builder; list any surviving helper with justification. | Keep dead helper functions (rejected: leaves redundant untested code paths); delete without caller check (rejected: risk of breaking unmigrated tests). | `nbfg7w` E-04, E-07, F-40 | yes |
| D-3 | What is the threshold for halting hand conversions? | Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting. | Attempt unbounded manual conversions (rejected: high risk of agent mistakes and drift). | `nbfg7w` Batch rule step 4, research `nj8zdp` | yes |
| D-4 | How should test fixtures with deliberately invalid values be constructed? | Use `RecordBuilder` with `raw_fields=` to inject invalid metadata bullets while maintaining structured generation. | Use raw markdown string literals or heredocs (rejected: bypasses builder pattern established for phase B). | `nbfg7w` Batch rule step 4, spec `4sd62s` section 6 | yes |
| D-5 | How is `.aw/state/59aiyh/` initialized across lane worktrees? | Create `.aw/state/59aiyh/` via `mkdir -p .aw/state/59aiyh/` at step 1 before recording test outcome lists in each lane worktree. | Rely on preexisting state directory (fails in isolated git worktrees where `.aw/state/` is gitignored and not shared). | `nbfg7w` Batch rule step 1, isolated lane environment | yes |
