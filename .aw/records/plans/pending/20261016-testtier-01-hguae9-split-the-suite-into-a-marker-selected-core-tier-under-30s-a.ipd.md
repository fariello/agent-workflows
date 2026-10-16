# IPD: Split the suite into a marker-selected core tier under 30s and a thorough pre-push and pre-release tier

- Date: 2026-10-16
- Kind: child
- Concern: Prompt `wazeo5` (Set `testprune`). Measured 2026-10-16 at main `eca2e2211` (research `7ry5kv`): the default `python3 -m pytest` runs 695 tests from 19 hand-picked `testpaths` modules in a median 20.9s on 6 workers, but covers only 28% of `agent_workflows/` lines (29309/93730) against 75% for the full suite (72507/93730), and reaches ZERO lines in 93 of 196 modules. That default is also every runner lane's merge gate (`suite_cache.SUITE_CHECK_ARGV` = bare `python3 -m pytest`), so regressions in about half the codebase reach `main` unseen. The full suite (`make test-all`) is 8794 tests, 565s, and nothing runs it before a push. The maintainer asked for a core default under 30s on 6 CPUs that broadly detects regressions, and a thorough tier run at most on push and at minimum before release.
- Scope: Replace the `testpaths` file list with an explicit `core` marker selected by default across `tests/`; choose core membership by measured coverage (every module and every declared `aw` leaf command executed by at least one core test, plus a few end-to-end smoke tests); add a wall-time budget guard; add a `pre-push` pre-commit stage running the thorough tier through the `aw suite` cache; give `aw suite` a thorough mode; split CI into a required core job and a thorough job; align `AGENTS.md` (repo-local section only), `CONTRIBUTING.md`, `RELEASING.md`, `Makefile`, `docs/row-level-test-evidence.md` and release-review Section 8 on the same two commands. Deletes and skips NO test (pruning is prompt `4ul37x`, Set `testprune`).
- Scope-Paths: pyproject.toml, conftest.py, Makefile, .pre-commit-config.yaml, .github/workflows/tests.yml, agent_workflows/suite_cache.py, agent_workflows/cli.py, tests/, AGENTS.md, CONTRIBUTING.md, RELEASING.md, docs/row-level-test-evidence.md, .aw/system/workflows/release-review/08-final-ship-review.md, .aw/records/research/20261016-testtier-01-7ry5kv-test-tier-baseline.assessment.md, CHANGELOG.md
- Item-Dependencies: none
- Status: to-review
- Work-Kind: chore
- Priority: high
- Set: testtier
- Order: 1
- Highest E allocated: 10
- Author: opencode its_direct/pt3-claude-opus-5.5-1m-us
- Id: hguae9

## Workflow history
- 2026-10-16 to-review (aw set): authored from prompt wazeo5 with baseline research 7ry5kv at main eca2e2211

