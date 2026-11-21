# IPD: Move runner-family, reader, record and review test data chunk 6 of 11 onto the record builder

- Date: 2026-11-09
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13, `cxxmyv`) changes the builder and not hundreds of test files, and C10a requires the suite to pass at every commit. Research `nj8zdp` and the maintainer's ruling ("plans that obtuse and not-too-smart agents won't mess up") set the guidance of at most 5 E-items, 8 work Scope-Paths and about 8 named units per item; `nbfg7w` named up to 25 modules per batch item. This part carries 8 of `nbfg7w`'s modules (subset G6a; 73 F-01 legacy lines at `3d0ddb845`), each item at most 4 modules, converted by the Order-49 codemod (`653ndz`) plus only its census-counted refusals.
- Scope: Chunk 6 of 11 of `nbfg7w` (round-3 split 2026-11-09 per research `nj8zdp` guidance): the 8 test modules named in the items and in F-40, each item one codemod run under the batch rule below, plus a finishing item. EXCLUDES: every other module of the subsets (the other chunk plans and `nbfg7w`); the builder (`9rgn2w`) and the codemod (`653ndz`); the F-03 EXCLUDED modules; production code; the switch-point proof, census and full-suite comparison (`59aiyh` E-11, E-12).
- Scope-Paths: tests/test_find_single_read.py, tests/test_front_matter_loose_whitespace.py, tests/test_read_class_callers_refuse.py, tests/test_read_verb_zero_match_refusal.py, tests/test_resolver_bypass_sites_climb.py, tests/test_selector_echo_sanitization.py, tests/test_selector_precedence_outcomes.py, tests/test_selector_resolver_matrix.py, .aw/records/plans/pending/20261109-metastore-197-f8jntm-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md
- Item-Dependencies: executed:653ndz, executed:9rgn2w, executed:g5hpbb, executed:tve77h, executed:xexn45
- Status: approved
- Readiness: go-pending-approval
- Review-Depth: complex
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 197
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: f8jntm
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-16 approved (aw set): status set to approved
- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED

- 2026-11-14 /plan-review (antigravity/gemini-3.8-flash): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 FIXED; review record .aw/records/reviews/20261109-metastore-197-f8jntm-move-runner-family-reader-record-and-review-test-data-chunk.review.md
- 2026-11-09 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from nbfg7w (round 3, research nj8zdp guidance).

## Goal

Every hand-built record in the 8 test modules named below comes from `tests/record_builder.py`, written by the Order-49 codemod or, for its census-counted refusals only, by hand, with each module's per-test outcomes identical before and after and every remaining legacy string classified.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item of this plan (the `59aiyh` batch rule, restructured 2026-11-08 for the Order-49 fixture codemod `653ndz` per maintainer decision 2026-11-07 "Codemod first, then small runs": the tool performs the mechanical rewrite, and the hand work is bounded by its measured refusals). In it, "E-13's `full-before.txt`" and "the builder's `raw_fields=` escape (E-01)" are items of Order 37 (`9rgn2w`), carried by the round-3 split into Order 170 (`j6o96i`) with the same ids; because `.aw/state/` does not travel between lane worktrees, step 2 always records a fresh before list here. Step 1's partition is restricted to the modules each batch item names (round-3 split 2026-11-09: a subset is now spread over several plans of at most 8 modules each): a module that the partition now places in the item's subset but that no plan names is NOT added here; it is reported, and the finishing item of `nbfg7w` converts it; a named module that no longer matches F-01 is reported and skipped:
1. Before the batch, create `.aw/state/59aiyh/` (`mkdir -p .aw/state/59aiyh`), re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706` or `ac76110f4`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Run the codemod: `python3 tools/fixture_codemod.py --apply --format json $(cat .aw/state/59aiyh/<batch>-files.txt) > .aw/state/59aiyh/<batch>-codemod.json`. It rewrites only the sites whose module outcome list it proved identical (`653ndz` E-03, carried with the same id into Order 172, `y3uowx`, by the round-3 split) and lists every other site as a refusal with a reason code and a disposition (`hand` or `legacy-kept`, the `653ndz` reason-code table).
4. Hand-convert ONLY the refusals with disposition `hand`: the static count is the sum of the `653ndz` F-30 rows of the item's modules (round-3 split 2026-11-09: an item now carries part of a subset, so the subset's F-31 row is context only), and the codemod report adds any apply-time `not-equivalent` refusals; the item's hand count is their sum. If the hand count exceeds 25, stop after step 3 (the proved codemod rewrites may be committed), convert nothing by hand, and report the subset for re-splitting. A hand conversion uses builder calls; a test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`. A refusal with disposition `legacy-kept` stays in legacy form on purpose and is listed with its F-06 reason class.
5. Re-run step 2's command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
6. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
7. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: batch items

