# Plan Review (pre-execution plan / IPD reviewer)

Treat this file as the controlling instruction for reviewing a proposed plan
before implementation, then improving that plan in place.

The goal is a plan that is safer, clearer, executable, and more likely to
produce a correct, secure, usable, maintainable, and principle-aligned result.

## Memory kernel

These rules are mandatory throughout the run:

1. Review and edit planning documents only. Do not implement code or config.
2. Verify material claims against repository evidence. Do not guess.
3. Fix findings by default. Severity never decides whether to fix.
4. Defer only when the fix itself has Medium-High or High Remediation Risk on
   complexity, usability, security, or functionality.
5. Effort, time, cost, and tokens never justify deferral.
6. Resolve every open question with the human when interaction is available.
7. Never push. Do not stage or commit unrelated changes.
8. The reviewed/not-reviewed enumeration is the final output. Print nothing
   after it.

Fix decisions use `../release-review/fix-decision-policy.md`.
Use the eight personas from `../release-review/00-run-protocol.md`: QA/QC,
testing/regression, UI/UX, architect, software engineer, power user, novice,
and stakeholder. Apply security as a mandatory cross-cutting lens.

If either sibling file is absent, apply these rules from memory:

- Fix by default, gated only by Remediation Risk.
- Review from multiple technical, user, and stakeholder perspectives.

---

## Boundaries

Do not change application code, tests, runtime configuration, infrastructure,
production data, or deployment state.

Do not run migrations or commands that alter application state.

Producing or editing a plan is not executing it.

---

## Step 0: Establish scope and project rules

Before reviewing:

1. Build a scope ledger containing every requested candidate plan.
2. Mark each candidate:
   - `ELIGIBLE` - review it.
   - `NOT REVIEWED` - skip it and record the exact reason.
3. Read the applicable instruction hierarchy, including repository and nested
   agent instructions, guiding principles, contributor rules, plan templates,
   lifecycle rules, and specifications.
4. Use the project's stated precedence rules. If a conflict remains, record an
   open question. Do not silently choose.
5. Discover the plan contract:
   - location and filename rules;
   - required headings and front matter;
   - status vocabulary and lifecycle;
   - approval, specification, traceability, history, and commit rules.
6. Discover the real project context:
   - project type, languages, frameworks, production runtime and data store;
   - deployment, integrations, tenancy, security model, and testing stack.
7. Identify domain invariants from authoritative specs, principles, ADRs,
   code, tests, constraints, and confirmed conversation context.
8. If behavior, policy, workflow, API, authorization, state, or domain rules
   change, require the plan to update the authoritative specification or docs.

If no project principles exist, use the fallback principles from
`../release-review/00-run-protocol.md` and record that choice:

- intuitive and self-documenting;
- general-case and configurable;
- KISS;
- honest documentation.

The final enumeration MUST contain every item in the scope ledger and no
incidental files.

---

## Step 1: Ground the review and snapshot the plans

For each eligible plan:

1. Read the full plan.
2. List every material file, requirement, issue, ADR, API, schema, test, and
   behavior on which it relies.
3. Open the actual evidence.
4. Verify material claims with `path:line` citations.
5. Record missing, stale, contradictory, or inaccessible evidence.
6. Do not infer details the evidence does not support.

If evidence is unavailable, record the limitation. Add a finding when the
missing evidence prevents a reliable plan. Create an open question when human
input is required.

### Pre-review snapshot

Before editing:

1. Inspect Git status.
2. Select only eligible plan files.
3. If a target plan is untracked or modified, commit it verbatim as:

   `plan: pre-review snapshot of <scope>`

4. If every target plan is committed and unchanged, skip the snapshot.
5. Never include unrelated files.
6. Never amend, reset, rebase, discard user changes, or push.

If Git is unavailable or a safe commit cannot be made, continue when safe and
report the reason.

---

## Step 2: Review and revise

Review each eligible plan against:

- its goals and acceptance criteria;
- the project contract and guiding principles;
- discovered domain invariants;
- all eight personas;
- the security lens;
- the engineering rubric below.

### Record findings

Record each distinct actionable finding. Combine duplicate symptoms under one
root cause. Do not invent findings.

For each finding assign:

- **Severity:** `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- **Scope:** `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- **Area:** rubric section and project rule.
- **Evidence:** `path:line`.
- **Remediation Risk:** complexity, usability, security, functionality, and
  overall rating.
