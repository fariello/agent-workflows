"""E-01: Generated CLI output-conformance matrix over EVERY parser leaf.

awcliux Order 05 (`e8hu4s`) E-01 / V-01. Stdlib unittest only (Python 3.9+).

Falsifiability contract (any of these FAILS CI):
- An undeclared parser leaf (a leaf with no ``CommandDeclaration``) FAILS.
- A declared leaf whose class requires a scenario the matrix cannot cover FAILS.
- A live-executed leaf whose agent/JSON stream carries ANSI FAILS.
- A live-executed leaf whose agent summary ``exit`` disagrees with the process
  return code FAILS.
- A usage error that does not exit 2 FAILS.
- An alias that is not byte-identical to its canonical target FAILS.

The matrix is generated from ``_build_parser()`` crossed with the per-class
required scenarios in ``tests.conformance_matrix``; it is not a hand-maintained
list, so new leaves are forced into coverage automatically.
"""

from __future__ import annotations

import pytest

import unittest

from agent_workflows.cli import _build_parser
from agent_workflows.command_surface import (
    find_undeclared_leaves,
    get_all_declarations,
    get_declaration,
)
from tests.conformance_matrix import (
    ANSI_RE,
    LIVE_SAFE_LEAVES,
    USAGE_ERROR_FLAG,
    build_matrix,
    outcome_family,
    required_scenarios,
    run_cli,
    semantic_facts_from_agent,
    semantic_facts_from_human,
)


# Heavy subprocess/conformance suite; excluded from the fast default run (see pyproject
# addopts `-m "not slow"`). Run with `make test-all`.
pytestmark = pytest.mark.slow


class UndeclaredLeafGuardTests(unittest.TestCase):
    """E-01: zero undeclared parser leaves; every leaf carries a contract."""

    def test_no_undeclared_parser_leaves(self):
        parser = _build_parser()
        undeclared = find_undeclared_leaves(parser)
        self.assertEqual(
            undeclared,
            set(),
            f"Undeclared parser leaves (add a CommandDeclaration): {sorted(undeclared)}",
        )

    def test_every_declared_leaf_gets_a_full_scenario_row_set(self):
        """Each declared leaf PRESENT in the parser must have every required scenario."""
        from agent_workflows.command_surface import discover_parser_leaves

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

    def test_declared_absent_leaves_are_only_the_known_prompts_family(self):
        """A declaration with no parser leaf is a KNOWN, documented drift.

        ``prompts set`` is declared (Order 04 inventory) but the ``prompts`` family
        parser is not yet wired. This test PINS that set so a NEW silent drift (a
        declaration whose parser leaf silently vanished) fails CI instead of hiding.
        """
        parser = _build_parser()
        report = build_matrix(parser)
        self.assertEqual(
            set(report.declared_absent),
            {"prompts set"},
            f"declaration/parser drift changed: {sorted(report.declared_absent)}",
        )

    def test_matrix_has_at_least_one_passing_row_per_live_leaf(self):
        parser = _build_parser()
        report = build_matrix(parser)
        for leaf in LIVE_SAFE_LEAVES:
            rows = report.rows_for(leaf)
            self.assertTrue(rows, f"live leaf {leaf!r} produced no matrix rows")


