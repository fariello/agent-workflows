# Spec: clean up the `.aw/records/` taxonomy (run-artifacts, duplicate prompts, flatten docs/)

- Date: 2026-08-17
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: The maintainer, looking at the on-disk `.aw/records/` tree during release-review run 20260817-153418, found three structural problems: (A) workflow RUN-ARTIFACT dirs (`assess-*`, `verify`, `verify-execution`, `release-review`, `advise-*`) sit at the `.aw/records/` ROOT mixed in with durable tracked record types; (B) two confusingly-identically-named `prompts` dirs exist (`.aw/records/prompts/` staging vs `.aw/records/docs/prompts/` library); (C) the `docs/` sub-nesting (`.aw/records/docs/{research,specs,walkthroughs,roadmaps,prompts}`) is deeper than needed and the maintainer prefers a flatter `.aw/records/{research,specs,walkthroughs,roadmaps,...}`.
- Relation to prior work: REVISES the physical layout established by spec 20260810-1447-01 (`implemented`). This is a taxonomy refinement of the SAME `.aw/records/` record class, not a new storage backend.
- **RELEASE BLOCKER: this MUST be addressed before any release.** Shipping the `.aw/` layout with run-artifacts scattered at the records root, two identically-named `prompts` dirs, and the deeper-than-intended `docs/` nesting would bake a confusing, self-inconsistent taxonomy into the first release that carries the new layout - and (per Section 0) doing it AFTER release would then require the very legacy->intermediate->final migration hop we can avoid entirely by fixing it pre-release. The release-review Go/No-Go (run 20260817-153418) MUST treat this spec as an open blocker: NO-GO until it is implemented (or the maintainer explicitly waives it).

## Workflow history

- 2026-08-17 draft (opencode Opus 4.8 its_direct/pt3-claude-opus-4.8-1m-us): authored from a maintainer observation during release-review run 20260817-153418; captures problems A (run-artifacts at records root), B (duplicate prompts name), C (flatten docs/). Framed PRE-RELEASE (legacy->final migration only, no intermediate hop) and marked a RELEASE BLOCKER.

## 0. PRE-RELEASE FRAMING (READ FIRST - load-bearing simplification)

**This is ALL pre-release work.** The `.aw/` physical layout (spec 20260810-1447-01) has NOT shipped in
any released version: the intermediate `.aw/records/docs/{...}` shape exists ONLY in unreleased commits
on `main`. Therefore:

- **There is NO "current `.aw/records/docs/` layout -> new layout" migration to build.** The migration
  tooling (`aw migrate-layout`) only ever needs to support **legacy `.agents/` -> the FINAL layout**.
  Treat the intermediate `.aw/records/docs/{...}` shape as if it never existed publicly.
- Concretely: when this spec's IPD changes the target layout, it updates the migration's DESTINATION
  mapping (`.agents/docs/research` -> the new `.aw/records/research`, etc.) IN PLACE. It does NOT add a
  second migration hop, a `.aw/records/docs/` detector, or any "re-migrate an already-migrated repo"
  path. Any repo already on the intermediate shape is a DEV repo (this one) and is fixed by a one-time
  `git mv`, not by shipped migration code.
- This keeps the change small: it is a rename of destination constants + resolver targets + a one-time
  dev-repo `git mv`, NOT a new reversible migration.

## 1. One-line summary

Refine the `.aw/records/` taxonomy so (A) all ephemeral workflow run-artifacts live under ONE obvious
"aw-generated run outputs" subdirectory (not at the records root), (B) the two `prompts` concepts get
distinct names, and (C) the durable doc record types are flattened out of `docs/` to sit directly under
`.aw/records/`; and update the legacy->final migration DESTINATIONS accordingly (no intermediate-layout
migration, per Section 0).

## 2. Problem / motivation (facts observed on disk)

`.aw/records/` today (release-review run 20260817-153418) contains, at its ROOT:

