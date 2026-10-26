# plan-review

Pre-execution plan reviewer: review and improve a proposed Implementation Plan Document
(IPD) before any code is written, fixing issues in the plan itself. The plan-time sibling
of `release-review`. Run `/plan-review [path]`, or from any agent: "read and execute
`.aw/system/workflows/plan-review/plan-review.md`".

## Pre-change baseline commit

- Baseline commit: `bb094ca8ab37a04dec9f7aa431551d4c70764b86`
- This is the `/plan-review` that Order 09's pilot uses for the current-review method (read it with `git show bb094ca8ab37a04dec9f7aa431551d4c70764b86:.aw/system/workflows/plan-review/plan-review.md`).

## Instruction bytes sent per tier

Instruction bytes measured with `wc -c` over the files named in each tier's checklist, compared with the 48,108 bytes of the pre-change single-file workflow:

| Tier | Checklist files | Measured bytes | Delta vs pre-change (48,108 bytes) |
|---|---|---|---|
| `simple` (without R3) | `_kernel.md`, `p-proofread.md`, `t-tier.md`, `q-quick-risk.md`, `_findings.md`, `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md` | 37,369 | -10,739 bytes (-22.3%) |
| `simple` (with R3 short) | `_kernel.md`, `p-proofread.md`, `t-tier.md`, `q-quick-risk.md`, `r3-security.md`, `_findings.md`, `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md` | 38,568 | -9,540 bytes (-19.8%) |
| `standard` | `_kernel.md`, `p-proofread.md`, `t-tier.md`, `r1-references.md`, `r2-executability.md`, `r3-security.md`, `r4-engineering.md`, `_findings.md`, `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md` | 55,590 | +7,482 bytes (+15.6%) |
| `complex` | `_kernel.md`, `p-proofread.md`, `t-tier.md`, `r1-references.md`, `r2-executability.md`, `r3-security.md`, `r4-engineering.md`, `r5-personas.md`, `r6-decomposition.md`, `r7-cross-plan.md`, `_findings.md`, `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md` | 57,923 | +9,815 bytes (+20.4%) |
| `orchestrator` | `_kernel.md`, `p-proofread.md`, `r1-references.md`, `r2-executability.md`, `r7-cross-plan.md`, `_findings.md`, `s5-questions.md`, `s6-rereview.md`, `s7-finalize.md` | 49,767 | +1,659 bytes (+3.4%) |

## Old-to-new section map

### Headings map (38 headings outside code fences in pre-change file)

| # | Pre-change heading | Pre-change level | New location |
|---|---|---|---|
| 1 | `# Plan Review (pre-execution plan / IPD reviewer)` | H1 (Preamble) | `steps/_kernel.md` |
| 2 | `## Memory kernel` | H2 | `steps/_kernel.md` |
| 3 | `## Step 0: Scope and project contract` | H2 | `plan-review.md` |
| 4 | `### 0.1 Build the review-scope ledger` | H3 | `plan-review.md` |
| 5 | `### 0.2 Discover controlling instructions` | H3 | `steps/_kernel.md` |
| 6 | `### 0.3 Discover the plan contract and implementation context` | H3 | `plan-review.md` |
| 7 | `## Step 1: Evidence and pre-review snapshot` | H2 | `steps/r1-references.md` |
| 8 | `### Structural preflight (before semantic review)` | H3 | `plan-review.md` |
| 9 | `#### Orchestrator checklist row check and bounded repair loop (IPD-S407)` | H4 | `steps/r2-executability.md` |
| 10 | `#### Orchestrator review readiness (IPD-S408)` | H4 | `steps/r2-executability.md` |
| 11 | `### Pre-review commit` | H3 | `plan-review.md` |
| 12 | `## Step 2: Review and revise` | H2 | `steps/_findings.md` |
| 13 | `### 2.1 Apply all required views` | H3 | `steps/_findings.md` |
| 14 | `### 2.2 Record findings` | H3 | `steps/_findings.md` |
| 15 | `### 2.3 Remediation Risk and Fix Bar` | H3 | `steps/_findings.md` |
| 16 | `### 2.4 Revise the plan in place` | H3 | `steps/_findings.md` |
| 17 | `## Step 3: Resolve open questions` | H2 | `steps/s5-questions.md` |
| 18 | `### 3.1 Build the question set` | H3 | `steps/s5-questions.md` |
| 19 | `#### Resolving HOW questions: demonstrate, do not describe` | H4 | `steps/s5-questions.md` |
| 20 | `#### Reversible or not, and what that obliges` | H4 | `steps/s5-questions.md` |
| 21 | `### 3.2 Ask interactively` | H3 | `steps/s5-questions.md` |
| 22 | `### 3.3 Non-interactive exception` | H3 | `steps/s5-questions.md` |
| 23 | `## Step 4: Finalize state and commit` | H2 | `steps/s7-finalize.md` |
| 24 | `### Write the structured Readiness field (REQUIRED output of the review)` | H3 | `steps/s7-finalize.md` |
| 25 | `### Hardened-result commit` | H3 | `steps/s7-finalize.md` |
| 26 | `## Engineering rubric` | H2 | `steps/r4-engineering.md` |
| 27 | `### A. Correctness and data integrity` | H3 | `steps/r4-engineering.md` |
| 28 | `### B. Security and privacy` | H3 | `steps/r3-security.md` |
| 29 | `### C. Architecture and operability` | H3 | `steps/r4-engineering.md` |
| 30 | `### D. Anti-regression and domain invariants` | H3 | `steps/r4-engineering.md` |
| 31 | `### E. Testing and verification` | H3 | `steps/r4-engineering.md` |
| 32 | `### F. KISS, principles, and UX` | H3 | `steps/r4-engineering.md` |
| 33 | `### G. Plan executability` | H3 | `steps/r2-executability.md` |
| 34 | `## Severity and scope` | H2 | `steps/_findings.md` |
| 35 | `## Verdict and readiness` | H2 | `steps/s7-finalize.md` |
| 36 | `### A NO-GO is RE-EVALUABLE` | H3 | `steps/s7-finalize.md` |
| 37 | `### The escalation RETURN PATH` | H3 | `steps/s5-questions.md` |
| 38 | `## Required final report` | H2 | `steps/s7-finalize.md` |

