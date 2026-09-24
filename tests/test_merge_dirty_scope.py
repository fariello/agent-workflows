#!/usr/bin/env python3
"""mergedirty-01 (`fujm0y`): the pre-merge dirty guard is asked about THE PATHS THE MERGE WOULD WRITE.

THE DEFECT, REPRODUCED RATHER THAN ARGUED. `runner_shared.integrate_lane_branch` called
`dirty_tree_overlap(repo, lane.changed_files)`, so main's dirty paths were compared only against files
THE LANE changed. A non-fast-forward merge also writes files the lane never touched - commits that
landed on main since the lane base, and renames of lane-touched files - and those were outside the
check. MEASURED (git 2.43.0): the lane changed only `a.txt`; main renamed `a.txt` to `renamed.txt` and
was dirty there; the guard returned `[]` ("clear") and `git merge --no-ff` then failed with "Your local
changes to the following files would be overwritten by merge: renamed.txt". The guard passed and the
merge died.

WHY IT MATTERS NOW rather than being a cosmetic message defect. Sibling `51vw4y` made the
dirty-overlap refusal (`integration-blocked`) NON-TERMINAL via a defer/poll/ask ladder while a real
conflict (`merge-conflict`) stayed terminal. With that ladder landed, classifying transient co-worker
dirt through the wrong arm converts a recoverable deferral into permanent in-run loss plus a
dependency cascade.

WHY A MOCKED PATH SET WOULD PROVE NOTHING, which is why every case here drives REAL git in a throwaway
repository. The bug was in WHICH paths get computed from real git history, so a test that handed the
function a pre-built list passed against the broken code.

THE ANTI-REGRESSION HALF IS THE LOAD-BEARING ONE. Widening the input set to a REFUSAL can only ever
refuse MORE, so the cases that must STILL INTEGRATE carry as much weight as the case that must now
refuse. One of them is mandatory and named: it is the fixture that DISPROVED this plan's original
algorithm (the merge-base-to-both-tips union, finding F-7). Base holds `a.txt` and `b.txt`; the lane
changes only `a.txt`; main advances `b.txt` with a commit AND is left dirty on `b.txt`. The union is
`['a.txt', 'b.txt']`, so a guard fed the union REFUSES - yet the real merge exits 0 and the co-worker's
dirty `b.txt` survives intact. If `test_the_union_disproof_case_STILL_INTEGRATES` fails, the
implementation is computing a union and `merge_write_set`'s docstring says why that is wrong.

Git floor: `git merge-tree --write-tree` requires git >= 2.38 (measured against 2.43.0 here).
`merge_write_set` returns None on the usage error an older git raises, and the guard then falls back to
the lane's `changed_files`, i.e. to the pre-change behavior, rather than checking nothing.
"""

from __future__ import annotations

import pathlib
import subprocess
import tempfile
import unittest
from unittest import mock

from agent_workflows import agy_runipd, oc_runipd, runner_shared, worktree_lease

#: Both hosts, exercised through THEIR OWN wrappers so the host-specific bindings (`host_label`,
#: `run_checked`) are the ones under test rather than being bypassed by calling the shared function.
HOSTS = {"oc_runipd": oc_runipd, "agy_runipd": agy_runipd}


def _renamable_body() -> str:
    """Content long enough for git to score a move as a rename rather than an add plus a delete."""
    return "".join(f"line {i}\n" for i in range(40))


