# Spec: `.agents/` artifact organization (naming, identity, state, and archival at scale)

- Date: 2026-07-30
- Status: approved (2026-07-30, human maintainer) as the design basis for the research-organization IPD Set. Design rationale; the follow-on IPD Set implements it (research first). Open questions OQ1 to OQ6 (Section 10) are resolved within the Set's child IPDs.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Scope: a GENERAL principle for organizing the durable, growing artifact trees under `.agents/` (research, plans, prompts, comms, walkthroughs) so a human and an agent can answer "what did we find / decide about X?" and "what still needs attention?" cheaply and at scale. IMPLEMENTATION is scoped to `.agents/docs/research/` first; the other areas are named future adopters.

This spec is the load-bearing rationale document. It captures the problem, the measured evidence, the full criteria, the chosen design and WHY, the trade-offs considered, and the migration outline, so the follow-on IPD Set can be authored and reviewed against a single source of truth. It deliberately records reasoning, not just conclusions.

IMPORTANT framing: prior decisions are NOT canon. The conventions this spec revises (the `YYYYMMDD-HHMM-NN` grouping theory; GUIDING_PRINCIPLES P5's "never move research" carve-out; the founding docs-convention IPD's "research is free-form, no lifecycle" stance) were adopted months ago with no operational evidence. After months of use we have evidence, and this spec unwinds what did not work. Those prior artifacts are evidence of intent, not binding law.

---

## 1. Problem statement

An agent and a human both need to answer two questions cheaply:

- "What did we find when researching X?" (a TOPIC / provenance query)
- "What still needs to be addressed / ingested?" (an ATTENTION-STATE query)

Today neither is answerable at a glance. Answering them requires finding and reading many files, which is expensive in tokens and time for an agent and effectively impossible at a glance for a human. The trees are noisy, unindexed, and organized ad hoc (some files flat, some in topic subdirs), with no reliable signal for ingested-vs-not or keep-vs-discard.

The core objective (A1): reduce cold-start and per-turn agent load, and make the human's glance in the IDE tree meaningful.

## 2. Evidence (measured 2026-07-30 across the maintainer's ~35 repos with `.agents/`)

The growth is real and fast, and it is dominated by plans, not research:

