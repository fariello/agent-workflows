- Id: 3rmvik
- Status: open
- Set: 3rmvik
- Priority: medium
- Work-Kind: chore
- Summary: Restore test coverage for release readiness gates and report aggregation

## Workflow history
- 2026-10-01 created (aw backlog): Restore test coverage for release readiness gates and report aggregation

Measured at execution HEAD (4e6cae0959d870fdd6cc0568f89a4dac57029f74):

1. Searching tests/ for symbols in agent_workflows/release_readiness.py:
- gate_changelog_versioning: 0 test matches
- gate_residual_risk: 0 test matches
- build_report: 0 test matches
- gate_leak_scan: 1 test file (tests/test_release_readiness_child_pin.py, guarding subprocess child pinning and stdin denial only)
- gate_ipd_lint: 1 test file (tests/test_release_readiness_child_pin.py, guarding subprocess child pinning and stdin denial only)
The former suite tests/test_release_readiness.py was deleted in commit 19313eed.

Work-Kind rationale:
- Selected: chore. Release readiness gate tests are internal review verification tools.
- Rejected bug: Missing tests are not user-perceptible runtime defects.
- Rejected security: These gates check versioning and residual risk, not security hardening boundaries.
- Rejected followup: Not trailing work from an active plan.
