# IPD: Restore behavioral coverage of the repository plans recognized-status drift guard

- Date: 2026-10-14
- Kind: child
- Concern: The D52 drift guard that asserted every plan in this repository's own `.aw/records/plans/` tree carries a recognized readiness `- Status:` token, and that every plan in a terminal directory carries the matching terminal status, was deleted with `tests/test_plan_status.py` in commit `19313eed`, so a plan with a misspelled or directory-mismatched status (for example `- Status: aproved`, or an `executed/` plan still reading `approved`) would now go undetected.
- Scope: Recreate `tests/test_plan_status.py` as a behavioral test module: a status-drift checker over a given plans directory that reuses `agent_workflows.plans` (`DISPOSITION_DIRS`, `read_status`, `RECOGNIZED`, `DIR_TERMINAL`, `LEGACY_GROUP`); synthetic-tree tests proving the checker reports unrecognized tokens, missing statuses and terminal/directory mismatches (and stays silent on a clean tree); `livecorpus`-marked tests applying the checker to the live repository plans tree; and a `normalize_status` behavior test for `auto-approved`. Then replace the stale "no live guard currently asserts this" remark in the `agent_workflows/plans.py` module docstring.
- Scope-Paths: tests/test_plan_status.py, agent_workflows/plans.py, .aw/records/plans/pending/20261014-7h2he0-01-sat4he-restore-behavioral-coverage-of-the-repository-plans-recogniz.ipd.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: 7h2he0
- Set: 7h2he0
- Order: 1
- Highest E allocated: 03
- Author: opencode
- Id: sat4he

