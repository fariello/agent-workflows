# IPD: Physical .aw hierarchy and migration orchestrator

- Date: 2026-08-10
- Kind: orchestrator
- Concern: Replace the partially logical legacy layout with a physically compartmentalized `.aw/` model, complete placement and Git-policy choices, and a loss-resistant migration for agent-workflows and every installed project.
- Scope: Orders 01 through 12 of Set `awphysical`, their shared contract, dependency gates, migration safety, source-repository adoption, independent postcheck, documentation, and release evidence.
- Status: reviewed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 0
- Highest E allocated: 14
- Author: Codex (GPT-5)
- Id: rma3j4

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created after maintainer approval of the refined hierarchy, including durable/runtime state separation and a source-checkout role.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.

## Goal

Deliver one coherent major-version cutover in which canonical AW material is physically separated into `system`, `config`, `state`, and `records`, every durable placement and Git consequence is chosen and previewed, and legacy projects can migrate without losing or silently exposing information. The Set must work both for ordinary target repositories and for the agent-workflows source repository itself.

Spec traceability: E-01 controls Sections 3 through 15; E-02 through E-10 delegate the corresponding child-owned sections; E-11/E-12 enforce Sections 11 and 13; E-13/E-14 enforce Sections 12, 13, and the release boundary.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Freeze the cross-Set contract

- [ ] E-01 Obtain human approval of the superseding physical-layout specification and record the exact cross-Set invariants, root vocabulary, preset semantics, compatibility window, and release boundary that every child must implement.
  - Depends on: none
  - Expected outcome: No child begins implementation against an ambiguous logical-only hierarchy; the approved spec explicitly distinguishes portable config from local config and durable state from runtime state.
  - Execution state: pending

### Task group 2: Execute the foundational contract and resolver

- [ ] E-02 Execute Order 01 and independently verify the physical root, ownership, tracking, source-checkout, and Git-boundary contract.
  - Depends on: E-01
  - Expected outcome: One normative mapping governs target, home, companion, clean-target, and source-checkout placements.
  - Execution state: pending

- [ ] E-03 Execute Order 02 and independently verify the versioned policy schema, precedence, provenance, path safety, and pure resolver.
  - Depends on: E-02
  - Expected outcome: `aw context` can explain every resolved path and tracking destination without reading prose or prompting.
  - Execution state: pending

### Task group 3: Execute configuration and installation surfaces

- [ ] E-04 Execute Order 03 and independently verify all wizard presets, custom choices, update review, persistence, accessibility, and noninteractive parity.
  - Depends on: E-02, E-03
  - Expected outcome: Users can select all-in-private-target, public-plus-private-companion, clean-target, local-only, or safe custom placement with an exact pre-write preview.
  - Execution state: pending

- [ ] E-05 Execute Order 04 and independently verify canonical `.aw/system/` installation, atomic update, manifest ownership, packaging, and protected source-checkout behavior.
  - Depends on: E-02, E-03
  - Expected outcome: Installed system content is isolated from mutable config, state, and records, while the framework source repository remains editable and cannot be overwritten by self-install.
  - Execution state: pending

- [ ] E-06 Execute Order 05 and independently verify companion selection, identity attachment, Git initialization, durability reporting, and privacy-honest remote acknowledgement.
  - Depends on: E-02, E-03, E-04
  - Expected outcome: A public target can keep candid durable material in an explicitly selected private companion without storing machine paths or private content in the public repository.
  - Execution state: pending

### Task group 4: Execute migration machinery and cutover

- [ ] E-07 Execute Order 06 and independently verify complete legacy inventory, deterministic classification, migration mapping, hash manifests, and collision/preflight reporting.
  - Depends on: E-02, E-03
  - Expected outcome: Every legacy file is known before mutation, including tracked, untracked, ignored, symlinked, external, and cross-Git-boundary material.
  - Execution state: pending

- [ ] E-08 Execute Order 07 and independently verify copy-verify-switch-retain migration, resume, rollback, cross-repository commit boundaries, and explicit cleanup.
  - Depends on: E-03, E-05, E-06, E-07
  - Expected outcome: Interruption or failure cannot produce two authoritative writers or a success claim with missing or changed content.
  - Execution state: pending

