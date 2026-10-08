"""Unit and outcome tests for CLI argparse dest-shadowing refusal and validation pass.

Guards against leaf argument dests shadowing ancestor subparsers dests.
Refuses colliding declarations at parser build time with an escape hatch
(AW_ALLOW_DEST_SHADOWING=1) to prevent catastrophic CLI lockouts.

Tests all four registration routes (direct, parents inheritance, argument group,
and mutually exclusive group), shipped-tree safety, known defect detection,
escape hatch semantics, and diagnostic error formatting.
"""

from __future__ import annotations

import argparse
import io
import os
import unittest
from unittest.mock import patch

from agent_workflows import cli
from agent_workflows.cli import (
    DestShadowFinding,
    find_dest_shadowing,
    validate_dest_shadowing,
)


class TestCliDestShadowRefusal(unittest.TestCase):
    """Tests for argparse dest-shadowing refusal across all registration routes."""

    # ----------------------------------------------------------------------------------
    # Four Registration Routes (F-05, E-04, V-04)
    # ----------------------------------------------------------------------------------

    def test_route_direct_add_argument(self) -> None:
        """Route 1: direct child.add_argument(...) shadows ancestor subparsers dest."""
        root = argparse.ArgumentParser(prog="synth")
        sub = root.add_subparsers(dest="command")
        child = sub.add_parser("direct")
        child.add_argument("--direct", dest="command")

        findings = find_dest_shadowing(root)
        self.assertEqual(len(findings), 1)
        expected = DestShadowFinding("synth direct", "command", ("--direct",))
        self.assertEqual(findings[0], expected)

    def test_route_parents_inheritance(self) -> None:
        """Route 2: add_parser(..., parents=[common]) where common declares colliding dest."""
        common = argparse.ArgumentParser(add_help=False)
        common.add_argument("--inherited", dest="command")

        root = argparse.ArgumentParser(prog="synth")
        sub = root.add_subparsers(dest="command")
        _ = sub.add_parser("viaparents", parents=[common])

        findings = find_dest_shadowing(root)
        self.assertEqual(len(findings), 1)
        expected = DestShadowFinding("synth viaparents", "command", ("--inherited",))
        self.assertEqual(findings[0], expected)

    def test_route_argument_group(self) -> None:
        """Route 3: child.add_argument_group(...).add_argument(...) shadows subparsers dest."""
        root = argparse.ArgumentParser(prog="synth")
        sub = root.add_subparsers(dest="command")
        child = sub.add_parser("viagroup")
        grp = child.add_argument_group("group title")
        grp.add_argument("--grp", dest="command")

        findings = find_dest_shadowing(root)
        self.assertEqual(len(findings), 1)
        expected = DestShadowFinding("synth viagroup", "command", ("--grp",))
        self.assertEqual(findings[0], expected)

    def test_route_mutually_exclusive_group(self) -> None:
        """Route 4: child.add_mutually_exclusive_group().add_argument(...) shadows dest."""
        root = argparse.ArgumentParser(prog="synth")
        sub = root.add_subparsers(dest="command")
        child = sub.add_parser("viamx")
        mx = child.add_mutually_exclusive_group()
        mx.add_argument("--mx", dest="command")

        findings = find_dest_shadowing(root)
        self.assertEqual(len(findings), 1)
        expected = DestShadowFinding("synth viamx", "command", ("--mx",))
        self.assertEqual(findings[0], expected)

    # ----------------------------------------------------------------------------------
    # Shipped Tree Safety, Known Defect, and Diagnostic Formatting
    # ----------------------------------------------------------------------------------

    def test_shipped_tree_builds_without_raising(self) -> None:
        """Shipped CLI parser tree builds cleanly with zero dest-shadowing findings."""
        parser = cli._build_parser()
        self.assertIsInstance(parser, argparse.ArgumentParser)
        findings = find_dest_shadowing(parser)
        self.assertEqual(findings, [])

    def test_real_defect_mutation_refused_on_local_parser(self) -> None:
        """Mutating a local parser to re-introduce the integration-lock defect is detected and refused."""
        parser = cli._build_parser()

        # Local in-place mutation of integration-lock locked_command -> command
        mutated = False
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                sp = action.choices.get("integration-lock")
                if sp:
                    for act in sp._actions:
                        if act.dest == "locked_command":
                            act.dest = "command"
                            mutated = True
                            break
        self.assertTrue(
            mutated, "Failed to find integration-lock locked_command action to mutate"
        )

        findings = find_dest_shadowing(parser)
        self.assertEqual(len(findings), 1)
        self.assertIn("integration-lock", findings[0].prog)
        self.assertEqual(findings[0].dest, "command")

        with self.assertRaises(ValueError) as ctx:
            validate_dest_shadowing(parser)

        err_msg = str(ctx.exception)
        self.assertIn("integration-lock", err_msg)
        self.assertIn("command", err_msg)
        self.assertIn("AW_ALLOW_DEST_SHADOWING=1", err_msg)

    def test_escape_hatch_env_var_downgrades_to_stderr_warning(self) -> None:
        """Escape hatch AW_ALLOW_DEST_SHADOWING=1 downgrades refusal to a stderr warning."""
        root = argparse.ArgumentParser(prog="test-hatch")
        sub = root.add_subparsers(dest="command")
        child = sub.add_parser("subcmd")
        child.add_argument("--colliding", dest="command")

        # 1. Unset: raises ValueError
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("AW_ALLOW_DEST_SHADOWING", None)
            with self.assertRaises(ValueError):
                validate_dest_shadowing(root)

        # 2. Set to '0': still raises ValueError (strict literal '1' check)
        with patch.dict(os.environ, {"AW_ALLOW_DEST_SHADOWING": "0"}):
            with self.assertRaises(ValueError):
                validate_dest_shadowing(root)

        # 3. Set to '1': does not raise, warns on stderr, stdout remains clean
        stderr_buf = io.StringIO()
        stdout_buf = io.StringIO()
        with patch.dict(os.environ, {"AW_ALLOW_DEST_SHADOWING": "1"}):
            with patch("sys.stderr", stderr_buf), patch("sys.stdout", stdout_buf):
                validate_dest_shadowing(root)

        err_output = stderr_buf.getvalue()
        self.assertIn("WARNING: argparse dest shadowing detected", err_output)
        self.assertIn("command", err_output)
        self.assertIn("AW_ALLOW_DEST_SHADOWING=1", err_output)
        self.assertEqual(stdout_buf.getvalue(), "")

    def test_multi_collision_error_is_diagnostic(self) -> None:
        """A tree with multiple collisions reports every finding in a single diagnostic error."""
        root = argparse.ArgumentParser(prog="test-multi")
        sub = root.add_subparsers(dest="command")

        child1 = sub.add_parser("first")
        child1.add_argument("--opt-collision", dest="command")

        child2 = sub.add_parser("second")
        child2.add_argument("command", metavar="POS")

        findings = find_dest_shadowing(root)
        self.assertEqual(len(findings), 2)

        with self.assertRaises(ValueError) as ctx:
            validate_dest_shadowing(root)

        err_msg = str(ctx.exception)
        self.assertIn("test-multi first", err_msg)
        self.assertIn("--opt-collision", err_msg)
        self.assertIn("test-multi second", err_msg)
        self.assertIn("<positional>", err_msg)
        self.assertIn("AW_ALLOW_DEST_SHADOWING=1", err_msg)


if __name__ == "__main__":
    unittest.main()
