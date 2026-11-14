# Review findings: plan w13bkp

- Subject-Id: w13bkp
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `f3520fbcd` in an isolated non-interactive runner review-sweep lane worktree. The tracked plan `.aw/records/plans/pending/20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped. Before edits, `aw ipd lint --phase author --agent` returned `clean` (0 findings). Baseline unit tests for all 6 target modules passed: `python3 -m pytest tests/test_set_dispatch_parity.py tests/test_set_refuses_review_record.py tests/test_spec_id6_filenames.py tests/test_spec_production.py tests/test_spec_review_gate_kind.py tests/test_specs_evidence_gate_parity.py` printed `101 passed in 14.26s`. After revisions and status progression, `aw ipd lint --phase review-finalize --agent` returned `clean` with 0 findings.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Front matter | `- Status: to-review`, lacked `- Readiness:` and `- Review-Depth:` | Updated `- Status: reviewed`, added `- Readiness: go-pending-approval` and `- Review-Depth: standard` | MD-15, Section 7.2 |
| `## Workflow history` | Bullets from split and draft creation | Added newest-first review history entry with verdict and findings PR-001..PR-005 | MD-15, Section 7.2 |
| `E-04` & batch rule preamble | Assumed `.aw/state/w13bkp/` exists before saving outcome list | Added explicit `mkdir -p .aw/state/w13bkp` and baseline test capture instruction into E-04 and batch rule preamble | PR-003 |
| `## Proposed changes` | Ordered list of 2 steps, no diagram | Ordered list plus Mermaid `flowchart TD` diagram | PR-002 (Requirement 12b) |
| `## Open questions` | OQ-01 and OQ-02 had `- Owner: none` | Updated to `- Owner: plan author` | PR-004 |
| `## Approval and execution gate` | Lacked explicit conditional runner/executor finalize ownership and prerequisite safety stop | Added conditional runner/executor finalize ownership ("never a hand `git mv`"), clarified scope fence declaration, and added narrow safety stop if prerequisite metastore helper symbols from `j5fqax` or `iog3cw` are absent | PR-001 |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No public interface or spec is changed. The plan converts setter-byte assertions across 6 test modules (`tests/test_set_dispatch_parity.py`, `tests/test_set_refuses_review_record.py`, `tests/test_spec_id6_filenames.py`, `tests/test_spec_production.py`, `tests/test_spec_review_gate_kind.py`, `tests/test_specs_evidence_gate_parity.py`) to use the format-aware field helper (`assert_field`/`assert_no_field`).
2. No. Touches only test modules under `tests/`; no production or security/isolation guard code is modified.
3. No. Compact plan with 2 execution items across 2 task groups and 6 test modules.
4. Yes. `- Scope-Paths:` explicitly declares all 6 test modules and the plan file itself.
5. Low. Test assertion conversion only; deterministic before/after per-test outcome lists verify parity (`diff` prints nothing).

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 6 and 7 step 9, C10a); parent cutover plan `cxxmyv` (Order 13); research `nj8zdp` guidance; prerequisite helper plan `j5fqax`/`iog3cw`; and target assertions in the 6 test modules.
- Verified that all 6 test modules exist and all 101 unit tests pass.

### Step R2

- Checked: `E-*`/`V-*` bijection (`2/2`: `E-04` <-> `V-04`, `E-11` <-> `V-11`), `- Highest E allocated: 11`, `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:ya4ee4, executed:qtvk2q, executed:cxylsu, executed:810kpy`, and isolated-lane reachability of every `V-*` demand.
- Checked gate contract: added hand-mv restriction, conditional runner/executor finalize ownership clause, and safety stop if prerequisite metastore helper symbols from `j5fqax`/`iog3cw` are absent.

### Step R3

- Checked: all changes are confined to test assertion conversions in `tests/`, without weakening commit gates, sandbox boundaries, or leak sanitizer awareness.

### Step R4

- Checked: conformance with spec `4sd62s` C10a (main keeps one metadata format at each commit; converted tests assert through active format and continue asserting exact bullet lines on legacy bytes until cutover flips builder).
- Checked: KISS principles, canonical helper reuse (`tests/record_builder.py` helpers), and Modest Executor (linear sequential dependencies).

