# Plan Review (pre-execution plan / IPD reviewer)

Treat this file as the controlling instruction for reviewing a proposed plan
before implementation, then improving that plan in place.

The goal is a plan that is materially safer and more likely to produce a
reliable, usable, secure, intuitive, maintainable, and principle-aligned result.

This is the plan-time sibling of release review. It reviews the written plan
before code is built.

It shares this framework's policies rather than redefining them:

- **Fix decisions use `../release-review/fix-decision-policy.md`.**
  Fix by default. Defer only when the Remediation Risk of the fix itself is
  Medium-High or High on complexity, usability, security, or functionality.
  Severity is for reporting and ordering only. Effort, time, and token cost
  never justify deferral.
- **Use the eight personas in `../release-review/00-run-protocol.md`.**
  Apply QA/QC, testing/regression, UI/UX, architect, software engineer, power
  user, novice, and stakeholder views. Security is a mandatory cross-cutting
  lens, not an additional persona.

If either sibling file is absent, apply the same rules from memory:

- Fix by default, gated only by Remediation Risk.
- Review from multiple technical, user, and stakeholder perspectives.

---

## What this command does NOT do

Review and revise planning documents only.

Do not change application code, tests, runtime configuration, infrastructure,
or production data.

Do not run migrations or commands that change application state.

Producing or editing a plan is not executing it.

---

## Step 0: Establish scope and discover project conventions

Complete this step before evaluating or editing any plan.

### 0.1 Build the review-scope ledger

Identify every plan file explicitly requested or selected by the project's
review workflow.

Record each candidate as one of:

- `ELIGIBLE` - will be reviewed.
- `NOT REVIEWED` - skipped, with the exact reason.

Use the project's status vocabulary and eligibility rules if they exist.

If no eligibility rule exists, review an explicitly requested plan unless it
is missing, unreadable, malformed beyond review, or not a planning document.

A plan referenced only as evidence is not part of the review scope unless it
is explicitly added to the ledger.

The final reviewed/not-reviewed enumeration MUST include every file in this
ledger and no incidental files.

### 0.2 Read controlling instructions in precedence order

Discover and read the project's applicable instruction hierarchy.

Include, as relevant:

1. Repository and directory-scoped agent instructions.
2. Guiding principles or equivalent product/architecture rules.
3. Contributor and workflow rules.
4. Plan lifecycle and status rules.
5. Specification and documentation obligations.
6. The target plan and its referenced plans or decisions.

Do not assume fixed filenames.

Common locations include:

- `AGENTS.md`
- `GUIDING_PRINCIPLES.md`
- `PRINCIPLES.md`
- `CONTRIBUTING.md`
- `README.md`
- ADRs
- RFC guidance
- Plan templates
- Tool-specific instruction files

If instructions conflict, apply the project's stated precedence rules.

If no precedence rule resolves the conflict, record it as an open question.
Do not silently choose one rule.

### 0.3 Discover the plan contract

Determine:

- Where plans live.
- Required headings and front matter.
- Status vocabulary and lifecycle.
- Required approval or review steps.
- Required specification updates.
- Required requirement IDs or traceability.
- Required workflow-history format.
- Commit rules.

Review each plan against its actual contract.

### 0.4 Discover the real implementation context

Determine the actual:

- Project type.
- Languages and frameworks.
- Production runtime.
- Production data store and dialect.
- Deployment model.
- External services and integrations.
- Security and tenancy model.
- Testing stack.

Apply the rubric to the production target, not only to tests or local
development.

### 0.5 Discover domain invariants

Identify the business and correctness truths the project must preserve.

Use:

- Specifications.
- Guiding principles.
- ADRs and accepted plans.
- Existing code and tests.
- Data constraints.
- The current conversation.
- Other authoritative project evidence.

These invariants become named anti-regression targets.

### 0.6 Confirm documentation impact

If a plan changes user-visible behavior, policy, workflow, API behavior,
authorization, state, or domain rules, confirm it includes updates to the
authoritative specification or documentation.

If missing, add the required synchronization work and traceability.

If no project principles exist, use the universal fallback principles from
`../release-review/00-run-protocol.md`:

- Intuitive and self-documenting.
- General-case and configurable.
- KISS.
- Honest documentation.

Record that the fallback was used.

---

## Step 1: Assemble evidence before judging the plan

