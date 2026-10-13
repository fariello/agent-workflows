"""Behavioral tests for the shared ## Workflow history bounding rule (Set histdedup, IPD kgv213).

Validates:
- (a) well-formed multi-record block returns all records newest-first and the body;
- (b) F-01 indented-only fixture returns records == [];
- (c) tk1gqo shape (column-zero records, blank line, prose, indented quoted records) returns
      only the column-zero records;
- (d) wrapped record (column-zero record followed directly by indented continuation lines)
      keeps following column-zero records inside the block, and record_lines carries continuation lines;
- (e) blank-separated indented quotation directly under the block is excluded from records and
      record_lines, and body starts with that line's indentation intact;
- (e2) writer round-trip (F-06/F-07): close_on_answer for wrapped and quoted fixtures preserves each
       record exactly once and does not promote quotations to records;
- (f) end-to-end aw backlog set under BOTH spellings on the F-01 fixture dated utc_history_date()
      writes a column-zero record;
- (g) predicate same_status_message_is_duplicate and backlog._prior_history_records agree
      (predicate True implies prior records non-empty);
- (h) specs path: aw specs note on an indented-history spec fixture appends a column-zero note record.

Conforms strictly to GUIDING_PRINCIPLES P16: tests observable outcomes, file contents and exit codes;
contains zero source inspection or caller counts.
"""

from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as core
from agent_workflows import attention_contract as ac
from agent_workflows import backlog
from agent_workflows import cli
from agent_workflows import set_records
from agent_workflows.status_set import same_status_message_is_duplicate


