"""Regression tests for IPD awretrofit Order 08: the install scaffolder, README-stub placement, and
`uninstall --deep` are layout-aware and FLAT.

Release-review 20260817-153418 B02/B03 + the README-stub placement handed over from Order 07: a fresh
`.aw/`-layout install must scaffold the FLAT `.aw/records/*` tree (no `docs/`; prompt-library distinct
from prompts staging), drop README stubs there (not `.agents/*`), and `aw uninstall --deep` must reach
the flat roots - while a not-yet-migrated `.agents/workflows` repo still gets the legacy `.agents/*`.
"""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_workflows import engine


def _git_init(p: Path) -> None:
    for a in (
        ["init", "-q"],
        ["config", "user.email", "t@e.com"],
        ["config", "user.name", "T"],
    ):
        subprocess.run(["git", "-C", str(p), *a], check=True, capture_output=True)


class FreshInstallScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.tmp, ignore_errors=True)

    def _fresh_repo(self) -> Path:
        repo = Path(self.tmp) / "fresh"
        repo.mkdir()
        _git_init(repo)
        return repo

    def test_scaffold_is_flat_aw_records(self):
        """E-01/V-01: a fresh (aw-layout) install creates the FULL FLAT .aw/records/* set."""
        repo = self._fresh_repo()
        self.assertEqual(engine.resolve_target_layout(repo), "aw")
        engine.create_setup_artifacts(repo, use_git=False, dry_run=False)
        recs = repo / ".aw" / "records"
        # The full flat set incl. backlog + roadmaps + prompt-library (plan-review PR-001).
        for d in (
            "plans/pending",
            "prompts/pending",
            "prompt-library",
            "comms/shared/inbox",
            "backlog",
            "research/reference",
            "research/archive",
            "specs",
            "walkthroughs",
            "roadmaps",
        ):
            self.assertTrue((recs / d).is_dir(), f"missing .aw/records/{d}")
        # NO docs/ level (Order 07 flatten), NO legacy .agents/ scaffold.
        self.assertFalse((recs / "docs").exists(), "docs/ level must not exist")
        self.assertFalse(
            (repo / ".agents").exists(), "no legacy .agents/ on a fresh install"
        )

    def test_readme_stubs_land_flat(self):
        """E-02/V-02: README stubs are dropped into the flat .aw/records/* dirs, not .agents/*."""
        repo = self._fresh_repo()
        engine.install_into_repo(repo, _source(), yes=True, no_color=True)
        recs = repo / ".aw" / "records"
        self.assertTrue((recs / "README.md").is_file())
        self.assertTrue((recs / "plans" / "README.md").is_file())
        self.assertTrue((recs / "comms" / "README.md").is_file())
        # No obsolete top-level docs/ README, no legacy .agents/ stubs.
        self.assertFalse((recs / "docs" / "README.md").exists())
        self.assertFalse((repo / ".agents" / "README.md").exists())

    def test_legacy_repo_still_scaffolds_agents(self):
        """A not-yet-migrated .agents/workflows repo still gets the legacy .agents/* layout."""
        repo = Path(self.tmp) / "legacy"
        repo.mkdir()
        _git_init(repo)
        (repo / ".agents" / "workflows").mkdir(
            parents=True
        )  # -> resolve_target_layout == legacy
        self.assertEqual(engine.resolve_target_layout(repo), "legacy")
        engine.create_setup_artifacts(repo, use_git=False, dry_run=False)
        self.assertTrue((repo / ".agents" / "plans" / "pending").is_dir())
        self.assertTrue((repo / ".agents" / "docs" / "research").is_dir())
        self.assertFalse((repo / ".aw" / "records").exists())

    def test_dry_run_matches_real_paths(self):
        """The dry-run mirror reports the same FLAT paths the real writes create (no drift)."""
        repo = self._fresh_repo()
        dry = engine.create_setup_artifacts(repo, use_git=False, dry_run=True)
        self.assertTrue(any(".aw/records/backlog" in x for x in dry))
        self.assertTrue(any(".aw/records/prompt-library" in x for x in dry))
        self.assertFalse(any(".aw/records/docs/" in x for x in dry))
        self.assertFalse(any(".agents/" in x for x in dry))


class DeepCleanupFlatTests(unittest.TestCase):
    def test_deep_cleanup_targets_flat_records(self):
        """E-03/V-03: plan_deep_cleanup enumerates the flat .aw/records/* roots on a migrated repo."""
        tmp = tempfile.mkdtemp()
        try:
            repo = Path(tmp) / "r"
            repo.mkdir()
            _git_init(repo)
            engine.install_into_repo(repo, _source(), yes=True, no_color=True)
            subprocess.run(["git", "-C", str(repo), "add", "-A"], capture_output=True)
            subprocess.run(
                ["git", "-C", str(repo), "commit", "-m", "seed"], capture_output=True
            )
            plan = engine.plan_deep_cleanup(repo)
            self.assertIn(".aw/records/plans", plan.counts)
            self.assertTrue(
                any(k.startswith(".aw/records/") for k in plan.counts),
                f"deep-cleanup missed the flat .aw/records/* roots: {list(plan.counts)}",
            )
        finally:
            import shutil

            shutil.rmtree(tmp, ignore_errors=True)


def _source() -> Path:
    """The framework's own shipped workflow bundle (source for install)."""
    from tests.support import SOURCE_WORKFLOWS

    return SOURCE_WORKFLOWS


if __name__ == "__main__":
    unittest.main()
