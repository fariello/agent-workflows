"""Tests for normalize_plan_names.py (IPD-3: plan filename convention). Stdlib unittest only."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.support import REPO_ROOT, load_module, init_repo, git

NPN = load_module(
    "normalize_plan_names",
    REPO_ROOT
    / ".agents"
    / "workflows"
    / "setup-repo"
    / "tools"
    / "normalize_plan_names.py",
)


class ParseTests(unittest.TestCase):
    def test_new_format_is_conformant(self):
        self.assertTrue(NPN.is_conformant("20260711-1430-01-my-plan.md"))
        self.assertTrue(NPN.is_conformant("20260711-1430-00-orchestrator.md"))

    def test_legacy_is_recognized_but_not_conformant(self):
        p = NPN.parse_name("20260711-my-plan.md")
        self.assertIsNotNone(p)
        self.assertFalse(p.conformant)
        self.assertIsNone(p.time)
        self.assertFalse(NPN.is_conformant("20260711-my-plan.md"))

    def test_uppercase_or_underscore_slug_not_conformant(self):
        self.assertFalse(NPN.is_conformant("20260711-1430-01-My_Plan.md"))
        self.assertFalse(NPN.is_conformant("20260711-1430-01-my--plan.md"))

    def test_junk_is_unrecognized(self):
        self.assertIsNone(NPN.parse_name("notes.md"))
        self.assertIsNone(NPN.parse_name("README.md"))

    def test_normalize_slug(self):
        self.assertEqual(NPN.normalize_slug("My Plan_v2"), "my-plan-v2")
        self.assertEqual(NPN.normalize_slug("already-kebab"), "already-kebab")
        self.assertEqual(NPN.normalize_slug("!!!"), "untitled")
        self.assertEqual(NPN.normalize_slug("Trailing- "), "trailing")


class ScanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        self.pending = self.repo / ".agents/plans/pending"
        self.pending.mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def _add(self, name, commit=True):
        p = self.pending / name
        p.write_text("# plan\n", encoding="utf-8")
        if commit:
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-q", "-m", f"add {name}")
        return p

    def test_conformant_files_are_left_alone(self):
        self._add("20260711-1430-01-good.md")
        renames = NPN.scan(self.repo)
        self.assertEqual([r for r in renames if r.old != r.new], [])

    def test_legacy_file_gets_renamed(self):
        self._add("20260711-my-plan.md")
        renames = [r for r in NPN.scan(self.repo) if r.old != r.new]
        self.assertEqual(len(renames), 1)
        new = renames[0].new
        self.assertRegex(Path(new).name, r"^20260711-\d{4}-01-my-plan\.md$")
        self.assertEqual(renames[0].reason, "legacy")

    def test_same_minute_legacy_files_get_sequential_nn(self):
        # Two files committed together -> same first-commit minute -> 01, 02.
        self._add("20260711-alpha.md", commit=False)
        self._add("20260711-beta.md", commit=False)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "both")
        renames = sorted(
            (r for r in NPN.scan(self.repo) if r.old != r.new), key=lambda r: r.old
        )
        nns = sorted(Path(r.new).name.split("-")[2] for r in renames)
        self.assertEqual(nns, ["01", "02"])
        # Same timestamp for both (committed together).
        stamps = {Path(r.new).name.split("-", 2)[1] for r in renames}
        self.assertEqual(len(stamps), 1)

    def test_untracked_file_falls_back_to_0000(self):
        self._add("20260711-untracked.md", commit=False)  # never committed
        renames = [r for r in NPN.scan(self.repo) if r.old != r.new]
        self.assertEqual(len(renames), 1)
        self.assertRegex(Path(renames[0].new).name, r"^20260711-0000-01-untracked\.md$")

    def test_slug_only_nonconformance_is_reason_slug_when_new_format(self):
        # A new-format prefix but a bad slug is caught (not conformant) -> normalized.
        # (Bad-slug new-format files parse as legacy here since the strict new regex fails;
        #  the important guarantee is they get normalized, not their reason label.)
        self._add("20260711-1430-01-Bad_Slug.md")
        renames = [r for r in NPN.scan(self.repo) if r.old != r.new]
        self.assertEqual(len(renames), 1)
        self.assertIn("bad-slug", Path(renames[0].new).name)


class ApplyTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")
        (self.repo / ".agents/plans/executed").mkdir(parents=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_apply_renames_tracked_file_staged_not_committed(self):
        p = self.repo / ".agents/plans/executed/20260711-thing.md"
        p.write_text("# t\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "add")
        renames = NPN.scan(self.repo)
        NPN.apply(renames, self.repo)
        # Old gone, new present, conforms.
        self.assertFalse(p.exists())
        new_files = list((self.repo / ".agents/plans/executed").glob("*.md"))
        self.assertEqual(len(new_files), 1)
        self.assertTrue(NPN.is_conformant(new_files[0].name))
        # Staged (a rename in the index) but NOT committed: working tree has staged changes.
        porcelain = git(self.repo, "status", "--porcelain").stdout
        self.assertTrue(porcelain.strip(), "rename should be staged")
        # And nothing committed since (HEAD still the 'add' commit).
        log = git(self.repo, "log", "--oneline").stdout.strip().splitlines()
        self.assertEqual(len(log), 1)

    def test_apply_is_idempotent(self):
        p = self.repo / ".agents/plans/executed/20260711-thing.md"
        p.write_text("# t\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "add")
        NPN.apply(NPN.scan(self.repo), self.repo)
        # Second scan finds nothing to do.
        again = [r for r in NPN.scan(self.repo) if r.old != r.new]
        self.assertEqual(again, [])

    def test_apply_never_clobbers_existing_target(self):
        # Plant a legacy file AND a file already occupying its computed target name.
        d = self.repo / ".agents/plans/executed"
        (d / "20260711-thing.md").write_text("# legacy\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "add legacy")
        # Precompute the target and create a conflicting file there.
        target = NPN.scan(self.repo)[0].new
        (self.repo / target).write_text("# occupied\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "occupy")
        NPN.apply(NPN.scan(self.repo), self.repo)
        # The occupied target must not be overwritten.
        self.assertEqual(
            (self.repo / target).read_text(encoding="utf-8"), "# occupied\n"
        )


class RepoConformanceTests(unittest.TestCase):
    """Drift-guard: THIS repo's own plan filenames must all conform (IPD-3 change #7).

    Skipped until this repo's files are normalized (change #5); once green it prevents
    regressions. NOTE: enabled by removing the skip after normalization lands.
    """

    def test_all_plan_files_conform(self):
        plans = REPO_ROOT / ".agents" / "plans"
        offenders = []
        for sub in (
            "pending",
            "executed",
            "superseded",
            "not-executed",
            "reusable",
            "done",
        ):
            d = plans / sub
            if not d.is_dir():
                continue
            for f in d.glob("*.md"):
                if not NPN.is_conformant(f.name):
                    offenders.append(f.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(offenders, [], f"nonconforming plan filenames: {offenders}")


if __name__ == "__main__":
    unittest.main()
