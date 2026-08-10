# IPD: Physical root ownership and Git policy contract

- Date: 2026-08-10
- Kind: child
- Concern: Replace the logical-only four-root description with an exact physical hierarchy, internal durable/runtime boundaries, placement vocabulary, and Git-policy invariants.
- Scope: Controlling layout specification, architecture decisions, canonical schema vocabulary, contract tests, and fixtures only; no live migration or producer cutover.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 1
- Highest E allocated: 06
- Author: Codex (GPT-5)
- Id: cwjnj0

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created as the foundational contract for the corrective physical-layout Set.

## Goal

Define one unambiguous hierarchy that keeps AW-installed system content separate from human policy, durable operational facts, disposable runtime data, and workflow-created records. Make physical location and Git tracking explicit policy rather than consequences inferred from repository visibility.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Amend the normative model

- [ ] E-01 Amend the controlling layout specification so target-resident roots are physically `.aw/system/`, `.aw/config/`, `.aw/state/`, and `.aw/records/`, with `config/project.json`, `config/local.json`, `state/durable/`, and `state/runtime/` ownership and tracking rules defined explicitly.
  - Depends on: none
  - Expected outcome: The spec no longer permits tracked `system` to resolve permanently to `.agents/`; local config and runtime state are prohibited from Git; thin host adapters are the only allowed canonical-namespace exceptions.
  - Execution state: pending

- [ ] E-02 Define the closed placement and Git-policy vocabulary for each root/class, including `target-tracked`, `target-ignored`, `home-untracked`, `companion-tracked`, `companion-untracked`, `source-checkout`, and explicitly validated custom paths.
  - Depends on: E-01
  - Expected outcome: Every supported placement has stated containment, ownership, commit destination, portability, durability, privacy, and clean-target consequences; invalid combinations are enumerated.
  - Execution state: pending

- [ ] E-03 Define the four preset contracts: private-target durable tracking, public-target plus private companion, completely clean target, and local-only; define the advanced-custom constraints without making every low-level combination valid.
  - Depends on: E-01
  - Expected outcome: Each preset resolves every root/class and states exactly what is tracked in which Git repository, what is ignored, and what remains external.
  - Execution state: pending

### Task group 2: Encode and test the contract

- [ ] E-04 Update `project_schema.py` with canonical enums/data structures for root class, placement, Git policy, project role, and preset, preserving a versioned compatibility parser for the prior schema.
  - Depends on: E-01
  - Expected outcome: Resolver, wizard, installer, migration, adapters, and tests can import one closed vocabulary; unknown future values fail with actionable errors rather than silently defaulting.
  - Execution state: pending

- [ ] E-05 Add contract fixtures and exhaustive tests that map every valid preset and rejected combination to exact physical roots and permitted commit destinations, including path containment, symlink, case-collision, worktree, and Windows path forms.
  - Depends on: E-01
  - Expected outcome: The policy matrix is executable, complete, cross-platform aware, and cannot drift independently across consumers.
  - Execution state: pending

- [ ] E-06 Append the architecture decision, update terminology references, and run focused schema/spec checks without changing installer or migration behavior in this Order.
  - Depends on: E-01
  - Expected outcome: The decision record explains why durable/runtime and project/local config are split, why runtime is never tracked, and why source checkout is an explicit role.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Executed `awlayout` plans remain immutable. This Order amends their implemented specification through a new dated history entry and append-only decision.
- User-facing prose must avoid em and en dashes; internal plan prose is exempt.
- Schema vocabulary is stdlib-only and imported, never duplicated as local string lists.
- A path being inside a private repository does not make locks, caches, backups, or local machine bindings suitable for Git.

## Findings

- The existing spec calls the `.aw/` tree logical and explicitly maps tracked system content to `.agents/` in `project_context.py`.
- `state` currently combines durable actions/history with transactions, backups, locks, and other runtime material.
- The existing two-axis model does not encode independent placement or tracking for config and state.
- Host-specific discovery paths justify thin adapters, not canonical workflow bodies or records outside `.aw/`.

## Proposed changes (ordered, validatable)

1. Amend the normative tree and ownership boundaries.
2. Freeze closed placement, tracking, role, and preset vocabularies.
3. Define exact preset matrices and invalid combinations.
4. Encode the vocabulary once in `project_schema.py`.
5. Add exhaustive contract fixtures and tests.
6. Record the architectural rationale and compatibility relation.

## Deferred / out of scope (with reason)

- Wizard implementation is Order 03.
- System relocation and packaging are Order 04.
- Companion operations are Order 05.
- Live migration is Orders 06 and 07.
- Producer and adapter cutover are Orders 08 and 09.

## Scope check

- Over-scope: This Order defines and encodes contracts only; it must not move files or change active writers.
- Under-scope: Physical paths, root internals, ownership, Git eligibility, presets, custom constraints, project roles, host exceptions, invalid combinations, compatibility vocabulary, and cross-platform path cases are included.

## Required tests / validation

- `python3 -m unittest tests.test_project_schema tests.test_project_context`
- New policy-matrix fixture test covering every supported and rejected combination.
- `python3 -m agent_workflows specs check --agent`
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`
- Scoped search proving no normative current-state text still maps tracked system to `.agents/`, excluding clearly labeled historical material.

## Spec / documentation sync

- Amend `.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` with a new corrective section and dated workflow-history entry.
- Append a new `ARCHITECTURE.md` decision; do not rewrite D126 through D129.
- Update schema documentation and fixture comments only where required by this Order.

## Open questions

No open questions. The maintainer approved the refined physical hierarchy and the rule that durable material may be tracked while local config and runtime state remain ignored.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: The amended spec contains the exact tree and ownership table, prohibits canonical tracked system content under `.agents/`, and distinguishes every durable, local, and runtime class without contradictory current-state text.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Every supported placement has stated containment, ownership, commit destination, portability, durability, privacy, and clean-target consequences; invalid combinations are enumerated. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Each preset resolves every root/class and states exactly what is tracked in which Git repository, what is ignored, and what remains external. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Resolver, wizard, installer, migration, adapters, and tests can import one closed vocabulary; unknown future values fail with actionable errors rather than silently defaulting. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: The policy matrix is executable, complete, cross-platform aware, and cannot drift independently across consumers. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: The decision record explains why durable/runtime and project/local config are split, why runtime is never tracked, and why source checkout is an explicit role. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Physical hierarchy, ownership, placement vocabulary, presets, and schema fixtures are one foundational contract consumed by every later Order.

Execution requires a GO `/plan-review`, human approval of the controlling spec, and confirmation that concurrent CLI work does not overlap the scoped schema/spec files. Scope fence: only the controlling spec, append-only architecture decision, canonical schema vocabulary, and their focused tests/fixtures. Do not modify wizard, installer, migration, producer, adapter, exclusion-list, or CLI-help behavior. Paste actual runner output for every pass, commit only explicitly scoped paths with path-scoped Git commands, never broad-stage, and never push. On completion, satisfy pre-transition lint, append evidence, and move this plan to `executed/`.
