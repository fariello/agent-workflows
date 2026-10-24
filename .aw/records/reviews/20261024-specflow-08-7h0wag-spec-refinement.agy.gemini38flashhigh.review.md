# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 3)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: agy/gemini-3.8-flash-high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED

## Round 3

All claims verified against repository baseline `4ece875d8ae5af2ca33ee16da774b88051665c18` (working tree clean).

This third adversarial review conducted a comprehensive end-to-end integration pass over candidate specification `18hh1u`. It examined recovery idempotency across brief mutations, configuration error handling for missing runner profiles, acceptance test coverage completeness, CLI command symmetry between specs and research, and visual alignment between flow diagrams and turn arithmetic.

Six material improvements were identified and resolved (F-17 through F-22). All six have been applied directly to candidate spec `18hh1u`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| F-17 | MAJOR | IN-SCOPE | Recovery & Idempotency | Refinement prompt Section 3 Point 19: "Are configuration/input changes detected rather than silently mixed with old outputs?" | If an operator edits the input brief file between an interrupted flow and an `aw specs flow resume` invocation, the engine would resume from checkpointed candidates generated against the old brief, silently mixing inconsistent inputs with downstream synthesis. | Low | FIXED | Added FR-31 (Resume Baseline Verification Guard). Mandated that `resume` verify the input brief hash and git commit SHA against `FROZEN_BASELINE`. If a brief mutation is detected, execution is refused (exit 2) unless `--force-stale-resume` is passed. |
| F-18 | MAJOR | IN-SCOPE | Configuration Validation | Refinement prompt Section 3 Point 5: "Are... missing/dangling profile references, frozen run settings, and migrations fully defined? Is actual versus requested model identity recorded without an unsupported guarantee?" | The configuration resolver did not define behavior when a participant slot references a profile absent from `runner-profiles.json`. In addition, candidate artifact front matter lacked explicit distinction between requested model and actual resolved runner/model strings. | Low | FIXED | Added FR-32 (Dangling Profile Validation and Identity Recording). Mandated fail-fast validation (exit 2) at baseline freeze for unresolvable profile references. Required generated artifacts to record both `- Requested-Model:` and `- Resolved-Model:`. |
| F-19 | MEDIUM | IN-SCOPE | Acceptance Test Coverage | Refinement prompt Section 3 Point 23: "Every normative requirement needs stable identity... and observable acceptance criteria." | Acceptance tests in Section 9 stopped at AT-15, omitting test cases for requirements added during previous refinement rounds (FR-18C, FR-27, FR-28, FR-29, FR-30) and current requirements (FR-31, FR-32). | Low | FIXED | Added acceptance tests AT-16 through AT-22 to Table 9, establishing complete traceability for claim classification, truncation detection, machine protocol envelope, reviewer isolation, partial roster fallback, resume mutation refusal, and profile validation. |
| F-20 | LOW | IN-SCOPE | CLI Symmetry & Precision | Refinement prompt Section 3 Point 1; Section 11 Phase 1 | Section 11 Phase 1 specified `aw research flow [new|status|resume]`, but Section 3.4 Command Matrix included only `aw research flow new`, omitting the `status` and `resume` subcommands. | Low | FIXED | Added `aw research flow status` and `aw research flow resume` rows to Table 3.4 with complete argument definitions and exit code contracts. |
| F-21 | LOW | IN-SCOPE | Diagram Alignment | Refinement prompt Section 3 Point 24: "Inspect spec/research/recovery flows for... exact agreement with state/command tables." | The Candidate Refinement subgraph in Section 7.1 represented the refinement loop as a single opaque block, obscuring the critique turn (reviews tree) versus revision turn (draft/intermediate tree) breakdown established in FR-29 and Section 4.3.1. | Low | FIXED | Updated Section 7.1 Mermaid flowchart to show the 2-step iteration loop (`Adversarial Review Turn in reviews/` -> `Candidate Revision Turn in draft/intermediate/`) before the convergence gate. |
| F-22 | LOW | IN-SCOPE | Epistemic Precision & Determinism | Refinement prompt Section 3 Point 22: "Are replays described as auditable rather than bit-for-bit deterministic model results?" | The specification lacked an explicit disclaimer clarifying that while prompt artifacts and frozen git baselines provide full audit traceability, non-zero LLM sampling temperatures mean replays are auditable process replays rather than bit-for-bit identical outputs. | Low | FIXED | Added an explicit non-determinism clarification to Section 4.1 noting that prompt artifacts guarantee auditable process reproducibility rather than bit-for-bit token identity. |