### Step R6

- Checked: right-sizing at 2 E-items in 2 task groups across 6 test Scope-Paths (`- Size assessment: standard`). Cleanly decoupled split from `cxxmyv`. No further decomposition needed.

### Step R7

- Checked: `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:90iqr1, executed:dcerjg, executed:g5hpbb, executed:iog3cw, executed:ya4ee4, executed:qtvk2q, executed:cxylsu, executed:810kpy`, sibling batches `j5fqax` (Order 261), `545ag7` (Order 262), `qtvk2q` (Order 263), `cxylsu` (Order 264), `810kpy` (Order 265), `aqc3m6` (Order 61), `zgyna1` (Order 62), and downstream cutover integration in `cxxmyv`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` and `OQ-02` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded decisions `D-1` and `D-2` in `### Decisions`, `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Verified `aw ipd lint --phase review-finalize --agent` returned clean (0 findings).
- Verified all 5 findings (PR-001..PR-005) fixed in place.
- Verified structural preservation: headings, E/V ids, and execution states preserved.

AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md:150; .aw/system/workflows/plan-review/steps/s7-finalize.md:31-46 | Approval and execution gate omitted the explicit hand-mv guard, conditional runner/executor finalize clause, and safety stop if prerequisite metastore helper symbols from `j5fqax` or `iog3cw` are absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction, conditional runner/executor finalize ownership clause, and prerequisite helper safety stop to Gate (strong). |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / Technical Writing | .aw/records/plans/pending/20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md:73-81; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | Proposed changes lacked a Mermaid diagram required by Technical Writing Standard Requirement 12b. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing batch execution flow (strong). |
| PR-003 | LOW | IN-SCOPE | Executability / Environment | .aw/records/plans/pending/20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md:39, 49 | The batch rule preamble and E-04 instructed saving the outcome list to `.aw/state/w13bkp/<batch>-before.txt` before editing, but the directory `.aw/state/w13bkp/` does not exist by default in fresh isolated lane worktrees, causing shell redirection to fail; also E-04 did not explicitly mention ensuring the directory exists before saving the baseline. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/w13bkp` instruction into E-04 and batch rule preamble (strong). |
| PR-004 | LOW | IN-SCOPE | Proofreading / Conventions | .aw/records/plans/pending/20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md:120-129 | OQ-01 and OQ-02 recorded `- Owner: none` on resolved questions, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `- Owner: plan author` in OQ-01 and OQ-02, and recorded the decisions in review record Decisions table (D-1, D-2) (strong). |
| PR-005 | LOW | IN-SCOPE | S7 / Front matter | .aw/records/plans/pending/20261108-metastore-47-w13bkp-move-the-remaining-setter-byte-test-assertions-onto-the-form.ipd.md:8-10 | Plan front matter omitted `- Readiness: go-pending-approval` and `- Review-Depth: standard`, and `## Workflow history` omitted the review history entry. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added `- Readiness: go-pending-approval` and `- Review-Depth: standard` to front matter, updated `- Status: reviewed`, and recorded review history entry in `## Workflow history` (very strong). |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why does this part run so late? | It carries `cxxmyv`'s own dependencies (rule of the 2026-11-07 split), including `90iqr1`, which depends on `9o83cr` and so on every phase-B deletion part. Running after them means the deletion parts' test retargets land first, so no assertion is converted twice. | Run concurrently with phase-B deletions (rejected: risk of churn if assertions are retargeted twice). | OQ-02, plan front matter `- Item-Dependencies:` | yes |
| D-2 | Can this run before the cutover without breaking C10a? | Yes; the format-aware field helper asserts through the active format, which is the legacy format until the cutover, so every converted test continues asserting the exact same bytes and requires no further edits when the cutover flips the record builder. | Defer assertion conversion to cutover commit (rejected: hides hundreds of conversions in an attended, high-risk cutover plan). | OQ-01, spec `4sd62s` C10a | yes |
