"""Executed reachability guard against argparse dest-shadowing across all CLI builders.

Guards against leaves declaring arguments whose dest collides with an ancestor
subparsers action's dest. In argparse, sub-namespaces overwrite parent namespaces
during parse_args, so a colliding dest silently destroys the subcommand dispatch
routing token, causing cli._dispatch to miss its routing branch and fall through
to top-level help with exit code 2.

What a failure MEANS:
A leaf command is registered and discoverable, but structurally unreachable at
runtime because parsing an invocation overwrites an ancestor subparsers dest
token.

What a failure DOES NOT mean (F-09's limit):
This guard verifies that the subcommand routing key survives parsing. It does
NOT assert that option flag values survive across nested subcommands (such as
the runs family-flag loss where shared parent flags like --dir are overwritten
by child subparser defaults, tracked separately in Order 02 / zwv1sa). Passing
this test does not imply all option flags retain their values.

Design rationale and static rule trade (F-15):
A static rule inspecting the parser tree (e.g. forbidding any argument dest from
matching an ancestor subparsers action's dest) was evaluated and measured viable.
It was declined in favor of this executed reachability walk for three reasons:
1. Directness: It asserts observable runtime reachability directly by executing
   parse_args on synthesized valid inputs, rather than inferring reachability
   from structural properties (GUIDING_PRINCIPLES P16).
2. Maintainability: It requires no hand-maintained exemption list for shared
   parent flags that future additions might silently invalidate.
3. Mechanism-agnostic: It remains sensitive regardless of how actions or
   subparsers are arranged or subclassed.
"""

from __future__ import annotations

import argparse
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable, Dict, List, Set, Tuple
from unittest.mock import patch

from agent_workflows import (
    agy_runipd,
    cli,
    layout_inventory,
    oc_models,
    oc_runipd,
    pwatch,
    upgrade_rehearsal,
)
from agent_workflows.command_surface import discover_parser_leaves

BUILDERS: Dict[str, Callable[[], argparse.ArgumentParser]] = {
    "cli": cli._build_parser,
    "oc_runipd": oc_runipd.build_parser,
    "agy_runipd": agy_runipd.build_parser,
    "layout_inventory": layout_inventory.build_parser,
    "oc_models": oc_models.build_parser,
    "upgrade_rehearsal": upgrade_rehearsal.build_parser,
    "pwatch": pwatch.build_parser,
}

LEAF_FLOORS: Dict[str, int] = {
    "cli": 151,
    "oc_runipd": 7,
    "agy_runipd": 7,
    "upgrade_rehearsal": 6,
    "layout_inventory": 0,
    "oc_models": 0,
    "pwatch": 0,
}


def derive_value(action: argparse.Action) -> str:
    """Derive a type-appropriate placeholder string for an action."""
    if action.choices:
        return str(list(action.choices)[0])
    if action.type is int:
        return "1"
    if action.type is float:
        return "1.0"
    return "placeholder"


def find_leaf_parser_and_chain(
    root_parser: argparse.ArgumentParser, leaf_path: str
) -> Tuple[argparse.ArgumentParser, List[Tuple[str, str]]]:
    """Traverse the parser tree following leaf_path tokens, returning leaf parser and chain."""
    tokens = leaf_path.split()
    current = root_parser
    chain: List[Tuple[str, str]] = []
    for token in tokens:
        subparsers_actions = [
            a for a in current._actions if isinstance(a, argparse._SubParsersAction)
        ]
        matched = False
        for sa in subparsers_actions:
            if token in sa.choices:
                chain.append((sa.dest, token))
                current = sa.choices[token]
                matched = True
                break
        if not matched:
            raise ValueError(
                f"Could not find subparser for token '{token}' in '{leaf_path}'"
            )
    return current, chain


def synthesize_argv(
    root_parser: argparse.ArgumentParser, leaf_path: str
) -> Tuple[List[str], List[Tuple[str, str]]]:
    """Synthesize a minimal valid argv vector to reach and parse leaf_path."""
    leaf_parser, chain = find_leaf_parser_and_chain(root_parser, leaf_path)
    argv = list(leaf_path.split())

    mutex_actions_handled: Set[argparse.Action] = set()
    for group in getattr(leaf_parser, "_mutually_exclusive_groups", []):
        if group.required and group._group_actions:
            act = group._group_actions[0]
            mutex_actions_handled.update(group._group_actions)
            if act.option_strings:
                argv.append(act.option_strings[0])
                if act.nargs != 0:
                    argv.append(derive_value(act))
            else:
                argv.append(derive_value(act))

    for action in leaf_parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            continue
        if action in mutex_actions_handled:
            continue
        if not action.option_strings:
            if action.nargs in (None, "+"):
                argv.append(derive_value(action))
            elif isinstance(action.nargs, int) and action.nargs > 0:
                for _ in range(action.nargs):
                    argv.append(derive_value(action))
            elif action.nargs in ("?", "*", argparse.REMAINDER):
                pass
        else:
            if action.required:
                opt = action.option_strings[0]
                argv.append(opt)
                if action.nargs != 0:
                    argv.append(derive_value(action))
    return argv, chain


