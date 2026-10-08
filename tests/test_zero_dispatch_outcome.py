"""Unit tests for the zero-dispatch outcome word in the run summary table (plan 4po0sc).

Validates:
1. Falsifiable core: zero-dispatch runs with operator remedies render NO WORK PERFORMED,
   not COMPLETED (E-04).
2. False-positive refusal: all-already-executed and mixed completed runs still render COMPLETED (E-04).
3. Table and disposition summary agreement across every measured shape (E-04).
4. Regression fence: BLOCKED, FAILED, INTERRUPTED, QUEUED, STRANDED, and COMPLETED
   retain their existing words across their respective status shapes (E-05).
5. Load-bearing branch placement proof: shapes like `not-attempted` and `not-run` return
   True from the predicate but keep their respective words (E-05).
6. Byte identity: progress line, totals row, per-artifact rows, and diagnostics block
   remain byte-identical for the changed shape (E-05).
7. Color styling: NO WORK PERFORMED renders in yellow (SGR 33) under color mode, bare word
   under Palette(False) (E-03).
"""

from __future__ import annotations

import difflib
import re
import unittest
from typing import Any

from agent_workflows import render_stream, run_selection_policy


def _item(**overrides: Any) -> dict[str, Any]:
    """Build one queue entry in the shape persisted by runner state."""
    item: dict[str, Any] = {
        "position": 1,
        "id6": "test01",
        "setid": "b7oicl",
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
        "run_id": "run-20260928T160357Z-4129130",
        "repo": "/repo",
        "queue": queue,
        "options": dict(options),
    }


def _outcome_line(rendered: str) -> str:
    """Extract stripped Outcome line from rendered summary table."""
    plain = render_stream._strip_ansi(rendered)
    for line in plain.splitlines():
        if "Outcome:" in line:
            return line.strip()
    raise AssertionError(f"No Outcome line found in rendered table:\n{rendered}")


def _outcome_word(rendered: str) -> str:
    """Extract outcome word from rendered summary table."""
    line = _outcome_line(rendered)
    match = re.search(r"Outcome:\s+([A-Z ]+?)\s+Duration:", line)
    if not match:
        raise AssertionError(f"Could not parse outcome word from line: {line!r}")
    return match.group(1).strip()


def _extract_sgr_code(rendered: str, word: str) -> str | None:
    """Extract ANSI SGR code preceding word in rendered table."""
    match = re.search(r"\033\[([0-9;]+)m" + re.escape(word), rendered)
    return match.group(1) if match else None


