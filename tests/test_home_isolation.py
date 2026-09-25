"""The test session must never resolve the developer's real AW_HOME or user config.

Regression guard for 2026-09-24: `DeclarativeAllowedValuesTests` rewrote the developer's real
`~/.config/agent-workflows/config.json` (leaving `"aw_home": "~/allowed"`), and the analytics
tests left hundreds of cache directories under `~/.aw/projects/`. The root `conftest.py` now
installs an unconditional sandbox and restores it after every test; these tests prove both
halves, including the one that failed: a test that POPS the variables must not strip the
sandbox from the tests that run after it.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from agent_workflows import config as CFG
from agent_workflows import project_context

_REAL_HOME = Path.home().resolve()


def _under_real_home(p: str | os.PathLike) -> bool:
    real_config = (_REAL_HOME / ".config").resolve()
    real_aw = (_REAL_HOME / ".aw").resolve()
    resolved = Path(p).expanduser().resolve()
    return any(resolved == r or r in resolved.parents for r in (real_config, real_aw))


class SessionSandboxTests(unittest.TestCase):
    def test_user_config_resolves_inside_the_sandbox(self):
        self.assertFalse(_under_real_home(CFG.config_path()), CFG.config_path())

    def test_aw_home_resolves_inside_the_sandbox(self):
        home = project_context.get_default_aw_home()
        self.assertFalse(_under_real_home(home), home)
        self.assertFalse(Path(home).resolve() == _REAL_HOME / "allowed")


class PopDoesNotLeakAcrossTests(unittest.TestCase):
    """Two tests run in order in one class: the first strips the sandbox the way ~20 real tests
    do in their cleanup, the second must still see it (the autouse fixture restores it)."""

    def test_1_strip_the_sandbox_like_a_careless_cleanup(self):
        os.environ.pop("XDG_CONFIG_HOME", None)
        os.environ.pop("AW_HOME", None)

    def test_2_next_test_still_sandboxed(self):
        self.assertIn("XDG_CONFIG_HOME", os.environ)
        self.assertIn("AW_HOME", os.environ)
        self.assertFalse(_under_real_home(CFG.config_path()), CFG.config_path())


if __name__ == "__main__":
    unittest.main()
