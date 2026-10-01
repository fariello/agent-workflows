- Id: um8ikz
- Status: open
- Blocks-Release: next
- Set: um8ikz
- Priority: low
- Work-Kind: bug
- Summary: aw prompts set is dispatched by cli.py to the shared setter but never registered in the prompts subparser, so the spelling is unreachable dead code

## Workflow history
- 2026-09-30 created (aw backlog): Split from plan 4gwgo3 finding F-09, measured in that lane: 'aw prompts set staged <id6> --message ...' exits with 'argument prompts_command: invalid choice: 'set' (choose from 'new')', yet cli.py contains a live dispatch arm routing prompt_cmd == 'set' to status_set.run_set_command with scoped_type='prompts'. The prompts tree is therefore reachable only through the untyped 'aw set'. Closing it needs a decision about which statuses the prompts tree accepts through that spelling: the untyped 'aw set' refused 'staged' as 'not valid for prompts' while accepting 'to-review', so simply registering the subparser would expose a vocabulary question rather than settle it. Nothing regresses by waiting since the arm is unreachable today, but a dispatch arm no spelling can reach will rot silently as the setter changes around it.
