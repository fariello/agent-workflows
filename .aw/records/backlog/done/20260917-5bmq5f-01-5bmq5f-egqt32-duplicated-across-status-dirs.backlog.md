- Id: 5bmq5f
- Status: done
- Set: 5bmq5f
- Priority: medium
- Work-Kind: bug
- Summary: Backlog item egqt32 exists in BOTH done/ and graduated/, so aw backlog check fails closed

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: fixed by 36129255: egqt32 exists only in backlog/done/
- 2026-09-18 open (aw set): Gated on next per the every-live-bug-gates-the-release rule (AGENTS.md); backfilled by nobugship rgaasb E-04.
- 2026-09-17 created (aw backlog): Backlog item egqt32 exists in BOTH done/ and graduated/, so aw backlog check fails closed

OBSERVED 2026-09-17 while executing rununify 05 (ct4w0a); PRE-EXISTING and unrelated to that plan.

`aw backlog check` exits 1 with:

    20260901-hookretry-01-egqt32-hook-rewrite-forces-commit-round-trip.backlog.md: backlog.id-duplicate: id egqt32 also in 20260901-hookretry-01-egqt32-hook-rewrite-forces-commit-round-trip.backlog.md

The same filename is tracked in TWO status directories:

    .aw/records/backlog/done/20260901-hookretry-01-egqt32-hook-rewrite-forces-commit-round-trip.backlog.md
    .aw/records/backlog/graduated/20260901-hookretry-01-egqt32-hook-rewrite-forces-commit-round-trip.backlog.md

Both are tracked (not working-tree litter), so this is committed state and it makes the backlog contract check fail closed for every agent that runs it, on every branch. It most likely arose from a `graduated` -> `done` transition that copied rather than moved, or from a merge that resurrected the source path.

NOTE THE DIAGNOSTIC IS ALSO CONFUSING: the message names the same basename twice, so it reads as though a file duplicates itself. Reporting the two DIRECTORIES would make the fix obvious without a filesystem search.

FIX: decide which status is authoritative (the item's own `- Status:` line and history should say) and `git rm` the other copy. Not done here because the item belongs to the `hookretry` Set and is outside ct4w0a's declared Scope-Paths.
