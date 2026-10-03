"""Regression test suite for explicit --dir at a non-AW directory (IPD ci9kx2-01 bjgqez).

Pins the full matrix of behaviors when --dir names an explicit non-project directory,
verifying that both `aw attention` and `aw ipd board` report cannot-run (exit 2
across human and machine surfaces per D158 / IPD rwvzqm) rather than falsely exiting 0.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent_workflows import agent_schema

REPO_ROOT = Path(__file__).resolve().parent.parent


class ExplicitDirNonProjectMatrixTests(unittest.TestCase):
    def setUp(self):
        self.run_dir_obj = tempfile.TemporaryDirectory()
        self.fixtures_dir_obj = tempfile.TemporaryDirectory()
        self.cwd = self.run_dir_obj.name
        self.fix_root = Path(self.fixtures_dir_obj.name)

        self.env = dict(os.environ)
        self.env["PYTHONPATH"] = str(REPO_ROOT)
        self.env["AW_NO_REEXEC"] = "1"

        # 1. Non-git empty directory
        self.nongit_dir = self.fix_root / "nongit"
        self.nongit_dir.mkdir()

        # 2. Git repo without AW
        self.git_dir = self.fix_root / "gitdir"
        self.git_dir.mkdir()
        subprocess.run(
            ["git", "init", str(self.git_dir)], check=True, capture_output=True
        )

        # 3. Nonexistent directory
        self.nonexistent_dir = self.fix_root / "nonexistent"

        # 4. Regular file
        self.regular_file = self.fix_root / "plain_file.txt"
        self.regular_file.write_text("not a directory\n")

        # 5. Directory with .aw containing only state/
        self.state_only_dir = self.fix_root / "state_only"
        (self.state_only_dir / ".aw" / "state").mkdir(parents=True)

        # 6. Real AW project with an open backlog item and a deep subdirectory
        self.real_proj = self.fix_root / "real_project"
        backlog_open = self.real_proj / ".aw" / "records" / "backlog" / "open"
        backlog_open.mkdir(parents=True)
        (backlog_open / "20260930-ci9kx2-01-abc123-test.backlog.md").write_text(
            "- Id: abc123\n"
            "- Status: open\n"
            "- Date: 2026-09-30\n"
            "- Work-Kind: feature\n"
            "- Priority: low\n"
            "- Summary: Test item\n\n"
            "## Description\nTest backlog item\n"
        )
        self.deep_subdir = self.real_proj / "src" / "deep"
        self.deep_subdir.mkdir(parents=True)

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

    def test_attention_explicit_dir_nongit_human(self):
        rc, out, err = self._run_cli(["attention", "--dir", str(self.nongit_dir)])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn(f"no AW project found at {self.nongit_dir}", err)
        self.assertIn("explicit --dir is honored verbatim with no upward climb", err)
        self.assertNotIn("and its parents", err)
        self.assertNotIn("pass --dir", err)
        self.assertNotIn("IS a git repository", err)

    def test_attention_explicit_dir_nongit_agent(self):
        rc, out, err = self._run_cli(
            ["attention", "--agent", "--dir", str(self.nongit_dir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(err, "")
        self.assertNotIn(str(self.nongit_dir), out)
        rec = json.loads(out.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "attention")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertIsNone(rec.get("next"))
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_attention_explicit_dir_git_human(self):
        rc, out, err = self._run_cli(["attention", "--dir", str(self.git_dir)])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn(f"no AW project found at {self.git_dir}", err)
        self.assertIn("explicit --dir is honored verbatim with no upward climb", err)
        self.assertNotIn("and its parents", err)
        self.assertNotIn("pass --dir", err)
        self.assertIn(
            f"{self.git_dir} IS a git repository, but agent-workflows is not installed in it.",
            err,
        )
        self.assertIn(f"aw install {self.git_dir}", err)

    def test_attention_explicit_dir_git_agent(self):
        rc, out, err = self._run_cli(
            ["attention", "--agent", "--dir", str(self.git_dir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(err, "")
        self.assertNotIn(str(self.git_dir), out)
        rec = json.loads(out.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "attention")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(rec.get("next"), "aw install .")
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_ipd_board_explicit_dir_nongit_human(self):
        rc, out, err = self._run_cli(["ipd", "board", "--dir", str(self.nongit_dir)])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertNotIn("CLEAN", out)
        self.assertNotIn("aw ipd scaffold", out)
        self.assertIn(f"no AW project found at {self.nongit_dir}", err)
        self.assertIn("explicit --dir is honored verbatim with no upward climb", err)
        self.assertNotIn("and its parents", err)
        self.assertNotIn("pass --dir", err)
        self.assertNotIn("IS a git repository", err)

    def test_ipd_board_explicit_dir_nongit_agent(self):
        rc, out, err = self._run_cli(
            ["ipd", "board", "--agent", "--dir", str(self.nongit_dir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(err, "")
        self.assertNotIn("CLEAN", out)
        self.assertNotIn(str(self.nongit_dir), out)
        rec = json.loads(out.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd board")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertIsNone(rec.get("next"))
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_ipd_board_explicit_dir_git_human(self):
        rc, out, err = self._run_cli(["ipd", "board", "--dir", str(self.git_dir)])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertNotIn("CLEAN", out)
        self.assertNotIn("aw ipd scaffold", out)
        self.assertIn(f"no AW project found at {self.git_dir}", err)
        self.assertIn("explicit --dir is honored verbatim with no upward climb", err)
        self.assertNotIn("and its parents", err)
        self.assertNotIn("pass --dir", err)
        self.assertIn(
            f"{self.git_dir} IS a git repository, but agent-workflows is not installed in it.",
            err,
        )
        self.assertIn(f"aw install {self.git_dir}", err)

    def test_ipd_board_explicit_dir_git_agent(self):
        rc, out, err = self._run_cli(
            ["ipd", "board", "--agent", "--dir", str(self.git_dir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(err, "")
        self.assertNotIn("CLEAN", out)
        self.assertNotIn(str(self.git_dir), out)
        rec = json.loads(out.strip())
        self.assertEqual(rec["schema"], "aw.agent/v1")
        self.assertEqual(rec["cmd"], "ipd board")
        self.assertEqual(rec["outcome"], "cannot-run")
        self.assertEqual(rec["exit"], 2)
        self.assertEqual(rec.get("next"), "aw install .")
        self.assertEqual(agent_schema.validate_agent_record(rec), [])

    def test_attention_check_explicit_dir_human_and_agent(self):
        # Human --check
        rc, out, err = self._run_cli(
            ["attention", "--check", "--dir", str(self.nongit_dir)]
        )
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn(f"no AW project found at {self.nongit_dir}", err)

        # Agent --check
        rc_a, out_a, err_a = self._run_cli(
            ["attention", "--check", "--agent", "--dir", str(self.nongit_dir)]
        )
        self.assertEqual(rc_a, 2)
        self.assertEqual(err_a, "")
        self.assertNotIn(str(self.nongit_dir), out_a)
        rec_a = json.loads(out_a.strip())
        self.assertEqual(rec_a["schema"], "aw.agent/v1")
        self.assertEqual(rec_a["cmd"], "attention")
        self.assertEqual(rec_a["outcome"], "cannot-run")
        self.assertEqual(rec_a["exit"], 2)
        self.assertEqual(rec_a.get("findings"), 0)
        self.assertEqual(agent_schema.validate_agent_record(rec_a), [])

    def test_attention_explicit_dir_nonexistent_and_file_and_state_only(self):
        for path in (self.nonexistent_dir, self.regular_file, self.state_only_dir):
            rc, out, err = self._run_cli(["attention", "--dir", str(path)])
            self.assertEqual(rc, 2, f"Expected rc 2 for {path}")
            self.assertEqual(out, "")
            self.assertIn(f"no AW project found at {path}", err)

            rc_b, out_b, err_b = self._run_cli(["ipd", "board", "--dir", str(path)])
            self.assertEqual(rc_b, 2, f"Expected rc 2 for {path}")
            self.assertEqual(out_b, "")
            self.assertNotIn("CLEAN", out_b)

    def test_real_project_root_control_and_subdirectory_refusal(self):
        # 1. Real project root with explicit --dir succeeds at exit 0
        rc_root, out_root, err_root = self._run_cli(
            ["attention", "--dir", str(self.real_proj)]
        )
        self.assertEqual(rc_root, 0)
        self.assertIn("1 artifact shown", out_root)
        self.assertEqual(err_root, "")

        # 2. Subdirectory with explicit --dir refuses (exit 2 cannot-run), F-15 / PR-701 / IPD rwvzqm
        rc_sub, out_sub, err_sub = self._run_cli(
            ["attention", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc_sub, 2)
        self.assertEqual(out_sub, "")
        self.assertIn(f"no AW project found at {self.deep_subdir}", err_sub)
        self.assertIn(
            "explicit --dir is honored verbatim with no upward climb", err_sub
        )

        rc_sub_agent, out_sub_agent, _ = self._run_cli(
            ["attention", "--agent", "--dir", str(self.deep_subdir)]
        )
        self.assertEqual(rc_sub_agent, 2)
        rec_sub = json.loads(out_sub_agent.strip())
        self.assertEqual(rec_sub["outcome"], "cannot-run")
        self.assertEqual(rec_sub["exit"], 2)

        # 3. Invocation from inside subdirectory without --dir climbs to project root at exit 0
        rc_climb, out_climb, err_climb = self._run_cli(
            ["attention"], run_cwd=self.deep_subdir
        )
        self.assertEqual(rc_climb, 0)
        self.assertIn("1 artifact shown", out_climb)
        self.assertEqual(err_climb, "")

    def test_no_dir_controls(self):
        # Bare attention outside project: human 2 with climb message
        rc, out, err = self._run_cli(["attention"])
        self.assertEqual(rc, 2)
        self.assertEqual(out, "")
        self.assertIn("Checked", err)
        self.assertIn("and its parents", err)
        self.assertIn("or pass --dir <repo>", err)

        # Bare attention --agent outside project: machine 2 cannot-run
        rc_a, out_a, _ = self._run_cli(["attention", "--agent"])
        self.assertEqual(rc_a, 2)
        rec_a = json.loads(out_a.strip())
        self.assertEqual(rec_a["outcome"], "cannot-run")
        self.assertEqual(rec_a["exit"], 2)

        # Bare ipd board outside project: human 2
        rc_b, out_b, err_b = self._run_cli(["ipd", "board"])
        self.assertEqual(rc_b, 2)
        self.assertEqual(out_b, "")
        self.assertIn("Checked", err_b)
        self.assertIn("and its parents", err_b)
        self.assertIn("or pass --dir <repo>", err_b)

        # Bare ipd board --agent outside project: machine 2
        rc_ba, out_ba, _ = self._run_cli(["ipd", "board", "--agent"])
        self.assertEqual(rc_ba, 2)
        rec_ba = json.loads(out_ba.strip())
        self.assertEqual(rec_ba["outcome"], "cannot-run")
        self.assertEqual(rec_ba["exit"], 2)

        # Bare attention --check outside project: exit 0 valid
        rc_c, out_c, _ = self._run_cli(["attention", "--check"])
        self.assertEqual(rc_c, 0)
        self.assertIn("aw attention --check: the view is valid.", out_c)

        # Bare attention --check --agent outside project: exit 0 clean
        rc_ca, out_ca, _ = self._run_cli(["attention", "--check", "--agent"])
        self.assertEqual(rc_ca, 0)
        rec_ca = json.loads(out_ca.strip())
        self.assertEqual(rec_ca["outcome"], "clean")
        self.assertEqual(rec_ca["exit"], 0)

    def test_machine_summary_content_and_path_free(self):
        # attention --format json with explicit --dir
        rc, out, _ = self._run_cli(
            ["attention", "--format", "json", "--dir", str(self.nongit_dir)]
        )
        self.assertEqual(rc, 2)
        self.assertNotIn(str(self.nongit_dir), out)
        data = json.loads(out)
        expected_summary = "no AW project found at the specified directory; --dir is honored verbatim with no upward climb"
        self.assertEqual(data.get("summary"), expected_summary)
        self.assertNotIn(
            "at the working directory or any ancestor", data.get("summary", "")
        )
        self.assertNotIn("pass --dir", data.get("summary", ""))


if __name__ == "__main__":
    unittest.main()