def _setup_backlog_repo(root: Path) -> None:
    for sub in ("open", "graduated", "done", "blocked", "parked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)


class HistoryBlockBoundingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        _setup_backlog_repo(self.root)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_a_well_formed_multi_record_block(self) -> None:
        """(a) Well-formed multi-record block returns all records newest-first and the body."""
        text = (
            "- Id: bk0001\n"
            "- Status: open\n\n"
            "## Workflow history\n"
            "- 2026-10-12 second (tester): second note\n"
            "- 2026-10-11 first (tester): first note\n\n"
            "Prose body line 1\n"
            "Prose body line 2\n"
        )
        hb = ac.history_block(text)
        expected_records = [
            "- 2026-10-12 second (tester): second note",
            "- 2026-10-11 first (tester): first note",
        ]
        self.assertEqual(hb.records, expected_records)
        self.assertEqual(hb.record_lines, expected_records)
        self.assertEqual(hb.body, "Prose body line 1\nProse body line 2")
        self.assertEqual(
            ac.newest_history_record(hb.records),
            "- 2026-10-12 second (tester): second note",
        )

    def test_b_f01_indented_only_fixture(self) -> None:
        """(b) F-01 indented-only fixture returns records == []."""
        today = core.utc_history_date()
        text = (
            "- Id: bk0001\n"
            "- Status: open\n\n"
            "## Workflow history\n"
            f"    - {today} same-status (aw backlog): metadata only\n\n"
            "Prose body\n"
        )
        hb = ac.history_block(text)
        self.assertEqual(hb.records, [])
        self.assertEqual(hb.record_lines, [])
        self.assertTrue(
            hb.body.startswith(f"    - {today} same-status (aw backlog): metadata only")
        )
        self.assertIn("Prose body", hb.body)
        self.assertIsNone(ac.newest_history_record(hb.records))

    def test_c_tk1gqo_shape_prose_quoted_records(self) -> None:
        """(c) tk1gqo shape: column-zero records, blank line, prose with indented quoted records."""
        text = (
            "## Workflow history\n"
            "- 2026-10-12 second (tester): second note\n"
            "- 2026-10-11 first (tester): first note\n\n"
            "Prose describing the issue:\n\n"
            "    - 2026-01-01 quoted (tester): example\n"
            "    - 2026-01-02 quoted (tester): another example\n"
        )
        hb = ac.history_block(text)
        expected_records = [
            "- 2026-10-12 second (tester): second note",
            "- 2026-10-11 first (tester): first note",
        ]
        self.assertEqual(hb.records, expected_records)
        self.assertEqual(hb.record_lines, expected_records)
        self.assertIn("Prose describing the issue:", hb.body)
        self.assertIn("    - 2026-01-01 quoted (tester): example", hb.body)

    def test_d_wrapped_record_with_continuation_lines(self) -> None:
        """(d) Wrapped record: column-zero record directly followed by indented continuation lines."""
        text = (
            "## Workflow history\n"
            "- 2026-10-12 second (tester): second note\n"
            "  wrapped continuation line 1\n"
            "  wrapped continuation line 2\n"
            "- 2026-10-11 first (tester): first note\n\n"
            "Prose body\n"
        )
        hb = ac.history_block(text)
        self.assertEqual(
            hb.records,
            [
                "- 2026-10-12 second (tester): second note",
                "- 2026-10-11 first (tester): first note",
            ],
        )
        self.assertEqual(
            hb.record_lines,
            [
                "- 2026-10-12 second (tester): second note",
                "  wrapped continuation line 1",
                "  wrapped continuation line 2",
                "- 2026-10-11 first (tester): first note",
            ],
        )
        self.assertEqual(hb.body, "Prose body")

    def test_e_blank_separated_indented_quotation(self) -> None:
        """(e) Blank-separated indented quotation directly under block is excluded from records."""
        text = (
            "## Workflow history\n"
            "- 2026-10-12 second (tester): second note\n\n"
            "    - 2026-01-01 quoted (tester): example\n"
            "    further indented body\n"
        )
        hb = ac.history_block(text)
        self.assertEqual(hb.records, ["- 2026-10-12 second (tester): second note"])
        self.assertEqual(hb.record_lines, ["- 2026-10-12 second (tester): second note"])
        self.assertEqual(
            hb.body,
            "    - 2026-01-01 quoted (tester): example\n    further indented body",
        )

    def test_e2_writer_round_trip_wrapped_and_quoted(self) -> None:
        """(e2) Writer round-trip (F-06/F-07): close_on_answer for wrapped and quoted fixtures."""
        today = core.utc_history_date()
        # 1. Wrapped fixture as a blocked decision item
        wrapped_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "blocked"
            / f"{today.replace('-', '')}-demo-01-bk0001-wrapped.backlog.md"
        )
        wrapped_content = (
            "- Id: bk0001\n"
            "- Status: blocked\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: followup\n"
            "- Summary: wrapped item\n"
            "- Gate-Kind: decision\n"
            "- Gate-Ref: D101\n\n"
            "## Workflow history\n"
            "- 2026-10-10 created (tester): created\n"
            "  wrapped continuation\n"
            "- 2026-10-09 prior (tester): prior note\n\n"
            "Prose body\n"
        )
        wrapped_file.write_text(wrapped_content, encoding="utf-8")

        dest1 = set_records.close_on_answer(self.root, wrapped_file)
        self.assertTrue(dest1.exists())
        self.assertEqual(dest1.parent.name, "done")
        dest1_text = dest1.read_text(encoding="utf-8")

        # Every original record occurs EXACTLY ONCE
        self.assertEqual(dest1_text.count("2026-10-10 created (tester): created"), 1)
        self.assertEqual(dest1_text.count("2026-10-09 prior (tester): prior note"), 1)
        # Continuation line is directly under its record
        lines1 = dest1_text.splitlines()
        rec_idx = lines1.index("- 2026-10-10 created (tester): created")
        self.assertEqual(lines1[rec_idx + 1], "  wrapped continuation")
        # history_block.records has new done record + original records
        hb1 = ac.history_block(dest1_text)
        self.assertEqual(
            hb1.records,
            [
                f"- {today} done (aw backlog): question answered; close-on-answer",
                "- 2026-10-10 created (tester): created",
                "- 2026-10-09 prior (tester): prior note",
            ],
        )

        # 2. Blank-separated indented quotation fixture
        quoted_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "blocked"
            / f"{today.replace('-', '')}-demo-01-bk0002-quoted.backlog.md"
        )
        quoted_content = (
            "- Id: bk0002\n"
            "- Status: blocked\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: followup\n"
            "- Summary: quoted item\n"
            "- Gate-Kind: decision\n"
            "- Gate-Ref: D102\n\n"
            "## Workflow history\n"
            "- 2026-10-10 created (tester): created\n\n"
            "    - 2026-01-01 quoted (tester): example\n\n"
            "Prose body\n"
        )
        quoted_file.write_text(quoted_content, encoding="utf-8")

        dest2 = set_records.close_on_answer(self.root, quoted_file)
        self.assertTrue(dest2.exists())
        self.assertEqual(dest2.parent.name, "done")
        dest2_text = dest2.read_text(encoding="utf-8")

        hb2 = ac.history_block(dest2_text)
        # Quoted line was NOT promoted to a record
        self.assertEqual(
            hb2.records,
            [
                f"- {today} done (aw backlog): question answered; close-on-answer",
                "- 2026-10-10 created (tester): created",
            ],
        )
        self.assertIn("    - 2026-01-01 quoted (tester): example", dest2_text)

    def test_f_end_to_end_backlog_set_both_spellings(self) -> None:
        """(f) End to end: aw backlog set writes column-0 record on F-01 fixture dated utc_history_date()."""
        today = core.utc_history_date()

        # 1. Test --status spelling
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20261012-demo-01-bk0001-item.backlog.md"
        )
        f1.write_text(
            "- Id: bk0001\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: item 1\n\n"
            "## Workflow history\n"
            f"    - {today} same-status (aw backlog): metadata only\n\n"
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
                    "metadata only",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc1, 0)
        text1 = f1.read_text(encoding="utf-8")
        hb1 = ac.history_block(text1)
        self.assertGreaterEqual(len(hb1.records), 1)
        self.assertTrue(
            any(
                r.startswith(f"- {today} same-status") and "metadata only" in r
                for r in hb1.records
            )
        )

        # 2. Test positional spelling
        f2 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20261012-demo-01-bk0002-item.backlog.md"
        )
        f2.write_text(
            "- Id: bk0002\n"
            "- Status: open\n"
            "- Set: demo\n"
            "- Priority: high\n"
            "- Work-Kind: feature\n"
            "- Summary: item 2\n\n"
            "## Workflow history\n"
            f"    - {today} same-status (aw backlog): metadata only\n\n"
            "Prose body\n",
            encoding="utf-8",
        )

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc2 = cli.main(
                [
                    "backlog",
                    "set",
                    "open",
                    str(f2),
                    "--message",
                    "metadata only",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc2, 0)
        text2 = f2.read_text(encoding="utf-8")
        hb2 = ac.history_block(text2)
        self.assertGreaterEqual(len(hb2.records), 1)
        self.assertTrue(
            any(
                r.startswith(f"- {today} same-status") and "metadata only" in r
                for r in hb2.records
            )
        )

    def test_g_predicate_and_prior_history_records_agree(self) -> None:
        """(g) Predicate same_status_message_is_duplicate and backlog._prior_history_records agree."""
        today = core.utc_history_date()
        fixtures = [
            # Well-formed matching duplicate
            (
                "## Workflow history\n"
                f"- {today} same-status (aw backlog): metadata only\n\n"
                "Prose body"
            ),
            # Well-formed different message
            (
                "## Workflow history\n"
                f"- {today} same-status (aw backlog): different message\n\n"
                "Prose body"
            ),
            # F-01 indented only
            (
                "## Workflow history\n"
                f"    - {today} same-status (aw backlog): metadata only\n\n"
                "Prose body"
            ),
            # Wrapped fixture
            (
                "## Workflow history\n"
                f"- {today} same-status (aw backlog): metadata only\n"
                "  continuation\n\n"
                "Prose body"
            ),
            # Blank-separated quoted fixture
            (
                "## Workflow history\n"
                f"- 2026-01-01 created (tester): note\n\n"
                f"    - {today} same-status (aw backlog): metadata only\n"
            ),
        ]
        for text in fixtures:
            is_dup = same_status_message_is_duplicate(
                text, status="same-status", date=today, message="metadata only"
            )
            priors = backlog._prior_history_records(text)
            if is_dup:
                self.assertGreater(
                    len(priors),
                    0,
                    f"Predicate reported duplicate, but prior records was empty for:\n{text}",
                )

    def test_h_specs_note_with_indented_history_fixture(self) -> None:
        """(h) Specs path: aw specs note on indented-history fixture appends column-0 note record."""
        today = core.utc_history_date()
        specs_dir = self.root / ".aw" / "records" / "specs" / "draft"
        specs_dir.mkdir(parents=True, exist_ok=True)
        spec_path = (
            specs_dir / f"{today.replace('-', '')}-sp0001-01-sp0001-test-spec.spec.md"
        )
        spec_path.write_text(
            "# Spec: Test Spec\n\n"
            f"- Date: {today}\n"
            "- Status: draft\n"
            "- Id: sp0001\n\n"
            "## Workflow history\n"
            f"    - {today} note (aw specs): note message\n\n"
            "## Requirements\n\n"
            "Some requirement.\n",
            encoding="utf-8",
        )

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(
            io.StringIO()
        ):
            rc = cli.main(
                [
                    "specs",
                    "note",
                    str(spec_path),
                    "--message",
                    "note message",
                ]
            )
        self.assertEqual(rc, 0)
        spec_text = spec_path.read_text(encoding="utf-8")
        hb = ac.history_block(spec_text)
        self.assertGreaterEqual(len(hb.records), 1)
        self.assertTrue(
            any(
                r.startswith(f"- {today} note") and "note message" in r
                for r in hb.records
            )
        )
