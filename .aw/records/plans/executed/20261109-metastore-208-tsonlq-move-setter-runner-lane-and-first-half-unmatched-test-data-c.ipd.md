# IPD: Move setter, runner-lane and first-half unmatched test data chunk 6 of 7 onto the record builder

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. Research `nj8zdp` and the maintainer's ruling ("plans that obtuse and not-too-smart agents won't mess up") set the guidance of at most 5 E-items, 8 work Scope-Paths and about 8 named units per item; `1upea0` named up to 25 modules per batch item. This part carries 7 of `1upea0`'s modules (subset G7a; 24 F-01 legacy lines at `3d0ddb845`), each item at most 4 modules, converted by the Order-49 codemod (`653ndz`) plus only its census-counted refusals.
- Scope: Chunk 6 of 7 of `1upea0` (round-3 split 2026-11-09 per research `nj8zdp` guidance): the 7 test modules named in the items and in F-40, each item one codemod run under the batch rule below, plus a finishing item. EXCLUDES: every other module of the subsets (the other chunk plans and `1upea0`); the builder (`9rgn2w`) and the codemod (`653ndz`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_authoring_coverage_guidance.py, tests/test_awcmdsurf_mutation_verbs.py, tests/test_awmigrename.py, tests/test_awphysical_tools.py, tests/test_collision_population_parity.py, tests/test_companion_record_owner_root.py, tests/test_completion.py, .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 208
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: tsonlq

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 executed (aw agy run model=Gemini-4-Neon-High): aw agy run self-finalize: tsonlq verified (set metastore, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_collision_population_parity.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): plan-review verified E/V bijection, Scope-Paths, batch rules, execution gate, and state directory initialization; findings PR-001..PR-005 fixed; marked reviewed and go-pending-approval.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 1upea0 (round 3, research nj8zdp guidance).

## Goal

Every hand-built record in the 7 test modules named below comes from `tests/record_builder.py`, written by the Order-49 codemod or, for its census-counted refusals only, by hand, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`), carried by the round-3 split into Order 170 (`j6o96i`) with the same ids; because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the modules each batch item names (round-3 split 2026-11-09: a subset is now spread over several plans of at most 8 modules each): a module that the partition now places in the item's subset but that no plan names is NOT added here; it is reported, and the finishing item of `1upea0` converts it; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, create directory `mkdir -p .aw/state/59aiyh/` and re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03, carried with the same id into Order 172, `y3uowx`, by the round-3 split) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 25, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: batch items

- [x] E-01 (carried from `1upea0` E-03, batch subset G7a; round-3 split 2026-11-09) Batch G7a, 4 of its 24 modules (the unmatched test modules, first half (basename sorts before `test_l`)): `tests/test_authoring_coverage_guidance.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_awmigrename.py`, `tests/test_awphysical_tools.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_authoring_coverage_guidance` 2, `test_awcmdsurf_mutation_verbs` 3, `test_awmigrename` 2, `test_awphysical_tools` 1. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G7a-tsonlq-1` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G7a-tsonlq-1` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

- [x] E-02 (carried from `1upea0` E-03, batch subset G7a; round-3 split 2026-11-09) Batch G7a, 3 of its 24 modules (the unmatched test modules, first half (basename sorts before `test_l`)): `tests/test_collision_population_parity.py`, `tests/test_companion_record_owner_root.py`, `tests/test_completion.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_collision_population_parity` 2, `test_companion_record_owner_root` 7, `test_completion` 7. Run the codemod on these modules and apply the batch rule with `<batch>` = `G7a-tsonlq-2` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G7a-tsonlq-2` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

### Task group 2: finish

- [x] E-03 Finish this part: run the batch rule's step-2 command once over every module of this plan (`$(cat .aw/state/59aiyh/G7a-tsonlq-1-files.txt .aw/state/59aiyh/G7a-tsonlq-2-files.txt)`) into `.aw/state/59aiyh/tsonlq-union-after.txt` and confirm it equals the sorted concatenation of the items' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit tsonlq -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The full-suite comparison stays in `59aiyh` E-12.)
  - Depends on: E-01, E-02
  - Expected outcome: the union comparison is empty; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: performed

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

