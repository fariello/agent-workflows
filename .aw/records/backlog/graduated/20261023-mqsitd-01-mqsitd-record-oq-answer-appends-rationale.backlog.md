- Id: mqsitd
- Status: graduated
- Graduated-To: mqsitd
- Blocks-Release: next
- Set: mqsitd
- Priority: medium
- Work-Kind: bug
- Summary: runner_shared.record_oq_answer replaces an OQ's existing rationale text instead of appending the pre-flight answer

## Workflow history
- 2026-10-23 graduated (aw backlog): graduated by run run-20261023T221913Z-2698148: ge4qh3
- 2026-10-23 created (aw backlog): Filed from lf4j52 OQ-01 (plan-review 2026-10-23) so the obligation has a durable carrier
- 2026-10-23 decision (maintainer via /askme): confirmed. Change the runner to append; keep as a release-blocking bug.

Raised as OQ-01 in plan lf4j52. The runner pre-flight question sweep (aw oc run / aw agy run) writes the answer via runner_shared.record_oq_answer, which substitutes the whole '- Resolution or deferral rationale:' line (rationale_pattern.sub(..., count=1)), so any author text already there is lost. This is the same overwrite lf4j52 forbids for agents (its D-7). Fix: append 'RESOLVED <date> by <who> via <channel>: <answer>' to existing text; add a test proving pre-existing rationale text survives the write. The existing test_a40_durable_artifact_write_back fixture writes no prior rationale, so its assertion should still hold unchanged (checked 2026-10-23).
