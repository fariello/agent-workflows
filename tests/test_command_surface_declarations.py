"""Tests for whole-CLI command surface declarations.

awcliux Order 04 (10jpsa) / cmdsurf (0yrtne) E-03 / V-03.
declabsent Order 01 (gm9baj) E-01 / V-01.

Asserts every parser leaf carries a contract declaration in COMMAND_INVENTORY
(zero undeclared leaves across the built CLI parser) and every declared command
resolves through the built parser's dispatch table (zero unreachable command
declarations).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import unittest

from agent_workflows import cli, command_surface
from agent_workflows.command_surface import find_undeclared_leaves
from tests.conformance_matrix import UNREACHABLE_COMMAND_ALLOW_SET, Exemption


def _resolves_through_dispatch(cmd: str, root_parser: argparse.ArgumentParser) -> bool:
    """Resolve a command's token path through the parser dispatch table.

    Starting at root_parser, each token in cmd.split() must match a choice
    in an argparse._SubParsersAction at that level. Family roots and leaf
    commands both resolve; phantoms and unregistered subparsers fail.
    """
    curr = root_parser
    for tok in cmd.split():
        subparsers_actions = [
            a for a in curr._actions if isinstance(a, argparse._SubParsersAction)
        ]
        if not subparsers_actions:
            return False
        found = False
        for sa in subparsers_actions:
            if tok in sa.choices:
                curr = sa.choices[tok]
                found = True
                break
        if not found:
            return False
    return True


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

    def test_zero_unreachable_command_declarations(self):
        """Require every command declared in COMMAND_INVENTORY resolves through _build_parser().

        A declared command whose tokens cannot be routed through the built parser's
        argparse._SubParsersAction dispatch table is unreachable by users.

        Exceptions are permitted only when enumerated with a typed citation and reason
        in UNREACHABLE_COMMAND_ALLOW_SET (tests/conformance_matrix.py).
        """
        parser = cli._build_parser()
        declarations = command_surface.get_all_declarations()

        # Validate allow-set entry contract
        for cmd, entry in UNREACHABLE_COMMAND_ALLOW_SET.items():
            self.assertIsInstance(entry, Exemption)
            self.assertIn(
                entry.reason_kind, ("sanctioned_raw", "known_broken", "not_runnable")
            )
            self.assertTrue(entry.citation, f"Missing citation for {cmd}")
            self.assertTrue(entry.reason, f"Missing reason for {cmd}")

        unreachable: set[str] = set()
        help_diagnostics: dict[str, str] = {}

        for decl in declarations:
            cmd = decl.command
            if cmd == "aw":
                continue
            if not _resolves_through_dispatch(cmd, parser):
                unreachable.add(cmd)
                # Capture --help stderr for diagnostic message
                err_buf = io.StringIO()
                out_buf = io.StringIO()
                with contextlib.redirect_stdout(out_buf), contextlib.redirect_stderr(
                    err_buf
                ):
                    try:
                        parser.parse_args([*cmd.split(), "--help"])
                    except SystemExit:
                        pass
                diag = err_buf.getvalue().strip()
                if diag:
                    help_diagnostics[cmd] = diag

        allowed = set(UNREACHABLE_COMMAND_ALLOW_SET.keys())

        unexpected = sorted(unreachable - allowed)
        stale = sorted(allowed - unreachable)

        failures = []
        if unexpected:
            msg_parts = [
                f"Found {len(unexpected)} declared command(s) that cannot be reached through the parser dispatch table:"
            ]
            for cmd in unexpected:
                diag = help_diagnostics.get(cmd)
                if diag:
                    err_lines = [line for line in diag.splitlines() if "error:" in line]
                    err_summary = err_lines[-1] if err_lines else diag.splitlines()[-1]
                    msg_parts.append(f"  - {cmd!r}: {err_summary}")
                else:
                    msg_parts.append(
                        f"  - {cmd!r} (no subparser choices accept this token path)"
                    )
            msg_parts.append(
                "Fix: register the subparser in cli._build_parser() or remove the declaration from COMMAND_INVENTORY."
            )
            failures.append("\n".join(msg_parts))

        if stale:
            msg_parts = [
                f"Found {len(stale)} stale entry/entries in UNREACHABLE_COMMAND_ALLOW_SET that are now REACHABLE:"
            ]
            for cmd in stale:
                msg_parts.append(f"  - {cmd!r}")
            msg_parts.append(
                "Fix: delete the stale entry/entries from UNREACHABLE_COMMAND_ALLOW_SET in tests/conformance_matrix.py."
            )
            failures.append("\n".join(msg_parts))

        self.assertEqual(
            unreachable,
            allowed,
            "\n\n".join(failures),
        )


if __name__ == "__main__":
    unittest.main()
