"""Behavioral tests for the shared history-record reader across attention, check_engine, and plan_readiness.

Fences the canonical workflow history bounding rule against indented-quotation and prose-separation
hazards (findings F-03, F-04, F-05 of IPD 6iab2o).
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention, check_engine, plan_readiness


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
            plan_text = (
                "# IPD: Test Plan\n\n"
                "- Date: 2026-10-12\n"
                "- Status: reviewed\n"
                "- Readiness: go-pending-approval\n"
                "- Id: tst001\n\n"
                "## Workflow history\n"
                "- 2026-10-12 to-review (aw set): authored\n\n"
                "Here is a column-zero prose note explaining background.\n\n"
                "    - 2026-10-12 reviewed (aw set): /plan-review (x): APPROVE; none\n\n"
                "## Goal\n\n"
                "Describe goal here.\n"
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
            plan_text = (
                "# IPD: Test Plan\n\n"
                "- Date: 2026-10-12\n"
                "- Status: reviewed\n"
                "- Readiness: go-pending-approval\n"
                "- Id: tst002\n\n"
                "## Workflow history\n"
                f"{reject_line}\n\n"
                "Here is a column-zero prose note explaining background.\n\n"
                "    - 2026-10-12 reviewed (aw set): /plan-review (x): APPROVE; none\n\n"
                "## Goal\n\n"
                "Describe goal here.\n"
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
                "- Id: tst003\n"
                "- Status: open\n"
                "- Set: testset\n"
                "- Priority: low\n"
                "- Work-Kind: bug\n"
                "- Summary: Test backlog item with indented history\n\n"
                "## Workflow history\n"
                "    - 2026-10-12 created: indented line\n",
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
        b_text = (
            "- Id: tst004\n"
            "- Status: done\n"
            "- Set: testset\n"
            "- Priority: low\n"
            "- Work-Kind: bug\n"
            "- Summary: Test item\n\n"
            "## Workflow history\n"
            "Some prose\n"
            "- 2026-10-12 done (aw set): finished\n"
            "- 2026-10-11 graduated (aw set): graduated to plan\n"
        )
        s_text = (
            "# Spec: Test Spec\n\n"
            "- Id: tst005\n"
            "- Status: implementing\n"
            "- Set: testset\n\n"
            "## Workflow history\n"
            "Some prose\n"
            "- 2026-10-12 implementing (aw set): start implementation\n"
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
        plan_text = (
            "# IPD: Test Multi-line Plan\n\n"
            "- Date: 2026-10-12\n"
            "- Status: reviewed\n"
            "- Id: tst006\n\n"
            "## Workflow history\n"
            f"{first_record}\n"
            "    indented continuation line\n"
            "- 2026-10-11 draft (aw set): created draft\n"
            "- 2026-10-10 reviewed (aw set): /plan-review (x): APPROVE; initial review\n\n"
            "## Goal\n\n"
            "Goal text\n"
        )

        self.assertEqual(
            plan_readiness.extract_newest_history_entry(plan_text), first_record
        )
        self.assertTrue(plan_readiness.history_has_review_record(plan_text))


if __name__ == "__main__":
    unittest.main()
