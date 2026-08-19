# Spec: sidecar administrative metadata (keep status inline, move history to a sidecar)

- Date: 2026-08-18
- Status: draft
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Every record file (plan/spec/backlog/research/prompt) carries a `## Workflow history` narrative that grows unbounded. Agents that consume these files fully read + cache the entire body, so the history burns tokens on administrative narrative that provides little value to the task at hand (the maintainer specifically flagged history). The tension: moving admin metadata OUT of the file saves tokens but risks agents "forgetting" to use the tool and missing information. This spec resolves that tension with a middle path.
- Relation to prior work: Touches EVERY record type and the manifest/index layer (plans_index, research_index, specs, backlog, attention). Consumes the id6 handle (spec 20260808 plans-adopter) as the sidecar join key. Independent of, but sequenced after, the naming grammar (spec 20260817-2147-01).
- This is a DESIGN spec that proposes the model. All design decisions are now RESOLVED (Sections 3, 6). **RELEASE BLOCKER (maintainer-confirmed 2026-08-18):** implementation IPDs are authored after the release-critical UX Sets (A-F) but MUST land before the first `.aw/`-layout release.

## Workflow history

- 2026-08-18 draft (opencode Opus 4.8): authored from a maintainer question during the 39-item pre-release review - whether admin metadata (status/history/disposition) should move to a sidecar `.json`. Maintainer chose the middle path (status inline, history to sidecar) and asked for a design spec kept OUT of the UX batch.
- 2026-08-18 note (aw specs): spec-editor pass (opencode Opus 4.8): added Users/scenarios + Constraints/dependencies sections, tagged requirements MUST/SHOULD; fixed stale/verb-coupled items (02 R2/AC1 latest-one + plans/IPD-S405 exclusion; 03 R5/AC3 -> check_blocks_release engine function not the aw check verb).

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

## 2.1 Users / actors and scenarios

- **Coding agent (primary beneficiary):** reads a record file and caches its full body. Today the unbounded `## Workflow history` narrative is dead weight in that cache. Scenario: an agent opens a plan to reason about its CURRENT state - it needs Status/Set/Id/Order (inline, kept) but not 15 lines of transition prose (moved to the sidecar). When the agent DOES need history, it calls `aw record-history <id6>`.
- **`aw` tooling (writer):** `specs set` / `backlog set` transition a record and must record provenance; they now append one line to the global sidecar and keep only the latest-one inline.
- **Maintainer (human):** wants an at-a-glance "how did this reach its current state" (the latest-one inline line) without the file bloating over time, and a full audit trail on demand.
Key flow: state stays inline (cheap, always-needed); the growing narrative lives in one queryable append-only log.

## 2.2 Constraints and dependencies

- The front-matter PARSERS (plans_index, specs, backlog, research_contract) and the attention `last_history_at` derivation (attention_contract.py:434, which reads the LAST inline record's date) MUST keep working unchanged - this is why the latest-one inline line is retained (R6/AC4).
- PLANS/IPD `## Workflow history` is a HARD CONSTRAINT EXCLUSION: `ipd_lint` IPD-S405 (ipd_lint.py:666) requires an inline `executed` history entry at post-transition, so plan/IPD history MUST NOT be slimmed or moved by this work. The sidecar covers non-plan record types; the IPD lifecycle owns plan history. (IPD/research writer routing is a deliberate follow-up, not this spec's initial scope.)
- Depends on the id6 handle (spec 20260808 plans-adopter) as the sidecar join key, and is sequenced after the naming grammar (spec 20260817-2147-01). The store is a LOCAL repo file (`.aw/records/history.jsonl`), no network.
- Append-only JSONL is chosen so concurrent-append git merges rarely conflict (a single global file otherwise risks a write hotspot).

## 4. Requirements

(MUST = required; SHOULD = strongly preferred.)

- R1 (MUST). Define the sidecar schema + location (Section 3: `.aw/records/history.jsonl`, line `{id6,date,tree,workflow,actor,message}`) and an append/read module `record_history.py`.
- R2 (MUST). Route the specs + backlog status-transition writers (`specs set`, `specs note`, `backlog set`) to ALSO append one sidecar history record, and SLIM the inline `## Workflow history` to the LATEST ONE record line (OQ-2 resolved: latest-one, not N). The IPD lifecycle transition + research status writers are a DOCUMENTED FOLLOW-UP, NOT this spec's initial scope, and plans/IPD history is never slimmed (Section 2.2 constraint).
- R3 (MUST). A history read verb (`aw record-history <id6>`; NOTE `aw history` collides with the existing action-lifecycle verb) reads the sidecar for a given id6, chronologically.
- R4 (MUST). An idempotent migration folds existing inline `## Workflow history` blocks into the sidecar (preserving dates/actors) then slims to latest-one - EXCLUDING the `plans` tree (IPD-S405 constraint).
- R5 (SHOULD). Add the `- Managed-by: aw ...` front-matter directive to the record templates + a generator so new files carry it (mitigates tool-skipping).
- R6 (MUST). The manifest/index/attention/validators keep reading inline Status/Set/Id/Order + the latest-one history line (unchanged behavior); only the FULL history log moves.

## 5. Testable acceptance criteria

- AC1. Transitioning a specs/backlog record appends exactly one sidecar history line AND slims its inline `## Workflow history` to a single (latest) record line.
- AC2. The `aw record-history <id6>` verb returns a record's full chronological history from the sidecar.
- AC3. The migration folds legacy inline-history into the sidecar with no loss and is idempotent (re-running adds nothing).
- AC4. `aw attention --check` / `aw specs check` / `aw backlog check` / `aw index ... --check` still pass, and `attention` `last_history_at` still resolves from the retained latest-one inline line.
- AC5. A representative slimmed record is measurably smaller (history removed from the cached body).
- AC6. Plans/IPDs are UNTOUCHED: every executed plan still carries its inline `executed` `## Workflow history` entry and passes `aw ipd lint --phase post-transition` (IPD-S405). The migration does not fold or slim the `plans` tree.

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
