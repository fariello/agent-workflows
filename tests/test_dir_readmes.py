"""Tests for the .agents/ tree directory READMEs (IPD-3: agents-tree-directory-readmes).

Category 1 (user-owned, installer-generated no-clobber): .agents/README.md,
.agents/plans/README.md, and one per lifecycle bucket. Category 2 (framework-authored,
copied): a README in each top-level .agents/workflows/<capability>/. Stdlib unittest only.
"""

from __future__ import annotations

import io
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.support import init_repo, REPO_ROOT
from agent_workflows import cli, engine


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class Category1GeneratedReadmes(unittest.TestCase):
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

    def test_agents_and_plans_readmes_created(self):
        _run(["install", str(self.repo), "--yes"])
        self.assertTrue((self.repo / ".agents/README.md").is_file())
        self.assertTrue((self.repo / ".agents/plans/README.md").is_file())
        # One per lifecycle bucket, driven by PLAN_LIFECYCLE_SUBDIRS.
        for bucket in engine.PLAN_LIFECYCLE_SUBDIRS:
            self.assertTrue(
                (self.repo / ".agents/plans" / bucket / "README.md").is_file(),
                f"missing README in plans/{bucket}",
            )

    def test_no_clobber_preserves_user_readme(self):
        target = self.repo / ".agents/plans/pending/README.md"
        target.parent.mkdir(parents=True)
        target.write_text("MINE\n", encoding="utf-8")
        _run(["install", str(self.repo), "--yes"])
        self.assertEqual(target.read_text(encoding="utf-8"), "MINE\n")

    def test_idempotent_rerun_reports_already_current(self):
        _run(["install", str(self.repo), "--yes"])
        # A second install must not error and must leave the READMEs in place.
        code, _ = _run(["install", str(self.repo), "--yes"])
        self.assertEqual(code, 0)
        self.assertTrue((self.repo / ".agents/README.md").is_file())

    def test_dry_run_writes_nothing(self):
        _run(["install", str(self.repo), "--dry-run", "--yes"])
        self.assertFalse((self.repo / ".agents/README.md").exists())
        self.assertFalse((self.repo / ".agents/plans/README.md").exists())


class Category2AuthoredReadmes(unittest.TestCase):
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

    def test_capability_readmes_installed(self):
        _run(["install", str(self.repo), "--yes"])
        # A representative sample across with-subdir and flat capabilities.
        for cap in (
            "assess",
            "advise",
            "verify",
            "spec",
            "templates",
            "release-review",
        ):
            self.assertTrue(
                (self.repo / ".agents/workflows" / cap / "README.md").is_file(),
                f"missing capability README for {cap}",
            )

    def test_source_has_readme_for_every_top_level_capability(self):
        # P8/completeness: every top-level .agents/workflows/<capability>/ in SOURCE has a
        # README (so installed repos are fully self-documenting at top-level depth).
        wf = REPO_ROOT / ".agents" / "workflows"
        missing = []
        for d in sorted(p for p in wf.iterdir() if p.is_dir()):
            if not (d / "README.md").is_file():
                missing.append(d.name)
        self.assertEqual(missing, [], f"capability dirs missing a README: {missing}")


if __name__ == "__main__":
    unittest.main()
