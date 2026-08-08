# Spec: artifact organization, plans adopter (generalize the core; apply to `.agents/plans/`)

- Date: 2026-08-08
- Status: approved (2026-08-08, human maintainer) as the design basis for the plans-adopter IPD Set. Design rationale; the follow-on IPD Set implements it. Open questions OQ1 to OQ5 (Section 8) are resolved.
- Implemented: SHIPPED as DECISIONS D124 via the executed plans-adopter IPD Set (orchestrator `20260808-0004-00` plus children `...-01..07`, in `.agents/plans/executed/`). This spec remains the standing design reference; the executed Set and its walkthrough carry the execution record. The Section 9 "next step / do NOT begin until approved" note below is historical.
- Author: opencode (its_direct/pt3-claude-opus-4.8-1m-us)
- Parent: `.agents/docs/specs/20260730-2152-01-agents-artifact-organization.spec.md` (the research-org
  design, now shipped as DECISIONS D123). This companion spec CORRECTS and EXTENDS the parent's
  Section 7 "future adopters" claim for `.agents/plans/`, records the design decisions that the
  parent deferred, and captures reasoning that was reached in discussion but never written down.
- Scope: a GENERALIZATION of the shipped research-org machinery into an area-agnostic core, plus the
  concrete design for the FIRST reuse of that core: `.agents/plans/`. Implementation is a follow-on
  IPD Set. `prompts/`, `comms/`, `walkthroughs/` remain named future adopters (Section 8).

This spec is the load-bearing rationale document for the plans adopter. It records the problem, the
recovered reasoning, the chosen design and WHY, the corrections to the parent spec, the migration
outline, and the open questions, so the follow-on IPD Set can be authored and reviewed against a
single source of truth.

---

## 1. Problem statement

`.agents/plans/executed/` is the measured worst case for artifact noise (parent spec Section 2:
about 179 plan files in the heaviest surveyed repo, about 85 plans/month; this repo has 116 in
`executed/` today). The parent spec named `plans/executed/` the highest-value next adopter of the
research-org model but deferred the actual plans design to "plan-adoption time." Two concrete needs:

- A1 (browse-by-topic): a human and an agent both want to answer "what plans did we do about X?"
  (install-safety, agent-comms, ipd-structure, ...) at a glance, not only by scanning dates.
- A2 (bounded hot glance): the flat `executed/` directory grows without bound; the working view
  must stay small.

## 2. Recovered reasoning (why plans need MORE than a bare manifest)

A fresh session initially proposed a REDUCED subset for plans (manifest + `--check` + weekly cold
shards + an archival verb), arguing plans do NOT need a stable id because (a) plans are cited by
their `YYYYMMDD-HHMM-NN` stem which is stable across `git mv` between disposition dirs, (b) plans
already carry rich `ipd_schema` metadata a research frontmatter block would duplicate, and (c)
executed plans are immutable history that must not be re-slugged.

That reduced conclusion is correct ONLY if executed plans are NEVER regrouped into after-the-fact
topic sets. The maintainer decided (2026-08-08) that regrouping IS wanted. This is decisive, and it
is the same failure mode the parent spec Section 8 recorded for research: a timestamp-led filename
welds identity to a date, so related files cannot be clustered by topic in a name-sorted tree after
the fact. Plans have the identical timestamp-led stem, so they inherit the identical failure the
moment topic-clustering is wanted. The `id6` remedy therefore applies to plans too.

Crucial discovery that shapes the design: plans ALREADY carry topic grouping in their `- Set:`
metadata (70 of the executed plans have a `Set:`; e.g. `install-safety-and-ownership`=7,
`ipd-structure`=7, `research-org`=8). The gap is not missing grouping; it is that (i) the grouping is
INVISIBLE in the name-sorted tree (filenames lead with a per-plan timestamp, so Set members do not
cluster), and (ii) it is UNINDEXED (`STATUS.md` groups by disposition, not by Set). So the plans
adopter REUSES `Set:`/`Order:` as the grouping key rather than inventing a new one; the new work is
surfacing that grouping in the tree + a manifest, and making Set reassignment/rename safe via a
stable id.

## 3. Corrections to the parent spec (what does and does NOT transfer)

The parent spec (Section 7) says "the model above ... is written to apply to any growing `.agents/`
artifact tree" and lists the whole model. In practice, only PART transfers verbatim; the identity and
metadata layer is area-specific because `ipd_schema` (which did not exist when the parent spec was
written) already owns plan metadata.

TRANSFERS (becomes a shared area-agnostic core, reused by research and plans):
- the `id6` primitive (6-char base36 lowercase; word-boundary + citation matchers);
- the weekly-shard date math (`YYYYMM-Www`);
- the dangling-citation detector shape;
- the tiered-manifest + `--check` drift-gate shape (INDEX.json all + a bounded human view);
- the deterministic writing-command safety pattern (preview by default, `--apply`, atomic write,
  tracked `git mv`);
- the deliberate archival verb pattern.

DOES NOT transfer verbatim (area-specific for plans):
- NO research-style frontmatter block. The stable id lives as a single `- Id:` line in the EXISTING
  `ipd_schema` metadata block, avoiding collision with `Set:`/`Order:`/`Status:`/`Kind:`/watermark.
