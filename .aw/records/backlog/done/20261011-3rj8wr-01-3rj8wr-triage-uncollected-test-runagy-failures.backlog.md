- Id: 3rj8wr
- Status: done
- Graduated-To: 3rj8wr
- Set: 3rj8wr
- Priority: medium
- Work-Kind: followup
- Summary: Triage the 10 failing tests in uncollected tools/ipdrunner/test_runagy.py and bring it under a gate

## Workflow history
- 2026-10-16 done (aw backlog): closed by aw agy run: IPD oi9kr8 executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261014-3rj8wr-01-oi9kr8-verify-and-close-test-runagy-triage-relocation-and-collectio.ipd.md); evidence .aw/records/plans/executed/20261014-3rj8wr-01-oi9kr8-verify-and-close-test-runagy-triage-relocation-and-collectio.ipd.md
- 2026-10-14 graduated (aw backlog): graduated by run run-20261014T131015Z-4038279: oi9kr8
- 2026-10-12 created (aw backlog): Triage the 10 failing tests in uncollected tools/ipdrunner/test_runagy.py and bring it under a gate

Found while graduating n8adhb (plan 5s31xp). tools/ipdrunner/test_runagy.py is outside testpaths=["tests"], so no gate runs it. At HEAD 8538be828, `python3 -m pytest tools/ipdrunner/test_runagy.py -o addopts="" -q -p no:randomly` reports `10 failed, 15 passed`. Failure shapes: 7 subprocess runs exit 2 with RUN-STRUCTURE-PREFLIGHT IPD-M101 'Concern: required field missing' (the fixture plan predates the Concern field); one prompt-text assertion expects an older Concurrent Work paragraph than agy_runipd now emits; one dependency-satisfaction assertion (line ~314) gets False. Not yet known which failures are stale tests and which are product regressions; triage each, fix or retire, then relocate the module into tests/ and remove its exemption from the uncollected-test-module guard that 5s31xp adds.
