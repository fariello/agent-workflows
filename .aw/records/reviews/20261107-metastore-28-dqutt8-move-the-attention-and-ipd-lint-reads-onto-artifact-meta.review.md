# Review findings: plan dqutt8

- Subject-Id: dqutt8
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini-3.8-flash
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `331f29f22` in an isolated runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md` was committed and clean at turn start, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (0 findings across all severities). Baseline test execution across the five existing attention modules (`tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_history_consumers_shared_reader.py`, `tests/test_history_date_clock_readers.py`, `tests/test_prompts_attention.py`) passed (116 passed in 15.58s). Live inspection against governing spec `4sd62s` (C5, Section 4.4, Section 7 step 5), orchestrator `63ib9r` (row 28, `E-28`/`V-28`), split parent `ffceq0`, sibling split plan `1suzlp`, executed carrier `2xwb9b`, and all declared Scope-Paths uncovered findings `PR-001..PR-006`, all fixed in place. Pass 2 re-checked `E-01..E-02` and `V-01..V-02`, added verified `Carrier-Evidence` for finished carrier `2xwb9b`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with 0 findings across all severities.

### Proofreading

Checked `.aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md` against all 12 numbered requirements of `.aw/system/workflows/technical-writing/technical-writing.md` and `.aw/system/workflows/plan-review/steps/p-proofread.md`.

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted scope fence declaration, lacked conditional runner/executor finalize ownership, and lacked safety stop clause | Added declaration scope fence with `--scope-reason`/`--scope-ack`, narrow safety stop for missing prerequisite reader interfaces or concurrent edits, and conditional runner/executor finalize ownership ("never a hand `git mv`") | PR-001, `steps/s7-finalize.md` execution-contract rules. |
| `## Proposed changes` | Ordered list of 1 step without diagram | Ordered list of 2 steps plus Mermaid `flowchart TD` diagram | PR-002, Technical Writing Standard Requirement 12(b). |
| Checklist preamble and `E-01` | Saved baseline files to `.aw/state/ffceq0/` without ensuring directory existence | Added explicit `mkdir -p .aw/state/ffceq0` instruction in checklist preamble and `E-01` | PR-003, R2 executability in fresh lane worktrees. |
| Open questions (`OQ-01`) | Recorded `- Owner: none` on resolved question | Updated to `- Owner: plan author` and logged decision `D-1` in `### Decisions` | PR-004, `steps/s5-questions.md` owner attestation rule. |
| Front matter, line 20, Step 0, `## Workflow history` | Retained template prompt blockquote, bare symbol citations in Step 0, lacked `Readiness` and `Review-Depth` | Replaced blockquote with technical writing compliance statement; qualified Step 0 symbols to `path::Symbol`; added `- Readiness: go-pending-approval`, `- Review-Depth: standard`, `- Status: reviewed`, and newest-first review history entry | PR-005, Technical Writing Standard Requirement 1, Section 11.1, and Step S7. |
| `E-02` expected outcome | Stale reference to parent item `E-04` ("E-04 and its five baseline modules pass unchanged") | Replaced stale reference with `E-01` ("E-01 and its five baseline modules pass unchanged") | PR-006, R2 executability and reference consistency. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. No. The plan moves internal attention reader call sites in `agent_workflows/attention.py` onto `artifact_meta.query` and `artifact_meta.history` without modifying public CLI options, output schema, or external contract interfaces.
2. No. Modifies read-only triage and reporting modules (`agent_workflows/attention.py` and `agent_workflows/attention_contract.py`), not code guarding private data, commits, worktree isolation, or sandboxes.
3. No. Compact child plan with 2 execution items (E-01, E-02) in 1 task group across 2 work Scope-Paths (`agent_workflows/attention.py`, `agent_workflows/attention_contract.py`) plus test module `tests/test_readers_attention.py`.
4. Yes. `- Scope-Paths:` explicitly declares all modified files.
5. Yes. `aw attention` is the central cross-tree status and readiness reporting surface across repository automation and runner triage; inaccurate status mappings or silent record omission would corrupt attention reporting across all trees.

