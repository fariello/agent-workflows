---
id: 5zczmo
created: 20260802
set: chkplace
order: 04
topic: []
model:
kind: findings
status: reference
outcome: adopted
summary: Migrated from 20260731-chkplace-04-5zczmo-checklist-placement-and-instruction-audit.findings.md.
consumed-by: []
---
# IPD Checklist Placement and Instruction Audit: Consolidated Multi-Agent Research Findings

**Synthesis date:** 2026-08-01
**Research-report cutoff:** 2026-07-31
**Reports synthesized:** 3
**External research added during synthesis:** None

## Document purpose and scope

This document integrates three independently authored reports about the placement, structure, and enforcement of execution and validation checklists in agent-executable Implementation Plan Documents (IPDs). It is intended to be sufficiently complete and traceable that a downstream agent can use the synthesis without rereading all three reports.

The original research prompt was not supplied with the synthesis materials. The shared scope is therefore reconstructed from the reports themselves:

1. **Q1 — Checklist placement and ordering:** Assess the evidence for placing an execution checklist near the beginning of an IPD and a separate validation/cross-check checklist near the end; distinguish read-order from act-order effects; compare alternative layouts; assess strong-frontier versus weak/fast-model behavior; and address premature completion.
2. **Q2 — Instruction audit:** Audit `ipd.md`, `ipd-spec.md`, `plan-review.md`, `review-rubric.md`, and `03-resolve-and-finalize.md` for ambiguous, conflicting, skippable, or over-literalizable instructions, especially those governing checklist placement, one-to-one mapping, evidence, review, and lifecycle state.
3. **Deliverable:** Give a consolidated recommendation, identify open questions, and propose experiments that could resolve the unsupported parts of the design.

The five framework files were available to and reportedly read by all three research agents, but they were not supplied as separate inputs to this synthesis. This synthesis can therefore compare the reports' quotations and audits, but it cannot independently re-audit the framework files. The three reports also cite research published through July 31, 2026. No source-validation report was supplied, and this synthesis did not browse or re-open cited sources. “Validated” below means only that an input report says it checked the source; it does not mean the synthesizer independently validated it.

### Canonical terms

- **Execution checklist:** The actionable, tickable list of work to perform, headed `## Detailed Implementation Checklist (TODO)` in the audited template.
- **Validation checklist:** A distinct evidence pass, headed `## Validation and cross-check (verify before reporting done)`.
- **Two-phase design:** Execution and validation remain semantically and statefully distinct, even if a small-plan exception renders them in one table or ledger.
- **Placement:** The physical order of headings or instruction blocks in the IPD.
- **Phase-local reminder:** A short, immutable restatement of the active phase rule at the point of execution or validation; it is not a second editable copy of the checklist.
- **Structural linter / preflight:** Deterministic validation of headings, order, identifiers, mappings, permitted state, and lifecycle invariants.
- **False completion:** Reporting success or entering terminal state while required work, evidence, tests, or lifecycle conditions remain false or incomplete.

### Important limitations

- No report found a controlled study that directly compares the proposed IPD layouts in a coding-agent workflow. The optimal physical placement is **unknown**.
- The strongest general evidence about position concerns retrieval or question answering, not iterative execution of a mutable plan.
- Several newer or provider-specific findings indicate that position effects vary materially by model, task, instruction type, and conversation history.
- R2 makes important claims about “cognitive forcing,” chain-of-thought, weak-model working memory, and tooling “preventing drift entirely” without adequate cited support. Those claims are not adopted as established findings.
- R1 relies partly on a 2026 single-author, unreplicated preprint with unusually large effects. Its directional implications are plausible; its exact magnitudes remain provisional.
- `report-template.md`, referenced by `03-resolve-and-finalize.md`, was not among the audited attachments. Full single-file/multi-file template parity remains untested.

## Executive synthesis

The maintainer's top-execution/bottom-validation convention is **defensible as a default but not established as optimal**. Long-context research supports keeping important control material out of the middle and sometimes supports instructions near the point of use. Provider guidance differs by model and task: Anthropic and Google guidance cited in the reports often favors a final query or instruction after long context, while OpenAI's GPT-4.1 guide reportedly found beginning-and-end repetition strongest and beginning-only better than end-only when one placement was required. These results do not directly answer where a mutable execution checklist belongs inside an iteratively used IPD.

The reports' most robust shared conclusion is that **physical placement is a secondary control**. The audited instruction set describes placement with non-testable phrases such as “near the top,” “near the beginning,” and “near the end”; does not define the unit of one-to-one execution/validation mapping; provides an aggregate validation example that conflicts with a strict bijection; and asks reviewers to assess content without an explicit structural preflight. Consequently, the observed checklist drift does not demonstrate that a capable model ignored a clear invariant. The invariant was not fully specified or enforced.

The highest-confidence intervention is to convert deterministic properties into deterministic checks. The execution heading should occur exactly once and immediately after `## Goal`; the validation heading should occur exactly once and immediately before `## Approval and execution gate`; executable leaves should have stable `E-*` identifiers; every execution ID should have exactly one `V-*` validation item with falsifiable evidence requirements; and phase/lifecycle state should be linted at authoring, review, pre-execution, pre-transition, and post-transition boundaries. Semantic review remains necessary because a linter cannot prove coverage, code correctness, or evidence authenticity.

The two-checklist concept should be retained by default because “performing an action” and “inspecting evidence that it succeeded” are different states. R2 recommends merging them when tooling is unavailable, chiefly to reduce synchronization burden for weaker models. R1 and R3 instead recommend retaining a separate validation pass and using stable IDs, phase-local reminders, and external evidence. The latter position is better supported: self-review and false-completion evidence argues against collapsing execution and validation, while no supplied controlled evidence establishes that adjacency or a chain-of-thought-shaped evidence sub-bullet improves actual compliance. A unified action/evidence ledger is a reasonable **small-plan exception** only if the workflow still requires a distinct final evidence pass.

The recommended design therefore keeps one canonical mutable execution checklist at the top boundary, one canonical validation checklist at the bottom boundary, and short immutable reminders at the point of use. It does not duplicate the full mutable checklist. It removes terminal status change and `git mv` from the checklist that must already be complete before transition, treating lifecycle transition as a post-gate transaction. It also resolves blocking questions before execution and treats numeric plan-size limits as warning thresholds requiring an explicit cohesion exception rather than pseudo-mandatory rules.

## Key conclusions

