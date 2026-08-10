# IPD: Record producers and legacy reference cutover

- Date: 2026-08-10
- Kind: child
- Concern: Route every AW record/state producer and consumer through resolved physical roots so no workflow recreates or trusts the legacy hierarchy after migration.
- Scope: Record-class router, producer and reader integrations, plans/specs/research/prompts/comms/runs/actions/history/index/attention surfaces, compatibility readers, forbidden-write guard, generated workflow text, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 8
- Highest E allocated: 08
- Author: Codex (GPT-5)
- Id: mb9xn2

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to complete the writer cutover and prevent post-migration legacy-tree regeneration.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.

## Goal

Make the Order 02 context resolver and a single record-class router authoritative for all AW-created records and durable state. Preserve bounded read compatibility during migration, but permit exactly one write destination and fail closed when context or migration authority is invalid.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Complete the routing API

- [ ] E-01 Extend the canonical router with closed record and durable-state classes, safe path construction, lifecycle-aware destinations, permitted Git owner, tracking policy, migration authority, and public-safe logical path rendering.
  - Depends on: none
  - Expected outcome: Producers cannot pass arbitrary relative paths, escape roots, mix records with state, or stage against the wrong repository; unsupported classes fail explicitly.
  - Execution state: pending

- [ ] E-02 Add a centralized write guard that rejects legacy destinations, unresolved/inaccessible roots, active pre-switch migrations, stale context, unsafe symlinks, cross-Git staging, and writes into installed system or runtime from record producers.
  - Depends on: E-01
  - Expected outcome: A literal or indirect legacy write raises before any file, directory, index, or status mutation; post-switch compatibility readers cannot become writers.
  - Execution state: pending

### Task group 2: Cut over all producers and consumers

- [ ] E-03 Re-derive the closed writer and reader inventory from code, including `ipd_authoring.run_scaffold`, `research_cmd.plan_new*`, `specs._set_status`, `artifact_core` write/move helpers, plan/research index/archive/ref owners, `attention*`, and `engine.py` scaffolders; do not trust current `record_producers.PRODUCER_INVENTORY` anchors. Remove every genuine writer from `LEGACY_ALLOWLIST`, require code-discovery source/anchor set equality with the manifest and tests, then migrate those producers and consumers to router-owned paths while preserving lifecycle identity and Git destinations.
  - Depends on: E-01
  - Expected outcome: Every producing CLI/workflow returns the actual resolved destination and commits/stages only where policy permits; repository and external backends behave equivalently apart from Git owner.
  - Execution state: pending

- [ ] E-04 Migrate actions, install snapshots/history, routing receipts, migration durable receipts, and other operational writers into `state/durable/`; route locks, transactions, backups, caches, and temporary output into `state/runtime/` with enforced ignore/no-stage rules.
  - Depends on: E-01
  - Expected outcome: Durable state remains inspectable and optionally trackable; runtime data never enters a Git index or records tree.
  - Execution state: pending

- [ ] E-05 Update read-side indexes, `aw attention`, `/whatnext`, workflow discovery, status, history, archive, ref checks, and other consumers to use resolver/router discovery and non-repo-relative logical item paths safely.
  - Depends on: E-01
  - Expected outcome: External records/state work without fake repo-relative paths; D125 remains the one attention projection; failure is explicit and public-safe.
  - Execution state: pending

### Task group 3: Bound compatibility and prove no legacy writes

- [ ] E-06 Replace the unenforced `LEGACY_ALLOWLIST` claim with an enforced closed compatibility-reader catalog, then implement a read-only compatibility adapter for retained legacy data, enabled only by migration state and time/version bound, with duplicate-authority detection and explicit deprecation output.
  - Depends on: E-01
  - Expected outcome: Old content remains readable during retention, but new writes cannot target it and ambiguous new/old duplicates invalidate the view.
  - Execution state: pending

- [ ] E-07 Update canonical workflow bodies/templates and generated derivatives to request paths through `aw context`/router surfaces instead of hard-coded `.agents` or `workflow-artifacts`; add a static no-legacy-write-sink guard over the closed producer source set plus a semantic planted indirect/literal writer audit rather than an impossible blanket text grep.
  - Depends on: E-01
  - Expected outcome: Legitimate historical/docs references remain allowed, while executable producers and instructions cannot write to forbidden paths.
  - Execution state: pending

- [ ] E-08 Add one end-to-end test per producer/consumer class across repository, home, companion, clean-target, migration-retention, inaccessible-root, wrong-Git, and state/records-confusion cases.
  - Depends on: E-01
  - Expected outcome: The producer/consumer inventory equals the test inventory, and filesystem/Git assertions prove one authoritative destination with no legacy recreation.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 02, 06, and 07 must be verified before switching writers.
- `aw attention` remains the only cross-tree attention projection and stays read-only.
- Plans/research/spec indexes are owner-generated and must be regenerated through their commands.
- Literal legacy-path references in historical evidence are not defects; executable write surfaces are the guarded set.
- Spec traceability: E-01/E-02 implement Sections 4.3, 4.4, and 11.2; E-03 through E-05 implement Sections 6 and 8; E-06/E-07 implement Section 11.3; E-08 implements Section 13.

