---
id: x96s18
created: 20261014
set: testmon-selection-measurement
order: 01
topic: [testing, suite-efficiency, testmon, test-selection]
model: 
kind: findings
status: active
outcome: rejected
summary: Measurement of pytest-testmon test selection on 20 consecutive real main commits
consumed-by: [1qut7y]
---

# Research Findings: Coverage-Based Test Selection (pytest-testmon) Measurement on Real Main Commits

- Date: 2026-10-14
- Status: done
- Plan Reference: IPD 1qut7y (Set `suiteeff`, Order 04)

## Objective

Empirically measure whether coverage-based test selection using `pytest-testmon` reduces agent iteration suite sizes and runtimes on this repository without sacrificing recall on failing tests, evaluated against a pre-stated adoption threshold across 20 consecutive real `main` commits from October 2026.

## Pre-Stated Adoption Threshold

ADOPT iff all three hold:
(i) the median selected fraction is <= 0.5;
(ii) minimum recall == 1.0 over all 20 steps; and
(iii) the control step selected and failed its broken test.
Otherwise DECLINE.

## Measurement Environment and Setup

- **Host Hardware & Cores**: `nproc` = 12
- **Load Average**:
  - Before measurement: `07:05:59 up 13 days, 19:44, 5 users, load average: 14.50, 16.51, 16.46`
  - After measurement: `11:43:51 up 14 days, 22 min, 5 users, load average: 7.09, 7.49, 7.47`
- **Package Versions**:
  - `pytest`: 9.1.1
  - `pytest-xdist`: 3.8.0
  - `pytest-testmon`: 2.2.0
  - `coverage`: 7.16.2
- **Coverage Core**: `COVERAGE_CORE=ctrace` (verified: the sysmon warning "Dynamic contexts aren't supported with core=sysmon; context data may be incomplete" did NOT appear).
- **Checkout**: Isolated scratch clone created via `git clone --shared --no-checkout /mnt/md1/VC/agent-workflows/.aw/worktrees/1qut7y /tmp/scratch_testmon_replay_1qut7y`, checked out per step via `git checkout --detach <sha>`, and deleted after measurement.
- **Virtual Environment**: Dedicated throwaway venv created at `/tmp/scratch_venv_1qut7y` and deleted after measurement.

## Exact Commands

1. Population derivation:
   ```sh
   git log --first-parent --reverse --since=2026-10-01 --until=2026-11-01 --format=%H main -- agent_workflows tests conftest.py pyproject.toml | tail -n 21
   ```
2. Selected suite per step:
   ```sh
   COVERAGE_CORE=ctrace python3 -m pytest --testmon
   ```
3. Baseline full suite per step:
   ```sh
   python3 -m pytest
   ```
   Both commands executed with the repository's configured `addopts` (`-q -n auto --dist=worksteal -m 'not slow and not livecorpus'`), with no forbidden flags (`-n0`, extra `-q`, or `-p no:randomly`).

## Replay Population (21 Commits)

- S0 (Database Build): `0638d4b23b1ed92d1a12b1b092d88eeb29b6b65f`
- S1: `21b8df8a981b409125f4edd78f15348de02e1875`
- S2: `b938ee3bb9edbfd37582c0e2f613ff9ebfef777d`
- S3: `3f388c880f59384226df8f2ba52eb51944da9b49`
- S4: `f2ef424da16529c7133aaa24745adb73b801be83`
- S5: `3379c12a5d95a9e599d57695bdb6b5440766ce17`
- S6: `9f39107fdbce83a15895f0788a18c4e7c0a3fb4e`
- S7: `05210b98ec4112654f779b0a15add2de847f3975`
- S8: `6808e3a74aec6ac0a0d940dda74e081b298162f0`
- S9: `e800986544ec1a230e1447f83a962f44ca4fedbf`
- S10: `3ae697cffea44d8ba6d25f21fd2ec8c7608b8424`
- S11: `b256e46116ee1bf5b28abad57c2462ba2a487c14`
- S12: `e64b89955f5e4f4ee83de6b9f30ecf48f1daa6da`
- S13: `3a8d2b200f225a0484ec914a6fd3ef4d64f126a6`
- S14: `3eaf8b89519f89be08716041a4d712d08ca5c633`
- S15: `8d5bbe95b7655d0d6dd4c273b831dcef631b50b2`
- S16: `11e030ea92b68b07d6200fb294040a7f1d4d642a`
- S17: `7ae3ad0ba9e2295923300b7e9c7bc2ad5bca5c41`
- S18: `a26ef9b0c9bf9b4c00bf040c70c90f5ee6565877`
- S19: `0c323ea3bd324cd4c64435a3b597ec8b4351c810`
- S20: `eccbe3f05cd6596aedbaab13f7b07d6410418e8d`

