- Id: krwj2o
- Status: open
- Set: krwj2o
- Priority: medium
- Work-Kind: chore
- Summary: Restore deleted CLI conformance test gates and refresh stale goldens

## Workflow history
- 2026-10-01 created (aw backlog): Restore deleted CLI conformance test gates and refresh stale goldens

Restore deleted CLI quality and conformance gates (tests/test_cli_quality_gates.py and tests/test_cli_conformance_matrix.py, removed by 19313eed; see audit xvp5vx) so tests/conformance_matrix.py and twelve goldens under tests/fixtures/conformance_goldens/ are exercised again (F-04). Refresh unrelated stale remediation strings in check_findings.human.golden (F-05).
