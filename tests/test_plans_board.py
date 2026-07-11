"""Tests for the plan status board helper and the `aw plans` verb (D52 follow-on).

Covers grouping/counts by disposition + readiness, legacy free-text tolerance, the deterministic
`--write-index` STATUS.md, plain (NO_COLOR) output, and the front-matter-only / read-only contract.
"""

from __future__ import annotations

import io
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import plans as plans_mod
from agent_workflows.term import Term


def _write(path: Path, status: str | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "# IPD: x\n\n"
    if status is not None:
        body += f"- Status: {status}\n"
    body += "\n## Goal\n\nx\n"
    path.write_text(body, encoding="utf-8")


def _fixture(root: Path) -> None:
    plans = root / ".agents" / "plans"
    _write(plans / "pending" / "20260101-0000-01-a.md", "draft")
    _write(plans / "pending" / "20260101-0001-01-b.md", "approved")
    _write(plans / "executed" / "20260101-0002-01-c.md", "EXECUTED")  # legacy uppercase
    _write(plans / "executed" / "20260101-0003-01-d.md", "DONE")  # legacy alias
    _write(plans / "not-executed" / "20260101-0004-01-e.md", "not-executed")
    _write(
        plans / "pending" / "20260101-0005-01-f.md", "GHESTALT"
    )  # unknown -> legacy/unknown
    _write(plans / "pending" / "README.md", None)  # must be skipped
    _write(
        root / ".agents" / "prompts" / "reusable" / "p.md", None
    )  # no status tolerated


class NormalizeTests(unittest.TestCase):
    def test_legacy_and_case_mapping(self):
        self.assertEqual(plans_mod.normalize_status("EXECUTED"), "executed")
        self.assertEqual(plans_mod.normalize_status("DONE"), "executed")
        # normalize_status receives a single token (the front-matter regex captures \S+); the
        # legacy "PENDING (awaiting...)" line yields the token "PENDING" -> pending -> to-review.
        self.assertEqual(plans_mod.normalize_status("PENDING"), "to-review")
        self.assertEqual(plans_mod.normalize_status("approved"), "approved")
        self.assertEqual(plans_mod.normalize_status("bogus"), plans_mod.LEGACY_GROUP)
        self.assertIsNone(plans_mod.normalize_status(None))
        self.assertIsNone(plans_mod.normalize_status("  "))


class ScanGroupTests(unittest.TestCase):
    def test_scan_groups_and_counts(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root)
            records = plans_mod.scan(root)
            by = plans_mod.group(records)
            # README.md skipped; 6 plans + 1 prompt = 7 records.
            self.assertEqual(len(records), 7)
            self.assertEqual(
                sorted(by["pending"]), ["approved", "draft", plans_mod.LEGACY_GROUP]
            )
            self.assertEqual(by["executed"]["executed"].__len__(), 2)  # EXECUTED + DONE
            self.assertIn("(no status)", by["reusable"])

    def test_read_only_no_mutation(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root)
            before = {p: p.read_bytes() for p in (root / ".agents").rglob("*.md")}
            plans_mod.scan(root)
            after = {p: p.read_bytes() for p in (root / ".agents").rglob("*.md")}
            self.assertEqual(before, after)


class WriteIndexTests(unittest.TestCase):
    def test_deterministic_index(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root)
            records = plans_mod.scan(root)
            first = plans_mod.render_status_index(root, records)
            second = plans_mod.render_status_index(root, plans_mod.scan(root))
            self.assertEqual(first, second)  # deterministic -> no spurious diff
            self.assertIn("## pending/", first)
            self.assertIn("legacy/unknown", first)
            self.assertTrue(first.endswith("\n"))


class BoardRenderTests(unittest.TestCase):
    def test_plain_output_has_no_ansi(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root)
            buf = io.StringIO()
            term = Term(stream=buf, color=False)
            for rec in plans_mod.scan(root):
                term.line(f"{term.colorize(rec.status or 'x', 'bold')} {rec.path.name}")
            self.assertNotIn("\033[", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
