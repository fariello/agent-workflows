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

    def test_untracked_dir_excluded_by_default(self) -> None:
        pdir = self.root / ".aw" / "records" / "prompts" / "untracked"
        pdir.mkdir(parents=True)
        (pdir / "bad-name.md").write_text("# Bad\n", encoding="utf-8")
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "add untracked prompt")

        # Default excludes untracked/ directory artifacts
        drift_default = doctor.run_doctor(self.root, include_untracked=False)
        self.assertEqual(drift_default, [])

        # include_untracked=True includes them and flags grammar issue
        drift_all = doctor.run_doctor(self.root, include_untracked=True)
        self.assertTrue(any(d.rule == "check.name-nonconformant" for d in drift_all))

    def test_executed_dir_warns_by_default(self) -> None:
        pdir = self.root / ".aw" / "records" / "plans" / "executed"
        pdir.mkdir(parents=True)
        (pdir / "bad-plan-name.md").write_text(
            "# Plan\n- Id: ppp111\n- Status: executed\n", encoding="utf-8"
        )
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "add executed plan")

        report = doctor.collect_doctor_report(self.root, include_executed=False)
        # Treated as executed warning, not in all_drift as name-nonconformant
        self.assertFalse(
            any(d.rule == "check.name-nonconformant" for d in report.all_drift)
        )
        self.assertTrue(
            any(
                d.rule == "check.name-nonconformant"
                for d in report.artifacts.executed_warnings
            )
        )

        # include_executed=True treats it as error
        report_strict = doctor.collect_doctor_report(self.root, include_executed=True)
        self.assertTrue(
            any(d.rule == "check.name-nonconformant" for d in report_strict.all_drift)
        )

    def test_split_brain_layout_detected(self) -> None:
        (self.root / ".agents").mkdir(parents=True, exist_ok=True)
        (self.root / ".aw").mkdir(parents=True, exist_ok=True)
        report = doctor.collect_doctor_report(self.root)
        self.assertIn("split-brain", report.env.layout)
        self.assertTrue(
            any(d.rule == "doctor.layout-split-brain" for d in report.env.drift)
        )

    def test_render_groups_artifact_issues_by_type_and_dir_with_fixes(self) -> None:
        from agent_workflows import term as T

        bdir = self.root / ".aw" / "records" / "backlog" / "open"
        bdir.mkdir(parents=True, exist_ok=True)
        (bdir / "bad-backlog.backlog.md").write_text(
            "# Title\n- Id: bk1\n- Summary: multi\nline\n- Status: open\n",
            encoding="utf-8",
        )
        _git(self.root, "add", "-A")
        _git(self.root, "commit", "-qm", "add bad backlog")

        report = doctor.collect_doctor_report(self.root)
        term = T.Term(color=False)
        rendered = doctor.render_human_report(report, term)

        self.assertIn(
            "Issue: Filename does not match artifact naming grammar", rendered
        )
        self.assertIn("- .aw/records/backlog/open", rendered)
        self.assertIn("1. bad-backlog.backlog.md", rendered)
        self.assertIn("Fix:", rendered)
        self.assertIn("Summary of issues and proposed fixes:", rendered)

    def test_render_git_modified_warns_without_error_block_prefix(self) -> None:
        from agent_workflows import term as T

        (self.root / "README.md").write_text("Hello", encoding="utf-8")
        _git(self.root, "add", "README.md")
        _git(self.root, "commit", "-qm", "add readme")
        (self.root / "README.md").write_text("Modified", encoding="utf-8")

        report = doctor.collect_doctor_report(self.root)
        term = T.Term(color=False)
        rendered = doctor.render_human_report(report, term)

        self.assertIn("Git Working Tree", rendered)
        self.assertNotIn("[ERROR] Git Working Tree", rendered)
        self.assertIn("Unstaged modifications (1):", rendered)

    def test_immediate_startup_announcement(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            doctor.run(types.SimpleNamespace(dir=str(self.root), as_agent=False))
        self.assertIn("Starting aw doctor repository health check...", out.getvalue())


if __name__ == "__main__":
    unittest.main()
