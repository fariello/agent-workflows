- Id: sflov4
- Status: open
- Set: runledger
- Priority: low
- Work-Kind: followup
- Summary: After aw run init (plan v47z9u), every later aw run/runs leaf still needs --workflow repeated, because the ledger stores only the workflow digest

## Workflow history
- 2026-10-12 created (aw backlog): Filed while authoring plan v47z9u from backlog hegwri: measured that start without --workflow reports unknown step.

MEASURED 2026-10-12 at HEAD a3084a234 in lane worktree hegwri: with a conformant kind=run header at state_root(repo)/run-abcdef1234/ledger.jsonl, 'aw run start run-abcdef1234 --step S-01' (no --workflow) printed "error: unknown step 'S-01'", because run_cli._reconstruct_workflow_from_ledger recovers step ids only from step_attempt records, of which a fresh ledger has none. With --workflow wf.json the same command exited 0 ('Started step S-01 (state: running)'). Plan v47z9u's header records workflow_digest but not the workflow, so an operator must pass the same --workflow to every later leaf and nothing checks it is the same file. Options: persist the workflow beside the ledger and fall back to it in run_cli._load_workflow_arg, or refuse a --workflow whose digest disagrees with the header. Depends on v47z9u being executed.
