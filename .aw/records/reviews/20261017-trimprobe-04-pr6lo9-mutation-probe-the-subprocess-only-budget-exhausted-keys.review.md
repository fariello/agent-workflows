# Review findings: plan pr6lo9

- Subject-Id: pr6lo9
- Subject-Type: ipd
- Reviewed-At: 2026-10-17
- Reviewer: opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `c2c1ab611`. Plan committed and byte-identical to the lane
input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`; after revisions
`--phase review-finalize`: `clean`. Not an orchestrator.

Verified at review:
- `b1mx2w` `## Rollup mutation results`: 25 `subprocess-only` `budget-exhausted` rows; operators 23
  `return-none`, 2 `raise` (`engine.py::_ensure_untracked_gitignore`,
  `runner_stop.py::install_stop_signal_handlers._sigint`) (F-01 correct).
- Hook modules live at `agent_workflows/hooks/`; `rg -l -w` per hook stem matches only
  `tests/test_core_module_coverage.py` at this HEAD (F-02 correct).
- `tools.mutation_probe.main` forwards everything after `--` to pytest; `pytest_timeout` is not
  installed (`f4pbs5` F-04).
- Full non-slow `tests/` collected 8,236 items at review, so "about 9,000" in Step 0 is a fair
  context figure and not a bar.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric A/G (wrong command) | plan E-02 step (3) "over `-n 6 -m ... tests/` with `--timeout 3600`"; `tools.mutation_probe.main` "post_sep" | The command's shape was not stated, and the natural reading (the Order 02/03 template with `--timeout` added to the pytest args) puts `--timeout` after `--`. Pytest rejects it, so every fallback would end `error` and the subprocess-only keys could never reach `unguarded`. | all Low | FIXED | E-02 step (3) gives the full command with `--timeout 3600` before `--` and the reason. V-02 demands one pasted fallback command line. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric A/E (false verdict) | plan E-01 "record the collected count"; `lictgf` F-04 | The preflight did not require exit 0, so a selection pytest partly rejected could produce a false narrowed `survived`. The consequence here is smaller, because a narrowed `survived` never maps to `unguarded` alone, but it wastes the control and fallback budget. | all Low | FIXED | E-01 applies the `lictgf` rule (exit 0 with at least 1 collected, logged to `preflight.tsv`); V-01, V-02 and Required tests check it. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric G (missing mapping) | plan E-02 step (1) handles only `killed` and `survived`; `rf1xxr` E-02 step 5 | The narrowed survivor's `killed-by-import`, `invalid`, `error` and `timeout` results had no mapping. | all Low | FIXED | Added the `rf1xxr` mapping: one operator retry on `killed-by-import`, otherwise `unprovable` with the reason. |
| PR-004 | LOW | IN-SCOPE | Rubric C (selection quality) | plan E-01 "`rg -l -w <stem> tests/`"; review F-04 | The text match also returns test-free support modules (`tests/conformance_matrix.py`, `tests/support.py`, `tests/fixtures/run_analytics/__init__.py`, `tests/tools/leaf_probe.py`). They add import time and no tests. | all Low | FIXED | Restricted the candidate search to `--glob 'test_*.py'` and recorded the measurement as F-04. |
| PR-005 | LOW | IN-SCOPE | Citation convention | plan Step 0 "`tools.replay_coverage_diff._function_coverage`" | The cited symbol does not exist; the function is `_collect_function_coverage`. | all Low | FIXED | Corrected the symbol and quoted the line. |

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Narrow the candidate text match to `test_*.py` files? | Yes, `--glob 'test_*.py'` | Keep all matches (support modules collect nothing) | Review measurement, plan F-04; pytest discovers only `test_*.py` under this repo's config | yes |
