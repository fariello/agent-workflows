- Id: 4vhe5o
- Status: graduated
- Graduated-To: fencegate
- Blocks-Release: next
- Set: 4vhe5o
- Priority: medium
- Work-Kind: bug
- Summary: the executed-transition pre-commit hook is not fence-aware, so a plan quoting '- Status: executed' inside a code fence is refused as a raw transition

## Workflow history
- 2026-09-25 graduated (aw set): graduated into fencegate (plan kecxnb); verified live at 8e74dcac
- 2026-09-18 created (aw backlog): the executed-transition pre-commit hook is not fence-aware, so a plan quoting '- Status: executed' inside a code fence is refused as a raw transition

Found while executing plan `di08i9` (Set `nobugship`), committing that plan's own evidence update.

WHAT IS WRONG. `agent_workflows/hooks/executed_transition_gate.py::_has_executed_status` walks the
staged plan text line by line and returns True when any stripped line equals `- status: executed` or
`- status: done`. It has no notion of a code fence, a block quote, or an indented literal, so a plan
that PASTES evidence containing such a line, or QUOTES another artifact's status, is treated as
having gained executed status itself.

MEASURED. Committing `di08i9`'s evidence update was refused twice:

```text
no raw plan->executed commit (use aw ipd finalize).......................Failed
  ... (di08i9): raw plan->executed transition (gained '- Status: executed') with NO matching
  finalize evidence in .aw/state/.
```

That plan's own status field read `approved` throughout and was never touched. The three triggering
lines were: a sentence describing ANOTHER plan's landed state, and two lines inside fenced
transcripts, one of which was a scratch BACKLOG item's status from a driven `aw backlog new
--status done` case. All three were prose or pasted output.

WHY IT MATTERS, i.e. why this is a `bug`: the refusal is indistinguishable from a real violation, and
the message instructs the agent to run `aw ipd finalize`, which is the WRONG remedy for a plan that is
not transitioning and which (in a managed lane) is itself refused by role. The only ways past it are to
reword truthful evidence until the pattern stops matching, which is what this execution had to do and
which silently degrades the record, or `--no-verify`, which the contributor rules forbid. A gate that
punishes pasting accurate evidence pushes directly against the evidence standard the IPD lifecycle is
built on, and the sibling detector already knows better: `check_engine._deferred_section_obligations`
deliberately walks `ipd_lint._structural_lines` precisely "so a bullet inside a code fence or a block
quote is not mistaken for a row".

SUGGESTED FIX. Make `_has_executed_status` fence-aware by consuming the same structural view
(`ipd_lint._structural_lines`) the carrier detector uses, and consider restricting the scan to the
FRONT-MATTER bullet block, since a plan's `- Status:` is only meaningful there. Note the same
line-by-line shape appears in the `no untooled plan status change` detector, so check whether it has
the identical blind spot.
