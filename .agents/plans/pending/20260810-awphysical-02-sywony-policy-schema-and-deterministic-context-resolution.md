# IPD: Policy schema and deterministic context resolution

- Date: 2026-08-10
- Kind: child
- Concern: Make persisted placement and tracking policy complete, versioned, explainable, and deterministically resolved for every project role and preset.
- Scope: Policy file schemas, machine-local bindings, precedence/provenance, root resolution, context/path commands, compatibility parsing, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 2
- Highest E allocated: 06
- Author: Codex (GPT-5)
- Id: sywony

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to replace default-derived pseudo-policy with explicit persisted and explainable project context.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.

## Goal

Give every AW invocation one pure resolver that returns exact physical roots, root classes, Git destinations, project role, policy provenance, accessibility, and migration state. A new repository must be distinguishable from a configured repository, and missing policy must never be silently represented as an existing saved choice.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Version and persist policy

- [ ] E-01 Implement a versioned portable project-policy schema for `.aw/config/project.json`, the Section 10 durability enum and `durable-private` input alias, and a separate machine-local binding schema outside tracked Git for local paths, companion attachment, runtime roots, and host-specific data.
  - Depends on: none
  - Expected outcome: Portable policy contains no machine-local absolute paths or secrets; local bindings identify the project durably and can be rebuilt or reattached safely.
  - Execution state: pending

- [ ] E-02 Add strict parsing, validation, atomic no-clobber merge, schema migration, unknown-key preservation rules, and explicit configured/unconfigured state rather than manufacturing an existing policy from built-in defaults. Migrate the shipped or legacy `.aw/config/config.json` by placing portable fields in `config/project.json` and absolute paths, aliases, attachment, runtime, and other machine-local fields in untracked `config/local.json`; preserve and block on conflicts or unknowns.
  - Depends on: E-01
  - Expected outcome: Malformed, conflicting, unsafe, or future-version policy fails closed with source-specific diagnostics; human-owned permitted fields survive updates.
  - Execution state: pending

### Task group 2: Resolve complete context

- [ ] E-03 Refactor `project_context.py` to resolve Order 01 vocabulary through one precedence table and return physical root/class mappings, Git policies and commit destinations, project role, preset, durability, accessibility, migration phase, and provenance for every value.
  - Depends on: E-01
  - Expected outcome: The resolver is side-effect free, never prompts, does not infer repository privacy, and distinguishes absent policy from configured policy while preserving the existing six `PrecedenceLevel` values: explicit flags, machine-local binding, portable project policy, named profile, global defaults, and built-in defaults.
  - Execution state: pending

- [ ] E-04 Extend and harden the existing `_canonical_path`, `_is_safe_subpath`, and `_check_path_security` primitives for non-existing destinations, symlink escape, Git common-dir/worktrees, case normalization, filesystem boundaries, companion identity, and containment constraints; do not create a second path-safety stack.
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
- Spec traceability: E-01/E-02 implement Sections 4.2 and 10; E-03 through E-06 implement Sections 5, 7, and 13. Coordinate the shared durability schema with Order 05 before either Order commits.

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

- `python3 -m unittest tests.test_project_layout tests.test_project_context tests.test_storage`
- New table-driven policy-version, configured/unconfigured, precedence, path-safety, worktree, and source-role tests.
- CLI snapshots for `aw context --json`, `--agent`, and every `aw path <root-class>` surface.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`
- Full suite after integration with Order 01.

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_project_context.PhysicalContextResolutionTests.test_e01` | `tests/fixtures/awphysical/order02/e01-*` | Portable policy contains no machine-local absolute paths or secrets; local bindings identify the project durably and can be rebuilt or reattached safely. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_project_context.PhysicalContextResolutionTests.test_e02` | `tests/fixtures/awphysical/order02/e02-*` | Legacy `.aw/config/config.json` is split into portable `project.json` and untracked `local.json`; malformed, conflicting, unknown, unsafe, or future-version data fails closed and remains preserved; human-owned permitted fields survive updates. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_project_context.PhysicalContextResolutionTests.test_e03` | `tests/fixtures/awphysical/order02/e03-*` | The resolver is side-effect free, never prompts, does not infer repository privacy, and distinguishes absent policy from configured policy while preserving the existing six `PrecedenceLevel` values: explicit flags, machine-local binding, portable project policy, named profile, global defaults, and built-in defaults. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_project_context.PhysicalContextResolutionTests.test_e04` | `tests/fixtures/awphysical/order02/e04-*` | Path traversal, ambiguous identity, unsafe overlap, target/companion aliasing, recursive placement, and clean-target containment violations fail before writes. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_project_context.PhysicalContextResolutionTests.test_e05` | `tests/fixtures/awphysical/order02/e05-*` | Users and agents can predict exact writes and commits before installation; stable machine output supports wizard, migration, postcheck, and tests. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_project_context.PhysicalContextResolutionTests.test_e06` | `tests/fixtures/awphysical/order02/e06-*` | Every precedence edge and invalid path has a falsifiable test; the legacy policy parser is bounded and emits migration-required state rather than silently rewriting. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Verify implementation against the controlling specification's policy schema, precedence, context output, and public-safe reporting sections. If implementation conflicts, stop and return the specification to review rather than silently editing approved requirements.
- Update architecture documentation only through an append-only clarification if implementation forces a new decision.
- Document legacy schema compatibility and the migration-required state, without claiming migration has shipped in this Order.

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


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Policy persistence, pure resolution, provenance, path safety, and context output are one deterministic API boundary for all later children.

Execution requires verified Order 01, a GO `/plan-review`, and human approval. Scope fence: policy/schema, resolver/context/path, config/registry primitives required by them, and focused tests/docs only. Do not implement wizard prompts, installer copies, companion Git, migration writes, repository exclusion behavior, or general CLI-help cleanup. Paste actual outputs, commit only path-scoped files, never broad-stage, and never push. Stop on any unresolved precedence, privacy, path, or identity ambiguity. Complete E/V evidence and pre-transition lint before moving the plan to `executed/`.
