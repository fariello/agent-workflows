# Review findings: plan c8bfp9

- Subject-Id: c8bfp9
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (HIGH, fixed), PR-003 (HIGH, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (MEDIUM, fixed), PR-010 (LOW, fixed), PR-011 (LOW, fixed), PR-012 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `8f1a94c58`. Plan committed and byte-identical to the lane input
(sha256 `d82cbb61...`), so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an
orchestrator (`- Kind: child`). Dependencies `83nnyn`, `qqrgv3` are `reviewed` and pending; `hguae9` is `reviewed`.

Verified anchors: `tests/conformance_matrix.py` `run_cli` (default cwd `REPO_ROOT`), `run_cli_tty`, `_pinned_env`,
`LIVE_SAFE_LEAVES`, `LIVE_HEAVY_LEAVES` (doctor, attention, status) and its measurement comment, `RUNNABLE_ARGV`
(`show f36de0`, `graduation 25kzda`, `workflow validate tests/fixtures/...`), `live_leaf_argv`,
`build_installed_project_template`, `clone_isolated_project`; `tests/test_exit_contract_conformance.py`
`test_live_safe_leaves_exit_contract_membership_heavy` (`slow`, `timeout(500)`) and its subset test;
`tests/test_live_conformance_sweep.py` `test_no_color_scenario_is_plain_heavy_leaves`; `scoped_repo_dir` with
`leaf in ("doctor", "check")` in both modules; `tests/test_typecheck_gate.py` (`mypy agent_workflows`);
`suite_cache.prune_expired_records(now=)`, `host_capability_registry` `is_expired(now=)`,
`run_viewer.parse_since_timestamp(now=)`; research `7ry5kv` "Slowest full-suite tests"; prompt `4ul37x`.

Measured at review (sandboxed `AW_HOME`/`XDG_CONFIG_HOME`, `AW_CONFIG_DIR` unset, scratch project under gitignored
`.aw/state/`, removed afterwards): `doctor` 61.5s at the repository vs 1.15s in a freshly installed project;
`partition -t plans -s approved --json` 3.4s vs 0.36s; `attention --check` 5.5s vs 1.7s; `status` 4.5s vs 0.46s.
With the lane's `AW_CONFIG_DIR` set, `status` walked 37 registered repos (5.8s even in the empty project).
cProfile of `doctor --agent` at the repository: `doctor.probe_artifacts` 87.5s of 99.0s, `check_engine.check_ipd_dependencies`
50.7s via `review_findings.subject_gating_blocks`. Five `RUNNABLE_ARGV` leaves went `clean 0` -> `cannot-run 2`
in the unseeded project. `rg -c 'time\.sleep\('`: 57 in 24 files. No `.mypy_cache/` and none gitignored.

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | D (silent coverage loss) | review probe: `show f36de0`, `graduation 25kzda`, `reviews decisions f36de0`, `record-history f36de0`, `workflow validate tests/fixtures/...` `clean 0` -> `cannot-run 2` | Moving sweeps to a seeded project would silently turn several leaves' success paths into refusals that still satisfy exit-contract membership, so the sweep would stop exercising them. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 seeds every id6 and path `RUNNABLE_ARGV` names and requires a per-leaf `(exit, outcome)` table with zero class changes; V-02 demands it; F-8 added. |
| PR-002 | HIGH | IN-SCOPE | C (in-process helper feasibility) | E-04 (pre-review) "`monkeypatch.chdir`"; 430/557 TestCase modules; `make test-serial` | The helper relied on `monkeypatch`, unusable in TestCase modules and under unittest, and did not reproduce `_pinned_env`, so conversions could change output. | all Low | FIXED | E-04 specifies save/restore of cwd and `os.environ` with `_pinned_env` parity and parity tests against `run_cli`; a differing conversion stays subprocess. |
| PR-003 | HIGH | IN-SCOPE | E (coverage proof) | E-10 (pre-review) "union line and branch coverage equal to or above"; no tool named | No tool or baseline for the coverage claim; `qqrgv3` tooling exists for exactly this. | all Low | FIXED | E-01 records a `percov_run` baseline; E-10 uses `percov_analyze --compare` (zero lost) and `core_measure`. |
| PR-004 | MEDIUM | IN-SCOPE | E (measurement validity) | F-7: `cli._repos_for_report`; lane `AW_CONFIG_DIR`; conftest pops it | Timings taken in an agent lane include every registered repo for `status`, misattributing cost. | all Low | FIXED | Gate, E-01, E-03 and validation require `AW_CONFIG_DIR` unset; F-7 added. |
| PR-005 | MEDIUM | UNDER-SCOPE | G (right-sizing) | E-04 (pre-review) bundled helper creation with converting ~85 modules | Two deliverables and test surfaces; conversion is the largest item in the Set. | all Low | FIXED | Split into E-04 (helper + tests) and E-11 (conversion in module groups); V-11 added; E-05/E-06 depend on E-11. |
| PR-006 | MEDIUM | IN-SCOPE | D (premise) | F-9 cProfile: records walk dominates `doctor` | E-05 assumed host probes drive `doctor`/`checkup` cost. | all Low | FIXED | E-05 is measure-first with revert rule and a recorded spawn list; production speedup deferred with a filing note. |
| PR-007 | MEDIUM | IN-SCOPE | G (re-derivation convention) | E-02 "drop from 118s and 64s to a few seconds"; E-07 "57 call sites in 42 files" (review: 24 files); V-07 "57 rows" | Authoring counts and durations used as bars. | all Low | FIXED | Counts are context; bars re-derived at execution; review figures added. |
| PR-008 | MEDIUM | UNDER-SCOPE | E (new conftest hook untested) | E-09 (pre-review) relied on a temporary sleep | The slow-test report had no durable behavioral test and no controller-side duration source. | all Low | FIXED | E-09 names `pytest_runtest_logreport` collection on the controller, coexistence with hguae9's guard, and `tests/test_slow_report.py`. |
| PR-009 | MEDIUM | IN-SCOPE | D (shard correctness) | E-08 "shard union equals the full plan list, asserted" | Where and how the union is asserted was unspecified; split tests could drop assertions. | all Low | FIXED | E-08 specifies a run-time union-and-disjointness test kept `livecorpus`, every original assertion kept across parts. |
| PR-010 | LOW | IN-SCOPE | E (mypy cache) | F-10; E-08 "enable mypy's incremental cache" | mypy is already incremental; the cold cause is no persisted cache and no ignore rule. | all Low | FIXED | E-08 picks `--cache-dir` under `.aw/state` or a `.gitignore` entry; `.gitignore` declared in Scope-Paths. |
| PR-011 | LOW | IN-SCOPE | G (evidence, OQ owner) | Concern cites `/tmp/opencode/testtier-full.log`; OQ-02 `Owner: maintainer` with no recorded answer | Machine-local path cited as evidence; owner label overstated. | all Low | FIXED | Citation points at research `7ry5kv`; OQ-02 owner corrected to plan author with reason. |
| PR-012 | LOW | IN-SCOPE | G (execution contract) | gate (pre-review) | Missing scope-fence wording, no-production-change rule, conditional finalize ownership. | all Low | FIXED | Gate rewritten to the Set's contract. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean`.

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | Accept outcome changes when sweeps move to a seeded project? | No; seed until outcome classes match. | Accept refusals as still contract-conformant (REJECTED: drops success-path coverage silently). | F-8 probe. | yes |
| D-2 | Make `doctor` faster in production here? | No; defer, executor may file a backlog item. | Optimize `review_findings.subject_gating_blocks` (REJECTED: production change in a test-only Set). | F-9; Set scope `4ul37x`. | yes |
| D-3 | OQ-02 owner | Plan author. | Keep `maintainer` (REJECTED: no recorded answer; plan-review 3.1 owner rule). | OQ-02 text. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
