# IPD: Uniform artifact-naming grammar rollout (.type.md across all record types)

- Date: 2026-08-18
- Kind: orchestrator
- Concern: Spec 20260817-2147-01 (RELEASE BLOCKER, backlog 047ce9): adopt ONE artifact-naming grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` across every durable `.aw/records/` type, moving the TYPE signal into the filename (`.ipd.md`/`.prompt.md`/`.spec.md`/`.walkthrough.md`/`.roadmap.md`/`.backlog.md`/`.comms.md`; research keeps its richer `.<model>.<kind>.md`). Code investigation shrank the surface: the record READERS (plans.py:184, plans_index.py:91, ipd_lint.py:758) glob `*.md` and read metadata from FRONT-MATTER, not the filename, so `.type.md` files are already read fine (dual-read is free). The filename grammar is enforced in only three narrow places: `plans_refs._CLUSTERED_RE` (31), `normalize_plan_names._CLUSTERED_RE`/`parse_name` (105/165), and `research_contract.parse_name` (265, already type-style, OUT). So the real change = extend those 2 regex tails + the name GENERATOR (`plans_refs.build_name`:126) + `aw plan-names` + rename this repo's own files.
- Scope: Ship the grammar as new-file behavior (all-repos, small) and dogfood-rename THIS repo's existing files (this-repo). OUT: the version NUMBER (S6-V01); run-artifacts naming (keep `<RUN_ID>/`); the directory taxonomy (spec 20260817-2124-01, done); research naming (already type-style).
- Status: reviewed
- Set: awnaming
- Order: 0
- Highest E allocated: 01
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Id: 6gy9rf

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)): created.
- 2026-08-18 authored (opencode Opus 4.8): built from spec 20260817-2147-01 (Set awnaming); by-layer decomposition (parsers-accept-first) so every intermediate state stays green.
- 2026-08-18 /plan-review (opencode Opus 4.8): APPROVE WITH REVISIONS APPLIED; child table verified against real filenames; no orchestrator-level findings; child findings PR-001..PR-004 fixed in Orders 01/02.

## Goal

Ship the uniform `.type.md` naming grammar across all durable record types without a broken
intermediate state. Because the record readers are already front-matter-driven and glob `*.md`,
`.type.md` files are read fine today with zero changes (dual-read is free). So the rollout is two
clean layers: (01) teach the grammar to the few filename-aware sites - the 2 clustering regexes, the
name generator, and `aw plan-names` - and make producers emit `.type.md`; then (02) dogfood-rename
THIS repo's ~267 existing files and reconcile AGENTS.md to the one grammar. No shipped
`.md`->`.type.md` migration is needed (the grammar never shipped; a legacy repo migrates in one hop
and its bare-named files keep working via the free dual-read); an optional rename-on-migrate nicety is
demoted to a follow-up backlog item, not a blocker.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation.

### Task group 1: orchestrate the Set

- [ ] E-01 Drive Orders 01..02 through the IPD lifecycle in dependency order (author -> /plan-review -> human approval -> execute -> verify -> transition), owning verification + path-scoped commits, never pushing; on completion advance spec 20260817-2147-01 to implemented and move blocked backlog 047ce9 to done (clearing release Blocker 2). Fold the vf03z3 tooling gaps (scaffold/mv-preserves-Order/plan-names-validates/AGENTS.md-single-grammar) into Orders 01/02 and close vf03z3 when they land; file the optional rename-on-migrate nicety (OQ-02 option) as a separate follow-up backlog item rather than gating the release on it.
  - Depends on: none
  - Expected outcome: Orders 01..02 executed; grammar in force for new files; this repo's files renamed; AGENTS.md single-grammar; spec implemented; 047ce9 + vf03z3 done.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Child IPDs, sequence, and dependencies

Split by AUDIENCE, not by micro-layer: Order 01 is the SHIPPED grammar (all-repos, small); Order 02
is the THIS-repo dogfood rename + docs. Every intermediate state is green because the free dual-read
means `.type.md` and bare `.md` files both read fine at all times.

| Order | File | What it does | Depends on |
|---|---|---|---|
| 01 | 20260818-awnaming-01-f8e6y7-grammar-and-producers.md | ALL-REPOS, ships. Extend the 2 filename-grammar sites to accept an optional `.<type>` before `.md` (`plans_refs._CLUSTERED_RE`:31, `normalize_plan_names._CLUSTERED_RE`/`is_conformant`/`parse_name`); make the name GENERATOR + producers EMIT `.type.md` (`plans_refs.clustered_name`:125, `aw ipd scaffold`->`.ipd.md`, `aw backlog new`->`.backlog.md`; spec already `.spec.md`); `aw plan-names` VALIDATE the grammar incl. `.type.md`; `aw plans mv`/`research mv` emit it AND preserve `- Order:`/`- Date:` (fixes vf03z3 mv-clobber). Standalone-singleton naming (id6-as-setid, NN=01). + tests. | none |
| 02 | 20260818-awnaming-02-975whv-rename-and-docs.md | THIS-REPO, ships nothing. Rename this repo's ~287 existing non-research files to `.type.md` (git mv per type), regenerate INDEX/STATUS manifests + fix internal citations; reconcile AGENTS.md's two documented grammars (lines 26 + 51) to the ONE grammar; close vf03z3; file the optional rename-on-migrate nicety (OQ-02) as a follow-up backlog item. | 01 |

## Completion criteria (the whole Set is done only when)

- Orders 01..02 both executed.
- New-file producers emit `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` (research excepted) and
  `aw plan-names` (+ peers) validate it; both `.type.md` and bare `.md` still READ fine (dual-read).
- Every durable file in THIS repo's `.aw/records/` matches the grammar (research excepted).
- AGENTS.md documents exactly ONE filename grammar; vf03z3 tooling gaps closed; the optional
  rename-on-migrate nicety is captured as a follow-up backlog item (not a release blocker).
- Full serial suite green throughout; `aw attention --check` / `plans index --check` /
  `research index --check` / `specs check` / `backlog check` / `sanitize --agent` clean.
- Spec 20260817-2147-01 -> implemented; backlog 047ce9 -> done (release Blocker 2 cleared).

## Cross-IPD validation

- Order 01 (grammar + producers) MUST precede Order 02 (rename) so the renamed files match exactly
  what the validators/`aw plan-names` now expect. The free front-matter dual-read means both name
  shapes read fine at every point, so there is no broken intermediate. Re-run the full check suite
  after each Order.

## Deferred / out of scope (with reason)

- The next-version NUMBER (S6-V01): maintainer decision, Section 9.
- Run-artifacts naming (`.aw/workflow-artifacts/<workflow>/<RUN_ID>/`): keep the timestamp-dir convention (spec OUT).
- Research's internal `.<model>.<kind>.md` suffix: kept (the one principled exception).
- Directory taxonomy (spec 20260817-2124-01): already done (awretrofit Order 07).

## Scope check

- Over-scope: cut. An earlier draft had five micro-layer Orders; code investigation showed the
  readers are front-matter-driven (dual-read is free) so the surface collapses to two: ship the
  grammar (01) + dogfood-rename this repo (02). The migration rename is demoted to an optional
  follow-up backlog item (OQ-02), not an Order.
- Under-scope: none - Order 01 covers the 2 grammar regexes, the name generator, producers,
  `aw plan-names`, and `mv`; Order 02 covers this repo's rename + AGENTS.md + vf03z3. Research +
  run-artifacts + the version number are the documented exceptions.

## THIS-repo vs ALL-repos (pre-release framing - load-bearing)

Like the directory-taxonomy spec, the `.type.md` grammar has NOT shipped, so there is NO
released-name -> new-name migration to build. The two Orders differ in WHO they affect:

- **Order 01 (grammar regexes + name generator + producers + `plan-names`/`mv`):** ALL-REPOS. This is
  shipped code; every repo that installs the framework gets producers that EMIT `.type.md` and
  validators that ACCEPT it. Existing legacy repos are unaffected at rest: the record readers glob
  `*.md` and read metadata from front-matter, so bare-named files keep working with zero changes
  (dual-read is free, and therefore permanent) - no forced rename of a user's files.
- **Order 02 (rename this repo's ~267 files + docs):** THIS-REPO-ONLY. A one-time dogfooding cleanup
  of THIS framework repo's own records + AGENTS.md; it ships nothing and imposes nothing on others.
- **The migration rename (OQ-02, RESOLVED ask-then-offer):** because dual-read is free, a legacy
  `.agents/` repo migrates in one hop and its files keep working un-renamed. Renaming migrated files
  to the grammar is a pure nicety, so it is DEMOTED to a follow-up backlog item (opt-in
  `--rename-to-grammar`, default off, ask when interactive) - NOT a release blocker and NOT an Order.

## Required tests / validation

Per-Order V-items + the whole-Set completion criteria above; the orchestrator's E-01 verification
re-runs the full check suite + a legacy->final migration-name fixture after all Orders land.

## Open questions

### OQ-01: Do comms messages adopt `.comms.md`, or keep their envelope naming? (mirrors spec OQ-1)

- Blocking: no
- Status: open
- Owner: maintainer (resolve when Order 01/02 reaches comms)
- Resolution or deferral rationale: comms messages have an inbox/envelope/ack convention (comms.py)
  that may name files by routing rather than the artifact grammar. Decide at the comms-touching work
  whether `.comms.md` + the grammar fits or comms is a second documented exception like research. Not
  blocking the Set's start (Order 01's producer/grammar work is type-agnostic plumbing); resolve
  before renaming this repo's comms files (Order 02).

### OQ-02: Does `aw migrate-layout` RENAME legacy files to `.type.md`, or only dual-read? (RESOLVED: ask-then-offer; demoted to a follow-up backlog item, not an Order)

- Blocking: no
- Status: resolved
- Owner: human maintainer (2026-08-18)
- Resolution or deferral rationale: RESOLVED = ASK-then-OFFER. The shipped `aw migrate-layout`:
  (1) does NOT force-rename a user's existing legacy records by default (gentle);
  (2) when INTERACTIVE, ASKS the human whether to also rename the migrated records to the `.type.md`
  grammar (a self-contained P12 prompt);
  (3) when NON-INTERACTIVE, defaults OFF and supports an opt-in `--rename-to-grammar` flag for the
  uniform end-state.
  Consequence: **dual-read is PERMANENT and FREE** (the front-matter-driven readers already accept both
  bare `.md` and `.type.md`, since a not-renamed migrated repo keeps mixed naming indefinitely). THIS
  repo's own ~267 files are still fully renamed by Order 02 (dogfooding, independent of the shipped
  migration policy). The ask/flag/default-off rename transform is filed as a follow-up backlog item,
  not an Order in this Set.

## Validation and cross-check (verify before reporting the Set complete)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: both child Orders 01-02 show `Status: executed` under `.aw/records/plans/executed/`; the whole-Set completion criteria are demonstrated (paste: a producer emits a `.type.md` name, `aw plan-names` clean over this repo, an artifact-name grammar sweep showing every durable type on `.type.md`, AGENTS.md single-grammar, full serial suite + all `--check`s + sanitize); spec 20260817-2147-01 is `implemented`, backlog 047ce9 is `done`, and the optional rename-on-migrate follow-up backlog item exists.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: two Orders for one coherent objective (roll out the uniform naming grammar), split by AUDIENCE - Order 01 is the all-repos shipped grammar+producers, Order 02 is the this-repo dogfood rename+docs - so each is independently reviewable/executable and every intermediate state stays green via the free front-matter dual-read.

Execution requires human approval (`Status: approved` + attributed `- Approval:` line). The orchestrator
(opencode Opus 4.8) drives each child Order through its own lifecycle, owns all verification + path-scoped
commits, never pushes, and moves each Order (and finally this orchestrator) to `executed/` only after
`aw ipd lint --phase pre-transition` conforms and the V-items are verified with pasted evidence. On
completion advances spec 20260817-2147-01 to implemented + backlog 047ce9 to done (clearing release
Blocker 2). The version bake + any tag/publish are Section 9, human-gated. RELEASE BLOCKER 2.
