# IPD: Declare the execution role in the undeclared lifecycle test classes (test_ipd_lifecycle_cli.py and test_orchestrator_retirement.py)

- Date: 2026-09-26
- Kind: child
- Concern: `tests/test_ipd_lifecycle_cli.py` has 11 `TestCase` classes and only `BeginCliTests` declares its execution role (`support.declare_execution_role(self)` first in `setUp`). The other ten inherit the ambient `AW_EXECUTION_ROLE`. The root `conftest.py` pops that variable at import, which masks the defect under pytest, but any process that re-asserts `AW_EXECUTION_ROLE=worker` after conftest (a runner lane turn whose environment is re-applied, a plugin, an in-test leak) turns lifecycle tests red with `AW-LIFECYCLE-ROLE-001`. Measured at review HEAD `de9b241c` with a throwaway plugin re-asserting the marker in `pytest_runtest_setup`: `22 failed, 16 passed`. THE SCRUB IS NOT THE ONLY MASK, AND `make test-serial` IS NOT MASKED AT ALL (review F-5): the scrub lives in the pytest root `conftest.py`, which `python3 -m unittest` never loads, so the repository's own documented serial fallback (`Makefile` target `test-serial`, `python3 -m unittest discover -s tests -t .`) is red TODAY on any shell exporting the marker, with no plugin involved. Measured: `AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli` -> `Ran 38 tests ... FAILED (failures=27)` (27 failure records over the same 22 distinct test methods, since a `subTest` reports per sub-case). The conftest comment explaining all of this cites a deleted test file and a stale count.
- Scope: IN: declare the role first in `setUp` of the ten undeclared classes of `tests/test_ipd_lifecycle_cli.py` (adding a `setUp` to the one that has none); declare it once in `tests/test_orchestrator_retirement.py`'s shared `RollupTransitionCase.setUp`, which review measured as the ONE remaining suite-wide failure of exactly this defect class (review F-6); correct the stale `conftest.py` comment. OUT: a permanent guard test (maintainer declined structural guards); any OTHER test file, and any change to an assertion body in either declared test file.
- Scope-Paths: tests/test_ipd_lifecycle_cli.py, tests/test_orchestrator_retirement.py, conftest.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: high
- From-Backlog: owi0no
- Blocks-Release: next
- Set: testhyg
- Order: 1
- Highest E allocated: 04
- Author: opencode/its_direct/pt3-claude-opus-5.5-1m-us
- Id: yx9xsa

