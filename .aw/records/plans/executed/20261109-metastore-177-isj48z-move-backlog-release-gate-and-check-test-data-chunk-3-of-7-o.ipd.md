# IPD: Move backlog, release-gate and check test data chunk 3 of 7 onto the record builder

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. Research `nj8zdp` and the maintainer's ruling ("plans that obtuse and not-too-smart agents won't mess up") set the guidance of at most 5 E-items, 8 work Scope-Paths and about 8 named units per item; `x05v02` named up to 25 modules per batch item. This part carries 8 of `x05v02`'s modules (subsets G1a, G1b; 305 F-01 legacy lines at `3d0ddb845`), each item at most 4 modules, converted by the Order-49 codemod (`653ndz`) plus only its census-counted refusals.
- Scope: Chunk 3 of 7 of `x05v02` (round-3 split 2026-11-09 per research `nj8zdp` guidance): the 8 test modules named in the items and in F-40, each item one codemod run under the batch rule below, plus a finishing item. EXCLUDES: every other module of the subsets (the other chunk plans and `x05v02`); the builder (`9rgn2w`) and the codemod (`653ndz`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_backlog_transition_gate.py, tests/test_release_gate_one_way_mismatch.py, tests/test_release_readiness.py, tests/test_releases_cli.py, tests/test_release_sentinel_succession.py, tests/test_releases_line_writers.py, tests/test_releases.py, tests/test_releases_sibling_line_writers_bounding.py, .aw/records/plans/pending/20261109-metastore-177-isj48z-move-backlog-release-gate-and-check-test-data-chunk-3-of-7-o.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 177
- Highest E allocated: 04
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: isj48z

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 executed (aw agy run model=Gemini-4-Neon-High): aw agy run self-finalize: isj48z verified (set metastore, attempt 1). [Scope reconciliation - in-scope-unmodified tests/test_backlog_transition_gate.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_release_gate_one_way_mismatch.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_release_readiness.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_release_sentinel_succession.py: declared-but-unmodified (auto-acknowledged by aw agy run); in-scope-unmodified tests/test_releases_cli.py: declared-but-unmodified (auto-acknowledged by aw agy run)]
- 2026-11-21 cap-update (maintainer decision): raised Batch rule step 4 hand-refusal cap from 25 to 100 (raw site count over-counts list elements and .replace() pairs); completed sibling E-item and Step-3 commits from run-20261121T014040Z-2638602 were salvaged onto main, so modules already at 0 rewrites and 0 hand refusals remain unmodified and are acknowledged via --scope-ack at finalize.
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): plan-review verified E/V bijection, Scope-Paths, batch rules, execution gate, and state directory initialization; findings PR-001..PR-005 fixed; marked reviewed and go-pending-approval.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from x05v02 (round 3, research nj8zdp guidance).

## Goal

Every hand-built record in the 8 test modules named below comes from `tests/record_builder.py`, written by the Order-49 codemod or, for its census-counted refusals only, by hand, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`), carried by the round-3 split into Order 170 (`j6o96i`) with the same ids; because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the modules each batch item names (round-3 split 2026-11-09: a subset is now spread over several plans of at most 8 modules each): a module that the partition now places in the item's subset but that no plan names is NOT added here; it is reported, and the finishing item of `x05v02` converts it; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, create directory `mkdir -p .aw/state/59aiyh/` and re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03, carried with the same id into Order 172, `y3uowx`, by the round-3 split) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 100, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: batch items

- [x] E-01 (carried from `x05v02` E-01, batch subset G1a; round-3 split 2026-11-09) Batch G1a, 1 of its 17 modules (the backlog tests (`test_backlog*`)): `tests/test_backlog_transition_gate.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_backlog_transition_gate` 31. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G1a-isj48z-1` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 100, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G1a-isj48z-1` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 100) pasted.
  - Execution state: performed

- [x] E-02 (carried from `x05v02` E-02, batch subset G1b; round-3 split 2026-11-09) Batch G1b, 4 of its 22 modules (the release and release-gate tests (`test_release*`, `test_releases*`, `test_graduat*`, `test_gate_*`, `test_blocks_release*`, `test_handoff*`, `test_from_backlog*`, `test_live_bug*`, `test_*close*`, `test_carrier*`, `test_durable_carrier*`)): `tests/test_release_gate_one_way_mismatch.py`, `tests/test_release_readiness.py`, `tests/test_releases_cli.py`, `tests/test_release_sentinel_succession.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_release_gate_one_way_mismatch` 26, `test_release_readiness` 1, `test_releases_cli` 9, `test_release_sentinel_succession` 21. Run the codemod on these modules and apply the batch rule with `<batch>` = `G1b-isj48z-2` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 100, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G1b-isj48z-2` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 100) pasted.
  - Execution state: performed

