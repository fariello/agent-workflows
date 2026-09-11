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

## ROOT CAUSE, LOCATED 2026-09-10 (read the code, do not re-derive this)

**THE CONFIRMATION GATE EXISTS BUT IS UNREACHABLE FROM A HUMAN TERMINAL.** `status_set.py:1333`:

```python
if (ctx.is_agent or ctx.is_json) and not is_dry_run and not yes:
    ... return exit_code=2, "confirmation required (--yes needed to execute mutation)"
```

The guard is conditioned on `--agent` or `--json` output mode. So a MACHINE caller is protected and a
HUMAN at a terminal is not, which is exactly backwards from every other safety convention here: the
machine can inspect a structured refusal and retry, while the human is the one who cannot undo a
silent bulk write. Removing `(ctx.is_agent or ctx.is_json) and` would extend the existing, already-built
refusal to the interactive path; the `--yes` escape and the `NextAction` hint are already in place.

**AND THERE IS A GATE FOR ENTERING `executed` BUT NONE FOR LEAVING IT.** `status_set.py:1312-1328`
deliberately intercepts a plan moving TO `executed` and delegates to the gated `aw ipd finalize`
transaction (begin receipt, scope reconciliation, three gates, attributed history, rollback). Nothing
guards the reverse. So `executed -> approved` on seven plans took the raw ungated path, which is the
asymmetry that turned a mistyped exploration into a fabricated regression of a completed Set.

## Reproduction (isolated scratch repo, no real records touched)

Two plans in `executed/` sharing setid `demo`, then one command with no flags:

```text
BEFORE: - Status: executed - Status: executed
$ aw ipd set approved demo
-    plan        20260101-demo-01-aaaa01  executed → approved
-    plan        20260101-demo-02-aaaa02  executed → approved
AFTER:  - Status: approved - Status: approved
dirs now: executed  pending
```

No prompt, no `--yes`, exit 0, and the files physically moved out of `executed/`. This is the measured
minimal case for a regression fixture.

## The sharpest part: it transitioned TERMINAL plans backwards

All seven were `executed`, a TERMINAL disposition. The setter accepted `executed -> approved` for six of
them without complaint. That is a backwards lifecycle move on completed, validated work, and the
repository has an explicit rule against exactly this class of claim (a plan in `executed/` must not be
re-opened in place; AGENTS.md says to close a post-execution gap with a new corrective IPD). Whatever the
transition table permits internally, `executed -> approved` on a bulk selector should refuse or at
minimum demand confirmation.

## Suggested fix, in priority order (the first two are small and independently valuable)

1. **EXTEND THE EXISTING CONFIRMATION GATE TO THE INTERACTIVE PATH.** Drop the
   `(ctx.is_agent or ctx.is_json)` condition at `status_set.py:1333` so a human mutation is refused
   without `--yes` exactly as a machine one already is. The refusal, its exit code, its change list and
   its `NextAction` hint are ALREADY WRITTEN; this is a condition change, not a new feature. Keep
   `--dry-run` and `--yes` behaving as they do. RISK TO CHECK: any script or workflow that calls
   `aw set` / `aw ipd set` interactively without `--yes` starts refusing, so grep the workflows and
   drivers for such calls and add `--yes` where the call is deliberate. That grep IS the work item.
2. **REFUSE A BACKWARDS TRANSITION OUT OF A TERMINAL DISPOSITION** (`executed`, `superseded`,
   `not-executed`) unless an explicit override is passed, naming the offending plans. This mirrors the
   existing forward gate at `:1312-1328`, which intercepts a move INTO `executed` and delegates to
   `aw ipd finalize`; the reverse direction simply has no counterpart. Rationale beyond this incident:
   `AGENTS.md` already forbids re-opening an executed plan in place, directing a corrective IPD instead,
   so the tool should enforce what the contract states.
3. **CONSIDER MAKING `--dry-run` THE DEFAULT** for the setters, matching the dry-run-by-default
   convention `aw ipd scaffold`, `aw specs new`, `aw backlog new` and `aw rename` already follow. This
   is the largest behavior change and deserves its own decision; fixes 1 and 2 remove the sharp edge
   without it.

DO NOT bundle this with a change to what a bare setid MEANS. Within-type fan-out is deliberate
(`laykok` E-07) and correct for a pending Set; the defect is the absence of a speed bump, not the
fan-out.

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
