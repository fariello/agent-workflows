- Id: 1gw7nl
- Status: graduated
- Graduated-To: smallfix
- Set: recstale
- Priority: low
- Work-Kind: chore
- Summary: Runner plan records leak a per-plan file read on the legacy-manifest path only, but three other rununify plans still cite the dissolved record split as a live reason

## Workflow history
- 2026-09-25 graduated (aw set): graduated into smallfix (plan 0i4fkt); verified live at 8e74dcac
- 2026-09-17 created (aw backlog): Found while executing rununify 06 (sy7uwh). Several in-tree comments and docstrings asserted the two hosts' PlanRecord types were distinct and used that as the REASON for an unrelated design choice. sy7uwh corrected the four it could reach inside its own Scope-Paths (runner_shared's module docstring, SpecRecord, SetMember, and the retirement section's no-third-mechanism note). Remaining risk: the same claim may be restated in plans and specs outside that fence, where a later reader would take it as current. Worth a sweep for the phrases 'per-host NamedTuples', 'oc's carries a kind', and 'two runners' PlanRecord' across .aw/records/ so no artifact keeps justifying a decision on a premise that no longer holds.
