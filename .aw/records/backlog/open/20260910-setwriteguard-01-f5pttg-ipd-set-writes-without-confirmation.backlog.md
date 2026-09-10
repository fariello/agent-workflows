- Id: f5pttg
- Status: open
- Set: setwriteguard
- Priority: high
- Work-Kind: bug
- Summary: aw ipd set writes by default with no confirmation, so a bare setid selector silently reverted 7 EXECUTED plans to approved/pending in one command

## Workflow history
- 2026-09-10 created (aw backlog): aw ipd set writes by default with no confirmation, so a bare setid selector silently reverted 7 EXECUTED plans to approved/pending in one command

## What happened (measured, on this repository, 2026-09-10)

Running `aw ipd set approved agentadhere` intending to REPRODUCE a historical failure message, I expected
a preview. Instead the command WROTE: it moved SEVEN plans out of `.aw/records/plans/executed/` into
`pending/`, rewrote each `- Status: executed` to `approved`, and printed six lines reading
`executed → approved`. No confirmation was requested. Exit status looked like success.

Reverted immediately with `git checkout -- .aw/records/plans/executed/` plus removing the seven stray
`pending/` copies; verified byte-identical to HEAD afterward and nothing was committed, so no permanent
damage. But the only reason this was caught is that I ran `git status` out of caution; a less careful
pass would have committed a fabricated regression of an entire completed six-phase plan Set.

## Why this is a defect and not operator error

Three properties combine into a trap, and any ONE of them removed would have prevented it:

1. **WRITE IS THE DEFAULT.** `--dry-run` exists (`aw ipd set --help`) but is opt-IN. Compare the
   repository's own convention elsewhere: `aw ipd scaffold`, `aw specs new`, `aw backlog new` and
   `aw rename` are all DRY-RUN BY DEFAULT with an explicit `--apply` to write. `aw ipd set` inverts that
   for a MORE destructive operation.
2. **NO CONFIRMATION, EVEN IN BULK.** `--yes/-y` exists to "confirm mutation without prompting", which
   implies a prompt exists when it is absent. None appeared for a seven-file transition in a TTY.
3. **A SETID SELECTOR FANS OUT SILENTLY.** A bare setid legitimately means "the whole Set" (IPD `laykok`
   E-07 made that deliberate, and it is correct for a pending Set). But combined with 1 and 2, one short
   token rewrites every member with no echo of the blast radius before acting.

## The sharpest part: it transitioned TERMINAL plans backwards

All seven were `executed`, a TERMINAL disposition. The setter accepted `executed -> approved` for six of
them without complaint. That is a backwards lifecycle move on completed, validated work, and the
repository has an explicit rule against exactly this class of claim (a plan in `executed/` must not be
re-opened in place; AGENTS.md says to close a post-execution gap with a new corrective IPD). Whatever the
transition table permits internally, `executed -> approved` on a bulk selector should refuse or at
minimum demand confirmation.

## Suggested fix (any of these closes it; the first two are cheap)

- **Refuse a backwards transition out of a terminal status** (`executed`, `superseded`, `not-executed`)
  unless an explicit override flag is passed, and name the offending plans in the refusal.
- **Prompt before a multi-artifact mutation** when stdin is a TTY, echoing the count and the resolved
  paths; honor `--yes` to skip. The flag's own help text already promises this behavior exists.
- **Consider making `--dry-run` the default** for `aw ipd set`, matching the dry-run-by-default
  convention the creation and rename verbs already follow, with `--apply` to write. This is the biggest
  behavior change of the three and deserves its own decision.

## Verification this needs

1. `aw ipd set approved <setid of an executed Set>` refuses, or prompts, rather than silently writing.
2. A single-plan legitimate transition (`to-review -> reviewed`) is UNAFFECTED, so the guard does not
   make ordinary use annoying.
3. A bulk transition on a genuinely `pending` Set still works, since that is the feature `laykok` E-07
   deliberately added.
4. A regression fixture reproducing the measured case: seven `executed` plans sharing one setid, one
   command, and the assertion that they remain `executed`.

## Related

- Filed during the setid-reversal cleanup (DECISIONS D153). Not caused by it; this is a pre-existing
  property of the setter that the cleanup merely exposed.
- Sibling data-loss defect found in the same session: `hg2oop`, where `aw backlog set` on a same-status
  item destroys the whole workflow history. Same theme, different verb: a mutating setter doing more
  than the caller asked, silently, at exit 0.
- `x6tk1u` (an `aw set` same-status call silently discards `--message`) is the third member of that
  family.
