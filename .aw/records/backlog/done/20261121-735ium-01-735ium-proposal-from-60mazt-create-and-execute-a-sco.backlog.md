- Id: 735ium
- Status: done
- Close-Evidence: .aw/records/plans/executed/20261117-mzw0kk-01-60mazt-verify-ac-42-aw-find-aw-attention-parity-and-clone-migration.ipd.md
- Set: 735ium
- Work-Kind: followup
- Priority: high
- Summary: Proposal from 60mazt: Create and execute a sco
- Short-Description: Proposal from 60mazt: Create and execute a sco
- Blocks-Release: next

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-21 done (aw set): Resolved by executed defect carriers zgxig2 (0dsjzl), s4utmv (fnabjy), dd48b5 (xl9xrm), vvxbbl (7mmhlp) and executed plan 60mazt (592445def)
- 2026-11-21 created (aw backlog): Proposal from 60mazt: Create and execute a sco

## Agent Proposal from 60mazt

- Run-Id: run-20261121T014040Z-2638602
- Proposing-Item: 60mazt
- Lane-Branch: aw/lane/60mazt
- Blocked-By: test_ac42_this_repository_clone_migration failed with 108 new post-migration attention violations (50 attention.missing-status + 50 attention.history-missing on migrated specs; 8 attention.unknown-status research status 'draft' on research-prompt records) and 8 aw find status mismatches ('-' vs 'draft'); legacy_agents_layout, mixed_layout, and no_sidecar failed on the same two production defects.
- Size: material

### Why
IPD 60mazt is a test-only verification plan that explicitly excludes modifying production readers ('EXCLUDES: modifying production readers (ffceq0 and its split parts)'). Fixing these two blockers requires (1) updating attention._spec_record / specs validation to validate v2 log-backed specs against artifact_meta.State and artifact_meta.history instead of stripped Markdown bullets (backlog 0dsjzl), and (2) resolving the metadata-v2 contract for status-less research-prompt and legacy research records across m0001_convert.py, artifact_meta.py (parse_artifact_mirror two-key grammar), m0001_verify.py, attention.py, cli.py, and the pinned st2.status == 'draft' test in tests/test_m0001_review_conversion.py (backlog fnabjy). Weakening AC-42 assertions would conceal real cutover-blocking regressions before 5qyba0 rehearsal and cxxmyv cutover.

### Proposed Change
Create and execute a scoped fix plan (or graduate backlogs 0dsjzl and fnabjy) to: (1) make agent_workflows/attention.py::_spec_record validate v2 log-backed specs from artifact_meta.State and artifact_meta.history rather than calling legacy specs.validate_spec on stripped Markdown text; and (2) stop m0001_convert.build_record_log from writing invalid status='draft' on status-less research-prompt and legacy research records, aligning artifact_meta mirror parsing, m0001_verify, attention._research_record, cli._find_type_records, and tests/test_m0001_review_conversion.py. After those land, re-run IPD 60mazt to pass all 6 AC-42 tests and complete E-03/V-03.

### Affected Paths
- agent_workflows/attention.py
- agent_workflows/specs.py
- agent_workflows/migrations/m0001_convert.py
- agent_workflows/artifact_meta.py
- agent_workflows/migrations/m0001_verify.py
- tests/test_m0001_review_conversion.py
