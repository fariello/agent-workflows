"""Cross-verb selector parity + kind-aware ambiguity policy (IPD laykok E-04/V-04 and E-07/V-07).

E-04: the SAME selector of a given kind resolves to the SAME file across every verb's resolution
entry point (rename/group/set/show/find and, for a terminal plan, archive), and a genuinely
ambiguous selector yields the SAME uniform result shape.

E-07: the kind-aware ambiguity policy for MUTATING verbs (resolved OQ-01): a setid multi-match acts
on ALL members with no --force; a unique-id (id6/path/stem) collision ALWAYS refuses; a filename
substring multi-match refuses unless --force; read-only verbs list all matches.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_rename as AR
from agent_workflows import selectors
from agent_workflows import status_set as SS


class CrossVerbParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        pend = self.root / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        self.A = pend / "20260101-demo-01-aaa111-alpha.ipd.md"
        self.A.write_text(
            "# IPD: alpha\n\n- Id: aaa111\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        self.B = pend / "20260101-other-01-bbb222-beta.ipd.md"
        self.B.write_text(
            "# IPD: beta\n\n- Id: bbb222\n- Status: draft\n- Set: other\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _via_find(self, sel):  # rename/group entry point
        r = AR.find_target_record(self.root, "plans", sel)
        return r.resolve() if r else None

    def _via_resolve(self, sel):  # show/find entry point
        res = selectors.resolve(self.root, "plans", sel)
        return res.paths[0].resolve() if res.is_unique else None

    def _via_match_selector(self, sel):  # set entry point
        recs = SS.inventory_all_artifacts(self.root)
        ms = SS.match_selector(sel, recs, self.root)
        return ms[0].path.resolve() if len(ms) == 1 else None

    def test_unique_selector_resolves_same_file_every_verb(self) -> None:
        want = self.A.resolve()
        for sel in ("aaa111", "20260101-demo-01-aaa111-alpha.ipd", "demo", "approved"):
            with self.subTest(selector=sel):
                self.assertEqual(self._via_find(sel), want)
                self.assertEqual(self._via_resolve(sel), want)
                self.assertEqual(self._via_match_selector(sel), want)

    def test_path_selector_parity(self) -> None:
        rel = ".aw/records/plans/pending/20260101-demo-01-aaa111-alpha.ipd.md"
        want = self.A.resolve()
        self.assertEqual(self._via_find(rel), want)
        self.assertEqual(self._via_resolve(rel), want)
        self.assertEqual(self._via_match_selector(rel), want)

    def test_ambiguous_selector_same_shape_every_verb(self) -> None:
        # A substring matching BOTH files is ambiguous. The unified resolver reports it uniformly.
        res = selectors.resolve(self.root, "plans", "2026")
        self.assertTrue(res.is_ambiguous)
        self.assertEqual(res.kind, selectors.MATCH_SUBSTRING)
        # match_selector (set's resolver) returns both records for the same ambiguous selector.
        recs = SS.inventory_all_artifacts(self.root)
        self.assertEqual(len(SS.match_selector("2026", recs, self.root)), 2)


class KindAwareAmbiguityPolicyTests(unittest.TestCase):
    """E-07/V-07: resolve_for_mutation applies the kind-aware policy; read-only resolve lists all."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        pend = self.root / ".aw" / "records" / "plans" / "pending"
        pend.mkdir(parents=True)
        # Two plans in the SAME set (setid multi-target), plus a substring that hits both.
        self.A = pend / "20260101-demo-01-aaa111-alpha.ipd.md"
        self.A.write_text(
            "# IPD\n\n- Id: aaa111\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        self.B = pend / "20260101-demo-02-bbb222-beta.ipd.md"
        self.B.write_text(
            "# IPD\n\n- Id: bbb222\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_setid_multi_target_no_force(self) -> None:
        paths, err = selectors.resolve_for_mutation(self.root, "plans", "demo")
        self.assertIsNone(err)
        self.assertEqual(len(paths), 2)  # acts on ALL Set members, no --force

    def test_substring_multi_refuses_without_force_then_succeeds(self) -> None:
        # '2026' is a filename substring hitting both -> refuse without force.
        paths, err = selectors.resolve_for_mutation(self.root, "plans", "2026")
        self.assertEqual(paths, [])
        self.assertIsNotNone(err)
        self.assertIn("ambiguous", err)
        self.assertIn("--force", err)
        # With force, acts on all.
        paths2, err2 = selectors.resolve_for_mutation(
            self.root, "plans", "2026", force=True
        )
        self.assertIsNone(err2)
        self.assertEqual(len(paths2), 2)

    def test_unique_id_collision_always_refuses(self) -> None:
        # Create an id6 COLLISION: two files declaring the same frontmatter Id.
        pend = self.root / ".aw" / "records" / "plans" / "pending"
        c1 = pend / "20260101-demo-03-dup999-c.ipd.md"
        c1.write_text(
            "# IPD\n\n- Id: dup999\n- Status: approved\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        c2 = pend / "20260101-other-01-dup999-d.ipd.md"
        c2.write_text(
            "# IPD\n\n- Id: dup999\n- Status: approved\n- Set: other\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        # A unique-id (id6) matching two files is a COLLISION: refuse even with force.
        paths, err = selectors.resolve_for_mutation(self.root, "plans", "dup999")
        self.assertEqual(paths, [])
        self.assertIn("collision", err)
        paths_f, err_f = selectors.resolve_for_mutation(
            self.root, "plans", "dup999", force=True
        )
        self.assertEqual(paths_f, [])  # --force does NOT override a collision
        self.assertIn("collision", err_f)

    def test_readonly_resolve_lists_all_matches(self) -> None:
        # Read-only resolve() does not refuse; it returns all matches for the caller to list.
        res = selectors.resolve(self.root, "plans", "demo")
        self.assertEqual(len(res.paths), 2)
        res2 = selectors.resolve(self.root, "plans", "2026")
        self.assertEqual(len(res2.paths), 2)

    def test_denied_kind_is_clear_rejection(self) -> None:
        paths, err = selectors.resolve_for_mutation(
            self.root, "plans", "alpha", deny=frozenset({selectors.MATCH_SUBSTRING})
        )
        self.assertEqual(paths, [])
        self.assertIn("does not accept", err)
        self.assertIn("substring", err)


if __name__ == "__main__":
    unittest.main()
