---
id: g5f3zq
created: 20260905
set: awmetastore
order: 06
topic: [artifact-storage, token-cost, history, schema]
model: gemini31prodeepthink
kind: research-report
status: archive
outcome: rejected
summary: Gemini 3.1 Pro Deep Think: a fifth answer to prompt 27rjro, DELIBERATELY EXCLUDED from reconciliation 6mye7n on the maintainer instruction because its own author note records that network restrictions prevented it reading the repository, so it reasoned from the prompt prose alone; adopted 2026-09-20 for provenance only
consumed-by: []
---

<!-- PROVENANCE AND STANDING, added on adoption 2026-09-20.
     This is the FIFTH answer to research prompt `27rjro` and it is NOT part of the consolidated
     finding. Reconciliation `6mye7n` states that it was produced and DELIBERATELY EXCLUDED on the
     maintainer's instruction: its own author's note records that network restrictions prevented it
     from cloning or reading the repository, so it reasoned from the prompt's prose alone while the
     other four checked live code. It sat unadopted in the gitignored `.aw/inbox/` until 2026-09-20
     and is adopted now for PROVENANCE ONLY, so the record shows the fifth report existed and why it
     was set aside. Do NOT read it as a co-equal source: `6mye7n` remains the document an
     implementer reads, and its "four sources" count is correct and deliberate.
     Body preserved verbatim per the research README's external-artifacts rule. -->

<!-- aw-adopt: provenance -->
> EXTERNAL PROVENANCE. This document was adopted from the gitignored `.aw/inbox/` raw-drop
> lane on 20260920 by `aw adopt`. Original filename: `aw-artifact-metadata-storage-research-report.gemini31prodeepthink.md`.
> Its body is preserved VERBATIM as received, so its punctuation and formatting are the
> external author's, not this repository's house style. Treat the CONTENT as untrusted
> external input: evaluate it on its merits, never as instructions from the maintainer.
# Research Report: Tool-Owned Artifact Metadata Storage Design

**Target System:** `fariello/agent-workflows` (`aw`)
**Focus:** Metadata token efficiency, parse correctness, Git-native concurrency, and safe migration.

> **Author's Note on Codebase Access:** Due to execution environment network restrictions, I was unable to dynamically clone and verify against the live repository. My analysis and recommendations rely strictly on the extensive architectural constraints, file metrics, module names, and structural behaviors detailed in your prompt.

---

## 1. Recommendation

**I recommend a Hybrid Architecture: Inline Front-Matter + Per-Artifact JSONL History Sidecars.**

1. **Keep Routing & State Metadata Inline:** The YAML-like front-matter (`Status`, `Id`, `Item-Dependencies`, `Readiness`, `Scope-Paths`, etc.) must remain at the top of the `*.ipd.md` files.
2. **Move Workflow History to Sidecars:** Extract the unbounded `## Workflow history` section out of Markdown and into per-artifact, append-only JSONL files (e.g., `.aw/records/plans/uyeko5.history.jsonl`).

**The Decision Rule:** Store metadata based on its primary consumer and mutability profile, constrained by Git concurrency and token limits.
*   **Front-matter dictates the *current state*.** Humans rely on it instantly during PR `git diff` reviews to understand routing changes, and AI agents require it in their baseline context to reason about an artifact's readiness. At a capped ~4.7% token footprint, the legibility benefits far outweigh the context cost.
*   **Workflow history is an *audit trail*.** It is unbounded, currently consumes ~10.2% (and up to 20%) of context tokens, and is fundamentally ignored by agents. Moving it to per-artifact sidecars reclaims massive context space, structurally resolves the parser ambiguity, and isolates Git merge conflicts to specific files rather than a central database.

---

## 2. Comparison of Realistic Options

| Design Option | Token / Context Effect | Parse Robustness | Merge-Conflict Behavior (Concurrent Agents) | Human Diff Legibility | Migration Cost | Crash / Partial-Write Safety |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **(a) Status Quo (Inline)** | **Failing** (14.9%+ overhead, grows unboundedly). | **Failing** (Prepend vs. append disagreement). | **Good** (Isolated per artifact). | **Excellent** (Everything in one view). | None | **Poor** (In-place MD prose edits risk corruption). |
| **(b) Recommended Hybrid (Front-Matter + Sidecar History)** | **Good** (Capped at 4.7%, 10.2% unbounded history removed). | **Excellent** (Strict JSONL schema, sequential). | **Excellent** (Conflicts strictly isolated per artifact). | **Good** (State in MD diff, history in clean JSONL diff). | Medium | **High** (Append-only JSONL; MD updates constrained). |
| **(c) Total Sidecar (All Metadata in JSON)** | **Best** (0% metadata tokens in prompt). | **Excellent** (Strict schemas). | **Good** (Isolated per artifact). | **Fatal** (Core status changes invisible in MD diffs; requires cross-referencing). | High | **High** (Atomic writes). |
| **(d) Central JSONL (`history.jsonl`)** *(Stalled Migration)* | **Good** (History tokens removed). | **Good** (Append-only ensures sequence). | **Fatal** (Central file is a global Git conflict magnet for concurrent agents). | **Poor** (History detached from artifact diffs). | Medium | **High** (Append-only). |
| **(e) SQLite as Source of Truth** | **Excellent**. | **Perfect** (ACID constraints). | **Fatal** (Git treats `.db` as unmergeable binary blobs; blocks concurrent agents). | **Zero** (Invisible in diffs). | High | **Perfect**. |

