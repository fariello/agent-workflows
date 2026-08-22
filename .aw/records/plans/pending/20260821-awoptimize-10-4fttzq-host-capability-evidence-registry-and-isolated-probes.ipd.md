# IPD: Host Capability Evidence Registry and Isolated Probes

- Date: 2026-08-21
- Kind: child
- Concern: Replace boolean host support claims with versioned evidence that defaults to unverified.
- Scope: The capability-evidence registry (keyed by host/version/mode/feature; unverified default) + isolated positive/negative host probes. Scoped OpenCode + Codex first; agy 1.1.17 tentative. Nothing marked supported without an operator-run live probe. No skills/adapters (Order 11).
- Status: draft
- Set: awoptimize
- Order: 10
- Highest E allocated: 04
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 4fttzq

## Workflow history

- 2026-08-21 draft (opencode (its_direct/pt3-claude-opus-4.8-1m-us)): created.

## Goal

Replace boolean host-support claims with a versioned capability-EVIDENCE registry that defaults every
unproven or expired claim to `unverified`, and provide the isolated probe harness (positive AND
negative) that is the ONLY thing allowed to promote a capability to supported. This Order owns the
registry + probes; it does not generate the skills/adapters that consume the registry (Order 11).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: evidence registry

- [ ] E-01 Implement the capability-evidence registry `agent_workflows/host_capability_registry.py`: records keyed by host, distribution, exact version, OS, mode, feature, configuration, probe variant, result, evidence artifact, observed date, expiry, and source type; any missing or expired entry defaults to `unverified`, and a generator asking about an unproven capability gets `unverified`, never `supported`.
  - Depends on: none
  - Expected outcome: a migration fixture proves every old static-matrix boolean becomes a versioned claim; missing evidence yields `unverified`; stale (past-expiry) evidence yields `unverified`; a query for an unproven capability cannot return `supported`.
  - Execution state: pending

### Task group 2: probe harness

- [ ] E-02 Upgrade the conformance probe harness: source command templates from validated adapters, detect the installed host version, scaffold isolated HOME/XDG fixtures, capture stdout/stderr/exit + a nonce side effect, redact the captured evidence, and REFUSE a real-HOME target. Probes test capability RESOLUTION and FOLLOWING separately and emit a machine-validated durable report.
  - Depends on: E-01
  - Expected outcome: isolated-fixture tests prove version detection, real-HOME refusal, adapter-derived commands, complete capture + redaction, nonce verification, and a valid durable report; no probe touches the real user HOME or credentials.
  - Execution state: pending
- [ ] E-03 Add NEGATIVE probes for missing skill, denied permission, no user input, path precedence, stale adapter, malformed frontmatter, external-path refusal, server authentication, and background result loss - so "supported" requires reproducing BOTH the positive contract and the expected fail-closed behavior.
  - Depends on: E-02
  - Expected outcome: every negative variant yields its declared fail-closed result and cannot promote a capability claim; positive and negative outcomes are recorded as separate evidence.
  - Execution state: pending

### Task group 3: tests

- [ ] E-04 Add `tests/test_host_capability_registry.py` (stdlib unittest): the migration + unverified-default + expiry fixtures (E-01); the isolated-fixture probe tests incl. real-HOME refusal + redaction + nonce (E-02); one negative-probe fixture per class (E-03). Then run the full serial suite and paste the tail.
  - Depends on: E-03
  - Expected outcome: registry + probe + negative-probe tests pass; the full serial suite is green (pasted).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The current conformance files call themselves Phase 0 and require live per-host/version proof before shipping a tier; the static host matrix currently includes commands not established by repository evidence.
- Local headless servers may be unauthenticated by default (repo DECISIONS D86/D87); probes must bind loopback + require auth before shared-network use.
- `agy` is a repository-local integration with no executable in the audit environment (installed `agy --version` = 1.1.17 per OQ-02); exact behavior is `unverified` until an operator-run probe.
- Pure/near-pure module shape (stdlib-only, D138); probe evidence is redacted (reuse the Order-03 redaction hook).

## Findings

| Finding | Consequence |
|---|---|
| The static host matrix contains unproven support booleans + command templates. | Treat it as seed data, not evidence; migrate to versioned claims that default to `unverified`. |
| A capability could be "supported" on documentation alone. | Only a positive-AND-negative isolated live probe on the exact host/version promotes a claim. |
| Probes could clobber the operator's real environment or leak secrets. | Isolated HOME/XDG fixtures, real-HOME refusal, and redacted evidence are mandatory. |

