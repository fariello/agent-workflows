- Id: xl9xrm
- Status: graduated
- Graduated-To: xl9xrm
- Set: xl9xrm
- Work-Kind: bug
- Priority: medium
- Summary: artifact_core.get_ignored_dirs caches ignored dirs without .aw/.gitignore or .git/index mtime hiding .aw/records after in-process layout migration
- Short-Description: artifact_core.get_ignored_dirs caches ignored dirs without .aw/.gitignore or .git/index mtime hiding .aw/records after in-process layout migration
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 graduated (aw set): Graduated to review-ready plan dd48b5 (set xl9xrm)
- 2026-11-21 created (aw backlog): artifact_core.get_ignored_dirs caches ignored dirs without .aw/.gitignore or .git/index mtime hiding .aw/records after in-process layout migration


## Problem

`agent_workflows/artifact_core.py::get_ignored_dirs` caches the output of `git ls-files --others --ignored --exclude-standard --directory` in `_cached_ignored_dirs` using the cache key `(resolved_root_str, gi_mtime, ex_mtime)`, where `gi_mtime` is the mtime of root `.gitignore` and `ex_mtime` is the mtime of `.git/info/exclude`.

The cache key omits `.aw/.gitignore` and `.git/index`. When a legacy `.agents/` repository runs `aw migrate metadata` dry run in-process, creating `.aw/state/` makes `.aw` an ignored-only directory, so `git ls-files` reports `.aw` and `_cached_ignored_dirs` caches `.aw` as ignored. After `aw migrate metadata --apply` creates `.aw/.gitignore` and commits `.aw/records/`, neither root `.gitignore` nor `.git/info/exclude` changes mtime. Subsequent in-process calls to `artifact_core.iter_scan_files` still treat `.aw` as ignored and return an empty list, causing `aw attention --all --format json` to report zero items.

Measured during IPD `60mazt` execution on `tests/migration_corpus.py::legacy_agents_layout`: `artifact_core.iter_scan_files(repo)` returned `[]` after `--apply` until `artifact_core._cached_ignored_dirs.cache_clear()` was called, after which it returned all 6 files under `.aw/records/`.

## Fix direction

1. Include `.aw/.gitignore` mtime (and `.git/index` mtime or equivalent tracked-state token) in the cache key of `agent_workflows/artifact_core.py::get_ignored_dirs`, or clear `_cached_ignored_dirs` after layout migration commits `.aw/` files.
2. Add a behavioral test exercising a `.agents/`-only repository that transitions to tracked `.aw/records/` in-process and asserting `artifact_core.iter_scan_files` returns the migrated records without manual cache clearing.
