# IPD: Build the artifact_meta core: registry, event schema, append key, SQLite cache, legacy loader

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` (approved) makes one module, `agent_workflows/artifact_meta.py`, the only reader and writer of artifact metadata, with a SQLite cache as the only read path (C5, C5a), and its facade-first order (section 7) requires that module to exist, fully tested, BEFORE any caller moves onto it. None of it exists: measured 2026-11-02, `agent_workflows/artifact_meta.py` and `agent_workflows/migrations/` are absent, no module imports `sqlite3`, and metadata is read today by 11 or more independent parsers (`selectors.read_front_matter_id`, `runner_shared._front_matter_bullets`, `ipd_schema.parse_metadata_block`, `backlog.parse_item`, `research_contract.parse_frontmatter`, `prompts.read_metadata_id6` and others; spec section 1). The corpus this core must load is 4,441 tracked `.md` files (111 MB) under `.aw/records/` with 70 distinct bullet field names, 2,878 `## Workflow history` sections, 1,289 review records and a 481-record history sidecar. Every later child of Set `metastore` (Orders 03 to 13) depends on this interface.
- Scope: Phase A step 1 of `4sd62s` section 7, additive only. Build `agent_workflows/artifact_meta.py` with: the per-type field registry and per-op payload schemas (4.2, 4.2c, OQ-1); the version-1 event envelope with the structured `actor`, the `append` key and the records-root-relative `path` rule (4.2, OQ-17, OQ-24); writer-side refusals (unsafe descriptive values including `short_description`, leaks in `actor`/`message`, bad paths); `seq` replay with every LOADER VALIDATION rule of 4.3 and every event-owned field rule of 4.2 and 4.4; the cache schema generated from the registry, with `schema_hash` (4.5, 4.5a); cache placement, WAL, rebuild and in-memory fallback (4.5); the two-check freshness rule (4.3); the one loader entry point; the LEGACY loader that fills the same rows from today's bullet blocks, research YAML, `aw-prompt` comments, history sections and review files (4.3, section 7); the public `read`, `history`, `query`, `resolve` and `read_at` functions (4.3, 4.4); and the ordered log-format `append`/`create` write with lock, `expect_seq`, operation journal and mirror repair (4.3, 4.7), proven on synthetic logs. Adds one new pure function to `artifact_naming` for D177 facets (OQ-32). EXCLUDES moving any caller (Orders 06 to 09), any CLI verb (Order 03 and later), the migration (Order 04), the description journal (Order 05), and switching the live format (Order 13).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/artifact_naming.py, tests/test_artifact_meta_registry.py, tests/test_artifact_meta_replay.py, tests/test_artifact_meta_cache.py, tests/test_artifact_meta_legacy.py, tests/test_artifact_meta_read.py, tests/test_artifact_meta_write.py, .aw/records/plans/pending/20261102-metastore-02-tve77h-build-the-artifact-meta-core-registry-event-schema-append-ke.ipd.md
- Item-Dependencies: none
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 2
- Highest E allocated: 18
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tve77h

## Workflow history
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Deliver the single metadata interface of spec `4sd62s` as a tested, caller-free module: it reads today's bullet format through a legacy loader into a disposable SQLite cache, and it already implements the event-log format, replay and write path that the cutover (Order 13) switches on.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Each E-item delivers ONE behavior together with the behavioral tests that prove it, in the named test module. Every new test module sets `pytestmark = pytest.mark.core`, builds its fixtures in `tmp_path`, calls the real functions, and never reads production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: registry and event format

- [ ] E-01 Create `agent_workflows/artifact_meta.py` with the FIELD REGISTRY: one entry per logical type (`ipd`, `spec`, `backlog`, `research`, `release`, `prompt`, `walkthrough`; 4.5c) mapping each snake_case field to a value type (string, integer, closed enum, string list, structured dependency list, path-with-reason list, reference) and an ownership mark (`generic`, `transition-owned`, `review-owned`, `coverage-owned`, `finalize-owned`, `path-event`, `migration-only`). It contains every field of the 4.2c table and every census name in F-03 that maps to a log field, including `short_description`, `plan_role`, `research_kind`, `prompt_kind`, `ace`, `model`, `pipeline` (enum `standard`/`quick`), `review_depth`, `scope_result` (enum `within`/`widened`/`exceeded`), `item_dependencies`, `graduated_to`, `blocks_release`, the gate fields, and the migration-only `coverage_checked`, `scope_exceeded_raw`, `created_day`, `last_history_day`, `description_source`, `description_model` and `description_prompt_version`. Lifecycle tables are REFERENCED, never copied: `attention_contract.SPEC_TRANSITIONS`, `attention_contract.BACKLOG_TRANSITIONS`, `ipd_lifecycle.validate_transition` plus the retirement targets `superseded`/`not-executed`/`reusable` that `status_set.TYPE_STATUSES["plans"]` accepts (F-12), and value-only validation for research, prompt and release (`research_contract.STATUSES`, `lifecycle_dirs.LIFECYCLE_SUBDIRS["prompts"]`, `releases.RELEASE_STATUSES`). Test module `tests/test_artifact_meta_registry.py`.
  - Depends on: none
  - Expected outcome: `artifact_meta.registry_fields("ipd")` lists every plan field with its type and owner; `artifact_meta.validate_event` reports an unknown field for each type; a plan `transition` from `approved` to `superseded` is legal and from `executed` to `draft` is not.
  - Execution state: pending

