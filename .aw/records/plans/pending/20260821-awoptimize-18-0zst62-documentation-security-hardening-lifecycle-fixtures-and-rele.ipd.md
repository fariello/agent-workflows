# IPD: Documentation Security Hardening Lifecycle Fixtures and Release Readiness

- Date: 2026-08-21
- Kind: child
- Concern: Make the cutover truthful, safe, and reversible, and produce a GO/NO-GO without publishing.
- Scope: Operator/author/security docs (generated from evidence registries) + threat-model hardening + clean-install/update/rollback lifecycle fixtures + a final release-readiness review that never tags/publishes/pushes.
- Status: approved
- Approval: Gabriele Fariello (human), 2026-08-22
- Set: awoptimize
- Order: 18
- Highest E allocated: 05
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 0zst62

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-21 authored (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): body carved from superseded old-Order-08 E-05..E-09 into 5 right-sized E-items (docs rendered from registries, model-profile docs, security hardening, lifecycle matrix fixtures, GO/NO-GO release-readiness); the final Order.
- 2026-08-21 /plan-review (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): APPROVE WITH REVISIONS APPLIED; GO - PENDING HUMAN APPROVAL. Deps on 17 + all prior justified; the never-tag/publish/push + GO/NO-GO-only invariant is airtight (9 hits) and cites RELEASING.md / release-review Section 9; docs render from registries (no prose exceeding claims). PR-002 (MEDIUM, rubric C): E-03/E-05 said generic "leak scan" without naming the repo's canonical security tools - FIXED by naming `aw sanitize`/`check-local-leaks` (leak sanitizer) + `scan_secrets.py` (secret scanner) in E-03, and `aw sanitize --agent` + `aw ipd lint --all --agent` in E-05 and the required-tests, so the release gate reuses existing tooling not a fork. V-01..V-05 map 1:1 with falsifiable evidence. OQ-01 resolved.
- 2026-08-22 approved (Gabriele Fariello, human): explicit human approval of the awoptimize Set after /plan-review; reviewed -> approved.

## Goal

Make the cutover truthful, safe, and reversible, and produce a GO/NO-GO WITHOUT publishing. This
Order writes the operator/author/security documentation (generated from evidence registries so prose
can never exceed proven claims), hardens the new execution + host-integration attack surface,
executes the clean-install/update/rollback lifecycle fixtures from real legacy states, and performs a
final release-readiness review that tags/publishes/pushes NOTHING. It is the last Order in the Set
(Layer G); it consumes the Order-17 compatibility mechanics.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: documentation

- [ ] E-01 Write architecture, authoring, skill-selection, orchestration, evidence, verification, benchmark, host-adapter, troubleshooting, recovery, and security documentation with exact commands, outputs, limitations, and responsibility boundaries.
  - Depends on: none
  - Expected outcome: documentation link/command/option checks pass, and operator walkthroughs reproduce incomplete-run diagnosis, evidence inspection, a host probe, recovery, and rollback from a clean fixture without reading implementation internals.
  - Execution state: pending
- [ ] E-02 Document model profiles as EVIDENCE-BACKED defaults, not universal personality claims: distinguish model ID from reasoning configuration, and render tables FROM the benchmark/capability registries with benchmark date, task corpus, host, version, thresholds, uncertainty, and pending combinations.
  - Depends on: E-01
  - Expected outcome: model/support tables render exact IDs/configurations, corpus, host/version, dates, thresholds, uncertainty, and pending cells from the registries, with NO documentation turning vendor marketing or one observed rollout into a general quality guarantee.
  - Execution state: pending

### Task group 2: security hardening

- [ ] E-03 Harden the security boundaries of the new execution + host integration: local servers loopback/authenticated, external files consented + contained, skills least-privilege, evidence redacted, real HOME excluded from probes, untrusted repository text isolated as data, and destructive tools human-gated. REUSE the repo's existing security tooling rather than inventing new scanners: `aw sanitize` / `aw check-local-leaks` (the leak sanitizer) and `.aw/system/workflows/assess/tools/scan_secrets.py` (the secret scanner) for the leak/secret checks (rubric C, no duplicate path).
  - Depends on: E-02
  - Expected outcome: threat-model tests + runbooks prove loopback/auth, containment, consent, least privilege, redaction, real-HOME refusal, untrusted-text isolation, and human destructive gates across the new attack surface, invoking the existing `aw sanitize`/`scan_secrets.py` tools (not new ones).
  - Execution state: pending

### Task group 3: lifecycle fixtures and release gate

- [ ] E-04 Execute clean-install, legacy-update, partial-state, customized-file, interrupted-update, rollback, downgrade-warning, no-network, no-credential, multi-host-discovery, and unsupported-host lifecycle fixtures from real legacy starting states.
  - Depends on: E-03
  - Expected outcome: every named lifecycle fixture passes from a clean isolated environment; unsupported/no-credential cases fail BEFORE mutation; reruns show no unmanaged drift.
  - Execution state: pending
- [ ] E-05 Perform the final release-readiness review and add `tests/test_release_readiness.py` (stdlib unittest for the checkable parts): full suite (`make test`), the canonical leak scan `aw sanitize --agent` (exit 0), all IPD lint phases (`aw ipd lint --all --agent`), generated/compiler drift, docs checks, complete workflow disposition, capability-evidence freshness, benchmark thresholds, changelog + versioning, artifact manifest, and residual-risk sign-off - producing a GO/NO-GO report that does NOT tag, publish, deploy, or push. Then run the full serial suite and paste the tail.
  - Depends on: E-04
  - Expected outcome: retained outputs show the full suite, leak scan, IPD lint phases, drift, docs, disposition, claim freshness, benchmark, and residual-risk gates pass; a GO/NO-GO report is produced; git evidence shows NO tag/release/deploy/push; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Release actions are distinct from release-note preparation and require SEPARATE authority (RELEASING.md / release-review Section 9); no ad-hoc tag/push/publish. This Order stops at a GO/NO-GO decision.
