# IPD: Move the remaining metadata writers onto artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 7 step 4 requires every metadata WRITER to change to write through `artifact_meta` in phase B, while `artifact_meta` still writes today's bullets and history lines, so that the cutover (Order 13) switches one writer and not dozens (C1, C10a). Order 06 (`2xwb9b`) moves the `status_set` engine. Every other writer still edits metadata text by hand. Measured 2026-11-02 at `0cbfcc706`: 12 writer modules in this plan's scope hold 99 hand-formatted `- Field: value` literals and 47 `## Workflow history` references (`specs` 14/8, `backlog` 29/18, `releases` 11/4, `ipd_authoring` 11/1, `artifact_rename` 11/0, `plans_refs` 4/0, `plan_readiness` 1/10, `coverage_record` 3/5, `set_records` 1/1, `review_sequence` 3/1, `runner_shared` writer helpers, `ipd_lifecycle` finalize), plus `prompts` comment writers. These modules use four different history-insertion rules (F-04), and three of them write the gitignored rename ledger (`record_history.record_rename`). Finalize writes `- Scope-Exceeded:` through `ipd_lifecycle._insert_scope_exceeded_metadata` (41 tracked plans carry it), which 4.2c and 4.4 replace with `scope_result`, `out_of_scope_paths` and `widened_paths` written in the executed append. No creating command can write `short_description` yet (AC-36 case 1). Section 7 and 3c require each phase-B plan to name each moved writer's behavior and the test that checks it, because a behavior that no test exercises can change unnoticed.
- Scope: Phase B step 4, part 2 of 2 (`4sd62s` section 7). Add ONE phase-B legacy writer inside `artifact_meta` (`write_legacy`) that renders a validated batch of events as bullet-block, `aw-prompt`-comment and history-line edits. Then move these writers onto `artifact_meta.create`, `artifact_meta.append` and `write_legacy`, each pinned first by its existing tests: `specs` (`run_new`, `run_note`, `run_migrate`), `backlog` (`run_new`, `run_note`, `_reattach_history`), `releases` (`create_release`, `plan_release`, `set_item_dependencies_line`, `set_graduated_to_line`), `prompts` (`run_new`, `render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`), `ipd_authoring` (`run_scaffold`, `run_sync` watermark), `artifact_rename` (`_update_frontmatter_metadata`, `_update_or_inject_set_metadata`, rename and group ledger), `plans_refs` (`_set_metadata`, `apply_renames`), `research_refs` and `research_cmd` and `research_archive` and `plans_archive` path and field writes, `artifact_adopt.apply_adoption`, `plan_readiness.recheck_readiness` with `readiness_recheck`, `set_records` (`write_walkthrough`, `close_on_answer`, `promote_question_to_backlog`), `coverage_record.write`, finalize scope fields (`ipd_lifecycle._finalize_transaction`, `_insert_scope_exceeded_metadata`), retirement (`ipd_lifecycle.retire_orchestrator` and `status_set`'s child-retirement history on the orchestrator), and the runner writer helpers (`runner_shared.rederive_front_matter`, `mark_plan_attended`, `record_oq_answer`, `perform_coordinator_proposal_file`, `review_sequence.restore_pre_s7_plan`). Add `--summary` to `aw ipd scaffold` and `aw prompts new` and an `aw describe <id6>` short-description setter (AC-36 case 1). EXCLUDES: the `status_set` engine itself (`2xwb9b`); readers (`ffceq0`, `t4gl15`); deleting old parsers (`9o83cr`); the log format, `rename` and path events and sidecar retirement, which start at the cutover (`cxxmyv`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/specs.py, agent_workflows/backlog.py, agent_workflows/releases.py, agent_workflows/prompts.py, agent_workflows/ipd_authoring.py, agent_workflows/artifact_rename.py, agent_workflows/plans_refs.py, agent_workflows/research_refs.py, agent_workflows/research_cmd.py, agent_workflows/research_archive.py, agent_workflows/plans_archive.py, agent_workflows/artifact_adopt.py, agent_workflows/plan_readiness.py, agent_workflows/readiness_recheck.py, agent_workflows/set_records.py, agent_workflows/coverage_record.py, agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/runner_shared.py, agent_workflows/review_sequence.py, agent_workflows/cli.py, agent_workflows/command_surface.py, docs/cli-output-contract.md, CHANGELOG.md, tests/test_artifact_meta_legacy_writer.py, tests/test_writers_create_summary.py, tests/test_writers_scope_fields.py, tests/test_writers_merge_independence.py, tests/test_writers_obligations.py, tests/test_artifact_meta_registry.py, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, .aw/records/plans/pending/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.ipd.md
- Item-Dependencies: executed:tve77h, executed:2xwb9b
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 7
- Highest E allocated: 14
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: xexn45
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-008 FIXED; review record .aw/records/reviews/20261102-metastore-07-xexn45-move-the-remaining-metadata-writers-onto-artifact-meta.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every metadata write outside the `status_set` engine goes through `artifact_meta`, which validates it with the Order 02 rules and renders it, in phase B, into today's bullets and history lines through one legacy writer. Each moved writer keeps a named, tested behavior, so the cutover changes one renderer instead of 30 hand-written text edits.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN-FIRST RULE for every "move" item: run the named existing test modules GREEN on the unmodified code and save the per-test outcome list under the gitignored `.aw/state/xexn45/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/xexn45/<E>-before.txt`; `-m ""` includes `slow` modules, `-p no:randomly -n 0` makes the list deterministic, and `-q` is not repeated because `addopts` is cleared); make the move; run the same command into `-after.txt`; `diff` of the two must print nothing, so a test that newly fails, errors or skips is caught, not only a lost PASSED line. An existing assertion may change only when the Behavior decisions D-1 to D-6 below name it. New tests set `pytestmark = pytest.mark.core`, build fixtures in `tmp_path`, drive the real CLI or function, and never read production source (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").

### Task group 1: the phase-B legacy writer

- [ ] E-01 Before any edit, save `aw check --agent` output to `.aw/state/xexn45/check-before.jsonl` and the bare `python3 -m pytest` summary line to `.aw/state/xexn45/core-before.txt`. Add `artifact_meta.write_legacy(path, events, *, record_type, dry_run=False)` and route the phase-B branch of `artifact_meta.create` and `artifact_meta.append` through it. `2xwb9b` E-03 to E-05 already built the legacy branch of `append` (its renderer, `LegacyRender`, `WritePreview`, the `_storage_format` per-target dispatch, the path-keyed target and the move-then-write order); `write_legacy` EXTRACTS that renderer into the one named function and extends it to `create`, the `aw-prompt` comment forms and the event types this plan adds, so there is still exactly ONE legacy renderer. It must not be a second implementation beside `2xwb9b`'s, and `tests/test_artifact_meta_legacy_write.py` and `tests/test_status_set_meta_writer.py` (both `2xwb9b`) must pass unchanged after the extraction. It takes events already accepted by `validate_new_events` and the replay rules (tve77h E-03, E-06), and renders them into the file: `set` and `unset` edit the bullet in the metadata block before the first `##` (in place when present; a new bullet goes after `- Status:`, else after `- Id:`, else at the end of the block, never into the body: the a88210 rule of `artifact_rename._update_frontmatter_metadata`); a prompt edits keys INSIDE its single `aw-prompt` comment and never adds a bullet (`prompts.inject_metadata_id6` rule, ubac5n); `note`, `transition`, `review` and `coverage` events with a `message` PREPEND one `- <YYYY-MM-DD> <label> (<tool>): <message>` line directly under `## Workflow history`, keeping the blank line under the heading exactly when one was there (D-1), and create the section before the first `##` after the metadata when absent; field names map back from registry names to legacy names (`plan_role` -> `Kind`, `work_kind` -> `Work-Kind`); `item_dependencies` renders through its `raw` declarations. It writes with `artifact_core.atomic_write`, holds `platform_lock.held(<state>/locks/meta-<key>.lock)` (the `2xwb9b` key, so an id-less legacy record locks by path) like the log path, keeps `2xwb9b`'s source-digest freshness check, and on refusal or `dry_run` writes nothing. Test module `tests/test_artifact_meta_legacy_writer.py`, including a round trip: for 40 tracked records copied to `tmp_path` (8 each of plans, specs, backlog items, releases and prompts, chosen by sorted path; when a type has fewer than 8 tracked records, all of them, and the count is reported), a `set` of an existing field to its own value, then `read()`, returns the same State and leaves the file byte-identical.
  - Depends on: none
  - Expected outcome: `write_legacy` edits exactly the bullet, comment key or history line an event names; a refused event (for example `set readiness`) changes no byte; the 40-record round trip is byte-identical; `2xwb9b`'s two test modules pass unchanged.
  - Execution state: pending

### Task group 2: creating commands and the short-description setter

- [ ] E-02 Move the creating commands onto `artifact_meta.create`, pinned first: `specs.run_new`, `backlog.run_new`, `releases.create_release`/`plan_release`, `prompts.run_new` with `render_metadata_comment`, `ipd_authoring.run_scaffold`, `research_cmd.run_new`/`run_new_comparison`, `artifact_adopt.apply_adoption` and `set_records.write_walkthrough`. Each passes its fields and its created-history message as events; the body text stays the command's own rendering. Behaviors kept: preview prints the exact bytes `--apply` writes (`tests/test_releases.py::test_plan_release_previews_exactly_what_create_writes`, `tests/test_prompts_new.py::test_dry_run_prints_intended_path_and_writes_nothing`, `tests/test_ipd_authoring.py::test_dry_run_writes_nothing`); conformant output (`tests/test_backlog.py::test_new_creates_conformant_item_that_checks_clean`, `tests/test_spec_id6_filenames.py::test_new_preview_then_apply_conformant`, `tests/test_releases_cli.py::test_apply_creates_a_record_that_check_releases_passes`, `tests/test_ipd_authoring.py::test_apply_writes_conforming_child`); the UTC history date (`tests/test_scaffold_history_clock.py`, `tests/test_history_date_clock.py`); descriptive refusals before any write (`tests/test_specs_releases_descriptive_safety.py`, `tests/test_backlog_descriptive_safety.py`, `tests/test_research_descriptive_safety.py`, `tests/test_descriptive_refusal_hoist.py`); walkthrough id6 and `Target-Id` (`tests/test_walkthrough_id6.py::test_write_walkthrough_mints_own_id6`); adoption safety (`tests/test_artifact_adopt.py::test_fail_severity_leak_refuses_before_any_write`, `test_destination_write_failure_leaves_the_original`); the prompt comment stays the single first line with the body byte-identical (`tests/test_prompts_set_surface.py::test_comment_write_with_body_byte_identity`); and the sidecar is written only after the durable write (`tests/test_history_write_order.py`).
  - Depends on: E-01
  - Expected outcome: every named module passes before and after with equal PASSED sets; `rg -n "Workflow history" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/ipd_authoring.py agent_workflows/set_records.py agent_workflows/research_cmd.py agent_workflows/artifact_adopt.py` shows no remaining text-building of the history section in a create path.
  - Execution state: pending

- [ ] E-03 Write `short_description` at creation (AC-36 case 1): add `--summary` to `aw ipd scaffold` and `aw prompts new` (registered in `cli` and `command_surface`); make every creating command (`aw backlog new --summary`, `aw specs new --summary`, `aw releases new --summary`, `aw research new --summary`, `aw adopt --summary`, `aw ipd scaffold --summary`, `aw prompts new --summary`) write the value as `short_description` in the `create` event when it passes `attention_contract.refuse_unsafe_descriptive` at `MAX_DESCRIPTIVE_LEN` (300); for `aw specs new`, a `--summary` over 300 characters (still accepted up to `MAX_PROSE_DESCRIPTIVE_LEN` today) is written only to the body summary and writes no `short_description` (4.2 SHORT DESCRIPTION). In phase B the legacy writer renders the field as a `- Short-Description:` bullet (a prompt: a `Short-Description:` comment key), registered in `ipd_schema.META_RECOGNIZED` (plans; otherwise `IPD-M103`). The other types have no unknown-bullet check today (`specs.validate_spec`, `backlog._render_item`, `releases.validate_release`; research validates only its required YAML keys in `research_contract.FRONTMATTER_FIELDS`), so for them the gate is a test: each `tests/test_writers_create_summary.py` case runs `aw check all --agent` on its fixture and asserts no diagnostic names the new field. Research writes the value as a `short-description:` YAML key, not a bullet (see OQ-02). Test module `tests/test_writers_create_summary.py`.
  - Depends on: E-02
  - Expected outcome: for each of the seven commands, `--summary "Adds a widget."` then `artifact_meta.read(<id6>).fields["short_description"] == "Adds a widget."`; a 301-character value, a newline value and a control-character value each exit nonzero with no file written; a 400-character `aw specs new --summary` writes the body summary and no `short_description`.
  - Execution state: pending

- [ ] E-04 Add the short-description setter `aw describe <id6> --summary <text> [--apply]` and `aw describe <id6> --clear [--apply]` (preview by default), registered in `cli`, `command_surface` and `docs/cli-output-contract.md`. It appends one `set` (or `unset`) of `short_description` through `artifact_meta.append` with no status change and is accepted on a terminal record (OQ-30: a terminal log accepts a `set` or `unset` of `short_description`). It resolves the selector through `selectors.resolve` and refuses zero or several matches with exit 2 (the `zyj8io` convention). Test module `tests/test_writers_create_summary.py`.
  - Depends on: E-03
  - Expected outcome: `aw describe <id6> --summary X` previews and writes nothing; `--apply` writes the field and one history line; the same call on an executed plan succeeds; `--clear --apply` removes it; an unknown id6 exits 2.
  - Execution state: pending

### Task group 3: notes, field setters and renames

- [ ] E-05 Move the note and field-setter writers onto `artifact_meta.append`, pinned first: `specs.run_note`, `specs.run_migrate`, `backlog.run_note`, `backlog._reattach_history` (used by `set_records.close_on_answer`), `releases.set_item_dependencies_line` and `set_graduated_to_line` (called by the `status_set` engine; Order 06 keeps the call site), `research_cmd.run_set_outcome`/`run_set_priority`, `ipd_authoring.run_sync` (the `Highest E allocated` watermark set), and `set_records.close_on_answer`/`promote_question_to_backlog`. Behaviors kept: one record per note, identical note deduplicated (`tests/test_specs_verbs.py::test_note_appends_one_record_only`, `test_note_deduplicates_identical_call`; `tests/test_backlog.py::test_note_records_history_without_changing_status_or_moving_the_file`, `test_a_second_note_preserves_the_first`); migrate folds prose into one history record (`tests/test_specs_verbs.py::test_migrate_free_form_to_bare_enum`, `test_migrate_to_deferred_with_gate`, `test_migrate_folds_implemented_line`); unknown backlog bullets kept in order (`tests/test_backlog.py::test_close_on_answer_preserves_custom_field_and_handed_off_blocks_release`, `test_backlog_set_metadata_preservation_both_spellings_agree`); watermark (`tests/test_ipd_authoring.py::test_sync_assigns_from_watermark_and_advances`, `test_sync_backfills_missing_id_and_leaves_present_id`); graduation lines (`tests/test_graduation_forward_links.py`); research setters (`tests/test_research_cmd_create.py::test_run_set_outcome_apply_writes`, `tests/test_research_priority.py`); history bounding (`tests/test_history_block_bounding.py::test_e2_writer_round_trip_wrapped_and_quoted`); slug slice (`tests/test_slug_slice_trailing_hyphen.py`).
  - Depends on: E-01
  - Expected outcome: every named module passes before and after with equal PASSED sets; `rg -n "f\"- \{(date|today|hdate)\} " agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/research_cmd.py agent_workflows/set_records.py` shows no hand-built history line outside `artifact_meta`.
  - Execution state: pending

- [ ] E-06 Move the rename, regroup and archive field writers onto `artifact_meta.append` in phase B: `artifact_rename._update_frontmatter_metadata` and `_update_or_inject_set_metadata` (Set, Order, injected Id), `plans_refs._set_metadata`/`apply_renames`, `research_refs.run_mv`/`run_set_assign` front-matter edits, and the status edit in `research_archive.apply_moves`. The file move itself stays `artifact_core.git_mv` and `plans_archive.apply_shard_moves` stays a pure move (phase B writes no `rename` or path event; section 7 "the writers of path-bearing events start at the cutover commit"). The gitignored rename ledger (`record_history.record_rename`) stays unchanged until the cutover (AC-31 is a post-cutover criterion). Behaviors kept: Set/Order/Id edit and the a88210 no-H1 rule (`tests/test_artifact_rename.py`, `tests/test_artifact_group.py`, `tests/test_spec_id6_filenames.py::test_to_id6_preview_then_apply_injects_and_rewrites`, `test_to_id6_idempotent_on_clustered_spec`); prompt id in the comment (`tests/test_artifact_rename.py::test_rename_prompts`); Order preservation and refusals (`tests/test_plans_group_order_preservation.py`, `tests/test_plans_order_grammar.py`); research front matter (`tests/test_research_rename_frontmatter.py`, `tests/test_research_set_assign_date_containment.py`); shelf moves (`tests/test_research_archive.py::test_promote_to_reference_moves_to_weekly_shard_keeps_id`, `tests/test_plans_archive.py::test_move_is_tracked_git_rename`); ledger (`tests/test_rename_ledger.py`); machine output (`tests/test_rename_group_machine_output.py`, `tests/test_mutation_result_facts.py`); citation rewrite (`tests/test_artifact_refs_rewrite.py`).
  - Depends on: E-01
  - Expected outcome: every named module passes before and after with equal PASSED sets; each pre-pass batch refusal (`plans_refs` yqv6b7 E-03: an invalid plan raises before any file is touched) still holds because validation now runs for the whole batch before the first `write_legacy`.
  - Execution state: pending

### Task group 4: attestations, finalize and retirement

- [ ] E-07 Move `plan_readiness.recheck_readiness` (`aw ipd recheck-readiness`) onto `artifact_meta.append` as ONE gate `review` event (4.4, 4.1a K2): `review_kind: gate`, `readiness: go-pending-approval` (still pinned to `plan_readiness.RECHECK_TARGET_READINESS`, never caller input), no new verdict: `plan_readiness.newest_verdict` returns a POLARITY and the raw newest review record, not a verdict string, so the event's `verdict` is the verdict token that `plan_readiness.classify_verdict` reads from that raw record (a member of `plan_readiness.VERDICTS`, as K2 requires of a `gate` event), and when no token can be read the recheck refuses exactly as it does today, so `aw ipd recheck-readiness` never mints a verdict, and `message` = the existing `plan_readiness.format_recheck_history_entry` text. The legacy writer renders it as today: the `- Readiness:` line replaced and one `readiness re-check` history line prepended. `readiness_recheck._run_stale_findings` and its call to `review_findings.append_round_resolving_stale` stay text edits of the REVIEW FILE body (N3), not metadata. Behaviors kept: `tests/test_plan_readiness_recheck.py` (40 tests, including `test_the_only_permitted_write_is_no_go_to_go_pending_approval`, `test_apply_writes_exactly_the_readiness_line_and_one_history_record`, `test_the_recheck_CLEARS_once_the_stale_finding_is_closed`), `tests/test_review_record_classifier.py`, `tests/test_read_verb_zero_match_refusal.py`.
  - Depends on: E-01
  - Expected outcome: the named modules pass before and after with equal PASSED sets; an extra test in `tests/test_writers_obligations.py` shows that a hand-built `set readiness=go` through `artifact_meta.append` is refused with no byte written, while the recheck path writes `go-pending-approval`.
  - Execution state: pending

- [ ] E-08 Move `coverage_record.write` onto `artifact_meta.append` as ONE `op: coverage` event carrying `coverage` and `coverage_fingerprint` (4.4); `coverage_checked` is written only as the legacy bullet that the legacy writer derives from the event's `at` day and `actor.model` (`<YYYY-MM-DD> by <model>`, its migrated-value format), so the post-cutover log never carries it. The `## Coverage findings` body section stays body text written by `coverage_record` (N3). The history line keeps the shape `- <day> coverage <verdict> (<tool>): fingerprint <12>, model <m>`, which `IPD-M112` reads in phase B. Behaviors kept: `tests/test_coverage_record.py` (`test_write_and_read_fail`, `test_write_pass_removes_findings_and_lints_conforming`, `test_checklist_edit_makes_is_current_false`), `tests/test_coverage_not_written.py`, `tests/test_history_date_clock_residual.py::test_coverage_record_write_records_utc_date`, `tests/test_orchestrator_readiness.py`, `tests/test_gradcover_end_to_end.py`.
  - Depends on: E-01
  - Expected outcome: the named modules pass before and after with equal PASSED sets; a `set coverage=pass` outside an `op: coverage` event is refused with no byte written (`tests/test_writers_obligations.py`).
  - Execution state: pending

- [ ] E-09 Move finalize's scope fields onto the executed append (the 4sd62s interim rule, 4.2 op list, 4.2c, 4.4): in `ipd_lifecycle._finalize_transaction`, the transition to `executed` from `status_set.apply_status_change` (Order 06) and, in the SAME `artifact_meta.append` call, a `set` of `scope_result` (`within` when no path was out of scope or widened, `widened` when only widened paths exist, `exceeded` when any out-of-scope path was accepted), `out_of_scope_paths` and `widened_paths` (each a list of `{path, reason}` from `evidence["scope_reconciliation"]`). Paths stay REPOSITORY-relative, the form `Scope-Paths` and `compute_scope_reconciliation` use, because a finalize path is a code path and not a records path (OQ-03). In phase B the legacy writer renders ONLY what today's file shows: the existing `- Scope-Exceeded: <path> (<reason>); ...` bullet with today's sanitizing from `_format_scope_exceeded_value` (sorted, `;()` removed, newlines folded, 200-character cap), and nothing for `within`/`widened` (D-3). `_insert_scope_exceeded_metadata` is deleted in favor of that renderer. In `artifact_meta.validate_new_events`, apply the records-root containment rule to `path` only and the repository-root rule to `out_of_scope_paths` and `widened_paths` (OQ-03), and amend spec `4sd62s` 4.2 to say so. If `tve77h`'s `tests/test_artifact_meta_registry.py` pins records-root containment for those two keys, its assertion changes here under decision D-6. Rollup retirement (`retire_orchestrator`) writes none of the three fields. Behaviors kept: `tests/test_scope_exceeded.py` (cases a to e), `tests/test_finalize_refusal_findings.py`, `tests/test_finalize_sendback.py`, `tests/test_ipd_lifecycle_cli.py::test_widening_finalizes_when_each_added_path_carries_a_reason`. New test module `tests/test_writers_scope_fields.py` asserts through `artifact_meta.read` that `scope_result`, both lists and their reasons are present after a fixture finalize (`exceeded`, `widened`, `within` cases), that a rollup retirement leaves all three absent, that a separate later `set scope_result` is refused, and that an `agent_workflows/...` out-of-scope path is stored while a `../x` path is refused (OQ-03).
  - Depends on: E-01
  - Expected outcome: `tests/test_scope_exceeded.py` passes unchanged; the three new cases report `exceeded`, `widened` and `within` with the expected path lists; rollup leaves them absent; the out-of-append `set` is refused.
  - Execution state: pending

- [ ] E-10 Move the retirement writers onto `artifact_meta.append`: `ipd_lifecycle.retire_orchestrator`'s history record (`rollup_history_message`) becomes the `message` of the transition event that `status_set.apply_status_change` writes (Order 06), with `_insert_rollup_checklist_statement` kept as a BODY edit (it writes into the checklist section, not metadata); `status_set`'s child-retirement history line on the orchestrator (`same-status (<actor>): child <id6> retired <status>`) becomes one `note` event appended to the orchestrator through `artifact_meta.append`; the `RETIRED <date>: <reason>` banner of a hand retirement stays body text that `artifact_audit._has_retired_banner` reads. Behaviors kept: `tests/test_orchestrator_retirement.py` (44 tests, including `test_honest_terminal_record_history_entry_and_actor`, `test_an_eligible_set_retires_and_lands_in_executed`), `tests/test_orchestrator_child_retired.py::test_retirement_appends_orchestrator_history_and_commits_both`, `test_skip_conditions_no_set_dirty_whole_set`, `tests/test_lifecycle_holder_gate.py::test_entry_05_retire_orchestrator_in_process`.
  - Depends on: E-01
  - Expected outcome: the named modules pass before and after with equal PASSED sets.
  - Execution state: pending

### Task group 5: runner writer helpers, obligations and finish

- [ ] E-11 Move the WRITE halves of the runner helpers (carried here by `t4gl15`): `runner_shared.mark_plan_attended` (`attended: required` plus its history line), `rederive_front_matter` (the `REDERIVABLE_FRONT_MATTER_KEYS` = `Work-Kind`, `Priority` set plus the lane's history bullet, applied to TARGET text), `perform_coordinator_proposal_file` (scaffold-then-set `Blocks-Release` on a created plan, and the fallback stub's created line) and `review_sequence.restore_pre_s7_plan` (restore `status` and `readiness` and drop review history lines added since the pre-pass snapshot). The two pure text-to-text helpers gain a `write_legacy` text mode (`artifact_meta.render_legacy_text(text, events)`, the same renderer over a string) because their callers operate on merge-stage or snapshot text that is not a file (OQ-04). `record_oq_answer` edits an open-question BODY block (`- Status:` and the rationale line inside `### OQ-..`), which N3 keeps as body text, so it is recorded as NOT a metadata writer and does not move. Behaviors kept: `tests/test_run_proposal_channel.py::test_needs_attended_proposal_marks_plan_and_files_no_stub`, `test_attended_field_value_is_linted`, `tests/test_records_only_lane_rederive.py` (24 tests, including `test_the_anti_revert_control_holds_on_the_shipped_allow_list`), `tests/test_review_sequence_runner.py::test_ac07_readiness_written_before_s7_reverted_and_reasked`, `tests/test_history_date_clock_residual.py::test_proposal_fallback_record_records_utc_date`, `tests/test_question_preflight.py::test_record_oq_answer_appends_to_existing_rationale`.
  - Depends on: E-01
  - Expected outcome: the named modules pass before and after with equal PASSED sets; `restore_pre_s7_plan` through the renderer emits no `set readiness` event (it restores the pre-pass VALUE as a legacy-text edit only, see D-5).
  - Execution state: pending

- [ ] E-12 Add `tests/test_writers_merge_independence.py` (AC-3, phase-B form): in a real git repository fixture, branch A runs `aw backlog note` and `aw describe` on backlog item X while branch B runs `aw specs note` and `aw ipd recheck-readiness` on a different spec and plan; `git merge` of B into A completes with no conflict, and `artifact_meta.read` on all three records afterwards shows both branches' changes. A second case changes the SAME record on both branches (one history line each) and asserts that `git merge` exits nonzero with that file in `git diff --name-only --diff-filter=U`: measured at review, two branches that each prepend one line directly under `## Workflow history` of the same file conflict, which is the phase-B limit that 4.7 removes at the cutover. The test pins that outcome; it does not accept either result.
  - Depends on: E-02, E-04, E-05, E-07
  - Expected outcome: the different-artifacts merge has exit 0 and no conflict markers; the same-record merge exits nonzero naming the shared file.
  - Execution state: pending

- [ ] E-13 Add `tests/test_writers_obligations.py` for AC-21 (4.4a) and the AC-6 phase-B form: (a) AC-21 rows: run and paste `tests/test_find_filters.py` (`wja06w`), the zero-match `aw find` exit code 2 (`zyj8io`, via `tests/test_cli_find.py`), `tests/test_graduation_forward_links.py` (`pw2ln3`: declarations alone, origin links alone, both), `tests/test_readiness_absence_invariant.py` (`l56tyz`) and the AC-15 tests of Order 06 (`fhinri`); a reference to this plan's commit closes the `63zo2f` row (its `Carrier: 4sd62s` deferral: "the setters change to use `artifact_meta`"); the `me227c` and `6tjye0` rows point at AC-1 (`9o83cr`) and AC-20 (`dcerjg`); (b) AC-6 phase-B form: a fixture `aw backlog set <id6> done` and a fixture finalize each produce a `git diff` whose metadata hunk is exactly the `- Status:` line, any owned unset, the scope bullet and ONE new history line (the phase-B form of "exactly one `transition`"); (c) the attestation refusals named in E-07 and E-08.
  - Depends on: E-07, E-08, E-09, E-12
  - Expected outcome: every listed module passes; the two `git diff` hunks contain exactly the listed lines.
  - Execution state: pending

- [ ] E-14 Finish: run `rg -n "atomic_write\(|write_text\(" agent_workflows/specs.py agent_workflows/backlog.py agent_workflows/releases.py agent_workflows/prompts.py agent_workflows/ipd_authoring.py agent_workflows/artifact_rename.py agent_workflows/plans_refs.py agent_workflows/plan_readiness.py agent_workflows/set_records.py agent_workflows/coverage_record.py` and record in `## Findings` (table F-09) every remaining hit with its reason (body text per N3, a generated index file, or a non-record file); update `docs/cli-output-contract.md` (the `aw describe` leaf and the two new `--summary` options) and add one `CHANGELOG.md` `2.0.0 (pending)` line; run every module named in E-02 to E-13, the bare core gate `python3 -m pytest` (within its 30 s budget), `make test-all`, `aw check --agent` (`(location, rule)` pairs compared with `.aw/state/xexn45/check-before.jsonl`, captured before E-01 by the PIN-FIRST rule's first run; no added pair), `aw ipd lint --all` on this repository (no new diagnostic) and `aw sanitize --agent`; commit through `aw commit xexn45 -- <each changed path>` (one commit per task group is allowed, each through `aw commit`). Never push.
  - Depends on: E-06, E-10, E-11, E-12, E-13
  - Expected outcome: all runs pass; F-09 lists every remaining raw write with a reason; every commit is path-scoped.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `history`, `query`, `resolve`, `read_at`, `append(id6, events, *, expect_seq)`, `create(...)`, `validate_new_events(type, events, *, records_root, migration_import=False)`, `repair`. Order 02's `append`/`create` are log-format and "switched on at the cutover"; this plan adds the phase-B branch (`write_legacy`) that Order 13 removes.
- Atomic replacement is `artifact_core.atomic_write(path, text, *, prefix)`; the lock is `platform_lock.held`; UTC history days come from `artifact_core.utc_history_date` (spec `2vev8j` 4.4).
- Today's history-insertion rules differ (F-04): `status_set._prepend_workflow_history_entry` and `backlog.run_note` insert DIRECTLY under the heading; `specs._append_history` normalizes to exactly one blank line then the record; `plan_readiness._prepend_history_entry` keeps an existing blank line and inserts after it; `coverage_record.write` inserts directly under the heading.
- The newest-history reader is `attention_contract.newest_history_record` over `attention_contract.history_block`, which drops blank lines; so the blank-line difference changes no reader result.
- Descriptive refusals: `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4300; `specs._refuse_unsafe_descriptive(..., prose=True)` is the spec `--summary` path.
- Recognized plan bullets are `ipd_schema.META_RECOGNIZED`; an unrecognized bullet is lint error `IPD-M103` (`ipd_lint.C_META_UNKNOWN`). Backlog keeps unknown bullets in order (`backlog._render_item`, rendrop 2yqt0a).
- The prompt mirror is the single `aw-prompt` comment (`prompts.render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`); nothing visible may precede the prompt body (spec `20260808-1958-01-prompt-purity-lint` R1/P4).
- Finalize scope evidence is `evidence["scope_reconciliation"]` with `reasons` and `widened_paths` (`ipd_lifecycle._finalize_transaction`, `runner_shared.compute_scope_reconciliation`).
- Rollup retirement is `ipd_lifecycle.retire_orchestrator` -> `_finalize_transaction` with `evidence["transition"] == "orchestrator-rollup"`.
- The rename ledger is `record_history.record_rename`, written by `artifact_rename` and `plans_refs`; the sidecar is gitignored (`.aw/.gitignore` `records/history.jsonl`).
- Core tier: `pyproject.toml` marker `core`; modules set `pytestmark = pytest.mark.core`.

## Findings

| Id | Evidence (measured 2026-11-02 at `0cbfcc706`) | Finding |
|---|---|---|
| F-01 | Per-module counts of hand-formatted bullet literals (`f"- Field: {` or `"- Field: "`) and `Workflow history` references: `specs` 14/8, `backlog` 29/18, `releases` 11/4, `ipd_authoring` 11/1, `artifact_rename` 11/0, `plans_refs` 4/0, `plan_readiness` 1/10, `coverage_record` 3/5, `set_records` 1/1, `review_sequence` 3/1; `prompts` writes only inside its comment (`render_metadata_comment`, `inject_metadata_id6`, `update_metadata_status`) | Each module builds metadata text itself; the move replaces those sites with events. |
| F-02 | Raw write calls (`atomic_write`, `write_text`, `git_mv`): `set_records` 6, `artifact_rename` 5, `ipd_authoring` 4, `specs` 3, `backlog` 2, `releases` 2, `plans_refs` 2, `prompts` 1, `plan_readiness` 1, `coverage_record` 1; `readiness_recheck` 0 (it calls `plan_readiness.recheck_readiness`) | The writer surface of this plan. E-14 re-measures what remains. |
| F-03 | Writers the spec's step-4 list does not name but that write metadata: `research_cmd.run_new`/`run_set_outcome`/`run_set_priority`, `research_refs.run_mv`/`run_set_assign`, `research_archive.apply_moves` (`_rewrite_status_in_text`), `plans_archive.apply_shard_moves`, `artifact_adopt.apply_adoption`; the runner writers `mark_plan_attended`, `rederive_front_matter`, `perform_coordinator_proposal_file`, `restore_pre_s7_plan` (handed here by `t4gl15` Deferred) | 4.8 lists them as tooled writers ("the research shelf moves", `aw archive plans`, `aw adopt --summary`); no other child owns their write side, so this plan carries them. |
| F-04 | Blank line directly under `## Workflow history`: plans 1,430 none / 250 one; specs 19 / 29; backlog 1,133 / 0; walkthroughs 0 / 1. Four insertion rules exist (Step 0) | The writers disagree today; D-1 decides the kept behavior. |
| F-05 | 41 tracked plans carry `- Scope-Exceeded:`; their entries name 29 `.aw/records/` paths and 35 code paths; `_format_scope_exceeded_value` sorts, strips `;()`, folds newlines and caps a reason at 200 characters | Finalize paths are repository-relative and include code paths (OQ-03); the legacy render must keep today's sanitizing. |
| F-06 | 39 plans carry `- Coverage:` (`coverage_record.write`); 61 plan history lines contain `readiness re-check`; 3 plans carry `- Attended:` | Volume of the attestation and runner-field writers. |
| F-07 | `aw prompts new --help` and `aw ipd scaffold --help` show no `--summary`; `aw adopt --help` does; no `aw describe` or walkthrough-creating verb exists (`aw walkthroughs` is an invalid choice) | AC-36 case 1 needs two new options and a setter (E-03, E-04). |
| F-08 | Tests that call private writer helpers directly: `tests/test_plans_order_grammar.py` (`plans_refs._set_metadata`, 3 tests), `tests/test_spec_id6_filenames.py` (`artifact_rename._update_frontmatter_metadata`), `tests/test_prompts_set_surface.py` (`prompts.render_metadata_comment`), `tests/test_records_only_lane_rederive.py` (`runner_shared.rederive_front_matter`) | These functions keep their signatures as thin adapters over `artifact_meta`, so the pins stay valid without editing assertions; Order 11 (`9o83cr`) may delete the adapters. |
| F-09 | (filled by E-14) remaining raw writes with reasons | Audit record for AC-1 (owned by `9o83cr`). |

## Behavior decisions (kept behavior where writers disagreed, 4.3)

- D-1 (blank line under the history heading). KEPT per file: the legacy writer inserts the new line after an existing blank line when one is present and directly under the heading otherwise; it never adds or removes a blank line. This keeps every existing file's shape (F-04) and matches `attention_contract.history_block`, which ignores blank lines. CHANGED: `specs._append_history`'s normalization of a missing blank line (19 specs) no longer adds one, and `specs._append_history` and `status_set._prepend_workflow_history_entry` create a missing section differently today (specs at end of file, plans before the first `##`); the legacy writer uses the `status_set` rule for every type except prompts, which keep end-of-file (pinned by `2xwb9b` E-02). Named tests: `tests/test_specs_verbs.py::test_note_appends_one_record_only` (asserts the record count, not the blank line), `tests/test_history_order.py::test_fixture_a_newest_first`, and a new `tests/test_artifact_meta_legacy_writer.py` case per insertion rule (with blank line, without, section absent) that compares full file bytes. Any existing test that pins the OLD specs normalization fails the E-05 pin diff; it is then listed here by name with its changed assertion, as the PIN-FIRST RULE allows, and in no other case.
- D-2 (new bullet position). KEPT: in place when present; otherwise after `- Status:`, else after `- Id:`, else end of block; never in the body (a88210). The few writers with a different anchor (`coverage_record` after `- Readiness:`, `runner_shared.mark_plan_attended` at block end, `perform_coordinator_proposal_file` after `- Priority:`) change position only; no reader depends on bullet order (`ipd_schema.parse_metadata_block` is order-free). Named tests: `tests/test_coverage_record.py`, `tests/test_run_proposal_channel.py`.
- D-3 (scope fields in phase B). The logged values `within` and `widened` have no legacy bullet; the legacy file shows only `- Scope-Exceeded:` for `exceeded`, exactly as today. So in phase B the cache returns `scope_result` only from a just-written append (fixture tests) and the legacy loader reads it back from `- Scope-Exceeded:` as `exceeded`; `within` and `widened` become durable only at the cutover. This is the honest phase-B form of AC-39 (4); Order 13 re-demonstrates it on logs.
- D-4 (rename ledger). KEPT until the cutover: `record_history.record_rename` still writes the gitignored sidecar; no `rename` event exists in phase B.
- D-6 (finalize path root, OQ-03). CHANGED: `out_of_scope_paths` and `widened_paths` are validated against the repository root, not the records root; `path` is unchanged. Named test: the OQ-03 case in `tests/test_writers_scope_fields.py`, and any `tests/test_artifact_meta_registry.py` assertion that pinned the records-root rule for those two keys.
- D-5 (`restore_pre_s7_plan`). KEPT as a TEXT restore of the pre-pass value of `- Status:` and `- Readiness:` through `render_legacy_text`; it emits no `set readiness` event, because it reverts an unauthorized write rather than making one. After the cutover the equivalent is a log-level refusal of the S7-premature event, owned by the runner review path (`cxxmyv`).

## Proposed changes (ordered, validatable)

1. The phase-B legacy writer and its text mode (E-01).
2. Creating commands, `--summary`, `aw describe` (E-02 to E-04).
3. Notes, field setters, renames and shelf moves (E-05, E-06).
4. Attestations, finalize scope fields, retirement (E-07 to E-10).
5. Runner writer helpers, the merge and obligation tests, finish (E-11 to E-14).

## Deferred / out of scope (with reason)

- The `status_set` setter engine, including the `approval` and `readiness` attestation writes on transition and the `->reviewed` gate predicate.
  - Carrier: 2xwb9b
- Reader moves (`selectors`, `check_engine`, `attention`, `ipd_lint`, including `IPD-M112` reading the last `coverage` event and the display of `short_description`).
  - Carrier: ffceq0
- Reader moves of the runner, hooks and git-content gates through `read_at`.
  - Carrier: t4gl15
- A tooled command that records a NEW review round as one subject event (AC-14 writer form, handed here by `dcerjg`), and the `plan-review` and `spec-review` workflow text that tells agents to run it instead of writing `- Readiness:` (4.4 "The implementing plan names that command"). No `aw` verb writes review records today (`aw reviews` is read-only; `review_findings.write_review` has no CLI caller), so the command must be NEW, and its text changes the managed workflow bodies, which may land only in the cutover commit (C10a). This plan names the command `aw reviews record <subject-id6> --round <n> --verdict <v> [--readiness <r>] [--review-depth <t>] --file <review.md>` and leaves its build to the documents child, which already rewrites those workflow bodies.
  - Carrier: 90iqr1
- `rename` and path-bearing events, retiring the sidecar writer and the rename ledger (AC-31, AC-34 post-cutover form), and switching `write_legacy` off.
  - Carrier: cxxmyv
- Deleting the thin adapters kept for F-08 and every remaining legacy parser, plus the AC-1 test.
  - Carrier: 9o83cr
- A walkthrough-creating command (4.2 SHORT DESCRIPTION: "the plan names the tooled command"). Named here as `aw walkthrough new --set <set> --order <nn> --target <id6> --slug <slug> [--summary ...]` over the existing `set_records.write_walkthrough`; its CLI is needed only after the cutover, when a hand-written walkthrough has no log, so it lands with the documents that describe it.
  - Carrier: 90iqr1
- The `finalize` event payload that later replaces the interim scope fields.
  - Carrier: nq1src

## Scope check

- Over-scope: none. F-03 writers are included because 4.8 names them as tooled writers and no sibling owns them.
- Under-scope: the review-recording command and the walkthrough creator are deferred with carriers (above), because their user-facing text must not land before the cutover. Plan size: 14 E-items in 5 task groups, inside both limits; OQ-01 records the split seam if review finds E-02, E-05 or E-06 too large for one pass.

## Required tests / validation

New core test modules: `tests/test_artifact_meta_legacy_writer.py`, `tests/test_writers_create_summary.py`, `tests/test_writers_scope_fields.py`, `tests/test_writers_merge_independence.py`, `tests/test_writers_obligations.py`. All use `tmp_path` fixtures and real git repositories where git is involved; none reads source code.

Existing modules pinned before and after each move (equal PASSED sets): `test_specs_verbs`, `test_spec_id6_filenames`, `test_specs_releases_descriptive_safety`, `test_specs_date_containment`, `test_backlog`, `test_backlog_descriptive_safety`, `test_history_write_order`, `test_history_block_bounding`, `test_history_order`, `test_history_date_clock`, `test_history_date_clock_residual`, `test_releases`, `test_releases_cli`, `test_graduation_forward_links`, `test_prompts_new`, `test_prompts_set_surface`, `test_ipd_authoring`, `test_scaffold_history_clock`, `test_artifact_rename`, `test_artifact_group`, `test_rename_ledger`, `test_plans_group_order_preservation`, `test_plans_order_grammar`, `test_research_rename_frontmatter`, `test_research_set_assign_date_containment`, `test_research_cmd_create`, `test_research_priority`, `test_research_descriptive_safety`, `test_research_archive`, `test_plans_archive`, `test_artifact_adopt`, `test_descriptive_refusal_hoist`, `test_rename_group_machine_output`, `test_mutation_result_facts`, `test_artifact_refs_rewrite`, `test_plan_readiness_recheck`, `test_review_record_classifier`, `test_read_verb_zero_match_refusal`, `test_coverage_record`, `test_coverage_not_written`, `test_orchestrator_readiness`, `test_gradcover_end_to_end`, `test_scope_exceeded`, `test_finalize_refusal_findings`, `test_finalize_sendback`, `test_ipd_lifecycle_cli`, `test_orchestrator_retirement`, `test_orchestrator_child_retired`, `test_lifecycle_holder_gate`, `test_walkthrough_id6`, `test_slug_slice_trailing_hyphen`, `test_run_proposal_channel`, `test_records_only_lane_rederive`, `test_review_sequence_runner`, `test_question_preflight` (all under `tests/`).

Acceptance criteria of `4sd62s` that this plan OWNS:

| AC | Proven by | Note |
|---|---|---|
| AC-21 | E-13 | every 4.4a row with its pasted evidence; the `63zo2f` row is closed by this plan's commit |

CONTRIBUTES to (owned or finally shown elsewhere):

| AC | Proven by | Owner / final demonstration |
|---|---|---|
| AC-3 | E-12 (phase-B form: different artifacts merge without conflict through the moved writers) | `cxxmyv` re-demonstrates on logs |
| AC-6 | E-13 (b) (phase-B form: status line plus one history line, and the finalize scope bullet) | `cxxmyv` shows the `transition` event diff |
| AC-34 | E-01 and E-06 keep path writes as moves only; the path rules are enforced by `validate_new_events` on every event this plan writes | `cxxmyv` (path-bearing events start at the cutover); `tve77h` owns the projection |
| AC-36 case 1 | E-03, E-04 | `cxxmyv` re-demonstrates the full criterion |
| AC-39 (4) | E-09 (writer side; phase-B rendering per D-3) | `tve77h` owns the projection; `cxxmyv` re-demonstrates on logs |
| AC-15 | E-07, E-08 (writer-side refusal of `set readiness` and `set coverage`) | `2xwb9b` |
| AC-14a (1)-(2) | E-07 (the recheck writes only a `gate` event with `readiness`) | `2xwb9b`, `dcerjg` |
| AC-40 case 3 | E-02 and E-06 (a prompt edit rewrites only its comment key) | `dcerjg`, `cxxmyv` |
| AC-1b | E-14 (core and thorough tier lines at this merge) | `cxxmyv` |

Commands: the pin-first runs of each E-item, E-14's bare core gate, `make test-all`, `aw check`, `aw ipd lint --all`, `aw sanitize --agent`.

## Spec / documentation sync

One spec amendment: spec `4sd62s` 4.2 states that `out_of_scope_paths` and `widened_paths` are repository-relative (relative, no `..`, not absolute, inside the repository root), while `path` stays records-root-relative. Why: finalize paths are code paths (F-05: 35 of 64 measured entries name `agent_workflows/` or `tests/`) that have no records-root form, so the current wording would refuse every out-of-scope code path that finalize records today (OQ-03). Otherwise this implements `4sd62s` section 7 step 4 (second half), 4.2 SHORT DESCRIPTION (`--summary` on every creating command and the setter), 4.4 (finalize scope fields, `aw ipd recheck-readiness` as a gate `review` event, the coverage record as `op: coverage`), 4.4a (AC-21) and 4.8 (the tooled writers). `docs/cli-output-contract.md` gains the `aw describe` leaf and the two `--summary` options, and one `CHANGELOG.md` line records them, because they are user-visible in phase B. Workflow bodies (`plan-review`, `spec-review`) are NOT changed here (C10a; carried by `90iqr1`).

## Open questions

### OQ-01: Split this plan into 07a and 07b?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: The plan fits the limits (14 E-items, 5 task groups), but its pinned-module list is the longest of the Set. If review judges a group too large for one pass, split at the natural seam, each half one green merge under C10a: 07a = Task groups 1 to 3 (E-01 to E-06: the legacy writer, creating commands, `--summary`, `aw describe`, notes, field setters, renames; owns AC-36 case 1 contribution) and 07b = Task groups 4 and 5 (E-07 to E-14: recheck, coverage, finalize scope fields, retirement, runner helpers, merge test, AC-21 obligations), with 07b depending on `executed:<07a id6>`, and Orders 08 and 09 depending on 07b. AC-21 stays with 07b. Recommendation strength: medium (keep as one plan unless an executor reports a group exceeded one focused pass). Resolved: keep as one plan; `/plan-review` of this plan may apply the split at the stated seam.

### OQ-02: How does `short_description` appear on disk in phase B?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: As a `- Short-Description:` bullet (a `Short-Description:` key inside a prompt's comment; a `short-description:` YAML key in research front matter), registered as a recognized field in `ipd_schema.META_RECOGNIZED` and proven unflagged for the other types by `aw check all --agent` (E-03). Evidence: phase B has one on-disk format (C10a), the legacy loader reads bullets (tve77h E-11) so the value survives a cache rebuild, and an unregistered bullet is lint error `IPD-M103` on plans. The alternative (no on-disk form until the cutover) would make AC-36 case 1 untestable through `read()` after a cache deletion. The migration (dcerjg) maps the bullet to `short_description` with `description_source` absent (written by a command, not generated), and the census lists it. Recommendation strength: strong.

### OQ-03: Are finalize's `out_of_scope_paths` and `widened_paths` records-root-relative?

- Blocking: no
- Status: resolved
- Owner: plan-review (round 1, decision D-2)
- Resolution or deferral rationale: No; they are repository-relative, exactly as `Scope-Paths` and `runner_shared.compute_scope_reconciliation` produce them. F-05 measures 35 of 64 entries as code paths (`agent_workflows/...`, `tests/...`) that have no records-root form. The 4.2 PATH HISTORY rule ("relative to the resolved records root") governs the artifact's own `path` field; 4.2 lists `out_of_scope_paths` and `widened_paths` only as payload values "checked by the path rules", which this plan reads as: relative, no `..`, no absolute path, sanitizer-scanned. Re-checked at review: `tve77h` E-03 (c) as written DOES require "every `path`, `out_of_scope_paths` and `widened_paths` value" to "resolve inside the resolved records root", and spec 4.2 says these two keys "are checked by the path rules (PATH HISTORY below)", whose root is the records root. So the two approved texts and this plan disagree, and 35 of 64 measured finalize paths (F-05) would be refused. Because `artifact_meta.py` is in this plan's Scope-Paths, E-09 resolves it in the writer: `validate_new_events` applies the records-root containment rule to `path` only, and applies "relative, no `..`, not absolute, sanitizer-scanned, inside the REPOSITORY root" to `out_of_scope_paths` and `widened_paths`; a `tests/test_writers_scope_fields.py` case finalizes with an `agent_workflows/...` out-of-scope path and one `../x` path and asserts the first is stored and the second refused. The spec text is amended in the same change (the 4.2 sentence naming the path rules gets "repository-relative for `out_of_scope_paths` and `widened_paths`"), so `.aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md` is in Scope-Paths and the spec-sync section says why. Recommendation strength: strong. Owner of the decision: plan-review round 1 (D-2).

### OQ-04: Do the pure text-to-text runner helpers write through a file path?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. `rederive_front_matter` returns TEXT for a merge-stage resolution (its docstring: "it returns TEXT and performs no IO"), and `restore_pre_s7_plan` compares two in-memory snapshots. So `artifact_meta.render_legacy_text(text, events)` exposes the same renderer over a string, validated by the same `validate_new_events`; the caller still writes the file it already writes. Order 13 replaces both with log appends. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_artifact_meta_legacy_writer.py` with every test PASSED, including named tests for: an in-place bullet edit, a new bullet placed after `- Status:` and never below the first `##`, a prompt key written inside its comment with the body byte-identical, a history line prepended with and without a blank line under the heading (D-1), a refused `set readiness` leaving the file byte-identical (quote the `sha256sum` before/after), and the 40-record round trip reporting `40 byte-identical`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-02-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_releases.py tests/test_releases_cli.py tests/test_prompts_new.py tests/test_prompts_set_surface.py tests/test_ipd_authoring.py tests/test_backlog.py tests/test_spec_id6_filenames.py tests/test_scaffold_history_clock.py tests/test_history_date_clock.py tests/test_specs_releases_descriptive_safety.py tests/test_backlog_descriptive_safety.py tests/test_research_descriptive_safety.py tests/test_descriptive_refusal_hoist.py tests/test_walkthrough_id6.py tests/test_artifact_adopt.py tests/test_research_cmd_create.py tests/test_history_write_order.py`, plus the `rg -n "Workflow history"` output of E-02 showing no create-path text building.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k "summary and not describe"` with one PASSED test per creating command (seven) asserting `artifact_meta.read(id6).fields["short_description"]`, the three refusal tests (301 characters, newline, control character) each asserting exit code nonzero and `git status --porcelain` empty, and the 400-character `aw specs new --summary` test asserting no `short_description` and the body summary present; plus `aw ipd scaffold --help` and `aw prompts new --help` lines showing `--summary`.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste the transcript in a fixture repository: `aw describe <id6> --summary "Adds a widget."` (preview, exit 0, `git status --porcelain` empty), the same with `--apply` (exit 0, `git diff` shows one `- Short-Description:` line and one history line), the same on an executed plan (exit 0), `--clear --apply` (bullet removed), and `aw describe zzzzzz --summary x; echo $?` printing `2`; plus `python3 -m pytest -o addopts="" -v tests/test_writers_create_summary.py -k describe` all PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-05-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_specs_verbs.py tests/test_backlog.py tests/test_ipd_authoring.py tests/test_graduation_forward_links.py tests/test_research_cmd_create.py tests/test_research_priority.py tests/test_history_block_bounding.py tests/test_slug_slice_trailing_hyphen.py tests/test_history_order.py`, plus the E-05 `rg` output showing no hand-built history line in the four modules.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-06-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_artifact_rename.py tests/test_artifact_group.py tests/test_spec_id6_filenames.py tests/test_plans_group_order_preservation.py tests/test_plans_order_grammar.py tests/test_research_rename_frontmatter.py tests/test_research_set_assign_date_containment.py tests/test_research_archive.py tests/test_plans_archive.py tests/test_rename_ledger.py tests/test_rename_group_machine_output.py tests/test_mutation_result_facts.py tests/test_artifact_refs_rewrite.py`, and quote the PASSED line of `tests/test_plans_order_grammar.py::test_set_metadata_raises_on_unmatchable_order_line` (the batch-refusal-before-write behavior).
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-07-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_plan_readiness_recheck.py tests/test_review_record_classifier.py tests/test_read_verb_zero_match_refusal.py`, and `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py -k readiness` PASSED, with the test asserting the refused `set readiness=go` leaves the file sha256 unchanged.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-08-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_coverage_record.py tests/test_coverage_not_written.py tests/test_history_date_clock_residual.py tests/test_orchestrator_readiness.py tests/test_gradcover_end_to_end.py`, and `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py -k coverage` PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_scope_exceeded.py tests/test_writers_scope_fields.py tests/test_finalize_refusal_findings.py tests/test_finalize_sendback.py tests/test_ipd_lifecycle_cli.py` all PASSED, with `tests/test_scope_exceeded.py` unchanged (`git diff --stat tests/test_scope_exceeded.py` empty); quote the `tests/test_writers_scope_fields.py` assertions for `scope_result == "exceeded"` with its `out_of_scope_paths`, `"widened"` with its `widened_paths`, `"within"` with both lists empty, the rollup case with all three absent, and the refused out-of-append `set scope_result`; plus `rg -n "_insert_scope_exceeded_metadata" agent_workflows` returning no match.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-10-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_orchestrator_retirement.py tests/test_orchestrator_child_retired.py tests/test_lifecycle_holder_gate.py`.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: paste the `diff` of `.aw/state/xexn45/E-11-before.txt` and `-after.txt` (must print nothing; both files are the PIN-FIRST rule's sorted outcome lists) and both summary lines of `python3 -m pytest -o addopts="" -q -rA tests/test_run_proposal_channel.py tests/test_records_only_lane_rederive.py tests/test_review_sequence_runner.py tests/test_history_date_clock_residual.py tests/test_question_preflight.py tests/test_attended_session.py`, and quote the PASSED line of `tests/test_review_sequence_runner.py::test_ac07_readiness_written_before_s7_reverted_and_reasked`.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_merge_independence.py` all PASSED, and from the test log the `git merge` exit code `0` and `git diff --name-only --diff-filter=U` empty for the different-artifacts case, plus the nonzero exit code and the `--diff-filter=U` file name for the same-record case.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_writers_obligations.py tests/test_find_filters.py tests/test_cli_find.py tests/test_graduation_forward_links.py tests/test_readiness_absence_invariant.py` all PASSED; the AC-21 row table with one evidence reference per 4.4a row (the `63zo2f` row citing this plan commit hash); and the two fixture `git diff -U0` metadata hunks (backlog `done`, finalize) showing exactly the lines listed in E-13 (b).
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: paste: the E-14 `rg` output and the filled F-09 table; `git diff docs/cli-output-contract.md CHANGELOG.md`; the bare `python3 -m pytest` summary line with its wall time; the `make test-all` summary line; the `(location, rule)` comparison with `check-before.jsonl` showing no added pair; `aw ipd lint --all` summary with no new diagnostic; the `aw sanitize --agent` result record; and the `aw commit` output listing the committed paths.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` and `2xwb9b` are executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every move is pin-first: the named existing modules run green on the unmodified code before the move, and an assertion may change only where D-1 to D-6 name it.

Honesty rule: run the named modules, `python3 -m pytest` (core gate) and `make test-all`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit xexn45 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize xexn45` itself.
