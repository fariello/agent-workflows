# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 23)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-25
- Reviewer: agy/gemini38flashhigh
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED
- Audited-Scope: [FR-01..FR-37, AT-01..AT-76, Decisions 01..14, Sections 1..13, 4 Mermaid diagrams, Flowcharts 7.1 and 7.2, State Diagram 7.3, Table 3.4, Table 6.1, Table 6.2, Worked Inventories 1..4]

This is a design-refinement record produced by prompt `jsgs0f` (refinement prompt). It is not a `/spec-review` attestation and grants no approval.

## Round 23

Baseline: subject file at commit `87f0de31e` on `main` (commit incorporating iteration 22 changes from review record `2q7ppl`). Repository facts and contracts were verified against source on that revision in an isolated git worktree (`.aw/worktrees/refine-18hh1u-iter23`). Reviewer: agy, Google Gemini 3.8 Flash High; identity class asserted by runtime environment.

### Maintainer input during this iteration

No new maintainer rulings were required during this iteration. All 11 findings were resolved deterministically from existing repository contracts, maintainer rulings (DL-16, DL-17), Decision D177, and internal consistency within spec `18hh1u`.

### Scope and verification summary

1. **Acceptance Test Precision & Pre-Dispatch Capacity**: Corrected `AT-30` to test companion prompt path `<C>/prompts/<stage>-<slot>-a<attempt>.prompt.txt` with digests in `<C>/run.json` instead of expecting a prompt-tree record (F-159); corrected `AT-37` pre-dispatch NN capacity check refusal exit code to 2 aligning with Section 6.3 line 647, State Diagram 7.3, and `AT-72` (F-166); updated `AT-67` to cite `ASSESSMENT_RECORD` and verify 11-entity total bijection with Table 6.1 (F-162).
2. **Workflow Ordering and Failure Recovery**: Re-sequenced Flowchart 7.2 to execute Candidate Research Refinement (Stage 2) before Citation Cross-Verification (Stage 3) and Reconciliation (Stages 4 and 5), matching Section 4.3.1 lines 292-298 and FR-18C (F-160); added single-participant worker failure branch `G_solo -- Worker Failed --> Halt_solo_fail[Halt: Exit 1 in state failed]` in Flowchart 7.1 (F-161); added `Cancelled: aw specs flow cancel` transitions from non-terminal stopping states `CappedHalted`, `BudgetExhausted`, `PartialRoster`, and `BlockedFindings` in State Diagram 7.3 (F-163).
3. **ERD & Persistence Model**: Added polymorphic `acts as` relationships in ERD 6.1 from `CANDIDATE_RECORD`, `SYNTHESIS_DRAFT`, and `RECONCILIATION_RECORD` to `SUBJECT_RECORD` (F-162); added `SUBJECT_RECORD` persistence row to Table 6.1 (F-162).
4. **CLI & Placement Consistency**: Updated Table 3.4 `aw research flow reconcile` to document that the live draft body is maintained in `<C>/reconciliation.md` with front matter only until finalize (F-164); added explicit setid selector resolution rules in Section 6.3 distinguishing mutating verbs from read-only verbs (F-165); clarified thorough mode execution with reconciliation refinement assessment order 08/09 in Worked Inventory 4 (F-167); reordered Decisions 13 and 14 in Section 10.4 (F-168); added `archive/<YYYYMM>/ (cancel)` destination to Table 6.2 rows 4 through 12 per FR-33 (F-169).
5. **Requirement Inventory**: Verified all 42 functional requirements (`FR-01`..`FR-37`) and all 76 acceptance tests (`AT-01`..`AT-76`). 0 uncovered functional requirements.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-159 | high | IN-SCOPE | Acceptance Tests (AT-30) | Sec 3.3 line 172, Table 6.2 line 616, FR-05, AT-45, prompt `jsgs0f` Section 2 | `AT-30` specified prompt filename matching `YYYYMMDD-<setid>-01-<id6>-gen.<ace>.<model>.prompt.md` with front matter, an un-migrated remnant from Iteration 21 contradicting DL-16 research-tree companion staging. | Low | fixed | Rewrote `AT-30` to verify companion prompt path `<C>/prompts/<stage>-<slot>-a<attempt>.prompt.txt` with SHA-256 digest recorded in `<C>/run.json` and zero prompt-tree pollution. |
| F-160 | high | IN-SCOPE | Flowchart 7.2 | Sec 4.3.1 lines 292-298, FR-18C | Flowchart 7.2 placed Citation Verification immediately after Evidence Gathering and before Candidate Refinement, with terminal halt if unverified, contradicting Stage 2 refinement before Stage 3 cross-verification in Sec 4.3.1. | Low | fixed | Re-sequenced Flowchart 7.2 to place Candidate Research Refinement first, followed by Citation Cross-Verification, and then Reconciliation Phase. Connected unverified halt branches to terminal sink. |
| F-161 | high | IN-SCOPE | Flowchart 7.1 | FR-30 line 264, State Diagram 7.3 line 958 | Flowchart 7.1 omitted worker failure paths for single-participant (`N = 1`) runs; `G_solo` had branches for Converged, Cap with Findings, and Retrying, but lacked Worker Failed to Exit 1 in state failed. | Low | fixed | Added `G_solo -- Worker Failed --> Halt_solo_fail[Halt: Exit 1 in state failed]` to Flowchart 7.1 and routed to terminal sink `Q_halt`. |
| F-162 | medium | IN-SCOPE | ERD 6.1, Table 6.1, AT-67 | Sec 6.1 line 585, Table 6.1 lines 593-605, AT-67 line 1167 | `AT-67` cited legacy `REVIEW_RECORD` and asserted total bijection between ERD 6.1 and Table 6.1, but Table 6.1 had 10 rows while ERD 6.1 had 11 entities (omitted `SUBJECT_RECORD`), and `SUBJECT_RECORD` lacked ERD relations. | Low | fixed | Added polymorphic relations `CANDIDATE_RECORD`, `SYNTHESIS_DRAFT`, and `RECONCILIATION_RECORD` `acts as` `SUBJECT_RECORD` in ERD 6.1; added `SUBJECT_RECORD` row in Table 6.1; updated `AT-67` to cite `ASSESSMENT_RECORD` and test 11-entity bijection. |
| F-163 | medium | IN-SCOPE | State Diagram 7.3 | Table 3.4 line 202, FR-33 line 272 | State Diagram 7.3 omitted `Cancelled: aw specs flow cancel` transitions from non-terminal stopping states (`CappedHalted`, `BudgetExhausted`, `PartialRoster`, `BlockedFindings`), despite FR-33 permitting cancellation of any non-terminal run. | Low | fixed | Added `Cancelled: aw specs flow cancel` transitions from `CappedHalted`, `BudgetExhausted`, `PartialRoster`, and `BlockedFindings` to `Cancelled` in State Diagram 7.3. |
| F-164 | medium | IN-SCOPE | Table 3.4 (`aw research flow reconcile`) | Sec 3.3 line 182, Table 6.2 line 628 | Table 3.4 line 207 stated `reconcile` drafts synthesis directly in `.aw/records/research/`, omitting the rule that live draft body is held in `<C>/reconciliation.md` with front matter only until finalize to avoid prematurely flipping attention to done. | Low | fixed | Updated Table 3.4 `aw research flow reconcile` description to explicitly specify front-matter-only record in research root with live body in `<C>/reconciliation.md`. |
| F-165 | medium | IN-SCOPE | Sec 6.3, Table 3.4 | Table 3.4 lines 201-203, lines 208-210, AT-47, AT-50 | Spec lacked explicit setid selector resolution rules distinguishing mutating commands (`resume`, `finalize`, `cancel`), which require resolving a single active run, from read commands (`status`), which resolve active or latest completed run. | Low | fixed | Added formal Setid selector resolution subsection in Section 6.3 specifying resolution precedence, ambiguity refusal (exit 2), active run targeting, and repository-wide default behavior. |
| F-166 | low | IN-SCOPE | Acceptance Tests (AT-37) | Sec 6.3 line 647, State Diagram 7.3 line 946, AT-72 line 1172 | `AT-37` stated reaching 99 NN capacity halts with exit code 1, whereas Section 6.3 line 647, Diagram 7.3 line 946, and `AT-72` explicitly mandate pre-dispatch refusal with exit code 2. | Low | fixed | Corrected `AT-37` to exit code 2 (`refusal: set '<setid>' cannot hold this run`) before dispatch, harmonizing with Section 6.3 and `AT-72`. |
| F-167 | low | IN-SCOPE | Sec 6.4 (Worked Inventory 4) | Sec 3.4 line 204, Table 6.2 line 628, Sec 6.4 line 748 | Section 6.4 Worked Inventory 4 omitted execution mode and caps, listing 08 as the reconciled report without clarifying that thorough mode with reconciliation refinement adds assessment record 08 and publishes the reconciled report as 09. | Low | fixed | Updated Worked Inventory 4 to specify thorough mode execution with reconciliation refinement assessment record 08 and final reconciled report 09 (or 08 in quick mode). |
| F-168 | low | IN-SCOPE | Sec 10.4 (Decision Log) | Sec 10.4 lines 1217-1219 | Decision Log inverted numerical order by listing Decision 14 ("Revision in Place") before Decision 13 ("Prompt Data Fencing and Injection Defense"). | Low | fixed | Reordered Decision 13 before Decision 14 in Section 10.4. |
| F-169 | low | IN-SCOPE | Table 6.2 (Artifact Matrix) | FR-33 line 272, Table 6.2 line 620 | Table 6.2 rows 4 to 12 omitted the `archive/<YYYYMM>/ (cancel)` destination under "Location after finalize", which was only noted on row 1, despite FR-33 specifying archive promotion on cancellation. | Low | fixed | Added `(finalize) or <R>/archive/<YYYYMM>/ (cancel)` lifecycle destination to Table 6.2 rows 4 through 12. |

