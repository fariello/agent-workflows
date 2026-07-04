# IPD: Lifecycle workflows (spec, incident, release-notes, migration)

- Date: 2026-07-04
- Concern: lifecycle coverage - the toolkit is strong on assess/review but thin at the
  front of the funnel (requirements) and the back (incident, release, migration).
- Scope: up to four new distinct workflows. This IPD proposes the set; each may become
  its own execution IPD when built.
- Status: PENDING (proposal for human approval; not executed)

## Goal

Fill the enterprise-delivery stages the toolkit currently under-serves, so it spans
discovery -> build -> review -> ship -> operate, not just assess/review.

## The four proposed workflows

### 1. `spec` / `draft-spec` (front of funnel)
Turn a fuzzy request into a reviewable specification / requirements document: goals,
non-goals, users, acceptance criteria, constraints, open questions. Feeds `plan-review`
and then implementation. Division of labor with IPD 4's `spec-editor` persona: the
`spec` workflow PRODUCES the artifact; `/advise spec-editor` interactively interrogates
and improves it. Guided/interactive (like setup-repo), writes the spec to the project's
docs/plan location.

### 2. `incident` / `post-mortem` (reactive operations)
A structured, blameless post-mortem for a production incident: timeline, impact,
detection, contributing factors (systemic, not blame), what went right/wrong, and
follow-up actions emitted as IPDs into pending/. Complements the PREVENTIVE reliability/
logging-audit/intrusion-detection lenses with a REACTIVE workflow. Honest about being
repo-scoped: the actual monitoring/SIEM/on-call data comes from the operator.

### 3. `release-notes` / `changelog` (release discipline)
A repeatable release step distinct from `release-review` Section 9 (which EXECUTES a
release): decide the version bump (from the changes / commit history), draft the
changelog and release notes, and (respecting the repo's convention) update
CHANGELOG/DECISIONS. Uses the prose style guide (assess-prose) for the notes.

### 4. `migrate` / `migration-plan` (high-risk change)
Assess-and-plan a migration (framework X->Y, DB v1->v2, dependency major bump, layout
change): inventory the blast radius, name the invariants that must survive, propose a
staged, reversible plan with characterization tests first, and emit it as an IPD. Runs
through the assess -> IPD -> plan-review -> execute pipeline. (The installer's own
legacy-layout migration, D17/D19, is a concrete example of this shape.)

## Why these four (and not more)

They are genuinely distinct ACTIVITIES (not personas or concerns), so they warrant their
own workflows rather than folding into assess/advise. Four is a bounded addition to the
command surface, consistent with the "few distinct workflows + parameterized families"
model. Anything more speculative is deferred (Fix Bar complexity axis).

## Scope check

- Over-scope: not project management, ticketing, roadmapping, or actual CI/CD/deploy
  execution (out of scope for a repo-agent framework). `release-notes` drafts notes and
  bumps versions; it does not publish. `incident` structures a post-mortem; it does not
  monitor.
- Under-scope: the front-of-funnel `spec` workflow is the most impactful gap; if only
  one is built first, build that.

## Dependencies / sequencing

- `spec` pairs with IPD 4's `spec-editor` persona (produce vs. interrogate).
- `release-notes` composes with the version stamping in IPD 2 and with prose (assess-prose).
- `migrate` reuses the assess harness/IPD pipeline; likely the last of the four.
- Each is independently buildable; recommend `spec` first, then `incident`,
  `release-notes`, `migrate` - or split into separate execution IPDs.

## Required validation

- Each workflow produces its artifact into the project's conventional location, follows
  the guided/ask-first pattern where it changes files, and stays honest about repo-scope
  limits (incident) and non-publishing (release-notes).

## Open questions

1. Build all four, or start with `spec` (highest-value front-of-funnel gap) and defer
   the rest?
2. Naming: `spec` vs `draft-spec`; `incident` vs `post-mortem`; `release-notes` vs
   `changelog`; `migrate` vs `migration-plan`.
3. Should `release-notes` be folded into `release-review` Section 9 instead of a
   separate command? (Leaning separate: notes/versioning is a distinct, reusable step.)

## Approval and execution gate

Proposal only. Likely best split into per-workflow execution IPDs. Approve/reorder and
decide which to build first.
