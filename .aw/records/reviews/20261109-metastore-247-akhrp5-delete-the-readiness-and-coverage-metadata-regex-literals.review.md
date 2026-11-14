# Review findings: plan akhrp5

- Subject-Id: akhrp5
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `ade4785a2` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-247-akhrp5-delete-the-readiness-and-coverage-metadata-regex-literals.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_executed_transition_gate.py tests/test_ipd_dependency_statement_gate.py` printed `29 passed in 0.99s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-004 | MD-15, Section 7.2 |
| `E-01` & checklist preamble | Assumed `.aw/state/akhrp5/` exists before saving PIN list | Added explicit `mkdir -p .aw/state/akhrp5/` and baseline PIN capture instruction into E-01 and preamble | PR-003 |
| `## Proposed changes` | Ordered list of 5 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite metastore symbols from `t4gl15`, `ffceq0`, or `k6jd6l` are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Deletes internal regex literals across `plan_readiness`, `readiness_recheck`, `coverage_record`, and `orchestrator_readiness`, modifying internal metadata extraction paths to route through `artifact_meta`. Downstream finishing plan `0xsx2n` relies on these deletions.
2. No. Touches `agent_workflows/plan_readiness.py`, `readiness_recheck.py`, `coverage_record.py`, and `orchestrator_readiness.py`, none of which guard private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 5 execution items across 1 task group and 7 work scope paths (4 modules, 3 test files).
4. Yes. `- Scope-Paths:` explicitly declares all files to modify.
5. Yes. Mistakes in regex removal or coverage/readiness extraction could break plan readiness assessment, orchestrator validation, or coverage recording.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/plan_readiness.py`, `agent_workflows/readiness_recheck.py`, `agent_workflows/coverage_record.py`, `agent_workflows/orchestrator_readiness.py`, `tests/test_coverage_record.py`, `tests/test_orchestrator_readiness.py`, `tests/test_plan_readiness_recheck.py`; spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 4.3, Section 7 step 7, C5); parent/sibling plans `0xsx2n` (Order 46, E-22, F-27), `786w7r` (Order 238, baseline & LIT definition), and `nx7fws` (Order 246).
- Verified that all cited modules exist and literal counts match the Concern statement (6 in `plan_readiness` plus 1 body prose that stays, 1 in `readiness_recheck`, 4 in `coverage_record`, 1 in `orchestrator_readiness`).

### Step R2

- Checked: 1:1 bijection between E-01..E-05 and V-01..V-05; `- Scope-Paths:` completeness; `- Item-Dependencies:` resolution (`executed:1ajqaa, executed:59aiyh, executed:786w7r, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:k6jd6l, executed:nx7fws, executed:t4gl15`); and verification reachability.
- Verified that V-01..V-05 demand verifiable evidence (LIT search over each module showing zero metadata literals, diff between before and after PIN test lists, summary test pass line, and git show stat).

### Step R3

- Checked: Security and privacy lens. Regex deletions and routing through `artifact_meta` do not touch trust boundaries, secrets, or sandboxes.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Sized cleanly (5 items, 1 task group, 7 work paths). PIN rule ensures strict preservation of test coverage and behavior across all three pinned test modules.

### Step S5

- Checked: Open questions. OQ-01 resolved. Review decisions (D-1..D-4) recorded and verified (`Reversible: yes`). No blocking questions remain.

### Pass 2

- Re-read all revised sections of `akhrp5`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261109-metastore-247-akhrp5-delete-the-readiness-and-coverage-metadata-regex-literals.ipd.md:159-162`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`") and lacked a narrow safety stop for missing prerequisite metastore symbols from `t4gl15`, `ffceq0`, or `k6jd6l`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership and narrow safety stop if prerequisite metastore symbols are absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | `.aw/records/plans/pending/20261109-metastore-247-akhrp5-delete-the-readiness-and-coverage-metadata-regex-literals.ipd.md:78-85`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the deletion of regex literals across all four modules, test updates, and final verification (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | `.aw/records/plans/pending/20261109-metastore-247-akhrp5-delete-the-readiness-and-coverage-metadata-regex-literals.ipd.md:36-40` | The checklist preamble instructed saving the before-list of test outcomes to `.aw/state/akhrp5/before.txt` before E-01, but the directory `.aw/state/akhrp5/` does not exist by default, which would cause shell redirection to fail; also E-01 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/akhrp5/` and baseline PIN capture instruction into E-01 and the checklist preamble (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | `.aw/records/plans/pending/20261109-metastore-247-akhrp5-delete-the-readiness-and-coverage-metadata-regex-literals.ipd.md:120-125` | OQ-01 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to `- Owner: plan author` (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize akhrp5` itself"), clarify scope fence declaration, and add a narrow safety stop if prerequisite metastore symbols from `t4gl15`, `ffceq0`, or `k6jd6l` are absent | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`; `AGENTS.md` "Agent execution contract" | yes |
| D-2 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` illustrating the deletion of regex literals across all four modules, test updates, and final verification | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-3 | How should the plan ensure the baseline PIN list directory exists before file redirection? | Add explicit `mkdir -p .aw/state/akhrp5/` and baseline capture instruction into E-01 and the checklist preamble | Rely on ambient existence of directory (would fail on missing directory) | `.aw/records/plans/pending/20261109-metastore-247-akhrp5-delete-the-readiness-and-coverage-metadata-regex-literals.ipd.md:36-40` | yes |
| D-4 | How should OQ-01's owner field be attributed? | Update `- Owner: plan author` | Leave `- Owner: none` (violates Check S5 attribution guidance) | `.aw/system/workflows/plan-review/steps/s5-questions.md:20-22` | yes |
