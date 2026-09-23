- Id: f2kqas
- Status: open
- Blocks-Release: next
- Set: rendrop
- Priority: medium
- Work-Kind: bug
- Summary: fixed-template record renderers silently drop unrecognized metadata fields, patched per field instead of at the root

## Workflow history
- 2026-09-23 created (aw backlog): fixed-template record renderers silently drop unrecognized metadata fields, patched per field instead of at the root

Found while executing plan `bwgyum`, which fixed ONE instance of this class and deliberately
deferred the general audit (see that plan's Deferred section) because it touches renderers the plan does not
otherwise open.

THE CLASS. `backlog._render_item` rebuilds an item's `- Field:` bullet block from a FIXED six-field
template, so ANY field outside that template is silently DROPPED when a write goes through it. Measured
2026-09-23 against HEAD: an item carrying `- Graduated-To: somesetid, othersetid` went through
`aw backlog set --status graduated <path>` and came out with the line GONE, exit 0, no warning.

IT IS PATCHED PER FIELD, WHICH IS THE EVIDENCE IT IS A CLASS RATHER THAN A BUG. `Blocks-Release` already
carries a re-apply-after-render workaround in `backlog.run_set`, and `bwgyum` added the identical
workaround for `Graduated-To` beside it (following the established pattern deliberately, rather than
widening the template). Every FUTURE optional field on a backlog item will hit the same trap and will need
the same third copy of the same workaround, and whoever adds that field will only discover the need if they
happen to test the `--status` spelling specifically.

WHAT TO AUDIT. Every other record renderer that rebuilds a metadata block from a fixed field list rather
than editing lines surgically, to see whether it drops unknown fields the same way. `status_set` is the
counter-example that shows the safe shape: it rewrites lines surgically and PRESERVES unknown fields, which
is why the same verb behaves correctly in its bare spelling and destructively in its `--status` spelling
(the two-path split is itself worth a look).

POSSIBLE FIX DIRECTION (not designed here). Make the renderer PRESERVE unrecognized bullets by default
instead of requiring each field to buy its own re-apply, so preservation is the property of the renderer
rather than a per-field patch that must be remembered.
