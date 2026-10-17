# IPD: Restore behavioral test coverage for layout migration litter, grammar facets and storage companions

- Date: 2026-10-17
- Kind: child
- Concern: Backlog item `q86fxm` (Set `trimgap`, residual rollup of `b1mx2w` `## Filing plan` groups 16 through 60) carries 135 production keys the routine selection did not reach at baseline HEAD `86f0d88d` after suite trim `19313eed`. This child owns the migration and storage slice: group 26 (`layout_migration.py`, 3 keys: `is_stale_tool_litter` verdict `unguarded`, survivor `survived`, control `killed (newly_failing: 7)`; `_apply_grammar_facet` and `_grammar_facet_for` verdict `unguarded-unreached`) and group 23 (`storage.py`, 4 keys), 7 keys in all.
- Scope: Restore three deleted test modules from `19313eed^` at their original paths, unchanged except `core` markers on the cheapest tests that reach each key and a provenance docstring paragraph. The 7 keys: `layout_migration.is_stale_tool_litter`, `_apply_grammar_facet`, `_grammar_facet_for`; `storage.move_companion`, `get_git_commit_boundaries`, `load_local_attachment_record`, `reattach_companion`. EXCLUDES any production change; EXCLUDES other `layout_migration` keys these files reach (for example `MigrationManager.*`, carried by `lrnh5f`).
- Scope-Paths: tests/test_layout_migration.py, tests/test_awmigrename.py, tests/test_storage.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: chore
- Priority: low
- From-Backlog: q86fxm
- Set: trimgap
- Order: 20
- Highest E allocated: 03
- Author: opencode
- Id: 5e7czd

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 5e7czd verified (set trimgap, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001, PR-002, PR-003, PR-004, PR-005. Readiness go-pending-approval. Review record .aw/records/reviews/20261017-trimgap-20-5e7czd-restore-behavioral-test-coverage-for-layout-migration-litter.review.md

- 2026-10-17 to-review (opencode): authored from backlog `q86fxm`. Replayed the deleted files with `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26`, measured per-key reach via coverage contexts and per-test durations, and ran an early-return mutation sweep over the 7 keys; scratch edits reverted, `.coverage` removed.
- 2026-10-17 draft (opencode): created.

## Goal

Make the 7 keys reached by the routine bare core-tier run through restored behavioral tests that sweep stale-tool litter during migration, resolve and apply grammar facets, and attach, move and reattach storage companions, asserting on files moved or preserved and on returned records. Done means an early-return mutation of any of the 7 keys turns a routine test red.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

RESTORE RULE for every E-item: create the file from `git show 19313eed^:<path>`; add `import pytest` if absent; add `@pytest.mark.core` to exactly the tests named; add a docstring paragraph naming backlog `q86fxm`, findings `b1mx2w` and revision `19313eed^`; change nothing else. All three files build tmpdir repositories (their `Path(__file__)` uses resolve committed fixtures under `tests/fixtures/awphysical/` or a working directory for a CLI subprocess, which is input data, not source reading), so no test is dropped. If a test fails at execution HEAD, do not mark its E-item performed until it is dispositioned: record it in Findings and either update only that expectation for an intended change (cite the commit `git log -S` finds), or, for a regression, file a `bug` backlog item with `--blocks-release next` (`aw backlog new`, an out-of-scope path justified at finalize with `--scope-reason`) and mark that test `@pytest.mark.xfail(strict=True, reason="<bug id6>")`, then continue. All 71 tests passed at review (`71 passed in 7.69s`).

- [x] E-01 Restore `tests/test_layout_migration.py` (49 tests, 3.6 to 7.3s summed CPU) with `@pytest.mark.core` on `LeftoverDispositionTests.test_remove_preserves_untracked_ignored_local_lanes` and `StaleToolLitterSweepTests.test_cli_migrate_layout_noninteractive_yes_leaves_litter` (together 0.24 to 0.31s; they reach `is_stale_tool_litter`).
  - Depends on: none
  - Expected outcome: every restored test passes on an explicit-path run (49 at review); exactly these 2 tests selected by `-m core`.
  - Execution state: performed

- [x] E-02 Restore `tests/test_awmigrename.py` (9 tests, 1.2 to 1.9s) with `@pytest.mark.core` on `FacetResolutionTests.test_records_subtypes_map_to_facets`, `FacetResolutionTests.test_non_records_class_is_excluded` and `FacetResolutionTests.test_apply_facet_transform` (all near 0s; together 0.16s at review). `test_records_subtypes_map_to_facets` is REQUIRED: `test_non_records_class_is_excluded` only asserts `None` returns, so a `_grammar_facet_for` -> `None` mutant passes both of the other two (measured at review: `2 passed`; with the third test added: `1 failed, 2 passed`).
  - Depends on: none
  - Expected outcome: every restored test passes (9 at review); exactly these 3 tests selected by `-m core`.
  - Execution state: performed

- [x] E-03 Restore `tests/test_storage.py` (13 tests, 1.7 to 2.9s) with `@pytest.mark.core` on `CompanionAttachmentTests.test_e01`, `test_e03` and `test_e05` (together 0.23 to 0.65s; they reach all four storage keys).
  - Depends on: none
  - Expected outcome: every restored test passes (13 at review); exactly these 3 tests selected by `-m core`.
  - Execution state: performed

## Project conventions discovered (Step 0)

- TESTS MUST EXERCISE BEHAVIOR, NOT CODE STRUCTURE (`AGENTS.md`; `GUIDING_PRINCIPLES` P16): the restored tests assert on migrated trees, journals and returned records; none reads production source.
- THE ROUTINE GATE IS THE CORE TIER (`conftest.pytest_collection_modifyitems`, IPD `hguae9`, 30s budget, enforced on 12 or more CPUs). The three files cost about 6.5 to 12s summed CPU whole, so only the 8 cheapest key-killing tests join the core tier; explicit-path, `make test-all` and CI runs still run all 71.
- Cite code by SYMBOL with a line number only appended, never alone (spec `ipd-structure-and-linting` Section 10.2).

## Findings

| Id | Evidence | Finding |
|---|---|---|
| F-01 | `hpjj44` `## Derived properties` | `is_stale_tool_litter` -> `tests/test_layout_migration.py`; the two facet keys -> `tests/test_awmigrename.py`; the four storage keys -> `tests/test_storage.py`. |
| F-02 | `tools/deleted_test_replay.py 19313eed` at HEAD `f84c3af26` | All three `pass`: 49, 9 and 13 passed. |
| F-03 | Scratch restore, coverage contexts, `--junitxml` durations | Every key executes; the E-01..E-03 named tests are the minimum-cost set covering all 7 (greedy set cover over measured per-test durations). Review correction: reach is not kill. The author's set cover selected for EXECUTION, and its 7 tests executed every key, but under the named set `_grammar_facet_for` -> `None` survived (`2 passed`), because the only facet-resolution assertion among them expects `None`. E-02 adds `test_records_subtypes_map_to_facets` (8 tests in all). |
| F-04 | Early-return mutation sweep over the 7 keys, each reverted | All 7 killed by the WHOLE restored files, for example `_grammar_facet_for` -> `None`: 3 failed (all three in `test_awmigrename.py`, none of them among the originally named core tests); `move_companion` -> `None`: 1 failed (`test_e05`). Re-measured at review against the CORE-MARKED set only, by runtime monkeypatch of each function (no production file edited): `is_stale_tool_litter` -> False and -> True each 1 failed; `_apply_grammar_facet` -> input 1 failed; `move_companion`, `get_git_commit_boundaries`, `load_local_attachment_record`, `reattach_companion` -> `None` each 1 failed; `_grammar_facet_for` -> `None` 0 failed until the E-02 addition. The `b1mx2w` `unguarded` verdict for `is_stale_tool_litter` reflected the trimmed suite; restoring `tests/test_layout_migration.py` closes it. |

## Proposed changes (ordered, validatable)

1. E-01..E-03 restore the three modules with the named core markers.

## Deferred / out of scope (with reason)

none.

## Scope check

- Over-scope: none. Three test files; no production code.
- Under-scope: none for the 7 keys (F-03, F-04).

## Required tests / validation

- `python3 -m pytest <the three files> -o addopts="" -v` passes, per-test list pasted.
- `-m core --collect-only -q` over the three files lists exactly the 8 named tests.
- Reach: `-m core --cov=agent_workflows.layout_migration --cov=agent_workflows.storage --cov-report=term-missing`, each of the 7 keys executing.
- Mutation spot-checks (scratch, reverted), run against the core-marked tests only (`-m core` over the three files): `is_stale_tool_litter` return False, `_grammar_facet_for` return None, `_apply_grammar_facet` return its input path, `move_companion` return None, `get_git_commit_boundaries` return None, `load_local_attachment_record` return None, `reattach_companion` return None. Each must produce at least one failure. Note for `is_stale_tool_litter`: `agent_workflows/cli.py` imports it by name, so a mutation must be made in the source file (or patched in both modules); patching only `layout_migration` leaves the CLI path calling the original.
- Bare `python3 -m pytest` summary line; `aw sanitize --agent` no `fail`.

## Spec / documentation sync

N/A: tests only; no behavior, CLI surface or spec-described contract changes. No `.spec.md` is declared in Scope-Paths.

## Open questions

### OQ-01: Mark the three files whole, or per test?

- Blocking: no
- Status: resolved
- Owner: none
- Resolution or deferral rationale: per test. The bare core tier already ran 36 to 45s against its 30s budget on this host before any restore (measured three times at HEAD `f84c3af26`, `CORE TIER BUDGET EXCEEDED`), so adding about 10s of CPU would worsen a known overrun (backlog `o58dro`); the 8 named tests reach and kill every key for under 1.2s (7 at authoring; the eighth was added at review, F-03).

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste a diff against `19313eed^` showing only the import, two markers and docstring lines; paste the `-v` run listing every test PASSED (49 at review) and `-m core --collect-only -q` listing the 2 marked tests; paste the failure of the core-marked tests under a scratch `is_stale_tool_litter` return-False mutation (reverted).
  - Observed evidence:
    - Unified diff against `19313eed^:tests/test_layout_migration.py`:
      ```diff
      --- a/tests/test_layout_migration.py
      +++ b/tests/test_layout_migration.py
      @@ -1,4 +1,7 @@
      -"""Unit tests for layout migration, rollback, and conservative uninstall (IPD 20260809-awlayout-09)."""
      +"""Unit tests for layout migration, rollback, and conservative uninstall (IPD 20260809-awlayout-09).
      +
      +Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^.
      +"""

       from __future__ import annotations

      @@ -10,6 +13,8 @@ import tempfile
       import unittest
       from pathlib import Path

      +import pytest
      +
       from agent_workflows.layout_migration import (
           MigrationManager,
       )
      @@ -810,6 +815,7 @@ class LeftoverDispositionTests(unittest.TestCase):
               )
               return tx.get("leftover_disposition", {})

      +    @pytest.mark.core
           def test_remove_preserves_untracked_ignored_local_lanes(self):
               """The load-bearing case: `remove` must NOT delete the gitignored local lanes; they
               survive on disk and are reported in `preserved`, not `removed`."""
      @@ -1439,6 +1445,7 @@ class StaleToolLitterSweepTests(unittest.TestCase):
               self.assertFalse(pyc.exists(), "remove MUST sweep litter from disk")
               self.assertFalse(tools_dir.exists(), "remove MUST prune emptied tools dir")

      +    @pytest.mark.core
           def test_cli_migrate_layout_noninteractive_yes_leaves_litter(self):
               """E-03 & V-03: non-interactive migration with --yes leaves litter in place under default defer."""
               from unittest import mock
      ```
    - `-v` run over `tests/test_layout_migration.py`:
      ```
      ============================== 49 passed in 4.42s ==============================
      ```
    - `-m core --collect-only -q` over `tests/test_layout_migration.py`:
      ```
      tests/test_layout_migration.py::StaleToolLitterSweepTests::test_cli_migrate_layout_noninteractive_yes_leaves_litter
      tests/test_layout_migration.py::LeftoverDispositionTests::test_remove_preserves_untracked_ignored_local_lanes

      NOTE: 47 tests were deselected by -m/-k and did not run (filtered by marker expression: 'core')
      ============================== SLOW TESTS REPORT ===============================
      0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
      2/49 tests collected (47 deselected) in 0.35s
      ```
    - Failure under scratch `is_stale_tool_litter` return-False mutation (reverted):
      ```
      FAILED tests/test_layout_migration.py::StaleToolLitterSweepTests::test_cli_migrate_layout_noninteractive_yes_leaves_litter - AssertionError: False is not true : non-interactive --yes MUST leave tools dir in place
      ================== 1 failed, 1 passed, 47 deselected in 0.82s ==================
      ```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: paste the diff against `19313eed^` showing only the `import pytest` line (if added), three markers and docstring lines, the `-v` run listing every test PASSED (9 at review), `-m core --collect-only -q` listing the 3 marked tests, and the failures of those tests under scratch `_grammar_facet_for` return-None and `_apply_grammar_facet` return-input mutations (reverted).
  - Observed evidence:
    - Unified diff against `19313eed^:tests/test_awmigrename.py`:
      ```diff
      --- a/tests/test_awmigrename.py
      +++ b/tests/test_awmigrename.py
      @@ -10,6 +10,8 @@ Covers:
       - integration over a real HOME->REPOSITORY migration of seeded legacy `.agents/` records: with
         rename ON a plan/spec lands `.type.md` (riding the atomic move + journaled), with rename OFF it
         lands bare, and comms/research stay bare (E-03/E-04).
      +
      +Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^.
       """

       from __future__ import annotations
      @@ -22,6 +24,8 @@ import tempfile
       import unittest
       from pathlib import Path

      +import pytest
      +
       from agent_workflows.layout_migration import (
           MigrationManager,
           _apply_grammar_facet,
      @@ -32,6 +36,7 @@ from agent_workflows.project_schema import DeliveryMode, RecordsBackend


       class FacetResolutionTests(unittest.TestCase):
      +    @pytest.mark.core
           def test_records_subtypes_map_to_facets(self) -> None:
               self.assertEqual(
                   _grammar_facet_for("records/plans/pending/a.md", "records"), "ipd"
      @@ -59,11 +64,13 @@ class FacetResolutionTests(unittest.TestCase):
               )
               self.assertIsNone(_grammar_facet_for("records/research/x.md", "records"))

      +    @pytest.mark.core
           def test_non_records_class_is_excluded(self) -> None:
               self.assertIsNone(_grammar_facet_for("system/VERSION", "system"))
               self.assertIsNone(_grammar_facet_for("records/plans/x.md", "doc"))
               self.assertIsNone(_grammar_facet_for("config/config.json", "config"))

      +    @pytest.mark.core
           def test_apply_facet_transform(self) -> None:
               self.assertEqual(
                   _apply_grammar_facet(Path("/t/20260101-0001-01-a.md"), "ipd").name,
      ```
    - `-v` run over `tests/test_awmigrename.py`:
      ```
      ============================== 9 passed in 1.55s ===============================
      ```
    - `-m core --collect-only -q` over `tests/test_awmigrename.py`:
      ```
      tests/test_awmigrename.py::FacetResolutionTests::test_apply_facet_transform
      tests/test_awmigrename.py::FacetResolutionTests::test_non_records_class_is_excluded
      tests/test_awmigrename.py::FacetResolutionTests::test_records_subtypes_map_to_facets

      NOTE: 6 tests were deselected by -m/-k and did not run (filtered by marker expression: 'core')
      ============================== SLOW TESTS REPORT ===============================
      0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
      3/9 tests collected (6 deselected) in 0.30s
      ```
    - Failures under scratch mutations:
      `_grammar_facet_for` return None:
      ```
      FAILED tests/test_awmigrename.py::FacetResolutionTests::test_records_subtypes_map_to_facets - AssertionError: None != 'ipd'
      ================== 1 failed, 2 passed, 6 deselected in 0.28s ===================
      ```
      `_apply_grammar_facet` return input path:
      ```
      FAILED tests/test_awmigrename.py::FacetResolutionTests::test_apply_facet_transform - AssertionError: '20260101-0001-01-a.md' != '20260101-0001-01-a.ipd.md'
      ================== 1 failed, 2 passed, 6 deselected in 0.25s ===================
      ```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: paste the diff against `19313eed^` showing only the `import pytest` line (if added), three markers and docstring lines, the `-v` run listing every test PASSED (13 at review), `-m core --collect-only -q` listing the 3 marked tests, the failures of those tests under scratch `move_companion`, `get_git_commit_boundaries`, `load_local_attachment_record` and `reattach_companion` return-None mutations (reverted), the reach output from Required tests, the bare `python3 -m pytest` summary line, and a final empty `git diff agent_workflows/`.
  - Observed evidence:
    - Unified diff against `19313eed^:tests/test_storage.py`:
      ```diff
      --- a/tests/test_storage.py
      +++ b/tests/test_storage.py
      @@ -1,4 +1,7 @@
      -"""Unit tests for AW records storage backends, safety boundaries, and durability reporting (IPD 20260809-awlayout-03)."""
      +"""Unit tests for AW records storage backends, safety boundaries, and durability reporting (IPD 20260809-awlayout-03).
      +
      +Restored for backlog q86fxm from findings b1mx2w and source revision 19313eed^.
      +"""

       from __future__ import annotations

      @@ -11,6 +14,8 @@ import unittest
       from pathlib import Path
       from unittest.mock import patch

      +import pytest
      +
       from agent_workflows.project_registry import (
           register_or_update_project,
       )
      @@ -269,6 +274,7 @@ class CompanionAttachmentTests(unittest.TestCase):
                   os.environ["AW_HOME"] = self._prev_aw_home
               shutil.rmtree(self.tmp_dir, ignore_errors=True)

      +    @pytest.mark.core
           def test_e01(self):
               """E-01: Portable companion identity and machine-local attachment record."""
               from agent_workflows.storage import (
      @@ -348,6 +354,7 @@ class CompanionAttachmentTests(unittest.TestCase):
               self.assertTrue(report["valid"])
               self.assertEqual(report["target_repo"], self.target_repo.resolve().as_posix())

      +    @pytest.mark.core
           def test_e03(self):
               """E-03: Materialize private companion storage bundle and Git boundary separation."""
               from agent_workflows.storage import (
      @@ -453,6 +460,7 @@ class CompanionAttachmentTests(unittest.TestCase):
               )
               self.assertFalse(st5.remote_acknowledged)

      +    @pytest.mark.core
           def test_e05(self):
               """E-05: Attachment lifecycle operations (attach, detach, move, reattach, status)."""
               from agent_workflows.storage import (
      ```
    - `-v` run over `tests/test_storage.py`:
      ```
      ============================== 13 passed in 2.77s ==============================
      ```
    - `-m core --collect-only -q` over `tests/test_storage.py`:
      ```
      tests/test_storage.py::CompanionAttachmentTests::test_e03
      tests/test_storage.py::CompanionAttachmentTests::test_e05
      tests/test_storage.py::CompanionAttachmentTests::test_e01

      NOTE: 10 tests were deselected by -m/-k and did not run (filtered by marker expression: 'core')
      ============================== SLOW TESTS REPORT ===============================
      0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
      3/13 tests collected (10 deselected) in 0.31s
      ```
    - Failures under scratch mutations:
      `load_local_attachment_record` return None:
      ```
      FAILED tests/test_storage.py::CompanionAttachmentTests::test_e01 - AssertionError: unexpectedly None
      ================== 1 failed, 2 passed, 10 deselected in 0.40s ==================
      ```
      `get_git_commit_boundaries` return None:
      ```
      FAILED tests/test_storage.py::CompanionAttachmentTests::test_e03 - TypeError: 'NoneType' object is not subscriptable
      ================== 1 failed, 2 passed, 10 deselected in 0.81s ==================
      ```
      `move_companion` return None:
      ```
      FAILED tests/test_storage.py::CompanionAttachmentTests::test_e05 - TypeError: 'NoneType' object is not subscriptable
      ================== 1 failed, 2 passed, 10 deselected in 0.42s ==================
      ```
      `reattach_companion` return None:
      ```
      FAILED tests/test_storage.py::CompanionAttachmentTests::test_e05 - TypeError: 'NoneType' object is not subscriptable
      ================== 1 failed, 2 passed, 10 deselected in 0.41s ==================
      ```
    - Reach output from Required tests (`-m core --cov=agent_workflows.layout_migration --cov=agent_workflows.storage --cov-report=term-missing`):
      ```
      Name                                  Stmts   Miss  Cover   Missing
      -------------------------------------------------------------------
      agent_workflows/layout_migration.py     722    344    52%   98, 157, 160, 231, 236, 251-264, 266-269, 315-321, 338-339, 342-343, 372, 388-395, 412-414, 419-423, 431, 455-471, 482-494, 499-504, 538, 545-551, 605, 610, 615-640, 649-677, 700-701, 712-714, 722-736, 755-756, 771-776, 817, 822, 826, 831-840, 844-845, 911-912, 931-932, 937-938, 940-941, 945-948, 966, 983-987, 996, 1001, 1013-1031, 1039-1044, 1070-1073, 1100-1103, 1108, 1133-1137, 1194-1197, 1217-1232, 1246-1308, 1314-1388, 1405-1482, 1488-1513
      agent_workflows/storage.py              307     94    69%   90, 94-95, 103, 113, 121-125, 139-150, 172, 179-184, 195-196, 198-203, 208-209, 211-212, 214-215, 217-218, 220-221, 249-270, 280-307, 328-329, 365, 369-370, 412-417, 436, 443, 451, 459, 481-482, 489-508, 521-526, 529, 576-578, 667
      -------------------------------------------------------------------
      TOTAL                                  1029    438    57%
      ======================= 8 passed, 63 deselected in 2.43s =======================
      ```
    - Bare test suite summary line:
      `818 passed in 27.91s` (`aw suite`, exit 0); `818 passed in 46.69s` (`python3 -m pytest`).
    - Final empty diff in production code:
      `git diff agent_workflows/` is empty.
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after explicit human approval (`Status: approved`).

Execution contract:
- All open questions are resolved (OQ-01).
- Scope fence: the three Scope-Paths test files are the only declared paths; an out-of-scope edit (for example a gated `bug` backlog item filed under the restore rule) is made and justified at finalize (`--scope-reason`), not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (migrated trees, journals, returned records), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Mutation spot-checks are scratch production edits that must be reverted and absent from the diff; confirm with an empty `git diff agent_workflows/`.
- Commit only through `aw commit 5e7czd -- tests/test_layout_migration.py tests/test_awmigrename.py tests/test_storage.py` (plus any justified out-of-scope path), verify `git diff --cached --name-only` lists only those paths, and never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner performs `aw ipd finalize`; when executing by hand, run `aw ipd lint --phase pre-transition` to conforming with every V-item at `Result: pass`, then `aw ipd finalize` yourself. Never `git mv` the plan to `executed/` by hand.
