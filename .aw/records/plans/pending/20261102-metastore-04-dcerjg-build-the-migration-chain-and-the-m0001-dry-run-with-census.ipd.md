# IPD: Build the migration chain and the m0001 dry run with census, renames, citations and round trip

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` makes the cutover one scripted migration (5.1, 5.2), and none of it exists. `agent_workflows/migrations/` does not exist; `aw migrate` does not exist (the only migration verbs are the top-level `aw migrate-layout` and `aw specs migrate`, `cli.build_parser`); `project_schema.parse_portable_policy` knows no `metadata_schema` key; `aw install` has no pending-migration question and its `-y/--yes` is documented as "Skip preflight confirmations." Measured this session: 35 tracked records outside comms match `artifact_naming._LEGACY_TIMESTAMP_RE` (the spec's 34 plus one research template), 7 of them are misread by `artifact_naming.parse_clustered`, renaming them touches 2,035 citations in 457 files once the scan roots are widened (OQ-27), and the gitignored history sidecar holds 481 records for 325 `id6` values that exist only on this machine. The code for the attended cutover (Order 13) must be written and proven on a COPY first (spec section 7 phase A step 3), or the one irreversible commit runs untested code.
- Scope: Add the numbered migration chain (`agent_workflows/migrations/`, the `metadata_schema` stamp in the resolved `project.json`, `aw migrate metadata`, `aw migrate layout` as the new spelling of `aw migrate-layout`), the `aw install` pending-migration prompt and `--migrate`, and `m0001_metadata_v2` with: the step-1 preflight and `--force`/`--force-worktree`; the step-2 sidecar import and orphan export; the step-3 legacy-name renames (OQ-26 logged-Order rule, OQ-28 checkpoint-at-old-path plus `rename` event) and citation rewrite over widened scan roots (OQ-27); the step-4 conversion of artifacts, walkthroughs, roadmap, staged prompts and review files; the step-4a terminal-exception marker accepted by the two commit hooks; step-5 target-repository cleanup; the step-6 field census and round-trip verifier; and a description seam that Order 05 fills. Everything runs ONLY on test fixtures and on a disposable clone of this repository; this plan never migrates this checkout. EXCLUDES: the description journal and model generation (Order 05, `ya4ee4`); switching the toolkit's loader and writer to logs, moving the legacy loader into `m0001`, the real cutover run, and flipping `CURRENT_METADATA_SCHEMA` to 2 (Order 13, `cxxmyv`); removing the sidecar writer and the `history.jsonl` lines from `engine.py` and `placement_switch.py` (Order 13); deleting INDEX/STATUS code (Order 11, `9o83cr`); `aw check meta` (Order 08, `ffceq0`).
- Scope-Paths: agent_workflows/migrations/__init__.py, agent_workflows/migrations/chain.py, agent_workflows/migrations/m0001_metadata_v2.py, agent_workflows/migrations/m0001_preflight.py, agent_workflows/migrations/m0001_renames.py, agent_workflows/migrations/m0001_convert.py, agent_workflows/migrations/m0001_verify.py, agent_workflows/artifact_meta.py, agent_workflows/project_schema.py, agent_workflows/install_wizard.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/completion.py, agent_workflows/engine.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, tests/test_migrations_chain.py, tests/test_m0001_preflight.py, tests/test_m0001_renames.py, tests/test_m0001_conversion.py, tests/test_m0001_roundtrip.py, tests/test_m0001_gate_marker.py, tests/test_install_migrate_prompt.py, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md
- Item-Dependencies: executed:tve77h
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 4
- Highest E allocated: 16
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dcerjg
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Build and prove, on fixtures and on a disposable clone, every piece of the one-time `aw migrate metadata` cutover except model generation and the storage switch, so that Order 13 runs code that has already produced a complete, verified, idempotent migration of a full copy of this repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: the migration chain, the stamp and the commands

- [ ] E-01 Before any edit, save `aw check --agent` output to `.aw/state/dcerjg/check-before.jsonl` (the V-16 baseline). Create `agent_workflows/migrations/__init__.py` and `agent_workflows/migrations/chain.py`: a `Migration` record (`number`, `name`, `target_schema`, `is_pending(repo) -> bool`, `run(repo, *, apply, force, force_worktree, describer=None)`), an ordered `MIGRATIONS` tuple holding `m0001` (`metadata-v2`, target 2), the constant `CURRENT_METADATA_SCHEMA = 1` (Order 13 flips it to 2 in the cutover commit), `read_metadata_schema(repo)` and `write_metadata_schema(repo, value)` against the `project_context.resolve_project_context` `config_project` path (never a hard-coded `.aw/config/project.json`), `repo_has_legacy_records(repo)` (any record with a `- Field:` bullet block before the first `##` or a `## Workflow history` section, READMEs excluded), and `require_current_schema(repo)` that raises with the exact text "run `aw migrate metadata`" when the stamp, or 1 when absent on a repository with legacy records, is below `CURRENT_METADATA_SCHEMA`. Call it from `artifact_meta`'s one cache-refresh entry point (the freshness check that every public read runs first, `tve77h` E-13), so every metadata-reading command reaches it through the one interface (5.3, C5) and no command needs its own call; `aw migrate`, `aw install`, `aw setup`, `aw doctor` and `aw --help` do not read metadata through `artifact_meta` and so never refuse. This is a one-line hook in `artifact_meta.py`, which is in Scope-Paths. Make `metadata_schema` a documented member of the portable policy: add it to `known_keys` in `project_schema.parse_portable_policy` AND to the fallback `known_proj_keys` set in `install_wizard` (the copy used when `parse_portable_policy` raises), add an optional `metadata_schema: Optional[int]` field to `project_schema.ProjectPolicySchema` that `to_dict` writes when set, and carry the parsed value through the `ProjectPolicySchema(...)` rebuild in `install_wizard`, so a reinstall never drops the stamp. Moving the key from `unknown_fields` to a field without these three edits would silently delete it on the next `aw install`, because `install_wizard` rebuilds `project.json` from named fields plus `unknown_fields`. `write_metadata_schema` writes the file atomically (temporary file plus `os.replace`, as `config.stamp_cutovers` and `install_wizard` do), keeps every other key and its value, and keeps the trailing newline (`tests/test_install_config_trailing_newline.py`). `parse_local_binding` is not changed: the stamp lives only in the portable `project.json`.
  - Depends on: none
  - Expected outcome: in a tmp repository, `write_metadata_schema(repo, 2)` adds `"metadata_schema": 2` to the resolved `project.json` and leaves `schema_version` and every other key unchanged; a following `aw install` into the same repository keeps `"metadata_schema": 2`; `require_current_schema` raises the named message when `CURRENT_METADATA_SCHEMA` is 2 and the stamp is absent on a legacy fixture, and returns silently under the shipped value 1, so no command in this repository refuses before the cutover; with `chain.CURRENT_METADATA_SCHEMA` monkeypatched to 2, `artifact_meta.read(<id6>)` on a legacy fixture raises naming `aw migrate metadata` (AC-11 case 1 at the interface; in phase A no CLI command reads through `artifact_meta` yet, so the CLI-level refusal is demonstrated by `cxxmyv` after Orders 08 and 09 have moved the readers).
  - Execution state: pending

