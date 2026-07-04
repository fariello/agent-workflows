# IPD: `advise` workflow + expert-persona library

- Date: 2026-07-04
- Concern: a new capability class - interrogation and mentoring (ask questions and
  coach to improve an artifact), distinct from the review/assess (find-and-propose)
  and the fix-in-place workflows.
- Scope: one parameterized `advise` workflow (harness) + a library of expert-persona
  files (like assess = harness + lenses). Absorbs the "grill-me"-style interrogator and
  the "spec tutors/experts" idea without adding many commands.
- Status: PENDING (proposal for human approval; not executed)

## Goal

Provide a way for an expert persona to examine the current context or a named artifact
(a spec, a plan, a design, a decision), ask probing questions, surface gaps and
assumptions, and coach the author toward a stronger result. `/advise <persona>`.

## Why one workflow, not many commands

The requested "grill me" interrogator and the "spec tutors/experts" are the SAME shape:
an expert examines something, asks questions, and helps improve it. Making each expert
its own command would push the toolkit past 100 commands (the stated worry). So this is
one `advise` harness parameterized by a persona file - the proven assess (harness +
lenses) pattern - which caps the command surface at one while allowing unlimited
experts (add a persona file + a manifest row).

## How it differs from the eight review personas

The framework already has eight REVIEW personas (QA, testing, UX, architect, engineer,
power user, novice, stakeholder) used to FIND faults. The advise personas are
INTERROGATORS/MENTORS: they ask questions and coach; they improve the artifact
interactively rather than emit a findings register. Different mode, different roster.

## Proposed persona roster (each a well-defined charter, not a label)

- **skeptic** (the "grill me" role): assumes the artifact is flawed; interrogates
  assumptions, missing cases, unstated risks, "what would make this fail / be rejected."
- **spec-editor / requirements-analyst:** turns fuzzy intent into testable requirements;
  hunts ambiguity, missing acceptance criteria, conflicting or unstated requirements.
- **architect:** interrogates design trade-offs, coupling, extensibility, future-proofing
  vs. over-engineering.
- **red-teamer / adversary:** security, abuse, and misuse interrogation.
- **staff-engineer / mentor:** coaches toward the simplest maintainable approach (KISS);
  "what would you cut; where is the accidental complexity."
- **domain-expert / stakeholder-proxy:** "would a real user/buyer want this; what is
  missing for the actual goal."
- **naive-user:** "I do not understand this; explain it; why would I do it this way" -
  surfaces unclear intent and jargon.

Each persona file states: its charter, its questioning style, what "good" looks like
from its viewpoint, and what it should NOT do (e.g. the mentor should not rubber-stamp;
the skeptic should not be merely contrarian). Personas reuse the rigor of the existing
eight-persona definitions.

## Interaction model

- Primarily **interactive** (it is a conversation: ask, listen, refine), consistent with
  the setup-repo/scaffold wizard style. Optional: produce a short written summary of the
  questions raised and the improvements agreed, saved to the run record.
- Can target the current context (no arg beyond the persona) or a named artifact
  (`/advise spec-editor .agents/plans/pending/feature.md`).
- It advises/improves; it does not execute code. If it improves a planning doc, that is
  editing a plan (allowed), not executing it.

## Scope check

- Over-scope: do NOT create a command per persona; do not duplicate the review personas'
  fault-finding role. Keep the roster focused; add personas only when a real advisory
  need is unmet.
- Under-scope: the personas must be genuinely distinct and useful, not seven names for
  the same voice.

## Dependencies / sequencing

- Enables the `/advise <persona>` half of the command-surface redesign (IPD 1).
- The spec-editor persona overlaps the spec/requirements lifecycle workflow (IPD 5);
  decide the division of labor (advise = interactive coaching; spec workflow = produce
  the artifact).

## Required validation

- One `advise` shim (per tool) + persona files; bare `/advise` lists personas and asks;
  a persona conducts a genuine question-driven session; a run-record summary is saved.
- Personas are distinct (a quick read test: the skeptic and the mentor produce visibly
  different sessions on the same artifact).

## Open questions

1. Command word: `/advise` vs `/consult` vs `/coach`. (Avoid clashing with any tool's
   built-in; `/grill-me` specifically is a Gemini built-in, so do NOT reuse that name -
   the skeptic persona covers that role under a neutral command.)
2. Should advise ever write to the artifact directly (with consent), like prose
   interactive mode, or only produce a summary of recommended changes?
3. Roster: build the full seven now, or start with skeptic + spec-editor + architect and
   add the rest on demand via scaffold?

## Approval and execution gate

Proposal only. Approve/reorder before execution. Naming (avoid built-in clashes) and
the persona charters should be settled before building.
