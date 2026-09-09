- Id: x6tk1u
- Status: open
- Set: setnotedrop
- Priority: high
- Work-Kind: bug
- Summary: aw set on a same-status artifact silently DISCARDS an explicit --message: apply_status_change returns early before the history write, so a deliberate provenance note exits 0 and is never recorded

## Workflow history
- 2026-09-08 created (aw backlog): aw set on a same-status artifact silently DISCARDS an explicit --message: apply_status_change returns early before the history write, so a deliberate provenance note exits 0 and is never recorded

FOUND 2026-09-08 the hard way: I ran `aw backlog set graduated <already-graduated item> --message
"<~2000 characters of measured evidence>"`, the command exited 0 and printed a normal-looking line, and
the note was NEVER WRITTEN. I only noticed because `git status` showed no modification. Had I trusted
the exit code, the evidence would have been silently lost and I would have reported it recorded.

REPRODUCTION, minimal and self-contained:

    $ printf -- "- Id: bbb222\n- Status: graduated\n- Set: demo\n- Priority: low\n- Work-Kind: bug\n- Summary: note drop proof\n\n## Workflow history\n- 2026-09-01 created (aw backlog): note drop proof\n" > .aw/records/backlog/graduated/x.backlog.md
    $ md5sum .aw/records/backlog/graduated/x.backlog.md
    d5a90247ade6c1e93106f941c79740e5  ...
    $ aw backlog set graduated .aw/records/backlog/graduated/x.backlog.md --message "IMPORTANT EVIDENCE THAT MUST NOT BE LOST"
    -    backlog     x  [low]  unchanged
    $ md5sum .aw/records/backlog/graduated/x.backlog.md
    d5a90247ade6c1e93106f941c79740e5  ...          # BYTE-IDENTICAL
    $ grep -c "IMPORTANT EVIDENCE" .aw/records/backlog/graduated/x.backlog.md
    0

Exit status 0. No warning, no diagnostic, no hint that the `--message` was discarded. The word
"unchanged" refers to the STATUS, so it reads as "status already correct, note recorded".

ROOT CAUSE, exact. `status_set.apply_status_change` computes a change predicate and RETURNS EARLY
before the history write (`agent_workflows/status_set.py:867-870`):

    content_changed = new_lines != lines
    path_changed = dest_path.resolve() != rec.path.resolve()

    if not content_changed and not path_changed:
        return rec.path, norm_status

The `hist_entry` construction and insertion sit BELOW that return (`:880-896`), so when the status is
unchanged and no other field mutation was requested, nothing is written. `content_changed` cannot
account for the message, because the message only ever enters `new_lines` via that later insertion.

THE FIX IS ALREADY DESIGNED IN THIS SAME FUNCTION, four times over. Every field write was deliberately
HOISTED out of the status branch for exactly this reason, each with a comment saying so:
`Blocks-Release` (`:715-721`, "MUST apply to plans and backlog too"), `From-Backlog` (`:723-732`, "so
`aw ipd set --from-backlog` persists even on a no-op (same-status) transition"),
`Item-Dependencies` (`:734-746`, "the SAME hoisted, status-branch-independent shape ... persists even
on a no-op"), and `Priority` (`:748-760`, same wording). A caller-supplied `--message` is the one
remaining mutation that does NOT survive a no-op, and the precedent for how to fix it is immediately
adjacent.

WHY THIS MATTERS MORE THAN A COSMETIC BUG. An explicit `--message` is the operator's or agent's
DELIBERATE act of recording durable evidence, and this repository's whole contract is built on written
provenance: the AGENTS.md execution contract requires pasting actual output and immortalizing findings,
and `graduated` items in particular accumulate long re-measurement notes that later readers are told to
trust. A setter that accepts such a note, exits 0, and drops it is a provenance-loss defect: the record
is not merely incomplete, it is silently incomplete, and the agent that wrote it has every reason to
believe otherwise. Same failure class as the two rename defects filed alongside this (`9yf5u9`,
`dl86am`): a mutation verb reporting success having written nothing.

SCOPE: NOT BACKLOG-ONLY. `apply_status_change` is the shared setter behind `aw set` / `aw ipd set` /
`aw spec set` / `aw prompts set` / `aw backlog set` (the positional `aw backlog set <status>
<selector>` form routes HERE, while `backlog.run_set` is the `--status` flag form and has its own
path). So verify the behavior on a same-status plan and spec too, and check whether `backlog.run_set`
has the same hole (it calls `_reattach_history` unconditionally at `backlog.py:539-540`, so it may
NOT -- if the two paths differ, that divergence is itself worth recording, since two spellings of one
verb should not disagree about whether a note is durable).

NOTE THE SIDECAR ALREADY GOT IT RIGHT, which sharpens the inconsistency: `backlog.run_set` appends the
message to the GLOBAL history sidecar via `record_history.append` (`backlog.py:544-559`) independently
of any content change. So on that path a note can land in the sidecar while never appearing inline.
Check what the `status_set` path does with the sidecar on a no-op; if it also writes there, the note
exists in one place and not the other, which is worse than a clean drop because the two disagree.

CANDIDATE FIXES:

1. PREFERRED, matching the four existing hoists: treat an explicitly-supplied `--message` as a
   mutation. Compute the history entry BEFORE the change predicate and include it in
   `content_changed`, so a same-status call with a message writes a history record and a same-status
   call WITHOUT one still returns early (preserving today's idempotence for tooling that re-asserts a
   status).
2. If a note-only write is judged out of scope for a status setter, then REFUSE loudly instead of
   succeeding silently: exit nonzero with "status already <x> and no field mutation requested; the
   --message was not recorded", and point at the verb that can record one.
3. Consider giving backlog a first-class `aw backlog note` verb. `aw specs note` already exists for
   precisely this need, and its absence here is why I reached for `set <same-status> --message` at all.

DO NOT fix this by making every same-status call write a history line unconditionally: tooling that
re-asserts a status idempotently would then append a duplicate record on every invocation, growing the
inline history without recording anything new. The message's PRESENCE is the discriminator.
