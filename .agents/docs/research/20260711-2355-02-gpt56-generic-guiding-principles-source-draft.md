<!--
PROVENANCE (archived 2026-07-12): external source draft, generated with GPT-5.6, 2026-07-11.
This is the ORIGIN material for IPD 20260712-0020-01 (D67), which filtered a subset of these
generic principles into the assess lenses + GUIDING_PRINCIPLES. This full generic doc was
deliberately NOT imported wholesale. Kept verbatim for provenance; the "Authoritative baseline"
wording below is the external draft's own claim, NOT this repo's status. This repo's authoritative
principles live in GUIDING_PRINCIPLES.md.
-->

# Project Development Guiding Principles

**Status:** Authoritative baseline
**Version:** 1.0
**Audience:** Human developers and AI coding agents

This document defines the default product, architecture, quality, security, and delivery rules for this project.

Project-specific rules may add constraints. They may not silently weaken this baseline.

---

## 1. Core Rules

1. **Prefer one coherent design over many parallel designs.**
2. **A new noun does not automatically require a new model, table, service, workflow, or API.**
3. **Express normal variation as data or configuration before adding code.**
4. **Use one canonical implementation for each business action.**
5. **Do not duplicate logic across labels, clients, endpoints, jobs, or integrations.**
6. **Choose the simplest design that fully meets the real requirement.**
7. **Generalize only for current or clearly expected needs.**
8. **Preserve correctness, security, accessibility, auditability, and data integrity.**
9. **Minimize user effort. Every unnecessary action is a defect.**
10. **Do not declare work complete without tests, evidence, documentation, and operational readiness.**

---

## 2. Design and Architecture

### 2.1 Canonical models

Before creating a new technical concept, ask:

- Is this only a different label, presentation, state, role, or configured use of an existing concept?
- Can the existing model support it through data or configuration?
- If not, can a shared core support it with a small specialization?
- What real invariant, identity, lifecycle, or behavior requires separation?

Create a separate model only when the difference is material and cannot be represented clearly and safely in the existing design.

Do not create parallel schemas or services for concepts that behave the same.

### 2.2 Generality and simplicity

Use this order:

1. One model with variation as data or configuration;
2. One shared core with a thin specialization;
3. A bounded special case with written justification.

Do not build abstractions for hypothetical needs.

Do not replace clear domain models with an unbounded metadata system merely because it can represent anything.

Measure total complexity, including:

- Code;
- Configuration;
- Indirection;
- Validation;
- Testing;
- Migrations;
- Operations;
- Debugging; and
- Maintainer cognitive load.

### 2.3 Configuration

Use configuration for expected variation such as:

- Labels;
- Roles;
- Thresholds;
- Routing;
- Rules;
- Templates;
- Notifications; and
- Effective dates.

Configuration must be:

- Typed;
- Validated;
- Versioned;
- Auditable;
- Testable; and
- Permission-controlled where editable at runtime.

Do not turn configuration into a hidden programming language.

### 2.4 API and execution paths

When the project has an application or service boundary:

- Every client must use the canonical API or application interface.
- Each business action must have one canonical implementation.
- UI, jobs, tools, workers, imports, exports, and integrations must not bypass validation, authorization, workflow, audit, or state rules.
- Compatibility endpoints may delegate to the canonical implementation but must not contain separate business logic.
- Direct persistence access must not become an alternate business interface.

Controlled migrations, backup, restore, and recovery tooling may use direct persistence access under change control.

---

## 3. User Experience

For user-facing work:

- Make common tasks obvious to a first-time user.
- Minimize clicks, taps, typing, scrolling, page changes, confirmations, and repeated entry.
- Prefill known or highly likely values when safe.
- Show questions only when relevant.
- Validate early and preserve entered data after errors.
- Do not require a user to select the only available option.
- Do not add review or confirmation steps unless they reduce a real risk.
- Use searchable, case-insensitive partial matching for medium and long lists.
- Use large, forgiving interaction targets.
- Keep help available at the point of need.
- Do not use separate forms for differently branded versions of the same action.