- [ ] E-02 Add the `aw migrate` command group in `cli.build_parser` with leaves `metadata` (dry run by default; `--apply`, `--force`, `--force-worktree`, `--agent`, `--json`) and `layout` (the same arguments and dispatch as `aw migrate-layout`, which stays as an alias printing no new warning). Declare both leaves in `command_surface` (`metadata` as `command_class="mutation"`, `mutation_gate="confirmation"`, `human_recipe="preview"`, mirroring the `migrate-layout` declaration) and add the `layout` positional choices to `completion` the way `migrate-layout action` is handled.
  - Depends on: E-01
  - Expected outcome: `aw migrate --help` lists `metadata` and `layout`; `aw migrate layout status` and `aw migrate-layout status` produce identical output; `tests/test_command_surface_declarations.py` reports no undeclared leaf.
  - Execution state: pending

- [ ] E-03 Add the pending-migration step to `aw install` and `aw setup` (`cli._run_install`, `cli._install_all`, `cli._run_setup`, and the `engine` install path they call): after the bundle install, if the repository has NO legacy records and no stamp, write `metadata_schema: CURRENT_METADATA_SCHEMA` and report nothing pending (5.3); otherwise list each pending migration and, only when stdin and stdout are a terminal, ask "Run migration 0001 metadata-v2 now? [y/N]"; with no terminal, print the pending migration and the exact command `aw migrate metadata`. `-y/--yes` never answers this question. Add `--migrate` to `install` and `setup`, which answers yes without a terminal and passes neither `--force` nor `--force-worktree`. A repository with legacy records is never stamped by install.
  - Depends on: E-01
  - Expected outcome: the four AC-28 cases and AC-11 cases (2) and (3) hold in tmp repositories, with every record byte-identical whenever the migration does not run.
  - Execution state: pending

### Task group 2: preflight, journal and sidecar

- [ ] E-04 Create `agent_workflows/migrations/m0001_preflight.py` implementing 5.2 step 1 in this order: (1) WORKTREE: refuse when the absolute `git rev-parse --path-format=absolute --git-dir` differs from `ipd_lifecycle.checkout_git_common_dir(repo)` (in this review lane they are `.git/worktrees/<name>` and `.git`), naming `--force-worktree`; `--force` never overrides it, and `None` from `checkout_git_common_dir` refuses as "cannot establish the common directory". (2) UNCOMMITTED: `git status --porcelain -- <records root>` non-empty. (3) LOCK: `platform_lock.probe_free(runner_shared.integration_lock_path(repo))` is False; `None` (unanswerable) is reported as its own condition and refuses like False, because `probe_free` documents that `None` is not proof the lock is free. (4) LANES: each linked worktree from `git worktree list --porcelain` whose branch changes a path under the plans tree and for which `runner_shared.lane_work_has_landed` is not True, listed by worktree, with `None` shown as "unknown" rather than dropped. Each condition refuses and is named; `--force` continues past (2) to (4) and the report names each overridden condition and its 5.2 consequence; refusals write nothing (no journal, no scratch). When the lock is free, the apply holds `runner_shared.integration_lock(repo, holder_label="aw migrate metadata")` for its whole duration.
  - Depends on: E-01
  - Expected outcome: every AC-27 case and AC-22 case (1) hold in tmp repositories; the tmp tree is byte-identical after each refusal.
  - Execution state: pending

- [ ] E-05 In `agent_workflows/migrations/m0001_metadata_v2.py`, build the migration journal on the `layout_migration.MigrationManager` components (reuse its writer lock, atomic journal save and load, and its resume and rollback model; do not write new ones) at a per-migration path under the resolved `state_durable` root (`migrations/m0001/journal.json`), never the shared `migration_transaction.json`. The journal records: the minted `id6` per legacy path (so every dry run and the apply mint the same value), the old-to-new rename map, per-step progress, the description-seam results, the orphan export path, and the terminal-exception marker (E-11). Dry run is the default; the scratch copy (records root plus the citation scan roots) lives under the same gitignored directory; `--apply` applies the verified scratch result to the checkout with per-file backups, and an interrupted apply resumes or rolls back from the journal, never restarts.
  - Depends on: E-04
  - Expected outcome: a fault injected between two applied files leaves a journal from which `aw migrate metadata --apply` resumes to the same final tree as an uninterrupted run, and a rollback restores the pre-apply bytes exactly; a dry run writes only under the gitignored journal directory.
  - Execution state: pending

- [ ] E-06 Implement step 2 (sidecar first) in `m0001_metadata_v2.py`: read `.aw/records/history.jsonl` before any other step; the sidecar is EXPECTED when the records tree has at least one spec or backlog item with an `id6`; the preflight line reports presence and record count; a missing expected sidecar refuses unless `--force` (the only non-step-1 refusal `--force` overrides). Classify each record by whether its `id6` resolves to a tracked record (filename `id6` or in-file `- Id:`): resolvable records are queued, in sidecar file order and unchanged, for `legacy` events with `source: sidecar` and `observed_day` from `date`; unresolvable ones are written to a gitignored `sidecar-orphans.jsonl` export beside the journal, counted per `id6` in the census, and get no log. Rename and group records stay `legacy`. On apply, move the sidecar file into the export directory and remove the `records/history.jsonl` line from the TARGET repository's `.aw/.gitignore`.
  - Depends on: E-05
  - Expected outcome: AC-30 case (1) and the `.aw/.gitignore` part of case (2) hold on a fixture; a lane-style worktree with `--force-worktree` and no sidecar refuses naming the sidecar.
  - Execution state: pending

### Task group 3: legacy-name renames and citations (step 3)