## Workflow history
- 2026-09-27 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: yx9xsa verified (set testhyg, attempt 1).
- 2026-09-27 approved (aw set): status set to approved
- 2026-09-27 reviewed (opencode/its_direct/pt3-claude-opus-5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-901..PR-908; added tests/test_orchestrator_retirement.py (one base-class declaration closing the suite's only other instance) and the unittest/test-serial verification path; corrected a third dead reference in the conftest comment
- 2026-09-26 to-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): Graduated from backlog owi0no: declare the execution role in the ten undeclared classes of test_ipd_lifecycle_cli.py; re-measured 22 failures under a re-asserted worker marker at HEAD 61ef21d8.

- 2026-09-26 draft (opencode/its_direct/pt3-claude-opus-5.5-1m-us): created.

## Goal

Every test in `tests/test_ipd_lifecycle_cli.py` and `tests/test_orchestrator_retirement.py` measures the same behavior whether or not the ambient process carries `AW_EXECUTION_ROLE=worker`, under BOTH runners the repository documents (`python3 -m pytest` and `make test-serial`).

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces.

### Task group 1: declare, correct, verify

- [x] E-01 In `tests/test_ipd_lifecycle_cli.py`, make `support.declare_execution_role(self)` the FIRST statement of `setUp` in each of: `BeginHappyPathTests`, `BeginFailClosedTests`, `FinalizeTests`, `ReconciliationTests`, `AdditiveScopeWideningTests`, `RollbackFailureSemanticsTests`, `TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout`, `DelegationAndBypassRemovalTests`, `ParenthesizedActorIsRefusedBeforeAnyWrite`. `ScaffoldStopsWritingTheShapeItsOwnSetterRefuses` has no `setUp`; add `def setUp(self) -> None: support.declare_execution_role(self)`. `support` is already imported (`from tests import support`). Every one of the 11 classes subclasses `unittest.TestCase` DIRECTLY, so no `super().setUp()` chain is involved and there is no inheritance hazard; the authored grep for it is retained only as a cheap re-confirmation at execution time (`grep -n "super().setUp" tests/test_ipd_lifecycle_cli.py` returns nothing today). No other change to any test body.
  - Depends on: none
  - Expected outcome: all 11 classes declare the coordinator role. Re-derive the class count at execution time (`grep -c "^class .*unittest.TestCase" tests/test_ipd_lifecycle_cli.py`) rather than trusting the 11 measured at review, and make the declaration count EQUAL it; 11 is context, not the bar.
  - Execution state: performed

- [x] E-02 In `tests/test_orchestrator_retirement.py`, make `support.declare_execution_role(self)` the first statement of the SHARED base class `RollupTransitionCase.setUp` (add `from tests import support` beside that method's existing local `from agent_workflows import ipd_lifecycle as LC` import, or at module level beside the existing `from tests.support import REPO_ROOT`). ONE declaration on the base class covers all 15 subclasses; do not add a per-subclass `setUp`. WHY THIS FILE AND ONLY THIS FILE: review ran the re-assert probe over the WHOLE suite and found exactly one failing test outside `test_ipd_lifecycle_cli.py`, in this file (`TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence`, which drives `LC.finalize` on the ambient environment and gets `AW-LIFECYCLE-ROLE-001` (exit 2) where it asserts `EXIT_FINDINGS` (1)). DO NOT WEAKEN `TheWorkerRoleIsRefused`: its whole point is refusal, and it is safe precisely because it passes an EXPLICIT `env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER}` rather than reading the ambient value, so a coordinator declaration on the base class cannot make it vacuous; review measured the whole file `42 passed` under the probe with the base-class declaration in place. No assertion body in this file may change.
  - Depends on: none
  - Expected outcome: `tests/test_orchestrator_retirement.py` is ambient-role independent with ONE added declaration, and `TheWorkerRoleIsRefused` still asserts the refusal from its own explicit env.
  - Execution state: performed

- [x] E-03 Rewrite the `HONEST LIMITS` and `CROSS-REFERENCE` paragraphs of the `conftest.py` comment block above `os.environ.pop("AW_EXECUTION_ROLE", None)`: remove both references to `tests/test_role_declaration_guard.py` (deleted; `git ls-files tests/test_role_declaration_guard.py` is empty) and the claim that 42 tests in `tests/test_ipd_lifecycle_cli.py` still inherit the ambient role; state instead that tests which drive lifecycle wrappers declare their role with `support.declare_execution_role`, and that re-asserting the marker with a throwaway `pytest_runtest_setup` plugin is how to check a file (as plan yx9xsa did). ALSO FIX THE THIRD DEAD REFERENCE THE AUTHORED ITEM WOULD HAVE LEFT BEHIND (review F-4): the `WHY NOT RELAX THE GUARD TEST` paragraph cites `tests/test_worker_role_refusal.py`, which the same trim `19313eed` deleted, and the `HONEST LIMITS` paragraph names `test_driver_own_process_is_not_worker_role`, a test that exists NOWHERE in the tree (`grep -rn "def test_driver_own_process_is_not_worker_role" --include=*.py .` returns nothing). So do NOT "keep the paragraph about `test_driver_own_process_is_not_worker_role` minus its dead cross-reference": that paragraph's SUBJECT is gone, and keeping it would leave the comment asserting a live guard the repository no longer has. Replace it with what is TRUE: the scrub's invariance is not asserted by any shipped test today (the guard file that did so was deleted), which is why a one-off re-assert probe is the check. Add ONE sentence recording that the scrub is pytest-only, so `make test-serial` (`python3 -m unittest`) never loads this file and is protected only by the per-class declarations. Also remove the parenthetical "re-measured at IPD `8i0xa7`: 42 tests ... see backlog `owi0no`" in the WHAT WENT WRONG paragraph, or reword it to say the gap was closed by plan yx9xsa. Write no em or en dashes (this is an internal code comment, so the rule is a repository style preference here, not the user-facing-prose MUST).
  - Depends on: E-01, E-02
  - Expected outcome: the comment cites no deleted file and no nonexistent test, carries no stale count, and states the pytest-only limit of the scrub.
  - Execution state: performed

- [x] E-04 Verify under BOTH runners, with the probe plugin written INSIDE the workspace. Write `reassert_worker.py` to a workspace-local path (`.aw/state/roleplug/` is gitignored and is the path executed plan `6vozur` used after its review found the hardcoded `/tmp/opencode/roleplug` unwritable from an isolated lane; review PR-703 on `6vozur` records that finding, and this review hit the same refusal). Content: `@pytest.hookimpl(trylast=True) def pytest_runtest_setup(item): os.environ["AW_EXECUTION_ROLE"] = "worker"` (trylast so it runs after conftest's import-time pop and before each test body; `setUp` then runs inside the test call and the declaration overrides it). (a) PYTEST, per file, BEFORE and AFTER: `PYTHONPATH=.aw/state/roleplug python3 -m pytest tests/test_ipd_lifecycle_cli.py tests/test_orchestrator_retirement.py -p reassert_worker -o addopts="-q -n auto"`. (b) PYTEST, WHOLE SUITE under the probe, which is what proves no OTHER file carries this defect and no declaration leaked: `PYTHONPATH=.aw/state/roleplug python3 -m pytest -p reassert_worker`. (c) UNITTEST, which needs no plugin because `conftest.py` is never loaded: `AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli` before and after. Then run the bare suite. DO NOT SUBSTITUTE `AW_EXECUTION_ROLE=worker python3 -m pytest` for the plugin: the scrub makes that spelling report green against the UNFIXED tree, a false pass measured on this repository before (`6vozur` F-7). Do not commit the plugin.
  - Depends on: E-01, E-02, E-03
  - Expected outcome: state the PROPERTY, then the review numbers as context. Property: under the probe, every previously failing test passes and the suite's failure count for this defect class reaches zero; under `unittest` with the marker exported, the lifecycle file is `OK`. Context measured at review HEAD `de9b241c`, to be re-derived rather than asserted: two-file pytest probe before `23 failed` (22 in the lifecycle file, 1 in the retirement file), after `38 passed` + `42 passed`; whole-suite probe before `23 failed, 2575 passed, 2 skipped`, after zero failures attributable to the role; `unittest` before `Ran 38 tests ... FAILED (failures=27)`, after `Ran 38 tests ... OK`. If the AFTER suite carries any failure, report it rather than attributing it to the role.
  - Execution state: performed

## Project conventions discovered (Step 0)

- `support.declare_execution_role(case, role=None)` enters the declaration immediately and unwinds via `addCleanup`, so it cannot leak into the next test on the same xdist worker (its docstring).
- Maintainer rule: no permanent structural guard tests; tests assert outcomes only. This plan adds no test; it corrects fixtures, and the verification is a one-off probe.
- Cite code by SYMBOL (`module.function`) or by a quoted content string, with a line number only appended to one of those and never alone: an offset expires before this plan executes (spec `ipd-structure-and-linting` Section 10.2; advisory `IPD-C801`).
- ADDED AT REVIEW. The scrub is PYTEST-ONLY: `os.environ.pop("AW_EXECUTION_ROLE", None)` lives in the repository-root `conftest.py`, which `python3 -m unittest` never imports. So the declaration is not defence in depth for the serial runner the `Makefile` ships (`test-serial`: `python3 -m unittest discover -s tests -t .`); it is the ONLY protection there, and the file is red today under an exported marker with no plugin at all.
- ADDED AT REVIEW. A declaration on a shared BASE class is the right unit when one exists: `tests/test_orchestrator_retirement.py`'s `RollupTransitionCase` is the `setUp` for 15 subclasses, so one line covers them all, whereas `tests/test_ipd_lifecycle_cli.py`'s 11 classes each subclass `unittest.TestCase` directly and each needs its own.
- ADDED AT REVIEW. A coordinator declaration does NOT weaken a refusal test that passes its role EXPLICITLY. `tests/test_orchestrator_retirement.py`'s `TheWorkerRoleIsRefused` drives `retire(..., env={LC.EXECUTION_ROLE_ENV: LC.ROLE_WORKER})`, which is the shape `tests/support.py`'s `worker_role` docstring prescribes precisely so a refusal test cannot pass vacuously off an ambient value.
- ADDED AT REVIEW. Write a throwaway probe plugin INSIDE the workspace, not to a machine-local `/tmp` path: executed plan `6vozur` hit exactly that refusal from an isolated lane (its review PR-703) and relocated to `.aw/state/roleplug/`, which `.aw/.gitignore` already ignores (`/state/`).

## Findings

F-1 to F-4 measured at authoring HEAD `61ef21d8`; F-5 to F-8 added at review and measured at review HEAD `de9b241c` (note `61ef21d8` is NOT an ancestor of the review HEAD, and one commit since, `7bed5478`, added a test to `RollbackFailureSemanticsTests`, which is why the file's collected count is 38 and not the 37 the authored plan expected).

| Id | Severity | Location | Finding | Evidence |
| --- | --- | --- | --- | --- |
| F-1 | HIGH | `tests/test_ipd_lifecycle_cli.py` | 10 of 11 classes do not declare their role; under a re-asserted worker marker 22 tests fail: FinalizeTests 5, RollbackFailureSemanticsTests 4, TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout 4, ReconciliationTests 3, AdditiveScopeWideningTests 3, DelegationAndBypassRemovalTests 2, ParenthesizedActorIsRefusedBeforeAnyWrite 1. CONFIRMED AT REVIEW, per-class counts identical. | authoring: `22 failed, 15 passed in 6.49s`; review at `de9b241c`: `PYTHONPATH=<workspace>/roleplug python3 -m pytest tests/test_ipd_lifecycle_cli.py -p reassert_worker -o addopts="-q -n auto"` -> `22 failed, 16 passed in 4.58s` |
| F-2 | INFO | BeginHappyPathTests, BeginFailClosedTests, ScaffoldStops... | These three pass under the probe today but are declared anyway so the file has one rule and a future edit cannot silently start inheriting. | same run: no failures in those classes |
| F-3 | LOW | `conftest.py` comment | Cites the deleted `tests/test_role_declaration_guard.py` twice and a count of 42. | `git ls-files tests/test_role_declaration_guard.py` -> empty |
| F-4 | INFO | backlog owi0no body | Says 42 tests fail; measured 22 at HEAD. The brief's 22 is correct. | F-1 |
| F-5 | HIGH | `Makefile` target `test-serial`; `conftest.py` scrub | **THE DEFECT IS LIVE TODAY UNDER `make test-serial`, WITH NO PLUGIN.** The authored Concern framed the scrub as the general mask and the plugin as the only way to observe the failure. `conftest.py` is a PYTEST conftest, so `python3 -m unittest` never loads it and never scrubs; the repository's documented serial fallback is therefore red on any shell exporting the marker, which is the ordinary condition inside a runner lane turn. This raises the plan's value and changes its verification (a pytest-only check cannot see this). | `AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli` -> `Ran 38 tests in 3.619s` / `FAILED (failures=27)` with `AW-LIFECYCLE-ROLE-001` in the assertion messages; the same command with `env -u AW_EXECUTION_ROLE` -> `Ran 38 tests ... OK`. `Makefile` `test-serial:` runs `python3 -m unittest discover -s tests -t .` |
| F-6 | HIGH | `tests/test_orchestrator_retirement.py`, `TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence` | **ONE MORE TEST IN THE SUITE CARRIES THE SAME DEFECT, AND THE AUTHORED SCOPE WOULD HAVE LEFT IT.** Review ran the probe over the WHOLE suite rather than the one file. Exactly one failure lies outside `test_ipd_lifecycle_cli.py`: this test drives `LC.finalize` on the ambient env and receives the role refusal (exit 2) where it asserts `EXIT_FINDINGS` (1). It is the same fix, one line on a shared base class, and leaving it means the plan's own verification cannot report a clean suite under the probe, which is the evidence that proves no other file inherits. | `PYTHONPATH=<workspace>/roleplug python3 -m pytest -p reassert_worker` -> `23 failed, 2575 passed, 2 skipped, 3 warnings in 37.82s`; the 23rd is that test, failing `AssertionError: 2 != 1 : AW-LIFECYCLE-ROLE-001: ...`. With `support.declare_execution_role(self)` added to `RollupTransitionCase.setUp`: `tests/test_orchestrator_retirement.py` -> `42 passed in 5.55s` under the same probe, `TheWorkerRoleIsRefused` included |
| F-7 | MEDIUM | E-04 as authored (was E-03) | The probe recipe hardcoded `/tmp/opencode/roleplug`, a machine-local path outside the executing workspace. Executed plan `6vozur` already measured that an isolated lane may be refused that path and relocated its plugin to `.aw/state/roleplug/`; this review was refused the same path by its own tooling. | `6vozur` E-05 text ("NOT the hardcoded `/tmp/opencode/roleplug` the authoring session used ... an isolated lane may not be able to write it") and its V-05 evidence recording `Plugin path: .aw/state/roleplug/_aw_reassert_role.py (inside workspace)`; `.aw/.gitignore` ignores `/state/` |
| F-8 | MEDIUM | `conftest.py` comment, `WHY NOT RELAX THE GUARD TEST` and `HONEST LIMITS` paragraphs | **THE COMMENT HAS THREE DEAD REFERENCES, NOT TWO, AND THE AUTHORED E-ITEM WOULD HAVE PRESERVED THE WORST ONE.** Besides the two hits on `tests/test_role_declaration_guard.py` that F-3 names, the block also cites `tests/test_worker_role_refusal.py` (deleted by the same trim `19313eed`) and builds a whole paragraph on `test_driver_own_process_is_not_worker_role`, which exists NOWHERE in the tree. The authored item said to KEEP that paragraph "minus its dead cross-reference", which would leave shipped code asserting a live guard the repository does not have. | `git ls-files tests/test_worker_role_refusal.py tests/test_role_declaration_guard.py` -> empty for both; `git show 19313eed --name-only` lists both as deleted; `grep -rn "def test_driver_own_process_is_not_worker_role" --include=*.py .` -> nothing; `grep -n` on `conftest.py` shows the four citation lines |

## Proposed changes (ordered, validatable)

1. E-01: declare the role in the ten undeclared classes of `tests/test_ipd_lifecycle_cli.py`.
2. E-02: declare it once on `RollupTransitionCase` in `tests/test_orchestrator_retirement.py` (F-6).
3. E-03: correct the conftest comment, including the third dead reference (F-8).
4. E-04: probe under pytest per-file and suite-wide, and under `unittest` (F-5), with an in-workspace plugin (F-7); then the bare suite.

## Deferred / out of scope (with reason)

- A permanent guard test asserting every lifecycle test class declares its role: the maintainer declined structural guards (2026-09-26); the probe in E-04 is the one-off check. NOTED AT REVIEW, so the human can weigh the residual: with no shipped guard AND (per F-8) no surviving guard file, nothing prevents a future test class from silently inheriting the role again. That is a deliberate, maintainer-set cost, not an oversight; it is recorded here rather than argued.
  - Carrier-Declined: maintainer decision 2026-09-26, no structural guard tests.
- Restoring the deleted `tests/test_role_declaration_guard.py` (the harness that DID assert scrub invariance): out of scope and left undone. It is a 222-line file with its own restoration decision, already recorded as `6vozur` F-8 and its review PR-704; this plan only stops `conftest.py` claiming it exists.
  - Carrier-Declined: already recorded on executed plan `6vozur` (F-8) as a separate file's restoration decision; filing a second carrier would duplicate it.

## Scope check

- Over-scope: none. F-2's three classes are included because the brief and the item scope all ten undeclared classes. `tests/test_orchestrator_retirement.py` is NOT over-scope: it is one line closing the one remaining instance of the same defect, measured by this plan's own suite-wide verification, and without it E-04's suite-wide probe cannot report clean.
- Under-scope: closed at review on two counts. (1) `tests/test_orchestrator_retirement.py` was missing (F-6). (2) Verification was pytest-only and therefore blind to the `unittest` path where the defect is live with no plugin (F-5).
- Explicitly NOT touched, named so reconciliation has something to check: any assertion body in either test file; `tests/support.py`; `TheWorkerRoleIsRefused`'s explicit `env=` (weakening it would make a refusal test vacuous, which is the failure mode `tests/support.py`'s `worker_role` docstring exists to prevent).
- CONCURRENCY NOTE: `conftest.py` is also declared by pending plan `a6xbso` (`- Status: reviewed`), which adds a two-line scrub beside this role pop and whose review recorded this same stale cross-reference as its F-12 with an explicit "not ours to fix". The two edits are in the same comment region. Whichever runs second must REBASE its edit onto the other rather than overwriting; if the comment block has already been corrected when this plan executes, record that as the outcome for E-03 rather than re-writing it.

## Required tests / validation

- The E-04 probes (pytest per-file, pytest suite-wide, and `unittest`) before and after, plus the bare suite. No new test is added (fixture correction only; outcome rule respected).
- HONEST LIMIT ON THE BARE SUITE: a bare `python3 -m pytest` is green BEFORE this plan and after, because `conftest.py` scrubs the marker. It is a no-regression check ONLY and is not evidence the fix works. The load-bearing evidence is the probe pair and the `unittest` pair.

## Spec / documentation sync

N/A: test fixtures and a code comment only. No `.spec.md` is in `- Scope-Paths:`. Considered and declined at review: documenting in `CONTRIBUTING.md` that `make test-serial` does not load `conftest.py`, which is a real documentation gap but belongs to the `test-serial` documentation and not to a fixture-correction plan; the fact is recorded in the `conftest.py` comment by E-03 instead, beside the scrub it describes.

## Open questions

### OQ-01: Should the plugin use `pytest_runtest_setup` or `pytest_configure`?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: `pytest_runtest_setup` with `trylast=True`, measured: it reproduces exactly the 22 failures, and it re-asserts before every test, which is the strongest ambient condition the declaration must survive. `pytest_configure` sets it once and a test's cleanup could clear it for later tests on the worker. RE-CONFIRMED AT REVIEW by re-measuring the `pytest_runtest_setup` shape at `de9b241c` (`22 failed, 16 passed`), and noting that the deleted guard file's canonical `_REASSERT_PLUGIN` used `pytest_configure`, so the two shapes are both attested in this repository and this plan's choice is the stricter one.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark.

- [x] V-01 validates E-01
  - Required evidence: paste the diff of `tests/test_ipd_lifecycle_cli.py`. Paste BOTH counts from the same tree and state that they are EQUAL: `grep -c "support.declare_execution_role(self)" tests/test_ipd_lifecycle_cli.py` and `grep -c "^class .*unittest.TestCase" tests/test_ipd_lifecycle_cli.py` (both were 11 at review; if the class count has moved, the declaration count must move with it and the equality is the bar, not the number). Paste `grep -n "super().setUp" tests/test_ipd_lifecycle_cli.py` showing no hit, so no class reaches `setUp` through a chain that skips the declaration. The diff must show ONLY added declaration lines and the one added `setUp`; an assertion body change is a failed validation.
  - Observed evidence: PASS. Diff of tests/test_ipd_lifecycle_cli.py shows only role declarations and added setUp; 11 == 11 classes/declarations; super().setUp empty.
```diff
diff --git a/tests/test_ipd_lifecycle_cli.py b/tests/test_ipd_lifecycle_cli.py
index c7c05f06..e9e9251f 100644
--- a/tests/test_ipd_lifecycle_cli.py
+++ b/tests/test_ipd_lifecycle_cli.py
@@ -88,6 +88,7 @@ def _write_plan(root: Path, text: str, name: str) -> Path:

 class BeginHappyPathTests(unittest.TestCase):
     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -188,6 +189,7 @@ class BeginHappyPathTests(unittest.TestCase):

 class BeginFailClosedTests(unittest.TestCase):
     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -346,6 +348,7 @@ class FinalizeTests(unittest.TestCase):
     """ipdgates Order v7e88a: the atomic terminal transaction with scope comparison + evidence."""

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -582,6 +585,7 @@ class ReconciliationTests(unittest.TestCase):
     """ipdgates Order qmt3yk: the finalize two-way scope reconciliation (surface + attribute)."""

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -769,6 +773,7 @@ class AdditiveScopeWideningTests(unittest.TestCase):
     """

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -1070,6 +1075,7 @@ class RollbackFailureSemanticsTests(unittest.TestCase):
     """ipdgates Order 3xh53a: crash-safe two-phase failure semantics for aw ipd finalize."""

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -1521,6 +1527,7 @@ class TheORDINARYFinalizeAlsoMutatesOffTheSharedCheckout(unittest.TestCase):
     """

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -1756,6 +1763,7 @@ class DelegationAndBypassRemovalTests(unittest.TestCase):
     """ipdgates Order wezhxg: `aw set executed <plan>` delegates into aw ipd finalize (no raw bypass)."""

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -1937,6 +1945,7 @@ class ParenthesizedActorIsRefusedBeforeAnyWrite(unittest.TestCase):
     GOOD = "opencode/its_direct/some-model"

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         self._tmp = tempfile.TemporaryDirectory()
         self.root = Path(self._tmp.name)
         _init_git(self.root)
@@ -2072,6 +2081,9 @@ class ScaffoldStopsWritingTheShapeItsOwnSetterRefuses(unittest.TestCase):
     BAD = "opencode (its_direct/some-model)"
     WANT = "opencode model=its_direct/some-model"

+    def setUp(self) -> None:
+        support.declare_execution_role(self)
+
     def test_author_normalization_and_contract_acceptance(self):
         from agent_workflows import attention_contract as AC
```

Counts verification:
```
$ grep -c "support.declare_execution_role(self)" tests/test_ipd_lifecycle_cli.py
11
$ grep -c "^class .*unittest.TestCase" tests/test_ipd_lifecycle_cli.py
11
```
Both counts are EQUAL (11 == 11).

Inheritance chain check:
```
$ grep -n "super().setUp" tests/test_ipd_lifecycle_cli.py
(none found, exit code 1)
```
Diff inspection confirms ONLY added declaration lines and the one added `setUp` method. No assertion bodies were modified.
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff of `tests/test_orchestrator_retirement.py`, which must be the ONE declaration (plus an import) on `RollupTransitionCase.setUp` and nothing else. Paste `PYTHONPATH=.aw/state/roleplug python3 -m pytest tests/test_orchestrator_retirement.py -p reassert_worker -o addopts="-q -n auto"` BEFORE (expected: 1 failure, `TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence`, with `AW-LIFECYCLE-ROLE-001` in the message) and AFTER (expected: 0 failed; review measured `42 passed`). Paste the AFTER run of `tests/test_orchestrator_retirement.py::TheWorkerRoleIsRefused` alone, passing, so the refusal test is proven not to have been made vacuous. A BEFORE run that shows no failure means the probe did not reach the tests: investigate rather than concluding the finding was wrong.
  - Observed evidence: PASS. RollupTransitionCase.setUp declares role; before probe 1 failed; after probe 42 passed; TheWorkerRoleIsRefused passed.
```diff
diff --git a/tests/test_orchestrator_retirement.py b/tests/test_orchestrator_retirement.py
index 894aae91..51744c7d 100644
--- a/tests/test_orchestrator_retirement.py
+++ b/tests/test_orchestrator_retirement.py
@@ -91,6 +91,7 @@ import unittest
 from pathlib import Path

 from agent_workflows import runner_shared as rs
+from tests import support
 from tests.support import REPO_ROOT

 # ==================================================================================================
@@ -2012,6 +2013,7 @@ class RollupTransitionCase(unittest.TestCase):
     """

     def setUp(self) -> None:
+        support.declare_execution_role(self)
         import tempfile as _tf

         from agent_workflows import ipd_lifecycle as LC
```

BEFORE probe run:
```
$ PYTHONPATH=.aw/state/roleplug python3 -m pytest tests/test_orchestrator_retirement.py -p reassert_worker -o addopts="-q -n auto"
..................................F.......                               [100%]
=================================== FAILURES ===================================
_ TheHumanFacingGateIsUNCHANGED.test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence _
...
AssertionError: 2 != 1 : AW-LIFECYCLE-ROLE-001: the runner owns begin/finalize for managed lanes; a worker-role process must not run them (refused: terminal finalize transaction). The runner performs begin/finalize for this lane from the coordinator role; report your result instead (write the outcome file the prompt names) and let the driver transition the plan.
=========================== short test summary info ============================
FAILED tests/test_orchestrator_retirement.py::TheHumanFacingGateIsUNCHANGED::test_the_ordinary_finalize_still_refuses_orchestrator_and_child_without_evidence
1 failed, 41 passed in 122.79s (0:02:02)
```

AFTER probe run:
```
$ PYTHONPATH=.aw/state/roleplug python3 -m pytest tests/test_orchestrator_retirement.py -p reassert_worker -o addopts="-q -n auto"
..........................................                               [100%]
42 passed in 124.41s (0:02:04)
```

AFTER run of `tests/test_orchestrator_retirement.py::TheWorkerRoleIsRefused` alone:
```
$ PYTHONPATH=.aw/state/roleplug python3 -m pytest tests/test_orchestrator_retirement.py::TheWorkerRoleIsRefused -p reassert_worker -o addopts="-q"
.                                                                        [100%]
1 passed in 0.23s
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the `conftest.py` diff. Paste `grep -n "test_role_declaration_guard\|test_worker_role_refusal\|test_driver_own_process_is_not_worker_role\|42 tests" conftest.py` returning NOTHING (all four, not just the two the authored item named). Paste the sentence that now records the pytest-only limit of the scrub. Confirm in words that the paragraph which previously described `test_driver_own_process_is_not_worker_role` no longer claims any shipped test asserts the scrub's invariance.
  - Observed evidence: PASS. Dead references removed from conftest.py; pytest-only scrub limitation documented; 0 grep hits.
```diff
diff --git a/conftest.py b/conftest.py
index 86ecbedb..f726f771 100644
--- a/conftest.py
+++ b/conftest.py
@@ -47,8 +47,8 @@ pytest_plugins = ["tests.deselect_notice"]
 # (`worker_role_active(os.environ)`, ipd_lifecycle.py:4105 and :4285), so every in-process
 # test that drives those CLI wrappers gets the worker refusal instead of the behavior it
 # asserts. Measured suite-wide: `31 failed, 8080 passed` with the marking present versus
-# `0 failed, 7993 passed` without it (re-measured at IPD `8i0xa7`: 42 tests in protected files
-# fail under the re-assert probe, because role declaration was incomplete; see backlog `owi0no`).
+# `0 failed, 7993 passed` without it (the gap where tests inherited the ambient role was
+# closed by plan yx9xsa).
 #
 # WHY IT MATTERS EVEN THOUGH IT CANNOT SHIP A BUG. The driver's own merge gate
 # (`oc_runipd.run_suite_check`) runs in the PRIMARY checkout inheriting the DRIVER's
@@ -69,25 +69,18 @@ pytest_plugins = ["tests.deselect_notice"]
 # individual fixture, and it makes a bare `python3 -m pytest` mean the same thing whether a
 # human or a runner turn typed it.
 #
-# WHY NOT RELAX THE GUARD TEST. `tests/test_worker_role_refusal.py` asserts that the
-# driver's own process is not worker-marked and is CORRECT as written; backlog `1uq1cu`
-# names relaxing it as the wrong fix. This scrub is what makes that assertion true again
-# inside a runner turn, rather than weakening it.
+# NO SHIPPED GUARD TEST. The scrub's invariance is not asserted by any shipped test today
+# (the guard file that did so was deleted), which is why a one-off re-assert probe is the
+# check.
 #
-# HONEST LIMITS, both deliberate. (1) A test that needs the marking must set it ITSELF, on
-# an explicit env dict passed to the code under test (or declare its role with
-# `support.declare_execution_role`). Note that `test_driver_own_process_is_not_worker_role`
-# is the one exception whose subject IS the ambient environment: because of this scrub,
-# that test cannot fail via ordinary shell export, but it remains falsifiable via a
-# `pytest_configure` re-assert plugin (see `tests/test_role_declaration_guard.py`).
-# Note also that compliance across the suite is incomplete (e.g. 42 tests in
-# `tests/test_ipd_lifecycle_cli.py` still inherit the ambient role, tracked in backlog
-# `owi0no`). (2) This scrubs the CURRENT process only; a subprocess a test spawns
-# inherits this already-cleaned environment, which is the intended propagation.
+# HONEST LIMITS, both deliberate. (1) Tests that drive lifecycle wrappers declare their
+# role with `support.declare_execution_role`, and a test that needs the worker marking sets
+# it on an explicit env dict passed to the code under test; re-asserting the marker with a
+# throwaway `pytest_runtest_setup` plugin is how to check a file (as plan yx9xsa did). The scrub
+# is pytest-only, so `make test-serial` (`python3 -m unittest`) never loads this file and is
+# protected only by the per-class declarations. (2) This scrubs the CURRENT process only;
+# a subprocess a test spawns inherits this already-cleaned environment, which is the
+# intended propagation.
 #
-# CROSS-REFERENCE: `tests/test_role_declaration_guard.py` asserts behavioral outcome
-# invariance under both roles across protected files by injecting a `pytest_configure`
-# plugin that re-asserts the marking after this scrub and before test collection.
 #
 # Done at import time, before any test module is collected, so no test can observe the
 # marked value. `pop` is unconditional and side-effect-free when the variable is absent,
```

Dead reference search in `conftest.py`:
```
$ grep -n "test_role_declaration_guard\|test_worker_role_refusal\|test_driver_own_process_is_not_worker_role\|42 tests" conftest.py
(returns exit code 1, nothing found)
```

Pytest-only scrub limitation sentence:
"The scrub is pytest-only, so `make test-serial` (`python3 -m unittest`) never loads this file and is protected only by the per-class declarations."

Confirmation:
The paragraph that previously discussed `test_driver_own_process_is_not_worker_role` and `test_worker_role_refusal.py` has been replaced by the `NO SHIPPED GUARD TEST` paragraph. It explicitly states that the scrub's invariance is not asserted by any shipped test today (the guard file that did so was deleted), and no longer claims that any shipped test asserts this property.
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: paste the plugin file content AND its path, which must be inside the workspace. Then paste six summary lines: (a) two-file pytest probe BEFORE (review measured `23 failed`) and AFTER (`0 failed`); (b) whole-suite pytest probe BEFORE (review measured `23 failed, 2575 passed, 2 skipped`) and AFTER, with zero failures attributable to the role and any residual failure named and explained rather than absorbed; (c) `AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli` BEFORE (review measured `FAILED (failures=27)`) and AFTER (`OK`). Finally paste the BARE `python3 -m pytest` summary showing 0 failed, labelled as a no-regression check and NOT as evidence the fix works. A run of `AW_EXECUTION_ROLE=worker python3 -m pytest` does NOT satisfy any part of this item; it is a measured false pass.
  - Observed evidence: PASS. Probe plugin at .aw/state/roleplug/reassert_worker.py; two-file probe 87 passed; whole-suite probe 2826 passed; unittest 45 passed OK; bare suite 2826 passed.
Probe plugin path: `.aw/state/roleplug/reassert_worker.py` (inside workspace).
Probe plugin content:
```python
import os
import pytest


@pytest.hookimpl(trylast=True)
def pytest_runtest_setup(item):
    os.environ["AW_EXECUTION_ROLE"] = "worker"
```

Summary lines:
(a) Two-file pytest probe (`tests/test_ipd_lifecycle_cli.py` and `tests/test_orchestrator_retirement.py`):
- BEFORE: `24 failed, 63 passed in 124.25s (0:02:04)`
- AFTER: `87 passed in 124.13s (0:02:04)`

(b) Whole-suite pytest probe (`PYTHONPATH=.aw/state/roleplug python3 -m pytest -p reassert_worker`):
- BEFORE: `24 failed, 2802 passed, 2 skipped, 3 warnings in 135.11s (0:02:15)`
- AFTER: `2826 passed, 2 skipped, 3 warnings in 147.94s (0:02:27)` (zero failures across the entire suite under probe)

(c) Unittest (`AW_EXECUTION_ROLE=worker python3 -m unittest tests.test_ipd_lifecycle_cli`):
- BEFORE: `Ran 45 tests in 5.221s` / `FAILED (failures=28)`
- AFTER: `Ran 45 tests in 8.415s` / `OK`

Bare `python3 -m pytest` summary (no-regression check only, not evidence of fix):
`2826 passed, 2 skipped, 3 warnings in 131.02s (0:02:11)`
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

This plan is `to-review` and requires explicit human approval before execution.

WHAT A HUMAN IS APPROVING. Eleven one-line fixture declarations in `tests/test_ipd_lifecycle_cli.py`, ONE more on a shared base class in `tests/test_orchestrator_retirement.py`, and a corrected comment block in `conftest.py`. No production code changes; no new test; no assertion body changed anywhere. What the fix buys, measured rather than asserted: 23 tests stop depending on the ambient `AW_EXECUTION_ROLE`, and `make test-serial` stops being red inside a runner lane (where the marker IS exported and where `conftest.py`'s scrub does not apply, because `unittest` never loads it).

Scope fence (a DECLARATION for reconciliation, not a stop directive): the three paths in `- Scope-Paths:`. Within `tests/test_ipd_lifecycle_cli.py`, only `setUp` bodies; within `tests/test_orchestrator_retirement.py`, only `RollupTransitionCase.setUp` and its import; within `conftest.py`, only the comment block above the role pop. Do not expand scope casually; if the work genuinely requires a file outside the fence, make the edit and JUSTIFY it in the two-way scope reconciliation at finalize (`--scope-reason` per out-of-scope path, `--scope-ack` per declared-but-unmodified path).

HONESTY RULE (hard MUST): every test claim pastes the ACTUAL runner output. Run the suite BARE as `python3 -m pytest`; do not add `-n0`, a second `-q`, or `-p no:randomly`. TWO SPELLINGS ARE SPECIFICALLY NOT ACCEPTED AS EVIDENCE, each a measured false pass. A green BARE suite proves nothing here, before or after, because the scrub hides the condition; it is a no-regression check only. And `AW_EXECUTION_ROLE=worker python3 -m pytest` reports green against the UNFIXED tree for the same reason (measured on this repository as `6vozur` F-7), so only a post-scrub re-assert plugin, or the `unittest` runner which loads no conftest, can observe the defect.

TWO STOP CONDITIONS, both of the genuinely-unsafe kind rather than scope questions. (1) If the probe's BEFORE run shows no failures, the probe is not reaching the tests; investigate the plugin rather than concluding the findings were wrong and skipping the work. (2) If `conftest.py`'s comment region has been changed under you by pending plan `a6xbso` (which also declares that file, is `- Status: reviewed`, and edits the same block), rebase your edit onto theirs and report it; do not overwrite a co-worker's change.

Commit ONLY paths in `- Scope-Paths:` through `aw commit yx9xsa -- <paths>` (never `git add -A`, never push); the probe plugin is written under gitignored `.aw/state/roleplug/` and is not committed. When every `V-*` carries real evidence and `aw ipd lint --phase pre-transition` conforms, perform the terminal transition with `aw ipd finalize`, never a raw `git mv`; the RUNNER owns it when it executes this plan in a lane (report your result and let the driver transition), and the executor otherwise performs it. Then set backlog item `owi0no` `done` with `--evidence` citing the executed plan; this plan carries its `- Blocks-Release: next`, so the gate is handed off here and needs no de-gating.
