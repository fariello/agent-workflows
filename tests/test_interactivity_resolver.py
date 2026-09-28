"""Tests for the single originating interactivity resolver (IPD da9n1s, Set svqhmp).

Covers:
- E-01 / V-01: Two-level override (explicit argument beats process-wide), setter/getter round-trip,
  and stdin rung delegation to `term.stdin_is_interactive`.
- E-02 / V-02: Layered four-rung ladder, strict fail-closed default, and both output stream choices.
- E-03 / V-03: CI / AW_NONINTERACTIVE truthiness reconciliation across all consumers.
- E-04 / V-04: Thin delegations at the four hardened sites and git_commit_helper.
- E-05 / V-05: cli._confirm fail-safe and behavior-delta proof (stdin TTY + stdout PIPE declines).
- E-06 / V-06: Single originating definition AST guard recovered from commit `19313eed`.
"""

from __future__ import annotations

import argparse
import ast
import io
import os
import pathlib
import sys
import unittest
from unittest import mock

from agent_workflows import (
    artifact_adopt,
    cli,
    engine,
    git_commit_helper,
    runner_shared,
    runner_stop,
    term,
)


class _FakeStream:
    """A controllable stream for TTY testing."""

    def __init__(self, is_a_tty: bool) -> None:
        self._isatty = is_a_tty

    def isatty(self) -> bool:
        return self._isatty


class InteractivityResolverOverrideTests(unittest.TestCase):
    """E-01 / V-01: Override short-circuiting, process-wide setter/getter, and stdin probe."""

    def setUp(self) -> None:
        super().setUp()
        self._orig_override = term.get_interactive_override()
        term.set_interactive_override(None)

    def tearDown(self) -> None:
        term.set_interactive_override(self._orig_override)
        super().tearDown()

    def test_explicit_override_short_circuits_both_ways(self) -> None:
        non_tty_in = _FakeStream(False)
        non_tty_out = _FakeStream(False)
        tty_in = _FakeStream(True)
        tty_out = _FakeStream(True)

        # Override True forces interactive even on non-TTY streams
        self.assertTrue(
            term.is_interactive(
                stdin=non_tty_in, output_stream=non_tty_out, override=True
            )
        )
        # Override False forces non-interactive even on real TTY streams
        self.assertFalse(
            term.is_interactive(stdin=tty_in, output_stream=tty_out, override=False)
        )

    def test_process_wide_override_setter_getter_round_trip(self) -> None:
        self.assertIsNone(term.get_interactive_override())

        term.set_interactive_override(True)
        self.assertIs(term.get_interactive_override(), True)

        term.set_interactive_override(False)
        self.assertIs(term.get_interactive_override(), False)

        term.set_interactive_override(None)
        self.assertIsNone(term.get_interactive_override())

    def test_explicit_override_beats_process_wide_override(self) -> None:
        non_tty_in = _FakeStream(False)
        non_tty_out = _FakeStream(False)

        term.set_interactive_override(False)
        # Explicit True beats process-wide False
        self.assertTrue(
            term.is_interactive(
                stdin=non_tty_in, output_stream=non_tty_out, override=True
            )
        )

        term.set_interactive_override(True)
        tty_in = _FakeStream(True)
        tty_out = _FakeStream(True)
        # Explicit False beats process-wide True
        self.assertFalse(
            term.is_interactive(stdin=tty_in, output_stream=tty_out, override=False)
        )

    def test_stdin_rung_delegates_to_stdin_is_interactive(self) -> None:
        tty_out = _FakeStream(True)
        with mock.patch.object(
            term, "stdin_is_interactive", return_value=False
        ) as m_probe:
            res = term.is_interactive(output_stream=tty_out, environ={})
            self.assertFalse(res)
            m_probe.assert_called_once()


