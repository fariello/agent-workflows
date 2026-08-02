# Checklist Placement and Instruction Audit

Date: 2026-07-31  
Scope: `ipd.md`, `ipd-spec.md`, `plan-review.md`, `review-rubric.md`, and `03-resolve-and-finalize.md`

## Evidence labels used in this report

- **ESTABLISHED EVIDENCE** means a finding directly observed in a cited experiment, benchmark, or provider test. It does not mean that the finding has been established for every model or for IPD execution specifically.
- **INFORMED INFERENCE** means an application of established findings to this framework where the exact IPD behavior has not been tested.
- **OPINION / ENGINEERING JUDGMENT** means a design recommendation based on failure containment, simplicity, and auditability rather than a direct experimental result.

No study located for this review directly tests the six IPD checklist layouts in a coding-agent workflow. In particular, there is no direct evidence that moving a verification checklist to the end of an IPD reduces false completion. That important negative finding limits how strongly any placement recommendation can be stated.

## 1. Executive summary

### Direct verdict

The maintainer's intuition that the execution checklist belongs near the top and the validation checklist near the bottom is **unresolved by direct evidence**. It is neither contradicted nor adequately proven.

The arrangement is directionally consistent with two established observations:

1. **ESTABLISHED EVIDENCE:** information at context boundaries is often used more reliably than information in the middle, although the size and shape of this effect vary by model and task.
2. **ESTABLISHED EVIDENCE:** repeating or reintroducing an instruction near the point of use can improve compliance in some long-context settings.

Those observations make top execution plus bottom validation a reasonable default, but they do not show that it is the optimal layout. They also do not show that a final validation checklist prevents false completion. Position is probably a secondary control. Atomic requirements, a stable one-to-one mapping, real evidence, phase-local reminders, and an externally enforced transition gate are more important.

### Single highest-impact change

Create and require a small structural and state linter for IPDs. The linter should assert exact heading order, one execution checklist, one validation checklist, unique execution IDs, a bijective execution-to-validation mapping, permitted checkbox state for the current lifecycle phase, and non-circular transition rules. Run it when an IPD is authored, reviewed, approved for execution, and moved to a terminal directory.

This change is higher impact than moving either checklist because the observed failure was not merely an attention failure. The rule says only "near the top" and "near the end," the examples do not actually implement the promised one-to-one mapping, and the review workflows ask a model to judge the same ambiguous prose. A machine check converts an intention into an invariant.

### Bottom-line design decision

Keep two distinct phases, but restructure them:

- Put `## Detailed Implementation Checklist (TODO)` **exactly once and immediately after `## Goal`**.
- Give every executable leaf a unique ID such as `E-01`. Do not make grouping labels checkboxes.
- Put `## Validation and cross-check` **exactly once and immediately before `## Approval and execution gate`**.
- Give every validation row a unique ID and an explicit target, for example `V-01 validates E-01`, plus an evidence field.
- Tick an execution item after the action is performed. Tick the matching validation item only during the separate evidence pass.
- Repeat only a short, immutable phase-control instruction at execution start and validation start. Do not duplicate the mutable execution checklist.
- Move the terminal status change and `git mv` out of the checklist that must already be complete before that transition. Treat them as a post-gate finalization transaction.

This design is simple enough for weaker agents, explicit enough for strong agents, and machine-checkable.

## 2. Q1: Evidence on placement and ordering

### 2.1 What the evidence establishes

| Finding | Evidence and date | What it supports here | Important limit |
|---|---|---|---|
| Relevant information is often used best at the beginning or end of a long context and less reliably in the middle. | Liu et al., *Lost in the Middle*, TACL 2024. Multi-document question answering and key-value retrieval frequently showed a U-shaped performance curve. | Keeping critical control material out of the middle is prudent. | The tasks were retrieval and question answering, not multi-step coding-agent execution. Models were primarily from 2023. The result does not choose which checklist belongs at which edge. |
| For GPT-4.1 long-context prompting, instructions at both the beginning and end performed better in OpenAI's internal tests than instructions at only one boundary; if placed once, instructions above the context performed better than below. | OpenAI, *GPT-4.1 Prompting Guide*, 2025-04-14. | A concise execution contract at both phase boundaries may help. It weakly favors an early framing instruction when only one copy is possible. | Provider guidance for one model family, not a peer-reviewed checklist experiment. It does not justify maintaining two copies of a mutable checklist. |
| In Anthropic's long-context guidance, putting long documents first and the query or instructions after them improved performance in internal tests, reportedly by as much as 30 percent for some complex multi-document tasks. | Anthropic, *Prompting best practices*, current documentation accessed 2026-07-31. | Recency at the moment of answering or acting can matter, so a phase-local reminder before execution or verification is sensible. | This is query placement around source documents, not checklist placement inside an action plan. Current Anthropic guidance also warns that explicit self-verification can cause newer models to over-verify. |
| Gemini guidance says that in many long-context cases a question placed at the end performs better, while multiple-needle accuracy still varies. | Google, *Long context*, updated 2026-06-22. | A final, explicit validation instruction can benefit from recency. | Provider guidance, not an IPD execution experiment. It concerns a question after context, not a persistent progress tracker. |
| Instruction-following degrades as conversations get longer; repeated compliant behavior in the history and reinstruction can improve later compliance. Repetition can also backfire for some smaller models and instruction types. | Robinette et al., *We Are What We Repeatedly Do*, Findings of EACL 2026. | Reintroducing a compact phase contract near action time is more defensible than relying on one distant instruction. History and execution trajectory matter, not just document position. | The benchmark uses 28 simple, binary, verifiable instructions in multi-turn conversations and older open models. It does not test coding plans. Effects were model- and instruction-dependent. |
| Models can struggle to reason over many instructions well inside their advertised context window. | Gavin et al., *LongIns*, arXiv 2024, revised 2025. | Nominal context capacity is not evidence of reliable compliance. Smaller plans and explicit structure remain useful. | Single-turn instruction reasoning benchmark, not an agent loop or dual-checklist study. |
| Intrinsic self-correction without external feedback often fails or degrades reasoning; apparent gains in prior work often rely on stronger feedback or an oracle. | Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet*, ICLR 2024. | A self-attested checkbox is weak evidence. Test output, repository state, and an external gate are better controls. | Reasoning tasks and older model generations. It does not prove that current coding agents cannot verify their work. |

