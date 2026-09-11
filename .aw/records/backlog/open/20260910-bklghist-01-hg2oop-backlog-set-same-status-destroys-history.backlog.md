- Id: hg2oop
- Status: open
- Set: bklghist
- Priority: high
- Work-Kind: bug
- Summary: The durable workflow history lives in a GITIGNORED sidecar while the inline record is slimmed to one line, so reasoning recorded by aw specs note / aw backlog set does not survive a clone

## Workflow history
- 2026-09-10 created (aw backlog): aw backlog set on a same-status item DESTROYS the existing workflow history, replacing every prior line with one new line, and exits 0

## CORRECTED 2026-09-10, SAME DAY IT WAS FILED: THE TRUNCATION IS DELIBERATE, THE DEFECT IS ELSEWHERE

I FILED THIS WRONG AND AM CORRECTING IT RATHER THAN QUIETLY CLOSING IT. The original report below said
the history truncation is an accidental data-loss bug in a fixed-template renderer. It is not. Slimming
the inline `## Workflow history` to the LATEST ONE record is an INTENTIONAL, reviewed, executed design
decision: plan `awhistory-02` (`b0behn`, executed 2026-08-18, spec `20260818-1525-02` OQ-2) routed the
specs and backlog writers to a global sidecar and deliberately slimmed the inline block, keeping exactly
one line so `aw attention`'s `last_history_at` derivation keeps working. `backlog._reattach_history`
(`backlog.py:628-649`) implements it, and its own comment says so: "the inline block keeps only the
LATEST record; the full chronological log lives in the global .aw/records/history.jsonl sidecar".

So the OBSERVED BEHAVIOR in the reproduction below is real and correctly measured, but it is the
feature working as designed, not a renderer bug. Two claims in the original report are WRONG and must
not be acted on: that `_render_item`'s fixed template is the cause (the slim happens in
`_reattach_history`, which exists precisely to carry prior history forward), and that the fix is to make
the section append-only (that would revert a reviewed decision and break the `attention` contract that
decision was shaped around).

## THE REAL DEFECT THIS EXPOSED, which is worse and is why the item stays open

**THE DURABLE HISTORY IS GITIGNORED, SO IT DOES NOT SURVIVE A CLONE.** The design is sound only if the
sidecar is as durable as the record it replaced. It is not:

```text
$ git check-ignore -v .aw/records/history.jsonl
.aw/.gitignore:11:records/history.jsonl	.aw/records/history.jsonl
```

Measured consequence on this very cleanup. Three `aw specs note` calls recorded substantial reasoning
(why spec `4w7d6s` was superseded rather than revised; why invariant `I-16` was added and what the
`I-09` misfiling was; why the cross-type finding must not be reported even at `info`). All three now
exist ONLY in the gitignored sidecar. What a fresh clone sees:

```text
$ grep -c '^- 2026' .aw/records/specs/20260910-2lcqno-...spec.md
1
$ grep -c '^- 2026' .aw/records/specs/20260828-pqsx96-...spec.md
1
```

The sidecar holds them (204 records total, including all four of mine), but a clone has none of it. So
the repository's own rule is violated by its own tooling: `AGENTS.md` states an answer must never live
only in a gitignored tree because it "would not survive", and the workflow-history convention exists so
the reasoning travels with the repo. Right now every `aw specs note` and `aw backlog set` message is
one machine away from being lost, and the loss is invisible because the inline line still looks present.

This is ALSO why the near-miss below mattered: on a multi-record item, the pre-`awhistory-02` records
still sitting inline are the ONLY committed copy, and a `set` call silently drops them. Measured: 5
backlog items still carry 4 to 7 inline records (`dcla4g` has 7), all of them legacy and all of them
committed-only.

## What should actually happen (supersedes the original suggested fix below)

Decide which of these the maintainer wants; do NOT revert `awhistory-02`:

1. **TRACK THE SIDECAR** (drop `records/history.jsonl` from `.aw/.gitignore`). Smallest change, makes the
   durable log actually durable. Cost: it is append-only per machine and would conflict on concurrent
   writes, which is presumably why it was ignored in the first place. That reason should be checked
   rather than assumed.
2. **KEEP MORE THAN ONE INLINE RECORD** (say, the latest N, or every record whose message exceeds a
   trivial length). Keeps provenance committed without abandoning the slimming rationale.
3. **REFUSE TO SLIM A RECORD THE SIDECAR CANNOT HOLD**, i.e. write inline whenever the sidecar write
   fails. Note `backlog.py:557` swallows sidecar failures in a bare `except Exception: pass`, so today a
   failed sidecar write plus a successful slim loses the record entirely with no signal.
