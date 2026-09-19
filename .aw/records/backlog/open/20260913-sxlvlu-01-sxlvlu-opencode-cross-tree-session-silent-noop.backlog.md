- Id: sxlvlu
- Status: open
- Blocks-Release: next
- Set: sxlvlu
- Priority: medium
- Work-Kind: bug
- Summary: opencode run with a --session from a different tree exits 0 with zero output: a silent no-op instead of an error, so a caller cannot tell the turn never ran

## Workflow history
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-13 created (aw backlog): opencode run with a --session from a different tree exits 0 with zero output: a silent no-op instead of an error, so a caller cannot tell the turn never ran

## Measured behavior

Reproduced 2026-09-13 against opencode 1.18.30 in two throwaway git repositories, `a` and `b`, each
holding a `marker.txt` naming itself.

1. A turn in tree `a` with a fresh session: works, and its session id was captured.
2. The SAME session id passed with `--dir` pointing at tree `b`: **exit 0, ZERO output**. Reproduced
   with a bare prompt, with `--format json`, and across repeat runs. No text, no tool events, no error.
3. Control, a FRESH session in tree `b`: works normally, printing `/tmp/.../b` for `pwd` and
   `I am tree b` for the marker.
4. Control, the ORIGINAL session in its OWN tree `a`: works normally.

So the failure is specific to carrying a session into a DIFFERENT tree, and its symptom is silence
plus a success exit code.

## Why this matters

A caller cannot distinguish "the turn ran and produced nothing" from "the turn never ran". Exit 0 is an
affirmative claim of success. Any driver that reuses a session id across trees will record a completed
turn that did not happen, and will do so without a single diagnostic to act on.

This toolkit already paid for the same underlying hazard once. `oc_runipd.py:5383-5390` records incident
`lanesess xd9sll`: sessions were keyed per SET while worktrees are allocated per ITEM, so lanes 2..N of a
Set launched with lane 1's session, and FOUR CONSECUTIVE LANES WERE LOST. The mitigation shipped there is
to force a fresh session for any isolated turn (`session = None if (fresh_session or isolated_turn or
is_rotation)`, `:5405`), which is why this repository is not currently exposed.

## What the recorded explanation says, and how the measurement differs

The `xd9sll` comment states the mechanism as: "an opencode session carries its own project/`directory`
binding, which then OVERRIDES `--dir` and silently runs the turn in the PREVIOUS lane's worktree", after
which main-repo paths look external, the external-directory gate asks with no answerer, and the turn dies
at the stall watchdog.

The measurement does NOT show a turn running in the wrong tree, and does not show a stall. It shows no
turn at all, and an immediate clean exit. Two possibilities, neither verified:

- the behavior changed between the version that produced `xd9sll` and 1.18.30, or
- the original diagnosis described a downstream symptom rather than the mechanism.

Also relevant, from reading the shipped source rather than inferring: in `run.ts` the session's own
directory is consulted ONLY in attach mode (`const cwd = args.attach ? (directory ?? sess.directory ??
...) : (directory ?? root)`), and this toolkit's runner never passes `--attach`. So the "session
directory overrides `--dir`" reading does not obviously hold for the non-attach path the runner uses.
Stated as an observation, not a conclusion: the silent no-op's actual cause is NOT established here.

## What would resolve this

1. Establish the cause. Determine whether opencode refuses the cross-tree session somewhere and swallows
   the refusal, or whether the prompt is delivered to a session whose project binding makes it a no-op.
2. Decide the correct contract and make it observable. A cross-tree session reuse should either WORK, or
   FAIL with a nonzero exit and a message naming both directories. Silence with exit 0 is the one
   outcome no caller can handle.
3. If the defect is upstream in opencode rather than in this toolkit's usage, report it there with this
   reproduction, and record the version it was measured against.
4. Re-read the `xd9sll` comment once the cause is known and correct it if the mechanism it describes is
   not the real one. A misleading incident record is how the wrong fix gets chosen next time; this item
   exists partly because that comment was trusted verbatim during a design discussion and turned out not
   to match the observable behavior.

## Scope note

NOT urgent for this repository: the shipped mitigation means no isolated turn reuses a session today,
verified on two 2026-09-13 runs which recorded 2 sessions for 2 turns and 3 for 3, with `set_sessions`
empty. The exposure returns the moment any code path reuses a session across trees, which is exactly what
plan `ajxr5d` (review-sweep isolation) had to reason about, and why the finding is filed rather than left
in a chat log.

## Related

- `oc_runipd.py:5383-5390` (the `xd9sll` rationale) and `:5405` (the mitigation).
- Plan `ajxr5d` (dirtygates Order 05), whose OQ-03 resolution records this measurement and explicitly
  does NOT take on fixing it.
