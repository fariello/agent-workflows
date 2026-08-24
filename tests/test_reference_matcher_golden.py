"""Golden characterization of the three reference rewriters + the per-type dangling matchers BEFORE
unification (IPD 3cmnfc E-01/V-01).

Pins which citation FORMS each rewriter rewrites today and which citation forms each type's dangling
checker recognizes, so the unification (E-02..E-04) can be shown to (a) fix research's full-name-only
orphan gap, (b) preserve the plans legacy three-form behavior, and (c) never start rewriting id6/setid.

Documented pre-refactor divergence this pins:
  * ``plans_refs.plan_reference_rewrites``      - clustered name: FULL-NAME only (its bare-stem comes
    from the legacy YYYYMMDD-HHMM-NN prefix, which a clustered name lacks); legacy name: full-name +
    bare-stem + range.
  * ``artifact_rename.plan_reference_rewrites`` - full-name + whole-stem (name minus .md) + range.
  * ``research_refs.plan_reference_rewrites``   - FULL-NAME only (the orphan gap).
  * dangling matchers: plans recognize only ``PLAN-<id6>``; research recognizes ``RSCH-<id6>`` + a
    full parseable research filename; neither recognizes a setid citation.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_rename as AR
from agent_workflows import plans_index as PI
from agent_workflows import plans_refs as PR
from agent_workflows import research_contract as RC
from agent_workflows import research_refs as RR


def _kinds(edits):
    """Map a RefEdit list to a sorted {kind: total_hits} dict (plans/artifact_rename have .kind)."""
    out = {}
    for e in edits:
        out[e.kind] = out.get(e.kind, 0) + e.hits
    return out


class RewriterGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.citing_dir = self.root / ".aw" / "records" / "plans" / "pending"
        self.citing_dir.mkdir(parents=True)
        self.citer = self.citing_dir / "20260101-demo-09-ccc333-citer.md"
        self.citer.write_text(
            "Full: 20260101-demo-01-aaa111-alpha.ipd.md\n"
            "Stem: 20260101-demo-01-aaa111-alpha.ipd\n"
            "Range: 20260101-demo-01-aaa111-alpha..03\n"
            "Legacy full: 20260101-1200-01-oldplan.md\n"
            "Legacy prefix: 20260101-1200-01\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_plans_clustered_now_full_and_wholestem(self) -> None:
        # POST-unification (E-04): a CLUSTERED plan rename now ALSO rewrites the whole-stem citation
        # (covering the "Stem:" line + the range shorthand) - the same fix research gets. Pre-
        # unification this was full-name only (decision 05-3cmnfc-D1).
        edits = PR.plan_reference_rewrites(
            self.root,
            {
                "20260101-demo-01-aaa111-alpha.ipd.md": "20260101-demo-01-aaa111-beta.ipd.md"
            },
            self.citing_dir,
        )
        self.assertEqual(_kinds(edits), {"full-name": 1, "bare-stem": 2})

    def test_plans_legacy_full_and_stem_preserved(self) -> None:
        # A LEGACY plan rename still rewrites the full name + the legacy YYYYMMDD-HHMM-NN prefix
        # stem (preserved); post-unification it ALSO emits the whole-stem form, so 2 bare-stem edits.
        edits = PR.plan_reference_rewrites(
            self.root,
            {"20260101-1200-01-oldplan.md": "20260101-1200-02-oldplan.md"},
            self.citing_dir,
        )
        self.assertEqual(_kinds(edits), {"full-name": 1, "bare-stem": 2})

    def test_artifact_rename_clustered_full_and_wholestem(self) -> None:
        edits = AR.plan_reference_rewrites(
            self.root,
            "20260101-demo-01-aaa111-alpha.ipd.md",
            "20260101-demo-01-aaa111-beta.ipd.md",
        )
        # whole-stem catches both the "Stem:" line and the range shorthand -> 2 hits (unchanged).
        self.assertEqual(_kinds(edits), {"full-name": 1, "bare-stem": 2})

    def test_research_now_rewrites_full_and_bare_stem(self) -> None:
        # POST-unification (E-04): the research orphan gap is CLOSED - a research rename now rewrites
        # the full name AND the bare stem (was full-name ONLY before). research RefEdit has no .kind.
        edits = RR.plan_reference_rewrites(
            self.root,
            {
                "20260101-demo-01-aaa111-alpha.ipd.md": "20260101-demo-01-aaa111-beta.ipd.md"
            },
        )
        olds = sorted((e.old_name, e.hits) for e in edits)
        self.assertEqual(
            olds,
            [
                ("20260101-demo-01-aaa111-alpha.ipd", 2),  # whole-stem (Stem + Range)
                ("20260101-demo-01-aaa111-alpha.ipd.md", 1),  # full-name
            ],
        )


class DanglingMatcherGoldenTests(unittest.TestCase):
    def test_plans_matcher_recognizes_only_plan_handle(self) -> None:
        # _plan_cite_matcher recognizes PLAN-<id6> only (not RSCH-, not a bare filename, not setid).
        self.assertEqual(PI._plan_cite_matcher("see PLAN-aaa111 here"), ["aaa111"])
        self.assertEqual(PI._plan_cite_matcher("see RSCH-bbb222 here"), [])
        self.assertEqual(
            PI._plan_cite_matcher("20260101-demo-01-aaa111-alpha.ipd.md"), []
        )
        self.assertEqual(PI._plan_cite_matcher("Set: demo"), [])

    def test_research_matcher_recognizes_rsch_and_full_filename(self) -> None:
        # iter_id6_citations recognizes RSCH-<id6> and a full parseable research filename.
        self.assertEqual(RC.iter_id6_citations("see RSCH-aaa111 here"), ["aaa111"])
        got = RC.iter_id6_citations(
            "cite 20260101-demo-01-abc123-slug.gpt56.findings.md"
        )
        self.assertEqual(got, ["abc123"])
        # A PLAN- handle is NOT a research citation; a bare setid is not either.
        self.assertEqual(RC.iter_id6_citations("PLAN-aaa111"), [])
        self.assertEqual(RC.iter_id6_citations("Set: demo"), [])


class UnifiedMatcherTests(unittest.TestCase):
    """The unified matcher (E-02/V-02): reproduces the strongest three-form rewrite for any type and
    emits NO edit for a bare id6 or setid token."""

    def setUp(self) -> None:
        from agent_workflows import artifact_refs as Aref

        self.Aref = Aref
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        cd = self.root / ".aw" / "records" / "plans" / "pending"
        cd.mkdir(parents=True)
        (cd / "20260101-demo-09-ccc333-citer.md").write_text(
            "Full: 20260101-demo-01-aaa111-alpha.ipd.md\n"
            "Stem: 20260101-demo-01-aaa111-alpha.ipd\n"
            "Range: 20260101-demo-01-aaa111-alpha..03\n"
            "id6 handle: PLAN-aaa111\n"
            "bare id6: aaa111\n"
            "setid: demo\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_three_form_rewrite_for_any_type(self) -> None:
        edits = self.Aref.plan_reference_rewrites(
            self.root,
            {
                "20260101-demo-01-aaa111-alpha.ipd.md": "20260101-demo-01-aaa111-beta.ipd.md"
            },
        )
        kinds = _kinds(edits)
        self.assertEqual(kinds.get("full-name"), 1)
        self.assertEqual(kinds.get("bare-stem"), 2)  # whole-stem covers Stem + Range

    def test_no_edit_for_bare_id6_or_setid(self) -> None:
        # The map targets a name; NO edit should touch the bare 'aaa111' id6 or 'demo' setid tokens.
        edits = self.Aref.plan_reference_rewrites(
            self.root,
            {
                "20260101-demo-01-aaa111-alpha.ipd.md": "20260101-demo-01-aaa111-beta.ipd.md"
            },
        )
        for e in edits:
            self.assertNotEqual(e.old, "aaa111")
            self.assertNotEqual(e.old, "demo")
        # And a map that would only touch id6/setid produces nothing (we never build such a map;
        # confirm the matcher does not invent id6/setid edits from prose).
        self.assertTrue(all(e.kind in ("full-name", "bare-stem") for e in edits))


if __name__ == "__main__":
    unittest.main()
