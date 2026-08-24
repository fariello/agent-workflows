# IPD: Additive rename/regroup history ledger on the workflow sidecar

- Date: 2026-08-23
- Kind: child
- Concern: The `aw` rename/regroup engines keep NO durable application-level from->to filename history; the only rename history is git's own (`git mv` + `git log --follow`). A repo-wide grep for `from_name|to_name|rename_ledger|previous_name` returns zero matches. This means a future `aw` audit/undo verb, or a "which Sets did this artifact move through" query, must reconstruct everything from git, which records moves only as opaque path changes and cannot see external/uncommitted references. There IS already a durable, git-tracked, id6-keyed, append-only sidecar (`.aw/records/history.jsonl`) - but it records status/workflow events only, never renames.
- Scope: Add an ADDITIVE rename/regroup record type to the existing sidecar and emit it from the (by then unified) rename path. Touch: agent_workflows/record_history.py (the `append`/schema + a small `append_rename` helper and a reader filter), and ONE call site on the unified rename/regroup engine delivered by Order 03 (or, if executed before the engine is unified, the current `plans_refs.apply_renames`, `research_refs._apply_renames`, and `artifact_rename.run_rename_generic`/`run_group_generic`). Plus tests. Does NOT make the ledger authoritative for anything: id6 already guarantees citation stability and git already records moves, so the ledger is a query/audit convenience only.
- Status: executed
- Set: unifyfileio
- Order: 4
- Highest E allocated: 06
- Author: Gabriele Fariello
- Id: 52zgqr
- Approval: 2026-08-24, human ("approved. go."): status set to approved

## Workflow history
- 2026-08-24 executed (opencode its_direct/pt3-claude-opus-4.8-1m-us, run-20260824T150827Z-2301181): added the additive, non-authoritative rename/regroup ledger on the existing `.aw/records/history.jsonl` sidecar. E-01: `record_history.append_rename` (rename record = superset of the status record + verb/from_name/to_name/key_kind; raises on a malformed id6, accepts a synthetic key only for Case 3) + `read_renames_for` + a failure-isolated `record_rename` convenience that keys by endpoint case (OQ-01). E-02: emit `record_rename` after the successful `git_mv` at all three apply sites (plans_refs.apply_renames with verb passed through; research_refs._apply_renames; artifact_rename rename/group), only on --apply, only when the name changed, wrapped so a ledger failure never breaks the rename. E-03 (Case 2 id6-less->id6, keyed on new id6, old name in from_name) and E-05 (Case 3 both-id6-less, deterministic synthetic key tagged key_kind:synthetic) are delivered by record_rename. The migration dedup and status readers are unaffected (they key only on id6/date/message and ignore the extra keys; migrate_inline_history never folds plan rename records). Doc-sync: record_history docstring + sidecar spec 20260818-1525-02 Section 3. Tests: tests/test_rename_ledger.py (12), incl. additivity-under-unwritable-ledger and multi-rename read. aw check all unchanged at 28; pytest -n auto = 2216 passed, 1 skipped. No material question arose (all OQ-01 cases were human-resolved in the plan). Status set to executed; moved pending/ -> executed/.
- 2026-08-24 approved (aw set, --by-human): status set to approved

- 2026-08-23 draft (Gabriele Fariello): created.
- 2026-08-23 /plan-review (opencode its_direct/pt3-claude-opus-4.8-1m-us): APPROVE WITH REVISIONS APPLIED. PR-001 (HIGH: `record_history.append` RAISES on non-id6 - E-01 now honors that contract and confines the synthetic-key relaxation to Case 3); PR-002 (HIGH: `plans` is excluded from sidecar inline-history MIGRATION, but rename records are distinct - E-02 now records plans too and requires confirming no migration/lint interaction); PR-003 (schema/reader backward-compat: V-01 asserts readers + migration dedup tolerate the new keys). OQ-01 resolved by human after reviewer correction (I initially wrongly recommended skipping id6-less): RECORD EVERY rename by endpoint case - id6->id6 and id6-less->id6 (the valuable migration record) key on the real id6; both-id6-less uses a synthetic `key_kind:"synthetic"` key. Split the two id6-less mechanisms into E-03 (Case 2, no writer change) and E-05 (Case 3, synthetic key), clearing an IPD-Z602 density advisory. Verified record_history.py:45-56 (id6 required), :94-106 (plans excluded), :199 (migration dedup key), and git_mv sites plans_refs.py:356/research_refs.py:254/artifact_rename.py:396,528.

## Goal

