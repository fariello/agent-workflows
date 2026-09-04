"""Characterization matrix for the three selector resolvers BEFORE unification (IPD laykok E-01/V-01).

Pins the CURRENT behavior of every selector-to-file resolver across the full selector vocabulary
{direct path, id6, setid, status, exact stem, filename substring}, INCLUDING the exact-vs-substring
match SEMANTICS each resolver uses per kind (not merely which kinds match). This is the baseline the
unified resolver (E-02) must converge to; E-03 must not silently lose any successful resolution here.

Documented gaps this pins (from Step 0 of the IPD):
  * ``selectors.resolve_one``  - has NO direct-path branch (a path selector -> no match); an exact
    stem resolves only incidentally via the substring rule; id6/status/setid are exact.
  * ``artifact_rename.find_target_record`` - the most complete: direct path + resolve_one + an extra
    scan matching ``selector in name`` OR ``selector == stem``; returns a SINGLE path (first hit).
  * ``status_set.match_selector`` - direct path + exact id6 + exact setid + filename substring, but
    NO status and NO bare-stem kind.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_rename as AR
from agent_workflows import selectors
from agent_workflows import status_set as SS


class ResolverMatrixTests(unittest.TestCase):
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

    # ---- resolver adapters returning sorted filename lists (or None for the single-path finder) ----

    def _resolve_one(self, sel):
        return sorted(p.name for p in selectors.resolve_one(self.root, "plans", sel))

    def _match_selector(self, sel):
        recs = SS.inventory_all_artifacts(self.root)
        return sorted(r.path.name for r in SS.match_selector(sel, recs, self.root))

    def _find_target_record(self, sel):
        r = AR.find_target_record(self.root, "plans", sel)
        return r.name if r else None

    # ---- resolve_one: no path branch; exact id/set/status; stem only via substring ----

    def test_resolve_one_path_kind_no_match(self) -> None:
        rel = ".aw/records/plans/pending/20260101-demo-01-aaa111-alpha.ipd.md"
        self.assertEqual(self._resolve_one(rel), [])  # documented gap: no path branch

    def test_resolve_one_exact_kinds(self) -> None:
        self.assertEqual(self._resolve_one("aaa111"), [self.A.name])  # id6
        self.assertEqual(self._resolve_one("demo"), [self.A.name])  # setid
        self.assertEqual(self._resolve_one("approved"), [self.A.name])  # status

    def test_resolve_one_stem_and_substring(self) -> None:
        # An exact stem resolves (incidentally, via the substring rule since stem is in name).
        self.assertEqual(
            self._resolve_one("20260101-demo-01-aaa111-alpha.ipd"), [self.A.name]
        )
        self.assertEqual(self._resolve_one("alpha"), [self.A.name])
        # A substring matching BOTH files over-matches (returns both).
        self.assertEqual(self._resolve_one("2026"), sorted([self.A.name, self.B.name]))

    # ---- find_target_record: most complete; single path; path branch present ----

    def test_find_target_record_all_unique_kinds(self) -> None:
        rel = ".aw/records/plans/pending/20260101-demo-01-aaa111-alpha.ipd.md"
        self.assertEqual(self._find_target_record(rel), self.A.name)  # path
        self.assertEqual(self._find_target_record("aaa111"), self.A.name)  # id6
        self.assertEqual(self._find_target_record("demo"), self.A.name)  # setid
        self.assertEqual(self._find_target_record("approved"), self.A.name)  # status
        self.assertEqual(
            self._find_target_record("20260101-demo-01-aaa111-alpha.ipd"), self.A.name
        )  # exact stem
        self.assertEqual(self._find_target_record("alpha"), self.A.name)  # substring

    def test_find_target_record_returns_single_for_multi(self) -> None:
        # A substring matching both returns a SINGLE path (first hit) today, not an error.
        r = self._find_target_record("2026")
        self.assertIn(r, {self.A.name, self.B.name})

    def test_find_target_record_no_match(self) -> None:
        self.assertIsNone(self._find_target_record("zzzzzz"))

    # ---- match_selector: path + exact id6/setid + substring; NO status, NO stem kind ----

    def test_match_selector_path_id_set_substring(self) -> None:
        rel = ".aw/records/plans/pending/20260101-demo-01-aaa111-alpha.ipd.md"
        self.assertEqual(self._match_selector(rel), [self.A.name])  # path
        self.assertEqual(self._match_selector("aaa111"), [self.A.name])  # id6
        self.assertEqual(self._match_selector("demo"), [self.A.name])  # setid
        self.assertEqual(self._match_selector("alpha"), [self.A.name])  # substring
        self.assertEqual(
            self._match_selector("2026"), sorted([self.A.name, self.B.name])
        )  # substring over-match

    def test_match_selector_status_now_supported(self) -> None:
        # PRE-unification gap (match_selector had NO status kind) is CLOSED by E-03: after routing
        # match_selector through the unified resolver, a status selector now resolves. This is the
        # intended new capability (V-03), not a regression.
        self.assertEqual(self._match_selector("approved"), [self.A.name])

    def test_match_selector_stem_via_substring(self) -> None:
        # No dedicated stem kind, but the stem is a filename substring, so it matches via rule 4.
        self.assertEqual(
            self._match_selector("20260101-demo-01-aaa111-alpha.ipd"), [self.A.name]
        )


class UnifiedResolveTests(unittest.TestCase):
    """The unified `selectors.resolve` (E-02/V-02): full vocabulary, exact kinds 2-5, substring only
    at 6, structured no/unique/ambiguous result carrying the match KIND, and clear denied-kind
    rejection (never a silent no-match)."""

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

    def _r(self, sel, **kw):
        return selectors.resolve(self.root, "plans", sel, **kw)

    def test_precedence_and_kinds(self) -> None:
        rel = ".aw/records/plans/pending/20260101-demo-01-aaa111-alpha.ipd.md"
        self.assertEqual(self._r(rel).kind, selectors.MATCH_PATH)
        self.assertEqual(self._r("aaa111").kind, selectors.MATCH_ID6)
        self.assertEqual(self._r("demo").kind, selectors.MATCH_SETID)
        self.assertEqual(self._r("approved").kind, selectors.MATCH_STATUS)
        self.assertEqual(
            self._r("20260101-demo-01-aaa111-alpha.ipd").kind, selectors.MATCH_STEM
        )
        self.assertEqual(self._r("alpha").kind, selectors.MATCH_SUBSTRING)

    def test_exact_kinds_are_exact_not_substring(self) -> None:
        # 'other' is an EXACT setid; it must resolve via setid to file B, NOT substring-match the
        # 'other' inside B's filename as a filename fragment (both would pick B here, so prove the
        # KIND is setid, not substring - the exact-vs-substring semantics fix).
        r = self._r("other")
        self.assertEqual(r.kind, selectors.MATCH_SETID)
        self.assertEqual([p.name for p in r.paths], [self.B.name])
        # An id6-shaped token that is NOT any file's Id does not fall through to substring on a
        # coincidental filename fragment unless it is literally a substring.
        self.assertFalse(self._r("zzzzzz").is_match)

    def test_result_shape_unique_and_ambiguous(self) -> None:
        uniq = self._r("aaa111")
        self.assertTrue(uniq.is_unique)
        self.assertFalse(uniq.is_ambiguous)
        amb = self._r("2026")
        self.assertTrue(amb.is_ambiguous)
        self.assertEqual(amb.kind, selectors.MATCH_SUBSTRING)
        self.assertEqual(len(amb.paths), 2)

    def test_denied_kind_is_clear_rejection_not_silent(self) -> None:
        # A selector that matches ONLY via a denied kind returns rejected_kind set, empty paths.
        r = self._r("alpha", deny=frozenset({selectors.MATCH_SUBSTRING}))
        self.assertEqual(r.paths, [])
        self.assertEqual(r.rejected_kind, selectors.MATCH_SUBSTRING)
        self.assertFalse(r.is_match)
        # allow-list form: allow only id6, give a setid -> rejected naming setid.
        r2 = self._r("demo", allow=frozenset({selectors.MATCH_ID6}))
        self.assertEqual(r2.rejected_kind, selectors.MATCH_SETID)
        self.assertEqual(r2.paths, [])

    def test_no_match_is_empty_not_rejection(self) -> None:
        r = self._r("zzzzzz")
        self.assertEqual(r.paths, [])
        self.assertIsNone(r.kind)
        self.assertIsNone(r.rejected_kind)


class OtherCatchAllDoesNotClaimTypedTreesTests(unittest.TestCase):
    """A `reviews` record must not ALSO resolve as `other` (regression, measured 2026-09-04).

    THE BUG: `reviews` was in neither `KNOWN_PRIMARY_TYPES` nor `EXCLUDED_RECORD_DIRS`, so the
    `other` catch-all swept `.aw/records/reviews/`. A bare id6 then matched TWICE - the plan as
    `plans`/id6 and its OWN review record as `other`/substring - and `aw set approved <id6>` refused
    with "id6 collision ... a data bug to fix, not overridable by --force". It was a RESOLVER defect
    rather than a data bug, and it broke bare-id6 `aw set` for every plan that had been reviewed
    (all 28 at the time).

    Why the obvious fixes are both wrong, pinned here so neither is "simplified" back in: adding
    `reviews` to `KNOWN_PRIMARY_TYPES` breaks the bijection `run_selection_policy` asserts and claims
    a review is a selectable work item, while adding it to `EXCLUDED_RECORD_DIRS` would make it
    unresolvable and un-`find`-able. Hence the third set, `NON_PRIMARY_RECORD_DIRS`.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        recs = self.root / ".aw" / "records"
        pend = recs / "plans" / "pending"
        pend.mkdir(parents=True)
        # A plan and ITS review record, sharing the id6 exactly as the real trees do.
        self.plan = pend / "20260101-demo-01-aaa111-alpha.ipd.md"
        self.plan.write_text(
            "# IPD: alpha\n\n- Id: aaa111\n- Status: reviewed\n- Set: demo\n\n## Goal\n\nx\n",
            encoding="utf-8",
        )
        reviews = recs / "reviews"
        reviews.mkdir(parents=True)
        self.review = reviews / "20260101-demo-01-aaa111-alpha.review.md"
        self.review.write_text(
            "# Review: alpha\n\n- Plan-Id: aaa111\n- Verdict: APPROVE\n\n## Round 1\n\nx\n",
            encoding="utf-8",
        )
        # A genuinely UNOWNED tree, which `other` legitimately still owns.
        misc = recs / "prompt-library"
        misc.mkdir(parents=True)
        self.misc = misc / "20260101-demo-01-ccc333-gamma.md"
        self.misc.write_text("# gamma\n\n- Id: ccc333\n", encoding="utf-8")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_reviews_is_not_swept_into_other(self) -> None:
        r = selectors.resolve(self.root, "other", "aaa111")
        self.assertEqual(
            r.paths, [], "a reviews record must not resolve as the `other` catch-all"
        )

    def test_review_record_is_still_resolvable_as_its_own_type(self) -> None:
        # The fix must not make reviews unreachable; `aw find reviews <id6>` depends on this.
        r = selectors.resolve(self.root, "reviews", "aaa111")
        self.assertEqual([p.resolve() for p in r.paths], [self.review.resolve()])

    def test_other_still_owns_a_genuinely_unowned_tree(self) -> None:
        # Proves the fix excluded only the TYPED tree, not the catch-all's real purpose.
        r = selectors.resolve(self.root, "other", "ccc333")
        self.assertEqual([p.resolve() for p in r.paths], [self.misc.resolve()])

    def test_bare_id6_is_unambiguous_across_types(self) -> None:
        # The end-to-end symptom: this is what `aw set approved <id6>` resolves, and a second match
        # here is what produced the un-overridable "id6 collision" refusal.
        recs = SS.inventory_all_artifacts(self.root)
        matches = SS.match_selector("aaa111", recs, self.root)
        self.assertEqual(
            [m.record_type for m in matches],
            ["plans"],
            "a bare id6 must resolve to the PLAN alone, not also its review record",
        )

    def test_the_three_dir_sets_are_disjoint(self) -> None:
        # Each set answers a different question (selectable work item / typed but status-less /
        # not a record tree at all), so an entry appearing in two of them is a contradiction.
        self.assertEqual(
            selectors.KNOWN_PRIMARY_TYPES & selectors.NON_PRIMARY_RECORD_DIRS, set()
        )
        self.assertEqual(
            selectors.KNOWN_PRIMARY_TYPES & selectors.EXCLUDED_RECORD_DIRS, set()
        )
        self.assertEqual(
            selectors.NON_PRIMARY_RECORD_DIRS & selectors.EXCLUDED_RECORD_DIRS, set()
        )

    def test_reviews_has_no_status_lifecycle(self) -> None:
        # WHY `reviews` cannot simply join KNOWN_PRIMARY_TYPES: `artifact_naming.TYPE_FACET` omits it
        # deliberately because a review has no `- Status:` bullet, and `TYPE_FACET` is ITERATED by
        # `status_set.detect_artifact_type`, so an entry would make `aw set` accept a review file.
        from agent_workflows import artifact_naming as naming

        self.assertNotIn("reviews", naming.TYPE_FACET)
        self.assertIsNone(SS.canonical_type("reviews"))


if __name__ == "__main__":
    unittest.main()