def run_reachability_walk(
    parser: argparse.ArgumentParser,
) -> Tuple[int, int, List[Tuple[str, List[str], str]], List[Tuple[str, str]]]:
    """Execute reachability walk on parser, returning (canonical_count, parsed_ok, failures, findings)."""
    leaves = sorted(discover_parser_leaves(parser))
    canonical_count = len(leaves)
    parsed_ok = 0
    failures: List[Tuple[str, List[str], str]] = []
    findings: List[Tuple[str, str]] = []

    for leaf in leaves:
        argv, chain = synthesize_argv(parser, leaf)
        out = io.StringIO()
        err = io.StringIO()
        try:
            with redirect_stdout(out), redirect_stderr(err):
                ns = parser.parse_args(argv)
            parsed_ok += 1
            for dest, expected in chain:
                val = getattr(ns, dest, None)
                if val != expected:
                    findings.append((leaf, f"{dest}={val!r} expected {expected!r}"))
        except SystemExit as exc:
            err_msg = err.getvalue().strip() or out.getvalue().strip()
            failures.append((leaf, argv, f"exit {exc.code}: {err_msg}"))

    return canonical_count, parsed_ok, failures, findings


def mutate_integration_lock_parser(
    parser: argparse.ArgumentParser,
) -> argparse.ArgumentParser:
    """Mutate parser in-place to re-introduce dest shadowing on integration-lock."""
    for a in parser._actions:
        if isinstance(a, argparse._SubParsersAction):
            sp = a.choices.get("integration-lock")
            if sp:
                for act in sp._actions:
                    if act.dest == "locked_command":
                        act.dest = "command"
    return parser


class TestCliDestShadowing(unittest.TestCase):
    """Reachability tests for CLI subcommand dispatch keys across all builders."""

    def test_clean_tree_reachability_and_total_coverage(self) -> None:
        """Verify all canonical leaves parse cleanly and retain subparsers routing keys."""
        for name, builder in BUILDERS.items():
            parser = builder()
            canonical_count, parsed_ok, failures, findings = run_reachability_walk(
                parser
            )

            floor = LEAF_FLOORS[name]
            self.assertGreaterEqual(
                canonical_count,
                floor,
                f"Builder '{name}' canonical leaf count {canonical_count} below expected floor {floor}",
            )

            self.assertEqual(
                parsed_ok,
                canonical_count,
                f"Builder '{name}' failed to achieve total leaf coverage ({parsed_ok}/{canonical_count}): {failures}",
            )

            self.assertEqual(
                findings,
                [],
                f"Builder '{name}' has dest-shadowing findings on clean tree: {findings}",
            )

    def test_mutation_sensitivity_detects_shadowed_dest(self) -> None:
        """Verify the reachability walk detects a re-shadowed integration-lock dest."""
        parser = cli._build_parser()
        mutate_integration_lock_parser(parser)

        canonical_count, parsed_ok, failures, findings = run_reachability_walk(parser)

        self.assertEqual(
            parsed_ok,
            canonical_count,
            f"Mutated parser failed to parse some leaves: {failures}",
        )
        self.assertEqual(
            len(findings),
            1,
            f"Expected exactly 1 finding on mutated parser, got {len(findings)}: {findings}",
        )
        leaf, detail = findings[0]
        self.assertEqual(leaf, "integration-lock")
        self.assertIn("command=", detail)
        self.assertIn("expected 'integration-lock'", detail)

    def test_shadowed_dest_symptom_dispatch_and_containment(self) -> None:
        """Verify dispatch symptom (rc 2, top-level usage) and proof of patch containment."""
        real_builder = cli._build_parser

        def make_mutated() -> argparse.ArgumentParser:
            return mutate_integration_lock_parser(real_builder())

        with tempfile.TemporaryDirectory() as tmpdir:
            out = io.StringIO()
            err = io.StringIO()
            with patch.object(cli, "_build_parser", side_effect=make_mutated):
                with redirect_stdout(out), redirect_stderr(err):
                    try:
                        rc = cli._dispatch(
                            ["integration-lock", "--status", "--dir", tmpdir]
                        )
                    except SystemExit as exc:
                        rc = exc.code

            stdout_text = out.getvalue()
            self.assertEqual(
                rc, 2, f"Expected dispatch rc 2, got {rc}. Stderr: {err.getvalue()}"
            )
            lines = stdout_text.splitlines()
            self.assertTrue(
                any(line.startswith("usage: agent-workflows") for line in lines[:3]),
                f"Expected top-level usage in stdout. First 3 lines: {lines[:3]}",
            )

        # Containment proof: immediately after context manager exit, a fresh parser must have no findings
        fresh_parser = cli._build_parser()
        _, _, _, clean_findings = run_reachability_walk(fresh_parser)
        self.assertEqual(
            clean_findings,
            [],
            f"Post-patch fresh parser leaked mutation or findings: {clean_findings}",
        )


if __name__ == "__main__":
    unittest.main()
