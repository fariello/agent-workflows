- Id: 8cpbia
- Status: open
- Set: 8cpbia
- Priority: low
- Work-Kind: chore
- Summary: find_from_backlog_artifacts re-walks the whole plans and specs corpus per call, so any per-item loop over it is O(items x corpus)

## Workflow history
- 2026-09-18 created (aw backlog): find_from_backlog_artifacts re-walks the whole plans and specs corpus per call, so any per-item loop over it is O(items x corpus)

FOUND 2026-09-18 while executing nobugship rgaasb E-01, where the plan's literal instruction would have shipped this cost into aw check all.

WHAT IS WRONG. check_engine.find_from_backlog_artifacts (and its find_from_backlog_plans / find_from_backlog_specs halves) answers 'which artifacts carry a handoff for ONE item' by walking the ENTIRE plans tree plus the specs tree on every call. That is correct and cheap for a single item, which is how the setter gate and evaluate_blocking_close's HANDOFF branch use it. It is quadratic the moment a caller loops over items.

MEASURED on this checkout (671 plans, 34 specs, 65 candidate items):
  * 65 per-item find_from_backlog_artifacts calls: 11.13 s
  * ONE shared walk producing the identical {item -> carriers} mapping: 207 ms
  * ratio: 54x
A single corpus walk alone is 136 ms, so the cost is the repetition, not the parse.

FILED AS chore, NOT bug, and the reasoning is AGENTS.md's perceptibility test applied honestly: there
is TODAY NO SHIPPED CALLER that loops. rgaasb added the only rule that needed this shape and it
consumes a new shared index (_from_backlog_carrier_index) instead, so no user currently waits on the
11 s. The redundancy is provable but not user-perceptible, which is exactly the case the test calls a
chore rather than a defect. Had the per-item form shipped, it would have been a bug by the same test:
it would have added ~11 s to aw check all, a command an operator waits on.

WHY IT IS STILL WORTH FILING. The function's shape invites the quadratic use, the plan under execution
literally prescribed it (and required a grep proving it), and release_gate_warnings ALREADY records
having been bitten by exactly this and refactored away from it ('Calling find_from_backlog_plans for
every open blocker re-walked the complete plans tree per item, even when no warning existed'). That is
three encounters with one shape.

SUGGESTED FIX. Either document on find_from_backlog_artifacts that it is single-item-only and point
callers needing many items at _from_backlog_carrier_index, or reimplement the per-item functions on top
of a cached index so the misuse stops being expensive. The docstring note is the cheap half and is
probably sufficient.
