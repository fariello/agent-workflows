# IPD: Split the suite into a marker-selected core tier under 30s and a thorough pre-push and pre-release tier

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `wazeo5` (Set `testtier`; the pruning follow-up is prompt `4ul37x`, Set `testprune`). Measured 2026-10-16 at main `eca2e2211` (research `7ry5kv`): the default `python3 -m pytest` runs 695 tests from 19 hand-picked `testpaths` modules in a median 20.9s on 6 workers, but covers only 28% of `agent_workflows/` lines (29309/93730) against 75% for the full suite (72507/93730), and reaches ZERO lines in 93 of 196 modules. That default is also every runner lane's merge gate (`suite_cache.SUITE_CHECK_ARGV` = bare `python3 -m pytest`), so regressions in about half the codebase reach `main` unseen. The full suite (`make test-all`) was 8794 tests, 565s at that commit, and nothing runs it before a push. The maintainer asked for a core default under 30s on 6 CPUs that broadly detects regressions, and a thorough tier run at most on push and at minimum before release.
- Scope: Replace the `testpaths` file list with an explicit `core` marker that selects the default run across `tests/` ONLY when pytest falls back to `testpaths` (an explicit path or node id runs every non-slow test it names, exactly as today); choose core membership by measured coverage (every module and every declared `aw` leaf command executed by at least one core test, plus a few end-to-end smoke tests); add a wall-time budget guard; give `aw suite` a thorough mode; add a `pre-push` pre-commit stage running it; make CI's required job run core plus thorough; align `AGENTS.md` (repo-local section only), `CONTRIBUTING.md`, `RELEASING.md`, `Makefile`, `docs/row-level-test-evidence.md`, `docs/cli-human-guide.md` and release-review Section 8 on the same two commands. Deletes and skips NO test (pruning is prompt `4ul37x`, Set `testprune`).
- Scope-Paths: pyproject.toml, conftest.py, Makefile, .pre-commit-config.yaml, .github/workflows/tests.yml, agent_workflows/suite_cache.py, agent_workflows/cli.py, tests/, AGENTS.md, CONTRIBUTING.md, RELEASING.md, docs/row-level-test-evidence.md, docs/cli-human-guide.md, .aw/system/workflows/release-review/08-final-ship-review.md, .aw/records/research/20261016-testtier-01-7ry5kv-test-tier-baseline.assessment.md, CHANGELOG.md
- Item-Dependencies: none
- Status: reviewed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: high
- Set: testtier
- Order: 1
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hguae9

## Workflow history
- 2026-10-16 reviewed (aw set): status set to reviewed
- 2026-10-16 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005, PR-006, PR-007, PR-008, PR-009, PR-010
- 2026-10-16 to-review (aw set): authored from prompt wazeo5 with baseline research 7ry5kv at main eca2e2211

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bare `pytest` (no path arguments) runs a `core` tier in under 30s (warm median, 6 workers) that executes every first-party module the full suite covers and every declared `aw` leaf command; an explicit `pytest <path>` keeps running every non-slow test it names; and one explicit command runs every retained test before push and before release.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: selection mechanism

- [ ] E-01 Register a `core` marker in `pyproject.toml` (description: "fast behavioral regression test run by a bare `pytest`; author-assigned; see CONTRIBUTING"), replace the `testpaths` module list with `testpaths = ["tests"]`, and LEAVE `addopts` as `-q -n auto --dist=worksteal -m 'not slow and not livecorpus'` (no `core` term in `-m`). Selection lives in a `pytest_collection_modifyitems` hook in the root `conftest.py` that, only when `config.args_source == pytest.Config.ArgsSource.TESTPATHS` (pytest >= 7.2; this repo requires pytest >= 8) and env `AW_TEST_TIER` is not `thorough`, keeps items carrying the `core` marker and reports the rest through `config.hook.pytest_deselected(items=...)` so `tests/deselect_notice.py` counts them. Extend the deselect NOTE text (in `tests/deselect_notice.py`) to name the core filter when it applied. In the same commit mark the 19 current `testpaths` modules `pytestmark = pytest.mark.core` (module level; where a module already sets `pytestmark`, append to it as a list), so the default selection is unchanged at this step.
  - Depends on: none
  - Expected outcome: the sorted node-id list from bare `python3 -m pytest --collect-only -q -p no:randomly` is identical before and after (empty `diff`); `python3 -m pytest tests/test_backlog.py --collect-only -q` (an explicit path) still collects every non-slow test in that file; `python3 -m pytest tests/ -m '' --collect-only -q -o addopts=""` collects the same count before and after (re-derived at execution; 9491 at review HEAD `a178320e9`, the count drifts as tests land); `tests/test_deselect_notice.py` still passes.
  - Execution state: pending

