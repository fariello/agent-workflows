"""Tests for the plan status board helper and the `aw plans` verb (D52 follow-on).

Covers grouping/counts by disposition + readiness, legacy free-text tolerance, deterministic
`aw ipd board` output, Set grouping and warnings, plain (NO_COLOR) output, and the
front-matter-only / read-only contract.
"""

from __future__ import annotations

import io
import json
import unittest
import unittest.mock
from pathlib import Path
from tempfile import TemporaryDirectory

from agent_workflows import cli
from agent_workflows import plans as plans_mod
from agent_workflows.term import Term
from tests.record_builder import RecordBuilder


def _write(
    path: Path,
    status: str | None,
    set_id: str | None = None,
    order: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw_fields: dict[str, str | None] = {}
    if status is None:
        effective_status = "draft"
        raw_fields["Status"] = None
    elif status in plans_mod.RECOGNIZED:
        effective_status = status
    else:
        effective_status = "draft"
        raw_fields["Status"] = status
    if set_id is None:
        raw_fields["Set"] = None
    else:
        raw_fields["Set"] = set_id
    if order is None:
        raw_fields["Order"] = None
    else:
        raw_fields["Order"] = order
    text = RecordBuilder().plan(
        title="x",
        status=effective_status,
        body="## Goal\n\nx",
        raw_fields=raw_fields,
        text_only=True,
    )
    path.write_text(text, encoding="utf-8")


def _board(root: Path) -> tuple[int, str]:
    buf = io.StringIO()
    with unittest.mock.patch("sys.stdout", buf):
        rc = cli.main(["ipd", "board", "--dir", str(root)])
    return rc, buf.getvalue()


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


class BoardDeterminismTests(unittest.TestCase):
    def test_deterministic_board(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root)
            rc_first, first = _board(root)
            rc_second, second = _board(root)
            self.assertEqual((rc_first, rc_second), (0, 0))
            self.assertEqual(first, second)  # byte-identical across runs
            self.assertIn("pending/ (", first)
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


class SetOrderTests(unittest.TestCase):
    def test_set_id_and_order_validation(self):
        self.assertTrue(plans_mod.is_set_id_valid("editor-workflow"))
        self.assertTrue(plans_mod.is_set_id_valid("agent-comms2"))
        self.assertFalse(
            plans_mod.is_set_id_valid("Editor_Workflow")
        )  # uppercase/underscore
        self.assertFalse(plans_mod.is_set_id_valid("-leading"))
        self.assertFalse(plans_mod.is_set_id_valid("x" * 41))
        self.assertFalse(plans_mod.is_set_id_valid(""))
        self.assertEqual(plans_mod.parse_order("2"), 2)
        self.assertIsNone(plans_mod.parse_order("0"))
        self.assertIsNone(plans_mod.parse_order("-1"))
        self.assertIsNone(plans_mod.parse_order("two"))
        self.assertIsNone(plans_mod.parse_order(None))

    def test_scan_reads_set_order_and_standalone_default(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            plans = root / ".agents" / "plans"
            _write(
                plans / "pending" / "20260101-0000-01-s1.md",
                "approved",
                "editor-workflow",
                "1",
            )
            _write(
                plans / "pending" / "20260101-0001-01-s2.md",
                "reviewed",
                "editor-workflow",
                "2",
            )
            _write(
                plans / "pending" / "20260101-0002-01-lone.md", "draft"
            )  # standalone
            _write(
                plans / "pending" / "20260101-0003-01-bad.md", "draft", "Bad_ID", "1"
            )  # invalid set id
            recs = {r.path.name: r for r in plans_mod.scan(root)}
            self.assertEqual(recs["20260101-0000-01-s1.md"].set_id, "editor-workflow")
            self.assertEqual(recs["20260101-0000-01-s1.md"].order, 1)
            self.assertIsNone(recs["20260101-0002-01-lone.md"].set_id)  # standalone
            self.assertIsNone(recs["20260101-0002-01-lone.md"].order)
            self.assertIsNone(
                recs["20260101-0003-01-bad.md"].set_id
            )  # malformed -> None

    def test_group_sets_orders_members_and_warns_on_duplicate_order(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            plans = root / ".agents" / "plans"
            _write(
                plans / "pending" / "20260101-0000-01-a.md", "approved", "myset", "2"
            )
            _write(
                plans / "pending" / "20260101-0001-01-b.md", "approved", "myset", "1"
            )
            _write(
                plans / "pending" / "20260101-0002-01-c.md", "approved", "myset", "1"
            )  # dup order
            by_set = plans_mod.group_sets(plans_mod.scan(root))
            self.assertEqual(sorted(by_set), ["myset"])
            members = by_set["myset"]
            self.assertEqual(len(members), 3)
            self.assertEqual(
                plans_mod.set_warnings("myset", members),
                ["set `myset`: duplicate Order values"],
            )
            # Order-1 members sort before the Order-2 member.
            ordered = [
                r.path.name for r in sorted(members, key=plans_mod._set_member_sort_key)
            ]
            self.assertLess(
                ordered.index("20260101-0001-01-b.md"),
                ordered.index("20260101-0000-01-a.md"),
            )

    def test_no_sets_when_no_set_declared(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            _fixture(root)  # none of these declare Set:
            self.assertEqual(plans_mod.group_sets(plans_mod.scan(root)), {})


class BoardCliFilterTests(unittest.TestCase):
    def test_ipd_board_status_not(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            plans = root / ".agents" / "plans"
            _write(plans / "pending" / "20260101-0000-01-a.md", "draft")
            _write(plans / "pending" / "20260101-0001-01-b.md", "approved")
            _write(plans / "executed" / "20260101-0002-01-c.md", "executed")

            # Run with --status-not draft --json
            buf = io.StringIO()
            with unittest.mock.patch("sys.stdout", buf):
                rc = cli.main(
                    [
                        "ipd",
                        "board",
                        "--dir",
                        str(root),
                        "--status-not",
                        "draft",
                        "--json",
                    ]
                )
            self.assertEqual(rc, 0)
            data = json.loads(buf.getvalue())
            plan_statuses = [p["status"] for p in data["data"]["plans"]]
            self.assertNotIn("draft", plan_statuses)
            self.assertIn("approved", plan_statuses)

            # Test invalid status refused with exit 2
            buf_bad = io.StringIO()
            with unittest.mock.patch("sys.stdout", buf_bad):
                rc_bad = cli.main(
                    [
                        "ipd",
                        "board",
                        "--dir",
                        str(root),
                        "--status-not",
                        "bogusvalue",
                        "--json",
                    ]
                )
            self.assertEqual(rc_bad, 2)


if __name__ == "__main__":
    unittest.main()
