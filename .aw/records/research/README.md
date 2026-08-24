# .aw/records/research/

Durable research, technology surveys, and structured analysis that an agent relied on to support a
design or architecture decision, kept for provenance and cold-start handoff (GUIDING_PRINCIPLES P4).

## Naming and identity

Research artifacts follow the grammar (spec
`.aw/records/specs/20260730-2152-01-agents-artifact-organization.spec.md`):

```
YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md
```

- `YYYYMMDD`: the SET's canonical date (shared by every member of a set); each file also records
  its own `created` date in frontmatter.
- `<set-id>`: a short kebab cohort key that clusters a set in a name-sorted tree. A singleton is a
  set of one.
- `<NN>`: two-digit read/execute order within the set (`00` is the originating prompt).
- `<id6>`: the stable 6-character base36-lowercase citation handle. It NEVER changes, even when the
  file is renamed, re-slugged, regrouped, or moved to a shard. Cite research by its `<id6>`
  (word-boundary greppable as `\b<id6>\b`), resolved via the manifest.
- `<slug>`: a short descriptive kebab.
- `[.<model>]`: an OPTIONAL authorship facet (also recorded in frontmatter); present only when
  disambiguation matters.
- `<kind>`: MANDATORY, drawn from the enumerated vocabulary.

Do NOT hand-name or hand-maintain research files or the index. Use the `aw research` and
`aw archive` verbs (see `aw research --help`); the tool owns naming, the frontmatter, and the
generated `INDEX.json`/`INDEX.md`.

## States and layout

`status:` frontmatter, tool-owned, is one of:

| State | Meaning | On disk |
|-------|---------|---------|
| `intake` | landed, not yet triaged | hot root |
| `active` | informing in-flight work | hot root |
| `reference` | cold but it mattered (durable provenance) | `reference/YYYYMM/` monthly shard |
| `archive` | cold and just-in-case (dead-end, rejected) | `archive/YYYYMM/` monthly shard |

Hot states (`intake`/`active`) stay flat at this directory's root and cluster by name. Cold states
live in monthly `YYYYMM` shards. `INDEX.md` shows the most-recent-N plus intake and includes
`reference`; `archive` is excluded from the hot glance but present in `INDEX.json`.

## The index

`aw research index` regenerates `INDEX.json` (every doc) and `INDEX.md` (the hot glance) purely from
frontmatter; both are COMMITTED so a fresh clone and a weak agent have them without running the tool.
The hot window shows the most-recent N sets (default N = 40, override with `aw research index
--limit N`). `aw research index --check` fails on drift (missing/invalid frontmatter, name vs
frontmatter mismatch, a stale generated view, or a dangling citation) and is wireable into a
pre-commit or CI gate. `aw research find --id|--set|--topic|--status` answers queries over the
manifest without reading the corpus.

## External artifacts

Externally-produced artifacts (for example an LLM's research output) are archived here verbatim;
their own punctuation and formatting are preserved, so the no-em-dash house rule that applies to
authored framework Markdown does not apply to a cited external artifact.

The canonical rationale for this convention lives in the spec named above; this README points to
it rather than restating it.
