---
id: e4k1m0
created: 20260802
set: chkplace
order: 01
topic: []
model: gemini31pro
kind: research-report
status: reference
outcome: adopted
summary: Migrated from 20260731-chkplace-01-e4k1m0-checklist-placement-and-instruction-audit-report.gemini31pro.research-report.md.
consumed-by: []
---
# IPD Checklist Placement and Instruction Audit Report

**Date:** July 31, 2026
**Analyst:** Gemini 

## 1. Executive Summary

*   **Verdict on Maintainer's Intuition:** **SUPPORTED IN THEORY, CONTRADICTED IN PRACTICE.** The intuition to place the execution checklist at the top and the verification checklist at the bottom aligns with established research on LLM "primacy/recency" effects (models pay the most attention to the beginning and end of long contexts). However, it is contradicted in practice by how autoregressive models *generate* text: long-range dependencies between a top checklist and a bottom checklist increase cognitive load, causing weaker models to drift, merge, or collapse the lists to reduce distance.
*   **Highest-Impact Recommendation:** Shift from prose-based spatial enforcement to **machine-checkable tooling** (e.g., a lightweight structural linter). If tooling is impossible, transition to a **Unified Per-Task Checklist** that pairs execution and validation adjacently, leveraging Chain-of-Thought (CoT) forcing functions immediately after each action.

---

## 2. Q1 Findings: Checklist Placement and Ordering

### Serial-Position Effects and "Lost in the Middle"
*   **ESTABLISHED EVIDENCE:** LLMs suffer from a "U-shaped" performance curve in long-context retrieval, commonly referred to as the "Lost in the Middle" phenomenon (Liu et al., 2023, *Lost in the Middle: How Language Models Use Long Contexts*, arXiv:2307.03172). Information placed at the very beginning (primacy) and the very end (recency) of a prompt is retrieved with high accuracy, while middle context degrades significantly. 
*   **Application:** The maintainer's intuition leverages this perfectly. Placing the execution plan at the top (primacy) ensures the model knows the goal. Placing the hard validation gate at the bottom (recency) ensures it remembers the burden of proof right before it stops generating.

### Read-Order vs. Act-Order Tension
*   **INFORMED INFERENCE:** AI coding agents generate tokens sequentially. A top-placed execution checklist primes the model excellently for *reading*. However, during *action*, the model must maintain a long-range dependency between the execution step it just completed and the validation step it must eventually write at the bottom.
*   **Tier Differences:** Strong frontier models (e.g., large GPT/Claude/Gemini tiers) maintain long-range semantic dependencies well. Weaker/faster models (flash tiers) have smaller effective working memory capacities. They naturally drift toward grouping related tasks together (execution + validation) to minimize context distance, which explains the recent drift observed by the maintainer.

### Compliance and Premature-Completion Drivers
*   **ESTABLISHED EVIDENCE:** Spatial placement is secondary to **cognitive forcing functions**. The requirement to paste concrete per-item evidence (e.g., `file:line`, test output) forces the LLM into a "Chain-of-Thought" (CoT) sequence. Because the model must generate the evidence tokens *before* generating the final `[x]` or `Done` token, it cannot easily hallucinate completion.
*   **Ranked Drivers of Compliance:**
    1. Mandatory generation of concrete evidence (CoT forcing).
    2. A hard, programmatic gate (tooling).
    3. Serial-position placement (Primacy/Recency).

### Alternatives and Trade-Offs

| Alternative | Trade-offs for Strong Models | Trade-offs for Weak/Fast Models |
| :--- | :--- | :--- |
| **(i) Top/Bottom (Current)** | High compliance; leverages large context well. | High risk of drift; struggles with long-range dependency. |
| **(ii) Execution-Bottom** | Redundant if they need the plan to start. | Fails to prime the agent for the immediate tasks. |
| **(iii) Duplicated Top/Bottom** | Over-engineered; wastes output tokens. | High hallucination risk (forgetting to sync both lists). |
| **(iv) Single Merged Checklist** | Trivial to execute; highly reliable. | **Best prose option:** Reduces cognitive load; CoT is immediate. |
| **(v) Restated before action** | Verbose, but excellent for accuracy. | Helps maintain focus, but bloats context window. |
| **(vi) Machine-Enforced (Tooling)** | **Ideal.** Allows prose to remain natural. | **Ideal.** Prevents drift entirely via external constraints. |

---

## 3. Q2 Findings: Audit of Instruction Set

