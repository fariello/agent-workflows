- Id: 68sur3
- Status: graduated
- Graduated-To: declabsent
- Blocks-Release: next
- Set: setdispgate
- Priority: low
- Work-Kind: bug
- Summary: aw prompts set is dispatched in cli.main and documented in help but is not registered in the parser

## Workflow history
- 2026-10-02 graduated (aw backlog): graduated by run run-20261001T221821Z-1985969: gm9baj
- 2026-10-01 created (aw backlog): Filed while authoring the fcnz1r dispatch-unification Set; measured, not inferred.

MEASURED 2026-10-01:

  $ aw prompts set draft foo
  agent-workflows prompts: error: argument prompts_command: invalid choice: 'set' (choose from 'new')

Yet cli.main contains a live 'prompts set' dispatch branch routing to status_set.run_set_command with scoped_type='prompts', and the command-surface help text advertises that 'set' transitions a staged prompt's status. So the help promises a verb the parser rejects, and the dispatch branch behind it is unreachable dead code.

WHY IT MATTERS BEYOND TIDINESS. It is a user-facing falsehood: a reader following the help gets an argparse error. It also silently inflates the apparent blast radius of any change to the shared set engine, because status_set._offer_self_commit's docstring enumerates 'prompts set' among the surfaces ONE integration covers, which an author reasonably reads as five live callers when four are live.

THE FIX IS A DECISION, NOT JUST CODE: either REGISTER the subparser (prompts become status-settable, which needs the prompt status vocabulary and lifecycle dirs checked against status_set's TYPE_STATUSES) or REMOVE both the dispatch branch and the help claim. Registering is the likelier intent given the dispatch branch already exists and names a scoped_type, but that is a scope call for the maintainer rather than something to assume.

Found while mapping the 'set' dispatch surface for backlog fcnz1r (dispatch-path unification); recorded there as a correction to that item's own 'five CLI surfaces' count, which is four reachable plus this one.
