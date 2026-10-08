"""Regression test for parity between pyproject.toml addopts and managed instruction text.

P16 compliance note:
pyproject.toml is build configuration, not production code (agent_workflows/*.py).
P16's narrow exception permits content verification where the text or file itself is
the artifact under test, which applies here because the instruction text in this repository's
AGENTS.md is the repo-local rule artifact, and agents_pointer_prose return values are tested
behaviorally.
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
    """Ensure AGENTS.md repo-local region accurately quotes pyproject addopts marker filter."""

    def test_instruction_quotes_configured_addopts_marker_filter(self):
        pyproject_path = REPO_ROOT / "pyproject.toml"
        content = pyproject_path.read_text(encoding="utf-8")
        marker_expr = extract_configured_marker_expr(content)

        # 1. Configured marker expression appears in this repository's AGENTS.md repo-local region
        agents_content = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
        parsed = engine.parse_aw_block(agents_content)
        self.assertTrue(parsed.found, "AGENTS.md must contain well-formed aw:block")
        repo_local = parsed.after

        self.assertIn(
            marker_expr,
            repo_local,
            f"Configured marker expression {marker_expr!r} missing in AGENTS.md repo-local region",
        )

        # 2. Exact stale fragment -m 'not slow' does not appear in repo-local region
        self.assertNotIn(
            "-m 'not slow'",
            repo_local,
            "Stale marker fragment \"-m 'not slow'\" found in AGENTS.md repo-local region",
        )

        # 3. agents_pointer_prose for both layouts no longer contains pyproject.toml
        for layout in ("aw", "legacy"):
            prose = engine.agents_pointer_prose(target_layout=layout)
            self.assertNotIn(
                "pyproject.toml",
                prose,
                f"Layout {layout} pointer prose must not contain pyproject.toml",
            )
