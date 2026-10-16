# Review findings: plan 24h56i

- Subject-Id: 24h56i
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (MEDIUM, fixed), PR-002 (MEDIUM, fixed), PR-003 (LOW, fixed), PR-004 (LOW, fixed), PR-005 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a178320e9`. Plan committed and byte-identical to the lane
input (sha256 `0eb6d4a7...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`.
Not an orchestrator (`- Kind: child`).

Re-measured at HEAD: `git show 19313eed^:tests/test_benchmark_runners_reports.py` run from an untracked
copy under `.aw/state/` -> `14 passed in 0.18s`; the module imports no `inspect`/`ast`; `tests/test_benchmark_runners_reports.py`
is absent; `agent_workflows/benchmark_reports.py:270` calls `compute_aggregate_metrics` from
`generate_benchmark_report`; `.aw/.gitignore:65` `/state/`; the only surviving `benchmark_metrics` importer is
`tests/test_run_analytics_statistics.py`. `hpjj44` findings line 3838 matches F1. Demonstration of the
E-03 mechanism (control form, `--extra-test 19313eed:...`, same selection): `verdict: killed`,
`newly_failing_total: 4`, `checkout_status_changed: []`, `wall_s: 5.66`, checkout clean before and after.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | MEDIUM | IN-SCOPE | Rubric G (live-artifact / test-organization criteria) | plan E-01 Expected outcome "14 tests pass"; V-01 "listing all 14 tests PASSED"; V-03 "`14 tests collected`" | A collected test count is an artifact of test organization and may not be a V-item bar. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01/V-01 now demand every collected test passing with zero failures/errors; V-03 demands collected count > 0 and equal to V-01's passed count (which still guards the `rq3q7v` F-03 empty-selection hazard); 14 kept as context. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (verdict mapping completeness) | `tools/mutation_probe.py:615` `verdict = "killed-by-import"`; plan E-03 mapping omitted it; `rq3q7v` Scope `import-only` rule | E-03's mapping had no branch for `killed-by-import`, and no rule for what a final `unprovable` means for V-03. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Added the `rq3q7v` rerun-once-with-`--op raise` branch; Expected outcome now accepts any measured verdict faithfully recorded and states a final `unprovable` leaves V-03 `failed`. |
| PR-003 | LOW | IN-SCOPE | Rubric G (executability) | plan E-03 "Write its JSON to `.aw/state/trimcarry-24h56i/prop02.json`" | No command created the directory or redirected output; and nothing proved the survivor run used the committed module rather than an `--extra-test` overlay. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | Command now `mkdir -p` and redirects; explicitly no `--extra-test`; V-03 demands `selection` and `extra_tests_overwrote: []` from the JSON. |
| PR-004 | LOW | IN-SCOPE | Rubric E (evidence) | `hpjj44` findings line 3838 names 3 of 4 control kills; plan E-03 asserted all four as the control's | Plan's claim that four named tests were "the ones the control killed" was not fully supported by the cited row. | all Low | FIXED | Added F5 with the review demonstration naming all four; names demoted to non-binding pointers. |
| PR-005 | LOW | UNDER-SCOPE | Rubric D (guard against concurrent recreation) | plan E-01 overwrites via `>` | Restore by redirect would silently clobber a module recreated by another change. | all Low | FIXED | E-01 pre-checks `git ls-files` and stops (an unsafe condition, not a scope question); V-01 demands the pre-check output. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How to handle `killed-by-import`? | Rerun once with `--op raise`, else `unprovable`. | Treat as `guarded` (REJECTED: contradicts `rq3q7v` `import-only` rule). | `rq3q7v` Scope; `tools/mutation_probe.py:615`. | yes |
| D-2 | Keep `testpaths` exclusion as a non-goal? | Keep. | Add to `testpaths` (REJECTED: routine-gate composition is a maintainer decision). | plan Deferred section; `pyproject.toml` testpaths policy. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