- [ ] E-18 Add the per-op payload schemas to the registry, the one table that both the writer and the loader consult for op payload keys (4.2). Covered ops are `create`, `set`, `unset`, `transition`, `note`, `checkpoint`, `legacy` (with `source` `history` or `sidecar`, `observed_day`, original position and `ordering_confidence`), `review` (`round`, `verdict` or the migrated `legacy_verdict`, `review_kind`, `reviewer`, and optional `review_ref`, `findings_summary`, `review_depth` and `readiness`), `coverage` (`coverage`, `coverage_fingerprint`) and `rename` (`verb` in `rename`, `group` or `archive`, plus `path`). The names `finalize` and `turn` are reserved without any schema, and the registry also owns the refinement verdict vocabulary, which holds at least `REVIEWED - MATERIAL CHANGES APPLIED` and `REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION` (4.1a K3). Test module `tests/test_artifact_meta_registry.py`.
  - Depends on: E-01
  - Expected outcome: a payload key outside its op schema is reported by `artifact_meta.validate_event`; `finalize` and `turn` are recognized names whose events are refused as "no registered payload schema"; a `rename` with verb `move` is refused.
  - Execution state: pending

- [ ] E-02 Implement the version-1 event envelope: `encode_event` produces one JSON line with sorted keys, UTF-8, no trailing whitespace and a final LF; `decode_line` parses one line; required keys `v`, `seq`, `append`, `at`, `actor`, `op`; `at` must be RFC 3339 UTC with a time of day (written with the same `datetime.now(timezone.utc)` clock as `runner_shared.utc_now`; 4.2b); `actor` is an object whose `tool` is required and whose other keys (`ace`, `host`, `model`, `variant`, `run_id`, `attempt`) are omitted, never `null`, when unknown; every id6 argument and path computation validates with a FULL match of `artifact_core.ID6_RE` (`re.fullmatch` semantics; a trailing newline is refused). Test module `tests/test_artifact_meta_registry.py`.
  - Depends on: E-01, E-18
  - Expected outcome: `encode_event(decode_line(x)) == x` for a canonical line; `"abc123\n"` is refused as an id6; an actor with `"model": null` is refused; an `at` of `2026-11-02` (day only) is refused.
  - Execution state: pending

- [ ] E-03 Implement writer-side refusals in `validate_new_events(type, events, *, records_root, migration_import=False)`: (a) every string value written to a log or mirror passes `attention_contract.refuse_unsafe_descriptive` (300-character bound for `short_description` and other single-line fields; prose class for `message`); (b) `actor` values and `message` are scanned with `leak_sanitizer.scan_text` and `leak_sanitizer.build_ruleset`, so a session id (`ses_...`), a home-directory or absolute path, a user name or host name is refused (AC-24 (2)); (c) every `path`, `out_of_scope_paths` and `widened_paths` value must be relative, contain no `..` segment, and resolve inside the resolved records root; (d) the single migration exception: when `migration_import=True`, `legacy.line`, the sidecar JSON object and `legacy_verdict` are stored byte-for-byte without the length and control-character refusal (4.2 SR-903), while the leak scan still runs. Test module `tests/test_artifact_meta_registry.py`.
  - Depends on: E-02
  - Expected outcome: a `short_description` of 301 characters, one with a newline, an actor carrying `ses_` plus 20 characters, and a path `<home>/a.md (an absolute home-directory path)` or `../a.md` are each refused with a named reason; the same 5,000-character history line is accepted only with `migration_import=True`.
  - Execution state: pending

- [ ] E-04 Implement the structured relationship values: `item_dependencies` is stored PARSED as `dependency_declaration` (`listed`/`none`/`unresolved`) plus an ordered list of `{condition, target_type, required_status, target_id6, raw}`, built from the existing grammar `ipd_schema.parse_item_dependencies`; an absent field stays absent and is distinct from `none`; `from_backlog`, `from_spec`, `from_plan` and `supersedes` are stored as individual lineage references; `graduated_to` is an ordered multi-value list that keeps duplicates and malformed entries for diagnosis (OQ-15); `blocks_release` keeps `next` as written. Test module `tests/test_artifact_meta_registry.py`.
  - Depends on: E-01
  - Expected outcome: `executed:abc123`, `exists:spec:def456`, `state:spec:approved:def456`, `none`, `unresolved` and no field produce six distinct stored shapes, and `none` differs from absent.
  - Execution state: pending

### Task group 2: replay and the loader

- [ ] E-05 Implement `replay(id6, type, lines)`: sort by `seq` (line order is irrelevant; AC-4); refuse a gap or duplicate `seq`; refuse any initial shape other than exactly one `create` at seq 1 or exactly one `checkpoint` at seq 0, and any later `create`/`checkpoint`; refuse an `id` or `type` that differs from the log filename and the record owner, and any later change to either; refuse an unsupported `v`; refuse an `append` that is not the `seq` of the first event of a contiguous run sharing `append`, `at` and `actor`; refuse a `transition` whose `from` differs from the replayed status or whose edge is illegal for the type; refuse a generic `set`/`unset` of `status`, `id` or `type`; `note` and `legacy` change no field; a migrated `review` event changes no status. Output: the current `State`, the `field_changes` rows (old value, new value, unset flag) and the `artifact_paths` rows. Test module `tests/test_artifact_meta_replay.py`.
  - Depends on: E-02, E-04
  - Expected outcome: a shuffled valid log replays identically to the ordered one; each listed defect yields a refusal naming the rule (`seq-gap`, `seq-duplicate`, `bad-initial-event`, `identity-changed`, `unsupported-version`, `append-mismatch`, `illegal-transition`, `transition-from-mismatch`).
  - Execution state: pending

