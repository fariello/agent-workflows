- Id: lalwnj
- Status: graduated
- Blocks-Release: next
- Set: lalwnj
- Priority: medium
- Work-Kind: bug
- Summary: aw completion install reports success into a shell where completion cannot work: it never checks whether bash-completion is loadable, and offers no way to make it so

## Workflow history
- 2026-09-12 graduated (aw set): Graduated to plan 92u0v9 (Set compinert), which inherits Blocks-Release: next. Design is handed off; code not yet written.
- 2026-09-12 created (aw backlog): aw completion install reports success into a shell where completion cannot work: it never checks whether bash-completion is loadable, and offers no way to make it so

## How this was found

Reported by the maintainer 2026-09-12 as a plain usage question ("how do I install tab completion on
this server?"), which turned into a defect when the documented steps did not work. They ran
`aw completion install`, saw three `OK` lines and "Next start a new bash shell (or run `exec bash`) to
pick it up", did exactly that, and `aw <TAB>` completed nothing.

## The defect

`aw completion install` writes into a directory whose entire purpose is AUTO-DISCOVERY BY
BASH-COMPLETION, and never checks that bash-completion is loadable. It then prints unconditional
success plus a next step ("start a new shell") that is precisely the action that does not help.

MEASURED on the reporting machine:

    bash -lic 'echo ${BASH_COMPLETION_VERSINFO-}'   -> 2        (framework loaded)
    bash  -ic 'echo ${BASH_COMPLETION_VERSINFO-}'   -> <empty>  (framework NOT loaded)

`/usr/share/bash-completion/bash_completion` exists but is sourced only by
`/etc/profile.d/bash_completion.sh`, which runs for LOGIN shells. The user's `~/.bashrc` has no
reference to it and there is no `~/.bash_profile`. So in a new terminal tab, tmux pane, or plain
`bash`, nothing at all is completed, `git` and `ssh` included. `aw` is not special.

`grep -n 'profile.d\|BASH_COMPLETION_VERSINFO\|bash_completion' agent_workflows/completion.py`
returns NOTHING, so the precondition is not checked anywhere.

## What is NOT the defect

The installed artifacts are CORRECT and must not be "fixed". The three files exist, sourcing the file
registers `complete -F _aw_completion aw`, and with the framework loaded the lazy loader resolves ALL
THREE entrypoint names. An initial suspicion that the single multi-name
`complete -F _aw_completion aw agentwf agent-workflows` was fragile was TESTED AND REFUTED: the
per-alias symlinks written by `_alias_filenames` (deliberate, documented) are what make it work. That
suspicion was withdrawn before filing rather than recorded as a finding.

## Graduated

Design handed off to plan `92u0v9` (Set `compinert`), which carries the detection predicate, the four
honest message variants, the opt-in remediation, and injection-driven tests. The release gate travels
with it.
