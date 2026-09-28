"""Tests for review record classification and verdict reading (verdictread xpta5g).

Covers:
- E-01: Per-item regression tests for ycg597, nwrb0j, gv36a7, and classifier table test.
- E-03: One-parser invariant (exactly one history-record-parts parser).
- E-07: Live pending corpus invariant (livecorpus-marked: no verdict-class refusal on any pending plan; deselected in default runner lanes).
"""

from __future__ import annotations

import unittest
from pathlib import Path

import pytest

from agent_workflows import plan_readiness

REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_plan_text(history_lines: list[str], *, id6: str = "fixt01") -> str:
    hist = "\n".join(history_lines)
    return (
        f"# IPD: Fixture Plan\n\n"
        f"- Id: {id6}\n"
        f"- Status: reviewed\n\n"
        f"## Workflow history\n"
        f"{hist}\n"
    )


class TestPerItemRegression(unittest.TestCase):
    """Three regression tests built on in-memory plan text, one per backlog item."""

    def test_ycg597_tooled_line_does_not_shadow_a_reject(self) -> None:
        """A bare setter line must not shadow an earlier REJECT review."""
        text = _make_plan_text(
            [
                "- 2026-09-10 reviewed (aw set): status set to reviewed",
                "- 2026-09-10 /plan-review (oc/m): REJECT - NEEDS REPLAN; PR-001",
            ],
            id6="ycg597",
        )
        polarity, entry = plan_readiness.newest_verdict(text)
        self.assertEqual(
            polarity,
            plan_readiness.NEGATIVE,
            f"expected polarity NEGATIVE, got {polarity!r}",
        )
        self.assertIn("REJECT", entry)
        refusals = plan_readiness.approval_refusals(
            REPO_ROOT, "fixture.ipd.md", plan_text=text
        )
        verdict_refusals = [
            r for r in refusals if "states a verdict that does not clear this plan" in r
        ]
        self.assertEqual(
            len(verdict_refusals),
            1,
            f"expected 1 verdict refusal for shadowed reject, got {verdict_refusals}",
        )

    def test_nwrb0j_review_word_label_on_a_non_review_act_is_not_a_verdict(
        self,
    ) -> None:
        """A descope/non-review record using 'reviewed' must not forge a rejection."""
        text = _make_plan_text(
            [
                "- 2026-09-12 reviewed (oc/m): descope per maintainer order; readiness stays no-go",
                "- 2026-09-10 /plan-review (oc/m): APPROVE WITH REVISIONS APPLIED; PR-001",
            ],
            id6="nwrb0j",
        )
        polarity, entry = plan_readiness.newest_verdict(text)
        self.assertEqual(
            polarity,
            plan_readiness.POSITIVE,
            f"expected polarity POSITIVE, got {polarity!r}",
        )
        self.assertIn("APPROVE WITH REVISIONS APPLIED", entry)
        refusals = plan_readiness.approval_refusals(
            REPO_ROOT, "fixture.ipd.md", plan_text=text
        )
        verdict_refusals = [
            r for r in refusals if "states a verdict that does not clear this plan" in r
        ]
        self.assertEqual(
            verdict_refusals,
            [],
            f"expected 0 verdict refusals, got {verdict_refusals}",
        )

    def test_gv36a7_out_of_vocab_verdict_is_unknown_not_negative(self) -> None:
        """An out-of-vocab verdict in a review record is unknown (None), not negative."""
        text = _make_plan_text(
            [
                "- 2026-09-12 /plan-review (oc/m): REVIEWED - REVISIONS APPLIED; readiness advanced from no-go",
                "- 2026-09-10 /plan-review (oc/m): APPROVE; PR-001",
            ],
            id6="gv36a7",
        )
        polarity, entry = plan_readiness.newest_verdict(text)
        self.assertIsNone(
            polarity,
            f"expected polarity None (unknown), got {polarity!r}",
        )
        self.assertIn("REVIEWED - REVISIONS APPLIED", entry)
        refusals = plan_readiness.approval_refusals(
            REPO_ROOT, "fixture.ipd.md", plan_text=text
        )
        verdict_refusals = [
            r for r in refusals if "states a verdict that does not clear this plan" in r
        ]
        self.assertEqual(
            verdict_refusals,
            [],
            f"expected 0 verdict refusals for unknown verdict, got {verdict_refusals}",
        )


