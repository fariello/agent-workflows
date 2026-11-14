# Review findings: plan iog3cw

- Subject-Id: iog3cw
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `44d0a8b63` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_executed_transition_gate.py tests/test_ipd_dependency_statement_gate.py` printed `29 passed in 1.05s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-004 | MD-15, Section 7.2 |
| `E-03` & checklist preamble | Assumed `.aw/state/iog3cw/` exists before saving batch list | Added explicit `mkdir -p .aw/state/iog3cw/` and baseline capture instruction into E-03 and batch rule | PR-003 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 and OQ-02 had `- Owner: none` | Updated both to `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite format-aware helper from `j5fqax` is absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Converts test assertions across 4 test modules to use the format-aware field helper, supporting cutover preparation for spec `4sd62s` C10a; downstream cutover plan `cxxmyv` relies on these conversions.
2. No. Touches test files only (`tests/test_backlog_gate_follows_status.py`, `tests/test_backlog_new_gate_vocabulary.py`, `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_production.py`), none of which guard private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 3 execution items across 1 task group and 4 work scope paths (all test modules).
4. Yes. `- Scope-Paths:` explicitly declares all files to modify.
5. Yes. Errors in converting setter-byte assertions could falsely pass or hide regressions in backlog gate behavior, vocabulary validation, positional close gates, or production backlog flows.

AW-TIER: standard

### Step R1

- Checked: `tests/test_backlog_gate_follows_status.py`, `tests/test_backlog_new_gate_vocabulary.py`, `tests/test_backlog_positional_close_gate.py`, `tests/test_backlog_production.py`; spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (Section 6, Section 7 step 9, C10a); prerequisite plans `1ajqaa`, `59aiyh`, `90iqr1`, `dcerjg`, `g5hpbb`, `ya4ee4`, `j5fqax`, `545ag7`.
- Verified that all cited test modules exist and candidate line counts match the Concern statement (18 in S02, 16 in S03, 34 total).

### Step R2

- Checked: 1:1 bijection between E-03, E-04, E-12 and V-03, V-04, V-12; `- Scope-Paths:` completeness; `- Item-Dependencies:` resolution (`executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:ya4ee4, executed:j5fqax, executed:545ag7`); and verification reachability.
- Verified that V-03, V-04, V-12 demand verifiable evidence (empty diff between before/after batch test outcome lists, F-28 rg -c counts and classification, full pytest summary line, aw sanitize zero fail, and git show stat).

### Step R3

- Checked: Security and privacy lens. Test assertion refactoring to format-aware helpers does not touch trust boundaries, secrets, or sandboxes.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Sized cleanly (3 items, 1 task group, 4 work paths). Batch rule ensures strict preservation of test coverage and behavior across all converted test modules.

### Step S5

- Checked: Open questions. OQ-01 and OQ-02 resolved. Review decisions (D-1..D-4) recorded and verified (`Reversible: yes`). No blocking questions remain.

### Pass 2

- Re-read all revised sections of `iog3cw`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | `.aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md:162-165`; `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46` | The execution gate in `## Approval and execution gate` lacked explicit conditional runner/executor finalize ownership ("never a hand `git mv`") and lacked a narrow safety stop if prerequisite metastore helper functions from `j5fqax` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership and narrow safety stop if prerequisite metastore helper from `j5fqax` is absent (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | `.aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md:77-83`; `.aw/system/workflows/technical-writing/technical-writing.md:40-46` | `Proposed changes` lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid `flowchart TD` diagram to `Proposed changes` illustrating the batch conversion of test assertions and final verification (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | `.aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md:37-41` | The checklist preamble instructed saving the before-list of test outcomes to `.aw/state/iog3cw/<batch>-before.txt` before editing, but the directory `.aw/state/iog3cw/` does not exist by default, which would cause shell redirection to fail; also E-03 did not explicitly mention capturing this baseline before editing. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/iog3cw/` and baseline capture instruction into E-03 and the batch rule preamble (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | `.aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md:120-135` | OQ-01 and OQ-02 had `- Owner: none` despite being marked `- Status: resolved`, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 and OQ-02 to `- Owner: plan author` (strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize iog3cw` itself"), clarify scope fence declaration, and add a narrow safety stop if prerequisite metastore helper functions from `j5fqax` are absent | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`; `AGENTS.md` "Agent execution contract" | yes |
| D-2 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in `Proposed changes` illustrating the batch conversion of test assertions and final verification | Omit diagram (violates Requirement 12b) | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-3 | How should the plan ensure the baseline batch list directory exists before file redirection? | Add explicit `mkdir -p .aw/state/iog3cw/` and baseline capture instruction into E-03 and the batch rule preamble | Rely on ambient existence of directory (would fail on missing directory) | `.aw/records/plans/pending/20261108-metastore-44-iog3cw-add-the-format-aware-field-assertion-helper-and-move-the-fir.ipd.md:37-41` | yes |
| D-4 | How should OQ-01 and OQ-02 owner fields be attributed? | Update `- Owner: plan author` for both | Leave `- Owner: none` (violates Check S5 attribution guidance) | `.aw/system/workflows/plan-review/steps/s5-questions.md:20-22` | yes |
