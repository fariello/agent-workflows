---
id: hesuzv
created: 20261106
set: specflow
order: 20
topic: [specflow, spec-synthesis]
model: 
kind: assessment
status: active
outcome: none-yet
summary: Topic-by-topic keep/alter/discard comparison of third candidate 1tx9t8 against the 53jbi5 Section 7 merge outline
consumed-by: []
---

# Comparison of third candidate `1tx9t8` against the merge outline of `53jbi5`

This record compares a third candidate specification against the merge plan that research record `53jbi5` already made for two other candidates. For each idea in the third candidate, it states whether the merged specification keeps it, alters it, or discards it. The reader is the author of the merged specification. That author has read `53jbi5` but has not read the third candidate.

The maintainer asked for this comparison on 2026-11-05 (`53jbi5` Q-7): compare `1tx9t8` topic by topic against the `53jbi5` Section 7 outline, then write the merged specification from all three candidates.

## 0. Labels and decision words

| Label | Meaning |
| --- | --- |
| C01 | Candidate spec `18hh1u` (`specflow-01`). |
| C02 | Candidate spec `1tx9t8` (`specflow-02`), `.aw/records/specs/draft/20261025-specflow-02-1tx9t8-synthesis-independent-candidate.codex.gpt-6-astra-medium.spec.md`, 684 lines. The file name says Codex with GPT-6 Astra Medium. The candidate states that this label is the maintainer's attribution, not a measured runtime identity (C02 section 1). Its supporting evidence record is `ear8qy`. |
| C03 | Candidate spec `yfz5u9` (`specflow-03`), the main source of the `53jbi5` outline. |
| Outline | The proposed structure of the merged specification in `53jbi5` Section 7, together with the per-topic decisions in `53jbi5` Section 4 and the entity model in `53jbi5` Section 5. |
| MS | Spec `4sd62s`, the artifact metadata store (status `approved`). |
| Maintainer answers | The `53jbi5` Section 8 answers recorded 2026-11-05: Q-1 one `aw synth` command; Q-2 the working spec record exists from the synthesis step; Q-3 `agy` profiles may store a variant and a bare model id; Q-4 run directories are `run-*` with a `queue`; Q-5 a research Set is `synthesized` only when a synthesis-kind member has status `reference`; Q-6 the new metadata fields go into a specflow plan after the MS cutover; Q-7 this comparison. |
| DL-16 | Maintainer ruling 2026-10-25: every intermediate artifact lives in the research tree. |
| DL-17 | Maintainer ruling 2026-10-25: finalize moves a spec to `to-review` automatically only after a synthesis across candidates from at least two distinct models; otherwise the spec stays `draft`. |
| dispatch | One launch of one model session for one stage (the `53jbi5` term; C02 calls it an "invocation" or "attempt"). |

Decision words follow `53jbi5`: `keep` (take the C02 item into the merged spec), `alter` (take it with the stated change), `discard` (leave it out), and `already covered` (the outline already has an equivalent, so C02 adds nothing). `needs maintainer decision` marks an item the repository cannot settle; Section 4 lists them.

## 1. Method and baseline

- Read in full: C02 (all 684 lines) and `53jbi5` Sections 0 to 8.
- Read in part: C03 requirements cited in the tables below, by requirement id; the generation prompt `443ltw` (the brief all three candidates answer); `ear8qy`.
- Repository state: HEAD `4f09df0c7` on 2026-11-06. The last commit touching `agent_workflows/` is `4bdbe1205`; no code changed between it and HEAD. C02 pins its own evidence to `933b94b74`.
- Identity: OpenCode, model `uri/its_direct/pt3-claude-opus-5.5-1m-us` as the host reports it; reasoning setting not observable from inside the session, so the record carries no model facet.
- Independence: in this session I put the `53jbi5` Section 8 questions to the maintainer and recorded the answers, so this comparison is not independent of the outline it is compared against.
- Every claim that a decision depends on was checked with a command. Section 5 lists the checks (V-01 to V-10). A claim I did not check says `not re-checked`.

## 2. Summary

1. C02 agrees with the outline on most architecture: one `aw synth` noun, the `oc` and `agy` hosts only, one synthesizer per run, profiles referenced rather than copied, no review or approval written by the workflow, and dispatches bounded by a hard counter.
2. C02 contradicts two maintainer rulings and must not be followed on them. (a) DL-17: C02 lets a one-participant run reach `to-review` (C02 section 9, D-08, A-08). (b) DL-16: C02 places candidates and revisions in `specs/draft/` and rendered prompts in the prompts tree (C02 8.2). The outline keeps the rulings.
3. C02's naming and identity design conflicts with the outline and with measured tool behavior. It gives every revision a new record and every rendered prompt a record, so its own worked inventory needs 60 records for one run (C02 8.3). It proposes a cross-tree order reservation and linked overflow Sets. The outline keeps revisions in place under one id6 and keeps prompts in the brief companion. Discard C02's allocation model.
4. C02 contributes nine ideas that the outline lacks. Section 3 marks them `keep` or `alter`:
   - a `--request-id` token that makes a repeated start return the same prepared run (T25-a);
   - an `unknown-outcome` state with explicit recovery verbs for a dispatch whose result is unknown (T25-b);
   - a publication journal with a commit point, so that an interrupted finalize recovers instead of leaving half-published records (T24-a);
   - a schema-versioned worker return envelope that binds each output to its dispatch and input digest (T42-a);
   - research evidence families, so that three reports citing one article count as one source (T23-a);
   - an explicit "inconclusive but supported" research outcome (T23-b);
   - a preview refusal when the dispatch ceiling cannot fund even the minimum work (T21-a);
   - an isolation label (`enforced` versus `instruction-only`) that the run records and the final record reports (T19-a);
   - a convention that marks fictional example ids in a spec so the dangling-citation checks skip them (T52-a).
