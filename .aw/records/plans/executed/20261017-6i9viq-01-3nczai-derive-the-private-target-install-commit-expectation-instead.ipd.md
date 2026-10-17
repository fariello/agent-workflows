# IPD: Derive the private-target install commit expectation instead of hard-coding a file count

- Date: 2026-10-17
- Kind: child
- Concern: `tests/test_clean_target_config_home.py` method `test_case_l_tracked_install_still_writes_target` asserts a literal file count (`self.assertIn("358 files changed", tail)`) on the commit a `private-target -y` install makes. The count is the size of the shipped payload, so every added or removed workflow asset breaks the test with no behavior change. It has already been bumped once (commit a75488af5 changed "357" to "358"), backlog `6i9viq` and the duplicate backlog `ioegmo` were both filed for the same breakage, and it will recur on the next payload change.
- Scope: IN: the literal count assertion in `test_case_l_tracked_install_still_writes_target` was ALREADY replaced, outside this plan, by commit 84cba788c ("fix(ci): derive test_case_l expectation ..."), with exactly the derived assertions this plan specified (install commit path set equals tracked installed path set, non-empty, contains `AGENTS.md` and `.aw/.gitignore`, clean `git status --porcelain`). This plan therefore (1) confirms the landed assertions match the specification and pass, and (2) performs the sensitivity proof that commit did not record (a deliberately partial commit and a stray untracked file each make the test fail), so the release-gated backlog item `6i9viq` closes on verified evidence. OUT: any further edit to the test (unless E-01 finds a divergence), any change to the installer, the payload, or other test cases; closing backlog `ioegmo` or its plan `im4afa` (a separate item; noted below).
- Scope-Paths: tests/test_clean_target_config_home.py
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 6i9viq
- Blocks-Release: next
- Set: 6i9viq
- Order: 1
- Highest E allocated: 02
- Author: opencode
- Id: 3nczai

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: 3nczai verified (set 6i9viq, attempt 1).
- 2026-10-17 approved (aw set): status set to approved
- 2026-10-17 reviewed (aw set): /plan-review (opencode/its_direct/pt3-claude-opus-5.5-1m-us): APPROVE WITH REVISIONS APPLIED; PR-001..PR-004 fixed
- 2026-10-17 draft (opencode): created.
- 2026-10-17 to-review (opencode): authored review-ready from backlog 6i9viq.

## Goal

Make test case (l) verify what actually matters about a tracked `private-target -y` install (it commits everything it wrote, and nothing is left uncommitted) without pinning the payload size, so the test stops failing every time a workflow file is added or removed.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Replace the pinned count with derived assertions

- [x] E-01 Confirm that `test_case_l_tracked_install_still_writes_target` as landed by commit 84cba788c carries the specified derived assertions and no literal count: (a) `git show --name-only --format= HEAD` gives the set of paths the install commit touched; (b) `git ls-files` in the target, minus the pre-existing `README.md`, gives the set of tracked installed paths; (a) is asserted equal to (b); (c) that set is asserted non-empty and to contain `AGENTS.md` and `.aw/.gitignore`; (d) `git status --porcelain` in the target is asserted empty; every earlier assertion of the method (`returncode == 0`, HEAD moved, `AGENTS.md`/`.aw/.gitignore`/backups exist, the `Git: changes staged; commit offered below` line) is still present. If the method at execution time diverges from (a)-(d), edit it to match and say so in V-01; otherwise make no edit to the test file.
  - Depends on: none
  - Expected outcome: the method contains no hard-coded file count and its assertions are all computed from the target repository's git state after the install; whether an edit was needed is stated.
  - Execution state: performed

### Task group 2: Prove the test still detects a broken commit

- [x] E-02 Run the test and the full module, then demonstrate the derived assertions are not vacuous with two temporary, uncommitted edits to the method, each inserted immediately after the `assertIn("Git: changes staged; commit offered below", ...)` line and reverted before the next: (1) a partial commit, `subprocess.run(["git", "rm", "--cached", "-q", "AGENTS.md"], cwd=str(target), check=True)` followed by `subprocess.run(["git", "commit", "-qm", "drop"], cwd=str(target), check=True)`, which must fail the set-equality assertion; (2) a stray file, `(target / "stray.txt").write_text("x", encoding="utf-8")`, which leaves the commit and tracked sets equal and must fail ONLY the clean-status assertion. Restore the file with `git checkout -- tests/test_clean_target_config_home.py` after each run.
  - Depends on: E-01
  - Expected outcome: the real test passes; each broken variant fails with an `AssertionError` from the expected assertion; `git status --short tests/test_clean_target_config_home.py` is empty afterwards.
  - Execution state: performed

