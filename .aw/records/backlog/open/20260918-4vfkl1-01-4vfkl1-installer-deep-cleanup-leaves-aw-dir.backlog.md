- Id: 4vfkl1
- Status: open
- Set: 4vfkl1
- Priority: medium
- Work-Kind: bug
- Summary: Two slow-marked test_installer deep-cleanup tests fail at HEAD: .aw/ remains after records removal

## Workflow history
- 2026-09-18 created (aw backlog): Two slow-marked test_installer deep-cleanup tests fail at HEAD: .aw/ remains after records removal

MEASURED 2026-09-18 at HEAD 6399c9f7 while executing wfartifacts Order 04 (l1c1iz).

WHAT IS WRONG. Two tests fail:

  FAILED tests/test_installer.py::UninstallCompletenessTests::test_deep_cleanup_records_remove_leaves_no_aw_directory
  FAILED tests/test_installer.py::DeepCleanupTests::test_plan_counts_and_all_recoverable_when_committed

The first asserts at `tests/test_installer.py:2964`:

  AssertionError: True is not false : NO .aw/ directory must remain after deep cleanup removing records

So a deep cleanup that removes the records tree leaves an `.aw/` directory behind.

NOT CAUSED BY THIS PLAN, PROVEN. Both fail with Order 04's three-file change STASHED (verified by
`git stash push` of the exact paths, re-running the two node ids, then `git stash pop`). They are
therefore pre-existing at HEAD.

WHY NOBODY SAW IT. Both are `slow`-marked, and `pyproject.toml` `addopts` carries
`-m 'not slow'`, so the contract-mandated bare `python3 -m pytest` never runs them: that run is
31 failed / 7989 passed both before and after this plan, with an EMPTY failure-set delta. They only
appear under `python3 -m pytest tests/test_installer.py -o addopts=""`.

WHY THAT MATTERS BEYOND THESE TWO. The repo's execution contract judges a change on the bare run's
failure-set delta, which is the right rule; but it means the slow subset can accumulate real
regressions invisibly. Worth deciding whether CI runs the slow marker on a schedule, since 'nothing in
the bare run regressed' is silent about this class of defect.