## Measurement Results

| Step | Commit SHA | Files Changed | Selected | Total | Fraction | Wall (Testmon) | Wall (Full) | Saving (s) | Load Valid | Failures (Testmon) | Failures (Full) | Recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | 21b8df8a9 | 13 | 8323 | 8323 | 100.0% | 571.7s | 338.2s | -233.5s | Yes | 0 | 0 | 1.00 |
| 02 | b938ee3bb | 9 | 6913 | 6913 | 100.0% | 430.6s | 300.9s | -129.7s | Yes | 49 | 49 | 1.00 |
| 03 | 3f388c880 | 75 | 6931 | 6931 | 100.0% | 315.4s | 247.1s | -68.3s | Yes | 49 | 49 | 1.00 |
| 04 | f2ef424da | 1 | 8372 | 8372 | 100.0% | 427.9s | 519.8s | 91.9s | No (discarded) | 0 | 0 | 1.00 |
| 05 | 3379c12a5 | 2 | 8372 | 8373 | 100.0% | 425.9s | 345.0s | -80.9s | No (discarded) | 0 | 0 | 1.00 |
| 06 | 9f39107fd | 7 | 8375 | 8375 | 100.0% | 426.7s | 349.3s | -77.4s | Yes | 0 | 0 | 1.00 |
| 07 | 05210b98e | 54 | 8375 | 8375 | 100.0% | 408.9s | 331.4s | -77.6s | Yes | 0 | 0 | 1.00 |
| 08 | 6808e3a74 | 3 | 8375 | 8375 | 100.0% | 389.6s | 347.8s | -41.8s | Yes | 0 | 0 | 1.00 |
| 09 | e80098654 | 3 | 8379 | 8379 | 100.0% | 397.6s | 341.0s | -56.7s | Yes | 0 | 0 | 1.00 |
| 10 | 3ae697cff | 6 | 8379 | 8379 | 100.0% | 406.5s | 340.9s | -65.7s | Yes | 0 | 0 | 1.00 |
| 11 | b256e4611 | 5 | 8386 | 8386 | 100.0% | 406.4s | 344.9s | -61.5s | Yes | 0 | 0 | 1.00 |
| 12 | e64b89955 | 11 | 8397 | 8397 | 100.0% | 425.1s | 346.7s | -78.4s | Yes | 0 | 0 | 1.00 |
| 13 | 3a8d2b200 | 1 | 8397 | 8397 | 100.0% | 408.2s | 338.9s | -69.3s | Yes | 0 | 0 | 1.00 |
| 14 | 3eaf8b895 | 8 | 8405 | 8405 | 100.0% | 401.2s | 341.1s | -60.1s | Yes | 0 | 0 | 1.00 |
| 15 | 8d5bbe95b | 12 | 8413 | 8413 | 100.0% | 406.4s | 341.6s | -64.8s | Yes | 0 | 0 | 1.00 |
| 16 | 11e030ea9 | 5 | 8419 | 8419 | 100.0% | 404.3s | 342.9s | -61.3s | Yes | 0 | 0 | 1.00 |
| 17 | 7ae3ad0ba | 2 | 8419 | 8419 | 100.0% | 404.8s | 351.2s | -53.6s | Yes | 0 | 0 | 1.00 |
| 18 | a26ef9b0c | 10 | 8428 | 8428 | 100.0% | 419.6s | 343.0s | -76.7s | Yes | 0 | 0 | 1.00 |
| 19 | 0c323ea3b | 18 | 8437 | 8437 | 100.0% | 429.6s | 347.1s | -82.5s | Yes | 0 | 0 | 1.00 |
| 20 | eccbe3f05 | 2 | 8437 | 8437 | 100.0% | 420.7s | 350.8s | -69.9s | Yes | 0 | 0 | 1.00 |
| Control | eccbe3f05 | 1 (term.py) | 8437 | 8437 | 100.0% | 417.4s | N/A | N/A | Yes | 186 | N/A | 1.00 |