- [ ] E-07 Create `agent_workflows/migrations/m0001_renames.py` with `classify_name(name)`, which tests `artifact_naming._LEGACY_TIMESTAMP_RE` BEFORE `artifact_naming.parse_clustered` (so `20260712-1033-01-assess-bugs-...` is legacy, not `set=1033, id6=assess`), and `build_rename_map(repo, journal)` for every tracked artifact, walkthrough and roadmap with a legacy name, excluding comms, `.data/` files, READMEs and the six templates named in OQ-02: mint a repository-unique `id6` with `artifact_core.mint_id6` for each id-less record and journal it; keep an existing `- Id:`; `set` is the existing `- Set:` or else the record's `id6`; `order` is the logged `- Order:` when present, otherwise the filename `NN` (OQ-26 correction); emit `YYYYMMDD-<set>-<NN>-<id6>-<slug>.<type>.md` with the original date, slug and facet. Do not call `artifact_rename.compute_target_name`, which hard-codes `set_id=mint_id6, order=1`. Refuse the map when two plans would share a Set and order.
  - Depends on: E-05
  - Expected outcome: on this repository (measured at authoring and re-checked at review: 35 legacy-timestamp files outside comms, minus the one OQ-02 template) the map has 34 entries: 28 minted (17 specs, 11 walkthroughs) and 6 preserved; the BAR is re-derived at execution time as "every `_LEGACY_TIMESTAMP_RE` record outside comms and the OQ-02 exclusions is mapped, each id-less one minted, each `- Id:` one preserved", and the fixed rows below are stable code facts of terminal records, with `wvlk84` mapped to `20260817-awphysical-17-wvlk84-assess-bugs-leftover-remove-dataloss.ipd.md`, `lus9ou`/`7qx7ys`/`8q6yr9` to `plans-adopter` orders 00, 06, 07, and `4o5lt9`/`4w7d6s` to Sets equal to their own `id6`.
  - Execution state: pending

- [ ] E-08 In `m0001_renames.py`, add `plan_citation_rewrites(repo, rename_map)` calling `artifact_refs.plan_reference_rewrites_with_warnings` with `scan_roots=artifact_core.REFERENCE_SCAN_ROOTS + ("agent_workflows", "docs", ".aw/system", "CHANGELOG.md")` (passed as an argument; `REFERENCE_SCAN_ROOTS` itself is unchanged so `aw rename` keeps its roots), then drop every edit that falls inside text that step 4 imports byte for byte (each `## Workflow history` line, sidecar objects, legacy `- Verdict:` values) and every entry of a named exemption list (deliberate old-format examples: the legacy-name fixture in `tests/test_plans_rename_selectors.py` and code comments in `artifact_naming`, `artifact_refs`, `plans_refs`, `artifact_rename` that describe the old grammar). The step captures each history line BEFORE any rewrite, applies the remaining edits in the scratch copy, and reports hits per location (top-level directory, or records type) plus every citation left unchanged with its reason.
  - Depends on: E-07
  - Expected outcome: the dry-run report on the clone shows per-location counts that sum to the planned edits, 0 ambiguity warnings, a non-empty "left unchanged" list naming the history-line and exemption reasons, and no edit inside any `## Workflow history` section.
  - Execution state: pending

### Task group 4: conversion, terminal marker and cleanup (steps 4, 4a, 5)

- [ ] E-09 Create `agent_workflows/migrations/m0001_convert.py` (and, in `artifact_meta.py`, the `roadmap` registry entry of OQ-02) that builds each log through `artifact_meta`'s event model (tve77h) using the legacy loader for parsing: one append with `append` 0: `seq` 0 `checkpoint` with every registry field under its 4.2/4.5c name (`Kind` to `plan_role`, research `kind` to `research_kind`, prompt `Kind` to `prompt_kind`, D177 facets to `ace`/`model`), `path` (the OLD path for a renamed record), `filename_date`, `created_day` when known (never the filename date), `last_history_day` from `attention_contract.newest_history_record`, parsed `item_dependencies`, `scope_result: exceeded` plus `out_of_scope_paths` and `scope_exceeded_raw` for a `Scope-Exceeded` bullet, and `short_description` plus `description_source`, `description_model`, `description_prompt_version` only when the `describer` seam returned a value; then for a renamed record one `rename` event (verb `rename`, new `path`, `actor.tool: aw migrate metadata`); then `legacy` events (`source: history` in file order, then `source: sidecar` in sidecar order) with the original line, `observed_day`, original position and `ordering_confidence: unknown`; then one `review` event per `## Round <n>` of each review file of the subject, with `review_kind` (`refinement` for `specflow` files, else `gate`), `review_ref` per 4.1a K4, and `legacy_verdict`/`reviewer`/`observed_day`/`findings_summary` on the last round only (K5a). Every event's `at` is the migration time; imported strings bypass only the length and control-character refusal (SR-903). Never write `finalize` or `turn`.
  - Depends on: E-06, E-07
  - Expected outcome: the AC-32 fixture (two inline history lines, one sidecar record, a review file with two rounds) produces exactly checkpoint, legacy, legacy, legacy(sidecar), review, review in `seq` 0 to 5, all `append` 0, and replay equals checkpoint state plus the review values; a renamed fixture's path history is old path then new path.
  - Execution state: pending

- [ ] E-10 In `m0001_convert.py`, rewrite each file in the scratch copy: artifacts get `---`/`id`/`status`/`---` plus the `aw-managed` banner of 4.1, both rendered by the same `artifact_meta` mirror writer; walkthroughs and the roadmap get `---`/`id`/`---` plus the banner and no status (a free-prose `- Status:` line moves into the body unchanged); staged prompts get line 1 the single `aw-managed-prompt` comment rendered by `artifact_meta`'s in-file mirror writer (`tve77h` E-07 and E-15 own the exact text of 4.1; this plan never spells the banner or mirror text itself, so the migration and the post-cutover writer cannot disagree) and no `---`, with every key of the old `aw-prompt` comment moved to a log field or a census-recorded drop, and a prompt with no comment taking `status` from its disposition and `id`/`set`/`order` from its filename; review files get `subject`, `subject_type` and, when K4 assigns one, `ref` front matter plus the review banner, with the `## Round`, `### Findings` and `### Decisions` sections byte-identical; prose fields (`Summary`, `Scope`, `Concern`, `Motivation`, `Relation to prior work`) move to body sections; the bullet block and the `## Workflow history` section are deleted. Comms, `.data/` files, READMEs and the six templates stay byte-identical.
  - Depends on: E-09
  - Expected outcome: AC-29 case (1), AC-40 cases (1) and (2) and AC-14 (migration form) hold on fixtures; a migrated staged prompt has no `---` line and its comment contains no instruction addressed to an agent.
  - Execution state: pending

