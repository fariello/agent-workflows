- Id: xd78mr
- Status: open
- Set: awphysical
- Priority: high
- Kind: chore
- Summary: awphysical Order 12 E-06: bind every acceptance-manifest expected token to a named test method + schema validator that loads each test (blocks Order 12 completion + spec implemented)

## Workflow history
- 2026-08-17 created (aw backlog): awphysical Order 12 E-06: bind every acceptance-manifest expected token to a named test method + schema validator that loads each test (blocks Order 12 completion + spec implemented)

The 44-scenario manifest (tools/awphysical/migration-scenarios.json) + ScenarioCatalogTests exist and pass, and the behaviors are covered by the executed acceptance suite, but Order 12 E-06 additionally requires: (1) a machine-readable binding of every scenario 'expected' token (and every legacy_crosswalk 1-25 assertion token) to one or more fully-qualified automated test methods + a named assertion condition; (2) a schema validator that LOADS each named test and rejects missing/stale/duplicate/unbound tokens; (3) a deliberately-bad-binding fixture that MUST fail. The evidence-matrix names tests.test_acceptance_matrix.PhysicalLayoutAcceptanceTests.test_e06 which does not exist. Completing this unblocks the Order-12 (pszk6x) terminal transition and lets the controlling spec 20260810-1447-01 advance to implemented (with orchestrator 00 closeout). Bounded test-infra work; no product-code change expected.
