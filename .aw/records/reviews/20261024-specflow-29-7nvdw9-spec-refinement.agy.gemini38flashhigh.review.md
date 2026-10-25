# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 24)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-25
- Reviewer: agy/gemini38flashhigh
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED
- Audited-Scope: [FR-01..FR-37, AT-01..AT-79, Decisions 01..14, Sections 1..13, 4 Mermaid diagrams, Flowcharts 7.1 and 7.2, State Diagram 7.3, Table 3.4, Table 6.1, Table 6.2, Worked Inventories 1..4]

This is a design-refinement record produced by prompt `jsgs0f` (refinement prompt). It is not a `/spec-review` attestation and grants no approval.

## Round 24

Baseline: subject file at commit `68f45d212` on `main` (commit incorporating iteration 23 changes from review record `kwsffr`, within tree at `fca4b91bd`). Repository facts and contracts were verified against source on that revision in an isolated git worktree (`.aw/worktrees/refine-18hh1u-iter24`). Reviewer: agy, Google Gemini 3.8 Flash High; identity class asserted by runtime environment.

### Maintainer input during this iteration

No new maintainer rulings were required during this iteration. All 11 findings were resolved deterministically from existing repository contracts, maintainer rulings (DL-16, DL-17), Decision D177, and internal consistency within spec `18hh1u`.

### Scope and verification summary

