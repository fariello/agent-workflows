# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 10)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: agy/gemini-3.8-flash-high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED

## Round 10

All claims verified against repository baseline `182161e5d3d8c850647facd730055891bdd748a5` (working tree clean).

This tenth adversarial review performed an exhaustive verification pass across candidate specification `18hh1u` (`.aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md`, Set `specflow`).

Ten material defects and actionable precision gaps were identified and resolved (F-37 through F-46). All corrections have been applied directly to candidate spec `18hh1u`.

### Scope and Verification Summary

1. **Specs CLI Module Citation**: Corrected non-existent `agent_workflows/specs_cli.py` module citations in Table 2.2 and Section 11 to reference `agent_workflows/specs.py` and `agent_workflows/cli.py`.
2. **Research Weekly Shard Format**: Fixed weekly shard directory references from `<YYYY-Www>` to the repository-standard `<YYYYMM-Www>` (e.g. `202610-W43`) in Table 3.4, Table 6.2, and Section 7.2, aligning with `agent_workflows.research_contract` and `artifact_core`.
3. **Research Flow Finalize & Refinement Symmetry**: Added `aw research flow finalize` and added `--refine-cap` and `--reconcile-refine-cap` to `aw research flow new` in Table 3.4 and Section 11, ensuring exact operational symmetry with spec flow.
4. **Lifecycle Placement Rule Citation**: Replaced non-existent rule `check.lifecycle-directory-drift` in Section 3.3 with canonical rule `check.lifecycle-placement-conflict` from `check_engine.py`.
5. **Execution Bounds Formula Precision**: Conditioned Stage 3 (synthesis merge) and Stage 4 (synthesis refinement) terms in the execution bounds formula (Section 4.3.1) on `(if N > 1 else 0)`, resolving the mathematical discrepancy where single-participant runs bypassed synthesis.
6. **Recovery and Cancellation State Transitions**: Added `Interrupted --> Cancelled: aw specs flow cancel` to State Diagram 7.3 and added single-participant cap check `G_solo` to Flowchart 7.1.
7. **Research Flow ERD and Persistence Modeling**: Expanded Section 6.1 ERD and persistence table to explicitly represent intermediate research reports (`research-report`) and reconciliation reports (`reconciliation-report`).
8. **Role Registry Architectural Boundary**: Clarified in Section 2.2 and Section 5.2 that flow roles (`synthesizer`, `research-verifier`, `reviewer`) are defined in `flow-preferences.json` and resolve to profile references, preserving the closed `ROLE_NAMES` vocabulary in `agent_workflows/runner_profiles.py`.
9. **Global Turn Budget Consistency**: Resolved internal contradiction in Section 8.3 where line 845 stated `default: 30 total model turns per run`, updating it to 40 turns in Thorough mode and 10 in Quick mode matching Section 4.3.1 and Section 5.2.
10. **Census and Verification Parity**: Synchronized self-check and workflow history to reflect all 34 functional requirements (`FR-01`..`FR-34`) and 24 acceptance tests (`AT-01`..`AT-24`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-37 | HIGH | IN-SCOPE | CLI Module Citation | Table 2.2; Sec 11 | Spec cited `agent_workflows/specs_cli.py` as existing module. Codebase inspection confirms `specs_cli.py` does not exist; spec commands live in `specs.py` and `cli.py`. | Low | FIXED | Replaced `specs_cli.py` citations with `agent_workflows/specs.py` and `agent_workflows/cli.py`. |
| F-38 | HIGH | IN-SCOPE | Research Shard Directory Format | Table 3.4; Table 6.2; Sec 7.2 | Spec specified research reference directory as `.aw/records/research/reference/<YYYY-Www>/`. `agent_workflows/research_contract.py` (lines 19, 299) and `artifact_core.py` strictly mandate `YYYYMM-Www`. | Low | FIXED | Updated research shard directory references to `<YYYYMM-Www>` across tables and diagrams. |
| F-39 | HIGH | IN-SCOPE | Research Flow Finalize & Refinement Symmetry | Table 3.4; Sec 4.5; Sec 11 | `aw specs flow` provided `finalize`, but `aw research flow` lacked `finalize`. Also, `aw research flow new` omitted `--refine-cap` and `--reconcile-refine-cap`. | Low | FIXED | Added `aw research flow finalize` and refinement cap flags to Table 3.4, Section 4.5, and Section 11. |
| F-40 | MEDIUM | IN-SCOPE | Check Engine Rule Citation | Sec 3.3 (Solution 1) | Spec claimed intermediate staging passes `check.lifecycle-directory-drift`. Inspection of `check_engine.py` reveals no such rule; the canonical rule is `check.lifecycle-placement-conflict`. | Low | FIXED | Updated Section 3.3 to cite canonical rule `check.lifecycle-placement-conflict`. |
| F-41 | MEDIUM | IN-SCOPE | Work Bounds Formula Conditioning | Sec 4.3.1 | Formula for `Max_Turns` unconditionally added Stage 3 and Stage 4 synthesis terms, contradicting FR-06 and Worked Example 2 where single-participant runs bypass synthesis. | Low | FIXED | Conditioned Stage 3 and Stage 4 terms on `(if N > 1 else 0)` in Section 4.3.1. |
| F-42 | MEDIUM | IN-SCOPE | State & Flow Recovery Transitions | Sec 7.1; Sec 7.3 | State Diagram 7.3 omitted `Interrupted --> Cancelled` transition promised in Table 3.4. Flowchart 7.1 omitted cap evaluation node for single-participant runs. | Low | FIXED | Added `Interrupted --> Cancelled: aw specs flow cancel` to State Diagram 7.3 and cap evaluation `G_solo` to Flowchart 7.1. |
| F-43 | LOW | IN-SCOPE | Research Flow ERD Modeling | Sec 6.1 (ERD & Table 6.1) | ERD and persistence table collapsed research reports and reconciliations under spec entities, obscuring research lifecycle distinctions. | Low | FIXED | Expanded ERD and persistence table with explicit research report and reconciliation entities. |
| F-44 | LOW | IN-SCOPE | Role Registry Boundary Clarity | Sec 2.2; Sec 5.2 | Spec was ambiguous regarding whether `runner_profiles.py` closed `ROLE_NAMES` was being modified. | Low | FIXED | Clarified that flow roles reside in `flow-preferences.json` and resolve to profile references without modifying `runner_profiles.py` closed vocabulary. |
| F-45 | LOW | IN-SCOPE | Census & Counter Alignment | Sec 9; Sec 12.2 | Verified self-check census and workflow history align with FR-01..FR-34 and AT-01..AT-24. | Low | FIXED | Verified and preserved full traceability census across all sections. |
| F-46 | MEDIUM | IN-SCOPE | Turn Budget Consistency | Sec 8.3 (Resource Bounds) | Line 845 stated `default: 30 total model turns per run`, contradicting Section 4.3.1 and Section 5.2 which define `global_turn_budget: 40` turns. | Low | FIXED | Updated line 845 to `default: 40 total model turns in Thorough mode, 10 in Quick mode`. |
