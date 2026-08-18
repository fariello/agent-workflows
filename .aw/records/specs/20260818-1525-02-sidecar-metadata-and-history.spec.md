# Spec: sidecar administrative metadata (keep status inline, move history to a sidecar)

- Date: 2026-08-18
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Every record file (plan/spec/backlog/research/prompt) carries a `## Workflow history` narrative that grows unbounded. Agents that consume these files fully read + cache the entire body, so the history burns tokens on administrative narrative that provides little value to the task at hand (the maintainer specifically flagged history). The tension: moving admin metadata OUT of the file saves tokens but risks agents "forgetting" to use the tool and missing information. This spec resolves that tension with a middle path.
- Relation to prior work: Touches EVERY record type and the manifest/index layer (plans_index, research_index, specs, backlog, attention). Consumes the id6 handle (spec 20260808 plans-adopter) as the sidecar join key. Independent of, but sequenced after, the naming grammar (spec 20260817-2147-01).
- This is a DESIGN spec: it proposes the model for maintainer approval BEFORE any implementation. It is NOT a release blocker unless the maintainer marks it so; it is an efficiency + hygiene improvement.

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

## 3. Design options for the sidecar shape (for maintainer decision)

Two candidate shapes; the maintainer picks one at review (this is why it is a design spec):

- OPTION A - per-tree append-only JSONL: one `history.jsonl` per record tree (e.g. `.aw/records/plans/history.jsonl`), each line `{id6, date, workflow, actor, message}`. Pros: few files, cheap append, easy to scan for one id6. Cons: a single hot file per tree.
- OPTION B - per-record sidecar: `<recordname>.history.jsonl` next to each record (or under a shadow dir). Pros: co-located, moves/deletes with the record, no hot file. Cons: many small files, more git churn.

Recommendation: OPTION A (per-tree JSONL) - fewer files, matches the existing per-tree INDEX.json manifest pattern, and a record's history is retrieved by id6 filter. The record file keeps only inline state + the `Managed-by` directive.

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

### OQ-1: JSONL-per-tree (A) vs sidecar-per-record (B)?

- Blocking: yes
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: determines R1/R2. Recommendation A (per-tree JSONL). Maintainer to decide at spec review.

### OQ-2: keep a short inline history TAIL (latest N) or move it entirely?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: a 1-3 line "latest" tail in the file preserves at-a-glance context for an agent that does not call the tool, at a small token cost. Recommendation: keep the LATEST ONE line inline (the current state's provenance) + full log in the sidecar.

### OQ-3: is this a release blocker?

- Blocking: no
- Status: open
- Owner: maintainer
- Resolution or deferral rationale: Recommendation NOT a release blocker - it is an efficiency improvement, safe to ship in a follow-up. Maintainer to confirm so it can be sequenced after the UX batch.
