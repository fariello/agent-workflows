# IPD: Policy schema and deterministic context resolution

- Date: 2026-08-10
- Kind: child
- Concern: Make persisted placement and tracking policy complete, versioned, explainable, and deterministically resolved for every project role and preset.
- Scope: Policy file schemas, machine-local bindings, precedence/provenance, root resolution, context/path commands, compatibility parsing, and focused tests.
- Status: to-review
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 2
- Highest E allocated: 06
- Author: Codex (GPT-5)
- Id: sywony

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to replace default-derived pseudo-policy with explicit persisted and explainable project context.

## Goal

Give every AW invocation one pure resolver that returns exact physical roots, root classes, Git destinations, project role, policy provenance, accessibility, and migration state. A new repository must be distinguishable from a configured repository, and missing policy must never be silently represented as an existing saved choice.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Version and persist policy

- [ ] E-01 Implement a versioned portable project-policy schema for `.aw/config/project.json` and a separate machine-local binding schema outside tracked Git for local paths, companion attachment, runtime roots, and host-specific data.
  - Depends on: none
  - Expected outcome: Portable policy contains no machine-local absolute paths or secrets; local bindings identify the project durably and can be rebuilt or reattached safely.
  - Execution state: pending

- [ ] E-02 Add strict parsing, validation, atomic no-clobber merge, schema migration, unknown-key preservation rules, and explicit configured/unconfigured state rather than manufacturing an existing policy from built-in defaults.
  - Depends on: E-01
  - Expected outcome: Malformed, conflicting, unsafe, or future-version policy fails closed with source-specific diagnostics; human-owned permitted fields survive updates.
  - Execution state: pending

### Task group 2: Resolve complete context

- [ ] E-03 Refactor `project_context.py` to resolve Order 01 vocabulary through one precedence table and return physical root/class mappings, Git policies and commit destinations, project role, preset, durability, accessibility, migration phase, and provenance for every value.
  - Depends on: E-01
  - Expected outcome: The resolver is side-effect free, never prompts, does not infer repository privacy, and distinguishes absent policy, inherited defaults, explicit flags, local binding, portable project policy, profile, and global default.
  - Execution state: pending

- [ ] E-04 Add safe root-resolution primitives for canonicalization, symlinks, non-existing destinations, Git common-dir/worktrees, case normalization, filesystem boundaries, companion identity, and containment constraints.
  - Depends on: E-01
  - Expected outcome: Path traversal, ambiguous identity, unsafe overlap, target/companion aliasing, recursive placement, and clean-target containment violations fail before writes.
  - Execution state: pending

### Task group 3: Expose and prove the result

- [ ] E-05 Extend `aw context` and `aw path` human/JSON/agent output to show the resolved value, provenance, Git owner, tracking policy, accessibility, and configured/default status for every root class without leaking sensitive local values in public-safe modes.
  - Depends on: E-01
  - Expected outcome: Users and agents can predict exact writes and commits before installation; stable machine output supports wizard, migration, postcheck, and tests.
  - Execution state: pending

- [ ] E-06 Add table-driven precedence, round-trip, path-safety, worktree, source-checkout, compatibility, and public-output redaction tests, then update resolver documentation.
  - Depends on: E-01
  - Expected outcome: Every precedence edge and invalid path has a falsifiable test; the legacy policy parser is bounded and emits migration-required state rather than silently rewriting.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependency: Order 01 must be executed and verified first.
- `project_context.py` is a pure resolver and must not become a wizard or filesystem materializer.
- Global configuration follows the repository's XDG/AW_HOME rules; project-local absolute paths belong only in machine-local bindings.
- JSON output is a compatibility surface and requires an explicit schema version.

## Findings

- The current resolver maps tracked system to `.agents`, state to AW_HOME, and records according to one backend enum.
- `resolve_existing_policy()` treats successfully resolved built-in defaults as existing policy, so a first install may skip the full interview.
- Current policy does not represent root-class Git policy, source-checkout role, runtime placement, or a private companion containing config plus durable state plus records.
- Some root overrides exist only as unexposed machine-config fields and lack one complete persisted schema.

## Proposed changes (ordered, validatable)

1. Define portable and machine-local schema files and version transitions.
2. Implement configured-state detection and strict atomic policy I/O.
3. Refactor resolution onto the closed Order 01 vocabulary and a single precedence table.
4. Harden identity, path, worktree, symlink, and containment checks.
5. Expose full provenance and Git consequences through stable context/path output.
6. Add exhaustive fixtures and compatibility tests.

## Deferred / out of scope (with reason)

- Interactive policy collection is Order 03.
- Filesystem materialization and system copy are Order 04.
- Companion Git operations are Order 05.
- Migration mutation is Order 07.

## Scope check

- Over-scope: Resolver and policy I/O only; no prompts, Git initialization, remote changes, system installation, or record movement.
- Under-scope: Configured detection, versioning, portable/local split, precedence, provenance, project roles, complete roots, Git destinations, path safety, worktrees, redaction, compatibility, and machine output are included.

## Required tests / validation

- `python3 -m unittest tests.test_project_schema tests.test_project_context tests.test_config tests.test_project_registry`
- New table-driven policy-version, configured/unconfigured, precedence, path-safety, worktree, and source-role tests.
- CLI snapshots for `aw context --json`, `--agent`, and every `aw path <root-class>` surface.
- `python3 -m agent_workflows ipd lint --phase executor --agent <this-plan>`
- Full suite after integration with Order 01.

## Spec / documentation sync

- Update the controlling spec's policy schema, precedence, context output, and public-safe reporting sections.
- Update architecture documentation only through an append-only clarification if implementation forces a new decision.
- Document legacy schema compatibility and the migration-required state, without claiming migration has shipped in this Order.

## Open questions

No open questions. The resolver is deterministic and noninteractive; the wizard owns choices and persistence requests.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: Round-trip fixtures prove portable policy contains no local absolute paths, local bindings resolve the intended project, schema versions are explicit, and malformed/future versions fail without modifying either file.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-02: Malformed, conflicting, unsafe, or future-version policy fails closed with source-specific diagnostics; human-owned permitted fields survive updates. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-03: The resolver is side-effect free, never prompts, does not infer repository privacy, and distinguishes absent policy, inherited defaults, explicit flags, local binding, portable project policy, profile, and global default. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-04: Path traversal, ambiguous identity, unsafe overlap, target/companion aliasing, recursive placement, and clean-target containment violations fail before writes. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-05: Users and agents can predict exact writes and commits before installation; stable machine output supports wizard, migration, postcheck, and tests. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: A scoped diff, the exact focused commands named in this plan, and direct filesystem/Git/output assertions prove E-06: Every precedence edge and invalid path has a falsifiable test; the legacy policy parser is bounded and emits migration-required state rather than silently rewriting. Record actual exit codes and relevant output; fail this V item if any stated condition is absent, skipped, stale, or inferred only from prose.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Policy persistence, pure resolution, provenance, path safety, and context output are one deterministic API boundary for all later children.

Execution requires verified Order 01, a GO `/plan-review`, and human approval. Scope fence: policy/schema, resolver/context/path, config/registry primitives required by them, and focused tests/docs only. Do not implement wizard prompts, installer copies, companion Git, migration writes, repository exclusion behavior, or general CLI-help cleanup. Paste actual outputs, commit only path-scoped files, never broad-stage, and never push. Stop on any unresolved precedence, privacy, path, or identity ambiguity. Complete E/V evidence and pre-transition lint before moving the plan to `executed/`.
