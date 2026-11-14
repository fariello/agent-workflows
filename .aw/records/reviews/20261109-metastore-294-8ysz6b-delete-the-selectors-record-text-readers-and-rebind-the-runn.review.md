# Review findings: plan 8ysz6b

- Subject-Id: 8ysz6b
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `91538aa37` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests passed on unmodified code: `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 tests/test_runner_shared.py tests/test_front_matter_loose_whitespace.py tests/test_history_order.py tests/test_fixfirst_end_to_end.py tests/test_blocks_release_reader_bounding.py` printed `196 passed in 145.48s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-004 | MD-15, Section 7.2 |
| `E-01` & checklist preamble | Assumed `.aw/state/9o83cr/` exists before saving PIN list | Added explicit `mkdir -p .aw/state/9o83cr/` and baseline test capture instruction into E-01 and preamble | PR-003 |
| `## Proposed changes` | Ordered list of 5 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 had `- Owner: none` | Updated `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite metastore symbols from `59aiyh`, `71ewpn`, `ffceq0`, or `t4gl15` are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. Deletes public text readers `selectors.read_front_matter_id`, `read_front_matter_status`, and `read_front_matter_blocks_release`, and regex constants `_ID_RE`, `_STATUS_RE`, and `_SET_RE`, and rebinds runner re-exports `oc_runipd._read_id` and `agy_runipd._read_id`.
2. No. Does not touch code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact plan with 5 execution items across 1 task group and 8 work scope paths.
4. Yes. `- Scope-Paths:` explicitly declares all files to modify.
5. Yes. Regressing front-matter id or status extraction could disrupt runner execution or artifact metadata parsing.

AW-TIER: standard

### Step R1

- Checked: `agent_workflows/selectors.py` (definitions of `read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release`, `_ID_RE`, `_STATUS_RE`, `_SET_RE`), `agent_workflows/oc_runipd.py` (import of `_read_id`), `agent_workflows/agy_runipd.py` (assignment of `_read_id`), `agent_workflows/artifact_meta.py` (call to `_sel.read_front_matter_id`), `tests/test_runner_shared.py` (`CrossHostReadIdReExportTests`), `tests/test_front_matter_loose_whitespace.py` (3 calls), `tests/test_history_order.py` (1 call), `tests/test_fixfirst_end_to_end.py` (1 call), `tests/test_blocks_release_reader_bounding.py` (5 calls); spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5, Section 4.3, Section 7 step 7, AC-1); prerequisite plans `1ajqaa`, `59aiyh`, `71ewpn`, `dcerjg`, `ffceq0`, `g5hpbb`, `t4gl15`.
- Verified that all cited modules exist, caller counts match the plan's Concern statement exactly (3, 1, 1, 5; 1 in `artifact_meta.append_legacy`), and verified that newly added `review_basis.py` (lines 95, 127) will be governed by the plan's existing scope fence clause (`--scope-reason`) if live when Order 294 executes.

### Step R2

- Checked: 1:1 bijection between E-01..E-05 and V-01..V-05; `- Scope-Paths:` completeness; `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:71ewpn, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15`; and verification reachability.
- Verified that V-01..V-05 demand verifiable evidence (regex asserting zero reader references across codebase, pytest passing `CrossHostReadIdReExportTests`, diff of PIN lists without failures, and git show stat).

### Step R3

- Checked: Security and privacy. Reader deletion and runner re-export rebinding do not touch trust-boundary inputs, credentials, or isolation barriers.

### Step R4

- Checked: Engineering rubric, right-sizing, anti-regression, and conceptual density.
- Sized cleanly (5 items, 1 task group, 8 work Scope-Paths). PIN rule ensures strict preservation of test coverage and all input cases.

### Step S5

- Checked: Open questions. OQ-01 resolved. Review decisions (D-1..D-4) recorded and verified (`Reversible: yes`). No blocking questions remain.

### Pass 2

- Re-read all revised sections of `8ysz6b`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, and verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md:144 | The execution gate in ## Approval and execution gate lacked explicit conditional runner/executor finalize ownership ("never a hand git mv") and lacked a narrow safety stop for missing prerequisite metastore symbols from 59aiyh, 71ewpn, ffceq0, or t4gl15. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added conditional runner/executor finalize ownership and narrow safety stop if prerequisite metastore symbols from 59aiyh, 71ewpn, ffceq0, or t4gl15 are absent. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md:75-81 | Proposed changes lacked a Mermaid flowchart diagram required by Technical Writing Standard Requirement 12b for multi-step processes. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram to Proposed changes illustrating the sequence of rebinding runner re-exports, retargeting tests, deleting readers, and deleting regex patterns. Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md:34-36,40-44 | The preamble instructed saving the before-list of test modules to .aw/state/9o83cr/E-11b-before.txt before E-01, but directory .aw/state/9o83cr/ does not exist by default, which would cause shell redirection to fail; also E-01 did not explicitly mention capturing this baseline before the first edit. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit mkdir -p .aw/state/9o83cr/ and baseline capture instruction into E-01 and preamble. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md:109 | OQ-01 had - Owner: none despite being marked - Status: resolved, which contradicts Check S5 owner attribution rules. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated OQ-01 to - Owner: plan author. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How should the plan execution gate specify lifecycle transition ownership and safety stops? | Add conditional runner/executor finalize ownership ("never a hand git mv", "When aw oc run or aw agy run executes the plan, the runner performs the finalize; a hand executor runs aw ipd finalize 8ysz6b itself"), clarify scope fence declaration, and add a narrow safety stop if prerequisite metastore symbols from 59aiyh, 71ewpn, ffceq0, or t4gl15 are absent. | Leave unconditional finalize instruction (violates s7-finalize.md); omit prerequisite safety stop. | .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46; AGENTS.md "Agent execution contract" | yes |
| D-2 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid flowchart TD in Proposed changes illustrating the sequence of rebinding runner re-exports, retargeting tests, deleting readers, and deleting regex patterns. | Omit diagram (violates Requirement 12b). | .aw/system/workflows/technical-writing/technical-writing.md:40-46 Requirement 12 | yes |
| D-3 | How should the plan ensure the baseline PIN list directory exists before file redirection? | Add explicit mkdir -p .aw/state/9o83cr/ and baseline capture instruction into E-01 and preamble. | Rely on ambient existence of directory (would fail on missing directory). | .aw/records/plans/pending/20261109-metastore-294-8ysz6b-delete-the-selectors-record-text-readers-and-rebind-the-runn.ipd.md:34-36 | yes |
| D-4 | How should OQ-01's owner field be attributed? | Update - Owner: plan author. | Leave - Owner: none (violates Check S5 attribution guidance). | .aw/system/workflows/plan-review/steps/s5-questions.md:20-22 | yes |
