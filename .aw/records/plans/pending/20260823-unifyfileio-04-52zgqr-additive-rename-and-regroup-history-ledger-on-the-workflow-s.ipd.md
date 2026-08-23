# IPD: Additive rename/regroup history ledger on the workflow sidecar

- Date: 2026-08-23
- Kind: child
- Concern: The `aw` rename/regroup engines keep NO durable application-level from->to filename history; the only rename history is git's own (`git mv` + `git log --follow`). A repo-wide grep for `from_name|to_name|rename_ledger|previous_name` returns zero matches. This means a future `aw` audit/undo verb, or a "which Sets did this artifact move through" query, must reconstruct everything from git, which records moves only as opaque path changes and cannot see external/uncommitted references. There IS already a durable, git-tracked, id6-keyed, append-only sidecar (`.aw/records/history.jsonl`) - but it records status/workflow events only, never renames.
- Scope: Add an ADDITIVE rename/regroup record type to the existing sidecar and emit it from the (by then unified) rename path. Touch: agent_workflows/record_history.py (the `append`/schema + a small `append_rename` helper and a reader filter), and ONE call site on the unified rename/regroup engine delivered by Order 03 (or, if executed before the engine is unified, the current `plans_refs.apply_renames`, `research_refs._apply_renames`, and `artifact_rename.run_rename_generic`/`run_group_generic`). Plus tests. Does NOT make the ledger authoritative for anything: id6 already guarantees citation stability and git already records moves, so the ledger is a query/audit convenience only.
- Status: draft
- Set: unifyfileio
- Order: 4
- Highest E allocated: 04
- Author: Gabriele Fariello
- Id: 52zgqr

## Workflow history

- 2026-08-23 draft (Gabriele Fariello): created.

## Goal

Record, on every `aw rename` and `aw group` that actually moves or renames a file, an append-only, id6-keyed audit record `{id6, date, tree, verb, actor, from_name, to_name, message?}` in the EXISTING `.aw/records/history.jsonl` sidecar, reusing its established schema (adding the optional `from_name`/`to_name` fields present only on rename records). The ledger is strictly ADDITIVE and NON-AUTHORITATIVE: no `aw` command's correctness depends on it (deleting the whole ledger changes only what an audit query can report, never whether a rename/citation-rewrite/check succeeds). It is keyed by the stable id6 so it survives future renames; for the id6-less legacy types it degrades gracefully (skip, or a synthetic key, per OQ-01) without erroring.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: Extend the sidecar with a rename record type

- [ ] E-01 Extend `agent_workflows/record_history.py` with an `append_rename(repo_root, *, id6, tree, verb, actor, from_name, to_name, message=None)` helper that writes an append-only JSONL record reusing the existing 6-key schema plus optional `from_name`/`to_name` (absent on status records, present on rename records), and a reader filter (e.g. `read_renames_for(id6)`) built on the existing `read_for`. Keep it schema-compatible: existing status readers must ignore the new fields cleanly.
  - Depends on: none
  - Expected outcome: the sidecar can durably record a rename event, keyed by id6, without breaking existing status records/readers.
  - Execution state: pending

### Task group 2: Emit the record from the rename/regroup path

- [ ] E-02 Emit an `append_rename` record from the rename/regroup engine AFTER the successful `git_mv`, at the single unified apply path if Order 03 has delivered it, else at each of the three current apply points (`plans_refs.apply_renames` after `git_mv` at `plans_refs.py:356`; `research_refs._apply_renames` after `git_mv` at `research_refs.py:254`; `artifact_rename.run_rename_generic`/`run_group_generic` after `git_mv` at `artifact_rename.py:396,528`). Record `from_name`/`to_name` as basenames and `verb` as `rename` or `group`. Only emit on `--apply` (never on dry-run) and only when the name actually changed. Wrap the ledger write so a ledger failure NEVER fails or rolls back the rename (additive, non-authoritative).
  - Depends on: E-01
  - Expected outcome: every applied rename/regroup that changes a name appends exactly one ledger record; dry-runs and no-op renames append nothing; a ledger write error does not break the rename.
  - Execution state: pending

### Task group 3: Handle id6-less types gracefully

