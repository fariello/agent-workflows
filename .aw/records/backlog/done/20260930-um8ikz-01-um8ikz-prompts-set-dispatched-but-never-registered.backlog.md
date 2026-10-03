- Id: um8ikz
- Status: done
- Graduated-To: promptsset
- Blocks-Release: next
- Set: um8ikz
- Priority: low
- Work-Kind: bug
- Summary: aw prompts set is dispatched by cli.py to the shared setter but never registered in the prompts subparser, so the spelling is unreachable dead code

## Workflow history
- 2026-10-03 done (aw backlog): closed by aw agy run: IPD 7z3ovv executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261002-promptsset-01-7z3ovv-register-the-aw-prompts-set-subparser-and-bound-the-prompts.ipd.md); evidence .aw/records/plans/executed/20261002-promptsset-01-7z3ovv-register-the-aw-prompts-set-subparser-and-bound-the-prompts.ipd.md
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T222151Z-2118435: 7z3ovv
- 2026-09-30 created (aw backlog): Split from plan 4gwgo3 finding F-09, measured in that lane: 'aw prompts set staged <id6> --message ...' exits with 'argument prompts_command: invalid choice: 'set' (choose from 'new')', yet cli.py contains a live dispatch arm routing prompt_cmd == 'set' to status_set.run_set_command with scoped_type='prompts'. The prompts tree is therefore reachable only through the untyped 'aw set'. Closing it needs a decision about which statuses the prompts tree accepts through that spelling: the untyped 'aw set' refused 'staged' as 'not valid for prompts' while accepting 'to-review', so simply registering the subparser would expose a vocabulary question rather than settle it. Nothing regresses by waiting since the arm is unreachable today, but a dispatch arm no spelling can reach will rot silently as the setter changes around it.
