"""Tests fencing the history record label contract across both spellings of aw backlog set.

Fences the contract established by IPD jbipfa (backlog awqzuh):
- Genuine transition (--status spelling) writes target status label (E-05(a))
- Genuine transition (positional spelling) writes target status label and agrees with --status (E-05(b))
- Same-status write writes 'same-status' label across both spellings (E-05(c))
- Transition label does not compromise the prior-history preservation property (E-05(d))
- Legacy default label for callers omitting label parameter is 'set' (E-05(e))

All cross-spelling comparisons compare history dates literally (unified onto UTC
per spec 2vev8j 4.4) while normalizing the actor and passing an explicit --message
to prevent failure from defaulted message asymmetry.
"""

from __future__ import annotations

import contextlib
import io
import re
from pathlib import Path
import tempfile
import unittest

from agent_workflows import attention as att
from agent_workflows import attention_contract as ac
from agent_workflows import backlog, cli

_ACTOR_PAREN = re.compile(r"\((?:aw backlog|aw set)\)")


def _normalize_history_record(record: str) -> str:
    """Normalize actor in a history record line for cross-spelling parity comparisons.

    Hides one known out-of-scope asymmetry:
    1. Actor: '(aw backlog)' vs '(aw set)' truthfully identifies the writer and is deliberate.
    (Date skew fnb8pl is fixed by routing all writers to UTC per spec 2vev8j 4.4; dates are compared literally).
    """
    return _ACTOR_PAREN.sub("(HIST_ACTOR)", record.strip())


