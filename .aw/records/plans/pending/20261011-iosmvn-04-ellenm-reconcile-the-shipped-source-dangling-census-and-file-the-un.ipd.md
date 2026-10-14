# IPD: Reconcile the shipped-source dangling census and file the unguarded behavioral claims

- Date: 2026-10-11
- Kind: child
- Concern: Orders 01 to 03 retire or repoint 87 residual `19313eed` dangling citations (41 + 19 + 27 at authoring HEAD `8538be828`). Two things no single child can do: (a) prove the WHOLE shipped-source population reached zero once all three have landed, and (b) give every RETIRE-UNGUARDED property (a behavioral guard deleted in `19313eed` that no live test replaces) a tracked carrier, so retiring the citation does not silently abandon the coverage gap. That second point is the backlog item's purpose: "ensure that no dangling test citations are silently abandoned."
- Scope: IN: (1) whole-population measurement over every tracked `agent_workflows/*.py` and `tools/*.py`; (2) cross-check of the three children's disposition tables against that measurement; (3) filing, with `aw backlog new`, one backlog item per cluster of RETIRE-UNGUARDED properties (grouped by deleted test file), each `Work-Kind: chore` unless the child recorded a user-perceptible defect, citing the child plan and site ids, unless an existing live item already owns the file (then record that owner instead). OUT: writing any test (each filed item's own work); editing production source; the sibling-owned clusters, whose own plans carry them.
- Scope-Paths: .aw/records/backlog/open/, .aw/records/plans/pending/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md
- Item-Dependencies: executed:yuhl6o, executed:9rthek, executed:ev7t1w
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: iosmvn
- Set: iosmvn
- Order: 4
- Highest E allocated: 03
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: ellenm
- Approval: 2026-10-13, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-13 approved (aw set): status set to approved
- 2026-10-13 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed.

- 2026-10-12 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.
- 2026-10-12 to-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): authored review-ready from backlog `iosmvn`.

## Goal

Close the rollup honestly: the shipped-source residual reaches zero, and every behavioral guard that the retirements expose as lost has a backlog carrier.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Reconcile

- [x] E-01 Run the Set measurement command over `$(git ls-files 'agent_workflows/*.py' 'tools/*.py')` at execution HEAD and record the output and HEAD sha. Expected residual: only the census fixture, `tools/lost_guard_census.py` `print_classifier`'s `mixed_example = "tests/test_dependency_verb.py"` (`ev7t1w` F-01, a census input). Any other line is either a site a child missed or a citation introduced after the child ran; record each with file, enclosing symbol, and which (check the child's E-01 list). This plan edits no source, so every such extra line becomes a RETIRE-UNGUARDED-equivalent entry in E-02's grouped list under a `RESIDUAL` group and gets a carrier in E-03.
  - Depends on: none
  - Expected outcome: the surviving set is exactly the F-01 census fixture (re-derived at execution; `UNRETIRED 1` is the expected shape, not the bar), or every extra line is listed, attributed, and carried into E-02 as `RESIDUAL`.
  - Execution state: performed

- [x] E-02 Cross-check: collect the appended disposition tables from executed plans `yuhl6o`, `9rthek`, `ev7t1w`; confirm each table's row count equals that child's own recorded E-01 `UNRETIRED N`, and that every row has a disposition in {REPOINT, RETIRE-PIN, RETIRE-UNGUARDED}. Produce the RETIRE-UNGUARDED list grouped by deleted test file (one group per basename; each group lists property, child id6, and site ids), plus the `RESIDUAL` group from E-01 if non-empty. Append it to this plan's Findings as a `Group | Deleted file | Property | Child / sites | Carrier` table with the Carrier column empty until E-03.
  - Depends on: E-01
  - Expected outcome: per-child row count equals that child's E-01 count; the grouped table is appended; any mismatch is listed by child and site.
  - Execution state: performed

### Task group 2: File carriers

- [x] E-03 First capture `aw check backlog --agent` (the pre-filing baseline; at review HEAD `cb23fb012` it reported 3 findings: 2 `check.name-nonconformant`, 1 `check.collisions-not-checked`). Then, for each E-02 group: (a) dedupe with `rg -lwF <basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending` (`aw find backlog` is NOT a text search: at review `aw find backlog test_lane_permission_posture` gave `no artifact matched`), and run the item's `aw backlog new ...` WITHOUT `--apply` to read its advisory duplicate report. OPEN each hit and judge whether it actually owns restoring that property (`owned-confirmed`) or merely mentions the file (`owned-rejected`); this Set's own plans and backlog `iosmvn` itself never count as owners. Known live owners at review: `mv18lz` (graduated, plan `df486j`) for `test_runner_item_dependencies.py::InRunExecutedDependencyTests`; `2ohbkj` (open) for `test_runner_stop_triggers.py` stop/audit shim routing; `yf1p8y` (graduated, plan `z2ugxc`) for `test_runner_backlog_close.py`. (b) If owned-confirmed, record the owner id6. Otherwise file one item with `aw backlog new --summary "Restore behavioral coverage of <property> lost with tests/<file>" --priority low --work-kind chore --body "<deleted file; property; child plan id6 and site ids; only behavioral outcomes may be restored, never a source-reading pin (P16)>" --apply`, letting the setid default to the item's own id6 (a singleton, as `2ohbkj`). File `--work-kind bug --blocks-release next` instead only when the child's disposition row recorded a user-perceptible defect, citing that row. (c) Write the owner or filed id6 into the E-02 table's Carrier column. Finally re-run `aw check backlog --agent`.
  - Depends on: E-02
  - Expected outcome: every E-02 group has a Carrier (filed id6 or owned-confirmed id6); the post-filing `aw check backlog` diagnostics equal the baseline set (no new rule id or location naming a newly filed item).
  - Execution state: performed

