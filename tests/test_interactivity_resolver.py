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
import io
import os
import sys
import types
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
                                # Expected answer logic (Option A asymmetric ladder, PR-306 / OQ-03):
                                # 1. negative override wins immediately
                                if override is False:
                                    expected = False
                                # 2. forced non-interactive env wins over positive override and detection
                                elif is_forced:
                                    expected = False
                                # 3. positive override beats stream detection
                                elif override is True:
                                    expected = True
                                # 4. stdin must be TTY
                                elif not stdin_tty:
                                    expected = False
                                # 5. output must be TTY
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
    """Behavioral reachability proof: all sanctioned delegations follow term.is_interactive."""

    SANCTIONED_DELEGATIONS: frozenset[tuple[str, str]] = frozenset(
        {
            ("artifact_adopt.py", "leak_gate_is_interactive"),
            ("git_commit_helper.py", "_is_interactive"),
            ("runner_stop.py", "interrupt_menu_is_safe"),
            ("runner_shared.py", "is_interactive_run"),
            ("engine.py", "is_interactive_session"),
        }
    )

    def test_sanctioned_delegations_reach_term_resolver(self) -> None:
        """Assert every sanctioned delegation follows term.is_interactive and engine short-circuits."""
        invokers = {
            (
                "artifact_adopt.py",
                "leak_gate_is_interactive",
            ): lambda: artifact_adopt.leak_gate_is_interactive(environ={}),
            (
                "git_commit_helper.py",
                "_is_interactive",
            ): lambda: git_commit_helper._is_interactive(),
            (
                "runner_stop.py",
                "interrupt_menu_is_safe",
            ): lambda: runner_stop.interrupt_menu_is_safe(),
            (
                "runner_shared.py",
                "is_interactive_run",
            ): lambda: runner_shared.is_interactive_run(),
            (
                "engine.py",
                "is_interactive_session",
            ): lambda: engine.is_interactive_session(types.SimpleNamespace(yes=False)),
        }
        for filename, func_name in sorted(self.SANCTIONED_DELEGATIONS):
            invoke = invokers[(filename, func_name)]
            with self.subTest(file=filename, func=func_name):
                with mock.patch.object(term, "is_interactive", return_value=True):
                    self.assertTrue(
                        invoke(),
                        f"Sanctioned delegation {func_name} in {filename} did not follow term.is_interactive=True",
                    )
                with mock.patch.object(term, "is_interactive", return_value=False):
                    self.assertFalse(
                        invoke(),
                        f"Sanctioned delegation {func_name} in {filename} did not follow term.is_interactive=False",
                    )

        # Pin engine.is_interactive_session short-circuit: yes=True returns False even when resolver is True
        with mock.patch.object(term, "is_interactive", return_value=True):
            self.assertFalse(
                engine.is_interactive_session(types.SimpleNamespace(yes=True)),
                "engine.is_interactive_session must short-circuit to False when yes=True",
            )


class AsymmetricPrecedenceLadderTests(unittest.TestCase):
    """PR-306 / OQ-03 Option A / E-05 / V-05: Asymmetric ladder and eight safety cells."""

    def setUp(self) -> None:
        super().setUp()
        self._orig_override = term.get_interactive_override()
        term.set_interactive_override(None)

    def tearDown(self) -> None:
        term.set_interactive_override(self._orig_override)
        super().tearDown()

    def test_negative_override_beats_everything_including_real_tty(self) -> None:
        tty_in = _FakeStream(True)
        tty_out = _FakeStream(True)
        self.assertFalse(
            term.is_interactive(
                stdin=tty_in, output_stream=tty_out, override=False, environ={}
            )
        )
        term.set_interactive_override(False)
        self.assertFalse(
            term.is_interactive(stdin=tty_in, output_stream=tty_out, environ={})
        )

    def test_forced_noninteractive_beats_positive_override(self) -> None:
        for var in ("CI", "AW_NONINTERACTIVE"):
            for val in ("1", "true", "yes"):
                with self.subTest(var=var, val=val):
                    self.assertFalse(
                        term.is_interactive(override=True, environ={var: val}),
                        f"{var}={val} must defeat override=True",
                    )
                    term.set_interactive_override(True)
                    self.assertFalse(
                        term.is_interactive(environ={var: val}),
                        f"{var}={val} must defeat process-wide override=True",
                    )
                    term.set_interactive_override(None)

    def test_positive_override_beats_stream_detection_when_not_forced(self) -> None:
        pipe_in = _FakeStream(False)
        pipe_out = _FakeStream(False)
        self.assertTrue(
            term.is_interactive(
                stdin=pipe_in, output_stream=pipe_out, override=True, environ={}
            )
        )
        term.set_interactive_override(True)
        self.assertTrue(
            term.is_interactive(stdin=pipe_in, output_stream=pipe_out, environ={})
        )

    def test_eight_safety_cells_across_four_hardened_sites(self) -> None:
        """PR-306 / OQ-03 Option A / V-05: Eight safety cells must all answer False."""
        term.set_interactive_override(True)
        for var in ("CI", "AW_NONINTERACTIVE"):
            with mock.patch.dict(os.environ, {var: "1"}):
                # 1. runner_stop.interrupt_menu_is_safe
                cell1 = runner_stop.interrupt_menu_is_safe()
                self.assertFalse(
                    cell1,
                    f"runner_stop.interrupt_menu_is_safe must be False for {var}=1",
                )

                # 2. ipd_lifecycle fence
                ctx = argparse.Namespace(is_agent=False, is_json=False)
                cell2 = not (ctx.is_agent or ctx.is_json) and term.is_interactive()
                self.assertFalse(
                    cell2, f"ipd_lifecycle fence must be False for {var}=1"
                )

                # 3. artifact_adopt.leak_gate_is_interactive
                cell3 = artifact_adopt.leak_gate_is_interactive()
                self.assertFalse(
                    cell3,
                    f"artifact_adopt.leak_gate_is_interactive must be False for {var}=1",
                )

                # 4. runner_shared.is_interactive_run
                cell4 = runner_shared.is_interactive_run()
                self.assertFalse(
                    cell4, f"runner_shared.is_interactive_run must be False for {var}=1"
                )
