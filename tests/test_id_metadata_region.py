"""Identity extraction is bounded to the METADATA REGION (IPD `76w6mq`, from backlog `cqytxf`).

THE DEFECT THESE TESTS PIN, stated once so a future reader knows what may not regress. The identity
readers matched `^- Id: <id6>` ANYWHERE in a document, so a file that merely QUOTED an example
metadata block was read as ASSERTING the quoted id6. That collided with the real artifact and made
it UNADDRESSABLE by every status verb, with the refusal explicitly saying it was "not overridable by
--force". The trigger was ordinary prose - quoting the metadata format - so the documents most
likely to break the tool were the specs and research ABOUT `aw` itself, and the same unbounded scan
also mis-reported `- Status:` and `- Set:`.

WHAT IS COVERED HERE:

1. `selectors.metadata_region`'s five input SHAPES, including the header-truncation case, which is
   the one most likely to be got wrong because it is COMMON rather than exotic.
2. The three private readers and the two PUBLIC runner-facing readers are all bounded, while their
   deliberately DIFFERENT whitespace tolerances are preserved (a quoted-metadata fix must not
   silently become a reader-harmonization).
3. The checker's own twin of the defect: `check_engine` applied a byte-identical pattern to a whole
   file body, so bounding only the selector would have left `aw check` asserting a collision no verb
   could see.
4. The `info`-severity `check.id6-outside-metadata-region` rule, which SURFACES an out-of-region
   `- Id:` rather than silently swallowing it, and provably does not fail the gate.

Fixtures are synthetic wherever a behavior can be pinned synthetically, so these tests do not rot
when the live corpus changes. The few live-tree assertions are guarded by a skip.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import artifact_core as _core
from agent_workflows import check_engine, selectors

# A bullet-front-matter record, the shape plans/specs/backlog/releases use.
BULLET_DOC = """# IPD: a plan about plans

- Date: 2026-09-08
- Kind: child
- Set: idcapture
- Status: approved
- Id: aaa111

## Workflow history
- 2026-09-08 draft: created.

## Goal

Quoting another plan's metadata block, which is legitimate cited content:

- Id: bbb222
- Status: reviewed
- Set: runflags
"""

# A YAML-fenced record, the shape research and roadmaps use.
YAML_DOC = """---
id: ccc333
created: 20260905
set: awmetastore
status: reference
---

# Where metadata should live

The block below is QUOTED, and discussing an id6 is not claiming it:

- Id: bbb222
- Status: reviewed
- Set: runflags
"""


class MetadataRegionShapeTests(unittest.TestCase):
    """E-01: the region boundary, for every shape present in the corpus."""

    def test_bullet_front_matter_region_ends_at_the_first_h2(self) -> None:
        region = selectors.metadata_region(BULLET_DOC)
        self.assertIn("- Id: aaa111", region)
        self.assertNotIn("bbb222", region)
        self.assertTrue(region.rstrip().endswith("- Id: aaa111"))

    def test_an_h1_title_does_not_end_the_region(self) -> None:
        """The boundary is `##`, not `#`, so a title-then-bullets file keeps its bullets."""
        doc = (
            "# A Title\n\n- Id: aaa111\n- Status: approved\n\n## Body\n\n- Id: bbb222\n"
        )
        region = selectors.metadata_region(doc)
        self.assertIn("- Id: aaa111", region)
        self.assertNotIn("bbb222", region)

    def test_yaml_fenced_region_is_the_leading_fence_block_only(self) -> None:
        region = selectors.metadata_region(YAML_DOC)
        self.assertTrue(region.startswith("---"))
        self.assertIn("id: ccc333", region)
        self.assertNotIn("bbb222", region)
        self.assertTrue(region.rstrip().endswith("---"))

    def test_yaml_region_excludes_body_bullets_before_the_first_heading(self) -> None:
        """A YAML doc's region stops at the fence even when body BULLETS follow its H1.

        Measured on the live corpus: exactly one record (`effzzi`) opens with a YAML fence and then
        carries narrative `- Key: value` bullets under its H1 BEFORE its first `##`. Those are prose,
        not metadata, so the fence - the record's real declaration site - is the correct bound. A
        "before the first `##`" rule would read `- Set: ...` out of that narrative.
        """
        doc = "---\nid: ccc333\nset: awoptimize\n---\n\n# Title\n\n- Set: `awoptimize`\n- Plans: nine\n\n## Body\n"
        region = selectors.metadata_region(doc)
        self.assertNotIn("`awoptimize`", region)
        self.assertIsNone(selectors._read_setid(doc))

    def test_a_file_with_no_h2_heading_at_all_still_has_a_region(self) -> None:
        """Header EXHAUSTION means "the region continues", never empty and never an error.

        This is the case a naive implementation breaks: measured on the live tree, 25 of 1614 tracked
        records present no `##` heading within the bounded header the readers actually get, so for
        them "everything before the first `##`" legitimately means the WHOLE window. Returning empty
        here would break identity extraction for 25 records while fixing 2.
        """
        doc = "# Title\n\n- Id: aaa111\n- Status: approved\n"
        self.assertEqual(selectors.metadata_region(doc), doc)
        self.assertEqual(selectors._read_id(doc), "aaa111")

    def test_a_header_truncated_mid_region_yields_the_whole_window(self) -> None:
        """The readers receive a BOUNDED header, so the terminator may lie past its end."""
        long_doc = (
            "# Title\n\n- Concern: "
            + ("x" * 5000)
            + "\n- Id: aaa111\n- Status: approved\n\n## Body\n\n- Id: bbb222\n"
        )
        truncated = long_doc[:4096]
        self.assertNotIn("## ", truncated)
        self.assertEqual(selectors.metadata_region(truncated), truncated)
        self.assertNotEqual(selectors.metadata_region(truncated), "")

    def test_an_unterminated_yaml_fence_yields_the_whole_input(self) -> None:
        doc = "---\nid: ccc333\nset: awmetastore\n" + ("y: " + "z" * 400 + "\n")
        self.assertEqual(selectors.metadata_region(doc), doc)

    def test_empty_input_is_tolerated(self) -> None:
        self.assertEqual(selectors.metadata_region(""), "")


class BoundedReaderTests(unittest.TestCase):
    """E-02: all three private readers consult only the region."""

    def test_a_quoted_block_does_not_override_a_real_declaration(self) -> None:
        self.assertEqual(selectors._read_id(BULLET_DOC), "aaa111")
        self.assertEqual(selectors._read_status(BULLET_DOC), "approved")
        self.assertEqual(selectors._read_setid(BULLET_DOC), "idcapture")

    def test_status_and_setid_share_the_bound_not_just_id(self) -> None:
        """The defect was never id-only; the same scan mis-read `- Status:` and `- Set:`."""
        doc = "# T\n\n- Id: aaa111\n\n## Body\n\n- Id: bbb222\n- Status: reviewed\n- Set: runflags\n"
        self.assertEqual(selectors._read_id(doc), "aaa111")
        self.assertIsNone(selectors._read_status(doc))
        self.assertIsNone(selectors._read_setid(doc))

    def test_a_yaml_doc_reads_as_ABSENT_rather_than_as_the_quoted_values(self) -> None:
        """`None` is the CORRECT post-fix answer for a YAML record, not its own YAML values.

        These patterns speak only the BULLET dialect and a YAML region contains no `^- Id:` line at
        all, so the fix stops the FALSE claim without inventing a true one. Teaching the readers the
        YAML dialect is a separate change (plan `xo3244`); an executor who expects `ccc333` here will
        wrongly think this regressed.
        """
        self.assertIsNone(selectors._read_id(YAML_DOC))
        self.assertIsNone(selectors._read_status(YAML_DOC))
        self.assertIsNone(selectors._read_setid(YAML_DOC))


class PublicReaderTests(unittest.TestCase):
    """E-03 / OQ-02: the runner-facing readers are bounded too, keeping their own patterns."""

    def test_public_readers_are_region_bounded(self) -> None:
        self.assertEqual(selectors.read_front_matter_id(BULLET_DOC), "aaa111")
        self.assertEqual(selectors.read_front_matter_status(BULLET_DOC), "approved")
        doc = "# T\n\n- Id: aaa111\n\n## Body\n\n- Id: bbb222\n- Status: reviewed\n"
        self.assertEqual(selectors.read_front_matter_id(doc), "aaa111")
        self.assertIsNone(selectors.read_front_matter_status(doc))

    def test_the_two_tiers_still_differ_on_whitespace(self) -> None:
        """Consolidate the REGION BOUND, never the whitespace tolerance.

        `_STATUS_RE`'s strictness is a documented MATCHING-BEHAVIOR contract that deliberately
        disagrees with `plans_index._META_RE`, so flattening these patterns would change what
        `aw find` matches. The permissive tier exists because both host runners once carried private
        copies that DRIFTED.
        """
        two_spaces = "# T\n\n-  Id: aaa111\n-  Status: approved\n"
        self.assertEqual(selectors.read_front_matter_id(two_spaces), "aaa111")
        self.assertEqual(selectors.read_front_matter_status(two_spaces), "approved")
        self.assertIsNone(selectors._read_id(two_spaces))
        self.assertIsNone(selectors._read_status(two_spaces))

    def test_a_long_plan_does_not_lose_its_region_to_truncation(self) -> None:
        """A driver reads PLAN front matter; exhaustion must not blank a long plan's identity."""
        long_meta = (
            "# IPD: x\n\n- Concern: "
            + ("q" * 6000)
            + "\n- Id: aaa111\n- Status: approved\n"
        )
        self.assertEqual(selectors.read_front_matter_id(long_meta), "aaa111")
        self.assertEqual(selectors.read_front_matter_status(long_meta), "approved")