class InteractivityResolverRungMatrixTests(unittest.TestCase):
    """E-02 / V-02: Layered contract matrix across stdin, output streams, env, and overrides."""

    def test_rung_matrix_all_combinations(self) -> None:
        """Drive stdin-TTY x output-TTY x forced-non-interactive x override for stdout and stderr."""
        env_cases = [
            ({}, False, "unset"),
            ({"CI": ""}, False, "CI_empty"),
            ({"CI": "0"}, False, "CI_0"),
            ({"CI": "false"}, False, "CI_false"),
            ({"CI": "no"}, False, "CI_no"),
            ({"CI": "1"}, True, "CI_1"),
            ({"CI": "true"}, True, "CI_true"),
            ({"AW_NONINTERACTIVE": ""}, False, "AW_empty"),
            ({"AW_NONINTERACTIVE": "0"}, False, "AW_0"),
            ({"AW_NONINTERACTIVE": "false"}, False, "AW_false"),
            ({"AW_NONINTERACTIVE": "no"}, False, "AW_no"),
            ({"AW_NONINTERACTIVE": "1"}, True, "AW_1"),
            ({"AW_NONINTERACTIVE": "true"}, True, "AW_true"),
        ]

        for out_stream_name in ("stdout", "stderr"):
            for stdin_tty in (True, False):
                for out_tty in (True, False):
                    in_stream = _FakeStream(stdin_tty)
                    out_stream = _FakeStream(out_tty)
                    for env_dict, is_forced, env_label in env_cases:
                        for override in (None, True, False):
                            with self.subTest(
                                stream=out_stream_name,
                                stdin_tty=stdin_tty,
                                out_tty=out_tty,
                                env=env_label,
                                override=override,
                            ):
                                ans = term.is_interactive(
                                    stdin=in_stream,
                                    output_stream=out_stream,
                                    override=override,
                                    environ=env_dict,
                                )
                                # Expected answer logic:
                                # 1. override wins if not None
                                if override is not None:
                                    expected = override
                                # 2. forced non-interactive wins
                                elif is_forced:
                                    expected = False
                                # 3. stdin must be TTY
                                elif not stdin_tty:
                                    expected = False
                                # 4. output must be TTY
                                elif not out_tty:
                                    expected = False
                                else:
                                    expected = True

                                self.assertEqual(
                                    ans,
                                    expected,
                                    f"Failed on {out_stream_name}, stdin={stdin_tty}, out={out_tty}, env={env_label}, override={override}",
                                )

    def test_default_answer_equals_strictest_prior_behavior_pipe_is_false(self) -> None:
        """Stdin a TTY and output stream a PIPE returns False (the wedge-prevention invariant)."""
        tty_in = _FakeStream(True)
        pipe_out = _FakeStream(False)

        # stdout as output stream
        self.assertFalse(
            term.is_interactive(stdin=tty_in, output_stream=pipe_out, environ={})
        )
        # stderr as output stream
        self.assertFalse(
            term.is_interactive(stdin=tty_in, output_stream=pipe_out, environ={})
        )


class CiTruthinessReconciliationTests(unittest.TestCase):
    """E-03 / V-03: CI truthiness parsing and reconciliation across engine and adopt."""

    def test_ci_truthiness_matrix(self) -> None:
        tty_in = _FakeStream(True)
        tty_out = _FakeStream(True)

        # {"0", "false", "no"} do NOT force non-interactive
        for val in ("0", "false", "no"):
            self.assertTrue(
                term.is_interactive(
                    stdin=tty_in, output_stream=tty_out, environ={"CI": val}
                ),
                f"CI={val!r} must not force non-interactive",
            )

        # CI="" does NOT force non-interactive (agreed all along)
        self.assertTrue(
            term.is_interactive(
                stdin=tty_in, output_stream=tty_out, environ={"CI": ""}
            ),
            "CI='' must not force non-interactive",
        )

        # {"1", "true"} DOES force non-interactive
        for val in ("1", "true"):
            self.assertFalse(
                term.is_interactive(
                    stdin=tty_in, output_stream=tty_out, environ={"CI": val}
                ),
                f"CI={val!r} must force non-interactive",
            )

    def test_engine_and_adopt_agree_after_change(self) -> None:
        plan = argparse.Namespace(yes=False)
        tty_in = _FakeStream(True)
        tty_out = _FakeStream(True)

        for val in ("0", "false", "no", "", "1", "true"):
            with mock.patch.dict(os.environ, {"CI": val}):
                with mock.patch.object(sys, "stdin", tty_in), mock.patch.object(
                    sys, "stdout", tty_out
                ):
                    engine_ans = engine.is_interactive_session(plan)
                    adopt_ans = artifact_adopt.leak_gate_is_interactive(
                        stdin=tty_in, stdout=tty_out
                    )
                    self.assertEqual(
                        engine_ans,
                        adopt_ans,
                        f"engine and artifact_adopt must agree for CI={val!r}",
                    )


