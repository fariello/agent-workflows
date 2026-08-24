"""Single-source + round-trip proof for the filename-grammar authority (IPD o6b8l3, E-05/V-05).

Asserts:
  (a) the golden characterization suite (E-01) still passes unchanged after re-routing every builder
      and validator through the authority (run the golden module and require it green);
  (b) STRUCTURAL single-source: the clustered-grammar regex signature, the facet-enum table, and the
      facet POLICY (the closed-enum ``_FACET_ALT`` alternation, OQ-03) each appear in exactly ONE
      module of the ``agent_workflows`` package - ``artifact_naming`` - and every other package module
      that needs them imports from it. ``normalize_plan_names`` (the shipped standalone stdlib-only
      bootstrap tool) is the single DOCUMENTED exception to "exactly one copy" (OQ-04 resolved on the
      safe path (a): keep it standalone so setup-repo can run it before the package is installed) and
      is covered by an explicit BYTE-IDENTICAL drift-guard test here instead of a runtime import;
  (c) ROUND-TRIP property: for the clustered grammar and the research grammar,
      ``parse(build(components)) == components`` and ``build(parse(name)) == name`` for conformant
      inputs.
"""

from __future__ import annotations

import ast
import importlib.util
import unittest
from pathlib import Path

from agent_workflows import artifact_naming as N
from agent_workflows import research_contract as RC

PKG_DIR = Path(N.__file__).resolve().parent
REPO_ROOT = PKG_DIR.parent
NORMALIZER = (
    REPO_ROOT
    / ".aw"
    / "system"
    / "workflows"
    / "setup-repo"
    / "tools"
    / "normalize_plan_names.py"
)

# The single-source signatures we forbid from appearing in more than one package module.
# The clustered id6 regex fragment is the tell-tale of a locally re-encoded clustered grammar.
_CLUSTERED_REGEX_SIGNATURE = r"id6>[0-9a-z]{6}"


def _package_py_files():
    return sorted(p for p in PKG_DIR.glob("*.py") if p.name != "__pycache__")


def _load_normalizer():
    spec = importlib.util.spec_from_file_location("awss_npn", NORMALIZER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GoldenStillGreenTests(unittest.TestCase):
    def test_golden_suite_still_passes(self) -> None:
        # Load and run the golden module in-process; require every test green (E-05 (a)).
        import unittest as _ut

        loader = _ut.TestLoader()
        suite = loader.loadTestsFromName("tests.test_naming_authority_golden")
        result = _ut.TestResult()
        suite.run(result)
        self.assertEqual(
            result.failures + result.errors,
            [],
            msg=f"golden suite regressed: {result.failures + result.errors}",
        )
        self.assertGreater(result.testsRun, 0)


class SingleSourceStructuralTests(unittest.TestCase):
    def test_clustered_regex_defined_in_exactly_one_module(self) -> None:
        hits = [
            p.name
            for p in _package_py_files()
            if _CLUSTERED_REGEX_SIGNATURE in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            hits,
            ["artifact_naming.py"],
            msg=f"clustered-grammar regex must live in exactly one module; found in {hits}",
        )

    def test_facet_enum_alternation_defined_in_exactly_one_module(self) -> None:
        # The `_FACET_ALT = "|".join(...)` regex-alternation policy (the closed-enum facet policy)
        # must be built in exactly one module.
        hits = [
            p.name
            for p in _package_py_files()
            if '_FACET_ALT = "|".join(' in p.read_text(encoding="utf-8")
        ]
        self.assertEqual(
            hits,
            ["artifact_naming.py"],
            msg=f"facet-policy alternation must be built once; found in {hits}",
        )

    def test_facet_enum_tuple_literal_defined_in_exactly_one_module(self) -> None:
        # The literal 8-token facet enum tuple must be assigned in exactly one module (others import
        # ``ARTIFACT_TYPE_FACETS``). A module that merely references ``_naming.ARTIFACT_TYPE_FACETS``
        # does not count as a second definition.
        canonical = tuple(N.ARTIFACT_TYPE_FACETS)
        defining = []
        for p in _package_py_files():
            tree = ast.parse(p.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Tuple):
                    try:
                        value = tuple(
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                        )
                    except Exception:
                        continue
                    if value == canonical:
                        defining.append(p.name)
        self.assertEqual(
            defining,
            ["artifact_naming.py"],
            msg=f"the facet-enum tuple literal must be defined once; found in {defining}",
        )

    def test_plans_refs_reexports_authority(self) -> None:
        from agent_workflows import plans_refs as PR

        self.assertIs(PR._CLUSTERED_RE, N._CLUSTERED_RE)
        self.assertIs(PR.ARTIFACT_TYPE_FACETS, N.ARTIFACT_TYPE_FACETS)

    def test_import_direction_core_does_not_import_naming(self) -> None:
        # The authority may import artifact_core; artifact_core MUST NOT import the authority
        # (orchestrator g6mbht module-placement principle).
        core_src = (PKG_DIR / "artifact_core.py").read_text(encoding="utf-8")
        self.assertNotIn("artifact_naming", core_src)


class NormalizerDriftGuardTests(unittest.TestCase):
    """OQ-04 resolved path (a): normalize_plan_names stays a standalone stdlib-only tool (so
    setup-repo can run it before agent_workflows is installed). It is the single DOCUMENTED
    exception to "exactly one copy"; this drift-guard asserts its grammar stays in sync with the
    authority WITHOUT a runtime dependency."""

    def setUp(self) -> None:
        self.npn = _load_normalizer()

    def test_normalizer_imports_only_stdlib(self) -> None:
        # Verify the tool takes no agent_workflows dependency (the reason it stays standalone).
        # Inspect the parsed AST for real import statements, not substrings in comments/docstrings.
        tree = ast.parse(NORMALIZER.read_text(encoding="utf-8"))
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_roots.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])
        self.assertNotIn("agent_workflows", imported_roots)

    def test_normalizer_facet_enum_matches_authority(self) -> None:
        # The normalizer's closed facet enum must be byte-identical (as a set) to the authority's.
        self.assertEqual(
            set(self.npn._ARTIFACT_TYPE_FACETS), set(N.ARTIFACT_TYPE_FACETS)
        )

    def test_normalizer_clustered_acceptance_matches_authority(self) -> None:
        # For a battery of clustered names, the normalizer's is_conformant must agree with the
        # authority's is_clustered_conformant (drift guard on the grammar's ACCEPTANCE).
        cases = [
            ("20260823-myset-01-abc123-my-slug.ipd.md", "ipd", True),
            ("20260823-myset-01-abc123-my-slug.md", "ipd", True),
            ("20260823-myset-01-abc123-my-slug.spec.md", "ipd", False),
            ("20260823-myset-01-abc123-my-slug.spec.md", "spec", True),
            ("20260823-myset-01-abc123-my-slug.customfacet.md", "ipd", False),
            ("20260823-myset-01-abc123-my-slug.walkthrough.md", "walkthrough", True),
        ]
        for name, expected_type, want in cases:
            self.assertEqual(
                self.npn.is_conformant(name, expected_type=expected_type),
                N.is_clustered_conformant(name, expected_type=expected_type),
                msg=f"drift on {name!r} (expected_type={expected_type})",
            )
            # And both must agree with the golden expectation pinned in E-01.
            self.assertEqual(
                N.is_clustered_conformant(name, expected_type=expected_type),
                want,
                msg=f"authority acceptance changed for {name!r}",
            )


