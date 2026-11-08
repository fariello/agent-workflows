# IPD: Fold the value writers into artifact_meta, delete the writer adapters and record text readers, and move the borrowed grammars

- Date: 2026-11-08
- Kind: child
- Concern: Spec `4sd62s` C5 allows exactly one metadata reader and writer (`artifact_meta`). After phase B, four groups of metadata code still live outside it: the record and selector modules' public text readers (`selectors.read_front_matter_*`, `plans.read_status`, `prompts.read_metadata_*`, `specs._read_*`, `backlog.parse_item`), twelve pure value writers that rewrite one bullet line (`releases.set_*_line`, `backlog.set_*_line`, `research_cmd._set_priority_line`), four thin adapters that `xexn45` kept between a caller and `artifact_meta` (`xexn45` F-08), and seven grammars that `artifact_meta`'s legacy loader still borrows from other modules. Measured 2026-11-07 at `ac76110f4`: `rg -n "def set_[a-z_]+_line|def _in_metadata_region|def _set_priority_line" agent_workflows` prints 12 definitions in 3 files with 18 production call sites; 10 test modules call them; the adapters have 16 lines in 4 files and 13 lines in 4 test modules; the seven grammars have 7 definitions and 102 production references, of which 85 sit in modules a phase-B reader plan already moves and 17 remain; the text readers have 170 references, of which 56 remain (F-25). Part 3 of the split of `9o83cr` (Order 11).
- Scope: `9o83cr` E-08 (value writers), E-09 (adapters), E-10 (borrowed grammars) and E-11 (record text readers), carried verbatim with their original ids, E-11's symbol list SPLIT into two items by module family (E-11 for the selectors, plans, prompts and attention readers; E-18 for the spec and backlog item readers; together they equal the original list), plus a baseline item E-01 and a finishing item E-17 new to this part. EXCLUDES: every other parser and regex literal (`9o83cr` E-12, Orders 45 and 46); the INDEX and STATUS code (Orders 41 and 42); switching `write_legacy` off and removing the folded value writers again at the cutover (`cxxmyv`).
- Scope-Paths: agent_workflows/artifact_meta.py, agent_workflows/releases.py, agent_workflows/backlog.py, agent_workflows/research_cmd.py, agent_workflows/status_set.py, agent_workflows/plans_refs.py, agent_workflows/artifact_rename.py, agent_workflows/prompts.py, agent_workflows/runner_shared.py, agent_workflows/ipd_schema.py, agent_workflows/ipd_lint.py, agent_workflows/research_contract.py, agent_workflows/prompts_index.py, agent_workflows/attention_contract.py, agent_workflows/research_index.py, agent_workflows/specs.py, agent_workflows/plan_readiness.py, agent_workflows/set_records.py, agent_workflows/record_history.py, agent_workflows/ipd_lifecycle.py, agent_workflows/cli.py, agent_workflows/selectors.py, agent_workflows/attention.py, agent_workflows/artifact_adopt.py, agent_workflows/hooks/backlog_blocking_close_gate.py, tests/test_releases_line_writers.py, tests/test_releases_sibling_line_writers_bounding.py, tests/test_blocks_release_reader_bounding.py, tests/test_backlog_metadata_duplicate_and_gate_summary.py, tests/test_research_priority.py, tests/test_from_backlog_cardinality.py, tests/test_check_engine_from_spec_missing.py, tests/test_check_engine_spec_criteria.py, tests/test_backlog_handoff_close.py, tests/test_research_descriptive_safety.py, tests/test_plans_order_grammar.py, tests/test_spec_id6_filenames.py, tests/test_prompts_set_surface.py, tests/test_records_only_lane_rederive.py, tests/test_backlog.py, tests/test_artifact_meta_legacy.py, tests/test_ipd_schema.py, tests/test_attention_contract.py, tests/test_history_block_bounding.py, agent_workflows/plans.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/orchestrator_readiness.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/check_engine.py, agent_workflows/production_checks.py, tools/gate_drop_audit.py, tests/test_runner_shared.py, tests/test_plan_status.py, tests/test_prompts_new.py, tests/test_backlog_duplicate_guard.py, tests/test_specs_status_dirs.py, tests/test_gate_drop_audit.py, .aw/records/plans/pending/20261108-metastore-43-k6jd6l-fold-the-value-writers-into-artifact-meta-delete-the-writer.ipd.md
- Item-Dependencies: executed:1ajqaa, executed:59aiyh, executed:dcerjg, executed:ffceq0, executed:g5hpbb, executed:t4gl15
- Status: to-review
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 43
- Highest E allocated: 18
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: k6jd6l

