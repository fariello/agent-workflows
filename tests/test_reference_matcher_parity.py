"""Reference-matcher parity, the research fix, id6/setid stability, and the dangling policy
(IPD 3cmnfc E-05/V-05 + V-03).

Proves, on the unified library:
  (a) a research rename now rewrites full-name AND bare-stem citations (the fixed orphan gap);
  (b) an id6 handle (``PLAN-<id6>``/``RSCH-<id6>``) and a bare setid are NEVER rewritten by any
      rename (stability preserved);
  (c) the dangling checker recognizes the id6 handles uniformly for plans and research; and
  (V-03) the ``dead_filename_citations`` primitive flags a truly-dead, type-appropriate filename
      while ignoring an existing name, a cross-type name, and prose.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_refs as Aref


class ResearchFixAndStabilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.docs = self.root / ".aw" / "records" / "specs"
        self.docs.mkdir(parents=True)
        self.citer = self.docs / "citer.spec.md"
        self.citer.write_text(
            "Full: 20260101-demo-01-abc123-topic.gpt56.findings.md\n"
            "Stem: 20260101-demo-01-abc123-topic.gpt56.findings\n"
            "id6 handle: RSCH-abc123 and PLAN-aaa111\n"
            "bare id6: abc123\n"
            "setid: demo\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_research_rename_rewrites_full_and_bare_stem(self) -> None:
        from agent_workflows import research_refs as RR

        name_map = {
            "20260101-demo-01-abc123-topic.gpt56.findings.md": "20260101-demo-02-abc123-topic.gpt56.findings.md",
        }
        edits = RR.plan_reference_rewrites(self.root, name_map)
        RR.apply_reference_rewrites(edits)
        text = self.citer.read_text(encoding="utf-8")
        # Full-name rewritten:
        self.assertIn("20260101-demo-02-abc123-topic.gpt56.findings.md", text)
        # Bare-stem rewritten (the FIXED gap - research used to leave this orphaned):
        self.assertIn("20260101-demo-02-abc123-topic.gpt56.findings\n", text)
        self.assertNotIn("20260101-demo-01-abc123-topic.gpt56.findings.md", text)

    def test_id6_handle_and_setid_never_rewritten(self) -> None:
        from agent_workflows import research_refs as RR

        name_map = {
            "20260101-demo-01-abc123-topic.gpt56.findings.md": "20260101-demo-02-abc123-topic.gpt56.findings.md",
        }
        edits = RR.plan_reference_rewrites(self.root, name_map)
        RR.apply_reference_rewrites(edits)
        text = self.citer.read_text(encoding="utf-8")
        # The RSCH-/PLAN- handles, the bare id6, and the setid are all untouched (stable by design).
        self.assertIn("RSCH-abc123 and PLAN-aaa111", text)
        self.assertIn("bare id6: abc123", text)
        self.assertIn("setid: demo", text)


class DanglingConsistencyTests(unittest.TestCase):
    def test_id6_handles_recognized_uniformly(self) -> None:
        plan_m = Aref.make_cite_matcher("PLAN")
        rsch_m = Aref.make_cite_matcher("RSCH")
        self.assertEqual(plan_m("see PLAN-aaa111 x"), ["aaa111"])
        self.assertEqual(rsch_m("see RSCH-bbb222 x"), ["bbb222"])
        # Each recognizes only its own handle (no cross-recognition).
        self.assertEqual(plan_m("RSCH-bbb222"), [])
        self.assertEqual(rsch_m("PLAN-aaa111"), [])


class DeadFilenamePrimitiveTests(unittest.TestCase):
    """V-03: dead_filename_citations flags a truly-dead, TYPE-APPROPRIATE filename; it never flags an
    existing name, a cross-type name, a setid, or arbitrary prose (decision D2's low-false-positive
    scoping)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        pend = self.root / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        # An EXISTING plan + an EXISTING research doc (cross-type name that must not be flagged).
        (pend / "20260101-demo-01-aaa111-alive.ipd.md").write_text(
            "# IPD\n\n- Id: aaa111\n- Set: demo\n\n## Goal\n\nx\n", encoding="utf-8"
        )
        rdir = self.root / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        (rdir / "20260101-demo-01-rsc111-topic.gpt56.findings.md").write_text(
            "---\nid: rsc111\n---\n", encoding="utf-8"
        )
        self.citer = self.root / ".aw" / "records" / "specs"
        self.citer.mkdir(parents=True)
        (self.citer / "c.spec.md").write_text(
            "alive plan: 20260101-demo-01-aaa111-alive.ipd.md\n"
            "dead plan: 20260101-demo-09-zzz999-gone.ipd.md\n"
            "cross-type research: 20260101-demo-01-rsc111-topic.gpt56.findings.md\n"
            "setid: demo\n"
            "prose: see the plan about foo\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_flags_only_the_truly_dead_type_appropriate_name(self) -> None:
        danglers = Aref.dead_filename_citations(
            self.root, "plans", exclude_root=self.root / ".aw" / "records" / "plans"
        )
        toks = [d.id6 for d in danglers]
        # ONLY the dead plan name is flagged.
        self.assertEqual(toks, ["20260101-demo-09-zzz999-gone.ipd.md"])
        # Explicitly NOT the alive plan, the cross-type research name, the setid, or prose.
        self.assertNotIn("20260101-demo-01-aaa111-alive.ipd.md", toks)
        self.assertNotIn("20260101-demo-01-rsc111-topic.gpt56.findings.md", toks)

    def test_cross_type_research_name_not_flagged_for_plans(self) -> None:
        # A research .findings.md name is not a plans citation, so the plans check ignores it even
        # though it is absent from the plans/ dir (the spec-only-stem safeguard).
        danglers = Aref.dead_filename_citations(
            self.root, "plans", exclude_root=self.root / ".aw" / "records" / "plans"
        )
        for d in danglers:
            self.assertNotIn("findings", d.id6)


if __name__ == "__main__":
    unittest.main()
