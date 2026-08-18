# IPD: Uniform artifact-naming grammar rollout (.type.md across all record types)

- Date: 2026-08-18
- Kind: orchestrator
- Concern: Spec 20260817-2147-01 (RELEASE BLOCKER, backlog 047ce9): adopt ONE artifact-naming grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` across every durable `.aw/records/` type, moving the TYPE signal into the filename (`.ipd.md`/`.prompt.md`/`.spec.md`/`.walkthrough.md`/`.roadmap.md`/`.backlog.md`/`.comms.md`; research keeps its richer `.<model>.<kind>.md`). Large: ~267 existing files + producers + parsers + `aw plan-names` + migration + docs.
- Scope: Roll out the naming grammar in dependency-safe LAYERS so every intermediate state is green. OUT: the version NUMBER (S6-V01); run-artifacts naming (keep `<RUN_ID>/`); the directory taxonomy (spec 20260817-2124-01, done).
- Status: to-review
- Set: awnaming
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 6gy9rf

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): built from spec 20260817-2147-01 (Set awnaming); by-layer decomposition (parsers-accept-first) so every intermediate state stays green.

## Goal

Ship the uniform `.type.md` naming grammar across all durable record types without a broken
intermediate state, by rolling it out in layers: make readers tolerant FIRST, then flip producers,
add validation, rename existing files, and finally update the migration + docs.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..05 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing; on completion advance spec 20260817-2147-01 to implemented and move blocked backlog 047ce9 to done (clearing release Blocker 2). Fold the vf03z3 tooling gaps (scaffold-derives-name, mv-preserves-Order, plan-names-validates, AGENTS.md-single-grammar) into the relevant child Orders and close vf03z3 when they land.
  - Depends on: none
  - Expected outcome: Orders 01..05 executed; grammar in force; spec implemented; 047ce9 + vf03z3 done.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Order chosen so EVERY intermediate state is green (readers accept both old + new before anything is renamed):

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | (to scaffold) awnaming-contract-and-parsers | Document the grammar contract in one place; make ALL parsers/resolvers/indexers ACCEPT `.type.md` AND bare `.md` (backward-compatible read), so nothing breaks mid-rollout. + tests. | none |
| 02 | (to scaffold) awnaming-producers | Make producers EMIT `.type.md` by default: `aw ipd scaffold` -> `.ipd.md`, prompt creation -> `.prompt.md`, `aw backlog new` -> `.backlog.md`, spec authoring -> `.spec.md` (already), comms/walkthrough/roadmap creators; standalone-singleton naming (id6-as-setid, NN=01). | 01 |
| 03 | (to scaffold) awnaming-planames-and-mv | `aw plan-names` (+ per-type peers) VALIDATE the grammar incl. `.type.md`; `aw plans mv`/`research mv` rename to it AND preserve `- Order:` (fixes vf03z3 mv-clobber). | 01,02 |
| 04 | (to scaffold) awnaming-rename-existing | Rename the ~267 existing dev-repo files to `.type.md` (tool-driven per type: plans/prompts/library/walkthroughs/roadmaps/backlog/comms), regenerate INDEX/STATUS manifests. | 01,02,03 |
| 05 | (to scaffold) awnaming-migration-and-docs | Legacy `.agents/` -> final NAME mapping in layout_migration (append `.type.md` on migrate); reconcile AGENTS.md's two documented grammars to the ONE grammar + shipped docs; close vf03z3. | 01,04 |

## Completion criteria (the whole Set is done only when)

- Orders 01..05 all executed.
- Every durable `.aw/records/` artifact filename matches `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md`
  (research excepted); `aw plan-names` (+ peers) validate it; producers emit it.
- A legacy `.agents/` fixture migrates DIRECTLY to the final `.type.md` names.
- AGENTS.md documents exactly ONE filename grammar; vf03z3 tooling gaps closed.
- Full serial suite green throughout; `aw attention --check` / `plans index --check` /
  `research index --check` / `specs check` / `backlog check` / `sanitize --agent` clean.
- Spec 20260817-2147-01 -> implemented; backlog 047ce9 -> done (release Blocker 2 cleared).

## Cross-IPD validation

- Order 01 (parsers accept both) MUST precede any producer flip (02) or rename (04) so no intermediate
  state has a reader that rejects an on-disk name. Order 04 (rename) runs only after 02/03 so renamed
  files match what producers/validators expect. Re-run the full check suite after each Order.

## Deferred / out of scope (with reason)

- The next-version NUMBER (S6-V01): maintainer decision, Section 9.
- Run-artifacts naming (`.aw/workflow-artifacts/<workflow>/<RUN_ID>/`): keep the timestamp-dir convention (spec OUT).
- Research's internal `.<model>.<kind>.md` suffix: kept (the one principled exception).
- Directory taxonomy (spec 20260817-2124-01): already done (awretrofit Order 07).

## Scope check

- Over-scope: none - every Order maps to a spec goal (G1..G8).
- Under-scope: none - the five layers cover the contract, producers, validation, the existing-file
  rename, and the migration+docs; research + run-artifacts are the documented exceptions.

## THIS-repo vs ALL-repos (pre-release framing - load-bearing)

Like the directory-taxonomy spec, the `.type.md` grammar has NOT shipped, so there is NO
released-name -> new-name migration. But the layers differ in WHO they affect:

- **Orders 01 (parsers-accept), 02 (producers emit), 03 (plan-names/mv):** ALL-REPOS. This is shipped
  code; every repo that installs the framework gets the new producers/validators. Order 01's
  backward-compatible read (accept BOTH bare `.md` and `.type.md`) is what lets an EXISTING legacy
  repo keep its old-named files working while NEW files use the grammar - no forced rename of a user's
  files.
- **Order 04 (rename ~267 existing files):** THIS-REPO-ONLY. It is a one-time dogfooding cleanup of
  THIS framework repo's own records; it ships nothing and imposes nothing on other repos.
- **Order 05 (migration NAME mapping):** ALL-REPOS, and the one genuine design question (OQ-02): when
  `aw migrate-layout` moves a legacy `.agents/` repo's records to `.aw/records/`, should it RENAME them
  to `.type.md` in the same hop (clean, single hop since we never shipped an intermediate), or LEAVE
  existing legacy-named files bare and rely on Order 01's dual-read (only NEW files get `.type.md`)?
  Renaming-on-migrate is more invasive (changes users' filenames + citations); dual-read-only is
  gentler. Resolve OQ-02 before Order 05.

## Required tests / validation

Per-Order V-items + the whole-Set completion criteria above; the orchestrator's E-01 verification
re-runs the full check suite + a legacy->final migration-name fixture after all Orders land.

## Open questions

### OQ-01: Do comms messages adopt `.comms.md`, or keep their envelope naming? (mirrors spec OQ-1)

- Blocking: no
- Status: open
- Owner: maintainer (resolve when Order 02/04 reaches comms)
- Resolution or deferral rationale: comms messages have an inbox/envelope/ack convention (comms.py)
  that may name files by routing rather than the artifact grammar. Decide at the comms-touching Order
  whether `.comms.md` + the grammar fits or comms is a second documented exception like research. Not
  blocking the Set's start (Orders 01-03 are type-agnostic plumbing); resolve before comms rename (04).

### OQ-02: Does `aw migrate-layout` RENAME legacy files to `.type.md`, or only dual-read? (determines Order 05 + whether Order 01's dual-read is permanent)

- Blocking: no
- Status: resolved
- Owner: human maintainer (2026-08-18)
- Resolution or deferral rationale: RESOLVED = ASK-then-OFFER. The shipped `aw migrate-layout`:
  (1) does NOT force-rename a user's existing legacy records by default (gentle);
  (2) when INTERACTIVE, ASKS the human whether to also rename the migrated records to the `.type.md`
  grammar (a self-contained P12 prompt);
  (3) when NON-INTERACTIVE, defaults OFF and supports an opt-in `--rename-to-grammar` flag for the
  uniform end-state.
  Consequence: **Order 01's dual-read is PERMANENT** (readers always accept both bare `.md` and
  `.type.md`, since a not-renamed migrated repo keeps mixed naming indefinitely). THIS repo's own
  ~267 files are still fully renamed by Order 04 (dogfooding, independent of the shipped migration
  policy). Order 05 implements the ask/flag/default-off behavior + the rename transform.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: all five child Orders show `Status: executed` under `.aw/records/plans/executed/`; the whole-Set completion criteria are demonstrated (paste: an artifact-name grammar sweep showing every durable type on `.type.md`, `aw plan-names` clean, a legacy->final migration-name fixture, full serial suite + all `--check`s + sanitize); spec 20260817-2147-01 is `implemented` and backlog 047ce9 is `done`.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: the five Orders are one coherent objective (roll out the uniform naming grammar), split by dependency LAYER (parsers-accept -> producers -> validation -> rename -> migration+docs) so each is independently reviewable/executable and every intermediate state stays green.

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, owns all verification + path-scoped
commits, never pushes, and moves each Order (and finally this orchestrator) to `executed/` only after
`aw ipd lint --phase pre-transition` conforms and the V-items are verified with pasted evidence. On
completion advances spec 20260817-2147-01 to implemented + backlog 047ce9 to done (clearing release
Blocker 2). The version bake + any tag/publish are Section 9, human-gated. RELEASE BLOCKER 2.