- [ ] E-09 Execute Order 08 and independently verify every record producer, reader, index, attention source, workflow instruction, and legacy compatibility reader against resolved roots.
  - Depends on: E-03, E-07, E-08
  - Expected outcome: New writes use exactly one resolved destination and no producing workflow silently recreates a legacy tree.
  - Execution state: pending

- [ ] E-10 Execute Order 09 and independently verify thin host adapters, root pointers, generated shims, source ownership, clean-target discovery, uninstall, and zero-target-delta proof.
  - Depends on: E-03, E-05, E-08, E-09
  - Expected outcome: Host-required exceptions contain no canonical logic or records, and clean-target mode leaves no AW-owned target files.
  - Execution state: pending

### Task group 5: Audit, dogfood, and release

- [ ] E-11 Execute Order 10 and independently verify the deterministic postcheck plus fresh-agent follow-up review against successful, partial, interrupted, and deceptive fixtures.
  - Depends on: E-07, E-08, E-09, E-10
  - Expected outcome: Migration completion depends on independently reproduced evidence, not the migrator's own summary.
  - Execution state: pending

- [ ] E-12 Execute Order 11 and independently migrate the agent-workflows repository, verifying source-checkout protection and preservation of its existing plans, specifications, research, prompts, communications, and history.
  - Depends on: E-05, E-06, E-07, E-08, E-09, E-10, E-11
  - Expected outcome: The source repository dogfoods the same policy and migration machinery without duplicating or overwriting canonical framework source.
  - Execution state: pending

- [ ] E-13 Execute Order 12 and independently verify documentation, compatibility messaging, upgrade/release behavior, and the complete acceptance scenario matrix.
  - Depends on: E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-11, E-12
  - Expected outcome: User guidance, CLI help, schemas, examples, generated material, tests, and release metadata describe one behavior and every named scenario has executable evidence.
  - Execution state: pending

- [ ] E-14 Perform the whole-Set closeout from a clean checkout, compare the implementation and evidence sets, run the complete regression and package gates, and record any intentionally retained legacy material plus its removal trigger.
  - Depends on: E-13
  - Expected outcome: Claim set equals evidence set; all children are terminal and conforming; no legacy writer remains; rollback and retention evidence exist; no release, tag, push, or cleanup occurs without its separate human gate.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | Id | What it does | Set dependencies |
|---:|---|---|---|
| 01 | `cwjnj0` | Physical hierarchy, ownership, tracking, and normative policy matrix | approved spec |
| 02 | `sywony` | Versioned policy schema and deterministic context resolver | 01 |
| 03 | `x2dfen` | Interactive presets, advanced placement, persistence, update checkpoint | 01, 02 |
| 04 | `ru5pmd` | Canonical system installation, packaging, atomic updates, source-checkout role | 01, 02 |
| 05 | `1e9ggw` | Companion identity, Git/durability handling, private-storage safeguards | 01, 02, 03 |
| 06 | `fcgala` | Read-only legacy inventory, classification, hash manifest, migration map | 01, 02 |
| 07 | `nhv0qm` | Transactional migration, resume, rollback, retention, cleanup planning | 02, 04, 05, 06 |
| 08 | `mb9xn2` | Producer/reader routing, legacy compatibility, indexes and attention | 02, 06, 07 |
| 09 | `2e2jrw` | Thin host adapters, clean-target integration, uninstall | 02, 04, 07, 08 |
| 10 | `n3fz8b` | Independent deterministic postcheck and skeptical agent follow-up | 06, 07, 08, 09 |
| 11 | `g5zl1u` | agent-workflows source-repository self-migration | 04 through 10 |
| 12 | `pszk6x` | Documentation, compatibility, release, acceptance matrix | 03 through 11 |

Orders may be implemented in parallel only when all listed dependencies are terminal and independently verified. Order 07 is the first mutation-capable migration order; Orders 01 through 06 must not migrate a live repository.

## Completion criteria (the whole Set is done only when)