| ID | Conclusion | Epistemic status | Evidence basis | Report provenance |
|---|---|---|---|---|
| C-01 | No supplied evidence directly establishes the optimal physical placement of execution and validation checklists in an iteratively executed coding-agent IPD. | **Established** within the supplied research search | All reports state or imply the direct experiment is absent. | R1, R2, R3 |
| C-02 | The current top-execution/bottom-validation arrangement is a defensible default, but its advantage is an inference from adjacent long-context evidence, not a proven IPD result. | **Plausible** | Boundary-position, provider prompting, and reinstruction evidence; task-transfer limitation. | R1, R3; partially R2 |
| C-03 | The audited framework does not express checklist placement as an exact, machine-testable invariant. | **Well supported** | Consistent quotations of “near the top/beginning/end” across the three audits. | R1, R2, R3 |
| C-04 | The template's stated one-to-one validation contract is under-specified and apparently contradicted by an aggregate validation example. | **Well supported** | Detailed template comparison in R3; compatible with R1/R2's broader structural critique. | R3; consistent with R1, R2 |
| C-05 | A deterministic structural/state linter is the highest-priority fix. | **Well supported engineering recommendation** | Unanimous cross-report recommendation; directly targets deterministic failure modes. No controlled effect-size evidence. | R1, R2, R3 |
| C-06 | Execution and validation should remain separate semantic phases by default. | **Well supported** | False-completion/self-correction evidence and state-model reasoning; R2 dissents for prose-only weak-model use. | R1, R3; contested by R2 |
| C-07 | The mutable execution checklist should not be duplicated. Use stable IDs and short phase-local reminders or tool-mediated next-item surfacing instead. | **Well supported engineering recommendation** | Repetition can help or backfire; mutable duplication creates divergence risk. | R1, R3; R2 also flags sync risk |
| C-08 | Concrete, falsifiable external evidence and an enforced transition gate matter more than checklist position. | **Well supported directionally** | Self-correction research, provider/benchmark evidence, and a provisional compliance preprint. Exact universal ranking is not established. | R1, R3; broadly R2 |
| C-09 | Terminal lifecycle transition must be outside the pre-transition execution/validation bijection to avoid a circular gate. | **Well supported** | Direct logical analysis of quoted template rules in R3. | R3 only |
| C-10 | Capability tier does not yield a simple rule such as “weak models are always more position-sensitive” or “reasoning models self-verify reliably.” | **Well supported** | Model- and instruction-dependent findings; false-success reports; explicit caution in R1/R3. | R1, R3; R2 overgeneralizes |

## Agreements across reports

| ID | Agreed finding | Nature of agreement | Independent underlying evidence? | Qualifications | Reports |
|---|---|---|---|---|---|
| A-01 | Long-context use often shows boundary advantages or degraded middle use. | Full at a high level | **No** for the core claim: all rely on Liu et al. [S-01]; R1/R3 add other sources. | Established mainly for retrieval/QA; not universal across models/tasks. | R1, R2, R3 |
| A-02 | The reports found no direct experiment on the exact IPD layout. | Full | The reports are independent searches, but search completeness is not provable. | Absence in the searches is not proof no such study exists. | R1, R3; implicit R2 |
| A-03 | “Near the top/end” is too vague to enforce consistently. | Full | **Yes** as independent textual audit of the same primary framework files. | Exact line references differ by report formatting. | R1, R2, R3 |
| A-04 | Review instructions assess checklist content but do not operationalize placement checking. | Full | **Yes** as independent textual audit; all examined the same files. | R3 provides the most detailed preflight specification. | R1, R2, R3 |
| A-05 | Machine checking should replace reliance on prose for deterministic structure. | Full | Engineering convergence, not independent empirical corroboration. | A linter cannot establish semantic completeness or evidence truth. | R1, R2, R3 |
| A-06 | Duplicating the full mutable checklist creates synchronization risk. | Full | Shared design reasoning; R1/R3 cite mixed repetition evidence. | Immutable reminders or tool views of the same canonical IDs are different from duplication. | R1, R2, R3 |
| A-07 | Actual evidence is more important than a bare checked box or completion claim. | Full | Mixed: distinct cited bodies in R1/R3; R2 offers mostly unsupported mechanism claims. | Evidence can itself be fabricated; external state and captured outputs are preferable. | R1, R2, R3 |
| A-08 | Strong and weak/fast models should both benefit from explicit structure and tooling. | Full | Design inference, not a controlled cross-tier IPD result. | Effect sizes and optimal presentation may differ by model. | R1, R2, R3 |

## Disagreements, contradictions, and resolutions

| ID | Issue | Positions and supporting evidence | Conflict type | Assessment or resolution | Residual uncertainty | Reports |
|---|---|---|---|---|---|---|
| D-01 | Is the maintainer's top/bottom intuition supported or contradicted? | R1: unresolved directly and partly contradicted by closest act-time guidance; R2: supported in theory but contradicted in practice; R3: unresolved but directionally coherent. | Interpretation and task transfer | **Resolution:** unresolved by direct evidence. Top/bottom is defensible, not proven. R2's “contradicted in practice” exceeds the evidence; one drift incident and an asserted generation mechanism do not establish contradiction. | High; requires direct experiment. | R1 vs. R2 vs. R3 |
| D-02 | Should a prose-only framework merge execution and validation? | R2 favors a unified per-task checklist for weak models. R1 says keep two checklists. R3 retains two phases, allowing a tiny-plan merged ledger with a separate final evidence pass. | Design recommendation | **Resolution:** retain two semantic phases by default. Allow a small-plan ledger exception only with a distinct final validation pass. R2 supplies no direct study showing adjacency improves fidelity. | Medium; weak-model A/B testing could change the fallback. | R2 vs. R1/R3 |
| D-03 | Does top execution placement have positive evidence? | R2 applies primacy directly. R1 emphasizes Anthropic's end-instruction guidance and sees top execution as poorly supported for act-time recall. R3 adds GPT-4.1 guidance favoring beginning-only over end-only when one copy is used. | Source scope/model difference | **Resolution:** evidence is provider- and task-specific. Early placement can frame the plan; late reminders can support action-time recall. Use one early canonical list plus a short phase-local reminder rather than claiming one position universally wins. | Medium to high. | R1, R2, R3 |
| D-04 | Is position a real compliance driver? | R1 cites one preprint reporting 8.9% variance from position and another study finding no consistent effect. R3 treats position as a low-ranked defense. R2 ranks it third without adequate quantification. | Measurement/task difference | **Resolution:** position may have a real but secondary and task-dependent effect. No universal magnitude is established. | High across current model families. | R1, R2, R3 |
| D-05 | Does evidence generation work by forcing chain-of-thought and preventing hallucinated completion? | R2 states this as established. R1 emphasizes audit-trail incentives and shortcut removal, with strong caveats. R3 emphasizes external evidence and warns against verbose reasoning. | Unsupported mechanism claim | **Resolution:** reject the chain-of-thought mechanism as established. Require observable evidence, not hidden or narrated reasoning. Evidence makes false claims more detectable; it does not make them impossible. | Medium. | R2 vs. R1/R3 |
| D-06 | Can tooling prevent drift entirely? | R2 says machine enforcement “prevents drift entirely.” R1/R3 describe tooling as enforcing structure but not semantics or authenticity. | Overstatement | **Resolution:** tooling can nearly eliminate the specific structural defects it checks; it cannot prevent omitted requirements, wrong edits, fabricated evidence, or unmodeled lifecycle errors. | Low for this resolution. | R2 vs. R1/R3 |
| D-07 | Which evidence should dominate the compliance ranking? | R1 gives high weight to Shin's 2026 compliance preprint; R3 omits it and relies on peer-reviewed/provider sources plus inference; R2 offers an uncited ranking. | Evidence-quality methodology | **Resolution:** use the preprint only as provisional directional support. Base the recommendation on converging logic and stronger adjacent evidence, not its exact 97%, 75%, or effect-size claims. | Medium pending replication. | R1 vs. R3; R2 weakly sourced |

