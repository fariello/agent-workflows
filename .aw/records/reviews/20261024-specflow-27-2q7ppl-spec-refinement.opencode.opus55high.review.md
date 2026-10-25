# Review: Configurable Spec and Research Synthesis Design Refinement (Iteration 22)

- Subject-Id: 18hh1u
- Subject-Type: spec
- Reviewed-At: 2026-10-24
- Reviewer: opencode/opus55high
- Verdict: REVIEWED - MATERIAL CHANGES APPLIED
- Audited-Scope: [FR-01..FR-37, AT-01..AT-76, Decisions 01..14, Sections 1..13, 4 Mermaid diagrams]

This is a design-refinement record produced by prompt `jsgs0f` (refinement prompt). It is not a `/spec-review` attestation and grants no approval.

## Round 22

Baseline: subject file at `59f6d3137` (iteration 21), re-verified unchanged against `main` at `41e6f96f7` immediately before editing. Repository facts were checked against source on that revision. Model and reviewer: OpenCode, Claude Opus 5.5 (high); identity class echoed by the host, not independently confirmed.

### Maintainer input during this iteration

The candidate cited maintainer ruling DL-16 (OQ-1, recorded in sibling candidate `yfz5u9`, commit `47bd8f9e9`: candidates and findings live in the research tree) as confirmed, yet specified the opposite (spec subtree staging under `specs/draft/intermediate/<setid>/` plus `.review.md` findings). The maintainer was asked whether the ruling binds this candidate and answered yes (research tree). F-145 applies that answer.

### Scope and verification summary

