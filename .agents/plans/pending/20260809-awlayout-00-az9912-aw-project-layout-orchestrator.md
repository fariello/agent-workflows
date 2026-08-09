# IPD: AW project layout, external records, wizard, and state

- Date: 2026-08-09
- Kind: orchestrator
- Concern: coordinate the approved implementation of the four logical AW roots, external-by-default records, AW_HOME project routing, the install/update policy wizard, operational actions, workflow rewiring, migration, clean-delta delivery, and final documentation.
- Scope: orchestration only for Set `awlayout (AW project layout)`; this file changes no product code. Orders 01 through 11 each own one bounded implementation surface and their own tests.
- Status: reviewed
- Set: awlayout (AW project layout)
- Order: 0
- Highest E allocated: 12
- Author: Codex (GPT-5, high reasoning)
- Id: az9912

## Workflow history

- 2026-08-09 to-review (Codex GPT-5 high): created from `.agents/docs/specs/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md` after the maintainer selected the four-root model, external records recommendation, wizard requirement, and generational AW-action design.
- 2026-08-09 revision (Codex GPT-5 high): rebased onto D123 through D125; adopted stable plan identity and clustered naming, owner-written spec status, and D125's existing attention projection as the sole `/whatnext` input.
- 2026-08-09 reviewed /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO. The Set is architecturally sound and all 12 plans lint conforming (valid DAG, dependencies match each child, E/V bijections 1:1, execution contract present, migration/uninstall preserve data by default, release boundary honored). Findings recorded per plan, NOT rewritten (another author's plans; the controlling spec is unapproved). Two gating conditions: (1) the controlling spec `20260809-2211-01` is Status: to-review, NOT approved - the orchestrator requires spec approval before any child executes; (2) several HIGH findings are FOUNDATIONAL and need the spec author / maintainer, not reviewer edits. Orchestrator findings: L0-01 (the table's "Depends on" column = prior Orders while each child's `- Depends on:` metadata = its own E-items; add a one-line note distinguishing them). L0-02 (E-12/V-12 assert all 25 spec Section 19 scenarios are "accounted for" but provide no per-scenario -> owning-child traceability map; delegate is only to Order 11 - see L11-01). Cross-Set HIGH themes returned to the author, below.
- 2026-08-09 /plan-review cross-Set HIGH findings (return to author Codex GPT-5): (H1, Orders 07 + attention_contract) the D125 attention scanner shipped AFTER this branch and is structurally REPO-RELATIVE (`iter_scan_files` over `SCAN_ROOTS`; `attention.py::_rel_posix` raises on external paths; `RULE_IDS` is a closed catalog; `TreePolicy.root` is a repo-relative prefix), so Order 07 cannot read an EXTERNAL `state/actions/` root as written - E-01 must add an external-root discovery branch + a non-repo-relative item-path + a new stable rule id, and must declare the Order 01 resolver as a direct dependency (currently only Depends on 06). (H2, Orders 05/06) the plans assume a TRANSACTIONAL installer with rollback, but the installer has no transaction boundary today (per-file backup + a separate user-invoked `--undo`); the "rollback-safe materialization" claim rests on machinery that does not exist - either build a staging+pivot transaction or restate the recovery mechanism. (H3, Order 05) human-owned `config/` no-clobber is asserted but not gated against the hash-recorded-content model (a human value AW never wrote has no recorded hash). (H4, Order 02) `~/.aw` default AW_HOME + config store conflicts with D46 "never write under `~/`"; reconcile which store owns AW_HOME selection. (H5, Order 04) required-test command `python3 -m agent_workflows update` targets a NON-EXISTENT verb (`cli.py` has no `update`; install is idempotent) - fix the command or add the verb to scope. (H6, Order 08) the forbidden-producer-path audit is a blunt literal grep matching ~48 legitimate references and can never yield the orchestrator's "zero-match" proof - redefine as an allowlist-backed, producer-write-scoped test. (H7, Order 11) the 25-scenario acceptance matrix is asserted but not enumerated per scenario; V-04's "no scenario silently skipped" is unenforceable without an explicit 25-row scenario -> test map. Plus MEDIUM security-test gaps (path-traversal/symlink at the resolver+registry, origin-URL spoofing, fail-closed precedence+provenance) and evidence-concreteness gaps recorded on Orders 01-03. NONE are BLOCKER/REPLAN; all are repairable with bounded edits once the spec is approved and the foundational calls are made.

## Goal

Deliver the 2026-08-09 specification without a partial mode, ambiguous path ownership, unsafe silent default, or workflow that still hard-codes a legacy record location. Keep every child short and explicit enough for a fast execution model, while requiring independent review and approval for each child.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Child gates and final cross-check

- [ ] E-01 verify Order 01 is executed and validated before any dependent child begins.
  - Depends on: none
  - Expected outcome: one canonical logical-root schema and context resolver exist with stable human and machine interfaces.
  - Execution state: pending
- [ ] E-02 verify Order 02 is executed and validated after Order 01.
  - Depends on: E-01
  - Expected outcome: AW_HOME resolution, stable project identity, registry matching, and safe attach or move behavior exist.
  - Execution state: pending
- [ ] E-03 verify Order 03 is executed and validated after Orders 01 and 02.
  - Depends on: E-01, E-02
  - Expected outcome: home, companion, and repository record backends plus honest durability classification exist.
  - Execution state: pending
- [ ] E-04 verify Order 04 is executed and validated after Orders 01 through 03.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: first install and update use the accessible color-aware policy wizard and deterministic noninteractive rules.
  - Execution state: pending
- [ ] E-05 verify Order 05 is executed and validated after Orders 01 through 04.
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: system, config, and state materialization plus manifest ownership use the new layout contract.
  - Execution state: pending
- [ ] E-06 verify Order 06 is executed and validated after Orders 01, 02, and 05.
  - Depends on: E-01, E-02, E-05
  - Expected outcome: AW operational actions, generations, lifecycle directories, short CLI verbs, and install history exist.
  - Execution state: pending
- [ ] E-07 verify Order 07 is executed and validated after Order 06.
  - Depends on: E-06
  - Expected outcome: `aw todo` owns action state, `aw attention` exposes its native-source projection, and setup-repo, whatnext, status, and list consume the correct owner surface.
  - Execution state: pending
- [ ] E-08 verify Order 08 is executed and validated after Orders 01, 03, and 05.
  - Depends on: E-01, E-03, E-05
  - Expected outcome: every producing workflow routes records and record commits through context instead of legacy hard-coded paths.
  - Execution state: pending
- [ ] E-09 verify Order 09 is executed and validated after Orders 03, 05, 06, and 08.
  - Depends on: E-03, E-05, E-06, E-08
  - Expected outcome: migration, rollback, compatibility detection, and conservative uninstall preserve records and user edits.
  - Execution state: pending
- [ ] E-10 verify Order 10 is executed and validated after Orders 01, 02, 03, 05, 08, and 09 and only for host mechanisms reproduced by D113 fixtures.
  - Depends on: E-01, E-02, E-03, E-05, E-08, E-09
  - Expected outcome: local clean-delta uses evidence-gated user-scope skills and verifies the target merge-base diff.
  - Execution state: pending
- [ ] E-11 verify Order 11 is executed and validated after Orders 01 through 10.
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10
  - Expected outcome: current-state docs, migration walkthrough, changelog, release boundary, full test matrix, and dogfood scenarios agree with shipped behavior.
  - Execution state: pending
- [ ] E-12 perform the whole-Set cross-check against the canonical specification and paste actual validation output.
  - Depends on: E-11
  - Expected outcome: no unresolved legacy output path, no duplicated policy source, all twenty-five spec acceptance scenarios accounted for, full suite green, leak scan clean, and authored Markdown dash-clean.
  - Execution state: pending

## Child IPDs, sequence, and dependencies

| Order | File | Bounded responsibility | Depends on |
|---|---|---|---|
| 01 | `20260809-awlayout-01-m9tqof-aw-context-and-logical-roots.md` | Canonical schema, logical roots, context/path resolver, CLI contract | none |
| 02 | `20260809-awlayout-02-bgyymp-aw-home-project-identity-and-registry.md` | AW_HOME, stable project IDs, registry matching, attach/move | 01 |
| 03 | `20260809-awlayout-03-g4y28x-records-backends-and-durability.md` | home/companion/repository backends, Git boundaries, durability truth | 01, 02 |
| 04 | `20260809-awlayout-04-q0wpk4-install-update-policy-wizard.md` | first-install wizard, update checkpoint, color/accessibility, noninteractive policy | 01, 02, 03 |
| 05 | `20260809-awlayout-05-tg60qo-system-config-state-layout-and-ownership.md` | physical materialization, manifests, thin adapters, transactions | 01, 02, 03, 04 |
| 06 | `20260809-awlayout-06-anlovz-operational-actions-and-install-history.md` | actions schema/lifecycle/CLI, release reconciliation, install history | 01, 02, 05 |
| 07 | `20260809-awlayout-07-b31tuy-action-workflow-and-status-integration.md` | action attention source, setup-repo, whatnext, status, list integrations | 06 |
| 08 | `20260809-awlayout-08-0me1hr-producing-workflow-record-routing.md` | all record-producing workflow paths and commit destinations | 01, 03, 05 |
| 09 | `20260809-awlayout-09-es1phc-layout-migration-rollback-and-uninstall.md` | transactional migration, compatibility, rollback, uninstall | 03, 05, 06, 08 |
| 10 | `20260809-awlayout-10-jmjh97-clean-delta-skills-and-host-gates.md` | evidence-gated user skills, zero-target delivery, clean-delta verification | 01, 02, 03, 05, 08, 09; D113 evidence |
| 11 | `20260809-awlayout-11-blw6qp-docs-release-and-end-to-end-cutover.md` | documentation, migration walkthrough, full acceptance, release cutover | 01 through 10 |

## Completion criteria (the whole Set is done only when)

- The canonical specification has been reviewed and explicitly approved.
- Every child has separately passed `/plan-review`, received human approval, executed in dependency order, passed `aw ipd lint --phase pre-transition`, and moved to `executed/` only after its own V-items passed with concrete evidence.
- External `home` records are the labeled recommended interactive default, while repository records remain an explicit informed choice.
- First install and update both expose the policy wizard behavior required by the specification, including accessible color and deterministic noninteractive failure.
- No producing workflow writes a new record to a legacy hard-coded path.
- The setup action persists until completed or dismissed and is visible through `aw todo`, the D125 attention projection, and all required consumer surfaces.
- Migration and uninstall preserve config, state, and records by default.
- Local clean-delta is advertised only for reproduced host mechanisms.
- The final full suite, leak scan, IPD lint, Markdown dash check, and twenty-five-scenario acceptance matrix pass with actual output retained.

## Cross-IPD validation

- Single source: Orders 02 through 11 import or consume Order 01's schema and resolver rather than restating policy enums or path precedence.
- Dependency safety: each child begins by verifying its required earlier symbols and stops if they are absent.
- Default consistency: spec, wizard, storage backend, docs, and tests all call `home` records recommended, but never silently choose it in an unconfigured noninteractive first install.
- Ownership consistency: system is CLI-owned, config is human-controlled, state is AW-operational, and records are workflow/human project artifacts in every backend.
- Privacy honesty: no test or prose equates out-of-target, a configured remote, or a clean target diff with secrecy.
- Migration safety: legacy records are validated at the destination before legacy ownership or adapters are removed.
- Host evidence: Order 10 contains no host claim stronger than D113 evidence for the exact tested host/version.
- Attention ownership: Order 06 owns action writes, Order 07 adds a pure exhaustive D125 source mapping, and `/whatnext` continues to consume `aw attention --format json` first and fail closed.

## Deferred / out of scope (with reason)

| Item | Reason | Later step |
|---|---|---|
| Remote or cloud clean-delta | Workstation AW_HOME and user skills do not automatically reach remote clones. | Separate evidence and specification. |
| Automatic Git hosting or remote creation | Requires provider authority and privacy choices beyond local installation. | Optional provider-specific integration after separate approval. |
| Encrypted records backend | Adds key management and does not solve all metadata disclosure. | Separate backend proposal if demanded. |
| History rewrite of already public records | Destructive and repository-specific. | Human-approved remediation workflow only. |

## Scope check

- Over-scope: none. The orchestrator coordinates only the canonical specification's implementation.
- Under-scope: all eleven children are required. Omitting the wizard, action ledger, producer rewire, or migration would leave an incoherent partial product.

## Required tests / validation

Each child carries literal focused and full-suite commands. Final Set validation must run `python3 -m unittest discover -s tests -t .`, `python3 -m agent_workflows ipd lint --all --agent .`, `python3 -m agent_workflows check-local-leaks . --agent`, the repository's Markdown dash check, and the Order 11 acceptance-scenario matrix. Paste actual output and retain any host-probe evidence required by Order 10.

## Open questions

No open questions.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: cite executed Order 01 with its V-items passed and show `aw context` schema tests green.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: cite executed Order 02 and passing identity, ambiguity, move, clone, and worktree tests.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: cite executed Order 03 and passing backend, Git-boundary, and durability-classification tests.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: cite executed Order 04 and passing first-install, update, noninteractive, color, and monochrome transcript tests.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: cite executed Order 05 and passing layout, manifest, adapter, drift, and transaction tests.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: cite executed Order 06 and passing action lifecycle, generation, reconciliation, and install-history tests.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: cite executed Order 07 and tests showing the same open setup action through todo, whatnext, status, and list, then completion through setup-repo.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: cite executed Order 08 and a zero-match audit for forbidden hard-coded producer output paths outside compatibility code.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: cite executed Order 09 and passing forward migration, rollback, drift preservation, and uninstall-preserves-records tests.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: cite executed Order 10, exact D113 host/version evidence, and a passing merge-base clean-delta verification fixture.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: cite executed Order 11, current-state docs, migration walkthrough, changelog entry, and the passing twenty-five-scenario matrix.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: paste actual final suite, IPD lint, leak scan, dash check, and cross-file policy audit output; cite any unresolved limitation explicitly.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This orchestrator and the canonical specification require `/plan-review` and explicit human approval before any child executes. Each child separately requires review and approval. Execute strictly in dependency order. A faster model may execute a child only from that child's full file and its named dependencies; it must not infer missing behavior from this orchestrator.

Execution contract: commit only files changed by the active child, path-scoped; never use `git add -A`, bare `git add`, `git commit -a`, or push. Paste actual validation output. Use no em or en dashes in authored Markdown. If a dependency, host proof, or required decision is absent, stop and report. Do not expand a child's file/symbol scope without a corrective or revised IPD. The terminal lifecycle transition is a post-gate transaction, not an E/V item. No tag, release, registry upload, or deployment is authorized by this Set.

After every child and this orchestrator have all E-items performed and matching V-items passed, append the lifecycle history, set `Status: executed`, move each plan from `pending/` to `executed/` with `git mv`, regenerate the plans index, and commit only the transaction's paths. Do not claim completion before that post-gate transaction succeeds.
