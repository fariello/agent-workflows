# IPD: aw set refuses a review record instead of writing a lifecycle into it

- Date: 2026-10-16
- Kind: child
- Concern: `aw set <status> <path to a .review.md>` types the review as `other` and, without `--dry-run`, rewrites it with a `- Status:` line and a `## Workflow history` entry, although a review has no status lifecycle (backlog `9pu7sf`, measured 2026-10-15 and re-measured 2026-10-16 below).
- Scope: Make the status setter (`status_set.run_set_command`) refuse, at exit 2 and before any write, every selector that resolves to a record inside a non-lifecycle record tree (today only `reviews`), naming `reviews` as a type with no status lifecycle, on the untyped verb and on every type-scoped spelling, dry-run or not. Add behavioral tests, correct the `artifact_types` module docstring that names this bug as outstanding, and add a CHANGELOG `Fixed:` line.
- Scope-Paths: agent_workflows/status_set.py, agent_workflows/artifact_types.py, tests/test_set_refuses_review_record.py, CHANGELOG.md
- Item-Dependencies: none
- Status: executed
- Readiness: go-pending-approval
- Work-Kind: bug
- Priority: medium
- From-Backlog: 9pu7sf
- Blocks-Release: next
- Set: 9pu7sf
- Order: 1
- Highest E allocated: 05
- Author: opencode
- Id: p4xo1u

## Workflow history
- 2026-10-17 executed (aw agy run model=Gemini-3.8-Flash-High): aw agy run self-finalize: p4xo1u verified (set 9pu7sf, attempt 1).
- 2026-10-16 approved (aw set): status set to approved
- 2026-10-16 reviewed (opencode its_direct/pt3-claude-opus-5.5-1m-us): /plan-review: APPROVE WITH REVISIONS APPLIED; PR-001..PR-005
- 2026-10-16 to-review (opencode): authored review-ready plan graduating backlog 9pu7sf.
- 2026-10-16 draft (opencode): created.

## Goal

A review record is never mutated by `aw set`: every spelling that reaches a `.aw/records/reviews/` file refuses at exit 2 with a message naming `reviews` as a record type with no status lifecycle, and the file stays byte-identical. This makes the `artifact_types` docstring's claim that reviews "stays out of ... `aw set`" true.

## Detailed Implementation Checklist (TODO)

Execution-state rule: mark an `E-*` item complete only after performing the action. That mark is not validation. Right-sizing rule: each E-item must address one concern and be executable in one focused pass; split when an E-item names multiple distinct deliverables or independent test-surfaces. Accepted execution states: blocked, failed, pending, performed; terminal gate demands 'performed'.

### Task group 1: Failing behavioral tests first

- [x] E-01 Create `tests/test_set_refuses_review_record.py`. Fixture: a temp git repo made with `tests.support.init_repo` (scrubs inherited `GIT_DIR`/`GIT_INDEX_FILE` via `clean_git_env` and sets local `user.email`/`user.name`/`commit.gpgsign false`; run the seed `git add`/`git commit` with `env=tests.support.clean_git_env()`) holding only `.aw/records/reviews/20260929-demo-01-ab12cd-x.review.md` with content `"# Review: x\n\n- Subject-Id: ab12cd\n"`, committed. Drive `cli.main([...])` with `--dir <repo>` (capture stdout+stderr, catch `SystemExit`, same harness shape as `_run_cli` in `tests/test_reviews_type_noun_surface.py`). Parametrize over argv forms: (a) `["--no-interactive", "set", "approved", <path>, "--yes", "--no-commit"]`; (b) the same with `--dry-run`; (c) `["--no-interactive", "set", "other", "approved", <path>, "--yes", "--no-commit"]` (the `other`-scoped spelling, whose type check would otherwise PASS because the review is typed `other`); (d) `["--no-interactive", "set", "to-review", <path relative to repo>, "--yes", "--no-commit"]` run with the repo as cwd (restore the previous cwd in a `finally`). For each assert: exit code is 2; output contains `reviews` and `no status lifecycle`; the review file bytes are unchanged; `git status --porcelain` in the repo is empty. Add a positive control in the same module: a backlog item `.aw/records/backlog/open/20260929-zz12cd-01-zz12cd-y.backlog.md` (`- Id: zz12cd`, `- Status: open`, `- Set: zz12cd`, `- Priority: low`, `- Work-Kind: chore`, `- Summary: y`) set to `parked` via `aw set parked <path> --yes --no-commit` exits 0 and the item now lives at `.aw/records/backlog/parked/20260929-zz12cd-01-zz12cd-y.backlog.md` reading `- Status: parked` (measured 2026-10-16: the setter moves it into the `parked/` bucket), proving the refusal is specific to reviews and not a blanket direct-path refusal. The module carries no `slow`/`livecorpus` mark, so CI's full `tests/` step collects it. Run the module against the UNCHANGED code and record that the four review cases fail (measured at review: (a), (c), (d) exit 0 and rewrite the file; (b) exits 0 with the file unchanged, so it fails on the exit-code and message assertions) while the positive control passes.
  - Depends on: none
  - Expected outcome: New module exists; against current code the review cases fail, the control passes.
  - Execution state: performed

