"""Structural conformance gate: parser leaf declaration coverage and alias equivalence.

Part of IPD dq9bj9 (backlog h0tiaw). Stdlib unittest and pytest (Python 3.9+).
Default-collected in CI and local test runs (no slow marker).

Enforces:
1. Zero undeclared parser leaves (every parser leaf carries a CommandDeclaration).
2. Every declared leaf present in the parser has full required scenario coverage.
3. Declared leaves absent from the parser equal the pinned set (expected empty).
4. Every member of LIVE_SAFE_LEAVES produces at least one matrix row.
5. Harness invariants (USAGE_ERROR_FLAG, ANSI_RE).
6. Alias leaves are agent-byte-equivalent to their canonical targets.
"""

from __future__ import annotations

import unittest
import pytest

from agent_workflows.cli import _build_parser
from agent_workflows.command_surface import (
    discover_parser_leaves,
    find_undeclared_leaves,
    get_all_declarations,
    get_declaration,
)
from tests.conformance_matrix import (
    ANSI_RE,
    LIVE_SAFE_LEAVES,
    USAGE_ERROR_FLAG,
    build_matrix,
    required_scenarios,
    run_cli,
)


class UndeclaredLeafGuardTests(unittest.TestCase):
    """Structural matrix gate: zero undeclared leaves, scenario completeness, and drift pinning."""

    def test_no_undeclared_parser_leaves(self) -> None:
        """Every leaf discoverable from the parser must carry a CommandDeclaration."""
        parser = _build_parser()
        undeclared = find_undeclared_leaves(parser)
        self.assertEqual(
            undeclared,
            set(),
            f"Undeclared parser leaves (add a CommandDeclaration): {sorted(undeclared)}",
        )

    def test_every_declared_leaf_gets_a_full_scenario_row_set(self) -> None:
        """Each declared leaf PRESENT in the parser must have every required scenario."""
        parser = _build_parser()
        report = build_matrix(parser)
        self.assertEqual(report.undeclared, [], "undeclared leaves present")
        parser_leaves = discover_parser_leaves(parser)
        for decl in get_all_declarations():
            if decl.command == "aw":
                continue
            # Alias leaves and declared-but-absent leaves are not live matrix rows;
            # aliases are gated by AliasEquivalenceTests, absences by the drift test.
            if decl.command not in parser_leaves:
                continue
            covered = report.scenarios_for(decl.command)
            req = set(required_scenarios(decl))
            missing = req - covered
            self.assertEqual(
                missing,
                set(),
                f"{decl.command} ({decl.command_class}) missing scenarios: {missing}",
            )

    def test_declared_absent_leaves_matches_pinned_set(self) -> None:
        """A declaration with no parser leaf is a known drift.

        This test pins the set of declared leaves missing from the parser so a
        silent drift (a declaration whose parser leaf vanished) fails CI. A
        non-empty set represents a declaration whose parser leaf vanished, to be
        fixed or owned with a filed id6, and cross-checked against the behavioral
        reachability gate
        tests/test_command_surface_declarations.py::test_zero_unreachable_command_declarations
        and its UNREACHABLE_COMMAND_ALLOW_SET (from gm9baj).
        """
        parser = _build_parser()
        report = build_matrix(parser)
        pinned_declared_absent: set[str] = set()
        self.assertEqual(
            set(report.declared_absent),
            pinned_declared_absent,
            "Declaration/parser drift changed. Any unexpected member represents a "
            "declaration whose parser leaf vanished, to be fixed or owned with a "
            "filed id6, and cross-checked against "
            "tests/test_command_surface_declarations.py::test_zero_unreachable_command_declarations "
            f"and UNREACHABLE_COMMAND_ALLOW_SET. Actual: {sorted(report.declared_absent)}",
        )

    def test_matrix_has_at_least_one_passing_row_per_live_leaf(self) -> None:
        """Every leaf in LIVE_SAFE_LEAVES must produce at least one matrix row."""
        parser = _build_parser()
        report = build_matrix(parser)
        for leaf in LIVE_SAFE_LEAVES:
            rows = report.rows_for(leaf)
            self.assertTrue(rows, f"live leaf {leaf!r} produced no matrix rows")


class HarnessInvariantsTests(unittest.TestCase):
    """Executors for harness invariants (USAGE_ERROR_FLAG, ANSI_RE)."""

    def test_usage_error_flag_triggers_argparse_error(self) -> None:
        """USAGE_ERROR_FLAG must deterministically trigger argparse exit 2."""
        res = run_cli(["status", USAGE_ERROR_FLAG])
        self.assertEqual(
            res.returncode,
            2,
            f"USAGE_ERROR_FLAG {USAGE_ERROR_FLAG!r} did not exit 2: {res.returncode}",
        )
        self.assertIn("usage", (res.stdout + res.stderr).lower())

    def test_ansi_re_detects_csi_sequences_and_spares_plain_text(self) -> None:
        """ANSI_RE must match CSI color sequences and leave plain text intact."""
        self.assertIsNotNone(ANSI_RE.search("\x1b[31mred\x1b[0m"))
        self.assertIsNone(ANSI_RE.search("plain text with no escapes"))


class AliasEquivalenceTests:
    """E-01 / E-04: every alias leaf is agent-byte-equivalent to its canonical target."""

    __test__ = True

    ALIAS_PAIRS = [
        ("spec check", "specs check"),
        ("sanitize", "check-local-leaks"),
    ]

    @pytest.mark.parametrize("alias,canonical", ALIAS_PAIRS)
    def test_alias_agent_output_is_byte_equivalent(
        self, alias: str, canonical: str
    ) -> None:
        decl = get_declaration(alias)
        assert decl is not None, f"alias {alias} not declared"
        assert (
            decl.command_class == "alias"
        ), f"{alias} declared class {decl.command_class} != 'alias'"
        a = run_cli([*alias.split(), "--agent"])
        c = run_cli([*canonical.split(), "--agent"])
        assert (
            a.returncode == c.returncode
        ), f"{alias} rc {a.returncode} != {canonical} rc {c.returncode}"
        assert a.stdout == c.stdout, f"{alias} stdout not byte-equal to {canonical}"
        assert (
            ANSI_RE.search(a.stdout) is None
        ), f"{alias} agent stdout contains ANSI: {a.stdout!r}"
        assert (
            ANSI_RE.search(c.stdout) is None
        ), f"{canonical} agent stdout contains ANSI: {c.stdout!r}"


if __name__ == "__main__":
    unittest.main()
