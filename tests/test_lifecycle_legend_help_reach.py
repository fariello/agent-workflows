"""spec uonrjg Section 9.2 / lifeglyph Order 08 (`7p3tt8`) E-03, E-04 / Set spvm3v (bmxgt7) E-03, E-04:
Assert the command help legend, user documentation, and lifecycle_style cannot drift.

1. The legend rendered in root command help is GENERATED and covers every stage
   in lifecycle_style.STAGE_ORDER (word, Unicode glyph, and ASCII fallback).
2. User documentation points at the canonical command help legend rather than
   maintaining a duplicate literal lifecycle color/glyph table.
3. The __{LIFECYCLE_LEGEND}__ placeholder is substituted and never leaked in root or subparsers (E-04).
4. The legend rendered in command help exercises the both_forms=True branch (E-04).
"""

from __future__ import annotations

import argparse
import contextlib
import io
import sys
import unittest
from pathlib import Path

import pytest

from agent_workflows import cli, lifecycle_style
from agent_workflows.term import Term

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"


@contextlib.contextmanager
def _pinned_help_environment():
    """Pin the rendering environment for command help generation (PR-001).

    cli's format_help uses Term(color=False), which falls back to term.should_unicode(sys.stdout).
    To ensure the help text carries Unicode glyphs regardless of process environment, delete
    AW_ASCII_ONLY and FORCE_ASCII, and set sys.stdout to a UTF-8 TextIOWrapper.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv("AW_ASCII_ONLY", raising=False)
        mp.delenv("FORCE_ASCII", raising=False)
        buf = io.BytesIO()
        mp.setattr(sys, "stdout", io.TextIOWrapper(buf, encoding="utf-8"))
        yield


class LifecycleLegendAndDocsDriftGuardTests(unittest.TestCase):
    """spec uonrjg Section 9.2 / lifeglyph Order 08 (`7p3tt8`) / Set spvm3v (bmxgt7):
    Drift guards for the lifecycle legend in command help and human guides.
    """

    def test_command_help_legend_covers_every_stage_in_lifecycle_style(self):
        """ASSERT COVERAGE, NEVER A ROW COUNT (plan 7p3tt8 F-04 / F-05):
        Every stage in lifecycle_style.STAGE_ORDER must appear in the rendered command help
        legend with its exact word, Unicode glyph, and ASCII fallback.
        """
        with _pinned_help_environment():
            parser = cli._build_parser()
            help_text = parser.format_help()

        self.assertIn("LIFECYCLE LEGEND", help_text)

        missing_stages = []
        for stage in lifecycle_style.STAGE_ORDER:
            style = lifecycle_style.style_for(stage)
            if f"  {stage}" not in help_text:
                missing_stages.append(f"{stage} (missing stage word)")
                continue
            if style.unicode not in help_text:
                missing_stages.append(
                    f"{stage} (missing unicode glyph {style.unicode!r})"
                )
                continue
            if f" {style.ascii} " not in help_text:
                missing_stages.append(
                    f"{stage} (missing ascii fallback {style.ascii!r})"
                )
                continue

        self.assertEqual(
            missing_stages,
            [],
            f"Command help legend does not cover all stages from lifecycle_style: {missing_stages}. "
            "The legend in command help must be generated from lifecycle_style so new stages appear automatically.",
        )

    def test_docs_reference_canonical_legend_without_duplicate_tables(self):
        """User docs must reference the canonical command help legend rather than duplicating
        a hand-maintained lifecycle color/glyph table."""
        guide_path = DOCS_DIR / "cli-human-guide.md"
        self.assertTrue(guide_path.is_file())
        guide_text = guide_path.read_text(encoding="utf-8")

        self.assertIn("aw --help", guide_text)
        self.assertIn("canonical lifecycle legend", guide_text)

    def test_lifecycle_legend_placeholder_is_substituted_and_never_leaked(self):
        """E-04: placeholder __{LIFECYCLE_LEGEND}__ is substituted and never leaked.

        Asserts that the raw token does not appear in root command help and is absent
        from every subparser help across the CLI tree.
        """
        with _pinned_help_environment():
            parser = cli._build_parser()
            root_help = parser.format_help()
            self.assertNotIn(
                "__{LIFECYCLE_LEGEND}__",
                root_help,
                "Root parser format_help() leaked raw placeholder __{LIFECYCLE_LEGEND}__",
            )

            leaks = []
            subparser_count = 0

            def walk(p: argparse.ArgumentParser) -> None:
                nonlocal subparser_count
                for action in p._actions:
                    if isinstance(action, argparse._SubParsersAction):
                        for name, sub in action.choices.items():
                            subparser_count += 1
                            if "__{LIFECYCLE_LEGEND}__" in sub.format_help():
                                leaks.append(f"{p.prog} -> {name}")
                            walk(sub)

            walk(parser)
            self.assertEqual(
                leaks,
                [],
                f"Subparsers leaked raw placeholder __{{LIFECYCLE_LEGEND}}__: {leaks}",
            )
            self.assertGreater(
                subparser_count,
                0,
                "Expected to walk subparsers across the CLI tree",
            )

    def test_command_help_legend_uses_both_forms_rendering_branch(self):
        """E-04: command help legend renders using both_forms=True.

        Verifies that help text contains both the Unicode marker and ASCII fallback per line,
        matching Term(color=False, unicode=True).format_lifecycle_legend(both_forms=True),
        and does NOT match the single-form shape format_lifecycle_legend(both_forms=False).
        """
        with _pinned_help_environment():
            parser = cli._build_parser()
            help_text = parser.format_help()

        term = Term(color=False, unicode=True)
        bf_true = term.format_lifecycle_legend(both_forms=True)
        bf_false = term.format_lifecycle_legend(both_forms=False)

        help_lines = set(help_text.splitlines())

        missing_lines = []
        for line in bf_true.splitlines():
            indented = f"  {line}"
            if indented not in help_lines:
                missing_lines.append(indented)
        self.assertEqual(
            missing_lines,
            [],
            f"Command help legend missing both_forms lines: {missing_lines}",
        )

        leaked_single_forms = []
        for line in bf_false.splitlines():
            indented = f"  {line}"
            if indented in help_lines:
                leaked_single_forms.append(indented)
        self.assertEqual(
            leaked_single_forms,
            [],
            f"Command help legend unexpectedly contained single_form lines: {leaked_single_forms}",
        )


if __name__ == "__main__":
    unittest.main()
