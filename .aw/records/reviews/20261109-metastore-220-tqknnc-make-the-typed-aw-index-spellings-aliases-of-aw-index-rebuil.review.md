# Review findings: plan tqknnc

- Subject-Id: tqknnc
- Subject-Type: ipd
- Reviewed-At: 2026-11-14
- Reviewer: antigravity/gemini
- Verdict: APPROVE WITH REVISIONS APPLIED

## Round 1

This review ran at HEAD `16e151859` in a non-interactive runner review-sweep lane worktree. The tracked plan at `.aw/records/plans/pending/20261109-metastore-220-tqknnc-make-the-typed-aw-index-spellings-aliases-of-aw-index-rebuil.ipd.md` was committed and unmodified, so the pre-review snapshot commit was skipped unchanged. Before edits, `aw ipd lint --phase author --agent --verbose` returned `clean` (`0` errors, `0` warnings, `0` info advisories). Live inspection against governing spec `4sd62s` 4.5, parent plan `q6epwc`, and affected CLI/check modules in `agent_workflows/` uncovered one `HIGH`, one `MEDIUM`, and one `LOW` finding (`PR-001..PR-003`), all fixed in place. Pass 2 re-checked `E-01..E-05` and `V-01..V-05`, and `aw ipd lint --phase review-finalize --agent --verbose` returned `clean` with `0` findings across all severities.

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

1. Yes. `tqknnc` turns `aw index plans|research|prompts|all` and `aw research index` into informational aliases calling `aw index rebuild`, stopping the generation of `INDEX.json` and `INDEX.md`.
2. No. It touches `agent_workflows/meta_cli.py`, `agent_workflows/artifact_types.py`, `agent_workflows/command_surface.py`, `agent_workflows/cli.py`, and `agent_workflows/check_engine.py`, not commit locks or isolation machinery.
3. No, it is right-sized at 5 E-items in 2 task groups across 5 production files and 1 test file.
4. Yes. `- Scope-Paths:` explicitly lists all 6 files plus the plan itself.
5. Yes. Regressing CLI index dispatch, alias behavior, or check drift engine wiring could disrupt repository index operations or report false drift violations.

AW-TIER: complex

### Step R1

- Checked: governing spec `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` (section 4.5 index aliases); parent plan `q6epwc` (Order 41); research `nj8zdp` guidance; and target CLI modules in `agent_workflows/`.
- Found owner violation in OQ-01 (`PR-002`): OQ-01 recorded `- Owner: none` on a resolved question. Fixed by setting `- Owner: plan author` and recording D-1 in `### Decisions`.

### Step R2

- Checked: `E-*`/`V-*` bijection (`5/5`: `E-01..E-05` <-> `V-01..V-05`, with `- Highest E allocated: 05` preserved), dependency chain (`E-01 -> E-02, E-03`, `E-02, E-03, E-04 -> E-05`), `- Scope-Paths:` completeness (all changed paths and the plan declared), and runtime reachability of all `V-*` checks.
- Found missing lifecycle finalize clause in Approval and execution gate (`PR-001`): gate lacked the explicit `never a hand git mv` guard and omitted the conditional runner/executor finalize clause required by `steps/s7-finalize.md`. Fixed in Gate.

### Step R3

- Checked: safety, clean alias dispatch without file mutations, graceful handling of `--limit` and `--check`, and regression protection. Verified that no `INDEX.*` files are generated.

### Step R4

- Checked: conformance with spec `4sd62s` 4.5, prompt drift rule migration into `check_engine.check_content`, pytest determinism (`-p no:randomly -n 0`), right-sizing (`5` `E-*` items, `6` work Scope-Paths), and outcome-based testing (`AGENTS.md`).

### Step R5

- Checked: QA/QC (deterministic outcome list diffs and live CLI execution checks), Architect (unifying index generation into `meta_cli.index_rebuild` while deprecating per-type index writers), Software Engineer (preserving command signatures and diagnostic formatting), and Modest Executor (bounded execution items).