Measured 2026-11-09 at `3d0ddb845` for F-40; F-01, F-03, F-06 and F-08 copied from `1upea0` (measured at `0cbfcc706` and at review).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l --glob '*.py' -e '- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|## Workflow history' tests` lists 309 files (307 test modules, `support.py`, `conformance_matrix.py`) of 717 Python files; 6,638 matching lines. The narrower `- Id:`/`- Status:`/`## Workflow history` pattern: 300 files, 3,430 lines | Spec section 6 counted 268 of 680 files and 2,607 matches at round 2; the plan's pattern is broader (21 fields). |
| F-03 | Family split by filename prefix, re-measured at review (HEAD `4a7499289`, 311 files, 6,657 lines) with a FIRST-MATCH rule (a file goes to the first group, in order G1 to G6, whose pattern list matches its basename; unmatched files go to G7): G1 39 files, 1,568 lines; G2 22, 1,102; G3 28, 795; G4 63, 1,244; G5 46, 598; G6 69, 1,004; G7 44, 346. Six files match two groups and are assigned by that rule (`test_ipd_authoring` G3, `test_readiness_absence_invariant` G4, `test_runner_backlog_close_behavior` G1, `test_orchestrator_retire_closes_backlog` G1, `test_records_only_lane_rederive` G5, `test_ipdrunner_runagy_shim` G4). The authored counts (G6 99, G7 11) did not sum to the file total; the first-match rule makes the partition exhaustive and disjoint. EXCLUDED from every batch (literal legacy input is their subject; owned by other plans): `tests/test_artifact_meta_*.py` (`tve77h`, `2xwb9b`), `tests/test_artifact_meta_legacy_writer.py` and `tests/test_writers_*.py` (`xexn45`), `tests/test_m0001_*.py` and `tests/test_migrations_chain.py` (`dcerjg`, `ya4ee4`) | Seven batches (E-03 to E-09); G1, G4 and G6 carry a pre-measured split seam (OQ-01). |
| F-06 | (written by E-11) remaining legacy strings in `tests/` after the batches, each with one reason class: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, `body prose` | Order 13 changes the builder plus the F-06 rows of class `setter-byte assertion`; `invalid-input` rows already go through `raw_fields=` and need a decision at the cutover (an invalid bullet has no log-format equivalent); every other class is either a legacy-format test (moved to the migration tests at the cutover) or prose. |
| F-08 | At review, 15 test modules write a deliberately invalid metadata value (for example `tests/test_releases.py` "`- Status: bogus`", `tests/test_check_engine.py` "`- Status: EXECUTED`", `tests/test_specs_set_adapter.py` "`- Priority: bogus`") | A builder that validates every field cannot build these; E-01 adds `raw_fields=` and the batch rule lists them as `invalid-input`. |
| F-40 | `rg -c` with the F-01 pattern over this part's modules at `3d0ddb845`; subset by the F-03 first-match rule; helpers as listed by `1upea0` at the 2026-11-07 split | See the table below; every module is named in exactly one item. |

| Module | Subset | F-01 lines | Helpers at the split | Item |
|---|---|---|---|---|
| `tests/test_authoring_coverage_guidance.py` | G7a | 2 | none | E-01 |
| `tests/test_awcmdsurf_mutation_verbs.py` | G7a | 3 | none | E-01 |
| `tests/test_awmigrename.py` | G7a | 2 | none | E-01 |
| `tests/test_awphysical_tools.py` | G7a | 1 | none | E-01 |
| `tests/test_collision_population_parity.py` | G7a | 2 | none | E-02 |
| `tests/test_companion_record_owner_root.py` | G7a | 7 | none | E-02 |
| `tests/test_completion.py` | G7a | 7 | none | E-02 |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Convert batch G7a-tsonlq-1 (E-01)<br/>tests/test_authoring_coverage_guidance.py, tests/test_awcmdsurf_mutation_verbs.py, tests/test_awmigrename.py, tests/test_awphysical_tools.py"]
    E02["2. Convert batch G7a-tsonlq-2 (E-02)<br/>tests/test_collision_population_parity.py, tests/test_companion_record_owner_root.py, tests/test_completion.py"]
    E03["3. Finish, assemble union & commit (E-03)<br/>Union diff, core gate, aw sanitize, aw commit"]

    E01 --> E02
    E02 --> E03
