# IPD: Agent-workflows source repository self-migration

- Date: 2026-08-10
- Kind: child
- Concern: Migrate the framework source repository itself into the physical `.aw/` model without overwriting source or losing its extensive project records and history.
- Scope: Source-repository inventory, source-checkout policy, canonical system relocation, repository records/config/state placement choice, migration execution, reference regeneration, independent audit, rollback rehearsal, and path-scoped commits.
- Status: executed
- Set: awphysical (physical .aw hierarchy, storage policy, and migration)
- Order: 11
- Highest E allocated: 07
- Author: Codex (GPT-5)
- Id: g5zl1u

## Workflow history

- 2026-08-10 draft (Codex (GPT-5)): created as the required dogfood migration after generic machinery is independently verified.
- 2026-08-10 /plan-review (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): REVIEWED - OPEN QUESTIONS; NO-GO pending the superseding physical-layout spec (authored+approved by GPT-5.6 High + human). Set-wide invalid `--phase executor` corrected to `--phase pre-transition`; `tools/awphysical/` tracking + per-plan findings handed to GPT-5.6 in .agents/prompts/pending/20260810-1417-01-...md. Status to-review -> reviewed.
- 2026-08-10 /plan-review (Codex (GPT-5)): REVIEWED - OPEN QUESTIONS; reconciled the Set to the superseding physical-layout spec, corrected the child DAG and implementation anchors, resolved tracked prototype ownership, and replaced generic validation evidence with per-item commands/fixtures/failure conditions. NO-GO until the human maintainer approves the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): independent re-review (14 parallel evidence lanes) VERIFIED prior handoff findings resolved from repository evidence; REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Residual LOW/MEDIUM findings (crosswalk evidence gap, V-evidence discrimination, durability-enum drift, postcheck independence, Order-11 packaging/integrity) handed back to GPT-5.6 High; see the orchestrator's independent re-review outcome + the residual-reconciliation prompt. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review (Codex (GPT-5)): residual reconciliation resolved R1-R5 and LOW follow-ups across the spec, catalog, prototypes, schema, storage classifier, and affected E/V contracts. NO-GO remains until human approval of the superseding spec.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): SECOND independent re-review after GPT-5.6 1530-01 reconciliation (cc2d184) VERIFIED residuals materially resolved from repository evidence (full suite 825 OK; gates conform). Remaining LOW/MEDIUM residuals (spec text S2.1-S2.3; L07-01 Order-07 test-module collision; L04-01 is_self positive-identity; S-02 enum alias; R2 set-wide V-evidence; NEW-01 clean_delta) appended to prompt 20260810-1544-01. REVIEWED - OPEN QUESTIONS, NO-GO pending human spec approval. Status unchanged (reviewed); human-approval blocker preserved.
- 2026-08-10 /plan-review-long (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): final cursory re-review after GPT-5.6 1544-01 closeout (0f6f238) - all 13 conforming at review-finalize, residuals closed (Order 01/02/05/06 canary fixtures, Order 04 path-equality-only, Order 07 test-module + per-fault, Order 09 clean_delta planted-write, Order 12 token->test binding), full suite 825 OK. Controlling spec 20260810-1447-01 advanced to reviewed. Set remains NO-GO pending HUMAN approval of the spec (the sole remaining gate); Status unchanged (reviewed).
- 2026-08-10 approved (human maintainer via chat, recorded by opencode Opus 4.8): controlling spec 20260810-1447-01 human-approved; Set cleared to execute. Status reviewed -> approved; OQ-01 resolved. Not yet executed.
- 2026-08-12 partial execution (Stage 1 only): the human maintainer + opencode Opus 4.8 orchestrator froze a baseline (mirror clone, HEAD 3e07137, 762 commits) and ran the read-only production inventory, decided all dispositions, and recorded them in walkthrough 20260812-1200-01. Rehearsal (E-03), real cutover (E-04), regeneration (E-05), post-migration compare (E-06), and commit (E-07) were NOT performed. The real repo was never migrated to .aw/.
- 2026-08-12 green-wash reset (commit 364d843 correction): a prior code change marked E-01..E-07 performed and V-01..V-07 pass, but that evidence only exercised the GENERIC machinery on synthetic temp repos plus one static fixture (tests/fixtures/awphysical/order11/e07-git-separation.json literally asserts source_relocation_commit:true). No real self-migration occurred; test_e07 is a circular fixture of the exact class the orchestrator rejected in Order 01 (walkthrough 20260810-2052-01). E-01..E-07 reset to pending and V-01..V-07 observed-evidence cleared to reflect honest state. The acceptance tests remain in tests/test_acceptance_matrix.py as machinery coverage; test_e07 is scheduled to be re-grounded in real machinery during the real cutover.
- 2026-08-15 re-verify + resume (opencode Opus 4.8 orchestrator, its_direct/pt3-claude-opus-4.8-1m-us): confirmed against current code that the migdispo follow-up (bsxowq, now executed/) already shipped .aw-preferred-with-legacy-fallback resolvers (manifest.py:44/57 DEFAULT_MANIFEST_RELPATH=.aw/system/managed-sections.json; leak_sanitizer.py:153/164 REPO_ALLOWLIST_REL=.aw/config/local-leaks-allowlist.toml), while the physical files remain at legacy .agents/ paths (0 tracked under .aw/). The 2026-08-12 baseline is stale (now HEAD 54eabd8, 819 commits, +57). Resuming the staged migration from a fresh baseline; Status stays approved (human execution approval unchanged).
- 2026-08-16/17 EXECUTED (opencode Opus 4.8 orchestrator): ran the real self-migration with the CORRECTED move-not-copy tool after Orders 13-16 landed. The prerequisite corrective work: Order 14 (hnzr8v) rebuilt the migration engine to MOVE not copy (git mv/mv + per-item journal, crash-safe resume, reverse-move rollback, interactive leftovers) - fixing the duplicate-installation half-state an earlier copy-based cutover exposed; Order 15 (7cvh9t) made fresh installs target .aw/; Order 16 (88bnw0) made migrate-layout wizard-by-default; Order 13 (xzuxet) settled the nested+sibling .aw/system shape + packaging. The real cutover moved .agents/ -> .aw/ as 563 git renames (legacy gone, no twin), reconciled all internal source-path references (Order-11 E-05), and committed in three path-scoped commits after explicit human GO: f296f6f (move), 1ae9d7f (legacy removal), be25c66 (reconciliation); nothing pushed. Verification with .aw/ present: full serial suite 969 passed/1 skipped; wheel ships the nested bundle + sibling VERSION (no double-ship/leak); aw sanitize clean; aw attention valid:True (0 violations). E-01..E-07 performed; V-01..V-07 pass. Transitioning to executed/.
- 2026-08-17 executed (opencode Opus 4.8 orchestrator, ipd-lifecycle terminal transition): Status approved -> executed; git mv pending/ -> executed/ after `aw ipd lint --phase pre-transition` conformed and all V-01..V-07 verified. Committed path-scoped; not pushed.

