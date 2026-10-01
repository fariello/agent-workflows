- Id: h0tiaw
- Status: open
- Set: h0tiaw
- Priority: low
- Work-Kind: chore
- Summary: tests/conformance_matrix.py declares a json scenario and names a driver test_cli_conformance_matrix.py that does not exist, so the matrix is built but never asserted

## Workflow history
- 2026-09-30 created (aw backlog): Found authoring plan 9yd6tx (backlog 7tixnq) as its F-14. Measured: tests/conformance_matrix.py defines the scenario set (including a 'json' scenario required when a leaf declares --json or is read/check/bare) plus helpers semantic_facts_from_agent, semantic_facts_from_human and build_matrix, and its module docstring references tests/test_cli_conformance_matrix.py as the driver. No such file exists under tests/. So the matrix machinery is maintained but nothing executes it, which means any conformance drift it was built to catch goes unnoticed. Pre-existing and NOT worsened by 9yd6tx; recorded there as deferred because that plan adds its own targeted test module (tests/test_json_surface_leak_posture.py) rather than reviving a dormant harness, which would be a much larger and differently-shaped job. Open question for whoever takes this: whether the driver was ever written (check git history) and whether the intended contract is still the one the helpers encode, since reviving a stale harness can assert obsolete promises. Filed low priority because it is latent coverage debt, not a live defect.
