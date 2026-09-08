# IPD: Cross-host resource telemetry schema, collector, and sampling controls

- Date: 2026-09-08
- Kind: child
- Concern: Capture contemporaneous resource context without leaking host identity or making runner reliability depend on optional probes.
- Scope: Build the telemetry event schema, safe system probes, pseudonymous node identity, lifecycle collector, periodic sampler, overhead limits, and configuration model.
- Scope-Paths: agent_workflows/run_analytics_telemetry.py, agent_workflows/run_analytics_config.py, tests/test_run_analytics_telemetry.py, tests/test_run_analytics_config.py
- Item-Dependencies: executed:bzz5e6
- Status: to-review
- Set: runanalytics
- Order: 3
- Highest E allocated: 03
- Author: Codex
- Id: lhccjf

## Workflow history

- 2026-09-08 draft (Codex): created.
- 2026-09-08 to-review (Codex): specified telemetry events, privacy minimization, multi-node behavior, degradation, and sampling controls.

## Goal

Provide a runner-neutral telemetry collector that records what hardware and load were present when an invocation actually ran, including node changes between attempts. Telemetry must be useful for performance analysis but non-fatal, bounded, configurable, and privacy-minimized.

## Detailed Implementation Checklist (TODO)

### Task group 1: Schema and safe probes

- [ ] E-01 Define versioned \`start\`, \`sample\`, and \`end\` JSONL events plus safe, portable resource probes.
  - Depends on: none
  - Expected outcome: events can represent execution/run/IPD/set/attempt/phase/host/model identifiers; timestamps and monotonic offsets; CPU count/capacity, memory totals and availability, load, process RSS/CPU, disk capacity, accelerator inventory/utilization when safely available, tool versions, exit status, and probe warnings.
  - Execution state: pending
- [ ] E-02 Implement pseudonymous node identity, basic snapshots, optional periodic sampling, lifecycle shutdown, and failure isolation.
  - Depends on: E-01
  - Expected outcome: one execution ID has exactly one start and best-effort end, samples stop on every normal/exception/signal cleanup path, a node change creates a different local pseudonym, and missing permissions or utilities emit warnings without failing work.
  - Execution state: pending
- [ ] E-03 Implement validated telemetry configuration and prove bounded overhead and privacy behavior across supported and degraded systems.
  - Depends on: E-02
  - Expected outcome: basic start/end telemetry is the default; periodic sampling is opt-in, interval-bounded, configurable, and disableable; tests use injected clocks/probes and include Linux, absent procfs, absent GPU tool, malformed output, timeout, and slow-probe cases.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Runner configuration and user-local profile storage already have project helpers; this module must integrate with those authorities rather than create an unrelated config home.
- The runners stream child output and have established signal/shutdown paths. The collector must expose a small lifecycle API for Order 04 to call without owning process policy.
- Hardware may vary by cluster node and by resumed attempt, so telemetry is per invocation, not a one-time installation inventory.
- Arbitrary environment capture is prohibited. Only explicitly reviewed non-secret categorical values may be allowlisted, and environment values must never be a fallback for host identity.
- Optional command probes require strict executable allowlists, timeouts, output-size caps, and parsers that persist only numeric/categorical fields, never raw stdout/stderr.

## Findings

| Topic | Required decision |
|---|---|
| Identity | Generate a locally stable keyed pseudonym from machine identity where available; persist neither the input nor raw hostname. Document correlation scope and rotation. |
| Sampling default | Capture start/end basic snapshots by default because they are low-volume and necessary to interpret run timing. Ask separately before enabling periodic samples. |
| Model price | Telemetry records provider/model/variant and runner/tool versions, not a guessed price. Pricing is joined by Order 06. |
| Probe failure | Record structured \`unavailable\`, \`timeout\`, or \`parse_error\` codes and continue the run. |
| Overhead | Define a measurable maximum probe time and event rate; skip overlapping samples instead of accumulating work. |

## Proposed changes (ordered, validatable)

1. Create strict dataclasses or equivalent typed schema and injected portable probe adapters.
2. Build a context-managed collector with monotonic timing, bounded background sampling, atomic JSONL append, and idempotent close.
3. Add configuration validation and deterministic failure/overhead/privacy tests.

## Deferred / out of scope (with reason)

- Hooking collectors into OpenCode and Agy lifecycle code is Order 04.
- Analysis of resource correlation is Order 06.
- Detailed process tracing, file contents, network addresses, and arbitrary environment collection are excluded for privacy and overhead.
- Continuous monitoring outside active runner invocations is not authorized.

## Scope check

- Over-scope: no runner orchestration, run parsing, report UI, submission, or installer prompting.
- Under-scope: includes schema, probes, sampler, config, identity, cleanup, warning codes, performance budget, and tests required for safe integration.

## Required tests / validation

- Event-schema round trips and rejection of unknown/private fields.
- Start/end ordering, monotonic durations, sample cadence, no overlap, idempotent close, exception and signal-assisted cleanup.
- Multi-node pseudonym distinction and same-node local stability without persisting identity inputs.
- Missing tools/files/permissions, timeouts, malformed output, impossible values, and clock skew.
- Secret/path/hostname canary scan over JSONL and logs.
- Measured test proving configured sampling does not exceed the documented event rate or block runner execution beyond the probe budget.
- Bare \`python3 -m pytest\` and \`git diff --check\`.

## Spec / documentation sync

Order 04 must amend the controlling runner contract if it defines the run artifact inventory. Order 10 documents configuration, privacy limits, platform coverage, and overhead. Do not market the telemetry as anonymous.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting done)

- [ ] V-01 validates E-01
  - Required evidence: schema and probe-adapter tests cover every field family, platform fallback, bound, and validation failure.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: lifecycle tests produce one well-formed JSONL stream per execution and show cleanup plus non-fatal degradation.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: default/disabled/periodic configurations, privacy canaries, overhead measurements, full suite, and diff check pass.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: the schema cannot be approved independently of the privacy, degradation, and overhead guarantees of its collector.

Execute only after approval. Any newly proposed field must pass the privacy allowlist review and tests before persistence; implementation convenience is not sufficient justification.