## Integrated findings by topic

### Topic 1 — What position evidence actually establishes

#### Finding F-01: “Lost in the middle” does not directly determine IPD checklist placement

- **Synthesized finding:** Long-context models often use information more reliably at the beginning or end than in the middle, but the best-established demonstrations concern multi-document question answering and key-value retrieval. The effect varies by model and task, and some newer-model evaluations reportedly weaken or fail to reproduce it. It does not establish whether an execution checklist should be first, last, duplicated, merged, or externally surfaced during iterative tool use.
- **Epistemic status:** **Established** for the bounded retrieval finding; **plausible** as a reason to avoid burying control material; **unknown** for optimal IPD placement.
- **Evidence:** Liu et al. [S-01] is the shared core source. R1 adds HELMET [S-09], Counting-Stars [S-10], a Gemini 2.5 Flash study [S-11], and an MIT mechanistic summary [S-21].
- **Qualifications:** Cross-report repetition is not independent corroboration because all three reports rely on [S-01]. The reports differ in how strongly they generalize retrieval to compliance.
- **Report provenance:** R1, R2, R3.
- **Implication:** Treat boundary placement as defense in depth, not as the primary compliance control.

#### Finding F-02: Read-order and act-order support different design functions

- **Synthesized finding:** An early execution checklist can frame the plan and organize later rationale; a late or phase-local instruction can be more available at the moment of action. Provider evidence does not yield a universal ordering rule. Anthropic and Google guidance cited by R1/R3 often favors placing the query or instructions after long context [S-03, S-04, S-05]. OpenAI's GPT-4.1 guide, cited by R3, reportedly found instructions at both boundaries strongest and beginning-only stronger than end-only if instructions appeared once [S-02].
- **Epistemic status:** **Well supported** that both mechanisms are plausible and model/task dependent; **unknown** which dominates in IPD execution.
- **Qualifications:** These provider tests concern source-context prompting, not repeated mutation of an IPD over a long agent loop.
- **Report provenance:** R1, R3; R2 offers compatible but less supported reasoning.
- **Implication:** Preserve early framing with one canonical list and add a compact reminder at each phase boundary. Do not duplicate the mutable checklist.

#### Finding F-03: Position is likely secondary to verifiability, state, and external enforcement

- **Synthesized finding:** The reports broadly agree that a well-placed prose checklist can still be falsely ticked. Atomic items, concrete expected outcomes, captured tool evidence, a distinct evidence pass, stable state, and a gate able to reject an invalid transition provide stronger failure containment.
- **Epistemic status:** **Well supported directionally**, but no universal rank ordering or effect sizes are established.
- **Evidence:** Self-correction limitations [S-08], long-context instruction degradation and reinstruction [S-06, S-07], false-success and multi-agent failure studies reported by R1 [S-15–S-18], and the provisional compliance preprint [S-12].
- **Qualifications:** R1's exact compliance magnitudes come from an unreplicated preprint. R2's chain-of-thought account is unsubstantiated.
- **Report provenance:** R1, R2, R3.
- **Implication:** Optimize for claims that are externally checkable and transitions that can be rejected, not for prose salience alone.

### Topic 2 — Root causes in the audited instruction set

#### Finding F-04: Placement wording is relational, subjective, and non-lintable

- **Synthesized finding:** The framework uses “near the top,” “near the BEGINNING,” “near the end,” or “near the END” rather than exact heading adjacency and uniqueness. A model can place a checklist elsewhere while preserving a coherent interpretation of “near.”
- **Epistemic status:** **Well supported**.
- **Evidence:** Direct quotations from `ipd.md` and `ipd-spec.md` reported independently by all three audits [S-22, S-23].
- **Report provenance:** R1, R2, R3.
- **Implication:** Replace relational wording with exact, normative placement and a deterministic order check.

#### Finding F-05: The specification does not present one complete canonical H2 order

- **Synthesized finding:** `ipd-spec.md` reportedly claims canonical order but provides only a partial section list and separately describes the checklist positions. This leaves a plausible path for appending the execution checklist later while still satisfying presence requirements.
- **Epistemic status:** **Well supported**, subject to the limitation that this synthesis did not independently inspect the file.
- **Evidence:** Detailed quotation and audit in R3; R1 independently notes that the specification's own requirement order conflicts with the desired document order.
- **Report provenance:** R1, R3.
- **Underlying source:** `ipd-spec.md` [S-23].
- **Implication:** Enumerate every required H2 in exact order, specify optional-section intervals, and derive templates/linter schema from one canonical definition.

#### Finding F-06: The claimed one-to-one mapping lacks a defined mapping unit and a conforming example

