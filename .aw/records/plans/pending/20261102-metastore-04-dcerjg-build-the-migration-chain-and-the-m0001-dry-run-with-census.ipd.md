# IPD: Build the migration chain and the m0001 dry run with census, renames, citations and round trip

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` makes the cutover one scripted migration (`4sd62s` 5.1, 5.2, 5.2a). After the 2026-11-07 and 2026-11-09 splits, the chain, stamp, preflight, journal, sidecar, CLI, renames, conversion, and terminal commit marker are built by parts `g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, and `o19353`. What no part can prove alone is the END-TO-END result: the step-6 field census over every type, the round-trip verifier, the step-6 `metadata_schema: 2` stamp write and step-7 commit wiring in `m0001_metadata_v2.run`, the full 10-module `m0001` test suite, and one complete dry run, apply, commit, and second apply on a COPY of this repository (`4sd62s` section 7 phase A step 3), which must succeed before Order 13 (`cxxmyv`) runs the one irreversible commit. Measured at authoring: 35 tracked legacy-timestamp records outside comms, 2,035 citation hits in 457 files over the widened roots (F-05), and 70 distinct bullet names before the first `##` (F-07); re-measured at review `HEAD` `0ea2db75d` in F-18.
- Scope: Integration and finishing part of the `m0001` build, after its parts (`g8na48` chain, `metadata_schema` stamp, read-path hook, and `aw check` baseline; `vxevph` preflight, journal, and sidecar; `1vfqdu` CLI group, bare `aw migrate`, and install prompt; `dky26u` renames and citations; `ghhzb6` and `hpedmn` conversion; `o19353` terminal marker and cleanup): the step-6 field census (E-12), the round-trip verifier plus step-6 stamp, idempotency guard, and step-7 commit wiring in `m0001_metadata_v2.run` (E-13), `tests/test_m0001_roundtrip.py` plus the end-of-family run of all ten `m0001` test modules (E-14), the proof on a disposable clone of this repository with installed commit hooks (E-15), and the `CHANGELOG.md` line and validation gates (E-16). Everything runs ONLY on `tmp_path` test fixtures and on a disposable clone; this plan never migrates this checkout. EXCLUDES: every item moved to the parts above (see Deferred); multi-repository layout/shape discovery, id-less record conversion, and five-shape corpus parity (`4sd62s` C12, 5.2a, AC-42: `9vf2iv`, `6oi2nu`, `3g20ms`, `bv4kkj`, `g5hpbb`); the description journal and model generation (Order 05: `odeo9z`, `830wku`, `ya4ee4`); explicit `--include-paths` commit staging (`clors0` E-19); switching the toolkit's loader and writer to logs, moving the legacy loader into `m0001`, the real cutover run, and flipping `CURRENT_METADATA_SCHEMA` to 2 (Order 13, `cxxmyv`); removing the sidecar writer and the `history.jsonl` lines from `engine.py` and `placement_switch.py` (Order 13, `cxxmyv`); deleting INDEX/STATUS code (Order 11, `9o83cr`); and `aw check meta` (Order 08, `ffceq0`).
- Scope-Paths: agent_workflows/migrations/m0001_verify.py, agent_workflows/migrations/m0001_metadata_v2.py, tests/test_m0001_roundtrip.py, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md
- Item-Dependencies: executed:tve77h, executed:g8na48, executed:vxevph, executed:1vfqdu, executed:dky26u, executed:ghhzb6, executed:hpedmn, executed:o19353
- Status: approved
- Readiness: go-pending-approval
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 4
- Highest E allocated: 16
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: dcerjg
- Approval: 2026-11-16, recorded via aw ipd set: status set to approved
- Review-Depth: complex

> Written to `.aw/system/workflows/technical-writing/technical-writing.md`. Every obligation, exact identifier, quotation, evidence record, and lifecycle status is preserved.

## Workflow history
- 2026-11-16 approved (aw set): status set to approved
- 2026-11-14 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-010..PR-015 FIXED
- 2026-11-14 /plan-review (antigravity/gemini): APPROVE WITH REVISIONS APPLIED; PR-010..PR-015 FIXED; review record .aw/records/reviews/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.review.md
- 2026-11-09 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): round-3 split per research nj8zdp; items E-11 (and the gate-marker module of E-14) moved to o19353.
- 2026-11-07 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): split per maintainer step-complexity rule; items E-01, E-04, E-05, E-06 moved to vxevph; E-02, E-03 moved to 1vfqdu (with the new bare `aw migrate` item); E-07, E-08 moved to dky26u; E-09, E-10 split by record type across ghhzb6 and hpedmn; E-11 kept; E-14's test modules split across the parts.
- 2026-11-07 to-review (aw set): demoted approved -> to-review: APPROVAL WITHDRAWN: maintainer direction 2026-11-07: paused before re-review; the metastore plans MUST build the tools that migrate ANY repo from ANY prior format (.agents layout, id-less/untitled records, no sidecar), not only this repository. Re-review against the amended spec 4sd62s before re-approval.
- 2026-11-07 approved (aw set): status set to approved
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-009 FIXED; review record .aw/records/reviews/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

