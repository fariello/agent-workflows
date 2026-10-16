#!/usr/bin/env python3
"""Behavioral tests for loose leading whitespace tolerance in plan front matter.

Restores behavioral coverage (yuhl6o S-06) originally in
`tests/test_runner_refork_guard.py::FrontMatterReaderBehaviorTests` (deleted in `19313eed`),
validating that `parse_plan_file` across both host drivers and the public `selectors`
readers tolerate loose leading whitespace (`- `, `-  `, `-\t`), while strict internal
readers reject loose whitespace, and the single-token status contract is preserved.
"""

import tempfile
import unittest
from pathlib import Path

from agent_workflows import agy_runipd, oc_runipd, runner_shared, selectors


class FrontMatterLooseWhitespaceTests(unittest.TestCase):
    """Behavioral tests for front-matter reader whitespace tolerance and contracts."""

    ONE_SPACE = "- Id: abc123\n- Status: approved\n"
    TWO_SPACES = "-  Id: abc123\n-  Status: approved\n"
    TAB = "-\tId: abc123\n-\tStatus: approved\n"

    def test_parse_plan_file_tolerates_loose_leading_whitespace(self):
        """E-01: parse_plan_file on both hosts accepts '- ', '-  ', and '-\\t'."""
        prefixes = (
            ("one space", "- "),
            ("two spaces", "-  "),
            ("tab", "-\t"),
        )
        hosts = (
            ("oc_runipd", oc_runipd),
            ("agy_runipd", agy_runipd),
        )
        for host_name, host in hosts:
            for spelling_name, prefix in prefixes:
                with self.subTest(host=host_name, spelling=spelling_name):
                    with tempfile.TemporaryDirectory() as tmp:
                        tmp_path = Path(tmp)
                        plan_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
                        plan_dir.mkdir(parents=True, exist_ok=True)
                        plan_path = plan_dir / "plan.md"
                        plan_content = (
                            f"{prefix}Id: abc123\n"
                            f"{prefix}Status: approved\n"
                            f"{prefix}Kind: child\n"
                            "\n"
                            "## Goal\n"
                        )
                        plan_path.write_text(plan_content, encoding="utf-8")
                        record = host.parse_plan_file(plan_path, tmp_path)
                        self.assertIsNotNone(record)
                        self.assertEqual(
                            (record.id6, record.status, record.kind),
                            ("abc123", "approved", "child"),
                        )

    def test_public_readers_tolerate_loose_leading_whitespace(self):
        """E-02 (public permissive): read_front_matter_id and read_front_matter_status accept all 3 spellings."""
        for spelling_name, text in (
            ("one space", self.ONE_SPACE),
            ("two spaces", self.TWO_SPACES),
            ("tab", self.TAB),
        ):
            with self.subTest(spelling=spelling_name):
                self.assertEqual(selectors.read_front_matter_id(text), "abc123")
                self.assertEqual(selectors.read_front_matter_status(text), "approved")

    def test_internal_readers_stay_strict(self):
        """E-02 (internal strict): _read_id and _read_status accept only one-space spelling."""
        # One space returns values
        self.assertEqual(selectors._read_id(self.ONE_SPACE), "abc123")
        self.assertEqual(selectors._read_status(self.ONE_SPACE), "approved")

        # Two spaces and tab return None
        self.assertIsNone(selectors._read_id(self.TWO_SPACES))
        self.assertIsNone(selectors._read_status(self.TWO_SPACES))
        self.assertIsNone(selectors._read_id(self.TAB))
        self.assertIsNone(selectors._read_status(self.TAB))

    def test_single_token_status_contract_survives(self):
        """E-03: multi-word status returns None from status readers and falls back to directory bucket."""
        multi = "- Status: EXECUTED (approved by maintainer)\n"
        self.assertIsNone(selectors.read_front_matter_status(multi))
        self.assertIsNone(selectors._read_status(multi))

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_dir = tmp_path / ".aw" / "records" / "plans" / "pending"
            plan_dir.mkdir(parents=True, exist_ok=True)
            plan_path = plan_dir / "plan.md"
            plan_path.write_text(multi, encoding="utf-8")
            record = runner_shared.parse_plan_file(plan_path, tmp_path)
            self.assertIsNotNone(record)
            self.assertEqual(record.status, "pending")
            self.assertNotEqual(record.status, "EXECUTED")


if __name__ == "__main__":
    unittest.main()
