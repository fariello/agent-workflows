---
id: y6vfto
created: 20261017
set: revsteps
order: 00
topic: [plan-review, runner]
model: 
kind: research-prompt
outcome: none-yet
summary: Multi-model design review of the runner-enforced, depth-scaled plan review redesign (Originating prompt for the comparison set)
consumed-by: []
---

# Design review: runner-enforced, depth-scaled plan review for agent-workflows

You are reviewing a proposed design for the agent-workflows toolkit before a specification is
written from it. Your output is one input to a revised design. Several independent reviewers receive
this same prompt, and their outputs are merged mechanically, so follow the output format in Section 6
exactly.

## 1. The codebase under discussion

agent-workflows is public: https://github.com/fariello/agent-workflows

You may read it. Prefer reading the source to guessing from this prompt. If you have a local
checkout of the repository, use it, because it may be newer than the public copy. If you cannot
access the repository, review the design on its own terms and set `Repository access` to `none` in
your output (Section 6.1).

What the toolkit does, briefly: it manages a repository's planning records (plans, specs, backlog
items, reviews) under `.aw/records/`, and it ships "runners" (`aw oc run` for OpenCode and
`aw agy run` for Antigravity) that drive coding agents through those records unattended. A plan is an
Implementation Plan Document (IPD): a Markdown file with execution items (`E-*`) and matching
validation items (`V-*`). Today a plan is reviewed in one agent turn by the `/plan-review` workflow
before a human approves it for execution.

## 2. Materials

Read both documents in full before you write anything.

1. **The design (the subject of the review):** spec `k3yx72`, "Runner-enforced, depth-scaled plan
   review", at `.aw/records/specs/draft/20261017-k3yx72-01-k3yx72-plan-review-redesign.spec.md`. It is a draft design summary, not yet a full normative spec. Its Section 3
   lists fixed decisions and its Section 14 lists open questions.
2. **The proofreading instructions that the design adopts as review step S-02:** prompt `wcisgc`,
   "Proofread Technical Artifacts", at `.aw/records/prompts/reusable/20261017-revsteps-01-wcisgc-technical-artifact-proofreading.prompt.md`.

Both files are committed in the repository. If they are not yet on the public copy, they are
attached to this conversation. If neither the files nor the attachments are available, stop and
report that the materials are missing. Do not review from this prompt alone.

These repository files are the most relevant context. Read the ones that bear on your findings:

- `.aw/system/workflows/plan-review/plan-review.md`: the current single-turn review.
- `.aw/system/workflows/plan-review-long/`: the multi-file variant that the design retires.
- `agent_workflows/runner_shared.py`: the shared runner logic. Relevant names include
  `build_review_prompt`, `review_handler_for`, `classify_probe_reply`, and `probe_reply_text`.
- `agent_workflows/ipd_schema.py` and `agent_workflows/ipd_lint.py`: the IPD structure and its lint
  rules, including the size thresholds and rule `IPD-C801`.
- `.aw/records/plans/README.md` and `.aw/records/reviews/README.md`: the plan and review-record
  contracts.
- `.aw/records/specs/` (spec `25kzda`, the runner contract) and the IPD spec
  (`20260726-1340-01-ipd-spec.spec.md`), both of which the design proposes to amend.
- `AGENTS.md`: the operating rules for agents in this repository.

## 3. Fixed decisions

Section 3 of the design lists decisions MD-1 to MD-8 that the maintainer has already made. Do not
argue against a fixed decision in a finding. If you believe a fixed decision is materially harmful,
record it once in the `Challenges to fixed decisions` section (Section 6.5), with evidence. Everything
else in the design is open to critique.

## 4. What to evaluate

Evaluate the design against each of these questions. Report only real issues. Do not report a
question as a finding merely because it is listed here.

1. **Correctness against the codebase.** Does each claim about current behavior match the
   repository? Do the named files, symbols, fields, lint rules, and commands exist and behave as the
   design says?
2. **Feasibility.** Can each runner postcondition in Sections 4 and 8 actually be checked from data
   the runner has? Can both hosts (OpenCode and Antigravity) support the single-session, multi-prompt
   sequence?
3. **Gaps and failure behavior.** What happens on a host crash, a timeout, an interrupted session, a
   resumed run, a plan edited by another agent during the review, or a review that runs in an
   isolated worktree?
