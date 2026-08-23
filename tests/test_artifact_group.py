"""Tests for universal artifact group CLI support (IPD grouptypes-01, o2ygf3)."""

from __future__ import annotations

import io
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import cli


class TestArtifactGroup(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp(prefix="aw_test_group_"))
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

    def test_group_backlog_preview_and_apply(self):
        bkl = self.backlog_dir / "20260823-oldset-01-bk1234-task.backlog.md"
        bkl.write_text(
            "# Backlog: Task\n\n- Id: bk1234\n- Set: oldset\n- Order: 1\n- Status: open\n",
            encoding="utf-8",
        )

        ref_doc = self.plans_dir / "20260823-planset-01-pl1234-ref.ipd.md"
        ref_doc.write_text(
            "Citing 20260823-oldset-01-bk1234-task.backlog.md here.\n",
            encoding="utf-8",
        )

        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        # 1. Preview with --rename
        rc, out = self._run(
            ["group", "backlog", "bk1234", "--set", "newgrp", "--rename"]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(bkl.exists())
        self.assertIn("would rename", out)
        self.assertIn("would set metadata Set: newgrp", out)

        # 2. Apply with --rename
        rc, out = self._run(
            ["group", "backlog", "bk1234", "--set", "newgrp", "--rename", "--apply"]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(bkl.exists())
        new_bkl = self.backlog_dir / "20260823-newgrp-01-bk1234-task.backlog.md"
        self.assertTrue(new_bkl.exists())
        content = new_bkl.read_text(encoding="utf-8")
        self.assertIn("- Set: newgrp", content)
        self.assertIn("- Id: bk1234", content)

        # Reference rewritten
        self.assertIn(
            "20260823-newgrp-01-bk1234-task.backlog.md",
            ref_doc.read_text(encoding="utf-8"),
        )

    def test_group_backlog_metadata_only(self):
        bkl = self.backlog_dir / "20260823-oldset-01-bk1234-task.backlog.md"
        bkl.write_text(
            "# Backlog: Task\n\n- Id: bk1234\n- Set: oldset\n- Order: 1\n- Status: open\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            ["group", "backlog", "bk1234", "--set", "newgrp", "--apply"]
        )
        self.assertEqual(rc, 0)
        self.assertTrue(bkl.exists())  # file not renamed
        self.assertIn("- Set: newgrp", bkl.read_text(encoding="utf-8"))

    def test_group_specs_injects_set(self):
        spec = self.specs_dir / "20260823-1430-01-spec.spec.md"
        spec.write_text(
            "# Spec: Feature\n\n- Date: 2026-08-23\n- Status: draft\n",
            encoding="utf-8",
        )
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            ["group", "specs", "20260823-1430-01-spec", "--set", "specgrp", "--apply"]
        )
        self.assertEqual(rc, 0)
        content = spec.read_text(encoding="utf-8")
        self.assertIn("- Set: specgrp", content)

    def test_group_walkthroughs_injects_set(self):
        wt = self.walkthroughs_dir / "20260823-migration-walkthrough.md"
        wt.write_text("# Walkthrough\n\n- Date: 2026-08-23\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            ["group", "walkthroughs", "20260823-migration", "--set", "wtgrp", "--apply"]
        )
        self.assertEqual(rc, 0)
        content = wt.read_text(encoding="utf-8")
        self.assertIn("- Set: wtgrp", content)

    def test_group_prompts_with_order(self):
        pr = self.prompts_dir / "20260823-oldset-01-pr1234-prompt.prompt.md"
        pr.write_text(
            "# Prompt\n\n- Id: pr1234\n- Set: oldset\n- Order: 1\n", encoding="utf-8"
        )
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            [
                "group",
                "prompts",
                "pr1234",
                "--set",
                "newpr",
                "--order",
                "5",
                "--rename",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0)
        self.assertFalse(pr.exists())
        new_pr = self.prompts_dir / "20260823-newpr-05-pr1234-prompt.prompt.md"
        self.assertTrue(new_pr.exists())
        content = new_pr.read_text(encoding="utf-8")
        self.assertIn("- Set: newpr", content)
        self.assertIn("- Order: 5", content)

    def test_group_roadmaps_injects_set(self):
        rm = self.roadmaps_dir / "20260823-roadmap.roadmap.md"
        rm.write_text("# Roadmap\n\n- Date: 2026-08-23\n", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.tmp_dir, check=True)
        subprocess.run(["git", "commit", "-qm", "init"], cwd=self.tmp_dir, check=True)

        rc, out = self._run(
            ["group", "roadmaps", "20260823-roadmap", "--set", "rdgrp", "--apply"]
        )
        self.assertEqual(rc, 0)
        content = rm.read_text(encoding="utf-8")
        self.assertIn("- Set: rdgrp", content)

    def test_group_comms_is_unsupported(self):
        rc, out = self._run(["group", "comms", "c12345", "--set", "foo"])
        self.assertEqual(rc, 2)
        self.assertIn("not supported for comms", out)


if __name__ == "__main__":
    unittest.main()