- [x] E-03 (carried from `x05v02` E-02, batch subset G1b; round-3 split 2026-11-09) Batch G1b, 3 of its 22 modules (the release and release-gate tests (`test_release*`, `test_releases*`, `test_graduat*`, `test_gate_*`, `test_blocks_release*`, `test_handoff*`, `test_from_backlog*`, `test_live_bug*`, `test_*close*`, `test_carrier*`, `test_durable_carrier*`)): `tests/test_releases_line_writers.py`, `tests/test_releases.py`, `tests/test_releases_sibling_line_writers_bounding.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_releases_line_writers` 151, `test_releases` 15, `test_releases_sibling_line_writers_bounding` 51. Run the codemod on these modules and apply the batch rule with `<batch>` = `G1b-isj48z-3` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 100, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G1b-isj48z-3` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 100) pasted.
  - Execution state: performed

### Task group 2: finish

- [x] E-04 Finish this part: run the batch rule's step-2 command once over every module of this plan (`$(cat .aw/state/59aiyh/G1a-isj48z-1-files.txt .aw/state/59aiyh/G1b-isj48z-2-files.txt .aw/state/59aiyh/G1b-isj48z-3-files.txt)`) into `.aw/state/59aiyh/isj48z-union-after.txt` and confirm it equals the sorted concatenation of the items' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit isj48z -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The full-suite comparison stays in `59aiyh` E-12.)
  - Depends on: E-01, E-02, E-03
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

Measured 2026-11-09 at `3d0ddb845` for F-40; F-01, F-03, F-06 and F-08 copied from `x05v02` (measured at `0cbfcc706` and at review).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l --glob '*.py' -e '- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|## Workflow history' tests` lists 309 files (307 test modules, `support.py`, `conformance_matrix.py`) of 717 Python files; 6,638 matching lines. The narrower `- Id:`/`- Status:`/`## Workflow history` pattern: 300 files, 3,430 lines | Spec section 6 counted 268 of 680 files and 2,607 matches at round 2; the plan's pattern is broader (21 fields). |
| F-03 | Family split by filename prefix, re-measured at review (HEAD `4a7499289`, 311 files, 6,657 lines) with a FIRST-MATCH rule (a file goes to the first group, in order G1 to G6, whose pattern list matches its basename; unmatched files go to G7): G1 39 files, 1,568 lines; G2 22, 1,102; G3 28, 795; G4 63, 1,244; G5 46, 598; G6 69, 1,004; G7 44, 346. Six files match two groups and are assigned by that rule (`test_ipd_authoring` G3, `test_readiness_absence_invariant` G4, `test_runner_backlog_close_behavior` G1, `test_orchestrator_retire_closes_backlog` G1, `test_records_only_lane_rederive` G5, `test_ipdrunner_runagy_shim` G4). The authored counts (G6 99, G7 11) did not sum to the file total; the first-match rule makes the partition exhaustive and disjoint. EXCLUDED from every batch (literal legacy input is their subject; owned by other plans): `tests/test_artifact_meta_*.py` (`tve77h`, `2xwb9b`), `tests/test_artifact_meta_legacy_writer.py` and `tests/test_writers_*.py` (`xexn45`), `tests/test_m0001_*.py` and `tests/test_migrations_chain.py` (`dcerjg`, `ya4ee4`) | Seven batches (E-03 to E-09); G1, G4 and G6 carry a pre-measured split seam (OQ-01). |
| F-06 | (written by E-11) remaining legacy strings in `tests/` after the batches, each with one reason class: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, `body prose` | Order 13 changes the builder plus the F-06 rows of class `setter-byte assertion`; `invalid-input` rows already go through `raw_fields=` and need a decision at the cutover (an invalid bullet has no log-format equivalent); every other class is either a legacy-format test (moved to the migration tests at the cutover) or prose. |
| F-08 | At review, 15 test modules write a deliberately invalid metadata value (for example `tests/test_releases.py` "`- Status: bogus`", `tests/test_check_engine.py` "`- Status: EXECUTED`", `tests/test_specs_set_adapter.py` "`- Priority: bogus`") | A builder that validates every field cannot build these; E-01 adds `raw_fields=` and the batch rule lists them as `invalid-input`. |
| F-40 | `rg -c` with the F-01 pattern over this part's modules at `3d0ddb845`; subset by the F-03 first-match rule; helpers as listed by `x05v02` at the 2026-11-07 split | See the table below; every module is named in exactly one item. |

