"""Tests for awcmdsurf Order 03: the noun-verb MUTATION verbs (rename/group/archive) + --no-refs."""

from __future__ import annotations

import io
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


def _write(p: Path, text: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class MutationVerbsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        # git-backed throwaway repo (renames use git mv); legacy .agents/plans layout so _dirs
        # resolves the local tree (mirrors tests/test_plans_refs.py convention).
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.root, check=True
        )
        subprocess.run(["git", "config", "user.name", "T"], cwd=self.root, check=True)
        self.pend = self.root / ".agents" / "plans" / "pending"
        self.plan_a = self.pend / "20260101-demo-01-aaa111-original.ipd.md"
        _write(
            self.plan_a,
            "# IPD\n\n- Id: aaa111\n- Set: demo (demo)\n- Status: draft\n\n## Workflow history\n- 2026-01-01 draft (t): x\n",
        )
        self.doc_b = self.root / ".agents" / "plans" / "INDEX.md"
        _write(self.doc_b, "citing 20260101-demo-01-aaa111-original.ipd.md here\n")
        subprocess.run(["git", "add", "-A"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.root, check=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.root)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def test_rename_preview_does_not_move(self):
        rc, out = self._run(["rename", "plans", "aaa111", "--slug", "newslug"])
        self.assertTrue(self.plan_a.exists())  # preview only
        self.assertIn("would rename", out)

    def test_rename_apply_updates_refs_and_preserves_id(self):
        rc, out = self._run(
            ["rename", "plans", "aaa111", "--slug", "newslug", "--apply"]
        )
        self.assertFalse(self.plan_a.exists())
        moved = list(self.pend.glob("*newslug*.ipd.md"))
        self.assertEqual(len(moved), 1)
        self.assertIn("- Id: aaa111", moved[0].read_text())  # Id preserved
        # doc B citation rewritten by default
        self.assertNotIn("aaa111-original", self.doc_b.read_text())

    def test_rename_no_refs_leaves_citation(self):
        rc, out = self._run(
            ["rename", "plans", "aaa111", "--slug", "newslug", "--no-refs", "--apply"]
        )
        self.assertIn("aaa111-original", self.doc_b.read_text())  # citation untouched

    def test_group_apply(self):
        rc, out = self._run(["group", "plans", "aaa111", "--set", "regrp", "--apply"])
        self.assertEqual(rc, 0)
        moved = list(self.pend.glob("*aaa111*.ipd.md"))
        self.assertEqual(len(moved), 1)
        self.assertIn("- Set: regrp", moved[0].read_text())

    def test_archive_backcompat_research_bare(self):
        rc, out = self._run(["archive"])  # bare research sweep preview
        self.assertEqual(rc, 0)

    def test_archive_plans_preview(self):
        rc, out = self._run(["archive", "plans"])
        self.assertEqual(rc, 0)

    def test_unsupported_type_verb(self):
        rc, out = self._run(["rename", "specs", "aaa111", "--slug", "x"])
        self.assertEqual(rc, 2)


if __name__ == "__main__":
    unittest.main()