## Project conventions discovered (Step 0)

- SET MEASUREMENT COMMAND: verbatim as recorded in sibling plan `yuhl6o` (Order 01) Project conventions.
- Backlog items are created only through `aw backlog new` (managed block, "What needs attention"); `TODO.md` is not a work surface.
- A `bug` work-kind backlog item must carry `- Blocks-Release:` while live (AGENTS.md "Every live bug gates the next release"); the default here is `chore` because a lost test is a coverage gap, not a user-visible defect, unless the child recorded otherwise.
- Prior art for the same shape: executed `oyh28b` (census filing) and pending `xmr5qj` (uncitedaudit filing).
- `aw find backlog <selector>` matches id6, status, Set and filename only, not body text; body dedupe needs `rg` plus the advisory duplicate report that `aw backlog new` prints without `--apply` (F-03).
- `aw backlog new` writes under `.aw/records/backlog/open/` and does not commit; the executor commits the new files through `aw commit`.

## Findings

| ID | Evidence | Finding |
|---|---|---|
| F-01 | Set measurement at HEAD `8538be828` over all tracked `agent_workflows/*.py` and `tools/*.py`: `UNRETIRED 88` | 87 sites are split across Orders 01-03; the 88th is `tools/lost_guard_census.py` `print_classifier`'s `mixed_example`, a census fixture (`ev7t1w` F-01) that E-01 will show; it is the only expected survivor. Re-measured at review HEAD `cb23fb012` (after `yuhl6o` was integrated but before it executed): `UNRETIRED 88`, with the same per-file split (41 `runner_shared.py`, 19 across the six Order 02 files, 27 across the 17 Order 03 files, 1 `tools/lost_guard_census.py` `print_classifier` `mixed_example`). |
| F-02 | `python3 tools/lost_guard_census.py --dedupe` at HEAD `8538be828`: "SHIPPED-SOURCE SUBSET ... Unowned: 44" | The backlog's "46 unowned" has drifted to 44; this Set reaches every one of them plus owned-by-basename paths that no sibling plan actually edits (e.g. `test_lane_tool_identity.py`, owned only by this rollup's own text). Re-run at review HEAD `cb23fb012`: still `Unowned: 44`. Context only; nothing here is a bar. |
| F-03 | Review at `cb23fb012`: `aw find backlog test_lane_permission_posture` -> `no artifact matched selector`; `aw backlog new --summary "...InRunExecutedDependencyTests" --priority low --work-kind chore` (no `--apply`) -> `candidate duplicate(s) detected ... mv18lz [graduated]` | The original E-03 dedupe (`aw find backlog <basename>`) would have reported every group unowned. The advisory detector plus `rg -lwF` is the working dedupe. Known RETIRE-UNGUARDED candidate already identified at review: `9rthek` S-14 (`tests/test_lane_permission_posture.py`, agy `dangerously_skip_permissions` default); `rg -lwF test_lane_permission_posture` over live backlog finds no owner. |

### E-02 Grouped RETIRE-UNGUARDED Table

