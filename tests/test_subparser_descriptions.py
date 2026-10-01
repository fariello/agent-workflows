"""Default-visible regression guard for authored subparser descriptions.

Guards the help contract (plan 3e70cv) for subparsers fixed by plan ypnk56:
1. The seven authored subparsers have non-empty descriptions strictly longer than their help.
2. The 'conf unset' alias renders the canonical authored prose (content-anchored, not identity).
3. Critical safety caveats survive in rendered help output for mutating/probing commands.
"""

import argparse
import re
import unittest

from agent_workflows import cli

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _normalize(text: str) -> str:
    """Strip ANSI escape sequences and flatten all whitespace runs to single spaces."""
    return " ".join(_ANSI_RE.sub("", text).split())


def _resolve_subparser(parser, path):
    parts = path.split()
    current = parser
    parent = None
    last_name = None
    for part in parts:
        found = False
        for action in current._actions:
            if isinstance(action, argparse._SubParsersAction):
                if part in action.choices:
                    parent = action
                    last_name = part
                    current = action.choices[part]
                    found = True
                    break
        if not found:
            raise KeyError(f"Subparser {part!r} not found for path {path!r}")
    help_by = {ca.dest: (ca.help or "") for ca in parent._choices_actions}
    return current, help_by.get(last_name, "")


class SubparserDescriptionRegressionTests(unittest.TestCase):
    """Default-visible tests verifying authored subparser descriptions and safety caveats."""

    def test_authored_subparsers_satisfy_description_contract(self):
        parser = cli._build_parser()
        paths = [
            "config unset",
            "upgrade-test list",
            "upgrade-test new",
            "upgrade-test sandboxes",
            "upgrade-test probe",
            "upgrade-test env",
            "upgrade-test clean",
        ]
        for path in paths:
            sub, hlp = _resolve_subparser(parser, path)
            desc = sub.description or ""
            self.assertTrue(
                bool(desc.strip()),
                f"{path}: expected non-empty description",
            )
            self.assertGreater(
                len(desc),
                len(hlp),
                f"{path}: expected len(desc) > len(help) ({len(desc)} <= {len(hlp)})",
            )
            self.assertNotEqual(
                desc,
                hlp,
                f"{path}: description equals help",
            )

    def test_alias_shows_canonical_authored_prose(self):
        parser = cli._build_parser()
        sub, _ = _resolve_subparser(parser, "conf unset")
        rendered = _normalize(sub.format_help())
        phrase = "unrecognized variable name is refused with exit 2"
        self.assertIn(
            phrase,
            rendered,
            f"Expected canonical authored phrase {phrase!r} in rendered help for 'conf unset'",
        )

    def test_safety_caveats_survive_in_rendered_help(self):
        parser = cli._build_parser()

        clean_sub, _ = _resolve_subparser(parser, "upgrade-test clean")
        clean_help = _normalize(clean_sub.format_help())
        preview_phrase = _normalize(
            "Previews removals by default and deletes nothing until `-y` is passed."
        )
        self.assertIn(
            preview_phrase,
            clean_help,
            "Expected preview-by-default caveat in 'upgrade-test clean' help",
        )
        clean_marker_phrase = _normalize(
            "Refuses any path lacking the harness marker (.aw-sandbox.json) even when `-y` is supplied"
        )
        self.assertIn(
            clean_marker_phrase,
            clean_help,
            "Expected marker refusal caveat in 'upgrade-test clean' help",
        )

        probe_sub, _ = _resolve_subparser(parser, "upgrade-test probe")
        probe_help = _normalize(probe_sub.format_help())
        probe_refusal_phrase = _normalize(
            "Refuses any path lacking the harness marker (.aw-sandbox.json) with exit 2."
        )
        self.assertIn(
            probe_refusal_phrase,
            probe_help,
            "Expected refusal caveat in 'upgrade-test probe' help",
        )
