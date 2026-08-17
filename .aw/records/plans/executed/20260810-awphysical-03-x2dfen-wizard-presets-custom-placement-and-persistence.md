# IPD: Wizard presets, custom placement, pre-write plan preview, and persistence

- Date: 2026-08-10
- Kind: child
- Concern: physical-layout
- Scope: agent_workflows/install_wizard.py, agent_workflows/project_layout.py, agent_workflows/cli.py, tests/test_install_wizard.py, tests/fixtures/awphysical/order03/
- Status: executed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 3
- Highest E allocated: 07
- Author: agent
- Id: x2dfen

## Workflow history

- 2026-08-10: Created by aw layout orchestrator plan.
- 2026-08-10: Executed task groups 1-3, implemented wizard state machine, 4 presets, custom placement validation, pre-write plan preview, accessibility matrix, and atomic policy persistence; validated all V-01..V-07 items with red-then-green proof (Antigravity executor; execute commits 8b00280, ae482e3, 7c2bbd9). The wrapper reported ERROR: timeout waiting for response because the executor's turns exceeded the print-timeout, but the work and plan bookkeeping were completed; resumed once with agy --continue.
- 2026-08-11 orchestrator verification + terminal transition (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): Independent verification with NO fix required (clean first execution under the hardened prompts). Full suite `python3 -m unittest discover -s tests -t .` = Ran 843 OK (skipped=1) exit 0 (baseline 837 + 7 Order-03 E-tests). Read all Order-03 test bodies: they assert real fail-closed/rejection behavior (IncompletePolicyError before any write, InvalidPolicyError on forbidden clean-delta+repository and on tracked config_local/state_runtime, PolicyCancelledError on decline, no ANSI leak under color=False, home path rendered portably as ~), not existence checks. Mutation-probe confirmed the clean-delta/repository invariant test fails RED when the check is neutralized and GREEN when restored. Pre-transition ipd lint conforming. Status approved -> executed; Approval line removed; moved pending/ -> executed/.

## Goal

