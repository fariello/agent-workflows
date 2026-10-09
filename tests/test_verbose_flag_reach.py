#!/usr/bin/env python3

"""Tests for --verbose flag reach, acceptance, and end-to-end observable difference.

IPD c4btis: Wire --verbose onto the shared output-mode parents so every agent-mode command
accepts the documented verbosity flag.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
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


class VerboseFlagReachTests(unittest.TestCase):
    """Reach, acceptance, and end-to-end tests for --verbose."""

    def test_derived_reach_every_agent_leaf_accepts_verbose(self) -> None:
        """Every leaf parser that accepts --agent must also accept --verbose.

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
            and "--verbose" not in _parser_option_strings(p)
        ]
        self.assertEqual(
            missing,
            [],
            f"Leaves accepting --agent without --verbose ({len(missing)} of {len(agent_leaves)}): {missing}",
        )

    def test_verbose_flag_acceptance_check_plans(self) -> None:
        """Assert that aw check plans accepts --agent --verbose and sets verbose=True.

        NOTE: This asserts on parse_args ONLY and deliberately NOT on command output/stdout.
        The end-to-end record assertion is E-03's job and lives in its own test, so a
        parse-level regression and a render-level regression fail separately and name
        themselves.
        """
        parser = cli._build_parser()
        args = parser.parse_args(["check", "plans", "--agent", "--verbose"])
        self.assertTrue(getattr(args, "verbose", False))

    def test_verbose_flag_synthetic_observable_difference(self) -> None:
        """Drive check plans against a synthetic repo and assert compact vs verbose key sets.

        Fast-suite twin for test_verbose_flag_end_to_end_observable_difference.
        Asserts that every diagnostics entry in the compact record carries exactly
        the keys 'location' and 'rule', while the verbose record's entries additionally
        carry 'detail' and 'severity'.
        Asserts on key presence and absence only, never on a findings count or a diagnostic's
        text (both of which move with the tree).
        Asserts that both compact and verbose diagnostics lists are non-empty before iterating.
        Asserts the verbose call does not raise and returns an exit code in (0, 1).
        """
        with tempfile.TemporaryDirectory() as td:
            repo_root = Path(td)
            (repo_root / ".aw" / "records" / "plans").mkdir(parents=True)

            compact_stdout = io.StringIO()
            with contextlib.redirect_stdout(compact_stdout):
                compact_rc = cli.main(
                    ["check", "plans", "--agent", "--dir", str(repo_root)]
                )
            self.assertIn(compact_rc, (0, 1), f"Unexpected exit code {compact_rc}")

            verbose_stdout = io.StringIO()
            with contextlib.redirect_stdout(verbose_stdout):
                verbose_rc = cli.main(
                    ["check", "plans", "--agent", "--verbose", "--dir", str(repo_root)]
                )
            self.assertIn(verbose_rc, (0, 1), f"Unexpected exit code {verbose_rc}")

            def parse_record(output: str) -> dict:
                for line in output.strip().splitlines():
                    line = line.strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            if (
                                data.get("schema") == "aw.agent/v1"
                                and data.get("kind") == "result"
                            ):
                                return data
                        except json.JSONDecodeError:
                            continue
                self.fail(f"No aw.agent/v1 result record found in output: {output}")

            compact_rec = parse_record(compact_stdout.getvalue())
            verbose_rec = parse_record(verbose_stdout.getvalue())

            compact_diags = compact_rec.get("diagnostics", [])
            verbose_diags = verbose_rec.get("diagnostics", [])

            self.assertTrue(
                compact_diags, "Expected non-empty diagnostics for check plans"
            )
            self.assertTrue(
                verbose_diags, "Expected non-empty diagnostics for check plans"
            )

            for diag in compact_diags:
                self.assertEqual(
                    set(diag.keys()),
                    {"location", "rule"},
                    f"Compact diagnostic has unexpected keys: {diag.keys()}",
                )
                self.assertNotIn("detail", diag)
                self.assertNotIn("severity", diag)

            for diag in verbose_diags:
                self.assertIn("location", diag)
                self.assertIn("rule", diag)
                self.assertIn("detail", diag)
                self.assertIn("severity", diag)

    # Deselected from the default fast suite via @pytest.mark.livecorpus because it sweeps
    # this repository's live .aw/records/ tree in-process (costing ~27s-135s).
    # Its key-presence/absence contract is covered in the fast suite by the synthetic-repo
    # twin test_verbose_flag_synthetic_observable_difference. Still run in make test-all.
    @pytest.mark.livecorpus
    def test_verbose_flag_end_to_end_observable_difference(self) -> None:
        """Drive check plans in-process and assert compact vs verbose observable difference.

        Asserts that every diagnostics entry in the compact record carries exactly the
        keys 'location' and 'rule', while the verbose record's entries additionally carry
        'detail' and 'severity'.
        Asserts on key presence and absence, never on a findings count or a diagnostic's
        text (both of which move with the tree).
        Asserts the verbose call does not raise and returns an exit code in (0, 1).
        """
        compact_stdout = io.StringIO()
        with contextlib.redirect_stdout(compact_stdout):
            compact_rc = cli.main(["check", "plans", "--agent"])
        self.assertIn(compact_rc, (0, 1), f"Unexpected exit code {compact_rc}")

        verbose_stdout = io.StringIO()
        with contextlib.redirect_stdout(verbose_stdout):
            verbose_rc = cli.main(["check", "plans", "--agent", "--verbose"])
        self.assertIn(verbose_rc, (0, 1), f"Unexpected exit code {verbose_rc}")

        def parse_record(output: str) -> dict:
            for line in output.strip().splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        if (
                            data.get("schema") == "aw.agent/v1"
                            and data.get("kind") == "result"
                        ):
                            return data
                    except json.JSONDecodeError:
                        continue
            self.fail(f"No aw.agent/v1 result record found in output: {output}")

        compact_rec = parse_record(compact_stdout.getvalue())
        verbose_rec = parse_record(verbose_stdout.getvalue())

        compact_diags = compact_rec.get("diagnostics", [])
        verbose_diags = verbose_rec.get("diagnostics", [])

        self.assertTrue(compact_diags, "Expected non-empty diagnostics for check plans")
        self.assertTrue(verbose_diags, "Expected non-empty diagnostics for check plans")

        for diag in compact_diags:
            self.assertEqual(
                set(diag.keys()),
                {"location", "rule"},
                f"Compact diagnostic has unexpected keys: {diag.keys()}",
            )
            self.assertNotIn("detail", diag)
            self.assertNotIn("severity", diag)

        for diag in verbose_diags:
            self.assertIn("location", diag)
            self.assertIn("rule", diag)
            self.assertIn("detail", diag)
            self.assertIn("severity", diag)


if __name__ == "__main__":
    unittest.main()
