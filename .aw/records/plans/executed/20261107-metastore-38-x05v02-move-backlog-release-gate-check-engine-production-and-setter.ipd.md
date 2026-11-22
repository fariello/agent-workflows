# IPD: Move backlog, release-gate, check-engine, production and setter test data onto the record builder

- Date: 2026-11-07
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. `59aiyh` (Order 10) carried the whole migration in seven batch items of 22 to 69 modules each, each hiding hundreds of edits. Measured 2026-11-07 at `ac76110f4`: this part's 62 test modules carry 2677 F-01 legacy lines and 23 private record-building helpers. Restructured 2026-11-08: each batch item runs the Order-49 codemod (`653ndz`) and hand-converts only the refusals its census (`653ndz` F-31) counts, so no item hides hundreds of hand edits. Part of the split of `59aiyh`; it uses the builder of Order 37 (`9rgn2w`).
- Scope: FINISHING PART after the round-3 split (2026-11-09, research `nj8zdp` guidance): 8 modules of subset G2b in two items of 4 (E-04, E-07) and the finishing item E-06, which also converts any module the partition now places in subsets G1a, G1b, G2a, G2b that no plan names. The other modules of subsets G1a, G1b, G2a, G2b moved to the chunk plans `id2pdx`, `2fn0vd`, `isj48z`, `dg43sc`, `wirc2e`, `872zd9`, `zl2pki` (F-41). Before the round-3 split: Batch subsets G1a, G1b, G2a, G2b of `59aiyh`'s batch items, each a named list of at most 25 modules, plus a finishing item. Each subset runs the Order-49 codemod (`653ndz`) and hand-converts only its census-counted refusals. Every subset applies the batch rule below (the `59aiyh` batch rule restructured for the codemod). EXCLUDES: the builder and fixtures (Order 37, `9rgn2w`); every other subset (Orders 38 to 40 and `59aiyh`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_production_correction_turn.py, tests/test_production_fix_it.py, tests/test_production_prompt_writing_standard.py, tests/test_production_resume_handoff.py, tests/test_production_set_check.py, tests/test_severity_truth_surfaces.py, tests/test_source_citation_scan.py, tests/test_suppress_narrowing.py, .aw/records/plans/pending/20261107-metastore-38-x05v02-move-backlog-release-gate-check-engine-production-and-setter.ipd.md
- Scope-Exceeded: tests/test_check_meta.py (E-06 late-module catch-up: added after round-3 split by a5ijjx and placed in G2b by the F-03 first-match partition)
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45, executed:id2pdx, executed:2fn0vd, executed:isj48z, executed:dg43sc, executed:wirc2e, executed:872zd9, executed:zl2pki
- Status: executed
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

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 executed (aw agy run model=Gemini-4-Neon-High): aw agy run self-finalize: x05v02 verified (set metastore, attempt 1). [Scope reconciliation - out-of-scope tests/test_check_meta.py: E-06 late-module catch-up: added after round-3 split by a5ijjx and placed in G2b by the F-03 first-match partition]
- 2026-11-22 cap-update (maintainer decision): raised Batch rule step 4 hand-refusal cap from 25 to 150 and late-module stop threshold from 8 to 20 (matching 6edbb2c83 rationale; raw site count over-counts list elements and .replace() pairs).
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
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 150, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: kept batch items