### 2.2 Serial position and the two IPD phases

**ESTABLISHED EVIDENCE:** long-context models can exhibit both primacy and recency, with degraded use of information in the middle. The effect is not universal, and newer models can be much better than the models in early studies. It remains unsafe to infer that all boundary content receives equal attention or that moving an instruction to a boundary guarantees compliance.

**INFORMED INFERENCE:** the top and bottom of an IPD are sensible locations for phase-control material because they avoid the middle. The execution checklist has a framing function, while the validation checklist has a terminal-gate function. This functional match makes top execution plus bottom validation coherent.

**OPINION / ENGINEERING JUDGMENT:** position should be treated as a defense in depth, not the primary mechanism. The exact location should be specified and linted because "near" is not a testable relation.

### 2.3 Read order versus act order

There are two plausible mechanisms, and the available evidence does not decide between them:

- **Framing or primacy:** an early execution checklist tells the model what the document is for and provides a schema into which later findings, constraints, and tests can be organized.
- **Immediate recency:** a checklist read immediately before action may be more available when the agent starts work.

The current template tries to obtain framing for execution and recency for final verification. That is rational, but it leaves the execution checklist separated from the moment of execution by most of the document.

The simplest resolution is not to move or clone the checklist. Keep one canonical execution checklist near the top and add a compact, identical phase-control block immediately before execution begins. In an interactive agent system, the orchestrator or task tool should surface the next `E-*` item rather than asking the model to remember the whole list.

For stronger models, this extra restatement may have a small benefit and a small token cost. For weaker or faster models, it is more likely to help, provided the restatement is short and does not compete with the canonical checklist. Robinette et al. show that repeated instructions can be model-dependent and can sometimes reduce compliance, so repeating a long or mutable checklist is not a generally safe rule.

### 2.4 Does a last validation checklist prevent premature completion?

No located evidence establishes this causal claim.

**INFORMED INFERENCE:** a final checklist can create a useful second pass because it is recent at completion time and semantically separates doing from proving. It can also fail completely if the same model ticks generic boxes without consulting external state. A checklist that says "confirm every task" is especially vulnerable because one assertion can stand in for many missing actions.

**OPINION / ENGINEERING JUDGMENT:** false-completion control should be evaluated by whether the system makes a false claim difficult, observable, and rejectable, not by where a prose reminder appears. A test log with exit status, a diff, a commit hash, and a linter-checked mapping are stronger than a second set of unchecked boxes.

### 2.5 Ranked drivers of compliance

The ranking below is a synthesis, not a directly measured universal ordering.

| Rank | Driver | Evidence label | Why it outranks placement | Capability-tier notes |
|---:|---|---|---|---|
| 1 | External evidence plus an enforced state-transition gate | **INFORMED INFERENCE**, supported by self-correction research | It prevents a model's assertion from being the only evidence. It can reject missing commands, mappings, or lifecycle state. | Highest value for weak/fast agents; still valuable for frontier agents and nondeterministic failures. It cannot prove semantic correctness by itself. |
| 2 | Atomic, verifiable execution items with stable IDs and a bijective validation mapping | **ESTABLISHED EVIDENCE** for the value of verifiable instructions; **INFORMED INFERENCE** for the exact schema | It removes ambiguous aggregation and makes omissions countable. | Helps all tiers. Over-fragmentation can burden strong agents and humans, so only executable leaves need IDs. |
| 3 | Concrete evidence criteria defined before execution | **INFORMED INFERENCE** | A command, expected result, artifact, or file location makes honest checking possible and fake checking more visible. | Weak agents need literal commands and expected outcomes. Strong agents need discretion to add relevant evidence when the plan cannot predict every detail. |
| 4 | Phase-local re-reading or a short reinstruction at execution and validation start | **ESTABLISHED EVIDENCE** in adjacent long-context tasks; **INFORMED INFERENCE** here | It addresses the read-order versus act-order gap without duplicating mutable content. | Particularly useful for weak/fast tiers. Excessive repetition can backfire and waste context. |
| 5 | A canonical external todo or state tracker mirroring the same IDs | **OPINION / ENGINEERING JUDGMENT** | It keeps current state visible and reduces reliance on long-context memory. | Useful for agents with tools. The IPD must remain usable without the tool, and two independently editable sources must not diverge. |
| 6 | Small, cohesive plans and explicit split criteria | **ESTABLISHED EVIDENCE** that long-context instruction use degrades; **INFORMED INFERENCE** for numeric thresholds | Fewer active obligations reduce omission and state-tracking load. | More important for weak/fast tiers. Blindly enforcing a numeric cap can split cohesive work into harmful fragments. |
| 7 | Clear sequential wording, conflict resolution, and examples that satisfy the rule | **ESTABLISHED EVIDENCE** in provider guidance; **INFORMED INFERENCE** here | Examples are often treated as the operational pattern. A contradictory example can defeat strong prose. | Important for all tiers. Strong models may rationalize ambiguity; weak models may copy it literally. |
| 8 | Boundary placement | **ESTABLISHED EVIDENCE** for attention effects; **INFORMED INFERENCE** for IPDs | It improves salience but does not make completion true or verification independent. | Likely more important as context and instruction count increase. Not reliably monotonic by model size. |
| 9 | Duplicating the full checklist | **ESTABLISHED EVIDENCE** that repetition sometimes helps and sometimes backfires | It creates synchronization and conflict risk, so it ranks last as a general control. | Most dangerous for weak agents when copies differ. Strong agents may spend effort reconciling the copies. |