- The canonical target hierarchy is physically `.aw/system`, `.aw/config`, `.aw/state`, and `.aw/records` wherever those roots are target-resident.
- `config/project.json` and `state/durable/` are separately trackable; `config/local.json` and `state/runtime/` are never tracked.
- All durable material in the private-target preset is tracked except explicitly prohibited local/runtime data.
- Public-plus-private-companion and clean-target presets are end-to-end proven with separate Git repositories.
- The source-checkout role protects canonical agent-workflows source and uses the same resolver contract.
- Pre-migration inventory and post-migration comparison account for every source item by hash and disposition.
- Migration is resumable, rollback-capable, cross-Git aware, and never deletes legacy material during the cutover transaction.
- Every producer writes only through the resolver, every compatibility reader is bounded, and forbidden legacy writes are covered by executable tests.
- The independent postcheck and fresh-agent review both pass after the migrator reports success.
- Full tests, packaging, sanitizer, generated-file, index, parity, install/uninstall, migration, and clean-delta gates pass from a clean checkout.

## Cross-IPD validation

- Maintain one machine-readable root/policy vocabulary imported by resolver, wizard, installer, migration, adapters, storage, and tests.
- Maintain one explicit scenario-to-test map; no child may claim a scenario already covered without naming the executable test.
- Compare source claims, documentation claims, and observed paths for every preset.
- Run migration fixtures through inventory, execution, comparison, postcheck, rollback, resume, and cleanup-preview surfaces.
- Verify target and companion Git indexes independently and prove no command stages or commits across the wrong boundary.
- Verify all support scripts with stdlib `unittest` fixtures and deterministic JSON output.
- Use the fresh-agent follow-up instruction only after deterministic postcheck output exists; the agent must consume evidence rather than reconstruct it from summaries.

## Deferred / out of scope (with reason)

- Secret storage is out of scope. AW policy files must not become a credential vault.
- Automatic remote creation, remote privacy inference, push, tag, release, or destructive cleanup is out of scope without separate explicit human authorization.
- General project task tracking remains outside AW actions and records.
- Repository exclusion-list behavior and CLI help ordering/detail are owned by concurrent work and must not be modified by this Set unless a merge conflict requires coordination.

## Scope check

- Over-scope: The Set changes AW layout, placement policy, migration, routing, adapters, self-adoption, and documentation only; it does not redesign unrelated workflow semantics.
- Under-scope: Physical naming, root internals, Git policy, presets, custom placement, persistence, source checkout, companion durability, inventory, collision handling, rollback/resume, compatibility, all producers/readers, adapters, self-migration, independent audit, documentation, and release evidence are included.

## Required tests / validation

- Each child must run `python3 -m agent_workflows ipd lint --phase pre-transition --agent <child>` before transition.
- The orchestrator must run `python3 -m agent_workflows ipd lint --phase pre-transition --agent <orchestrator>` after every child evidence update.
- The final executor must run the exact focused commands named by each child, then `python3 -m unittest discover -s tests -t .` after the final code change.
- Run `python3 -m agent_workflows plans index --check --agent`, all generated-file and entry-point parity checks, package build/inspection, and `python3 -m agent_workflows check-local-leaks . --agent`.
- Exercise every row in `tools/awphysical/migration-scenarios.json`; fail if the scenario set and evidence set differ.
- Run `tools/awphysical/aw_layout_inventory.py`, `aw_layout_compare.py`, and `aw_layout_postcheck.py` against fixtures and the agent-workflows self-migration; preserve their actual JSON and exit statuses.
- Prove `git status --short`, `git diff --cached --name-only`, and merge-base deltas separately for target, companion, and source repositories.

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. Child completion requires both terminal structural conformance and the actual observed E/V evidence recorded in that child; the linter alone is never sufficient.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m agent_workflows specs check .agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md --agent && grep -Fx -- '- Status: approved' .agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` | superseding spec plus owner-tool history | Spec conforms, is human-approved, and contains the complete cross-Set contract before any child starts. | spec is nonconforming/not approved, approval lacks owner-tool history, or a child starts early |
| E-02 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-01-*.md` | Order 01 executed IPD and observed E/V evidence | Physical-root and Git-policy contract is terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-03 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-02-*.md` | Order 02 executed IPD and observed E/V evidence | Policy schema and resolver are terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-04 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-03-*.md` | Order 03 executed IPD and observed E/V evidence | Wizard and persistence behavior are terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-05 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-04-*.md` | Order 04 executed IPD and observed E/V evidence | System installation/source-checkout behavior is terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-06 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-05-*.md` | Order 05 executed IPD and observed E/V evidence | Companion privacy/durability behavior is terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-07 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-06-*.md` | Order 06 executed IPD and observed E/V evidence | Inventory and mapping are terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-08 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-07-*.md` | Order 07 executed IPD and observed E/V evidence | Migration, rollback, and resume are terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-09 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-08-*.md` | Order 08 executed IPD and observed E/V evidence | Producer and compatibility cutover is terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-10 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-09-*.md` | Order 09 executed IPD and observed E/V evidence | Adapters and clean-target behavior are terminal, conforming, and independently evidenced. | structural nonconformance or any E/V evidence is missing/stale |
| E-11 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-10-*.md` | Order 10 executed IPD and observed E/V evidence | Independent comparison/postcheck is terminal, conforming, and catches every deceptive fixture. | structural nonconformance, unmapped deceptive fixture, or missing actual evidence |
| E-12 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-11-*.md` | Order 11 executed IPD plus real pre/post baseline | Source-repository dogfood migration is terminal and preserves bytes and every artifact Git history. | any digest/history count or tip is missing/reduced, or structural/evidence check fails |
| E-13 | `python3 -m agent_workflows ipd lint --phase post-transition --agent .agents/plans/executed/20260810-awphysical-12-*.md` | Order 12 executed IPD plus 25-to-44 behavior crosswalk | Documentation/release acceptance is terminal and claim set equals evidence set without publication. | scenario/crosswalk/claim mismatch, structural failure, or unauthorized publication |
| E-14 | `python3 -m unittest discover -s tests -t . && python3 -m agent_workflows plans index --check --agent && python3 -m agent_workflows specs check --agent && python3 -m agent_workflows check-local-leaks . --agent` | clean checkout, all terminal children, package/scenario evidence | Full regression and owner-tool gates pass and retained legacy removal triggers remain explicit. | any command is nonzero, any child/evidence is absent, or claim set differs from evidence set |