### Task group 2: The refusal

- [x] E-02 In `agent_workflows/status_set.py` add a helper `_non_lifecycle_record_type(path: Path, repo_root: Path) -> str | None` that returns the owning type name when `path` resolves inside any directory returned by `selectors.record_dirs(repo_root, t)` for `t` in `selectors.NON_PRIMARY_RECORD_DIRS` (derived, never a hardcoded `"reviews"` literal), else `None`. In `run_set_command`, inside the `for tok in selector_tokens:` loop immediately after the `if not matches:` refusal and BEFORE the ambiguity block, refuse when any match's path is in such a tree: `term.status("fail", f"Selector '{tok}' resolved to a {t} record ({path}); {t} records have no status lifecycle, so aw set cannot change them. Refusing before making changes.")` and `return 2`. Do NOT change `detect_artifact_type` (it has seven callers across `runner_shared`, `check_engine`, `artifact_audit` and `run_selection_policy`; retyping reviews there is a wider behavior change this bug does not need, see Findings F-03).
  - Depends on: E-01
  - Expected outcome: All E-01 cases pass; no other behavior changes. (Mechanism demonstrated at review: a monkeypatched equivalent of this helper and placement, deriving from `selectors.NON_PRIMARY_RECORD_DIRS` == `{'reviews'}` and `selectors.record_dirs`, refused all four spellings at rc 2 with the file byte-identical and `git status --porcelain` empty.)
  - Execution state: performed

### Task group 3: Docs and changelog

- [x] E-03 In `agent_workflows/artifact_types.py` module docstring replace "while `aw set` does not yet refuse a review path (backlog `9pu7sf`)." with a sentence stating that `aw set` refuses a review path at exit 2 (`status_set.run_set_command`, backlog `9pu7sf`, guarded by `tests/test_set_refuses_review_record.py`).
  - Depends on: E-02
  - Expected outcome: Docstring no longer claims the bug is outstanding.
  - Execution state: performed

- [x] E-04 Add one `- Fixed:` bullet to the top pending section of `CHANGELOG.md`: aw set now refuses a review record (exit 2, file untouched) instead of writing a Status line and workflow history into it, since reviews have no status lifecycle. No em or en dashes (user-facing prose).
  - Depends on: E-02
  - Expected outcome: CHANGELOG carries the entry.
  - Execution state: performed

### Task group 4: Regression and commit

- [x] E-05 Run `python3 -m pytest -o addopts="" -v tests/test_set_refuses_review_record.py tests/test_reviews_type_noun_surface.py tests/test_status_set.py tests/test_review_record_classifier.py`, then the routine suite bare (`python3 -m pytest`), then commit via `aw commit p4xo1u -- agent_workflows/status_set.py agent_workflows/artifact_types.py tests/test_set_refuses_review_record.py CHANGELOG.md`.
  - Depends on: E-03, E-04
  - Expected outcome: All pass; one path-scoped commit.
  - Execution state: performed

## Project conventions discovered (Step 0)