5. Two items need the maintainer (Section 4). N-1: whether `--gates each` (pause after every candidate check) belongs in release 1. N-2: whether `agy` dispatches should run with `--sandbox` instead of `--dangerously-skip-permissions`.
6. C02's requirement and acceptance ids parse: 20 `R-` ids and 26 `A-` ids (V-01). Its acceptance ids use the prefix `A-`, the outline uses `AC-`. The merged spec uses `AC-`, so carried C02 tests are renumbered.

## 3. Per-topic decision tables

Topic ids `Tn` match the `53jbi5` alignment table (`53jbi5` Section 3). C02 section numbers are given as "C02 x.y".

### T1 to T8. Front matter, terms, summary, actors, goals, release boundary

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Summary and actors (C02 1) | already covered | The outline takes C03 1.1 to 1.3. C02's actor rule "neither can attest human approval" matches C03 1.3. | none | `53jbi5` T3 to T8 |
| Goals and non-goals (C02 1) | already covered | Same goals and non-goals as C03 1.4, 1.5. | none | `53jbi5` T6, T7 |
| Release one includes "previously adopted candidate inputs" and "prompt preparation without dispatch" (C02 1) | already covered | C03 R-04 (`--prepare-only`) and R-06 (`import`) cover both. | none | C03 R-04, R-06 |
| "A preferred but unsupported binding refuses dispatch; it never silently becomes OpenCode" (C02 1) | already covered | C03 R-16 and the outline's capability verdicts state the same refusal. | none | C03 R-16 |
| Native Codex dispatch deferred; prepare and import as the route for other ACEs (C02 1, D-10) | keep | Same as the outline's Codex deferral (`53jbi5` T8). C02 adds the explicit rule that the deferral is tolerable because prepare and import exist. | Add that sentence to the merged 1.6 reason table. | `53jbi5` T8; `RUNNER_REGISTRY` has `oc` and `agy` only |
| "All `aw synth` syntax below is PROPOSED" and the `EXISTING` labels (C02 1, 3.2) | already covered | C03 0 labels `[EXISTING]`, `[APPROVED-UNBUILT]`, `[PROPOSED]`, which the outline keeps. | none | `53jbi5` T2 |
| Attribution paragraph about the file name (C02 1, 8.4) | discard | It describes one candidate's provenance, not the feature. `53jbi5` T2 discards C03's equivalent "Candidate status" table for the same reason. | Move the fact that C02's facet is a maintainer-supplied label into the merged spec's provenance section. | `53jbi5` T2 |
| `## Workflow history` written by the owner verb (C02 front matter) | already covered | The outline forbids hand-written history (`53jbi5` T1). C02 itself only carries owner-written history. | none | `53jbi5` T1 |

### T9 to T11. Repository findings, reuse table, discrepancies

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Reuse table (C02 2) | already covered | Every row maps onto a C03 FND row or 2.2 row the outline keeps. C02 cites pinned links at `933b94b74`; the outline re-pins all links to the synthesis commit. | none | `53jbi5` T9, T10 |
| "Adapter metadata mentioning `codex exec` is not a registered runner profile" (C02 2) | already covered | C03 1.6 Codex row states the same, with measured `codex exec` flags. | none | C03 1.6 |
| "Retry helpers are not evidence that every driver uses them" (C02 2) | already covered | `53jbi5` T31 to T40 keeps C03's own state machine because `plan_retry` has no production callers. | none | `53jbi5` T31 to T40 |
| Documentation discrepancies (`ear8qy` "Documentation discrepancies observed": P5 stable spec path, the specs module docstring on approval, agent-protocol examples) | alter | They are real documentation defects, but not specflow requirements. | Do not put them in the merged spec. File them through `aw backlog new` if the maintainer wants them fixed; they are `not re-checked` here. | `ear8qy` |

### T12, T13. CLI alternatives and canonical grammar

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Three-grammar comparison, with `aw run synth` as the third option (C02 3.1) | keep | The outline compares C03's four grammars. C02 adds the argument against `aw run synth`: the run family already has two exit tables and host forwarding, so a typed process inside it needs stage-specific flags. That argument is not in C03. | Add it as one row of the merged 3.1 table. | C02 3.1; `run_cli` exit constants |
| No aliases in release one; help epilogs in `aw specs`, `aw research`, `aw run` (C02 3.1) | alter | The outline keeps C03's epilog pointer for `aw specs` and `aw research`. C02 adds `aw run --help`. | Add the `aw run --help` pointer. | `53jbi5` T12, T13 |
| Start verb with typed inputs: `aw synth start --brief`, `--spec`, `--question`, `--question-file`, `--candidates` (C02 3.2, 3.3) versus `aw synth spec|research <brief>` (C03 3.2) | discard | Q-1 chose one `aw synth` noun; it did not choose the leaf shape. C03's `spec` and `research` leaves make the record type explicit at the verb, so each leaf has one positional input and one argument contract. C02 needs a rule that exactly one of five source flags is present and that `--kind` agrees with it. That rule adds a refusal class without adding a capability. | none | C02 3.3 "Exactly one source mode is required" |
| `preview` as a separate leaf (C02 3.2) | already covered | C03 previews any mutating leaf without `--apply`, the repository's `dry_run_default` convention. | none | C03 FND-13 |
| `show R --view progress|findings|artifacts|plan|config` (C02 3.2) | already covered | C03 `status`, `findings`, and `status --plan` cover the same reads. | none | C03 3.5 |
| `fork R --config` (C02 3.2) | already covered | C03 `--from-run <run> --reuse generate|refine|none` (R-25b) starts a new run that reuses digest-identical outputs. | none | C03 R-25, R-25b |
| `config put|use|show` with `--scope user|project` (C02 3.2, 4) | alter | C03 keeps preferences user-local and allows project policy only as ceilings, because model ids can disclose institution topology (`53jbi5` T26 to T30). C02 allows a project-scope preset that names profiles. A profile name is not a model id, so a project preset of profile references does not disclose models. | Keep C03's rule. Allow a project file to hold roster templates of profile NAMES only, never model ids. This is a minor extension; omit it if the merged spec's author judges it unnecessary. | `53jbi5` T26 to T30 row "Preferences file location" |
| `import R --manifest returns.json` for externally executed prepared tasks (C02 3.2) | keep | C03 `import` brings in whole candidates. C02 additionally lets an operator run individual prepared tasks outside the tool (for example on Codex, which has no runner) and return the outputs by manifest. That is the release-1 route for an unsupported ACE that C02 and the outline both rely on (T8 row above). C03 has no per-task return path. | Specify it as `aw synth import <run> --returns <manifest>`, validated by the worker return envelope (T42-a). | C02 3.2, 4 last paragraph |
| `--gates exceptions|each` (C02 3.2) | needs maintainer decision | The brief asks to "accept or reject a stage result" (`443ltw` line 84). C03 pauses only on exceptions and lets the operator `reject` a published output before the next stage consumes it. C02 adds an opt-in pause after every candidate's final check and after synthesis verification. See N-1. | none | `443ltw` line 84; C03 R-98 |
| Exit contract 0, 1, 2 with `data.engine_exit` for a reused engine error (C02 3.4) | alter | C03 R-100 to R-102 already confine the facade to 0, 1, 2. C02 adds a field that preserves the underlying run-family exit (3 to 7) when an engine error is mapped. | Add `data.engine_exit` to C03 R-102. | C02 3.4; C03 FND-12 |
| `show` exits 0 for a capped run, with `data.run_state` (C02 3.4) | already covered | C03 3.6 `status` row: "Read succeeded". | none | C03 3.6 |

