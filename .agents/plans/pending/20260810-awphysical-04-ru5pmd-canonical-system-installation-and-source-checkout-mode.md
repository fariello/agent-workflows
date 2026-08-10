# IPD: Canonical system installation and source-checkout mode

- Date: 2026-08-10
- Kind: child
- Concern: Move canonical installed framework content from `.agents/` into `.aw/system/` while protecting the agent-workflows source checkout from self-overwrite or duplicate sources.
- Scope: Packaged system-source layout, installer/materializer transaction, manifests, versioning, adapters' source inputs, source-checkout detection/protection, install/update/uninstall behavior, and focused tests.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 4
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: ru5pmd

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created to make `.aw/system/` the physical canonical system root and give the source repository a safe explicit role.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.

## Goal

Install all AW-owned workflow bodies, tools, templates, manifests, and version data beneath the resolved system root, never mixed with mutable project records. In the framework source repository, use an explicit source-checkout provider that remains developer-owned and cannot be overwritten by `aw install`.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Establish one distributable system source

- [ ] E-01 Define and implement the canonical source tree and package-resource resolver for system content, moving workflow distribution sources from `.agents/workflows/` to `.aw/system/` or another approved source path that materializes exactly as `.aw/system/` in ordinary targets.
  - Depends on: none
  - Expected outcome: Wheel, sdist, source checkout, installer, tests, and generated adapters consume one manifest-backed source; no duplicate normative workflow tree exists.
  - Execution state: pending

- [ ] E-02 Update `pyproject.toml`, `agent_workflows/_compat.py` `_DATA_RELATIVE`, `versioning.py`, `hatch_build.py`, and manifest/resource lookup so packaged installs are location-independent, stdlib-only at runtime, deterministic, and reject incomplete or mixed-version system sources.
  - Depends on: E-01
  - Expected outcome: Package inspection proves every required system file is present once, development-only records are absent, and version/manifest hashes agree.
  - Execution state: pending

### Task group 2: Install and update atomically

- [ ] E-03 Integrate Order 02 context and Order 03 confirmed policy with the real install path, staging a complete candidate system tree, validating it, pivoting atomically where supported, and recording manifest/state only after success.
  - Depends on: E-01
  - Expected outcome: Tracked targets receive `.aw/system/`; external-system modes write only to their resolved external root; partial updates cannot become authoritative; failed validation rolls back.
  - Execution state: pending

- [ ] E-04 Move installer backups, transaction scratch, locks, and recovery data into `state/runtime/`; keep durable install snapshot/history in `state/durable/`; enforce no writes to config or records during system refresh.
  - Depends on: E-01
  - Expected outcome: System updates do not pollute repository root, tracked durable state, or records with transient data, and rollback artifacts are excluded from Git.
  - Execution state: pending

### Task group 3: Protect source checkouts and ownership

- [ ] E-05 Implement positive structurally evidenced source-checkout detection reusing the existing `engine.py` `is_self` mechanism and an explicit `source-checkout` project role; refuse any installer operation that would overwrite developer-owned canonical source, and resolve the system provider without creating a duplicate installed copy.
  - Depends on: E-01
  - Expected outcome: The agent-workflows repository can dogfood its own workflows; copied lookalike files cannot spoof source role; source edits remain ordinary project changes and system update reports an actionable source-mode result.
  - Execution state: pending

- [ ] E-06 Update conservative uninstall and ownership checks so ordinary targets remove only manifest-owned system files and adapters, source checkouts never remove canonical source, and config/state/records remain unless separately requested.
  - Depends on: E-01
  - Expected outcome: Modified human files, foreign files, source content, durable state, and records are preserved with explicit reports.
  - Execution state: pending

### Task group 4: Characterize and verify

- [ ] E-07 Add fresh, update, no-op, corrupt-candidate, interrupted-pivot, rollback, tracked/external, source-checkout, spoofed-source, package, uninstall, and no-cross-root-write tests; update system path references owned by this Order.
  - Depends on: E-01
  - Expected outcome: Every install mode has exact filesystem, manifest, state, Git-index, and exit-code assertions, including Windows fallback semantics where atomic directory replacement differs.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Set dependencies: Orders 01 and 02 must be verified; coordinate the policy handoff with Order 03.
- System content is CLI-owned in installed targets but developer-owned in a verified source checkout.
- Generated adapters contain no normative workflow copy and are completed in Order 09.
- Do not hand-edit generated `VERSION`; use the existing owner tooling adapted to the new source root.
- Spec traceability: E-01/E-02 implement Sections 4.1 and 9; E-03/E-04 implement Sections 7 and 9; E-05/E-06 implement Section 9; E-07 implements Sections 9 and 13.