- [x] E-01 (carried from `nbfg7w` E-02, batch subset G6a; round-3 split 2026-11-09) Batch G6a, 4 of its 25 modules (the find, attention, CLI, selector, front-matter, read and resolver tests (`test_find*`, `test_attention*`, `test_cli*`, `test_selector*`, `test_front_matter*`, `test_read*`, `test_resolver*`)): `tests/test_find_single_read.py`, `tests/test_front_matter_loose_whitespace.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_read_verb_zero_match_refusal.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_find_single_read` 8, `test_front_matter_loose_whitespace` 2, `test_read_class_callers_refuse` 6, `test_read_verb_zero_match_refusal` 14. Run the codemod on these modules and apply the batch rule with `<batch>` = `G6a-f8jntm-1` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. The `aw-prompt` comment tests use `prompt(...)`. Tests whose subject is the legacy grammar itself (`test_front_matter_loose_whitespace.py`, `test_history_block_bounding.py`, the quoted-example cases of `test_selector_two_dialect_readers.py`) keep their literal input and are listed as `legacy-format subject`. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G6a-f8jntm-1` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

- [x] E-02 (carried from `nbfg7w` E-02, batch subset G6a; round-3 split 2026-11-09) Batch G6a, 4 of its 25 modules (the find, attention, CLI, selector, front-matter, read and resolver tests (`test_find*`, `test_attention*`, `test_cli*`, `test_selector*`, `test_front_matter*`, `test_read*`, `test_resolver*`)): `tests/test_resolver_bypass_sites_climb.py`, `tests/test_selector_echo_sanitization.py`, `tests/test_selector_precedence_outcomes.py`, `tests/test_selector_resolver_matrix.py`. F-01 legacy lines per module at `3d0ddb845` (context, not the bar): `test_resolver_bypass_sites_climb` 16, `test_selector_echo_sanitization` 9, `test_selector_precedence_outcomes` 9, `test_selector_resolver_matrix` 9. Run the codemod on these modules and apply the batch rule with `<batch>` = `G6a-f8jntm-2` (outcome lists identical); hand-convert ONLY the refusals that the `653ndz` F-30 rows of these modules list with disposition `hand`, plus the codemod's apply-time `not-equivalent` refusals, and state their count (at most 25, the batch rule's stop); leave each refusal the census marks `legacy-kept` in legacy form with its reason class. The `aw-prompt` comment tests use `prompt(...)`. Tests whose subject is the legacy grammar itself (`test_front_matter_loose_whitespace.py`, `test_history_block_bounding.py`, the quoted-example cases of `test_selector_two_dialect_readers.py`) keep their literal input and are listed as `legacy-format subject`. These modules held no private record-building helper at the split; a helper found now is deleted when it has no caller, or listed with its reason.
  - Depends on: none
  - Expected outcome: an empty before/after `diff` for the `G6a-f8jntm-2` outcome lists; for each named module, its remaining legacy-string count and the reason class of every remaining line pasted; every deleted and surviving helper listed; the codemod report and the hand count (at most 25) pasted.
  - Execution state: performed

### Task group 2: finish

- [x] E-03 Finish this part: run the batch rule's step-2 command once over every module of this plan (`$(cat .aw/state/59aiyh/G6a-f8jntm-1-files.txt .aw/state/59aiyh/G6a-f8jntm-2-files.txt)`) into `.aw/state/59aiyh/f8jntm-union-after.txt` and confirm it equals the sorted concatenation of the items' `-before.txt` lists; run the bare core gate `python3 -m pytest` and `aw sanitize --agent`; commit through `aw commit f8jntm -- <each changed path>`, one commit per item allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push. (The full-suite comparison stays in `59aiyh` E-12.)
  - Depends on: E-01, E-02
  - Expected outcome: the union comparison is empty; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`): `agent_workflows/artifact_meta.py::registry_fields`, `agent_workflows/artifact_meta.py::validate_event`, `agent_workflows/artifact_meta.py::validate_new_events`, `agent_workflows/artifact_meta.py::read`, `agent_workflows/artifact_meta.py::create` and `agent_workflows/artifact_meta.py::append`. Order 02's `create`/`append` write the log format; `2xwb9b` E-03 adds the phase-B legacy branch of `append` and `xexn45` E-01 routes the phase-B branch of `create` and `append` through `write_legacy`, with `agent_workflows/artifact_meta.py::render_legacy_text` (`xexn45` E-11) as the same renderer over a string. In phase B the on-disk format is the bullet format; the legacy loader reads it into the cache.
