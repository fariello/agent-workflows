- Id: 9pa9x3
- Status: open
- Set: 9pa9x3
- Work-Kind: chore
- Priority: low
- Summary: tests/test_notify_cli.py::test_listen_lifecycle_and_answering exceeds the 2s core slow-test threshold (~3.6s) and is missing from tests/slow_allowlist.txt

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 created (aw backlog): tests/test_notify_cli.py::test_listen_lifecycle_and_answering exceeds the 2s core slow-test threshold (~3.6s) and is missing from tests/slow_allowlist.txt

Observed during `g6tw94` core test execution: `tests/test_notify_cli.py::test_listen_lifecycle_and_answering` ran in 3.56s under bare `python3 -m pytest` and 3.59s under `aw suite`. Because the test carries the `core` marker and is absent from `tests/slow_allowlist.txt`, `conftest.py::pytest_terminal_summary` prints an unlisted slow-test warning. Add an allowlist entry in `tests/slow_allowlist.txt` with a justification or reduce the test's runtime below 2s so `SLOW TESTS REPORT` reports 0 unlisted slow tests.
