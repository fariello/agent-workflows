# IPD: Move runner-family, reader, record and review test data chunk 2 of 11 onto the record builder

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. Research `nj8zdp` and the maintainer's ruling ("plans that obtuse and not-too-smart agents won't mess up") set the guidance of at most 5 E-items, 8 work Scope-Paths and about 8 named units per item; `nbfg7w` named up to 25 modules per batch item. This part carries 8 of `nbfg7w`'s modules (subset G5b; 90 F-01 legacy lines at `3d0ddb845`), each item at most 4 modules, converted by the Order-49 codemod (`653ndz`) plus only its census-counted refusals.
- Scope: Chunk 2 of 11 of `nbfg7w` (round-3 split 2026-11-09 per research `nj8zdp` guidance): the 8 test modules named in the items and in F-40, each item one codemod run under the batch rule below, plus a finishing item. EXCLUDES: every other module of the subsets (the other chunk plans and `nbfg7w`); the builder (`9rgn2w`) and the codemod (`653ndz`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_freeze_time_refusal.py, tests/test_host_capability_wiring.py, tests/test_hostcapgate_execute_requirement.py, tests/test_isolation_per_action.py, tests/test_prior_attempt_projection.py, tests/test_reaskscore_composed.py, tests/test_red_ci_stop.py, tests/test_runfresh_end_to_end.py, .aw/records/plans/pending/20261109-metastore-193-v1t2ai-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: executed
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 193
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: v1t2ai

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 executed (aw agy run model=Gemini-4-Neon-High): aw agy run self-finalize: v1t2ai verified (set metastore, attempt 1).
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (antigravity/gemini-3.8-flash): plan-review verified E/V bijection, Scope-Paths, batch rules, execution gate, and state directory initialization; findings PR-001..PR-005 fixed; marked reviewed and go-pending-approval.
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from nbfg7w (round 3, research nj8zdp guidance).

## Goal

Every hand-built record in the 8 test modules named below comes from `tests/record_builder.py`, written by the Order-49 codemod or, for its census-counted refusals only, by hand, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`), carried by the round-3 split into Order 170 (`j6o96i`) with the same ids; because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the modules each batch item names (round-3 split 2026-11-09: a subset is now spread over several plans of at most 8 modules each): a module that the partition now places in the item's subset but that no plan names is NOT added here; it is reported, and the finishing item of `nbfg7w` converts it; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, create directory `mkdir -p .aw/state/59aiyh/` and re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03, carried with the same id into Order 172, `y3uowx`, by the round-3 split) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 25, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: batch items

- [x] E-01 (carried from `nbfg7w` E-01, batch subset G5b; round-3 split 2026-11-09) Batch G5b, 4 of its 25 modules (the other runner-family tests (`test_integrat*`, `test_isolation*`, `test_freeze*`, `test_typed_queue*`, `test_attempt*`, `test_attended*`, `test_turn*`, `test_verifier*`, `test_runwire*`, `test_runfresh*`, `test_red_ci*`, `test_silent*`, `test_prior*`, `test_reask*`, `test_hostcap*`, `test_host*`, `test_fixfirst*`, `test_fix_it*`, `test_clean_target*`, `test_commit*`, `test_work_*`, `test_ipdrunner*`, `test_stdin*`)): `tests/test_freeze_time_refusal.py`, `tests/test_host_capability_wiring.py`, `tests/test_hostcapgate_execute_requirement.py`, `tests/test_isolation_per_action.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_freeze_time_refusal` 31, `test_host_capability_wiring` 1, `test_hostcapgate_execute_requirement` 1, `test_isolation_per_action` 3. Ensure `.aw/state/59aiyh/` exists (`mkdir -p .aw/state/59aiyh/`), run the codemod on these modules and apply the batch rule with `<batch>` = `G5b-v1t2ai-1` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that builds a two-branch merge or a lane worktree commits builder-made records on each branch with real `git`. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_freeze_time_refusal.py`: `_write_plan`, `_write_spec`, `_write_backlog`); a surviving helper is listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G5b-v1t2ai-1` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

- [x] E-02 (carried from `nbfg7w` E-01, batch subset G5b; round-3 split 2026-11-09) Batch G5b, 4 of its 25 modules (the other runner-family tests (`test_integrat*`, `test_isolation*`, `test_freeze*`, `test_typed_queue*`, `test_attempt*`, `test_attended*`, `test_turn*`, `test_verifier*`, `test_runwire*`, `test_runfresh*`, `test_red_ci*`, `test_silent*`, `test_prior*`, `test_reask*`, `test_hostcap*`, `test_host*`, `test_fixfirst*`, `test_fix_it*`, `test_clean_target*`, `test_commit*`, `test_work_*`, `test_ipdrunner*`, `test_stdin*`)): `tests/test_prior_attempt_projection.py`, `tests/test_reaskscore_composed.py`, `tests/test_red_ci_stop.py`, `tests/test_runfresh_end_to_end.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_prior_attempt_projection` 1, `test_reaskscore_composed` 3, `test_red_ci_stop` 11, `test_runfresh_end_to_end` 39. Run the codemod on these modules and apply the batch rule with `<batch>` = `G5b-v1t2ai-2` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that builds a two-branch merge or a lane worktree commits builder-made records on each branch with real `git`. Then delete each private record-building helper in these modules that no longer has a caller (at the split: `tests/test_red_ci_stop.py`: `_write_plan`); a surviving helper is listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G5b-v1t2ai-2` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