## Analysis of Key Metrics

1. **Selection Fraction**:
   - Median selected fraction: **100.0%**
   - 90th percentile (P90) selected fraction: **100.0%**
   - Threshold requirement: `<= 0.5` (**FAILED**)
   - Explanation: In this codebase, the transitive dependency closure is dense. Central modules like `runner_shared.py`, `cli.py`, `attention.py`, and `suite_cache.py`, as well as shared test infrastructure (`tests/support.py`), are imported either directly or transitively by practically all test suites. Even single-file edits to leaf files triggered full-suite reselection because test fixtures and CLI invocation helpers transitively touch those modules during collection and execution.

2. **Recall**:
   - Minimum recall: **1.00**
   - Threshold requirement: `== 1.0` (**PASSED**)
   - Steps with full-suite failures: **2** (Steps 02 and 03 each experienced 49 failing node IDs due to in-progress branch commits; in both steps, `pytest --testmon` selected and reproduced all 49 failures with zero misses).
   - Vacuity Note: Because 2 of the 20 steps carried genuine full-suite failures, criterion (ii) is non-vacuous. Furthermore, the control step verified failure selection. Nonetheless, structural blind spots of `pytest-testmon` remain present by design: testmon cannot detect changes reached through `subprocess` children (e.g., tests invoking `support.run_cli` as external processes) or data file modifications.

3. **Wall Time Impact**:
   - Median wall-time saving across 18 load-valid steps: **-68.81s**
   - Explanation: Rather than accelerating test execution, `pytest --testmon` was approximately 69 seconds **slower** than the bare full suite on median. Because testmon reselected virtually 100% of all tests at every step, the system paid the full cost of running all tests plus the substantial CPU overhead of coverage instrumentation tracing (`ctrace`).

4. **Control Step**:
   - At commit S20 (`eccbe3f05cd6596aedbaab13f7b07d6410418e8d`), a deliberate syntax/return breakage was injected into `strip_ansi` in `agent_workflows/term.py`.
   - `pytest --testmon` selected 8437 tests and failed with exit code 1, reporting 186 test failures including `tests/test_term.py` (e.g., `EveryTierKeepsTheInvariantTests::test_invariant_glyph_and_word_preserved_across_tiers`).
   - The breakage was cleanly reverted immediately after the test run.
   - Threshold requirement: control step selects and fails (**PASSED**).

## Decision

Decision: DECLINE

### Rationale

The adoption threshold mandates that all three criteria hold:
1. Median selected fraction <= 0.5: **FAILED** (measured: 100.0%).
2. Minimum recall == 1.0: **PASSED** (measured: 1.00 across all 20 steps).
3. Control step selected and failed: **PASSED** (186 failures detected).

Because criterion (i) failed decisively—coverage-based selection selected 100% of tests on every single commit and increased median runtime by 68.8 seconds due to tracing overhead—adopting `pytest-testmon` for agent iteration would penalize developer and agent turnaround times while adding dependency and maintenance overhead. Test selection does not pay on this repository structure.