### T14. Intermediate placement and attention surfacing

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Candidates, revisions and split parts in `specs/draft/` (C02 8.2 rows "Independent spec candidates", "Revisions", "Split parts") | discard | Contradicts DL-16. | none | DL-16 |
| Rendered prompts as prompt records in `prompts/pending` and `prompts/executed` (C02 8.2) | discard | `53jbi5` T14 keeps rendered prompts as brief companion files, because `attention_contract._PROMPTS_MAP` maps `pending` to `ready` and each rendered prompt would show as work (V-02). C02's inventory has 30 prompt records per run. | none | V-02 |
| Brief as research kind `requirements` (C02 5.1, 8.2) | discard | `derive_pipeline_positions` gives a Set a position only when a member has kind `research-prompt`. Replacing the brief's kind with `requirements` removes the Set's position (V-03). The outline keeps the brief as `research-prompt`. | none | V-03 |
| Per-iteration findings as research `assessment` records (C02 8.2) | already covered | Same as the outline. | none | `53jbi5` T14 |
| "Use `assessment` for iterative findings so research's `findings` heuristic does not claim the whole run is synthesized" (C02 8.1) | already covered | Q-5 answered the liveness problem by counting only `reference` synthesis members. | none | `53jbi5` Q-5 |

### T15. Command matrix and per-command contracts

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| `decide R S --accept|--reject --reason` (C02 3.2) | already covered | C03 `accept`, `reject`, and `decide` (R-96, R-98, R-46). | none | C03 3.2 |
| `decide --recover-result returns.json` and `--abandon-attempt ATTEMPT --reason` (C02 6.2) | keep | See T25-b. | Fold into the merged `decide` leaf. | C02 6.2 |
| `finalize --allow-limitations --reason` (C02 3.2, 9) | already covered | C03 `--accept-limitations <text> --by-human` is the outline's choice, and it refuses for single-model runs under DL-17. | none | `53jbi5` T15 |
| `cancel R --reason` (C02 3.2) | alter | C03 R-07 has no reason argument. A reason costs nothing and lets `status` explain a cancelled run. | Add an optional `--reason` to C03 `cancel`, recorded in the cancel event. | C03 R-07 |

### T16, T17. Selectors, precedence, modes

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Run selectors require an exact run id, never "latest" (C02 3.3) | already covered | C03 3.3 rules, with `last` reserved, which the outline keeps. | none | `53jbi5` T16 |
| Single-input artifact selectors demand exactly one match (C02 3.3) | keep | C03 3.3 does not state that a Set selector naming many records refuses for a single-spec input. `ear8qy` records that `selectors.resolve_for_mutation` can intentionally name many records for a Set. | Add: "A selector for an input that takes one record MUST resolve to exactly one record, else exit 2." | `ear8qy` row `selectors.py`; `not re-checked` here |
| Same-named preset resolution local > project > user, whole preset replaced, never merged (C02 4) | alter | The outline uses C03's six-level precedence (C03 3.3). C02's rule that a roster is replaced as a whole, never mixed across levels, is not stated in C03. | Add to the merged precedence rule: "A roster from one level replaces the roster of a lower level as a whole." | C03 3.3; C02 4 |
| Preview warns when explicit round counts make quick as expensive as thorough (C02 4) | keep | Small, observable, and consistent with C03 3.4's mode table. | Add to C03 R-38. | C02 4 |
| Quick keeps the whole roster and reduces iterations only (C02 5.2, D-03) | already covered | Same as C03 3.4, which `53jbi5` T17 keeps. | none | `53jbi5` T17 |
| Self-contained expanded config through `--config`, exported by `show --view config --json` (C02 4, 6.1a) | alter | C03 prints the explicit form at preview (`--explicit`), and C03 OQ-13 notes that the explicit form cannot spell every preference value. A frozen JSON export solves OQ-13 without new negating flags. | Resolve C03 OQ-13 with a frozen-config export that `start --config` accepts. Keep the printed explicit form for readability. | C03 OQ-13 |