- [ ] E-06 Implement the event-owned field rules inside `replay`, checked with the `append` key (4.2 replay paragraph, 4.4, AC-15, AC-39): `readiness` and `review_depth` are set ONLY by a gate `review` payload, and a `set` of either is always refused; `readiness` must be unset in the append of a backward plan transition to `draft` or `to-review`; `approval` is set only in the append containing the transition to `approved` and must be unset in the append containing a transition away from `approved`; `coverage` and `coverage_fingerprint` only by an `op: coverage` event; `scope_result`, `out_of_scope_paths` and `widened_paths` only by a `set` in the append containing a plan's transition to `executed`; `path` only on path-bearing events (`create`, `checkpoint`, `rename`, a disposition-changing `transition`), and a path-bearing op without `path` is refused; typed reviews: a `gate` verdict must be in `plan_readiness.VERDICTS`, a `refinement` verdict must be in the registry vocabulary and never carries `readiness`; a `finalize` or `turn` event is refused; a migrated review event may carry `legacy_verdict` instead of `verdict`. Test module `tests/test_artifact_meta_replay.py`.
  - Depends on: E-05
  - Expected outcome: hand-written logs placing `set approval`, `unset approval`, `unset readiness` or `set scope_result` outside the owning append are refused; a log where `approval` survives a transition away from `approved` is refused; a gate review with `readiness: go` replays to `readiness=go`.
  - Execution state: pending

- [ ] E-07 Implement the LOADER, the only code that opens a `meta/*.jsonl` log, and the strict mirror parsers: one entry point `_load_sources(conn, changed)` that, for each changed or new source, parses it, validates and replays it, and replaces that artifact's rows in every table in ONE transaction; on refusal it first DELETES any previously valid projection of that artifact, then records `files.load_error` and an `artifacts` row with `valid = 0` and `defect`. The post-cutover mirror parsers use a strict line grammar, not YAML: two-key `---` front matter (`id`, `status`), one-key walkthrough front matter, review front matter (`subject`, `subject_type`, optional `ref`), and the single leading `<!-- aw-managed-prompt: id: <id> | status: <status> ... -->` comment (4.1, OQ-25). Test module `tests/test_artifact_meta_replay.py`.
  - Depends on: E-06
  - Expected outcome: replacing a valid log with an invalid one makes `read(id6)` fail naming the defect and never return the old state; a staged-prompt file whose line 1 is the managed comment yields its `id` and `status`; a second `---` key on an artifact is a mirror parse error.
  - Execution state: pending

### Task group 3: the cache

- [ ] E-08 Generate the cache schema from the registry (4.5, 4.5a), so that a registry change is the only thing that changes the schema. The generated set is the 4.5a table list (`meta`, `directories`, `files`, `artifacts`, the per-type tables with one typed column per registry field, `scope_paths`, `artifact_paths`, `scope_exceptions`, `dependencies`, `lineage`, `graduation_targets`, `release_gates`, `gates`, `actors`, `events`, `field_changes`, `review_files`, `reviews`, `rev_log_states`, `rev_mirrors`) with the 4.5a minimum indexes. The `meta` table holds `schema_hash` (SHA-256 of the canonical registry plus a layout version constant) and the reserved keys `runs_root` and `run_reader_version` (4.5b). Table and column identifiers come only from the registry and fixed vocabulary, quoted as SQLite identifiers, every value is a `?` binding, and reference columns carry no foreign-key constraint. Test module `tests/test_artifact_meta_cache.py`.
  - Depends on: E-01
  - Expected outcome: `sqlite_master` lists exactly the 4.5a table set; each table's columns equal the 4.5a minimum plus the registry fields; adding one field to a copied registry changes `schema_hash` and the next read rebuilds with the new column (AC-23 (1), (2)).
  - Execution state: pending

- [ ] E-09 Implement cache placement and failure handling: the path is `<state root>/index.db`, where the state root is `project_context.resolve_project_context(...).logical_roots["state"]` (the `/state/` rule in `.aw/.gitignore` already ignores it); the records root is `logical_roots["records"]`, so logs live under the RESOLVED records root for `repository`, `companion` and `home` backends (AC-18); SQLite opens in WAL mode with a busy timeout; a `schema_hash` or `records_root` mismatch, or a damaged file, deletes and rebuilds; if the file cannot be rebuilt, or stays busy past the timeout, the same schema and validation run in an in-memory database; a source-validation error still fails with its real cause. Test module `tests/test_artifact_meta_cache.py`.
  - Depends on: E-08
  - Expected outcome: query results are identical with a cold cache, a warm cache, a deleted `index.db`, an `index.db` overwritten with random bytes, and a read-only state directory (in-memory fallback) (AC-8 at the interface level, AC-1a cases); a companion-backend fixture places `meta/<id6>.jsonl` under the resolved companion records root and answers `query()`.
  - Execution state: pending

- [ ] E-10 Implement the freshness check run before every public read (4.3): MEMBERSHIP lists each in-scope directory (`meta/` and every record-type and disposition directory, recursively), treating `directories.mtime_ns` as a hint only, discovering new subdirectories and dropping vanished members; CONTENT compares `(size, mtime_ns)` as a hint and confirms identity with a SHA-256 digest of the current working bytes (unstaged edits included), so a same-size, same-mtime replacement is detected; changed or new files go to the loader; removed files lose their rows; after any target inventory change, resolved references (`dependencies.target_id6`, `lineage.parent_id6`, `release_gates.release_id6` including `next` resolved through `releases.resolve_release_outcome`, `graduation_targets.target_set_id`) are recomputed even when the source did not change. Test module `tests/test_artifact_meta_cache.py`.
  - Depends on: E-07, E-09
  - Expected outcome: each AC-26 change (add, delete, `git mv` to another disposition, same-size same-mtime byte replacement, a dangling target appearing, a second planned release changing `next`, a new nested directory, a directory membership change with restored mtime) is visible on the next `query()` with no rebuild call.
  - Execution state: pending