class ResolutionTests(unittest.TestCase):
    """E-04/E-07: a quoted id6 must not RESOLVE, and a real one still must."""

    def _tree(self, tmp: Path) -> Path:
        pdir = tmp / ".aw" / "records" / "plans"
        pdir.mkdir(parents=True)
        (pdir / "20260908-idcapture-01-aaa111-the-real-plan.ipd.md").write_text(
            BULLET_DOC, encoding="utf-8"
        )
        rdir = tmp / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        (
            rdir / "20260905-awmetastore-00-ccc333-quoting-doc.research-prompt.md"
        ).write_text(YAML_DOC, encoding="utf-8")
        return tmp

    def test_a_body_quoted_id6_does_not_resolve_as_that_id6(self) -> None:
        """The first required regression: this FAILS against the pre-change reader."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            res = selectors.resolve(root, "plans", "bbb222")
            self.assertEqual(
                [], list(res.paths), "a QUOTED id6 must never resolve as an identity"
            )
            self.assertEqual(
                [], list(selectors.resolve(root, "research", "bbb222").paths)
            )

    def test_the_genuine_artifact_still_resolves_by_id6(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            res = selectors.resolve(root, "plans", "aaa111")
            self.assertEqual(selectors.MATCH_ID6, res.kind)
            self.assertEqual(1, len(res.paths))

    def test_no_collision_across_the_two_trees(self) -> None:
        """The live shape: a quoting doc must not become a second claimant of a real id6."""
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            for rtype in ("plans", "research"):
                paths, err = selectors.resolve_for_mutation(root, rtype, "bbb222")
                self.assertEqual([], paths)
                self.assertIsNotNone(err)
                self.assertNotIn("collision", err or "")

    def test_precedence_is_preserved_on_a_filename_present_token(self) -> None:
        """Removing an id6 match must not silently narrow the LATER rules.

        Asserted on a token that CAN still match, deliberately: the quoted id6 appears in no
        filename, so demanding a substring fallback for it would assert something false. `ccc333` IS
        in a filename, so it must still resolve - by `substring`, not `id6`, because this plan does
        not teach the reader the YAML dialect.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            res = selectors.resolve(root, "research", "ccc333")
            self.assertEqual(1, len(res.paths))
            self.assertEqual(selectors.MATCH_SUBSTRING, res.kind)
            self.assertEqual(
                [], list(selectors.resolve(root, "research", "bbb222").paths)
            )


