- Id: pz34kx
- Status: open
- Set: pz34kx
- Priority: medium
- Work-Kind: chore
- Summary: IPD lint's V-item 'Observed evidence' is a same-line field, so a multi-line evidence block reads as empty

## Workflow history
- 2026-09-22 created (aw backlog): IPD lint's V-item 'Observed evidence' is a same-line field, so a multi-line evidence block reads as empty

FOUND WHILE EXECUTING `d91i3e` (runrecon Order 01).

WHAT IS WRONG. `aw ipd lint --phase pre-transition` reads a `V-*` item's `- Observed evidence:`
as a SAME-LINE field value (`agent_workflows/ipd_lint.py`, the `_SUBFIELD_RE` branch assigns
`cur_fields[key] = value` from one line). So evidence written in the natural shape the IPD spec's
own prose invites - a `- Observed evidence:` line followed by an indented multi-line transcript of
pasted command output - parses to the EMPTY STRING and the linter reports
`IPD-S404: <V-id>: empty Observed evidence at pre-transition` while a full transcript sits
directly beneath it.

WHY IT MATTERS RATHER THAN BEING COSMETIC. The evidence this field is FOR is pasted command
output, which is inherently multi-line: the execution contract requires the actual runner output,
and a `V-*` item routinely needs several commands' worth. The current shape therefore pushes an
executor toward one of two bad outcomes: cram the evidence into a single very long line, or write
it naturally and then be refused by a gate whose message says the evidence is ABSENT when it is
present. The second is the dangerous one, because the obvious way to make the gate pass is to
delete or shrink real evidence.

WORKAROUND USED IN `d91i3e` (so this is not a blocker): write a one-line SUMMARY on the
`- Observed evidence:` line itself, and continue the transcript in the indented lines below it.
The linter is satisfied by the summary and a human still gets the full transcript. That is a
reasonable convention, but it is UNDOCUMENTED and was discovered by reading the linter's source
after a refusal.

A SECOND, SMALLER HALF OF THE SAME ROUGH EDGE. `Result: verified` is refused with
`IPD-S402: unknown validation result 'verified'`; the accepted token is `pass`. That is correct
behaviour (a closed vocabulary is the point) but the finding message names only what is wrong and
not what the accepted values ARE, so the fix requires reading `ipd_lint.py` to discover that
`pass` is wanted.

SUGGESTED FIX, not prescribed. Either (a) teach the parser to accept an indented continuation
block as part of the field value, which makes the natural shape work; or (b) keep the parser and
DOCUMENT the summary-line convention in the `ipd-spec` doc plus emit it in the finding message
("put a one-line summary on the field line"); and in either case (c) have `IPD-S402` name the
accepted vocabulary in its message. Option (b)+(c) is the cheap one and needs no parser change.

EVIDENCE. Measured at HEAD 23dfbf2d in an isolated lane worktree: an eight-block evidence set
written as indented multi-line transcripts produced eight `IPD-S404 ... empty Observed evidence`
findings plus eight `IPD-S402 ... unknown validation result 'verified'`; moving a one-line summary
onto each field line and changing `verified` to `pass` produced `errors: false` at exit 0 with no
change to the transcripts themselves.
