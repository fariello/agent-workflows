"""Tests for awdoctor Order 02: the setup-needed notice + release-blockers section on the human
attention board (never in JSON / --check)."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from agent_workflows import cli


class AttentionNoticesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".aw" / "records").mkdir(parents=True)
        # Isolate global config: force `is_configured()` False so setup_needed reflects the fixture,
        # not whatever a prior test left in the real/AW_HOME config (test-order independence).
        from agent_workflows import config as _config

        self._orig_is_configured = _config.is_configured
        _config.is_configured = lambda: False

    def tearDown(self) -> None:
        from agent_workflows import config as _config

        _config.is_configured = self._orig_is_configured
        self._tmp.cleanup()

    def _human(self, extra=None):
        out = io.StringIO()
        argv = ["attention", "--dir", str(self.root), "--no-color"] + (extra or [])
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            try:
                cli.main(argv)
            except SystemExit:
                pass
        return out.getvalue()

    def _json(self):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            try:
                cli.main(["attention", "--dir", str(self.root), "--format", "json"])
            except SystemExit:
                pass
        return out.getvalue()

    def _seed_setup_action(self):
        d = self.root / "aw-state" / "actions" / "open"
        d.mkdir(parents=True, exist_ok=True)
        (d / "setup-repo-v1.md").write_text(
            "- Id: setup-repo\n- Status: open\n", encoding="utf-8"
        )

    def _seed_blocker(self):
        d = self.root / ".aw" / "records" / "backlog" / "open"
        d.mkdir(parents=True, exist_ok=True)
        (d / "20260101-demo-01-aaa111-x.backlog.md").write_text(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: next\n\n## Workflow history\n- 2026-01-01 created (t): x\n",
            encoding="utf-8",
        )

    def test_setup_notice_present(self):
        self._seed_setup_action()
        self.assertIn("setup not complete", self._human())

    def test_setup_notice_absent_without_action(self):
        self.assertNotIn("setup not complete", self._human())

    def test_release_blocker_section_present(self):
        self._seed_blocker()
        self.assertIn("## release-blockers (1)", self._human())

    def test_release_blocker_absent_without_field(self):
        self.assertNotIn("release-blockers", self._human())

    def test_notices_never_in_json(self):
        self._seed_setup_action()
        self._seed_blocker()
        j = self._json()
        self.assertNotIn("setup not complete", j)
        self.assertNotIn("release-blockers", j)


if __name__ == "__main__":
    unittest.main()
