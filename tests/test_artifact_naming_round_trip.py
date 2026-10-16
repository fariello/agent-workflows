"""Behavioral round-trip tests for build_clustered_name and parse_clustered (IPD 90yi49).

Restores behavioral coverage asserting that build_clustered_name and parse_clustered are
mutual inverses on conformant clustered names, with no source-reading or code-pinning
assertions (GUIDING_PRINCIPLES P16).
"""

from __future__ import annotations

import unittest

from agent_workflows import artifact_naming


class ArtifactNamingRoundTripTests(unittest.TestCase):
    def test_clustered_build_then_parse(self) -> None:
        # Canonical ipd facet assertion as specified in E-01.
        name = artifact_naming.build_clustered_name(
            date="20260823",
            set_id="myset",
            order=3,
            id6="abc123",
            slug="a-slug",
            artifact_type="ipd",
        )
        self.assertEqual(name, "20260823-myset-03-abc123-a-slug.ipd.md")
        m = artifact_naming.parse_clustered(name)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group("date"), "20260823")
        self.assertEqual(m.group("set"), "myset")
        self.assertEqual(int(m.group("nn")), 3)
        self.assertEqual(m.group("id6"), "abc123")
        self.assertEqual(m.group("slug"), "a-slug")
        self.assertEqual(m.group("type"), "ipd")

        # Repeat for artifact_type=None and every member of ARTIFACT_TYPE_FACETS via subTest.
        cases = (None, *artifact_naming.ARTIFACT_TYPE_FACETS)
        for facet in cases:
            with self.subTest(artifact_type=facet):
                built = artifact_naming.build_clustered_name(
                    date="20260823",
                    set_id="myset",
                    order=3,
                    id6="abc123",
                    slug="a-slug",
                    artifact_type=facet,
                )
                expected_suffix = f".{facet}.md" if facet else ".md"
                self.assertEqual(
                    built, f"20260823-myset-03-abc123-a-slug{expected_suffix}"
                )
                parsed = artifact_naming.parse_clustered(built)
                self.assertIsNotNone(parsed)
                assert parsed is not None
                self.assertEqual(parsed.group("date"), "20260823")
                self.assertEqual(parsed.group("set"), "myset")
                self.assertEqual(int(parsed.group("nn")), 3)
                self.assertEqual(parsed.group("id6"), "abc123")
                self.assertEqual(parsed.group("slug"), "a-slug")
                self.assertEqual(parsed.group("type"), facet)

    def test_clustered_parse_then_build_is_identity(self) -> None:
        corpus = (
            "20260823-myset-03-abc123-a-slug.ipd.md",
            "20260823-myset-03-abc123-a-slug.md",
            "20260823-my-set-11-zzz999-longer-slug.spec.md",
            "20260101-foo-12-abc123-bar-01-def456-slug.ipd.md",
        )
        for name in corpus:
            with self.subTest(name=name):
                m = artifact_naming.parse_clustered(name)
                self.assertIsNotNone(m, f"expected conformant name to parse: {name}")
                assert m is not None
                if name == "20260101-foo-12-abc123-bar-01-def456-slug.ipd.md":
                    self.assertEqual(m.group("set"), "foo")
                    self.assertEqual(m.group("nn"), "12")
                    self.assertEqual(m.group("slug"), "bar-01-def456-slug")
                rebuilt = artifact_naming.build_clustered_name(
                    date=m.group("date"),
                    set_id=m.group("set"),
                    order=int(m.group("nn")),
                    id6=m.group("id6"),
                    slug=m.group("slug"),
                    artifact_type=m.group("type"),
                )
                self.assertEqual(rebuilt, name)

    def test_build_clustered_name_rejects_unknown_facet(self) -> None:
        with self.assertRaises(ValueError):
            artifact_naming.build_clustered_name(
                date="20260823",
                set_id="myset",
                order=3,
                id6="abc123",
                slug="a-slug",
                artifact_type="ipdd",
            )

    def test_parse_clustered_rejects_unknown_facet(self) -> None:
        result = artifact_naming.parse_clustered(
            "20260823-myset-03-abc123-a-slug.ipdd.md"
        )
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
