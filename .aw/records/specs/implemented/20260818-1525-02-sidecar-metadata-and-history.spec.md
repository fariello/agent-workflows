# Spec: sidecar administrative metadata (keep status inline, move history to a sidecar)

- Date: 2026-08-18
- Status: implemented
- Author: opencode Opus 4.8 (its_direct/pt3-claude-opus-4.8-1m-us)
- Motivation: Every record file (plan/spec/backlog/research/prompt) carries a `## Workflow history` narrative that grows unbounded. Agents that consume these files fully read + cache the entire body, so the history burns tokens on administrative narrative that provides little value to the task at hand (the maintainer specifically flagged history). The tension: moving admin metadata OUT of the file saves tokens but risks agents "forgetting" to use the tool and missing information. This spec resolves that tension with a middle path.
- Relation to prior work: Touches EVERY record type and the manifest/index layer (plans_index, research_index, specs, backlog, attention). Consumes the id6 handle (spec 20260808 plans-adopter) as the sidecar join key. Independent of, but sequenced after, the naming grammar (spec 20260817-2147-01).
- This is a DESIGN spec that proposes the model. All design decisions are now RESOLVED (Sections 3, 6). **RELEASE BLOCKER (maintainer-confirmed 2026-08-18):** implementation IPDs are authored after the release-critical UX Sets (A-F) but MUST land before the first `.aw/`-layout release.

## Workflow history

- 2026-09-22 note (aw specs): AMENDED by plan vhbvwz (setterguard Order 02) per the maintainer's 2026-09-10 ruling: OQ-2's latest-one inline slimming is SUPERSEDED, and inline history is now the DURABLE home for specs and backlog items, matching plans. Six passages amended: OQ-2 (original reasoning preserved as superseded, not deleted), R2, R6, AC1, AC4, and the Section 2.2 citation, which both miscited the last_history_at derivation's location as attention_contract.py:434 and stated its LAST-record behavior as a property to protect - that behavior was itself the defect, since every writer PREPENDS, and it misreported 373 of 679 multi-record plans, 153 of 200 backlog items and 8 of 21 specs. The sidecar is retained as a machine-local activity log (Section 3, R1, R3, AC2 untouched); a failed sidecar write is now reported rather than swallowed. Status deliberately UNCHANGED at implemented: the only legal transitions from there are deferred/superseded, and this is a text amendment, not a lifecycle move.
- 2026-08-19 implemented (aw specs): Implemented by the awhistory Set (global history.jsonl sidecar + writer routing + inline slimming + migration excluding plans + aw record-history verb); suite 1079 passed 1 skipped.
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
- **Additive RENAME/regroup record (IPD 52zgqr, unifyfileio Order 04).** Every applied `aw rename`/`aw group` that changes a name appends ONE record that is a SUPERSET of the status line: the same `{id6,date,tree,workflow,actor,message}` keys plus `verb` (rename|group), `from_name`/`to_name` (basenames), and `key_kind` (`id6` for id6->id6 and id6-less->id6, keyed on the (new) id6; `synthetic` for both-id6-less, keyed on a deterministic normalized-name token). It is strictly ADDITIVE and NON-AUTHORITATIVE: no `aw` command's correctness depends on it (id6 already guarantees citation stability and git already records moves), the emit is failure-isolated (a ledger error never fails a rename), and status readers/the inline-history migration key only on id6/date/message and ignore the extra keys. Read via `record_history.read_renames_for(key)`.

## 2.1 Users / actors and scenarios

- **Coding agent (primary beneficiary):** reads a record file and caches its full body. Today the unbounded `## Workflow history` narrative is dead weight in that cache. Scenario: an agent opens a plan to reason about its CURRENT state - it needs Status/Set/Id/Order (inline, kept) but not 15 lines of transition prose (moved to the sidecar). When the agent DOES need history, it calls `aw record-history <id6>`.
- **`aw` tooling (writer):** `specs set` / `backlog set` transition a record and must record provenance; they now append one line to the global sidecar and keep only the latest-one inline.
- **Maintainer (human):** wants an at-a-glance "how did this reach its current state" (the latest-one inline line) without the file bloating over time, and a full audit trail on demand.
Key flow: state stays inline (cheap, always-needed); the growing narrative lives in one queryable append-only log.

## 2.2 Constraints and dependencies

