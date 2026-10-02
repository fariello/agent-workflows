"""Position parity assertions for runs family flags (IPD zwv1sa).

Ensures flags declared on both the runs family and its leaves resolve
identically regardless of whether they precede or follow the leaf name.
"""

from __future__ import annotations

import argparse
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from agent_workflows import cli

# Presentation and interactivity flags are scoped out to OQ-03 (carried by
# backlog item 0b290s) because they span both runs and run nouns and involve
# the cli-output-contract specification. They are excluded from this operational
# parity test suite explicitly rather than omitted silently.
EXCLUDED_PRESENTATION_DESTS: frozenset[str] = frozenset(
    {
        "help",
        "agent",
        "color",
        "no_color",
        "interactive",
        "no_interactive",
        "json",
        "fields",
        "verbose",
    }
)

LEAF_REQUIRED_ARGS: dict[str, list[str]] = {
    "show": ["run-1"],
    "evidence": ["run-1"],
    "verify-ledger": ["run-1"],
    "next": ["run-1"],
    "resume": ["run-1"],
    "status": ["run-1"],
    "decisions": ["run-1"],
    "questions": ["run-1"],
}


def derive_colliding_pairs(
    parser: argparse.ArgumentParser | None = None,
) -> list[tuple[str, argparse.Action, argparse.Action, bool, Any]]:
    """Derive leaf actions that collide with family actions under `runs`.

    Returns tuples of (leaf_name, leaf_action, family_action, is_positional, leaf_parser).
    Excludes ancestor _VersionAction (per F-09) and EXCLUDED_PRESENTATION_DESTS.
    Deduplicates subparsers by id().
    """
    if parser is None:
        parser = cli._build_parser()

    runs_p = [
        a.choices["runs"]
        for a in parser._actions
        if getattr(a, "dest", None) == "command"
    ][0]
    runs_sub = [
        a for a in runs_p._actions if getattr(a, "dest", None) == "runs_command"
    ][0]
    family_actions = {a.dest: a for a in runs_p._actions}

    pairs = []
    seen_parser_ids = set()
    for leaf_name, leaf_p in runs_sub.choices.items():
        if id(leaf_p) in seen_parser_ids:
            continue
        seen_parser_ids.add(id(leaf_p))
        leaf_seen_dests = set()
        for la in leaf_p._actions:
            if la.dest in leaf_seen_dests:
                continue
            leaf_seen_dests.add(la.dest)
            if la.dest in family_actions:
                fa = family_actions[la.dest]
                # F-09 rule: exclude ancestor _VersionAction
                if isinstance(fa, argparse._VersionAction):
                    continue
                # Exclude presentation dests scoped out to OQ-03 / 0b290s
                if (
                    la.dest in EXCLUDED_PRESENTATION_DESTS
                    or fa.dest in EXCLUDED_PRESENTATION_DESTS
                ):
                    continue
                is_pos = len(la.option_strings) == 0
                pairs.append((leaf_name, la, fa, is_pos, leaf_p))
    return pairs


def _get_option_test_args(action: argparse.Action) -> list[str]:
    """Return argv tokens for setting an option action to a non-default value."""
    opt = action.option_strings[0]
    if isinstance(action, argparse._StoreTrueAction) or action.const is True:
        return [opt]
    if action.dest in ("dir", "repo"):
        return [opt, "/custom/repo"]
    if action.dest == "last":
        return [opt, "5"]
    if action.dest == "set":
        return [opt, "test-set"]
    if action.dest == "ipd":
        return [opt, "zwv1sa"]
    if action.dest == "status":
        return [opt, "executed"]
    if action.dest == "since":
        return [opt, "2026-09-01"]
    return [opt, "val"]