- TRACKED durable record types: `backlog/`, `comms/`, `docs/` (with sub-types), `plans/`, `prompts/`.
- UNTRACKED + gitignored RUN-ARTIFACT dirs: `assess-bugs/`, `assess-documentation/`, `assess-secrets/`,
  `assess-self-documentation/`, `assess-testing/`, `advise-spec-editor/`, `release-review/`, `verify/`,
  `verify-execution/` (each a `<RUN_ID>/` tree of report.md/findings.csv/evidence.md/...).

Three problems:

- **A - run-artifacts at the records root.** These are ephemeral, gitignored (`.gitignore:68-72`)
  outputs of executing a workflow, NOT durable project records. Mixing them at the same level as
  `plans/`/`specs/` obscures the tree and makes "what is a durable record?" non-obvious. They ALSO
  duplicate a second, still-documented home: the shipped workflows write run records to
  `workflow-artifacts/<workflow>/<RUN_ID>/` (assess.md:135, verify.md:65, the release-review runbook),
  and a top-level `workflow-artifacts/` dir also exists. The awphysical migration additionally
  relocated the OLD `workflow-artifacts/` content INTO `.aw/records/{assess-*,verify,...}` and
  gitignores it there (`.gitignore` comment lines 63-72 + spec 20260810-1447-01). So there are TWO
  homes for the same class of thing and an internal inconsistency between the shipped workflow bodies
  (`workflow-artifacts/`) and the migrated layout (`.aw/records/<run>/`).

- **B - duplicate `prompts` name.** `.aw/records/prompts/` is the lifecycle STAGING tree
  (`pending/executed/reusable/superseded/not-executed/`, tracked, like plans - queued prompt files).
  `.aw/records/docs/prompts/` is an evergreen prompt LIBRARY (`fix-bar.md`,
  `older-general-qaqc-prompt-library.md`, ... - reference copy-paste prompts). Two different concepts,
  identical leaf name -> confusing. (`engine.py` even documents the distinction inline, which proves
  the collision is a known smell.)

- **C - unnecessary `docs/` nesting.** Durable doc record types are nested
  `.aw/records/docs/{research,specs,walkthroughs,roadmaps,prompts}`. The maintainer prefers them
  directly under `.aw/records/` for a flatter, more obvious tree.

## 3. Proposed target taxonomy (for review - see OQs)

A candidate FINAL `.aw/records/` layout (exact names are OQ-resolved in review):

```
.aw/records/
  backlog/                 # durable, tracked (unchanged)
  comms/                   # durable, tracked (unchanged)
  plans/                   # durable, tracked (unchanged)
  prompts/                 # lifecycle STAGING (unchanged root, keeps pending/executed/...)
  specs/                   # was docs/specs/        (flattened, C)
  research/                # was docs/research/      (flattened, C)
  walkthroughs/            # was docs/walkthroughs/  (flattened, C)
  roadmaps/                # was docs/roadmaps/      (flattened, C)
  prompt-library/          # was docs/prompts/       (renamed to break the collision, B) [name = OQ]
  runs/                    # was assess-*/verify/verify-execution/release-review/advise-* (A) [name = OQ]
    assess-<concern>/<RUN_ID>/
    verify/<RUN_ID>/
    release-review/<RUN_ID>/
    ...
  misc/                    # optional catch-all for durable docs with no typed home [OQ - may be dropped]
```

The maintainer's stated instinct for A: run-artifacts belong in a subdirectory whose name makes it
obvious they are "stuff `aw` created as part of executing some skill/workflow" (candidate: `runs/`,
`run-artifacts/`, or keep the top-level `workflow-artifacts/` as the single home and REMOVE the
`.aw/records/<run>` home entirely - see OQ-A1).

## 4. Goals

- G1 `[Must]` Run-artifacts (assess/verify/verify-execution/release-review/advise) have exactly ONE
  canonical home, obvious as "aw-generated run outputs", NOT scattered at the `.aw/records/` root.
  Resolve the `workflow-artifacts/` vs `.aw/records/<run>/` double-home inconsistency to a single answer
  and make the shipped workflow bodies + `.gitignore` + migration agree.
- G2 `[Must]` The two `prompts` concepts have distinct, self-explanatory names (staging vs library).
- G3 `[Must]` The durable doc record types are reachable at their agreed final paths (flattened per C
  unless review rejects it); `resolve_record_path`/`resolve_record_read_paths` and every consumer
  resolve the final paths.