### Step R6

- Checked: `5` `E-*` items in `2` task groups across `6` work `- Scope-Paths:` entries (`- Size assessment: standard`; split from `q6epwc` on 2026-11-09 per `nj8zdp`). No further split is required.

### Step R7

- Checked: `- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:sdzcur, executed:t4gl15` (all verified under `.aw/records/plans/`), split parent `q6epwc`, and downstream family plans (Orders 221-227). All contracts align cleanly.

### Step S5

- Checked: pre-existing `OQ-01` (`Blocking: no`, `Status: resolved`), updated owner from `none` to `plan author`; recorded three engineering decisions (`D-1..D-3`) in `### Decisions`, all `Reversible: yes`. Zero human-owned questions remain.

### Pass 2

- Re-reviewed `E-01..E-05` and `V-01..V-05` per `steps/s6-rereview.md` rule 1 after adding gate clauses, Mermaid diagram, and formatting decisions.
- Verified 5-to-5 `E-*`/`V-*` bijection, `- Highest E allocated: 05`, valid `- Scope-Paths:` and `- Item-Dependencies:`, zero em/en dashes, and `0` findings across all severities from `aw ipd lint --phase review-finalize --agent --verbose` (`clean`).
- `AW-REVIEW: DONE`

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | R2 / S7 / Approval and execution gate | .aw/records/plans/pending/20261109-metastore-220-tqknnc-make-the-typed-aw-index-spellings-aliases-of-aw-index-rebuil.ipd.md:147 | Approval and execution gate omitted the explicit hand-mv guard and conditional runner/executor finalize clause, required by steps/s7-finalize.md and rubric G. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added standard hand-mv restriction and conditional runner/executor ownership clause to Gate. Recommendation strength: strong. |
| PR-002 | MEDIUM | IN-SCOPE | R1 / S5 / OQ-01 | .aw/records/plans/pending/20261109-metastore-220-tqknnc-make-the-typed-aw-index-spellings-aliases-of-aw-index-rebuil.ipd.md:110 | OQ-01 recorded - Owner: none on a resolved question, violating the owner attestation standard in steps/s5-questions.md. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Updated - Owner: plan author in OQ-01 and recorded the decision in ### Decisions (D-1). Recommendation strength: strong. |
| PR-003 | LOW | IN-SCOPE | Proofreading / Technical writing standard Requirement 12 / R4 | .aw/records/plans/pending/20261109-metastore-220-tqknnc-make-the-typed-aw-index-spellings-aliases-of-aw-index-rebuil.ipd.md:78 | Proposed changes lacked a Mermaid diagram required by requirement 12(b). | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added Mermaid flowchart TD diagram in Proposed changes showing execution dependency flow. Recommendation strength: strong. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | What does `aw index <type> --check` do once INDEX drift is gone? | Run non-INDEX drift rules and exit as `aw check <type> --all` would, printing the alias notice. | Turn `--check` into a no-op exit 0 (rejected: loses drift verification) or fail with an error (rejected: breaks existing scripts). | `tqknnc` OQ-01, `q6epwc` OQ-01 | yes |
| D-2 | How is `--limit` handled by the alias? | Accept and ignore `--limit` while printing the informational alias notice, preventing CLI argument parse errors on legacy invocations. | Raise an unrecognized argument error (rejected: breaks backward compatibility). | `tqknnc` E-01, `4sd62s` 4.5 | yes |
| D-3 | Where does `prompts_index.check_drift` belong after `run_index` write removal? | Wire `prompts_index.check_drift` directly into `check_engine.check_content` so `name-metadata-mismatch` remains continuously enforced by `aw check prompts`. | Remove the drift check entirely (rejected: permits undetected prompt metadata divergence). | `tqknnc` E-04, `q6epwc` F-04 | yes |