- [ ] E-11 Implement steps 4a and 5 on the scratch result: step 5 deletes `plans/STATUS.md` and every `INDEX.json`/`INDEX.md` under plans, research and prompts, and removes the INDEX ignore lines from the target repository's `.aw/.gitignore`; step 4a writes, after the apply stages the migration's own path list, a positive marker into the journal holding the migration id and the `git write-tree` id of the staged index. In `hooks/executed_transition_gate.check` and `hooks/backlog_blocking_close_gate.check`, accept a staged change ONLY when such a marker exists at the journal path resolved from `project_context.resolve_project_context(repo).logical_roots` `state_durable` (never a literal path) and its tree id equals the current `git write-tree`; any other staged content, including the same paths with one extra edit, is judged by the existing rules. The hooks only READ the marker; `m0001` deletes it after the commit succeeds (and on rollback), so a stale marker can never admit a later commit, and a marker whose tree id no longer matches is ignored and reported once on stderr. `git write-tree` is the only git write the hooks perform, and it writes only tree objects that already describe the staged index. `--no-verify` is never used or suggested.
  - Depends on: E-10
  - Expected outcome: in a tmp repository holding an executed plan and a release-blocking `done` backlog item, a staged migration result is refused by each hook without the marker, accepted with a matching marker, refused again after one extra staged edit, and refused after the marker is consumed by a completed commit.
  - Execution state: pending

### Task group 5: census, round trip, real-copy proof and commit

- [ ] E-12 Create `agent_workflows/migrations/m0001_verify.py` with the step-6 field census (AC-20): every distinct field name found before the first `##` heading, in research YAML, in `aw-prompt` comments and as D177 filename facets, each with its destination (log field, body section, review-event field, or a recorded drop with reason) and a count; `unknown-field` and unparseable-value refusals (for example an `Item-Dependencies` value outside the closed grammar); `plan_role` legacy values and absent-`Kind` counts; staged prompts with no comment; sidecar orphan `id6` values with counts; the excluded templates by name; the count of records with and without a `short_description`; and the rename and citation summaries. `--apply` refuses when the census has a refusal or when any record lacks a description the census does not list as a deliberate absence.
  - Depends on: E-08, E-10
  - Expected outcome: the census on the clone lists every field the corpus uses (70 bullet names measured this session plus YAML, comment and facet keys) with zero `unknown-field` refusals, and reports a nonzero "without description" count that makes `--apply` refuse when no describer ran.
  - Execution state: pending

- [ ] E-13 In `m0001_verify.py`, add the round-trip verifier (AC-10) and run it as part of every dry run and apply: replay each produced log through `artifact_meta`'s log loader (tve77h, pointed at the scratch records root) and assert that every legacy field value (under its new name, or found verbatim in the body or in `scope_exceeded_raw`) and every raw history line and sidecar object is recoverable byte for byte; that no two plans share a Set and order; that no artifact, walkthrough or roadmap name matches `_LEGACY_TIMESTAMP_RE`; and run `leak_sanitizer.scan_text` with `leak_sanitizer.build_ruleset(repo_root)` over every new log and mirror, refusing `--apply` on any `fail` (5.2 step 6, AC-16 "zero `fail` diagnostics"); `warn` findings are listed in the report and do not refuse, because imported legacy bytes are stored with `migration_import=True` and `tve77h` E-03 (d) already runs its own leak scan on them, so a `warn` here is a report, not a second gate. Then run `aw sanitize --agent` on the clone's staged tree in E-15. A second `--apply` on a stamped repository reports "metadata_schema is 2; nothing to do" and changes no file.
  - Depends on: E-12
  - Expected outcome: a fixture holding a history line longer than `MAX_PROSE_DESCRIPTIVE_LEN` (4,300) and one with a control character round-trips both byte for byte, while the same long value given to `artifact_meta`'s writer validation is refused; a fixture with a planted home-directory path in a field value makes `--apply` refuse on the sanitizer.
  - Execution state: pending

- [ ] E-14 Add the test modules, all on `tmp_path` fixture repositories built with real `git init`, calling the real functions and the real `aw` CLI leaves and asserting on outputs, exit codes and file bytes (no source reading): `tests/test_migrations_chain.py` (E-01, E-02, AC-11 cases with `CURRENT_METADATA_SCHEMA` patched to 2), `tests/test_install_migrate_prompt.py` (AC-28 with a pseudo-terminal for the yes and no cases), `tests/test_m0001_preflight.py` (AC-27 cases 1 to 4, AC-22 case 1, journal resume and rollback), `tests/test_m0001_renames.py` (AC-41 cases 2 and 3 on fixtures, the logged-Order rule, the Set-and-order collision refusal, citation exemptions and history-line protection), `tests/test_m0001_conversion.py` (AC-32, AC-29 case 1, AC-40 cases 1 and 2, AC-14 migration form, AC-14a case 5 with all four off-vocabulary verdict strings measured this session, AC-19 migration cases, AC-30 case 1), `tests/test_m0001_roundtrip.py` (AC-10 fixture cases, AC-20 fixture census, idempotence), `tests/test_m0001_gate_marker.py` (E-11 hook cases). Mark each `core`; any module whose slowest test exceeds 2 s in `--durations=10` is marked `slow` instead and named in V-14. Add `tests/test_m0001_conversion.py::...roadmap...` for the roadmap disposition and a project-schema test that a reinstall keeps the stamp (PR-001).
  - Depends on: E-01, E-02, E-03, E-04, E-05, E-06, E-07, E-08, E-09, E-10, E-11, E-12, E-13
  - Expected outcome: all seven modules pass under `python3 -m pytest -o addopts="" -n auto <modules>`, and the bare core gate stays inside its 30 s budget.
  - Execution state: pending

- [ ] E-15 Prove the migration on a COPY of this repository, never on this checkout: commit the E-01 to E-14 work first (E-16 may be split so that this commit precedes the proof), then `git clone --no-hardlinks <this checkout> tmp/dcerjg-clone` (the gitignored `tmp/` inside this checkout, so a runner lane keeps the clone inside its workspace), copy the gitignored `.aw/records/history.jsonl` into the clone when this checkout has one (a runner lane has none: record that, run the sidecar half with a synthetic sidecar of at least one resolvable and one orphan record, and leave the real-sidecar line to `cxxmyv` E-02, which already owns AC-22 case 2), and in the clone run, with the clone's own package (`cd tmp/dcerjg-clone && python3 -m agent_workflows ...`, which the `checkout_pin` re-exec rule resolves to the clone) (a) `aw migrate metadata` (dry run), (b) `aw migrate metadata --apply` (must refuse on missing descriptions), (c) a short driver `python3 -c` calling `m0001_metadata_v2.run(copy, apply=True, describer=<fixed-text fake>)`, (d) the step-7 commit via `aw commit --no-plan` with the migration's path list, running `python3 -m agent_workflows ipd-executed-gate` and the backlog close gate first, (e) `aw migrate metadata --apply` again, then (f) `git status --porcelain --ignored` in the clone. Step (c) needs a describer, so it exercises the seam with a fixed-text fake and is NOT evidence about real descriptions. Record wall time and peak scratch size. Delete the clone afterwards. Before and after, `git status --porcelain` of THIS checkout must be identical.
  - Depends on: E-14
  - Expected outcome: the dry run prints the preflight (sidecar presence and record count, real or synthetic as recorded), the rename map (34 entries at authoring; the bar is that every `_LEGACY_TIMESTAMP_RE` artifact, walkthrough and roadmap of the clone is mapped except the OQ-02 templates), per-location citation counts with 0 warnings, the census and a passing round trip; (b) refuses naming the missing descriptions; (c) applies; (d) both hooks accept the marked commit; (e) changes nothing; (f) shows no `records/history.jsonl`, no `STATUS.md` and no INDEX file.
  - Execution state: pending

