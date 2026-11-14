# Review findings: plan w819as

- Subject-Id: w819as
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `87e30fcb4` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests for all 3 pinned test modules passed: `python3 -m pytest tests/test_plans_index.py tests/test_prompts_index.py tests/test_nv_backend_args_climb.py` printed `38 passed in 11.79s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-005 | MD-15, Section 7.2 |
| `E-01` & checklist preamble | Assumed `.aw/state/w819as/` exists before saving PIN list | Added explicit `mkdir -p .aw/state/w819as` and baseline test capture instruction into E-01 and checklist preamble | PR-003 |
| `## Proposed changes` | Ordered list of 3 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated to `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite metastore symbols from `59aiyh`, `sdzcur`, or `tqknnc` are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Deletes `check.stale-index-missing` and `check.stale-index-stale` findings emitted by `plans_index.check_drift` and `prompts_index.check_drift`, affecting output of `aw check plans` and `aw index prompts --check`, and updates test suites per spec `4sd62s` Section 4.5.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 4 execution items across 1 task group and 6 work modules.
4. Yes. `- Scope-Paths:` explicitly declares all files to modify: `agent_workflows/plans_index.py`, `agent_workflows/prompts_index.py`, `agent_workflows/ipd_lifecycle.py`, `tests/test_plans_index.py`, `tests/test_prompts_index.py`, `tests/test_nv_backend_args_climb.py`, and the plan file itself.
5. Yes. If other drift rules in `check_drift` are accidentally altered or deleted, or if tests are incorrectly retargeted, repository drift detection could silently fail.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/plans_index.py` (lines 386, 397: `check.stale-index-missing` and `check.stale-index-stale` in `plans_index.check_drift`), `agent_workflows/prompts_index.py` (lines 261, 272: `check.stale-index-missing` and `check.stale-index-stale` in `prompts_index.check_drift`), `agent_workflows/ipd_lifecycle.py` (lines 4652, 4973, 6253: comments describing stale-index rules), `tests/test_plans_index.py` (`test_stale_index_flagged` lines 251-260 and `test_missing_index_is_informational_not_failing` lines 262-276), `tests/test_prompts_index.py` (`test_check_drift_missing_index` lines 102-108, `test_check_drift_stale_index` lines 109-127, and docstring lines 6-7), `tests/test_nv_backend_args_climb.py` (`test_assertion_d_outside_project_unaltered` lines 434-452); spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` Section 4.5 (lines 1178-1180); and prerequisite plans `1ajqaa`, `59aiyh`, `dcerjg`, `ffceq0`, `g5hpbb`, `sdzcur`, `t4gl15`, `tqknnc`.
- Verified that all cited functions, lines, and test cases exist in production code and test modules as described.

### Step R2

- Checked: 1:1 bijection between E-01..E-04 and V-01..V-04; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15, executed:tqknnc`; and verification reachability.
- Verified that V-01..V-04 demand verifiable evidence (regex asserting zero remaining stale-index emitters in target modules, diff of pinned before/after outcome lists with mapped cases, test suite pass summary, and git show stat).

### Step R3

- Checked: Security and privacy lens. Deleting obsolete stale-index drift emitters from internal metadata drift checkers does not touch trust boundaries, access control, secrets, or sandboxes.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Sized cleanly (4 items, 1 task group, 6 work paths). PIN rule ensures strict preservation of test coverage and behavior across all 3 pinned test modules. Safe emitter-before-registry ordering ensures no rule is emitted unregistered during intermediate transitions.

### Step R5

- Checked: QA/QC (deterministic outcome list diffs before and after), Architect (removal of gitignored index file drift checks per spec `4sd62s` Section 4.5), Testing/Regression (identical per-test outcomes and explicitly mapped retargets), and Software Engineer (clean removal of obsolete emitter loops).

### Step R6

- Checked: Decomposition and right-sizing. Plan is already a right-sized child chunk of `q6epwc` (Order 41) following research `nj8zdp` guidance. It contains 4 E-items, 1 task group, and 6 work Scope-Paths (well within the <= 5 E-items / <= 8 work paths limit). No further split needed.

### Step R7

- Checked: Cross-plan consistency within Set `metastore`. Aligns with orchestrator `63ib9r`, parent `q6epwc`, prerequisite `sdzcur` (Order 228), and downstream siblings `f1yjlx` (Order 225) and `6qh68x` (Order 229).

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
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md:128-133; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), omitted the scope fence declaration clarification, and lacked a narrow safety stop if prerequisite metastore symbols from `59aiyh`, `sdzcur`, or `tqknnc` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), scope fence declaration clarification, and narrow safety stop if prerequisite metastore symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md:70-74; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the sequential deletion, comment rewrite, and retargeting process (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md:36, 40-43 | The checklist preamble and E-01 instructed saving the PIN list to `.aw/state/w819as/E-01-before.txt` before editing, but the directory `.aw/state/w819as/` does not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-01 did not explicitly mention ensuring the directory exists before saving the baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/w819as` instruction into E-01 and checklist preamble (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md:97-103 | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-224-w819as-delete-the-stale-index-rules-from-the-registry-and-the-check.ipd.md:9-10 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: standard`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: standard` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Is it safe to remove emitters before the registry entries? | Yes; removing emitters leaves registered rules inert, while removing registry first would cause remaining emitters to fall through to `check_engine._DEFAULT_RULESPEC` at severity `error`. | Remove registry entries first or simultaneously (rejected: simultaneously would enlarge child plan scope beyond right-sizing limits). | OQ-01, spec `4sd62s` Section 4.5, Order 229 (`6qh68x`) | yes |