- **Synthesized finding:** The framework requires validation items to map one-to-one to execution items but reportedly mixes parent task checkboxes, child actions, tests, documentation, commits, and lifecycle items. The validation example then uses a broad “for each execution Task” confirmation rather than one explicit validation row per executable leaf.
- **Epistemic status:** **Well supported**.
- **Evidence:** Detailed, quoted comparison in R3; R1/R2's concerns about content/placement enforcement are compatible but less specific.
- **Report provenance:** R3; complementary support from R1/R2.
- **Underlying source:** `ipd.md` [S-22].
- **Implication:** Make only executable leaves checkboxes, assign each a unique `E-*` ID, and require exactly one `V-*` item targeting each execution ID.

#### Finding F-07: Execution and validation checkbox semantics are conflated

- **Synthesized finding:** The execution checklist reportedly says items are updated as “completed AND verified,” while the validation checklist is described as the separate evidence pass and warns that a checked box is not proof. These rules permit two incompatible readings: validation already occurred before the execution box was checked, or the execution text incorrectly labels performance as verification.
- **Epistemic status:** **Well supported**.
- **Evidence:** Directly quoted cross-section analysis in R3.
- **Report provenance:** R3 only.
- **Underlying source:** `ipd.md` [S-22].
- **Implication:** Define `E-* checked` as action performed and `V-* checked/pass` as evidence inspected in a later phase.

#### Finding F-08: The terminal lifecycle gate is circular

- **Synthesized finding:** The template reportedly includes terminal status change and `git mv` as an execution item, while requiring every execution and validation item to be complete before transitioning the plan. A literal executor cannot satisfy both requirements.
- **Epistemic status:** **Well supported**.
- **Evidence:** Direct logical comparison of quoted rules in R3.
- **Report provenance:** R3 only.
- **Underlying source:** `ipd.md` [S-22].
- **Implication:** Move lifecycle transition outside the pre-transition bijection and perform it as a post-gate transaction, followed by a post-transition check.

#### Finding F-09: Blocking questions and plan-size rules need explicit state semantics

- **Synthesized finding:** Open questions may remain “before or during execution,” which can allow execution to begin before decisions affecting correctness, security, scope, architecture, or acceptance criteria are resolved. Plan-size guidance combines hedged discretion, numeric thresholds, and “close to REQUIRED,” which can invite arbitrary splitting, padding, or ignoring the rule.
- **Epistemic status:** **Plausible to well supported** as textual risk; behavioral impact is not experimentally established.
- **Evidence:** R3's direct audit; R1 independently identifies numeric over-literalization risk.
- **Report provenance:** R1, R3.
- **Underlying sources:** `ipd.md`, `ipd-spec.md` [S-22, S-23].
- **Implication:** Reject open blocking questions at pre-execution. Treat size thresholds as warnings; require a one-sentence cohesion exception and explicit approval for weak/fast-tier execution.

### Topic 3 — Review and instruction architecture

#### Finding F-10: Review repeats a qualitative rule instead of running a structural preflight

- **Synthesized finding:** `plan-review.md`, `review-rubric.md`, and `03-resolve-and-finalize.md` reportedly repeat “top execution checklist,” “end validation checklist,” and “maps 1:1,” but do not define exact position, identifiers, cardinality, evidence sufficiency, or a mandatory early structural failure. A reviewer can reasonably approve a strong but misplaced checklist.
- **Epistemic status:** **Well supported**.
- **Evidence:** Independent audits in all three reports [S-24–S-26].
- **Report provenance:** R1, R2, R3.
- **Implication:** Run a structural preflight before semantic review and again after edits/finalization. Treat a failed invariant as a distinct structural finding.

#### Finding F-11: Duplicated rubrics and report templates create parity risk

- **Synthesized finding:** The single-file review workflow embeds rubric/report content while the multi-file workflow references standalone files. The supplied reports did not identify a mechanical parity control, and `report-template.md` was unavailable for audit.
- **Epistemic status:** **Plausible to well supported**.
- **Evidence:** R3's architecture audit and missing-dependency note; R1 observes intentional near-verbatim repetition across review-facing files.
- **Report provenance:** R1, R3.
- **Underlying sources:** [S-24–S-26]; missing `report-template.md` [S-27].
- **Implication:** Maintain one canonical rubric and report template, generate embedded copies or compare normalized content in CI, and fail explicitly when a required dependency is unavailable.

#### Finding F-12: Deterministic and semantic review duties should be separated

- **Synthesized finding:** Heading order, uniqueness, ID bijection, permitted checkbox state, and lifecycle location are deterministic. Coverage, evidence adequacy, correctness, and whether an item is meaningfully atomic require semantic judgment. Asking a model to perform both through undifferentiated prose wastes review capacity and leaves deterministic defects probabilistic.
- **Epistemic status:** **Well supported engineering judgment**.
- **Report provenance:** R1, R2, R3, most fully R3.
- **Implication:** Make the linter output an input to semantic review; do not claim that a passing linter makes the IPD correct.

### Topic 4 — Recommended two-phase state model

#### Finding F-13: Separate execution and validation states are the safest default

- **Synthesized finding:** Execution answers whether an action was performed. Validation answers whether independently inspectable evidence supports the expected outcome. Conflating the states encourages confirmation-as-you-go and makes a single checkmark carry two meanings.
- **Epistemic status:** **Well supported** as a state-design conclusion; no direct IPD A/B test exists.
- **Evidence:** Self-correction limitations [S-08], false-completion evidence summarized in R1 [S-15–S-18], and state analysis in R3. R2's unified fallback is a material dissent.
- **Report provenance:** R1, R3; contested by R2.
- **Implication:** Retain two phases. For tiny plans, a single ledger may display action and evidence adjacently, but validation must still occur in a distinct final pass.

#### Finding F-14: The canonical structure should use exact headings, IDs, and evidence fields

- **Synthesized finding:** The best-supported structure is one canonical execution list immediately after `## Goal`, one canonical validation list immediately before the approval gate, unique execution and validation IDs, explicit targets, required/observed evidence, and pass/blocked/failed results.
- **Epistemic status:** **Well supported engineering recommendation**.
- **Report provenance:** R3 directly; R1 and R2 support exact placement and linter enforcement.
- **Recommended contract:**

```markdown
## Goal

<short goal>

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the
action. That mark is not validation.

### <task group>

- [ ] E-01 `<file>` (`<symbol>`): <one observable action>.
  - Depends on: <IDs or none>
  - Expected outcome: <observable result>

<findings, proposed changes, scope, tests, documentation, and questions>

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a
`V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: <falsifiable evidence>
  - Observed evidence: <filled during validation>
  - Result: <pass | blocked | failed>

