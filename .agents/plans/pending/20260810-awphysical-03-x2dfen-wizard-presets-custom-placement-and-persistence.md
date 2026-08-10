# IPD: Wizard presets custom placement and persistence

- Date: 2026-08-10
- Kind: child
- Concern: Give first installs and updates a complete, accessible, privacy-honest policy wizard whose choices are actually persisted and consumed.
- Scope: Install/setup policy wizard, preset/custom choice model, exact consequence preview, noninteractive flags, policy persistence handoff, update checkpoints, terminal rendering, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 3
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: x2dfen

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to replace the current two-question, non-persisted policy interview with complete preset-first configuration.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.


## Goal

Let a user choose the intended privacy, durability, and repository footprint without understanding resolver internals. Before any write, show exact physical paths, Git owners, tracked/ignored consequences, host exceptions, durability limits, and migration implications, then persist the confirmed policy for all install entry points.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Build a complete pure choice model

- [ ] E-01 Replace the current coarse `ProjectPolicy` interview model with a pure wizard state machine over the Order 01/02 schema, distinguishing truly unconfigured projects from configured projects and separating choice logic from rendering and writes.
  - Depends on: none
  - Expected outcome: First install, including EOF/closed stdin, cannot be mistaken for an update or silently defaulted; every wizard result fully resolves all root classes, Git policies, role, hosts, and durability intent.
  - Execution state: pending

- [ ] E-02 Implement the four approved presets with concise pros, cons, visibility, durability, portability, and collaboration explanations, plus an advanced custom path that exposes only valid combinations.
  - Depends on: E-01
  - Expected outcome: Private-target, public-plus-private-companion, clean-target, and local-only choices are screen-sized and safe by default; custom mode cannot bypass Order 01 invariants.
  - Execution state: pending

- [ ] E-03 Add detailed subflows for target visibility acknowledgement, portable versus local config, durable versus runtime state, records durability, companion selection, enabled hosts, source-checkout detection, and whether migration is required.
  - Depends on: E-01
  - Expected outcome: The wizard does not infer remote privacy or repository ownership and does not silently initialize Git, choose a remote, push, or migrate.
  - Execution state: pending

### Task group 2: Preview, confirm, and persist

- [ ] E-04 Render one exact pre-write plan showing every resolved path, containing Git repository, track/ignore policy, public/private acknowledgement, adapter exception, expected target delta, companion delta, and unresolved durability action.
  - Depends on: E-01
  - Expected outcome: Confirmation is informed and self-contained; home-relative paths are displayed portably where possible and absolute machine paths are never persisted into public/tracked policy; color improves navigation but all meaning remains in labels and monochrome output.
  - Execution state: pending

- [ ] E-05 Wire the confirmed policy through atomic Order 02 persistence and materialization handoffs used by `aw install`, `aw install all`, and `aw setup`; add complete noninteractive flags and fail closed when required first-install choices are absent.
  - Depends on: E-01
  - Expected outcome: Wizard selections survive the process, update checkpoints show the saved policy, dry-run writes nothing, and `--yes` never invents first-install consent.
  - Execution state: pending

- [ ] E-06 Implement update review/change flows that preserve current policy by default, preview migrations before policy switches, and never conflate `aw setup` with the `/setup-repo` workflow or its action.
  - Depends on: E-01
  - Expected outcome: Ordinary updates are concise; material placement changes invoke migration planning rather than mutating roots in place; setup terminology follows the shipped `aw setup` versus `/setup-repo` distinction and the persisted `setup-repo` action contract in the superseding spec.
  - Execution state: pending

### Task group 3: Test all interaction modes

- [ ] E-07 Add transcript, pure-state, CLI, TTY, `NO_COLOR`, `TERM=dumb`, noninteractive, dry-run, cancellation, EOF, batch, source-checkout, and invalid-combination tests for every preset and representative custom choices.
  - Depends on: E-01
  - Expected outcome: Prompt sequences and outputs are stable, accessible, resumable where appropriate, and behaviorally equivalent across entry points.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 01 and 02 must be executed and verified first.
- The wizard chooses; `project_context.py` resolves; materializers write. These responsibilities must not collapse.
- The repository has concurrent work on exclusion lists and CLI help. This Order may improve help only for new flags it owns and must coordinate any shared parser edits.
- Terminal color must never be the only carrier of state, risk, default, or confirmation meaning.

## Findings