- NO research `<kind>`/`<model>`/`status`/`outcome` vocab. Plans keep the `ipd_schema` kinds
  (child/orchestrator) and the `plans.py` readiness `Status:` + disposition dirs.
- Grouping key is the EXISTING `Set:`/`Order:`, not a new one.
- Tooling stays in the plans family (`aw plans` / `aw ipd`), NOT `aw research`. One id CONCEPT across
  areas (shared core) does not mean one verb surface; the verbs remain area-native so agents keep the
  mental model they already have for plans.

## 4. Design decisions

### 4.1 Shared area-agnostic core
Extract the TRANSFERS list (Section 3) into a core module (working name
`agent_workflows/artifact_core.py`) that `research_contract` and the new plans code both import. No
behavior change for research (its public API is preserved; internals delegate to the core). This is
the "learn one id concept once" + future cross-area-query enabler, without forcing a single verb
surface.

### 4.2 Stable plan `Id`
Each plan carries a `- Id: <id6>` line in its metadata block (same 6-char base36 grammar as research,
from the shared core). It NEVER changes across renames/regrouping and is the citation handle that
makes clustering safe. `ipd_schema` gains `Id` as a REQUIRED metadata field (OQ2; linter-enforced for
all plans, the migration backfills every existing plan, nothing grandfathered); `aw ipd
scaffold`/`sync` emit it.

### 4.3 Set-clustering filename grammar
Executed (and pending) plans adopt a Set-leading grammar so Set members cluster in a name-sorted
tree: `<YYYYMMDD>-<set-id>-<NN>-<id6>-<slug>.md`. `Set:`/`Order:` remain the source of truth in
metadata; the filename mirrors them. Orchestrator stays `NN=00`.