- [ ] E-16 Add one `CHANGELOG.md` entry under `2.0.0 (pending)` (new `aw migrate metadata` dry-run command and `aw migrate layout` spelling; `aw install --migrate`; the migration does not yet run on any repository), with no em or en dashes. Run the named modules, the bare core gate `python3 -m pytest`, `make test-all` (not a phase end, but the migration touches many modules), and `aw check`; commit through `aw commit dcerjg -- <each changed path>` (E-15 needs the E-01 to E-14 code committed before it clones, so this is normally two commits: the code before E-15, the changelog and any E-15 fixes after it). Never push.
  - Depends on: E-14, E-15
  - Expected outcome: every run passes; `aw check` reports no error or warning that this plan introduced; each path-scoped commit's `git show --stat` lists only Scope-Paths files.
  - Execution state: pending

## Project conventions discovered (Step 0)

- Transactional migrations reuse `layout_migration.MigrationManager` (`_acquire_lock`, `_save_transaction`, `_load_transaction`, `resume_migration`, `rollback_migration`); spec 5.1 forbids new journal or lock components. Its shared journal path (`state/runtime/transactions/migration_transaction.json`) belongs to the layout migration, so m0001 needs its own path.
- Path roots come from `project_context.resolve_project_context` (`config_project`, `state_durable`, `records`), never `<repo>/.aw/...` literals (spec 4.5, 5.1).
- The integration lock is `runner_shared.integration_lock_path` and `runner_shared.integration_lock` (bounded, loud wait); a non-mutating probe is `platform_lock.probe_free`. Worktree identity is `ipd_lifecycle.checkout_git_common_dir`. Lane landing is `runner_shared.lane_work_has_landed` (True/False/None, None kept visible as unknown).
- Naming authority is `artifact_naming` (`_LEGACY_TIMESTAMP_RE`, `parse_clustered`); citations go through `artifact_refs.plan_reference_rewrites_with_warnings`, whose `scan_roots` is a parameter; ids are minted by `artifact_core.mint_id6` (repository-wide collision check).
- Every CLI leaf must be declared in `command_surface` (`command_surface.find_undeclared_leaves`, enforced by `tests/test_command_surface_declarations.py`); `migrate-layout`'s declaration is the template for a mutation verb with a confirmation gate.
- Descriptive-value safety is `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4,300; leak scanning is `leak_sanitizer.scan_text` with `leak_sanitizer.build_ruleset`.
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); a real model or network call from a test is refused by construction, as `runner_shared._assert_probe_spawn_is_permitted` does for the coverage probe.

## Findings

All values measured in this session at the current `HEAD` of this checkout.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `ls agent_workflows/migrations` fails; `cli.build_parser` has `migrate-layout` (top level) and `specs migrate` only | No migration chain and no `aw migrate` group exist. |
| F-02 | `git ls-files .aw/records` filtered by `_LEGACY_TIMESTAMP_RE`, comms excluded: 35 files: 5 executed plans, 15 implemented specs, 3 superseded specs, 11 walkthroughs, and `research/plan-review/20260712-0156-14-chatgpt-modular-report-template.md` | The spec's 34 plus one research template, which OQ-02 excludes. |
| F-03 | Of those, `parse_clustered` also matches 7: plan `20260817-1357-01-assess-...`, specs `...-agents-artifact-organization`, `...-honest-human-approval-attestation`, `...-prompt-purity-lint`, walkthroughs `...-assess-bugs-and-tests-...`, `...-agents-docs-...`, `...-mirror-workflow-pointer-...` | Classification must test the legacy form first (5.2 step 3). |
| F-04 | `grep '^- Id:\|^- Set:\|^- Order:'` on the 34: `lus9ou`, `7qx7ys`, `8q6yr9` (`plans-adopter`, orders 0, 6, 7), `4o5lt9` (no Set), `wvlk84` (`awphysical`, order 17), spec `4w7d6s` (no Set); the other 28 (17 specs, 11 walkthroughs) carry no `- Id:` | Matches OQ-26 and its round-18 correction exactly. |
| F-05 | `artifact_refs.plan_reference_rewrites_with_warnings` on a synthetic 34-entry map: default roots 1,951 hits in 423 files; with `agent_workflows`, `docs`, `.aw/system`, `CHANGELOG.md` added 2,035 hits in 457 files (agent_workflows 70, `.aw/system/workflows` 6, docs 5, CHANGELOG 3); 0 warnings both ways | Up from 1,940/419 at r18; widening adds 84 hits in 34 files. |
| F-06 | `python3` over `.aw/records/history.jsonl`: 481 records, 325 `id6`; 442 status/history, 20 rename, 19 group; by tree backlog 335, specs 124, research 11, plans 8, walkthroughs 2, roadmaps 1; 4 `id6` (`3srje9`, `6rya7d`, `jpmhjb`, `frq8c2`, one record each) match no tracked filename `id6` or in-file `- Id:` | Spec r9 said 8 records for 7 `id6`; the census must report the real count at run time. |
| F-07 | `git ls-files .aw/records` `.md`: 4,441 (4,415 non-README); 2,959 contain `## Workflow history`; 70 distinct `- Field:` names before the first `##` | Spec section 1 said 68 fields; the census, not this plan, is the registry check. |
| F-08 | Reviews: 1,289 `.review.md`; 24 whose filename `id6` differs from `Subject-Id` (all subject `18hh1u`); multi-file subjects `18hh1u` 24, `rtvdak`/`e25iy9`/`l4vw9o`/`urv602` 2 each; 35 off-vocabulary verdicts: `REVIEWED - MATERIAL CHANGES APPLIED` 20, `REVIEWED` 11, `REVIEWED - NO MATERIAL IMPROVEMENTS FOUND IN THIS ITERATION` 3, `REVIEWED - CONVERGED WITH REVISIONS` 1 | Matches the spec's r11 counts; 4 distinct strings for AC-14a(5). |
| F-09 | Staged prompts: 30 `.md` under `.aw/records/prompts` (README excluded), 25 with a leading `<!-- aw-prompt:` comment; 3 research files embed an `aw-prompt` comment below YAML (`8it88r`, `yq6aub`, `9bd3j8`, lines 14 to 15) | 5 prompts take status from disposition; OQ-04 decides the 3 research comments. |
| F-10 | `project_schema.parse_portable_policy` `known_keys` lacks `metadata_schema`; other keys land in `unknown_fields` | The stamp must be added as a known key. |
| F-11 | `hooks/executed_transition_gate._staged_plan_executed_transitions` flags a plan "ARRIVING in an `executed/` directory ... not ALREADY there at HEAD under the SAME `- Id:`"; `hooks/backlog_blocking_close_gate.check` delegates to `check_engine.check_release_gate_consistency` | The 5 renamed executed plans and every rewritten terminal file need the positive marker (5.2 step 4a). |
| F-12 | `cli` `install` `-y/--yes` help "Skip preflight confirmations."; `setup` `-y/--yes` "Install without per-repo prompts." | Neither may answer the migration question (5.1). |
| F-13 | `artifact_rename.compute_target_name` builds the `--to-id6` name with `set_id=mint_id6, order=1` (called from `artifact_rename.run_rename_generic`) | It cannot be reused for the OQ-26 rule. |
| F-14 | `.aw/.gitignore` line `records/history.jsonl`; INDEX lines for plans, research, prompts; tracked `.aw/records/plans/STATUS.md`; `engine.py` template and adder and `placement_switch.py` list also name `records/history.jsonl` | Target-repo lines are step 2/5 output; the source-code lines are Order 13's. |
| F-15 | `.aw/records/roadmaps/` holds 1 record (`7ny1bg`, bold-prose metadata, 1 sidecar record); `prompt-library/` 4 `.prompt.md` with no id; research templates `conformance-results-template.md` and the F-02 template; `research/reference/` 74 files with clustered names | Inputs to the by-name decisions of OQ-02. |
| F-17 | Re-measured at review (HEAD `4f09df0c7`): 35 tracked legacy-timestamp files outside comms (unchanged); 4,470 tracked `.md` under `.aw/records`, 2,898 with `## Workflow history`, 1,300 tracked review files; `install_wizard` rebuilds `project.json` from `ProjectPolicySchema` named fields plus `unknown_fields`, with a fallback `known_proj_keys` copy of the key set; `tve77h` E-01 registers seven types and no `roadmap`; this review lane has no `.aw/records/history.jsonl` | Counts drift (context only); the stamp needs a round-trip field (PR-001); a lane-run E-15 needs a synthetic sidecar (PR-004). |
| F-16 | `opencode` 1.18.35 and `agy` on PATH; clone size: `.git` 240 MB, 6,211 tracked files | A `--no-hardlinks` clone for E-15 is feasible in `/tmp`. |