### Open questions

- OQ-I22-1 (nonblocking, preserved from iteration 22, recorded in Section 10.5): how a high-effort Gemini 3.8 Flash configuration is selected on `agy`. Recommendation: default effort (`gemini38flash`) for Phase 1, reporting `variant-not-applied` per FR-37.

### Validation performed

- `aw specs check` on subject spec: `all specs conform. 1 specs checked.`
- Requirement and acceptance test inventory: 42 FRs (`FR-01`..`FR-37`), 76 ATs (`AT-01`..`AT-76`), 0 uncovered FRs.
- Diagram structural review: all 4 Mermaid diagrams (ERD 6.1, Spec Flow 7.1, Research Flow 7.2, State Diagram 7.3) checked for syntax integrity, node naming, and closed transition paths.
- Local leak sanitizer: `python3 -m agent_workflows check-local-leaks . --agent` returned exit code 0 (`clean`).
- Prose style check: verified zero em dashes (U+2014) and zero en dashes (U+2013) in user-facing and spec prose.
- Path and SSH safety check: verified zero file URI schemes and zero absolute machine home directory paths.
- Walkthroughs verified: one-participant quick run (Inventory 2, Transcript 13.1); three-model thorough run (Inventory 1, Transcript 13.2); research run with conflicting sources (Inventory 4, AT-09, AT-33); partial roster failure (FR-30, State 7.3, AT-20); cap with findings (Inventory 3, Transcript 13.3, AT-06); resume after input/profile change (FR-31, AT-21); and cancellation cleanup across active states (FR-33, State 7.3, AT-76).

### Stopping result

Material changes made; rerun warranted. The workflow diagrams, acceptance tests, ERD relationships, and selector resolution rules were corrected in this iteration. Future iterations should continue adversarial review of context window chunking and Phase 1 CLI implementation seams.
