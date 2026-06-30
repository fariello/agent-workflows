# Assess (single-concern assessment that produces an Implementation Plan Document)

Treat this file as the controlling instruction for a **focused, single-concern**
review of a project. You **assess** one concern deeply, then **propose** the work as a
dated **Implementation Plan Document (IPD)** in the project's pending-plans directory.
You do **not** change project code, and you do **not** execute the plan. A human
reviews and approves the IPD (optionally via the `plan-review` workflow) before any
execution.

This is the "assess and propose" front end of the workflow pipeline:

```
assess-<concern>  ->  IPD in pending/  ->  plan-review (optional)  ->  human approval  ->  execution
```

A **lens** file selects the concern (performance, security, accessibility, ...) and
supplies the concern-specific rubric and lead personas. The invoking command names the
lens; read it and apply it on top of this shared protocol. If no lens was provided,
ask the user which concern to assess (or infer it from `$ARGUMENTS`).

`$ARGUMENTS`, if present, narrows the scope (a subdirectory, module, feature, or set
of files) and/or carries options. Honor it; otherwise assess the whole project.

It shares this framework's policies rather than redefining them (the release-review
runbook is a sibling under `.agents/workflows/`):

- **Fix Bar - applied here as "what to propose":** `../release-review/fix-decision-policy.md`.
  Propose addressing every finding by default; recommend deferring only when the
  *Remediation Risk* of the fix is Medium-High or higher (complexity / usability /
  security / functionality). Severity is for reporting; Remediation Risk gates the
  recommendation. Effort/time/token cost are never a reason to defer. Record
  Remediation Risk on every proposed change.
- **Eight personas:** `../release-review/00-run-protocol.md`. Lead with the personas
  the lens names, but let the others surface what the leads miss - especially the
  novice and stakeholder views.

If those files are absent (this workflow copied alone), apply the same rules from
memory: fix-by-default gated by Remediation Risk, and multi-perspective review.

---

## What this workflow does NOT do

- It does not modify application code, tests, configuration, or docs. It produces a
  plan only. (Editing the IPD it writes is not "changing the project".)
- It does not execute the plan, and it does not move the IPD out of `pending/`.
- It does not push, deploy, or change remote state.

---

## Step 0: Discover the project's conventions (do not hardcode)

1. **Project intent, audience, stack, and scope** - enough to judge the concern in
   context and to ground the personas.
2. **Guiding principles** - `GUIDING_PRINCIPLES.md` or equivalent; or the universal
   fallback in `../release-review/00-run-protocol.md`.
3. **Pending-plans / IPD location and format** - where plans live and any required
   structure. Discover the project's convention (e.g. `.agents/plans/pending/`,
   `docs/rfcs/`, an ADR dir). If none exists, create and use
   `.agents/plans/pending/`. Record which you chose.
4. **Contributor contract** - `AGENTS.md`/`CONTRIBUTING.md` for plan/spec-sync rules.
5. **Apply the review scope exclusions** from `../release-review/00-run-protocol.md`:
   do not assess the framework's own directory (`.agents/workflows/`) or
   `repository-review/` run records as if they were the project.

Then read the selected lens file and adopt its focus, lead personas, and rubric.

---

## Operating mode (assess, then propose)

1. **Assess** the concern deeply across the project (or the `$ARGUMENTS` scope). Read
   the actual source/docs/UI/config to verify, do not infer from names. Reason from
   the lens's lead personas and let the others contribute. Apply the lens rubric.
2. **Record every finding**, however small, with a **Severity** (impact if left
   alone: Blocker / High / Medium / Low) and a **Remediation Risk** (the Fix Bar gate
   for whether to propose acting now). Note the persona(s) that surfaced it.
3. **Propose** the work as concrete, ordered changes in the IPD: what to change,
   where (`file:line` where known), why, the Remediation Risk, and how to validate.
   Fix-by-default: propose acting on everything unless Remediation Risk is Medium-High
   or higher (then propose deferral with the named axis). Down-scope to the safe part
   where possible; never silently drop a finding.
4. **Guard scope (KISS):** the Complexity axis is the counterweight to fix-by-default.
   Flag over-scope (untraceable to a need - propose removal/deferral) and under-scope
   (a needed capability that is missing - propose adding it). Do not gold-plate.
5. **Write the IPD** to the pending-plans directory using `templates/ipd.md`, named
   with a date and the concern, e.g.
   `<plans-pending>/YYYY-MM-DD-assess-<concern>.md`.
6. **Report and stop.** Summarize the verdict and the IPD path, and ask the user to
   review and approve (optionally via `plan-review`) before execution. Do not execute.

---

## The IPD you produce

Use `templates/ipd.md`. It must contain: goal and concern; scope (and any
`$ARGUMENTS` narrowing); the project conventions discovered; a findings table
(severity + Remediation Risk + persona + evidence); proposed changes as ordered,
validatable steps with Remediation Risk; deferred items with the named axis; required
tests/validation; spec/doc sync if behavior changes; open questions; and an explicit
**approval and execution gate** stating the plan must be human-approved before
execution and is not auto-run.

Keep the IPD honest and self-contained enough that a different agent or engineer could
execute it later with no other context (the cold-start standard).

---

## Required report format (to the user, after writing the IPD)

```
## Assessment - <concern> <scope if narrowed>
Verdict: <strong / adequate / needs work / at risk> for <concern>
IPD written: <path>

### Top findings
| ID | Severity | Remediation Risk | Persona | Finding |
|----|----------|------------------|---------|---------|

### Proposed plan (summary)
- <ordered, high-level summary of the proposed changes>

### Deferred (with reason)
- <finding>: Remediation Risk <Medium-High|High> on <axis> because <reason>.

Next step: review the IPD (optionally run plan-review on it) and approve before
execution. This workflow does not execute the plan.
```

Be rigorous and specific, cite evidence, and do not invent issues where there are
none. Default to proposing the fix - even small ones - because the only reason to
leave a finding out of the plan is that the fix itself carries Medium-High-or-higher
Remediation Risk. Never let effort be the reason, and never silently drop a finding.
