"""Behavioral tests for lazy CLI startup, selective subparser dispatch, and O(1) layout git state."""

from __future__ import annotations

import argparse
import subprocess
import sys
import unittest

from agent_workflows import cli, config, layout_inventory


def _subparser_names(parser: argparse.ArgumentParser) -> set[str]:
    for act in parser._actions:
        if isinstance(act, argparse._SubParsersAction):
            return set(act._name_parser_map.keys())
    return set()


class LazyCliStartupTests(unittest.TestCase):
    """Verify selective subparser dispatch and lazy imports preserve full CLI parity."""

    def test_title_style_values_stay_in_sync_with_config(self) -> None:
        self.assertEqual(cli._TITLE_STYLE_VALUES, config.TITLE_STYLE_VALUES)

    def test_selective_dispatch_parser_covers_every_top_command_and_alias(self) -> None:
        full_parser = cli._build_parser()
        full_sub = next(
            act
            for act in full_parser._actions
            if isinstance(act, argparse._SubParsersAction)
        )
        all_names = sorted(full_sub._name_parser_map.keys())
        self.assertGreater(len(all_names), 40)

        for name in all_names:
            if name in ("completion", "__complete"):
                continue
            selective = cli._get_dispatch_parser(only_cmd=name)
            sel_sub = next(
                act
                for act in selective._actions
                if isinstance(act, argparse._SubParsersAction)
            )
            self.assertIn(name, sel_sub._name_parser_map)
            full_child = full_sub._name_parser_map[name]
            sel_child = sel_sub._name_parser_map[name]
            self.assertEqual(sel_child.prog, full_child.prog)
            self.assertEqual(
                _subparser_names(sel_child),
                _subparser_names(full_child),
                f"Subcommand mismatch for top-level command {name!r}",
            )

    def test_unknown_command_falls_back_to_full_usage_error(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "definitely-not-a-real-cmd"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("invalid choice", proc.stderr)

    def test_version_fast_path_prints_version_and_exits_zero(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "agent_workflows", "--version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(proc.stdout.startswith("agent-workflows "), proc.stdout)


class LayoutInventoryAncestorLookupTests(unittest.TestCase):
    """Verify O(1) ancestor-prefix _git_state matches linear prefix scan."""

    def test_precomputed_ancestors_match_linear_scan_across_all_cases(self) -> None:
        tracked = {".aw/system/a.md", ".aw/records/plans/p1.md"}
        untracked = {".aw/records/plans/p2.md", ".agents/draft.md"}
        ignored = {".aw/state/index.db", ".aw/worktrees/w1/file.py"}
        unmerged = {".aw/records/conflict.md"}

        tracked_anc = layout_inventory._ancestor_prefixes(tracked)
        untracked_anc = layout_inventory._ancestor_prefixes(untracked)
        ignored_anc = layout_inventory._ancestor_prefixes(ignored)
        unmerged_anc = layout_inventory._ancestor_prefixes(unmerged)

        probes = [
            None,
            "",
            ".aw",
            ".aw/",
            ".aw/system",
            ".aw/system/a.md",
            ".aw/records",
            ".aw/records/plans",
            ".aw/records/plans/p1.md",
            ".aw/records/plans/p2.md",
            ".aw/records/conflict.md",
            ".aw/state",
            ".aw/state/index.db",
            ".agents",
            ".agents/draft.md",
            "unrelated/path.txt",
        ]
        for rel in probes:
            expected = layout_inventory._git_state(
                rel, tracked, untracked, ignored, unmerged
            )
            actual = layout_inventory._git_state(
                rel,
                tracked,
                untracked,
                ignored,
                unmerged,
                tracked_anc=tracked_anc,
                untracked_anc=untracked_anc,
                ignored_anc=ignored_anc,
                unmerged_anc=unmerged_anc,
            )
            self.assertEqual(actual, expected, f"Mismatch for rel={rel!r}")
