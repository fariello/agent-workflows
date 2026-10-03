"""Regression test suite for explicit --dir at an AW project subdirectory (IPD ci9kx2-02 lmyeas).

Tests the pure classifier in `project_context` and the diagnostic refusal behavior for both
`aw attention` and `aw ipd board` when --dir points to a subdirectory within a real AW project.

Existing ownership citation (per F-15):
- `tests/test_explicit_dir_non_project.py::test_real_project_root_control_and_subdirectory_refusal`
  owns the general non-project refusal matrix, root control, and bare climb control.
- `tests/test_explicit_dir_non_project.py::test_no_dir_controls` owns the bare no-project controls.
This file extends coverage to the classifier's three outcomes, the enclosing root-naming and corrected
command output, the F-14 negative assertions (no false 'not installed' claims, no `aw install <root>`,
and machine `next` not `aw install .`), and the re-asserted controls for the modified guard path.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_workflows import agent_schema
from agent_workflows.project_context import (
    ProjectLocationCase,
    classify_project_dir,
)

REPO_ROOT = Path(__file__).resolve().parent.parent


class ExplicitDirSubdirResolutionTests(unittest.TestCase):
    def setUp(self):
        self.run_dir_obj = tempfile.TemporaryDirectory()
        self.fixtures_dir_obj = tempfile.TemporaryDirectory()
        self.cwd = self.run_dir_obj.name
        self.fix_root = Path(self.fixtures_dir_obj.name)

        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(REPO_ROOT)
        self.env["AW_NO_REEXEC"] = "1"

        # 1. Real AW project with an open backlog item and git initialized
        self.real_proj = self.fix_root / "real_project"
        backlog_open = self.real_proj / ".aw" / "records" / "backlog" / "open"
        backlog_open.mkdir(parents=True)
        (backlog_open / "20261001-ci9kx2-01-abc123-test.backlog.md").write_text(
            "- Id: abc123\n"
            "- Status: open\n"
            "- Date: 2026-10-01\n"
            "- Work-Kind: feature\n"
            "- Priority: low\n"
            "- Summary: Test item\n\n"
            "## Description\nTest backlog item\n"
        )
        subprocess.run(
            ["git", "init", str(self.real_proj)], check=True, capture_output=True
        )

        # 2. Deep subdirectory within the real project
        self.deep_subdir = self.real_proj / "src" / "deep"
        self.deep_subdir.mkdir(parents=True)

        # 3. Unrelated git repo without AW
        self.git_no_aw = self.fix_root / "git_no_aw"
        self.git_no_aw.mkdir()
        subprocess.run(
            ["git", "init", str(self.git_no_aw)], check=True, capture_output=True
        )

        # 4. Non-git empty directory
        self.nongit_dir = self.fix_root / "nongit"
        self.nongit_dir.mkdir()

    def tearDown(self):
        self.run_dir_obj.cleanup()
        self.fixtures_dir_obj.cleanup()

    def _run_cli(self, args, run_cwd=None):
        target_cwd = run_cwd or self.cwd
        cmd = [sys.executable, "-m", "agent_workflows"] + args
        res = subprocess.run(
            cmd,
            cwd=target_cwd,
            env=self.env,
            capture_output=True,
            text=True,
        )
        return res.returncode, res.stdout, res.stderr

    def test_classifier_outcomes_direct(self):
        """Test the pure classifier directly on all three distinct outcomes."""
        # Outcome 1: Real project root
        cls_root = classify_project_dir(self.real_proj)
        self.assertEqual(cls_root.case, ProjectLocationCase.IS_PROJECT_ROOT)
        self.assertTrue(cls_root.is_root)
        self.assertFalse(cls_root.is_inside_project)
        self.assertFalse(cls_root.is_no_project)
        self.assertEqual(cls_root.root, self.real_proj.resolve())

        # Outcome 2: Subdirectory of real project
        cls_sub = classify_project_dir(self.deep_subdir)
        self.assertEqual(cls_sub.case, ProjectLocationCase.INSIDE_PROJECT)
        self.assertFalse(cls_sub.is_root)
        self.assertTrue(cls_sub.is_inside_project)
        self.assertFalse(cls_sub.is_no_project)
        self.assertEqual(cls_sub.root, self.real_proj.resolve())
        self.assertEqual(cls_sub.enclosing_root, self.real_proj.resolve())

        # Outcome 3: Directory in no project at all
        cls_nongit = classify_project_dir(self.nongit_dir)
        self.assertEqual(cls_nongit.case, ProjectLocationCase.NO_PROJECT)
        self.assertFalse(cls_nongit.is_root)
        self.assertFalse(cls_nongit.is_inside_project)
        self.assertTrue(cls_nongit.is_no_project)
        self.assertIsNone(cls_nongit.root)
        self.assertIsNone(cls_nongit.enclosing_root)

    def test_attention_subdirectory_human(self):
        """Human attention with --dir <subdir> names enclosing root and corrected command; pins F-14 negatives."""
        rc, out, err = self._run_cli(["attention", "--dir", str(self.deep_subdir)])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        # Names the enclosing root
        self.assertIn(str(self.real_proj), err)
        # States the no-climb rule
        self.assertIn("explicit --dir is honored verbatim with no upward climb", err)
        # Literal corrected command
        self.assertIn(f"aw attention --dir {self.real_proj}", err)
        # F-14 Negatives: must NOT claim not installed or offer install
        self.assertNotIn("is not installed in it", err)
        self.assertNotIn("aw install ", err)

    def test_attention_subdirectory_agent(self):
        """Machine attention with --dir <subdir> is path-free, valid, and next is not aw install ."""
        rc, out, err = self._run_cli(
            ["attention", "--agent", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(err, "")
        # Path-free: neither deep_subdir nor real_proj may appear in stdout
        self.assertNotIn(str(self.deep_subdir), out)
        self.assertNotIn(str(self.real_proj), out)
        rec = json.loads(out.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "attention")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        # F-14 Negative: next must NOT say aw install .
        self.assertNotEqual(rec.get("next"), "aw install .")
        self.assertIsNone(rec.get("next"))

        # Also test --format json which carries the summary field
        rc_j, out_j, _ = self._run_cli(
            ["attention", "--format", "json", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc_j, 2)
        self.assertNotIn(str(self.deep_subdir), out_j)
        self.assertNotIn(str(self.real_proj), out_j)
        rec_j = json.loads(out_j.strip())
        self.assertEqual(
            rec_j.get("summary"),
            "the specified directory is inside an AW project but is not its root; --dir is honored verbatim with no upward climb",
        )

    def test_attention_check_subdirectory_human_and_agent(self):
        """Human and agent attention --check on subdirectory fail closed with diagnosis."""
        # Human --check
        rc, out, err = self._run_cli(
            ["attention", "--check", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn(str(self.real_proj), err)
        self.assertIn(f"aw attention --dir {self.real_proj}", err)
        self.assertNotIn("is not installed in it", err)
        self.assertNotIn("aw install ", err)

        # Agent --check
        rc_a, out_a, err_a = self._run_cli(
            ["attention", "--check", "--agent", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc_a, 2)
        self.assertEqual(err_a, "")
        self.assertNotIn(str(self.deep_subdir), out_a)
        self.assertNotIn(str(self.real_proj), out_a)
        rec_a = json.loads(out_a.strip())
        self.assertEqual(rec_a["schema"], "aw.agent/v1")
        self.assertEqual(rec_a["outcome"], "cannot-run")
        self.assertEqual(rec_a["exit"], 2)
        self.assertEqual(agent_schema.validate_agent_record(rec_a), [])
        self.assertNotEqual(rec_a.get("next"), "aw install .")
        self.assertIsNone(rec_a.get("next"))

    def test_ipd_board_subdirectory_human(self):
        """Human ipd board with --dir <subdir> names root, literal command with verb 'ipd board', pins F-14 negatives."""
        rc, out, err = self._run_cli(["ipd", "board", "--dir", str(self.deep_subdir)])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn(str(self.real_proj), err)
        self.assertIn(f"aw ipd board --dir {self.real_proj}", err)
        self.assertNotIn("aw plans", err)
        self.assertNotIn("is not installed in it", err)
        self.assertNotIn("aw install ", err)

    def test_ipd_board_subdirectory_agent(self):
        """Machine ipd board with --dir <subdir> is path-free, valid, and next is not aw install ."""
        rc, out, err = self._run_cli(
            ["ipd", "board", "--agent", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(err, "")
        self.assertNotIn(str(self.deep_subdir), out)
        self.assertNotIn(str(self.real_proj), out)
        rec = json.loads(out.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd board")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(agent_schema.validate_agent_record(rec), [])
        self.assertNotEqual(rec.get("next"), "aw install .")
        self.assertIsNone(rec.get("next"))

        # Also test --json which carries the summary field
        rc_j, out_j, _ = self._run_cli(
            ["ipd", "board", "--json", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc_j, 2)
        self.assertNotIn(str(self.deep_subdir), out_j)
        self.assertNotIn(str(self.real_proj), out_j)
        rec_j = json.loads(out_j.strip())
        self.assertEqual(
            rec_j.get("summary"),
            "the specified directory is inside an AW project but is not its root; --dir is honored verbatim with no upward climb",
        )

    def test_controls_reasserted(self):
        """Re-asserted controls: real root reports artifacts, bare climb works, no-project git offers install."""
        # 1. Real project root with explicit --dir reports its artifact at exit 0
        rc_r, out_r, err_r = self._run_cli(["attention", "--dir", str(self.real_proj)])
        self.assertEqual(rc_r, 0)
        self.assertIn("1 artifact shown", out_r)
        self.assertEqual(err_r, "")

        # 2. Bare invocation from inside subdirectory climbs to root and reports artifact at exit 0
        rc_cl, out_cl, err_cl = self._run_cli(
            ["attention"], run_cwd=str(self.deep_subdir)
        )
        self.assertEqual(rc_cl, 0)
        self.assertIn("1 artifact shown", out_cl)
        self.assertEqual(err_cl, "")

        # 3. No-project git repo refuses, correctly asserts not installed, and offers aw install
        rc_g, out_g, err_g = self._run_cli(["attention", "--dir", str(self.git_no_aw)])
        self.assertEqual(rc_g, 2)
        self.assertIn(
            "IS a git repository, but agent-workflows is not installed in it.", err_g
        )
        self.assertIn(f"Install it there with: aw install {self.git_no_aw}", err_g)

        # 4. No-project git repo machine record attaches aw install .
        rc_ga, out_ga, _ = self._run_cli(
            ["attention", "--agent", "--dir", str(self.git_no_aw)]
        )
        self.assertEqual(rc_ga, 2)
        rec_ga = json.loads(out_ga.strip())
        self.assertEqual(rec_ga["outcome"], "cannot-run")
        self.assertEqual(rec_ga.get("next"), "aw install .")


if __name__ == "__main__":
    unittest.main()
