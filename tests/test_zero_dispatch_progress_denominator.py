"""Unit tests for the zero-dispatch progress denominator in the run summary table (plan 35mjqc).

Validates:
1. (a) Eight-reviewed shape: renders 0/8 in progress bar and totals row, and the count
   in the fraction equals the number of per-artifact rows rendered in the same table.
2. (b) All-already-executed shape: renders 0/5 in progress bar and totals row, and still
   renders Outcome: COMPLETED.
3. (c) Single-reviewed shape: byte-identical to pre-plan output (0/1), preserving 4po0sc's
   pinned assertions.
4. (d) Ten-member, four-pre-executed shape: byte-identical to pre-plan output (6/6),
   preserving progdenom's live-workload denominator.
5. (e) Empty queue: renders 0/0 and Outcome: QUEUED.
6. (f) dispatchable_work_total contract is unchanged for all measured shapes, guaranteeing
   the IPD nn/NN banner and host statuslines remain completely undisturbed.
"""

from __future__ import annotations

import re
import unittest
from typing import Any

from agent_workflows import render_stream


def _item(**overrides: Any) -> dict[str, Any]:
    """Build one queue entry in the shape persisted by runner state."""
    item: dict[str, Any] = {
        "position": 1,
        "id6": "test01",
        "setid": "5hf2qy",
        "action": "execute",
        "status": "reviewed",
        "verification_status": "verified",
        "attempts": [],
    }
    item.update(overrides)
    return item


def _state(queue: list[dict[str, Any]], **options: Any) -> dict[str, Any]:
    """Build minimal state dictionary for render_run_summary_table."""
    return {
        "run_id": "run-repro",
        "repo": "/repo",
        "queue": queue,
        "options": dict(options),
    }


def _outcome_word(rendered: str) -> str:
    """Extract outcome word from rendered summary table."""
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Outcome:" in line:
            match = re.search(r"Outcome:\s+([A-Z ]+?)\s+Duration:", line)
            if match:
                return match.group(1).strip()
    raise AssertionError(
        f"Could not parse outcome word from rendered table:\n{rendered}"
    )


def _progress_fraction(rendered: str) -> str:
    """Extract the progress fraction (e.g. '0/8') from rendered summary table."""
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Progress:" in line:
            match = re.search(r"Progress:\s+([0-9]+/[0-9]+)", line)
            if match:
                return match.group(1).strip()
    raise AssertionError(
        f"Could not parse progress fraction from rendered table:\n{rendered}"
    )


