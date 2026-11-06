# IPD: Move runner, gate, hook and module reads onto artifact_meta and read_at

- Date: 2026-11-02
- Kind: child
- Concern: Spec `4sd62s` C5a requires every gate, hook and runner to read metadata through the cache, and 4.4 requires every reader of a HEAD, staged or branch revision to call `artifact_meta.read_at` instead of parsing git content. Measured 2026-11-02 at `0cbfcc706`: the runners and record modules outside Order 08's surfaces hold 27 reader modules (F-02 of `ffceq0`); `runner_shared` alone has 20 `^-` metadata regex sites and its own bullet parser `runner_shared._front_matter_bullets`; and 15 functions read metadata out of git blobs (`git show <rev>:<path>`, `git cat-file -p`, `:0:<path>`) and then apply a regex: `check_engine._blob_text`/`_status_meta` and their 6 callers, the four hooks in `agent_workflows/hooks/`, `status_set._prepare_status_change`, `plan_readiness.review_staleness_index`, five `runner_shared` functions and `ipd_lifecycle._release_own_plan_edit_before_landing`. Until they move, Order 11 (`9o83cr`) cannot delete the parsers, and a gate's verdict depends on which regex it happens to use.
- Scope: Phase B readers, part 2 of 2 (`4sd62s` section 7 step 5). (a) Move every 4.4 reader of git content onto `artifact_meta.read_at(id6, rev)` and the existing 4.4 gate rules, with the round-2 re-search recorded (F-03). (b) Move the runner reads (`runner_shared.parse_plan_file`, `discover_plans`, `discover_specs`, `edge_satisfied`, `resolve_backlog_item`, `backlog_item_paths_for_id`, `read_set_membership`, `_read_item_dependencies`, `_read_from_backlog`, `plan_bucket`, `expand_selectors`, `reconcile_disposition`, `execute_item_core`, `initialize_run_core`, `run_review_sequence`, `handle_review_orchestrator_readiness`, `enforce_freeze_time_refusal`, `enforce_no_active_runner_conflict`, `plan_audit_target`, `populate_manifest_backlog`, `compute_scope_reconciliation`, `declared_spec_paths`, the `_SET_RE`/`_ORDER_RE`/`_KIND_RE` users) and the `oc_runipd`/`agy_runipd` re-exports onto `artifact_meta.read`/`query`/`history`. (c) Move the record-module readers: `plans_index`, `plans_archive`, `plans_refs` (read side), `ipd_set_plan`, `completion`, `research_index`, `research_archive`, `prompts_index`, `artifact_audit`, `review_findings`, `review_sequence`, `review_tier`, `review_rereview`, `orchestrator_readiness`, `production_checks`, `work_cmd`, `artifact_adopt`, `plan_readiness` (working-tree reads). (d) Add the 4.8 hook that refuses a staged non-append change to `meta/*.jsonl` and treat a finalized plan's own `meta/<id6>.jsonl` as owned in finalize scope logic (4.4). EXCLUDES: the readers of Order 08 (`ffceq0`); writers, including the WRITE half of `runner_shared.rederive_front_matter`, `mark_plan_attended`, `record_oq_answer` and `perform_coordinator_proposal_file` (Orders 06/07); deleting parsers and INDEX code (Order 11); the event-ownership gate rules after the cutover (Order 13).
- Scope-Paths: agent_workflows/runner_shared.py, agent_workflows/oc_runipd.py, agent_workflows/agy_runipd.py, agent_workflows/check_engine.py, agent_workflows/hooks/executed_transition_gate.py, agent_workflows/hooks/ipd_dependency_statement_gate.py, agent_workflows/hooks/status_untooled_gate.py, agent_workflows/hooks/backlog_blocking_close_gate.py, agent_workflows/hooks/meta_log_append_gate.py, agent_workflows/status_set.py, agent_workflows/plan_readiness.py, agent_workflows/ipd_lifecycle.py, agent_workflows/plans_index.py, agent_workflows/plans_archive.py, agent_workflows/plans_refs.py, agent_workflows/ipd_set_plan.py, agent_workflows/completion.py, agent_workflows/research_index.py, agent_workflows/research_archive.py, agent_workflows/prompts_index.py, agent_workflows/artifact_audit.py, agent_workflows/review_findings.py, agent_workflows/review_sequence.py, agent_workflows/review_tier.py, agent_workflows/review_rereview.py, agent_workflows/orchestrator_readiness.py, agent_workflows/production_checks.py, agent_workflows/work_cmd.py, agent_workflows/artifact_adopt.py, agent_workflows/cli.py, agent_workflows/command_surface.py, agent_workflows/engine.py, agent_workflows/artifact_meta.py, agent_workflows/reviews.py, tests/conformance_matrix.py, tests/test_artifact_audit_verdicts.py, tests/test_plans_index.py, .aw/records/specs/approved/20260925-metastore-01-4sd62s-artifact-metadata-store.spec.md, tests/test_readers_read_at_gates.py, tests/test_readers_runner.py, tests/test_readers_record_modules.py, tests/test_readers_review_modules.py, tests/test_meta_log_append_gate.py, tests/test_readers_gate_cache_parity.py, tests/test_front_matter_loose_whitespace.py, CHANGELOG.md, .aw/records/plans/pending/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.ipd.md
- Item-Dependencies: executed:tve77h, executed:xexn45, executed:ffceq0
- Status: reviewed
- From-Spec: 4sd62s
- Work-Kind: feature
- Priority: high
- Blocks-Release: next
- Set: metastore
- Order: 9
- Highest E allocated: 16
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: t4gl15
- Readiness: go-pending-approval
- Review-Depth: complex

## Workflow history
- 2026-11-06 reviewed (aw set): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED
- 2026-11-06 /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-010 FIXED; review record .aw/records/reviews/20261102-metastore-09-t4gl15-move-runner-gate-hook-and-module-reads-onto-artifact-meta-an.review.md
- 2026-11-05 to-review (aw set): authored review-ready for spec 4sd62s (Set metastore)
- 2026-11-05 note (opencode its_direct/pt3-claude-opus-5.5-1m-us): maintainer-agreed addition of E-16/V-16 and F-09 (research body test must ignore the 4.1 banner), found by research 53jbi5 E-2/E-3; status unchanged at to-review.

- 2026-11-02 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every gate, hook, runner and record module reads metadata only through `artifact_meta` (working tree) or `artifact_meta.read_at` (index, commit or branch), each moved reader keeps a named, tested behavior, and staged `meta/*.jsonl` changes are refused unless they only append valid events.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

The pin-first rule of `ffceq0` applies to every move here: BEFORE the edit, a behavioral test in the named module pins the reader's current observable behavior (the ledger in `## Findings`) and runs green on the unmodified code; AFTER the edit, the same test runs unchanged. A test that must change is a behavior change and must be one of D-1 to D-4 below. For every existing module named as a baseline, save the per-test outcome list under the gitignored `.aw/state/t4gl15/` (`python3 -m pytest -o addopts="" -m "" -p no:randomly -n 0 -rA <modules> | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sed -E 's/ - .*//' | sort > .aw/state/t4gl15/<E>-before.txt`) before the move and the same command into `<E>-after.txt` after it; `diff` of the two prints nothing except lines a named decision explains. Run a new module's `-k` selection as its own command, never combined with baseline module paths, because `-k` filters every path on the command line. Every saved baseline goes under `.aw/state/t4gl15/`, never `/tmp`. A count measured at authoring (for example F-05's 1,719 records) is context, never the bar. New test modules set `pytestmark = pytest.mark.core` unless they need real `git` subprocesses across many commits, in which case they are marked `slow` and run in `make test-all`; none reads production source.

