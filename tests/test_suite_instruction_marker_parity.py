"""Regression test for parity between pyproject.toml addopts and managed instruction text.

P16 compliance note:
pyproject.toml is build configuration, not production code (agent_workflows/*.py).
P16's narrow exception permits content verification where the text or file itself is
the artifact under test, which applies here because the instruction text emitted by
engine.agents_pointer_prose is the installed artifact. Asserting on the return value
of agents_pointer_prose is a behavioral assertion on a pure function.
Production source (agent_workflows/engine.py) is not read with read_text(), inspect,
ast, or substring search.
"""

import re
import unittest

from agent_workflows import engine, leak_sanitizer
from tests.support import REPO_ROOT


def extract_configured_marker_expr(pyproject_content: str) -> str:
    """Extract configured marker filter expression from pyproject.toml content.

    3.9-safe: uses existing flat-TOML string parser from leak_sanitizer (no tomllib).
    """
    strings = leak_sanitizer._parse_simple_toml_strings(pyproject_content)
    addopts = strings.get("addopts", "")
    match = re.search(r"-m\s+'([^']+)'", addopts)
    if not match:
        raise ValueError(f"Could not extract -m '<expr>' from addopts: {addopts!r}")
    return match.group(1)


class SuiteInstructionMarkerParityTests(unittest.TestCase):
    """Ensure engine.agents_pointer_prose accurately quotes pyproject addopts marker filter."""

    def test_instruction_quotes_configured_addopts_marker_filter(self):
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        marker_expr = extract_configured_marker_expr(content)

        # Assert over both supported layouts (aw and legacy)
        for layout in ("aw", "legacy"):
            prose = engine.agents_pointer_prose(target_layout=layout)

            # 1. Configured marker expression appears verbatim in prose
            self.assertIn(
                marker_expr,
                prose,
                f"Configured marker expression {marker_expr!r} missing in layout={layout} prose",
            )

            # 2. Exact stale fragment -m 'not slow' does not appear
            self.assertNotIn(
                "-m 'not slow'",
                prose,
                f"Stale marker fragment \"-m 'not slow'\" found in layout={layout} prose",
            )
