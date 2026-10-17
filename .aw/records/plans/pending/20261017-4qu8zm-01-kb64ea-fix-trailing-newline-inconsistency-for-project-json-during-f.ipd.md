# IPD: Fix trailing newline inconsistency for project.json during framework install

- Date: 2026-10-17
- Kind: child
- Concern: `.aw/config/project.json` ends with a trailing newline or not depending on which install code path wrote it last, so a reinstall flips the file's final byte and produces spurious git diffs in a tracked, committed policy file.
- Scope: Make the placement-switch writer of `.aw/config/project.json` and `.aw/config/local.json` (`placement_switch._write_atomic_json`) emit exactly one trailing newline, and add behavioral tests that drive the writers and assert on the bytes on disk, including a regression test that the install-wizard writer (`install_wizard.persist_project_policy`) stays byte-stable. The install-wizard writer fix itself is carried by plan `gbnrdf` (Set `denczr`), which this plan depends on, so the two plans never make the same edit.
- Scope-Paths: agent_workflows/placement_switch.py, tests/test_install_config_trailing_newline.py
- Item-Dependencies: executed:gbnrdf
- Status: approved
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: low
- From-Backlog: 4qu8zm
- Blocks-Release: next
- Set: 4qu8zm
- Order: 1
- Highest E allocated: 04
- Author: opencode claude opus
- Id: kb64ea
- Approval: 2026-10-17, recorded via aw ipd set: status set to approved

## Workflow history
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed (review record `.aw/records/reviews/20261017-4qu8zm-01-kb64ea-fix-trailing-newline-inconsistency-for-project-json-during-f.review.md`)

- 2026-10-17 draft (opencode claude opus): created.
- 2026-10-17 to-review (opencode claude opus): authored from backlog 4qu8zm with findings, checklist, and validation.

## Goal

Every install-time write of `.aw/config/project.json` ends with exactly one `\n`, so running the installer twice (or an install followed by a placement switch) leaves the tracked file byte-identical when the policy content did not change.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Writers