AW-TIER: standard

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5, Section 4.4, Section 7 step 5); orchestrator `63ib9r` (row 28, `E-28`/`V-28`); split parent `ffceq0` (Order 08); sibling split plan `1suzlp` (Order 151); executed carrier `2xwb9b` (Order 06); and all declared Scope-Paths files.
- Checked: all 9 prerequisite plans in `- Item-Dependencies: executed:g5hpbb, executed:tve77h, executed:xexn45, executed:r81uvz, executed:w1cs3p, executed:na188y, executed:i3b5zu, executed:ebrc4t, executed:1suzlp`.
- Checked: symbols in `agent_workflows/attention.py` (`scan`, `_plans_record`, `_spec_record`, `_backlog_record`, `_research_record`, `_release_record`, `_prompts_record`, `_plans_id`, `_frontmatter_block`, `_ITEM_DEPS_RE`, `read_readiness`, `_extract_detail`) and `agent_workflows/attention_contract.py` (`history_block`, `last_history_at`, `newest_history_record`).
- Added verified `Carrier-Evidence` for finished carrier `2xwb9b` in `## Deferred / out of scope (with reason)`.

### Step R2

- Checked: 1:1 bijection between E-01..E-02 and V-01..V-02; `- Scope-Paths:` completeness; `- Item-Dependencies:`; and verification reachability.
- Added explicit directory creation in preamble and E-01 for gitignored `.aw/state/ffceq0/` to ensure clean saving of before-baseline outcome lists (PR-003).
- Corrected stale reference in E-02 expected outcome from parent `E-04` to `E-01` (PR-006).

### Step R3

- Checked: security, file paths, and temporary state isolation.
- Baselines are saved strictly under `.aw/state/ffceq0/` (gitignored), avoiding `/tmp` pollution and ensuring no untracked state is committed.
- Incomplete or malformed query records are surfaced as structured `attention.missing-status` violations rather than silently dropped or crashed.

### Step R4

- Checked: conceptual density, right-sizing, anti-regression, and backward compatibility.
- The plan cleanly isolates reader migration into two focused steps: pin current behavior across all six trees (E-01) and retarget reader call sites to `artifact_meta` (E-02).
- Preserves `_extract_detail` fallback cascade when `short_description` is absent (Decision D-5, carried from `ffceq0` D-3).

### Step S5

- Checked: no unresolved open questions; `OQ-01` is resolved and owned by `plan author` (PR-004). All five review decisions (D-1..D-5) are recorded and verified (`Reversible: yes`).

### Pass 2