- Routine suite is run bare as `python3 -m pytest`; a narrowed run uses `-o addopts=""` for per-test output (AGENTS.md repository development contract).
- Tests must drive the CLI and assert exit codes and on-disk effects, never read source (AGENTS.md, GUIDING_PRINCIPLES P16).
- The non-lifecycle record trees are owned by `layout.py` (`RecordClassDefinition(name="reviews", ..., is_primary=False)`) and exported as `selectors.NON_PRIMARY_RECORD_DIRS`; consumers derive from that set rather than re-listing (P8 single source).
- `status_set.run_set_command` already refuses before writing for collisions and type mismatches with `term.status("fail", ...)` then `return 2`; the new refusal follows that shape.
- Commits go through `aw commit <plan> -- <paths>`.
- Every other mutating spelling funnels into the same `status_set.run_set_command` (`backlog.py`, `specs.py`, `work_cmd.py`, the three `cli.py` call sites), so one refusal there covers them. Measured at review: `aw ipd set`, `aw specs set` and `aw backlog set` on the review path already refuse with `Type mismatch` (rc 2, file unchanged), and a bare id6 refuses with `No artifact matched` (rc 2).

## Findings

- F-01 (re-measured 2026-10-16 in this lane, temp repo holding only the review file): `python3 -m agent_workflows set approved .aw/records/reviews/20260929-demo-01-ab12cd-x.review.md --dry-run` printed `other  20260929-demo-01-ab12cd  draft -> ?  approved  (dry-run)` and exited `rc=0`.
- F-02 Root: `status_set.detect_artifact_type` has no facet match for `.review.md` (`artifact_naming.TYPE_FACET` deliberately omits reviews) and `TYPE_ALIASES` has no `reviews` key, so it reaches the final "Fallback for any other record in records or .agents" branch and returns `"other"`. `selectors.resolve`'s direct-path precedence then hands the file back regardless of the `other` sweep exclusion (`selectors._OTHER_SWEEP_SKIP_DIRS`), so only a direct path reaches it; a bare id6 does not (`aw set approved ab12cd --dry-run` printed `No artifact matched 'ab12cd'.` rc=2).
- F-03 `detect_artifact_type` callers outside the setter: `runner_shared` (plan-path refusal), `check_engine` (dangling index entry lookup, which skips `other`), `artifact_audit` (two sites, one defaulting an unknown canonical type to `plans`), `run_selection_policy.classify_paths`. Returning a new `reviews` type there would change `artifact_audit`'s fallback from `other` to `plans`. Hence the refusal is placed in `run_set_command`, the one mutating surface the bug names.
- F-04 The type-scoped spellings `aw ipd set approved <review path>`, `aw specs set <review path> --status approved` and `aw backlog set <review path> --status done` already refuse (re-measured at review) (`Type mismatch ... type ['other'] ... scoped to 'plans'`, rc=2), but `aw set other approved <review path>` would pass that check because the record IS typed `other`; E-01(c) covers it.
- F-05 `tests/test_reviews_type_noun_surface.py` (from plan `ybf6za`) guards only the `TYPE_BACKENDS` and `KNOWN_PRIMARY_TYPES` halves; nothing covers the `aw set` half.

## Proposed changes (ordered, validatable)

1. Failing tests (E-01).
2. Refusal in `run_set_command` derived from `selectors.NON_PRIMARY_RECORD_DIRS` (E-02).
3. Docstring correction (E-03) and CHANGELOG (E-04).
4. Regression run and commit (E-05).

## Deferred / out of scope (with reason)

None. Retyping reviews in `detect_artifact_type` was considered and decided against (OQ-01, F-03), so it leaves no outstanding obligation. comms, walkthroughs and roadmaps are primary types with their own handling and are unaffected by this bug.

## Scope check

- Over-scope: none.
- Under-scope: none; every spelling that can reach a review path (untyped, `other`-scoped, dry-run, relative path) is tested, and plans-scoped spellings already refuse (F-04).

## Required tests / validation

- `tests/test_set_refuses_review_record.py` (new, E-01) proves refusal plus byte-identity for four spellings and a positive control.
- Neighbouring modules `tests/test_reviews_type_noun_surface.py`, `tests/test_status_set.py`, `tests/test_review_record_classifier.py` and the routine suite stay green (E-05).

## Spec / documentation sync

- `agent_workflows/artifact_types.py` docstring updated (E-03); CHANGELOG `Fixed:` (E-04). No spec describes `aw set` on reviews, so no `.spec.md` is touched.

## Open questions

### OQ-01: Refuse in the setter or retype in detect_artifact_type?

