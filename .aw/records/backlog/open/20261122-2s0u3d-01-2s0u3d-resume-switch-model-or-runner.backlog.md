- Id: 2s0u3d
- Status: open
- Set: 2s0u3d
- Work-Kind: feature
- Priority: medium
- Summary: Allow resuming a run with a different model or runner when credits are exhausted
- Short-Description: Allow resuming a run with a different model or runner when credits are exhausted

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-22 created (aw backlog): Allow resuming a run with a different model or runner when credits are exhausted

When credits or quota run out mid-run, operators need to resume an existing run_id using a different model on the same runner (--model / --effort / --variant / --opencode) or hand off the run across runners (aw agy run resume <oc-run-id> and aw oc run resume <agy-run-id>), clearing incompatible host/model session IDs, updating driver identity and cost attribution, and preserving the queue, preserved lanes, retry state, and answered questions.