## Approval and execution gate
```

#### Finding F-15: Phase-local reminders should reference, not fork, canonical state

- **Synthesized finding:** Reintroducing a short rule at execution and validation boundaries may reduce the gap between reading and acting. Repeating the full mutable checklist creates divergence and may backfire for some models/instructions.
- **Epistemic status:** **Plausible** for IPDs; adjacent instruction-following evidence is **well supported**.
- **Evidence:** Robinette et al. [S-06], provider guidance [S-02–S-05], and tool-state inference in R1/R3 [S-19].
- **Report provenance:** R1, R3; compatible with R2's preference for local evidence prompts.
- **Implication:** Use a short immutable phase kernel or have an orchestrator surface the next canonical `E-*` ID. Never maintain two independently editable lists.

### Topic 5 — Minimum tooling and lifecycle contract

#### Finding F-16: The linter should be phase-aware

- **Synthesized finding:** A useful linter must check more than heading offsets. It should understand authoring, review-finalize, pre-execution, pre-transition, and post-transition states.
- **Epistemic status:** **Well supported engineering recommendation**.
- **Report provenance:** R3; R1/R2 support the narrower heading-order check.
- **Minimum checks:**

1. Required H2 headings occur exactly once and in canonical order.
2. The execution heading immediately follows `## Goal`.
3. The validation heading immediately precedes the approval gate.
4. Every executable leaf has one unique `E-*` ID; grouping headings are not executable checkboxes.
5. Every `E-*` has exactly one `V-*` target and every `V-*` target exists.
6. Checkbox/evidence state is permitted for the current lifecycle phase.
7. No blocking question remains at execution start.
8. Terminal transition is not a prerequisite inside the pre-transition bijection.
9. Post-transition status, history, directory, and lifecycle commit agree.

- **Boundary:** The checker must not claim to validate semantic completeness, correct code, truth of pasted evidence, or adequacy of acceptance criteria.

#### Finding F-17: Terminal transition should be an atomic post-gate operation

- **Synthesized finding:** After every reachable execution item is complete and every corresponding validation result passes, the workflow should update history/status, move the IPD, and create the path-scoped lifecycle commit as one finalization transaction, then run a post-transition check.
- **Epistemic status:** **Well supported engineering recommendation**.
- **Report provenance:** R3 only.
- **Implication:** This removes the circular requirement to complete and validate the transition before being allowed to perform it.

### Topic 6 — Capability-tier implications

#### Finding F-18: Capability tier moderates design effects but does not replace controls

- **Synthesized finding:** Weak/fast agents plausibly benefit more from small plans, literal commands, expected outcomes, stable IDs, and tool-mediated next-item surfacing. Strong frontier agents may better reconnect distant sections, but they can still over-literalize contradictory rules, rationalize ambiguity, or falsely self-assess completion. The supplied reports do not justify a monotonic rule that weaker models always have stronger position effects.
- **Epistemic status:** **Well supported directionally**; exact interactions are **unknown**.
- **Evidence:** Model-dependent reinstruction findings [S-06], context/instruction load [S-07], false-success claims [S-15–S-18], and R3's cross-tier caution.
- **Report provenance:** R1, R3; R2's simpler weak-model narrative is not retained as established.
- **Implication:** Apply structural and external-evidence controls to every model tier; tune plan size and local scaffolding rather than relaxing validation for stronger models.

## Unique contributions from individual reports

| Report | Material contribution not substantially covered elsewhere | Evidence quality | Treatment in synthesis |
|---|---|---|---|
| R1 | Identifies natural composition order versus mandated final document order as a plausible cause of drift; distinguishes retrieval from instruction compliance; introduces compliance-gap, false-success, MAST, and external todo-tool evidence; proposes explicit review placement checks and direct A/B tests. | Mixed: strong source caveats and some peer-reviewed sources, but substantial reliance on one unreplicated 2026 preprint and practitioner material. | Integrated in F-01–F-03, F-10, F-15, F-18; exact preprint magnitudes treated as provisional. |
| R2 | Provides the clearest dissent: if tooling is unavailable, merge execution and evidence adjacently for weak models. | Weak for the dissent's causal mechanism; only one external research citation and unsupported chain-of-thought/working-memory assertions. | Preserved in D-02 and as an experimental condition; not adopted as default. |
| R3 | Supplies the most comprehensive file-by-file audit: mapping example defect, checkbox-state conflict, circular lifecycle gate, unresolved-question gate, plan-size semantics, required-source loading, parity risks, relevance boilerplate, exact state model, phase-aware linter, and two-part experiment. | Strong internal analysis and more conservative epistemic labeling; cited external literature remains unvalidated by this synthesis. | Forms F-05–F-18 and the recommended canonical contract. |

## Evidence-quality and source assessment

### Strongest evidence base

1. **Primary framework text [S-22–S-26]:** All reports audited the same five files, and their central quotations about vague placement and review duties agree. This is the most direct evidence for the immediate design defects. R3 provides the most granular cross-file analysis.
2. **Liu et al., TACL 2024 [S-01]:** Peer-reviewed evidence for boundary/middle effects in long-context retrieval. It is authoritative for its tasks but indirect for IPD execution.
3. **Robinette et al., Findings of EACL 2026 [S-06]:** Peer-reviewed adjacent evidence that instruction-following changes over longer conversations and that reinstruction/repeated compliant behavior can help or backfire depending on model and instruction.
4. **Huang et al., ICLR 2024 [S-08]:** Peer-reviewed evidence that intrinsic self-correction without external feedback is unreliable in the tested reasoning settings. It supports external evidence and gates but does not directly test modern coding agents.
5. **Provider guidance [S-02–S-05]:** Direct, current operational evidence for particular model families. The reports appropriately expose that provider recommendations differ; none should be treated as a universal law.

### Evidence limitations

- **Shared-source dependence:** All three reports cite Liu et al. [S-01]. Their agreement on lost-in-the-middle is not three independent empirical confirmations.
- **Task mismatch:** Retrieval, QA, single-turn instruction following, and reasoning self-correction are adjacent to but not identical with iterative coding-agent plan execution.
- **Model/version sensitivity:** Results from older models may not generalize to frontier models available in 2026. Provider tests may not generalize across providers.
- **Unreplicated preprint:** Shin [S-12] supplies striking process-compliance effects and position/content variance claims but is described by R1 as single-author, unreviewed, and unreplicated. Use directionally, not quantitatively.
- **Unvalidated recent sources:** R1 cites several 2025–2026 arXiv papers [S-11, S-15–S-18]. This synthesis did not verify their metadata, methods, or claims.
- **Practitioner evidence:** Todo-tool rationale [S-19, S-20] is product design/practitioner reporting, not a controlled IPD study.
- **Missing primary attachment:** `report-template.md` [S-27] was not available to the auditors, preventing full parity analysis.
- **Original prompt unavailable:** The controlling scope, exact questions, and required deliverables were inferred from the reports.

