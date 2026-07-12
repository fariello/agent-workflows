# Guiding Principles

The values that guide work in this repository, and especially the design of the
`release-review/` framework. These are the principles we actually hold and apply, not
aspirations. Where a principle is also enforced mechanically, the enforcing location
is noted.

## 1. Fix by default; justify deferral, not action

The cost of a fix (effort, time, tokens) is not a reason to skip it. Address findings
by default; defer only when the *Remediation Risk* of the fix itself is Medium-High or
higher (complexity, usability, security, or functionality). Severity is for
reporting; Remediation Risk is for deciding.
*Enforced in `release-review/fix-decision-policy.md`.*

## 2. Honest documentation over aspirational documentation

Docs describe what the software actually does today. Intent and rationale recovered
from conversation are verified or clearly marked "inferred, needs confirmation" - we
never manufacture fiction to fill a gap.

## 3. Self-documenting and learn-as-you-go

Software should teach the user as they go (clear names, helpful defaults, actionable
errors, good first-run guidance) so they need not read a manual or take a course.
Prefer making the product self-explanatory over compensating with more documentation.
Minimize user effort; an unnecessary action is a defect.

## 4. Durable knowledge for cold-start handoff

A competent engineer or an LLM with zero prior context should be able to understand a
project's intent, philosophy, architecture, and the *why* behind major decisions from
its own tracked docs. We hold ourselves to this: this repository keeps `README.md`,
`ARCHITECTURE.md`, `DECISIONS.md`, and this file for exactly that reason.

## 5. Externalize state; do not trust memory

For multi-step work, the authoritative record lives in files, not in conversational
memory or ephemeral task lists. This makes work recoverable, auditable, and robust to
context degradation.

## 6. KISS, and guard against scope creep

Prefer the simplest design that meets the need. Because "fix by default" invites
gold-plating, the complexity axis is the deliberate counterweight: do not add
abstraction, features, or dependencies not traceable to a real need. A new noun does
not automatically require a new model or abstraction; compare semantics, not names.
Follow the generality ladder: prefer variation as data or config first, then a shared
core with thin specialization, and only use bounded special cases when justified.
Do not build for hypothetical needs.

## 7. Solve the general case; stay project-agnostic

Generalize project-specific insight into universal concepts rather than hardcoding one
stack's checklist. The framework must work across languages, frameworks, and project
types. Prefer variation as data or config before code.

## 8. Single source of truth; no drift

Each policy, table, or rule lives in exactly one canonical place and is referenced
elsewhere. Duplicated normative content is a maintenance and correctness hazard.

## 9. Design instructions for the model that will run them

Instructions for LLMs are engineered for reliable execution: forcing functions,
exit-gate checklists, MUST/SHOULD tiering, and context-assembly ordering that respects
how attention degrades. Reliability comes from structure, not from writing more prose.

## 10. Safety and reversibility

Default to non-destructive action. Do not push, publish, deploy, expose secrets, or
change public contracts without explicit permission and analysis. Prefer staged,
reversible changes and a clear record of what was done.