The `<set-id>` is SHORT/TERSE (a compressed cohort key, like the research migration's `awdeliv`,
`chkplace`, `ocsec`), NOT the full slug; the `<slug>` is the longer descriptive name. A SINGLETON is
a set of one and is NEVER special-cased (uniform grammar for all plans, so filename symmetry holds
and adding a second member later needs no cascade rename). The terse set-id for the 9 existing plan
Sets and the singletons is hand-picked (explicit, per parent spec 4.2's "explicit or tool-derived").

The `- Set:` METADATA carries BOTH forms: `Set: <terse-id> (<descriptive name>)`, e.g.
`Set: researchorg (research-org)`, `Set: instsafe (install safety and ownership)`. The leading
whitespace-delimited token before any `(` is the canonical set-id (parsed by the manifest, refs, and
archival tools and matching the filename `<set-id>` exactly); the parenthetical is a human-readable
display name shown in the manifest. This removes any divergence between the terse filename token and
the descriptive Set name, and prose Set-name mentions in DECISIONS/TODO are left untouched (no fuzzy
prose rewriting). The tools ignore the parenthetical when reading the set-id.

### 4.4 Plans manifest + browse-by-Set + `--check`
A generated `INDEX.json` (every plan, all fields incl. disposition + Set + Order + Id + resolved
path) and a browse-by-Set human view (complements, does not replace, the existing disposition-grouped
`STATUS.md`). `aw plans index --check` fails on drift (missing/invalid `Id`, name-vs-metadata
mismatch, stale generated view, dangling plan citation), analogous to `aw research index --check` and
`aw ipd lint`. This is a candidate pre-commit/CI gate (shares the deferred `aw ipd lint` hook
question, OQ4).

### 4.5 Regroup / rename verb
`aw plans set-assign <id...> --set <s> [--rename]` and `aw plans mv <id> [...]`: (re)assign a plan's
`Set:`/`Order:` and OPTIONALLY rename it to the clustering grammar, keeping `Id` stable and rewriting
citations by the stable id. Reuses the shared dangling detector to flag danglers. Writing-command
safety per Section 3.

### 4.6 Weekly cold shards inside the terminal disposition dirs + archival
Each COLD/terminal disposition dir (`executed/`, `superseded/`, `not-executed/`) gains weekly
`YYYYMM-Www/` shards (OQ3). The HOT tier (`pending/`) and the STANDING tier (`reusable/`) stay flat. A
deliberate `aw plans archive` verb (targeted + an aged sweep with per-item preview, mirroring `aw
archive` for research) moves aged plans into the shards of their disposition dir. Disposition dirs
remain the coarse lifecycle; the shard layer is the fine-grained cold storage within each terminal
dir.

### 4.7 One-time migration (mandatory dry-run + STOP gate)
A one-time script (like research-org Order 06) assigns an `Id` to every plan, renames all executed
(and pending) plans to the clustering grammar, and rewrites the THREE plan-citation forms:
1. full filename (exact-string) - straightforward;
2. bare stem `YYYYMMDD-HHMM-NN` (no slug/`.md`) - rewritten via an old-stem -> new-name map built
   from the rename table;
3. range shorthand `` `<stem>`..`NN` `` citing a whole Set - expanded/rewritten specially.
It regenerates the manifest. It MUST produce the full dry-run mapping + citation-rewrite diff and STOP
for human review BEFORE applying, and verify every old plan is accounted for and moves are tracked git
renames. This accepts a one-time churn on files otherwise treated as immutable history; the CONTENT
and append-only workflow history of each plan are preserved verbatim (only the name and the added `Id`
line change), and the tradeoff is recorded as the deliberate cost of topic-clustering.

### 4.8 Immutable-history reconciliation
"Executed plans are immutable history" is narrowed (as P5 was narrowed for research in D123): the
BODY and workflow history of an executed plan stay immutable; its NAME and grouping become mutable via
the stable `Id`. The migration is the one sanctioned mass-rename; routine post-migration regrouping is
a deliberate, tool-driven, citation-safe act.

## 5. What this deliberately does NOT do
- Does not impose a research frontmatter block on plans (Section 3).
- Does not unify the verb surface into `aw research` (verbs stay area-native, Section 4.1).
- Does not adopt prompts/comms/walkthroughs (Section 8).
- Does not change the readiness `Status:` vocabulary or the disposition-dir lifecycle.

## 6. Prompts, comms, walkthroughs (future adopters)
Per the parent spec Section 7 and the recovered reasoning, prompts are the WEAKEST case: low volume,
an existing pending/executed lifecycle, filenames already the stable stem, and the research-prompt
lineage already handled (parent 4.6). A prompts adopter, if wanted, is its own small later Set. Comms
and walkthroughs likewise. This spec does not design them.

## 7. Migration outline (the accepted one-time cost)
For all plans (about 116 executed + a few pending):
1. Assign each an `Id` (`- Id:` metadata line); collision-checked.
2. Rename to the clustering grammar (Section 4.3); tracked `git mv`.
3. Build the old-stem -> new-name map; rewrite the three citation forms (Section 4.7).
4. Regenerate the plans manifest; `aw plans index --check` clean afterward.
5. Preserve content + workflow history verbatim; no dangling citation remains.
Discrete migration child IPD with its own validation (every old plan accounted for; no dangling cite;
manifest regenerates clean; moves are git renames).

## 8. Resolved questions (settled with the maintainer 2026-08-08)
- OQ1 (RESOLVED): the clustering filename grammar is `<YYYYMMDD>-<set-id>-<NN>-<id6>-<slug>.md`;
  `HHMM` is dropped. The leading date is the plan's date; `set-id`+`NN` come from the existing
  `Set:`/`Order:` metadata; `id6` is the stable handle; `slug` is the descriptive kebab. REFINED at
  the Order-06 STOP gate (2026-08-08): `<set-id>` is SHORT/TERSE (hand-picked, like `awdeliv`), NOT
  the full slug; singletons are never special-cased (uniform grammar); the `- Set:` metadata carries
  `<terse-id> (<descriptive>)` with the leading token as the canonical set-id (see Section 4.3).
- OQ2 (RESOLVED): `Id` is REQUIRED for all plans. `ipd_schema` makes `- Id:` a required metadata
  field (linter-enforced); the migration backfills every existing plan; nothing is grandfathered.
- OQ3 (RESOLVED): ALL cold disposition dirs shard weekly, not only `executed/`. `executed/`,
  `superseded/`, and `not-executed/` each gain `YYYYMM-Www/` shards; `pending/` (and `reusable/`)
  stay flat as the hot/standing tiers. (Update Section 4.6 accordingly: the shard layer applies to
  every terminal disposition dir.)
- OQ4 (RESOLVED): ship HOOK-LESS initially. The plans `aw plans index --check` gate is invoked BY
  the workflows (`plan-review`, `ipd-lifecycle`), which carry the obligation, exactly as `aw ipd
  lint` does today (D122; the pre-commit hook for it was deliberately deferred as a v1 follow-up). A
  pre-commit/CI hook is a SEPARATE later defense-in-depth item, shared with the existing deferred
  leak-sanitizer / `aw ipd lint` hook-wiring follow-up (one `setup-repo`-installed, off-by-default
  hook that agents are made aware of even when absent) rather than a second hook mechanism bolted on
  here. Rationale: consistency with the established precedent; an always-on blocking hook is
  higher-friction and intrusive for a package installed into other people's repos; the obligation is
  already carried where it matters (the workflows).
- OQ5 (RESOLVED): the human browse view is GROUPED BY `Set:` (each Set lists its members in `Order`),
  Sets ordered by most-recent activity, BOUNDED to the N most-recently-active Sets (default N=40,
  configurable); the complete corpus stays in `INDEX.json`. This gives browse-by-topic while keeping
  the view itself from becoming a new noise problem.

## 9. Next step
This spec is drafted and paused for HUMAN REVIEW. On approval, author an ORCHESTRATED IPD Set (a `00`
orchestrator plus focused children: the shared-core extraction; `Id` in `ipd_schema` + linter +
scaffold/sync; the plans manifest + `--check`; the set-assign/mv regroup verb; the shards + archival
verb; the one-time migration; scaffold/directives/DECISIONS updates), scoped to `plans/`, with
`prompts/` named the subsequent adopter. Do NOT begin any IPD until this spec is approved.