## Proposed changes (ordered, validatable)

1. E-01 to E-03: chain, stamp, `aw migrate`, install prompt.
2. E-04 to E-06: preflight, journal, sidecar.
3. E-07, E-08: rename map and citation rewrite.
4. E-09 to E-11: conversion, file rewrite, terminal marker and cleanup.
5. E-12 to E-16: census, round trip, tests, real-copy proof, changelog and commit.

## Deferred / out of scope (with reason)

- The description journal, the tracked generation prompt, the tool-less model call and the cost trial; this plan provides only the `describer` seam and the census and refusal accounting.
  - Carrier: ya4ee4
- Switching `artifact_meta`'s loader and writer to logs, moving the legacy loader into `migrations/m0001_metadata_v2.py`, flipping `CURRENT_METADATA_SCHEMA` to 2, running the migration on this checkout, the real preflight sidecar line (AC-22 case 2), the real census orphan lines (AC-30 case 3), and final AC-10, AC-11, AC-16 and AC-41 evidence on the real repository, including AC-41 case 4's `aw show --history` display with the current name (the phase-A toolkit cannot read a v2 copy, C9).
  - Carrier: cxxmyv
- Retiring `record_history.append`, `append_advisory`, `append_rename` and removing `records/history.jsonl` from the `engine.py` template, the `engine.py` adder and `placement_switch.py` (AC-30 case 2, source half): done in phase A it would stop ignoring a sidecar the toolkit still writes, so a broad `git add` could commit purged records.
  - Carrier: cxxmyv
- Deleting INDEX and STATUS code and the `check.stale-index-*` rules (AC-9).
  - Carrier: 9o83cr
- `aw check meta`, which AC-29 case 2 and AC-40 case 4 use, and the 5.2 step 6 "`aw check meta` clean" condition.
  - Carrier: ffceq0
- A setter transition rewriting only the staged-prompt comment `status` (AC-40 case 3), and recording a NEW review round as one subject event (AC-14 writer form).
  - Carrier: xexn45
- `inferred-from-git` ordering for legacy events: optional in 5.2 step 4 ("can add"); every imported event uses `ordering_confidence: unknown` (OQ-05).
  - Carrier-Declined: optional by spec wording; adding it later needs no log-format change because `ordering_confidence` already exists.

## Scope check

- Over-scope: none. The hook edits (E-11) are additive marker acceptance; the `artifact_meta.py` edits are limited to the `roadmap` registry entry (OQ-02) and the one `require_current_schema` call in the read path (E-01); `install_wizard.py` gets the stamp round-trip (E-01).
- Under-scope: none for the spec items assigned to this step. Spec 5.1 (chain, stamp, install question, `--migrate`, naming), 5.2 steps 0 to 7 (step 6 without `aw check meta`, step 7 on the clone only), 4.1 by-name decisions, 4.2a layout, 4.1a K4/K5/K5a, OQ-12, OQ-26, OQ-27, OQ-28 are each covered by an E-item; the parts that can only happen at the cutover are carried above.

## Required tests / validation

