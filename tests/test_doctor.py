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
        # h90ij1: the marker goes at `.aw/system/VERSION`, the location `engine.read_installed_version`
        # actually probes and every install writes. This fixture previously wrote `.aw/VERSION`, a path
        # NO layout creates; it only read back as "installed" because doctor's probe was reading the
        # same fictional path. With both sides corrected the fixture is genuinely installed, so the
        # emitted layout document must be present too or `check.system-layout-missing` fires (which is
        # correct behavior for an installed workspace, see check_engine.check_system_layout).
        packaged = versioning.resolve_version(engine.resolve_source_root(None))
        (self.root / ".aw" / "system").mkdir(parents=True)
        (self.root / ".aw" / "system" / "VERSION").write_text(
            packaged + "\n", encoding="utf-8"
        )
        engine.emit_layout_artifacts(self.root)
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
        from agent_workflows import term as T

        out = io.StringIO()
        term = T.Term(stream=out, color=False)
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = doctor.run(
                types.SimpleNamespace(dir=str(self.root), as_agent=False), term=term
            )
        self.assertEqual(rc, 0)
        self.assertIn("no findings", out.getvalue())

    def test_run_agent_output(self) -> None:
        import json

        (self.root / "x.txt").write_text("x", encoding="utf-8")
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            rc = doctor.run(types.SimpleNamespace(dir=str(self.root), as_agent=True))
        self.assertEqual(rc, 1)
        data = json.loads(out.getvalue().strip())
        self.assertEqual(data.get("schema"), "aw.agent/v1")
        self.assertEqual(data.get("cmd"), "doctor")
        self.assertEqual(data.get("outcome"), "findings")
        self.assertEqual(data.get("exit"), 1)

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
        from agent_workflows import term as T

        out = io.StringIO()
        term = T.Term(stream=out, color=False)
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            doctor.run(
                types.SimpleNamespace(dir=str(self.root), as_agent=False), term=term
            )
        self.assertIn("Starting aw doctor repository health check...", out.getvalue())


class DoctorEnvironmentProbeReadsCanonicalPathsTests(unittest.TestCase):
    """h90ij1: doctor's environment probe must read the paths a real install actually writes.

    Before the fix, `probe_environment` resolved the installed VERSION from `.aw/VERSION` and
    `.agents/VERSION`, and the preset/backend from `.aw/config.json` / `.agents/config.json`.
    NONE of those four paths is created by either supported layout, so a correctly installed
    target read back as `not installed` with a blank preset and backend.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _install_marker(self, rel: str, value: str) -> None:
        marker = self.root / rel
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(value + "\n", encoding="utf-8")

    def test_probe_agrees_with_engine_on_aw_system_version(self) -> None:
        """E-03/V-01: the probe must return what the single version authority returns.

        Binds doctor's answer to `engine.read_installed_version` rather than to a literal path,
        so a future change to the probe order cannot silently desynchronize the two again.
        """
        self._install_marker(".aw/system/VERSION", "1.2.1")

        expected = engine.read_installed_version(self.root)
        self.assertEqual(expected, "1.2.1")
        self.assertEqual(
            doctor.probe_environment(self.root).installed_version, expected
        )

    def test_probe_agrees_with_engine_on_legacy_workflows_version(self) -> None:
        """V-01 (second half): the legacy `.agents/workflows/VERSION` location resolves too."""
        self._install_marker(".agents/workflows/VERSION", "1.1.0")

        expected = engine.read_installed_version(self.root)
        self.assertEqual(expected, "1.1.0")
        self.assertEqual(
            doctor.probe_environment(self.root).installed_version, expected
        )

    def test_probe_reads_preset_and_backend_from_canonical_project_config(self) -> None:
        """E-02/V-02: preset and backend come from `.aw/config/project.json`."""
        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            '{"schema_version": 2, "preset": "private-target",'
            ' "records_backend": "repository"}\n',
            encoding="utf-8",
        )

        res = doctor.probe_environment(self.root)
        self.assertEqual(res.preset, "private-target")
        self.assertEqual(res.backend, "repository")

    def test_healthy_installed_target_emits_no_version_not_installed_finding(
        self,
    ) -> None:
        """E-04/V-04: the user-visible symptom - a healthy NON-SOURCE target must not be
        reported as `not installed`.

        Distinct surface from the read tests above: this asserts on the drift entry the read
        DRIVES. It must be a non-source repo, because the finding is gated on
        `not res.is_source_repo`, which is exactly why the framework's own checkout never
        showed the bug.
        """
        packaged = versioning.resolve_version(engine.resolve_source_root(None))
        self._install_marker(".aw/system/VERSION", packaged)
        (self.root / ".aw" / "records").mkdir(parents=True, exist_ok=True)

        res = doctor.probe_environment(self.root)
        self.assertFalse(res.is_source_repo)
        self.assertEqual(res.installed_version, packaged)
        self.assertNotIn(
            "doctor.version-not-installed",
            [d.rule for d in res.drift],
            [f"{d.rule}:{d.detail}" for d in res.drift],
        )

    def test_status_and_doctor_report_the_same_preset_and_backend(self) -> None:
        """E-05/V-05: `aw status` and `aw doctor` share ONE reader, so they cannot diverge."""
        from agent_workflows import cli

        cfg = self.root / ".aw" / "config"
        cfg.mkdir(parents=True)
        (cfg / "project.json").write_text(
            '{"schema_version": 2, "preset": "public-target-private-companion",'
            ' "records_backend": "companion"}\n',
            encoding="utf-8",
        )
        self._install_marker(".aw/system/VERSION", "1.2.1")

        env = doctor.probe_environment(self.root)
        status = cli._collect_repo_status_details(self.root, "1.3.0")

        self.assertEqual(env.preset, "public-target-private-companion")
        self.assertEqual(env.backend, "companion")
        self.assertEqual(status["preset"], env.preset)
        self.assertEqual(status["backend"], env.backend)


if __name__ == "__main__":
    unittest.main()
