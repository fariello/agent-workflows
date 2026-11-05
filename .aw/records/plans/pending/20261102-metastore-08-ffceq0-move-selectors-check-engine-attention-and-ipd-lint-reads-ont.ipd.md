# IPD: Move selectors, check_engine, attention and ipd_lint reads onto artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` C5 and C5a require that every metadata read goes through `artifact_meta` and its SQLite cache, and section 7 step 5 moves the readers while the bullet format is still on disk. Measured 2026-11-02 at `0cbfcc706`: 59 of 211 package modules contain a legacy bullet pattern, a `^-` metadata regular expression or a `## Workflow history` reference; 200 metadata regular-expression call sites start with `^-`; the four read surfaces this plan owns (`selectors`, `check_engine`, the `attention` modules, `ipd_lint`, plus the `aw find` and `aw ipd board` paths in `cli` that consume them) hold 52 of those call sites and every one of the 17 `history_block` and `last_history_at` reader calls outside the setters. Two readers of the same field disagree today: `selectors._read_status` (single token) and `plans_index.plan_entry` (whole line) return different statuses for 24 tracked plans, so `aw find plans executed` lists 1,610 plans while `aw find plans --status executed` lists 1,635. Until these readers move, Order 11 (`9o83cr`) cannot delete the parsers and AC-1 cannot hold.
- Scope: Phase B readers, part 1 of 2 (`4sd62s` section 7 step 5). Move the metadata READS of `selectors`, `cli._find_type_records` with its prompt helpers and `cli._run_search`, `cli._run_plans` (`aw ipd board`), `attention` (every per-tree `_*_record`, `_plans_id`, `_extract_detail`), `attention_contract.history_block` and `last_history_at` callers, `plans.read_status`/`plans.scan`, `check_engine` working-tree readers (every `_read_*`, `_metadata_status` working-tree call, every `^-` metadata literal, `known_spec_ids`, `build_dependency_index`, `build_graduation_reverse_index`, `graduation_cluster`, `evaluate_blocking_close`, `evaluate_handoff_ready`, `check_spec_review_attestation`), and `ipd_lint` (`parse` metadata slice, the `IPD-S405`/`IPD-M107`/`IPD-M112`/`IPD-M113` history and field reads, `run_lint` row reads) onto `artifact_meta.read`, `artifact_meta.history`, `artifact_meta.query` and `artifact_meta.resolve`. Add `aw check meta` (4.6) and `aw meta repair` (4.3, 4.7) as the CLI over the Order 02 functions, and one additive interface function, `artifact_meta.read_text`, for metadata of in-memory text (OQ-03). Replace the three `_SKIP_NAMES` copies with one exclusion list (4.4 last bullet). Record the kept behavior for the `selectors`/`plans_index` disagreement. EXCLUDES: every reader of HEAD, staged or branch content (`check_engine._blob_text`/`_status_meta` git callers, hooks, runner) and the runner, plans/research/prompts index, `artifact_audit` and `review_findings` modules (Order 09, `t4gl15`); deleting the old parsers and INDEX code (Order 11, `9o83cr`); writers (Orders 06 and 07).
- Scope-Paths: agent_workflows/selectors.py, agent_workflows/cli.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/plans.py, agent_workflows/check_engine.py, agent_workflows/ipd_lint.py, agent_workflows/ipd_schema.py, agent_workflows/artifact_refs.py, agent_workflows/layout.py, agent_workflows/meta_cli.py, agent_workflows/command_surface.py, agent_workflows/artifact_meta.py, tests/conformance_matrix.py, tests/test_readers_selectors_find.py, tests/test_readers_attention.py, tests/test_readers_check_engine.py, tests/test_readers_ipd_lint.py, tests/test_check_meta.py, tests/test_meta_repair_cli.py, tests/test_readers_cache_parity.py, tests/test_readers_offline.py, tests/test_front_matter_loose_whitespace.py, tests/test_find_single_read.py, tests/test_selector_two_dialect_readers.py, docs/cli-output-contract.md, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-08-ffceq0-move-selectors-check-engine-attention-and-ipd-lint-reads-ont.ipd.md
- Item-Dependencies: executed:tve77h, executed:xexn45
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 8
- Highest E allocated: 14
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ffceq0

