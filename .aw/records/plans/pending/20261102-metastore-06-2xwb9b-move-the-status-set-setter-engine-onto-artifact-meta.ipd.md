# IPD: Move the status_set setter engine onto artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` 4.8 makes the `status_set` engine (the single setter engine since spec `wy9aru`) the ONE place where every status setter changes to write through `artifact_meta`, and section 7 step 4 orders it first among the phase-B writers. Today the engine edits Markdown itself. Measured 2026-11-02 at `0cbfcc706`: `agent_workflows/status_set.py` is 4,571 lines with 20 `re.compile`/`re.match`/`re.search`/`re.finditer`/`re.split` metadata sites (7 module-level patterns `_ID_RE`, `_STATUS_RE`, `_SET_RE`, `_HISTORY_HDR_RE`, `_GATE_KIND_RE`, `_GATE_REF_RE`, `_GATE_SUMMARY_RE`); `_prepare_status_change` rewrites the status bullet, YAML `status:` or prompt comment, 13 optional bullet fields, the `- Approval:`/`- Readiness:` attestations and the `## Workflow history` line in a line list; `apply_status_change` writes with `artifact_core.atomic_write`, moves with `artifact_core.git_mv`, and appends the gitignored sidecar through `record_history.append_advisory`; `run_set_command` writes an orchestrator's retirement history line with a raw `Path.write_text`. The `->reviewed` attestation predicate `review_findings.review_attestation_missing` accepts any parseable record, so the 24 `specflow` refinement records for spec `18hh1u` would attest it (4.4 SR-601). C10a requires the move to keep today's on-disk bullet format and to pass the core tier at the merge, and 3c requires this plan to name each moved behavior and the test that checks it.
- Scope: Phase B, section 7 step 4, first writer. (1) Add to `artifact_meta` the LEGACY-format write path: `append` renders its events into today's bullet block, status mirror and `## Workflow history` line (no log file is written in phase B), with a `dry_run` preview, a source-digest freshness check, a path-keyed target for id-less legacy records, the per-artifact lock, the disposition move, the specs/backlog sidecar append, and the same event-owned field rules as the log format (AC-15, AC-14a (1)-(3)). (2) Change `status_set._prepare_status_change`, `apply_status_change` and the orchestrator retirement line in `run_set_command` to build events and call `artifact_meta.append` once per record. (3) Move `status_set`'s own metadata READS (`read_artifact_record`, `inventory_all_artifacts`, `_format_status_transition_line`, `plan_priority_work_kind_problems`, `read_item_dependencies_value`, the backlog gate-default inputs) onto `artifact_meta.resolve`/`read`/`query`. (4) Make `review_findings.review_attestation_missing` require a `gate` review (4.4 SR-601, AC-14a (4)). EXCLUDES: the HEAD-status read in `_prepare_status_change` (`check_engine._blob_text`/`_status_meta`, Order 09 `t4gl15` E-04); the other writers (`specs`, `backlog`, `releases`, `prompts`, `ipd_authoring`, finalize, retirement, coverage and review writers; Order 07 `xexn45`); deleting the `releases.set_*_line`/`backlog.set_*_line` helpers (Order 11 `9o83cr`); the log format (Order 13 `cxxmyv`).
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/artifact_meta.py, agent_workflows/review_findings.py, tests/test_status_set_meta_writer.py, tests/test_artifact_meta_legacy_write.py, tests/test_spec_review_gate_kind.py, .aw/records/plans/pending/20261102-metastore-06-2xwb9b-move-the-status-set-setter-engine-onto-artifact-meta.ipd.md
- Item-Dependencies: executed:tve77h, executed:7ehv8l
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 6
- Highest E allocated: 15
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 2xwb9b
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED; review record .aw/records/reviews/20261102-metastore-06-2xwb9b-move-the-status-set-setter-engine-onto-artifact-meta.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make every status change that the `status_set` engine performs a single `artifact_meta.append` call, while the bytes it writes stay exactly today's bullet format, so the cutover (Order 13) changes the storage in one place and no setter behavior changes before it.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Every new test module sets `pytestmark = pytest.mark.core`, builds fixtures in `tmp_path` (real `git init` where git is involved), drives `cli.main` or the public functions, and asserts on file bytes, exit codes and printed output. No test reads production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: pin today's behavior

