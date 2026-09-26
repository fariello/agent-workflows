"""Tests for whole-CLI command surface declarations.

awcliux Order 04 (10jpsa) / cmdsurf (0yrtne) E-03 / V-03.

Asserts every parser leaf carries a contract declaration in COMMAND_INVENTORY
(zero undeclared leaves across the built CLI parser).
"""

from __future__ import annotations

import unittest

from agent_workflows import cli
from agent_workflows.command_surface import find_undeclared_leaves


class CommandSurfaceDeclarationsTests(unittest.TestCase):
    """Assert exhaustive leaf declarations and zero undeclared parser leaves."""

    def test_zero_undeclared_parser_leaves(self):
        """Require 0 undeclared leaves across _build_parser()."""
        parser = cli._build_parser()
        undeclared = find_undeclared_leaves(parser)
        self.assertEqual(
            undeclared,
            set(),
            f"Found undeclared parser leaves: {sorted(undeclared)}",
        )


if __name__ == "__main__":
    unittest.main()