This ranking intentionally does not claim that weaker models are always more sensitive to physical position. Robinette et al. found some larger tested models showed larger position effects. Capability tier, context length, instruction type, and model training interact.

### 2.6 Alternatives and trade-offs

| Alternative | Strong frontier models | Weak or fast models | Main failure mode | Verdict |
|---|---|---|---|---|
| **1. Execution top, validation bottom** | Coherent phase framing and final gate. A strong model can connect rationale to early tasks. | Keeps both controls at context boundaries, but the execution list may be distant when action begins. | Vague placement, generic validation, and unchecked drift if prose is the only control. | **Keep as the canonical document structure**, with exact positions, IDs, and phase-local reminders. |
| **2. Execution bottom** | Gives immediate recency before action but removes the early schema that should organize the plan. Validation would need another location. | May help immediate action selection, but forces the agent to absorb rationale without a task frame and may crowd the completion gate. | The task plan becomes an afterthought, and the separate verification phase is displaced or merged. | **Do not adopt as the default.** Test it as an experimental condition. |
| **3. Duplicate execution checklist at top and bottom** | May improve salience, but a capable model must reconcile two mutable states. | Two copies can diverge, be ticked inconsistently, or be mistaken for two sets of work. | Source-of-truth conflict and twice the maintenance surface. | **Do not duplicate the mutable checklist.** Repeat only a short immutable control instruction or a reference to the same IDs. |
| **4. Single merged action-and-evidence checklist** | Compact and easy to scan. Appropriate for very small, mechanical plans. | Fewer structures to understand, but it encourages verifying while acting and removes the deliberate second pass. | Confirmation bias and "done means verified" collapse. | **Allow only for tiny plans under an explicit exception.** Retain two phases by default. |
| **5. Restate execution immediately before each action** | Good local context but noisy; can make the agent over-focus on one step and lose global constraints. | Strong local support, especially if a task tool surfaces exactly one next item. | Token growth, inconsistent paraphrases, and repeated prohibitions that can backfire. | **Use tool-generated next-item surfacing, not manually duplicated prose.** Preserve global constraints in a compact fixed kernel. |
| **6. Machine-check and enforce placement/state** | Removes an avoidable class of nondeterministic formatting and lifecycle errors. | Most reliable way to compensate for skipped or misread prose. | A syntactically valid plan can still be semantically wrong, and fabricated evidence can still be pasted. | **Highest-priority change.** Combine with human review and real tool evidence. |

### 2.7 What is established, inferred, and still unknown

**ESTABLISHED EVIDENCE:** boundary position, recency, reinstruction, compliant prior behavior, context length, and instruction verifiability can affect model performance. Effects vary substantially by task and model. Self-review without external feedback is not a dependable substitute for evidence.

**INFORMED INFERENCE:** execution-top plus validation-bottom is a defensible mapping of the two phases to context boundaries. A compact reminder at each point of use should be more robust than relying on physical position alone.

**OPINION / ENGINEERING JUDGMENT:** exact placement and mapping should be enforced by tooling. This is not because tooling makes semantic review unnecessary, but because deterministic properties should not consume probabilistic reasoning capacity.

**UNKNOWN:** whether top/bottom has a lower false-completion rate than bottom/top, top/top, a merged ledger, or a tool-mediated layout for present-day coding agents. The experiment in Section 5 is required to answer that.

## 3. Q2: Audit of the attached instruction set

### 3.1 Attachment and scope status

All five files named as expected attachments in the research prompt were present and reviewed in full.

`03-resolve-and-finalize.md` requires `report-template.md`, but that dependency was not among the expected or supplied attachments. Therefore, parity and consistency of the multi-file workflow's final-report template could not be audited. Other externally referenced project documents, including `AGENTS.md`, `CONTRIBUTING.md`, `.agents/plans/README.md`, and decision records, were outside the supplied scope and were not assumed to agree or disagree.

### 3.2 Cross-file diagnosis

The capable authoring model's placement drift is explainable from the supplied text. Four controls are missing:

1. The placement words are relational but not exact: "near the top," "near the BEGINNING," "near the end," and "near the END."
2. `ipd-spec.md` calls section order canonical but does not enumerate a complete ordered heading sequence.
3. The template's validation example does not implement the promised one-to-one mapping. One aggregate validation item stands in for every execution task.
4. Review repeats the same qualitative rule but performs no deterministic heading-order, ID, or cardinality check.

