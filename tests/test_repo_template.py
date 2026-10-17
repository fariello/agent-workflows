"""Behavioral tests for shared temp git repository template helper (IPD 83nnyn E-09).

Tests:
1. Two copies are independent (file written/committed in one is absent from other and template).
2. A fresh copy has no commits (git rev-parse --verify -q HEAD exits 1).
3. A copy keeps the configured local identity (user.name, user.email).
4. git rev-parse --show-toplevel in a copy resolves to the copy path.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from tests.repo_template import copy_template_repo, get_template_repo


class TestRepoTemplate(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="test_repo_template_"))
        self.addCleanup(shutil.rmtree, str(self.tmp_dir), ignore_errors=True)

    def test_two_copies_are_independent(self) -> None:
        """A file written and committed in copy A is absent from copy B and template."""
        repo_a = copy_template_repo(self.tmp_dir / "repo_a")
        repo_b = copy_template_repo(self.tmp_dir / "repo_b")

        template = get_template_repo()

        file_in_a = repo_a / "extra.txt"
        file_in_a.write_text("hello from a\n", encoding="utf-8")
        subprocess.run(
            ["git", "add", "extra.txt"], cwd=repo_a, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "add extra in a"],
            cwd=repo_a,
            check=True,
            capture_output=True,
        )

        self.assertTrue(file_in_a.is_file())
        self.assertFalse((repo_b / "extra.txt").exists())
        self.assertFalse((template / "extra.txt").exists())

    def test_copy_has_no_commits(self) -> None:
        """Fresh copy has no commits: git rev-parse --verify -q HEAD exits 1."""
        repo = copy_template_repo(self.tmp_dir / "fresh_repo")
        res = subprocess.run(
            ["git", "rev-parse", "--verify", "-q", "HEAD"],
            cwd=repo,
            capture_output=True,
        )
        self.assertEqual(res.returncode, 1)

    def test_copy_keeps_local_identity(self) -> None:
        """Copy preserves configured local user.name and user.email."""
        repo = copy_template_repo(self.tmp_dir / "ident_repo")
        name = subprocess.check_output(
            ["git", "config", "user.name"], cwd=repo, text=True
        ).strip()
        email = subprocess.check_output(
            ["git", "config", "user.email"], cwd=repo, text=True
        ).strip()
        self.assertEqual(name, "Test User")
        self.assertEqual(email, "test@example.com")

    def test_show_toplevel_is_the_copy(self) -> None:
        """git rev-parse --show-toplevel in a copy resolves to the copy path."""
        repo = copy_template_repo(self.tmp_dir / "toplevel_repo")
        toplevel = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=repo, text=True
        ).strip()
        self.assertEqual(Path(toplevel).resolve(), repo.resolve())


if __name__ == "__main__":
    unittest.main()
