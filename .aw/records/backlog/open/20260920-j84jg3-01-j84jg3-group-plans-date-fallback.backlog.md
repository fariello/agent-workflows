- Id: j84jg3
- Status: open
- Blocks-Release: next
- Set: j84jg3
- Priority: medium
- Work-Kind: bug
- Summary: aw group plans renames a plan with no - Date: line to the literal 20260101 where aw rename preserves its date

## Workflow history
- 2026-09-20 created (aw backlog): Filed while executing plan e3hzyc (F-13): a second, measured divergence between group and rename, deliberately excluded from that plan's fence.

MEASURED WHILE EXECUTING PLAN e3hzyc, which fixed the ORDER divergence between `aw group plans` and `aw rename plans` and deliberately left the DATE divergence alone.

THE DIVERGENCE. `plan_set_assign` derives the new filename's date from `_plan_date(text)` alone, i.e. the front-matter `- Date:` line, whose no-match fallback is the literal string "20260101" (agent_workflows/plans_refs.py:113-118). `run_mv` instead prefers the CURRENT FILENAME's date and only falls back to the front matter (`parsed_name.group("date") if parsed_name else _plan_date(text)`). So for a plan carrying no `- Date:` line, `aw group plans <id6> --set X --rename --apply` renames it to `20260101-...` while `aw rename plans` on the same file preserves its real date.

WHY IT WAS NOT FIXED THERE: bundling a second field's behavior change into the Order fix would have made that fix unreviewable, and e3hzyc's approval gate required this be FILED with its measurement rather than merely mentioned.

THE FIX SHAPE is the same three-tier idea the Order fix used: prefer the filename's own date, then the front matter, and treat the 20260101 literal as a last resort (or refuse rather than inventing a date).

BLAST RADIUS NOTE: the fallback also fires for a plan whose `- Date:` line is malformed rather than absent, and a wrong date in a clustered filename is not reported by `aw check plans`, the same reachability gap k9awrq owns.