- Support + performance tables must be GENERATED from their evidence registries (Order 10 capability, Orders 12/13 benchmark) so documented prose cannot exceed a recorded claim.
- Local headless servers may be unauthenticated by default (D86/D87); the new host integration must bind loopback + require auth. Untrusted repository/tool/inter-agent text is data, not instructions.
- A green implementation suite does NOT prove clean update/rollback; lifecycle fixtures must exercise real legacy starting states (reuse the installer's isolated-repo test harness).

## Findings

| Finding | Consequence |
|---|---|
| Host/model support becomes stale quickly. | Documentation renders from the capability + benchmark registries with dates; no static support claim. |
| A green implementation suite does not prove clean update or rollback. | Lifecycle matrix fixtures run from real legacy states, not just from a fresh install. |
| The new execution + host surface adds attack surface. | Explicit threat-model tests: loopback/auth, containment, consent, least privilege, redaction, real-HOME refusal, untrusted-text isolation, human destructive gates. |
| Release actions are irreversible + externally consequential. | The release-readiness review produces GO/NO-GO only; it never tags/publishes/pushes (that is a separately authorized action). |

## Proposed changes (ordered, validatable)

1. Write complete operator/author/security documentation with exact commands + limits (E-01).
2. Document model profiles as evidence-backed defaults rendered from registries (E-02).
3. Harden the new execution + host-integration security boundaries (E-03).
4. Execute the clean/legacy lifecycle matrix fixtures (E-04).
5. Produce a GO/NO-GO release-readiness review without releasing (E-05).

## Deferred / out of scope (with reason)

- The compatibility contract + migration/rollback/deprecation MECHANICS: Order 17 (this Order documents + validates + gates them).
- Actual tag/release/publish/deploy/push: a SEPARATELY authorized release action (RELEASING.md / release-review Section 9), never here.
- REMOVING compatibility surfaces: their documented removal authority, after the adoption window.
- Central telemetry collection: out unless separately specified + privacy-reviewed.

## Scope check

- Over-scope: no release mutation, external publishing, forced deletion, or compatibility-contract/migration mechanics (Order 17).
- Under-scope: none - documentation, security hardening, the lifecycle matrix, and the release-readiness gate are covered; this is the final Order.

## Required tests / validation

- Documentation command/option/link validation + generated-table drift (tables render from registries).
- Security threat-model tests: containment, symlink escape, untrusted-instruction isolation, permissions, authentication, redaction, real-HOME refusal, human destructive gates.
- Lifecycle fixtures: fresh, update, partial, customized, interrupt, rollback, downgrade-warning, no-network, no-credential, multi-host-discovery, unsupported-host - each from a clean isolated environment, failing before mutation where required, no unmanaged drift on rerun.
- `tests/test_release_readiness.py` for the checkable gates; full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; `aw sanitize --agent` (leak scan) exit 0 + `aw ipd lint --all --agent` + compiler/generated drift + benchmark gates clean; git evidence shows no tag/release/deploy/push.

## Spec / documentation sync

- This Order OWNS the current-state architecture, migration, rollback, troubleshooting, security, support matrix, benchmark summary, changelog, and release-note CONSISTENCY docs. All support + performance tables are generated from their evidence registries.

## Open questions

### OQ-01: none

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The docs/security/lifecycle/release-readiness scope is enumerated from old Order 08's E-05..E-09; no open decision. The deprecation-window question is Order 17's OQ-01. The actual release is out of scope (a separate authorized action).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted documentation link/command/option check output, and operator-walkthrough fixtures reproducing incomplete-run diagnosis, evidence inspection, a host probe, recovery, and rollback from a clean fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted output showing model/support tables render exact IDs/configurations, corpus, host/version, dates, thresholds, uncertainty, and pending cells FROM the registries, with no unsupported generalization.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted threat-model test output proving loopback/auth, containment, consent, least privilege, redaction, real-HOME refusal, untrusted-text isolation, and human destructive gates.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted output showing every named lifecycle fixture passes from a clean isolated environment, unsupported/no-credential cases fail before mutation, and reruns show no unmanaged drift.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: retained outputs showing full suite, leak scan, all IPD lint phases, compiler/generated drift, docs, disposition, claim freshness, benchmark, and residual-risk gates pass; a GO/NO-GO report; git evidence showing NO tag/release/deploy/push; `tests/test_release_readiness.py` exists and passes; pasted full serial-suite tail.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 17 (compatibility mechanics) and ALL prior Orders (01-16); this is the final Order in the Set. Scope fence: touch only the documentation set, the security-hardening + threat-model test modules, the lifecycle-matrix fixtures, and `tests/test_release_readiness.py` (plus generated support/benchmark tables rendered from registries); do NOT alter the compatibility mechanics (Order 17), and NEVER tag, publish, deploy, or push - if it seems to need more, STOP and report. The release-readiness review produces a GO/NO-GO decision ONLY; the actual release is a separately authorized action (RELEASING.md / release-review Section 9) outside this Set. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