- [ ] E-01 Run the 26 existing behavior tests named in the Findings table W/R rows (the "Baseline modules" command in Required tests) on the unchanged tree and record the per-module pass counts; dump `status_set.inventory_all_artifacts(<this repo>)` as sorted JSON (`path`, `record_type`, `id6`, `set_id`, `status`) to `.aw/state/2xwb9b/inventory-before.json` (gitignored and inside the workspace; a runner lane may refuse writes outside it); save `aw check --agent` to `.aw/state/2xwb9b/check-before.jsonl`; and run `tests/test_artifact_meta_write.py` (tve77h's log-branch write and repair tests) and record its pass count.
  - Depends on: none
  - Expected outcome: every baseline test passes before any edit; the inventory dump and the `aw check` baseline exist; the tve77h write module passes.
  - Execution state: pending

- [ ] E-02 Add `tests/test_status_set_meta_writer.py` (core) that pins, against the UNCHANGED code, the write behaviors that no existing test checks (Findings rows W-04, W-05 position, W-09 refusal, W-14 single-line case, W-18 heading creation, W-16 position): a plan with no `- Status:` gets one inserted after `- Date:`; a research report with a `---` block and no `status:` gets one inserted before the closing `---`; `aw backlog set` on an item carrying only `- Kind: chore` writes `- Work-Kind: chore` and no `- Kind:` line; gate bullets land directly after `- Status:` in `Gate-Kind`, `Gate-Ref`, `Gate-Summary` order; `- Approval:` lands directly after `- Id:`; a plan with no `## Workflow history` gets the heading before its first `## ` and a prompt gets it at the end; `aw ipd set to-review <plan> --from-spec zzzzzz` exits nonzero naming `zzzzzz` with the file byte-identical. Each test compares full file bytes with an expected literal.
  - Depends on: E-01
  - Expected outcome: the new module passes on the unchanged code, so it can only fail later if the move changes bytes.
  - Execution state: pending

### Task group 2: the legacy-format writer in artifact_meta

- [ ] E-03 In `artifact_meta.py`, make `append` dispatch on the TARGET artifact's on-disk format through `_storage_format(records_root, target)`, which returns `log` when `<records_root>/meta/<id6>.jsonl` exists for the target and `legacy` otherwise (so in phase B every real record writes the legacy format, since no log exists before the cutover, while tve77h's synthetic-log tests in `tests/test_artifact_meta_write.py` keep exercising the log branch unchanged; a repository-wide `legacy` switch would silently route those tests to the legacy branch and break them at this merge, contrary to C10a; Order 13 replaces the rule) and implement the LEGACY branch: validate the events with the same writer rules the log branch uses (`validate_new_events` and the event-owned field rules of tve77h E-03/E-06) BEFORE any write; take `platform_lock.held(<state>/locks/meta-<key>.lock)`; render the events into the current `.md` text (status mirror for bullet, `---` YAML and `aw-prompt` comment forms with the insertion rules pinned in E-02; one bullet edit per `set`/`unset`, reusing the existing pure value writers `releases.set_*_line` and `backlog.set_release_exempt_*_line`/`set_close_evidence_line` for the fields they own; the `- Kind:` to `- Work-Kind:` canonicalization; the newest-first history line under `## Workflow history`); and return the rendered text. Test module `tests/test_artifact_meta_legacy_write.py`.
  - Depends on: E-02
  - Expected outcome: for each pinned E-02 case and each W-row fixture, rendering the equivalent events produces byte-identical text to today's setter output; `tests/test_artifact_meta_write.py` passes unchanged with the E-01 count; an artifact with a `meta/<id6>.jsonl` takes the log branch and one without takes the legacy branch.
  - Execution state: pending

- [ ] E-04 Add the phase-B write arguments to `append`: `dry_run=True` returns a `WritePreview` (rendered text, destination path, `changed` flag) and writes nothing; `legacy_render=LegacyRender(tag, day, actor_label)` carries the exact history-line token, day and actor label that today's line uses (removed with the legacy branch at the cutover; OQ-02); the target may be the handle returned by `artifact_meta.resolve(path)` so the 14 id-less legacy specs stay settable by path (OQ-03); the freshness check compares the source digest that `read`/`resolve` returned (`State.source_digest`) with the current file and refuses a changed file. Test module `tests/test_artifact_meta_legacy_write.py`.
  - Depends on: E-03
  - Expected outcome: a dry-run returns the same text a real write produces and leaves every file byte-identical; an append after an out-of-band edit refuses naming the file; an id-less spec handle resolves and writes.
  - Execution state: pending

- [ ] E-05 Complete the legacy branch's write steps in today's order: disposition move first through `record_placement.resolve_transition_path` and `artifact_core.git_mv` against the record's git root (`project_context.record_git_root` for a companion backend), then `artifact_core.atomic_write` of the rendered text (the phase-B commit point), then the belt-and-braces source unlink, then for `specs` and `backlog` records the `record_history.append_advisory` sidecar record with today's `tree`, `workflow`, `actor`, `message` and `date` values, then the cache rows (best effort); a failure before the content write leaves every file and the sidecar unchanged and raises, as `tests/test_history_write_order.py` requires. Test module `tests/test_artifact_meta_legacy_write.py`.
  - Depends on: E-04
  - Expected outcome: a spec moved `draft` to `to-review` is `git mv`-staged in its new directory with the rendered bytes; a backlog append writes exactly one sidecar record; a plan append writes none; a read-only destination raises `OSError` with the source byte-identical and no sidecar record.
  - Execution state: pending

- [ ] E-06 Prove the event-owned field rules hold in the legacy branch exactly as in the log branch (AC-15, AC-14a (1)-(3)): `set readiness` refused alone and beside a `review` event; a gate `review` event carrying `readiness: go` renders `- Readiness: go`; `set coverage` refused while an `op: coverage` event renders the three `Coverage*` bullets; a generic `set approval` refused, a `transition` to `approved` with `set approval` in the same append renders `- Approval:`, a `transition` away from `approved` without `unset approval` refused; a backward plan `transition` to `draft` or `to-review` without `unset readiness` refused; a `gate` review with a refinement verdict refused; a `refinement` review with `readiness` refused; three `refinement` rounds appended in turn replay in `seq` order. Test module `tests/test_artifact_meta_legacy_write.py`.
  - Depends on: E-03
  - Expected outcome: every refusal leaves the file byte-identical and names the rule; every accepted append renders the expected bullets.
  - Execution state: pending

### Task group 3: move the status_set write paths

