"""Behavioral guard for carrier detail Section 8.8 descriptive bound (plan lxcexr)."""

import re
import tempfile
import unittest
from pathlib import Path

from agent_workflows import attention_contract
from agent_workflows import check_engine as ce


class CarrierDetailDescriptiveBoundTests(unittest.TestCase):
    """Behavioral tests asserting evaluate_durable_carrier composes conforming detail."""

    def _setup_scratch_repo(self, td: str) -> Path:
        """Create a fixture repository in a temp directory outside the checkout."""
        root = Path(td)
        bk_dir = root / ".aw" / "records" / "backlog" / "done"
        bk_dir.mkdir(parents=True, exist_ok=True)
        (bk_dir / "20260101-backlog-01-bk0001-sample.backlog.md").write_text(
            "# Backlog\n\n- Id: bk0001\n- Status: done\n- Priority: medium\n- Work-Kind: chore\n",
            encoding="utf-8",
        )

        pl_exec_dir = root / ".aw" / "records" / "plans" / "executed"
        pl_exec_dir.mkdir(parents=True, exist_ok=True)
        (pl_exec_dir / "20260101-plans-01-pl0001-sample.ipd.md").write_text(
            "# IPD\n\n- Id: pl0001\n- Status: executed\n",
            encoding="utf-8",
        )

        pl_pend_dir = root / ".aw" / "records" / "plans" / "pending"
        pl_pend_dir.mkdir(parents=True, exist_ok=True)
        return root

    def test_case_a_uncarried_six_rows_descriptive_bound(self):
        """Case (a): 6 uncarried rows satisfy is_safe_descriptive and MAX_DESCRIPTIVE_LEN."""
        with tempfile.TemporaryDirectory() as td:
            root = self._setup_scratch_repo(td)
            carrier_index = ce._carrier_index(root)
            plan_text = (
                "# IPD: Test\n\n"
                "- Date: 2026-10-01\n"
                "- Id: pl9001\n"
                "- Status: pending\n\n"
                "## Deferred / out of scope (with reason)\n"
                "- Row 1\n"
                "- Row 2\n"
                "- Row 3\n"
                "- Row 4\n"
                "- Row 5\n"
                "- Row 6\n"
            )
            plan_path = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261001-test-01-pl9001-test.ipd.md"
            )
            drifts = ce.evaluate_durable_carrier(
                root,
                plan_path=plan_path,
                plan_text=plan_text,
                carrier_index=carrier_index,
            )
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            self.assertEqual(d.rule, "check.ipd-uncarried-obligation")
            self.assertTrue(
                attention_contract.is_safe_descriptive(d.detail),
                f"Detail failed is_safe_descriptive (length={len(d.detail)}, has_newline={chr(10) in d.detail}): {d.detail!r}",
            )
            self.assertLessEqual(
                len(d.detail),
                attention_contract.MAX_DESCRIPTIVE_LEN,
                f"Detail length {len(d.detail)} > {attention_contract.MAX_DESCRIPTIVE_LEN}: {d.detail!r}",
            )

    def test_case_b_finished_carrier_two_rows_newline_and_length(self):
        """Case (b): 2 rows with same finished carrier contain no newlines and satisfy bound."""
        with tempfile.TemporaryDirectory() as td:
            root = self._setup_scratch_repo(td)
            carrier_index = ce._carrier_index(root)
            plan_text = (
                "# IPD: Test\n\n"
                "- Date: 2026-10-01\n"
                "- Id: pl9002\n"
                "- Status: pending\n\n"
                "## Deferred / out of scope (with reason)\n"
                "- Row 1\n"
                "  - Carrier: pl0001\n"
                "- Row 2\n"
                "  - Carrier: pl0001\n"
            )
            plan_path = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261001-test-01-pl9002-test.ipd.md"
            )
            drifts = ce.evaluate_durable_carrier(
                root,
                plan_path=plan_path,
                plan_text=plan_text,
                carrier_index=carrier_index,
            )
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            self.assertEqual(d.rule, "check.ipd-carrier-finished-unverified")
            self.assertNotIn(
                "\n",
                d.detail,
                f"Detail contains embedded newline: {d.detail!r}",
            )
            self.assertTrue(
                attention_contract.is_safe_descriptive(d.detail),
                f"Detail failed is_safe_descriptive (length={len(d.detail)}, has_newline={chr(10) in d.detail}): {d.detail!r}",
            )
            self.assertLessEqual(
                len(d.detail),
                attention_contract.MAX_DESCRIPTIVE_LEN,
                f"Detail length {len(d.detail)} > {attention_contract.MAX_DESCRIPTIVE_LEN}: {d.detail!r}",
            )

    def test_case_c_locator_completeness_shown_plus_hidden_equals_total(self):
        """Case (c): No locator lost; shown locators plus (and N more) equals total obligations."""
        with tempfile.TemporaryDirectory() as td:
            root = self._setup_scratch_repo(td)
            carrier_index = ce._carrier_index(root)
            plan_text = (
                "# IPD: Test\n\n"
                "- Date: 2026-10-01\n"
                "- Id: pl9003\n"
                "- Status: pending\n\n"
                "## Deferred / out of scope (with reason)\n"
                "- Row 1\n"
                "- Row 2\n"
                "- Row 3\n"
                "- Row 4\n"
                "- Row 5\n"
                "- Row 6\n"
                "- Row 7\n"
            )
            plan_path = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261001-test-01-pl9003-test.ipd.md"
            )
            drifts = ce.evaluate_durable_carrier(
                root,
                plan_path=plan_path,
                plan_text=plan_text,
                carrier_index=carrier_index,
            )
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            m_header = re.match(r"^(\d+)\s+obligation\(s\)", d.detail)
            self.assertIsNotNone(m_header, f"Header missing in {d.detail!r}")
            total_reported = int(m_header.group(1))
            self.assertEqual(total_reported, 7)

            m_tail = re.search(r"\(and\s+(\d+)\s+more\)$", d.detail)
            hidden_count = int(m_tail.group(1)) if m_tail else 0

            shown_locators = re.findall(r"\bdeferred row \d+\b", d.detail)
            shown_count = len(shown_locators)
            self.assertEqual(
                shown_count + hidden_count,
                7,
                f"Locator arithmetic mismatch: shown {shown_count} + hidden {hidden_count} != 7 in {d.detail!r}",
            )

    def test_case_d_pasteable_remedy_survives(self):
        """Case (d): Finished-carrier detail retains literal - Carrier-Evidence: <path> substring and Carrier-Declined."""
        with tempfile.TemporaryDirectory() as td:
            root = self._setup_scratch_repo(td)
            carrier_index = ce._carrier_index(root)
            plan_text = (
                "# IPD: Test\n\n"
                "- Date: 2026-10-01\n"
                "- Id: pl9004\n"
                "- Status: pending\n\n"
                "## Deferred / out of scope (with reason)\n"
                "- Row 1\n"
                "  - Carrier: pl0001\n"
            )
            plan_path = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261001-test-01-pl9004-test.ipd.md"
            )
            drifts = ce.evaluate_durable_carrier(
                root,
                plan_path=plan_path,
                plan_text=plan_text,
                carrier_index=carrier_index,
            )
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            expected_line = "- Carrier-Evidence: .aw/records/plans/executed/20260101-plans-01-pl0001-sample.ipd.md"
            self.assertIn(
                expected_line,
                d.detail,
                f"Pasteable remedy {expected_line!r} not found in detail: {d.detail!r}",
            )
            self.assertIn(
                "Carrier-Declined",
                d.detail,
                f"'Carrier-Declined' warning not found in detail: {d.detail!r}",
            )
            self.assertNotIn(
                "\n",
                d.detail,
                f"Detail contains embedded newline: {d.detail!r}",
            )
            self.assertTrue(
                attention_contract.is_safe_descriptive(d.detail),
                f"Detail failed is_safe_descriptive (length={len(d.detail)}, has_newline={chr(10) in d.detail}): {d.detail!r}",
            )

    def test_case_e_uncarried_nine_rows_single_body_partial_group_bound(self):
        """Case (e): 9 uncarried rows sharing one body fit under bound via partial group and preserve arithmetic."""
        with tempfile.TemporaryDirectory() as td:
            root = self._setup_scratch_repo(td)
            carrier_index = ce._carrier_index(root)
            plan_text = (
                "# IPD: Test\n\n"
                "- Date: 2026-10-01\n"
                "- Id: pl9005\n"
                "- Status: pending\n\n"
                "## Deferred / out of scope (with reason)\n"
                + "".join(f"- Row {i}\n" for i in range(1, 10))
            )
            plan_path = (
                root
                / ".aw"
                / "records"
                / "plans"
                / "pending"
                / "20261001-test-01-pl9005-test.ipd.md"
            )
            drifts = ce.evaluate_durable_carrier(
                root,
                plan_path=plan_path,
                plan_text=plan_text,
                carrier_index=carrier_index,
            )
            self.assertEqual(len(drifts), 1)
            d = drifts[0]
            self.assertEqual(d.rule, "check.ipd-uncarried-obligation")
            self.assertTrue(
                attention_contract.is_safe_descriptive(d.detail),
                f"Detail failed is_safe_descriptive (length={len(d.detail)}, has_newline={chr(10) in d.detail}): {d.detail!r}",
            )
            self.assertLessEqual(
                len(d.detail),
                attention_contract.MAX_DESCRIPTIVE_LEN,
                f"Detail length {len(d.detail)} > {attention_contract.MAX_DESCRIPTIVE_LEN}: {d.detail!r}",
            )
            m_tail = re.search(r"\(and\s+(\d+)\s+more\)$", d.detail)
            hidden_count = int(m_tail.group(1)) if m_tail else 0
            shown_locators = re.findall(r"\bdeferred row \d+\b", d.detail)
            self.assertEqual(
                len(shown_locators) + hidden_count,
                9,
                f"Arithmetic mismatch: shown {len(shown_locators)} + hidden {hidden_count} != 9 in {d.detail!r}",
            )


if __name__ == "__main__":
    unittest.main()
