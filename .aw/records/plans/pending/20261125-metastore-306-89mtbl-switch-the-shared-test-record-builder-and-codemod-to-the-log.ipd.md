# IPD: Switch the shared test record builder and codemod to the log format in the cutover code patch

- Date: 2026-11-25
- Kind: child
- Concern: Backlog `ldfefd` (`x1mmdp` F-05 to F-07): the cutover code patch removes the legacy bullet API (`_LEGACY_BULLET_LABEL`, `LegacyRender`, `LegacyTarget`, `render_legacy_text`, `set_legacy_bullet_line`, `_format_legacy_value`, `_RESEARCH_YAML_KEY`, `_format_yaml_value`, `_PROMPT_COMMENT_KEY`) that `tests/record_builder.py` and `tools/fixture_codemod.py` call. On the switched tree, the shared builder fails at import (`AttributeError` on `_LEGACY_BULLET_LABEL`) and every test importing `tests/support.py` fails with it. In addition, the builder's `text_only=True` mode (about 1690 calls across 310 files, about 650 written to disk by callers) needs an explicit log-format contract because a log-format artifact requires a paired `meta/<id6>.jsonl` log (and a review record stores events in its subject's log per spec `4sd62s` Section 4.1a).
- Scope: In an isolated scratch worktree with both cutover patches applied (including `hdwqex`), record the log-format `text_only` and `raw_fields` contract in F-02, switch `tests/record_builder.py` to `RECORD_FORMAT = "log"` across all eight record types (7 log-backed artifact types through `artifact_meta.create`/`append`, plus `review` through `artifact_meta.render_review_mirror` and subject-log `op: "review"` events per spec `4sd62s` Section 4.1a) with the log branch of `assert_field`/`assert_no_field`, update `tests/support.py` (`_conforming_orchestrator_path` and `ready_plan_text`) as required by F-02, repoint `tools/fixture_codemod.py::_registry_field_map` onto `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS` and align its rewrite/proof target with F-02, update and pass the four builder and codemod test modules (plus their fixture/golden baselines), measure the per-module core-gate failure census in F-04, and regenerate `.aw/system/cutover/metastore-code.cutover.patch`. No live code changes.
- Scope-Paths: .aw/records/plans/pending/20261125-metastore-306-89mtbl-switch-the-shared-test-record-builder-and-codemod-to-the-log.ipd.md, .aw/system/cutover/metastore-code.cutover.patch
- Item-Dependencies: executed:hdwqex
- Status: approved
- Review-Depth: standard
- Readiness: go-pending-approval
- From-Spec: 4sd62s
- Work-Kind: followup
- Priority: high
- From-Backlog: ldfefd
- Blocks-Release: next
- Set: metastore
- Order: 306
- Highest E allocated: 05
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 89mtbl
- Approval: 2026-11-26, recorded via aw ipd set: status set to approved

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-27 note (antigravity/gemini): resolved OQ-01 per maintainer answer to run-20261127T045218Z-1963184 question 219-89mtbl-a1-89mtbl-slow-tests-circular-dep ("Defer slow integration test to final rollup plan x1mmdp and add a child plan for 0b3ynm and 2etrjf"); authored Order 322 child plan 6cltab and deferred tests/test_record_builder_slow.py to x1mmdp E-04/V-04.
- 2026-11-26 approved (aw set): status set to approved
- 2026-11-26 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 FIXED
- 2026-11-26 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006; review record .aw/records/reviews/20261125-metastore-306-89mtbl-switch-the-shared-test-record-builder-and-codemod-to-the-log.review.md
- 2026-11-26 to-review (aw set): authored as part of the x1mmdp split per maintainer answer to run-20261125T162650Z-1337442 question 06-x1mmdp-a1-Q-01 (Split into new children; fix jycxw8 first)
- 2026-11-26 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Make `tests/record_builder.py`, `tests/support.py`, and `tools/fixture_codemod.py` work on the switched log-format tree, with a written `text_only` and `raw_fields` contract (F-02) and a fresh per-module core-gate failure census (F-04) that the batch children (`nv3upa` to `x3mig6`) follow so converting the remaining failing test modules is mechanical.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: write for a modest executor that cannot hold much in its head. Each E-item is one step (one concern, about one file, executable in one focused pass) and its V-item names each unit it covers with its own check; a plan stays at about 5 E-items and 8 work Scope-Paths, else split it into more child plans (guidance, `IPD-Z603`). Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: scratch worktree

- [x] E-01 Create the scratch worktree following the SCRATCH PROCEDURE of `2k5t16` (Step 0): run `git worktree add --detach .aw/state/89mtbl/scratch HEAD`; inside `.aw/state/89mtbl/scratch`, run `git apply --index .aw/system/cutover/metastore-docs.cutover.patch`, record `BASE=$(git write-tree)` in F-01, and then run `git apply --index .aw/system/cutover/metastore-code.cutover.patch`. If either patch rejects, stop and report.
  - Depends on: none
  - Expected outcome: `.aw/state/89mtbl/scratch` holds HEAD plus both patches staged, and F-01 records the base tree id.
  - Execution state: performed

### Task group 2: builder and codemod (scratch worktree only)

