# Spec: uniform artifact-naming grammar with a `.type.md` suffix across `.aw/records/`

- Date: 2026-08-17
- Status: implemented
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Today the record types name their files inconsistently: plans/specs/research use an id6-bearing clustered name, but prompts/backlog/comms/walkthroughs/roadmaps do not all share one grammar, and only specs carry a type suffix (`.spec.md`). The DIRECTORY carries the type, so two dirs named `prompts` (staging vs library) are indistinguishable at a glance - actively hostile to a reader who pattern-matches on the word (the maintainer flagged this as a recurring, dyslexia-aggravating confusion). Moving the TYPE signal into the filename (`.prompt.md`, `.ipd.md`, ...) makes every artifact self-identifying regardless of its directory, greppable/sortable by type, and robust to being moved to the wrong place.
- Relation to prior work: BUILDS ON the Set-clustering filename grammar (`YYYYMMDD-<set-id>-NN-<id6>-<slug>.md`) already used by plans/specs/research and documented in AGENTS.md; EXTENDS it to all durable record types and adds a `.type.md` suffix. Companion to spec 20260817-2124-01 (the DIRECTORY taxonomy cleanup): that spec fixes WHERE artifacts live, this spec fixes HOW they are NAMED. Absorbs the tooling gaps captured in backlog vf03z3.
- **RELEASE BLOCKER (maintainer-confirmed 2026-08-17):** this MUST be addressed before the first `.aw/`-layout release. It is a naming-CONTRACT change; doing it pre-release avoids a future rename migration (same logic as spec 20260817-2124-01 Section 0). The release-review Go/No-Go (run 20260817-153418) is NO-GO until this spec is implemented (or explicitly waived). Separable from the directory-taxonomy blocker (spec 20260817-2124-01) - both block.

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer proposal during release-review run 20260817-153418. Contract details settled interactively (type-token set, standalone shape, run-artifact scope). Separated from the directory-taxonomy spec 20260817-2124-01 per the maintainer.
- 2026-08-18 to-review (aw specs): Completed for review; drove the awnaming Set IPDs.
- 2026-08-18 reviewed (aw specs): Reviewed via /plan-review of the awnaming orchestrator + Orders 01/02 (APPROVE WITH REVISIONS APPLIED).
- 2026-08-18 approved (aw specs, --by-human): Human approved the awnaming Set ('Approved. Go, one after the other.', 2026-08-18) which implements this spec.
- 2026-08-18 implementing (aw specs): awnaming Set executing (Orders 01, 02).
- 2026-08-18 implemented (aw specs): Implemented by awnaming Set: Order 01 f8e6y7 at 0f8a861, Order 02 975whv at f0ddd40; comms + research documented exceptions; suite 1021 passed 1 skipped.

## 0. PRE-RELEASE FRAMING

Like spec 20260817-2124-01: the `.aw/` layout has NOT shipped. If this lands pre-release, it is a
one-time rename of dev-repo files + a change to how PRODUCERS name new files + a legacy `.agents/` ->
final NAME mapping in the migration - NOT a released-name -> new-name migration hop. Treat any existing
non-conforming names as dev-only and fix by a one-time `aw plans mv`-style rename.

## 1. One-line summary

Adopt ONE artifact-naming grammar for every durable `.aw/records/` type -
`YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` - where `<type>` is a per-type token
(`ipd`/`prompt`/`spec`/`walkthrough`/`roadmap`/`backlog`/`comms`), research keeps its richer
`.<model>.<kind>.md` convention as the one principled exception, and run-artifacts keep their
`<RUN_ID>/` timestamp-dir convention (out of scope).

## 2. The grammar

```
YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md
```

- `YYYYMMDD` - creation date (local).
- `<setid>` - the Set id for Set members; for a STANDALONE (non-Set) artifact, the item's own `<id6>`
  is the setid (a singleton set), so a lone item reads `YYYYMMDD-<id6>-NN-<id6>-<slug>.<type>.md` with
  `NN=01` (mirrors how `aw backlog` already derives "a singleton from the item id"). (OQ-resolved.)
- `NN` - two-digit order within the Set (`00` reserved for an orchestrator, `01+` otherwise);
  `01` for a standalone singleton.