## Open questions

### OQ-01: Human approval of the superseding physical-layout spec (BLOCKS the whole Set)

- Blocking: yes
- Status: open
- Owner: human maintainer
- Resolution or deferral rationale: `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` now exists at `to-review`, supersedes the implemented logical-layout spec, and contains the physical tree, presets, migration retention, 25-to-44 behavior scenario crosswalk, compatibility, and release boundary. No child may execute until independent review and human approval transition it through the owner tool.

### OQ-02: Tracked prototype ownership and clean-checkout replay

- Blocking: no
- Status: resolved
- Owner: Order 06 and Order 10
- Resolution or deferral rationale: Commit `767d98c` tracks `tools/awphysical/` and the scenario catalog. Order 06 owns promotion of inventory/map prototypes into the production command surface; Order 10 owns promotion of compare/postcheck prototypes and deceptive-fixture coverage. The tracked prototypes are review inputs, not proof that production behavior exists.

## Plan-review outcome (2026-08-10 /plan-review, Codex GPT-5)

Verdict: REVIEWED - OPEN QUESTIONS. Readiness: NO-GO solely because the superseding physical-layout spec is `to-review`, not human-approved (OQ-01). The Opus findings are reconciled: the child DAG now controls orchestrator dependencies; every E/V pair names an executable test, fixture, positive assertion, and failure condition; stale test/plan references are removed; existing resolver, installer, migration, producer, adapter, audit, dogfood, and release anchors are explicit; and tracked prototypes from commit `767d98c` have named promotion owners. All 13 plans conform at `--phase review-finalize`. Human spec approval is the required next step; no child execution is authorized by this review.

## Independent re-review outcome (2026-08-10 /plan-review-long, opencode Opus 4.8, 14 parallel evidence lanes)

Verdict: REVIEWED - OPEN QUESTIONS. Readiness: NO-GO (human spec approval, OQ-01). This independent re-review verified, against actual repository evidence at path:line, that essentially every prior handoff finding is RESOLVED: the new physical spec `20260810-1447-01` exists and supersedes `20260809-2211-01` (`aw specs check` passes; D130 recorded); `--phase executor` is gone Set-wide (`--phase pre-transition`); the orchestrator E-item dependencies now mirror the child DAG (all 14 rows verified); the config.json->project.json/local.json split is defined (spec Section 7); `tools/awphysical/` is tracked (commit 767d98c); honest blocking OQ present in every plan; all 13 conform at `--phase author` and `--phase review-finalize`; no execution is claimed. The package is materially sound and correctly self-blocked on human approval.