### Task group 2: coverage-driven membership

- [ ] E-02 Write measurement tooling under `tests/tools/` (create `tests/tools/__init__.py`; module names carry no `test_` prefix so `tests/test_uncollected_test_modules.py::is_pytest_test_filename` does not flag them): `tests/tools/core_measure.py` (`python3 -m tests.tools.core_measure --out DIR`) runs core (bare) and thorough (`tests/ -m ''`) under `coverage run` with branch coverage and prints a per-module table (statements, core %, thorough %); and a pytest plugin `tests/tools/leaf_probe.py` (loaded only via `-p tests.tools.leaf_probe`) that records, per test node id from `PYTEST_CURRENT_TEST`, the declared leaf driven by (a) in-process dispatch, by wrapping `argparse.ArgumentParser.parse_known_args` for the root parser whose `prog` is `agent-workflows` (`cli._build_parser`), and (b) subprocess dispatch, by wrapping `subprocess.Popen.__init__` and reading argv after `-m agent_workflows`. A leaf is the longest positional prefix that is a member of `command_surface.get_declared_leaves()` (170 at review HEAD). Do NOT key on `cli.get_last_command()`: it records the parser-level name (`ipd`, not `ipd lint`) and is not published for `--help` exits. Add `coverage>=7.10` to both the `test` extra and the PEP 735 `dev` group (the two are kept in sync; plan `qqrgv3` E-02 needs the same floor for `patch = subprocess` and is conditioned on this addition). Document both commands in `CONTRIBUTING.md`.
  - Depends on: E-01
  - Expected outcome: `core_measure` prints the module table with totals; `leaf_probe` prints a driven/declared leaf map; both are documented in `CONTRIBUTING.md`.
  - Execution state: pending
- [ ] E-03 Grow core to cover every module: for each first-party module with at least one full-suite-covered line and zero core coverage (74 of 93 zero-coverage modules at research `7ry5kv`; re-derive with E-02), mark the cheapest existing non-slow, non-livecorpus behavioral test that executes it as `core` (per-test `@pytest.mark.core`, per-class decorator, or module `pytestmark`; marks work on `unittest.TestCase` methods), preferring tests under 0.5s by `--durations`; write a new small behavioral test only where none exists. Repeat the E-02 measurement until no such module has zero core coverage.
  - Depends on: E-02
  - Expected outcome: zero modules at 0% core coverage among modules the full suite covers; core line and branch coverage reported, target at least 55% lines (rationale in OQ-01).
  - Execution state: pending
- [ ] E-04 Cover every declared leaf: for each declared leaf with no core test driving it (per E-02 `leaf_probe`), mark (or add) one fast in-process test (`cli.main([...])`) asserting exit code and one output property. Keep a smoke set marked `core` of at most 6 end-to-end subprocess tests: one install into a temp repo, one `aw oc runipd ... --prepare-only` (the declared leaf is `oc runipd`; `oc run` is its alias), one `aw ipd lint`, one `aw check`, one `aw.agent/v1` conformance record, one `aw attention`. A test marked `slow` or `livecorpus` never also counts as core (the addopts `-m` still deselects it); prefer a non-slow test or add one.
  - Depends on: E-03
  - Expected outcome: `leaf_probe` over the core tier shows every declared leaf driven (count re-derived at execution); smoke set listed by node id.
  - Execution state: pending

