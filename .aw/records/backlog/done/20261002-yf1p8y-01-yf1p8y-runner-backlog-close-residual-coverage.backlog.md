- Id: yf1p8y
- Status: done
- Graduated-To: yf1p8y
- Set: yf1p8y
- Priority: low
- Work-Kind: chore
- Summary: Triage the behavioral coverage tests/test_runner_backlog_close.py held beyond the delegation guard (shutdown report, signal safety, exit codes, child kill)

## Workflow history
- 2026-10-15 done (aw backlog): closed by aw agy run: IPD z2ugxc executed (every IPD carrier is executed and this run executed .aw/records/plans/executed/20261012-yf1p8y-01-z2ugxc-triage-and-restore-the-residual-behavioral-coverage-of-the-d.ipd.md); evidence .aw/records/plans/executed/20261012-yf1p8y-01-z2ugxc-triage-and-restore-the-residual-behavioral-coverage-of-the-d.ipd.md
- 2026-10-12 graduated (aw backlog): graduated by run run-20261012T005641Z-2321995: z2ugxc
- 2026-10-02 created (aw backlog): Triage the behavioral coverage tests/test_runner_backlog_close.py held beyond the delegation guard (shutdown report, signal safety, exit codes, child kill)

Filed by /plan-review of plan 1o7i7g (backlog p7k57l). That plan restores ONLY the delegation and host-independence properties and defers the rest of the 2703 lines that 19313eed deleted from tests/test_runner_backlog_close.py: shutdown reporting, signal-handler safety, SIGINT/SIGTERM exit codes, the child-kill escalation path, and the committed-tree integrity self-check. Its deferred row named xvp5vx as the carrier, but xvp5vx is done and its census plan oyh28b treated this file as already OWNED by p7k57l, so it filed nothing for it. The residual was therefore owned by no one, and this item carries it. ALSO OWNS the sibling dangling-guard claims in runner_shared.py that cite deleted guards for the re-homed host-neutral block: 'which is what tests/test_runner_layering.py now freezes' and tests/test_runner_shared.py::ReHomedHostNeutralNameTests, neither of which exists. THE WORK: recover the file from 19313eed^, list the behavioral properties it asserted, check each against live coverage, and mutation-test any that look unguarded; and correct the two stale runner_shared.py claims. Restore behavioral outcomes only. Code, AST and text pins stay deleted per GUIDING_PRINCIPLES P16 and the xvp5vx maintainer ruling.
