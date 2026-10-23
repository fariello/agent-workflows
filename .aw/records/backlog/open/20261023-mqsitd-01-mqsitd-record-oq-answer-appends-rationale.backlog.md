- Id: mqsitd
- Status: open
- Blocks-Release: next
- Set: mqsitd
- Priority: medium
- Work-Kind: bug
- Summary: runner_shared.record_oq_answer replaces an OQ's existing rationale text instead of appending the pre-flight answer

## Workflow history
- 2026-10-23 created (aw backlog): Filed from lf4j52 OQ-01 (plan-review 2026-10-23) so the obligation has a durable carrier

Raised as OQ-01 in plan lf4j52. The runner pre-flight question sweep (aw oc run / aw agy run) writes the answer via runner_shared.record_oq_answer, which substitutes the whole '- Resolution or deferral rationale:' line (rationale_pattern.sub(..., count=1)), so any author text already there is lost. This is the same overwrite lf4j52 forbids for agents (its D-7). Fix: append 'RESOLVED <date> by <who> via <channel>: <answer>' to existing text; update tests/test_question_preflight.py test_a40_durable_artifact_write_back accordingly.