- [x] E-02 Record the log-format `text_only` and `raw_fields` contract in F-02, then switch `tests/record_builder.py` (and `tests/support.py` callers as needed) to `RECORD_FORMAT = "log"`:
  1. In F-02, document the `text_only` and `raw_fields` contract with one concrete example call of each form that batch children (`nv3upa` to `x3mig6`) use. Default (to adopt unless a measured finding in F-02 requires adjustment): `text_only=True` returns the in-file text that `artifact_meta.create(..., dry_run=True)["text"]` renders (the in-file mirror, banner, and body) for in-memory readers (`artifact_meta.read_text`, `ipd_lint.lint_text` on mirror+body), while any caller that writes a record to disk must call `RecordBuilder(repo)` without `text_only` (or a new `RecordBuilder.materialize` helper calling `artifact_meta.create`) so `meta/<id6>.jsonl` exists beside the file. Also state how `raw_fields` operates in log format without calling removed `set_legacy_bullet_line` (for example mutating the mirror/body text or raw log fields for negative-input fixtures).
  2. In `tests/record_builder.py`, set `RECORD_FORMAT = "log"`, update `_require_legacy_format` to accept `"log"` (refusing unknown values), and remove all module-level reads of removed `artifact_meta` symbols (`_LEGACY_BULLET_LABEL`, `LegacyRender`, `LegacyTarget`, `render_legacy_text`, `set_legacy_bullet_line`, `_format_legacy_value`, `_RESEARCH_YAML_KEY`, `_format_yaml_value`, `_PROMPT_COMMENT_KEY`).
  3. Rewrite `_emit_record` and the seven log-backed artifact methods (`plan`, `spec`, `backlog`, `research`, `release`, `prompt`, `walkthrough`) to pass complete registry fields (`plan_role`, `author`, `set`, `order`, `title`, `highest_e_allocated`, etc. that legacy bullets or filenames used to carry) into `artifact_meta.create(id6, record_type, fields, body, destination=rel_path, project_context=ctx, actor=_ACTOR, ...)` (consuming the returned dict `res["text"]`, with no `legacy_render` or `repo_root` keyword) and follow-up/history events through `artifact_meta.append(id6, events, project_context=ctx, actor=_ACTOR, ...)` (emitting valid `op: "review"` events carrying `round`, `review_kind`, `verdict`, and `readiness` when `readiness` is set, and never editing a `## Workflow history` body section).
  4. Update `RecordBuilder.review` per spec `4sd62s` Section 4.1a: a review has NO `meta/<id6>.jsonl` log of its own; write the `.review.md` file with `artifact_meta.render_review_mirror(subject, subject_type, ref=...)` plus the `## Round <n>` / `### Findings` / `### Decisions` tables, and when `text_only=False` and `meta/<subject>.jsonl` exists, append one `op: "review"` event per round to the subject's log via `artifact_meta.append(subject, ...)`.
  5. Implement the log-format branch of `assert_field` and `assert_no_field`: for log-backed types read `artifact_meta.read(id6, project_context=...)` AND verify the on-disk mirror (`id`/`status` YAML front matter or staged-prompt comment mirror); for `review`, read the review front matter and (when present) the subject log's `op: "review"` events.
  6. Update `tests/support.py::_conforming_orchestrator_path` and `ready_plan_text` as needed under F-02 so `import tests.support` succeeds cleanly and `CONFORMING_ORCHESTRATOR` works in the log format.
  - Depends on: E-01
  - Expected outcome: F-02 holds the contract; `python3 -c "import tests.support"` exits 0 in the scratch worktree; all 7 log-backed artifact types read back via `artifact_meta.read` with the fields given; and `review` reads back via `review_findings.parse_review_file` plus `artifact_meta.history(subject)` showing the `op: "review"` event.
  - Execution state: performed

- [x] E-03 In `tools/fixture_codemod.py`, replace the removed `artifact_meta` label-map reads in `_registry_field_map` with `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS` (deriving legacy label -> registry field mappings for `identity`, `status`, and `log_field` destinations per record type; record the exact symbol and helper in F-03), and align the codemod's rewrite target and equivalence proof with the F-02 contract.
  - Depends on: E-02
  - Expected outcome: `python3 tools/fixture_codemod.py --dry-run --format json tests/test_fixture_codemod.py` runs in the scratch worktree with exit 0 and no `AttributeError`.
  - Execution state: performed

- [x] E-04 Update and run the four builder and codemod test modules in the scratch worktree, then measure the core-gate failure census in F-04:
  1. Update `tests/test_record_builder.py` (including regenerating or updating `tests/fixtures/record_builder/ready_plan_text_golden.json` and `test_lint_ready_plan_conforms` for the F-02 log format), `tests/test_record_builder_slow.py`, `tests/test_record_builder_assert_field.py` (replacing legacy bullet-spacing strictness checks with log-plus-mirror strictness checks), and `tests/test_fixture_codemod.py` (including any `tests/fixtures/fixture_codemod/` fixtures whose assertions assumed bullet-block `read_text` fields under `text_only=True`).
  2. Run `python3 -m pytest -o addopts="" -m '' tests/test_record_builder.py tests/test_record_builder_slow.py tests/test_record_builder_assert_field.py tests/test_fixture_codemod.py` in the scratch worktree; all four modules must exit 0 with every test PASSED.
  3. Run the bare core gate (`python3 -m pytest`) in the scratch worktree (a nonzero exit is expected until batches `nv3upa` to `x3mig6` run) and record the per-module failure census in F-04 as a Markdown table with columns `| Module | Failed | Errors | Category (schema-1 refusal / removed-API / assertion / REPO_ROOT) |` alongside the core-gate summary line.
  - Depends on: E-03
  - Expected outcome: all four builder and codemod test modules pass; F-04 holds the per-module failure census table and the core-gate summary line.
  - Execution state: performed
  - Execution note: 3 of 4 modules (`tests/test_record_builder.py`, `tests/test_record_builder_assert_field.py`, `tests/test_fixture_codemod.py`) plus `tests/test_fixture_codemod_slow.py` passed 43/43 and F-04 census was recorded; per maintainer resolution of `OQ-01` (2026-11-27, `219-89mtbl-a1-89mtbl-slow-tests-circular-dep`), `tests/test_record_builder_slow.py` is deferred to `x1mmdp` E-04/V-04 and newly discovered production defects `0b3ynm` and `2etrjf` are assigned to Order 322 child plan `6cltab`.

