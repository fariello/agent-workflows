# IPD: Move runner-family, reader, record and review test data chunk 1 of 11 onto the record builder

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. Research `nj8zdp` and the maintainer's ruling ("plans that obtuse and not-too-smart agents won't mess up") set the guidance of at most 5 E-items, 8 work Scope-Paths and about 8 named units per item; `nbfg7w` named up to 25 modules per batch item. This part carries 8 of `nbfg7w`'s modules (subset G5b; 29 F-01 legacy lines at `3d0ddb845`), each item at most 4 modules, converted by the Order-49 codemod (`653ndz`) plus only its census-counted refusals.
- Scope: Chunk 1 of 11 of `nbfg7w` (round-3 split 2026-11-09 per research `nj8zdp` guidance): the 8 test modules named in the items and in F-40, each item one codemod run under the batch rule below, plus a finishing item. EXCLUDES: every other module of the subsets (the other chunk plans and `nbfg7w`); the builder (`9rgn2w`) and the codemod (`653ndz`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_attempt_model_identity.py, tests/test_attended_session.py, tests/test_clean_target_zero_delta_e2e.py, tests/test_commit_default_message.py, tests/test_commit_scope_reason.py, tests/test_fixfirst_end_to_end.py, tests/test_fix_it_global_caps.py, tests/test_fix_it_notice.py, .aw/records/plans/pending/20261109-metastore-192-i29bd5-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: approved
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 192
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: i29bd5
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved
- Readiness: go-pending-approval
- Review-Depth: standard

> Written to `.aw/system/workflows/technical-writing/technical-writing.md`. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history
- 2026-11-16 approved (aw set): status set to approved

- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 FIXED
- 2026-11-14 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 FIXED; review record .aw/records/reviews/20261109-metastore-192-i29bd5-move-runner-family-reader-record-and-review-test-data-chunk.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from nbfg7w (round 3, research nj8zdp guidance).

## Goal

Every hand-built record in the 8 test modules named below comes from `tests/record_builder.py`, written by the Order-49 codemod or, for its census-counted refusals only, by hand, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`), carried by the round-3 split into Order 170 (`j6o96i`) with the same ids; because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the modules each batch item names (round-3 split 2026-11-09: a subset is now spread over several plans of at most 8 modules each): a module that the partition now places in the item's subset but that no plan names is NOT added here; it is reported, and the finishing item of `nbfg7w` converts it; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it: `mkdir -p .aw/state/59aiyh && ... > .aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03, carried with the same id into Order 172, `y3uowx`, by the round-3 split) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 25, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: batch items

- [x] E-01 (carried from `nbfg7w` E-01, batch subset G5b; round-3 split 2026-11-09) Batch G5b, 4 of its 25 modules (the other runner-family tests (`test_integrat*`, `test_isolation*`, `test_freeze*`, `test_typed_queue*`, `test_attempt*`, `test_attended*`, `test_turn*`, `test_verifier*`, `test_runwire*`, `test_runfresh*`, `test_red_ci*`, `test_silent*`, `test_prior*`, `test_reask*`, `test_hostcap*`, `test_host*`, `test_fixfirst*`, `test_fix_it*`, `test_clean_target*`, `test_commit*`, `test_work_*`, `test_ipdrunner*`, `test_stdin*`)): `tests/test_attempt_model_identity.py`, `tests/test_attended_session.py`, `tests/test_clean_target_zero_delta_e2e.py`, `tests/test_commit_default_message.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_attempt_model_identity` 3, `test_attended_session` 1, `test_clean_target_zero_delta_e2e` 2, `test_commit_default_message` 15. Run the codemod on these modules and apply the batch rule with `<batch>` = `G5b-i29bd5-1` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that builds a two-branch merge or a lane worktree commits builder-made records on each branch with real `git`. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G5b-i29bd5-1` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

- [x] E-02 (carried from `nbfg7w` E-01, batch subset G5b; round-3 split 2026-11-09) Batch G5b, 4 of its 25 modules (the other runner-family tests (`test_integrat*`, `test_isolation*`, `test_freeze*`, `test_typed_queue*`, `test_attempt*`, `test_attended*`, `test_turn*`, `test_verifier*`, `test_runwire*`, `test_runfresh*`, `test_red_ci*`, `test_silent*`, `test_prior*`, `test_reask*`, `test_hostcap*`, `test_host*`, `test_fixfirst*`, `test_fix_it*`, `test_clean_target*`, `test_commit*`, `test_work_*`, `test_ipdrunner*`, `test_stdin*`)): `tests/test_commit_scope_reason.py`, `tests/test_fixfirst_end_to_end.py`, `tests/test_fix_it_global_caps.py`, `tests/test_fix_it_notice.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_commit_scope_reason` 1, `test_fixfirst_end_to_end` 4, `test_fix_it_global_caps` 2, `test_fix_it_notice` 1. Run the codemod on these modules and apply the batch rule with `<batch>` = `G5b-i29bd5-2` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. A test that builds a two-branch merge or a lane worktree commits builder-made records on each branch with real `git`. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G5b-i29bd5-2` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