1. **Workflow Diagrams & Failure Conflation Elimination**: Corrected Flowchart 7.1 and Flowchart 7.2 to eliminate terminal sink state conflation by separating worker failure, partial roster, unverified citation, and cap-with-findings halts into distinct terminal sink nodes (`Q_halt_cap`, `Q_halt_fail`, `Q_halt_part` in Flowchart 7.1; `Stop_halt_cap`, `Stop_halt_fail`, `Stop_halt_part`, `Stop_halt_unverified` in Flowchart 7.2) (F-170); added initial Stage 1 worker failure decision branches to both Flowcharts 7.1 and 7.2 for solo and multi-participant candidate/evidence generation (F-171).
2. **State & Recovery Integrity**: Added unresumed terminal exit transition `Interrupted --> [*]: Unresumed Interrupted Run (Exit 1)` in State Diagram 7.3, and added `SIGINT`/`SIGTERM` interrupt and `aw specs flow cancel` transitions during `Dispatching` and `Finalizing` stages, as well as `Finalizing --> Failed: Validation / Promotion Error (Exit 2)` (F-172).
3. **Persistence Model & Naming Precision**: Harmonized Table 6.1 storage persistence rows for `RECONCILIATION_RECORD` and `SYNTHESIS_DRAFT` to include `<R>/reference/<YYYYMM>/ (finalize) or <R>/archive/<YYYYMM>/ (cancel)` post-lifecycle destinations matching Table 6.2 (F-173); disambiguated Table 6.2 Row 13 refinement assessment slug pattern to `<synth|reconcile>-review` to formally distinguish spec synthesis reviews from research reconciliation reviews (F-175).
4. **Protocol Parity & Closed Vocabularies**: Formalized the closed enum for `auto_advance` in Section 4.6 FR-20 as `("multi-model", "not-multi-model", "unresolved-findings", "none")` (F-174); aligned Table 3.4 research CLI exit code 1 categories with complete failure modes (`findings/unverified/cap` and `blocked/unverified/findings`) (F-178); added explicit explanatory note regarding the stream item count in Section 13.4 for thorough mode executions (F-179).
5. **Context Chunking & NN Capacity Rigor**: Clarified Section 6.3 NN capacity formula to explicitly define candidate record counts for heterogeneous split candidate sets versus worst-case homogeneous split sets (F-176); specified in Section 7.4 that hierarchical synthesis Pass 2 intermediate section drafts stage strictly in brief companion directory `<C>/synth-sections/section-<k>.md` without research root pollution or NN sequence consumption (F-177).
6. **Acceptance Test Coverage Expansion**: Updated `AT-42` and added acceptance tests `AT-77` (terminal sink routing verification), `AT-78` (hierarchical section companion staging verification), and `AT-79` (`auto_advance` closed enum validation), expanding test census to 79 tests (`AT-01`..`AT-79`) (F-180).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-170 | high | IN-SCOPE | Flowcharts 7.1 and 7.2 | Flowchart 7.1 lines 865-874, Flowchart 7.2 lines 950-958, FR-28, prompt `jsgs0f` Section 2 | Flowcharts 7.1 and 7.2 routed all worker failure, partial roster, unverified citation, and cap halts into a single terminal sink node labeled `Exit 1 in state capped_with_findings`, conflating distinct exit states and mislabeling failed and partial runs. | Low | fixed | Separated terminal sink nodes into dedicated sinks: `Q_halt_cap`, `Q_halt_fail`, and `Q_halt_part` in Flowchart 7.1; and `Stop_halt_cap`, `Stop_halt_fail`, `Stop_halt_part`, and `Stop_halt_unverified` in Flowchart 7.2. |
| F-171 | high | IN-SCOPE | Flowcharts 7.1 and 7.2 | Flowchart 7.1 lines 778, 795-799, Flowchart 7.2 lines 887, 906-910, State Diagram 7.3 lines 975-977 | Initial candidate generation turns in Flowchart 7.1 (`E_solo`, `E1`..`E3`) and initial evidence collection turns in Flowchart 7.2 (`Single_Evidence`, `RE1`..`RE3`) lacked worker failure exit paths, representing worker failure handling only inside refinement loops. | Low | fixed | Added worker failure branches out of Stage 1 generation turns to `Halt_solo_fail`/`RStop_solo_fail` for solo runs and `FailDec`/`RFailDec` decision diamonds for multi-participant runs. |
| F-172 | medium | IN-SCOPE | State Diagram 7.3 | State Diagram 7.3 lines 986-987, 1029-1035, 1060-1067, FR-33 | State Diagram 7.3 lacked an unresumed terminal exit transition for `Interrupted` (`Interrupted --> [*]`), and omitted `SIGINT`/`SIGTERM` interrupt and `cancel` transitions during `Dispatching` and `Finalizing` stages. | Low | fixed | Added `Interrupted --> [*]: Unresumed Interrupted Run (Exit 1)`, added `Interrupted` and `Cancelled` transitions from `Dispatching` and `Finalizing`, and added `Finalizing --> Failed: Validation / Promotion Error (Exit 2)`. |
| F-173 | medium | IN-SCOPE | Table 6.1 (Entity Persistence) | Table 6.1 lines 603-605, Table 6.2 lines 631-633, FR-33 | Table 6.1 storage column for `RECONCILIATION_RECORD` and `SYNTHESIS_DRAFT` omitted destination storage paths after finalize or cancel, unlike candidate and assessment rows. | Low | fixed | Updated Table 6.1 storage column for `RECONCILIATION_RECORD` and `SYNTHESIS_DRAFT` to explicitly include `<R>/reference/<YYYYMM>/ (finalize) or <R>/archive/<YYYYMM>/ (cancel)`. |
| F-174 | medium | IN-SCOPE | FR-20, Section 13.4 | FR-20 line 362, Sec 13.4 line 1380, `agent_schema.py` | FR-20 specified `auto_advance: "not-multi-model"` for solo runs and Section 13.4 used `"multi-model"`, but the complete closed enum for `auto_advance` was not formally defined in the normative requirement text. | Low | fixed | Formally defined the closed enum for `auto_advance` in FR-20 as `("multi-model", "not-multi-model", "unresolved-findings", "none")`. |
| F-175 | low | IN-SCOPE | Table 6.2 (Artifact Matrix) | Table 6.2 line 633, Worked Inventory 4 line 760 | Table 6.2 Row 13 assigned pattern `YYYYMMDD-<setid>-NN-<id6>-<slug>-synth-review.<ace>.<model>.assessment.md` to both synthesis and reconciliation findings, obscuring the distinction between spec synthesis review and research reconciliation review. | Low | fixed | Disambiguated Table 6.2 Row 13 slug pattern to `YYYYMMDD-<setid>-NN-<id6>-<slug>-<synth|reconcile>-review.<ace>.<model>.assessment.md`, matching `-synth-review` for specs and `-reconcile-review` for research. |
| F-176 | low | IN-SCOPE | Section 6.3 (NN Capacity) | Sec 6.3 line 653, Worked Inventory 1 line 742 | Section 6.3 stated general formula `N*(1 + P_max)` which assumed all candidates split, conflicting with the heterogeneous candidate roster example where only 1 of 3 candidates split into parts. | Low | fixed | Clarified Section 6.3 NN capacity calculation to explicitly specify candidate record formulas for both homogeneous split rosters and heterogeneous rosters `(N - S) + \sum (1 + P_s)`. |
| F-177 | low | IN-SCOPE | Section 7.4 (Synthesizer Context) | Sec 7.4 lines 1067-1073, FR-34, Sec 3.3 | Section 7.4 item 5 specified partitioned section drafting turns during hierarchical synthesis (Pass 2) but omitted the staging location for intermediate unstitched section drafts prior to assembly. | Low | fixed | Specified that Pass 2 intermediate section drafts stage in companion directory `<C>/synth-sections/section-<k>.md` without polluting the research root or consuming set NN orders. |
| F-178 | low | IN-SCOPE | Table 3.4 (CLI Matrix) | Table 3.4 lines 205-208, FR-11, FR-18B, AT-42 | Table 3.4 research CLI exit code 1 columns listed `findings/unverified` and `blocked/unverified`, omitting `cap` and `findings` failure modes when runs halt at caps with unresolved findings. | Low | fixed | Harmonized Table 3.4 exit code 1 categories to `findings/unverified/cap` for `new`/`reconcile`/`resume` and `blocked/unverified/findings` for `finalize`. |
| F-179 | low | IN-SCOPE | Section 13.4 (Machine Protocol) | Sec 13.4 line 1380, Sec 13.2 | Section 13.4 JSONL summary record listed `"total": 5` after showing 5 stream items in an excerpt, creating potential confusion over stream item counts in thorough runs with refinement passes. | Low | fixed | Added an explicit explanatory note in Section 13.4 clarifying that the 5 items represent an illustrative milestone excerpt from a thorough execution stream. |
| F-180 | low | IN-SCOPE | Section 9 (Acceptance Tests) | Sec 9 lines 1099-1196, AT-42, AT-76 | Acceptance test matrix lacked explicit tests verifying terminal sink state separation, hierarchical section companion staging, and `auto_advance` closed enum validation. | Low | fixed | Updated `AT-42` to cite `blocked/unverified/findings` and added acceptance tests `AT-77`, `AT-78`, and `AT-79`, expanding total acceptance tests to 79. |

