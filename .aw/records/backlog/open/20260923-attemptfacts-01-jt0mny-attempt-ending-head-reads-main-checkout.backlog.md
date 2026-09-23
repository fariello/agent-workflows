- Id: jt0mny
- Status: open
- Blocks-Release: next
- Set: attemptfacts
- Priority: medium
- Work-Kind: bug
- Summary: A per-attempt ending_head/ending_status describes the MAIN checkout even for an isolated lane turn

## Workflow history
- 2026-09-23 created (aw backlog): Found executing dy9ymn. execute_item_core records attempt['ending_head'] = git_head(repo) and attempt['ending_status'] = git_status(repo), where repo is the MAIN CHECKOUT - but an isolated turn (the DEFAULT) works in work_dir. So for the default execution shape both fields describe a tree the turn never touched: they are TRUE BY CONSTRUCTION (unchanged head, clean status) even for a lane that committed substantial real work, because a lane agent never moves the main checkout's HEAD and never dirties its tree. Any consumer reading them as 'what this turn did' is silently wrong, and wrong in the dangerous direction (it reads as 'nothing happened'). A live consumer: collect_earned_paths diffs the attempt's starting_head..ending_head. dy9ymn WORKS AROUND this rather than fixing it - its predicate reads the lane's own commits_ahead/dirty via describe_lane for an isolated turn, and documents the trap at the predicate - because repairing the recorded fields is outside its declared scope and would change a record shape other readers consume. THE FIX NEEDS A DECISION, which is why this is filed rather than patched: either record the LANE's head/status for an isolated turn (changing the meaning of an existing field, so every reader must be audited), or add distinct lane_ending_head/lane_ending_status fields and migrate readers. Filed as a bug on the perceptibility test: a reader cannot tell a no-op turn from a productive lane turn, and that is the exact confusion that cost run run-20260918T045802Z-2547360 four of five items.