4. **ACCEPT IT AND FIX THE DOCS**, stating plainly that inline history is a one-line pointer and that
   durable history is machine-local. Honest, but it contradicts the durability rule in `AGENTS.md`.

RECOMMENDATION: (1) plus (3), because together they make the claim "the full log lives in the sidecar"
actually true. (2) is the fallback if tracking the sidecar is genuinely unworkable.

## ALSO STILL TRUE AND WORTH FIXING INDEPENDENTLY

There is no `aw backlog note` verb (only `new`, `set`, `check`), which is why annotating an item at all
requires a status-setting call. `aw specs note` exists and is the obvious precedent. Adding it would
remove the need to abuse `set` for annotation, which is how this whole thread started.

---

## ORIGINAL REPORT, PRESERVED (its diagnosis is wrong; its measurements are correct)

`aw backlog set <item> --status <its CURRENT status> --message "..."` REBUILDS the item from a fixed
template instead of appending to it, so the entire `## Workflow history` section is replaced by a single
`created` line. Every prior history record is silently deleted. The command exits 0 and prints a normal
success line, so nothing signals the loss.

## How it was found (a live near-miss, not a lab exercise)

Hit on 2026-09-10 while trying to append a correction note to backlog item `sjsoqq` (a `graduated` item
carrying two history lines, one of them a long graduation record). The command reported success; a
`git diff` showed `1 insertion, 2 deletions`, i.e. BOTH existing history lines gone. Reverted with
`git checkout --` before committing, so nothing was lost permanently. Had this been run by an agent that
commits without inspecting the diff, the graduation record would have been destroyed in history.

## Reproduction (isolated, deterministic)

Scratch repo, one item carrying two history lines, status `open`, set to `open` again:

```text
=== BEFORE: history lines = 2
aw backlog set: 20260910-tst-01-zzzzz9-demo.backlog.md -> open
=== AFTER: history lines = 1
=== was MY NEW NOTE written? 1
=== remaining history:
## Workflow history
- 2026-09-10 set (aw backlog): MY NEW NOTE
```

Both pre-existing lines (`- 2026-09-01 created ...`, `- 2026-09-02 note ...`) are gone. The new message
IS written, so this is not a no-op: it is a destructive overwrite that looks like a successful append.

## Cause

`backlog._render_item` (`agent_workflows/backlog.py:330-337`) builds the history section from scratch:

```python
today = datetime.date.today().isoformat()
msg = (message or "").strip() or item.summary
lines.append("")
lines.append("## Workflow history")
lines.append(f"- {today} created (aw backlog): {msg}")
```

It emits exactly one history line and never reads the existing one. Any write path that routes through
this renderer therefore truncates history. This is the SAME fixed-template renderer that plan `bwgyum`
already flagged (its F-11) for silently dropping unknown front-matter fields, so the renderer has two
known data-loss modes and the field-dropping one was patched per-field rather than at the root.

## Relationship to the other same-status defect (`x6tk1u`)

`x6tk1u` records that `aw set` on a SAME-STATUS artifact silently DISCARDS `--message`
(`status_set.apply_status_change` returns early before the history write). This item is a DIFFERENT and
worse failure on the backlog path: the message is written and the PRIOR HISTORY IS DELETED. Fixing one
does not fix the other, and a fix for `x6tk1u` that simply lets the same-status path proceed could route
into this renderer and turn a silent no-op into silent destruction. FIX THIS ONE FIRST, or fix them
together.

## Suggested fix

Make the history section APPEND-ONLY on any re-render: read the existing `## Workflow history` block,
preserve every line in order, and add the new record at the end (the convention every other record type
follows, e.g. `aw specs note`). Do not special-case the same-status path only; the renderer is wrong for
every caller that re-renders an existing item.

TRAP TO AVOID, carried from `x6tk1u`: do NOT make every same-status call write a line, or idempotent
re-assertion grows duplicate history. The message's PRESENCE is the discriminator.

ALSO WORTH FIXING: there is no `aw backlog note` verb (only `new`, `set`, `check`), which is why
appending a note requires a status-setting call at all. `aw specs note` exists and is the obvious
precedent. Adding it would remove the need to abuse `set` for annotation.

## Verification this needs

1. An item with N history lines, re-rendered by any path, still has all N plus at most one new line.
2. The measured two-line case above, as a regression fixture.
3. A same-status call with NO `--message` adds nothing (no duplicate growth).
4. The field-dropping mode (`bwgyum` F-11) is not reintroduced by the fix.
