"""Behavioral tests for the shared history-record reader across attention, check_engine, and plan_readiness.

Fences the canonical workflow history bounding rule against indented-quotation and prose-separation
hazards (findings F-03, F-04, F-05 of IPD 6iab2o).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention, check_engine, plan_readiness
from tests.record_builder import RecordBuilder


class TestHistoryConsumersSharedReader(unittest.TestCase):
    def test_gate_case_indented_quoted_review_does_not_attest_readiness(self):
        """Case (a) / F-04: indented quoted review record cannot attest readiness or verdict.

        A plan whose only real record is to-review, carrying Readiness: go-pending-approval,
        followed by blank line, column-zero prose, blank line, and indented quoted review record,
        must have history_has_review_record False, newest_verdict (None, ''), and
        is_plan_review_approved False.
        """
        with tempfile.TemporaryDirectory() as td:
            plan_path = Path(td) / "20261012-testset-01-tst001-test-plan.ipd.md"
            plan_text = RecordBuilder().plan(
                title="Test Plan",
                when="2026-10-12",
                status="reviewed",
                id6="tst001",
                raw_fields={"Readiness": "go-pending-approval"},
                history=[
                    "- 2026-10-12 to-review (aw set): authored\n\n"
                    "Here is a column-zero prose note explaining background.\n\n"
                    "    - 2026-10-12 reviewed (aw set): /plan-review (x): APPROVE; none"
                ],
                body="## Goal\n\nDescribe goal here.\n",
                text_only=True,
            )
            plan_path.write_text(plan_text, encoding="utf-8")

            self.assertFalse(plan_readiness.history_has_review_record(plan_text))
            self.assertEqual(plan_readiness.newest_verdict(plan_text), (None, ""))
            self.assertFalse(plan_readiness.is_plan_review_approved(plan_path))

    def test_gate_case_indented_quoted_review_under_real_reject(self):
        """Case (a2): indented quoted review record separated by prose under real REJECT.

        The quoted APPROVE is excluded by the column-zero prose boundary; newest_verdict
        returns the NEGATIVE polarity read from the real record.
        """
        with tempfile.TemporaryDirectory() as td:
            plan_path = Path(td) / "20261012-testset-01-tst002-test-plan-reject.ipd.md"
            reject_line = "- 2026-10-12 reviewed (aw set): /plan-review (x): REJECT - NEEDS REPLAN; major findings"
            plan_text = RecordBuilder().plan(
                title="Test Plan",
                when="2026-10-12",
                status="reviewed",
                id6="tst002",
                raw_fields={"Readiness": "go-pending-approval"},
                history=[
                    f"{reject_line}\n\n"
                    "Here is a column-zero prose note explaining background.\n\n"
                    "    - 2026-10-12 reviewed (aw set): /plan-review (x): APPROVE; none"
                ],
                body="## Goal\n\nDescribe goal here.\n",
                text_only=True,
            )
            plan_path.write_text(plan_text, encoding="utf-8")

            polarity, entry = plan_readiness.newest_verdict(plan_text)
            self.assertEqual(polarity, plan_readiness.NEGATIVE)
            self.assertEqual(entry, reject_line)

    def test_backlog_indented_history_ignored_by_attention_scan(self):
        """Case (b): backlog item whose only history-shaped line is indented.

        attention.scan on a repo holding that item reports last_history_at as None.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            bdir = root / ".aw" / "records" / "backlog" / "open"
            bdir.mkdir(parents=True)
            item_path = bdir / "20261012-testset-01-tst003-indented.backlog.md"
            item_path.write_text(
                RecordBuilder().backlog(
                    id6="tst003",
                    status="open",
                    set="testset",
                    priority="low",
                    work_kind="bug",
                    summary="Test backlog item with indented history",
                    history=[],
                    body="    - 2026-10-12 created: indented line",
                    text_only=True,
                ),
                encoding="utf-8",
            )
            items, _ = attention.scan(root)
            matched = [it for it in items if it.id == "tst003"]
            self.assertEqual(len(matched), 1)
            self.assertIsNone(matched[0].last_history_at)

    def test_prose_bounded_history_in_check_engine_date_readers(self):
        """Case (b2) / F-05: column-zero records following column-zero prose lines are excluded.

        A backlog item whose block is 'Some prose' followed by done/graduated lines yields
        None for _item_close_date and _item_graduated_date. A spec of the same shape with an
        implementing line yields None for _spec_implementing_date.
        """
        b_text = RecordBuilder().backlog(
            id6="tst004",
            status="done",
            set="testset",
            priority="low",
            work_kind="bug",
            summary="Test item",
            history=[],
            body=(
                "Some prose\n"
                "- 2026-10-12 done (aw set): finished\n"
                "- 2026-10-11 graduated (aw set): graduated to plan"
            ),
            text_only=True,
        )
        s_text = (
            RecordBuilder().spec(
                title="Test Spec",
                id6="tst005",
                status="implementing",
                set="testset",
                body="",
                history=[],
                text_only=True,
            )
            + "Some prose\n"
            + "- 2026-10-12 implementing (aw set): start implementation\n"
        )

        self.assertIsNone(check_engine._item_close_date(b_text))
        self.assertIsNone(check_engine._item_graduated_date(b_text))
        self.assertIsNone(check_engine._spec_implementing_date(s_text))

    def test_multiline_wrapped_plan_record_preserves_subsequent_records(self):
        """Case (c): wrapped multi-line plan record keeps every following record visible.

        A column-zero record directly followed by an indented continuation, then two more
        column-zero records: extract_newest_history_entry returns the first record, and
        history_has_review_record sees the review record placed third.
        """
        first_record = "- 2026-10-12 to-review (aw set): first line of record"
        plan_text = RecordBuilder().plan(
            title="Test Multi-line Plan",
            when="2026-10-12",
            status="reviewed",
            id6="tst006",
            history=[
                f"{first_record}\n    indented continuation line",
                "- 2026-10-11 draft (aw set): created draft",
                "- 2026-10-10 reviewed (aw set): /plan-review (x): APPROVE; initial review",
            ],
            body="## Goal\n\nGoal text\n",
            text_only=True,
        )

        self.assertEqual(
            plan_readiness.extract_newest_history_entry(plan_text), first_record
        )
        self.assertTrue(plan_readiness.history_has_review_record(plan_text))


if __name__ == "__main__":
    unittest.main()