### Source conflicts or citation concerns

| Concern ID | Source/claim | Concern | Treatment |
|---|---|---|---|
| EC-01 | Anthropic end-placement [S-03–S-05] vs. OpenAI GPT-4.1 beginning/both-boundaries [S-02] | Different providers, models, prompt shapes, and metrics; not a direct contradiction. | Preserve as model/task-specific guidance; recommend early canonical state plus phase-local reminders. |
| EC-02 | Shin position effect [S-12] vs. “Boosting Instruction Following at Scale” [S-13] | Different compliance definitions and experimental shapes; one reports a secondary position effect, the other reportedly no consistent positional relationship. | Conclude that position is task-dependent and secondary, not zero or universal. |
| EC-03 | R2 “CoT forcing prevents hallucination” | No supporting citation, exposes an internal-reasoning mechanism, and claims impossibility too strongly. | Mark unsubstantiated; require observable evidence instead. |
| EC-04 | R2 “tooling prevents drift entirely” | A linter only prevents modeled structural/state defects. | Narrow to near-elimination of checked structural defects. |
| EC-05 | R1 claim that R1's sources were rechecked | This is report-level testimony; no separate validation artifact was supplied. | Record the claim without treating synthesis as independent validation. |
| EC-06 | `[cite: 13]`–`[cite: 17]` in R2 | These identifiers appear to refer to prompt attachments rather than stable public citations. | Normalize to primary framework sources [S-22–S-26]. |

## Gaps and unresolved questions

| ID | Unresolved question or gap | Why unresolved | What evidence would resolve it | Importance |
|---|---|---|---|---|
| G-01 | Which checklist layout minimizes false completion for current coding agents? | No direct comparative IPD study. | Pre-registered, randomized execution experiment with hidden ground truth and captured tool logs. | High |
| G-02 | Does a compact execution-start reminder outperform top placement alone? | Adjacent reinstruction evidence does not test IPDs. | Factorial comparison of top-only vs. top plus immutable reminder, across context lengths and tiers. | High |
| G-03 | Does a unified per-task action/evidence ledger outperform two physical lists for weak/fast models? | R2 recommends it without direct evidence; R1/R3 raise independence concerns. | Weak/fast-model A/B test measuring structural drift, valid completion, and false completion. | High |
| G-04 | How much does a linter improve semantic completion, not merely structure? | Linting directly checks syntax/state, not omitted or wrong tasks. | Compare structural-only, semantic-review-only, and combined conditions against hidden requirements. | High |
| G-05 | Do external todo tools improve fidelity enough to make static position largely irrelevant? | Product rationale and practitioner reports are not controlled evidence. | Same canonical IDs with/without tool-mediated next-item surfacing. | Medium |
| G-06 | Does a separate agent or process for validation materially improve independence? | No report tests validator identity. | Same-agent vs. separate-validator experiment with blinded evidence. | Medium |
| G-07 | Are numeric plan-size limits useful or counterproductive? | Behavioral risk is inferred; no incident or test supplied. | Vary plan size and threshold wording; measure omission, unnecessary splitting, tokens, and human burden. | Medium |
| G-08 | Does `report-template.md` match the embedded template? | File was missing. | Retrieve both canonical sources and run normalized parity comparison. | Medium |
| G-09 | Are nested parent checkboxes consumed by downstream tooling? | Framework runtime behavior was outside supplied scope. | Inspect parser/tool contracts and migration impact. | Medium |
| G-10 | Can the runtime enforce pre-execution and pre-transition hooks reliably? | Orchestrator capabilities were not supplied. | Runtime architecture review and failure-mode tests. | High |

## Recommended controlled experiment

Authoring/review and execution should be tested separately so malformed-plan effects are not confused with executor noncompliance.

### Experiment A — Authoring and review

Randomize otherwise identical work specifications across:

1. Current execution-top/validation-bottom prose.
2. Exact top/bottom invariants without tooling.
3. Execution-bottom layout.
4. Full mutable duplication at both boundaries.
5. Unified action/evidence ledger with a separate final pass.
6. Exact top/bottom plus compact execution-start reminder.
7. Exact top/bottom plus structural linter feedback.

Measure exact heading-order compliance, missing required actions, unique-ID coverage, mapping precision/recall, non-falsifiable validation items, reviewer detection/repair, token use, latency, and human edit burden.

### Experiment B — Execution and false completion

Use only structurally and semantically validated plans. Each fixture should include an easy-to-skip middle action, a test that initially fails for a known reason, an unavailable dependency, a documentation obligation, and a lifecycle/commit requirement. Hidden checks must establish ground truth independently of the agent's report.

The primary endpoint should be false-completion rate: the proportion of runs reporting success or entering terminal state while any required action, evidence item, test, or lifecycle invariant is false. Secondary endpoints should include valid completion, correct stop/report behavior, evidence authenticity, time, tokens, and state divergence.

Cross layout with capability tier, document length, plan size, prose-only versus linter enforcement, and external todo-tool availability. Hold model version and decoding settings constant within comparisons; randomize condition order and fixtures; blind scorers to layout; preserve diffs, command outputs, tool logs, and commits. Thirty trials per cell is an exploratory floor proposed by R3, not a power-justified confirmatory sample. Use pilot results for power analysis and preregister the primary comparison.

## Overall conclusions and implications

### Factual conclusions

1. The supplied research does not establish an optimal checklist placement for current coding agents.
2. The audited framework's placement and mapping language is not exact enough to constitute a deterministic invariant.
3. The review workflow reportedly repeats the ambiguity instead of performing a structural preflight.
4. The supplied reports identify additional internal defects: ambiguous checkbox state, a circular lifecycle gate, blocking-question ambiguity, and parity risks.

### Analytical inferences

1. The observed drift is better explained as an instruction-system defect than as proof of a general model-attention failure. A capable model could reasonably follow a coherent but unintended interpretation.
2. Boundary placement is useful defense in depth, but external evidence, atomic state, and rejectable gates more directly address false completion.
3. One canonical execution list plus phase-local reminders reconciles early framing with act-time recency without creating mutable duplicate state.

### Recommendations

