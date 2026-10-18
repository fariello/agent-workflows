"""Tests for awdoctorfix Order 03: quiet the ? age marker on history-less trees + aw doctor
source-repo awareness (PR-001) + summary line.

Restored under backlog q86fxm, findings b1mx2w, from revision 19313eed^.
Doctor summary tests deliberately not restored (PR-004: calls doctor.run on working directory, took 62-66s CPU, trips 60s hang guard; _version_drift is reached by VersionDriftSourceRepoTests).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import attention, doctor

pytestmark = pytest.mark.core


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


if __name__ == "__main__":
    unittest.main()
