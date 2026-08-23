"""Tests for awcolor Order 01: 256-color human output policy + accessibility invariant.

Color appears only under a color-affirming environment (FORCE_COLOR / TTY); NO_COLOR, --no-color, and
a piped (non-TTY) stdout suppress it. The literal disposition WORD is present in every case."""

from __future__ import annotations

import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_ANSI = re.compile(r"\033\[[0-9;]*m")


def _lint(plan_path, env_extra):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env.pop("FORCE_COLOR", None)
    env.pop("NO_COLOR", None)
    env.update(env_extra)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_workflows",
            "ipd",
            "lint",
            "--phase",
            "post-transition",
            str(plan_path),
        ],
        capture_output=True,
        text=True,
        env=env,
    )


class ColorOutputPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # a conforming executed plan already in the repo
        cls.plan = next(
            (REPO / ".aw/records/plans/executed").glob("20260818-awhelp-00-*.ipd.md")
        )

    def test_force_color_emits_ansi(self):
        r = _lint(self.plan, {"FORCE_COLOR": "1"})
        self.assertTrue(_ANSI.search(r.stdout), r.stdout)
        self.assertIn("conforming", _ANSI.sub("", r.stdout))

    def test_no_color_env_suppresses(self):
        r = _lint(self.plan, {"NO_COLOR": "1"})
        self.assertIsNone(_ANSI.search(r.stdout))
        self.assertTrue("conforming" in r.stdout or "clean" in r.stdout)

    def test_no_color_flag_suppresses(self):
        # even with FORCE_COLOR set, an explicit --no-color wins.
        env = dict(os.environ)
        env["PYTHONPATH"] = str(REPO) + os.pathsep + env.get("PYTHONPATH", "")
        env["FORCE_COLOR"] = "1"
        r2 = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_workflows",
                "ipd",
                "lint",
                "--no-color",
                "--phase",
                "post-transition",
                str(self.plan),
            ],
            capture_output=True,
            text=True,
            env=env,
        )
        self.assertIsNone(_ANSI.search(r2.stdout))
        self.assertTrue("conforming" in r2.stdout or "clean" in r2.stdout)

    def test_piped_stdout_suppresses(self):
        # a plain subprocess pipe (not a TTY) with no FORCE_COLOR yields no ANSI.
        r = _lint(self.plan, {})
        self.assertIsNone(_ANSI.search(r.stdout))
        self.assertTrue("conforming" in r.stdout or "clean" in r.stdout)


if __name__ == "__main__":
    unittest.main()