> Write and proofread this plan per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history

- 2026-11-07 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): split from 9o83cr per maintainer step-complexity rule (no single E/V item hides hundreds of steps).

## Goal

Every bullet-line value writer and every grammar the legacy loader needs lives privately inside `artifact_meta`, and no adapter stands between a caller and `artifact_meta`, and no record or selector module defines a metadata text reader, so the regex literals deleted by Orders 45 and 46 have nothing left to serve; `aw find`, `aw attention` and `aw check` give the same results as before.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

Item ids E-08, E-09, E-10 and E-11 are the ids these items had in `9o83cr`; they are kept so cross-references in sibling plans (for example `cxxmyv` "the value writers that `9o83cr` E-08 folded") still point at the right item. E-18 is the second half of E-11's symbol list; E-01 and E-17 are new to this part. "F-20" in the carried text means this plan's F-24 (the residual reference list measured at the split, re-derived by E-01); `9o83cr` E-01 writes the final F-20 after all parts.

PIN RULE for every deletion or retarget (carried from `9o83cr`): before the edit, save the named test modules' per-test outcome list (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/9o83cr/<E>-before.txt`); after it, run the same command into `<E>-after.txt`. A retargeted test keeps every input case, so the after-list may rename a test but not drop a case; the evidence pastes both lists and maps each removed name to its successor.

### Task group 1: baseline

- [ ] E-01 Before any edit, re-derive F-24: run `rg -n "def set_[a-z_]+_line|def _in_metadata_region|def _set_priority_line|set_[a-z_]+_line\(|_set_priority_line\(" agent_workflows tools`, `rg -n "_set_metadata\b|_update_frontmatter_metadata|_update_or_inject_set_metadata|render_metadata_comment|rederive_front_matter" agent_workflows tools tests` and `rg -n "parse_metadata_block|parse_frontmatter\b|_parse_metadata_comment|history_block\b|last_history_at\b|newest_history_record\b|SPEC_STATUS_RE" agent_workflows tools`, and record in F-24 every hit that is not a comment, with the E-item that owns it. A hit in a module whose phase-B reader plan has already moved it to `artifact_meta` is listed as `moved`; a hit that is still a live caller is owned by E-08, E-09 or E-10. Re-derive F-25 the same way for each symbol of E-11 and E-18. Save the bare core gate summary line to `.aw/state/k6jd6l/core-before.txt`, and to `.aw/state/k6jd6l/before/` the stdout of `aw find plans --agent`, `aw attention --format json` and the rule-id multiset of `aw check all --all --agent` (`jq -r '.diagnostics[].rule' | sort | uniq -c`).
  - Depends on: none
  - Expected outcome: F-24 and F-25 list every live caller with an owner and the baselines are saved.
  - Execution state: pending

### Task group 2: value writers and thin adapters