class MergeDirtyScopeFixture(unittest.TestCase):
    """A real repository, a real lane worktree, and a real merge. No mocks anywhere."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

    def git(self, cwd: pathlib.Path, *args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
        ).stdout.strip()

    def git_rc(self, cwd: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)

    def make_repo(self, name: str = "repo") -> pathlib.Path:
        repo = self.root / name
        repo.mkdir()
        self.git(repo, "init", "-q", "-b", "main")
        self.git(repo, "config", "user.email", "test@example.invalid")
        self.git(repo, "config", "user.name", "Test")
        self.git(repo, "config", "commit.gpgsign", "false")
        (repo / "a.txt").write_text(_renamable_body(), encoding="utf-8")
        (repo / "b.txt").write_text("b1\n", encoding="utf-8")
        self.git(repo, "add", "a.txt", "b.txt")
        self.git(repo, "commit", "-qm", "base")
        return repo

    def make_lane(
        self,
        repo: pathlib.Path,
        id6: str,
        *,
        edits: dict[str, str] | None = None,
        rename: tuple[str, str] | None = None,
    ):
        """A real lane worktree on its own branch, committing ``edits`` and/or a ``rename``."""
        base = self.git(repo, "rev-parse", "HEAD")
        branch = f"aw/lane/{id6}"
        self.git(repo, "branch", branch)
        wt = self.root / f"wt-{id6}"
        self.git(repo, "worktree", "add", "-q", str(wt), branch)
        if rename is not None:
            self.git(wt, "mv", rename[0], rename[1])
        for path, body in (edits or {}).items():
            target = wt / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(body, encoding="utf-8")
            self.git(wt, "add", path)
        self.git(wt, "commit", "-qm", f"lane {id6}: work")
        return worktree_lease.WorktreeHandle(
            lane_id=id6, path=wt, branch=branch, base_commit=base
        )

    def lane_changed_files(self, repo: pathlib.Path, handle) -> tuple[str, ...]:
        """The OLD input set: the lane's own diff, as `build_lane_outcome` derives it."""
        return runner_shared.build_lane_outcome(
            repo, handle, handle.lane_id, run_checked=oc_runipd.run_checked
        ).changed_files

    def integrate(self, host: str, repo: pathlib.Path, handle):
        """Integrate through the named HOST's own wrapper, with a passing revalidation runner."""
        return HOSTS[host].integrate_lane_branch(
            repo, handle, handle.lane_id, lambda _diff, _files: True
        )


