# IPD: OpenCode and Agy runner telemetry lifecycle integration

- Date: 2026-09-08
- Kind: child
- Concern: Make both driver implementations emit equivalent per-invocation telemetry on every lifecycle path.
- Scope: Integrate the shared collector into OpenCode and Agy runner attempts, verifiers, recovery/resume paths, and shutdown handling; amend the runner contract accordingly.
- Scope-Paths: agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/runner_shutdown.py, tests/test_oc_runipd.py, tests/test_oc_runipd_cli.py, tests/test_agy_runipd_cli.py, .aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md
- Item-Dependencies: executed:lhccjf
- Status: to-review
- Set: runanalytics
- Order: 4
- Highest E allocated: 03
- Author: Codex
- Id: 5f2h8i

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): mapped the collector to both runner lifecycles, resume identity, verifier phases, and shutdown failure modes.

## Goal

Write \`<run>/telemetry/<execution-id>.jsonl\` for each OpenCode and Agy execution or verification invocation. Preserve distinct attempts and nodes across resume, keep the two runners semantically aligned, and never let telemetry failure alter the work result.

## Detailed Implementation Checklist (TODO)

### Task group 1: Driver lifecycle integration

- [ ] E-01 Integrate telemetry with every OpenCode executor and verifier invocation.
  - Depends on: none
  - Expected outcome: collection begins immediately before child launch, records resolved run/set/IPD/attempt/phase/model/provider/variant metadata, ends with normalized outcome and exit information, and closes on success, failure, timeout, signal, cancellation, and launcher exception.
  - Execution state: pending
- [ ] E-02 Integrate the identical lifecycle contract with Agy and the shared shutdown paths, including resume and recovery.
  - Depends on: E-01
  - Expected outcome: Agy emits the same schema and phase semantics; each resumed or retried invocation gets a new execution ID and contemporaneous node pseudonym; shared shutdown cannot double-close or orphan the sampler.
  - Execution state: pending
- [ ] E-03 Amend the deterministic runner specification and add parity, degradation, and lifecycle regression tests.
  - Depends on: E-02
  - Expected outcome: the approved contract names telemetry as a best-effort derived run artifact, states privacy/default/disable semantics, and tests prove instrumentation cannot change runner exit status, merge decision, state transitions, or cleanup.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Both runners own \`state.json\`, driver \`events.jsonl\`, \`sessions/\`, \`outcomes/\`, prompts, and execution reports; telemetry is a separate derived subtree and must not be confused with the hash-chained run ledger.
- Existing attempts already record cost and token summaries after log extraction. Telemetry adds resource context and invocation identity without becoming the authority for those totals.
- Runner shutdown and stop modules centralize signal behavior; cleanup must be registered there when necessary rather than relying only on happy-path \`finally\` blocks.
- Prompts, child stdout, and session JSONL are sensitive source artifacts and must never be copied into telemetry.
- Driver behavior and output are heavily tested. Test instrumentation through injected collectors to avoid timing flakes.

## Findings

There can be multiple executor attempts and an independent verifier invocation per IPD, plus later resume in the same run directory. Therefore the execution ID, attempt, phase, start/end times, model identity, and node pseudonym must be recorded per file and must not be inferred later from a single run-level snapshot.

“Telemetry disabled” means no telemetry directory or event file is created. “Periodic sampling disabled” still permits the default start/end basic events unless all telemetry is disabled.

## Proposed changes (ordered, validatable)

1. Wrap all OpenCode subprocess invocation boundaries with the shared collector.
2. Apply the same boundary and shutdown semantics to Agy and resume/retry paths.
3. Amend the spec and pin parity/non-interference with fault-injected tests.

## Deferred / out of scope (with reason)

- Resource probe implementation is Order 03.
- Parsing and statistical use of telemetry are Orders 05 and 06.
- Changes to agent prompts or model selection are not needed to collect driver-owned telemetry.
- Historical runs without telemetry remain supported and receive explicit missing-coverage flags.

## Scope check

- Over-scope: no analyzer, pricing, SPA, export, network, or setup wizard.
- Under-scope: covers executor, verifier, retries, resume, cancellation, signals, exceptions, both hosts, and controlling spec sync.

## Required tests / validation

- OpenCode and Agy parity for start/end metadata and phase/attempt identity.
- Resume on a different pseudonymous node; retry in the same run; verifier with a different model.
- Disabled telemetry creates nothing; basic default produces two lifecycle events; periodic mode samples.
- Probe timeout/exception/disk-write failure leaves original runner status and exit behavior unchanged and produces the documented warning path where writable.
- Signal, cancellation, launch failure, merge failure, verifier failure, and normal completion close samplers.
- Existing runner CLI/shim/shutdown tests, bare \`python3 -m pytest\`, and \`git diff --check\`.

## Spec / documentation sync

Amend \`.aw/records/specs/20260826-0718-01-aw-run-deterministic-run-and-verify.spec.md\` in the same execution before implementation depends on the new artifact contract. Preserve its deterministic validation and merge requirements; telemetry is observational and best effort, never a gate.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: OpenCode lifecycle tests inspect telemetry for all phase and termination paths without changed run outcomes.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: equivalent Agy and shared-shutdown tests prove per-invocation identity, resume behavior, and idempotent cleanup.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: spec lint, runner-focused tests, bare full suite, and diff check pass; a field-by-field parity assertion covers both hosts.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: both runner integrations must ship together to prevent host-specific observability and schema drift.

Execute only after approval and after Order 03 is executed. Telemetry failures are diagnostic only and must never turn successful work into failure or mask an existing failure.
