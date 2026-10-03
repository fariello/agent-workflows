#!/usr/bin/env python3

"""Tests for --fields flag reach, acceptance, end-to-end projection, and abbreviation contract.

IPD 75ic2f: Wire --fields onto the shared output-mode parents so every agent-mode command
accepts the documented projection flag.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import unittest

import pytest

from agent_workflows import cli


def _discover_leaf_parsers(
    parser: argparse.ArgumentParser, prefix: str = ""
) -> list[tuple[str, argparse.ArgumentParser]]:
    """Recursively extract all canonical leaf (name, parser) pairs from an argparse parser tree.

    Deduplicates by parser object identity so aliases are not counted twice,
    following the identity rule documented in command_surface.discover_parser_leaves.
    """
    subparsers_actions = [
        a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
    ]
    if not subparsers_actions:
        leaf = prefix.strip()
        return [(leaf, parser)] if leaf else []

    leaves: list[tuple[str, argparse.ArgumentParser]] = []
    for sa in subparsers_actions:
        seen_parsers: list[tuple[str, argparse.ArgumentParser]] = []
        for choice_name, subparser in sa.choices.items():
            if any(subparser is prior for _, prior in seen_parsers):
                continue
            seen_parsers.append((choice_name, subparser))
            full_name = f"{prefix} {choice_name}".strip()
            leaves.extend(_discover_leaf_parsers(subparser, full_name))
    return leaves


def _parser_option_strings(parser: argparse.ArgumentParser) -> set[str]:
    opts: set[str] = set()
    for action in parser._actions:
        opts.update(action.option_strings)
    return opts


class FieldsFlagReachTests(unittest.TestCase):
    """Reach, acceptance, and projection tests for --fields."""

    def test_derived_reach_every_agent_leaf_accepts_fields(self) -> None:
        """Every leaf parser that accepts --agent must also accept --fields.

        Derived dynamically from cli._build_parser() with identity deduplication
        for aliases; no hardcoded integer count is used.
        """
        parser = cli._build_parser()
        leaves = _discover_leaf_parsers(parser)
        agent_leaves = [
            name for name, p in leaves if "--agent" in _parser_option_strings(p)
        ]
        missing = [
            name
            for name, p in leaves
            if "--agent" in _parser_option_strings(p)
            and "--fields" not in _parser_option_strings(p)
        ]
        self.assertEqual(
            missing,
            [],
            f"Leaves accepting --agent without --fields ({len(missing)} of {len(agent_leaves)}): {missing}",
        )

    def test_fields_flag_acceptance_find_plans(self) -> None:
        """Assert that aw find plans accepts --agent --fields findings.

        NOTE: This asserts on parse_args ONLY and deliberately NOT on command output/stdout.
        As measured in F-08, aw find's agent branch prints bare repository paths and returns
        before building any CommandResult record. Asserting a projected record here would
        pin behavior that IPD 75ic2f does not deliver and which is tracked in backlog item
        wdazvp.
        """
        parser = cli._build_parser()
        args = parser.parse_args(["find", "plans", "--agent", "--fields", "findings"])
        self.assertEqual(getattr(args, "fields", None), "findings")

    @pytest.mark.livecorpus
    def test_fields_flag_end_to_end_projection(self) -> None:
        """Drive aw check plans --agent --fields findings end to end and assert projection.

        Asserts that the requested key ('findings') is present in the emitted JSONL record,
        while non-envelope keys ('target', 'diagnostics') that the unprojected record
        carries are absent.
        Per PR-205 and F-14, this does NOT assert on the count/value of findings (which is
        live-tree state) and specifically checks for absence of 'target' or 'diagnostics'
        rather than 'next' (which is unstable in unprojected runs).
        """
        stdout_buf = io.StringIO()
        with contextlib.redirect_stdout(stdout_buf):
            rc = cli.main(["check", "plans", "--agent", "--fields", "findings"])
        self.assertIn(rc, (0, 1), f"Unexpected exit code {rc}")
        captured_out = stdout_buf.getvalue()
        record = None
        for line in captured_out.strip().splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    data = json.loads(line)
                    if (
                        data.get("schema") == "aw.agent/v1"
                        and data.get("kind") == "result"
                    ):
                        record = data
                        break
                except json.JSONDecodeError:
                    continue
        self.assertIsNotNone(
            record, f"No aw.agent/v1 result record found in stdout: {captured_out}"
        )
        self.assertIn(
            "findings",
            record,
            f"Requested key 'findings' missing from record: {record}",
        )
        self.assertNotIn(
            "target",
            record,
            f"'target' should have been dropped by projection: {record}",
        )
        self.assertNotIn(
            "diagnostics",
            record,
            f"'diagnostics' should have been dropped by projection: {record}",
        )

    def test_abbreviation_disabled_contract(self) -> None:
        """Observable outcome: full options parse, but abbreviations are refused with exit 2.

        IPD 75ic2f E-03 disables prefix abbreviation (allow_abbrev=False) on _AwArgumentParser
        so that adding a flag to a shared parent cannot silently alter the resolution or
        availability of existing options.

        Sampled leaves (at minimum check --force, check-local-leaks --fix, ipd set --from-backlog,
        runs list --failed). check-local-leaks --fi is singled out explicitly: prior to IPD 75ic2f,
        --fi was an unambiguous prefix for --fix (the flag that rewrites files). Turning off
        abbreviation ensures it is explicitly rejected as unrecognized rather than silently resolved
        or conditionally ambiguous.
        """
        parser = cli._build_parser()

        # 1. Full long options must parse without error on sampled leaves (both before and after E-03)
        args_check = parser.parse_args(["check", "--force"])
        self.assertTrue(getattr(args_check, "force", False))

        args_leak = parser.parse_args(["check-local-leaks", "--fix"])
        self.assertTrue(getattr(args_leak, "fix", False))

        args_ipd = parser.parse_args(
            ["ipd", "set", "dummy", "--from-backlog", "rcjorx"]
        )
        self.assertEqual(getattr(args_ipd, "from_backlog", None), "rcjorx")

        args_runs = parser.parse_args(["runs", "list", "--failed"])
        self.assertTrue(getattr(args_runs, "failed", False))

        # 2. Abbreviated long options must be rejected with SystemExit(2) and 'unrecognized arguments'
        sampled_abbrev = [
            (["check", "--f"], "--f"),
            (["check-local-leaks", "--fi"], "--fi"),
            (["ipd", "set", "dummy", "--from-b", "rcjorx"], "--from-b"),
            (["runs", "list", "--fail"], "--fail"),
        ]
        for cmd, abbrev in sampled_abbrev:
            stderr_buf = io.StringIO()
            with contextlib.redirect_stderr(stderr_buf):
                with self.assertRaises(SystemExit) as ctx:
                    parser.parse_args(cmd)
            self.assertEqual(ctx.exception.code, 2)
            err_msg = stderr_buf.getvalue()
            self.assertIn(
                f"unrecognized arguments: {abbrev}",
                err_msg,
                f"Expected explicit unrecognized arguments for abbreviation {abbrev}, got: {err_msg}",
            )

        # 3. Dedicated single-option leaf test for check-local-leaks --fi:
        # Prior to E-02, check-local-leaks had only --fix (no --fields), so --fi was accepted
        # as a working abbreviation. With allow_abbrev=False on _AwArgumentParser, an isolated
        # parser with only --fix still refuses --fi with 'unrecognized arguments: --fi'.
        single_p = cli._AwArgumentParser()
        single_p.add_argument("--fix", action="store_true")
        single_stderr = io.StringIO()
        with contextlib.redirect_stderr(single_stderr):
            with self.assertRaises(SystemExit) as ctx_single:
                single_p.parse_args(["--fi"])
        self.assertEqual(ctx_single.exception.code, 2)
        self.assertIn(
            "unrecognized arguments: --fi",
            single_stderr.getvalue(),
            f"Expected unrecognized arguments for --fi on isolated parser, got: {single_stderr.getvalue()}",
        )


if __name__ == "__main__":
    unittest.main()