```

1. Convert each item's modules under the batch rule (E-01 to E-02).
2. Re-run the union, the core gate, commit (E-03).

## Deferred / out of scope (with reason)

- The other modules of subset G7a, the partition re-derivation that catches modules no plan names, and the subsets' finishing checks.
  - Carrier: 1upea0
- The fixture codemod and its census (F-30, F-31).
  - Carrier: 653ndz
  - Carrier-Evidence: .aw/records/plans/executed/20261108-metastore-49-653ndz-build-and-prove-the-test-fixture-codemod.ipd.md
- The builder, its tests, the baselines and the tracked fixtures.
  - Carrier: 9rgn2w
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-37-9rgn2w-add-the-shared-test-record-builder-and-convert-the-tracked-r.ipd.md
- The switch-point proof, the F-06 census and the full-suite comparison.
  - Carrier: 59aiyh
- Adding `RECORD_FORMAT = "log"` and converting setter-byte assertions (cutover commit).
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No production module changes; every Scope-Paths entry is a module named in one item, plus this plan.
- Under-scope: none known. Size: 3 E-items (2 batch items of at most 4 modules each and the finish), 7 work Scope-Paths.

## Required tests / validation

Each item is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, unchanged assertions, the same outcomes. Commands: the batch rule's command per item, the codemod's `--apply` report, the bare core gate `python3 -m pytest`, `aw sanitize --agent`. CONTRIBUTES to AC-1b (owned by `cxxmyv`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` section 6 and section 7 step 6.

## Open questions

