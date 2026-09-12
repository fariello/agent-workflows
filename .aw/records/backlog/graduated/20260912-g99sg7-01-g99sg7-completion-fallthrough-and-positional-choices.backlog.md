- Id: g99sg7
- Status: graduated
- Blocks-Release: next
- Set: g99sg7
- Priority: medium
- Work-Kind: bug
- Summary: bash completion suggests the top-level command list as the argument to any command without subcommands (30 of 47), so 'aw completion <TAB>' offers 'index' and 'aw find <TAB>' offers 'commit'

## Workflow history
- 2026-09-12 graduated (aw set): Graduated to plan 4y95tp (Set compargs), which inherits Blocks-Release: next.
- 2026-09-12 created (aw backlog): bash completion suggests the top-level command list as the argument to any command without subcommands (30 of 47), so 'aw completion <TAB>' offers 'index' and 'aw find <TAB>' offers 'commit'

## Reported by the maintainer 2026-09-12, from a live session

    % aw completion [tab][tab]
    agy  archive  backlog  check  ...  (all 47 commands)
    % aw completion in[tab][tab]
    include  index    install
    % aw completion index
    agent-workflows: error: unknown completion target 'index'
      (expected bash|zsh|fish|install|uninstall).

The completion led them into an error within seconds of completion starting to work at all.

## Two independent causes

FALL-THROUGH (the broader half). `generate_bash_completion` ends its `case` with an unconditional
`COMPREPLY=( ... top_names ... )`, so any command without a `case` arm suggests the whole command list.
Only 17 of 47 commands get an arm (those with real subparsers). Verified by driving the installed
function: `aw find <TAB>`, `aw search <TAB>`, `aw install <TAB>` and `aw completion <TAB>` all return the
same 47 items, so `aw find <TAB>` proposes `commit` and `archive` as things to find.

POSITIONAL CHOICES NEVER INTROSPECTED (the reported half). `aw completion`'s valid values are a
positional with `choices`, not subparsers, and `introspect_cli_tree` descends only `_SubParsersAction`.
Verified: `t['subcommands']['completion']['subcommands']` is `{}`. So fixing the fall-through alone would
make `aw completion <TAB>` offer nothing, which is better but still not right.

## Why it was invisible until now

Completion was INERT on the reporting machine: bash-completion was never loaded for interactive
non-login shells (backlog `lalwnj`, plan `92u0v9`). Nobody could observe wrong suggestions from a
feature that produced none. Both defects were found in the same session, minutes apart.

## Graduated

Design handed off to plan `4y95tp` (Set `compargs`): remove the fall-through, capture positional
choices under their own key, emit them, and test by DRIVING the generated function rather than reading
its text (a text assertion could not have caught this, since the script was always internally
consistent). The release gate travels with the plan.

F-5 there raises a separate question left for the maintainer: nothing regenerates an installed
completion script on upgrade, so this fix reaches an existing user only when they re-run
`aw completion install`.
