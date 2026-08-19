"""Tests for awselect Order 02: `aw show` resolves a RECORDS artifact (id6/etc.) first, then the
action ledger. Verifies `aw show pp6y76` finds a records plan and an unknown ref returns 1."""

from __future__ import annotations

import io
import tempfile
import types
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from agent_workflows import cli
from agent_workflows.term import Term


class ShowRecordsTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name)
        pend = self.repo / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        (pend / "20260101-demo-01-pp6y76-example.ipd.md").write_text(
            "# IPD: example\n\n- Id: pp6y76\n- Status: approved\n\n## Goal\n\nMARKER_SHOW_BODY\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, ref: str) -> tuple[int, str]:
        args = types.SimpleNamespace(action_ref=ref, dir=str(self.repo), no_color=True)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli._run_show(args, Term(color=False))
        return rc, buf.getvalue()

    def test_records_artifact_found(self) -> None:
        rc, out = self._run("pp6y76")
        self.assertEqual(rc, 0)
        self.assertIn("MARKER_SHOW_BODY", out)

    def test_unknown_ref_returns_1(self) -> None:
        rc, _out = self._run("nonexistent-xyz")
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()
