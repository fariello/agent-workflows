"""Tests for agent_workflows.manifest (IPD 20260723-1100-01, CP1).

Schema round-trip, atomic write, normalized-hash determinism, absent-manifest =
fresh-install, and the record/decline mutations. Stdlib unittest only.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_workflows import manifest as M


class NormalizationHashTests(unittest.TestCase):
    def test_hash_is_stable_across_line_endings_and_whitespace(self):
        a = "---\ndescription: x\nagent: build\n---\nRead and execute @x\n"
        b = "---\r\ndescription: DIFFERENT WORDING\r\nagent: build\r\n---\r\n  Read and execute @x  \r\n\r\n"
        # Same intent, different line endings / trailing whitespace / description wording.
        self.assertEqual(M.hash_content(a), M.hash_content(b))

    def test_hash_differs_on_real_body_change(self):
        a = "---\nagent: build\n---\nRead and execute @x\n"
        b = "---\nagent: build\n---\nRead and execute @y\n"
        self.assertNotEqual(M.hash_content(a), M.hash_content(b))

    def test_normalize_is_idempotent(self):
        raw = "  a \r\n\r\n description: drop me \n b \n"
        once = M.normalize_for_hash(raw)
        self.assertEqual(M.normalize_for_hash(once), once)
        self.assertNotIn("description:", once)

    def test_matches_the_engine_customization_normalization(self):
        # M13: the manifest normalization must be the SAME the engine uses for its drift
        # comparison, so a freshly written file matches its own recorded hash.
        from agent_workflows import engine as INS

        text = "---\ndescription: whatever\nagent: build\n---\nRead and execute @z\n"
        self.assertEqual(
            M.normalize_for_hash(text), INS.strip_description_and_normalize(text)
        )


class ManifestRoundTripTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_absent_manifest_is_fresh_install(self):
        man = M.load(self.base / "nope" / "managed-sections.json")
        self.assertEqual(man.files, {})
        self.assertEqual(man.installed_version, "")
        self.assertIsNone(man.recorded_hash("anything"))

    def test_corrupt_manifest_yields_empty_not_crash(self):
        p = self.base / "managed-sections.json"
        p.write_text("{ this is not json", encoding="utf-8")
        man = M.load(p)
        self.assertEqual(man.files, {})

    def test_round_trip_preserves_entries(self):
        man = M.Manifest(installed_version="1.3.0")
        man.record(
            ".opencode/commands/advise.md",
            "---\nagent: build\n---\nRead and execute @advise\n",
            kind="shim",
            host="opencode",
            logical_id="advise",
        )
        p = self.base / "sub" / "managed-sections.json"
        M.save(man, p)
        self.assertTrue(p.is_file())

        loaded = M.load(p)
        self.assertEqual(loaded.installed_version, "1.3.0")
        entry = loaded.get(".opencode/commands/advise.md")
        assert entry is not None
        self.assertEqual(entry.host, "opencode")
        self.assertEqual(entry.logical_id, "advise")
        self.assertEqual(entry.kind, "shim")
        self.assertEqual(
            entry.sha256, man.recorded_hash(".opencode/commands/advise.md")
        )

    def test_saved_json_is_sorted_and_has_reserved_sections_key(self):
        man = M.Manifest(installed_version="1.3.0")
        man.record("b.md", "b")
        man.record("a.md", "a")
        p = self.base / "managed-sections.json"
        M.save(man, p)
        raw = json.loads(p.read_text(encoding="utf-8"))
        self.assertIn("managed_sections", raw)  # reserved for IPD 02
        self.assertEqual(list(raw["files"].keys()), ["a.md", "b.md"])  # sorted
        self.assertEqual(raw["schema_version"], M.SCHEMA_VERSION)

    def test_save_is_atomic_no_temp_left_behind(self):
        man = M.Manifest()
        man.record("x.md", "x")
        p = self.base / "managed-sections.json"
        M.save(man, p)
        leftovers = [
            q.name
            for q in p.parent.iterdir()
            if q.name.startswith(".managed-sections.")
        ]
        self.assertEqual(leftovers, [], f"atomic temp file left behind: {leftovers}")


class MatchesRecordedTests(unittest.TestCase):
    def test_matches_recorded_true_for_our_unchanged_file(self):
        man = M.Manifest()
        content = "---\nagent: build\n---\nRead and execute @advise\n"
        man.record("advise.md", content)
        # Same intent, cosmetic differences only -> still OURS.
        reformatted = "---\r\ndescription: added later\r\nagent: build\r\n---\r\nRead and execute @advise\r\n"
        self.assertTrue(man.matches_recorded("advise.md", reformatted))

    def test_matches_recorded_false_for_user_edit(self):
        man = M.Manifest()
        man.record("advise.md", "---\nagent: build\n---\nRead and execute @advise\n")
        edited = "---\nagent: build\n---\nRead and execute @advise\nMY OWN NOTE\n"
        self.assertFalse(man.matches_recorded("advise.md", edited))

    def test_matches_recorded_false_when_unknown(self):
        man = M.Manifest()
        self.assertFalse(man.matches_recorded("never-seen.md", "anything"))


class DeclineTombstoneTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_decline_persists_across_save_load(self):
        man = M.Manifest()
        man.mark_declined(".claude/commands/advise.md", kind="shim", host="claude")
        p = self.base / "managed-sections.json"
        M.save(man, p)
        loaded = M.load(p)
        self.assertTrue(loaded.is_declined(".claude/commands/advise.md"))

    def test_record_preserves_existing_decline(self):
        man = M.Manifest()
        man.mark_declined("advise.md")
        # Recording a written hash should not silently un-decline.
        man.record("advise.md", "content")
        self.assertTrue(man.is_declined("advise.md"))


class ManifestPathResolverTests(unittest.TestCase):
    """E-04 / V-04 (manifest side): resolve_manifest_path prefers .aw/system, falls back to legacy."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_create_default_is_aw_system(self):
        # Neither location exists -> create-default is the .aw/system location.
        p = M.resolve_manifest_path(self.repo)
        self.assertEqual(p, self.repo / ".aw" / "system" / "managed-sections.json")

    def test_migrated_repo_resolves_aw_system(self):
        new = self.repo / ".aw" / "system" / "managed-sections.json"
        new.parent.mkdir(parents=True)
        new.write_text("{}", encoding="utf-8")
        self.assertEqual(M.resolve_manifest_path(self.repo), new)

    def test_unmigrated_repo_falls_back_to_legacy(self):
        legacy = self.repo / ".agents" / "agent-workflows" / "managed-sections.json"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("{}", encoding="utf-8")
        # Falsifiable: with only the legacy file present, the resolver MUST return it
        # (not the new create-default), else an un-migrated repo's manifest is invisible.
        self.assertEqual(M.resolve_manifest_path(self.repo), legacy)

    def test_new_wins_over_legacy_when_both_present(self):
        new = self.repo / ".aw" / "system" / "managed-sections.json"
        new.parent.mkdir(parents=True)
        new.write_text("{}", encoding="utf-8")
        legacy = self.repo / ".agents" / "agent-workflows" / "managed-sections.json"
        legacy.parent.mkdir(parents=True)
        legacy.write_text("{}", encoding="utf-8")
        self.assertEqual(M.resolve_manifest_path(self.repo), new)


if __name__ == "__main__":
    unittest.main()
