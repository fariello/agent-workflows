- Id: enygec
- Status: open
- Blocks-Release: next
- Set: enygec
- Priority: medium
- Work-Kind: bug
- Summary: aw attention, aw runs and aw partition echo a raw user-supplied selector into a hand-built aw.agent/v1 record, so a home-path selector crashes the machine surface with a ValueError traceback

## Workflow history
- 2026-09-29 created (aw backlog): Carrier filed while authoring plan wqiofa (backlog un6ppd). Measured live at HEAD 95d1d114: 'attention <path under the home directory> --agent' and '--json', and 'runs <same> --agent', each exit 1 with a ValueError traceback and EMPTY stdout. The trigger is the validator's unsanitized-home-path rule firing on the user's own selector token, which attention.unresolved_selector_agent_record and run_viewer.emit_unresolvable_target_refusal interpolate verbatim into unresolved_selectors/unresolved_targets AND into their error string. partition's agent branch does the same with user-supplied ids in 'unknown', and run_analytics_cli has two further direct render_jsonl_record callers. These sites are DELIBERATELY EXCLUDED from wqiofa: they build records by hand outside renderers.py, so wqiofa's guarded serializer never runs for them, and routing them through it would MASK the real defect (an unsanitized echo) behind a generic refusal instead of fixing it. The honest fix is to sanitize the input at each site (normalize_repo_path or equivalent) and decide per surface what a selector is SHOWN AS once sanitized, which is a per-verb product decision.
