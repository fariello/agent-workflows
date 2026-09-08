# IPD: Sanitized export, explicit submission, and setup wizard controls

- Date: 2026-09-08
- Kind: child
- Concern: Allow useful voluntary data sharing without accidental disclosure, automatic network activity, or ambiguous consent.
- Scope: Implement sensitivity-tiered export bundles, explicit submission to configured endpoints, manifests and previews, local telemetry/report setup choices, retention/deletion controls, and hostile privacy tests.
- Scope-Paths: agent_workflows/run_analytics_export.py, agent_workflows/run_analytics_submit.py, agent_workflows/run_analytics_wizard.py, agent_workflows/cli.py, tests/test_run_analytics_export.py, tests/test_run_analytics_submit.py, tests/test_run_analytics_wizard.py
- Item-Dependencies: executed:mm5p3v
- Status: to-review
- Set: runanalytics
- Order: 9
- Highest E allocated: 03
- Author: Codex
- Id: ixis0c

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): defined three export tiers, explicit per-submission consent, transport boundaries, and optional wizard integration.

## Goal

Let users create inspectable bundles and, only by an explicit separate command, submit a chosen bundle to an approved endpoint. Installation must not enable sharing or periodic sampling by default, and unattended setup must never infer consent.

## Detailed Implementation Checklist (TODO)

### Task group 1: Export, submit, and consent

- [ ] E-01 Implement \`aw runs export\` with \`metrics\`, \`events-redacted\`, and \`raw\` sensitivity tiers, deterministic manifests, preview, and destination safeguards.
  - Depends on: none
  - Expected outcome: metrics exports contain only safe normalized facts; redacted-event exports pass the shared sanitizer and declare residual risk; raw exports copy selected original records only after an every-time interactive confirmation or explicit noninteractive acknowledgement naming the risk and destination.
  - Execution state: pending
- [ ] E-02 Implement \`aw runs submit <bundle>\` as a separate, auditable, opt-in transport with endpoint policy and no automatic retry/upload.
  - Depends on: E-01
  - Expected outcome: submission validates manifest/schema/checksums/tier/size, displays endpoint and sensitivity, requires explicit confirmation unless an exact-purpose noninteractive flag is supplied, uses configured authentication without storing secrets in bundles/logs, records a local receipt, and documents retention/deletion/contact terms.
  - Execution state: pending
- [ ] E-03 Add optional setup/wizard choices for analytics, basic telemetry, periodic sampling, retention, and default export behavior without granting submission consent.
  - Depends on: E-02
  - Expected outcome: analytics tooling is installed only when selected if packaging supports optional feature installation; basic local telemetry choice is clear, periodic sampling has a separate question, defaults are conservative, unattended mode stays local/no-submit, and users can inspect/change/disable/delete settings and generated analytics.
  - Execution state: pending

## Project conventions discovered (Step 0)

- User-local profile/config helpers already exist; use them for preferences and endpoint configuration rather than putting secrets or user choices in repository files.
- Host-level setup interviews are optional and tolerate unavailable components. Analytics prompts must follow that resilience while never swallowing a requested configuration error silently.
- The local cache and report are minimized but not anonymous. Export UI must not overstate privacy.
- The entire runs tree is disposable, but deletion commands must target exact tool-owned analytics children and preserve source runs unless the user explicitly selects raw run deletion through an existing supported lifecycle.
- CLI registration shares Order 08’s routing-sensitive \`aw runs\` surface, so this IPD executes afterward and adds fixed leaves only.

## Findings

Sensitivity contract:

| Tier | Contents | Consent |
|---|---|---|
| \`metrics\` | privacy-projected normalized facts, aggregate metadata, quality, taxonomy/pricing versions, system resource categories/pseudonyms | explicit export command; safe default tier |
| \`events-redacted\` | bounded structured event facts with content/commands/paths/identity removed plus sanitizer report | explicit tier selection and warning |
| \`raw\` | selected original run artifacts, potentially including prompts/conversations/code/commands/paths/secrets | every-time confirmation or explicit exact-purpose noninteractive acknowledgement; never default |

Submission is never part of analyze, open, export, install, periodic telemetry, or cleanup. No background uploader, queued retry daemon, tracking pixel, analytics beacon, or implicit “improve product” consent is permitted.

The endpoint contract must specify operator, URL allowlist/configuration, TLS, authentication source, maximum size, accepted schema/tier, server retention, access, aggregation, deletion request method, contact, response/receipt, and behavior on partial/duplicate submission. If those details are not approved, implement local export only and make submit return an actionable unavailable status.

## Proposed changes (ordered, validatable)

1. Produce tiered local bundles with manifest, checksums, preview, and sanitizer evidence.
2. Gate a separate transport behind explicit bundle, endpoint, and consent validation.
3. Add conservative wizard/configuration and precise deletion/disable controls.

## Deferred / out of scope (with reason)

- Operating a collection server, choosing an organization endpoint, legal/privacy policy approval, or defining server-side research governance is outside repository implementation.
- Automatic telemetry submission and automatic price/system data upload are prohibited.
- Claiming anonymization is prohibited unless independently demonstrated.
- Installing the analyzer by default is prohibited by the user decision; the wizard may offer it clearly.

## Scope check

- Over-scope: no source parsing, analysis/statistics, SPA internals, runner lifecycle mechanics, or server implementation.
- Under-scope: includes export tiers, sanitizer, manifests, preview, submission boundary, receipts, auth handling, wizard defaults, periodic-sampling consent, retention, deletion, and absent-endpoint behavior.

## Required tests / validation

- Metrics and redacted bundles contain all required numeric facts but no seeded prompt/response, command, path, hostname, username, remote, branch, commit message, environment secret, high-entropy token, spreadsheet formula, or archive traversal canaries.
- Raw export refuses without every-time confirmation/acknowledgement and precisely lists selected files; metrics remains the default.
- Analyze, report open, wizard, install, and periodic sampling make zero network calls.
- Submit rejects unapproved schemes/hosts, redirects outside policy, invalid TLS, oversized/tampered/unknown-schema bundles, missing auth, and unsupported tier; secrets never appear in argv guidance, output, logs, receipts, or bundle.
- Cancellation, timeout, server rejection, duplicate receipt, and interrupted upload do not silently retry.
- Wizard interactive/unattended/default/reconfigure/disable/delete paths and no-consent assertions.
- Archive extraction/creation path traversal and symlink defenses.
- Bare \`python3 -m pytest\` and \`git diff --check\`.

## Spec / documentation sync

Order 10 documents local-only defaults, every privacy tier, residual risks, endpoint governance, consent, retention, deletion, and absence of automatic submission. If no endpoint policy is approved, docs must say submission is unavailable rather than imply a future server.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: deterministic bundle/sanitizer tests and manual manifest inspection prove tier contents and confirmation behavior.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: a mocked transport matrix proves endpoint/auth/consent/receipt behavior and zero network calls outside explicit submit.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: wizard and configuration tests prove conservative defaults, separate periodic opt-in, no submission consent, disable/delete precision, full suite, and clean diff.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: export sensitivity, network consent, and wizard defaults are one privacy boundary and must not be implemented independently.

Execute only after explicit plan approval. If endpoint governance remains unspecified, complete export and wizard work but implement submit as a tested unavailable capability, not an arbitrary generic uploader.