### Open questions

- OQ-I22-1 (nonblocking, preserved from iteration 22, recorded in Section 10.5): how a high-effort Gemini 3.8 Flash configuration is selected on `agy`. Recommendation: default effort (`gemini38flash`) for Phase 1, reporting `variant-not-applied` per FR-37.

### Validation performed

- `aw specs check` on subject spec: `all specs conform. 1 specs checked.`
- Requirement and acceptance test inventory: 42 FRs (`FR-01`..`FR-37`), 79 ATs (`AT-01`..`AT-79`), 0 uncovered FRs.
- Diagram structural review: all 4 Mermaid diagrams (ERD 6.1, Spec Flow 7.1, Research Flow 7.2, State Diagram 7.3) checked for syntax integrity, node naming, and closed transition paths.
- Local leak sanitizer: `python3 -m agent_workflows check-local-leaks . --agent` returned exit code 0 (`clean`).
- Prose style check: verified zero em dashes (U+2014) and zero en dashes (U+2013) in user-facing and spec prose.
- Path and SSH safety check: verified zero file URI schemes and zero absolute machine home directory paths.
- Walkthroughs verified: one-participant quick run (Inventory 2, Transcript 13.1); three-model thorough run (Inventory 1, Transcript 13.2); research run with conflicting sources (Inventory 4, AT-09, AT-33); partial roster failure (FR-30, State 7.3, AT-20, AT-65); cap with findings (Inventory 3, Transcript 13.3, AT-06, AT-52); resume after input/profile change (FR-31, AT-21); terminal sink state distinction (AT-77); and cancellation cleanup across active states (FR-33, State 7.3, AT-76).

### Stopping result

Material changes made; rerun warranted. The workflow diagrams, state transitions, persistence model destinations, closed protocol vocabularies, context staging, and acceptance tests were hardened in this iteration. Future iterations should continue adversarial review of core CLI parameter parsing and Phase 1 test coverage boundaries.
