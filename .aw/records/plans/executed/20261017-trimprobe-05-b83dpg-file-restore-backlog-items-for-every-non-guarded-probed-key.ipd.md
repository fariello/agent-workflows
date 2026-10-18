# IPD: File restore backlog items for every non-guarded probed key and reconcile the 319

- Date: 2026-10-17
- Kind: child
- Concern: Backlog `lrnh5f`'s remedy has two halves: probe the 319 budget-exhausted keys, then restore behavioral test coverage where the probe shows the surviving suite does not guard a key. Orders 01 to 04 produce the verdicts; which keys need restoring, and therefore what tests to write, is unknown until they run, so the restore work cannot be specified as test-writing steps today. Without a filing step the probe results would sit in a findings doc that `aw attention` does not surface, and the restore half of `lrnh5f` would be silently dropped.
- Scope: IN: group every key whose final verdict in `## Budget probe results` or `## Probe queue` is not carrier-free, dedupe against live backlog, file one `trimgap` backlog item per module group (top 15 by key count, the rest in one residual item), and write `## Filed items` and `## Reconciliation` accounting for all 319 keys. OUT: writing any test (each filed item's own work); editing any existing backlog item, including `lrnh5f`; any code or test edit.
- Scope-Paths: .aw/records/backlog/**/*-trimgap-*.backlog.md, .aw/records/research/*-trimprobe-01-*.findings.md
- Item-Dependencies: executed:g00ljy, executed:lictgf, executed:f4pbs5, executed:pr6lo9
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: lrnh5f
- Set: trimprobe
- Order: 5
- Highest E allocated: 03
- Author: opencode
- Id: b83dpg

## Workflow history
- 2026-10-18 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: b83dpg verified (set trimprobe, attempt 2).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006

- 2026-10-17 to-review (opencode): authored review-ready child of Set `trimprobe` graduating backlog `lrnh5f`.
- 2026-10-17 draft (opencode): created.

## Goal

Each of the 319 keys ends either carrier-free on evidence (`guarded`, `key-gone`) or carried by a specific live backlog item that names the key, its verdict, and the deleted test file to mine.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Gaps and dedupe

- [x] E-01 FIRST, before any filing, capture the per-rule counts of `aw check --agent` (rule and severity of every diagnostic) into the gitignored `.aw/state/trimprobe-b83dpg/check-before.jsonl`, which E-03 (d) compares against (the `z2xs98` E-01 precedent). Then, from the Set doc, collect every key with final verdict `unguarded`, `unguarded-unreached`, `unprovable` or `budget-exhausted` (from `## Budget probe results`, and for the no-probe classes from `## Probe queue`); `guarded` and `key-gone` are CARRIER-FREE and are not grouped. Group the gaps by (module, remedy shape), as `z2xs98` did, so each group has exactly one Remedy Shape. For each group, DEDUPE by searching live backlog and pending plans for each key's qualified name (`rg -l -F '<module>::<qualname>' .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/plans/pending`), IGNORING hits in this Set's own artifacts (backlog `lrnh5f` and every `*-trimprobe-*` plan), which name keys as inputs or examples rather than owning them (at review, `g00ljy` names `comms.py::validate_ack` and `ipd_schema.py::_parse_item_dependency_edge` in its Findings, Findings F-04): a key named by any other live item is `owned-confirmed` with that item's id6 and is removed from the group. `aw backlog new`'s duplicate-candidate report in E-02 is a second, advisory check. Write `## Filing plan` (columns as `b1mx2w` `## Filing plan`: Group, Module, Keys covered, Counts, Remedy Shape, Dedupe Judgement, Work-Kind, Priority, Justification, Action), ranked by gap key count descending; top 15 `filed`, the rest `rolled-up`. Remedy shape: `restore behavioral coverage` for `unguarded`/`unguarded-unreached`, `investigate probe` for `unprovable`, `probe then restore` for `budget-exhausted`.
  - Depends on: none
  - Expected outcome: every gap key is in exactly one group or is `owned-confirmed`.
  - Execution state: performed

### Task group 2: Filing

- [x] E-02 For each `filed` group, and once for the residual, run `aw backlog new --summary "<...>" --set trimgap --priority low --work-kind chore --body "<keys covered with verdict and operator; Set doc id6 and section; deleted test files to mine: the queue's control files plus hpjj44 ## Derived properties; source 19313eed^; carried from lrnh5f via plan b83dpg>" --apply`, pasting each output. Work-Kind is `chore` and no `--blocks-release` is set because an absent or unasserted test is not a user-visible wrong behavior (the `b1mx2w` `## Filed items` precedent and `lrnh5f` itself, which carries no gate). EXCEPTION: for every probe JSON with `baseline_failing` > 0 (the JSON records only the count, `tools.mutation_probe.ProbeResult`), re-run its `selection` unmutated at `git rev-parse HEAD` with `python3 -m pytest -o addopts= -q -p no:randomly <selection>` and paste the failing node ids (or `none`); a test that fails there is a live regression: file it as its own `--work-kind bug --blocks-release next` item (never rolled up), per `AGENTS.md` "Every live bug gates the next release". Write `## Filed items` listing each id6, path, group, Work-Kind, Priority and summary.
  - Depends on: E-01
  - Expected outcome: one item per filed group plus at most one residual; paths listed.
  - Execution state: performed

### Task group 3: Reconciliation and commit

- [x] E-03 Write `## Reconciliation`: (a) a table mapping all 319 keys by final verdict to a filed id6, an `owned-confirmed` id6, or carrier-free, summing to 319; (b) a per-partition wall-time table (`P2`, `P3`, `P4` totals from the subtotal lines); (c) for each of `g00ljy`, `lictgf`, `f4pbs5`, `pr6lo9`: `git log --format='%h %p %s' --grep='(<id6>)' --grep='lane <id6> ' HEAD`, then for each listed commit `git diff --stat <hash>^1 <hash> -- agent_workflows tests` (the `^1` form, because `git show --stat` prints nothing for a merge commit, so the `integrate(...) merge verified lane` commits would pass vacuously), showing the Set's own commits changed no code or test file (a plain `git log <Order 01 commit>^..HEAD -- agent_workflows tests` range is NOT used: other Sets merge to main in the same window, and their code commits would falsely appear, Findings F-04); (d) `aw check --agent` per-rule counts now versus `check-before.jsonl`, explaining any NEW finding that names a file this plan wrote and fixing it with the owning `aw backlog` or `aw research` verb. Run `aw research index` (backlog has no index: `aw index backlog` prints `'index' is not supported for backlog`), then commit only the doc and the new backlog items with `aw commit <this plan> -- <doc path> <each new backlog path>`.
  - Depends on: E-02
  - Expected outcome: reconciliation sums to 319; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Backlog items are created only with `aw backlog new` (`AGENTS.md` "What needs attention"); `TODO.md` is not a work surface.
- Executed `z2xs98` (Set `trimcarry` Order 06) is the precedent for grouping, the 15-item cap with a residual, `chore`/`low` defaults and the regression-as-bug exception.
- Records are declared by glob in Scope-Paths (`.aw/records/plans/README.md` "Declaring records in Scope-Paths").
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `b1mx2w` `## Filing plan` and `## Filed items` | The prior Set filed 15 per-module `trimgap` items plus residual `q86fxm`; `lrnh5f` itself is group 1. |
| F-02 | Authoring check: each of the 319 qualified key names searched in every other `trimgap` backlog item and pending `trimgap` plan | No other item or plan names any of the 319 keys today, so dedupe is expected to find little; it is still re-run at execution because items may be filed meanwhile. |
| F-03 | `rf1xxr` totals in `b1mx2w` `## Rollup mutation totals` | Of 37 keys probed there, 30 were `guarded`, 2 `unguarded`, 1 `unprovable`: most reached keys are expected to be carrier-free, so the filed set should be far smaller than 319. |
| F-04 | Review checks at HEAD `789e1ace5` | (1) The 319 qualified key names searched in `backlog/open`, `backlog/graduated` and `plans/pending` hit only `g00ljy` (2 keys, cited as calibration examples); `lrnh5f` and the other `trimprobe` plans name none. (2) `aw find backlog storage` -> `no artifact matched selector 'storage'`: `find` matches id6, status, Set or filename, not body text, so it is not a key-level dedupe. (3) `aw index backlog` -> `WARN 'index' is not supported for backlog.` (4) Main also carries other Sets' code commits (for example `work(c8bfp9)`) interleaved with this Set's merges, so a commit range cannot prove the Set changed no code. (5) `aw check --agent` has pre-existing findings (2 errors, 2 warnings, 103 info at review), so only a before/after delta is meaningful. (6) For the precedent merge `942486446` (`integrate(aw agy run): merge verified lane rf1xxr to main`), `git show --stat` printed nothing while `git diff --stat 942486446^1 942486446` printed `3 files changed, 1227 insertions(+), 134 deletions(-)`, so a merge must be diffed against its first parent. (7) `aw backlog new ... --set trimgap --priority low --work-kind chore` previews `.aw/records/backlog/open/<date>-trimgap-01-<id6>-<slug>.backlog.md`, matching the Scope-Paths glob. |

## Proposed changes (ordered, validatable)

1. E-01 collects, dedupes and groups gaps.
2. E-02 files items.
3. E-03 reconciles and commits.

## Deferred / out of scope (with reason)

- Writing the restored tests: each filed item's own graduation and plan, as for the 15 `b1mx2w` items; the target tests are unknowable before the probes run.
  - Carrier-Declined: no work is lost; every non-carrier-free key is named by a filed or owned item in E-03 (a).

## Scope check

- Over-scope: none. New backlog items under `trimgap` and the Set doc; no existing item edited.
- Under-scope: none. E-03 (a) accounts for all 319 keys.

## Required tests / validation

- Reconciliation sums to 319; every filed path exists; `aw backlog check` and `aw check` report no new error.

## Spec / documentation sync

N/A: records only; no `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore tests inside this Set, or file restore items?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: file items. A restore plan must name the keys, the deleted file to mine and the assertions that kill each mutant (sibling plans `syzi9i`, `33f8tn`), none of which exists until Orders 02 to 04 run. This matches how `z2xs98` carried `trimcarry`'s gaps.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the line count of `check-before.jsonl` and its timestamp showing it predates the first `aw backlog new --apply`; paste per-verdict gap counts, the dedupe search outputs with each `owned-confirmed` key and id6 (or `none`) and any ignored Set-own hits, and the `## Filing plan` table.
  - Observed evidence:
    ~~~text
    - Line count of `check-before.jsonl`: 6 lines
    - Timestamp: 2026-10-18 05:33:36.183122362 -0400 (2026-10-18T09:33:36.184052+00:00 UTC), strictly predating the first `aw backlog new --apply` executed at 2026-10-18 05:35:41 -0400.
    - Per-verdict gap counts (from Set doc `wo21z5` `## Budget probe results` and `## Probe queue`):
      - `budget-exhausted`: 64 keys
      - `unguarded`: 18 keys
      - `unprovable`: 17 keys
      - `unguarded-unreached`: 2 keys
      - Total gap keys: 101 keys. (Carrier-free: `guarded`: 218 keys, `key-gone`: 0 keys; Total candidate keys: 319).
    - Dedupe search outputs:
      - Command: `rg -l -F '<module>::<qualname>' .aw/records/backlog/open .aw/records/backlog/graduated .aw/records/plans/pending`
      - `owned-confirmed`: none (0 keys)
      - Ignored Set-own hits:
        `agent_workflows/ipd_schema.py::_parse_item_dependency_edge`: `.aw/records/plans/pending/20261017-trimprobe-05-b83dpg-file-restore-backlog-items-for-every-non-guarded-probed-key.ipd.md` (IPD b83dpg itself)
    - `## Filing plan` table:

    Grouped filing plan for every non-guarded key from the 319 budget-exhausted candidate keys (Set `trimprobe`, Order 05 `b83dpg`). Groups are ranked by gap key count descending. The top 15 groups are filed individually under `--set trimgap`; all remaining groups (ranks 16 through 52) are rolled into a single residual rollup backlog item.

    | Group | Module | Keys covered | Counts | Remedy Shape | Dedupe Judgement | Work-Kind | Priority | Justification | Action |
    |---|---|---|---|---|---|---|---|---|---|
    | 1 | `agent_workflows/check_engine.py` | `check_ipd_draft_ready`, `check_plan_priority_required`, `check_review_decision_unescalated`, ... (10 keys) | 10 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 2 | `agent_workflows/run_analytics_telemetry.py` | `ResourceSampler.__init__`, `ResourceSampler.start`, `ResourceSampler.stop`, ... (8 keys) | 8 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 3 | `agent_workflows/run_analytics_spa.py` | `_render_findings`, `_render_pricing`, `_render_refusals`, ... (5 keys) | 5 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | filed |
    | 4 | `agent_workflows/ipd_lifecycle.py` | `_baseline_ambiguity`, `begin`, `_execution_cohesive_committed_paths`, ... (4 keys) | 4 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 5 | `agent_workflows/run_analytics_telemetry.py` | `_validate_label_list`, `_validate_tool_versions`, `node_pseudonym`, ... (4 keys) | 4 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
    | 6 | `agent_workflows/run_evidence.py` | `validate_evidence`, `_porcelain_paths`, `dirty_within`, ... (4 keys) | 4 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 7 | `agent_workflows/attention.py` | `_shared_gate_ref`, `render_table`, `_render_table_row` | 3 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 8 | `agent_workflows/benchmark_manifest.py` | `BenchmarkManifest.digest`, `Ceilings.digest`, `_digest` | 3 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | filed |
    | 9 | `agent_workflows/record_history.py` | `_endpoint_id6`, `append_rename`, `record_rename` | 3 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 10 | `agent_workflows/run_analytics_findings.py` | `assert_no_causal_language`, `build_finding`, `findings_from_results` | 3 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
    | 11 | `agent_workflows/runner_shared.py` | `spec_impacts_for_queue`, `expand_selectors`, `route_recovery_turn` | 3 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 12 | `agent_workflows/benchmark_corpus.py` | `SeededTask.workspace_seed_path`, `load_corpus` | 2 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | filed |
    | 13 | `agent_workflows/benchmark_runners.py` | `TrialResult.to_dict`, `RunnerAdapter.adapter_digest` | 2 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | filed |
    | 14 | `agent_workflows/config.py` | `findings_gate_threshold`, `read_review_findings_gate` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 15 | `agent_workflows/ipd_lint.py` | `lint_file`, `check_item_dependencies` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | filed |
    | 16 | `agent_workflows/ipd_schema.py` | `_parse_item_dependency_edge`, `parse_item_dependencies` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 17 | `agent_workflows/plans_refs.py` | `apply_renames`, `_dirs` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 18 | `agent_workflows/render_stream.py` | `Palette.status`, `_status_glyph_char` | 2 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 19 | `agent_workflows/result_types.py` | `CommandResult.to_agent_record`, `select_output` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 20 | `agent_workflows/run_analytics_config.py` | `_coerce_bool`, `parse_telemetry_settings` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 21 | `agent_workflows/term.py` | `stdin_is_interactive`, `is_interactive` | 2 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 22 | `agent_workflows/agent_schema.py` | `validate_agent_record` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 23 | `agent_workflows/artifact_rename.py` | `_existing_type_id6s` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 24 | `agent_workflows/attention.py` | `_gate_ref_display` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 25 | `agent_workflows/backlog.py` | `run_new` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 26 | `agent_workflows/benchmark_ablations.py` | `AblationTrialSpec.cell_key` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 27 | `agent_workflows/benchmark_manifest.py` | `BenchmarkManifest.to_dict` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 28 | `agent_workflows/benchmark_metrics.py` | `MetricSummary.to_dict` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 29 | `agent_workflows/benchmark_thresholds.py` | `GateEvaluationResult.to_dict` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 30 | `agent_workflows/check_engine.py` | `_review_index` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 31 | `agent_workflows/check_engine.py` | `check_push_authorization` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 32 | `agent_workflows/cli.py` | `_dispatch` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 33 | `agent_workflows/comms.py` | `validate_envelope_header` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 34 | `agent_workflows/doctor.py` | `_infer_artifact_type` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 35 | `agent_workflows/engine.py` | `resolve_source_root` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 36 | `agent_workflows/engine.py` | `migrate_local_lanes_to_untracked` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 37 | `agent_workflows/ipd_lifecycle.py` | `classify_commit_refusal` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 38 | `agent_workflows/leak_sanitizer.py` | `scan_text` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 39 | `agent_workflows/plan_readiness.py` | `cite_review_entry` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 40 | `agent_workflows/project_context.py` | `_resolve_effective_aw_home` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 41 | `agent_workflows/render_stream.py` | `format_spec_impact_announcement` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 42 | `agent_workflows/renderers.py` | `BaseRenderer.emit` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 43 | `agent_workflows/research_cmd.py` | `build_frontmatter` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 44 | `agent_workflows/research_contract.py` | `validate_frontmatter` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 45 | `agent_workflows/run_analytics_privacy.py` | `_project_number_map` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 46 | `agent_workflows/run_analytics_telemetry.py` | `TelemetryCollector._observe_tool_versions` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 47 | `agent_workflows/run_ledger_schema.py` | `validate_record` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 48 | `agent_workflows/runner_shared.py` | `attributed_away_failure_ids` | 1 keys | restore behavioral coverage | non-owned | chore | low | Absent behavioral test coverage without observed regression is chore with low priority by default. | rolled-up |
    | 49 | `agent_workflows/selectors.py` | `resolve_for_mutation` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 50 | `agent_workflows/storage.py` | `get_git_common_dir` | 1 keys | investigate probe | non-owned | chore | low | Investigation of probe applicability for unprovable keys is chore with low priority by default. | rolled-up |
    | 51 | `agent_workflows/verify_roles.py` | `check_role_action` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    | 52 | `agent_workflows/worktree_lease.py` | `lane_id_from_branch` | 1 keys | probe then restore | non-owned | chore | low | Deferred mutation probing and test restoration for unprobed keys is preventive maintenance; no live regression observed. | rolled-up |
    ~~~
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste every `aw backlog new` output; paste `ls` of each new path; paste `aw backlog check` output; paste the `baseline_failing` re-run output for every JSON with a non-zero count (or state that none had one).
  - Observed evidence:
    ~~~text
    - Pasted outputs of every `aw backlog new ... --apply` command:
    ```
    === [1/16] Group 1 (agent_workflows/check_engine.py) -> lzg859 ===
    Summary: Probe then restore behavioral test coverage for check_engine
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - jys5dp [done]: a known unfixed defect named in an IPD's prose vanishes when the plan reaches executed: require handoff to a durable carrier, mirroring the release-gate close predicate
      - wxgu55 [done]: tests/test_review_decisions.py proves wiring-exactly-once by counting a symbol's occurrences in check_engine.py source text, so any prose mention of that symbol fails it
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-lzg859-probe-then-restore-behavioral-test-coverage-for-ch.backlog.md

    === [2/16] Group 2 (agent_workflows/run_analytics_telemetry.py) -> zd8l04 ===
    Summary: Probe then restore behavioral test coverage for run_analytics_telemetry
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - xelvyi [done]: The sole-blocking-caller guard was a text search a docstring could trip, so it went red against a correct tree
      - yqpb7q [done]: Restore behavioral test coverage for run_analytics_telemetry
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-zd8l04-probe-then-restore-behavioral-test-coverage-for-ru.backlog.md

    === [3/16] Group 3 (agent_workflows/run_analytics_spa.py) -> aaud70 ===
    Summary: Investigate probe applicability for run_analytics_spa
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - 4vn040 [done]: test_turn_bounds isolation-scoped permission policy test fails inside a runner lane because OPENCODE_CONFIG_CONTENT is ambient
      - rd2yh7 [done]: Audit tests that derive leak-detector fixture input from Path(__file__) so no other test asserts a property of its own checkout location
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-aaud70-investigate-probe-applicability-for-run-analytics.backlog.md

    === [4/16] Group 4 (agent_workflows/ipd_lifecycle.py) -> gcpj15 ===
    Summary: Probe then restore behavioral test coverage for ipd_lifecycle
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - a8eufb [done]: finalize still demands a scope reason for a CONCURRENT agent's COMMITTED out-of-scope path (the committed half of the shared-checkout attribution defect)
      - 5h1lxs [done]: planprio lkexaw under-declares its scope: enforcing Priority and Work-Kind at the ready-to-execute gate breaks 175 tests across 21 undeclared test files, so the verifier correctly refused it
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-gcpj15-probe-then-restore-behavioral-test-coverage-for-ip.backlog.md

    === [5/16] Group 5 (agent_workflows/run_analytics_telemetry.py) -> gmfupc ===
    Summary: Restore behavioral test coverage for run_analytics_telemetry
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - xelvyi [done]: The sole-blocking-caller guard was a text search a docstring could trip, so it went red against a correct tree
      - yqpb7q [done]: Restore behavioral test coverage for run_analytics_telemetry
      - zd8l04 [open]: Probe then restore behavioral test coverage for run_analytics_telemetry
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-gmfupc-restore-behavioral-test-coverage-for-run-analytics.backlog.md

    === [6/16] Group 6 (agent_workflows/run_evidence.py) -> i2g20d ===
    Summary: Probe then restore behavioral test coverage for run_evidence
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-i2g20d-probe-then-restore-behavioral-test-coverage-for-ru.backlog.md

    === [7/16] Group 7 (agent_workflows/attention.py) -> 1n4qco ===
    Summary: Probe then restore behavioral test coverage for attention
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-1n4qco-probe-then-restore-behavioral-test-coverage-for-at.backlog.md

    === [8/16] Group 8 (agent_workflows/benchmark_manifest.py) -> g5ypvb ===
    Summary: Investigate probe applicability for benchmark_manifest
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-g5ypvb-investigate-probe-applicability-for-benchmark-mani.backlog.md

    === [9/16] Group 9 (agent_workflows/record_history.py) -> hrz4cv ===
    Summary: Probe then restore behavioral test coverage for record_history
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-hrz4cv-probe-then-restore-behavioral-test-coverage-for-re.backlog.md

    === [10/16] Group 10 (agent_workflows/run_analytics_findings.py) -> 6ntz8v ===
    Summary: Restore behavioral test coverage for run_analytics_findings
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - q86fxm [done]: Residual rollup of remaining uncited trim-deleted test audit gaps across 45 modules
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-6ntz8v-restore-behavioral-test-coverage-for-run-analytics.backlog.md

    === [11/16] Group 11 (agent_workflows/runner_shared.py) -> l2zsa9 ===
    Summary: Probe then restore behavioral test coverage for runner_shared
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - cnwy8g [done]: agy_runipd imports 40 names from oc_runipd, so the two host runners are not peers: a host driver depends on the other host's driver module, which the rununify shared library must correct rather than preserve
      - zt2b16 [done]: runner_shared carries its own diverged copy of classify_recovery_disposition and build_verify_and_continue_notice, so recovery routing has two disagreeing implementations
      - 4mdi4v [done]: Six execute_item_core getattr(driver_module, ...) fallbacks default to a shared definition that cannot satisfy the call site, so a host without its own copy gets TypeError instead of working behavior
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-l2zsa9-probe-then-restore-behavioral-test-coverage-for-ru.backlog.md

    === [12/16] Group 12 (agent_workflows/benchmark_corpus.py) -> 3hurk1 ===
    Summary: Restore behavioral test coverage for benchmark_corpus
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - g5ypvb [open]: Investigate probe applicability for benchmark_manifest
      - i2g20d [open]: Probe then restore behavioral test coverage for run_evidence
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-3hurk1-restore-behavioral-test-coverage-for-benchmark-cor.backlog.md

    === [13/16] Group 13 (agent_workflows/benchmark_runners.py) -> l9ssp6 ===
    Summary: Investigate probe applicability for benchmark_runners
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-l9ssp6-investigate-probe-applicability-for-benchmark-runn.backlog.md

    === [14/16] Group 14 (agent_workflows/config.py) -> yvmxs9 ===
    Summary: Probe then restore behavioral test coverage for config
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-yvmxs9-probe-then-restore-behavioral-test-coverage-for-co.backlog.md

    === [15/16] Group 15 (agent_workflows/ipd_lint.py) -> kkzvca ===
    Summary: Probe then restore behavioral test coverage for ipd_lint
    aw backlog new: no duplicate candidates detected.
      ADVISORY ONLY: this silence means nothing matched the signal, not that the defect is definitely new.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-kkzvca-probe-then-restore-behavioral-test-coverage-for-ip.backlog.md

    === [16/16] Residual Rollup (Groups 16-52) -> nzc6dm ===
    Summary: Residual rollup of remaining budget probe gaps across 37 module groups
    aw backlog new: candidate duplicate(s) detected (advisory only; creation proceeds):
      - vwios6 [done]: aw ipd set must support --blocks-release (release-gate parity with backlog and specs setters)
      - sr47pt [done]: Rename research status 'intake' -> 'todo' (intuitive 'you still need to do this'); migrate the 8 modules + existing docs; ride with 5tapom's state-advancement so 'todo' means genuinely-not-started
      - sjsoqq [done]: Enforce setid uniqueness across types (hard/prevented) + bidirectional graduation links (From-Backlog/From-Spec by id6, Graduated-To by setid); fix the agentadhere collision
      - p9o1oo [done]: Add a uniform Priority field (low|medium|high) to research/plans/specs (backlog already has it); attention already reads Priority - extend the field + setters + checks + board rendering across types
      - 1ap48y [done]: Add a uniform recognized-but-optional Work-Kind field (bug/feature/chore/... work-nature) to IPDs and specs, distinct from the structural Kind (orchestrator/child) and artifact type; enables cross-tree filtering of work by nature across backlog/plans/specs
      - suugsf [done]: installed agent contract never warns that other agents or humans share the checkout, so agents sweep others' uncommitted work into their own commits
      - l6rh0z [done]: begin's in-scope-dirty gate measures the MAIN tree for an isolated lane, so another agent's uncommitted edit to a commonly-scoped file (cli.py) withholds execution authority from an unrelated lane that would run clean at its frozen base
      - y9lcem [done]: The runner cannot read Item-Dependencies: oc_runipd matches only the legacy Dependencies/Depends-on field, so 11 pending plans declare edges the queue silently ignores and ordering falls back to Set/Order
      - 077yqc [done]: aw ipd finalize misattributes concurrent agents' uncommitted files to whichever plan finalizes first, because _paths_changed_by_this_execution unions the whole git status porcelain with no ownership filter
      - qzhfk2 [done]: Should specs get lifecycle subdirs? 24 specs sit intermixed in a flat tree while carrying a real 6-state lifecycle, 16 of them terminal
      - rxoazt [done]: No aw verb sets/removes dependencies for backlog items or specs, none removes a single edge, none accepts a setid target, and 'aw ipd dependencies set' accepts a dangling id6 pre-write (validated only later by aw check)
      - v880xk [done]: Decide how a begin receipt should behave when its frozen base goes stale: scope-drift emits ~1000 findings for plans that are not actually drifting
      - a8eufb [done]: finalize still demands a scope reason for a CONCURRENT agent's COMMITTED out-of-scope path (the committed half of the shared-checkout attribution defect)
      - wjl471 [done]: Commit guard that detects agent context from the environment and redirects to the tooled path: an accident-stopper, not a security boundary, plus wire the four existing gates that are currently invoked by nothing
      - h2ceme [done]: aw find renders a duplicate id6 as an ordinary multi-result list with exit 0, bypassing the resolver's own UNIQUE_KINDS collision policy; it must flag the violation and name the remedy
      - wx95o4 [done]: id6 is minted per-tree not globally, D140's identity-slot rule cannot catch a walkthrough that DECLARES a plan's id6, and the cross-type collision rule only runs in the full sweep
      - ila6vl [done]: DECIDED (maintainer 2026-08-31): stop tracking the four generated INDEX.json/INDEX.md manifests; gitignore and git rm --cached them, then reconcile the measured consumers (stale-index semantics, finalize owned_paths, auto-refresh self-commit, three docs, one test)
      - f8m2z2 [done]: re-author aw find as two-tier filesystem-first (maintainer ruling 2026-08-31 displaced e32j35's index-first design): filename listing 20ms vs 357ms, content fallback mandatory for status queries and 8 legacy records
      - tk1gqo [done]: aw check reports check.lifecycle-transition-invalid on conformant plans: _plan_status_events reverses inline history on a newest-first assumption while the repo's actual convention is oldest-first (9 diagnostics repo-wide, incl. approved plans)
      - egqt32 [done]: A mutating pre-commit hook (whitespace/eof fixer, formatter) rewrites a staged file and rejects, and offer_commit unstages and exits 1 instead of re-staging, so routine whitespace churn costs every agent a full commit round trip plus a mandated index re-verify
      - okm6e6 [done]: aw attention's no-project message never checks whether cwd is a git repo, so it reports where it looked but cannot offer the install that would fix it
      - isg0kg [done]: Every aw command should accept a uniform trio of presentation overrides: --no-color (exists on 59/60 top-level but missing from 9 nested host-driver subcommands), --color (force 256-color ANSI, no env var needed), and --tty (behave as if attached to an interactive TTY)
      - ydbhfd [done]: aw runs reports abandoned? for a crashed driver step whose outcome file on disk already records the real disposition: run_viewer flips running -> abandoned? on a dead lock holder without ever reading outcomes/*.json
      - d07nz2 [done]: RUN-BASELINE-OWNERSHIP and RUN-NO-PUSH land as names with no predicate; the machinery behind them is unbuilt
      - plbkp5 [done]: surface a plain count of waiting .aw/inbox/ drops in aw attention, by LISTING the directory only and never opening a file, so a forgotten drop is visible without inbox content ever being parsed
      - f1sw71 [done]: attention has no per-requirement spec tracking, so an approved spec can sit half-built with nothing asking which half: decide whether requirement-level tracking should exist
      - jys5dp [done]: a known unfixed defect named in an IPD's prose vanishes when the plan reaches executed: require handoff to a durable carrier, mirroring the release-gate close predicate
      - ld08f1 [done]: retire TODO.md as a work surface: it holds zero items, is scanned but silently dropped by attention, and two deferred specs still gate on it
      - v7u6vm [done]: releases is a declared tracked tree with no scan root, so release records are invisible to aw attention; the reviews tree has no policy at all
      - yocdq4 [done]: no way to re-integrate a verified lane without a full agent re-run, and resume re-dispatches finished work instead of merging it: add aw <host> integrate and call it from resume
      - r4qliv [done]: two lanes from run-20260905 remain unintegrated: cqx5v7 needs conflict resolution in both runners, i6015i never did its work and needs re-running
      - trjfyy [done]: spec 25kzda 2.1 retry/correction budget is dormant: plan_retry and retry_budget_remaining have zero production callers, so a failed run item gets no automatic correction attempt
      - ol8iyx [done]: wtiso retirement debt: the out-of-repo control-state relocation (Phase 4, 58ha43) has no successor plan, and six in-code pointers plus spec c4gd2h OQ-03 still name retired wtiso plans as the live owner of unbuilt work
      - 9yf5u9 [done]: aw doctor prints an unrunnable rename remediation: 'aw rename <type> <path>' exits 2 without --slug, and with --slug but no --apply it exits 0 having written nothing
      - adgtqb [done]: Every aw ipd finalize leaves the tracked plans manifests dirty: idxuntrack child 4r0qp1 removed INDEX.json from every commit path-set but child yvvf98 never untracked it, so HEAD's index goes stale while aw index plans --check reads disk and reports clean
      - imntrh [done]: Research status enum fits only answer docs: split pipeline position (derived, set-level) from shelf disposition, and let the research set own the prompt
      - lmjc8h [done]: check_collisions include_retired disagreement: aw doctor and aw check report different populations from one predicate
      - hdhzr2 [done]: aw doctor reads a nonexistent VERSION path (.aw/VERSION, .agents/VERSION) and reports 'not installed' on a correctly installed repo
      - x15f0q [done]: install --to-aw leaves empty legacy directories and .agents/README.md behind, so every migrated repo permanently reports a dual-layout split-brain and doctor advises a migration that already ran
      - lb5dzj [done]: aw oc run will re-execute an already-executed plan named by id6: determine_action maps executed to execute and no gate refuses it, so an agent turn is spent before finalize rejects the backwards transition
      - 7ts6ek [done]: finalize's commit-cohesion scope audit demands reasons for other plans' paths when several lanes share a hot file
      - ipfgl1 [done]: 31 tests fail at HEAD in the runner-harness modules (KeyError 'main_status_during_turn' and empty-dict assertions)
      - 770fkp [done]: 31 tests fail inside any runner lane because AW_EXECUTION_ROLE=worker refuses aw ipd begin/finalize
      - fci7yn [done]: Stranded-lane remedy says 'no aw integrate verb exists yet' though it shipped: lane_remedy_hint probes cmd_integrate, a symbol that does not exist
      - sovauj [done]: check.setid-collision reports a false cross-type collision when a walkthrough declares the Set of a plan still in pending/
      - 3f4ayi [done]: AgentRenderer.render_summary crashes whenever --fields is set
      - 57dwkc [done]: aw uninstall --deep orphans .aw/system/layout.json, so the no-.aw-remains promise fails
      - dtrect [done]: Deferred-section carrier subfields have no authoring or scaffold support, so an author must hand-write the typed field aw ipd scaffold does not emit
      - os1b9j [done]: aw install --source with a string path crashes: resolve_source_root calls .expanduser() on a str
      - a3ugp1 [done]: The approval gate refuses three pending reaskscore plans on a stale negative verdict, failing tests/test_plan_readiness.py at HEAD
      - lv92c6 [done]: Plan yaxr4i asserts the color engine is already correct and complete, which measurement falsifies
      - nyz8dt [done]: Unify the three divergent should_color implementations and stop FORCE_COLOR=0 forcing color on
      - 1zknu7 [done]: plans cite a spec id6 in prose without carrying - From-Spec:, so coverage is uncomputable for the specs where it matters: 37 plans mention c4gd2h and 0 carry the edge
      - 3sh9d6 [done]: The published `docs/cli-output-contract.md` non-TTY retraction is correct but plan 9iiqmm and its review both recorded the OPPOSITE as measured fact, so two artifacts assert a behavior that does not exist
      - 4y4xo5 [done]: aw group research clobbers each record Order to 0 when --order is omitted (the e3hzyc defect in research_refs)
      - 4znh53 [done]: Color-env tests race under xdist: NO_COLOR/FORCE_COLOR/TERM mutate process-global os.environ, so parallel workers cross-contaminate and a different color node fails per run
      - ccbe60 [done]: Subprocess CLI tests run from a worktree silently exercise the MAIN checkout, because the editable install pins an absolute path
      - ci9kx2 [done]: aw attention --dir <non-AW-directory> prints nothing and exits 0, so an explicitly named wrong directory looks like success
      - 0f809c [done]: Four check_engine test fixtures declared a Set contradicting their own filename, masking name-vs-metadata coverage
      - gyv9tf [done]: aw rename plans refuses a filename selector, so a suggested command built from a filename fails
      - q1ov25 [done]: status_set._ID_RE is a THIRD unbounded identity reader outside 76w6mq's declared scope, so a quoted - Id: is still read as a declaration after that plan lands
      - jb0sc1 [done]: Six live-corpus tests carry no livecorpus marker, so a third party's artifact can still red a lane's suite
      - xqm16x [done]: aw check's errors/warnings tally keys on the rule NAME prefix instead of the finding's severity, so every warning is counted as an error
      - zf999x [done]: A third FULL_AUTO_ACTOR in runner_shared disagrees with both host copies in value AND message, and nothing reads it, so consolidating the hosts onto it would silently rewrite every recorded actor and overstate what the gate proved
      - 0vbdll [done]: A lane worktree's own code is invisible to the installed 'aw', so an agent measures the main checkout and reports the wrong result
      - 19lmbe [done]: aw backlog set --status ignores --dry-run and mutates the tree, because the path-form handler reads a nonexistent 'apply' flag
      - 5x195l [done]: aw ipd --agent crashes with a schema ValueError in a non-project directory (exit_code=3 is unemittable)
      - lw1rhj [done]: test_artifact_audit VerdictParityTests::test_four_verdict_shapes failed once under random ordering and did not reproduce in four subsequent full runs
      - axayfn [done]: Three identity readers outside plan 76w6mq's fence are still unbounded to the metadata region
      - hd5bkk [done]: aw find reports a zero-match selector as CLEAN exit 0, the same fail-open aw attention just fixed
      - wxgu55 [done]: tests/test_review_decisions.py proves wiring-exactly-once by counting a symbol's occurrences in check_engine.py source text, so any prose mention of that symbol fails it
      - k0v9hs [done]: A comma-separated From-Backlog value resolves to NOTHING: the shared regex matches a single token to end of line, so every gate and check reading it sees no source at all
      - oii7hd [done]: run_viewer_cli reads args.dir directly instead of resolve_verb_repo_root, so aw runs cannot see a run from a subdirectory
      - p9ag41 [done]: test_defect_report's bare-except tripwire fails at HEAD: 894d7924 added 'except Exception: pass' inside the defect-report section of runner_shared.py
      - qztbeq [done]: A content conflict against a stale lane base is terminal on first attempt and nothing ever re-merges the lane onto current main, so a trivially resolvable additive conflict permanently strands verified work
      - uin96r [done]: The aw console script resolves agent_workflows from the main checkout, so a lane worktree's edits are invisible to CLI evidence
      - knvpiv [done]: Unify the two independent traversals of the source-to-Set graduation edge (reverse index vs check_graduated_to)
      - mblu3p [done]: aw archive/rename/group for research bypass the ONE resolver, contradicting selectors.py's documented single-resolver claim
      - 8gwpjy [done]: aw group routes per type, so a verb-wide guard added only to artifact_rename misses the plans and research backends
      - bxi1o0 [done]: aw backlog set and aw specs set IGNORE --dry-run on their --status spelling: the backlog one rewrites the record and the specs one MOVES it between disposition directories, both reporting success
      - zftbta [done]: aw rename leaves 44 record citations dangling in agent_workflows source, so a maintainer keeps hand-fixing the shipped package after every rename
      - 2cnvh1 [done]: aw check's CLI overwrites every finding's structured recovery with doctor's human fix string, so a rule that populates no recovery gets a fabricated one in the machine record
      - cm80ge [done]: run_analytics_cli._emit_query_agent's crash-workaround comment goes stale once the --fields projection defect is fixed
      - qbz8i1 [done]: aw specs new and aw releases new write an unvalidated --summary into front matter, so a newline in it injects real metadata (a smuggled - Blocks-Release: next parses as the record gate) and both checkers report clean
      - rcjorx [done]: Docs advertise --fields as a general agent-mode flag but only four runs subcommands accept it, so the documented example exits 2
      - dtq6jr [done]: every aw config verb except the exclude subgroup (seven of them) crashes with an unhandled ImportError when passed --agent, so the whole config family has no machine-readable surface
      - 11pjkd [done]: doctor renders leak_sanitizer's fail/warn severity vocabulary raw beside error/warning diagnostics
      - eeiytw [done]: aw rename plans and aw group plans emit no aw.agent/v1 payload at all under --json/--agent, and print a nested index-refresh line onto stdout
      - phdpbf [done]: Decide whether render_run_summary_table Status cell should render Section 5 lifecycle glyph
      - qdd6ey [done]: Sixteen aw config --help epilogs claim '--agent or non-TTY piped emits aw.agent/v1 JSONL', promising the non-TTY auto-switch retracted on 2026-09-10
      - 3ouico [done]: aw.agent/v1 findings counts every Diagnostic regardless of severity, so one warning-severity diagnostic reports findings 1 on a clean repo (outcome clean, exit 0), blocking the cheap route for any advisory that should reach an agent
      - 7jl2bf [done]: Decide whether aw check --source-anchors should resolve <file>.py:<line> offsets in tracked source, not only spec anchors
      - hegwri [done]: Nothing in the package can create a run ledger: no writer of a kind='run' header record exists, so RunLedgerStore refuses every first append with RL-E041
      - 23p80m [done]: aw rename rewrites citing Scope-Paths entries with no in-flight begin-receipt guard, so renaming an artifact can stale an executing plan's frozen contract and strand its lane at finalize
      - wxpytg [done]: Doctor machine diagnostic construction hardcodes severity error for every drift
      - y11p5u [done]: Raw 38;5 escapes in pwatch, runners_monitor and render_stream headers bypass the color_depth pin
      - 9qvfie [done]: Rollup of uncited trim-deleted test audit carrier-needed outcomes
      - 7df9md [done]: Restore behavioral test coverage for engine
      - q86fxm [done]: Residual rollup of remaining uncited trim-deleted test audit gaps across 45 modules
      - ms06pi [graduated]: Decide where aw-only artifact metadata lives (inline md vs sidecar JSONL vs sqlite) and finish the awhistory plans migration with real timestamps; tk1gqo is a symptom of the deferred b0behn follow-up
      - 1vd74h [graduated]: Decide whether check.spec-anchor-stale should gate, and wire it where a gate actually runs
      - lzg859 [open]: Probe then restore behavioral test coverage for check_engine
      - sv0sf3 [parked]: Should review artifacts move from a flat .aw/records/reviews/ to per-type .aw/records/<type>/reviews/?
      ADVISORY ONLY: this guard shows candidates; it does not decide, and it refuses nothing.
      What it can and cannot tell you:
        - exact identifier and token overlap: DETECTABLE - items sharing distinctive identifiers (e.g. test node ids, function names, environment variables) or distinctive summary tokens are reported
        - paraphrased defect descriptions: PARTLY DETECTABLE - defects described with entirely different vocabulary and no shared distinctive identifiers cannot be matched mechanically
        - distinct issues referencing the same test or symbol: NOT DETECTABLE - items citing the same test or symbol may be distinct concerns (e.g. different assertions or triage lists); human review is required
      Searched: BACKLOG ITEMS across all statuses (open, graduated, blocked, parked, done), matched by distinctive token overlap and co-occurrence. Items outside the backlog tree or using disjoint vocabulary are not indexed.
    aw backlog new: wrote /mnt/md1/VC/agent-workflows/.aw/worktrees/b83dpg/.aw/records/backlog/open/20261018-trimgap-01-nzc6dm-residual-rollup-of-remaining-budget-probe-gaps-acr.backlog.md
    ```
    - Pasted `ls` of each new path:
    ```
    -rw-r--r-- 1 user group 1059 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-1n4qco-probe-then-restore-behavioral-test-coverage-for-at.backlog.md
    -rw-r--r-- 1 user group  923 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-3hurk1-restore-behavioral-test-coverage-for-benchmark-cor.backlog.md
    -rw-r--r-- 1 user group 1065 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-6ntz8v-restore-behavioral-test-coverage-for-run-analytics.backlog.md
    -rw-r--r-- 1 user group 1276 Oct 18 05:35 .aw/records/backlog/open/20261018-trimgap-01-aaud70-investigate-probe-applicability-for-run-analytics.backlog.md
    -rw-r--r-- 1 user group 1003 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-g5ypvb-investigate-probe-applicability-for-benchmark-mani.backlog.md
    -rw-r--r-- 1 user group 1275 Oct 18 05:35 .aw/records/backlog/open/20261018-trimgap-01-gcpj15-probe-then-restore-behavioral-test-coverage-for-ip.backlog.md
    -rw-r--r-- 1 user group 1191 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-gmfupc-restore-behavioral-test-coverage-for-run-analytics.backlog.md
    -rw-r--r-- 1 user group 1037 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-hrz4cv-probe-then-restore-behavioral-test-coverage-for-re.backlog.md
    -rw-r--r-- 1 user group 1191 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-i2g20d-probe-then-restore-behavioral-test-coverage-for-ru.backlog.md
    -rw-r--r-- 1 user group  920 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-kkzvca-probe-then-restore-behavioral-test-coverage-for-ip.backlog.md
    -rw-r--r-- 1 user group 1111 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-l2zsa9-probe-then-restore-behavioral-test-coverage-for-ru.backlog.md
    -rw-r--r-- 1 user group  939 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-l9ssp6-investigate-probe-applicability-for-benchmark-runn.backlog.md
    -rw-r--r-- 1 user group 2053 Oct 18 05:35 .aw/records/backlog/open/20261018-trimgap-01-lzg859-probe-then-restore-behavioral-test-coverage-for-ch.backlog.md
    -rw-r--r-- 1 user group 4568 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-nzc6dm-residual-rollup-of-remaining-budget-probe-gaps-acr.backlog.md
    -rw-r--r-- 1 user group  936 Oct 18 05:36 .aw/records/backlog/open/20261018-trimgap-01-yvmxs9-probe-then-restore-behavioral-test-coverage-for-co.backlog.md
    -rw-r--r-- 1 user group 1756 Oct 18 05:35 .aw/records/backlog/open/20261018-trimgap-01-zd8l04-probe-then-restore-behavioral-test-coverage-for-ru.backlog.md
    ```
    - Pasted `aw backlog check` output:
    ```
    aw backlog check: all backlog items conform. 1100 backlog items checked.
    ```
    - `baseline_failing` re-run output:
    None of the probe JSON results had a non-zero `baseline_failing` count (0 probes recorded baseline failures across Orders 02, 03, 04).
    ~~~
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the reconciliation table with its 319 total, the per-child commit hashes and their `git diff --stat <hash>^1 <hash> -- agent_workflows tests` output (empty for each), the before/after per-rule `aw check --agent` counts with any new finding explained, the `aw commit` output and `git show --stat HEAD` listing only the doc and the new backlog items.
  - Observed evidence:
    ~~~text
    - Reconciliation section with 319 total, per-partition wall-time table, and commit footprint audit:

    Set-wide reconciliation accounting for all 319 budget-exhausted candidate keys from backlog `lrnh5f`.

    **(a) 319-Key Reconciliation Table**

    | Candidate Key Population / Verdict | Count | Partition / Resolution | Carrier or Carrier-Free Disposition |
    |---|---:|---|---|
    | `guarded` (P2) | 188 | Probed in Order 02 (`lictgf`); mutant killed by surviving suite | Carrier-free (`guarded`) |
    | `guarded` (P3) | 14 | Probed in Order 03 (`f4pbs5`); mutant killed by surviving suite | Carrier-free (`guarded`) |
    | `guarded` (P4) | 16 | Probed in Order 04 (`pr6lo9`); mutant killed by surviving suite | Carrier-free (`guarded`) |
    | `key-gone` | 0 | All 319 keys present at HEAD | Carrier-free (`key-gone`) |
    | Group 1: `agent_workflows/check_engine.py` [probe then restore] | 10 | Budget exhausted under run cap | Backlog item `lzg859` |
    | Group 2: `agent_workflows/run_analytics_telemetry.py` [probe then restore] | 8 | Budget exhausted under run cap | Backlog item `zd8l04` |
    | Group 3: `agent_workflows/run_analytics_spa.py` [investigate probe] | 5 | Control survived or target unprovable | Backlog item `aaud70` |
    | Group 4: `agent_workflows/ipd_lifecycle.py` [probe then restore] | 4 | Budget exhausted under run cap | Backlog item `gcpj15` |
    | Group 5: `agent_workflows/run_analytics_telemetry.py` [restore behavioral coverage] | 4 | Mutation survived in surviving suite | Backlog item `gmfupc` |
    | Group 6: `agent_workflows/run_evidence.py` [probe then restore] | 4 | Budget exhausted under run cap | Backlog item `i2g20d` |
    | Group 7: `agent_workflows/attention.py` [probe then restore] | 3 | Budget exhausted under run cap | Backlog item `1n4qco` |
    | Group 8: `agent_workflows/benchmark_manifest.py` [investigate probe] | 3 | Control survived or target unprovable | Backlog item `g5ypvb` |
    | Group 9: `agent_workflows/record_history.py` [probe then restore] | 3 | Budget exhausted under run cap | Backlog item `hrz4cv` |
    | Group 10: `agent_workflows/run_analytics_findings.py` [restore behavioral coverage] | 3 | Mutation survived in surviving suite | Backlog item `6ntz8v` |
    | Group 11: `agent_workflows/runner_shared.py` [probe then restore] | 3 | Budget exhausted under run cap | Backlog item `l2zsa9` |
    | Group 12: `agent_workflows/benchmark_corpus.py` [restore behavioral coverage] | 2 | Mutation survived in surviving suite | Backlog item `3hurk1` |
    | Group 13: `agent_workflows/benchmark_runners.py` [investigate probe] | 2 | Control survived or target unprovable | Backlog item `l9ssp6` |
    | Group 14: `agent_workflows/config.py` [probe then restore] | 2 | Budget exhausted under run cap | Backlog item `yvmxs9` |
    | Group 15: `agent_workflows/ipd_lint.py` [probe then restore] | 2 | Budget exhausted under run cap | Backlog item `kkzvca` |
    | Residual Groups 16-52 (37 module groups) | 43 | Unreached (2), unprovable (7), unguarded (7), budget-exhausted (27) | Residual backlog item `nzc6dm` |
    | **Total Candidate Keys** | **319** | **All 319 budget-exhausted candidate keys accounted for** | **Reconciles exactly: 218 carrier-free + 58 top-15 filed + 43 residual = 319** |

    **(b) Per-Partition Wall-Time Table**

    | Partition | Keys | Total Wall Time (s) | Verdict Counts | Responsible Child IPD |
    |---|---:|---:|---|---|
    | `P2` | 263 | 11130.81 | guarded: 188, budget-exhausted: 47, unguarded: 14, unprovable: 14 | `lictgf` (Order 02) |
    | `P3` | 37 | 10845.88 | guarded: 14, budget-exhausted: 17, unguarded: 4, unprovable: 2 | `f4pbs5` (Order 03) |
    | `P4` | 17 | 8459.79 | guarded: 16, budget-exhausted: 0, unguarded: 0, unprovable: 1 | `pr6lo9` (Order 04) |
    | `unguarded-unreached` | 2 | n/a | unguarded-unreached: 2 | `g00ljy` (Order 01 baseline) |
    | **Total** | **319** | **30436.48** | **guarded: 218, budget-exhausted: 64, unguarded: 18, unprovable: 17, unguarded-unreached: 2** | **Set trimprobe complete** |

    **(c) Set trimprobe Commit Footprint Audit**

    For each child IPD in Set `trimprobe` (`g00ljy`, `lictgf`, `f4pbs5`, `pr6lo9`), git commits and diffs against parent 1:

    ```sh
    for id6 in g00ljy lictgf f4pbs5 pr6lo9; do
      git log --format='%h %p %s' --grep="($id6)" --grep="lane $id6 " HEAD
    done
    ```

    Commit list and diff verification:
    - `f98fa0d5a` `integrate(aw agy run): merge verified lane g00ljy to main` -> `git diff --stat f98fa0d5a^1 f98fa0d5a -- agent_workflows tests` -> empty (0 files changed)
    - `e7702b6d5` `lifecycle(g00ljy): finalize g00ljy -> executed` -> `git diff --stat e7702b6d5^1 e7702b6d5 -- agent_workflows tests` -> empty (0 files changed)
    - `d416e8d8f` `work(g00ljy): Re-measure HEAD reach for the 319 budget-exhausted keys and build the probe queue` -> `git diff --stat d416e8d8f^1 d416e8d8f -- agent_workflows tests` -> empty (0 files changed)
    - `f371fbe11` `integrate(aw oc run): merge verified lane g00ljy to main` -> `git diff --stat f371fbe11^1 f371fbe11 -- agent_workflows tests` -> empty (0 files changed)
    - `d9ed1bcc6` `integrate(aw agy run): merge verified lane lictgf to main` -> `git diff --stat d9ed1bcc6^1 d9ed1bcc6 -- agent_workflows tests` -> empty (0 files changed)
    - `0eb2ecf74` `lifecycle(lictgf): finalize lictgf -> executed` -> `git diff --stat 0eb2ecf74^1 0eb2ecf74 -- agent_workflows tests` -> empty (0 files changed)
    - `5312e8638` `work(lictgf): Mutation-probe the budget-exhausted keys with small surviving selections` -> `git diff --stat 5312e8638^1 5312e8638 -- agent_workflows tests` -> empty (0 files changed)
    - `cb60e5c80` `integrate(aw oc run): merge verified lane lictgf to main` -> `git diff --stat cb60e5c80^1 cb60e5c80 -- agent_workflows tests` -> empty (0 files changed)
    - `918c30558` `integrate(aw agy run): merge verified lane f4pbs5 to main` -> `git diff --stat 918c30558^1 918c30558 -- agent_workflows tests` -> empty (0 files changed)
    - `b9b7404c9` `lifecycle(f4pbs5): finalize f4pbs5 -> executed` -> `git diff --stat b9b7404c9^1 b9b7404c9 -- agent_workflows tests` -> empty (0 files changed)
    - `c7da1e9ca` `work(f4pbs5): Mutation-probe the budget-exhausted keys with large surviving selections` -> `git diff --stat c7da1e9ca^1 c7da1e9ca -- agent_workflows tests` -> empty (0 files changed)
    - `da2918b79` `lifecycle(pr6lo9): finalize pr6lo9 -> executed` -> `git diff --stat da2918b79^1 da2918b79 -- agent_workflows tests` -> empty (0 files changed)
    - `92b2b4f27` `work(pr6lo9): Mutation-probe the subprocess-only budget-exhausted keys` -> `git diff --stat 92b2b4f27^1 92b2b4f27 -- agent_workflows tests` -> empty (0 files changed)
    - `789e1ace5` `integrate(aw oc run): merge verified lane pr6lo9 to main` -> `git diff --stat 789e1ace5^1 789e1ace5 -- agent_workflows tests` -> empty (0 files changed)

    All diffs are empty. The Set's own commits changed zero production code and zero test files.

    **(d) Diagnostic Rule Delta (aw check --agent)**

    Comparison of `aw check --agent` per-rule counts between `check-before.jsonl` (captured at 2026-10-18T09:33:36Z) and post-filing:

    | Rule | Before | After | Delta | Note |
    |---|---:|---:|---:|---|
    | `check.identity-absent-from-name` | 1 | 1 | +0 | Pre-existing |
    | `check.lifecycle-transition-unvalidated` | 7 | 7 | +0 | Pre-existing |
    | `check.scope-drift` | 1 | 1 | +0 | Pre-existing |
    | `check.source-test-citation-dangling` | 42 | 42 | +0 | Pre-existing |
    | `check.spec-criteria-uncovered` | 2 | 2 | +0 | Pre-existing |
    | `check.system-layout-missing` | 1 | 1 | +0 | Pre-existing |
    | **Total** | **54** | **54** | **+0** | **0 new findings on files authored by this plan** |

    - Pasted `aw commit` output:
    ```
    aw commit: committed 17 path(s): d1f30ff2def3abb701a2ce8d4838953cc2e550f4
    ```
    - Pasted `git show --stat HEAD`:
    ```
    commit d1f30ff2def3abb701a2ce8d4838953cc2e550f4 (HEAD -> aw/lane/b83dpg)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Sun Oct 18 05:39:51 2026 -0400

        work(b83dpg): File restore backlog items for every non-guarded probed key and reconcile the 319

        AW-Run: run-20261017T220251Z-1893841
        AW-Item: b83dpg
        AW-Runner: aw agy run

     ...tore-behavioral-test-coverage-for-at.backlog.md |  22 +++
     ...oral-test-coverage-for-benchmark-cor.backlog.md |  21 +++
     ...oral-test-coverage-for-run-analytics.backlog.md |  22 +++
     ...robe-applicability-for-run-analytics.backlog.md |  24 +++
     ...obe-applicability-for-benchmark-mani.backlog.md |  22 +++
     ...tore-behavioral-test-coverage-for-ip.backlog.md |  23 +++
     ...oral-test-coverage-for-run-analytics.backlog.md |  23 +++
     ...tore-behavioral-test-coverage-for-re.backlog.md |  22 +++
     ...tore-behavioral-test-coverage-for-ru.backlog.md |  23 +++
     ...tore-behavioral-test-coverage-for-ip.backlog.md |  21 +++
     ...tore-behavioral-test-coverage-for-ru.backlog.md |  22 +++
     ...obe-applicability-for-benchmark-runn.backlog.md |  21 +++
     ...tore-behavioral-test-coverage-for-ch.backlog.md |  29 ++++
     ...p-of-remaining-budget-probe-gaps-acr.backlog.md |  56 +++++++
     ...tore-behavioral-test-coverage-for-co.backlog.md |  21 +++
     ...tore-behavioral-test-coverage-for-ru.backlog.md |  27 ++++
     ...17-trimprobe-01-wo21z5-budget-probe.findings.md | 165 +++++++++++++++++++++
     17 files changed, 564 insertions(+)
    ```
    ~~~
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`). EXECUTION CONTRACT: all open questions are resolved. Prerequisite: Orders 01 to 04 are `executed`. Scope fence: `- Scope-Paths:` declares new `trimgap` backlog items and this Set's findings doc (do not edit existing items, including `lrnh5f`); do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize. No code or test edits. Paste the ACTUAL output of every command; never record a filing or count you did not produce. Commit only the files this plan wrote through `aw commit <plan> -- <paths>`, never `git add -A`, never push. After every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms, finalize through `aw ipd finalize` (under a runner, the runner finalizes).