### Task group 3: budget, thorough command, hooks, CI

- [ ] E-05 Add a budget guard in the root `conftest.py` (`pytest_sessionfinish` on the xdist controller only, i.e. `PYTEST_XDIST_WORKER` unset): when the core filter from E-01 applied, measure session wall time from `pytest_sessionstart`; compare to a budget of 30s; FAIL (set `session.exitstatus` nonzero) only when `os.cpu_count() >= 12` (so 6 workers) and env `AW_CORE_BUDGET_ENFORCE` is not `0`, else print a warning; always print the 10 slowest core tests when over budget. Document the budget, the margin, and the `AW_CORE_BUDGET_ENFORCE=0` escape in `pyproject.toml` comments beside the marker. Add behavioral tests in a new `tests/test_core_tier_selection.py` (marked `core`) that run pytest in a subprocess on a temp project with a copy of the hook and assert: bare run selects only core; explicit path runs non-core; `AW_TEST_TIER=thorough` runs all; over-budget with enforce exits nonzero and prints the slowest list; enforce `0` warns and exits 0 (budget injected through an env override such as `AW_CORE_BUDGET_SECONDS` so no test sleeps 30s).
  - Depends on: E-04
  - Expected outcome: the new tests pass; on this 12-CPU host a temporary `time.sleep(40)` in one core test makes the bare run fail with the budget message and the slowest-tests list; reverting restores pass; with fewer than 12 CPUs it only warns.
  - Execution state: pending
- [ ] E-06 Make the thorough tier one command. `make test-all` stays `python3 -m pytest tests/ -m ''` (an explicit path, so the core filter does not apply). Add `aw suite --thorough` in `agent_workflows/cli.py` (`p_suite`) and `agent_workflows/suite_cache.py`: a module constant `SUITE_THOROUGH_ARGV = (sys.executable or "python3", "-m", "pytest", "tests/", "-m", "")` passed to `run_full_suite(argv=...)`; the existing narrowed-selection refusal (`cli.py` `suite_targets`/`narrowed_k`/`narrowed_m` branch and `suite_cache.check_narrowed_selection`) stays unchanged for user-supplied tokens and is not applied to this internally built argv; the cache key already digests the argv (`suite_key` component `argv`), so core and thorough records never collide. Give the thorough mode a timeout of at least 1800s (the 900s `SUITE_CHECK_TIMEOUT_SECONDS` default is below the measured 565s thorough wall plus confirm re-run headroom; keep 900s for core). Update `_DESCRIPTIONS["suite"]` and `--help` to name the mode, and the `aw suite` section of `docs/cli-human-guide.md`. `aw suite` with no flag stays the core tier and the runner merge gate (`SUITE_CHECK_ARGV`) is unchanged. Add behavioral tests in `tests/test_suite_cache.py` that drive `aw suite --thorough --explain` and assert the argv component differs from plain `aw suite --explain`, and that `--thorough -k x` still exits 2 with `SUITE_REFUSAL_MESSAGE`.
  - Depends on: E-01
  - Expected outcome: `aw suite --thorough` twice on an unchanged tree: second run is a cache hit; `aw suite` unchanged; `--explain` shows different argv digests for the two modes.
  - Execution state: pending
- [ ] E-07 Add a local `pre-push` hook to `.pre-commit-config.yaml` (`stages: [pre-push]`, `always_run: true`, `pass_filenames: false`, `language: system`, entry `python3 -m agent_workflows suite --thorough` so it does not depend on an `aw` shim on PATH, `verbose: true`) and add `pre-push` to `default_install_hook_types`. Update the row in `tests/test_executed_transition_gate_e2e.py` that pins `default_install_hook_types` to `["pre-commit", "pre-merge-commit"]` to the new list and keep its rationale true. Document in `CONTRIBUTING.md` that it is local feedback, skippable with `--no-verify`, not an authority boundary, and that an existing clone must re-run `pre-commit install` to gain it.
  - Depends on: E-06
  - Expected outcome: `pre-commit install --hook-type pre-push` installs it; `pre-commit run --hook-stage pre-push --all-files` runs the thorough tier (cache hit on second call); a failing test makes it exit nonzero; the updated e2e row passes.
  - Execution state: pending