- [ ] E-08 Fold the pure value writers into `artifact_meta`'s phase-B legacy writer (`write_legacy`, `xexn45`): move `releases.set_blocks_release_line`, `set_priority_line`, `set_work_kind_line`, `set_from_backlog_line`, `set_from_spec_line`, `set_item_dependencies_line`, `set_graduated_to_line`, `releases._in_metadata_region`, `backlog.set_release_exempt_kind_line`, `set_release_exempt_ref_line`, `set_close_evidence_line` and `research_cmd._set_priority_line` into private `artifact_meta` functions with unchanged behavior, delete the originals, and change any remaining caller (`status_set`, `backlog`, `research_cmd`, comments in `hooks/backlog_blocking_close_gate`, `attention`, `ipd_schema`) to `artifact_meta.append`. Pin first: save each named test module's outcome list to `.aw/state/9o83cr/E-08-before.txt` with the deterministic command of the PIN rule above. Retarget the tests that call the originals (`tests/test_releases_line_writers.py`, `tests/test_releases_sibling_line_writers_bounding.py`, `tests/test_blocks_release_reader_bounding.py`, `tests/test_backlog_metadata_duplicate_and_gate_summary.py`, `tests/test_research_priority.py`, `tests/test_from_backlog_cardinality.py`, `tests/test_check_engine_from_spec_missing.py`, `tests/test_check_engine_spec_criteria.py`, `tests/test_backlog_handoff_close.py`, `tests/test_research_descriptive_safety.py`) to drive `artifact_meta.append(..., dry_run=True)` or the setter CLI and assert on the rendered text, keeping every input case. Measured units at `ac76110f4`: 12 definitions in 3 files; 18 production call sites (`releases` 7 internal `_in_metadata_region` calls, `status_set` 4, `backlog` 5, `research_cmd` 1, `artifact_meta` 1); 3 comment sites; 10 test modules: about 25 edit sites once the internal `_in_metadata_region` calls move with their functions.
  - Depends on: E-01
  - Expected outcome: `rg -n "def set_[a-z_]+_line|def _in_metadata_region|def _set_priority_line" agent_workflows` lists only `artifact_meta.py`; the retargeted tests pass with the same number of cases as before.
  - Execution state: pending

- [ ] E-09 Delete the thin adapters kept by `xexn45` F-08: `plans_refs._set_metadata`, `artifact_rename._update_frontmatter_metadata` (and `_update_or_inject_set_metadata` if E-01 shows it is also an adapter), `prompts.render_metadata_comment` and `runner_shared.rederive_front_matter`; their one production caller each (`plans_refs.apply_renames`, `artifact_rename.run_rename_generic`, `prompts.run_new`, `runner_shared.apply_records_only_rederivation`) calls `artifact_meta` directly. Retarget `tests/test_plans_order_grammar.py`, `tests/test_spec_id6_filenames.py`, `tests/test_prompts_set_surface.py`, `tests/test_records_only_lane_rederive.py` and `tests/test_backlog.py` to the behavior through `aw group plans`, `aw rename specs --to-id6`, `aw prompts new` and `runner_shared.apply_records_only_rederivation`, asserting on the resulting `artifact_meta.read` state and file bytes. Measured units: 4 (or 5) definitions and 4 callers in 4 files; 5 test modules with 13 references: about 14.
  - Depends on: E-08
  - Expected outcome: `rg -n "_set_metadata\b|_update_frontmatter_metadata|render_metadata_comment|rederive_front_matter" agent_workflows tests` prints nothing; the retargeted tests pass, including the batch-refusal-before-write case of `tests/test_plans_order_grammar.py`.
  - Execution state: pending

### Task group 3: borrowed grammars

