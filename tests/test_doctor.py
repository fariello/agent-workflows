"""Tests for awdoctor Order 03: `aw doctor` deep repo inspector (composes existing signals)."""

from __future__ import annotations

import io
import subprocess
import tempfile
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import doctor
from agent_workflows import engine, versioning


def _git(root, *args):
    subprocess.run(["git", *args], cwd=str(root), check=True, capture_output=True)


class DoctorTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _git(self.root, "init", "-q")
        _git(self.root, "config", "user.email", "t@e.com")
        _git(self.root, "config", "user.name", "T")
        (self.root / ".aw" / "records").mkdir(parents=True)
        # Seed an installed VERSION matching the packaged/source version so version-drift is clean.
        packaged = versioning.resolve_version(engine.resolve_source_root(None))
        (self.root / ".aw" / "VERSION").write_text(packaged + "\n", encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "init")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clean_repo_no_findings(self) -> None:
        drift = doctor.run_doctor(self.root)
        self.assertEqual(
            drift, [], [f"{d.location}:{d.rule}:{d.detail}" for d in drift]
        )

    def test_dirty_repo_flagged(self) -> None:
        (self.root / "newfile.txt").write_text("x", encoding="utf-8")
        drift = doctor.run_doctor(self.root)
        self.assertTrue(any(d.rule == "doctor.git-untracked" for d in drift))

    def test_run_no_findings_exit0(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = doctor.run(types.SimpleNamespace(dir=str(self.root), as_agent=False))
        self.assertEqual(rc, 0)
        self.assertIn("no findings", out.getvalue())

    def test_run_agent_tab_separated(self) -> None:
        (self.root / "x.txt").write_text("x", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = doctor.run(types.SimpleNamespace(dir=str(self.root), as_agent=True))
        self.assertEqual(rc, 1)
        self.assertIn("\t", out.getvalue())


if __name__ == "__main__":
    unittest.main()
