- Id: ncpc8z
- Status: done
- Graduated-To: ncpc8z
- Blocks-Release: next
- Set: ncpc8z
- Priority: low
- Work-Kind: bug
- Summary: test_stall_watchdog_does_not_trip_on_active_child flakes under parallel test suite load due to 0.5s timeout

## Workflow history
- 2026-10-13 done (aw backlog): closed by aw agy run: IPD masjx4 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-ncpc8z-01-masjx4-make-the-active-child-stall-watchdog-test-robust-to-interpre.ipd.md); evidence .aw/records/plans/executed/20261012-ncpc8z-01-masjx4-make-the-active-child-stall-watchdog-test-robust-to-interpre.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005606Z-2321569: masjx4
- 2026-10-03 created (aw backlog): test_stall_watchdog_does_not_trip_on_active_child flakes under parallel test suite load due to 0.5s timeout

WHAT IS WRONG: `tests/test_oc_runipd.py::StallWatchdogTests::test_stall_watchdog_does_not_trip_on_active_child` sets `--stall-timeout 0.5`. Under full parallel test suite load with 37+ xdist workers, Python process startup for `active_child` (`import json, pathlib, re, sys, time`) can exceed 0.5s before printing its first event line. The driver stall watchdog trips and kills the child (`KeyboardInterrupt` in importlib), failing the test with exit code 1. When run in isolation, the test passes reliably in ~7.5s.
