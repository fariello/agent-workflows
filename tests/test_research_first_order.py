"""Tests for research first document order numbering and --order override (IPD zye6k4).

Covers:
(a) a new-set research-report is 01
(b) a new-set research-prompt is 00
(c) a second document in an existing set is max+1
(d) aw adopt --apply into a new set is 01
(e) --order 03 yields 03
(f) --order on an occupied slot exits 2, names the occupant, and writes no file
(g) a singleton (no --set) non-prompt is 01
(h) --order 00 adds a prompt to an existing set
"""

from __future__ import annotations

import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Tuple
import unittest
from unittest.mock import patch
from contextlib import redirect_stderr, redirect_stdout

from agent_workflows import cli
from agent_workflows import research_contract as R


class TestResearchFirstOrder(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="aw_test_first_order_")).resolve()
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

        self.repo_dir = self.tmp / "repo"
        self.research_root = self.repo_dir / ".aw" / "records" / "research"
        self.inbox_dir = self.repo_dir / ".aw" / "inbox"
        self.research_root.mkdir(parents=True, exist_ok=True)
        self.inbox_dir.mkdir(parents=True, exist_ok=True)

        self.env_patcher = patch.dict(
            os.environ,
            {
                "HOME": str(self.tmp),
                "XDG_CONFIG_HOME": str(self.tmp),
                "AW_NO_REEXEC": "1",
            },
        )
        self.env_patcher.start()
        self.addCleanup(self.env_patcher.stop)

        subprocess.run(["git", "init", "-q"], cwd=self.repo_dir, check=True)
        subprocess.run(
            ["git", "config", "user.email", "t@e.com"], cwd=self.repo_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.name", "T"], cwd=self.repo_dir, check=True
        )

    def _run_cli(self, cmd: list[str]) -> Tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            try:
                rc = cli.main(cmd)
            except SystemExit as e:
                rc = int(e.code or 0)
        return rc, out.getvalue(), err.getvalue()

    def test_a_new_set_research_report_is_01(self):
        """(a) a new-set research-report is 01."""
        rc, out, err = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-a",
                "--kind",
                "research-report",
                "--slug",
                "rep-a",
                "--summary",
                "report a summary",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"stdout: {out}, stderr: {err}")
        matches = list(self.research_root.glob("*-set-a-*.research-report.md"))
        self.assertEqual(len(matches), 1)
        parsed, _ = R.parse_name(matches[0].name)
        assert parsed is not None
        self.assertEqual(parsed.order, "01")

    def test_b_new_set_research_prompt_is_00(self):
        """(b) a new-set research-prompt is 00."""
        rc, out, err = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-b",
                "--kind",
                "research-prompt",
                "--slug",
                "prompt-b",
                "--summary",
                "prompt b summary",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"stdout: {out}, stderr: {err}")
        matches = list(self.research_root.glob("*-set-b-*.research-prompt.md"))
        self.assertEqual(len(matches), 1)
        parsed, _ = R.parse_name(matches[0].name)
        assert parsed is not None
        self.assertEqual(parsed.order, "00")

    def test_c_second_document_in_existing_set_is_max_plus_one(self):
        """(c) a second document in an existing set is max+1."""
        rc1, _, _ = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-c",
                "--kind",
                "research-report",
                "--slug",
                "first",
                "--summary",
                "first doc",
                "--apply",
            ]
        )
        self.assertEqual(rc1, 0)
        rc2, _, _ = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-c",
                "--kind",
                "research-report",
                "--slug",
                "second",
                "--summary",
                "second doc",
                "--apply",
            ]
        )
        self.assertEqual(rc2, 0)
        matches = sorted(self.research_root.glob("*-set-c-*.research-report.md"))
        self.assertEqual(len(matches), 2)
        parsed1, _ = R.parse_name(matches[0].name)
        parsed2, _ = R.parse_name(matches[1].name)
        assert parsed1 is not None and parsed2 is not None
        self.assertEqual(parsed1.order, "01")
        self.assertEqual(parsed2.order, "02")

    def test_d_adopt_apply_into_new_set_is_01(self):
        """(d) aw adopt --apply into a new set is 01."""
        drop = self.inbox_dir / "external-finding.md"
        drop.write_text("# External Finding\n\nExternal drop body.\n", encoding="utf-8")
        rc, out, err = self._run_cli(
            [
                "adopt",
                str(drop),
                "--dir",
                str(self.repo_dir),
                "--set",
                "set-d",
                "--kind",
                "findings",
                "--slug",
                "ext-finding",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"stdout: {out}, stderr: {err}")
        matches = list(self.research_root.glob("*-set-d-*.findings.md"))
        self.assertEqual(len(matches), 1)
        parsed, _ = R.parse_name(matches[0].name)
        assert parsed is not None
        self.assertEqual(parsed.order, "01")

    def test_e_order_override_yields_specified_order(self):
        """(e) --order 03 yields 03."""
        rc, out, err = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-e",
                "--kind",
                "research-report",
                "--slug",
                "doc-e",
                "--summary",
                "doc e summary",
                "--order",
                "03",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"stdout: {out}, stderr: {err}")
        matches = list(self.research_root.glob("*-set-e-*.research-report.md"))
        self.assertEqual(len(matches), 1)
        parsed, _ = R.parse_name(matches[0].name)
        assert parsed is not None
        self.assertEqual(parsed.order, "03")

    def test_f_order_on_occupied_slot_refuses_and_writes_nothing(self):
        """(f) --order on an occupied slot exits 2, names the occupant, and writes no file."""
        rc1, _, _ = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-f",
                "--kind",
                "research-report",
                "--slug",
                "occupant",
                "--summary",
                "occupant summary",
                "--order",
                "05",
                "--apply",
            ]
        )
        self.assertEqual(rc1, 0)
        initial_files = sorted(p.name for p in self.research_root.glob("*.md"))
        occupant_name = [f for f in initial_files if "-set-f-05-" in f][0]

        # Attempt to occupy slot 05 again
        rc2, out2, err2 = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-f",
                "--kind",
                "research-report",
                "--slug",
                "intruder",
                "--summary",
                "intruder summary",
                "--order",
                "05",
                "--apply",
            ]
        )
        self.assertEqual(rc2, 2)
        combined2 = out2 + err2
        self.assertIn(occupant_name, combined2)
        self.assertIn("already occupied", combined2)

        # Directory listing shows nothing new was written
        current_files = sorted(p.name for p in self.research_root.glob("*.md"))
        self.assertEqual(initial_files, current_files)

    def test_g_singleton_non_prompt_is_01(self):
        """(g) a singleton (no --set) non-prompt is 01."""
        rc, out, err = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--kind",
                "findings",
                "--slug",
                "singleton-doc",
                "--summary",
                "singleton summary",
                "--apply",
            ]
        )
        self.assertEqual(rc, 0, f"stdout: {out}, stderr: {err}")
        matches = list(self.research_root.glob("*-singleton-doc-*.findings.md"))
        self.assertEqual(len(matches), 1)
        parsed, _ = R.parse_name(matches[0].name)
        assert parsed is not None
        self.assertEqual(parsed.order, "01")

    def test_h_order_00_adds_prompt_to_existing_set(self):
        """(h) --order 00 adds a prompt to an existing set."""
        rc1, _, _ = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-h",
                "--kind",
                "research-report",
                "--slug",
                "first",
                "--summary",
                "first report",
                "--apply",
            ]
        )
        self.assertEqual(rc1, 0)
        # Add prompt at order 00
        rc2, out2, err2 = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-h",
                "--kind",
                "research-prompt",
                "--slug",
                "originating-prompt",
                "--summary",
                "orig prompt summary",
                "--order",
                "00",
                "--apply",
            ]
        )
        self.assertEqual(rc2, 0, f"stdout: {out2}, stderr: {err2}")
        matches = sorted(self.research_root.glob("*-set-h-*.md"))
        self.assertEqual(len(matches), 2)
        parsed_prompt, _ = R.parse_name(matches[0].name)
        parsed_report, _ = R.parse_name(matches[1].name)
        assert parsed_prompt is not None and parsed_report is not None
        self.assertEqual(parsed_prompt.order, "00")
        self.assertEqual(parsed_prompt.kind, "research-prompt")
        self.assertEqual(parsed_report.order, "01")
        self.assertEqual(parsed_report.kind, "research-report")

    def test_order_out_of_range_exits_two(self):
        """Out of range order (e.g. 100) exits 2."""
        rc, out, err = self._run_cli(
            [
                "research",
                "new",
                str(self.repo_dir),
                "--set",
                "set-range",
                "--kind",
                "research-report",
                "--slug",
                "doc",
                "--summary",
                "doc summary",
                "--order",
                "100",
            ]
        )
        self.assertEqual(rc, 2)
        self.assertIn("--order must be between 0 and 99", out + err)

    def test_adopt_order_override_and_occupied_refusal(self):
        """Adopt honors --order and refuses occupied slot."""
        drop1 = self.inbox_dir / "drop1.md"
        drop1.write_text("# Drop 1\nBody 1\n", encoding="utf-8")
        rc1, _, _ = self._run_cli(
            [
                "adopt",
                str(drop1),
                "--dir",
                str(self.repo_dir),
                "--set",
                "adopt-order",
                "--kind",
                "findings",
                "--slug",
                "ad1",
                "--order",
                "03",
                "--apply",
            ]
        )
        self.assertEqual(rc1, 0)
        matches1 = list(self.research_root.glob("*-adopt-order-03-*.findings.md"))
        self.assertEqual(len(matches1), 1)

        # Attempt to adopt into occupied slot 03
        drop2 = self.inbox_dir / "drop2.md"
        drop2.write_text("# Drop 2\nBody 2\n", encoding="utf-8")
        rc2, out2, err2 = self._run_cli(
            [
                "adopt",
                str(drop2),
                "--dir",
                str(self.repo_dir),
                "--set",
                "adopt-order",
                "--kind",
                "findings",
                "--slug",
                "ad2",
                "--order",
                "03",
                "--apply",
            ]
        )
        self.assertEqual(rc2, 2)
        self.assertIn("already occupied", out2 + err2)
        self.assertIn(matches1[0].name, out2 + err2)

        # Adopt with --order 100 exits 2
        rc3, out3, err3 = self._run_cli(
            [
                "adopt",
                str(drop2),
                "--dir",
                str(self.repo_dir),
                "--set",
                "adopt-order",
                "--kind",
                "findings",
                "--slug",
                "ad2",
                "--order",
                "100",
                "--apply",
            ]
        )
        self.assertEqual(rc3, 2)
        self.assertIn("--order must be between 0 and 99", out3 + err3)
