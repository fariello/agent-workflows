# Review findings: plan csobg7

- Subject-Id: csobg7
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `37be5722c` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-292-csobg7-move-the-attention-history-readers-and-spec-status-re-and-de.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests for the five pinned test modules passed: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_attention.py tests/test_check_engine.py tests/test_specs_status_dirs.py tests/test_attention_contract.py tests/test_history_block_bounding.py` passed (177 passed). Extra modules passed: `tests/test_artifact_meta_legacy.py` and `tests/test_ipd_lint.py` (84 passed). `aw attention --format json` evaluated validly. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-005 | MD-15, Section 7.2 |
| `E-01` & checklist preamble | Assumed `.aw/state/9o83cr/` and `.aw/state/k6jd6l/` exist before saving PIN list & json | Added explicit `mkdir -p .aw/state/9o83cr/ .aw/state/k6jd6l/` and baseline capture instruction into E-01 and preamble | PR-003 |
| `## Proposed changes` | Ordered list of 5 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated to `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite metastore symbols from `1ajqaa`, `59aiyh`, `ay6sxp`, `dcerjg`, `ffceq0`, `g5hpbb`, or `t4gl15` are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Deletes history grammar functions `history_block`, `newest_history_record`, `last_history_at`, and constant `SPEC_STATUS_RE` from `agent_workflows/attention_contract.py`, retargeting readers in `attention.py`, `check_engine.py`, `specs.py`, and `research_index.py` onto `artifact_meta`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 5 execution items across 1 task group and 5 work modules plus 2 test modules.
4. Yes. `- Scope-Paths:` explicitly declares all files to modify.
5. Yes. If `attention.py` or `check_engine.py` history reading breaks, attention sorting, graduation gates, or close gates could fail to compute artifact history dates, leading to incorrect attention reports or gate evaluation failures.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/attention.py` (6 `A.last_history_at(A.history_block(text).records)` sites in `_prompts_record`, `_release_record`, `_spec_record`, `_plans_record`, `_research_record`, `_backlog_record`), `agent_workflows/check_engine.py` (3 history call sites in `_item_close_date`, `_item_graduated_date`, `_spec_implementing_date`), `agent_workflows/specs.py` (`_find_status_index`, `_read_status`), `agent_workflows/research_index.py` (`_spec_is_implemented`), `agent_workflows/attention_contract.py` (definitions of `SPEC_STATUS_RE`, `history_block`, `newest_history_record`, `last_history_at`), `tests/test_attention_contract.py`, `tests/test_history_block_bounding.py`, spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5, Section 4.3, Section 7 step 7, AC-1), prerequisite plans `1ajqaa`, `59aiyh`, `ay6sxp`, `dcerjg`, `ffceq0`, `g5hpbb`, `t4gl15`, split parent `k6jd6l` with research `nj8zdp`.
- Verified that all symbols exist at cited locations and all callers match Scope-Paths.

### Step R2

- Checked: 1:1 bijection between E-01..E-05 and V-01..V-05; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:ay6sxp, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15`; and verification reachability.
- Verified that V-01..V-05 demand verifiable output (`rg` queries, diffs, attention json validation, and test outcomes). Fixed missing directory creation for `.aw/state/9o83cr/` and `.aw/state/k6jd6l/` in E-01 and preamble.

### Step R3

- Checked: Full security lens for standard tier. Centralizing metadata reads into `artifact_meta` removes fragmented, regex-based parsing across tools and enforces single-writer / single-reader invariants per Spec 4sd62s C5.

### Step R4

- Checked: Engineering quality and domain invariants. Preserves exact history timestamp extraction across all six attention record types and check engine date gates. Ensures `aw attention --format json` produces identical sorted output before and after reader migration.

### Step R5

- Checked: Personas (QA/QC, testing/regression, architect, software engineer). PIN rule and attention JSON comparison verify that attention ordering and gate timestamps remain regression-free.

### Step R6

- Checked: Right-sizing and decomposition. 5 E-items and 7 work Scope-Paths is right-sized for a single focused pass. No further split needed.

### Step R7

- Checked: Cross-plan consistency within Set `metastore`. Aligns with orchestrator `63ib9r`, parent `k6jd6l`, predecessor `ay6sxp` (Order 291), follow-on reader cleanup `specs._read_*` (Order 297), and regex cleanup `tdhav3` (Order 248).

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
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261109-metastore-292-csobg7-move-the-attention-history-readers-and-spec-status-re-and-de.ipd.md:152; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`"), omitted the scope fence declaration clarification, and lacked a narrow safety stop if prerequisite metastore symbols from `1ajqaa`, `59aiyh`, `ay6sxp`, `dcerjg`, `ffceq0`, `g5hpbb`, or `t4gl15` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), scope fence declaration clarification, and narrow safety stop if prerequisite metastore symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261109-metastore-292-csobg7-move-the-attention-history-readers-and-spec-status-re-and-de.ipd.md:77-85; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the sequential reader migration, deletion, and test retargeting sequence (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261109-metastore-292-csobg7-move-the-attention-history-readers-and-spec-status-re-and-de.ipd.md:34-43 | The checklist preamble instructed saving the PIN list to `.aw/state/9o83cr/E-10f-before.txt` and attention JSON to `.aw/state/k6jd6l/attention-292-before.json` before editing, but directories `.aw/state/9o83cr/` and `.aw/state/k6jd6l/` do not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-01 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/9o83cr/ .aw/state/k6jd6l/` and baseline capture instructions into E-01 and checklist preamble (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261109-metastore-292-csobg7-move-the-attention-history-readers-and-spec-status-re-and-de.ipd.md:118 | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261109-metastore-292-csobg7-move-the-attention-history-readers-and-spec-status-re-and-de.ipd.md:9-11 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: standard`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: standard` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Who is the recorded owner for resolved OQ-01? | Set to `plan author` per S5 rules for questions resolved during authoring/review without human intervention. | Leave as `none` (rejected: contradicts S5 owner requirement); set to `maintainer` (rejected: maintainer did not answer). | Check S5, OQ-01 | yes |
| D-2 | Should `specs._read_status` be modified in E-03 even though Order 297 later deletes it? | Yes, modify `specs._read_status` to remove `SPEC_STATUS_RE` so E-04 can cleanly delete `SPEC_STATUS_RE` from `attention_contract.py`. | Leave unedited until Order 297 (rejected: leaves a broken import / reference when E-04 deletes `SPEC_STATUS_RE`). | OQ-01, E-03, E-04 | yes |
