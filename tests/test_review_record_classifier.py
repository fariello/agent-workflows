"""Tests for review record classification and verdict reading (verdictread xpta5g).

Covers:
- E-01: Per-item regression tests for ycg597, nwrb0j, gv36a7, and classifier table test.
- E-03: One-parser invariant (exactly one history-record-parts parser).
- E-07: Live pending corpus invariant (no verdict-class refusal on any pending plan).
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

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


class TestOneParserInvariant(unittest.TestCase):
    """E-03: Assert exactly ONE history-record parser in plan_readiness.py."""

    def test_exactly_one_history_record_parts_parser_in_plan_readiness(self) -> None:
        plan_readiness_path = REPO_ROOT / "agent_workflows" / "plan_readiness.py"
        source = plan_readiness_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(plan_readiness_path))

        # Scan string constants and regex compiles for patterns having all 4 group names:
        # date, mid, actor, msg
        required_groups = {"date", "mid", "actor", "msg"}
        matching_patterns: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                val = node.value
                groups = set(re.findall(r"\(\?P<([a-zA-Z0-9_]+)>", val))
                if required_groups.issubset(groups):
                    matching_patterns.append(val)

        self.assertEqual(
            len(matching_patterns),
            1,
            f"Expected exactly ONE pattern with history record capture groups "
            f"{required_groups} in {plan_readiness_path}, found {len(matching_patterns)}: "
            f"{matching_patterns}",
        )


class TestLivePendingCorpus(unittest.TestCase):
    """E-07: Assert no pending plan is refused on a verdict-class refusal."""

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