## Findings

- The current installer hard-codes `.agents/workflows` and writes repository-root backup directories.
- `materialize_project_layout()` is not integrated with the production install path.
- The source repository currently stores canonical workflows in the same legacy tree also used for its plans/docs/comms records.
- A naive self-install would either overwrite source or duplicate the workflow tree.

## Proposed changes (ordered, validatable)

1. Establish one canonical packaged system source and manifest.
2. Adapt version/build/resource resolution.
3. Integrate policy, materialization, staged validation, pivot, and durable publication.
4. Route transient and durable install state correctly.
5. Implement protected source-checkout role.
6. Harden uninstall and ownership.
7. Add complete install/package/source-role characterization.

## Deferred / out of scope (with reason)

- Legacy data migration is Orders 06 and 07.
- Producer routing is Order 08.
- Final host adapter cutover is Order 09.
- The actual agent-workflows self-migration is Order 11.

## Scope check

- Over-scope: System distribution/install/update/uninstall and source role only; no records migration, companion remote setup, or release.
- Under-scope: Packaging, manifests, versions, transaction state placement, atomicity/fallback, source verification, spoofing, tracked/external modes, ownership, rollback, uninstall, and cross-platform behavior are covered.

## Required tests / validation

- `python3 -m unittest tests.test_installer tests.test_project_layout tests.test_packaging tests.test_versioning`
- Positive source-checkout, copied-marker spoof, wrong-origin, and ambiguous-evidence fixtures with no-write assertions.
- Wheel and sdist build plus archive-content and installed-resource inspection.
- Fresh/update/failure filesystem and Git-index snapshots for tracked and external system roots.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`
- Full suite after final path-reference adaptation owned by this Order.

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e01` | `tests/fixtures/awphysical/order04/e01-*` | Wheel, sdist, source checkout, installer, tests, and generated adapters consume one manifest-backed source; no duplicate normative workflow tree exists. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-02 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e02` | `tests/fixtures/awphysical/order04/e02-*` | Package inspection proves every required system file is present once, development-only records are absent, and version/manifest hashes agree. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-03 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e03` | `tests/fixtures/awphysical/order04/e03-*` | Tracked targets receive `.aw/system/`; external-system modes write only to their resolved external root; partial updates cannot become authoritative; failed validation rolls back. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e04` | `tests/fixtures/awphysical/order04/e04-*` | System updates do not pollute repository root, tracked durable state, or records with transient data, and rollback artifacts are excluded from Git. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e05` | `source-positive`, `copied-marker-spoof`, `origin-only-spoof`, `ambiguous-source-evidence` | Positive source fixture resolves source role and produces zero canonical-source writes; both spoof fixtures remain ordinary targets or refuse; ambiguous evidence fails closed; before/after source hashes and Git index are identical in every case. | any source byte/index changes, a spoof gains source role, ambiguity proceeds, or an expected exit code differs |
| E-06 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e06` | `tests/fixtures/awphysical/order04/e06-*` | Modified human files, foreign files, source content, durable state, and records are preserved with explicit reports. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-07 | `python3 -m unittest tests.test_installer.PhysicalSystemInstallTests.test_e07` | named modes: `fresh-tracked`, `fresh-external`, `update`, `same-version`, `corrupt-candidate`, `interrupted-pivot`, `rollback`, `source-positive`, `source-spoof`, `wheel`, `uninstall`, `windows-fallback` | Each mode asserts exact exit, authority, manifest digest, filesystem delta, state delta, and Git-index delta; Windows fallback proves journaled copy/switch/rollback without assuming POSIX directory replacement. | any named mode is absent, an unexpected root/index changes, failure becomes authoritative, or fallback cannot resume/rollback |

## Spec / documentation sync

- Verify implementation against the controlling specification's system ownership, source provider, transaction, packaging, uninstall, and source-checkout sections. If implementation conflicts, stop and return the specification to review rather than silently editing approved requirements.
- Update internal developer documentation for canonical system sources and regeneration commands.
- Do not publish end-user migration instructions before Order 12.

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
- Cohesion rationale: Canonical source, package resources, installation transaction, source-role protection, and uninstall share one ownership manifest and must change together.

Execution requires verified Orders 01/02, coordination with Order 03, a GO `/plan-review`, and human approval. Scope fence: canonical system sources, package/build/resource logic, installer/materializer/version/manifest/uninstall paths, source-role detection, and focused tests/docs. Do not migrate records, change companion remotes, alter exclusion behavior, or perform the final source-repository migration. Paste actual outputs, path-scope commits, never broad-stage, never push, and stop if source ownership or rollback is ambiguous. Complete evidence and lint before moving this plan to `executed/`.