Residual findings (all LOW/MEDIUM remediation-risk, several HIGH-severity-but-low-risk-to-fix) were HANDED BACK to GPT-5.6 High (the author) for coherent cross-artifact resolution, per maintainer direction, in the prompt `.agents/prompts/pending/20260810-1530-01-awphysical-residual-reconciliation.md`. Themes:

- OQ-R1 (crosswalk evidence gap, HIGH-severity/LOW-risk; spec Section 12 + Order 12 + `tools/awphysical/migration-scenarios.json`): old scenarios #6 (first-install EOF fails closed) and #22/#23 (color / screen-reader accessibility) are mapped to AWP scenarios (AWP-041, AWP-001) whose `expected` sets do NOT encode those behaviors, so the "scenario set equals evidence set" gate (Order 12 V-06) can pass while two spec-mandated behaviors ship untested. Add real `expected` tokens or dedicated AWP rows and make the machine-checkable crosswalk assert per-behavior coverage, not just parent-id existence.
- OQ-R2 (V-evidence discrimination, MEDIUM; nearly all children): the per-item matrix binds each E to one `test_eNN` whose "required positive assertion" is a verbatim copy of the E expected-outcome and whose failure condition is an identical generic string; mega-items (Order 04 E-05/E-07, Order 07 E-08 [~12 fault classes], Order 10 E-07 [~10 deceptive classes]) collapse many independently-failing conditions into one row. Give safety-critical rows a named negative/planted-violation fixture and per-condition assertions.
- OQ-R3 (durability enum drift, MEDIUM; Order 05 + `agent_workflows/project_schema.py`): spec Section 10 lists `acknowledged-durable` and `unreachable`; the shipped `DurabilityState` enum has 5 values (`durable-private`, no `unreachable`). Reconcile (rename/map + add states) and name the owning Order; treat the shared-schema edit under the coordination gate.
- OQ-R4 (postcheck independence, HIGH-severity/MEDIUM-risk; Order 10 + `tools/awphysical/aw_layout_postcheck.py`): the compare tool independently re-hashes the filesystem (good, verified deterministic), but the postcheck trusts the migrator-authored context JSON for routing/authority/rollback - the exact checks meant to catch a lying migrator - and lacks companion/source Git + adapter-purity + wrong-git-index rules and a deterministic sort/digest. Add real filesystem/Git probes (a fabricated-clean-context fixture must be caught), a determinism digest, and the two missing rule classes.
- OQ-R5 (Order 11 packaging-move ownership + integrity predicate, MEDIUM; Order 11 + Order 04): the `.agents/workflows` dual role (live system root AND packaged distribution source: `pyproject.toml` force-include, `agent_workflows/_compat.py` `_DATA_RELATIVE`, `hatch_build.py`, `versioning.py`) is not named, Order 04's source-checkout protection is not required to be evidence-cited before Order 11 mutates the real repo, the intra-plan E-DAG is flattened to E-01 (real mutation E-04 could run before a green rehearsal E-03), and the E-06 hard-fail predicate ("post commit-count >= pre for every artifact tree and full history; any missing/changed tracked path fails") is not stated.

All residuals keep the spec at `to-review` and the human-approval blocker intact. Next action: GPT-5.6 addresses OQ-R1..R5; then a re-review; then human approval of the spec is the sole remaining design gate.

## Residual reconciliation outcome (2026-08-10, Codex GPT-5.6)

OQ-R1 through OQ-R5 are resolved for re-review. The catalog now has 44 scenarios and a behavior-level 1-through-25 crosswalk; safety-critical matrices name separate planted failures and observable predicates; Order 02 owns the seven-state durability vocabulary and compatibility alias while Order 05 owns classification; the postcheck reads independent artifacts, actual paths, adapter bytes, and Git ownership and emits `postcheck_id`; Order 11 now has the sequential E-DAG, Order 04 evidence gate, explicit external roots, named packaging ownership, and hard history/content predicates. LOW follow-ups add spec traceability, exact CHANGELOG targets, closed deterministic Git classifications, physical-layout test-module ownership, and static producer discovery/legacy-sink guards. The spec remains `to-review`; OQ-01 is still the sole execution blocker.

## Second independent re-review outcome (2026-08-10 /plan-review-long, opencode Opus 4.8, post-1530-01)

