"""Regression tests for IPD awretrofit Order 06: repo-scoped verbs climb to the project root.

Maintainer report (release-review run 20260817-153418): `aw att` from a repo SUBDIRECTORY printed
nothing (repo-scoped verbs resolved bare cwd with no upward climb), and from a markerless dir the
empty output was indistinguishable from a clean project. This adds a git-style `find_project_root`
climb + a verbose no-project message, and these tests lock both behaviors (fail-before/pass-after).
"""

from __future__ import annotations

import argparse
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from agent_workflows import project_context as pc


def _make_project(root: Path) -> None:
    """Materialize a minimal AW project root (a `.aw/` with a durable class dir)."""
    (root / ".aw" / "records" / "plans").mkdir(parents=True)
    (root / ".aw" / "system").mkdir(parents=True)


class FindProjectRootTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp) / "repo"
        _make_project(self.repo)

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_from_repo_root(self):
        self.assertEqual(pc.find_project_root(self.repo), self.repo.resolve())

    def test_from_nested_subdir(self):
        nested = self.repo / ".aw" / "records" / "plans"
        self.assertEqual(pc.find_project_root(nested), self.repo.resolve())
        deep = self.repo / "a" / "b" / "c"
        deep.mkdir(parents=True)
        self.assertEqual(pc.find_project_root(deep), self.repo.resolve())

    def test_markerless_returns_none(self):
        bare = Path(self.tmp) / "nowhere"
        bare.mkdir()
        self.assertIsNone(pc.find_project_root(bare))

    def test_legacy_agents_marker(self):
        legacy = Path(self.tmp) / "legacyrepo"
        (legacy / ".agents" / "plans").mkdir(parents=True)
        self.assertEqual(
            pc.find_project_root(legacy / ".agents" / "plans"), legacy.resolve()
        )

    def test_stray_nested_aw_is_not_a_root(self):
        """A bare `.aw/` that holds only runtime state (no durable class) must NOT be a root -
        prevents the false positive where a stray `.aw/state/.aw/` shadows the real root."""
        stray = self.repo / ".aw" / "state" / ".aw" / "state"
        stray.mkdir(parents=True)
        # Climbing from inside the stray still resolves the REAL repo root, not the stray dir.
        self.assertEqual(
            pc.find_project_root(self.repo / ".aw" / "state"), self.repo.resolve()
        )

    def test_bare_git_ancestor_is_not_a_root(self):
        """A `.git` dir with no AW marker is not an AW project root (OQ-01)."""
        gitonly = Path(self.tmp) / "gitonly"
        (gitonly / ".git").mkdir(parents=True)
        self.assertIsNone(pc.find_project_root(gitonly))


class AttentionClimbTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.repo = Path(self.tmp) / "repo"
        _make_project(self.repo)
        self._cwd = os.getcwd()

    def tearDown(self):
        os.chdir(self._cwd)
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run_attention(self, extra=None):
        from agent_workflows import attention

        args = argparse.Namespace(
            dir=None, check=False, agent=False, format=None, all=False, no_color=True
        )
        if extra:
            for k, v in extra.items():
                setattr(args, k, v)
        # capture stdout + stderr + exit code
        import sys

        out, err = io.StringIO(), io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            rc = attention.run(args)
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        return rc, out.getvalue(), err.getvalue()

    def test_subdir_resolves_same_as_top(self):
        """`aw attention` from a repo subdir produces the same board as from the top."""
        os.chdir(self.repo)
        rc_top, out_top, _ = self._run_attention()
        sub = self.repo / ".aw" / "records" / "plans"
        os.chdir(sub)
        rc_sub, out_sub, _ = self._run_attention()
        self.assertEqual(rc_top, rc_sub)
        self.assertEqual(out_top, out_sub)

    def test_markerless_prints_no_project_message(self):
        """From a markerless dir, attention emits the verbose no-project guidance (not empty)."""
        bare = Path(self.tmp) / "nowhere"
        bare.mkdir()
        os.chdir(bare)
        rc, out, err = self._run_attention()
        self.assertEqual(rc, 3)
        self.assertIn("no AW project found", err)
        self.assertIn("--dir", err)
        self.assertEqual(out, "")

    def test_explicit_dir_bypasses_climb(self):
        """An explicit --dir is honored verbatim (no climb) even from a markerless cwd."""
        bare = Path(self.tmp) / "nowhere2"
        bare.mkdir()
        os.chdir(bare)
        rc, out, err = self._run_attention(extra={"dir": str(self.repo)})
        # With an explicit project --dir, it runs normally (no no-project message).
        self.assertNotIn("no AW project found", err)

    def test_check_on_markerless_is_valid(self):
        """--check stays fail-closed-valid (exit 0) when there is no project (nothing to violate)."""
        bare = Path(self.tmp) / "nowhere3"
        bare.mkdir()
        os.chdir(bare)
        rc, out, err = self._run_attention(extra={"check": True})
        self.assertEqual(rc, 0)
        self.assertIn("valid", out)


class ClimbMutationProbe(unittest.TestCase):
    """Falsifiable: with the climb reverted to bare-cwd, a subdir run finds no project (the pre-fix
    bug), proving the climb is load-bearing."""

    def test_reverting_climb_breaks_subdir(self):
        tmp = tempfile.mkdtemp()
        try:
            repo = Path(tmp) / "repo"
            _make_project(repo)
            sub = repo / ".aw" / "records" / "plans"
            # Real resolver: climbs to the repo root from the subdir.
            with mock.patch(
                "agent_workflows.project_context.Path.cwd", return_value=sub
            ):
                self.assertEqual(pc.resolve_verb_repo_root(None), repo.resolve())
            # Mutated (pre-fix bare-cwd): would return the subdir, which is_project_dir() rejects.
            with mock.patch.object(pc, "find_project_root", lambda start=None: None):
                with mock.patch(
                    "agent_workflows.project_context.Path.cwd", return_value=sub
                ):
                    self.assertEqual(pc.resolve_verb_repo_root(None), sub.resolve())
                    self.assertFalse(pc.is_project_dir(sub))
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