- [x] E-04 (kept from this plan's E-04, batch subset G2b, round-3 split 2026-11-09: its first 4 of the 8 modules this plan keeps; the other 7 modules of G2b moved to the chunk plans named in F-41) Batch G2b, 4 of its 15 modules (the other check, production, decision-ref, citation, severity and suppression tests (`test_check*` except `test_check_engine*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`)): `tests/test_production_correction_turn.py`, `tests/test_production_fix_it.py`, `tests/test_production_prompt_writing_standard.py`, `tests/test_production_resume_handoff.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_production_correction_turn` 50, `test_production_fix_it` 40, `test_production_prompt_writing_standard` 7, `test_production_resume_handoff` 53. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G2b-x05v02-04` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 150, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_production_correction_turn.py`: `_write_backlog_item`, `_write_spec`; `tests/test_production_fix_it.py`: `_write_review_plan`; `tests/test_production_resume_handoff.py`: `_write_backlog_item`, `_write_spec`); a surviving helper is listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G2b-x05v02-04` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 150) pasted.
  - Execution state: performed

- [x] E-07 (kept from this plan's E-04, batch subset G2b, round-3 split 2026-11-09: its second 4 of the 8 modules this plan keeps; the other 7 modules of G2b moved to the chunk plans named in F-41) Batch G2b, 4 of its 15 modules (the other check, production, decision-ref, citation, severity and suppression tests (`test_check*` except `test_check_engine*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`)): `tests/test_production_set_check.py`, `tests/test_severity_truth_surfaces.py`, `tests/test_source_citation_scan.py`, `tests/test_suppress_narrowing.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_production_set_check` 45, `test_severity_truth_surfaces` 1, `test_source_citation_scan` 1, `test_suppress_narrowing` 1. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G2b-x05v02-07` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 150, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_production_set_check.py`: `_write_backlog_item`, `_write_spec`); a surviving helper is listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G2b-x05v02-07` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 150) pasted.
  - Execution state: performed

### Task group 2: finish

- [x] E-06 Finish this part: (1) Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), re-derive the F-03 first-match partition for subsets G1a, G1b, G2a, G2b over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and compare it with the union of the module lists in F-41 (the chunk plans' items and this plan's E-04 and E-07); convert every module that the partition places in these subsets but that no list names under the batch rule with `<batch>` = `x05v02-late` (if there are more than 20, stop and report them for re-splitting); (2) run the batch rule's step-2 command once over `$(cat .aw/state/59aiyh/G2b-x05v02-04-files.txt .aw/state/59aiyh/G2b-x05v02-07-files.txt)` into `.aw/state/59aiyh/x05v02-union-after.txt` and confirm it equals the sorted concatenation of the two items' `-before.txt` lists; (3) run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit x05v02 -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The cross-subset full-suite comparison stays in `59aiyh` E-12, because the chunk plans' `-before.txt` lists live in their own lane worktrees.)
  - Depends on: E-04, E-07
  - Expected outcome: the partition comparison lists every late module (or none) and each one converted; the union comparison is empty; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: performed

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
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-175-id2pdx-move-backlog-release-gate-and-check-test-data-chunk-1-of-7-o.ipd.md
- Moved to 2fn0vd (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subset G1a (items E-01; F-41 names each module).
  - Carrier: 2fn0vd
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-176-2fn0vd-move-backlog-release-gate-and-check-test-data-chunk-2-of-7-o.ipd.md
- Moved to isj48z (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subsets G1a, G1b (items E-01, E-02; F-41 names each module).
  - Carrier: isj48z
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-177-isj48z-move-backlog-release-gate-and-check-test-data-chunk-3-of-7-o.ipd.md
- Moved to dg43sc (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subset G1b (items E-02; F-41 names each module).
  - Carrier: dg43sc
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-178-dg43sc-move-backlog-release-gate-and-check-test-data-chunk-4-of-7-o.ipd.md
- Moved to wirc2e (round-3 split 2026-11-09 per research nj8zdp guidance): 8 modules of subsets G1b, G2a (items E-02, E-03; F-41 names each module).
  - Carrier: wirc2e
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-179-wirc2e-move-backlog-release-gate-and-check-test-data-chunk-5-of-7-o.ipd.md
- Moved to 872zd9 (round-3 split 2026-11-09 per research nj8zdp guidance): 7 modules of subset G2a (items E-03; F-41 names each module).
  - Carrier: 872zd9
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-180-872zd9-move-backlog-release-gate-and-check-test-data-chunk-6-of-7-o.ipd.md
- Moved to zl2pki (round-3 split 2026-11-09 per research nj8zdp guidance): 7 modules of subset G2b (items E-04; F-41 names each module).
  - Carrier: zl2pki
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-181-zl2pki-move-backlog-release-gate-and-check-test-data-chunk-7-of-7-o.ipd.md
- Batch subset G3a (the setter, scaffold and authoring tests, carried from `59aiyh` E-05): Moved to 1upea0 (restructuring 2026-11-08 per maintainer decision "Codemod first, then small runs"; at most 4 batch items per plan).
  - Carrier: 1upea0
- The fixture codemod and its census (F-30, F-31).
  - Carrier: 653ndz
  - Carrier-Evidence: .aw/records/plans/executed/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md
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

- [x] V-04 validates E-04
  - Required evidence: paste `.aw/state/59aiyh/G2b-x05v02-04-files.txt` and the empty `diff .aw/state/59aiyh/G2b-x05v02-04-before.txt .aw/state/59aiyh/G2b-x05v02-04-after.txt`; then, for each of `tests/test_production_correction_turn.py`, `tests/test_production_fix_it.py`, `tests/test_production_prompt_writing_standard.py`, `tests/test_production_resume_handoff.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G2b-x05v02-04-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G2b-x05v02-04-files.txt`:
      `tests/test_production_correction_turn.py`, `tests/test_production_fix_it.py`, `tests/test_production_prompt_writing_standard.py`, `tests/test_production_resume_handoff.py`.
    - `diff -u .aw/state/59aiyh/G2b-x05v02-04-before.txt .aw/state/59aiyh/G2b-x05v02-04-after.txt`: empty output, exit code 0 (33 `PASSED` outcomes before and after, verified post-format).
    - `tests/test_production_correction_turn.py`:
      - F-01 `rg -c`: 50 before -> 5 after.
      - Remaining 5 F-01 matches and reason classes (post-commit):
        - line 466 (`test_e02_backlog_production_fixed_on_first_correction`): `"- Status: graduated"` in `self.assertIn("- Status: graduated", bkl_files[0].read_text(encoding="utf-8"))` (`setter-byte assertion`).
        - line 592 (`test_e02_backlog_production_never_fixed_exhausted`): `"- Status: open"` in `self.assertIn("- Status: open", bkl_files[0].read_text(encoding="utf-8"))` (`setter-byte assertion`).
        - line 1157 (`test_e03_review_orchestrator_fixed_and_exhausted`): comment `# Plan on disk remains to-review and has NO - Readiness: line` (`body prose`).
        - line 1164 (`test_e03_review_orchestrator_fixed_and_exhausted`): `self.assertIn("- Status: to-review", plan_txt)` (`setter-byte assertion`).
        - line 1165 (`test_e03_review_orchestrator_fixed_and_exhausted`): `self.assertNotIn("- Readiness:", plan_txt)` (`setter-byte assertion`).
        - Summary: 4 `setter-byte assertion`, 1 `body prose`.
      - `G2b-x05v02-04-codemod.json`: sites=31, rewrites=0 (standard=0, invalid-input=0), refusals=31 (`dynamic-construction`=12 `hand`, `unsupported-shape`=14 `hand`, `setter-byte assertion`=4 `legacy-kept`, `body prose`=1 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True (0 rewrites applied).
      - `653ndz` F-30 row: `| tests/test_production_correction_turn.py | G2b | x05v02 | 31 | 0 | 0 | 12 | 14 | 0 | 0 | 0 | 4 | 1 | 26 | 5 |`.
    - `tests/test_production_fix_it.py`:
      - F-01 `rg -c`: 40 before -> 0 after (no remaining matches).
      - `G2b-x05v02-04-codemod.json`: sites=20, rewrites=0 (standard=0, invalid-input=0), refusals=20 (`dynamic-construction`=8 `hand`, `unsupported-shape`=10 `hand`, `not-equivalent`=1 `hand`, `body prose`=1 `legacy-kept`), before_hash=`ec81c8513cc5d87c0876b13b48f2b2102b00d1f28f37106a0435c3dd147c877d`, after_hash=`ec81c8513cc5d87c0876b13b48f2b2102b00d1f28f37106a0435c3dd147c877d`, equivalent=True (1 planned rewrite reverted by bisection as `not-equivalent`).
      - `653ndz` F-30 row: `| tests/test_production_fix_it.py | G2b | x05v02 | 20 | 1 | 0 | 8 | 10 | 0 | 0 | 0 | 0 | 1 | 18 | 1 |`.
    - `tests/test_production_prompt_writing_standard.py`:
      - F-01 `rg -c`: 7 before -> 0 after (no remaining matches).
      - `G2b-x05v02-04-codemod.json`: sites=7, rewrites=7 (standard=7, invalid-input=0), refusals=0, before_hash=`e86acd22768da509d8bb6ccc3b1462f67db72bca0aaa7a69ef0e2389eeda016d`, after_hash=`e86acd22768da509d8bb6ccc3b1462f67db72bca0aaa7a69ef0e2389eeda016d`, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_production_prompt_writing_standard.py | G2b | x05v02 | 7 | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |`.
    - `tests/test_production_resume_handoff.py`:
      - F-01 `rg -c`: 53 before -> 7 after.
      - Remaining 7 F-01 matches and reason classes (post-commit):
        - line 88 (`_write_child_plan`): comment `# rdyreq (fhinri, IPD-M113): reviewed/ready-to-execute requires - Readiness:, attested by a` (`body prose`).
        - line 553 (`test_prompt_builders_continue_section_and_findings`): `".aw/records/plans/pending/20261004-tstset-00-orc001-test-orch.ipd.md (- Status: to-review)"` asserted in rendered prompt `prompt_bkl_cont` (`displayed-output assertion`; codemod labeled `setter-byte assertion` `legacy-kept`).
        - line 557 (`test_prompt_builders_continue_section_and_findings`): `".aw/records/plans/pending/20261004-tstset-01-chd001-test-child.ipd.md (- Status: draft)"` asserted in rendered prompt `prompt_bkl_cont` (`displayed-output assertion`; codemod labeled `setter-byte assertion` `legacy-kept`).
        - line 936 (`test_case_i_backlog_resumes_unfinished_handoff`): `self.assertIn("- Status: graduated", bkl_txt)` (`setter-byte assertion`).
        - line 942 (`test_case_i_backlog_resumes_unfinished_handoff`): comment `# - Graduated-To: set401` (`body prose`).
        - line 943 (`test_case_i_backlog_resumes_unfinished_handoff`): `self.assertIn("- Graduated-To: set401", bkl_txt)` (`setter-byte assertion`).
        - line 1154 (`test_case_iii_spec_resumes_unfinished_handoff`): `self.assertIn("- Status: implementing", spec_txt)` (`setter-byte assertion`).
        - Summary: 3 `setter-byte assertion`, 2 `displayed-output assertion`, 2 `body prose`.
      - `G2b-x05v02-04-codemod.json`: sites=35, rewrites=0 (standard=0, invalid-input=0), refusals=35 (`dynamic-construction`=12 `hand`, `unsupported-shape`=17 `hand`, `setter-byte assertion`=5 `legacy-kept`, `body prose`=1 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True (0 rewrites applied).
      - `653ndz` F-30 row: `| tests/test_production_resume_handoff.py | G2b | x05v02 | 35 | 0 | 0 | 12 | 17 | 0 | 0 | 0 | 5 | 1 | 29 | 6 |`.
    - Hand count: 74 (73 static in `653ndz` F-30: 26 + 18 + 0 + 29, plus 1 apply-time `not-equivalent` in `tests/test_production_fix_it.py`; <= 150 cap). Every hand-converted site (original pre-codemod lines):
      - `tests/test_production_correction_turn.py` (26 sites):
        1. L63 (`_write_backlog_item`, `dynamic-construction`)
        2. L64-73 (`_write_backlog_item`, `dynamic-construction`)
        3. L92 (`_write_spec`, `dynamic-construction`)
        4. L93-101 (`_write_spec`, `dynamic-construction`)
        5. L123 (`_write_child_plan`, `dynamic-construction`)
        6. L124 (`_write_child_plan`, `dynamic-construction`)
        7. L125 (`_write_child_plan`, `dynamic-construction`)
        8. L127-191 (`_write_child_plan`, `dynamic-construction`)
        9. L231 (`_write_orchestrator_plan`, `dynamic-construction`)
        10. L232 (`_write_orchestrator_plan`, `dynamic-construction`)
        11. L233 (`_write_orchestrator_plan`, `dynamic-construction`)
        12. L234 (`_write_orchestrator_plan`, `dynamic-construction`)
        13. L239 (`_write_orchestrator_plan`, `unsupported-shape`)
        14. L240 (`_write_orchestrator_plan`, `unsupported-shape`)
        15. L241 (`_write_orchestrator_plan`, `unsupported-shape`)
        16. L242 (`_write_orchestrator_plan`, `unsupported-shape`)
        17. L243 (`_write_orchestrator_plan`, `unsupported-shape`)
        18. L244 (`_write_orchestrator_plan`, `unsupported-shape`)
        19. L246 (`_write_orchestrator_plan`, `unsupported-shape`)
        20. L251 (`_write_orchestrator_plan`, `unsupported-shape`)
        21. L252 (`_write_orchestrator_plan`, `unsupported-shape`)
        22. L254 (`_write_orchestrator_plan`, `unsupported-shape`)
        23. L991 (`test_e03_review_orchestrator_fixed_and_exhausted`, `unsupported-shape`)
        24. L992 (`test_e03_review_orchestrator_fixed_and_exhausted`, `unsupported-shape`)
        25. L1109 (`test_e03_review_orchestrator_fixed_and_exhausted`, `unsupported-shape`)
        26. L1110 (`test_e03_review_orchestrator_fixed_and_exhausted`, `unsupported-shape`)
      - `tests/test_production_fix_it.py` (19 sites):
        27. L77 (`_write_child_plan`, `dynamic-construction`)
        28. L78 (`_write_child_plan`, `dynamic-construction`)
        29. L79 (`_write_child_plan`, `dynamic-construction`)
        30. L81-146 (`_write_child_plan`, `dynamic-construction`)
        31. L186 (`_write_orchestrator_plan`, `dynamic-construction`)
        32. L187 (`_write_orchestrator_plan`, `dynamic-construction`)
        33. L188 (`_write_orchestrator_plan`, `dynamic-construction`)
        34. L189 (`_write_orchestrator_plan`, `dynamic-construction`)
        35. L194 (`_write_orchestrator_plan`, `unsupported-shape`)
        36. L195 (`_write_orchestrator_plan`, `unsupported-shape`)
        37. L196 (`_write_orchestrator_plan`, `unsupported-shape`)
        38. L197 (`_write_orchestrator_plan`, `unsupported-shape`)
        39. L198 (`_write_orchestrator_plan`, `unsupported-shape`)
        40. L199 (`_write_orchestrator_plan`, `unsupported-shape`)
        41. L201 (`_write_orchestrator_plan`, `unsupported-shape`)
        42. L206 (`_write_orchestrator_plan`, `unsupported-shape`)
        43. L207 (`_write_orchestrator_plan`, `unsupported-shape`)
        44. L209 (`_write_orchestrator_plan`, `unsupported-shape`)
        45. L278-343 (`_write_review_plan`, `not-equivalent`; deleted and inlined as `RecordBuilder(repo).plan(...)` with non-`TODO` `Concern`/`Scope` via `raw_fields`)
      - `tests/test_production_resume_handoff.py` (29 sites):
        46. L87 (`_write_backlog_item`, `dynamic-construction`)
        47. L88-97 (`_write_backlog_item`, `dynamic-construction`)
        48. L116 (`_write_spec`, `dynamic-construction`)
        49. L117-130 (`_write_spec`, `dynamic-construction`)
        50. L153 (`_write_child_plan`, `dynamic-construction`)
        51. L154 (`_write_child_plan`, `dynamic-construction`)
        52. L155 (`_write_child_plan`, `dynamic-construction`)
        53. L156 (`_write_child_plan`, `dynamic-construction`)
        54. L161 (`_write_child_plan`, `unsupported-shape`)
        55. L164-228 (`_write_child_plan`, `dynamic-construction`)
        56. L269 (`_write_orchestrator_plan`, `dynamic-construction`)
        57. L270 (`_write_orchestrator_plan`, `dynamic-construction`)
        58. L271 (`_write_orchestrator_plan`, `dynamic-construction`)
        59. L276 (`_write_orchestrator_plan`, `unsupported-shape`)
        60. L277 (`_write_orchestrator_plan`, `unsupported-shape`)
        61. L278 (`_write_orchestrator_plan`, `unsupported-shape`)
        62. L279 (`_write_orchestrator_plan`, `unsupported-shape`)
        63. L280 (`_write_orchestrator_plan`, `unsupported-shape`)
        64. L281 (`_write_orchestrator_plan`, `unsupported-shape`)
        65. L284 (`_write_orchestrator_plan`, `unsupported-shape`)
        66. L287 (`_write_orchestrator_plan`, `unsupported-shape`)
        67. L291 (`_write_orchestrator_plan`, `unsupported-shape`)
        68. L296 (`_write_orchestrator_plan`, `unsupported-shape`)
        69. L297 (`_write_orchestrator_plan`, `unsupported-shape`)
        70. L299 (`_write_orchestrator_plan`, `unsupported-shape`)
        71. L915 (`test_case_i_backlog_resumes_unfinished_handoff`, `"- Status: draft"`, `unsupported-shape`)
        72. L915 (`test_case_i_backlog_resumes_unfinished_handoff`, `"- Status: to-review"`, `unsupported-shape`)
        73. L1111 (`test_case_iii_spec_resumes_unfinished_handoff`, `"- Status: draft"`, `unsupported-shape`)
        74. L1111 (`test_case_iii_spec_resumes_unfinished_handoff`, `"- Status: to-review"`, `unsupported-shape`)
    - E-09 helper census (`rg -n -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*"`):
      - Before = 5 (`tests/test_production_correction_turn.py`: `def _write_backlog_item` L45, `def _write_spec` L78; `tests/test_production_fix_it.py`: `def _write_review_plan` L268; `tests/test_production_resume_handoff.py`: `def _write_backlog_item` L69, `def _write_spec` L102).
      - After = 0 (`(none)`).
      - Deleted helpers (5): `_write_backlog_item` and `_write_spec` in `tests/test_production_correction_turn.py` (callers in both `test_production_correction_turn.py` and `test_production_fix_it.py` replaced by direct `RecordBuilder(repo).backlog(...)` / `.spec(...)` calls), `_write_review_plan` in `tests/test_production_fix_it.py` (single caller replaced by direct `RecordBuilder(repo).plan(...)` call), and `_write_backlog_item` and `_write_spec` in `tests/test_production_resume_handoff.py` (all callers replaced by direct `RecordBuilder(repo).backlog(...)` / `.spec(...)` calls).
      - Surviving helpers: none.
    - Post-conversion idempotency check (`python3 tools/fixture_codemod.py --dry-run`): 0 rewrites, 0 `hand` refusals across all 4 modules.
  - Result: pass

- [x] V-07 validates E-07
  - Required evidence: paste `.aw/state/59aiyh/G2b-x05v02-07-files.txt` and the empty `diff .aw/state/59aiyh/G2b-x05v02-07-before.txt .aw/state/59aiyh/G2b-x05v02-07-after.txt`; then, for each of `tests/test_production_set_check.py`, `tests/test_severity_truth_surfaces.py`, `tests/test_source_citation_scan.py`, `tests/test_suppress_narrowing.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G2b-x05v02-07-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G2b-x05v02-07-files.txt`:
      `tests/test_production_set_check.py`, `tests/test_severity_truth_surfaces.py`, `tests/test_source_citation_scan.py`, `tests/test_suppress_narrowing.py`.
    - `diff -u .aw/state/59aiyh/G2b-x05v02-07-before.txt .aw/state/59aiyh/G2b-x05v02-07-after.txt`: empty output, exit code 0 (30 `PASSED` outcomes before and after, verified post-format).
    - `tests/test_production_set_check.py`:
      - F-01 `rg -c`: 45 before -> 5 after.
      - Remaining 5 F-01 matches and reason classes (post-commit):
        - line 767 (`test_backlog_production_draft_child_fail_gate`): `self.assertIn("- Status: open", bkl_txt)` (`setter-byte assertion`).
        - line 880 (`test_backlog_production_ready_set_graduated`): `self.assertIn("- Status: graduated", bkl_txt)` (`setter-byte assertion`).
        - line 1019 (`test_spec_production_unready_child_fail_gate`): `self.assertIn("- Status: approved", spec_txt)` (`setter-byte assertion`).
        - line 1131 (`test_spec_production_ready_set_implementing`): `self.assertIn("- Status: implementing", spec_txt)` (`setter-byte assertion`).
        - line 1231 (`test_backlog_production_could_not_ask`): `self.assertIn("- Status: open", bkl_txt)` (`setter-byte assertion`).
        - Summary: 5 `setter-byte assertion` (`legacy-kept`).
      - `G2b-x05v02-07-codemod.json`: sites=27, rewrites=0 (standard=0, invalid-input=0), refusals=27 (`dynamic-construction`=11 `hand`, `unsupported-shape`=10 `hand`, `setter-byte assertion`=5 `legacy-kept`, `body prose`=1 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True (0 rewrites applied).
      - `653ndz` F-30 row: `| tests/test_production_set_check.py | G2b | x05v02 | 27 | 0 | 0 | 11 | 10 | 0 | 0 | 0 | 5 | 1 | 21 | 6 |`.
    - `tests/test_severity_truth_surfaces.py`:
      - F-01 `rg -c`: 1 before -> 0 after (no remaining matches).
      - `G2b-x05v02-07-codemod.json`: sites=2, rewrites=2 (standard=2, invalid-input=0), refusals=0, before_hash=`818e7734f9a06bda3b63b43199b8a8f54979cb9af37117e55001b0f32c8b5168`, after_hash=`818e7734f9a06bda3b63b43199b8a8f54979cb9af37117e55001b0f32c8b5168`, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_severity_truth_surfaces.py | G2b | x05v02 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |`.
    - `tests/test_source_citation_scan.py`:
      - F-01 `rg -c`: 1 before -> 0 after (no remaining matches).
      - `G2b-x05v02-07-codemod.json`: sites=1, rewrites=1 (standard=1, invalid-input=0), refusals=0, before_hash=`d002655715a2e5cbbacc8ea1d934580822574e75f6ee222937b9e3b0dd44c118`, after_hash=`d002655715a2e5cbbacc8ea1d934580822574e75f6ee222937b9e3b0dd44c118`, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_source_citation_scan.py | G2b | x05v02 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |`.
    - `tests/test_suppress_narrowing.py`:
      - F-01 `rg -c`: 1 before -> 0 after (no remaining matches).
      - `G2b-x05v02-07-codemod.json`: sites=1, rewrites=1 (standard=1, invalid-input=0), refusals=0, before_hash=`ce609ce90bacec8a8217e7fd8a9822e269d50eae71f0358e0979ad44bcfc721a`, after_hash=`ce609ce90bacec8a8217e7fd8a9822e269d50eae71f0358e0979ad44bcfc721a`, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_suppress_narrowing.py | G2b | x05v02 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |`.
    - Hand count: 21 (21 static in `653ndz` F-30: 21 + 0 + 0 + 0, plus 0 apply-time `not-equivalent`; <= 150 cap). Every hand-converted site (original pre-codemod lines):
      - `tests/test_production_set_check.py` (21 sites):
        1. L68 (`_write_backlog_item`, `dynamic-construction`)
        2. L69-78 (`_write_backlog_item`, `dynamic-construction`)
        3. L97 (`_write_spec`, `dynamic-construction`)
        4. L98-111 (`_write_spec`, `dynamic-construction`)
        5. L133 (`_write_child_plan`, `dynamic-construction`)
        6. L134 (`_write_child_plan`, `dynamic-construction`)
        7. L135 (`_write_child_plan`, `dynamic-construction`)
        8. L137-201 (`_write_child_plan`, `dynamic-construction`)
        9. L241 (`_write_orchestrator_plan`, `dynamic-construction`)
        10. L242 (`_write_orchestrator_plan`, `dynamic-construction`)
        11. L243 (`_write_orchestrator_plan`, `dynamic-construction`)
        12. L248 (`_write_orchestrator_plan`, `unsupported-shape`)
        13. L249 (`_write_orchestrator_plan`, `unsupported-shape`)
        14. L250 (`_write_orchestrator_plan`, `unsupported-shape`)
        15. L251 (`_write_orchestrator_plan`, `unsupported-shape`)
        16. L252 (`_write_orchestrator_plan`, `unsupported-shape`)
        17. L253 (`_write_orchestrator_plan`, `unsupported-shape`)
        18. L255 (`_write_orchestrator_plan`, `unsupported-shape`)
        19. L260 (`_write_orchestrator_plan`, `unsupported-shape`)
        20. L261 (`_write_orchestrator_plan`, `unsupported-shape`)
        21. L263 (`_write_orchestrator_plan`, `unsupported-shape`)
    - E-09 helper census (`rg -n -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*"`):
      - Before = 2 (`tests/test_production_set_check.py`: `def _write_backlog_item` L50, `def _write_spec` L83).
      - After = 0 (`(none)`).
      - Deleted helpers (2): `_write_backlog_item` and `_write_spec` in `tests/test_production_set_check.py` (all callers replaced by direct `RecordBuilder(repo).backlog(...)` / `.spec(...)` calls).
      - Surviving helpers: none.
    - Post-conversion idempotency check (`python3 tools/fixture_codemod.py --dry-run`): 0 rewrites, 0 `hand` refusals across all 4 modules.
  - Result: pass

- [x] V-06 validates E-06
  - Required evidence: paste the re-derived partition for G1a, G1b, G2a, G2b beside the F-41 union (a `diff` of the two sorted lists), each late module with its own before/after outcome `diff` (empty) and codemod summary, or the line `no late modules`; the `diff` of the sorted concatenation of the two items' `-before.txt` lists against `.aw/state/59aiyh/x05v02-union-after.txt` (empty); the bare `python3 -m pytest` summary line and wall time; the `aw sanitize --agent` result with zero `fail`; and every `aw commit x05v02` output listing only Scope-Paths.
  - Observed evidence:
    - Partition comparison (`diff -u .aw/state/59aiyh/x05v02-f41-union.txt .aw/state/59aiyh/x05v02-head-partition.txt` at starting HEAD `f8bb03e8a`; 17 `-` rows are F-41 modules already reduced to 0 F-01 lines by executed chunk plans `id2pdx`, `2fn0vd`, `isj48z`, `dg43sc`, `wirc2e`, `872zd9`, `zl2pki`; 1 `+` row is late G2b module `tests/test_check_meta.py` added post-split by `a5ijjx`):
      ```diff
      --- .aw/state/59aiyh/x05v02-f41-union.txt
      +++ .aw/state/59aiyh/x05v02-head-partition.txt
      @@ -1,12 +1,9 @@
       tests/test_backlog.py
       tests/test_backlog_already_complete.py
       tests/test_backlog_close_evidence_plan_disposition.py
      -tests/test_backlog_close_host_label.py
       tests/test_backlog_descriptive_safety.py
      -tests/test_backlog_duplicate_guard.py
       tests/test_backlog_gate_follows_status.py
       tests/test_backlog_handoff_close.py
      -tests/test_backlog_history_dedup_parity.py
       tests/test_backlog_history_empty_rule.py
       tests/test_backlog_metadata_duplicate_and_gate_summary.py
       tests/test_backlog_new_gate_vocabulary.py
      @@ -16,10 +13,6 @@
       tests/test_backlog_transition_authority.py
       tests/test_backlog_transition_gate.py
       tests/test_blocks_release_reader_bounding.py
      -tests/test_carrier_detail_descriptive_bound.py
      -tests/test_carrier_reverse_lookup.py
      -tests/test_carrier_ungated_rule.py
      -tests/test_check_ci_local_parity.py
       tests/test_check_engine.py
       tests/test_check_engine_from_spec_missing.py
       tests/test_check_engine_metadata_region.py
      @@ -28,20 +21,13 @@
       tests/test_check_engine_spec_criteria.py
       tests/test_check_engine_status_meta.py
       tests/test_check_engine_test_citation.py
      -tests/test_check_finding_path_relativity.py
      -tests/test_check_recovery_fidelity.py
      -tests/test_check_severity_tally.py
      -tests/test_decision_ref_resolution.py
      -tests/test_durable_carrier_shared_predicate.py
      +tests/test_check_meta.py
       tests/test_from_backlog_cardinality.py
       tests/test_gate_answer_wiring.py
       tests/test_gate_drop_audit.py
       tests/test_gate_pair_validation_parity.py
      -tests/test_gate_ref_resolution.py
      -tests/test_graduated_closable_warning.py
       tests/test_graduation_forward_links.py
       tests/test_handoff_ready_gate.py
      -tests/test_orchestrator_retire_closes_backlog.py
       tests/test_production_baseline_same_commit.py
       tests/test_production_checks_trace.py
       tests/test_production_correction_turn.py
      @@ -49,8 +35,6 @@
       tests/test_production_prompt_writing_standard.py
       tests/test_production_resume_handoff.py
       tests/test_production_set_check.py
      -tests/test_release_gate_one_way_mismatch.py
      -tests/test_release_readiness.py
       tests/test_release_sentinel_succession.py
       tests/test_releases.py
       tests/test_releases_cli.py
      ```
    - Late module (`<batch>` = `x05v02-late`, 1 module <= 20 late-module cap):
      - `tests/test_check_meta.py`:
        - `diff -u .aw/state/59aiyh/x05v02-late-before.txt .aw/state/59aiyh/x05v02-late-after.txt`: empty output, exit code 0 (17 `PASSED` outcomes before and after, verified post-format).
        - F-01 `rg -c`: 9 before -> 0 after (no remaining matches).
        - `x05v02-late-codemod.json`: sites=10, rewrites=7 (standard=4, invalid-input=3), refusals=3 (`dynamic-construction`=1 `hand` at L78-85 `_write_clean_plan`, `unsupported-shape`=1 `hand` at L138 walkthrough fixture, `not-equivalent`=1 `hand` at L417-418 skipped-round review fixture; 0 `legacy-kept`), before_hash=`4390dbc38731d6d92ac0018ad01840c6d1adeada156cc3dca31128a9f1ddc2f3`, after_hash=`4390dbc38731d6d92ac0018ad01840c6d1adeada156cc3dca31128a9f1ddc2f3`, equivalent=True.
        - Hand count: 3 (<= 150 cap); all 3 converted via `RecordBuilder().plan(...)` (using `raw_fields={"Ace": ..., "Model": ...}` for `test_drift_d177_facet`), `RecordBuilder().walkthrough(...)`, and `RecordBuilder().review(..., rounds=[{"number": 1}, {"number": 3}])`.
        - E-09 helper census: 0 before -> 0 after (`(none)`).
    - Union diff (`diff -u .aw/state/59aiyh/x05v02-union-before.txt .aw/state/59aiyh/x05v02-union-after.txt`): empty output, exit code 0 (63 `PASSED` outcomes across all 8 kept modules, verified post-format).
    - Bare core gate (`aw suite`, running bare `python3 -m pytest` on the core tier with 6 bounded workers, exit 0):
      `2734 passed, 1 skipped, 11 warnings in 154.19s (0:02:34)` (host 1-minute load average 9.25 on 12 CPUs; none of `x05v02`'s 9 modules appeared in top-10 slowest).
    - `aw sanitize --agent` (exit 0, zero `fail`):
      `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":7076,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw commit x05v02` output (code commit covering all 8 test `Scope-Paths` plus late G2b module `tests/test_check_meta.py` justified via `--scope-reason` per E-06 and `## Scope check`):
      `aw commit: committed 9 path(s): 8d1fd0e9d74442b51b8427eabb613c6dcde043dc` (`tests/test_check_meta.py`, `tests/test_production_correction_turn.py`, `tests/test_production_fix_it.py`, `tests/test_production_prompt_writing_standard.py`, `tests/test_production_resume_handoff.py`, `tests/test_production_set_check.py`, `tests/test_severity_truth_surfaces.py`, `tests/test_source_citation_scan.py`, `tests/test_suppress_narrowing.py`). Followed by the plan-evidence commit via `aw commit x05v02 -- .aw/records/plans/pending/20261107-metastore-38-x05v02-move-backlog-release-gate-check-engine-production-and-setter.ipd.md` (recorded in the lane execution report and outcome JSON).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45`, `id2pdx`, `2fn0vd`, `isj48z`, `dg43sc`, `wirc2e`, `872zd9`, `zl2pki` are executed. OQ-01 is resolved.

Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or required builder symbols from `9rgn2w` or codemod from `653ndz` are absent, stop and report rather than proceeding. Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a subset cannot keep its outcome list identical without a production change, stop that subset and report the missing capability rather than changing production code or an assertion.

Honesty rule: run the batch comparisons and the bare `python3 -m pytest` core gate, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit x05v02 -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize x05v02` itself.
