- Id: vaboqp
- Status: open
- Set: vaboqp
- Priority: medium
- Work-Kind: bug
- Summary: runner statusline always shows Review: both drivers derive the action label from a queue status that is never approved/to-review

## Workflow history
- 2026-08-31 created (aw backlog): runner statusline always shows Review: both drivers derive the action label from a queue status that is never approved/to-review

OBSERVED by the maintainer during a live run of y6mfgo (run-20260831T153226Z-3424176), an EXECUTE run whose statusline read `Review IPD` for its whole duration.

## The bug

Both drivers build the statusline's action column from the QUEUE ITEM'S `status`:

    action=("Review" if item.get("status") == "to-review"
            else ("Execute" if item.get("status") == "approved" else "Review"))

  - `agent_workflows/oc_runipd.py:4150-4154`
  - `agent_workflows/agy_runipd.py:2800-2804`

But a queued item's `status` is set to the literal `"queued"` (or `"reviewed"`) at
`oc_runipd.py:2954`, NEVER to `approved` or `to-review`. Both branches therefore always
miss and every run falls through to the else, so the column reads `Review` for an execute
run AND for a review run. Reproduced against the shipped expression with the real queue-item
shape: an `action=execute` item yields `'Review'`.

The plan's own status is `approved`; the QUEUE item's status is not, and that is the
confusion. The values the code tests for are the PLAN'S lifecycle statuses, which the queue
builder deliberately maps away from because a queue entry tracks run progress, not plan
readiness. `initial_status` (also set at :2954) preserves the plan's real status.

## The fix is already present in the same function

`item.get("action")` is the item's real intent and the SAME function already uses it
correctly 80 lines later:

    is_review = item.get("action") == "review"        # oc_runipd.py:4067

so the label should derive from `action` (values: `review`, `execute`, `orchestrate`), not
from `status`. `render_stream.ACTION_DISPLAY_MAP` already maps `review|execute|exec|
graduate|validate` to display labels, so passing the raw action through
`format_action_label` needs no new vocabulary. Note `orchestrate` is NOT in that map and
would render as `Orchest` via the truncating fallback; decide whether to add it explicitly.

## Why no test caught it

`tests/test_render_stream.py:293` covers `format_action_label` thoroughly IN ISOLATION,
including `None -> "Review"`, and `:444` passes `action="Execute"` directly to the
Statusline. So the formatter is correct and proven; nothing tests the CALLER'S derivation
from a queue item. A regression test should build a queue item the way `_build_queue` does
and assert the rendered column, in BOTH drivers.

## Severity

Cosmetic but genuinely misleading: an operator watching a long unattended run cannot tell
from the statusline whether the driver is reviewing or executing, and those have very
different consequences (a review edits a plan; an execute edits product code). It also
makes `format_action_label`'s careful `None -> Review` default look intentional here when
in fact the argument is never absent, just always wrong.

Also note `format_action_label`'s default of `Review` for a missing action means this class
of caller bug FAILS QUIET rather than loud. Worth considering whether an unrecognized or
absent action should render something visibly wrong (e.g. `?`) instead of the most common
real value.