- Blocking: no
- Status: resolved
- Owner: plan author
- Resolution or deferral rationale: Refuse in `run_set_command` (F-03): it is the only mutating surface named by the backlog item, and retyping would alter `artifact_audit`'s `plans` fallback and other callers' behavior. The backlog's "Likely root" is a diagnosis, not a requirement; the required outcome (exit 2 naming reviews, file byte-identical) is met.

## Validation and cross-check (verify before reporting done)

Validation-state rule: inspect evidence in a separate pass. Do not mark a `V-*` item complete from memory or from the matching execution checkmark. Accepted validation results: blocked, failed, pass, pending; terminal gate demands 'pass'. Runtime-demonstration reachability rule: for each `V-*` item demanding the software be observed acting (such as a run, a dispatch, or a transition)—as distinct from items demanding a diff, a file's content, or a test result, which are reachable by construction—name the code path that produces the observation or the sibling `E-*` that creates it, else the demand is UNDER-SCOPE.

- [x] V-01 validates E-01
  - Required evidence: Pasted pytest output of `tests/test_set_refuses_review_record.py` run against the unchanged code showing the four review cases FAILED and the positive control PASSED.
  - Observed evidence:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
cachedir: .pytest_cache
Using --randomly-seed=1892574370
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/p4xo1u
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 5 items

