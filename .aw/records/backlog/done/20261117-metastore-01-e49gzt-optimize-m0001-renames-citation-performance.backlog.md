- Id: e49gzt
- Status: done
- Graduated-To: e49gzt
- Set: metastore
- Work-Kind: chore
- Priority: medium
- Summary: Optimize m0001_renames.build_rename_map repeated global_id6s scan and artifact_refs.plan_reference_rewrites_with_warnings regex prefilter (~430s dry run)
- Short-Description: Optimize m0001_renames.build_rename_map repeated global_id6s scan and artifact_refs.plan_reference_rewrites_with_warnings regex prefilter (~430s dry run)

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 done (aw backlog): closed by aw agy run: IPD n2bfd4 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md); evidence .aw/records/plans/executed/20261119-e49gzt-01-n2bfd4-optimize-m0001-rename-id-minting-citation-scan-prefiltering.ipd.md
- 2026-11-20 graduated (aw backlog): graduated by run run-20261120T044041Z-1175270: n2bfd4
- 2026-11-17 created (aw backlog): Optimize m0001_renames.build_rename_map repeated global_id6s scan and artifact_refs.plan_reference_rewrites_with_warnings regex prefilter (~430s dry run)

## Problem

Measured during `m0001` dry-run and `--apply` verification on the 3,364-record repository (435.34s dry run):

1. `agent_workflows/migrations/m0001_renames.py` (`build_rename_map`) calls `artifact_core.mint_id6(repo_path, existing=pool)` inside the per-legacy-record loop. Because `artifact_core.mint_id6` calls `global_id6s(repo_root)` on every call (~4.36s each), minting 28 new `id6`s re-scans the repository 28 times (~120s+).
2. `agent_workflows/artifact_refs.py` (`plan_reference_rewrites_with_warnings`) compiles and evaluates per-stem negative-lookaround regexes (`_boundaried`, `_facetless_boundaried`) across all ~6,274 scan files without a single combined prefilter regex, re-scanning large files such as `agent_workflows/runner_shared.py` (~2.58 MB) ~100 times (~250s+).
3. `agent_workflows/migrations/m0001_metadata_v2.py` (`_execute_operations`) calls `mgr._save_transaction(tx_data)` (atomically dumping a ~4.0 MB `journal.json` with `indent=2, sort_keys=True`) on every single operation across 8,332 operations (~6 ops/s, ~20+ minutes on `--apply`).

```text
Current bottleneck:
  build_rename_map ──(x28 mints)──> artifact_core.mint_id6() ──> global_id6s() (~4.36s/call)
  plan_reference_rewrites_with_warnings ──(6,274 files x ~100 regexes)──> unprefiltered scans
  _execute_operations ──(x8,332 ops)──> mgr._save_transaction() (4.0 MB JSON dump/op)

Target flow:
  build_rename_map ──(once)──> global_id6s() ──> generate_id6(pool) in memory
  plan_reference_rewrites_with_warnings ──(once/file)──> prefilter regex ──(hits only)──> per-stem matchers
  _execute_operations ──> append JSONL op log or flush journal.json every N ops / on completion
```

## Fix Direction

- Seed `pool` once from `artifact_core.global_id6s(repo_path)` before the loop in `build_rename_map` and call `artifact_core.generate_id6(pool)` for each minted `id6`.
- Prefilter each scanned file in `plan_reference_rewrites_with_warnings` with one combined literal alternation regex over all candidate stems before running `_boundaried` and `_facetless_boundaried`.
- Batch or stream `_execute_operations` journal progress (e.g., periodic checkpoint every N operations plus final flush, or an append-only progress log) instead of rewriting a multi-megabyte `journal.json` 8,332 times.