- `<id6>` - the stable 6-char base36 id (the artifact's `- Id:`), in the filename.
- `<slug>` - lowercase kebab-case.
- `.<type>.md` - the type suffix (below).

### 2.1 Type tokens

| Type | Suffix | Note |
|---|---|---|
| Plan / IPD | `.ipd.md` | (was bare `.md`) |
| Prompt | `.prompt.md` | staging AND library items are `.prompt.md` |
| Spec | `.spec.md` | ALREADY the convention (no change) |
| Walkthrough | `.walkthrough.md` | |
| Roadmap | `.roadmap.md` | |
| Backlog item | `.backlog.md` | |
| Comms message | `.comms.md` | (if comms files adopt the grammar; see OQ) |
| Research | `.<model>.<kind>.md` | **EXCEPTION**: keep the existing richer convention (encodes model+kind, more than a type token; forcing `.research.md` would lose information). (OQ-resolved.) |

## 3. Scope

- IN: durable `.aw/records/` types (plans, prompts [staging + library], specs, walkthroughs, roadmaps,
  backlog, comms), the producers that create them (`aw ipd scaffold`, prompt creation, `aw backlog new`,
  `aw research new` [research keeps its convention], spec authoring), the parsers/resolvers/indexers
  that read them, `aw plan-names` (validate the grammar), the legacy `.agents/` -> final NAME mapping
  in `layout_migration.py`, and the shipped docs/AGENTS.md that describe names.
- OUT (OQ-resolved): run-artifacts under `.aw/workflow-artifacts/<workflow>/<RUN_ID>/` keep their
  timestamp-dir convention (ephemeral, grouped by run, not individually id6-addressable). Research's
  internal suffix. The four physical roots. Directory taxonomy (spec 20260817-2124-01).

## 4. Goals

- G1 `[Must]` One documented grammar `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` for all in-scope types,
  with the standalone-singleton rule and the research exception explicit.
- G2 `[Must]` Every PRODUCER emits the conforming name by default (`aw ipd scaffold` -> `.ipd.md`,
  prompt creation -> `.prompt.md`, `aw backlog new` -> `.backlog.md`, etc.). This subsumes the vf03z3
  finding that `aw ipd scaffold` did not derive the canonical name.
- G3 `[Must]` Every PARSER/resolver/indexer reads the new names (and, pre-release, the dev-repo files are
  renamed once so nothing is orphaned). Plans/specs/research indexers keep working.
- G4 `[Must]` `aw plan-names` (and equivalent for other types) VALIDATES the grammar incl. the
  `.type.md` suffix and flags divergence (subsumes the vf03z3 "plan-names does not flag divergence").
- G5 `[Must]` `aw plans mv`/`aw research mv` rename to the grammar AND preserve `- Order:` (fixes the
  vf03z3 "mv clobbers Order to 0" bug); scaffold+mv agree on the canonical name.
- G6 `[Must]` The legacy `.agents/` -> final migration maps to the final NAMES (no released-name
  migration hop; Section 0).
- G7 `[Must]` AGENTS.md + shipped docs reconcile the two conflicting documented grammars (AGENTS.md
  line 26 Set-clustering vs line 51 lifecycle `YYYYMMDD-HHMM-NN-<slug>`) to this ONE grammar
  (subsumes the vf03z3 AGENTS.md-grammar finding).
- G8 `[Must]` Stdlib only; Python 3.9; ships in the package.

## 5. Non-goals

- NOT changing directory locations (spec 20260817-2124-01).
- NOT renaming run-artifacts.
- NOT changing research's internal `.<model>.<kind>.md` convention.
- NOT building a released-name -> new-name migration (pre-release, Section 0).

## 6. Open questions

### OQ-1: do comms messages adopt the grammar, or keep their envelope naming?
- Blocking: no. Comms messages have an envelope/ack convention (comms.py) that may already name files
  differently (inbox routing). Decide whether `.comms.md` + the grammar fits or comms is a second
  documented exception like research.

### OQ-2: is this a release blocker? [RESOLVED]
- Blocking: no (resolved). Maintainer confirmed 2026-08-17: YES, pre-release release blocker (avoid a
  later name migration). Tracked via blocked backlog + the release-review Go/No-Go.

### OQ-3: `.gitkeep`/`README.md`/`INDEX.*`/`STATUS.md` are NOT artifacts.
- Blocking: no. Confirm the grammar applies only to artifact files, not to the structural
  `README.md`/`.gitkeep`/generated `INDEX.json`/`INDEX.md`/`STATUS.md` (they keep their fixed names).

## 7. Acceptance criteria

- Every in-scope durable artifact filename matches `YYYYMMDD-<setid>-NN-<id6>-<slug>.<type>.md` (research
  excepted); `aw plan-names` (+ peers) validate it and flag divergence.
- Producers emit conforming names by default; `aw plans mv` preserves `- Order:`.
- Indexers/resolvers read the new names; full serial suite green.
- Legacy `.agents/` fixtures migrate to the final names directly.
- AGENTS.md documents exactly ONE grammar; the vf03z3 tooling gaps are closed.

## 8. Sequencing

Runs AFTER (or coordinated with) the directory-taxonomy spec 20260817-2124-01 / Order 07, since both
touch the migration mapping, resolvers, and shipped docs. Recommend: land Order 07 (dirs) first, then
this naming grammar, so files are renamed once into their final directories. This spec supersedes the
lightweight backlog vf03z3 (fold its four tooling gaps into G2/G4/G5/G7); vf03z3 can be closed as
"promoted to this spec" once this is approved.