- [ ] E-10 Move into `artifact_meta` (private, unchanged behavior) every grammar its legacy loader or legacy writer still borrows, and delete the originals: `ipd_schema.parse_metadata_block` (the E/V checklist and section grammar of `ipd_schema` stays, N3), `research_contract.parse_frontmatter`, `prompts_index._parse_metadata_comment`, `attention_contract.history_block`, `last_history_at`, `newest_history_record` and `SPEC_STATUS_RE`. Non-loader callers (`ipd_lint.parse`, the research contract checks, `research_index`, `specs`, `backlog`, and the measured `attention_contract` importers `plan_readiness`, `set_records`, `record_history`, `ipd_lifecycle` and `status_set`, whichever F-20 still lists) read through `artifact_meta.read`, `history`, `read_text` or `read_at`. The migration (`dcerjg` E-09, `m0001_convert`) computes `last_history_day` with `newest_history_record`: it must call the moved private function inside `artifact_meta` (or a public `artifact_meta` wrapper), and `tests/test_m0001_conversion.py` and `tests/test_m0001_roundtrip.py` must pass unchanged. Keep `ipd_schema.parse_item_dependencies`, which parses a VALUE, not a block (`tve77h` conventions). Measured units at `ac76110f4`: 7 definitions in 4 modules; 102 production references, of which 85 are in modules that a phase-B reader plan (Orders 27 to 36) already lists and so should be `moved` by now, leaving 17 live references at the split (F-24: `SPEC_STATUS_RE` in `attention_contract`, `research_index` and `specs` (4), `_parse_metadata_comment` in `cli` (3), `last_history_at` in `plan_readiness` and `runner_shared` (3), `parse_frontmatter` in `artifact_adopt`, `attention`, `releases`, `research_contract` and `selectors` (7)); 4 test modules (`tests/test_artifact_meta_legacy.py`, `tests/test_ipd_schema.py`, `tests/test_attention_contract.py`, `tests/test_history_block_bounding.py`) that import a moved name: about 28. If E-01 finds more than 25 live references, record the excess rows in F-24 as `delete (follow-on)` and report them rather than overrunning (as `9o83cr` OQ-03 prescribed).
  - Depends on: E-09
  - Expected outcome: `rg -n "def (parse_metadata_block|parse_frontmatter|_parse_metadata_comment|history_block|last_history_at|newest_history_record)\b|SPEC_STATUS_RE\s*=" agent_workflows` lists only `artifact_meta.py`; `tests/test_artifact_meta_legacy.py` and `tests/test_ipd_lint*.py` pass.
  - Execution state: pending

### Task group 4: record text readers

- [ ] E-11 (`9o83cr` E-11, subset 1: selectors, plans, prompts and attention readers) Delete the text readers of the record and selector modules: `selectors._ID_RE`, `_STATUS_RE`, `_SET_RE`, `read_front_matter_id`, `read_front_matter_status`, `read_front_matter_blocks_release` and `metadata_region` (their remaining callers, including `hooks/executed_transition_gate`, use `artifact_meta.read`, `read_text` or `read_at`); `plans._STATUS_RE`, `_SET_RE`, `_ORDER_RE` and `plans.read_status`; `prompts._METADATA_STATUS_RE`, `read_metadata_id6` and `read_metadata_status`; `attention._frontmatter_block`. The public `selectors.read_front_matter_*` callers that remain after `ffceq0` and `t4gl15` include the `oc_runipd`/`agy_runipd` `_read_id` re-exports pinned by `tests/test_runner_shared.py::CrossHostReadIdReExportTests` (loose `-  `/`-\t` spelling); rebind the re-export to `artifact_meta.read_text`'s loose `id` value (`ffceq0` D-2, `t4gl15` D-4) so that test passes unchanged. Measured live references at the split (F-25): `metadata_region` in `hooks/executed_transition_gate` (2) and `orchestrator_readiness` (1), the `oc_runipd`/`agy_runipd` re-exports, `prompts.read_metadata_id6`/`read_metadata_status`/`_METADATA_STATUS_RE` in `artifact_rename`, `attention` (2), `cli` (2), `prompts` (3) and `status_set` (2), plus the 15 definitions themselves and 2 test modules (`tests/test_plan_status.py`, `tests/test_prompts_new.py`): about 25.
  - Depends on: E-10
  - Expected outcome: none of the subset-1 symbols is defined or referenced in `agent_workflows` (`rg -n` with the symbol list prints nothing); `aw find` and `aw attention --format json` match the E-01 baseline.
  - Execution state: pending