### OQ-01: Can this part run in any order relative to the other chunk plans?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. The module lists of all chunk plans are disjoint, each needs the builder (`9rgn2w`) and the codemod (`653ndz`), and none edits `tests/support.py` (that is `59aiyh` E-09, which runs last). Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `.aw/state/59aiyh/G7a-tsonlq-1-files.txt` and the empty `diff .aw/state/59aiyh/G7a-tsonlq-1-before.txt .aw/state/59aiyh/G7a-tsonlq-1-after.txt`; then, for each of `tests/test_authoring_coverage_guidance.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_awmigrename.py`, `tests/test_awphysical_tools.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G7a-tsonlq-1-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G7a-tsonlq-1-files.txt`:
      - `tests/test_authoring_coverage_guidance.py`
      - `tests/test_awcmdsurf_mutation_verbs.py`
      - `tests/test_awmigrename.py`
      - `tests/test_awphysical_tools.py`
    - Partition check at starting HEAD `6d258d9324dff458d7ef95db977037b509f3e27d`: all 4 named modules matched F-01 before conversion. Nine post-split G7a modules matching F-01 are not named by any chunk plan (`tests/test_aw_repo_survey.py`, `tests/test_companion_containment_and_storage.py`, `tests/test_companion_doctor_and_carriers.py`, `tests/test_companion_runner_integration.py`, `tests/test_ctrlc_worktree_cleanup_ux.py`, `tests/test_fixture_codemod.py`, `tests/test_fixture_codemod_slow.py`, `tests/test_install_migrate_prompt.py`, `tests/test_installer_scaffold_preview_parity.py`); per the batch rule they were not added here and are reported for `1upea0` E-04.
    - Outcome diff (`diff -u .aw/state/59aiyh/G7a-tsonlq-1-before.txt .aw/state/59aiyh/G7a-tsonlq-1-after.txt`): empty output, exit code 0 (62 `PASSED` outcomes).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_authoring_coverage_guidance.py`:
        - F-01 `rg -c`: before 2, after 0. Remaining matches: none.
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-1-codemod.json`): `sites=2`, `rewrites=2` (`standard=2`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=e144177ef7e9c03be493902da24e34938447719c0f21c2590512aa027cd3f6ff`, `after_hash=e144177ef7e9c03be493902da24e34938447719c0f21c2590512aa027cd3f6ff`, `equivalent=true`, `pytest_runs=2`, `changed=true`.
        - `653ndz` F-30 row: `G7a | tsonlq | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_awcmdsurf_mutation_verbs.py`:
        - F-01 `rg -c`: before 3, after 2. Remaining matches (2):
          - `setter-byte assertion` (2, `legacy-kept` per codemod): `MutationVerbsTests.test_rename_apply_updates_refs_and_preserves_id` committed line 80 (`self.assertIn("- Id: aaa111", moved[0].read_text())`); `MutationVerbsTests.test_group_apply` committed line 95 (`self.assertIn("- Set: regrp", moved[0].read_text())`).
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-1-codemod.json`): `sites=3`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=2` (`setter-byte assertion=2`, `hand=0`, `legacy-kept=2`), `before_hash=dc0224f814cb24d31a4dbbe66638bf2b1b86abdd65454501800280188c421a6a`, `after_hash=dc0224f814cb24d31a4dbbe66638bf2b1b86abdd65454501800280188c421a6a`, `equivalent=true`, `pytest_runs=2`, `changed=true`.
        - `653ndz` F-30 row: `G7a | tsonlq | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 2`.
      - `tests/test_awmigrename.py`:
        - F-01 `rg -c`: before 2, after 0. Remaining matches: none.
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-1-codemod.json`): `sites=2`, `rewrites=2` (`standard=2`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=6305fe92b3d82cedfd261049027514cf04b45192b911d5535a2a41bc2862ff58`, `after_hash=6305fe92b3d82cedfd261049027514cf04b45192b911d5535a2a41bc2862ff58`, `equivalent=true`, `pytest_runs=2`, `changed=true`.
        - `653ndz` F-30 row: `G7a | tsonlq | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_awphysical_tools.py`:
        - F-01 `rg -c`: before 1, after 0. Remaining matches: none (pre-edit line 244 `"- Id: x\n- Status: open\n"` rewritten via `RecordBuilder().backlog(status='open', raw_fields={'Id': 'x'}, text_only=True)`, `invalid-input` rewrite class).
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-1-codemod.json`): `sites=1`, `rewrites=1` (`standard=0`, `invalid-input=1`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=8059061e6a9078bc86f17e133d1a76ebeb4b9a6b95d7aee8d89da09b41e47c09`, `after_hash=8059061e6a9078bc86f17e133d1a76ebeb4b9a6b95d7aee8d89da09b41e47c09`, `equivalent=true`, `pytest_runs=2`, `changed=true`.
        - `653ndz` F-30 row: `G7a | tsonlq | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
    - Hand count: 0 (0 static + 0 apply-time `not-equivalent`; <= 25; no hand-converted sites).
    - Post-edit codemod dry-run over all 4 modules: `test_authoring_coverage_guidance.py`, `test_awmigrename.py`, `test_awphysical_tools.py` at `sites=0`; `test_awcmdsurf_mutation_verbs.py` at `sites=2` (`hand=0`, `legacy-kept=2`).
    - Helper census (`rg -n "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*"`):
      - Before: `(none)` (0 matches).
      - After: `(none)` (0 matches).
      - Deleted helpers (0): none. Surviving helpers: none.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G7a-tsonlq-2-files.txt` and the empty `diff .aw/state/59aiyh/G7a-tsonlq-2-before.txt .aw/state/59aiyh/G7a-tsonlq-2-after.txt`; then, for each of `tests/test_collision_population_parity.py`, `tests/test_companion_record_owner_root.py`, `tests/test_completion.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G7a-tsonlq-2-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G7a-tsonlq-2-files.txt`:
      - `tests/test_collision_population_parity.py`
      - `tests/test_companion_record_owner_root.py`
      - `tests/test_completion.py`
    - Partition check at starting HEAD `6d258d9324dff458d7ef95db977037b509f3e27d`: all 3 named modules matched F-01 before conversion.
    - Outcome diff (`diff -u .aw/state/59aiyh/G7a-tsonlq-2-before.txt .aw/state/59aiyh/G7a-tsonlq-2-after.txt`): empty output, exit code 0 (43 `PASSED` outcomes).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_collision_population_parity.py`:
        - F-01 `rg -c`: before 2, after 2 (file intentionally left unmodified; 0 codemod sites; declared Scope-Path acknowledged for finalize). Remaining matches (2):
          - `body prose` (2): `CollisionPopulationParityTests.setUp` comment lines 47-48 (`# 3) a walkthrough whose identity slot reuses aaa111 while declaring no - Id:`, `# 4) two executed plans that both declare - Id: ccc333`).
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-2-codemod.json`): `sites=0`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`, `changed=false`.
        - `653ndz` F-30 row: `G7a | tsonlq | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_companion_record_owner_root.py`:
        - F-01 `rg -c`: before 7, after 2. Remaining matches (2):
          - `body prose` (2, `legacy-kept` per codemod): `test_specs_note_history_lands_in_companion_records_root` committed lines 656 and 716 (`r"^- Id:\s*([a-z0-9]{6})"` regex over `aw specs new` output with filename fallback).
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-2-codemod.json`): `sites=9`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=8` (`unsupported-shape=6`, `body prose=2`, `hand=6`, `legacy-kept=2`), `before_hash=537cb9efbec7364e4738596a166ad132fa318da831214188232625f01c388556`, `after_hash=537cb9efbec7364e4738596a166ad132fa318da831214188232625f01c388556`, `equivalent=true`, `pytest_runs=2`, `changed=true`.
        - `653ndz` F-30 row: `G7a | tsonlq | 9 | 1 | 0 | 0 | 6 | 0 | 0 | 0 | 0 | 2 | 6 | 2`.
      - `tests/test_completion.py`:
        - F-01 `rg -c`: before 7, after 1. Remaining matches (1):
          - `body prose` (1, `legacy-kept` per codemod): `CompleteQueryTests.QUERIES` rationale string committed line 1078 (`"the Set id comes from the plans' \`- Set:\` FRONT MATTER, not from the resolver; target "`).
        - Codemod JSON row (`.aw/state/59aiyh/G7a-tsonlq-2-codemod.json`): `sites=7`, `rewrites=5` (`standard=5`, `invalid-input=0`), `refusals=2` (`unsupported-shape=1`, `body prose=1`, `hand=1`, `legacy-kept=1`), `before_hash=923a64bc36b2b57d70cf59694c15fc992ae1ba5f9f0732287fe04926ea19a6ae`, `after_hash=923a64bc36b2b57d70cf59694c15fc992ae1ba5f9f0732287fe04926ea19a6ae`, `equivalent=true`, `pytest_runs=2`, `changed=true`.
        - `653ndz` F-30 row: `G7a | tsonlq | 7 | 5 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1`.
    - Hand count: 7 (7 static + 0 apply-time `not-equivalent`; <= 25; all 7 hand-converted):
      1. `tests/test_companion_record_owner_root.py` pre-edit line 151 (`c1_sibling_companion`, `unsupported-shape`): replaced manual `- Id:` line scan with `artifact_meta.read_text(plan_path.read_text(encoding="utf-8"), record_type="ipd").id6`.
      2. `tests/test_companion_record_owner_root.py` pre-edit line 229 (`c2_custom_companion`, `unsupported-shape`): replaced manual `- Id:` line scan with `artifact_meta.read_text(plan_path.read_text(encoding="utf-8"), record_type="ipd").id6`.
      3. `tests/test_companion_record_owner_root.py` pre-edit line 579 (2 sites in `test_ipd_lint_resolves_companion_sibling_dependency`, `unsupported-shape`): replaced `re.sub(r"- Item-Dependencies:.*", f"- Item-Dependencies: executed:{id6}", txt)` with `artifact_meta.render_legacy_text(..., [{"op": "set", "fields": {"item_dependencies": f"executed:{id6}"}}], record_type="ipd", render=artifact_meta.LegacyRender(tag="edit", day="2026-08-24", actor_label="probe", history=False))`.
      4. `tests/test_companion_record_owner_root.py` pre-edit line 593 (2 sites in `test_ipd_lint_resolves_companion_sibling_dependency`, `unsupported-shape`): replaced `re.sub(r"- Item-Dependencies:.*", "- Item-Dependencies: executed:zzzzzz", txt)` with `artifact_meta.render_legacy_text(..., [{"op": "set", "fields": {"item_dependencies": "executed:zzzzzz"}}], record_type="ipd", render=artifact_meta.LegacyRender(tag="edit", day="2026-08-24", actor_label="probe", history=False))`.
      5. `tests/test_completion.py` pre-edit line 947 (`_DynamicRepoFixture.setUp`, `unsupported-shape`): replaced `"# Task\n\n- Id: def456\n- Status: open\n- Summary: x\n"` with `RecordBuilder().backlog(id6="def456", status="open", summary="x", text_only=True)`.
    - Post-edit codemod dry-run over all 3 modules: `test_collision_population_parity.py` at `sites=0`; `test_companion_record_owner_root.py` at `sites=2` (`hand=0`, `legacy-kept=2`); `test_completion.py` at `sites=1` (`hand=0`, `legacy-kept=1`).
    - Helper census (`rg -n "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*"`):
      - Before: `(none)` (0 matches).
      - After: `(none)` (0 matches).
      - Deleted helpers (0): none. Surviving helpers: none.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `diff` of the sorted concatenation of the `-before.txt` lists of `G7a-tsonlq-1`, `G7a-tsonlq-2` against `.aw/state/59aiyh/tsonlq-union-after.txt` (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit tsonlq` output listing only Scope-Paths.
  - Observed evidence:
    - Union comparison (`diff -u .aw/state/59aiyh/tsonlq-union-before.txt .aw/state/59aiyh/tsonlq-union-after.txt`): empty output, exit code 0 (105 `PASSED` outcomes = 62 + 43 across all 7 modules).
    - Core gate (`aw suite`, running bare `python3 -m pytest` with 6 xdist workers): `2666 passed, 11 warnings in 105.77s (0:01:45)`, exit code 0.
    - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6899,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw commit tsonlq` outputs (all committed paths strictly inside Scope-Paths; `tests/test_collision_population_parity.py` intentionally unmodified with 0 codemod sites; never pushed):
      - E-01: `aw commit: committed 4 path(s): 3d3ec634ddaabaad77c3d43757be3324da9d868e` (`tests/test_authoring_coverage_guidance.py`, `tests/test_awcmdsurf_mutation_verbs.py`, `tests/test_awmigrename.py`, `tests/test_awphysical_tools.py`).
      - E-02: `aw commit: committed 2 path(s): a53160140d661e0f4e3df0a8e6998124d5ba30b4` (`tests/test_companion_record_owner_root.py`, `tests/test_completion.py`).
      - Plan evidence: committed via `aw commit tsonlq -- .aw/records/plans/pending/20261109-metastore-208-tsonlq-move-setter-runner-lane-and-first-half-unmatched-test-data-c.ipd.md`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45` are executed. Every open question is resolved.

Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or required builder symbols from `9rgn2w` or codemod from `653ndz` are absent, stop and report rather than proceeding. Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a module cannot keep its outcome list identical without a production change, stop that item and report the missing capability rather than changing production code or an assertion.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit tsonlq -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize tsonlq` itself.