tests/test_set_refuses_review_record.py::test_set_positive_control_backlog_item PASSED [ 20%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[other_scoped] FAILED [ 40%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[untyped] FAILED [ 60%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[dry_run] FAILED [ 80%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[relative_path_in_cwd] FAILED [100%]

=================================== FAILURES ===================================
/mnt/md1/VC/agent-workflows/.aw/worktrees/p4xo1u/tests/test_set_refuses_review_record.py:120: AssertionError: Expected rc=2, got 0. Output: -    other       20260929-demo-01-ab12cd  draft → ?  approved
/mnt/md1/VC/agent-workflows/.aw/worktrees/p4xo1u/tests/test_set_refuses_review_record.py:120: AssertionError: Expected rc=2, got 0. Output: -    other       20260929-demo-01-ab12cd  draft → ?  approved
/mnt/md1/VC/agent-workflows/.aw/worktrees/p4xo1u/tests/test_set_refuses_review_record.py:120: AssertionError: Expected rc=2, got 0. Output: -    other       20260929-demo-01-ab12cd  draft → ?  approved  (dry-run)
/mnt/md1/VC/agent-workflows/.aw/worktrees/p4xo1u/tests/test_set_refuses_review_record.py:120: AssertionError: Expected rc=2, got 0. Output: -    other       20260929-demo-01-ab12cd  draft → ?  to-review
=========================== short test summary info ============================
FAILED tests/test_set_refuses_review_record.py::test_set_refuses_review_record[other_scoped]
FAILED tests/test_set_refuses_review_record.py::test_set_refuses_review_record[untyped]
FAILED tests/test_set_refuses_review_record.py::test_set_refuses_review_record[dry_run]
FAILED tests/test_set_refuses_review_record.py::test_set_refuses_review_record[relative_path_in_cwd]
========================= 4 failed, 1 passed in 3.74s ==========================
```
  - Result: pass

- [x] V-02 validates E-02
  - Required evidence: Pasted `git diff agent_workflows/status_set.py` showing the helper derived from `selectors.NON_PRIMARY_RECORD_DIRS` and the refusal in `run_set_command` with no change to `detect_artifact_type`; plus pasted pytest output of the new module with all cases PASSED; plus a pasted manual run (code path `status_set.run_set_command`, created by E-02) in a temp repo of `aw set approved <review path> --yes --no-commit` showing the refusal message and `rc=2`, and `git status --porcelain` empty afterwards.
  - Observed evidence:
```diff
diff --git a/agent_workflows/status_set.py b/agent_workflows/status_set.py
index 269721901..2e84a3587 100644
--- a/agent_workflows/status_set.py
+++ b/agent_workflows/status_set.py
@@ -208,6 +208,22 @@ def detect_artifact_type(path: Path, repo_root: Path) -> str | None:
     return None


+def _non_lifecycle_record_type(path: Path, repo_root: Path) -> str | None:
+    """Return owning type name when path resolves inside any non-primary record dir, else None."""
+    try:
+        resolved = path.resolve()
+    except OSError:
+        return None
+    for t in _sel.NON_PRIMARY_RECORD_DIRS:
+        for d in _sel.record_dirs(repo_root, t):
+            try:
+                if resolved.is_relative_to(d.resolve()):
+                    return t
+            except (ValueError, OSError):
+                continue
+    return None
+
+
 def read_artifact_record(
     path: Path, repo_root: Path, default_type: str | None = None
 ) -> ArtifactRecord | None:
@@ -2996,6 +3012,17 @@ def run_set_command(
                 term.status("fail", f"No artifact matched '{tok}'.")
             return 2

+        for m in matches:
+            t = _non_lifecycle_record_type(m.path, repo_root)
+            if t:
+                term.status(
+                    "fail",
+                    f"Selector '{tok}' resolved to a {t} record ({m.path}); "
+                    f"{t} records have no status lifecycle, so aw set cannot change them. "
+                    "Refusing before making changes.",
+                )
+                return 2
+
         # IPD laykok E-07: kind-aware ambiguity for the MUTATING `set` verb. A setid legitimately
         # transitions a whole Set (act on all, no --force); a UNIQUE-id collision (id6/path/stem)
         # ALWAYS refuses; a filename SUBSTRING multi-match refuses unless --force. Determine the
```
New test module:
```
============================= test session starts ==============================
platform linux -- Python 3.14.6, pytest-8.2.2, pluggy-1.6.0 -- python3
cachedir: .pytest_cache
Using --randomly-seed=4033036682
rootdir: /mnt/md1/VC/agent-workflows/.aw/worktrees/p4xo1u
configfile: pyproject.toml
plugins: anyio-4.14.1, randomly-4.1.0, cov-7.1.0, xdist-3.8.0
collecting ... collected 5 items

tests/test_set_refuses_review_record.py::test_set_refuses_review_record[dry_run] PASSED [ 20%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[relative_path_in_cwd] PASSED [ 40%]
tests/test_set_refuses_review_record.py::test_set_positive_control_backlog_item PASSED [ 60%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[other_scoped] PASSED [ 80%]
tests/test_set_refuses_review_record.py::test_set_refuses_review_record[untyped] PASSED [100%]

============================== 5 passed in 3.58s ===============================
```
Manual run in temp repo:
```
$ aw set approved .aw/records/reviews/20260929-demo-01-ab12cd-x.review.md --yes --no-commit
FAIL     Selector '/tmp/repo/.aw/records/reviews/20260929-demo-01-ab12cd-x.review.md' resolved to a reviews record (/tmp/repo/.aw/records/reviews/20260929-demo-01-ab12cd-x.review.md); reviews records have no status lifecycle, so aw set cannot change them. Refusing before making changes.
exit code: 2
git status --porcelain: ''
```
  - Result: pass

- [x] V-03 validates E-03
  - Required evidence: Pasted `git diff agent_workflows/artifact_types.py` showing the docstring no longer says `aw set` does not yet refuse a review path.
  - Observed evidence:
```diff
diff --git a/agent_workflows/artifact_types.py b/agent_workflows/artifact_types.py
index a7edaa85a..bd423d16f 100644
--- a/agent_workflows/artifact_types.py
+++ b/agent_workflows/artifact_types.py
@@ -18,8 +18,8 @@ ONE DELIBERATE BEHAVIOR CHANGE, per the maintainer's UNION ruling (2026-09-01, s
 carries. It was previously rejected (`aw check reviews` exited 2 with "unknown artifact type"). It is
 deliberately NOT a `TYPE_BACKENDS` key and has no status lifecycle, so it stays out of
 `selectors.KNOWN_PRIMARY_TYPES` (guarded for both `TYPE_BACKENDS` and `KNOWN_PRIMARY_TYPES` by
-`tests/test_reviews_type_noun_surface.py`), while `aw set` does not yet refuse a review path
-(backlog `9pu7sf`).
+`tests/test_reviews_type_noun_surface.py`), and `aw set` refuses a review path at exit 2
+(`status_set.run_set_command`, backlog `9pu7sf`, guarded by `tests/test_set_refuses_review_record.py`).
 """

 from __future__ import annotations
```
  - Result: pass

- [x] V-04 validates E-04
  - Required evidence: Pasted `git diff CHANGELOG.md` showing one `- Fixed:` bullet with no em or en dash.
  - Observed evidence:
```diff
diff --git a/CHANGELOG.md b/CHANGELOG.md
index fd556244e..1548c583b 100644
--- a/CHANGELOG.md
+++ b/CHANGELOG.md
@@ -24,6 +24,7 @@ now under way. The direction of the 2.x line (in progress, not all shipped in th

 Major storage-layout boundary. The logical model (D126-D129) was superseded by the PHYSICAL `.aw/` hierarchy specified in `20260810-1447-01-physical-aw-hierarchy-placement-and-migration.spec.md` (D130, D134-D137), which the framework now implements and has migrated its own repository onto:

+- Fixed: aw set now refuses a review record (exit 2, file untouched) instead of writing a Status line and workflow history into it, since reviews have no status lifecycle.
 - Added: Test suite split into a fast core regression tier (under 30s wall time budget on 6 workers) that covers every first-party module and every declared leaf command, and a thorough tier for pre-push, CI, and pre-release validation via aw suite --thorough and make test-all.
 - Fixed: `runner_shared.check_lane_hook_bypass` and `leak_sanitizer._staged_files` now pass `--no-renames` to `git diff`, ensuring deleted rename sources are removed in disposable worktrees and renamed files are scanned for staged leaks even when git rename detection is enabled.
 - Fixed: `aw releases readiness` now reports gates whose input files are absent as not-applicable instead of failing (or vacuously passing), so release review is usable in managed repositories.
```
  - Result: pass

- [x] V-05 validates E-05
  - Required evidence: Pasted runner output of the four-module narrowed run and of bare `python3 -m pytest` including the `N passed` summary line with 0 failed; plus `git show --stat HEAD` listing exactly the four Scope-Paths files.
  - Observed evidence:
    Narrowed four-module run:
    ```
    python3 -m pytest -o addopts="" -v tests/test_set_refuses_review_record.py tests/test_reviews_type_noun_surface.py tests/test_status_set.py tests/test_review_record_classifier.py
    ============================= 136 passed in 44.35s =============================
    ```
    Routine bare test suite:
    ```
    python3 -m pytest
    =========================== short test summary info ============================
    745 passed in 30.62s
    ```
    Commit git show:
    ```
    $ git show --stat HEAD
    commit 0ad6e966a652d0927d63bae647f72628a31e842b (HEAD -> aw/lane/p4xo1u)
    Author: Gabriele Fariello <gabriele.fariello@gmail.com>
    Date:   Fri Oct 16 19:58:16 2026 -0400

        work(p4xo1u): aw set refuses a review record instead of writing a lifecycle into it

        AW-Run: run-20261016T221413Z-3466881
        AW-Item: p4xo1u
        AW-Runner: aw agy run

     CHANGELOG.md                            |   1 +
     agent_workflows/artifact_types.py       |   4 +-
     agent_workflows/status_set.py           |  27 +++++
     tests/test_set_refuses_review_record.py | 185 ++++++++++++++++++++++++++++++++
     4 files changed, 215 insertions(+), 2 deletions(-)
    ```
  - Result: pass

## Approval and execution gate

- Size assessment: standard
- Cohesion rationale: not required

Execute only after human approval (`Status: approved`). Execution contract:

- Open questions: OQ-01 is resolved; nothing blocks execution.
- Scope fence: `- Scope-Paths:` declares what this plan edits. An edit outside it is allowed when needed and must be justified at finalize (`--scope-reason`); do not stop over it. `detect_artifact_type` is deliberately left unchanged (F-03).
- Honesty: you MUST paste the ACTUAL runner output in each `V-*`; never claim a pass you did not run.
- Commits: path-scoped via `aw commit p4xo1u -- <paths>`; verify `git diff --cached --name-only` first; never `git add -A`, never push.
- Lifecycle: under `aw oc run` / `aw agy run` the runner owns finalize, so leave the plan in `pending/`. Executed by hand (`aw work begin p4xo1u`), finish with `aw ipd finalize p4xo1u --actor <agent/model> --message <summary> --apply` once every `V-*` is `pass` and `aw ipd lint --phase pre-transition` conforms; never `git mv` the plan to `executed/`.