## Project conventions discovered (Step 0)

- AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE": tests must assert on real outputs, exit codes, and side effects. The replacement assertions read the target repo's git state produced by actually running `aw install`, which satisfies this; a literal payload size is an implementation detail of the shipped asset set, not an outcome of the behavior under test.
- The routine gate is bare `python3 -m pytest`; narrowed per-test runs use `python3 -m pytest -o addopts="" <path> -k <name>` (AGENTS.md, repository development contract).
- Commits go through `aw commit <plan> -- <paths>`; never push.
- The test drives the CLI through the class helper `self._run_aw(...)` and git through `subprocess.run(..., cwd=str(target))`; the new assertions follow the same pattern.

## Findings

| # | Finding | Evidence |
|---|---|---|
| F1 | The assertion pinned the payload size (historical; fixed at HEAD). | Before 84cba788c the method ended with `self.assertIn("358 files changed", tail)` where `tail` is the last line of `git show --stat --format= HEAD`. |
| F6 | The fix already landed outside this plan, with no sensitivity proof. | `git show 84cba788c -- tests/test_clean_target_config_home.py` replaces the stat parse with the `commit_paths == tracked_paths`, non-empty, `AGENTS.md`, `.aw/.gitignore` and empty-porcelain assertions; the commit message records no mutation run. At review, `python3 -m pytest -o addopts="" -q tests/test_clean_target_config_home.py -k test_case_l` reported `1 passed, 22 deselected`. |
| F2 | The count has already drifted once. | `git log -L` on that line: introduced as "357" in 9ca816dba (3m8aix), changed to "358" in a75488af5 (ki6t17). |
| F3 | (Superseded by F6.) When authored, the backlog failure was masked by the a75488af5 bump while the pinned count remained. | Authoring-time run reported `1 passed`; 84cba788c later removed the literal. |
| F4 | A duplicate backlog item exists for the same breakage. | `.aw/records/backlog/open/20261016-ioegmo-01-ioegmo-test-clean-target-config-home-pins-stale-357-files.backlog.md` ("pins stale 357 files changed count broken by askme rationale.md"). |
| F5 | The intent of the count was "the install commit captures the installed tree", which can be checked directly. | The method's docstring: "tracked private-target install still writes target, commits under -y, and matches baseline". |

## Proposed changes (ordered, validatable)

1. E-01: confirm the landed tail of `test_case_l_tracked_install_still_writes_target` matches the derived-assertion specification (edit only on divergence). Validated by V-01.
2. E-02: run the test and module, and prove a partial commit and a stray file are each caught. Validated by V-02.

## Deferred / out of scope (with reason)

- Backlog `ioegmo` describes the same defect, and its pending plan `im4afa` is equally stale after 84cba788c. Closing or retiring them is a decision for the maintainer and is outside this plan's scope fence; this plan's V-02 evidence is what a reviewer may cite when doing so.
  - Carrier-Declined: duplicate backlog item ioegmo is tracked separately and graduated to plan im4afa
- No installer or payload change: the installer behavior is correct; only the test is wrong.
  - Carrier-Declined: installer behavior is correct; only the test assertion is changed

## Scope check

- Over-scope: none.
- Under-scope: none. The sensitivity proof (E-02) is the only work 84cba788c left undone. The only failing surface named by the backlog item is the single literal in this one method; no other test in `tests/` asserts a "files changed" count (`grep -rn "files changed" tests/` finds only this line and an unrelated comment in `tests/test_status_set.py`).

## Required tests / validation

- `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l` passes (V-01).
- `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py` passes (V-02).
- A deliberately partial commit, and separately a stray untracked file, each make the test fail (V-02).
- The routine gate `python3 -m pytest` passes (V-02).

## Spec / documentation sync

N/A: test-only change; no spec or user-facing documentation describes the install commit's file count.

## Open questions