This is not evidence that the model ignored a perfectly specified rule. The rule permits judgment, the example contradicts its strongest interpretation, and the reviewer has no objective test. A strong model can interpret "near" semantically and place the checklist elsewhere while believing the document remains coherent. A weak model can simply copy the aggregate example.

### 3.3 `ipd.md` audit

#### IPD-01: Placement is not an invariant

**Quoted text, lines 51 and 57:** "placed near the top" and "near the end."

**Risk:** Neither phrase defines adjacency, permitted intervening sections, heading count, or uniqueness. It cannot be linted as written. Repetition in other files does not remove the ambiguity.

**Recommended replacement, combination of template structure, prose, and tooling:**

```markdown
`## Detailed Implementation Checklist (TODO)` MUST occur exactly once and MUST be
the first H2 section after `## Goal`; no other H2 section may intervene.

`## Validation and cross-check` MUST occur exactly once and MUST immediately precede
`## Approval and execution gate`; no other H2 section may intervene.

The IPD structural check MUST reject a missing, duplicate, or out-of-order required heading.
```

Keep the headings in those exact locations in the template. Add a linter assertion rather than relying on authors to infer "near."

**Tier impact:** All tiers benefit. There is no meaningful loss of discretion because section position is a formatting invariant, not a reasoning choice.

#### IPD-02: The example violates the stated one-to-one contract

**Quoted text, lines 129 to 132:** "Each item maps 1:1 to a `## Detailed Implementation Checklist (TODO)` item."

**Conflicting example, line 138:** "For each execution Task above: CONFIRM it was performed."

**Risk:** The execution example contains parent task boxes, child action boxes, tests, documentation, commit, and lifecycle items. The validation example contains five broad boxes. There is no defined unit of mapping and no bijection. A single generic confirmation can hide a missed child action.

**Recommended structural replacement:** Make only executable leaves checkboxes and assign stable IDs. Group labels are plain text.

```markdown
### Task 1: <short title>

- [ ] E-01 Edit `<file>` (`<symbol>`): <exact change and preserved invariant>.
- [ ] E-02 Add `<test_name>` in `<test_file>`: <expected outcome>.
- [ ] E-03 Run `<literal command>`; retain stdout, stderr, and exit status.
```

Then require one validation row per execution ID:

```markdown
- [ ] V-01 validates E-01
  - Required evidence: `<diff or file:line>`
  - Observed evidence: `<fill during validation>`
  - Result: `<pass | blocked | failed>`
- [ ] V-02 validates E-02
  - Required evidence: `<test file:line>`
  - Observed evidence: `<fill during validation>`
  - Result: `<pass | blocked | failed>`
- [ ] V-03 validates E-03
  - Required evidence: `<command, exit status, actual output or artifact path>`
  - Observed evidence: `<fill during validation>`
  - Result: `<pass | blocked | failed>`
```

The linter should reject duplicate execution IDs, missing validation targets, duplicate validation targets, and validation targets that do not exist.

**Tier impact:** Especially important for weak/fast agents. Strong agents also benefit from an auditable definition of completeness. Excessive fragmentation would backfire, so headings and explanatory bullets should not receive IDs.

#### IPD-03: Execution and verification checkbox semantics are conflated

**Quoted text, lines 51 to 52:** the execution checklist is "updated in place as each item is completed AND verified."

**Quoted text, lines 56 to 58:** "A ticked box is a claim, not proof" and the end checklist "is the evidence pass."

**Risk:** If the execution box can be ticked only after verification, the supposed separate verification phase has already occurred. If it is ticked when work is merely performed, "completed AND verified" is false. Agents can choose either reading.

**Recommended prose replacement:** 

```markdown
Execution-state rule: mark `E-*` complete when the described action has been performed.
Do not treat that mark as validation. After all reachable `E-*` items have been attempted,
begin a separate validation pass. Mark `V-*` complete only after inspecting the required
evidence. If any execution item is blocked, failed, skipped, or lacks evidence, leave its
validation item unchecked, record the actual state, and stop before terminal transition.
```

**Tier impact:** Helps all tiers. Newer models that already self-verify should not be told to repeat gratuitous reasoning. The rule asks for external evidence inspection, not a verbose chain-of-thought exercise.

#### IPD-04: The lifecycle gate is circular

**Quoted execution item, lines 68 to 70:** "Set terminal `Status:` and `git mv` this plan to the right terminal dir."

**Quoted gate, lines 149 to 153:** before "transitioning this plan to `executed/`, EVERY" execution item and its validation item must already be complete.

**Risk:** Terminal transition is itself an execution checkbox, but all execution checkboxes must be complete before terminal transition. The validation example also requires lifecycle completion before the transition. A literal agent cannot satisfy the gate. A pragmatic agent must violate or reinterpret it. A commit before moving the plan can also leave the status and move uncommitted.

**Recommended structural replacement:** Remove terminal transition from the pre-transition execution/validation bijection. Define a finalization transaction after the gate:

```markdown
Pre-transition gate:
1. Every `E-*` item is complete.
2. Every `V-*` item is complete with observed evidence and a passing result.
3. The IPD structural/state check passes for phase `pre-transition`.

After the gate passes, perform the terminal transition as one finalization transaction:
1. Append the workflow-history entry and set terminal `Status:`.
2. `git mv` the IPD to the required terminal directory.
3. Create a path-scoped lifecycle commit containing the status/history update and move.
4. Report the lifecycle commit hash. Never push.
```

A post-transition check can confirm directory, status, history, and commit state. It must not be a prerequisite for the transition it verifies.