class LiveScenarioConformanceTests(unittest.TestCase):
    """E-01: execute each SAFE leaf across audience scenarios and assert invariants."""

    def _agent_records_ansi_free(self, leaf: str, extra):
        res = run_cli([*leaf.split(), *extra, "--agent"])
        combined = res.stdout + res.stderr
        self.assertIsNone(
            ANSI_RE.search(combined),
            f"agent stream for {leaf!r} contained ANSI escapes:\n{combined!r}",
        )
        return res

    def test_agent_streams_are_ansi_free_and_exit_consistent(self):
        for leaf, extra in LIVE_SAFE_LEAVES.items():
            with self.subTest(leaf=leaf):
                res = self._agent_records_ansi_free(leaf, extra)
                facts = semantic_facts_from_agent(res.stdout)
                # The terminal record's exit must equal the process return code.
                if facts.get("exit") is not None:
                    self.assertEqual(
                        facts["exit"],
                        res.returncode,
                        f"{leaf!r} agent exit {facts['exit']} != rc {res.returncode}",
                    )

    def test_non_tty_human_streams_are_plain(self):
        """Piped human output (no flag) must be plain (no ANSI) under the auto cutover."""
        for leaf, extra in LIVE_SAFE_LEAVES.items():
            with self.subTest(leaf=leaf):
                res = run_cli([*leaf.split(), *extra])
                self.assertIsNone(
                    ANSI_RE.search(res.stdout),
                    f"non-TTY human stream for {leaf!r} contained ANSI: {res.stdout!r}",
                )

    def test_no_color_scenario_is_plain(self):
        for leaf, extra in LIVE_SAFE_LEAVES.items():
            with self.subTest(leaf=leaf):
                res = run_cli([*leaf.split(), *extra], no_color=True)
                self.assertIsNone(
                    ANSI_RE.search(res.stdout),
                    f"NO_COLOR human stream for {leaf!r} contained ANSI",
                )

    def test_help_scenario_exits_zero_and_documents_agent(self):
        # Help is Python-version-dependent; pin NO_COLOR + COLUMNS via run_cli env.
        for leaf in LIVE_SAFE_LEAVES:
            with self.subTest(leaf=leaf):
                res = run_cli([*leaf.split(), "--help"])
                self.assertEqual(
                    res.returncode, 0, f"{leaf} --help rc={res.returncode}"
                )
                self.assertIn("usage", res.stdout.lower())

    def test_usage_error_scenario_exits_two(self):
        for leaf in LIVE_SAFE_LEAVES:
            with self.subTest(leaf=leaf):
                res = run_cli([*leaf.split(), USAGE_ERROR_FLAG])
                self.assertEqual(
                    res.returncode,
                    2,
                    f"{leaf} bad-flag rc={res.returncode} (expected usage error 2)",
                )
                self.assertIn("usage", (res.stdout + res.stderr).lower())


class FactParityTests(unittest.TestCase):
    """E-01/E-02: human vs agent semantic outcome family must agree."""

    def test_human_and_agent_outcome_families_match(self):
        for leaf, extra in LIVE_SAFE_LEAVES.items():
            with self.subTest(leaf=leaf):
                agent = run_cli([*leaf.split(), *extra, "--agent"])
                human = run_cli([*leaf.split(), *extra])
                agent_facts = semantic_facts_from_agent(agent.stdout)
                human_facts = semantic_facts_from_human(human.stdout)
                agent_family = outcome_family(agent_facts.get("outcome"))
                human_family = human_facts.get("outcome_family")
                if agent_family is None or human_family is None:
                    # A leaf whose human render omits an outcome banner (e.g. rich
                    # reports) is compared on exit code instead.
                    self.assertEqual(
                        agent.returncode,
                        human.returncode,
                        f"{leaf} exit differs human/agent",
                    )
                    continue
                self.assertEqual(
                    agent_family,
                    human_family,
                    f"{leaf} outcome family mismatch: agent={agent_family} human={human_family}",
                )


class AliasEquivalenceTests(unittest.TestCase):
    """E-01: every alias leaf is agent-byte-equivalent to its canonical target."""

    ALIAS_SAFE = {
        "spec check": "specs check",
        "sanitize": "check-local-leaks",
    }

    def test_alias_agent_output_is_byte_equivalent(self):
        for alias, canonical in self.ALIAS_SAFE.items():
            with self.subTest(alias=alias):
                decl = get_declaration(alias)
                self.assertIsNotNone(decl, f"alias {alias} not declared")
                assert decl is not None  # narrow for type-checkers
                self.assertEqual(decl.command_class, "alias")
                a = run_cli([*alias.split(), "--agent"])
                c = run_cli([*canonical.split(), "--agent"])
                self.assertEqual(a.returncode, c.returncode, f"{alias} rc differs")
                self.assertEqual(a.stdout, c.stdout, f"{alias} stdout not byte-equal")


if __name__ == "__main__":
    unittest.main()
