"""Golden characterization suite for the filename-grammar authority (IPD o6b8l3, E-01/V-01).

This pins the CURRENT observable naming behavior BEFORE the naming-authority refactor, so that
consolidating the ~6 duplicated grammar regexes and 3 facet tables into one module cannot silently
change which name any builder PRODUCES or which name any validator ACCEPTS/PARSES.

It exercises, for every artifact type that has a builder or validator today:
  * BUILD  - the exact filename a current builder emits for fixed component inputs
             (plans via ``plans_refs.clustered_name``; research via ``research_contract.format_name``;
             specs/prompts/backlog/walkthroughs/roadmaps/releases via
             ``artifact_rename.compute_target_name`` on rename, since those types mint no new name
             except through rename);
  * PARSE/VALIDATE - the exact conformant/non-conformant + extracted-component result of the current
             validators (``normalize_plan_names.is_conformant``/``parse_name``,
             ``plans_refs._CLUSTERED_RE``, ``research_contract.parse_name``,
             ``status_set.detect_artifact_type``), INCLUDING the legacy ``YYYYMMDD-HHMM-NN`` form,
             the walkthrough facet form, and the CLOSED-vs-OPEN facet divergence between
             ``plans_refs._CLUSTERED_RE`` (closed enum) and ``artifact_rename._UNIFORM_RE`` (open).

After E-02..E-04 re-route builders/validators through the single authority, EVERY assertion here
MUST still pass unchanged. A red assertion means the unification changed a produced/accepted name -
a golden-suite diff that MUST be confirmed against this baseline before it is accepted.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from agent_workflows import artifact_rename as AR
from agent_workflows import plans_refs as R
from agent_workflows import research_contract as RC
from agent_workflows import status_set as SS

REPO_ROOT = Path(__file__).resolve().parent.parent
NORMALIZER = (
    REPO_ROOT
    / ".aw"
    / "system"
    / "workflows"
    / "setup-repo"
    / "tools"
    / "normalize_plan_names.py"
)


def _load_normalizer():
    spec = importlib.util.spec_from_file_location("awgolden_npn", NORMALIZER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# --------------------------------------------------------------------------------------
# BUILD golden values
# --------------------------------------------------------------------------------------


class PlansBuildGoldenTests(unittest.TestCase):
    def test_clustered_name_faceted(self) -> None:
        self.assertEqual(
            R.clustered_name(
                date="20260823",
                set_id="myset",
                order=1,
                id6="abc123",
                slug="my-slug",
                artifact_type="ipd",
            ),
            "20260823-myset-01-abc123-my-slug.ipd.md",
        )

    def test_clustered_name_bare(self) -> None:
        self.assertEqual(
            R.clustered_name(
                date="20260823",
                set_id="myset",
                order=1,
                id6="abc123",
                slug="my-slug",
            ),
            "20260823-myset-01-abc123-my-slug.md",
        )

    def test_clustered_name_kebabs_set_and_slug_and_pads_order(self) -> None:
        self.assertEqual(
            R.clustered_name(
                date="20260823",
                set_id="My Set",
                order=7,
                id6="abc123",
                slug="Some Slug",
                artifact_type="ipd",
            ),
            "20260823-my-set-07-abc123-some-slug.ipd.md",
        )

    def test_clustered_name_unknown_type_raises(self) -> None:
        with self.assertRaises(ValueError):
            R.clustered_name(
                date="20260823",
                set_id="myset",
                order=1,
                id6="abc123",
                slug="x",
                artifact_type="nope",
            )


class ResearchBuildGoldenTests(unittest.TestCase):
    def test_format_name_with_model(self) -> None:
        rn = RC.ResearchName(
            date="20260823",
            set_id="myset",
            order="02",
            id6="abc123",
            slug="my-slug",
            model="gpt56",
            kind="findings",
        )
        self.assertEqual(
            RC.format_name(rn), "20260823-myset-02-abc123-my-slug.gpt56.findings.md"
        )

    def test_format_name_without_model(self) -> None:
        rn = RC.ResearchName(
            date="20260823",
            set_id="myset",
            order="02",
            id6="abc123",
            slug="my-slug",
            model=None,
            kind="findings",
        )
        self.assertEqual(
            RC.format_name(rn), "20260823-myset-02-abc123-my-slug.findings.md"
        )


class RenameBuildGoldenTests(unittest.TestCase):
    """``artifact_rename.compute_target_name`` is the builder for the six generic types on rename.

    Each case pins the EXACT (new_name, error) tuple today. This covers all five legacy branches:
    uniform clustered, legacy timestamp, walkthrough dated, walkthrough bare, dated-slug-facet, plus
    the free-form fallback.
    """

    def _check(self, name, artifact_type, kwargs, expected):
        self.assertEqual(
            AR.compute_target_name(name, artifact_type, **kwargs), expected
        )

    def test_uniform_reslug(self) -> None:
        self._check(
            "20260823-myset-01-abc123-old.ipd.md",
            "plans",
            {"new_slug": "new-slug"},
            ("20260823-myset-01-abc123-new-slug.ipd.md", None),
        )

    def test_uniform_reset_reorder(self) -> None:
        self._check(
            "20260823-myset-01-abc123-old.ipd.md",
            "plans",
            {"new_set": "other", "new_order": 5},
            ("20260823-other-05-abc123-old.ipd.md", None),
        )

    def test_uniform_open_facet_preserved(self) -> None:
        # artifact_rename._UNIFORM_RE accepts an OPEN facet ([a-z0-9.-]+): a name with an unknown
        # facet parses and the facet is preserved on rename. This is the CLOSED-vs-OPEN divergence
        # (OQ-03); the golden net pins that this rename currently SUCCEEDS.
        self._check(
            "20260823-myset-01-abc123-old.customfacet.md",
            "specs",
            {"new_slug": "new"},
            ("20260823-myset-01-abc123-new.customfacet.md", None),
        )

    def test_legacy_timestamp(self) -> None:
        self._check(
            "20260101-1200-01-old.md",
            "plans",
            {"new_slug": "new"},
            ("20260101-1200-01-new.md", None),
        )

    def test_walkthrough_dated_suffix(self) -> None:
        self._check(
            "20260101-my-topic-walkthrough.md",
            "walkthroughs",
            {"new_slug": "renamed"},
            ("20260101-renamed-walkthrough.md", None),
        )

    def test_walkthrough_bare_suffix(self) -> None:
        self._check(
            "some-bare-walkthrough.md",
            "walkthroughs",
            {"new_slug": "renamed"},
            ("renamed-walkthrough.md", None),
        )

    def test_dated_slug_facet(self) -> None:
        self._check(
            "20260101-a-dated-slug.spec.md",
            "specs",
            {"new_slug": "renamed"},
            ("20260101-renamed.spec.md", None),
        )

    def test_dated_slug_bare(self) -> None:
        self._check(
            "20260101-a-dated-slug.md",
            "specs",
            {"new_slug": "renamed"},
            ("20260101-renamed.md", None),
        )

    def test_no_mutation_arg_is_error(self) -> None:
        new, err = AR.compute_target_name("20260101-a-dated-slug.md", "specs")
        self.assertIsNone(new)
        self.assertIsNotNone(err)


# --------------------------------------------------------------------------------------
# PARSE / VALIDATE golden values
# --------------------------------------------------------------------------------------

# Names exercised by the validators, with their CURRENT observed classification.
_CLUSTERED_FACETED = "20260823-myset-01-abc123-my-slug.ipd.md"
_CLUSTERED_BARE = "20260823-myset-01-abc123-my-slug.md"
_CLUSTERED_WRONGFACET = "20260823-myset-01-abc123-my-slug.spec.md"
_CLUSTERED_UNKNOWNFACET = "20260823-myset-01-abc123-my-slug.customfacet.md"
_LEGACY_TS = "20260101-1200-01-legacy-slug.md"
_WALKTHROUGH_SUFFIX = "20260101-my-topic-walkthrough.md"


class NormalizerConformanceGoldenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.npn = _load_normalizer()

    def test_is_conformant_ipd(self) -> None:
        self.assertTrue(self.npn.is_conformant(_CLUSTERED_FACETED))
        self.assertTrue(self.npn.is_conformant(_CLUSTERED_BARE))
        # A plan-typed check on a spec-faceted name is nonconformant (facet must match type).
        self.assertFalse(self.npn.is_conformant(_CLUSTERED_WRONGFACET))
        # An unknown facet is not a recognized facet -> nonconformant as a clustered name.
        self.assertFalse(self.npn.is_conformant(_CLUSTERED_UNKNOWNFACET))
        # The legacy YYYYMMDD-HHMM-NN form is accepted.
        self.assertTrue(self.npn.is_conformant(_LEGACY_TS))
        self.assertFalse(self.npn.is_conformant(_WALKTHROUGH_SUFFIX))

    def test_is_conformant_walkthrough_facet(self) -> None:
        # The walkthrough facet form is conformant when checked as a walkthrough.
        self.assertTrue(
            self.npn.is_conformant(
                "20260823-myset-01-abc123-my-slug.walkthrough.md",
                expected_type="walkthrough",
            )
        )

    def test_parse_name_components(self) -> None:
        # parse_name drops a recognized facet and reports the clustered core as a single slug (the
        # normalizer's HHMM-NN grammar does not decompose the clustered id6 form). Pin that.
        p = self.npn.parse_name(_CLUSTERED_FACETED)
        self.assertEqual(
            (p.date, p.time, p.nn, p.slug, p.conformant),
            ("20260823", None, None, "myset-01-abc123-my-slug", False),
        )
        pb = self.npn.parse_name(_CLUSTERED_BARE)
        self.assertEqual(pb, p)  # faceted and bare parse identically
        pl = self.npn.parse_name(_LEGACY_TS)
        self.assertEqual(
            (pl.date, pl.time, pl.nn, pl.slug, pl.conformant),
            ("20260101", "1200", "01", "legacy-slug", True),
        )

    def test_parse_name_unknown_facet_keeps_facet_in_slug(self) -> None:
        # An unknown facet is NOT stripped, so it survives into the parsed slug.
        p = self.npn.parse_name(_CLUSTERED_UNKNOWNFACET)
        self.assertEqual(p.slug, "myset-01-abc123-my-slug.customfacet")


class PlansClusteredReGoldenTests(unittest.TestCase):
    def test_faceted_and_bare_components(self) -> None:
        mf = R._CLUSTERED_RE.match(_CLUSTERED_FACETED)
        mb = R._CLUSTERED_RE.match(_CLUSTERED_BARE)
        self.assertIsNotNone(mf)
        self.assertIsNotNone(mb)
        self.assertEqual(
            mf.groupdict(),
            {
                "date": "20260823",
                "set": "myset",
                "nn": "01",
                "id6": "abc123",
                "slug": "my-slug",
                "type": "ipd",
            },
        )
        self.assertEqual(mb.group("type"), None)

    def test_wrong_facet_still_parses_with_that_type(self) -> None:
        m = R._CLUSTERED_RE.match(_CLUSTERED_WRONGFACET)
        self.assertIsNotNone(m)
        self.assertEqual(m.group("type"), "spec")

    def test_unknown_facet_rejected_closed_enum(self) -> None:
        # plans_refs uses a CLOSED facet enum: an unknown facet does not match at all.
        self.assertIsNone(R._CLUSTERED_RE.match(_CLUSTERED_UNKNOWNFACET))

    def test_walkthrough_suffix_not_clustered(self) -> None:
        self.assertIsNone(R._CLUSTERED_RE.match(_WALKTHROUGH_SUFFIX))


class ResearchParseGoldenTests(unittest.TestCase):
    def test_with_model(self) -> None:
        parsed, err = RC.parse_name(
            "20260823-myset-02-abc123-my-slug.gpt56.findings.md"
        )
        self.assertIsNone(err)
        self.assertEqual(
            parsed,
            RC.ResearchName(
                date="20260823",
                set_id="myset",
                order="02",
                id6="abc123",
                slug="my-slug",
                model="gpt56",
                kind="findings",
            ),
        )

    def test_without_model(self) -> None:
        parsed, err = RC.parse_name("20260823-myset-02-abc123-my-slug.findings.md")
        self.assertIsNone(err)
        self.assertEqual(parsed.model, None)
        self.assertEqual(parsed.kind, "findings")

    def test_unknown_kind_errors(self) -> None:
        parsed, err = RC.parse_name("20260823-myset-02-abc123-my-slug.unknownkind.md")
        self.assertIsNone(parsed)
        self.assertIn("unknown kind", err.message)

    def test_unknown_model_errors(self) -> None:
        parsed, err = RC.parse_name(
            "20260823-myset-02-abc123-my-slug.badmodel.findings.md"
        )
        self.assertIsNone(parsed)
        self.assertIn("unknown model", err.message)

    def test_missing_kind_errors(self) -> None:
        parsed, err = RC.parse_name("20260101-1200-01-legacy.md")
        self.assertIsNone(parsed)
        self.assertIsNotNone(err)


class DetectArtifactTypeGoldenTests(unittest.TestCase):
    def _detect(self, name):
        return SS.detect_artifact_type(Path(name), Path("."))

    def test_facet_detection(self) -> None:
        self.assertEqual(self._detect(_CLUSTERED_FACETED), "plans")
        self.assertEqual(self._detect(_CLUSTERED_WRONGFACET), "specs")
        self.assertEqual(
            self._detect("20260823-x-01-abc123-s.walkthrough.md"), "walkthroughs"
        )
        self.assertEqual(self._detect("20260823-x-01-abc123-s.release.md"), "releases")
        self.assertEqual(self._detect("20260823-x-01-abc123-s.backlog.md"), "backlog")
        self.assertEqual(self._detect("20260823-x-01-abc123-s.roadmap.md"), "roadmaps")
        self.assertEqual(self._detect("20260823-x-01-abc123-s.prompt.md"), "prompts")

    def test_bare_and_unknown_facet_not_detected_by_name(self) -> None:
        self.assertIsNone(self._detect(_CLUSTERED_BARE))
        self.assertIsNone(self._detect(_CLUSTERED_UNKNOWNFACET))


if __name__ == "__main__":
    unittest.main()