| Group | Deleted file | Property | Child / sites | Carrier |
|---|---|---|---|---|
| G-01 | `tests/test_artifact_core.py` | `SCAN_ROOTS` classification completeness in `classify_rel` (`ScanRootClassificationInvariantTests.test_no_scan_root_is_scanned_then_silently_dropped`) | `ev7t1w` S-02 | `sfdwaz` |
| G-02 | `tests/test_awcmdsurf_vocab_and_parsers.py` | `reviews` absence from `TYPE_BACKENDS` and `selectors.KNOWN_PRIMARY_TYPES` (`DerivedVocabularyTests.test_reviews_has_no_backend_and_no_status_lifecycle`) | `ev7t1w` S-04 | `nrcvpg` |
| G-03 | `tests/test_bug_gate_check.py` | Zero-finding direction in `check_release_gate_consistency` on ungated item with gated carrier (`test_the_mismatch_rule_fires_only_for_a_live_carrier`) | `ev7t1w` S-07 | `hybluq` |
| G-04 | `tests/test_ci_check_parity.py` | Findings parity between CI and local check runs on the same tree (`TestCiLocalParity.test_ci_and_local_identical_on_same_tree`) | `ev7t1w` S-06 | `crk6wb` |
| G-05 | `tests/test_dirty_base_gate.py` | `evaluate_clean_base` identical tracked scope (`clean` and `dirty_paths`) on shared and isolated paths (`test_the_tracked_scope_is_IDENTICAL_on_both_paths`) | `ev7t1w` S-16 | `x6trbp` |
| G-06 | `tests/test_durable_capture.py` | `lint_file` and `check_durable_carrier` shared `evaluate_durable_carrier` predicate (`test_one_predicate_backs_both_surfaces`) | `ev7t1w` S-09 | `8owahv` |
| G-07 | `tests/test_id6_global_mint.py` | `global_id6s` deliberate over-collection of quoted `Id` tokens (`PurityAndSubsetContractTests.test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate`) | `ev7t1w` S-01 | `s8eaay` |
| G-08 | `tests/test_interrupt_menu.py` | `oc_runipd.main` interrupt stderr preservation notice (`RunnerMainOutputOnInterruptTests`) | `9rthek` S-07 | `zgqs4e` |
| G-09 | `tests/test_lane_clean_base.py` | `evaluate_clean_base` non-refusal on untracked files (`test_case_3_an_untracked_file_does_NOT_refuse`) | `yuhl6o` S-09 | `dc80rp` |
| G-10 | `tests/test_lane_permission_posture.py` | `agy_runipd.build_parser` `dangerously_skip_permissions` default `True` (`TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser`) | `9rthek` S-14 | `m7o4ew` |
| G-11 | `tests/test_lane_tool_identity.py` | `driver_begin` subprocess environment baseline identity pin (`test_the_env_handed_to_the_begin_child_actually_carries_the_pin`) | `yuhl6o` S-26 | `o0gy5v` |
| G-12 | `tests/test_naming_authority_single_source.py` | `build_clustered_name` and `parse_clustered` round-trip identity (`RoundTripTests`) | `ev7t1w` S-03 | `09i7fy` |
| G-13 | `tests/test_orchestrator_deferral_reporting.py` | `RETIRE_REFUSED` to `ORCH_REASON` translation and unrecognized-reason fallback in `orchestrator_refusal_text` | `yuhl6o` S-10, S-11 | `dxe6w1` |
| G-14 | `tests/test_plan_status.py` | Repository plans recognized status token drift guard (`PlanStatusDriftGuard.test_every_plan_has_a_recognized_status`) | `ev7t1w` S-19 | `7h2he0` |
| G-15 | `tests/test_pwatch.py` | `pwatch` `--no-color` suppression on a real TTY (`ColorDecisionOnARealTtyTests.test_no_color_flag_still_suppresses_color_on_a_real_tty`) | `ev7t1w` S-21 | `081smx` |
| G-16 | `tests/test_reporting_contract.py` | `runner_owns_lifecycle_notice` and driver prompt pure-ASCII invariant (`DriverPromptTests.test_prompts_are_pure_ascii`) | `ev7t1w` S-14 | `9yjp33` |
| G-17 | `tests/test_run_cli_ledger_message.py` | Machine JSON payload key set `{"ok", "error", "exit_code"}` in `run_cli._emit_error` (`test_machine_payload_carries_the_same_text_with_unchanged_keys`) | `ev7t1w` S-24 | `n2fx9i` |
| G-18 | `tests/test_runner_item_dependencies.py` | `manifest_entry_is_selectable` preserving `executed` entries for `InRunExecutedDependencyTests` | `yuhl6o` S-07, S-08 | `mv18lz` |
| G-19 | `tests/test_runner_profile_wizard.py` | `runner_profile_wizard` interactive discovery failure and manual entry flows | `ev7t1w` S-25 | `heknx6` |
| G-20 | `tests/test_runner_refork_guard.py` | `parse_plan_file` and front-matter readers loose leading whitespace tolerance (`FrontMatterReaderBehaviorTests.test_public_readers_tolerate_loose_leading_whitespace`) | `yuhl6o` S-06 | `qmpvcy` |
| G-21 | `tests/test_runner_stop.py` | `_record_checkpoint_stop` isolated git status recording on dirty worktree (`test_stop_isolated_git_status`) | `yuhl6o` S-33 | `09f6x3` |
| G-22 | `tests/test_rununify_conflicts.py` | `ses_` preference over earlier `conversation_id` hit in `extract_session_id` (`06-ct4w0a-D1` conflict case, `PrecedenceTests`) | `yuhl6o` S-25; `9rthek` S-12 | `u77lip` |
| G-23 | `tests/test_rununify_record.py` | Approved orchestrator end-to-end derivation on both hosts (`EndToEndDerivationTests.test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts`) and legacy manifest kind fallback (`test_legacy_manifest_fallback_infers_orchestrator_kind_from_plan_file`) | `yuhl6o` S-04, S-05; `9rthek` S-11 | `8ww1zo` |
| G-24 | `tests/test_rununify_run_queue.py` | `run_queue` exit code reading `SUCCESS_STATES` so `substantially-complete` exits nonzero (`TheExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES`) | `yuhl6o` S-29 | `bzjclz` |
| G-25 | `tests/test_selector_zero_open.py` | Selector resolution setid precedence over filename substring (`PrecedenceForcesFrontMatterReadsTests`) | `ev7t1w` S-26 | `ni8n5s` |
| G-26 | `tests/test_suite_adjudication.py` | Exit-code authority over failing-test list in suite adjudication (`TheExitCodeIsTheAuthorityAndNotTheList`) | `yuhl6o` S-18, S-22, S-23, S-24 | `jgpts7` |
| G-27 | `tests/test_suite_baseline.py` | `perform_gate_answer` baseline non-refusal and `not-mine` outcome equivalence (`NothingRefusesOnTheBaseline`) | `yuhl6o` S-16, S-20, S-21 | `xhrpeg` |
| G-28 | `tests/test_work_primitives.py` | `work_cmd.run_commit` routing through `git_commit_helper.offer_commit` | `ev7t1w` S-27 | `3vz4wj` |

(`RESIDUAL` group from E-01: empty, 0 rows.)

## Proposed changes (ordered, validatable)

1. E-01 whole-population measurement. 2. E-02 cross-check and grouped RETIRE-UNGUARDED list. 3. E-03 file or attribute a carrier per group.

## Deferred / out of scope (with reason)

- Writing replacement behavioral tests.
  - Carrier-Declined: each backlog item E-03 files carries its own restoration; this Set only retires citations and records carriers.
- The census fixture survivor (F-01).
  - Carrier-Declined: a classifier input, not a citation; see `ev7t1w` F-01.