class CheckerBoundTests(unittest.TestCase):
    """The checker had its OWN copy of the defect; bounding only the selector was a half-fix."""

    def _tree(self, tmp: Path) -> Path:
        rdir = tmp / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        (
            rdir / "20260905-awmetastore-00-ccc333-quoting-doc.research-prompt.md"
        ).write_text(YAML_DOC, encoding="utf-8")
        (
            rdir / "20260905-awmetastore-01-ddd444-other-quoting-doc.research-report.md"
        ).write_text(YAML_DOC.replace("ccc333", "ddd444"), encoding="utf-8")
        return tmp

    def test_two_docs_quoting_one_block_are_not_a_collision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            found = [
                d
                for d in check_engine.check_collisions(root, include_untracked=True)
                if d.rule == "check.id6-collision"
            ]
            self.assertEqual(
                [],
                found,
                f"a quotation is not a declaration; got {[d.detail for d in found]}",
            )

    def test_a_real_duplicate_declaration_is_still_reported(self) -> None:
        """The contrast case, so the fix is not mistaken for disabling the collision rule."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = root / ".aw" / "records" / "plans"
            pdir.mkdir(parents=True)
            (pdir / "20260908-s-01-aaa111-one.ipd.md").write_text(
                "# One\n\n- Id: aaa111\n- Status: approved\n", encoding="utf-8"
            )
            (pdir / "20260908-s-02-aaa111-two.ipd.md").write_text(
                "# Two\n\n- Id: aaa111\n- Status: approved\n", encoding="utf-8"
            )
            found = [
                d
                for d in check_engine.check_collisions(root, include_untracked=True)
                if d.rule == "check.id6-collision"
            ]
            self.assertEqual(1, len(found))

    def test_the_checker_reads_setid_from_the_region_too(self) -> None:
        self.assertEqual((None, None), check_engine._parse_setid(YAML_DOC))
        self.assertEqual(("idcapture", None), check_engine._parse_setid(BULLET_DOC))


class OutsideRegionRuleTests(unittest.TestCase):
    """E-05: surface the ambiguity rather than swallowing it, at a severity that cannot fail."""

    def _tree(self, tmp: Path) -> Path:
        rdir = tmp / ".aw" / "records" / "research"
        rdir.mkdir(parents=True)
        (
            rdir / "20260905-awmetastore-00-ccc333-quoting-doc.research-prompt.md"
        ).write_text(YAML_DOC, encoding="utf-8")
        (
            rdir / "20260905-awmetastore-01-ddd444-other-quoting-doc.research-report.md"
        ).write_text(YAML_DOC.replace("ccc333", "ddd444"), encoding="utf-8")
        return tmp

    def test_it_fires_on_every_offending_file_not_just_the_first(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            found = check_engine.check_id_outside_metadata_region(
                root, include_untracked=True
            )
            self.assertEqual(
                2, len(found), "a rule flagging only one of two is half-built"
            )
            self.assertEqual(
                {"check.id6-outside-metadata-region"}, {d.rule for d in found}
            )

    def test_it_is_registered_at_info_and_cannot_fail_the_gate(self) -> None:
        """`warning` would NOT have been advisory: only `info` exits 0 (measured)."""
        spec = check_engine.rule_spec("check.id6-outside-metadata-region")
        self.assertEqual("info", spec.severity)
        self.assertNotEqual("warning", spec.severity)
        with tempfile.TemporaryDirectory() as tmp:
            root = self._tree(Path(tmp))
            found = check_engine.check_id_outside_metadata_region(
                root, include_untracked=True
            )
            self.assertEqual(0, _core.drift_exit_code(found))

    def test_an_unregistered_rule_would_have_defaulted_to_error(self) -> None:
        """Why the registry entry is mandatory rather than bookkeeping."""
        self.assertEqual(
            "error", check_engine.rule_spec("check.not-a-real-rule").severity
        )

    def test_a_conformant_record_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pdir = root / ".aw" / "records" / "plans"
            pdir.mkdir(parents=True)
            (pdir / "20260908-idcapture-01-aaa111-the-real-plan.ipd.md").write_text(
                "# T\n\n- Id: aaa111\n- Status: approved\n\n## Body\n\nprose only\n",
                encoding="utf-8",
            )
            self.assertEqual(
                [],
                check_engine.check_id_outside_metadata_region(
                    root, include_untracked=True
                ),
            )

    def test_it_fires_on_the_shape_without_needing_a_colliding_counterpart(
        self,
    ) -> None:
        """Strictly stronger than the collision rule for a LONE quoting document."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rdir = root / ".aw" / "records" / "research"
            rdir.mkdir(parents=True)
            (
                rdir / "20260905-s-00-ccc333-lone-quoting-doc.research-prompt.md"
            ).write_text(YAML_DOC, encoding="utf-8")
            collisions = [
                d
                for d in check_engine.check_collisions(root, include_untracked=True)
                if d.rule == "check.id6-collision"
            ]
            self.assertEqual(
                [], collisions, "one side only: no collision is reportable"
            )
            self.assertEqual(
                1,
                len(
                    check_engine.check_id_outside_metadata_region(
                        root, include_untracked=True
                    )
                ),
            )


class LiveTreeTests(unittest.TestCase):
    """A few assertions against the real corpus, guarded so they cannot break a clone."""

    def setUp(self) -> None:
        self.repo = Path(__file__).resolve().parents[1]
        if not (self.repo / ".aw" / "records" / "plans").is_dir():
            self.skipTest("not running inside the agent-workflows repo tree")

    def test_no_live_record_declares_an_id_outside_its_region(self) -> None:
        """The count may legitimately grow (quoting is allowed); the SHAPE is what is pinned."""
        found = check_engine.check_id_outside_metadata_region(self.repo)
        self.assertEqual(0, _core.drift_exit_code(found))
        for d in found:
            self.assertEqual("info", d.severity)

    def test_every_records_own_id6_still_resolves_to_itself(self) -> None:
        """Bounding must not make a real artifact unresolvable - the inverse of the fixed bug."""
        checked = 0
        for path, text in selectors._iter_files(self.repo, "plans"):
            id6 = selectors._read_id(text)
            if not id6:
                continue
            checked += 1
            if checked > 40:
                break
            res = selectors.resolve(self.repo, "plans", id6)
            self.assertIn(
                path.resolve(),
                [p.resolve() for p in res.paths],
                f"{path.name} declares {id6} but does not resolve to itself",
            )
        self.assertGreater(checked, 10, "expected a populated plans tree")


if __name__ == "__main__":
    unittest.main()