### T18, T19. Inputs, freeze, independent generation

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Frozen brief, source hashes, commit (C02 R-01) | already covered | C03 R-20, R-21, R-26. | none | `53jbi5` T18 |
| Brief fields: confidentiality and egress scope, as-of time (C02 5.1) | alter | C03 freezes the brief and has a run-level `--as-of` but no source-scope field. The brief requires that private repository content be protected (`443ltw` line 142). | Add an optional `source_scope` list of logical paths to the frozen brief, and refuse a packet that includes a path outside it. | `443ltw` line 142 |
| "A model prompt saying 'do not read peers' is not an enforced boundary"; isolation label `enforced|instruction-only` (C02 7.3) | keep (T19-a) | C03 R-80 lists per-participant controls in the preview but records no run-level isolation label. For Antigravity, out-of-worktree access is "not controlled" (C03 R-80), because the driver passes `--dangerously-skip-permissions` (V-04). The merged spec must therefore not claim enforced independence for an `agy` participant. | Record `isolation: enforced|instruction-only` per participant from the R-80 verdict. The final record's `## Synthesis provenance` MUST state it. The independence label of R-29 MUST NOT say `independent` without qualification for an `instruction-only` participant. | V-04; C03 R-29, R-80 |
| `allow_weak_isolation` preference (C02 9) | discard | With the label above, the run already reports weak isolation honestly. A separate opt-in would make every run with an `agy` participant refuse by default, which contradicts the maintainer's roster (Gemini on `agy`). | none | C03 R-80; `53jbi5` T26 to T30 |
| Fresh same-model check sessions are not independent-model corroboration (C02 7.3, R-08, A-04) | already covered | C03 R-15, R-29, AC-12. | none | C03 AC-12 |

### T20. Refinement loops and convergence

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Iteration = one check plus one revision; generation and terminal check not counted (C02 5.2) | already covered | C03 R-30. | none | `53jbi5` T20 |
| Finding id `F-0001` per run (C02 5.3) versus `<doc-id6>.F<nn>` per document (C03 R-32) | discard | C03's id names the document a finding belongs to, which survives a document being split or renamed under its id6. | none | C03 R-32 |
| Severity `BLOCKER|HIGH|MEDIUM|LOW` and significance `material|editorial` (C02 5.3) | discard | The outline uses the `review_findings.SEVERITIES` vocabulary and the configured gate threshold (`53jbi5` T20). A second vocabulary would need its own mapping. | none | `53jbi5` T20 row "Material threshold" |
| `fixed` requires a later checker to confirm it on the new digest (C02 5.3) | already covered | C03 R-36 `capped-unverified` expresses the same rule at the cap. | none | C03 R-36 |
| Oscillation by repeated finding fingerprint or a return to a prior content hash (C02 5.3) | already covered | C03 R-35 (section digest k-2, or a finding reopened twice). | none | `53jbi5` T20 |
| Operator sufficiency may accept medium or low limitations but not missing requirements (C02 5.3) | already covered | C03 R-96 and 6.3.1 hard blocks. | none | C03 R-96 |
| Contribution disposition `adopted|adapted|deduplicated|rejected|unresolved` (C02 7.1) | already covered | C03 7.3 uses the same five values. | none | C03 7.3 matrix table |

### T21. Work bounds

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Bound formula `N*(2+2C) + (N>1 ? 2+2M : 0) + 1`, times `1+T` for retries (C02 5.2) | discard | `53jbi5` T21 keeps C03 3.4 arithmetic, which also counts integration reviews and split units. C02 itself says split planning must enumerate tasks instead of using its formula. | none | `53jbi5` T21 |
| Defaults: invocation cap 24 quick and 64 thorough; concurrency 3; timeout 900 s; wall budget 3600 s and 7200 s (C02 5.2) | discard | All are unmeasured, as are C03's (12 and 40). The outline keeps C03's values and its statement that they are estimates. | none | `53jbi5` T21 |
| Preview refuses before dispatch when the no-refinement minimum does not fit the ceiling (C02 5.2) | keep (T21-a) | C03 R-38 prints the arithmetic and warns, but does not refuse when even generation plus the terminal steps exceeds `--max-dispatches`. Such a run can only end `capped` without a result. | Add to C03 R-38: "When the minimum dispatch count (every generation, one review per document, synthesis when N > 1, verify when thorough) exceeds the ceiling, start MUST exit 2 `ceiling-below-minimum` before any dispatch." | C03 R-37, R-38 |
| Run wall-clock budget `--max-seconds` (C02 3.3, 5.2) | alter | C03 has a per-dispatch timeout but no run-wide time limit. A dispatch ceiling already bounds spend. A wall-clock limit bounds an unattended run that waits on slow hosts. | Add optional `--max-seconds`, default unset. When it is reached the run enters `capped` with reason `max-seconds`. Paused time in `waiting-for-human` does not count. | C03 3.3 `--dispatch-timeout` row |
| Retry delays 2, 4, doubling to 60 s (C02 5.2) versus 30, 120, 300 s (C03 R-84) | discard | C03 distinguishes `host-rate-limit` (at least 300 s) from other failures. C02's short delays would retry a rate-limited host four times inside two minutes. | none | C03 R-84 |
| Optional `max_tokens` and `max_cost` caps that refuse when the adapter cannot measure them (C02 6.1a, 9) | alter | C03 R-89 reports cost when known and has no cost cap. C02's rule (refuse a cost cap the adapter cannot enforce) is correct, but neither host adapter reserves tokens before a dispatch today. | Record as deferred in the merged 1.6 table, with C02's refusal rule as the condition for enabling it. | C03 R-89 |

