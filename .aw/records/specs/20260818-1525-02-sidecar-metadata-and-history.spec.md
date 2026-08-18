# Spec: sidecar administrative metadata (keep status inline, move history to a sidecar)

- Date: 2026-08-18
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Every record file (plan/spec/backlog/research/prompt) carries a `## Workflow history` narrative that grows unbounded. Agents that consume these files fully read + cache the entire body, so the history burns tokens on administrative narrative that provides little value to the task at hand (the maintainer specifically flagged history). The tension: moving admin metadata OUT of the file saves tokens but risks agents "forgetting" to use the tool and missing information. This spec resolves that tension with a middle path.
- Relation to prior work: Touches EVERY record type and the manifest/index layer (plans_index, research_index, specs, backlog, attention). Consumes the id6 handle (spec 20260808 plans-adopter) as the sidecar join key. Independent of, but sequenced after, the naming grammar (spec 20260817-2147-01).
- This is a DESIGN spec that proposes the model. All design decisions are now RESOLVED (Sections 3, 6). **RELEASE BLOCKER (maintainer-confirmed 2026-08-18):** implementation IPDs are authored after the release-critical UX Sets (A-F) but MUST land before the first `.aw/`-layout release.

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8): authored from a maintainer question during the 39-item pre-release review - whether admin metadata (status/history/disposition) should move to a sidecar `.json`. Maintainer chose the middle path (status inline, history to sidecar) and asked for a design spec kept OUT of the UX batch.

## 0. The tension (why a middle path)

- FULL sidecar (all of status+history+disposition in JSON, file carries only content): cleanest token story, but (a) highest "agent forgets the tool" risk, and (b) fights the current design where `aw attention`/`specs`/`backlog`/`plans_index` all parse `- Status:`/`- Set:`/`- Id:` from front-matter.
- ALL inline (status quo): no tool-skip risk, but the token-heavy history is always in the cached body.
- MIDDLE (this spec): keep the SMALL, high-value, frequently-needed fields inline (agents need Status/Set/Id/Order at a glance and to reason about a file); move the BULKY, low-per-read-value narrative (workflow history) to an append-only sidecar that `aw` owns. Captures ~90% of the token savings (history is the bulk) with far less tool-skip risk.

## 1. Goals

- G1. `- Status:`, `- Id:`, `- Set:`, `- Order:`, gate fields, and (for research) the frontmatter scalars STAY inline in the file (source of truth for state; small, high value).
- G2. `## Workflow history` narrative MOVES to an append-only per-record sidecar owned by `aw`. The file keeps at most a short pointer, not the full log.
- G3. `aw` reads/writes the sidecar transparently: `aw <verb> ... --message ...` appends to the sidecar, and a `history`-style verb reads it back.
- G4. A short front-matter directive on every managed file mitigates tool-skipping, e.g. a one-line `- Managed-by: aw (do not hand-edit status/history; use aw)`.
- G5. Backward-compatible read: a file that still carries an inline `## Workflow history` (legacy) is still valid; migration folds it into the sidecar.

## 2. Non-goals

- Moving status/disposition out of the file (they stay inline - G1).
- Changing the naming grammar or directory taxonomy.
- A networked/remote store; the sidecar is a local repo file.

## 3. Sidecar shape (DECIDED, maintainer 2026-08-18)

- **ONE GLOBAL append-only JSONL: `.aw/records/history.jsonl`**, keyed by id6, covering every record type. Each line is a JSON object `{id6, date, tree, workflow, actor, message}` (tree in {plans,specs,research,backlog,prompts,walkthroughs,roadmaps,releases,...}). Append-only, so line order is irrelevant and git merges of concurrent appends rarely conflict.
- Rationale: single reader/writer, trivial cross-tree "what happened to id6 X" and "everything on date D" queries, matches the id6-as-universal-handle model, and append-only JSONL neutralizes the write-hotspot concern. Simpler than per-tree or per-record.
- Records keep inline state (Status/Set/Id/Order/gate) + a `- Managed-by:` directive + the latest-one history line (OQ-2 below); the FULL chronological log lives only in `.aw/records/history.jsonl`.

## 4. Requirements (once a shape is chosen)

- R1. Define the sidecar schema + location (per the chosen option) and a reader/writer in a new module (e.g. `record_history.py`).
- R2. Route every status-transition writer (`specs set`, `backlog set`, the IPD lifecycle transition, `research` status changes) to ALSO append a sidecar history record, and STOP writing the growing inline `## Workflow history` (or keep only the latest N lines as a convenience tail - maintainer to decide).
- R3. A `history` read verb (or `aw show ... --history`) reads the sidecar for a given id6.
- R4. A migration that folds existing inline `## Workflow history` blocks into the sidecar, idempotently, preserving dates/actors.
- R5. Add the `- Managed-by: aw ...` front-matter directive to the record templates + a generator so new files carry it.
- R6. The manifest/index/attention/validators keep reading inline Status/Set/Id/Order (unchanged); only history moves.

## 5. Testable acceptance criteria

- AC1. Creating/transitioning a record appends exactly one sidecar history line and does NOT grow the inline body's history unbounded.
- AC2. The history read verb returns a record's full chronological history from the sidecar by id6.
- AC3. The migration folds a legacy inline-history file into the sidecar with no loss and is idempotent (re-running adds nothing).
- AC4. `aw attention`/`specs check`/`backlog check`/`index --check` still pass reading inline state (unchanged).
- AC5. A measurable token reduction on a representative record (history removed from the cached body).

## 6. Open questions

### OQ-1: sidecar shape? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: ONE GLOBAL `.aw/records/history.jsonl` keyed by id6 (Section 3). Maintainer chose global over per-tree/per-record for simplicity + cross-tree queries; append-only JSONL keeps conflicts rare.

### OQ-2: keep a short inline history TAIL? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: KEEP THE LATEST ONE line inline (the current state's provenance); full chronological log lives in `.aw/records/history.jsonl`.

### OQ-3: is this a release blocker? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: YES - the maintainer designated both this spec and the release-record spec (03) as RELEASE BLOCKERS for the first `.aw/`-layout release. Implementation IPDs are authored after the release-critical UX Sets (A-F) but before the release ships.
