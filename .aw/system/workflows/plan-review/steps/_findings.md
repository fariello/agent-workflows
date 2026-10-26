# Findings, Classification, and Revision Rules

### 2.1 Apply all required views
Review against:
- The engineering rubric below.
- Project principles.
- Domain invariants.
- Plan goals and acceptance criteria.
- The eight personas.
- The security lens.

### 2.2 Record findings
Record each distinct actionable issue. Combine duplicate symptoms under one
root cause. Do not invent findings. A maintainer's sizing or splitting question is an
actionable FINDING to investigate by decomposition, never a signal to dismiss because the
size lint passed.

Classify each finding with:
- **Severity:** `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- **Scope:** `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- **Area:** rubric or project rule.
- **Evidence:** `path:line`, plus the symbol or a quoted string, for example the symbol `mod.func_name` beside its path and line.
- **Remediation Risk:** complexity, usability, security, functionality, and
  overall.
- **Decision:** `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.

Write the findings to BOTH places:

1. The findings table in the final report (below).
2. A typed review record, `.aw/records/reviews/<...>.review.md`, using the same columns.

The record is what makes a severity readable by tooling. Before it, severity survived only as prose,
so a `HIGH` left unfixed gated nothing. This is a transcription of the classification you already
made, not a second classification.

Append a new `## Round <n>` for a re-review rather than editing an earlier round: the gate reads only
the CURRENT (last) round, so a finding you raised in round 1 and fixed in round 2 correctly stops
counting against the plan.

Findings are rows in the current round's single `### Findings` table (columns exactly as `review_findings.FINDING_COLUMNS`: `ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution`). Per-check notes go in a `### Step <check>` subsection beginning with one `- Checked: <what was examined>` line.

Every recommendation the review writes (in an open question, a finding's resolution, or the proofreading issues table) states its strength: `very weak`, `weak`, `medium`, `strong`, or `very strong`.

### 2.3 Remediation Risk and Fix Bar
Overall Remediation Risk is the highest applicable axis rating.

- **Low:** Local, understood, easy to verify, unlikely to harm behavior.
- **Medium:** Bounded uncertainty with a clear verification path.
- **Medium-High:** Material chance of significant complexity, usability harm,
  security weakness, or functional regression.
- **High:** Likely major harm, a foundational unresolved decision, or no safe
  fix from available evidence.

Fix every finding unless overall Remediation Risk is Medium-High or High.

Every deferral MUST state:
- Axis or axes.
- Why the risk reaches the threshold.
- Required decision or evidence.
- Consequence of leaving it unresolved.

Effort, time, cost, and tokens are never valid deferral reasons.

For over-scope, the default fix is removal or explicit deferral from the plan.
That is normally Low risk.

### 2.4 Revise the plan in place
Make surgical edits:
- Preserve valid content and required structure.
- Replace ambiguity instead of appending duplicate prose.
- Add missing guardrails, sequencing, acceptance criteria, tests, validation,
  specification updates, and traceability.
- Remove unsupported or gold-plated scope.
- Keep the plan concise and executable.
- Do not weaken valid requirements.

When a finding spans plans, fix it in the owning plan and cross-reference it
from dependent plans.

When a revision corrects a mechanism, ordering, or classification, the
correction is not complete until every other item in the plan that quotes or
depends on the replaced wording has been swept and reconciled. This sweep
is not limited to `V-*` items: check every item, field, and prose block
(`E-*`, `V-*`, findings, proposed changes, gates, scope paths) against the plan
as it now reads, not merely your own diff. Grep for distinctive tokens of the
superseded wording (e.g. `PHASE_COMMITTED_INCOMPLETE` in `u23gbn`, where round 3
corrected E-06 and V-06 but left V-02 demanding an impossible state). If a stale
sibling belongs to an already executed plan and cannot be edited in place,
record the contradiction in a dated `## Workflow history` note where readers
will find it.

If the approach is fundamentally unsound and cannot be repaired with bounded
edits, mark `REPLAN`, explain why, and describe the minimum shape of a sound
replacement. Do not invent decisions that require the human.

Make sure that every edit you made in this step conforms to the proofreading instructions.

---
## Severity and scope
Severity is for reporting only:
- **BLOCKER:** likely data loss, breach, normal-path failure, silent invariant
  violation, or core-principle violation.
- **HIGH:** material reliability, security, accessibility, maintainability, or
  required-coverage gap.
- **MEDIUM:** real gap on a non-critical path or uncommon condition.
- **LOW:** polish or small clarity improvement.

LOW and MEDIUM findings are fixed by default too.

Scope:
- **IN-SCOPE:** flaw in proposed work.
- **OVER-SCOPE:** not traceable to a driver or requirement.
- **UNDER-SCOPE:** required capability, guardrail, test, migration, or
  documentation is missing.