- `agent_workflows/review_findings.py::render_review` (pure) and `agent_workflows/review_findings.py::write_review` render and write a `.review.md` record; no CLI calls `write_review` (`xexn45` Findings).
- The existing shared plan builder is `tests/support.py::ready_plan_text`, which is "BUILT FROM THE REAL GENERATOR (`agent_workflows/ipd_authoring.py::build_skeleton`)" and then fills the fields a draft leaves open; the builder keeps that approach for plans, so a scaffold change still reaches every fixture.
- Shared test plumbing lives in `tests/support.py` (`init_repo`, `git`, `run_cli`, `pinned_env`, `ready_plan_text`, `scope_drift_repo`); `tests/repo_template.py` (`copy_template_repo`) gives a pre-built repository; there is no `tests/conftest.py`, and the root `conftest.py` owns tier selection.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); core modules set `pytestmark = pytest.mark.core`; `slow` tests are listed in `tests/slow_allowlist.txt`; `pyproject.toml` `addopts` deselects `slow` and `livecorpus`, so a complete comparison passes `-m ""`, and `pytest-randomly` is installed, so a deterministic order needs `-p no:randomly`.
- `tests/fixtures/review-pilot/` is the input corpus of `tools/review_pilot.py` (`manifest.json` names each plan file, `defects.json` quotes exact text to plant), and `tests/test_review_pilot.py` copies the whole directory into its fixture repository.
- Filenames come from `agent_workflows/artifact_naming.py::build_clustered_name` and parse with `agent_workflows/artifact_naming.py::parse_clustered`.
- Cite code by repo-relative `path::Symbol` identifiers or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (Technical Writing Standard Requirement 7; advisory `IPD-C801`).

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
| `tests/test_find_single_read.py` | G6a | 8 | none | E-01 |
| `tests/test_front_matter_loose_whitespace.py` | G6a | 2 | none | E-01 |
| `tests/test_read_class_callers_refuse.py` | G6a | 6 | none | E-01 |
| `tests/test_read_verb_zero_match_refusal.py` | G6a | 14 | none | E-01 |
| `tests/test_resolver_bypass_sites_climb.py` | G6a | 16 | none | E-02 |
| `tests/test_selector_echo_sanitization.py` | G6a | 9 | none | E-02 |
| `tests/test_selector_precedence_outcomes.py` | G6a | 9 | none | E-02 |
| `tests/test_selector_resolver_matrix.py` | G6a | 9 | none | E-02 |

### Behavior decisions

- D-1 (Chunk 6 execution order relative to other chunk plans, OQ-01). The module lists of all chunk plans are disjoint, each needs the builder (`tests/record_builder.py::RecordBuilder`) and the codemod (`tools/fixture_codemod.py`), and none edits `tests/support.py` (`59aiyh` E-09), allowing independent execution order.
- D-2 (private test helper handling in target modules). None were identified at split or review in this chunk's modules; if any uncalled helper is discovered at conversion time, delete it, or list surviving helper with justification.
- D-3 (hand conversion threshold). Stop after codemod step 3 if hand conversion count exceeds 25, commit proved codemod rewrites, and report subset for re-splitting.
- D-4 (handling invalid-input test cases). Deliberately invalid test inputs (such as `- Status: EXECUTED` or malformed gates) use `RecordBuilder`'s `raw_fields=` argument rather than hand-formatting raw text.
- D-5 (state directory initialization). Explicitly create `.aw/state/59aiyh/` (`mkdir -p .aw/state/59aiyh`) before recording test outcome lists in each lane worktree.

