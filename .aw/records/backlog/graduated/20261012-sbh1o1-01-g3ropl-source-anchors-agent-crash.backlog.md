- Id: g3ropl
- Status: graduated
- Graduated-To: sbh1o1
- Blocks-Release: next
- Set: sbh1o1
- Priority: medium
- Work-Kind: bug
- Summary: aw check --source-anchors --agent crashes with a traceback whenever the detector has findings

## Workflow history
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131029Z-4042525: f0kolj
- 2026-10-12 created (aw backlog): Found while graduating 1vd74h on 2026-10-12 at 92a6f240d. The --source-anchors branch of cli._run_check hardcodes exit_code = 0 but sets status 'findings' when any finding exists, and agent_schema.assert_valid_agent_record rejects that pair ('Exit code mismatch: exit=0 incompatible with negative outcome findings'), so 'aw check --source-anchors --agent' (and 'aw check specs --source-anchors --agent') raises ValueError and exits 1 with a traceback on the real tree (1 finding) and on any fixture with a stale anchor; the human-mode output is unaffected and zero findings is unaffected. Carrier: plan sbh1o1 Order 03 (graduation of 1vd74h) fixes it as part of making the census honest; close this item done with --evidence pointing at that executed plan.
