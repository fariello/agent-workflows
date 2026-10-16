# Review findings: plan hguae9

- Subject-Id: hguae9
- Subject-Type: ipd
- Reviewed-At: 2026-10-16
- Reviewer: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Verdict: APPROVE WITH REVISIONS APPLIED
- Findings: PR-001 (HIGH, fixed), PR-002 (MEDIUM, fixed), PR-003 (MEDIUM, fixed), PR-004 (MEDIUM, fixed), PR-005 (MEDIUM, fixed), PR-006 (MEDIUM, fixed), PR-007 (MEDIUM, fixed), PR-008 (MEDIUM, fixed), PR-009 (LOW, fixed), PR-010 (LOW, fixed)

## Round 1

Reviewed in an isolated review lane at HEAD `a178320e9`. Plan committed (`6ea45c974`) and byte-identical to
the lane input, so no pre-review snapshot. `aw ipd lint --phase author --agent`: `clean`. Not an
orchestrator.

Probes run at review (scratch under the gitignored `.aw/state/`, removed afterwards):

- Selection: a temp project with `testpaths = ["tests"]`, addopts `-m 'not slow'`, and a
  `pytest_collection_modifyitems` hook gated on `config.args_source == pytest.Config.ArgsSource.TESTPATHS`.
  Bare run: 2 passed, 2 deselected (core only). `pytest tests/test_b.py`: 1 passed, 1 deselected (slow only).
  `pytest tests/`: 3 passed, 1 deselected. Same results under `-n 2`. Contrast: addopts
  `-m 'core and not slow'` with `tests/test_b.py` gave `2 deselected`, i.e. an explicit non-core file runs nothing.
- Collection cost (no-op `-k`, 3 samples): `tests/` 8.85s / 9.15s / 9.60s wall vs default 19 modules
  4.28s / 4.64s / 7.97s. Collect counts: `tests/` 9491 total, 9192 non-slow; default 712 (707 selected); slow 285.
- Leaf recording: `cli.main([...])` with a patched `cli.set_last_command` recorded `None` for `ipd lint --help`,
  `attention --format json`, `ipd board`, `suite -k x`; resolved names elsewhere are parser-level (`ipd`).
  A probe plugin wrapping `argparse.ArgumentParser.parse_known_args` (root `prog` `agent-workflows`) and
  `subprocess.Popen.__init__` (argv after `-m agent_workflows`) over `tests/test_status_set.py` and
  `tests/test_cli_search.py` (126 passed) recorded 11 declared leaves including `ipd set` (30 tests),
  `specs set`, `spec set`, `search`, `ipd lint`, `ipd scaffold`. `get_declared_leaves()` = 170; `oc run` is
  not a declared leaf (`oc runipd` is).
- Re-verified symbols: `suite_cache.SUITE_CHECK_ARGV`, `SUITE_REFUSAL_MESSAGE`, `check_narrowed_selection`,
  `run_full_suite(argv=..., timeout=SUITE_CHECK_TIMEOUT_SECONDS=900.0)`, `suite_key` component `argv`;
  `cli.py` `p_suite` and the `suite_targets`/`narrowed_k`/`narrowed_m` refusal branch;
  `oc_runipd` `--prepare-only`; `tests/deselect_notice.py` `pytest_deselected`;
  `tests/test_executed_transition_gate_e2e.py` `REGISTRATIONS` row pinning `default_install_hook_types`;
  `tests.yml` advisory slow step citing 57dwkc, 4vfkl1, 3ypquf, g0bdgg (all `done` per `aw find`).

### Findings