4. **Enforcement strength.** Where can an agent satisfy a postcondition without doing the work? For
   example: empty review subsections, a proofreading pass that changes nothing, or a depth rating
   that is always the floor.
5. **The depth model.** Are the floor conditions in Section 5 and the step allocation in Section 6
   reasonable? Which plans would they misclassify? Suggest better measurable signals if you know
   any.
6. **The re-review loop.** Are the marker rules in Section 8.1, the runner triggers in Section 8.2,
   and the two-round limit in Section 8.3 sound? Can the loop fail to terminate, or terminate too
   early?
7. **The split step.** Is Section 9 safe? Consider provenance, release gates, plans that were
   already partly reviewed, and requeue ordering.
8. **The citation format.** Is Section 7 durable in practice? What does it miss (other languages,
   generated files, moved files)? Propose an exact syntax for the quoted-text form (open question
   OQ-2).
9. **Cost.** Is 8 to 11 prompts per review acceptable for a queue of hundreds of plans? Where could
   steps be merged without losing enforcement?
10. **Interaction with existing gates.** Does the design conflict with `- Readiness:` attestation,
    the review-staleness check, the orchestrator coverage gate, auto-approval, or the status setters?
11. **Writing quality of the design itself.** Apply the proofreading instructions to the design
    document. Report only defects that could change how the design is understood or implemented. Do
    not report style preferences.
12. **Open questions.** Answer OQ-2 to OQ-6 in Section 14 of the design.

## 5. Rules for your review

- Distinguish what you verified in the repository from what you inferred. Mark every finding
  `Verified` or `Inferred` (Section 6.3).
- Cite repository locations with the durable form that the design proposes: `path::Symbol` for
  Python code, `path#Heading text` for Markdown, or `path` plus a short exact quoted string. Do not
  cite line numbers.
- Cite the design by its section and item ids (for example `§4 S-02`, `§8.1 rule 3`, `OQ-3`).
- Combine findings that share one root cause into one finding.
- Do not invent requirements, numbers, or repository behavior. When you do not know something, say
  so in the finding.
- Do not edit any repository file. This is a review only.
- Write in plain, precise English.

## 6. Output

Return your review as ONE downloadable Markdown file named
`plan-review-redesign-review-<reviewer>.md`, where `<reviewer>` is a short lowercase name for you or
your model (for example `opus55high`, `gemini4argonmedium`, `gpt61solmedium`, `gemini38flashhigh`). If you cannot produce a downloadable file,
return the same content as one fenced Markdown block. Use exactly the sections below, in this order.
Write `None.` in a section that has no content.

### 6.1 Header

```markdown
# Review of the plan-review redesign
- Reviewer: <name and model>
- Repository access: <local checkout | public GitHub | none>
- Materials read: <list of files you actually read>
- Overall assessment: <sound | sound with changes | needs rework>
- Summary: <three sentences or fewer>
```

### 6.2 Top issues

The three most important findings, by finding id, each with one sentence explaining why it ranks at
the top.

### 6.3 Findings

One table row for each finding:

| Field | Content |
| --- | --- |
| ID | `F-01`, `F-02`, and so on. |
| Severity | `blocker` (the design cannot work as written), `major` (material risk or gap), `minor` (a real but small issue), or `wording` (a defect in the design's text). |
| Category | One of: `correctness`, `feasibility`, `gap`, `enforcement`, `depth-model`, `rereview`, `split`, `citations`, `cost`, `gate-interaction`, `wording`. |
| Location | The design section and item id. |
| Issue | What is wrong, stated so that a reader who has not seen your review understands it. |
| Evidence | Durable repository citations or quotations from the design. |
| Basis | `Verified` or `Inferred`. |
| Proposed change | The specific change to the design. If you cannot propose a change, say what decision or information is needed. |

### 6.4 Answers to open questions

For each of OQ-2 to OQ-6: your answer, your reason, and whether the answer is `Verified` against the
repository or is a judgement.

### 6.5 Challenges to fixed decisions

For each fixed decision (MD-1 to MD-8) that you believe is materially harmful: the decision id, the
harm, and the evidence. Write `None.` if you have no challenges.

### 6.6 Alternative designs

At most two alternatives that would meet the goal in Section 1 of the design better. For each: a
description, what it improves, and what it costs.

### 6.7 Limits of this review

What you could not read, could not verify, or did not evaluate.