- **Decision:** `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.

### Remediation Risk

Overall Remediation Risk is the highest applicable axis rating:

- **Low:** local, understood, easily verified, unlikely to cause harm.
- **Medium:** bounded uncertainty with a clear verification path.
- **Medium-High:** material chance of significant complexity, usability harm,
  security weakness, or functional regression.
- **High:** likely major harm, foundational uncertainty, or no safe fix from
  available evidence.

Fix every Low or Medium risk finding.

A deferral MUST state:

- the Medium-High or High axis;
- why the fix is risky;
- what decision or evidence is needed;
- the consequence of leaving it unresolved.

For over-scope, the default fix is removal or explicit exclusion. Removing
unsupported scope is normally Low risk.

### Revise in place

Make surgical edits:

- preserve valid content and required structure;
- replace ambiguity instead of appending duplicate prose;
- add missing guardrails, sequencing, acceptance criteria, tests, rollout,
  recovery, specification work, and validation;
- remove unsupported or gold-plated scope;
- keep the plan concise and executable;
- do not weaken valid requirements.

When a finding spans plans, fix it in the owning plan and cross-reference it
from dependent plans. Do not duplicate the same requirement.

If the approach cannot be repaired with bounded edits, mark `REPLAN`, explain
why, and describe the minimum shape of a sound replacement. Do not invent
product decisions that require the human.

---

## Engineering rubric

Apply only relevant items. `Not applicable` requires a reason.

### A. Plan completeness

Verify problem, goals, non-goals, scope, exclusions, acceptance criteria,
existing mechanisms to reuse, target components, ordered steps, dependencies,
assumptions, open questions, validation, rollout, rollback, recovery, and
follow-up ownership.

The plan must be executable by another qualified agent or developer without
inventing architecture.

### B. Data and integrity

Check transactions, rollback, concurrency, uniqueness, ordering, lost updates,
idempotency, production dialect, migrations, indexes, audit integrity,
provenance, retention, deletion, restoration, and archival where relevant.

### C. Security, privacy, and abuse

Check verified identity, default-deny authorization, object/row and tenant
scope, privilege paths, secrets, boundary validation, injection, unsafe
outbound access, uploads, rate/replay controls, privacy minimization, and safe
errors.

### D. Architecture, scale, and KISS

Prefer existing canonical mechanisms and one implementation per action.
Justify new models, dependencies, services, abstractions, queues, caches, and
execution paths. Architect required seams, but do not build for hypothetical
scale or reuse.

### E. Invariants and compatibility

Name affected invariants and map each to a test. Preserve intended correct
behavior unless an approved requirement or bug fix changes it. Do not freeze
accidental behavior that project policy says to replace. Identify public API,
schema, configuration, migration, and integration effects.

### F. Testing and verification

Require concrete happy, validation, authorization, denial, constraint,
rollback, retry, concurrency, integration-failure, accessibility, contract,
end-to-end, and performance tests where relevant. Use production-equivalent
dependencies when differences matter. State exact validation commands and
expected evidence.

### G. UX and accessibility

Minimize user effort. Define loading, empty, error, success, and recovery
states. Preserve input after correctable errors. Provide contextual help.
Require keyboard operation, focus behavior, semantics, accessible names,
contrast, and assistive-technology feedback where relevant. Include novice,
power-user, and stakeholder outcomes.

### H. Operations and documentation

Define logs, correlation, metrics, health, alerts, timeouts, retries, degraded
behavior, reconciliation, rollout, rollback, and recovery where relevant.
Keep specifications, docs, examples, schemas, and release notes synchronized.
Do not log secrets or unnecessary sensitive data.

---

## Step 3: Resolve open questions interactively

Before the final report:

1. Collect pre-existing questions, review-created questions, unresolved
   instruction conflicts, and decisions needed for repair or replan.
2. Resolve questions already answered by authoritative evidence. Cite it.
3. Deduplicate overlapping questions.
4. Mark which questions block correctness, security, scope, architecture, or
   GO readiness.

In an interactive run, ask one to three related questions at a time.

For each question provide:

1. **Decision needed.**
2. **Context.**
3. **Why it matters.**
4. **Options.**
5. **Trade-offs.**
6. **Recommendation and one-line reason.**

Use plain language. Define acronyms and identifiers. Do not guess.

After each answer:

1. Record it in the owning plan.
2. Resolve or rewrite the open question.
3. Apply consequent edits.
4. Re-run affected rubric areas.
5. Ask any newly required dependent question.

Continue until no resolvable question remains.

Treat a run as non-interactive only when no human interaction channel exists.
A delayed response is not non-interactive.

In a genuinely non-interactive run:

- leave questions explicitly `OPEN`;
- use verdict `REVIEWED - OPEN QUESTIONS`;
- recommend `NO-GO`.

---

## Step 4: Finalize and commit

For each reviewed plan confirm:

1. Every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.
2. Every deferral meets the Fix Bar.
3. Every resolved decision is written into the plan.
4. Required specification and documentation work is included.
5. Tests and validation cover affected invariants.
6. The plan does not claim implementation or execution.

Apply the project's review status. If it uses `Status`, set `reviewed` unless
its contract requires another review-complete value.

`reviewed` does not mean approved, GO, ready to execute, or executed.

Append or update:

```markdown
## Workflow history

- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>
```

Use `unknown` if the agent/model identifier is unavailable.

### Hardened-result commit

After all edits and interactive decisions:

1. Commit only reviewed plans and any required run record.
2. Use:

   `plan-review: harden <scope> (revisions applied)`

3. Never include unrelated files.
4. Never push.
5. Report a skipped or failed commit exactly.

---

## Severity, scope, verdict, and readiness

Severity is for reporting and ordering only:

- **BLOCKER:** likely data loss, corruption, breach, normal-path failure,
  silent invariant violation, or core-principle violation.
- **HIGH:** material reliability, security, accessibility, maintainability,
  scalability, or required-coverage gap.
- **MEDIUM:** real non-critical gap or ambiguity.
- **LOW:** polish or small clarity improvement.

Scope:

- **IN-SCOPE:** flaw in proposed work.
- **OVER-SCOPE:** unsupported work. Default fix: remove or exclude.
- **UNDER-SCOPE:** required work is missing. Default fix: add it.

Use exactly one verdict:

- **`APPROVE`** - no revisions needed; no questions remain; all deferrals pass.
- **`APPROVE WITH REVISIONS APPLIED`** - findings fixed; no questions remain;
  all deferrals pass.
- **`REVIEWED - OPEN QUESTIONS`** - review complete, but human decisions remain.
- **`REJECT - NEEDS REPLAN`** - approach is unsound and not safely patchable.

Readiness:

- **GO:** verdict is APPROVE or APPROVE WITH REVISIONS APPLIED, all questions
  resolved, and no unfixed BLOCKER or HIGH remains.
- **NO-GO:** any question remains, any BLOCKER or HIGH remains unfixed, or the
  verdict is REVIEWED - OPEN QUESTIONS or REJECT - NEEDS REPLAN.

A reviewed plan may still be NO-GO.

---

## Required final report

Do not issue the report before the interactive loop is complete unless the run
is genuinely non-interactive.

Use this exact order and cite evidence as `path:line`:

```markdown
## Plan Review - <plan name(s)>

Verdict: <APPROVE | APPROVE WITH REVISIONS APPLIED | REVIEWED - OPEN QUESTIONS | REJECT - NEEDS REPLAN>

### Review scope

ELIGIBLE:
- <plan file>

NOT ELIGIBLE:
- <plan file>: <reason>

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | <level> | <scope> | <ref> | <path:line> | <finding> | C:<rating>; U:<rating>; S:<rating>; F:<rating>; Overall:<rating> | <FIXED|DEFERRED|OPEN|REPLAN> | <resolution> |

### Edits applied

- `<plan file>` - `<section>`: <edit>

### Deferred and open

- `<finding ID>` - `<DEFERRED | OPEN>`:
  - Reason: <reason>
  - Remediation Risk: <Medium-High | High>
  - Axis: <complexity | usability | security | functionality>
  - Required decision or evidence: <needed>
  - Consequence if unresolved: <impact>

### Commit result

- Pre-review snapshot: <hash | skipped because unchanged | not applicable | failed with reason>
- Hardened result: <hash | not applicable | failed with reason>
- Push: not performed

### Plans reviewed and not reviewed

REVIEWED:
- `<plan file>`: <GO | NO-GO> - <reason>.
  Verdict: <verdict>.
  Open questions: all resolved interactively | <N open, blocks GO>.
  Required next step: <approval | decision | replan | other>.

NOT REVIEWED:
- `<plan file>`: <exact reason>.
```

The `### Plans reviewed and not reviewed` section MUST be the final output.
Enumerate every file from the Step 0 scope ledger. Print nothing after it.
