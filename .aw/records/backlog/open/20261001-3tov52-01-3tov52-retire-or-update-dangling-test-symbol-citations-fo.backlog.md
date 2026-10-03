- Id: 3tov52
- Status: open
- Set: 3tov52
- Priority: low
- Work-Kind: chore
- Summary: Retire or update dangling test-symbol citations for code pins in runner_shared and agy_runipd

## Workflow history
- 2026-10-01 created (aw backlog): Retire or update dangling test-symbol citations for code pins in runner_shared and agy_runipd

Several comments in runner_shared.py and agy_runipd.py cite deleted tests that were retired code pins (e.g. tests/test_review_findings_cascade.py::SharedPredicateTests which pinned attribute existence and source text, and tests/test_runner_stop_triggers.py which regexed subcommands out of source). Because these code pins were deleted per GUIDING_PRINCIPLES P16 and cannot return, the citing comments should be updated to remove or retire the dead citations.
