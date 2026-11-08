# IPD: Move setter, runner-lane and first-half unmatched test data onto the record builder with the fixture codemod

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. The batch parts `x05v02`, `7qxey9` and `nbfg7w` (Orders 38 to 40) each carried five batch subsets; under the maintainer decision 2026-11-07 ("Codemod first, then small runs") every batch item runs the Order-49 codemod (`653ndz`) and hand-converts only its census-counted refusals, and each batch plan holds at most four batch items. This part carries the fifth subset of each: G3a (from `x05v02`), G5a (from `7qxey9`) and G7a (from `nbfg7w`). Measured 2026-11-07 at `ac76110f4`: 57 test modules, 1,044 F-01 legacy lines, 3 private record-building helpers.
- Scope: Batch subsets G3a, G5a, G7a, moved verbatim (module lists unchanged) from `x05v02` E-05, `7qxey9` E-05 and `nbfg7w` E-05, plus a finishing item. Each subset runs the codemod and hand-converts only its census-counted refusals under the batch rule below. EXCLUDES: the builder and fixtures (`9rgn2w`); the codemod and its census (`653ndz`); every other subset (Orders 38 to 40 and `59aiyh`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_bidi_control_rejection.py, tests/test_descriptive_length_classes.py, tests/test_ipd_authoring.py, tests/test_scaffold_history_clock.py, tests/test_set_dispatch_dedup.py, tests/test_set_dispatch_parity.py, tests/test_set_refuses_review_record.py, tests/test_status_set_descriptive_safety.py, tests/test_status_set_metadata_region.py, tests/test_status_set_meta_writer.py, tests/test_status_set_partial_batch.py, tests/test_status_set.py, tests/test_agy_runipd_cli.py, tests/test_agy_run_resolve_ipd_recursive.py, tests/test_agy_skip_permissions_default.py, tests/test_lane_rule_break_detection.py, tests/test_merge_gate_spec_anchors.py, tests/test_oc_runipd.py, tests/test_records_only_lane_rederive.py, tests/test_run_analytics_review_cost.py, tests/test_run_dir_parents_are_guaranteed.py, tests/test_runner_bare_verb_shim.py, tests/test_runner_fallback_bindings.py, tests/test_runner_findings_dependency_gate.py, tests/test_runner_peer_dependency.py, tests/test_runner_shared.py, tests/test_runner_shared_restored_behavior.py, tests/test_runner_stop_triggers_e2e.py, tests/test_run_proposal_channel.py, tests/test_runs_answer.py, tests/test_run_selection_policy.py, tests/test_run_summary_table.py, tests/test_run_viewer.py, tests/test_action_table_runner_parity.py, tests/test_already_landed_dispatch.py, tests/test_authoring_coverage_guidance.py, tests/test_awcmdsurf_mutation_verbs.py, tests/test_awmigrename.py, tests/test_awphysical_tools.py, tests/test_collision_population_parity.py, tests/test_companion_record_owner_root.py, tests/test_completion.py, tests/test_cross_tree_session_refusal.py, tests/test_defect_report.py, tests/test_doctor.py, tests/test_drift_detail_escaping.py, tests/test_empty_result_convention_doc.py, tests/test_explicit_dir_non_project.py, tests/test_explicit_dir_subdir_resolution.py, tests/test_generators_writing_standard_pointer.py, tests/test_generic_color_depth.py, tests/test_id6_global_mint.py, tests/test_identity_rename_hint.py, tests/test_index_check_agent_records.py, tests/test_index_rebuild.py, tests/test_index_write_agent_records.py, tests/test_inlane_retirement_lands.py, .aw/records/plans/pending/20261108-metastore-50-1upea0-move-setter-runner-lane-and-first-half-unmatched-test-data-o.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 50
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 1upea0

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-08 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from x05v02, 7qxey9 and nbfg7w (their E-05 subsets G3a, G5a, G7a) per maintainer decision 2026-11-07 ("Codemod first, then small runs"; at most 4 batch items per plan; no single E/V item hides hundreds of steps).

## Goal

Every hand-built record in this part's 57 test modules comes from `tests/record_builder.py`, written by the Order-49 codemod or, for its census-counted refusals only, by hand, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

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

- [ ] E-01 (carried via `x05v02` E-05 from `59aiyh` E-05, batch G3, subset G3a) Batch G3a: the setter, scaffold and authoring tests (`test_status*`, `test_set_*`, `test_scaffold*`, `test_ipd_authoring*`, `test_descriptive*`, `test_bidi*`), 12 modules and 490 F-01 legacy lines at `ac76110f4` (80 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_bidi_control_rejection.py`, `tests/test_descriptive_length_classes.py`, `tests/test_ipd_authoring.py`, `tests/test_scaffold_history_clock.py`, `tests/test_set_dispatch_dedup.py`, `tests/test_set_dispatch_parity.py`, `tests/test_set_refuses_review_record.py`, `tests/test_status_set_descriptive_safety.py`, `tests/test_status_set_metadata_region.py`, `tests/test_status_set_meta_writer.py`, `tests/test_status_set_partial_batch.py`, `tests/test_status_set.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G3a` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G3a` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that asserts the bytes a SETTER wrote (for example `test_status_set.py` checking the rewritten `- Status:` line) keeps that assertion in phase B, because the written format is the subject. Each such assertion is listed with reason class `setter-byte assertion`, so Order 13 can convert it to `artifact_meta.read` plus the in-file mirror. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_status_set.py`: `_write_spec_review_record`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 12 modules; 1 helpers; the `653ndz` F-31 `hand` count for G3a, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G3a outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-02 (carried via `7qxey9` E-05 from `59aiyh` E-07, batch G5, subset G5a) Batch G5a: the runner, lane and merge tests (`test_oc_*`, `test_agy*`, `test_runner*`, `test_run_*`, `test_runs_*`, `test_lane*`, `test_records_only*`, `test_merge*`), 21 modules and 400 F-01 legacy lines at `ac76110f4` (93 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_agy_runipd_cli.py`, `tests/test_agy_run_resolve_ipd_recursive.py`, `tests/test_agy_skip_permissions_default.py`, `tests/test_lane_rule_break_detection.py`, `tests/test_merge_gate_spec_anchors.py`, `tests/test_oc_runipd.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_run_analytics_review_cost.py`, `tests/test_run_dir_parents_are_guaranteed.py`, `tests/test_runner_bare_verb_shim.py`, `tests/test_runner_fallback_bindings.py`, `tests/test_runner_findings_dependency_gate.py`, `tests/test_runner_peer_dependency.py`, `tests/test_runner_shared.py`, `tests/test_runner_shared_restored_behavior.py`, `tests/test_runner_stop_triggers_e2e.py`, `tests/test_run_proposal_channel.py`, `tests/test_runs_answer.py`, `tests/test_run_selection_policy.py`, `tests/test_run_summary_table.py`, `tests/test_run_viewer.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G5a` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G5a` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that builds a two-branch merge or a lane worktree commits builder-made records on each branch with real `git`. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_runner_findings_dependency_gate.py`: `_write_review`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 21 modules; 1 helpers; the `653ndz` F-31 `hand` count for G5a, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G5a outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-03 (carried via `nbfg7w` E-05 from `59aiyh` E-09, batch G7, subset G7a) Batch G7a: the unmatched test modules, first half (basename sorts before `test_l`), 24 modules and 154 F-01 legacy lines at `ac76110f4` (61 of them `- Id:` lines). The module list, re-derived by the batch rule's first-match partition at the current HEAD and restricted to this subset, was at the split: `tests/test_action_table_runner_parity.py`, `tests/test_already_landed_dispatch.py`, `tests/test_authoring_coverage_guidance.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_awmigrename.py`, `tests/test_awphysical_tools.py`, `tests/test_collision_population_parity.py`, `tests/test_companion_record_owner_root.py`, `tests/test_completion.py`, `tests/test_cross_tree_session_refusal.py`, `tests/test_defect_report.py`, `tests/test_doctor.py`, `tests/test_drift_detail_escaping.py`, `tests/test_empty_result_convention_doc.py`, `tests/test_explicit_dir_non_project.py`, `tests/test_explicit_dir_subdir_resolution.py`, `tests/test_generators_writing_standard_pointer.py`, `tests/test_generic_color_depth.py`, `tests/test_id6_global_mint.py`, `tests/test_identity_rename_hint.py`, `tests/test_index_check_agent_records.py`, `tests/test_index_rebuild.py`, `tests/test_index_write_agent_records.py`, `tests/test_inlane_retirement_lands.py`. Run the codemod on these modules and apply the batch rule with `<batch>` = `G7a` (outcome lists identical); hand-convert ONLY the refusals that `653ndz` F-31 row `G7a` lists with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_action_table_runner_parity.py`: `_write_plan`); a surviving helper is listed with its reason. (Measured units: 1 codemod run over 24 modules; 1 helpers; the `653ndz` F-31 `hand` count for G7a, at most 25 by the batch rule's stop. The F-01 line count is context: the tool, not the executor, performs those edits.)
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the G7a outcome lists; the remaining legacy-string count for the subset and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-04 Finish this part: run `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA` over every module of G3a, G5a, G7a once more and confirm the outcome multiset equals the union of the subsets' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit 1upea0 -- <each changed path>`, one commit per subset allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (Finishing item for this part; the full-suite comparison stays in `59aiyh` E-12.)
  - Depends on: E-01, E-02, E-03
  - Expected outcome: the union comparison is empty; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

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
| F-11 | Subsets of this part, by the F-03 first-match rule at `ac76110f4`, moved unchanged from the three earlier batch parts | See the table below; each item's hand count comes from `653ndz` F-31. |

| Subset | Modules | Count | F-01 lines | Helpers | Moved from |
|---|---|---|---|---|---|
| G3a | setter, scaffold and authoring tests (`test_status*`, `test_set_*`, `test_scaffold*`, `test_ipd_authoring*`, `test_descriptive*`, `test_bidi*`) | 12 | 490 | 1 | `x05v02` E-05 |
| G5a | runner, lane and merge tests (`test_oc_*`, `test_agy*`, `test_runner*`, `test_run_*`, `test_runs_*`, `test_lane*`, `test_records_only*`, `test_merge*`) | 21 | 400 | 1 | `7qxey9` E-05 |
| G7a | unmatched test modules, first half (basename sorts before `test_l`) | 24 | 154 | 1 | `nbfg7w` E-05 |

## Proposed changes (ordered, validatable)

1. Migrate subsets G3a, G5a, G7a under the batch rule (E-01 to E-03), each by the codemod plus its census-counted refusals.
2. Re-run the union, the core gate, commit (E-04).

## Deferred / out of scope (with reason)

- The builder, its tests, the baselines and the tracked fixtures.
  - Carrier: 9rgn2w
- The fixture codemod and its census (F-30, F-31).
  - Carrier: 653ndz
- The remaining subsets, the switch-point proof, the F-06 census and the full-suite comparison.
  - Carrier: 59aiyh
- Adding `RECORD_FORMAT = "log"` and converting setter-byte assertions (cutover commit).
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No production module changes; every Scope-Paths entry is a module named in one subset, plus this plan.
- Under-scope: none known. Size: 4 E-items (3 batch items and the finish), 58 Scope-Paths. Every batch item is one codemod run over at most 24 modules plus at most 25 census-counted hand conversions (the per-item step bound); the plan-level Scope-Paths count exceeds the 12-entry guideline, see the size assessment.

## Required tests / validation

Each subset is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, unchanged assertions, the same outcomes. Commands: the batch rule's command per subset, the codemod's `--apply` report, the bare core gate `python3 -m pytest`, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` section 6 and section 7 step 6.

## Open questions

### OQ-01: Can the subsets of this part run in any order, and alongside Orders 38 to 40?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. The subsets are disjoint module lists, disjoint from every other batch part, each needs only the builder (`9rgn2w`) and the codemod (`653ndz`), and none edits `tests/support.py` (that is `59aiyh`'s last subset). Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `.aw/state/59aiyh/G3a-files.txt`, the empty `diff .aw/state/59aiyh/G3a-before.txt .aw/state/59aiyh/G3a-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match, and the list of setter-byte assertions kept for Order 13 (file::test and the asserted line), and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G3a-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G3a, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G5a-files.txt`, the empty `diff .aw/state/59aiyh/G5a-before.txt .aw/state/59aiyh/G5a-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match; the outcome lists are run with the batch rule's `-m ""`, so `slow` tests are included; paste the count of `slow` node ids in the list, and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G5a-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G5a, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `.aw/state/59aiyh/G7a-files.txt`, the empty `diff .aw/state/59aiyh/G7a-before.txt .aw/state/59aiyh/G7a-after.txt`, the before and after F-01 `rg -c` totals for the subset, the reason class of every remaining match, and the before and after helper census of the E-09 `rg` pattern over the subset's modules with each surviving helper and its reason, the `.aw/state/59aiyh/G7a-codemod.json` summary (per-module rewrites, refusals by reason code and disposition, outcome-list hashes), the `653ndz` F-31 row for G7a, and the hand count with every hand-converted site listed (module, line, reason code).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the `diff` of the concatenated, sorted `-before.txt` lists of G3a, G5a, G7a against the combined after-run list (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit 1upea0` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: The step bound holds: every batch item is one run of the tested codemod (`653ndz`) over at most 24 named test modules, and its hand work is the census-counted refusals, at most 25 by the batch rule's stop. The plan-level bound (12 Scope-Paths) does not, because the Scope-Paths list names every module the codemod may rewrite (57). The subsets are disjoint and independently verifiable (each has its own before/after outcome diff), so a run that stops after any subset leaves a consistent, committed state.

Execute only after human approval (`Status: approved`) and after `9rgn2w`, `653ndz`, `g5hpbb`, `tve77h` and `xexn45` are executed. OQ-01 is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a subset cannot keep its outcome list identical without a production change, stop that subset and report the missing capability rather than changing production code or an assertion.

Honesty rule: run the batch comparisons and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 1upea0 -- <paths>` (one commit per subset allowed); never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