- [ ] E-18 (`9o83cr` E-11, subset 2: spec and backlog item readers) Delete `specs._read_status`, `_read_gate`, `_read_blocks_release`, `_read_priority`, `_read_work_kind`, `_read_scope` and `_read_summary`, and the metadata part of `backlog.parse_item`; their remaining callers use `artifact_meta.read`, `read_text` or `read_at`. Measured live references at the split (F-25): the `specs` readers in `specs` itself (13 internal calls), `attention` (4), `check_engine` (3: `_specs._read_gate` twice, `_specs._read_status`), and `runner_shared` and `tools/gate_drop_audit.py` through `check_engine._read_blocks_release` (4, owned by Order 45 if that symbol is still the caller); `backlog.parse_item` in `backlog` (9), `attention` (1), `set_records` (2 calls) and `tools/gate_drop_audit.py` (1); test modules `tests/test_backlog.py`, `tests/test_backlog_duplicate_guard.py`, `tests/test_specs_status_dirs.py`, `tests/test_gate_drop_audit.py`: about 27 call sites, many of them one-line swaps inside `specs` and `backlog`. Retarget `tools/gate_drop_audit.py`'s `backlog.parse_item` call to `artifact_meta.read`/`read_at`, keeping `tests/test_gate_drop_audit.py` green.
  - Depends on: E-11
  - Expected outcome: none of the subset-2 symbols is defined or referenced in `agent_workflows` or `tools` as a metadata reader (`backlog.parse_item` may survive only as a body parser with no metadata field); `aw find`, `aw attention --format json` and `aw check --agent` match the E-01 baseline.
  - Execution state: pending

### Task group 5: finish

- [ ] E-17 Finish: run every test module named in E-08 to E-11 and E-18 (including `tests/test_runner_shared.py -k CrossHostReadIdReExport` unchanged), the bare core gate `python3 -m pytest` (compare with `.aw/state/k6jd6l/core-before.txt`), `aw check all --agent`, `aw ipd lint` on this plan, and `aw sanitize --agent`; commit through `aw commit k6jd6l -- <paths>` with only Scope-Paths files, one commit per task group allowed, never `git add -A`, a bare `git add` or `git commit -a`; never push.
  - Depends on: E-18
  - Expected outcome: all runs pass; every commit's `git show --stat` lists only Scope-Paths files (or paths justified at finalize).
  - Execution state: pending

## Project conventions discovered (Step 0)

- The `artifact_meta` interface (names from `tve77h`, `ffceq0`, `xexn45`): `read(id6) -> State`, `query(...)`, `history(id6)`, `resolve(path_or_id6)`, `read_at(id6, rev)`, `read_text(text, *, record_type=None) -> State`, `create(...)`, `append(id6, events, *, expect_seq)` with `dry_run`, the phase-B legacy writer (`append_legacy`, `render_legacy`, `LegacyRender`, `LegacyTarget`), and the legacy loader (`load_legacy_artifact`, `load_legacy_review`, `_parse_bullet_metadata`, `_parse_yaml_front_matter`).
- `artifact_meta.append_legacy` already calls `backlog.set_close_evidence_line` (one of the E-08 call sites), which is why the fold target is the legacy writer.
- Test data comes from ONE builder, `tests/record_builder.py` (`59aiyh`).
- `selectors.read_front_matter_id` and `read_front_matter_status` are the loose-spelling readers (`^-\s*Id:`), and `oc_runipd`/`agy_runipd` re-export them as `_read_id`; `tests/test_runner_shared.py::CrossHostReadIdReExportTests` pins that behavior.
- `backlog.parse_item` returns a `BacklogItem` with metadata fields and body sections; its body parsing (N3) may stay, its metadata fields come from `artifact_meta`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (advisory `IPD-C801`).

## Findings

Measured 2026-11-07 at `ac76110f4`. F-08 and F-09 are copied from `9o83cr`.