**Tier impact:** Essential for literal strong agents and weak agents that otherwise choose an arbitrary shortcut.

#### IPD-05: Blocking open questions are not barred at execution start

**Quoted text, lines 122 to 125:** "Anything needing a human decision before or during execution."

**Risk:** "During execution" permits an agent to start with unresolved correctness, security, architecture, or scope decisions. The review workflow distinguishes blocking questions, but the executable IPD gate does not state the same rule locally.

**Recommended prose and linter rule:** 

```markdown
Execution may begin only when every question that can change correctness, security,
scope, architecture, or acceptance criteria is resolved in the IPD. A non-blocking
question may remain only if it is explicitly marked `DEFERRED`, has an owner or trigger,
and cannot change any `E-*` or `V-*` item in this plan.
```

The pre-execution check should reject an `OPEN` blocking question.

#### IPD-06: Size guidance mixes discretion with near-mandatory language

**Quoted text, lines 157 to 166:** "strong guidance, not an inflexible rule," numeric ranges, and "close to REQUIRED when the executing model is a faster/weaker tier."

**Risk:** "Close to REQUIRED" has no normative meaning. A strong agent may over-literalize the numeric counts and split a cohesive change. A weak agent may ignore the entire paragraph because it begins as guidance. "Major step" and "actionable checklist item" are also not defined consistently with nested boxes.

**Recommended replacement, prose plus warning-level tooling:**

```markdown
Plan-size policy: prefer at most 5 task groups and at most 18 executable `E-*` leaves.
Exceeding either threshold is a review warning, not an automatic failure. The author MUST
either (a) split the work when it contains independently executable phases or distinct
concerns, or (b) record a one-sentence cohesion reason for keeping one plan. For a weak/fast
execution tier, the reviewer MUST explicitly approve the exception before execution.
```

This preserves discretion while making the decision observable.

### 3.4 `ipd-spec.md` audit

#### SPEC-01: The canonical specification does not specify a complete order

**Quoted text, lines 22 to 25:** a partial section list followed by a checklist "placed near the BEGINNING" and validation "placed near the END."

**Risk:** The document says it defines section order, but it does not enumerate the full sequence. The two checklist headings are described separately from the partial list. A model can reasonably append the execution checklist to the end and still claim it is present.

**Recommended replacement:** Add an exact ordered list of required H2 headings:

```markdown
Required H2 order, with each heading occurring exactly once:
1. `## Workflow history`
2. `## Goal`
3. `## Detailed Implementation Checklist (TODO)`
4. `## Project conventions discovered (Step 0)`
5. `## Findings`
6. `## Proposed changes (ordered, validatable)`
7. `## Deferred / out of scope (with reason)`
8. `## Scope check`
9. `## Required tests / validation`
10. `## Spec / documentation sync`
11. `## Open questions`
12. `## Validation and cross-check (verify before reporting done)`
13. `## Approval and execution gate`
```

If optional sections are intended, explicitly mark them and define their permitted interval. Generate the linter's ordered schema and the template from one canonical definition where practical.

#### SPEC-02: "Single entry point" and "by reference" can be misread

**Quoted text, line 7:** "This is the single entry point" and "CONSOLIDATES the conventions by REFERENCE ... it does not restate or fork them."

**Risk:** The document is an index, not a self-contained execution contract. That may be intentional, but a model can read "single entry point" as sufficient authority without loading every referenced file. The supplied material cannot establish whether a loader always provides those dependencies.

**Recommended replacement:** 

```markdown
This file is the mandatory index, not a self-contained execution contract. Before
authoring, reviewing, or executing an IPD, the agent MUST load the template and every
applicable authoritative source listed below. If any required source is unavailable or
conflicts with another, STOP and report the missing source or conflict. Do not infer the rule.
```

Add a machine-readable manifest of required source paths and versions if the framework controls loading.

#### SPEC-03: The mapping, checkbox-state, lifecycle, and size defects are duplicated

Lines 23 to 37 repeat the same ambiguous one-to-one rule, hard gate, and "close to REQUIRED" size guidance found in `ipd.md`. Repetition does not create clarity and creates parity risk.

**Recommended structural change:** Make `ipd-spec.md` own normative semantics and make `ipd.md` an example generated or tested against them. Define ID mapping, checkbox states, and lifecycle phases once. If prose must be duplicated for portability, add a synchronization test or embedded block version/hash.

### 3.5 `plan-review.md` audit

#### REVIEW-01: Review has no structural preflight

**Quoted text, lines 259 to 265:** the reviewer assesses both checklists, determines that validation "maps 1:1," and treats a weak checklist as under-scope.

**Repeated text, lines 357 to 359:** the rubric again asks for "a top execution checklist AND an end verification/cross-check checklist."

**Risk:** "Top," "end," and "maps 1:1" remain judgment calls. The rule appears after broad semantic review and again at finalization, so a reviewer can spend most of its context before reaching the deterministic defect. No instruction says that out-of-order headings are necessarily a finding.

**Recommended new subsection before semantic review:** 

```markdown
### 2.0 IPD structural preflight

For every agent-executable IPD, run the canonical IPD check before applying the
engineering rubric. The check MUST verify:
1. every required heading occurs exactly once and in the canonical order;
2. the execution heading immediately follows `## Goal`;
3. the validation heading immediately precedes the approval gate;
4. every executable leaf has one unique `E-*` ID;
5. every `E-*` ID has exactly one `V-*` item and every `V-*` target exists;
6. checkbox state is permitted for the plan lifecycle phase;
7. no blocking open question remains at execution start;
8. terminal transition is outside the pre-transition execution/validation bijection.

