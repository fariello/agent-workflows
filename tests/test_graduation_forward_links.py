"""Tests for forward graduation links in aw graduation (IPD pw2ln3 E-08).

Covers:
  (1) Forward-only fixture: backlog item with Graduated-To and plans with no From-Backlog.
  (2) Reverse-only fixture: plan with From-Backlog and no Graduated-To on the item.
  (3) Agreement in both directions: source with Graduated-To and plan with From-Backlog in that Set.
  (4) Disagreement visible: Graduated-To naming non-existent Set -> forward_unresolved and check findings agree.
  (5) Sweep identity: all plan setids indexed (including executed/), terminal Set resolves clean.
  (6) No source at all: affirmative zero answer ("Proceed.") preserved.
  (7) --agent evidence value: string scalar survives compaction as graduation-forward:<...>.
  (8) Spec source: spec record with Graduated-To resolves with source_kind=None and source_kind="spec".
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from agent_workflows import check_engine, cli, releases


def _capture_cli(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = cli.main(list(args))
    return rc, out.getvalue(), err.getvalue()


class GraduationForwardLinksTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / ".aw" / "records" / "backlog" / "graduated").mkdir(parents=True)
        (self.root / ".aw" / "records" / "plans" / "pending").mkdir(parents=True)
        (self.root / ".aw" / "records" / "plans" / "executed").mkdir(parents=True)
        (self.root / ".aw" / "records" / "specs" / "approved").mkdir(parents=True)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_case_1_forward_only(self) -> None:
        """(1) FORWARD-ONLY FIXTURE: graduated backlog item with Graduated-To: fwdset and

        two plans in Set fwdset with no From-Backlog. Assert graduation_cluster reports both
        plans as forward artifacts, and human output does NOT contain 'Proceed' and DOES
        name 'fwdset'.
        """
        b_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260927-fwdonly-01-fwd001-item.backlog.md"
        )
        b_file.write_text(
            "# Backlog: Item\n\n- Id: fwd001\n- Status: graduated\n- Graduated-To: fwdset\n",
            encoding="utf-8",
        )
        p1 = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-fwdset-01-plan01-first.ipd.md"
        )
        p1.write_text(
            "# IPD: First\n\n- Id: plan01\n- Status: pending\n- Set: fwdset (First)\n- Order: 1\n",
            encoding="utf-8",
        )
        p2 = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-fwdset-02-plan02-second.ipd.md"
        )
        p2.write_text(
            "# IPD: Second\n\n- Id: plan02\n- Status: pending\n- Set: fwdset (Second)\n- Order: 2\n",
            encoding="utf-8",
        )

        cluster = check_engine.graduation_cluster(self.root, "fwd001")
        self.assertEqual(cluster.artifact_count, 0)
        self.assertEqual(cluster.forward_setids, ("fwdset",))
        self.assertEqual(cluster.forward_count, 2)
        self.assertTrue(cluster.has_any_link)
        self.assertEqual(
            [a.id6 for a in cluster.forward_artifacts], ["plan01", "plan02"]
        )

        rc, out, _ = _capture_cli("graduation", "fwd001", "--dir", str(self.root))
        self.assertEqual(rc, 0)
        self.assertNotIn("Proceed", out)
        self.assertIn("fwdset", out)
        self.assertIn("Forward links (this source's Graduated-To)", out)

    def test_case_2_reverse_only(self) -> None:
        """(2) REVERSE-ONLY: a plan with From-Backlog: <item> and no Graduated-To on the item.

        Reverse artifacts as before, forward empty, output unchanged in shape.
        """
        b_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260927-revonly-01-rev001-item.backlog.md"
        )
        b_file.write_text(
            "# Backlog: Item\n\n- Id: rev001\n- Status: graduated\n",
            encoding="utf-8",
        )
        p_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-revset-01-plan03-rev.ipd.md"
        )
        p_file.write_text(
            "# IPD: Rev\n\n- Id: plan03\n- Status: pending\n- Set: revset\n- Order: 1\n- From-Backlog: rev001\n",
            encoding="utf-8",
        )

        cluster = check_engine.graduation_cluster(self.root, "rev001")
        self.assertEqual(cluster.artifact_count, 1)
        self.assertEqual(cluster.setids, ("revset",))
        if hasattr(cluster, "forward_setids"):
            self.assertEqual(cluster.forward_setids, ())
            self.assertEqual(cluster.forward_artifacts, ())
            self.assertEqual(cluster.forward_count, 0)
            self.assertTrue(cluster.has_any_link)

        rc, out, _ = _capture_cli("graduation", "rev001", "--dir", str(self.root))
        self.assertEqual(rc, 0)
        self.assertIn("Existing artifacts for source rev001", out)
        self.assertNotIn("Forward links (this source's Graduated-To)", out)
        self.assertIn("revset", out)

    def test_case_3_agreement_both_directions(self) -> None:
        """(3) AGREEMENT BOTH DIRECTIONS: a source with Graduated-To: bothset and a plan in

        bothset carrying From-Backlog: <source>. The plan appears in BOTH artifacts and
        forward_artifacts, and set(cluster.setids) == set(cluster.forward_setids).
        """
        b_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260927-both-01-bth001-item.backlog.md"
        )
        b_file.write_text(
            "# Backlog: Item\n\n- Id: bth001\n- Status: graduated\n- Graduated-To: bothset\n",
            encoding="utf-8",
        )
        p_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-bothset-01-plan04-both.ipd.md"
        )
        p_file.write_text(
            "# IPD: Both\n\n- Id: plan04\n- Status: pending\n- Set: bothset\n- Order: 1\n- From-Backlog: bth001\n",
            encoding="utf-8",
        )

        cluster = check_engine.graduation_cluster(self.root, "bth001")
        self.assertEqual(len(cluster.artifacts), 1)
        self.assertEqual(len(cluster.forward_artifacts), 1)
        self.assertEqual(cluster.artifacts[0].id6, "plan04")
        self.assertEqual(cluster.forward_artifacts[0].id6, "plan04")
        self.assertEqual(set(cluster.setids), set(cluster.forward_setids))
        self.assertEqual(set(cluster.setids), {"bothset"})

    def test_case_4_disagreement_visible(self) -> None:
        """(4) DISAGREEMENT VISIBLE: Graduated-To: nosuchset -> listed in forward_unresolved

        and printed as naming no plan Set, and check_graduated_to on the same fixture reports
        check.graduated-to-dangling.
        """
        b_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260927-dangle-01-dng001-item.backlog.md"
        )
        b_file.write_text(
            "# Backlog: Item\n\n- Id: dng001\n- Status: graduated\n- Graduated-To: nosuchset\n",
            encoding="utf-8",
        )
        # Create at least one valid plan so the corpus is not considered empty by check_graduated_to
        p_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-restr-01-plan05-other.ipd.md"
        )
        p_file.write_text(
            "# IPD: Other\n\n- Id: plan05\n- Status: pending\n- Set: realset\n- Order: 1\n",
            encoding="utf-8",
        )

        cluster = check_engine.graduation_cluster(self.root, "dng001")
        self.assertEqual(cluster.forward_unresolved, ("nosuchset",))

        rc, out, _ = _capture_cli("graduation", "dng001", "--dir", str(self.root))
        self.assertEqual(rc, 0)
        self.assertIn("names no plan Set", out)
        self.assertIn("nosuchset", out)

        findings = releases.check_graduated_to(self.root)
        self.assertTrue(
            any(f.rule == "check.graduated-to-dangling" for f in findings),
            f"Expected check.graduated-to-dangling in {findings}",
        )

    def test_case_5_sweep_identity(self) -> None:
        """(5) SWEEP IDENTITY: set(build_plan_setid_index(tmp)) equals every setid on the fixture's

        plans, including one in executed/, and check_graduated_to does NOT flag a link to a Set
        whose only plan is executed.
        """
        p1 = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-setone-01-plan10-live.ipd.md"
        )
        p1.write_text(
            "# IPD: Live\n\n- Id: plan10\n- Status: pending\n- Set: setone\n- Order: 1\n",
            encoding="utf-8",
        )
        p2 = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "executed"
            / "20260927-execset-01-plan11-done.ipd.md"
        )
        p2.write_text(
            "# IPD: Exec\n\n- Id: plan11\n- Status: executed\n- Set: execset\n- Order: 1\n",
            encoding="utf-8",
        )
        b_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260927-swp-01-swp001-item.backlog.md"
        )
        b_file.write_text(
            "# Backlog: Item\n\n- Id: swp001\n- Status: graduated\n- Graduated-To: execset\n",
            encoding="utf-8",
        )

        index = check_engine.build_plan_setid_index(self.root)
        self.assertEqual(set(index.keys()), {"setone", "execset"})

        findings = releases.check_graduated_to(self.root)
        self.assertEqual(findings, [])

    def test_case_6_no_source_at_all(self) -> None:
        """(6) No source at all: 'nothing yet ... Proceed.' still printed (affirmative zero answer)."""
        cluster = check_engine.graduation_cluster(self.root, "none01")
        if hasattr(cluster, "has_any_link"):
            self.assertFalse(cluster.has_any_link)
            self.assertEqual(cluster.forward_setids, ())
            self.assertEqual(cluster.forward_artifacts, ())
        self.assertEqual(cluster.artifact_count, 0)

        rc, out, _ = _capture_cli("graduation", "none01", "--dir", str(self.root))
        self.assertEqual(rc, 0)
        self.assertIn(
            "nothing yet: no plan or spec links to source none01. Proceed.", out
        )

    def test_case_7_agent_evidence_value(self) -> None:
        """(7) --agent output contains the graduation-forward evidence key for case (1),

        and the compacted item startswith 'graduation-forward:' AND contains the setid.
        """
        b_file = (
            self.root
            / ".aw"
            / "records"
            / "backlog"
            / "graduated"
            / "20260927-agnt-01-agnt01-item.backlog.md"
        )
        b_file.write_text(
            "# Backlog: Item\n\n- Id: agnt01\n- Status: graduated\n- Graduated-To: fwdset\n",
            encoding="utf-8",
        )
        p_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-fwdset-01-plan20-p.ipd.md"
        )
        p_file.write_text(
            "# IPD: P\n\n- Id: plan20\n- Status: pending\n- Set: fwdset\n- Order: 1\n",
            encoding="utf-8",
        )

        rc, out, _ = _capture_cli(
            "graduation", "agnt01", "--dir", str(self.root), "--agent"
        )
        self.assertEqual(rc, 0)
        data = json.loads(out)
        evidence = data.get("evidence", [])
        forward_items = [
            e
            for e in evidence
            if e == "graduation-forward" or e.startswith("graduation-forward:")
        ]
        self.assertTrue(
            forward_items,
            f"Expected graduation-forward item in evidence: {evidence}",
        )
        # CASE (7) REQUIREMENT: assert the compacted item equals/startswith 'graduation-forward:'
        # AND contains the setid (must fail if value is a dict, which compacts to bare 'graduation-forward').
        item = forward_items[0]
        self.assertTrue(
            item.startswith("graduation-forward:"),
            f"Compacted evidence item must carry scalar string value with ':', got: {item!r}",
        )
        self.assertIn("fwdset", item)

    def test_case_8_spec_source(self) -> None:
        """(8) THE SPEC SOURCE: a spec record declaring - Id: and - Graduated-To: specset plus

        a plan in specset, asserting its forward links resolve. Driven BOTH with
        source_kind=None and with source_kind="spec".
        """
        s_file = (
            self.root
            / ".aw"
            / "records"
            / "specs"
            / "approved"
            / "20260927-spec01-01-spec01-universal.spec.md"
        )
        s_file.write_text(
            "# Spec: Spec\n\n- Id: spec01\n- Status: approved\n- Graduated-To: specset\n",
            encoding="utf-8",
        )
        p_file = (
            self.root
            / ".aw"
            / "records"
            / "plans"
            / "pending"
            / "20260927-specset-01-plan30-specplan.ipd.md"
        )
        p_file.write_text(
            "# IPD: Specplan\n\n- Id: plan30\n- Status: pending\n- Set: specset\n- Order: 1\n",
            encoding="utf-8",
        )

        # Drive with source_kind=None
        cluster_none = check_engine.graduation_cluster(
            self.root, "spec01", source_kind=None
        )
        self.assertEqual(cluster_none.forward_setids, ("specset",))
        self.assertEqual(cluster_none.forward_count, 1)
        self.assertEqual(cluster_none.forward_artifacts[0].id6, "plan30")

        # Drive with source_kind="spec" (exercises the spec -> specs mapping)
        cluster_spec = check_engine.graduation_cluster(
            self.root, "spec01", source_kind="spec"
        )
        self.assertEqual(cluster_spec.forward_setids, ("specset",))
        self.assertEqual(cluster_spec.forward_count, 1)
        self.assertEqual(cluster_spec.forward_artifacts[0].id6, "plan30")


if __name__ == "__main__":
    unittest.main()