### Task group 2: finish

- [x] E-03 Finish this part: run the batch rule's step-2 command once over every module of this plan (`$(cat .aw/state/59aiyh/G5b-v1t2ai-1-files.txt .aw/state/59aiyh/G5b-v1t2ai-2-files.txt)`) into `.aw/state/59aiyh/v1t2ai-union-after.txt` and confirm it equals the sorted concatenation of the items' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit v1t2ai -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The full-suite comparison stays in `59aiyh` E-12.)
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

Measured 2026-11-09 at `3d0ddb845` for F-40; F-01, F-03, F-06 and F-08 copied from `nbfg7w` (measured at `0cbfcc706` and at review).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l --glob '*.py' -e '- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|## Workflow history' tests` lists 309 files (307 test modules, `support.py`, `conformance_matrix.py`) of 717 Python files; 6,638 matching lines. The narrower `- Id:`/`- Status:`/`## Workflow history` pattern: 300 files, 3,430 lines | Spec section 6 counted 268 of 680 files and 2,607 matches at round 2; the plan's pattern is broader (21 fields). |
| F-03 | Family split by filename prefix, re-measured at review (HEAD `4a7499289`, 311 files, 6,657 lines) with a FIRST-MATCH rule (a file goes to the first group, in order G1 to G6, whose pattern list matches its basename; unmatched files go to G7): G1 39 files, 1,568 lines; G2 22, 1,102; G3 28, 795; G4 63, 1,244; G5 46, 598; G6 69, 1,004; G7 44, 346. Six files match two groups and are assigned by that rule (`test_ipd_authoring` G3, `test_readiness_absence_invariant` G4, `test_runner_backlog_close_behavior` G1, `test_orchestrator_retire_closes_backlog` G1, `test_records_only_lane_rederive` G5, `test_ipdrunner_runagy_shim` G4). The authored counts (G6 99, G7 11) did not sum to the file total; the first-match rule makes the partition exhaustive and disjoint. EXCLUDED from every batch (literal legacy input is their subject; owned by other plans): `tests/test_artifact_meta_*.py` (`tve77h`, `2xwb9b`), `tests/test_artifact_meta_legacy_writer.py` and `tests/test_writers_*.py` (`xexn45`), `tests/test_m0001_*.py` and `tests/test_migrations_chain.py` (`dcerjg`, `ya4ee4`) | Seven batches (E-03 to E-09); G1, G4 and G6 carry a pre-measured split seam (OQ-01). |
| F-06 | (written by E-11) remaining legacy strings in `tests/` after the batches, each with one reason class: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, `body prose` | Order 13 changes the builder plus the F-06 rows of class `setter-byte assertion`; `invalid-input` rows already go through `raw_fields=` and need a decision at the cutover (an invalid bullet has no log-format equivalent); every other class is either a legacy-format test (moved to the migration tests at the cutover) or prose. |
| F-08 | At review, 15 test modules write a deliberately invalid metadata value (for example `tests/test_releases.py` "`- Status: bogus`", `tests/test_check_engine.py` "`- Status: EXECUTED`", `tests/test_specs_set_adapter.py` "`- Priority: bogus`") | A builder that validates every field cannot build these; E-01 adds `raw_fields=` and the batch rule lists them as `invalid-input`. |
| F-40 | `rg -c` with the F-01 pattern over this part's modules at `3d0ddb845`; subset by the F-03 first-match rule; helpers as listed by `nbfg7w` at the 2026-11-07 split | See the table below; every module is named in exactly one item. |