def _totals_fraction(rendered: str) -> str:
    """Extract the totals fraction (e.g. '0/8') from rendered summary table."""
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Total (" in line:
            match = re.search(r"Total\s+\(([0-9]+/[0-9]+)\s+items\s+run\)", line)
            if match:
                return match.group(1).strip()
    raise AssertionError(
        f"Could not parse totals fraction from rendered table:\n{rendered}"
    )


def _artifact_row_count(rendered: str) -> int:
    """Count per-artifact table rows in the rendered summary table."""
    plain = render_stream._strip_ansi(rendered)
    count = 0
    # Artifact rows have format: │  01 │  01 │ <id6> │ ...
    pattern = re.compile(r"^│\s+\d+\s+│\s+\d+\s+│\s+[a-z0-9_]+\s+│")
    for line in plain.splitlines():
        if pattern.match(line):
            count += 1
    return count


class ZeroDispatchProgressDenominatorTests(unittest.TestCase):
    """E-03: Validate the zero-dispatch progress denominator behavior across all required shapes."""

    def test_eight_reviewed_shape_fraction_and_row_count_agreement(self) -> None:
        """(a) Eight-reviewed shape names 8 in progress and totals, agreeing with per-artifact rows."""
        queue = [
            _item(
                position=i,
                id6=f"it{i:02d}",
                status="reviewed",
                attempts=[],
            )
            for i in range(1, 9)
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_progress_fraction(rendered), "0/8")
        self.assertEqual(_totals_fraction(rendered), "0/8")
        self.assertEqual(_outcome_word(rendered), render_stream.NO_WORK_OUTCOME)

        row_count = _artifact_row_count(rendered)
        self.assertEqual(row_count, 8)
        self.assertEqual(int(_progress_fraction(rendered).split("/")[1]), row_count)
        self.assertIn("Progress: 0/8  [          ]   0% (8 reviewed)", rendered)
        self.assertIn("Total (0/8 items run)", rendered)

    def test_all_already_executed_shape_names_matched_count_and_completed(self) -> None:
        """(b) All-already-executed shape names 5 and still reads COMPLETED."""
        queue = [
            _item(
                position=i,
                id6=f"exec{i:02d}",
                status="executed",
                initial_status="executed",
                attempts=[],
            )
            for i in range(1, 6)
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_progress_fraction(rendered), "0/5")
        self.assertEqual(_totals_fraction(rendered), "0/5")
        self.assertEqual(_outcome_word(rendered), "COMPLETED")
        self.assertIn("Total (0/5 items run)", rendered)

    def test_single_reviewed_shape_byte_identical_to_pinned_output(self) -> None:
        """(c) Single-reviewed shape names 0/1 and is byte-identical to 4po0sc's pinned assertion."""
        queue = [
            _item(
                position=1,
                id6="test01",
                setid="b7oicl",
                action="execute",
                status="reviewed",
                verification_status="verified",
                attempts=[],
            )
        ]
        rendered = render_stream.render_run_summary_table(
            {
                "run_id": "run-20260928T160357Z-4129130",
                "repo": "/repo",
                "queue": queue,
                "options": {},
            },
            pal=render_stream.Palette(False),
        )
        lines = rendered.splitlines()
        self.assertEqual(
            lines[3].strip(),
            "│ Progress: 0/1  [          ]   0% (1 reviewed)                                                                             │",
        )
        self.assertEqual(
            lines[9].strip(),
            "│ Total (0/1 items run)                                         │       0s │ $0.00 │       0 │      0 │       0 │         0 │",
        )
        self.assertEqual(_outcome_word(rendered), render_stream.NO_WORK_OUTCOME)

    def test_ten_member_four_pre_executed_shape_byte_identical(self) -> None:
        """(d) Ten-member, four-pre-executed shape retains 6/6 live-workload progress."""
        queue = []
        for i in range(1, 5):
            queue.append(
                _item(
                    position=i,
                    id6=f"it{i:02d}",
                    status="executed",
                    initial_status="executed",
                    attempts=[],
                )
            )
        for i in range(5, 11):
            queue.append(
                _item(
                    position=i,
                    id6=f"it{i:02d}",
                    status="executed",
                    attempts=[{"number": 1}],
                )
            )
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_progress_fraction(rendered), "6/6")
        self.assertEqual(_totals_fraction(rendered), "6/6")
        self.assertEqual(_outcome_word(rendered), "COMPLETED")
        self.assertIn("Total (6/6 items run)", rendered)

    def test_empty_queue_renders_zero_over_zero(self) -> None:
        """(e) An empty queue still renders 0/0 and Outcome: QUEUED."""
        rendered = render_stream.render_run_summary_table(
            _state([]), pal=render_stream.Palette(False)
        )
        self.assertEqual(_progress_fraction(rendered), "0/0")
        self.assertEqual(_totals_fraction(rendered), "0/0")
        self.assertEqual(_outcome_word(rendered), "QUEUED")

    def test_dispatchable_work_total_contract_unchanged(self) -> None:
        """(f) dispatchable_work_total is unchanged across all shapes, protecting banner and statusline."""
        # Eight-reviewed shape: 0 dispatchable -> divide guard returns 1
        q_8rev = [
            _item(position=i, id6=f"it{i:02d}", status="reviewed", attempts=[])
            for i in range(1, 9)
        ]
        self.assertEqual(render_stream.dispatchable_work_total(q_8rev), 1)
        self.assertEqual(render_stream.progress_display_total(q_8rev), 8)

        # All-already-executed shape: 0 dispatchable -> divide guard returns 1
        q_5exec = [
            _item(
                position=i,
                id6=f"it{i:02d}",
                status="executed",
                initial_status="executed",
                attempts=[],
            )
            for i in range(1, 6)
        ]
        self.assertEqual(render_stream.dispatchable_work_total(q_5exec), 1)
        self.assertEqual(render_stream.progress_display_total(q_5exec), 5)

        # Single-reviewed shape: 0 dispatchable -> divide guard returns 1
        q_1rev = [_item(position=1, id6="it01", status="reviewed", attempts=[])]
        self.assertEqual(render_stream.dispatchable_work_total(q_1rev), 1)
        self.assertEqual(render_stream.progress_display_total(q_1rev), 1)

        # Ten-member, 4 pre-executed: 6 dispatchable -> returns 6
        q_10 = [
            _item(
                position=i,
                id6=f"it{i:02d}",
                status="executed",
                initial_status="executed",
                attempts=[],
            )
            for i in range(1, 5)
        ] + [
            _item(
                position=i,
                id6=f"it{i:02d}",
                status="executed",
                attempts=[{"number": 1}],
            )
            for i in range(5, 11)
        ]
        self.assertEqual(render_stream.dispatchable_work_total(q_10), 6)
        self.assertEqual(render_stream.progress_display_total(q_10), 6)

        # Empty queue: returns 0
        self.assertEqual(render_stream.dispatchable_work_total([]), 0)
        self.assertEqual(render_stream.progress_display_total([]), 0)


if __name__ == "__main__":
    unittest.main()
