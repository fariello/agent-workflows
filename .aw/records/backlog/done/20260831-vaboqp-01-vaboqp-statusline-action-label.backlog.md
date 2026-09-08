- Id: vaboqp
- Status: done
- Set: vaboqp
- Priority: medium
- Work-Kind: bug
- Summary: runner statusline always shows Review: both drivers derive the action label from a queue status that is never approved/to-review

## Workflow history
- 2026-09-08 done (aw set): OBSOLETE: the fix landed in 7884379a on 2026-09-04, in the exact shape this item recommended. Verified at HEAD by symbol: both drivers call the shared render_stream.statusline_action_for_item:874 (oc_runipd.py:5538, agy_runipd.py:2904) whose docstring names vaboqp; the defective status-based expression is gone from both; ACTION_DISPLAY_MAP gained explicit orchestrate/orchest entries (render_stream.py:836-837), which was the open sub-decision; and the regression test this item specified exists as tests/test_render_stream.py:1559 StatuslineActionDerivationTests (3 passed) with both-driver coverage pinned by tests/test_runner_refork_guard.py:97 (9 passed). Gate RELEASED rather than transferred: no remaining work carries it. The item's separate closing note (format_action_label's quiet None -> Review default) is deliberately not carried forward, because statusline_action_for_item never returns empty so that branch is unreachable from either driver.
- 2026-09-03 set (aw backlog): GATED by the 2026-09-03 all-bugs-block-release audit (maintainer rule: we do not ship with known bugs). Work-Kind is bug and the defect is live on main, so the item now carries Blocks-Release: next. Status and Priority unchanged; no code touched.

OBSOLETE 2026-09-08, VERIFIED IN-REPO. DO NOT GRADUATE THIS ITEM: the fix it asks for HAS ALREADY
LANDED, and it landed in the exact shape this item recommended. Commit `7884379a` (2026-09-04,
"fix(render_stream): derive statusline action from item action instead of queue status") replaced the
defective expression in BOTH drivers.

WHAT THIS ITEM ASKED FOR, AND WHERE EACH PART NOW LIVES, every part checked at HEAD by symbol:

  1. "The label should derive from `action`, not from `status`." DONE. The three-way `status ==
     "to-review" / "approved" / else` expression is GONE from both drivers. Both now call one shared
     helper: `action=statusline_action_for_item(item)` at `oc_runipd.py:5538` and
     `agy_runipd.py:2904`. The helper (`render_stream.statusline_action_for_item:874`) reads
     `item["action"]` first and its docstring names this item (`vaboqp`) as the defect it fixes,
     falling back to `initial_status` then `status`, defaulting to `execute`.
  2. "Decide whether to add `orchestrate` explicitly, since it would render as `Orchest` via the
     truncating fallback." DONE, and decided the way this item preferred. `7884379a` added BOTH
     `"orchestrate": "Orchest"` and `"orchest": "Orchest"` to `ACTION_DISPLAY_MAP`
     (`render_stream.py:836-837`) and updated `format_action_label`'s docstring to list it, so the
     label no longer depends on the 7-char truncating fallback.
  3. "A regression test should build a queue item the way `_build_queue` does and assert the rendered
     column, in BOTH drivers." DONE, and it is the assertion this item specified.
     `tests/test_render_stream.py:1559` opens `StatuslineActionDerivationTests`, whose docstring cites
     `vaboqp` by name; `test_queue_item_renders_execute_action_in_statusline` (`:1610`) builds a queue
     item with `initial_status="approved"`, `action="execute"`, `status="running"` (the real shape the
     queue builder produces) and asserts the rendered line contains `Execute` and NOT `Review`. BOTH
     drivers are covered: `tests/test_render_stream.py:1496-1503` asserts the helper is the SAME
     OBJECT in `oc_runipd` and `agy_runipd`, and `tests/test_runner_refork_guard.py:97` carries
     `statusline_action_for_item` as a row in the symmetric AST-based re-fork guard, so neither host
     can silently re-fork it. Re-run at HEAD: 3 passed (StatuslineAction), 9 passed (refork guard).

WHAT SURVIVES, AND IT IS NOT THIS ITEM'S DEFECT. The item's closing paragraph raised a SEPARATE,
still-open design question: `format_action_label` still returns `"Review"` for a missing action
(`render_stream.py:857-858`), so an unrecognized or absent action fails QUIET as the most common real
value rather than rendering something visibly wrong. That is deliberately NOT carried forward as work
here, because the caller bug that made it dangerous is fixed: `statusline_action_for_item` never
returns an empty value (its final fallback is the literal `"execute"`), so the `None -> "Review"`
branch is no longer reachable from either driver's statusline. The quiet default is now a defensive
branch on an unreachable path, which is a cosmetic preference and not a live defect. Anyone who still
wants `?` for an unknown action should file that as its own item; it needs no release gate.

WHY THIS IS `done` AND NOT `parked`: the requested change exists in the tree, in both drivers, with the
regression test this item asked for and the `orchestrate` decision it flagged. Nothing awaits a decision
or an opportunity. The gate is RELEASED rather than transferred, because no remaining work carries it.

Evidence citation for the close: `.aw/records/plans/executed/20260829-terseout-01-ntf6sx-make-coding-agent-reporting-concise-across-opencode-agy-code.ipd.md`
is NOT the carrier; the fix landed as a direct maintainer commit (`7884379a`) with no IPD, which is why
this item is closed on cited in-tree evidence plus that commit rather than by handoff to a plan.

ORIGINAL ITEM TEXT BELOW, PRESERVED. Its diagnosis was correct and its recommendation was adopted
verbatim; only its status is stale.

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
