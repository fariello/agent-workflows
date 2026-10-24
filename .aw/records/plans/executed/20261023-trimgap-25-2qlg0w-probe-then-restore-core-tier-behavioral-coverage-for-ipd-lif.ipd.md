# IPD: Probe then restore core-tier behavioral coverage for ipd_lifecycle begin and finalize keys

- Date: 2026-10-23
- Kind: child
- Concern: Backlog item `gcpj15` (Set `trimgap`, group 4 of the `wo21z5` `## Filing plan`) carries four production keys of `agent_workflows/ipd_lifecycle.py` that the `wo21z5` budget probe never measured (verdict `budget-exhausted` at 11130.81s): `_baseline_ambiguity`, `begin`, `_execution_cohesive_committed_paths` and `finalize_precheck`, all with operator `return-none`. Their control files were deleted by `19313eed` (`tests/test_begin_dirty_gate_scope.py`, `tests/test_finalize_exact_attribution.py`, `tests/test_finalize_scope_ownership.py`). Probing at authoring HEAD `5fc148a3` (F-01..F-03) shows all four `return-none` mutants SURVIVE the routine core tier (bare `python3 -m pytest`, the runner merge gate), and are killed only by non-core files that a routine run deselects. So a regression that made `begin` or `finalize_precheck` return nothing would pass the merge gate.
- Scope: Add ONE new core-marked test module, `tests/test_ipd_lifecycle_restored_behavior.py`, holding eight behavioral tests mined verbatim (fixtures and bodies) from the three `19313eed^` control files: two per key, chosen because each pair alone kills that key's `return-none` mutant (F-04). Then re-probe all four keys under the core selection. EXCLUDES any production-code change; EXCLUDES restoring the three control files whole (core budget, F-05); EXCLUDES the `run_evidence.py` keys `_porcelain_paths`, `dirty_within`, `get_git_head` that share the `test_begin_dirty_gate_scope.py` control file (owned by backlog `i2g20d`); EXCLUDES `RunnerDeclaresTheExecutionBaselineTests::test_driver_begin_accepts_the_isolated_declaration` (it pins a signature through `inspect`, which `AGENTS.md` forbids).
- Scope-Paths: tests/test_ipd_lifecycle_restored_behavior.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: gcpj15
- Set: trimgap
- Order: 25
- Highest E allocated: 04
- Author: opencode
- Id: 2qlg0w