## Proposed changes (ordered, validatable)

```mermaid
flowchart TD
    E01["1. Convert find, front-matter & read modules (E-01)<br/>tests/test_find_single_read.py<br/>tests/test_front_matter_loose_whitespace.py<br/>tests/test_read_class_callers_refuse.py<br/>tests/test_read_verb_zero_match_refusal.py"]
    E02["2. Convert resolver & selector modules (E-02)<br/>tests/test_resolver_bypass_sites_climb.py<br/>tests/test_selector_echo_sanitization.py<br/>tests/test_selector_precedence_outcomes.py<br/>tests/test_selector_resolver_matrix.py"]
    E03["3. Re-run Union, Core Gate & Path-Scoped Commits (E-03)"]

    E01 --> E03
    E02 --> E03
```

1. Convert each item's modules under the batch rule (E-01 to E-02).
2. Re-run the union, the core gate, commit (E-03).

## Deferred / out of scope (with reason)

- The other modules of subset G6a, the partition re-derivation that catches modules no plan names, and the subsets' finishing checks.
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
- Resolution or deferral rationale: Yes. The module lists of all chunk plans are disjoint, each needs the builder (`tests/record_builder.py::RecordBuilder`) and the codemod (`tools/fixture_codemod.py`), and none edits `tests/support.py` (that is `59aiyh` E-09, which runs last). Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `.aw/state/59aiyh/G6a-f8jntm-1-files.txt` and the empty `diff .aw/state/59aiyh/G6a-f8jntm-1-before.txt .aw/state/59aiyh/G6a-f8jntm-1-after.txt`; then, for each of `tests/test_find_single_read.py`, `tests/test_front_matter_loose_whitespace.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_read_verb_zero_match_refusal.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G6a-f8jntm-1-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G6a-f8jntm-1-files.txt`:
      - `tests/test_find_single_read.py`
      - `tests/test_front_matter_loose_whitespace.py`
      - `tests/test_read_class_callers_refuse.py`
      - `tests/test_read_verb_zero_match_refusal.py`
    - Step-1 partition report (G6a modules matching F-01 at HEAD `90643b560` that no plan names, NOT added here and deferred to `nbfg7w` E-06): `tests/test_readers_attention.py`, `tests/test_readers_cache_parity.py`, `tests/test_readers_check_engine.py`, `tests/test_readers_ipd_lint.py`, `tests/test_readers_offline.py`, `tests/test_readers_read_at_gates.py`, `tests/test_readers_selectors_find.py`, `tests/test_selector_scan_once.py`. (`tests/test_readiness_absence_invariant.py` belongs to G4 under the F-03 first-match rule.)
    - Outcome diff (`diff -u .aw/state/59aiyh/G6a-f8jntm-1-before.txt .aw/state/59aiyh/G6a-f8jntm-1-after.txt`): empty output, exit code 0 (33 `PASSED` outcomes).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_find_single_read.py`:
        - F-01 `rg -c`: before 8, after 1. Remaining match (1): line 110 (`# 5: One whose - Status: has trailing prose so plans_index and selectors disagree`, `body prose`, comment). (`PLAN_TEMPLATE` and `RESEARCH_TEMPLATE` use `raw_fields` for `{status}`/`{order}`/`{id6}` template placeholders, `invalid-input` rewrites by the codemod.)
        - Codemod JSON row: `sites=2`, `rewrites=2` (`standard=0`, `invalid-input=2`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=c47663b1874c47ceba61d4f5d9779d1da499ffcab14fdbaf1b9433b3fb3f70c5`, `after_hash=c47663b1874c47ceba61d4f5d9779d1da499ffcab14fdbaf1b9433b3fb3f70c5`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 2 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_front_matter_loose_whitespace.py`:
        - F-01 `rg -c`: before 2, after 2. Remaining matches (2): line 21 (`ONE_SPACE = "- Id: abc123\n- Status: approved\n"`, `legacy-format subject`, literal legacy whitespace-tolerance test input); line 84 (`multi = "- Status: EXECUTED (approved by maintainer)\n"`, `legacy-format subject`, literal legacy single-token status contract test input). Module intentionally left unmodified.
        - Codemod JSON row: `sites=2`, `rewrites=0` (`standard=0`, `invalid-input=0`), `refusals=2` (`legacy-format subject=2`, `hand=0`, `legacy-kept=2`), `before_hash=null`, `after_hash=null`, `equivalent=true`, `pytest_runs=0`.
        - `653ndz` F-30 row: `G6a | f8jntm | 2 | 0 | 0 | 0 | 0 | 0 | 2 | 0 | 0 | 0 | 0 | 2`.
      - `tests/test_read_class_callers_refuse.py`:
        - F-01 `rg -c`: before 6, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=4`, `rewrites=3` (`standard=3`, `invalid-input=0`), `refusals=1` (`unsupported-shape=1`, `hand=1`, `legacy-kept=0`), `before_hash=aac4f914f8be760c0cb8cd859cfd0068fcf0a77af14c102baa06f3905450fae5`, `after_hash=aac4f914f8be760c0cb8cd859cfd0068fcf0a77af14c102baa06f3905450fae5`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 4 | 3 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0`.
      - `tests/test_read_verb_zero_match_refusal.py`:
        - F-01 `rg -c`: before 14, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=5`, `rewrites=2` (`standard=2`, `invalid-input=0`), `refusals=3` (`unsupported-shape=3`, `hand=3`, `legacy-kept=0`), `before_hash=fa08cd2fe7eb1cde086a9ee7cc801a9e27a272037027a1e8b6e75d75f7fc236e`, `after_hash=fa08cd2fe7eb1cde086a9ee7cc801a9e27a272037027a1e8b6e75d75f7fc236e`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 5 | 2 | 0 | 0 | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 0`.
    - Hand count: 4 (4 static + 0 apply-time `not-equivalent`; <= 25). Every hand-converted site:
      1. `tests/test_read_class_callers_refuse.py` pre-edit lines 151-156 (`unsupported-shape`; converted plan seed `pln001` to `RecordBuilder().plan(title="Test Plan", id6="pln001", status="draft", set="plan01", order=1, body="Cites RSCH-arc001 and RSCH-dng999.\n", text_only=True)`).
      2. `tests/test_read_verb_zero_match_refusal.py` pre-edit line 58 (`unsupported-shape`; converted backlog item `b10001` to `RecordBuilder().backlog(id6="b10001", status="open", set="test", order=1, summary="Item One", body="Content.\n", text_only=True)`).
      3. `tests/test_read_verb_zero_match_refusal.py` pre-edit line 62 (`unsupported-shape`; converted backlog item `b20002` to `RecordBuilder().backlog(id6="b20002", status="open", set="test", order=2, summary="Item Two", body="Non-plan.\n", text_only=True)`).
      4. `tests/test_read_verb_zero_match_refusal.py` pre-edit lines 71-82 (`unsupported-shape`; converted review record `self.r1_content` with structured decisions table to `RecordBuilder().review("p10001", subject_type="ipd", reviewed_at="2026-10-12", reviewer="test-agent", verdict="APPROVE", rounds=[{"number": 1, "decisions": [...]}], text_only=True)`).
    - E-09 / `59aiyh` V-09 helper census (`rg -n "(def _(plan|review|backlog|spec|research)[a-z_]*\()|(def (write|ready)_(plan|review)[a-z_]*\()"`):
      - Before (0): none.
      - After (0): none.
      - Deleted helpers (0): none.
      - Surviving helpers (0): none.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `.aw/state/59aiyh/G6a-f8jntm-2-files.txt` and the empty `diff .aw/state/59aiyh/G6a-f8jntm-2-before.txt .aw/state/59aiyh/G6a-f8jntm-2-after.txt`; then, for each of `tests/test_resolver_bypass_sites_climb.py`, `tests/test_selector_echo_sanitization.py`, `tests/test_selector_precedence_outcomes.py`, `tests/test_selector_resolver_matrix.py` separately: its before and after F-01 `rg -c` count, the reason class of every remaining match, its rows of `.aw/state/59aiyh/G6a-f8jntm-2-codemod.json` (rewrites, refusals by reason code and disposition, before and after outcome-list hashes) and its `653ndz` F-30 row; the hand count with every hand-converted site listed (module, line, reason code); and the before and after helper census of the E-09 `rg` pattern over these modules with each deleted and surviving helper and its reason.
  - Observed evidence:
    - `.aw/state/59aiyh/G6a-f8jntm-2-files.txt`:
      - `tests/test_resolver_bypass_sites_climb.py`
      - `tests/test_selector_echo_sanitization.py`
      - `tests/test_selector_precedence_outcomes.py`
      - `tests/test_selector_resolver_matrix.py`
    - Outcome diff (`diff -u .aw/state/59aiyh/G6a-f8jntm-2-before.txt .aw/state/59aiyh/G6a-f8jntm-2-after.txt`): empty output, exit code 0 (59 `PASSED` outcomes).
    - Per-module F-01 counts, remaining classifications, codemod rows, and `653ndz` F-30 rows:
      - `tests/test_resolver_bypass_sites_climb.py`:
        - F-01 `rg -c`: before 16, after 0. Remaining matches: none. (`_PLAN_CONTENT` uses `raw_fields={"Status": "pending"}`, `invalid-input` rewrite by the codemod.)
        - Codemod JSON row: `sites=3`, `rewrites=3` (`standard=2`, `invalid-input=1`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=e6b02f41ba5e10402ab9fc369bf6ebc9b8bc2d7fad0ecc91179e604d80f797c8`, `after_hash=e6b02f41ba5e10402ab9fc369bf6ebc9b8bc2d7fad0ecc91179e604d80f797c8`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 3 | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_selector_echo_sanitization.py`:
        - F-01 `rg -c`: before 9, after 0. Remaining matches: none.
        - Codemod JSON row: `sites=1`, `rewrites=1` (`standard=1`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=738aa47880a209f923eec6fda7764806abc3f3a6764946d3226002b0904f9bbe`, `after_hash=738aa47880a209f923eec6fda7764806abc3f3a6764946d3226002b0904f9bbe`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_selector_precedence_outcomes.py`:
        - F-01 `rg -c`: before 9, after 3. Remaining matches (3): line 41 (`# Several plans declaring \`- Set: demo\``, `body prose`, comment); line 77 (`# Colliding plan declaring \`- Set: other\` whose FILENAME contains \`demo\``, `body prose`, comment); line 92 (`# Colliding plan declaring \`- Set: other\` and \`- Status: draft\` whose FILENAME contains \`approved\``, `body prose`, comment).
        - Codemod JSON row: `sites=6`, `rewrites=6` (`standard=6`, `invalid-input=0`), `refusals=0` (`hand=0`, `legacy-kept=0`), `before_hash=1821c85878291d58d7247aead2b8bfae3e4d67489ba48ac0dce56f045218aa7d`, `after_hash=1821c85878291d58d7247aead2b8bfae3e4d67489ba48ac0dce56f045218aa7d`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 6 | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0`.
      - `tests/test_selector_resolver_matrix.py`:
        - F-01 `rg -c`: before 9, after 1. Remaining match (1): line 361 (`# deliberately because a review has no \`- Status:\` bullet, and \`TYPE_FACET\` is ITERATED by`, `body prose`, comment).
        - Codemod JSON row: `sites=7`, `rewrites=6` (`standard=6`, `invalid-input=0`), `refusals=1` (`unsupported-shape=1`, `hand=1`, `legacy-kept=0`), `before_hash=f292655e602b7e6eebfb60f3307a5129f6e4133299f00b60941b4feee9fd5b9c`, `after_hash=f292655e602b7e6eebfb60f3307a5129f6e4133299f00b60941b4feee9fd5b9c`, `equivalent=true`, `pytest_runs=2`.
        - `653ndz` F-30 row: `G6a | f8jntm | 7 | 6 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0`.
    - Hand count: 1 (1 static + 0 apply-time `not-equivalent`; <= 25). Every hand-converted site:
      1. `tests/test_selector_resolver_matrix.py` pre-edit line 268 (`unsupported-shape`; converted unowned `prompt-library` fixture `self.misc` to `RecordBuilder().walkthrough(id6="ccc333", target_id="ccc333", set="demo", body="# gamma\n", text_only=True)`).
    - E-09 / `59aiyh` V-09 helper census (`rg -n "(def _(plan|review|backlog|spec|research)[a-z_]*\()|(def (write|ready)_(plan|review)[a-z_]*\()"`):
      - Before (0): none.
      - After (0): none.
      - Deleted helpers (0): none.
      - Surviving helpers (0): none.
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `diff` of the sorted concatenation of the `-before.txt` lists of `G6a-f8jntm-1`, `G6a-f8jntm-2` against `.aw/state/59aiyh/f8jntm-union-after.txt` (empty), the bare `python3 -m pytest` summary line and wall time, the `aw sanitize --agent` result with zero `fail`, and every `aw commit f8jntm` output listing only Scope-Paths.
  - Observed evidence:
    - Union diff (`diff -u <(sort .aw/state/59aiyh/G6a-f8jntm-1-before.txt .aw/state/59aiyh/G6a-f8jntm-2-before.txt) .aw/state/59aiyh/f8jntm-union-after.txt`): empty output, exit code 0 (92 `PASSED` outcomes across all 8 modules).
    - Post-edit codemod dry-run over all 8 modules (`python3 tools/fixture_codemod.py --dry-run --format json`): `modules=8`, `sites=2`, `rewrites=0`, `refusals=2` (`legacy-format subject=2`, `hand=0`, `legacy-kept=2`).
    - Core gate (`aw suite`, running bare `python3 -m pytest` with 6 xdist workers): `2661 passed, 11 warnings in 107.67s (0:01:47)`, exit code 0 (0 failures; none of `f8jntm`'s 8 modules appeared in the top-10 slowest or unlisted slow-tests report).
    - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6876,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw commit f8jntm` (7 modified test Scope-Paths): `aw commit: committed 7 path(s): fdbc25367d65d10b04177b7c4cdcdf2f4422c23e` (`tests/test_find_single_read.py`, `tests/test_read_class_callers_refuse.py`, `tests/test_read_verb_zero_match_refusal.py`, `tests/test_resolver_bypass_sites_climb.py`, `tests/test_selector_echo_sanitization.py`, `tests/test_selector_precedence_outcomes.py`, `tests/test_selector_resolver_matrix.py`). Declared Scope-Path `tests/test_front_matter_loose_whitespace.py` was intentionally left unmodified because both of its sites are `legacy-format subject` (`legacy-kept`, per E-01), acknowledged for `--scope-ack` at finalize. Followed by the plan-evidence commit via `aw commit f8jntm -- .aw/records/plans/pending/20261109-metastore-197-f8jntm-move-runner-family-reader-record-and-review-test-data-chunk.ipd.md`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `653ndz`, `9rgn2w`, `g5hpbb`, `tve77h`, `xexn45` are executed. Every open question is resolved. Stop and report without editing production code or tests if prerequisite symbols from `653ndz` (`tools/fixture_codemod.py`) or `9rgn2w` (`tests/record_builder.py::RecordBuilder`) are absent on HEAD, if baseline test suites fail on unmodified HEAD before starting, or if concurrent edits in a shared checkout conflict with `- Scope-Paths:`.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a module cannot keep its outcome list identical without a production change, stop that item and report the missing capability rather than changing production code or an assertion.

Honesty rule: run every command a V-item names and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit f8jntm -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner owns retirement to `executed/` and runs finalize automatically upon task completion; when executed standalone by hand or direct agent turn, the executor runs `aw ipd finalize f8jntm`.