## Proposed changes (ordered, validatable)

1. Versioned capability-evidence registry with `unverified` default + expiry (E-01).
2. Isolated positive probe harness (version detect, real-HOME refusal, capture/redact/nonce) (E-02).
3. Negative probes so support = positive + fail-closed behavior (E-03).
4. Registry + probe + negative-probe tests + full suite (E-04).

## Deferred / out of scope (with reason)

- Generating the skills/adapters that CONSUME the registry, and the agy fresh-verifier: Order 11.
- Behavioral quality/cost comparison across hosts: Orders 12/13.
- Workflow-content migration: Orders 14-16. Removing legacy shims: Order 17.
- Actually RUNNING the live probes: operator-run (this Order builds the harness + registry; the maintainer runs the exact-version probes and pastes evidence).

## Scope check

- Over-scope: no skill/adapter generation, no provider credential setup, no live paid model calls, no shim deletion.
- Under-scope: none - the evidence registry and the positive+negative isolated probe harness are covered; Order 11 consumes them.

## Required tests / validation

- `tests/test_host_capability_registry.py`: migration fixture (matrix boolean -> versioned claim); `unverified` default + expiry; version detection; real-HOME refusal; adapter-derived commands; capture + redaction + nonce; a valid durable report; one negative-probe fixture per class (each fail-closed, none promoting a claim).
- At least one operator-run live probe per advertised host/version/mode is REQUIRED before any status becomes `supported` (operator-run, evidence pasted).
- Full serial suite green (canonical `make test` / `python3 -m unittest discover -s tests -t .`) with pasted tail; leak scan clean.

## Spec / documentation sync

- Publish the capability-claim schema, the evidence-expiry rules, and the exact probe runbook. Generate any support tables FROM the evidence records so documented prose can never exceed a recorded claim.

## Open questions

### OQ-01: Which cross-host skill directory is the primary generated target?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED (2026-08-21, /plan-review with the maintainer): scope v1 to OpenCode + Codex FIRST, generating to the shared `.agents/skills/` convention as the primary target where each host discovers it, with per-host directories only where a host requires its own; Gemini CLI, Claude Code, and Kiro CLI are secondary, deferred until probed. This is a SCOPING decision that does NOT mark any capability `supported`: every claim stays `unverified` in this registry until an operator-run isolated live probe (E-02/E-03) on the exact version. Consumed by Order 11 (skill/adapter generation); recorded here because the registry is the gate.

### OQ-02: What is the exact supported `agy` version and vendor documentation?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: RESOLVED (2026-08-21): the maintainer's installed `agy --version` is `1.1.17`, recorded as the TENTATIVE target. Per the fail-closed discipline (E-01) it stays `unverified` until an isolated live probe (E-02/E-03) reproduces both the positive contract and the expected fail-closed behavior on that exact version and the maintainer pastes the evidence; the existing agy runner remains an unverified compatibility integration until then. Vendor documentation for 1.1.17 is cited by the operator with the probe.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: pasted migration-fixture output proving every old matrix boolean becomes a versioned claim, missing evidence -> `unverified`, stale evidence -> `unverified`, and an unproven-capability query cannot return `supported`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted isolated-fixture test output proving version detection, real-HOME refusal, adapter-derived commands, complete capture + redaction, nonce verification, and a valid durable report; no real HOME/credentials touched.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted test output showing every negative variant yields its declared fail-closed result and cannot promote a claim; positive and negative outcomes recorded separately.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_host_capability_registry.py` exists and passes; pasted full serial-suite tail (`make test` / `python3 -m unittest discover -s tests -t .`) showing green counts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires executed Order 05 (engine) and Order 08 (roles/verifier), plus Orders 01-04 upstream. Scope fence: touch only `agent_workflows/host_capability_registry.py`, the probe-harness module it defines/upgrades, and `tests/test_host_capability_registry.py`; do NOT generate skills/adapters (Order 11), migrate workflows (Orders 14-16), or set up provider credentials - if it seems to need more, STOP and report. No host status may be promoted from documentation alone; a positive isolated live probe is required; never access the real user HOME or credentials in tests. Execution contract: path-scoped commits only, never `git add -A`/`-a`, never push; paste the ACTUAL runner output; the executor may not certify its own V-items or perform a terminal transition. After every V-item is verified with concrete evidence and `aw ipd lint --phase pre-transition` conforms, perform the post-gate lifecycle transaction (workflow-history line, terminal Status, git mv to executed/, post-transition lint), dropping the `Approval:` field on the executed status. This plan requires explicit human approval before execution.