- Re-read all revised sections of `dqutt8`. Confirmed exact 1:1 E/V mapping, valid Mermaid diagram, zero em or en dashes, verified `Carrier-Evidence` for finished carrier `2xwb9b`, and verified `aw ipd lint --phase review-finalize --agent --verbose` returned clean (0 findings across all severities).
- AW-REVIEW: DONE

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Gate / Lifecycle | .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md:156-163; .aw/system/workflows/plan-review/steps/s7-finalize.md:33-46 | The gate lacked an explicit scope fence declaration section, lacked conditional runner/executor finalize ownership ("never a hand `git mv`"), and lacked a narrow safety stop for missing prerequisite reader interfaces or concurrent edits. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added declaration scope fence, narrow safety stop for missing prerequisite reader interfaces, and conditional runner/executor finalize ownership. Recommendation strength: very strong. |
| PR-002 | MEDIUM | IN-SCOPE | Proofreading / R6 | .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md:96-100; .aw/system/workflows/technical-writing/technical-writing.md:40-46 | `## Proposed changes` contained only a single-line summary and lacked the Mermaid flowchart diagram required by Technical Writing Standard Requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added 2-step process description and Mermaid `flowchart TD` diagram illustrating the pin and move workflow. Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | R2 / Executability | .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md:38,42 | Checklist preamble and E-01 directed saving baseline files to `.aw/state/ffceq0/` without ensuring directory existence, which fails on fresh lane worktrees where `.aw/state/` is gitignored and absent. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added explicit `mkdir -p .aw/state/ffceq0` instruction in checklist preamble and E-01. Recommendation strength: strong. |
| PR-004 | LOW | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md:131-137 | `OQ-01` carried `- Owner: none` on a `- Status: resolved` question, violating the owner attestation standard in `steps/s5-questions.md` Section 3.1 item 5. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated `OQ-01` to `- Owner: plan author` and recorded decision `D-1` in `### Decisions`. Recommendation strength: strong. |
| PR-005 | LOW | IN-SCOPE | Proofreading / S7 / Requirement 1 & Section 11.1 | .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md:9-11,20,58-64 | Plan retained the authoring template prompt blockquote at line 20, used bare symbol citations in Step 0 without path qualification, and lacked S7 front-matter outputs (`- Readiness:`, `- Review-Depth:`, `- Status: reviewed`, review history). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced template prompt blockquote with technical writing compliance statement; qualified Step 0 symbols to `path::Symbol`; added `- Readiness: go-pending-approval`, `- Review-Depth: standard`, `- Status: reviewed`, and review history entry. Recommendation strength: very strong. |
| PR-006 | LOW | IN-SCOPE | R2 / References & Consistency | .aw/records/plans/pending/20261107-metastore-28-dqutt8-move-the-attention-and-ipd-lint-reads-onto-artifact-meta.ipd.md:49 | E-02 expected outcome contained a stale reference to parent item `E-04` ("E-04 and its five baseline modules pass unchanged") from before the split, instead of referencing this plan's pin item `E-01`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Replaced stale reference with `E-01` ("E-01 and its five baseline modules pass unchanged"). Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Does this part fit the step-complexity limits after moving `ipd_lint` (E-03) to `1suzlp`? | Yes. Retaining 2 E-items and 3 work Scope-Paths (`agent_workflows/attention.py`, `agent_workflows/attention_contract.py`, `tests/test_readers_attention.py`) satisfies the ~25 units per item bound. | Keep `ipd_lint` in `dqutt8` (rejected: would exceed unit complexity limits); further split E-02 per tree (rejected: status mapping across trees shares `query()` loop in `scan`). | `dqutt8` `OQ-01`, research `nj8zdp` | yes |
| D-2 | How should the plan execution gate specify lifecycle transition ownership, scope fence, and safety stops? | Add conditional runner/executor finalize ownership ("never a hand `git mv`", "When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize dqutt8` itself"), clarify scope fence declaration with `--scope-reason`/`--scope-ack`, and add a narrow safety stop for missing prerequisite `artifact_meta` interfaces or concurrent edits. | Leave unconditional finalize instruction (violates `s7-finalize.md`); omit prerequisite safety stop. | `.aw/system/workflows/plan-review/steps/s7-finalize.md:31-46`, `AGENTS.md` "Agent execution contract" | yes |
| D-3 | How should the plan satisfy Technical Writing Standard Requirement 12 (Diagrams)? | Add a Mermaid `flowchart TD` in Proposed changes illustrating E-01 pin, E-02 reader move, and V-02 validation. | Omit diagram (violates Requirement 12b). | `.aw/system/workflows/technical-writing/technical-writing.md:40-46` Requirement 12 | yes |
| D-4 | How should baseline directory creation be handled? | Add explicit `mkdir -p .aw/state/ffceq0` instruction in checklist preamble and E-01. | Rely on ambient existence of directory (fails on fresh worktrees where `.aw/state/` is gitignored). | `dqutt8:38,42` | yes |
| D-5 | How should detail text extraction behave when `short_description` is absent in Phase B? | Retain `_extract_detail` cascade fallback when `short_description` is absent, preserving exact output until cutover. | Replace `_extract_detail` immediately (rejected: would lose detail text in Phase B before descriptions are populated). | `dqutt8` D-3, `ffceq0` D-3, spec `4sd62s` Section 4.4 | yes |