class MergeWriteSetTests(MergeDirtyScopeFixture):
    """What `merge_write_set` computes, measured against what the real merge then does."""

    def test_the_reproduced_rename_case_names_the_path_the_lane_never_touched(self):
        """E-02's central claim: `['renamed.txt']` where the lane's own diff said `['a.txt']`.

        This is the fixture the defect was reproduced with, so it is the one that must change answer.
        """
        repo = self.make_repo()
        handle = self.make_lane(repo, "ren001", edits={"a.txt": "lane content\n"})
        self.git(repo, "mv", "a.txt", "renamed.txt")
        self.git(repo, "commit", "-qm", "main renames a.txt")
        (repo / "renamed.txt").write_text("co-worker dirty\n", encoding="utf-8")

        self.assertEqual(self.lane_changed_files(repo, handle), ("a.txt",))
        write_set = runner_shared.merge_write_set(repo, handle.branch)
        self.assertEqual(write_set, ["renamed.txt"])
        # The OLD input set says clear; the NEW one names the path. Both in the SAME fixture, which is
        # what makes this a before/after rather than two unrelated measurements.
        self.assertEqual(
            runner_shared.dirty_tree_overlap(
                repo, self.lane_changed_files(repo, handle)
            ),
            [],
            "the pre-change input set is what let this through",
        )
        self.assertEqual(
            runner_shared.dirty_tree_overlap(repo, write_set or []),
            ["renamed.txt"],
        )
        # And the real merge really does fail here, so blocking is correct and not merely stricter.
        merged = self.git_rc(
            repo, "merge", "--no-ff", "--no-edit", "-m", "m", handle.branch
        )
        self.assertNotEqual(merged.returncode, 0)
        self.assertIn("renamed.txt", merged.stdout + merged.stderr)

    def test_the_union_disproof_case_is_EMPTY(self):
        """F-7: the merge-base-to-both-tips union returns `['a.txt', 'b.txt']` here and is WRONG.

        Main ADVANCED `b.txt` and is DIRTY on `b.txt`; the lane touched only `a.txt`. The merge does
        not write `b.txt`, so the write set must not name it. A `['b.txt']` result means a union was
        implemented instead of the merge-result diff.
        """
        repo = self.make_repo()
        handle = self.make_lane(repo, "uni001", edits={"a.txt": "lane content\n"})
        (repo / "b.txt").write_text("b2\n", encoding="utf-8")
        self.git(repo, "commit", "-qm", "main advances b.txt", "--", "b.txt")
        (repo / "b.txt").write_text("co-worker dirty b\n", encoding="utf-8")

        # The union, computed here so the disproof is visible rather than asserted from prose.
        base = self.git(repo, "merge-base", "HEAD", handle.branch)
        union = sorted(
            set(self.git(repo, "diff", "--name-only", base, "HEAD").split())
            | set(self.git(repo, "diff", "--name-only", base, handle.branch).split())
        )
        self.assertEqual(union, ["a.txt", "b.txt"], "the union DOES name b.txt")

        write_set = runner_shared.merge_write_set(repo, handle.branch)
        self.assertEqual(write_set, ["a.txt"], "the merge writes only a.txt")
        self.assertEqual(runner_shared.dirty_tree_overlap(repo, write_set or []), [])

    def test_a_lane_rename_reports_BOTH_endpoints_because_the_merge_writes_BOTH(self):
        """`--no-renames` on the diff is load-bearing, not stylistic.

        With rename detection ON, a lane renaming `a` -> `b` reports only `b`, yet the merge must still
        DELETE `a` in main, so dirt on `a` would pass the guard and git would refuse the merge. The
        working tree is written at both paths, so both must be in the set.
        """
        repo = self.make_repo()
        handle = self.make_lane(repo, "two001", rename=("a.txt", "moved.txt"))
        (repo / "a.txt").write_text("co-worker dirty\n", encoding="utf-8")

        self.assertEqual(
            runner_shared.merge_write_set(repo, handle.branch), ["a.txt", "moved.txt"]
        )
        self.assertEqual(
            runner_shared.dirty_tree_overlap(repo, ["a.txt", "moved.txt"]), ["a.txt"]
        )
        merged = self.git_rc(
            repo, "merge", "--no-ff", "--no-edit", "-m", "m", handle.branch
        )
        self.assertNotEqual(
            merged.returncode, 0, "the real merge refuses, so blocking is right"
        )

    def test_a_CONFLICTING_merge_yields_UNKNOWN_and_never_a_fabricated_empty_set(self):
        """OQ-01: a conflict is `merge-conflict` (terminal) and must not be reclassified as dirt.

        `git merge-tree --write-tree` exits non-zero on a conflict. Returning `[]` there would tell the
        guard "the merge writes nothing", i.e. "clear", which is the fail-open shape this plan removes.
        `None` means UNKNOWN, and the caller falls back to the lane's own `changed_files`.
        """
        repo = self.make_repo()
        handle = self.make_lane(repo, "cnf001", edits={"a.txt": "lane side\n"})
        (repo / "a.txt").write_text("main side\n", encoding="utf-8")
        self.git(repo, "commit", "-qm", "main writes a.txt", "--", "a.txt")

        probe = self.git_rc(repo, "merge-tree", "--write-tree", "HEAD", handle.branch)
        self.assertNotEqual(probe.returncode, 0, "this fixture must really conflict")
        result = runner_shared.merge_write_set(repo, handle.branch)
        self.assertIsNone(result)
        # Stated explicitly because `[]` and `None` are both falsy: the DISTINCTION is the contract.
        # An empty list would be intersected with main's dirt and yield "clear".
        self.assertNotEqual(
            result, [], "UNKNOWN must not be spelled as an empty path set"
        )

    def test_an_UNMERGEABLE_REF_is_UNKNOWN_too(self):
        """The other non-zero exit: nothing to merge. Still unknown, still never `[]`."""
        repo = self.make_repo()
        self.assertIsNone(runner_shared.merge_write_set(repo, "aw/lane/does-not-exist"))

    def test_a_git_WITHOUT_write_tree_is_UNKNOWN_so_the_guard_falls_back(self):
        """F-11: the git floor is >= 2.38, and an older git must degrade to the old behavior.

        Simulated by making the plumbing call fail the way an unsupported flag fails (rc 129), which is
        what an older git does with `--write-tree`. The point is the CONTRACT: unknown, not empty.
        """
        repo = self.make_repo()
        real = runner_shared._run_git

        def older_git(r, args, **kwargs):
            if args[:1] == ["merge-tree"]:
                return 129, "", "error: unknown option `write-tree'"
            return real(r, args, **kwargs)

        with mock.patch.object(runner_shared, "_run_git", older_git):
            self.assertIsNone(runner_shared.merge_write_set(repo, "main"))

    def test_it_states_the_GIT_VERSION_it_was_measured_against(self):
        """Not an assertion about behavior: a recorded floor, so a regression on an old git is legible."""
        version = subprocess.run(
            ["git", "--version"], capture_output=True, text=True, check=True
        ).stdout.strip()
        self.assertTrue(version.startswith("git version"), version)
        parts = version.split()[-1].split(".")
        major, minor = int(parts[0]), int(parts[1])
        self.assertGreaterEqual(
            (major, minor),
            (2, 38),
            f"`merge-tree --write-tree` needs git >= 2.38; found {version}",
        )


