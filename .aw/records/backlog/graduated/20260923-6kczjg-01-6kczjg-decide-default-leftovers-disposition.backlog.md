- Id: 6kczjg
- Status: graduated
- Graduated-To: setprompt
- Set: 6kczjg
- Priority: medium
- Work-Kind: chore
- Summary: Decide whether aw install --to-aw should default --leftovers to remove now that the cleanup path is reachable and tested

## Workflow history
- 2026-09-26 graduated (aw set): Graduated 2026-09-26 into plan o7k6lt (Set setprompt), re-verified live at HEAD.
- 2026-09-26 note (aw backlog): Maintainer ruling 2026-09-26 (/askme during batch graduation): with nothing saved, an unattended aw install --to-aw migration defaults --leftovers to REMOVE (git-tracked leftovers only, recoverable from history; untracked content, private lanes and skills are preserved). Ordered after je74a0, which adds the saved defaults.leftovers answer.
- 2026-09-23 created (aw backlog): Decide whether aw install --to-aw should default --leftovers to remove now that the cleanup path is reachable and tested

Carrier for a deliberately deferred obligation in plan z1yefm (migleftover Order 01).

WHAT IS DEFERRED
z1yefm made a cleanup disposition REACHABLE from an install-driven migration (`aw install
--to-aw --leftovers {keep,remove,defer}`) but deliberately kept `defer` as the non-interactive
default, so nothing became destructive without an explicit choice. Flipping the default to
`remove` is a destructive-by-default change to a migration and is the maintainer's call.

WHY IT IS NOW A CHEAP DECISION
The plan's E-05 test (`tests/test_layout_migration.py::InstallMigrationResidueSweepTests`)
already pins the whole `remove` outcome, including that `.agents/skills` SURVIVES, so the flip
is a one-line change with regression cover already in place.

SEQUENCING
The maintainer's OQ-01 ruling was that a policy question like this should ASK, with the prompt
DEFAULTING TO THE ENCOURAGED ACTION, and that the answer must be SAVEABLE so users are not
nagged on every install. That persistence mechanism is backlog `kapm7y`. So the natural order is
`kapm7y` first (prompt + remember), and this item is then either satisfied by that prompt's
default or becomes the narrower question of what the NON-INTERACTIVE default should be.