- [ ] E-07 Rewrite `status_set._prepare_status_change` to build, instead of a line list, one event list per record: a `transition` (`from` the current status, `to` the normalized target) or, for a same-status write, a `note`; one `set`/`unset` per supplied flag (`gate_kind`/`gate_ref`/`gate_summary`, `blocks_release`, `release_exempt_kind`/`release_exempt_ref`, `from_backlog` plus the inherited gate from `inherit_from_backlog_release_gate`, `from_spec`, `item_dependencies`, `priority`, `work_kind`, `graduated_to`, the backlog default gate from `backlog.decide_gate_default`, `close_evidence` on a SATISFIED close); the owned attestations in the same append (`set approval` on entering `approved` when none exists, `unset approval` on leaving it, `unset readiness` on a backward move to `draft`/`to-review`, `unset` of the gate fields on leaving the gate status); and a `LegacyRender` carrying today's tag (`same-status`, the target status, or for specs the target status on a same-status write), day (the specs `--date` override or `artifact_core.utc_history_date`) and actor label (with the `--by-human`, `--allow-open-questions`, `--allow-terminal-reopen` and `--allow-unresolvable-release-sentinel` suffixes). The duplicate check keeps `same_status_message_is_duplicate`. `_PreparedStatusChange.updated_text` is filled from `artifact_meta.append(..., dry_run=True)`, so `specs.validate_spec` and `check_engine.evaluate_blocking_close(item_text=...)` still judge the rendered result.
  - Depends on: E-05, E-06
  - Expected outcome: `_prepare_status_change` no longer edits Markdown lines; the dry-run and batch-refusal paths print the same output as before.
  - Execution state: pending

- [ ] E-08 Rewrite `status_set.apply_status_change` to call `artifact_meta.append` once with the prepared events and `LegacyRender`, and delete its own `git_mv`, `atomic_write`, source unlink and `record_history.append_advisory` code; keep the no-op early return, the spec conformance backstop (on the preview text) and the post-move citation rewrite through `artifact_refs.post_relocation_citation_rewrite`.
  - Depends on: E-07
  - Expected outcome: `status_set.py` contains no call to `atomic_write`, `git_mv`, `write_text` on a record, or `record_history`; every W-row baseline test still passes.
  - Execution state: pending

- [ ] E-09 Replace the orchestrator retirement history write in `status_set.run_set_command` (the `_prepend_workflow_history_entry` plus `orch.path.write_text` block that records "child <id6> retired <status>") with an `artifact_meta.append` of one `note` event on the orchestrator carrying `LegacyRender("same-status", <day>, <actor>)`; then delete `_prepend_workflow_history_entry` and `_HISTORY_HDR_RE` from `status_set`.
  - Depends on: E-08
  - Expected outcome: `tests/test_orchestrator_child_retired.py::OrchestratorChildRetiredTests::test_retirement_appends_orchestrator_history_and_commits_both` passes unchanged and the orchestrator line is byte-identical to before.
  - Execution state: pending

### Task group 4: move the status_set reads and the review-kind rule

- [ ] E-10 Change `status_set.read_artifact_record` and `inventory_all_artifacts` to take `id6`, `status`, `set_id` and `record_type` from `artifact_meta.resolve`/`artifact_meta.read`/`artifact_meta.query` (type detection by path stays, since it reads no file content); `ArtifactRecord.raw_text` stays as the body text for body-prose consumers (open-question gates, N3); delete `_ID_RE`, `_STATUS_RE`, `_SET_RE` and the two inline YAML regexes. Then dump the inventory again to `.aw/state/2xwb9b/inventory-after.json`.
  - Depends on: E-01, E-08
  - Expected outcome: the before and after inventory dumps are identical; `tests/test_status_set_metadata_region.py` and `tests/test_selector_resolver_matrix.py` pass unchanged.
  - Execution state: pending

- [ ] E-11 Change the remaining `status_set` metadata reads to cached fields: `_format_status_transition_line` (priority, blocks_release, gate kind and ref), `plan_priority_work_kind_problems` (priority and work kind; same `ipd_schema.parse_plan_priority`/`parse_plan_work_kind` judgement), `read_item_dependencies_value` (raw `item_dependencies` declaration), and the backlog gate-default inputs in `_prepare_status_change` (`work_kind`, `blocks_release`, the release exemption pair; today `backlog.parse_item` and `selectors.read_front_matter_blocks_release` on in-memory text). `_format_status_transition_line(rec, dest_path, norm_stat, term, ...)` KEEPS its `ArtifactRecord` signature (it reads the cached fields for `rec` internally), because `tests/test_blocks_release_reader_bounding.py` calls it directly and must pass unchanged; only the text-taking `plan_priority_work_kind_problems` and `read_item_dependencies_value`, whose only callers are inside `status_set.py` (measured: no test calls them), change to take a `State`.
  - Depends on: E-10
  - Expected outcome: `rg -n "re\.(compile|match|search|finditer|split)" agent_workflows/status_set.py` lists only non-metadata patterns (none of `Id`, `Status`, `Set`, `Priority`, `Gate-`, `Kind`, `Work-Kind`, `Approval`, `Readiness`, `Workflow history`); the R-row baseline tests pass.
  - Execution state: pending

- [ ] E-12 Change `review_findings.review_attestation_missing(repo_root, subject_id6, subject_type)` to pass only when `artifact_meta.query` returns at least one `review` row for the subject with `review_kind = gate` whose review file has `parse_ok`; a subject with only `refinement` rows gets a reason string that names the refinement-only state and says a gate review (`/spec-review`) is required. The callers `specs._review_attestation_refusal`, the positional `aw set` path in `status_set.validate_transition_allowed`, `check_engine.check_spec_review_attestation` and the runner's spec-review disposition gate `runner_shared.reconcile_disposition` are unchanged and inherit the rule. The runner caller passes the LANE worktree as `repo_root` and judges review files that are still uncommitted there, so the query must build the cache for the `repo_root` it is given (that worktree's state root) and the freshness check must see working-tree bytes; `tests/test_spec_review_dispatch.py` proves it. This is the deliberate behavior change that 4.4 SR-601 assigns to this consumer.
  - Depends on: E-08
  - Expected outcome: one predicate, four callers, stricter for refinement-only subjects, identical for every subject with a gate record; `tests/test_spec_review_dispatch.py` passes unchanged.
  - Execution state: pending

