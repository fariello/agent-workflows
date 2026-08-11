# IPD: Documentation release and end-to-end acceptance

- Date: 2026-08-10
- Kind: child
- Concern: Ship the physical-layout change as an honest major-version migration with complete user guidance, bounded compatibility, executable acceptance evidence, and no unsupported claims.
- Scope: User/developer documentation, CLI help for new layout surfaces, compatibility/deprecation messaging, release metadata and package gates, scenario manifest, end-to-end tests, final Set evidence, and release handoff.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 12
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: pszk6x

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created as the final documentation, compatibility, acceptance, and release boundary for the Set.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): final cursory re-review after GPT-5.6 1544-01 closeout (0f6f238) - all 13 conforming at review-finalize, residuals closed (Order 01/02/05/06 canary fixtures, Order 04 path-equality-only, Order 07 test-module + per-fault, Order 09 clean_delta planted-write, Order 12 token->test binding), full suite 825 OK. Controlling spec 20260810-1447-01 advanced to reviewed. Set remains NO-GO pending HUMAN approval of the spec (the sole remaining gate); Status unchanged (reviewed).

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

- [ ] E-05 Verify compatibility implementation owned by Orders 07/08, then document bounded legacy detection/read compatibility, deprecation status, unsupported-version behavior, current authoritative root, and the exact future removal gate; refuse silent mixed-layout operation.
  - Depends on: E-01
  - Expected outcome: Existing users receive actionable migration choices; compatibility cannot become an indefinite second writer or conceal partial migration.
  - Execution state: pending

### Task group 3: Prove every scenario and prepare release

- [ ] E-06 Finalize `tools/awphysical/migration-scenarios.json` as the closed 44-scenario acceptance manifest, require every `legacy_crosswalk` row 1 through 25 to name assertion tokens present in its cited scenarios, and add a machine-readable binding for every `expected` token to one or more fully qualified automated test methods plus a named assertion condition. Bind every scenario and crosswalk assertion to those tests, deterministic tools, expected target/companion/source deltas, rollback result, and documentation section; schema validation MUST load each named test and reject missing, stale, duplicate, or unbound tokens.
  - Depends on: E-01
  - Expected outcome: Scenario set equals test/evidence set; no row is silently skipped; adding/removing a claim requires updating the manifest.
  - Execution state: pending

- [ ] E-07 Execute the complete matrix from clean environments, including upgrades from representative legacy releases and agent-workflows self-migration, then run full tests, package inspection, sanitizer, indexes, parity, generated files, install/update/uninstall, rollback/resume, and postcheck.
  - Depends on: E-01
  - Expected outcome: Actual outputs and artifacts support every claim; failures return to the owning Order and block release.
  - Execution state: pending

- [ ] E-08 Rewrite the CHANGELOG 2.0 `Four logical roots` bullet and the citation to superseded spec `20260809-2211-01` to the physical contract, then prepare the major-version changelog/decision/release notes and compatibility warning, derive version through the existing release tooling without hand-editing `VERSION`, and follow bake/tag rungs in `RELEASING.md` and stop at the explicit release-review human GO before any tag, push, GitHub release, or registry upload.
  - Depends on: E-01
  - Expected outcome: Release materials are complete and accurate, generated `VERSION` is not hand-edited, and no publication side effect occurs in this IPD without the repository's separate release gate.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 03 through 11 must be terminal and independently verified.
- User-facing prose must contain no em or en dashes.
- Generated indexes, adapters, version files, and package metadata are updated through owner tools.
- Tags, pushes, releases, and registry uploads require release-review Section 9 and explicit human GO.
- Concurrent CLI-help/order work owns general cleanup; this Order documents only new layout surfaces and coordinates shared files.
- Spec traceability: E-01 through E-05 implement Sections 8, 11.3, and 12; E-06 implements Sections 12 and 13; E-07 implements Section 13; E-08 implements Sections 11.3, 13, and the release boundary.

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
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>` and orchestrator pre-transition lint.

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e01` | `tests/fixtures/awphysical/order12/e01-*` | Every example shows exact paths and Git consequences; local/runtime exclusions are explicit; public/private language is honest; old `.agents` canonical-layout text is limited to migration/history. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e02` | `tests/fixtures/awphysical/order12/e02-*` | Users can migrate without guessing command order or when legacy data is safe to remove; no guide tells users to push or delete automatically. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e03` | `tests/fixtures/awphysical/order12/e03-*` | Contributors know which files are source, generated, installed, human-owned, durable, runtime, and records, and which owner tool regenerates derivatives. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e04` | `tests/fixtures/awphysical/order12/e04-*` | `aw install`, context/path, storage/companion, migrate inventory/plan/apply/status/resume/rollback/cleanup, postcheck, and uninstall explain safety, defaults, outputs, and examples. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e05` | `tests/fixtures/awphysical/order12/e05-*` | Existing users receive actionable migration choices; compatibility cannot become an indefinite second writer or conceal partial migration. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tools.awphysical.test_awphysical_tools.ScenarioCatalogTests tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e06` | 44 scenarios, 25 legacy crosswalk rows, fully qualified test methods, named assertion conditions, and a deliberately missing/stale binding fixture | Scenario IDs equal test/evidence/doc scenario IDs; old IDs are exactly 1 through 25; every `expected` and crosswalk assertion token resolves to a loadable test method and named assertion condition; no row is skipped. | any set differs, a test method cannot be loaded, an assertion token is missing/stale/duplicate/unbound, the deliberately bad binding passes, parent ID alone is used as proof, or count differs |
| E-07 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e07` | `tests/fixtures/awphysical/order12/e07-*` | Actual outputs and artifacts support every claim; failures return to the owning Order and block release. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-08 | `python3 -m unittest tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e08` | `tests/fixtures/awphysical/order12/e08-*` | Release materials are complete and accurate, generated `VERSION` is not hand-edited, and no publication side effect occurs in this IPD without the repository's separate release gate. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Complete README, architecture, contributing, installation, migration, privacy, troubleshooting, source-development, and release documentation.
- Append implementation evidence/status through owner commands; do not rewrite historical decisions or executed plan bodies.
- Regenerate all owner-managed derivatives and verify clean index state.

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
- [ ] V-08 validates E-08
  - Required evidence: Run Evidence matrix row E-08 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Documentation, help, compatibility, scenario evidence, and release preparation are one final truthfulness boundary after implementation.

Execution requires terminal verified Orders 03 through 11, a GO `/plan-review`, and human approval. Scope fence: current user/developer docs, new-layout help, bounded compatibility messaging/guards, scenario/evidence manifest, generated derivatives, acceptance/package gates, and release preparation. Coordinate shared help/parser files with concurrent work. Do not publish, tag, push, merge, upload, or delete retained legacy material. Paste actual outputs, path-scope commits, never broad-stage, and stop on any claim/evidence mismatch. Complete child and orchestrator pre-transition lint before moving this plan to `executed/`.