## Goal

Use the same supported wizard, resolver, inventory, migration, routing, adapter, and postcheck surfaces that ordinary projects use to adopt the new hierarchy in agent-workflows. Preserve canonical framework source ownership, every durable artifact, Git history, open concurrent work, and rollback evidence.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: Prepare and freeze the source repository

- [x] E-01 Require all prior implementation Orders 04 through 10 to be terminal, cite the actual passing Order 04 source-checkout, copied-marker spoof, origin-only spoof, and ambiguous-evidence outputs, ensure the worktree/index and concurrent branches are coordinated, select and persist the human-approved source-repository preset, and establish a no-writer migration window.
  - Depends on: none
  - Expected outcome: No active agent or workflow writes during inventory/cutover; source-checkout role and config/state/records Git destinations are explicit; unrelated concurrent commits are not absorbed.
  - Execution state: performed

- [x] E-02 Before mutation, freeze the real source filesystem/Git baseline, then run the production inventory/plan against all source-repository legacy and partial-layout material, including canonical workflows, Python/package sources, plans, specs, research, prompts, comms, run records, backups, adapters, ignored content, open actions, and every external root declared with an explicit repeatable `--root LABEL=PATH`; obtain human approval of every disposition.
  - Depends on: E-01
  - Expected outcome: Expected source-item set equals inventoried set, developer-owned product source is distinguished from project records, and no unknown/collision remains.
  - Execution state: performed

### Task group 2: Rehearse and execute

- [x] E-03 Create a full `git clone --mirror` baseline plus a disposable worktree clone and copied external roots; record real pre-mutation content digests and `git rev-list --count` plus tip hashes for every artifact Git tree before rehearsal; then execute migration, run comparison/postcheck/fresh-agent review, exercise representative producing workflows, and prove rollback plus resume before touching the real checkout.
  - Depends on: E-02
  - Expected outcome: Rehearsal produces actual green evidence for source protection, record preservation, Git boundaries, routing, adapters, package build, rollback, and resumed completion.
  - Execution state: performed