class DispositionTests(MergeDirtyScopeFixture):
    """E-03: WHICH disposition the reproduced case now gets, and that nothing became permissive."""

    def test_the_reproduced_case_is_INTEGRATION_BLOCKED_naming_the_path(self):
        """The observable win. Previously `merge-conflict` (terminal) via git's own refusal; now the
        pre-merge guard catches it and returns the deferrable arm with an accurate operator reason."""
        for host in HOSTS:
            with self.subTest(host=host):
                repo = self.make_repo(f"repo-{host}")
                handle = self.make_lane(
                    repo, f"rp{host[:4]}", edits={"a.txt": "lane\n"}
                )
                self.git(repo, "mv", "a.txt", "renamed.txt")
                self.git(repo, "commit", "-qm", "main renames")
                (repo / "renamed.txt").write_text("co-worker dirty\n", encoding="utf-8")
                head_before = self.git(repo, "rev-parse", "HEAD")

                integrated, reason, kind = self.integrate(host, repo, handle)

                self.assertFalse(integrated, reason)
                self.assertEqual(kind, "merge-retry")
                self.assertIn("renamed.txt", reason)
                self.assertIn("un-owned dirty paths", reason)
                # The deferrable arm is the one the ladder re-attempts; that is the whole point.
                self.assertTrue(runner_shared.classify_integration_refusal(kind))
                # Main is exactly as found and the co-worker's edit is untouched.
                self.assertEqual(self.git(repo, "rev-parse", "HEAD"), head_before)
                self.assertEqual(
                    (repo / "renamed.txt").read_text(encoding="utf-8"),
                    "co-worker dirty\n",
                )
                self.assertIn(
                    handle.branch, self.git(repo, "branch", "--format=%(refname:short)")
                )

    def test_the_refusal_reason_tells_NOBODY_to_touch_un_owned_work(self):
        """`z2isfg` wording discipline: AGENTS.md forbids touching another party's work, so the
        operator-facing reason must not suggest committing, stashing, resetting or cleaning it."""
        repo = self.make_repo()
        handle = self.make_lane(repo, "wrd001", edits={"a.txt": "lane\n"})
        self.git(repo, "mv", "a.txt", "renamed.txt")
        self.git(repo, "commit", "-qm", "main renames")
        (repo / "renamed.txt").write_text("co-worker dirty\n", encoding="utf-8")

        _integrated, reason, _kind = self.integrate("oc_runipd", repo, handle)
        for forbidden in (
            "git stash",
            "git reset",
            "git clean",
            "stash them",
            "discard",
        ):
            self.assertNotIn(forbidden, reason)
        for dash in ("\u2014", "\u2013"):
            self.assertNotIn(
                dash, reason, "no em or en dashes in operator-facing prose"
            )

    # ---- the anti-regression set: every case that integrated before must still integrate ----------

    def test_a_clean_main_still_FAST_FORWARDS(self):
        for host in HOSTS:
            with self.subTest(host=host):
                repo = self.make_repo(f"ff-{host}")
                handle = self.make_lane(
                    repo, f"ff{host[:4]}", edits={"a.txt": "lane\n"}
                )
                integrated, reason, kind = self.integrate(host, repo, handle)
                self.assertTrue(integrated, reason)
                self.assertEqual(kind, "integrated")
                self.assertIn("fast-forward", reason)
                self.assertEqual((repo / "a.txt").read_text(encoding="utf-8"), "lane\n")

    def test_a_clean_ADVANCED_main_still_NON_FF_MERGES(self):
        for host in HOSTS:
            with self.subTest(host=host):
                repo = self.make_repo(f"adv-{host}")
                handle = self.make_lane(
                    repo, f"ad{host[:4]}", edits={"a.txt": "lane\n"}
                )
                (repo / "other.txt").write_text("moved on\n", encoding="utf-8")
                self.git(repo, "add", "other.txt")
                self.git(repo, "commit", "-qm", "main advances")
                integrated, reason, kind = self.integrate(host, repo, handle)
                self.assertTrue(integrated, reason)
                self.assertEqual(kind, "integrated")
                self.assertIn("non-ff", reason)

    def test_dirt_on_a_NON_OVERLAPPING_path_still_integrates_and_SURVIVES(self):
        """Git only writes the paths the merge result changes, so disjoint dirt is not this guard's
        business and must not become it. The dirty content is asserted INTACT afterwards."""
        for host in HOSTS:
            with self.subTest(host=host):
                repo = self.make_repo(f"dis-{host}")
                handle = self.make_lane(
                    repo, f"di{host[:4]}", edits={"a.txt": "lane\n"}
                )
                (repo / "b.txt").write_text("co-worker dirty b\n", encoding="utf-8")
                integrated, reason, kind = self.integrate(host, repo, handle)
                self.assertTrue(integrated, reason)
                self.assertEqual(kind, "integrated")
                self.assertEqual(
                    (repo / "b.txt").read_text(encoding="utf-8"), "co-worker dirty b\n"
                )

    def test_the_union_disproof_case_STILL_INTEGRATES(self):
        """MANDATORY (F-7). Main ADVANCED `b.txt` and is DIRTY on `b.txt`; the lane touched only
        `a.txt`. The merge succeeds and the co-worker's `b.txt` survives, so refusing here would be a
        FAILURE of this plan rather than a stricter success. A failure here means a union was built."""
        for host in HOSTS:
            with self.subTest(host=host):
                repo = self.make_repo(f"f7-{host}")
                handle = self.make_lane(
                    repo, f"f7{host[:4]}", edits={"a.txt": "lane\n"}
                )
                (repo / "b.txt").write_text("b2\n", encoding="utf-8")
                self.git(repo, "commit", "-qm", "main advances b.txt", "--", "b.txt")
                (repo / "b.txt").write_text("co-worker dirty b\n", encoding="utf-8")

                integrated, reason, kind = self.integrate(host, repo, handle)

                self.assertTrue(integrated, f"the real merge succeeds here: {reason}")
                self.assertEqual(kind, "integrated")
                self.assertEqual(
                    (repo / "b.txt").read_text(encoding="utf-8"),
                    "co-worker dirty b\n",
                    "the co-worker's dirty edit must survive untouched",
                )
                self.assertEqual((repo / "a.txt").read_text(encoding="utf-8"), "lane\n")

    def test_a_GENUINE_CONFLICT_still_returns_MERGE_CONFLICT(self):
        """Only the dirty-overlap case moves. `merge-conflict` must stay reachable and TERMINAL, or
        the ladder would spin against a failure repetition cannot fix."""
        for host in HOSTS:
            with self.subTest(host=host):
                repo = self.make_repo(f"cf-{host}")
                handle = self.make_lane(
                    repo, f"cf{host[:4]}", edits={"a.txt": "lane side\n"}
                )
                (repo / "a.txt").write_text("main side\n", encoding="utf-8")
                self.git(repo, "commit", "-qm", "main writes a.txt", "--", "a.txt")
                head_before = self.git(repo, "rev-parse", "HEAD")

                integrated, reason, kind = self.integrate(host, repo, handle)

                self.assertFalse(integrated, reason)
                self.assertEqual(kind, "merge-refused")
                self.assertFalse(runner_shared.classify_integration_refusal(kind))
                # Main is clean: HEAD unmoved, no markers, no in-progress merge.
                self.assertEqual(self.git(repo, "rev-parse", "HEAD"), head_before)
                self.assertEqual(self.git(repo, "status", "--short"), "")
                self.assertNotIn(
                    "<<<<<<<", (repo / "a.txt").read_text(encoding="utf-8")
                )
                self.assertFalse(runner_shared.merge_in_progress(repo))

    def test_an_UNKNOWN_write_set_falls_back_to_the_LANE_diff_and_still_refuses_overlap(
        self,
    ):
        """The fallback must be the PREVIOUS behavior, not "check nothing".

        With `merge_write_set` forced to UNKNOWN, dirt on a path the LANE changed must still refuse: an
        older git loses the widening, and must not also lose the guard it already had.
        """
        repo = self.make_repo()
        handle = self.make_lane(repo, "fbk001", edits={"a.txt": "lane\n"})
        (repo / "a.txt").write_text("co-worker dirty\n", encoding="utf-8")
        with mock.patch.object(
            runner_shared, "merge_write_set", lambda _repo, _branch: None
        ):
            integrated, reason, kind = self.integrate("oc_runipd", repo, handle)
        self.assertFalse(integrated)
        self.assertEqual(kind, "merge-retry")
        self.assertIn("a.txt", reason)


class OneImplementationTests(unittest.TestCase):
    """E-04: both hosts reach ONE shared implementation, asserted by object identity.

    After `6sb3yu` there is a single function, so running the same assertions twice against two symbols
    would prove less than showing the two names are the same object.
    """

    def test_both_drivers_resolve_dirty_tree_overlap_to_the_SAME_object(self):
        for name, module in HOSTS.items():
            with self.subTest(host=name):
                self.assertIs(
                    module.dirty_tree_overlap, runner_shared.dirty_tree_overlap
                )


if __name__ == "__main__":  # pragma: no cover - manual invocation
    unittest.main()