1. Placement and naming (F-145, F-146, F-147, F-148, F-149) were rebuilt on the research tree: Sections 1.4, 1.6, 2.2, 3.3, 3.4, FR-05, FR-07, FR-13, FR-19, FR-22 to FR-26, FR-33, 6.1 to 6.4, 7.1 to 7.4, 9, 10, 11, 12, 13.
2. Machine protocol and identity (F-150, F-151, F-152, F-153) were checked against `agent_schema.validate_agent_record`, `research_contract.normalize_model`, and `RUNNER_REGISTRY`.
3. CLI precision (F-154, F-155), ERD (F-156), and resume (F-157, F-158) were corrected.
4. Requirement inventory: baseline FR-01..FR-36 kept; FR-22, FR-23, FR-24 rewritten (same obligation: isolate intermediates and keep work visible, now by research-tree records); FR-37 added (no silent substitution, a brief obligation). Baseline AT-01..AT-68 kept; AT-12, AT-13, AT-45, AT-49, AT-60, AT-63, AT-67 rewritten to the new placement; AT-69..AT-76 added. Decisions 04 and 05 marked superseded by Decision 12; Decision 14 added. No obligation was dropped.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|---|---|---|---|---|---|---|---|---|
| F-145 | blocker | IN-SCOPE | Sec 3.3, FR-22..FR-24, 6.2, Decision 12 | `yfz5u9` OQ-1 and DL-16 (commit `47bd8f9e9`); maintainer answer this iteration; `specs._spec_files` rglob; `review_findings.SUBJECT_TYPES = ("ipd","spec")` gives `REV-M102` for `research` (observed by calling `parse_review_text`) | The candidate cited a maintainer ruling as decided and specified the opposite design, which also needed new scanner exceptions in `specs.py` and `attention.py` and a new review subject type. | Medium | fixed | All intermediates are research-tree records of existing kinds (`research-prompt`, `source-draft`, `research-report`, `assessment`, `reconciliation-report`) created by `aw research new` and moved by `aw research promote`; rendered prompts are brief companion files. Rejected alternatives recorded. |
| F-146 | high | IN-SCOPE | FR-23, FR-24, Sec 3.3 | `research_index.derive_pipeline_positions` (synthesized when any `SYNTHESIS_KINDS` member has a body); `attention.py` maps statusless prompts through `_PROMPT_PIPELINE_MAP`; `.aw/.gitignore` ignores `records/runs/` | The attention design relied on a bespoke rollup and a banner, and the banner read only a gitignored ledger. A matrix with a body would mark a live run done. | Low | fixed | Visibility uses the existing pipeline position; the matrix and reconciled report carry an empty body until finalize; the footer line is documented as local only. AT-13 rewritten to observe the four classes. |
| F-147 | high | IN-SCOPE | Table 3.4 `--set` default, Sec 6.3 | `config.validate_setid_length_for_authoring` (refuse above 24, warn above 14); research singleton default from slug | Every command defaulted `--set` to the shared `specflow`, so unrelated runs would share an order space, a lock, and a pipeline position. The 14-character limit was stated as a hard refusal, which is not the repository rule. | Low | fixed | Default setid derived from the slug; live-run lock refuses a second run on one set (AT-71); length rule restated from source. |
| F-148 | high | IN-SCOPE | Sec 6.3 NN rules, 6.4 inventories | Inventory 1 used NN `10`, `12` for revisions and `80`..`82` for synthesis with a slot-stride formula; owner verbs allocate the next free order | NN encoded stage, participant, and iteration; revisions consumed orders; the stride formula overlapped for N > 4 and the 99 check fired mid-run. | Low | fixed | NN is publish order allocated by the owner verb; revisions edit in place (`revision` key, prior body in companion); a preview capacity check refuses before any write (AT-72, AT-73). Inventories recomputed and checked: netmesh orders 00..12 contiguous. |
| F-149 | medium | IN-SCOPE | Sec 2.2, 6.2, 9, 13 | `artifact_core.shard_for_date` and `SHARD_DIR_RE` produce monthly `YYYYMM`; weekly names are legacy read-only; `ls .aw/records/research/reference` shows `202607`..`202610` | 19 occurrences of `reference/<YYYYMM-Www>/` and one `202610-W43` described a shard format the tooling no longer writes. | Low | fixed | All replaced with `<YYYYMM>` and `202610`. |
| F-150 | high | IN-SCOPE | FR-20, FR-28, 13.4 | `agent_schema.VALID_OUTCOMES`; `validate_agent_record` rejects `finalized-clean` (observed) | FR-20 required outcome `finalized-clean`, which the machine contract rejects; run states were not separated from outcomes. | Low | fixed | FR-20 emits `clean` plus `auto_advance`; FR-28 maps every halted state to a valid outcome and a separate `state` field; JSONL examples validated with zero errors (clean, capped, refusal); AT-75 added. |
| F-151 | high | IN-SCOPE | Sec 6.3 token normalization, Sec 11 | `normalize_model("gemini-3.8-flash-high")` returns `malformed model token` before consulting the table (observed); `.aw/config/research-models.toml` already holds `opus55high`, `gpt61solmedium` | The algorithm could invent unregistered tokens for filenames, and Section 11 proposed dotted normalization keys that are unreachable. | Low | fixed | Each slot carries a `token` validated at preview; unknown tokens refused naming `aw research add-model`; dotted keys forbidden; AT-60 rewritten to test refusal. |
| F-152 | high | IN-SCOPE | Sec 5.2, 5.3, FR-37 | `RUNNER_REGISTRY["agy"].supports_variant=False`; brief: requested settings must not be silently substituted | The `agy` slot injected the variant into prompt text and named the output `gemini38flashhigh`, presenting a substituted configuration as the requested one. | Low | fixed | FR-37 requires `variant-not-applied`, `applied-variant: none`, and a token describing what launched (`gemini38flash`). OQ-I22-1 records the open choice. AT-74 added. |
| F-153 | medium | IN-SCOPE | Sec 1.3, 5.2, 5.3, 13 | No provider catalog in this repository verifies `anthropic/claude-opus-5-5`, `google/gemini-3.8-flash`, or `openai/gpt-6.1`; brief: exact IDs must be verified | Provider model ids were stated as the launch arguments of a "fully supported" configuration. | Low | fixed | Ids marked unverified examples; model ids come from the user's profile; support evidence is `aw host capabilities` plus a probe; identity recorded as requested, observed, and identity class (FR-32). Built-in fallback no longer guesses a model from installed hosts. |
| F-154 | medium | IN-SCOPE | New Sec 3.5 | Brief: concise and explicit forms must be equivalent; profiles must not shadow commands | No rule made the shortest and explicit invocations equivalent; `<roster-spec>` was undefined, so a roster and a profile of one name were ambiguous. | Low | fixed | Preview prints the explicit form and records `resolved_argv`; roster spec grammar defined; ambiguous name refused (AT-69, AT-70). |
| F-155 | medium | IN-SCOPE | Table 3.4 finalize, merge, reconcile | FR-20 conditions | `finalize --status to-review` could request promotion that FR-20 forbids; `--synthesizer` defaulted to an undefined "roster verifier"; research `--destination archive` conflicted with finalize semantics. | Low | fixed | `--status to-review` refused unless FR-20 holds; defaults point to `roles.synthesizer`; `--destination` removed (cancel archives). |
| F-156 | medium | IN-SCOPE | Sec 6.1 ERD | Baseline ERD gave REVIEW_RECORD a mandatory exactly-one relation to each of CANDIDATE_ARTIFACT, SYNTHESIS_ARTIFACT, and RESEARCH_REPORT (one review requires all three); `FROZEN_BASELINE` keyed by commit; `ITERATION_FINDING` keyed by `finding_id` alone | Cardinalities required every review to critique a candidate, a synthesis, and a research report at once; keys were not unique across runs. | Low | fixed | ERD rebuilt on the research-record entities with a polymorphic subject, composite finding keys, and part and supersedes self-relations; mapped to Table 6.1. Rendered with mermaid-cli 12.0.0. |
| F-157 | medium | IN-SCOPE | FR-31, State 7.3 | Brief: configuration changes must be detected on resume | Resume checked brief and commit only; a profile or model change would mix old candidates with a new roster. | Low | fixed | FR-31 also compares a roster digest; State 7.3 adds the refusal transition. |
| F-158 | low | IN-SCOPE | 7.4, Decision 06 | Brief: do not accept invented provider context sizes | Character budgets read as model context ceilings. | Low | fixed | Restated as operator-configured prompt-size targets with recorded prompt sizes and a pre-dispatch refusal. |