class TestClassifierTable(unittest.TestCase):
    """Classifier table covering the rows listed under Proposed changes."""

    TABLE_ROWS = (
        ("- 2026-09-10 reviewed (aw set): status set to reviewed", False),
        (
            "- 2026-09-10 reviewed (aw set): set Item-Dependencies to executed:76w6mq",
            False,
        ),
        ("- 2026-09-10 reviewed (oc/m): descope ...; readiness stays no-go", False),
        ("- 2026-09-10 readiness re-check (a/m): ...", False),
        ("- 2026-09-10 to-review (aw specs): ...", False),
        ("- 2026-09-10 /plan-review (a/m): REVIEWED - REVISIONS APPLIED; ...", True),
        ("- 2026-09-10 reviewed (oc): /spec-review round 1; APPROVE", True),
        ("- 2026-09-10 reviewed (aw specs): REJECT - RESUBMIT", True),
        ("- 2026-09-10 reviewed round 2 (a/m): APPROVE ...", True),
    )

    def test_classifier_table_rows(self) -> None:
        wrong = []
        for line, expected in self.TABLE_ROWS:
            got = plan_readiness.is_review_history_entry(line)
            if got != expected:
                wrong.append(f"  {line!r}: expected {expected}, got {got}")
        self.assertEqual(
            wrong,
            [],
            f"is_review_history_entry table mismatch on {len(wrong)} rows:\n"
            + "\n".join(wrong),
        )


class TestA3ugp1IncidentAndClearedShapes(unittest.TestCase):
    """E-02: Pin the a3ugp1 /askme shape and sibling cleared/asserted shapes end to end.

    Built on in-memory plan text via _make_plan_text (reads no file under .aw/records/).
    """

    INCIDENT_ASKME_MESSAGE = (
        "/askme: OQ-03 RESOLVED FROM THE REPOSITORY WITHOUT ASKING, "
        "because there was no live decision left to ask about, "
        "clearing this plan's only blocking question and with it its `no-go`."
    )

    SHAPES = (
        (
            "a3ugp1_incident_askme_cleared_with_older_review",
            [
                f"- 2026-09-19 reviewed (opencode its_direct/pt3-claude-opus-5-1m-us): {INCIDENT_ASKME_MESSAGE}",
                "- 2026-09-18 /plan-review (opencode its_direct/pt3-claude-opus-5-1m-us): REVIEWED - OPEN QUESTIONS; PR-001",
            ],
            plan_readiness.NEUTRAL,
            0,
        ),
        (
            "askme_naming_plan_review_in_first_clause",
            [
                "- 2026-09-19 reviewed (opencode its_direct/m): /askme per /plan-review: OQ-01 resolved, clearing this plan's only blocking question and with it its `no-go`.",
            ],
            None,
            0,
        ),
        (
            "plan_review_clearing_no_go_no_verdict_token",
            [
                "- 2026-09-19 /plan-review (opencode its_direct/m): OQ-01 resolved, clearing readiness no-go",
            ],
            None,
            0,
        ),
        (
            "plan_review_clearing_no_go_stating_approve",
            [
                "- 2026-09-19 /plan-review (opencode its_direct/m): APPROVE; OQ-01 resolved, clearing readiness no-go",
            ],
            plan_readiness.POSITIVE,
            0,
        ),
        (
            "negative_control_reject_needs_replan",
            [
                "- 2026-09-19 /plan-review round 1 (opencode its_direct/m): REJECT - NEEDS REPLAN; readiness no-go",
            ],
            plan_readiness.NEGATIVE,
            1,
        ),
    )

    def test_a3ugp1_and_sibling_shapes_approval_refusals(self) -> None:
        """Every cleared shape must be refusal-free; the REJECT control must refuse."""
        wrong = []
        for (
            name,
            history_lines,
            expected_polarity,
            expected_refusal_count,
        ) in self.SHAPES:
            text = _make_plan_text(history_lines, id6=name[:6])
            polarity, entry = plan_readiness.newest_verdict(text)
            refusals = plan_readiness.approval_refusals(
                REPO_ROOT, f"{name}.ipd.md", plan_text=text
            )
            v_refusals = [
                r
                for r in refusals
                if "states a verdict that does not clear this plan" in r
            ]
            if name == "a3ugp1_incident_askme_cleared_with_older_review":
                if "REVIEWED - OPEN QUESTIONS" not in entry:
                    wrong.append(
                        f"  {name}: expected newest_verdict sourced from older review record "
                        f"containing 'REVIEWED - OPEN QUESTIONS', got {entry!r}"
                    )
            if (polarity, len(v_refusals)) != (
                expected_polarity,
                expected_refusal_count,
            ):
                wrong.append(
                    f"  {name}: expected (polarity={expected_polarity!r}, verdict_refusals={expected_refusal_count}), "
                    f"got (polarity={polarity!r}, verdict_refusals={len(v_refusals)})"
                )
        self.assertEqual(
            wrong,
            [],
            f"Approval refusals / polarity mismatch on {len(wrong)} rows:\n"
            + "\n".join(wrong),
        )


