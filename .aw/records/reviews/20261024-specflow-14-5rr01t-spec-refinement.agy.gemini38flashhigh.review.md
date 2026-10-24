# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 9)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: agy/gemini-3.8-flash-high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED

## Round 9

All claims verified against repository baseline `542a6183758578fbba65c2e9094245daff8b92bd` (working tree clean).

This ninth adversarial review performed an exhaustive verification pass across candidate specification `18hh1u` (`.aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md`, Set `specflow`).

Nine material defects and actionable precision gaps were identified and resolved (F-28 through F-36). All corrections have been applied directly to candidate spec `18hh1u`.

### Scope and Verification Summary

1. **CLI Handoff Contract**: Verified that `aw specs check` requires a concrete file path or no arguments, resolving the failure where passing an `id6` caused unreadable spec errors.
2. **Cancellation and Signal Trapping**: Established a strict contract for `SIGINT` (Ctrl+C), `SIGTERM`, and CLI cancellation (`aw specs flow cancel`, `aw research flow cancel`), guaranteeing termination of spawned child worker processes (`oc`/`agy`) within 3 seconds, ledger checkpointing with `interrupted` or `cancelled`, and clean attention pipeline recovery.
3. **Research Flow Symmetry**: Added dedicated `aw research flow prepare`, `aw research flow reconcile` (alias `merge`), and `aw research flow cancel` subcommands to match `aw specs flow` capabilities.
4. **Parser Gap Documentation**: Documented the Decision D177 parser gap in `agent_workflows.research_contract.parse_name` alongside `artifact_naming._CLUSTERED_RE`.
5. **Execution Budget Headroom**: Increased the default global turn budget from 30 to 40 turns, providing necessary resilience against transient network and schema retries without violating runaway bounds.
6. **Synthesizer Context Overflow Protection**: Specified a two-pass hierarchical synthesis strategy (Pass 1 matrix compilation, Pass 2 partitioned section authoring) when candidate volume exceeds 80% of synthesizer context capacity.
7. **Convergence Verification Integrity**: Strengthened FR-09 to require an explicit audited scope census in `.review.md` before zero findings can trigger convergence.
8. **Chunking Phasing Boundary**: Clarified that Phase 1 encompasses modular brief/task partitioning for context-limited models (`gemini38flashhigh`), while arbitrary recursive multi-document chunking and assembly is deferred to Phase 2.
9. **Ordering and Metadata Formalization**: Formulated the deterministic NN slot-block formula (`NN = 10 + (slot_index * 10) + step`) and defined YAML schemas for intermediate specs, review records, and synthesis artifacts.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| F-28 | HIGH | IN-SCOPE | CLI Handoff Contract | FR-21; AT-11; Sec 13.1; Sec 13.4 | Candidate spec specified `aw specs check <spec-id6>`. Repository inspection shows `specs check` accepts `[path]` or nothing; passing an `id6` treats it as a path and errors with `attention.unreadable: cannot read/decode spec`. | Low | FIXED | Updated FR-21, AT-11, and Section 13 transcripts to specify `aw specs check .aw/records/specs/to-review/<filename>`. |
| F-29 | HIGH | IN-SCOPE | Process Lifecycle & Cancellation | Table 3.4; Sec 4.3; Sec 7.3 | Candidate spec lacked cancellation commands and signal trapping specifications. Without explicit `SIGINT`/`SIGTERM` handling, spawned runner subprocesses (`oc`/`agy`) could become orphaned runaway tasks consuming tokens. | Low | FIXED | Added `aw specs flow cancel` and `aw research flow cancel` to Table 3.4; added FR-33, AT-23, Decision 10, and updated State Diagram 7.3 with `Cancelled` and `Interrupted` transitions. |
| F-30 | MEDIUM | IN-SCOPE | Research CLI Command Symmetry | Table 3.4; Sec 11 | `aw specs flow` provided `prepare` and `merge`, but `aw research flow` lacked dedicated `prepare`, `reconcile` (alias `merge`), and `cancel` subcommands. | Low | FIXED | Added `aw research flow prepare`, `aw research flow reconcile`, and `aw research flow cancel` to Table 3.4 and Section 11 phasing. |
| F-31 | MEDIUM | IN-SCOPE | Research Contract D177 Parser Gap | Sec 6.2; Decision D177 | Section 6.2 noted parser gaps in `artifact_naming._CLUSTERED_RE` but omitted `agent_workflows.research_contract.parse_name`, which strictly enforces `[.<model>].<kind>` and rejects `<ace>.<model>.<kind>` with `NameError_`. | Low | FIXED | Documented required extension to `research_contract.parse_name` and `ResearchName` in Section 6.2. |
| F-32 | MEDIUM | IN-SCOPE | Execution Bounds Headroom | Sec 4.3.1; Sec 5.2 | Thorough mode happy path requires 26 turns. Setting `global_turn_budget: 30` left only 4 turns of headroom before aborting on isolated transient retries (`max_retries_per_turn: 2`). | Low | FIXED | Adjusted default `global_turn_budget` to 40 turns in Section 4.3.1 and Section 5.2, and added retry arithmetic explanation. |
| F-33 | MEDIUM | IN-SCOPE | Context Budget Management | Sec 4.4; Sec 7.4 | Multi-candidate inputs passed simultaneously to the synthesizer can exceed the synthesizer's context budget (e.g. 80k chars), risking context truncation. | Low | FIXED | Added FR-34, AT-24, and Section 7.4.5 defining two-pass hierarchical synthesis (Pass 1 matrix compilation, Pass 2 partitioned section drafting). |
| F-34 | LOW | IN-SCOPE | Review Convergence Integrity | FR-09 | FR-09 allowed declaring convergence upon zero critical/major findings without requiring the review record to certify that all required sections and constraints were audited. | Low | FIXED | Strengthened FR-09 to require an explicit audited scope census in `.review.md` before convergence is accepted. |
| F-35 | LOW | IN-SCOPE | Chunking Phasing Boundary | Sec 1.6; Sec 7.4 | Section 1.6 listed document chunking as deferred to Phase 2 while Section 7.4 specified modular chunking for Gemini Flash High as active. | Low | FIXED | Clarified that Phase 1 includes brief-level partitioned prompt generation (`modular-chunks`), while arbitrary multi-document recursive chunking is Phase 2. |
| F-36 | LOW | IN-SCOPE | Ordering and Metadata Formalization | Sec 6.3 | Section 6.3 lacked an explicit NN slot-block formula and lacked YAML front matter schema definitions for intermediate specs, reviews, and synthesis artifacts. | Low | FIXED | Defined `NN = 10 + (participant_slot_index * 10) + step` and documented complete YAML schemas for all intermediate artifacts in Section 6.3. |