1. **Keep two semantic phases.** Do not collapse “performed” and “validated” into one state.
2. **Make placement exact.** Execution immediately follows `## Goal`; validation immediately precedes the approval gate; each occurs once.
3. **Introduce stable IDs and a bijection.** Each executable `E-*` leaf has exactly one `V-*` row with required evidence, observed evidence, and result.
4. **Implement a phase-aware linter.** Run it at authoring, review, pre-execution, pre-transition, and post-transition.
5. **Use evidence external to model assertion.** Capture literal commands, exit status, relevant output, diffs/artifacts, and lifecycle state where practical.
6. **Repeat only immutable phase controls.** Surface the next canonical ID through an orchestrator/tool if available; do not clone mutable checklists.
7. **Fix lifecycle semantics.** Perform status/history/move/commit only after the pre-transition gate passes.
8. **Resolve blockers before execution.** Permit only explicitly deferred non-blocking questions.
9. **Treat plan-size thresholds as warnings.** Require a cohesion rationale rather than arbitrary splitting.
10. **Test rather than assume.** In particular, test the R2 unified-ledger fallback for weak/fast agents instead of adopting or rejecting it solely from intuition.

## Guidance for downstream agents

### Findings safe to rely on

- The optimal physical layout is not established by the supplied evidence.
- “Near the top/end” should be replaced with exact structural invariants.
- Deterministic structure should be machine-checked.
- A linter complements rather than replaces semantic review.
- Execution state and validation state need distinct meanings.
- Mutable checklist duplication creates source-of-truth risk.
- A checked box without external evidence is not proof of completion.

### Findings requiring qualification or verification

- Top-execution/bottom-validation is a reasonable default, not a proven optimum.
- Phase-local reinstruction is supported by adjacent evidence, not direct IPD trials.
- External todo tooling is promising but not established by controlled IPD evidence.
- Weak/fast models may benefit more from local scaffolding, but capability interactions are not monotonic or fully known.
- The precise framework defects reported in F-05–F-11 should be confirmed against the current versions before editing, because only the dated July 31, 2026 files were audited.

### Claims that should not be repeated as established facts

- “Lost in the middle proves the execution checklist belongs at the top.”
- “Anthropic guidance proves the execution checklist belongs at the bottom.”
- “A final validation checklist prevents premature completion.”
- “Generating evidence forces chain-of-thought and makes hallucinated completion impossible.”
- “A structural linter prevents all checklist drift or false completion.”
- “Weak models necessarily have smaller effective working memory or stronger position effects than frontier models.”
- “The 97%, 75%, 8.9%, or 35.8% compliance figures are replicated universal effects.”

### Recommended retrieval keys

`Implementation Plan Document`; `IPD`; `Detailed Implementation Checklist (TODO)`; `Validation and cross-check`; `execution checklist`; `validation checklist`; `verification checklist`; `two-phase design`; `top/bottom placement`; `read-order`; `act-order`; `primacy`; `recency`; `lost in the middle`; `phase-local reminder`; `E-*`; `V-*`; `bijective mapping`; `falsifiable evidence`; `false completion`; `premature completion`; `structural linter`; `IPD preflight`; `lifecycle gate`; `pre-transition`; `post-transition`; `weak/fast model`; `frontier model`; `ipd.md`; `ipd-spec.md`; `plan-review.md`; `review-rubric.md`; `03-resolve-and-finalize.md`; `report-template.md`; `2026-07-31`.

## Input report manifest

| Report ID | Filename/title | Author/agent if known | Date | Scope | Notable strengths | Notable limitations |
|---|---|---|---|---|---|---|
| R1 | `20260731-checklist-placement-and-instruction-audit-report.sonnet5(2).md` / *Checklist Placement and Instruction Audit: Research Report* | Sonnet 5 (from filename) | 2026-07-31 | Q1 evidence and Q2 audit of five framework files | Strong source caveats; retrieval/compliance distinction; generation-order hypothesis; broad failure and tooling evidence; clear experimental questions | Relies materially on a single-author unreplicated 2026 preprint and practitioner sources; some file-by-file conclusions are less exhaustive than R3 |
| R2 | `20260731-checklist-placement-and-instruction-audit-report.gemini31pro(2).md` / *IPD Checklist Placement and Instruction Audit Report* | Gemini (report); Gemini 3.1 Pro (filename) | 2026-07-31 | Q1 evidence, Q2 audit, alternatives | Concise; clearly surfaces unified-checklist dissent; agrees on linter and reviewer gap | Very limited source base; unsupported CoT, working-memory, and “prevents entirely” claims; overstates primacy transfer and “contradicted in practice” |
| R3 | `20260731-checklist-placement-and-instruction-audit-report.gpt56medium(2).md` / *Checklist Placement and Instruction Audit* | GPT-5.6 medium (filename) | 2026-07-31 | Q1 evidence and detailed file-by-file Q2 audit | Most comprehensive structural/state/lifecycle analysis; conservative epistemic labels; exact canonical contract; phase-aware linter and experiment | No independent source-validation artifact; some conclusions are engineering judgment; `report-template.md` unavailable |

## Consolidated references

The source registry preserves the most complete bibliographic details actually supplied. URLs and metadata were not independently validated during synthesis.