New modules (all `core` unless E-14's duration rule moves one to `slow`): `tests/test_migrations_chain.py`, `tests/test_install_migrate_prompt.py`, `tests/test_m0001_preflight.py`, `tests/test_m0001_renames.py`, `tests/test_m0001_conversion.py`, `tests/test_m0001_roundtrip.py`, `tests/test_m0001_gate_marker.py`. Existing: `tests/test_command_surface_declarations.py`, `tests/test_layout_migration.py`, `tests/test_migrate_layout_cli.py`, `tests/test_plans_rename_selectors.py`, `tests/test_date_reader_clock_parity.py`. Gates: bare `python3 -m pytest`, `make test-all`, `aw check`.

Acceptance criteria of spec `4sd62s` this plan OWNS (proven here on fixtures and on the clone; Order 13 re-demonstrates on the real repository where noted):

- AC-10: fixture round trip with the long and control-character lines (E-13), clone dry run, apply, second apply and round trip (E-15). Final real-repo run: `cxxmyv`.
- AC-11: mechanism (the read-path call in `artifact_meta`) and all three cases with `CURRENT_METADATA_SCHEMA` patched to 2 (E-01, E-03); the shipped value flips in `cxxmyv`, which re-demonstrates.
- AC-14 (migration form): every migrated review round becomes one subject event, no review log, K4 bindings for the 24 own-`id6` files and the 4 pairs (E-09, E-10).
- AC-14a case 5: all 4 off-vocabulary strings recovered byte for byte (E-14).
- AC-19 (migration cases): research filename date differing from creation day kept without drift, unknown creation stays unknown, age and grandfathering identical before and after (E-09, E-14); the new-record-at-23:30 case is a creation-path test owned by `tve77h`.
- AC-20: fixture census (E-14) and the clone census (E-15).
- AC-22 case 1 (E-04).
- AC-27 cases 1 to 4 (E-04).
- AC-28 cases 1 to 4 (E-03).
- AC-29 case 1 (E-10).
- AC-30 cases 1 and 2 (target-repo half) on fixture and clone (E-06, E-15).
- AC-32 cases 1 to 3 and 5 on fixtures (E-09); case 4 needs a post-cutover setter: `cxxmyv`.
- AC-40 cases 1 and 2 (E-10).
- AC-41 cases 1, 2, 3, 5 and the byte-for-byte half of case 4 (E-07, E-08, E-13, E-15).

CONTRIBUTES to: AC-16 case 1 (marker acceptance by both hooks and the sanitizer on the clone commit; `aw attention --check --agent` on the migrated tree is `cxxmyv`'s), AC-22 case 2, AC-29 case 2, AC-30 case 3, AC-34 case 5 (checkpoint at old path then `rename`), AC-36 case 6 (census counts with and without description), AC-13 (clone wall time as an input).

## Spec / documentation sync

No spec change; implements `4sd62s` sections 5.1 and 5.2 (steps 0 to 7 on a copy), 4.1 (by-name record decisions), 4.1a K4 to K6, 4.2a and OQ-12, OQ-26, OQ-27, OQ-28. User documentation for `aw migrate metadata` is written for the post-cutover state by Order 12 (`90iqr1`) and lands in the cutover commit (C10a); this plan adds only the CHANGELOG line and `--help` text.

## Open questions

### OQ-01: Does this plan fit one pass, or should it be split?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: It fits the limits: 16 E-items in 5 task groups (limits 18 and 5). It is dense, so if review finds it too large, split at the task-group boundary: `04a` = task groups 1 and 2 plus the E-14 tests for them (chain, stamp, `aw migrate`, install prompt and `--migrate`, preflight and force flags, journal, sidecar import; AC-11, AC-22 case 1, AC-27, AC-28, AC-30 case 1), and `04b` = task groups 3 to 5 (renames, citations, conversion, file rewrite, marker, cleanup, census, round trip, clone proof; AC-10, AC-14, AC-14a(5), AC-19, AC-20, AC-29(1), AC-32, AC-40(1,2), AC-41), with `04b` depending on `executed:04a` and Order 05 depending on `04b`. Recommendation strength: medium (keep one plan).

### OQ-02: How are roadmaps, prompt-library files, research templates, reference packages and READMEs handled (spec 4.1 "the plan must also decide, by name")?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Decided from the evidence in F-15, as 4.1 delegates it to the plan. `roadmaps/` (`7ny1bg`): a status-less logged record like a walkthrough (one-key front matter, log with no `transition`, its 1 sidecar record imported), because it has an `id6` and sidecar history that 5.2 step 2 must not lose, and N2 forbids adding a status vocabulary; its bold-prose header stays body prose. `tve77h` E-01's registry has seven types (`ipd`, `spec`, `backlog`, `research`, `release`, `prompt`, `walkthrough`) and no `roadmap`, so this plan adds a `roadmap` registry entry with the walkthrough field set (E-09); if `tve77h` adds one first, E-09 uses it and records that no edit was needed. `prompt-library/` (4 files) and the 2 research templates (`conformance-results-template.md` and `plan-review/20260712-0156-14-chatgpt-modular-report-template.md`): excluded and byte-identical, listed by name in the census, because they are reusable text with no lifecycle, and 4.6 explicitly places "any template the plan leaves unrenamed" outside the filename check; the legacy-named template therefore stays the one remaining `_LEGACY_TIMESTAMP_RE` match and the AC-41(3) check excludes it by name. `research/reference/` (74 files): ordinary research records, migrated like research. READMEs (including `research/20260726-0054-.../README.md`): not records, excluded. Comms and `.data/` files: unchanged (OQ-2 of the spec).

### OQ-03: How can `metadata_schema` and the AC-11 refusal ship in phase A without refusing this unmigrated repository?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `require_current_schema` is called from `artifact_meta`'s read-path refresh (E-01), and compares against `CURRENT_METADATA_SCHEMA`, which is 1 (the legacy format, the only format phase-A code reads) and an absent stamp counts as 1. So nothing refuses before the cutover, and install stamps a legacy-free new repository with 1, which is true. Order 13 sets the constant to 2 in the cutover commit, which makes every legacy repository refuse and every new install stamp 2, exactly AC-11. Tests patch the constant to 2 to prove the behavior now. This keeps C10a (one format per commit) and avoids a stamp that lies.

### OQ-04: Are the 3 non-leading `aw-prompt` comments in research files metadata or body prose (4.2c row)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Body prose, unchanged. In `8it88r`, `yq6aub` and `9bd3j8` the comment sits at lines 14 to 15, below the record's YAML front matter, and repeats the header of the prompt the research record quotes; the record's own metadata is its YAML. Moving it to the log would invent metadata for a different artifact. The census lists the 3 files under this disposition.

### OQ-05: Does the migration infer `inferred-from-git` ordering?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. 5.2 step 4 says the migration "can" add it; running `git log -p` per record over 2,959 history-bearing files would dominate the migration time for an order that 4.2a says carries no replay meaning. Every imported event records its original file position and `ordering_confidence: unknown`, which is the honest value.

### OQ-06: Does `aw migrate-layout` become `aw migrate layout` (5.1, research `ffi66q`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, as an added spelling. `aw migrate layout` dispatches to the existing `cli._run_migrate_layout`; `aw migrate-layout` stays as an alias with unchanged output, because README and help text name it and removing a shipped verb is a separate breaking decision. This gives one `aw migrate <name>` family for migrations, which is what 5.1 asks. Research `ffi66q` is still `status: todo` and names no conflicting spelling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_migrations_chain.py -k "stamp or schema"` with every selected test PASSED, including a test asserting the resolved `project.json` gains `"metadata_schema": 2` with `schema_version` unchanged and a test asserting the exact refusal text "run `aw migrate metadata`" under a patched `CURRENT_METADATA_SCHEMA = 2`; the `git diff` hunks adding `metadata_schema` in `project_schema.py` and `install_wizard.py`; the PASSED test showing `aw install` into a stamped repository keeps `"metadata_schema": 2`; and the PASSED test showing `artifact_meta.read` on a legacy fixture with the constant monkeypatched to 2 raises naming `aw migrate metadata`.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: paste `aw migrate --help` output listing `metadata` and `layout`; `diff <(aw migrate layout status) <(aw migrate-layout status)` printing nothing; and `python3 -m pytest -o addopts="" tests/test_command_surface_declarations.py tests/test_completion.py` summary line with 0 failed.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_install_migrate_prompt.py` with each AC-28 case (terminal no, terminal yes, no terminal, `--yes`, `install all --yes`, `--migrate` with a step-1 condition true) and AC-11 cases 2 and 3 PASSED, each asserting record bytes by SHA-256 before and after.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_preflight.py -k "preflight or worktree or sidecar_missing"` with one PASSED test per AC-27 case 1 (three conditions, refused and then forced, output naming the overridden condition), 2, 3, 4 and AC-22 case 1; each refusal test asserts a byte-identical tree.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_preflight.py -k "journal or resume or rollback"` all PASSED; and `ls -R` of the journal directory after one fixture dry run, showing files only under the gitignored `state/durable/migrations/m0001/` path.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_conversion.py -k sidecar` all PASSED (status record, repeated inline line kept twice with distinct `source`, rename record kept as `legacy`, orphan `id6` in the export with no log, target `.aw/.gitignore` without the `records/history.jsonl` line); and the E-15 clone's preflight line naming the sidecar record count.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: paste the E-15 clone dry-run rename-map section, with its row count beside the clone's re-derived legacy-timestamp count minus the OQ-02 exclusions (34, 28 minted and 6 preserved at authoring), including the exact `wvlk84` row `20260817-awphysical-17-wvlk84-assess-bugs-leftover-remove-dataloss.ipd.md` and the three `plans-adopter` rows with orders 00, 06, 07; and `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py -k "classify or order or collision"` all PASSED.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: paste the E-15 clone dry-run citation section: hits per location, `0 ambiguity warnings`, and the left-unchanged list with reasons; and `python3 -m pytest -o addopts="" -v tests/test_m0001_renames.py -k citation` all PASSED, including the test that a `## Workflow history` line citing an old name is not edited.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_conversion.py -k "layout or path_history or clock"` all PASSED, and the six JSON lines (seq 0 to 5) of the AC-32 fixture log printed by the test on failure or by a `python3 -c` dump, showing `op` checkpoint, legacy, legacy, legacy, review, review and `append` 0 on each.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_conversion.py -k "mirror or prompt or walkthrough or review_file or excluded"` all PASSED; and `head -3` of one migrated staged prompt, one walkthrough and one review file from the E-15 clone.
  - Observed evidence:
  - Result: pending
- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_gate_marker.py` all PASSED (refused without marker, accepted with matching tree id, refused after one extra staged edit, refused after the marker is consumed, for each of the two hooks); and the `git diff` hunks of both hook files.
  - Observed evidence:
  - Result: pending
- [ ] V-12 validates E-12
  - Required evidence: paste the census section of the E-15 clone dry run in full: field rows with destinations and counts, zero `unknown-field` refusals, the excluded templates by name, the orphan sidecar `id6` lines, and the with/without description counts; and the refusal text of the E-15 step (b) `--apply`.
  - Observed evidence:
  - Result: pending
- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_roundtrip.py` all PASSED, naming the long-line (over 4,300 characters), control-character, writer-refusal, sanitizer-refusal and second-apply-no-change tests.
  - Observed evidence:
  - Result: pending
- [ ] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -n auto tests/test_migrations_chain.py tests/test_install_migrate_prompt.py tests/test_m0001_preflight.py tests/test_m0001_renames.py tests/test_m0001_conversion.py tests/test_m0001_roundtrip.py tests/test_m0001_gate_marker.py --durations=10` summary with 0 failed and the durations table, naming any module marked `slow`; and the bare `python3 -m pytest` summary line inside the 30 s budget.
  - Observed evidence:
  - Result: pending
- [ ] V-15 validates E-15
  - Required evidence: paste the `git clone` command line (target `tmp/dcerjg-clone`) and whether the real or a synthetic sidecar was used; then, from the clone: the dry-run output (preflight, rename map count, citation totals, census summary, `round trip: pass`), the step (b) refusal, the step (d) `aw commit --no-plan` output with both hooks passing, the step (e) `nothing to do` line, and step (f) `git status --porcelain --ignored | grep -E 'history.jsonl|STATUS.md|INDEX'` printing nothing; the wall time; and `git status --porcelain | sha256sum` of THIS checkout before and after, equal.
  - Observed evidence:
  - Result: pending
- [ ] V-16 validates E-16
  - Required evidence: paste the `CHANGELOG.md` diff hunk; the summary lines of the named-module run, bare `python3 -m pytest` and `make test-all`; the `(location, rule)` pairs of `aw check --agent` after E-16 compared with `.aw/state/dcerjg/check-before.jsonl`, with no added error or warning pair; and every `aw commit dcerjg` output with its `git show --stat`, listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan NEVER runs `aw migrate metadata --apply` in this checkout. Every apply is on a `tmp_path` fixture or on the E-15 clone under `tmp/dcerjg-clone`, and E-15's evidence includes `git status --porcelain` of this checkout before and after. If an apply would touch this checkout's records, stop and report: that is a genuinely unsafe condition, not a scope question.

Honesty rule: run the named test modules, the bare core gate `python3 -m pytest` and `make test-all`, and paste the ACTUAL summary lines; never claim a result you did not run. E-15 step (c) uses a fake describer and proves only the seam.

Commits: commit only through `aw commit dcerjg -- <paths>` (the E-15 clone commit uses `aw commit --no-plan` INSIDE the clone); never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize dcerjg` itself.