### Fenced template headings

| Heading in fenced report / history template | New location |
|---|---|
| `## Workflow history` | `steps/s7-finalize.md` |
| `## Plan Review - <plan name(s)>` | `steps/s7-finalize.md` |
| `### Review scope` | `steps/s7-finalize.md` |
| `### Findings` | `steps/s7-finalize.md` |
| `### Edits applied` | `steps/s7-finalize.md` |
| `### Deferred and open` | `steps/s7-finalize.md` |
| `### Commit result` | `steps/s7-finalize.md` |
| `### Plans reviewed and not reviewed` | `steps/s7-finalize.md` |

### Rubric G bullets map

| Rubric G bullet (first words) | Assigned step file | Category |
|---|---|---|
| `Problem, driver, goals, non-goals, scope, and exclusions.` | `steps/r2-executability.md` | Structure |
| `Acceptance criteria and ordered implementation steps.` | `steps/r2-executability.md` | Structure |
| `Target components and existing mechanisms to reuse.` | `steps/r2-executability.md` | Structure |
| `Dependencies, sequencing, and data/API/workflow effects.` | `steps/r2-executability.md` | Structure |
| `Security, privacy, migration, documentation, and specification effects.` | `steps/r2-executability.md` | Structure |
| `Validation, rollout or recovery when relevant.` | `steps/r2-executability.md` | Structure |
| `Assumptions, open questions, ownership, and follow-up work.` | `steps/r2-executability.md` | Structure |
| `An execution contract in the gate:` | `steps/r2-executability.md` | Structure |
| `For an agent-executable plan: BOTH a top execution checklist AND an end verification/cross-check checklist` | `steps/r2-executability.md` | Structure |
| `Qualified spec citations (post-cutover spec trace convention):` | `steps/r2-executability.md` | Evidence / Trace |
| `Live-artifact success criteria vs. stable code facts (re-derivation convention):` | `steps/r2-executability.md` | Count / Durability |
| `Canonical no-error-added proof shape vs. unsatisfiable exit-0 demands (evidence-feasibility convention):` | `steps/r2-executability.md` | Evidence Feasibility |
| `Runtime-demonstration reachability vs. unsatisfiable observation demands (reachability convention):` | `steps/r2-executability.md` | Evidence Reachability |
| `Right-sizing and conceptual density (per E-item):` | `steps/r4-engineering.md` | Right-sizing |
| `Maintainer sizing signals:` | `steps/r4-engineering.md` | Right-sizing |
| `Another qualified agent or developer must be able to execute the plan without inventing missing architecture.` | `steps/r4-engineering.md` | Completeness |
