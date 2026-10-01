- Id: gh409m
- Status: open
- Set: gh409m
- Priority: medium
- Work-Kind: chore
- Summary: Persist the --evidence citation on a backlog item when it closes via the SATISFIED path, so a later audit can distinguish a legitimately evidenced close from an ungated one

## Workflow history
- 2026-10-01 created (aw backlog): Persist the --evidence citation on a backlog item when it closes via the SATISFIED path, so a later audit can distinguish a legitimately evidenced close from an ungated one

Filed while authoring plan 1hrlp3 (backlog mbjuv5), which deferred this row and needs a durable carrier for it.

THE DEFECT IS A GAP IN THE DURABLE RECORD, NOT IN THE GATE. `backlog.run_set` reads `evidence=getattr(args, "evidence", None)` and hands it to `check_engine.evaluate_blocking_close`, which returns a SATISFIED verdict when the citation resolves. Nothing then writes the citation to the item. So a close that was fully legitimate leaves no trace of WHY it was legitimate, and the item on disk is byte-indistinguishable from one closed with no evidence at all.

WHY IT MATTERS CONCRETELY: it is the reason audit plan 1hrlp3 can only ever publish an UPPER BOUND. That audit found 53 historical done items whose on-disk state yields an error verdict, and it cannot narrow the number, because any of them may have been closed through SATISFIED with a citation that was consumed and discarded. Persisting the citation would make a future audit decisive instead of upper-bounded.

SCOPE WARNING: this changes the backlog record SCHEMA plus the setter's write path, which is why 1hrlp3 (a read-only audit) deliberately did not take it. Consider which field name is right, whether the existing `## Workflow history` close message is the better home than a new metadata bullet, and whether `status_set.run_set_command` (the positional spelling, which plan 47ttnv wired to the same predicate) must write it too, since a field written by only one of the two spellings would reproduce exactly the asymmetry class that 47ttnv, 43p53n and the gate-defaulting plans each had to fix in turn.
