"""The technical writing standard is installed and the managed AGENTS.md block points at it."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from agent_workflows import engine
from tests.support import SOURCE_WORKFLOWS, init_repo

STANDARD_REL = "technical-writing/technical-writing.md"


class TechnicalWritingDeliveryTests(unittest.TestCase):
    def test_pointer_prose_names_the_installed_standard_for_both_layouts(self):
        for layout, root in (
            ("aw", ".aw/system/workflows"),
            ("legacy", ".agents/workflows"),
        ):
            with self.subTest(layout=layout):
                prose = engine.agents_pointer_prose(layout)
                self.assertIn(f"`{root}/{STANDARD_REL}`", prose)

    @pytest.mark.slow
    def test_install_delivers_the_standard_and_the_agents_rule(self):
        with tempfile.TemporaryDirectory() as td:
            repo = init_repo(Path(td) / "target")
            with redirect_stdout(io.StringIO()):
                engine.install_into_repo(
                    repo, SOURCE_WORKFLOWS, yes=True, no_color=True
                )

            installed = repo / ".aw" / "system" / "workflows" / STANDARD_REL
            self.assertTrue(installed.is_file(), "the standard must be installed")
            self.assertEqual(
                installed.read_bytes(),
                (Path(SOURCE_WORKFLOWS) / STANDARD_REL).read_bytes(),
                "the installed standard must be a verbatim copy of the source",
            )

            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(f"`.aw/system/workflows/{STANDARD_REL}`", agents)


if __name__ == "__main__":
    unittest.main()