Automatic progression is encouraged for safe intermediate steps. Never automatically commit a consequential final action.

---

## 4. Accessibility

User-facing work must meet the project's stated accessibility target. Unless a stricter rule applies, use **WCAG 2.2 AA**.

At minimum:

- Use native semantic elements where available.
- Support full keyboard operation.
- Keep focus visible and logical.
- Provide accessible names, labels, states, errors, and dynamic updates.
- Do not rely on color alone.
- Avoid tiny controls and precision clicking.
- Test with automated tools and manual keyboard or assistive-technology checks.

Accessibility defects are functional defects.

---

## 5. Security, Privacy, and Audit

Apply controls in proportion to risk.

For sensitive, regulated, privileged, or externally connected systems:

- Use least privilege, defense in depth, secure defaults, and fail-closed behavior.
- Authenticate every human and workload.
- Authorize every protected action and resource.
- Use narrowly scoped, revocable, monitored credentials.
- Protect secrets using approved secret-management systems.
- Record consequential reads and writes.
- Preserve who acted, what they accessed or changed, when, through which channel, under whose authority, and with what result.
- Protect audit records from ordinary alteration or deletion.
- Detect suspicious access, privilege misuse, bulk retrieval, exfiltration, and control failure.
- Treat uploads and external content as untrusted.
- Maintain tested backup, restore, and recovery procedures.
- Minimize collection, exposure, retention, and logging of sensitive data.

Security and compliance controls are part of the feature, not later hardening work.

---

## 6. Data Integrity and Historical Truth

- Preserve what was submitted, approved, viewed, configured, and effective at each point in time.
- Do not silently rewrite history.
- Preserve provenance for imported, synchronized, calculated, and user-entered data.
- Version or effective-date rules and configuration when historical reconstruction matters.
- Use explicit state transitions, constraints, and transactions.
- Make migrations reviewable, tested, and recoverable where practical.
- Do not duplicate authoritative data without defined ownership, synchronization, and conflict handling.
- Use canonical definitions in reports and integrations.

---

## 7. Pre-Release and Compatibility

Before the first real release or external dependency:

- Prefer the correct design over preserving provisional or half-working code.
- Remove, replace, migrate, or refactor flawed structures.
- Do not add compatibility layers for hypothetical consumers.
- Tests should preserve intended behavior, not accidental defects.

After real users, integrations, contracts, or public APIs depend on the system:

- Preserve documented behavior unless a deliberate migration or breaking-change process is approved.
- Reassess compatibility obligations explicitly.

---

## 8. Target State and Existing Gaps

This document defines the required target state. It does not certify that the current codebase already meets every rule.

- New work must not add new violations.
- Work must not worsen existing violations.
- Touched gaps should be fixed when reasonably in scope.
- Deferred gaps must be tracked with risk, owner, priority, and remediation plan.
- An unrelated existing gap does not fail an otherwise compliant task.
- Critical unsafe gaps may block release or require explicit risk acceptance.

Do not confuse **existing gap** with **not applicable**.

---

## 9. Verification and Completion

Work is complete only when applicable requirements are verified.

Check:

- Correctness;
- Canonical model and implementation reuse;
- API and execution-path consistency;
- Security and authorization;
- Audit behavior;
- Accessibility;
- Data integrity;
- Negative and abuse cases;
- Migrations;
- Monitoring and diagnostics;
- Documentation; and
- Handoff readiness.

Every completion claim must be supported by evidence.

---

## 10. Final Review Questions

Before completion, answer:

- Is this the simplest design that meets the real requirement?
- Did I reuse the canonical model and implementation?
- Did I avoid duplicate APIs, workflows, services, and rules?
- Is normal variation data or configuration?
- Did I minimize user effort?
- Is the result accessible?
- Are security, privacy, and audit controls sufficient for the risk?
- Is historical truth preserved?
- Are tests and operational evidence complete?
- Can another developer or agent safely continue the work?

If an applicable answer is no, the work is not complete.
