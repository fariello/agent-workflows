# IPD: Move spec, plan, lifecycle, orchestration and runner test data onto the record builder

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. `59aiyh` (Order 10) carried the whole migration in seven batch items of 22 to 69 modules each, each hiding hundreds of edits. Measured 2026-11-07 at `ac76110f4`: this part's 81 test modules carry 1589 F-01 legacy lines and 26 private record-building helpers. Restructured 2026-11-08: each batch item runs the Order-49 codemod (`653ndz`) and hand-converts only the refusals its census (`653ndz` F-31) counts, so no item hides hundreds of hand edits. Part of the split of `59aiyh`; it uses the builder of Order 37 (`9rgn2w`).
- Scope: Batch subsets G3b, G4a, G4b, G4c of `59aiyh`'s batch items, each a named list of at most 25 modules, plus a finishing item. Each subset runs the Order-49 codemod (`653ndz`) and hand-converts only its census-counted refusals. Every subset applies the batch rule below (the `59aiyh` batch rule restructured for the codemod). EXCLUDES: the builder and fixtures (Order 37, `9rgn2w`); every other subset (Orders 38 to 40 and `59aiyh`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_spec_citation_anchors.py, tests/test_spec_edit_ack_gate.py, tests/test_spec_id6_filenames.py, tests/test_spec_production.py, tests/test_spec_review_attestation.py, tests/test_spec_review_dispatch.py, tests/test_spec_review_gate_kind.py, tests/test_specs_date_containment.py, tests/test_specs_evidence_gate_parity.py, tests/test_specs_from_backlog.py, tests/test_specs_metadata_duplicate_bullet.py, tests/test_specs_recursive_read.py, tests/test_specs_releases_descriptive_safety.py, tests/test_specs_releases_unsafe_field.py, tests/test_specs_set_adapter.py, tests/test_specs_set_gate_parity.py, tests/test_specs_status_dirs.py, tests/test_specs_verbs.py, tests/test_ipd_dependency_check.py, tests/test_ipd_dependency_statement_gate.py, tests/test_ipd_exec_finding_codes.py, tests/test_ipd_lifecycle_backward_edges.py, tests/test_ipd_lifecycle_cli.py, tests/test_ipd_lint.py, tests/test_ipdrunner_runagy_shim.py, tests/test_ipd_schema.py, tests/test_ipd_set_executor.py, tests/test_ipd_set_plan.py, tests/test_plan_priority_required.py, tests/test_plan_readiness_recheck.py, tests/test_plans_archive.py, tests/test_plans_archive_selectors.py, tests/test_plans_board.py, tests/test_plans_group_order_preservation.py, tests/test_plans_index.py, tests/test_plans_order_grammar.py, tests/test_plans_rename_selectors.py, tests/test_plan_status.py, tests/test_plan_transition_gate.py, tests/test_dependency_block_reporting.py, tests/test_executed_transition_gate_e2e.py, tests/test_executed_transition_gate.py, tests/test_finalize_refusal_findings.py, tests/test_finalize_sendback.py, tests/test_finalize_stale_plan_path.py, tests/test_lifecycle_gate_coverage.py, tests/test_lifecycle_holder_gate.py, tests/test_lifecycle_style.py, tests/test_question_carrier.py, tests/test_question_drain.py, tests/test_question_inbox.py, tests/test_question_parking.py, tests/test_question_preflight.py, tests/test_question_resume.py, tests/test_question_visibility.py, tests/test_scope_drift_lane_resolution.py, tests/test_scope_match.py, tests/test_scope_paths_status_agnostic.py, tests/test_scope_path_target_stale.py, tests/test_coverage_not_written.py, tests/test_coverage_record.py, tests/test_gradcover_end_to_end.py, tests/test_implementing_spec_replan.py, tests/test_orchestrator_child_retired.py, tests/test_orchestrator_kind_derivation.py, tests/test_orchestrator_not_approved_reason.py, tests/test_orchestrator_probe_payload.py, tests/test_orchestrator_probe_quotes.py, tests/test_orchestrator_probe_scope.py, tests/test_orchestrator_readiness.py, tests/test_orchestrator_refusal_reason_translation.py, tests/test_orchestrator_retirement.py, tests/test_orchestrator_row_grammar_source.py, tests/test_orchestrator_shape_composed.py, tests/test_orchestrator_shape_gate.py, tests/test_orchestrator_status_gate.py, tests/test_partition.py, tests/test_partition_set_cohesion.py, tests/test_readiness_absence_invariant.py, tests/test_terminal_status_vocabulary.py, tests/test_unresolved_selector_near_match.py, .aw/records/plans/pending/20261107-metastore-39-7qxey9-move-spec-plan-lifecycle-orchestration-and-runner-test-data.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 39
- Highest E allocated: 06
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 7qxey9

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-08 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): restructured per maintainer decision 2026-11-07 ("Codemod first, then small runs"); batch items E-01 to E-04 now run the Order-49 codemod 653ndz and hand-convert only its census-counted refusals; item E-05 (subset G5a) moved to 1upea0; added executed:653ndz.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 59aiyh per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

