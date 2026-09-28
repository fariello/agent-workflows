#!/usr/bin/env python3
"""Regression tests pinning foreign merge refusal on both hosts.

foreignmerge-01 (`g2z2pp`) E-05.

Validates that `integrate_lane_branch` refuses a checkout that is already mid-merge with
`INTEGRATION_REFUSAL_TRANSIENT` ("merge-retry"), attempting no merge and issuing no abort,
preserving the third party's staged index tree byte-identically. Tested through both hosts'
own wrappers (`oc_runipd.integrate_lane_branch` and `agy_runipd.integrate_lane_branch`).
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared

BOTH = ("oc_runipd", "agy_runipd")
_MODULES = {
    "oc_runipd": oc_runipd,
    "agy_runipd": agy_runipd,
    "runner_shared": runner_shared,
}


class ForeignMergeRefusalTests(unittest.TestCase):
    """Regression suite for foreign merge refusal across both hosts."""

    def _repo(self, tmp: pathlib.Path) -> pathlib.Path:
        """A throwaway repository with one initial commit on `main`."""
        repo = tmp / "repo"
        repo.mkdir()
        run = lambda *a: subprocess.run(  # noqa: E731
            list(a), cwd=repo, check=True, capture_output=True, text=True
        )
        run("git", "init", "-q", "-b", "main")
        run("git", "config", "user.email", "test@example.invalid")
        run("git", "config", "user.name", "Test")
        run("git", "config", "commit.gpgsign", "false")
        (repo / "base.txt").write_text("base content\n", encoding="utf-8")
        run("git", "add", "base.txt")
        run("git", "commit", "-qm", "base commit")
        return repo

    def _git(self, repo: pathlib.Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()

    def _lane(self, repo: pathlib.Path, id6: str, *, path: str, body: str):
        """Commit ``body`` at ``path`` on a lane branch and return a handle for it."""
        from agent_workflows import worktree_lease

        base = self._git(repo, "rev-parse", "HEAD")
        branch = f"aw/lane/{id6}"
        self._git(repo, "branch", branch)
        wt = repo.parent / f"wt-{id6}"
        self._git(repo, "worktree", "add", "-q", str(wt), branch)
        target = wt / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        self._git(wt, "add", path)
        self._git(wt, "commit", "-qm", f"lane {id6}: write {path}")
        return worktree_lease.WorktreeHandle(
            lane_id=id6, path=wt, branch=branch, base_commit=base
        )

    def _passing_runner(self):
        return lambda _diff, _files: True

    def _git_trace(self):
        """Record every `git` argv `runner_shared` runs, so tests can assert what was not run."""
        calls: list[list[str]] = []
        real = runner_shared._run_git

        def traced(r, args, **kwargs):
            calls.append(list(args))
            return real(r, args, **kwargs)

        return calls, mock.patch.object(runner_shared, "_run_git", traced)

    def _stage_foreign_merge(self, repo: pathlib.Path) -> tuple[str, str]:
        """Stage a third party's non-fast-forward merge in main without committing.

        Returns (foreign_branch_name, foreign_tip_sha).
        """
        self._git(repo, "branch", "foreign-branch")
        wt = repo.parent / "wt-foreign"
        self._git(repo, "worktree", "add", "-q", str(wt), "foreign-branch")
        (wt / "foreign.txt").write_text("foreign staged work\n", encoding="utf-8")
        self._git(wt, "add", "foreign.txt")
        self._git(wt, "commit", "-qm", "foreign commit")
        foreign_tip = self._git(wt, "rev-parse", "HEAD")
        # In main, merge foreign-branch with --no-ff --no-commit
        subprocess.run(
            ["git", "merge", "--no-ff", "--no-commit", "foreign-branch"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        )
        return "foreign-branch", foreign_tip

    def test_case_1_foreign_merge_refuses_without_abort_preserving_index(self):
        """Case 1 (the defect): stage third party merge in main; assert kind is merge-retry,
        no merge --abort in trace, MERGE_HEAD still set, staged set and write-tree identical.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                _fbranch, _ftip = self._stage_foreign_merge(repo)

                staged_before = self._git(
                    repo, "diff", "--cached", "--name-only"
                ).splitlines()
                tree_before = self._git(repo, "write-tree")
                self.assertTrue(runner_shared.merge_in_progress(repo))

                handle = self._lane(
                    repo, "fm1111", path="lane.txt", body="lane content\n"
                )

                calls, trace_ctx = self._git_trace()
                with trace_ctx:
                    integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                        repo, handle, "fm1111", self._passing_runner()
                    )

                self.assertFalse(
                    integrated, "Integration must be refused when main is mid-merge"
                )
                self.assertEqual(
                    kind,
                    runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
                    f"Refusal kind must be merge-retry, got {kind}: {reason}",
                )
                self.assertNotIn(
                    ["merge", "--abort"],
                    calls,
                    "No git merge --abort may be issued on a foreign merge",
                )
                self.assertTrue(
                    runner_shared.merge_in_progress(repo),
                    "MERGE_HEAD must remain set after foreign merge refusal",
                )
                staged_after = self._git(
                    repo, "diff", "--cached", "--name-only"
                ).splitlines()
                tree_after = self._git(repo, "write-tree")
                self.assertEqual(
                    staged_after, staged_before, "Staged set must be byte-identical"
                )
                self.assertEqual(
                    tree_after, tree_before, "Index tree hash must be byte-identical"
                )

    def test_case_2_genuine_conflict_still_aborts_leaving_main_clean(self):
        """Case 2 (genuine conflict unchanged): assert fail-merge, merge --abort IS in trace,
        merge_in_progress is False afterwards, main status is empty, and lane branch survives.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(
                    repo, "gc2222", path="clash.txt", body="lane version\n"
                )

                # Main commits conflicting change
                (repo / "clash.txt").write_text("main version\n", encoding="utf-8")
                self._git(repo, "add", "clash.txt")
                self._git(repo, "commit", "-qm", "main writes clash.txt")
                head_before = self._git(repo, "rev-parse", "HEAD")

                calls, trace_ctx = self._git_trace()
                with trace_ctx:
                    integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                        repo, handle, "gc2222", self._passing_runner()
                    )

                self.assertFalse(integrated, "Genuine conflict must not integrate")
                self.assertEqual(
                    kind,
                    runner_shared.INTEGRATION_REFUSAL_CONFLICT,
                    f"Refusal kind must be fail-merge, got {kind}: {reason}",
                )
                self.assertIn(
                    ["merge", "--abort"],
                    calls,
                    "Genuine conflict must execute git merge --abort",
                )
                self.assertFalse(
                    runner_shared.merge_in_progress(repo),
                    "MERGE_HEAD must be cleared after genuine conflict abort",
                )
                self.assertEqual(self._git(repo, "rev-parse", "HEAD"), head_before)
                self.assertEqual(self._git(repo, "status", "--short"), "")
                self.assertIn(
                    handle.branch,
                    self._git(repo, "branch", "--format=%(refname:short)"),
                )
                self.assertIn("clash.txt", reason)
                self.assertIn("merge-back conflict", reason)

    def test_case_3_ownership_predicate_directly(self):
        """Case 3 (ownership predicate directly): owns_merge_in_progress True mid-own-conflict,
        False for foreign merge, False on clean tree, False for octopus with foreign parent,
        and merge_head_commits returning both ids for octopus and [] for clean tree.
        """
        with tempfile.TemporaryDirectory() as tmp:
            repo = self._repo(pathlib.Path(tmp))
            handle = self._lane(repo, "op3333", path="clash.txt", body="lane version\n")

            # Clean tree
            self.assertFalse(
                runner_shared.owns_merge_in_progress(repo, branch=handle.branch),
                "Clean tree must return False",
            )
            self.assertEqual(runner_shared.merge_head_commits(repo), [])

            # Unresolvable branch
            self.assertFalse(
                runner_shared.owns_merge_in_progress(repo, branch="nonexistent-branch"),
                "Unresolvable branch must return False",
            )

            # Mid-own-conflict
            (repo / "clash.txt").write_text("main conflicting\n", encoding="utf-8")
            self._git(repo, "add", "clash.txt")
            self._git(repo, "commit", "-qm", "main writes clash.txt")
            lane_tip = self._git(repo, "rev-parse", handle.branch)

            subprocess.run(
                ["git", "merge", "--no-ff", handle.branch],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            self.assertTrue(runner_shared.merge_in_progress(repo))
            self.assertEqual(runner_shared.merge_head_commits(repo), [lane_tip])
            self.assertTrue(
                runner_shared.owns_merge_in_progress(repo, branch=handle.branch),
                "Mid-own-conflict must return True",
            )
            self._git(repo, "merge", "--abort")

            # Foreign merge
            _fbranch, ftip = self._stage_foreign_merge(repo)
            self.assertEqual(runner_shared.merge_head_commits(repo), [ftip])
            self.assertFalse(
                runner_shared.owns_merge_in_progress(repo, branch=handle.branch),
                "Foreign merge must return False for lane branch",
            )
            self._git(repo, "merge", "--abort")

            # Octopus merge
            self._git(repo, "branch", "branch-a")
            self._git(repo, "branch", "branch-b")
            wt_a = pathlib.Path(tmp) / "wt-a"
            wt_b = pathlib.Path(tmp) / "wt-b"
            self._git(repo, "worktree", "add", "-q", str(wt_a), "branch-a")
            self._git(repo, "worktree", "add", "-q", str(wt_b), "branch-b")
            (wt_a / "a.txt").write_text("a\n", encoding="utf-8")
            self._git(wt_a, "add", "a.txt")
            self._git(wt_a, "commit", "-qm", "add a")
            (wt_b / "b.txt").write_text("b\n", encoding="utf-8")
            self._git(wt_b, "add", "b.txt")
            self._git(wt_b, "commit", "-qm", "add b")
            tip_a = self._git(wt_a, "rev-parse", "HEAD")
            tip_b = self._git(wt_b, "rev-parse", "HEAD")

            subprocess.run(
                ["git", "merge", "--no-ff", "--no-commit", "branch-a", "branch-b"],
                cwd=repo,
                check=True,
                capture_output=True,
                text=True,
            )
            commits = runner_shared.merge_head_commits(repo)
            self.assertEqual(
                commits,
                [tip_a, tip_b],
                "merge_head_commits must return all commit ids in octopus MERGE_HEAD",
            )
            self.assertFalse(
                runner_shared.owns_merge_in_progress(repo, branch="branch-a"),
                "Octopus merge with foreign parent must return False",
            )
            self._git(repo, "merge", "--abort")

    def test_case_4_refusal_is_deferrable_and_distinguishable(self):
        """Case 4 (refusal is deferrable and distinguishable): classify_integration_refusal
        is True for returned kind, and reason names mid-merge condition and does not contain
        'merge-back conflict'.
        """
        for runner in BOTH:
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                self._stage_foreign_merge(repo)
                handle = self._lane(
                    repo, "df4444", path="lane.txt", body="lane content\n"
                )

                integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                    repo, handle, "df4444", self._passing_runner()
                )

                self.assertFalse(integrated)
                self.assertTrue(
                    runner_shared.classify_integration_refusal(kind),
                    f"Returned kind {kind} must be deferrable by classify_integration_refusal",
                )
                self.assertIn(
                    "already mid-merge",
                    reason,
                    f"Reason must name the mid-merge condition: {reason}",
                )
                self.assertIn("MERGE_HEAD", reason)
                self.assertNotIn(
                    "merge-back conflict",
                    reason,
                    f"Reason must NOT contain 'merge-back conflict': {reason}",
                )

    def test_case_5_impostor_case_third_party_merge_of_own_branch_not_aborted(self):
        """Case 5 (impostor case, finding PR-201, F-15): a third party merges this lane's own
        branch in main, hits conflict, resolves a path and stages an extra file.
        Assert returned kind is merge-retry, NO merge --abort in trace, MERGE_HEAD still set,
        staged set and index tree are byte-identical including the extra file.

        Tested under two timings:
        1. pre-staged: third party merge is staged before integration begins (E-03 pre-check catches it).
        2. race_window: third party merge occurs between E-03's check and driver's merge attempt
           (E-04's conjunction is what prevents the abort).
        """
        for runner in BOTH:
            # 1. Pre-staged impostor merge
            with self.subTest(
                runner=runner, timing="pre_staged"
            ), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(
                    repo, "imp551", path="clash.txt", body="lane content\n"
                )

                (repo / "clash.txt").write_text("main content\n", encoding="utf-8")
                self._git(repo, "add", "clash.txt")
                self._git(repo, "commit", "-qm", "main writes clash.txt")

                subprocess.run(
                    ["git", "merge", "--no-ff", handle.branch],
                    cwd=repo,
                    capture_output=True,
                    text=True,
                )
                self.assertTrue(runner_shared.merge_in_progress(repo))

                (repo / "clash.txt").write_text(
                    "human hand resolution\n", encoding="utf-8"
                )
                self._git(repo, "add", "clash.txt")
                (repo / "human_only.txt").write_text(
                    "precious human work\n", encoding="utf-8"
                )
                self._git(repo, "add", "human_only.txt")

                staged_before = self._git(
                    repo, "diff", "--cached", "--name-only"
                ).splitlines()
                tree_before = self._git(repo, "write-tree")
                self.assertIn("human_only.txt", staged_before)

                calls, trace_ctx = self._git_trace()
                with trace_ctx:
                    integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                        repo, handle, "imp551", self._passing_runner()
                    )

                self.assertFalse(
                    integrated, "Integration must be refused for impostor merge"
                )
                self.assertEqual(
                    kind,
                    runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
                    f"Refusal kind must be merge-retry: {reason}",
                )
                self.assertNotIn(
                    ["merge", "--abort"],
                    calls,
                    "Impostor merge must not issue git merge --abort",
                )
                self.assertTrue(
                    runner_shared.merge_in_progress(repo),
                    "MERGE_HEAD must remain set after refusal",
                )
                staged_after = self._git(
                    repo, "diff", "--cached", "--name-only"
                ).splitlines()
                tree_after = self._git(repo, "write-tree")
                self.assertEqual(
                    staged_after, staged_before, "Staged set must be byte-identical"
                )
                self.assertEqual(
                    tree_after, tree_before, "Index tree hash must be byte-identical"
                )
                self.assertTrue(
                    (repo / "human_only.txt").exists(),
                    "Human's uncommitted file must not be deleted",
                )

            # 2. Race-window impostor merge (peer stages between E-03 and merge attempt)
            with self.subTest(
                runner=runner, timing="race_window"
            ), tempfile.TemporaryDirectory() as tmp:
                repo = self._repo(pathlib.Path(tmp))
                handle = self._lane(
                    repo, "imp552", path="clash.txt", body="lane content\n"
                )

                (repo / "clash.txt").write_text("main content\n", encoding="utf-8")
                self._git(repo, "add", "clash.txt")
                self._git(repo, "commit", "-qm", "main writes clash.txt")

                race_state = {"staged": False, "staged_before": [], "tree_before": ""}
                calls: list[list[str]] = []
                real_run_git = runner_shared._run_git

                def race_traced_git(r, args, **kwargs):
                    # Intercept right before driver's first merge attempt
                    if args and args[0] == "merge" and not race_state["staged"]:
                        race_state["staged"] = True
                        subprocess.run(
                            ["git", "merge", "--no-ff", handle.branch],
                            cwd=repo,
                            capture_output=True,
                            text=True,
                        )
                        (repo / "clash.txt").write_text(
                            "human hand resolution\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "clash.txt"], cwd=repo, check=True
                        )
                        (repo / "human_only.txt").write_text(
                            "precious human work\n", encoding="utf-8"
                        )
                        subprocess.run(
                            ["git", "add", "human_only.txt"], cwd=repo, check=True
                        )
                        race_state["staged_before"] = self._git(
                            repo, "diff", "--cached", "--name-only"
                        ).splitlines()
                        race_state["tree_before"] = self._git(repo, "write-tree")
                    calls.append(list(args))
                    return real_run_git(r, args, **kwargs)

                with mock.patch.object(runner_shared, "_run_git", race_traced_git):
                    integrated, reason, kind = _MODULES[runner].integrate_lane_branch(
                        repo, handle, "imp552", self._passing_runner()
                    )

                self.assertFalse(
                    integrated,
                    "Integration must be refused for race-window impostor merge",
                )
                self.assertEqual(
                    kind,
                    runner_shared.INTEGRATION_REFUSAL_TRANSIENT,
                    f"Refusal kind must be merge-retry: {reason}",
                )
                self.assertNotIn(
                    ["merge", "--abort"],
                    calls,
                    "Race-window impostor merge must NOT issue git merge --abort",
                )
                self.assertTrue(
                    runner_shared.merge_in_progress(repo),
                    "MERGE_HEAD must remain set after refusal",
                )
                staged_after = self._git(
                    repo, "diff", "--cached", "--name-only"
                ).splitlines()
                tree_after = self._git(repo, "write-tree")
                self.assertEqual(
                    staged_after,
                    race_state["staged_before"],
                    "Staged set must be byte-identical",
                )
                self.assertEqual(
                    tree_after,
                    race_state["tree_before"],
                    "Index tree hash must be byte-identical",
                )
                self.assertTrue(
                    (repo / "human_only.txt").exists(),
                    "Human's uncommitted file must not be deleted in race window",
                )


if __name__ == "__main__":
    unittest.main()