- Heaviest repo surveyed: 179 plan files (75 in month 202606, 98 in 202607) -> ~85 plans/month in ONE area.
- Other active repos: 128 plans; this repo (agent-workflows) 109 plans + 70 research (46 research in a single month); 81 plans; 78 plans. (Repo names elided; the counts are the point.)
- Busiest single day (the heaviest repo's plans): 37 files on 20260628, 29 the next day; most other days 1 to 13. Work arrives in bursts.

Consequences that drive the design:

- Hundreds of files per area within about two months is the norm for active repos, so any scheme MUST scale to hundreds and then thousands.
- Monthly granularity is NOT enough for a heavy area (about 85 per month would put about 85 files in one month folder). See Section 7.
- The volume is bursty, so a fixed time window ("last two weeks") is unstable; a fixed COUNT window ("most recent N") is stable. See Section 6.
- The most acute pain is `plans/executed/` (179 files), not research (70). We implement for research first (smaller, self-contained, safe to dogfood) but the model is designed to lift to plans, which is the highest-value next adopter.

## 3. Criteria (objectives, needs, wants, constraints)

Marked `[Must]`, `[Want]`, `[Constraint]`. These are the acceptance criteria for any design and for the follow-on IPD Set.

### A. Primary objective
- A1 `[Must]` Reduce cold-start / agent load. Answering the two questions in Section 1 must not require reading many files.

### B. The three sub-jobs
- B1 `[Must]` Cheaply identify NOT-yet-ingested research without recursively reading the corpus, and without relying SOLELY on a hand-typed in-file status (proven unreliable; agents forget to update it).
- B2 `[Must]` Clear compartmentalization (active / kept-because-it-mattered / kept-just-in-case) discoverable without reading files.
- B3 `[Must]` Purpose legible to BOTH human and agent via filenames and/or directory structure (visible in the tree, not only inside files).

### C. Human environment constraints (load-bearing)
- C1 `[Constraint]` The human navigates an IDE file tree that sorts lexicographically by NAME, not by time, and cannot sort by mtime in the tree.
- C2 `[Constraint]` Clicking many files to discover what belongs together is unacceptable; grouping must be visual in the name-sorted tree.
- C3 `[Must]` Files that belong together must be visually adjacent/clustered in the name-sorted tree.
- C4 `[Must]` Grouping must be assignable AFTER THE FACT; we routinely discover "these N docs are a set" later, without churn or broken references. (This is WHY the `YYYYMMDD-HHMM` prefix failed: set members get different timestamps and do not cluster.)
- C5 `[Must]` Visual ordering WITHIN a group without sorting, especially where read/execute ORDER matters (a numbered position token).
- C6 `[Constraint]` Both human and agent mostly navigate via the IDE tree or by asking the agent, NOT by clicking path citations in files and NOT via raw shell `ls`. This lowers the weight of click-through citation ergonomics and raises the weight of tree legibility and agent queryability.

### D. Identity and citation
- D1 `[Must]` Every document is uniquely identifiable by a stable `<doc-id>` that survives moves and regrouping.
- D2 `[Must]` The id is greppable both as a filename fragment (`find -name '*<id>*'`) and as a word inside files (`grep -E '\b<id>\b'`); therefore the id is alnum/kebab-clean (no dots or slashes inside it).
- D3 `[Constraint]` Citations must survive a file moving between groups or state buckets; resolve via id plus manifest rather than fragile full paths.
- D4 `[Constraint]` The on-disk name must LEAD with something a human reads (date and/or descriptive slug); the id is present but not dominant. (`<id>-<slug>.md` alone is good for a tool, poor for a human.)

### E. Filename and grouping grammar
- E1 `[Want]` A structured grammar of the shape `YYYYMMDD-<set-id>-<NN>-<id>-<slug>[.<model>].<kind>.md`.
- E2 `[Must]` The `<NN>` token encodes read/execute ORDER within the set, not merely display order.
- E3 `[Must]` `<model>` and `<kind>` suffixes are REAL, enumerated vocabularies derived from the corpus (Section 5.4), standardized by a tool (e.g. normalize `gpt-56` to `gpt56`).
- E4 `[Must]` Support multi-file research SETS as a first-class unit (a prompt plus N per-model reports plus a reconciliation), and a SINGLETON is simply a set of one (no separate "standalone" concept).

### F. Tooling and token economy
- F1 `[Must]` Minimize model/token churn: anything achievable by implicit FS organization or a deterministic tool must NOT cost model tokens. No "send every doc back to the model to rebuild an index."
- F2 `[Must]` The manifest/index is tool-GENERATED from structured in-file frontmatter, not hand-maintained by an agent. This is what makes B1/B2 reliable despite the distrust of hand-typed status: a tool writes it (at creation) and a tool reads it.
- F3 `[Want]` A naming/creation tool emits the id, the standardized name, and starter frontmatter, so correct naming is a command, not a fallible convention.
- F4 `[Want]` The generator detects drift (stale citations, missing/invalid frontmatter, name-vs-frontmatter mismatch) so the FS and the index cannot silently diverge.
- F5 `[Want]` A rename/reference-updating tool: rename/move files and update references repo-wide, and highlight items that matched `\b<id>\b` but did NOT match the full-filename regex (a citation whose target moved/renamed = a dangling reference). Also finds docs whose references no longer resolve.
- F6 `[Must]` Token-economical tool ADOPTION: agents must prefer the tools without paying a large always-loaded AGENTS.md tax. Discovery must cost near-zero permanent tokens (progressive disclosure).

### G. Scope and reuse
- G1 `[Constraint]` This ships as a framework scaffold into every consumer repo plus an AGENTS.md directive, so it must be simple enough for a weak agent (e.g. a fast/small model) in someone else's repo to follow.
- G2 `[Must]` Keep the first IPD Set focused on `research/`, but design id/naming/grouping/tool/archival so they lift cleanly to `plans/` (especially the noisy `executed/`), `prompts/`, `comms/`, `walkthroughs/`. Track "everything else" as future work; do not build it now.
- G3 `[Constraint]` We are explicitly allowed to unwind prior decisions (Section 8).

### H. Tensions and their resolutions
- H1 One primary directory axis. For tree legibility a file lives in one directory, so only ONE axis can be encoded in the path. RESOLUTION: grouping is encoded in the FILENAME (set-id + NN), not a directory, so the working area stays FLAT and set-clustered; the only directory axis used is the time-shard for cold items (Section 7). Topic and state are frontmatter plus manifest, not directories.
- H2 Reliability of state. Hand-typed status is unreliable. RESOLUTION: a TOOL writes status at creation and reads it to build the manifest (F2); state is acceptable in frontmatter precisely because it is tool-owned, not hand-maintained.
- H3 Readable-first vs id-first name (D4). RESOLUTION: date and slug lead the name; the id sits after `<NN>` and is greppable but not dominant.

## 4. Design decisions and the reasoning behind each

### 4.1 Identity: a stable, greppable `<id6>`, decoupled from date and slug
Decision: each document gets a 6-character random alphanumeric id (about 2 billion combinations; collision-checked by the tool). It is the CITATION handle and never changes, even when the file is renamed, re-slugged, regrouped into a different set, or moved to a shard.

Why: the timestamp failed as an identity/grouping primitive (set members span days), and the slug is something we sometimes want to improve. A dedicated stable id decouples identity from both. It is word-boundary-clean so `grep -E '\bg7h8i9\b'` finds every reference in prose AND the file itself matches (verified: a `-` delimited id is bounded by `\b`). This satisfies D1/D2/D3.

Human-facing recency still comes from a leading `YYYYMMDD` in the name (the maintainer creates at most about 15 of a type per day, so date + a small per-day sequence stays meaningful), so the name is readable-first (D4) while the id carries identity.

### 4.2 Naming grammar
```
YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md
```
- `YYYYMMDD`: the SET's canonical date, shared by all members even if individual members were authored on adjacent days. The file's own creation date lives in frontmatter (`created:`) and git. Rationale: the human thinks in "when the investigation happened," not per-file mtime; a shared date is what clusters the set with the set-id.
- `<set-id>`: short kebab cohort key (explicit or tool-derived). This is the visual clustering key. A SINGLETON is a set of one (E4); there is no separate "standalone" concept or directory.
- `<NN>`: two-digit read/execute order within the set (E2/C5). `00` is the originating prompt (Section 4.6); `01..NN` are members; the reconciliation/synthesis is the last.
- `<id6>`: the stable citation id (4.1).
- `<slug>`: short descriptive kebab.
- `[.<model>]`: OPTIONAL authorship facet (4.4).
- `<kind>`: MANDATORY, enumerated (4.4).

Why filename-encoded grouping and not a `sets/` directory: the maintainer explicitly disliked a `sets/` vs `standalone/` split. Encoding `set-id` and `NN` in the name makes the lexical sort key `date -> set -> order`, so sets cluster and order is preserved in a name-sorted IDE tree with NO subdirectory (C1 to C5, H1). A worked stress test of 12 docs across 3 sets confirms clean clustering and ordering under lexical sort.

### 4.3 The `<set-id>` and after-the-fact grouping (C4)
A set is defined by its shared `YYYYMMDD-<set-id>`. Assigning a set later is a tool operation that renames the chosen files to share the set's date and set-id and assigns `NN` in a given order. Because the citation handle is `<id6>` (unchanged by the rename) and the rename/reference tool updates name-based references and flags danglers (F5), regrouping does NOT break citations. This is the capability the timestamp-prefix scheme could not deliver.

### 4.4 `<kind>` (mandatory) and `<model>` (optional authorship facet)
`<kind>` is always present and drawn from an enumerated vocabulary. `<model>` is present ONLY when authorship disambiguation matters, and always ALSO recorded in frontmatter (`model:`) so provenance is queryable even when omitted from the name.

Why `<model>` is conditional: the corpus survey (Section 5.4) shows the model token appears for three reasons: (a) TRUE multi-model comparison sets (same slug, several models, then a synthesis; e.g. `aw-delivery` and `host-probe` each have gpt56 + gemini36flash + gemini31pro + sonnet5 + a reconciliation); (b) single-author provenance worth recording; (c) a single model's iterative outputs. Most single-author research needs NO model token, which keeps the common name clean (D4). The tool adds it only when disambiguation matters, and normalizes spelling/position (the corpus has both `gpt56` and `gpt-56`, and the token appears both as a prefix in July 11 to 13 files and as a dotted suffix in the July 26 sets). The `new-comparison` verb scaffolds the whole multi-model pattern in one command (Section 5.3).

### 4.5 States: intake -> active -> reference -> archive (outcome-differentiated cold)
`status:` frontmatter, tool-owned (H2):

| State | Meaning | In hot INDEX.md glance? | On disk |
|-------|---------|-------------------------|---------|
| `intake` | landed, not yet triaged/ingested | Yes (the "needs addressing" band) | hot working area |
| `active` | informing in-flight work | Yes | hot working area |
| `reference` | cold BUT it mattered: informed a decision/design; durable provenance | Yes (subject to the most-recent-N window; the "why did we do X" corpus must not be buried) | weekly shard `reference/YYYYMM-Www/` |
| `archive` | cold AND just-in-case: dead-end, rejected option, superseded draft; kept only for the record | No (findable via INDEX.json + the shard catalog) | weekly shard `archive/YYYYMM-Www/` |

Why split cold into two by OUTCOME: "archive" was overloaded. Keeping something because it INFORMED us (provenance we will revisit) is a different job from keeping something JUST IN CASE (a dead-end we will almost never revisit). `reference` stays in the hot glance because "what mattered" must never be buried; `archive` is deep-shelved and excluded from the hot glance, which is precisely what keeps the glance small at hundreds of files. The finer `outcome:` facet (`adopted` / `informational` / `rejected` / `none-yet`) lives within these and is surfaced by the tool.

Caution recorded for the IPD: the reference-vs-archive judgment ("did it matter?") is human/agent CURATION, not tool-derivable. The tool may DEFAULT it (cited by a DECISIONS entry or plan -> reference; never cited and aged -> archive candidate) and MUST flag miscategorization (e.g. "this is in `archive/` but is cited by D107; should it be `reference`?"), but the final call is a recorded judgment. This is the one place the design relies on a recorded decision rather than a mechanical move, so the tool must make it a cheap, prompted, one-command act.

### 4.6 Prompt lineage (resolving the prompts/ vs research/ flip-flop)
A research prompt has two identities at two times: while queued/unrun it is an OPERATIONAL artifact (the `.agents/prompts/` pending -> executed lifecycle's job); once run it is the PROVENANCE of a research cohort. Resolution: the prompt is `NN=00` of its research set (it joins the cohort as the read-order-0 member), while the operational prompt queue stays separate for as long as the prompt is queued. The manifest records the linkage. This makes a set self-contained (prompt -> 01..NN reports -> reconciliation -> findings) without polluting the operational queue.

### 4.7 Manifest tiering (the hundreds-of-files answer)
Source of truth is each doc's FRONTMATTER. From it the tool generates:

| Artifact | Contains | Who reads it | Size |
|----------|----------|--------------|------|
| `INDEX.json` | EVERY doc (all states), the complete manifest | the TOOL (and agents via `aw research find`), never slurped whole | may be large; never model-read whole |
| `INDEX.md` | the most-recent-N (see 4.8) plus the intake band; includes `reference`; EXCLUDES `archive` | the human in the IDE; a weak agent that slurps it only pays for the small hot view | BOUNDED by N |
| shard catalogs (per `reference/` and `archive/` week, or a rollup) | terse listing of shelved items | rarely opened | grows slowly, out of the hot glance |

Principle (state it reusably): do NOT design assuming agents are smart about large files. Make the CHEAP path the DEFAULT path: a small bounded hot `INDEX.md`, tool-over-JSON for everything else, archive excluded from the glance. If an agent IS smart (offset reads, greps the id), it is even cheaper; if it slurps, it slurps only the small hot file.

### 4.8 Recency by COUNT, not TIME
`INDEX.md` shows the most recent N items (default configurable, about 30 to 50), where a set's recency = its last-touched date (most recent member added or status change), so an actively growing cohort stays visible even if its origin date is old. Rationale: work is bursty (Section 2), so a time window ("last two weeks") is unstable (empty in a lull, flooded in a burst) while a count window is stable and gives INDEX.md a predictable size and token cost (F1).

### 4.9 Directory shape and archival granularity: WEEKLY shards for BOTH reference and archive
- The HOT working area (`intake`/`active`) is FLAT and set-clustered by name (H1).
- BOTH `reference/` and `archive/` are sharded WEEKLY as `YYYYMM-Www/` (e.g. `202607-W30/`).

Why weekly (evidence-based; supersedes an earlier half-year and an earlier monthly lean): at about 85 items/month a MONTHLY shard holds about 85 files (the same noise one level down); weekly holds about 20 for a heavy user, which is scannable, and 1 to 4 for a light user. Both trees browse rarely and by "when," so a modest number of week folders is acceptable. `reference/` is sharded too (not left flat) because the maintainer expects `reference` to FAR outnumber `archive` (most research that mattered becomes long-lived provenance), so it is the corpus that most needs sharding; the hot glance stays bounded by the count window (4.8) regardless of how `reference/` is sharded on disk.

External-user note: a light user (5 to 15 items/month) gets few, sparse week folders in the cold shards, which is acceptable because those shards are opened rarely. The convention is the same across all `.agents/` areas so a user learns it once. (An adaptive split was considered and set aside in favor of a single, predictable weekly rule; revisit only if evidence shows weekly is wrong for real external usage.)

### 4.10 Archival trigger (deliberate, tool-executed, never a silent side effect)
- `aw archive [research] <set-id|doc-id>`: deep-shelve a specific set or doc (move to the appropriate `archive/YYYYMM-Www/`).
- `aw archive [research]` (bare): a deliberate SWEEP that archives candidates older than two weeks by default (age is the default SELECTOR for the bare command; `status` and explicit ids are the other selectors), always with a preview before moving, always on invocation. It is never a background or index-time side effect.
Promotion to `reference` is a distinct, deliberate "this mattered" act (4.5).

### 4.11 Token-economical tool adoption (F6)
Combine: (1) a THIN one-line AGENTS.md pointer ("to create/rename/index/archive research, use the `aw research` / `aw archive` verbs; do not hand-name or hand-maintain the index"); (2) a SELF-DOCUMENTING tool (`--help`, and self-revealing next-step output such as "created X; run `aw research index` to refresh"); (3) the DETAILED convention in the generated `research/README.md`, loaded only when an agent is working in that directory (progressive disclosure). Net: reliable discovery for near-zero permanent token cost. State this as a reusable principle for ALL future tools, not just research.

## 5. Tooling contract (the `aw research` and `aw archive` verb families)

### 5.1 `aw research new`
Inputs (explicit or tool-derived): `--set`, `--kind`, optional `--model`, `--slug`, `--summary`, `--topic`, optional `--date`. Behavior: resolve/derive the set (reuse an existing set's date + next `NN`, or create a new set at `NN=00`; omitted `--set` means a singleton derived from the slug); generate a unique `<id6>`; validate/normalize `--model` and `--kind` against the enumerated vocab; kebab-normalize `--slug`; emit the full path and WRITE starter frontmatter (`id`, `created`, `set`, `order`, `topic`, `model`, `kind`, `status: intake`, `summary`, `consumed-by: []`); print the next step (F6).

### 5.2 `aw research index [--check]`
Regenerate `INDEX.json` (all docs) and `INDEX.md` (most-recent-N + intake, reference included, archive excluded) FROM frontmatter. `--check` fails (nonzero) on drift: missing/invalid frontmatter, name-vs-frontmatter mismatch, a generated view out of date, or a dangling citation (F4). Suitable for a pre-commit or CI gate.

### 5.3 `aw research new-comparison`
Scaffold the multi-model pattern in one command: `--set <id> --slug <slug> --models gpt56,sonnet5,gemini31pro,gemini36flash` creates the prompt at `NN=00`, one report slot per model at `NN=01..N`, and reserves a `reconciliation-report` slot. Encodes "ask several models the same question, then synthesize" as first-class.

### 5.4 Enumerated vocabularies (grounded in the corpus, to be finalized in the IPD)
- `<model>`: `gpt56`, `gemini31pro`, `gemini36flash`, `sonnet5`, ... (normalize `gpt-56` -> `gpt56`; `chatgpt` is a product label to be mapped to a model version or recorded as provenance). `reconciliation` denotes a synthesis with no single author.
- `<kind>` (observed in the corpus): `research-prompt`, `research-report`, `reconciliation-report`, `findings`, `requirements`, `advisory`, `howto`, `concept`, `survey`, `source-draft`, `reference-research`, `assessment`, `notes`, `roadmap`, plus multi-part report parts (`executive-summary`, `test-evidence`, `patch-proposal`, ...). The IPD will fix the canonical closed-ish set and an extension mechanism.

### 5.5 `aw research find --id | --set | --topic | --status`
Token-cheap queries over `INDEX.json` (the answer to "what did we find re X" and "what needs addressing"), so the model never reads the corpus to answer them.

### 5.6 `aw research set-assign` / `aw research mv` (F5)
Regroup/rename after the fact: rename the target files to a set's `YYYYMMDD-<set-id>` and assign `NN`; update name-based references repo-wide; and REPORT any `\b<id6>\b` match whose surrounding filename no longer resolves (a dangling citation). `<id6>` never changes, so citations survive.

### 5.7 `aw archive [research] [<set-id|doc-id>]`
Per 4.10.

### 5.8 Frontmatter schema (authored/tool-written; the source of truth)
```
---
id: g7h8i9              # 6-char stable citation handle; never changes
created: 20260726       # this file's own creation date (git-first-commit fallback)
set: aw-delivery        # cohort key (assignable later)
order: 02               # read/execute order within the set (00 = originating prompt)
topic: [delivery, hosts, install]   # list; a doc may span topics
model: reconciliation   # authorship facet; present even when omitted from the name
kind: reconciliation-report
status: reference        # intake | active | reference | archive
outcome: adopted         # adopted | rejected | informational | none-yet
summary: One-line human summary shown in INDEX.md.
consumed-by: [D107, 20260723-1100-05]   # DECISIONS/plan ids that relied on this
---
```

## 6. Citation policy
Cite research by its `<id6>` (optionally `RSCH-<id6>`), resolved via the manifest; the file may live anywhere. The rename/reference tool (5.6) prevents silent rot by flagging id matches whose path no longer resolves. Full-path citations are permitted but discouraged; the drift check (5.2) reports stale ones. This REPLACES GUIDING_PRINCIPLES P5's "do not move research; keep the path stable" rule for the research area (Section 8).

## 7. General principle and future adopters (scope G2)
The model above (stable id + filename-encoded set/order + tool-generated tiered manifest + count-window hot glance + weekly cold shards + deliberate archival verbs + progressive-disclosure tool adoption) is written to apply to any growing `.agents/` artifact tree. Implementation order:
1. `research/` (this Set): smallest, self-contained, safe to dogfood.
2. `plans/executed/` (highest-value next adopter): the measured 179-file, ~85/month pain. Tracked in TODO.md.
3. `prompts/`, `comms/`, `walkthroughs/`: subsequent adopters.
Only research is BUILT now; the rest are named future work, not speculative structure (P6).

## 8. Prior decisions this spec revises (not canon)
- The `YYYYMMDD-HHMM-NN` grouping theory (D48/D50/D55 family): FAILED at grouping (set members span timestamps and do not cluster). Superseded by filename-encoded `set-id` + `NN` + a stable `<id6>`, with human recency from a leading `YYYYMMDD`.
- GUIDING_PRINCIPLES P5 research carve-out ("do not move research; cite by stable path; use a rare in-file Status"): revised. Research is now cited by `<id6>` via the manifest, which makes files freely movable between states/shards; P5's boundary text will be updated to describe cite-by-id + tool-maintained references instead of path immobility.
- The founding docs-convention IPD (`20260712-0033-01`) OQ2 lean "research is free-form reference, NOT a lifecycle artifact": superseded. Research gets a light, tool-owned lifecycle (intake/active/reference/archive) precisely because free-form did not scale.
The follow-on IPD will make these edits in place (P5 text, a short DECISIONS pointer entry) and record the supersession; it will not silently contradict the old text.

## 9. Migration outline (the accepted one-time cost)
For the 78 existing research files:
1. Assign each an `<id6>` and back-fill frontmatter (id, created from git-first-commit, set, order, topic, model, kind, status, outcome, summary, consumed-by inferred from existing DECISIONS/plan citations where possible).
2. Group existing cohorts into sets (the two dated bundles, the plan-review set, the opencode and opencode-security groups) and rename to the grammar; assign `NN`.
3. Normalize the `gpt-56`/`gpt56` and prefix-vs-suffix model-token drift.
4. Generate `INDEX.json` + `INDEX.md`; classify each doc's initial `status`/`outcome` (cited -> reference; uncited/dead-end -> archive candidate) as a reviewed pass, not a blind default.
5. Preserve citations: update in-repo references to the new names, and record the id so future moves are safe.
The migration is a discrete child IPD with its own validation (every old file accounted for; no dangling citation; INDEX regenerates clean).

## 10. Open questions and assumptions (to confirm before/within the IPD Set)
- OQ1: exact closed set of `<kind>` values and the extension mechanism (Section 5.4). Assumption: start from the observed corpus vocab and allow additions via the tool.
- OQ2: default N for the most-recent-N hot window (assumption: 30 to 50, configurable).
- OQ3: whether `INDEX.json` is committed or generated-on-demand-and-gitignored (assumption: commit `INDEX.json` and `INDEX.md` so a fresh clone and a weak agent have them without running the tool; the `--check` gate keeps them fresh). To confirm.
- OQ4: whether the leading `YYYYMMDD` is the set date only, or each file also keeps its own date somewhere visible (assumption: set date in the name, per-file `created:` in frontmatter).
- OQ5: `<id6>` length/alphabet final choice (assumption: 6 chars base36 lowercase, collision-checked).
- OQ6: whether `reference` shards live under `research/reference/YYYYMM-Www/` while `intake`/`active` stay at `research/` root, or all four states use an explicit subdir (assumption: hot states at root for glanceability, `reference/` and `archive/` sharded; confirm the exact paths in the IPD).

## 11. Next step
Per the agreed process: this spec is drafted and paused for HUMAN REVIEW. On approval, author an ORCHESTRATED IPD Set (a `00` orchestrator plus focused children: this spec's finalization; frontmatter schema + back-fill; the `aw research` tool; the tiered index generator; the rename/reference tool; migration of the 78 existing files; the archival mechanism; docs/AGENTS/installer scaffolding + P5/DECISIONS updates), scoped to `research/`, with `plans/executed/` named as the next adopter in TODO.md. Do NOT begin any IPD until this spec is approved.