## Workflow history
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every metadata read in the search, attention, check and lint surfaces answers from the `artifact_meta` cache (still filled by the legacy loader from today's bullets), each moved reader keeps a named, tested behavior, `aw check meta` and `aw meta repair` exist, and the `selectors`/`plans_index` status disagreement is resolved by a recorded decision instead of by two regular expressions.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Every E-item that moves a reader follows one rule, so a reviewer can check each the same way: (1) BEFORE the edit, add or extend a behavioral test in the named module that pins the reader's CURRENT observable behavior on a `tmp_path` fixture repository (the "prior behavior" column of the reader ledger in `## Findings`), and run it green against the unmodified code; (2) change the reader to call `artifact_meta`; (3) run the same test unchanged. A test that has to change in step 3 is a behavior change and must be one of the decisions listed in the ledger (D-1 to D-4), never a silent one. New test modules set `pytestmark = pytest.mark.core`, call real functions or the real `aw` CLI, and never read production source.

### Task group 1: selectors, aw find and the status-disagreement decision

- [ ] E-01 Pin the current `aw find` and `selectors` behavior in `tests/test_readers_selectors_find.py` before any change: id6, Set, status, stem and substring selector matching per type; `aw find plans <id6>` and `--status`/`--status-not`/`--set`/`--id` filters; `aw find research` and `aw find prompts` rows (prompt id and Set from the `aw-prompt` comment, then the filename slot); `selectors.read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release` and `declared_id6` on loose-whitespace (`-  `, `-\t`) and quoted-example fixtures; `aw find` exit code 2 for a selector that matches nothing (4.4a row `zyj8io`); and the fixture form of the 24-plan disagreement (one plan with `- Status: EXECUTED (approved ...)` in `executed/`). Also run the existing `tests/test_find_filters.py` (4.4a row `wja06w`), `tests/test_find_single_read.py`, `tests/test_selector_two_dialect_readers.py`, `tests/test_front_matter_loose_whitespace.py` and `tests/test_selector_resolver_matrix.py` green.
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the summary line of the five existing modules is recorded as the baseline.
  - Execution state: pending

- [ ] E-02 Move `selectors` reads onto `artifact_meta`: `_read_id`, `_read_status`, `_read_setid`, `_read_yaml_scalar`, `read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release`, `declared_id6`, `declares_id6`, `id6_ownership` and the `resolve` selector kinds `MATCH_ID6`/`MATCH_SETID`/`MATCH_STATUS` answer from `artifact_meta.resolve`/`artifact_meta.read`/`artifact_meta.query`; filename-only kinds (`MATCH_STEM`, `MATCH_SUBSTRING`, `MATCH_PATH`) keep reading no file content. The public `read_front_matter_*(text)` functions keep their text signature for Order 09's callers in this phase and answer through the one additive interface function this plan adds, `artifact_meta.read_text(text, *, record_type=None) -> State` (OQ-03), so no regex remains in `selectors`. Apply decision D-1 (status) and D-2 (whitespace).
  - Depends on: E-01
  - Expected outcome: `rg -n "re\.(compile|search|match)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/selectors.py` prints nothing; the E-01 module and the five existing modules pass unchanged except the assertions that D-1 names.
  - Execution state: pending

- [ ] E-03 Move the `aw find` and `aw search` paths in `cli` onto `artifact_meta.query`: `_find_type_records` (plans, research, prompts, specs, backlog, releases branches), `_find_prompt_id6`, `_find_prompt_setid`, `_run_search._artifact_status`, and `_run_plans` (`aw ipd board` through `plans.scan`/`plans.read_status`). `plans.read_status` and `plans.scan` keep their signatures and return the same canonical readiness value (`plans.normalize_status`), now computed from the cached raw status. `aw find` shows `artifacts.short_description` when present and the current `detail` otherwise (AC-36 case 2 owner side).
  - Depends on: E-02
  - Expected outcome: E-01 passes; `aw find plans executed` and `aw find plans --status executed` list the same 1,635 paths on this checkout (D-1); `aw find plans zzzzzz` exits 2; `aw ipd board --agent` row count is unchanged from the baseline.
  - Execution state: pending

### Task group 2: attention

- [ ] E-04 Pin the current `aw attention` behavior in `tests/test_readers_attention.py`: per-tree status mapping (`attention.missing-status`, `attention.unknown-status`, disposition mismatch), `id`, `priority`, `blocks_release`, `readiness`, `last_history_at` (newest record by `attention_contract.newest_history_record`), gate fields, open-question counts and `detail_kind`/`detail_text` for one fixture of each tree (plans, specs, backlog, research, releases, prompts), and the `aw attention --check --agent` exit code with one violation. Run `tests/test_attention.py`, `tests/test_attention_contract.py`, `tests/test_history_consumers_shared_reader.py`, `tests/test_history_date_clock_readers.py` and `tests/test_prompts_attention.py` green as the baseline.
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the five existing modules' summary lines are recorded.
  - Execution state: pending

- [ ] E-05 Move `attention` reads onto `artifact_meta.query`: `scan` builds `Item`s from one `query()` over the in-scope types instead of reading each file; `_plans_record`, `_spec_record`, `_backlog_record`, `_research_record`, `_release_record`, `_prompts_record`, `_plans_id`, `_frontmatter_block`, `_ITEM_DEPS_RE` and `read_readiness` callers read cached fields; `last_history_at` comes from `artifact_meta.history` through the unchanged `attention_contract.last_history_at` rule (phase B: same lines, same answer; the post-cutover `last_history_precision` key is Order 13's, see Deferred). Body-derived columns (open-question counts, E/V counts) still read the body (N3). `_extract_detail` stays as the fallback when `short_description` is absent (D-3). A cross-artifact `query()` `incomplete` list becomes an `attention.missing-status` violation for each named record, so an invalid record is reported, never silently dropped.
  - Depends on: E-04
  - Expected outcome: E-04 and its five baseline modules pass unchanged; `aw attention --all --format json` on this checkout yields the same 3,096 items and 1 violation as the baseline (diff of sorted `id`/`tree`/`native_status`/`last_history_at` tuples is empty).
  - Execution state: pending

### Task group 3: check_engine working-tree readers

- [ ] E-06 Pin the current behavior of the `check_engine` working-tree readers in `tests/test_readers_check_engine.py`: `check.id-missing`/identity rules, `check_id_outside_metadata_region`, `known_spec_ids`, `build_dependency_index` with each `Item-Dependencies` form, `build_graduation_reverse_index` and `graduation_cluster` (declarations alone, origin links alone, both; 4.4a row `pw2ln3`), `evaluate_blocking_close` (handoff, satisfied, de-gated), `evaluate_handoff_ready`, `check_spec_review_attestation`, `check_live_bug_gate`, `check_from_spec_dangling`, `check_decision_ref_dangling`, `check_ipd_lint_reach` and `check_orchestrator_not_review_ready`, each on a `tmp_path` fixture through `aw check <type> --agent`. Run `tests/test_check_engine.py`, `tests/test_check_engine_metadata_region.py`, `tests/test_check_engine_release_gate.py`, `tests/test_from_backlog_cardinality.py`, `tests/test_graduation_forward_links.py`, `tests/test_gate_ref_resolution.py`, `tests/test_check_engine_from_spec_missing.py`, `tests/test_handoff_ready_gate.py` and `tests/test_spec_review_attestation.py` green as the baseline.
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the nine baseline summary lines are recorded.
  - Execution state: pending

- [ ] E-07 Move the `check_engine` working-tree metadata readers onto `artifact_meta`: `_read_declared_id`, `_read_item_id`, `_read_plan_status`, `_read_blocks_release`, `_read_setid` and the identity readers (`_identity_metadata_region` with its bullet/YAML pairs), the `_ITEM_*`/`_META_*`/`_PLAN_STATUS_RE`/`_ITEM_DEPENDENCIES_RE`/`_DATE_LINE_RE`/`_REVIEW_SUBJECT_TYPE_RE`/`_FROM_SPEC_LINE_RE`/`_CARRIER_DATE_RE` users, the inline `^- Kind:`/`^- Status:`/`^- Set:`/`^- Date:`/`^- Id:` searches, `backlog.parse_item` uses inside `check_engine`, the `prompts_index._parse_metadata_comment` use, and the `history_block`/`last_history_at` uses, all through `artifact_meta.read`/`query`/`history`. `_metadata_status(text)` keeps its text signature ONLY for the git-content callers that Order 09 moves to `read_at`; every working-tree call site passes through `artifact_meta.read` instead. Body-prose bullets kept by N3 (`_TARGET_BULLET_RE` over `Concern`/`Scope`/`Scope-Paths` body scanning for citations, open-question `Carrier*` rows) are NOT metadata reads and stay; each is listed in the E-14 exclusion list.
  - Depends on: E-06
  - Expected outcome: E-06 and its nine baseline modules pass unchanged; `aw check all --agent` on this checkout reports the same rule-id multiset as the pre-E-07 baseline (pasted sorted counts, empty diff).
  - Execution state: pending

- [ ] E-08 Replace the three `_SKIP_NAMES` copies (`check_engine`, `selectors`, `artifact_refs`) and the `records/meta/` exclusion with ONE list, `layout.RECORD_SCAN_SKIP_NAMES` beside `layout.TRAVERSAL_EXCLUSIONS` (4.4 last bullet; `artifact_core.iter_scan_files`, `selectors._iter_md` and `check_engine`'s walkers all consult it), adding `meta` as an excluded records subdirectory so a `meta/*.jsonl` log is never walked as a record. Tested behaviorally: a fixture with `.aw/records/meta/abc123.jsonl` and a `README.md` yields no `aw find`, `aw check` or `aw attention` row for either.
  - Depends on: E-07
  - Expected outcome: the fixture test passes; the three modules no longer define `_SKIP_NAMES` (shown by `rg -n "_SKIP_NAMES\s*=" agent_workflows`, which lists only `layout.py`).
  - Execution state: pending

### Task group 4: ipd_lint and the new meta commands

- [ ] E-09 Pin and move the `ipd_lint` metadata reads: `parse` takes `meta_fields`/`meta_errors` from `artifact_meta` for a tracked plan (the `ipd_schema.parse_metadata_block` grammar now runs only inside the legacy loader); `lint_text(text, *, state=None)` gains a `state` argument that carries the plan's `State` from `artifact_meta.read`, `artifact_meta.read_at` or `artifact_meta.read_text` (OQ-03), and uses `artifact_meta.read_text(text)` when the caller passes none, so the string callers in `review_sequence`, the runner and 58 test call sites keep working and no second parser exists; `IPD-S405` reads `artifact_meta.history` (4.4 bullet "Gate IPD-S405"); `IPD-M107`, `IPD-M113` and `IPD-M112` read cached `readiness`, `approval` and `coverage` fields and their history (their meaning is unchanged; the event-ownership form is Order 06's AC-15); `run_lint` row status, priority and `blocks_release` read cached fields; `_CITATION_PLAN_DATE_RE` reads cached `date`; `plans.read_status` is the shared status for `M105`. Pin first in `tests/test_readers_ipd_lint.py` (one fixture per rule id above, conforming and refused), run `tests/test_ipd_lint.py`, `tests/test_readiness_absence_invariant.py`, `tests/test_orchestrator_readiness.py` and `tests/test_plan_priority_required.py` green before and after.
  - Depends on: E-07
  - Expected outcome: every listed test passes before and after; `aw ipd lint` over every pending plan reports the same verdict per plan as the pre-change baseline (pasted per-plan verdict diff, empty).
  - Execution state: pending

- [ ] E-10 Add `aw check meta` (4.6) in `agent_workflows/meta_cli.py`, registered in `cli`, `command_surface` and `tests/conformance_matrix.py`: in phase B it runs every 4.6 row that the legacy format can express, reading only `artifact_meta.query` (in-file `status` and `id` mirror against cached state; filename Set, `NN`, `id6`, date and D177 facets through `artifact_naming`; research filename facets; disposition directory against status; review rounds against review rows; orphans: a `meta/*.jsonl` file with no record, and, once logs exist, a record with no log). Rows that need a log (logged path) report `not-applicable (legacy format)` so the output names them instead of skipping them. Exit 0 clean, 1 findings, 2 cannot-run; `--agent` emits `aw.agent/v1` records with `{location, rule}`. Test module `tests/test_check_meta.py`: one fixture per drift kind, each detected (AC-7 phase-B form), plus a clean fixture with zero findings.
  - Depends on: E-07
  - Expected outcome: each drift fixture produces exactly its rule id; the clean fixture exits 0; `aw check meta --agent` on this checkout runs to completion and its finding count by rule is pasted (not required to be zero before the cutover).
  - Execution state: pending

- [ ] E-11 Add `aw meta repair <id6> [--apply] [--confirm]` in `meta_cli.py` over the Order 02 `artifact_meta.repair` function: preview by default; `--apply` performs mirror and move repair (no event, log byte-identical, idempotent); a divergent-tail repair requires `--confirm` and prints every resulting field change first (4.7). In phase B no log exists, so the command reports `nothing to repair (legacy format)` on a legacy record and is exercised on synthetic log fixtures. Registered in `cli`, `command_surface` and `tests/conformance_matrix.py`. Test module `tests/test_meta_repair_cli.py`.
  - Depends on: E-10
  - Expected outcome: on a synthetic log fixture with a stale front-matter `status`, `aw meta repair <id6>` previews one mirror change and exits 0 with no file change, `--apply` rewrites the mirror and a second `--apply` changes nothing; on a legacy record it reports the legacy message.
  - Execution state: pending

### Task group 5: cache parity, offline proof and finish

- [ ] E-12 Add `tests/test_readers_cache_parity.py` (AC-1a, phase B form): for a fixture corpus with one record of each type, run `aw find` (all types), `aw attention --format json`, `aw check meta --agent`, `aw check all --agent` and `aw ipd lint` with (a) a cold cache, (b) a warm cache, (c) `.aw/state/index.db` deleted, (d) `index.db` overwritten with random bytes; assert byte-identical normalized outputs. Then edit one record's `- Status:` bullet outside `artifact_meta` (as a pull does) and assert the next `aw find` and `aw attention` show it with no rebuild; then replace a record with an unparseable one and assert it is REPORTED (`incomplete`/violation), not silently omitted and not served stale. Also covers AC-8 at the command level (with and without `index.db`, empty diff).
  - Depends on: E-03, E-05, E-07, E-09, E-10
  - Expected outcome: every case passes; the module is marked `core` and runs under 5 s.
  - Execution state: pending

- [ ] E-13 Add `tests/test_readers_offline.py` (AC-12 reader half): run `aw find`, `aw attention --format json` and `aw check all --agent` in a fixture repository with `PATH` stripped of every host binary (`opencode`, `agy`, `claude`) and with `socket.socket` patched to raise in a `sitecustomize` on `PYTHONPATH`; assert each succeeds. Paste `git diff 0cbfcc706 -- pyproject.toml` restricted to the `dependencies` list (unchanged).
  - Depends on: E-03, E-05, E-07
  - Expected outcome: three successful runs; the `dependencies` list reads `["filelock>=3"]`.
  - Execution state: pending

- [ ] E-14 Record the AC-1 partial audit and finish: run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/selectors.py agent_workflows/attention.py agent_workflows/check_engine.py agent_workflows/ipd_lint.py agent_workflows/plans.py` and `rg -n "history_block\(|last_history_at\(" agent_workflows/attention.py agent_workflows/check_engine.py agent_workflows/ipd_lint.py`; every remaining hit must be in the written exclusion list (body-prose bullets per N3, git-content readers carried by Order 09, or the plan's own `- [ ] E-` leaf grammar), which this item writes into the plan's `## Findings` as table F-12. Update `docs/cli-output-contract.md` with the two new leaves and add a `CHANGELOG.md` `2.0.0 (pending)` line. Run the named modules of E-01 to E-13, the bare core gate `python3 -m pytest`, `make test-all`, `aw check` (rule-id multiset equal to the E-07 baseline) and `aw sanitize --agent`; commit through `aw commit ffceq0 -- <each changed path>`. Never push.
  - Depends on: E-08, E-11, E-12, E-13
  - Expected outcome: every residual hit is listed with its reason; all runs pass; one path-scoped commit.
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- The `artifact_meta` interface names come from Order 02 (`tve77h`) and are used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` with typed filters (type, status, Set, order, `depends_on`, `latest_gate_review_of`, `path`) and an `incomplete` list, `artifact_meta.resolve(path_or_id6)`, `artifact_meta.read_at(id6, rev)` (Order 09 only), `artifact_meta.repair(id6, *, confirm=None)`, and the `artifacts.short_description` column. The legacy loader stores a multi-word `- Status:` raw value in a legacy-only column and sets `artifacts.status` only for a single token (tve77h OQ-03, which names this plan as the carrier of the reader decision).
- One status normalizer already exists: `plans.normalize_status` maps `EXECUTED`/`DONE` to `executed` and any other unrecognized token to `plans.LEGACY_GROUP` (`legacy/unknown`); `plans.read_status` applies it to the FIRST token of the whole-file `- Status:` line. `attention._plans_record` and `ipd_lint.lint_text` (M105) already use it.
- `selectors.metadata_region` is the shared region bound (the bullet block before the first `##`, or the YAML fence). The PARITY CONSTRAINT comment above `selectors._STATUS_RE` records the 24-plan disagreement and forbids changing it without "owning that contract change", which D-1 does here.
- Shared history rules: `attention_contract.history_block`, `attention_contract.newest_history_record`, `attention_contract.last_history_at`.
- `aw find` for plans uses `plans_index.plan_entry` and `plans_index.query` for display rows and `selectors.resolve` (through `cli._resolve_selectors_with_kinds`) for selector hits; `aw ipd board` is `cli._run_plans` over `plans.scan`.
- New CLI leaves are declared in `command_surface` (`CommandDeclaration`) and covered by `tests/conformance_matrix.py`. Order 03 (`1ajqaa`) creates `agent_workflows/meta_cli.py` for `aw show --history`, so this plan adds `check meta` and `meta repair` to that module.
- Traversal exclusions live in `layout.TRAVERSAL_EXCLUSIONS` (consumed by `selectors`); `_SKIP_NAMES` is defined separately in `check_engine`, `selectors` and `artifact_refs`.
- Core tier: modules set `pytestmark = pytest.mark.core`; the bare gate is `python3 -m pytest` (30 s budget).
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured 2026-11-02 at `0cbfcc706` (211 package modules under `agent_workflows/`).

| Id | Evidence | Finding |
|---|---|---|
| F-01 | Union of `rg -l` for (a) `^-` regex literals, (b) `- <Field>:` strings for 21 metadata fields, (c) `Workflow history`: 59 modules. Regex call sites starting `^-`: 200 (spec r5: 95 literals, a narrower count). `Workflow history` references: 28 modules (spec: 27) | Spec section 1 counts re-measured; the reader modules are split between this plan and Order 09 (F-02). |
| F-02 | Reader modules by owner (writers are Orders 06/07). THIS PLAN: `selectors` (7 regex sites), `cli` find/search/board paths (`_find_type_records`, `_find_prompt_id6`, `_find_prompt_setid`, `_run_search`, `_run_plans`), `attention` (10), `attention_contract` (history readers), `plans` (3), `check_engine` working-tree readers (30 sites in the module; its 12 `_blob_text` git call sites go to Order 09), `ipd_lint` (5), `ipd_schema.parse_metadata_block` (via its caller), `artifact_refs._SKIP_NAMES`. ORDER 09: `runner_shared` (20), `oc_runipd`, `agy_runipd`, the four hooks, `check_engine` git readers, `plan_readiness.review_staleness_index`, `ipd_lifecycle._release_own_plan_edit_before_landing`, `status_set._prepare_status_change` HEAD read, `plans_index` (6), `plans_archive` (5), `plans_refs` read side, `research_index` (2), `research_archive`, `prompts_index`, `artifact_audit` (1), `review_findings` (1), `review_sequence` (2), `review_tier`, `review_rereview`, `orchestrator_readiness` (1), `production_checks` (5), `work_cmd` (2), `artifact_adopt` (1), `ipd_set_plan`, `completion` | 9 reader modules here, 27 in Order 09; with the writer modules of Orders 06/07 they cover the 59. Comment-only mentions (`term`, `config`, `lifecycle_style`, `command_surface`, docstrings in `agy_runipd`) are not readers. |
| F-03 | `aw find plans executed` lists 1,610 paths; `aw find plans --status executed` lists 1,635. The 25 extra: 24 multi-word `- Status:` plans in `executed/` (`EXECUTED 2026-07-0x ...` 13, `DONE (...)` 7, `EXECUTED (approved ...)` 4) plus `vfa1tl`, whose single token is upper-case `EXECUTED` | The selector path (`selectors._read_status`, exact token) and the filter path (`plans_index.query`, status OR disposition) answer the same question differently. |
| F-04 | Python check over all tracked plans: `selectors._read_status` and `plans_index.plan_entry(...).status` disagree on exactly 24 plans; for all 24, `plans.normalize_status(<whole line>)` is `legacy/unknown`, `plans.read_status` (first token) is `executed`, and `aw attention` reports `native_status: executed` | Three answers exist: none (selectors), the prose line (plans_index), `executed` (plans, attention). D-1 picks one. |
| F-05 | `selectors._read_status` (strict `^- `, YAML fallback) and `selectors.read_front_matter_status` (loose `^-\s*`, no YAML) disagree on 157 records, ALL research files with YAML status. No tracked record uses `-  ` or `-\t` before a metadata field (0 matches) | The whitespace difference has no corpus effect; the YAML difference is real, and D-2 keeps each caller's answer. |
| F-06 | 4 records have a `- Status:` bullet only OUTSIDE the metadata region (3 reviews, 1 walkthrough quoting `- Status: approved <- unchanged`); `plans.read_status` (whole file) reads them, the region readers do not | No plan is affected (D-4). |
| F-07 | `aw attention --all --format json`: 3,096 items (plans 1,719, backlog 1,133, research 165, specs 48, prompts 30, releases 1), 1 violation, `valid: true` | Baseline for E-05. |
| F-08 | `history_block(` call sites: `attention` 6, `check_engine` 3; `last_history_at(` and `history_block(` together 10 sites in `attention` and `check_engine` | All history reads in this plan's modules go through `artifact_meta.history`. |
| F-09 | `_SKIP_NAMES = {"README.md", "INDEX.md", "STATUS.md"}` is defined identically in `check_engine`, `selectors` and `artifact_refs`; `layout.TRAVERSAL_EXCLUSIONS` holds 7 directory names | 4.4 asks for one list; E-08 places it in `layout`. |
| F-10 | No `aw check meta` and no `aw meta` command exist (`aw check --help` lists plans, specs, prompts, research, backlog, walkthroughs, roadmaps, comms, releases, all). Order 02 defers the `aw meta repair` CLI here; Orders 03, 04 and 05 defer `aw check meta` and the `short_description` display in `aw find`/`aw attention --details` here | E-10, E-11, E-03 and E-05 own them. |
| F-11 | `aw find plans zzzzzz` exits 2 today (4.4a `zyj8io`) | Pinned by E-01, re-checked after E-03. |
| F-12 | (written by E-14) residual `^-` and history hits in this plan's modules after the move, each with its exclusion reason | Input to Order 11's AC-1 audit. |

READER LEDGER: prior behavior, the test that pins it, and the result (section 7: "name the behavior that its moved consumers had and the test that checks it").

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `selectors._read_status`, `resolve` `MATCH_STATUS` | exact single token of the region `- Status:`; YAML `status:` for research; none for multi-word | E-01 module; `tests/test_selector_two_dialect_readers.py`; `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives` | D-1: canonical status from the cache; multi-word executed plans match `executed` |
| `selectors.read_front_matter_id`/`_status`/`_blocks_release` | loose `^-\s*` bullet only, region-bounded, no YAML | `tests/test_front_matter_loose_whitespace.py`, `tests/test_blocks_release_reader_bounding.py` | D-2: same answers |
| `selectors.declared_id6`, `id6_ownership` | whole-file id read for the ownership verdict | `tests/test_plans_rename_selectors.py`, E-01 | cached `id` |
| `plans_index.plan_entry` status in `aw find plans` JSON | whole prose line | `tests/test_find_single_read.py::test_d_status_disagreement_record_matches_and_preserves_plans_index_status` | D-1: canonical value (the printed row already shows the disposition first, `e.disposition or e.status`, so it does not change) |
| `plans.read_status`, `plans.scan` (`aw ipd board`, attention, M105) | first token of whole-file line, normalized | `tests/test_plan_status.py`, `tests/test_plans_board.py` | same normalized value from the cached raw status |
| `attention._plans_record` and siblings | per-tree reads, drift on missing/unknown status | E-04 module, `tests/test_attention.py`, `tests/test_attention_degraded_item.py` | same Items and drift |
| `attention._extract_detail` | Summary, Scope, Concern, Question, Title, H1 cascade | `tests/test_attention.py`, `tests/test_specs_releases_unsafe_field.py` | D-3 |
| `attention_contract.last_history_at` callers | newest history record date | `tests/test_history_consumers_shared_reader.py`, `tests/test_history_date_clock_readers.py` | same rule over `artifact_meta.history` |
| `check_engine` identity, status, Set, Item-Dependencies and From-* readers | region-bounded `^- ` bullets with mixed whitespace rules | E-06 module and its nine baseline modules | cached fields; identical rule ids on this checkout |
| `check_engine.build_graduation_reverse_index`, `graduation_cluster` | declarations and reverse links read separately | `tests/test_graduation_forward_links.py`, `tests/test_from_backlog_cardinality.py` | `lineage` and `graduation_targets` rows, still distinct (4.4a `pw2ln3`) |
| `check_engine.check_spec_review_attestation` | any parsing record naming the subject | `tests/test_spec_review_attestation.py` | unchanged here (the gate-only rule of 4.4 SR-601 is Order 06's deliberate change) |
| `ipd_lint.parse` metadata, `IPD-S405`, `M107`, `M112`, `M113`, `run_lint` rows | `ipd_schema.parse_metadata_block` slice; history lines parsed in `ipd_lint` | E-09 module, `tests/test_ipd_lint.py`, `tests/test_readiness_absence_invariant.py`, `tests/test_orchestrator_readiness.py` | same verdict per plan |
| `cli._find_prompt_id6`/`_find_prompt_setid` | `aw-prompt` comment first, then guarded filename slot | `tests/test_find_prompts_lane_status.py`, E-01 | cached `id`/`set` (the legacy loader applies the same order) |
| `cli._run_search._artifact_status` | loose `^-\s*Status:` over the whole file | `tests/test_cli_search.py` | cached status |

DECISIONS where readers disagreed (4.3: "record which behavior each consumer of the two disagreeing readers loses"):

- D-1 (status of the 24 multi-word plans; F-03, F-04). KEPT: the canonical normalized status that `aw attention`, `aw ipd board` and `ipd_lint` already report (`executed` for `EXECUTED ...` and `DONE ...`, `legacy/unknown` for any other unrecognized token). Both `aw find` paths match `plans.normalize_status` of the FIRST token of the cached raw value (the `plans.read_status` rule). WHAT EACH CONSUMER LOSES OR GAINS: `aw find plans executed` (selector path) GAINS the 24 plans plus `vfa1tl` and agrees with `--status executed` (1,635 rows); `aw find plans EXECUTED` stops matching `vfa1tl` by exact case (its only match today); the `aw find` JSON `status` of those 24 changes from the prose line to `executed` (the prose stays in the raw legacy column and in the file); the one test edit is the expected value in `tests/test_find_single_read.py::test_d...`. Reason: one reader, one answer (4.3), and it is the answer three surfaces already give. The migration (Order 04) normalizes these terminal records at the cutover.
- D-2 (whitespace and YAML; F-05). KEPT: each caller's current answer. The cache holds research YAML status, so `_read_status`/`MATCH_STATUS` keep matching research by it, while the public `read_front_matter_status` keeps returning None for a YAML-only record (Order 09's runner callers read plans, which use bullets). Loose bullet whitespace stays accepted because the legacy loader grammar accepts `^-[ \t]*` (0 corpus records depend on it).
- D-3 (detail text). KEPT: the `_extract_detail` cascade as the fallback; `short_description` wins when present (4.4 first bullet). In phase B no record has one, so output is unchanged until Order 13.
- D-4 (status bullet outside the metadata region; F-06). KEPT: region-bounded reading. The 4 records are 3 reviews and 1 walkthrough, which have no lifecycle status, so no plan-status consumer changes.

## Proposed changes (ordered, validatable)

1. Pin then move `selectors` and the `aw find`/`aw search`/`aw ipd board` paths, applying D-1 and D-2 (E-01 to E-03).
2. Pin then move `attention` and its history reads (E-04, E-05).
3. Pin then move the `check_engine` working-tree readers; unify the skip list (E-06 to E-08).
4. Pin then move `ipd_lint`; add `aw check meta` and `aw meta repair` (E-09 to E-11).
5. Cache parity (AC-1a), offline proof (AC-12), residual audit, docs, commit (E-12 to E-14).

## Deferred / out of scope (with reason)

- Readers of HEAD, staged or branch content (`check_engine._blob_text`/`_status_meta` git callers: `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `_staged_backlog_done_items`, `check_release_gate_consistency`), the hooks, the runners and `runner_shared`, `plan_readiness.review_staleness_index`, `ipd_lifecycle._release_own_plan_edit_before_landing`, `status_set._prepare_status_change`: they need `read_at` (4.4 list).
  - Carrier: t4gl15
- The `plans_index`, `plans_archive`, `plans_refs`, `research_*`, `prompts_index`, `artifact_audit`, `review_findings`, `review_*`, `orchestrator_readiness`, `production_checks`, `work_cmd`, `artifact_adopt`, `ipd_set_plan` and `completion` readers (section 7 step 5, second half).
  - Carrier: t4gl15
- The hook that refuses a non-append change to `meta/*.jsonl` (4.8 last bullet).
  - Carrier: t4gl15
- Deleting `selectors._STATUS_RE` and every other leftover parser and regex, the INDEX/STATUS code, and the AC-1 test.
  - Carrier: 9o83cr
- The `->reviewed` gate-only attestation change in `review_findings.review_attestation_missing` (4.4 SR-601) and the event-owned readiness/approval/coverage rules (AC-15).
  - Carrier: 2xwb9b
- Writing `short_description` (creating commands and the setter; AC-36 case 1).
  - Carrier: xexn45
- The post-cutover `last_history_at` from the newest event `at` with `last_history_precision` (4.4), the logged-path drift row of `aw check meta`, and AC-7 "zero findings on the migrated corpus".
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. `meta_cli.py`, `command_surface.py` and `tests/conformance_matrix.py` change only to add the two leaves this plan owns; `artifact_meta.py` changes only to add `artifact_meta.read_text` (OQ-03) and to fix an interface defect that a pinning test exposes, which the finalize scope reconciliation records.
- Under-scope: none known for the first half of F-02. Plan size: 14 E-items in 5 task groups (limits 18 and 5).

## Required tests / validation

New core test modules: `tests/test_readers_selectors_find.py`, `tests/test_readers_attention.py`, `tests/test_readers_check_engine.py`, `tests/test_readers_ipd_lint.py`, `tests/test_check_meta.py`, `tests/test_meta_repair_cli.py`, `tests/test_readers_cache_parity.py`, `tests/test_readers_offline.py`. All build `tmp_path` fixture repositories, call real functions or the `aw` CLI, assert on outputs and exit codes, and never read production source. The existing modules named in E-01, E-04, E-06 and E-09 run before and after each move.

Acceptance criteria of `4sd62s` this plan OWNS jointly with Order 09 (`t4gl15`), the phase-B reader pair. Each case has exactly one owner:

| AC | This plan's part | Order 09's part |
|---|---|---|
| AC-1a | `aw find`, `aw attention --format json`, `aw check meta`, `aw check all`, `aw ipd lint` across cold, warm, deleted and corrupt caches; external edit visible; invalid replacement reported (E-12) | the setter and the pre-commit gate cases |
| AC-7 | every 4.6 row the legacy format can express, one fixture per drift kind (E-10) | none; Order 13 shows zero findings on the migrated corpus |
| AC-9 (reader parts) | none of this plan's readers consults an INDEX file (checked in E-14) | the `plans_index`/`research_index`/`prompts_index` readers; deletion is Order 11 |
| AC-12 | `aw find` and `aw attention` with no model launcher and no network; `dependencies` unchanged (E-13) | the setter case |

CONTRIBUTES to: AC-8 (command-level form in E-12; owned by `tve77h`), AC-36 case 2 (`aw find` and `aw attention --details` read the column; finally shown by `cxxmyv`), AC-21 rows `wja06w`, `zyj8io`, `pw2ln3` (pasted runs; AC-21 is owned by `xexn45`), AC-1 (residual audit F-12; owned by `9o83cr`), AC-18 (`aw find` on a companion fixture in E-12; owned by `tve77h`).

Commands: the named modules, the bare core gate `python3 -m pytest`, `make test-all` (the phase-B thorough checkpoint belongs to Order 11, but this plan must not break it), `aw check`, `aw sanitize --agent`.

## Spec / documentation sync

No spec change; implements `4sd62s` 4.3 (one reader; the D-1 record), 4.4 (IPD-S405 through `history`, the shared exclusion list, the `_extract_detail` replacement), 4.6 (`aw check meta`), 4.7 and 4.8 (`aw meta repair`), and section 7 step 5 (first half). `docs/cli-output-contract.md` gains the two new leaves, and a `CHANGELOG.md` line records the D-1 matching change, because `aw find plans executed` returns more rows than before.

## Open questions

### OQ-01: Is the D-1 matching change acceptable before the cutover?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes, from repository evidence. The PARITY CONSTRAINT comment asks only that the change be owned, and 4.3 requires the plan to pick one behavior. D-1 makes the two `aw find` paths agree with `aw attention`, `aw ipd board` and `ipd_lint` (F-04), affects 25 records in `executed/`, removes no row from any listing, and is recorded in `CHANGELOG.md`. Recommendation strength: strong.

### OQ-02: Does the plan fit the size limits?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes: 14 E-items in 5 task groups. If execution finds E-07 (`check_engine`) too large for one pass, split it at the type boundary into plans/specs readers and backlog/release-gate/graduation readers; the plan stays within 18. Recommendation strength: medium.

### OQ-03: How does a reader get metadata for TEXT that is not a tracked working-tree file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `tve77h` defines `read`, `history`, `query`, `resolve` and `read_at` (revision blobs), but no entry point for an in-memory string, and today 58 test call sites plus `review_sequence` (before/after snapshots) and the public `selectors.read_front_matter_*(text)` readers pass text. This plan adds ONE additive function, `artifact_meta.read_text(text, *, record_type=None) -> State`, which runs the SAME loader that `read_at` feeds a blob to (tve77h E-14), writes no cache row, and returns the same `State` type. It is the only way to keep C5 (no parser outside `artifact_meta`) without a second grammar. After the cutover a text carries only `id` and `status`, so Order 13 (`cxxmyv`) must either switch each `read_text` caller to `read`/`read_at` or accept the mirror-only `State`; Order 11 (`9o83cr`) lists the remaining callers. Order 09 (`t4gl15`) uses this function, so it depends on this plan. Recommendation strength: medium; the coordinator may instead move `read_text` into `tve77h` before that plan executes.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste `git stash list` showing no stash and `git diff --stat agent_workflows/` empty (proving the code is unmodified), then `python3 -m pytest -o addopts="" -v tests/test_readers_selectors_find.py` with every test PASSED, including named tests for the multi-word `EXECUTED (approved ...)` fixture, loose-whitespace fixtures and the zero-match exit code 2; then the summary line of `python3 -m pytest -o addopts="" tests/test_find_filters.py tests/test_find_single_read.py tests/test_selector_two_dialect_readers.py tests/test_front_matter_loose_whitespace.py tests/test_selector_resolver_matrix.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste the empty output of `rg -n "re\.(compile|search|match)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/selectors.py`; the E-01 command and the five-module command re-run with the same pass counts; and `git diff tests/` showing that the only changed test assertions are the ones D-1 names.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `aw find plans executed | wc -l` and `aw find plans --status executed | wc -l` both printing 1635, the empty `diff` of their sorted path lists, `aw find plans zzzzzz; echo $?` printing 2, `aw ipd board --agent` summary row count equal to the pre-change value recorded in E-01, and `python3 -m pytest -o addopts="" -v tests/test_readers_selectors_find.py tests/test_find_prompts_lane_status.py tests/test_cli_search.py` all PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `git diff --stat agent_workflows/attention.py agent_workflows/attention_contract.py` empty, then `python3 -m pytest -o addopts="" -v tests/test_readers_attention.py` all PASSED with one test per tree, and the summary line of `python3 -m pytest -o addopts="" tests/test_attention.py tests/test_attention_contract.py tests/test_history_consumers_shared_reader.py tests/test_history_date_clock_readers.py tests/test_prompts_attention.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste the E-04 commands re-run with identical pass counts, and the output of a `python3 -c` snippet that loads `aw attention --all --format json` saved before (`/tmp/att_before.json`, captured during E-04) and after, sorts `(id, tree, native_status, last_history_at, detail_text)` tuples, and prints `items 3096 -> 3096, violations 1 -> 1, diff 0`.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff --stat agent_workflows/check_engine.py` empty, then `python3 -m pytest -o addopts="" -v tests/test_readers_check_engine.py` all PASSED (one test per reader listed in E-06), and the summary line of the nine named baseline modules; also save `aw check all --agent | python3 -c '...'` sorted rule-id counts to `/tmp/check_before.txt` and paste them.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the E-06 commands re-run with identical pass counts, and `aw check all --agent` sorted rule-id counts with `diff /tmp/check_before.txt -` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `rg -n "_SKIP_NAMES\s*=|RECORD_SCAN_SKIP_NAMES\s*=" agent_workflows` listing only `agent_workflows/layout.py`, and `python3 -m pytest -o addopts="" -v tests/test_readers_check_engine.py -k meta_dir` PASSED for the fixture with `.aw/records/meta/abc123.jsonl` and a `README.md`, asserting zero rows from `aw find`, `aw check` and `aw attention`.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the before/after per-plan verdict lists from `for f in .aw/records/plans/pending/*.ipd.md; do aw ipd lint "$f" | tail -1; done` with `diff` empty, and `python3 -m pytest -o addopts="" -v tests/test_readers_ipd_lint.py` all PASSED (one conforming and one refused fixture each for IPD-S405, IPD-M107, IPD-M112, IPD-M113 and M105), plus the summary line of `tests/test_ipd_lint.py tests/test_readiness_absence_invariant.py tests/test_orchestrator_readiness.py tests/test_plan_priority_required.py` before and after with equal counts.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_check_meta.py` all PASSED with one named test per drift kind (status mirror, id mirror, filename Set, NN, id6, date, D177 facet, research facet, disposition, review rounds, orphan log) and the clean fixture exiting 0; paste `aw check meta --agent` on this checkout ending with its `summary` record and a per-rule count; paste `aw check meta --help` showing the leaf exists.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the transcript of the synthetic-log fixture: `aw meta repair <id6>` preview text and exit 0 with `git status --porcelain` empty, `aw meta repair <id6> --apply` exit 0 with the mirror line changed in `git diff`, a second `--apply` with `git status --porcelain` unchanged; and the legacy-record run printing `nothing to repair (legacy format)`; plus `python3 -m pytest -o addopts="" -v tests/test_meta_repair_cli.py` all PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste `python3 -m pytest -o addopts="" -v --durations=0 tests/test_readers_cache_parity.py` with every test PASSED: one per (command x cache state) pair for the five commands and four cache states, the external-edit test, and the invalid-replacement test asserting the record is named in a violation; the module's total duration under 5 s.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_offline.py` all PASSED (three named tests, each asserting exit 0 with host binaries removed from `PATH` and sockets disabled), and `git diff 0cbfcc706 -- pyproject.toml` showing no change to the `dependencies` line.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste the two `rg` commands of E-14 and the F-12 table they produced (each residual hit with its exclusion reason); the bare `python3 -m pytest` summary line and wall time; the `make test-all` summary line; `aw check` rule counts equal to `/tmp/check_before.txt`; the `aw sanitize --agent` result record with zero `fail`; and the `aw commit ffceq0` output listing only Scope-Paths.
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h` and `xexn45` are executed. Scope fence: the paths in `- Scope-Paths:`; a needed file outside the fence is edited only with a justification recorded in the finalize scope reconciliation. Every reader move is pin-first: the E-01, E-04, E-06 and E-09 baselines run green on the unmodified code before the matching move, and a test edited after a move must be one that D-1 to D-4 name. Commit only through `aw commit ffceq0 -- <paths>`; never push. Run the named modules, `python3 -m pytest` (core gate) and `make test-all`, and paste the actual summary lines. Move the plan to `.aw/records/plans/executed/` only through `aw ipd finalize ffceq0`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