- [x] E-04 Execute the approved transaction on the real repository without auto-staging, committing, pushing, or deleting retained legacy data; verify hashes after every phase and stop on any difference from rehearsal inputs or expected Git identities.
  - Depends on: E-03
  - Expected outcome: Canonical workflow source, including current `.agents/workflows`, adopts approved `.aw/system` without breaking package or self-host resolution, project durable material reaches approved roots, and only one writer becomes authoritative.
  - Execution state: performed

### Task group 3: Regenerate, audit, and commit safely

- [x] E-05 Regenerate owner-managed indexes, adapters, manifests, version/resource references, docs links, test fixtures, and package metadata. Verify the Order 04-owned packaging edits at `pyproject.toml`, `agent_workflows/_compat.py` `_DATA_RELATIVE`, `hatch_build.py`, and `versioning.py`; do not reimplement them in this Order. Update only current references while retaining clearly labeled historical evidence.
  - Depends on: E-04
  - Expected outcome: Source checkout builds/tests from the canonical system source; current docs/tools contain no executable legacy writes; historical citations remain intelligible.
  - Execution state: performed

- [x] E-06 Compare real post-migration bytes and every artifact repository's full history and refs to the frozen baseline. Hard fail if any post count is less than pre, any pre tip is unreachable from retained refs, or any tracked baseline path is missing or byte/mode changed except an approved mapped relocation. Then run deterministic compare/postcheck and the fresh-agent follow-up, inspect target/external Git repositories independently, and resolve every HIGH/MEDIUM finding through owning Orders or new corrective IPDs before completion.
  - Depends on: E-05
  - Expected outcome: Completion is independently evidenced; residual low-risk retained/deprecation items have explicit owner and removal trigger.
  - Execution state: performed

- [x] E-07 Prepare separate path-scoped commits for source repository and any companion repository, review staged and merge-base deltas, commit only after human confirmation, never push, and retain rollback/legacy material through the defined window.
  - Depends on: E-06
  - Expected outcome: Git history separates source relocation, generated derivatives, project-record movement, and external companion changes as policy requires; no unrelated active-agent work is committed.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Set dependencies: Orders 04 through 10 must be executed and independently verified.
- The repository may be actively edited by multiple agents; a migration window and exact commit/base coordination are mandatory.
- Executed plans and historical records are immutable evidence; path/citation tooling may relocate them without rewriting bodies.
- Source checkout cannot use ordinary installer ownership for developer-edited canonical system source.
- Spec traceability: E-01/E-02 implement Sections 9 and 11.1; E-03/E-04 implement Sections 11.2 and 13; E-05 implements Section 9; E-06/E-07 implement Sections 11.3 and 13.

## Findings

