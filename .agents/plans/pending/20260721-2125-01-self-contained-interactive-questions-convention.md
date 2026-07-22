# IPD: self-contained interactive questions convention (the whole QUESTION SET lives in the prompt)

- Date: 2026-07-21
- Concern: agent UX / interaction quality - how agents ask a human for a decision
- Scope: a new guiding principle + a cross-cutting agent rule, referenced from the workflows that ask interactive questions. Prose only; no product code. Standalone (not part of any Set).
- Status: to-review
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-21 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored after the maintainer observed that an agent (this session) stranded the decision CONTEXT in chat prose and put only the bare question + options inside the interactive question tool, so a human reading the interactive prompt could not make the decision from the prompt alone. The maintainer specified the desired convention and asked that it be made durable across all agent-workflows agents.

## Goal

Establish a durable, repo-wide convention: an interactive question an agent poses to a human MUST be self-contained - the ENTIRE "question set" (the plain-English context/information needed to decide, the actual question sentence, and the selectable/enterable answer options) lives INSIDE the interactive question presented to the human. An agent MAY add supplementary prose in the surrounding message before a prompt, but only for ONE question at a time, and that prose is ADDITIVE: it must never be the sole home of information required to answer.

Why it matters: agents ask decision questions through an interactive prompt UI (a picker with a question + options). If the context that justifies the choice lives only in the chat body and not in the prompt, a human answering from the prompt is deciding blind. The information, the question, and the answers must travel together. This is an interaction-quality and honesty issue (do not force a decision without its basis), and it recurs across every workflow that asks the human anything.

## Project conventions discovered (Step 0)

- Guiding principles live in `GUIDING_PRINCIPLES.md` (currently P1-P11; the next is P12). No em/en dashes.
- Cross-cutting agent rules that apply even outside a named workflow live in `AGENTS.md` (the always-read file; it deliberately does not inline workflow bodies, `index.md:14-15`).
- Workflows that ask interactive questions (verified by grep): `.agents/workflows/plan-review/plan-review.md` (Step 3.2, "Ask interactively", one to three questions per prompt, provides Decision needed / Context / Why it matters / Options / Trade-offs / Recommendation); `.agents/workflows/plan-review-long/03-resolve-and-finalize.md` (parity sibling); `.agents/workflows/advise/advise.md`; `.agents/workflows/spec/spec.md`; `.agents/workflows/getting-started/getting-started.md`. These say "ask" and enumerate what to include, but none states WHERE it must go (inside the prompt vs the chat body).
- The `plan-review` Step 3.2 list (Decision needed, Context, Why it matters, Options, Trade-offs, Recommendation) is exactly the "question set" content; this IPD adds the placement rule (all of it inside the prompt) rather than new content requirements.
- Plans lifecycle: `.agents/plans/pending/` + `YYYYMMDD-HHMM-NN-<slug>.md`; IPD born `to-review`.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| Q1 | MEDIUM | Low | stakeholder / any human answering | interaction quality | No convention says the decision CONTEXT must be inside the interactive prompt; agents put it in chat prose and leave the prompt with only a bare question + options, so a human answering from the prompt decides without the basis. Observed live this session. | no such rule in `GUIDING_PRINCIPLES.md`, `AGENTS.md`, or the ask-interactively steps |
| Q2 | LOW | Low | agent | consistency | The question-asking workflows (`plan-review` 3.2, `advise`, `spec`, `getting-started`, `plan-review-long`) enumerate WHAT to include but not WHERE it must live, so behavior varies by agent. | `plan-review.md` Step 3.2 ("Ask interactively") |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | Q1 | Add GUIDING_PRINCIPLES P12 "Ask self-contained questions": an interactive question MUST carry its whole question set - context/information, the question, and the answer options - INSIDE the prompt itself; surrounding chat prose is optional and additive, for one question at a time, and never the sole home of required context. State the why (a human answering from the prompt must be able to decide from the prompt alone). | `GUIDING_PRINCIPLES.md` | Low | P12 present, concise, matches the house style; no em/en dashes |
| 2 | Q1,Q2 | Add a one-line cross-cutting rule to `AGENTS.md` (so it applies even outside a named workflow) pointing at P12: "When you ask a human a question interactively, put the entire question set (context + question + options) in the prompt itself; extra prose may precede it but only for one question at a time and only as a supplement." Keep it short (AGENTS.md does not inline bodies). | `AGENTS.md` | Low | AGENTS.md carries the one-line rule referencing P12; nothing inlined |
| 3 | Q2 | Reference the rule from the question-asking workflows so they inherit it rather than restating it: `plan-review` Step 3.2 and `plan-review-long/03-resolve-and-finalize.md` (add a line: the six-part question set MUST be presented inside the interactive prompt, per P12), and a short pointer in `advise`, `spec`, and `getting-started` where they instruct the agent to ask. Do not duplicate the full rule; cross-reference P12. | `.agents/workflows/plan-review/plan-review.md`, `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `.agents/workflows/advise/advise.md`, `.agents/workflows/spec/spec.md`, `.agents/workflows/getting-started/getting-started.md` | Low | each ask-interactively surface references P12 / the self-contained rule; the single source of the rule is P12 (no divergent restatements) |
| 4 | Q1 | Docs/decision sync: a DECISIONS entry (pin at execution) recording the convention + why (the observed stranded-context incident) and that it is enforced via P12 + AGENTS.md + the workflow references; CHANGELOG 1.3.0. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; links resolve; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| A programmatic linter that checks an agent actually put context in the prompt | High | functionality | The prompt content is produced at runtime by the agent, not a tracked artifact, so there is nothing static to lint; this is a behavioral convention enforced by instruction (like the other guiding principles). | n/a - a convention, not a checkable file. |
| Changing the tool/mechanism agents use to ask questions | Medium | complexity | Out of scope: this is about HOW agents use whatever prompt mechanism exists, not building a new one. | n/a. |

## Scope check

- Over-scope: none. One principle + one AGENTS.md line + cross-references + docs. No new content requirements beyond placement; no code.
- Under-scope: the rule must live in ONE authoritative place (P12) and be REFERENCED, not restated divergently, by the workflows (P8 single source of truth); the AGENTS.md line must stay short (it is always-read context).

## Required tests / validation

- Prose only (no code): validate by review + consistency. (a) P12 states the self-contained-question rule with its why; (b) AGENTS.md carries a short pointer to it; (c) each question-asking workflow references P12 rather than restating it; (d) no divergent copies of the rule; (e) no em/en dashes; (f) `aw check-local-leaks .` clean; (g) `python -m pytest -q` stays green (these are docs; expect no change) - paste actual output.
- If any test asserts the count/content of GUIDING_PRINCIPLES or AGENTS.md, update it; otherwise none.

## Spec / documentation sync

- `GUIDING_PRINCIPLES.md` (P12, the authoritative rule), `AGENTS.md` (the cross-cutting pointer), the five question-asking workflow files (references), DECISIONS, CHANGELOG 1.3.0.

## Open questions

- OQ1 (AGENTS.md placement): put the one-line rule in the existing "Agent execution contract" paragraph of `AGENTS.md`, or as its own short bullet? Lean: fold it into the execution-contract area as a short sentence (it is a how-you-behave rule), avoiding a new heading. Confirm at review.
- OQ2 (workflow reference depth): a single cross-reference line per workflow, or also restate the "one question at a time for the supplementary prose" nuance inline where relevant? Lean: single cross-reference to P12 everywhere (P8); the nuance lives only in P12. Confirm at review.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
