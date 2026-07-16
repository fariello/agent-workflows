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

Then prefer LOCATION over CONTENTS for state that is surveyed across many items. When
you need to see the state of many artifacts at once (which plans are pending, which
prompts are queued to run), encode that state in the filesystem itself (directory
placement and filename) rather than only in a line inside each file. A directory listing
reveals the state of every item in one cheap glance; reading a status line inside each
file requires opening every file (costly for a human, and many tokens for an agent).
Location-encoded state also resists rot: the state changes by the act of moving the
file, which cannot be half-done or forgotten the way an in-file marker can, and it is
tool-agnostic (a file tree works everywhere; parsing file contents needs a parser that
can drift). This is why the plan lifecycle uses directories for disposition.

Boundaries (when an in-file marker or a stable path is still right):
- One primary axis per tree. A file lives in exactly one directory, so encode only the
  ONE primary lifecycle axis in the path. Orthogonal or secondary attributes
  (readiness, grouping, ordering) stay as in-file fields. This is why plans keep
  disposition in the directory but `Status:`, `Set:`, and `Order:` in the file.
- Do not move artifacts that are cited by a stable path. Durable knowledge (research
  analysis notes, specs) is referenced by path; there, citation stability outweighs
  glanceability, so keep the path stable and let an in-file `Status:` carry the rare
  state change (for example current vs superseded).
- If the file must be opened anyway for the task, an in-file marker is fine.

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
