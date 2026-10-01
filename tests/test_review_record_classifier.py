"""Tests for review record classification and verdict reading (verdictread xpta5g).

Covers:
- E-01: Per-item regression tests for ycg597, nwrb0j, gv36a7, and classifier table test.
- E-03: One-parser invariant (exactly one history-record-parts parser).
- E-07: Live pending corpus invariant (livecorpus-marked: no verdict-class refusal on any pending plan; deselected in default runner lanes).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import pytest

from agent_workflows import plan_readiness, readiness_recheck
from agent_workflows import review_findings as RF

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


class TestTerminalDispositionRefusal(unittest.TestCase):
    """E-03: Pin terminal disposition refusal and stale escalation amendment behavior."""

    def test_case_1_terminal_dispositions_refused(self) -> None:
        """Case (1): a no-go plan under each terminal disposition is refused naming disposition."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()
            for disp in ("executed", "superseded", "not-executed"):
                disp_dir = root / ".aw" / "records" / "plans" / disp
                disp_dir.mkdir(parents=True, exist_ok=True)
                p = disp_dir / f"20260901-test-01-{disp[:6]}-test.ipd.md"
                p.write_text(
                    f"# IPD: Test {disp}\n\n"
                    f"- Id: {disp[:6]}\n"
                    f"- Status: {disp}\n"
                    f"- Readiness: no-go\n\n"
                    f"## Workflow history\n"
                    f"- 2026-09-01 /plan-review: APPROVE; PR-001\n",
                    encoding="utf-8",
                )
                res = plan_readiness.recheck_conditions(root, p)
                self.assertFalse(res.may_write, f"{disp} plan must not be writable")
                refusal_match = any(
                    f"terminal disposition `{disp}`" in r for r in res.refusals
                )
                self.assertTrue(
                    refusal_match,
                    f"Refusal for {disp} must name disposition and state history; got {res.refusals}",
                )

                # Drive through run_recheck_readiness with apply=True and assert bytes unchanged
                h_before = hashlib.sha256(p.read_bytes()).hexdigest()
                args = argparse.Namespace(
                    dir=str(root),
                    apply=True,
                    stale_findings=False,
                    selectors=[str(p)],
                    actor="test-actor",
                    agent=False,
                    json=False,
                )
                rc = readiness_recheck.run_recheck_readiness(args)
                self.assertEqual(rc, 0)
                h_after = hashlib.sha256(p.read_bytes()).hexdigest()
                self.assertEqual(
                    h_before, h_after, f"Terminal plan {disp} must not be modified"
                )

    def test_case_2_pending_plan_updated(self) -> None:
        """Case (2): a no-go plan under pending/ is still updated."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            pend_dir = root / ".aw" / "records" / "plans" / "pending"
            pend_dir.mkdir(parents=True, exist_ok=True)
            p = pend_dir / "20260901-test-01-pnd001-test.ipd.md"
            p.write_text(
                "# IPD: Pending Test\n\n"
                "- Id: pnd001\n"
                "- Status: to-review\n"
                "- Readiness: no-go\n\n"
                "## Workflow history\n"
                "- 2026-09-01 /plan-review: APPROVE; PR-001\n",
                encoding="utf-8",
            )
            res = plan_readiness.recheck_conditions(root, p)
            self.assertTrue(res.may_write, "Pending plan should be writable")
            self.assertEqual(res.refusals, ())

            args = argparse.Namespace(
                dir=str(root),
                apply=True,
                stale_findings=False,
                selectors=[str(p)],
                actor="test-actor",
                agent=False,
                json=False,
            )
            rc = readiness_recheck.run_recheck_readiness(args)
            self.assertEqual(rc, 0)
            text = p.read_text(encoding="utf-8")
            self.assertIn("- Readiness: go-pending-approval", text)
            self.assertIn("readiness re-check", text)

    def test_case_3_terminal_plan_stale_escalation_review_amended_plan_unchanged(
        self,
    ) -> None:
        """Case (3): a terminal plan carrying stale escalation has review amended while plan bytes unchanged."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            plans_dir = root / ".aw" / "records" / "plans" / "superseded"
            rev_dir = root / ".aw" / "records" / "reviews"
            plans_dir.mkdir(parents=True, exist_ok=True)
            rev_dir.mkdir(parents=True, exist_ok=True)

            p = plans_dir / "20260901-test-01-stale1-test.ipd.md"
            p.write_text(
                "# IPD: Stale Test\n\n"
                "- Id: stale1\n"
                "- Status: superseded\n"
                "- Readiness: no-go\n\n"
                "## Open questions\n"
                "### OQ-01: Question\n"
                "- Blocking: no\n"
                "- Status: resolved\n"
                "- Finding: PR-001\n\n"
                "## Workflow history\n"
                "- 2026-09-01 /plan-review: APPROVE; PR-001\n",
                encoding="utf-8",
            )
            r_file = rev_dir / "20260901-test-01-stale1-test.review.md"
            RF.write_review(
                r_file,
                subject_id="stale1",
                subject_type="ipd",
                reviewed_at="2026-09-01",
                reviewer="test-reviewer",
                verdict="APPROVE",
                rounds=[
                    RF.Round(
                        number=1,
                        findings=(
                            RF.Finding(
                                id="PR-001",
                                severity="blocker",
                                scope="plan",
                                area="clarity",
                                evidence="text",
                                finding="Finding text",
                                remediation_risk="low",
                                decision="open",
                                resolution="escalated as OQ-01",
                            ),
                        ),
                        decisions=(),
                    ),
                ],
            )
            h_before = hashlib.sha256(p.read_bytes()).hexdigest()
            args = argparse.Namespace(
                dir=str(root),
                apply=True,
                stale_findings=True,
                selectors=[str(p)],
                actor="test-actor",
                agent=False,
                json=False,
            )
            rc = readiness_recheck.run_recheck_readiness(args)
            self.assertEqual(rc, 0)
            h_after = hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(
                h_before, h_after, "Plan file bytes must remain byte-identical"
            )
            rev_text = r_file.read_text(encoding="utf-8")
            self.assertIn("Round 2", rev_text)
            self.assertIn("fixed", rev_text)

    def test_case_4_terminal_sharded_plan_recognized_as_terminal(self) -> None:
        """Case (4): a terminal plan sharded into <disposition>/YYYYMM/ is recognized as terminal.

        Note: zero plans in .aw/records/plans/ currently sit under a YYYYMM shard directory in
        the live repo, so this sharded structure is constructed under tmp_path.
        """
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            shard_dir = root / ".aw" / "records" / "plans" / "executed" / "202609"
            shard_dir.mkdir(parents=True, exist_ok=True)
            p = shard_dir / "20260901-test-01-shrd01-test.ipd.md"
            p.write_text(
                "# IPD: Shard Test\n\n"
                "- Id: shrd01\n"
                "- Status: executed\n"
                "- Readiness: no-go\n\n"
                "## Workflow history\n"
                "- 2026-09-01 /plan-review: APPROVE; PR-001\n",
                encoding="utf-8",
            )
            res = plan_readiness.recheck_conditions(root, p)
            self.assertFalse(
                res.may_write, "Sharded terminal plan must not be writable"
            )
            self.assertTrue(
                any("terminal disposition `executed`" in r for r in res.refusals),
                f"Expected executed disposition refusal, got {res.refusals}",
            )

    def test_case_5_out_of_tree_plan_not_refused_for_disposition(self) -> None:
        """Case (5): a plan at a path under no plans directory is NOT refused for disposition."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "repo"
            root.mkdir()
            p = root / "outside_plan.ipd.md"
            p.write_text(
                "# IPD: Out of Tree\n\n"
                "- Id: oot001\n"
                "- Status: to-review\n"
                "- Readiness: no-go\n\n"
                "## Workflow history\n"
                "- 2026-09-01 /plan-review: APPROVE; PR-001\n",
                encoding="utf-8",
            )
            res = plan_readiness.recheck_conditions(root, p)
            self.assertTrue(
                res.may_write,
                "Out-of-tree plan should be writable when conditions clear",
            )
            self.assertFalse(
                any("terminal disposition" in r for r in res.refusals),
                "Out-of-tree plan must not receive a disposition refusal",
            )

    def test_case_6_companion_backed_repo_terminal_plan_refused(self) -> None:
        """Case (6): in a companion-backed scratch repo, plan under resolved root is still refused."""
        with tempfile.TemporaryDirectory() as td:
            comp_root = Path(td) / "comp_repo"
            comp_root.mkdir()
            cfg_dir = comp_root / ".aw" / "config"
            cfg_dir.mkdir(parents=True)
            (cfg_dir / "project.json").write_text(
                json.dumps({"records_backend": "companion"}), encoding="utf-8"
            )
            comp_plans = (
                Path(td) / f"{comp_root.name}.aw" / "records" / "plans" / "not-executed"
            )
            comp_plans.mkdir(parents=True)
            p = comp_plans / "20260901-test-01-cmp001-test.ipd.md"
            p.write_text(
                "# IPD: Companion Test\n\n"
                "- Id: cmp001\n"
                "- Status: not-executed\n"
                "- Readiness: no-go\n\n"
                "## Workflow history\n"
                "- 2026-09-01 /plan-review: APPROVE; PR-001\n",
                encoding="utf-8",
            )
            res = plan_readiness.recheck_conditions(comp_root, p)
            self.assertFalse(
                res.may_write, "Companion terminal plan must not be writable"
            )
            self.assertTrue(
                any("terminal disposition `not-executed`" in r for r in res.refusals),
                f"Expected not-executed disposition refusal, got {res.refusals}",
            )
