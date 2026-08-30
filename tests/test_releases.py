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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class ReleaseQueryPrimitiveTests(unittest.TestCase):
    """IPD w0ln4q E-01 / V-01: the `aw releases` query primitives.

    Uses a controlled temp repo (never the live tree) so the expected counts and blocker sets are
    stable. The key invariant asserted here is the REUSE rule: `get_release_blockers` must return
    exactly the set `attention.release_blockers` returns, proving no second `- Blocks-Release:` scan
    was written that could drift from the board.
    """

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.rec = self.root / ".aw" / "records"
        # Two release records: ONE planned (so `next` resolves) and one shipped.
        _write(
            self.rec / "releases" / "20260101-aaaaaa-01-aaaaaa-2-0-0.release.md",
            "# Release: 2.0.0\n\n- Id: aaaaaa\n- Status: planned\n- Version: 2.0.0\n"
            "- Summary: the planned one\n\n## Workflow history\n\n- 2026-01-01 created (aw releases): x\n",
        )
        _write(
            self.rec / "releases" / "20251201-bbbbbb-01-bbbbbb-1-0-0.release.md",
            "# Release: 1.0.0\n\n- Id: bbbbbb\n- Status: shipped\n- Version: 1.0.0\n"
            "- Summary: the shipped one\n",
        )
        # Items that GATE the planned release, across three trees + one that gates nothing.
        _write(
            self.rec / "backlog" / "open" / "20260102-g-01-gate01-blocker.backlog.md",
            "- Id: gate01\n- Status: open\n- Set: g\n- Priority: high\n- Kind: bug\n"
            "- Summary: gates the release\n- Blocks-Release: next\n",
        )
        _write(
            self.rec / "backlog" / "open" / "20260102-g-01-gate02-byid.backlog.md",
            "- Id: gate02\n- Status: open\n- Set: g\n- Priority: low\n- Kind: chore\n"
            "- Summary: gates by id6\n- Blocks-Release: aaaaaa\n",
        )
        _write(
            self.rec / "backlog" / "open" / "20260102-g-01-free01-nogate.backlog.md",
            "- Id: free01\n- Status: open\n- Set: g\n- Priority: low\n- Kind: chore\n"
            "- Summary: gates nothing\n",
        )
        _write(
            self.rec / "plans" / "pending" / "20260102-g-01-gate03-a-plan.ipd.md",
            "# IPD: p\n\n- Id: gate03\n- Status: approved\n- Set: g (g)\n"
            "- Blocks-Release: next\n\n## Goal\n\nx\n",
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_list_releases_matches_on_disk_count(self) -> None:
        got = releases.list_releases(self.root)
        on_disk = sorted((self.rec / "releases").glob("*.release.md"))
        self.assertEqual(len(got), len(on_disk))
        self.assertEqual(len(got), 2)
        self.assertEqual(sorted(r.path for r in got), on_disk)
        by_id = {r.id6: r for r in got}
        self.assertEqual(set(by_id), {"aaaaaa", "bbbbbb"})
        self.assertEqual(by_id["aaaaaa"].version, "2.0.0")
        self.assertEqual(by_id["aaaaaa"].status, "planned")
        self.assertEqual(by_id["aaaaaa"].summary, "the planned one")
        self.assertEqual(len(by_id["aaaaaa"].history), 1)

    def test_list_releases_empty_tree(self) -> None:
        empty = Path(self._tmp.name) / "nowhere"
        self.assertEqual(releases.list_releases(empty), [])

    def test_get_release_by_id6(self) -> None:
        rec = releases.get_release(self.root, "bbbbbb")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.id6, "bbbbbb")
        self.assertEqual(rec.version, "1.0.0")

    def test_get_release_by_version(self) -> None:
        rec = releases.get_release(self.root, "2.0.0")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.id6, "aaaaaa")

    def test_get_release_by_filename(self) -> None:
        name = "20251201-bbbbbb-01-bbbbbb-1-0-0.release.md"
        rec = releases.get_release(self.root, name)
        self.assertIsNotNone(rec)
        self.assertEqual(rec.id6, "bbbbbb")
        # the stem (without the .release.md facet) resolves too
        stem = name[: -len(".release.md")]
        self.assertEqual(releases.get_release(self.root, stem).id6, "bbbbbb")

    def test_get_release_by_next_sentinel(self) -> None:
        rec = releases.get_release(self.root, "next")
        self.assertIsNotNone(rec)
        self.assertEqual(rec.id6, "aaaaaa")
        # `next` DELEGATES to resolve_release: same path, single source of truth.
        self.assertEqual(rec.path, releases.resolve_release(self.root, "next"))

    def test_get_release_unknown_selector_is_none(self) -> None:
        self.assertIsNone(releases.get_release(self.root, "nosuch"))
        self.assertIsNone(releases.get_release(self.root, ""))
        self.assertIsNone(releases.get_release(self.root, "zzzzzz"))

    def test_get_release_blockers_equals_attention_release_blockers(self) -> None:
        """THE reuse assertion: set equality with the existing attention authority."""
        from agent_workflows import attention

        items, _drift = attention.scan(self.root)
        expected = {it.path for it in attention.release_blockers(items, self.root)}
        got = {b["path"] for b in releases.get_release_blockers(self.root, "next")}
        self.assertEqual(
            got,
            expected,
            "get_release_blockers must return the SAME set as attention.release_blockers "
            "(no second Blocks-Release scan)",
        )
        # And the ids are the real gating items, not the free one.
        got_ids = {b["id"] for b in releases.get_release_blockers(self.root, "next")}
        self.assertEqual(got_ids, {"gate01", "gate02", "gate03"})
        self.assertNotIn("free01", got_ids)

    def test_get_release_blockers_reuse_is_wired_in_source(self) -> None:
        # A source-level guard so a future refactor cannot quietly reintroduce a second scan.
        src = Path(releases.__file__).read_text(encoding="utf-8")
        self.assertIn("_attention.release_blockers(items, repo_root)", src)
        self.assertIn("from agent_workflows import attention as _attention", src)

    def test_get_release_blockers_scoped_to_the_named_release(self) -> None:
        # The SHIPPED release is gated by nobody: an item declaring `next`/`aaaaaa` must not leak in.
        self.assertEqual(releases.get_release_blockers(self.root, "bbbbbb"), [])
        # An unresolvable selector yields no blockers (not an exception).
        self.assertEqual(releases.get_release_blockers(self.root, "nosuch"), [])

    def test_get_release_blockers_carries_render_fields(self) -> None:
        blockers = releases.get_release_blockers(self.root, "aaaaaa")
        self.assertTrue(blockers)
        for b in blockers:
            for key in (
                "id",
                "path",
                "tree",
                "native_status",
                "attention_class",
                "priority",
                "blocks_release",
            ):
                self.assertIn(key, b)
        by_id = {b["id"]: b for b in blockers}
        self.assertEqual(by_id["gate01"]["tree"], "backlog")
        self.assertEqual(by_id["gate01"]["blocks_release"], "next")
        self.assertEqual(by_id["gate02"]["blocks_release"], "aaaaaa")
        self.assertEqual(by_id["gate03"]["tree"], "plans")

    def test_plan_release_previews_exactly_what_create_writes(self) -> None:
        # `run_new`'s preview uses plan_release; create_release is plan_release + the write, so the
        # previewed bytes ARE the written bytes (no second renderer that could drift). Each call mints
        # a FRESH id6, so the comparison normalizes the id6 out and asserts everything else matches.
        empty = Path(self._tmp.name) / "fresh"
        (empty / ".aw" / "records" / "releases").mkdir(parents=True)
        path, body = releases.plan_release(empty, "3.0.0", "preview probe")
        self.assertFalse(path.exists(), "plan_release must not write")
        self.assertEqual(list((empty / ".aw" / "records" / "releases").iterdir()), [])
        planned_id = releases.parse_release(path, body).id6
        self.assertIsNotNone(planned_id)

        written = releases.create_release(empty, "3.0.0", "preview probe")
        written_text = written.read_text(encoding="utf-8")
        written_id = releases.parse_release(written, written_text).id6
        self.assertIsNotNone(written_id)
        self.assertEqual(
            written_text.replace(written_id, "ID6"),
            body.replace(planned_id, "ID6"),
            "create_release must write exactly the bytes plan_release previewed",
        )
        self.assertTrue(written.name.endswith(".release.md"))
        self.assertEqual(
            written.name.replace(written_id, "ID6"),
            path.name.replace(planned_id, "ID6"),
        )

    def test_parse_release_reads_prose_summary_section(self) -> None:
        # The live 2.0.0 record uses a `## Summary` section, not a `- Summary:` bullet; both parse.
        p = self.rec / "releases" / "20260103-cccccc-01-cccccc-9-9-9.release.md"
        _write(
            p,
            "# Release: 9.9.9\n\n- Id: cccccc\n- Status: blocked\n- Version: 9.9.9\n\n"
            "## Summary\n\nprose summary line one\nline two\n\n## Blockers\n\nignored\n",
        )
        rec = releases.parse_release(p, p.read_text(encoding="utf-8"))
        self.assertEqual(rec.id6, "cccccc")
        self.assertEqual(rec.status, "blocked")
        self.assertEqual(rec.summary, "prose summary line one line two")

    def test_parse_release_tolerates_a_malformed_record(self) -> None:
        p = self.rec / "releases" / "20260104-dddddd-01-dddddd-bad.release.md"
        _write(p, "# Release: nothing\n\nno front matter at all\n")
        rec = releases.parse_release(p, p.read_text(encoding="utf-8"))
        self.assertIsNone(rec.id6)
        self.assertIsNone(rec.status)
        self.assertIsNone(rec.version)
        # It still LISTS (validation is `aw check releases`, not the reader's job).
        self.assertIn(p, [r.path for r in releases.list_releases(self.root)])


if __name__ == "__main__":
    unittest.main()
