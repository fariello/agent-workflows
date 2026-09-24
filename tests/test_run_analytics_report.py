#!/usr/bin/env python3
"""runanalytics Order 07 (`6eq3oq`) E-01: transactional bundle publication.

HERMETICITY. Every fixture is built in a temporary directory in this file; nothing reads
`.aw/records/runs/`. That tree is gitignored, mutable, grows with every run, ABSENT from a fresh
checkout entirely, and its outcome files carry absolute paths the leak detector flags at `fail`. The
plan's own stop condition says so: "if a test needs the live corpus to pass, STOP and build a
fixture".

WHAT THIS SUITE IS FOR. The plan's original atomicity requirement was UNIMPLEMENTABLE as written, so
the first test here re-measures WHY (`os.replace` onto a non-empty directory raises errno 39) rather
than citing a review note. The rest assert the two implemented paths, the manifest-last ordering that
makes both honest, and the fault injection that proves an interruption never leaves a readable
half-bundle.
"""

from __future__ import annotations

import errno
import json
import os
import tempfile
import unittest
from pathlib import Path

from agent_workflows import run_analytics_report as rep
from agent_workflows.run_analytics_report import (
    MANIFEST_FILENAME,
    PublicationError,
    PUBLICATION_ORDER,
)


def _analytics_dir(root: Path) -> Path:
    """A reserved analytics directory inside a throwaway repo, via the real layout."""

    directory = root / ".aw" / "records" / "runs" / "analytics"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


class MeasuredPlatformBehaviourTests(unittest.TestCase):
    """The MEASUREMENTS the publication scheme rests on, re-derived rather than cited."""

    def test_os_replace_REFUSES_a_non_empty_directory(self):
        """errno 39. This is why the single-file atomic pattern does not generalize to a bundle."""

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            src, dst = base / "src", base / "dst"
            src.mkdir()
            dst.mkdir()
            (src / "a.txt").write_text("a", encoding="utf-8")
            (dst / "b.txt").write_text("b", encoding="utf-8")
            with self.assertRaises(OSError) as ctx:
                os.replace(src, dst)
            self.assertEqual(ctx.exception.errno, errno.ENOTEMPTY)
            print(
                f"MEASURED: os.replace onto a non-empty directory -> OSError errno="
                f"{ctx.exception.errno} ({ctx.exception.strerror})"
            )

    @unittest.skipUnless(hasattr(os, "symlink"), "platform has no os.symlink")
    def test_a_symlink_flip_IS_atomic(self):
        """The working alternative: os.symlink to a temp name, then os.replace onto the link."""

        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            v1, v2 = base / "v1", base / "v2"
            v1.mkdir()
            v2.mkdir()
            (v1 / "index.html").write_text("one", encoding="utf-8")
            (v2 / "index.html").write_text("two", encoding="utf-8")
            link = base / "latest"
            try:
                os.symlink(v1, link)
            except (OSError, NotImplementedError) as exc:  # pragma: no cover - Windows
                self.skipTest(f"symlink creation unavailable: {exc}")
            self.assertEqual((link / "index.html").read_text(encoding="utf-8"), "one")
            temp = base / "latest.tmp"
            os.symlink(v2, temp)
            os.replace(temp, link)
            self.assertEqual((link / "index.html").read_text(encoding="utf-8"), "two")
            print(
                "MEASURED: symlink flip via os.symlink + os.replace succeeded and is atomic"
            )