### Open questions

- OQ-I22-1 (nonblocking, recorded in spec Section 10.5): how a high-effort Gemini 3.8 Flash configuration is selected on `agy`. Recommendation: default effort (`gemini38flash`) for Phase 1.

### Validation performed

- `aw specs check` on the subject: `all specs conform. 1 specs checked.`
- Mermaid: all 4 diagrams rendered to SVG with `@mermaid-js/mermaid-cli` 12.0.0, exit 0 each.
- Names: every research filename in Sections 6.4 and 13 parsed with `research_contract.parse_name`; one-facet names parse today; two-facet names parse only after removing the ACE, which is the documented parser extension. Kinds all in `KINDS`. Tokens `gemini38flash` and `reconciliation` recognized by the package vocabulary; `opus55high` and `gpt61solmedium` are recognized only with the repository layer (Section 11 proposes adding them to the package default).
- JSONL: `agent_schema.validate_agent_record` returned no errors for the clean summary, the capped summary, and the refusal result; it rejected `finalized-clean`, confirming F-150.
- `aw sanitize --agent`: exit 0, outcome `clean`.
- No dash characters (U+2013, U+2014) in the subject.
- Walks: one-participant quick run (Inventory 2, Transcript 13.1); three-model thorough run (Inventory 1, 13.2); research run with conflicting sources (Inventory 4, AT-09, AT-33); partial roster (FR-30, State 7.3, AT-20); cap with findings (Inventory 3, 13.3, AT-06); resume after input or profile change (FR-31, AT-21). Expected status at each gate is stated in those sections.
- Limits: no implementation exists, so no behavior was tested. Arithmetic in Section 4.3.1 was not changed this iteration and was re-read only.

### Stopping result

Material changes made; rerun warranted. Placement changed across most sections, so the next iteration should audit the new Sections 3.3 and 6.2 to 6.4 end to end.
