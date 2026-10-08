- Id: tj9dq9
- Status: done
- Graduated-To: tj9dq9
- Set: tj9dq9
- Priority: medium
- Work-Kind: followup
- Summary: release_readiness.gate_docs_checks is inert: it takes a doc_findings sequence and nothing in the repository ever computes one, so the documentation gate always reports clean regardless of the real state of docs/

## Workflow history
- 2026-10-08 done (aw backlog): closed by aw agy run: IPD wix4xe executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-tj9dq9-01-wix4xe-wire-the-documentation-checks-into-the-release-readiness-gat.ipd.md); evidence .aw/records/plans/executed/20261002-tj9dq9-01-wix4xe-wire-the-documentation-checks-into-the-release-readiness-gat.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: wix4xe
- 2026-09-30 created (aw backlog): Filed by plan t9lcdu (gzmr54-01) as the durable carrier for its deferred wiring row. Measured at HEAD 2e2ecce12: 'rg -n doc_findings' matches only agent_workflows/release_readiness.py itself (the parameter, its default, and the build_report pass-through), and nothing calls docs_check.check_docs_dir anywhere outside its own module. release_readiness.build_report defaults doc_findings to the empty tuple, so gate_docs_checks passes vacuously. t9lcdu restores the test coverage but deliberately leaves this wiring decision alone.