class RunsFlagPositionParityTests(unittest.TestCase):
    """Black-box parse outcome tests verifying position parity for runs flags."""

    def test_derived_pairs_lower_bound_and_breakdown(self) -> None:
        """Derive colliding pairs from the parser and assert lower bound and breakdown."""
        parser = cli._build_parser()
        pairs = derive_colliding_pairs(parser)

        options = [p for p in pairs if not p[3]]
        positionals = [p for p in pairs if p[3]]

        # Authoring baseline is 29 pairs (26 options + 3 positionals across 13 leaves).
        self.assertGreaterEqual(
            len(pairs),
            29,
            f"Expected at least 29 derived pairs, got {len(pairs)}",
        )
        self.assertGreaterEqual(
            len(options),
            26,
            f"Expected at least 26 option pairs, got {len(options)}",
        )
        self.assertGreaterEqual(
            len(positionals),
            3,
            f"Expected at least 3 positional pairs, got {len(positionals)}",
        )

        pos_leaves = sorted({p[0] for p in positionals})
        self.assertIn("list", pos_leaves)
        self.assertIn("analyze", pos_leaves)
        self.assertIn("export", pos_leaves)

    def test_runs_leaf_flag_position_parity(self) -> None:
        """Assert position parity across all derived runs leaf-and-flag pairs."""
        parser = cli._build_parser()
        pairs = derive_colliding_pairs(parser)

        for leaf_name, la, fa, is_pos, leaf_p in pairs:
            dest = la.dest
            with self.subTest(leaf=leaf_name, flag=dest, is_positional=is_pos):
                if is_pos:
                    # For positionals re-declared by leaves (list, analyze, export),
                    # absence on the leaf must not populate a default in subnamespace
                    # that clobbers the family value.
                    subns, _ = leaf_p.parse_known_args([])
                    self.assertFalse(
                        hasattr(subns, dest),
                        f"Leaf {leaf_name!r} positional {dest!r} defaulted in subnamespace "
                        f"instead of being suppressed; will clobber family value",
                    )
                else:
                    req = LEAF_REQUIRED_ARGS.get(leaf_name, [])
                    flag_args = _get_option_test_args(la)

                    # runs <flag> [v] <leaf> [required]
                    argv_before = ["runs", *flag_args, leaf_name, *req]
                    # runs <leaf> [required] <flag> [v]
                    argv_after = ["runs", leaf_name, *req, *flag_args]

                    sentinel = object()
                    ns_before = parser.parse_args(argv_before)
                    ns_after = parser.parse_args(argv_after)

                    val_before = getattr(ns_before, dest, sentinel)
                    val_after = getattr(ns_after, dest, sentinel)

                    self.assertEqual(
                        val_before,
                        val_after,
                        f"Position parity failure on leaf {leaf_name!r}, flag {dest!r}: "
                        f"before-leaf {argv_before} yielded {val_before!r}, "
                        f"after-leaf {argv_after} yielded {val_after!r}",
                    )

    def test_releases_sibling_position_parity_control(self) -> None:
        """Sibling control: releases family already uses SUPPRESS and has parity."""
        parser = cli._build_parser()
        test_dir = "/tmp/sibling_test_repo"

        for leaf in ("list", "show", "new"):
            with self.subTest(leaf=leaf):
                extra_args = ["next"] if leaf == "show" else []
                argv_before = ["releases", "--dir", test_dir, leaf, *extra_args]
                argv_after = ["releases", leaf, *extra_args, "--dir", test_dir]

                ns_before = parser.parse_args(argv_before)
                ns_after = parser.parse_args(argv_after)

                self.assertEqual(
                    getattr(ns_before, "dir", None),
                    getattr(ns_after, "dir", None),
                )
                self.assertEqual(getattr(ns_before, "dir", None), test_dir)

    def test_runs_dir_flag_position_parity_end_to_end(self) -> None:
        """End-to-end: aw runs --dir <tmp> list and aw runs list --dir <tmp> both report runs."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            run_dir = root / ".aw" / "runs" / "run-20260101T000000Z-1"
            run_dir.mkdir(parents=True)
            state = {
                "run_id": "run-20260101T000000Z-1",
                "driver": "OpenCode",
                "queue": [],
            }
            (run_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            out_before, err_before = io.StringIO(), io.StringIO()
            with redirect_stdout(out_before), redirect_stderr(err_before):
                rc_before = cli.main(["runs", "--dir", str(root), "list"])

            out_after, err_after = io.StringIO(), io.StringIO()
            with redirect_stdout(out_after), redirect_stderr(err_after):
                rc_after = cli.main(["runs", "list", "--dir", str(root)])

            self.assertEqual(rc_before, 0)
            self.assertEqual(rc_after, 0)
            self.assertIn("run-20260101T000000Z-1", out_before.getvalue())
            self.assertIn("run-20260101T000000Z-1", out_after.getvalue())
            self.assertNotIn("no matching runs found", out_before.getvalue())
            self.assertNotIn("no matching runs found", out_after.getvalue())


if __name__ == "__main__":
    unittest.main()
