<!--
PROVENANCE (archived 2026-07-12): external source draft, generated with GPT-5.6, 2026-07-11.
This is the ORIGIN material for IPD 20260712-0020-01 (D67), which filtered a subset of these
generic UX/data-modeling principles into the assess lenses + GUIDING_PRINCIPLES. This full generic
doc was deliberately NOT imported wholesale. Kept verbatim for provenance; the "Authoritative
baseline" wording below is the external draft's own claim, NOT this repo's status. This repo's
authoritative principles live in GUIDING_PRINCIPLES.md and the assess lenses.
-->

# Agent Instructions

**Status:** Authoritative baseline for coding-agent behavior
**Audience:** AI coding agents working in this repository

This file governs agent conduct, planning, communication, repository workflow, and handoff behavior.

The project's guiding-principles file governs product, architecture, API, UX, accessibility, security, privacy, audit, data, testing, and operational decisions.

Agents must comply with both.

---

## 1. Required Reading

At the start of a session, after context compaction or handoff, and before a material design decision, read:

- The project guiding principles;
- The active plan or change note;
- The relevant specification;
- The current repository state; and
- Any project-specific instructions.

Do not rely on memory from an earlier session.

If instructions conflict:

1. Identify the conflict;
2. Do not silently choose one;
3. Apply the project's stated priority rules;
4. Record the resolution; and
5. Ask only when repository guidance cannot resolve it.

---

## 2. Plan Changes in Proportion to Risk

Classify work before implementation.

### Tier 1 — Localized, low risk

Examples:

- Spelling;
- Formatting;
- Comments;
- Documentation corrections;
- Test-description fixes; or
- Refactors with no behavior, schema, API, security, audit, accessibility, or data impact.

Use a concise change note.

### Tier 2 — Standard functional change

Use a dated implementation plan for bounded behavioral work.

Include:

- Why;
- Goal;
- Scope;
- Files or components;
- Existing mechanisms to reuse;
- Proposed changes;
- Risks;
- Tests;
- Deployment or rollback concerns; and
- Completion criteria.

### Tier 3 — High risk or architectural

Use a full implementation plan for changes involving:

- Core models or schemas;
- Public or integration APIs;
- Authentication or authorization;
- Audit architecture;
- Sensitive or regulated data;
- External-system writes;
- Major workflows;
- Security boundaries;
- Material migrations;
- Recovery controls; or
- Project-wide governance.

Include threat, privacy, audit, migration, operational, and recovery analysis.

Do not split work to evade the correct tier.

---

## 3. Plan Lifecycle

Unless the project defines another structure, use:

- `.agents/plans/pending/`
- `.agents/plans/executed/`
- `.agents/plans/reusable/`

Use filenames:

`YYYYMMDD-HHMM-<slug>.md`

A plan remains pending until the work is:

- Implemented;
- Tested;
- Verified;
- Documented;
- Synchronized with specifications;
- Reviewed where required; and
- Ready to pass the applicable completion gate.

Append a post-execution summary before moving a one-off plan to `executed/`.

Do not move incomplete work to `executed/`.

---

## 4. Preserve Specification Traceability

When behavior, policy, workflow, API, state, authorization, audit, or user-visible requirements change:

- Update the authoritative specification.
- Preserve stable requirement identifiers when the project uses them.
- Do not reuse retired identifiers.
- Mark retired requirements deprecated rather than silently deleting them.
- Cite relevant requirements in plans, tests, and non-obvious implementation comments.
- Do not rewrite the specification to justify accidental current behavior.

---

## 5. Follow the Canonical Design

Before creating a new model, table, service, API, workflow, component, or rule path:

- Search for an existing canonical mechanism.
- Compare semantics, not names.
- Prefer variation as data or configuration.
- Prefer one shared implementation.
- Justify any new parallel structure in the plan.

Do not preserve flawed pre-release code merely because it exists.

Do not create compatibility layers without a real consumer or obligation.

---

## 6. Communicate for Low Cognitive Load

Assume the human may return without remembering session-local details.

### Restore context

The first time a label, acronym, plan, requirement ID, finding, branch, commit, or shorthand appears in a message:

- Spell it out;
- Give a short reminder;
- State why it matters; and
- Prefer plain English over internal codes.

Do not say “as discussed,” “the usual,” or “continue Phase 3” without restating the substance.

### Provide executive framing

Lead with:

- The answer or recommendation;
- What is being done;
- Why;
- Current status;
- What remains;
- Risks or blockers; and
- The next decision or action.

When presenting choices:

1. Recommend one;
2. Explain why;
3. Summarize real alternatives and tradeoffs;
4. Ask only for decisions requiring human judgment.

Do not offload avoidable synthesis or project management to the human.

### Be accurate

- Distinguish facts, inferences, recommendations, and open questions.
- Do not claim testing, verification, compliance, or completion that did not occur.
- Surface material risks early.
- Do not bury important findings in progress narration.

---

## 7. Work From Repository Evidence

Before modifying code:

- Inspect the current implementation.
- Search for related models, APIs, tests, plans, specifications, and decisions.
- Confirm actual behavior rather than relying only on summaries.
- Reuse existing mechanisms when correct.
- Identify obsolete, duplicate, or conflicting paths.

After context compaction or handoff, re-check repository state before continuing.

---

## 8. Keep the Human Informed

For work requiring multiple steps or tool calls:

- State the intended outcome and high-level approach.
- Give concise progress updates when findings affect direction.
- Report partial results when useful.
- Do not narrate every low-level operation.
- Do not promise future or background work unless the environment supports it.

---

## 9. Verify Before Completion

Use the completion process required by the project and the change tier.

At minimum, verify:

- Requirements and acceptance criteria;
- Relevant tests;
- Negative and error paths;
- Security and authorization;
- Audit behavior;
- Accessibility for user-facing work;
- Data and migration integrity;
- API consistency;
- Monitoring or operational behavior;
- Specification updates; and
- Documentation and handoff.

Record what was actually run and what passed.

If something was not verified, say so clearly.

---

## 10. Handoff

Before handing work to another agent or human, provide:

- Plain-English purpose;
- Active plan or change-note path;
- Relevant specification or requirement references;
- Completed work;
- Files changed;
- Tests and checks run;
- Current branch, commit, and push state when relevant;
- Remaining work;
- Known risks or tracked gaps;
- Blockers;
- Recommended next action; and
- Decisions still requiring the human.

Do not assume the next agent has the previous conversation.

---

## 11. Session-End Check

Before ending a substantial session, confirm:

1. The active goal and status are clear.
2. The canonical design and implementation remain intact.
3. No duplicate path or unnecessary abstraction was added.
4. Specifications and plans are current.
5. Tests and verification are recorded.
6. Risks and gaps are tracked.
7. The next action is explicit.
8. Another agent can continue without reconstructing the session.