- Closing backlog `iosmvn` itself.
  - Carrier-Declined: not this plan's act. Under `aw oc run`/`aw agy run` the runner's backlog-close path (`runner_shared.process_backlog_close`) closes a `From-Backlog` item when the run earns it; this plan neither hand-edits nor sets `iosmvn`.

## Scope check

- Over-scope: none; only new backlog files under `.aw/records/backlog/open/` (written by `aw backlog new`) and this plan. No source, test, or other plan is edited.
- Under-scope: none; whole-population closure and carrier filing are both itemized.

## Required tests / validation

- Whole-population measurement (E-01).
- `aw check backlog --agent` before and after filing; the diagnostic set is unchanged except for none naming a new item (E-03). The whole-repo `aw check` is not used as the bar: at review it exits 1 on 178 pre-existing findings across unrelated trees and takes minutes.

## Spec / documentation sync

N/A: no spec governs these comments; the only new records are backlog items created by the tool.

## Open questions

### OQ-01: One backlog item per site, per deleted file, or one rollup?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Per deleted file. A rollup is what this item already was and it proved hard to act on; per-site is too fine (several sites cite one behavioral class). Per-file matches the existing dedicated items `mv18lz`, `yf1p8y`, `2ohbkj`.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted whole-population measurement output (every hit line plus `UNRETIRED N`) and `git rev-parse --short HEAD`, with every surviving line attributed (census fixture, or child-missed / introduced-later with file and enclosing symbol).
  - Observed evidence:
    Command and output at execution HEAD:
    ```
    $ git rev-parse --short HEAD
    8df93a864
    $ python3 -c 'import re,subprocess,sys;from pathlib import Path;D=set(subprocess.check_output(["git","diff","--diff-filter=D","--name-only","19313eed^","19313eed"],text=True).split());O=re.compile(r"test_(orchestrator_probe_cache|review_findings_cascade|runner_stop_triggers|runner_backlog_close|runner_layering|run_flag_surface)\.py");B=[(f,i+1,t) for f in sys.argv[1:] for L in [Path(f).read_text().splitlines()] for i,l in enumerate(L) for t in re.findall(r"tests/test_\w+\.py",l) if t in D and not Path(t).is_file() and not O.search(t) and "19313eed" not in " ".join(L[max(0,i-3):i+4])];[print(*b) for b in B];print("UNRETIRED",len(B))' $(git ls-files 'agent_workflows/*.py' 'tools/*.py')
    tools/lost_guard_census.py 1104 tests/test_dependency_verb.py
    UNRETIRED 1
    ```
    Attribution of surviving line:
    - `tools/lost_guard_census.py 1104 tests/test_dependency_verb.py`: `tools/lost_guard_census.py` `print_classifier`'s `mixed_example = "tests/test_dependency_verb.py"` (`ev7t1w` F-01 census classifier fixture input, not a guard citation). Zero child-missed or introduced-later lines (`RESIDUAL` group is empty).
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: per child, the pasted E-01 `UNRETIRED N` from its executed plan beside the row count of its disposition table, and the count of each disposition; plus the appended grouped table (including any `RESIDUAL` group) quoted from this plan.
  - Observed evidence:
    Per-child E-01 `UNRETIRED N`, disposition table row count, and disposition counts:
    - `yuhl6o` (`.aw/records/plans/executed/20261011-iosmvn-01-yuhl6o-retire-or-repoint-the-residual-dangling-test-citations-in-ru.ipd.md`):
      - E-01 recorded: `UNRETIRED 41` (at HEAD `0c323ea3b`)
      - E-02 Disposition Table row count: `41` (`S-01`..`S-41`; mismatch count: `0`)
      - Dispositions: `REPOINT: 0`, `RETIRE-PIN: 22`, `RETIRE-UNGUARDED: 19`
    - `9rthek` (`.aw/records/plans/executed/20261011-iosmvn-02-9rthek-retire-or-repoint-the-dangling-test-citations-in-the-host-dr.ipd.md`):
      - E-01 recorded: `UNRETIRED 19` (at HEAD `7f8bfa478`)
      - E-02 Disposition Table row count: `19` (`S-01`..`S-19`; mismatch count: `0`)
      - Dispositions: `REPOINT: 0`, `RETIRE-PIN: 15`, `RETIRE-UNGUARDED: 4`
    - `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`):
      - E-01 recorded: `UNRETIRED 27` (at HEAD `7a99736fc`)
      - E-02 Disposition Table row count: `27` (`S-01`..`S-27`; mismatch count: `0`)
      - Dispositions: `REPOINT: 0`, `RETIRE-PIN: 12`, `RETIRE-UNGUARDED: 15`
    - Sum across Orders 01-03: `41 + 19 + 27 = 87` (equals whole-population `88` minus `1` census fixture); total `RETIRE-UNGUARDED` rows: `19 + 4 + 15 = 38`, grouped into `28` deleted test file basenames (`G-01`..`G-28`), plus `0` rows in `RESIDUAL`.
    Appended grouped table quoted from Findings:
    ```
    | Group | Deleted file | Property | Child / sites | Carrier |
    |---|---|---|---|---|
    | G-01 | `tests/test_artifact_core.py` | `SCAN_ROOTS` classification completeness in `classify_rel` (`ScanRootClassificationInvariantTests.test_no_scan_root_is_scanned_then_silently_dropped`) | `ev7t1w` S-02 | `sfdwaz` |
    | G-02 | `tests/test_awcmdsurf_vocab_and_parsers.py` | `reviews` absence from `TYPE_BACKENDS` and `selectors.KNOWN_PRIMARY_TYPES` (`DerivedVocabularyTests.test_reviews_has_no_backend_and_no_status_lifecycle`) | `ev7t1w` S-04 | `nrcvpg` |
    | G-03 | `tests/test_bug_gate_check.py` | Zero-finding direction in `check_release_gate_consistency` on ungated item with gated carrier (`test_the_mismatch_rule_fires_only_for_a_live_carrier`) | `ev7t1w` S-07 | `hybluq` |
    | G-04 | `tests/test_ci_check_parity.py` | Findings parity between CI and local check runs on the same tree (`TestCiLocalParity.test_ci_and_local_identical_on_same_tree`) | `ev7t1w` S-06 | `crk6wb` |
    | G-05 | `tests/test_dirty_base_gate.py` | `evaluate_clean_base` identical tracked scope (`clean` and `dirty_paths`) on shared and isolated paths (`test_the_tracked_scope_is_IDENTICAL_on_both_paths`) | `ev7t1w` S-16 | `x6trbp` |
    | G-06 | `tests/test_durable_capture.py` | `lint_file` and `check_durable_carrier` shared `evaluate_durable_carrier` predicate (`test_one_predicate_backs_both_surfaces`) | `ev7t1w` S-09 | `8owahv` |
    | G-07 | `tests/test_id6_global_mint.py` | `global_id6s` deliberate over-collection of quoted `Id` tokens (`PurityAndSubsetContractTests.test_the_mint_set_over_collects_quoted_ids_and_that_is_deliberate`) | `ev7t1w` S-01 | `s8eaay` |
    | G-08 | `tests/test_interrupt_menu.py` | `oc_runipd.main` interrupt stderr preservation notice (`RunnerMainOutputOnInterruptTests`) | `9rthek` S-07 | `zgqs4e` |
    | G-09 | `tests/test_lane_clean_base.py` | `evaluate_clean_base` non-refusal on untracked files (`test_case_3_an_untracked_file_does_NOT_refuse`) | `yuhl6o` S-09 | `dc80rp` |
    | G-10 | `tests/test_lane_permission_posture.py` | `agy_runipd.build_parser` `dangerously_skip_permissions` default `True` (`TestAntigravitySkipPermissionsDefaultIsPinned.test_option_still_defaults_to_true_on_the_parser`) | `9rthek` S-14 | `m7o4ew` |
    | G-11 | `tests/test_lane_tool_identity.py` | `driver_begin` subprocess environment baseline identity pin (`test_the_env_handed_to_the_begin_child_actually_carries_the_pin`) | `yuhl6o` S-26 | `o0gy5v` |
    | G-12 | `tests/test_naming_authority_single_source.py` | `build_clustered_name` and `parse_clustered` round-trip identity (`RoundTripTests`) | `ev7t1w` S-03 | `09i7fy` |
    | G-13 | `tests/test_orchestrator_deferral_reporting.py` | `RETIRE_REFUSED` to `ORCH_REASON` translation and unrecognized-reason fallback in `orchestrator_refusal_text` | `yuhl6o` S-10, S-11 | `dxe6w1` |
    | G-14 | `tests/test_plan_status.py` | Repository plans recognized status token drift guard (`PlanStatusDriftGuard.test_every_plan_has_a_recognized_status`) | `ev7t1w` S-19 | `7h2he0` |
    | G-15 | `tests/test_pwatch.py` | `pwatch` `--no-color` suppression on a real TTY (`ColorDecisionOnARealTtyTests.test_no_color_flag_still_suppresses_color_on_a_real_tty`) | `ev7t1w` S-21 | `081smx` |
    | G-16 | `tests/test_reporting_contract.py` | `runner_owns_lifecycle_notice` and driver prompt pure-ASCII invariant (`DriverPromptTests.test_prompts_are_pure_ascii`) | `ev7t1w` S-14 | `9yjp33` |
    | G-17 | `tests/test_run_cli_ledger_message.py` | Machine JSON payload key set `{"ok", "error", "exit_code"}` in `run_cli._emit_error` (`test_machine_payload_carries_the_same_text_with_unchanged_keys`) | `ev7t1w` S-24 | `n2fx9i` |
    | G-18 | `tests/test_runner_item_dependencies.py` | `manifest_entry_is_selectable` preserving `executed` entries for `InRunExecutedDependencyTests` | `yuhl6o` S-07, S-08 | `mv18lz` |
    | G-19 | `tests/test_runner_profile_wizard.py` | `runner_profile_wizard` interactive discovery failure and manual entry flows | `ev7t1w` S-25 | `heknx6` |
    | G-20 | `tests/test_runner_refork_guard.py` | `parse_plan_file` and front-matter readers loose leading whitespace tolerance (`FrontMatterReaderBehaviorTests.test_public_readers_tolerate_loose_leading_whitespace`) | `yuhl6o` S-06 | `qmpvcy` |
    | G-21 | `tests/test_runner_stop.py` | `_record_checkpoint_stop` isolated git status recording on dirty worktree (`test_stop_isolated_git_status`) | `yuhl6o` S-33 | `09f6x3` |
    | G-22 | `tests/test_rununify_conflicts.py` | `ses_` preference over earlier `conversation_id` hit in `extract_session_id` (`06-ct4w0a-D1` conflict case, `PrecedenceTests`) | `yuhl6o` S-25; `9rthek` S-12 | `u77lip` |
    | G-23 | `tests/test_rununify_record.py` | Approved orchestrator end-to-end derivation on both hosts (`EndToEndDerivationTests.test_an_approved_orchestrator_derives_orchestrate_on_BOTH_hosts`) and legacy manifest kind fallback (`test_legacy_manifest_fallback_infers_orchestrator_kind_from_plan_file`) | `yuhl6o` S-04, S-05; `9rthek` S-11 | `8ww1zo` |
    | G-24 | `tests/test_rununify_run_queue.py` | `run_queue` exit code reading `SUCCESS_STATES` so `substantially-complete` exits nonzero (`TheExitCodeReflectsTheRealOutcome.test_the_exit_code_reads_SUCCESS_STATES_not_EXECUTION_SUCCESS_STATES`) | `yuhl6o` S-29 | `bzjclz` |
    | G-25 | `tests/test_selector_zero_open.py` | Selector resolution setid precedence over filename substring (`PrecedenceForcesFrontMatterReadsTests`) | `ev7t1w` S-26 | `ni8n5s` |
    | G-26 | `tests/test_suite_adjudication.py` | Exit-code authority over failing-test list in suite adjudication (`TheExitCodeIsTheAuthorityAndNotTheList`) | `yuhl6o` S-18, S-22, S-23, S-24 | `jgpts7` |
    | G-27 | `tests/test_suite_baseline.py` | `perform_gate_answer` baseline non-refusal and `not-mine` outcome equivalence (`NothingRefusesOnTheBaseline`) | `yuhl6o` S-16, S-20, S-21 | `xhrpeg` |
    | G-28 | `tests/test_work_primitives.py` | `work_cmd.run_commit` routing through `git_commit_helper.offer_commit` | `ev7t1w` S-27 | `3vz4wj` |
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: per group, the pasted `rg -lwF` output and dry-run duplicate report, then either the pasted `aw backlog new ... --apply` output (id6 and path) or the owner's id6 with the line of its body that owns the property; `grep -n 'Blocks-Release' <path>` for any item filed `bug` (or a statement none was); the completed Carrier column quoted from this plan; and the pasted before and after `aw check backlog --agent` diagnostics.
  - Observed evidence:
    1. Pre-filing baseline `aw check backlog --agent`:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"backlog","findings":1,"findings_by_severity":{"error":0,"warning":0,"info":1},"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw backlog check"}
       ```
    2. Per-group `rg -lwF <basename> .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/backlog/blocked .aw/records/backlog/parked .aw/records/plans/pending` output, dry-run duplicate report, ownership judgment, and `aw backlog new ... --apply` output (or owner id6 + owning line):
       - `G-01` (`test_artifact_core.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `candidate duplicate(s) detected: - v7u6vm [done]: releases is a declared tracked tree with no scan root, so release records are invisible to aw attention; the reviews tree has no policy at all` -> opened `.aw/records/backlog/done/20260905-durablecapture-01-v7u6vm-attention-tracked-tree-scan-root-mismatch.backlog.md`: predates `19313eed` (closed 2026-09-18 via `m867ox`), `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-sfdwaz-01-sfdwaz-restore-behavioral-coverage-of-scan-roots-classifi.backlog.md` (`sfdwaz`)
       - `G-02` (`test_awcmdsurf_vocab_and_parsers.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-nrcvpg-01-nrcvpg-restore-behavioral-coverage-of-reviews-absence-fro.backlog.md` (`nrcvpg`)
       - `G-03` (`test_bug_gate_check.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-hybluq-01-hybluq-restore-behavioral-coverage-of-zero-finding-direct.backlog.md` (`hybluq`)
       - `G-04` (`test_ci_check_parity.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-crk6wb-01-crk6wb-restore-behavioral-coverage-of-findings-parity-bet.backlog.md` (`crk6wb`)
       - `G-05` (`test_dirty_base_gate.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `candidate duplicate(s) detected: - 2c7q0r [done]: 3i0aaz left tests/test_dirty_base_gate.py asserting the isolated dirty-base refusal that approved sibling d7qoxv was already signed off to remove` -> opened `.aw/records/backlog/done/20260916-planfence-01-2c7q0r-sibling-plan-test-fence-missed-later-approved-chan.backlog.md`: closed 2026-09-25 as moot when `test_dirty_base_gate.py` was deleted in `19313eed`, `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-x6trbp-01-x6trbp-restore-behavioral-coverage-of-evaluate-clean-base.backlog.md` (`x6trbp`)
       - `G-06` (`test_durable_capture.py`):
         - `rg -lwF`: `.aw/records/backlog/graduated/20261001-iosmvn-01-iosmvn-rollup-tracking-remaining-unowned-dangling-test-ci.backlog.md` (`iosmvn` itself, excluded by rule).
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-8owahv-01-8owahv-restore-behavioral-coverage-of-lint-file-and-check.backlog.md` (`8owahv`)
       - `G-07` (`test_id6_global_mint.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-s8eaay-01-s8eaay-restore-behavioral-coverage-of-global-id6s-deliber.backlog.md` (`s8eaay`)
       - `G-08` (`test_interrupt_menu.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-zgqs4e-01-zgqs4e-restore-behavioral-coverage-of-oc-runipd-main-inte.backlog.md` (`zgqs4e`)
       - `G-09` (`test_lane_clean_base.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-dc80rp-01-dc80rp-restore-behavioral-coverage-of-evaluate-clean-base.backlog.md` (`dc80rp`)
       - `G-10` (`test_lane_permission_posture.py`):
         - `rg -lwF`: `.aw/records/plans/pending/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md` (`ellenm` itself, excluded by rule).
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-m7o4ew-01-m7o4ew-restore-behavioral-coverage-of-agy-runipd-build-pa.backlog.md` (`m7o4ew`)
       - `G-11` (`test_lane_tool_identity.py`):
         - `rg -lwF`: `.aw/records/plans/pending/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md`, `.aw/records/backlog/graduated/20261001-iosmvn-01-iosmvn-rollup-tracking-remaining-unowned-dangling-test-ci.backlog.md` (`ellenm` and `iosmvn`, excluded by rule).
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-o0gy5v-01-o0gy5v-restore-behavioral-coverage-of-driver-begin-subpro.backlog.md` (`o0gy5v`)
       - `G-12` (`test_naming_authority_single_source.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-09i7fy-01-09i7fy-restore-behavioral-coverage-of-build-clustered-nam.backlog.md` (`09i7fy`)
       - `G-13` (`test_orchestrator_deferral_reporting.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-dxe6w1-01-dxe6w1-restore-behavioral-coverage-of-retire-refused-to-o.backlog.md` (`dxe6w1`)
       - `G-14` (`test_plan_status.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-7h2he0-01-7h2he0-restore-behavioral-coverage-of-repository-plans-re.backlog.md` (`7h2he0`)
       - `G-15` (`test_pwatch.py`):
         - `rg -lwF`: `.aw/records/plans/pending/20261011-x31lcm-01-ww744p-make-aw-pwatch-return-143-on-sigterm-while-keeping-exit-0-on.ipd.md` -> opened `ww744p`: tests SIGTERM `143` / SIGINT `0` exit codes and signal handler restoration (mentions `tests/test_pwatch.py` in Step 0 only as deleted history; does not restore `--no-color` real-TTY suppression), `owned-rejected`.
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-081smx-01-081smx-restore-behavioral-coverage-of-pwatch-no-color-sup.backlog.md` (`081smx`)
       - `G-16` (`test_reporting_contract.py`):
         - `rg -lwF`: `.aw/records/backlog/graduated/20261001-iosmvn-01-iosmvn-rollup-tracking-remaining-unowned-dangling-test-ci.backlog.md` (`iosmvn`, excluded by rule).
         - Dry-run duplicate report: `candidate duplicate(s) detected: - 8kttqq [done]: test_reporting_contract parity test walks GITIGNORED directories, so any local agent dump (e.g. opencode-recovery/) fails the suite on a clean tree` -> opened `.aw/records/backlog/done/20260908-testignore-01-8kttqq-parity-test-walks-gitignored-paths.backlog.md`: closed 2026-09-12 before `19313eed`, `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-9yjp33-01-9yjp33-restore-behavioral-coverage-of-runner-owns-lifecyc.backlog.md` (`9yjp33`)
       - `G-17` (`test_run_cli_ledger_message.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-n2fx9i-01-n2fx9i-restore-behavioral-coverage-of-machine-json-payloa.backlog.md` (`n2fx9i`)
       - `G-18` (`test_runner_item_dependencies.py`):
         - `rg -lwF`: `.aw/records/plans/pending/20261011-iosmvn-04-ellenm-reconcile-the-shipped-source-dangling-census-and-file-the-un.ipd.md`, `.aw/records/backlog/graduated/20261001-iosmvn-01-iosmvn-rollup-tracking-remaining-unowned-dangling-test-ci.backlog.md` (and `mv18lz`, graduated at review to `df486j`, now in `.aw/records/backlog/done/` after `df486j` executed in this run and committed `tests/test_manifest_entry_selectable.py`).
         - Dry-run duplicate report: `candidate duplicate(s) detected: - mv18lz [done]: Restore behavioral test coverage for manifest_entry_is_selectable preserving executed entries`
         - Ownership (`owned-confirmed`): `mv18lz` (`.aw/records/backlog/done/20261001-mv18lz-01-mv18lz-restore-behavioral-test-coverage-for-manifest-entr.backlog.md`, line 14: `Commit 19313eed deleted tests/test_runner_item_dependencies.py. Its InRunExecutedDependencyTests suite pinned that manifest_entry_is_selectable preserves executed plans as selectable queue entries.`).
       - `G-19` (`test_runner_profile_wizard.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-heknx6-01-heknx6-restore-behavioral-coverage-of-runner-profile-wiza.backlog.md` (`heknx6`)
       - `G-20` (`test_runner_refork_guard.py`):
         - `rg -lwF`: `.aw/records/backlog/graduated/20260930-fh8x8k-01-fh8x8k-agy-runipd-has-no-all.backlog.md` -> opened `fh8x8k`: tracks `agy_runipd.__all__` and mentions `test_runner_refork_guard.py` only as why an old `# noqa` existed, `owned-rejected`.
         - Dry-run duplicate report: `candidate duplicate(s) detected: - ykfgpd [done]: Collapse discover_plans' now-vestigial parse_plan_file injection, since one shared parser makes the seam pointless` -> opened `.aw/records/backlog/done/20260917-recunify-01-ykfgpd-collapse-vestigial-discover-plans-injection.backlog.md`: closed 2026-09-26 before `19313eed`, `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-qmpvcy-01-qmpvcy-restore-behavioral-coverage-of-parse-plan-file-and.backlog.md` (`qmpvcy`)
       - `G-21` (`test_runner_stop.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `candidate duplicate(s) detected: - wi2pmm [done]: test_runner_stop_level4's ten slow end-to-end tests fail when the slow marker is cleared` -> opened `.aw/records/backlog/done/20260922-wi2pmm-01-wi2pmm-stop-level4-slow-tests-fail-unmarked.backlog.md`: closed 2026-09-25 as moot for `test_runner_stop_level4.py`, `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-09f6x3-01-09f6x3-restore-behavioral-coverage-of-record-checkpoint-s.backlog.md` (`09f6x3`)
       - `G-22` (`test_rununify_conflicts.py`):
         - `rg -lwF`: `.aw/records/backlog/graduated/20261001-iosmvn-01-iosmvn-rollup-tracking-remaining-unowned-dangling-test-ci.backlog.md` (`iosmvn`, excluded by rule).
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-u77lip-01-u77lip-restore-behavioral-coverage-of-ses-preference-over.backlog.md` (`u77lip`)
       - `G-23` (`test_rununify_record.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-8ww1zo-01-8ww1zo-restore-behavioral-coverage-of-approved-orchestrat.backlog.md` (`8ww1zo`)
       - `G-24` (`test_rununify_run_queue.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `candidate duplicate(s) detected: - em0z50 [done]: aw oc run silently skips matched artifacts... - 7l1ggb [done]: test_rununify_run_queue.py's closure census never classified _integrate_stranded_lanes...` -> opened `em0z50` (closed 2026-09-19) and `7l1ggb` (closed 2026-09-25 as moot), both `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-bzjclz-01-bzjclz-restore-behavioral-coverage-of-run-queue-exit-code.backlog.md` (`bzjclz`)
       - `G-25` (`test_selector_zero_open.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-ni8n5s-01-ni8n5s-restore-behavioral-coverage-of-selector-resolution.backlog.md` (`ni8n5s`)
       - `G-26` (`test_suite_adjudication.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-jgpts7-01-jgpts7-restore-behavioral-coverage-of-exit-code-authority.backlog.md` (`jgpts7`)
       - `G-27` (`test_suite_baseline.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `aw backlog new: no duplicate candidates detected.`
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-xhrpeg-01-xhrpeg-restore-behavioral-coverage-of-perform-gate-answer.backlog.md` (`xhrpeg`)
       - `G-28` (`test_work_primitives.py`):
         - `rg -lwF`: `(0 hits, exit 1)`
         - Dry-run duplicate report: `candidate duplicate(s) detected: - 41mtsm [done]: git_commit_helper._is_interactive trusts stdin alone...` -> opened `.aw/records/backlog/done/20260927-41mtsm-01-41mtsm-git-commit-helper-is-interactive-trusts-stdin-alon.backlog.md`: fixed `_is_interactive` TTY stream check (closed 2026-09-30), `owned-rejected`.
         - `--apply` output: `aw backlog new: wrote .aw/records/backlog/open/20261014-3vz4wj-01-3vz4wj-restore-behavioral-coverage-of-work-cmd-run-commit.backlog.md` (`3vz4wj`)
    3. `bug` / `Blocks-Release` check: None of the 27 filed items was filed with `--work-kind bug` (no child disposition row recorded a user-perceptible defect; all 27 were filed `--work-kind chore --priority low`).
    4. Completed `Carrier` column quoted from Findings: `G-01: sfdwaz`, `G-02: nrcvpg`, `G-03: hybluq`, `G-04: crk6wb`, `G-05: x6trbp`, `G-06: 8owahv`, `G-07: s8eaay`, `G-08: zgqs4e`, `G-09: dc80rp`, `G-10: m7o4ew`, `G-11: o0gy5v`, `G-12: 09i7fy`, `G-13: dxe6w1`, `G-14: 7h2he0`, `G-15: 081smx`, `G-16: 9yjp33`, `G-17: n2fx9i`, `G-18: mv18lz`, `G-19: heknx6`, `G-20: qmpvcy`, `G-21: 09f6x3`, `G-22: u77lip`, `G-23: 8ww1zo`, `G-24: bzjclz`, `G-25: ni8n5s`, `G-26: jgpts7`, `G-27: xhrpeg`, `G-28: 3vz4wj` (plus `g73xcx` filed for the adjacent `backlog.cmd_new` 50-char slug trailing-hyphen slice defect discovered during E-03).
    5. Post-filing `aw check backlog --agent`:
       ```json
       {"schema":"aw.agent/v1","kind":"result","cmd":"check","outcome":"conforms","exit":0,"verified":true,"complete":true,"target":"backlog","findings":1,"findings_by_severity":{"error":0,"warning":0,"info":1},"evidence":["inventory","rules"],"diagnostics":[{"location":"<collisions>","rule":"check.collisions-not-checked"}],"next":"aw backlog check"}
       ```
       Diagnostics equal the pre-filing baseline set (`[{"location":"<collisions>","rule":"check.collisions-not-checked"}]`, 0 errors, 0 warnings).
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval recorded through `aw ipd set approved`, and after Orders 01-03 are executed (`- Item-Dependencies:`; the runner re-checks this at dispatch). OQ-01 is resolved; no open question remains.

EXECUTION CONTRACT. Scope fence: the declared Scope-Paths; an out-of-scope edit is made and then justified at finalize (`--scope-reason`), not a stop. Commit only those paths (this plan plus the new backlog files) through `aw commit ellenm -- <paths>`; never `git add -A`, bare, or `-a`, never `--no-verify`, never push; verify `git diff --cached --name-only` before committing. You MUST paste the actual command output for every measurement, dedupe search, `aw backlog new`, and `aw check`; never claim a result you did not run.

POST-GATE LIFECYCLE MOVE. After every `V-*` is `pass` with pasted evidence and `aw ipd lint --phase pre-transition` conforms: under `aw oc run`/`aw agy run` the runner performs `aw ipd begin`/`aw ipd finalize`; in a manual run use `aw ipd finalize <plan> --actor <agent/model> --message <summary> --apply`. Never `git mv` the plan or hand-edit `- Status:`. Backlog `iosmvn` carries no `- Blocks-Release:` to inherit.