- [ ] E-08 In `.github/workflows/tests.yml`, keep the required `unittest` matrix job's "Run self-tests (parallel)" step running the whole tree (`python -m pytest tests/ -n auto -rfEs`, an explicit path, so the non-slow thorough set stays required on every OS and Python) and add before it a named step "Run core tier" running bare `python -m pytest -rfEs`, so the merge gate selection is itself exercised in CI. Replace the advisory slow step's backlog list (57dwkc, 4vfkl1, 3ypquf, g0bdgg, all now `done`) with the current state: run `python -m pytest tests/ -n auto -m slow` on the ubuntu leg; if it reports 0 failed at execution, drop `continue-on-error`, else keep it and list the currently failing tests' owning backlog items. Correct every comment that no longer matches the YAML.
  - Depends on: E-04
  - Expected outcome: YAML diff shows the core step and the corrected slow step; `python3 -c "import yaml;yaml.safe_load(open('.github/workflows/tests.yml'))"` passes; the local `-m slow` run result that decided `continue-on-error` is recorded.
  - Execution state: pending

### Task group 4: documentation and proof

- [ ] E-09 Update the repo-local "HOW TO RUN THE SUITE" paragraph in `AGENTS.md` (below the `<!-- /aw:block -->` marker only), the `[tool.pytest.ini_options]` comments in `pyproject.toml`, `CONTRIBUTING.md`, `RELEASING.md`, `Makefile` comments, `docs/row-level-test-evidence.md`, and release-review `08-final-ship-review.md` so all name `python3 -m pytest` (core, runner merge gate; an explicit path runs everything non-slow it names) and `make test-all` / `aw suite --thorough` (thorough: pre-push, CI, release); finalize research `7ry5kv` with the after-measurements (append a dated "After" section; keep the baseline numbers); add a CHANGELOG line (no em/en dashes in user-facing docs).
  - Depends on: E-05, E-07, E-08
  - Expected outcome: `git grep -n -e "testpaths selects" -e "19 hand-picked" -e "representative behavioral modules" -e "representative behavioral tests" -- ':!.aw/records/'` finds no stale description (historical records are excluded because they are not edited).
  - Execution state: pending
- [ ] E-10 Prove the result: three warm bare core runs; one thorough run; before/after `tests/ -m '' --collect-only` count equality (unless pruning landed first, then explain the delta); three consecutive core runs with `pytest-randomly` active (default) and no failure; a one-line mutation in a module only core-covered since E-03 fails the bare core run; a mutation in a thorough-only path (one no core test executes, per E-02) fails `pre-commit run --hook-stage pre-push --all-files`; both reverted with an empty `git diff`.
  - Depends on: E-09
  - Expected outcome: all evidence pasted in V-10.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `suite_cache.SUITE_CHECK_ARGV` (bare `python3 -m pytest`) is what the runners revalidate lanes with (`runner_shared` merge gate; spec `25kzda` note 2026-10-14), so the core tier IS the merge gate; keeping it fast is a throughput requirement, keeping it broad is a correctness one. The gate argv is unchanged, so spec `25kzda` text needs no amendment.