If a check fails, record an `UNDER-SCOPE` finding and repair it before the plan can pass.
If the checker cannot run, perform the same checks explicitly and report that machine
verification was unavailable.
```

This should be early because it is cheap, deterministic, and prevents later review from operating on an invalid plan shape.

#### REVIEW-02: A memory kernel is useful but self-enforced

**Quoted text, lines 30 to 39:** "Re-read this before each step" followed by nine rules.

**Risk:** This is a reasonable recency device, but no mechanism confirms the reread, and the kernel omits the exact checklist invariant. It also demonstrates that the workflow already accepts phase-local restatement, making the absence of checklist structure from the kernel more consequential.

**Recommended change:** Keep the compact kernel and add one line:

```markdown
10. For each agent-executable IPD, pass the structural preflight before semantic review
and again before finalization; do not infer placement or one-to-one mapping from prose.
```

An orchestrator should inject the kernel at each step boundary if available. Do not duplicate the full workflow.

#### REVIEW-03: Checklist enforcement is repeated but not operationalized

The same requirement appears in finalization at lines 259 to 265 and the embedded rubric at lines 357 to 359. Both are qualitative. Repetition raises instruction volume without adding a check.

**Recommended change:** Replace both long copies with a reference to the structural preflight result and a short semantic duty:

```markdown
Confirm the IPD structural preflight passed. Then assess semantic coverage: every required
action, decision, deliverable, and validation must be represented by an `E-*` leaf, and each
`V-*` item must demand evidence capable of disproving completion, not merely a confirmation.
```

This separates syntactic bijection, which a tool can prove, from semantic completeness, which still needs review.

#### REVIEW-04: Embedded and standalone rubrics can drift

`plan-review.md` contains an engineering rubric while the multi-file variant supplies `review-rubric.md`. Their checklist provisions are similar but not mechanically tied in the supplied files.

**Risk:** Future edits can harden one variant but not the other. The prompt states that they are kept in parity, but no parity mechanism is visible.

**Recommended tooling change:** Maintain one canonical rubric source. Generate the embedded single-file block and standalone file from it, or compare normalized blocks in CI. A version string is helpful for diagnosis but is weaker than content comparison.

#### REVIEW-05: Relevance handling can invite boilerplate

The single-file workflow says to "Apply all required views" at lines 132 to 139. The standalone rubric says "Apply only relevant items. `Not applicable` requires a reason" at line 3.

**Risk:** A literal strong model may produce an `N/A` explanation for every irrelevant bullet, expanding the review and burying material findings. A weak model may treat broad views as a box-ticking exercise.

**Recommended replacement:**

```markdown
Triage rubric sections for relevance once per plan. For each wholly inapplicable section,
record one concise reason. Do not produce an `N/A` statement for every bullet. Apply every
relevant bullet and cite evidence for every resulting finding.
```

### 3.6 `review-rubric.md` audit

#### RUBRIC-01: The rubric inherits the central ambiguity

**Quoted text, lines 21 to 24:** "a top execution checklist AND an end verification/cross-check checklist that maps 1:1."

**Risk:** The reviewer has no definition of top, end, mapping unit, uniqueness, or evidence sufficiency. It can approve the template's own aggregate example even though that example is not a one-to-one row mapping.

**Recommended replacement:**

```markdown
For an agent-executable IPD, require a passing canonical IPD structural check. Separately
verify semantic coverage: each executable `E-*` leaf describes one observable action; each
matching `V-*` item names that ID and requires concrete evidence that could reveal failure.
Generic items such as "confirm every task" do not satisfy this requirement.
```

#### RUBRIC-02: `Not applicable` granularity is undefined

**Quoted text, line 3:** "Apply only relevant items. `Not applicable` requires a reason."

**Risk:** It is unclear whether every bullet or each section needs a reason. This can cause either excessive boilerplate or silent skipping.

**Recommended replacement:** Use the relevance-triage text from REVIEW-05 and require one reason per wholly inapplicable section.

### 3.7 `03-resolve-and-finalize.md` audit

#### FINAL-01: Structural assessment happens too late and is still qualitative

**Quoted text, lines 64 to 68:** finalization confirms that both checklists exist and validation "maps 1:1."

**Risk:** A structural defect can survive until finalization, and the finalizer repeats the same ambiguous judgment that should have been resolved earlier.

**Recommended change:** Require a stored or freshly produced strict preflight result at lines 54 to 68:

```markdown
- the canonical IPD structural check passes for phase `review-finalize`;
- semantic checklist coverage was assessed during review and no unresolved checklist finding remains;
```

Keep semantic checking in the review step. Re-run deterministic checks at finalization because edits made while resolving questions can reintroduce structural defects.

#### FINAL-02: The exit gate is model-attested

**Quoted text, lines 128 to 138:** seven checkboxes assert completion, report shape, and literal final-output ordering.

**Risk:** The exit checklist is useful as an operator summary but cannot establish its own truth. Some items, such as "Nothing follows," are mechanically testable. Others, such as consistent verdict and readiness, can be partially validated by a state table.

**Recommended combination:** Keep the human-readable exit list, but auto-check report heading order, required ledger coverage, allowed verdict/readiness combinations, and that the final enumeration is last. Require tool output or an explicit "checker unavailable" result.

#### FINAL-03: An unavailable dependency prevents a complete parity audit

**Quoted text, lines 121 to 126:** "Read `report-template.md` in full and use it exactly."

`report-template.md` was not supplied. This is not necessarily a framework defect, because it was not listed as an expected attachment. It is an audit limitation. The single-file report template at `plan-review.md` lines 412 to 464 cannot safely be assumed identical to the missing file.

**Recommended tooling change:** Add a parity test between the single-file embedded report template and `report-template.md`, just as for the rubric. At runtime, fail explicitly if a required workflow part is unavailable.

### 3.8 Assessment of the two-checklist design

The design is **sound in intent but under-specified in representation and lifecycle**.

It is not inherently over-engineered. Execution and verification are different states:

- execution asks whether an action was performed;
- validation asks whether concrete evidence supports the expected result.

Merging them by default would make confirmation-as-you-go more likely and weaken the deliberate second pass. The current implementation, however, duplicates concepts without a stable mapping, so it gets the cost of two checklists without the full audit benefit.

Recommendation: keep the two phases, simplify the data model, and make it checkable. Use one execution leaf per observable action, one validation row per execution ID, and one short phase-control block. For a tiny plan with only a few mechanical actions, a merged action/evidence ledger may be allowed, but only if the workflow still requires a separate final pass over the evidence column.

## 4. Consolidated recommendation

### 4.1 Canonical placement and structure

Adopt this normative contract:

```markdown
## Goal