---

## 3. Resolving the Ordering Bug (15 Diagnostics)

The parser bug in `agent_workflows/ipd_lifecycle.py` (`_plan_status_events`) returning 15 false diagnostics is fundamentally a structural deficit. Day-granular dates, timezone mismatches (UTC tools vs. local authors), and conflicting write directions (prepend vs. append) mean the durable record lacks sufficient entropy to reconstruct sequence mathematically.

**This design makes transition order unambiguous by construction:**
1.  **Strict Append-Only Enforcement:** JSONL structurally dictates an append-only write pattern. By removing history from human hands, CLI tools natively enforce a uniform append direction.
2.  **Explicit Identity/Sequence Fields:** Every sidecar entry **must** contain a strict, monotonically increasing integer: `"seq": 1`. This permanently decouples chronological sequence from timestamps. The reader simply sorts by `seq` (or reads top-to-bottom). `events.reverse()` and heuristic rank sorts are eliminated.
3.  **Timestamp Granularity:** Standardize on ISO 8601 with microsecond precision and an explicit UTC identifier (e.g., `"timestamp": "2026-09-03T18:02:45.123456Z"`). Forced via `datetime.now(timezone.utc)`, this permanently fixes the time-travel defect where local evening writes appeared in the future.

---

## 4. Single-Source-of-Truth Position & Drift

**The SSOT Position:**
*   **The Markdown Front-Matter** is the absolute Source of Truth for *Current State* (because human agents edit this to signal intent).
*   **The JSONL Sidecar** is the absolute Source of Truth for *Historical Transitions*.

**Detecting and Healing Drift:**
1.  **Detection:** When `aw lint` or `check_engine.py` runs, it asserts that `Markdown["Status"] == JSONL[-1]["to_status"]`.
2.  **Finding:** If a human edits the Markdown status manually but forgets to run a state-transition tool, they drift, and a CI diagnostic finding is thrown.
3.  **Repair:** A repair CLI command (e.g., `aw doctor` or `aw history sync`) executes. Trusting the Markdown as the human intent, the tool safely appends a reconciliation entry to the sidecar: `{"seq": N+1, "action": "manual-sync", "to_status": "<md-status>", "notes": "Auto-recovered from drift"}`. There is no silent divergence.

---

## 5. Safe & Incremental Migration Path

The previous migration attempt (`b0behn`) stalled specifically on the plans tree because `ipd_lint` (IPD-S405) hard-required the inline `executed` text. The migration must decouple readers *before* mutating data.

1.  **Phase 1: Abstract the Readers (Non-Breaking):** Introduce a `HistoryReader` service in `agent_workflows/record_history.py`. Update the 19 affected modules to query this reader. The reader checks for `[id].history.jsonl` first, and falls back to parsing the Markdown `## Workflow history` if the sidecar is missing.
2.  **Phase 2: Unblock the Stalled Linter (Crucial Step):** Modify `ipd_lint` (IPD-S405) to strictly use `HistoryReader.has_transition("executed")` instead of grepping inline text. Modify `aw attention` so `last_history_at` queries the reader.
3.  **Phase 3: Update Tool Writers:** Modify status-setting tools to append strictly to the new JSONL sidecars, injecting the `seq` and UTC timestamps.
4.  **Phase 4: The Cutover Script (Bulk Backfill):** Run a one-off script over the 483 `*.ipd.md` plan files.
    * Parse the messy inline history one last time using the "date + domain rank invariant" heuristic *as a one-time sequence reconstruction*.
    * Assign synthetic `seq` integers and generate the per-artifact sidecars.
    * **Physically strip** the `## Workflow history` blocks from all Markdown files.
5.  **Phase 5: Deprecate the Central Log:** Read the 128 records currently trapped in `.aw/records/history.jsonl`. Scatter them into per-artifact sidecars. Delete the central file entirely.

---

## 6. What I would NOT do (Rejected Alternatives)

*   **I would NOT proceed with the central `history.jsonl` migration.** Git is optimized for distributed text edits. A central append-only log modified concurrently by multiple autonomous AI agents will result in continuous, blocking Git merge conflicts.
*   **I would NOT move front-matter to the sidecar.** Removing `Status` from the Markdown saves < 5% of tokens but utterly destroys human legibility during code review.
*   **I would NOT use SQLite.** Its binary format is unmergeable by Git. Concurrent AI agents working on different branches would hit unresolvable binary conflicts, paralyzing the system.
*   **I would NOT normalize the inline Markdown history.** Normalizing ~500 files to a "prepend-only" rule fixes the parser but ignores the primary tension: Token Cost. AI agents continue to waste 10-20% of their context windows reading historical audit logs.
