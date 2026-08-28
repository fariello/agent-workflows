"""Tests for awrelease Order 01: the releases record class + create/validate."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine as _engine
from agent_workflows import releases
from agent_workflows.record_producers import RecordClass, resolve_record_path


class ReleasesClassTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_class_resolves(self) -> None:
        self.assertEqual(RecordClass.RELEASES.value, "releases")
        # The class is registered: resolve_record_path returns a path whose subpath is `releases`
        # (the concrete root depends on the backend; for a bare repo it is the home-backend path).
        p = resolve_record_path("releases", target_repo=str(self.root))
        self.assertEqual(Path(p).name, "releases")
        self.assertIn("records", str(p))

    def test_facet_recognized(self) -> None:
        # the normalizer accepts a *.release.md clustered name as conformant for expected_type=release
        import importlib.util

        root = _engine.resolve_source_root(None)
        spec = importlib.util.spec_from_file_location(
            "npn_rel", root / "setup-repo" / "tools" / "normalize_plan_names.py"
        )
        npn = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(npn)
        self.assertTrue(
            npn.is_conformant(
                "20260818-r1a2b3-01-r1a2b3-first.release.md", expected_type="release"
            )
        )

    def test_create_and_validate(self) -> None:
        p = releases.create_release(self.root, "2.0.0", "first .aw/ release")
        self.assertTrue(p.name.endswith(".release.md"))
        text = p.read_text(encoding="utf-8")
        self.assertIn("- Status: planned", text)
        self.assertIn("- Version: 2.0.0", text)
        self.assertEqual(releases.validate_release(p, text), [])
        # a bad status is flagged
        bad = text.replace("- Status: planned", "- Status: bogus")
        drift = releases.validate_release(p, bad)
        self.assertTrue(any(d.rule == "release.status-invalid" for d in drift))

    def test_resolve_next(self) -> None:
        # zero planned -> None; exactly one planned -> that record; the created one is planned.
        self.assertIsNone(releases.resolve_release(self.root, "next"))
        p = releases.create_release(self.root, "2.0.0", "x")
        self.assertEqual(releases.resolve_release(self.root, "next"), p)

    def test_describe_planned_release(self) -> None:
        # None when no planned release; (id6, version) when exactly one.
        self.assertIsNone(releases.describe_planned_release(self.root))
        p = releases.create_release(self.root, "2.0.0", "x")
        desc = releases.describe_planned_release(self.root)
        self.assertIsNotNone(desc)
        id6, version = desc
        self.assertEqual(version, "2.0.0")
        # id6 is the release record's own Id
        import re as _re

        m = _re.search(r"(?m)^- Id:\s*([0-9a-z]{6})\s*$", p.read_text(encoding="utf-8"))
        self.assertEqual(id6, m.group(1))

    def test_load_active_release(self) -> None:
        # None when none planned; the ActiveRelease (id6/version/path) when exactly one.
        # This backs the `aw doctor` Release line (doctor calls load_active_release).
        self.assertIsNone(releases.load_active_release(self.root))
        p = releases.create_release(self.root, "2.0.0", "x")
        act = releases.load_active_release(self.root)
        self.assertIsNotNone(act)
        self.assertEqual(act.version, "2.0.0")
        self.assertEqual(act.path, p)
        self.assertRegex(act.id6, r"^[0-9a-z]{6}$")

    def test_attention_release_reader(self) -> None:
        # Unit-level: the attention release reader maps a planned release to the `ready` class.
        from agent_workflows import attention

        p = releases.create_release(self.root, "2.0.0", "x")
        item, drift = attention._release_record(
            ".aw/records/releases/" + p.name, p, p.read_text(encoding="utf-8")
        )
        self.assertIsNotNone(item)
        self.assertEqual(item.tree, "releases")
        self.assertEqual(item.attention_class, "ready")  # planned -> ready
        self.assertEqual(drift, [])

    def test_deep_cleanup_includes_releases(self) -> None:
        self.assertIn(".aw/records/releases", _engine._DEEP_CLEANUP_ROOTS)


if __name__ == "__main__":
    unittest.main()