- [ ] E-03 Handle the id6-less legacy types (specs/prompts/roadmaps/releases/walkthroughs, which lack a frontmatter `- Id:`): per OQ-01, either skip the ledger record for them (git remains their history) or write a record under a synthetic stable key derived from the name; whichever is chosen, it MUST NOT raise and MUST be covered by a test. Document the choice in the record_history docstring.
  - Depends on: E-01
  - Expected outcome: renaming an id6-less artifact never errors on the ledger path and behaves per the recorded decision.
  - Execution state: pending

### Task group 4: Prove additivity and correctness

- [ ] E-04 Add `tests/test_rename_ledger.py` asserting: (a) an applied plan/research rename appends exactly one id6-keyed `{from_name,to_name,verb}` record; (b) a dry-run and a no-op rename append nothing; (c) ADDITIVITY - performing a rename with the ledger file deleted (or made unwritable) produces an identical rename result (files moved, citations rewritten, exit code) and does not raise; (d) `read_renames_for(id6)` returns the recorded history across multiple renames of the same artifact; (e) an id6-less rename behaves per E-03 without error; and confirm `pytest -n auto` is green.
  - Depends on: E-02, E-03
  - Expected outcome: the ledger is proven additive, non-authoritative, id6-keyed, and correct.
  - Execution state: pending

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

## Scope check

- Over-scope: none. Only a durable, additive record type and its emission are added.
- Under-scope: none. Record type, emission on every applied rename/regroup, id6-less handling, and additivity proof are all covered.

## Required tests / validation

- `tests/test_rename_ledger.py` (E-04) covering emission, dry-run/no-op silence, additivity-under-deletion, multi-rename read, id6-less safety.
- Full suite via `pytest -n auto` (paste actual runner output).

## Spec / documentation sync

- Update the sidecar/history spec (`20260818-1525-02`, referenced by `record_history.py:1`) to document the additive rename record type and its non-authoritative status. If that spec cannot be extended, add the note to the `record_history` docstring and record the spec touch as N/A with reason.

## Open questions

### OQ-01: For id6-less legacy types (specs/prompts/roadmaps/releases/walkthroughs), skip the ledger, or key by a synthetic token?

- Blocking: yes
- Status: open
- Owner: human
- Resolution or deferral rationale: TODO (human). id6-less types have no stable handle, so an id6-keyed record cannot be written straightforwardly. Option A: skip the ledger for them (git remains their history) - simplest, but their rename history is not in the ledger. Option B: key by a synthetic stable token (e.g. the earliest-known name) - fuller ledger, but the key can drift and duplicates git's job. The executor MUST get a human decision before E-03; this also interacts with the deferred id6-rollout (orchestrator Deferred).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [ ] V-01 validates E-01
  - Required evidence: a unit test writes and reads back a rename record via `append_rename`/`read_renames_for`, and asserts an existing status reader ignores the new `from_name`/`to_name` fields without error.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: an applied plan and an applied research rename each append exactly one record with correct `from_name`/`to_name`/`verb`; a dry-run and a no-op rename append nothing (asserted).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: renaming an id6-less artifact does not raise and behaves per the OQ-01 decision (asserted).
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: `tests/test_rename_ledger.py` passes including the additivity test (rename with ledger deleted/unwritable yields identical result and does not raise) and the multi-rename `read_renames_for` history; `pytest -n auto` is green (pasted).
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: one concern - a minimal additive rename/regroup ledger on the existing sidecar - staged safely (schema -> emit -> id6-less handling -> prove additive).

### Execution contract

1. Open questions RESOLVED: OQ-01 (id6-less handling) MUST be resolved by a human before E-03.
2. Scope fence: add ONLY the additive rename record type and its emission on the applied rename/regroup path; reuse the existing sidecar. Do NOT make the ledger authoritative, do NOT build a consumer verb, do NOT backfill from git. If it seems to need more, STOP and report.
3. Honesty rule (hard MUST): when reporting tests passed, paste the ACTUAL runner output; never claim a pass without running the actual command.
4. Commit ONLY this plan's own changed files, path-scoped (`git commit -m msg -- <paths>`); never `git add -A`/bare/`-a`; never push.
5. Lifecycle move: on completion, after every E item is performed and every V item is verified with pasted evidence, append the `## Workflow history` line, set `Status: executed`, `git mv` this file from `pending/` to `executed/`, and make the path-scoped lifecycle commit.
