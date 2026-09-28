#!/usr/bin/env python3

"""Behavioral uniformity tests for CLI presentation and interactivity flags across subcommands.

Recovered and redesigned per OQ-02 maintainer ruling and PR-305 / bmf32u E-04 / V-04.
Tests real user-observable command execution and behavioral dispatch across the CLI surface,
rather than code signatures, syntax, AST, or private parser data structure walks:
1. Parsed commands accept both flag pairs without error.
2. Forwarded driver commands properly consume flags before dispatch without unrecognized argument errors.
3. Mutual exclusion: passing both flags exits 2 with usage error, split into operator path and parser backstop.
4. Precedence and token passthrough: tokens after `--` are left alone and unrelated flags are untouched.
"""

from __future__ import annotations

import contextlib
import io
import unittest

from agent_workflows import cli


class ParsedCommandFlagAcceptanceTests(unittest.TestCase):
    """Observable behavior: parsed subcommands accept presentation and interactivity flags without error."""

    SAMPLED_PARSED_SUBCOMMANDS = (
        ["attention"],
        ["check"],
        ["doctor"],
        ["find", "plans"],
        ["ipd", "lint"],
    )

    def test_parsed_commands_accept_both_flag_pairs(self) -> None:
        parser = cli._build_parser()
        flags = ("--no-color", "--color", "--no-interactive", "--interactive")
        for subcmd in self.SAMPLED_PARSED_SUBCOMMANDS:
            for flag in flags:
                with self.subTest(subcommand=" ".join(subcmd), flag=flag):
                    buf = io.StringIO()
                    with contextlib.redirect_stderr(buf):
                        try:
                            # Verify parse_args accepts the flag without raising SystemExit (no unrecognized arguments)
                            # Adding --help or invoking parse_args directly on valid subcommands
                            args = parser.parse_args([*subcmd, flag])
                            self.assertIsNotNone(args)
                        except SystemExit as exc:
                            # A subcmd that raises SystemExit on help is fine, but not exit code 2 (usage error)
                            self.assertNotEqual(
                                exc.code,
                                2,
                                f"Command {' '.join(subcmd)} with flag {flag} raised usage error: {buf.getvalue()}",
                            )


class ForwardedCommandFlagConsumptionTests(unittest.TestCase):
    """Observable behavior: forwarded driver commands consume flags before dispatch.

    Every command here forwards its argv to another program's parser that declares no color
    or interactivity flags. Stripping the flags in `_consume_early_flags` prevents `unrecognized arguments`.
    """

    FORWARDED_COMMANDS = (
        ["oc", "run"],
        ["opencode", "run"],
        ["oc", "runipd"],
        ["agy", "run"],
        ["antigravity", "runagy"],
        ["oc", "review"],
        ["agy", "integrate"],
        ["run", "as"],
        ["run", "ipd"],
        ["agy", "sessions"],
        ["agy", "view"],
        ["agy", "exec"],
    )

    def test_presentation_flags_are_stripped_from_every_forwarded_argv(self) -> None:
        for prefix in self.FORWARDED_COMMANDS:
            for flag in ("--no-color", "--color"):
                with self.subTest(command=" ".join(prefix), flag=flag):
                    kept, found = cli._consume_early_flags([*prefix, flag, "status"])
                    self.assertEqual(
                        kept,
                        [*prefix, "status"],
                        f"Color flag {flag} survived into forwarded argv for {' '.join(prefix)}",
                    )
                    self.assertEqual(found.color_override, flag == "--color")

    def test_interactivity_flags_are_stripped_from_every_forwarded_argv(self) -> None:
        for prefix in self.FORWARDED_COMMANDS:
            for flag in ("--no-interactive", "--interactive"):
                with self.subTest(command=" ".join(prefix), flag=flag):
                    kept, found = cli._consume_early_flags([*prefix, flag, "status"])
                    self.assertEqual(
                        kept,
                        [*prefix, "status"],
                        f"Interactivity flag {flag} survived into forwarded argv for {' '.join(prefix)}",
                    )
                    self.assertEqual(
                        found.interactive_override, flag == "--interactive"
                    )

    def test_tokens_after_a_bare_double_dash_are_left_alone(self) -> None:
        """`--` indicates raw data. Tokens following it must not be stripped."""
        for flag in ("--color", "--no-color", "--interactive", "--no-interactive"):
            with self.subTest(flag=flag):
                kept, found = cli._consume_early_flags(["oc", "run", "--", flag, "as"])
                self.assertEqual(kept, ["oc", "run", "--", flag, "as"])
                self.assertIsNone(found.color_override)
                self.assertIsNone(found.interactive_override)
                self.assertFalse(found.saw_color)
                self.assertFalse(found.saw_interactive)

    def test_an_unrelated_flag_is_never_consumed(self) -> None:
        """Flags owned by downstream commands (like --agent or --model) must remain intact."""
        argv = ["oc", "run", "start", "--agent", "build", "--json", "--model", "x"]
        kept, found = cli._consume_early_flags(argv)
        self.assertEqual(kept, argv)
        self.assertIsNone(found.color_override)
        self.assertIsNone(found.interactive_override)


class FlagMutualExclusionTests(unittest.TestCase):
    """PR-305 / V-04: Mutual exclusion exits 2 with usage error, split into operator path and parser backstop."""

    def test_color_mutual_exclusion_on_operator_path(self) -> None:
        # Parsed command via cli._dispatch
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = cli._dispatch(["attention", "--no-color", "--color"])
        self.assertEqual(rc, 2)
        self.assertIn(
            "argument --color: not allowed with argument --no-color", buf.getvalue()
        )

        # Forwarded command via cli._dispatch
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = cli._dispatch(["oc", "run", "--no-color", "--color", "status"])
        self.assertEqual(rc, 2)
        self.assertIn(
            "argument --color: not allowed with argument --no-color", buf.getvalue()
        )

    def test_interactivity_mutual_exclusion_on_operator_path(self) -> None:
        # Parsed command via cli._dispatch
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = cli._dispatch(["attention", "--no-interactive", "--interactive"])
        self.assertEqual(rc, 2)
        self.assertIn(
            "argument --interactive: not allowed with argument --no-interactive",
            buf.getvalue(),
        )

        # Forwarded command via cli._dispatch
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            rc = cli._dispatch(
                ["oc", "run", "--no-interactive", "--interactive", "status"]
            )
        self.assertEqual(rc, 2)
        self.assertIn(
            "argument --interactive: not allowed with argument --no-interactive",
            buf.getvalue(),
        )

    def test_color_mutual_exclusion_parser_backstop(self) -> None:
        parser = cli._build_parser()
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as caught:
                parser.parse_args(["attention", "--no-color", "--color"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("not allowed with argument", buf.getvalue())

    def test_interactivity_mutual_exclusion_parser_backstop(self) -> None:
        parser = cli._build_parser()
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            with self.assertRaises(SystemExit) as caught:
                parser.parse_args(["attention", "--no-interactive", "--interactive"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("not allowed with argument", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