- [x] E-01 Confirm (read-only) that plan `gbnrdf` is in `.aw/records/plans/executed/` and that `install_wizard.persist_project_policy` now writes `"\n"` after both `json.dump(proj_schema.to_dict(), f, indent=2)` and `json.dump(local_schema.to_dict(), f, indent=2)`. Do NOT edit `install_wizard.py` (it is not in this plan's Scope-Paths); if the fix is absent, STOP and report, because the prerequisite `gbnrdf` did not land.
  - Depends on: none
  - Expected outcome: the install-wizard newline fix is present from `gbnrdf`, so this plan's test (a)/(b) below are regression coverage that pass from the start, and this plan changes only `placement_switch.py`.
  - Execution state: performed
- [x] E-02 After E-03's tests have been run red (see E-03), in `placement_switch._write_atomic_json`, write a trailing `"\n"` after `json.dump(data, f, indent=2)`, so the project.json and local.json writes that go through it (the `new_proj_schema` and `new_local_schema` writes) match the records-backend rewrite path in the same module, which already appends `f.write("\n")`.
  - Depends on: E-03
  - Expected outcome: every file written through `_write_atomic_json` (project.json, local.json, journals, receipts) ends in exactly one `\n`; readers use `json.load`/`json.loads`, which accept trailing whitespace.
  - Execution state: performed

### Task group 2: Tests

- [x] E-03 Create `tests/test_install_config_trailing_newline.py` with tests that (a) call `persist_project_policy` on a fresh temp git repo (pattern from `tests/test_reinstall_preserves_config.py::TestPersistProjectPolicyPreservation`) and assert `project.json` and `local.json` bytes end with `b"}\n"` and not `b"\n\n"`; (b) seed a `project.json` whose `cutovers` are already complete (so `sync_cutovers_on_install` does not rewrite), run `persist_project_policy` twice, and assert the second run leaves `project.json` byte-identical to the first and ending in one `\n`; (c) call `placement_switch._write_atomic_json` on a temp path and assert the bytes end in exactly one `\n` (`endswith(b"}\n")` and not `endswith(b"\n\n")`) and round-trip through `json.loads`. Write the file BEFORE E-02 and run it once against the unmodified `placement_switch.py`, keeping the output for V-03.
  - Depends on: E-01
  - Expected outcome: before E-02, (a) and (b) pass (the `gbnrdf` fix is present) and (c) fails (measured at review: `_write_atomic_json` currently ends the file with `b'\n}'`, no trailing newline); after E-02 all pass.
  - Execution state: performed
- [x] E-04 Run the new test file, the existing install and placement-switch test files (with the slow marker filter cleared, since most of them are `pytestmark = pytest.mark.slow`), and the core suite.
  - Depends on: E-02, E-03
  - Expected outcome: all pass with no new failures.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Install writes are atomic temp-file plus `os.replace` (`install_wizard.persist_project_policy`, `config.sync_cutovers_on_install`, `placement_switch._write_atomic_json`); the fix keeps that pattern and only adds the newline inside the temp-file write.
- The repository's own committed `.aw/config/project.json` ends in `}\n` (checked with `od -c`), and `config.py` writes canonical config with `json.dumps(..., indent=2, sort_keys=True) + "\n"`, so trailing-newline is the established convention.
- Tests must exercise code and assert on outputs (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE"); no source-reading tests.
- Suite command: bare `python3 -m pytest` (core tier); narrowed runs by explicit path.

## Findings

| Writer | File(s) | Trailing newline today |
|---|---|---|
| `install_wizard.persist_project_policy` (`json.dump(proj_schema.to_dict(), f, indent=2)`) | project.json | no (fixed by plan `gbnrdf`, a prerequisite) |
| `install_wizard.persist_project_policy` (`json.dump(local_schema.to_dict(), f, indent=2)`) | local.json | no (fixed by plan `gbnrdf`, a prerequisite) |
| `config.sync_cutovers_on_install` (`f.write("\n")` after dump), only when `modified` | project.json | yes |
| `placement_switch._write_atomic_json` (used for `new_proj_schema` / `new_local_schema`) | project.json, local.json | no |
| `placement_switch` records-backend rewrite (`json.dump(new_proj_data, f, indent=2)` then `f.write("\n")`) | project.json, local.json | yes |

Mechanism: `persist_project_policy` writes project.json without a newline, then calls `config.sync_cutovers_on_install`, which rewrites it WITH a newline only when it stamps a missing cutover. A first install stamps cutovers (newline present); a reinstall finds cutovers already present, skips the rewrite, and leaves the newline-less file from `persist_project_policy`. The tracked file therefore toggles its final byte between installs. A placement switch writes project.json through `_write_atomic_json` with no newline, so a later reinstall (which, after `gbnrdf`, writes a newline) toggles it again; that is the half this plan fixes.

Duplicate carrier: pending plan `gbnrdf` (Set `denczr`, `- Blocks-Release: next`, reviewed) adds exactly the two `persist_project_policy` newline writes this plan's former E-01 described, plus a byte-stability test. This plan therefore depends on `executed:gbnrdf` and does not edit `install_wizard.py`.

## Proposed changes (ordered, validatable)

1. E-01: confirm the `gbnrdf` install-wizard fix landed (read-only).
2. E-03: behavioral tests, run red before E-02.
3. E-02: append `\n` in `placement_switch._write_atomic_json`.
4. E-04: suite runs.

## Deferred / out of scope (with reason)

- `install_history.py` snapshot write (`json.dump(snapshot, f, indent=2)`): an install-history record under durable state, not `project.json`; the backlog item is scoped to project.json, so it is left unchanged.
  - Carrier-Declined: install-history record under durable state; backlog item is scoped to project.json
- The `install_wizard.persist_project_policy` newline fix: carried by plan `gbnrdf` (Set `denczr`), a declared prerequisite; making the same edit here would duplicate it.
  - Carrier: gbnrdf
  - Carrier-Evidence: .aw/records/plans/executed/20261017-denczr-01-gbnrdf-make-the-install-wizard-write-project-json-and-local-json-wi.ipd.md
- A shared JSON-write helper consolidating all writers: refactor beyond this bug's scope.
  - Carrier-Declined: architectural refactoring beyond this bug's focused scope

## Scope check

- Over-scope: the former install-wizard edit duplicated plan `gbnrdf` and was removed (now a read-only prerequisite check). E-02 also changes journal/receipt files written through `_write_atomic_json`; this is accepted because splitting the helper just for config files adds complexity, and all readers parse with `json` which ignores trailing whitespace. local.json is fixed alongside project.json because the same functions write it with the same defect.
- Under-scope: none.

## Required tests / validation

- `python3 -m pytest -o addopts="" -q tests/test_install_config_trailing_newline.py` passes (V-03).
- `python3 -m pytest -o addopts="" -q -n auto tests/test_reinstall_preserves_config.py tests/test_placement_switch_execute.py tests/test_placement_switch_companion_execute.py tests/test_placement_switch_guard.py tests/test_installer.py` passes (V-04). Clearing `addopts` is required: three of these files are `pytestmark = pytest.mark.slow`, and the default filter deselects 174 of their 185 tests (measured at review).
- Bare `python3 -m pytest` core tier passes (V-04).

## Spec / documentation sync

N/A: no spec or user-facing doc describes the byte format of `project.json`; this restores the existing convention.

## Open questions

### OQ-01: Should local.json and placement-switch journals also get the newline?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Yes. They are written by the same functions with the same defect, and the repository convention (`config.py` canonical write, `sync_cutovers_on_install`) is trailing newline; fixing only project.json would leave the same function inconsistent.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `ls .aw/records/plans/executed/ | grep gbnrdf` showing the prerequisite plan, the `grep -n -A1 'json.dump(\(proj\|local\)_schema.to_dict(), f, indent=2)' agent_workflows/install_wizard.py` output showing an `f.write("\n")` line after each, and `git diff --name-only <base>..HEAD -- agent_workflows/install_wizard.py` for this plan's own commits showing nothing.
  - Observed evidence:
```
$ ls .aw/records/plans/executed/ | grep gbnrdf
20261017-denczr-01-gbnrdf-make-the-install-wizard-write-project-json-and-local-json-wi.ipd.md

$ grep -n -A1 'json.dump(\(proj\|local\)_schema.to_dict(), f, indent=2)' agent_workflows/install_wizard.py
1383:        json.dump(proj_schema.to_dict(), f, indent=2)
1384-        f.write("\n")
--
1483:        json.dump(local_schema.to_dict(), f, indent=2)
1484-        f.write("\n")

$ git diff --name-only 740bf0135..HEAD -- agent_workflows/install_wizard.py
(empty output)
```
  - Result: pass
- [x] V-02 validates E-02
  - Required evidence: paste the `git diff agent_workflows/placement_switch.py` hunk showing the `\n` write in `_write_atomic_json`.
  - Observed evidence:
```diff
diff --git a/agent_workflows/placement_switch.py b/agent_workflows/placement_switch.py
index f95d56e4f..4927d81fb 100644
--- a/agent_workflows/placement_switch.py
+++ b/agent_workflows/placement_switch.py
@@ -1663,6 +1663,7 @@ def _write_atomic_json(target_path: Path, data: Dict[str, Any]) -> None:
     tmp_path = target_path.parent / f".tmp_{target_path.name}"
     with open(tmp_path, "w", encoding="utf-8") as f:
         json.dump(data, f, indent=2)
+        f.write("\n")
     os.replace(tmp_path, target_path)
```
  - Result: pass
- [x] V-03 validates E-03
  - Required evidence: paste `python3 -m pytest -o addopts="" -v tests/test_install_config_trailing_newline.py` output run BEFORE E-02 showing tests (a) and (b) PASSED and test (c) FAILED on the trailing-newline assertion, then the same command after E-02 showing every test PASSED with zero failed.
  - Observed evidence:
```
--- BEFORE E-02 (showing test_placement_switch_write_atomic_json_trailing_newline FAILED):
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <python3-bin>
cachedir: .pytest_cache
Using --randomly-seed=1762769113
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 3 items

tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_persist_project_policy_reinstall_byte_identical_with_complete_cutovers PASSED [ 33%]
tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_persist_project_policy_fresh_install_trailing_newline PASSED [ 66%]
tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_placement_switch_write_atomic_json_trailing_newline FAILED [100%]

=================================== FAILURES ===================================
_ TestInstallConfigTrailingNewline.test_placement_switch_write_atomic_json_trailing_newline _

self = <tests.test_install_config_trailing_newline.TestInstallConfigTrailingNewline testMethod=test_placement_switch_write_atomic_json_trailing_newline>

    def test_placement_switch_write_atomic_json_trailing_newline(self):
        """(c) _write_atomic_json ends with exactly one newline and round-trips through json.loads."""
        with tempfile.TemporaryDirectory() as td:
            tpath = Path(td)
            target_path = tpath / "sub" / "test.json"
            data = {"key": "value", "items": [1, 2, 3], "nested": {"a": True}}

            _write_atomic_json(target_path, data)

            raw = target_path.read_bytes()
>           self.assertTrue(
                raw.endswith(b"}\n"),
                f"Expected raw bytes to end with b'}}\\n', got: {raw[-10:]!r}",
            )
E           AssertionError: False is not true : Expected raw bytes to end with b'}\n', got: b'true\n  }\n}'

tests/test_install_config_trailing_newline.py:130: AssertionError
============================== SLOW TESTS REPORT ===============================
0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
=========================== short test summary info ============================
FAILED tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_placement_switch_write_atomic_json_trailing_newline
========================= 1 failed, 2 passed in 0.38s ==========================

--- AFTER E-02 (showing all 3 tests PASSED):
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- <python3-bin>
cachedir: .pytest_cache
Using --randomly-seed=2090151111
rootdir: <repo-root>
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 3 items

tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_persist_project_policy_fresh_install_trailing_newline PASSED [ 33%]
tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_placement_switch_write_atomic_json_trailing_newline PASSED [ 66%]
tests/test_install_config_trailing_newline.py::TestInstallConfigTrailingNewline::test_persist_project_policy_reinstall_byte_identical_with_complete_cutovers PASSED [100%]
============================== SLOW TESTS REPORT ===============================

0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
============================== 3 passed in 0.36s ===============================
```
  - Result: pass
- [x] V-04 validates E-04
  - Required evidence: paste the summary line of the `-o addopts=""` run of the named existing test files (zero failed, zero deselected) and the `N passed` summary line of the bare `python3 -m pytest` core run with `echo "exit=$?"` showing 0.
  - Observed evidence:
```
Summary line of python3 -m pytest -o addopts="" -q -n auto tests/test_reinstall_preserves_config.py tests/test_placement_switch_execute.py tests/test_placement_switch_companion_execute.py tests/test_placement_switch_guard.py tests/test_installer.py:
191 passed in 139.59s (0:02:19)

Summary line of bare python3 -m pytest; echo "exit=$?":
893 passed in 75.56s (0:01:15)
exit=0
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`) and after `gbnrdf` is executed; every open question is resolved. Commit only files you changed, through `aw commit kb64ea -- agent_workflows/placement_switch.py tests/test_install_config_trailing_newline.py`; never `git add -A`, never push. You MUST paste the ACTUAL runner output into each `V-*`; never claim a test passed that you did not run. Scope fence: `- Scope-Paths:` is a declaration, not a stop condition; an out-of-scope edit that proves necessary is made and justified (`aw ipd finalize` requires `--scope-reason` per out-of-scope path and `--scope-ack` per declared-but-unmodified path). The one stop condition is E-01's missing prerequisite. Lifecycle: after every V-item is `pass` and `aw ipd lint --phase pre-transition` conforms, the plan reaches `.aw/records/plans/executed/` only through `aw ipd finalize`, never a hand `git mv`; under `aw oc run` / `aw agy run` the runner performs that transition, and only an executor running by hand invokes `aw ipd finalize` itself.
