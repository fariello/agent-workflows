- Id: hg2oop
- Status: open
- Set: bklghist
- Priority: high
- Work-Kind: bug
- Summary: aw backlog set on a same-status item DESTROYS the existing workflow history, replacing every prior line with one new line, and exits 0

## Workflow history
- 2026-09-10 created (aw backlog): aw backlog set on a same-status item DESTROYS the existing workflow history, replacing every prior line with one new line, and exits 0

## The defect

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