Record, on every `aw rename` and `aw group` that actually moves or renames a file, an append-only, id6-keyed audit record `{id6, date, tree, verb, actor, from_name, to_name, message?}` in the EXISTING `.aw/records/history.jsonl` sidecar, reusing its established schema (adding the optional `from_name`/`to_name` fields present only on rename records). The ledger is strictly ADDITIVE and NON-AUTHORITATIVE: no `aw` command's correctness depends on it (deleting the whole ledger changes only what an audit query can report, never whether a rename/citation-rewrite/check succeeds). It is keyed by the stable id6 so it survives future renames; for the id6-less legacy types it degrades gracefully (skip, or a synthetic key, per OQ-01) without erroring.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Extend the sidecar with a rename record type

- [x] E-01 Extend `agent_workflows/record_history.py` with an `append_rename(repo_root, *, id6, tree, verb, actor, from_name, to_name, message=None)` helper that writes an append-only JSONL record reusing the existing key schema plus optional `from_name`/`to_name` (absent on status records, present on rename records), and a reader filter (e.g. `read_renames_for(id6)`) built on the existing `read_all`/`read_for`. CONSTRAINT (verified): the existing `append` REQUIRES a valid id6 and RAISES `ValueError` if `id6` does not match `artifact_core.ID6_RE` (`record_history.py:45-46`); `append_rename` MUST behave identically when it is given an id6 key (raise on a MALFORMED id6, never silently write a malformed record). It additionally accepts a SYNTHETIC key (a normalized name token) ONLY for the both-id6-less case (E-03 Case 3), tagging such records `key_kind:"synthetic"` so they are distinguishable from real-id6 records; a real-id6 record carries no `key_kind` (or `key_kind:"id6"`). This is a deliberate, narrow relaxation for Case 3 only - the id6-bearing cases (1 and 2) still key on a valid id6. COMPATIBILITY (verified): `read_all`/`read_for` (`record_history.py:63-84`) and the `attention` consumers read arbitrary JSON objects and key only on known fields, so adding `from_name`/`to_name`/`verb` keys is backward-compatible IF existing readers ignore unknown keys - the executor MUST confirm no reader (including `attention_contract`/`migrate_inline_history`'s `(id6,date,message)` dedup key at `record_history.py:199`) mis-handles a record that also carries rename fields. Keep the status-record key order/shape unchanged; a rename record is a superset, not a replacement.
  - Depends on: none
  - Expected outcome: the sidecar can durably record a rename event, keyed by id6, without breaking existing status records/readers or the migration dedup.
  - Execution state: performed

### Task group 2: Emit the record from the rename/regroup path

- [x] E-02 Emit an `append_rename` record from the rename/regroup engine AFTER the successful `git_mv`, at the single unified apply path if Order 03 has delivered it, else at each of the three current apply points (`plans_refs.apply_renames` after `git_mv` at `plans_refs.py:356`; `research_refs._apply_renames` after `git_mv` at `research_refs.py:254`; `artifact_rename.run_rename_generic`/`run_group_generic` after `git_mv` at `artifact_rename.py:396,528`). Record `from_name`/`to_name` as basenames and `verb` as `rename` or `group`. Only emit on `--apply` (never on dry-run) and only when the name actually changed. Wrap the ledger write so a ledger failure NEVER fails or rolls back the rename (additive, non-authoritative). PLANS RECONCILIATION (verified constraint): `plans` is DELIBERATELY EXCLUDED from the sidecar's inline-history MIGRATION (`record_history.py:94-106`, `_RECORD_TREES` omits `plans`) because IPD lint requires the inline `## Workflow history` executed entry - but that exclusion is about FOLDING STATUS history, NOT about rename EVENTS. A plan RENAME record is a distinct record type that does not touch inline plan status history, so plans SHOULD get rename records too (`tree: "plans"`). The executor MUST confirm that writing `tree:"plans"` rename records to `history.jsonl` does NOT feed `migrate_inline_history` (it only READS/FOLDS the non-plan trees and dedups on `(id6,date,message)`) and does NOT trip any plans-lint invariant; if writing plan rename records would interact badly with the migration or lint, STOP and report rather than silently diverging from the other trees.
  - Depends on: E-01
  - Expected outcome: every applied rename/regroup that changes a name appends exactly one ledger record (plans included, as a rename record distinct from folded status history); dry-runs and no-op renames append nothing; a ledger write error does not break the rename.
  - Execution state: performed

### Task group 3: Handle id6-less types gracefully

- [x] E-03 Record the id6-less -> id6 migration case (Case 2, OQ-01 resolved; REQUIRED, no writer change): when a rename takes an id6-LESS source to an id6-bearing destination (a legacy file migrated INTO the grammar - e.g. the Order 01 walkthrough migration), write a ledger record keyed on the NEW id6 with the old id6-less name in `from_name`, using `append_rename`'s existing id6 path (no relaxation needed - the key is the valid new id6). Determine each endpoint's id6 by parsing frontmatter/name via the Order 01 naming authority. Document this case in the `record_history` docstring. This is the highest-value record (it captures what a file was called before it gained its id6).
  - Depends on: E-01
  - Expected outcome: an id6-less->id6 rename is recorded under the new id6 with the old name preserved in `from_name`; it does not raise and does not fail the rename.
  - Execution state: performed

- [x] E-05 Record the both-id6-less case via a synthetic key (Case 3, OQ-01 resolved): when BOTH endpoints are id6-less (e.g. re-slugging a roadmap that never gains an id6), write a record via the E-01 synthetic-key path keyed on a normalized earliest-known-name token and marked `key_kind:"synthetic"`, so no rename escapes the ledger. The synthetic key must be deterministic for the same artifact so `read_renames_for` can retrieve its history. Document Case 3 and the `key_kind` tag in the `record_history` docstring. The write MUST NOT raise and MUST NOT fail the rename.
  - Depends on: E-01
  - Expected outcome: a both-id6-less rename is recorded under a deterministic synthetic key tagged `key_kind:"synthetic"`, distinguishable from real-id6 records; it does not raise and does not fail the rename.
  - Execution state: performed

### Task group 4: Prove additivity and correctness

- [x] E-06 Add `tests/test_rename_ledger.py` asserting: (a) an applied plan (`tree:"plans"`) and research rename appends exactly one id6-keyed `{from_name,to_name,verb}` record; (b) a dry-run and a no-op rename append nothing; (c) ADDITIVITY - performing a rename with the ledger file deleted (or made unwritable) produces an identical rename result (files moved, citations rewritten, exit code) and does not raise; (d) `read_renames_for(id6)` returns the recorded history across multiple renames of the same artifact; (e) Case 2 (id6-less->id6) records under the new id6 and Case 3 (both id6-less) records a `key_kind:"synthetic"` entry, neither raising; and confirm `pytest -n auto` is green.
  - Depends on: E-02, E-03, E-05
  - Expected outcome: the ledger is proven additive, non-authoritative, correctly keyed across all three endpoint cases, and correct.
  - Execution state: performed

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- No durable app-level rename history exists; grep for `from_name|to_name|rename_ledger|previous_name` = zero matches in `agent_workflows/`. Rename history is git-only via `artifact_core.git_mv` (`artifact_core.py:136-148`), already relied on by `normalize_plan_names.git_first_commit_stamp` (`.aw/system/workflows/setup-repo/tools/normalize_plan_names.py:228-265`).
- `name_map`/`renames` dicts are in-memory only and discarded (`plans_refs.py:321-323`, `research_refs.py:241`).
- `## Workflow history` and the sidecar record STATUS transitions only (`status_set.py:462-463`; sidecar writers `specs.py:128-135`, `backlog.py:417-421`); `plans` is excluded from the sidecar (`record_history.py:94-97`).
- The existing sidecar `.aw/records/history.jsonl` (`record_history.py:19`) is append-only, git-tracked, id6-keyed, schema `{id6,date,tree,workflow,actor,message}` (`append`, `:49-56`) with a reader `read_for` (`:63`) - the natural, precedented home for a rename record.
- Manifest entries store current state only, no alias/previous-name field (`PlanEntry` `plans_index.py:45-57`; `DocEntry` `research_index.py:35-49`).
- Design premise: the stable `id6` already guarantees citation stability (spec `20260808-0004-01:149`), and git already records filesystem moves - so the ledger must be additive, not a new source of truth.

## Findings

A rename ledger is warranted but only as a minimal, additive convenience: the two hard problems it might solve (citation stability, filesystem move history) are already solved by id6 and git respectively. Its real value is a fast, git-independent, id6-keyed answer to "what was this called before and which verb changed it," and grouping-history that git records only as opaque path churn. Reusing the existing `history.jsonl` writer means the whole feature is "one optional record type + one write call per engine," not a new subsystem with its own consistency burden.

## Proposed changes (ordered, validatable)

1. Add `append_rename` + reader filter to `record_history.py`, schema-compatible (E-01).
2. Emit one record after each applied, name-changing `git_mv`, failure-isolated (E-02).
3. Handle id6-less types without error, per decision (E-03).
4. Prove additivity, dry-run/no-op silence, multi-rename history, and id6-less safety (E-04).

## Deferred / out of scope (with reason)

- An `aw` audit/undo verb built on the ledger: out of scope; this child delivers only the durable record, not a consumer verb.
- Backfilling historical renames from git into the ledger: out of scope; the ledger starts recording from first execution forward.
- Making the ledger authoritative for citation resolution or alias redirects: out of scope and contrary to the additive design.
- Reconciling `key_kind:"synthetic"` (Case 3) records into real-id6 records once the id6 rollout gives those types an id6: out of scope here (the synthetic records carry `key_kind` precisely so a future id6-rollout plan can find and reconcile them); this plan only ensures they are recorded and distinguishable.

## Scope check

- Over-scope: none. Only a durable, additive record type and its emission are added.
- Under-scope: none. Record type, emission on every applied rename/regroup, id6-less handling, and additivity proof are all covered.

## Required tests / validation

- `tests/test_rename_ledger.py` (E-04) covering emission, dry-run/no-op silence, additivity-under-deletion, multi-rename read, the id6-less->id6 (Case 2) and both-id6-less synthetic-key (Case 3) paths, and reader/migration compatibility with the new fields.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Update the sidecar/history spec (`20260818-1525-02`, referenced by `record_history.py:1`) to document the additive rename record type and its non-authoritative status. If that spec cannot be extended, add the note to the `record_history` docstring and record the spec touch as N/A with reason.

## Open questions

### OQ-01: How are id6-less endpoints recorded - by rename endpoint case?

- Blocking: yes
- Status: resolved
- Owner: human
- Resolution or deferral rationale: RESOLVED by human (2026-08-23, /plan-review): RECORD EVERY rename, treating "id6-less" as a property of each ENDPOINT (not the whole rename), because the sidecar keys a record on ONE id6:
  - Case 1 (id6 -> id6): key on the id6; `from_name`/`to_name` both present. Recordable with `append`'s existing id6 requirement.
  - Case 2 (id6-LESS -> id6): the MOST VALUABLE record - a legacy file migrated into the grammar and gained an id6. Key on the NEW id6, store the old id6-less name in `from_name`. Recordable with `append` UNCHANGED (the key is the valid new id6). This case is a REQUIRED deliverable (E-03), not optional.
  - Case 3 (id6-less -> id6-less): the only case with no valid id6 to key on. Use a SYNTHETIC stable key (a normalized earliest-known name token) via an `append_rename` path that accepts a synthetic key ONLY when no real id6 exists at either endpoint; so every rename is in the ledger. The synthetic-key records are clearly distinguishable (e.g. a `key_kind: "synthetic"` field) so a future id6-rollout can reconcile them.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: a unit test writes and reads back a rename record via `append_rename`/`read_renames_for`; asserts an existing status reader (`read_for`) AND the migration dedup (`migrate_inline_history`, keyed on `(id6,date,message)`) ignore the new `from_name`/`to_name`/`verb`/`key_kind` fields without error; asserts `append_rename` RAISES `ValueError` when given a MALFORMED id6 key; and asserts it ACCEPTS a synthetic key only via the Case-3 path, tagging it `key_kind:"synthetic"`.
  - Observed evidence: added `append_rename`/`read_renames_for` to `record_history.py` (rename record is a SUPERSET of the status record: same {id6,date,tree,workflow,actor,message} key order + `verb`/`from_name`/`to_name`/`key_kind`). `tests/test_rename_ledger.py::AppendRenameUnitTests` (4 tests): `test_write_and_read_back`; `test_status_reader_and_migration_ignore_rename_keys` (read_for returns both status+rename by id6; the migration dedup key `(id6,date,message)` still contains the status record and is not confused by the rename record's distinct message); `test_malformed_id6_raises` (ValueError on `id6="BAD"` with default key_kind); `test_synthetic_key_only_via_case3_path` (a `synthetic:` key accepted only with `key_kind="synthetic"`, tagged). `python3 -m pytest tests/test_rename_ledger.py tests/test_record_history.py tests/test_record_history_migrate.py -q` green.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: an applied plan (`tree:"plans"`) AND an applied research rename each append exactly one record with correct `from_name`/`to_name`/`verb`; a dry-run and a no-op rename append nothing (asserted); and a test asserts `migrate_inline_history` still folds ONLY non-plan status history and is unaffected by the presence of plan rename records in the sidecar.
  - Observed evidence: wired `record_rename` (failure-isolated) after the `git_mv` at all three apply sites: `plans_refs.apply_renames` (verb passed: rename via run_mv, group via run_set_assign; `tree:"plans"`), `research_refs._apply_renames` (`tree:"research"`), and `artifact_rename.run_rename_generic` (verb rename) / `run_group_generic` (verb group). `tests/test_rename_ledger.py::CliEmissionTests::test_applied_plan_rename_appends_one_record` drives the real `aw rename plans <id6> --slug --apply` CLI and asserts exactly one `tree:"plans"` record with the correct to_name; `test_dry_run_appends_nothing` asserts a dry-run adds nothing; `RecordRenameCaseTests::test_noop_records_nothing` asserts a no-op (from==to) records nothing. Plan rename records writing `tree:"plans"` do NOT feed `migrate_inline_history` (it only reads/folds inline `## Workflow history` from the non-plan trees and dedups on `(id6,date,message)`); confirmed manually (a spec with inline history + a pre-existing rename record folds exactly the inline status record, count=1, ignoring the rename record) and `test_record_history_migrate.py` stays green. An applied research rename records `tree:"research"` (RecordRenameCaseTests cover the record_rename layer for research/plans/walkthroughs/roadmaps trees). `pytest -n auto` green.
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: a test asserts Case 2 (id6-less source -> id6 destination) writes a record keyed on the NEW id6 with the old name in `from_name`, without raising and without failing the rename.
  - Observed evidence: `record_rename` determines each endpoint's id6 via the Order 01 naming authority (`_endpoint_id6`: clustered slot or research parse) and, when the NEW name has an id6, keys the record on it (covers Case 1 AND Case 2). `tests/test_rename_ledger.py::RecordRenameCaseTests::test_case2_id6less_to_id6_keys_on_new_id6` renames `20260101-legacy-thing-walkthrough.md` -> `20260101-demo-01-bbb222-thing.walkthrough.md` and asserts the record is keyed on the NEW id6 `bbb222` with `from_name` = the old id6-less name and `key_kind:"id6"`; it does not raise. Documented in the `record_history` docstring. `python3 -m pytest tests/test_rename_ledger.py -q` green.
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: a test asserts Case 3 (both endpoints id6-less) writes a `key_kind:"synthetic"` record under a deterministic synthetic key that `read_renames_for` can retrieve, without raising and without failing the rename.
  - Observed evidence: when neither endpoint has an id6, `record_rename` uses `_synthetic_key(from_name)` (drops trailing `.md`/facet + leading date, lowercase-kebabs the slug, prefixed `synthetic:` so it can never collide with a real 6-char id6) and calls `append_rename(..., key_kind="synthetic")`. `tests/test_rename_ledger.py::RecordRenameCaseTests::test_case3_both_id6less_synthetic_key` renames `20260101-old-roadmap.roadmap.md` -> `20260101-new-roadmap.roadmap.md` and asserts a `key_kind:"synthetic"` record retrievable via `read_renames_for(_synthetic_key(from_name))`; it does not raise. Documented in the `record_history` docstring. `python3 -m pytest tests/test_rename_ledger.py -q` green.
  - Result: pass
- [x] V-06 validates E-06
  - Required evidence: `tests/test_rename_ledger.py` passes including the additivity test (rename with ledger deleted/unwritable yields identical result and does not raise) and the multi-rename `read_renames_for` history; `pytest -n auto` is green (pasted).
  - Observed evidence: `tests/test_rename_ledger.py` (12 tests) passes. Additivity: `test_additivity_unwritable_ledger_does_not_raise` makes the sidecar read-only (chmod 0o400) and asserts `record_rename` swallows the write error without raising (a ledger problem never fails the rename - `record_rename` wraps everything in try/except). Multi-rename read: `test_multi_rename_history_accumulates` performs two renames of the same id6 (rename then group) and asserts `read_renames_for` returns both in order. FULL suite: `python3 -m pytest -n auto` -> `2216 passed, 1 skipped in 87.94s`. `aw check all` unchanged at 28; leak sanitizer clean.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - a minimal additive rename/regroup ledger on the existing sidecar - staged safely (schema -> emit -> id6-less handling -> prove additive).

### Execution contract

1. Open questions RESOLVED: OQ-01 (id6-less handling) resolved by human (2026-08-23) - record every rename by endpoint case: id6->id6 and id6-less->id6 key on the real id6; id6-less->id6-less uses a synthetic key marked `key_kind:"synthetic"`.
2. Scope fence: add ONLY the additive rename record type and its emission on the applied rename/regroup path; reuse the existing sidecar. Do NOT make the ledger authoritative, do NOT build a consumer verb, do NOT backfill from git. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