Every hand-built record in this part's 81 test modules comes from `tests/record_builder.py`, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`); because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the named subset: a module that the partition now places in this subset but the list below does not name is added and reported; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the subset's row in `653ndz` F-31, and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 25, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.


### Task group 1: batch subsets

- [ ] E-01 (carried from `59aiyh` E-05, batch G3, subset G3b) Batch G3b: the spec tests (`test_spec*`, `test_specs*`), 18 modules and 345 F-01 legacy lines at `ac76110f4` (48 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_spec_citation_anchors.py`, `tests/test_spec_edit_ack_gate.py`, `tests/test_spec_id6_filenames.py`, `tests/test_spec_production.py`, `tests/test_spec_review_attestation.py`, `tests/test_spec_review_dispatch.py`, `tests/test_spec_review_gate_kind.py`, `tests/test_specs_date_containment.py`, `tests/test_specs_evidence_gate_parity.py`, `tests/test_specs_from_backlog.py`, `tests/test_specs_metadata_duplicate_bullet.py`, `tests/test_specs_recursive_read.py`, `tests/test_specs_releases_descriptive_safety.py`, `tests/test_specs_releases_unsafe_field.py`, `tests/test_specs_set_adapter.py`, `tests/test_specs_set_gate_parity.py`, `tests/test_specs_status_dirs.py`, `tests/test_specs_verbs.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G3b` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G3b` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that asserts the bytes a SETTER wrote (for example `test_status_set.py` checking the rewritten `- Status:` line) keeps that assertion in phase B, because the written format is the subject. Each such assertion is listed with reason class `setter-byte assertion`, so Order 13 can convert it to `artifact_meta.read` plus the in-file mirror. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_spec_id6_filenames.py`: `_write_spec`; `tests/test_spec_production.py`: `_write_spec`, `_write_plan_content`; `tests/test_spec_review_attestation.py`: `_write_spec`, `_write_record`; `tests/test_spec_review_dispatch.py`: `_write_plan`, `_write_spec`, `_write_review_record`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 18 modules; 8 helpers; the `653ndz` F-31 `hand` count for G3b, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G3b outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-02 (carried from `59aiyh` E-06, batch G4, subset G4a) Batch G4a: the plan, lint and IPD tests (`test_ipd*`, `test_plan*`, `test_plans*`), 21 modules and 403 F-01 legacy lines at `ac76110f4` (41 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_ipd_dependency_check.py`, `tests/test_ipd_dependency_statement_gate.py`, `tests/test_ipd_exec_finding_codes.py`, `tests/test_ipd_lifecycle_backward_edges.py`, `tests/test_ipd_lifecycle_cli.py`, `tests/test_ipd_lint.py`, `tests/test_ipdrunner_runagy_shim.py`, `tests/test_ipd_schema.py`, `tests/test_ipd_set_executor.py`, `tests/test_ipd_set_plan.py`, `tests/test_plan_priority_required.py`, `tests/test_plan_readiness_recheck.py`, `tests/test_plans_archive.py`, `tests/test_plans_archive_selectors.py`, `tests/test_plans_board.py`, `tests/test_plans_group_order_preservation.py`, `tests/test_plans_index.py`, `tests/test_plans_order_grammar.py`, `tests/test_plans_rename_selectors.py`, `tests/test_plan_status.py`, `tests/test_plan_transition_gate.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G4a` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G4a` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Open-question rows (`- Blocking:`, `- Status: open`, `- Carrier:`) are body prose (N3) and are written through the builder's `body=` or `open_questions=` argument, never as metadata. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_ipd_dependency_statement_gate.py`: `_write_plan`; `tests/test_ipd_lifecycle_cli.py`: `_write_plan`; `tests/test_ipd_set_executor.py`: `_write_plan`; `tests/test_ipd_set_plan.py`: `_write_plan`; `tests/test_plans_archive_selectors.py`: `_make_plan`; `tests/test_plans_group_order_preservation.py`: `_seed_plan_record`; `tests/test_plan_status.py`: `_write_plan`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 21 modules; 7 helpers; the `653ndz` F-31 `hand` count for G4a, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G4a outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-03 (carried from `59aiyh` E-06, batch G4, subset G4b) Batch G4b: the finalize, lifecycle, scope, executed-gate, question and dependency tests (`test_finalize*`, `test_lifecycle*`, `test_scope*`, `test_executed*`, `test_exec*`, `test_question*`, `test_dependency*`), 20 modules and 318 F-01 legacy lines at `ac76110f4` (89 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_dependency_block_reporting.py`, `tests/test_executed_transition_gate_e2e.py`, `tests/test_executed_transition_gate.py`, `tests/test_finalize_refusal_findings.py`, `tests/test_finalize_sendback.py`, `tests/test_finalize_stale_plan_path.py`, `tests/test_lifecycle_gate_coverage.py`, `tests/test_lifecycle_holder_gate.py`, `tests/test_lifecycle_style.py`, `tests/test_question_carrier.py`, `tests/test_question_drain.py`, `tests/test_question_inbox.py`, `tests/test_question_parking.py`, `tests/test_question_preflight.py`, `tests/test_question_resume.py`, `tests/test_question_visibility.py`, `tests/test_scope_drift_lane_resolution.py`, `tests/test_scope_match.py`, `tests/test_scope_paths_status_agnostic.py`, `tests/test_scope_path_target_stale.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G4b` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G4b` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Open-question rows (`- Blocking:`, `- Status: open`, `- Carrier:`) are body prose (N3) and are written through the builder's `body=` or `open_questions=` argument, never as metadata. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_executed_transition_gate_e2e.py`: `_write_plan`, `_write_plan_at`; `tests/test_lifecycle_holder_gate.py`: `_write_plan`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 20 modules; 3 helpers; the `653ndz` F-31 `hand` count for G4b, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G4b outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-04 (carried from `59aiyh` E-06, batch G4, subset G4c) Batch G4c: the orchestration, coverage, readiness and partition tests (`test_orchestrator*`, `test_coverage*`, `test_gradcover*`, `test_readiness*`, `test_partition*`, `test_unresolved*`, `test_terminal*`, `test_implementing*`), 22 modules and 523 F-01 legacy lines at `ac76110f4` (70 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_coverage_not_written.py`, `tests/test_coverage_record.py`, `tests/test_gradcover_end_to_end.py`, `tests/test_implementing_spec_replan.py`, `tests/test_orchestrator_child_retired.py`, `tests/test_orchestrator_kind_derivation.py`, `tests/test_orchestrator_not_approved_reason.py`, `tests/test_orchestrator_probe_payload.py`, `tests/test_orchestrator_probe_quotes.py`, `tests/test_orchestrator_probe_scope.py`, `tests/test_orchestrator_readiness.py`, `tests/test_orchestrator_refusal_reason_translation.py`, `tests/test_orchestrator_retirement.py`, `tests/test_orchestrator_row_grammar_source.py`, `tests/test_orchestrator_shape_composed.py`, `tests/test_orchestrator_shape_gate.py`, `tests/test_orchestrator_status_gate.py`, `tests/test_partition.py`, `tests/test_partition_set_cohesion.py`, `tests/test_readiness_absence_invariant.py`, `tests/test_terminal_status_vocabulary.py`, `tests/test_unresolved_selector_near_match.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G4c` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G4c` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Open-question rows (`- Blocking:`, `- Status: open`, `- Carrier:`) are body prose (N3) and are written through the builder's `body=` or `open_questions=` argument, never as metadata. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_gradcover_end_to_end.py`: `_write_backlog_item`; `tests/test_implementing_spec_replan.py`: `_write_spec`, `_write_plan`; `tests/test_orchestrator_probe_scope.py`: `_make_plan_text`, `write_plan`; `tests/test_orchestrator_retirement.py`: `_write_plan`, `write_plan`; `tests/test_partition.py`: `make_item`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 22 modules; 8 helpers; the `653ndz` F-31 `hand` count for G4c, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G4c outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-06 Finish this part: run `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA` over every module of G3b, G4a, G4b, G4c once more and confirm the outcome multiset equals the union of the subsets' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit 7qxey9 -- <each changed path>`, one commit per subset allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (New finishing item for this part; the full-suite comparison stays in `59aiyh` E-12.)
  - Depends on: E-01, E-02, E-03, E-04
  - Expected outcome: the union comparison is empty; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`): `artifact_meta.registry_fields(type)`, `artifact_meta.validate_event`, `artifact_meta.validate_new_events(type, events, *, records_root, migration_import=False)`, `artifact_meta.read(id6) -> State`, `artifact_meta.create(...)` and `artifact_meta.append(id6, events, *, expect_seq)`. Order 02's `create`/`append` write the log format; `2xwb9b` E-03 adds the phase-B legacy branch of `append` and `xexn45` E-01 routes the phase-B branch of `create` and `append` through `write_legacy`, with `render_legacy_text(text, events)` (`xexn45` E-11) as the same renderer over a string. In phase B the on-disk format is the bullet format; the legacy loader reads it into the cache.
- `review_findings.render_review` (pure) and `review_findings.write_review` render and write a `.review.md` record; no CLI calls `write_review` (`xexn45` Findings).
- The existing shared plan builder is `support.ready_plan_text`, which is "BUILT FROM THE REAL GENERATOR (`ipd_authoring.build_skeleton`)" and then fills the fields a draft leaves open; the builder keeps that approach for plans, so a scaffold change still reaches every fixture.
- Shared test plumbing lives in `tests/support.py` (`init_repo`, `git`, `run_cli`, `pinned_env`, `ready_plan_text`, `scope_drift_repo`); `tests/repo_template.py` (`copy_template_repo`) gives a pre-built repository; there is no `tests/conftest.py`, and the root `conftest.py` owns tier selection.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); core modules set `pytestmark = pytest.mark.core`; `slow` tests are listed in `tests/slow_allowlist.txt`; `pyproject.toml` `addopts` deselects `slow` and `livecorpus`, so a complete comparison passes `-m ""`, and `pytest-randomly` is installed, so a deterministic order needs `-p no:randomly`.
- `tests/fixtures/review-pilot/` is the input corpus of `tools/review_pilot.py` (`manifest.json` names each plan file, `defects.json` quotes exact text to plant), and `tests/test_review_pilot.py` copies the whole directory into its fixture repository.
- Filenames come from `artifact_naming.build_clustered_name` and parse with `artifact_naming.parse_clustered`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4` for the subsets; F-01, F-03, F-06 and F-08 copied from `59aiyh` (measured at `0cbfcc706` and at review).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l --glob '*.py' -e '- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|## Workflow history' tests` lists 309 files (307 test modules, `support.py`, `conformance_matrix.py`) of 717 Python files; 6,638 matching lines. The narrower `- Id:`/`- Status:`/`## Workflow history` pattern: 300 files, 3,430 lines | Spec section 6 counted 268 of 680 files and 2,607 matches at round 2; the plan's pattern is broader (21 fields). |
| F-03 | Family split by filename prefix, re-measured at review (HEAD `4a7499289`, 311 files, 6,657 lines) with a FIRST-MATCH rule (a file goes to the first group, in order G1 to G6, whose pattern list matches its basename; unmatched files go to G7): G1 39 files, 1,568 lines; G2 22, 1,102; G3 28, 795; G4 63, 1,244; G5 46, 598; G6 69, 1,004; G7 44, 346. Six files match two groups and are assigned by that rule (`test_ipd_authoring` G3, `test_readiness_absence_invariant` G4, `test_runner_backlog_close_behavior` G1, `test_orchestrator_retire_closes_backlog` G1, `test_records_only_lane_rederive` G5, `test_ipdrunner_runagy_shim` G4). The authored counts (G6 99, G7 11) did not sum to the file total; the first-match rule makes the partition exhaustive and disjoint. EXCLUDED from every batch (literal legacy input is their subject; owned by other plans): `tests/test_artifact_meta_*.py` (`tve77h`, `2xwb9b`), `tests/test_artifact_meta_legacy_writer.py` and `tests/test_writers_*.py` (`xexn45`), `tests/test_m0001_*.py` and `tests/test_migrations_chain.py` (`dcerjg`, `ya4ee4`) | Seven batches (E-03 to E-09); G1, G4 and G6 carry a pre-measured split seam (OQ-01). |
| F-06 | (written by E-11) remaining legacy strings in `tests/` after the batches, each with one reason class: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, `body prose` | Order 13 changes the builder plus the F-06 rows of class `setter-byte assertion`; `invalid-input` rows already go through `raw_fields=` and need a decision at the cutover (an invalid bullet has no log-format equivalent); every other class is either a legacy-format test (moved to the migration tests at the cutover) or prose. |
| F-08 | At review, 15 test modules write a deliberately invalid metadata value (for example `tests/test_releases.py` "`- Status: bogus`", `tests/test_check_engine.py` "`- Status: EXECUTED`", `tests/test_specs_set_adapter.py` "`- Priority: bogus`") | A builder that validates every field cannot build these; E-01 adds `raw_fields=` and the batch rule lists them as `invalid-input`. |
| F-11 | Subsets of this part, by the F-03 first-match rule at `ac76110f4`, each split from its group by basename pattern so no item exceeds 25 modules | See the table below. |

| Subset | Modules | Count | F-01 lines | Helpers |
|---|---|---|---|---|
| G3b | spec tests (`test_spec*`, `test_specs*`) | 18 | 345 | 8 |
| G4a | plan, lint and IPD tests (`test_ipd*`, `test_plan*`, `test_plans*`) | 21 | 403 | 7 |
| G4b | finalize, lifecycle, scope, executed-gate, question and dependency tests (`test_finalize*`, `test_lifecycle*`, `test_scope*`, `test_executed*`, `test_exec*`, `test_question*`, `test_dependency*`) | 20 | 318 | 3 |
| G4c | orchestration, coverage, readiness and partition tests (`test_orchestrator*`, `test_coverage*`, `test_gradcover*`, `test_readiness*`, `test_partition*`, `test_unresolved*`, `test_terminal*`, `test_implementing*`) | 22 | 523 | 8 |

## Proposed changes (ordered, validatable)

1. Migrate subsets G3b, G4a, G4b, G4c under the batch rule (E-01 to E-04), each by the codemod plus its census-counted refusals.
2. Re-run the union, the core gate, commit (E-06).

## Deferred / out of scope (with reason)

- Batch subset G5a (the runner, lane and merge tests, carried from `59aiyh` E-07): Moved to 1upea0 (restructuring 2026-11-08 per maintainer decision "Codemod first, then small runs"; at most 4 batch items per plan).
  - Carrier: 1upea0
- The fixture codemod and its census (F-30, F-31).
  - Carrier: 653ndz
- The builder, its tests, the baselines and the tracked fixtures.
  - Carrier: 9rgn2w
- The remaining subsets, the switch-point proof, the F-06 census and the full-suite comparison.
  - Carrier: 59aiyh
- Adding `RECORD_FORMAT = "log"` and converting setter-byte assertions (cutover commit).
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No production module changes; every Scope-Paths entry is a module named in one subset.
- Under-scope: none known. Size: 5 E-items (4 batch items and the finish), 82 Scope-Paths. Every batch item is one codemod run over at most 25 modules plus at most 25 census-counted hand conversions (the per-item step bound); the plan-level Scope-Paths count exceeds the 12-entry guideline, see the size assessment.

## Required tests / validation

Each subset is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, unchanged assertions, the same outcomes. Commands: the batch rule's command per subset, the bare core gate `python3 -m pytest`, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` section 6 and section 7 step 6.

## Open questions

### OQ-01: Can the subsets of this part run in any order?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. The subsets are disjoint module lists, each needs only the builder (Order 37), and none edits `tests/support.py` (that is `59aiyh`'s last subset). Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `.aw/state/59aiyh/G3b-files.txt`, the empty `diff .aw/state/59aiyh/G3b-before.txt .aw/state/59aiyh/G3b-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match, and the list of setter-byte assertions kept for Order 13 (file::test and the asserted line), and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G3b-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G3b, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G4a-files.txt`, the empty `diff .aw/state/59aiyh/G4a-before.txt .aw/state/59aiyh/G4a-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match (open-question body rows shown as written through `body=`/`open_questions=`), and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G4a-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G4a, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `.aw/state/59aiyh/G4b-files.txt`, the empty `diff .aw/state/59aiyh/G4b-before.txt .aw/state/59aiyh/G4b-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match (open-question body rows shown as written through `body=`/`open_questions=`), and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G4b-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G4b, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `.aw/state/59aiyh/G4c-files.txt`, the empty `diff .aw/state/59aiyh/G4c-before.txt .aw/state/59aiyh/G4c-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match (open-question body rows shown as written through `body=`/`open_questions=`), and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G4c-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G4c, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the `diff` of the concatenated, sorted `-before.txt` lists of G3b, G4a, G4b, G4c against the combined after-run list (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit 7qxey9` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The step bound holds: every batch item is one run of the tested codemod (`653ndz`) over at most 25 named test modules, and its hand work is the census-counted refusals, at most 25 by the batch rule's stop. The plan-level bound (12 Scope-Paths) does not: the split of `59aiyh` was allotted four Order numbers (37 to 40) for 318 test modules, and one of them carries the builder, so each batch part carried five subsets; after the 2026-11-08 restructuring it carries four (81 modules), the fifth moved to `1upea0`. The subsets are disjoint and independently verifiable (each has its own before/after outcome diff), so a run that stops after any subset leaves a consistent, committed state, and the remaining subsets can be split into further plans without changing any item text if a turn proves too long.

Execute only after human approval (`Status: approved`) and after `9rgn2w`, `653ndz`, `g5hpbb`, `tve77h` and `xexn45` are executed. OQ-01 is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a subset cannot keep its outcome list identical without a production change, stop that subset and report the missing capability rather than changing production code or an assertion.

Honesty rule: run the batch comparisons and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 7qxey9 -- <paths>` (one commit per subset allowed); never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