None. The remedy follows from AGENTS.md's outcome-testing rule and the test's own docstring; no decision needs the maintainer.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: paste `git show 84cba788c -- tests/test_clean_target_config_home.py` (the landed change removing the literal and adding the path-set and clean-status assertions) and `git diff -- tests/test_clean_target_config_home.py` (empty unless E-01 found a divergence, in which case paste the corrective hunk and say why); paste `grep -n "files changed" tests/test_clean_target_config_home.py` returning no match; paste the actual output of `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l` showing `1 passed`.
  - Observed evidence:
```
$ git show 84cba788c -- tests/test_clean_target_config_home.py
commit 84cba788cd58ece72756a63042700308ffeab6e5
Author: Gabriele Fariello <gabriele.fariello@gmail.com>
Date:   Sat Oct 17 13:24:09 2026 -0400

    fix(ci): derive test_case_l expectation and declare Carrier-Declined in pending plans

    AW-Runner: aw commit

diff --git a/tests/test_clean_target_config_home.py b/tests/test_clean_target_config_home.py
index e48dfa529..1d24cb606 100644
--- a/tests/test_clean_target_config_home.py
+++ b/tests/test_clean_target_config_home.py
@@ -563,15 +563,36 @@ class TestCleanTargetConfigHome(unittest.TestCase):
         self.assertTrue((target / ".agent-workflows-installer-backups").is_dir())

         self.assertIn("Git: changes staged; commit offered below", res.stdout)
-        stat = subprocess.run(
-            ["git", "show", "--stat", "--format=", "HEAD"],
+        commit_paths = set(
+            subprocess.run(
+                ["git", "show", "--name-only", "--format=", "HEAD"],
+                cwd=str(target),
+                capture_output=True,
+                text=True,
+                check=True,
+            ).stdout.splitlines()
+        )
+        tracked_paths = set(
+            subprocess.run(
+                ["git", "ls-files"],
+                cwd=str(target),
+                capture_output=True,
+                text=True,
+                check=True,
+            ).stdout.splitlines()
+        ) - {"README.md"}
+        self.assertEqual(commit_paths, tracked_paths)
+        self.assertTrue(len(commit_paths) > 0)
+        self.assertIn("AGENTS.md", commit_paths)
+        self.assertIn(".aw/.gitignore", commit_paths)
+        status = subprocess.run(
+            ["git", "status", "--porcelain"],
             cwd=str(target),
             capture_output=True,
             text=True,
             check=True,
         ).stdout.strip()
-        tail = stat.splitlines()[-1] if stat.splitlines() else ""
-        self.assertIn("358 files changed", tail)
+        self.assertEqual(status, "")

     def test_case_m_clean_target_reinstall_and_rollback(self) -> None:
         """Case (m): clean-delta reinstall is a no-op on target, and rollback removes home files leaving target empty."""

$ git diff -- tests/test_clean_target_config_home.py
diff --git a/tests/test_clean_target_config_home.py b/tests/test_clean_target_config_home.py
index 77eb31796..3ac65d5fd 100644
--- a/tests/test_clean_target_config_home.py
+++ b/tests/test_clean_target_config_home.py
@@ -511,7 +511,6 @@ class TestCleanTargetConfigHome(unittest.TestCase):
                 "Expected .created-files.json in home runtime backups",
             )

-    @pytest.mark.xfail(strict=False, reason="bug: 96lj37 - hardcodes file count")
     def test_case_l_tracked_install_still_writes_target(self) -> None:
         """Case (l): tracked private-target install still writes target, commits under -y, and matches baseline."""
         target = self.base / "repo_l"

Divergence rationale: commit 24e4c39cc merged lane vgus66 into main, which had added @pytest.mark.xfail(strict=False, reason="bug: 96lj37 - hardcodes file count") to quarantine the hardcoded file count failure. Because 84cba788c had already fixed the failure on main by deriving the path-set assertions, the xfail decorator was stale, turning what should be 1 passed into 1 xpassed and masking failure on mutations. Removing the stale xfail un-quarantines the test so it runs and asserts actively.

$ grep -n "files changed" tests/test_clean_target_config_home.py
(returned no match, exit code 1)

$ python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py -k test_case_l
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=2769639453
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/3nczai
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 23 items / 22 deselected / 1 selected

tests/test_clean_target_config_home.py .                                 [100%]

NOTE: 22 tests were deselected by -m/-k and did not run (no marker filter was active; deselected by -k/--deselect)
============================== SLOW TESTS REPORT ===============================
0 unlisted slow tests (all tests > 2s are documented in tests/slow_allowlist.txt).
======================= 1 passed, 22 deselected in 3.93s =======================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: for EACH of the two broken variants in E-02, paste the actual `AssertionError` lines showing which assertion failed (set equality for the partial commit; the `git status --porcelain` equality for the stray file); paste `git status --short tests/test_clean_target_config_home.py` empty after reverting; paste the actual output of `python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py` with the `N passed` summary and zero failures; paste the `N passed` summary line of a bare `python3 -m pytest`; paste `git diff --cached --name-only` at commit time listing only this plan file (plus `tests/test_clean_target_config_home.py` only if E-01 required an edit).
  - Observed evidence:
```
Variant 1 (partial commit: git rm --cached -q AGENTS.md && git commit -qm drop):
>       self.assertEqual(commit_paths, tracked_paths)
E       AssertionError: Items in the first set but not the second:
E       'AGENTS.md'
E       Items in the second set but not the first:
E       ...
FAILED tests/test_clean_target_config_home.py::TestCleanTargetConfigHome::test_case_l_tracked_install_still_writes_target

