# IPD: deepen the interactive-questions convention (what to include/omit, screen-length, do-not-repeat-options, pre-flight)

- Date: 2026-07-22
- Concern: agent interaction quality - HOW an agent composes an interactive question, extending the P12 self-contained rule with practical guidance
- Scope: expand GUIDING_PRINCIPLES P12, its AGENTS.md installer-template block, and the existing P12 references so agents get the fuller "how to write the question" guidance. Prose only; no product code. Standalone.
- Status: reviewed
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)

## Workflow history

- 2026-07-22 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; I1-I5 (I5 added). Verified P12 (`GUIDING_PRINCIPLES.md:107-114`) and both plan-review variants' six-part set with "Options" + the "present INSIDE the prompt" line. I5 (MEDIUM, FIXED): the do-not-repeat-options rule collided with P12's own "answer options ... INSIDE the prompt" wording and Step 3.2's "Options" item, readable as contradictory; fixed by clarifying at the source (Step 1: "answer options = the tool's rendered choices") and stating Step 3 as a concrete rule (the Options item is satisfied by the tool's choices, not narrated in context). OQ1 resolved from the lean-AGENTS.md convention (one-line pointer); OQ2 resolved from P8 (pre-flight lives in P12). No open questions remain. Readiness: GO - PENDING HUMAN APPROVAL.
- 2026-07-22 created (opencode its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer instruction that deepens the P12/D100 self-contained-questions convention with concrete composition guidance (what facts to include vs omit, keep it screen-sized, do NOT repeat the tool's options in the context, and a pre-flight checklist). Same principle as D100; this adds the practical "how".

## Goal

Extend the self-contained-questions convention (P12 / DECISIONS D100) from "the whole question set lives in the prompt" to also tell an agent HOW to compose that prompt well: which facts to include, what to leave out, how long it may be, that the context must not duplicate the answer options the tool renders, and a short pre-flight self-check. One authoritative rule (P12), referenced everywhere; this is a deepening, not a competing rule.

Why it matters: D100 fixed WHERE the question set lives (inside the prompt). But agents (including in this very session) still write bloated prompts: chronology, filenames, quoted evidence, and a prose re-listing of the same options the picker will show. That wastes the user's attention, overflows the terminal, and duplicates the tool UI. The maintainer wants a compact, decision-ready synthesis: relevant facts + what changed + why a decision is needed + essential constraints/tradeoffs + a recommendation with its basis, and nothing else. The "do not repeat the options" point is a real behavior change from the current P12 wording, which says the options live inside the prompt but does not forbid also narrating them in the surrounding context.

## Project conventions discovered (Step 0)

- Guiding principles: `GUIDING_PRINCIPLES.md` P12 (D100) currently states only that the whole question set (context + question + options) lives inside the prompt and that surrounding prose is additive, one question at a time. It does NOT yet cover what-to-include/omit, length, do-not-repeat-options, or a pre-flight check. No em/en dashes.
- The P12 rule is stamped into the installer AGENTS.md template via `agent_workflows/engine.py` `agents_pointer_block()` ("Ask self-contained questions" section) and REGENERATED into `AGENTS.md` verbatim (D100 / plan-review Q3: edit the TEMPLATE, not AGENTS.md directly, or it is clobbered on install).
- P12 is REFERENCED (not restated, P8) from: `.agents/workflows/plan-review/plan-review.md` (Step 3.2), `.agents/workflows/plan-review-long/03-resolve-and-finalize.md`, `.agents/workflows/advise/advise.md`, `.agents/workflows/spec/spec.md`, `.agents/workflows/getting-started/getting-started.md`. These references stay pointing at P12; deepening P12 flows to them automatically (P8).
- `plan-review` Step 3.2 also enumerates a six-part "Decision needed / Context / Why it matters / Options / Trade-offs / Recommendation" question set - which currently invites listing the OPTIONS in the composed context; this IPD must reconcile that with the new do-not-duplicate-the-tool's-options rule.

## Findings (drivers)

| ID | Severity | Remediation Risk | Persona | Area | Finding | Evidence |
|----|----------|------------------|---------|------|---------|----------|
| I1 | MEDIUM | Low | any human answering | interaction quality | P12 says WHERE the question set goes but not HOW to compose it; agents write over-long prompts with chronology, filenames, quotes, and exhaustive evidence, burying the decision. | `GUIDING_PRINCIPLES.md:107-114` (no composition guidance) |
| I2 | MEDIUM | Low | any human answering | duplication / UI | Nothing forbids the context from repeating/previewing the options the tool will render; agents do (observed this session), doubling the reading and duplicating the picker UI. | `GUIDING_PRINCIPLES.md:107-114`; `plan-review.md` Step 3.2 six-part set includes "Options" |
| I3 | LOW | Low | any human answering | screen fit | No length guidance; prompts can overflow a terminal screen. The maintainer wants it to fit comfortably, reduced to the minimum facts if too long, with any imperative extra detail flagged in chat as a last resort. | `GUIDING_PRINCIPLES.md:107-114` |
| I4 | LOW | Low | agent | self-check | No pre-flight checklist to catch violations before asking (answerable without reopening material? every fact necessary? reason clear? options not repeated?). | none exists |
| I5 | MEDIUM | Low | executor / maintainer | self-consistency | The do-not-repeat-options rule collides with P12's own phrase "the answer options ... lives INSIDE the prompt" and with `plan-review` Step 3.2's "Options" item + "present this whole six-part question set INSIDE the interactive prompt" - readable as putting the options in the composed prose. Without clarifying that "answer options" = the tool's rendered CHOICES (distinct from the composed context), the deepened P12 and Step 3.2 can be read as contradictory. Raised + fixed by plan-review (PR-001): clarify P12 at the source (Step 1) and state Step 3 as a concrete rule. | `GUIDING_PRINCIPLES.md:109-111`; `plan-review.md:204-215` |

## Proposed changes (ordered, validatable)

| Step | Source | Change | Files | Remediation Risk | Validation |
|------|--------|--------|-------|------------------|------------|
| 1 | I1,I2,I3,I4 | Expand GUIDING_PRINCIPLES P12 with the composition guidance (keeping the existing "whole question set lives in the prompt" core). RESOLVE THE OPTIONS AMBIGUITY AT THE SOURCE (plan-review PR-001): P12's phrase "the answer options" MUST be clarified to mean "the answer options, rendered as the interactive tool's selectable CHOICES" - the composed context is the situation, the tool's choices are the answers, and the two do not overlap. Then add, in the maintainer's terms: INCLUDE the relevant facts, what changed/was discovered (if applicable), the general reason a decision is needed, any essential constraint/dependency/consequence/tradeoff, and a recommendation with its main factual basis when you have one. OMIT chronology, investigation details, quotations, filenames, and exhaustive evidence unless important to the decision; prefer a compact synthesis in plain English. DO NOT repeat, preview, or separately summarize the options the tool will display - the context explains the situation, the tool's choices present the answers. Keep it SCREEN-SIZED; if too long, cut to the minimum facts; if extra detail is imperative, put it in chat as a LAST RESORT and say so in the prompt. Add a PRE-FLIGHT self-check: can the user answer without reopening other material? is every fact necessary? is the reason clear? have I avoided repeating the options? | `GUIDING_PRINCIPLES.md` (P12) | Low | P12 clarifies "answer options = the tool's rendered choices", covers include/omit, do-not-repeat-options, screen-length + last-resort-chat, and the 4-point pre-flight; the existing core is preserved; no em/en dashes |
| 2 | I1,I2 | Update the AGENTS.md installer TEMPLATE (`agents_pointer_block()` in `engine.py`) "Ask self-contained questions" section to add a one-line deepening pointer (compact synthesis; do NOT repeat the tool's options; keep it screen-sized; see P12), then REGENERATE `AGENTS.md` to match the template verbatim. Keep it short (AGENTS.md does not inline bodies) - the full guidance lives in P12. | `agent_workflows/engine.py`, `AGENTS.md` | Low | template + regenerated AGENTS.md carry the short deepening pointer; AGENTS.md matches the template verbatim (no drift); nothing inlined |
| 3 | I2 | Reconcile `plan-review` Step 3.2 (and its parity sibling `plan-review-long/03`) with the clarified P12 (PR-001), stated as a concrete rule, not a vague "add a sentence": the six-part set (Decision needed / Context / Why it matters / Options / Trade-offs / Recommendation) names what the agent must CONVEY, but the "Options" item is satisfied by the interactive tool's rendered CHOICES - the agent supplies them AS the tool's answer options and does NOT also narrate/restate them in the composed context prose. Add exactly that clarifying sentence to both variants (they currently say "present this whole six-part question set INSIDE the interactive prompt", which alone could be read as putting the options in the prose) and cross-reference P12; do not remove the six-part content requirement. The other three references (advise/spec/getting-started) already point at P12 and inherit the deepening (P8); no change. | `.agents/workflows/plan-review/plan-review.md`, `.agents/workflows/plan-review-long/03-resolve-and-finalize.md` | Low | both plan-review variants state the Options item = the tool's rendered choices (not duplicated in context prose); cross-reference P12; six-part requirement preserved; no divergent restatement |
| 4 | I1 | Docs/decision sync: a DECISIONS entry (pin at execution) recording the P12 deepening (compose compactly; include/omit lists; do-not-repeat-options; screen-length; pre-flight), noting it extends D100; CHANGELOG 1.3.0. | `DECISIONS.md`, `CHANGELOG.md` | Low | entries present; extends D100; no em/en dashes |

## Deferred / out of scope (with reason)

| Item | Remediation Risk | Axis | Reason | Recommended later step |
|------|------------------|------|--------|------------------------|
| A programmatic check that a composed prompt obeys the rules (length, no option-duplication) | High | functionality | The prompt is runtime agent output, not a tracked artifact; nothing static to lint. Enforced by instruction like the other guiding principles. | n/a. |
| Changing the interactive question TOOL/mechanism | Medium | complexity | This is about how agents USE whatever prompt tool exists, not building one. | n/a. |

## Scope check

- Over-scope: none. Deepen one principle + a short AGENTS.md template pointer + reconcile the two plan-review variants + docs. No code logic; the only `engine.py` change is the prose template string (regenerated into AGENTS.md).
- Under-scope: the deepening MUST live in ONE authoritative place (P12) and be referenced not restated (P8); the AGENTS.md addition MUST go through the engine template (never a direct AGENTS.md edit that install clobbers) and AGENTS.md regenerated verbatim; the do-not-repeat-options rule MUST be reconciled with plan-review's six-part set (I2) AND with P12's own "answer options" wording (I5/PR-001) so the documents cannot be read as contradictory.

## Required tests / validation

- Prose (+ the engine template string): validate by review + consistency. (a) P12 clarifies "answer options = the tool's rendered choices" (I5) AND covers include/omit, do-not-repeat-options, screen-length + last-resort-chat, and the 4-point pre-flight, with the D100 core preserved; (b) the engine `agents_pointer_block()` carries the short deepening pointer AND `AGENTS.md` matches the regenerated template VERBATIM (no drift); (c) both plan-review variants state the Options item = the tool's rendered choices (not duplicated in context) and cross-reference P12; (d) READ P12 + plan-review Step 3.2 together and confirm they cannot be read as contradictory (I5); (e) advise/spec/getting-started unchanged (they inherit via P8); (f) no divergent restatements; (g) no em/en dashes; (h) `aw check-local-leaks .` clean; (i) `python -m pytest -q` stays green (docs + one template string; expect no test change) - paste actual output.

## Spec / documentation sync

- `GUIDING_PRINCIPLES.md` (P12, the authoritative rule), the AGENTS.md engine template + regenerated `AGENTS.md`, the two plan-review variant files, DECISIONS, CHANGELOG 1.3.0.

## Open questions

- OQ1 (AGENTS.md depth): RESOLVED from the established convention (plan-review). A ONE-LINE deepening pointer only ("compose a compact synthesis; do not repeat the tool's options; keep it screen-sized; see P12"). The always-read AGENTS.md block is deliberately kept lean and does not inline principle/workflow bodies (the D99/D100 precedent); the full include/omit/pre-flight guidance lives in P12 (P8).
- OQ2 (pre-flight placement): RESOLVED from P8 (plan-review). The 4-point pre-flight checklist lives in P12 (single source of truth); the workflow references inherit it and do not restate it.

## Approval and execution gate

This IPD is a proposal. It MUST be reviewed and approved by a human before execution, and it is NOT auto-executed.

Execution contract (per `.agents/plans/README.md` and `AGENTS.md`): commit ONLY files changed by this plan, path-scoped (`git commit -m msg -- <path>`), never `git add -A`/`-a`, never push. When reporting tests, paste the ACTUAL runner output; never claim a pass not run. No em or en dashes in authored Markdown. STOP and report if execution exceeds this plan's scope. Never create or push a tag / Release / PyPI upload.

Recommended next steps:
1. Review (optionally `/plan-review`). Resolve OQ1-OQ2. Pin the DECISIONS number at execution.
2. On human approval, set `Status: approved` (+ `Approval:`), execute, validate, sync docs; commit path-scoped (no push).
3. Set terminal `Status: executed` and `git mv` to `.agents/plans/executed/`.
