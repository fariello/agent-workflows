"""Tests for awdoctorfix Order 03: quiet the ? age marker on history-less trees + aw doctor
source-repo awareness (PR-001) + summary line."""

from __future__ import annotations

import pytest

import io
import tempfile
import types
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import attention, doctor

# Heavy subprocess/CLI suite; excluded from the fast default run (see pyproject addopts
# `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow


class AgeMarkerTests(unittest.TestCase):
    def test_historyless_trees_have_no_question_mark(self):
        self.assertEqual(attention._age_marker(None, "research"), "")
        self.assertEqual(attention._age_marker(None, "actions"), "")

    def test_history_trees_still_flag_unknown(self):
        self.assertEqual(attention._age_marker(None, "backlog"), "?")
        self.assertEqual(attention._age_marker(None, "plans"), "?")

    def test_stale_and_recent(self):
        from datetime import date, timedelta

        old = (date.today() - timedelta(days=60)).strftime("%Y-%m-%d")
        recent = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.assertEqual(attention._age_marker(old, "backlog"), "!")
        self.assertEqual(attention._age_marker(recent, "backlog"), "")


class VersionDriftSourceRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_source_checkout_skips_version_probe(self):
        # framework source: pyproject names agent-workflows + agent_workflows/ dir + no VERSION
        (self.root / "agent_workflows").mkdir()
        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "agent-workflows"\n', encoding="utf-8"
        )
        self.assertEqual(doctor._version_drift(self.root), [])

    def test_consumer_repo_still_flags(self):
        # a downstream repo that only lists agent-workflows as a dep (no agent_workflows/ dir, no VERSION)
        (self.root / "pyproject.toml").write_text(
            '[project]\nname = "my-app"\ndependencies = ["agent-workflows"]\n',
            encoding="utf-8",
        )
        drift = doctor._version_drift(self.root)
        self.assertTrue(any(d.rule == "doctor.version-not-installed" for d in drift))

    def test_installed_target_stale_flagged(self):
        # an installed target with a VERSION that does not match packaged
        (self.root / ".aw").mkdir()
        (self.root / ".aw" / "VERSION").write_text("0.0.1\n", encoding="utf-8")
        drift = doctor._version_drift(self.root)
        # versioning.status('0.0.1', <dev>) is not 'current'; some version-* drift is emitted
        self.assertTrue(any(d.rule.startswith("doctor.version-") for d in drift))


class DoctorSummaryTests(unittest.TestCase):
    def test_summary_and_untracked_note(self):
        drift = [
            attention.core.Drift(
                "<git>", "doctor.git-untracked", "3 untracked file(s)"
            ),
        ]
        # monkeypatch run_doctor to return a fixed untracked-only drift
        orig = doctor.run_doctor
        doctor.run_doctor = lambda root: drift
        try:
            from agent_workflows import term as T

            out = io.StringIO()
            term = T.Term(stream=out, color=False)
            with redirect_stdout(out), redirect_stderr(io.StringIO()):
                rc = doctor.run(
                    types.SimpleNamespace(dir=".", as_agent=False), term=term
                )
            text = out.getvalue()
        finally:
            doctor.run_doctor = orig
        self.assertEqual(rc, 1)
        self.assertIn("finding(s) (git:", text)
        self.assertIn("informational", text)


if __name__ == "__main__":
    unittest.main()
