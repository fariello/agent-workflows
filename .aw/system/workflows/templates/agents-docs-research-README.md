# .aw/records/research/

Durable research, technology surveys, and structured analysis that an agent relied on to support a
design or architecture decision, kept for provenance and cold-start handoff (GUIDING_PRINCIPLES P4).

## Naming and identity

Research artifacts follow the grammar (see `aw research --help` and `.aw/system/workflows/index.md`):

```
YYYYMMDD-<set-id>-<NN>-<id6>-<slug>[.<model>].<kind>.md
```

- `YYYYMMDD`: the SET's canonical date (shared by every member of a set); each file also records
  its own `created` date in frontmatter.
- `<set-id>`: a short kebab cohort key that clusters a set in a name-sorted tree. A singleton is a
  set of one. ITS LENGTH IS BOUNDED (catalog invariant I-17, spec `2lcqno` N8): 14 characters or
  fewer is strongly preferred, over 14 is a WARNING, and over 24 is REFUSED, so `aw research new`
  and `aw group research` reject an over-length `--set` and `aw check` reports
  `check.setid-length-warn` / `check.setid-length-error`. Grandfathering is PER ARTIFACT against the
  `cutovers.setid_length` boundary stamped into `.aw/config/project.json` on install or update, so an
  older artifact keeps its long setid while a NEW one is judged. The intended consequence is that a
  new artifact may NOT join an existing long-setid topic after the cutover; regroup the topic under a
  shorter setid instead.
- `<NN>`: two-digit read/execute order within the set (`00` is the originating prompt).
- `<id6>`: the stable 6-character base36-lowercase citation handle. It NEVER changes, even when the
  file is renamed, re-slugged, regrouped, or moved to a shard. Cite research by its `<id6>`
  (word-boundary greppable as `\b<id6>\b`), resolved via the metadata cache.
- `<slug>`: a short descriptive kebab.
- `[.<model>]`: an OPTIONAL authorship facet (also recorded in frontmatter); drawn from an open, data-driven vocabulary (packaged defaults + `.aw/config/research-models.toml`). An unrecognized model is recorded with an advisory warning; bless one via `aw research add-model <token>`.
- `<kind>`: MANDATORY, drawn from the enumerated vocabulary.

Do NOT hand-name or hand-maintain research files or the index. Use the `aw research` and
`aw archive` verbs (see `aw research --help`); the tool owns naming, the frontmatter, and the
metadata cache.

## States and layout

Research documents carry two distinct axes: per-document shelf status and set-level pipeline position. A research prompt carries no hot status; its pipeline position is derived.

### Shelf status

`status:` frontmatter, tool-owned for answer documents, is one of:

| State | Meaning | On disk |
|-------|---------|---------|
| `todo` (legacy `intake`) | landed, not yet triaged | hot root |
| `active` | informing in-flight work | hot root |
| `reference` | cold but it mattered (durable provenance) | `reference/YYYYMM/` monthly shard |
| `archive` | cold and just-in-case (dead-end, rejected) | `archive/YYYYMM/` monthly shard |

### Pipeline position

A derived, set-level position computed from set members and body presence:

| Position | Meaning |
|----------|---------|
| `unrun` | prompt exists, no landed response bodies |
| `partial` | one or more response reports have landed |
| `synthesized` | reconciliation or findings summary has landed |

Hot states (`todo`/`active`) stay flat at this directory's root and cluster by name. `todo` and `active` are status values of documents kept flat in this directory's root, not subdirectories, and external material is dropped in `.aw/inbox/` and filed with `aw adopt`. Cold states
live in monthly `YYYYMM` shards. `aw research find` lists documents in every state, including
`reference` and `archive`, and `aw research pending` lists the prompts still waiting for an answer.

## The index

`aw index rebuild` rebuilds the local cache; `aw index <type>` is an alias, so `aw research index`
and `aw index research` do the same thing and print one notice saying so. The cache is the SQLite
database `.aw/state/index.db`, built only from the tracked research documents and their metadata. It
is gitignored and disposable: a command that finds it missing or out of date still answers from the
tracked files, and deleting it changes no command output. No command writes `INDEX.json` or
`INDEX.md` any more, and the checks that reported a missing or out of date INDEX file are gone.

History, in one sentence: the INDEX files were once committed, became gitignored local views after a
conflict in `records/plans/INDEX.json` aborted one lane's merge back on 2026-09-06, and were then
replaced by the cache.

`aw research index --check` runs the research content drift rules instead of rebuilding, and exits
nonzero on a finding, as `aw check research --all` would. The rules cover missing or invalid
frontmatter, repeated frontmatter keys (`research.frontmatter-key-repeated`), a name vs frontmatter
mismatch, a dangling citation, a status-versus-tier mismatch (remediate with `aw research promote`),
and an orphaned companion directory. It is wireable into a pre-commit or CI gate. `aw research find
--id|--set|--topic|--status` answers queries from the cache without reading the corpus.

## Companion files

A research document may carry non-Markdown companion files (such as raw datasets, CSV tables, images, or archives) in a sibling companion directory named `<doc-stem>.data/`, where `<doc-stem>` is the document filename without the `.md` extension.

The companion directory shares the document identity and sorts directly beside it. Running `aw research index --check` validates that every companion directory has an owning research document in the same directory and flags orphaned companion directories (`check.research-companion-orphaned`).

Mutation and lifecycle verbs automatically carry companion directories along with their owning documents:
- `aw research mv` and `aw research set-assign` rename the companion directory alongside the document and refuse to overwrite a colliding destination.
- `aw research promote` and `aw archive` move the companion directory alongside the document into the target shard.

## External artifacts

Externally-produced artifacts (for example an LLM's research output) are archived here verbatim;
their own punctuation and formatting are preserved, so the no-em-dash house rule that applies to
authored framework Markdown does not apply to a cited external artifact.

The canonical rationale for this convention lives in the documentation named above; this README points to
it rather than restating it.
