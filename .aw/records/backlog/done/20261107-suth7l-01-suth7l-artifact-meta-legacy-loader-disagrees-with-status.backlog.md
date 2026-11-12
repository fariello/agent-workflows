- Id: suth7l
- Status: done
- Close-Evidence: .aw/records/backlog/done/20261107-suth7l-01-suth7l-artifact-meta-legacy-loader-disagrees-with-status.backlog.md
- Blocks-Release: next
- Set: suth7l
- Priority: high
- Work-Kind: bug
- Summary: artifact_meta legacy loader disagrees with status_set reader on 1385 of 3143 records (backlog status None: bullets read only after a '# ' title; research/prompt/spec Set and YAML status missing) and fills no per-type field rows, blocking 2xwb9b E-10/E-11

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-07 done (aw set): fixed in 7377cbc0b: loader parity restored (242 remaining = named filename-Set decision); see Evidence
- 2026-11-07 created (aw backlog): artifact_meta legacy loader disagrees with status_set reader on 1385 of 3143 records (backlog status None: bullets read only after a '# ' title; research/prompt/spec Set and YAML status missing) and fills no per-type field rows, blocking 2xwb9b E-10/E-11

## Problem

The `artifact_meta` cache is filled in phase B by its legacy loader (`artifact_meta.load_legacy_artifact`). Plan `2xwb9b` measured, before moving any read onto the cache, that the cache disagreed with today's reader (`status_set.inventory_all_artifacts`) on 1385 of 3143 records and that every per-type table (`ipd`, `spec`, `backlog`, ...) held 0 rows. Re-measured on 2026-11-07 at `main`: 1388 of 3146. Every later metastore plan that moves a read onto the cache (`ffceq0`, `t4gl15`, `59aiyh`, `9o83cr`, and the `2xwb9b` reads re-scoped to `ffceq0`) would have changed behavior on those records.

## Causes and fix

| Cause | Records | Fix |
|---|---|---|
| `_parse_bullet_metadata` started reading bullets only after a `# ` title; backlog items have no title line | 1146 backlog, status lost | read from the top of the file, the same region `selectors.metadata_region` uses |
| The YAML branch ran only when the type was the literal `research`, but research files carry a KIND facet (`findings`, `roadmap`, ...) that the filename parser returns as the type | 156 research/roadmap, status lost; 21 bogus types cached | resolve a non-registry facet to the records tree's registry type and keep the facet as `research_kind`; read YAML for any record that opens with a YAML fence that yields keys |
| The loader computed the registry fields and never wrote them | all per-type tables empty | write the per-type row, with the log branch's column layout and encoding |
| The cache's schema hash covered the field registry only, so a loader change never rebuilt an existing cache | every existing cache | fold `LEGACY_LOADER_VERSION` into the schema hash |

## Decision: a record with no `- Set:` line takes its Set from the filename

242 records (164 research, 30 prompts, 23 specs, 14 plans, 8 walkthroughs, 3 roadmaps) declare no in-file `- Set:` bullet. Today's reader returns no Set for them; the cache returns the filename's Set. KEPT, deliberately (maintainer, 2026-11-07): spec `4sd62s` C1/C10 make the filename the checked mirror of `set`, and 5.2 step 3 already defaults `set` from the filename, so the filename value is the target behavior and caching the old empty value would cache something the design deletes. The reader move in `ffceq0` (former `2xwb9b` E-10/E-11) compares against this as a NAMED difference, not a regression: once `status_set` reads the cache, `aw set <setid>` also matches those 242 records.

## Evidence

- Record parity on this repository after the fix: `records_disagreeing: 242`, all of them the Set decision above; `missing_from_cache: 0`; status and id6 agree on all 3146.
- Per-type field parity on this repository against today's text readers: `backlog.blocks_release 0/1146`, `backlog.priority 0/1146`, `backlog.work_kind 0/1146`, `ipd.blocks_release 0/1725`, `ipd.item_dependencies 0/1725`, `ipd.priority 0/1725`, `spec.blocks_release 0/49`, `spec.priority 0/49` mismatches.
- New fixture tests `tests/test_artifact_meta_loader_parity.py` (core), and the artifact_meta, status_set and spec-review modules: `236 passed`; bare core gate `2067 passed`; `mypy agent_workflows` clean.