- [ ] E-13 Add `tests/test_spec_review_gate_kind.py` (core) for AC-14a (4): a spec at `to-review` whose only review record is a `specflow` refinement record (`Verdict: REVIEWED - MATERIAL CHANGES APPLIED`) is refused `->reviewed` by `aw specs set <spec> --status reviewed` and by `aw set reviewed <id6>`, each exit nonzero with the file byte-identical; a spec forced to `reviewed` by hand with that record makes `aw check specs --agent` report `check.spec-review-unattested`; adding one gate record (`Verdict: APPROVE WITH REVISIONS APPLIED`) makes both spellings succeed and the check clean.
  - Depends on: E-12
  - Expected outcome: the module passes; `tests/test_spec_review_attestation.py` (including `GrandfatheringAndCheckerTests::test_every_real_spec_in_this_repository_still_conforms`) passes unchanged.
  - Execution state: pending

### Task group 5: parity, gates and commit

- [ ] E-14 Add the AC-1a setter case to `tests/test_status_set_meta_writer.py`: the same `aw set approved <plan> --yes` in four copies of one fixture repository with a cold cache, a warm cache, a deleted `.aw/state/index.db` and an `index.db` overwritten with random bytes produces byte-identical plan files and identical stdout.
  - Depends on: E-08
  - Expected outcome: four identical results.
  - Execution state: pending

- [ ] E-15 Re-run the baseline modules and every new module, the bare core gate `python3 -m pytest`, `aw check --agent` diffed by `(location, rule)` against `.aw/state/2xwb9b/check-before.jsonl`, `aw ipd lint` on this plan, and `aw sanitize --agent`; commit through `aw commit 2xwb9b -- <each changed path>`. Never push.
  - Depends on: E-09, E-11, E-13, E-14
  - Expected outcome: every run passes with equal or higher per-module pass counts than E-01; no new `aw check` error or warning; one path-scoped commit.
  - Execution state: pending

## Project conventions discovered (Step 0)

- The setter engine: `status_set.run_set_command` is the single dispatch (spec `wy9aru`); `backlog.run_set` and `specs.run_set` are thin adapters that call it with `scoped_type`, and `status_set._write_item_dependencies` (the `aw ipd dependencies set|remove` writer) drives a same-status `run_set_command` call, so moving `_prepare_status_change`/`apply_status_change` moves all of them.
- `status_set._prepare_status_change` computes in memory; `apply_status_change` writes. `run_set_command` validates every member of a batch with `_prepare_status_change(..., quiet=True)` before writing any (the batch byte-identity rule of `tests/test_status_set_partial_batch.py`).
- Atomic text write: `artifact_core.atomic_write(path, text)`; staged move: `artifact_core.git_mv(repo_root, src_rel, dst_rel)`; destination directory: `record_placement.resolve_transition_path(record_type, path, status, repo_root=...)`; companion git root: `project_context.record_git_root`.
- History-line grammar (parsed by `plan_readiness._HISTORY_RECORD_PARTS_RE`): `- YYYY-MM-DD <tag> (<actor>): <message>`, newest first, day from `artifact_core.utc_history_date`; duplicates judged by `status_set.same_status_message_is_duplicate` through `attention_contract.history_block`.
- Value writers for optional bullets already exist as pure text functions bounded to `selectors.metadata_region`: `releases.set_blocks_release_line`, `set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_from_spec_line`, `set_item_dependencies_line` (anchored after `- Scope-Paths:`), `set_graduated_to_line`; `backlog.set_release_exempt_kind_line`, `set_release_exempt_ref_line`, `set_close_evidence_line`.
- Sidecar: `record_history.append_advisory` reports a failure on stderr and never raises; `status_set.apply_status_change` calls it after the durable write for `specs` and `backlog` only (spec `wy9aru` 4.3).
- Locks: `platform_lock.held(path, blocking=False)` (non-blocking, not re-entrant).
- The `->reviewed` predicate is `review_findings.review_attestation_missing`, called by `specs._review_attestation_refusal`, `status_set.validate_transition_allowed` and `check_engine.check_spec_review_attestation`.
- Interface names come from `tve77h`: `artifact_meta.read`, `history`, `query`, `resolve`, `read_at`, `append(id6, events, *, expect_seq)`, `create`, `validate_new_events`, `replay`, `repair`; the cache lives at `<state root>/index.db`. `ffceq0` proposes `artifact_meta.read_text`; this plan does not need it (OQ-04).
- Core tier: modules set `pytestmark = pytest.mark.core` (`tests/test_status_set.py` does); the bare `python3 -m pytest` runs only core-marked tests (`conftest.py` core selection).

## Findings

Measured 2026-11-02 at `0cbfcc706`. Each row names a behavior that a moved code path has today and the existing test that checks it (3c, section 7). "NEW" means no existing test checks it and E-02 pins it first.

