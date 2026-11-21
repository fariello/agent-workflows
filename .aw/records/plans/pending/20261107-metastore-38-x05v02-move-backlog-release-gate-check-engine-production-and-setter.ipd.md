# IPD: Move backlog, release-gate, check-engine, production and setter test data onto the record builder

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. `59aiyh` (Order 10) carried the whole migration in seven batch items of 22 to 69 modules each, each hiding hundreds of edits. Measured 2026-11-07 at `ac76110f4`: this part's 62 test modules carry 2677 F-01 legacy lines and 23 private record-building helpers. Restructured 2026-11-08: each batch item runs the Order-49 codemod (`653ndz`) and hand-converts only the refusals its census (`653ndz` F-31) counts, so no item hides hundreds of hand edits. Part of the split of `59aiyh`; it uses the builder of Order 37 (`9rgn2w`).
- Scope: FINISHING PART after the round-3 split (2026-11-09, research `nj8zdp` guidance): 8 modules of subset G2b in two items of 4 (E-04, E-07) and the finishing item E-06, which also converts any module the partition now places in subsets G1a, G1b, G2a, G2b that no plan names. The other modules of subsets G1a, G1b, G2a, G2b moved to the chunk plans `id2pdx`, `2fn0vd`, `isj48z`, `dg43sc`, `wirc2e`, `872zd9`, `zl2pki` (F-41). Before the round-3 split: Batch subsets G1a, G1b, G2a, G2b of `59aiyh`'s batch items, each a named list of at most 25 modules, plus a finishing item. Each subset runs the Order-49 codemod (`653ndz`) and hand-converts only its census-counted refusals. Every subset applies the batch rule below (the `59aiyh` batch rule restructured for the codemod). EXCLUDES: the builder and fixtures (Order 37, `9rgn2w`); every other subset (Orders 38 to 40 and `59aiyh`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_production_correction_turn.py, tests/test_production_fix_it.py, tests/test_production_prompt_writing_standard.py, tests/test_production_resume_handoff.py, tests/test_production_set_check.py, tests/test_severity_truth_surfaces.py, tests/test_source_citation_scan.py, tests/test_suppress_narrowing.py, .aw/records/plans/pending/20261107-metastore-38-x05v02-move-backlog-release-gate-check-engine-production-and-setter.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:id2pdx, executed:2fn0vd, executed:isj48z, executed:dg43sc, executed:wirc2e, executed:872zd9, executed:zl2pki
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 38
- Highest E allocated: 07
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: x05v02
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): plan-review verified E/V bijection, Scope-Paths, batch rules, execution gate, and state directory initialization; findings PR-001..PR-005 fixed; marked reviewed and go-pending-approval.
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-01, E-02, E-03 and 7 to 14 modules of E-04 moved to id2pdx, 2fn0vd, isj48z, dg43sc, wirc2e, 872zd9, zl2pki; kept 8 modules of G2b as E-04 and E-07; Highest E allocated raised to 07.
- 2026-11-08 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): restructured per maintainer decision 2026-11-07 ("Codemod first, then small runs"); batch items E-01 to E-04 now run the Order-49 codemod 653ndz and hand-convert only its census-counted refusals; item E-05 (subset G3a) moved to 1upea0; added executed:653ndz.
- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 59aiyh per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

After the round-3 split this plan converts 8 modules of subset G2b and closes subsets G1a, G1b, G2a, G2b once its chunk plans are executed. The family goal: Every hand-built record in this part's 62 test modules comes from `tests/record_builder.py`, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Split note (round 3, 2026-11-09, research `nj8zdp` guidance): items E-01, E-02, E-03 and all but 8 modules of E-04 moved to the chunk plans named in F-41 and in `## Deferred / out of scope`; this plan keeps 8 modules of subset G2b as E-04 and E-07 (4 each) and the finishing item E-06.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`), carried by the round-3 split into Order 170 (`j6o96i`) with the same ids; because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the modules each batch item names (round-3 split 2026-11-09: a subset is now spread over several plans of at most 8 modules each): a module that the partition now places in the item's subset but that no plan names is NOT added here; it is reported, and the finishing item of `x05v02` converts it; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, create directory `mkdir -p .aw/state/59aiyh/` and re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03, carried with the same id into Order 172, `y3uowx`, by the round-3 split) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 25, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: kept batch items

