"""Behavioral tests for same-status history record deduplication parity across aw backlog set spellings.

Fences the contract established by IPD evbx9s (backlog r74211):
- (a) same-status, identical explicit --message, twice: exactly ONE such record on BOTH spellings,
      and prior records intact.
- (b) same-status, DIFFERENT messages: BOTH records present on BOTH spellings (newest-record-only check).
- (c) same-status, DEFAULTED message (no --message), twice: ONE record on the --status spelling.
      Asserted against itself to accommodate defaulted message asymmetry declined in jbipfa.
- (d) genuine transition then an identical repeat of it: the transition record, then suppression.
- (e) the F-03 indented-prose fixture: the record IS written and the history block is non-empty.
- (f) the sidecar: a suppressed call adds no .aw/records/history.jsonl line; a recorded call adds exactly one.

All cross-spelling comparisons compare history dates literally (unified onto UTC
per spec 4sd62s 4.2b) while normalizing:
1. Actor ('(aw backlog)' vs '(aw set)') as truthful attribution kept distinct by design (jbipfa).

Conforms strictly to GUIDING_PRINCIPLES P16 and AGENTS.md:
- No inspect, ast, regex, or substring search over production source code.
- No assertion that same_status_message_is_duplicate is called, or on caller counts.
- All assertions are on written file contents, exit codes, or sidecar lines.
"""

from __future__ import annotations

import contextlib
import io
import re
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention as att
from agent_workflows import attention_contract as ac
from agent_workflows import cli
from tests.record_builder import RecordBuilder

_ACTOR_PAREN = re.compile(r"\((?:aw backlog|aw set)\)")


def _normalize_history_record(record: str) -> str:
    """Normalize actor in a history record line for cross-spelling parity comparisons.

    Hides one known out-of-scope axis per IPD evbx9s:
    1. Actor: '(aw backlog)' vs '(aw set)' truthfully identifies the writer and is deliberate (jbipfa).
    (Date clock differences are eliminated by unifying writers onto UTC per spec 4sd62s 4.2b; dates are compared literally).
    """
    return _ACTOR_PAREN.sub("(HIST_ACTOR)", record.strip())


def _normalize_for_parity(text: str) -> str:
    """Normalize whole artifact text for cross-spelling byte-level parity comparison."""
    lines = []
    for line in text.splitlines():
        if line.startswith("- ") and ("(aw backlog)" in line or "(aw set)" in line):
            lines.append(_normalize_history_record(line))
        else:
            lines.append(line)
    return "\n".join(lines) + "\n"


def _setup_backlog_repo(root: Path) -> None:
    for sub in ("open", "graduated", "done", "blocked", "parked"):
        (root / ".aw" / "records" / "backlog" / sub).mkdir(parents=True, exist_ok=True)


def _write_conforming_plan(
    root: Path,
    *,
    id6: str = "pl0001",
    backlog_id6: str = "bk0001",
    set_id: str = "demo",
) -> Path:
    plan_dir = root / ".aw" / "records" / "plans" / "pending"
    plan_dir.mkdir(parents=True, exist_ok=True)
    p = plan_dir / f"20260901-{set_id}-01-{id6}-plan.ipd.md"
    plan_body = (
        f"## Goal\n\nGoal {id6}.\n\n"
        "## Detailed Implementation Checklist (TODO)\n\n"
        "### Task group 1: work\n\n"
        "- [ ] E-01 Work item\n"
        "  - Depends on: none\n"
        "  - Expected outcome: done\n"
        "  - Execution state: pending\n\n"
        "## Project conventions discovered (Step 0)\n\n"
        "None.\n\n"
        "## Findings\n\n"
        "None.\n\n"
        "## Proposed changes (ordered, validatable)\n\n"
        "1. E-01 do work.\n\n"
        "## Deferred / out of scope (with reason)\n\n"
        "- None.\n\n"
        "## Scope check\n\n"
        "- None.\n\n"
        "## Required tests / validation\n\n"
        "- None.\n\n"
        "## Spec / documentation sync\n\n"
        "- None.\n\n"
        "## Open questions\n\n"
        "- None.\n\n"
        "## Validation and cross-check (verify before reporting done)\n\n"
        "- [ ] V-01 validates E-01\n"
        "  - Required evidence: check.\n"
        "  - Observed evidence:\n"
        "  - Result: pending\n\n"
        "## Approval and execution gate\n\n"
        "- Size assessment: standard\n"
        "- Cohesion rationale: not required\n"
    )
    p.write_text(
        RecordBuilder().plan(
            id6=id6,
            title=f"Plan {id6}",
            when="2026-09-01",
            status="to-review",
            work_kind="chore",
            priority="medium",
            set=set_id,
            order=1,
            from_backlog=backlog_id6,
            scope_paths="README.md",
            highest_e_allocated="01",
            author="test",
            item_dependencies="none",
            history=["- 2026-09-01 to-review (test): created"],
            body=plan_body,
            raw_fields={
                "Concern": "Test concern.",
                "Scope": "Test scope.",
            },
            text_only=True,
        ),
        encoding="utf-8",
    )
    return p


class BacklogHistoryDedupParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        _setup_backlog_repo(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_a_same_status_identical_message_twice_deduplicates_both_spellings(
        self,
    ) -> None:
        """(a) Same-status re-assertion with identical explicit --message deduplicates across both spellings."""
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
        initial_content_f1 = RecordBuilder().backlog(
            id6="bk0001",
            status="open",
            set="demo",
            priority="high",
            work_kind="feature",
            summary="item 1",
            when="2026-09-01",
            history=[
                "- 2026-09-01 created (tester): initial",
                "- 2026-08-15 created (tester): older initial",
            ],
            body="Prose body",
            text_only=True,
        )
        initial_content_f2 = RecordBuilder().backlog(
            id6="bk0002",
            status="open",
            set="demo",
            priority="high",
            work_kind="feature",
            summary="item 2",
            when="2026-09-01",
            history=[
                "- 2026-09-01 created (tester): initial",
                "- 2026-08-15 created (tester): older initial",
            ],
            body="Prose body",
            text_only=True,
        )
        f1.write_text(initial_content_f1, encoding="utf-8")
        f2.write_text(initial_content_f2, encoding="utf-8")

        # Drive f1 with --status spelling TWICE
        for _ in range(2):
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                rc = cli.main(
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
            self.assertEqual(rc, 0)

        # Drive f2 with positional spelling TWICE
        for _ in range(2):
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0002",
                        "--yes",
                        "--message",
                        "metadata only",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ]
                )
            self.assertEqual(rc, 0)

        # Check f1 (--status) has exactly ONE same-status record plus the 2 prior records
        text1 = f1.read_text(encoding="utf-8")
        records1 = [
            ln
            for ln in att._history_section_lines(text1)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(
            len(records1), 3, f"Expected exactly 3 records in f1, found: {records1}"
        )
        self.assertIn("same-status (aw backlog): metadata only", records1[0])
        self.assertIn("- 2026-09-01 created (tester): initial", records1[1])
        self.assertIn("- 2026-08-15 created (tester): older initial", records1[2])

        # Check f2 (positional) has exactly ONE same-status record plus the 2 prior records
        text2 = f2.read_text(encoding="utf-8")
        records2 = [
            ln
            for ln in att._history_section_lines(text2)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(
            len(records2), 3, f"Expected exactly 3 records in f2, found: {records2}"
        )
        self.assertIn("same-status (aw set): metadata only", records2[0])
        self.assertIn("- 2026-09-01 created (tester): initial", records2[1])
        self.assertIn("- 2026-08-15 created (tester): older initial", records2[2])

        # Whole-file cross-spelling comparison (modulo date shape and actor)
        norm1 = _normalize_for_parity(
            text1.replace("bk0001", "bkXXXX").replace("item 1", "item X")
        )
        norm2 = _normalize_for_parity(
            text2.replace("bk0002", "bkXXXX").replace("item 2", "item X")
        )
        self.assertEqual(norm1, norm2)

    def test_b_same_status_different_messages_records_both_both_spellings(self) -> None:
        """(b) Same-status writes with different messages record both records across both spellings."""
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
            RecordBuilder().backlog(
                id6="bk0001",
                status="open",
                set="demo",
                priority="high",
                work_kind="feature",
                summary="item 1",
                when="2026-09-01",
                history=["- 2026-09-01 created (tester): initial"],
                body="Prose body",
                text_only=True,
            ),
            encoding="utf-8",
        )
        f2.write_text(
            RecordBuilder().backlog(
                id6="bk0002",
                status="open",
                set="demo",
                priority="high",
                work_kind="feature",
                summary="item 2",
                when="2026-09-01",
                history=["- 2026-09-01 created (tester): initial"],
                body="Prose body",
                text_only=True,
            ),
            encoding="utf-8",
        )

        for msg in ("first note", "second note"):
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(f1),
                        "--status",
                        "open",
                        "--message",
                        msg,
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ]
                )
            self.assertEqual(rc, 0)

        for msg in ("first note", "second note"):
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        "open",
                        "bk0002",
                        "--yes",
                        "--message",
                        msg,
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ]
                )
            self.assertEqual(rc, 0)

        text1 = f1.read_text(encoding="utf-8")
        records1 = [
            ln
            for ln in att._history_section_lines(text1)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(records1), 3)
        self.assertIn("second note", records1[0])
        self.assertIn("first note", records1[1])
        self.assertIn("initial", records1[2])

        text2 = f2.read_text(encoding="utf-8")
        records2 = [
            ln
            for ln in att._history_section_lines(text2)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(len(records2), 3)
        self.assertIn("second note", records2[0])
        self.assertIn("first note", records2[1])
        self.assertIn("initial", records2[2])

        norm1 = _normalize_for_parity(
            text1.replace("bk0001", "bkXXXX").replace("item 1", "item X")
        )
        norm2 = _normalize_for_parity(
            text2.replace("bk0002", "bkXXXX").replace("item 2", "item X")
        )
        self.assertEqual(norm1, norm2)

    def test_c_same_status_defaulted_message_twice_deduplicates_status_spelling(
        self,
    ) -> None:
        """(c) Same-status writes with defaulted message deduplicate on --status spelling."""
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-item-1.backlog.md"
        )
        f1.write_text(
            RecordBuilder().backlog(
                id6="bk0001",
                status="open",
                set="demo",
                priority="high",
                work_kind="feature",
                summary="item 1",
                when="2026-09-01",
                history=["- 2026-09-01 created (tester): initial"],
                body="Prose body",
                text_only=True,
            ),
            encoding="utf-8",
        )

        for _ in range(2):
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                rc = cli.main(
                    [
                        "backlog",
                        "set",
                        str(f1),
                        "--status",
                        "open",
                        "--no-commit",
                        "--dir",
                        str(self.root),
                    ]
                )
            self.assertEqual(rc, 0)

        text1 = f1.read_text(encoding="utf-8")
        records1 = [
            ln
            for ln in att._history_section_lines(text1)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(
            len(records1), 2, f"Expected exactly 2 records, found: {records1}"
        )
        self.assertIn("status -> open", records1[0])
        self.assertIn("initial", records1[1])

    def test_d_genuine_transition_then_repeat_deduplicates(self) -> None:
        """(d) Genuine transition followed by an identical repeat records transition and suppresses repeat."""
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-item-1.backlog.md"
        )
        f1.write_text(
            RecordBuilder().backlog(
                id6="bk0001",
                status="open",
                set="demo",
                priority="high",
                work_kind="feature",
                summary="item 1",
                when="2026-09-01",
                history=["- 2026-09-01 created (tester): initial"],
                body="Prose body",
                text_only=True,
            ),
            encoding="utf-8",
        )
        _write_conforming_plan(self.root, backlog_id6="bk0001")

        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc1 = cli.main(
                [
                    "backlog",
                    "set",
                    str(f1),
                    "--status",
                    "graduated",
                    "--message",
                    "carrier handed off",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc1, 0)

        moved = self.root / ".aw" / "records" / "backlog" / "graduated" / f1.name
        self.assertTrue(moved.exists())

        # Repeat call with identical status and message
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc2 = cli.main(
                [
                    "backlog",
                    "set",
                    str(moved),
                    "--status",
                    "graduated",
                    "--message",
                    "carrier handed off",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc2, 0)

        text = moved.read_text(encoding="utf-8")
        records = [
            ln
            for ln in att._history_section_lines(text)
            if ac.HISTORY_RECORD_RE.match(ln)
        ]
        self.assertEqual(
            len(records),
            2,
            f"Expected 2 records (transition + initial), found: {records}",
        )
        self.assertIn("graduated (aw backlog): carrier handed off", records[0])
        self.assertIn("initial", records[1])

    def test_e_f03_indented_prose_fixture_fails_safe_writes_record(self) -> None:
        """(e) F-03 indented prose fixture fails safe and writes the record so the history block is not empty."""
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-item-1.backlog.md"
        )
        # Indented history line: seen by attention, but _prior_history_records returns []
        f1.write_text(
            RecordBuilder().backlog(
                id6="bk0001",
                status="open",
                set="demo",
                priority="high",
                work_kind="feature",
                summary="item 1",
                when="2026-09-01",
                history=[],
                body="    - 2026-10-02 same-status (aw backlog): metadata only\n\nProse body",
                text_only=True,
            ),
            encoding="utf-8",
        )

        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc = cli.main(
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
        self.assertEqual(rc, 0)

        text = f1.read_text(encoding="utf-8")
        # Ensure the record was written at column 0 and history section is not empty
        records = [
            ln
            for ln in text.splitlines()
            if ln.startswith("- ") and "same-status" in ln
        ]
        self.assertGreaterEqual(
            len(records),
            1,
            f"Expected column-0 record to be written, file content:\n{text}",
        )

    def test_f_sidecar_behavior_suppressed_call_adds_no_line(self) -> None:
        """(f) Sidecar activity log appends on recorded call and does NOT append on suppressed call."""
        f1 = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "open"
            / "20260901-demo-01-bk0001-item-1.backlog.md"
        )
        f1.write_text(
            RecordBuilder().backlog(
                id6="bk0001",
                status="open",
                set="demo",
                priority="high",
                work_kind="feature",
                summary="item 1",
                when="2026-09-01",
                history=["- 2026-09-01 created (tester): initial"],
                body="Prose body",
                text_only=True,
            ),
            encoding="utf-8",
        )
        sidecar = self.root / ".aw" / "records" / "history.jsonl"

        # Recorded call 1
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc1 = cli.main(
                [
                    "backlog",
                    "set",
                    str(f1),
                    "--status",
                    "open",
                    "--message",
                    "first change",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc1, 0)
        self.assertTrue(sidecar.exists())
        lines1 = sidecar.read_text(encoding="utf-8").splitlines()
        count1 = len(lines1)
        self.assertGreaterEqual(count1, 1)

        # Suppressed call 2 (identical repeat)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc2 = cli.main(
                [
                    "backlog",
                    "set",
                    str(f1),
                    "--status",
                    "open",
                    "--message",
                    "first change",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc2, 0)
        lines2 = sidecar.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            len(lines2), count1, "Sidecar must not grow on suppressed call"
        )

        # Recorded call 3 (different message)
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            rc3 = cli.main(
                [
                    "backlog",
                    "set",
                    str(f1),
                    "--status",
                    "open",
                    "--message",
                    "second change",
                    "--no-commit",
                    "--dir",
                    str(self.root),
                ]
            )
        self.assertEqual(rc3, 0)
        lines3 = sidecar.read_text(encoding="utf-8").splitlines()
        self.assertEqual(
            len(lines3),
            count1 + 1,
            "Sidecar must grow by 1 on recorded call with new message",
        )
