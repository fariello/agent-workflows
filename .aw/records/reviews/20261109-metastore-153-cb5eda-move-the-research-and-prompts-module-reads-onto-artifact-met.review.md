# Review findings: plan cb5eda

- Subject-Id: cb5eda
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `feaf50568` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-153-cb5eda-move-the-research-and-prompts-module-reads-onto-artifact-met.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` C5a, parent plan `jd7874`, and target reader modules in `agent_workflows/` uncovered one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01..E-03` and `V-01..V-03`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

### Proofreading

#### Changes

| Location | Old text summary | New text summary | Reason |
|---|---|---|---|
| Approval and execution gate | Omitted Scope fence hand-mv restriction and conditional runner/executor finalize clause | Added explicit `never a hand git mv` and conditional runner/executor ownership clause ("When `aw oc run` or `aw agy run` executes the plan...") | PR-001. |
| Open questions (OQ-01) | `- Owner: none` recorded on resolved question | Updated to `- Owner: plan author` and recorded decision in `### Decisions` (D-1) | PR-002. |
| Proposed changes | Lacked Requirement 12 Mermaid diagram | Added Mermaid `flowchart TD` diagram to `Proposed changes` showing execution dependency flow | Proofreading, PR-003. |

#### Issues

| ID | Location | Ambiguity | Information needed | Recommended answer | Recommendation strength |
|---|---|---|---|---|---|
| (none) | | | | | |

### Step T

1. Yes. `cb5eda` moves internal readers of `research_index`, `research_archive`, and `prompts_index` onto `artifact_meta.query`/`read`, and makes `derive_pipeline_positions` `has_body` calculation banner-blind.
2. No. It touches `agent_workflows/research_index.py`, `agent_workflows/research_archive.py`, and `agent_workflows/prompts_index.py`, not commit locks or isolation machinery.
3. No, it is right-sized at 3 E-items across 3 production modules and 1 test module.
4. Yes. `- Scope-Paths:` explicitly lists all 4 files plus the plan itself.
5. Yes. Regressing research or prompts indexing could break command workflows, status views, or pipeline position derivation across the repository.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (C5a, section 4.1 banner format); parent plan `jd7874` (Order 35); research `nj8zdp` guidance; and target reader modules in `agent_workflows/`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`3/3`: `E-01..E-03` <-> `V-01..V-03`, with `- Highest E allocated: 03` preserved), dependency chain (`E-01 -> E-02`, `E-01 -> E-03`), `- Scope-Paths:` completeness (all 4 target paths and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause in Approval and execution gate (`PR-001`): gate lacked the explicit `never a hand git mv` guard and omitted the conditional runner/executor finalize clause required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: safety, pin-first baseline comparison, non-breaking backward compatibility of `research_contract.parse_frontmatter` and `prompts_index._parse_metadata_comment`, and isolated banner detection. Verified outcome diff invariance against `.aw/state/t4gl15/`.

### Step R4

- Checked: conformance with spec `4sd62s` C5a, banner-blind body detection logic, pytest determinism (`-p no:randomly -n 0`), right-sizing (`3` `E-*` items, `4` work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs before and after), Architect (decoupling reader modules from physical on-disk INDEX files into memory cache), Software Engineer (pin-first workflow preserving existing reader contracts), and Modest Executor (bounded execution items).

### Step R6

- Checked: `3` `E-*` items in `2` task groups across `4` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `jd7874` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:ffceq0, executed:g5hpbb, executed:h58z9n, executed:tve77h, executed:xexn45, executed:kyl3m4` (all verified under `.aw/records/plans/`), split parent `jd7874`, and successor plan `9o83cr`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-03` and `V-01..V-03` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and formatting decisions.
- Verified 3-to-3 `E-*`/`V-*` bijection, `- Highest E allocated: 03`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-153-cb5eda-move-the-research-and-prompts-module-reads-onto-artifact-met.ipd.md:152 | Approval and execution gate omitted the explicit hand-mv guard and conditional runner/executor finalize clause, required by steps/s7-finalize.md and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction and conditional runner/executor ownership clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-153-cb5eda-move-the-research-and-prompts-module-reads-onto-artifact-met.ipd.md:117 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-153-cb5eda-move-the-research-and-prompts-module-reads-onto-artifact-met.ipd.md:86 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing execution dependency flow. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Why does E-03 depend only on E-01? | E-03 depends solely on E-01 because the banner test exercises the moved `research_index` reader; `prompts_index` (E-02) does not touch `has_body`. | Force serial dependency E-01 -> E-02 -> E-03 (rejected: unnecessary serialization of independent reader moves). | `cb5eda` OQ-01, `jd7874` E-04 | yes |
| D-2 | How should reader parsing functions be handled after migration? | Keep `research_contract.parse_frontmatter` and `prompts_index._parse_metadata_comment` defined with no external reader callers until Order 11 (`9o83cr`), maintaining writer and legacy loader compatibility. | Immediately delete parsing functions (rejected: breaks callers in legacy writer paths before cutover). | `cb5eda` E-01, E-02, `4sd62s` C5a | yes |
| D-3 | Where should banner-blind body detection be computed? | Compute banner stripping in one shared helper used by `research_index.derive_pipeline_positions` or exposed by `artifact_meta`, specifically ignoring the leading `<!-- aw-managed: ... -->` comment rather than stripping arbitrary HTML comments. | Strip all HTML comments indiscriminately (rejected: could silently strip user-authored comments in research bodies). | `cb5eda` E-03, `4sd62s` 4.1, research `53jbi5` | yes |