### Task group 3: package

- [x] E-05 In `.aw/state/89mtbl/scratch`, run `git add -A` and write `git diff --cached --binary $BASE` over `.aw/system/cutover/metastore-code.cutover.patch` in the executing checkout; remove the scratch worktree (`git worktree remove --force .aw/state/89mtbl/scratch`); run `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout; verify `git status --short` shows only `- Scope-Paths:` modified; and commit through `aw commit 89mtbl -- .aw/records/plans/pending/20261125-metastore-306-89mtbl-switch-the-shared-test-record-builder-and-codemod-to-the-log.ipd.md .aw/system/cutover/metastore-code.cutover.patch`; never push.
  - Depends on: E-04
  - Expected outcome: `.aw/system/cutover/metastore-code.cutover.patch` contains all prior changes plus this plan's; `tests/test_metastore_cutover_code_patch.py` passes; scratch worktree is removed; one path-scoped commit is created.
  - Execution state: performed

## Project conventions discovered (Step 0)

- The scratch procedure and cumulative code patch are defined in executed plan `2k5t16` (Step 0, OQ-01); executed sibling `g45vyv` follows it.
- Conversion rules shared by the `ldfefd` batch children (`nv3upa`, `cugg3w`, `psm9ac`, `x8id25`, `e0g2gt`, `qi0kl6`, `x3mig6`), fixed here so no executor invents them: (1) a call to an API the code patch removes (`LegacyRender`, `LegacyTarget`, `render_legacy_text`, `set_legacy_bullet_line`, `_LEGACY_BULLET_LABEL`, `_format_legacy_value`, `_RESEARCH_YAML_KEY`, `_format_yaml_value`, `_PROMPT_COMMENT_KEY`, `write_legacy`, `SidecarRecord`, `backlog._render_item`'s bullet form) is replaced by its log-format equivalent: `artifact_meta.create` or `artifact_meta.append` keyed by id6, or `tests.record_builder.assert_field`/`assert_no_field`; (2) a fixture written as bullet-format literal text is rebuilt through `tests.record_builder.RecordBuilder` under the `text_only` contract that `89mtbl` F-02 records; (3) a test whose SUBJECT is legacy input (the legacy loader, migration, conversion) keeps its literal input and calls `m0001` (`agent_workflows.migrations.m0001_metadata_v2.load_legacy_artifact`, or `aw migrate metadata` on the fixture repository first); (4) a test of behavior the cutover removes may be deleted only with the spec `4sd62s` clause that removes the behavior cited in F-02 beside each deleted node id; (5) never weaken an assertion to make a test pass: an unexplained failure on unmodified production code stops the plan and is reported.
- A fixture repository written by the switched builder is log-format, so `migrations.chain.require_current_schema` sees no legacy record and does not refuse; a test that still sees "run `aw migrate metadata`" on its OWN fixture has not been converted. Only tests reading this repository's own unmigrated records (`livecorpus`, `REPO_ROOT`) may still refuse, and those are listed in F-03, not edited.
- Per spec `4sd62s` Section 4.1a, review files carry `subject` / `subject_type` / optional `ref` front matter (no `id:` key and no own `meta/<id6>.jsonl` log); each review round is an `op: "review"` event in its subject's log.
- Tests exercise code and assert on observable outcomes (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Cite code by symbol (`path::Symbol`) or by a quoted content string, with a line number only appended as a hint and never alone (advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `git apply --index .aw/system/cutover/metastore-docs.cutover.patch` (exit 0) in `.aw/state/89mtbl/scratch` from HEAD `188044b31821eea2932047e63a47b9ad36b2b1d1`, followed by `git write-tree`. | Base tree id `BASE=3f1ce679f1f827835969cf2c92436d9d27aa4478`. |
| F-02 | `tests/record_builder.py` (`RECORD_FORMAT = "log"`, `_get_dry_run_context`, `RecordBuilder.materialize`, `_emit_record`, `_apply_raw_fields_to_text`, `_patch_log_with_raw_fields`), `tests/support.py` (`_conforming_orchestrator_path`, `scope_drift_repo`), verified by `tests/test_record_builder.py` (15 passed), `tests/test_record_builder_assert_field.py` (15 passed), `tests/test_fixture_codemod.py` (11 passed), `tests/test_fixture_codemod_slow.py` (2 passed). | Log-format `text_only` and `raw_fields` contract for batch children (`nv3upa` to `x3mig6`): (1) `text_only=True` calls `artifact_meta.create(..., dry_run=True, project_context=_get_dry_run_context())` using a process-private ephemeral context and returns `res["text"]` (the YAML or staged-prompt in-file mirror, `aw-managed` banner, and Markdown body) without touching the repository; intended strictly for in-memory readers (`artifact_meta.read_text`, or `ipd_lint.lint_text` paired with a `State`). Example: `text = RecordBuilder(None).plan(id6="ab12cd", title="Demo", status="draft", text_only=True)`. (2) Disk fixtures MUST omit `text_only` (default `text_only=False`) or call `RecordBuilder(repo).materialize(id6=..., record_type=..., destination=..., fields=..., body=..., raw_fields=...)` so `artifact_meta.create` writes both the Markdown artifact and its companion `meta/<id6>.jsonl` log (for `review`, writes the Section 4.1a mirror and appends `op: "review"` events to `meta/<subject>.jsonl` when present). Example: `path = RecordBuilder(repo).plan(id6="ab12cd", title="Demo", status="approved")` or `RecordBuilder(repo).materialize(id6="ab12cd", record_type="ipd", destination=".aw/records/plans/pending/20260824-s-01-ab12cd-demo.ipd.md", fields={"status": "draft", "title": "Demo"}, body="# IPD: Demo\n")`. (3) `raw_fields` maps keys through `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS` without calling removed legacy bullet APIs: on IPDs `Concern` and `Scope` map to `## Concern` / `## Scope` body sections inserted before `## Goal`; in disk mode (`text_only=False`), mirror keys (`id`, `status`, and prompt comment keys) are mutated in the written file and event 1 of `meta/<id6>.jsonl` is patched in place; in `text_only=True` mode, mirror keys are mutated in the leading mirror block so `artifact_meta.read_text` observes negative-input overrides. Example: `bad = RecordBuilder(None).plan(id6="ab12cd", raw_fields={"Status": "EXECUTED"}, text_only=True)` (in-memory) or `RecordBuilder(repo).plan(id6="ab12cd", raw_fields={"Priority": "bogus"})` (on-disk). |
| F-03 | `tools/fixture_codemod.py::_registry_field_map` importing `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS`, verified by `python3 tools/fixture_codemod.py --dry-run --format json tests/test_fixture_codemod.py` (exit 0) and `tests/test_fixture_codemod.py` (11 passed) + `tests/test_fixture_codemod_slow.py` (2 passed). | `tools/fixture_codemod.py::_registry_field_map` reads `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS` per `record_type`, iterating `(legacy_label, dest)` entries where `dest.kind in ("identity", "status", "log_field")` and mapping lowercase and hyphen/space-to-underscore forms of `legacy_label` to `dest.target` when `dest.target` is in `artifact_meta.registry_fields(record_type)` or `("id", "status")`. |
| F-04 | Bare core gate `python3 -m pytest --tb=line` in `.aw/state/89mtbl/scratch` after E-02/E-03/E-04 updates (exit 1). | Core-gate summary line: `692 failed, 2243 passed, 1 skipped, 11 warnings, 66 errors in 121.03s (0:02:01)` across 86 modules. Full per-module census table is recorded below under `### F-04 per-module core-gate failure census`. |
| F-05 | `x1mmdp` F-05 to F-07 (2026-11-25, historical attempt-1 run `run-20261125T162650Z-1337442` provenance; lane submission file is gitignored and not present in fresh lanes): on the switched tree with copies of the removed helpers, the core gate reported `567 failed, 2348 passed, 1 skipped, 11 warnings, 66 errors` across 71 modules, 385 of them `MetadataSchemaError` from fixture repositories the tests build themselves. | A fixture repository with bullet records counts as schema 1 under `migrations.chain.require_current_schema`; switching the builder to log format removes most of those refusals. |
| F-06 | Spec `4sd62s` Section 4.1a; `agent_workflows/artifact_meta.py::render_review_mirror`; `tests/record_builder.py::RecordBuilder.review`; `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS`; `tests/fixtures/fixture_codemod/plain_constant.py.txt`; `tests/test_record_builder.py::RecordBuilderGoldenTests.test_golden_ready_plan_text`; `tests/support.py::_conforming_orchestrator_path`. | Reviews have no log of their own (events live in the subject's log); `m0001_convert.py::FIELD_DESTINATIONS` (not `m0001_metadata_v2.py`) holds the per-type legacy label maps; `tests/record_builder.py` must supply complete `create` fields and consume `artifact_meta.create`'s dict return; and `plain_constant.py.txt`, `ready_plan_text_golden.json`, and `tests/support.py` must align with the F-02 log-format contract. |

### F-04 per-module core-gate failure census

Summary line: `692 failed, 2243 passed, 1 skipped, 11 warnings, 66 errors in 121.03s (0:02:01)` (86 failing/erroring modules).

| Module | Failed | Errors | Category (schema-1 refusal / removed-API / assertion / REPO_ROOT) |
|---|---:|---:|---|
| `tests/test_artifact_meta_cache.py` | 2 | 0 | schema-1 refusal |
| `tests/test_artifact_meta_legacy.py` | 14 | 0 | removed-API |
| `tests/test_artifact_meta_legacy_write.py` | 31 | 0 | removed-API |
| `tests/test_artifact_meta_legacy_writer.py` | 11 | 0 | removed-API, schema-1 refusal |
| `tests/test_artifact_meta_loader_parity.py` | 5 | 0 | schema-1 refusal |
| `tests/test_artifact_meta_read.py` | 4 | 0 | schema-1 refusal |
| `tests/test_artifact_meta_shapes.py` | 15 | 0 | schema-1 refusal |
| `tests/test_artifact_meta_write.py` | 1 | 0 | schema-1 refusal |
| `tests/test_attention_contract.py` | 4 | 0 | assertion, schema-1 refusal |
| `tests/test_attention_priority_blocker.py` | 1 | 0 | assertion |
| `tests/test_awcmdsurf_mutation_verbs.py` | 2 | 0 | assertion |
| `tests/test_backlog.py` | 33 | 0 | assertion, removed-API, schema-1 refusal |
| `tests/test_begin_dirty_gate_scope.py` | 10 | 0 | assertion |
| `tests/test_blocks_release_reader_bounding.py` | 0 | 6 | removed-API |
| `tests/test_check_engine.py` | 12 | 0 | assertion, schema-1 refusal |
| `tests/test_check_engine_from_spec_missing.py` | 0 | 6 | removed-API |
| `tests/test_check_engine_restored_behavior.py` | 2 | 0 | assertion |
| `tests/test_check_engine_spec_criteria.py` | 1 | 0 | assertion |
| `tests/test_check_meta.py` | 11 | 0 | assertion |
| `tests/test_cli_search.py` | 11 | 0 | assertion |
| `tests/test_cutover_log_gates.py` | 2 | 0 | assertion, schema-1 refusal |
| `tests/test_cutover_log_readers.py` | 1 | 0 | assertion |
| `tests/test_event_overrides.py` | 5 | 0 | assertion, schema-1 refusal |
| `tests/test_from_backlog_cardinality.py` | 0 | 6 | removed-API |
| `tests/test_generators_writing_standard_pointer.py` | 4 | 0 | assertion |
| `tests/test_history_order.py` | 2 | 0 | assertion |
| `tests/test_index_aliases.py` | 7 | 0 | assertion |
| `tests/test_index_rebuild.py` | 6 | 0 | assertion |
| `tests/test_ipd_dependency_check.py` | 3 | 0 | assertion |
| `tests/test_ipd_dependency_statement_gate.py` | 5 | 0 | assertion |
| `tests/test_ipd_followability.py` | 5 | 0 | assertion |
| `tests/test_ipd_lifecycle_restored_behavior.py` | 6 | 0 | assertion |
| `tests/test_ipd_lint.py` | 33 | 0 | assertion |
| `tests/test_ipd_set_executor.py` | 5 | 0 | assertion |
| `tests/test_log_rename_events.py` | 1 | 0 | assertion |
| `tests/test_m0001_any_repo.py` | 5 | 0 | assertion, schema-1 refusal |
| `tests/test_m0001_gate_marker.py` | 11 | 0 | schema-1 refusal |
| `tests/test_m0001_review_conversion.py` | 2 | 0 | assertion |
| `tests/test_m0001_sidecar.py` | 1 | 0 | removed-API |
| `tests/test_meta_repair_cli.py` | 1 | 0 | schema-1 refusal |
| `tests/test_metadata_single_owner.py` | 7 | 0 | assertion |
| `tests/test_migrate_cli.py` | 1 | 0 | assertion |
| `tests/test_migrations_chain.py` | 2 | 0 | schema-1 refusal |
| `tests/test_partition.py` | 1 | 0 | assertion |
| `tests/test_plan_readiness_recheck.py` | 2 | 0 | assertion |
| `tests/test_plans_index.py` | 2 | 0 | assertion |
| `tests/test_poll_for_deps.py` | 4 | 0 | assertion |
| `tests/test_prompts_set_surface.py` | 1 | 0 | schema-1 refusal |
| `tests/test_prose_dash_advisory.py` | 8 | 0 | assertion, schema-1 refusal |
| `tests/test_readers_attention.py` | 13 | 0 | assertion, schema-1 refusal |
| `tests/test_readers_cache_parity.py` | 3 | 20 | assertion, schema-1 refusal |
| `tests/test_readers_check_engine.py` | 39 | 0 | assertion, schema-1 refusal |
| `tests/test_readers_gate_cache_parity.py` | 8 | 16 | assertion |
| `tests/test_readers_ipd_lint.py` | 8 | 0 | assertion |
| `tests/test_readers_offline.py` | 2 | 0 | assertion |
| `tests/test_readers_read_at_gates.py` | 13 | 0 | assertion |
| `tests/test_readers_record_modules.py` | 12 | 0 | assertion, schema-1 refusal |
| `tests/test_readers_review_modules.py` | 21 | 0 | assertion, schema-1 refusal |
| `tests/test_readers_runner.py` | 9 | 0 | assertion |
| `tests/test_readers_selectors_find.py` | 4 | 0 | assertion |
| `tests/test_record_residual_helpers.py` | 1 | 0 | assertion |
| `tests/test_releases_line_writers.py` | 0 | 6 | removed-API |
| `tests/test_releases_sibling_line_writers_bounding.py` | 0 | 6 | assertion |
| `tests/test_research_index.py` | 44 | 0 | assertion, schema-1 refusal |
| `tests/test_research_meta_writer_characterization.py` | 5 | 0 | assertion, schema-1 refusal |
| `tests/test_research_priority.py` | 4 | 0 | assertion, removed-API |
| `tests/test_review_decisions.py` | 7 | 0 | assertion |
| `tests/test_review_findings_gate.py` | 1 | 0 | assertion |
| `tests/test_review_rereview.py` | 2 | 0 | assertion |
| `tests/test_review_sequence.py` | 3 | 0 | assertion |
| `tests/test_review_tier.py` | 2 | 0 | assertion |
| `tests/test_run_selection_policy.py` | 1 | 0 | assertion |
| `tests/test_runner_shared.py` | 11 | 0 | assertion, schema-1 refusal |
| `tests/test_runner_shared_restored_behavior.py` | 1 | 0 | assertion |
| `tests/test_scope_match.py` | 2 | 0 | assertion |
| `tests/test_selector_resolver_matrix.py` | 3 | 0 | assertion |
| `tests/test_show_history.py` | 6 | 0 | assertion |
| `tests/test_spec_id6_filenames.py` | 6 | 0 | assertion, schema-1 refusal |
| `tests/test_spec_review_gate_kind.py` | 4 | 0 | assertion |
| `tests/test_specs_metadata_duplicate_bullet.py` | 1 | 0 | assertion |
| `tests/test_status_set.py` | 82 | 0 | assertion, removed-API, schema-1 refusal |
| `tests/test_status_set_meta_writer.py` | 10 | 0 | assertion, schema-1 refusal |
| `tests/test_writers_create_summary.py` | 34 | 0 | assertion, removed-API, schema-1 refusal |
| `tests/test_writers_merge_independence.py` | 2 | 0 | assertion |
| `tests/test_writers_obligations.py` | 16 | 0 | assertion, removed-API, schema-1 refusal |
| `tests/test_writers_scope_fields.py` | 9 | 0 | assertion, removed-API, schema-1 refusal |

## Proposed changes (ordered, validatable)

1. E-01: Create scratch worktree `.aw/state/89mtbl/scratch` with both cutover patches staged.
2. E-02: Record the F-02 `text_only`/`raw_fields` contract; switch `tests/record_builder.py` (all 8 types, `assert_field`/`assert_no_field`) and `tests/support.py` to log format.
3. E-03: Repoint `tools/fixture_codemod.py::_registry_field_map` onto `m0001_convert.FIELD_DESTINATIONS` and align its rewrite/proof target with F-02.
4. E-04: Update and pass the four builder and codemod test modules (and fixtures/golden baseline); measure the core-gate failure census in F-04.
5. E-05: Regenerate `.aw/system/cutover/metastore-code.cutover.patch`, remove the scratch worktree, pass the guard test, and commit path-scoped.

```mermaid
flowchart TD
    E01["E-01: Create scratch worktree with both patches"] --> E02["E-02: Record F-02 contract; switch record_builder and support.py to log format"]
    E02 --> E03["E-03: Repoint fixture_codemod onto m0001_convert.FIELD_DESTINATIONS"]
    E03 --> E04["E-04: Pass 4 builder/codemod test modules; measure F-04 census"]
    E04 --> E05["E-05: Regenerate code patch, run guard test, commit"]
```

## Deferred / out of scope (with reason)

- Slow end-to-end integration test `tests/test_record_builder_slow.py` (blocked by downstream production-fix plans `fljn9b`, `szykgd`, `lec341` and newly filed defects `0b3ynm` and `2etrjf`): deferred to rollup plan `x1mmdp` E-04/V-04 per maintainer resolution of `OQ-01`.
  - Carrier: x1mmdp
- Production cutover fixes for missing CLI creator log fields (`0b3ynm`) and `cli._find_type_records` bare-repo context (`2etrjf`): split into Order 322 child plan `6cltab` ahead of `x1mmdp` per maintainer resolution of `OQ-01`.
  - Carrier: 6cltab
- Converting the remaining failing test modules that call removed legacy APIs or fail on the switched tree (starting from F-04): batch children `nv3upa` through `x3mig6`.
  - Carrier: nv3upa
- Updating exact-spelling rows, settling the `review-pilot` corpus, and assembling the final refusal list: narrowed parent step.
  - Carrier: x1mmdp
- Applying the cutover patches on the real tree: attended cutover commit.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. No live code or test files are modified outside `.aw/system/cutover/metastore-code.cutover.patch`.
- Under-scope: none. Backlog `ldfefd`'s builder, `assert_field`/`assert_no_field`, `text_only`/`raw_fields` contract, `tests/support.py` alignment, codemod, and refreshed census items map to E-02 through E-05.

## Required tests / validation

- Builder and codemod suites in `.aw/state/89mtbl/scratch`: `python3 -m pytest -o addopts="" -m '' tests/test_record_builder.py tests/test_record_builder_slow.py tests/test_record_builder_assert_field.py tests/test_fixture_codemod.py` (V-04).
- Bare core-gate census measurement `python3 -m pytest` in `.aw/state/89mtbl/scratch` (V-04).
- Cumulative patch guard test `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` in the executing checkout (V-05).

## Spec / documentation sync

No spec or documentation change is needed in this plan. Spec `4sd62s` Sections 4.1 through 4.3 already define the log format, review-event model (Section 4.1a), and cutover, and `.aw/system/cutover/metastore-docs.cutover.patch` already updates the documentation and templates. This plan brings the shared test builder and codemod inside the cutover code patch into line with them.

## Open questions

### OQ-01: How to break the circular dependency blocking `tests/test_record_builder_slow.py` in E-04/V-04?
- Blocking: yes
- Status: resolved
- Owner: maintainer
- Carrier: x1mmdp
- Context: `tests/test_record_builder_slow.py` checks end-to-end visibility (`aw find -p`, `aw attention`, `aw check all`) and builder-vs-CLI parity across record types on the switched cutover tree. Six of its seven tests fail (`test_parity_backlog` passes) because of five production cutover gaps outside `89mtbl`'s scope: three already owned by downstream approved plans that depend on `89mtbl` (`fljn9b` Order 314 for 5 backlog `aw check all` errors; `szykgd` Order 315 for spec `attention.history-missing` and release `release.version-missing`; `lec341` Order 320 for `research_cmd.py::_write_planned_research_file` dropping planned fields), plus two newly discovered gaps filed as open backlog items (`0b3ynm`: four CLI creators `ipd_authoring.py::run_scaffold`, `specs.py::run_new`, `releases.py::_create_release_via_meta`, and `prompts.py::run_new` omit `title`, `set`, or `order` in `artifact_meta.create`; `2etrjf`: `cli.py::_find_type_records` calls `resolve_project_context` instead of `artifact_meta.legacy_context` on bare temp repos, dropping research records in `aw find -p`, sibling of `ggp2pf`). Because `fljn9b`, `szykgd`, and `lec341` cannot execute until `89mtbl` completes, requiring `tests/test_record_builder_slow.py` to exit 0 inside `89mtbl` creates a circular dependency.
- Options:
  1. Narrow `89mtbl` E-04/V-04 to require the three unit/codemod suites (`tests/test_record_builder.py`, `tests/test_record_builder_assert_field.py`, `tests/test_fixture_codemod.py` plus `tests/test_fixture_codemod_slow.py`, all currently passing 42/42), defer `tests/test_record_builder_slow.py` to `x1mmdp` after all production-fix children execute, and graduate backlog items `0b3ynm` and `2etrjf` into a new production-fix child plan ahead of `x1mmdp`.
  2. Re-order the dependency graph so `fljn9b`, `szykgd`, `lec341`, and a new child plan for `0b3ynm` and `2etrjf` run before `89mtbl`, then re-run `89mtbl` with `tests/test_record_builder_slow.py` enabled.
  3. Expand `89mtbl` scope to patch all five production gaps inside `89mtbl` directly and supersede overlapping production edits in `fljn9b`, `szykgd`, and `lec341`.
- Recommendation: Option 1 (strong). It unblocks the entire downstream `metastore` batch immediately using the already-verified patch snapshot on `aw/lane/89mtbl`, preserves the clean separation between test-harness work and production-fix plans, and keeps `tests/test_record_builder_slow.py` as a full end-to-end gate at `x1mmdp` without weakening any test assertion.
- Resolution or deferral rationale: RESOLVED 2026-11-27 by the user via /askme: Defer slow integration test to final rollup plan x1mmdp and add a child plan for 0b3ynm and 2etrjf. No reason was given. Authored Order 322 child plan `6cltab` (added to orchestrator `63ib9r` and `x1mmdp` `- Item-Dependencies:`) and deferred `tests/test_record_builder_slow.py` to `x1mmdp` E-04/V-04.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition) - as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction - name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the `git worktree add --detach .aw/state/89mtbl/scratch HEAD` command, both `git apply --index` commands (for `.aw/system/cutover/metastore-docs.cutover.patch` and `.aw/system/cutover/metastore-code.cutover.patch`) with exit status 0, and the base tree id recorded in F-01.
  - Observed evidence:
    - `git worktree add --detach .aw/state/89mtbl/scratch HEAD` -> exit 0 (detached HEAD `188044b31821eea2932047e63a47b9ad36b2b1d1`).
    - `git apply --index .aw/system/cutover/metastore-docs.cutover.patch` -> `docs_apply_exit=0`.
    - `BASE=$(git write-tree)` -> `3f1ce679f1f827835969cf2c92436d9d27aa4478` (recorded in F-01).
    - `git apply --index .aw/system/cutover/metastore-code.cutover.patch` -> `code_apply_exit=0`.
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste F-02 with the `text_only`/`raw_fields` contract and one concrete example call of each form; the diff hunks in `tests/record_builder.py` setting `RECORD_FORMAT = "log"` and adding the log branch of `assert_field`/`assert_no_field`; `python3 -c "import tests.support"` exiting 0 in the scratch worktree; and a verification run (code paths updated by E-02) building one record of each of the 7 log-backed artifact types (`ipd`, `spec`, `backlog`, `research`, `release`, `prompt`, `walkthrough`) reading each back via `artifact_meta.read`, plus one `review` record verified via `review_findings.parse_review_file` and `artifact_meta.history(subject)` showing the `op: "review"` event.
  - Observed evidence:
    - F-02 recorded above with concrete example calls for `text_only=True`, disk creation / `RecordBuilder.materialize`, and `raw_fields` (in-memory and on-disk).
    - `tests/record_builder.py` diff hunk (`RECORD_FORMAT`): `-RECORD_FORMAT = "legacy"` -> `+RECORD_FORMAT = "log"`.
    - `tests/record_builder.py` `assert_field` / `assert_no_field`: switched to `_load_verified_log_state(record_path, text, resolved_type, field)` (verifying on-disk mirror + `meta/<id6>.jsonl` via `artifact_meta.read`) and `_read_review_observed(record_path, text, field)` (verifying Section 4.1a review mirror + subject log `op: "review"` events).
    - `python3 -c "import tests.support; print('import tests.support OK')"` in scratch worktree -> `import tests.support OK` (exit 0).
    - 8-record-type verification run in scratch worktree (exit 0):
      ```text
      OK ipd         id=v02ipd status=draft title='V02 Plan'
      OK spec        id=v02spc status=draft title='V02 Spec'
      OK backlog     id=v02bkl status=open title='V02 Backlog'
      OK research    id=v02res status=reference title='V02 Research'
      OK release     id=v02rel status=planned title='Release: 1.2.3'
      OK prompt      id=v02prm status=pending title='V02 Prompt'
      OK walkthrough id=v02wlk status=None title='V02 Walkthrough'
      OK review      rounds=1 subject_review_events=1 op=review verdict=APPROVE
      ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste F-03 naming `m0001_convert.FIELD_DESTINATIONS`, the `_registry_field_map` diff hunk in `tools/fixture_codemod.py`, and the `python3 tools/fixture_codemod.py --dry-run --format json tests/test_fixture_codemod.py` output exiting 0 in the scratch worktree.
  - Observed evidence:
    - F-03 recorded above naming `agent_workflows/migrations/m0001_convert.py::FIELD_DESTINATIONS` and `tools/fixture_codemod.py::_registry_field_map`.
    - `tools/fixture_codemod.py` `_registry_field_map` diff hunk: replaced removed `_LEGACY_BULLET_LABEL`, `_RESEARCH_YAML_KEY`, and `_PROMPT_COMMENT_KEY` loops with `dest_map = _m0001_convert.FIELD_DESTINATIONS.get(record_type, {})` filtering `dest.kind in ("identity", "status", "log_field")`.
    - `python3 tools/fixture_codemod.py --dry-run --format json tests/test_fixture_codemod.py` in scratch worktree -> exit 0, JSON totals: `{"modules": 1, "sites": 5, "rewrites": 0, "standard_rewrites": 0, "invalid_input_rewrites": 0, "refusals": 5, "by_reason": {"dynamic-construction": 0, "unsupported-shape": 0, "not-equivalent": 0, "legacy-format subject": 0, "displayed-output assertion": 0, "setter-byte assertion": 5, "body prose": 0}, "by_disposition": {"hand": 0, "legacy-kept": 5}}`.
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the pytest summary line for each of the four modules (`tests/test_record_builder.py`, `tests/test_record_builder_slow.py`, `tests/test_record_builder_assert_field.py`, `tests/test_fixture_codemod.py`) showing every test PASSED with exit 0 in the scratch worktree; then paste F-04 containing the per-module failure census table and the bare core-gate summary line.
  - Observed evidence:
    - `tests/test_record_builder.py`: `15 passed in 3.80s` (exit 0; includes `test_materialize_accepts_repo_relative_and_records_relative_destinations`).
    - `tests/test_record_builder_assert_field.py`: `15 passed in 3.48s` (exit 0).
    - `tests/test_fixture_codemod.py`: `11 passed in 9.60s` (exit 0).
    - `tests/test_fixture_codemod_slow.py` (additional codemod verification): `2 passed in 5.43s` (exit 0).
    - `tests/test_record_builder_slow.py`: measured `6 failed, 1 passed in 7.49s` (`test_parity_backlog` passed) due to out-of-scope production cutover gaps (`fljn9b`, `szykgd`, `lec341`, `0b3ynm`, `2etrjf`); deferred to `x1mmdp` E-04/V-04 with new Order 322 child plan `6cltab` per maintainer resolution of `OQ-01` (`219-89mtbl-a1-89mtbl-slow-tests-circular-dep`).
    - Bare core-gate census (`python3 -m pytest --tb=line` in scratch worktree, exit 1): `692 failed, 2243 passed, 1 skipped, 11 warnings, 66 errors in 121.03s (0:02:01)` across 86 modules (full table recorded in F-04 above).
  - Result: pass
- [x] V-05 validates E-05
  - Required evidence: paste `git apply --stat .aw/system/cutover/metastore-code.cutover.patch`, the `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py` run with all 3 tests PASSED, `git worktree list` showing `.aw/state/89mtbl/scratch` removed, `git status --short` confirming no live edits outside `- Scope-Paths:`, and the `aw commit 89mtbl` output naming the commit hash.
  - Observed evidence:
    - `git apply --stat .aw/system/cutover/metastore-code.cutover.patch`: `67 files changed, 4111 insertions(+), 5890 deletions(-)` (exit 0).
    - `python3 -m pytest -o addopts="" tests/test_metastore_cutover_code_patch.py`: `3 passed in 0.40s` (exit 0).
    - `git worktree list`: `.aw/state/89mtbl/scratch` removed (no scratch worktree listed).
    - `git status --short` after committing companion records (`f1f15ba5cef428208ecd85513fcebe340fb866ca`) and code patch (`a4bad2682eb0f193d7c45dcaa85d9e8564bb8711`): only `.aw/records/plans/pending/20261125-metastore-306-89mtbl-switch-the-shared-test-record-builder-and-codemod-to-the-log.ipd.md` modified; no live code or test edits outside `.aw/system/cutover/metastore-code.cutover.patch`.
    - `aw commit 89mtbl` on patch: `aw commit: committed 1 path(s): a4bad2682eb0f193d7c45dcaa85d9e8564bb8711`; out-of-scope backlog paths (`0b3ynm`, `2etrjf`) from `OQ-01` resolution justified in begin receipt via `aw commit 89mtbl --scope-reason`.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` (`hdwqex`) is executed; open questions: none open. Code and tests are edited ONLY inside `.aw/state/89mtbl/scratch` and packaged into `.aw/system/cutover/metastore-code.cutover.patch`. Scope fence: `- Scope-Paths:` is a declaration; any needed edit outside it must be justified at finalize (`--scope-reason`), and any declared path left unmodified must be acknowledged (`--scope-ack`). Safety stop conditions: stop and report rather than editing live production code outside the scratch worktree or weakening test assertions if a patch hunk rejects, an unexpected failure occurs on unmodified code, or an unresolvable concurrent-edit conflict occurs. Honesty rule: you MUST paste the ACTUAL runner output of every command named in V-01 through V-05; never claim a result you did not run. Commits: commit only through `aw commit 89mtbl -- <paths>`; never push. Lifecycle transition: after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence, in a managed runner lane stop after committing the updated plan and let the runner run `aw ipd finalize`; in a hand-run session run `aw ipd finalize` to move the plan to `.aw/records/plans/executed/` (never use a raw `git mv` to `executed/`).
