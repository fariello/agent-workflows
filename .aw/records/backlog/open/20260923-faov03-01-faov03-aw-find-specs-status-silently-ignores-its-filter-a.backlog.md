- Id: faov03
- Status: open
- Blocks-Release: next
- Set: faov03
- Priority: medium
- Work-Kind: bug
- Summary: aw find specs --status silently ignores its filter, affecting seven record types

## Workflow history
- 2026-09-23 created (aw backlog): MEASURED 2026-09-23 at HEAD a7e27f4a while executing plan ui8b9b: 'aw find specs --status to-review' and 'aw find specs --status bogusvalue' each return the SAME full list at exit 0, and the --status to-review output visibly lists specs whose status is 'approved'. So a caller cannot distinguish a real filtered answer from an unfiltered one, and an INVALID status value is accepted silently rather than refused.

ROOT CAUSE, already located by spec 6m4kow's review and re-verified here: cli._find_type_records's 'All other types' branch never consults explicit_flags.status, unlike the 'plans' and 'research' branches which each call a query(...) helper. So the defect affects SEVEN record types, not just specs.

WHY THIS IS A BUG AND NOT A CHORE (per the AGENTS.md perceptibility test): the output is WRONG, not merely slow. An operator or agent asking 'which specs await review' gets every spec in the repository at exit 0, with no signal that the filter did nothing, which is a user-perceptible incorrect answer.

WHY IT IS FILED NOW: it has been recorded in spec 6m4kow's honest-limits section since 2026-09-13 with the explicit note that it 'is not tracked by any backlog item, which is itself a gap'. Executed plan 5slbpi deliberately AVOIDED the filter rather than fixing it (its D4, the fix being outside its scope) and used check_engine._iter_spec_records instead; plan ui8b9b likewise routed around it via runner_shared.discover_specs. Two plans have now navigated around this defect, so it is filed rather than worked around a third time.

NOTE THE POPULATION FIGURE IN THE SPEC IS ALREADY STALE and should not be trusted: it recorded 32 specs, then 33; re-derive at fix time rather than citing a count.

WHERE: agent_workflows/cli.py, _find_type_records, the 'All other types' branch.