For each eligible plan:

1. Read the entire plan.
2. List every file, requirement, issue, ADR, API, schema, test, or behavior the
   plan relies on.
3. Open the actual referenced evidence.
4. Verify material claims against `file:line` evidence.
5. Identify missing, stale, contradictory, or inaccessible evidence.
6. Do not infer implementation details that the evidence does not support.

If evidence cannot be accessed:

- Do not fabricate it.
- Record the limitation.
- Add a finding if the missing evidence prevents a reliable plan.
- Convert it to an open question when human input is required.

---

## Step 2: Review, classify, and revise

Execute these steps in order.

### 2.1 Review through all required perspectives

Apply:

- The cross-cutting rubric below.
- Every project-specific principle.
- Every discovered domain invariant.
- The eight personas.
- The mandatory security lens.
- The plan's own stated goals and acceptance criteria.

### 2.2 Record each distinct actionable finding

Record every real finding, including:

- Correctness bug.
- Missing requirement.
- Security or privacy gap.
- Authorization or audit gap.
- Ambiguity.
- Unsupported claim.
- Missing validation or test.
- Missing rollout or recovery step.
- Over-scope.
- Under-scope.
- Unnecessary complexity.
- Usability or accessibility issue.
- Documentation or traceability gap.
- Small polish issue that materially improves execution reliability.

Combine duplicate symptoms under one root-cause finding.

Do not invent findings.

### 2.3 Classify each finding

Assign:

- **Severity:** `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`.
- **Scope:** `IN-SCOPE`, `OVER-SCOPE`, or `UNDER-SCOPE`.
- **Area:** rubric section and project rule.
- **Remediation Risk:** rate the proposed fix on all four axes:
  complexity, usability, security, and functionality.
- **Decision:** `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.

Severity never decides whether to fix.

### 2.4 Apply the Fix Bar

Fix every finding by default.

Defer only when the fix itself has overall Remediation Risk of
`Medium-High` or `High`.

Overall Remediation Risk is the highest applicable axis rating.

Use these ratings:

- **Low:** Local, well-understood, easily verified, and unlikely to cause
  adverse behavior.
- **Medium:** Bounded change with manageable uncertainty and a clear
  verification path.
- **Medium-High:** Material chance the fix will introduce significant
  complexity, usability harm, security weakness, or functional regression.
- **High:** The fix is likely to create major harm, requires a foundational
  decision, or cannot be made safely from available evidence.

A deferral MUST state:

- The affected axis or axes.
- Why the fix is Medium-High or High.
- What decision or evidence is needed.
- The consequence of leaving the finding unresolved.

Effort, time, cost, and token use are never valid reasons to defer.

For over-scope, the default fix is removal or explicit deferral from the plan.
Removing unsupported scope is normally Low Remediation Risk.

### 2.5 Revise the plan in place

Make surgical, well-anchored edits.

- Preserve valid content.
- Preserve the required plan structure.
- Replace ambiguous text instead of appending a duplicate explanation.
- Add missing guardrails, acceptance criteria, sequencing, tests, and
  verification.
- Remove unsupported or gold-plated scope.
- Keep the plan executable and concise.
- Do not weaken an existing valid requirement.
- Do not convert a clear plan into a generic essay.

When a finding spans plans:

- Fix it in the owning plan.
- Add precise cross-references in dependent plans.
- Do not duplicate the same requirement in several plans.

If the fundamental approach is unsound and cannot be safely repaired with
bounded edits:

- Mark the finding `REPLAN`.
- Explain the failure.
- Describe the minimum shape of a sound replacement approach.
- Do not invent detailed design decisions that require human judgment.

---

## Step 3: Resolve all open questions interactively

This step is mandatory before the final report.

### 3.1 Build the open-question list

Collect:

- Pre-existing unresolved questions.
- Questions created by findings.
- Instruction conflicts.
- Decisions required to repair or replan the approach.

Do not ask the human a question that authoritative project evidence already
answers. Resolve it from evidence and cite the source.

Deduplicate overlapping questions.

Identify which questions block:

- Plan correctness.
- Security or compliance.
- Scope.
- Architecture.
- GO readiness.

### 3.2 Ask the human

In an interactive run, ask and wait for answers before issuing the final
report.

Ask one to three tightly related questions per prompt.

For each question provide:

1. **Decision needed:** the question in plain language.
2. **Context:** what prompted it.
3. **Why it matters:** practical effect on the plan.
4. **Options:** concise, concrete choices.
5. **Trade-offs:** the meaningful differences.
6. **Recommendation:** one option and a one-line reason.

Define acronyms and internal identifiers on first use.

Do not guess.

Do not bury the recommendation.

### 3.3 Apply each answer

After each response:

1. Record the decision in the owning plan.
2. Mark or rewrite the open question as resolved.
3. Apply all consequent plan edits.
4. Re-run affected rubric sections.
5. Identify any new dependent question.
6. Continue until no resolvable open question remains.

### 3.4 Non-interactive exception

Treat a run as non-interactive only when the execution environment explicitly
provides no human interaction channel.

Do not treat a delayed response as non-interactive.

In a genuinely non-interactive run:

- Leave questions explicitly `OPEN`.
- Do not invent answers.
- State what decision is needed.
- Use verdict `REVIEWED - OPEN QUESTIONS`.
- Recommend `NO-GO`.

---

## Step 4: Finalize plan review state

For each reviewed plan:

1. Confirm every finding is `FIXED`, `DEFERRED`, `OPEN`, or `REPLAN`.
2. Confirm every deferral meets the Fix Bar.
3. Confirm every resolved question is written into the plan.
4. Confirm specification and documentation work is included when required.
5. Confirm tests and validation map to each affected invariant.
6. Confirm the plan remains a plan and does not claim execution.
7. Apply the project's review status.

If the plan uses `Status`, set it to `reviewed` unless the project contract
requires another review-complete status.

`reviewed` means the review occurred. It does not mean:

- Human approved.
- Ready to execute.
- GO.
- Executed.

Only human sign-off or the project's approval workflow may set `approved`.

Append or update:

```markdown
## Workflow history

