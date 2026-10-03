"""Regression guard ensuring no CLI help surface claims the retracted non-TTY auto-switch.

Plan 79piey / Backlog qdd6ey.
Prevents help surfaces from promising automatic aw.agent/v1 JSONL or structured JSON
when piped or redirected to a non-TTY stdout. The only route to JSONL is --agent,
and the only route to structured JSON is --json (docs/cli-output-contract.md Section 9).
"""

from __future__ import annotations

import argparse
import re
import unittest
from typing import Iterator, Tuple

from agent_workflows import cli

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Claim shape matching: catches retracted auto-switch promises in original or reworded form.
CLAIM_PATTERN = re.compile(
    r"(non-TTY|\bpiped\b|\bredirect\w*)[^.]{0,80}(JSONL|aw\.agent/v1)|"
    r"(JSONL|aw\.agent/v1)[^.]{0,80}(\bpiped\b|non-TTY|\bredirect\w*)"
)


def _normalize(text: str) -> str:
    """Strip ANSI escape sequences and flatten all whitespace runs to single spaces."""
    return " ".join(_ANSI_RE.sub("", text).split())


def _iter_all_parsers(
    root_parser: argparse.ArgumentParser,
) -> Iterator[Tuple[str, argparse.ArgumentParser]]:
    """Recursively yield (path, parser) across the entire parser tree, deduplicating aliases."""
    seen = set()
    stack = [("aw", root_parser)]
    while stack:
        path, p = stack.pop(0)
        p_id = id(p)
        if p_id in seen:
            continue
        seen.add(p_id)
        yield path, p
        for a in p._actions:
            if isinstance(a, argparse._SubParsersAction):
                for name, choice_parser in a.choices.items():
                    if id(choice_parser) not in seen:
                        stack.append((f"{path} {name}", choice_parser))


class HelpNonTTYClaimTests(unittest.TestCase):
    """Assert across whole parser tree that no help surface claims non-TTY auto-switch."""

    def test_no_rendered_help_surface_claims_nontty_autoswitch(self):
        """No rendered help surface claims JSONL on non-TTY / piped / redirected stdout.

        Walks the whole built parser tree, renders format_help() for each parser,
        normalizes whitespace and strips ANSI color escapes, and verifies against CLAIM_PATTERN.
        Also verifies the positive limb: any surface declaring 'Agent mode:' must name
        '--agent' in that sentence, and at least one such surface must exist.
        """
        root = cli._build_parser()
        agent_mode_surfaces = 0

        for path, parser in _iter_all_parsers(root):
            rendered_help = parser.format_help()
            norm = _normalize(rendered_help)

            # Negative limb: no surface claims auto-switch on non-TTY / pipe / redirect.
            match = CLAIM_PATTERN.search(norm)
            if match is not None:
                self.fail(
                    f"{path}: help surface asserts retracted non-TTY auto-switch claim: "
                    f"{match.group(0)!r} in help text:\n{norm}"
                )

            # Positive limb: surfaces with 'Agent mode:' must name '--agent' in that sentence.
            if "Agent mode:" in norm:
                agent_mode_surfaces += 1
                for m in re.finditer(r"Agent mode:[^.]*\.?", norm):
                    sentence = m.group(0)
                    self.assertIn(
                        "--agent",
                        sentence,
                        f"{path}: 'Agent mode:' sentence must name '--agent', found: {sentence!r}",
                    )

        self.assertGreater(
            agent_mode_surfaces,
            0,
            "Expected at least one help surface to contain 'Agent mode:'",
        )


if __name__ == "__main__":
    unittest.main()
