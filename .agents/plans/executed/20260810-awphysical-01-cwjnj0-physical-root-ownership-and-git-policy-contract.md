# IPD: Physical root ownership and Git policy contract

- Date: 2026-08-10
- Kind: child
- Concern: Replace the logical-only four-root description with an exact physical hierarchy, internal durable/runtime boundaries, placement vocabulary, and Git-policy invariants.
- Scope: Controlling layout specification, architecture decisions, canonical schema vocabulary, contract tests, and fixtures only; no live migration or producer cutover.
- Status: executed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 1
- Highest E allocated: 06
- Author: Codex (GPT-5)
- Id: cwjnj0
- Approval: 2026-08-10 human maintainer (chat, after approving the controlling spec 20260810-1447-01) - approved to execute the awphysical Set; recorded by opencode Opus 4.8.

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created as the foundational contract for the corrective physical-layout Set.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): final cursory re-review after GPT-5.6 1544-01 closeout (0f6f238) - all 13 conforming at review-finalize, residuals closed (Order 01/02/05/06 canary fixtures, Order 04 path-equality-only, Order 07 test-module + per-fault, Order 09 clean_delta planted-write, Order 12 token->test binding), full suite 825 OK. Controlling spec 20260810-1447-01 advanced to reviewed. Set remains NO-GO pending HUMAN approval of the spec (the sole remaining gate); Status unchanged (reviewed).
- 2026-08-10 approved (human maintainer via chat, recorded by opencode Opus 4.8): controlling spec 20260810-1447-01 human-approved; Set cleared to execute. Status reviewed -> approved; OQ-01 resolved. Not yet executed.
- 2026-08-10 executed (Antigravity Agent): executed E-01..E-06, V-01..V-06 verified with full test suite passing.

## Goal

Define one unambiguous hierarchy that keeps AW-installed system content separate from human policy, durable operational facts, disposable runtime data, and workflow-created records. Make physical location and Git tracking explicit policy rather than consequences inferred from repository visibility.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Amend the normative model

- [x] E-01 Implement and verify the human-approved controlling layout specification so target-resident roots are physically `.aw/system/`, `.aw/config/`, `.aw/state/`, and `.aw/records/`, with `config/project.json`, `config/local.json`, `state/durable/`, and `state/runtime/` ownership and tracking rules defined explicitly.
  - Depends on: none
  - Expected outcome: The spec no longer permits tracked `system` to resolve permanently to `.agents/`; local config and runtime state are prohibited from Git; thin host adapters are the only allowed canonical-namespace exceptions.
  - Execution state: performed

- [x] E-02 Define the closed placement and Git-policy vocabulary for each root/class, including `target-tracked`, `target-ignored`, `home-untracked`, `companion-tracked`, `companion-untracked`, `source-checkout`, and explicitly validated custom paths.
  - Depends on: E-01
  - Expected outcome: Every supported placement has stated containment, ownership, commit destination, portability, durability, privacy, and clean-target consequences; invalid combinations are enumerated.
  - Execution state: performed

- [x] E-03 Define the four preset contracts: private-target durable tracking, public-target plus private companion, completely clean target, and local-only; define the advanced-custom constraints without making every low-level combination valid.
  - Depends on: E-01
  - Expected outcome: Each preset resolves every root/class and states exactly what is tracked in which Git repository, what is ignored, and what remains external.
  - Execution state: performed

### Task group 2: Encode and test the contract

- [x] E-04 Update `project_schema.py` with canonical enums/data structures for root class, placement, Git policy, project role, and preset, preserving a versioned compatibility parser for the prior schema.
  - Depends on: E-01
  - Expected outcome: Resolver, wizard, installer, migration, adapters, and tests can import one closed vocabulary; unknown future values fail with actionable errors rather than silently defaulting.
  - Execution state: performed

- [x] E-05 Add contract fixtures and exhaustive tests that map every valid preset and rejected combination to exact physical roots and permitted commit destinations, including path containment, symlink, case-collision, worktree, and Windows path forms.
  - Depends on: E-01
  - Expected outcome: The policy matrix is executable, complete, cross-platform aware, and cannot drift independently across consumers.
  - Execution state: performed

- [x] E-06 Verify D130 in `DECISIONS.md`, update terminology references, and run focused schema/spec checks without changing installer or migration behavior in this Order.
  - Depends on: E-01
  - Expected outcome: The decision record explains why durable/runtime and project/local config are split, why runtime is never tracked, and why source checkout is an explicit role.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The implemented logical-layout spec is preserved as superseded history. The new physical-layout spec is the only normative contract once human-approved; implementation does not rewrite either spec.
