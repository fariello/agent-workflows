"""Tests restoring outcome coverage for history provenance and sidecar routing.

Fences the durability and provenance behaviors restored after being trimmed in 19313eed:
- Prior inline history preservation through backlog transitions (E-03(d))
- Prior inline history preservation through specs note (E-03(e))
- Sidecar failure reporting and non-blocking inline write (E-03(f))
- Spec 20260818-1525-02 AC1 pin: sidecar append + inline prepend preservation (E-03(g))
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention as att
from agent_workflows import attention_contract as ac
from agent_workflows import cli, record_history


class HistoryProvenanceRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.dir = self.root / ".aw" / "records" / "backlog" / "open"
        self.dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_a_legacy_item_keeps_every_prior_record_through_a_transition(self) -> None:
        """(d) aw backlog set --status on a legacy multi-record item preserves every prior record."""
        item = self.dir / "20260101-demo-01-lg0001-x.backlog.md"
        item.write_text(
            "- Id: lg0001\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n"
            "- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n"
            "- 2026-03-03 set (aw backlog): third\n"
            "- 2026-02-02 set (aw backlog): second\n"
            "- 2026-01-01 created (aw backlog): first\n",
            encoding="utf-8",
        )
        before = [
            ln
            for ln in att._history_section_lines(item.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(before), 3)

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    str(item),
                    "--status",
                    "done",
                    "--message",
                    "a real transition",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc, 0)
        moved = self.root / ".aw" / "records" / "backlog" / "done" / item.name
        after = [
            ln
            for ln in att._history_section_lines(moved.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(after), 4)
        self.assertIn("a real transition", after[0])
        self.assertEqual(
            after[1:], before, "every prior record must survive verbatim, in order"
        )

    def test_specs_preserves_inline(self) -> None:
        """(e) aw specs note twice on a multi-record spec preserves every prior record, newest-first."""
        specs_dir = self.root / ".aw" / "records" / "specs"
        specs_dir.mkdir(parents=True)
        spec = specs_dir / "20260101-aaa333-01-aaa333-demo.spec.md"
        spec.write_text(
            "# Spec: demo\n\n- Date: 2026-01-01\n- Status: draft\n- Id: aaa333\n\n"
            "## Workflow history\n- 2026-01-02 to-review (t): b\n- 2026-01-01 draft (t): a\n",
            encoding="utf-8",
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc1 = cli.main(
                [
                    "specs",
                    "note",
                    str(spec),
                    "--message",
                    "first note",
                    "--date",
                    "2026-01-03",
                ]
            )
            rc2 = cli.main(
                [
                    "specs",
                    "note",
                    str(spec),
                    "--message",
                    "second note",
                    "--date",
                    "2026-01-04",
                ]
            )
        self.assertEqual(rc1, 0)
        self.assertEqual(rc2, 0)

        records = [
            ln
            for ln in att._history_section_lines(spec.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(
            records,
            [
                "- 2026-01-04 note (aw specs): second note",
                "- 2026-01-03 note (aw specs): first note",
                "- 2026-01-02 to-review (t): b",
                "- 2026-01-01 draft (t): a",
            ],
        )

    def test_backlog_set_appends_sidecar_and_preserves_inline(self) -> None:
        """(g) Spec AC1 pin: aw backlog set --status appends exactly one sidecar line and prepends exactly one inline record leaving priors in place."""
        item = self.dir / "20260101-demo-01-aaa111-x.backlog.md"
        item.write_text(
            "- Id: aaa111\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n- 2026-01-02 set (aw backlog): newer\n- 2026-01-01 created (aw backlog): x\n",
            encoding="utf-8",
        )
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    str(item),
                    "--status",
                    "done",
                    "--message",
                    "finished",
                    "--dir",
                    str(self.root),
                    "--no-commit",
                ]
            )
        self.assertEqual(rc, 0)
        moved = self.root / ".aw" / "records" / "backlog" / "done" / item.name
        text = moved.read_text(encoding="utf-8")
        inline = [
            ln
            for ln in att._history_section_lines(text)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(inline), 3, inline)
        self.assertIn("finished", inline[0])
        self.assertIn("newer", inline[1])
        self.assertIn("created", inline[2])

        recs = record_history.read_for(self.root, "aaa111")
        self.assertEqual(len(recs), 1)
        self.assertIn("finished", recs[0]["message"])


class SidecarFailureIsReportedTests(unittest.TestCase):
    """A failed sidecar write is REPORTED and never costs the inline record (plan `vhbvwz` E-04)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self._orig_append = record_history.append

    def tearDown(self) -> None:
        record_history.append = self._orig_append
        self._tmp.cleanup()

    def _break_the_sidecar(self) -> None:
        def boom(*_a, **_k):
            raise OSError(28, "No space left on device")

        record_history.append = boom

    def test_backlog_new_reports_and_still_writes_the_inline_record(self) -> None:
        (self.root / ".aw" / "records" / "backlog" / "open").mkdir(parents=True)
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(
                [
                    "backlog",
                    "new",
                    "--dir",
                    str(self.root),
                    "--summary",
                    "a summary",
                    "--set",
                    "demo",
                    "--priority",
                    "medium",
                    "--work-kind",
                    "chore",
                    "--message",
                    "the recorded reason",
                    "--apply",
                ]
            )
        self.assertEqual(rc, 0)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        item = next((self.root / ".aw" / "records" / "backlog" / "open").glob("*.md"))
        self.assertIn("the recorded reason", item.read_text(encoding="utf-8"))

    def test_backlog_set_reports_and_still_writes_the_inline_record(self) -> None:
        d = self.root / ".aw" / "records" / "backlog" / "open"
        d.mkdir(parents=True)
        item = d / "20260101-demo-01-aaa222-x.backlog.md"
        item.write_text(
            "- Id: aaa222\n- Status: open\n- Priority: medium\n- Work-Kind: chore\n"
            "- Set: demo\n- Summary: x\n\n"
            "## Workflow history\n- 2026-01-01 created (aw backlog): x\n",
            encoding="utf-8",
        )
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(
                [
                    "backlog",
                    "set",
                    str(item),
                    "--dir",
                    str(self.root),
                    "--status",
                    "done",
                    "--message",
                    "why it is done",
                    "--no-commit",
                ]
            )
        self.assertEqual(rc, 0)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        moved = (
            self.root / ".aw" / "records" / "backlog" / "done" / item.name
        ).read_text(encoding="utf-8")
        self.assertIn("why it is done", moved)
        self.assertIn("- 2026-01-01 created", moved)

    def test_specs_note_reports_and_still_writes_the_inline_record(self) -> None:
        d = self.root / ".aw" / "records" / "specs"
        d.mkdir(parents=True)
        spec = d / "20260101-aaa333-01-aaa333-demo.spec.md"
        spec.write_text(
            "# Spec: demo\n\n- Date: 2026-01-01\n- Status: draft\n- Id: aaa333\n\n"
            "## Workflow history\n- 2026-01-01 draft (aw specs): created.\n",
            encoding="utf-8",
        )
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err), contextlib.redirect_stdout(io.StringIO()):
            rc = cli.main(
                [
                    "specs",
                    "note",
                    str(spec),
                    "--message",
                    "the note that matters",
                    "--date",
                    "2026-02-02",
                ]
            )
        self.assertEqual(rc, 0)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        self.assertIn("the note that matters", spec.read_text(encoding="utf-8"))

    def test_the_advisory_helper_returns_false_rather_than_raising(self) -> None:
        self._break_the_sidecar()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ok = record_history.append_advisory(
                self.root,
                id6="aaa555",
                tree="backlog",
                workflow="aw backlog set",
                actor="aw backlog",
                message="m",
            )
        self.assertFalse(ok)
        self.assertIn("could not append to the history sidecar", err.getvalue())
        record_history.append = self._orig_append
        self.assertTrue(
            record_history.append_advisory(
                self.root,
                id6="aaa555",
                tree="backlog",
                workflow="aw backlog set",
                actor="aw backlog",
                message="m",
            )
        )