### T22. Synthesis and provenance

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| No majority vote, minority eligible, novel ideas tagged `origin=synthesizer` (C02 7.1, R-07) | already covered | C03 7.3, R-41 to R-43. | none | `53jbi5` T22 |
| "Provenance means who proposed it; evidence means why it is justified. These are separate fields" (C02 7.1) | keep | C03's matrix row has a source quote and a rationale, but does not state that origin and justification are separate fields. | Add the sentence to the merged matrix schema. | C03 7.3 |
| Contribution extraction in bounded packets when synthesis input exceeds context (C02 7.3) | discard | `53jbi5` T22 discards C01's equivalent two-pass synthesis as the lossy summary the brief forbids. C03 R-54 stops with `context-overflow`. | none | `53jbi5` T22 row "Two-pass hierarchical synthesis" |
| One synthesizer per run, alternative syntheses deferred (C02 1, D-02) | already covered | C03 R-44, R-45. | none | `53jbi5` T22 |
| Solo run skips merge and keeps an identity contribution map (C02 R-08, 7.1) | already covered | C03 R-40, R-47. | none | C03 R-40 |

### T23. Research evidence

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Evidence families: "three reports citing one source are one evidence family" (C02 7.2, A-09) | alter (T23-a) | C03 R-113 counts corroboration by distinct `origin` values. C03 R-112 makes `origin` optional ("when known"). Without an origin, three citations of one article from three candidates count as three. C02's rule closes that gap. | Add to C03 R-113: "Sources with the same canonical locator (URL after normalization, or repository path plus commit) MUST share one `origin` when none is given." Add C02 A-09 as an acceptance test. | C03 R-112, R-113 |
| A research run may finish clean with a supported answer that the evidence is inconclusive (C02 7.2, 9, A-09) | keep (T23-b) | C03 R-117 does not say whether "inconclusive" is a clean answer or an incomplete one. Without the rule, an honest "the evidence does not decide" report reads as missing work. | Add to C03 R-117: "An answer that states, with cited evidence, that the question cannot be decided is a complete answer." | C03 R-117 |
| Claim kind `fact|inference|recommendation`, sources with access time and digest (C02 7.2) | already covered | C03 R-112, R-115. | none | `53jbi5` T23 |
| Complementary coverage: "a participant's silence on another question is not disagreement" (C02 7.2) | already covered | C03 R-111 `--partition split`. | none | C03 R-111 |
| Final research kind `findings`, shelf `active` then `reference` (C02 7.2) | already covered | C03 R-116, R-118. | none | `53jbi5` T23 |

### T24. Identity, lifecycle, finalization

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| A one-participant run may reach `to-review` (C02 9, D-08, A-08) | discard | Contradicts DL-17. | none | DL-17; C03 R-64 |
| Publication journal: allocate, validate, write, rename, update owner indexes, commit a receipt; recovery rolls forward or leaves an explicit pending publication (C02 6.3); cancellation racing publication uses the commit point (C02 6.2) | keep (T24-a) | C03 R-63 to R-69 list finalize's checks and effects but no order and no recovery rule for a crash between them. C03's state table has no transition out of `ready-to-finalize` on interrupt. A finalize killed after `aw specs set` but before `aw research promote` would leave the spec advanced and the intermediates unpromoted. | Add: "Finalize MUST write a publication journal in the run directory before its first owner verb, MUST record each completed owner verb, and MUST write a receipt last. Finalize after an interrupt MUST resume from the journal and MUST NOT repeat a recorded step. Cancel after the receipt reports `already-published`." Add C02 A-12 and A-25 as acceptance tests. | C03 R-63 to R-69, 6.3 |
| Finalize is idempotent: a repeated call returns the same receipt (C02 9) | keep | Same reason as the row above. | Part of the journal rule. | C03 6.3 |
| No `Readiness`, `Approval`, or review record written (C02 R-13, 9) | already covered | C03 R-62. | none | C03 R-62 |
| Requested, resolved and reported identity; `confirmed|unobservable|mismatch` (C02 4) | already covered | C03 `identity_class` (`confirmed|echoed|unobservable|mismatch`) is finer: it separates Antigravity's echoed model id. | none | C03 R-71, R-72 |
| A prompt targeting an unconfirmed model stays unattributed; "intention is not authorship" (C02 8.1) | already covered | C03 R-74 emits facets only when identity is known. | none | C03 R-74 |

### T25. Run control and recovery

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| `--request-id TOKEN`: the same token with the same frozen request returns the existing prepared run; the same token with a changed request refuses (C02 10 last paragraph, A-26) | keep (T25-a) | C03 has no idempotency token (V-05). An agent that retries `start` after a lost response creates a second run and charges for it twice. | Add the flag to `start` and `--prepare-only` with C02's rules. | V-05 |
| `unknown-outcome` state with `decide --recover-result` and `--abandon-attempt --reason` (C02 6.2, A-11) | alter (T25-b) | C03 R-86 handles an interrupted dispatch: a live process refuses resume (`dispatch-alive`), a dead process with a valid outbox is adopted, otherwise the dispatch is `lost` and consumes a retry. C03 assumes a dead local process means the work stopped. That assumption fails when the host process died but a remote session may still be running or billing. C02 names that case and requires an explicit decision before retrying. | Keep C03 R-86. Add: when the dispatch is dead, the outbox is empty, and the host reports the session may still be active (or cannot say), the dispatch enters `unknown-outcome`. `resume` refuses until `aw synth decide <run> <did> --recover-result <file>` or `--abandon-attempt --reason <text> --by-human` is given. Whether a host can report a live remote session is `not re-checked`. | C03 R-86 |
| Cancellation states with no deletion (C02 3.2, 6.2) | already covered | C03 R-07, R-68. | none | `53jbi5` T25 |
| Partial roster requires `--allow-partial` or a decision (C02 6.3) | already covered | C03 R-49 `--allow-reduced`, `resume --continue-reduced`. | none | C03 R-49 |