| Id | Evidence | Finding |
|---|---|---|
| F-08 | Value writers: 7 `releases.set_*_line`, 3 `backlog` (`set_release_exempt_kind_line`, `set_release_exempt_ref_line`, `set_close_evidence_line`), `research_cmd._set_priority_line`; callers re-measured: `status_set` 4, `backlog` 5, `research_cmd` 1, `artifact_meta` 1, plus 7 internal `releases._in_metadata_region` calls. | E-08. |
| F-09 | `xexn45` F-08 adapters: `plans_refs._set_metadata` (caller `apply_renames`), `artifact_rename._update_frontmatter_metadata` (caller `run_rename_generic`), `prompts.render_metadata_comment` (caller `run_new`), `runner_shared.rederive_front_matter` (caller `apply_records_only_rederivation`); 16 production lines in 4 files, 13 test lines in 4 files. | E-09. |
| F-24 | Borrowed-grammar references, `rg` of the seven names over `agent_workflows` and `tools`, comments excluded: 102 total, 85 in a module that a phase-B reader plan names in Scope-Paths, 17 not (listed in E-10). Re-derived by E-01. | E-10 is bounded by what phase B leaves; E-01 re-measures. |
| F-25 | `rg -n "\b<symbol>\b" agent_workflows tools`, comments excluded, at `ac76110f4`, classed by whether the file is in a phase-B reader plan's Scope-Paths (Orders 27 to 36): `selectors` readers 63 references, 9 left; `plans`/`prompts`/`attention` readers 19, 12 left; `specs._read_*` 51, 20 left; `backlog.parse_item` 37, 15 left. Re-derived by E-01. | E-11 owns subset 1, E-18 subset 2; each about 25 units at the split. |

## Proposed changes (ordered, validatable)

1. Re-derive F-24 and save the core baseline (E-01).
2. Fold value writers (E-08), then delete adapters (E-09).
3. Move the borrowed grammars (E-10).
4. Delete the record text readers: subset 1 (E-11), then subset 2 (E-18).
5. Validate and commit (E-17).

## Deferred / out of scope (with reason)

- The `check_engine`, runner, setter and release parsers and regex literals of `9o83cr` E-12.
  - Carrier: e8420v
- The remaining module regex literals of `9o83cr` E-12.
  - Carrier: 0xsx2n
- Switching `write_legacy` off and removing the value writers this plan folds into it: they need the log format.
  - Carrier: cxxmyv
- Moving the legacy loader, with the grammars E-10 moves into it, from `artifact_meta` into `migrations/m0001_metadata_v2.py`.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none.
- Under-scope: none known; E-01 catches residue. Size: 7 E-items; 59 Scope-Paths entries, most of them modules that lose one to four references (see the size assessment); the largest items (E-10, E-18) hide about 28 units at the split.

## Required tests / validation

Retargeted modules: those named in E-08, E-09, E-10, E-11 and E-18, plus `tests/test_m0001_conversion.py`, `tests/test_m0001_roundtrip.py` and `tests/test_ipd_lint*.py`, which must pass unchanged. Commands: `python3 -m pytest` (core gate), `aw check all --agent`, `aw find plans --agent`, `aw attention --format json`, `aw check all --all --agent`, `aw sanitize --agent`. CONTRIBUTES to AC-1 (owned by `9o83cr`).

## Spec / documentation sync

No spec change; implements part of `4sd62s` 4.3 and section 7 step 7.

## Open questions

### OQ-01: Must every module that imports a moved grammar be edited here?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No. Orders 27 to 36 move the readers of 85 of the 102 measured references onto `artifact_meta` before this plan runs (each lists the module in its Scope-Paths); this plan edits only the references E-01 finds still live, and the Scope-Paths list every module that could hold one, so a stale entry is acknowledged with `--scope-ack` at finalize. Recommendation strength: strong.