class PublicationPathTests(unittest.TestCase):
    """Both implemented paths, and the report of WHICH one ran."""

    def test_primary_path_publishes_versioned_and_flips_latest(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            result = rep.publish_bundle(
                directory,
                {"index.html": "<html></html>", "analysis.json": "{}"},
                generated_label="fixture",
                repo=td,
            )
            if not result.used_symlink:  # pragma: no cover - Windows without privilege
                self.skipTest(f"platform fell back: {result.fallback_reason}")
            version_dir = result.version_dir
            assert version_dir is not None  # the symlink path always sets it
            self.assertTrue((version_dir / MANIFEST_FILENAME).is_file())
            self.assertEqual(rep.verify_bundle(directory), [])

    def test_a_second_publish_leaves_the_first_bundle_intact(self):
        """The property the plan wanted and the original scheme could not deliver."""

        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            first = rep.publish_bundle(
                directory, {"index.html": "<html>1</html>"}, repo=td
            )
            if not first.used_symlink:  # pragma: no cover - Windows
                self.skipTest("platform has no symlink publication")
            second = rep.publish_bundle(
                directory, {"index.html": "<html>2</html>"}, repo=td
            )
            first_dir, second_dir = first.version_dir, second.version_dir
            assert first_dir is not None and second_dir is not None
            self.assertNotEqual(first_dir, second_dir)
            # The PREVIOUS bundle is still readable and still sound.
            self.assertEqual(
                (first_dir / "index.html").read_text(encoding="utf-8"),
                "<html>1</html>",
            )
            self.assertEqual(rep.verify_bundle(first_dir), [])
            self.assertEqual((directory / "latest").resolve().name, second_dir.name)

    def test_the_windows_no_symlink_FALLBACK_is_implemented_and_completes(self):
        """Simulate os.symlink raising, exactly as it does on Windows without privilege."""

        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            real_symlink = os.symlink

            def _refuse(*args, **kwargs):
                raise OSError(errno.EPERM, "symbolic link privilege not held")

            os.symlink = _refuse  # type: ignore[assignment]
            try:
                result = rep.publish_bundle(
                    directory,
                    {"index.html": "<html></html>", "analysis.json": "{}"},
                    generated_label="fixture",
                    repo=td,
                )
            finally:
                os.symlink = real_symlink  # type: ignore[assignment]
            self.assertFalse(result.used_symlink)
            self.assertIn("symlink publication unavailable", result.fallback_reason)
            # Publication still COMPLETED correctly, flat, with the manifest present.
            self.assertTrue((directory / "index.html").is_file())
            self.assertTrue((directory / MANIFEST_FILENAME).is_file())
            self.assertEqual(rep.verify_bundle(directory), [])
            print(f"MEASURED fallback engaged: {result.fallback_reason}")

    def test_explicit_flat_publication_is_also_available(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            result = rep.publish_bundle(
                directory, {"index.html": "<html></html>"}, repo=td, allow_symlink=False
            )
            self.assertFalse(result.used_symlink)
            self.assertEqual(rep.verify_bundle(directory), [])


class ManifestIsTheCompletenessSignalTests(unittest.TestCase):
    """The manifest is written LAST, on both paths, and a bundle without one is INCOMPLETE."""

    def test_manifest_is_ordered_last(self):
        names = [
            f.name
            for f in rep.bundle_files_from_mapping(
                {
                    MANIFEST_FILENAME: "{}",
                    "index.html": "<html></html>",
                    "analysis.json": "{}",
                    "zzz-extra.txt": "x",
                }
            )
        ]
        self.assertEqual(names[-1], MANIFEST_FILENAME)
        self.assertLess(names.index("analysis.json"), names.index("index.html"))
        self.assertEqual(PUBLICATION_ORDER[-1], MANIFEST_FILENAME)

    def test_a_directory_with_no_manifest_is_REFUSED_as_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            (directory / "index.html").write_text("<html></html>", encoding="utf-8")
            with self.assertRaises(PublicationError) as ctx:
                rep.read_manifest(directory)
            self.assertIn("completeness signal", str(ctx.exception))

    def test_INTERRUPTION_between_file_writes_leaves_no_readable_half_bundle(self):
        """FAULT INJECTION: die mid-publish; assert no reader can mistake the result for complete."""

        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            real_write = rep._write_file_durably
            written: list[str] = []

            def _die_after_first(path: Path, content: bytes) -> None:
                if written:
                    raise KeyboardInterrupt(
                        "simulated interruption between file writes"
                    )
                written.append(Path(path).name)
                real_write(Path(path), content)

            rep._write_file_durably = _die_after_first  # type: ignore[assignment]
            try:
                with self.assertRaises(KeyboardInterrupt):
                    rep.publish_bundle(
                        directory,
                        {
                            "index.html": "<html></html>",
                            "analysis.json": "{}",
                            "findings.md": "# findings",
                        },
                        repo=td,
                        allow_symlink=False,
                    )
            finally:
                rep._write_file_durably = real_write  # type: ignore[assignment]

            # A reader finds NO manifest, so it must treat the directory as incomplete.
            self.assertFalse((directory / MANIFEST_FILENAME).exists())
            with self.assertRaises(PublicationError):
                rep.read_manifest(directory)
            self.assertTrue(rep.verify_bundle(directory))
            print(
                "MEASURED fault injection: wrote "
                f"{written} then interrupted; no manifest present, bundle correctly unreadable"
            )

    def test_an_interrupted_republish_never_leaves_a_STALE_manifest(self):
        """The old manifest is removed FIRST, so it can never describe the new files wrongly."""

        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            rep.publish_bundle(
                directory,
                {"index.html": "<html>1</html>"},
                repo=td,
                allow_symlink=False,
            )
            self.assertEqual(rep.verify_bundle(directory), [])

            real_write = rep._write_file_durably
            calls = {"n": 0}

            def _die_on_second(path: Path, content: bytes) -> None:
                calls["n"] += 1
                if calls["n"] > 1:
                    raise KeyboardInterrupt("simulated interruption")
                real_write(Path(path), content)

            rep._write_file_durably = _die_on_second  # type: ignore[assignment]
            try:
                with self.assertRaises(KeyboardInterrupt):
                    rep.publish_bundle(
                        directory,
                        {"index.html": "<html>2</html>", "analysis.json": "{}"},
                        repo=td,
                        allow_symlink=False,
                    )
            finally:
                rep._write_file_durably = real_write  # type: ignore[assignment]
            self.assertFalse((directory / MANIFEST_FILENAME).exists())

    def test_manifest_carries_size_and_digest_for_every_file(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            result = rep.publish_bundle(
                directory,
                {"index.html": "<html></html>", "analysis.json": "{}"},
                repo=td,
                allow_symlink=False,
            )
            entries = {e["name"]: e for e in result.manifest["files"]}
            self.assertEqual(set(entries), {"index.html", "analysis.json"})
            for entry in entries.values():
                self.assertIsInstance(entry["size"], int)
                self.assertEqual(len(entry["sha256"]), 64)

    def test_verify_bundle_DETECTS_a_tampered_file(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            rep.publish_bundle(
                directory, {"index.html": "<html></html>"}, repo=td, allow_symlink=False
            )
            (directory / "index.html").write_text(
                "<html>tampered</html>", encoding="utf-8"
            )
            problems = rep.verify_bundle(directory)
            self.assertTrue(
                any("sha256" in p or "size" in p for p in problems), problems
            )


class RefusalTests(unittest.TestCase):
    """What publication REFUSES, each for a reason the plan names."""

    def test_publishing_OUTSIDE_the_analytics_namespace_is_refused(self):
        """Order 01 owns the resolver; a publish into the tracked tree is a refusal, not a mkdir."""

        with tempfile.TemporaryDirectory() as td:
            outside = Path(td) / "docs"
            outside.mkdir()
            with self.assertRaises(PublicationError) as ctx:
                rep.publish_bundle(outside, {"index.html": "<html></html>"}, repo=td)
            self.assertIn("analytics namespace", str(ctx.exception))

    def test_an_empty_bundle_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            with self.assertRaises(PublicationError):
                rep.publish_bundle(directory, {}, repo=td)

    def test_a_bundle_without_index_html_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            directory = _analytics_dir(Path(td))
            with self.assertRaises(PublicationError) as ctx:
                rep.publish_bundle(directory, {"analysis.json": "{}"}, repo=td)
            self.assertIn("index.html", str(ctx.exception))

    def test_a_nested_bundle_file_name_is_refused(self):
        with self.assertRaises(PublicationError):
            rep.BundleFile(name="nested/index.html", content=b"")

    def test_a_traversing_snapshot_label_is_refused(self):
        for label in ("..", "a/b", ""):
            with self.subTest(label=label):
                with self.assertRaises(PublicationError):
                    rep.resolve_snapshot_dir(label)


class ResolverTests(unittest.TestCase):
    """The path comes from Order 01's resolver, never from a composed literal."""

    def test_report_dir_is_order_01s_analytics_root(self):
        from agent_workflows.runner_shared import analytics_root

        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(rep.resolve_report_dir(td), analytics_root(td))

    def test_snapshot_dir_is_under_order_01s_snapshots_dir(self):
        from agent_workflows.runner_shared import analytics_snapshots_dir

        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(
                rep.resolve_snapshot_dir("20260913", td),
                analytics_snapshots_dir(td) / "20260913",
            )


class SnapshotRetentionTests(unittest.TestCase):
    """Retention prunes ONLY tool-owned snapshots."""

    def test_snapshots_are_pruned_to_the_keep_count(self):
        with tempfile.TemporaryDirectory() as td:
            _analytics_dir(Path(td))
            for label in ("v1", "v2", "v3"):
                rep.publish_snapshot(
                    label, {"index.html": f"<html>{label}</html>"}, repo=td
                )
            removed = rep.prune_snapshots(keep=2, repo=td)
            self.assertEqual(removed, ["v1"])
            remaining = sorted(
                p.name
                for p in (Path(td) / ".aw/records/runs/analytics/snapshots").iterdir()
                if p.is_dir()
            )
            self.assertEqual(remaining, ["v2", "v3"])

    def test_a_directory_we_did_not_write_is_NEVER_pruned(self):
        """A retention policy that deletes unrecognized content is data loss, not a feature."""

        with tempfile.TemporaryDirectory() as td:
            _analytics_dir(Path(td))
            for label in ("v1", "v2"):
                rep.publish_snapshot(label, {"index.html": "<html></html>"}, repo=td)
            foreign = Path(td) / ".aw/records/runs/analytics/snapshots" / "human-notes"
            foreign.mkdir(parents=True)
            (foreign / "notes.md").write_text("mine", encoding="utf-8")
            rep.prune_snapshots(keep=0, repo=td)
            self.assertTrue((foreign / "notes.md").is_file())

    def test_a_snapshot_manifest_records_immutability(self):
        with tempfile.TemporaryDirectory() as td:
            _analytics_dir(Path(td))
            result = rep.publish_snapshot(
                "20260913", {"index.html": "<html></html>"}, repo=td
            )
            self.assertTrue(result.manifest["immutable"])
            self.assertEqual(result.manifest["snapshot_label"], "20260913")


class DeterminismTests(unittest.TestCase):
    """Byte-identical output for identical input, so a diff means a real change."""

    def test_two_publications_of_identical_input_produce_identical_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            first = _analytics_dir(Path(td) / "a")
            second = _analytics_dir(Path(td) / "b")
            payload = {"index.html": "<html></html>", "analysis.json": '{"a":1}'}
            r1 = rep.publish_bundle(
                first,
                payload,
                generated_label="fixed",
                repo=str(Path(td) / "a"),
                allow_symlink=False,
            )
            r2 = rep.publish_bundle(
                second,
                payload,
                generated_label="fixed",
                repo=str(Path(td) / "b"),
                allow_symlink=False,
            )
            self.assertEqual(
                json.dumps(r1.manifest, sort_keys=True),
                json.dumps(r2.manifest, sort_keys=True),
            )
            self.assertEqual(
                (first / MANIFEST_FILENAME).read_bytes(),
                (second / MANIFEST_FILENAME).read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