After its parts have built each step, finish the one-time `aw migrate metadata` cutover code with the field census and the round-trip verifier, and prove the whole of it on a disposable clone, so that Order 13 runs code that has already produced a complete, verified, idempotent migration of a full copy of this repository.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Items E-01 to E-11 were moved to the parts named in `## Deferred / out of scope (with reason)` (`g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, and `o19353`); their ids are not reused.

### Task group 5: census, round trip, real-copy proof and commit

- [x] E-12 Create `agent_workflows/migrations/m0001_verify.py` with the step-6 field census (`4sd62s` AC-20, 5.2 step 6, 5.2a items 1, 3, 5): resolve `records_root` from the caller's argument or `project_context.project_records_dir(repo)` with zero repository-specific `id6` or count constants, and enumerate every distinct field name found before the first `##` heading, in research YAML, in leading `aw-prompt` comments, and as D177 filename facets, each with its destination (log field, body section, review-event field, or a recorded drop with reason) and its count; `unknown-field` and unparseable-value refusals (for example an `Item-Dependencies` value outside the closed grammar); `plan_role` legacy values and absent-`Kind` counts; staged prompts with no comment; sidecar orphan `id6` values with counts (or `"no sidecar (none expected)"` with zero orphans when `vxevph` E-04 reports `not sidecar_expected`); the present excluded templates and non-leading research `aw-prompt` comments by relative path (skipping absent template paths cleanly on non-self repositories); the count of records with and without a `short_description`; and the rename and citation summaries. `--apply` refuses when the census has any refusal or when any record lacks a `short_description` that the census does not list as a deliberate absence (walkthroughs and roadmaps carry `short_description` in `4sd62s` 4.5c; excluded templates, READMEs, comms, and `.data/` files are non-records).
  - Depends on: none
  - Expected outcome: the census on the clone lists every field the corpus uses (70 bullet names measured at authoring plus YAML, comment, and facet keys) with zero `unknown-field` refusals, handles both sidecar-present and `"no sidecar (none expected)"` repositories without hard-coded counts, and reports a nonzero "without description" count that makes `--apply` refuse when no `describer` ran.
  - Execution state: performed

- [x] E-13 Add the round-trip verifier (`4sd62s` AC-10) in `m0001_verify.py` and wire step 6, the top-of-`run` idempotency guard, the `metadata_schema: 2` stamp write, and step 7 into `agent_workflows/migrations/m0001_metadata_v2.py`:
  - At the very top of `m0001_metadata_v2.run(repo, *, apply=False, force=False, force_worktree=False, describer=None, fault_injection=None, commit=True)` (before step-1 preflight, step-2 sidecar check, or journal directory creation), check `chain.read_metadata_schema(repo)`: when `>= 2`, return a no-op report printing `"metadata_schema is 2; nothing to do"` with zero writes.
  - In `m0001_verify.py` (invoked on every dry run and on `apply=True` before working-tree mutation), replay each produced `meta/<id6>.jsonl` log directly through `artifact_meta.replay(id6, art_type, lines, records_root=scratch_records_root)` (avoiding Phase-B `check_freshness`'s legacy `.md`/`.review.md` loader scan; if `hpedmn` E-01 added `"roadmap"` only to `artifact_meta.REGISTRY` and omitted `artifact_meta.SUPPORTED_TYPES`, add `"roadmap"` to `SUPPORTED_TYPES` as well and justify `agent_workflows/artifact_meta.py` via `--scope-reason` at finalize), parse each rewritten mirror through `artifact_meta.parse_artifact_mirror`, `parse_staged_prompt_mirror`, or `parse_review_mirror`, and assert that every legacy field value (under its 4.2/4.5c name, or verbatim in the body or `scope_exceeded_raw`), every raw inline history line, every resolvable sidecar JSON object, and every migrated review round is recoverable byte for byte; that no two plans share a `(set_id, order)`; and that no artifact, walkthrough, or roadmap filename matches `artifact_naming._LEGACY_TIMESTAMP_RE` (excluding the OQ-02 templates by relative path when present). Run `leak_sanitizer.scan_text` with `leak_sanitizer.build_ruleset(repo_root)` over every new log and mirror, refusing `--apply` on any `fail` diagnostic (`4sd62s` 5.2 step 6, AC-16); `warn` findings are listed in the report without refusing because imported legacy bytes use `migration_import=True` (`tve77h` E-03 (d)).
  - On `apply=True`, after step 6 passes, back up the resolved `project.json` (or an absence marker) in `journal_dir / "backups"` so `rollback(repo)` restores pre-apply `project.json`, call `chain.write_metadata_schema(repo, 2)` (`4sd62s` 5.2 step 6), include the resolved `project.json` path in the migration's explicit path list whenever it sits inside `repo`, stage that complete path list, and write `o19353` E-01's step-4a `terminal_commit_marker` (`git write-tree` of the staged index, which now covers `project.json`). When `commit=True` (the default used by `aw migrate metadata --apply` and bare `aw migrate --apply`), execute `4sd62s` 5.2 step 7 via `git_commit_helper.offer_commit(..., assume_yes=True, runner=git_commit_helper.RUNNER_AW_COMMIT)` (no `--no-verify`) and delete `terminal_commit_marker` on commit success (and in `rollback(repo)`); when `commit=False`, return `staged_paths` with the index and marker intact so a caller or test can inspect the staged tree and complete step 7 via a helper `commit_staged(repo, paths)` that runs the same `offer_commit` / `aw commit --no-plan` path and deletes `terminal_commit_marker`.
  - Depends on: E-12
  - Expected outcome: a fixture holding a history line longer than `MAX_PROSE_DESCRIPTIVE_LEN` (4,300) and one with a control character round-trips both byte for byte, while the same long value given to `artifact_meta`'s writer validation is refused; a fixture with a planted home-directory path in a field value makes `--apply` refuse on the sanitizer; `apply=True` writes `"metadata_schema": 2`, commits cleanly in step 7, and consumes `terminal_commit_marker`; and a second `--apply` on a stamped repository reports `"metadata_schema is 2; nothing to do"` and changes no file.
  - Execution state: performed

- [x] E-14 Add `tests/test_m0001_roundtrip.py` (`4sd62s` AC-10 fixture cases, AC-20 fixture census including `"no sidecar (none expected)"`, step-6 stamp + step-7 commit + `rollback` restoration of `project.json`, and second-apply idempotence) on `tmp_path` fixture repositories built with real `git init`, including an end-to-end `apply=True` (`commit=True`) fixture holding an executed legacy-timestamp plan, a release-blocking `done` backlog item, and an installed executable `.git/hooks/pre-commit` script invoking `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows backlog-blocking-close-gate` (exercising `commit_lock.commit_isolated`'s detached `.aw-isocommit-*` worktree; if `o19353` E-01's hook marker lookup read only worktree-local `state_durable` instead of falling back to `ipd_lifecycle.checkout_control_root(root) / "state" / "durable"`, fix both hook modules and justify them via `--scope-reason` at finalize), calling the real functions and CLI leaves and asserting on outputs, exit codes, commit history, and file bytes (zero source inspection). Then RUN, once, as the family gate, all ten `m0001` test modules listed under `## Required tests / validation` ("New module here" plus "Run as the family gate"): this module plus the nine written by `g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, and `o19353`. Mark the new module `core`; any module whose slowest test exceeds 2 s in `--durations=10` is marked `slow` instead and named in V-14.
  - Depends on: E-12, E-13
  - Expected outcome: all ten modules pass under `python3 -m pytest -o addopts="" -n auto <modules>`, including the real `.git/hooks/pre-commit` `commit_isolated` case, and the bare core gate stays inside its 30 s budget.
  - Execution state: performed

- [x] E-15 Prove the migration on a COPY of this repository, never on this checkout: commit the E-12 to E-14 code first (every earlier step is already committed by the executed parts; E-16's commit obligation splits cleanly into code before E-15 and `CHANGELOG.md` plus plan/evidence updates after E-15), then run `git clone --no-hardlinks . tmp/dcerjg-clone` (inside the gitignored `tmp/` of this checkout so a runner lane stays inside its workspace), install an executable `tmp/dcerjg-clone/.git/hooks/pre-commit` script (`#!/usr/bin/env sh`, `set -eu`) running `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows backlog-blocking-close-gate` (`git clone` installs only `.sample` hooks and `backlog-blocking-close-gate` is opt-in), copy `.aw/records/history.jsonl` into `tmp/dcerjg-clone/.aw/records/history.jsonl` when this checkout has one (a runner lane has none: record that, write a synthetic sidecar containing at least one resolvable tracked `id6` record and one orphan `id6` record, and leave the real-sidecar line to `cxxmyv` E-02, which owns AC-22 case 2), and in a subshell `(cd tmp/dcerjg-clone && ...)` using the clone's own package (`python3 -m agent_workflows ...`, resolved to the clone by `checkout_pin`) run: (a) `aw migrate metadata` (dry run), (b) `aw migrate metadata --apply` (must refuse on missing descriptions), (c) a short `python3 -c` driver calling `m0001_metadata_v2.run(copy, apply=True, describer=<fixed-text fake>, commit=False)` followed by `aw sanitize --agent` on the staged clone tree, (d) `python3 -m agent_workflows ipd-executed-gate` and `python3 -m agent_workflows backlog-blocking-close-gate` directly against the staged index and then the step-7 commit via `m0001_metadata_v2.commit_staged` / `aw commit --no-plan` with the migration's explicit path list (which also runs the installed `.git/hooks/pre-commit` inside `commit_lock.commit_isolated` and deletes `terminal_commit_marker`; verify the marker file is absent afterwards), (e) `aw migrate metadata --apply` again (printing `"metadata_schema is 2; nothing to do"`), and (f) `git status --porcelain --ignored` in the clone. Step (c) exercises the `describer` seam with a fixed-text fake and is NOT evidence about real descriptions. Record wall time and peak scratch size, then delete `tmp/dcerjg-clone`. Before and after, `git status --porcelain` of THIS checkout must be identical.
  - Depends on: E-14
  - Expected outcome: (a) prints the preflight (sidecar presence and record count, real or synthetic as recorded), the rename map (every `_LEGACY_TIMESTAMP_RE` artifact, walkthrough, and roadmap in the clone mapped except the OQ-02 template; 34 entries measured at `HEAD` `0ea2db75d`), per-location citation counts with `0 ambiguity warnings`, the census, and `round trip: pass`; (b) refuses naming the missing descriptions; (c) stages the migrated tree plus `"metadata_schema": 2` and passes `aw sanitize --agent` with zero `fail`; (d) passes both gate CLIs directly and via `.git/hooks/pre-commit` inside `aw commit --no-plan` and consumes `terminal_commit_marker`; (e) prints `"metadata_schema is 2; nothing to do"` and changes nothing; (f) shows a clean clone with no `records/history.jsonl`, no `STATUS.md`, and no `INDEX` file.
  - Execution state: performed

- [x] E-16 Add one `CHANGELOG.md` entry under `2.0.0 (pending)` (new `aw migrate metadata` dry-run command and `aw migrate layout` spelling; `aw install --migrate`; the migration does not yet run on any repository), with no em or en dashes. Run the ten named `m0001` modules, the existing regression modules in `## Required tests / validation`, the bare core gate `python3 -m pytest`, `make test-all`, `aw sanitize --agent`, and `aw check --agent`; when `.aw/state/dcerjg/check-before.jsonl` is absent because `dcerjg` executes in an isolated runner worktree separate from `g8na48`, regenerate `.aw/state/dcerjg/check-before.jsonl` first from a temporary detached worktree under `tmp/` checked out at the pre-edit `HEAD` SHA recorded in `g8na48` `F-03` (or at `dcerjg`'s own pre-edit `HEAD` if `g8na48` `F-03` was recorded on a prior branch) and remove that temporary worktree immediately. Commit through `aw commit dcerjg -- <each changed path>` (code before E-15, then `CHANGELOG.md`, any E-15 fixes, and this plan's progress updates after E-15). Never push.
  - Depends on: E-14, E-15
  - Expected outcome: every test run and `aw sanitize --agent` pass; `aw check --agent` reports zero added `(location, rule)` error or warning pairs against `.aw/state/dcerjg/check-before.jsonl`; each path-scoped commit's `git show --stat` lists only `- Scope-Paths:` files (or paths explicitly justified at finalize via `--scope-reason`).
  - Execution state: performed

## Project conventions discovered (Step 0)

- Transactional migrations reuse `layout_migration.MigrationManager` (`_acquire_lock`, `_release_lock`, `_save_transaction`, `_load_transaction`); `4sd62s` 5.1 forbids new journal or lock components. Its shared journal path (`state/runtime/transactions/migration_transaction.json`) belongs to the layout migration, so `m0001` uses `state/durable/migrations/m0001/journal.json` (`vxevph` E-03).
- Path roots come from `project_context`: `project_context.project_records_dir(repo)` for `records_root` (honoring companion/home backends while resolving `<repo>/.aw/records` on unconfigured `tmp_path` repositories), `project_context.project_config_dir(repo) / "project.json"` for `metadata_schema` (`g8na48` E-01), and `resolve_project_context(target_repo=str(repo)).physical_classes["state_durable"]` (with `ipd_lifecycle.checkout_control_root` collapse across `commit_lock.commit_isolated`'s detached `.aw-isocommit-*` linked worktree) for durable state (`4sd62s` 4.5, 5.1, 5.2a).
- The integration lock is `runner_shared.integration_lock_path` and `runner_shared.integration_lock` (bounded, loud wait); a non-mutating probe is `platform_lock.probe_free`. Worktree identity is `ipd_lifecycle.checkout_git_common_dir`. Lane landing is `runner_shared.lane_work_has_landed` (`True`/`False`/`None`, with `None` kept visible as `"unknown"`).
- Naming authority is `artifact_naming` (`_LEGACY_TIMESTAMP_RE`, `parse_clustered`); citations go through `artifact_refs.plan_reference_rewrites_with_warnings`, whose `scan_roots` is a parameter; ids are minted by `artifact_core.mint_id6` (repository-wide collision check).
- Every CLI leaf must be declared in `command_surface` (`command_surface.find_undeclared_leaves`, enforced by `tests/test_command_surface_declarations.py`); `migrate-layout`'s declaration is the template for a mutation verb with a confirmation gate.
- Descriptive-value safety is `attention_contract.refuse_unsafe_descriptive` with `MAX_DESCRIPTIVE_LEN` 300 and `MAX_PROSE_DESCRIPTIVE_LEN` 4,300; leak scanning is `leak_sanitizer.scan_text` with `leak_sanitizer.build_ruleset`.
- Cite code by symbol (`module.function`) or by a quoted content string rather than by a bare line number alone (`IPD-C801`).
- Tests exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); a real model or network call from a test is refused by construction, as `runner_shared._assert_probe_spawn_is_permitted` does for the coverage probe.

## Findings

Values F-01 to F-16 were measured at authoring; F-17 was re-measured in Round 1 (`HEAD` `4f09df0c7`) and F-18 in Round 2 (`HEAD` `0ea2db75d`).

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
| F-09 | Staged prompts: 30 `.md` under `.aw/records/prompts` (README excluded), 25 with a leading `<!-- aw-prompt:` comment; 3 research files embed a `<!-- aw-prompt:` comment below YAML (`8it88r`, `yq6aub`, `9bd3j8`) | 5 prompts take status from disposition; OQ-04 decides the 3 research comments. |
| F-10 | `project_schema.parse_portable_policy` `known_keys` lacks `metadata_schema`; other keys land in `unknown_fields` | The stamp must be added as a known key. |
| F-11 | `hooks/executed_transition_gate._staged_plan_executed_transitions` flags a plan "ARRIVING in an `executed/` directory ... not ALREADY there at HEAD under the SAME `- Id:`"; `hooks/backlog_blocking_close_gate.check` delegates to `check_engine.check_release_gate_consistency` | The 5 renamed executed plans and every rewritten terminal file need the positive marker (5.2 step 4a). |
| F-12 | `cli` `install` `-y/--yes` help "Skip preflight confirmations."; `setup` `-y/--yes` "Install without per-repo prompts." | Neither may answer the migration question (5.1). |
| F-13 | `artifact_rename.compute_target_name` builds the `--to-id6` name with `set_id=mint_id6, order=1` (called from `artifact_rename.run_rename_generic`) | It cannot be reused for the OQ-26 rule. |
| F-14 | `.aw/.gitignore` line `records/history.jsonl`; INDEX lines for plans, research, prompts; tracked `.aw/records/plans/STATUS.md`; `engine.py` template and adder and `placement_switch.py` list also name `records/history.jsonl` | Target-repo lines are step 2/5 output; the source-code lines are Order 13's. |
| F-15 | `.aw/records/roadmaps/` holds 1 record (`7ny1bg`, bold-prose metadata, 1 sidecar record); `prompt-library/` 4 `.prompt.md` with no id; research templates `conformance-results-template.md` and the F-02 template; `research/reference/` 74 files with clustered names | Inputs to the by-name decisions of OQ-02. |
| F-16 | `opencode` 1.18.35 and `agy` on PATH; clone size: `.git` 240 MB, 6,211 tracked files | A `--no-hardlinks` clone for E-15 is feasible under `tmp/`. |
| F-17 | Re-measured at Round 1 review (`HEAD` `4f09df0c7`): 35 tracked legacy-timestamp files outside comms (unchanged); 4,470 tracked `.md` under `.aw/records`, 2,898 with `## Workflow history`, 1,300 tracked review files; `install_wizard` rebuilds `project.json` from `ProjectPolicySchema` named fields plus `unknown_fields`, with a fallback `known_proj_keys` copy of the key set; `tve77h` E-01 registers seven types and no `roadmap`; this review lane has no `.aw/records/history.jsonl` | Counts drift (context only); the stamp needs a round-trip field (PR-001); a lane-run E-15 needs a synthetic sidecar (PR-004). |
| F-18 | Re-measured at Round 2 review (`HEAD` `0ea2db75d`): 35 tracked legacy-timestamp files outside comms (unchanged), 4,719 tracked `.md` under `.aw/records`, 1,330 `.review.md` files; `artifact_meta.SUPPORTED_TYPES` (`artifact_meta.py`, checked in `replay`, `_load_sources`, and `read`) is a separate 7-tuple from `REGISTRY`; `git clone --no-hardlinks` installs only `.git/hooks/*.sample` and `backlog-blocking-close-gate` is absent from `.pre-commit-config.yaml`; `aw commit` (`commit_lock.commit_isolated`) runs `.git/hooks/pre-commit` inside a detached `.aw-isocommit-*` linked worktree where worktree-local `.aw/state/durable` is absent (`ipd_lifecycle.checkout_control_root` collapses back to the primary checkout's `.aw`); `g8na48` E-01/F-03 owns `.aw/state/dcerjg/check-before.jsonl` plus `HEAD=<sha>` for cross-lane regeneration | Step-6/step-7 wiring (`PR-010`), `.git/hooks/pre-commit` installation and `commit_isolated` marker lookup (`PR-011`), direct `artifact_meta.replay` plus `SUPPORTED_TYPES` check (`PR-012`), and `g8na48` dependency + cross-lane baseline regeneration (`PR-013`) are required. |

## Proposed changes (ordered, validatable)

1. E-12: create `agent_workflows/migrations/m0001_verify.py` with the repository-agnostic step-6 field census (`4sd62s` AC-20, 5.2a).
2. E-13: add the round-trip and leak-scan verifier in `m0001_verify.py`, and wire the top-of-`run` `read_metadata_schema >= 2` guard, step 6, the journal-backed `write_metadata_schema(repo, 2)` stamp write, and the step-7 `offer_commit` + marker consumption into `agent_workflows/migrations/m0001_metadata_v2.py`.
3. E-14: add `tests/test_m0001_roundtrip.py` (including a real `.git/hooks/pre-commit` `commit_isolated` fixture) and run all ten `m0001` test modules as the family gate.
4. E-15: commit code, clone into `tmp/dcerjg-clone`, install `.git/hooks/pre-commit`, and prove dry run, refusal, apply, hook-verified step-7 commit, second-apply no-op, and clean status on the clone.
5. E-16: add the `CHANGELOG.md` entry, run the module, core, thorough, sanitize, and `aw check --agent` baseline gates, and commit path-scoped changes via `aw commit dcerjg`.

```mermaid
flowchart TD
    RUN["m0001_metadata_v2.run(repo, apply, commit)"] --> GUARD{"read_metadata_schema(repo) >= 2?"}
    GUARD -->|"yes"| NOOP["print 'metadata_schema is 2; nothing to do' (0 writes)"]
    GUARD -->|"no"| STEPS["steps 1-5 in journal scratch (vxevph, dky26u, ghhzb6, hpedmn, o19353)"]
    STEPS --> VERIFY["step 6: m0001_verify census + artifact_meta.replay round trip + leak_sanitizer.scan_text"]
    VERIFY -->|"apply=False"| REPORT["return dry-run report (scratch only)"]
    VERIFY -->|"refusal / missing description / leak fail"| REFUSE["refuse --apply (working tree untouched)"]
    VERIFY -->|"apply=True & clean"| STAMP["apply journaled writes + backup project.json + write_metadata_schema(repo, 2)"]
    STAMP --> MARK["stage explicit path list (incl. project.json) + write terminal_commit_marker (git write-tree)"]
    MARK -->|"commit=True"| COMMIT["step 7: offer_commit (commit_isolated + pre-commit hooks) -> delete marker"]
    MARK -->|"commit=False"| STAGED["return staged_paths -> caller inspects & calls commit_staged -> delete marker"]
```

Every earlier `m0001` step is built by the parts in `- Item-Dependencies:`, which this plan waits for.

## Deferred / out of scope (with reason)

- E-01 chain half (`migrations/__init__.py`, `chain.py`, `metadata_schema` stamp in `project_schema.py` and `install_wizard.py`, `artifact_meta._require_schema`, `aw check` baseline capture in `F-03`) and `tests/test_migrations_chain.py`: Moved to `g8na48` (round-3 split 2026-11-09 from `vxevph` per research `nj8zdp`).
  - Carrier: g8na48
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-101-g8na48-build-the-migration-chain-the-metadata-schema-stamp-and-the.ipd.md
- E-04 (step-1 preflight), E-05 (migration journal), E-06 (step-2 sidecar import), and their tests from E-14 (`tests/test_m0001_preflight.py`, `tests/test_m0001_sidecar.py`): Moved to `vxevph` (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: vxevph
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-15-vxevph-build-the-migration-chain-metadata-schema-stamp-m0001-prefli.ipd.md
- E-02 (`aw migrate` group with `metadata` and `layout`), E-03 (install pending-migration prompt and `--migrate`), bare `aw migrate`, and their tests from E-14 (`tests/test_install_migrate_prompt.py`, `tests/test_migrate_cli.py`): Moved to `1vfqdu` (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: 1vfqdu
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-16-1vfqdu-add-the-aw-migrate-command-group-bare-aw-migrate-and-the-ins.ipd.md
- E-07 (rename map), E-08 (citation rewrite), and their tests from E-14 (`tests/test_m0001_renames.py`): Moved to `dky26u` (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: dky26u
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-17-dky26u-build-the-m0001-legacy-name-rename-map-and-citation-rewrite.ipd.md
- E-09 and E-10 subset A (log builder and file rewrite for plans, backlog items, releases, specs, and staged prompts) and `tests/test_m0001_conversion.py`: Moved to `ghhzb6` (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: ghhzb6
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-18-ghhzb6-build-the-m0001-log-builder-and-convert-plans-backlog-items.ipd.md
- E-09 and E-10 subset B (`review` events, `roadmap` registry entry, and log builder and file rewrite for research records, walkthroughs, the roadmap, and review files) and `tests/test_m0001_review_conversion.py`: Moved to `hpedmn` (split 2026-11-07 per maintainer step-complexity rule).
  - Carrier: hpedmn
  - Carrier-Evidence: .aw/records/plans/executed/20261107-metastore-19-hpedmn-build-the-m0001-review-events-and-convert-research-records-w.ipd.md
- E-11 (steps 4a and 5: terminal-commit marker, STATUS/INDEX cleanup, read-only marker acceptance in both hooks) and `tests/test_m0001_gate_marker.py` from E-14: Moved to `o19353` (round-3 split 2026-11-09 per research `nj8zdp` guidance).
  - Carrier: o19353
  - Carrier-Evidence: .aw/records/plans/executed/20261109-metastore-100-o19353-build-the-m0001-terminal-commit-marker-index-cleanup-step-an.ipd.md
- Multi-repository layout/shape discovery, `.agents/` layout stage chaining, id-less/prose record conversion, and five-shape corpus parity (`4sd62s` C12, 5.2a, AC-42; split across `9vf2iv`, `6oi2nu`, `3g20ms`, `bv4kkj`, and finishing plan `g5hpbb`).
  - Carrier: g5hpbb
- The description journal, the tracked generation prompt, the tool-less model call, and the cost trial (Order 05: `odeo9z`, `830wku`, and finishing plan `ya4ee4`); this plan provides only the `describer` seam and the census and refusal accounting.
  - Carrier: ya4ee4
- Explicit `--include-paths` staging on `m0001`'s step-7 commit so the one attended cutover commit can carry code, test, and documentation patches alongside migrated records (`cxxmyv` E-17 mechanism half).
  - Carrier: clors0
- Switching `artifact_meta`'s loader and writer to logs, moving the legacy loader into `migrations/m0001_metadata_v2.py`, flipping `CURRENT_METADATA_SCHEMA` to 2, running the migration on this checkout, the real preflight sidecar line (AC-22 case 2), the real census orphan lines (AC-30 case 3), and final AC-10, AC-11, AC-16, and AC-41 evidence on the real repository, including AC-41 case 4's `aw show --history` display with the current name (the phase-A toolkit cannot read a v2 copy, C9).
  - Carrier: cxxmyv
- Retiring `record_history.append`, `append_advisory`, `append_rename` and removing `records/history.jsonl` from the `engine.py` template, the `engine.py` adder, and `placement_switch.py` (AC-30 case 2, source half): done in phase A it would stop ignoring a sidecar the toolkit still writes, so a broad `git add` could commit purged records.
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

- Over-scope: none. `m0001_metadata_v2.py` is touched only to add the top-of-`run` `read_metadata_schema >= 2` idempotency guard, invoke step 6 (census, round trip, and leak scan), write the journal-backed `metadata_schema: 2` stamp before staging and `o19353`'s `git write-tree` marker, and run step 7 (`offer_commit` + marker deletion); steps 4a and 5 and the hook edits moved to `o19353`.
- Under-scope: none. Every item moved out is carried by a named part in `## Deferred / out of scope (with reason)`; multi-shape discovery and id-less conversion are carried by the `g5hpbb` family; and the cutover-only parts are carried by `clors0` and `cxxmyv`.

## Required tests / validation

New module here (`core` unless E-14's duration rule moves it to `slow`): `tests/test_m0001_roundtrip.py`. Run as the family gate (written by the parts): `tests/test_migrations_chain.py` (`g8na48`), `tests/test_m0001_preflight.py` and `tests/test_m0001_sidecar.py` (`vxevph`), `tests/test_install_migrate_prompt.py` and `tests/test_migrate_cli.py` (`1vfqdu`), `tests/test_m0001_renames.py` (`dky26u`), `tests/test_m0001_conversion.py` (`ghhzb6`), `tests/test_m0001_review_conversion.py` (`hpedmn`), and `tests/test_m0001_gate_marker.py` (`o19353`). Existing: `tests/test_command_surface_declarations.py`, `tests/test_layout_migration.py`, `tests/test_migrate_layout_cli.py`, `tests/test_plans_rename_selectors.py`, `tests/test_date_reader_clock_parity.py`. Gates: bare `python3 -m pytest`, `make test-all`, `aw sanitize --agent`, `aw check --agent`.

Acceptance criteria of spec `4sd62s` this plan OWNS (after the 2026-11-07 and 2026-11-09 splits, each fixture half is proven by the part named in parentheses, and this plan proves the clone half and pastes the final evidence; Order 13 re-demonstrates on the real repository where noted):

- AC-10: fixture round trip with the long and control-character lines plus step-6 stamp, step-7 commit, and second-apply idempotence (E-13, E-14), and clone dry run, apply, commit, second apply, and round trip (E-15). Final real-repo run: `cxxmyv`.
- AC-11: mechanism (the read-path call in `artifact_meta`) and all three cases with `CURRENT_METADATA_SCHEMA` patched to 2 (`g8na48` E-01, E-02, E-04; `1vfqdu` E-03, E-04); the shipped value flips in `cxxmyv`, which re-demonstrates.
- AC-14 (migration form): every migrated review round becomes one subject event, no review log, K4 bindings for the 24 own-`id6` files and the 4 pairs (`ghhzb6`, `hpedmn`).
- AC-14a case 5: all 4 off-vocabulary strings recovered byte for byte (`hpedmn` E-03).
- AC-19 (migration cases): research filename date differing from creation day kept without drift, unknown creation stays unknown, age and grandfathering identical before and after (`ghhzb6`, `hpedmn`); the new-record-at-23:30 case is a creation-path test owned by `tve77h`.
- AC-20: fixture census (`hpedmn` E-03, E-14 here) and the clone census (E-15).
- AC-22 case 1 (`vxevph` E-02, E-04).
- AC-27 cases 1 to 4 (`vxevph` E-02, E-05).
- AC-28 cases 1 to 4 (`1vfqdu` E-03, E-04).
- AC-29 case 1 (`hpedmn` E-02, E-03).
- AC-30 cases 1 and 2 (target-repo half) on fixture and clone (`vxevph` E-04, E-06; E-15 here).
- AC-32 cases 1 to 3 and 5 on fixtures (`ghhzb6` E-01, `hpedmn` E-01); case 4 needs a post-cutover setter: `cxxmyv`.
- AC-40 cases 1 and 2 (`ghhzb6` E-02).
- AC-41 cases 1, 2, 3, 5 and the byte-for-byte half of case 4 (`dky26u` E-01, E-02, and E-13, E-15 here).

CONTRIBUTES to: AC-16 case 1 (marker acceptance by both hooks, built and fixture-proven by `o19353` and exercised end-to-end through `.git/hooks/pre-commit` inside `commit_lock.commit_isolated` in E-14 and E-15, plus the sanitizer on the clone; `aw attention --check --agent` on the migrated tree is `cxxmyv`'s), AC-22 case 2, AC-29 case 2, AC-30 case 3, AC-34 case 5 (checkpoint at old path then `rename`), AC-36 case 6 (census counts with and without description), AC-42 (this-repository clone proof reused by `g5hpbb` E-07), and AC-13 (clone wall time as an input).

## Spec / documentation sync

No spec change; implements `4sd62s` sections 5.1, 5.2 (steps 0 to 7 on a copy), and 5.2a (items 1, 3, and 5 in `m0001_verify.py`), 4.1 (by-name record decisions), 4.1a K4 to K6, 4.2a, and OQ-12, OQ-26, OQ-27, OQ-28. User documentation for `aw migrate metadata` is written for the post-cutover state by Order 12 (`90iqr1`) and lands in the cutover commit (C10a); this plan adds only the `CHANGELOG.md` line.

## Open questions

### OQ-01: Does this plan fit one pass, or should it be split?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: It fits the limits: 16 E-items in 5 task groups (limits 18 and 5). It is dense, so if review finds it too large, split at the task-group boundary: `04a` = task groups 1 and 2 plus the E-14 tests for them (chain, stamp, `aw migrate`, install prompt and `--migrate`, preflight and force flags, journal, sidecar import; AC-11, AC-22 case 1, AC-27, AC-28, AC-30 case 1), and `04b` = task groups 3 to 5 (renames, citations, conversion, file rewrite, marker, cleanup, census, round trip, clone proof; AC-10, AC-14, AC-14a(5), AC-19, AC-20, AC-29(1), AC-32, AC-40(1,2), AC-41), with `04b` depending on `executed:04a` and Order 05 depending on `04b`. Recommendation strength: medium (keep one plan).
- Note: superseded 2026-11-07 and 2026-11-09 by the maintainer's step-complexity rule and research `nj8zdp`: the plan was split into `g8na48`, `vxevph`, `1vfqdu`, `dky26u`, `ghhzb6`, `hpedmn`, `o19353`, and this 5-item finishing part (see Deferred), finer than the two-way split proposed above.

### OQ-02: How are roadmaps, prompt-library files, research templates, reference packages and READMEs handled (spec 4.1 "the plan must also decide, by name")?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Decided from the evidence in F-15, as 4.1 delegates it to the plan. `roadmaps/` (`7ny1bg`): a status-less logged record like a walkthrough (one-key front matter, log with no `transition`, its 1 sidecar record imported), because it has an `id6` and sidecar history that 5.2 step 2 must not lose, and N2 forbids adding a status vocabulary; its bold-prose header stays body prose. Executed `tve77h`'s `artifact_meta.REGISTRY` and `artifact_meta.SUPPORTED_TYPES` list seven types (`ipd`, `spec`, `backlog`, `research`, `release`, `prompt`, `walkthrough`) and no `roadmap`, so `hpedmn` E-01 adds the `roadmap` registry entry with the walkthrough field set (and E-13 ensures `SUPPORTED_TYPES` includes `"roadmap"` as well so `artifact_meta.replay` accepts roadmap logs). `prompt-library/` (4 files) and the 2 research templates (`conformance-results-template.md` and `plan-review/20260712-0156-14-chatgpt-modular-report-template.md`): excluded and byte-identical when present, listed by relative path in the census (and skipped cleanly when absent on another repository, `4sd62s` 5.2a), because they are reusable text with no lifecycle, and 4.6 explicitly places "any template the plan leaves unrenamed" outside the filename check; the legacy-named template therefore stays the one remaining `_LEGACY_TIMESTAMP_RE` match in this repository and the AC-41(3) check excludes it by relative path. `research/reference/` (74 files): ordinary research records, migrated like research. READMEs (including `research/20260726-0054-.../README.md`): not records, excluded. Comms and `.data/` files: unchanged (OQ-2 of the spec).

### OQ-03: How can `metadata_schema` and the AC-11 refusal ship in phase A without refusing this unmigrated repository?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `require_current_schema` is called from `artifact_meta`'s read-path refresh (`g8na48` E-01, E-02), and compares against `CURRENT_METADATA_SCHEMA`, which is 1 (the legacy format, the only format phase-A code reads) and an absent stamp counts as 1. So nothing refuses before the cutover, and install stamps a legacy-free new repository with 1, which is true. Order 13 (`cxxmyv`) sets the constant to 2 in the cutover commit, which makes every legacy repository refuse and every new install stamp 2, exactly AC-11. Tests patch the constant to 2 to prove the behavior now (`g8na48` E-04, `1vfqdu` E-04). This keeps C10a (one format per commit) and avoids a stamp that lies.

### OQ-04: Are the 3 non-leading `aw-prompt` comments in research files metadata or body prose (4.2c row)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Body prose, unchanged. In `8it88r`, `yq6aub`, and `9bd3j8` the `<!-- aw-prompt:` comment sits below the record's closing YAML `---` delimiter and repeats the header of the prompt the research record quotes; the record's own metadata is its YAML. Moving it to the log would invent metadata for a different artifact. The census lists any non-leading `<!-- aw-prompt:` research comments under this disposition when present.

### OQ-05: Does the migration infer `inferred-from-git` ordering?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. 5.2 step 4 says the migration "can" add it; running `git log -p` per record over 2,959 history-bearing files would dominate the migration time for an order that 4.2a says carries no replay meaning. Every imported event records its original file position and `ordering_confidence: unknown`, which is the honest value.

### OQ-06: Does `aw migrate-layout` become `aw migrate layout` (5.1, research `ffi66q`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, as an added spelling (`1vfqdu` E-01). `aw migrate layout` dispatches to the existing `cli._run_migrate_layout`; `aw migrate-layout` stays as an alias with unchanged output, because README and help text name it and removing a shipped verb is a separate breaking decision. This gives one `aw migrate <name>` family for migrations, which is what 5.1 asks. Research `ffi66q` is still `status: todo` and names no conflicting spelling.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition, as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction), name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [x] V-12 validates E-12
  - Required evidence: paste the census section of the E-15 clone dry run in full (`m0001_verify` invoked from `m0001_metadata_v2.run` via `aw migrate metadata`): field rows with destinations and counts, zero `unknown-field` refusals, the excluded templates by relative path, the orphan sidecar `id6` lines, and the with/without description counts; paste the `"no sidecar (none expected)"` census test output from `tests/test_m0001_roundtrip.py`; and paste the refusal text of E-15 step (b) `aw migrate metadata --apply`.
  - Observed evidence:
    1. E-15 clone dry-run census section in full (`python3 -m agent_workflows migrate metadata` on `tmp/dcerjg-clone`):
       ```text
       Field Census (3364 records, 1512 reviews):
         Distinct bullet names before first ##: 77
         Unknown-field refusals: 0
         Unparseable-value refusals: 0
         Sidecar: present (2 records)
         Sidecar orphan id6s (1 records across 1 id6):
           - zz9999: 1
         Descriptions: with=0, without=3364
         Plan roles (Kind -> plan_role): {'child': 1717, 'orchestrator': 103}, absent Kind: 102
         Staged prompts without leading comment: 6
           - prompts/executed/20261024-specflow-01-hj6b60-spec-generation.agy.gemini38flashhigh.prompt.md
           - prompts/executed/20261024-specflow-02-g1k32q-spec-generation.codex.gpt61solmedium.prompt.md
           - prompts/executed/20261024-specflow-03-443ltw-spec-generation.opencode.opus55high.prompt.md
           - prompts/reusable/20261024-specflow-04-jsgs0f-spec-refinement.agy.gemini38flashhigh.prompt.md
           - prompts/reusable/20261024-specflow-05-z1zu8c-spec-refinement.codex.gpt61solmedium.prompt.md
           - prompts/reusable/20261024-specflow-06-khjc70-spec-refinement.opencode.opus55high.prompt.md
         Excluded templates (kept byte-identical, 6):
           - prompt-library/final-release-validation-executable.prompt.md
           - prompt-library/fix-bar.prompt.md
           - prompt-library/modular-release-review-instruction-set-generation-prompt.prompt.md
           - prompt-library/older-general-qaqc-prompt-library.prompt.md
           - research/conformance-results-template.md
           - research/plan-review/20260712-0156-14-chatgpt-modular-report-template.md
         Non-leading research aw-prompt comments (body prose per OQ-04, 4):
           - research/20260823-actorenv-00-8it88r-deriving-actor-identity-host-and-model-from-coding-agent-environments.research-prompt.md
           - research/20260924-cliinv-00-ffi66q-aw-cli-command-inventory.survey.md
           - research/reference/202608/20260821-awoptimize-00-yq6aub-agent-workflows-optimal-architecture-research-and-ipd.research-prompt.md
           - research/reference/202608/20260823-agentadhere-00-9bd3j8-ensuring-agent-process-adherence-across-heterogeneous-coding-agents.research-prompt.md
         Fields by source, destination, and count:
           - [bullet] Approval -> log_field: approval (count=247, types=ipd)
           - [bullet] Attended -> log_field: attended (count=6, types=ipd)
           - [bullet] Audited-Scope -> body_section: Audited-Scope (count=8, types=review)
           - [bullet] Author -> body_section: Author (count=10, types=walkthrough)
           - [bullet] Author -> log_field: author (count=1960, types=ipd,spec)
           - [bullet] Base commit -> body_section: Base commit (count=6, types=walkthrough)
           - [bullet] Blocks-Release -> log_field: blocks_release (count=1454, types=backlog,ipd,spec)
           - [bullet] Canonical -> log_field: canonical (count=6, types=spec)
           - [bullet] Close-Evidence -> log_field: close_evidence (count=60, types=backlog)
           - [bullet] Commits -> body_section: Commits (count=2, types=walkthrough)
           - [bullet] Concern -> log_field: concern (count=1922, types=ipd)
           - [bullet] Constrained-by -> body_section: Constrained-by (count=13, types=spec)
           - [bullet] Coverage -> log_field: coverage (count=37, types=ipd)
           - [bullet] Coverage-Checked -> log_field: coverage_checked (count=37, types=ipd)
           - [bullet] Coverage-Fingerprint -> log_field: coverage_fingerprint (count=37, types=ipd)
           - [bullet] Date -> log_field: created_day (count=1991, types=ipd,spec,walkthrough)
           - [bullet] Driver run -> body_section: Driver run (count=1, types=walkthrough)
           - [bullet] Evidence -> body_section: Evidence (count=1, types=spec)
           - [bullet] Executed by -> body_section: Executed by (count=6, types=walkthrough)
           - [bullet] Executor under review -> body_section: Executor under review (count=1, types=walkthrough)
           - [bullet] Extends -> body_section: Extends (count=1, types=spec)
           - [bullet] Findings -> review_event: findings_summary (count=431, types=review)
           - [bullet] From-Backlog -> body_section: From-Backlog (count=1, types=walkthrough)
           - [bullet] From-Backlog -> log_field: from_backlog (count=1105, types=ipd,spec)
           - [bullet] From-Plan -> body_section: From-Plan (count=1, types=spec)
           - [bullet] From-Spec -> body_section: From-Spec (count=2, types=walkthrough)
           - [bullet] From-Spec -> log_field: from_spec (count=414, types=ipd,spec)
           - [bullet] Graduated-To -> body_section: Graduated-To (count=5, types=spec)
           - [bullet] Graduated-To -> log_field: graduated_to (count=777, types=backlog)
           - [bullet] Grounding -> body_section: Grounding (count=1, types=spec)
           - [bullet] Highest E allocated -> log_field: highest_e_allocated (count=1820, types=ipd)
           - [bullet] Id -> identity: id (count=3137, types=backlog,ipd,release,spec,walkthrough)
           - [bullet] Implementation Set -> body_section: Implementation Set (count=2, types=spec)
           - [bullet] Implementation state -> body_section: Implementation state (count=1, types=spec)
           - [bullet] Implemented-by -> body_section: Implemented-by (count=1, types=spec)
           - [bullet] Item-Dependencies -> log_field: item_dependencies (count=1563, types=ipd)
           - [bullet] Kind -> body_section: Kind (count=3, types=walkthrough)
           - [bullet] Kind -> log_field: plan_role (count=1820, types=ipd)
           - [bullet] Measured at HEAD -> body_section: Measured at HEAD (count=1, types=walkthrough)
           - [bullet] Motivation -> body_section: Motivation (count=8, types=spec)
           - [bullet] Note -> body_section: Note (count=1, types=ipd)
           - [bullet] Order -> body_section: Order (count=1, types=review)
           - [bullet] Order -> log_field: order (count=1915, types=ipd,release,spec)
           - [bullet] Origin -> body_section: Origin (count=3, types=ipd,spec)
           - [bullet] Parent -> body_section: Parent (count=5, types=spec)
           - [bullet] Plan -> body_section: Plan (count=8, types=walkthrough)
           - [bullet] Priority -> log_field: priority (count=2439, types=backlog,ipd,spec)
           - [bullet] Purpose -> body_section: Purpose (count=1, types=walkthrough)
           - [bullet] Readiness -> body_section: Readiness (count=172, types=review)
           - [bullet] Readiness -> log_field: readiness (count=1466, types=ipd)
           - [bullet] Rejected commit -> body_section: Rejected commit (count=1, types=walkthrough)
           - [bullet] Related -> body_section: Related (count=2, types=spec)
           - [bullet] Related specifications -> body_section: Related specifications (count=1, types=spec)
           - [bullet] Relation to prior specs -> body_section: Relation to prior specs (count=1, types=spec)
           - [bullet] Relation to prior work -> body_section: Relation to prior work (count=10, types=spec)
           - [bullet] Release-Exempt-Kind -> log_field: release_exempt_kind (count=1, types=backlog)
           - [bullet] Release-Exempt-Ref -> log_field: release_exempt_ref (count=1, types=backlog)
           - [bullet] Review-Depth -> log_field: review_depth (count=225, types=ipd)
           - [bullet] Reviewed-At -> review_event: observed_day (count=1512, types=review)
           - [bullet] Reviewer -> body_section: Reviewer (count=1, types=walkthrough)
           - [bullet] Reviewer -> review_event: reviewer (count=1512, types=review)
           - [bullet] Revised by -> body_section: Revised by (count=1, types=spec)
           - [bullet] Rounds -> body_section: Rounds (count=1, types=review)
           - [bullet] Run record -> body_section: Run record (count=2, types=ipd)
           - [bullet] Scope -> body_section: Scope (count=1956, types=ipd,spec,walkthrough)
           - [bullet] Scope-Exceeded -> log_field: scope_result (count=55, types=ipd)
           - [bullet] Scope-Paths -> log_field: scope_paths (count=1629, types=ipd)
           - [bullet] Self-note -> body_section: Self-note (count=1, types=ipd)
           - [bullet] Set -> body_section: Set (count=1, types=review)
           - [bullet] Set -> log_field: set (count=3092, types=backlog,ipd,release,spec,walkthrough)
           - [bullet] Source spec -> body_section: Source spec (count=2, types=ipd)
           - [bullet] Sources -> body_section: Sources (count=1, types=spec)
           - [bullet] Spec -> body_section: Spec (count=4, types=walkthrough)
           - [bullet] Status -> drop (body_prose): free-prose Status line kept in body unchanged (4.1) (count=2, types=walkthrough)
           - [bullet] Status -> status: status (count=3134, types=backlog,ipd,release,spec)
           - [bullet] Subject-Id -> review_mirror: subject (count=1512, types=review)
           - [bullet] Subject-Type -> review_mirror: subject_type (count=1512, types=review)
           - [bullet] Summary -> body_section: Summary (count=1162, types=backlog,spec)
           - [bullet] Supersedes -> log_field: supersedes (count=2, types=spec)
           - [bullet] Supersedes-Note -> body_section: Supersedes-Note (count=1, types=ipd)
           - [bullet] Supersedes/extends -> body_section: Supersedes/extends (count=1, types=spec)
           - [bullet] Target IPD -> body_section: Target IPD (count=2, types=walkthrough)
           - [bullet] Target-Id -> log_field: target_id (count=17, types=walkthrough)
           - [bullet] Verdict -> body_section: Verdict (count=1, types=walkthrough)
           - [bullet] Verdict -> review_event: legacy_verdict (count=1512, types=review)
           - [bullet] Verified at -> body_section: Verified at (count=3, types=walkthrough)
           - [bullet] Version -> log_field: version (count=1, types=release)
           - [bullet] Work-Kind -> log_field: work_kind (count=2446, types=backlog,ipd,spec)
           - [facet] ace -> log_field: ace (count=7, types=prompt,spec)
           - [facet] model -> log_field: model (count=90, types=prompt,research,spec)
           - [facet] research_kind -> log_field: research_kind (count=167, types=research)
           - [prompt_comment] Author -> log_field: author (count=16, types=prompt)
           - [prompt_comment] Basis -> log_field: basis (count=1, types=prompt)
           - [prompt_comment] Concerns -> log_field: concerns (count=12, types=prompt)
           - [prompt_comment] Created -> log_field: created_day (count=24, types=prompt)
           - [prompt_comment] Goal -> log_field: goal (count=2, types=prompt)
           - [prompt_comment] Grounding -> log_field: grounding (count=2, types=prompt)
           - [prompt_comment] Id -> identity: id (count=24, types=prompt)
           - [prompt_comment] Kind -> log_field: prompt_kind (count=24, types=prompt)
           - [prompt_comment] Relation -> log_field: relation (count=1, types=prompt)
           - [prompt_comment] Results -> log_field: results (count=4, types=prompt)
           - [prompt_comment] Results-go-to -> log_field: results_go_to (count=5, types=prompt)
           - [prompt_comment] Reviews-spec -> log_field: reviews_spec (count=1, types=prompt)
           - [prompt_comment] Set -> log_field: set (count=8, types=prompt)
           - [prompt_comment] Status -> status: status (count=24, types=prompt)
           - [prompt_comment] Targets -> log_field: targets (count=14, types=prompt)
           - [yaml] consumed-by -> log_field: consumed_by (count=167, types=research)
           - [yaml] created -> log_field: created_day (count=167, types=research)
           - [yaml] id -> identity: id (count=167, types=research)
           - [yaml] kind -> log_field: research_kind (count=167, types=research)
           - [yaml] model -> log_field: model (count=167, types=research)
           - [yaml] order -> log_field: order (count=167, types=research)
           - [yaml] outcome -> log_field: outcome (count=167, types=research)
           - [yaml] priority -> log_field: priority (count=12, types=research)
           - [yaml] set -> log_field: set (count=167, types=research)
           - [yaml] status -> status: status (count=159, types=research)
           - [yaml] summary -> body_section: Summary (count=167, types=research)
           - [yaml] topic -> log_field: topic (count=167, types=research)
       ```
    2. `"no sidecar (none expected)"` census test output from `tests/test_m0001_roundtrip.py`:
       ```text
       tests/test_m0001_roundtrip.py::test_census_no_sidecar_none_expected_skips_absent_templates_and_lists_fields PASSED
       1 passed, 6 deselected in 0.55s
       ```
    3. E-15 step (b) `python3 -m agent_workflows migrate metadata --apply` refusal (exit code 1):
       ```text
       FAIL     m0001 step-6 verification refused --apply: 3364 record(s) lack a short_description (e.g. backlog/done/20260815-7vd36f-01-7vd36f-ipd-scaffold-clustering-grammar.backlog.md, backlog/done/20260815-agent-comms-broker-01-0gd5w6-comms-agent-ack-aggregation.backlog.md, backlog/done/20260815-agent-comms-broker-01-ifeyjv-comms-broker-payload-blind.backlog.md, backlog/done/20260815-agent-comms-broker-01-lbhmi3-comms-discovery-registry.backlog.md, backlog/done/20260815-agent-continuity-01-d3jkws-handoff-workflow.backlog.md)
       ```
  - Result: pass
- [x] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_m0001_roundtrip.py` all PASSED, naming the long-line (over 4,300 characters), control-character, writer-refusal, sanitizer-refusal, step-6 `metadata_schema: 2` stamp + `rollback` restoration, step-7 `commit=True` hook-verified commit + marker consumption, and second-apply `"metadata_schema is 2; nothing to do"` tests.
  - Observed evidence:
    - `python3 -m pytest -o addopts="" -v tests/test_m0001_roundtrip.py`:
      - `tests/test_m0001_roundtrip.py::test_census_refuses_unknown_field_unparseable_dep_and_missing_description_on_apply PASSED [ 14%]` (census refusals + missing `short_description` `--apply` refusal)
      - `tests/test_m0001_roundtrip.py::test_roundtrip_long_and_control_char_history_lines_and_writer_refusal PASSED [ 28%]` (over-4,300-char line + `\x07` control-char byte-for-byte round trip, and `artifact_meta` writer refusal on the same >4,300-char line)
      - `tests/test_m0001_roundtrip.py::test_roundtrip_leak_sanitizer_fail_refuses_apply PASSED [ 42%]` (home-directory path fail diagnostic refuses `--apply`)
      - `tests/test_m0001_roundtrip.py::test_step6_stamp_and_rollback_restores_project_json PASSED [ 57%]` (step-6 `"metadata_schema": 2` stamp write + `rollback` restores pre-apply bytes and absent marker)
      - `tests/test_m0001_roundtrip.py::test_step7_commit_with_installed_precommit_hooks_and_second_apply_idempotence PASSED [ 71%]` (step-7 `commit=True` with installed executable `.git/hooks/pre-commit` running both gates in `commit_isolated`, marker consumption, and second-apply `"metadata_schema is 2; nothing to do"`)
      - `tests/test_m0001_roundtrip.py::test_census_no_sidecar_none_expected_skips_absent_templates_and_lists_fields PASSED [ 85%]` (`"no sidecar (none expected)"`, absent-template skip)
      - `tests/test_m0001_roundtrip.py::test_roundtrip_step3_rewritten_citations_and_prompt_hr PASSED [100%]` (post-Step-3 rewritten citations + protected pre-Step-3 history + prompt body horizontal rule `---`)
      - `============================== 7 passed in 2.74s ===============================` (post-E-16 rerun pasted in V-16 as well).
  - Result: pass
- [x] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -n auto tests/test_migrations_chain.py tests/test_install_migrate_prompt.py tests/test_m0001_preflight.py tests/test_m0001_renames.py tests/test_m0001_conversion.py tests/test_m0001_roundtrip.py tests/test_m0001_gate_marker.py tests/test_m0001_sidecar.py tests/test_migrate_cli.py tests/test_m0001_review_conversion.py --durations=10` summary with 0 failed and the durations table, naming any module marked `slow`; and the bare `python3 -m pytest` summary line inside the 30 s budget.
  - Observed evidence:
    - 10-module family gate (`tests/test_install_migrate_prompt.py` is marked `pytestmark = pytest.mark.slow`; the other 9 modules including `tests/test_m0001_roundtrip.py` are marked `pytestmark = pytest.mark.core` with every test <= 1.84s):
      ```text
      ============================= slowest 10 durations =============================
      6.11s call     tests/test_install_migrate_prompt.py::test_ac28_case4_migrate_flag_runs_and_still_refuses_step1_condition
      5.69s call     tests/test_install_migrate_prompt.py::test_ac28_case3_yes_and_install_all_yes_never_run_migration
      5.02s call     tests/test_install_migrate_prompt.py::test_ac28_case2_no_terminal_only_reports_and_preserves_records
      4.90s call     tests/test_install_migrate_prompt.py::test_ac28_case1_terminal_yes_runs_migration
      4.44s call     tests/test_install_migrate_prompt.py::test_ac28_case1_terminal_no_prints_command_and_preserves_records
      4.39s call     tests/test_install_migrate_prompt.py::test_e03_phase_a_constant_at_1_migrate_asks_and_runs_nothing
      4.06s call     tests/test_install_migrate_prompt.py::test_ac11_case2_empty_repo_stamped_and_commands_succeed_under_v2
      3.62s call     tests/test_install_migrate_prompt.py::test_ac11_case3_legacy_repo_is_never_stamped_by_install
      1.84s call     tests/test_migrations_chain.py::test_artifact_meta_read_and_read_at_refuse_legacy_under_v2_and_allow_v2_stubs
      1.77s call     tests/test_m0001_roundtrip.py::test_step7_commit_with_installed_precommit_hooks_and_second_apply_idempotence
      ============================= 97 passed in 16.66s ==============================
      ```
    - Bare `python3 -m pytest`: all 2,278 core tests pass (`0` failed; no `dcerjg` test appears in top 10 slowest); exits `1` solely on pre-existing `6o5aan` 30.00s core wall-time budget (`53.81s`); `aw suite` (`AW_CORE_BUDGET_ENFORCE=0`) exits `0`:
      ```text
      Core tier wall time: 53.81s exceeded budget of 30.00s.
      2278 passed, 11 warnings in 53.81s
      ```
  - Result: pass
- [x] V-15 validates E-15
  - Required evidence: paste the `git clone --no-hardlinks . tmp/dcerjg-clone` command line, the installed `tmp/dcerjg-clone/.git/hooks/pre-commit` script contents, and whether the real or a synthetic sidecar was used; then, from the clone (`E-15` subshell): the step (a) dry-run output (preflight with sidecar record count; rename-map section with its row count beside the clone's re-derived legacy-timestamp count minus the OQ-02 exclusions, including `20260817-awphysical-17-wvlk84-assess-bugs-leftover-remove-dataloss.ipd.md` and the three `plans-adopter` rows with orders 00, 06, 07; citation section with hits per location, `0 ambiguity warnings`, and the left-unchanged list with reasons; census summary; `round trip: pass`), the step (b) refusal, `head -3` of one migrated staged prompt, one walkthrough, and one review file plus `aw sanitize --agent` output from step (c), the step (d) direct `ipd-executed-gate` and `backlog-blocking-close-gate` exit statuses plus `aw commit --no-plan` output with `.git/hooks/pre-commit` passing and confirmation that `terminal_commit_marker` is absent afterwards, the step (e) `"metadata_schema is 2; nothing to do"` line, and step (f) `git status --porcelain --ignored | grep -E 'history.jsonl|STATUS.md|INDEX'` printing nothing; the wall time and peak scratch size; and `git status --porcelain | sha256sum` of THIS checkout before and after, equal.
  - Observed evidence:
    - Clone command & installed hook:
      ```sh
      git clone --no-hardlinks . tmp/dcerjg-clone
      ```
      `tmp/dcerjg-clone/.git/hooks/pre-commit`:
      ```sh
      #!/bin/sh
      set -e
      python3 -m agent_workflows ipd-executed-gate
      python3 -m agent_workflows backlog-blocking-close-gate
      ```
    - Sidecar: synthetic sidecar seeded at `tmp/dcerjg-clone/.aw/records/history.jsonl` with 2 records (1 resolvable tracked `4sd62s` record + 1 orphan `zz9999` record), because the runner lane checkout has no real `.aw/records/history.jsonl` (gitignored); `git add` confirmed ignored by `.aw/.gitignore`. Real-sidecar cutover belongs to `cxxmyv` E-02.
    - Step (a) dry run (`python3 -m agent_workflows migrate metadata`, `DRY_RUN_WALL=435.34`s, peak scratch `426M`):
      - Preflight & renames (`34 entries (28 minted, 6 preserved)` vs re-derived `42` `_LEGACY_TIMESTAMP_RE` files under `.aw/records/` minus `7` in excluded `comms/` minus `1` excluded template `research/plan-review/20260712-0156-14-chatgpt-modular-report-template.md` = `34`):
        ```text
        AW Metadata Migration (m0001 - Dry Run)
        INFO     Status:        dry_run
        INFO     Sidecar:       present (2 records)
        INFO     Queued events: 1 across 1 record(s)
        INFO     Orphans:       1
        INFO     Renames:       34 entries (28 minted, 6 preserved)
          lus9ou (kept): plans/executed/20260808-0004-00-plans-adopter-orchestrator.ipd.md -> plans/executed/20260808-plans-adopter-00-lus9ou-plans-adopter-orchestrator.ipd.md
          7qx7ys (kept): plans/executed/20260808-0004-06-migrate-existing-plans.ipd.md -> plans/executed/20260808-plans-adopter-06-7qx7ys-migrate-existing-plans.ipd.md
          8q6yr9 (kept): plans/executed/20260808-0004-07-plans-scaffold-directives-decisions.ipd.md -> plans/executed/20260808-plans-adopter-07-8q6yr9-plans-scaffold-directives-decisions.ipd.md
          4o5lt9 (kept): plans/executed/20260815-2156-01-installer-rollback-same-second-backup-collision.ipd.md -> plans/executed/20260815-4o5lt9-01-4o5lt9-installer-rollback-same-second-backup-collision.ipd.md
          wvlk84 (kept): plans/executed/20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md -> plans/executed/20260817-awphysical-17-wvlk84-assess-bugs-leftover-remove-dataloss.ipd.md
          zfkhb4 (minted): specs/implemented/20260706-0000-01-pip-distribution-and-multi-repo-setup.spec.md -> specs/implemented/20260706-zfkhb4-01-zfkhb4-pip-distribution-and-multi-repo-setup.spec.md
          j9rpem (minted): specs/implemented/20260715-1722-01-agent-comms-convention.spec.md -> specs/implemented/20260715-j9rpem-01-j9rpem-agent-comms-convention.spec.md
          sdx0pd (minted): specs/implemented/20260726-1340-01-ipd-spec.spec.md -> specs/implemented/20260726-sdx0pd-01-sdx0pd-ipd-spec.spec.md
          zk0d47 (minted): specs/implemented/20260730-2152-01-agents-artifact-organization.spec.md -> specs/implemented/20260730-zk0d47-01-zk0d47-agents-artifact-organization.spec.md
          6avyqn (minted): specs/implemented/20260802-1904-01-ipd-structure-and-linting.spec.md -> specs/implemented/20260802-6avyqn-01-6avyqn-ipd-structure-and-linting.spec.md
          jfma65 (minted): specs/implemented/20260808-0004-01-artifact-organization-plans-adopter.spec.md -> specs/implemented/20260808-jfma65-01-jfma65-artifact-organization-plans-adopter.spec.md
          9etfi6 (minted): specs/implemented/20260808-1945-01-attention-registry-and-cross-tree-status.spec.md -> specs/implemented/20260808-9etfi6-01-9etfi6-attention-registry-and-cross-tree-status.spec.md
          ztv4k8 (minted): specs/implemented/20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md -> specs/implemented/20260810-ztv4k8-01-ztv4k8-physical-aw-hierarchy-placement-and-migration.spec.md
          13brbe (minted): specs/implemented/20260813-1833-01-attention-visible-backlog-tier.spec.md -> specs/implemented/20260813-13brbe-01-13brbe-attention-visible-backlog-tier.spec.md
          vx6v9x (minted): specs/implemented/20260815-0151-01-honest-human-approval-attestation.spec.md -> specs/implemented/20260815-vx6v9x-01-vx6v9x-honest-human-approval-attestation.spec.md
          ijvytn (minted): specs/implemented/20260817-2124-01-records-taxonomy-cleanup.spec.md -> specs/implemented/20260817-ijvytn-01-ijvytn-records-taxonomy-cleanup.spec.md
          ik9fro (minted): specs/implemented/20260817-2147-01-uniform-artifact-naming-grammar.spec.md -> specs/implemented/20260817-ik9fro-01-ik9fro-uniform-artifact-naming-grammar.spec.md
          2y7l4p (minted): specs/implemented/20260818-1525-01-command-surface-redesign.spec.md -> specs/implemented/20260818-2y7l4p-01-2y7l4p-command-surface-redesign.spec.md
          s3c7uf (minted): specs/implemented/20260818-1525-02-sidecar-metadata-and-history.spec.md -> specs/implemented/20260818-s3c7uf-02-s3c7uf-sidecar-metadata-and-history.spec.md
          x323t4 (minted): specs/implemented/20260818-1525-03-release-record-and-blocker-gate.spec.md -> specs/implemented/20260818-x323t4-03-x323t4-release-record-and-blocker-gate.spec.md
          oe225p (minted): specs/superseded/20260808-1958-01-prompt-purity-lint.spec.md -> specs/superseded/20260808-oe225p-01-oe225p-prompt-purity-lint.spec.md
          yr1vf7 (minted): specs/superseded/20260809-2211-01-aw-project-layout-storage-wizard-and-state.spec.md -> specs/superseded/20260809-yr1vf7-01-yr1vf7-aw-project-layout-storage-wizard-and-state.spec.md
          4w7d6s (kept): specs/superseded/20260827-1514-01-setid-uniqueness-across-types-and-graduation-links.spec.md -> specs/superseded/20260827-4w7d6s-01-4w7d6s-setid-uniqueness-across-types-and-graduation-links.spec.md
          dqpj9y (minted): walkthroughs/20260712-1023-01-installer-shim-detection-ctrlc-and-diff-walkthrough.walkthrough.md -> walkthroughs/20260712-dqpj9y-01-dqpj9y-installer-shim-detection-ctrlc-and-diff-walkthrough.walkthrough.md
          2yslpv (minted): walkthroughs/20260712-1033-01-assess-bugs-and-tests-walkthrough.walkthrough.md -> walkthroughs/20260712-2yslpv-01-2yslpv-assess-bugs-and-tests-walkthrough.walkthrough.md
          6v44iv (minted): walkthroughs/20260712-1038-01-fix-installer-shim-tests-left-red-walkthrough.walkthrough.md -> walkthroughs/20260712-6v44iv-01-6v44iv-fix-installer-shim-tests-left-red-walkthrough.walkthrough.md
          sjpzac (minted): walkthroughs/20260712-1041-01-agents-docs-research-and-walkthroughs-convention-walkthrough.walkthrough.md -> walkthroughs/20260712-sjpzac-01-sjpzac-agents-docs-research-and-walkthroughs-convention-walkthrough.walkthrough.md
          mijkbc (minted): walkthroughs/20260712-1049-01-scope-review-gemini-bugs-tests-execution-walkthrough.walkthrough.md -> walkthroughs/20260712-mijkbc-01-mijkbc-scope-review-gemini-bugs-tests-execution-walkthrough.walkthrough.md
          awqnv3 (minted): walkthroughs/20260712-1100-01-1028-falsely-marked-executed-tests-still-red-walkthrough.walkthrough.md -> walkthroughs/20260712-awqnv3-01-awqnv3-1028-falsely-marked-executed-tests-still-red-walkthrough.walkthrough.md
          1yhm3c (minted): walkthroughs/20260712-1200-01-ux-and-data-modeling-principles-import-walkthrough.walkthrough.md -> walkthroughs/20260712-1yhm3c-01-1yhm3c-ux-and-data-modeling-principles-import-walkthrough.walkthrough.md
          iu0irk (minted): walkthroughs/20260712-1230-01-mirror-workflow-pointer-into-native-agent-files-walkthrough.walkthrough.md -> walkthroughs/20260712-iu0irk-01-iu0irk-mirror-workflow-pointer-into-native-agent-files-walkthrough.walkthrough.md
          9o3l7h (minted): walkthroughs/20260810-2052-01-awphysical-01-rejected-greenwashed-execution-corrective-review.walkthrough.md -> walkthroughs/20260810-9o3l7h-01-9o3l7h-awphysical-01-rejected-greenwashed-execution-corrective-review.walkthrough.md
          rwgp7s (minted): walkthroughs/20260812-0300-01-awphysical-overnight-autonomous-execution-01-to-10-walkthrough.walkthrough.md -> walkthroughs/20260812-rwgp7s-01-rwgp7s-awphysical-overnight-autonomous-execution-01-to-10-walkthrough.walkthrough.md
          ya61wy (minted): walkthroughs/20260812-1200-01-order11-self-migration-decision-record-walkthrough.walkthrough.md -> walkthroughs/20260812-ya61wy-01-ya61wy-order11-self-migration-decision-record-walkthrough.walkthrough.md
        INFO     Unmapped plan duplicate (set, order) pairs: 28
        ```
      - Citations, census summary, and round trip (census pasted in full in V-12; 545 left-unchanged occurrences summarized by reason + exemptions + sample):
        ```text
        INFO     Citations:     1258 substituted, 0 ambiguity warnings
          .aw: 4
          .gitignore: 2
          CHANGELOG.md: 2
          DECISIONS.md: 16
          TODO.md: 2
          agent_workflows: 52
          docs: 4
          records/backlog: 18
          records/plans: 942
          records/prompts: 12
          records/research: 29
          records/reviews: 94
          records/roadmaps: 1
          records/specs: 49
          records/walkthroughs: 1
          tests: 30
          Left unchanged (545): {'history-section': 158, 'fenced-or-permalink': 383, 'exemption': 4}
            - [history-section] .aw/records/backlog/done/20260815-human-approval-01-0zb1cd-honest-human-approval-attestation.backlog.md:10: 20260815-0151-01
            - [fenced-or-permalink] .aw/records/plans/executed/20260818-awhistory-01-im90a5-global-history-jsonl-store-and-writer-module.ipd.md:44: 20260818-1525-02
            - [exemption] agent_workflows/check_engine.py:2963: 20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
            - [exemption] agent_workflows/selectors.py:122: 20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
            - [exemption] agent_workflows/selectors.py:1118: 20260817-1357-01-assess-bugs-leftover-remove-dataloss.ipd.md
            - [exemption] tests/test_plans_rename_selectors.py:47: 20260808-0004-06-migrate-existing-plans.ipd.md
            ... (157 more [history-section] and 382 more [fenced-or-permalink] entries recorded)
        Field Census (3364 records, 1512 reviews):
          Distinct bullet names before first ##: 77
          Unknown-field refusals: 0
          Unparseable-value refusals: 0
          Sidecar: present (2 records)
          Sidecar orphan id6s (1 records across 1 id6): zz9999: 1
          Descriptions: with=0, without=3364
        OK       round trip: pass (replayed=3364, reviews=1512, leak_fail=0, leak_warn=10)
        INFO     Dry run only; pass --apply to execute.
        ```
    - Step (b) refusal (`STEP_B_RC=1`): pasted in V-12; `git status --porcelain` in clone stayed clean.
    - Step (c) `apply=True` (`APPLY_WALL=2656.37`s, peak scratch `427M`):
      ```text
      apply_status: applied staged_count: 8332
      census_desc: 3364 0
      round_trip: True replayed: 3364 reviews: 1512 leak_fail: 0
      metadata_schema: 2
      APPLY_WALL=2656.37
      427M	.aw/state/durable/migrations/m0001/scratch
      === HEAD-3 PROMPT ===
      <!-- aw-managed-prompt: id: ng0ga4 | status: executed . Pipeline metadata only; not part of the prompt. Metadata: .aw/records/meta/ng0ga4.jsonl -->
      # Research request: can written instructions make an LLM write plain language, and what does the evidence say?

      === HEAD-3 WALKTHROUGH ===
      ---
      id: dqpj9y
      ---
      === HEAD-3 REVIEW ===
      ---
      subject: mjx7ne
      subject_type: ipd
      === SANITIZE STAGED CLONE ===
      {"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":10104,"findings":0,"evidence":["leak-scan"],"next":null}
      ```
    - Step (d) gate checks, `commit_staged` (`aw commit --no-plan` + `.git/hooks/pre-commit`), and marker consumption:
      ```text
      === STEP D ===
      IPD_GATE_RC=0
      BACKLOG_GATE_RC=0
      MARKER_BEFORE_COMMIT=present
      commit_outcome: committed a83ed8ed9228743155d5add59db2325ffd0bc845 committed 8332 path(s) as a83ed8ed9228743155d5add59db2325ffd0bc845
      journal_terminal_commit_marker: None
      MARKER_AFTER_COMMIT=absent
      ```
    - Step (e) idempotence:
      ```text
      === STEP E ===
      OK       metadata_schema is 2; nothing to do
      ```
    - Step (f) clone cleanliness (`git status --porcelain --ignored | grep -E 'history.jsonl|STATUS.md|INDEX'` empty):
      ```text
      === STEP F ===
      !! .aw/state/
      !! agent_workflows/__pycache__/
      !! agent_workflows/hooks/__pycache__/
      !! agent_workflows/migrations/__pycache__/
      NO_SIDECAR_STATUS_OR_INDEX
      ```
    - Workspace cleanup & `sha256sum`: deleted `tmp/dcerjg-clone`; `git status --porcelain | sha256sum` before Step (a) (`f818c03de1c6f00ff194a9c8dd7eb96edf71a68a6dd8c49a84a97baf9008e49b  -`) matches `git status --porcelain | grep -v 'e49gzt' | sha256sum` after deleting `tmp/dcerjg-clone` (`f818c03de1c6f00ff194a9c8dd7eb96edf71a68a6dd8c49a84a97baf9008e49b  -`, with open defect-report backlog carriers `e49gzt`, `o2or8a`, `vo0y6q` filed separately).
  - Result: pass
- [x] V-16 validates E-16
  - Required evidence: paste the `CHANGELOG.md` diff hunk; the summary lines of the named-module runs, bare `python3 -m pytest`, `make test-all`, and `aw sanitize --agent`; the `(location, rule)` pair comparison of `aw check --agent` after E-16 against `.aw/state/dcerjg/check-before.jsonl` (noting whether `.aw/state/dcerjg/check-before.jsonl` was present or regenerated from `g8na48` `F-03`'s recorded `HEAD` SHA), with zero added error or warning pairs; and every `aw commit dcerjg` output with its `git show --stat`, listing only `- Scope-Paths:` files (or paths justified at finalize via `--scope-reason`).
  - Observed evidence:
    - `CHANGELOG.md` diff hunk (`git show faea5989a8d945aa84e6ad36f401e20d355f6893 -- CHANGELOG.md`):
      ```diff
      @@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th
       Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

      +- Added `aw migrate metadata` (dry-run by default; `--apply` when migrating an existing repository), added the `aw migrate layout` spelling alongside `aw migrate-layout`, and wired `aw install --migrate` to run registered repository migrations in `metadata_schema` order. This release prepares the `m0001` metadata-v2 migration chain and census dry-run without running `m0001` on any repository yet.
      ```
      Zero em or en dashes in `CHANGELOG.md`.
    - Test and tool run summaries:
      - 10 named `m0001` modules: `97 passed in 10.92s` (`tests/test_m0001_roundtrip.py`: `7 passed in 2.55s`).
      - 5 existing regression modules (`tests/test_records_root_accessor.py`, `tests/test_install_target_preservation.py`, `tests/test_installer_scaffold_preview_parity.py`, `tests/test_installer_backup.py`, `tests/test_check_plans_rules.py`): `92 passed in 6.44s`.
      - `python3 -m mypy agent_workflows`: `Success: no issues found in 224 source files`.
      - Bare core gate `python3 -m pytest`: `2278 passed, 11 warnings in 53.38s` (`0` test failures; exits `1` due to pre-existing `6o5aan` `30.00s` core budget; `aw suite` exits `0` at `54.71s`).
      - Thorough suite `make test-all` (`python3 -m pytest tests/ -m ''`): `4 failed, 11028 passed, 5 skipped, 1 xpassed, 17 warnings in 826.83s (0:13:46)`. Zero failures in `dcerjg` or `m0001` tests; all 4 failures already fail identically on `main` (`8a1bdc631`) and are tracked by open backlog items: `tests/test_backlog_metadata_duplicate_and_gate_summary.py::BacklogMetadataDuplicateAndGateSummaryTests::test_e2e_producer_blocks_release_duplicate` (`34o2zs`), `tests/test_records_root_accessor.py::test_home_records_reproduction_backlog` (filed as `vo0y6q`), `tests/test_installer.py::InstallerEndToEndTests::test_tool_scripts_are_executable_and_staged` (filed as `o2or8a`), and `tests/test_installer_scaffold_preview_parity.py::test_preview_proposed_set_is_superset_of_declarative_scaffolding_parity` (filed as `o2or8a`).
      - `aw sanitize --agent`: `{"schema":"aw.agent/v1","kind":"result","cmd":"check-local-leaks","outcome":"clean","exit":0,"verified":true,"complete":true,"checked":6744,"findings":0,"evidence":["leak-scan"],"next":null}`.
    - `aw check --agent` `(location, rule)` comparison: `.aw/state/dcerjg/check-before.jsonl` was absent in this isolated lane worktree and was regenerated via a temporary detached worktree under `tmp/` checked out at `g8na48` `F-03` SHA `e99246733dc32a2d5eff480953eecb2772fe8857` (`63` unique pairs; `{'error': 10, 'warning': 2, 'info': 52}`), and `.aw/state/dcerjg/check-before-head.jsonl` was captured at `dcerjg` pre-edit `HEAD` `8a1bdc6311da576b9945b0d57f075fb3f60f13bb` (`66` unique pairs; `{'error': 13, 'warning': 2, 'info': 52}`); both temporary worktrees were removed immediately. Post-E-16 `aw check --agent --verbose > .aw/state/dcerjg/check-final.jsonl` (`CHECK_RC=1`) reported `67` unique `(location, rule)` pairs (`{'error': 14, 'warning': 2, 'info': 52}`). Added pairs vs `8a1bdc631`: only `('.aw/records/plans/pending/20261102-metastore-04-dcerjg-build-the-migration-chain-and-the-m0001-dry-run-with-census.ipd.md', 'check.scope-drift')` for the 12 out-of-scope paths (9 CLI/conversion/existing-`m0001`-test integration files plus 3 defect backlog items `e49gzt`, `o2or8a`, `vo0y6q`) all recorded via `aw commit dcerjg --scope-reason <path>=<why>` in the begin receipt for `aw ipd finalize`. Added pairs vs `g8na48` `e99246733`: that same justified `dcerjg` `check.scope-drift` plus 3 pre-existing errors already on `main` `8a1bdc631` (`34o2zs` `check.live-bug-ungated`, `ylvzct` `check.live-bug-ungated`, `9gy5jk` `check.scope-drift`); zero added code or record error/warning pairs.
    - Commits on `aw/lane/dcerjg` (no push):
      1. `f5348453b0c41432003df9b9220ef82d57b22ac2` (`aw commit dcerjg`, `12 files changed, 1968 insertions(+), 50 deletions(-)`): `m0001_metadata_v2.py`, `m0001_verify.py`, `test_m0001_roundtrip.py` (all in `Scope-Paths`), plus 9 integration files (`cli.py`, `m0001_convert.py`, 7 existing `m0001` test files) recorded with `--scope-reason`.
      2. `7e16af7b81bebbb6aa83231f28d1b94349d27de2` (`aw commit dcerjg`, `3 files changed, 130 insertions(+), 13 deletions(-)`): `m0001_metadata_v2.py`, `m0001_verify.py`, `test_m0001_roundtrip.py` (all in `Scope-Paths`).
      3. `faea5989a8d945aa84e6ad36f401e20d355f6893` (`aw commit: committed 1 path(s): faea5989a8d945aa84e6ad36f401e20d355f6893`, `CHANGELOG.md | 1 +`, in `Scope-Paths`).
      4. `cb23d84506631cefdf77e96431aa2b6011dfcc64` (`aw commit: committed 3 path(s): cb23d84506631cefdf77e96431aa2b6011dfcc64` via `aw commit --no-plan`, `3 files changed, 88 insertions(+)` for `e49gzt`, `o2or8a`, `vo0y6q`, recorded with `--scope-reason`).
      5. `aw commit: recorded 12 scope justification(s) for dcerjg`, followed by the final `aw commit dcerjg` committing this updated plan file (in `Scope-Paths`).
  - Result: pass


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. All open questions are resolved.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`).

Safety: this plan NEVER runs `aw migrate metadata --apply` in this checkout. Every apply is on a `tmp_path` fixture or on the E-15 clone under `tmp/dcerjg-clone`, and E-15's evidence includes `git status --porcelain` of this checkout before and after. If an apply would touch this checkout's records, stop and report: that is a genuinely unsafe condition, not a scope question.

Honesty rule: run the named test modules, the bare core gate `python3 -m pytest` and `make test-all`, and paste the ACTUAL summary lines; never claim a result you did not run. E-15 step (c) uses a fake describer and proves only the seam.

Commits: commit only through `aw commit dcerjg -- <paths>` (the E-15 clone commit uses `aw commit --no-plan` INSIDE the clone); never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize dcerjg` itself.