- G4 `[Must]` The legacy `.agents/` -> FINAL migration destination mapping is updated IN PLACE (no
  intermediate `.aw/records/docs/` migration hop; Section 0). Legacy inputs (`.agents/docs/research`
  etc.) map directly to the final targets.
- G5 `[Must]` This dev repo is brought onto the final layout by a one-time `git mv` (tracked types) +
  directory move (untracked run-artifacts), with all resolvers/tests/docs updated so the suite is green.
- G6 `[Must]` The shipped docs Order 02 already corrected (AGENTS.md generator, index.md, workflow
  bodies, templates) are updated to the FINAL paths (e.g. `.aw/records/docs/research` ->
  `.aw/records/research`) so nothing regresses to the intermediate shape.
- G7 `[Must]` Stdlib only; no new migration ceremony; the change is destination-constant + resolver +
  one-time dev `git mv`, per Section 0.

## 5. Non-goals

- NOT building an intermediate-layout (`.aw/records/docs/`) -> final migration path (Section 0).
- NOT changing the four physical ROOTS (system/records/config/state) of spec 20260810-1447-01.
- NOT changing what any workflow DOES; only WHERE its records/run-outputs live.
- NOT re-opening the records-backend (repository/companion/home) decision.

## 6. Open questions (resolve in review)

### OQ-A1: run-artifacts home - `workflow-artifacts/` (top-level) OR `.aw/records/runs/`?
- Blocking: yes (determines the whole A fix). Two coherent options; pick one and make everything agree.
  (1) Keep the top-level `workflow-artifacts/` as the SINGLE home (what the shipped bodies already say),
  and DROP the `.aw/records/<run>` home + its gitignore lines + the migration-into-records-of-runs.
  (2) Make `.aw/records/runs/<workflow>/<RUN_ID>/` the single home, and update every workflow body +
  `workflow-artifacts/` references to it. Trade-off: (1) is less churn to shipped bodies and keeps run
  scratch out of `.aw/` entirely (arguably cleaner - `.aw/records/` becomes purely durable records);
  (2) consolidates everything under `.aw/`. Recommendation leans (1) unless there is a reason run
  outputs must live under `.aw/`.

### OQ-B1: name for the prompt LIBRARY (currently `.aw/records/docs/prompts/`)
- Blocking: no. Candidates: `prompt-library/`, `prompts-library/`, `reference-prompts/`. Must not
  collide with the staging `prompts/`.

### OQ-C1: flatten `docs/` entirely, or keep a `docs/` for a subset?
- Blocking: yes. Maintainer prefers flat `.aw/records/{specs,research,walkthroughs,roadmaps}`. Confirm
  no consumer relies on a `docs/` grouping, and decide whether a `misc/` catch-all is warranted or
  dropped.

### OQ-C2: is `misc/` a real need or scope creep?
- Blocking: no. Only add if there are durable docs with no typed home; otherwise omit (KISS, P6).

## 7. Acceptance criteria

- `.aw/records/` root contains only durable record types (agreed set); no `<RUN_ID>` run-artifact dirs
  at the root; run-artifacts have one documented home that the workflows, `.gitignore`, and migration
  all agree on.
- No two record subtrees share a confusing identical leaf name.
- `resolve_record_path`/read-paths + every consumer verb resolve the final paths; full serial suite green.
- `aw migrate-layout` maps legacy `.agents/*` DIRECTLY to the final paths (verified by the migration
  tests) with NO intermediate hop.
- This dev repo is on the final layout; `aw attention --check`, `aw plans index --check`,
  `aw sanitize --agent` clean; wheel ships the corrected bundle.

## 8. Sequencing note

This spec's IPD should run AFTER the in-flight awretrofit release-fix Orders that touch the same files
(Order 02 shipped-docs already executed; Orders 03-06 pending) OR be explicitly coordinated with them,
to avoid edit conflicts on the resolvers, migration, and shipped docs. The maintainer chose "fix A now,
defer B and C" for immediate action; this spec captures ALL THREE so the design is not lost, and the
IPD can be scoped to A-first with B/C as follow-on task groups if desired.