| Id | Moved path and behavior today | Existing test that checks it |
|---|---|---|
| W-01 | `_prepare_status_change`: rewrites the first `- Status:` bullet above the first `## ` | `tests/test_status_set.py::StatusSetTests::test_spec_set_by_filename_and_id6`, `::test_backlog_set_and_directory_move` |
| W-02 | rewrites `status:` inside a leading `---` block, with alias normalization (`intake` to `todo`) | `tests/test_status_set.py::StatusSetTests::test_set_intake_alias_writes_todo_for_report` |
| W-03 | prompt: rewrites the `aw-prompt` comment status through `prompts.update_metadata_status`; a commentless prompt only moves and prints a note | `tests/test_prompts_set_surface.py::...::test_comment_write_with_body_byte_identity`, `::test_commentless_prompt_fallback_relocates_without_comment`, `tests/test_status_set.py::StatusSetTests::test_prompt_set` |
| W-04 | inserts a missing status (bullet after `# `/`- Date:`, or before the closing `---`) | NEW (E-02) |
| W-05 | writes `Gate-Kind`/`Gate-Ref`/`Gate-Summary` after `- Status:` at the gate status; strips them on leaving it | `tests/test_status_set.py::...::test_backlog_leaving_blocked_clears_gate_fields`, `::test_backlog_staying_blocked_retains_gate_fields`, `::test_spec_leaving_deferred_still_clears_gate`, `::test_plan_transition_is_unaffected_by_gate_clearing`, `tests/test_gate_pair_validation_parity.py::...::test_surface_1_specs_set_flag_deferred`; insertion position NEW (E-02) |
| W-06 | `--blocks-release` write and clear | `tests/test_status_set.py::...::test_plans_set_writes_and_clears_blocks_release`, `::test_backlog_positional_status_persists_blocks_release_61qk4a` |
| W-07 | `--release-exempt-kind`/`--release-exempt-ref` | `tests/test_backlog.py::...::test_release_exempt_setter_roundtrip_and_parity` |
| W-08 | `--from-backlog`: refuses an unknown id, writes the field, inherits the item's gate (`inherit_from_backlog_release_gate`) | `tests/test_releases_line_writers.py::test_cli_ipd_set_refuse_unresolvable_backlog_id`, `tests/test_specs_from_backlog.py::...::test_status_spelling_from_backlog_writes_field_and_inherits_gate` |
| W-09 | `--from-spec` write; refuses an unknown spec id | write: `tests/test_check_engine_from_spec_missing.py::...::test_cli_set_from_spec_writes_bullet`; refusal NEW (E-02; `rg "unresolvable spec id" tests` finds nothing) |
| W-10 | `--item-dependencies` (and `aw ipd dependencies set|remove`) | `tests/test_status_set_descriptive_safety.py::...::test_in_repo_callers_and_deps_wrapper`, `tests/test_work_begin_plan_path_outside_root.py::...::test_plan_path_in_root_tracked_records` |
| W-11 | `--priority`, `--work-kind` | `tests/test_set_dispatch_parity.py::...::test_backlog_priority_and_work_kind_writes_agreement` |
| W-12 | `--graduated-to` | `tests/test_set_dispatch_parity.py::...::test_backlog_graduated_to_canonicalization_agreement` |
| W-13 | backlog default gate (`backlog.decide_gate_default`) with its notice | `tests/test_backlog_gate_follows_status.py::...::test_route_a_reclassification_chore_to_bug_status_spelling` |
| W-14 | backlog `- Kind:` to `- Work-Kind:` canonicalization | dual-line case `tests/test_backlog.py::...::test_duplicate_work_kind_deduped`; single-line case NEW (E-02) |
| W-15 | `- Close-Evidence:` on a SATISFIED close | `tests/test_backlog_handoff_close.py::...::test_case_6_satisfied_evidence_allowed` |
| W-16 | plan `- Approval:` written on entering `approved` (human or "recorded via aw ipd set" form), stripped on leaving it, never on `auto-approved` | `tests/test_status_set.py::...::test_set_approved_inserts_approval_field`, `::test_approval_field_stripped_when_leaving_approved`, `::test_auto_approved_does_not_get_approval_field`, `::test_custom_message_and_by_human_attestation`; position after `- Id:` NEW (E-02) |
| W-17 | `- Readiness:` stripped on a backward move to `draft`/`to-review`, with the APPROVAL WITHDRAWN message | `tests/test_orchestrator_status_gate.py::...::test_e05_backward_pairs_message_requirement_and_approval_withdrawn` |
| W-18 | newest-first history line, tags (`same-status`, target, untooled), duplicate suppression | `tests/test_status_set.py::...::test_same_status_message_recording_and_deduplication`, `::test_untooled_true_same_status_writes_same_status_token`, `::test_untooled_idempotent_rerun_records_exactly_once`, `tests/test_backlog_history_dedup_parity.py::...::test_a_same_status_identical_message_twice_deduplicates_both_spellings`, `tests/test_history_block_bounding.py::HistoryBlockBoundingTests::test_a_well_formed_multi_record_block`; heading creation NEW (E-02) |
| W-19 | actor-label suffixes for `--by-human`, `--allow-open-questions`, `--allow-terminal-reopen`, the release sentinel override | `tests/test_status_set.py::...::test_custom_message_and_by_human_attestation`, `::test_blocking_open_question_refuses_then_the_override_permits_and_is_recorded`, `::test_the_override_performs_it_and_records_itself_in_the_history`, `tests/test_release_sentinel_succession.py::...::test_override_flag_permits_write_records_history_refuses_empty` |
| W-20 | specs `--date` override of the history day | `tests/test_specs_set_adapter.py::...::test_date_override_passthrough_on_specs` |
| W-21 | spec conformance judged on the rendered text before any write | `tests/test_specs_set_adapter.py::...::test_validate_spec_refusal_leaves_file_byte_identical` |
| W-22 | disposition move by `git mv`, companion git root | `tests/test_specs_status_dirs.py::...::test_status_set_run_set_command_relocates_spec`, `tests/test_status_set.py::...::test_set_plan_status_from_executed_to_pending_moves_file_back`, `tests/test_companion_record_owner_root.py::test_companion_record_move_stays_staged_in_companion_git` |
| W-23 | sidecar record for specs/backlog only after the durable write | `tests/test_history_write_order.py::...::test_backlog_set_failed_write_leaves_no_sidecar_and_artifact_unchanged`, `::test_backlog_set_successful_write_records_sidecar_event`, `tests/test_set_dispatch_parity.py::...::test_specs_case_c_f06_sidecar_written_from_unrelated_cwd`, `tests/test_history_date_clock_sidecar.py::...::test_backlog_set_inline_and_sidecar_agree_on_utc_under_skew_zones` |
| W-24 | a no-op writes nothing | `tests/test_status_set.py::...::test_status_set_unchanged_idempotent_no_rewrite` |
| W-25 | dry run writes nothing | `tests/test_status_set.py::...::test_dry_run_mode`, `::test_flagless_dry_run_previews_without_writing`, `tests/test_prompts_set_surface.py::...::test_dry_run_byte_identity` |
| W-26 | a batch with a refused member writes no member | `tests/test_status_set_partial_batch.py::...::test_case_01_non_interactive_without_flag_refuses_byte_compare` |
| W-27 | citation rewrite after a move | `tests/test_status_set.py::...::test_g_setter_spellings_rewrite_citing_pending_plan_and_skip_receipt_plan` |
| W-28 | orchestrator retirement history line (`run_set_command`, raw `write_text`) | `tests/test_orchestrator_child_retired.py::...::test_retirement_appends_orchestrator_history_and_commits_both` |
| R-01 | `read_artifact_record`: id6, status, Set from the metadata region; YAML fallback | `tests/test_status_set_metadata_region.py::test_read_artifact_record_bullet_frontmatter_all_fields`, `::test_read_artifact_record_yaml_fence_declared_or_nothing`, `tests/test_check_engine_metadata_region.py::test_build_dependency_index_single_owner_on_quoted_id` |
| R-02 | `inventory_all_artifacts` (also used by `check_engine` line `_ss.inventory_all_artifacts`) | `tests/test_selector_resolver_matrix.py` (core), `tests/test_blocks_release_reader_bounding.py` |
| R-03 | `_format_status_transition_line`: priority, gate and Blocks-Release in the result line | `tests/test_blocks_release_reader_bounding.py::...::test_bidirectional_display_divergence` |
| R-04 | `plan_priority_work_kind_problems` backstop at `approved` | `tests/test_status_set.py::...::test_terminal_reopen_and_priority_backstop_multiline_output` |
| R-05 | `read_item_dependencies_value` (remove path) | `tests/test_status_set_descriptive_safety.py::...::test_in_repo_callers_and_deps_wrapper` |

