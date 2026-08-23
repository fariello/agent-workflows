# IPD: Exec Set Workflow Skill Shims and Conformance Tests

- Date: 2026-08-23
- Kind: child
- Concern: Make autonomous Set execution discoverable, portable, understandable, and regression-proof.
- Scope: Canonical `/exec-set` workflow, thin skill/shims, CLI UX, examples, lifecycle wording, conformance, security, and release readiness.
- Status: to-review
- Set: execset
- Order: 5
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 2h7777

## Workflow history
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created as the packaging and proof tail of the Set.

## Goal

Expose one concise `/exec-set` entry point across hosts while keeping authority in the deterministic runtime and proving the exact no-stop, evidence, parallelism, and compatibility contracts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Canonical workflow and skill

- [ ] E-01 Add `.aw/system/workflows/exec-set/` and manifest rows for `exec-set` plus plan-only mode over the same coordinator; generate a compact Agent Skill/router and host shims with semantic-digest parity.
  - Depends on: none
  - Expected outcome: supported hosts discover `/exec-set`, while explicit `aw ipd execute-set` always remains available.
  - Execution state: pending

### Material change 2: Self-documenting interface and lifecycle sync

- [ ] E-02 Add human/agent CLI output, help, config examples, decision/question/resume commands, and update `ipd-lifecycle`/templates so child `STOP` is contained and deferred work cannot be reported executed.
  - Depends on: E-01
  - Expected outcome: a small-context model or human can invoke, inspect, answer, and resume without reading implementation code.
  - Execution state: pending

### Material change 3: Conformance and adversarial release gate

- [ ] E-03 Add end-to-end fixtures across hosts/models, maximal-parallel/serial-fallback checks, no-stop truth table, greenwashing/soft-denial defenses, crash/resume, generated drift, compatibility, security/leak, packaging, and full-suite tests.
  - Depends on: E-02
  - Expected outcome: all required behaviors have falsifiable evidence and unsupported adapters stay unavailable.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Complex workflows should be thin skill entry points; authoritative behavior never lives only in SKILL.md prose.
- Existing host/shim generators and capability evidence must be extended, not duplicated.
- Run scratch remains under ignored `.aw/workflow-artifacts`; durable walkthrough/backlog records follow normal AW conventions.

## Findings

Separate host workflows would multiply semantic drift. A single small router is friendlier to weak-context models and leaves scheduling/checklists/evidence in deterministic code. Plan-only must be a flag/alias over the same coordinator, not a companion implementation.

## Proposed changes (ordered, validatable)

Target help:

```text
/exec-set <set-id> [--plan-only] [--max-parallel N]
Executes every approved runnable child. Questions are deferred when safe.
Stops only when human input is required and neither affected work nor IPD can be skipped.
Run records: aw run status|questions|decisions <run-id>
Resume: aw ipd execute-set --resume <run-id>
```

The final report begins with completed, deferred, failed, and remaining tables; lists decisions and questions; states whether combined validation passed; and never calls a partial Set complete.

## Deferred / out of scope (with reason)

- GUI dashboards and distributed scheduling are deferred.
- Release/tag/push remains outside `/exec-set` unless a separate explicitly approved workflow owns it.

## Scope check

- Over-scope: none.
- Under-scope: test small-context workers with bounded packets and no inherited intended answer.

## Required tests / validation

Forward-test the skill on realistic Sets using fresh agents; run all focused/unit/integration/golden/security/packaging tests, full serial suite, `aw check all`, `aw doctor --agent`, and `aw sanitize --agent`. Preserve actual outputs.

## Spec / documentation sync

Update workflow index, README/getting-started/list-workflows, CLI help, contributor command checklist, lifecycle/template wording, generated skills/shims, and evidence-derived support matrix.

## Open questions

### OQ-01: Separate planning workflow?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: no. Planning is mandatory inside execute-set; expose `--plan-only` and an optional alias over the same code path.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: manifest discovery, skill format/resource resolution, digest parity, explicit-runtime fallback, and generated-drift tests pass.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: golden human/agent help and run reports expose invocation, partial state, decisions, questions, resume, and evidence compactly; lifecycle fixtures prove child `STOP` cannot terminate the Set or mark deferred work executed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: focused and full serial suites, generated-drift checks, hostile worker fixtures, security/leak gates, package checks, and fresh small-context forward tests all pass on the integrated HEAD with captured logs.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes package, explain, and prove the already-built coordinator.

Requires executed Order 04 and explicit approval. No live host claim without evidence; no push/tag/release/publish.