Implement the complete AW policy wizard state machine, four approved presets (`private-target`, `public-private-companion`, `clean-target`, `local-only`), custom placement validation, exact pre-write plan preview, update checkpoints, and atomic persistence specified by Sections 5, 6, 8, 11, and 13 of `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Wizard state machine, presets, and subflows

- [x] E-01 Implement pure wizard state machine, first-install vs update classification, and fail-closed noninteractive policy resolution.
  - Depends on: none
  - Expected outcome: Wizard choice logic and policy validation are separate from terminal rendering and writes; unconfigured repositories default to first install and require complete choices; existing policies trigger update review.
  - Execution state: performed

- [x] E-02 Implement four approved presets (`private-target`, `public-private-companion`, `clean-target`, `local-only`) plus advanced custom selection with invariant enforcement.
  - Depends on: E-01
  - Expected outcome: Approved presets set valid placements and Git policies; custom selection enforces all Order 01 invariants before confirmation.
  - Execution state: performed

- [x] E-03 Implement target visibility, companion directory selection, source-checkout role locking, host selection, and Git-safety subflows.
  - Depends on: E-01
  - Expected outcome: Visibility warnings trigger companion switch; source checkouts lock system placement; host exceptions are acknowledged; no silent Git init/remote/push.
  - Execution state: performed

### Task group 2: Preview, confirm, and persist

- [x] E-04 Render one exact pre-write plan showing every resolved path, containing Git repository, track/ignore policy, public/private acknowledgement, adapter exception, expected target delta, companion delta, and unresolved durability action.
  - Depends on: E-01
  - Expected outcome: Confirmation is informed and self-contained; home-relative paths are displayed portably where possible and absolute machine paths are never persisted into public/tracked policy; color improves navigation but all meaning remains in labels and monochrome output.
  - Execution state: performed

- [x] E-05 Wire the confirmed policy through atomic Order 02 persistence and materialization handoffs used by `aw install`, `aw install all`, and `aw setup`; add complete noninteractive flags and fail closed when required first-install choices are absent.
  - Depends on: E-01
  - Expected outcome: Wizard selections survive the process, update checkpoints show the saved policy, dry-run writes nothing, and `--yes` never invents first-install consent.
  - Execution state: performed

- [x] E-06 Implement update review/change flows that preserve current policy by default, preview migrations before policy switches, and never conflate `aw setup` with the `/setup-repo` workflow or its action.
  - Depends on: E-01
  - Expected outcome: Ordinary updates are concise; material placement changes invoke migration planning rather than mutating roots in place; setup terminology follows the shipped `aw setup` versus `/setup-repo` distinction and the persisted `setup-repo` action contract in the superseding spec.
  - Execution state: performed

### Task group 3: Test all interaction modes

- [x] E-07 Add transcript, pure-state, CLI, TTY, `NO_COLOR`, `TERM=dumb`, noninteractive, dry-run, cancellation, EOF, batch, source-checkout, and invalid-combination tests for every preset and representative custom choices.
  - Depends on: E-01
  - Expected outcome: Prompt sequences and outputs are stable, accessible, resumable where appropriate, and behaviorally equivalent across entry points.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Set dependencies: Orders 01 and 02 must be executed and verified first.
- The wizard chooses; `project_context.py` resolves; materializers write. These responsibilities must not collapse.
- The repository has concurrent work on exclusion lists and CLI help. This Order may improve help only for new flags it owns and must coordinate any shared parser edits.
- Terminal color must never be the only carrier of state, risk, default, or confirmation meaning.
- Spec traceability: E-01 through E-03 implement Sections 5 and 8; E-04/E-05 implement Section 8; E-06/E-07 implement Sections 8 and 13, including AWP-043/AWP-044.

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
| E-01 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e01` | `first-interactive-complete`, `first-closed-stdin`, `first-incomplete-policy`, `update-existing-policy` | Complete first install resolves every required choice; closed stdin and incomplete policy both exit nonzero before any filesystem/registry/index write and list missing choices; existing policy is recognized only in update fixture. | either AWP-043 negative fixture writes/defaults/succeeds, or complete/update classification differs |
| E-02 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e02` | `tests/fixtures/awphysical/order03/e02-*` | Private-target, public-plus-private-companion, clean-target, and local-only choices are screen-sized and safe by default; custom mode cannot bypass Order 01 invariants. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e03` | `tests/fixtures/awphysical/order03/e03-*` | The wizard does not infer remote privacy or repository ownership and does not silently initialize Git, choose a remote, push, or migrate. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e04` | AWP-044 modes: `color-auto`, `color-always`, `color-never`, `NO_COLOR`, `TERM-dumb`, `redirected`, `screen-reader` | Normalized words, choices, risks, defaults, and exit status are identical across modes; ANSI is absent when disabled/dumb/redirected; screen-reader output conveys every state without color; absolute canaries remain absent. | meaning differs by mode, ANSI leaks, a state is color-only, or a machine path leaks |
| E-05 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e05` | `tests/fixtures/awphysical/order03/e05-*` | Wizard selections survive the process, update checkpoints show the saved policy, dry-run writes nothing, and `--yes` never invents first-install consent. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e06` | `tests/fixtures/awphysical/order03/e06-*` | Ordinary updates are concise; material placement changes invoke migration planning rather than mutating roots in place; setup terminology follows the shipped `aw setup` versus `/setup-repo` distinction and the persisted `setup-repo` action contract in the superseding spec. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e07` | `tests/fixtures/awphysical/order03/e07-*` | Prompt sequences and outputs are stable, accessible, resumable where appropriate, and behaviorally equivalent across entry points. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Verify implementation against the controlling specification's wizard, noninteractive, update, preview, and accessibility contracts. If implementation conflicts, stop and return the specification to review rather than silently editing approved requirements.
- Add user-facing wizard help for new flags and presets without rewriting unrelated command help owned by concurrent work.
- Keep screenshots or ANSI output out of normative tests; use semantic transcript fixtures.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-10 - the controlling spec `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` was human-approved (Status: approved). The Set is cleared to execute via ipd-lifecycle in dependency order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: Run Evidence matrix row E-01 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e01` -> Ran 1 test in 0.009s OK. Negative demonstration: returning default policy on incomplete flags failed test with `AssertionError: IncompletePolicyError not raised`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Run Evidence matrix row E-02 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e02` -> Ran 1 test in 0.001s OK. Negative demonstration: bypassing custom local config tracking validation failed test with `AssertionError: InvalidPolicyError not raised`.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Run Evidence matrix row E-03 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e03` -> Ran 1 test in 0.001s OK. Negative demonstration: corrupting source-checkout role failed test with `AssertionError: 'corrupted' != 'source-checkout'`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Run Evidence matrix row E-04 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e04` -> Ran 1 test in 0.006s OK. Negative demonstration: injecting ANSI code when color=False failed test with `AssertionError: '\x1b[' unexpectedly found in ... ANSI escape sequences leaked`.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Run Evidence matrix row E-05 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e05` -> Ran 1 test in 0.003s OK. Negative demonstration: skipping project.json write failed test with `AssertionError: False is not true`.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: Run Evidence matrix row E-06 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e06` -> Ran 1 test in 0.001s OK. Negative demonstration: omitting preset from summary output failed test with `AssertionError: 'private-target' not found in ...`.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: Run Evidence matrix row E-07 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_install_wizard.PhysicalLayoutWizardTests.test_e07` -> Ran 1 test in 0.009s OK. Negative demonstration: omitting PolicyCancelledError raise failed test with `AssertionError: PolicyCancelledError not raised`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Presets, custom selection, exact preview, persistence, update behavior, and interaction tests form one user-consent boundary.

Execution requires verified Orders 01 and 02, a GO `/plan-review`, and human approval. Scope fence: wizard/policy CLI surfaces, persistence handoff, terminal rendering, and focused tests/docs. Coordinate before editing parser/help files touched by the active concurrent agent; do not modify exclusion semantics or unrelated help ordering. Paste actual outputs, path-scope every commit, never broad-stage, never push, and stop if any choice can write before complete confirmation or can misstate privacy/durability. Complete evidence and pre-transition lint before moving this plan to `executed/`.