Variant 2 (stray untracked file: (target / "stray.txt").write_text("x", encoding="utf-8")):
>       self.assertEqual(status, "")
E       AssertionError: '?? stray.txt' != ''
E       - ?? stray.txt

tests/test_clean_target_config_home.py:598: AssertionError
FAILED tests/test_clean_target_config_home.py::TestCleanTargetConfigHome::test_case_l_tracked_install_still_writes_target

Reverted mutations check (both E-02 temporary mutations removed; only E-01 corrective edit remains):
$ git status --short tests/test_clean_target_config_home.py
 M tests/test_clean_target_config_home.py

Full module test:
$ python3 -m pytest -o addopts="" tests/test_clean_target_config_home.py
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0
Using --randomly-seed=2015223151
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/3nczai
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 23 items

tests/test_clean_target_config_home.py .......................           [100%]
============================== SLOW TESTS REPORT ===============================

WARNING: 2 test(s) exceeded 2s and are not listed in tests/slow_allowlist.txt:
    3.15s  tests/test_clean_target_config_home.py::TestCleanTargetConfigHome::test_case_s_uninstall_refuses_live_driver
    2.09s  tests/test_clean_target_config_home.py::TestCleanTargetConfigHome::test_case_q_uninstall_tears_down_idle_lane
============================= 23 passed in 52.34s ==============================

Bare pytest N passed summary line:
775 passed in 78.87s (0:01:18)
and via aw suite (bounded workers, passing within core tier budget):
775 passed in 28.55s

git diff --cached --name-only at commit time:
.aw/records/plans/pending/20261017-6i9viq-01-3nczai-derive-the-private-target-install-commit-expectation-instead.ipd.md
tests/test_clean_target_config_home.py
```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Requires explicit human approval before execution.

Execution contract:
- All open questions are resolved.
- Scope fence: see Scope check; an out-of-scope edit is made and justified at finalize, not a reason to stop.
- You MUST paste the ACTUAL command output into each V-item's Observed evidence; never claim a result you did not run.
- Tests assert observable behavior (real outputs, exit codes, files written), never source text or structure (AGENTS.md "TEST OUTCOMES, NOT CODE STRUCTURE").
- Commit only through `aw commit 3nczai -- <this plan> [tests/test_clean_target_config_home.py only if E-01 edited it]`, verify `git diff --cached --name-only` lists only your paths, and never push.
- Post-gate lifecycle: after every V-item reads `pass` and `aw ipd lint --phase pre-transition` conforms, the plan moves to `executed/`: under `aw oc run`/`aw agy run` the runner owns that transition; by hand run `aw ipd finalize 3nczai`, passing `--scope-ack tests/test_clean_target_config_home.py` when E-01 needed no edit (the declared path is then legitimately unmodified). Never `git mv` the plan by hand. This plan carries `- Blocks-Release: next` inherited from backlog `6i9viq`.
