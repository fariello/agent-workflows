- Id: svqhmp
- Status: open
- Set: svqhmp
- Priority: medium
- Work-Kind: feature
- Summary: Add --tty as two separate axes (presentation and interactivity) behind one interactivity resolver

## Workflow history
- 2026-09-19 created (aw backlog): Add --tty as two separate axes (presentation and interactivity) behind one interactivity resolver

Graduated from the Deferred section of plan `yaxr4i` (ttyflags 01), which deliberately did NOT implement `--tty` and instead recorded the design constraint in `docs/cli-output-contract.md` section 9.1.

WHY THIS IS NOT JUST 'ADD A FLAG'. TTY-ness controls two unrelated things through two different streams: PRESENTATION keyed on stdout (`term.should_color`) and INTERACTIVITY keyed on stdin (57 `isatty` references package-wide at 2026-09-19, 19 in `cli.py`, plus `git_commit_helper._is_interactive`). A single undifferentiated `--tty` boolean would silently re-enable prompting while the operator was only asking about color, weakening a real fail-safe: `cli._confirm` and `_is_interactive` currently DECLINE rather than prompt when stdin is not a terminal, which is what stops an unattended runner wedging on a question nobody can answer.

WHAT THE WORK IS. The presentation axis is DONE (`yaxr4i` shipped `--color`/`--no-color` with a flag-beats-env-beats-detection precedence). What remains is the interactivity axis: an `--interactive`/`--no-interactive` pair routed through ONE resolver that every call site already consults, generalizing the shape of `git_commit_helper._is_interactive` (an explicit override falling back to `sys.stdin.isatty()`). A per-site flag check across ~57 sites is explicitly the wrong shape and is how the two axes drift apart.

A maintainer ruling is needed on whether `--tty` should exist as a name at all, given that two separate flags are the safe construction.
