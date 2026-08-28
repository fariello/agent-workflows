- Id: 43p53n
- Status: open
- Blocks-Release: next
- Set: gateclear
- Priority: high
- Kind: bug
- Summary: aw backlog set (leaving blocked) must clear the Gate-Kind/Gate-Ref fields; today it moves status but leaves stale gate fields, so aw backlog check then fails gate-unexpected and forces a hand-edit

## Workflow history
- 2026-08-28 created (aw backlog): aw backlog set (leaving blocked) must clear the Gate-Kind/Gate-Ref fields; today it moves status but leaves stale gate fields, so aw backlog check then fails gate-unexpected and forces a hand-edit

BUG: 'aw backlog set open <id6>' (or any transition OUT of blocked) changes Status but does NOT remove the item's '- Gate-Kind:'/'- Gate-Ref:' lines. The result fails 'aw backlog check' with 'backlog.gate-unexpected: gate fields present on a non-blocked item', forcing the operator to hand-edit the file to delete the gate lines - exactly the untooled hand-edit the house rules forbid.

REPRO (observed this session): filed i97baj as blocked with a gate, then 'aw backlog set open i97baj'; the item moved to open/ but retained Gate-Kind/Gate-Ref; 'aw backlog check' reported gate-unexpected; had to hand-delete lines 7-8.

DESIRED: when a 'set' transition lands on any non-blocked status (open/parked/done), the setter clears Gate-Kind/Gate-Ref automatically (they are only valid while blocked). Symmetric with the existing rule that moving TO blocked requires the typed pair. Consider whether an explicit '--keep-gate' escape is ever wanted (likely not; a non-blocked item has no valid gate). Add a regression test: set blocked-with-gate -> set open -> 'aw backlog check' is clean with no gate fields remaining.

DISCOVERED: while correcting a mis-classified backlog item (blocked -> open) this session.