- 2026-10-16 draft (opencode its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Bare `pytest` runs a `core` tier in under 30s (warm median, 6 workers) that executes every first-party module and every declared `aw` leaf command, and one explicit command runs every retained test before push and before release.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: selection mechanism

- [ ] E-01 Register a `core` marker in `pyproject.toml` (description: "fast behavioral regression test run by default; author-assigned"), remove `testpaths`' module list in favor of `testpaths = ["tests"]`, and change `addopts` to `-q -n auto --dist=worksteal -m 'core and not slow and not livecorpus'`. Keep `--strict-markers` behavior if present. In the same commit mark the 19 current `testpaths` modules `pytestmark = pytest.mark.core` (module level), so behavior and count are unchanged at this step.
  - Depends on: none
  - Expected outcome: `python3 -m pytest --collect-only -q` collects exactly the same 695 node ids as before (diff of sorted id lists is empty); `pytest tests/ -m '' --collect-only` still 8794.
  - Execution state: pending

### Task group 2: coverage-driven membership

- [ ] E-02 Write a measurement script under `tests/tools/` (not collected: name it without `test_` prefix) that runs core and thorough with `coverage.py` branch coverage, emits a per-module table, and enumerates `command_surface.get_declared_leaves()` (168 leaves at authoring) with the core tests that drive each leaf (via `coverage` dynamic contexts on `cli.main` dispatch or a pytest plugin hook recording invoked leaves). Add `coverage>=7` to the `test` extra.
  - Depends on: E-01
  - Expected outcome: script prints module table and leaf map; documented in `CONTRIBUTING.md`.
  - Execution state: pending
- [ ] E-03 Grow core to cover every module: for each of the 93 zero-coverage modules (research `7ry5kv`), mark the cheapest existing non-slow behavioral tests that execute it as `core` (per-test `@pytest.mark.core` or per-class), preferring tests under 0.5s by `--durations`; write a new small behavioral test only where none exists. Repeat the E-02 measurement until no first-party module with at least one full-suite-covered line has zero core coverage.
  - Depends on: E-02
  - Expected outcome: zero modules at 0% core coverage among modules the full suite covers; core line coverage reported, target at least 55% (rationale in OQ-01).
  - Execution state: pending
- [ ] E-04 Cover every declared leaf: for each `aw` leaf with no core test driving it, mark (or add) one fast in-process test (`cli.main([...])`) asserting exit code and one output property. Keep a smoke set marked `core` of at most 6 end-to-end subprocess tests: one install into a temp repo, one `aw oc run --prepare-only`, one `aw ipd lint`, one `aw check`, one `aw.agent/v1` conformance record, one `aw attention`.
  - Depends on: E-03
  - Expected outcome: leaf map shows 168/168 (or the measured count) leaves driven by a core test; smoke set listed.
  - Execution state: pending

### Task group 3: budget, thorough command, hooks, CI

- [ ] E-05 Add a budget guard in `conftest.py` (`pytest_sessionfinish`, controller process only under xdist): when the run selected exactly the default marker expression and no explicit paths, compare session wall time to a budget of 30s; FAIL (exit nonzero) only when `os.cpu_count() >= 12` (so 6 workers) and env `AW_CORE_BUDGET_ENFORCE` is not `0`, else print a warning; always print the 10 slowest tests when over budget. Budget value and margin documented in `pyproject.toml` comments.
  - Depends on: E-04
  - Expected outcome: a deliberately slowed core test (temporary `time.sleep(40)`) makes the run fail with the slowest-tests list; reverting restores pass; CI (fewer CPUs) warns only.
  - Execution state: pending
- [ ] E-06 Make the thorough tier one command: `make test-all` stays `python3 -m pytest tests/ -m ''`; add `aw suite --thorough` in `suite_cache`/`cli` that runs that argv through the same tree-keyed cache (the narrowed-selection refusal must not reject this mode; the cache key includes the mode). `aw suite` with no flag stays the core tier, and the runner merge gate (`SUITE_CHECK_ARGV`) is unchanged.
  - Depends on: E-01
  - Expected outcome: `aw suite --thorough` twice on an unchanged tree: second run is a cache hit; `aw suite` unchanged.
  - Execution state: pending
- [ ] E-07 Add a local `pre-push` hook to `.pre-commit-config.yaml` (`stages: [pre-push]`, `always_run: true`, `pass_filenames: false`, entry `aw suite --thorough`, `verbose: true`) and add `pre-push` to `default_install_hook_types`. Document that it is local feedback, skippable with `--no-verify`, and not an authority boundary.
  - Depends on: E-06
  - Expected outcome: `pre-commit install --hook-type pre-push` installs it; `pre-commit run --hook-stage pre-push --all-files` runs the thorough tier (cache hit on second call); a failing test makes it exit nonzero.
  - Execution state: pending
- [ ] E-08 In `.github/workflows/tests.yml`, make the required matrix job run `python -m pytest` (core) and add a thorough job running `python -m pytest tests/ -m ''` on ubuntu, keeping the existing tracked-advisory pattern for the named slow failures; correct every comment that no longer matches the YAML.
  - Depends on: E-04
  - Expected outcome: YAML diff shows the two jobs; `python3 -c "import yaml;yaml.safe_load(open('.github/workflows/tests.yml'))"` passes.
  - Execution state: pending

### Task group 4: documentation and proof

- [ ] E-09 Update the repo-local "HOW TO RUN THE SUITE" paragraph in `AGENTS.md` (below the managed block only), `CONTRIBUTING.md`, `RELEASING.md`, `Makefile` comments, `docs/row-level-test-evidence.md`, and release-review `08-final-ship-review.md` so all name `python3 -m pytest` (core, runner merge gate) and `make test-all` / `aw suite --thorough` (thorough: pre-push, CI, release); finalize research `7ry5kv` with the after-measurements; add a CHANGELOG line (no em/en dashes in user-facing docs).
  - Depends on: E-05, E-07, E-08
  - Expected outcome: `git grep -n "testpaths\|19 hand-picked\|representative behavioral modules"` finds no stale description.
  - Execution state: pending
- [ ] E-10 Prove the result: three warm core runs; thorough run; before/after `--collect-only -m ''` count equality (8794 unless pruning landed first); three consecutive core runs under `pytest-randomly` with no failure; one-line mutation in a core-covered module fails core, one in a thorough-only path fails `pre-commit run --hook-stage pre-push`; both reverted with an empty diff.
  - Depends on: E-09
  - Expected outcome: all evidence pasted in V-10.
  - Execution state: pending

## Project conventions discovered (Step 0)

- `suite_cache.SUITE_CHECK_ARGV` (bare `python3 -m pytest`) is what the runners revalidate lanes with (`runner_shared` merge gate), so the core tier IS the merge gate; keeping it fast is a throughput requirement, keeping it broad is a correctness one.
- `conftest.pytest_xdist_auto_num_workers` caps workers at min(6, cpus/2); this host resolves to 6.
- Markers `slow` (280 tests) and `livecorpus` (12) exist with recorded reasons; `livecorpus` must stay out of the merge gate (pyproject marker text).
- Local hooks are best-effort feedback, not authority (AGENTS.md "Before you publish to main", prepush-authorization-gate wording).
- P16: tests exercise behavior; membership changes here move tests between tiers, never weaken them.

## Findings

| # | Finding | Evidence |
| --- | --- | --- |
| F-1 | Default covers 28% of lines; 93/196 modules at zero | research `7ry5kv` coverage table |
| F-2 | Default median 20.9s, so about 9s of budget remains for broadening | research `7ry5kv` wall times |
| F-3 | Full suite 565s; two `doctor` live-leaf conformance tests take 118s and 64s | `--durations=30` in research `7ry5kv` |
| F-4 | No pre-push stage; `default_install_hook_types: [pre-commit, pre-merge-commit]` | `.pre-commit-config.yaml` |
| F-5 | CI required job already runs the whole `tests/` tree, not the default | `tests.yml` "Run self-tests (parallel)" step |
| F-6 | `aw suite` refuses any narrowed selection, so a thorough mode needs an explicit flag | `suite_cache.SUITE_REFUSAL_MESSAGE` |

## Proposed changes (ordered, validatable)

E-01 (mechanism, zero behavior change) -> E-02..E-04 (measured broadening) -> E-05..E-08 (guard, thorough command, hook, CI) -> E-09..E-10 (docs, proof).

## Deferred / out of scope (with reason)

- Deleting, merging or speeding up tests: owned by prompt `4ul37x` (Set `testprune`), which runs after this plan.
  - Carrier-Declined: tracked by staged prompt `4ul37x`; it will produce its own plan Set.

## Scope check

- Over-scope: none.
- Under-scope: none.

## Required tests / validation

Per V-items; bare `python3 -m pytest` and `make test-all` at the end, pasted.

## Spec / documentation sync

No spec governs the test tiers; documentation updated in E-09.

## Open questions

### OQ-01: What core coverage target is right?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from evidence 2026-10-16: the hard requirement is every module and every leaf executed by core (E-03/E-04); the numeric line-coverage target is at least 55% (about three quarters of the full suite's 75%), chosen because 9s of budget remains (F-2) and the cheapest per-module tests are sub-second. If 30s is reached first, E-03 records the achieved number and the uncovered modules rather than exceeding the budget.

### OQ-02: Should the pre-push hook be installed by default?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Resolved from the maintainer's request ("run the more extended regression tests at most when pushing"): yes, add `pre-push` to `default_install_hook_types`, so `pre-commit install` installs it; it remains skippable with `--no-verify` and cache-backed so an unchanged tree costs nothing.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [ ] V-01 validates E-01
  - Required evidence: pasted `diff` of sorted default node ids before and after (empty) and the `-m ''` collect count.
  - Observed evidence:
  - Result: pending
- [ ] V-02 validates E-02
  - Required evidence: pasted measurement script output header (module table excerpt and leaf-map totals).
  - Observed evidence:
  - Result: pending
- [ ] V-03 validates E-03
  - Required evidence: pasted per-module table showing zero modules at 0% core among full-covered modules, and core total line and branch coverage.
  - Observed evidence:
  - Result: pending
- [ ] V-04 validates E-04
  - Required evidence: pasted leaf-map totals (driven/declared) and the smoke-test node ids.
  - Observed evidence:
  - Result: pending
- [ ] V-05 validates E-05
  - Required evidence: pasted failing run with the temporary sleep (budget message plus slowest list), pasted passing run after revert, and empty `git diff` of the temporary change.
  - Observed evidence:
  - Result: pending
- [ ] V-06 validates E-06
  - Required evidence: pasted two `aw suite --thorough` runs (second a cache hit) and `aw suite --explain` showing the mode in the key.
  - Observed evidence:
  - Result: pending
- [ ] V-07 validates E-07
  - Required evidence: pasted `pre-commit run --hook-stage pre-push --all-files` (pass, then cache hit) and a failing case's nonzero exit (code path: the pre-push hook entry `aw suite --thorough`).
  - Observed evidence:
  - Result: pending
- [ ] V-08 validates E-08
  - Required evidence: the YAML diff and the `yaml.safe_load` check output.
  - Observed evidence:
  - Result: pending
- [ ] V-09 validates E-09
  - Required evidence: pasted stale-description `git grep` returning nothing, the CHANGELOG line, and the updated research summary line.
  - Observed evidence:
  - Result: pending
- [ ] V-10 validates E-10
  - Required evidence: three warm core wall times (median under 30s) with test count, thorough wall time and count, collect-count equality, three randomized core runs, both mutation demonstrations with reverts, and the bare `python3 -m pytest` summary line.
  - Observed evidence:
  - Result: pending

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after review and human approval, in an isolated worktree (`aw work begin hguae9`); commit via `aw commit hguae9 -- <paths>`; never push or tag; publish via `aw integration-lock -- git merge --ff-only <branch>`. `tests/` is declared because E-03/E-04 add `core` markers across many test modules; no test is deleted or skipped. Paste ACTUAL output in each V-item.