- <date> /plan-review (<agent/model>): <verdict>; <finding IDs>
```

Do not fabricate the agent or model identifier. Use the available tool/model
name, or `unknown` if it is unavailable.

---

## Commit contract: capture before and after review

Create at most two commits for the review run.

Never push.

Never amend, reset, rebase, or discard user changes.

Never stage unrelated files.

### Commit 1: pre-review snapshot

Before editing:

1. Inspect repository status.
2. Identify only the eligible target plan files.
3. If any target plan is untracked or has uncommitted changes, commit those
   target plan files verbatim.
4. Use:

   `plan: pre-review snapshot of <scope>`

5. If all target plans are already committed and unchanged, skip this commit.

The skipped snapshot is expected and is not an error.

### Commit 2: hardened result

After all revisions and interactive decisions are applied:

1. Commit only the reviewed plan files and any required review run record.
2. Use:

   `plan-review: harden <scope> (revisions applied)`

3. Do not include unrelated changes.
4. Never push.

If Git is unavailable, the repository is not a Git repository, the files are
not tracked, or a required commit fails:

- Continue the review when safe.
- Do not bypass hooks or safety controls unless project instructions allow it.
- Report exactly why the commit was not created.

---

## Cross-cutting engineering rubric

For every item:

- Verify the plan addresses it, or
- Verify that it is explicitly and correctly out of scope.

`Not applicable` requires a reason.

Apply only what is relevant to the discovered project type.

### A. Data-layer correctness and integrity

- **Atomicity:** dependent writes use a real transaction and rollback.
- **Concurrency:** identify races, locking, uniqueness, ordering, and lost
  updates where relevant.
- **Idempotency:** retries cannot double-apply or double-respond.
- **Production compatibility:** queries, parameters, types, and constraints
  work on the production data store and dialect.
- **Migrations:** schema changes are versioned, tested, and recoverable.
  Use expand/contract when zero-downtime compatibility is required.
- **Indexes:** queried, joined, constrained, and audit keys are indexed when
  justified by expected access patterns.
- **Audit integrity:** append-only or tamper-evident records remain
  concurrency-safe and queryable.
- **Data lifecycle:** retention, deletion, restoration, and archival behavior
  are explicit when relevant.

### B. Security, privacy, and abuse resistance

- **Authentication:** identity comes only from verified sources. No privileged
  default identity.
- **Authorization:** default-deny, route/action checks, object or row checks,
  and tenant or organization scoping.
- **Privilege:** justify bypasses, impersonation, delegation, and break-glass
  behavior.
- **Secrets:** no hardcoded secrets. Use approved secret storage and fail
  safely when required secrets are absent.
- **Boundary validation:** validate type, size, range, format, and unknown
  fields at trust boundaries.
- **Injection and outbound access:** parameterize commands and queries. Control
  unsafe URL fetching, redirects, and external calls where relevant.
- **Uploads:** validate content and size, isolate processing, and include
  malware scanning when risk requires it.
- **Abuse controls:** rate limits, replay protection, quotas, or anti-automation
  work across the actual deployment model.
- **Privacy:** minimize collection, exposure, logging, retention, and export of
  sensitive data.
- **Errors:** do not expose stack traces, secrets, or sensitive internals.

### C. Scalability and architecture seams

Use the rule: architect the seam, provision for current needs.

- Avoid request-path local state that incorrectly assumes one process or node.
- Define connection pooling and resource limits.
- Choose tenancy, partition, or ownership keys early when the domain needs
  them.
- Move slow or unreliable side effects off the synchronous path when required.
- Async work must be durable, retryable, idempotent, observable, and have a
  terminal failure path.
- If caching is proposed, define consistency, invalidation, and failure
  behavior.
- Correctness-critical status must not silently rely on stale data.
- Avoid hardcoded clock assumptions. Make time controllable in tests.
- Do not add scale infrastructure without a real requirement.

### D. Anti-regression and invariant preservation

- Name each affected domain invariant.
- Route each invariant to a concrete test.
- Preserve current correct behavior unless the plan explicitly fixes a bug or
  changes an approved requirement.
- For risky refactors, add characterization tests for intended correct
  behavior before the change.
- Do not freeze accidental behavior that project policy says should be
  replaced, especially in a pre-release project.
- Treat unexplained behavior changes as blockers.

### E. Observability, rollout, and operability

- Define structured logs and correlation identifiers where relevant.
- Define metrics for new success and failure paths.
- Define health and readiness behavior.
- Map actionable alerts to an owner and response procedure.
- Define timeout, retry, backoff, and degraded behavior for dependencies.
- Define rollout, rollback, reconciliation, and recovery.
- Use feature flags only when they solve a real rollout or safety need.
- Prevent logs and telemetry from exposing secrets or unnecessary sensitive
  data.

### F. Testing, verification, and test data

Require concrete tests for applicable behavior:

- Happy paths.
- Validation failures.
- Authorization matrix.
- Cross-tenant or cross-scope denial.
- Constraints and invariants.
- Transactions and rollback.
- Retry and idempotency.
- Concurrency.
- Integration failures.
- Accessibility.
- API or contract compatibility.
- End-to-end behavior.
- Load or performance limits when relevant.

Use production-equivalent dependencies when dialect or runtime differences
matter.

Keep fixtures and seeds realistic enough to preserve important edge cases.

State the exact commands, environments, and evidence that will verify the
plan.

### G. KISS and cost discipline

- Justify every new dependency, service, abstraction, framework, or execution
  path.
- Explain why the existing mechanism cannot satisfy the requirement.
- Prefer the smallest correct design.
- Flag premature complexity.
- Flag missing seams that would force unsafe duplication later.
- Do not treat implementation effort as Remediation Risk.
- Do not optimize for hypothetical scale or reuse.

### H. Guiding principles, usability, and accessibility

- Map the plan to each applicable project principle.
- Replace vague compliance claims with verifiable outcomes.
- Minimize user actions, repeated entry, unnecessary steps, and precision
  interaction.
- Define loading, empty, error, success, and recovery states.
- Preserve user input after correctable errors.
- Provide contextual help for non-obvious actions.
- Require keyboard operation, focus behavior, semantic structure, accessible
  names, contrast, and assistive-technology feedback when relevant.
- Include novice, power-user, and stakeholder outcomes.
- Prevent silent failure.

### I. Domain invariants

For every invariant discovered in Step 0:

- State how the plan preserves or intentionally changes it.
- Cite the authoritative source.
- Map it to implementation work.
- Map it to a test.
- Define migration or compatibility behavior when needed.

Do not change a currently correct domain outcome silently.

### J. Plan completeness and executability

Verify the plan states:

- The problem and driver.
- Goals and non-goals.
- Scope and explicit exclusions.
- Acceptance criteria.
- Target files or components, when knowable.
- Existing mechanisms to reuse.
- Ordered implementation steps.
- Dependencies and sequencing.
- Data, API, workflow, and migration effects.
- Security and privacy effects.
- Specification and documentation updates.
- Validation commands and expected evidence.
- Rollout, rollback, and recovery.
- Ownership of follow-up work.
- Known assumptions and open questions.

A plan must be specific enough that another qualified agent or developer can
execute it without inventing missing architecture.

---

## Finding classification

### Severity

Severity is for reporting and ordering only.

- **BLOCKER:** likely data loss or corruption, security breach, normal-path
  failure, silent invariant violation, or core-principle violation.
- **HIGH:** material reliability, security, scalability, accessibility,
  maintainability, or required-coverage gap on an exercised path.
- **MEDIUM:** real gap or ambiguity on a non-critical path or under uncommon
  conditions.
- **LOW:** polish or small clarity improvement.

LOW and MEDIUM findings are fixed by default too.

### Scope

- **IN-SCOPE:** flaw in the proposed work.
- **OVER-SCOPE:** work not traceable to a stated driver or requirement.
  Default fix: remove or explicitly defer it.
- **UNDER-SCOPE:** required capability, guardrail, test, migration, or
  documentation is missing. Default fix: add it.

---

## Verdict and readiness

Verdict describes the result of the review.

Readiness is reported separately as `GO` or `NO-GO`.

Use exactly one verdict:

- **`APPROVE`**
  - No revisions were needed.
  - No open questions remain.
  - Every deferral meets the Fix Bar.
- **`APPROVE WITH REVISIONS APPLIED`**
  - Findings were fixed in place.
  - No open questions remain.
  - Every deferral meets the Fix Bar.
- **`REVIEWED - OPEN QUESTIONS`**
  - The review was completed, but one or more required human decisions remain.
  - Use only for a genuinely non-interactive run or an interrupted review.
- **`REJECT - NEEDS REPLAN`**
  - The fundamental approach is unsound and cannot be repaired safely with
    bounded edits.

Readiness:

- **GO**
  - Verdict is `APPROVE` or `APPROVE WITH REVISIONS APPLIED`.
  - All open questions are resolved.
  - No unfixed BLOCKER or HIGH finding remains.
  - The plan is recommended for human approval to execute.
- **NO-GO**
  - Any open question remains.
  - Any BLOCKER or HIGH finding remains unfixed.
  - Verdict is `REVIEWED - OPEN QUESTIONS`.
  - Verdict is `REJECT - NEEDS REPLAN`.

A plan may have `Status: reviewed` and still be `NO-GO`.

---

## Required final report

Do not issue the final report until the interactive question loop is complete,
unless the run is genuinely non-interactive.

Use this exact section order.

Cite evidence as `path:line`.

Use one row per distinct finding.

Allowed `Decision` values are:

- `FIXED`
- `DEFERRED`
- `OPEN`
- `REPLAN`

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
| PR-001 | <level> | <scope> | <rubric/project ref> | <path:line> | <finding> | C:<rating>; U:<rating>; S:<rating>; F:<rating>; Overall:<rating> | <decision> | <resolution or required next step> |

### Edits applied

- `<plan file>` - `<section or heading>`: <concise edit>
- `<plan file>` - `<section or heading>`: <concise edit>

### Deferred and open

- `<finding ID>` - `<DEFERRED | OPEN>`:
  - Reason: <reason>
  - Remediation Risk: <Medium-High | High>
  - Axis: <complexity | usability | security | functionality>
  - Required decision or evidence: <what is needed>
  - Consequence if unresolved: <impact>

### Commit result

- Pre-review snapshot: <commit hash | skipped because unchanged | not applicable | failed with reason>
- Hardened result: <commit hash | not applicable | failed with reason>
- Push: not performed

### Plans reviewed and not reviewed

REVIEWED:
- `<plan file>`: <GO | NO-GO> - <one-line reason>.
  Verdict: <verdict>.
  Open questions: all resolved interactively | <N open, blocks GO>.
  Required next step: <human approval | decision | replan | other concrete action>.

NOT REVIEWED:
- `<plan file>`: <exact reason>.
```

The `### Plans reviewed and not reviewed` section MUST be the final output.

Enumerate every file from the Step 0 review-scope ledger.

Do not print any text after it.
