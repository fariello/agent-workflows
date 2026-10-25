# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 13)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: agy/gemini-3.8-flash-high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED

## Round 13

All claims verified against repository baseline `517a22a58db03d4638fa4ff60068f1d021b211c6` (working tree clean).

This thirteenth adversarial review performed an exhaustive verification pass across candidate specification `18hh1u` (`.aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md`, Set `specflow`).

Twelve material defects, schema boundaries, and actionable precision gaps were identified and resolved (F-68 through F-79). All corrections have been applied directly to candidate spec `18hh1u`.

### Scope and Verification Summary

1. **Decision D177 Middle Segment Positional Parsing Regex Error (F-68)**: Fixed the proposed D177 extension regex in Section 6.2. The candidate regex parsed from left to right, erroneously capturing single middle segments (such as `.reconciliation.spec.md` or `.opus55high.research-report.md`) as `ace` rather than `model`. Corrected to positional right-to-left regex `(?:\.(?P<ace>[a-z0-9-]+)\.(?P<model>[a-z0-9-]+)|\.(?P<model_only>[a-z0-9-]+))?\.(?P<type>...)\.md\Z` ensuring 1 middle segment maps to `model`, strictly conforming to Decision D177.
2. **CLI Investigation Mode Flag Collision with `--mode` (F-69)**: Disambiguated research flow mode selection by designating the inquiry topology flag as `--investigation-mode parallel|decomposed` (default: `parallel`) in Table 3.4, FR-18A, and AT-34, resolving the conflict where AT-34 passed `--mode parallel` while Table 3.4 defined `--mode quick|thorough`.
3. **State Diagram Terminal Transitions & Partial Roster Failures (F-70)**: Added missing `PartialRoster` (Exit 1) state and terminal transitions `PartialRoster --> [*]` and `Failed --> [*]` in Section 7.3 State Diagram-v2. Added transitions from `CandidateRefining` to `PartialRoster` (without `--allow-partial-roster`) and `Synthesizing` (with `--allow-partial-roster`), as well as to `Failed` when zero candidates survive, completing FR-30 state alignment.
4. **Research Flowchart Branches for `--prepare-only` and Single-Participant (F-71)**: Added `--prepare-only` decision point (`DP_res{--prepare-only?}`) and single-participant branch (`DR_res{Roster Size?}`) to Section 7.2 Flowchart, aligning with Table 3.4 and Section 4.3.1 turn bounds.
5. **Hardcoded Model String in Table 6.2 Row "1. Synth Prompt" (F-72)**: Replaced hardcoded `opencode.opus55high` in row "1. Synth Prompt" with generic pattern `YYYYMMDD-<setid>-05-<id6>-synth.<ace>.<model>.prompt.md`, restoring participant independence and configurable roster alignment. Also updated Verification Prompt pattern to `verify[.<ace>].<model>`.
6. **Missing CLI Options in Table 3.4 (F-73)**: Synchronized CLI argument tables with normative requirements, adding `--budget` and `--turn-timeout` to `aw specs flow new` and `aw research flow new`, adding `--slug` and `--set` to `aw specs flow from-spec`, and adding `--allow-unresolved-findings` to `aw specs flow finalize`.
7. **Runner Profiles Schema Boundary for Antigravity (`agy`) (F-74)**: Clarified in Section 5.2, Section 5.3, and Section 11 Phase 1 that profile `"gem"` in `runner-profiles.json` must omit `variant` because `RUNNER_REGISTRY["agy"].supports_variant` is False (which triggers `ProfileSchemaError` upon parsing). Specified that `flow_config.py` strips variant prior to invoking `runner_profiles.resolve()`, injecting variant `high` into prompt instructions as `variant_instruction`. Also clarified that flow roles (`synthesizer`, `reviewer`, `research-verifier`) belong to `flow-preferences.json` and must not be placed in `runner-profiles.json`'s closed `ROLE_NAMES` map.
8. **Built-In Fallback Defaults Specification (F-75)**: Added subsection 5.1.1 explicitly defining the hardcoded fallback defaults (mode `thorough`, caps 3/2, budget 40, timeout 600s, and fallback roster resolution via `default_runner`) when neither `.aw/config/flow.json` nor user flow preferences exist.
9. **Markdown Quote Syntax Repairs in Table 3.4 (F-76)**: Fixed unmatched backtick/apostrophe syntax in Table 3.4 for `merge` and `reconcile` commands (`` `<candidate-paths...>' `` -> `` `<candidate-paths...>` ``).
10. **Finalize Contract on Capped Runs with Unresolved Findings (F-77)**: Formalized the contract in FR-11, FR-20, and Table 3.4: `finalize` unconditionally refuses to promote a spec with unresolved critical or major findings to `to-review/` (exit 1). If `--allow-unresolved-findings` is supplied, the spec is finalized to `specs/draft/` with status `draft` (exit 1), documenting remaining issues in workflow history.
11. **Comprehensive Model Normalizations in Research Models TOML (F-78)**: Detailed the complete normalization mappings in Section 11 Phase 1 for Opus 5.5 and GPT-6.1 Sol families to guarantee robust model token resolution.
12. **Acceptance Test Matrix Traceability Expansion (F-79)**: Added tests `AT-35` (turn timeout enforcement) and `AT-36` (finalize on capped run with `--allow-unresolved-findings`), expanding verified scope to `AT-01..AT-36`.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-68 | HIGH | IN-SCOPE | Decision D177 Positional Parsing Regex Error | Sec 6.2 | Candidate regex parsed left-to-right, binding single middle segment to `ace` instead of `model` (`.reconciliation.spec.md` -> `ace="reconciliation", model=None`). | Low | FIXED | Replaced with right-to-left regex binding single middle segment to `model`, strictly conforming to D177. |
| F-69 | HIGH | IN-SCOPE | CLI Investigation Mode Flag Collision | Sec 3.4; Sec 4.5; Sec 9 | AT-34 invoked `--mode parallel` vs `--mode decomposed`, colliding with Table 3.4 `--mode quick\|thorough`. | Low | FIXED | Designated investigation topology flag as `--investigation-mode parallel\|decomposed`, keeping `--mode quick\|thorough` orthogonal. |
| F-70 | HIGH | IN-SCOPE | State Diagram Terminal Transitions & Worker Failure | Sec 7.3 | Diagram 7.3 lacked transitions for permanent worker failure (FR-30) and lacked terminal `[*]` transitions from `Failed` and `PartialRoster`. | Low | FIXED | Added `PartialRoster` state and terminal transitions `PartialRoster --> [*]` and `Failed --> [*]`, aligning with FR-30. |
| F-71 | MEDIUM | IN-SCOPE | Research Flowchart Missing Branches | Sec 7.2 | Diagram 7.2 omitted `--prepare-only` decision point and single-participant routing. | Low | FIXED | Added `--prepare-only` decision point and N=1 single-report branch to Flowchart 7.2. |
| F-72 | MEDIUM | IN-SCOPE | Table 6.2 Hardcoded Synthesis Prompt Pattern | Sec 6.2 | Table 6.2 hardcoded `opencode.opus55high` in row "1. Synth Prompt" Target Filename Pattern. | Low | FIXED | Replaced with generic pattern `YYYYMMDD-<setid>-05-<id6>-synth.<ace>.<model>.prompt.md`. |
| F-73 | MEDIUM | IN-SCOPE | Missing CLI Options in Table 3.4 | Sec 3.4 | Table 3.4 omitted `--budget`, `--turn-timeout`, `--slug`, `--set`, and `--allow-unresolved-findings`. | Low | FIXED | Added missing options to Table 3.4 across `new`, `from-spec`, `finalize`, and research commands. |
| F-74 | MEDIUM | IN-SCOPE | Runner Profiles Variant Schema Boundary for `agy` | Sec 5.2; Sec 5.3; Sec 11 | `RUNNER_REGISTRY["agy"].supports_variant` is False; storing `variant` in profile `"gem"` causes `ProfileSchemaError`. | Low | FIXED | Clarified that profile `"gem"` in `runner-profiles.json` omits `variant`, and `flow_config.py` strips variant before calling `resolve()`. |
| F-75 | MEDIUM | IN-SCOPE | Specification of Built-In Fallback Defaults | Sec 5.1 | Section 5.1 cited 4-tier precedence ending in `Built-In Defaults` but never defined the hardcoded fallback values. | Low | FIXED | Added subsection 5.1.1 detailing fallback limits, default runner resolution, and fallback single-participant roster. |
| F-76 | LOW | IN-SCOPE | Markdown Code Syntax Typos in Table 3.4 | Sec 3.4 | Command arguments for `merge` and `reconcile` contained unmatched quotes: `` `<candidate-paths...>' ``. | Low | FIXED | Corrected quotes to standard markdown backticks `` `<candidate-paths...>` `` and `` `<report-paths...>` ``. |
| F-77 | LOW | IN-SCOPE | Finalize Contract on Capped Runs with Findings | Sec 4.3; Sec 4.6; Sec 3.4 | Finalize behavior when caps are reached with unresolved critical/major findings was under-specified. | Low | FIXED | Formalized refusal of `to-review/` advancement, requiring `--allow-unresolved-findings` to place in `draft/` with status `draft` (exit 1). |
| F-78 | LOW | IN-SCOPE | Comprehensive Research Models Normalization | Sec 11 Phase 1 | Section 11 listed only two aliases; other common model variants would still produce warnings. | Low | FIXED | Detailed full normalization mapping sets for Opus 5.5 and GPT-6.1 Sol families in Section 11 Phase 1. |
| F-79 | LOW | IN-SCOPE | Acceptance Test Matrix Traceability Expansion | Sec 9; Sec 12.2 | Gaps existed for `--turn-timeout` enforcement and `finalize` on capped runs with `--allow-unresolved-findings`. | Low | FIXED | Added acceptance tests `AT-35` and `AT-36`; updated audited scope census to `AT-01..AT-36`. |
