"""Tests for awrelease Order 02: the Blocks-Release gate field (parse + setter + dangling validation)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import backlog, releases, specs


class BlocksReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_backlog_parse_field(self) -> None:
        item = backlog.parse_item(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: next\n"
        )
        self.assertEqual(item.blocks_release, "next")
        item2 = backlog.parse_item("- Id: aaa111\n- Status: open\n")
        self.assertIsNone(item2.blocks_release)

    def test_specs_read_field(self) -> None:
        lines = (
            "# Spec\n\n- Status: draft\n- Blocks-Release: r1a2b3\n\n## Body\n".split(
                "\n"
            )
        )
        self.assertEqual(specs._read_blocks_release(lines), "r1a2b3")
        self.assertIsNone(
            specs._read_blocks_release("# Spec\n\n- Status: draft\n".split("\n"))
        )

    def test_setter_set_and_clear(self) -> None:
        text = "# X\n\n- Id: aaa111\n- Status: open\n\n## Goal\n\nx\n"
        with_field = releases.set_blocks_release_line(text, "next")
        self.assertIn("- Blocks-Release: next", with_field)
        cleared = releases.set_blocks_release_line(with_field, "-")
        self.assertNotIn("Blocks-Release", cleared)

    def test_dangling_flagged(self) -> None:
        bl = self.root / ".aw" / "records" / "backlog" / "open"
        bl.mkdir(parents=True)
        (bl / "20260101-demo-01-aaa111-x.backlog.md").write_text(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: nonexist\n\n## Workflow history\n- 2026-01-01 created (t): x\n",
            encoding="utf-8",
        )
        drift = releases.check_blocks_release(self.root)
        self.assertTrue(any(d.rule == "check.blocks-release-dangling" for d in drift))

    def test_next_resolves(self) -> None:
        bl = self.root / ".aw" / "records" / "backlog" / "open"
        bl.mkdir(parents=True)
        (bl / "20260101-demo-01-aaa111-x.backlog.md").write_text(
            "- Id: aaa111\n- Status: open\n- Blocks-Release: next\n\n## Workflow history\n- 2026-01-01 created (t): x\n",
            encoding="utf-8",
        )
        # no release yet -> dangling
        self.assertTrue(
            any(
                d.rule == "check.blocks-release-dangling"
                for d in releases.check_blocks_release(self.root)
            )
        )
        # create the single planned release -> next resolves, no drift
        releases.create_release(self.root, "2.0.0", "x")
        self.assertEqual(releases.check_blocks_release(self.root), [])


class PlanBlocksReleaseCheckTests(unittest.TestCase):
    """IPD 7mw7m5 E-01: aw check validates a PLAN's Blocks-Release (dangling + clean)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.pdir = self.root / ".aw" / "records" / "plans" / "pending"
        self.pdir.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _write_plan(self, br_value):
        (self.pdir / "20260101-demo-01-pl0001-x.ipd.md").write_text(
            "# IPD: pl0001\n\n- Date: 2026-08-22\n- Kind: child\n- Status: draft\n"
            f"- Set: demo\n- Order: 1\n- Id: pl0001\n- Blocks-Release: {br_value}\n\n"
            "## Workflow history\n- 2026-08-22 draft (t): x.\n\n## Goal\nx\n",
            encoding="utf-8",
        )

    def test_dangling_plan_blocks_release_flagged(self):
        self._write_plan("nosuchid")
        drift = releases.check_blocks_release(self.root)
        self.assertTrue(
            any(
                d.rule == "check.blocks-release-dangling"
                and "pl0001" in str(d.location)
                for d in drift
            ),
            f"expected dangling flag for the plan; got {drift}",
        )

    def test_resolving_plan_blocks_release_clean(self):
        self._write_plan("next")
        releases.create_release(self.root, "2.0.0", "x")  # single planned release
        drift = releases.check_blocks_release(self.root)
        self.assertEqual(
            [d for d in drift if d.rule == "check.blocks-release-dangling"], []
        )


class IpdSetBlocksReleaseE2ETests(unittest.TestCase):
    """IPD efnn74 E-04: `aw ipd set --blocks-release` writes/clears/resolves and the plan lints clean
    (relies on the child 01 schema recognition of the Blocks-Release field)."""

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

    def test_ipd_set_writes_clears_and_lints_clean(self) -> None:
        from agent_workflows import cli

        # baseline: the conforming fixture lints clean.
        import io
        from unittest.mock import patch

        def _lint():
            buf = io.StringIO()
            with patch("sys.stdout", buf):
                rc = cli.main(["ipd", "lint", "--agent", str(self.plan)])
            return rc, buf.getvalue()

        rc0, _ = _lint()
        self.assertEqual(rc0, 0, "fixture must lint clean before the field is set")

        # write the field
        rc = cli.main(
            [
                "ipd",
                "set",
                "draft",
                "fix000",
                "--blocks-release",
                "next",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc, 0)
        self.assertIn("- Blocks-Release: next", self.plan.read_text(encoding="utf-8"))

        # the plan still lints CONFORMING with the field present (child 01 schema recognition).
        rc1, out1 = _lint()
        self.assertEqual(rc1, 0, f"plan with Blocks-Release must lint clean: {out1}")
        self.assertNotIn("IPD-M103", out1)

        # clear with '-'
        rc2 = cli.main(
            [
                "ipd",
                "set",
                "draft",
                "fix000",
                "--blocks-release",
                "-",
                "--yes",
                "--dir",
                str(self.root),
            ]
        )
        self.assertEqual(rc2, 0)
        self.assertNotIn("Blocks-Release", self.plan.read_text(encoding="utf-8"))

    def test_next_resolution_via_shared_primitive(self) -> None:
        # `next` is stored literally (parity with backlog/specs), and resolve_release maps it to the
        # single planned release record.
        cli_ok = releases.set_blocks_release_line(
            self.plan.read_text(encoding="utf-8"), "next"
        )
        self.assertIn("- Blocks-Release: next", cli_ok)
        releases.create_release(self.root, "2.0.0", "x")
        self.assertIsNotNone(releases.resolve_release(self.root, "next"))


if __name__ == "__main__":
    unittest.main()