| ID | Severity | Scope | Area | Evidence | Finding | Remediation Risk | Decision | Resolution |
|----|----------|-------|------|----------|---------|------------------|----------|------------|
| PR-001 | HIGH | IN-SCOPE | Rubric D (anti-regression) | plan E-01 (pre-review) "change `addopts` to `-m 'core and not slow and not livecorpus'`"; review probe: explicit non-core file gave `2 deselected` | Putting `core` in addopts `-m` silently deselects every non-core test in `pytest tests/test_x.py`, the routine targeted-test workflow AGENTS.md prescribes ("Run the changed feature's test module explicitly"). Developers would see green on files whose tests never ran. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-01 keeps addopts as is and selects core in a `pytest_collection_modifyitems` hook gated on `args_source == TESTPATHS` (demonstrated), reported via `pytest_deselected`; OQ-03 and F-7 added. |
| PR-002 | MEDIUM | IN-SCOPE | Rubric G (executability) | plan E-02 (pre-review) "via `coverage` dynamic contexts on `cli.main` dispatch or a pytest plugin hook"; `cli.get_last_command` probe | Leaf-recording mechanism undecided; the obvious hook (`get_last_command`) records `None` or parser-level names, and subprocess-driven tests are invisible to in-process hooks. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-02 specifies the demonstrated `parse_known_args` + `Popen.__init__` probe plugin and longest-declared-prefix resolution; rejects `get_last_command`; OQ-04 added. |
| PR-003 | MEDIUM | IN-SCOPE | Rubric C (performance) | review timing: collection 9s (`tests/`) vs 4.5s (19 modules) | OQ-01 and F-2 assume 9s headroom; full-tree collection consumes about 5s of it, so the 55% target was sized on a wrong budget. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | F-8 added; OQ-01 revised to state real headroom and that module/leaf requirements outrank the percentage. |
| PR-004 | MEDIUM | IN-SCOPE | Rubric G (accuracy) | plan E-08 (pre-review) "make the required matrix job run `python -m pytest` (core)"; `tests.yml` "Run self-tests (parallel)" runs `tests/` | Switching the required job to core would REMOVE about 8500 non-slow tests from required CI on every OS and Python, a large coverage regression at the authority boundary; and the advisory slow step cites four backlog items that are all `done`. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-08 keeps the full-tree required step, adds a named bare core step, and re-derives the slow step's advisory status from a fresh `-m slow` run. |
| PR-005 | MEDIUM | UNDER-SCOPE | Rubric E (tests) | plan E-05/E-06 (pre-review) | No behavioral tests for the new selection hook, budget guard, or `aw suite --thorough`; only manual demonstrations. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-05 adds `tests/test_core_tier_selection.py` (subprocess, injected budget); E-06 adds `test_suite_cache.py` cases; V-05/V-06 demand their pass lines. |
| PR-006 | MEDIUM | UNDER-SCOPE | Rubric C (operability) | `suite_cache.SUITE_CHECK_TIMEOUT_SECONDS = 900.0`; research `7ry5kv` full wall 565s | Thorough mode would inherit a 900s timeout, which a 565s run plus one confirm re-run on a slower or busy host can exceed, turning the pre-push hook into a spurious failure. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 sets the thorough timeout to at least 1800s, core unchanged. |
| PR-007 | MEDIUM | UNDER-SCOPE | Rubric D (anti-regression) | `tests/test_executed_transition_gate_e2e.py` `REGISTRATIONS` pins `["pre-commit", "pre-merge-commit"]` | E-07's `default_install_hook_types` change would turn this test red with no step owning the update. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-07 updates the row and keeps its rationale true; V-07 demands it pass. |
| PR-008 | MEDIUM | UNDER-SCOPE | Rubric G (doc sync) | `docs/cli-human-guide.md` "Running the full test suite (`aw suite`)"; `cli.py` `_DESCRIPTIONS["suite"]` | User-facing `aw suite` docs and help were not in scope, so `--thorough` would ship undocumented. | C:Low; U:Low; S:Low; F:Low; Overall:Low | FIXED | E-06 updates both; path added to Scope-Paths. |
| PR-009 | LOW | IN-SCOPE | Rubric G (accuracy, live-artifact counts) | plan E-01/E-04/E-10 (pre-review) "still 8794", "168/168"; review: 9491 collected, 170 declared leaves | Authoring-time counts used as bars had already drifted; `aw oc run --prepare-only` names an alias, not a declared leaf; `coverage>=7` too low for `qqrgv3`'s `patch = subprocess` and missing from the `dev` group. | all Low | FIXED | Bars rewritten as properties re-derived at execution; smoke test names `oc runipd`; `coverage>=7.10` in both `test` and `dev`. |
| PR-010 | LOW | IN-SCOPE | Rubric G (execution contract) | plan gate (pre-review); Concern "Set `testprune`" | Gate lacked scope-fence wording, the paste-actual-output MUST, and conditional finalize ownership; Concern named the wrong Set for `wazeo5`; pre-push entry depended on an `aw` shim on PATH; stale-grep pattern would hit historical records. | all Low | FIXED | Gate rewritten; Concern corrected; entry `python3 -m agent_workflows suite --thorough`; grep excludes `.aw/records/`. |

`aw ipd lint --phase review-finalize --agent` after revisions: `clean` (one `info` advisory, IPD-Z602).

### Decisions

| ID | Question | Chosen | Alternatives considered | Basis | Reversible |
|----|----------|--------|-------------------------|-------|------------|
| D-1 | How does the default run select core? | `pytest_collection_modifyitems` gated on `args_source == TESTPATHS` and `AW_TEST_TIER != thorough`. | addopts `-m 'core and ...'` (REJECTED: breaks explicit-file runs, probe); separate `testpaths` list (REJECTED: what the plan replaces). | review probe at `a178320e9`; pytest 8.2.2 `Config.ArgsSource`. | yes |
| D-2 | How are driven leaves recorded? | Probe plugin wrapping `parse_known_args` and `Popen.__init__`, longest declared prefix. | `cli.get_last_command` (REJECTED: None / parser-level); coverage dynamic contexts (REJECTED: lines, not leaves). | review probe, 126 passed, 11 leaves. | yes |
| D-3 | What does required CI run? | Bare core step plus the existing full-tree non-slow step. | Core only (REJECTED: drops ~8500 tests from required CI). | `tests.yml` "Run self-tests (parallel)". | yes |
| D-4 | Thorough timeout? | At least 1800s; core keeps 900s. | Inherit 900s (REJECTED: 565s + confirm re-run headroom). | `SUITE_CHECK_TIMEOUT_SECONDS`; research `7ry5kv`. | yes |

No decision is `Reversible: no`. No finding was left `OPEN` or `DEFERRED`.