### T26 to T30. Configuration, profiles, capabilities, roles

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Preferences in `synthesis.json` with `schema_version`, `presets`, `selected` (C02 4) | discard | C03 R-17 `synth-preferences.json` beside `runner-profiles.json` is the outline's choice. The two shapes are equivalent; one must be chosen, and the outline already chose. | none | C03 R-17 |
| Roles `author`, `check`, `revise`, `synthesis`, `verify` with defaults (C02 3.3) | already covered | C03 `--role` with `refine`, `synth-refine`, `verify` and the defaults of R-47. | none | `53jbi5` T26 to T30 |
| Profile snapshot with digest copied into the frozen run (C02 4) | already covered | C03 R-86 launches from the frozen `ResolvedLaunch`. | none | C03 R-86 |
| "Current agy profiles refuse `variant`" (C02 4) | discard | Maintainer answer Q-3 relaxes this rule. | none | `53jbi5` Q-3 |
| Capability checks distinguish catalog absence, authentication error, unsupported feature, stale evidence and missing executable (C02 4) | already covered | C03 5.4 capability verdicts and R-84 failure classes. | none | C03 5.4 |
| Permissions object: `isolation`, `source_scope`, `network: deny|allowlist`, `destinations` (C02 6.1a) | alter | `source_scope` is taken in T18. `network` cannot be enforced: C03 R-80 records network access as "not controlled" for both hosts. A `deny` value would be a claim the tool cannot keep. | Keep `source_scope` only. Report network as `not-controlled`, as C03 R-80 does. | C03 R-80 |

### T31 to T40. Entities, states, persistence, naming, inventories

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| ER diagram with run, stage, attempt, prompt, artifact, chunk, finding, claim, evidence, contribution, decision, finalOutput (C02 6.1) | discard | The outline replaces all candidate ER diagrams with the `53jbi5` Section 5.6 model, which maps entities onto MS events and relations. C02's model has no MS mapping. | none | `53jbi5` 5.6 |
| State table with `ready`, `completed`, `completed-with-limitations`, `unknown-outcome` (C02 6.2) | alter | The outline keeps C03 6.3. Only `unknown-outcome` is new (T25-b). | Add `unknown-outcome` to C03 6.3 as a `waiting-for-human` reason, not a new state, so the state machine stays as C03 defines it. | C03 6.3 |
| Every content change after consumption creates a new artifact with a new id6 and `Supersedes` (C02 8.1) | discard | `53jbi5` T31 to T40 keeps C03 R-75: revisions keep their id6 and filename, and bodies are snapshotted in the companion. C02's rule produces one record per revision; its own inventory reaches 60 records for one run. | none | C03 R-75; C02 8.3 |
| Cross-tree NN reservation shared by prompts, research and specs, with linked overflow "volume" Sets (C02 8.1, D-05, A-18) | discard | With DL-16 and rendered prompts in the companion, a run's records live in the research tree plus one working spec record. C03 R-93 refuses a run that would exceed NN 99 before it starts. A cross-tree allocator and a volume-Set mechanism would change every `new` verb for a case the outline does not produce. | none | C03 R-93; DL-16 |
| Set canonical date for new run records (C02 8.1, D-06) | already covered | C03 R-60 creates the spec with `aw specs new --date <set date>`, then regroups it with `aw group specs ... --date <set date> --rename`. V-06 shows that `specs new --date` sets the filename date and that `group --rename` keeps the existing date, ignoring `--date`; C02 8.4 reports the same. R-60 therefore works only because `specs new` already wrote the right date. | Keep C03 R-60. Drop `--date` from its `aw group` call, which has no effect. Add an acceptance test that the final spec's filename date equals the Set date. | V-06 |
| Filename byte limit 240 and slug at most 48 characters (C02 8.1) | alter | C03 has no filename length rule. The filesystem limit here is 255 bytes per name (V-07), and D177 facets lengthen names. | Add: "The engine MUST refuse a derived filename longer than 240 bytes with a shorter-slug remedy." Drop the 48-character slug cap, which is not grounded. | V-07 |
| Native JSON companions `manifest.json`, `config.json`, `contributions.json`, `claims.json`, `decisions.jsonl`, `metrics.json` (C02 8.2) | already covered | C03 6.5 and `53jbi5` E-8 (companion files need their own schema and check). | none | `53jbi5` E-8 |
| Placement through `resolve_record_path` for companion and home backends (C02 8.2, A-21) | already covered | C03 2.2 "Storage roots" row and 6.5. C02's acceptance test A-21 (repeat the lifecycle in repository, companion and home placements) has no C03 equivalent. | Add C02 A-21 as an acceptance test. | C03 2.2 |
| Worked inventories (C02 8.3) | discard | They follow C02's placement and identity rules, which are discarded above. | none | rows above |

### T41 to T44. Flow diagrams, templates, outputs, chunking

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Worker return envelope: `schema_version`, `task_id`, `attempt_id`, `input_digest`, `result_kind`, `documents` (path, media type, byte count, SHA-256), `completed_parts`, `expected_parts_digest` (C02 6.1a) | alter (T42-a) | C03's outcome file has `synth_outcome`, `run`, `dispatch`, `stage`, `subject` and `subject_revision`, but no digest of the inputs the worker saw and no declared byte count or hash for its document (V-08). A stale or swapped output therefore passes the envelope check. The binding matters most for `import --returns` (T12 row), where the tool did not launch the worker. | Add `input_digest`, and per document `bytes` and `sha256`, to the C03 outcome envelope. The engine MUST refuse an outcome whose `input_digest` differs from the dispatch record. Keep C03's other field names. | V-08 |
| Template customization limited to objectives, formatting and explanatory text; changes to permissions, output schema or gates need a new run configuration (C02 5.1) | keep | C03 lets a project `template_dir` override a packaged template and validates placeholders, closed data blocks and size, but does not restrict what an override may change. An override could drop the data-block instruction (C03 R-82). | Add: "A template override MUST keep the data-block rule, the output path rule and the outcome schema; the engine MUST refuse a rendered prompt that lacks them." | C03 7.1 "Customization" |
| Packet budget defaults 12000 input and 4000 output characters when limits are unknown (C02 7.3) | discard | `53jbi5` T41 to T44 keeps C03's token budgets from discovered limits. | none | `53jbi5` T41 to T44 |
| Spec and research flowcharts (C02 7.1, 7.2) | already covered | The outline keeps C03 7.5 and 7.7. | none | `53jbi5` T41 to T44 |

