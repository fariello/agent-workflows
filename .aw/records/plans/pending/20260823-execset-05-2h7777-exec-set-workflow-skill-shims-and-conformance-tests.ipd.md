# IPD: Exec Set Workflow Skill Shims and Conformance Tests

- Date: 2026-08-23
- Kind: child
- Concern: Make autonomous Set execution discoverable, portable, understandable, and regression-proof.
- Scope: Canonical `/exec-set` workflow, thin skill/shims, CLI UX, examples, lifecycle wording, conformance, security, and release readiness.
- Status: reviewed
- Set: execset
- Order: 5
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 2h7777

## Workflow history
- 2026-08-23 /plan-review focused (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (help advertised nonexistent commands - aw run questions/decisions, --max-parallel, execute-set --resume; E-02 must own or trim), PR-002 (lifecycle-wording overlap with Order 02 - inherit, do not re-author the shared always-loaded surface), PR-003 (skill-generation-into-installer wiring is net-new), PR-004 (manifest-row registration mechanism clarified). V-02 strengthened.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; no plan-specific finding (reviewed as Set evidence; conforms).
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created as the packaging and proof tail of the Set.

## Goal

Expose one concise `/exec-set` entry point across hosts while keeping authority in the deterministic runtime and proving the exact no-stop, evidence, parallelism, and compatibility contracts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Canonical workflow and skill

- [ ] E-01 Add `.aw/system/workflows/exec-set/` and manifest rows for `exec-set` plus plan-only mode over the same coordinator; generate a compact Agent Skill/router and host shims with semantic-digest parity.
  - Depends on: none
  - Note (verified - registration mechanism + net-new wiring): register by adding the workflow subdir `.aw/system/workflows/exec-set/` and a manifest ROW inside `index.md` between the `WORKFLOWS-MANIFEST` markers (`engine.py:220-221`, table at `.aw/system/workflows/index.md:28-91`; columns `command|body|lens|description|arg-hint`), following the multi-file `release-review/`/`plan-review-long/` pattern (one manifest row each + a per-dir README/steps). REUSE the existing skill/shim generation (`host_adapters.build_skill_package`, `compute_workflow_semantic_digest`, `engine.generate_shim_members`/`validate_shim_grammar`) and the drift/parity checks (`migration_compact.detect_shim_drift`, `tests/test_migration_compact_shims.py`) - do not fork. NOTE: that skill generation is library code today and is NOT yet wired into the installer `run()` path (no `.agents/skills/` is emitted), so wiring generation-into-target is net-new here.
  - Expected outcome: supported hosts discover `/exec-set`, while explicit `aw ipd execute-set` always remains available.
  - Execution state: pending

### Material change 2: Self-documenting interface and lifecycle sync

- [ ] E-02 Add human/agent CLI output, help, config examples, decision/question/resume commands, and update `ipd-lifecycle`/templates so child `STOP` is contained and deferred work cannot be reported executed.
  - Depends on: E-01
  - Note (verified - own or align the advertised surface; verb accuracy): the help block below advertises commands that do NOT exist today. `aw run` exposes `show|evidence|verify-ledger|start|next|record|resume|cancel|status|finalize` (`run_cli.py:49-73`) - it has `status` and `resume` but NO `questions` or `decisions` subcommands, and no sibling Order adds them (Order 02 emits `decisions.md`/`open-questions.md` FILES, not `aw run` subcommands). `--max-parallel` is not a wired flag anywhere. `aw ipd execute-set` is net-new (Order 01 adds `--plan-only`, Order 03 the executor). E-02 MUST either (a) add the `aw run questions|decisions` inspection subcommands + the `--max-parallel` flag it advertises (own them here), or (b) trim the help to the surfaces that exist / are delivered by Orders 01/03; do NOT ship help that names nonexistent commands. Confirm the resume spelling matches Order 03's executor (`aw ipd execute-set --resume <run-id>`).
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

CROSS-PLAN COORDINATION (verified): the child-`STOP`-containment / "deferred work cannot be reported executed" wording lives on the SHARED, always-loaded surfaces `.aw/system/workflows/ipd-lifecycle/ipd-lifecycle.md:20`, `.aw/records/specs/20260726-1340-01-ipd-spec.spec.md:35`, and the generated AGENTS block `agent_workflows/engine.py:1138-1148` - and Order 02 (`3m4e54`) already OWNS the substantive semantic change there (its Spec-sync claims those exact lines). Because this Order runs after 01-04, it MUST INHERIT Order 02's wording and confine itself to the exec-set workflow/skill/TEMPLATE surface (new `.aw/system/workflows/exec-set/`, generated skills/shims, README/index rows); it MUST NOT re-author the shared lifecycle/spec/always-loaded text Order 02 changed (avoid divergent phrasing on an always-loaded surface). Verified doc-sync targets that DO exist: `.aw/system/workflows/index.md` manifest, `README.md:150-160` workflow table, `/list-workflows` (a workflow, not a CLI verb), `CONTRIBUTING.md:14-30` doc-sync checklist, `getting-started`.

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
  - Required evidence: golden human/agent help and run reports expose invocation, partial state, decisions, questions, resume, and evidence compactly; lifecycle fixtures prove child `STOP` cannot terminate the Set or mark deferred work executed. SPECIFICALLY: every command the shipped help text names actually dispatches (no help line advertises a nonexistent command) - i.e. `aw run questions`/`aw run decisions`/`--max-parallel`/`aw ipd execute-set --resume` either exist and are tested, or were trimmed from the help; and the lifecycle fixture uses Order 02's (inherited) shared wording, not a re-authored variant.
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