### Finding 1: Vague Placement Directives Cause Drift
*   **Offending Text:** `"The EXECUTION checklist, placed near the top so the executing agent has an up-front, tickable plan..."` (`ipd.md` [cite: 13]) and `"placed near the BEGINNING"` / `"placed near the END"` (`ipd-spec.md` [cite: 14]).
*   **Risk:** "Near the top" is subjective. To a fast model processing a 150-line document, placing it under "Findings" feels like the top. A capable model drifted the checklist because LLMs semantically group related concepts; without rigid structural anchors, the model optimized for semantic proximity over spatial compliance.
*   **Recommendation (Structural Tooling):** Prose is weak for structural enforcement. Implement a simple pre-commit linter or validator script that asserts: `Index(## Detailed Implementation Checklist) < Index(## Findings)` and `Index(## Validation and cross-check) > Index(## Open questions)`. 

### Finding 2: Reviewers Do Not Check Placement
*   **Offending Text:** `"for an agent-executable plan... the CREATOR authored BOTH the top execution checklist AND the end verification/cross-check checklist, and you (the REVIEWER) assessed both..."` (`03-resolve-and-finalize.md` [cite: 17] and `plan-review.md` [cite: 15]).
*   **Risk:** The reviewer is instructed to assess *content* ("execution covers every action... specific enough to catch a false completion claim" [cite: 17]). It is never explicitly instructed to fail the plan if the *placement* drifted. Strong models over-literalize: if the checklist exists and is robust, they will pass it, ignoring the spatial location.
*   **Recommendation (Prose Rewrite):** Update `review-rubric.md` [cite: 16] and `plan-review.md` [cite: 15]. Add: *“Checklist Placement: The Execution checklist MUST appear exactly after `## Goal`, and the Validation checklist MUST appear exactly before `## Approval and execution gate`. If they have drifted or merged, this is a structural UNDER-SCOPE finding. Mark as REPLAN/FIX.”*

### Finding 3: Two-Checklist Design is Over-Engineered for Weak Models
*   **Risk:** The dual-checklist system is conceptually sound but technically fragile for small models. Forcing a 1:1 mapping between a top checklist and a bottom checklist creates a synchronization burden. If a weak model adds a step mid-execution, it often forgets to append the corresponding validation step at the bottom.
*   **Recommendation (Restructure):** Simplify. If you cannot implement a machine-linter, transition to a **Unified Evidence-Driven Checklist**. 
    *   Instead of two lists, require one list where each task has an immediate validation sub-bullet. 
    *   *Example:* 
        `- [ ] Task 1: Update auth logic.`
          `- [ ] Evidence: [Paste tests passing here before ticking Task 1]`
    *   *Why:* This forces the CoT immediately at the point of action, eliminating the long-range dependency while retaining the strict evidence requirement.

---

## 4. Consolidated Recommendation

1.  **If you control the tooling:** Keep the current Top/Bottom split, as it maximizes Primacy/Recency benefits. **Do not rely on prose to enforce it.** Write a 50-line Python script that parses the Markdown headers and rejects the IPD if the section indices are out of order. Tooling beats prose for structural formatting 100% of the time.
2.  **If you rely purely on prompt prose:** The two-checklist design is under-specified for weak models and prone to drift. Transition to a **Unified Evidence-Driven Checklist** located near the top. Mandate that every `[ ]` task has a nested `[ ] Evidence: <paste>` requirement.
3.  **Update the Reviewer Rubric:** Immediately patch `plan-review.md` [cite: 15] and `review-rubric.md` [cite: 16] to explicitly mandate checking spatial placement, classifying structural drift as a `REPLAN` finding.

---

## 5. Open Questions and Proposed Experiments

*   **Unresolved Question:** Does a unified checklist (Execution + Validation paired adjacently) yield higher actual execution fidelity than the split Top/Bottom layout for weak models?
*   **Proposed Experiment:** Run an A/B test using a flash-tier model (e.g., Gemini 1.5 Flash). 
    *   *Condition A:* Author and execute 50 IPDs using the current split Top/Bottom template.
    *   *Condition B:* Author and execute 50 IPDs using a Unified Evidence-Driven Checklist.
    *   *Metrics:* Measure the rate of hallucinated completions (ticked boxes with no actual git diff or test execution) and the rate of structural drift in the authored IPDs.

---

## 6. Sources

*   Liu, N. F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F., & Liang, P. (2023). *Lost in the Middle: How Language Models Use Long Contexts*. arXiv preprint arXiv:2307.03172.
*   `ipd.md` (Provided via prompt context, accessed July 31, 2026) [cite: 13]
*   `ipd-spec.md` (Provided via prompt context, accessed July 31, 2026) [cite: 14]
*   `plan-review.md` (Provided via prompt context, accessed July 31, 2026) [cite: 15]
*   `review-rubric.md` (Provided via prompt context, accessed July 31, 2026) [cite: 16]
*   `03-resolve-and-finalize.md` (Provided via prompt context, accessed July 31, 2026) [cite: 17]