### OQ-02: Does `backlog.parse_item` disappear entirely?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `9o83cr` E-11 deletes only "the metadata part of `backlog.parse_item`". Body sections are Markdown prose that N3 keeps, so a body-only parser may survive under the same or a narrower name; the executor decides by whether any caller still needs body sections, and records the choice in F-25. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition), as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction, name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: paste the `rg` commands with their hit counts, F-24 and F-25 as written with an owner on every live row, `.aw/state/k6jd6l/core-before.txt` and `ls -l .aw/state/k6jd6l/before/`.
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
  - Required evidence: paste `rg -n "def (parse_metadata_block|parse_frontmatter|_parse_metadata_comment|history_block|last_history_at|newest_history_record)\b|SPEC_STATUS_RE\s*=" agent_workflows` listing only `artifact_meta.py`; `rg -n "def parse_item_dependencies" agent_workflows/ipd_schema.py` still one hit; and the summary lines of `python3 -m pytest -o addopts="" tests/test_artifact_meta_legacy.py tests/test_ipd_lint*.py tests/test_research_contract*.py tests/test_m0001_conversion.py tests/test_m0001_roundtrip.py tests/test_ipd_schema.py tests/test_attention_contract.py tests/test_history_block_bounding.py` passing.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste the empty output of `rg -n` over `agent_workflows` for the subset-1 symbol list (`read_front_matter_(id|status|blocks_release)|metadata_region|plans\.read_status|read_metadata_(id6|status)|_METADATA_STATUS_RE|_frontmatter_block`, and `^_(ID|STATUS|SET|ORDER)_RE =` in `selectors.py`/`plans.py`), `python3 -m pytest -o addopts="" -v tests/test_runner_shared.py -k CrossHostReadIdReExport` PASSED unchanged, and `diff` of `aw find plans --agent` and `aw attention --format json` against the E-01 baselines, each empty.
  - Observed evidence:
  - Result: pending

- [ ] V-18 validates E-18
  - Required evidence: paste the empty output of `rg -n "specs\._read_|_specs\._read_|def _read_(status|gate|blocks_release|priority|work_kind|scope|summary)\b" agent_workflows/specs.py agent_workflows/attention.py agent_workflows/check_engine.py`, `rg -n "parse_item\(" agent_workflows tools` showing only body-parser uses (or nothing), the PIN-rule before/after lists for `tests/test_backlog.py`, `tests/test_backlog_duplicate_guard.py`, `tests/test_specs_status_dirs.py` and `tests/test_gate_drop_audit.py` with every removed name mapped, and `diff` of `aw find plans --agent`, `aw attention --format json` and the `aw check all --all --agent` rule multiset against E-01, each empty.
  - Observed evidence:
  - Result: pending

- [ ] V-17 validates E-17
  - Required evidence: paste the bare `python3 -m pytest` summary line beside `.aw/state/k6jd6l/core-before.txt`, `aw check all --agent` rule multiset, `aw sanitize --agent` with zero `fail`, and `git show --stat` of every `aw commit k6jd6l` commit listing only Scope-Paths files.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: exception
- Cohesion rationale: 7 E-items and 59 Scope-Paths entries against guides of about 6 and 12. The step bound holds (each E-item at about 25 units). Seven items: the Order budget of this split did not allow a separate plan for the two reader items, and E-01 is a short baseline; the five work items share one concern (no metadata writer, reader or borrowed grammar outside `artifact_meta`) and each is verified separately. The path count is a ceiling, not a work list: E-10's grammars are imported by 25 production modules, but phase-B reader plans move 85 of the 102 references first, so the executor edits only the about 17 that E-01 finds live; the rest are declared so a live reference found at execution needs no scope justification. The three items share one concern (no metadata writer or grammar outside `artifact_meta`) and E-10 depends on E-08's fold target.

Execute only after human approval (`Status: approved`) and after every plan in `- Item-Dependencies:` is executed. Every deletion is pin-first (PIN RULE above). Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Honesty rule: paste the ACTUAL summary lines; never claim a result you did not run. Commits: only through `aw commit k6jd6l -- <paths>`; never push. Lifecycle: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence.