- User-facing prose must avoid em and en dashes; internal plan prose is exempt.
- Schema vocabulary is stdlib-only and imported, never duplicated as local string lists.
- A path being inside a private repository does not make locks, caches, backups, or local machine bindings suitable for Git.
- Spec traceability: E-01 through E-03 implement Sections 3 and 4; E-04/E-05 implement Sections 5 and 7; E-06 implements Sections 9 and 13.

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

- `python3 -m unittest tests.test_project_layout tests.test_project_context`
- New policy-matrix fixture test covering every supported and rejected combination.
- `python3 -m agent_workflows specs check --agent`
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`
- Scoped search proving no normative current-state text still maps tracked system to `.agents/`, excluding clearly labeled historical material.

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e01` | `tests/fixtures/awphysical/order01/e01-*`, including staged/tracked `config/local.json` and `state/runtime/` canaries | The spec no longer permits tracked `system` to resolve permanently to `.agents/`; `git ls-files`, staged-index, and policy-owner assertions prove local config and runtime state cannot enter any Git owner; thin host adapters are the only allowed canonical-namespace exceptions. | either planted canary remains tracked or staged, a policy permits either class to be tracked, `.agents/` remains a current system destination, or the expected rejection is absent |
| E-02 | `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e02` | `tests/fixtures/awphysical/order01/e02-*` | Every supported placement has stated containment, ownership, commit destination, portability, durability, privacy, and clean-target consequences; invalid combinations are enumerated. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e03` | `tests/fixtures/awphysical/order01/e03-*` | Each preset resolves every root/class and states exactly what is tracked in which Git repository, what is ignored, and what remains external. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e04` | `tests/fixtures/awphysical/order01/e04-*` | Resolver, wizard, installer, migration, adapters, and tests can import one closed vocabulary; unknown future values fail with actionable errors rather than silently defaulting. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e05` | `tests/fixtures/awphysical/order01/e05-*` | The policy matrix is executable, complete, cross-platform aware, and cannot drift independently across consumers. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e06` | `tests/fixtures/awphysical/order01/e06-*` | The decision record explains why durable/runtime and project/local config are split, why runtime is never tracked, and why source checkout is an explicit role. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Treat `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` as immutable approved input; if implementation reveals a design conflict, stop and return it to spec review rather than silently editing it.
- Verify D130 in `DECISIONS.md`; append a new decision only for a genuinely new human-approved architecture choice. Do not rewrite D126 through D129.
- Update schema documentation and fixture comments only where required by this Order.

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
  - Observed evidence: `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e01` returned exit status 0 (OK). Fixture `tests/fixtures/awphysical/order01/e01-canary.json` verified.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Run Evidence matrix row E-02 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e02` returned exit status 0 (OK). Fixture `tests/fixtures/awphysical/order01/e02-placements.json` verified.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Run Evidence matrix row E-03 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e03` returned exit status 0 (OK). Fixture `tests/fixtures/awphysical/order01/e03-presets.json` verified.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Run Evidence matrix row E-04 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e04` returned exit status 0 (OK). Fixture `tests/fixtures/awphysical/order01/e04-schema.json` verified. Enums RootClass, Placement, GitPolicy, ProjectRole, Preset validated.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Run Evidence matrix row E-05 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e05` returned exit status 0 (OK). Fixture `tests/fixtures/awphysical/order01/e05-matrix.json` verified.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: Run Evidence matrix row E-06 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence: `python3 -m unittest tests.test_project_layout.PhysicalPolicyMatrixTests.test_e06` returned exit status 0 (OK). Fixture `tests/fixtures/awphysical/order01/e06-decisions.json` and DECISIONS.md D130 verified.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: Physical hierarchy, ownership, placement vocabulary, presets, and schema fixtures are one foundational contract consumed by every later Order.

Execution requires a GO `/plan-review`, human approval of the controlling spec, and confirmation that concurrent CLI work does not overlap the scoped schema/spec files. Scope fence: only the controlling spec, append-only architecture decision, canonical schema vocabulary, and their focused tests/fixtures. Do not modify wizard, installer, migration, producer, adapter, exclusion-list, or CLI-help behavior. Paste actual runner output for every pass, commit only explicitly scoped paths with path-scoped Git commands, never broad-stage, and never push. On completion, satisfy pre-transition lint, append evidence, and move this plan to `executed/`.