class ZeroDispatchOutcomeFalsifiableCoreTests(unittest.TestCase):
    """E-04: Validate the falsifiable core and false-positive prevention."""

    def test_case_a_single_needs_approval_item_renders_no_work_performed(self) -> None:
        """(a) ONE reviewed/zero-attempt item with needs_input renders NO WORK PERFORMED, not COMPLETED."""
        queue = [_item(status="reviewed", needs_input=True, attempts=[])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        outcome = _outcome_word(rendered)
        self.assertEqual(
            outcome,
            render_stream.NO_WORK_OUTCOME,
            f"Needs-approval run must render {render_stream.NO_WORK_OUTCOME}, got {outcome}",
        )
        self.assertNotIn("COMPLETED", _outcome_line(rendered))

    def test_case_b_eight_needs_approval_items_renders_no_work_performed(self) -> None:
        """(b) Eight-plan em0z50 shape renders NO WORK PERFORMED."""
        queue = [
            _item(
                position=i,
                id6=f"em0z{i:02d}",
                status="reviewed",
                needs_input=True,
                attempts=[],
            )
            for i in range(1, 9)
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        outcome = _outcome_word(rendered)
        self.assertEqual(outcome, render_stream.NO_WORK_OUTCOME)

    def test_case_c_reviewed_item_without_needs_input_renders_no_work_performed(
        self,
    ) -> None:
        """(c) A reviewed item with no needs_input (type_or_status_not_runnable) renders NO WORK PERFORMED."""
        queue = [_item(status="reviewed", attempts=[])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        outcome = _outcome_word(rendered)
        self.assertEqual(outcome, render_stream.NO_WORK_OUTCOME)

    def test_case_d_all_already_executed_renders_completed(self) -> None:
        """(d) A queue whose every member has status: executed with zero attempts STILL renders COMPLETED."""
        queue = [
            _item(
                position=1,
                id6="exec01",
                status="executed",
                initial_status="executed",
                attempts=[],
            ),
            _item(
                position=2,
                id6="exec02",
                status="executed",
                initial_status="executed",
                attempts=[],
            ),
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        outcome = _outcome_word(rendered)
        self.assertEqual(
            outcome,
            "COMPLETED",
            "An all-already-executed queue legitimately finished and must render COMPLETED",
        )
        self.assertNotEqual(outcome, render_stream.NO_WORK_OUTCOME)

    def test_case_e_mixed_executed_and_needs_approval_renders_completed(self) -> None:
        """(e) A queue mixing one executed item (with attempts) and one needs-approval item renders COMPLETED."""
        queue = [
            _item(
                position=1, id6="exec01", status="executed", attempts=[{"number": 1}]
            ),
            _item(
                position=2,
                id6="appr02",
                status="reviewed",
                needs_input=True,
                attempts=[],
            ),
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        outcome = _outcome_word(rendered)
        self.assertEqual(
            outcome,
            "COMPLETED",
            "A run with executed work is not a zero-dispatch run and must render COMPLETED",
        )

    def test_case_f_empty_queue_renders_queued(self) -> None:
        """(f) An EMPTY queue still renders QUEUED."""
        rendered = render_stream.render_run_summary_table(
            _state([]), pal=render_stream.Palette(False)
        )
        outcome = _outcome_word(rendered)
        self.assertEqual(outcome, "QUEUED")

    def test_table_and_summary_agree_on_all_actionable_shapes(self) -> None:
        """The exit table Outcome word and closing disposition summary agree on all actionable shapes."""
        actionable_shapes: list[tuple[str, list[dict[str, Any]]]] = [
            ("case_a", [_item(status="reviewed", needs_input=True, attempts=[])]),
            (
                "case_b",
                [
                    _item(
                        position=i,
                        id6=f"em0z{i:02d}",
                        status="reviewed",
                        needs_input=True,
                        attempts=[],
                    )
                    for i in range(1, 9)
                ],
            ),
            ("case_c", [_item(status="reviewed", attempts=[])]),
        ]

        for label, queue in actionable_shapes:
            rendered = render_stream.render_run_summary_table(
                _state(queue), pal=render_stream.Palette(False)
            )
            outcome = _outcome_word(rendered)
            summary_lines = run_selection_policy.render_disposition_summary(
                queue, refusal_reader=render_stream.refusal_of_item
            )
            summary_text = "\n".join(summary_lines)

            self.assertEqual(outcome, render_stream.NO_WORK_OUTCOME)
            self.assertIn("NO WORK WAS PERFORMED", summary_text)

    def test_table_and_summary_consistency_across_all_six_shapes(self) -> None:
        """Verify the table Outcome and disposition summary across all six core shapes."""
        shapes: list[tuple[str, list[dict[str, Any]], str, bool]] = [
            (
                "case_a",
                [_item(status="reviewed", needs_input=True, attempts=[])],
                render_stream.NO_WORK_OUTCOME,
                True,
            ),
            (
                "case_b",
                [
                    _item(
                        position=i,
                        id6=f"em0z{i:02d}",
                        status="reviewed",
                        needs_input=True,
                        attempts=[],
                    )
                    for i in range(1, 9)
                ],
                render_stream.NO_WORK_OUTCOME,
                True,
            ),
            (
                "case_c",
                [_item(status="reviewed", attempts=[])],
                render_stream.NO_WORK_OUTCOME,
                True,
            ),
            (
                "case_d",
                [_item(status="executed", initial_status="executed", attempts=[])],
                "COMPLETED",
                False,  # Table correctly refuses NO WORK PERFORMED per F-06
            ),
            (
                "case_e",
                [
                    _item(position=1, status="executed", attempts=[{"number": 1}]),
                    _item(position=2, status="reviewed", needs_input=True, attempts=[]),
                ],
                "COMPLETED",
                False,
            ),
            ("case_f", [], "QUEUED", False),
        ]

        for label, queue, expected_table_word, expected_summary_no_work in shapes:
            rendered = render_stream.render_run_summary_table(
                _state(queue), pal=render_stream.Palette(False)
            )
            outcome = _outcome_word(rendered)
            self.assertEqual(outcome, expected_table_word, f"Mismatch on shape {label}")

            summary_lines = run_selection_policy.render_disposition_summary(
                queue, refusal_reader=render_stream.refusal_of_item
            )
            summary_text = "\n".join(summary_lines)

            if expected_summary_no_work:
                self.assertIn("NO WORK WAS PERFORMED", summary_text)
            elif not queue:
                self.assertEqual(summary_lines, [])
            elif label == "case_d":
                self.assertIn("ipd_already_executed", summary_text)
            else:
                self.assertNotIn("NO WORK WAS PERFORMED", summary_text)


class ZeroDispatchOutcomeRegressionFenceTests(unittest.TestCase):
    """E-05: Anti-regression fence and branch placement guard."""

    def test_regression_dependency_blocked_status_renders_blocked(self) -> None:
        queue = [_item(status="dependency-blocked", attempts=[])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(rendered), "BLOCKED")

    def test_regression_blocked_and_fail_gate_status_renders_blocked(self) -> None:
        for st in ("blocked", "fail-gate"):
            # Without refusal record
            q1 = [_item(status=st, attempts=[])]
            r1 = render_stream.render_run_summary_table(
                _state(q1), pal=render_stream.Palette(False)
            )
            self.assertEqual(_outcome_word(r1), "BLOCKED")

            # With refusal record
            item = _item(status=st, attempts=[])
            render_stream.record_refusal(
                item,
                code="awaiting-human-decision",
                reason="gate refusal",
                remedy="review gate",
            )
            r2 = render_stream.render_run_summary_table(
                _state([item]), pal=render_stream.Palette(False)
            )
            self.assertEqual(_outcome_word(r2), "BLOCKED")

    def test_regression_failed_with_attempts_renders_failed(self) -> None:
        queue = [_item(status="failed", attempts=[{"number": 1}])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(rendered), "FAILED")

    def test_regression_merge_refused_with_attempts_renders_failed(self) -> None:
        # Without refusal record
        q1 = [_item(status="merge-refused", attempts=[{"number": 1}])]
        r1 = render_stream.render_run_summary_table(
            _state(q1), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(r1), "FAILED")

        # With refusal record
        item = _item(status="merge-refused", attempts=[{"number": 1}])
        render_stream.record_refusal(
            item,
            code="merge-refused",
            reason="merge conflict",
            remedy="resolve conflict",
        )
        r2 = render_stream.render_run_summary_table(
            _state([item]), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(r2), "FAILED")

    def test_regression_interrupted_with_attempts_renders_interrupted(self) -> None:
        queue = [_item(status="interrupted", attempts=[{"number": 1}])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(rendered), "INTERRUPTED")

    def test_regression_not_attempted_only_renders_queued(self) -> None:
        queue = [_item(status="not-attempted", attempts=[])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(rendered), "QUEUED")

    def test_regression_substantially_complete_with_attempts_renders_completed(
        self,
    ) -> None:
        queue = [_item(status="substantially-complete", attempts=[{"number": 1}])]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(rendered), "COMPLETED")

    def test_regression_substantially_complete_with_refusing_signal_renders_stranded(
        self,
    ) -> None:
        queue = [
            _item(
                status="substantially-complete",
                attempts=[{"number": 1}],
                integration_signal="suite-failed",
            )
        ]
        rendered = render_stream.render_run_summary_table(
            _state(queue), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(rendered), render_stream.STRANDED_OUTCOME)

    def test_placement_proof_predicate_true_word_unchanged(self) -> None:
        """F-14 / PR-602: Predicate returns True for not-attempted and not-run, but their rendered words are unchanged.

        The ONLY reason these shapes do not get relabeled is that neither reaches the COMPLETED branch.
        """
        # not-attempted: predicate is True, rendered word is QUEUED
        q_not_attempted = [_item(status="not-attempted", attempts=[])]
        self.assertTrue(render_stream.queue_performed_no_work(q_not_attempted))
        r_not_attempted = render_stream.render_run_summary_table(
            _state(q_not_attempted), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(r_not_attempted), "QUEUED")

        # not-run: predicate is True, rendered word is BLOCKED
        q_not_run = [_item(status="not-run", attempts=[])]
        self.assertTrue(render_stream.queue_performed_no_work(q_not_run))
        r_not_run = render_stream.render_run_summary_table(
            _state(q_not_run), pal=render_stream.Palette(False)
        )
        self.assertEqual(_outcome_word(r_not_run), "BLOCKED")

    def test_changed_shape_byte_identity(self) -> None:
        """Progress line, totals row, per-artifact rows, and diagnostics are byte-identical for the changed shape."""
        item = _item(
            position=1,
            id6="test01",
            setid="b7oicl",
            action="execute",
            status="reviewed",
            verification_status="verified",
            needs_input=True,
            attempts=[],
        )
        state = _state([item])

        rendered = render_stream.render_run_summary_table(
            state, pal=render_stream.Palette(False)
        )
        lines = rendered.splitlines()

        # Outcome line contains NO WORK PERFORMED
        self.assertIn("Outcome: NO WORK PERFORMED", lines[2])

        # Progress line is byte-identical to progdenom format
        self.assertEqual(
            lines[3].strip(),
            "│ Progress: 0/1  [          ]   0% (1 reviewed)                                                                             │",
        )

        # Per-artifact row is unchanged
        self.assertEqual(
            lines[7].strip(),
            "│  01 │  01 │ test01 │ b7oicl │ execute │ ◑ reviewed │ verified │        - │     - │       - │      - │       - │         - │",
        )

        # Totals row is unchanged
        self.assertEqual(
            lines[9].strip(),
            "│ Total (0/1 items run)                                         │       0s │ $0.00 │       0 │      0 │       0 │         0 │",
        )

        # Diagnostics block is empty
        self.assertNotIn("Diagnostics", rendered)

        # Simulate before-version with COMPLETED (all other lines identical)
        simulated_before = render_stream.render_run_summary_table(
            state, pal=render_stream.Palette(False), exit_reason="COMPLETED"
        )
        diff = list(
            difflib.unified_diff(
                simulated_before.splitlines(),
                rendered.splitlines(),
                lineterm="",
            )
        )
        # Unified diff should only show changes in the Outcome line
        changed_diff_lines = [
            diff_line
            for diff_line in diff
            if (diff_line.startswith("+") or diff_line.startswith("-"))
            and not diff_line.startswith("+++")
            and not diff_line.startswith("---")
        ]
        self.assertEqual(len(changed_diff_lines), 2)
        self.assertTrue(
            any("Outcome: COMPLETED" in diff_line for diff_line in changed_diff_lines)
        )
        self.assertTrue(
            any(
                "Outcome: NO WORK PERFORMED" in diff_line
                for diff_line in changed_diff_lines
            )
        )

    def test_outcome_color_selection(self) -> None:
        """E-03: NO WORK PERFORMED renders in yellow (SGR 33), bare word under Palette(False)."""
        # NO WORK PERFORMED -> 33 (c_yellow)
        q_nowork = [_item(status="reviewed", needs_input=True, attempts=[])]
        r_nowork = render_stream.render_run_summary_table(
            _state(q_nowork), pal=render_stream.Palette(True)
        )
        self.assertEqual(
            _extract_sgr_code(r_nowork, render_stream.NO_WORK_OUTCOME), "33"
        )

        # Under Palette(False), renders bare unstyled word
        r_plain = render_stream.render_run_summary_table(
            _state(q_nowork), pal=render_stream.Palette(False)
        )
        self.assertIn("Outcome: NO WORK PERFORMED", r_plain)
        self.assertNotIn("\033[", r_plain)

        # COMPLETED -> 32 (c_green)
        q_comp = [_item(status="executed", attempts=[{"number": 1}])]
        r_comp = render_stream.render_run_summary_table(
            _state(q_comp), pal=render_stream.Palette(True)
        )
        self.assertEqual(_extract_sgr_code(r_comp, "COMPLETED"), "32")

        # STRANDED -> 31 (c_red)
        q_strand = [
            _item(
                status="substantially-complete",
                attempts=[{"number": 1}],
                integration_signal="failed",
            )
        ]
        r_strand = render_stream.render_run_summary_table(
            _state(q_strand), pal=render_stream.Palette(True)
        )
        self.assertEqual(
            _extract_sgr_code(r_strand, render_stream.STRANDED_OUTCOME), "31"
        )

        # PARTIAL -> 33 (c_yellow)
        q_part = [
            _item(position=1, status="executed", attempts=[{"number": 1}]),
            _item(position=2, status="queued", attempts=[]),
        ]
        r_part = render_stream.render_run_summary_table(
            _state(q_part), pal=render_stream.Palette(True)
        )
        self.assertEqual(_extract_sgr_code(r_part, "PARTIAL"), "33")

        # Nonsense word -> 36 (c_cyan, fallback else-branch)
        r_nonsense = render_stream.render_run_summary_table(
            _state([]), exit_reason="NOTHING TO DO", pal=render_stream.Palette(True)
        )
        self.assertEqual(_extract_sgr_code(r_nonsense, "NOTHING TO DO"), "36")