Verdict: REVIEWED - OPEN QUESTIONS. Readiness: NO-GO (human spec approval, OQ-01). After GPT-5.6 High's 1530-01 residual reconciliation (commit cc2d184), an independent re-review (spec lane + code/tools lane + 13 plan lanes, verified at path:line) found the reconciliation MATERIALLY SUCCESSFUL: R1 crosswalk closed (catalog now 44 scenarios; real AWP-043 first-install-EOF-fail-closed and AWP-044 color/screen-reader; Section 12 requires per-behavior assertion tokens with a machine check); R3 durability enum reconciled in project_schema.py/storage.py (acknowledged-durable/unacknowledged-remote/unreachable + legacy alias); R4/R5 postcheck now probes the actual Git owner and emits a deterministic postcheck_id digest and catches a fabricated-clean context; Orders 04/07/08/10/11/12 residuals verified resolved (source-spoof/ambiguous tests + packaging; byte-copy + journal reuse; producer inventory from real symbols + parity test + allowlist purge + sink guard; per-class deceptive table; real-repo before/after baseline + hard-fail predicate + mirror rehearsal + Order-04 citation gate; crosswalk + release boundary). Full suite `Ran 825 tests OK (skipped=1)`; `aw specs check` conforms; all 13 lint conforming at review-finalize; `aw sanitize` clean. Every plan keeps Status reviewed, OQ-01 intact, no execution claim, and the prior 14-lane history line.

Remaining LOW/MEDIUM residuals (none blocks anything beyond OQ-01) appended to `.agents/prompts/pending/20260810-1544-01-awphysical-spec-to-reviewed-focus.md` for GPT-5.6:
- Spec text still needs S2.1 durability-enum redefinition note, S2.2 postcheck-independence definition, S2.3 all-preset scenario counting (behaviors are already enforced in tests; only the normative spec sentences are missing) - these are the only items gating the spec's advance to `reviewed`.
- L07-01: Order 07's test-matrix module still targets the SUPERSEDED tests/test_layout_migration.py (collision fix applied to 06/08 but missed on 07).
- L04-01: Order 04 E-05 "reuse is_self" is path-equality-only; extend with positive-identity (package metadata + Git common-dir) per spec Section 9.
- S-02: project_schema.py `DURABLE_PRIVATE` enum member is a misleading alias of ACKNOWLEDGED_DURABLE (dead; the dict does the real mapping).
- R2 (Set-wide): V-evidence discrimination was applied selectively; extend named negative/per-condition assertions to Orders 01/02/05 and O7's non-kill fault classes.
- NEW-01: clean_delta.py is still the fabricated hardcoded-zero module (correctly scheduled for Order 09 E-01; add a return-value-provenance negative assertion so the literal cannot survive execution).

Next action: GPT-5.6 folds the spec S2.1-S2.3 items (advancing the spec to eligible-for-reviewed) plus the plan/code residuals; then a final re-verify; human approval of the spec remains the sole design gate.

## Validation and cross-check (verify before reporting the Set complete)

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
- [ ] V-09 validates E-09
  - Required evidence: Run Evidence matrix row E-09 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: Run Evidence matrix row E-10 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: Run Evidence matrix row E-11 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: Run Evidence matrix row E-12 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: Run Evidence matrix row E-13 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: Run Evidence matrix row E-14 exactly and paste the actual command, exit status, and relevant raw output. The named fixture and positive assertions MUST pass, and its named failure condition MUST be observed as a non-pass in the negative case; a prose summary or another row's output is not evidence.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The Set is one major-version cutover, but its independently verifiable contracts, resolver, wizard, installer, companion, migration, routing, adapters, audit, dogfood, and release surfaces are separated into short child IPDs.

Execution is blocked until `/plan-review` gives the orchestrator and every child a GO verdict and the human maintainer approves the controlling spec and Set. Each executor must obey its child scope fence, coordinate overlapping files with concurrent work, paste actual runner output for every claimed pass, commit only its explicitly scoped paths with path-scoped Git commands, never use broad staging, and never push. Any discovered data-loss, privacy, Git-boundary, source-overwrite, or rollback ambiguity is a hard stop. After all children pass independently, update this orchestrator's E/V evidence, run the whole-Set gates, and move it to `executed/`; do not release or delete retained legacy material without the separate gates in Order 12.
