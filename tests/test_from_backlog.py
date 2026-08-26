"""Tests for bklggrad Order ku93tn: the From-Backlog link field.

Covers schema recognition (lint-clean, no IPD-M103), the idempotent write primitive
(`set_from_backlog_line`), the `aw ipd set --from-backlog` setter (write/clear + same-status
no-op persist), and the `check.from-backlog-dangling` cross-tree reference check.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflows import cli, ipd_schema, releases


class FromBacklogSchemaTests(unittest.TestCase):
    """V-02: an IPD carrying `- From-Backlog: <id6>` lints CONFORMING (no IPD-M103)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        from tests.support import CONFORMING_ORCHESTRATOR

        self.plan = self.plans / "20260803-fixture-00-fix000-sample-fixture.ipd.md"
        base = CONFORMING_ORCHESTRATOR.read_text(encoding="utf-8")
        # Inject the From-Backlog field right after the `- Id:` line.
        self.plan.write_text(
            releases.set_from_backlog_line(base, "aaa111"), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_field_is_recognized(self) -> None:
        self.assertIn("From-Backlog", ipd_schema.META_RECOGNIZED)
        self.assertNotIn("From-Backlog", ipd_schema.META_REQUIRED)

    def _lint(self):
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc = cli.main(["ipd", "lint", "--agent", str(self.plan)])
        return rc, buf.getvalue()

    def test_lints_clean_with_from_backlog(self) -> None:
        rc, out = self._lint()
        self.assertEqual(rc, 0, f"plan with From-Backlog must lint clean: {out}")
        self.assertNotIn("IPD-M103", out)
        self.assertIn("- From-Backlog: aaa111", self.plan.read_text(encoding="utf-8"))


class FromBacklogPrimitiveTests(unittest.TestCase):
    """V-03: `set_from_backlog_line` sets, overwrites, and clears idempotently."""

    def test_set_overwrite_clear_round_trip(self) -> None:
        text = "# X\n\n- Id: aaa111\n- Status: open\n\n## Goal\n\nx\n"
        with_field = releases.set_from_backlog_line(text, "aaa111")
        self.assertIn("- From-Backlog: aaa111", with_field)
        # anchored right after Status
        self.assertIn("- Status: open\n- From-Backlog: aaa111", with_field)
        # overwrite (idempotent: exactly one line)
        over = releases.set_from_backlog_line(with_field, "bbb222")
        self.assertIn("- From-Backlog: bbb222", over)
        self.assertEqual(over.count("From-Backlog"), 1)
        # clear
        cleared = releases.set_from_backlog_line(over, "-")
        self.assertNotIn("From-Backlog", cleared)
        # clearing with None also works and leaves other metadata intact
        self.assertNotIn("From-Backlog", releases.set_from_backlog_line(over, None))
        self.assertIn("- Status: open", cleared)


class IpdSetFromBacklogE2ETests(unittest.TestCase):
    """V-04: `aw ipd set --from-backlog` writes, persists on a same-status no-op, and clears."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.plans = self.root / ".aw" / "records" / "plans" / "pending"
        self.plans.mkdir(parents=True)
        from tests.support import CONFORMING_ORCHESTRATOR

        self.plan = self.plans / "20260803-fixture-00-fix000-sample-fixture.ipd.md"
        self.plan.write_text(
            CONFORMING_ORCHESTRATOR.read_text(encoding="utf-8"), encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _status(self) -> str:
        for line in self.plan.read_text(encoding="utf-8").split("\n"):
            if line.startswith("- Status:"):
                return line.split(":", 1)[1].strip()
        return ""

    def test_write_noop_persist_and_clear(self) -> None:
        start_status = self._status()
        # write on a same-status (no-op) transition: the hoisted write must still persist.
        rc = cli.main(
            [
                "ipd",
                "set",
                start_status,
                "fix000",
                "--from-backlog",
                "aaa111",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- From-Backlog: aaa111", self.plan.read_text(encoding="utf-8"))

        # the plan still lints clean with the field present.
        buf = io.StringIO()
        with patch("sys.stdout", buf):
            rc_lint = cli.main(["ipd", "lint", "--agent", str(self.plan)])
        self.assertEqual(rc_lint, 0, buf.getvalue())
        self.assertNotIn("IPD-M103", buf.getvalue())

        # clear with '-'
        rc2 = cli.main(
            [
                "ipd",
                "set",
                self._status(),
                "fix000",
                "--from-backlog",
                "-",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc2, 0)
        self.assertNotIn("From-Backlog", self.plan.read_text(encoding="utf-8"))


class FromBacklogDanglingCheckTests(unittest.TestCase):
    """V-05: `check.from-backlog-dangling` fires on a nonexistent target, clean when it resolves."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pdir = self.root / ".aw" / "records" / "plans" / "pending"
        self.pdir.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_plan(self, fb_value: str) -> None:
        (self.pdir / "20260101-demo-01-pl0001-x.ipd.md").write_text(
            "# IPD: pl0001\n\n- Date: 2026-08-22\n- Kind: child\n- Status: draft\n"
            f"- Set: demo\n- Order: 1\n- Id: pl0001\n- From-Backlog: {fb_value}\n\n"
            "## Workflow history\n- 2026-08-22 draft (t): x.\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def _write_backlog_item(self, id6: str) -> None:
        bl = self.root / ".aw" / "records" / "backlog" / "open"
        bl.mkdir(parents=True, exist_ok=True)
        (bl / f"20260101-demo-01-{id6}-x.backlog.md").write_text(
            f"- Id: {id6}\n- Status: open\n- Set: demo\n- Priority: high\n"
            "- Kind: chore\n- Summary: x\n\n## Workflow history\n- 2026-01-01 created (t): x\n",
            encoding="utf-8",
        )

    def test_dangling_flagged(self) -> None:
        self._write_plan("nosuchid")
        drift = releases.check_from_backlog(self.root)
        self.assertTrue(
            any(
                d.rule == "check.from-backlog-dangling" and "pl0001" in str(d.location)
                for d in drift
            ),
            f"expected dangling flag; got {drift}",
        )

    def test_resolving_clean(self) -> None:
        self._write_backlog_item("aaa111")
        self._write_plan("aaa111")
        drift = releases.check_from_backlog(self.root)
        self.assertEqual(
            [d for d in drift if d.rule == "check.from-backlog-dangling"], []
        )


if __name__ == "__main__":
    unittest.main()