- `conftest.pytest_xdist_auto_num_workers` caps workers at min(6, cpus/2); this host (12 CPUs) resolves to 6.
- Markers `slow` (285 at review HEAD) and `livecorpus` exist with recorded reasons; `livecorpus` must stay out of the merge gate (pyproject marker text).
- `tests/deselect_notice.py` (registered in root `conftest.pytest_plugins`) prints the deselected-count NOTE from `pytest_deselected`, so a hook-based filter must report through that hook.
- Local hooks are best-effort feedback, not authority (AGENTS.md "Before you publish to main").
- P16: tests exercise behavior; membership changes here move tests between tiers, never weaken them.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Default covers 28% of lines; 93/196 modules at zero (74 of them covered by the full suite) | research `7ry5kv` coverage table |
| F-2 | Default median 20.9s, so about 9s of budget remains for broadening | research `7ry5kv` wall times |
| F-3 | Full suite 565s; two `doctor` live-leaf conformance tests take 118s and 64s | `--durations=30` in research `7ry5kv` |
| F-4 | No pre-push stage; `default_install_hook_types: [pre-commit, pre-merge-commit]`, pinned by a test row | `.pre-commit-config.yaml`; `tests/test_executed_transition_gate_e2e.py` `REGISTRATIONS` |
| F-5 | CI required job already runs the whole `tests/` tree, not the default | `tests.yml` "Run self-tests (parallel)" step |
| F-6 | `aw suite` refuses any narrowed selection from the user, so a thorough mode needs an explicit flag | `cli.py` `suite_targets`/`narrowed_k`/`narrowed_m` branch; `suite_cache.SUITE_REFUSAL_MESSAGE` |
| F-7 | A `-m 'core and ...'` addopts would deselect every non-core test in an explicit `pytest tests/test_x.py` run; an `args_source == TESTPATHS` hook keeps explicit runs whole (demonstrated at review, also under `-n 2`) | review probe, see review record `hguae9` Round 1 |
| F-8 | Collecting all of `tests/` costs about 9s wall vs about 4.5s for the 19 modules (no-op `-k` run, 3 samples), so roughly 5s of the 9s headroom goes to collection | review measurement at `a178320e9` |

## Proposed changes (ordered, validatable)

E-01 (mechanism, zero selection change) -> E-02..E-04 (measured broadening) -> E-05..E-08 (guard, thorough command, hook, CI) -> E-09..E-10 (docs, proof).

## Deferred / out of scope (with reason)

- Deleting, merging or speeding up tests: owned by prompt `4ul37x` (Set `testprune`), which runs after this plan.
  - Carrier-Declined: tracked by the `testprune` Set (orchestrator `8wfzb5`, children `qqrgv3`, `tv72xy`, `83nnyn`, `c8bfp9`, `vgus66`, all pending with `executed:hguae9` dependency).

## Scope check

- Over-scope: none.
- Under-scope: none after review (PR-005, PR-006, PR-008 added the missing tests, doc and timeout).

## Required tests / validation

Per V-items; bare `python3 -m pytest`, `python3 -m pytest tests/test_core_tier_selection.py tests/test_suite_cache.py tests/test_deselect_notice.py tests/test_executed_transition_gate_e2e.py tests/test_uncollected_test_modules.py -o addopts="-n auto -m ''"`, and `make test-all` at the end, pasted.

## Spec / documentation sync

No spec governs test tier selection. Spec `25kzda` names the runner merge gate as the full suite through `aw suite`; `SUITE_CHECK_ARGV` is unchanged, so its contract is unchanged. Documentation updated in E-06 (`docs/cli-human-guide.md`) and E-09.

## Open questions

### OQ-01: What core coverage target is right?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-16: the hard requirement is every module and every leaf executed by core (E-03/E-04); the numeric line-coverage target is at least 55% (about three quarters of the full suite's 75%). Review re-measured that collecting all of `tests/` costs about 5s more than the 19 modules (F-8), so the real headroom is about 4s, not 9s. If 30s is reached first, E-03 records the achieved number and the uncovered modules rather than exceeding the budget; the module and leaf requirements still take precedence over the percentage.

### OQ-02: Should the pre-push hook be installed by default?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the maintainer's request ("run the more extended regression tests at most when pushing"): yes, add `pre-push` to `default_install_hook_types`, so `pre-commit install` installs it; it remains skippable with `--no-verify` and cache-backed so an unchanged tree costs nothing.