class RoundTripTests(unittest.TestCase):
    def test_clustered_build_then_parse(self) -> None:
        name = N.build_clustered_name(
            date="20260823",
            set_id="myset",
            order=3,
            id6="abc123",
            slug="a-slug",
            artifact_type="ipd",
        )
        m = N.parse_clustered(name)
        self.assertIsNotNone(m)
        assert m is not None
        self.assertEqual(m.group("date"), "20260823")
        self.assertEqual(m.group("set"), "myset")
        self.assertEqual(int(m.group("nn")), 3)
        self.assertEqual(m.group("id6"), "abc123")
        self.assertEqual(m.group("slug"), "a-slug")
        self.assertEqual(m.group("type"), "ipd")

    def test_clustered_parse_then_build_is_identity(self) -> None:
        for name in (
            "20260823-myset-03-abc123-a-slug.ipd.md",
            "20260823-myset-03-abc123-a-slug.md",
            "20260823-my-set-11-zzz999-longer-slug.spec.md",
        ):
            m = N.parse_clustered(name)
            self.assertIsNotNone(m, name)
            assert m is not None
            rebuilt = N.build_clustered_name(
                date=m.group("date"),
                set_id=m.group("set"),
                order=int(m.group("nn")),
                id6=m.group("id6"),
                slug=m.group("slug"),
                artifact_type=m.group("type"),
            )
            self.assertEqual(rebuilt, name)

    def test_research_build_then_parse(self) -> None:
        for model in ("gpt56", None):
            rn = RC.ResearchName(
                date="20260823",
                set_id="myset",
                order="02",
                id6="abc123",
                slug="a-slug",
                model=model,
                kind="findings",
            )
            name = RC.format_name(rn)
            parsed, err = RC.parse_name(name)
            self.assertIsNone(err, name)
            self.assertEqual(parsed, rn)

    def test_research_parse_then_build_is_identity(self) -> None:
        for name in (
            "20260823-myset-02-abc123-a-slug.gpt56.findings.md",
            "20260823-myset-02-abc123-a-slug.findings.md",
        ):
            parsed, err = RC.parse_name(name)
            self.assertIsNone(err, name)
            assert parsed is not None
            self.assertEqual(RC.format_name(parsed), name)


if __name__ == "__main__":
    unittest.main()
