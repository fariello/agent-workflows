- Id: p7k57l
- Status: graduated
- Graduated-To: p7k57l
- Set: p7k57l
- Priority: medium
- Work-Kind: chore
- Summary: restore the runner layering and shared-not-copied guards deleted with tests/test_runner_layering.py and tests/test_runner_backlog_close.py

## Workflow history
- 2026-10-01 set (aw backlog): graduated by run run-20260930T053059Z-3200713: 1o7i7g
- 2026-09-29 created (aw backlog): Filed while authoring plan nf71bz (backlog 2kspdy). The 19313eed suite trim deleted tests/test_runner_layering.py and tests/test_runner_backlog_close.py, which together were the ONLY guards on two live conventions: (a) the host-neutrality criterion that decides whether a symbol may be shared between oc_runipd and agy_runipd, and (b) the shared-not-copied structural property that each host's backlog-close wrapper is a SINGLE delegating statement naming runner_shared.<same name>, which comment blocks in BOTH drivers still cite as asserted by tests/test_runner_backlog_close.py::SharedNotCopied. MEASURED: grep for SharedNotCopied across tests/ returns zero hits, and git log --diff-filter=D names 19313eed as the deleting commit. WHY IT MATTERS, with a concrete cost already paid: with those guards gone, plan 1f7xno re-homed process_backlog_close into runner_shared verbatim and carried a hardcoded 'aw oc run' host label through the move with a fully green suite; that defect is backlog 2kspdy, and plan nf71bz fixes the one string and pins the one message, deliberately NOT restoring the broader layering coverage. So this item is the carrier for that broader restoration. Related to the same family as xvp5vx (audit what lost its only guard in the trim); this item is narrower and names the two specific files and the two specific properties.