| Module | Subset | F-01 lines | Helpers at the split | Item |
|---|---|---|---|---|
| `tests/test_freeze_time_refusal.py` | G5b | 31 | `_write_plan`, `_write_spec`, `_write_backlog` | E-01 |
| `tests/test_host_capability_wiring.py` | G5b | 1 | none | E-01 |
| `tests/test_hostcapgate_execute_requirement.py` | G5b | 1 | none | E-01 |
| `tests/test_isolation_per_action.py` | G5b | 3 | none | E-01 |
| `tests/test_prior_attempt_projection.py` | G5b | 1 | none | E-02 |
| `tests/test_reaskscore_composed.py` | G5b | 3 | none | E-02 |
| `tests/test_red_ci_stop.py` | G5b | 11 | `_write_plan` | E-02 |
| `tests/test_runfresh_end_to_end.py` | G5b | 39 | none | E-02 |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Convert batch G5b-v1t2ai-1 (E-01)<br/>tests/test_freeze_time_refusal.py, tests/test_host_capability_wiring.py, tests/test_hostcapgate_execute_requirement.py, tests/test_isolation_per_action.py"]
    E02["2. Convert batch G5b-v1t2ai-2 (E-02)<br/>tests/test_prior_attempt_projection.py, tests/test_reaskscore_composed.py, tests/test_red_ci_stop.py, tests/test_runfresh_end_to_end.py"]
    E03["3. Finish, assemble union & commit (E-03)<br/>Union diff, core gate, aw sanitize, aw commit"]

    E01 --> E02
    E02 --> E03