## Findings

- Existing workflow bodies and tools contain many `.agents/...` and `workflow-artifacts/...` paths.
- A literal zero-match grep cannot distinguish legitimate history/read compatibility from active producers.
- Current records routing exists but legacy producers and state writers are not comprehensively integrated.
- External action and attention paths already require special non-repo-relative handling that must generalize safely.

## Proposed changes (ordered, validatable)

1. Complete closed router classes and safe path construction.
2. Enforce one write authority and Git owner.
3. Cut over every record producer.
4. Separate durable and runtime state writers.
5. Cut over all readers/indexes/attention consumers.
6. Add bounded read-only legacy compatibility.
7. Regenerate workflow instructions and add semantic forbidden-write audit.
8. Prove every producer/consumer across all placements.

## Deferred / out of scope (with reason)

- Host adapter path generation is Order 09.
- Migration copy/switch mechanics are Order 07.
- Final legacy cleanup is separately gated after Order 10.
- General workflow behavior unrelated to path/routing is out of scope.

## Scope check

- Over-scope: Path resolution, writing, reading, indexing, and instructions only; no unrelated workflow redesign.
- Under-scope: All record classes, durable/runtime state, every producer/consumer, Git owners, attention, compatibility, generated text, forbidden writes, external roots, and failure states are included.

## Required tests / validation

- Existing plans, specs, research, attention, actions, comms, archive, record-routing, and workflow-contract suites.
- New producer/consumer manifest assertion: declared source set equals exercised test set.
- End-to-end filesystem and separate Git-index assertions for every placement preset.
- Semantic forbidden-write audit with planted indirect/literal legacy writers and allowed historical references.
- `python3 -m agent_workflows plans index --check --agent` and corresponding specs/research checks.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e01` | `tests/fixtures/awphysical/order08/e01-*` | Producers cannot pass arbitrary relative paths, escape roots, mix records with state, or stage against the wrong repository; unsupported classes fail explicitly. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e02` | `tests/fixtures/awphysical/order08/e02-*` | A literal or indirect legacy write raises before any file, directory, index, or status mutation; post-switch compatibility readers cannot become writers. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_record_producer_inventory tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e03` | `code-discovery-parity`, `stale-anchor`, `undeclared-writer`, `writer-in-allowlist` | Discovered writer/reader sources and anchors equal manifest and exercised-test sets; stale anchors, undeclared writers, and any writing allowlist member fail before routing assertions. | any set differs, any anchor is absent, any genuine writer remains allowlisted, or a negative fixture passes |
| E-04 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e04` | `tests/fixtures/awphysical/order08/e04-*` | Durable state remains inspectable and optionally trackable; runtime data never enters a Git index or records tree. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e05` | `tests/fixtures/awphysical/order08/e05-*` | External records/state work without fake repo-relative paths; D125 remains the one attention projection; failure is explicit and public-safe. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e06` | `tests/fixtures/awphysical/order08/e06-*` | Old content remains readable during retention, but new writes cannot target it and ambiguous new/old duplicates invalidate the view. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e07` | `clean-producer-set`, `literal-legacy-writer`, `indirect-legacy-writer`, `historical-reference-reader` | Static sink guard finds zero legacy writers after cutover; literal and indirect planted writers fail; the read-only historical reference remains allowed. | a planted writer passes, clean source reports a sink, or allowed history is rejected |
| E-08 | `python3 -m unittest tests.test_awphysical_routing.PhysicalProducerRoutingTests.test_e08` | named backends/failures: `repository`, `home`, `companion`, `clean-target`, `retention-reader`, `inaccessible-root`, `wrong-git`, `state-records-confusion` | For every discovered producer class, each applicable fixture asserts one observed output beneath the resolved class, exact Git owner/index delta, no legacy recreation, and expected exit; manifest producer set equals exercised producer set. | any producer/backend pair is unexercised, output or Git owner differs, legacy path appears, or a negative fixture succeeds |

## Spec / documentation sync

- Verify implementation against the controlling specification's producing-workflow, state-class, attention, compatibility, and path-rendering requirements. Stop and return the specification to review on conflict.
- Regenerate all owner-managed workflow indexes and host-source templates touched by source path changes.
- Do not hand-edit generated shims; Order 09 owns their final regeneration.

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
- Cohesion rationale: Router, writers, readers, compatibility, generated instructions, and exhaustive producer tests must cut over together to prevent split authority.

Execution requires verified Orders 02/06/07, a GO `/plan-review`, and human approval. Scope fence: router, listed producers/readers/indexes/attention/state writers, canonical workflow path instructions, semantic audit, and focused tests/docs. Do not change unrelated workflow semantics, host adapters, migration copy engine, exclusion policy, or CLI help outside owned commands. Paste actual outputs, path-scope commits, never broad-stage, never push, and stop if any producer lacks an authoritative class or Git owner. Complete evidence and lint before moving this plan to `executed/`.