## Workflow history
- 2026-10-16 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: sat4he verified (set 7h2he0, attempt 1).
- 2026-10-15 approved (aw set): status set to approved
- 2026-10-15 reviewed (aw set): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-15 /plan-review (opencode its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-005 fixed (review record 20261014-7h2he0-01-sat4he)
- 2026-10-14 draft (opencode): created.
- 2026-10-14 to-review (opencode): authored from backlog 7h2he0; review-ready.

## Goal

Restore, as behavioral tests only (P16), the guarantee that this repository's own plan files carry a recognized readiness status that agrees with their lifecycle directory, which was lost when `tests/test_plan_status.py` was deleted (`ev7t1w` site S-19, disposition RETIRE-UNGUARDED).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: drift checker and its synthetic-tree tests

- [x] E-01 Create `tests/test_plan_status.py` with a module-level helper `status_drift(plans_dir: Path) -> tuple[int, list[str], list[str]]` that iterates `plans_mod.DISPOSITION_DIRS` under `plans_dir`, skips missing directories and any file named `README.md`, reads the status of every `*.md` file RECURSIVELY (`rglob("*.md")`, sorted, because `plans_archive` moves terminal plans into `YYYYMM/` shards inside `executed/`/`superseded/`/`not-executed/`, and a flat `glob` would silently exempt every sharded plan) with `plans_mod.read_status(path)`, and returns `(examined, unrecognized, mismatched)`: `examined` is the count of plan files read; `unrecognized` lists `"<rel>: Status=<value>"` for every file whose status is `None` or `plans_mod.LEGACY_GROUP`; `mismatched` lists every OTHER file (one already in `unrecognized` is not repeated) under a top-level directory present in `plans_mod.DIR_TERMINAL` whose status differs from the mapped terminal value. Add a `unittest.TestCase` (each test with its own `tempfile.TemporaryDirectory` cleaned up via `addCleanup`, xdist-safe; no execution-role declaration, since the checker is read-only and invokes no lifecycle verb) that writes synthetic plan files and asserts: a clean tree (`pending/` with `draft`, `to-review`, `approved`, `auto-approved`; `executed/` with `executed` and legacy `DONE`; `superseded/` with `superseded`; `not-executed/` with `not-executed`; `reusable/` with `reusable`; a `README.md` with no status) yields `([], [])`; a `pending/` file with `- Status: aproved` and one with no status line both appear in `unrecognized`; an `executed/` file with `- Status: approved` appears in `mismatched` and not in `unrecognized`; a `pending/` file with `- Status: approved` is not reported as mismatched; and a SHARDED file `executed/202609/<name>.ipd.md` with `- Status: approved` appears in `mismatched` (proving shards are scanned), while `examined` equals the number of non-README files written.
  - Depends on: none
  - Expected outcome: the module exists and its synthetic-tree tests pass, proving the checker detects each drift class (including inside a shard) and is silent on a clean tree.
  - Execution state: performed

### Task group 2: live-corpus guard and auto-approved behavior

- [x] E-02 In the same module add two tests decorated `@pytest.mark.livecorpus` (the marker registered in `pyproject.toml` for tests asserting a property over this repository's own `.aw/records/` tree, deselected from the default fast run and run by `make test-all` and release-review): `test_every_repository_plan_has_a_recognized_status` and `test_repository_terminal_plan_status_matches_directory`, each calling `status_drift(support.SOURCE_PLANS)` and asserting the respective list is empty, with the offender list in the failure message. Each asserts first that `support.SOURCE_PLANS` is a directory and that `examined > 0`, so the guard cannot pass vacuously on a missing tree. Also add a default-suite test asserting `plans_mod.normalize_status("auto-approved") == "auto-approved"` and `plans_mod.normalize_status("AUTO-APPROVED") == "auto-approved"` (D65 readiness token stays recognized through the runtime normalizer), replacing the deleted constant-membership assertions with an observed outcome.
  - Depends on: E-01
  - Expected outcome: `python3 -m pytest -o addopts="" -m livecorpus tests/test_plan_status.py` passes against the current tree, and the auto-approved test passes in the default run.
  - Execution state: performed

### Task group 3: stale remark

- [x] E-03 In the `agent_workflows/plans.py` module docstring, replace the parenthetical "(``tests/test_plan_status.py`` was deleted in ``19313eed``; no live guard currently asserts this drift check directly)" with text naming `tests/test_plan_status.py` as the live drift guard (noting its live-corpus tests are marked `livecorpus`). Docstring-only change; no behavior change.
  - Depends on: E-02
  - Expected outcome: the docstring names the restored live guard and no longer claims the guard is absent.
  - Execution state: performed

## Project conventions discovered (Step 0)

- P16 (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"): tests must drive the code and assert on outputs; never read production source via `inspect`/`ast`/regex. Reading plan RECORD files (data, not source) through `plans_mod.read_status` is behavioral.
- `pyproject.toml` registers the `livecorpus` marker for tests asserting a property over every artifact in this repo's own `.aw/records/` tree and deselects it by default (`addopts = "-q -n auto --dist=worksteal -m 'not slow and not livecorpus'"`), because a red live-corpus test would block every concurrent runner lane's integration. Precedent: `tests/test_readiness_absence_invariant.py` `test_corpus_partition_pre_review_plans_lack_readiness_field`.
- `tests/support.py` `SOURCE_PLANS` resolves this repo's own plans tree (`.aw/records/plans`, legacy `.agents/plans` fallback).
- `plans.scan` resolves its root through `record_producers.resolve_record_path`, which for an arbitrary temp directory resolves to a per-user external projects directory, not `<tmp>/.aw/records/plans`; the checker therefore walks a given plans directory directly with `DISPOSITION_DIRS` + `read_status` so synthetic-tree tests stay hermetic.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).

## Findings

- `agent_workflows/plans.py` defines `PRE_TERMINAL` (includes `auto-approved`), `RECOGNIZED`, `DIR_TERMINAL` (`executed`/`superseded`/`not-executed`), `LEGACY_MAP` (`pending`->`to-review`, `done`->`executed`), `LEGACY_GROUP`, `DISPOSITION_DIRS`, `normalize_status` and `read_status`; these are the single source of truth the restored guard reuses.
- Executed plan `ev7t1w` (`.aw/records/plans/executed/20261011-iosmvn-03-ev7t1w-retire-or-repoint-the-dangling-test-citations-in-the-non-run.ipd.md`) row S-19: `plans.py` / module docstring / `tests/test_plan_status.py` / `19313eed` / RETIRE-UNGUARDED, noting `PlanStatusDriftGuard.test_every_plan_has_a_recognized_status` scanned live plans and `rg -n "DIR_TERMINAL" tests/` returned empty.
- The deleted module (`git show 19313eed7^:tests/test_plan_status.py`) held `test_every_plan_has_a_recognized_status`, `test_terminal_status_matches_directory` and `test_auto_approved_is_recognized_and_pre_terminal`; the first two are the model for E-01/E-02, the third is replaced by a `normalize_status` outcome test.
- Current coverage: `tests/test_plans_board.py` exercises `normalize_status`/`scan` on synthetic `.agents/plans` fixtures but asserts nothing about the live repository tree; no live test asserts terminal status/directory agreement.
- Measured during authoring: applying the deleted test's logic to the current tree reported 0 unrecognized and 0 mismatched across all plan files, so the restored live tests are expected to pass on landing.
- `DECISIONS.md` (D52 follow-on) still cites `tests/test_plan_status.py` as the drift guard; recreating the module at that path makes that historical citation live again without editing DECISIONS.

## Proposed changes (ordered, validatable)

1. E-01: recreate `tests/test_plan_status.py` with the `status_drift` checker and synthetic-tree tests.
2. E-02: add `livecorpus` live-tree tests and the `auto-approved` normalizer test.
3. E-03: docstring-only update in `agent_workflows/plans.py`.

## Deferred / out of scope (with reason)

- Any change to `plans.py` behavior or the status vocabulary: this is a coverage-restoration chore.
  - Carrier-Declined: deliberate non-goal (coverage restoration only), not an outstanding obligation.
- Restoring other site rows of `ev7t1w`: each has its own backlog item; backlog `7h2he0` names only S-19.
  - Carrier-Declined: owned by the per-site backlog items filed from `ev7t1w`, not by this plan.
- Editing `DECISIONS.md`: it is a historical decision record, and its citation becomes accurate again once the module exists.
  - Carrier-Declined: no obligation remains; recreating the module at the cited path discharges the stale citation.

## Scope check

- Over-scope: none. The only production edit is a docstring that would otherwise become false.
- Under-scope: none. Both properties of the deleted guard (recognized token, terminal/directory agreement) are restored on the live tree, and their detection is proven on synthetic trees in the default suite.

## Required tests / validation

- `python3 -m pytest -o addopts="" -v tests/test_plan_status.py` (all tests including `livecorpus`) passes (V-01, V-02).
- Non-vacuity: synthetic drift cases, including a sharded terminal plan, are reported (V-01), and a temporary `- Status: aproved` edit to a copy of a live pending plan in a temp tree is reported (V-02); the live repository tree is never edited.
- Full bare suite `python3 -m pytest` passes with no new failures (V-03).

## Spec / documentation sync

N/A: no spec or user-facing documentation describes this test; the only text change is the `plans.py` module docstring in E-03.

## Open questions

### OQ-01: Should the live-tree tests run in the default suite or be marked `livecorpus`?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: marked `livecorpus`. The `pyproject.toml` marker description states that tests asserting a property over every artifact in this repo's own `.aw/records/` tree are deselected by default because one red such test blocks integration for every concurrent runner lane (measured 2026-09-19). The detection logic itself is covered in the default suite by the synthetic-tree tests of E-01, so the default run still guards the checker.

### OQ-02: New module name or recreate the deleted path?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: recreate `tests/test_plan_status.py`, because `DECISIONS.md` and the `plans.py` docstring already cite that path as the drift guard, so restoring it makes both references accurate.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v tests/test_plan_status.py -m "not livecorpus"` showing each synthetic-tree behavior (clean tree, unrecognized token, missing status, terminal mismatch, pending not mismatched, sharded terminal mismatch, examined count) PASSED; plus pasted output of `rg -n "import inspect|from inspect|import ast|getsource|agent_workflows/plans\.py.*read_text|__file__" tests/test_plan_status.py` showing no source-reading match.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v tests/test_plan_status.py -m "not livecorpus"
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2746636712
    rootdir: <repo>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items / 2 deselected / 8 selected

    tests/test_plan_status.py::TestSyntheticPlanStatus::test_clean_tree PASSED [ 12%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_examined_count_excludes_readme PASSED [ 25%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_terminal_mismatch PASSED [ 37%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_unrecognized_token PASSED [ 50%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_sharded_terminal_mismatch PASSED [ 62%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_pending_not_mismatched PASSED [ 75%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_auto_approved_normalization PASSED [ 87%]
    tests/test_plan_status.py::TestSyntheticPlanStatus::test_missing_status PASSED [100%]

    NOTE: 2 tests were deselected by -m/-k and did not run (this run's marker filter skips 'livecorpus'); run everything with: make test-all
    ======================= 8 passed, 2 deselected in 0.22s ========================

    $ rg -n "import inspect|from inspect|import ast|getsource|agent_workflows/plans\.py.*read_text|__file__" tests/test_plan_status.py
    (no matches, exit code 1)
    ```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: pasted output of `python3 -m pytest -o addopts="" -v -m livecorpus tests/test_plan_status.py` showing both live-tree tests PASSED, plus the auto-approved test PASSED in a default-marker run; AND pasted output of a throwaway check (a temp tree containing a copy of one live pending plan with its status line edited to `- Status: aproved`, passed to `status_drift`) showing that file reported in `unrecognized`.
  - Observed evidence:
    ```
    $ python3 -m pytest -o addopts="" -v -m livecorpus tests/test_plan_status.py
    ============================= test session starts ==============================
    platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
    cachedir: .pytest_cache
    Using --randomly-seed=2864422293
    rootdir: <repo>
    configfile: pyproject.toml
    plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
    collecting ... collected 10 items / 8 deselected / 2 selected

    tests/test_plan_status.py::PlanStatusDriftGuard::test_repository_terminal_plan_status_matches_directory PASSED [ 50%]
    tests/test_plan_status.py::PlanStatusDriftGuard::test_every_repository_plan_has_a_recognized_status PASSED [100%]

    NOTE: 8 tests were deselected by -m/-k and did not run (filtered by marker expression: 'livecorpus')
    ======================= 2 passed, 8 deselected in 0.61s ========================

    $ python3 -m pytest tests/test_plan_status.py -k test_auto_approved_normalization
    bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...bringing up nodes...
    .                                                                        [100%]
    NOTE: 9 tests were deselected by -m/-k and did not run (this run's marker filter skips 'slow' and 'livecorpus', and -k/--deselect also contributed); run everything with: make test-all
    1 passed in 1.49s

    $ python3 -c "import tempfile, re; from pathlib import Path; from tests import support; from tests.test_plan_status import status_drift; ... "
    Examined: 1
    Unrecognized: ['pending/20261015-cleantgt-06-xoy5yg-make-uninstall-remove-clean-target-home-trees-keeping-record.ipd.md: Status=legacy/unknown']
    Mismatched: []
    ```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: pasted `git diff agent_workflows/plans.py` showing only docstring lines changed and naming `tests/test_plan_status.py` as the live guard; AND the pasted summary line of a bare `python3 -m pytest` run with no new failures.
  - Observed evidence:
    ```diff
    $ git diff agent_workflows/plans.py
    diff --git a/agent_workflows/plans.py b/agent_workflows/plans.py
    index 222648435..f9ab91914 100644
    --- a/agent_workflows/plans.py
    +++ b/agent_workflows/plans.py
    @@ -1,9 +1,9 @@
     """Scan plan/prompt lifecycle files and read their readiness ``Status:`` (DECISIONS D52/Dnn).

     This is the single source of truth for the plan readiness vocabulary and the legacy mapping. It is
    -shared by the ``aw plans`` board (``cli.py``) and the former repo drift-guard test
    -(``tests/test_plan_status.py`` was deleted in ``19313eed``; no live guard currently asserts this
    -drift check directly), so the two can never diverge.
    +shared by the ``aw plans`` board (``cli.py``) and the repository drift-guard test
    +(``tests/test_plan_status.py``, with live-corpus tests marked ``livecorpus``), so the two can
    +never diverge.

     Directories carry DISPOSITION (pending/executed/superseded/not-executed/reusable; ``done`` is an
     accepted alias for ``executed``). The front-matter ``- Status:`` line carries READINESS. See D52 and
    ```
    Bare `python3 -m pytest` run summary:
    ```
    705 passed in 28.04s
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`aw ipd set approved sat4he --by-human`); OQ-01 and OQ-02 are resolved and no question blocks. Begin with `aw ipd begin sat4he`.

Scope fence: `- Scope-Paths:` is a DECLARATION, not a stop condition; an edit outside it is made and justified at finalize with `--scope-reason <path>=<why>`. STOP only for a genuinely unsafe condition: a concurrent edit to `agent_workflows/plans.py` that cannot be safely combined, or a live-tree test going red on landing (a real drift in a plan this plan does not own; report it rather than editing that plan).

Honesty: you MUST paste the ACTUAL output of every command and test in each `V-*`; never claim a result you did not run. The V-02 throwaway check runs only on a temp copy and is never committed.

Commits: commit only the Scope-Paths files you changed through `aw commit sat4he -- <paths>`; never `git add -A`, never push, never tag. Verify the staged set with `git diff --cached --name-only` before committing.

Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize; when executed by hand, run `aw ipd finalize sat4he` only after every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms. Never hand-edit `- Status:` or hand-roll a `git mv` into `executed/`.