def _setup_backlog_repo(root: Path) -> None:
    for sub in ("open", "graduated", "done", "blocked", "parked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)


class HistoryLabelParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _setup_backlog_repo(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_a_genuine_transition_status_spelling_records_graduated_label(self) -> None:
        """(a) Genuine transition (open -> graduated) via --status spelling records 'graduated' label."""
        item = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-test-item.backlog.md"
        )
        item.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: test item\n\n"
            "## Workflow history\n"
            "- 2026-09-01 created (tester): initial\n\n"
            "Prose body\n",
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
                    "graduated",
                    "--message",
                    "carrier handed off",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc, 0)

        moved = self.root / ".aw" / "records" / "backlog" / "graduated" / item.name
        self.assertTrue(moved.exists(), f"expected moved item at {moved}")
        text = moved.read_text(encoding="utf-8")
        records = [
            ln
            for ln in att._history_section_lines(text)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertGreaterEqual(len(records), 2)
        newest = records[0]
        # Assert the label token is positively 'graduated'
        self.assertIn(" graduated (aw backlog): carrier handed off", newest)

    def test_b_genuine_transition_positional_spelling_agrees_with_status_spelling(
        self,
    ) -> None:
        """(b) Genuine transition via positional spelling records 'graduated' label and agrees with --status."""
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-item-1.backlog.md"
        )
        f2 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0002-item-2.backlog.md"
        )
        f1.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: item 1\n\n"
            "## Workflow history\n"
            "- 2026-09-01 created (tester): initial\n\n"
            "Prose body\n",
            encoding="utf-8",
        )
        f2.write_text(
            "- Id: bk0002\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: item 2\n\n"
            "## Workflow history\n"
            "- 2026-09-01 created (tester): initial\n\n"
            "Prose body\n",
            encoding="utf-8",
        )

        # Route 1: --status spelling
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc1 = cli.main(
                [
                    "backlog",
                    "set",
                    str(f1),
                    "--status",
                    "graduated",
                    "--message",
                    "handed off to plan",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc1, 0)

        # Route 2: positional spelling
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc2 = cli.main(
                [
                    "backlog",
                    "set",
                    "graduated",
                    "bk0002",
                    "--yes",
                    "--message",
                    "handed off to plan",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc2, 0)

        res1_file = self.root / ".aw" / "records" / "backlog" / "graduated" / f1.name
        res2_file = self.root / ".aw" / "records" / "backlog" / "graduated" / f2.name
        self.assertTrue(res1_file.exists())
        self.assertTrue(res2_file.exists())

        rec1 = [
            ln
            for ln in att._history_section_lines(res1_file.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ][0]
        rec2 = [
            ln
            for ln in att._history_section_lines(res2_file.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ][0]

        # Positively assert label tokens
        self.assertIn(" graduated (aw backlog): handed off to plan", rec1)
        self.assertIn(" graduated (aw set): handed off to plan", rec2)

        # Normalized comparison (hiding actor and date skew)
        norm1 = _normalize_history_record(rec1)
        norm2 = _normalize_history_record(rec2)
        self.assertEqual(norm1, norm2)

    def test_c_same_status_write_records_same_status_on_both_spellings(self) -> None:
        """(c) Same-status write (open -> open with explicit message) records 'same-status' through both."""
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-item-1.backlog.md"
        )
        f2 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0002-item-2.backlog.md"
        )
        f1.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: item 1\n\n"
            "## Workflow history\n"
            "- 2026-09-01 created (tester): initial\n\n"
            "Prose body\n",
            encoding="utf-8",
        )
        f2.write_text(
            "- Id: bk0002\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: item 2\n\n"
            "## Workflow history\n"
            "- 2026-09-01 created (tester): initial\n\n"
            "Prose body\n",
            encoding="utf-8",
        )

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc1 = cli.main(
                [
                    "backlog",
                    "set",
                    str(f1),
                    "--status",
                    "open",
                    "--message",
                    "clarification note",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc1, 0)

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc2 = cli.main(
                [
                    "backlog",
                    "set",
                    "open",
                    "bk0002",
                    "--yes",
                    "--message",
                    "clarification note",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc2, 0)

        rec1 = [
            ln
            for ln in att._history_section_lines(f1.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ][0]
        rec2 = [
            ln
            for ln in att._history_section_lines(f2.read_text(encoding="utf-8"))
            if ac.HISTORY_RECORD_RE.match(ln)
        ][0]

        # Positively assert label tokens
        self.assertIn(" same-status (aw backlog): clarification note", rec1)
        self.assertIn(" same-status (aw set): clarification note", rec2)

        norm1 = _normalize_history_record(rec1)
        norm2 = _normalize_history_record(rec2)
        self.assertEqual(norm1, norm2)

    def test_d_status_spelling_preserves_prior_history_records(self) -> None:
        """(d) Transition label does not compromise the prior-history preservation property (3 -> 4)."""
        item = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-multi.backlog.md"
        )
        original_records = [
            "- 2026-03-03 set (aw backlog): third",
            "- 2026-02-02 set (aw backlog): second",
            "- 2026-01-01 created (aw backlog): first",
        ]
        item.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: medium\n"
            "- Work-Kind: chore\n"
            "- Summary: multi\n\n"
            "## Workflow history\n" + "\n".join(original_records) + "\n\n"
            "Prose body\n",
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
                    "graduated",
                    "--message",
                    "transitioning",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc, 0)

        moved = self.root / ".aw" / "records" / "backlog" / "graduated" / item.name
        self.assertTrue(moved.exists())
        text = moved.read_text(encoding="utf-8")
        records = [
            ln
            for ln in att._history_section_lines(text)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(records), 4)
        self.assertIn("transitioning", records[0])
        self.assertEqual(records[1:], original_records)

    def test_e_reattach_history_default_label_is_legacy_set(self) -> None:
        """(e) backlog._reattach_history without explicit label emits legacy 'set (aw backlog)'."""
        prior_records = [
            "- 2026-03-03 note (tester): note 3",
            "- 2026-02-02 note (tester): note 2",
            "- 2026-01-01 created (tester): initial",
        ]
        old_text = (
            "- Id: bk0001\n- Status: open\n\n"
            "## Workflow history\n" + "\n".join(prior_records) + "\n\n"
            "Body\n"
        )
        rendered = (
            "- Id: bk0001\n- Status: done\n\n"
            "## Workflow history\n"
            "- 2026-10-01 created (aw backlog): item\n\n"
            "Body\n"
        )

        res = backlog._reattach_history(old_text, rendered, "done", "test message")
        history_lines = [
            ln
            for ln in att._history_section_lines(res)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(history_lines), 4)
        self.assertIn(" set (aw backlog): test message", history_lines[0])
        self.assertEqual(history_lines[1:], prior_records)


if __name__ == "__main__":
    unittest.main()
