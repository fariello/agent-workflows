# Changes to `plan-review.md`

## Summary

The revised runbook keeps the original purpose, Fix Bar, multi-perspective
review, interactive decision loop, two-commit provenance, and final
reviewed/not-reviewed enumeration.

The main changes make execution more deterministic for an LLM:

- Added a fixed context and scope assembly order.
- Defined Remediation Risk as an executable four-axis scale.
- Tightened the interactive open-question loop.
- Separated review verdict from GO/NO-GO readiness.
- Added a blocked verdict for non-interactive unresolved questions.
- Made plan eligibility and final enumeration use one shared scope ledger.
- Clarified Git safety and multi-plan commit behavior.
- Added missing plan-executability, privacy, rollout, and recovery checks.
- Removed ambiguity and over-prescriptive wording in several rubric items.

## Per-change details

### 1. Added a review-scope ledger

**Changed**

The agent must identify every candidate plan before review and classify it as
`ELIGIBLE` or `NOT REVIEWED`.

The final enumeration must use this same ledger.

**Why**

The original required enumeration of every plan considered, but did not define
when a plan became "considered." Agents could omit skipped plans or include
incidental references inconsistently.

**Targets**

Completeness, consistency, and report reliability.

**Risk or trade-off**

Adds a small setup step. The cost is low and prevents scope drift.

### 2. Added explicit instruction-discovery order

**Changed**

The agent now reads applicable agent instructions, principles, workflow rules,
plan contracts, specifications, and the target plan in a defined sequence.

**Why**

The original discovery step listed sources but did not define precedence or
what to do when instructions conflict.

**Targets**

Correctness and clarity.

**Risk or trade-off**

Repository-specific precedence may still vary. The revision requires the agent
to use the project's own precedence rule and ask when no rule resolves a
conflict.

### 3. Added an evidence-assembly step

**Changed**

The agent must list and reopen every material source the plan relies on before
judging it.

Missing or inaccessible evidence must be reported rather than inferred.

**Why**

The original required `file:line` verification but did not provide a forcing
sequence or handling for unavailable evidence.

**Targets**

Correctness and anti-hallucination.

**Risk or trade-off**

Can increase review time for plans with many references. That is intentional
when evidence is material.

### 4. Clarified the persona and security relationship

**Changed**

The eight existing personas remain unchanged.

Security is now a mandatory cross-cutting lens, not a ninth persona.

**Why**

The original said to use eight personas but also said the review was led by a
security view that was not one of those personas.

**Targets**

Internal consistency.

**Risk or trade-off**

None. Security review remains mandatory.

### 5. Defined Remediation Risk

**Changed**

Added Low, Medium, Medium-High, and High definitions.

Every finding is rated on complexity, usability, security, and functionality.
The overall rating is the highest applicable axis.

**Why**

The Fix Bar depended on Medium-High-or-higher Remediation Risk, but the file did
not define the scale or how to combine axes.

**Targets**

Correctness, repeatability, and Fix Bar enforcement.

**Risk or trade-off**

Adds classification work. It prevents severity from silently replacing the
Fix Bar.

### 6. Standardized finding decisions

**Changed**

Allowed decisions are now:

- `FIXED`
- `DEFERRED`
- `OPEN`
- `REPLAN`

Duplicate symptoms should be combined under one root-cause finding.

**Why**

The original table did not constrain decision values, which could produce
inconsistent reports and duplicate findings.

**Targets**

Clarity and report consistency.

**Risk or trade-off**

Some nuanced states must be explained in the Resolution column rather than
inventing new labels.

### 7. Tightened in-place revision rules

**Changed**

The agent must replace ambiguous text instead of appending duplicate prose,
preserve valid content, remove unsupported scope, and keep the plan executable
and concise.

**Why**

"Add missing sections and specificity" can cause agents to grow plans by
appending overlapping material.

**Targets**

Concision, maintainability, and fidelity.

**Risk or trade-off**

Requires more careful editing than simply appending a review section.

### 8. Made the open-question loop deterministic

**Changed**

The agent must:

1. Collect and deduplicate questions.
2. Resolve questions already answered by authoritative evidence.
3. Ask one to three related questions at a time.
4. Use a fixed question format.
5. Record each answer in the plan.
6. Re-run affected rubric sections.
7. Continue until no resolvable question remains.

**Why**

The original required interaction but left batching, ordering, evidence-based
resolution, and post-answer re-review underspecified.

**Targets**

Correctness, repeatability, and human usability.

**Risk or trade-off**

The loop may take more turns. It prevents silent assumptions and incomplete
plan updates.

### 9. Tightened the non-interactive exception

**Changed**

A run is non-interactive only when the environment explicitly lacks a human
interaction channel.

A delayed reply is not non-interactive.

**Why**

An agent could otherwise use the exception to avoid asking required questions.

**Targets**

Correctness and forcing-function strength.

**Risk or trade-off**

Interactive runs may pause until the human answers, as intended.

### 10. Added `REVIEWED - OPEN QUESTIONS`

**Changed**

Added a fourth verdict for a completed review that still requires human
decisions in a genuinely non-interactive or interrupted run.

**Why**

The original could produce an `APPROVE` verdict while the final enumeration
said `NO-GO` because questions remained open.

**Targets**

Internal consistency and clarity.

**Risk or trade-off**

Adds one verdict. It removes a more serious semantic contradiction.