```

1. Convert each item's modules under the batch rule (E-01 to E-02).
2. Re-run the union, the core gate, commit (E-03).

## Deferred / out of scope (with reason)

- The other modules of subset G5b, the partition re-derivation that catches modules no plan names, and the subsets' finishing checks.
  - Carrier: nbfg7w
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
- Under-scope: none known. Size: 3 E-items (2 batch items of at most 4 modules each and the finish), 8 work Scope-Paths.

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
  - Required evidence: paste `.aw/state/59aiyh/G5b-v1t2ai-1-files.txt` and the empty `diff .aw/state/59aiyh/G5b-v1t2ai-1-before.txt .aw/state/59aiyh/G5b-v1t2ai-1-after.txt`; then, for each of `tests/test_freeze_time_refusal.py`, `tests/test_host_capability_wiring.py`, `tests/test_hostcapgate_execute_requirement.py`, `tests/test_isolation_per_action.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G5b-v1t2ai-1-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); the outcome lists are run with the batch rule's `-m ""`, so `slow` tests are included; paste the count of `slow` node ids in the list; and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G5b-v1t2ai-1-files.txt`:
      - `tests/test_freeze_time_refusal.py`
      - `tests/test_host_capability_wiring.py`
      - `tests/test_hostcapgate_execute_requirement.py`
      - `tests/test_isolation_per_action.py`
    - Outcome diff (`diff -u .aw/state/59aiyh/G5b-v1t2ai-1-before.txt .aw/state/59aiyh/G5b-v1t2ai-1-after.txt`): empty output, exit code 0 (52 `PASSED` outcomes; `slow` node id count: 0 via `python3 -m pytest -o addopts="" -m "slow" --collect-only -q`).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_freeze_time_refusal.py`:
        - F-01 `rg -c`: before 31, after 1. Remaining matches (1): line 74 (`# rdyreq (\`fhinri\`, IPD-M113): a reviewed/ready-to-execute plan must carry \`- Readiness:\`, so a`, `body prose` comment).
        - Codemod JSON row: `sites=10`, `rewrites=2` (`standard=2`, `invalid-input=0`), `refusals=8` (`dynamic-construction=5`, `unsupported-shape=1`, `not-equivalent=2`, `hand=8`, `legacy-kept=0`), `before_hash=0774552912900f86d346cf861fdc0529f5659d5f239aea0e1872c1b94a8bab0c`, `after_hash=0774552912900f86d346cf861fdc0529f5659d5f239aea0e1872c1b94a8bab0c`, `equivalent=true`, `pytest_runs=6`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 10 | 4 | 0 | 5 | 1 | 0 | 0 | 0 | 0 | 0 | 6 | 0`.
      - `tests/test_host_capability_wiring.py`:
        - F-01 `rg -c`: before 1, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=1`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=3cae3e2209fdc869bf8d5e15e2cee1527fdfae843520df3d15eadd886599a1ff`, `after_hash=3cae3e2209fdc869bf8d5e15e2cee1527fdfae843520df3d15eadd886599a1ff`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_hostcapgate_execute_requirement.py`:
        - F-01 `rg -c`: before 1, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=2`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=2` (`unsupported-shape=2`, `hand=2`, `legacy-kept=0`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 0`.
      - `tests/test_isolation_per_action.py`:
        - F-01 `rg -c`: before 3, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=3`, `rewrites=3` (`standard=3`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=3bc97cafe49400de2cde7318d91b9328cc0ebba90ffb0cce769135e585139a7a`, `after_hash=3bc97cafe49400de2cde7318d91b9328cc0ebba90ffb0cce769135e585139a7a`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
    - Hand count: 10 (8 static + 2 apply-time `not-equivalent`; <= 25). Every hand-converted site:
      1. `tests/test_freeze_time_refusal.py` pre-edit line 74 (`dynamic-construction`, `deps_line` in `_write_plan`).
      2. `tests/test_freeze_time_refusal.py` pre-edit line 81 (`dynamic-construction`, `readiness_line` in `_write_plan`).
      3. `tests/test_freeze_time_refusal.py` pre-edit line 84 (`dynamic-construction`, `approval_line` approved branch in `_write_plan`).
      4. `tests/test_freeze_time_refusal.py` pre-edit line 86 (`dynamic-construction`, `approval_line` override branch in `_write_plan`).
      5. `tests/test_freeze_time_refusal.py` pre-edit lines 88-150 (`dynamic-construction`, plan template in `_write_plan`; sites 1-5 replaced by `RecordBuilder(repo).plan(...)`).
      6. `tests/test_freeze_time_refusal.py` pre-edit lines 166-171 (`not-equivalent`, malformed spec in `_write_spec`; replaced at call site by `RecordBuilder(repo).spec(..., history=[])` so `attention.history-missing` fires).
      7. `tests/test_freeze_time_refusal.py` pre-edit lines 173-186 (`unsupported-shape`, valid spec with `- Slug:` in `_write_spec`; replaced at call sites by `RecordBuilder(repo).spec(..., slug="spec", ...)`).
      8. `tests/test_freeze_time_refusal.py` pre-edit lines 202-204 (`not-equivalent`, malformed backlog in `_write_backlog`; replaced at call site by `RecordBuilder(repo).backlog(..., raw_fields={"priority": None})`, `invalid-input` escape so `backlog.priority-invalid` fires).
      9. `tests/test_hostcapgate_execute_requirement.py` pre-edit line 368 cols 20-47 (`unsupported-shape`, `"- Item-Dependencies: none"` in `test_refused_item_cascades_dependents_and_independent_items_continue`).
      10. `tests/test_hostcapgate_execute_requirement.py` pre-edit line 368 cols 49-87 (`unsupported-shape`, `"- Item-Dependencies: executed:ref001"` in `test_refused_item_cascades_dependents_and_independent_items_continue`; sites 9-10 replaced by `RecordBuilder(repo).plan(...)` for `dep001` and `ind001`).
    - E-09 helper census (`rg -n -o 'def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*'`):
      - Before (3): `tests/test_freeze_time_refusal.py`: `def _write_plan` (line 55), `def _write_spec` (line 155), `def _write_backlog` (line 191).
      - After (1): `tests/test_freeze_time_refusal.py`: `def _write_plan` (line 56).
      - Deleted helpers (2): `tests/test_freeze_time_refusal.py`: `_write_spec`, `_write_backlog` (no external callers; all internal calls replaced directly with `RecordBuilder(repo)`).
      - Surviving E-09 helpers (1): `tests/test_freeze_time_refusal.py`: `_write_plan` — retained as a thin `RecordBuilder(repo).plan(...)` wrapper with zero legacy template strings because two out-of-scope test modules import it directly (`tests/test_attended_session.py` and `tests/test_run_proposal_channel.py`; both verified passing: `20 passed in 3.39s`).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G5b-v1t2ai-2-files.txt` and the empty `diff .aw/state/59aiyh/G5b-v1t2ai-2-before.txt .aw/state/59aiyh/G5b-v1t2ai-2-after.txt`; then, for each of `tests/test_prior_attempt_projection.py`, `tests/test_reaskscore_composed.py`, `tests/test_red_ci_stop.py`, `tests/test_runfresh_end_to_end.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G5b-v1t2ai-2-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); the outcome lists are run with the batch rule's `-m ""`, so `slow` tests are included; paste the count of `slow` node ids in the list; and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G5b-v1t2ai-2-files.txt`:
      - `tests/test_prior_attempt_projection.py`
      - `tests/test_reaskscore_composed.py`
      - `tests/test_red_ci_stop.py`
      - `tests/test_runfresh_end_to_end.py`
    - Outcome diff (`diff -u .aw/state/59aiyh/G5b-v1t2ai-2-before.txt .aw/state/59aiyh/G5b-v1t2ai-2-after.txt`): empty output, exit code 0 (33 `PASSED` outcomes; `slow` node id count: 6 via `python3 -m pytest -o addopts="" -m "slow" --collect-only -q`, all 6 tests in `tests/test_runfresh_end_to_end.py`).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_prior_attempt_projection.py`:
        - F-01 `rg -c`: before 1, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=1`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=3352752736bab61d10bd6ecffc08f1cde392315f19f2b76f02215a66fb9685a3`, `after_hash=3352752736bab61d10bd6ecffc08f1cde392315f19f2b76f02215a66fb9685a3`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_reaskscore_composed.py`:
        - F-01 `rg -c`: before 3, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=3`, `rewrites=3` (`standard=3`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=9c796173f945f13561161d8b3e1dbe7187dcfbb7e25b02043a85f74fb42ad097`, `after_hash=9c796173f945f13561161d8b3e1dbe7187dcfbb7e25b02043a85f74fb42ad097`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 3 | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_red_ci_stop.py`:
        - F-01 `rg -c`: before 11, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=1`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=1` (`not-equivalent=1`, `hand=1`, `legacy-kept=0`), `before_hash=562b6a14854948e173dd502a3ea68abd5dfb3e949cdfc8ba68b8d64005f33cd7`, `after_hash=562b6a14854948e173dd502a3ea68abd5dfb3e949cdfc8ba68b8d64005f33cd7`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_runfresh_end_to_end.py`:
        - F-01 `rg -c`: before 39, after 9. Remaining matches (9): lines 156, 157, 160, 167, 168, 170, 171 (7 lines inside `_FAKE_HOST_SCRIPT` embedded fake-agent subprocess script, `body prose`, codemod `legacy-kept`), line 644 (`# 3. Orchestrator file under executed/ with - Status: executed`, `body prose` comment), line 656 (`self.assertIn("- Status: executed", orch_executed_text)`, `setter-byte assertion`, codemod `legacy-kept`).
        - Codemod JSON row: `sites=9`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=9` (`unsupported-shape=4`, `not-equivalent=2`, `setter-byte assertion=1`, `body prose=2`, `hand=6`, `legacy-kept=3`), `before_hash=acbe6d8eb4a71d788dcb86beb4f843f0e8b8f09ef4f51e60f4a0b654a22b0705`, `after_hash=acbe6d8eb4a71d788dcb86beb4f843f0e8b8f09ef4f51e60f4a0b654a22b0705`, `equivalent=true`, `pytest_runs=4`.
        - `653ndz` F-30 row: `G5b | v1t2ai | 9 | 2 | 2 | 0 | 4 | 0 | 0 | 0 | 1 | 2 | 4 | 3`.
    - Hand count: 7 (4 static + 3 apply-time `not-equivalent`; <= 25). Every hand-converted site:
      1. `tests/test_red_ci_stop.py` pre-edit lines 23-88 (`not-equivalent`, `PLAN_TEMPLATE`; deleted along with `_write_plan` and replaced by `RecordBuilder(repo).plan(...)` inside `_setup_repo`).
      2. `tests/test_runfresh_end_to_end.py` pre-edit lines 35-106 (`not-equivalent`, `_ORCHESTRATOR_TEMPLATE`; deleted and replaced by `RecordBuilder(fixture).plan(...)` in `make_runfresh_fixture`).
      3. `tests/test_runfresh_end_to_end.py` pre-edit lines 108-176 (`not-equivalent`, `_CHILD_TEMPLATE`; deleted and replaced by `RecordBuilder(fixture).plan(...)` in `make_runfresh_fixture`).
      4. `tests/test_runfresh_end_to_end.py` pre-edit line 444 cols 16-38 (`unsupported-shape`, `"- Status: approved\n"` in `test_e01_pre_run_linter_drift`).
      5. `tests/test_runfresh_end_to_end.py` pre-edit line 444 cols 40-84 (`unsupported-shape`, `f"- Status: executed\n- {_PROBE_FIELD}: x\n"` in `test_e01_pre_run_linter_drift`).
      6. `tests/test_runfresh_end_to_end.py` pre-edit line 448 (`unsupported-shape`, `"## Workflow history\n"` in `test_e01_pre_run_linter_drift`).
      7. `tests/test_runfresh_end_to_end.py` pre-edit line 449 (`unsupported-shape`, `"## Workflow history\n- 2026-10-06 executed (tester): executed\n"` in `test_e01_pre_run_linter_drift`; sites 4-7 replaced by `RecordBuilder(fixture_root).plan(..., disposition="executed", status="executed", approval=None, raw_fields={..., _PROBE_FIELD: "x"})`).
    - E-09 helper census (`rg -n -o 'def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*'`):
      - Before (1): `tests/test_red_ci_stop.py`: `def _write_plan` (line 135).
      - After (0): none.
      - Deleted helpers (1): `tests/test_red_ci_stop.py`: `_write_plan` (sole caller `_setup_repo` now calls `RecordBuilder(repo).plan(...)` directly).
      - Surviving E-09 helpers (0): none.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `diff` of the sorted concatenation of the `-before.txt` lists of `G5b-v1t2ai-1`, `G5b-v1t2ai-2` against `.aw/state/59aiyh/v1t2ai-union-after.txt` (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit v1t2ai` output listing only Scope-Paths.
  - Observed evidence:
    - Union diff (`diff -u <(sort .aw/state/59aiyh/G5b-v1t2ai-1-before.txt .aw/state/59aiyh/G5b-v1t2ai-2-before.txt) .aw/state/59aiyh/v1t2ai-union-after.txt`): empty output, exit code 0 (85 `PASSED` outcomes across all 8 modules).
    - Post-edit codemod dry-run over all 8 modules (`python3 tools/fixture_codemod.py --dry-run --format json`): `sites=2`, `rewrites=0`, `hand=0`, `legacy-kept=2` (both in `tests/test_runfresh_end_to_end.py`: `_FAKE_HOST_SCRIPT` `body prose` and line 656 `setter-byte assertion`).
    - Core gate (`aw suite`, running bare core `python3 -m pytest` with bounded xdist workers): `2661 passed, 11 warnings in 103.25s (0:01:43)`, exit code 0 (0 failures; `CORE TIER BUDGET EXCEEDED` warning only because host 1-minute load average was 7.85 on 12 CPUs and `AW_CORE_BUDGET_ENFORCE=0`; none of `v1t2ai`'s 8 modules appeared in the top-10 slowest or slow-tests report).
    - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6869,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw commit v1t2ai` (8 modified test Scope-Paths): `aw commit: committed 8 path(s): 961d0d76250ebb1e45077480461ad17306323bd6` (`tests/test_freeze_time_refusal.py`, `tests/test_host_capability_wiring.py`, `tests/test_hostcapgate_execute_requirement.py`, `tests/test_isolation_per_action.py`, `tests/test_prior_attempt_projection.py`, `tests/test_reaskscore_composed.py`, `tests/test_red_ci_stop.py`, `tests/test_runfresh_end_to_end.py`). Followed by the plan-evidence commit via `aw commit v1t2ai -- .aw/records/plans/pending/20261109-metastore-193-v1t2ai-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md` (recorded in the lane execution report and outcome JSON).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45` are executed. Every open question is resolved.

Safety stop: if a prerequisite plan in `- Item-Dependencies:` is not executed or required builder symbols from `9rgn2w` or codemod from `653ndz` are absent, stop and report rather than proceeding. Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a module cannot keep its outcome list identical without a production change, stop that item and report the missing capability rather than changing production code or an assertion.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit v1t2ai -- <paths>` with only Scope-Paths files; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize v1t2ai` itself.
