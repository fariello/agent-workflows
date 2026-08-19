"""Tests for `aw exclude`, `aw include`, and enhanced `aw status` with rich per-repo details."""

from __future__ import annotations

import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from tests.support import init_repo
from agent_workflows import cli, config as CFG


def _run(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cli.main(argv)
    return code, buf.getvalue()


class ExcludeIncludeStatusTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self._old_xdg = os.environ.get("XDG_CONFIG_HOME")
        os.environ["XDG_CONFIG_HOME"] = str(self.base / "cfg")
        self._old_nocolor = os.environ.get("NO_COLOR")
        os.environ["NO_COLOR"] = "1"

    def tearDown(self):
        if self._old_xdg is None:
            os.environ.pop("XDG_CONFIG_HOME", None)
        else:
            os.environ["XDG_CONFIG_HOME"] = self._old_xdg
        if self._old_nocolor is None:
            os.environ.pop("NO_COLOR", None)
        else:
            os.environ["NO_COLOR"] = self._old_nocolor
        self._tmp.cleanup()

    def _repo(self, name):
        return init_repo(self.base / name)

    def test_exclude_and_include_verbs(self):
        r1 = self._repo("repo1")
        r2 = self._repo("repo2")

        # Include repo1 and repo2
        code, out = _run(["include", "repos", str(r1), str(r2)])
        self.assertEqual(code, 0)
        self.assertIn("Included repository", out)
        self.assertIn("Config:", out)
        self.assertIn("excluded", out)
        self.assertIn("configured", out)

        cfg = CFG.load()
        self.assertIn(CFG._preserve_home(str(r1)), cfg["repos"])
        self.assertIn(CFG._preserve_home(str(r2)), cfg["repos"])

        # Listing included repos
        code, out = _run(["include"])
        self.assertEqual(code, 0)
        self.assertIn("Configured Repositories", out)
        self.assertIn("Config:", out)

        # Exclude repo1 with noun syntax
        code, out = _run(["exclude", "repo", str(r1)])
        self.assertEqual(code, 0)
        self.assertIn("Excluded repository", out)
        self.assertIn("Config:", out)

        cfg = CFG.load()
        self.assertIn(CFG._preserve_home(str(r1)), cfg["exclude"])
        self.assertNotIn(CFG._preserve_home(str(r1)), cfg["repos"])

        # Listing excluded repos
        code, out = _run(["exclude"])
        self.assertEqual(code, 0)
        self.assertIn("Excluded Repositories", out)
        self.assertIn("Config:", out)

        # Re-include repo1
        code, out = _run(["include", str(r1)])
        self.assertEqual(code, 0)
        self.assertIn("un-excluded", out)

        cfg = CFG.load()
        self.assertNotIn(CFG._preserve_home(str(r1)), cfg["exclude"])
        self.assertIn(CFG._preserve_home(str(r1)), cfg["repos"])

    def test_status_per_repo_details(self):
        r1 = self._repo("proj1")
        _run(["install", str(r1), "--yes"])
        cfg = CFG.load()
        cfg["repos"] = [str(r1)]
        CFG.save(cfg)

        code, out = _run(["status"])
        self.assertEqual(code, 0)
        self.assertIn("Managed Repositories", out)
        self.assertIn("proj1", out)
        self.assertIn("Version:", out)
        self.assertIn("Layout:", out)
        self.assertIn("Git:", out)

    def test_status_json_per_repo_details(self):
        r1 = self._repo("proj1")
        _run(["install", str(r1), "--yes"])
        cfg = CFG.load()
        cfg["repos"] = [str(r1)]
        CFG.save(cfg)

        code, out = _run(["status", "--json"])
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertIn("repositories", data)
        self.assertEqual(len(data["repositories"]), 1)
        repo_data = data["repositories"][0]
        self.assertIn("proj1", repo_data["path"])
        self.assertEqual(repo_data["layout"], ".aw")
        self.assertIn("git", repo_data)


if __name__ == "__main__":
    unittest.main()