- The front-matter PARSERS (plans_index, specs, backlog, research_contract) and the attention `last_history_at` derivation MUST keep working unchanged.
  **AMENDED 2026-09-22 (plan `vhbvwz` E-02/E-07), AND THE ORIGINAL TEXT HERE WAS WRONG IN BOTH HALVES.** As authored this line said the derivation lives at `attention_contract.py:434` and "reads the LAST inline record's date". The LOCATION was wrong (`:434` is inside the `TRANSITION_AUTHORITY` table; the derivation was at `:610`), and the BEHAVIOR it described as a thing to protect was itself the defect: every writer PREPENDS, so the section is NEWEST-FIRST and the last record in file order is the OLDEST one. Measured over this repository at `2362b102`, the last-record rule reported a date that was not the artifact's newest record for 373 of 679 multi-record plans, 153 of 200 backlog items and 8 of 21 specs. The rule is now single-sourced in `attention_contract.newest_history_record` (the FIRST matching record of the bounded section), which `last_history_at` and `plan_readiness.extract_newest_history_entry` both consume, so the two readers that used to implement opposite rules can no longer disagree. The derivation is therefore NOT the reason to retain a single inline line, and R2/R6/AC1/AC4 are amended accordingly.
- PLANS/IPD `## Workflow history` is a HARD CONSTRAINT EXCLUSION: `ipd_lint` IPD-S405 (ipd_lint.py:666) requires an inline `executed` history entry at post-transition, so plan/IPD history MUST NOT be slimmed or moved by this work. The sidecar covers non-plan record types; the IPD lifecycle owns plan history. (IPD/research writer routing is a deliberate follow-up, not this spec's initial scope.)
- Depends on the id6 handle (spec 20260808 plans-adopter) as the sidecar join key, and is sequenced after the naming grammar (spec 20260817-2147-01). The store is a LOCAL repo file (`.aw/records/history.jsonl`), no network.
- Append-only JSONL is chosen so concurrent-append git merges rarely conflict (a single global file otherwise risks a write hotspot).

## 4. Requirements

(MUST = required; SHOULD = strongly preferred.)

- R1 (MUST). Define the sidecar schema + location (Section 3: `.aw/records/history.jsonl`, line `{id6,date,tree,workflow,actor,message}`) and an append/read module `record_history.py`.
- R2 (MUST). Route the specs + backlog status-transition writers (`specs set`, `specs note`, `backlog set`, `backlog note`) to ALSO append one sidecar history record, and PRESERVE the full inline `## Workflow history`, newest-first.
  **AMENDED 2026-09-22 (maintainer ruling 2026-09-10, plan `vhbvwz` OQ-01 / E-08).** As authored this requirement said to SLIM the inline history "to the LATEST ONE record line". That is REVERSED: the inline block keeps every record, newest-first, exactly as plans already do. The premise the slimming rested on does not hold - `.aw/.gitignore` ignores `.aw/records/history.jsonl`, so the sidecar is PER-MACHINE and the slimmed records did not survive a clone; measured, three `aw specs note` records from the 2026-09-10 setid cleanup existed ONLY there. The IPD lifecycle transition + research status writers remain a DOCUMENTED FOLLOW-UP, and plans/IPD history was never slimmed (Section 2.2 constraint), so all three types now share ONE durability model.
- R3 (MUST). A history read verb (`aw record-history <id6>`; NOTE `aw history` collides with the existing action-lifecycle verb) reads the sidecar for a given id6, chronologically.
- R4 (MUST). An idempotent migration folds existing inline `## Workflow history` blocks into the sidecar (preserving dates/actors) then slims to latest-one - EXCLUDING the `plans` tree (IPD-S405 constraint).
- R5 (SHOULD). Add the `- Managed-by: aw ...` front-matter directive to the record templates + a generator so new files carry it (mitigates tool-skipping).
- R6 (MUST). The manifest/index/attention/validators keep reading inline Status/Set/Id/Order + the inline history.
  **AMENDED 2026-09-22 (plan `vhbvwz` E-07).** As authored this said they keep reading "the latest-one history line" and that "only the FULL history log moves". Neither holds now: the full log STAYS inline (R2 as amended), and the readers take the NEWEST record of the section rather than a single retained line. `last_history_at`'s behavior did change, deliberately and in the corrective direction: it now reports the newest record's date instead of the last line's (Section 2.2 as amended).

## 5. Testable acceptance criteria

- AC1. Transitioning a specs/backlog record appends exactly one sidecar history line AND prepends exactly one record to its inline `## Workflow history`, leaving every prior record in place.
  **AMENDED 2026-09-22 (plan `vhbvwz` E-07/E-08).** As authored this criterion required the inline block to be slimmed "to a single (latest) record line"; it now requires the opposite, for the reason recorded at R2. Pinned by `tests/test_history_routing.py` (`test_backlog_set_appends_sidecar_and_preserves_inline`, `test_specs_preserves_inline`).
- AC2. The `aw record-history <id6>` verb returns a record's full chronological history from the sidecar.
- AC3. The migration folds legacy inline-history into the sidecar with no loss and is idempotent (re-running adds nothing).
- AC4. `aw attention --check` / `aw specs check` / `aw backlog check` / `aw index ... --check` still pass, and `attention` `last_history_at` resolves to the NEWEST inline record's date on a multi-record section.
  **AMENDED 2026-09-22 (plan `vhbvwz` E-02/E-07).** As authored this said the derivation "still resolves from the retained latest-one inline line", which stopped being meaningful once the block keeps many records - and was already wrong for plans, which were never slimmed. A single-record fixture cannot tell the two candidate rules apart (its first and last record coincide), which is why the contradiction survived this spec's own review; the criterion now demands a NEWEST-FIRST multi-record case, pinned by `tests/test_attention_contract.py::HistoryTests::test_newest_first_section_yields_its_newest_record`.
- AC5. A representative slimmed record is measurably smaller (history removed from the cached body).
- AC6. Plans/IPDs are UNTOUCHED: every executed plan still carries its inline `executed` `## Workflow history` entry and passes `aw ipd lint --phase post-transition` (IPD-S405). The migration does not fold or slim the `plans` tree.

## 6. Open questions

### OQ-1: sidecar shape? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: ONE GLOBAL `.aw/records/history.jsonl` keyed by id6 (Section 3). Maintainer chose global over per-tree/per-record for simplicity + cross-tree queries; append-only JSONL keeps conflicts rare.

### OQ-2: keep a short inline history TAIL? RESOLVED, THEN SUPERSEDED 2026-09-10

- Blocking: no
- Status: resolved (superseded)
- Owner: maintainer (2026-08-18; superseded by the maintainer 2026-09-10)
- Resolution or deferral rationale (ORIGINAL, 2026-08-18, PRESERVED AS SUPERSEDED - do not delete): KEEP THE LATEST ONE line inline (the current state's provenance); full chronological log lives in `.aw/records/history.jsonl`.
  THE ORIGINAL REASONING IS KEPT BECAUSE IT STILL CONSTRAINS THE DESIGN. The slimming was a considered decision, not an accident, and its motivation was concrete: `aw attention`'s `last_history_at` derivation reads the inline block, so exactly one line was retained specifically to keep that derivation working. Any future change to inline history must still satisfy that reader, which is why the record of WHY latest-one was chosen stays here rather than being erased.
- **SUPERSEDING RESOLUTION (maintainer, 2026-09-10; implemented by plan `vhbvwz` E-08, 2026-09-22): KEEP THE FULL INLINE HISTORY for specs and backlog items, newest-first, matching what plans already do.**
  WHY THE ORIGINAL PREMISE FAILED. This question's answer rested on "the full chronological log lives in `.aw/records/history.jsonl`". It does not, for anyone but the machine that wrote it: `git check-ignore -v .aw/records/history.jsonl` resolves to `.aw/.gitignore`, so the sidecar is gitignored and does not survive a clone. Every record the slimming dropped was therefore destroyed rather than relocated. Measured consequence on this repository's own work: three `aw specs note` calls during the 2026-09-10 setid cleanup recorded substantial reasoning that existed ONLY in the sidecar, while each spec showed exactly one inline record - which `AGENTS.md` forbids outright, since an answer must never live only in a gitignored tree.
  WHAT DECIDED IT. Tracing the CALLERS rather than the writers showed the sidecar is written by nine deliberate record-keeping actions and that `status_set.py` writes to it ZERO times, so plan history was ALREADY inline, already version-controlled, and already protected by `ipd_lint` IPD-S405. The August decision left specs and backlog on a different durability model from plans, and that split was the actual defect. One model - the one that already worked - is the answer.
  THE SIDECAR IS NOT REMOVED. It remains a machine-local, cross-tree ACTIVITY LOG read by `aw record-history <id6>` (Section 3, R1, R3 and AC2 are untouched). It is simply no longer the durable store, so a failed sidecar write can never cost a record; that failure is now REPORTED rather than swallowed (`record_history.append_advisory`).
  THE ORIGINAL CONSTRAINT WAS HONORED, BY FIXING THE READER FIRST. Keeping more than one inline line was only safe once `last_history_at` genuinely meant "newest", so plan `vhbvwz` corrected that derivation (E-02) BEFORE changing either writer (E-08); see Section 2.2 as amended for the measurement. Landing them in the other order would have made every multi-record spec and backlog item report its OLDEST date.

### OQ-3: is this a release blocker? RESOLVED

- Blocking: no
- Status: resolved
- Owner: maintainer (2026-08-18)
- Resolution or deferral rationale: YES - the maintainer designated both this spec and the release-record spec (03) as RELEASE BLOCKERS for the first `.aw/`-layout release. Implementation IPDs are authored after the release-critical UX Sets (A-F) but before the release ships.