### Task group 4: legacy loader and read interface

- [ ] E-11 Implement the LEGACY loader for artifacts (phase B source, moved unchanged into `m0001` at the cutover): parse the bullet block before the first `##` with one strict `- Field: value` grammar; research `---` YAML keys (`kind` -> `research_kind`); the staged-prompt `<!-- aw-prompt: ... -->` comment (`Kind` -> `prompt_kind`); filename identity tested in this order: `artifact_naming._LEGACY_TIMESTAMP_RE` first, then the clustered prefix, then the new `artifact_naming.parse_attributed(name)` (additive, returns `date`, `set`, `nn`, `id6`, `slug`, optional `ace` and `model`, and `type` for D177 names, which `parse_clustered` rejects today; F-05); legacy field names map to registry names (`Kind` -> `plan_role`, `Work-Kind` -> `work_kind`, and so on; 4.2, 4.5c); `Item-Dependencies` through E-04; the current path only (no path history in phase B; section 7). Fields with no registry entry are kept as `legacy_unregistered` rows for the Order 04 census and do NOT invalidate the record (OQ-02). Status: see OQ-03. Test module `tests/test_artifact_meta_legacy.py`.
  - Depends on: E-10
  - Expected outcome: fixtures for a plan, spec, backlog item, research report, staged prompt with and without a comment, release, walkthrough and a legacy `20260818-1525-02-assess-...` name load to the expected rows; a legacy name whose slug starts with a 6-letter word is classified as legacy, never as `id6`; a D177 review filename yields its `ace` and `model`.
  - Execution state: pending