Further measurements:

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -n "re\.(compile|match|search|finditer|split)" agent_workflows/status_set.py` gives 20 lines, all metadata patterns | Every one is replaced or deleted by E-08, E-09, E-10, E-11. |
| F-02 | `status_set.read_artifact_record` is called from `run_selection_policy` (2), `runner_shared` (2), `ipd_lifecycle` (3); `inventory_all_artifacts` from `check_engine` (1) | E-10 changes what these callers receive only if parity breaks; the before/after inventory dump (E-01, E-10) proves it does not. |
| F-03 | Records with no `id6` in name or metadata: 14 legacy specs (13 `implemented`, 1 `superseded`) plus `plans/STATUS.md` | The writer must accept a path-keyed target until the cutover mints ids (5.2 step 3; OQ-03). |
| F-04 | 62 tracked plans carry `- Approval:`, all `executed` (finalize, not `status_set`, moves `approved` to `executed`, so the strip never ran) | The "unset approval when leaving approved" rule for finalize belongs to Order 07; the existing 62 values are migration input (Order 04). |
| F-05 | `.aw/records/specs/reviewed/` holds 0 specs; all 24 `specflow` refinement records name subject `18hh1u`, which is `draft` | The SR-601 change (E-12) refuses nothing in this repository today. |
| F-06 | 119 tracked history lines carry `--by-human` in the actor; 0 carry an `--allow-*` suffix | The actor label must keep the suffix forms byte-for-byte (OQ-02). |
| F-07 | `status_set.apply_status_change` moves BEFORE it writes; with a read-only destination the move fails and the source stays unchanged (`tests/test_history_write_order.py`) | The legacy branch keeps this order (E-05); the spec 4.3 order (log, mirror, move) applies to the log branch only. |
| F-08 | 5 tracked tool-written history lines contain a `/home/`, `/Users/`, `/mnt/` or `/tmp/` substring (4 `aw backlog` creation lines, 1 `aw set` line) | The writer's message leak refusal (tve77h E-03, 4.2) now refuses such a message from a setter: a deliberate change required by 4.2, tested in E-06. |

## Proposed changes (ordered, validatable)

1. Pin today's bytes and baseline (E-01, E-02).
2. Legacy-format `append` in `artifact_meta` with preview, freshness, path target, move, sidecar and owned-field rules (E-03 to E-06).
3. `status_set` writes become one `append` per record (E-07 to E-09).
4. `status_set` reads come from the cache; the `->reviewed` rule needs a gate review (E-10 to E-13).
5. Cache parity, gates, commit (E-14, E-15).

## Deferred / out of scope (with reason)

- The HEAD-status read in `_prepare_status_change` (`check_engine._blob_text`, `_status_meta`): a revision reader, moved to `read_at` with the other 4.4 git readers.
  - Carrier: t4gl15
- `specs`, `backlog`, `releases`, `prompts`, `ipd_authoring`, `artifact_rename`, `plans_refs`, `plan_readiness`, `readiness_recheck`, `set_records`, `coverage_record` writers, finalize (including its scope fields and the finalize-side `unset approval`, F-04) and retirement: section 7 step 4 after this engine.
  - Carrier: xexn45
- Folding the `releases.set_*_line` and `backlog.set_*_line` value writers into `artifact_meta` and deleting every legacy parser outside it, with the AC-1 test.
  - Carrier: 9o83cr
- Switching `append` to the log branch, deleting the legacy branch with `LegacyRender` and the path-keyed target, and the final AC-31 (2) "no sidecar" evidence on the real repository.
  - Carrier: cxxmyv
- `aw meta repair` and `aw check meta` over the drift a failed legacy write can leave.
  - Carrier: ffceq0
- `artifact_meta.read_text` for in-memory text readers.
  - Carrier: ffceq0
- Normalizing the 62 executed plans' `- Approval:` values and the multi-word statuses at the cutover.
  - Carrier: dcerjg

## Scope check

- Over-scope: none. `artifact_meta.py` changes only to add the legacy write branch, `WritePreview`, `LegacyRender`, the path-keyed target and the source-digest check (E-03, E-04); `review_findings.py` changes only `review_attestation_missing` (E-12), which 4.4 SR-601 assigns to the plan that moves this setter's attestation read.
- Under-scope: none known. Every write in `status_set.py` (`atomic_write`, `git_mv`, the source unlink, `record_history.append_advisory`, `orch.path.write_text`) and every metadata regex (F-01) has an E-item. Size: 15 E-items in 5 task groups.

## Required tests / validation

New core modules: `tests/test_status_set_meta_writer.py` (E-02, E-14), `tests/test_artifact_meta_legacy_write.py` (E-03 to E-06), `tests/test_spec_review_gate_kind.py` (E-13).

Baseline modules (run at E-01 and E-15, counts compared): `python3 -m pytest -o addopts="" -n auto tests/test_status_set.py tests/test_prompts_set_surface.py tests/test_gate_pair_validation_parity.py tests/test_backlog.py tests/test_releases_line_writers.py tests/test_specs_from_backlog.py tests/test_check_engine_from_spec_missing.py tests/test_status_set_descriptive_safety.py tests/test_work_begin_plan_path_outside_root.py tests/test_set_dispatch_parity.py tests/test_backlog_gate_follows_status.py tests/test_backlog_handoff_close.py tests/test_orchestrator_status_gate.py tests/test_backlog_history_dedup_parity.py tests/test_history_block_bounding.py tests/test_release_sentinel_succession.py tests/test_specs_set_adapter.py tests/test_specs_status_dirs.py tests/test_companion_record_owner_root.py tests/test_history_write_order.py tests/test_history_date_clock_sidecar.py tests/test_status_set_partial_batch.py tests/test_orchestrator_child_retired.py tests/test_status_set_metadata_region.py tests/test_check_engine_metadata_region.py tests/test_selector_resolver_matrix.py tests/test_blocks_release_reader_bounding.py tests/test_spec_review_attestation.py tests/test_spec_review_dispatch.py tests/test_artifact_meta_write.py`.

Gate at merge (C10a, AC-1b per-merge line): the bare `python3 -m pytest` core tier summary line.

Acceptance criteria of `4sd62s` that this plan OWNS:

| AC | Proven by | Note |
|---|---|---|
| AC-15 | E-06, E-07, E-08 | All five cases at `artifact_meta.append` in the legacy branch, plus the setter producing the owned `set`/`unset approval` and `unset readiness` in one append (W-16, W-17 tests). The log-branch form runs in `tve77h`'s replay tests; Order 13 re-demonstrates on the real repository. |
| AC-14a (1)-(3) | E-06 | Writer refusals and `seq`-ordered refinement rounds. |
| AC-14a (4) | E-12, E-13 | Both setter spellings and `check.spec-review-unattested`; with a migrated gate event re-demonstrated by Order 13. |
| AC-31 (phase-B form) | E-05, E-08 | The only sidecar writer for setter appends is `artifact_meta`'s legacy branch: a spec and a backlog setter each write one record, a plan setter and a refused or dry-run write none, and `status_set.py` no longer references `record_history`. Cases (1) and (2) in their final form (rename events; no sidecar file) are Order 13 on the real repository, after Order 07 moves `aw rename`/`aw group`. |

CONTRIBUTES to (owned elsewhere): AC-1a (the setter case with cold, warm, deleted and corrupt caches, E-14; Orders 08/09); AC-1 (no metadata regex left in `status_set`, E-11; Order 11); AC-5 (legacy-branch failure before the content write leaves files unchanged, E-05; `tve77h`); AC-6 (one append per status change; Order 07 phase-B form, Order 13 final); AC-24 (2) (message and actor leak refusal reached through the setter, E-06; `tve77h`).

## Spec / documentation sync

No spec change; implements `4sd62s` 4.3 (writes, phase-B legacy loader counterpart), 4.4 (the `approval` and `readiness` attestation rules; SR-601 for the `->reviewed` predicate), 4.8 (the engine change happens once) and section 7 step 4 (first writer). The phase-B-only arguments (`LegacyRender`, the path-keyed target) are internal to `artifact_meta` and removed at the cutover; `WritePreview` stays because a setter must judge its rendered result before writing (C6). No user-facing document changes: command behavior and output are unchanged except the two deliberate changes (F-08 message leak refusal, E-12 gate-only attestation), which Order 12 documents with the cutover.

## Open questions

### OQ-01: Does this plan fit one green merge?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. 15 E-items in 5 groups; the move is all-or-nothing inside `apply_status_change`, so splitting the writer move from the reader move would leave one merge in which the engine writes through `artifact_meta` but still parses its own metadata, which is legal under C10a but adds a merge for no checkpoint value. If review wants a split, the seam is Task group 4 (E-10 to E-13) as its own child depending on this one. Recommendation strength: medium.

### OQ-02: Where do the history-only flags go after the cutover?

- Blocking: no
- Status: resolved
- Owner: maintainer
- Resolution or deferral rationale: Today the actor label carries `--by-human` (119 lines, F-06), `--allow-open-questions`, `--allow-terminal-reopen` and `--allow-unresolvable-release-sentinel`, and specs `--date` sets the history day. In phase B `LegacyRender` reproduces them byte-for-byte, so nothing changes here. The event schema (4.2) has `by_human` but no key for the three overrides, and `at` is always the write time, so `--date` has no event home. Recommendation: record each override as a message suffix `(override: --allow-terminal-reopen)` and drop `--date` from the log (keeping it as a display-only argument), decided before Order 13 writes its first log. Recommendation strength: medium. Carrier: cxxmyv. RESOLVED 2026-11-02 by the user via /askme (recorded in plan `cxxmyv` OQ-01 and spec `4sd62s` 4.2): events carry a structured `overrides` list; `aw specs set --date` is refused once `metadata_schema` is 2. No reason was given.

### OQ-03: How are the 14 id-less legacy specs written in phase B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Through the handle that `artifact_meta.resolve(path)` returns, keyed by path when the record has no `id6` (F-03); today `aw set` targets them by path, and C10a forbids losing that. If `tve77h` lands without a path-keyed handle, E-04 adds it inside `artifact_meta.py` (declared in Scope). The cutover mints an `id6` for each (5.2 step 3), after which the path key is deleted with the legacy branch. Recommendation strength: strong.

### OQ-04: Does this plan need `artifact_meta.read_text` (proposed by `ffceq0`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Every `status_set` record is on disk, so its metadata comes from `resolve`/`read`; the two places that judge in-memory text (`specs.validate_spec` and `check_engine.evaluate_blocking_close(item_text=...)`) judge the RENDERED result, which `append(..., dry_run=True)` returns as `WritePreview.text`, and they read body content, not metadata through a second grammar. So this plan runs before Order 08 without that function. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the summary line of the "Baseline modules" command (Required tests) run BEFORE any edit, with its per-module pass counts from `-o addopts="" -q -rA | grep -c PASSED` per module, `wc -l .aw/state/2xwb9b/inventory-before.json` plus its first 3 lines, and `ls -l .aw/state/2xwb9b/check-before.jsonl`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_status_set_meta_writer.py` run on the UNCHANGED `status_set.py` (`git diff --stat agent_workflows/status_set.py` empty, pasted) with every one of the seven named cases PASSED, and quote the expected-bytes literal of the `- Kind: chore` case.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy_write.py -k render` with every selected test PASSED, covering each of W-01 to W-18 by name (one test id per row), the `git diff` hunk adding the `legacy` branch of `append` and `_storage_format`, the test showing a target with a log takes the log branch and one without takes the legacy branch, and the `tests/test_artifact_meta_write.py` summary line with the E-01 pass count.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy_write.py -k "preview or fresh or pathkey"` with every selected test PASSED, including the assertion that the dry-run `WritePreview.text` equals the bytes a real write leaves, the refusal text for an out-of-band edit naming the file, and a write to an id-less spec fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy_write.py -k "move or sidecar or order"` with every selected test PASSED, plus `python3 -m pytest -o addopts="" tests/test_history_write_order.py tests/test_companion_record_owner_root.py tests/test_specs_status_dirs.py` summary line with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy_write.py -k "owned or review_kind or refinement"` with every selected test PASSED: one test id for each of AC-15 cases (1) to (5) and AC-14a cases (1) to (3), each refusal test asserting the file bytes are unchanged, plus the printed refusal reason for a `set readiness` and for a message containing `<home>/a.md (an absolute home-directory path)`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the `git diff` hunk of `_prepare_status_change` showing the event list and `LegacyRender` replacing the line edits, and the summary line of `python3 -m pytest -o addopts="" tests/test_status_set.py tests/test_status_set_partial_batch.py tests/test_specs_set_adapter.py tests/test_backlog_handoff_close.py` with 0 failed and pass counts equal to E-01.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `rg -n "atomic_write|git_mv|write_text|record_history" agent_workflows/status_set.py` (no output) and the summary line of the full "Baseline modules" command with 0 failed and per-module pass counts equal to E-01.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_orchestrator_child_retired.py` with `test_retirement_appends_orchestrator_history_and_commits_both` PASSED and `rg -n "_prepend_workflow_history_entry|_HISTORY_HDR_RE" agent_workflows/status_set.py` (no output).
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `diff .aw/state/2xwb9b/inventory-before.json .aw/state/2xwb9b/inventory-after.json` (no output) and the summary line of `python3 -m pytest -o addopts="" tests/test_status_set_metadata_region.py tests/test_selector_resolver_matrix.py tests/test_check_engine_metadata_region.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the output of `rg -n "re\.(compile|match|search|finditer|split)" agent_workflows/status_set.py` (no line names a metadata field) and the summary line of `python3 -m pytest -o addopts="" tests/test_blocks_release_reader_bounding.py tests/test_status_set.py -k "priority or bidirectional or deps" tests/test_status_set_descriptive_safety.py` with 0 failed.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the `git diff` hunk of `review_findings.review_attestation_missing` and the summary line of `python3 -m pytest -o addopts="" tests/test_spec_review_attestation.py tests/test_spec_review_dispatch.py` with 0 failed and pass counts equal to E-01.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_spec_review_gate_kind.py` with every test PASSED, quoting the refusal text of both setter spellings and the `check.spec-review-unattested` record from `aw check specs --agent` on the fixture.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_status_set_meta_writer.py -k cache` with the four cache-state cases PASSED, each asserting byte-identical plan files and identical stdout.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste: the "Baseline modules" summary line with per-module counts against E-01; the summary line of the three new modules; the bare `python3 -m pytest` core-tier summary line with its wall time (AC-1b per-merge line); the `(location, rule)` diff of `aw check --agent` against `.aw/state/2xwb9b/check-before.jsonl` (no new error or warning; each other difference named with its cause); `aw ipd lint` on this plan (`conforming`); the `aw sanitize --agent` result record; and the `aw commit 2xwb9b` output listing the committed paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` and `7ehv8l` are executed. All open questions are resolved. Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). The on-disk format must stay the bullet format (C10a): E-01/E-02 baselines and the inventory dump diff are the proof. Commit only through `aw commit 2xwb9b -- <paths>`; never `git add -A`, a bare `git add`, or `git commit -a`, and never push. Run the bare `python3 -m pytest` core gate, the baseline modules and the three new modules, and paste the ACTUAL summary lines; never claim a result you did not run. Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 2xwb9b` itself.
