# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 11)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: agy/gemini-3.8-flash-high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED

## Round 11

All claims verified against repository baseline `47bd8f9e94ac369121fdd93a51596f629a841ae6` (working tree clean).

This eleventh adversarial review performed an exhaustive verification pass across candidate specification `18hh1u` (`.aw/records/specs/draft/20261024-specflow-01-18hh1u-spec-research-synthesis.spec.md`, Set `specflow`).

Ten material defects and actionable precision gaps were identified and resolved (F-47 through F-56). All corrections have been applied directly to candidate spec `18hh1u`.

### Scope and Verification Summary

1. **Intermediate Candidate Validator Isolation**: Identified conflict between `specs.py:148` recursive `rglob("*.md")` walk and intermediate candidate staging under `.aw/records/specs/draft/intermediate/<setid>/`. Reconciled by requiring `_spec_files()` and `attention.py` to filter out `intermediate/` directories, added `## Workflow history` to the candidate schema, and documented maintainer alternative DL-16 (OQ-1) where candidates live in the research tree.
2. **Multi-Model Auto-Advance Ruling Enforcement (DL-17 / OQ-2)**: Corrected unconditional advancement of single-participant and single-model runs to `to-review/`, aligning strictly with maintainer decision DL-17 where single-participant, single-model, or single-surviving-candidate runs finalize to `draft/` with status `draft` and next-action `aw specs set to-review <id6>`.
3. **Missing `from-spec` Functional Requirement and Acceptance Test**: Added normative requirement `FR-35` and acceptance test `AT-25` defining `from-spec` baseline capture, setid handling, and `- Supersedes: <id6>` front-matter lineage.
4. **Research Tree Directory Alignment**: Fixed phantom `research/todo/` and `research/active/` subdirectory references across tables and text, aligning with the canonical flat hot root `.aw/records/research/` and cold weekly shards in `research_contract.py`.
5. **Prompt Injection Defense and Data Delimiters**: Added normative requirement `FR-36` and acceptance test `AT-26` defining per-run random delimiter fencing (`<<<SYNTH-DATA-...>>>`) and prompt instructions treating enclosed content strictly as non-executable data.
6. **Research Flow Execution Bounds and Verifier Accounting**: Expanded Section 4.3.1 with a closed execution bounds formula for research flows and documented single-pass `research-verifier` LLM turn accounting.
7. **Claude Opus 5.5 Model String Accuracy**: Corrected legacy `"anthropic/claude-3-opus"` citations in Section 5.2 and Section 5.3 to `"anthropic/claude-opus-5-5"`.
8. **Cancellation CLI Exit Code Consistency**: Clarified that CLI command `aw specs flow cancel` exits 0 on clean cancellation (exit 1 if not active), while signal-interrupted background runs checkpoint with exit 1.
9. **Research CLI Subcommand Module Placement**: Corrected Section 11 to place research CLI verbs in `agent_workflows/research_cmd.py` rather than `specs.py`.
10. **Prepare-Only Prompt Staging Phasing**: Clarified in FR-26 and Section 11 that `--prepare-only` renders the frozen brief and initial Stage 1 generation prompts, while subsequent prompts are compiled just-in-time during execution.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-47 | HIGH | IN-SCOPE | Spec Intermediate Staging & Validator Conflict | Sec 3.3; Table 2.2; Sec 6.3 | Candidate specs staged in `specs/draft/intermediate/` are scanned by `specs.py:148` recursive `rglob("*.md")`, failing `validate_spec()` on missing history and cluttering `aw attention`. | Low | FIXED | Required `_spec_files()` and `attention.py` to filter `intermediate/`, added `## Workflow history` to intermediate schema, and cited maintainer alternative DL-16. |
| F-48 | HIGH | IN-SCOPE | Maintainer Auto-Advance Ruling (DL-17) | FR-06; FR-20; Table 3.4; Sec 6.4; Sec 13.1 | Spec auto-advanced single-participant runs to `to-review`, contradicting maintainer decision DL-17 requiring multi-model synthesis to auto-advance. | Low | FIXED | Updated FR-20, Table 3.4, Worked Inventory 2, and Transcript 13.1 so solo/single-model runs finalize to `draft` and output `aw specs set to-review <id6>`. |
| F-49 | HIGH | IN-SCOPE | Missing `from-spec` Contract | Table 3.4; Sec 4; Sec 9; Sec 11 | `aw specs flow from-spec` was listed in CLI tables but omitted from functional requirements and acceptance tests. | Low | FIXED | Added FR-35 (`from-spec` Successor Flow Contract) and AT-25 to spec and test matrices. |
| F-50 | MEDIUM | IN-SCOPE | Research Tree Directory Alignment | Table 3.4; Table 6.1; Table 6.2; Sec 4.5 | Spec cited non-existent `.aw/records/research/todo/` and `active/` subdirectories. Canonical hot root is flat `.aw/records/research/`. | Low | FIXED | Updated all research paths to reference flat hot root `.aw/records/research/` and cold weekly shards. |
| F-51 | MEDIUM | IN-SCOPE | Prompt Injection Defense | FR-03; Sec 4; Sec 8.1 | Spec lacked delimiter fencing for untrusted briefs and candidate drafts interpolated into prompt templates. | Low | FIXED | Added FR-36 and AT-26 mandating random per-run delimiter fences (`<<<SYNTH-DATA-...>>>`) and data-only instructions. |
| F-52 | MEDIUM | IN-SCOPE | Research Flow Turn Bounds | Sec 4.3.1; Sec 5.2 | Execution bounds formula covered only spec flows, omitting research flow math and `research-verifier` dispatch accounting. | Low | FIXED | Added closed mathematical formula for research flows in Section 4.3.1. |
| F-53 | LOW | IN-SCOPE | Roster Model String Inaccuracy | Sec 5.2; Sec 5.3 | Section 5.2 cited `"anthropic/claude-3-opus"` (legacy 2024 model) instead of Claude Opus 5.5 (`"anthropic/claude-opus-5-5"`). | Low | FIXED | Updated model strings in Section 5.2 and Section 5.3 to `"anthropic/claude-opus-5-5"`. |
| F-54 | LOW | IN-SCOPE | Cancellation CLI Exit Parity | FR-33; Table 3.4; Sec 7.3 | Spec ambiguously noted exit 1 for cancellation in FR-33 and State Diagram 7.3 while Table 3.4 promised exit 0. | Low | FIXED | Clarified CLI `cancel` exits 0 on clean abort (exit 1 if not active); signal-interrupted executions checkpoint with exit 1. |
| F-55 | LOW | IN-SCOPE | Research CLI Module Placement | Sec 11 | Section 11 placed research flow CLI verbs under `specs.py` instead of `research_cmd.py`. | Low | FIXED | Corrected module citation to `agent_workflows/research_cmd.py`. |
| F-56 | LOW | IN-SCOPE | Prepare-Only Phasing Precision | FR-26; Sec 11 | FR-26 did not distinguish Stage 1 generation prompts (staged in prepare-only) from dependent Stage 2-4 prompts rendered dynamically. | Low | FIXED | Clarified in FR-26 and Section 11 that prepare-only stages frozen brief and initial generation prompts. |