- [ ] E-12 Extend the legacy loader to history and review records: each `## Workflow history` line becomes an ordered history row of its artifact (file order kept, no transition inferred, newest record chosen by `attention_contract.newest_history_record` so `last_history_day` matches today's `last_history_at`); each `.review.md` file becomes a `review_files` row (subject from `Subject-Id`, round count from `## Round <n>` headings, `parse_ok` from `review_findings.parse_review_text`) and one `reviews` row per round bound to its file (default binding for a sole file, otherwise the 4.1a K4 reference), with the file's `Verdict`, `Reviewer` and `Reviewed-At` on the LAST round only (K5a) and `review_kind` `refinement` for `specflow` refinement files, else `gate`; the gitignored sidecar `.aw/records/history.jsonl` is NOT read in phase B (it stays the setters' concern until Order 04). Test module `tests/test_artifact_meta_legacy.py`.
  - Depends on: E-11
  - Expected outcome: a three-round review file yields three `reviews` rows with the verdict only on round 3; two review files for one subject keep distinct bindings; the history rows of a plan with tool-prepended and author-appended lines are returned in file order, and `last_history_day` equals `attention_contract.last_history_at` on the same lines.
  - Execution state: pending

- [ ] E-13 Implement the public read functions over the cache, each running the freshness check first: `read(id6) -> State` (fails closed on an invalid record), `history(id6) -> list[Event]` (log events after the cutover; legacy history rows in phase B), `resolve(path_or_id6)`, and `query(...)` with typed filters for type, status, Set, order, "depends on X", "latest gate review of X" and `artifact_paths(path)`, every filter name resolved through the registry before SQL is built; a cross-artifact query returns its rows plus an `incomplete` list naming invalid or missing records, never a silent omission. Test module `tests/test_artifact_meta_read.py`.
  - Depends on: E-12
  - Expected outcome: `EXPLAIN QUERY PLAN` for `query(status=..., set_id=...)`, `query(depends_on=X)`, `query(latest_gate_review_of=X)` and `query(path=P)` each names an index (AC-23 (3)); one invalid record in a 3-record fixture yields 2 rows and `incomplete == [<id6>]`.
  - Execution state: pending

- [ ] E-14 Implement `read_at(id6, rev)` (4.4): run git in the repository that owns the resolved records root; resolve the record's path INSIDE that revision (`git ls-files -s` for the index, `git rev-parse <rev>:<path>` for a commit); look up the log blob in `rev_log_states` and the `.md` blob in `rev_mirrors`; feed a miss through `git cat-file` to the SAME loader (log loader, or the legacy loader for a bullet-format blob in phase B); fail closed on a validation error and cache no valid row; return distinct results for an absent record, an invalid revision, and an unversioned placement (`home`, `repository-untracked`). Test module `tests/test_artifact_meta_read.py`.
  - Depends on: E-13
  - Expected outcome: after a fixture rename commit, `read_at(id6, "HEAD~1")` returns the old metadata from the old path; `read_at(id6, "nosuchrev")` and an absent id6 give different result kinds; a companion fixture reads blobs from the records repository; a corrupt blob fails and leaves no `rev_log_states` row (AC-33).
  - Execution state: pending

### Task group 5: log-format writes, repair, and finish

- [ ] E-15 Implement the log-format write path `append(id6, events, *, expect_seq)` and `create(...)`, used by tests now and switched on at the cutover: validate with the E-03 and E-06 rules BEFORE any write (a refusal or `dry_run=True` writes nothing; C6); hold the per-artifact lock `platform_lock.held(<state>/locks/meta-<id6>.lock)`; check `expect_seq` against the log; for `create` and rename/group, first retain recovery data (body and destination, or source-to-destination map) in a gitignored operation journal under the state root; then in order: (1) LOG via temp file, `fsync`, `os.replace` (the commit point), (2) in-file mirror via `artifact_core.atomic_write`, (3) disposition move, (4) cache rows (best effort). Assign consecutive `seq`, one `append`, one `at` and one `actor` to every event of the call (AC-39 (1)). Report failure BEFORE the commit point as "no change" and failure AFTER it as "change recorded; run repair". Test module `tests/test_artifact_meta_write.py`, with failure injection at each step for a transition, a create and a rename.
  - Depends on: E-13
  - Expected outcome: injected failure before step 1 leaves every file byte-identical; after step 1 the log holds the events, the result names the repair; a second mutation of that artifact is refused while recovery is pending (AC-5).
  - Execution state: pending

- [ ] E-16 Implement `repair(id6, *, confirm=None)` and same-artifact divergence handling: (a) mirror and move repair restores the in-file mirror and completes a journaled pending create or move from the log, appends NO event, leaves the log byte-identical, and is idempotent; a create whose journaled body is missing is refused naming the missing recovery source; (b) a log merged from two branches that both appended after the same `seq` is reported (duplicate `seq` or invalid replay), identical appends need no repair, and a confirmed tail repair renumbers only the divergent, not-yet-integrated events after the winning prefix, re-validates every resulting field change and transition, keeps the winning prefix byte-identical, and refuses when reconciliation would change that prefix (4.7). Test module `tests/test_artifact_meta_write.py`, including real two-branch `git merge` fixtures.
  - Depends on: E-15
  - Expected outcome: running `repair` twice yields the same bytes; a two-branch merge with different events at seq 4 fails `read()`; after a confirmed tail repair the first N lines are unchanged and replay succeeds (AC-17).
  - Execution state: pending

- [ ] E-17 Prove the module is additive and the full tier passes: `rg -l "artifact_meta" agent_workflows` lists only `artifact_meta.py`; `git diff --stat` touches only Scope-Paths; `pyproject.toml` `dependencies` is unchanged (`["filelock>=3"]`); run `python3 -m pytest -o addopts="" -n auto tests/test_artifact_meta_registry.py tests/test_artifact_meta_replay.py tests/test_artifact_meta_cache.py tests/test_artifact_meta_legacy.py tests/test_artifact_meta_read.py tests/test_artifact_meta_write.py tests/test_artifact_naming_round_trip.py`, the bare core gate `python3 -m pytest` (within its 30 s budget), `make test-all` (phase-A thorough checkpoint is owned by Order 04, but this plan must not break it), `aw check` against a pre-E-01 baseline, and `aw sanitize --agent`; commit through `aw commit tve77h -- <each changed path>`. Never push.
  - Depends on: E-14, E-16
  - Expected outcome: all runs pass; no new `aw check` error or warning; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Atomic file replacement already exists as `artifact_core.atomic_write` (temp file then `os.replace`; it normalizes only `.md` text, so a `.jsonl` log passes byte-for-byte). It does not `fsync`; `run_ledger_store` does (`os.fsync(fd)`), so the log write adds `fsync` before `os.replace`.
- The single lock wrapper is `platform_lock.acquire` / `platform_lock.held`, non-blocking by default and not re-entrant (its docstring forbids new blocking callers).
- Project roots come from `project_context.resolve_project_context(...)`; `logical_roots["state"]` and `logical_roots["records"]` give the state and records roots for every delivery mode and backend (`runner_shared.state_root` uses the same resolver).
- `artifact_core.ID6_RE` is `\A[0-9a-z]{6}\Z`; the spec requires full-match use.
- Descriptive-value refusal is `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN = 300` and `MAX_PROSE_DESCRIPTIVE_LEN = 4300`.
- The leak sanitizer exposes `leak_sanitizer.build_ruleset(repo_root)` and `leak_sanitizer.scan_text(text, location_prefix, ruleset)`; its `session-id` rule matches `ses_` plus 8 or more characters.
- The dependency grammar is `ipd_schema.parse_item_dependencies(value) -> (edges, ready, error)`; it parses a VALUE, not a metadata block, so the core may reuse it without becoming one of the parsers Order 11 deletes.
- Filename grammar lives in `artifact_naming` (`_LEGACY_TIMESTAMP_RE`, `parse_clustered_prefix`, `parse_clustered`); DECISIONS.md D177 fixes the attributed form `[.<ace>][.<model>].<type>.md`.
- Newest-history rule: `attention_contract.newest_history_record` (first matching line; writers prepend).
- Review files parse with `review_findings.parse_review_text`; gate verdicts are the keys of `plan_readiness.VERDICTS`.
- The rebuildable-cache precedent is `run_analytics_cache` (fingerprint, decide, publish).
- Core tier: `pyproject.toml` marker `core`, 30 s budget; modules set `pytestmark = pytest.mark.core` (for example `tests/test_review_tier.py`).

## Findings

| Id | Evidence (measured 2026-11-02 at `0cbfcc706`) | Finding |
|---|---|---|
| F-01 | `ls agent_workflows/artifact_meta.py agent_workflows/migrations` fails; `rg -l sqlite3 agent_workflows` finds no module | Nothing to extend; the module is new and no caller exists. |
| F-02 | `git ls-files .aw/records` gives 4,441 `.md` files (4,415 excluding READMEs): plans 1,706, reviews 1,289, backlog 1,133, research 170, specs 48, prompts 30, walkthroughs 26, comms 7, prompt-library 4, releases 1, roadmaps 1; 2,878 have `## Workflow history`; total 111,057,940 bytes | Corpus the legacy loader must serve (spec's r17 figure was 4,435). |
| F-03 | Bullet census before the first `##`: 70 distinct names. Plans: `Status`/`Id` 1,705, `Kind` 1,603, `Readiness` 1,242, `Scope-Paths` 1,412, `Item-Dependencies` 1,346, `Scope-Exceeded` 40, `Coverage*` 36 each, `Attended` 3, `Review-Depth` 2, plus one-off `Note`, `Self-note`, `Origin`, `Supersedes-Note`. Reviews: `Subject-Id`/`Subject-Type`/`Reviewed-At`/`Reviewer`/`Verdict` 1,289, `Findings` 431, `Readiness` 172, `Audited-Scope` 8. Research YAML keys: `id`, `created`, `set`, `order`, `topic`, `model`, `kind`, `outcome`, `summary`, `consumed-by` 165 each, `status` 157, `priority` 12. Prompt `aw-prompt` keys: `Kind`/`Id`/`Status`/`Created` 24, `Author` 16, `Targets` 14, `Concerns` 12, `Set` 8 | Registry input; the one-off names are why unregistered legacy bullets must not invalidate a record (OQ-02). |
| F-04 | `Item-Dependencies` over 1,705 plans: `none` 998, `executed:` edges 480, absent 359, `state:` 3, `exists:` 3, `unresolved` 1 | The closed grammar of 4.2 holds; `none` versus absent must stay distinct. |
| F-05 | 32 tracked D177 filenames; `artifact_naming.parse_clustered` returns `None` for all 32 | Confirms OQ-32: facet parsing must be added (as a new function, so no caller changes). |
| F-06 | 42 tracked filenames match `_LEGACY_TIMESTAMP_RE` (includes comms and templates; the spec counts 34 artifacts and walkthroughs) | Legacy loader must test this pattern first. |
| F-07 | Review verdicts: `APPROVE WITH REVISIONS APPLIED` 1,151, `REVIEWED - OPEN QUESTIONS` 98, `REVIEWED - MATERIAL CHANGES APPLIED` 20, `REVIEWED` 11, `REJECT - NEEDS REPLAN` 3, `REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION` 3, `APPROVE` 2, `REVIEWED - CONVERGED WITH REVISIONS` 1 | 35 off-vocabulary verdicts (spec r11 count) must load as `legacy_verdict`, never as `verdict`. |
| F-08 | 24 of 1,705 plans have a multi-word `- Status:`, all in `executed/` (`EXECUTED` 17, `DONE` 7 among them); `selectors._STATUS_RE` captures `(\S+)` and so returns no status for them (its PARITY CONSTRAINT comment) | The legacy loader must preserve today's `aw find` matching (OQ-03). |
| F-09 | Sidecar `.aw/records/history.jsonl`: 481 records (backlog 335, specs 124, research 11, plans 8, walkthroughs 2, roadmaps 1); 39 carry rename keys `from_name`/`to_name`/`verb` | Read by the migration (Order 04), not by the phase-B loader. |
| F-10 | No duplicate `- Id:` across non-review records | `id6` alone can key the cache (4.5). |
| F-11 | Warm SHA-256 of all 4,441 `.md` files: 0.437 s on this machine | The content-digest check is affordable as the starting method; AC-13 (Order 13) measures end to end. |
| F-12 | `ipd_lifecycle.validate_transition("approved", "superseded")` returns `unknown target status`; `status_set.TYPE_STATUSES["plans"]` accepts `superseded`, `not-executed`, `reusable` | The plan lifecycle table needs the retirement targets added by reference in the registry, not by editing `ipd_lifecycle` (N2). |
| F-13 | Python `sqlite3.sqlite_version` is 3.45.1; `pyproject.toml` `dependencies = ["filelock>=3"]` | WAL and `EXPLAIN QUERY PLAN` are available with no new dependency (C8, AC-12). |

## Proposed changes (ordered, validatable)

1. Registry, op schemas and format (E-01, E-18, E-02 to E-04).
2. Replay rules and the loader (E-05 to E-07).
3. Cache schema, placement and freshness (E-08 to E-10).
4. Legacy loader and the read interface (E-11 to E-14).
5. Write path, repair, additive proof, commit (E-15 to E-17).

## Deferred / out of scope (with reason)

- `aw show --history`, `aw show --format json` and `aw index rebuild`: section 7 step 2.
  - Carrier: 1ajqaa
- Migration framework, `m0001` dry run, census (AC-20), sidecar import and renames: section 7 step 3.
  - Carrier: dcerjg
- Description journal and the generation prompt: section 7 step 3, OQ-22, OQ-31.
  - Carrier: ya4ee4
- Moving the `status_set` engine and every other writer onto `artifact_meta`, including the tooled `review` and `coverage` writers and finalize's scope fields: section 7 step 4.
  - Carrier: 2xwb9b
- Moving readers, gates and hooks, including `aw check meta` (AC-7): section 7 step 5.
  - Carrier: ffceq0
- The `aw meta repair` CLI verb over E-16's `repair` function: no Set child names it yet; it belongs with `aw check meta`, which reports the drift it repairs.
  - Carrier: ffceq0
- Switching the loader and writer to logs and moving the legacy loader into `m0001`: section 7 step 9.
  - Carrier: cxxmyv
- `finalize` and `turn` payloads, per-item attribution and run-index tables: moved scope.
  - Carrier: nq1src
- Run-record tables in the cache (`runs_root`, `run_reader_version` keys are reserved here only).
  - Carrier: f4p4vn

## Scope check

- Over-scope: none. `artifact_naming.parse_attributed` is a new function; no existing function changes.
- Under-scope: none known. Covered: 4.2 (envelope, actor, ops, path history, field names, dependencies, identity, replay, event-owned fields, short description bounds), 4.2a (legacy events change no field), 4.2b (UTC `at`; distinct `filename_date`/`created_day`/`created_at` columns), 4.2c (registry), 4.3 (interface, freshness, writes, loader validation, legacy loader), 4.4 (`read_at`), 4.5 and 4.5a (cache), 4.7 (divergence). Plan-size note: this plan has 18 E-items in 5 task groups, exactly at both limits; see OQ-01. Lint advisory `IPD-Z602` on E-08 and E-18 is accepted: each item produces ONE deliverable (the generated cache schema; the op payload schema table) and the heuristic counts the enumerated table and op names as clauses. Splitting either would separate a schema from its own name list and exceed the 18-item limit.

## Required tests / validation

New core test modules: `tests/test_artifact_meta_registry.py`, `tests/test_artifact_meta_replay.py`, `tests/test_artifact_meta_cache.py`, `tests/test_artifact_meta_legacy.py`, `tests/test_artifact_meta_read.py`, `tests/test_artifact_meta_write.py`. All use `tmp_path` fixtures and real git repositories where git is involved; none reads source code.

Acceptance criteria of `4sd62s` that this plan OWNS (meets in phase A on synthetic logs and legacy fixtures):

| AC | Proven by | Note |
|---|---|---|
| AC-4 | E-05 | shuffle and gap/duplicate refusal |
| AC-5 | E-15, E-16 | failure injection, journal recovery, idempotent repair |
| AC-8 | E-09 | at the `query()` level; Order 08 re-demonstrates with `aw find` and `aw attention --format json` once they read the cache, and Order 13 on the real repository |
| AC-17 | E-16 | two-branch merge fixtures |
| AC-18 | E-09, E-13 | companion fixture with `query()`; Order 08 re-demonstrates with `aw find` |
| AC-23 | E-08, E-13 | table set, rebuild on registry change, `EXPLAIN QUERY PLAN` |
| AC-24 | E-03, E-04, E-11 | parsed dependency forms and `none` versus absent, actor/message leak refusal, lineage and graduation preserved separately; Order 04 re-demonstrates the "migration test" form |
| AC-26 | E-10 | every listed change visible on the next read |
| AC-33 | E-05, E-14 | invalid initial events, identity, version, `from` mismatch; revision reads, companion blobs, unversioned result |
| AC-39 | E-06, E-15 | (1) one append per write, (2) owned-field placement refusals, (3) a synthetic migrated log's checkpoint and imported events share `append` 0; (4) the projection side only: `scope_exceptions` rows from a checkpoint and from a finalize append; the finalize WRITER is Order 07, re-demonstrated by Order 13 |

CONTRIBUTES to (owned elsewhere): AC-1a (cold, warm, deleted, corrupt cache parity at the interface; owned by Orders 08/09), AC-1 (all parsing inside `artifact_meta.py`; Order 11), AC-7 (mirror parsers; Orders 08/09), AC-12 (no new dependency; Orders 08/09), AC-14 and AC-14a (1)-(3) (review binding and typed-kind refusals in replay; Orders 04 and 06), AC-15 (event-owned field rules in replay; Order 06), AC-19 (UTC `at` and distinct date columns; Order 04), AC-29 (walkthrough logs never carry `transition`; Order 04), AC-32 (migrated layout accepted by replay; Order 04), AC-34 (`artifact_paths` and path refusals; Order 07), AC-36 (`short_description` refusal; Order 05), AC-40 (managed-prompt mirror parse; Order 04).

Commands: E-17's named pytest run, the bare core gate, `make test-all`, `aw check`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change; implements `4sd62s` sections 4.2, 4.2a, 4.2b, 4.2c, 4.3, 4.4 (`read_at`), 4.5, 4.5a and 4.7, and section 7 phase A step 1. The registry decided here is the plan-step-1 decision that OQ-1 delegates; its field list is recorded in the module and reviewed with this plan. No user-facing document changes (no command changes); Order 12 owns documentation.

## Open questions

### OQ-01: Split this plan into 02a and 02b?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The plan fits the limits (18 E-items, 5 task groups) only because each E-item carries its own tests. If review judges that too dense, split at the natural seam, each half one green merge under C10a: 02a = Task groups 1 to 3 (E-01 to E-10 and E-18: registry, format, replay, loader, cache, freshness; tests registry/replay/cache) and 02b = Task groups 4 and 5 (E-11 to E-17: legacy loader, read interface, `read_at`, write path, repair; tests legacy/read/write), with 02b depending on `executed:<02a id6>` and Order 03 depending on 02b. Owned ACs split as: 02a AC-4, AC-8, AC-23 (1)(2), AC-26, AC-33 (replay part), AC-39 (1)-(3); 02b AC-5, AC-17, AC-18, AC-23 (3), AC-24, AC-33 (`read_at` part), AC-39 (4). Recommendation strength: medium (keep as one plan unless review finds an E-item too large to execute in one pass). Resolved: keep as one plan; `/plan-review` of this plan may apply the split at the stated seam.

### OQ-02: Does an unregistered legacy bullet make a record invalid in phase B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. F-03 measures one-off bullets (`Note`, `Self-note`, `Origin`, `Supersedes-Note`, `Audited-Scope` and others) that no current reader treats as metadata; refusing them would make records unreadable in phase B and change behavior C10a forbids. The legacy loader keeps them as `legacy_unregistered` rows; Order 04's census (AC-20) assigns each a disposition (log field, body section or recorded drop) before the cutover, and the post-cutover log loader refuses unknown fields as 4.2 requires. Recommendation strength: strong.

### OQ-03: Which status does the legacy loader report for the 24 multi-word `- Status:` plans?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The loader stores the raw value verbatim in a legacy-only column and sets `artifacts.status` to the value only when it is a single token, which reproduces `selectors._STATUS_RE` (`(\S+)`) and so today's `aw find` matching (F-08). The `plans_index` reading (whole line) stays reconstructible from the raw column. The phase-B reader plan that retires the second reader records which consumers lose which behavior (4.3), and the migration normalizes these terminal records at the cutover. Recommendation strength: medium. Carrier of the reader decision: ffceq0.

### OQ-04: One module file or a package?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: One file, `agent_workflows/artifact_meta.py`. AC-1's evidence requires that legacy-pattern matches appear "ONLY in `artifact_meta.py` and `migrations/m0001_metadata_v2.py`"; a package would need that criterion reworded. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_registry.py -k registry` with every selected test PASSED, and the output of `python3 -c "from agent_workflows import artifact_meta as m; print(sorted(m.registry_fields('ipd')))"` showing `plan_role`, `review_depth`, `pipeline`, `scope_result`, `short_description` and `item_dependencies`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_registry.py -k envelope` with every selected test PASSED, including named tests for the round trip of a canonical line, refusal of `"abc123\n"` as an id6, refusal of an actor with a `null` key, and refusal of a day-only `at`; quote the assertion that compares `encode_event(decode_line(line))` with `line`.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_registry.py -k refus` with every selected test PASSED, and the printed refusal reasons for: a 301-character `short_description`, a value with a newline, an actor `run_id` containing `ses_` plus 20 characters, `path` values `<home>/a.md (an absolute home-directory path)` and `../a.md`, and the same 5,000-character legacy line accepted with `migration_import=True` and refused without it.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_registry.py -k dependenc` with every selected test PASSED, and the printed stored values for `executed:abc123`, `exists:spec:def456`, `state:spec:approved:def456`, `none`, `unresolved` and an absent field, showing six distinct shapes and `none` different from absent.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_replay.py -k "shuffle or seq or initial or identity or version or append or transition"` with every selected test PASSED; one test per refusal rule name listed in E-05's expected outcome, and the shuffle test asserting equal `State` for 10 random permutations.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_replay.py -k owned` with every selected test PASSED, covering each owned field of E-06 inside and outside its owning append, plus quote the assertion that a gate review with `readiness: go` replays to `state.fields['readiness'] == 'go'` and the assertion that a refinement event with `readiness` is refused.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_replay.py -k "loader or mirror"` with every selected test PASSED, including the test that replaces a valid log with an invalid one and asserts `read()` raises naming the defect and that no `artifacts` row with `valid = 1` remains for that id6.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_cache.py -k schema` with every selected test PASSED, and the output of a `python3 -c` snippet that builds a cache in a temp directory and prints the sorted table names from `sqlite_master`, which must equal the 4.5a table list of E-08.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_cache.py -k "placement or corrupt or fallback or companion"` with every selected test PASSED, including the parity test that compares `query()` output across cold, warm, deleted, corrupted and read-only-state caches, and the companion-backend test asserting the log path is under the resolved companion records root.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_cache.py -k fresh` with every selected test PASSED: one test per AC-26 change listed in E-10, each asserting the next `query()` result, with no explicit rebuild call in the test.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy.py -k "artifact or naming"` with every selected test PASSED, plus `python3 -c "from agent_workflows import artifact_naming as n; print(n.parse_attributed('20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md'))"` showing `ace='agy'`, `model='gemini38flashhigh'`, `type='prompt'`, and `python3 -m pytest -o addopts="" tests/test_artifact_naming_round_trip.py` passing unchanged.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy.py -k "history or review"` with every selected test PASSED, and quote the assertion that the legacy `last_history_day` equals `attention_contract.last_history_at` on the same history lines.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_read.py -k "read or query or incomplete"` with every selected test PASSED, and the four `EXPLAIN QUERY PLAN` outputs named in E-13, each containing `USING INDEX` or `USING COVERING INDEX`.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_read.py -k read_at` with every selected test PASSED, covering the rename case, invalid revision versus absent record, the companion repository, the unversioned placement, and the corrupt blob that leaves no `rev_log_states` row.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_write.py -k "append or create or inject"` with every selected test PASSED: failure injection before and after the commit point for a transition, a create and a rename, each asserting either byte-identical files or a result that names repair; plus the test asserting one `append`, `at` and `actor` across a three-event write.
  - Observed evidence:
  - Result: pending

- [ ] V-16 validates E-16
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_write.py -k "repair or diverge or merge"` with every selected test PASSED, including the double-repair byte-equality test, the missing-body refusal, and the real two-branch `git merge` fixture whose confirmed tail repair keeps the first N log lines byte-identical.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste: `rg -l artifact_meta agent_workflows` output (exactly `agent_workflows/artifact_meta.py`); `git diff --stat` limited to Scope-Paths; `git diff pyproject.toml` (empty); the summary line of the E-17 named pytest run; the bare `python3 -m pytest` summary line with its wall time; the `make test-all` summary line; the before/after `aw check` error and warning counts; the `aw sanitize --agent` result record; and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending

- [ ] V-18 validates E-18
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_registry.py -k op_schema` with every selected test PASSED, and the printed `validate_event` results for: a `review` event with an unknown payload key (refused), a `finalize` event (refused, reason names the missing schema), a `rename` with verb `move` (refused), and a valid `coverage` event (accepted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited only with a justification recorded in the finalize scope reconciliation. This plan must move NO caller: no existing module may import `artifact_meta` when it lands (E-17 proves it). Commit only through `aw commit tve77h -- <paths>`; never push. Run `python3 -m pytest` (core gate), the E-17 named modules and `make test-all`, and paste the actual summary lines. Move the plan to `.aw/records/plans/executed/` only through `aw ipd finalize tve77h`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
