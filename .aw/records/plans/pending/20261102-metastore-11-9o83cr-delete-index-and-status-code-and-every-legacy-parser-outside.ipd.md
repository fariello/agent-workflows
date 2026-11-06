# IPD: Delete INDEX and STATUS code and every legacy parser outside artifact_meta

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader and writer (`artifact_meta`), 4.3 requires deleting every parser listed in section 1 plus the smaller helpers, and 4.5 says the SQLite cache REPLACES the `INDEX.{json,md}` files, `plans/STATUS.md` and `artifact_audit._INDEX_CACHE`, with `aw index plans|research|prompts` kept only as informational aliases of `aw index rebuild` and `check.stale-index-*` deleted. Phases A and B (Orders 02 to 10) move every caller onto `artifact_meta` but deliberately leave the old code in place (handoffs from `1ajqaa`, `dcerjg`, `2xwb9b`, `xexn45`, `ffceq0`, `t4gl15`, `59aiyh`). Measured 2026-11-02 at `0cbfcc706`: `stale-index` occurs 36 times in 7 modules; 31 package modules name `INDEX.json`, `INDEX.md` or `STATUS.md`; three `run_index` functions write INDEX files and 11 production call sites regenerate them; 200 `^-` metadata regex call sites remain in 35 files; and at least 25 named parser or helper symbols outside `artifact_meta` exist (F-06). Until they are deleted, C5 is not met and AC-1 and AC-9 cannot pass.
- Scope: Phase B, section 7 step 7 of `4sd62s`. (1) Make `aw index plans|research|prompts|all` and `aw research index` informational aliases of `aw index rebuild` (`meta_cli.index_rebuild`); delete the INDEX writers, every automatic INDEX regeneration call, the INDEX `--check` freshness classes and the `check.stale-index-missing`/`check.stale-index-stale` rules with their doctor remediation, while keeping every non-INDEX drift rule that `check_drift` hosts today. (2) Delete the STATUS code (`plans.render_status_index` and the dead `write_index` branch of `cli._run_plans`) and `artifact_audit._INDEX_CACHE`. (3) Fold the `releases.set_*_line`, `backlog.set_*_line` and `research_cmd._set_priority_line` value writers into `artifact_meta`; delete the thin adapters kept by `xexn45` F-08; delete every legacy metadata parser and regular expression outside `artifact_meta` that phase B left, moving any grammar the legacy loader still borrows into `artifact_meta`. (4) Add the AC-1 behavioral test and the AC-1 audit. EXCLUDES: anything that needs the log format or the migrated tree (cutover, `cxxmyv`), and document rewrites for log-based commands (`90iqr1`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/meta_cli.py, agent_workflows/plans_index.py, agent_workflows/research_index.py, agent_workflows/prompts_index.py, agent_workflows/plans.py, agent_workflows/cli.py, agent_workflows/artifact_types.py, agent_workflows/command_surface.py, agent_workflows/record_producers.py, agent_workflows/artifact_core.py, agent_workflows/check_engine.py, agent_workflows/doctor.py, agent_workflows/ipd_lifecycle.py, agent_workflows/status_set.py, agent_workflows/artifact_rename.py, agent_workflows/research_cmd.py, agent_workflows/research_refs.py, agent_workflows/plans_refs.py, agent_workflows/artifact_adopt.py, agent_workflows/artifact_audit.py, agent_workflows/selectors.py, agent_workflows/releases.py, agent_workflows/backlog.py, agent_workflows/specs.py, agent_workflows/prompts.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/research_contract.py, agent_workflows/attention.py, agent_workflows/attention_contract.py, agent_workflows/plan_readiness.py, agent_workflows/review_findings.py, agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/orchestrator_readiness.py, agent_workflows/production_checks.py, agent_workflows/research_archive.py, agent_workflows/review_sequence.py, agent_workflows/set_records.py, agent_workflows/lane_containment.py, agent_workflows/record_history.py, tools/gate_drop_audit.py, tests/test_*.py, tests/conformance_matrix.py, tests/support.py, docs/cli-output-contract.md, docs/cli-agent-protocol.md, README.md, CONTRIBUTING.md, CHANGELOG.md, .aw/records/plans/README.md, .aw/records/research/README.md, .aw/system/workflows/templates/agents-docs-research-README.md, .aw/records/plans/pending/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.ipd.md
- Item-Dependencies: executed:ffceq0, executed:t4gl15, executed:59aiyh, executed:1ajqaa, executed:dcerjg
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 11
- Highest E allocated: 16
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: 9o83cr
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261102-metastore-11-9o83cr-delete-index-and-status-code-and-every-legacy-parser-outside.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Leave `artifact_meta` as the only code that reads or writes artifact metadata, and leave the SQLite cache as the only metadata index, by deleting the INDEX and STATUS code, the stale-index rules and every legacy parser, writer helper and adapter that phase B kept alive, then prove it with the AC-1 behavioral test and audit.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

PIN RULE for every deletion or retarget: before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/9o83cr/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor. A count measured at authoring (F-01 to F-11) is context, never the bar.

### Task group 1: baseline and residual audit

- [ ] E-01 Record the baseline and the residual inventory: save to the gitignored `.aw/state/9o83cr/before/` (never `/tmp`, which a lane integration discards) the stdout and exit code of `aw index plans --agent`, `aw index research --check --agent`, `aw check plans --all --agent`, `aw check research --all --agent`, `aw check prompts --all --agent`, `aw find plans --agent`, `aw attention --format json`, `aw doctor --agent`, `aw ipd board` (as `board.txt`) and `aw check all --agent` and `aw check all --all --agent` (rule-id multisets, `jq -r '.diagnostics[].rule' | sort | uniq -c`), plus the core gate summary line of `python3 -m pytest`. `--all` matters: `check_engine.check_content` reaches `plans_index.check_drift` and `research_index.check_drift` only when `include_retired` is set, so without it the INDEX rules and the F-04 content rules never appear (measured at review: `aw check all --agent` has 0 `check.stale-index-*` findings and `aw check all --all --agent` has 2). Re-run the four AC-1 searches of E-14 and `rg -n "INDEX\.(json|md)|STATUS\.md|stale-index|_INDEX_CACHE|run_index|check_drift" agent_workflows`, merge in the residual tables F-12 of `ffceq0`, F-04 of `t4gl15` and F-09 of `xexn45`, and write table F-20 in this plan: one row per hit, classed `delete (E-nn)`, `body prose (N3)`, `comms (N4)`, `user prose (90iqr1)` or `cutover (cxxmyv)`. Any hit not in F-06 gets a row and an owning E-item. Also search `tools/` for callers of every symbol this plan deletes (measured at review: `tools/gate_drop_audit.py` calls `check_engine._status_meta` and `backlog.parse_item`, pinned by `tests/test_gate_drop_audit.py`), and give each a row; a `tools/` caller is retargeted in the E-item that deletes its symbol.
  - Depends on: none
  - Expected outcome: the saved outputs and a core gate summary exist under `.aw/state/9o83cr/before/`; F-20 exists with no unclassed row and covers `agent_workflows` and `tools`.
  - Execution state: pending

### Task group 2: INDEX and STATUS code (AC-9)

- [ ] E-02 Convert the typed index spellings into informational aliases (4.5): `aw index plans`, `aw index research`, `aw index prompts`, `aw index all` and the legacy `aw research index` call `meta_cli.index_rebuild` and print one information line ("`aw index <type>` is an alias of `aw index rebuild`; INDEX files are no longer generated"), as an `info` diagnostic in `--agent`/`--json` output and on stderr for humans. `--limit` is accepted and ignored with the same information line. `--check` runs the surviving content drift rules of that type (OQ-01) and exits as `aw check <type> --all` would (the `--all` path is the one that reaches `check_drift`, F-04). For prompts, the surviving rules are `prompts_index.check_drift`'s `name-metadata-mismatch` (today reached only through `aw index prompts --check`, not through `check_engine.check_content`); E-02 also wires `prompts_index.check_drift` into the prompts branch of `check_engine.check_content`, so the rule keeps a home once `run_index` loses its write path. Point the three `artifact_types.TYPE_BACKENDS` `index` entries at one alias function, register it in `command_surface`, and update the `cli.py` help strings that say "Regenerate INDEX.json + INDEX.md". New test module `tests/test_index_aliases.py` (core, built with `tests/record_builder.py`).
  - Depends on: E-01
  - Expected outcome: each spelling exits 0, prints the information line, creates no `INDEX.*` file and leaves `git status --porcelain` unchanged; `--check` on a fixture with a dangling plan citation exits nonzero naming `dangling-citation`.
  - Execution state: pending

- [ ] E-03 Delete the INDEX writers and their result helpers: `build_index_json`, `build_index_md`, `_set_last_touched` and the write path of `run_index` in `plans_index`, `research_index` and `prompts_index`; `DEFAULT_INDEX_LIMIT`; `artifact_core.emit_index_write_result` and `emit_index_check_result`; the `plans_index` and `research_index` (and any prompts) entries in `record_producers`. Keep `scan_*`, `query`, `run_find` and the non-INDEX drift classes of each `check_drift` (F-04), which `check_engine.check_content` still reaches. Delete or retarget the tests that assert INDEX bytes (`tests/test_plans_index.py`, `tests/test_research_index.py`, `tests/test_prompts_index.py`, `tests/test_index_write_agent_records.py`, `tests/test_index_check_agent_records.py`), keeping every assertion about `aw find` results and non-INDEX drift findings. `prompts_index` has no `run_find` (it has `scan_prompts` and `check_drift`); keep those.
  - Depends on: E-02
  - Expected outcome: `rg -n "build_index_(json|md)|emit_index_(write|check)_result|DEFAULT_INDEX_LIMIT" agent_workflows` prints nothing; `aw check plans --all --agent`, `aw check research --all --agent` and `aw check prompts --all --agent` report the same non-INDEX rule multiset as the E-01 baseline.
  - Execution state: pending

- [ ] E-04 Delete every automatic INDEX regeneration call (F-03): `ipd_lifecycle._refresh_plans_index_fail_loud` and its call in `ipd_lifecycle._finalize_transaction` (AC-26 freshness replaces it), `status_set._auto_index_types` and its two calls, the `run_index` calls in `artifact_rename.run_rename_generic` (four sites), `research_cmd` (two sites), `research_refs` (including the "manifest was not regenerated" notes), `plans_refs.apply_renames` and `artifact_adopt._default_refresh_index`. Each affected command's result loses only its INDEX-refresh line; pin each command's other output in the touched tests first.
  - Depends on: E-03
  - Expected outcome: `rg -n "run_index\(|_auto_index_types|_refresh_plans_index_fail_loud|_default_refresh_index" agent_workflows` prints nothing; a finalize, a rename, a group, an adopt and a research set-outcome on fixtures create no `INDEX.*` file and their next `aw find` shows the change.
  - Execution state: pending

- [ ] E-05 Delete the stale-index rules: the `check.stale-index-missing` and `check.stale-index-stale` entries of `check_engine.RULE_REGISTRY`, the code in the three `check_drift` functions that emits them, the `"stale-index" in rule` remediation branch of `doctor.build_remediation`, the priority-4 stale-index case of `doctor.resolve_next_actions` and the other `stale-index` substring sites in `doctor`, and the `stale-index` comments in `check_engine` and `ipd_lifecycle` that describe the deleted rules. Update `tests/test_drift_rule_registration.py`, `tests/test_doctor.py` and `tests/test_nv_backend_args_climb.py` to the new rule set.
  - Depends on: E-03
  - Expected outcome: `rg -n "stale-index" agent_workflows` lists only the `.aw/.gitignore` template comment in `engine.py` (cutover, F-20); `aw doctor --agent` on a fresh clone fixture with no INDEX files reports no index finding. Deleting the registry entry and the emitters together matters: an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC` (severity `error`).
  - Execution state: pending

- [ ] E-06 Delete the STATUS code: `plans.render_status_index` and the unreachable `write_index` branch of `cli._run_plans` (no parser defines `--write-index`, F-02). Retarget `tests/test_plans_board.py` and `tests/test_support_section.py` from `render_status_index` to the observable `aw ipd board` output.
  - Depends on: E-01
  - Expected outcome: `rg -n "render_status_index|write_index" agent_workflows` prints only `run_cli.write_index` (the run ledger, unrelated); `aw ipd board` output is byte-identical to the E-01 baseline.
  - Execution state: pending

- [ ] E-07 Delete `artifact_audit._INDEX_CACHE` and `_INDEX_CACHE_MAX` (4.5: the cache replaces it): `artifact_audit.build_index` answers from `artifact_meta.query`/`resolve` on every call. Delete `tests/test_artifact_audit_cache_eviction.py` (it tests the removed LRU) and retarget the freshness assertions of `tests/test_artifact_audit_index_cache.py` and `tests/test_artifact_audit_identity_staleness.py` to the behavior: a record added, deleted or moved after a first `build_index` call is reflected by the second call.
  - Depends on: E-01
  - Expected outcome: `rg -n "_INDEX_CACHE" agent_workflows tests` prints nothing; the retargeted tests pass.
  - Execution state: pending

### Task group 3: value writers and thin adapters

- [ ] E-08 Fold the pure value writers into `artifact_meta`'s phase-B legacy writer (`write_legacy`, `xexn45`): move `releases.set_blocks_release_line`, `set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_from_spec_line`, `set_item_dependencies_line`, `set_graduated_to_line`, `releases._in_metadata_region`, `backlog.set_release_exempt_kind_line`, `set_release_exempt_ref_line`, `set_close_evidence_line` and `research_cmd._set_priority_line` into private `artifact_meta` functions with unchanged behavior, delete the originals, and change any remaining caller (`status_set`, `backlog`, `research_cmd`, comments in `hooks/backlog_blocking_close_gate`, `attention`, `ipd_schema`) to `artifact_meta.append`. Pin first: save each named test module's outcome list to `.aw/state/9o83cr/E-08-before.txt` with the deterministic command of the PIN rule below. Retarget the tests that call the originals (`tests/test_releases_line_writers.py`, `tests/test_releases_sibling_line_writers_bounding.py`, `tests/test_blocks_release_reader_bounding.py`, `tests/test_backlog_metadata_duplicate_and_gate_summary.py`, `tests/test_research_priority.py`, `tests/test_from_backlog_cardinality.py`, `tests/test_check_engine_from_spec_missing.py`, `tests/test_check_engine_spec_criteria.py`, `tests/test_backlog_handoff_close.py`, `tests/test_research_descriptive_safety.py`) to drive `artifact_meta.append(..., dry_run=True)` or the setter CLI and assert on the rendered text, keeping every input case.
  - Depends on: E-01
  - Expected outcome: `rg -n "def set_[a-z_]+_line|def _in_metadata_region|def _set_priority_line" agent_workflows` lists only `artifact_meta.py`; the retargeted tests pass with the same number of cases as before.
  - Execution state: pending

- [ ] E-09 Delete the thin adapters kept by `xexn45` F-08: `plans_refs._set_metadata`, `artifact_rename._update_frontmatter_metadata` (and `_update_or_inject_set_metadata` if E-01 shows it is also an adapter), `prompts.render_metadata_comment` and `runner_shared.rederive_front_matter`; their one production caller each (`plans_refs.apply_renames`, `artifact_rename.run_rename_generic`, `prompts.run_new`, `runner_shared.apply_records_only_rederivation`) calls `artifact_meta` directly. Retarget `tests/test_plans_order_grammar.py`, `tests/test_spec_id6_filenames.py`, `tests/test_prompts_set_surface.py`, `tests/test_records_only_lane_rederive.py` and `tests/test_backlog.py` to the behavior through `aw group plans`, `aw rename specs --to-id6`, `aw prompts new` and `runner_shared.apply_records_only_rederivation`, asserting on the resulting `artifact_meta.read` state and file bytes.
  - Depends on: E-08
  - Expected outcome: `rg -n "_set_metadata\b|_update_frontmatter_metadata|render_metadata_comment|rederive_front_matter" agent_workflows tests` prints nothing; the retargeted tests pass, including the batch-refusal-before-write case of `tests/test_plans_order_grammar.py`.
  - Execution state: pending

### Task group 4: legacy parsers (AC-1)

- [ ] E-10 Move into `artifact_meta` (private, unchanged behavior) every grammar its legacy loader or legacy writer still borrows, and delete the originals: `ipd_schema.parse_metadata_block` (the E/V checklist and section grammar of `ipd_schema` stays, N3), `research_contract.parse_frontmatter`, `prompts_index._parse_metadata_comment`, `attention_contract.history_block`, `last_history_at`, `newest_history_record` and `SPEC_STATUS_RE`. Non-loader callers (`ipd_lint.parse`, the research contract checks, `research_index`, `specs`, `backlog`, and the measured `attention_contract` importers `plan_readiness`, `set_records`, `record_history`, `ipd_lifecycle` and `status_set`, whichever F-20 still lists) read through `artifact_meta.read`, `history`, `read_text` or `read_at`. The migration (`dcerjg` E-09, `m0001_convert`) computes `last_history_day` with `newest_history_record`: it must call the moved private function inside `artifact_meta` (or a public `artifact_meta` wrapper), and `tests/test_m0001_conversion.py` and `tests/test_m0001_roundtrip.py` must pass unchanged. Keep `ipd_schema.parse_item_dependencies`, which parses a VALUE, not a block (`tve77h` conventions).
  - Depends on: E-09
  - Expected outcome: `rg -n "def (parse_metadata_block|parse_frontmatter|_parse_metadata_comment|history_block|last_history_at|newest_history_record)\b|SPEC_STATUS_RE\s*=" agent_workflows` lists only `artifact_meta.py`; `tests/test_artifact_meta_legacy.py` and `tests/test_ipd_lint*.py` pass.
  - Execution state: pending

- [ ] E-11 Delete the text readers of the record and selector modules: `selectors._ID_RE`, `_STATUS_RE`, `_SET_RE`, `read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release` and `metadata_region` (their remaining callers, including `hooks/executed_transition_gate`, use `artifact_meta.read`, `read_text` or `read_at`); `plans._STATUS_RE`, `_SET_RE`, `_ORDER_RE` and `plans.read_status`; `prompts._METADATA_STATUS_RE`, `read_metadata_id6` and `read_metadata_status`; `attention._frontmatter_block`; `specs._read_status`, `_read_gate`, `_read_blocks_release`, `_read_priority`, `_read_work_kind`, `_read_scope` and `_read_summary`; the metadata part of `backlog.parse_item`. The public `selectors.read_front_matter_*` callers that remain after `ffceq0` and `t4gl15` include the `oc_runipd`/`agy_runipd` `_read_id` re-exports pinned by `tests/test_runner_shared.py::CrossHostReadIdReExportTests` (loose `-  `/`-\t` spelling); rebind the re-export to `artifact_meta.read_text`'s loose `id` value (`ffceq0` D-2, `t4gl15` D-4) so that test passes unchanged.
  - Depends on: E-10
  - Expected outcome: none of the named symbols is defined or referenced in `agent_workflows` (`rg -n` with the symbol list prints nothing); `aw find`, `aw attention --format json` and `aw check --agent` match the E-01 baseline.
  - Execution state: pending

- [ ] E-12 Delete the remaining parsers and regular expressions classed `delete` in F-20, at least: `check_engine._blob_text`, `_status_meta` and `_metadata_status`; `runner_shared._front_matter_bullets` and its re-exports in `oc_runipd`/`agy_runipd`; `review_findings._META_RE` (the round and finding grammar stays, N3); `plans_index._META_RE` and `plans_index._meta`; `status_set._STATUS_RE` and its `finditer` loop; `releases._STATUS_RE`; `plan_readiness._STATUS_RE`; `artifact_audit._STATUS_LINE_RE`; and every other `^-` metadata regex literal in F-20. Update code comments in the touched modules that cite a deleted symbol. Retarget `tools/gate_drop_audit.py` (`check_engine._status_meta`, `backlog.parse_item`) to `artifact_meta.read`/`read_at`, keeping `tests/test_gate_drop_audit.py` green.
  - Depends on: E-11
  - Expected outcome: every F-20 `delete` row is gone from the re-run E-01 searches; the named test modules of each touched module pass.
  - Execution state: pending

- [ ] E-13 Add `tests/test_metadata_single_owner.py` (core, records built with `tests/record_builder.py`) for AC-1 part (2), without reading any source: (a) monkeypatch `artifact_meta.read`, `query`, `history`, `resolve` and `read_at` to return one sentinel state for a built plan, then drive `aw find`, `aw attention --format json`, `aw show <id6> --format json`, `aw ipd lint`, `aw check plans --agent` and the `aw ipd-executed-gate` leaf on a staged fixture, and assert each output reflects the sentinel status, not the on-disk bullet; (b) monkeypatch `artifact_meta.append` and `create` to raise, then run `aw ipd set`, `aw backlog set`, `aw specs set`, `aw group plans` and `aw prompts new`, and assert each exits nonzero and every record file is byte-identical afterwards; (c) with no patch, the same setters change the state that `artifact_meta.read` returns.
  - Depends on: E-12
  - Expected outcome: a passing core module whose assertions are on CLI exit codes, stdout and file bytes.
  - Execution state: pending

- [ ] E-14 Run the AC-1 part (1) audit and record it as table F-21: `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows`, `rg -n "Workflow history" agent_workflows`, `rg -n "aw-prompt|aw-managed-prompt" agent_workflows` and `rg -n "records/meta" agent_workflows`, each piped through ONE listed exclusion pattern file `.aw/state/9o83cr/ac1-exclusions.txt` (also pasted in full into F-21, so the evidence survives the lane) that names every excluded pattern (N3 body prose: OQ-row fields such as `Carrier`, `Carrier-Evidence`, `Carrier-Declined`, `Blocking`, and `plan_readiness._OQ_FIELD_RE`/`_OQ_HEADING_RE`; E/V checklist fields; N4 `comms`; user-facing help or managed-block text rewritten by `90iqr1`; code that the cutover moves into `m0001`). F-21 lists each surviving hit with its class; no hit outside `artifact_meta.py` and `migrations/m0001_*.py` may be a parser or writer. The phase-B legacy loader lives in `artifact_meta.py` (`tve77h` E-11), so its hits are expected there until `cxxmyv` moves it into `m0001`.
  - Depends on: E-13
  - Expected outcome: F-21 shows parser and writer hits only in `artifact_meta.py` and `migrations/m0001_*.py`; every other hit is covered by a listed exclusion.
  - Execution state: pending

### Task group 5: documents and finish

- [ ] E-15 Update the documents that describe INDEX generation as current behavior (they become wrong when E-02 and E-03 land, C10a): `docs/cli-output-contract.md` (the `--limit` hot-window sentence and the `index` step-cue example), `docs/cli-agent-protocol.md` (the `INDEX.md` hot-window sentence), `CONTRIBUTING.md` (the two manifest bullets), `README.md` (the research `INDEX.json`/`INDEX.md` mention), `.aw/records/plans/README.md` and `.aw/records/research/README.md` with its installed template `.aw/system/workflows/templates/agents-docs-research-README.md` (the INDEX paragraphs: replace with "`aw index rebuild` rebuilds the local cache; `aw index <type>` is an alias"), keeping `tests/test_installed_text_current.py` green; add one `CHANGELOG.md` `2.0.0 (pending)` line. Write no em or en dashes in this user-facing prose.
  - Depends on: E-03
  - Expected outcome: `rg -n "INDEX\.(json|md)|STATUS\.md" README.md CONTRIBUTING.md docs .aw/records/plans/README.md .aw/records/research/README.md .aw/system/workflows/templates/agents-docs-research-README.md` prints only lines that describe the removal; `tests/test_installed_text_current.py` passes.
  - Execution state: pending

- [ ] E-16 Finish: run every test module named in E-02 to E-15, the bare core gate `python3 -m pytest` (within its 30 s budget), `make test-all`, `aw check all --agent` and `aw check all --all --agent` (rule-id multisets equal the E-01 baselines minus the `check.stale-index-*` findings; any other difference traced to a record changed in between), `aw ipd lint --all` (no new diagnostic), `aw sanitize --agent`, and `pyproject.toml` `dependencies` unchanged; commit through `aw commit 9o83cr -- <paths>` with only Scope-Paths files, one commit per task group allowed, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-14, E-15
  - Expected outcome: all runs pass; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- Typed verbs route through `artifact_types.TYPE_BACKENDS` (`"index": "plans_index.run_index"`, `"research_index.run_index"`, `"prompts_index.run_index"`) and `artifact_types.resolve_backend`, dispatched by `cli._run_noun_verb`; `aw research index` has its own branch in `cli.py` (`if research_cmd == "index":`). `aw index rebuild` is added by `1ajqaa` as `meta_cli.index_rebuild(repo_root) -> CommandResult`, routed before type normalization.
- Drift findings are `artifact_core.Drift(location, rule, detail)`; exit codes come from `artifact_core.drift_exit_code`; severities come from `check_engine.RULE_REGISTRY` (`RuleSpec`), and an unregistered rule falls through to `check_engine._DEFAULT_RULESPEC` (severity `error`), so deleting a rule's emitter and its registry entry must happen together.
- `doctor.build_remediation` matches `"stale-index" in rule` by substring, and its comment states the five `doctor` sites must change together.
- `check_engine.check_content` calls `plans_index.check_drift` and `research_index.check_drift`, which host non-INDEX rules (`name-metadata-mismatch`, `dangling-citation`, `research_index.STALE_STATE_RULE` and six more), so those functions survive with their INDEX classes removed.
- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `query(...)`, `history(id6)`, `resolve(path_or_id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `create(...)`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B `write_legacy` renderer, and the legacy loader (`tve77h` E-11, E-12).
- Test data comes from ONE builder, `tests/record_builder.py` (`RecordBuilder(repo_root)`, `59aiyh`); new tests use it from the start. Core tests carry `pytestmark = pytest.mark.core` (for example `tests/test_plans_index.py`, `tests/test_research_index.py`); the root `conftest.py` selects them on a bare `python3 -m pytest`.
- Commits go through `aw commit <id6> -- <paths>`; plans move to `executed/` only through `aw ipd finalize`.

## Findings

Measured 2026-11-02 at `0cbfcc706` (before phase B; E-01 re-measures, because Orders 06 to 10 delete some of these).

| # | Evidence | Consequence |
|---|---|---|
| F-01 | `rg -c "stale-index" agent_workflows --type py`: 36 hits in 7 modules (`check_engine` 18, `doctor` 8, `ipd_lifecycle` 3, `plans_index`/`research_index`/`prompts_index` 2 each, `engine` 1). Registry: `"check.stale-index-missing": RuleSpec("info", ...)`, `"check.stale-index-stale": RuleSpec("warning", ...)`. | E-05 deletes all except the `engine.py` `.aw/.gitignore` template comment (cutover). |
| F-02 | 31 package modules name `INDEX.json`, `INDEX.md` or `STATUS.md`. Writers: `plans_index.run_index` (`json_path.write_text`, `md_path.write_text`), `research_index.run_index`, `prompts_index.run_index`, `artifact_core.emit_index_write_result`. `plans.render_status_index` is reached only from `cli._run_plans` `if getattr(args, "write_index", False)`, and no parser defines `--write-index` (`aw ipd board --help` lists no write option). Tracked `.aw/records/plans/STATUS.md` last changed 2026-08-17. | E-03, E-06. The rest are skip-name lists and ignore lines that protect against on-disk files; F-20 classes them `cutover`. |
| F-03 | `run_index` and refresh callers: `artifact_rename.run_rename_generic` (4), `status_set._auto_index_types` (2 calls), `research_cmd` (2), `research_refs` (1), `plans_refs.apply_renames` (1), `artifact_adopt._default_refresh_index`, `ipd_lifecycle._refresh_plans_index_fail_loud` (called from `_finalize_transaction`), `cli` research branch, `artifact_types.TYPE_BACKENDS` (3), `record_producers` (`plans_index`, `research_index` entries). | E-02, E-03, E-04. |
| F-04 | Non-INDEX drift rules inside `check_drift`: `plans_index` emits `name-metadata-mismatch` and `dangling-citation`; `research_index` emits `stale-state-to-promote`, `dangling-consumed-by`, `adopted-without-consumer`, `unrecognized-model`, `research.frontmatter-key-repeated`, `status-tier-mismatch`, `check.research-companion-orphaned`. | These are kept (E-03); E-02 `--check` reports them. |
| F-05 | No CI, Makefile or pre-commit file runs `aw index ... --check` (`rg "aw index\|index --check" .github Makefile .pre-commit-config.yaml .pre-commit-hooks.yaml`: no output). `aw index plans|research` appears 33 times in 10 package modules (help text, notes, managed block). | Alias behavior for `--check` is a compatibility choice, not a CI constraint (OQ-01). |
| F-06 | Section 1 parsers and helpers verified to exist by `rg -n "^def ..."`: `ipd_schema.parse_metadata_block`, `runner_shared._front_matter_bullets`, `status_set._STATUS_RE` (and its loop), `plan_readiness._OQ_FIELD_RE` (body prose, N3), `backlog.parse_item`, `specs._read_status`/`_read_gate`/`_read_blocks_release`/`_read_priority`/`_read_work_kind`/`_read_scope`/`_read_summary`, `research_contract.parse_frontmatter`, `comms.parse_envelope_header` (N4), `prompts.read_metadata_id6`/`read_metadata_status`/`_METADATA_STATUS_RE`, `prompts_index._parse_metadata_comment`, `review_findings._META_RE`, `attention_contract.history_block`/`last_history_at`/`newest_history_record`/`SPEC_STATUS_RE`, `selectors.read_front_matter_id`/`_status`/`_blocks_release`/`metadata_region`/`_ID_RE`/`_STATUS_RE`/`_SET_RE`, `check_engine._metadata_status`/`_blob_text`/`_status_meta`, `releases._in_metadata_region`/`_STATUS_RE`, `attention._frontmatter_block`, `plans._STATUS_RE`/`_SET_RE`/`_ORDER_RE`/`read_status`, `plans_index._META_RE`/`_meta`, `plan_readiness._STATUS_RE`, `artifact_audit._STATUS_LINE_RE`. | E-10 to E-12. `comms` and the OQ-row parser are excluded with a listed pattern (E-14). |
| F-07 | `rg` regex literals starting `^-`: 200 call sites in 35 files; `Workflow history` in 28 modules; `aw-prompt` in 6 modules (`artifact_rename`, `prompts`, `prompts_index`, `artifact_naming`, `check_engine`, `cli`); `records/meta`: none yet. | E-01 and E-14 re-measure after phase B. |
| F-08 | Value writers: 7 `releases.set_*_line`, 3 `backlog` (`set_release_exempt_kind_line`, `set_release_exempt_ref_line`, `set_close_evidence_line`), `research_cmd._set_priority_line`; callers today `status_set` (17 sites), `backlog` (5), `research_cmd` (1). `2xwb9b` reuses them inside `artifact_meta`'s legacy branch. | E-08 moves them into `artifact_meta`. |
| F-09 | `xexn45` F-08 adapters: `plans_refs._set_metadata` (caller `apply_renames`), `artifact_rename._update_frontmatter_metadata` (caller `run_rename_generic`), `prompts.render_metadata_comment` (caller `run_new`), `runner_shared.rederive_front_matter` (caller `apply_records_only_rederivation`); pinned by 5 test files. | E-09. |
| F-10 | `artifact_audit._INDEX_CACHE: OrderedDict` with `_INDEX_CACHE_MAX = 8` inside `artifact_audit.build_index`; tests `tests/test_artifact_audit_index_cache.py` (6 tests), `tests/test_artifact_audit_cache_eviction.py` (4), `tests/test_artifact_audit_identity_staleness.py`. No other Set plan deletes it (`rg _INDEX_CACHE` over the Set's plans: only spec text). | E-07. |
| F-11 | 45 test files reference a symbol this plan deletes (`rg -l` over `tests`). | Each is retargeted to behavior in the E-item that deletes the symbol. |
| F-12 | Documents describing INDEX generation: `README.md`, `CONTRIBUTING.md`, `docs/cli-agent-protocol.md`, `docs/cli-output-contract.md`, `.aw/records/plans/README.md`, `.aw/records/research/README.md` and its template; `tests/test_installed_text_current.py` checks the template text. | E-15. |
| F-20 | (written by E-01) residual hits after phase B with class and owner | Input to E-08 to E-12. |
| F-21 | (written by E-14) AC-1 audit with the exclusion list | AC-1 part (1) evidence. |

## Proposed changes (ordered, validatable)

1. Baseline and residual inventory F-20 (E-01).
2. Aliases, then delete INDEX writers, regeneration calls, stale-index rules, STATUS code and `_INDEX_CACHE` (E-02 to E-07).
3. Fold value writers into `artifact_meta`; delete the thin adapters (E-08, E-09).
4. Move borrowed grammars into `artifact_meta`; delete the text readers and every remaining parser; add the AC-1 test and audit (E-10 to E-14).
5. Update the INDEX documents; full validation and commit (E-15, E-16).

## Deferred / out of scope (with reason)

- Deleting the on-disk `INDEX.*` files, this repository's tracked `plans/STATUS.md`, and the INDEX ignore lines in the `engine.py` `.aw/.gitignore` template, the `engine.py` adder (`_ensure_aw_gitignore`) and `placement_switch.py`, plus the skip-name entries that protect scans from those files (`_SKIP_NAMES` and `layout.RECORD_SCAN_SKIP_NAMES` entries `INDEX.md`/`STATUS.md`, `artifact_refs._GENERATED_MANIFEST_NAMES`, `install_wizard._RECORDS_SCAFFOLD_NAMES`, `layout_migration._NON_DURABLE_BASENAMES`, `runner_shared.generated_manifest_paths` and its `lane_containment.inventory_lane` clause). These files exist in every unmigrated repository until `m0001` step 5 deletes them (5.2 CLEANUP, built by `dcerjg` E-11); removing the ignore lines or skip names first would surface stale INDEX files to `git status` and to record scans. AC-9's final `git ls-files` and `rg` proof therefore happens after the migration.
  - Carrier: cxxmyv
- Retiring `record_history.append`, `append_advisory`, `append_rename` and `records/history.jsonl` from the `engine.py` template, adder and `placement_switch.py` (AC-30 case 2, source half). Listed in the `9o83cr` handoff file but carried by `dcerjg`'s deferral to `cxxmyv`: the sidecar is still written in phase B.
  - Carrier: cxxmyv
- `rename` and path-bearing events, retiring the sidecar writer and the rename ledger (AC-31, AC-34 post-cutover form), switching `write_legacy` off, and removing the value writers that E-08 folds into `artifact_meta`'s legacy writer. They need the log format, which is legacy until the cutover.
  - Carrier: cxxmyv
- Moving the legacy loader (with the grammars E-10 moves into it) from `artifact_meta` into `migrations/m0001_metadata_v2.py`, which is what makes the strict AC-1 `rg` result hold; and re-running the E-14 audit on the cutover commit.
  - Carrier: cxxmyv
- The post-cutover rules of the hook that refuses a non-append change to `meta/*.jsonl` (4.8 last bullet). `t4gl15` adds the phase-B hook; its terminal-log rules apply only once logs exist.
  - Carrier: cxxmyv
- The WRITE halves of `runner_shared.rederive_front_matter`, `mark_plan_attended`, `record_oq_answer`, `perform_coordinator_proposal_file`, `review_sequence.restore_pre_s7_plan` and the remaining writers (appear in the `9o83cr` handoff file only as context; this plan deletes only the adapters those moves leave, E-09).
  - Carrier: xexn45
- Converting the legacy-format tests that must keep literal input (legacy loader tests of `tve77h`, migration round-trip and conversion tests of `dcerjg` and `ya4ee4`); this plan does not convert them.
  - Carrier: dcerjg
- Rewording the managed block in `engine.py`/`AGENTS.md` ("`aw index plans [--check]`/`aw find plans` for the manifest"), quickstarts and other text for log-based commands. The alias keeps that command working, so the text is dated rather than wrong until the cutover.
  - Carrier: 90iqr1

## Scope check

- Over-scope: none. The document edits (E-15) are limited to INDEX statements that become false when this plan lands (C10a); log-format documentation stays with `90iqr1`.
- Under-scope: none known; E-01 exists to catch residue that phase B left beyond F-06. Size: 16 E-items in 5 task groups (limits 18 and 5). If F-20 shows more than about 40 `delete` rows, split E-12 into a follow-on child (OQ-03).

## Required tests / validation

New test modules (core, built with `tests/record_builder.py`): `tests/test_index_aliases.py` (E-02), `tests/test_metadata_single_owner.py` (E-13). Retargeted modules: those named in E-03 to E-11. Commands: `python3 -m pytest` (core gate), `make test-all`, `aw check --agent`, `aw ipd lint --all`, `aw sanitize --agent`, and the `rg` audits of E-01 and E-14.

Acceptance criteria of `4sd62s` this plan OWNS:

| AC | This plan's part |
|---|---|
| AC-1 | part (2): the behavioral test (E-13); part (1): the `rg` audit with the listed exclusion patterns (E-14). Phase-B form; `cxxmyv` re-runs the audit after the legacy loader moves into `m0001`. |
| AC-9 | deletion of every INDEX and STATUS writer and the `check.stale-index-*` rules, so nothing creates the files again (E-02 to E-06), proved by a test that each former producer creates no `INDEX.*` (E-02, E-04). The final `git ls-files` and filesystem proof follows the migration's file deletion on the cutover commit (`cxxmyv`). |

CONTRIBUTES to: AC-26 (finalize, rename and adopt stop regenerating INDEX and rely on the freshness rule; owned by `tve77h`), AC-1a (the aliases and `artifact_audit.build_index` read through the cache; owned by `ffceq0`/`t4gl15`), AC-1b (the core-tier summary line for this merge; owned by `cxxmyv`).

## Spec / documentation sync

No spec change; implements `4sd62s` 4.3 (delete every section 1 parser and the regex literals), 4.5 (the cache replaces INDEX files, `STATUS.md` and `artifact_audit._INDEX_CACHE`; typed `aw index` spellings become aliases; `--check` INDEX drift and `check.stale-index-*` deleted) and section 7 step 7. Documentation: E-15 updates only the INDEX statements this change makes false; `CHANGELOG.md` gains one line.

## Open questions

### OQ-01: What does `aw index <type> --check` do once INDEX drift is gone?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: It runs the non-INDEX drift classes that the same `check_drift` reported before (F-04) and exits as `aw check <type>` would, after printing the alias information line. Reason: those classes were part of what `--check` gated, so silently passing would weaken a check a user may rely on, while refusing the flag would break scripts; no CI in this repository uses it (F-05). Recommendation strength: strong.

### OQ-02: Should `plans_index`, `research_index` and `prompts_index` be renamed once they write no index?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. They still host `aw find` backends (`run_find`, `query`) and the F-04 content rules; renaming is churn the spec does not ask for and would widen this plan's diff across 17 importing modules. Recommendation strength: strong.

### OQ-03: Is the plan too large?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: 16 E-items in 5 groups is within the limits. The size risk is E-12, whose list depends on what phase B left; if F-20 has more than about 40 `delete` rows, the executor finishes E-11, records the rest of E-12 as `delete (follow-on)` rows in F-20 and reports them for a follow-on child rather than overrunning (the gate states this). Recommendation strength: medium.

### OQ-05: Which plans must execute before this one?

- Blocking: no
- Status: resolved
- Owner: plan reviewer
- Resolution or deferral rationale: `ffceq0`, `t4gl15` and `59aiyh` as authored, plus `1ajqaa` (E-02 calls `meta_cli.index_rebuild`, which `1ajqaa` E-05 creates) and `dcerjg` (E-10 moves `attention_contract.newest_history_record`, which `dcerjg` E-09's `m0001_convert` calls, and E-14 audits `migrations/m0001_*.py`, which `dcerjg` creates). Neither is reached transitively: both depend only on `tve77h` (measured). Adding the two edges changes no order in practice, because both are Order 03 and 04 and run before Order 11, but it makes the runner refuse to dispatch this plan if either has not executed. Recommendation strength: strong.

### OQ-04: Can the strict AC-1 `rg` result (matches only in `artifact_meta.py` and `m0001`) hold before the cutover?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Not fully: user-facing help and managed-block text (`90iqr1`) and the legacy loader location (`cxxmyv`) change only at the cutover. AC-1 allows explicit exclusions; E-14 lists every one, and `cxxmyv` re-runs the audit when the loader moves into `m0001`. Recommendation strength: strong.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste `ls -l .aw/state/9o83cr/before/` showing the saved outputs with their exit codes (including both `aw check all` rule multisets), the core gate `N passed` summary line, and the F-20 table written into this plan with one row per hit of the E-01 searches and a non-empty class column on every row (`grep -c` of F-20 rows equal to the pasted search hit count minus duplicates), including the `tools/` rows.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_index_aliases.py` with every test PASSED (one per spelling: `aw index plans`, `research`, `prompts`, `all`, `aw research index`, plus `--limit` and `--check`), and a live run on this repository of `aw index plans --agent; echo rc=$?` showing the `info` alias diagnostic and `rc=0`, followed by `git status --porcelain --ignored .aw/records | grep INDEX` before and after with no new line, and `aw check prompts --all --agent` showing a planted `name-metadata-mismatch` prompt fixture reported through `check_engine.check_content` (the E-02 wiring). Code path: `artifact_types.resolve_backend` -> the alias function -> `meta_cli.index_rebuild` (E-02).
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste the empty output of `rg -n "build_index_(json|md)|emit_index_(write|check)_result|DEFAULT_INDEX_LIMIT" agent_workflows`; paste `aw check plans --all --agent`, `aw check research --all --agent` and `aw check prompts --all --agent` rule-id multisets (`jq -r '.diagnostics[].rule' | sort | uniq -c`) beside the E-01 baselines, equal except for the `check.stale-index-*` ids; and the summary lines of `python3 -m pytest -o addopts="" tests/test_plans_index.py tests/test_research_index.py tests/test_prompts_index.py tests/test_index_check_agent_records.py` (or the note that a module was deleted, with the `git diff --stat` line).
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste the empty output of `rg -n "run_index\(|_auto_index_types|_refresh_plans_index_fail_loud|_default_refresh_index" agent_workflows`, and `python3 -m pytest -o addopts="" -v tests/test_index_aliases.py -k producers` PASSED for the fixture test that runs `aw ipd finalize`, `aw rename plans`, `aw group plans`, `aw research set-outcome` and the adopt path, then asserts no `INDEX.*` exists and `aw find` shows the change.
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `rg -n "stale-index" agent_workflows` listing only the `engine.py` `.aw/.gitignore` template comment; the summary lines of `python3 -m pytest -o addopts="" tests/test_drift_rule_registration.py tests/test_doctor.py tests/test_nv_backend_args_climb.py` all passing; and `aw doctor --agent` run in a fresh `git clone` of this repository at the plan's commit, with no `index` diagnostic in its output.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `rg -n "render_status_index|write_index" agent_workflows` showing only `run_cli.write_index`; `diff <(aw ipd board) .aw/state/9o83cr/before/board.txt` empty (board saved in E-01); and the summary lines of `python3 -m pytest -o addopts="" tests/test_plans_board.py tests/test_support_section.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste the empty output of `rg -n "_INDEX_CACHE" agent_workflows tests`, the `git diff --stat` line deleting `tests/test_artifact_audit_cache_eviction.py`, and `python3 -m pytest -o addopts="" -v tests/test_artifact_audit_index_cache.py tests/test_artifact_audit_identity_staleness.py` with the add, delete and move freshness cases PASSED.
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `rg -n "def set_[a-z_]+_line|def _in_metadata_region|def _set_priority_line" agent_workflows` listing only `agent_workflows/artifact_meta.py`; and `diff .aw/state/9o83cr/E-08-before.txt .aw/state/9o83cr/E-08-after.txt` for the modules named in E-08, each removed test name mapped to its successor and no FAILED or ERROR line.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste the empty output of `rg -n "_set_metadata\b|_update_frontmatter_metadata|render_metadata_comment|rederive_front_matter" agent_workflows tests`; and `python3 -m pytest -o addopts="" -v tests/test_plans_order_grammar.py tests/test_spec_id6_filenames.py tests/test_prompts_set_surface.py tests/test_records_only_lane_rederive.py tests/test_backlog.py` with every test PASSED, including `set_metadata_raises_on_unmatchable_order_line` or its renamed successor.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `rg -n "def (parse_metadata_block|parse_frontmatter|_parse_metadata_comment|history_block|last_history_at|newest_history_record)\b|SPEC_STATUS_RE\s*=" agent_workflows` listing only `artifact_meta.py`; `rg -n "def parse_item_dependencies" agent_workflows/ipd_schema.py` still one hit; and the summary lines of `python3 -m pytest -o addopts="" tests/test_artifact_meta_legacy.py tests/test_ipd_lint*.py tests/test_research_contract*.py tests/test_m0001_conversion.py tests/test_m0001_roundtrip.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the empty output of `rg -n` over `agent_workflows` for the E-11 symbol list (`read_front_matter_(id|status|blocks_release)|metadata_region|plans\.read_status|read_metadata_(id6|status)|_METADATA_STATUS_RE|_frontmatter_block|specs\._read_`, and `^_(ID|STATUS|SET|ORDER)_RE =` in `selectors.py`/`plans.py`), `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py -k CrossHostReadIdReExport` PASSED unchanged, and `diff` of `aw find plans --agent`, `aw attention --format json` and the `aw check all --all --agent` rule multiset against the E-01 baselines, each empty or differing only by the `check.stale-index-*` ids.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste F-20 with each `delete` row marked done, and the re-run E-01 searches showing none of those rows; and the summary lines of the named test modules of every module touched (at least `tests/test_runner_shared.py`, `tests/test_review_findings_gate.py`, `tests/test_status_set*.py`, `tests/test_artifact_audit.py`, `tests/test_check_engine*.py`, `tests/test_gate_drop_audit.py`) passing, and `rg -n "_status_meta|parse_item\(" tools/` printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_metadata_single_owner.py` with every case PASSED (a: six read surfaces reflect the sentinel; b: five writers exit nonzero with byte-identical files; c: unpatched setters change `artifact_meta.read`), and `rg -n "inspect\.|import ast|getsource|read_text\(.*agent_workflows" tests/test_metadata_single_owner.py` empty (the test reads no source). Code path: each command's normal dispatch through `cli.main`.
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste the four `rg` commands with the exclusion file `.aw/state/9o83cr/ac1-exclusions.txt` printed in full (and copied into F-21), the surviving hit list, and F-21 written into this plan, where every row outside `artifact_meta.py` and `migrations/m0001_*.py` names an exclusion class and none is a parser or writer.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste the `git diff` hunks of each named document, the output of the E-15 `rg` command (only removal-describing lines), `python3 -m pytest -o addopts="" tests/test_installed_text_current.py` passing, and `grep -nP "[\x{2013}\x{2014}]"` over the changed user-facing lines printing nothing.
  - Observed evidence:
  - Result: pending

- [ ] V-16 validates E-16
  - Required evidence: paste the bare `python3 -m pytest` summary line with its wall time under 30 s, the `make test-all` summary line, the `aw check all --agent` and `aw check all --all --agent` rule multiset diffs against E-01 (only `check.stale-index-*` findings removed, any other difference traced), `aw ipd lint --all` with no new diagnostic, `aw sanitize --agent` result `pass`, `git diff 0cbfcc706 -- pyproject.toml` with no `dependencies` change, and `git show --stat` of every `aw commit 9o83cr` commit listing only Scope-Paths files (or paths justified at finalize).
  - Observed evidence:
  - Result: pending


## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `ffceq0`, `t4gl15`, `59aiyh`, `1ajqaa` and `dcerjg` are executed. Open questions: OQ-01 to OQ-05 are resolved and none is blocking. OQ-03's split is a recommendation to the maintainer, not a stop: if F-20 holds more than about 40 `delete` rows, finish E-11, record the remaining rows in F-20 as `delete (follow-on)`, and report them for a follow-on child.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every deletion is pin-first (PIN RULE above), and a retargeted test keeps every input case.

Honesty rule: run the named modules, `python3 -m pytest` (core gate) and `make test-all`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit 9o83cr -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize 9o83cr` itself.
