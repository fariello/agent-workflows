# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 12)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: agy/gemini-3.8-flash-high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED

## Round 12

All claims verified against repository baseline `6936316fdee618d4b0566fa3c0aee99fe13984a0` (working tree clean).

This twelfth adversarial review performed an exhaustive verification pass across candidate specification `18hh1u` (`.aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md`, Set `specflow`).

Eleven material defects and actionable precision gaps were identified and resolved (F-57 through F-67). All corrections have been applied directly to candidate spec `18hh1u`.

### Scope and Verification Summary

1. **Mermaid Flowchart Syntax Hardening and Undefined Node `O`**: Fixed the undefined node `O` in the Section 7.1 flowchart (`N --> O --> P`) by explicitly defining `O["Write Final Candidate Spec to to-review/"]`. Hardened subgraph declarations across Section 7.1 and 7.2 using quoted string labels (`subgraph Gen_Phase ["..."]`) to prevent parse errors across standard Mermaid engines.
2. **Mermaid Research Diagram Subgraph Directory Alignment**: Replaced phantom directory `research/todo/` in Section 7.2 diagram line 795 with `subgraph Evidence_Phase ["Evidence Collection Phase: Flat Hot Root research/"]`, completing the reconciliation initiated in F-50.
3. **Acceptance Test Matrix Completeness**: Closed the traceability gap where 8 functional requirements had zero mapping in Section 9. Added `AT-29` through `AT-34` covering standard objectives injection & auditable replay (`FR-03`, `FR-03A`, `FR-03B`), prompt rendering & D177 naming (`FR-05`, `FR-25`), iteration accounting vs retry (`FR-08`), non-voting synthesis (`FR-12`), citation non-corroboration (`FR-17`), and research investigation modes (`FR-18A`). Updated audited scope census to `AT-01..AT-34`.
4. **Worked Transcript Model String Accuracy**: Corrected legacy model citation `anthropic/claude-3-opus` in Section 13.2 line 1082 to `anthropic/claude-opus-5-5`, completing model string harmonization across all transcripts and tables.
5. **Acceptance Test Cancellation Exit Parity**: Clarified in `AT-23` that signal-trapped executions exit 1 upon halting, while invoking `aw specs flow cancel <run-id6>` directly exits 0 on clean cancellation (exit 1 if not active), matching Table 3.4, FR-33, and State Diagram 7.3.
6. **Artifact Placement Matrix Completeness**: Expanded Table 6.2 with dedicated rows for rendered refinement prompts, rendered synthesis prompts, scoped context packets, chunk part indexes, and research citation verification prompts conforming to Decision D177.
7. **Two-Digit NN Slot Stride and Exhaustion Safety**: Replaced the fixed `10 + slot * 10` formula in Section 6.3 with a dynamic stride calculation for rosters where N > 4, added fallback sequential allocation via `FLOW_RUN.allocated_nns` when blocks fill, added hard refusal on two-digit sequence exhaustion (NN 99), and disambiguated NN sort sequence from front-matter iteration/attempt counters.
8. **Matrix and Provenance Immutable Link Durability**: Mandated in FR-13 and FR-14 that Similarities/Differences Matrix tables and provenance tags use tool-minted `<id6>` tokens as primary keys rather than mutable file paths, ensuring references remain durable across moves, renames, and regroupings.
9. **Research Models Vocabulary Implementation Seam**: Added an explicit task to Section 11 Phase 1 to register canonical model tokens `opus55high` and `gpt61solmedium` in `agent_workflows/data/research-models.toml` with appropriate normalizations.
10. **CLI Matrix Option Notation and Resume Selector Flexibility**: Documented `--agent` / `--json` support across all research flow verbs and secondary spec flow verbs in Table 3.4. Specified that `resume` commands accept either `<flow-run-id6>` or `<setid>` (resolving to the latest active/interrupted run).
11. **State Diagram Terminal Transitions and Token Telemetry**: Completed terminal transitions to `[*]` from all exit states (`CompleteToReviewMulti`, `CompleteDraftSolo`, `CompleteWithFindings`, `Refused`) in Section 7.3. Added `FR-03B` governing honest token metrics logging (`null`/`unknown` for unsupported runners, prohibiting synthetic cost projection).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-57 | HIGH | IN-SCOPE | Mermaid Flowchart Syntax & Undefined Node | Sec 7.1 | Node `O` had no label or definition in Section 7.1 (`N --> O --> P`), rendering as a bare box with "O". Subgraph labels with slashes/colons were unquoted. | Low | FIXED | Defined `O["Write Final Candidate Spec to to-review/"]` and quoted all subgraph headers with alphanumeric IDs. |
| F-58 | HIGH | IN-SCOPE | Research Flowchart Subgraph Directory | Sec 7.2 | Diagram line 795 still declared `subgraph Evidence Collection Phase: research/todo/`, contradicting F-50 flat hot root alignment. | Low | FIXED | Updated to `subgraph Evidence_Phase ["Evidence Collection Phase: Flat Hot Root research/"]`. |
| F-59 | HIGH | IN-SCOPE | Acceptance Test Matrix Traceability Gap | Sec 9; Sec 12.2 | 8 functional requirements (`FR-03`, `FR-03A`, `FR-05`, `FR-08`, `FR-12`, `FR-17`, `FR-18A`, `FR-25`) had zero mapped acceptance tests. | Low | FIXED | Added tests `AT-29` through `AT-34` providing 100% test coverage across all 36 FRs; updated audited scope in metadata and Section 12.2 to `AT-01..AT-34`. |
| F-60 | MEDIUM | IN-SCOPE | Worked Transcript Model String Inaccuracy | Sec 13.2 | Line 1082 cited legacy `"anthropic/claude-3-opus"` instead of Claude Opus 5.5 (`"anthropic/claude-opus-5-5"`). | Low | FIXED | Corrected model string in Section 13.2 to `"anthropic/claude-opus-5-5"`. |
| F-61 | MEDIUM | IN-SCOPE | Cancellation Acceptance Test Exit Parity | AT-23; Sec 9 | `AT-23` asserted exit 1 for both SIGINT and CLI `cancel`, contradicting Table 3.4 and FR-33 exit 0 clean cancellation. | Low | FIXED | Updated `AT-23` pass criteria: SIGINT exits 1 upon halting; CLI `aw specs flow cancel` exits 0 on clean abort. |
| F-62 | MEDIUM | IN-SCOPE | Artifact Placement Matrix Completeness | Table 6.2 | Missing intermediate rows required by brief: refinement prompts, synthesis prompts, context packets, chunk indexes, and verification prompts. | Low | FIXED | Added explicit D177 rows for all intermediate prompt, index, and packet artifacts to Table 6.2. |
| F-63 | MEDIUM | IN-SCOPE | Two-Digit NN Dynamic Stride & Exhaustion | Sec 6.3 | Fixed NN formula collided for rosters N > 4 and iteration steps > 9. Exhaustion behavior at NN 99 was undefined. | Low | FIXED | Specified dynamic stride for N > 4, fallback sequential allocation via `FLOW_RUN.allocated_nns`, and hard refusal at NN 99. |
| F-64 | MEDIUM | IN-SCOPE | Matrix Provenance Immutable Link Durability | FR-13; FR-14 | Candidate proposals in matrix tables lacked explicit requirement for immutable `<id6>` primary keys, risking broken links upon rename. | Low | FIXED | Mandated immutable tool-minted `<id6>` tokens as primary keys in Similarities/Differences Matrix tables and provenance tags. |
| F-65 | LOW | IN-SCOPE | Implementation Seams Vocabulary Prerequisite | Sec 11 | Phase 1 implementation omitted registering `opus55high` and `gpt61solmedium` in `agent_workflows/data/research-models.toml`. | Low | FIXED | Added explicit model token registration task to Section 11 Phase 1. |
| F-66 | LOW | IN-SCOPE | CLI Table Argument Parity & Resume Selector | Table 3.4 | Table 3.4 omitted `--agent` / `--json` on research verbs. `resume` did not document accepting `<setid>`. | Low | FIXED | Added `--agent` / `--json` to all commands in Table 3.4 and documented `<flow-run-id6> \| <setid>` selector support for resume. |
| F-67 | LOW | IN-SCOPE | State Diagram Termination & Token Policy | Sec 7.3; Sec 4.1 | End states in State Diagram 7.3 did not transition to `[*]`. Token telemetry accounting policy was absent. | Low | FIXED | Added terminal transitions to `[*]` in state diagram; added `FR-03B` defining honest token telemetry and cost accounting policy. |