<short goal>

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action.
That mark is not validation. Work in ID order unless an item's dependency says otherwise.

### <task group>

- [ ] E-01 `<file>` (`<symbol>`): <one observable action>.
  - Depends on: <IDs or none>
  - Expected outcome: <observable result>
- [ ] E-02 Run `<literal command>`.
  - Depends on: E-01
  - Expected outcome: <exit status and material output>

<findings, changes, scope, tests, documentation, and questions>

## Validation and cross-check (verify before reporting done)

Validation-state rule: re-open the execution list and inspect evidence in a separate pass.
Do not mark `V-*` complete from memory or from the corresponding execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: <diff, file:line, artifact, or other falsifiable evidence>
  - Observed evidence: <filled during validation>
  - Result: <pass | blocked | failed>
- [ ] V-02 validates E-02
  - Required evidence: command, exit status, and actual output or retained output path
  - Observed evidence: <filled during validation>
  - Result: <pass | blocked | failed>

## Approval and execution gate

<approval, pre-execution, pre-transition, and post-transition rules>
```

The words "immediately after" and "immediately before" must replace every normative use of "near the top," "near the beginning," "near the end," and "near the END."

### 4.2 State model

Use these distinct states:

| State | Meaning | Who or what verifies it |
|---|---|---|
| `E-*` unchecked | Action not yet performed, or its actual state is unresolved | Executor |
| `E-*` checked | Action was performed | Executor plus repository/tool trace where available |
| `V-*` unchecked | Evidence has not passed the separate validation pass | Validator |
| `V-*` checked with `Result: pass` | Required evidence was inspected and matched the expected outcome | Validator plus captured evidence |
| `V-*` unchecked with blocked/failed note | Work is incomplete and terminal transition is barred | Gate |
| Terminal transition complete | Status/history, move, and lifecycle commit were performed after the pre-transition gate | Post-transition checker |

Do not make terminal transition an `E-*` item whose completion is required before transition. It is the transaction authorized by the successful gate.

### 4.3 Minimum tooling contract

A small parser is sufficient. It need not use an LLM. It should report precise failures and nonzero exit status for:

1. missing, duplicate, or out-of-order required H2 headings;
2. execution heading not immediately after Goal;
3. validation heading not immediately before the approval gate;
4. missing or duplicate `E-*` and `V-*` IDs;
5. a non-bijective `E-*` to `V-*` mapping;
6. an executable checkbox without an ID;
7. invalid checkbox/evidence state for authoring, review, pre-execution, pre-transition, or post-transition phase;
8. open blocking questions at execution start;
9. status, directory, history, and lifecycle-commit inconsistencies.

Illustrative invocations could be `ipd-lint --phase author`, `--phase review-finalize`, `--phase pre-execution`, `--phase pre-transition`, and `--phase post-transition`. The command name is not important. The shared phase semantics are.

The checker should not pretend to validate semantic coverage, code correctness, or evidence authenticity. Reviewers still decide whether every required action is represented and whether evidence could actually disprove a false completion claim. Command capture should record the literal command, exit status, and output artifact so that the agent is not the sole source of truth.

### 4.4 Instruction architecture

1. Make `ipd-spec.md` the normative semantic source.
2. Generate or test `ipd.md` against its heading schema and ID rules.
3. Put the structural preflight before semantic review in both plan-review variants.
4. Maintain one canonical rubric and one canonical report template, with generated single-file copies or parity tests.
5. Keep a compact phase kernel and have an orchestrator re-present it at action boundaries when possible.
6. Keep size thresholds as warnings with an explicit exception record, not pseudo-mandatory prose.

This combination is optimized for weak/fast agents without forcing strong agents to narrate needless self-reflection. It reserves model judgment for semantic questions and uses deterministic checks for deterministic properties.

## 5. Open questions and experiments

### 5.1 Primary controlled experiment

The decisive study should test authoring compliance and execution honesty separately. Combining them would make it impossible to tell whether a bad execution came from a malformed authored plan or from an executor ignoring a correct plan.

#### Experiment A: IPD authoring and review

Randomly assign otherwise identical source material to these layouts or rule variants:

1. execution top, validation bottom;
2. execution bottom, validation after it;
3. mutable execution checklist duplicated top and bottom;
4. merged action/evidence ledger;
5. canonical top checklist plus a compact execution-start restatement;
6. canonical top/bottom layout plus structural linter feedback.

Measure:

- exact heading-order compliance;
- number of missing required actions;
- proportion of executable leaves with unique IDs;
- execution-to-validation mapping precision and recall;
- generic or non-falsifiable validation items;
- reviewer detection and repair rate;
- tokens, latency, and human edit burden.

#### Experiment B: Execution and false completion

Use validated plans with hidden ground truth. Each fixture should contain:

- multiple code edits with at least one easy-to-skip middle action;
- a test that initially fails for a known reason;
- one deliberately blocked or unavailable dependency;
- a documentation or spec-sync obligation;
- a path-scoped commit requirement;
- hidden checks that identify whether each edit and command actually occurred.

The main endpoint should be **false-completion rate**: the fraction of runs that report success or enter terminal state while at least one required action, test, evidence item, or lifecycle invariant is false. Secondary endpoints should include task recall, valid completion, correct stop-and-report behavior, evidence authenticity, time, and token cost.

#### Experimental factors

Cross layout with:

- at least one strong frontier tier, one fast commercial tier, and one smaller open or local tier;
- short, medium, and long document conditions;
- small and threshold-exceeding plan sizes;
- prose-only versus linter-enforced transition;
- execution with and without an external todo tool.

Use the same model version and decoding settings within each comparison, randomize fixtures and condition order, and run enough independent trials to estimate rare false-completion events. Thirty trials per cell is a minimal exploratory floor; a power analysis based on pilot failure rates should set the confirmatory sample. Blind the scorer to layout. Preserve tool logs, diffs, command output, and commits as independent ground truth.

Pre-register top/bottom versus the strongest competing layout as the primary comparison. Fit a model with layout, capability tier, context length, plan size, and their key interactions. Do not pool all models into one headline rate if interactions are large.

### 5.2 Key hypotheses to test rather than assume

1. A compact execution-start restatement will outperform physical top placement alone, especially as the rationale section grows.
2. Linter-enforced structure will nearly eliminate placement and mapping defects but will not eliminate semantic omissions.
3. Concrete evidence capture and an enforced gate will reduce false completion more than checklist position.
4. Full-checklist duplication will improve recall in some cells but increase state inconsistency, especially for weaker agents.
5. A merged checklist will be competitive on tiny mechanical plans and worse on plans that require an independent regression or integration pass.
6. Capability tier will interact with layout, but the direction will not be monotonic across every instruction type.

### 5.3 Remaining document questions

- Is every IPD always rendered from `ipd.md`, or can an author work from `ipd-spec.md` alone? The answer determines how much normative structure the spec must restate.
- Does the runtime have a reliable hook before execution and terminal transition? If yes, enforcement belongs there. If not, repository CI or a pre-commit check should provide the backstop.
- Is a separate agent ever used for validation? Separation would improve independence, but it is not required for the proposed evidence schema.
- Are nested parent checkboxes currently used by downstream tooling? If so, migration must distinguish grouping state from executable leaf state without creating duplicate validation obligations.
- Does the missing `report-template.md` exactly match the embedded single-file template? This needs a parity check, not an assumption.

## 6. Sources

All URLs were accessed on 2026-07-31.

1. Liu, Nelson F., et al. "Lost in the Middle: How Language Models Use Long Contexts." *Transactions of the Association for Computational Linguistics*, 2024. [ACL Anthology PDF](https://aclanthology.org/anthology-files/pdf/tacl/2024.tacl-1.9.pdf). DOI: [10.1162/tacl_a_00638](https://doi.org/10.1162/tacl_a_00638).
2. OpenAI. "GPT-4.1 Prompting Guide." Published 2025-04-14. [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/gpt4-1_prompting_guide).
3. Anthropic. "Prompting best practices." Current Claude documentation. [Anthropic documentation](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
4. Google. "Long context." Gemini API documentation, updated 2026-06-22. [Google AI for Developers](https://ai.google.dev/gemini-api/docs/long-context).
5. Robinette, Paul, et al. "We Are What We Repeatedly Do: Improving Long Context Instruction Following." *Findings of the Association for Computational Linguistics: EACL 2026*, 2026. [ACL Anthology PDF](https://aclanthology.org/2026.findings-eacl.254.pdf).
6. Gavin, Maxime, et al. "LongIns: A Challenging Long-context Instruction-based Exam for LLMs." arXiv:2406.17588, submitted 2024-06-25, revised 2025-08-13. [arXiv record](https://arxiv.org/abs/2406.17588).
7. Huang, Jie, et al. "Large Language Models Cannot Self-Correct Reasoning Yet." *International Conference on Learning Representations*, 2024. [ICLR paper PDF](https://proceedings.iclr.cc/paper_files/paper/2024/file/8b4add8b0aa8749d80a34ca5d941c355-Paper-Conference.pdf).

### Supplied primary materials

The following verbatim attachments were audited as primary framework evidence. They have no external URL in the supplied material:

1. `ipd.md`, accessed 2026-07-31.
2. `ipd-spec.md`, accessed 2026-07-31.
3. `plan-review.md`, accessed 2026-07-31.
4. `review-rubric.md`, accessed 2026-07-31.
5. `03-resolve-and-finalize.md`, accessed 2026-07-31.

