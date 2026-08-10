# IPD: Documentation release and end-to-end acceptance

- Date: 2026-08-10
- Kind: child
- Concern: Ship the physical-layout change as an honest major-version migration with complete user guidance, bounded compatibility, executable acceptance evidence, and no unsupported claims.
- Scope: User/developer documentation, CLI help for new layout surfaces, compatibility/deprecation messaging, release metadata and package gates, scenario manifest, end-to-end tests, final Set evidence, and release handoff.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 12
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: pszk6x

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created as the final documentation, compatibility, acceptance, and release boundary for the Set.

## Goal

Make the new hierarchy understandable and safe for first-time users, existing private repositories, public projects with private companions, clean-target users, and the agent-workflows source checkout. Prove every documented claim with a named scenario and actual executable evidence before preparing a major-version release.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Document the complete user model

- [ ] E-01 Rewrite current installation, update, storage, context, companion, tracking, migration, rollback, cleanup, uninstall, privacy, and troubleshooting documentation around the physical `.aw/` hierarchy and four preset outcomes.
  - Depends on: none
  - Expected outcome: Every example shows exact paths and Git consequences; local/runtime exclusions are explicit; public/private language is honest; old `.agents` canonical-layout text is limited to migration/history.
  - Execution state: pending

- [ ] E-02 Add migration guides for private all-in-repository, public plus private companion, clean target, local-only, custom, partial prior migration, interrupted migration, worktree, and source-checkout cases, including preflight, confirmation, separate commits, rollback, retention, postcheck, and follow-up review.
  - Depends on: E-01
  - Expected outcome: Users can migrate without guessing command order or when legacy data is safe to remove; no guide tells users to push or delete automatically.
  - Execution state: pending

- [ ] E-03 Update developer/packaging/extension documentation for canonical system source, source-checkout role, router APIs, adapter generation, policy schemas, migration schemas, evidence tools, and compatibility removal criteria.
  - Depends on: E-01
  - Expected outcome: Contributors know which files are source, generated, installed, human-owned, durable, runtime, and records, and which owner tool regenerates derivatives.
  - Execution state: pending

### Task group 2: Complete help and compatibility surfaces

- [ ] E-04 Provide detailed help and examples for every new or materially changed layout command/flag, coordinated with concurrent general CLI-help work; keep positional ordering and unrelated help edits out of this Order unless required for conflict resolution.
  - Depends on: E-01
  - Expected outcome: `aw install`, context/path, storage/companion, migrate inventory/plan/apply/status/resume/rollback/cleanup, postcheck, and uninstall explain safety, defaults, outputs, and examples.
  - Execution state: pending

- [ ] E-05 Implement and document bounded legacy detection/read compatibility, deprecation status, unsupported-version behavior, current authoritative root, and the exact future removal gate; refuse silent mixed-layout operation.
  - Depends on: E-01
  - Expected outcome: Existing users receive actionable migration choices; compatibility cannot become an indefinite second writer or conceal partial migration.
  - Execution state: pending

### Task group 3: Prove every scenario and prepare release

- [ ] E-06 Finalize `tools/awphysical/migration-scenarios.json` as the closed acceptance manifest and bind every row to named automated tests, required deterministic tools, expected target/companion/source deltas, rollback result, and documentation section.
  - Depends on: E-01
  - Expected outcome: Scenario set equals test/evidence set; no row is silently skipped; adding/removing a claim requires updating the manifest.
  - Execution state: pending

- [ ] E-07 Execute the complete matrix from clean environments, including upgrades from representative legacy releases and agent-workflows self-migration, then run full tests, package inspection, sanitizer, indexes, parity, generated files, install/update/uninstall, rollback/resume, and postcheck.
  - Depends on: E-01
  - Expected outcome: Actual outputs and artifacts support every claim; failures return to the owning Order and block release.
  - Execution state: pending

- [ ] E-08 Prepare the major-version changelog/decision/release notes and compatibility warning, derive version through the existing release tooling, and stop at the explicit release-review human GO before any tag, push, GitHub release, or registry upload.
  - Depends on: E-01
  - Expected outcome: Release materials are complete and accurate, generated `VERSION` is not hand-edited, and no publication side effect occurs in this IPD without the repository's separate release gate.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 03 through 11 must be terminal and independently verified.