- The current interview asks only delivery mode and records backend.
- It does not collect companion path, AW_HOME, config/state placement, tracking policies, source role, enabled hosts, or durability details.
- The `ProjectPolicy` blast radius spans `install_wizard.py`, `project_layout.py`, and `cli.py`; update all three consumers and compatibility tests together.
- Normal installation collects a policy but does not call `materialize_project_layout()` or otherwise persist and apply the complete result.
- Default context resolution can make an unconfigured repository look configured.

## Proposed changes (ordered, validatable)

1. Implement a pure complete wizard state machine.
2. Add four presets and constrained advanced custom selection.
3. Add detailed privacy, Git, companion, durability, host, and source-role subflows.
4. Render exact path/Git consequences and one confirmation boundary.
5. Persist confirmed policy and wire all install/setup entry points.
6. Add update checkpoints and migration handoff.
7. Test every interaction and automation mode.

## Deferred / out of scope (with reason)

- Canonical system copy is Order 04.
- Companion Git mutation is Order 05; this wizard only collects and previews consent.
- Migration execution is Order 07.
- General command help reordering/detail and repository exclusion lists remain concurrent work.

## Scope check

- Over-scope: Policy collection, preview, confirmation, persistence handoff, and tests only; no remote creation, push, migration copy, or cleanup.
- Under-scope: All presets, custom mode, first/update distinction, exact consequences, source checkout, hosts, durability, TTY/accessibility, noninteractive flags, dry-run, cancellation, batch, and migration handoff are covered.

## Required tests / validation

- `python3 -m unittest tests.test_install_wizard tests.test_cli tests.test_config tests.test_project_context`
- Golden transcript tests for all presets and update review/change paths.
- Parser tests for every new explicit flag and invalid/missing first-install policy.
- Dry-run filesystem and Git before/after snapshots.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`
- Full suite after coordinating parser changes with concurrent CLI work.

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e01` | `tests/fixtures/awphysical/order03/e01-*` | First install, including EOF/closed stdin, cannot be mistaken for an update or silently defaulted; every wizard result fully resolves all root classes, Git policies, role, hosts, and durability intent. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e02` | `tests/fixtures/awphysical/order03/e02-*` | Private-target, public-plus-private-companion, clean-target, and local-only choices are screen-sized and safe by default; custom mode cannot bypass Order 01 invariants. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e03` | `tests/fixtures/awphysical/order03/e03-*` | The wizard does not infer remote privacy or repository ownership and does not silently initialize Git, choose a remote, push, or migrate. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e04` | `tests/fixtures/awphysical/order03/e04-*` | Confirmation is self-contained; home-relative display is portable; absolute-path canaries are absent from public/tracked policy; color adds no exclusive meaning. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e05` | `tests/fixtures/awphysical/order03/e05-*` | Wizard selections survive the process, update checkpoints show the saved policy, dry-run writes nothing, and `--yes` never invents first-install consent. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e06` | `tests/fixtures/awphysical/order03/e06-*` | Ordinary updates are concise; material placement changes invoke migration planning rather than mutating roots in place; setup terminology follows the shipped `aw setup` versus `/setup-repo` distinction and the persisted `setup-repo` action contract in the superseding spec. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e07` | `tests/fixtures/awphysical/order03/e07-*` | Prompt sequences and outputs are stable, accessible, resumable where appropriate, and behaviorally equivalent across entry points. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Verify implementation against the controlling specification's wizard, noninteractive, update, preview, and accessibility contracts. If implementation conflicts, stop and return the specification to review rather than silently editing approved requirements.
- Add user-facing wizard help for new flags and presets without rewriting unrelated command help owned by concurrent work.
- Keep screenshots or ANSI output out of normative tests; use semantic transcript fixtures.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: yes
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` is `to-review`. This plan MUST NOT execute until that spec is independently reviewed and human-approved; approval is a design gate, not an executor inference.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Run Evidence matrix row E-01 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: Run Evidence matrix row E-02 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: Run Evidence matrix row E-03 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: Run Evidence matrix row E-04 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: Run Evidence matrix row E-05 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: Run Evidence matrix row E-06 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: Run Evidence matrix row E-07 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Presets, custom selection, exact preview, persistence, update behavior, and interaction tests form one user-consent boundary.

Execution requires verified Orders 01 and 02, a GO `/plan-review`, and human approval. Scope fence: wizard/policy CLI surfaces, persistence handoff, terminal rendering, and focused tests/docs. Coordinate before editing parser/help files touched by the active concurrent agent; do not modify exclusion semantics or unrelated help ordering. Paste actual outputs, path-scope every commit, never broad-stage, never push, and stop if any choice can write before complete confirmation or can misstate privacy/durability. Complete evidence and pre-transition lint before moving this plan to `executed/`.