### OQ-03: How does the default select core without breaking explicit runs?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved by demonstration at review (record `hguae9` Round 1, D-1): a `pytest_collection_modifyitems` hook gated on `config.args_source == pytest.Config.ArgsSource.TESTPATHS` (pytest 8.2.2 here) selected 2 of 4 items on a bare run, ran all non-slow items for `pytest tests/test_b.py` and `pytest tests/`, and behaved identically under `-n 2`; the addopts alternative deselected both tests of an explicit non-core file.

### OQ-04: How are driven leaves recorded?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved by demonstration at review (record `hguae9` Round 1, D-2): a probe plugin wrapping `argparse.ArgumentParser.parse_known_args` and `subprocess.Popen.__init__`, resolving the longest positional prefix in `get_declared_leaves()`, recorded 11 leaves (`ipd set`, `specs set`, `search`, ...) over `tests/test_status_set.py` and `tests/test_cli_search.py` (126 passed); `cli.get_last_command()` was shown to record `None` or the parser-level name and is rejected.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `diff` of sorted bare-run node ids before and after (empty), the explicit-path collect line for one non-core file showing all its non-slow tests, the `tests/ -m ''` collect counts before and after (equal), and the `tests/test_deselect_notice.py` pass line.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted `core_measure` output header (module table excerpt and totals) and `leaf_probe` driven/declared totals (code path: `tests/tools/leaf_probe.py` from E-02), plus the `pyproject.toml` diff showing `coverage>=7.10` in both `test` and `dev`.
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted per-module table showing zero modules at 0% core among full-covered modules, and core total line and branch coverage.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted `leaf_probe` totals (driven equals declared, both re-derived at execution) and the smoke-test node ids.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted `tests/test_core_tier_selection.py` pass line; pasted failing bare run with the temporary sleep (budget message plus slowest list; code path: the E-05 `pytest_sessionfinish` hook); pasted passing run after revert; empty `git diff` of the temporary change.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted two `aw suite --thorough` runs (second a cache hit; code path: `suite_cache.run_full_suite` with `SUITE_THOROUGH_ARGV` from E-06), `aw suite --explain` and `aw suite --thorough --explain` showing different argv digests, and the new `tests/test_suite_cache.py` cases passing.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `pre-commit run --hook-stage pre-push --all-files` (pass, then cache hit) and a failing case's nonzero exit (code path: the pre-push hook entry `python3 -m agent_workflows suite --thorough` from E-07), plus the updated `test_executed_transition_gate_e2e.py` row passing.
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: the YAML diff, the `yaml.safe_load` check output, and the pasted local `-m slow` summary line that decided `continue-on-error`.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted stale-description `git grep` returning nothing, the CHANGELOG line, the AGENTS.md diff confined to below `<!-- /aw:block -->`, and the updated research "After" summary.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: three warm bare core wall times (median under 30s) with test count, thorough wall time and count, collect-count equality, three randomized core runs, both mutation demonstrations with reverts (code paths: bare `pytest` core selection from E-01, and the pre-push hook from E-07), and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval (all open questions are resolved), in an isolated worktree (`aw work begin hguae9`, or the runner's lane). Scope fence: `- Scope-Paths:` is a declaration; an edit outside it is allowed when needed and must be justified at finalize (`--scope-reason`), and a declared path left unmodified is acknowledged (`--scope-ack`). `tests/` is declared because E-03/E-04 add `core` markers across many test modules; no test is deleted or skipped. You MUST paste the ACTUAL runner output in each V-item; never claim a pass you did not run. Commit via `aw commit hguae9 -- <paths>` only (never `git add -A`); never push or tag. Lifecycle: when run under `aw oc run` / `aw agy run`, the runner owns finalize and the move to `executed/`; when executed by hand, finish with `aw ipd lint --phase pre-transition` conforming and then `aw ipd finalize hguae9`, never a hand `git mv`; publish a hand run with `aw integration-lock -- git merge --ff-only <branch>`.