class SanctionedPredicatesRoutingTests(unittest.TestCase):
    """E-04 / V-04: Four hardened predicates and git_commit_helper route through resolver."""

    def test_artifact_adopt_reaches_resolver(self) -> None:
        with mock.patch.object(term, "is_interactive", return_value=True) as m_res:
            res = artifact_adopt.leak_gate_is_interactive()
            self.assertTrue(res)
            m_res.assert_called_once()

    def test_git_commit_helper_reaches_resolver(self) -> None:
        with mock.patch.object(term, "is_interactive", return_value=True) as m_res:
            res = git_commit_helper._is_interactive()
            self.assertTrue(res)
            m_res.assert_called_once_with(override=None)

    def test_runner_stop_honors_force_interactive_interrupt(self) -> None:
        # AW_FORCE_INTERACTIVE_INTERRUPT=1 bypasses stream checks
        with mock.patch.dict(
            os.environ,
            {"AW_FORCE_INTERACTIVE_INTERRUPT": "1", "AW_NONINTERACTIVE": "", "CI": ""},
        ):
            self.assertTrue(runner_stop.interrupt_menu_is_safe())

        # But AW_NONINTERACTIVE / CI still REFUSES even with force escape
        with mock.patch.dict(
            os.environ,
            {"AW_FORCE_INTERACTIVE_INTERRUPT": "1", "AW_NONINTERACTIVE": "1"},
        ):
            self.assertFalse(runner_stop.interrupt_menu_is_safe())

        with mock.patch.dict(
            os.environ,
            {"AW_FORCE_INTERACTIVE_INTERRUPT": "1", "CI": "1"},
        ):
            self.assertFalse(runner_stop.interrupt_menu_is_safe())

    def test_runner_shared_is_interactive_run_guards(self) -> None:
        args_unattended = argparse.Namespace(unattended=True, full_auto=False)
        self.assertFalse(runner_shared.is_interactive_run(args_unattended))

        args_full_auto = argparse.Namespace(unattended=False, full_auto=True)
        self.assertFalse(runner_shared.is_interactive_run(args_full_auto))

        # Behavior delta: now honors AW_NONINTERACTIVE / CI
        args_normal = argparse.Namespace(unattended=False, full_auto=False)
        with mock.patch.dict(os.environ, {"AW_NONINTERACTIVE": "1"}):
            self.assertFalse(runner_shared.is_interactive_run(args_normal))


class CliConfirmBehaviorTests(unittest.TestCase):
    """E-05 / V-05: cli._confirm fail-safe and behavior-delta proof."""

    def test_confirm_non_interactive_emits_warn_and_declines(self) -> None:
        buf = io.StringIO()
        t = term.Term(stream=buf, color=False)
        non_tty_in = _FakeStream(False)

        with mock.patch.object(sys, "stdin", non_tty_in):
            ans = cli._confirm(t, "Apply dangerous change?", False)

        self.assertFalse(ans)
        self.assertIn("pass --yes to proceed", buf.getvalue())

    def test_confirm_stdin_tty_stdout_pipe_declines_where_previously_prompted(
        self,
    ) -> None:
        """PR-203 required evidence: stdin a TTY and stdout a PIPE declines."""
        buf = io.StringIO()
        t = term.Term(stream=buf, color=False)

        r_fd, w_fd = os.pipe()
        try:
            pipe_out = os.fdopen(w_fd, "w")
            tty_in = _FakeStream(True)

            with mock.patch.object(sys, "stdin", tty_in), mock.patch.object(
                sys, "stdout", pipe_out
            ):
                ans = cli._confirm(t, "Execute plan?", False)

            self.assertFalse(ans)
            self.assertIn("declining: non-interactive", buf.getvalue())
        finally:
            os.close(r_fd)


