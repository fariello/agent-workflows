# IPD: Move test data to one shared record builder over artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` section 6 requires that test data be written by ONE shared record builder in phase B, so that the cutover (Order 13) changes the builder and not hundreds of test files; C10a requires the suite to pass at every commit, including the cutover commit. Measured 2026-11-02 at `0cbfcc706`: 309 of 717 Python files under `tests/` (307 test modules plus `tests/support.py` and `tests/conformance_matrix.py`) contain 6,638 lines with a legacy bullet string (`- Id:`, `- Status:`, `- Set:` and 18 other metadata fields) or `## Workflow history`; 88 private helper functions in 60 modules build plans, specs, backlog items, reviews, research and prompts by hand (24 copies of `_write_plan`, 12 of `_write_spec`, 7 of `_write_backlog_item`); 7 modules hand-write `aw-prompt` comments; 26 of the 40 tracked `.md` files under `tests/fixtures/` and `tests/benchmark_fixtures/` carry `- Id:` or `- Status:` bullets (27 carry an F-01 string). The one existing shared helper, `support.ready_plan_text`, is used by 14 modules. If the cutover had to rewrite these strings, the cutover commit would carry thousands of test edits and C10a would be unverifiable.
- Scope: Phase B step 6 (`4sd62s` section 7). Add `tests/record_builder.py`, one builder that creates every record type (plan, spec, backlog item, research report, release, staged prompt, walkthrough, review) in a fixture repository through `artifact_meta` (its write path when available, and in phase B the legacy on-disk format that the legacy loader reads), plus a text form for tests that need a string. Move test DATA in the F-01 files onto it in seven family batches (G1 to G7, partitioned by the first-match rule of F-03): every hand-built record becomes a builder call. Keep assertions on observable output (CLI text, JSON fields, exit codes) and change no assertion unless the assertion inspected the raw record bytes as a stand-in for metadata, in which case it moves to `artifact_meta.read` (listed per batch). Convert the tracked `.md` fixtures that tests copy or lint as records into builder calls (E-10). EXCLUDES: changing production code; tests whose subject IS the legacy text format (the legacy loader tests of `tve77h`, the legacy writer tests of `2xwb9b` and `xexn45`, and the migration tests of `dcerjg`/`ya4ee4`, which must keep literal legacy input; the EXCLUDED list in F-03), which are listed and left unchanged; the review-pilot plan corpus that `tools/review_pilot.py` reads (F-05); changing the builder's on-disk output to the log format (Order 13, `cxxmyv`).
- Scope-Paths: tests/record_builder.py, tests/support.py, tests/conformance_matrix.py, tests/test_record_builder.py, tests/test_*.py, tests/fixtures/attnview/**, tests/fixtures/conforming-orchestrator.md, tests/fixtures/record_builder/**, .aw/records/plans/pending/20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.ipd.md
- Item-Dependencies: executed:tve77h, executed:xexn45
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 10
- Highest E allocated: 13
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 59aiyh
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261102-metastore-10-59aiyh-move-test-data-to-one-shared-record-builder-over-artifact-me.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every test that needs a record gets it from one builder, so that the cutover switches the test corpus to the log format by changing one module, and the suite proves C10a at the cutover commit without rewriting test data.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Batch rule, applied to every batch E-item (E-03 to E-09):
1. Before the batch, re-derive its file list with the F-03 first-match partition over the F-01 `rg -l` output at the current HEAD, minus the F-03 EXCLUDED list, and save it as `.aw/state/59aiyh/<batch>-files.txt`. The counts in each E-item are context measured at `0cbfcc706`, not the bar.
2. Record the unmodified per-test outcome list (a batch whose files a previous batch did not touch may reuse the matching lines of E-13's `full-before.txt`): `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA $(cat .aw/state/59aiyh/<batch>-files.txt) | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/59aiyh/<batch>-before.txt`. `-p no:randomly` and `-n 0` make the list deterministic; `-m ""` includes `slow` and `livecorpus` modules.
3. Replace hand-built records with builder calls. A test that deliberately writes an INVALID value (an unknown status, `- Status: EXECUTED`, `- Priority: bogus`, a malformed gate) gets it through the builder's `raw_fields=` escape (E-01) and is listed with reason class `invalid-input`.
4. Re-run the same command into `<batch>-after.txt` and require `diff` to print nothing. A batch that would need any changed assertion other than a raw-byte metadata stand-in moved to `artifact_meta.read` (scope rule) stops and is reported; it does not weaken the assertion.
5. Count the remaining legacy strings with the F-01 `rg` pattern over the batch files, and give each remaining line one reason class from F-06: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, or `body prose` (for example open-question `- Status: open` rows, which N3 keeps in Markdown).
6. The builder never reads production source, and no test gains a source-reading assertion.

### Task group 1: the builder

- [ ] E-13 Capture every baseline BEFORE any edit, under the gitignored `.aw/state/59aiyh/`:
  - the bare `python3 -m pytest` summary line and wall time (`core-before.txt`);
  - the full-suite outcome list (`full-before.txt`), using the E-12 command;
  - `aw check --agent` output (`check-before.jsonl`);
  - the F-01 `rg` count over `tests/` (`legacy-before.txt`);
  - the E-09 helper count (`helpers-before.txt`);
  - the golden bytes of `support.ready_plan_text(**kwargs)` for every distinct argument set its call sites use at HEAD, plus the default call. They go in `tests/fixtures/record_builder/ready_plan_text_golden.json`, a tracked generated file whose generating command E-02 writes in its module docstring.
  - Depends on: none
  - Expected outcome: all six files exist with modification times earlier than the first edit to `tests/support.py` or `tests/record_builder.py`.
  - Execution state: pending

- [ ] E-01 Create `tests/record_builder.py` with one `RecordBuilder(repo_root)` and one method per type: `plan(...)`, `spec(...)`, `backlog(...)`, `research(...)`, `release(...)`, `prompt(...)`, `walkthrough(...)` and `review(subject, rounds=...)`. Each method takes registry field names (`status`, `set`, `order`, `plan_role`, `item_dependencies`, `blocks_release`, `from_backlog`, `readiness`, `approval`, `gate_kind`, `gate_ref`, `short_description`, ...), `history=[...]` events, `body=` prose (and, for plans, `open_questions=`), `disposition=` (a non-default lifecycle directory) and `raw_fields={legacy_name: text}` (inserted verbatim into the metadata block after the validated write and never validated; ONLY for tests whose input is deliberately invalid, F-08). Each method returns the created `Path`. Rules:
  - VALIDATION. Every field name and value outside `raw_fields` is validated through the `artifact_meta` registry (`artifact_meta.registry_fields`, `artifact_meta.validate_new_events`), so a misspelled field fails the test at build time.
  - WRITING (phase B). The builder writes through `artifact_meta`, as spec `4sd62s` section 7 step 6 requires: the file form calls `artifact_meta.create` (whose phase-B branch renders through `write_legacy`, `xexn45` E-01) and `artifact_meta.append` for `history=` events, with the fixture repository as the project that `artifact_meta` resolves (the fixture repository carries `.aw/`, without which `project_context` finds no project). The text form calls `artifact_meta.render_legacy_text(text, events)` (`xexn45` E-11). The builder has NO renderer of its own, so the cutover changes the format by changing `artifact_meta` and `RECORD_FORMAT`, never by editing a second copy of the format in the tests. Plans start from `ipd_authoring.build_skeleton`, as `support.ready_plan_text` does today; other types start from the minimal heading and body that today's creating command emits. Review records have no `artifact_meta` writer in phase B (no CLI writes them; `xexn45` defers the review-recording command), so `review(...)` renders through `review_findings.render_review` and writes with `review_findings.write_review`.
  - PLACEMENT. The file goes at `artifact_naming.build_clustered_name` under the type's records directory and default disposition: `pending/` for a plan, `artifact_types.TYPE_BACKENDS` for the other types.
  - DETERMINISM. `when=` defaults to the fixed day `2026-08-24` (the `support.ready_plan_text` default) and is never read from the clock, so built bytes are reproducible.
  - TEXT FORM. `text_only=True` returns the string without writing, for tests that pass text (`ipd_lint.lint_text`, merge-stage helpers).
  - SWITCH. One module-level constant, `RECORD_FORMAT`, names the format: `"legacy"` now; Order 13 adds `"log"`.
  - SUPERSESSION. `support.ready_plan_text` becomes a thin call into `plan(..., text_only=True)` with the same signature and the same bytes.
  - Depends on: E-13
  - Expected outcome: `RecordBuilder(tmp).plan(status="approved", set="demo", order=1)` writes a plan that `aw ipd lint` and `artifact_meta.read` accept; `plan(stauts="approved")` raises naming `stauts`; `plan(raw_fields={"Status": "EXECUTED"})` writes the literal line.
  - Execution state: pending

- [ ] E-02 Add `tests/test_record_builder.py` (core). Tests:
  - (a) ROUND TRIP. For each of the eight types, a built record round-trips through `artifact_meta.read` with every field equal to the builder input.
  - (b) LINT. A built plan with `support.ready_plan_text`'s defaults lints `conforming` at the `pre-execution` checkpoint.
  - (c) VISIBILITY. One fixture repository holds one record of each type. ONE call each of `aw find`, `aw attention --format json` and `aw check all --agent` sees every built record.
  - (d) GOLDEN. `support.ready_plan_text` reproduces the E-13 golden bytes for every captured argument set (30 call expressions at review).
  - (e) PARITY. For plan, spec, backlog, research, release and prompt, the builder's file and the file the production creating command writes (`aw ipd scaffold`, `aw specs new`, `aw backlog new`, `aw research new`, `aw releases new`, `aw prompts new`, each with `--apply`) for the same fields give equal `artifact_meta.read` states, so a builder record is a record the toolkit itself would write. Review is excluded because no CLI creates review records; its rounds are checked by (a) through `review_findings.parse_review_text`.
  - (f) REFUSALS. An unknown field, an illegal status for the type and a `short_description` over 300 characters each raise.
  - Depends on: E-01
  - Expected outcome: every test passes; the module's total wall time under `-n 0` stays under 10 s, because (c) and (e) start CLI subprocesses (if it exceeds 10 s, (c) and (e) move to a separate module listed in `tests/slow_allowlist.txt` and the core module keeps (a), (b), (d) and (f)) (measured at review: about 0.4 s for `aw find`, 2.4 s for `aw attention --format json` and 0.9 s for `aw check all --agent` in an empty fixture repository).
  - Execution state: pending

### Task group 2: migrate the high-density families

- [ ] E-03 Batch G1, backlog and release-gate tests (39 files and 1,568 legacy lines at review; F-03): `test_backlog*`, `test_release*`, `test_releases*`, `test_graduat*`, `test_gate_*`, `test_blocks_release*`, `test_handoff*`, `test_from_backlog*`, `test_live_bug*`, `test_*close*`, `test_carrier*`, `test_durable_carrier*`. Apply the batch rule. This is the densest batch: if it cannot be done in one pass, split it at G1a (`test_backlog*`, `test_release*`, `test_releases*`: 24 files, 1,012 lines) and G1b (the rest: 15 files, 556 lines), per OQ-01.
  - Depends on: E-02
  - Expected outcome: an empty before/after `diff`; the remaining legacy-string count for the batch and the reason class of every remaining line pasted.
  - Execution state: pending

- [ ] E-04 Batch G2, check-engine tests (22 files, 1,102 legacy lines): `test_check*`, `test_production*`, `test_decision_ref*`, `test_source_citation*`, `test_severity*`, `test_suppress*`, `test_from_spec*`. Apply the batch rule.
  - Depends on: E-02
  - Expected outcome: an empty before/after `diff`; the remaining count and reason classes pasted.
  - Execution state: pending

- [ ] E-05 Batch G3, setter and spec tests (28 files, 795 legacy lines): `test_status*`, `test_spec*`, `test_specs*`, `test_set_*`, `test_scaffold*`, `test_ipd_authoring*`, `test_descriptive*`, `test_bidi*`. A test that asserts the bytes a SETTER wrote (for example `test_status_set.py` checking the rewritten `- Status:` line) keeps that assertion in phase B, because the written format is the subject. Each such assertion is listed with reason class `setter-byte assertion`, so Order 13 can convert it to `artifact_meta.read` plus the in-file mirror.
  - Depends on: E-02
  - Expected outcome: an empty before/after `diff`; the remaining count, the reason classes and the list of setter-byte assertions pasted.
  - Execution state: pending

### Task group 3: migrate plan, lifecycle and runner tests

- [ ] E-06 Batch G4, plan, lint, lifecycle, finalize and orchestration tests (63 files, 1,244 legacy lines): `test_ipd*`, `test_plan*`, `test_plans*`, `test_finalize*`, `test_lifecycle*`, `test_scope*`, `test_executed*`, `test_exec*`, `test_question*`, `test_dependency*`, `test_orchestrator*`, `test_coverage*`, `test_gradcover*`, `test_readiness*`, `test_partition*`, `test_unresolved*`, `test_terminal*`, `test_implementing*`. Open-question rows (`- Blocking:`, `- Status: open`, `- Carrier:`) are body prose (N3) and are written through the builder's `body=` or `open_questions=` argument, never as metadata. If the batch cannot be done in one pass, split it at G4a (`test_ipd*`, `test_plan*`, `test_plans*`: 21 files, 403 lines) and G4b (the rest: 42 files, 841 lines).
  - Depends on: E-02
  - Expected outcome: an empty before/after `diff`; the remaining count and reason classes pasted.
  - Execution state: pending

- [ ] E-07 Batch G5, runner and lane tests (46 files, 598 legacy lines): `test_oc_*`, `test_agy*`, `test_runner*`, `test_run_*`, `test_runs_*`, `test_lane*`, `test_records_only*`, `test_merge*`, `test_integrat*`, `test_isolation*`, `test_freeze*`, `test_typed_queue*`, `test_attempt*`, `test_attended*`, `test_turn*`, `test_verifier*`, `test_runwire*`, `test_runfresh*`, `test_red_ci*`, `test_silent*`, `test_prior*`, `test_reask*`, `test_hostcap*`, `test_host*`, `test_fixfirst*`, `test_fix_it*`, `test_clean_target*`, `test_commit*`, `test_work_*`, `test_ipdrunner*`, `test_stdin*`. A test that builds a two-branch merge or a lane worktree commits builder-made records on each branch with real `git`.
  - Depends on: E-02
  - Expected outcome: an empty before/after `diff` (the batch rule's `-m ""` includes this batch's `slow` modules); the remaining count and reason classes pasted.
  - Execution state: pending

### Task group 4: migrate reader tests, helpers and fixtures

- [ ] E-08 Batch G6, reader and record-surface tests (69 files, 1,004 legacy lines): `test_find*`, `test_attention*`, `test_history*`, `test_selector*`, `test_cli*`, `test_front_matter*`, `test_record*`, `test_artifact*`, `test_rename*`, `test_group*`, `test_research*`, `test_prompt*`, `test_prompts*`, `test_walkthrough*`, `test_read*`, `test_resolver*`, `test_reference*`, `test_review*`, `test_reviews*`. The `aw-prompt` comment tests (7 files) use `prompt(...)`. Tests whose subject is the legacy grammar itself (`test_front_matter_loose_whitespace.py`, `test_history_block_bounding.py`, the quoted-example cases of `test_selector_two_dialect_readers.py`) keep their literal input and are listed as `legacy-format subject`. If the batch cannot be done in one pass, split it at G6a (`test_find*`, `test_attention*`, `test_history*`, `test_selector*`, `test_cli*`: 31 files, 503 lines) and G6b (the rest: 38 files, 501 lines).
  - Depends on: E-02
  - Expected outcome: an empty before/after `diff`; the remaining count and reason classes pasted.
  - Execution state: pending

- [ ] E-09 Batch G7, the files no G1 to G6 pattern matches, and the shared helpers (44 files, 346 legacy lines at review, including `tests/support.py` (`ready_plan_text`, `scope_drift_repo`) and `tests/conformance_matrix.py`). The file list is re-derived by the batch rule; at review it included `test_action_table_runner_parity.py`, `test_already_landed_dispatch.py`, `test_authoring_coverage_guidance.py`, `test_completion.py`, `test_legacy_finalize.py`, `test_receipt_lane_record.py`, `test_repo_relative_posix.py`, `test_rereview_reviewed_plan.py`, `test_resolve_plan_path_typed.py`, `test_staged_illegal_backlog_transition_gate.py`, `test_workflow_artifacts_prune.py` and the `test_notify*`, `test_index_*`, `test_awmig*` and `test_explicit_dir*` modules. Then delete every private record-building helper (`_write_plan`, `_write_spec`, `_write_backlog_item`, `_make_item`, `_mk_plan`, ...) that no longer has a caller.
  - Depends on: E-03, E-04, E-05, E-06, E-07, E-08
  - Expected outcome: an empty before/after `diff`; the helper count from `rg --no-filename -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*" tests | wc -l` pasted before and after, with each surviving helper and its reason (89 matches at review).
  - Execution state: pending

- [ ] E-10 Convert the tracked `.md` fixtures that tests copy into a repository or lint as records. Re-derive the list with `git ls-files tests/fixtures tests/benchmark_fixtures | grep '\.md$' | xargs grep -l -E '^- (Id|Status):'` (26 at review: `tests/fixtures/attnview/specs-valid` 9, `tests/fixtures/attnview/violations` 7, `tests/fixtures/review-pilot/plans` 9, `tests/fixtures/conforming-orchestrator.md` 1). Rules:
  - A fixture that a test copies or lints is replaced by a builder recipe in the consuming test. The consumers are `test_attention.py`, `test_attention_stem.py`, `test_attention_contract.py`, `test_specs_verbs.py`, `test_specs_releases_unsafe_field.py` (attnview), and `test_ipd_lint.py` and `test_ipd_schema.py` through `support.CONFORMING_ORCHESTRATOR`. Because the orchestrator fixture is a `Path` used by name, `support.CONFORMING_ORCHESTRATOR` becomes a builder-generated file written once per test session under a temporary directory, so its consumers stay unchanged.
  - A fixture whose purpose is malformed legacy input (the `violations` set) stays literal and is listed.
  - `tests/fixtures/review-pilot/plans/` stays literal and is listed. `tools/review_pilot.py` reads it by `manifest.json` filename as a frozen corpus of real plans whose `defects.json` entries quote exact text, so its tracked files must exist and must not change. Order 13 decides its fate with the migrated corpus.
  - Depends on: E-02
  - Expected outcome: the consuming modules' before/after `diff` is empty; the converted and kept fixture lists, each with its reason, are pasted.
  - Execution state: pending

### Task group 5: prove the switch point and finish

- [ ] E-11 Prove that the builder is the single switch point, and write F-06:
  - Add to `tests/test_record_builder.py` a test that monkeypatches `record_builder.RECORD_FORMAT` to an unknown value and asserts that every builder method, including `text_only=True` and `raw_fields=`, raises. This proves that no builder path bypasses the switch. It does not prove that no test builds records outside the builder; the F-06 census below is the evidence for that.
  - Run the F-01 `rg` pattern over `tests/` and write table F-06 in this plan: every remaining legacy string, grouped by file, each with one reason class (`legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, `body prose`).
  - Compare the remaining-line count with the baseline recorded before E-03.
  - Depends on: E-09, E-10
  - Expected outcome: the test passes; F-06 has no row without a reason class; the remaining-line count and E-13's `legacy-before.txt` are pasted.
  - Execution state: pending

- [ ] E-12 Finish:
  - Full-suite comparison. Run `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA tests`, with the batch rule's `grep`, `sed` and `sort` filter, into `.aw/state/59aiyh/full-after.txt`, and compare it with the E-13 `full-before.txt`. The two outcome multisets must be identical except for the new `tests/test_record_builder.py` node ids, which `full-after.txt` adds and which are listed.
  - Core gate. Run the bare `python3 -m pytest` and compare its summary line and wall time with E-13's `core-before.txt`. The after time must be within 110 percent of the before time and inside the 30 s core budget.
  - Also run `make test-all`, `aw check --agent` (no `(location, rule)` pair that E-13's `check-before.jsonl` lacks), and `aw sanitize --agent`.
  - Commit through `aw commit 59aiyh -- <each changed path>`. One commit per batch is allowed, each through `aw commit`. Never push.
  - Depends on: E-11
  - Expected outcome: identical result multisets apart from the listed added node ids; core wall time within 110 percent of the baseline; all runs pass.
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

Measured 2026-11-02 at `0cbfcc706`.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `rg -l --glob '*.py' -e '- (Id|Status|Set|Kind|Blocks-Release|Readiness|Item-Dependencies|Scope-Paths|From-Backlog|From-Spec|Work-Kind|Priority|Order|Date|Gate-Kind|Gate-Ref|Approval|Subject-Id|Verdict|Graduated-To):|## Workflow history' tests` lists 309 files (307 test modules, `support.py`, `conformance_matrix.py`) of 717 Python files; 6,638 matching lines. The narrower `- Id:`/`- Status:`/`## Workflow history` pattern: 300 files, 3,430 lines | Spec section 6 counted 268 of 680 files and 2,607 matches at round 2; the plan's pattern is broader (21 fields). |
| F-02 | Distribution: 44 files have 40 or more matching lines, 126 have 10 to 39, 139 have fewer than 10; top files `test_check_engine_release_gate.py` 442, `test_status_set.py` 216, `test_backlog.py` 205, `test_releases_line_writers.py` 151, `test_graduated_closable_warning.py` 148, `test_check_engine.py` 146 | Effort is concentrated: about 170 files hold 6,056 of the 6,638 lines. |
| F-03 | Family split by filename prefix, re-measured at review (HEAD `4a7499289`, 311 files, 6,657 lines) with a FIRST-MATCH rule (a file goes to the first group, in order G1 to G6, whose pattern list matches its basename; unmatched files go to G7): G1 39 files, 1,568 lines; G2 22, 1,102; G3 28, 795; G4 63, 1,244; G5 46, 598; G6 69, 1,004; G7 44, 346. Six files match two groups and are assigned by that rule (`test_ipd_authoring` G3, `test_readiness_absence_invariant` G4, `test_runner_backlog_close_behavior` G1, `test_orchestrator_retire_closes_backlog` G1, `test_records_only_lane_rederive` G5, `test_ipdrunner_runagy_shim` G4). The authored counts (G6 99, G7 11) did not sum to the file total; the first-match rule makes the partition exhaustive and disjoint. EXCLUDED from every batch (literal legacy input is their subject; owned by other plans): `tests/test_artifact_meta_*.py` (`tve77h`, `2xwb9b`), `tests/test_artifact_meta_legacy_writer.py` and `tests/test_writers_*.py` (`xexn45`), `tests/test_m0001_*.py` and `tests/test_migrations_chain.py` (`dcerjg`, `ya4ee4`) | Seven batches (E-03 to E-09); G1, G4 and G6 carry a pre-measured split seam (OQ-01). |
| F-04 | 88 private record-building helpers in 60 modules (89 matches of the E-09 pattern at review) (`_write_plan` 24, `_write_spec` 12, `_write_backlog_item` 7, `_make_item` 5, `write_plan` 3, `_mk_plan` 3, `_make_plan_text` 3, others 31); by type: plan 43, spec 15, backlog 16, review 5, research 4, release 2, prompt 1, walkthrough 0; `support.ready_plan_text` is used by 14 modules (29 calls) | The builder replaces these helpers. |
| F-05 | 7 test modules hand-write `aw-prompt` comments; 40 tracked `.md` files under `tests/fixtures/` and `tests/benchmark_fixtures/`, of which 26 carry `^- (Id|Status):` (`fixtures/attnview/specs-valid` 9, `fixtures/attnview/violations` 7, `fixtures/review-pilot/plans` 9, `fixtures/conforming-orchestrator.md` 1; the same 26 at `0cbfcc706`); the other 14 are READMEs, prompts, rubrics and workflow-source fixtures with no record metadata. `fixtures/review-pilot/plans` is read by `tools/review_pilot.py` through `manifest.json` filenames and `defects.json` quotations, so it cannot become builder output without changing a tool outside the test tree. 58 `ipd_lint.lint_text(` calls in 10 test modules pass plan text | The builder needs a text form (`text_only=True`) and a prompt form; the review-pilot corpus stays literal (E-10). |
| F-06 | (written by E-11) remaining legacy strings in `tests/` after the batches, each with one reason class: `legacy-format subject`, `displayed-output assertion`, `setter-byte assertion`, `invalid-input`, `body prose` | Order 13 changes the builder plus the F-06 rows of class `setter-byte assertion`; `invalid-input` rows already go through `raw_fields=` and need a decision at the cutover (an invalid bullet has no log-format equivalent); every other class is either a legacy-format test (moved to the migration tests at the cutover) or prose. |
| F-08 | At review, 15 test modules write a deliberately invalid metadata value (for example `tests/test_releases.py` "`- Status: bogus`", `tests/test_check_engine.py` "`- Status: EXECUTED`", `tests/test_specs_set_adapter.py` "`- Priority: bogus`") | A builder that validates every field cannot build these; E-01 adds `raw_fields=` and the batch rule lists them as `invalid-input`. |
| F-09 | At review, in an empty installed fixture repository: `aw find plans` 0.47 s, `aw attention --format json` 2.4 s, `aw check all --agent` 0.9 s; `aw install` into a fresh repository 4.6 s | E-02's visibility and parity tests cost several seconds, so its bound is 10 s, not 3 s, with a stated fallback. |
| F-07 | `python3 -m pytest --collect-only -q -o addopts="" tests` collects 10,469 tests (10,498 at review) | Context only; the bar is E-12's comparison with E-13's re-derived baseline. |

## Proposed changes (ordered, validatable)

1. Capture the baselines, then build and test the shared builder (E-13, E-01, E-02).
2. Migrate the backlog/release, check-engine and setter families (E-03 to E-05).
3. Migrate the plan/lifecycle and runner families (E-06, E-07).
4. Migrate the reader family, the helpers and the `.md` fixtures (E-08 to E-10).
5. Prove the single switch point, then run the full comparison and commit (E-11, E-12).

## Deferred / out of scope (with reason)

- Adding `RECORD_FORMAT = "log"` (builder writes through `artifact_meta.create`/`append` and the two-key front matter) and converting the F-06 setter-byte assertions to `artifact_meta.read` plus the in-file mirror: both belong in the cutover commit (C10a: one format per commit).
  - Carrier: cxxmyv
- The legacy-format tests that must keep literal input (the legacy loader tests in `tve77h`, the legacy writer tests in `2xwb9b` and `xexn45`, the migration round-trip and conversion tests in `dcerjg` and `ya4ee4`; the F-03 EXCLUDED list).
  - Carrier: dcerjg
- The `tests/fixtures/review-pilot/plans/` corpus stays literal legacy input (F-05); its fate after the cutover belongs with the migrated corpus.
  - Carrier: cxxmyv
- Deleting production parsers (the builder must not depend on them; it validates through the registry only).
  - Carrier: 9o83cr
- Tests added by later Set children (Orders 11 to 13) use the builder from the start; enforcing that is a review concern of those plans.
  - Carrier: 9o83cr

## Scope check

- Over-scope: none. No production module changes. `tests/test_*.py` is a glob because the batches touch about 300 modules; each batch's file list is saved under `.aw/state/59aiyh/` and pasted in its V-item, and the finalize scope reconciliation lists every changed file. `tests/fixtures/review-pilot/**` was removed from `- Scope-Paths:` because E-10 keeps that corpus literal; `tests/fixtures/record_builder/**` was added for the E-13 golden file.
- Under-scope: none known. Plan size: 13 E-items in 5 task groups (limits 18 and 5).

## Required tests / validation

New core test module: `tests/test_record_builder.py`. Every batch is validated by an identical per-test result list before and after (the batch rule), which is behavioral by construction: the same tests, unchanged assertions, the same outcomes.

Acceptance criteria of `4sd62s`:

- OWNS: none outright. This plan supplies the switch point that makes AC-1b provable at the cutover.
- CONTRIBUTES to AC-1b (owned by `cxxmyv`): the core-tier summary line pasted for this plan's merge (E-12), and the single builder switch (E-11) so the cutover commit passes the thorough tier without a test-data rewrite. CONTRIBUTES to AC-1 (owned by `9o83cr`): the builder validates through the registry and parses nothing itself, so no test helper becomes a second parser.

Commands: the batch rule's `python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <batch files>` per batch, `tests/test_record_builder.py`, the bare core gate `python3 -m pytest`, `make test-all`, `aw check --agent`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change; implements `4sd62s` section 6 ("Rewrite the test data with ONE shared record builder in phase B") and section 7 step 6. `CONTRIBUTING.md` needs no change in phase B; Order 12 (`90iqr1`) documents the builder for test authors after the cutover.

## Open questions

### OQ-01: Should the plan be split?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No: 13 E-items in 5 task groups. The work is large in files, not in decisions; each batch is mechanical under the batch rule. If a batch proves too large for one pass during execution, split it at the seam its E-item names, measured at review: G1 into G1a/G1b (1,012 and 556 lines), G4 into G4a/G4b (403 and 841), G6 into G6a/G6b (503 and 501). Adding all three splits brings the plan to 16 E-items, inside the 18-item limit. Recommendation strength: medium.

### OQ-02: Which prior Orders does the builder depend on?

- Blocking: no
- Status: resolved
- Owner: plan-review (round 1, decision D-1)
- Resolution or deferral rationale: `tve77h` and `xexn45`. It does NOT depend on Order 08's `artifact_meta.read_text`: `test_record_builder.py` reads built records back with `artifact_meta.read` (Order 02), and text-only records are checked by writing them into a fixture repository. But spec `4sd62s` section 7 step 6 requires a builder "that writes through `artifact_meta`", and in phase B only `xexn45` gives `artifact_meta.create` a legacy-format branch (`write_legacy`) and adds `render_legacy_text`; Order 02's `create` writes the log format. Depending only on `tve77h` would force the builder to carry its own legacy renderer, a second copy of the format that the cutover would have to change as well. The authored resolution said `executed:tve77h` was sufficient; review revised it to `executed:tve77h, executed:xexn45`. Critical-path cost: none, because Order 11 (`9o83cr`) already waits for `ffceq0` and `t4gl15`, which both wait for `xexn45`. Batches may run before or after Orders 08 and 09; each batch's before/after comparison runs against whatever production code is on `main` at that time. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -c` output that builds one record of each of the eight types in a temporary fixture repository with `RecordBuilder` and prints, for each, the created path and the `artifact_meta.read(<id6>)` status, set and order; `aw ipd lint <built plan>` ending in `conforming`; the exception message raised for `plan(stauts="approved")`, naming `stauts`; the bytes of the line written by `plan(raw_fields={"Status": "EXECUTED"})`; and `rg -n "def |import" tests/record_builder.py` output showing that the module imports `artifact_meta` for writing and defines no metadata renderer of its own (the verbatim `raw_fields=` line insertion is the one permitted text edit).
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -n 0 -v --durations=0 tests/test_record_builder.py` with every test PASSED: one round-trip test per type, the lint test, the `aw find`/`aw attention`/`aw check` visibility test, the golden test over every argument set in `tests/fixtures/record_builder/ready_plan_text_golden.json`, the six-type parity test, and the three refusal tests. Paste the total duration (under 10 s, or the moved module named in `tests/slow_allowlist.txt` with its own PASSED run).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `.aw/state/59aiyh/G1-files.txt` (or G1a and G1b), `diff .aw/state/59aiyh/G1-before.txt .aw/state/59aiyh/G1-after.txt` printing nothing, the before and after F-01 `rg -c` totals for the batch, and the reason class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the G2 file list, the empty `diff` of `G2-before.txt` and `G2-after.txt`, the before/after F-01 totals for the batch, and the reason class of every remaining match.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the G3 file list, the empty `diff` of `G3-before.txt` and `G3-after.txt`, the before/after F-01 totals, the reason classes, and the list of setter-byte assertions kept for Order 13 (file::test and the asserted line).
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste the G4 file list (or G4a and G4b), the empty `diff` of the before/after outcome lists, the before/after F-01 totals, and the reason classes (open-question body rows shown as written through `body=`/`open_questions=`).
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the G5 file list, the empty `diff` of the before/after outcome lists (run with the batch rule's `-m ""`, so `slow` tests are included; paste the count of `slow` node ids in the list), the before/after F-01 totals, and the reason classes.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste the G6 file list (or G6a and G6b), the empty `diff` of the before/after outcome lists, the before/after F-01 totals, and the reason classes, including the legacy-grammar modules kept literal.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the G7 file list, the empty `diff` of the before/after outcome lists, and the helper count from `rg --no-filename -o "def _?(make|write|build|mk|seed)_(plan|spec|backlog|item|record|ipd|release|research|prompt|review|walkthrough)\w*" tests | wc -l` before (E-13's `helpers-before.txt`) and after, with each surviving helper and its reason.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `git ls-files tests/fixtures tests/benchmark_fixtures | grep '\.md$' | xargs grep -l -E '^- (Id|Status):'` before and after; the converted and kept lists, each path with its reason (the `violations` set and `review-pilot/plans` kept); `git status --short tests/fixtures/review-pilot` printing nothing; and the empty `diff` of the before/after outcome lists of every consuming module named in E-10.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_record_builder.py -k switch` PASSED, the F-06 table written into this plan with a reason class on every row, and the remaining-line count beside E-13's `legacy-before.txt` value.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste the `diff` of `full-before.txt` and `full-after.txt`, showing only added `tests/test_record_builder.py` node ids, with both line counts; the bare `python3 -m pytest` summary line and wall time now beside E-13's `core-before.txt` (now within 110 percent); the `make test-all` summary line; the `aw check --agent` `(location, rule)` comparison with `check-before.jsonl` showing no added pair; the `aw sanitize --agent` result with zero `fail`; and every `aw commit 59aiyh` output, listing only Scope-Paths.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `ls -l --time-style=full-iso .aw/state/59aiyh/ tests/fixtures/record_builder/ready_plan_text_golden.json` and `git log --reverse --format='%H %ci %s' -- tests/record_builder.py | head -1` (the commit that adds the module, which does not exist at review), showing every baseline file older than that commit; the first line of `core-before.txt`; the line count of `full-before.txt`; and the number of argument sets in the golden file.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` and `xexn45` are executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration. A needed test-tree file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Production code under `agent_workflows/` and `tools/` is out of this plan's purpose: if a batch cannot keep its outcome list identical without a production change, stop that batch and report the missing capability rather than changing production code or an assertion. Each batch keeps every assertion except those its V-item lists.

Honesty rule: run the batch comparisons, `tests/test_record_builder.py`, the bare `python3 -m pytest` core gate and `make test-all`, and paste the ACTUAL output; never claim a result you did not run.

Commits: commit only through `aw commit 59aiyh -- <paths>` (one commit per batch allowed); never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 59aiyh` itself.
