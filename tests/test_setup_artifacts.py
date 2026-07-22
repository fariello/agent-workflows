"""Tests for deterministic setup-artifact creation on install (IPD-2 Batch E; AC-16).

Verifies the CLI/engine creates the plan lifecycle dirs, a .gitleaksignore baseline, and
the secret-scan CI workflow in a target repo (staged, idempotent, no-clobber - R-2), and
that the "run /setup-repo" guidance is emitted. Stdlib unittest only.
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.support import REPO_ROOT, init_repo
from agent_workflows import cli, engine


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class SetupArtifactTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        os.environ["NO_COLOR"] = "1"
        self.repo = init_repo(self.base / "r")

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        os.environ.pop("NO_COLOR", None)
        self._tmp.cleanup()

    def test_install_creates_all_artifacts_and_guidance(self):
        code, out = _run(["install", str(self.repo), "--yes"])
        self.assertEqual(code, 0, out)
        for sub in ("pending", "reusable", "executed", "superseded", "not-executed"):
            self.assertTrue(
                (self.repo / ".agents/plans" / sub / ".gitkeep").is_file(),
                f"missing plan dir {sub}",
            )
        for sub in ("research", "walkthroughs"):
            self.assertTrue(
                (self.repo / ".agents/docs" / sub / ".gitkeep").is_file(),
                f"missing docs dir {sub}",
            )
        # Prompts staging buckets (D91): all 5, mirroring plans.
        for sub in ("pending", "executed", "superseded", "not-executed", "reusable"):
            self.assertTrue(
                (self.repo / ".agents/prompts" / sub / ".gitkeep").is_file(),
                f"missing prompts dir {sub}",
            )
        # Prompts staging READMEs (D91): area README + one per bucket.
        self.assertTrue((self.repo / ".agents/prompts/README.md").is_file())
        for sub in ("pending", "executed", "superseded", "not-executed", "reusable"):
            self.assertTrue(
                (self.repo / ".agents/prompts" / sub / "README.md").is_file(),
                f"missing prompts README {sub}",
            )
        # Prompts quarantine lane (D94): a nested .gitignore ignores local/, and the local/ dir is
        # materialized (installer creates all expected dirs) but NOT tracked (empty + gitignored).
        self.assertTrue((self.repo / ".agents/prompts/.gitignore").is_file())
        self.assertIn(
            "local/",
            (self.repo / ".agents/prompts/.gitignore").read_text(encoding="utf-8"),
        )
        self.assertTrue((self.repo / ".agents/prompts/local").is_dir())
        self.assertFalse((self.repo / ".agents/prompts/local/.gitkeep").exists())
        # Comms local/ is also materialized now (D94, uniform "installer creates all expected dirs").
        self.assertTrue((self.repo / ".agents/comms/local/inbox").is_dir())
        # Verify no-clobber READMEs
        self.assertTrue((self.repo / ".agents/docs/README.md").is_file())
        self.assertTrue((self.repo / ".agents/docs/research/README.md").is_file())
        self.assertTrue((self.repo / ".agents/docs/walkthroughs/README.md").is_file())
        self.assertTrue((self.repo / ".gitleaksignore").is_file())
        self.assertTrue((self.repo / ".github/workflows/secret-scan.yml").is_file())
        # Inter-agent comms skeleton (D81): nested .gitignore, README, shared/ gitkeeps.
        self.assertTrue((self.repo / ".agents/comms/.gitignore").is_file())
        self.assertTrue((self.repo / ".agents/comms/README.md").is_file())
        for sub in ("inbox", "sent", "archive"):
            self.assertTrue(
                (self.repo / ".agents/comms/shared" / sub / ".gitkeep").is_file(),
                f"missing comms shared dir {sub}",
            )
        # `local/` is ignored by the nested .gitignore, so it gets NO committed .gitkeep.
        self.assertFalse((self.repo / ".agents/comms/local/inbox/.gitkeep").exists())
        # The nested .gitignore ignores local/ and does NOT touch the target root .gitignore.
        self.assertIn(
            "local/",
            (self.repo / ".agents/comms/.gitignore").read_text(encoding="utf-8"),
        )
        # AC-16: guidance to run /setup-repo is emitted.
        self.assertIn("/setup-repo", out)

    def test_idempotent_rerun_creates_nothing_new(self):
        _run(["install", str(self.repo), "--yes"])
        # Second engine call directly: no artifacts created the second time.
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git)
        self.assertEqual(created, [])

    def test_no_clobber_preserves_existing_files(self):
        # A user's own .gitleaksignore and CI must not be overwritten (R-2).
        (self.repo / ".gitleaksignore").write_text("MY BASELINE\n", encoding="utf-8")
        (self.repo / ".github/workflows").mkdir(parents=True)
        (self.repo / ".github/workflows/secret-scan.yml").write_text(
            "name: my-own-scan\n", encoding="utf-8"
        )
        _run(["install", str(self.repo), "--yes"])
        self.assertEqual(
            (self.repo / ".gitleaksignore").read_text(encoding="utf-8"), "MY BASELINE\n"
        )
        self.assertIn(
            "my-own-scan",
            (self.repo / ".github/workflows/secret-scan.yml").read_text(
                encoding="utf-8"
            ),
        )

    def test_engine_returns_created_list(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git)
        # 5 plan-dir gitkeeps (pending/executed/superseded/not-executed/reusable)
        # + 4 docs-dir gitkeeps (research/walkthroughs/specs/prompts)
        # + 5 prompts-dir gitkeeps (pending/executed/superseded/not-executed/reusable) (D91)
        # + prompts .gitignore (D94 local/ lane; the mkdir'd local/ dirs are side-effect-only,
        #   NOT counted)
        # + gitleaksignore + secret-scan CI
        # + comms .gitignore + comms README + 3 comms shared/ gitkeeps (inbox/sent/archive) = 22.
        self.assertEqual(len(created), 22)

    def test_install_does_not_touch_target_root_gitignore(self):
        # The comms nested .gitignore is a created deliverable; the ROOT .gitignore must not be
        # created/modified by comms scaffolding. (ensure_backups_gitignored is a separate path.)
        root_gi = self.repo / ".gitignore"
        before = root_gi.read_text(encoding="utf-8") if root_gi.exists() else None
        use_git = engine.git_available(self.repo)
        engine.create_setup_artifacts(self.repo, use_git)
        after = root_gi.read_text(encoding="utf-8") if root_gi.exists() else None
        self.assertEqual(
            before, after, "create_setup_artifacts must not touch the root .gitignore"
        )

    def test_dry_run_reports_without_writing(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git, dry_run=True)
        self.assertTrue(all("dry-run" in c for c in created))
        self.assertFalse((self.repo / ".gitleaksignore").exists())


class PromptsScaffoldTests(unittest.TestCase):
    """`.agents/prompts/` operational-staging scaffold (D91)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        os.environ["NO_COLOR"] = "1"
        self.repo = init_repo(self.base / "r")

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        os.environ.pop("NO_COLOR", None)
        self._tmp.cleanup()

    def test_constants_mirror_plans_buckets(self):
        # The prompts lifecycle buckets are the same set/order as the plans buckets.
        self.assertEqual(engine.PROMPT_LIFECYCLE_SUBDIRS, engine.PLAN_LIFECYCLE_SUBDIRS)
        self.assertEqual(engine.PROMPTS_DIR, ".agents/prompts")

    def test_dry_run_reports_prompts_buckets_without_writing(self):
        # Dry-run/real parity for the new prompts branch (plan PR-002).
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git, dry_run=True)
        for sub in engine.PROMPT_LIFECYCLE_SUBDIRS:
            keep = f".agents/prompts/{sub}/.gitkeep"
            self.assertTrue(
                any(c.startswith(keep) for c in created),
                f"dry-run did not report {keep}: {created}",
            )
            self.assertFalse((self.repo / keep).exists(), f"dry-run wrote {keep}")

    def test_undo_removes_prompts_scaffold(self):
        # The prompts scaffold (dirs + READMEs) is recorded in .created-files.json so rollback
        # removes it (D85 F5 parity for the new prompts area).
        engine.install_into_repo(
            self.repo, REPO_ROOT / ".agents" / "workflows", yes=True, no_color=True
        )
        readme = self.repo / ".agents/prompts/README.md"
        keep = self.repo / ".agents/prompts/executed/.gitkeep"
        self.assertTrue(readme.is_file())
        self.assertTrue(keep.is_file())
        engine.run_rollback(self.repo, no_color=True)
        self.assertFalse(readme.exists(), "rollback left the prompts README behind")
        self.assertFalse(keep.exists(), "rollback left a prompts bucket gitkeep behind")

    def test_local_quarantine_lane(self):
        # D94: the nested .gitignore ignores local/, the local/ dir is materialized (installer
        # creates all expected dirs) but not tracked, and rollback removes the .gitignore.
        import subprocess

        # Install once (this records the created files incl. the prompts .gitignore for --undo).
        engine.install_into_repo(
            self.repo, REPO_ROOT / ".agents" / "workflows", yes=True, no_color=True
        )
        gi = self.repo / ".agents/prompts/.gitignore"
        self.assertTrue(gi.is_file())
        self.assertIn("local/", gi.read_text(encoding="utf-8"))
        self.assertTrue((self.repo / ".agents/prompts/local").is_dir())
        self.assertFalse((self.repo / ".agents/prompts/local/.gitkeep").exists())
        # git actually ignores content under local/
        (self.repo / ".agents/prompts/local/x.md").write_text("raw\n", encoding="utf-8")
        r = subprocess.run(
            ["git", "-C", str(self.repo), "check-ignore", ".agents/prompts/local/x.md"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(r.returncode, 0, "local/ content is not gitignored")
        # rollback removes the .gitignore file (it is in the created record, D85 F5).
        engine.run_rollback(self.repo, no_color=True)
        self.assertFalse(gi.exists(), "rollback left the prompts .gitignore behind")

    def test_dry_run_reports_prompts_gitignore(self):
        use_git = engine.git_available(self.repo)
        created = engine.create_setup_artifacts(self.repo, use_git, dry_run=True)
        self.assertTrue(
            any(c.startswith(".agents/prompts/.gitignore") for c in created),
            f"dry-run did not report the prompts .gitignore: {created}",
        )

    def test_readmes_no_clobber(self):
        # A user's own prompts README is never overwritten.
        (self.repo / ".agents/prompts").mkdir(parents=True)
        (self.repo / ".agents/prompts/README.md").write_text(
            "MY PROMPTS DOC\n", encoding="utf-8"
        )
        _run(["install", str(self.repo), "--yes"])
        self.assertEqual(
            (self.repo / ".agents/prompts/README.md").read_text(encoding="utf-8"),
            "MY PROMPTS DOC\n",
        )


class LocalLeaksBackstopTests(unittest.TestCase):
    """The OFF-by-default local-leaks CI/hook writer (IPD 20260721-2005-01 Order 3)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = init_repo(Path(self._tmp.name) / "r")

    def tearDown(self):
        self._tmp.cleanup()

    def test_default_setup_artifacts_unchanged_count_22(self):
        # G6: the off-by-default backstop MUST NOT leak into the always-on path.
        created = engine.create_setup_artifacts(self.repo, use_git=False)
        self.assertEqual(len(created), 22)
        # And neither backstop file is written by the default path.
        self.assertFalse((self.repo / engine.LOCAL_LEAKS_CI).exists())
        self.assertFalse((self.repo / engine.PRE_COMMIT_CONFIG).exists())

    def test_neither_flag_writes_nothing(self):
        res = engine.create_local_leaks_backstop(
            self.repo, use_git=False, install_ci=False, install_hook=False
        )
        self.assertEqual(res["created"], [])
        self.assertFalse((self.repo / engine.LOCAL_LEAKS_CI).exists())

    def test_optin_creates_ci_and_hook(self):
        res = engine.create_local_leaks_backstop(
            self.repo, use_git=False, install_ci=True, install_hook=True
        )
        self.assertIn(engine.LOCAL_LEAKS_CI, res["created"])
        self.assertIn(engine.PRE_COMMIT_CONFIG, res["created"])
        ci = (self.repo / engine.LOCAL_LEAKS_CI).read_text(encoding="utf-8")
        # G4: the target-repo CI must install agent-workflows and pick a current Python.
        self.assertIn("pip install agent-workflows", ci)
        self.assertIn('python-version: "3.12"', ci)
        self.assertIn("python -m agent_workflows check-local-leaks", ci)
        hook = (self.repo / engine.PRE_COMMIT_CONFIG).read_text(encoding="utf-8")
        self.assertIn("id: local-leaks", hook)
        self.assertIn("pass_filenames: false", hook)  # whole-tree (OQ2)

    def test_no_clobber_existing_precommit_hands_back_block(self):
        (self.repo / engine.PRE_COMMIT_CONFIG).write_text(
            "repos: []\n", encoding="utf-8"
        )
        res = engine.create_local_leaks_backstop(
            self.repo, use_git=False, install_ci=False, install_hook=True
        )
        self.assertEqual(res["created"], [])  # did not clobber
        self.assertEqual(
            (self.repo / engine.PRE_COMMIT_CONFIG).read_text(encoding="utf-8"),
            "repos: []\n",
        )
        self.assertTrue(any("id: local-leaks" in n for n in res["notes"]))

    def test_dry_run_writes_nothing(self):
        res = engine.create_local_leaks_backstop(
            self.repo, use_git=False, install_ci=True, install_hook=True, dry_run=True
        )
        self.assertEqual(res["created"], [])
        self.assertFalse((self.repo / engine.LOCAL_LEAKS_CI).exists())
        self.assertTrue(res["notes"])

    def test_idempotent_rerun_no_clobber(self):
        engine.create_local_leaks_backstop(
            self.repo, use_git=False, install_ci=True, install_hook=True
        )
        res = engine.create_local_leaks_backstop(
            self.repo, use_git=False, install_ci=True, install_hook=True
        )
        self.assertEqual(res["created"], [])
        self.assertTrue(all("exists" in s or "manually" in s for s in res["skipped"]))


if __name__ == "__main__":
    unittest.main()
