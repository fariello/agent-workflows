- Id: wqk5s2
- Status: open
- Blocks-Release: next
- Set: wqk5s2
- Priority: medium
- Work-Kind: bug
- Summary: Two slow-marked end-to-end stop-trigger tests fail at HEAD: SIGTERM and terminal-rung runs record no 'stopped'/'interrupted' item state

## Workflow history
- 2026-09-21 created (aw backlog): Two slow-marked end-to-end stop-trigger tests fail at HEAD: SIGTERM and terminal-rung runs record no 'stopped'/'interrupted' item state

## What is wrong

Two `@pytest.mark.slow` end-to-end tests in `tests/test_runner_stop_triggers.py` FAIL at HEAD:

- `SigtermTests::test_a_real_sigterm_records_level_3_and_stops_at_a_checkpoint`, with
  `KeyError: 'stopped'` at `run.item("ta0001")["stopped"]`. The level-3 request IS recorded and the
  `deliberate-stop-at-checkpoint` event IS emitted; what is missing is the `stopped` record on the
  queue item.
- `PreExistingInterruptContractTests::test_the_terminal_rung_still_records_the_item_interrupted`,
  an `AssertionError`.

WHY IT WENT UNNOTICED: both are `slow`-marked, and `pyproject.toml`'s `addopts` carries
`-m 'not slow'`, so a bare `python3 -m pytest` (the contract's prescribed invocation) never runs
them. They are only reached by clearing the defaults, e.g.
`python3 -m pytest tests/test_runner_stop_triggers.py -o addopts=""`, which reports
`2 failed, 61 passed, 1 xfailed`.

## Where

`tests/test_runner_stop_triggers.py` (the two tests named above), against
`agent_workflows/runner_stop.py`'s level-3 / terminal-rung item bookkeeping. Whether the defect is in
the PRODUCTION recording or in the tests' expectation is exactly what needs deciding, and this item
does not presume: spec `c4gd2h` A3/R13 require a level-3 SIGTERM stop to leave the turn's outcome
KNOWN, and `install_stop_signal_handlers`' docstring states the terminal rung must leave the item
recorded `interrupted`, so a genuinely missing record would be a real conformance gap rather than a
stale assertion.

## Provenance

Found while executing IPD `wqq8ua` (stop-discoverability text). CONFIRMED PRE-EXISTING AND UNRELATED
to that change by stashing the whole change set and re-running both tests at the unmodified HEAD,
where both fail identically. `wqq8ua` is text-only on three operator-facing surfaces and touches no
level, budget, escalation rule, poll site or stop-request flag.

## Why it gates the release

`Work-Kind: bug` and live, so it carries `Blocks-Release: next` per the repository's
every-live-bug-gates-the-next-release policy. Note the user-visible stake if the production side is
at fault: an operator who sends SIGTERM to wind a run down is relying on the stopped item's outcome
being recorded, and `runner_stop`'s own level-4 design says an unrecorded outcome is what forces
reconciliation before a resume.