## Workflow history
- 2026-10-24 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 2qlg0w verified (set trimgap, attempt 1).
- 2026-10-23 approved (aw set): status set to approved
- 2026-10-23 reviewed (aw set): /plan-review (opencode/uri/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-006 fixed (ruff-safe import set, _commit_paths collision named, V-03 kill attribution, commit-then-probe, count bars and <base>, execution contract); swap demonstrated (F-08)

- 2026-10-23 to-review (opencode): authored from backlog `gcpj15`. Probed all four keys at HEAD `5fc148a3` under `-m core` (all `survived`), under existing non-core lifecycle files (all `killed`), and under two-test subsets of the `19313eed^` control files (all `killed`, `mutant_failing: 2`); measured bare core at `1675 passed ... 91.54s` with the budget already exceeded, which is why the restore is a minimal subset.
- 2026-10-23 draft (opencode): created.

## Goal

Make a `return-none` mutation of each of the four `gcpj15` keys turn the routine core tier red, by restoring a minimal set of the deleted behavioral tests into a core-marked module. Done means all four keys report `verdict: killed` under the full `-m core` selection with the new module present.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: restore the minimal core-tier module

- [x] E-01 Create `tests/test_ipd_lifecycle_restored_behavior.py` with a provenance docstring naming backlog `gcpj15`, plan `2qlg0w`, source `19313eed^` and the three control files; `import pytest` and module-level `pytestmark = pytest.mark.core` (the pattern of `tests/test_engine_restored_behavior.py`); the helper imports the control files used from `tests.test_ipd_lifecycle_cli` (`_init_git`, `_commit_all`, `_ready_plan_text`, `_completed_plan_text`, `_write_plan`); and the three fixture base classes copied from `19313eed^`: `_Fixture` plus its `_git` helper and `IN_SCOPE` constant from `tests/test_begin_dirty_gate_scope.py`, `_ScopeOwnershipBase` plus `_commit_paths`/`_git_out` from `tests/test_finalize_scope_ownership.py`, and `_ExactAttributionBase` plus its `_commit_paths` from `tests/test_finalize_exact_attribution.py`. Rename colliding module-level helpers or constants (`_commit_paths`, `ACTOR`, `SCOPE`) with a per-source prefix only where the two sources differ; do not change any helper's behavior. Measured at review: `ACTOR = "opencode/test"` and `SCOPE = "agent_workflows/demo.py, tests/test_demo.py"` are identical in both finalize sources (define once), while `_commit_paths` differs (the exact-attribution copy returns the sha, the scope-ownership copy returns `None`), so keep both as `_ea_commit_paths` and `_so_commit_paths` and update only the call sites inside the copied bases and tests. Module imports are exactly what the copied code uses: `json`, `subprocess`, `tempfile`, `unittest`, `pathlib.Path`, `pytest`, `from agent_workflows import ipd_lifecycle as LC`, and the five `tests.test_ipd_lifecycle_cli` helpers. Do NOT copy `from agent_workflows import oc_runipd as OC` (used only by the excluded `RunnerDeclaresTheExecutionBaselineTests`) or `inspect`: the pre-commit `ruff --fix` hook (`.pre-commit-config.yaml` `id: ruff`) would rewrite an unused import and reject the commit. Before creating the file, record `git rev-parse HEAD` as `<base>` in this item's evidence; V-03 and the no-production-change check diff against it.
  - Depends on: none
  - Expected outcome: the module imports cleanly, `ruff check` and `ruff format --check` on it are clean, and it defines the three fixture bases with no test methods yet; `<base>` recorded.
  - Execution state: performed

- [x] E-02 Add these eight test methods, bodies copied verbatim from `19313eed^` except for renamed helper references, each in a subclass of its source fixture base: `begin` = `IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn` and `NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline`; `_baseline_ambiguity` = `IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo` and `IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated`; `_execution_cohesive_committed_paths` = `NothingElseMovedTests::test_cohesion_reports_UNANCHORED_rather_than_an_empty_set` and `NothingElseMovedTests::test_cohesion_groups_paths_by_commit_not_by_position`; `finalize_precheck` = `FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly` and `ExactSourceWinsTests::test_the_plans_own_out_of_scope_path_is_still_demanded`. Every test calls `ipd_lifecycle` functions and asserts on exit codes, receipts, returned attribution objects or finalize output; none reads source. Disposition rule if a copied test fails at execution HEAD (none did at review, F-08): do not mark this item performed until it is dispositioned. Record the failure in Findings; for an intended behavior change cite the commit `git log -S` finds and adjust only that expectation; for a regression file a `bug` backlog item with `aw backlog new ... --blocks-release next` and mark the test `@pytest.mark.xfail(strict=True, reason="<bug id6>")` rather than deleting it.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" -v tests/test_ipd_lifecycle_restored_behavior.py` reports every collected test PASSED with none failed, skipped, xfailed or errored, and the collected set covers all four keys (the binding proof that each key is guarded is the E-03 probe, not the count).
  - Execution state: performed

### Task group 2: prove the mutants die in the core tier

- [x] E-03 For each key K in (`begin`, `_baseline_ambiguity`, `_execution_cohesive_committed_paths`, `finalize_precheck`), run `python3 tools/mutation_probe.py --op return-none agent_workflows/ipd_lifecycle.py::K -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/`. `tools/mutation_probe.py` mutates in its own isolated worktree cut from HEAD, so the new file must be COMMITTED first (E-04) and the probe run afterwards; do not use `--extra-test` for it (that flag reads `COMMIT^:PATH`, the parent of the named commit, and exists to resurrect deleted files, not to inject an uncommitted one). Record each `verdict:` and `mutant_failing:` line in Findings. If any key reports `survived`, add the next killing test for that key from its control file (the `newly_failing` lists in F-04's sources) and re-probe.
  - Depends on: E-04
  - Expected outcome: four `verdict: killed` lines under the full core selection.
  - Execution state: performed

- [x] E-04 Commit `tests/test_ipd_lifecycle_restored_behavior.py` with `aw commit 2qlg0w -- tests/test_ipd_lifecycle_restored_behavior.py`, then run the routine bare gate `python3 -m pytest` and record the summary line and any `CORE TIER BUDGET EXCEEDED` block, with the new module's own durations from `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_ipd_lifecycle_restored_behavior.py`.
  - Depends on: E-02
  - Expected outcome: bare run shows no test failures and its `passed` count grew by the new module's collected tests relative to `<base>`; the new module's summed call time is a few seconds at most (F-05 measured per-test calls of about 0.5s to 0.7s; F-08 measured 3.82s total serial for the eight). A `CORE TIER BUDGET EXCEEDED` block is recorded, not treated as a failure of this item, when it was already firing at `<base>` (F-05); if it fires ONLY with the new module, record both wall times and the module's share.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md` "TEST OUTCOMES, NOT CODE STRUCTURE"): every restored test drives `ipd_lifecycle.begin`, `finalize_precheck` or the helpers on real throwaway git repos and asserts on results. The one `inspect`-based control test is excluded.
- THE ROUTINE GATE IS THE CORE TIER: bare `python3 -m pytest` keeps only `core`-marked items (`conftest.pytest_collection_modifyitems`, IPD `hguae9`) under a 30s budget enforced by `conftest.pytest_sessionfinish`. Module-level `pytestmark = pytest.mark.core` applies to `unittest.TestCase` classes (`tests/test_engine_restored_behavior.py`, executed `33f8tn`).
- Probe tool: `tools/mutation_probe.py` (`--op`, `--extra-test COMMIT:PATH`, selection after `--`) is the tool `wo21z5` and sibling plan `92tzo6` used, so verdicts are comparable.
- Sibling precedent: executed `jy7439` restored a deleted module into the core tier with `pytestmark` and recorded its budget impact.
- Commit only through `aw commit 2qlg0w -- <paths>`; never push.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `tools/mutation_probe.py --op return-none agent_workflows/ipd_lifecycle.py::<K> -- -o addopts= -q -p no:randomly -n 6 -m "core and not slow and not livecorpus" tests/` at HEAD `5fc148a3` | `begin`: `verdict: survived`, `mutant_failing: 0` (220.93s). `_baseline_ambiguity`: `survived`, 0 (270.88s). `_execution_cohesive_committed_paths`: `survived`, 0 (287.69s). `finalize_precheck`: `survived`, 0 (440.73s). The merge gate does not guard any of the four keys. |
| F-02 | bare `python3 -m pytest --collect-only` at HEAD `5fc148a3` | Core collects 1675 of 10225 tests; the only lifecycle-adjacent core files are `test_ipd_lint.py`, `test_ipd_schema.py`, `test_ipd_set_executor.py`, `test_lifecycle_fixtures.py`, `test_scope_match.py` and the like. `tests/test_ipd_lifecycle_cli.py`, `tests/test_finalize_*.py` and `tests/test_receipt_lane_record.py` carry no core marker. |
| F-03 | same probe tool, non-core selection `-m "not slow and not livecorpus"` over `tests/test_receipt_lane_record.py tests/test_finalize_disregarded_record.py tests/test_finalize_trailer_attribution.py tests/test_finalize_empty_declared_scope.py tests/test_commit_scope_reason.py tests/test_finalize_sendback.py tests/test_finalize_stale_plan_path.py tests/test_finidem_reusable_not_finalized.py` | All four `killed` (`mutant_failing` 28, 28, 21, 25). The keys are guarded by the thorough tier, not by the core tier. The gap is core-tier reach only. |
| F-04 | same probe tool with `--extra-test 19313eed:<control>` and two node ids per key (the E-02 pairs) | Every pair kills its key alone: `begin` killed 2 (20.88s), `_baseline_ambiguity` killed 2 (20.64s), `_execution_cohesive_committed_paths` killed 2 (20.58s), `finalize_precheck` killed 2 (15.21s). The whole control files kill 14, 15, 22 and 8 tests respectively. The `_baseline_ambiguity` pair used for F-04 was (`test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo`, `test_the_same_dirt_still_refuses_a_non_isolated_turn`); E-02 swaps the second for `test_unreadable_base_commit_is_still_refused_when_isolated` so no test is listed twice. That swap was untested at authoring; review demonstrated it (F-08), and E-03 still re-probes under the full core selection. |
| F-05 | bare `python3 -m pytest` at HEAD `5fc148a3`; `-n0 --durations` over the three restored control files | Bare core: `1675 passed, 11 warnings in 91.54s` with `CORE TIER BUDGET EXCEEDED` already firing before any change (host load and pre-existing tests; not caused here). The three control files total 55 tests passing in 19.95s serial, per-test calls about 0.5s to 0.73s. Restoring all 55 into core would add about 20s CPU to an already over-budget tier; eight tests add about 5s CPU, spread over 6 workers. |
| F-06 | `git show 19313eed^:tests/test_begin_dirty_gate_scope.py`, `RunnerDeclaresTheExecutionBaselineTests` | `test_driver_begin_accepts_the_isolated_declaration` uses `inspect.signature`, a code-structure pin; excluded. All other control tests call code and assert outcomes. |
| F-07 | `.aw/records/backlog/open/20261018-trimgap-01-i2g20d-*.backlog.md` | Backlog `i2g20d` owns the `run_evidence.py` keys (`_porcelain_paths`, `dirty_within`, `get_git_head`) that share the `test_begin_dirty_gate_scope.py` control file; they are out of scope here so the two items do not double-restore. |
| F-08 | review at HEAD `623eb73c`: the eight E-02 tests run from `19313eed^` copies (`-n0 --durations=0`); `tools/mutation_probe.py --op return-none --extra-test 19313eed:tests/test_begin_dirty_gate_scope.py agent_workflows/ipd_lifecycle.py::_baseline_ambiguity` over the two E-02 `_baseline_ambiguity` node ids | Eight tests `8 passed in 3.82s`, slowest call 1.72s (`test_cohesion_reports_UNANCHORED_rather_than_an_empty_set`), the rest 0.03s to 0.19s. Swapped pair: `verdict: killed`, `baseline_failing: 0`, `mutant_failing: 1`, newly failing `test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo` (17.98s). The second test does not itself kill `_baseline_ambiguity` (cause not investigated), so the key is guarded by one test within the pair; that suffices for the item's bar, and E-03 measures the full core selection. Constants `ACTOR`/`SCOPE` are identical across the finalize sources; `_commit_paths` differs (returns sha vs `None`). |

## Proposed changes (ordered, validatable)

1. E-01 creates the core-marked module with the three fixture bases mined from `19313eed^`.
2. E-02 adds the eight behavioral tests, two per key.
3. E-04 commits the module and checks the bare core gate and the module's cost.
4. E-03 re-probes all four keys under the full core selection against the committed tree.

## Deferred / out of scope (with reason)

- Restoring the three control files whole (55 tests).
  - Carrier-Declined: no work is owed; the item's remedy is behavioral coverage of four keys, which eight tests deliver (F-04), the full files remain killing in the thorough tier through existing modules (F-03), and the core tier is already over budget (F-05).
- Core-marking existing lifecycle modules such as `tests/test_ipd_lifecycle_cli.py`.
  - Carrier-Declined: no work is owed; marking whole existing modules core would add far more time than eight targeted tests and is a core-tier policy decision outside this item.
- The `inspect`-based `test_driver_begin_accepts_the_isolated_declaration`.
  - Carrier-Declined: no work is owed; it pins code structure, which `AGENTS.md` forbids restoring.

## Scope check

- Over-scope: none. Only the new test module is declared; no production file or existing test changes.
- Under-scope: none. All four backlog keys get two killing tests (E-02) and a core-selection probe (E-03).

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_ipd_lifecycle_restored_behavior.py`: every collected test PASSED, per-test list pasted (E-02); module present in the bare `--collect-only` core selection.
- Four `tools/mutation_probe.py` runs under `-m "core and not slow and not livecorpus" tests/`, full `head`/`target`/`operator`/`selection`/`verdict`/`mutant_failing` output pasted, each `killed` (E-03).
- Bare `python3 -m pytest` summary line and any budget block pasted, plus the module's `--durations=0` output (E-04).
- `git diff --stat <base>..HEAD -- agent_workflows/` empty (no production change; `<base>` recorded in E-01).
- `ruff check` / `ruff format --check` clean on the new module (E-01).

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Restore the control files whole, or a minimal killing subset?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: minimal subset. F-04 shows two tests per key kill each mutant; F-03 shows the remaining behaviors stay guarded outside core; F-05 shows core is already over its 30s budget, so adding 55 serial-git tests would worsen the merge gate for no additional key coverage. Sibling `92tzo6` applied the same no-redundant-tests reasoning.

### OQ-02: Should E-03 probe the full core selection or only the new file?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: the full core selection (`-m core ... tests/`), because the item's gap is "the routine gate does not kill the mutant" (F-01), and only a probe over that exact selection proves it closed. It costs about 4 to 8 minutes per key (F-01 wall times), acceptable for a one-off verification.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste the head of `tests/test_ipd_lifecycle_restored_behavior.py` showing the provenance docstring (naming `gcpj15`, `2qlg0w`, `19313eed^`) and `pytestmark = pytest.mark.core`; paste `grep -nE "inspect|getsource|ast\." tests/test_ipd_lifecycle_restored_behavior.py` returning nothing; paste clean `ruff check` and `ruff format --check` output for the file; paste the recorded `<base>` sha.
  - Observed evidence:
    Head of `tests/test_ipd_lifecycle_restored_behavior.py`:
    ```python
    """Restored behavioral tests for agent_workflows/ipd_lifecycle.py begin, _baseline_ambiguity,
    _execution_cohesive_committed_paths, and finalize_precheck.

    Restores core-tier behavioral coverage for four production keys recorded in backlog item gcpj15
    and IPD 2qlg0w, whose control files were deleted at 19313eed^:
    - tests/test_begin_dirty_gate_scope.py
    - tests/test_finalize_exact_attribution.py
    - tests/test_finalize_scope_ownership.py
    """

    from __future__ import annotations

    import json
    import subprocess
    import tempfile
    import unittest
    from pathlib import Path

    import pytest

    from agent_workflows import ipd_lifecycle as LC
    from tests.test_ipd_lifecycle_cli import (
        _commit_all,
        _completed_plan_text,
        _init_git,
        _ready_plan_text,
        _write_plan,
    )

    pytestmark = pytest.mark.core
    ```
    No ast/inspect/getsource references:
    ```
    $ grep -nE "inspect|getsource|ast\." tests/test_ipd_lifecycle_restored_behavior.py
    (empty, exit 1)
    ```
    Clean ruff check and format:
    ```
    $ ruff check tests/test_ipd_lifecycle_restored_behavior.py && ruff format --check tests/test_ipd_lifecycle_restored_behavior.py
    All checks passed!
    1 file already formatted
    ```
    Recorded `<base>` sha:
    ```
    45f067269c849f8004d48d6fc8d233dc77b77835
    ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_ipd_lifecycle_restored_behavior.py` (re-run at execution) showing every collected test PASSED and a summary line with no `failed`, `skipped`, `xfailed` or `error`, and the collected tests covering the E-02 behaviors of all four keys (the E-02 names are pointers, not the bar); paste `python3 -m pytest --collect-only -q 2>&1 | grep test_ipd_lifecycle_restored_behavior` showing the module is collected by the BARE core selection.
  - Observed evidence:
    `python3 -m pytest -o addopts="" -v tests/test_ipd_lifecycle_restored_behavior.py`:
    ```
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <venv>/bin/python3
    cachedir: .pytest_cache
    Using --randomly-seed=860840240
    rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/2qlg0w
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 8 items

    tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo PASSED [ 12%]
    tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated PASSED [ 25%]
    tests/test_ipd_lifecycle_restored_behavior.py::ExactSourceWinsTests::test_the_plans_own_out_of_scope_path_is_still_demanded PASSED [ 37%]
    tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn PASSED [ 50%]
    tests/test_ipd_lifecycle_restored_behavior.py::NothingElseMovedTests::test_cohesion_reports_UNANCHORED_rather_than_an_empty_set PASSED [ 62%]
    tests/test_ipd_lifecycle_restored_behavior.py::NothingElseMovedTests::test_cohesion_groups_paths_by_commit_not_by_position PASSED [ 75%]
    tests/test_ipd_lifecycle_restored_behavior.py::FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly PASSED [ 87%]
    tests/test_ipd_lifecycle_restored_behavior.py::NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline PASSED [100%]
    ============================== SLOW TESTS REPORT ===============================

    WARNING: 1 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
        2.48s  tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated
    ============================== 8 passed in 5.17s ===============================
    ```
    Bare collect-only:
    ```
    $ python3 -m pytest --collect-only -q 2>&1 | grep test_ipd_lifecycle_restored_behavior
    tests/test_ipd_lifecycle_restored_behavior.py: 8
    ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the full output of the four `tools/mutation_probe.py` runs (produced by the tool itself, E-03), each with `selection:` containing `-m core and not slow and not livecorpus tests/`, a `head:` equal to the E-04 commit or later, `baseline_failing: 0`, `verdict: killed`, and a `newly_failing` list naming at least one test from `tests/test_ipd_lifecycle_restored_behavior.py` (so the kill is attributable to the new module rather than to an unrelated core test); paste `git diff --stat <base>..HEAD -- agent_workflows/` (the E-01 `<base>`) showing no change.
  - Observed evidence:
    Probe 1 (`begin`):
    ```
    head: f76b44cee1fecbdd11c8637ef32e6ac77d66c478
    target: agent_workflows/ipd_lifecycle.py::begin
    operator: return-none
    selection: -o addopts= -q -p no:randomly -n 6 -m core and not slow and not livecorpus tests/
    verdict: killed
    baseline_failing: 0
    mutant_failing: 7
    newly_failing (7 total):
      tests.test_ipd_lifecycle_restored_behavior.ExactSourceWinsTests::test_the_plans_own_out_of_scope_path_is_still_demanded
      tests.test_ipd_lifecycle_restored_behavior.FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly
      tests.test_ipd_lifecycle_restored_behavior.IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn
      tests.test_ipd_lifecycle_restored_behavior.IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated
      tests.test_ipd_lifecycle_restored_behavior.NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline
      tests.test_ipd_lifecycle_restored_behavior.NothingElseMovedTests::test_cohesion_groups_paths_by_commit_not_by_position
      tests.test_ipd_lifecycle_restored_behavior.NothingElseMovedTests::test_cohesion_reports_UNANCHORED_rather_than_an_empty_set
    wall_s: 554.61
    ```
    Probe 2 (`_baseline_ambiguity`):
    ```
    head: f76b44cee1fecbdd11c8637ef32e6ac77d66c478
    target: agent_workflows/ipd_lifecycle.py::_baseline_ambiguity
    operator: return-none
    selection: -o addopts= -q -p no:randomly -n 6 -m core and not slow and not livecorpus tests/
    verdict: killed
    baseline_failing: 0
    mutant_failing: 7
    newly_failing (7 total):
      tests.test_ipd_lifecycle_restored_behavior.ExactSourceWinsTests::test_the_plans_own_out_of_scope_path_is_still_demanded
      tests.test_ipd_lifecycle_restored_behavior.FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly
      tests.test_ipd_lifecycle_restored_behavior.IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn
      tests.test_ipd_lifecycle_restored_behavior.IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo
      tests.test_ipd_lifecycle_restored_behavior.NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline
      tests.test_ipd_lifecycle_restored_behavior.NothingElseMovedTests::test_cohesion_groups_paths_by_commit_not_by_position
      tests.test_ipd_lifecycle_restored_behavior.NothingElseMovedTests::test_cohesion_reports_UNANCHORED_rather_than_an_empty_set
    wall_s: 507.46
    ```
    Probe 3 (`_execution_cohesive_committed_paths`):
    ```
    head: f76b44cee1fecbdd11c8637ef32e6ac77d66c478
    target: agent_workflows/ipd_lifecycle.py::_execution_cohesive_committed_paths
    operator: return-none
    selection: -o addopts= -q -p no:randomly -n 6 -m core and not slow and not livecorpus tests/
    verdict: killed
    baseline_failing: 0
    mutant_failing: 3
    newly_failing (3 total):
      tests.test_ipd_lifecycle_restored_behavior.FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly
      tests.test_ipd_lifecycle_restored_behavior.NothingElseMovedTests::test_cohesion_groups_paths_by_commit_not_by_position
      tests.test_ipd_lifecycle_restored_behavior.NothingElseMovedTests::test_cohesion_reports_UNANCHORED_rather_than_an_empty_set
    wall_s: 499.37
    ```
    Probe 4 (`finalize_precheck`):
    ```
    head: f76b44cee1fecbdd11c8637ef32e6ac77d66c478
    target: agent_workflows/ipd_lifecycle.py::finalize_precheck
    operator: return-none
    selection: -o addopts= -q -p no:randomly -n 6 -m core and not slow and not livecorpus tests/
    verdict: killed
    baseline_failing: 0
    mutant_failing: 2
    newly_failing (2 total):
      tests.test_ipd_lifecycle_restored_behavior.ExactSourceWinsTests::test_the_plans_own_out_of_scope_path_is_still_demanded
      tests.test_ipd_lifecycle_restored_behavior.FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly
    wall_s: 443.15
    ```
    Zero production code changes check:
    ```
    $ git diff --stat 45f067269c849f8004d48d6fc8d233dc77b77835..HEAD -- agent_workflows/
    (empty, 0 files changed)
    ```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste `git show --stat HEAD` (or the `aw commit` output) showing only `tests/test_ipd_lifecycle_restored_behavior.py`; paste the bare `python3 -m pytest` summary line showing `passed` and no `failed`, any `CORE TIER BUDGET EXCEEDED` block verbatim, and the `--durations=0` output for the new module.
  - Observed evidence:
    `git show --stat f76b44cee1fecbdd11c8637ef32e6ac77d66c478`:
    ```
    commit f76b44cee1fecbdd11c8637ef32e6ac77d66c478 (HEAD -> aw/lane/2qlg0w)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 23 21:51:26 2026 -0400

        Restore core-tier behavioral coverage for ipd_lifecycle keys (E-01, E-02)

        AW-Run: run-20261024T014612Z-3125888
        AW-Item: 2qlg0w
        AW-Runner: aw agy run

     tests/test_ipd_lifecycle_restored_behavior.py | 408 ++++++++++++++++++++++++++
     1 file changed, 408 insertions(+)
    ```
    Bare `python3 -m pytest` summary line:
    ```
    1683 passed, 11 warnings in 100.24s (0:01:40)
    ```
    (No `CORE TIER BUDGET EXCEEDED` block emitted; passed count grew by 8 from 1675 at `<base>`)
    `python3 -m pytest -o addopts="" --durations=0 -n0 tests/test_ipd_lifecycle_restored_behavior.py`:
    ```
    ============================== slowest durations ===============================
    0.35s call     tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated
    0.33s call     tests/test_ipd_lifecycle_restored_behavior.py::ExactSourceWinsTests::test_the_plans_own_out_of_scope_path_is_still_demanded
    0.32s call     tests/test_ipd_lifecycle_restored_behavior.py::FallBackWhenAbsentTests::test_no_corpus_reproduces_the_cohesion_result_exactly
    0.24s call     tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineGrantsAuthorityTests::test_the_same_dirt_still_refuses_a_non_isolated_turn
    0.19s call     tests/test_ipd_lifecycle_restored_behavior.py::NothingElseMovedTests::test_cohesion_reports_UNANCHORED_rather_than_an_empty_set
    0.18s call     tests/test_ipd_lifecycle_restored_behavior.py::NonIsolatedRefusalIsUnchangedTests::test_refusal_names_the_measured_baseline
    0.14s call     tests/test_ipd_lifecycle_restored_behavior.py::NothingElseMovedTests::test_cohesion_groups_paths_by_commit_not_by_position
    0.06s call     tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo
    0.01s teardown tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_unreadable_base_commit_is_still_refused_when_isolated
    0.01s setup    tests/test_ipd_lifecycle_restored_behavior.py::IsolatedBaselineStillFailsClosedTests::test_baseline_ambiguity_helper_reports_unversioned_outside_a_repo

    (14 durations < 0.005s hidden.  Use -vv to show these durations.)
    ============================== 8 passed in 2.79s ===============================
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`); every open question is resolved. Commit only files you changed, through `aw commit 2qlg0w -- tests/test_ipd_lifecycle_restored_behavior.py` (plus this plan when recording evidence); never `git add -A`, never push. You MUST paste the ACTUAL runner and probe output into each `V-*`; never claim a test passed or a mutant was killed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary (for example a gated `bug` backlog item filed under the E-02 disposition rule) is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). No production file under `agent_workflows/` may change. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize 2qlg0w` itself.