- **S-01.** Liu, Nelson F., et al. “Lost in the Middle: How Language Models Use Long Contexts.” *Transactions of the Association for Computational Linguistics*, 2024. [ACL Anthology PDF](https://aclanthology.org/anthology-files/pdf/tacl/2024.tacl-1.9.pdf); [DOI](https://doi.org/10.1162/tacl_a_00638); preprint arXiv:2307.03172.
- **S-02.** OpenAI. “GPT-4.1 Prompting Guide.” 2025-04-14. [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide).
- **S-03.** Anthropic. “Prompting best practices.” Current documentation as cited 2026-07-31. [Claude documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
- **S-04.** Anthropic. “Long context prompting tips.” Current documentation as cited 2026-07-31. <https://docs.anthropic.com/en/docs/long-context-window-tips>
- **S-05.** Anthropic. “Prompt engineering for Claude's long context window.” 2024. <https://www.anthropic.com/news/prompting-long-context>
- **S-06.** Robinette, Paul, et al. “We Are What We Repeatedly Do: Improving Long Context Instruction Following.” *Findings of EACL 2026*. [ACL Anthology PDF](https://aclanthology.org/2026.findings-eacl.254.pdf).
- **S-07.** Gavin, Maxime, et al. “LongIns: A Challenging Long-context Instruction-based Exam for LLMs.” arXiv:2406.17588, submitted 2024-06-25, revised 2025-08-13. [arXiv](https://arxiv.org/abs/2406.17588).
- **S-08.** Huang, Jie, et al. “Large Language Models Cannot Self-Correct Reasoning Yet.” *ICLR 2024*. [Conference PDF](https://proceedings.iclr.cc/paper_files/paper/2024/file/8b4add8b0aa8749d80a34ca5d941c355-Paper-Conference.pdf).
- **S-09.** HELMET long-context evaluation suite, arXiv:2410.02694. Full bibliographic details were not consistently supplied.
- **S-10.** “Counting-Stars: A Multi-evidence, Position-aware, and Scalable Benchmark for Evaluating Long-Context Large Language Models.” arXiv:2403.11802.
- **S-11.** McKinnon, M. “Retrieval Quality at Context Limit.” arXiv:2511.05850. R1 reports no lost-in-the-middle effect for Gemini 2.5 Flash on its needle-in-a-haystack task.
- **S-12.** Shin, K. S. “The Compliance Gap: Why AI Systems Promise to Follow Process Instructions but Don't.” arXiv:2605.01771, submitted 2026-05-03. [arXiv](https://arxiv.org/abs/2605.01771). R1 describes it as a single-author, unreviewed, unreplicated workshop-track preprint.
- **S-13.** “Boosting Instruction Following at Scale.” arXiv:2510.14842. Full bibliographic details were not supplied.
- **S-14.** Cemri, M., Pan, M. Z., et al. “Why Do Multi-Agent LLM Systems Fail?” MAST taxonomy. [OpenReview PDF](https://openreview.net/pdf?id=fAjbYBmonr).
- **S-15.** “From Confident Closing to Silent Failure: Characterizing False Success in LLM Agents.” arXiv:2606.09863.
- **S-16.** “SHIELDA: Structured Handling of Exceptions in LLM-Driven Agentic Workflows.” arXiv:2508.07935.
- **S-17.** “NL2Repo-Bench: Towards Long-Horizon Repository Generation Evaluation of Coding Agents.” arXiv:2512.12730.
- **S-18.** Additional coding-agent failure-mode studies referenced generically by R1. Bibliographic identity not supplied; do not cite as specific evidence.
- **S-19.** Anthropic. “Todo Lists.” Claude Agent SDK documentation. <https://platform.claude.com/docs/en/agent-sdk/todo-tracking>
- **S-20.** Practitioner reporting on Claude Code TodoWrite/Tasks, cited by R1: dev.to (shinpr, 2026-03-05), aibuilderclub.com (2026-06-11), and spring.io blog (2026-01-20). Direct article URLs were not supplied.
- **S-21.** MIT News. “Unpacking the bias of large language models.” 2025-06-17. <https://news.mit.edu/2025/unpacking-large-language-model-bias-0617>
- **S-22.** `ipd.md`, supplied primary framework material, accessed by the reports 2026-07-31. No external URL supplied.
- **S-23.** `ipd-spec.md`, supplied primary framework material, accessed by the reports 2026-07-31. No external URL supplied.
- **S-24.** `plan-review.md`, supplied primary framework material, accessed by the reports 2026-07-31. No external URL supplied.
- **S-25.** `review-rubric.md`, supplied primary framework material, accessed by the reports 2026-07-31. No external URL supplied.
- **S-26.** `03-resolve-and-finalize.md`, supplied primary framework material, accessed by the reports 2026-07-31. No external URL supplied.
- **S-27.** `report-template.md`, referenced by S-26 but not supplied to the reports. Identity/parity unknown.
- **S-28.** Google. “Long context.” Gemini API documentation, updated 2026-06-22 as reported by R3. [Google AI for Developers](https://ai.google.dev/gemini-api/docs/long-context).
- **S-29.** Anthropic. “Effective context engineering for AI agents.” Current engineering post as cited by R1. <https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents>
- **S-30.** IntuitionLabs. “LLM Position Bias: Primacy and Recency Effects in Prompts.” 2026-04-23. <https://intuitionlabs.ai/articles/llm-position-bias-primacy-recency-effects>. Secondary source; not needed for principal conclusions.

## Provenance crosswalk

| Finding ID | Supporting report(s) | Underlying source(s) | Conflicting report(s) or source(s) | Notes |
|---|---|---|---|---|
| F-01 | R1, R2, R3 | S-01, S-09–S-11, S-21 | R2 overgeneralizes S-01 | Retrieval result retained; IPD transfer labeled unknown. |
| F-02 | R1, R3; partial R2 | S-02–S-05, S-28 | Provider guidance differs by model/task | Supports combined early canonical state and local reminder. |
| F-03 | R1, R2, R3 | S-06–S-08, S-12, S-14–S-18 | R2's unsupported CoT mechanism | Exact ranking not treated as established. |
| F-04 | R1, R2, R3 | S-22, S-23 | None | Core audit consensus. |
| F-05 | R1, R3 | S-23 | None | Confirm against current file before editing. |
| F-06 | R3; complementary R1/R2 | S-22 | Template's aggregate example conflicts with strict mapping | Stable IDs resolve mapping unit. |
| F-07 | R3 | S-22 | None | Unique contribution. |
| F-08 | R3 | S-22 | None | Unique contribution. |
| F-09 | R1, R3 | S-22, S-23 | None | Behavioral severity partly inferred. |
| F-10 | R1, R2, R3 | S-24–S-26 | None | Independent textual convergence. |
| F-11 | R1, R3 | S-24–S-27 | Missing S-27 | Requires parity test. |
| F-12 | R1, R2, R3 | S-22–S-26 | None | Engineering judgment. |
| F-13 | R1, R3 | S-08, S-12, S-14–S-18, S-22 | R2 recommends unified fallback | Preserve dissent as test condition. |
| F-14 | R3; compatible R1/R2 | S-22–S-26 | None | Proposed normative contract, not empirical fact. |
| F-15 | R1, R3; compatible R2 | S-02–S-06, S-19, S-29 | Repetition can backfire in S-06 | Repeat immutable control, not mutable state. |
| F-16 | R3; narrower R1/R2 | S-22–S-26 | None | Scope limits explicitly preserved. |
| F-17 | R3 | S-22 | None | Resolves circular gate. |
| F-18 | R1, R3; partial R2 | S-06, S-07, S-14–S-18 | R2's monotonic weak-model narrative | Exact tier interactions remain unknown. |