- [ ] E-04 (kept from this plan's E-04, batch subset G2b, round-3 split 2026-11-09: its first 4 of the 8 modules this plan keeps; the other 7 modules of G2b moved to the chunk plans named in F-41) Batch G2b, 4 of its 15 modules (the other check, production, decision-ref, citation, severity and suppression tests (`test_check*` except `test_check_engine*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`)): `tests/test_production_correction_turn.py`, `tests/test_production_fix_it.py`, `tests/test_production_prompt_writing_standard.py`, `tests/test_production_resume_handoff.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_production_correction_turn` 50, `test_production_fix_it` 40, `test_production_prompt_writing_standard` 7, `test_production_resume_handoff` 53. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G2b-x05v02-04` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_production_correction_turn.py`: `_write_backlog_item`, `_write_spec`; `tests/test_production_fix_it.py`: `_write_review_plan`; `tests/test_production_resume_handoff.py`: `_write_backlog_item`, `_write_spec`); a surviving helper is listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G2b-x05v02-04` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

- [ ] E-07 (kept from this plan's E-04, batch subset G2b, round-3 split 2026-11-09: its second 4 of the 8 modules this plan keeps; the other 7 modules of G2b moved to the chunk plans named in F-41) Batch G2b, 4 of its 15 modules (the other check, production, decision-ref, citation, severity and suppression tests (`test_check*` except `test_check_engine*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`)): `tests/test_production_set_check.py`, `tests/test_severity_truth_surfaces.py`, `tests/test_source_citation_scan.py`, `tests/test_suppress_narrowing.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_production_set_check` 45, `test_severity_truth_surfaces` 1, `test_source_citation_scan` 1, `test_suppress_narrowing` 1. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G2b-x05v02-07` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_production_set_check.py`: `_write_backlog_item`, `_write_spec`); a surviving helper is listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G2b-x05v02-07` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: pending

### Task group 2: finish

- [ ] E-06 Finish this part: (1) Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), re-derive the F-03 first-match partition for subsets G1a, G1b, G2a, G2b over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and compare it with the union of the module lists in F-41 (the chunk plans' items and this plan's E-04 and E-07); convert every module that the partition places in these subsets but that no list names under the batch rule with `<batch>` = `x05v02-late` (if there are more than 8, stop and report them for re-splitting); (2) run the batch rule's step-2 command once over `$(cat .aw/state/59aiyh/G2b-x05v02-04-files.txt .aw/state/59aiyh/G2b-x05v02-07-files.txt)` into `.aw/state/59aiyh/x05v02-union-after.txt` and confirm it equals the sorted concatenation of the two items' `-before.txt` lists; (3) run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit x05v02 -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The cross-subset full-suite comparison stays in `59aiyh` E-12, because the chunk plans' `-before.txt` lists live in their own lane worktrees.)
  - Depends on: E-04, E-07
  - Expected outcome: the partition comparison lists every late module (or none) and each one converted; the union comparison is empty; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
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
| G1a | backlog tests (`test_backlog*`) | 17 | 738 | 7 |
| G1b | release and release-gate tests (`test_release*`, `test_releases*`, `test_graduat*`, `test_gate_*`, `test_blocks_release*`, `test_handoff*`, `test_from_backlog*`, `test_live_bug*`, `test_*close*`, `test_carrier*`, `test_durable_carrier*`) | 22 | 830 | 3 |
| G2a | check-engine tests (`test_check_engine*`) | 8 | 702 | 2 |
| G2b | other check, production, decision-ref, citation, severity and suppression tests (`test_check*` except `test_check_engine*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`) | 15 | 407 | 11 |

F-41 (round-3 split 2026-11-09, research `nj8zdp` guidance; module basenames under `tests/`, each `.py`): where each of this plan's 62 modules now lives. Every module is in exactly one row; the union is the module set of the 2026-11-07 split, checked by script.

| Plan | Subset | Count | Modules |
|---|---|---|---|
| `id2pdx` (Order 175) | G1a | 8 | `test_backlog_already_complete`, `test_backlog_close_evidence_plan_disposition`, `test_backlog_close_host_label`, `test_backlog_descriptive_safety`, `test_backlog_duplicate_guard`, `test_backlog_gate_follows_status`, `test_backlog_handoff_close`, `test_backlog_history_dedup_parity` |
| `2fn0vd` (Order 176) | G1a | 8 | `test_backlog_history_empty_rule`, `test_backlog_metadata_duplicate_and_gate_summary`, `test_backlog_new_gate_vocabulary`, `test_backlog_positional_close_gate`, `test_backlog_production`, `test_backlog`, `test_backlog_set_adapter`, `test_backlog_transition_authority` |
| `isj48z` (Order 177) | G1a | 1 | `test_backlog_transition_gate` |
| `isj48z` (Order 177) | G1b | 7 | `test_release_gate_one_way_mismatch`, `test_release_readiness`, `test_releases_cli`, `test_release_sentinel_succession`, `test_releases_line_writers`, `test_releases`, `test_releases_sibling_line_writers_bounding` |
| `dg43sc` (Order 178) | G1b | 8 | `test_blocks_release_reader_bounding`, `test_carrier_detail_descriptive_bound`, `test_carrier_reverse_lookup`, `test_carrier_ungated_rule`, `test_durable_carrier_shared_predicate`, `test_from_backlog_cardinality`, `test_gate_answer_wiring`, `test_gate_drop_audit` |
| `wirc2e` (Order 179) | G1b | 7 | `test_gate_pair_validation_parity`, `test_gate_ref_resolution`, `test_graduated_closable_warning`, `test_graduation_forward_links`, `test_handoff_ready_gate`, `test_orchestrator_retire_closes_backlog`, `test_runner_backlog_close_behavior` |
| `wirc2e` (Order 179) | G2a | 1 | `test_check_engine_from_spec_missing` |
| `872zd9` (Order 180) | G2a | 7 | `test_check_engine_metadata_region`, `test_check_engine_plan_date_filename`, `test_check_engine`, `test_check_engine_release_gate`, `test_check_engine_spec_criteria`, `test_check_engine_status_meta`, `test_check_engine_test_citation` |
| `zl2pki` (Order 181) | G2b | 7 | `test_check_ci_local_parity`, `test_check_finding_path_relativity`, `test_check_recovery_fidelity`, `test_check_severity_tally`, `test_decision_ref_resolution`, `test_production_baseline_same_commit`, `test_production_checks_trace` |
| this plan, E-04 | G2b | 4 | `test_production_correction_turn`, `test_production_fix_it`, `test_production_prompt_writing_standard`, `test_production_resume_handoff` |
| this plan, E-07 | G2b | 4 | `test_production_set_check`, `test_severity_truth_surfaces`, `test_source_citation_scan`, `test_suppress_narrowing` |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E04["1. Convert batch G2b-x05v02-04 (E-04)<br/>tests/test_production_correction_turn.py, tests/test_production_fix_it.py, tests/test_production_prompt_writing_standard.py, tests/test_production_resume_handoff.py"]
    E07["2. Convert batch G2b-x05v02-07 (E-07)<br/>tests/test_production_set_check.py, tests/test_severity_truth_surfaces.py, tests/test_source_citation_scan.py, tests/test_suppress_narrowing.py"]
    E06["3. Finish, catch late modules & commit (E-06)<br/>Late partition catch-up, union diff, core gate, aw sanitize, aw commit"]

    E04 --> E06
    E07 --> E06
```

1. Convert the 8 kept modules of G2b under the batch rule (E-04, E-07), each by the codemod plus its census-counted refusals.
2. Catch late partition modules, re-run the union, the core gate, commit (E-06).

## Deferred / out of scope (with reason)

- Moved to id2pdx (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subset G1a (items E-01; F-41 names each module).
  - Carrier: id2pdx
- Moved to 2fn0vd (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subset G1a (items E-01; F-41 names each module).
  - Carrier: 2fn0vd
- Moved to isj48z (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subsets G1a, G1b (items E-01, E-02; F-41 names each module).
  - Carrier: isj48z
- Moved to dg43sc (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subset G1b (items E-02; F-41 names each module).
  - Carrier: dg43sc
- Moved to wirc2e (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subsets G1b, G2a (items E-02, E-03; F-41 names each module).
  - Carrier: wirc2e
- Moved to 872zd9 (round-3 split 2026-11-09 per research nj8zdp guidance): 7 modules of subset G2a (items E-03; F-41 names each module).
  - Carrier: 872zd9
- Moved to zl2pki (round-3 split 2026-11-09 per research nj8zdp guidance): 7 modules of subset G2b (items E-04; F-41 names each module).
  - Carrier: zl2pki
- Batch subset G3a (the setter, scaffold and authoring tests, carried from `59aiyh` E-05): Moved to 1upea0 (restructuring 2026-11-08 per maintainer decision "Codemod first, then small runs"; at most 4 batch items per plan).
  - Carrier: 1upea0
- The fixture codemod and its census (F-30, F-31).
  - Carrier: 653ndz
- The builder, its tests, the baselines and the tracked fixtures.
  - Carrier: 9rgn2w
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-37-9rgn2w-add-the-shared-test-record-builder-and-convert-the-tracked-r.ipd.md
- The remaining subsets, the switch-point proof, the F-06 census and the full-suite comparison.
  - Carrier: 59aiyh
- Adding `RECORD_FORMAT = "log"` and converting setter-byte assertions (cutover commit).
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No production module changes; every work Scope-Paths entry is a module named in E-04 or E-07.
- Under-scope: none known. Size after the round-3 split: 3 E-items (two batch items of 4 modules each and the finish), 8 work Scope-Paths. The late-module catch-up in E-06 may touch a module outside Scope-Paths; it is justified at finalize (`--scope-reason`).

## Required tests / validation

Each subset is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, unchanged assertions, the same outcomes. Commands: the batch rule's command per subset, the bare core gate `python3 -m pytest`, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` section 6 and section 7 step 6.

## Open questions

### OQ-01: Can the subsets of this part run in any order?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. The kept items and the chunk plans (F-41) are disjoint module lists, each needs only the builder (`9rgn2w`) and the codemod (`653ndz`), and none edits `tests/support.py` (that is `59aiyh` E-09). This plan depends on its chunk plans only so that E-06's late-module catch-up sees their conversions. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-04 validates E-04
  - Required evidence: paste `.aw/state/59aiyh/G2b-x05v02-04-files.txt` and the empty `diff .aw/state/59aiyh/G2b-x05v02-04-before.txt .aw/state/59aiyh/G2b-x05v02-04-after.txt`; then, for each of `tests/test_production_correction_turn.py`, `tests/test_production_fix_it.py`, `tests/test_production_prompt_writing_standard.py`, `tests/test_production_resume_handoff.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G2b-x05v02-04-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `.aw/state/59aiyh/G2b-x05v02-07-files.txt` and the empty `diff .aw/state/59aiyh/G2b-x05v02-07-before.txt .aw/state/59aiyh/G2b-x05v02-07-after.txt`; then, for each of `tests/test_production_set_check.py`, `tests/test_severity_truth_surfaces.py`, `tests/test_source_citation_scan.py`, `tests/test_suppress_narrowing.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G2b-x05v02-07-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the re-derived partition for G1a, G1b, G2a, G2b beside the F-41 union (a `diff` of the two sorted lists), each late module with its own before/after outcome `diff` (empty) and codemod summary, or the line `no late modules`; the `diff` of the sorted concatenation of the two items' `-before.txt` lists against `.aw/state/59aiyh/x05v02-union-after.txt` (empty); the bare `python3 -m pytest` summary line and wall time; the `aw sanitize --agent` result with zero `fail`; and every `aw commit x05v02` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `id2pdx`, `2fn0vd`, `isj48z`, `dg43sc`, `wirc2e`, `872zd9`, `zl2pki` are executed. OQ-01 is resolved.

Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or required builder symbols from `9rgn2w` or codemod from `653ndz` are absent, stop and report rather than proceeding. Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a subset cannot keep its outcome list identical without a production change, stop that subset and report the missing capability rather than changing production code or an assertion.

Honesty rule: run the batch comparisons and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit x05v02 -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize x05v02` itself.
