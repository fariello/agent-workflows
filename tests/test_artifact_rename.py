"""Tests for universal artifact rename CLI support (IPD renametypes-01, 53yczi)."""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


class TestArtifactRename(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="aw_test_rename_"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp_dir, ignore_errors=True))

        # Git-backed throwaway repo
        subprocess.run(["git", "init", "-q"], cwd=self.tmp_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.tmp_dir,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Tester"], cwd=self.tmp_dir, check=True
        )

        # Standard .aw layout
        self.records_dir = self.tmp_dir / ".aw" / "records"
        self.backlog_dir = self.records_dir / "backlog" / "open"
        self.specs_dir = self.records_dir / "specs"
        self.prompts_dir = self.records_dir / "prompts" / "pending"
        self.walkthroughs_dir = self.records_dir / "walkthroughs"
        self.roadmaps_dir = self.records_dir / "roadmaps"
        self.releases_dir = self.records_dir / "releases"
        self.plans_dir = self.records_dir / "plans" / "pending"

        for d in (
            self.backlog_dir,
            self.specs_dir,
            self.prompts_dir,
            self.walkthroughs_dir,
            self.roadmaps_dir,
            self.releases_dir,
            self.plans_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    def _run(self, argv: list[str]) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(argv + ["--dir", str(self.tmp_dir)])
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue() + err.getvalue()

    def test_rename_backlog_preview_and_apply(self):
        bkl = self.backlog_dir / "20260823-bklset-01-bk1234-old-task.backlog.md"
        bkl.write_text(
            "# Backlog: Old Task\n\n- Id: bk1234\n- Set: bklset\n- Order: 1\n- Status: open\n",
            encoding="utf-8",
        )

        # Referencing doc in plans
        ref_doc = self.plans_dir / "20260823-planset-01-pl1234-ref.ipd.md"
        ref_doc.write_text(
            "Citing 20260823-bklset-01-bk1234-old-task.backlog.md here.\n",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        # 1. Preview
        rc, out = self._run(["rename", "backlog", "bk1234", "--slug", "new-shiny-task"])
        self.assertEqual(rc, 0)
        self.assertTrue(bkl.exists())
        self.assertIn("would rename", out)
        self.assertIn("would rewrite", out)

        # 2. Apply
        rc, out = self._run(
            ["rename", "backlog", "bk1234", "--slug", "new-shiny-task", "--apply"]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(bkl.exists())
        new_bkl = (
            self.backlog_dir / "20260823-bklset-01-bk1234-new-shiny-task.backlog.md"
        )
        self.assertTrue(new_bkl.exists())
        self.assertIn("- Id: bk1234", new_bkl.read_text(encoding="utf-8"))

        # Inbound reference rewritten
        self.assertIn(
            "20260823-bklset-01-bk1234-new-shiny-task.backlog.md",
            ref_doc.read_text(encoding="utf-8"),
        )

    def test_rename_specs_legacy_timestamp(self):
        spec = self.specs_dir / "20260823-1430-01-old-spec.spec.md"
        spec.write_text(
            "# Spec: Old Spec\n\n- Date: 2026-08-23\n- Status: draft\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            [
                "rename",
                "specs",
                "20260823-1430-01-old-spec",
                "--slug",
                "new-spec-slug",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(spec.exists())
        new_spec = self.specs_dir / "20260823-1430-01-new-spec-slug.spec.md"
        self.assertTrue(new_spec.exists())

    def test_rename_walkthroughs(self):
        wt = self.walkthroughs_dir / "20260823-old-migration-walkthrough.md"
        wt.write_text("# Walkthrough\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            [
                "rename",
                "walkthroughs",
                "20260823-old-migration",
                "--slug",
                "new-migration",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(wt.exists())
        new_wt = self.walkthroughs_dir / "20260823-new-migration-walkthrough.md"
        self.assertTrue(new_wt.exists())

    def test_rename_prompts(self):
        pr = self.prompts_dir / "20260823-prmset-01-pr1234-old-prompt.prompt.md"
        pr.write_text("# Prompt\n- Id: pr1234\n- Set: prmset\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            ["rename", "prompts", "pr1234", "--slug", "new-prompt", "--apply"]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(pr.exists())
        new_pr = self.prompts_dir / "20260823-prmset-01-pr1234-new-prompt.prompt.md"
        self.assertTrue(new_pr.exists())

    def test_rename_roadmaps(self):
        rm = self.roadmaps_dir / "20260823-old-roadmap.roadmap.md"
        rm.write_text("# Roadmap\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            [
                "rename",
                "roadmaps",
                "20260823-old-roadmap",
                "--slug",
                "new-roadmap",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(rm.exists())
        new_rm = self.roadmaps_dir / "20260823-new-roadmap.roadmap.md"
        self.assertTrue(new_rm.exists())

    def test_rename_releases(self):
        rel = self.releases_dir / "20260823-rel123-01-rel123-v1-0-0.release.md"
        rel.write_text(
            "# Release\n- Id: rel123\n- Version: 1.0.0\n- Status: planned\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            ["rename", "releases", "rel123", "--slug", "v1-1-0", "--apply"]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(rel.exists())
        new_rel = self.releases_dir / "20260823-rel123-01-rel123-v1-1-0.release.md"
        self.assertTrue(new_rel.exists())

    def test_rename_comms_is_unsupported(self):
        rc, out = self._run(["rename", "comms", "c12345", "--slug", "foo"])
        self.assertEqual(rc, 2)
        self.assertIn("not supported for comms", out)


if __name__ == "__main__":
    unittest.main()
