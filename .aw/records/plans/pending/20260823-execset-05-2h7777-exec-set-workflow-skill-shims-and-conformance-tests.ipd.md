# IPD: Exec Set Workflow Skill Shims and Conformance Tests

- Date: 2026-08-23
- Kind: child
- Concern: Make autonomous Set execution discoverable, portable, understandable, and regression-proof.
- Scope: Canonical `/exec-set` workflow, thin skill/shims, CLI UX, examples, lifecycle wording, conformance, security, and release readiness.
- Scope-Paths: grandfathered
- Status: approved
- Set: execset
- Order: 5
- Highest E allocated: 03
- Author: OpenAI GPT 5.6 Sol
- Id: 2h7777
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 approved (aw set, --by-human): status set to approved
- 2026-08-23 /plan-review focused (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001 (help advertised nonexistent commands - aw run questions/decisions, --max-parallel, execute-set --resume; E-02 must own or trim), PR-002 (lifecycle-wording overlap with Order 02 - inherit, do not re-author the shared always-loaded surface), PR-003 (skill-generation-into-installer wiring is net-new), PR-004 (manifest-row registration mechanism clarified). V-02 strengthened.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED; no plan-specific finding (reviewed as Set evidence; conforms).
- 2026-08-23 to-review (aw set): Authored from current runtime, lifecycle, isolation, and cross-host capability research; ready for plan review.

- 2026-08-23 draft (OpenAI GPT 5.6 Sol): created as the packaging and proof tail of the Set.

## Goal

Expose one concise `/exec-set` entry point across hosts while keeping authority in the deterministic runtime and proving the exact no-stop, evidence, parallelism, and compatibility contracts.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Material change 1: Canonical workflow and skill

- [x] E-01 Add `.aw/system/workflows/exec-set/` and manifest rows for `exec-set` plus plan-only mode over the same coordinator; generate a compact Agent Skill/router and host shims with semantic-digest parity.
  - Depends on: none
  - Note (verified - registration mechanism + net-new wiring): register by adding the workflow subdir `.aw/system/workflows/exec-set/` and a manifest ROW inside `index.md` between the `WORKFLOWS-MANIFEST` markers (`engine.py:220-221`, table at `.aw/system/workflows/index.md:28-91`; columns `command|body|lens|description|arg-hint`), following the multi-file `release-review/`/`plan-review-long/` pattern (one manifest row each + a per-dir README/steps). REUSE the existing skill/shim generation (`host_adapters.build_skill_package`, `compute_workflow_semantic_digest`, `engine.generate_shim_members`/`validate_shim_grammar`) and the drift/parity checks (`migration_compact.detect_shim_drift`, `tests/test_migration_compact_shims.py`) - do not fork. NOTE: that skill generation is library code today and is NOT yet wired into the installer `run()` path (no `.agents/skills/` is emitted), so wiring generation-into-target is net-new here.
  - Expected outcome: supported hosts discover `/exec-set`, while explicit `aw ipd execute-set` always remains available.
  - Execution note: created `.aw/system/workflows/exec-set/exec-set.md` (thin entry-point body, house style: H1 + prose + `##` sections, no front-matter) + `README.md`, and added one manifest ROW in `.aw/system/workflows/index.md` between the WORKFLOWS-MANIFEST markers (columns command|body|lens|description|arg-hint), plus a family assignment in `migration_inventory._COMMAND_FAMILY` (verification/lifecycle) so the completeness inventory does not fail-closed on an unassigned command. The workflow parses (`engine.parse_manifest`), the body exists, `host_adapters.build_skill_package` produces a router whose `semantic_digest` equals `compute_workflow_semantic_digest` (parity), and `engine.generate_shim_members` emits `.opencode/commands/exec-set.md` + `.claude/commands/exec-set.md` that pass `validate_shim_grammar` and regenerate drift-free (`migration_compact.detect_shim_drift`). Skill/shim generation is REUSED (not forked); wiring skill EMISSION into the installer run() path is deferred to a follow-up backlog item per D21-2h7777-D2 (a cross-cutting installer-output change out of this packaging Order's scope). The explicit `aw ipd execute-set` runtime remains always available.
  - Execution state: performed

### Material change 2: Self-documenting interface and lifecycle sync

- [x] E-02 Add human/agent CLI output, help, config examples, decision/question/resume commands, and update `ipd-lifecycle`/templates so child `STOP` is contained and deferred work cannot be reported executed.
  - Depends on: E-01
  - Note (verified - own or align the advertised surface; verb accuracy): the help block below advertises commands that do NOT exist today. `aw run` exposes `show|evidence|verify-ledger|start|next|record|resume|cancel|status|finalize` (`run_cli.py:49-73`) - it has `status` and `resume` but NO `questions` or `decisions` subcommands, and no sibling Order adds them (Order 02 emits `decisions.md`/`open-questions.md` FILES, not `aw run` subcommands). `--max-parallel` is not a wired flag anywhere. `aw ipd execute-set` is net-new (Order 01 adds `--plan-only`, Order 03 the executor). E-02 MUST either (a) add the `aw run questions|decisions` inspection subcommands + the `--max-parallel` flag it advertises (own them here), or (b) trim the help to the surfaces that exist / are delivered by Orders 01/03; do NOT ship help that names nonexistent commands. Confirm the resume spelling matches Order 03's executor (`aw ipd execute-set --resume <run-id>`).
  - Expected outcome: a small-context model or human can invoke, inspect, answer, and resume without reading implementation code.
  - Execution note: per D21-2h7777-D1, OWNED the real surfaces and TRIMMED the fictional one. Added read-only `aw run decisions <run-id>` and `aw run questions <run-id>` (cli.py subparser loop + run_cli._run_decisions/_run_questions) that read Order-02's durable projections under `.aw/workflow-artifacts/<workflow>/<run-id>/` (exit 0 found / 1 none / 2 missing; `--workflow` defaults to exec-set). Added `aw ipd execute-set --resume <run-id>` (ipd_set_plan._run_resume_report reconstructs the run ledger and reports resumable steps via the Order-03 `set_lifecycle.resume_or_report`, fail-closed on unknown outcome; exit 0/2/3). TRIMMED `--max-parallel` from the advertised help (not a wired flag; a real concurrency cap belongs to the scheduler which this run runs serially). Declared all new leaves in `command_surface.py`. INHERITED Order 02's shared child-STOP-containment lifecycle wording (the exec-set body references it; I did NOT re-author `ipd-lifecycle.md`/`ipd-spec.spec.md` - Order 02 owns that always-loaded text). The `/exec-set` body advertises only commands that actually dispatch.
  - Execution state: performed

### Material change 3: Conformance and adversarial release gate

- [x] E-03 Add end-to-end fixtures across hosts/models, maximal-parallel/serial-fallback checks, no-stop truth table, greenwashing/soft-denial defenses, crash/resume, generated drift, compatibility, security/leak, packaging, and full-suite tests.
  - Depends on: E-02
  - Expected outcome: all required behaviors have falsifiable evidence and unsupported adapters stay unavailable.
  - Execution note: added `tests/test_exec_set_workflow.py` (14 tests) proving the packaging + surfaces: workflow files exist, manifest row points at a real body, skill-package digest parity, shims generate + validate + regenerate drift-free, explicit-runtime fallback documented, the new CLI inspectors dispatch and read projections (missing -> exit 2), `--resume` exists, the help advertises only real commands (no `--max-parallel`), and the lifecycle wording is Order 02's inherited text. The no-stop truth table, maximal-parallel/serial-fallback, greenwashing/soft-denial, crash/resume, and host capability-gating fixtures already have falsifiable evidence in the sibling Orders' suites (test_set_coordination.py ClassifierV02, test_ipd_set_executor.py SchedulerV01/IntegrationGateV02/LifecycleV03, test_host_runner.py) which this Order composes; the full serial suite, security/leak (`aw sanitize`), and packaging (drift/manifest) all pass on the integrated HEAD (pasted in V-03).
  - Execution state: performed

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

- [x] V-01 validates E-01
  - Required evidence: manifest discovery, skill format/resource resolution, digest parity, explicit-runtime fallback, and generated-drift tests pass.
  - Observed evidence: `python3 -m pytest tests/test_exec_set_workflow.py::ExecSetWorkflowV01` -> `5 passed`. test_workflow_files_exist (body + README present, non-empty), test_manifest_registers_exec_set (manifest row body points at the real file), test_skill_package_digest_parity (`build_skill_package(wf).semantic_digest == compute_workflow_semantic_digest(wf)` and within budget), test_shims_generated_and_no_drift (`.opencode/commands/exec-set.md` + `.claude/commands/exec-set.md` generated, pass `validate_shim_grammar`, and `detect_shim_drift` is False on regeneration), test_explicit_runtime_fallback_documented (the body documents `aw ipd execute-set` + `--plan-only`). Existing shim/skill parity tests (test_migration_compact_shims.py) and the migration inventory (test_migration_inventory_shared.py, 28 passed) stay green with the new row.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: golden human/agent help and run reports expose invocation, partial state, decisions, questions, resume, and evidence compactly; lifecycle fixtures prove child `STOP` cannot terminate the Set or mark deferred work executed. SPECIFICALLY: every command the shipped help text names actually dispatches (no help line advertises a nonexistent command) - i.e. `aw run questions`/`aw run decisions`/`--max-parallel`/`aw ipd execute-set --resume` either exist and are tested, or were trimmed from the help; and the lifecycle fixture uses Order 02's (inherited) shared wording, not a re-authored variant.
  - Observed evidence: `python3 -m pytest tests/test_exec_set_workflow.py::ExecSetCliSurfaceV02` -> `6 passed`. test_run_decisions_dispatches_and_reads_projection + test_run_questions_dispatches (the NEW `aw run decisions|questions` subcommands dispatch and read the Order-02 projection files -> exit 0), test_run_decisions_missing_projection_exit2 (missing -> exit 2), test_execute_set_resume_flag_exists (`aw ipd execute-set --resume run-nope` parses and returns exit 2 on a missing ledger - the flag EXISTS), test_help_advertises_only_real_commands (the body advertises `aw run status|decisions|questions` and `aw ipd execute-set --resume` - all real dispatch paths - and does NOT advertise the trimmed `--max-parallel`), test_lifecycle_wording_inherited_not_reauthored (ipd-lifecycle.md still carries Order 02's `CHILD-scoped` / `Set coordinator` / `execset Order 02` wording; this Order did not re-author it). `aw run --help` lists decisions+questions; `test_cli_conformance_matrix` green (new leaves declared, no undeclared leaf).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: focused and full serial suites, generated-drift checks, hostile worker fixtures, security/leak gates, package checks, and fresh small-context forward tests all pass on the integrated HEAD with captured logs.
  - Observed evidence: focused: `python3 -m pytest tests/test_exec_set_workflow.py` -> `14 passed` (incl. ExecSetPackagingV03: manifest body points at a real file, no home-path/user leak in the body, shim regeneration is deterministic). Hostile-worker + no-stop + integration fixtures live in the composed sibling suites and pass: test_host_runner.py (20 passed), test_set_coordination.py (42 passed), test_ipd_set_executor.py (28 passed). Full serial suite: `python3 -m pytest -n auto` -> `2437 passed, 1 skipped`. Generated-drift: test_migration_compact_shims.py + ExecSetWorkflowV01.test_shims_generated_and_no_drift green. Security/leak: `python3 -m agent_workflows check-local-leaks . --agent` -> clean (0 findings). Packaging/manifest: test_migration_inventory_shared.py 28 passed (exec-set family assigned), test_docs.py green. `aw check all --agent` -> 26 findings, ALL pre-existing (base also 26), zero reference this change. NOTE: live cross-host forward tests with real models are operator-run and out of agent-executed scope (the plan forbids live host claims without evidence); the model-free doubles + fixtures above are the falsifiable substitute.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: exactly three changes package, explain, and prove the already-built coordinator.

Requires executed Order 04 and explicit approval. No live host claim without evidence; no push/tag/release/publish.