### 11. Separated verdict from readiness

**Changed**

Verdict now describes review outcome.

`GO` or `NO-GO` describes readiness for human approval and execution.

**Why**

The original mixed plan quality, review completion, and execution readiness.

**Targets**

Precision and report usability.

**Risk or trade-off**

Reviewers must report both values. The distinction is operationally useful.

### 12. Clarified `Status: reviewed`

**Changed**

`reviewed` means the review occurred. It does not mean approved, GO, or
executed.

The agent follows the project's status contract when it differs.

**Why**

The original required `Status: reviewed` even for rejected or blocked plans
without explaining the meaning.

**Targets**

Lifecycle correctness.

**Risk or trade-off**

Projects with different status vocabulary require a small adaptation.

### 13. Hardened the commit contract

**Changed**

The agent must inspect Git status, commit only eligible target plans, avoid
unrelated files, never amend/reset/rebase, never bypass safety controls without
authorization, and report commit failures.

The two commits are per review run, including multi-plan runs.

**Why**

The original did not fully specify dirty-tree safety, untracked plans,
multi-plan scope, or commit failure behavior.

**Targets**

Repository safety and provenance.

**Risk or trade-off**

Commit creation can fail rather than bypassing hooks. The review still
continues when safe and reports the limitation.

### 14. Expanded data correctness checks

**Changed**

Added concurrency, uniqueness, lost-update, data-lifecycle, and recoverability
checks.

**Why**

Transactions alone do not cover common integrity failures.

**Targets**

Completeness and correctness.

**Risk or trade-off**

These checks are conditional on project relevance.

### 15. Expanded security into privacy and abuse resistance

**Changed**

Added privilege paths, unsafe outbound access, replay/abuse controls, privacy
minimization, and sensitive logging checks.

**Why**

The original security section was strong but missed several common plan-time
risks.

**Targets**

Security and completeness.

**Risk or trade-off**

Adds review surface. `Not applicable` remains allowed with a reason.

### 16. Reduced scalability over-specification

**Changed**

Kept scalable seams but made read/write split, caching, queues, and similar
patterns conditional on real requirements.

**Why**

The original could push infrastructure choices into plans where they were not
needed.

**Targets**

KISS, tool-agnosticism, and concision.

**Risk or trade-off**

The reviewer must judge relevance instead of applying a fixed architecture.

### 17. Reconciled anti-regression with pre-release correctness

**Changed**

Characterization tests pin intended correct behavior, not accidental behavior
that project policy says should be replaced.

**Why**

The original could conflict with projects that explicitly prefer pre-release
redesign over compatibility with defects.

**Targets**

Correctness and internal consistency.

**Risk or trade-off**

Requires identifying which behavior is authoritative rather than assuming all
current behavior must remain.

### 18. Added rollout, rollback, and recovery checks

**Changed**

Observability now includes dependency failure behavior, rollout, rollback,
reconciliation, and recovery.

**Why**

A plan can be technically correct but operationally unsafe to deploy.

**Targets**

Completeness and operability.

**Risk or trade-off**

Small projects may justify these items as not applicable.

### 19. Added plan completeness and executability rubric

**Changed**

Added a rubric section for goals, non-goals, acceptance criteria, sequencing,
dependencies, target components, assumptions, ownership, and validation
evidence.

**Why**

The prior rubric reviewed engineering quality but did not directly verify that
another developer could execute the plan without inventing missing decisions.

**Targets**

Deliverable quality and handoff reliability.

**Risk or trade-off**

Adds one rubric section. It prevents technically thoughtful but unusable plans.

### 20. Added evidence and commit fields to the report

**Changed**

The findings table now has an Evidence column and fixed Remediation Risk
format.

The report includes commit outcomes.

**Why**

The original demanded `file:line` evidence but had no dedicated place for it.
It also required commits without requiring the final report to state whether
they happened.

**Targets**

Precision, auditability, and report completeness.

**Risk or trade-off**

The findings table is wider. The added fields are directly actionable.

### 21. Made the final enumeration mechanically enforceable

**Changed**

The final section must use the Step 0 ledger and must be the last output.

The file ends with that instruction.

**Why**

The original stated the requirement, but earlier ambiguity about scope made it
hard to execute consistently.

**Targets**

Forcing-function strength and deterministic output.

**Risk or trade-off**

No post-report commentary is allowed. This is intentional.

## Deliberately left unchanged

### Fix Bar philosophy

Fix by default remains the governing rule.

Severity still never decides whether to fix.

Only Medium-High-or-higher risk from the fix itself can justify deferral.

Effort, time, cost, and tokens remain invalid deferral reasons.

### Relative sibling references and graceful degradation

The references to:

- `../release-review/fix-decision-policy.md`
- `../release-review/00-run-protocol.md`

remain relative and tool-agnostic.

The agent still applies the policies from memory when those files are absent.

### Planning-only boundary

The command still edits plans only.

It does not implement code, tests, runtime configuration, or infrastructure.

### Multi-perspective review

The existing eight personas remain intact.

The revision only clarifies security as a cross-cutting requirement.

### Interactive human decisions

Open questions still require human resolution whenever interaction is
available.

The agent may not guess.

### Two-commit, never-push provenance

The pre-review snapshot and hardened-result commits remain.

The revision adds safety details but does not weaken the contract.

### Final reviewed/not-reviewed enumeration

The enumeration remains mandatory and remains the final output.
