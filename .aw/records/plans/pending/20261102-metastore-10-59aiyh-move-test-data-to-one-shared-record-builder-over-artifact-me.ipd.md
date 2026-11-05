# IPD: Move test data to one shared record builder over artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files; C10a requires the suite to pass at every commit, including the cutover commit. Measured 2026-11-02 at `0cbfcc706`: 309 of 717 Python files under `tests/` (307 test modules plus `tests/support.py` and `tests/conformance_matrix.py`) contain 6,638 lines with a legacy bullet string (`- Id:`, `- Status:`, `- Set:` and 18 other metadata fields) or `## Workflow history`; 88 private helper functions in 60 modules build plans, specs, backlog items, reviews, research and prompts by hand (24 copies of `_write_plan`, 12 of `_write_spec`, 7 of `_write_backlog_item`); 7 modules hand-write `aw-prompt` comments; 40 tracked `.md` fixtures under `tests/fixtures/` carry bullet metadata. The one existing shared helper, `support.ready_plan_text`, is used by 14 modules. If the cutover had to rewrite these strings, the cutover commit would carry thousands of test edits and C10a would be unverifiable.
- Scope: Phase B step 6 (`4sd62s` section 7). Add `tests/record_builder.py`, one builder that creates every record type (plan, spec, backlog item, research report, release, staged prompt, walkthrough, review) in a fixture repository through `artifact_meta` (its write path when available, and in phase B the legacy on-disk format that the legacy loader reads), plus a text form for tests that need a string. Move test DATA in the 309 files onto it in six family batches: every hand-built record becomes a builder call. Keep assertions on observable output (CLI text, JSON fields, exit codes) and change no assertion unless the assertion inspected the raw record bytes as a stand-in for metadata, in which case it moves to `artifact_meta.read` (listed per batch). Convert the 40 `.md` fixtures that tests load as records into builder calls or builder-generated files. EXCLUDES: changing production code; tests whose subject IS the legacy text format (the legacy loader tests of `tve77h` and the migration tests of `dcerjg`/`ya4ee4`, which must keep literal legacy input), which are listed and left unchanged; changing the builder's on-disk output to the log format (Order 13, `cxxmyv`).
- Scope-Paths: tests/record_builder.py, tests/support.py, tests/conformance_matrix.py, tests/test_record_builder.py, tests/test_*.py, tests/fixtures/attnview/**, tests/fixtures/review-pilot/**, tests/fixtures/conforming-orchestrator.md, .aw/records/plans/pending/20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md
- Item-Dependencies: executed:tve77h
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 10
- Highest E allocated: 12
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 59aiyh

## Workflow history
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every test that needs a record gets it from one builder, so that the cutover switches the test corpus to the log format by changing one module, and the suite proves C10a at the cutover commit without rewriting test data.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item: (1) record the batch's per-file pass/fail list on the unmodified tests (`python3 -m pytest -o addopts="" -p no:randomly -q <files> -rA | grep -E "PASSED|FAILED|ERROR|SKIPPED"` sorted); (2) replace hand-built records with builder calls; (3) re-run and require the identical per-test result list; (4) count remaining legacy strings with the F-01 `rg` pattern and list each remaining file with its reason (an assertion on displayed output, a test of the legacy format itself, or body prose such as open-question `- Status: open` rows, which N3 keeps in Markdown). The builder never reads production source and no test gains a source-reading assertion.

### Task group 1: the builder

- [ ] E-01 Create `tests/record_builder.py` with one `RecordBuilder(repo_root)` and one function per type: `plan(...)`, `spec(...)`, `backlog(...)`, `research(...)`, `release(...)`, `prompt(...)`, `walkthrough(...)`, `review(subject, rounds=...)`, each taking registry field names (`status`, `set`, `order`, `plan_role`, `item_dependencies`, `blocks_release`, `from_backlog`, `readiness`, `approval`, `gate_kind`, `gate_ref`, `short_description`, ...) plus `history=[...]` events and `body=` prose, and returning the created `Path`. It validates every field name and value through the `artifact_meta` registry (`artifact_meta.registry_fields`, `artifact_meta.validate_event`) so a misspelled field fails the test at build time. In phase B it renders the legacy format exactly as today's writers do (bullet block, `## Workflow history`, research YAML, `aw-prompt` comment, review front matter and `## Round <n>` sections), places the file at the canonical clustered name and disposition directory, and offers `text_only=True` returning the string for tests that pass text. One module-level switch, `RECORD_FORMAT`, names the format (`"legacy"` now); Order 13 adds `"log"`. Supersedes `support.ready_plan_text`, which becomes a thin call into `plan(...)` with the same signature.
  - Depends on: none
  - Expected outcome: `RecordBuilder(tmp).plan(status="approved", set="demo", order=1)` writes a plan that `aw ipd lint` and `artifact_meta.read` accept; a misspelled field raises naming the field.
  - Execution state: pending

- [ ] E-02 Add `tests/test_record_builder.py` (core): for each type, a built record round-trips through `artifact_meta.read` with every field equal to the builder input; a built plan lints `conforming` at the `pre-execution` checkpoint when given `support.ready_plan_text`'s defaults; `aw find`, `aw attention --format json` and `aw check all --agent` see each built record; byte equality between `support.ready_plan_text(...)` before E-01 and after it for its 29 existing call sites' argument sets; and an unknown field, an illegal status for the type and an over-long `short_description` each raise.
  - Depends on: E-01
  - Expected outcome: the module passes and runs under 3 s.
  - Execution state: pending

### Task group 2: migrate the high-density families

- [ ] E-03 Batch G1, backlog and release-gate tests (37 files, 1,525 legacy lines, F-03): `test_backlog*`, `test_release*`, `test_releases*`, `test_graduat*`, `test_gate_*`, `test_blocks_release*`, `test_handoff*`, `test_from_backlog*`, `test_live_bug*`, `test_*close*`, `test_carrier*`, `test_durable_carrier*`. Apply the batch rule.
  - Depends on: E-02
  - Expected outcome: identical per-test result list before and after; remaining legacy-string count for the batch and its per-file reasons pasted.
  - Execution state: pending

- [ ] E-04 Batch G2, check-engine tests (22 files, 1,102 legacy lines): `test_check*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`. Apply the batch rule.
  - Depends on: E-02
  - Expected outcome: identical per-test result list before and after; remaining count and reasons pasted.
  - Execution state: pending

- [ ] E-05 Batch G3, setter and spec tests (28 files, 792 legacy lines): `test_status*`, `test_spec*`, `test_specs*`, `test_set_*`, `test_scaffold*`, `test_ipd_authoring*`, `test_descriptive*`, `test_bidi*`. Tests that assert the bytes a SETTER wrote (for example `test_status_set.py` checking the rewritten `- Status:` line) keep that assertion in phase B, because the written format is the subject; each such assertion is listed so Order 13 can convert it to `artifact_meta.read` plus the in-file mirror.
  - Depends on: E-02
  - Expected outcome: identical per-test result list; remaining count, reasons and the list of setter-byte assertions pasted.
  - Execution state: pending

### Task group 3: migrate plan, lifecycle and runner tests

- [ ] E-06 Batch G4, plan, lint, lifecycle, finalize and orchestration tests (64 files, 1,257 legacy lines): `test_ipd*`, `test_plan*`, `test_plans*`, `test_finalize*`, `test_lifecycle*`, `test_scope*`, `test_executed*`, `test_exec*`, `test_question*`, `test_dependency*`, `test_orchestrator*`, `test_coverage*`, `test_gradcover*`, `test_readiness*`, `test_partition*`, `test_unresolved*`, `test_terminal*`, `test_implementing*`. Open-question rows (`- Blocking:`, `- Status: open`, `- Carrier:`) are body prose (N3) and are written through the builder's `body=` or `open_questions=` argument, never as metadata.
  - Depends on: E-02
  - Expected outcome: identical per-test result list; remaining count and reasons pasted.
  - Execution state: pending

- [ ] E-07 Batch G5, runner and lane tests (48 files, 639 legacy lines): `test_oc_*`, `test_agy*`, `test_runner*`, `test_run_*`, `test_runs_*`, `test_lane*`, `test_records_only*`, `test_merge*`, `test_integrat*`, `test_isolation*`, `test_freeze*`, `test_typed_queue*`, `test_attempt*`, `test_attended*`, `test_turn*`, `test_verifier*`, `test_runwire*`, `test_runfresh*`, `test_red_ci*`, `test_silent*`, `test_prior*`, `test_reask*`, `test_hostcap*`, `test_host*`, `test_fixfirst*`, `test_fix_it*`, `test_clean_target*`, `test_commit*`, `test_work_*`, `test_ipdrunner*`, `test_stdin*`. Tests that build a two-branch merge or a lane worktree commit builder-made records on each branch with real `git`.
  - Depends on: E-02
  - Expected outcome: identical per-test result list (this batch includes `slow` modules; run them with `-m ""`); remaining count and reasons pasted.
  - Execution state: pending

### Task group 4: migrate reader tests, helpers and fixtures

- [ ] E-08 Batch G6, reader and record-surface tests (99 files, 1,199 legacy lines): `test_find*`, `test_attention*`, `test_history*`, `test_selector*`, `test_cli*`, `test_front_matter*`, `test_record*`, `test_artifact*`, `test_rename*`, `test_group*`, `test_research*`, `test_prompt*`, `test_prompts*`, `test_walkthrough*`, `test_read*`, `test_resolver*`, `test_reference*`, `test_review*`, `test_reviews*` and the remaining reader-surface modules of F-03. The `aw-prompt` comment tests (7 files) use `prompt(...)`. Tests whose subject is the legacy grammar itself (`test_front_matter_loose_whitespace.py`, `test_history_block_bounding.py`, `test_selector_two_dialect_readers.py` quoted-example cases) keep their literal input and are listed.
  - Depends on: E-02
  - Expected outcome: identical per-test result list; remaining count and reasons pasted.
  - Execution state: pending

- [ ] E-09 Batch G7, the 11 unclassified files and the shared helpers (124 legacy lines): `tests/support.py` (`ready_plan_text`, `scope_drift_repo`), `tests/conformance_matrix.py` fixture records, `test_action_table_runner_parity.py`, `test_already_landed_dispatch.py`, `test_authoring_coverage_guidance.py`, `test_completion.py`, `test_receipt_lane_record.py`, `test_rereview_reviewed_plan.py`, `test_resolve_plan_path_typed.py`, `test_staged_illegal_backlog_transition_gate.py`, `test_workflow_artifacts_prune.py`; then delete every private `_write_plan`/`_write_spec`/`_write_backlog_item`/`_make_item`/`_mk_plan`/... helper that no longer has a caller (88 helpers at measurement).
  - Depends on: E-03, E-04, E-05, E-06, E-07, E-08
  - Expected outcome: identical per-test result list; `rg --no-filename -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*" tests` count pasted before (88) and after, each survivor listed with its reason.
  - Execution state: pending

- [ ] E-10 Convert the 40 tracked `.md` fixtures that carry bullet metadata (`tests/fixtures/attnview/specs-valid` 9, `tests/fixtures/attnview/violations` 7, `tests/fixtures/review-pilot/plans` 9, `tests/fixtures/conforming-orchestrator.md` 1, and the rest found by `git ls-files tests/fixtures tests/benchmark_fixtures | grep '\.md$'`): a fixture that a test copies into a repository is replaced by a builder recipe in the consuming test (`test_attention.py`, `test_attention_stem.py`, `test_attention_contract.py`, `test_review_pilot.py`, `test_specs_verbs.py`, `test_specs_releases_unsafe_field.py`), or regenerated from the builder by a `tests/fixtures/README.md`-documented command if the test needs a checked-in file; a fixture whose purpose is malformed legacy input (the `violations` set) stays literal and is listed.
  - Depends on: E-02
  - Expected outcome: the consuming tests' per-test result lists are identical; the converted and kept fixture lists are pasted.
  - Execution state: pending

### Task group 5: prove the switch point and finish

- [ ] E-11 Prove that the builder is the single switch point: add to `tests/test_record_builder.py` a test that monkeypatches `record_builder.RECORD_FORMAT` to an unknown value and asserts every builder function raises (so no test can bypass the switch by building records another way through the builder), and run the F-01 `rg` pattern over `tests/` to produce table F-06 in this plan: every remaining legacy string with its file and reason class (legacy-format subject, displayed-output assertion, setter-byte assertion for Order 13, body prose). Compare with the 6,638-line baseline.
  - Depends on: E-09, E-10
  - Expected outcome: the test passes; F-06 has no row without a reason class; the remaining-line count is pasted.
  - Execution state: pending

- [ ] E-12 Finish: run `python3 -m pytest -o addopts="" -p no:randomly -q tests -rA` result list before E-03 and now and show the per-test result multiset is identical (10,469 tests collected at measurement); run the bare core gate `python3 -m pytest` (within its 30 s budget; record wall time before and after, since the builder must not slow the core tier by more than 10 percent), `make test-all`, `aw check`, and `aw sanitize --agent`; commit through `aw commit 59aiyh -- <each changed path>` (one commit per batch is allowed, each through `aw commit`). Never push.
  - Depends on: E-11
  - Expected outcome: identical result multiset; core wall time within 10 percent of the baseline; all runs pass.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`): `artifact_meta.registry_fields(type)`, `artifact_meta.validate_event`, `artifact_meta.read(id6) -> State`, `artifact_meta.create(...)` and `artifact_meta.append(id6, events, *, expect_seq)` (the log-format write path, switched on at the cutover). In phase B the on-disk format is the bullet format, so the builder renders it; the legacy loader reads it into the cache.
- The existing shared plan builder is `support.ready_plan_text`, which is "BUILT FROM THE REAL GENERATOR (`ipd_authoring.build_skeleton`)" and then fills the fields a draft leaves open; the builder keeps that approach for plans, so a scaffold change still reaches every fixture.
- Shared test plumbing lives in `tests/support.py` (`init_repo`, `git`, `run_cli`, `pinned_env`, `ready_plan_text`, `scope_drift_repo`); `tests/repo_template.py` (`copy_template_repo`) gives a pre-built repository; there is no `tests/conftest.py`, and the root `conftest.py` owns tier selection.
- Tests are behavioral (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); core modules set `pytestmark = pytest.mark.core`; `slow` modules are listed in `tests/slow_allowlist.txt`.
- Filenames come from `artifact_naming.build_clustered_name` and parse with `artifact_naming.parse_clustered`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured 2026-11-02 at `0cbfcc706`.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l --glob '*.py' -e '- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|## Workflow history' tests` lists 309 files (307 test modules, `support.py`, `conformance_matrix.py`) of 717 Python files; 6,638 matching lines. The narrower `- Id:`/`- Status:`/`## Workflow history` pattern: 300 files, 3,430 lines | Spec section 6 counted 268 of 680 files and 2,607 matches at round 2; the plan's pattern is broader (21 fields). |
| F-02 | Distribution: 44 files have 40 or more matching lines, 126 have 10 to 39, 139 have fewer than 10; top files `test_check_engine_release_gate.py` 442, `test_status_set.py` 216, `test_backlog.py` 205, `test_releases_line_writers.py` 151, `test_graduated_closable_warning.py` 148, `test_check_engine.py` 146 | Effort is concentrated: about 170 files hold 6,056 of the 6,638 lines. |
| F-03 | Family split by filename prefix: G1 backlog/release gates 37 files, 1,525 lines; G2 check engine 22, 1,102; G3 setter/specs 28, 792; G4 plan/lint/lifecycle/orchestration 64, 1,257; G5 runners/lanes 48, 639; G6 readers/record surfaces 99, 1,199; G7 unclassified and helpers 11, 124 | Seven batches (E-03 to E-09), each one focused pass. |
| F-04 | 88 private record-building helpers in 60 modules (`_write_plan` 24, `_write_spec` 12, `_write_backlog_item` 7, `_make_item` 5, `write_plan` 3, `_mk_plan` 3, `_make_plan_text` 3, others 31); by type: plan 43, spec 15, backlog 16, review 5, research 4, release 2, prompt 1, walkthrough 0; `support.ready_plan_text` is used by 14 modules (29 calls) | The builder replaces these helpers. |
| F-05 | 7 test modules hand-write `aw-prompt` comments; 40 tracked `.md` fixtures carry bullet metadata (`fixtures/attnview/specs-valid` 9, `fixtures/attnview/violations` 7, `fixtures/review-pilot/plans` 9, `fixtures/conforming-orchestrator.md` 1, others); 58 `ipd_lint.lint_text(` calls in 10 test modules pass plan text | The builder needs a text form (`text_only=True`) and a prompt form. |
| F-06 | (written by E-11) remaining legacy strings in `tests/` after the batches, each with a reason class | Order 13 changes the builder plus the F-06 rows of class "setter-byte assertion"; every other class is either a legacy-format test (moved to the migration tests at the cutover) or prose. |
| F-07 | `python3 -m pytest --collect-only -q -o addopts="" tests` collects 10,469 tests | Baseline for E-12's result-multiset comparison. |

## Proposed changes (ordered, validatable)

1. Build and test the shared builder (E-01, E-02).
2. Migrate the backlog/release, check-engine and setter families (E-03 to E-05).
3. Migrate the plan/lifecycle and runner families (E-06, E-07).
4. Migrate the reader family, the helpers and the `.md` fixtures (E-08 to E-10).
5. Prove the single switch point, then run the full comparison and commit (E-11, E-12).

## Deferred / out of scope (with reason)

- Adding `RECORD_FORMAT = "log"` (builder writes through `artifact_meta.create`/`append` and the two-key front matter) and converting the F-06 setter-byte assertions to `artifact_meta.read` plus the in-file mirror: both belong in the cutover commit (C10a: one format per commit).
  - Carrier: cxxmyv
- The legacy-format tests that must keep literal input (the legacy loader tests in `tve77h`, the migration round-trip and conversion tests in `dcerjg` and `ya4ee4`).
  - Carrier: dcerjg
- Deleting production parsers (the builder must not depend on them; it validates through the registry only).
  - Carrier: 9o83cr
- Tests added by later Set children (Orders 11 to 13) use the builder from the start; enforcing that is a review concern of those plans.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. No production module changes. `tests/test_*.py` is a glob because the batches touch about 300 modules; each batch's file list is pasted in its V-item, and the finalize scope reconciliation lists every changed file.
- Under-scope: none known. Plan size: 12 E-items in 5 task groups (limits 18 and 5).

## Required tests / validation

New core test module: `tests/test_record_builder.py`. Every batch is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, unchanged assertions, the same outcomes.

Acceptance criteria of `4sd62s`:

- OWNS: none outright. This plan supplies the switch point that makes AC-1b provable at the cutover.
- CONTRIBUTES to AC-1b (owned by `cxxmyv`): the core-tier summary line pasted for this plan's merge (E-12), and the single builder switch (E-11) so the cutover commit passes the thorough tier without a test-data rewrite. CONTRIBUTES to AC-1 (owned by `9o83cr`): the builder validates through the registry and parses nothing itself, so no test helper becomes a second parser.

Commands: `python3 -m pytest -o addopts="" -p no:randomly -q <batch files> -rA` per batch, `tests/test_record_builder.py`, the bare core gate `python3 -m pytest`, `make test-all`, `aw check`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change; implements `4sd62s` section 6 ("Rewrite the test data with ONE shared record builder in phase B") and section 7 step 6. `CONTRIBUTING.md` needs no change in phase B; Order 12 (`90iqr1`) documents the builder for test authors after the cutover.

## Open questions

### OQ-01: Should the plan be split?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No: 12 E-items in 5 task groups. The work is large in files, not in decisions; each batch is mechanical under the batch rule. If a batch proves too large for one pass during execution, split it by the F-02 density boundary (files with 40 or more lines first, the rest second); the largest batch, G6, would split into G6a (`test_find*`, `test_attention*`, `test_history*`, `test_selector*`, `test_cli*`) and G6b (the rest), keeping the plan at 13 E-items. Recommendation strength: medium.

### OQ-02: Does the builder depend on Order 08's `artifact_meta.read_text`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. The builder WRITES records and validates field names and values with the Order 02 registry functions, and `test_record_builder.py` reads built records back with `artifact_meta.read`, which Order 02 provides; text-only records are checked by writing them into a fixture repository. So `- Item-Dependencies: executed:tve77h` is sufficient, as the brief states. Batches may run before or after Orders 06 to 09; each batch's before/after comparison runs against whatever production code is on `main` at that time. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c` output that builds one record of each of the eight types in a temp repository with `RecordBuilder` and prints, for each, the created path and `artifact_meta.read(<id6>)` status, set and order; then `aw ipd lint <built plan>` ending in `conforming`; and the `KeyError`/`ValueError` message raised for `plan(stauts="approved")` naming `stauts`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v --durations=0 tests/test_record_builder.py` with every test PASSED (one round-trip test per type, the lint test, the `aw find`/`aw attention`/`aw check` visibility tests, the `ready_plan_text` byte-equality test over the 29 recorded argument sets, and the three refusal tests) and a total duration under 3 s.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the G1 file list, the `diff` of the sorted before/after per-test result lists (empty), the before and after F-01 `rg -c` totals for the batch, and the per-file reason list for every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the G2 file list, the empty `diff` of the sorted before/after per-test result lists, the before/after F-01 totals for the batch, and the reason list for remaining matches.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the G3 file list, the empty `diff` of the before/after per-test result lists, the before/after F-01 totals, the reason list, and the list of setter-byte assertions kept for Order 13 (file::test and the asserted line).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the G4 file list, the empty `diff` of the before/after per-test result lists, the before/after F-01 totals, and the reason list (open-question body rows shown as written through `body=`/`open_questions=`).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the G5 file list, the empty `diff` of the before/after per-test result lists run with `-m ""` so `slow` modules are included, the before/after F-01 totals, and the reason list.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the G6 file list, the empty `diff` of the before/after per-test result lists, the before/after F-01 totals, and the reason list including the legacy-grammar modules kept literal.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the G7 file list, the empty `diff` of the before/after per-test result lists, and the helper count from `rg --no-filename -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*" tests | wc -l` before (88) and after, with each surviving helper and its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `git ls-files tests/fixtures tests/benchmark_fixtures | grep '\.md$' | xargs grep -l -E '^- (Id|Status):'` before (40 paths) and after, the converted and kept lists with reasons, and the empty `diff` of the before/after per-test result lists of the six consuming modules named in E-10.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_record_builder.py -k switch` PASSED, the F-06 table written into this plan with a reason class on every row, and the remaining-line count compared with 6,638.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the empty `diff` of the sorted full-suite per-test result multisets (`-m ""`, before E-03 vs now) with the collected count; the bare `python3 -m pytest` summary line with wall time before and after (after within 110 percent of before); the `make test-all` summary line; `aw check` with no new errors; the `aw sanitize --agent` result with zero `fail`; and every `aw commit 59aiyh` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` is executed. Scope fence: the paths in `- Scope-Paths:`; no production module may change (a needed production change stops the batch and is reported). Each batch keeps every assertion except those its V-item lists. Commit only through `aw commit 59aiyh -- <paths>` (one commit per batch allowed); never push. Run the batch comparisons, `tests/test_record_builder.py`, `python3 -m pytest` (core gate) and `make test-all`, and paste the actual summary lines. Move the plan to `.aw/records/plans/executed/` only through `aw ipd finalize 59aiyh`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