- User-facing prose must contain no em or en dashes.
- Generated indexes, adapters, version files, and package metadata are updated through owner tools.
- Tags, pushes, releases, and registry uploads require release-review Section 9 and explicit human GO.
- Concurrent CLI-help/order work owns general cleanup; this Order documents only new layout surfaces and coordinates shared files.

## Findings

- Current README and architecture documentation present `.agents/workflows` as canonical and describe a logical root model that does not match the approved physical design.
- A major path migration without scenario-bound docs and compatibility behavior would strand existing records or encourage unsafe deletion.
- The prior 25-scenario claim required an explicit scenario-to-test map; this Set uses a machine-readable closed manifest from the start.
- Package and source-repository behavior must be validated after actual self-migration, not inferred from fixtures alone.

## Proposed changes (ordered, validatable)

1. Rewrite the user model and exact preset/path/Git outcomes.
2. Add comprehensive migration and recovery guides.
3. Update contributor/source/package ownership documentation.
4. Complete new-command help with concurrent-work coordination.
5. Document and enforce bounded compatibility.
6. Bind every scenario to tests/evidence/docs.
7. Run the complete matrix and repository/package gates.
8. Prepare, but do not publish, a major release.

## Deferred / out of scope (with reason)

- Publishing, tagging, pushing, merging, and registry upload remain separate explicit release-review actions.
- Automatic remote creation or cleanup is not introduced.
- General exclusion-list and unrelated CLI-help work remain owned by their concurrent implementation.

## Scope check

- Over-scope: Documentation/help/compatibility/acceptance/release preparation only after implementation; no opportunistic feature work.
- Under-scope: All user types, presets, exact paths/Git, migration/recovery/cleanup, source development, compatibility, help, scenarios, self-migration, package/repository gates, privacy, and release boundary are included.

## Required tests / validation

- Scenario manifest schema and claim-set/test-set/evidence-set/documentation-set equality checks.
- Every command/example smoke-tested against the built package in isolated environments.
- `python3 -m unittest discover -s tests -t .` after final docs/generated changes.
- Package build, metadata/archive inspection, version derivation, and install smoke tests.
- Plans/specs/research indexes, adapter/entry-point parity, generated-file, sanitizer, migration compare/postcheck, rollback/resume, clean-target, and uninstall gates.
- Markdown/link/example/help snapshot checks.
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>` and orchestrator pre-transition lint.

## Spec / documentation sync

- Complete README, architecture, contributing, installation, migration, privacy, troubleshooting, source-development, and release documentation.
- Append implementation evidence/status through owner commands; do not rewrite historical decisions or executed plan bodies.
- Regenerate all owner-managed derivatives and verify clean index state.

## Open questions

No open questions. Publication remains blocked on the repository's explicit release-review human GO after all Set evidence is green.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: A documentation claim inventory maps every current path, preset, Git consequence, privacy/durability statement, migration phase, rollback/cleanup rule, and uninstall behavior to actual CLI output and an acceptance scenario, with no contradictory current-state legacy text.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Users can migrate without guessing command order or when legacy data is safe to remove; no guide tells users to push or delete automatically. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: Contributors know which files are source, generated, installed, human-owned, durable, runtime, and records, and which owner tool regenerates derivatives. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: `aw install`, context/path, storage/companion, migrate inventory/plan/apply/status/resume/rollback/cleanup, postcheck, and uninstall explain safety, defaults, outputs, and examples. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Existing users receive actionable migration choices; compatibility cannot become an indefinite second writer or conceal partial migration. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Scenario set equals test/evidence set; no row is silently skipped; adding/removing a claim requires updating the manifest. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-07: Actual outputs and artifacts support every claim; failures return to the owning Order and block release. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-08: Release materials are complete and accurate, generated `VERSION` is not hand-edited, and no publication side effect occurs in this IPD without the repository's separate release gate. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Documentation, help, compatibility, scenario evidence, and release preparation are one final truthfulness boundary after implementation.

Execution requires terminal verified Orders 03 through 11, a GO `/plan-review`, and human approval. Scope fence: current user/developer docs, new-layout help, bounded compatibility messaging/guards, scenario/evidence manifest, generated derivatives, acceptance/package gates, and release preparation. Coordinate shared help/parser files with concurrent work. Do not publish, tag, push, merge, upload, or delete retained legacy material. Paste actual outputs, path-scope commits, never broad-stage, and stop on any claim/evidence mismatch. Complete child and orchestrator pre-transition lint before moving this plan to `executed/`.