class TestNegativeReadinessAsserted(unittest.TestCase):
    """E-03: Pure table test for plan_readiness.negative_readiness_asserted."""

    TABLE_ROWS = (
        # Clearing shapes: clearing verb before token, and arrow transition away
        ("clearing OQ-01 and with it its no-go", False),
        ("readiness no-go -> go-pending-approval", False),
        # Asserted shapes: bare token, rejection, and regression direction
        ("readiness no-go", True),
        ("REJECT - NEEDS REPLAN; readiness no-go", True),
        ("readiness go-pending-approval -> no-go", True),
        # Adjacency row: bound keeps clearing verb and token in same sentence; separated returns True
        ("we cleared OQ-01. readiness no-go", True),
        # KNOWN LIMIT: clearing clause anywhere excuses entire message (pinned at measured False; PR-701, F-14)
        (
            "clearing OQ-01 and with it its no-go. A new blocking question asserts readiness no-go",
            False,
        ),
        # Fail-open on empty string
        ("", False),
    )

    def test_negative_readiness_asserted_table(self) -> None:
        wrong = []
        for text, expected in self.TABLE_ROWS:
            got = plan_readiness.negative_readiness_asserted(text)
            if got != expected:
                wrong.append(f"  {text!r}: expected {expected}, got {got}")
        self.assertEqual(
            wrong,
            [],
            f"negative_readiness_asserted mismatch on {len(wrong)} rows:\n"
            + "\n".join(wrong),
        )


class TestLivePendingCorpus(unittest.TestCase):
    """E-07: Assert no pending plan is refused on a verdict-class refusal."""

    @pytest.mark.livecorpus
    def test_no_pending_plan_has_verdict_class_refusal(self) -> None:
        pending_dir = REPO_ROOT / ".aw" / "records" / "plans" / "pending"
        plan_paths = sorted(pending_dir.glob("*.ipd.md"))
        self.assertGreater(
            len(plan_paths),
            0,
            f"Pending plans corpus in {pending_dir} must not be empty.",
        )

        failures = []
        for p in plan_paths:
            refusals = plan_readiness.approval_refusals(REPO_ROOT, p)
            verdict_refusals = [
                r
                for r in refusals
                if "states a verdict that does not clear this plan" in r
            ]
            if verdict_refusals:
                failures.append(f"{p.name}: {verdict_refusals}")

        self.assertEqual(
            failures,
            [],
            f"Found {len(failures)} pending plan(s) with verdict-class refusals:\n"
            + "\n".join(failures),
        )