### Task group 2: finish

- [x] E-03 Finish this part: run the batch rule's step-2 command once over every module of this plan (`$(cat .aw/state/59aiyh/G5b-i29bd5-1-files.txt .aw/state/59aiyh/G5b-i29bd5-2-files.txt)`) into `.aw/state/59aiyh/i29bd5-union-after.txt` and confirm it equals the sorted concatenation of the items' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit i29bd5 -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The full-suite comparison stays in `59aiyh` E-12.)
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
| `tests/test_attempt_model_identity.py` | G5b | 3 | none | E-01 |
| `tests/test_attended_session.py` | G5b | 1 | none | E-01 |
| `tests/test_clean_target_zero_delta_e2e.py` | G5b | 2 | none | E-01 |
| `tests/test_commit_default_message.py` | G5b | 15 | none | E-01 |
| `tests/test_commit_scope_reason.py` | G5b | 1 | none | E-02 |
| `tests/test_fixfirst_end_to_end.py` | G5b | 4 | none | E-02 |
| `tests/test_fix_it_global_caps.py` | G5b | 2 | none | E-02 |
| `tests/test_fix_it_notice.py` | G5b | 1 | none | E-02 |

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    A["E-01: Batch G5b-i29bd5-1 (4 runner modules)<br/>Codemod + hand-convert refusals <= 25"] --> B["E-02: Batch G5b-i29bd5-2 (4 runner modules)<br/>Codemod + hand-convert refusals <= 25"]
    B --> C["E-03: Union comparison & core gate<br/>Verify i29bd5-union-after.txt equals concatenated -before lists"]
    C --> D["Commit via aw commit i29bd5"]
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
- Owner: plan author (carried from nbfg7w)
- Resolution or deferral rationale: Yes. The module lists of all chunk plans are disjoint, each needs the builder (`9rgn2w`) and the codemod (`653ndz`), and none edits `tests/support.py` (that is `59aiyh` E-09, which runs last). Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `.aw/state/59aiyh/G5b-i29bd5-1-files.txt` and the empty `diff .aw/state/59aiyh/G5b-i29bd5-1-before.txt .aw/state/59aiyh/G5b-i29bd5-1-after.txt`; then, for each of `tests/test_attempt_model_identity.py`, `tests/test_attended_session.py`, `tests/test_clean_target_zero_delta_e2e.py`, `tests/test_commit_default_message.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G5b-i29bd5-1-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); the outcome lists are run with the batch rule's `-m ""`, so `slow` tests are included; paste the count of `slow` node ids in the list; and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G5b-i29bd5-1-files.txt`:
      - `tests/test_attempt_model_identity.py`
      - `tests/test_attended_session.py`
      - `tests/test_clean_target_zero_delta_e2e.py`
      - `tests/test_commit_default_message.py`
    - Outcome diff (`diff -u .aw/state/59aiyh/G5b-i29bd5-1-before.txt .aw/state/59aiyh/G5b-i29bd5-1-after.txt`): empty output, exit code 0 (33 `PASSED` outcomes; `slow` node id count: 0 via `python3 -m pytest -o addopts="" -m "slow" --collect-only -q`).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_attempt_model_identity.py`:
        - F-01 `rg -c`: before 3, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=2`, `rewrites=2` (`standard=2`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=fffde43acb9525bf8e839f81959960a69f89671e54f74d3cab4e1b3647a94d44`, `after_hash=fffde43acb9525bf8e839f81959960a69f89671e54f74d3cab4e1b3647a94d44`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_attended_session.py`:
        - F-01 `rg -c`: before 1, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=2`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=2` (`unsupported-shape=2` `hand=2`, `legacy-kept=0`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 0`.
      - `tests/test_clean_target_zero_delta_e2e.py`:
        - F-01 `rg -c`: before 2, after 2. Remaining matches (2): line 250 (`m = re.search(r"^- Id:\s*([a-z0-9]{6})", plan_content, re.MULTILINE)`, `body prose`, codemod `legacy-kept`), line 251 (`self.assertIsNotNone(m, "scaffolded plan must have '- Id: <id6>'")`, `setter-byte assertion`, codemod `legacy-kept`). Module left unmodified.
        - Codemod JSON row: `sites=2`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=2` (`setter-byte assertion=1` `legacy-kept=1`, `body prose=1` `legacy-kept=1`, `hand=0`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 2`.
      - `tests/test_commit_default_message.py`:
        - F-01 `rg -c`: before 15, after 4. Remaining matches (4): lines 4, 10, 106, 183 (module and method docstrings referencing `- Id:` behavior, all 4 classified `body prose`).
        - Codemod JSON row: `sites=1`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=ea9b60818147441d6ade47c6e897e4e416f691d7c682ed7796f3e5d6d9e9eb53`, `after_hash=ea9b60818147441d6ade47c6e897e4e416f691d7c682ed7796f3e5d6d9e9eb53`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
    - Hand count: 2 (2 static + 0 apply-time `not-equivalent`; <= 25). Every hand-converted site:
      1. `tests/test_attended_session.py` pre-edit line 73 cols 12-28 (`unsupported-shape`, `"- Id: att004\n"` inside `_attended_repo`).
      2. `tests/test_attended_session.py` pre-edit line 73 cols 30-68 (`unsupported-shape`, `"- Id: att004\n- Attended: required\n"` inside `_attended_repo`).
      Both replaced by `RecordBuilder(repo).plan(id6="att004", ..., attended="required", ...)` inside `_attended_repo`.
    - E-09 helper census (`rg -n -o 'def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*'`):
      - Before (0): none.
      - After (0): none.
      - Deleted helpers (0): none. Surviving E-09 helpers (0): none.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G5b-i29bd5-2-files.txt` and the empty `diff .aw/state/59aiyh/G5b-i29bd5-2-before.txt .aw/state/59aiyh/G5b-i29bd5-2-after.txt`; then, for each of `tests/test_commit_scope_reason.py`, `tests/test_fixfirst_end_to_end.py`, `tests/test_fix_it_global_caps.py`, `tests/test_fix_it_notice.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G5b-i29bd5-2-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); the outcome lists are run with the batch rule's `-m ""`, so `slow` tests are included; paste the count of `slow` node ids in the list; and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G5b-i29bd5-2-files.txt`:
      - `tests/test_commit_scope_reason.py`
      - `tests/test_fix_it_global_caps.py`
      - `tests/test_fix_it_notice.py`
      - `tests/test_fixfirst_end_to_end.py`
    - Outcome diff (`diff -u .aw/state/59aiyh/G5b-i29bd5-2-before.txt .aw/state/59aiyh/G5b-i29bd5-2-after.txt`): empty output, exit code 0 (89 `PASSED` outcomes; `slow` node id count: 0 via `python3 -m pytest -o addopts="" -m "slow" --collect-only -q`).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_commit_scope_reason.py`:
        - F-01 `rg -c`: before 1, after 1. Remaining matches (1): line 468 (`# 4. Finalize with apply=True passes and records reason in ## Workflow history`, `body prose` comment). Module left unmodified.
        - Codemod JSON row: `sites=0`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_fixfirst_end_to_end.py`:
        - F-01 `rg -c`: before 4, after 2. Remaining matches (2): line 235 (`m_order = re.search(r"^- Order:\s*(\S+)", plan_text, re.MULTILINE)`, `body prose`, codemod `legacy-kept`), line 241 (`m_set = re.search(r"^- Set:\s*(\S+)", plan_text, re.MULTILINE)`, `body prose`, codemod `legacy-kept`).
        - Codemod JSON row: `sites=6`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=6` (`unsupported-shape=4` `hand=4`, `body prose=2` `legacy-kept=2`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 6 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 2 | 4 | 2`.
      - `tests/test_fix_it_global_caps.py`:
        - F-01 `rg -c`: before 2, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=4`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=4` (`unsupported-shape=4` `hand=4`, `legacy-kept=0`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 0 | 4 | 0`.
      - `tests/test_fix_it_notice.py`:
        - F-01 `rg -c`: before 1, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=1`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=4fe8ff3f9e88524e63f0fc04eefe13112005444af69e38960600bfda3c6e601e`, `after_hash=4fe8ff3f9e88524e63f0fc04eefe13112005444af69e38960600bfda3c6e601e`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G5b | i29bd5 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
    - Hand count: 8 (8 static + 0 apply-time `not-equivalent`; <= 25). Every hand-converted site:
      1. `tests/test_fixfirst_end_to_end.py` pre-edit line 885 cols 20-40 (`unsupported-shape`, `"- Status: approved"` in `_run_matrix_untooled_status_change`).
      2. `tests/test_fixfirst_end_to_end.py` pre-edit line 885 cols 42-63 (`unsupported-shape`, `"- Status: to-review"` in `_run_matrix_untooled_status_change`).
      3. `tests/test_fixfirst_end_to_end.py` pre-edit line 896 cols 20-41 (`unsupported-shape`, `"- Status: to-review"` in `_run_matrix_untooled_status_change`).
      4. `tests/test_fixfirst_end_to_end.py` pre-edit line 896 cols 43-63 (`unsupported-shape`, `"- Status: approved"` in `_run_matrix_untooled_status_change`).
         Sites 1-4 replaced by `RecordBuilder().plan(..., status="to-review"|"approved", history=["- 2026-10-07 approved (test): created."], raw_fields=raw_id, text_only=True)` inside `_run_matrix_untooled_status_change`.
      5. `tests/test_fix_it_global_caps.py` pre-edit line 718 cols 42-55 (`unsupported-shape`, `"- Set: demo"` in `_setup_driver_fixture`).
      6. `tests/test_fix_it_global_caps.py` pre-edit line 718 cols 57-74 (`unsupported-shape`, `f"- Set: {setid}"` in `_setup_driver_fixture`).
      7. `tests/test_fix_it_global_caps.py` pre-edit line 772 cols 42-55 (`unsupported-shape`, `"- Set: demo"` in `_add_plan_item`).
      8. `tests/test_fix_it_global_caps.py` pre-edit line 772 cols 57-74 (`unsupported-shape`, `f"- Set: {setid}"` in `_add_plan_item`).
         Sites 5-8 replaced by `_create_caps_plan`, which delegates to `RecordBuilder().plan(..., set=setid, scope_paths=f"clash_{id6}.txt", text_only=True)`.
    - E-09 helper census (`rg -n -o 'def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*'`):
      - Before (0): none.
      - After (0): none.
      - Deleted helpers (0): none. Surviving E-09 helpers (0): none. (`_create_caps_plan` in `tests/test_fix_it_global_caps.py` delegates to `RecordBuilder` and does not match the E-09 pattern.)
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `diff` of the sorted concatenation of the `-before.txt` lists of `G5b-i29bd5-1`, `G5b-i29bd5-2` against `.aw/state/59aiyh/i29bd5-union-after.txt` (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit i29bd5` output listing only Scope-Paths.
  - Observed evidence:
    - Union diff (`diff -u <(sort .aw/state/59aiyh/G5b-i29bd5-1-before.txt .aw/state/59aiyh/G5b-i29bd5-2-before.txt) .aw/state/59aiyh/i29bd5-union-after.txt`): empty output, exit code 0 (122 `PASSED` outcomes across all 8 modules).
    - Core gate (`aw suite`, running bare core `python3 -m pytest` with bounded xdist workers): `2661 passed, 11 warnings in 94.63s (0:01:34)`, exit code 0 (0 failures; `CORE TIER BUDGET EXCEEDED` warning only because host 1-minute load average was 5.84 on 12 CPUs and `AW_CORE_BUDGET_ENFORCE=0`; none of `i29bd5`'s 8 modules appeared in the top-10 slowest or slow-tests report).
    - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6863,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw commit i29bd5` (6 modified test Scope-Paths): `aw commit: committed 6 path(s): 29c57325ce72161e1340153c980d1554cb91537a` (`tests/test_attempt_model_identity.py`, `tests/test_attended_session.py`, `tests/test_commit_default_message.py`, `tests/test_fix_it_global_caps.py`, `tests/test_fix_it_notice.py`, `tests/test_fixfirst_end_to_end.py`). Two declared Scope-Paths (`tests/test_clean_target_zero_delta_e2e.py`, `tests/test_commit_scope_reason.py`) had 0 codemod rewrites and 0 `hand` refusals and remain unmodified (acknowledged at finalize). Followed by the plan-evidence commit via `aw commit i29bd5 -- .aw/records/plans/pending/20261109-metastore-192-i29bd5-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md` (recorded in the lane execution report and outcome JSON).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45` are executed. Every open question is resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a module cannot keep its outcome list identical without a production change, stop that item and report the missing capability rather than changing production code or an assertion.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit i29bd5 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize i29bd5`.