### Task group 1: read_at gates and hooks (4.4)

- [ ] E-01 Re-run the 4.4 search for git-content readers and record the result as table F-03 in this plan: `rg -n -e '"show"' -e 'cat-file' -e '"ls-files", "-s"' -e '"--cached"' -e '":0:"' -e 'rev-parse' agent_workflows`, classifying each hit as metadata reader (moves to `read_at`), path-only reader (no change: `work_cmd`, `cli`, `git_commit_helper`, `commit_lock`, `clean_delta`, `placement_switch`, `engine`, `layout_migration`), or not a metadata read (`leak_sanitizer.scan_working_tree_counted`, `artifact_audit.FinalizeEvidenceIndex`, `project_context`). Any metadata reader not in the 4.4 list is added to E-02 or E-04. Before any code edit, also save the sorted rule-id counts of `aw check all --agent` to `.aw/state/t4gl15/check-before.txt` and the `aw index plans --check`, `aw index research --check` and `aw index prompts --check` exit codes and outputs to `.aw/state/t4gl15/index-before.txt`.
  - Depends on: none
  - Expected outcome: F-03 lists every hit with its class; the metadata-reader set equals F-02's 15 functions or names the additions; both baselines are saved.
  - Execution state: pending

- [ ] E-02 Pin, then move, the `check_engine` git-content readers onto `artifact_meta.read_at`: `_blob_text` and `_status_meta` stop being called by `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `_staged_backlog_done_items` and `check_release_gate_consistency`, which call `read_at(id6, ":0:")`, `read_at(id6, "HEAD")` or `read_at(id6, <commit>)` and compare the returned `State`s. The phase-B rule shapes stay (4.4 rewrites them only after the cutover): "status changed with no matching tool-authored history line" compares `read_at` states and their `history` rows; a renamed or moved record is resolved INSIDE each revision, so a staged rename compares the HEAD record at its old path with the staged record at its new path. Pin in `tests/test_readers_read_at_gates.py` (real `git init` fixtures: an untooled status flip refused, a tooled one accepted, a staged rename into `executed/`, an illegal backlog transition, a release-blocking `done` with and without a handoff), and run `tests/test_check_engine_status_meta.py`, `tests/test_check_engine_release_gate.py`, `tests/test_precommit_scope_gate_severity.py` and `tests/test_backlog_close_gate_prose.py` green before and after.
  - Depends on: E-01
  - Expected outcome: every listed test passes before and after; `check_engine` no longer calls `_blob_text` (shown by `rg -n "_blob_text\(" agent_workflows`, which lists only its definition until Order 11 deletes it).
  - Execution state: pending

- [ ] E-03 Move the four hooks onto `read_at`: `executed_transition_gate` (`_blob_at`, `_has_executed_status`, `_plan_id_of`, `_staged_plan_executed_transitions` call `read_at` for `HEAD` and `:0:`; "an executed transition" stays "the staged status is terminal and the HEAD status is not"); `ipd_dependency_statement_gate._staged_ipd_overlay` (staged status and Item-Dependencies from `read_at(id6, ":0:")`); `status_untooled_gate` and `backlog_blocking_close_gate` keep delegating to the moved `check_engine` rules. Pin in `tests/test_readers_read_at_gates.py` through the real CLI entry points (`aw ipd-executed-gate`, `aw ipd-status-untooled-gate`, `aw backlog-blocking-close-gate`, `aw ipd-dependency-statement-gate`) on staged fixture repositories, and run `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` and `tests/test_ipd_dependency_statement_gate.py` green before and after.
  - Depends on: E-02
  - Expected outcome: each hook refuses and accepts the same fixtures before and after with the same exit codes; no hook module contains a `^-` metadata regex or a `git show` of a record.
  - Execution state: pending

- [ ] E-04 Move the remaining 4.4 git-content readers onto `read_at`: `status_set._prepare_status_change` (HEAD status), `plan_readiness.review_staleness_index` (plan status at the latest `plan-review:` commit through `read_at(id6, <commit>)`; the batched `git cat-file --batch` body read stays for the frozen-region digest, which is body prose, N3), `ipd_lifecycle._release_own_plan_edit_before_landing` (the byte comparison of a landed blob is not a metadata read and stays; any status or id read uses `read_at`), and the five `runner_shared` functions (`backlog_item_paths_for_commit`, `check_review_lane_artifacts`, `read_merge_stage`, `classify_conflict_set_for_rederivation`, `integrate_lane_branch` conflict description). For a merge stage blob (`:<stage>:<path>`), `read_at` accepts the stage revision spelling, or the function passes the blob text to `artifact_meta.read_text` (added by `ffceq0`) when no revision name exists. Pin with `tests/test_review_staleness_advisory.py`, `tests/test_ipd_lifecycle_cli.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_runner_backlog_close_behavior.py`, `tests/test_merge_conflict_sendback.py` and `tests/test_status_set.py -k untooled` (5 tests at review; `-k head` selects none) before and after, plus a new `tests/test_readers_read_at_gates.py` case that drives `aw ipd set` on a plan whose working-tree status differs from HEAD and asserts the HEAD status the setter reports is unchanged by the move.
  - Depends on: E-02
  - Expected outcome: all listed modules pass before and after; F-03's metadata-reader set has no remaining direct git-blob regex read.
  - Execution state: pending

- [ ] E-05 Add `agent_workflows/hooks/meta_log_append_gate.py` (4.8 last bullet), wired as `aw meta-log-append-gate` in `cli` and `command_surface` and offered as an optional pre-commit hook beside the four existing ones in the `engine` hook template: for every staged `.aw/records/meta/*.jsonl`, call ONE additive `artifact_meta` function (`artifact_meta.check_staged_log_append(id6) -> list[str]`, refusal reasons, empty when acceptable) that reads the HEAD and staged log blobs through `read_at`'s blob path and the loader, because spec 4.3 says "No other code, inside or outside `artifact_meta`, opens a log", so the hook never reads log bytes itself (this plan adds the function to the spec `4sd62s` 4.3 function list, the same kind of additive amendment `ffceq0` makes for `read_text`; tests in `tests/test_meta_log_append_gate.py`); the function refuses unless the staged bytes are the HEAD bytes plus whole new lines that the loader accepts (valid events, consecutive `seq`, valid `append`); a deleted or rewritten line, a new invalid event, or a new file whose first event is not `create` seq 1 or `checkpoint` seq 0 is refused with a teaching message. In phase B no log exists in this repository, so the hook is a no-op here and is proven on fixtures in `tests/test_meta_log_append_gate.py`.
  - Depends on: E-02
  - Expected outcome: fixtures for a valid append (accepted), a rewritten earlier line, a deleted line, an invalid appended event and a bad first event (each refused, exit 1) pass; `aw meta-log-append-gate` exits 0 on this checkout.
  - Execution state: pending

### Task group 2: runner reads

- [ ] E-06 Pin the runner's metadata behavior in `tests/test_readers_runner.py`: `runner_shared.parse_plan_file` on both hosts (`oc_runipd.parse_plan_file`, `agy_runipd` re-export) for id, status (single token, loose whitespace, multi-word falls back to the directory bucket), kind, Set, Order, Item-Dependencies, From-Backlog, Attended; `discover_plans`, `discover_specs`, `edge_satisfied` for `executed:`, `exists:` and `state:` edges, `resolve_backlog_item`, `backlog_item_paths_for_id`, `read_set_membership`, `expand_selectors` (id6, Set, status selectors), `plan_bucket`, `reconcile_disposition`, `enforce_freeze_time_refusal`, and the readiness read used before auto-approval (`plan_readiness.is_plan_review_approved`, 4.4a row `l56tyz`: a missing readiness is refused). Run `tests/test_front_matter_loose_whitespace.py`, `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_typed_queue_entries.py`, `tests/test_run_selection_policy.py`, `tests/test_spec_review_dispatch.py`, `tests/test_readiness_absence_invariant.py`, `tests/test_attended_session.py` and `tests/test_freeze_time_refusal.py` green as the baseline.
  - Depends on: none
  - Expected outcome: the new module passes on the unmodified code; the ten baseline summary lines are recorded.
  - Execution state: pending

- [ ] E-07 Move the runner reads listed in Scope (b) onto `artifact_meta.read`/`query`/`history`: `parse_plan_file` builds `PlanRecord` from `artifact_meta.read(id6)` resolved by path; `discover_plans`/`discover_specs` use one `query()`; `edge_satisfied` reads target status from the cache; `_SET_RE`, `_ORDER_RE`, `_KIND_RE`, `_read_set`, `_read_order`, `_read_item_dependencies`, `_read_from_backlog` and the `read_front_matter_*` and `backlog.parse_item` calls are replaced; plan text read for prompts and bodies (lint, review sequence, scope reconciliation of body sections) still reads the file (N3). `runner_shared._front_matter_bullets` and `_split_metadata_region` keep their roles only inside the records-only conflict classifier and `rederive_front_matter` (merge-stage text, E-04) until `artifact_meta.read_text` serves them; their remaining uses are listed in F-04 for Order 11. `oc_runipd`/`agy_runipd` keep their `_read_id` re-exports (`tools/ipdrunner/runagy.py` consumes `agy_runipd._read_id`) bound to the moved selector function. `parse_plan_file` keeps today's loose `-  `/`-\t` tolerance (D-4) by taking `id` and `status` from the loose values that `ffceq0`'s `artifact_meta.read_text` returns when the strict cached value is absent; the fallbacks for a missing Set, Order or id6 (filename, then a path hash) are unchanged.
  - Depends on: E-06
  - Expected outcome: E-06 and its ten baseline modules pass unchanged except the assertions D-1 names; a `python3 -c` snippet that prints `sorted((r.id6, r.status, r.setid, r.order, r.kind, tuple(r.dependencies)) for r in runner_shared.discover_plans(Path(".").resolve()).values())` for this checkout, saved to `.aw/state/t4gl15/discover-before.txt` before the edit, prints the same list after the move except the status values D-1 names (measured at review: one record, `vfa1tl`, changes from `EXECUTED` to `executed`; F-05's count is context) (`aw oc run` has no dry-run mode, measured with `aw oc run start --help`).
  - Execution state: pending

- [ ] E-08 Treat a finalized plan's own `meta/<id6>.jsonl` as a path the plan owns (4.4 bullet on `runner_shared._body_change_is_history_insert_only`): `compute_scope_reconciliation`, `_body_change_is_history_insert_only` and the finalize scope check in `ipd_lifecycle` accept a change to `.aw/records/meta/<own id6>.jsonl` without a Scope-Paths entry and still flag another artifact's log. Test in `tests/test_readers_runner.py` with a finalize-scope fixture that changes its own log and another plan's log.
  - Depends on: E-07
  - Expected outcome: the own-log change is in scope, the other plan's log is reported out of scope.
  - Execution state: pending

### Task group 3: plans, research and prompts modules

- [ ] E-09 Pin, then move, `plans_index` (`plan_entry`, `scan_plans`, `query`, `_meta`, `check_drift` metadata reads), `plans_archive` (`_ID_RE`, date, status and Set reads in `sweep_candidates` and `_plan_status`), `plans_refs` read side, `ipd_set_plan` (Set inventory via `plans_index.scan_plans`) and `completion` (active Set ids) onto `artifact_meta.query`. `plans_index` entries keep their fields; `status` for a multi-word plan follows D-1 of `ffceq0` (canonical value). The INDEX writers keep writing INDEX files from the same entries until Order 11 deletes them (AC-9). Pin in `tests/test_readers_record_modules.py` and run `tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_plans_archive_selectors.py`, `tests/test_ipd_set_plan.py` and `tests/test_completion.py` green before and after.
  - Depends on: none
  - Expected outcome: all listed modules pass before and after; `aw index plans --check` reports the same exit code and output as `.aw/state/t4gl15/index-before.txt` (any change traced to D-1); `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/plans_index.py agent_workflows/plans_archive.py` prints nothing.
  - Execution state: pending

- [ ] E-10 Pin, then move, `research_index` (`_scan_docs`, the `- Status:` line reader, `resolvable_consumer_ids` with `_META_ID_RE`), `research_archive` (`research_contract.parse_frontmatter` reads) and `prompts_index` (`_parse_metadata_comment` uses) onto `artifact_meta.query`/`read`; `research_contract.parse_frontmatter` and `prompts_index._parse_metadata_comment` stay defined (writers and the legacy loader still need the grammar until Order 11) but have no reader caller outside `artifact_meta`. Pin in `tests/test_readers_record_modules.py` and run `tests/test_research_index.py`, `tests/test_research_archive.py`, `tests/test_research_companion.py`, `tests/test_prompts_index.py` and `tests/test_index_check_agent_records.py` green before and after.
  - Depends on: E-09
  - Expected outcome: all listed modules pass before and after; `aw index research --check` and `aw index prompts --check` report the same result as before.
  - Execution state: pending

- [ ] E-16 Make the research body test ignore the 4.1 `aw-managed` banner (F-09): the value that `research_index.derive_pipeline_positions` reads as `has_body` (today computed in `research_index._doc_entry` as "any non-blank text after the closing `---`") must be false when the only text after the front matter is the single leading `<!-- aw-managed: ... -->` banner comment of `4sd62s` 4.1 plus whitespace, and true when any other text follows it. Compute it in ONE place used by every reader of `has_body`, whether that is the moved `research_index` reader or a field `artifact_meta` exposes; do not strip arbitrary HTML comments, only the leading banner. Test in `tests/test_readers_record_modules.py` with `tmp_path` research trees written in the post-cutover shape (two-key front matter plus banner): a Set holding a `research-prompt` with `outcome: none-yet` and a `reconciliation-report` whose body is only the banner yields `unrun`; adding a `research-report` whose body is the banner plus one heading yields `partial`; giving the reconciliation report the banner plus a heading yields `synthesized`. The same three trees in the pre-cutover shape (no banner) yield the same three positions.
  - Depends on: E-10
  - Expected outcome: the six fixture cases yield `unrun`, `partial`, `synthesized` in both shapes; `aw index research --check` reports the same result as before on this checkout.
  - Execution state: pending

### Task group 4: review and orchestration modules

- [ ] E-11 Pin, then move, `review_findings` (`_META_RE` front-matter read in `parse_review_text`; the review body grammar of rounds and findings stays, N3), `artifact_audit` (`_STATUS_LINE_RE` in `read_declared_status`, which serves every artifact type, so D-1 normalization applies only when the record is a plan), `reviews` subject resolution (`reviews._resolve_selector_paths` and `collect_decisions` subject lookups) and `review_findings.review_attestation_missing` lookups onto the cached `review_files` and `reviews` rows (`artifact_meta.query(latest_gate_review_of=...)`); the predicate's acceptance rule stays as it is (the gate-only change is Order 06's). Pin in `tests/test_readers_review_modules.py` and run `tests/test_review_findings_gate.py`, `tests/test_spec_review_attestation.py`, `tests/test_artifact_audit.py`, `tests/test_artifact_audit_verdicts.py` and `tests/test_artifact_audit_identity_staleness.py` green before and after.
  - Depends on: none
  - Expected outcome: all listed modules pass before and after; `aw check specs --agent` reports the same `check.spec-review-unattested` set as before.
  - Execution state: pending

- [ ] E-12 Pin, then move, `review_sequence` (`count_verdict_bearing_entries`, `restore_pre_s7_plan` status and readiness reads, the snapshot verdict checks), `review_tier` and `review_rereview` (`meta_fields` reads, the `ipd_schema.read_readiness` call in `review_rereview`), `orchestrator_readiness` (`_BATCH_META_RE`, `meta_fields` reads), `production_checks` (`_PLAN_ID_RE`, `_ITEM_DEPS_RE`, `_SCOPE_PATHS_RE`, `_ITEM_FROM_BACKLOG_RE`, `_SET_RE`, `parse_item`, history clause), `work_cmd` (`_plan_id6`, `_plan_status`) and `artifact_adopt` (`_BULLET_ID_RE` in the adoption id inventory) onto `artifact_meta.read`/`query`/`history`, or `artifact_meta.read_text` for before/after snapshot strings that are not files. `restore_pre_s7_plan` still WRITES plan text and is a writer for Order 07; only its reads move here. Pin in `tests/test_readers_review_modules.py` and run `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py`, `tests/test_review_rereview.py`, `tests/test_orchestrator_readiness.py`, `tests/test_production_checks_trace.py`, `tests/test_backlog_production.py`, `tests/test_scope_match.py` and `tests/test_artifact_adopt.py` green before and after.
  - Depends on: E-11
  - Expected outcome: all listed modules pass before and after; none of the seven modules contains a `^-` metadata regex call.
  - Execution state: pending

### Task group 5: parity, offline proof and finish

- [ ] E-13 Add `tests/test_readers_gate_cache_parity.py` (AC-1a, the setter and pre-commit gate cases): on a staged fixture repository, run a setter (`aw ipd set to-review <plan>`), `aw ipd-status-untooled-gate`, `aw ipd-executed-gate` and `aw backlog-blocking-close-gate` with a cold cache, a warm cache, a deleted `.aw/state/index.db` and an `index.db` overwritten with random bytes; assert identical exit codes and normalized outputs. Then stage an external edit to a record and assert each gate sees it with no rebuild; replace the staged blob with an unparseable record and assert the gate fails closed naming the record.
  - Depends on: E-03, E-07
  - Expected outcome: every case passes; the module is marked `core` unless its git work exceeds the core budget, in which case `slow` with the reason recorded.
  - Execution state: pending

- [ ] E-14 Prove AC-12's setter case and the absence of network use in this plan's surfaces: in `tests/test_readers_gate_cache_parity.py`, run `aw ipd set to-review <plan>` and `aw ipd-executed-gate` with `PATH` stripped of `opencode`, `agy` and `claude` and with `socket.socket` patched to raise through a `sitecustomize` on `PYTHONPATH`; both succeed.
  - Depends on: E-13
  - Expected outcome: both runs exit 0.
  - Execution state: pending

- [ ] E-15 Record the residual audit and finish: run `rg -n "re\.(compile|search|match|finditer|findall|sub|fullmatch)\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows` and `rg -n "Workflow history" agent_workflows`, and write table F-04 in this plan listing every remaining hit with its owner: writer (Orders 06/07, named), body-prose bullet kept by N3 (named pattern), legacy grammar inside `artifact_meta.py`, or a parser that Order 11 deletes. A reader hit with no such owner is a defect of this plan and is moved before finishing. Run every module named in E-02 to E-14 and E-16, the bare core gate `python3 -m pytest`, `make test-all`, `aw check all --agent` (rule-id multiset equal to `.aw/state/t4gl15/check-before.txt`, any difference traced to a record changed in between), and `aw sanitize --agent`; add a `CHANGELOG.md` `2.0.0 (pending)` line for the new hook, with no em or en dashes in that user-facing prose; commit through `aw commit t4gl15 -- <each changed path>`, one commit per task group allowed, never `git add -A`, a bare `git add` or `git commit -a`. Never push.
  - Depends on: E-04, E-05, E-08, E-10, E-12, E-14, E-16
  - Expected outcome: F-04 has no unowned reader hit; all runs pass; every commit is path-scoped to Scope-Paths (or justified at finalize).
  - Execution state: pending

Add further leaves as `- [ ] E-NEW <action>` and run `aw ipd sync` to assign ids.

## Project conventions discovered (Step 0)

- Interface names from Order 02 (`tve77h`), used exactly: `artifact_meta.read(id6) -> State`, `artifact_meta.history(id6)`, `artifact_meta.query(...)` (type, status, Set, order, `depends_on`, `latest_gate_review_of`, `path` filters, and an `incomplete` list), `artifact_meta.resolve(path_or_id6)`, and `artifact_meta.read_at(id6, rev)`, which runs git in the repository that owns the resolved records root, resolves the record's path inside that revision (`git ls-files -s` for the index, `git rev-parse <rev>:<path>` for a commit), caches by blob sha in `rev_log_states`/`rev_mirrors`, feeds a miss to the same loader (the legacy loader for a bullet blob in phase B), fails closed on a validation error, and returns distinct results for an absent record, an invalid revision and an unversioned placement. From Order 08 (`ffceq0`): `artifact_meta.read_text(text, *, record_type=None) -> State` for in-memory text (merge-stage blobs, before/after review snapshots), and decision D-1 (canonical normalized status for multi-word plans).
- Today's git-content helpers: `check_engine._blob_text(repo_root, ref, path)` (`git show <ref>:<path>`, `:0:<path>` for the index) and `check_engine._status_meta(text)`; `hooks.executed_transition_gate._blob_at`; `runner_shared.read_merge_stage` (`git cat-file -p :<stage>:<path>`); `runner_shared._run_git`.
- The hooks are thin: `hooks.status_untooled_gate.check` delegates to `check_engine.check_status_untooled`, and `hooks.backlog_blocking_close_gate.check` filters `check_engine.check_release_gate_consistency`; both are dispatched by `cli` (`ipd-status-untooled-gate`, `backlog-blocking-close-gate`, `ipd-executed-gate`, `ipd-dependency-statement-gate`) and installed as optional pre-commit hooks from the `engine` template (`ipd-executed-transition-gate`, `ipd-status-untooled-gate`).
- One runner plan record serves both hosts: `runner_shared.PlanRecord` (`id6`, `setid`, `status`, `order`, `path`, `rel_path`, `dependencies`, `kind`, `dependency_error`, `from_backlog`) built by `runner_shared.parse_plan_file`; `oc_runipd` re-exports `selectors.read_front_matter_id as _read_id`, and `tools/ipdrunner/runagy.py` consumes `agy_runipd._read_id`.
- `runner_shared._front_matter_bullets` and `_split_metadata_region` feed the records-only conflict classifier (`classify_records_only_front_matter_conflict`) and `rederive_front_matter` (plan `kl18sz`).
- The plans index writer and reader are one module (`plans_index.run_index`, `scan_plans`, `plan_entry`, `query`); `ipd_set_plan` and `completion` consume `scan_plans`; `plans_archive` reads `_idx._EXCLUDE_NAMES` and calls `scan_plans`.
- Review files: `review_findings.parse_review_text` (front matter via `review_findings._META_RE`, then rounds and findings), `review_findings.review_attestation_missing` (the one attestation predicate).
- Core tier: `pytestmark = pytest.mark.core`; tests needing many real git commits use the `slow` marker and run in `make test-all`.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

Measured 2026-11-02 at `0cbfcc706`.

| Id | Evidence | Finding |
|---|---|---|
| F-01 | Reader module split (see `ffceq0` F-02). This plan: `runner_shared` (20 `^-` regex sites in 30+ functions), `oc_runipd`, `agy_runipd`, `hooks/executed_transition_gate` (1 regex plus inline `re.search` calls), `hooks/ipd_dependency_statement_gate`, `hooks/status_untooled_gate`, `hooks/backlog_blocking_close_gate`, `check_engine` git readers (12 `_blob_text` call sites), `status_set._prepare_status_change`, `plan_readiness` (6 regex sites; `review_staleness_index`), `ipd_lifecycle._release_own_plan_edit_before_landing`, `plans_index` (6), `plans_archive` (5), `plans_refs` (read side), `ipd_set_plan`, `completion`, `research_index` (2), `research_archive`, `prompts_index`, `artifact_audit` (1), `review_findings` (1), `review_sequence` (2), `review_tier`, `review_rereview`, `orchestrator_readiness` (1), `production_checks` (5), `work_cmd` (2), `artifact_adopt` (1) | 27 reader modules. |
| F-02 | `git show`/`cat-file`/`:0:` metadata readers: `check_engine._blob_text` callers `check_status_untooled`, `check_status_untooled_range`, `check_staged_illegal_backlog_transition`, `_lane_carrier_is_executed`, `check_release_gate_consistency` (via `_staged_backlog_done_items`); `hooks.executed_transition_gate._blob_at`; `hooks.ipd_dependency_statement_gate._staged_ipd_overlay` (through `check_engine._blob_text`/`_status_meta`); `status_set._prepare_status_change` (HEAD status through `check_engine._blob_text`); `plan_readiness.review_staleness_index` (`git cat-file --batch`); `runner_shared.backlog_item_paths_for_commit` (`git show <sha>:<path>` then `backlog.parse_item`), `check_review_lane_artifacts` (`git show <branch>:<path>`), `read_merge_stage`, `classify_conflict_set_for_rederivation` (`git cat-file -p`), `integrate_lane_branch` (`git cat-file -p <tree>:<path>` then `check_engine._metadata_status`); `ipd_lifecycle._release_own_plan_edit_before_landing` (`git show <landed>:<path>`) | 15 functions, matching the 4.4 list; E-01 re-runs the search at execution time and records it as F-03. |
| F-03 | (written by E-01) the re-run 4.4 search with each hit classified | 4.4 says the list is a minimum. |
| F-04 | (written by E-15) residual `^-` regex and `Workflow history` hits after this plan, with owners | Input to Order 11. |
| F-05 | `runner_shared.discover_plans(repo)` returns 1,719 records on this checkout | Baseline for E-07's parity check. |
| F-06 | `aw oc run` sub-commands are `start, resume, status, report, stop, integrate, audit`; none has a dry-run option | E-07 compares `discover_plans` output instead of a queue preview. |
| F-07 | Path-only git readers (no change): `work_cmd` (`diff --name-only --cached`), `git_commit_helper`, `commit_lock`, `clean_delta`, `cli`, `placement_switch`, `engine`, `layout_migration`; non-metadata readers: `leak_sanitizer.scan_working_tree_counted` (reads every tracked file as text, which will include `meta/*.jsonl`), `artifact_audit.FinalizeEvidenceIndex` (commit subjects), `project_context` (`ls-files -s` modes) | Matches 4.4's "not metadata readers"; recorded so the E-01 classification is checkable. |
| F-08 | No hook inspects `meta/*.jsonl`; 4.8 requires one | E-05 adds it. |
| F-09 | Measured 2026-11-05: `research_index._doc_entry` sets `has_body` true for any non-blank text after the closing `---`, and `derive_pipeline_positions` uses it to place a Set `unrun`, `partial` or `synthesized`. `4sd62s` 4.1 puts the `aw-managed` banner after the front matter of every artifact. Re-running `derive_pipeline_positions` on this checkout's 164 research entries with every `has_body` forced true (the post-cutover state if the banner counts as body) moves Set `awclia` from `unrun` to `synthesized`, because its reconciliation report `v912ed` has no body today. Found by research `53jbi5` findings E-2/E-3. | A defect the cutover would introduce whether or not any other spec lands; E-16 fixes it before Order 13 (`cxxmyv`). |

READER LEDGER: prior behavior, the pinning test, and the result.

| Reader | Prior behavior | Pinning test | After |
|---|---|---|---|
| `check_engine.check_status_untooled` and `_range` | HEAD vs staged `- Status:` via `_blob_text` + `_status_meta`; refuse with no matching history line | E-02 fixtures; `tests/test_check_engine_status_meta.py`, `tests/test_precommit_scope_gate_severity.py` | same verdicts via `read_at` states and their history |
| `check_engine.check_staged_illegal_backlog_transition`, `_staged_backlog_done_items`, `check_release_gate_consistency`, `_lane_carrier_is_executed` | staged/HEAD backlog and carrier status via git blobs | E-02 fixtures; `tests/test_check_engine_release_gate.py`, `tests/test_backlog_close_gate_prose.py` | same via `read_at` |
| `hooks.executed_transition_gate` | case-insensitive region `status: executed|done`, `- Id:` outside fences, finalize evidence | `tests/test_executed_transition_gate.py`, `tests/test_executed_transition_gate_e2e.py` | same via `read_at`; D-2 for case |
| `hooks.ipd_dependency_statement_gate` | staged `- Status:` and `Item-Dependencies` overlay | `tests/test_ipd_dependency_statement_gate.py` | same via `read_at(":0:")` |
| `status_set._prepare_status_change` HEAD read | HEAD `- Status:` of the plan path | `tests/test_status_set.py` | `read_at(id6, "HEAD")` |
| `plan_readiness.review_staleness_index` | status at latest `plan-review:` commit plus frozen-region body digest | `tests/test_review_staleness_advisory.py` | status via `read_at`; body digest unchanged (N3) |
| `runner_shared` git readers | backlog id from commit blob, review-lane plan checks, merge-stage keys, conflict status | `tests/test_runner_backlog_close_behavior.py`, `tests/test_records_only_lane_rederive.py`, `tests/test_merge_conflict_sendback.py` | `read_at` or `read_text` |
| `ipd_lifecycle._release_own_plan_edit_before_landing` | byte equality of landed blob vs mirrored bytes | `tests/test_ipd_lifecycle_cli.py` | unchanged (not a metadata read); recorded in F-03 |
| `runner_shared.parse_plan_file` (both hosts) | loose `^-\s*` id/status/kind/Set/Order; multi-word status falls back to the directory bucket (`pending`) | `tests/test_front_matter_loose_whitespace.py`, E-06 | D-1, D-4 |
| `runner_shared.discover_plans`, `discover_specs`, `edge_satisfied`, `expand_selectors`, `resolve_backlog_item` | per-file regex reads | E-06 module, `tests/test_runner_shared.py`, `tests/test_oc_runipd.py`, `tests/test_agy_runipd_cli.py`, `tests/test_typed_queue_entries.py`, `tests/test_run_selection_policy.py`, `tests/test_spec_review_dispatch.py` | cached fields; same `discover_plans` list (F-05) |
| `plan_readiness.is_plan_review_approved` | structured readiness believed only with review provenance in history; missing readiness refused (4.4a `l56tyz`) | `tests/test_readiness_absence_invariant.py` | same rule over cached readiness and `history` |
| `plans_index`, `plans_archive`, `ipd_set_plan`, `completion` | whole-file `_META_RE` reads (whole-line status) | `tests/test_plans_index.py`, `tests/test_plans_archive.py`, `tests/test_plans_archive_selectors.py`, `tests/test_ipd_set_plan.py`, `tests/test_completion.py` | D-1 status; other fields unchanged |
| `research_index`, `research_archive`, `prompts_index` | YAML and `aw-prompt` comment parse | `tests/test_research_index.py`, `tests/test_research_archive.py`, `tests/test_research_companion.py`, `tests/test_prompts_index.py`, `tests/test_index_check_agent_records.py` | cached fields |
| `review_findings`, `artifact_audit`, `reviews` | review front matter by `_META_RE`; `_STATUS_LINE_RE` strict single-token status | `tests/test_review_findings_gate.py`, `tests/test_spec_review_attestation.py`, `tests/test_artifact_audit.py`, `tests/test_artifact_audit_verdicts.py`, `tests/test_artifact_audit_identity_staleness.py` | cached `review_files`/`reviews` rows; D-1 for status |
| `review_sequence`, `review_tier`, `review_rereview`, `orchestrator_readiness`, `production_checks`, `work_cmd`, `artifact_adopt` | `meta_fields`, `read_readiness` and module-local regex reads | `tests/test_review_sequence.py`, `tests/test_review_sequence_runner.py`, `tests/test_review_tier.py`, `tests/test_review_rereview.py`, `tests/test_orchestrator_readiness.py`, `tests/test_production_checks_trace.py`, `tests/test_backlog_production.py`, `tests/test_scope_match.py`, `tests/test_artifact_adopt.py` | cached fields or `read_text` for snapshots |

DECISIONS where readers disagreed (4.3):

- D-1 (multi-word status). This plan applies `ffceq0` D-1 as amended at its review: PLAN records return the canonical normalized status (`plans.normalize_status` of the first token); every other type keeps its raw single-token status, because `plans.normalize_status` maps `open`, `implemented`, `planned` and similar non-plan values to `legacy/unknown`, and the runner (`discover_specs`, `resolve_backlog_item`, `edge_satisfied` `state:` edges) and `artifact_audit.read_declared_status` read specs and backlog items too. WHAT EACH CONSUMER LOSES: `runner_shared.parse_plan_file` today returns the directory bucket (`pending` in the test fixture, `executed` for the 24 real plans, which are all in `executed/`) for a multi-word value; it now returns the normalized first-token value, which for all 24 real plans is the same `executed`. The one test assertion that changes is the fixture in `tests/test_front_matter_loose_whitespace.py::test_single_token_status_contract_survives`, whose multi-word `EXECUTED (approved by maintainer)` in `pending/` now yields `executed` instead of `pending`; that test is updated and listed in Scope-Paths. `plans_index`, `ipd_set_plan` and `artifact_audit` lose the prose status line for those 24 plans (none are runnable or in a pending Set). `artifact_audit._STATUS_LINE_RE` returned None for them and now returns `executed`. Test assertions that may change, each only in its multi-word or upper-case plan case: `tests/test_artifact_audit_verdicts.py::test_multi_word_status_is_unreadable_by_design` (its fixture is not under a plans directory; if the moved reader resolves it as a non-plan, the assertion stays), and any `tests/test_plans_index.py` assertion on a whole-line status; both are in Scope-Paths. Measured at review: on this checkout `discover_plans` differs from the normalized value on one record only (`vfa1tl`, `EXECUTED` to `executed`), because `parse_plan_file` already falls back to the directory bucket for the multi-word records.
- D-2 (status case in `executed_transition_gate`). The hook matches `status: executed|done` case-insensitively; the cached status is canonical lower-case (`EXECUTED`/`DONE` normalize to `executed`), so the hook's verdict is unchanged for every input the old regex accepted.
- D-4 (loose whitespace in the runner). KEPT: `runner_shared.parse_plan_file` accepts `-  ` and `-\t` bullets today (`tests/test_front_matter_loose_whitespace.py::test_parse_plan_file_tolerates_loose_leading_whitespace`), while `tve77h`'s legacy loader is strict. The runner takes `id` and `status` from `read_text`'s loose values when the strict value is absent (E-07), so the pinned test passes unchanged. 0 tracked records use the loose spelling, so the cache and the runner agree on the corpus.
- D-3 (YAML vs bullet for research in `research_index` and `artifact_adopt`). Kept as `ffceq0` D-2: the cache carries research YAML status and `id`, and the bullet `- Id:` inventory of `artifact_adopt` reads the cached `id` for plans, specs, backlog and releases, so each consumer gets the answer it gets today.

## Proposed changes (ordered, validatable)

1. Re-run the 4.4 search; move the `check_engine` git readers, the four hooks and the other git-content readers onto `read_at`; add the `meta/*.jsonl` append hook (E-01 to E-05).
2. Pin then move the runner reads; own-log finalize scope (E-06 to E-08).
3. Pin then move the plans, research and prompts modules (E-09, E-10), and make the research body test ignore the 4.1 banner (E-16, F-09).
4. Pin then move the review and orchestration modules (E-11, E-12).
5. Gate cache parity (AC-1a), offline setter (AC-12), residual audit, commit (E-13 to E-15).

## Deferred / out of scope (with reason)

- The readers of `selectors`, `aw find`/`aw search`/`aw ipd board`, `attention`, `check_engine` working-tree rules and `ipd_lint`; `aw check meta`; `aw meta repair`; `artifact_meta.read_text`.
  - Carrier: ffceq0
- The WRITE halves of `runner_shared.rederive_front_matter`, `mark_plan_attended`, `record_oq_answer`, `perform_coordinator_proposal_file` and `review_sequence.restore_pre_s7_plan`, and every setter.
  - Carrier: xexn45
- Deleting `check_engine._blob_text`, `_status_meta`, `runner_shared._front_matter_bullets`, `review_findings._META_RE`, `plans_index._META_RE`, the INDEX writers and every other leftover parser; the AC-1 test.
  - Carrier: 9o83cr
- Gate rules in their post-cutover form ("mirrored status differs from replayed state", "staged log violates append rules", executed transition as finalize or rollup append only) and AC-16 case 2.
  - Carrier: cxxmyv
- The `->reviewed` gate-only attestation rule (4.4 SR-601).
  - Carrier: 2xwb9b
- `leak_sanitizer` scanning `meta/*.jsonl` as text: it already scans every tracked file, so logs are scanned once they exist; no change needed (F-07). Recorded for the cutover check.
  - Carrier: cxxmyv

## Scope check

- Over-scope: none. `cli.py`, `command_surface.py`, `engine.py` and `tests/conformance_matrix.py` change only to register the new hook; `artifact_meta.py` changes only to add `check_staged_log_append` (E-05) and, if needed, to let `read_at` accept a merge-stage revision spelling (E-04), recorded in the finalize scope reconciliation if used; `reviews.py` changes only for its subject-resolution reads (E-11); `tests/test_artifact_audit_verdicts.py` and `tests/test_plans_index.py` change only in D-1 assertions; the spec changes only by the E-05 function-list entry.
- Under-scope: none known; E-01 and E-15 exist to find what the measurement missed. Plan size: 16 E-items in 5 task groups (limits 18 and 5).

## Required tests / validation

New test modules: `tests/test_readers_read_at_gates.py`, `tests/test_readers_runner.py`, `tests/test_readers_record_modules.py`, `tests/test_readers_review_modules.py`, `tests/test_meta_log_append_gate.py`, `tests/test_readers_gate_cache_parity.py`. All mark `core` except where real multi-commit git fixtures exceed the core budget (then `slow`, with the reason in the module docstring). All build `tmp_path` fixture repositories with real `git init`, call real functions or the `aw` CLI hook leaves, assert on exit codes and outputs, and never read production source.

Acceptance criteria of `4sd62s` this plan OWNS jointly with `ffceq0` (the split table in `ffceq0` `## Required tests / validation` is authoritative):

| AC | This plan's part |
|---|---|
| AC-1a | the setter and pre-commit gate cases across cold, warm, deleted and corrupt caches; staged external edit visible; invalid staged record fails closed (E-13) |
| AC-9 (reader parts) | `plans_index`, `research_index` and `prompts_index` readers answer from the cache, so no reader depends on an INDEX file (E-09, E-10); deletion is Order 11 |
| AC-12 | a setter and a gate with no model launcher and no network (E-14) |

CONTRIBUTES to: AC-16 (the hooks read through `read_at`, and the new append hook exists; final proof on the cutover commit by `cxxmyv`), AC-33 (gate-level `read_at` use after a rename; owned by `tve77h`), AC-21 row `l56tyz` (pasted `tests/test_readiness_absence_invariant.py`; AC-21 is owned by `xexn45`), AC-1 (residual audit F-04; owned by `9o83cr`), AC-3 and AC-17 (merge-path readers through `read_at`; owned by `xexn45` and `tve77h`).

Commands: every module named in E-02 to E-14 and E-16, the bare core gate `python3 -m pytest`, `make test-all`, `aw check`, `aw sanitize --agent`.

## Spec / documentation sync

ONE spec amendment: `4sd62s` 4.3 gains `check_staged_log_append(id6) -> list[str]` in its function list (E-05). Reason: 4.3 says no code outside the loader opens a log, and 4.8 requires a hook that judges staged log bytes, so the judgement must be an `artifact_meta` function and the spec's interface list must name it. The amendment adds a function and changes no rule. Implements `4sd62s` 4.4 (`read_at` consumers, the re-run search, finalize own-log scope), 4.8 (the `meta/*.jsonl` append hook), C5a for gates, hooks and runners, and section 7 step 5 (second half). `CHANGELOG.md` gains a line for the new optional hook; the managed block and quickstarts describing hooks change only at the cutover (Order 12, `90iqr1`).

## Open questions

### OQ-01: Does this plan depend on Order 08?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: Yes. The brief names `tve77h` and `xexn45` as the dependencies; this plan also needs `artifact_meta.read_text` and the D-1 status rule, both introduced by `ffceq0`, and it moves `runner_shared` callers of `selectors.read_front_matter_*`, which `ffceq0` rewrites. So `- Item-Dependencies:` adds `executed:ffceq0`. If the coordinator moves `read_text` into `tve77h`, the edge can still stay, because D-1 lives in `ffceq0`. Recommendation strength: strong.

### OQ-02: How does `read_at` serve a merge-stage blob (`:<stage>:<path>`)?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `tve77h` E-14 defines `read_at` for the index (`git ls-files -s`) and commits (`git rev-parse <rev>:<path>`). A merge stage is an index entry with a stage number, which `git ls-files -s` already lists, so E-04 first tries `read_at(id6, ":<stage>:")`; if `tve77h`'s implementation rejects a stage spelling, E-04 passes the stage blob text (from `runner_shared.read_merge_stage`) to `artifact_meta.read_text`, which uses the same loader. Either path keeps C5a (one loader). The chosen path is recorded in F-03. Recommendation strength: medium.

### OQ-03: Should the plan be split?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: No: 15 E-items in 5 task groups, within limits (16 after the 2026-11-05 banner item, F-09). If execution finds E-07 (the runner move) too large, split it into E-07a (`parse_plan_file`, `discover_*`, `edge_satisfied`) and E-07b (the remaining `execute_item_core`/`initialize_run_core`/review-sequence reads), which keeps the plan at 16. Recommendation strength: medium.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.
- [ ] V-01 validates E-01
  - Required evidence: paste the exact `rg` command of E-01 with its full output line count, and the F-03 table written into this plan with one row per hit and a class column (metadata reader / path-only / not a metadata read); every metadata-reader row names the E-item (E-02, E-03 or E-04) that moves it; and `ls -l .aw/state/t4gl15/check-before.txt .aw/state/t4gl15/index-before.txt`.
  - Observed evidence:
  - Result: pending

- [ ] V-02 validates E-02
  - Required evidence: paste `git diff --stat agent_workflows/check_engine.py` empty before the move, then `python3 -m pytest -o addopts="" -v tests/test_readers_read_at_gates.py -k check_engine` all PASSED (untooled flip refused, tooled flip accepted, staged rename into `executed/`, illegal backlog transition, release-blocking done with and without handoff) and `diff .aw/state/t4gl15/E-02-before.txt .aw/state/t4gl15/E-02-after.txt` (outcome lists of `tests/test_check_engine_status_meta.py tests/test_check_engine_release_gate.py tests/test_precommit_scope_gate_severity.py tests/test_backlog_close_gate_prose.py`) printing nothing; paste `rg -n "_blob_text\(" agent_workflows` showing only the definition.
  - Observed evidence:
  - Result: pending

- [ ] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_read_at_gates.py -k hook` all PASSED, each test driving the real `aw ipd-executed-gate`, `aw ipd-status-untooled-gate`, `aw backlog-blocking-close-gate` or `aw ipd-dependency-statement-gate` leaf on a staged fixture and asserting the exit code; `diff .aw/state/t4gl15/E-03-before.txt .aw/state/t4gl15/E-03-after.txt` (outcome lists of `tests/test_executed_transition_gate.py tests/test_executed_transition_gate_e2e.py tests/test_ipd_dependency_statement_gate.py`) printing nothing; and `rg -n "\^-|\"show\"" agent_workflows/hooks/` showing no metadata regex or record `git show`.
  - Observed evidence:
  - Result: pending

- [ ] V-04 validates E-04
  - Required evidence: paste `diff .aw/state/t4gl15/E-04-before.txt .aw/state/t4gl15/E-04-after.txt` (outcome lists of `tests/test_review_staleness_advisory.py tests/test_ipd_lifecycle_cli.py tests/test_records_only_lane_rederive.py tests/test_runner_backlog_close_behavior.py tests/test_merge_conflict_sendback.py`) printing nothing, the same diff for `tests/test_status_set.py -k untooled` showing 5 or more selected tests, the new HEAD-status setter case PASSED, and the F-03 row recording which merge-stage path (`read_at` stage spelling or `read_text`) was used (OQ-02).
  - Observed evidence:
  - Result: pending

- [ ] V-05 validates E-05
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_meta_log_append_gate.py` all PASSED with five named tests (valid append accepted; rewritten line, deleted line, invalid appended event and bad first event each refused with exit 1 and a message naming the log), a test asserting the hook delegates to `artifact_meta.check_staged_log_append` (a fixture whose staged log the loader refuses is refused by the hook with the loader's reason); and `aw meta-log-append-gate; echo $?` on this checkout printing 0.
  - Observed evidence:
  - Result: pending

- [ ] V-06 validates E-06
  - Required evidence: paste `git diff --stat agent_workflows/runner_shared.py agent_workflows/oc_runipd.py agent_workflows/agy_runipd.py` empty, `python3 -m pytest -o addopts="" -v tests/test_readers_runner.py` all PASSED on the unmodified code (including the `l56tyz` missing-readiness refusal), `wc -l` of the ten baseline modules' outcome list `.aw/state/t4gl15/E-06-before.txt`, and `wc -l .aw/state/t4gl15/discover-before.txt`.
  - Observed evidence:
  - Result: pending

- [ ] V-07 validates E-07
  - Required evidence: paste `diff .aw/state/t4gl15/E-06-before.txt .aw/state/t4gl15/E-07-after.txt` printing nothing or only lines D-1 names, `git diff tests/` showing only D-1 assertions, and `diff .aw/state/t4gl15/discover-before.txt <(python3 -c '<the E-07 snippet>')` printing only the D-1 status lines (each named).
  - Observed evidence:
  - Result: pending

- [ ] V-08 validates E-08
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_runner.py -k own_log` PASSED, asserting that a finalize-scope fixture changing `.aw/records/meta/<own id6>.jsonl` is in scope while a change to another plan's log is reported out of scope.
  - Observed evidence:
  - Result: pending

- [ ] V-09 validates E-09
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_record_modules.py -k plans` all PASSED, `diff .aw/state/t4gl15/E-09-before.txt .aw/state/t4gl15/E-09-after.txt` (outcome lists of `tests/test_plans_index.py tests/test_plans_archive.py tests/test_plans_archive_selectors.py tests/test_ipd_set_plan.py tests/test_completion.py`) printing nothing or only D-1 lines, `aw index plans --check; echo $?` compared with `.aw/state/t4gl15/index-before.txt`, and the empty output of `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/plans_index.py agent_workflows/plans_archive.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-10 validates E-10
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_record_modules.py -k "research or prompt"` all PASSED, `diff .aw/state/t4gl15/E-10-before.txt .aw/state/t4gl15/E-10-after.txt` (outcome lists of `tests/test_research_index.py tests/test_research_archive.py tests/test_research_companion.py tests/test_prompts_index.py tests/test_index_check_agent_records.py`) printing nothing, and `aw index research --check; echo $?` and `aw index prompts --check; echo $?` compared with `.aw/state/t4gl15/index-before.txt`.
  - Observed evidence:
  - Result: pending

- [ ] V-11 validates E-11
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_review_modules.py -k "review_findings or audit"` all PASSED, `diff .aw/state/t4gl15/E-11-before.txt .aw/state/t4gl15/E-11-after.txt` (outcome lists of `tests/test_review_findings_gate.py tests/test_spec_review_attestation.py tests/test_artifact_audit.py tests/test_artifact_audit_verdicts.py tests/test_artifact_audit_identity_staleness.py`) printing nothing or only D-1 lines, and the sorted `check.spec-review-unattested` locations from `aw check specs --agent` before and after with an empty diff.
  - Observed evidence:
  - Result: pending

- [ ] V-12 validates E-12
  - Required evidence: paste `diff .aw/state/t4gl15/E-12-before.txt .aw/state/t4gl15/E-12-after.txt` (outcome lists of the nine modules named in E-12) printing nothing, `tests/test_readers_review_modules.py` all PASSED, and the empty output of `rg -n "re\.\w+\(\s*r?[\"'](\(\?m\))?\^-" agent_workflows/review_sequence.py agent_workflows/review_tier.py agent_workflows/review_rereview.py agent_workflows/orchestrator_readiness.py agent_workflows/production_checks.py agent_workflows/work_cmd.py agent_workflows/artifact_adopt.py`.
  - Observed evidence:
  - Result: pending

- [ ] V-13 validates E-13
  - Required evidence: paste `python3 -m pytest -o addopts="" -v --durations=0 tests/test_readers_gate_cache_parity.py -k parity` with every (command x cache state) test PASSED for the setter and the three gate leaves across the four cache states, the staged external-edit test, and the invalid staged record test asserting a non-zero exit naming the record; and the module's marker (`core` or `slow` with the docstring reason).
  - Observed evidence:
  - Result: pending

- [ ] V-14 validates E-14
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_gate_cache_parity.py -k offline` with both tests PASSED, each asserting exit 0 with host binaries removed from `PATH` and sockets disabled.
  - Observed evidence:
  - Result: pending

- [ ] V-15 validates E-15
  - Required evidence: paste the two `rg` commands of E-15 and the F-04 table (every remaining hit with its owner, none unowned); the bare `python3 -m pytest` summary line and wall time; the `make test-all` summary line; `aw check all --agent` rule-id counts diffed against `.aw/state/t4gl15/check-before.txt` (empty, or each difference traced); the `aw sanitize --agent` result with zero `fail`; and every `aw commit t4gl15` output listing only Scope-Paths (or paths justified at finalize).
  - Observed evidence:
  - Result: pending
- [ ] V-16 validates E-16
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_readers_record_modules.py -k banner` with six tests PASSED (`unrun`, `partial`, `synthesized` for the banner shape and for the no-banner shape), each asserting the position `derive_pipeline_positions` returns for its `tmp_path` tree; and `aw index research --check; echo $?` on this checkout with the same exit code as `.aw/state/t4gl15/index-before.txt`.
  - Observed evidence:
  - Result: pending



## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `tve77h`, `xexn45` and `ffceq0` are executed. Open questions: OQ-01 to OQ-03 are resolved and none is blocking.

Scope fence: the paths in `- Scope-Paths:` are a declaration; a needed file outside the fence is edited and then justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). Every reader move is pin-first (the named baseline modules run green on the unmodified code before the move), and a test edited after a move must be one that D-1 to D-4 name.

Honesty rule: run the named modules, `python3 -m pytest` (core gate) and `make test-all`, and paste the ACTUAL summary lines; never claim a result you did not run.

Commits: commit only through `aw commit t4gl15 -- <paths>`; never `git add -A`, a bare `git add` or `git commit -a`; never push.

Lifecycle transition: the plan moves to `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`, and only after `aw ipd lint --phase pre-transition` conforms and every `V-*` reads `pass` with pasted evidence. When `aw oc run` or `aw agy run` executes the plan, the runner performs the finalize; a hand executor runs `aw ipd finalize t4gl15` itself.
