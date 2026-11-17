- Id: 6o5aan
- Status: open
- Set: 6o5aan
- Work-Kind: chore
- Priority: medium
- Summary: Bare python3 -m pytest core tier (2223 tests, 48.6s-63.7s) persistently exceeds 30.00s wall-time budget in conftest.py

> Write and proofread this backlog item per the technical writing standard, `.aw/system/workflows/technical-writing/technical-writing.md` (`.agents/workflows/technical-writing/technical-writing.md` in a legacy-layout install), including requirement 12 (diagrams).

## Workflow history
- 2026-11-17 created (aw backlog): Bare python3 -m pytest core tier (2223 tests, 48.6s-63.7s) persistently exceeds 30.00s wall-time budget in conftest.py

Observed during metastore plan n5sxxk verification on 12 CPUs (1-minute load average 5.56-6.35): bare python3 -m pytest passed all 2223 core tests (0 failed, 0 errors) in 63.73s and exited 1 solely because conftest.py::pytest_sessionfinish enforces the 30.00s budget in pyproject.toml ([tool.pytest.ini_options]). Bounded aw suite (which sets AW_CORE_BUDGET_ENFORCE=0 per ytz6z4) also exceeded 30.00s (48.63s, exit 0 with warning). Top slowest core tests measured 7.64s (test_status_json_is_valid), 5.18s (test_verification_polarity_matrix_and_agreement), 4.83s (test_status_human_unchanged), and 4.33s (test_verification_tiers_1_through_4_precedence). Trim or reclassify slowest core tests or adjust the 30.00s budget so bare python3 -m pytest exits 0 when all core tests pass.