| Module | Subset | F-01 lines | Helpers at the split | Item |
|---|---|---|---|---|
| `tests/test_backlog_transition_gate.py` | G1a | 31 | none | E-01 |
| `tests/test_release_gate_one_way_mismatch.py` | G1b | 26 | none | E-02 |
| `tests/test_release_readiness.py` | G1b | 1 | none | E-02 |
| `tests/test_releases_cli.py` | G1b | 9 | none | E-02 |
| `tests/test_release_sentinel_succession.py` | G1b | 21 | none | E-02 |
| `tests/test_releases_line_writers.py` | G1b | 151 | none | E-03 |
| `tests/test_releases.py` | G1b | 15 | none | E-03 |
| `tests/test_releases_sibling_line_writers_bounding.py` | G1b | 51 | none | E-03 |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Convert batch G1a-isj48z-1 (E-01)<br/>tests/test_backlog_transition_gate.py"]
    E02["2. Convert batch G1b-isj48z-2 (E-02)<br/>tests/test_release_gate_one_way_mismatch.py, tests/test_release_readiness.py, tests/test_releases_cli.py, tests/test_release_sentinel_succession.py"]
    E03["3. Convert batch G1b-isj48z-3 (E-03)<br/>tests/test_releases_line_writers.py, tests/test_releases.py, tests/test_releases_sibling_line_writers_bounding.py"]
    E04["4. Finish, assemble union & commit (E-04)<br/>Union diff, core gate, aw sanitize, aw commit"]

    E01 --> E02
    E02 --> E03
    E03 --> E04