### T45 to T50. Security, privacy, performance, usability, observability

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Argument arrays, no shell interpolation, model output never executes (C02 9) | already covered | C03 R-83, R-82. | none | `53jbi5` T45 to T50 |
| Confidential sources not sent to a newly selected provider without authorization (C02 9) | alter | Covered by the `source_scope` addition (T18) and C03 R-18 `allowed_providers`. | none beyond T18 | C03 R-18 |
| Leak sanitizer before publication; redaction noted, never disguised (C02 9) | already covered | C03 R-88, R-63. | none | C03 R-88 |
| Timings split into queue, dispatch, model and validation (C02 9) | alter | C03 R-89 reports wall time per dispatch. Separate validation time helps diagnose a slow run at no cost. | Optional; add to C03 R-89 if cheap. | C03 R-89 |

### T51. Acceptance tests

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| A-01 to A-26 (C02 10) | alter | Each names an observable outcome; none reads production source. Most duplicate C03 AC rows. | Carry only the tests that back a `keep` or `alter` above: A-09 (evidence families, inconclusive answer), A-11 (unknown outcome), A-12 and A-25 (journal and cancel at the commit point), A-21 (three storage backends), A-26 (request id), and a version of A-04 that checks the isolation label. Renumber as `AC-`. | V-01 |
| A-08 (solo run publishes `to-review` when clean) | discard | Contradicts DL-17. | none | DL-17 |
| A-18, A-19 (cross-tree allocation, volume Sets) | discard | Their design is discarded (T31 to T40). | none | rows above |

### T52 to T61. Risks, decisions, open questions, implementation, sources

| Item (C02 location) | Decision | Reason | Alteration | Evidence |
| --- | --- | --- | --- | --- |
| Decisions D-01 to D-10 (C02 12) | alter | D-01, D-02, D-03, D-04, D-07, D-09 and D-10 agree with the outline. D-05 and D-06 are discarded (T31 to T40). D-08 contradicts DL-17. | none | rows above |
| "No blocking product question is left" (C02 12) | discard | C02 answers questions that the maintainer has since ruled on differently (DL-16, DL-17) and leaves the Q-1 to Q-6 choices unexamined. | none | `53jbi5` Section 8 |
| Six integration seams (C02 12) | already covered | C03 11 has eight steps in dependency order, which the outline keeps, plus the MS step. | none | `53jbi5` T52 to T61 |
| Fictional example ids flagged as dangling citations; a marked example-inventory convention needed (C02 13) | keep (T52-a) | Measured: `aw research check-refs` reports fictional ids in all three candidates as dangling: 2 in C01, 4 in C03, 8 in C02 (V-09). The merged spec needs worked inventories with valid sample names, and so will hit the same check. | Add as a separate small requirement on the citation checker: an explicitly marked example block is excluded from dangling-citation checks, and its names are still checked against the naming grammar. This is a checker change, so it may be filed as its own backlog item instead. | V-09 |

## 4. Questions that need a maintainer decision

### N-1. Pause after every stage (`--gates each`)

- Context: the brief asks that an operator can "accept or reject a stage result" (`443ltw` line 84). The outline (from C03) pauses only on exceptions: reduced participation, conflicts, caps, modified artifacts. Between stages the operator can still `reject` a published output before a later stage consumes it (C03 R-98), but nothing waits for them. C02 adds `--gates each`, which pauses after each candidate's final check and after synthesis verification and continues only on `decide --accept`.
- Options: (a) add `--gates each` as an opt-in flag, default `exceptions`; (b) leave it out of release 1.
- Recommendation, weak: (b). The exception pauses plus `reject` already meet the brief, and an every-stage pause adds a `waiting-for-human` reason and a resume path to test. Unknown: how often the maintainer would want to inspect candidates before synthesis.
- Blocking: no. The merged spec can be written with either answer, and (a) is additive.
- RESOLVED 2026-11-06 by the user via /askme: (a), add `--gates exceptions|each` as an opt-in flag in release 1, default `exceptions`. Under `each` the run pauses after every candidate's final check and after synthesis verification, and continues only on `decide --accept`. No reason was given. Effect on the merged spec: one more `waiting-for-human` reason and its resume path, with tests.

### N-2. Antigravity permission posture

- Context: the existing Antigravity driver always passes `--dangerously-skip-permissions` (V-04). So an `agy` participant can read files outside its worktree, including other participants' outputs, and the outline therefore cannot enforce independence for it (C03 R-80, T19 row above). `agy --help` also lists `--sandbox` ("Run in a sandbox with terminal restrictions enabled"). Whether that sandbox stops file reads outside the workspace is `not re-checked`.
- Options: (a) keep the driver's posture and record `isolation: instruction-only` for `agy` participants; (b) have specflow dispatches use `--sandbox`, after a measurement shows what it blocks.
- Recommendation, medium: (a) for the merged spec, with (b) recorded as a measured follow-up. (a) is honest today and needs no driver change; (b) depends on an unmeasured host feature.
- Blocking: no. The isolation label (T19-a) is correct under both answers.
- RESOLVED 2026-11-06 by the user via /askme: (a), keep the driver's `--dangerously-skip-permissions` posture and record `isolation: instruction-only` for `agy` participants; measuring what `agy --sandbox` blocks is a follow-up backlog item. No reason was given.

## 5. Validation performed

All commands ran in this checkout on 2026-11-06 at HEAD `4f09df0c7`.

