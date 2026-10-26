- Id: n4a06q
- Status: open
- Blocks-Release: next
- Set: reslife
- Priority: medium
- Work-Kind: feature
- Summary: Back-fill outcome and consumed-by on aw research promote --suggest --apply (spec 5tapom AC-5)

## Workflow history
- 2026-10-26 created (aw backlog): Filed 2026-10-25 from the spec audit; maintainer chose to build the AC-5 back-fill.

Spec 5tapom AC-5 requires the triage classifier (`aw research promote --suggest`, confirmed with --apply) to back-fill each promoted document's `outcome` and `consumed-by`, and to propose uncited dead ends for archive. At HEAD 5db4791c1 apply_moves (agent_workflows/research_archive.py:362) rewrites only status and moves the file; nothing writes outcome or consumed-by, and plan m383qb E-03 never scoped it. Measured 2026-10-25: 41 proposed moves (31 reference, 10 archive); 18 of the 31 reference documents have empty consumed-by. Also, suggest_triage only proposes archive for uncited documents inside a run set; uncited documents outside one are never proposed. Build: on --apply, write consumed-by from the citing artifact id6s suggest_triage already computes (cited_by_executed_ids / _collect_all_citations), set outcome, show both in the --suggest preview, and add a behavioral test reproducing AC-5's fixture (cited doc -> reference with its citer as consumed-by; uncited dead end -> archive; no mutation without --apply). First check whether found citations are real uses or passing mentions; if many are mentions, restrict consumed-by to executed citers. Then 5tapom can move to implemented. Maintainer decision 2026-10-25 via /askme: build it.
