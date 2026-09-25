- Id: 9eiwnl
- Status: done
- Set: 9eiwnl
- Priority: medium
- Work-Kind: followup
- Summary: The lane session-promotion ordering pin has no behavioral equivalent yet

## Workflow history
- 2026-09-25 done (aw set): OBSOLETE at 877545fc, closed during graduate-top10 triage: moot: tests/test_lane_session_isolation.py deleted in 19313eed
- 2026-09-17 created (aw backlog): The lane session-promotion ordering pin has no behavioral equivalent yet

Plan yrqyxb E-03 produced a behavioral equivalent for seven of the eight execute_item ordering pins, all implemented and passing in tests/test_rununify_execute_item_gates.py. The eighth, tests/test_lane_session_isolation.py:125, asserts a STRUCTURAL property (the state['set_sessions'][...] promotion sits under a work_dir guard) and cannot be replaced by a call-graph assertion. The honest behavioral equivalent is a driver-level test that runs two lanes and asserts the second does not inherit the first's session, which needs a real git repo and the driver role and therefore belongs with the host CLI suites rather than with the fast characterization net. Until it exists, a split of execute_item would have to re-base that pin on source text again, which is the weakest of the available options. Not blocking: the existing pin passes today and is untouched.