V-01. Requirement-id parse of C02 and C03 with the repository parser.

```text
$ python3 - <<'EOF'
from agent_workflows.production_checks import parse_spec_requirement_ids
...
EOF
1tx9t8 requirements 20 acceptance 26
yfz5u9 requirements 108 acceptance 104
['R-01', 'R-02', 'R-03'] ['A-01', 'A-02', 'A-03', 'A-04', 'A-05']
```

V-02. Attention mapping for prompt records.

```text
$ python3 -c "from agent_workflows import attention_contract as a; print(a._PROMPTS_MAP)"
{'pending': 'ready', 'executed': 'done', 'superseded': 'parked', 'not-executed': 'parked', 'reusable': 'parked'}
```

V-03. A Set whose brief has kind `requirements` instead of `research-prompt` loses its pipeline position. Set `awclia` was used as the fixture, with its prompt's kind replaced in memory.

```text
awclia kinds ['research-prompt', 'research-report', 'research-report', 'research-report', 'reconciliation-report'] {'awclia': 'unrun'}
brief as requirements -> {}
```

V-04. The Antigravity driver's permission flag, in `agy_runipd.run_agy_turn`.

```text
    if options.get("dangerously_skip_permissions", True):
        argv.append("--dangerously-skip-permissions")
$ agy --help | grep -iE 'sandbox|permission|dir'
  --add-dir                       Add a directory to the workspace (repeatable) (default [])
  --dangerously-skip-permissions  Auto-approve all tool permission requests without prompting
  --sandbox                       Run in a sandbox with terminal restrictions enabled
```

V-05. Terms absent from C03 (count of matching lines).

```text
request-id 0
idempot 0
preset 0
--gates 0
input_digest 0
```

V-06. Date handling of the owner verbs (previews only; nothing was written).

```text
$ aw specs new --title "Probe" --slug probe-date --date 2026-10-24
--- would write .../specs/draft/20261024-70p3sp-01-70p3sp-probe-date.spec.md ---
$ aw group specs 1tx9t8 --set zzzt --order 3 --date 20261024 --rename
--- would rename ...20261025-specflow-02-1tx9t8-...spec.md -> 20261025-zzzt-03-1tx9t8-...spec.md ---
```

`aw specs new --date` sets the filename date. `aw group specs --date 20261024 --rename` keeps `20261025` in its preview, which matches C02 8.4's report.

V-07. Filesystem name limit.

```text
$ getconf NAME_MAX .
255
```

V-08. C03 outcome envelope fields (C03 7.1): `synth_outcome`, `run`, `dispatch`, `stage`, `subject`, `subject_revision`, `document`, `findings`, `coverage`, `notes`. No input digest and no document hash or byte count appear (V-05 `input_digest 0`).

V-09. Dangling-citation check on the candidates.

```text
$ aw research check-refs
...specflow-01-18hh1u...:1440: dangling id6 'c1a001'
...specflow-01-18hh1u...:1461: dangling id6 'th48m1'
...specflow-03-yfz5u9...:1352: dangling id6 'k2m9qa'
...specflow-03-yfz5u9...:1369: dangling id6 'f6nb1x'
...specflow-03-yfz5u9...:1408: dangling id6 'q3rw8e'
...specflow-03-yfz5u9...:2115: dangling id6 'n4bt7c'
...specflow-02-1tx9t8...: 8 lines (x00001, x00002, x00049, x00059, y00001, y00002, y00013, z00025)
research check-refs: detected 345 dangling citation(s) across 2989 files
```

V-10. `aw check` findings that name a `specflow` artifact: `check.name-nonconformant` on the six D177 prompts and on C02, and `check.prompt-metadata-missing` on the three generation prompts. These confirm C03 1.2 item 1 and C02 8.4 (C02's attributed spec name is not accepted by the current grammar).

Claims marked `not re-checked`: the `ear8qy` documentation discrepancies; the `selectors.resolve_for_mutation` behavior that `ear8qy` reports; whether either host can report a still-active remote session after its local process dies (T25-b); what `agy --sandbox` blocks (N-2).

## 6. Effect on the merge outline

The `53jbi5` Section 7 outline stands. The merged spec adds these items, each placed in the outline section shown:

| Outline section | Additions from C02 |
| --- | --- |
| 1.6 | Codex deferral justified by prepare and import; cost caps deferred with C02's refusal rule (T8, T21). |
| 3.1 to 3.5 | `aw run synth` comparison row; `aw run --help` pointer; `import --returns`; `data.engine_exit`; optional `cancel --reason`; exactly-one-match single-input selectors; whole-roster replacement in precedence; frozen-config export resolving C03 OQ-13; quick-as-costly warning (T12 to T17). |
| 4.1 | `--request-id`; `unknown-outcome` as a `waiting-for-human` reason with `decide --recover-result` and `--abandon-attempt` (T25). |
| 4.2 | `source_scope` in the frozen brief (T18). |
| 4.3 | Isolation label per participant (T19-a). |
| 4.5 | `ceiling-below-minimum` refusal; optional `--max-seconds` (T21). |
| 4.6 | Origin and justification as separate matrix fields (T22). |
| 4.8 | Publication journal, receipt and idempotent finalize (T24-a). |
| 4.9 | Same-locator sources share one `origin`; inconclusive-but-supported answers are complete (T23). |
| 4.10 | 240-byte filename refusal; filename date equals Set date as an acceptance test (T31 to T40). |
| 4.13 and 7 | `input_digest` and per-document `bytes` and `sha256` in the outcome envelope; template overrides must keep the safety rules (T42). |
| 9 | Carried C02 tests A-04 (isolation label), A-09, A-11, A-12, A-21, A-25, A-26, renumbered as `AC-` (T51). |
| 10.4 | N-1 and N-2. |
| separate | Example-block exemption for dangling-citation checks (T52-a), as a requirement or a backlog item. |
