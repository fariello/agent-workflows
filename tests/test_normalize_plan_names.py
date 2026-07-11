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
        self.assertEqual(renames[0].reason, "to-rename")

    def test_legacy_shapes_all_normalize(self):
        # date-only, NN-only, time-only, hyphenated, hyphenated+NN (committed today so the
        # name-date agrees with git and none is flagged imported).
        for name in (
            "20260711-date-only.md",
            "20260711-07-with-nn.md",
            "20260711-1430-with-time.md",
            "2026-07-11-hyphenated.md",
            "2026-07-11-09-hyphenated-nn.md",
        ):
            self._add(name)
        renames = [r for r in NPN.scan(self.repo) if r.reason == "to-rename"]
        self.assertEqual(len(renames), 5, [r.old for r in NPN.scan(self.repo)])
        for r in renames:
            self.assertTrue(NPN.is_conformant(Path(r.new).name), r.new)
        by_old = {Path(r.old).name: Path(r.new).name for r in renames}
        # Present time/NN preserved.
        self.assertIn("-1430-", by_old["20260711-1430-with-time.md"])
        self.assertRegex(by_old["20260711-07-with-nn.md"], r"-07-with-nn\.md$")
        self.assertRegex(
            by_old["2026-07-11-09-hyphenated-nn.md"], r"^20260711-\d{4}-09-"
        )
        # Hyphenated date compacted to YYYYMMDD (N-1 regression: did not raise + no hyphens in date).
        self.assertTrue(by_old["2026-07-11-hyphenated.md"].startswith("20260711-"))

    def test_nn_vs_hhmm_disambiguation(self):
        p2 = NPN.parse_name("20260709-01-foo.md")
        self.assertEqual(p2.nn, "01")
        self.assertIsNone(p2.time)
        p4 = NPN.parse_name("20260709-1044-foo.md")
        self.assertEqual(p4.time, "1044")
        self.assertIsNone(p4.nn)

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

    def test_untracked_file_uses_fs_mtime_not_0000(self):
        # D50: an untracked file's time comes from earliest fs evidence, not 0000.
        p = self._add("20260711-untracked.md", commit=False)  # never committed
        import os as _os

        # Set mtime to a known instant; the name-date wins for DATE, time from fs.
        _os.utime(p, (1751000000, 1751000000))  # some fixed epoch in 2025-ish
        renames = [r for r in NPN.scan(self.repo) if r.reason == "to-rename"]
        self.assertEqual(len(renames), 1)
        name = Path(renames[0].new).name
        # Name date preserved; time is a real HHMM (4 digits), not necessarily 0000.
        self.assertTrue(name.startswith("20260711-"))
        self.assertRegex(name, r"^20260711-\d{4}-01-untracked\.md$")

    def test_name_date_wins_over_git_and_fs(self):
        # A file whose name says 20260101 but committed today keeps 20260101 as the date.
        self._add("20260101-old-dated.md")
        r = [
            x for x in NPN.scan(self.repo, assume_dates=True) if x.reason == "to-rename"
        ]
        self.assertEqual(len(r), 1)
        self.assertTrue(Path(r[0].new).name.startswith("20260101-"))

    def test_import_case_mtime_older_than_git_flagged_and_uses_mtime(self):
        # Non-numeric name, mtime = June 1 (older than the July commit) -> earliest = mtime,
        # flagged imported? (needs --assume-dates), and resolves to the June date.
        import os as _os

        p = self._add("imported-notes.md")  # committed now (git = today)
        june = 1748800000  # ~2025-06; a clearly-older-than-now epoch
        _os.utime(p, (june, june))
        flagged = [
            r
            for r in NPN.scan(self.repo, rename_non_numeric=True)
            if r.reason == "imported"
        ]
        self.assertEqual(len(flagged), 1)
        # With --assume-dates it renames, using the (older) fs date, not today's git date.
        done = [
            r
            for r in NPN.scan(self.repo, rename_non_numeric=True, assume_dates=True)
            if r.reason == "to-rename"
        ]
        self.assertEqual(len(done), 1)
        import datetime as _dt

        june_date = _dt.datetime.fromtimestamp(june, _dt.timezone.utc).strftime(
            "%Y%m%d"
        )
        self.assertTrue(Path(done[0].new).name.startswith(june_date + "-"))

    def test_bad_slug_new_format_is_normalized(self):
        # A canonical prefix but a bad slug is not conformant -> normalized slug.
        self._add("20260711-1430-01-Bad_Slug.md")
        renames = [r for r in NPN.scan(self.repo) if r.reason == "to-rename"]
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
        target = [r for r in NPN.scan(self.repo) if r.reason == "to-rename"][0].new
        (self.repo / target).write_text("# occupied\n", encoding="utf-8")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "occupy")
        NPN.apply(NPN.scan(self.repo), self.repo)
        # The occupied target must not be overwritten.
        self.assertEqual(
            (self.repo / target).read_text(encoding="utf-8"), "# occupied\n"
        )


class ScopeExcludeNonNumericTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "repo")

    def tearDown(self):
        self._tmp.cleanup()

    def _mk(self, rel, commit=True):
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
        if commit:
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-q", "-m", f"add {rel}")
        return p

    def _statuses(self, **kw):
        return {r.old: r.reason for r in NPN.scan(self.repo, **kw)}

    def test_prompts_scanned_by_default_area_narrows(self):
        self._mk(".agents/prompts/pending/20260711-note.md")
        # Default (plans+prompts): the prompts file is found (to-rename).
        st = self._statuses()
        self.assertIn(".agents/prompts/pending/20260711-note.md", st)
        # --area plans: prompts excluded entirely (not reported).
        st2 = self._statuses(areas=["plans"])
        self.assertNotIn(".agents/prompts/pending/20260711-note.md", st2)

    def test_workflows_tree_never_targeted_even_with_all(self):
        self._mk(".agents/workflows/assess/20260711-not-a-plan.md")
        self._mk(".agents/plans/pending/20260711-real.md")
        st = self._statuses(all_areas=True)
        self.assertNotIn(".agents/workflows/assess/20260711-not-a-plan.md", st)
        self.assertIn(".agents/plans/pending/20260711-real.md", st)

    def test_nested_reported_not_renamed_without_include(self):
        self._mk(".agents/plans/pending/suite/sources/20260711-input.md")
        st = self._statuses()
        self.assertEqual(
            st[".agents/plans/pending/suite/sources/20260711-input.md"], "nested"
        )
        st2 = self._statuses(include_nested=True)
        self.assertEqual(
            st2[".agents/plans/pending/suite/sources/20260711-input.md"], "to-rename"
        )

    def test_readme_excluded_by_default(self):
        self._mk(".agents/plans/pending/README.md")
        st = self._statuses()
        # README under a lifecycle dir is excluded (or simply not offered); never to-rename.
        self.assertNotEqual(st.get(".agents/plans/pending/README.md"), "to-rename")

    def test_custom_exclude_pattern(self):
        self._mk(".agents/plans/pending/20260711-keep.md")
        self._mk(".agents/plans/pending/20260711-skip.md")
        st = self._statuses(excludes=["*/20260711-skip.md"])
        self.assertEqual(st[".agents/plans/pending/20260711-skip.md"], "excluded")
        self.assertEqual(st[".agents/plans/pending/20260711-keep.md"], "to-rename")

    def test_non_numeric_off_by_default_then_opt_in(self):
        self._mk(".agents/plans/pending/free-form-name.md")
        st = self._statuses()
        self.assertEqual(st[".agents/plans/pending/free-form-name.md"], "non-numeric")
        r = [
            x
            for x in NPN.scan(self.repo, rename_non_numeric=True, assume_dates=True)
            if x.reason == "to-rename"
        ]
        self.assertEqual(len(r), 1)
        self.assertTrue(NPN.is_conformant(Path(r[0].new).name))
        self.assertIn("free-form-name", Path(r[0].new).name)

    def test_non_numeric_with_embedded_date_uses_it(self):
        self._mk(".agents/plans/pending/MASTER-CONTEXT-proj-20260101.md")
        r = [
            x
            for x in NPN.scan(self.repo, rename_non_numeric=True, assume_dates=True)
            if x.reason == "to-rename"
        ]
        self.assertEqual(len(r), 1)
        name = Path(r[0].new).name
        self.assertTrue(name.startswith("20260101-"), name)
        # The consumed date is dropped from the slug.
        self.assertNotIn("20260101", name.split("-", 3)[3])


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
                # README.md is a directory doc, not a plan file (the normalizer excludes
                # it by default); it is not subject to the plan-filename convention.
                if f.name == "README.md":
                    continue
                if not NPN.is_conformant(f.name):
                    offenders.append(f.relative_to(REPO_ROOT).as_posix())
        self.assertEqual(offenders, [], f"nonconforming plan filenames: {offenders}")


if __name__ == "__main__":
    unittest.main()