class SingleOriginatingDefinitionTests(unittest.TestCase):
    """E-06 / V-06: Exactly ONE originating interactivity definition in the package.

    Recovered from commit `19313eed^:tests/test_term.py` (which originally guarded `should_color`).
    Ported with all four load-bearing properties:
    (a) AST, NOT SUBSTRING (avoids whitespace evasion and false passes on comments);
    (b) "ORIGINATING", NOT "one def" (sanctioned delegations are syntactically defs);
    (c) _is_pure_delegation test for wrapper checking;
    (d) walks every *.py in the agent_workflows package.
    """

    SANCTIONED_DELEGATIONS: frozenset[tuple[str, str]] = frozenset(
        {
            ("artifact_adopt.py", "leak_gate_is_interactive"),
            ("git_commit_helper.py", "_is_interactive"),
            ("runner_stop.py", "interrupt_menu_is_safe"),
            ("runner_shared.py", "is_interactive_run"),
            ("engine.py", "is_interactive_session"),
        }
    )

    @staticmethod
    def _package_dir() -> pathlib.Path:
        return pathlib.Path(term.__file__).parent

    @staticmethod
    def _is_pure_delegation(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        """One statement returning a single call whose callee is an attribute of a module."""
        body = [
            stmt
            for stmt in node.body
            if not (
                isinstance(stmt, ast.Expr)
                and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str)
            )
            and not isinstance(stmt, (ast.Import, ast.ImportFrom))
        ]
        if len(body) != 1:
            return False
        stmt = body[0]
        value = stmt.value if isinstance(stmt, (ast.Return, ast.Expr)) else None
        if not isinstance(value, ast.Call):
            return False
        return isinstance(value.func, ast.Attribute) and isinstance(
            value.func.value, ast.Name
        )

    def test_exactly_one_originating_is_interactive_in_package(self) -> None:
        """Walk all *.py in agent_workflows and assert exactly one originating is_interactive in term.py."""
        originating_sites: list[tuple[str, int]] = []
        rival_definitions: list[tuple[str, str, int]] = []

        pkg_dir = self._package_dir()
        for path in sorted(pkg_dir.glob("*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            except SyntaxError:
                continue

            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if node.name == "is_interactive":
                        if path.name == "term.py":
                            originating_sites.append((path.name, node.lineno))
                        else:
                            rival_definitions.append(
                                (path.name, node.name, node.lineno)
                            )

        self.assertEqual(
            originating_sites,
            [("term.py", originating_sites[0][1] if originating_sites else 0)],
            f"Expected exactly one originating is_interactive definition in term.py; found {originating_sites}",
        )
        self.assertEqual(
            rival_definitions,
            [],
            f"Found rival originating is_interactive definitions in package: {rival_definitions}",
        )

    def test_sanctioned_delegations_are_closed_and_reach_term_resolver(self) -> None:
        """Assert every sanctioned delegation exists and calls term.is_interactive."""
        pkg_dir = self._package_dir()
        for filename, func_name in self.SANCTIONED_DELEGATIONS:
            path = pkg_dir / filename
            self.assertTrue(path.exists(), f"Module {filename} must exist")
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

            found = False
            reaches_resolver = False
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == func_name
                ):
                    found = True
                    # Check that the function body calls is_interactive or is_forced_noninteractive
                    for inner in ast.walk(node):
                        if (
                            isinstance(inner, ast.Call)
                            and isinstance(inner.func, ast.Attribute)
                            and inner.func.attr
                            in ("is_interactive", "is_forced_noninteractive")
                        ):
                            reaches_resolver = True
                            break
                    break

            self.assertTrue(
                found,
                f"Sanctioned delegation {func_name} not found in {filename}",
            )
            self.assertTrue(
                reaches_resolver,
                f"Sanctioned delegation {func_name} in {filename} must call term.is_interactive",
            )
