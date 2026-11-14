# Review findings: plan 9eqgcl

- Subject-Id: 9eqgcl
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `813669020` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-223-9eqgcl-stop-research-commands-plan-renames-and-adopt-regenerating-i.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` 4.5, parent plan `q6epwc`, sister orders 220 (`tqknnc`), 221 (`lywgzs`), 222 (`mv0j4k`), and affected modules in `agent_workflows/` uncovered one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01..E-05` and `V-01..V-05`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

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

1. Yes. `9eqgcl` deletes callers of `run_index` across `research_cmd.py` (`set-outcome`, `set-priority`), `research_refs.py`, `plans_refs.py`, and `artifact_adopt.py`, stopping automatic generation of `INDEX.*` files and eliminating obsolete index regeneration stdout notes.
2. No. It touches `agent_workflows/research_cmd.py`, `agent_workflows/research_refs.py`, `agent_workflows/plans_refs.py`, `agent_workflows/artifact_adopt.py`, and test files, not commit locks, leak sanitizer, or isolation machinery.
3. No, it is right-sized at 5 E-items in 2 task groups across 4 production files and 3 test files.
4. Yes. `- Scope-Paths:` explicitly lists all 7 work files plus the plan itself.
5. Yes. Faulty caller deletion or adopt rollback removal could cause file adoption errors or citation rewrite regressions across the repository.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 4.5 index callers); parent plan `q6epwc` (Order 41); research `nj8zdp` guidance; sister orders 220 (`tqknnc`), 221 (`lywgzs`), 222 (`mv0j4k`); target production modules `agent_workflows/research_cmd.py`, `agent_workflows/research_refs.py`, `agent_workflows/plans_refs.py`, `agent_workflows/artifact_adopt.py`; and test modules `tests/test_artifact_refs_rewrite.py`, `tests/test_artifact_adopt.py`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, with `- Highest E allocated: 05` preserved), dependency chain (`E-01 -> E-02, E-03, E-04 -> E-05`), `- Scope-Paths:` completeness (all changed paths and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause in Approval and execution gate (`PR-001`): gate lacked the explicit `never a hand git mv` guard and omitted the conditional runner/executor finalize clause required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: security and safety implications of deleting automatic index refreshes. Verified that the injectable `refresh_index` seam in `artifact_adopt` is preserved so rollback on destination write failure continues to be proven and tested. Verified that no data loss or security exposure can occur.

### Step R4

- Checked: conformance with spec `4sd62s` 4.5, AC-9 (`9o83cr`), and AC-26 (`tve77h`); PIN RULE mechanics (`E-01-before.txt` and `E-05-after.txt`); pytest determinism (`-p no:randomly -n 0`); right-sizing (`5` `E-*` items, `7` work Scope-Paths); and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs and live CLI execution checks), Architect (unifying index retirement across callers while preserving rollback seams), Software Engineer (clean removal of obsolete messages and dead index dispatch), and Modest Executor (bounded execution items).

### Step R6

- Checked: `5` `E-*` items in `2` task groups across `7` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `q6epwc` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:lywgzs, executed:mv0j4k, executed:sdzcur, executed:t4gl15, executed:tqknnc` (all verified under `.aw/records/plans/`), split parent `q6epwc`, sister orders 220 (`tqknnc`), 221 (`lywgzs`), 222 (`mv0j4k`), and downstream plan `snin8q`. All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-05` and `V-01..V-05` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and formatting decisions.
- Verified 5-to-5 `E-*`/`V-*` bijection, `- Highest E allocated: 05`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-223-9eqgcl-stop-research-commands-plan-renames-and-adopt-regenerating-i.ipd.md:144 | Approval and execution gate omitted the explicit hand-mv guard and conditional runner/executor finalize clause, required by steps/s7-finalize.md and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction and conditional runner/executor ownership clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-223-9eqgcl-stop-research-commands-plan-renames-and-adopt-regenerating-i.ipd.md:107 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-223-9eqgcl-stop-research-commands-plan-renames-and-adopt-regenerating-i.ipd.md:82 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing execution dependency flow. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Should `artifact_adopt.apply_adoption` drop the `refresh_index` seam entirely? | Retain the injectable `refresh_index` callable parameter while removing default refresher `_default_refresh_index`, skipping step 2 and reporting `index_refreshed=False` when no refresher is injected. | Remove `refresh_index` entirely (rejected: deletes rollback test injection hook) or keep `_default_refresh_index` calling `run_index` (rejected: continues obsolete index regeneration). | `9eqgcl` OQ-01, `tests/test_artifact_adopt.py:435-439`, `agent_workflows/artifact_adopt.py:871-927` | yes |
| D-2 | How should deleted CLI status and diagnostic notes be handled in tests? | Retarget test assertions in `tests/test_artifact_refs_rewrite.py` and `tests/test_artifact_adopt.py` to surviving outputs and verify that no `INDEX.*` files are generated. | Keep asserting deleted stdout messages (rejected: tests would fail) or delete test modules (rejected: drops regression coverage). | `9eqgcl` E-05, `tests/test_artifact_refs_rewrite.py:642-681` | yes |
| D-3 | Where should the whole-family `producers` test be added? | Add the `producers` case in `tests/test_index_aliases.py` (created by Order 220 `tqknnc`), executing across finalize, rename, group, adopt, and research commands after prerequisites are met. | Place in a new standalone test file (rejected: fragments alias and producer test coverage) or add to each individual module (rejected: lacks unified whole-family verification). | `9eqgcl` E-05, `q6epwc` V-04, `tests/test_index_aliases.py` | yes |