```

1. Convert each item's modules under the batch rule (E-01 to E-03).
2. Re-run the union, the core gate, commit (E-04).

## Deferred / out of scope (with reason)

- The other modules of subsets G1a, G1b, the partition re-derivation that catches modules no plan names, and the subsets' finishing checks.
  - Carrier: x05v02
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
- Under-scope: none known. Size: 4 E-items (3 batch items of at most 4 modules each and the finish), 8 work Scope-Paths.

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
  - Required evidence: paste `.aw/state/59aiyh/G1a-isj48z-1-files.txt` and the empty `diff .aw/state/59aiyh/G1a-isj48z-1-before.txt .aw/state/59aiyh/G1a-isj48z-1-after.txt`; then, for each of `tests/test_backlog_transition_gate.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G1a-isj48z-1-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G1a-isj48z-1-files.txt`: `tests/test_backlog_transition_gate.py`. (Late G1a partition check: none; all F-01-matching `tests/test_backlog*.py` modules at starting HEAD `6ecb307be` are owned by `id2pdx`, `2fn0vd`, or `isj48z`.)
    - `diff -u .aw/state/59aiyh/G1a-isj48z-1-before.txt .aw/state/59aiyh/G1a-isj48z-1-after.txt`: empty output, exit code 0 (`14` `PASSED` outcomes before and after).
    - Note on salvaged E-01 commit: commit `0d5d6a7fb` (salvaged onto `main` from `run-20261121T014040Z-2638602`) already converted `tests/test_backlog_transition_gate.py` onto `RecordBuilder`. At starting HEAD `6ecb307be`, the module sits at 0 rewrites and 0 hand refusals, so it remains unmodified and is acknowledged via `--scope-ack` at finalize per the 2026-11-21 `cap-update` workflow history entry.
    - `tests/test_backlog_transition_gate.py`:
      - F-01 `rg -c`: 6 before (at `6ecb307be`; 31 at split `3d0ddb845`) -> 6 after.
      - Remaining 6 F-01 matches: lines 12 (module docstring), 636 (comment), 640 and 674 (test docstrings) (4 `body prose`); lines 320 and 382 `self.assertIn(f"- Status: {tgt}", found.read_text(encoding="utf-8"))` (2 `setter-byte assertion`).
      - `G1a-isj48z-1-codemod.json`: sites=2, rewrites=0 (standard=0, invalid-input=0), refusals=2 (`setter-byte assertion`=2 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_backlog_transition_gate.py | G1a | isj48z | 15 | 3 | 0 | 1 | 9 | 0 | 0 | 0 | 2 | 0 | 10 | 2 |`.
    - Hand count: 0 in this turn (the 10 static hand refusals in `653ndz` F-30 — 1 `dynamic-construction` and 9 `unsupported-shape` — were already hand-converted in salvaged commit `0d5d6a7fb`; 0 apply-time `not-equivalent`; <= 100).
    - E-09 helper census (`rg -n -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*"`): before at `6ecb307be` = 0 (`(none)`); after = 0 (`(none)`). Deleted helpers: none. Surviving helpers: none.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G1b-isj48z-2-files.txt` and the empty `diff .aw/state/59aiyh/G1b-isj48z-2-before.txt .aw/state/59aiyh/G1b-isj48z-2-after.txt`; then, for each of `tests/test_release_gate_one_way_mismatch.py`, `tests/test_release_readiness.py`, `tests/test_releases_cli.py`, `tests/test_release_sentinel_succession.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G1b-isj48z-2-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G1b-isj48z-2-files.txt`: `tests/test_releases_cli.py`, `tests/test_release_sentinel_succession.py`. (`tests/test_release_gate_one_way_mismatch.py` and `tests/test_release_readiness.py` no longer match F-01 at starting HEAD `6ecb307be` after salvaged commit `a0acd715c`, so per Batch rule step 1 both are reported and skipped; verified directly: `2` `PASSED` in `tests/test_release_gate_one_way_mismatch.py` and `35` `PASSED` in `tests/test_release_readiness.py`. Late G1b partition check: none; all F-01-matching G1b modules at starting HEAD `6ecb307be` are owned by `isj48z`, `dg43sc`, or `wirc2e`.)
    - `diff -u .aw/state/59aiyh/G1b-isj48z-2-before.txt .aw/state/59aiyh/G1b-isj48z-2-after.txt`: empty output, exit code 0 (`46` `PASSED` outcomes before and after across the 2 F-01-matching modules: `37` in `tests/test_releases_cli.py`, `9` in `tests/test_release_sentinel_succession.py`; plus `37` `PASSED` across the 2 skipped modules = `83` total).
    - Note on salvaged E-02 commit: commit `a0acd715c` (salvaged onto `main` from `run-20261121T014040Z-2638602`) already converted all 4 E-02 modules onto `RecordBuilder`. At starting HEAD `6ecb307be`, all 4 modules sit at 0 rewrites and 0 hand refusals, so they remain unmodified and are acknowledged via `--scope-ack` at finalize per the 2026-11-21 `cap-update` workflow history entry.
    - `tests/test_release_gate_one_way_mismatch.py`:
      - F-01 `rg -c`: 0 before (at `6ecb307be`; 26 at split `3d0ddb845`) -> 0 after (skipped in step 1; verified `2` `PASSED` outcomes directly).
      - Remaining F-01 matches: none (0).
      - `G1b-isj48z-2-codemod.json`: skipped from `G1b-isj48z-2-files.txt` per step 1 (dry-run confirmed sites=0, rewrites=0, refusals=0, hand=0, legacy-kept=0).
      - `653ndz` F-30 row: `| tests/test_release_gate_one_way_mismatch.py | G1b | isj48z | 7 | 1 | 0 | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 6 | 0 |`.
    - `tests/test_release_readiness.py`:
      - F-01 `rg -c`: 0 before (at `6ecb307be`; 1 at split `3d0ddb845`) -> 0 after (skipped in step 1; verified `35` `PASSED` outcomes directly).
      - Remaining F-01 matches: none (0).
      - `G1b-isj48z-2-codemod.json`: skipped from `G1b-isj48z-2-files.txt` per step 1 (dry-run confirmed sites=0, rewrites=0, refusals=0, hand=0, legacy-kept=0).
      - `653ndz` F-30 row: `| tests/test_release_readiness.py | G1b | isj48z | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |`.
    - `tests/test_releases_cli.py`:
      - F-01 `rg -c`: 1 before (at `6ecb307be`; 9 at split `3d0ddb845`) -> 1 after.
      - Remaining 1 F-01 match: line 274 `self.assertIn("- Status: planned", text)` (`setter-byte assertion`).
      - `G1b-isj48z-2-codemod.json`: sites=1, rewrites=0 (standard=0, invalid-input=0), refusals=1 (`setter-byte assertion`=1 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_releases_cli.py | G1b | isj48z | 7 | 2 | 0 | 0 | 4 | 0 | 0 | 0 | 1 | 0 | 4 | 1 |`.
    - `tests/test_release_sentinel_succession.py`:
      - F-01 `rg -c`: 4 before (at `6ecb307be`; 21 at split `3d0ddb845`) -> 4 after.
      - Remaining 4 F-01 matches: lines 340, 369, 370, 464 (all 4 `setter-byte assertion`).
      - `G1b-isj48z-2-codemod.json`: sites=4, rewrites=0 (standard=0, invalid-input=0), refusals=4 (`setter-byte assertion`=4 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_release_sentinel_succession.py | G1b | isj48z | 17 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 0 | 0 | 4 |`.
    - Hand count: 0 in this turn (the 10 static hand refusals in `653ndz` F-30 — 3 `dynamic-construction` and 3 `unsupported-shape` in `tests/test_release_gate_one_way_mismatch.py`, 4 `unsupported-shape` in `tests/test_releases_cli.py` — were already hand-converted in salvaged commit `a0acd715c`; 0 apply-time `not-equivalent`; <= 100).
    - E-09 helper census: before at `6ecb307be` = 0 (`(none)`); after = 0 (`(none)`). Deleted helpers: none. Surviving helpers: none.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste `.aw/state/59aiyh/G1b-isj48z-3-files.txt` and the empty `diff .aw/state/59aiyh/G1b-isj48z-3-before.txt .aw/state/59aiyh/G1b-isj48z-3-after.txt`; then, for each of `tests/test_releases_line_writers.py`, `tests/test_releases.py`, `tests/test_releases_sibling_line_writers_bounding.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G1b-isj48z-3-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G1b-isj48z-3-files.txt`: `tests/test_releases_line_writers.py`, `tests/test_releases.py`, `tests/test_releases_sibling_line_writers_bounding.py`.
    - `diff -u .aw/state/59aiyh/G1b-isj48z-3-before.txt .aw/state/59aiyh/G1b-isj48z-3-after.txt`: empty output, exit code 0 (`54` `PASSED` outcomes before and after: `23` in `tests/test_releases_line_writers.py`, `22` in `tests/test_releases.py`, `9` in `tests/test_releases_sibling_line_writers_bounding.py`).
    - Note on salvaged Step 3 commit: commit `abbd84e5a` (salvaged onto `main` from `run-20261121T014040Z-2638602`) had already applied the 11 proved codemod rewrites for E-03 (4 in `tests/test_releases_line_writers.py`, 4 in `tests/test_releases.py`, 3 in `tests/test_releases_sibling_line_writers_bounding.py`), so the fresh Step 3 run at `6ecb307be` applied 0 further rewrites and isolated the 38 remaining `hand` refusals (all 38 static in `653ndz` F-30, 0 apply-time `not-equivalent`). Post-edit `fixture_codemod.py --dry-run` confirmed `rewrites=0, hand=0, legacy-kept=45` across all 3 modules.
    - `tests/test_releases_line_writers.py`:
      - F-01 `rg -c`: 127 before (at `6ecb307be`; 151 at split `3d0ddb845`) -> 51 after.
      - Remaining 51 F-01 matches (at committed `344e13d44`):
        - 33 `setter-byte assertion`: lines 73, 107, 141, 171, 172, 186, 187, 253, 254, 257, 258, 278, 313, 339, 365, 391, 393, 408, 409, 463, 464, 467, 468, 487, 653, 654, 679, 697, 756, 757, 783, 802, 838.
        - 2 `displayed-output assertion`: lines 651, 753.
        - 2 `invalid-input`: line 272 (`"Blocks-Release": "\n- Blocks-Release: old123"`), line 481 (`"From-Backlog": "\n- From-Backlog: old123"`) (duplicate-bullet corruption built through `RecordBuilder().plan(..., raw_fields=...)`).
        - 14 `body prose`: module docstring lines 7, 8; test docstring lines 56, 91, 125, 159, 175, 206, 300, 327, 353, 379, 397, 428.
      - `G1b-isj48z-3-codemod.json`: sites=63, rewrites=0 (standard=0, invalid-input=0), refusals=63 (`unsupported-shape`=28 `hand`, `displayed-output assertion`=2 `legacy-kept`, `setter-byte assertion`=33 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_releases_line_writers.py | G1b | isj48z | 67 | 4 | 0 | 0 | 28 | 0 | 0 | 2 | 33 | 0 | 28 | 35 |`.
    - `tests/test_releases.py`:
      - F-01 `rg -c`: 9 before (at `6ecb307be`; 15 at split `3d0ddb845`) -> 3 after.
      - Remaining 3 F-01 matches (at committed `344e13d44`): line 51 `self.assertIn("- Status: planned", text)` (`setter-byte assertion`); line 84 `_re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", p.read_text(encoding="utf-8"))` (`setter-byte assertion`, codemod label `body prose` `legacy-kept`); line 144 docstring (`body prose`). Note: `test_create_and_validate` builds its invalid status via `RecordBuilder().release(..., raw_fields={"status": "bogus"}, text_only=True)` (`invalid-input`, F-08).
      - `G1b-isj48z-3-codemod.json`: sites=7, rewrites=0 (standard=0, invalid-input=0), refusals=7 (`unsupported-shape`=5 `hand`, `setter-byte assertion`=1 `legacy-kept`, `body prose`=1 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_releases.py | G1b | isj48z | 11 | 4 | 0 | 0 | 5 | 0 | 0 | 0 | 1 | 1 | 5 | 2 |`.
    - `tests/test_releases_sibling_line_writers_bounding.py`:
      - F-01 `rg -c`: 41 before (at `6ecb307be`; 51 at split `3d0ddb845`) -> 26 after.
      - Remaining 26 F-01 matches (at committed `344e13d44`):
        - 8 `setter-byte assertion`: lines 180, 181, 261, 264, 265, 266, 359, 360.
        - 18 `body prose`: docstring/comment lines 152, 154, 159, 160, 183, 184, 213, 214, 244, 247, 291, 292; body-quote fixture strings inside `RecordBuilder` `body=` arguments on lines 169, 199, 226, 227, 254, 325.
      - `G1b-isj48z-3-codemod.json`: sites=13, rewrites=0 (standard=0, invalid-input=0), refusals=13 (`unsupported-shape`=5 `hand`, `setter-byte assertion`=8 `legacy-kept`), before_hash=None, after_hash=None, equivalent=True.
      - `653ndz` F-30 row: `| tests/test_releases_sibling_line_writers_bounding.py | G1b | isj48z | 16 | 3 | 0 | 0 | 5 | 0 | 0 | 0 | 8 | 0 | 5 | 8 |`.
    - Hand count: 38 (38 static in `653ndz` F-30 + 0 apply-time `not-equivalent`; <= 100). Hand-converted sites (pre-edit lines at `6ecb307be`):
      1-28. `tests/test_releases_line_writers.py`: L44-48, L53-57, L64-68, L73-77, L84-88, L93-97, L103, L110, L117, L125, L126, L127, L140-145, L150-154, L165-169, L174-178, L185-189, L194-198, L205-209, L214-218, L225, L235, L243, L252, L253, L254, L267-272, L277-281 (28 `unsupported-shape`; converted to `RecordBuilder().plan(..., raw_fields=..., text_only=True)` and `RecordBuilder().spec(..., raw_fields={"Status": None, "Author": None, "Scope": "test"}, text_only=True)` for the two fallback-after-id cases).
      29-33. `tests/test_releases.py`: L55 x2 (2 `unsupported-shape`, replaced `text.replace("- Status: planned", "- Status: bogus")` with `RecordBuilder().release(..., raw_fields={"status": "bogus"}, text_only=True)`), L169-170, L174-175, L179-180 (3 `unsupported-shape`, converted to `RecordBuilder().backlog(..., text_only=True)`).
      34-38. `tests/test_releases_sibling_line_writers_bounding.py`: L45-54, L60-68, L155-162, L181-187, L202-209 (5 `unsupported-shape`; converted `_make_fixture`, `_make_fixture_no_field`, `text_deps`, `text_stat`, and `text_no_anchor` to `RecordBuilder().plan(..., raw_fields=..., text_only=True)`).
    - E-09 helper census: before at `6ecb307be` = 0 (`(none)`); after = 0 (`(none)`). Deleted helpers: none. Surviving helpers: none.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the `diff` of the sorted concatenation of the `-before.txt` lists of `G1a-isj48z-1`, `G1b-isj48z-2`, `G1b-isj48z-3` against `.aw/state/59aiyh/isj48z-union-after.txt` (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit isj48z` output listing only Scope-Paths.
  - Observed evidence:
    - Union diff (`diff -u .aw/state/59aiyh/isj48z-union-before.txt .aw/state/59aiyh/isj48z-union-after.txt`): empty output, exit code 0 (`114` `PASSED` outcomes across the 6 F-01-matching modules; plus `37` `PASSED` across the 2 skipped E-02 modules = `151` total).
    - Core gate (`aw suite`, bounded-worker `python3 -m pytest` core tier): `2665 passed, 1 skipped, 11 warnings in 160.83s (0:02:40)` (exit code 0).
    - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":7049,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw commit isj48z` outputs (all paths within `Scope-Paths`; E-01's 1 module and E-02's 4 modules were already converted in salvaged commits `0d5d6a7fb` and `a0acd715c` and remain unmodified at 0 rewrites / 0 hand refusals for `--scope-ack` at finalize):
      - E-03 (3 Scope-Paths): `aw commit: committed 3 path(s): 344e13d44fdb39e5ac1f1f2115bae4273019a287` (`tests/test_releases_line_writers.py`, `tests/test_releases.py`, `tests/test_releases_sibling_line_writers_bounding.py`).
      - Followed by the plan-evidence commit via `aw commit isj48z -- .aw/records/plans/pending/20261109-metastore-177-isj48z-move-backlog-release-gate-and-check-test-data-chunk-3-of-7-o.ipd.md` (recorded in the lane execution report and outcome JSON).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45` are executed. Every open question is resolved.

Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or required builder symbols from `9rgn2w` or codemod from `653ndz` are absent, stop and report rather than proceeding. Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a module cannot keep its outcome list identical without a production change, stop that item and report the missing capability rather than changing production code or an assertion.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit isj48z -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize isj48z` itself.
