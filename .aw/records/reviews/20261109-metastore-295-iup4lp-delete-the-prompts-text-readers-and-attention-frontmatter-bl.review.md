# Review findings: plan iup4lp

- Subject-Id: iup4lp
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `dc224078a` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-295-iup4lp-delete-the-prompts-text-readers-and-attention-frontmatter-bl.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` C5 and 4.3, split parent `k6jd6l`, prerequisite `8ysz6b`, and affected modules in `agent_workflows/` and `tests/` uncovered one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01..E-04` and `V-01..V-04`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

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

1. No public interface is changed. Internal readers `prompts.read_metadata_id6`, `prompts.read_metadata_status`, `prompts._METADATA_STATUS_RE`, and `attention._frontmatter_block` are deleted, and internal call sites are retargeted to `artifact_meta.read_text`.
2. No. It touches `agent_workflows/prompts.py`, `agent_workflows/artifact_rename.py`, `agent_workflows/attention.py`, `agent_workflows/cli.py`, `agent_workflows/status_set.py`, and `tests/test_prompts_new.py`, not commit locks or isolation machinery.
3. No, it is right-sized at 4 E-items in 1 task group across 5 production files and 1 test file.
4. Yes. `- Scope-Paths:` explicitly lists all 6 files plus the plan itself.
5. Yes. Careless modification of prompt status/id reading or attention detail extraction could regress `aw attention` or prompt metadata maintenance commands.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section C5 single metadata reader invariant and section 4.3); parent plan `k6jd6l` (Order 43); research `nj8zdp` guidance; prerequisite `8ysz6b` (Order 294); and target symbols in `agent_workflows/`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`4/4`: `E-01..E-04` <-> `V-01..V-04`, with `- Highest E allocated: 04` preserved), dependency chain (`E-01 -> E-02 -> E-03 -> E-04`), `- Scope-Paths:` completeness (all changed paths and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause in Approval and execution gate (`PR-001`): gate lacked explicit `never a hand git mv` guard and omitted conditional runner/executor finalize clause required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: security, sandbox boundaries, leak sanitizer awareness, no mock leakage, no test-pinning of source structure (`AGENTS.md`). Verified that prompt metadata reads cleanly route through `artifact_meta.read_text`.

### Step R4

- Checked: conformance with spec `4sd62s` C5 and 4.3, complete elimination of legacy prompt readers and frontmatter block extractor, cascade order preservation in `attention._extract_detail`, determinism (`-p no:randomly -n 0` PIN rule across 4 test modules), right-sizing (4 E-items, 6 work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs and live attention output diff), Architect (retargeting prompt ID and status reads onto `artifact_meta.read_text`), Software Engineer (preserving cascade order in `attention._extract_detail`), and Modest Executor (linear sequential dependencies with callers first, then definitions).

### Step R6

- Checked: right-sizing at 4 E-items in 1 task group across 6 work `- Scope-Paths:` entries (`- Size assessment: standard`). Cleanly decoupled split from `k6jd6l`. No further decomposition needed.

### Step R7

- Checked: `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:8ysz6b, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15` (all verified present under `.aw/records/plans/`), split parent `k6jd6l`, and downstream deletion plans `qttoyc` and `tdhav3`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-04` and `V-01..V-04` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and owner update.
- Verified 4-to-4 `E-*`/`V-*` bijection, `- Highest E allocated: 04`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-295-iup4lp-delete-the-prompts-text-readers-and-attention-frontmatter-bl.ipd.md:150 | Approval and execution gate omitted the explicit hand-mv guard and conditional runner/executor finalize clause, required by steps/s7-finalize.md and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction and conditional runner/executor ownership clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-295-iup4lp-delete-the-prompts-text-readers-and-attention-frontmatter-bl.ipd.md:118 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-295-iup4lp-delete-the-prompts-text-readers-and-attention-frontmatter-bl.ipd.md:75 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing execution dependency flow. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | `artifact_adopt._yaml_frontmatter_block` has a similar name; is it in scope? | No: `k6jd6l` E-11 names only `attention._frontmatter_block`, and `artifact_adopt._yaml_frontmatter_block` frames an inbox file before adoption (not a record); it is kept out of scope for this plan. | Delete both frontmatter block extractors simultaneously (rejected: `artifact_adopt` operates on unvetted external inbox text prior to adoption, which has different parsing constraints). | `iup4lp` OQ-01, `k6jd6l` E-11 | yes |
| D-2 | Cascade precedence in `attention._extract_detail` after replacing `_frontmatter_block`: | Preserve the established cascade order (bulleted form first, then YAML form parsed via `artifact_meta.read_text`), ensuring full backwards compatibility with both legacy bulleted and frontmatter metadata formats. | Only read through `artifact_meta.read_text` and drop bulleted fallback (rejected: could break display of un-migrated or legacy artifacts). | `iup4lp` E-04, Project conventions discovered | yes |
| D-3 | Retargeting `prompts.update_metadata_status`: | Retarget `prompts.update_metadata_status` internal reader to `artifact_meta.read_text` so that status line updates read the current state through the canonical reader before updating the line. | Rewrite `prompts.update_metadata_status` to use raw regex match (rejected: duplicates parsing logic and violates C5 single-reader mandate). | `iup4lp` E-02, Spec `4sd62s` C5 | yes |
