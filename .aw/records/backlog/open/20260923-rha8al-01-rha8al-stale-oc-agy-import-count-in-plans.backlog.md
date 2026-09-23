- Id: rha8al
- Status: open
- Set: rha8al
- Priority: low
- Work-Kind: chore
- Summary: Three plans carry a stale oc_runipd-to-agy_runipd import count (48) that AST measurement puts at 56

## Workflow history
- 2026-09-23 created (aw backlog): Found while executing w33lrl: plan w33lrl F-10 corrected the count 47 -> 48 and says two sibling plans carry the same figure, but AST measurement across all 8 'from agent_workflows.oc_runipd import' statements gives 56. tests/test_rununify_initialize_run.py's own comments independently say 56 (and that a sibling drops it 56 -> 53), so the plans' figure is stale by 8 and is used as an ARGUMENT for a layering claim. Affected: the F-10 row and the 'Project conventions discovered' bullet in w33lrl plus the two siblings that copied it.