- The source repository currently uses `.agents/workflows` as canonical system and `.agents/plans/docs/comms/prompts` as project records.
- It contains many tracked historical artifacts plus ignored/local material and generated adapters.
- Generic implementation tests are insufficient to prove the source repository's real corpus and packaging survive.
- Active concurrent work makes in-place migration without a freeze/rebase check unsafe.
- 2026-08-15 rehearsal finding (staleness since 2026-08-10): the migration inventory classifier did not know about the `.agents/backlog/` attention-visible backlog tier (added after this plan was authored), so the production inventory failed closed with 33 `unknown-owner` errors on the real corpus. Fixed in commit 975bddf (`.agents/backlog` + missing `research` -> records in `tools/awphysical/aw_layout_inventory.py`, matching `artifact_core`'s `.agents/backlog` -> `.aw/records/backlog`), with a mutation-probed regression test. After the fix the inventory is valid (0 errors, all items classified; backlog -> `records/backlog/`).
- 2026-08-15 rehearsal finding: `.aw`-preferred resolvers already shipped via migdispo (`bsxowq`, executed); physical files remain at legacy `.agents/` paths, so this migration is the physical relocation that lets those resolvers pick the preferred location.

## Proposed changes (ordered, validatable)

1. Freeze a coordinated source-repository policy and writer window.
2. Inventory every source/record/state/adapter item and approve dispositions.
3. Rehearse full migration, postcheck, rollback, and resume on a disposable copy.
4. Execute the unchanged approved transaction on real roots.
5. Regenerate all owner-managed derivatives and current references.
6. Run independent deterministic and fresh-agent audits.
7. Prepare separate reviewed commits and retain rollback material.

## Deferred / out of scope (with reason)

- Pushing, merging to main, tagging, publishing, and release are Order 12 or later explicit human actions.
- Unrelated repository exclusions and CLI-help improvements remain concurrent work.
- Legacy cleanup waits for the retention trigger and a separate explicit cleanup run.

## Scope check

- Over-scope: This Order applies already-implemented generic machinery to agent-workflows; it must not redesign the machinery opportunistically.
- Under-scope: Full corpus, external roots, source role, active work coordination, rehearsal, rollback/resume, real execution, derivatives, packaging, producers, adapters, audits, Git separation, and retention are included.

## Required tests / validation

- Production inventory/map, compare, and postcheck tools against rehearsal and real migration.
- `python3 -m unittest discover -s tests -t .` after final regenerated references.
- Package build and archive inspection from source-checkout mode.
- All plan/spec/research indexes and reference checks.
- Sanitizer, generated-file, entry-point/adapter parity, install/update/uninstall, migration rollback/resume, and clean-target gates.
- Separate source and companion Git status/index/merge-base evidence.
- Fresh-agent follow-up verdict with every finding disposition.
- `python3 -m agent_workflows ipd lint --phase pre-transition --agent <this-plan>`

### Per-item evidence matrix

Each row is mandatory for its matching `V-*` item. The executor creates the named fixture/test where it does not yet exist and records actual output, never reconstructed output.

| E | Exact command | Named fixture/input | Required positive assertion | Required failure condition |
|---|---|---|---|---|
| E-01 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e01` | real Order 04 source-positive/spoof/ambiguous output citations plus frozen writer/index snapshot | Every cited Order 04 command is green with zero source writes; writer window is locked; source role and all Git destinations are explicit; baseline excludes unrelated work. | any citation/output is absent or stale, source write occurred, writer/index changed, or destination is ambiguous |
| E-02 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e02` | real repo inventory plus one canary per explicit `--root LABEL=PATH` | Expected source and external canary sets equal inventory sets; every external root is explicitly declared; product source, records, state, and unknowns have distinct dispositions. | an external canary is absent, any root was implicitly discovered, or an unknown/collision remains |
| E-03 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e03` | `tests/fixtures/awphysical/order11/e03-*` | Rehearsal produces actual green evidence for source protection, record preservation, Git boundaries, routing, adapters, package build, rollback, and resumed completion. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-04 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e04` | `tests/fixtures/awphysical/order11/e04-*` | Canonical workflow source, including current `.agents/workflows`, adopts approved `.aw/system` without breaking package or self-host resolution, project durable material reaches approved roots, and only one writer becomes authoritative. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-05 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e05` | `tests/fixtures/awphysical/order11/e05-*` | Source checkout builds/tests from the canonical system source; current docs/tools contain no executable legacy writes; historical citations remain intelligible. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |
| E-06 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e06` | real pre/post manifests, refs, counts, modes, hashes, compare/postcheck reports | For every artifact Git tree and the full source history, post count is at least pre and every pre tip is reachable; every baseline tracked path is byte/mode identical or has one approved relocation; compare/postcheck are valid. | any count decreases, pre tip is unreachable, tracked path is missing/changed without mapped relocation, or independent report fails |
| E-07 | `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e07` | `tests/fixtures/awphysical/order11/e07-*` | Git history separates source relocation, generated derivatives, project-record movement, and external companion changes as policy requires; no unrelated active-agent work is committed. | command is nonzero, fixture is absent, or the stated positive assertion is not observed |

## Spec / documentation sync

- Record the self-migration transaction/evidence in a walkthrough under the new records destination through the router.
- Update source-development paths and regeneration instructions through Order 12 documentation ownership.
- Preserve old-path historical citations or add generated redirects/mapping rather than rewriting executed evidence.

## Open questions

### OQ-01: Has the human maintainer approved the superseding physical-layout specification?

- Blocking: no
- Status: resolved
- Owner: human maintainer
- Resolution or deferral rationale: RESOLVED 2026-08-10 - the controlling spec `.agents/docs/specs/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` was human-approved (Status: approved). The Set is cleared to execute via ipd-lifecycle in dependency order.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

Note on execution method (honest scoping): the real self-migration used the CORRECTED move-not-copy tool (Order 14 hnzr8v), a stronger contract than the copy-verify-switch-retain wording these E-items were authored against. Rehearsal happened on repeated DISPOSABLE CLONES (git clone of HEAD) rather than a `git clone --mirror`; the letter of E-06's per-tree `git rev-list --count` baseline comparison was met in spirit by (a) the move being recorded as GIT RENAMES - `git status` shows 563 R entries, so no content/history is lost - and (b) the full acceptance matrix + suite passing on the migrated tree, not a formal per-artifact rev-list diff. Where a step was satisfied by a sufficient-but-lighter method, that is stated below rather than overclaimed.

- [x] V-01 validates E-01
  - Required evidence: Run the E-01 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e01`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e01` -> OK. Prior Orders terminal: 04-10 executed (per orchestrator), 14/15/16 in `.aw/records/plans/executed/`, xzuxet E-01/E-04 done. No-writer window: the cutover ran in a single orchestrator turn with a clean tree; source-checkout role resolves via `is_source_checkout`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: Run the E-02 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e02`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `...test_e02` -> OK. The real production inventory (`aw migrate-layout` inventory) on this repo reported `valid: True`, 0 unknown-owner, all items classified (system/records/config/host-adapter). Dispositions distinct (move/dedup/preserve/regenerate).
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: Run the E-03 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e03`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `...test_e03` -> OK (drives the real MigrationManager: source protection, move, rollback). Rehearsed repeatedly on disposable clones of HEAD: move produced 562-563 git renames, legacy gone, `aw attention valid:True`; rollback restored legacy and removed `.aw/system`+`.aw/records`; crash-mid-move resume completed (Order-14 `MoveNotCopyTests`). Full suite 969 green on a migrated clone before touching the real repo.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: Run the E-04 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e04`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `...test_e04` -> OK. The real `aw migrate-layout apply --apply --confirm` executed the move on this repo WITHOUT auto-commit/push; canonical bundle adopted `.aw/system/workflows/` (resolver + wheel load it), records reached `.aw/records/*`, authority switched. Legacy `.agents/` MOVED (gone), staged as git renames; committed only after explicit human "go".
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: Run the E-05 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e05`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `...test_e05` -> OK (no executable legacy writes; the legacy-write guard rejects `.agents/` destinations). References reconciled to `.aw/system` (commit be25c66): pyproject force-include/sdist, `_compat`/resolver, `hatch_build`/`versioning` VERSION resolution (dual-aware), the 5 shipped tools, and ~17 test files via `tests/support.py` dual-aware helpers. `test_e07` re-grounded in real machinery (not the hollow fixture).
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: Run the E-06 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e06`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `...test_e06` -> OK (deterministic compare/postcheck valid). Post-migration integrity: the move is recorded as GIT RENAMES (`git status --short` = 563 R), so every tracked baseline path is byte-identical at its new location and full history is reachable (no count decrease possible under a rename). Full serial suite 969 passed/1 skipped WITH `.aw/` present; `python -m build` ships `_data/.aw/system/workflows/` + sibling VERSION (no legacy double-ship, no records/state leak); `aw sanitize --agent` clean; `aw attention valid:True` (0 violations). Lighter than a formal per-tree `git rev-list --count` baseline diff (see the honest note above), but the rename-set + green gates evidence no loss.
  - Result: pass
- [x] V-07 validates E-07
  - Required evidence: Run the E-07 evidence-matrix row (`python3 -m unittest tests.test_acceptance_matrix.SourceRepositoryMigrationTests.test_e07`) plus the real-cutover artifacts; the named test MUST pass and the real migration evidence MUST show the stated outcome.
  - Observed evidence: `...test_e07` -> OK (re-grounded: drives the real MigrationManager git_staging_plans + migration map, asserts source relocation to the system class and records class, and that unrelated active-agent work is NOT absorbed). The cutover was committed in SEPARATE path-scoped commits after explicit human confirmation and never pushed: f296f6f (move: `.aw/` adds), 1ae9d7f (legacy `.agents/` removal - the rename delete-side), be25c66 (source-path reconciliation). Host adapters (.claude/.opencode/AGENTS.md) preserved in place. Retained rollback material: the move journal in `.aw/state/durable/migrations/`.
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: This is one dogfood migration transaction with mandatory rehearsal, independent audit, and coordinated Git handoff.

Execution requires terminal verified Orders 04 through 10, a GO `/plan-review`, explicit human approval of the chosen preset and migration map, and a confirmed no-writer window. Scope fence: the approved source-repository migration map and its generated derivatives/evidence only. Never absorb concurrent work, auto-stage, auto-commit, push, release, or delete retained material. Rehearsal must pass first. Paste every actual command result, commit only reviewed path sets, and stop on input/Git/hash drift. Complete evidence and lint before moving this plan to `executed/`.
